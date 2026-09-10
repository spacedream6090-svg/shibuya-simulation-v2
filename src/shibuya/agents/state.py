"""agents.state — 個体状態の SoA(``core.soa.Registry`` の上)+起床条件表+結果コード。

正典
- 実装計画書 §3: 「agents: 状態SoA/T0習慣/記憶/関係」「SoA: 1フィールド=1本の NumPy 配列+
  dtype レジストリ(M9)。**個体オブジェクトを作らない**」。
- 予算宣言表 M1 ≤30KB/体(内訳 M2 位置・運動・身体 ≤128B/体・M12 p_notice用2B+
  invocation distance 2B)。本モジュールが確保するのは M2+M12 相当の**コア欄のみ**
  (T0習慣 M3・記憶 M4・関係 M5・プロフィール M6 は C3 以降の別レジストリ)。
- 知覚契約書 §6 不応期表(11 行)= ``WakeCondition`` と ``REFRACTORY_MINUTES``。
  「タイマーは**体×条件ごと**」→ ``refractory_until`` は ``(n, 11)`` の int32(tick)。
- 行動契約書 §2.1 失敗の意味論 = ``ResultCode``(§6「直前の結果」に載る値)。
- 運用設計書 §2.2 Phase C:「engine.resolve が確定分だけ適用」=**世界状態への書き込み口は1本**。
  本モジュールは ``freeze()`` / ``writable()`` でそれを**機械強制**する(numpy の
  ``writeable=False``)。``.writable(`` を呼んでよいのは ``engine/resolve.py`` だけ
  (``tests/engine/test_two_phase.py`` の静的検査で強制)。

逐次ループ宣言(P4)
- ``freeze`` / ``thaw``: **フィールド数**ぶんのループ(20 本前後)。個体数に比例しない。

expedient(本モジュール分)
- フィールドの選定と dtype(設計書はバイト上限しか与えていない)。特に
  ``holdings`` を uint8 の**個数**にしたのは C2 の範囲で物の種別を持たないため
  (U-Goods の品目別在庫は C4)。
- ``refractory_until`` を「条件ごとに次に起床してよい tick」で持つ形(表は分で与えられている)。
  「同一相手60分」「同一話者30分」の**相手別**不応期は C2 では持たない(相手表が C3 の
  関係辺・傍受ゲートに依存するため)。持たないことを本書の未実装として登録。
- ``last_action``(1 byte)は「直前に**試みた**行動」。``activity``(現在の状態)では
  B6「直前の結果」の主語を復元できない(失敗した行動は状態に残らない)ので追加した
  (C3 結線・書き手は ``engine.resolve`` のみ)。**エンジン継続(``ENGINE_STEP``)は書かない**
  ——「移動の続き」は新しく試みた行動ではないので、直前の 移動 が主語のまま残るのが正しい。
- ``board_line`` / ``board_since``(5 B/体・D-51 乗車の意図保持)。「乗車を選んだがホームに
  居ない」体を世界がホームまで運び、着いたら待ち行列に並べるための 2 欄。**待ちは
  ``transit_state=0``(在圏)の中の状態**で、3 値(乗客の保存則の分母)は増やさない。
  待ちの打ち切り時間は ``engine.resolve.BOARD_WAIT_LIMIT_TICKS``(expedient)。
- ``last_result`` を 1 byte のコードにし、失敗の詳細(残高・次回開店時刻)は**持たない**
  (行動契約書 §6 は「残高/価格・次回開店時刻」を返せと言う=C3 のプロンプト側で
  現在値から再構成する。C2 は「どの失敗か」だけを保持)。
- 書き込み禁止ガード(``freeze``/``writable``)は agents と world に**同じ実装を二重に置く**。
  層契約(``world | agents`` は同層=相互 import 禁止)のため共有モジュールを作れない。
"""

from __future__ import annotations

from contextlib import contextmanager
from enum import IntEnum
from typing import Final, Iterator

import numpy as np

from shibuya.core.soa import Registry
from shibuya.core.types import EventClass

