"""llm.undefined — 未定義行動の受理5段(行動契約書 §7・決定台帳 行16)。

正典(逐語・行動契約書 §7)
    「段0 辞書写像(ゼロ呼)→段1 未定義行動レコード+失敗フィードバック+計数→段2 同一行動が
    閾値N(初期10体)で裁定LLMが1呼で契約行(前提/効果/コスト/失敗/台帳照合1行)を生成→
    段3 保存則・性能予算に触れる行は自動テスト+親検収まで不採用→段4 採用後は語彙に加わり
    2回目以降は決定論参照(判例化・R8と接続)。制度的事実に触れる場合はcounts_asへ登録。
    Nは較正パラメータ。」
- 行動契約書 §6: 失敗フィードバックは「直前の<行動>は失敗(理由=…)。**いま可能: <3語>**」。
  未定義行動の文面は 「未定義の行動『…』。いま可能な行動: 待機/休憩/移動」。
- 行動契約書 §2 共通の必須事項③: 「**失敗しない行動が常に1つ以上(待機)**」=段1の落とし先。

逐次ループ宣言(P4)
- ``UndefinedActionRegistry.observe``: **辞書表の語数**ぶんの部分一致ループ(段0)。
  1呼=1回で個体数・tick 数に比例しない。裁定(段2)は「新しい語が閾値に達したとき」だけ
  1呼(``LLMClient.complete``)で、常設の逐次ループではない。

C6 段0 の拡張(2026-09-09・実 LLM スモークのテープが根拠)
- 初回スモーク(5,000体×24tick・Qwen3-8B INT8・温度0)で**未定義行動 43 件**。中身は語彙外の
  行動語(探索・観察・調査・探す・調べる)。契約書 §7 段0「辞書写像」の**枠内**で表を広げた
  (``SYNONYMS_C6``・語彙12語+役割語は不変)。方針は既存表に合わせ、
  **移動を伴う探索**は ``移動``・**その場の観察/確認**は ``待機``(既存の「様子を見る→待機」に接続)。
- 第2弾(``--fleet-debug-dir``・60tick・2,083呼): ``unknown_action_word`` 96 の内訳は
  探索 50・**通勤 16**・観察 9・調査 ほか。通勤系(通勤/通学/出勤/退勤/出社/登校)を ``移動`` へ。
  **``通報``・``退去``・``購入`` は §2.1 の12語そのもの**なので辞書には入れない(語彙一致で通る)。

expedient(本モジュール分)
- **辞書表(段0)の中身と版**(``SYNONYM_TABLE_VERSION``)。契約書は「辞書写像」としか
  言わず語を与えていない。品質プローブv0 ``tools/quality_probe_v0/scorer.py`` の
  ``ACTION_SYNONYMS`` を出発点に、12語+役割語へ拡張した。
- 部分一致(完全一致で外れたら**最長一致**の語で写す)。
- 「帰る/帰宅」は ``移動`` へ写すが、**対象(=自宅セル)はエンジンの仕事**なので
  ``target_hint="home"`` を付けて返すだけ(パーサ側で自宅セルIDを作らない)。
- 閾値 **N=10 体**(契約書「初期10体」)・記録簿の上限 ``log_limit=4096`` 行(有界化は
  状態成長宣言 D-R2-6 の要求。契約書に値はない)。
- 段3 のキーワード表(保存則/在庫/所持金/性能/予算/faucet/sink)。契約書は
  「保存則・性能予算に触れる行」としか言わない。
- 裁定プロンプトの文面(``ADJUDICATION_TEMPLATE``)。契約書は「1呼で契約行(前提/効果/
  コスト/失敗/台帳照合1行)」としか言わない。**文面凍結の対象**(版を上げずに変えない)。
"""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final, Iterable, Mapping, Sequence

from shibuya.llm.contract import (
    ACTION_SPECS,
    DEFAULT_VOCAB_VERSION,
    ActionSpec,
    action_code_of,
    action_words,
    check_vocab_version,
)

