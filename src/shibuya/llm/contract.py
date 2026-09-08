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
from dataclasses import dataclass
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
    "action_code_of",
    "spec_of",
    "is_role_action",
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
    """「対象」欄の型(行動契約書 §1 の ``<セルID|物カテゴリ|人ID|なし>`` の一般化)。"""

    NONE = 0  # なし
    CELL = 1  # セルID
    ITEM_CATEGORY = 2  # 物カテゴリ(+店ID)
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


def is_role_action(word: str) -> bool:
    """§2.2 の役割語か。"""
    return word in ROLE_ACTIONS


def action_code_of(word: str) -> int:
    """行動語 → コード。12語は 0..11・役割語は 12..・未知は ``UNDEFINED_ACTION``。"""
    if word in ACTION_CODES:
        return int(ACTION_CODES[word])
    if word in ROLE_ACTION_CODES:
        return int(ROLE_ACTION_CODES[word])
    return UNDEFINED_ACTION


def spec_of(word: str) -> ActionSpec | None:
    """行動語 → 契約行(未知は None)。"""
    return ACTION_SPECS.get(word)


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
    """

    kind: TargetKind
    raw: str
    cell_id: str | None = None
    cell_index: int | None = None
    band: str | None = None
    person_id: int | None = None
    category: str | None = None

    @property
    def is_none(self) -> bool:
        return self.kind is TargetKind.NONE

    def __str__(self) -> str:
        return self.raw or NO_TARGET


#: 「対象なし」を表す唯一のインスタンス。
NO_TARGET_VALUE: Final[Target] = Target(kind=TargetKind.NONE, raw=NO_TARGET)


def parse_target(text: str | None) -> Target:
    """「対象」欄の文字列 → ``Target``。**例外を投げない**。

    認識順(先に当たったものを採る):
        ``なし``/空 → NONE、``C-0117``/``C0117`` → CELL、``g12_34_GL`` → CELL、
        ``P-204``/``P204`` → PERSON、素の整数 → PERSON、``…駅`` → STATION_OR_VEHICLE、
        それ以外の自由文 → ITEM_CATEGORY。

    Note:
        EVENT(事象ID)は表層形が定まっていないため**この関数では出さない**
        (通報・遅延報告の対象は engine 側が文脈から決める)。
    """
    if text is None:
        return NO_TARGET_VALUE
    raw = str(text).strip().strip(_TARGET_STRIP).strip()
    if not raw or raw in (NO_TARGET, "無し", "none", "None", "NONE", "-", "—"):
        return NO_TARGET_VALUE
    token = unicodedata.normalize("NFKC", raw)

    m = _CELL_C_RE.match(token)
    if m:
        return Target(TargetKind.CELL, raw, cell_id=raw, cell_index=int(m.group(1)))
    m = _CELL_W2_RE.match(token)
    if m:
        return Target(TargetKind.CELL, raw, cell_id=raw, band=m.group(3))
    m = _PERSON_RE.match(token)
    if m:
        return Target(TargetKind.PERSON, raw, person_id=int(m.group(1)))
    m = _INT_RE.match(token)
    if m:
        return Target(TargetKind.PERSON, raw, person_id=int(m.group(1)))
    if _STATION_RE.match(token):
        return Target(TargetKind.STATION_OR_VEHICLE, raw, category=raw)
    return Target(TargetKind.ITEM_CATEGORY, raw, category=raw)