__all__ = [
    "AgentKind",
    "MOCK_KIND_COUNT",
    "Activity",
    "LAST_ACTION_NONE",
    "ResultCode",
    "WakeCondition",
    "N_WAKE_CONDITIONS",
    "REFRACTORY_MINUTES",
    "WAKE_CONDITION_CLASS",
    "RESULT_TEXT",
    "AgentState",
]


#: ``last_action`` の「まだ何も試みていない」値(**行動コードと衝突しない負値**)。
#: ``engine.commit.ENGINE_STEP`` も −1 だが、エンジン継続は「直前に試みた行動」ではない
#: (移動の続き)ので ``resolve`` は ENGINE_STEP を ``last_action`` に**書かない**。
LAST_ACTION_NONE: Final[int] = -1


class AgentKind(IntEnum):
    """個体の種別。

    0-4 は C2 の mock 用に置いた 5 値、**5-8 は C5(W16 母集団合成)で足した 4 値**。
    値は**固定**(``economy.anchors.WalletKind`` の写し・``perception.templates.KIND_WORDS``
    の索引・W16 出力 ``w16_population.parquet`` の ``kind`` 列と 1 対 1)。知覚契約書 §2.2
    「B1 種別(約10)」の枠内。

    W16 の割り当て規約(``build.pop.w16_population``)
      - ``RESIDENT``  : 舞台に常住し、舞台内の組織に勤めていない体(域外通勤・在宅・非就業)
      - ``WORKER``    : 舞台に常住し、舞台内の組織に勤める体(=在区就業)
      - ``COMMUTER``  : 域外常住・舞台内の組織に勤める体
      - ``STUDENT``   : 域外常住・舞台内の学校に通う体
      - ``VISITOR`` / ``FOREIGN_VISITOR`` / ``REGULAR_VISITOR``: 来街者(訪日・定期の別)
      - ``CREW``      : 乗務員・駅務・警察/消防などの職務者
      - ``DISPATCHER``: 運行/警備の指令
    """

    COMMUTER = 0  # 通勤者
    VISITOR = 1  # 来街者
    WORKER = 2  # 従業者
    RESIDENT = 3  # 居住者
    DISPATCHER = 4  # 指令(権限行動の観測用・C2 では行動しない)
    STUDENT = 5  # 通学者(W16)
    REGULAR_VISITOR = 6  # 定期来街者(W16)
    FOREIGN_VISITOR = 7  # 訪日来街者(W16)
    CREW = 8  # 乗務員・職務者(W16)


#: C2 の mock 合成日課が引く種別の数(0..3=通勤/来街/従業/居住)。**指令以降は出さない**。
#: ``len(AgentKind)`` を使うと C5 で種別を足したときに mock の乱数列が動くので定数で釘付ける。
MOCK_KIND_COUNT: Final[int] = 4


class Activity(IntEnum):
    """現在の行動状態(行動契約書 §2.1 の効果が落ちる先)。"""

    IDLE = 0
    MOVING = 1  # 移動
    WAITING = 2  # 待機
    RESTING = 3  # 休憩
    SLEEPING = 4  # 就寝
    SHOPPING = 5  # 購入(店頭滞在)
    CONVERSING = 6  # 会話
    RIDING = 7  # 乗車


class ResultCode(IntEnum):
    """「直前の結果」コード(行動契約書 §2.1 失敗の意味論 / §6 の 50 tok 欄の素材)。

    0 は成功。1 以上が失敗の型。``RESULT_TEXT`` に契約書の文言を持つ。
    """

    OK = 0
    UNREACHABLE = 1  # 到達不能
    INTERRUPTED = 2  # 途中打ち切り(混雑・閉鎖)
    TRAIN_FULL = 3  # 満員
    FARE_SHORT = 4  # 運賃不足
    NO_TRAIN = 5  # 列車なし
    NO_STOP = 6  # その駅には止まらない
    MONEY_SHORT = 7  # 所持金不足
    OUT_OF_STOCK = 8  # 在庫切れ
    CLOSED = 9  # 営業時間外
    PARTNER_BUSY = 10  # 相手が会話中
    REFUSED = 11  # 断られた
    PARTNER_GONE = 12  # 去った
    NO_BED = 13  # 寝る場所がない
    NO_PERMISSION = 14  # 権限なし
    LOST_ARBITRATION = 15  # 資源競合に落選(二相コミット Phase B)
    UNDEFINED_ACTION = 16  # 未定義行動(§7 段1)
    BAD_TARGET = 17
    INSUFFICIENT_ABILITY = 18  # 能力不足(手伝い・行動契約書 §2.1)


