"""llm.contract — 行動契約書(R4・v1)の**唯一の正典置き場**(語彙・契約表・対象の型)。

これまで行動語彙は ``shibuya.llm.__init__`` に置かれ、``__init__`` 自身が
「パーサ実装時に**正典の置き場所を1つに決める**必要がある」と宣言していた。本モジュールが
その1つ。``shibuya.llm.__init__`` と ``shibuya.engine.commit`` は**ここを import する**。

正典(逐語の出典)
- 行動契約書 §1 出力形: 1行目「理由: <40字以内・1文>」/ 2行目
  「行動: <語彙1語> **対象: <セルID|物カテゴリ|人ID|なし>** ひと言: <20字以内|なし>」。
- 行動契約書 §2 冒頭: 「**語彙は全種別共通(案B)・権限はエンジンが検査**(prefix完全共有・
  『権限なき者の試行』を逸脱の創発として観測=U18入口)。種別あたりの語彙上限24語」。
- 行動契約書 §2.1 種別横断12語の表(対象/前提条件/効果/コスト/失敗の意味論/タグ)。
- 行動契約書 §2.2 種別固有(権限保持者/前提条件/効果/失敗の意味論/タグ)。
- 知覚契約書 §2.5: 「厳密JSONは課さず、パーサは**ラベル基準の寛容行指向**」。

層契約: 本モジュールは ``shibuya.core`` 以外の shibuya パッケージを import しない
(import-linter 契約「llm は world/agents/perception/engine/economy/census を import しない」)。
``ResultCode`` は ``shibuya.agents.state`` にあるため**名前の文字列**で持つ
(``tests/engine/test_parser_contract.py`` が実在を機械検査する)。

逐次ループ宣言(P4): なし(表の宣言と正規表現だけ。``ACTION_SPECS`` の構築は
インポート時1回・語数(24)ぶんのループで、個体数にも tick 数にも比例しない)。

expedient(本モジュール分)
- §2.2 の表には **「対象」列が無い**。役割語の ``target_kind`` は前提/効果の文面から親が
  推定した値であり、``target_declared=False`` で区別する(§2.1 の12語は表に対象列がある
  =``target_declared=True``)。
- ``preconditions`` の**名前**(``route_exists`` 等)は契約書の日本語文から起こした識別子。
  文面そのものは ``precondition_text`` に逐語で残す(検査の実体は engine 側)。
- 「発車/停車」「並ぶ/撮影」は表では**1行**だが、行動語としては別語なので**2行に割った**
  (同じ文面を共有し ``table_row`` に元の行名を残す)。
- 対象の表層形(``C-0117`` / ``g12_34_GL`` / ``P-204`` / 整数)の**認識規則**は自前。
  ``g<ix>_<iy>_<band>`` は W2 ``w2_cells.parquet`` の ``place_id`` 実体から起こした
  (band ∈ {GL, UG, DECK}・ix/iy は負値あり)。
- ``手伝い`` の失敗「能力不足」= ``ResultCode.INSUFFICIENT_ABILITY``(C3 出口で親が追加)。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Final, Mapping

__all__ = [
    "REASON_MAX_CHARS",
    "COMMENT_MAX_CHARS",
    "VOCAB_LIMIT_PER_KIND",
    "NO_TARGET",
    "ACTION_VOCAB_12",
    "ROLE_ACTION_WORDS",
    "ACTION_VOCAB_ROLE",
    "ALL_ACTION_WORDS",
    "ROLE_ACTIONS",
    "ACTION_CODES",
    "ROLE_ACTION_CODES",
    "UNDEFINED_ACTION",
    "TargetKind",
    "Target",
    "NO_TARGET_VALUE",
    "ActionSpec",
    "ACTION_SPECS",
    "TWO_LINE_RE",
    "format_two_line",
    "parse_target",
    "LANDMARK_MIN_CHARS",
    "resolve_landmark",
    "action_code_of",
    "spec_of",
    "is_role_action",
    # ---- 語彙成長 v2(D-71 §3 E/F/H・2026-09-17 ユーザー決定)。既定 v1 は 1 バイトも動かない ----
    "VOCAB_VERSIONS",
    "DEFAULT_VOCAB_VERSION",
    "ACTION_WORD_EAT",
    "EAT_ACTION_CODE",
    "ACTION_VOCAB_13",
    "ALL_ACTION_WORDS_V2",
    "ACTION_SPECS_V2",
    "VOCAB_COMPAT",
    "check_vocab_version",
    "action_words",
    "cross_action_words",
    "engine_action_codes",
    "compat_word",
    # ---- 語彙 v3(行為と活動の二層・D-116・第274 アジェンダ §1)。v1/v2 は 1 バイトも動かさない ----
    "ACTION_WORD_NONE",
    "NONE_ACTION_CODE",
    "ACTION_WORD_QUEUE",
    "REMOVED_ACTION_WORDS_V3",
    "ACTION_VOCAB_V3",
    "ROLE_ACTION_WORDS_V3",
    "ALL_ACTION_WORDS_V3",
    "ACTION_SPECS_V3",
    "ACTION_CODES_V3",
    "ROLE_ACTION_CODES_V3",
    "SAFE_ACTION_BY_VERSION",
    "safe_action_word",
    "role_action_words",
    "ACTIVITY_MAX_CHARS",
    "UNTIL_DEFAULT_MINUTES",
    "UNTIL_MAX_MINUTES",
    "UntilKind",
    "Until",
    "DEFAULT_UNTIL",
    "parse_until",
    "TWO_LINE_RE_V3",
    "format_two_line_v3",
    "TARGET_WANDER",
    "TARGET_BASE_WORDS_V3",
    "TARGET_PLACEHOLDERS_V3",
]

#: 行動契約書 §1「理由: <40字以内・1文>」。
REASON_MAX_CHARS: Final[int] = 40
#: 行動契約書 §1「ひと言: <20字以内|なし>」。
COMMENT_MAX_CHARS: Final[int] = 20
#: 行動契約書 §2「種別あたりの語彙上限24語(到達時は最も使われない語を封印)」。
VOCAB_LIMIT_PER_KIND: Final[int] = 24
#: 「対象」が無いときの語(行動契約書 §1)。
NO_TARGET: Final[str] = "なし"

#: パーサが行動語を取れなかったときのコード(行動契約書 §7 段1「未定義行動レコード」)。
#: ``engine.commit.UNDEFINED_ACTION`` はこの値を import する(値の二重定義を作らない)。
UNDEFINED_ACTION: Final[int] = -2


class TargetKind(IntEnum):
    """「対象」欄の型(行動契約書 §1 の ``<セルID|物カテゴリ|人ID|なし>`` の一般化)。

    Note:
        **C9b(2026-09-17・G6 a′)で型は増やしていない**。目印(landmark/attraction の POI)は
        ``ITEM_CATEGORY``(=表の「物カテゴリ**(+店ID)**」枠)のまま ``Target.poi_id`` に
        POI 索引を入れて返す。型を増やすと ``last_action``/テープ/``_target_person`` など
        「型で分岐している箇所」を全部見直すことになり、**既存の型で表せるものに新しい型を
        足さない**(決定台帳 :460 の原則「表せるなら世界データを足し、語/型は足さない」)。
    """

    NONE = 0  # なし
    CELL = 1  # セルID
    ITEM_CATEGORY = 2  # 物カテゴリ(+店ID / **目印 POI**)
    PERSON = 3  # 人ID
    STATION_OR_VEHICLE = 4  # 駅/車両ID
    EVENT = 5  # 事象ID


@dataclass(frozen=True)
class ActionSpec:
    """行動契約表の**1行**(§2.1 の12語 / §2.2 の役割語)。

    Attributes:
        word: 行動語。
        target_kind: 「対象」欄の主たる型。
        alt_target_kinds: 併記されている別の型(例: 通報=人/事象ID)。
        target_declared: 表に「対象」列があるか(§2.1=True・§2.2=False は親の推定)。
        preconditions: エンジン検査の**名前**(識別子)。
        precondition_text: 契約書の前提条件の**逐語**。
        effects: 効果の逐語。
        cost: コストの逐語(§2.2 の表にはコスト列が無く空文字)。
        failure_text: 「失敗の意味論」の**逐語**(日本語のまま凍結)。
        failure_codes: ``agents.state.ResultCode`` の**名前**(層契約のため文字列)。
        never_fails: 契約書が「**失敗しない**」と明記した行。
        tag: ``mechanism`` / ``expedient``。
        permission_holder: §2.2 の権限保持者(§2.1 は空)。
        section: 出典の節(``2.1`` / ``2.2``)。
        table_row: 表の行名(「発車/停車」のように1行を2語へ割った場合の元の行)。
    """

    word: str
    target_kind: TargetKind
    preconditions: tuple[str, ...]
    precondition_text: str
    effects: str
    cost: str
    failure_text: str
    failure_codes: tuple[str, ...]
    tag: str
    section: str
    alt_target_kinds: tuple[TargetKind, ...] = ()
    target_declared: bool = True
    never_fails: bool = False
    permission_holder: str = ""
    table_row: str = ""

    def __post_init__(self) -> None:
        if self.tag not in ("mechanism", "expedient"):
            raise ValueError(f"tag は mechanism|expedient: {self.tag!r}")
        if self.never_fails and self.failure_codes:
            raise ValueError(f"{self.word}: 「失敗しない」行に failure_codes がある")

    @property
    def is_role(self) -> bool:
        """§2.2(権限保持者つき)の語か。"""
        return self.section == "2.2"


# ------------------------------------------------------------------ §2.1 種別横断12語
_SPECS_12: Final[tuple[ActionSpec, ...]] = (
    ActionSpec(
        word="移動",
        target_kind=TargetKind.CELL,
        preconditions=("route_exists", "same_band_connected", "current_action_interruptible"),
        precondition_text="経路が存在・同層で連結・現行動が中断可",
        effects="位置=経路上へ(到着時刻はエンジン)",
        cost="時間・体力",
        failure_text="到達不能/途中打ち切り(混雑・閉鎖)",
        failure_codes=("UNREACHABLE", "INTERRUPTED"),
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="乗車",
        target_kind=TargetKind.STATION_OR_VEHICLE,
        preconditions=("vehicle_stopped_in_cell", "fare_affordable", "capacity_available"),
        precondition_text="同一セルに停車中・運賃≦残高orIC・定員に空き",
        effects="位置=車両・運賃決済",
        cost="運賃・時間",
        failure_text="満員/運賃不足/列車なし",
        failure_codes=("TRAIN_FULL", "FARE_SHORT", "NO_TRAIN"),
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="降車",
        target_kind=TargetKind.CELL,
        preconditions=("is_riding", "vehicle_stops_here"),
        precondition_text="乗車中・当該駅に停車",
        effects="位置=駅セル",
        cost="0",
        failure_text="その駅には止まらない",
        failure_codes=("NO_STOP",),
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="購入",
        target_kind=TargetKind.ITEM_CATEGORY,
        preconditions=("shop_open", "stock_positive", "money_ge_price"),
        precondition_text="営業中・在庫>0・所持金≧価格",
        effects="在庫−1・所持金−価格・所持+1・店の売上+同額(保存則)",
        cost="価格・待ち時間",
        failure_text="所持金不足(残高/価格を返す)/在庫切れ/営業時間外(次回開店時刻を返す)",
        failure_codes=("MONEY_SHORT", "OUT_OF_STOCK", "CLOSED"),
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="待機",
        target_kind=TargetKind.NONE,
        preconditions=(),
        precondition_text="なし(常に可能=安全弁)",
        effects="時間経過",
        cost="時間",
        failure_text="失敗しない",
        failure_codes=(),
        never_fails=True,
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="会話",
        target_kind=TargetKind.PERSON,
        preconditions=(
            "same_cell",
            "within_d_talk",
            "partner_idle",
            "no_refusal_history",
            "call_budget_both",
        ),
        precondition_text="同一セル・距離≦d_talk(≈1m)・相手idle・拒否履歴なし・双方に会話呼予算",
        effects="会話セッション生成(§3)",
        cost="呼",
        failure_text="相手が会話中/断られた/去った",
        failure_codes=("PARTNER_BUSY", "REFUSED", "PARTNER_GONE"),
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="退去",
        target_kind=TargetKind.NONE,
        preconditions=("belongs_to_group_or_queue_or_facility",),
        precondition_text="会話/待ち行列/施設に所属中",
        effects="所属解除(会話はCLOSING経由)",
        cost="0-短時間",
        failure_text="失敗しない",
        failure_codes=(),
        never_fails=True,
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="通報",
        target_kind=TargetKind.EVENT,
        alt_target_kinds=(TargetKind.PERSON,),
        preconditions=("report_target_exists", "event_perceived"),
        precondition_text="通報先が存在・当該事象を知覚済み",
        effects="事象レコードに通報1件→検知確率へ(行12)",
        cost="時間",
        failure_text="対象特定不能/届かない",
        failure_codes=("BAD_TARGET", "UNREACHABLE"),
        tag="expedient",
        section="2.1",
    ),
    ActionSpec(
        word="手伝い",
        target_kind=TargetKind.PERSON,
        preconditions=("partner_requesting_help", "same_cell"),
        precondition_text="相手が援助要求状態・同一セル",
        effects="相手のタスク進捗+・関係辺強度+Δ",
        cost="時間",
        failure_text="相手が要求していない/能力不足",
        failure_codes=("BAD_TARGET", "INSUFFICIENT_ABILITY"),
        tag="expedient",
        section="2.1",
    ),
    ActionSpec(
        word="断る",
        target_kind=TargetKind.PERSON,
        alt_target_kinds=(TargetKind.EVENT,),
        preconditions=("pending_request_exists",),
        precondition_text="保留中の要求が存在",
        effects="要求却下・関係辺強度−Δ",
        cost="0",
        failure_text="失敗しない",
        failure_codes=(),
        never_fails=True,
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="休憩",
        target_kind=TargetKind.NONE,
        preconditions=(),
        precondition_text="なし",
        effects="内受容3変数の回復",
        cost="時間",
        failure_text="失敗しない",
        failure_codes=(),
        never_fails=True,
        tag="mechanism",
        section="2.1",
    ),
    ActionSpec(
        word="就寝",
        target_kind=TargetKind.CELL,
        preconditions=("cell_is_sleepable",),
        precondition_text="当該セルが就寝可(自宅/宿)",
        effects="睡眠状態へ→T2日次内省を発火(知覚契約書§6)",
        cost="時間",
        failure_text="寝る場所がない(路上就寝はU18)",
        failure_codes=("NO_BED",),
        tag="mechanism",
        section="2.1",
    ),
)

# ------------------------------------------------------------------ §2.2 種別固有(権限検査)
_SPECS_ROLE: Final[tuple[ActionSpec, ...]] = (
    ActionSpec(
        word="接客",
        target_kind=TargetKind.PERSON,
        target_declared=False,
        preconditions=("same_shop", "queue_positive"),
        precondition_text="同一店舗・待ち行列>0",
        effects="待ち行列−1・購入成立を可能に",
        cost="",
        failure_text="客がいない",
        failure_codes=("BAD_TARGET",),
        tag="mechanism",
        section="2.2",
        permission_holder="従業者",
    ),
    ActionSpec(
        word="補充",
        target_kind=TargetKind.ITEM_CATEGORY,
        target_declared=False,
        preconditions=("backroom_stock_positive", "shop_open"),
        precondition_text="在庫置場>0・営業中",
        effects="棚在庫+(棚が減る=補充行動のドクトリン)",
        cost="",
        failure_text="バックヤードに在庫なし",
        failure_codes=("OUT_OF_STOCK",),
        tag="mechanism",
        section="2.2",
        permission_holder="従業者",
    ),
    ActionSpec(
        word="開閉店",
        target_kind=TargetKind.NONE,
        target_declared=False,
        preconditions=("has_management_permission",),
        precondition_text="管理権限",
        effects="PlanSpec(営業時間)の実績確定",
        cost="",
        failure_text="権限なし",
        failure_codes=("NO_PERMISSION",),
        tag="mechanism",
        section="2.2",
        permission_holder="従業者(権限)",
    ),
    ActionSpec(
        word="価格改定",
        target_kind=TargetKind.ITEM_CATEGORY,
        target_declared=False,
        preconditions=("is_price_reviser",),
        precondition_text="改訂権者",
        effects="revises(Agent, PlanSpec[価格表])(行5の決定に従う)",
        cost="",
        failure_text="権限なし(=創発の観測点)",
        failure_codes=("NO_PERMISSION",),
        tag="mechanism",
        section="2.2",
        permission_holder="従業者(権限)/本部",
    ),
    ActionSpec(
        word="発車",
        target_kind=TargetKind.STATION_OR_VEHICLE,
        target_declared=False,
        preconditions=("on_duty_on_train", "block_ahead_clear"),
        precondition_text="当該列車に乗務中・前方閉塞",
        effects="列車位置更新・ActualLog追記",
        cost="",
        failure_text="前方閉塞/指令の抑止",
        failure_codes=("INTERRUPTED",),
        tag="mechanism",
        section="2.2",
        permission_holder="乗務員",
        table_row="発車/停車",
    ),
    ActionSpec(
        word="停車",
        target_kind=TargetKind.STATION_OR_VEHICLE,
        target_declared=False,
        preconditions=("on_duty_on_train", "block_ahead_clear"),
        precondition_text="当該列車に乗務中・前方閉塞",
        effects="列車位置更新・ActualLog追記",
        cost="",
        failure_text="前方閉塞/指令の抑止",
        failure_codes=("INTERRUPTED",),
        tag="mechanism",
        section="2.2",
        permission_holder="乗務員",
        table_row="発車/停車",
    ),
    ActionSpec(
        word="放送",
        target_kind=TargetKind.CELL,
        target_declared=False,
        preconditions=("has_broadcast_equipment",),
        precondition_text="放送設備",
        effects="当該セルの聴覚イベント",
        cost="",
        failure_text="設備がない",
        failure_codes=("BAD_TARGET",),
        tag="mechanism",
        section="2.2",
        permission_holder="乗務員/駅員",
    ),
    ActionSpec(
        word="遅延報告",
        target_kind=TargetKind.EVENT,
        target_declared=False,
        preconditions=("delay_exceeds_threshold",),
        precondition_text="実績−計画>閾値",
        effects="ActualLogに逸脱語彙(GTFS-RT式)",
        cost="",
        failure_text="報告先不明",
        failure_codes=("BAD_TARGET",),
        tag="mechanism",
        section="2.2",
        permission_holder="乗務員",
    ),
    ActionSpec(
        word="計画改訂",
        target_kind=TargetKind.EVENT,
        target_declared=False,
        preconditions=("is_plan_reviser",),
        precondition_text="改訂権者",
        effects="revises(指令, PlanSpec[ダイヤ])・公示範囲に従い配送",
        cost="",
        failure_text="権限なし",
        failure_codes=("NO_PERMISSION",),
        tag="mechanism",
        section="2.2",
        permission_holder="指令(権限)",
    ),
    ActionSpec(
        word="指示",
        target_kind=TargetKind.PERSON,
        target_declared=False,
        preconditions=("target_is_own_crew",),
        precondition_text="対象が自社乗務員",
        effects="対象の役割知識に指示レコード",
        cost="",
        failure_text="受信圏外",
        failure_codes=("UNREACHABLE",),
        tag="mechanism",
        section="2.2",
        permission_holder="指令",
    ),
    ActionSpec(
        word="並ぶ",
        target_kind=TargetKind.CELL,
        target_declared=False,
        preconditions=("queue_exists",),
        precondition_text="待ち行列が存在/撮影可",
        effects="待ち行列加入/記憶+SNS投稿候補",
        cost="",
        failure_text="行列がない/撮影禁止",
        failure_codes=("BAD_TARGET",),
        tag="expedient",
        section="2.2",
        permission_holder="全員",
        table_row="並ぶ/撮影",
    ),
    ActionSpec(
        word="撮影",
        target_kind=TargetKind.CELL,
        target_declared=False,
        preconditions=("photography_allowed",),
        precondition_text="待ち行列が存在/撮影可",
        effects="待ち行列加入/記憶+SNS投稿候補",
        cost="",
        failure_text="行列がない/撮影禁止",
        failure_codes=("BAD_TARGET",),
        tag="expedient",
        section="2.2",
        permission_holder="全員",
        table_row="並ぶ/撮影",
    ),
)

#: 行動契約書 §2.1 種別横断12語(表の出現順)。
ACTION_VOCAB_12: Final[tuple[str, ...]] = tuple(s.word for s in _SPECS_12)

#: 行動契約書 §2.2 種別固有(権限はエンジンが検査・語彙自体は全員に見せる)。
ROLE_ACTION_WORDS: Final[tuple[str, ...]] = tuple(s.word for s in _SPECS_ROLE)

#: 旧名(``shibuya.llm`` が再輸出してきた名前)。§2.2 の全12語へ拡張した。
ACTION_VOCAB_ROLE: Final[tuple[str, ...]] = ROLE_ACTION_WORDS

#: 12語 + 役割語(パーサが行動語として受理する全体集合)。
ALL_ACTION_WORDS: Final[tuple[str, ...]] = ACTION_VOCAB_12 + ROLE_ACTION_WORDS

#: 役割語 → 権限保持者(§2.2「権限保持者」列)。
ROLE_ACTIONS: Final[Mapping[str, str]] = {s.word: s.permission_holder for s in _SPECS_ROLE}

#: 行動語 → 契約行。
ACTION_SPECS: Final[Mapping[str, ActionSpec]] = {s.word: s for s in (*_SPECS_12, *_SPECS_ROLE)}

#: 行動語 → コード(**``engine.commit.ACTION_CODES`` と同値**=12語の表の出現順 0..11)。
ACTION_CODES: Final[Mapping[str, int]] = {w: i for i, w in enumerate(ACTION_VOCAB_12)}

#: 役割語 → コード(12..)。**エンジンの ``_APPLY`` には対応分岐が無い**(効果先は C4)。
#: 役割語の intent 化は ``engine.llm_bridge`` が「待機+権限検査待ち」に落とす(expedient)。
ROLE_ACTION_CODES: Final[Mapping[str, int]] = {
    w: len(ACTION_VOCAB_12) + i for i, w in enumerate(ROLE_ACTION_WORDS)
}

assert len(ACTION_VOCAB_12) == 12
assert len(set(ALL_ACTION_WORDS)) == len(ALL_ACTION_WORDS)
assert len(ALL_ACTION_WORDS) <= VOCAB_LIMIT_PER_KIND, "§2 語彙上限24語"


# ================================================================== 語彙版(D-71 §3 E/F/H)
#
# 正典: ``docs/design/v2-vocab-growth-design.md`` §3(ユーザー決定 2026-09-17「A〜K 親推奨
# どおり」)。**E**=動詞を足すのではなく**オブジェクトに affordance を足す**・**F**=版を上げて
# 次ランから有効+旧版への対応表・**H**=採用語は契約表参照(LLM を呼ばない)。
#
# **v1 は 1 バイトも動かさない**: ``ACTION_VOCAB_12`` / ``ROLE_ACTION_WORDS`` /
# ``ALL_ACTION_WORDS`` / ``ACTION_CODES`` / ``ROLE_ACTION_CODES`` / ``ACTION_SPECS`` は
# **同じオブジェクトのまま**で、v2 は別名(``*_V2``)に積む。既定の呼び出し
# (``action_code_of(word)`` 等)は引数を足しても v1 の値を返す。
#
# **コードの割り当て**: 12 語=0..11・役割語=12..23 は動かせない(テープ・checkpoint・
# ``agents.last_action`` の実体)。したがって「食事」は**末尾の 24** を取る
# (= ``len(ALL_ACTION_WORDS)``)。v2 で 12 語の並びに割り込ませることは**しない**。
#
# **上限 24 語との関係(未決・親/ユーザー判断待ち)**: §2 は「種別あたりの語彙上限24語
# (到達時は最も使われない語を封印)」と言う。v2 は 25 語=**上限を 1 語超える**。どの語を
# 封印するかは D-71 §3 **J**(使用率の計測を先に・退役の基準はデータが出てから)の決定待ちで、
# ここでは**封印しない**(勝手に語を落とすのは設計者の指紋になる)。v1 側の assert は上のまま。
#
# expedient(本節分)
# - 「食事」という**語の表層**(社会生活基本調査 20 種・ATUS 一次 17 のどちらにも食事は
#   あるが、日本語の 1 語をこの綴りに決めたのは親)。
# - 前提/効果/失敗の文面と ``NOT_IN_EATERY`` の新設(既存コードに「その店にいない」が無い)。
# - 所要時間 20 分(契約行の宣言値。**専用タイマーは未実装**=在店の解除は既存の回転率
#   ``engine.processes.crowd.DWELL_MAX_TICKS`` に従う。親へ報告済み)。

#: 語彙の版(F: 版はラン単位・ラン中に切り替えない)。**v3**=行為と活動の二層(D-116・第274)。
VOCAB_VERSIONS: Final[tuple[str, ...]] = ("v1", "v2", "v3")
#: 既定の版(= 現行 24 語。既定経路のバイトはこの版で決まる)。
DEFAULT_VOCAB_VERSION: Final[str] = "v1"

#: v2 で足す横断語(E: 飲食店オブジェクトの affordance ``eat`` の語)。
ACTION_WORD_EAT: Final[str] = "食事"
#: 「食事」の行動コード(= 24 = 既存 24 語の**次**。既存コードは 1 つも動かない)。
EAT_ACTION_CODE: Final[int] = len(ALL_ACTION_WORDS)

_SPEC_EAT: Final[ActionSpec] = ActionSpec(
    word=ACTION_WORD_EAT,
    target_kind=TargetKind.ITEM_CATEGORY,  # 購入と同じ「物カテゴリ(+店ID)」の枠
    preconditions=("in_eatery", "shop_open", "money_ge_price"),
    precondition_text="飲食店(cat が飲食帯)のセルに居る・営業中・所持金≧価格",
    effects="所持金−価格・店の売上+同額(保存則)・空腹−・在店(その tick は移動しない)",
    cost="価格・時間(20 分・expedient)",
    failure_text="飲食店にいない/所持金不足(残高・価格を返す)/営業時間外",
    failure_codes=("NOT_IN_EATERY", "MONEY_SHORT", "CLOSED"),
    tag="expedient",
    section="7.4",  # 行動契約書 §7 段4(採用語)。§2.1/§2.2 の表の行ではない
    table_row="D-71 §3 E(飲食店 affordance)",
)

#: v2 の種別横断語(12 語 + 食事)。**``ACTION_VOCAB_12`` は変えない**。
ACTION_VOCAB_13: Final[tuple[str, ...]] = ACTION_VOCAB_12 + (ACTION_WORD_EAT,)

#: v2 でパーサが受理する全体集合(24 語 + 食事 = 25 語)。
ALL_ACTION_WORDS_V2: Final[tuple[str, ...]] = ALL_ACTION_WORDS + (ACTION_WORD_EAT,)

#: v2 の契約表(v1 の 24 行 + 食事)。
ACTION_SPECS_V2: Final[Mapping[str, ActionSpec]] = {**ACTION_SPECS, ACTION_WORD_EAT: _SPEC_EAT}

# ================================================================== 語彙 v3(二層・D-116)
#
# 正典: ``docs/design/v2-two-layer-implementation-agenda.md`` §1-1(第274・ユーザー決定 D-116
# 「A〜I 推奨どおり」の実装形)+ ``docs/design/v2-action-activity-two-layer-draft.md`` §4-3。
# **行為**(世界に触れる行動=契約行つき)と**活動**(世界を変えない過ごし方=自由文+持続)を
# 分け、行為の語彙から **待機・休憩・降車** を外す(過ごし方は「活動:」「まで:」の欄へ)。
#
# **v1/v2 は 1 バイトも動かさない**: 既存の表・コード・契約行は同一オブジェクトのまま。
# **コードは 1 つも動かさない**(テープ・checkpoint・``last_action`` の実体): 降車 2・待機 4・
# 休憩 10 は v3 では**欠番**(受理しない=``action_code_of(w, "v3")`` は ``UNDEFINED_ACTION``)、
# 並ぶ は役割語のコード 22 のまま**種別だけ横断へ**、新設「なし」は**末尾の 25**。
# 語彙数の上限 ``VOCAB_LIMIT_PER_KIND`` の assert は **v3 の表には掛けない**(D-92 (a): 門は
# 「契約行+エンジン効果+台帳行+テスト」)。v1 の assert は上のまま。
#
# expedient(本節分・アジェンダ §5 に登録)
# - 「なし」の契約行の文面(待機の行から「常に可能・時間経過・失敗しない」を引き継いだ)と
#   節名 ``D-116``(契約書 §2.1 の表の行ではない)。
# - 並ぶ の v3 行は v1 の行の ``section``/``permission_holder``/``table_row`` だけを差し替えた
#   (前提・効果・失敗の文面は「並ぶ/撮影」の共有行のまま)。**エンジンの適用分岐は段 2**
#   (``engine_action_codes("v3")`` に 並ぶ=22 を載せた=段 2 で ``_APPLY_BY_VOCAB["v3"]`` に要る)。
# - 横断語の**並び**(アジェンダ §1-1 の表の順=B0 の提示順)。

#: 安全弁の語(**失敗しない**・待機の代替=行動契約書 §2 共通の必須事項③)。
ACTION_WORD_NONE: Final[str] = "なし"
#: 「なし」の行動コード(= 25 = 食事 24 の**次**。既存コードは 1 つも動かない)。
NONE_ACTION_CODE: Final[int] = EAT_ACTION_CODE + 1
#: 役割語から横断語へ移る語(コードは役割語の 22 のまま)。
ACTION_WORD_QUEUE: Final[str] = "並ぶ"
#: v3 で**受理しない**語(コード 2・4・10 は欠番として残す=動かさない)。
REMOVED_ACTION_WORDS_V3: Final[tuple[str, ...]] = ("待機", "休憩", "降車")

_SPEC_NONE: Final[ActionSpec] = ActionSpec(
    word=ACTION_WORD_NONE,
    target_kind=TargetKind.NONE,
    preconditions=(),
    precondition_text="なし(常に可能=安全弁)",
    effects="時間経過(世界に触れない。過ごし方は「活動」欄・持続は「まで」欄が持つ)",
    cost="時間",
    failure_text="失敗しない",
    failure_codes=(),
    never_fails=True,
    tag="mechanism",
    section="D-116",
    table_row="§2 共通③ 失敗しない行動(待機の代替・D-116 C)",
)

#: 並ぶ の v3 行(**横断語**=権限保持者なし)。前提・効果・失敗の文面は v1 の行のまま。
_SPEC_QUEUE_V3: Final[ActionSpec] = replace(
    ACTION_SPECS[ACTION_WORD_QUEUE],
    section="D-116",
    permission_holder="",
    table_row="並ぶ/撮影(v3 で役割語から横断語へ・D-116 C)",
)

#: v3 の種別横断語(11 語 + なし)。**並びはアジェンダ §1-1 の表の順**(B0 の提示順)。
ACTION_VOCAB_V3: Final[tuple[str, ...]] = (
    "移動", "乗車", "購入", ACTION_WORD_EAT, "会話", "退去", "通報", "手伝い", "断る", "就寝",
    ACTION_WORD_QUEUE, ACTION_WORD_NONE,
)
#: v3 の役割語(11 語=v1 の 12 語から 並ぶ を横断へ移した残り・並びは v1 のまま)。
ROLE_ACTION_WORDS_V3: Final[tuple[str, ...]] = tuple(
    w for w in ROLE_ACTION_WORDS if w != ACTION_WORD_QUEUE
)
#: v3 でパーサが受理する全体集合(12 + 11 = 23 語)。
ALL_ACTION_WORDS_V3: Final[tuple[str, ...]] = ACTION_VOCAB_V3 + ROLE_ACTION_WORDS_V3

#: v3 の契約表(v2 の行から外す 3 語を抜き、並ぶ を差し替え、なし を足したもの)。
ACTION_SPECS_V3: Final[Mapping[str, ActionSpec]] = {
    **{
        w: ACTION_SPECS_V2[w]
        for w in ACTION_VOCAB_V3
        if w not in (ACTION_WORD_QUEUE, ACTION_WORD_NONE)
    },
    ACTION_WORD_QUEUE: _SPEC_QUEUE_V3,
    ACTION_WORD_NONE: _SPEC_NONE,
    **{w: ACTION_SPECS[w] for w in ROLE_ACTION_WORDS_V3},
}

#: 既存コード(v1 の 24 語+食事)+ なし。**v3 はこの表から引くだけ**(割り当てを変えない)。
_CODES_ALL_VERSIONS: Final[Mapping[str, int]] = {
    **ACTION_CODES, **ROLE_ACTION_CODES,
    ACTION_WORD_EAT: EAT_ACTION_CODE, ACTION_WORD_NONE: NONE_ACTION_CODE,
}
#: v3 の横断語 → コード(**エンジンに適用分岐が要る語**=``engine_action_codes("v3")``)。
ACTION_CODES_V3: Final[Mapping[str, int]] = {w: _CODES_ALL_VERSIONS[w] for w in ACTION_VOCAB_V3}
#: v3 の役割語 → コード(v1 と同じ値・並ぶ を除く)。
ROLE_ACTION_CODES_V3: Final[Mapping[str, int]] = {
    w: ROLE_ACTION_CODES[w] for w in ROLE_ACTION_WORDS_V3
}
_ALL_CODES_V3: Final[Mapping[str, int]] = {**ACTION_CODES_V3, **ROLE_ACTION_CODES_V3}
_ROLE_SET_V3: Final[frozenset[str]] = frozenset(ROLE_ACTION_WORDS_V3)

#: 版 → 安全弁の語(**未定義行動の落ち先**。v1/v2=待機・v3=なし=アジェンダ §1-1)。
SAFE_ACTION_BY_VERSION: Final[Mapping[str, str]] = {
    "v1": "待機", "v2": "待機", "v3": ACTION_WORD_NONE,
}

assert len(ACTION_VOCAB_V3) == 12 and len(ROLE_ACTION_WORDS_V3) == 11
assert len(set(ALL_ACTION_WORDS_V3)) == len(ALL_ACTION_WORDS_V3) == 23
assert not set(REMOVED_ACTION_WORDS_V3) & set(ALL_ACTION_WORDS_V3)
assert NONE_ACTION_CODE == 25
assert tuple(ACTION_SPECS_V3) == ALL_ACTION_WORDS_V3
# (v3 には ``VOCAB_LIMIT_PER_KIND`` の assert を**掛けない**=D-92 (a)。)

#: 版 → パーサが受理する語(``action_words``/``cross_action_words`` の実体)。
_WORDS_BY_VERSION: Final[Mapping[str, tuple[str, ...]]] = {
    "v1": ALL_ACTION_WORDS,
    "v2": ALL_ACTION_WORDS_V2,
    "v3": ALL_ACTION_WORDS_V3,
}
_CROSS_BY_VERSION: Final[Mapping[str, tuple[str, ...]]] = {
    "v1": ACTION_VOCAB_12,
    "v2": ACTION_VOCAB_13,
    "v3": ACTION_VOCAB_V3,
}
_ROLE_BY_VERSION: Final[Mapping[str, tuple[str, ...]]] = {
    "v1": ROLE_ACTION_WORDS,
    "v2": ROLE_ACTION_WORDS,
    "v3": ROLE_ACTION_WORDS_V3,
}
_SPECS_BY_VERSION: Final[Mapping[str, Mapping[str, ActionSpec]]] = {
    "v1": ACTION_SPECS,
    "v2": ACTION_SPECS_V2,
    "v3": ACTION_SPECS_V3,
}
#: 版 → **エンジンに適用分岐がある**語のコード(役割語は含まない=効果先が C4)。
#: ``engine.resolve._APPLY_BY_VOCAB`` と 1 対 1(**v3 の分岐は段 2** で足す)。
_ENGINE_CODES_BY_VERSION: Final[Mapping[str, Mapping[str, int]]] = {
    "v1": ACTION_CODES,
    "v2": {**ACTION_CODES, ACTION_WORD_EAT: EAT_ACTION_CODE},
    "v3": ACTION_CODES_V3,
}

#: **旧版への対応表**(F: 新語 → 旧語彙での読み替え。ラン間比較を壊さないための橋)。
#: 「食事」を v1 の語彙で読むと「購入」= 段0 辞書 v1 が ``食べる/飲む`` を写していた先
#: (語彙政策 v0 の★「意味の損失」行)。**読み替えは比較のときだけ**で、
#: エンジンの効果は v2 の契約行に従う(読み替えで購入の効果になるのではない)。
#:
#: **v3**(アジェンダ §1-1)は**両向き**を 1 つの表に持つ: 待機/休憩 → なし(v1/v2 のテープを
#: v3 の語彙で読む向き)と なし → 待機(v3 → v2/v1 の向き)。キーが版で交わらない
#: (なし は v3 にだけ・待機/休憩 は v1/v2 にだけ在る)ので向きはキーの所属で決まる。
#: **降車は欠番**(対応なし=そのまま返す)。
VOCAB_COMPAT: Final[Mapping[str, Mapping[str, str]]] = {
    "v2": {ACTION_WORD_EAT: "購入"},
    "v3": {"待機": ACTION_WORD_NONE, "休憩": ACTION_WORD_NONE, ACTION_WORD_NONE: "待機"},
}

#: 版 ``v`` → 「``v`` から 1 つ前の版へ降りる」読み替え(キーが ``v`` の語彙に在る行)。
_COMPAT_DOWN: Final[Mapping[str, Mapping[str, str]]] = {
    ver: {k: w for k, w in VOCAB_COMPAT.get(ver, {}).items() if k in _WORDS_BY_VERSION[ver]}
    for ver in VOCAB_VERSIONS
}
#: 版 ``v`` → 「1 つ前の版から ``v`` へ上がる」読み替え(キーが ``v`` の語彙に**無い**行)。
_COMPAT_UP: Final[Mapping[str, Mapping[str, str]]] = {
    ver: {k: w for k, w in VOCAB_COMPAT.get(ver, {}).items() if k not in _WORDS_BY_VERSION[ver]}
    for ver in VOCAB_VERSIONS
}


def check_vocab_version(vocab_version: str) -> str:
    """``vocab_version`` を検査して正規化する(不正値は ``ValueError``)。"""
    ver = str(vocab_version)
    if ver not in VOCAB_VERSIONS:
        raise ValueError(f"vocab_version は {VOCAB_VERSIONS} のどれか(いま {vocab_version!r})")
    return ver


def action_words(vocab_version: str = DEFAULT_VOCAB_VERSION) -> tuple[str, ...]:
    """その版でパーサが受理する行動語(v1=24 語・v2=25 語・v3=23 語)。

    ``"v1"``(既定)は ``ALL_ACTION_WORDS`` と**同一オブジェクト**を返す。
    """
    return _WORDS_BY_VERSION[check_vocab_version(vocab_version)]


def cross_action_words(vocab_version: str = DEFAULT_VOCAB_VERSION) -> tuple[str, ...]:
    """その版の**種別横断語**(v1=12 語・v2=13 語・v3=11 語+なし)。B0 の出力規約に出す並び。"""
    return _CROSS_BY_VERSION[check_vocab_version(vocab_version)]


def role_action_words(vocab_version: str = DEFAULT_VOCAB_VERSION) -> tuple[str, ...]:
    """その版の**役割語**(v1/v2=12 語=``ROLE_ACTION_WORDS`` そのもの・v3=11 語)。"""
    return _ROLE_BY_VERSION[check_vocab_version(vocab_version)]


def safe_action_word(vocab_version: str = DEFAULT_VOCAB_VERSION) -> str:
    """その版の安全弁の語(**失敗しない**・未定義行動の落ち先)。v1/v2=待機・v3=なし。"""
    return SAFE_ACTION_BY_VERSION[check_vocab_version(vocab_version)]


def engine_action_codes(vocab_version: str = DEFAULT_VOCAB_VERSION) -> Mapping[str, int]:
    """その版で**エンジンに適用分岐がある**語 → コード(役割語は含まない)。"""
    return _ENGINE_CODES_BY_VERSION[check_vocab_version(vocab_version)]


def compat_word(word: str, vocab_version: str = "v2", to_version: str = "v1") -> str:
    """ある版の語を別の版の語彙で読む(``VOCAB_COMPAT``・F)。対応が無い語はそのまま返す。

    版を 1 つずつ辿る(v3 → v1 は v3 → v2 → v1)。降りる向きは「その版の語彙に在るキー」の行、
    上がる向きは「その版の語彙に無いキー」の行を使う(``_COMPAT_DOWN``/``_COMPAT_UP``)。
    v2 → v1(既定)は従来どおり 食事 → 購入 だけ。

    Example:
        >>> compat_word("食事")
        '購入'
        >>> compat_word("移動")
        '移動'
        >>> compat_word("なし", "v3", "v1")
        '待機'
        >>> compat_word("休憩", "v1", "v3")
        'なし'
    """
    src = VOCAB_VERSIONS.index(check_vocab_version(vocab_version))
    dst = VOCAB_VERSIONS.index(check_vocab_version(to_version))
    w = str(word)
    if src > dst:
        for i in range(src, dst, -1):
            w = _COMPAT_DOWN[VOCAB_VERSIONS[i]].get(w, w)
    else:
        for i in range(src + 1, dst + 1):
            w = _COMPAT_UP[VOCAB_VERSIONS[i]].get(w, w)
    return w


assert len(ACTION_VOCAB_13) == 13
assert len(set(ALL_ACTION_WORDS_V2)) == len(ALL_ACTION_WORDS_V2)
assert EAT_ACTION_CODE == 24
assert set(VOCAB_COMPAT["v2"]) <= set(ALL_ACTION_WORDS_V2)
assert set(VOCAB_COMPAT["v2"].values()) <= set(ALL_ACTION_WORDS)
assert set(_COMPAT_UP["v3"]) <= set(REMOVED_ACTION_WORDS_V3)
assert set(_COMPAT_UP["v3"].values()) <= set(ALL_ACTION_WORDS_V3)
assert set(_COMPAT_DOWN["v3"]) == {ACTION_WORD_NONE}
assert set(_COMPAT_DOWN["v3"].values()) <= set(ALL_ACTION_WORDS_V2)


# ------------------------------------------------------------------ 2行形の整形と検査
#: 2行形の書式検査(**厳密**な詰め形。寛容パーサは ``llm.parser.parse_two_line``)。
TWO_LINE_RE: Final[re.Pattern[str]] = re.compile(
    r"^理由: (?P<reason>[^\n]{1,40})\n"
    r"行動: (?P<action>\S+) 対象: (?P<target>\S+) ひと言: (?P<comment>[^\n]{1,20})$"
)


def format_two_line(
    reason: str, action: str, target: str = NO_TARGET, comment: str = NO_TARGET
) -> str:
    """行動契約書 §1 の固定2行形に整形する(字数は呼び出し側が守る)。"""
    return f"理由: {reason}\n行動: {action} 対象: {target} ひと言: {comment}"


#: v3 の厳密 2 行形(アジェンダ §1-2: ひと言 を外し 活動・まで を足した詰め形)。
TWO_LINE_RE_V3: Final[re.Pattern[str]] = re.compile(
    r"^理由: (?P<reason>[^\n]{1,40})\n"
    r"行動: (?P<action>\S+) 対象: (?P<target>\S+) 活動: (?P<activity>\S{1,10}) "
    r"まで: (?P<until>\S+)$"
)


def format_two_line_v3(
    reason: str,
    action: str,
    target: str = NO_TARGET,
    activity: str = NO_TARGET,
    until: str = "次の予定",
) -> str:
    """v3 の固定 2 行形に整形する(字数は呼び出し側が守る)。``until`` の既定は語の 1 つ。"""
    return f"理由: {reason}\n行動: {action} 対象: {target} 活動: {activity} まで: {until}"


def is_role_action(word: str, vocab_version: str = DEFAULT_VOCAB_VERSION) -> bool:
    """§2.2 の役割語か(``"v3"`` では 並ぶ は横断語=役割語ではない)。"""
    if str(vocab_version) == "v3":
        return word in _ROLE_SET_V3
    return word in ROLE_ACTIONS


def action_code_of(word: str, vocab_version: str = DEFAULT_VOCAB_VERSION) -> int:
    """行動語 → コード。12語は 0..11・役割語は 12..・未知は ``UNDEFINED_ACTION``。

    ``vocab_version="v2"`` のときだけ「食事」が ``EAT_ACTION_CODE``(24)になる
    (既定 v1 では「食事」は語彙外=``UNDEFINED_ACTION``=段0 辞書/段1 の経路へ)。
    ``"v3"`` は v3 の 23 語だけを引く(待機 4・休憩 10・降車 2 は**欠番**=``UNDEFINED_ACTION``・
    なし=25)。
    """
    if str(vocab_version) == "v3":
        return int(_ALL_CODES_V3.get(word, UNDEFINED_ACTION))
    if word in ACTION_CODES:
        return int(ACTION_CODES[word])
    if word in ROLE_ACTION_CODES:
        return int(ROLE_ACTION_CODES[word])
    if word == ACTION_WORD_EAT and check_vocab_version(vocab_version) == "v2":
        return EAT_ACTION_CODE
    return UNDEFINED_ACTION


def spec_of(word: str, vocab_version: str = DEFAULT_VOCAB_VERSION) -> ActionSpec | None:
    """行動語 → 契約行(未知は None)。``"v2"`` で「食事」・``"v3"`` で v3 の 23 行を引く。"""
    return _SPECS_BY_VERSION[check_vocab_version(vocab_version)].get(word)


# ------------------------------------------------------------------ 「対象」欄の解釈
#: C2/品質プローブ形のセルID(``C-0117`` / ``C0117``)。
_CELL_C_RE: Final[re.Pattern[str]] = re.compile(r"^[Cc]-?(\d{1,6})$")
#: W2 ``w2_cells.parquet`` の ``place_id``(``g<ix>_<iy>_<band>``・ix/iy は負値あり)。
_CELL_W2_RE: Final[re.Pattern[str]] = re.compile(r"^g(-?\d{1,6})_(-?\d{1,6})_(GL|UG|DECK)$")
#: 人ID(``P-204`` / ``P204``)。
_PERSON_RE: Final[re.Pattern[str]] = re.compile(r"^[Pp]-?(\d{1,9})$")
#: 素の整数(= 人ID。行動契約書 §1 の「人ID」の最短表記)。
_INT_RE: Final[re.Pattern[str]] = re.compile(r"^(\d{1,9})$")
#: 駅/車両ID(「渋谷駅」「JY01」等の表層。**推定**=expedient)。
_STATION_RE: Final[re.Pattern[str]] = re.compile(r"^.{1,20}(駅|ホーム|番線)$")

#: 「対象」欄の周囲から剥がす飾り。
_TARGET_STRIP: Final[str] = " \t　「」『』\"'<>＜＞[]【】()()。、,."
#: **第271(2026-09-26)**: B2 の文「現在地はセルg-1_0_GL」を LLM がそのまま写した「セルg-1_0_GL」
#: (テープ 28 本で移動 10,751 呼・食事 921 呼・購入 387 呼)がセル ID と読まれず自由記述に落ちていた。
#: 「セル」「セルID:」「セルID_」の接頭辞を剥がした残りが**セル ID の形のときだけ**セルとして読む
#: (「セルID」だけ=説明語は NONE のまま・「セルID_コンビニ」は物カテゴリのまま)。
_CELL_PREFIX_RE: Final[re.Pattern[str]] = re.compile(r"^セル(?:ID)?\s*[:：_\-]?\s*")


@dataclass(frozen=True)
class Target:
    """「対象」欄の解釈結果。``raw`` は**常に逐語**(文面凍結のため加工しない)。

    Attributes:
        kind: 認識できた型。
        raw: 入力の逐語(前後の飾りだけ落としたもの)。
        cell_id: セルID(``C-0117`` は正規化せずそのまま・``g12_34_GL`` も同様)。
        cell_index: ``C-0117`` 形のときの整数(117)。W2 形は None。
        band: ``g..._GL`` 形のときの層(GL/UG/DECK)。
        person_id: 人ID の整数。
        category: 物カテゴリ(自由文)。
        poi_id: 固有名が**世界の POI** に解決できたときの POI 索引(C9b G6 a′・
            ``parse_target(..., landmarks=...)`` を通したときだけ入る。既定は ``None``)。
        wander: **「対象: あたり」**(語彙 v3・D-116 F=近傍を歩き回る)の印。型は増やさず
            ``ITEM_CATEGORY``・``category="あたり"`` のまま、この欄だけで区別する
            (アジェンダ §1-2)。v1/v2 では常に ``False``=**現行のまま**。
    """

    kind: TargetKind
    raw: str
    cell_id: str | None = None
    cell_index: int | None = None
    band: str | None = None
    person_id: int | None = None
    category: str | None = None
    poi_id: int | None = None
    wander: bool = False

    @property
    def is_none(self) -> bool:
        return self.kind is TargetKind.NONE

    def __str__(self) -> str:
        return self.raw or NO_TARGET


#: 「対象なし」を表す唯一のインスタンス。
NO_TARGET_VALUE: Final[Target] = Target(kind=TargetKind.NONE, raw=NO_TARGET)
#: テンプレート(``perception.templates`` の「対象: <セルID / 物のカテゴリ / 人ID / なし>」)の説明語。
#: これを値として写した応答は「対象なし」(第223・D-89)。
TARGET_PLACEHOLDERS: Final[frozenset[str]] = frozenset({
    "物のカテゴリ", "物カテゴリ", "セルID", "人ID", "カテゴリ", "セルID/物のカテゴリ/人ID", "セルID/物のカテゴリ/人ID/なし",
    "セルID|物カテゴリ|人ID|なし", "セルID|物のカテゴリ|人ID|なし",
})
_CATEGORY_SUFFIX: Final[str] = "のカテゴリ"

#: **語彙 v3** の「対象: あたり」(近傍を歩き回る=D-116 F・アジェンダ §1-2)。
TARGET_WANDER: Final[str] = "あたり"
#: **語彙 v3** の拠点の語(対象ヒント home/work/school へ写る=``llm.undefined``)。
#: v3 ではこの 3 語を**目印(POI)に解決しない**(「学校」が「〇〇小学校」の目印に当たらないように)。
TARGET_BASE_WORDS_V3: Final[tuple[str, ...]] = ("自宅", "職場", "学校")
#: **語彙 v3** の B0(``perception.templates.OUTPUT_SPEC_V3``・対象の役割知識)と、アジェンダ
#: §1-2 の契約形に出る**説明語**。値として写した応答は対象なしとして読む(第223 と同じ扱い・
#: v3 のときだけ ``TARGET_PLACEHOLDERS`` に足して引く)。**expedient**(実測前の予防)。
TARGET_PLACEHOLDERS_V3: Final[frozenset[str]] = frozenset({
    "名前かID", "名前かID/自宅/職場/学校/あたり/なし", "名前", "ID",
    "店や駅の名前", "店の種類", "人のID",
    "店名", "店のカテゴリ", "駅名",
})


#: 目印の固有名を部分一致で引くときの最短字数(C9b・expedient。1 字だと「像」「坂」が
#: どの目印にも当たる)。
LANDMARK_MIN_CHARS: Final[int] = 2


def resolve_landmark(token: str, landmarks: Mapping[str, int] | None) -> int | None:
    """固有名 → POI 索引(``None``=解決できない)。

    ``landmarks`` は「**NFKC 正規化済みの POI 名** → POI 索引」の表(作るのは世界側=
    ``world.state.World.landmark_targets``。``llm`` 層は world を import できないので
    表を**受け取るだけ**にしてある=import-linter 契約「llm は world を import しない」)。

    照合順(**expedient**・契約書に規則は無い):
      1. **完全一致**。
      2. **名 ⊂ 入力** のうち**最長の名**(「忠犬ハチ公像の前」→ 忠犬ハチ公像)。
      3. **入力 ⊂ 名** のうち**最短の名**(余計な語が最も少ない名)。同長は POI 索引の若い方。

    3 を「最短」にした理由: 実資産には ``忠犬ハチ公像`` のほかに ``ハチ公口``・
    ``ハチ公口自転車等駐輪場`` が landmark として入っており、最長を採ると「ハチ公」が
    **駐輪場**に解決してしまう。最短なら ``ハチ公口`` になる。
    **「ハチ公」の曖昧さ自体は残る**(像か出口か)=実測の表層が出るまで直さない。

    逐次ループ宣言(P4): 目印数ぶん(実資産 68・名 64 件)。完全一致で当たれば 0 回。
    """
    if not landmarks or not token:
        return None
    hit = landmarks.get(token)
    if hit is not None:
        return int(hit)
    if len(token) < LANDMARK_MIN_CHARS:
        return None
    inside: tuple[int, int, str] | None = None   # 名 ⊂ 入力(最長の名)
    outside: tuple[int, int, str] | None = None  # 入力 ⊂ 名(最短の名)
    for name, pid in landmarks.items():
        if len(name) < LANDMARK_MIN_CHARS:
            continue
        if name in token:
            cand = (-len(name), int(pid), name)
            if inside is None or cand < inside:
                inside = cand
        elif token in name:
            cand = (len(name), int(pid), name)
            if outside is None or cand < outside:
                outside = cand
    best = inside if inside is not None else outside
    return None if best is None else best[1]


def parse_target(
    text: str | None,
    landmarks: Mapping[str, int] | None = None,
    vocab_version: str = DEFAULT_VOCAB_VERSION,
) -> Target:
    """「対象」欄の文字列 → ``Target``。**例外を投げない**。

    認識順(先に当たったものを採る):
        ``なし``/空 → NONE、``C-0117``/``C0117`` → CELL、``g12_34_GL`` → CELL
        (第271: ``セルg12_34_GL`` / ``セルID: g12_34_GL`` も CELL=接頭辞を剥がして ``cell_id`` に入れる)、
        ``P-204``/``P204`` → PERSON、素の整数 → PERSON、``…駅`` → STATION_OR_VEHICLE、
        それ以外の自由文 → ITEM_CATEGORY(``landmarks`` を渡すと**固有名は POI 索引まで
        解決**して ``poi_id`` に入る=C9b G6 a′)。

    Args:
        landmarks: 目印(W6 の landmark/attraction)の「名 → POI 索引」表。
            ``None``(既定)では**1 バイトも挙動が変わらない**(``poi_id`` は常に ``None``)。
            駅名(``…駅``)の判定は**目印より先**に置いたままにしてある=表を渡しても
            既存の STATION_OR_VEHICLE の道は動かない。
        vocab_version: 語彙版。``"v3"`` のときだけ (i) ``あたり`` → ``wander=True``
            (``ITEM_CATEGORY``・``category="あたり"``)(ii) ``自宅/職場/学校`` は目印に解決しない
            (iii) v3 の説明語 ``TARGET_PLACEHOLDERS_V3`` も対象なしとして読む。
            **既定 ``"v1"``(と ``"v2"``)は 1 バイトも挙動が変わらない**。

    Note:
        EVENT(事象ID)は表層形が定まっていないため**この関数では出さない**
        (通報・遅延報告の対象は engine 側が文脈から決める)。

    Example:
        >>> parse_target("ハチ公", {"忠犬ハチ公像": 7}).poi_id
        7
        >>> parse_target("ハチ公").poi_id is None
        True
    """
    if text is None:
        return NO_TARGET_VALUE
    raw = str(text).strip().strip(_TARGET_STRIP).strip()
    if not raw or raw in (NO_TARGET, "無し", "none", "None", "NONE", "-", "—"):
        return NO_TARGET_VALUE
    token = unicodedata.normalize("NFKC", raw)
    v3 = str(vocab_version) == "v3"
    # 第223(D-89 (i)(a)): 観測テンプレートの**欄の説明語**をそのまま値として書いた応答
    # (実 LLM スモークで「物のカテゴリ」9,055 呼・「セルID」398 呼)は対象なしとして読む。
    # ``raw`` は残す(診断側が ``kind == NONE and raw != NO_TARGET`` で数えられる)。
    # 「食品のカテゴリ」のように説明語の型を付けた値は型だけ剥がして中身を読む。
    if token.replace(" ", "") in TARGET_PLACEHOLDERS:  # 「セルID / 物のカテゴリ / 人ID / なし」の空白差を吸収
        return Target(TargetKind.NONE, raw)
    if v3 and token.replace(" ", "") in TARGET_PLACEHOLDERS_V3:  # v3 の B0 の説明語
        return Target(TargetKind.NONE, raw)
    if token.endswith(_CATEGORY_SUFFIX) and len(token) > len(_CATEGORY_SUFFIX):
        token = token[: -len(_CATEGORY_SUFFIX)].strip()
        raw = token
    if v3 and token == TARGET_WANDER:
        # D-116 F: 近傍を歩き回る。型は増やさない(アジェンダ §1-2)。
        return Target(TargetKind.ITEM_CATEGORY, raw, category=TARGET_WANDER, wander=True)
    if v3 and token in TARGET_BASE_WORDS_V3:
        # 拠点の語(対象ヒントはパーサが ``llm.undefined.target_surface_hint`` で付ける)。
        return Target(TargetKind.ITEM_CATEGORY, raw, category=raw)

    # 第271: 「セル」接頭辞つきのセル ID(B2 の文の写し)。残りがセル ID の形のときだけ剥がす。
    cell_token = token
    pm = _CELL_PREFIX_RE.match(token)
    if pm and pm.end() > 0:
        rest = token[pm.end() :]
        if rest and (_CELL_C_RE.match(rest) or _CELL_W2_RE.match(rest)):
            cell_token = rest
    m = _CELL_C_RE.match(cell_token)
    if m:
        return Target(TargetKind.CELL, raw, cell_id=cell_token, cell_index=int(m.group(1)))
    m = _CELL_W2_RE.match(cell_token)
    if m:
        return Target(TargetKind.CELL, raw, cell_id=cell_token, band=m.group(3))
    m = _PERSON_RE.match(token)
    if m:
        return Target(TargetKind.PERSON, raw, person_id=int(m.group(1)))
    m = _INT_RE.match(token)
    if m:
        return Target(TargetKind.PERSON, raw, person_id=int(m.group(1)))
    if _STATION_RE.match(token):
        return Target(TargetKind.STATION_OR_VEHICLE, raw, category=raw)
    poi = resolve_landmark(token, landmarks)
    return Target(TargetKind.ITEM_CATEGORY, raw, category=raw, poi_id=poi)


# ------------------------------------------------------------------ 「活動」「まで」欄(語彙 v3)
#
# 正典: アジェンダ §1-2(第274)・草案 §4-2/§4-4(D-116 B/D)。活動=世界を変えない過ごし方
# (自由文 10 字・契約行も辞書写像も持たない)/まで=次に考え直す目安(持続の上限)。
# **パーサは語を型に写すだけ**。時刻・到着・相手・予定の tick への解決はエンジン(段 2)。
#
# expedient(本節分・アジェンダ §5 に登録)
# - ``UntilKind`` の**数値**(DEFAULT=0・以下アジェンダの列挙順 1..5)。
# - 既定 60 分・上限 480 分(アジェンダ §5 の行)。**0 分は MINUTES(0) のまま返す**(段 2 で扱う)。
# - 認識は**部分一致**(値に「到着」「相手」「次の予定」を含めばその型)・順序はアジェンダの列挙順
#   (到着 → 相手 → N分 → HH:MM → 次の予定)。**「時」を含む値は N分 として読まない**
#   (「1時間30分」「12時30分」を 30 分と誤読しないため=DEFAULT に落ちる。「N時間」は未対応)。
# - HH:MM は 0:00〜23:59 だけ(24:00 等は DEFAULT)。値は**その日の分**(時×60+分)で返し、
#   「過去なら翌日」の解決はエンジン。全角数字・全角コロンは NFKC で吸収する。

#: 「活動」欄の字数(アジェンダ §1-2「10 字以内」。超過は理由/ひと言と同じく**切り詰め+フラグ**)。
ACTIVITY_MAX_CHARS: Final[int] = 10
#: 「まで」が空・読めないときの持続[分](Concordia interrupt 駆動の docstring 既定 1 時間と同値)。
UNTIL_DEFAULT_MINUTES: Final[int] = 60
#: 「N分」の上限[分](1 回の決定が半日を超えないように)。
UNTIL_MAX_MINUTES: Final[int] = 480


class UntilKind(IntEnum):
    """「まで」欄の型(アジェンダ §1-2 の 6 型)。"""

    DEFAULT = 0  # 空・その他(既定 60 分)
    ARRIVAL = 1  # 到着(移動の到着イベントで満了)
    PARTNER = 2  # 相手(会話の成立で満了)
    MINUTES = 3  # N分
    CLOCK = 4  # HH:MM(その日の分・過去なら翌日はエンジン)
    NEXT_SCHEDULE = 5  # 次の予定(カレンダーの次の予定の開始)


@dataclass(frozen=True)
class Until:
    """「まで」欄の解釈結果。

    Attributes:
        kind: 型。
        value: MINUTES=分(上限 ``UNTIL_MAX_MINUTES`` で丸め済み)/ CLOCK=その日の分
            (時×60+分)/ DEFAULT=``UNTIL_DEFAULT_MINUTES`` / それ以外=0。
    """

    kind: UntilKind
    value: int = 0


#: 「まで」が空のときの値(= DEFAULT・60 分)。
DEFAULT_UNTIL: Final[Until] = Until(UntilKind.DEFAULT, UNTIL_DEFAULT_MINUTES)

_UNTIL_MINUTES_RE: Final[re.Pattern[str]] = re.compile(r"(\d+)\s*分")
_UNTIL_CLOCK_RE: Final[re.Pattern[str]] = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")


def parse_until(text: str | None) -> Until:
    """「まで」欄の文字列 → ``Until``。**例外を投げない**。

    Example:
        >>> parse_until("30分")
        Until(kind=<UntilKind.MINUTES: 3>, value=30)
        >>> parse_until("12:30").value
        750
        >>> parse_until("").kind is UntilKind.DEFAULT
        True
    """
    if text is None:
        return DEFAULT_UNTIL
    t = unicodedata.normalize("NFKC", str(text)).strip().strip(_TARGET_STRIP).strip()
    if not t:
        return DEFAULT_UNTIL
    if "到着" in t:
        return Until(UntilKind.ARRIVAL)
    if "相手" in t:
        return Until(UntilKind.PARTNER)
    if "時" not in t:
        m = _UNTIL_MINUTES_RE.search(t)
        if m:
            digits = m.group(1)
            n = int(digits) if len(digits) <= 6 else UNTIL_MAX_MINUTES
            return Until(UntilKind.MINUTES, min(n, UNTIL_MAX_MINUTES))
    m = _UNTIL_CLOCK_RE.search(t)
    if m:
        hh, mm = int(m.group(1)), int(m.group(2))
        if hh <= 23 and mm <= 59:
            return Until(UntilKind.CLOCK, hh * 60 + mm)
        return DEFAULT_UNTIL
    if "次の予定" in t:
        return Until(UntilKind.NEXT_SCHEDULE)
    return DEFAULT_UNTIL