__all__ = [
    "SYNONYM_TABLE_VERSION",
    "SYNONYMS",
    "SYNONYMS_C6",
    # ---- 段0 辞書 v3(語彙 v2 用・D-71 §3 E)。v1 の表と版は 1 行も動かさない ----
    "SYNONYMS_V3_DIFF",
    "SYNONYMS_V3",
    "SYNONYM_TABLE_VERSION_V3",
    "SYNONYM_TABLE_VERSION_BY_VOCAB",
    "synonym_table_version",
    "synonym_table",
    "TARGET_HINTS",
    "FALLBACK_ACTIONS",
    "ADJUDICATION_TEMPLATE",
    "REVIEW_KEYWORDS",
    "DEFAULT_THRESHOLD_AGENTS",
    "ProposalStatus",
    "UndefinedActionRecord",
    "Proposal",
    "UndefinedOutcome",
    "undefined_feedback",
    "map_synonym",
    "UndefinedActionRegistry",
]

#: 辞書表の版(**expedient**・表を変えたら上げる。ランの manifest に載せる想定)。
#: v1 = C6 初回スモークの語彙外行動語(探索・観察・調査・探す・調べる)を足した版。
#: v2 = ``--fleet-debug-dir`` の実測(``unknown_action_word`` 96)で出た通勤系を足した版。
SYNONYM_TABLE_VERSION: Final[str] = "undefined-synonyms-v2"

#: 段0 辞書写像(表層の言い換え → 契約語彙)。**ゼロ呼**。
_SYNONYMS_V0: Final[Mapping[str, str]] = {
    # 移動
    "歩く": "移動",
    "歩いていく": "移動",
    "向かう": "移動",
    "行く": "移動",
    "移動する": "移動",
    "出発": "移動",
    "帰る": "移動",
    "帰宅": "移動",
    "戻る": "移動",
    "登る": "移動",
    "渡る": "移動",
    # 乗車・降車
    "乗る": "乗車",
    "電車に乗る": "乗車",
    "改札を通る": "乗車",
    "降りる": "降車",
    "下車": "降車",
    # 購入
    "買う": "購入",
    "買い物": "購入",
    "購入する": "購入",
    "注文": "購入",
    "食べる": "購入",
    "飲む": "購入",
    "支払う": "購入",
    # 待機
    "待つ": "待機",
    "待機する": "待機",
    "様子を見る": "待機",
    "何もしない": "待機",
    "立ち止まる": "待機",
    # 会話
    "話す": "会話",
    "話しかける": "会話",
    "会話する": "会話",
    "声をかける": "会話",
    "挨拶": "会話",
    "返事": "会話",
    "尋ねる": "会話",
    "相談": "会話",
    # 退去
    "立ち去る": "退去",
    "離れる": "退去",
    "その場を離れる": "退去",
    "抜ける": "退去",
    # 通報
    "通報する": "通報",
    "110番": "通報",
    "119番": "通報",
    "救急": "通報",
    "駅員を呼ぶ": "通報",
    "知らせる": "通報",
    # 手伝い
    "助ける": "手伝い",
    "手伝う": "手伝い",
    "手を貸す": "手伝い",
    "介抱": "手伝い",
    "支える": "手伝い",
    # 断る
    "断わる": "断る",
    "ことわる": "断る",
    "辞退": "断る",
    "お断り": "断る",
    "拒否": "断る",
    # 休憩
    "休む": "休憩",
    "休憩する": "休憩",
    "座る": "休憩",
    "一息つく": "休憩",
    # 就寝
    "寝る": "就寝",
    "眠る": "就寝",
    "就寝する": "就寝",
    "横になる": "就寝",
    # 役割語(§2.2)
    "レジを打つ": "接客",
    "対応する": "接客",
    "品出し": "補充",
    "棚に並べる": "補充",
    "開店": "開閉店",
    "閉店": "開閉店",
    "値上げ": "価格改定",
    "値下げ": "価格改定",
    "アナウンス": "放送",
    "並ぶ列に加わる": "並ぶ",
    "写真を撮る": "撮影",
    "撮る": "撮影",
}