#: 契約書の文言(「直前の結果」の 50 tok 欄で使う短句)。
RESULT_TEXT: Final[dict[int, str]] = {
    ResultCode.OK: "成功",
    ResultCode.UNREACHABLE: "到達不能",
    ResultCode.INTERRUPTED: "途中打ち切り",
    ResultCode.TRAIN_FULL: "満員",
    ResultCode.FARE_SHORT: "運賃不足",
    ResultCode.NO_TRAIN: "列車なし",
    ResultCode.NO_STOP: "その駅には止まらない",
    ResultCode.MONEY_SHORT: "所持金不足",
    ResultCode.OUT_OF_STOCK: "在庫切れ",
    ResultCode.CLOSED: "営業時間外",
    ResultCode.PARTNER_BUSY: "相手が会話中",
    ResultCode.REFUSED: "断られた",
    ResultCode.PARTNER_GONE: "去った",
    ResultCode.NO_BED: "寝る場所がない",
    ResultCode.NO_PERMISSION: "権限なし",
    ResultCode.LOST_ARBITRATION: "先に取られた",
    ResultCode.UNDEFINED_ACTION: "未定義の行動",
    ResultCode.BAD_TARGET: "対象を特定できない",
    ResultCode.INSUFFICIENT_ABILITY: "能力不足",
}


class WakeCondition(IntEnum):
    """起床条件(知覚契約書 §6 不応期表の**11 行と 1 対 1**)。

    値は ``refractory_until`` の列番号。行の並びは契約書の表の順。
    """

    CONVERSATION_TURN = 0  # (iv) 会話ターン
    PLAN_SLEEPING = 1  # (iii) 計画境界: 睡眠中
    PLAN_WORKING = 2  # (iii) 計画境界: 就業/就学中
    PLAN_GENERAL = 3  # (iii) 計画境界: 一般活動
    PLAN_TRANSIT = 4  # (iii) 計画境界: 移動・待機中
    INTEROCEPTION = 5  # (ii) 内受容閾値
    ACQUAINTANCE = 6  # (ii) 知人出現
    PROXIMITY_SWAP = 7  # (ii) 近接入替
    BEING_WATCHED = 8  # (ii) 被注視
    OVERHEARD = 9  # (ii) 傍受
    CELL_BLOCK = 10  # (i) セル動的ブロック変化


#: 条件数 K(``refractory_until`` の列数)。
N_WAKE_CONDITIONS: Final[int] = len(WakeCondition)

#: 不応期[分](知覚契約書 §6 の表。睡眠中は「起床まで≥360 分」を 360 で表す)。
REFRACTORY_MINUTES: Final[tuple[int, ...]] = (
    0,  # 会話ターン(mechanism・床なし)
    360,  # 計画境界: 睡眠中(mechanism)
    150,  # 計画境界: 就業/就学中(expedient・GATSim 就業値)
    60,  # 計画境界: 一般活動(expedient)
    15,  # 計画境界: 移動・待機中(expedient)
    45,  # 内受容閾値(expedient・ヒステリシスで置換を試す)
    10,  # 知人出現(expedient・同一相手 60 分は C2 未実装)
    15,  # 近接入替(expedient・最大の暴発源)
    5,  # 被注視(expedient)
    5,  # 傍受(expedient・同一話者 30 分は C2 未実装)
    30,  # セル動的ブロック変化(expedient)
)

