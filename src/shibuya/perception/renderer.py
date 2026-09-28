"""perception.renderer — 観測レコード → B0-B6 の決定論描画(知覚契約書 §2)。

正典
- §2.1「エンジンが構造化レコードを作り、決定論テンプレで**素性タグ付きの短い平叙文**
  (1行1事実・固定順序)に描画する。生JSONは渡さない。」
- §2.2 ブロック表と順序(変化率の昇順=``templates.BLOCK_IDS``)+v1 予算
  (共有静的 500-750・セル依存 ≤250・個体 ≤300・出力 o64)。
- §2.4 正規化規約9項(``normalize``)。§3.2 チャネル別上限(``channels``)。
- §5「B2 は**セル代表点**(またはセル内多数点)から見える物」「B5 には位置依存の差分だけ
  (**通常は空**)」「B0-B4 は同セル・同時間帯の全員でバイト一致」。
- §6 起床理由(B6)・R4 §6「直前の結果」=失敗理由+観測値+いま可能な行動3語。
- R5(認知設計書)§5「δ_read は**新着情報にのみ課金**・常在の観測プレフィクスには課さない」
  → 本モジュールは δ_read を返さない(新着=看板/傍受/受信は呼び出し側が数える)。

逐次ループ宣言(P4)
1. ``Renderer.render``: **起床した個体 1 体につき 1 回**の呼び出し(=1呼1描画)。
   個体数ぶんの Python ループは持たない(呼ぶ側が起床集合ぶん回す)。
   1 回の中で回るのは「同一セル在席者ぶんの距離計算」(NumPy・ループなし)と
   「行数ぶんの format」(1 桁)。
2. ``Renderer.prepare_tick``: **セル数**ぶんの xxh64(``hashes.field_row_hashes``・宣言済み)。
3. ``PerceptionAssets.load``: 可視性表の行数(43,479)ぶんの集約 1 本(**起動時 1 回**)。

expedient(本モジュール分)
- **歩行可能面積**(密度→人/m² の分母)。W2 に「歩ける面積」の欄が無いので、
  実データでは W10 街路点(2.5 m 格子=1 点 6.25 m²)の数から作り、合成世界では
  ``CELL_SIZE_M² × 0.15`` を使う。Fruin LOS の**境界**は mechanism、**分母**は expedient。
- 近接 k の密度逓減の写像: LOS A/B→疎(k=3)・C/D→中(k=2)・E/F→密(k=1)
  (契約書は「疎3/中2/密1」としか書かず、疎中密の境界を与えていない)。
- 内受容の閾値 ``INTERO_UP_EDGES=(4,7,9)``(``engine.change_detect`` と同値の二重定義。
  層契約により import できない)。
- 「いま可能な行動3語」の表 ``RESULT_OPTIONS``(契約書は「3語」としか書かない)。
- B4b は C3 では**固定の空文言**(サブセル 25 m 級のデータが無い)。C4 で**待ち行列だけ**
  差し込み口を付けた(``prepare_tick(queues=…)``)。行列は POI 単位=**セル共有**なので
  規約⑧(B0-B4b に個体依存語を置かない)は保たれる。行列が無いセルは従来の固定文言のまま。
- 流れ(B4)は既定 0(「一定です」)。方向データが無い。
- 天候が W13 に無い日付は**その時刻の最頻値**へ落とす(決定論)。
- **W14/W15 の凍結静的文への切替**(C5): ``world_dir`` に ``w14_signage.parquet`` /
  ``w15_cell_static.parquet`` が在ればその文面を使い、無ければ従来の合成文へ落ちる
  (**テンプレ本体と ``template_sha256`` は不変**)。凍結文の置き場所は
  W14 → ``B2.signage`` の本文(§3.2 の 25 tok 枠)・W15 → ``B2.visible`` の ``{items}``。
  W15 を B2 に**足す**と群予算(B2+B4+B4b ≤250)を超えるので、可視物リストを**置き換える**
  形にした。W15 側の上限は 45 tok(= B2 ブロック予算 150 − 実資産での他行最大)で、
  仕様 §1 W15 の「150 tok」は B2 ブロック全体の予算と読む(=**親判断待ち**)。
  どの版の文面で走ったかは ``PerceptionAssets.frozen_sources``(ファイル名→sha256)に出る。

**解決した曖昧点(親へ報告・黙って解決していない)**
1. §2.4 ⑧「同セル同時間帯の2体で B0-B4 のバイト差分がゼロ」対 §2.2「B1=種別(約10)」。
   同一セルに種別の違う2体が居れば B1 は必ず違う → 検査は **(セル, 5分帯, 種別)** で行う。
2. §2.2 の「B0 300 tok」対 §2.2 の「共有静的(B0+B1+B3)≈500-750」+「共有静的は長くてよい」
   +§2.5「B0 に**条例の適用規則を明記する方針を維持**」。v0 の system ブロック(1,171字≒586 tok)
   を維持すると B0 単体では 300 を超えるので、**実効ゲートはグループ予算**
   (共有静的 ≤750・セル依存 ≤250・個体 ≤300)にした。B0 単体の超過は報告値として出す。
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, ClassVar, Final, Mapping, Sequence

import numpy as np

from shibuya.agents.state import (
    INTENT_NONE,
    INTEROCEPTION_FIELDS,
    RESULT_TEXT,
    Activity,
    ActivityKind,
    AgentState,
    IntentKind,
    ResultCode,
    WakeCondition,
)
from shibuya.core.hashing import blake3_hex, xxh64
from shibuya.perception import channels as ch
from shibuya.perception import hashes as H
from shibuya.perception import normalize as N
from shibuya.perception import templates as T
from shibuya.perception.attention import (
    P_SEE_MEDIUM_RANGE,
    SalientItem,
    gate_stage1,
    rank_by_saliency,
    strip_imperatives,
)
from shibuya.world.assets import CELL_SIZE_M, WorldAssets
from shibuya.world.state import LANDMARK_CATS, World

__all__ = [
    "compose_memory_line",
    "memory_item_text",
    "P_SEE_ACTIVITY_KINDS",
    "P_SEE_BY_ACTIVITY",
    "check_p_see_activity",
    "DEFAULT_START_DATETIME",
    "WALKABLE_FRACTION_SYNTHETIC",
    "STREET_POINT_AREA_M2",
    "INTERO_UP_EDGES",
    "RESULT_OPTIONS",
    "RESULT_OPTIONS_V3",
    "DEFAULT_OPTIONS_V3",
    "ACTIVITY_WORDS_V3",
    "ACTIVITY_EXPIRY_REASON",
    "ACTIVITY_LINE",
    "ACTIVITY_LINE_MAX_TOKENS",
    "activity_line",
    "INTENT_LINE",
    "INTENT_LINE_MAX_TOKENS",
    "INTENT_ACTION_WORDS",
    "INTENT_BED_WORD",
    "INTENT_FALLBACK_TARGET",
    "intent_line",
    "NAMED_CLOSED_NOTE",
    "NAMED_CLOSED_NOTE_MAX_TOKENS",
    "named_closed_note",
    "INVITE_REASON",
    "person_word",
    "ACTIVITY_WORDS",
    "RANKING_PRIOR_SCORES",
    "Rendered",
    "PerceptionAssets",
    "Renderer",
]

#: 既定の世界内開始日時(W13 の最初の日=2026-07-28)。``clock_fn`` を渡さないときに使う。
DEFAULT_START_DATETIME: Final[datetime] = datetime(2026, 7, 28, 0, 0)

#: **看板(広告面)の注視ゲート**(知覚契約書 §4 段1 の p_see)の既定。``1.0``= 在圏セルの
#: 看板行が必ず観測に入る=**現行のバイト**(D-59 (b) 以前の挙動)。1.0 未満にすると
#: 体×看板×tick の決定論的ベルヌーイで看板行が落ちる。帯の出典は §4 段1
#: (中小媒体 ``P_SEE_MEDIUM_RANGE`` 0.14-0.40 / 大型ビジョン 0.63-0.78)。
#: **既定を 1.0 に置いたのは「切替口は既定不変」の規律**(較正値は腕の側で指定する)。
SIGNAGE_P_SEE_DEFAULT: Final[float] = 1.0

#: 注視ゲートの乱数ドメイン(``core.rng`` のドメイン表・``attention.gate_stage1`` が使う)。
SIGNAGE_P_SEE_DOMAIN: Final[str] = "perception.attention.p_see"


#: **5 段目 5c(D-117・M1 (a)・M2 (b)・M4 (a))**: 看板の注視ゲート p_see に掛ける**活動の種別の乗数**の鍵。
#: move_to=目的地つき移動・wander=あたり・in_shop=在店・in_place=その場・phone=通話/スマホ操作中
#: (旗は D-121 O3 で来る=いまは該当する体が無い・鍵だけ置く)・companion_talk=連れとの会話中
#: (会話の成立=``Activity.CONVERSING`` で判る範囲・宣言)。
P_SEE_ACTIVITY_KINDS: Final[tuple[str, ...]] = (
    "move_to", "wander", "in_shop", "in_place", "phone", "companion_talk",
)
#: 乗数の既定=**全部 1.0**(M2 (b))=既定のランは描画バイトも checkpoint も 1 バイトも動かない。
#: 錨のある腕(草案 §3-2): 通話 0.49(Hyman 2010 表 2 の 25.0/51.3)・連れとの会話 1.39(71.4/51.3)。
#: 目的地つき移動 0.5 は錨の無い感度腕の 1 点。実効 p_see=min(1, p_see × 乗数)(> 1 は切る=宣言)。
P_SEE_BY_ACTIVITY: Final[Mapping[str, float]] = {k: 1.0 for k in P_SEE_ACTIVITY_KINDS}


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


def check_p_see_activity(value: "Mapping[str, float] | str | None") -> dict[str, float]:
    """活動の種別の乗数表を検査して、全部の鍵を持つ辞書で返す(欠けた鍵は 1.0)。

    ``value`` は辞書か JSON 文字列(CLI ``--p-see-activity``)か ``None``(既定=全部 1.0)。

    Example:
        >>> check_p_see_activity('{"phone": 0.49}')["phone"], check_p_see_activity(None)["wander"]
        (0.49, 1.0)
    """
    import json
    import math

    if value is None:
        return dict(P_SEE_BY_ACTIVITY)
    raw = json.loads(value) if isinstance(value, str) else dict(value)
    if not isinstance(raw, dict):
        raise ValueError("p_see_activity は {活動の種別: 乗数} の辞書")
    unknown = sorted(set(raw) - set(P_SEE_ACTIVITY_KINDS))
    if unknown:
        raise ValueError(f"p_see_activity の鍵は {P_SEE_ACTIVITY_KINDS} のどれか(未知 {unknown})")
    out = dict(P_SEE_BY_ACTIVITY)
    for k, v in raw.items():
        x = float(v)
        if not (math.isfinite(x) and x >= 0.0):
            raise ValueError(f"p_see_activity の乗数は 0 以上の有限値(いま {k}={v!r})")
        out[k] = x
    return out


def check_signage_p_see(value: float) -> float:
    """看板の注視確率を検査して返す(0.0〜1.0 の外は ``ValueError``)。

    Example:
        >>> check_signage_p_see(0.3)
        0.3
    """
    p = float(value)
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"signage_p_see は 0.0〜1.0 の確率(いま {value!r})")
    return p
#: 合成世界の歩行可能面積の割合(expedient)。
WALKABLE_FRACTION_SYNTHETIC: Final[float] = 0.15
#: W10 街路点 1 点が代表する面積[m²](2.5 m 格子)。
STREET_POINT_AREA_M2: Final[float] = 6.25
#: 内受容の閾値(``engine.change_detect.INTERO_UP_EDGES`` と同値・層契約により二重定義)。
INTERO_UP_EDGES: Final[tuple[int, ...]] = (4, 7, 9)


def _hunger_word(value: int) -> str | None:
    """空腹の写し(1/5/8/10)→ B5 の語の 1 文(5 段目 5a)。段が ``HUNGER_WORD_DRAW_MIN_STAGE``
    未満(満腹・ふつう)なら ``None``(描かない)。段=``INTERO_UP_EDGES`` を何本越えたか。"""
    stage = sum(1 for e in INTERO_UP_EDGES if int(value) >= e)
    if stage < T.HUNGER_WORD_DRAW_MIN_STAGE:
        return None
    return T.HUNGER_ITEM_TEMPLATE.format(word=T.HUNGER_WORDS[stage])

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

#: ``Activity`` → 日本語(B5 直近の行動・B6 直前の結果)。
ACTIVITY_WORDS: Final[tuple[str, ...]] = (
    "待機", "移動", "待機", "休憩", "就寝", "購入", "会話", "乗車",
)
#: 同(語彙 v3=待機/休憩 → なし の機械的な読み替え・二層の段 2)。
ACTIVITY_WORDS_V3: Final[tuple[str, ...]] = tuple(
    "なし" if w in ("待機", "休憩", "降車") else w for w in ACTIVITY_WORDS
)

#: 失敗コード → 「いま可能」3語(行動契約書 §6・**待機を必ず含む**=失敗しない行動・expedient)。
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
#: 同セルの活動の 1 行(B4b・**テンプレ本体ではない**=``template_sha256`` は不変・二層の段 2)。
#: 同セルの**全員**の活動文で作る=同セルの 2 体でバイト一致(規約⑧)。
ACTIVITY_LINE: Final[str] = "[B4b 活動] 近くの人: {items}。"
#: 1 行の上限[tok](アジェンダ §2「1 行 ≤ 15 tok」)。
ACTIVITY_LINE_MAX_TOKENS: Final[int] = 15
#: 項目の区切り(アジェンダ §2 の文面「…が<人数>人・…」)。
ACTIVITY_ITEM_SEPARATOR: Final[str] = "・"


#: 段 2c: 意図の 1 行(B5・**テンプレ本体ではない**=``template_sha256`` は不変・アジェンダ §3-2
#: 「いま <行為> のため <対象> へ向かっている」・文面は自前=expedient)。意図を持つ体だけに出る
#: (=その体の prompt_hash だけが動く)。
INTENT_LINE: Final[str] = "[B5 意図] いま{action}のため{target}へ向かっている。"
#: 1 行の上限[tok](アジェンダ §3-2「≤ 15 tok」)。対象の名を末尾から切り詰めて収める。
INTENT_LINE_MAX_TOKENS: Final[int] = 15
#: 行為コード → 語(**語彙 v3 の語**・層契約(perception は llm を import できない)のため字面で持つ
#: =``llm.contract.ACTION_CODES`` との一致はテストが機械検査する)。
INTENT_ACTION_WORDS: Final[Mapping[int, str]] = {
    3: "購入", 24: "食事", 22: "並ぶ", 5: "会話", 11: "就寝",
}
#: 寝床(自宅セル)の対象の語。
INTENT_BED_WORD: Final[str] = "自宅"
#: 対象の名に省略記法の語(⑥)が入っているときの代わりの語(宣言・expedient)。
INTENT_FALLBACK_TARGET: Final[str] = "目的の場所"


def intent_line(action_word: str, target: str) -> str:
    """意図の 1 行(``INTENT_LINE_MAX_TOKENS`` に収まるよう対象の名を末尾から切り詰める)。"""
    t = N.canonical_whitespace(str(target)).strip() or INTENT_FALLBACK_TARGET
    if any(a in t for a in N.ABBREVIATIONS):
        t = INTENT_FALLBACK_TARGET
    line = INTENT_LINE.format(action=action_word, target=t)
    while ch.estimate_tokens(line) > INTENT_LINE_MAX_TOKENS and len(t) > 1:
        t = t[:-1]
        line = INTENT_LINE.format(action=action_word, target=t)
    return line


#: 段 2c Q25: 名指しの店が見えるが閉店で歩かずに失敗した体の B6「直前の結果」の補足の 1 句
#: (``RESULT_TEXT`` の短句「営業時間外」は変えない・テンプレ本体ではない=``template_sha256`` 不変)。
NAMED_CLOSED_NOTE: Final[str] = "({name}は閉店中{opens})"
#: 同(開店の時刻=W7 の当日/翌日の最初の開店・無ければ付けない)。
NAMED_CLOSED_OPENS: Final[str] = "・{hhmm}に開く"
#: 補足の 1 句の上限[tok](≤ 15 tok・B6 枠 80 の内)。店名を末尾から切り詰めて収める。
NAMED_CLOSED_NOTE_MAX_TOKENS: Final[int] = 15
#: 店名に省略記法の語が入っているときの代わりの語(宣言・expedient)。
NAMED_CLOSED_FALLBACK_NAME: Final[str] = "その店"


def named_closed_note(name: str, open_minute: int = -1) -> str:
    """Q25 の補足の 1 句(店名 + 閉店中 + あれば「HH:MM に開く」・≤ 15 tok)。"""
    n = N.canonical_whitespace(str(name)).strip() or NAMED_CLOSED_FALLBACK_NAME
    if any(a in n for a in N.ABBREVIATIONS):
        n = NAMED_CLOSED_FALLBACK_NAME
    m = int(open_minute)
    opens = (
        NAMED_CLOSED_OPENS.format(hhmm=f"{(m // 60) % 24:02d}:{m % 60:02d}") if m >= 0 else ""
    )
    line = NAMED_CLOSED_NOTE.format(name=n, opens=opens)
    while ch.estimate_tokens(line) > NAMED_CLOSED_NOTE_MAX_TOKENS and len(n) > 1:
        n = n[:-1]
        line = NAMED_CLOSED_NOTE.format(name=n, opens=opens)
    return line


def activity_line(rows: Sequence[tuple[str, int]]) -> str:
    """活動の (文, 人数) の列(人数降順→文字列順・上位 2)→ B4b の 1 行(無ければ ``""``)。

    ``ACTIVITY_LINE_MAX_TOKENS`` に収まる分だけ項目を載せる。先頭の項目だけでも収まらなければ
    文を末尾から切り詰める(expedient)。省略記法・個体依存語を含む文は載せない(⑥⑧)。
    """
    items: list[str] = []
    for text, count in rows:
        t = N.canonical_whitespace(str(text)).strip()
        if not t or any(a in t for a in N.ABBREVIATIONS):
            continue
        if any(p.search(t) for _, p in N.AGENT_DEPENDENT_PATTERNS):
            continue
        item = f"{t}が{int(count)}人"
        cand = items + [item]
        line = ACTIVITY_LINE.format(items=ACTIVITY_ITEM_SEPARATOR.join(cand))
        if ch.estimate_tokens(line) <= ACTIVITY_LINE_MAX_TOKENS:
            items = cand
            continue
        if not items:
            while len(t) > 1:
                t = t[:-1]
                item = f"{t}が{int(count)}人"
                line = ACTIVITY_LINE.format(items=item)
                if ch.estimate_tokens(line) <= ACTIVITY_LINE_MAX_TOKENS:
                    items = [item]
                    break
        break
    if not items:
        return ""
    return ACTIVITY_LINE.format(items=ACTIVITY_ITEM_SEPARATOR.join(items))



def _prior_scores() -> Mapping[str, float]:
    """チャネル既定素性そのものの顕著性スコア(**採った項目が無い行の並び**に使う)。

    ``attention.rank_by_saliency`` を 1 件ずつのダミーに掛けるだけ(起動時 1 回・12 件)。
    式を二重に書かないための実装(スコアの定義は attention 側の 1 か所だけ)。
    """
    items = [
        SalientItem(
            item_id=cid, text="", size_m=pr.size_m, distance_m=pr.distance_m,
            contrast=pr.contrast, motion=pr.motion, deviance=pr.deviance,
        )
        for cid, pr in ch.RANKING_PRIORS.items()
    ]
    ranked, scores = rank_by_saliency(items)
    return {it.item_id: float(sc) for it, sc in zip(ranked, scores)}


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

    @property
    def tokens_total(self) -> int:
        return int(sum(self.tokens_est.values()))

    def within_group_budgets(self) -> bool:
        return all(v <= T.GROUP_TOKEN_BUDGET[k] for k, v in self.group_tokens.items())

    def shared_static_bytes(self) -> bytes:
        """B0-B4b の連結(§2.4 ⑧ のバイト一致検査に使う)。"""
        return b"\n".join(self.blocks[b] for b in T.BLOCK_IDS if b not in ("B5", "B6"))


# ------------------------------------------------------------------ 知覚側の静的資産
@dataclass(frozen=True)
class PerceptionAssets:
    """描画に要る静的資産(セル代表点からの可視物・名称・歩行可能面積・天候表)。

    ``World``/``WorldAssets``(C2)は名称・可視性・天候を持たないので、知覚側で読む。
    """

    source: str
    place_ids: tuple[str, ...]
    walkable_area_m2: np.ndarray
    has_street: np.ndarray
    #: セル → 可視の店舗・施設(POI 索引・可視視点数の降順→ID 昇順)
    visible_poi: tuple[tuple[int, ...], ...]
    #: セル → 可視のランドマーク/出口の表示名(同順)
    visible_landmark: tuple[tuple[str, ...], ...]
    poi_name: tuple[str, ...]
    poi_cat: tuple[str, ...]
    #: (日付文字列, 時) → (天候, 日照, 暑さ)
    weather_by_date_hour: Mapping[tuple[str, int], tuple[str, str, str]]
    #: 時 → (天候, 日照, 暑さ)の最頻値(日付が表に無いときの決定論フォールバック)
    weather_by_hour: Mapping[int, tuple[str, str, str]]
    #: セル別の騒音段階(昼/夜・W10 街路点の最頻値)
    noise_stage_day: np.ndarray
    noise_stage_night: np.ndarray
    #: POI → W14 で**凍結された看板(a)文面**(無い POI は空文字=合成文へフォールバック)。
    poi_signage: tuple[str, ...] = ()
    #: セル → W15 で**凍結された B2 セル静的文**(無いセルは空文字=合成の可視物リストへ)。
    cell_static: tuple[str, ...] = ()
    #: 凍結資産のファイル名 → sha256(**manifest へ記録する値**。切替は「ファイルが在るか」だけで
    #: 決まるので、どの版の文面で走ったかはこの SHA でしか特定できない)。
    frozen_sources: Mapping[str, str] = field(default_factory=dict)

    @property
    def n_cells(self) -> int:
        return len(self.place_ids)

    @property
    def uses_frozen_signage(self) -> bool:
        return any(self.poi_signage)

    @property
    def uses_frozen_cell_static(self) -> bool:
        return any(self.cell_static)

    def noise_stage_for_tick(self, when: datetime) -> np.ndarray:
        """時刻 → セル別騒音段階(環境基準の昼 6-22 時 / 夜 22-6 時)。"""
        return self.noise_stage_day if 6 <= when.hour < 22 else self.noise_stage_night

    def weather(self, when: datetime) -> tuple[str, str, str]:
        """世界内日時 → (天候, 日照, 暑さ)。"""
        key = (when.strftime("%Y-%m-%d"), int(when.hour))
        got = self.weather_by_date_hour.get(key)
        if got is not None:
            return got
        return self.weather_by_hour.get(
            int(when.hour), (T.WEATHER_WORDS[0], T.DAYLIGHT_WORDS[1], T.HEAT_STAGE_WORDS[0])
        )

    # ---------------------------------------------------------- 生成
    @classmethod
    def synthetic(cls, world: World) -> "PerceptionAssets":
        """合成世界(または資産が無い実行)用。POI 名は ``カテゴリ+連番``。"""
        a = world.assets
        n = a.n_cells
        band_word = {-1: "UG", 0: "GL", 1: "DECK"}
        place_ids = tuple(
            f"g{int(a.cell_ix[i])}_{int(a.cell_iy[i])}_{band_word[int(a.cell_band[i])]}"
            for i in range(n)
        )
        names = tuple(f"{a.poi_cat[j]}{j:04d}" for j in range(a.n_poi))
        vis_poi: list[tuple[int, ...]] = [() for _ in range(n)]
        for c in range(n):
            hit = np.flatnonzero(a.poi_cell == c)
            vis_poi[c] = tuple(int(j) for j in hit[:8])
        area = np.full(n, CELL_SIZE_M * CELL_SIZE_M * WALKABLE_FRACTION_SYNTHETIC, np.float64)
        return cls(
            source="synthetic",
            place_ids=place_ids,
            walkable_area_m2=area,
            has_street=np.ones(n, dtype=bool),
            visible_poi=tuple(vis_poi),
            visible_landmark=tuple(() for _ in range(n)),
            poi_name=names,
            poi_cat=tuple(a.poi_cat),
            weather_by_date_hour={},
            weather_by_hour={
                h: (
                    T.WEATHER_WORDS[0],
                    T.DAYLIGHT_WORDS[1] if 5 <= h < 19 else T.DAYLIGHT_WORDS[2 if h >= 19 else 0],
                    T.HEAT_STAGE_WORDS[1],
                )
                for h in range(24)
            },
            noise_stage_day=np.ones(n, dtype=np.uint8),
            noise_stage_night=np.zeros(n, dtype=np.uint8),
        )

    #: ``load`` が要る資産ファイル(1 つでも欠けたら ``load_or_synthetic`` は合成へ落ちる)。
    REQUIRED_FILES: ClassVar[tuple[str, ...]] = (
        "w2_cells.parquet",
        "w6_poi.parquet",
        "w8_targets.parquet",
        "w8_t1_cell.parquet",
        "w10_street_points.parquet",
        "w11_station_exits.parquet",
        "w13_weather_hourly.parquet",
    )

    @classmethod
    def available(cls, path: str | Path | None) -> bool:
        """``load`` に必要なファイルが揃っているか。"""
        if path is None:
            return False
        p = Path(path)
        return p.is_dir() and all((p / f).exists() for f in cls.REQUIRED_FILES)

    @classmethod
    def load_or_synthetic(cls, path: str | Path | None, world: World) -> "PerceptionAssets":
        """資産があれば読み、無ければ合成へ落ちる(``World.load_or_synthetic`` と同じ作法)。"""
        if cls.available(path) and world.assets.source != "synthetic":
            return cls.load(path, world)  # type: ignore[arg-type]
        return cls.synthetic(world)

    @classmethod
    def load(cls, path: str | Path, world: World) -> "PerceptionAssets":
        """``data/world/v2`` から読む(W2/W6/W8/W10/W11/W13)。

        Note:
            逐次ループ宣言(P4)3: 可視性表の行数ぶんの集約 1 本(**起動時 1 回**)。
        """
        import pyarrow.parquet as pq

        p = Path(path)
        cells = pq.read_table(p / "w2_cells.parquet", columns=["place_id"]).to_pydict()
        place_ids = tuple(str(s) for s in cells["place_id"])
        n = len(place_ids)
        if n != world.n_cells:
            raise ValueError(f"セル数不一致: 資産 {n} vs World {world.n_cells}")

        poi = pq.read_table(
            p / "w6_poi.parquet", columns=["poi_id", "name", "cat"]
        ).to_pydict()
        poi_name = tuple(str(s) for s in poi["name"])
        poi_cat = tuple(str(s) for s in poi["cat"])
        poi_index = {str(pid): i for i, pid in enumerate(poi["poi_id"])}

        exits = pq.read_table(
            p / "w11_station_exits.parquet", columns=["exit_id", "exit_name", "station_title"]
        ).to_pydict()
        exit_label = {
            str(e): f"{str(st)}{str(nm)}"
            for e, nm, st in zip(exits["exit_id"], exits["exit_name"], exits["station_title"])
        }

        tgt = pq.read_table(
            p / "w8_targets.parquet", columns=["target_id", "kind", "ref_id"]
        ).to_pydict()
        tgt_kind = list(map(str, tgt["kind"]))
        tgt_ref = list(map(str, tgt["ref_id"]))

        t1 = pq.read_table(
            p / "w8_t1_cell.parquet", columns=["place_idx", "target_id", "n_viewpoints"]
        ).to_pydict()
        pidx = np.asarray(t1["place_idx"], dtype=np.int64)
        tid = np.asarray(t1["target_id"], dtype=np.int64)
        nvp = np.asarray(t1["n_viewpoints"], dtype=np.int64)
        # 可視視点数の降順 → target_id 昇順(§2.4 ② の決定論的な順序)
        order = np.lexsort((tid, -nvp, pidx))
        pidx, tid = pidx[order], tid[order]
        starts = np.searchsorted(pidx, np.arange(n), side="left")
        ends = np.searchsorted(pidx, np.arange(n), side="right")

        vis_poi: list[tuple[int, ...]] = []
        vis_land: list[tuple[str, ...]] = []
        for c in range(n):
            pois: list[int] = []
            lands: list[str] = []
            for t in tid[starts[c] : ends[c]]:
                k = tgt_kind[int(t)]
                ref = tgt_ref[int(t)]
                if k == "poi":
                    j = poi_index.get(ref)
                    if j is None:
                        continue
                    # C9b G6 a′: 目印の集合は**世界側と同じ 1 本**
                    # (``world.state.LANDMARK_CATS`` = ``World.landmark_mask`` の判定)。
                    if poi_cat[j] in LANDMARK_CATS:
                        if len(lands) < 4:
                            lands.append(poi_name[j])
                    elif len(pois) < 8:
                        pois.append(j)
                elif k == "exit":
                    if len(lands) < 4:
                        lands.append(exit_label.get(ref, "駅出入口"))
                if len(pois) >= 8 and len(lands) >= 4:
                    break
            vis_poi.append(tuple(pois))
            vis_land.append(tuple(lands))

        # ---- W10 街路点 → セル別 歩行可能面積・騒音段階(最頻値) ----
        area, has_street, ns_day, ns_night = _street_aggregate(p, world.assets, n)

        # ---- W14/W15 の凍結静的文(在れば使う・無ければ従来の合成文) ----
        frozen_sources: dict[str, str] = {}
        poi_signage = _load_frozen_text(
            p, "w14_signage.parquet", "poi_id", [str(s) for s in poi["poi_id"]], frozen_sources
        )
        cell_static = _load_frozen_text(
            p, "w15_cell_static.parquet", "place_id", list(place_ids), frozen_sources
        )

        # ---- W13 天候 ----
        w13 = pq.read_table(
            p / "w13_weather_hourly.parquet",
            columns=["date", "hour", "weather", "daylight", "heat_stage"],
        ).to_pydict()
        by_dh: dict[tuple[str, int], tuple[str, str, str]] = {}
        per_hour: dict[int, list[tuple[str, str, str]]] = {}
        for d, h, w, dl, hs in zip(
            w13["date"], w13["hour"], w13["weather"], w13["daylight"], w13["heat_stage"]
        ):
            key = (str(d)[:10], int(h))
            val = (str(w), str(dl), str(hs))
            by_dh[key] = val
            per_hour.setdefault(int(h), []).append(val)
        by_hour = {
            h: max(sorted(set(v)), key=lambda x: (v.count(x), x)) for h, v in per_hour.items()
        }

        return cls(
            source=str(p),
            place_ids=place_ids,
            walkable_area_m2=area,
            has_street=has_street,
            visible_poi=tuple(vis_poi),
            visible_landmark=tuple(vis_land),
            poi_name=poi_name,
            poi_cat=poi_cat,
            weather_by_date_hour=by_dh,
            weather_by_hour=by_hour,
            noise_stage_day=ns_day,
            noise_stage_night=ns_night,
            poi_signage=poi_signage,
            cell_static=cell_static,
            frozen_sources=frozen_sources,
        )


def _load_frozen_text(
    path: Path, name: str, key_col: str, keys: Sequence[str], sources: dict[str, str]
) -> tuple[str, ...]:
    """W14/W15 の凍結文 parquet → ``keys`` の順に並べた文面(無い鍵は空文字)。

    ファイルが無ければ全部空文字を返す(= **切替は world_dir のファイル有無で決まる**)。
    在るときは ``sources[name] = sha256`` を記録する(manifest 用)。

    Note:
        逐次ループ宣言(P4): 行数(POI 2,337 / セル 520)ぶんの辞書化 1 本。**起動時 1 回**。
    """
    import hashlib

    import pyarrow.parquet as pq

    f = Path(path) / name
    if not f.exists():
        return tuple("" for _ in keys)
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    sources[name] = h.hexdigest()
    d = pq.read_table(f, columns=[key_col, "text"]).to_pydict()
    table = {str(k): str(t) for k, t in zip(d[key_col], d["text"])}
    return tuple(table.get(str(k), "") for k in keys)


def _street_aggregate(
    path: Path, assets: WorldAssets, n_cells: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """W10 街路点 → (歩行可能面積, 街路の有無, 昼騒音段, 夜騒音段)。全てベクトル演算。"""
    import pyarrow.parquet as pq

    d = pq.read_table(path / "w10_street_points.parquet", columns=["x", "y", "band"]).to_pydict()
    sx = np.asarray(d["x"], dtype=np.float64)
    sy = np.asarray(d["y"], dtype=np.float64)
    band_code = {"UG": -1, "GL": 0, "DECK": 1}
    sb = np.array([band_code[str(b)] for b in d["band"]], dtype=np.int8)
    ix = np.floor(sx / CELL_SIZE_M).astype(np.int64)
    iy = np.floor(sy / CELL_SIZE_M).astype(np.int64)

    def key(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
        return (a + 1_000_000) * 8_000_000 + (b + 1_000_000) * 4 + (c + 1)

    ck = key(assets.cell_ix.astype(np.int64), assets.cell_iy.astype(np.int64),
             assets.cell_band.astype(np.int64))
    order = np.argsort(ck, kind="stable")
    sk = ck[order]
    q = key(ix, iy, sb.astype(np.int64))
    pos = np.clip(np.searchsorted(sk, q), 0, sk.size - 1)
    hit = sk[pos] == q
    cell_of_point = np.where(hit, order[pos], -1)

    valid = cell_of_point >= 0
    counts = np.bincount(cell_of_point[valid], minlength=n_cells).astype(np.float64)
    area = np.maximum(counts * STREET_POINT_AREA_M2,
                      CELL_SIZE_M * CELL_SIZE_M * WALKABLE_FRACTION_SYNTHETIC)
    has_street = counts > 0

    ns_day = np.zeros(n_cells, dtype=np.uint8)
    ns_night = np.zeros(n_cells, dtype=np.uint8)
    for name, out in (("w10_noise_stage_day.npy", ns_day), ("w10_noise_stage_night.npy", ns_night)):
        f = path / name
        if not f.exists():
            continue
        stage = np.load(f)
        # セル×段の度数 → 最頻値(段は 0..3)
        n_stage = 4
        flat = cell_of_point[valid] * n_stage + np.clip(stage[valid].astype(np.int64), 0, n_stage - 1)
        tab = np.bincount(flat, minlength=n_cells * n_stage).reshape(n_cells, n_stage)
        out[:] = tab.argmax(axis=1).astype(np.uint8)
    return area, has_street, ns_day, ns_night


# ------------------------------------------------------------------ レンダラ
@dataclass
class _TickCache:
    """1 tick ぶんの前計算(セル配列とハッシュ)。"""

    tick: int = -1
    when: datetime = DEFAULT_START_DATETIME
    band5: int = -1
    los_stage: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint8))
    noise_stage: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint8))
    flow: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint8))
    salient: Mapping[int, tuple[str, ...]] = field(default_factory=dict)
    salient_digest: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int32))
    #: セル → B4b「近景」の描画バイト(行列がある セルだけ。無ければ固定文言)。
    b4b: Mapping[int, bytes] = field(default_factory=dict)
    #: セル → B4b の**生の項目**(単一ランキングが池へ入れる素材。固定枠では使わない)。
    b4b_items: Mapping[int, tuple[str, ...]] = field(default_factory=dict)
    #: ``hashes.b4_field_row`` の生欄 ``(n_cells, 4)`` int32(エンジンの変化検出器が読む)。
    b4_field_rows: np.ndarray = field(default_factory=lambda: np.zeros((0, 4), np.int32))
    b4_field_hash: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint64))
    cell_order: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    cell_start: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    cell_end: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    #: 個体 → ``cell_order`` の位置(逆置換)。自分の行を O(1) で外すために持つ(C7)。
    cell_pos: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    #: ``cell_order`` の順に並べた x / y(**連続配列**)。1 呼あたりの gather を無くす(C7)。
    cell_x: np.ndarray = field(default_factory=lambda: np.zeros(0, np.float64))
    cell_y: np.ndarray = field(default_factory=lambda: np.zeros(0, np.float64))


class Renderer:
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
        p_see_activity: "Mapping[str, float] | str | None" = None,
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
        """
        self.world = world
        self.agents = agents
        self.assets = assets if assets is not None else PerceptionAssets.synthetic(world)
        self.clock_fn = clock_fn or (lambda t: DEFAULT_START_DATETIME + timedelta(minutes=int(t)))
        self.seed = seed
        self.acquaintances = dict(acquaintances or {})
        self.watched_by = watched_by
        self.budget_mode = ch.BudgetMode.parse(budget_mode)
        self.strict_group_budget = strict_group_budget
        self.signage_enabled = bool(signage_enabled)
        self.signage_p_see = check_signage_p_see(signage_p_see)
        #: 5 段目 5c: 活動の種別の乗数表(全部の鍵・既定は全部 1.0=``_p_see_identity``)。
        self.p_see_activity = check_p_see_activity(p_see_activity)
        self._p_see_mult = np.asarray(
            [self.p_see_activity[k] for k in P_SEE_ACTIVITY_KINDS], dtype=np.float64
        )
        self._p_see_identity = bool(np.all(self._p_see_mult == 1.0))
        #: 記憶 第 1 段 6b: 想起の口 ``(体, tick, 起床条件, 招待者) → [RecallItem…]``(``engine.run`` が
        #: ``--memory on`` のランだけ差し込む)。``None``(既定)=記憶の行を描かない=1 バイトも変わらない。
        self.memory_recall: Callable[[int, int, int, int], Sequence[object]] | None = None
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

        self._tickc = _TickCache()
        # 既定(vocab × v1)は ``TEMPLATES["B0.system"]`` と同一文字列=描画バイト不変
        # (AB7・語彙 v2)。
        self._b0 = N.canonical_whitespace(
            T.b0_system(self.intent_mode, self.vocab_version, self.role_words)
        ).encode("utf-8")
        self._b4b = N.canonical_whitespace(
            T.TEMPLATES["B4b.near_empty"]
        ).encode("utf-8")
        #: **注意の焦点**の欄(C9b G4)。``attention_columns`` のランだけ在る配列を 1 度だけ
        #: 掴む(``AgentState`` の配列は freeze/thaw で差し替わらない)。``None``= 焦点の無い
        #: ラン=**B5 の描画は 1 バイトも変わらない**。
        #: **B2(地物)は共有ブロック**(§2.4 ⑧ + §5 の共有 prefix)なので焦点で並べ替えない
        #: ——地物の焦点は描画に出さない(親へ報告済みの空欄)。
        self._focus_target: np.ndarray | None = (
            agents.focus_target if getattr(agents, "attention_columns", False) else None
        )
        #: **5 段目 5a(D-118 K2)**: 空腹を**語**で描くか(``energy_columns`` のラン=
        #: ``--hunger-model energy``)。``hunger`` はそのランでは語の段の写し(1/5/8/10)なので、
        #: 数値の代わりに ``T.HUNGER_WORDS`` の語を ``T.HUNGER_WORD_DRAW_MIN_STAGE`` 以上だけ描く。
        #: 欄の無いラン(v1)は従来の「空腹はNで閾値を超えています。」=**1 バイトも変わらない**。
        self._hunger_words: bool = bool(getattr(agents, "energy_columns", False))
        #: 個体 → (知人の集合, 知人の id 配列)。**構築時に固定**なので 1 度作れば使い回せる(C7)。
        self._acq_cache: dict[int, tuple[frozenset[int], np.ndarray]] = {}
        self._b1_cache: dict[int, bytes] = {}
        #: 鍵は ``(セル, 看板を見たか)``。既定(p_see 1.0)は第2要素が常に True=
        #: セルだけで引くのと同じ(命中率も同じ)。
        self._b2_cache: dict[tuple[int, bool], bytes] = {}
        self._b3_cache: dict[int, bytes] = {}
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
        #: 段 2c Q25: 名指しの即時閉店の補足(体 → (POI, 失敗の tick, 開店の分))。``engine.run`` が
        #: 意図の層のあるランだけ差し込む(``None``=従来どおり=描画は 1 バイトも変わらない)。
        self.named_closed_lookup: Callable[[int], tuple[int, int, int] | None] | None = None
        self.named_closed_notes = 0
        #: 4 段目(M17 露出): 看板行が載った (体, POI) の控え(``engine.run`` が tick ごとに取り出す)。
        #: ``None``=控えない(既定)。
        self.signage_exposures: list[tuple[int, int]] | None = None
        #: 注視ゲートの抽選回数(看板のあるセルで p_see<1.0 のときだけ増える)。
        self.signage_gate_draws = 0
        #: そのうち**通った**(看板行を載せた)回数。既定のランでは 0/0。
        self.signage_gate_shown = 0
        #: 5 段目 5c(層別の計数・描画は変えない): 看板のあるセルでの描画(eligible)・抽選(draws)・
        #: 看板行が載った(shown)を活動の種別ごとに。実効 p_see の分布(看板のあるセルの描画ごと)。
        n_k = len(P_SEE_ACTIVITY_KINDS)
        self.signage_by_kind = np.zeros((3, n_k), dtype=np.int64)
        self.signage_effective_p: dict[str, int] = {}

    # ---------------------------------------------------------- 前計算(1 tick 1 回)
    def prepare_tick(
        self,
        tick: int,
        *,
        salient_events: Mapping[int, Sequence[str]] | None = None,
        flow: np.ndarray | None = None,
        density: np.ndarray | None = None,
        noise_stage: np.ndarray | None = None,
        queues: Sequence[tuple[int, str, int]] | None = None,
        activity_rows: Mapping[int, Sequence[tuple[str, int]]] | None = None,
    ) -> None:
        """この tick のセル配列とハッシュを作る(**セル数ぶんの xxh64 が 1 本**)。

        Args:
            queues: B4b の材料 ``(POI, 表示名, 人数)`` の列
                (``engine.processes.crowd.CrowdProcess.queue_rows``)。セルあたり上位 1 件を
                「<店名>の行列に<人数>人」として ``B4b.near`` に載せる。
            activity_rows: **二層の段 2** の B4b の材料「セル → ((活動文, 人数), …)」
                (``engine.activity.ActivityLayer.cell_rows``)。``activity_line`` の 1 行を
                行列の行の**後**に足す(B4b の予算 40 tok に収まるときだけ)。行列も活動も無い
                セルは従来の固定文言。``None``(既定)では 1 バイトも変わらない。
                **起床条件 (i) の欄(B4 ダイジェスト)には混ぜない**(活動の変化を場所の変化
                として起床させない=新しい起床の源を足さない・expedient)。固定枠の描画だけに
                載せる(単一ランキングの腕には載せない・expedient)。
        """
        w = self.world
        n = w.n_cells
        when = self.clock_fn(int(tick))
        dens = w.cells.density if density is None else np.asarray(density)
        per_m2 = np.asarray(dens, dtype=np.float64) / np.maximum(
            self.assets.walkable_area_m2, 1.0
        )
        los = N.peg_stage_array(per_m2, T.DENSITY_LOS_EDGES_PER_M2)

        if noise_stage is not None:
            ns = np.asarray(noise_stage, dtype=np.uint8)
        elif np.any(w.cells.noise_stage):
            ns = np.asarray(w.cells.noise_stage, dtype=np.uint8)
        else:
            ns = self.assets.noise_stage_for_tick(when).astype(np.uint8)

        fl = np.zeros(n, dtype=np.uint8) if flow is None else np.asarray(flow, dtype=np.uint8)

        sal: dict[int, tuple[str, ...]] = {}
        digest = np.zeros(n, dtype=np.int32)
        if salient_events:
            for c, items in salient_events.items():
                lines = tuple(str(s) for s in items)
                if not lines:
                    continue
                sal[int(c)] = lines
                digest[int(c)] = int(xxh64("\x1f".join(lines).encode("utf-8")) & 0x7FFF_FFFF)

        # B4b(行列)は**セル動的**なので、変化検出器が読む欄(``b4_field_row`` の第4列)へ
        # 混ぜる。混ぜないと「B4b の文面が変わったのに起床条件(i) が鳴らない」取りこぼしが
        # 生まれる(C3 で B4 について潰した穴と同じ形)。列を増やすと ``hashes.b4_field_row``
        # の凍結形が動くので、**同じ列にダイジェストを畳む**(行列が無ければ従来どおり 0)。
        b4b_items = self._b4b_raw(queues)
        b4b = self._b4b_lines(b4b_items)
        for c, blob in b4b.items():
            mixed = int(xxh64(blob) & 0x7FFF_FFFF)
            digest[int(c)] = int((int(digest[int(c)]) * 31 + mixed) & 0x7FFF_FFFF)

        if activity_rows:
            b4b = self._merge_activity_lines(b4b, activity_rows)
        rows = H.b4_field_row(los, ns, fl, digest)
        # C7: セル順の連続座標(1 tick 1 回の gather)。個体数ぶんの 3 配列
        # =24 byte/体(390,067 体で 9.4 MB)。1 呼あたりのセル在席者ぶんの gather を消す。
        idx = _cell_index(self.agents.cell, n)
        xy_all = np.asarray(self.agents.xy, dtype=np.float64)
        order = idx["cell_order"]
        self._tickc = _TickCache(
            tick=int(tick),
            when=when,
            band5=N.time_band(when),
            los_stage=los,
            noise_stage=ns,
            flow=fl,
            salient=sal,
            salient_digest=digest,
            b4b=b4b,
            b4b_items=b4b_items,
            b4_field_rows=rows,
            b4_field_hash=H.field_row_hashes(rows),
            cell_x=np.ascontiguousarray(xy_all[order, 0]),
            cell_y=np.ascontiguousarray(xy_all[order, 1]),
            **idx,
        )

    @property
    def b4_field_rows(self) -> np.ndarray:
        """直近の ``prepare_tick`` が作った B4 描画欄 ``(n_cells, 4)`` int32。

        **エンジンの変化検出器(起床条件 (i))はこの 1 本を読む**。描画と検出が同じ欄を見るので
        「(i) が鳴らないのに文面が変わる」取りこぼしが構造的に 0 になる(§2.2/§5 の三役)。
        """
        return self._tickc.b4_field_rows

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
        """1 個体・1 起床ぶんの観測を描画する。

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

        Note:
            逐次ループ宣言(P4)1: **1 起床につき 1 回**。個体数ぶんのループは持たない。
        """
        if self._tickc.tick != int(tick):
            self.prepare_tick(int(tick))
        tc = self._tickc
        a = self.agents
        i = int(agent_id)
        cell = int(a.cell[i])
        kind = int(a.kind[i])
        hits0, misses0 = self.cache_hits, self.cache_misses

        blocks: "OrderedDict[str, bytes]" = OrderedDict()
        trunc: list[ch.TruncationReport] = []
        ranking = self.budget_mode is ch.BudgetMode.SINGLE_RANKING
        # D-59 (b): 看板の注視ゲート(§4 段1)。既定 p_see=1.0 では常に True=抽選も引かない。
        seen = self._signage_seen(i, cell, int(tick))
        # 4 段目(M17 露出): 注視ゲートを通って B2 に看板行が載った POI を控える(``--familiarity on``
        # のランだけ ``engine.run`` が list を差し込む=既定 None では 1 行も通らない・描画は不変)。
        if self.signage_exposures is not None and seen:
            _sp = self._signage_poi(cell)
            if _sp >= 0:
                self.signage_exposures.append((i, int(_sp)))
        # ablation ①: セル依存(B2/B4/B4b)は**1 本の池**なので 3 ブロックを一緒に組む。
        cellb = self._cell_blocks_ranked(cell, tc, trunc, seen) if ranking else None
        b6 = self._b6(i, wake_reason, last_result, cell, tc, last_action, inviter)
        blocks["B0"] = self._b0
        blocks["B1"] = self._b1(kind)
        blocks["B2"] = cellb["B2"] if cellb is not None else self._b2(cell, trunc, seen)
        blocks["B3"] = self._b3(tc)
        blocks["B4"] = cellb["B4"] if cellb is not None else self._b4(cell, tc, trunc)
        blocks["B4b"] = cellb["B4b"] if cellb is not None else tc.b4b.get(cell, self._b4b)
        blocks["B5"] = (
            self._b5_ranked(i, cell, tc, trunc, ch.estimate_tokens(b6.decode("utf-8")))
            if ranking
            else self._b5(i, cell, tc, trunc)
        )
        # 段 2c: 意図を持つ体だけ B5 に「いま <行為> のため <対象> へ向かっている」の 1 行
        blocks["B5"] = self._with_intent_line(i, blocks["B5"], b6)
        # 記憶 第 1 段 6b: 想起した記憶を B5 の**最後**に 1 行(on のランだけ・0 件なら出さない)
        recalled: tuple[int, ...] = ()
        if self.memory_recall is not None:
            blocks["B5"], recalled = self._with_memory_line(
                i, int(tick), blocks["B5"], b6, wake_reason, inviter
            )
        blocks["B6"] = b6

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
            tick=int(tick),
            blocks=blocks,
            text=text,
            block_hashes=bh,
            prefix_key=H.prefix_key([bh[b] for b in shared_ids], shared_ids),  # 共有 prefix(B0-B4b)のみ=§5
            prompt_hash=blake3_hex(b"\n".join(blocks[b] for b in T.BLOCK_IDS)),
            tokens_est=tokens,
            group_tokens=groups,
            truncations=tuple(trunc),
            recalled_rows=recalled,
            cache_hits=self.cache_hits - hits0,
            cache_misses=self.cache_misses - misses0,
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

    def _signage_poi(self, cell: int) -> int:
        """看板(a)に使う **POI の index**(無ければ ``-1``)。

        **看板の選び方はこの 1 本**(``_signage_body`` もここを通る)なので、注視ゲートが
        抽選に使う ``poi_id`` と実際に描かれる看板は常に同じものを指す。
        """
        if not self.signage_enabled:
            return -1
        A = self.assets
        if not (0 <= cell < A.n_cells):
            return -1
        n_poi = self.world.n_poi
        for j in A.visible_poi[cell]:
            if int(j) < n_poi:
                return int(j)
        return -1

    def _signage_body(self, cell: int) -> str | None:
        """看板(a)の**本文**(命令文除去済み・枠の切り詰め前)。

        ablation ⑥(§8 第1陣「広告ゼロ」)は ``signage_enabled=False`` でここを ``None`` に
        する。**固定枠と単一ランキングの両方**がこの 1 本を材料にしているので、腕は 1 箇所で
        効く(固定枠 → ``_signage`` が ``B2.signage_empty``・ランキング → 候補が空列)。
        D-59 (b) の注視ゲートも**同じ 1 本**の手前で切る(``_signage``/``_cell_candidates``)。

        Returns:
            見える表示が**無い**セルは ``None``、在るが命令文除去で本文が消えた場合は ``""``
            (この 2 つは描画が違う=前者は「見える表示はありません」・後者は素性タグだけの行)。
        """
        j = self._signage_poi(cell)
        if j < 0:
            return None
        A = self.assets
        w = self.world
        frozen = A.poi_signage[j] if j < len(A.poi_signage) else ""
        if frozen:
            return strip_imperatives(frozen).kept
        frm = int(w.pois.open_from[j]) // 60
        to = int(w.pois.open_to[j]) // 60
        return strip_imperatives(f"{A.poi_name[j]}の表示。営業は{frm}時から{to}時。").kept

    def signage_poi_by_cell(self) -> np.ndarray:
        """セル → B2 の看板行に出す POI(``_signage_poi`` と同じ 1 件・無ければ −1)。

        4 段目(M17 露出・親決定 (f)): 「セルに入った回 × そのセルの看板」の露出を数える側
        (``engine.familiarity``)が、描画と**同じ集合**を読むための口。起動時 1 回(セル数ぶん)。
        ``signage_enabled=False``(ablation ⑥)なら全部 −1。
        """
        n = int(self.assets.n_cells)
        return np.fromiter((self._signage_poi(c) for c in range(n)), dtype=np.int64, count=n)

    def activity_class_of(self, agent_id: int) -> int:
        """体 → 活動の種別の索引(:data:`P_SEE_ACTIVITY_KINDS`・5c・宣言)。

        1. 会話の成立(``Activity.CONVERSING``)→ 連れとの会話中 2. (通話/スマホ操作中の旗は無い)
        3. 活動層のあるラン: ``activity_kind``(目的地つき移動/あたり/在店/その場・なし=その場)
        4. 活動層の無いラン: 歩行中=目的地つき移動・在店(``SHOPPING``)=在店・他=その場。
        """
        r = self.agents.registry
        act = int(r.activity[agent_id])
        if act == int(Activity.CONVERSING):
            return 5
        if "activity_kind" in r.arrays:
            k = int(r.activity_kind[agent_id])
            return {int(ActivityKind.MOVE_TO): 0, int(ActivityKind.WANDER): 1,
                    int(ActivityKind.IN_SHOP): 2}.get(k, 3)
        if act == int(Activity.MOVING):
            return 0
        if act == int(Activity.SHOPPING):
            return 2
        return 3

    def activity_classes(self, agent_ids: np.ndarray) -> np.ndarray:
        """体の配列 → 活動の種別の索引の配列(:meth:`activity_class_of` の配列版・配列演算)。"""
        a = np.asarray(agent_ids, dtype=np.int64)
        r = self.agents.registry
        act = np.asarray(r.activity)[a]
        out = np.full(a.size, 3, dtype=np.int64)
        if "activity_kind" in r.arrays:
            k = np.asarray(r.activity_kind)[a]
            out[k == int(ActivityKind.MOVE_TO)] = 0
            out[k == int(ActivityKind.WANDER)] = 1
            out[k == int(ActivityKind.IN_SHOP)] = 2
        else:
            out[act == int(Activity.MOVING)] = 0
            out[act == int(Activity.SHOPPING)] = 2
        out[act == int(Activity.CONVERSING)] = 5
        return out

    def effective_p_see(self, agent_ids: np.ndarray) -> np.ndarray:
        """体の配列 → 実効 p_see=min(1, p_see × 乗数[活動の種別])(5c・配列演算)。"""
        mult = self._p_see_mult[self.activity_classes(agent_ids)]
        return np.minimum(1.0, float(self.signage_p_see) * mult)

    def p_see_activity_summary(self) -> dict:
        """manifest ``p_see_activity``: 乗数表・既定か・活動の種別ごとの計数・実効 p_see の分布。"""
        by = self.signage_by_kind
        return {
            "table": dict(self.p_see_activity),
            "identity": bool(self._p_see_identity),
            "signage_p_see": float(self.signage_p_see),
            "applies_to": "p_see only (M4 (a)): the B2 visible rows are unchanged",
            "by_kind": {
                k: {"eligible": int(by[0, j]), "draws": int(by[1, j]), "shown": int(by[2, j])}
                for j, k in enumerate(P_SEE_ACTIVITY_KINDS)
            },
            "effective_p_see": dict(sorted(self.signage_effective_p.items())),
        }

    def _signage_seen(self, agent_id: int, cell: int, tick: int) -> bool:
        """**看板の注視ゲート**(知覚契約書 §4 段1・D-59 (b) ユーザー決定 2026-09-17)。

        体×看板×tick の**決定論的ベルヌーイ**。乱数は ``attention.gate_stage1``
        (``core.rng.stream`` の Philox4x64・ドメイン ``perception.attention.p_see``・
        カウンタ ``(tick, agent_id, poi_id)``)なので、

        - 同じ ``(seed, tick, agent_id, poi_id)`` は**常に同じ結果**(テープから再現できる)、
        - 体を増やしても既存の体の列は動かない(カウンタベースの性質・運用設計書 §1.4 T4)、
        - tick・体・看板のどれが違えば独立な抽選になる。

        既定(``p_see=1.0``)と**看板の無いセル**では抽選を引かない(描画が変わらないため)。
        帯の出典は §4 段1(中小媒体 ``P_SEE_MEDIUM_RANGE`` 0.14-0.40・大型ビジョン 0.63-0.78)。

        逐次ループ宣言(P4): **1 起床につき 1 回**(``render`` の中の 1 回・個体数ぶんの
        ループは持たない)。既定のランでは 0 回。

        **5 段目 5c(D-117)**: 実効 p_see=min(1, p_see × 乗数[活動の種別])。乗数表が全部 1.0(既定)なら
        実効 p_see=p_see で抽選の有無も乱数の列も従来と同じ(同じカウンタ・同じ u を比べる)。
        看板のあるセルの描画は活動の種別ごとに数える(描画は変えない)。
        """
        poi = self._signage_poi(cell)
        k = self.activity_class_of(int(agent_id)) if poi >= 0 else -1
        p = float(self.signage_p_see)
        if not self._p_see_identity and k >= 0:
            p = min(1.0, p * float(self._p_see_mult[k]))
        if k >= 0:
            self.signage_by_kind[0, k] += 1
            key = f"{p:.4f}"
            self.signage_effective_p[key] = self.signage_effective_p.get(key, 0) + 1
        if p >= 1.0:
            if k >= 0:
                self.signage_by_kind[2, k] += 1
            return True
        if poi < 0:
            return True  # 見える看板が無いセル=ゲートの対象外(描画は同じ)
        self.signage_gate_draws += 1
        self.signage_by_kind[1, k] += 1
        if p <= 0.0:
            return False  # random() は [0,1) なので ``< 0.0`` は常に偽=短絡と同値
        ok = bool(
            gate_stage1(
                1,
                p,
                seed=self.seed,
                domain_counters=(int(tick), int(agent_id), int(poi)),
            )[0]
        )
        if ok:
            self.signage_gate_shown += 1
            self.signage_by_kind[2, k] += 1
        return ok

    def _b3(self, tc: _TickCache) -> bytes:
        got = self._b3_cache.get(tc.band5)
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        h, m = N.format_time(tc.when)
        weather, daylight, heat = self.assets.weather(tc.when)
        lines = [
            T.TEMPLATES["B3.time"].format(hour=h, minute=m),
            T.TEMPLATES["B3.weather"].format(weather=weather, daylight=daylight),
            T.TEMPLATES["B3.heat"].format(heat=heat),
        ]
        out = N.join_lines(lines).encode("utf-8")
        self._b3_cache[tc.band5] = out
        return out

    def _b4b_raw(
        self, queues: Sequence[tuple[int, str, int]] | None
    ) -> dict[int, tuple[str, ...]]:
        """待ち行列 → セル別の B4b **生の項目**(セルあたり上位 1 件)。

        Note:
            逐次ループ宣言(P4): **行列行数**ぶん(``queue_rows(k)`` の k・既定 1-3)。
            セル数・個体数には比例しない。
        """
        if not queues:
            return {}
        poi_cell = np.asarray(self.world.pois.cell, dtype=np.int64)
        best: dict[int, tuple[int, str]] = {}
        for poi, name, count in queues:  # 逐次: 行列行数ぶん
            j = int(poi)
            if not (0 <= j < poi_cell.size) or int(count) <= 0:
                continue
            c = int(poi_cell[j])
            if c < 0:
                continue
            prev = best.get(c)
            if prev is None or int(count) > prev[0]:
                best[c] = (int(count), str(name))
        return {c: (f"{name}の行列に{count}人",) for c, (count, name) in best.items()}

    def _b4b_lines(self, items: Mapping[int, tuple[str, ...]]) -> dict[int, bytes]:
        """B4b の生の項目 → セル別の描画バイト(固定枠の切り詰めを掛ける)。"""
        out: dict[int, bytes] = {}
        for c, raw in items.items():
            kept, _ = ch.truncate_lines(list(raw), "B4b.near")
            if not kept:
                continue
            out[c] = N.canonical_whitespace(
                T.TEMPLATES["B4b.near"].format(items=N.LIST_SEPARATOR.join(kept))
            ).encode("utf-8")
        return out

    def _merge_activity_lines(
        self, b4b: Mapping[int, bytes], activity_rows: Mapping[int, Sequence[tuple[str, int]]]
    ) -> dict[int, bytes]:
        """行列の B4b にセルの活動の 1 行を足す(二層の段 2)。B4b 40 tok を超えるなら足さない。

        逐次ループ宣言(P4): 活動の行があるセルの数ぶん(≤ セル数)。
        """
        out = dict(b4b)
        budget = int(T.BLOCK_TOKEN_BUDGET["B4b"])
        for c, rows in activity_rows.items():
            line = activity_line(rows)
            if not line:
                continue
            prev = out.get(int(c))
            if prev is None:
                out[int(c)] = N.canonical_whitespace(line).encode("utf-8")
                continue
            merged = N.join_lines([prev.decode("utf-8"), N.canonical_whitespace(line)])
            if ch.estimate_tokens(merged) <= budget:
                out[int(c)] = merged.encode("utf-8")
        return out

    def _b4(self, cell: int, tc: _TickCache, trunc: list[ch.TruncationReport]) -> bytes:
        if not (0 <= cell < tc.los_stage.size):
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
        key = (cell, int(tc.b4_field_hash[cell]))
        got = self._b4_cache.get(key)
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        los = int(min(tc.los_stage[cell], len(T.DENSITY_LOS_LETTERS) - 1))
        ns = int(min(tc.noise_stage[cell], len(T.NOISE_STAGE_VOCAB) - 1))
        lines = [
            T.TEMPLATES["B4.density"].format(
                stage=T.DENSITY_LOS_LETTERS[los], flow=T.FLOW_WORDS[int(tc.flow[cell])]
            ),
            T.TEMPLATES["B4.noise"].format(
                stage=T.NOISE_STAGE_VOCAB[ns], band=T.NOISE_BAND_WORDS[ns]
            ),
        ]
        items = list(tc.salient.get(cell, ()))
        kept, rep = ch.truncate_lines(items, "B4.salient")
        trunc.append(rep)
        lines.append(
            T.TEMPLATES["B4.salient"].format(items=N.LIST_SEPARATOR.join(kept))
            if kept
            else T.TEMPLATES["B4.salient_empty"]
        )
        out = N.join_lines(lines).encode("utf-8")
        self._b4_cache[key] = out
        return out

    def _b5(
        self, i: int, cell: int, tc: _TickCache, trunc: list[ch.TruncationReport]
    ) -> bytes:
        a = self.agents
        lines: list[str] = []
        # 内受容(閾値割れ分のみ)
        crossed = []
        for name, label in zip(INTEROCEPTION_FIELDS, ("空腹", "体力", "体感温度")):
            v = int(a.registry.field(name)[i])
            if name == "hunger" and self._hunger_words:
                word = _hunger_word(v)
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
        self_lines = [
            T.TEMPLATES["B5.holding"].format(
                money=f"{int(a.money[i]):,}",
                hands=T.HANDS_WORDS[1 if int(a.holdings[i]) > 0 else 0],
            ),
            T.TEMPLATES["B5.recent"].format(
                activity=_activity_word(int(a.activity[i]), self.vocab_version == "v3")
            ),
        ]
        kept, rep = ch.truncate_lines(self_lines, "B5.self", max_items=2)
        lines += kept
        trunc.append(rep)
        # 近接人物 上位k(密度逓減 3/2/1)+知人は常に掲載
        near = self._nearby(i, cell, tc)
        kept, rep = ch.truncate_lines(near, "B5.near_person", max_items=len(near) or None)
        trunc.append(rep)
        lines.append(
            T.TEMPLATES["B5.near_person"].format(items=N.LIST_SEPARATOR.join(kept))
            if kept
            else T.TEMPLATES["B5.near_person_empty"]
        )
        # 被注視(T2 の転置。無ければ固定文言)
        nw = 0 if self.watched_by is None else int(self.watched_by[i])
        lines.append(
            T.TEMPLATES["B5.watched"].format(n=nw) if nw > 0 else T.TEMPLATES["B5.watched_empty"]
        )
        return N.join_lines(lines).encode("utf-8")

    def _intent_text(self, i: int) -> str:
        """意図を持つ体の 1 行(持たなければ ``""``)。SoA の意図の欄を読むだけ。"""
        arrays = self.agents.registry.arrays
        if "intent_action" not in arrays:
            return ""
        code = int(arrays["intent_action"][i])
        if code == INTENT_NONE:
            return ""
        word = INTENT_ACTION_WORDS.get(code)
        if word is None:
            return ""
        kind = int(arrays["intent_kind"][i])
        tgt = int(arrays["intent_target"][i])
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

    def _with_intent_line(self, i: int, b5: bytes, b6: bytes) -> bytes:
        """B5 の「直近」の行の後に意図の行を差し込む(個体群の予算 300 を超えるなら差し込まない)。"""
        line = self._intent_text(i)
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
        self, i: int, tick: int, b5: bytes, b6: bytes, wake_reason: int | str, inviter: int | None
    ) -> tuple[bytes, tuple[int, ...]]:
        """B5 の最後に「記憶」の 1 行(6b・M4)。チャネル 60 tok・個体枠 300 を超えるなら末尾の項から削る。"""
        cond = int(wake_reason) if isinstance(wake_reason, (int, np.integer)) else -1
        items = list(self.memory_recall(i, int(tick), cond, -1 if inviter is None else int(inviter)))
        if not items:
            return b5, ()
        when = self.clock_fn(int(tick))
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
            return b5, ()
        kept = texts[:n_keep]
        self.memory_lines += 1
        self.memory_items += len(kept)
        tok = ch.estimate_tokens(line)
        self.memory_line_tokens[tok] = self.memory_line_tokens.get(tok, 0) + 1
        return out, tuple(rows[: len(kept)])

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

    def _nearby(self, i: int, cell: int, tc: _TickCache) -> list[str]:
        """同一セル在席者から近接上位 k(密度逓減)+知人常掲を作る。"""
        return [text for text, _d in self._nearby_items(i, cell, tc)]

    def _nearby_items(self, i: int, cell: int, tc: _TickCache) -> list[tuple[str, float]]:
        """``_nearby`` の各行と**その距離[m]**(単一ランキングの視角に使う)。

        近接 k の選び方(密度逓減 3/2/1・知人常掲)は §3 人物④の規則なので**両モード共通**。
        ablation ① が外すのは §3.2 のチャネル枠(トークン上限と件数)だけ。

        C7 性能修正(挙動不変): セル在席者ぶんの **Python 反復を全廃**した。
        以前は ① 距離の辞書(``{id: sqrt(d2)}``)と ② ``set(peers)`` を**毎呼**作っており、
        390,067 体(セル人口 1.4 万)で 1 呼 17 ms・llm 位相 46 s/tick になっていた
        (cProfile: 1 呼あたり 13,663 反復)。いまは
        ③ 座標は ``prepare_tick`` が作ったセル順の**連続配列**から取り(gather 無し)、
        ④ 自分の行は逆置換 ``cell_pos`` で O(1) に外し、
        ⑤ 知人の同セル判定は ``cell_pos`` の範囲比較(知人数ぶん)、
        ⑥ ``sqrt`` は**採った数件だけ**。
        **順序・同点処理・上位 k・距離の値は 1 ビットも変えていない**
        (``np.argpartition`` に渡す配列が旧実装と同一=``d2`` の並びまで同じ)。
        """
        a = self.agents
        if not (0 <= cell < tc.los_stage.size) or tc.cell_start.size == 0:
            return []
        lo, hi = int(tc.cell_start[cell]), int(tc.cell_end[cell])
        m = hi - lo
        if m <= 0:
            return []
        # d2 は「セル順の連続配列 − 自分」。旧実装の ``((xy[peers]-xy[i])**2).sum(1)`` と
        # **同じ順序・同じ丸め**(x²+y² の加算順まで同じ)。自分の座標は**2 スカラーだけ**読む
        # (``np.asarray(a.xy, float64)`` は float32 SoA の**全体コピー**=390,067 体で 1.6 ms/呼)。
        dx = tc.cell_x[lo:hi] - float(a.xy[i, 0])
        dy = tc.cell_y[lo:hi] - float(a.xy[i, 1])
        d2_full = dx * dx + dy * dy
        ids_full = tc.cell_order[lo:hi]
        p = int(tc.cell_pos[i]) - lo if 0 <= i < tc.cell_pos.size else -1
        if 0 <= p < m:  # 自分の行だけ外す(= 旧 ``peers[peers != i]``・順序は保たれる)
            peers = np.delete(ids_full, p)
            d2 = np.delete(d2_full, p)
        else:  # 自分がこの tick のセル索引に居ない(旧実装でも素通り)
            peers, d2 = ids_full, d2_full
        if peers.size == 0:
            return []
        los = int(tc.los_stage[cell])
        k = 3 if los <= 1 else (2 if los <= 3 else 1)  # 疎3/中2/密1(境界は expedient)
        take = min(k, peers.size)
        sel = peers[np.argpartition(d2, take - 1)[:take]] if peers.size > take else peers
        friends, friend_ids = self._acquaintances_of(i)
        chosen_set = {int(x) for x in sel}
        if friend_ids.size:  # 知人常掲(§3 人物④)= 同セルの知人を足す(知人数ぶん)
            pf = tc.cell_pos[friend_ids]
            chosen_set |= {
                int(x) for x in friend_ids[(pf >= lo) & (pf < hi) & (friend_ids != i)]
            }
        # C9b G4: **注意の焦点**が同じセルの人物なら常に載せ、**先頭に置く**
        # (UE AI Perception の ``Dominant Sense`` ではなく「焦点は優先して描く」だけ)。
        # ablation ①(``--budget-mode ranking``)では ``_rank_items`` が顕著性で並べ直すので
        # 先頭は保たれない——**掲載は保たれる**(順序は ablation の主題そのものなので譲る)。
        focus = -1
        if self._focus_target is not None:
            f = int(self._focus_target[i])
            if 0 <= f < int(a.n) and f != i:
                pf = int(tc.cell_pos[f])
                if lo <= pf < hi:
                    focus = f
                    chosen_set.add(f)
        chosen = sorted(chosen_set)
        if focus >= 0:  # 焦点だけ先頭へ(残りの並びは従来どおり id 昇順)
            chosen = [focus] + [x for x in chosen if x != focus]
        q = tc.cell_pos[np.asarray(chosen, dtype=np.int64)] - lo
        if 0 <= p < m:
            q = q - (q > p)  # 自分の行を外したぶん詰める
        dist = np.sqrt(d2[q])  # 採った数件だけ sqrt(旧: セル在席者ぶんの辞書)
        return [
            (
                f"{person_word(j)}({'知人' if j in friends else '未知'})",
                max(float(dv), 0.1),
            )
            for j, dv in zip(chosen, dist)
        ]

    def _acquaintances_of(self, i: int) -> tuple[frozenset[int], np.ndarray]:
        """個体 → (知人の集合, 知人 id の配列)。**1 度作って使い回す**(C7)。

        知人表は ``Renderer`` の構築時に固定される(§3 人物④「知人は常に掲載」)ので、
        毎呼 ``set(...)`` を組み直す必要がない。範囲外の id はここで落とす
        (旧実装では同セル集合との積で自然に落ちていた)。
        """
        got = self._acq_cache.get(i)
        if got is None:
            names = frozenset(int(x) for x in self.acquaintances.get(i, ()))
            arr = np.fromiter(sorted(names), dtype=np.int64, count=len(names))
            n = int(self.agents.n)
            if arr.size:
                arr = arr[(arr >= 0) & (arr < n)]
            got = (names, arr)
            self._acq_cache[i] = got
        return got

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
        self, cell: int, tc: _TickCache, shown: bool = True
    ) -> tuple[dict[str, list[str]], str]:
        """セル依存(B2/B4/B4b)の候補と、チャネルでない構造行(B2 場所)。

        ``shown=False``(注視ゲートで落ちた・D-59 (b))は看板の候補を空列にする
        =**⑥ 広告ゼロと同じ道**(材料は ``_signage_body`` 1 本のまま)。
        """
        A = self.assets
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
        if 0 <= cell < tc.los_stage.size:
            los = int(min(tc.los_stage[cell], len(T.DENSITY_LOS_LETTERS) - 1))
            ns = int(min(tc.noise_stage[cell], len(T.NOISE_STAGE_VOCAB) - 1))
            cand["B4.density"] = [
                T.TEMPLATES["B4.density"].format(
                    stage=T.DENSITY_LOS_LETTERS[los], flow=T.FLOW_WORDS[int(tc.flow[cell])]
                )
            ]
            cand["B4.noise"] = [
                T.TEMPLATES["B4.noise"].format(
                    stage=T.NOISE_STAGE_VOCAB[ns], band=T.NOISE_BAND_WORDS[ns]
                )
            ]
            cand["B4.salient"] = list(tc.salient.get(cell, ()))
            cand["B4b.near"] = list(tc.b4b_items.get(cell, ()))
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
        cell: int,
        tc: _TickCache,
        trunc: list[ch.TruncationReport],
        shown: bool = True,
    ) -> dict[str, bytes]:
        """B2/B4/B4b を**セル依存の 1 本の池**(≤250 tok)で組む(ablation ①)。

        材料はセルの情報だけ(個体依存語は 1 語も入らない)ので、§2.4 ⑧「同セル同時間帯の
        2 体でバイト差分ゼロ」は固定枠と同じく成り立つ。キャッシュ鍵は ``(セル, B4 欄ハッシュ)``
        (固定枠の B2 はセルだけで足りるが、単一ランキングでは B4 の内容が B2 の採否を動かす)。
        """
        fh = int(tc.b4_field_hash[cell]) if 0 <= cell < tc.b4_field_hash.size else -1
        # 第3要素=注視ゲート(D-59 (b))。既定 p_see=1.0 では常に True=従来の 2 要素鍵と同じ。
        key = (int(cell), fh, bool(shown))
        got = self._rank_cell_cache.get(key)
        if got is not None:
            self.cache_hits += 1
            trunc.extend(got[1])
            return got[0]
        self.cache_misses += 1
        cand, place = self._cell_candidates(cell, tc, shown)

        def build(kept: Mapping[str, list[str]], order: Sequence[str]) -> dict[str, bytes]:
            rows: dict[str, list[str]] = {"B2": [place], "B4": [], "B4b": []}
            for cid in order:
                block = "B4b" if cid.startswith("B4b.") else cid.split(".", 1)[0]
                rows[block].extend(self._lines_for(cid, kept[cid]))
            return {b: N.join_lines(rows[b]).encode("utf-8") for b in ("B2", "B4", "B4b")}

        out, reports = self._pool_render(cand, {}, ("B2", "B4", "B4b"), "cell", 0, build)
        self._rank_cell_cache[key] = (out, reports)
        trunc.extend(reports)
        return out

    def _b5_ranked(
        self,
        i: int,
        cell: int,
        tc: _TickCache,
        trunc: list[ch.TruncationReport],
        reserve_tokens: int,
    ) -> bytes:
        """B5 を**個体の 1 本の池**(≤220 tok)で組む(ablation ①)。

        群予算(個体 ≤300)から B6 の実測ぶんを差し引いた残りが上限になる。
        """
        a = self.agents
        overrides: dict[tuple[str, int], dict[str, float]] = {}
        crossed: list[str] = []
        span = max(1, T.INTERO_SCALE_MAX - INTERO_UP_EDGES[0])
        for name, label in zip(INTEROCEPTION_FIELDS, ("空腹", "体力", "体感温度")):
            v = int(a.registry.field(name)[i])
            if name == "hunger" and self._hunger_words:
                word = _hunger_word(v)
                if word is not None:
                    overrides[("B5.intero", len(crossed))] = {
                        "deviance": min(1.0, (v - INTERO_UP_EDGES[0]) / span)
                    }
                    crossed.append(word)
                continue
            if v >= INTERO_UP_EDGES[0]:
                overrides[("B5.intero", len(crossed))] = {
                    "deviance": min(1.0, (v - INTERO_UP_EDGES[0]) / span)
                }
                crossed.append(f"{label}は{v}で閾値を超えています。")
        near = self._nearby_items(i, cell, tc)
        for k, (_text, d) in enumerate(near):
            overrides[("B5.near_person", k)] = {"distance_m": float(d)}
        nw = 0 if self.watched_by is None else int(self.watched_by[i])
        cand: dict[str, list[str]] = {
            "B5.intero": crossed,
            "B5.self": [
                T.TEMPLATES["B5.holding"].format(
                    money=f"{int(a.money[i]):,}",
                    hands=T.HANDS_WORDS[1 if int(a.holdings[i]) > 0 else 0],
                ),
                T.TEMPLATES["B5.recent"].format(
                    activity=_activity_word(int(a.activity[i]), self.vocab_version == "v3")
                ),
            ],
            "B5.near_person": [t for t, _d in near],
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

    def _b6(
        self,
        i: int,
        wake_reason: int | str,
        last_result: int | None,
        cell: int,
        tc: _TickCache,
        last_action: str | None = None,
        inviter: int | None = None,
    ) -> bytes:
        a = self.agents
        if inviter is not None and int(inviter) >= 0:
            # §6 起床(ii) 被招待: 誰に話しかけられたかを**個体ブロック**で名指す。
            # B6 は個体ブロックなので規約⑧(B0-B4b のバイト一致)には触れない。
            reason = INVITE_REASON.format(person=person_word(int(inviter)))
        elif isinstance(wake_reason, str):
            reason = wake_reason
        else:
            r = int(wake_reason)
            if r == int(WakeCondition.ACTIVITY_EXPIRY):
                # 二層の段 2: 満了入口(語彙 v3 の活動層が立つランだけ来る)
                reason = ACTIVITY_EXPIRY_REASON
            else:
                reason = T.WAKE_REASON_TEXT[r] if 0 <= r < len(T.WAKE_REASON_TEXT) else (
                    T.WAKE_REASON_TEXT[3]
                )
        lines = [T.TEMPLATES["B6.wake"].format(reason=reason)]
        code = int(a.last_result[i]) if last_result is None else int(last_result)
        v3 = self.vocab_version == "v3"
        acted = last_action or _activity_word(int(a.activity[i]), v3)
        if int(a.last_result_tick[i]) < 0 and last_result is None:
            lines.append(T.TEMPLATES["B6.result_none"])
        elif code == int(ResultCode.OK):
            lines.append(T.TEMPLATES["B6.result_ok"].format(action=acted))
        else:
            why = RESULT_TEXT.get(code, "不明な理由")
            observed = self._observation(i, code, cell, tc)
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
        return N.join_lines(lines).encode("utf-8")

    def _observation(self, i: int, code: int, cell: int, tc: _TickCache) -> str:
        """R4 §6「失敗理由+**観測値**」。現在値から再構成する(C2 は詳細を持たない)。"""
        a = self.agents
        w = self.world
        if code == int(ResultCode.MONEY_SHORT):
            price = self._cheapest_price(cell)
            money = N.format_money(int(a.money[i]))
            return f"(所持金{money}・最も安い品は{N.format_money(price)})" if price else f"(所持金{money})"
        if code == int(ResultCode.CLOSED):
            note = self._named_closed_text(i)
            if note:
                return note
            nxt = self._next_open_hour(cell)
            return f"(次の開店は{nxt}時)" if nxt is not None else ""
        if code == int(ResultCode.FARE_SHORT):
            return f"(所持金{N.format_money(int(a.money[i]))})"
        return ""

    def _named_closed_text(self, i: int) -> str:
        """Q25: 名指しの店が見えるが閉店で歩かずに失敗した体だけの補足の 1 句(それ以外は ``""``)。

        ``named_closed_lookup``(``engine.run`` が渡す・体 → ``(POI, 失敗の tick, 開店の分)``)が
        返した tick が ``last_result_tick`` と一致するときだけ載せる(=その失敗の直後の起床だけ)。
        """
        look = self.named_closed_lookup
        if look is None:
            return ""
        got = look(int(i))
        if not got:
            return ""
        poi, t, opens = (int(x) for x in got)
        if int(self.agents.last_result_tick[i]) != t:
            return ""
        names = self.assets.poi_name
        name = str(names[poi]) if 0 <= poi < len(names) else NAMED_CLOSED_FALLBACK_NAME
        self.named_closed_notes += 1
        return named_closed_note(name, opens)

    def _cheapest_price(self, cell: int) -> int:
        if not (0 <= cell < self.world.n_cells):
            return 0
        m = self.world.pois.cell == cell
        return int(self.world.pois.price[m].min()) if m.any() else 0

    def _next_open_hour(self, cell: int) -> int | None:
        if not (0 <= cell < self.world.n_cells):
            return None
        m = self.world.pois.cell == cell
        if not m.any():
            return None
        return int(self.world.pois.open_from[m].min()) // 60

    # ---------------------------------------------------------- 監査
    @property
    def cache_hit_rate(self) -> float:
        """共有ブロック(B1/B2/B3/B4)のキャッシュ命中率。"""
        total = self.cache_hits + self.cache_misses
        return float(self.cache_hits) / total if total else 0.0

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
            f"template_sha256={T.template_sha256()[:16]}"
            f"{frozen}"
        )