#: C6 で足した段0 の写像(**expedient**・実スモークの語彙外行動語)。
#: 方針: **移動を伴う探索 → 移動**(対象はエンジンが決める=ヒントは付けない) /
#: **その場の観察・確認 → 待機**(既存の「様子を見る→待機」と同じ扱い・失敗しない行)。
SYNONYMS_C6: Final[Mapping[str, str]] = {
    # 探索(locomotion を伴う)→ 移動
    "探す": "移動",
    "探し": "移動",  # 探して/探した/探しに行く(部分一致の受け皿)
    "探索": "移動",
    "探る": "移動",
    "見回る": "移動",
    "歩き回る": "移動",
    "うろつく": "移動",
    "散策": "移動",
    # 通勤・通学(目的地つきの locomotion)→ 移動。**対象(職場/学校セル)はエンジンの仕事**
    # なので ``TARGET_HINTS`` は足さない(``home`` に相当する印は未定義=親判断待ち)。
    "通勤": "移動",
    "通学": "移動",
    "出勤": "移動",
    "退勤": "移動",
    "出社": "移動",
    "登校": "移動",
    "進入": "移動",  # ``退去`` は §2.1 の語彙なので辞書に要らない(対になる語だけ足す)
    # 観察・確認(その場に留まる)→ 待機
    "観察": "待機",
    "眺める": "待機",
    "見物": "待機",
    "見学": "待機",
    "確認": "待機",
    "調べる": "待機",
    "調べ": "待機",  # 調べて/調べた
    "調査": "待機",
    "チェック": "待機",
}

#: 段0 辞書写像の全体(``_SYNONYMS_V0`` ∪ ``SYNONYMS_C6``)。
SYNONYMS: Final[Mapping[str, str]] = {**_SYNONYMS_V0, **SYNONYMS_C6}

# ----------------------------------------------------------- 段0 辞書 v3(語彙 v2 用・D-71)
#
# 正典: ``docs/design/v2-synonym-policy-v0.md`` §4-2「★の行(意味の損失)は段2 の裁定と
# AB7-c(辞書改訂腕)の起草材料。順序は **食事**(食べる・飲む・未定義「食事」)→ …」+
# ``docs/design/v2-vocab-growth-design.md`` §3 **E**(オブジェクトの affordance)・
# **F**(版を上げて次ランから)。ユーザー決定 2026-09-17。
#
# **v1 の表(``SYNONYMS``)も版(``SYNONYM_TABLE_VERSION``)も 1 行も動かさない**
# ——語彙政策 v0 §4-1 の 3 点セット(分類と根拠を書く / 版を上げる / manifest に載せる)は
# **新しい版 v3** の側で満たす。``vocab_version="v1"`` のランは辞書も版も現状のまま。
#
# 差分の中身(すべて「食事」へ):
#   - ``食べる`` / ``飲む``: v1 では **購入** へ写していた★「意味の損失」行(摂食≠購買・
#     AB7 open seed 1 で 食べる 12,594 行=34.2%・飲む 44 行)。**写像先の付け替え**。
#   - ``食事`` 系の表層: v2 では ``食事`` が契約語なのでパーサが直接取る。辞書に残すのは
#     **助詞・活用つきの表層**(``食事する`` など)の受け皿。
#   - ``飲食``: AB7 の未定義台帳に実測(14 体)。第205 の裁定バッチで 食事 に併合。
#     (ランチ/昼食/夕食/朝食 は実測に無い自前行だったので第205 で外した=行の追加は観測から。
#     方法論「自己修正ループ」原則 1・語彙政策 v0 §4-1。)
#
# ``飲む`` を 食事 に写すと「飲酒」も食事に畳まれる(条例=公共の場所での飲酒禁止の観測点が
# 摂食に紛れる)。**分類は「意味の損失(縮小)」**として親へ報告済み・第2陣の再訪対象。

#: 語彙 v2 用の段0 辞書の**差分**(v1 の表にこれを重ねたものが v3)。
SYNONYMS_V3_DIFF: Final[Mapping[str, str]] = {
    # v1 で 購入 へ写していた★行の付け替え(語彙政策 v0 §2)
    "食べる": "食事",
    "飲む": "食事",
    # 活用・助詞つきの表層(部分一致の受け皿)
    "食事する": "食事",
    "食事を": "食事",
    # 実測にあった同族語(AB7 台帳「飲食」14 体・第205 の裁定バッチで 食事 に併合)
    "飲食": "食事",
    # ランチ/昼食/夕食/朝食 は実測に無い自前行だったので第205(親)で外した=行の追加は観測から(方法論「自己修正ループ」原則 1)
}