#: 起床条件 → 繰り延べアービタの 4 クラス(知覚契約書 §6・運用設計書 §2.5 と同順序)。
WAKE_CONDITION_CLASS: Final[tuple[EventClass, ...]] = (
    EventClass.CONVERSATION,
    EventClass.PLAN_BOUNDARY,
    EventClass.PLAN_BOUNDARY,
    EventClass.PLAN_BOUNDARY,
    EventClass.PLAN_BOUNDARY,
    EventClass.INDIVIDUAL,
    EventClass.INDIVIDUAL,
    EventClass.INDIVIDUAL,
    EventClass.INDIVIDUAL,
    EventClass.INDIVIDUAL,
    EventClass.CELL,
)

assert len(REFRACTORY_MINUTES) == N_WAKE_CONDITIONS
assert len(WAKE_CONDITION_CLASS) == N_WAKE_CONDITIONS

#: 内受容 3 変数の並び(``<名前>_stage`` フィールドの順序)。
INTEROCEPTION_FIELDS: Final[tuple[str, ...]] = ("hunger", "fatigue", "thermal")


class AgentState:
    """個体状態 SoA。``core.soa.Registry`` を1本持ち、フィールドは全て**宣言つき**(M9)。

    Example:
        >>> st = AgentState(4)
        >>> st.money[:] = 3_000
        >>> st.freeze()
        >>> st.money.flags.writeable
        False
    """

    def __init__(self, n: int, cap_bytes: int | None | str = "auto") -> None:
        """
        Args:
            n: 個体数。
            cap_bytes: 個体あたりバイト上限。``"auto"`` = 予算行 M1(30,000 B)を読む。
        """
        self.n = int(n)
        self.registry = Registry.for_agents(self.n, per_entity_byte_cap=cap_bytes)
        r = self.registry
        # ---- 位置・運動(M2 位置・運動・身体 ≤128B/体 の内数) ----
        r.declare("cell", np.int32, byte_budget_per_agent=4, mechanism=True,
                  doc="所属セル(place_id 索引・M2)。-1=場外")
        r.declare("node", np.int32, byte_budget_per_agent=4, mechanism=True,
                  doc="現在の歩行グラフノード(W1 node_idx・M2)")
        r.declare("band", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="層 UG=-1 / GL=0 / DECK=1(W2 band・M2)")
        r.declare("xy", np.float32, (2,), byte_budget_per_agent=8, mechanism=True,
                  doc="平面座標[m](W0 CRS・M2)")
        r.declare("path_next_node", np.int32, byte_budget_per_agent=4, mechanism=True,
                  doc="次ホップのノード(next-hop 表の結果・M2)。-1=経路なし")
        r.declare("target_node", np.int32, byte_budget_per_agent=4, mechanism=True,
                  doc="移動の目的ノード(行動語「移動」の対象・M2)。-1=目的なし")
        # ---- 身体・内受容(知覚契約書 §4 内受容第1陣3変数) ----
        r.declare("kind", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="AgentKind(通勤者/来街者/従業者/居住者/指令/通学者/定期来街/訪日/乗務・M2)")
        # ---- プロフィール(M6 ≤3KB/体・W16 母集団合成が入れる素性) ----
        r.declare("age", np.uint8, byte_budget_per_agent=1, mechanism=True,
                  doc="年齢[歳](W16・国勢調査/経済センサスへ raking 済み・M6)")
        r.declare("sex", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="性別 0=男 / 1=女 / -1=不明(W16・M6)")
        r.declare("hunger", np.uint8, byte_budget_per_agent=1, mechanism=True,
                  doc="空腹 0-10(内受容3変数・M2)")
        r.declare("fatigue", np.uint8, byte_budget_per_agent=1, mechanism=True,
                  doc="疲労 0-10(内受容3変数・M2)")
        r.declare("thermal", np.uint8, byte_budget_per_agent=1, mechanism=True,
                  doc="体感温度 0-10(内受容3変数・M2)")
        # 内受容の閾値段は**1変数=1本の連続配列**で持つ((n,3) にすると
        # ブロードキャスト比較が遅く P6 の 2 ms を食う=実測 0.6 ms/op vs 0.008 ms/op)
        r.declare("hunger_stage", np.int8, byte_budget_per_agent=1, mechanism=False,
                  doc="空腹の閾値段(ヒステリシス用の前回段・expedient=段の刻みは自前)")
        r.declare("fatigue_stage", np.int8, byte_budget_per_agent=1, mechanism=False,
                  doc="疲労の閾値段(同上)")
        r.declare("thermal_stage", np.int8, byte_budget_per_agent=1, mechanism=False,
                  doc="体感温度の閾値段(同上)")
        # ---- 経済(行動契約書 §2.1 購入・保存則) ----
        r.declare("money", np.int32, byte_budget_per_agent=4, mechanism=True,
                  doc="所持金[円](保存則 U11 の個体側・M2)")
        r.declare("holdings", np.uint8, byte_budget_per_agent=1, mechanism=False,
                  doc="所持品の個数(品目別在庫は C4 の U-Goods・expedient)")
        # ---- 行動・計画 ----
        r.declare("activity", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="Activity(idle/moving/…/riding・M2)")
        r.declare("plan_cursor", np.int16, byte_budget_per_agent=2, mechanism=True,
                  doc="T0 スケジュールの何番目の境界まで消化したか")
        r.declare("talk_partner", np.int32, byte_budget_per_agent=4, mechanism=True,
                  doc="会話中の相手 agent_id(-1=なし・行動契約書 §3)")
        r.declare("invocation_distance", np.uint16, byte_budget_per_agent=2, mechanism=False,
                  doc="次の計画境界までの残時間[分](M12・知覚契約書 §6 三役・expedient)")
        # ---- 交通(C4 鉄道運行・行動契約書 §2.1 乗車/降車・運用設計書 §2.6) ----
        r.declare("transit_state", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="0=bbox 内 / 1=乗車中 / 2=域外ノード滞在(U10 §1.1)。"
                      "**乗客の保存則の分母**: 3 値の件数和 = 個体数")
        r.declare("transit_ref", np.int32, byte_budget_per_agent=4, mechanism=True,
                  doc="乗車中=列車索引 / 域外滞在=外界ノード索引(路線索引)。-1=なし")
        # ---- 乗車の意図保持(D-51・2026-09-10 ユーザー決定 (c)) ----
        # **``transit_state`` を増やさない**(3 値は乗客の保存則の分母)。待ちは在圏(0)の中の状態。
        r.declare("board_line", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="乗ろうとしている路線索引(=そのホーム。-1=乗車の意図なし)。"
                      "ホーム以外で乗車を選ぶと世界が最寄りホームへ運ぶ(登録簿 §8 D-51)")
        r.declare("board_since", np.int32, byte_budget_per_agent=4, mechanism=False,
                  doc="ホームで待ち始めた tick(-1=まだ待っていない=移動中)。"
                      "打ち切り BOARD_WAIT_LIMIT_TICKS の判定に使う・expedient")
        # ---- 屋内占有・待ち行列(C4 混雑場・16行表 行2) ----
        r.declare("poi_ref", np.int32, byte_budget_per_agent=4, mechanism=False,
                  doc="在席中の POI 索引(-1=なし)。屋内占有の集約に使う(席数換算は expedient)")
        r.declare("poi_since", np.int32, byte_budget_per_agent=4, mechanism=False,
                  doc="在席を始めた tick(回転率=滞在上限の判定・expedient)")
        r.declare("queue_poi", np.int32, byte_budget_per_agent=4, mechanism=False,
                  doc="並んでいる POI 索引(-1=並んでいない)。M/M/c 近似の待ち行列")
        r.declare("queue_since", np.int32, byte_budget_per_agent=4, mechanism=False,
                  doc="並び始めた tick(離脱閾値の判定・expedient)")
        # ---- 起床機構(知覚契約書 §6) ----
        r.declare("refractory_until", np.int32, (N_WAKE_CONDITIONS,),
                  byte_budget_per_agent=4 * N_WAKE_CONDITIONS, mechanism=True,
                  doc="体×条件ごとの「次に起床してよい tick」(§6 運用規定②)")
        r.declare("wake_pending_class", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="保留中の起床クラス(EventClass・-1=なし)")
        # ---- 直前の結果(行動契約書 §6) ----
        r.declare("last_action", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="直前に**試みた**行動コード(llm.contract.ACTION_CODES・§6「直前の結果」の"
                      "主語。-1=まだ何も試みていない=LAST_ACTION_NONE)")
        r.declare("last_result", np.int8, byte_budget_per_agent=1, mechanism=True,
                  doc="ResultCode(直前の行動の成否・§6 の 50 tok 欄の素材)")
        r.declare("last_result_tick", np.int32, byte_budget_per_agent=4, mechanism=True,
                  doc="last_result を書いた tick(古い失敗を出さないため)")
        r.declare("fail_streak", np.uint8, byte_budget_per_agent=1, mechanism=False,
                  doc="同一失敗の連続回数(行動契約書 §6「4回で打ち切り」・expedient)")

        # 既定値(0 では意味が壊れる欄だけ)
        self.registry.cell[:] = -1
        self.registry.node[:] = -1
        self.registry.path_next_node[:] = -1
        self.registry.target_node[:] = -1
        self.registry.talk_partner[:] = -1
        self.registry.wake_pending_class[:] = -1
        self.registry.last_result_tick[:] = -1
        self.registry.last_action[:] = LAST_ACTION_NONE
        self.registry.transit_ref[:] = -1
        self.registry.board_line[:] = -1
        self.registry.board_since[:] = -1
        self.registry.poi_ref[:] = -1
        self.registry.poi_since[:] = -1
        self.registry.queue_poi[:] = -1
        self.registry.queue_since[:] = -1
        self.registry.sex[:] = -1
        self._frozen = False

    # ---- フィールドの素通し(``st.money`` で配列を引く) ----
    def __getattr__(self, name: str) -> np.ndarray:
        """宣言フィールドを属性で引く。

        Note:
            ``Registry`` 自身の属性(``kind``・``arrays``・``field`` 等)と**同名のフィールド**が
            ありうるので、``registry.field(name)`` を使う(``getattr(registry, name)`` だと
            ``Registry.kind``(= ``"agent"`` の文字列)が勝ってしまう)。
            同じ理由で ``agents.registry.kind`` は**使ってはいけない**——
            ``agents.kind`` か ``agents.registry.field("kind")`` を使う。
        """
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.__dict__["registry"].field(name)
        except (KeyError, AttributeError):
            raise AttributeError(f"未宣言のフィールド: {name!r}") from None

    def __len__(self) -> int:
        return self.n

    # ---- 書き込みガード(resolve 単一書き手の機械強制) ----
    @property
    def frozen(self) -> bool:
        return self._frozen

    def freeze(self) -> None:
        """全配列を読み取り専用にする(初期化が終わったら一度だけ呼ぶ)。

        逐次ループ宣言(P4): フィールド数ぶん(20 本前後)。
        """
        for arr in self.registry.arrays.values():
            arr.flags.writeable = False
        self._frozen = True

    def thaw(self) -> None:
        """全配列を書き込み可能に戻す(``writable`` 以外から呼ばない)。"""
        for arr in self.registry.arrays.values():
            arr.flags.writeable = True
        self._frozen = False

    @contextmanager
    def writable(self) -> Iterator["AgentState"]:
        """``with st.writable():`` の間だけ書ける。**呼んでよいのは engine/resolve.py だけ**。"""
        was_frozen = self._frozen
        if was_frozen:
            self.thaw()
        try:
            yield self
        finally:
            if was_frozen:
                self.freeze()

    # ---- 監査 ----
    def state_hash(self) -> str:
        """全フィールドの blake3(checkpoint 一致判定 T1/T2)。"""
        return self.registry.state_hash()

    def bytes_total(self) -> int:
        return self.registry.bytes_total()

    def budget_report(self):  # type: ignore[no-untyped-def]
        """M9 の宣言 vs 実バイト報告。"""
        return self.registry.budget_report()

    @property
    def declared_bytes_per_agent(self) -> int:
        return self.registry.declared_bytes_per_entity
