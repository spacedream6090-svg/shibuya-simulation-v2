"""mind.percept.draw — 割る段で ``perception/renderer.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``world/model/percept_scene.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Final, Mapping, Sequence
import re
import numpy as np
from shibuya.foundation.vocab.agent_codes import (
    INTEROCEPTION_FIELDS,
    INTERO_UP_EDGES,
    RESULT_TEXT,
    IntentKind,
    ResultCode,
    WakeCondition,
)
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.foundation.hashing import blake3_hex
from shibuya.foundation.text import channels as ch
from shibuya.foundation.text import hashes as H
from shibuya.foundation.text import normalize as N
from shibuya.foundation.text import templates as T
from shibuya.foundation.text.salience import (
    SalientItem,
    rank_by_saliency,
    StripReport,
    strip_imperatives,
)
from shibuya.foundation.ports import percept_contact as CV
from shibuya.foundation.ports.percept import Percept, SceneView, TimeView
from shibuya.world.model.state import World
from shibuya.foundation.text.percept_words import (
    INTENT_FALLBACK_TARGET,
    _activity_word,
    _hunger_word,
    intent_line,
    near_person_text,
    person_word,
)
from shibuya.world.model.percept_scene import PerceptScene, PerceptionAssets, _TickCache, _noise_stage, _prior_scores
from shibuya.mind.percept.notice import SignageNotice, check_signage_p_see

__all__ = [
    "HUNGER_WORDS_MODES", "DEFAULT_HUNGER_WORDS", "check_hunger_words", "compose_memory_line", "memory_item_text",
    "P_SEE_ACTIVITY_KINDS", "RESULT_OPTIONS", "RESULT_OPTIONS_V3", "DEFAULT_OPTIONS_V3", "ACTIVITY_EXPIRY_REASON",
    "INTENT_ACTION_WORDS", "INTENT_BED_WORD", "INVITE_REASON", "RANKING_PRIOR_SCORES", "Rendered", "Renderer",
]


#: **看板(広告面)の注視ゲート**(知覚契約書 §4 段1 の p_see)の既定。``1.0``= 在圏セルの
#: 看板行が必ず観測に入る=**現行のバイト**(D-59 (b) 以前の挙動)。1.0 未満にすると
#: 体×看板×tick の決定論的ベルヌーイで看板行が落ちる。帯の出典は §4 段1
#: (中小媒体 ``P_SEE_MEDIUM_RANGE`` 0.14-0.40 / 大型ビジョン 0.63-0.78)。
#: **既定を 1.0 に置いたのは「切替口は既定不変」の規律**(較正値は腕の側で指定する)。
SIGNAGE_P_SEE_DEFAULT: Final[float] = 1.0

#: 注視ゲートの乱数ドメイン(``core.rng`` のドメイン表・``attention.gate_stage1`` が使う)。
SIGNAGE_P_SEE_DOMAIN: Final[str] = "perception.attention.p_see"


#: **5 段目 5c(D-117)** の活動の種別(親しみの層が「入った回」の看板の露出を種別ごとに数える計数の鍵=
#: ``Renderer.activity_classes``)。move_to=目的地つき移動・wander=あたり・in_shop=在店・in_place=その場・
#: phone=通話/スマホ操作中(旗は無い=該当する体が無い・鍵だけ)・companion_talk=連れとの会話中(``Activity.CONVERSING``)。
#: 〔第 1 期 1-2・決定 10-12 §1-6「係数で持たない」〕看板の注視 p_see に掛けていた**活動の種別の乗数の表**(既定は全部 1.0・
#: 通話 0.49 と連れとの会話 1.39=Hyman 2010 表 2 は腕の値)と、その腕 ``p_see_activity`` は消した(既定のランで効く道が
#: 無かった=byte-check 19 構成で結果不変・記録 ``docs/bench/analysis/wallbounce-1012/p12/README.md``)。0.49・1.39 は
#: パターン台帳 §10 の検証専用の値。気づきの差は目の向き・心の向きの仕組み(CT2)から出す。
P_SEE_ACTIVITY_KINDS: Final[tuple[str, ...]] = (
    "move_to", "wander", "in_shop", "in_place", "phone", "companion_talk",
)


def memory_item_text(
    item: object, *, hhmm: str, poi_names: Sequence[str], place_ids: Sequence[str],
    result_text: Mapping[int, str], max_tokens: int = T.MEMORY_ITEM_MAX_TOKENS,
) -> str:
    """想起した 1 行(``engine.memory.RecallItem`` と同じ欄を持つもの)→ B5「記憶」の項 1 件(6b・v1.2)。

    場所=POI 名(object ≥0)/ 場所の ID(object=−(cell+2) か 行のセル)/ セルが範囲外なら「範囲外」。
    相手=``P-<id>``。結果=``RESULT_TEXT`` の語。1 件が ``max_tokens`` を超えるなら場所名/要旨を末尾から削る
    (宣言)。**⑥ 省略記法**(``N.ABBREVIATIONS``・B5 は列挙行の検査が掛かる): POI 名に禁止語があれば
    その行のセルの ID に替え、要旨に禁止語があれば要旨を載せない(「話した。」)=宣言・expedient
    (意図の行の ``INTENT_FALLBACK_TARGET`` と同じ流儀)。逐次ループ宣言: 削る字数ぶん(≤ 名前の字数)。
    """
    kind = int(getattr(item, "kind"))
    obj = int(getattr(item, "obj"))
    cell = int(getattr(item, "cell"))
    if kind == _STORE_ITEM_KIND:  # 7c(v1.3): 店の評価の行
        return _store_item_text(item, obj, cell, poi_names, place_ids)
    partner = int(getattr(item, "partner"))
    result = int(getattr(item, "result"))
    gist = N.canonical_whitespace(str(getattr(item, "gist", "") or "")).strip().rstrip("。.")
    if any(a in gist for a in N.ABBREVIATIONS):
        gist = ""
    where = ""
    if 0 <= obj < len(poi_names):
        where = N.canonical_whitespace(str(poi_names[obj])).strip()
        if any(a in where for a in N.ABBREVIATIONS):
            where = ""
    if not where:
        c = (-obj - 2) if obj <= -2 else cell
        where = str(place_ids[c]) if 0 <= c < len(place_ids) else T.MEMORY_OUT_OF_AREA_WORD
    event = T.MEMORY_EVENT_WORDS[kind] if 0 <= kind < len(T.MEMORY_EVENT_WORDS) else ""
    who = person_word(partner) if partner >= 0 else ""
    tpl = T.MEMORY_ITEM_TEMPLATES
    res = result_text.get(result, "")
    if kind == 7 and result == 0 and who:  # 成立した会話(engine.memory.EVENT_KINDS["talk"])
        key, var = ("talk", gist) if gist else ("talk_plain", "")
    elif kind in (10, 11):  # 気づき・看板(結果を書かない)
        key, var = "seen", where
    elif who:
        key, var = "person", ""
    else:
        key, var = "place", where

    def fill(v: str) -> str:
        return tpl[key].format(hhmm=hhmm, where=v if key in ("place", "seen") else where, who=who,
                               event=event, result=res, gist=v if key == "talk" else gist)

    text = fill(var)
    while var and ch.estimate_tokens(text) > int(max_tokens):  # 逐次: 削る字数ぶん
        var = var[:-1]
        text = fill(var)
    return text


#: 7c: ``engine.memory.STORE_ITEM_KIND``(描画は engine を import しない=値を写す・テストで一致を見る)。
_STORE_ITEM_KIND: Final[int] = 12
#: 7c: 出どころのビット「自分の訪問」(``engine.store_memory.STORE_SOURCE_BIT["self"]`` の写し)。
_STORE_SELF_BIT: Final[int] = 1


def _store_item_text(item: object, obj: int, cell: int, poi_names: Sequence[str],
                     place_ids: Sequence[str]) -> str:
    """店の評価の行 → 項(v1.3)。自分が行った店=「最近 X に行った(良かった/知っている/よくなかった)。」・
    看板/伝聞だけ=「X を知っている。」か「X は良い/よくないと聞いた。」。≤ 15 tok(店の名を末尾から削る)。
    ⑥ 省略記法は 6b と同じ(店の名に禁止語 → そのセルの ID)。逐次: 削る字数ぶん。
    """
    valence = int(getattr(item, "valence", 0))
    source = int(getattr(item, "source", 0))
    name = ""
    if 0 <= obj < len(poi_names):
        name = N.canonical_whitespace(str(poi_names[obj])).strip()
        if any(a in name for a in N.ABBREVIATIONS):
            name = ""
    if not name:
        name = str(place_ids[cell]) if 0 <= cell < len(place_ids) else T.MEMORY_OUT_OF_AREA_WORD
    tpl = T.MEMORY_ITEM_TEMPLATES
    if source & _STORE_SELF_BIT:
        key, word = "store", T.MEMORY_STORE_VALENCE_WORDS[int(np.sign(valence))]
    elif valence != 0:
        key, word = "store_heard", T.MEMORY_STORE_HEARD_WORDS[int(np.sign(valence))]
    else:
        key, word = "store_known", ""
    text = tpl[key].format(store=name, valence=word)
    while len(name) > 1 and ch.estimate_tokens(text) > int(T.MEMORY_STORE_ITEM_MAX_TOKENS):
        name = name[:-1]
        text = tpl[key].format(store=name, valence=word)
    return text


def compose_memory_line(texts: Sequence[str]) -> tuple[str, int]:
    """項(順位の高い順)→ B5「記憶」の 1 行と載せた項の数(6b・M4)。0 件なら ``("", 0)``。

    チャネル 60 tok は**行全体**(頭の「[B5 記憶] 」を含む)で守る: 項の予算=60−頭の tok で
    ``truncate_lines``(行の途中では切らない)→ 概算 tok の丸めで超える分は末尾の項から落とす。
    逐次ループ宣言: 想起の件数ぶん(≤ 3)。
    """
    head = ch.estimate_tokens(T.TEMPLATES["B5.memory"].format(items=""))
    kept, _rep = ch.truncate_lines(
        list(texts), "B5.memory", limit_tokens=max(0, T.MEMORY_CHANNEL_TOKENS - head)
    )
    while kept:
        line = N.canonical_whitespace(T.TEMPLATES["B5.memory"].format(items="".join(kept)))
        if ch.estimate_tokens(line) <= T.MEMORY_CHANNEL_TOKENS:
            return line, len(kept)
        kept.pop()
    return "", 0


#: **第2波 §2B 項 3(Q31 (b))** B5 に描く空腹の語の段(``--hunger-words``)。``hungry``(**既定**=旧)=
#: ``T.HUNGER_WORD_DRAW_MIN_STAGE``(空腹)以上だけ / ``all``=満腹・ふつうも描く(4 段とも)。
#: 既定の切り替えは食事の束の版上げで確認する(指示書 §8-2)。D-111 の予想表の「閾値超え 11%」は ``hungry``
#: の定義の値。
HUNGER_WORDS_MODES: Final[tuple[str, ...]] = ("hungry", "all")
DEFAULT_HUNGER_WORDS: Final[str] = "hungry"


def check_hunger_words(mode: str) -> str:
    if str(mode) not in HUNGER_WORDS_MODES:
        raise ValueError(f"hunger_words は {HUNGER_WORDS_MODES} のどれか(いま {mode!r})")
    return str(mode)

#: 被招待(§6 起床(ii))の起床理由=``B6.wake`` の ``{reason}`` に入る**値**。
#: **テンプレ本体ではない**(``templates.TEMPLATES``/``WAKE_REASON_TEXT`` は不変=
#: ``template_sha256`` は動かない)。``RESULT_OPTIONS``(いま可能3語)と同じ扱いで、
#: 文面は自前=**expedient**(契約書は起床条件(ii)を列挙するだけで文面を与えない)。
#: 招待者を名指せないと承諾できない(行動契約書 §1-2 対象スロット:
#: 承諾=「行動: 会話 **対象: 招待者**」・``engine.run._settle_pending_invites``)。
INVITE_REASON: Final[str] = (
    "{person}があなたに話しかけました。"
    "応じるなら 行動: 会話 対象: {person}、応じないなら別の行動を選びます。"
)

#: 〔第 1 期 1-8b 発話の口〕届いた発話の行(B6 の末尾・腕 ``--speech-port on`` のランだけ)。**テンプレ本体ではない**
#: (``templates.TEMPLATES`` は不変=``template_sha256`` は動かない・``INVITE_REASON`` と同じ扱い)。素性タグは短い形
#: ``〔発話・命令文除去〕``(親の判断=B6 の枠 80 tok)。本文は描くときに命令文を文単位で除く(憲法 6・
#: ``strip_speech_imperatives``)。文面は実装役の自前(台帳の行=``engine/speech/layer.py`` の expedient)。
SPEECH_HEARD_LINE: Final[str] = "[B6 発話] {person}のひと言:〔発話・命令文除去〕{body}"
#: 〔第 1 期 1-8b〕会話の番の呼び出しだけ B6 の末尾に足す出力の欄の指示(語彙 v3・10 tok=親の判断)。
#: ``llm.contract.SPEECH_FIELD_LINE`` と同じ文字列(層契約により二重定義=``tests/engine/speech/test_speech_port_schema.py``
#: が突き合わせる)。共有部(B0〜B4b)は変えない(B6 は個体ブロック=残り 5 tok の共有の予算を使わない)。
SPEECH_FIELD_LINE: Final[str] = "2行目末尾に ひと言:<20字内|なし>"
#: 〔第 1 期 1-8b 検収 中1〕**発話の行だけ**に足す命令文の型(看板・広告の表 ``attention.IMPERATIVE_PATTERNS`` は変えない=
#: 既定の描画は不変)。て形の依頼(「〜して。」「〜して、」「〜してね」・「〜んで」「〜いで」)・「無視」「忘れて」・英語の
#: ignore/forget/disregard。**過剰に落とす側**(接続の「〜て、」の平叙文も落ちる)=台帳の expedient。
SPEECH_IMPERATIVE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"(?:て|んで|いで)(?:ね|よ|な|ちょうだい)?(?:[、,。!?！?…]|$)"),
    re.compile(r"無視|忘れ(?:て|ろ|なさい)"),
    re.compile(r"(?i)\b(?:ignore|forget|disregard)\b"),
)
_SPEECH_SENTENCE_SPLIT: Final[re.Pattern[str]] = re.compile(r"(?<=[。!?！?])")


def strip_speech_imperatives(text: str) -> StripReport:
    """発話の本文 → 看板と同じ表(``strip_imperatives``)で落とした後、発話だけの型(``SPEECH_IMPERATIVE_PATTERNS``)の文も落とす。

    逐次ループ宣言(P4): 文数ぶん(1 発話は 20 字前後=数文)。
    """
    base = strip_imperatives(text)
    kept: list[str] = []
    removed = list(base.removed)
    for sent in (x for x in _SPEECH_SENTENCE_SPLIT.split(base.kept) if x.strip()):
        if any(pt.search(sent) for pt in SPEECH_IMPERATIVE_PATTERNS):
            removed.append(sent.strip())
        else:
            kept.append(sent.strip())
    return StripReport(kept="".join(kept), removed=tuple(removed))

#: 失敗コード → 「いま可能」3語(行動契約書 §6・**待機を必ず含む**=失敗しない行動・expedient)。語彙 v1/v2 の表。
#: 〔11-03 棚卸し A §4-2〕語彙 v3 には待機が無く、下の ``RESULT_OPTIONS_V3`` が待機を「なし」に畳む(=なしを必ず含む)。
RESULT_OPTIONS: Final[Mapping[int, tuple[str, str, str]]] = {
    ResultCode.MONEY_SHORT: ("移動", "待機", "休憩"),
    ResultCode.OUT_OF_STOCK: ("移動", "待機", "購入"),
    ResultCode.CLOSED: ("移動", "待機", "休憩"),
    ResultCode.TRAIN_FULL: ("待機", "移動", "休憩"),
    ResultCode.FARE_SHORT: ("移動", "待機", "休憩"),
    ResultCode.NO_TRAIN: ("待機", "移動", "休憩"),
    ResultCode.NO_STOP: ("移動", "待機", "乗車"),
    ResultCode.UNREACHABLE: ("移動", "待機", "休憩"),
    ResultCode.INTERRUPTED: ("移動", "待機", "休憩"),
    ResultCode.PARTNER_BUSY: ("待機", "移動", "会話"),
    ResultCode.REFUSED: ("移動", "待機", "退去"),
    ResultCode.PARTNER_GONE: ("移動", "待機", "会話"),
    ResultCode.NO_BED: ("移動", "待機", "休憩"),
    ResultCode.NO_PERMISSION: ("移動", "待機", "退去"),
    ResultCode.LOST_ARBITRATION: ("待機", "移動", "休憩"),
    ResultCode.UNDEFINED_ACTION: ("移動", "待機", "休憩"),
    ResultCode.BAD_TARGET: ("移動", "待機", "休憩"),
    # 段 2c: 遠すぎて時間切れ(経路は在る)=経路なしと同じ 3 語
    ResultCode.TOO_FAR: ("移動", "待機", "休憩"),
}


# ------------------------------------------------------------------ 語彙 v3(二層の段 2)
#
# 正典: 二層の実装アジェンダ §6「段 2 の発注範囲」(renderer の ``RESULT_OPTIONS``/
# ``DEFAULT_OPTIONS`` は v3=なし/移動・``ACTIVITY_WORDS``)。**作り方は機械的**: v1 の表の語を
# ``llm.contract.VOCAB_COMPAT`` で v3 の語彙へ読み替えて(待機/休憩/降車 → なし)重複を落とす
# (段 1 の ``FALLBACK_ACTIONS_V3`` と同じ規則)。層契約(perception は llm を import できない)
# のため**字面で持つ**=一致はテストが機械検査する。v1/v2 の表と描画は 1 バイトも変わらない。
def _to_v3(words: tuple[str, ...]) -> tuple[str, ...]:
    out: list[str] = []
    for w in words:
        v = "なし" if w in ("待機", "休憩", "降車") else w
        if v not in out:
            out.append(v)
    return tuple(out)


#: 失敗コード → 「いま可能」(語彙 v3)。
RESULT_OPTIONS_V3: Final[Mapping[int, tuple[str, ...]]] = {
    k: _to_v3(v) for k, v in RESULT_OPTIONS.items()
}
#: 表に無い失敗コードの「いま可能」(語彙 v3=``templates.DEFAULT_OPTIONS`` の読み替え)。
DEFAULT_OPTIONS_V3: Final[tuple[str, ...]] = _to_v3(tuple(T.DEFAULT_OPTIONS))
#: 満了入口の起床理由(**テンプレ本体ではない**=``INVITE_REASON`` と同じ扱い・語彙 v3 の
#: 活動層が立つランでだけ出る・文面は自前=expedient)。
ACTIVITY_EXPIRY_REASON: Final[str] = (
    "決めていた過ごし方の区切りに来たため、次の行動を決める必要があります。"
)
#: 行為コード → 語(**語彙 v3 の語**・層契約(perception は llm を import できない)のため字面で持つ
#: =``llm.contract.ACTION_CODES`` との一致はテストが機械検査する)。
INTENT_ACTION_WORDS: Final[Mapping[int, str]] = {
    3: "購入", 24: "食事", 22: "並ぶ", 5: "会話", 11: "就寝",
}
#: 寝床(自宅セル)の対象の語。
INTENT_BED_WORD: Final[str] = "自宅"


#: チャネル → 既定素性のスコア(ablation ① の行の並び・**起動時に 1 回だけ**計算)。
RANKING_PRIOR_SCORES: Final[Mapping[str, float]] = _prior_scores()

# ------------------------------------------------------------------ 描画結果
@dataclass(frozen=True)
class Rendered:
    """1 起床ぶんの描画結果。

    Attributes:
        agent_id / tick: どの個体のどの tick か。
        blocks: ブロック id → 描画バイト列(**順序=``templates.BLOCK_IDS``**)。
        text: 連結した本文(ブロック間は LF)。
        block_hashes: ブロック id → xxh64(三役の 1 本目)。
        prefix_key: ブロックハッシュ列の合成鍵(prefix キャッシュ鍵)。
        prompt_hash: 連結バイト列の blake3(16 進・再現性の指紋)。
        tokens_est: ブロック id → 推定トークン。
        group_tokens: 予算グループ → 推定トークン(実効ゲート)。
        truncations: チャネル切り詰めの記録。
        cache_hits / cache_misses: この描画で引いた共有ブロックの命中数。
    """

    agent_id: int
    tick: int
    blocks: "OrderedDict[str, bytes]"
    text: str
    block_hashes: Mapping[str, int]
    prefix_key: int
    prompt_hash: str
    tokens_est: Mapping[str, int]
    group_tokens: Mapping[str, int]
    truncations: tuple[ch.TruncationReport, ...] = ()
    cache_hits: int = 0
    cache_misses: int = 0
    #: 記憶 第 1 段 6b: B5「記憶」行に載せた記憶の行番号(テープ版 3 の ``recalled_rows``)。
    recalled_rows: tuple[int, ...] = ()
    #: テープ版 4(10e・E5・A8): 引いた記憶の同定(``recalled_rows`` と同じ並び)。最初に書かれた時刻(通しの T)・
    #: 種類(``memory.EVENT_KINDS``・店の行は ``STORE_ITEM_KIND``)・対象(``mem_object`` の符号化・店の行は POI)。
    recalled_first_tick: tuple[int, ...] = ()
    recalled_kind: tuple[int, ...] = ()
    recalled_object: tuple[int, ...] = ()
    #: テープ版 4: 「(知人)」の印を見せた相手の体 id(B5 の本文に出た順・重複なし)。
    acquaintance_ids: tuple[int, ...] = ()
    #: 第 1 期 1-2: 描いた知覚の事実(``facts.Percept``・刻みの中の一時=判断の入力と ``TickScratch.percepts`` へ渡す)。
    percept: Percept | None = None

    @property
    def tokens_total(self) -> int:
        return int(sum(self.tokens_est.values()))

    def within_group_budgets(self) -> bool:
        return all(v <= T.GROUP_TOKEN_BUDGET[k] for k, v in self.group_tokens.items())

    def shared_static_bytes(self) -> bytes:
        """B0-B4b の連結(§2.4 ⑧ のバイト一致検査に使う)。"""
        return b"\n".join(self.blocks[b] for b in T.BLOCK_IDS if b not in ("B5", "B6"))
DEFAULT_NEAR_TIEBREAK: Final[str] = "hash"
DEFAULT_NEAR_ORDER: Final[str] = "distance"


class Renderer(PerceptScene, SignageNotice):
    """観測レンダラ(1 起床=1 呼び出し)。

    Example:
        >>> from shibuya.world.state import World
        >>> from shibuya.agents.state import AgentState
        >>> w = World.synthetic(n_cells=9, seed=1)
        >>> a = AgentState(4)
        >>> a.cell[:] = 0
        >>> r = Renderer(w, a, seed=7)
        >>> out = r.render(0, tick=750, wake_reason=3)
        >>> out.text.splitlines()[0].startswith("あなたは渋谷の街にいる")
        True
    """
    def __init__(
        self,
        world: World,
        agents: AgentState,
        assets: PerceptionAssets | None = None,
        clock_fn: Callable[[int], datetime] | None = None,
        seed: int | str = 0,
        *,
        acquaintances: Mapping[int, Sequence[int]] | None = None,
        watched_by: np.ndarray | None = None,
        budget_mode: ch.BudgetMode | str = ch.BudgetMode.FIXED_SLOTS,
        strict_group_budget: bool = True,
        signage_enabled: bool = True,
        signage_p_see: float = SIGNAGE_P_SEE_DEFAULT,
        intent_mode: str = T.DEFAULT_INTENT_MODE,
        vocab_version: str = T.DEFAULT_VOCAB_VERSION,
        role_words: bool | str = False,
        near_tiebreak: str = DEFAULT_NEAR_TIEBREAK,
        near_salt: bytes | None = None,
        near_order: str = DEFAULT_NEAR_ORDER,
        hunger_words: str = DEFAULT_HUNGER_WORDS,
        day_kind_fn: Callable[[int], str] | None = None,
    ) -> None:
        """
        Args:
            world: 世界状態(セル密度・騒音段・POI 営業)。
            agents: 個体 SoA。
            assets: 知覚側資産。None なら ``PerceptionAssets.synthetic(world)``。
            clock_fn: tick → 世界内日時。None なら ``DEFAULT_START_DATETIME + tick 分``。
            seed: 乱数のマスターシード(注意ゲートの抽選に使う)。
            acquaintances: 個体 → 知人の agent_id(§3 人物④「知人は常に掲載」)。
            watched_by: ``(n,)`` 被注視人数(T2 の転置。None なら 0)。
            budget_mode: §3.2 の義務 ablation の切替(``ch.BudgetMode`` か
                ``"fixed"``/``"ranking"``)。既定=固定枠(現行の描画)。
            strict_group_budget: True でグループ予算超過を例外にする(既定)。
            signage_enabled: 看板・広告面(B2.signage)を描くか。知覚契約書 §8 第1陣 **⑥
                「広告ゼロ」**の切替口。``False`` で W14 凍結文も合成文も載せず、全セルで
                ``B2.signage_empty``(=「見える表示はありません」)にする。既定 True=
                現行の描画で**1 バイトも変わらない**。テンプレ本体は触らないので
                ``template_sha256`` は不変・規約⑧(セルの情報しか使わない)も不変。
            signage_p_see: **看板の注視ゲート**(知覚契約書 §4 段1 の視認確率 p_see・
                D-59 (b) ユーザー決定 2026-09-17)。在圏セルの看板行を観測へ入れるかを
                **体×看板×tick の決定論的ベルヌーイ**で決める。既定 1.0=常に入れる
                =**現行のバイトで 1 バイトも変わらない**(抽選も引かない)。0.0 で
                全員・全 tick 落ちる(=⑥ 広告ゼロと同じ描画)。抽選は
                ``attention.gate_stage1``(``core.rng`` の Philox・ドメイン
                ``perception.attention.p_see``・カウンタ ``(tick, agent_id, poi_id)``)
                なので、同じ seed・同じ tick・同じ体・同じ看板は常に同じ結果
                (テープから再現できる)。**看板の無いセルでは抽選を引かない**
                (描画が変わらないため)。落ちた看板行は ``B2.signage_empty`` になり、
                **空いた枠は他のチャネルへ回らない**(固定枠。枠の再配分は D-60 の別議論。
                ただし ``budget_mode='ranking'`` は池を分け合う設計なので ⑥ と同じく
                他チャネルが空きを取りうる)。
                注: 1.0 未満では **§2.4 ⑧「同セル同時間帯の 2 体で B0-B4b バイト一致」が
                成り立たない**(注視は体ごとの事象だから)。同一セルの B2 は
                **看板あり/なしの 2 変種**に分かれる=共有 prefix の断片化は高々 2 倍。
            intent_mode: **AB7 自由意図の腕**の切替口(``"vocab"`` | ``"open"`` | ``"hint"``)。
                ``"open"`` で B0 の出力規約を ``templates.OUTPUT_SPEC_OPEN``(``行動:`` の
                1 行だけが「いま自分がしたいことを10字以内の動詞句で」)に差し替える。
                ``"hint"``(AB7b)は ``templates.OUTPUT_SPEC_HINT``= 語彙を例として見せた
                まま「当てはまる語が無いときだけ 10 字以内の動詞句で」を許す中間の腕。
                既定 ``"vocab"`` は現行の 24 語ホワイトリスト提示=**1 バイトも変わらない**。
                テンプレ本体(``TEMPLATES``)は触らないので ``template_sha256`` も不変。
                仕様書 ``docs/design/v2-open-intent-arm-spec.md`` §2。
            vocab_version: **行動語彙の版**(D-71 §3 F・``"v1"`` | ``"v2"``)。``"v2"`` で
                B0 の出力規約に 13 語目「食事」が載る(``templates.OUTPUT_SPEC_V2``)。
                既定 ``"v1"`` は現行の 24 語提示=**1 バイトも変わらない**。``"open"`` 腕は
                語彙を見せないので v1/v2 で B0 は同一(差は段0 辞書とエンジン側)。
            near_tiebreak: B5 近接行の**距離の同点**の切り方(第300 Q107)。``"hash"``(既定)= 同点を
                ``near_salt`` の決定論ハッシュ(観る体 × 相手)で撹拌 / ``"id"`` = 旧挙動(セル内の並び=
                行番号の順)。**文面・並び(id 昇順)は変えない**=採る人だけ。同点が k 人目の境で起きない
                描画は両方で同じ。
            near_salt: 撹拌の salt(``engine.run`` は run_salt を渡す)。``None`` なら ``seed`` から
                ``engine.run.run_salt_for`` と同じ式で作る。
            near_order: B5 近接行の**並び**(第304 Q130)。``"distance"``(既定)= 距離の昇順・同点は
                ``near_tiebreak`` の順 / ``"id"`` = 旧挙動(行番号の昇順)。焦点は両方で先頭。文面は変えない。
            day_kind_fn: 第 1 期 1-2: 通しの刻みの番号 → 暦の日の種類(``Percept.time_view.day_kind``。組み立てが暦の
                ``SimCalendar.day_kind`` を渡す)。``None`` なら日の種類は空(None)。描画の文は読まない=バイトは変わらない。
        """
        PerceptScene.__init__(self, world, agents, assets, clock_fn, seed, acquaintances=acquaintances,
                              watched_by=watched_by, signage_enabled=signage_enabled, near_tiebreak=near_tiebreak,
                              near_salt=near_salt, near_order=near_order, day_kind_fn=day_kind_fn)
        self.seed = seed
        self.budget_mode = ch.BudgetMode.parse(budget_mode)
        self.strict_group_budget = strict_group_budget
        self.signage_p_see = check_signage_p_see(signage_p_see)
        #: 6b の計数(記憶の行を載せた描画・想起の件数・行の tok・予算で削った/載せなかった)。
        self.memory_lines = 0
        self.memory_items = 0
        self.memory_line_tokens: dict[int, int] = {}
        self.memory_items_dropped_for_budget = 0
        self.memory_items_dropped_for_channel = 0
        self.memory_lines_over_budget = 0
        self.intent_mode = T.check_intent_mode(intent_mode)
        self.vocab_version = T.check_vocab_version(vocab_version)
        #: D-113 ④(第269): B0 の末尾に役割語の 1 行を足すか。レンダラの既定は False(描画バイトの
        #: 凍結を保つ)。**ランの既定は True**(``engine.run.run_day(role_words=True)``)。
        self.role_words = T.check_role_words(role_words)
        # 既定(vocab × v1)は ``TEMPLATES["B0.system"]`` と同一文字列=描画バイト不変
        # (AB7・語彙 v2)。
        self._b0 = N.canonical_whitespace(
            T.b0_system(self.intent_mode, self.vocab_version, self.role_words)
        ).encode("utf-8")
        self._b4b = N.canonical_whitespace(
            T.TEMPLATES["B4b.near_empty"]
        ).encode("utf-8")
        #: **5 段目 5a(D-118 K2)**: 空腹を**語**で描くか(``energy_columns`` のラン=
        #: ``--hunger-model energy``)。``hunger`` はそのランでは語の段の写し(1/5/8/10)なので、
        #: 数値の代わりに ``T.HUNGER_WORDS`` の語を ``T.HUNGER_WORD_DRAW_MIN_STAGE`` 以上だけ描く。
        #: 欄の無いラン(v1)は従来の「空腹はNで閾値を超えています。」=**1 バイトも変わらない**。
        self._hunger_words: bool = bool(getattr(agents, "energy_columns", False))
        #: 第2波 §2B 項 3: 描く最小の段(``hungry``=None=旧の定数 / ``all``=0)。
        self.hunger_words: str = check_hunger_words(hunger_words)
        self._hunger_min_stage: int | None = 0 if self.hunger_words == "all" else None
        self._b1_cache: dict[int, bytes] = {}
        #: 鍵は ``(セル, 看板を見たか)``。既定(p_see 1.0)は第2要素が常に True=
        #: セルだけで引くのと同じ(命中率も同じ)。
        self._b2_cache: dict[tuple[int, bool], bytes] = {}
        self._b4_cache: dict[tuple[int, int], bytes] = {}
        #: ablation ①(単一ランキング)のセル依存ブロック。B2 が B4 と同じ池を分けるので
        #: 鍵は ``(セル, B4 欄ハッシュ)``(固定枠の ``_b2_cache`` はセルだけ)。
        self._rank_cell_cache: dict[
            tuple[int, int, bool], tuple[dict[str, bytes], tuple[ch.TruncationReport, ...]]
        ] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.renders = 0
        self.truncation_count = 0
        #: 段 2c: 意図の 1 行を載せた回数 / 個体群の予算で載せなかった回数。
        self.intent_lines = 0
        self.intent_lines_over_budget = 0
        #: 注視ゲートの抽選回数(看板のあるセルで p_see<1.0 のときだけ増える)。
        self.signage_gate_draws = 0
        #: そのうち**通った**(看板行を載せた)回数。既定のランでは 0/0。
        self.signage_gate_shown = 0
        #: 〔1-8b 検収 低8〕B6 に実際に載せた発話を口へ報告する口 ``(体, 載せた目印, 本文が空(全部が命令文)の数, 予算で外した数)``
        #: (組み立てが腕 on のランだけ ``SpeechPort.report_shown`` を差し込む・``None``=報告しない)。
        self.heard_seen_fn: Callable[[int, tuple[tuple[int, int], ...], int, int], None] | None = None
        #: 〔1-8b〕会話の番の呼び出しの B6 に出力の欄の指示(``SPEECH_FIELD_LINE``)を足すか(腕 on・語彙 v3 のランだけ真)。
        self.speech_field = False
        #: 〔1-8b〕B6 に足した発話の行(届いた発話と出力の欄の指示)の数 / 個体群の予算 300 を超えるので外した描画の数。
        self.speech_lines = 0
        self.speech_lines_over_budget = 0
        #: 〔6-4 C1〕B6 に足した連絡の行の数 / 個体群の予算で外した描画の数 / 割り込めなかった周りの出来事のあった描画の数。
        self.contact_lines = 0
        self.contact_lines_over_budget = 0
        self.contact_unnoticed_renders = 0

    # ---------------------------------------------------------- 本体
    def render(
        self,
        agent_id: int,
        tick: int,
        wake_reason: int | str = 3,
        last_result: int | None = None,
        last_action: str | None = None,
        inviter: int | None = None,
    ) -> Rendered:
        """1 個体・1 起床ぶんの観測を描画する(第 1 期 1-2: 状態 → ``Percept``=``perceive`` → 文=``render_percept``)。

        Args:
            agent_id: 起床した個体。
            tick: 起床 tick。
            wake_reason: ``agents.state.WakeCondition`` の値、または文言そのもの。
            last_result: ``ResultCode``(None なら ``agents.last_result`` を読む)。
            last_action: 直前に**試みた**行動語(None なら ``agents.activity`` で代用)。
                C2 の SoA は「直前に試みた行動」を持たない(``activity`` は現在の状態)ので、
                正確な文面には engine 側からの受け渡しが要る(親への hook 要求)。
            inviter: **招待者の個体 id**(§6 起床(ii) 被招待。招待が無ければ None か負値)。
                与えると B6 起床行が ``INVITE_REASON``(招待者を名指す文)に替わる。
                ``wake_reason`` より優先する(被招待は起床理由そのものだから)。

        Returns:
            描画の結果(``Rendered.percept`` に描いた ``Percept``)。

        Note:
            逐次ループ宣言(P4)1: **1 起床につき 1 回**。個体数ぶんのループは持たない。
        """
        if self._tickc.tick != int(tick):
            # 〔段 5-1b 検収 L4〕前計算の無い刻みの道は ``los_stage`` を渡さない=nav1 のランでここを通ると B4 の密度の段が前の式
            # (density ÷ 歩ける面積)になる。今の回り方(毎刻み perceive_prepare が前計算する)では通らない(単体の描画と試験の道だけ)
            self.prepare_tick(int(tick))
        hits0, misses0 = self.cache_hits, self.cache_misses
        p = self.perceive(
            agent_id, tick, wake_reason=wake_reason, last_result=last_result, last_action=last_action,
            inviter=inviter,
        )
        return self._render_percept(p, hits0, misses0)

    # ---------------------------------------------------------- 第 1 期 1-2: 知覚の事実 → 文(B0〜B6)
    def render_percept(self, p: Percept) -> Rendered:
        """知覚の事実 → B0〜B6(文の描き方)。``p`` は今の刻みの物だけ(刻みの外で残らない=違えば ``ValueError``)。

        描く側が引くのは ``p`` と、テンプレ・知覚の静的資産(名・帯・凍結文・店の営業時間)・キャッシュ(セルと刻みで
        決まる事実を描いた文)だけ。個体 SoA・世界の動く状態・層の口は読まない(B4b の文は ``prepare_tick`` が描いた物を
        セルで引く=記録の残した直接読み)。
        """
        return self._render_percept(p, self.cache_hits, self.cache_misses)

    def draw(self, p: Percept) -> str:
        """``facts.PerceptDrawing`` の口: 知覚の事実 → 本文(B0〜B6 を LF でつないだ物=``Rendered.text``)。"""
        return self.render_percept(p).text

    def _render_percept(self, p: Percept, hits0: int, misses0: int) -> Rendered:
        tc = self._tickc
        if int(p.step) != int(tc.tick):
            raise ValueError(
                f"Percept は刻みの中だけの物(描く刻み {tc.tick}・Percept の刻み {p.step}): 刻みをまたいで描かない"
            )
        i = int(p.agent_id)
        cell = int(p.cell)
        seen = bool(p.signage_shown)
        blocks: "OrderedDict[str, bytes]" = OrderedDict()
        trunc: list[ch.TruncationReport] = []
        ranking = self.budget_mode is ch.BudgetMode.SINGLE_RANKING
        # ablation ①: セル依存(B2/B4/B4b)は**1 本の池**なので 3 ブロックを一緒に組む。
        cellb = self._cell_blocks_ranked(p.scene, trunc, seen) if ranking else None
        b6 = self._b6(p)
        blocks["B0"] = self._b0
        blocks["B1"] = self._b1(p.self_view.kind)
        blocks["B2"] = cellb["B2"] if cellb is not None else self._b2(cell, trunc, seen)
        blocks["B3"] = self._draw_b3(p.time_view)
        blocks["B4"] = cellb["B4"] if cellb is not None else self._draw_b4(p.scene, trunc)
        blocks["B4b"] = cellb["B4b"] if cellb is not None else tc.b4b.get(cell, self._b4b)
        blocks["B5"] = (
            self._b5_ranked(p, trunc, ch.estimate_tokens(b6.decode("utf-8")))
            if ranking
            else self._b5(p, trunc)
        )
        # 段 2c: 意図を持つ体だけ B5 に「いま <行為> のため <対象> へ向かっている」の 1 行
        blocks["B5"] = self._with_intent_line(p, blocks["B5"], b6)
        # 記憶 第 1 段 6b: 想起した記憶を B5 の**最後**に 1 行(on のランだけ・0 件なら出さない)
        recalled: tuple[int, ...] = ()
        recalled_meta: tuple[tuple[int, int, int], ...] = ()
        if p.memories is not None:
            blocks["B5"], recalled, recalled_meta = self._with_memory_line(p, blocks["B5"], b6)
        if p.heard_speech or self.speech_field:  # 第 1 期 1-8b(腕 on のランだけ): 発話の行は B5 を組んだ後に足す
            b6 = self._with_speech_lines(p, blocks["B5"], b6)
        blocks["B6"] = b6
        if self.contact_fn is not None:  # 〔第 6 期 6-4 C1〕腕 c1 のランだけ: 周辺視・割り込めなかった出来事・連絡の行
            self._contact_blocks(p, blocks, trunc)

        # §2.4 ⑧: B0-B4b に個体依存語が無いこと(機械検査)
        shared_ids = [b for b in T.BLOCK_IDS if b not in ("B5", "B6")]
        shared = b"\n".join(blocks[b] for b in shared_ids)
        N.assert_no_agent_dependent_words(shared.decode("utf-8"))
        # §2.4 ⑥: 列挙ブロックに省略記法が無いこと(層2指摘で描画経路に結線)。
        # B2 は OSM 由来の固有名詞(「…等」を含む店名)が乗るため対象外=テンプレ側の列挙構造にのみ課す(expedient・登録簿)。
        for b in ("B4", "B4b", "B5"):
            N.assert_no_abbreviation(blocks[b].decode("utf-8"), b)

        tokens = {b: ch.estimate_tokens(blocks[b].decode("utf-8")) for b in T.BLOCK_IDS}
        groups: dict[str, int] = {"shared_static": 0, "cell": 0, "individual": 0}
        for b, t in tokens.items():
            groups[T.BLOCK_GROUP[b]] += t
        if self.strict_group_budget:
            for g, v in groups.items():
                if v > T.GROUP_TOKEN_BUDGET[g]:
                    raise ValueError(
                        f"§2.2 予算超過: グループ {g} が {v} tok(上限 {T.GROUP_TOKEN_BUDGET[g]})"
                    )

        bh = {b: H.block_hash(blocks[b]) for b in T.BLOCK_IDS}
        text = "\n".join(blocks[b].decode("utf-8") for b in T.BLOCK_IDS)
        self.renders += 1
        self.truncation_count += sum(1 for r in trunc if r.truncated)
        return Rendered(
            agent_id=i,
            tick=int(p.step),
            blocks=blocks,
            text=text,
            block_hashes=bh,
            prefix_key=H.prefix_key([bh[b] for b in shared_ids], shared_ids),  # 共有 prefix(B0-B4b)のみ=§5
            prompt_hash=blake3_hex(b"\n".join(blocks[b] for b in T.BLOCK_IDS)),
            tokens_est=tokens,
            group_tokens=groups,
            truncations=tuple(trunc),
            recalled_rows=recalled,
            recalled_first_tick=tuple(m[0] for m in recalled_meta),
            recalled_kind=tuple(m[1] for m in recalled_meta),
            recalled_object=tuple(m[2] for m in recalled_meta),
            acquaintance_ids=acquaintance_ids_in(blocks["B5"]),
            cache_hits=self.cache_hits - hits0,
            cache_misses=self.cache_misses - misses0,
            percept=p,
        )

    # ---------------------------------------------------------- 各ブロック
    def _b1(self, kind: int) -> bytes:
        got = self._b1_cache.get(kind)
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        word = T.KIND_WORDS[kind] if 0 <= kind < len(T.KIND_WORDS) else T.KIND_WORDS[1]
        out = N.canonical_whitespace(T.TEMPLATES["B1.kind"].format(kind=word)).encode("utf-8")
        self._b1_cache[kind] = out
        return out

    def _b2(
        self, cell: int, trunc: list[ch.TruncationReport], shown: bool = True
    ) -> bytes:
        """B2(地物)。``shown=False``= **この体のこの tick は看板を見なかった**
        (D-59 (b) の注視ゲート)。既定 True=現行の描画。
        """
        got = self._b2_cache.get((cell, shown))
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        A = self.assets
        lines: list[str] = []
        if 0 <= cell < A.n_cells:
            band = int(self.world.assets.cell_band[cell])
            lines.append(
                T.TEMPLATES["B2.place"].format(
                    place_id=A.place_ids[cell], band=T.BAND_WORDS.get(band, "地上")
                )
            )
            ground = T.GROUND_WORDS.get(band, T.GROUND_WORDS[0]) if bool(
                A.has_street[cell]
            ) else T.GROUND_NO_STREET
            kept, rep = ch.truncate_lines([ground], "B2.ground")
            trunc.append(rep)
            if kept:
                lines.append(T.TEMPLATES["B2.ground"].format(ground=kept[0]))
            # 可視物: **W15 の凍結セル静的文が在ればそれ**・無ければ合成の可視物リスト。
            # 凍結文は ``B2.visible`` の枠(§3.2・60 tok)を占める(生成側の上限は 45 tok=
            # B2 予算 150 − 実資産での他行最大。枠を超えた文は切り詰めで落ち合成文へ戻る)。
            # テンプレは変えない。
            static = self._visible_static(cell)
            used_static = False
            if static:
                kept, rep = ch.truncate_lines([static], "B2.visible")
                trunc.append(rep)
                if kept:
                    lines.append(T.TEMPLATES["B2.visible"].format(items=kept[0]))
                    used_static = True
            if not used_static:
                # 可視物 上位3(可視視点数の降順→ID 昇順は資産側で確定済み)
                names = self._visible_names(cell)
                kept, rep = ch.truncate_lines(names, "B2.visible")
                trunc.append(rep)
                lines.append(
                    T.TEMPLATES["B2.visible"].format(items=N.LIST_SEPARATOR.join(kept))
                    if kept
                    else T.TEMPLATES["B2.visible_empty"]
                )
            # 看板(a)=店舗基本属性 1 件(素性タグは凍結テンプレ側・命令文除去を掛ける)
            lines.append(self._signage(cell, shown))
            # 地物・ランドマーク・出口
            kept, rep = ch.truncate_lines(list(A.visible_landmark[cell]), "B2.landmark")
            trunc.append(rep)
            lines.append(
                T.TEMPLATES["B2.landmark"].format(items=N.LIST_SEPARATOR.join(kept))
                if kept
                else T.TEMPLATES["B2.landmark_empty"]
            )
        else:
            lines.append(T.TEMPLATES["B2.place"].format(place_id="なし", band="地上"))
            lines.append(T.TEMPLATES["B2.visible_empty"])
            lines.append(T.TEMPLATES["B2.signage_empty"])
            lines.append(T.TEMPLATES["B2.landmark_empty"])
        out = N.join_lines(lines).encode("utf-8")
        self._b2_cache[(cell, shown)] = out
        return out

    def _signage(self, cell: int, shown: bool = True) -> str:
        """看板(a): そのセルで最も可視の店舗 1 件の店頭表示。

        **W14 で凍結された文面が在ればそれを使い**、無ければ従来の合成文(店名+営業時間)を
        使う(切替は ``world_dir`` に ``w14_signage.parquet`` が在るかだけで決まる)。
        凍結文にも命令文除去とチャネル枠の切り詰めを掛ける(憲法6・多重防御。W14 のゲートを
        通っていれば no-op)。

        §3.2 の「看板・広告面1件 25 tok」は**内容**(店名+属性)に掛ける。ブロックラベルと
        凍結された素性タグは全描画に共通の固定オーバーヘッドなので、ブロック総額(B2 150)側で
        見る(解決した曖昧点・親へ報告)。

        Args:
            shown: 注視ゲート(§4 段1・D-59 (b))を通ったか。``False`` は
                ``B2.signage_empty``=「見える表示はありません」。**枠は他へ回さない**。
        """
        if not shown:
            return T.TEMPLATES["B2.signage_empty"]
        body = self._signage_body(cell)
        if body is None:
            return T.TEMPLATES["B2.signage_empty"]
        kept, _ = ch.truncate_lines([body], "B2.signage")
        if kept:
            return T.TEMPLATES["B2.signage"].format(body=kept[0])
        return T.TEMPLATES["B2.signage_empty"]

    # ---------------------------------------------------------- 素材(固定枠と単一ランキングで共有)
    def _visible_static(self, cell: int) -> str:
        """W15 の凍結セル静的文(無ければ空文字)。"""
        A = self.assets
        return A.cell_static[cell] if cell < len(A.cell_static) else ""

    def _visible_names(self, cell: int) -> list[str]:
        """可視の店舗・施設(可視視点数の降順→ID 昇順は資産側で確定済み)。"""
        A = self.assets
        return [A.poi_name[j] + "の店頭" for j in A.visible_poi[cell]]

    def _b3(self, tc: _TickCache) -> bytes:
        """B3(時刻・天候・暑さ)。第 1 期 1-2: 刻み → ``TimeView``(``_time_view``)→ 文(``_draw_b3``)。"""
        return self._draw_b3(self._time_view(tc))

    def _draw_b3(self, tv: TimeView) -> bytes:
        """``TimeView`` → B3 の文(時と分は 5 分に切り捨てた値の表記=``normalize.format_time`` と同じ)。

        描いた文は刻みの中だけ ``TimeView`` の値で引く(同じ刻みの全員で 1 回だけ描く・鍵は描く入力そのもの)。
        """
        memo = self._tickc.b3_text
        got = memo.get(tv)
        if got is not None:
            return got
        out = N.join_lines([
            T.TEMPLATES["B3.time"].format(hour=str(int(tv.hour)), minute=f"{int(tv.minute):02d}"),
            T.TEMPLATES["B3.weather"].format(weather=tv.weather, daylight=tv.daylight),
            T.TEMPLATES["B3.heat"].format(heat=tv.heat),
        ]).encode("utf-8")
        memo[tv] = out
        return out

    def _b4(self, cell: int, tc: _TickCache, trunc: list[ch.TruncationReport]) -> bytes:
        """B4(密度・騒音・顕著)。第 1 期 1-2: セル → ``SceneView``(``_scene``)→ 文(``_draw_b4``)。"""
        return self._draw_b4(self._scene(cell, tc), trunc)

    def _scene_is_shared(self, scene: SceneView) -> bool:
        """〔第 6 期 6-4 C1〕場面がこの刻みのセルの共有の物(``_scene`` が作った物)か。目と心の向きの写し(腕 c1 の
        ``coarsen`` が顕著行為を落とした場面)は共有でない=セルのキャッシュを読まず書かない(同じセルのほかの体の描画を汚さない)。
        既定のランの場面はいつも共有の物=キャッシュの使い方は前と同じ。"""
        return self._tickc.scenes.get(int(scene.cell)) is scene

    def _draw_b4(self, scene: SceneView, trunc: list[ch.TruncationReport], cache: bool = True) -> bytes:
        """``SceneView`` → B4 の文。キャッシュの鍵は ``(セル, B4 の欄の指紋)``(1-2 の前と同じ)。〔6-4 C1〕``cache=False`` か
        共有でない場面(目と心の向きの写し)はキャッシュを読まず書かない。"""
        cache = cache and self._scene_is_shared(scene)
        if not scene.in_area:
            return N.join_lines(
                [
                    T.TEMPLATES["B4.density"].format(
                        stage=T.DENSITY_LOS_LETTERS[0], flow=T.FLOW_WORDS[0]
                    ),
                    T.TEMPLATES["B4.noise"].format(
                        stage=T.NOISE_STAGE_VOCAB[0], band=T.NOISE_BAND_WORDS[0]
                    ),
                    T.TEMPLATES["B4.salient_empty"],
                ]
            ).encode("utf-8")
        key = (int(scene.cell), int(scene.field_hash))
        got = self._b4_cache.get(key) if cache else None
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        los = int(min(scene.crowd_stage, len(T.DENSITY_LOS_LETTERS) - 1))
        ns = int(min(_noise_stage(scene), len(T.NOISE_STAGE_VOCAB) - 1))
        lines = [
            T.TEMPLATES["B4.density"].format(
                stage=T.DENSITY_LOS_LETTERS[los], flow=T.FLOW_WORDS[int(scene.flow)]
            ),
            T.TEMPLATES["B4.noise"].format(
                stage=T.NOISE_STAGE_VOCAB[ns], band=T.NOISE_BAND_WORDS[ns]
            ),
        ]
        items = list(scene.salient)
        kept, rep = ch.truncate_lines(items, "B4.salient")
        trunc.append(rep)
        lines.append(
            T.TEMPLATES["B4.salient"].format(items=N.LIST_SEPARATOR.join(kept))
            if kept
            else T.TEMPLATES["B4.salient_empty"]
        )
        out = N.join_lines(lines).encode("utf-8")
        if cache:
            self._b4_cache[key] = out
        return out

    # ---------------------------------------------------------- 〔第 6 期 6-4 C1〕目と心の向き(腕 c1 のランだけ)
    def _b2_peripheral(self, cell: int) -> bytes:
        """画面を見ている体の B2(場所と路面は今のまま・見えるもの・看板・目印は見分けていない=周辺視の行)。"""
        A = self.assets
        lines: list[str] = []
        if 0 <= cell < A.n_cells:
            band = int(self.world.assets.cell_band[cell])
            lines.append(T.TEMPLATES["B2.place"].format(place_id=A.place_ids[cell], band=T.BAND_WORDS.get(band, "地上")))
            ground = T.GROUND_WORDS.get(band, T.GROUND_WORDS[0]) if bool(A.has_street[cell]) else T.GROUND_NO_STREET
            lines.append(T.TEMPLATES["B2.ground"].format(ground=ground))
        else:
            lines.append(T.TEMPLATES["B2.place"].format(place_id="なし", band="地上"))
        lines.append(CV.B2_PERIPHERAL_LINE)
        return N.join_lines(lines).encode("utf-8")

    def _contact_blocks(self, p: Percept, blocks: "OrderedDict[str, bytes]", trunc: list[ch.TruncationReport]) -> None:
        """知覚の事実の目と心の向き(``mind_dir``)と道具の状態(``tool_state``)を描く。B2・B4・B5 の差し替えと B6 の末尾の行。"""
        att = p.mind_dir if isinstance(p.mind_dir, CV.AttentionView) else None
        dev = p.tool_state if isinstance(p.tool_state, CV.DeviceView) else None
        if att is not None and att.peripheral:
            blocks["B2"] = self._b2_peripheral(int(p.cell))
            empty = T.TEMPLATES["B5.near_person_empty"]
            b5 = blocks["B5"].decode("utf-8")
            if empty in b5:
                line = CV.B5_PERIPHERAL_NEAR_LINE.format(hint=CV.people_hint_word(att.people_hint))
                blocks["B5"] = b5.replace(empty, line, 1).encode("utf-8")
        if att is not None and att.unnoticed:
            self.contact_unnoticed_renders += 1
        lines = CV.contact_lines(att, dev, person_word)
        if not lines:
            return
        b6 = blocks["B6"]
        full = N.join_lines([*b6.decode("utf-8").split(N.LINE_SEPARATOR), *lines]).encode("utf-8")
        if (ch.estimate_tokens(blocks["B5"].decode("utf-8")) + ch.estimate_tokens(full.decode("utf-8"))
                > int(T.GROUP_TOKEN_BUDGET["individual"])):
            self.contact_lines_over_budget += 1
            return
        self.contact_lines += len(lines)
        blocks["B6"] = full

    def _b5(self, p: Percept, trunc: list[ch.TruncationReport]) -> bytes:
        """B5(固定枠)。第 1 期 1-2: ``Percept`` だけから描く(体の段・自分の状態・見えた人・被注視の人数)。"""
        lines: list[str] = []
        # 内受容(閾値割れ分のみ)
        crossed = []
        for name, label in zip(INTEROCEPTION_FIELDS, ("空腹", "体力", "体感温度")):
            v = int(getattr(p.body, name))
            if name == "hunger" and self._hunger_words:
                word = _hunger_word(v, self._hunger_min_stage)
                if word is not None:
                    crossed.append(word)
                continue
            if v >= INTERO_UP_EDGES[0]:
                crossed.append(f"{label}は{v}で閾値を超えています。")
        kept, rep = ch.truncate_lines(crossed, "B5.intero")
        trunc.append(rep)
        lines.append(
            T.TEMPLATES["B5.intero"].format(items="".join(kept))
            if kept
            else T.TEMPLATES["B5.intero_empty"]
        )
        # 自己状態・所持・直近行動
        me = p.self_view
        self_lines = [
            T.TEMPLATES["B5.holding"].format(
                money=f"{int(me.money):,}",
                hands=T.HANDS_WORDS[1 if me.hands_full else 0],
            ),
            T.TEMPLATES["B5.recent"].format(
                activity=_activity_word(int(me.activity), self.vocab_version == "v3")
            ),
        ]
        kept, rep = ch.truncate_lines(self_lines, "B5.self", max_items=2)
        lines += kept
        trunc.append(rep)
        # 近接人物 上位k(密度逓減 3/2/1)+知人は常に掲載
        near = [near_person_text(sp) for sp in p.seen_people]
        kept, rep = ch.truncate_lines(near, "B5.near_person", max_items=len(near) or None)
        trunc.append(rep)
        lines.append(
            T.TEMPLATES["B5.near_person"].format(items=N.LIST_SEPARATOR.join(kept))
            if kept
            else T.TEMPLATES["B5.near_person_empty"]
        )
        # 被注視(T2 の転置。無ければ固定文言)
        nw = int(p.watched_n)
        lines.append(
            T.TEMPLATES["B5.watched"].format(n=nw) if nw > 0 else T.TEMPLATES["B5.watched_empty"]
        )
        return N.join_lines(lines).encode("utf-8")

    def _intent_text(self, p: Percept) -> str:
        """意図を持つ体の 1 行(持たなければ ``""``)。第 1 期 1-2: ``Percept.intent`` から描く。"""
        iv = p.intent
        if iv is None:
            return ""
        word = INTENT_ACTION_WORDS.get(int(iv.action))
        if word is None:
            return ""
        kind = int(iv.target_kind)
        tgt = int(iv.target)
        if kind in (int(IntentKind.POI_NAMED), int(IntentKind.POI_CATEGORY)):
            names = self.assets.poi_name
            target = str(names[tgt]) if 0 <= tgt < len(names) else INTENT_FALLBACK_TARGET
        elif kind == int(IntentKind.PERSON):
            target = person_word(tgt)
        elif kind == int(IntentKind.BED):
            target = INTENT_BED_WORD
        else:
            target = INTENT_FALLBACK_TARGET
        return intent_line(word, target)

    def _with_intent_line(self, p: Percept, b5: bytes, b6: bytes) -> bytes:
        """B5 の「直近」の行の後に意図の行を差し込む(個体群の予算 300 を超えるなら差し込まない)。"""
        line = self._intent_text(p)
        if not line:
            return b5
        rows = b5.decode("utf-8").split(N.LINE_SEPARATOR)
        at = next(
            (k + 1 for k, r in enumerate(rows) if r.startswith("[B5 直近]")), len(rows)
        )
        rows.insert(at, line)
        out = N.join_lines(rows).encode("utf-8")
        total = ch.estimate_tokens(out.decode("utf-8")) + ch.estimate_tokens(b6.decode("utf-8"))
        if total > int(T.GROUP_TOKEN_BUDGET["individual"]):
            self.intent_lines_over_budget += 1
            return b5
        self.intent_lines += 1
        return out

    def _with_memory_line(
        self, p: Percept, b5: bytes, b6: bytes
    ) -> tuple[bytes, tuple[int, ...], tuple[tuple[int, int, int], ...]]:
        """B5 の最後に「記憶」の 1 行(6b・M4)。返り値の 3 つ目は 10e(E5)の同定(最初の時刻・種類・対象)。チャネル 60 tok・
        個体枠 300 を超えるなら末尾の項から削る。第 1 期 1-2: 想起した行は ``Percept.memories``(想起は ``perceive`` が呼ぶ)。"""
        items = list(p.memories or ())
        # 10e(E5・A8): テープ版 4 の同定(最初の時刻・種類・対象)。行番号と同じ並び・載せた分だけ返す
        meta = tuple(
            (int(getattr(it, "first_tick", -1)), int(getattr(it, "kind")), int(getattr(it, "obj"))) for it in items
        )
        if not items:
            return b5, (), ()
        when = self.clock_fn(int(p.step))
        texts: list[str] = []
        rows: list[int] = []
        for it in items:  # 逐次ループ宣言: 想起の件数ぶん(≤ 3)
            lt = int(getattr(it, "last_tick"))
            h, m = N.format_time(self.clock_fn(lt) if lt >= 0 else when)
            texts.append(memory_item_text(
                it, hhmm=f"{h}:{m}", poi_names=self.assets.poi_name, place_ids=self.assets.place_ids,
                result_text=RESULT_TEXT,
            ))
            rows.append(int(getattr(it, "row")))
        line, n_keep = compose_memory_line(texts)
        self.memory_items_dropped_for_channel += len(texts) - n_keep
        b5_text = b5.decode("utf-8")
        b6_tok = ch.estimate_tokens(b6.decode("utf-8"))
        cap = int(T.GROUP_TOKEN_BUDGET["individual"])
        out = b""
        while n_keep:  # 逐次: 想起の件数ぶん(≤ 3・個体枠 300 を超えるなら末尾の項から削る)
            out = N.join_lines([b5_text, line]).encode("utf-8")
            if ch.estimate_tokens(out.decode("utf-8")) + b6_tok <= cap:
                break
            prev = n_keep
            line, n_keep = compose_memory_line(texts[: n_keep - 1])
            self.memory_items_dropped_for_budget += prev - n_keep
        if not n_keep:
            self.memory_lines_over_budget += 1
            return b5, (), ()
        kept = texts[:n_keep]
        self.memory_lines += 1
        self.memory_items += len(kept)
        tok = ch.estimate_tokens(line)
        self.memory_line_tokens[tok] = self.memory_line_tokens.get(tok, 0) + 1
        return out, tuple(rows[: len(kept)]), meta[: len(kept)]

    def memory_summary(self) -> dict:
        """manifest ``memory_summary.render``: 記憶の行を載せた描画・項の件数・行の tok の分布。"""
        toks = self.memory_line_tokens
        n = sum(toks.values())
        return {
            "lines": int(self.memory_lines),
            "items": int(self.memory_items),
            "items_per_line": round(self.memory_items / n, 4) if n else 0.0,
            "line_tokens": {str(k): int(v) for k, v in sorted(toks.items())},
            "line_tokens_max": int(max(toks)) if toks else 0,
            "line_tokens_mean": round(sum(k * v for k, v in toks.items()) / n, 3) if n else 0.0,
            "items_dropped_for_channel": int(self.memory_items_dropped_for_channel),
            "items_dropped_for_group_budget": int(self.memory_items_dropped_for_budget),
            "lines_over_group_budget": int(self.memory_lines_over_budget),
        }

    # ---------------------------------------------------------- ablation ①(単一ランキング)
    def _rank_items(
        self,
        cand: Mapping[str, Sequence[str]],
        overrides: Mapping[tuple[str, int], Mapping[str, float]],
    ) -> list[tuple[str, str, float]]:
        """候補 → **顕著性の降順**(同点は item_id 昇順)の ``(channel_id, 行, スコア)``。

        顕著性は ``attention.rank_by_saliency`` そのもの(§4 のフロア付き対数加算)。
        素性はチャネル既定 ``channels.RANKING_PRIORS`` で、実測がある項目
        (近接人物の距離・内受容の閾値超過)は ``overrides`` が上書きする。

        Note:
            逐次ループ宣言(P4): 候補件数ぶんのループ1本(1 セル/1 個体で十数件)。
        """
        items: list[SalientItem] = []
        for cid in sorted(cand):  # 決定論: 入力の辞書順に依存しない
            prior = ch.RANKING_PRIORS[cid]
            for k, text in enumerate(cand[cid]):
                ov = dict(overrides.get((cid, k), {}))
                items.append(
                    SalientItem(
                        item_id=f"{cid}#{k:03d}",
                        text=text,
                        size_m=float(ov.get("size_m", prior.size_m)),
                        distance_m=float(ov.get("distance_m", prior.distance_m)),
                        contrast=float(ov.get("contrast", prior.contrast)),
                        motion=float(ov.get("motion", prior.motion)),
                        deviance=float(ov.get("deviance", prior.deviance)),
                    )
                )
        ranked, scores = rank_by_saliency(items)
        return [
            (it.item_id.split("#", 1)[0], it.text, float(sc)) for it, sc in zip(ranked, scores)
        ]

    def _pool_render(
        self,
        cand: Mapping[str, Sequence[str]],
        overrides: Mapping[tuple[str, int], Mapping[str, float]],
        blocks: Sequence[str],
        group: str,
        reserve_tokens: int,
        build: Callable[[Mapping[str, list[str]], Sequence[str]], dict[str, bytes]],
    ) -> tuple[dict[str, bytes], tuple[ch.TruncationReport, ...]]:
        """§3.2 の ablation ①: **1 本の池**で採否を決め、群予算に収まるまで最下位を落とす。

        1. 池の総額 = そのブロック群のチャネル上限の総和(§3.2「**同一総トークン**」)。
        2. 順位順に採る(``channels.take_within_pool``= 固定枠と同じ「行の途中で切らない」)。
        3. 実際の描画バイトが §2.2 のグループ予算を超えていたら、**最下位から 1 件ずつ**
           落として組み直す(ラベル等の固定オーバーヘッドは池の会計に入らないため)。

        Note:
            逐次ループ宣言(P4): 2 は候補件数ぶん・3 は採った件数が上限のループ。
            どちらも**個体数・セル数に比例しない**(1 セル/1 個体で十数件)。
        """
        ranked = self._rank_items(cand, overrides)
        n_fit, _used = ch.take_within_pool([t for _, t, _ in ranked], ch.pool_token_budget(blocks))
        kept: dict[str, list[str]] = {cid: [] for cid in cand}
        best: dict[str, float] = {}
        accepted: list[str] = []  # 採った項目のチャネル(順位順)
        for idx, (cid, text, score) in enumerate(ranked):
            if idx >= n_fit:
                break
            kept[cid].append(text)
            accepted.append(cid)
            best.setdefault(cid, score)
        budget = int(T.GROUP_TOKEN_BUDGET[group]) - int(reserve_tokens)
        while True:
            out = build(kept, self._channel_order(cand, best))
            total = sum(ch.estimate_tokens(b.decode("utf-8")) for b in out.values())
            if total <= budget or not accepted:
                break
            cid = accepted.pop()
            kept[cid].pop()
            if not kept[cid]:
                best.pop(cid, None)
        reports = tuple(
            ch.TruncationReport(
                channel_id=cid,
                kept=len(kept[cid]),
                dropped=len(cand[cid]) - len(kept[cid]),
                tokens_before=sum(ch.estimate_tokens(t) for t in cand[cid]),
                tokens_after=sum(ch.estimate_tokens(t) for t in kept[cid]),
            )
            for cid in sorted(cand)
        )
        return out, reports

    def _channel_order(
        self, cand: Mapping[str, Sequence[str]], best: Mapping[str, float]
    ) -> list[str]:
        """ブロック内の**行の並び**= チャネルの最上位項目のスコア降順(同点は id 昇順)。

        1 チャネル=1 行(``B5.self`` だけ 2 行)なので、これが「単一ランキングの順序」。
        採った項目が無いチャネル(空文言を出す行)はチャネル既定素性のスコアで並べる。
        """
        return sorted(
            cand,
            key=lambda cid: (-float(best.get(cid, RANKING_PRIOR_SCORES[cid])), cid),
        )

    def _lines_for(self, channel_id: str, items: Sequence[str]) -> list[str]:
        """チャネル + 採った項目 → 描画行(固定枠と**同じテンプレ**を使う)。"""
        if channel_id == "B2.ground":
            return [T.TEMPLATES["B2.ground"].format(ground=items[0])] if items else []
        if channel_id == "B2.visible":
            return [
                T.TEMPLATES["B2.visible"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B2.visible_empty"]
            ]
        if channel_id == "B2.signage":
            return [
                T.TEMPLATES["B2.signage"].format(body=items[0])
                if items
                else T.TEMPLATES["B2.signage_empty"]
            ]
        if channel_id == "B2.landmark":
            return [
                T.TEMPLATES["B2.landmark"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B2.landmark_empty"]
            ]
        if channel_id in ("B4.density", "B4.noise"):
            return [items[0]] if items else []
        if channel_id == "B4.salient":
            return [
                T.TEMPLATES["B4.salient"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B4.salient_empty"]
            ]
        if channel_id == "B4b.near":
            return [
                T.TEMPLATES["B4b.near"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B4b.near_empty"]
            ]
        if channel_id == "B5.intero":
            return [
                T.TEMPLATES["B5.intero"].format(items="".join(items))
                if items
                else T.TEMPLATES["B5.intero_empty"]
            ]
        if channel_id == "B5.self":
            return list(items)
        if channel_id == "B5.near_person":
            return [
                T.TEMPLATES["B5.near_person"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B5.near_person_empty"]
            ]
        if channel_id == "B5.watched":
            return [items[0]] if items else [T.TEMPLATES["B5.watched_empty"]]
        raise KeyError(f"未登録チャネル: {channel_id!r}")

    def _cell_candidates(
        self, scene: SceneView, shown: bool = True
    ) -> tuple[dict[str, list[str]], str]:
        """セル依存(B2/B4/B4b)の候補と、チャネルでない構造行(B2 場所)。第 1 期 1-2: B4/B4b は ``SceneView`` から。

        ``shown=False``(注視ゲートで落ちた・D-59 (b))は看板の候補を空列にする
        =**⑥ 広告ゼロと同じ道**(材料は ``_signage_body`` 1 本のまま)。
        """
        A = self.assets
        cell = int(scene.cell)
        cand: dict[str, list[str]] = {
            "B2.ground": [],
            "B2.visible": [],
            "B2.signage": [],
            "B2.landmark": [],
            "B4.density": [],
            "B4.noise": [],
            "B4.salient": [],
            "B4b.near": [],
        }
        if 0 <= cell < A.n_cells:
            band = int(self.world.assets.cell_band[cell])
            place = T.TEMPLATES["B2.place"].format(
                place_id=A.place_ids[cell], band=T.BAND_WORDS.get(band, "地上")
            )
            cand["B2.ground"] = [
                T.GROUND_WORDS.get(band, T.GROUND_WORDS[0])
                if bool(A.has_street[cell])
                else T.GROUND_NO_STREET
            ]
            static = self._visible_static(cell)
            cand["B2.visible"] = [static] if static else self._visible_names(cell)
            body = self._signage_body(cell) if shown else None
            cand["B2.signage"] = [] if body is None else [body]
            cand["B2.landmark"] = list(A.visible_landmark[cell])
        else:
            place = T.TEMPLATES["B2.place"].format(place_id="なし", band="地上")
        if scene.in_area:
            los = int(min(scene.crowd_stage, len(T.DENSITY_LOS_LETTERS) - 1))
            ns = int(min(_noise_stage(scene), len(T.NOISE_STAGE_VOCAB) - 1))
            cand["B4.density"] = [
                T.TEMPLATES["B4.density"].format(
                    stage=T.DENSITY_LOS_LETTERS[los], flow=T.FLOW_WORDS[int(scene.flow)]
                )
            ]
            cand["B4.noise"] = [
                T.TEMPLATES["B4.noise"].format(
                    stage=T.NOISE_STAGE_VOCAB[ns], band=T.NOISE_BAND_WORDS[ns]
                )
            ]
            cand["B4.salient"] = list(scene.salient)
            cand["B4b.near"] = list(scene.near_items)
        else:
            cand["B4.density"] = [
                T.TEMPLATES["B4.density"].format(
                    stage=T.DENSITY_LOS_LETTERS[0], flow=T.FLOW_WORDS[0]
                )
            ]
            cand["B4.noise"] = [
                T.TEMPLATES["B4.noise"].format(
                    stage=T.NOISE_STAGE_VOCAB[0], band=T.NOISE_BAND_WORDS[0]
                )
            ]
        return cand, place

    def _cell_blocks_ranked(
        self,
        scene: SceneView,
        trunc: list[ch.TruncationReport],
        shown: bool = True,
    ) -> dict[str, bytes]:
        """B2/B4/B4b を**セル依存の 1 本の池**(≤250 tok)で組む(ablation ①)。第 1 期 1-2: 材料は ``SceneView``。

        材料はセルの情報だけ(個体依存語は 1 語も入らない)ので、§2.4 ⑧「同セル同時間帯の
        2 体でバイト差分ゼロ」は固定枠と同じく成り立つ。キャッシュ鍵は ``(セル, B4 欄ハッシュ)``
        (固定枠の B2 はセルだけで足りるが、単一ランキングでは B4 の内容が B2 の採否を動かす)。
        """
        # 第3要素=注視ゲート(D-59 (b))。既定 p_see=1.0 では常に True=従来の 2 要素鍵と同じ。
        key = (int(scene.cell), int(scene.field_hash), bool(shown))
        shared = self._scene_is_shared(scene)  # 〔6-4 C1〕目と心の向きの写しはキャッシュを読まず書かない
        got = self._rank_cell_cache.get(key) if shared else None
        if got is not None:
            self.cache_hits += 1
            trunc.extend(got[1])
            return got[0]
        self.cache_misses += 1
        cand, place = self._cell_candidates(scene, shown)

        def build(kept: Mapping[str, list[str]], order: Sequence[str]) -> dict[str, bytes]:
            rows: dict[str, list[str]] = {"B2": [place], "B4": [], "B4b": []}
            for cid in order:
                block = "B4b" if cid.startswith("B4b.") else cid.split(".", 1)[0]
                rows[block].extend(self._lines_for(cid, kept[cid]))
            return {b: N.join_lines(rows[b]).encode("utf-8") for b in ("B2", "B4", "B4b")}

        out, reports = self._pool_render(cand, {}, ("B2", "B4", "B4b"), "cell", 0, build)
        if shared:
            self._rank_cell_cache[key] = (out, reports)
        trunc.extend(reports)
        return out

    def _b5_ranked(
        self,
        p: Percept,
        trunc: list[ch.TruncationReport],
        reserve_tokens: int,
    ) -> bytes:
        """B5 を**個体の 1 本の池**(≤220 tok)で組む(ablation ①)。第 1 期 1-2: ``Percept`` だけから描く。

        群予算(個体 ≤300)から B6 の実測ぶんを差し引いた残りが上限になる。
        """
        overrides: dict[tuple[str, int], dict[str, float]] = {}
        crossed: list[str] = []
        span = max(1, T.INTERO_SCALE_MAX - INTERO_UP_EDGES[0])
        for name, label in zip(INTEROCEPTION_FIELDS, ("空腹", "体力", "体感温度")):
            v = int(getattr(p.body, name))
            if name == "hunger" and self._hunger_words:
                word = _hunger_word(v, self._hunger_min_stage)
                if word is not None:
                    # all の満腹・ふつう(v < 閾値)は逸脱 0(負にしない)。hungry は旧と同じ値
                    overrides[("B5.intero", len(crossed))] = {
                        "deviance": min(1.0, max(0.0, (v - INTERO_UP_EDGES[0]) / span))
                    }
                    crossed.append(word)
                continue
            if v >= INTERO_UP_EDGES[0]:
                overrides[("B5.intero", len(crossed))] = {
                    "deviance": min(1.0, (v - INTERO_UP_EDGES[0]) / span)
                }
                crossed.append(f"{label}は{v}で閾値を超えています。")
        for k, sp in enumerate(p.seen_people):
            overrides[("B5.near_person", k)] = {"distance_m": float(sp.distance_m)}
        nw = int(p.watched_n)
        me = p.self_view
        cand: dict[str, list[str]] = {
            "B5.intero": crossed,
            "B5.self": [
                T.TEMPLATES["B5.holding"].format(
                    money=f"{int(me.money):,}",
                    hands=T.HANDS_WORDS[1 if me.hands_full else 0],
                ),
                T.TEMPLATES["B5.recent"].format(
                    activity=_activity_word(int(me.activity), self.vocab_version == "v3")
                ),
            ],
            "B5.near_person": [near_person_text(sp) for sp in p.seen_people],
            "B5.watched": [T.TEMPLATES["B5.watched"].format(n=nw)] if nw > 0 else [],
        }

        def build(kept: Mapping[str, list[str]], order: Sequence[str]) -> dict[str, bytes]:
            rows: list[str] = []
            for cid in order:
                rows.extend(self._lines_for(cid, kept[cid]))
            return {"B5": N.join_lines(rows).encode("utf-8")}

        out, reports = self._pool_render(
            cand, overrides, ("B5",), "individual", int(reserve_tokens), build
        )
        trunc.extend(reports)
        return out["B5"]

    def _b6(self, p: Percept) -> bytes:
        """B6(起きた理由・直前の結果・問い)。第 1 期 1-2: ``Percept.wake`` と ``Percept.self_view`` だけから描く。
        〔第 1 期 1-8b〕発話の行は ``_render_percept`` が B5 を組んだ後に ``_with_speech_lines`` で足す(腕 on のランだけ)。"""
        return N.join_lines(self._b6_lines(p)).encode("utf-8")

    def _speech_parts(self, p: Percept) -> tuple[list[str], tuple[tuple[int, int], ...], int]:
        """〔第 1 期 1-8b〕B6 の末尾の発話の行と、載せる発話の目印・本文が空になった(全部が命令文の)発話の数。

        届いた発話(``Percept.heard_speech`` の目印 → 刻みの中の控えの本文・素性タグと発話の命令文の除去つき=本文が空なら行を
        出さない=検収 低4)と、会話の番の呼び出しの出力の欄の指示(``speech_field`` かつ語彙 v3)。
        """
        out: list[str] = []
        shown: list[tuple[int, int]] = []
        empty = 0
        for eid in p.heard_speech or ():  # 逐次ループ宣言: 届いた発話の数ぶん(≤ 3)
            key = (int(eid[0]), int(eid[1]))
            got = self._tickc.heard.get(key)
            if got is None:
                raise ValueError(f"届いた発話の目印 {eid} の本文がこの刻みの控えに無い(Percept は perceive が作った物だけ描く)")
            who, text = got
            body = strip_speech_imperatives(text).kept
            if not body:
                empty += 1
                continue
            out.append(SPEECH_HEARD_LINE.format(person=person_word(who), body=body))
            shown.append(key)
        w = p.wake
        turn = (w.inviter is not None and int(w.inviter) >= 0) or (
            not isinstance(w.reason, str) and int(w.reason) == int(WakeCondition.CONVERSATION_TURN))
        if self.speech_field and self.vocab_version == "v3" and turn:
            out.append(SPEECH_FIELD_LINE)
        return out, tuple(shown), empty

    def _with_speech_lines(self, p: Percept, b5: bytes, b6: bytes) -> bytes:
        """〔第 1 期 1-8b〕B5 を組んだ後の B6 に発話の行を足す。個体群の予算 300 を超えるなら発話の行を外す(記憶の行・意図の
        行は B5 の側で先に席を取る=検収 低2)。載せた発話・本文が空の発話・予算で外した発話を口へ報告する(低8)。"""
        lines, shown, empty = self._speech_parts(p)
        n_drop = 0
        out = b6
        if lines:
            full = N.join_lines([*b6.decode("utf-8").split(N.LINE_SEPARATOR), *lines]).encode("utf-8")
            if (ch.estimate_tokens(b5.decode("utf-8")) + ch.estimate_tokens(full.decode("utf-8"))
                    > int(T.GROUP_TOKEN_BUDGET["individual"])):
                self.speech_lines_over_budget += 1
                n_drop, shown = len(shown), ()
            else:
                self.speech_lines += len(lines)
                out = full
        tc = self._tickc
        if self.heard_seen_fn is not None and (p.heard_speech or ()) and int(p.agent_id) not in tc.heard_reported:
            tc.heard_reported.add(int(p.agent_id))
            self.heard_seen_fn(int(p.agent_id), shown, empty, n_drop)
        return out

    def _b6_lines(self, p: Percept) -> list[str]:
        """B6 の 1-8b の前の行(起きた理由・直前の結果・問い)。"""
        w = p.wake
        if w.inviter is not None and int(w.inviter) >= 0:
            # §6 起床(ii) 被招待: 誰に話しかけられたかを**個体ブロック**で名指す。
            # B6 は個体ブロックなので規約⑧(B0-B4b のバイト一致)には触れない。
            reason = INVITE_REASON.format(person=person_word(int(w.inviter)))
        elif isinstance(w.reason, str):
            reason = w.reason
        else:
            r = int(w.reason)
            if r == int(WakeCondition.ACTIVITY_EXPIRY):
                # 二層の段 2: 満了入口(語彙 v3 の活動層が立つランだけ来る)
                reason = ACTIVITY_EXPIRY_REASON
            else:
                reason = T.WAKE_REASON_TEXT[r] if 0 <= r < len(T.WAKE_REASON_TEXT) else (
                    T.WAKE_REASON_TEXT[3]
                )
        lines = [T.TEMPLATES["B6.wake"].format(reason=reason)]
        code = int(w.result)
        v3 = self.vocab_version == "v3"
        acted = w.last_action or _activity_word(int(p.self_view.activity), v3)
        if not w.result_known:
            lines.append(T.TEMPLATES["B6.result_none"])
        elif code == int(ResultCode.OK):
            lines.append(T.TEMPLATES["B6.result_ok"].format(action=acted))
        else:
            why = RESULT_TEXT.get(code, "不明な理由")
            observed = self._observation(p)
            options = (
                RESULT_OPTIONS_V3.get(code, DEFAULT_OPTIONS_V3)
                if v3
                else RESULT_OPTIONS.get(code, T.DEFAULT_OPTIONS)
            )
            lines.append(
                T.TEMPLATES["B6.result_fail"].format(
                    action=acted,
                    why=why,
                    observed=observed,
                    options=N.LIST_SEPARATOR.join(options),
                )
            )
        lines.append(T.TEMPLATES["B6.question"])
        return lines

    def _observation(self, p: Percept) -> str:
        """R4 §6「失敗理由+**観測値**」。第 1 期 1-2: 観測値は ``perceive`` が引いた ``Percept.wake`` の欄。"""
        w = p.wake
        code = int(w.result)
        if code == int(ResultCode.MONEY_SHORT):
            price = int(w.cheapest_price)
            money = N.format_money(int(p.self_view.money))
            return f"(所持金{money}・最も安い品は{N.format_money(price)})" if price else f"(所持金{money})"
        if code == int(ResultCode.CLOSED):
            if w.closed_note:
                return w.closed_note
            nxt = w.next_open_hour
            return f"(次の開店は{nxt}時)" if nxt is not None else ""
        if code == int(ResultCode.FARE_SHORT):
            return f"(所持金{N.format_money(int(p.self_view.money))})"
        return ""

    # ---------------------------------------------------------- 監査
    @property
    def cache_hit_rate(self) -> float:
        """共有ブロック(B1/B2/B3/B4)のキャッシュ命中率。"""
        total = self.cache_hits + self.cache_misses
        return float(self.cache_hits) / total if total else 0.0

    def _hunger_sha_min_stage(self) -> int | None:
        """第2波 §2B: 文面の指紋に使う空腹の語の段の下限(all かつ語で描くランだけ 0・他は None=凍結値)。"""
        return 0 if (self._hunger_words and self._hunger_min_stage == 0) else None

    def report(self) -> str:
        """診断行 1 本。

        凍結静的文(W14/W15)を使っているときは**その SHA を出す**(切替はファイルの有無で
        決まるので、どの版の文面で走ったかはこの値でしか特定できない=manifest へ記録する)。
        """
        frozen = "".join(
            f" {k}={v[:16]}" for k, v in sorted(self.assets.frozen_sources.items())
        )
        return (
            f"[perception.renderer] renders={self.renders} "
            f"cache_hit_rate={self.cache_hit_rate:.3f} "
            f"(hits={self.cache_hits} misses={self.cache_misses}) "
            f"truncated_channels={self.truncation_count} "
            f"template_sha256={T.template_sha256(self._hunger_sha_min_stage())[:16]}"
            f"{frozen}"
        )


# ------------------------------------------------------------------ 補助
_ACQ_RE = re.compile(r"P-(\d+)\(" + re.escape(T.NEAR_PERSON_MARKS[1]) + r"\)")


def acquaintance_ids_in(b5: bytes) -> tuple[int, ...]:
    """10e(E5・A8): B5 の本文に「(知人)」の印つきで出た相手の体 id(出た順・重複なし)=テープ版 4 の列。

    印を付けるのは近接人物の行だけ(``P-<id>(知人)``=``person_word`` と ``NEAR_PERSON_MARKS``)。本文から引くので、
    チャネルの切り詰めで消えた人は入らない(見せた相手だけ)。
    """
    seen: dict[int, None] = {}
    for m in _ACQ_RE.finditer(b5.decode("utf-8")):
        seen.setdefault(int(m.group(1)), None)
    return tuple(seen)