#: 段0 辞書 v3(= ``SYNONYMS`` に ``SYNONYMS_V3_DIFF`` を重ねたもの)。**語彙 v2 専用**。
SYNONYMS_V3: Final[Mapping[str, str]] = {**SYNONYMS, **SYNONYMS_V3_DIFF}

#: 辞書 v3 の版(語彙政策 v0 §4-1 (ii)「行の追加・変更は版を上げる」)。
SYNONYM_TABLE_VERSION_V3: Final[str] = "undefined-synonyms-v3"

#: 語彙版 → 段0 辞書の版(manifest に載る値)。**v1 は現行のまま**。
SYNONYM_TABLE_VERSION_BY_VOCAB: Final[Mapping[str, str]] = {
    "v1": SYNONYM_TABLE_VERSION,
    "v2": SYNONYM_TABLE_VERSION_V3,
}

#: 語彙版 → 段0 辞書の実体。
_SYNONYMS_BY_VOCAB: Final[Mapping[str, Mapping[str, str]]] = {
    "v1": SYNONYMS,
    "v2": SYNONYMS_V3,
}


def synonym_table(vocab_version: str = DEFAULT_VOCAB_VERSION) -> Mapping[str, str]:
    """語彙版 → 段0 辞書(``"v1"`` は ``SYNONYMS`` と**同一オブジェクト**)。"""
    return _SYNONYMS_BY_VOCAB[check_vocab_version(vocab_version)]


def synonym_table_version(vocab_version: str = DEFAULT_VOCAB_VERSION) -> str:
    """語彙版 → 段0 辞書の版文字列(run manifest の欄)。"""
    return SYNONYM_TABLE_VERSION_BY_VOCAB[check_vocab_version(vocab_version)]

#: 語に付随する対象のヒント(**対象の決定はエンジンの仕事**・ここでは印だけ付ける)。
TARGET_HINTS: Final[Mapping[str, str]] = {
    "帰る": "home",
    "帰宅": "home",
    "戻る": "home",
}

#: 失敗フィードバックで提示する「いま可能な行動」3語(行動契約書 §6・安全弁=待機を先頭)。
FALLBACK_ACTIONS: Final[tuple[str, str, str]] = ("待機", "休憩", "移動")

#: 段1 の失敗フィードバック文面(**文面凍結**)。
_FEEDBACK_TEMPLATE: Final[str] = "未定義の行動『{word}』。いま可能な行動: {actions}"

#: 段2 裁定プロンプト(**文面凍結**・T2 モデルへ1呼)。
ADJUDICATION_TEMPLATE: Final[str] = (
    "あなたは世界規則の裁定者です。以下の未定義行動について、行動契約表の1行だけを日本語で書いてください。\n"
    "行動語: {word}\n"
    "観測された回数: {count}(異なる個体 {agents} 体)\n"
    "既存の語彙: {vocab}\n"
    "出力は次の5行に限ります(各行1文・余計な説明は書かない)。\n"
    "前提: <エンジンが検査できる条件>\n"
    "効果: <世界状態のどの欄がどう変わるか>\n"
    "コスト: <時間・金銭・呼のいずれか>\n"
    "失敗: <失敗の意味論>\n"
    "台帳照合: <どの現実パターン照合に使うか1行>\n"
)

#: 段3「保存則・性能予算に触れる行」を検出する語(expedient)。
REVIEW_KEYWORDS: Final[tuple[str, ...]] = (
    "保存則",
    "在庫",
    "所持金",
    "性能",
    "予算",
    "売上",
    "faucet",
    "sink",
)

#: 段2 の閾値 N(契約書「初期10体」・較正パラメータ)。
DEFAULT_THRESHOLD_AGENTS: Final[int] = 10


class ProposalStatus(Enum):
    """裁定行の状態(段2→段3→段4)。"""

    PROPOSED = "PROPOSED"
    NEEDS_PARENT_REVIEW = "NEEDS_PARENT_REVIEW"
    ADOPTED = "ADOPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class UndefinedActionRecord:
    """段1 の未定義行動レコード。"""

    raw_word: str
    agent_id: int
    tick: int
    context_hash: str = ""