# ------------------------------------------------------------------ 補助
def person_word(agent_id: int) -> str:
    """個体 id → 観測に出る人 ID の表層(``P-17``)。

    ``B5.near_person`` の ``P-<id>(未知/知人)`` と**同じ表層**にする(行動契約書 §1-2 の
    「対象: 人ID」・``llm.contract`` の ``_PERSON_RE`` が読む形)。
    """
    return f"P-{int(agent_id)}"


def _activity_word(code: int, v3: bool = False) -> str:
    words = ACTIVITY_WORDS_V3 if v3 else ACTIVITY_WORDS
    return words[code] if 0 <= code < len(words) else words[0]


def _cell_index(cell: np.ndarray, n_cells: int) -> dict[str, np.ndarray]:
    """セル → 在席個体の CSR(1 tick 1 回・ベクトル演算)。"""
    c = np.asarray(cell, dtype=np.int64)
    order = np.argsort(c, kind="stable")
    sorted_c = c[order]
    idx = np.arange(n_cells, dtype=np.int64)
    pos = np.empty(order.size, dtype=np.int64)  # 逆置換: 個体 → order 上の位置(C7)
    pos[order] = np.arange(order.size, dtype=np.int64)
    return {
        "cell_order": order,
        "cell_start": np.searchsorted(sorted_c, idx, side="left"),
        "cell_end": np.searchsorted(sorted_c, idx, side="right"),
        "cell_pos": pos,
    }