@dataclass
class Proposal:
    """段2 が作った契約行の候補(段3 で状態が決まる)。"""

    word: str
    text: str
    status: ProposalStatus
    tick: int
    n_agents: int
    n_occurrences: int
    keywords_hit: tuple[str, ...] = ()
    spec: ActionSpec | None = None
    prompt: str = ""

    @property
    def needs_parent_review(self) -> bool:
        return self.status is ProposalStatus.NEEDS_PARENT_REVIEW


@dataclass(frozen=True)
class UndefinedOutcome:
    """``observe`` の返り値。

    Attributes:
        stage: 0=辞書写像 / 1=記録+フィードバック / 2=裁定要求を出した / 4=判例参照。
        word: 写った契約語彙(段0/段4)。写らなければ None。
        action_code: ``word`` のコード(写らなければ ``UNDEFINED_ACTION``)。
        feedback: 段1 の失敗フィードバック文面(段0/段4 では空)。
        target_hint: 対象のヒント(``home`` 等・エンジンが解決する)。
        proposal: 段2 で作られた候補(出していなければ None)。
        source: ``dictionary`` / ``precedent`` / ``record``。
    """

    stage: int
    word: str | None
    action_code: int
    feedback: str = ""
    target_hint: str = ""
    proposal: Proposal | None = None
    source: str = ""

    @property
    def mapped(self) -> bool:
        return self.word is not None

    @property
    def action_from_dictionary(self) -> bool:
        """段0 の**辞書写像**で契約語彙が入ったか(段4 の判例参照は含めない・C6 診断名)。"""
        return self.stage == 0 and self.source == "dictionary" and self.word is not None


def undefined_feedback(word: str, actions: Sequence[str] = FALLBACK_ACTIONS) -> str:
    """段1 の失敗フィードバック文面(**文面凍結**)。"""
    return _FEEDBACK_TEMPLATE.format(word=word, actions="/".join(actions))


def map_synonym(
    raw_word: str,
    extra: Mapping[str, str] | None = None,
    vocab_version: str = DEFAULT_VOCAB_VERSION,
) -> tuple[str | None, str]:
    """段0 辞書写像。完全一致 → 最長部分一致の順に引く。**ゼロ呼**。

    Args:
        raw_word: 行動欄の逐語。
        extra: 追加表(段4 の判例)。
        vocab_version: 語彙版(``"v1"``=既定・``SYNONYMS`` / ``"v2"``=``SYNONYMS_V3``)。
            **既定では 1 行も変わらない**(同じ表・同じ写像先)。

    Returns:
        ``(契約語彙 or None, target_hint)``。

    逐次ループ宣言(P4): 表の語数ぶん(数十)。

    Example:
        >>> map_synonym("食べる")[0]
        '購入'
        >>> map_synonym("食べる", vocab_version="v2")[0]
        '食事'
    """
    if not raw_word:
        return None, ""
    text = raw_word.strip()
    tables: tuple[Mapping[str, str], ...] = (
        (extra or {}), synonym_table(vocab_version),
    )
    for table in tables:
        hit = table.get(text)
        if hit is not None:
            return hit, TARGET_HINTS.get(text, "")
    # 部分一致(最長優先)
    best: tuple[int, str, str] | None = None
    for table in tables:
        for surface, canonical in table.items():
            if surface and surface in text:
                cand = (-len(surface), surface, canonical)
                if best is None or cand < best:
                    best = cand
    if best is None:
        return None, ""
    return best[2], TARGET_HINTS.get(best[1], "")


class UndefinedActionRegistry:
    """未定義行動の5段(§7)を回す台帳。**エンジン状態には触れない**。

    Args:
        threshold_agents: 段2 を起こす「異なる個体数」の閾値 N(既定 10=契約書の初期値)。
        log_limit: 段1 レコードの保持上限(有界化・D-R2-6)。
        adjudicator: 段2 で1呼する ``llm.LLMClient``(None なら段2 に進まない)。
        params: 裁定呼のデコード設定(``LLMRequest.params``)。
        vocab_version: 語彙版(D-71 §3 F)。``"v2"`` で段0 辞書が v3 になり、
            行動コードの解決に「食事」が入る。**既定 ``"v1"`` は現行と 1 バイトも変わらない**。

    Example:
        >>> reg = UndefinedActionRegistry()
        >>> reg.observe("歩く", agent_id=1, tick=0).word
        '移動'
    """

    def __init__(
        self,
        *,
        threshold_agents: int = DEFAULT_THRESHOLD_AGENTS,
        log_limit: int = 4_096,
        adjudicator: Any | None = None,
        params: Mapping[str, Any] | None = None,
        review_keywords: Iterable[str] = REVIEW_KEYWORDS,
        vocab_version: str = DEFAULT_VOCAB_VERSION,
    ) -> None:
        if threshold_agents < 1:
            raise ValueError("threshold_agents は 1 以上")
        self.vocab_version = check_vocab_version(vocab_version)
        self.threshold_agents = int(threshold_agents)
        self.log_limit = int(log_limit)
        self.adjudicator = adjudicator
        self.params: Mapping[str, Any] = dict(params or {"temperature": 0.0, "max_tokens": 256})
        self.review_keywords = tuple(review_keywords)
        self.log: deque[UndefinedActionRecord] = deque(maxlen=self.log_limit)
        self.counts: Counter[str] = Counter()
        self.proposals: dict[str, Proposal] = {}
        #: 段4 の判例(語 → 契約語彙)。2回目以降は**LLMを呼ばない**。
        self.precedents: dict[str, str] = {}
        #: 段4 で採用された契約行(語 → ``ActionSpec``)。
        self.vocabulary_extension: dict[str, ActionSpec] = {}
        self._agents: dict[str, set[int]] = {}
        self.n_dropped_records = 0
        self.n_adjudication_calls = 0
        #: 段0 の辞書写像で救えた件数(C6 診断・``counters()["dictionary_mapped"]``)。
        self.n_dictionary_mapped = 0

    # ---------------------------------------------------------------- 観測
    def observe(
        self, raw_word: str, agent_id: int, tick: int, context_hash: str = ""
    ) -> UndefinedOutcome:
        """未定義行動を1件受ける(段4→段0→段1→段2→段3 の順で判定)。"""
        word = (raw_word or "").strip()
        ver = self.vocab_version
        if not word:
            return UndefinedOutcome(
                stage=1, word=None, action_code=action_code_of("", ver),
                feedback=undefined_feedback(""), source="record",
            )

        # 段4: 判例(採用済みの語)は決定論参照=呼ゼロ
        if word in self.precedents:
            mapped = self.precedents[word]
            return UndefinedOutcome(
                stage=4, word=mapped, action_code=action_code_of(mapped, ver), source="precedent"
            )
        if word in self.vocabulary_extension:
            return UndefinedOutcome(
                stage=4, word=word, action_code=action_code_of(word, ver), source="precedent"
            )

        # 段0: 辞書写像(ゼロ呼)
        mapped, hint = map_synonym(word, self.precedents, ver)
        if mapped is not None:
            self.n_dictionary_mapped += 1
            return UndefinedOutcome(
                stage=0, word=mapped, action_code=action_code_of(mapped, ver),
                target_hint=hint, source="dictionary",
            )

        # 段1: 記録+計数+失敗フィードバック
        if len(self.log) == self.log.maxlen:
            self.n_dropped_records += 1
        self.log.append(UndefinedActionRecord(word, int(agent_id), int(tick), context_hash))
        self.counts[word] += 1
        self._agents.setdefault(word, set()).add(int(agent_id))
        feedback = undefined_feedback(word)

        # 段2/段3: 閾値到達で裁定を1呼
        proposal = self._maybe_adjudicate(word, tick)
        stage = 2 if proposal is not None else 1
        return UndefinedOutcome(
            stage=stage, word=None, action_code=action_code_of(word, ver),
            feedback=feedback, proposal=proposal, source="record",
        )

    def distinct_agents(self, word: str) -> int:
        """その語を出した**異なる個体数**(段2 の閾値の分子)。"""
        return len(self._agents.get(word, ()))

    # ---------------------------------------------------------------- 段2/段3
    def _maybe_adjudicate(self, word: str, tick: int) -> Proposal | None:
        if word in self.proposals or self.adjudicator is None:
            return None
        if self.distinct_agents(word) < self.threshold_agents:
            return None
        return self.adjudicate(word, tick)

    def adjudicate(self, word: str, tick: int) -> Proposal | None:
        """段2: 裁定LLMに**1呼**で契約行を書かせ、段3 の判定まで済ませる。"""
        if self.adjudicator is None:
            return None
        from shibuya.llm import LLMRequest  # 遅延 import(``__init__`` の定義順による循環回避)

        prompt = ADJUDICATION_TEMPLATE.format(
            word=word,
            count=int(self.counts[word]),
            agents=self.distinct_agents(word),
            vocab="/".join(action_words(self.vocab_version)),
        )
        request = LLMRequest(
            agent_id=0,  # 裁定は個体に紐づかない(テープ鍵は tick と語で決まる)
            tick=int(tick),
            wake_class=0,
            prompt=prompt,
            params=self.params,
            call_id=f"adjudicate:{word}:{tick}",
        )
        response = self.adjudicator.complete(request)
        self.n_adjudication_calls += 1
        text = getattr(response, "text", str(response))
        hits = tuple(k for k in self.review_keywords if k in text)
        proposal = Proposal(
            word=word,
            text=text,
            status=(
                ProposalStatus.NEEDS_PARENT_REVIEW if hits else ProposalStatus.PROPOSED
            ),
            tick=int(tick),
            n_agents=self.distinct_agents(word),
            n_occurrences=int(self.counts[word]),
            keywords_hit=hits,
            prompt=prompt,
        )
        self.proposals[word] = proposal
        return proposal

    # ---------------------------------------------------------------- 段4
    def adopt(self, word: str, spec: ActionSpec) -> Proposal:
        """段4: **親の行為**として語彙を拡張し、判例を記録する(以後は呼ゼロで写る)。

        Args:
            word: 未定義だった語。
            spec: 採用する契約行(``ActionSpec``)。``spec.word`` が既存語なら**別名**として、
                新語なら**語彙拡張**として登録する。

        Returns:
            更新後の ``Proposal``(段2 を経ていなければその場で作る)。
        """
        if not isinstance(spec, ActionSpec):
            raise TypeError("spec は ActionSpec")
        proposal = self.proposals.get(word)
        if proposal is None:
            proposal = Proposal(
                word=word,
                text="",
                status=ProposalStatus.PROPOSED,
                tick=-1,
                n_agents=self.distinct_agents(word),
                n_occurrences=int(self.counts[word]),
            )
            self.proposals[word] = proposal
        if proposal.status is ProposalStatus.NEEDS_PARENT_REVIEW:
            # 親が明示的に adopt を呼ぶこと自体が「親検収」。段3 の門はここで開く。
            pass
        proposal.spec = spec
        proposal.status = ProposalStatus.ADOPTED
        if spec.word in ACTION_SPECS or spec.word in self.vocabulary_extension:
            self.precedents[word] = spec.word
        else:
            self.vocabulary_extension[spec.word] = spec
            self.precedents[word] = spec.word
        return proposal

    def reject(self, word: str, reason: str = "") -> Proposal | None:
        """親が候補を却下する(語彙には入らない)。"""
        proposal = self.proposals.get(word)
        if proposal is None:
            return None
        proposal.status = ProposalStatus.REJECTED
        proposal.text = (proposal.text + f"\n[却下] {reason}").strip() if reason else proposal.text
        return proposal

    # ---------------------------------------------------------------- 診断
    def counters(self) -> Mapping[str, int]:
        """診断行に載せる計数。"""
        return {
            "undefined_records": int(sum(self.counts.values())),
            "undefined_words": len(self.counts),
            "undefined_dropped": int(self.n_dropped_records),
            "dictionary_mapped": int(self.n_dictionary_mapped),
            "proposals": len(self.proposals),
            "needs_parent_review": sum(
                1 for p in self.proposals.values() if p.needs_parent_review
            ),
            "adopted": sum(
                1 for p in self.proposals.values() if p.status is ProposalStatus.ADOPTED
            ),
            "adjudication_calls": int(self.n_adjudication_calls),
        }

    def top_words(self, k: int = 10) -> list[tuple[str, int]]:
        """出現上位の未定義語(診断・親の検収用)。"""
        return self.counts.most_common(k)
