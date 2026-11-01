"""engine.calendar_self — カレンダー 1b「勤務の出入りを本人へ」(第 6 期 6-2・腕 ``--calendar 1b``)。

正: 決定 10-12 §4-1 CA2 (b)(勤務・通学の出入りを本人へ)・CA4(壊れた予定だけ拒む・本人に見せるのは置き場所の道具が現実に
教えることだけ・間に合わない/閉店中は記録だけ)・CA5(出勤率のくじは判断モデルまでのつなぎ・問い 1=本人が知っている予想と
観測を並べる・問い 2=モックは「そのまま」寄り)・CA7・CA8(計器の一覧・合否なし)・CA11・AT1(置き場所の性質で思い出し方)・
AT2(時間の見積り=経験・幅・余裕は本人・更新は直近の平均)・AT3(本人が経路を決めホームでは来た電車に乗る・**エンジンは
逆算して起こさない・間に合う便を選ばない・時刻で強制的に退出させない**)・経過時間の実感(R-111 §1 の形)・§4-2 TM5・TM8
(時計やスマホを見れば分単位・見なければおおよそ)・§4-4 CT0(時計と天気予報は 1b と一緒=道具の台帳の行)。
回答 10-12 §2-1(GPU の前に腕として作る=仮のモデル mock・古典)。口の約束 1-2・1-3・1-7・1-8。

腕(切替口): ``--calendar {w17,1b}``(環境変数 ``SHIBUYA_CALENDAR``・:func:`set_arm`)。既定 ``w17``=層を作らない(計画実行層が
W17 の週次表で到着・退出・就寝・起床を実行する=今と同じ・19 構成で不変)。``1b``=W20(構築の段 W20cal の週の表)の時刻つきの
勤務の約束を持つ体について、

1. **本人の予定の器**(``cal_store``): その日の約束を本人が知っている形で持つ(時刻・場所の言葉・置き場所・見積り・余裕)。
   置き場所(AT1)ごとの思い出し方=アプリ(本人が決めた時刻に通知)・アラーム(本人が決めた時刻に鳴る=周りの出来事)・手帳
   (見たとき=時計なしのおおよその時刻)・頭の中(本人が時計を見たとき=MR7 までは入力に載せるつなぎ)。CA4=壊れた予定
   (時刻が空・終わり ≤ 始まり・場所の種類が空)だけ拒み、前の日の約束との重なりは警告(数えるだけ)。
2. **時間の見積り**(AT2): ランの前に積んだ経験=実際の道のり(舞台の中=W3 の歩行グラフの節の数・舞台の外=粗い域外の時間)
   から幅 [lo, hi] で持つ(幅=その路線の便の間隔=待ちの最大)。余裕は本人の判断(仮のモデルは体の鍵で引く)。更新は直近の
   平均(記憶の仕組みまでのつなぎ)。記憶には実感の値を入れる(下の 6)。
3. **出入りの判断を本人へ**(CA2 (b)): 「出発するか・いつ出発するか・帰るか」を候補の口 J0 の候補(源 plan/continue/
   deliberate)として判断の口(``DecisionPort.choose``)に出す。入力は本人が知っている予想(``Prediction``)と観測
   (``Observation``)を並べる(CA5 問い 1)。出発を選んだ体は自分の路線のホームへ歩き(``begin_exit_walk``)、ホームでは来た
   電車に乗る(待ち行列と受容関数=世界の続き)・域外からは「出発の時刻+域外の時間」より後に最初にホームへ入る便で着く
   (``rail_arrive``)・舞台の中は行き先へ歩く(``begin_walk_to``)。**エンジンはしないこと**: 機会の時刻は本人が置いた記録
   (通知・アラーム・見る習慣・前の判断の「次に見る時刻」)だけ=逆算して起こさない・便は選ばない(域外からは来た便)・退出は
   電車の発車か境界を歩いて越えるときだけ(時刻で消さない・歩きが途切れたらその場に居続ける=E4 を外す)。
4. **つなぎの外し方**: この腕のランでは、管理する体(その日に時刻つきの勤務の約束がある体)の計画実行層の到着・退出(W17 の
   ARRIVE/DEPART と張り直しの到着)を実行しない(``PlanExecutor.io_hook``)。就寝・起床は W17 のまま(疲労の後)・来街者の来訪も
   W17 のまま(判断モデルの後)・出勤率のくじは残す(判断モデルまで)。
5. **計器**(CA8・合否なし): 出勤・帰宅の時刻の分布(W20 の約束との差)・通勤時間(見積り vs 実際 vs 実感)・5 分前到着・遅刻
   (錨は空欄)・計画一致率・15 分ごとの約束の場所に居る率・不可能な予定(間に合わない=記録だけ)・活動の切り替え・忘れた割合
   (置き場所ごと)・判断の数と源と番号・エンジンがしないこと 3 つの検査(下)・つなぎの台帳の数。manifest の末尾の
   ``calendar_1b``(腕のランだけ)。
6. **経過時間の実感**(R-111 §1 の形): 待ちは実感=1.9+0.72×実際[分](Watkins 2011・R-111 §1-2 の錨の値そのまま・ほかの
   項は 0)・待ち以外(歩く・乗る・域外)は比 1(R-111 §1-3 の空欄=係数を決め打ちしない)・言葉は 5 分に丸める。本人の
   見積りの更新は実感の値・実際の値は記録(``cal_meter``)に残す。

エンジンがしないこと 3 つの検査(計器・負の対照の試験が植えた写しで落ちることを確かめる):

- **時刻で強制的に退出させた体**(``checks.exits_unexplained``): 管理する体が域外へ出たのに、(a) 発車した電車に乗って出た
  (鉄道の発車が計画実行層に知らせる口 ``notify_departed_by_llm`` から ``note_rode_out``)・(b) この層が境界を歩いて越えさせた、
  のどちらでもない(=列車にも境界にも乗らずに消えた)数。うち歩きの途中で消えた分は ``exits_during_walk``(E4 の消去)。
  逆向き(この層の到着でなく急に現れた体)は ``appear_unexplained``。
- **逆算して起こした体**(``checks.backward_wakes``): 機会の時刻が本人の記録(置いた通知・アラーム・見る習慣・前の判断の
  「次に見る時刻」)を指さない数。終わりの時刻の気づき(つなぎ ``DOC-ca1b-end-notice``)は ``end_notices`` に別に数える。
- **間に合う便を選んだ数**(``checks.selected_trains``): 域外からの到着の便が「出発+域外の時間」より後に最初にホームへ
  入るその路線の便でない数(到着のたびに時刻表から数え直す)。

状態(状態台帳の腕の行): ``C1B``=本人の予定の器と見積り(``cal_store``・軸 1 behavior・軸 2 required)・``C1BM``=判断の
記録と計器(``cal_meter``・軸 1 diag・軸 2 required=再開でも日ごとの記録が通しと同じ)。腕 w17 は層が無い(None)=既定の
2 つのハッシュと状態のファイルは不変。再開=通し(日の頭の張り直しは W20・暦・日番号と保存した器から決まる)。

仮採用(10-13b §0-3・つなぎの台帳の行 ``DOC-ca1b-*``=記録 docs/bench/analysis/wallbounce-1012/ca1b/README.md の表):
置き場所の初期の割り振り(4 つ等分・体の鍵)・余裕の分布(0/5/10/15 分 等分)・時計を見る間隔(30 分・位相は体の鍵)・
見積りの初期値の作り方(節の数と便の間隔)・域外の時間(W20 の片道の時間−舞台の中の歩き)・手帳を見る時刻(その日の最初に
起きている刻み)・おおよその時刻(30 分に丸める)・終わりの時刻の気づき・目的のセルが空欄の場所は駅の口のセル・非鉄道の方面
は駅の口のセルを境界の代わり・定期券(計画の退出と同じ運賃の免除)・中断の再提示の上限・経過時間の実感の形。
仮のモデル(mock=見積りの幅の上を使う・古典=幅の真ん中を使う)は判断モデルまでのつなぎ(CA5 問い 2)。

層契約: engine の中・``world``/``agents`` は ``engine.resolve`` の口でだけ書く(``begin_walk_to``・``begin_exit_walk``・
``rail_arrive``・``rail_depart``=境界を歩いて越える・``release_indoor``・``balk_queue``・``set_plan_state``)。``build`` は import
しない(W20 の表は ``engine.calendar_shadow.load_table`` で読む)。乱数の流れは使わない(体ごとの割り振りは体の id と用途の
塩の混ぜ合わせ=決定論・ランの乱数列を消費しない=計画実行層の出勤率の抽選と同じ形)。提示の並べ替えは J0 の口の乱数のまま。

逐次ループ宣言(P4): (1) 刻みごとの機会の数ぶんのループ 1 本(``_opportunities``=判断の口を 1 体ずつ呼ぶ=頭の中の体は
30 分ごと・出発の前まで=1 体 1 日 約 20 回)。(2) 日の頭に 1 回、歩く節の数を数えるループ(``route_steps``=道のりの最大の節の
数ぶん・体はベクトル)と、路線の数ぶんのループ(便の表)。(3) 機会の判断の後の実行は種類ごとのベクトル演算。体の数に
比例する Python のループは (1) だけ。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import numpy as np

from shibuya.agents.state import Activity
from shibuya.core.hashing import blake3_hex
from shibuya.core.time_consts import MINUTES_PER_DAY, MINUTES_PER_HOUR, NS_PER_SECOND, SECONDS_PER_MINUTE
from shibuya.engine import calendar_shadow as _CS
from shibuya.engine import resolve as R
from shibuya.engine.decision.port import (
    DELIBERATE_KIND,
    SOURCE_CONTINUE,
    SOURCE_DELIBERATE,
    SOURCE_PLAN,
    Candidate,
    DecisionContext,
    DecisionPort,
)
from shibuya.engine.decision.sources import DELIBERATE_ID

__all__ = [
    "MODE_W17", "MODE_1B", "MODES", "DEFAULT_MODE", "SCHEMA", "FP_KEY", "MANIFEST_KEY", "MANIFEST_CONFIG",
    "MANIFEST_OBSERVED", "arm", "set_arm", "is_on", "PLACEMENTS", "PLACEMENT_TRAITS", "TRIGGERS", "TRIPS",
    "LOOK_INTERVAL_MIN", "MARGINS_MIN", "RECENT_K", "ROUND_MIN", "APPROX_ROUND_MIN", "FELT_WAIT_INTERCEPT",
    "FELT_WAIT_SLOPE", "MAX_RETRIES", "Observation", "Prediction", "CommuteMockPort", "CommuteClassicalPort",
    "commute_candidates", "observe_time", "felt_minutes", "duration_words", "validate_commitments", "route_steps",
    "hop_walk_steps",
    "Estimate", "update_estimate", "CalendarSelf", "manifest_fields", "build", "BRIDGES",
]

MODE_W17: Final[str] = "w17"
MODE_1B: Final[str] = "1b"
MODES: Final[tuple[str, ...]] = (MODE_W17, MODE_1B)
#: 既定(層を作らない=計画実行層が W17 で出入りを実行する=今と同じ)。
DEFAULT_MODE: Final[str] = MODE_W17
#: manifest の ``calendar_1b`` の形の版。
SCHEMA: Final[str] = "shibuya.calendar_self/1"
#: 設定の指紋の鍵(1b のランだけ入れる=既定の指紋は今のまま)。
FP_KEY: Final[str] = "calendar"
#: manifest の欄の名(腕のランだけ末尾に足す)。
MANIFEST_KEY: Final[str] = "calendar_1b"
MANIFEST_CONFIG: Final[tuple[str, ...]] = (
    "schema", "mode", "port", "w20", "placements", "look_interval_min", "margins_min", "recent_k", "round_min",
    "approx_round_min", "felt", "bridges")
MANIFEST_OBSERVED: Final[tuple[str, ...]] = ("days", "totals", "checks")

#: 状態台帳の腕の行の腕の名(``LedgerRow.arm``)。
LEDGER_ARM_NAME: Final[str] = "calendar"

_ARM: str = os.environ.get("SHIBUYA_CALENDAR", DEFAULT_MODE).strip().lower() or DEFAULT_MODE
if _ARM not in MODES:
    raise ValueError(f"SHIBUYA_CALENDAR は {MODES} のどれか(いま {_ARM!r})")


def arm() -> str:
    """いまの腕(``w17``=既定・``1b``=出入りを本人へ)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--calendar``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    global _ARM
    if str(name) not in MODES:
        raise ValueError(f"--calendar は {MODES} のどれか(いま {name!r})")
    _ARM = str(name)


def is_on(mode: str | None = None) -> bool:
    return str(_ARM if mode is None else mode) == MODE_1B


# ---------------------------------------------------------------- 置き場所(AT1・CA3)と機会のきっかけ
#: 置き場所の種類(CA3: 性質で書く・種類は増やせる)。番号は器の ``placement`` の値。
PLACEMENTS: Final[tuple[str, ...]] = ("アプリ", "アラーム", "手帳", "頭の中")
PL_APP, PL_ALARM, PL_PLANNER, PL_HEAD = range(4)
#: 置き場所の性質(CA3=知らせ・持ち歩き・見える範囲・忘れやすさ)と思い出し方(AT1)と時刻の見え方(TM8)。
PLACEMENT_TRAITS: Final[Mapping[str, Mapping[str, Any]]] = MappingProxyType({
    "アプリ": MappingProxyType({"知らせ": "本人が決めた時刻に通知", "持ち歩き": True, "見える範囲": "画面",
                                "忘れやすさ": "低い", "思い出し方": "通知", "時刻": "分(画面の時計)"}),
    "アラーム": MappingProxyType({"知らせ": "本人が決めた時刻に鳴る(周りの出来事として System 1 へ)", "持ち歩き": True,
                                  "見える範囲": "音", "忘れやすさ": "低い", "思い出し方": "鳴る",
                                  "時刻": "分(鳴った時刻)"}),
    "手帳": MappingProxyType({"知らせ": "無し", "持ち歩き": True, "見える範囲": "開いたとき", "忘れやすさ": "中",
                              "思い出し方": "見たとき", "時刻": "おおよそ(時計を見ていない)"}),
    "頭の中": MappingProxyType({"知らせ": "無し", "持ち歩き": True, "見える範囲": "無し", "忘れやすさ": "高い",
                                "思い出し方": "記憶で思い出せたとき(MR7 までは入力に載せるつなぎ)",
                                "時刻": "分(時計を見たとき)"}),
})
#: 機会のきっかけ(記録の ``trigger`` の番号)。
TRIGGERS: Final[tuple[str, ...]] = ("アプリの通知", "アラーム", "手帳を見た", "時計を見た", "終わりの時刻", "続き")
TR_APP, TR_ALARM, TR_PLANNER, TR_HEAD, TR_END, TR_RETRY = range(6)
#: 行きと帰り。
TRIPS: Final[tuple[str, ...]] = ("行き", "帰り")
TRIP_GO, TRIP_BACK = 0, 1

# ---------------------------------------------------------------- 仮採用の値(つなぎの台帳 DOC-ca1b-*)
#: 時計を見る間隔[分](頭の中の予定を思い出す機会=MR7 までのつなぎ・位相は体の鍵)。
LOOK_INTERVAL_MIN: Final[int] = 30
#: 余裕[分]の候補(本人の判断=仮のモデルは体の鍵で等分に引く)。
MARGINS_MIN: Final[tuple[int, ...]] = (0, 5, 10, 15)
#: 見積りの更新に使う直近の回数。
RECENT_K: Final[int] = 5
#: 経過時間を言葉にするときの丸め[分](R-111 §1-1 の丸め=5 分の倍数)。
ROUND_MIN: Final[int] = 5
#: 時計を見ないときの時刻の丸め[分](TM8 の「おおよそ」=未リサーチ)。
APPROX_ROUND_MIN: Final[int] = 30
#: 待ちの実感の形(R-111 §1-2 #1 Watkins 2011・○=実感=切片+傾き×実際・ほかの項は 0)。係数は錨の値そのまま。
FELT_WAIT_INTERCEPT: Final[float] = 1.9
FELT_WAIT_SLOPE: Final[float] = 0.72
#: 待ちの実感の式を当てる範囲[分](R-111 §1-1 #1 Watkins=停留所の待ち 3〜15 分の範囲の研究)。外は比 1(宣言)。
FELT_WAIT_RANGE_MIN: Final[tuple[float, float]] = (3.0, 15.0)
#: 歩きが途切れたときの再提示の上限(安全装置・当たったら数える)。
MAX_RETRIES: Final[int] = 8
#: 15 分の枠。
SLOT_MIN: Final[int] = 15

#: この段の仮採用とつなぎの台帳の行(manifest の ``bridges`` の行と記録の表)。
BRIDGES: Final[tuple[str, ...]] = (
    "BR-W17-IO-SLEEP", "BR-E4-EXIT-VANISH", "BR-ATTENDANCE-LOTTERY", "BR-K9-MONDAY",
    "DOC-ca1b-placement-initial", "DOC-ca1b-margin", "DOC-ca1b-look-interval", "DOC-ca1b-estimate-initial",
    "DOC-ca1b-estimate-update", "DOC-ca1b-outside-time", "DOC-ca1b-planner-look", "DOC-ca1b-approx-time",
    "DOC-ca1b-end-notice", "DOC-ca1b-blank-place-cell", "DOC-ca1b-gate-exit", "DOC-ca1b-commuter-pass",
    "DOC-ca1b-retry-cap", "DOC-ca1b-felt-form", "DOC-ca1b-provisional-model", "DOC-ca1b-scope",
    "DOC-ca1b-forecast-blank", "DOC-ca1b-events-what",
    # 〔検収〕H1・M2 (a)(c)・L4・L8・L10
    "DOC-ca1b-left-at-work", "DOC-ca1b-observation-form", "DOC-ca1b-llm-run-mock-port", "DOC-ca1b-alarm-system1",
    "DOC-ca1b-tools-n-tools", "DOC-ca1b-initial-inside",
)

# ---------------------------------------------------------------- 器の欄の番号
RT_NONE, RT_IN, RT_OUT, RT_LOCAL = range(4)
ROUTES: Final[tuple[str, ...]] = ("なし", "域外から舞台の中へ", "舞台の中から域外へ", "舞台の中")
(PH_NONE, PH_BEFORE, PH_GO_OUTSIDE, PH_GO_WALK, PH_GO_LEAVE, PH_AT, PH_BACK_LEAVE, PH_BACK_OUTSIDE, PH_BACK_WALK,
 PH_HOME, PH_STRANDED, PH_FORGOT) = range(12)
PHASES: Final[tuple[str, ...]] = ("なし", "出発の前", "域外を移動(行き)", "舞台の中を歩く(行き)", "舞台を出る(行き)",
                                  "約束の場所", "舞台を出る(帰り)", "域外を移動(帰り)", "舞台の中を歩く(帰り)", "家",
                                  "動けない", "行かなかった")
WK_NONE, WK_PLACE, WK_HOME, WK_LEAVE_RAIL, WK_LEAVE_GATE = range(5)
WALK_WORDS: Final[tuple[str, ...]] = ("なし", "約束の場所へ", "家へ", "ホームへ", "駅の口へ")
#: 日の頭に「行き来の途中」と読む段(夜をまたぐ勤務の約束の場所に居る体を含む)。
_INFLIGHT_PHASES: Final[tuple[int, ...]] = (PH_GO_OUTSIDE, PH_GO_WALK, PH_GO_LEAVE, PH_AT, PH_BACK_LEAVE,
                                            PH_BACK_OUTSIDE, PH_BACK_WALK)
#: 途中の体の今日の約束の控え(家に着いたら器に張る)。
_PEND_KEYS: Final[tuple[str, ...]] = ("route", "day", "day_T0", "start_T", "end_T", "place_kind", "place_cell", "lead")
#: 除いた理由(管理しない体)。
EXCLUDE_REASONS: Final[tuple[str, ...]] = ("約束なし", "授業(時刻が空欄)", "壊れた予定", "自宅で働く", "家も場所も域外",
                                           "出勤率のくじ", "表に無い")
EX_NO, EX_SCHOOL, EX_BROKEN, EX_HOME, EX_OUTSIDE, EX_ABSENT, EX_NOT_IN_TABLE = range(7)

_DECIDE_STEP_KEY: Final[str] = "cal1b"
#: W20 の場所の語(構築の段 W20cal の ``PLACE_WORDS`` の写し=engine は build を import しない・一致は試験が見る)。
W20_PLACE_WORDS: Final[tuple[str, ...]] = ("なし", "建物", "駅", "担当区域", "乗り物", "学校", "域外", "自宅")
_PK_OUTSIDE: Final[int] = W20_PLACE_WORDS.index("域外")
_PK_HOME: Final[int] = W20_PLACE_WORDS.index("自宅")


# ---------------------------------------------------------------- 決定論の割り振り(乱数の流れを使わない)
def _mix64(x: np.ndarray) -> np.ndarray:
    """splitmix64 の最終混合(決定論・ベクトル化・乱数の流れではない)。"""
    v = np.asarray(x, dtype=np.uint64).copy()
    with np.errstate(over="ignore"):
        v ^= v >> np.uint64(33)
        v *= np.uint64(0xFF51AFD7ED558CCD)
        v ^= v >> np.uint64(33)
        v *= np.uint64(0xC4CEB9FE1A85EC53)
        v ^= v >> np.uint64(33)
    return v


def _key_draw(agent_key: np.ndarray, purpose: str, seed: int | str, k: int) -> np.ndarray:
    """体の鍵と用途の塩から 0..k-1 の値(決定論・体の数に依らない)。"""
    salt = np.uint64(int(blake3_hex(f"calendar1b:{purpose}:{seed}".encode("utf-8"))[:16], 16))
    a = np.maximum(np.asarray(agent_key, dtype=np.int64), 0).astype(np.uint64) ^ salt
    return (_mix64(a) % np.uint64(max(int(k), 1))).astype(np.int64)


# ---------------------------------------------------------------- 時刻の見え方(TM8)と実感(R-111 §1)
def _hhmm(minute: int) -> str:
    m = int(minute)
    d, m = divmod(m, MINUTES_PER_DAY)
    h, mm = divmod(m, MINUTES_PER_HOUR)
    return ("翌" if d > 0 else "") + f"{h}:{mm:02d}"


def observe_time(minute: int, *, precise: bool) -> tuple[int, str]:
    """本人が読む時刻(TM8): 時計やスマホを見れば分単位・見なければ ``APPROX_ROUND_MIN`` 分に丸めた「ごろ」。"""
    m = int(minute)
    if precise:
        return m, _hhmm(m)
    r = int(round(m / APPROX_ROUND_MIN)) * APPROX_ROUND_MIN
    return r, _hhmm(r) + "ごろ"


def felt_minutes(actual_min: float, wait_min: float = 0.0) -> float:
    """経過時間の実感[分](R-111 §1 の形): 待ちは 1.9+0.72×実際(出典の範囲 3〜15 分の中だけ=外は比 1)・待ち以外は比 1
    (空欄=係数を置かない)。"""
    w = max(float(wait_min), 0.0)
    rest = max(float(actual_min) - w, 0.0)
    lo, hi = FELT_WAIT_RANGE_MIN
    felt_wait = FELT_WAIT_INTERCEPT + FELT_WAIT_SLOPE * w if lo <= w <= hi else w
    return rest + felt_wait


def duration_words(minutes: float) -> str:
    """本人に渡す長さの言葉(``ROUND_MIN`` 分に丸める・最小は「5 分ほど」)。"""
    r = max(int(round(float(minutes) / ROUND_MIN)) * ROUND_MIN, ROUND_MIN)
    return f"{r} 分ほど"


# ---------------------------------------------------------------- 本人が知っている予想と今の観測(CA5 問い 1)
@dataclass(frozen=True, slots=True)
class Observation:
    """今の観測(本人が見たもの)。``time_min``=本人が読んだその日の時刻[分](おおよそなら丸めた値)。"""

    time_min: int
    precise: bool
    words: str
    where: str
    trigger: str


@dataclass(frozen=True, slots=True)
class Prediction:
    """本人が知っている予想(約束の時刻と場所の言葉・見積りの幅・余裕・時計を見る間隔)。時刻はその日の分。"""

    trip: str
    kind: str
    start_min: int
    end_min: int
    place: str
    est_lo_min: float
    est_hi_min: float
    est_words: str
    margin_min: int
    look_interval_min: int


def commute_candidates(pred: Prediction) -> tuple[Candidate, ...]:
    """出入りの候補(J0 の候補の形・番号は口が振る)。行き=出発する/まだ出ない/よく考える・帰り=帰る/まだ残る/よく考える。"""
    if pred.trip == TRIPS[TRIP_GO]:
        go = Candidate(id="plan:出発", kind="移動",
                       text=f"出発する({pred.kind} {_hhmm(pred.start_min)} {pred.place})", source=SOURCE_PLAN)
        stay = Candidate(id="continue:まだ", kind="なし", text="まだ出ない(このまま続ける)", source=SOURCE_CONTINUE)
    else:
        go = Candidate(id="plan:帰る", kind="移動", text=f"帰る({pred.kind} {_hhmm(pred.end_min)} まで)", source=SOURCE_PLAN)
        stay = Candidate(id="continue:まだ", kind="なし", text="まだ残る(このまま続ける)", source=SOURCE_CONTINUE)
    return (go, stay, Candidate(id=DELIBERATE_ID, kind=DELIBERATE_KIND, text=DELIBERATE_KIND, source=SOURCE_DELIBERATE))


class CommuteMockPort(DecisionPort):
    """仮のモデル(mock・判断モデルまでのつなぎ=CA5 問い 2「モックはそのまま寄り」)。

    行き: 本人の予定の出発=約束の始まり − 見積りの幅の上 − 余裕。読んだ時刻がそれを過ぎていれば出発・まだなら「次に見る
    時刻」を連続値で返す(時計を見ていれば予定の出発に・おおよそなら時計を見る間隔の後)。約束の終わりを過ぎていたら行かない
    (次に見る時刻なし=忘れた)。帰り: 終わりを過ぎていれば帰る・まだなら終わりに見る。よく考える・その他は選ばない。
    """

    name = "mock"
    #: 見積りの幅のどこを使うか(mock=上=遅れない側)。
    use_center: bool = False

    def planned_departure(self, pred: Prediction) -> int:
        est = (pred.est_lo_min + pred.est_hi_min) / 2.0 if self.use_center else pred.est_hi_min
        return int(pred.start_min - int(np.ceil(est)) - int(pred.margin_min))

    def _answer(self, ctx: DecisionContext, presented: tuple[Candidate, ...]) -> tuple[str, dict[str, Any]]:
        obs: Observation = ctx.percept
        pred: Prediction = ctx.prediction
        plan = next(c.id for c in presented if c.source == SOURCE_PLAN)
        stay = next(c.id for c in presented if c.source == SOURCE_CONTINUE)
        t = int(obs.time_min)
        if pred.trip == TRIPS[TRIP_GO]:
            if t >= int(pred.end_min):
                return stay, {"continuous": {"next_look_min": -1.0}, "reason": "約束の時刻が過ぎた"}
            p = self.planned_departure(pred)
            if t >= p:
                return plan, {"continuous": {"planned_min": float(p)}, "reason": "出る時刻になった"}
            nxt = p if obs.precise else min(p, t + int(pred.look_interval_min))
            return stay, {"continuous": {"next_look_min": float(nxt), "planned_min": float(p)}, "reason": "まだ早い"}
        if t >= int(pred.end_min):
            return plan, {"continuous": {"planned_min": float(pred.end_min)}, "reason": "終わった"}
        nxt = int(pred.end_min) if obs.precise else min(int(pred.end_min), t + int(pred.look_interval_min))
        return stay, {"continuous": {"next_look_min": float(nxt)}, "reason": "まだ終わっていない"}


class CommuteClassicalPort(CommuteMockPort):
    """仮のモデル(古典=見積りの幅の真ん中を使う)。ほかは mock と同じ規則(判断モデルまでのつなぎ)。"""

    name = "classical"
    use_center = True


# ---------------------------------------------------------------- CA4(壊れた予定だけ拒む・重なりは警告)
def validate_commitments(start: Sequence[int], end: Sequence[int], *, kind: Sequence[int] | None = None,
                         place_kind: Sequence[int] | None = None) -> tuple[np.ndarray, list[tuple[int, int]]]:
    """1 人の約束の列を確かめる(CA4 (d))。返り値=(壊れた行の印, 重なりの組の一覧)。

    壊れた=時刻が空(負)・終わり ≤ 始まり・種類か場所の種類が空(0)。壊れた行は拒む(呼び手が器に入れない)。重なりは
    警告だけ(アプリなら重なりの警告=本人に見せるのは道具が現実に教えること・行は残す)。
    """
    s = np.asarray(start, dtype=np.int64).ravel()
    e = np.asarray(end, dtype=np.int64).ravel()
    bad = (s < 0) | (e < 0) | (e <= s)
    if kind is not None:
        bad |= np.asarray(kind, dtype=np.int64).ravel() <= 0
    if place_kind is not None:
        bad |= np.asarray(place_kind, dtype=np.int64).ravel() <= 0
    ok = np.flatnonzero(~bad)
    order = ok[np.argsort(s[ok], kind="stable")]
    pairs: list[tuple[int, int]] = []
    for i, j in zip(order[:-1].tolist(), order[1:].tolist()):  # 逐次ループ宣言: 1 人の約束の数ぶん
        if int(s[j]) < int(e[i]):
            pairs.append((int(i), int(j)))
    return bad, pairs


# ---------------------------------------------------------------- AT2 見積り
@dataclass(frozen=True, slots=True)
class Estimate:
    """見積りの幅[分](``lo``〜``hi``)。"""

    lo: float
    hi: float

    @property
    def center(self) -> float:
        return (self.lo + self.hi) / 2.0


def update_estimate(recent: Sequence[float], initial: Estimate) -> Estimate:
    """直近の実感の値の平均で見積りを作り直す(記憶の仕組みまでのつなぎ)。幅=直近の最小と最大(2 回より少なければ最初の幅)。"""
    v = np.asarray([x for x in recent if np.isfinite(x)], dtype=np.float64)
    if v.size == 0:
        return initial
    c = float(v.mean())
    w = float(v.max() - v.min()) if v.size >= 2 else float(initial.hi - initial.lo)
    return Estimate(lo=max(c - w / 2.0, 0.0), hi=c + w / 2.0)


def hop_walk_steps(steps: Any, hop_steps: Any, ids: Any) -> np.ndarray:
    """節の数 → 歩く刻み(〔第 5 期 空間の段 1・検収 M5〕)。``hop_steps`` が None なら 1 刻み 1 節(legacy の見積り=B8)・
    nav1 のランは節 1 つの刻み(W1 の辺長の平均 ÷ 本人の m/刻み)を掛ける(体 ``ids`` ごと)。"""
    st = np.asarray(steps)
    if hop_steps is None:
        return st
    return st.astype(np.float64) * np.asarray(hop_steps, dtype=np.float64)[np.asarray(ids, dtype=np.int64)]


def route_steps(world: Any, src_node: np.ndarray, dst_node: np.ndarray, *, cap: int = 4_000) -> np.ndarray:
    """歩行グラフ(W3 の next-hop)で src → dst の節の数(着かなければ −1)。体はベクトル・ループは道のりの節の数ぶん。"""
    s = np.asarray(src_node, dtype=np.int64).ravel()
    d = np.asarray(dst_node, dtype=np.int64).ravel()
    out = np.full(s.size, -1, dtype=np.int64)
    ok = (s >= 0) & (d >= 0)
    out[ok & (s == d)] = 0
    live = np.flatnonzero(ok & (s != d))
    cur = s[live].copy()
    for k in range(1, int(cap) + 1):  # 逐次ループ宣言: 道のりの節の数ぶん(上限 cap)
        if live.size == 0:
            break
        nxt = np.asarray(world.graph.route_next_node(cur, d[live]), dtype=np.int64)
        dead = nxt < 0
        arrived = ~dead & (nxt == d[live])
        out[live[arrived]] = k
        keep = ~dead & ~arrived
        live, cur = live[keep], nxt[keep]
    return out


def first_entering_train(rail: Any, line: int, ready_T: int) -> int:
    """検査の口(実装の ``CalendarSelf.first_train`` と別に鉄道の表を直に引く): 路線 ``line`` で ``ready_T`` 以降に最初に
    ホームへ入る便(同着は便の索引の小さい方)。無ければ −1。"""
    enter = np.asarray(rail.enter_tick, dtype=np.int64)
    ok = np.flatnonzero((np.asarray(rail.train_line, dtype=np.int64) == int(line)) & (enter >= int(ready_T)))
    if ok.size == 0:
        return -1
    best = enter[ok].min()
    return int(ok[enter[ok] == best].min())


# ---------------------------------------------------------------- 層
def _i(n: int, v: int = -1, dt: Any = np.int64) -> np.ndarray:
    return np.full(int(n), v, dtype=dt)


class CalendarSelf:
    """カレンダー 1b の層(状態台帳の腕の行 ``C1B``・``C1BM``・腕 ``--calendar 1b`` のランだけ)。

    Args:
        table: W20 の週の表(``engine.calendar_shadow.load_table``=ランの体の並び)。
        calendar: 暦(``engine.calendar.SimCalendar``・読むだけ)。
        agents / world: 状態(書くのは ``engine.resolve`` の口だけ)。
        presence: 計画実行層(読むだけ=自宅・路線・駅の口・出勤率のくじ・鉄道・W17 の到着の参考。口 ``io_hook`` を挿す)。
        port: 判断の口(``CommuteMockPort``・``CommuteClassicalPort``)。
        agent_key: 体の鍵(W16 の ``agent_id``=割り振りの鍵)。
        seed: 割り振りの塩の種。
        step_seconds: 刻みの幅[秒]。
        steps_per_day: 1 日の刻みの数。
        tools: 道具の台帳(1-7・時計の行を読む・無ければ全員が時計を見られる扱い)。
        events: 出来事の記録(1-3・無ければ書かない)。
    """

    LEDGER_ARM: Final[str] = LEDGER_ARM_NAME

    def __init__(self, table: Any, *, calendar: Any, agents: Any, world: Any, presence: Any, port: DecisionPort,
                 agent_key: Any, seed: int | str, step_seconds: int, steps_per_day: int, events: Any = None,
                 tools: Any = None, hop_steps: Any = None) -> None:
        self.table = table
        #: 〔第 5 期 空間の段 1・検収 M5〕節 1 つを歩く刻み(体ごと)。None=1 刻み 1 節(legacy の見積り=B8)・nav1 のランは
        #: W1 の辺長の平均 ÷ 本人の m/刻み(``store_choice.walk_m_per_tick``)
        self.hop_steps = None if hop_steps is None else np.asarray(hop_steps, dtype=np.float64)
        self.calendar = calendar
        self.agents = agents
        self.world = world
        self.presence = presence
        self.port = port
        self.events = events
        self.seed = seed
        self.step_seconds = int(step_seconds)
        self.tpd = int(steps_per_day)
        self.tools = tools
        n = int(agents.n)
        self.n = n
        self.rail = getattr(presence, "rail", None)
        #: この刻みに歩き始めた体(``engine.systems.body.sys_presence`` が活動層を「目的地つき移動・到着まで」にする)。
        self.walk_started_now = np.empty(0, dtype=np.int64)
        key = np.full(n, -1, dtype=np.int64)
        src = np.asarray(agent_key, dtype=np.int64).ravel()
        key[: min(n, src.size)] = src[: min(n, src.size)]
        exits = np.asarray(presence._exit_cells(), dtype=np.int64)
        line = np.asarray(presence.line_of_agent, dtype=np.int64)[:n]
        rail_on = self.rail is not None and bool(getattr(self.rail, "active", False))
        line = np.where(rail_on, line, -1)
        exit_cell = np.full(n, -1, dtype=np.int32)
        if exits.size:
            exit_cell[:] = exits[np.arange(n, dtype=np.int64) % exits.size]
        plat = np.full(n, -1, dtype=np.int32)
        if rail_on:
            lc = np.asarray(getattr(self.rail, "line_cell", np.empty(0)), dtype=np.int64)
            has = (line >= 0) & (line < lc.size)
            plat[has] = lc[line[has]]
        plat = np.where(plat >= 0, plat, exit_cell)
        #: 本人の予定の器(状態台帳の腕の行 C1B=軸 1 behavior・軸 2 required)。体ごとの配列の dict。
        self.cal_store: dict[str, np.ndarray] = {
            # ---- ランの間に変わらない本人の性質(体の鍵から)----
            "placement": _key_draw(key, "placement", seed, len(PLACEMENTS)).astype(np.int8),
            "margin": np.asarray(MARGINS_MIN, dtype=np.int16)[_key_draw(key, "margin", seed, len(MARGINS_MIN))],
            "look_phase": _key_draw(key, "look_phase", seed, LOOK_INTERVAL_MIN).astype(np.int16),
            "habit_ref": np.arange(1, n + 1, dtype=np.int64),
            "home_cell": np.asarray(presence.home_cell, dtype=np.int32)[:n].copy(),
            "line": line.astype(np.int32),
            "exit_cell": exit_cell,
            "arrive_cell": plat.astype(np.int32),
            # ---- その日の約束(日の頭に張る)----
            "managed": np.zeros(n, dtype=bool), "watch": np.zeros(n, dtype=bool),
            "route": np.zeros(n, dtype=np.int8), "phase": np.zeros(n, dtype=np.int8),
            "day": _i(n), "day_T0": _i(n), "start_T": _i(n), "end_T": _i(n), "place_kind": np.zeros(n, dtype=np.int8),
            "place_cell": _i(n, -1, np.int32), "lead": np.zeros(n, dtype=np.int16), "d_out": np.zeros(n, dtype=np.int16),
            "walk_go": np.zeros(n, dtype=np.int16),
            # ---- 前の日の行き来の途中の体の今日の約束の控え(家に着いたら張る)----
            "pend_route": _i(n, -1, np.int8), "pend_day": _i(n), "pend_day_T0": _i(n), "pend_start_T": _i(n),
            "pend_end_T": _i(n), "pend_place_kind": _i(n, -1, np.int8), "pend_place_cell": _i(n, -1, np.int32),
            "pend_lead": _i(n, -1, np.int16),
            # ---- 見積り(日をまたいで持つ)----
            "est_init": np.zeros(n, dtype=bool), "est_lo": np.zeros(n, dtype=np.float32),
            "est_hi": np.zeros(n, dtype=np.float32), "est0_lo": np.zeros(n, dtype=np.float32),
            "est0_hi": np.zeros(n, dtype=np.float32), "recent": np.full((n, RECENT_K), np.nan, dtype=np.float32),
            "recent_n": np.zeros(n, dtype=np.int8),
            # ---- 機会(次に見る時刻と、それを置いた記録)----
            "plan_T": _i(n), "next_T": _i(n), "next_ref": _i(n), "next_trig": _i(n, -1, np.int8),
            # ---- 行きと帰りの時刻 ----
            "go_T": _i(n), "move_T": _i(n), "arrive_T": _i(n), "back_T": _i(n), "home_T": _i(n),
            "wait_go": np.zeros(n, dtype=np.float32), "plat_T": _i(n), "impossible": np.zeros(n, dtype=bool),
            "retries": np.zeros(n, dtype=np.int16), "switches": np.zeros(n, dtype=np.int16),
            "today_pending": np.zeros(n, dtype=bool),
            # ---- 域外からの到着(本人の出発の時刻+域外の時間 → 来た便)----
            "arr_T": _i(n), "arr_ready_T": _i(n), "arr_train": _i(n), "arr_cell": _i(n, -1, np.int32),
            "arr_trip": _i(n, -1, np.int8),
            # ---- 歩き ----
            "walk_kind": np.zeros(n, dtype=np.int8), "walk_node": _i(n, -1, np.int32),
            "walk_cell": _i(n, -1, np.int32), "walk_pending": np.zeros(n, dtype=bool),
            "walk_trip": _i(n, -1, np.int8),
            # ---- 連続性の検査の控え(直前の刻み)----
            "st_prev": np.full(n, -1, dtype=np.int8), "bl_prev": np.zeros(n, dtype=bool),
            "flag_cross": np.zeros(n, dtype=bool), "flag_arrive": np.zeros(n, dtype=bool),
            "flag_rode": np.zeros(n, dtype=bool),
            # ---- 〔検収 H1〕勤務中に本人の行為で舞台を出た回数と、約束の場所に戻った回数(その日)----
            "away_n": np.zeros(n, dtype=np.int16), "back_n": np.zeros(n, dtype=np.int16),
        }
        #: 判断の記録と計器(状態台帳の腕の行 C1BM=軸 1 diag・軸 2 required)。
        self.cal_meter: dict[str, Any] = {
            "days": {}, "cur": {}, "next_id": int(n) + 1, "last_T": -1,
            "checks": {"exits_unexplained": 0, "exits_during_walk": 0, "appear_unexplained": 0, "backward_wakes": 0,
                       "end_notices": 0, "selected_trains": 0, "inbound_checked": 0, "opportunities": 0},
            "trips_total": 0,
        }
        #: 路線ごとの便の表(日の頭に作り直す=鉄道の便が日の頭に足される)。
        self._line_tab: dict[int, tuple[np.ndarray, np.ndarray]] = {}
        self._headway: dict[int, float] = {}
        self.source = MODE_1B

    # ------------------------------------------------------------------ 口(計画実行層が呼ぶ)
    @property
    def io_off(self) -> np.ndarray:
        """計画実行層が到着・退出を実行しない体(その日に管理する体と、前の日の行き来の途中の体)。"""
        return self.cal_store["watch"]

    def note_suppressed(self, kind: str, n: int) -> None:
        """計画実行層が実行しなかった W17 の到着・退出の数(計器)。"""
        cur = self.cal_meter["cur"]
        if cur:
            sup = cur.setdefault("suppressed_w17", {"arrive": 0, "depart": 0})
            sup[kind] = int(sup.get(kind, 0)) + int(n)

    def note_rode_out(self, agent_ids: np.ndarray) -> None:
        """管理する体が発車した電車に乗って域外へ出た(鉄道の発車が計画実行層に知らせる口から)=連続性の検査の手がかり。"""
        a = np.asarray(agent_ids, dtype=np.int64)
        if a.size:
            self.cal_store["flag_rode"][a] = True

    def walk_hold(self, agent_ids: np.ndarray) -> np.ndarray:
        """この層の歩き(行き先へ・ホームへ・境界へ)の途中の体(``PlanExecutor.suppress_walker_wakes`` が場所の変化と満了と
        計画境界で起こさない=9a の歩いて乗る退出と同じ扱い)。"""
        a = np.asarray(agent_ids, dtype=np.int64)
        return self.cal_store["walk_kind"][a] > 0

    # ------------------------------------------------------------------ 時刻の換算
    def _steps(self, minutes: Any) -> np.ndarray:
        m = np.asarray(minutes, dtype=np.float64)
        return np.rint(m * SECONDS_PER_MINUTE / self.step_seconds).astype(np.int64)

    def _minutes(self, steps: Any) -> np.ndarray:
        return np.asarray(steps, dtype=np.float64) * self.step_seconds / SECONDS_PER_MINUTE

    def _new_id(self) -> int:
        i = int(self.cal_meter["next_id"])
        self.cal_meter["next_id"] = i + 1
        return i

    # ------------------------------------------------------------------ 便の表
    def _rebuild_lines(self) -> None:
        self._line_tab = {}
        rail = self.rail
        if rail is None or not bool(getattr(rail, "active", False)):
            return
        enter = np.asarray(rail.enter_tick, dtype=np.int64)
        tline = np.asarray(rail.train_line, dtype=np.int64)
        for li in np.unique(tline).tolist():  # 逐次ループ宣言: 路線の数ぶん(≤ 8)
            idx = np.flatnonzero(tline == li)
            order = idx[np.argsort(enter[idx], kind="stable")]
            self._line_tab[int(li)] = (enter[order], order)
            if int(li) not in self._headway:
                lo, hi = rail.day_range(0) if hasattr(rail, "day_range") else (0, enter.size)
                day0 = order[(order >= lo) & (order < hi)]
                gaps = np.diff(np.sort(enter[day0]))
                gaps = gaps[gaps > 0]
                self._headway[int(li)] = float(self._minutes(np.median(gaps))) if gaps.size else 0.0

    def first_train(self, line: int, ready_T: int) -> int:
        """路線 ``line`` で ``ready_T`` 以降に最初にホームへ入る便(来た電車=本人は便を選ばない)。無ければ −1。"""
        tab = self._line_tab.get(int(line))
        if tab is None:
            return -1
        ent, order = tab
        k = int(np.searchsorted(ent, int(ready_T), side="left"))
        return int(order[k]) if k < ent.size else -1

    # ------------------------------------------------------------------ 日の頭
    def relay_day(self, d: int) -> None:
        """``d`` 日目の約束を器に張る(W20 の週の表・暦・日番号と、保存した見積りから決まる=再開でも同じ)。"""
        d = int(d)
        s = self.cal_store
        m = self.cal_meter
        if m["cur"] and int(m["cur"].get("day", -1)) != d:
            m["days"][str(int(m["cur"]["day"]))] = self._summary(m["cur"])
        self._rebuild_lines()
        cal = self.calendar
        dt = cal.date_of_day(d)
        twd = int(cal.table_weekday(d))
        wk_raw = (dt - _CS.WEEK0_MONDAY).days // _CS.N_DAYS
        wk = wk_raw % max(int(self.table.n_weeks), 1)
        n = self.n
        mt = min(n, int(self.table.n))
        col = {}
        for c, v in self.table.cols.items():
            a = np.full(n, -1 if c not in ("commit", "place_kind", "recurrence", "certainty") else 0, dtype=np.int64)
            a[:mt] = np.asarray(v)[:mt, wk, twd]
            col[c] = a
        found = np.zeros(n, dtype=bool)
        found[:mt] = np.asarray(self.table.found)[:mt]
        T0 = d * self.tpd
        # ---- 前の日の行き来の途中の体(夜をまたぐ勤務・帰りの途中・域外からの到着の予約)。続きは世界と本人が進め、器の
        # その体の欄は持ち越す。今日の約束は「途中の後」に回す(pend_*=家に着いたら張る)----
        inflight = (np.isin(s["phase"], _INFLIGHT_PHASES) | (s["walk_kind"] > 0) | (s["arr_T"] >= 0)
                    | s["walk_pending"])
        prev_end = s["end_T"].copy()
        # ---- 管理する体(時刻つきの勤務の約束・CA4)----
        commit = col["commit"]
        work = commit == _CS.COMMIT_WORK
        start = col["start_min"]
        end = col["end_min"]
        pk = col["place_kind"]
        bad, _pairs = validate_commitments(np.where(work, start, 0), np.where(work, end, 1),
                                           place_kind=np.where(work, pk, 1))
        broken = work & bad
        home_out = s["home_cell"] < 0
        place_out = pk == _PK_OUTSIDE
        place_home = pk == _PK_HOME
        absent = self._absent(d)
        ex = np.full(n, -1, dtype=np.int64)
        ex[~found] = EX_NOT_IN_TABLE
        ex[found & (commit == 0)] = EX_NO
        ex[found & (commit == _CS.COMMIT_SCHOOL)] = EX_SCHOOL
        ex[(ex < 0) & broken] = EX_BROKEN
        ex[(ex < 0) & work & place_home] = EX_HOME
        ex[(ex < 0) & work & place_out & home_out] = EX_OUTSIDE
        ex[(ex < 0) & work & absent] = EX_ABSENT
        managed = (ex < 0) & work
        route = np.zeros(n, dtype=np.int8)
        route[managed & home_out & ~place_out] = RT_IN
        route[managed & ~home_out & place_out] = RT_OUT
        route[managed & ~home_out & ~place_out] = RT_LOCAL
        overlap = managed & (prev_end >= 0) & (prev_end > T0 + self._steps(start))
        cell = col["target_cell"]
        blank = managed & ~place_out & (cell < 0)
        today = {
            "route": route, "day": np.full(n, d, dtype=np.int64), "day_T0": np.full(n, T0, dtype=np.int64),
            "start_T": T0 + self._steps(start), "end_T": T0 + self._steps(end), "place_kind": pk,
            "place_cell": np.where(~place_out, np.where(blank, s["exit_cell"], cell), -1),
            "lead": np.maximum(col["lead_min"], 0),
        }
        # ---- 器を張る: 途中でない体は今日の約束を張る・途中の体は今日の約束を pend_* に控える ----
        fresh = ~inflight
        put = managed & fresh
        for k, v in today.items():  # 逐次ループ宣言: 欄の数ぶん(8)
            s[k][put] = np.asarray(v)[put].astype(s[k].dtype)
            s["pend_" + k][:] = np.where(managed & inflight, np.asarray(v), -1).astype(s["pend_" + k].dtype)
        clear = fresh & ~managed
        s["route"][clear] = RT_NONE
        s["start_T"][clear] = -1
        s["end_T"][clear] = -1
        s["place_kind"][clear] = 0
        s["place_cell"][clear] = -1
        s["managed"][:] = managed
        for k in ("go_T", "move_T", "arrive_T", "back_T", "home_T", "plat_T", "plan_T"):
            s[k][fresh] = -1
        s["wait_go"][fresh] = 0.0
        s["impossible"][fresh] = False
        s["retries"][:] = 0
        s["switches"][:] = 0
        s["away_n"][:] = 0
        s["back_n"][:] = 0
        s["today_pending"][:] = managed & inflight
        s["phase"][fresh] = np.where(managed[fresh], PH_BEFORE, PH_NONE).astype(np.int8)
        s["next_T"][fresh] = -1
        s["next_ref"][fresh] = -1
        s["next_trig"][fresh] = -1
        s["watch"][:] = managed | inflight
        # ---- 計器(その日)----
        exc = {EXCLUDE_REASONS[k]: int(np.count_nonzero(ex == k)) for k in range(len(EXCLUDE_REASONS))}
        m["cur"] = {
            "day": d, "date": dt.isoformat(), "weekday": int(dt.weekday()), "table_weekday": twd, "week": int(wk),
            "week_wrapped": bool(wk != wk_raw), "agents": int(n),
            "managed": int(managed.sum()),
            "by_route": {ROUTES[k]: int(np.count_nonzero(route == k)) for k in (RT_IN, RT_OUT, RT_LOCAL)},
            "by_placement": {PLACEMENTS[k]: int(np.count_nonzero(managed & (s["placement"] == k)))
                             for k in range(len(PLACEMENTS))},
            "excluded": exc, "rejected_broken": int(broken.sum()), "overlap_warnings": int(overlap.sum()),
            "blank_place_cell": int(blank.sum()), "carried_over": int((managed & inflight).sum()),
            "inflight_at_head": int(inflight.sum()),
            "suppressed_w17": {"arrive": 0, "depart": 0},
            "decisions": {"total": 0, "plan": 0, "continue": 0, "deliberate": 0, "other": 0,
                          "by_trigger": {t: 0 for t in TRIGGERS}, "precise": 0, "approx": 0, "numbers": {},
                          "asleep_wait_steps": 0, "riding_wait_steps": 0},
            "plan_match": [None] * (MINUTES_PER_DAY // MINUTES_PER_HOUR),
            "at_rate15": [None] * (MINUTES_PER_DAY // SLOT_MIN),
            "plan_match_phase": [None] * (MINUTES_PER_DAY // MINUTES_PER_HOUR),
            "at_rate15_phase": [None] * (MINUTES_PER_DAY // SLOT_MIN),
            "left_at_work": 0, "back_to_work": 0, "reminders_set": 0, "reminders_blank": 0, "clock_reads": 0,
            "trips": {k: [] for k in ("agent", "trip", "T", "number", "source", "trigger", "precise", "n_cand")},
            "inbound": [],
            "interrupts": 0, "interrupt_by": {}, "interrupt_result": {}, "retries_capped": 0, "conversing_waits": 0,
            "no_train": 0, "unreachable": 0, "alarm_rang_asleep": 0,
            "arrivals_cancelled": 0, "go_trips": [], "back_trips": [],
            "w17_ref": self._w17_ref(managed, start, absent, T0),
        }
        # ---- 見積り(初めて管理する体だけ)と、本人が置く機会(AT1)=置いた記録を参照に持つ ----
        self._init_estimates(put & ~s["est_init"])
        self._set_reminders(np.flatnonzero(put), T0)

    def _absent(self, d: int) -> np.ndarray:
        """出勤率のくじ(CA5=判断モデルまでのつなぎ・BR-ATTENDANCE-LOTTERY)でその日来ない体。計画実行層と同じ口・同じ鍵で
        引き直す(計画実行層の表の欄は読まない=その欄は計器の側)。"""
        pr = self.presence
        out = np.zeros(self.n, dtype=bool)
        fn = getattr(pr, "_attendance_absent", None)
        if fn is None:
            return out
        got = np.asarray(fn(pr._kind, pr._agent_key, float(pr.attendance_rate), day=int(d)), dtype=bool)
        out[: min(self.n, got.size)] = got[: self.n]
        return out

    def _w17_ref(self, managed: np.ndarray, start_min: np.ndarray, absent: np.ndarray, T0: int) -> dict[str, Any]:
        """参考: W17 の計画実行層なら最初の在圏ブロックの始まりと、その到着の便(E1=間に合う最も遅い便・散らす前)の時刻と、
        約束の始まりの差(家が域外の体・W17 の週次表から同じ読み口で引き直す=計画実行層の表の欄は読まない)。"""
        from shibuya.engine.presence import PlanBlocks

        pr = self.presence
        weekly = getattr(pr, "weekly", None)
        if weekly is None:
            return {"n": 0}
        m = min(self.n, int(weekly.n_agents))
        home_out = (self.cal_store["home_cell"] < 0)[:m]
        ex = np.asarray(absent, dtype=bool)[:m]
        blocks = PlanBlocks.from_weekly(weekly, int(pr.day_index), home_out, mode=str(pr.mode), exclude=ex,
                                        derive_rule=str(pr.derive_rule))
        if blocks.n_blocks == 0:
            return {"n": 0}
        has = np.zeros(self.n, dtype=bool)
        has[:m] = np.asarray(blocks.blocks_per_agent())[:m] > 0
        sel = np.flatnonzero(managed & has & (self.cal_store["home_cell"] < 0))
        if sel.size == 0:
            return {"n": 0}
        first = np.asarray(blocks.offset)[sel]
        b_start = np.asarray(blocks.start, dtype=np.int64)[first]
        out: dict[str, Any] = {
            "n": int(sel.size), "block_start_hist15": _CS._hist15(b_start),
            "block_start_minus_start": _CS._stats(b_start - np.asarray(start_min, dtype=np.float64)[sel])}
        trains = np.asarray(pr._assign_trains(sel, b_start), dtype=np.int64)
        rail = self.rail
        ok = trains >= 0
        if rail is not None and bool(ok.any()):
            ent = np.asarray(rail.enter_tick, dtype=np.int64)[trains[ok]]
            a_min = self._minutes(ent - int(T0))
            out["e1_arrive_hist15"] = _CS._hist15(a_min.astype(np.int64))
            out["e1_arrive_minus_start"] = _CS._stats(a_min - np.asarray(start_min, dtype=np.float64)[sel[ok]])
        return out

    def _init_estimates(self, mask: np.ndarray) -> None:
        """見積りの初期値(AT2=ランの前に積んだ経験=実際の道のり)。舞台の中は歩行グラフの節の数・域外は W20 の片道の時間から
        舞台の中の歩きを引いた時間・幅は路線の便の間隔(待ちの最大)。"""
        s = self.cal_store
        ids = np.flatnonzero(mask)
        if ids.size == 0:
            return
        world = self.world
        rep = np.asarray(world.assets.cell_rep_node, dtype=np.int64)

        def node_of(c: np.ndarray) -> np.ndarray:
            c = np.asarray(c, dtype=np.int64)
            return np.where((c >= 0) & (c < rep.size), rep[np.clip(c, 0, max(rep.size - 1, 0))], -1)

        route = s["route"][ids]
        src = np.full(ids.size, -1, dtype=np.int64)
        dst = np.full(ids.size, -1, dtype=np.int64)
        rin = route == RT_IN
        src[rin] = node_of(s["arrive_cell"][ids[rin]])
        dst[rin] = node_of(s["place_cell"][ids[rin]])
        rout = route == RT_OUT
        src[rout] = node_of(s["home_cell"][ids[rout]])
        dst[rout] = node_of(s["arrive_cell"][ids[rout]])
        rloc = route == RT_LOCAL
        src[rloc] = node_of(s["home_cell"][ids[rloc]])
        dst[rloc] = node_of(s["place_cell"][ids[rloc]])
        steps = route_steps(world, src, dst)
        walk = np.where(steps >= 0, self._minutes(hop_walk_steps(steps, self.hop_steps, ids)), 0.0)
        lead = s["lead"][ids].astype(np.float64)
        d_out = np.where(rloc, 0.0, np.maximum(lead - walk, 0.0))
        head = np.array([self._headway.get(int(li), 0.0) if li >= 0 else 0.0 for li in s["line"][ids].tolist()],
                        dtype=np.float64)  # 逐次ループ宣言: 体の数ぶんの辞書引き(初期化の 1 回だけ)
        head = np.where(rloc, 0.0, head)
        lo = d_out + walk
        hi = lo + head
        s["walk_go"][ids] = np.rint(walk).astype(np.int16)
        s["d_out"][ids] = np.rint(d_out).astype(np.int16)
        s["est0_lo"][ids] = lo
        s["est0_hi"][ids] = hi
        s["est_lo"][ids] = lo
        s["est_hi"][ids] = hi
        s["est_init"][ids] = True
        cur = self.cal_meter.get("cur") or {}
        if cur:
            cur["unreachable"] = int(cur.get("unreachable", 0)) + int(np.count_nonzero((steps < 0) & (route != RT_NONE)))

    def _prediction(self, a: int, trip: int) -> Prediction:
        s = self.cal_store
        t0 = int(s["day_T0"][a])
        lo, hi = float(s["est_lo"][a]), float(s["est_hi"][a])
        pk = int(s["place_kind"][a])
        place = W20_PLACE_WORDS[pk] if 0 < pk < len(W20_PLACE_WORDS) else "勤め先"
        return Prediction(
            trip=TRIPS[trip], kind="勤務",
            start_min=int(self._minutes(int(s["start_T"][a]) - t0)), end_min=int(self._minutes(int(s["end_T"][a]) - t0)),
            place=place, est_lo_min=lo, est_hi_min=hi,
            est_words=f"{duration_words(lo)}〜{duration_words(hi)}", margin_min=int(s["margin"][a]),
            look_interval_min=LOOK_INTERVAL_MIN)

    def _set_reminders(self, ids: np.ndarray, T0: int) -> None:
        """本人が置く機会(AT1): アプリとアラームは、その日の頭に本人が予定を見て置く時刻=判断の口(``choose``)に出し、答えの
        「次に見る時刻」(``Choice.continuous``)を通知・アラームの時刻にする(すぐ出る答えならその日の頭)。答えに時刻が無い口
        では空欄(機会を置かない=0 時にしない)。手帳はその日の最初の刻み(起きていれば見る)・頭の中は時計を見る習慣の位相。
        どれも置いた記録の id を参照に持つ。"""
        s = self.cal_store
        if ids.size == 0:
            return
        cur = self.cal_meter["cur"]
        pl = s["placement"][ids]
        T_head = T0 + self._steps(s["look_phase"][ids])
        nxt = np.where(pl == PL_PLANNER, T0, T_head).astype(np.int64)
        trig = np.select([pl == PL_APP, pl == PL_ALARM, pl == PL_PLANNER], [TR_APP, TR_ALARM, TR_PLANNER], TR_HEAD)
        refs = s["habit_ref"][ids].astype(np.int64).copy()
        plan_T = np.full(ids.size, -1, dtype=np.int64)
        st = np.asarray(self.agents.registry.transit_state)
        t_ns = int(T0) * self.step_seconds * NS_PER_SECOND
        for j, a in enumerate(ids.tolist()):  # 逐次ループ宣言: その日に通知とアラームを置く体の数ぶん(日の頭に 1 回)
            if int(pl[j]) not in (PL_APP, PL_ALARM):
                continue
            pred = self._prediction(int(a), TRIP_GO)
            obs = Observation(time_min=0, precise=True, words=_hhmm(0), where="域外" if int(st[a]) == 2 else "舞台の中",
                              trigger="予定を置く")
            ctx = DecisionContext(agent_id=int(a), step=int(T0), t_ns=t_ns, wake_class=-1, condition=-1, cell=-1,
                                  call_id=f"{_DECIDE_STEP_KEY}-set:{int(T0)}:{int(a)}", percept=obs, prediction=pred)
            cands = commute_candidates(pred)
            ch = self.port.choose(ctx, cands)
            cont = dict(ch.continuous or {})
            src = next((c.source for c in cands if c.id == ch.candidate_id), None)
            refs[j] = self._new_id()
            if "planned_min" in cont:
                plan_T[j] = T0 + int(self._steps(float(cont["planned_min"])))
            if src == SOURCE_PLAN:
                nxt[j] = T0  # もう出る時刻=その日の頭に鳴らす
                cur["reminders_set"] += 1
            elif float(cont.get("next_look_min", -1.0)) >= 0:
                nxt[j] = T0 + int(self._steps(float(cont["next_look_min"])))
                cur["reminders_set"] += 1
            else:
                nxt[j] = -1  # 口の答えに時刻が無い=置かない(空欄)
                cur["reminders_blank"] += 1
        s["plan_T"][ids] = plan_T
        s["next_T"][ids] = nxt
        s["next_trig"][ids] = trig.astype(np.int8)
        s["next_ref"][ids] = refs

    # ------------------------------------------------------------------ 刻み
    def step(self, T: int) -> None:
        """刻み ``T`` の出入り(計画実行層の後・同じ系)。順: 連続性の検査 → 控え → 勤務中に舞台を出た体の再提示 → 域外からの
        到着 → 歩きの続き → 機会 → この刻みに置いた到着(〔検収 L1〕同じ刻みに着く)→ 計器。"""
        self.walk_started_now = np.empty(0, dtype=np.int64)
        T = int(T)
        s = self.cal_store
        if not self.cal_meter["cur"]:
            return
        r = self.agents.registry
        self.cal_meter["last_T"] = T
        st = np.asarray(r.transit_state).astype(np.int8)
        self._check_continuity(st)
        s["st_prev"][:] = st
        s["bl_prev"][:] = np.asarray(r.board_line) >= 0
        s["flag_cross"][:] = False
        s["flag_arrive"][:] = False
        s["flag_rode"][:] = False
        started: list[np.ndarray] = []
        self._left_at_work(T, st)
        self._arrivals_due(T, started)
        self._walks(T)
        self._pending_walks(T, started)
        self._opportunities(T, started)
        self._arrivals_due(T, started)  # 〔検収 L1〕この刻みの判断や退出で置いた到着(便が今ホームに入る・域外の時間 0)を同じ刻みに
        self._sample(T)
        if started:
            self.walk_started_now = np.unique(np.concatenate(started))

    def _check_continuity(self, st: np.ndarray) -> None:
        """体は消えず急に現れない(10-12 §1-3 の 1): 管理する体の在圏の変化を直前の刻みの控えと比べる。"""
        s = self.cal_store
        w = s["watch"]
        prev = s["st_prev"]
        known = prev >= 0
        out = w & known & (st == 2) & (prev != 2)
        if out.any():
            # 説明がつく退出は 2 つだけ: 発車した電車に乗って出た(鉄道の発車の知らせ)・境界を歩いて越えた(この層)
            ok = s["flag_rode"] | s["flag_cross"]
            bad = out & ~ok
            ch = self.cal_meter["checks"]
            ch["exits_unexplained"] += int(bad.sum())
            ch["exits_during_walk"] += int((bad & (s["walk_kind"] > 0)).sum())
        back = w & known & (st == 0) & (prev == 2)
        if back.any():
            bad_in = back & ~s["flag_arrive"]
            self.cal_meter["checks"]["appear_unexplained"] += int(bad_in.sum())

    def _left_at_work(self, T: int, st: np.ndarray) -> None:
        """〔検収 H1〕約束の場所(舞台の中)の段の体が、本人の行為(乗車など)で舞台を出た。約束が続いている間は、歩きが途切れた
        ときと同じ規則で本人の次の機会(時計を見る習慣の 30 分後・1 日 8 回まで)に出入りをもう一度出す=戻るかは本人の判断。
        上限を超えた体は終わりの時刻の機会で帰りを決める(つなぎ DOC-ca1b-left-at-work)。"""
        s = self.cal_store
        away = s["watch"] & (s["phase"] == PH_AT) & (st == 2) & (s["place_kind"] != _PK_OUTSIDE)
        ids = np.flatnonzero(away & (s["end_T"] > T))
        if ids.size == 0:
            return
        cur = self.cal_meter["cur"]
        cur["left_at_work"] += int(ids.size)
        s["away_n"][ids] += 1
        s["retries"][ids] += 1
        self._phase(ids, PH_BEFORE)
        ok = ids[s["retries"][ids] <= MAX_RETRIES]
        cap = ids[s["retries"][ids] > MAX_RETRIES]
        if ok.size:
            s["next_T"][ok] = T + int(self._steps(LOOK_INTERVAL_MIN))
            s["next_trig"][ok] = TR_RETRY
            s["next_ref"][ok] = s["habit_ref"][ok]
        if cap.size:
            cur["retries_capped"] += int(cap.size)
            s["next_T"][cap] = s["end_T"][cap]
            s["next_trig"][cap] = TR_END
            s["next_ref"][cap] = -1

    def _at_work(self, ids: np.ndarray, T: int) -> None:
        """約束の場所に着いた: 初めてなら行きの時間を記録して見積りを直す・出た後に戻ったなら戻った数だけ数える。"""
        s = self.cal_store
        first = ids[s["arrive_T"][ids] < 0]
        again = ids[s["arrive_T"][ids] >= 0]
        s["arrive_T"][first] = T
        self._phase(ids, PH_AT)
        self._finish_go(first, T)
        if again.size:
            self.cal_meter["cur"]["back_to_work"] += int(again.size)
            s["back_n"][again] += 1
        self._schedule_end(ids, T)

    def _phase(self, ids: np.ndarray, ph: int) -> None:
        s = self.cal_store
        if ids.size:
            s["switches"][ids] += 1
            s["phase"][ids] = np.int8(ph)

    # ------------------------------------------------------------------ 域外からの到着
    def _arrivals_due(self, T: int, started: list[np.ndarray]) -> None:
        s = self.cal_store
        due = np.flatnonzero((s["arr_T"] >= 0) & (s["arr_T"] <= T))
        if due.size == 0:
            return
        cur = self.cal_meter["cur"]
        trip = s["arr_trip"][due].astype(np.int64)
        cell = s["arr_cell"][due].astype(np.int64)
        st = np.asarray(self.agents.registry.transit_state)[due]
        # 域外の約束の場所に着いた(行き)・域外の家に着いた(帰り)=粗い域外
        far = cell < 0
        if far.any():
            f = due[far]
            go = trip[far] == TRIP_GO
            self._at_work(f[go], T)
            s["home_T"][f[~go]] = T
            self._phase(f[~go], PH_HOME)
            self._after_home(f[~go], T)
        inn = ~far
        if inn.any():
            ids, cells, tr = due[inn], cell[inn], trip[inn]
            outside = st[inn] == 2
            # 間に合う便を選んでいないか(到着の便=出発+域外の時間より後に最初にホームへ入る便)
            trains = s["arr_train"][ids]
            ready = s["arr_ready_T"][ids]
            ch = self.cal_meter["checks"]
            for j in np.flatnonzero(trains >= 0).tolist():  # 逐次ループ宣言: この刻みに着く体の数ぶん
                ch["inbound_checked"] += 1
                cur["inbound"].append([int(ids[j]), int(ready[j]), int(trains[j]), int(s["line"][ids[j]]), int(T)])
                want = first_entering_train(self.rail, int(s["line"][ids[j]]), int(ready[j]))
                if want != int(trains[j]):
                    ch["selected_trains"] += 1
            go_in = ids[outside]
            if go_in.size:
                R.rail_arrive(self.agents, self.world, go_in, cells[outside])
                from shibuya.engine.presence import FLAG_ARRIVED

                R.set_plan_state(self.agents, go_in, flags_set=FLAG_ARRIVED)
                s["flag_arrive"][go_in] = True
                wait = self._minutes(np.maximum(T - ready[outside], 0))
                g = tr[outside] == TRIP_GO
                s["wait_go"][go_in[g]] += wait[g].astype(np.float32)
            cancel = ids[~outside]
            cur["arrivals_cancelled"] += int(cancel.size)
            walkers = ids  # 着いた体も、先に舞台に居た体も、今いる所から行き先へ歩く
            go = tr == TRIP_GO
            self._start_walk(walkers[go], s["place_cell"][walkers[go]], WK_PLACE, TRIP_GO, T, started)
            self._start_walk(walkers[~go], s["home_cell"][walkers[~go]], WK_HOME, TRIP_BACK, T, started)
        for k in ("arr_T", "arr_ready_T", "arr_train"):
            s[k][due] = -1
        s["arr_cell"][due] = -1
        s["arr_trip"][due] = -1

    # ------------------------------------------------------------------ 歩き
    def _start_walk(self, ids: np.ndarray, cells: np.ndarray, kind: int, trip: int, T: int,
                    started: list[np.ndarray]) -> None:
        """行き先のセルへ歩き出す(着いていればその場で着いた扱い・会話中は会話の後・歩けなければ動けない)。"""
        s = self.cal_store
        if ids.size == 0:
            return
        ids = np.asarray(ids, dtype=np.int64)
        cells = np.asarray(cells, dtype=np.int64)
        self._release(ids, T)
        walk_m, here_m, busy_m, fail_m = R.begin_walk_to(self.agents, self.world, ids, cells)
        w = ids[walk_m]
        if w.size:
            s["walk_kind"][w] = np.int8(kind)
            s["walk_cell"][w] = cells[walk_m].astype(np.int32)
            s["walk_node"][w] = np.asarray(self.agents.registry.target_node)[w].astype(np.int32)
            s["walk_trip"][w] = np.int8(trip)
            s["walk_pending"][w] = False
            if kind == WK_LEAVE_GATE:
                self._phase(w, PH_GO_LEAVE if trip == TRIP_GO else PH_BACK_LEAVE)
            else:
                self._phase(w, PH_GO_WALK if kind == WK_PLACE else PH_BACK_WALK)
            started.append(w)
        b = ids[busy_m]
        if b.size:
            s["walk_pending"][b] = True
            s["walk_kind"][b] = WK_NONE
            s["walk_cell"][b] = cells[busy_m].astype(np.int32)
            s["walk_trip"][b] = np.int8(trip)
            s["walk_node"][b] = np.int32(kind)  # 始められなかった歩きの種類を控える(始めるときに読み直す)
            self.cal_meter["cur"]["conversing_waits"] += int(b.size)
        h = ids[here_m]
        if h.size:
            s["walk_pending"][h] = False
            self._arrived(h, kind, trip, T)
        f = ids[fail_m]
        if f.size:
            s["walk_pending"][f] = False
            self.cal_meter["cur"]["unreachable"] += int(f.size)
            self._phase(f, PH_STRANDED)  # 歩けない体(経路が無い・在圏でない)は動けない=そこに居続ける

    def _release(self, ids: np.ndarray, T: int) -> None:
        """本人が出ると決めた体の在席と列を解く(計画実行層の退出と同じ口)。"""
        r = self.agents.registry
        shop = ids[np.asarray(r.poi_ref)[ids] >= 0]
        if shop.size:
            R.release_indoor(self.agents, shop)
        q = ids[np.asarray(r.queue_poi)[ids] >= 0]
        if q.size:
            R.balk_queue(self.agents, q, int(T))

    def _start_leave(self, ids: np.ndarray, trip: int, T: int, started: list[np.ndarray]) -> None:
        """舞台を出る: 自分の路線のホームへ歩き、来た電車に乗る(``begin_exit_walk``)。路線が無い体は駅の口へ歩いて境界を越える。
        会話中の体は会話の後(計画実行層の退出の繰り延べと同じ=片側だけ会話が残らない)。"""
        s = self.cal_store
        if ids.size == 0:
            return
        ids = np.asarray(ids, dtype=np.int64)
        talking = np.asarray(self.agents.registry.activity)[ids] == int(Activity.CONVERSING)
        if talking.any():
            b = ids[talking]
            s["walk_pending"][b] = True
            s["walk_kind"][b] = WK_NONE
            s["walk_cell"][b] = -1
            s["walk_trip"][b] = np.int8(trip)
            s["walk_node"][b] = np.int32(WK_LEAVE_RAIL)  # 始められなかった歩きの種類を控える(始めるときに読み直す)
            self.cal_meter["cur"]["conversing_waits"] += int(b.size)
            ids = ids[~talking]
            if ids.size == 0:
                return
        line = s["line"][ids].astype(np.int64)
        rail_on = self.rail is not None and bool(getattr(self.rail, "active", False))
        rl = ids[(line >= 0) & rail_on]
        gate = ids[(line < 0) | (not rail_on)]
        if rl.size:
            self._release(rl, T)
            walk_m, wait_m, fail_m = R.begin_exit_walk(self.agents, self.world, self.rail, rl, s["line"][rl], int(T))
            ok = rl[walk_m | wait_m]
            if ok.size:
                s["walk_kind"][ok] = WK_LEAVE_RAIL
                s["walk_trip"][ok] = np.int8(trip)
                s["walk_node"][ok] = -1
                s["walk_cell"][ok] = -1
                s["walk_pending"][ok] = False
                s["plat_T"][ok] = -1
                R.set_plan_state(self.agents, ok, flags_set=R.EXIT_WALK_FLAG)
                self._phase(ok, PH_GO_LEAVE if trip == TRIP_GO else PH_BACK_LEAVE)
                started.append(rl[walk_m])
            gate = np.concatenate([gate, rl[fail_m]])  # 便もホームも無い路線=駅の口へ歩いて境界を越える
        if gate.size:
            self._start_walk(gate, s["exit_cell"][gate], WK_LEAVE_GATE, trip, T, started)

    def _pending_walks(self, T: int, started: list[np.ndarray]) -> None:
        """会話の後に始める歩き(会話が終わった体から)。"""
        s = self.cal_store
        p = np.flatnonzero(s["walk_pending"])
        if p.size == 0:
            return
        act = np.asarray(self.agents.registry.activity)[p]
        ready = p[act != int(Activity.CONVERSING)]
        if ready.size == 0:
            return
        kinds = s["walk_node"][ready].astype(np.int64)
        s["walk_pending"][ready] = False
        for k in (WK_PLACE, WK_HOME, WK_LEAVE_RAIL, WK_LEAVE_GATE):  # 逐次ループ宣言: 歩きの種類の数ぶん(4)
            sel = ready[kinds == k]
            if sel.size == 0:
                continue
            trips = s["walk_trip"][sel].astype(np.int64)
            for tp in (TRIP_GO, TRIP_BACK):  # 逐次ループ宣言: 行きと帰り(2)
                ss = sel[trips == tp]
                if ss.size == 0:
                    continue
                if k == WK_LEAVE_RAIL:
                    self._start_leave(ss, tp, T, started)
                else:
                    self._start_walk(ss, s["walk_cell"][ss], k, tp, T, started)

    def _walks(self, T: int) -> None:
        """歩きの続き: 着いた(場所に着く・家に着く・境界を越える)/電車で出た/途切れた(その場に居続け、本人の次の機会へ)。"""
        s = self.cal_store
        wk = s["walk_kind"]
        ids = np.flatnonzero(wk > 0)
        if ids.size == 0:
            return
        r = self.agents.registry
        st = np.asarray(r.transit_state)[ids]
        kind = wk[ids].astype(np.int64)
        trip = s["walk_trip"][ids].astype(np.int64)
        node = np.asarray(r.node, dtype=np.int64)[ids]
        dest = s["walk_node"][ids].astype(np.int64)
        tgt = np.asarray(r.target_node, dtype=np.int64)[ids]
        act = np.asarray(r.activity)[ids]
        bl = np.asarray(r.board_line)[ids]
        bs = np.asarray(r.board_since)[ids]
        rail = kind == WK_LEAVE_RAIL
        # ---- 電車で出る流れ ----
        if rail.any():
            ri = ids[rail]
            rst = st[rail]
            first_wait = rail & (bs >= 0)
            fw = ids[first_wait]
            fw = fw[s["plat_T"][fw] < 0]
            s["plat_T"][fw] = np.asarray(r.board_since)[fw].astype(np.int64)
            left = ri[rst == 2]
            if left.size:
                R.set_plan_state(self.agents, left, flags_clear=R.EXIT_WALK_FLAG)
                self._left_area(left, T)
            lost = ri[(rst == 0) & (bl[rail] < 0)]
            if lost.size:
                R.set_plan_state(self.agents, lost, flags_clear=R.EXIT_WALK_FLAG)
                self._interrupt(lost, T)
        # ---- 歩いて行き先へ(場所・家・境界)----
        walk = ~rail
        if walk.any():
            wi = ids[walk]
            arrived = walk & (st == 0) & (node == dest)
            moving = (act == int(Activity.MOVING)) & (tgt == dest)
            lost = walk & ~arrived & ((st != 0) | ~moving)
            for k in (WK_PLACE, WK_HOME, WK_LEAVE_GATE):  # 逐次ループ宣言: 歩きの種類の数ぶん(3)
                for tp in (TRIP_GO, TRIP_BACK):  # 逐次ループ宣言: 行きと帰り(2)
                    sel = ids[arrived & (kind == k) & (trip == tp)]
                    if sel.size:
                        self._arrived(sel, k, tp, T)
            gone = ids[lost]
            if gone.size:
                self._interrupt(gone, T)
            del wi

    def _arrived(self, ids: np.ndarray, kind: int, trip: int, T: int) -> None:
        s = self.cal_store
        s["walk_kind"][ids] = WK_NONE
        s["walk_node"][ids] = -1
        s["walk_cell"][ids] = -1
        if kind == WK_PLACE:
            self._at_work(ids, T)
        elif kind == WK_HOME:
            s["home_T"][ids] = T
            self._phase(ids, PH_HOME)
            self._after_home(ids, T)
        elif kind == WK_LEAVE_GATE:
            # 境界を歩いて越える(非鉄道の方面=駅の口を境界の代わり=仮採用)。域外の置き場へ移す口は rail_depart と同じ書き方。
            R.rail_depart(self.agents, ids, np.full(ids.size, -1, dtype=np.int64))
            s["flag_cross"][ids] = True
            self._left_area(ids, T)

    def _left_area(self, ids: np.ndarray, T: int) -> None:
        """舞台を出た(電車の発車か境界を越えた)。行き=域外の約束の場所へ・帰り=域外の家へ(粗い域外の時間の後に着く)。"""
        s = self.cal_store
        trip = s["walk_trip"][ids].astype(np.int64)
        s["walk_kind"][ids] = WK_NONE
        s["walk_node"][ids] = -1
        s["walk_cell"][ids] = -1
        plat = s["plat_T"][ids]
        wait = np.where(plat >= 0, self._minutes(np.maximum(T - 1 - plat, 0)), 0.0)
        go = trip == TRIP_GO
        s["wait_go"][ids[go]] += wait[go].astype(np.float32)
        arr = T + self._steps(s["d_out"][ids])
        s["arr_T"][ids] = arr
        s["arr_ready_T"][ids] = arr
        s["arr_train"][ids] = -1
        s["arr_cell"][ids] = -1
        s["arr_trip"][ids] = trip.astype(np.int8)
        self._phase(ids[go], PH_GO_OUTSIDE)
        self._phase(ids[~go], PH_BACK_OUTSIDE)

    def _interrupt(self, ids: np.ndarray, T: int) -> None:
        """歩きが途切れた(本人がほかの行為を選んだ・待ちの打ち切り・経路の途切れ)。体は消さず、その場に居続ける=本人の次の
        機会(時計を見る習慣の次の時刻)に出入りをもう一度出す(E4 を外す)。上限を超えたら動けないと数える。"""
        s = self.cal_store
        cur = self.cal_meter["cur"]
        trip = s["walk_trip"][ids].astype(np.int64)
        by = cur["interrupt_by"]
        for k, c in zip(*np.unique(s["walk_kind"][ids].astype(np.int64), return_counts=True)):  # 逐次: 歩きの種類(≤ 4)
            by[WALK_WORDS[int(k)]] = int(by.get(WALK_WORDS[int(k)], 0)) + int(c)
        res = cur["interrupt_result"]
        lr = np.asarray(self.agents.registry.last_result).astype(np.int64)[ids]
        for k, c in zip(*np.unique(lr, return_counts=True)):  # 逐次: 直前の結果の種類(≤ 25)
            res[str(int(k))] = int(res.get(str(int(k)), 0)) + int(c)
        s["walk_kind"][ids] = WK_NONE
        s["walk_node"][ids] = -1
        s["walk_cell"][ids] = -1
        cur["interrupts"] += int(ids.size)
        s["retries"][ids] += 1
        cap = ids[s["retries"][ids] > MAX_RETRIES]
        ok = ids[s["retries"][ids] <= MAX_RETRIES]
        if cap.size:
            cur["retries_capped"] += int(cap.size)
            self._phase(cap, PH_STRANDED)
            s["next_T"][cap] = -1
        if ok.size:
            tr = trip[s["retries"][ids] <= MAX_RETRIES]
            self._phase(ok[tr == TRIP_GO], PH_BEFORE)
            self._phase(ok[tr == TRIP_BACK], PH_AT)
            s["next_T"][ok] = T + int(self._steps(LOOK_INTERVAL_MIN))
            s["next_trig"][ok] = TR_RETRY
            s["next_ref"][ok] = s["habit_ref"][ok]

    def _schedule_end(self, ids: np.ndarray, T: int) -> None:
        """約束の場所に着いた体の帰りの機会=約束の終わりの時刻(職場の時計=分単位・つなぎ DOC-ca1b-end-notice)。"""
        s = self.cal_store
        if ids.size == 0:
            return
        s["next_T"][ids] = np.maximum(s["end_T"][ids], T)
        s["next_trig"][ids] = TR_END
        s["next_ref"][ids] = -1

    def _finish_go(self, ids: np.ndarray, T: int) -> None:
        """行きが終わった: 実際の時間と実感の時間を記録し、見積りを直近の平均で作り直す(AT2)。"""
        s = self.cal_store
        cur = self.cal_meter["cur"]
        for a in ids.tolist():  # 逐次ループ宣言: この刻みに着いた体の数ぶん
            mv = int(s["move_T"][a])
            if mv < 0:
                continue
            actual = float(self._minutes(T - mv))
            wait = float(s["wait_go"][a])
            felt = felt_minutes(actual, wait)
            init = Estimate(float(s["est0_lo"][a]), float(s["est0_hi"][a]))
            est_c = (float(s["est_lo"][a]) + float(s["est_hi"][a])) / 2.0
            cur["go_trips"].append([int(a), int(s["route"][a]), round(actual, 3), round(wait, 3), round(felt, 3),
                                    round(est_c, 3), int(s["placement"][a])])
            k = int(s["recent_n"][a]) % RECENT_K
            s["recent"][a, k] = np.float32(felt)
            s["recent_n"][a] = np.int8(min(int(s["recent_n"][a]) + 1, np.iinfo(np.int8).max))
            e = update_estimate(s["recent"][a].tolist(), init)
            s["est_lo"][a] = np.float32(e.lo)
            s["est_hi"][a] = np.float32(e.hi)

    def _after_home(self, ids: np.ndarray, T: int) -> None:
        """家に着いた。前の日の行き来の続きで今日の約束が残っていれば、今日の出発の前へ(時計を見る習慣の次の機会)。"""
        s = self.cal_store
        cur = self.cal_meter["cur"]
        for a in ids.tolist():  # 逐次ループ宣言: この刻みに家に着いた体の数ぶん
            bt = int(s["back_T"][a])
            if bt >= 0:
                cur["back_trips"].append([int(a), int(s["route"][a]), round(float(self._minutes(T - bt)), 3)])
        pend = ids[s["today_pending"][ids]]
        if pend.size:  # 前の日の行き来が終わった=今日の約束(控え)を張り、本人が置く機会を作る
            s["today_pending"][pend] = False
            for k in _PEND_KEYS:  # 逐次ループ宣言: 欄の数ぶん(8)
                s[k][pend] = s["pend_" + k][pend].astype(s[k].dtype)
                s["pend_" + k][pend] = -1
            for k in ("go_T", "move_T", "arrive_T", "back_T", "home_T", "plat_T", "plan_T"):
                s[k][pend] = -1
            s["wait_go"][pend] = 0.0
            s["impossible"][pend] = False
            self._phase(pend, PH_BEFORE)
            mask = np.zeros(self.n, dtype=bool)
            mask[pend] = True
            self._init_estimates(mask & ~s["est_init"])
            for t0 in np.unique(s["day_T0"][pend]).tolist():  # 逐次ループ宣言: 控えの日の数ぶん(≤ 2)
                self._set_reminders(pend[s["day_T0"][pend] == t0], int(t0))

    # ------------------------------------------------------------------ 機会(本人の判断)
    def _opportunities(self, T: int, started: list[np.ndarray]) -> None:
        s = self.cal_store
        due = np.flatnonzero((s["next_T"] >= 0) & (s["next_T"] <= T))
        if due.size == 0:
            return
        r = self.agents.registry
        cur = self.cal_meter["cur"]
        dec = cur["decisions"]
        act = np.asarray(r.activity)[due]
        stt = np.asarray(r.transit_state)[due]
        asleep = act == int(Activity.SLEEPING)
        riding = stt == 1
        # アラームは鳴る(周りの出来事)=寝ていても鳴った刻みに数える(起こすのは W17 の起床のつなぎのまま=疲労の後)
        cur["alarm_rang_asleep"] += int(np.count_nonzero(asleep & (s["next_trig"][due] == TR_ALARM)
                                                        & (s["next_T"][due] == T)))
        dec["asleep_wait_steps"] += int(asleep.sum())
        dec["riding_wait_steps"] += int(riding.sum())
        due = due[~asleep & ~riding]
        if due.size == 0:
            return
        ch = self.cal_meter["checks"]
        go_ids: list[int] = []
        back_ids: list[int] = []
        log = self.events
        t_ns = int(T) * self.step_seconds * NS_PER_SECOND
        for a in due.tolist():  # 逐次ループ宣言 (1): この刻みの機会の数ぶん
            ph = int(s["phase"][a])
            trig = int(s["next_trig"][a])
            ref = int(s["next_ref"][a])
            ch["opportunities"] += 1
            if trig == TR_END:
                ch["end_notices"] += 1
            elif ref < 0:
                ch["backward_wakes"] += 1
            trip = TRIP_GO if ph == PH_BEFORE else TRIP_BACK
            if ph not in (PH_BEFORE, PH_AT):
                s["next_T"][a] = -1
                continue
            t0 = int(s["day_T0"][a])
            precise = trig != TR_PLANNER and self._clock_known(a)  # 時計の道具の行(見れば分単位=TM8)
            if precise:
                cur["clock_reads"] += 1
            tm, words = observe_time(int(self._minutes(T - t0)), precise=precise)
            where = "域外" if int(r.transit_state[a]) == 2 else "舞台の中"
            obs = Observation(time_min=tm, precise=precise, words=words, where=where, trigger=TRIGGERS[trig])
            pred = self._prediction(a, trip)
            cands = commute_candidates(pred)
            ctx = DecisionContext(agent_id=int(a), step=int(T), t_ns=t_ns, wake_class=-1, condition=-1,
                                  cell=int(r.cell[a]), call_id=f"{_DECIDE_STEP_KEY}:{int(T)}:{int(a)}:{trip}",
                                  percept=obs, prediction=pred)
            choice = self.port.choose(ctx, cands)
            dec["total"] += 1
            dec["by_trigger"][TRIGGERS[trig]] += 1
            dec["precise" if precise else "approx"] += 1
            kn = str(int(choice.number))
            dec["numbers"][kn] = int(dec["numbers"].get(kn, 0)) + 1
            src = next((c.source for c in cands if c.id == choice.candidate_id), None)
            if choice.is_other:
                dec["other"] += 1
                s["next_T"][a] = T + int(self._steps(LOOK_INTERVAL_MIN))
                s["next_ref"][a] = s["habit_ref"][a]
                continue
            if src == SOURCE_DELIBERATE:
                dec["deliberate"] += 1
                s["next_T"][a] = T + int(self._steps(LOOK_INTERVAL_MIN))
                s["next_ref"][a] = s["habit_ref"][a]
                continue
            if src == SOURCE_PLAN:
                dec["plan"] += 1
                (go_ids if trip == TRIP_GO else back_ids).append(int(a))
                tr = cur["trips"]
                for k_, v_ in (("agent", int(a)), ("trip", int(trip)), ("T", int(T)),
                               ("number", int(choice.number)), ("source", SOURCE_PLAN), ("trigger", int(trig)),
                               ("precise", int(precise)), ("n_cand", len(cands))):
                    tr[k_].append(v_)
                self.cal_meter["trips_total"] = int(self.cal_meter["trips_total"]) + 1
                s["next_T"][a] = -1
                if log is not None and getattr(log, "enabled", False):
                    self._write_event(log, a, choice, cands, ctx)
                continue
            dec["continue"] += 1
            cont = choice.continuous or {}
            nxt = float(cont.get("next_look_min", -1.0))
            if nxt < 0:
                s["next_T"][a] = -1
                if trip == TRIP_GO and int(s["arrive_T"][a]) >= 0:
                    # 〔検収 H1〕約束の場所を出た後に約束の時刻が過ぎた=帰りを決める(次の刻みに終わりの時刻の機会)
                    self._phase(np.array([a], dtype=np.int64), PH_AT)
                    s["next_T"][a] = T + 1
                    s["next_trig"][a] = TR_END
                    s["next_ref"][a] = -1
                elif trip == TRIP_GO:
                    self._phase(np.array([a], dtype=np.int64), PH_FORGOT)
                continue
            s["next_T"][a] = max(t0 + int(self._steps(nxt)), T + 1)
            s["next_ref"][a] = self._new_id()  # 本人の判断が置いた「次に見る時刻」
            if trig == TR_PLANNER:
                s["next_trig"][a] = TR_HEAD  # 手帳を見た後は頭の中にある(MR7 までは入力に載せるつなぎ)
        if go_ids:
            self._depart(np.asarray(go_ids, dtype=np.int64), T, started)
        if back_ids:
            self._return(np.asarray(back_ids, dtype=np.int64), T, started)

    def _clock_known(self, a: int) -> bool:
        """時計の道具の行(1-7・``engine.tools.registry`` の「時計」)をこの体が知っているか(台帳が無ければ知っている扱い)。"""
        reg = self.tools
        if reg is None:
            return True
        from shibuya.engine.tools.registry import CLOCK

        return CLOCK in reg and bool(reg.known(int(a), CLOCK))

    def _write_event(self, log: Any, a: int, choice: Any, cands: Sequence[Candidate], ctx: DecisionContext) -> None:
        """判断の出来事(1-3)=``行為:移動``・原因 ``LlmCall``(選んだ候補の源と提示の番号=口の約束 1-8 の約束 (3))。"""
        from shibuya.engine.events import vocab as V
        from shibuya.engine.events.log import Event, LlmCall

        log.append(Event(t_ns=log.now_ns, who=int(a), what=V.word(V.FAMILY_ACT, "移動"),
                         where=("cell", int(ctx.cell)) if int(ctx.cell) >= 0 else None,
                         cause=LlmCall(ctx.call_id, (), source=SOURCE_PLAN, number=int(choice.number))))

    def _depart(self, ids: np.ndarray, T: int, started: list[np.ndarray]) -> None:
        """出発(本人の判断の後の実行): 域外からは「今+域外の時間」より後に最初にホームへ入る便で着く・舞台の中は歩く。"""
        s = self.cal_store
        cur = self.cal_meter["cur"]
        st = np.asarray(self.agents.registry.transit_state)[ids]
        first = ids[s["go_T"][ids] < 0]  # 歩きが途切れて出直した体は最初の出発の時刻のまま(実際の時間に途切れた分も入る)
        s["go_T"][first] = T
        s["move_T"][first] = T
        s["wait_go"][first] = 0.0
        lo = self._steps(s["est_lo"][ids])
        imp = (T + lo) > s["start_T"][ids]
        s["impossible"][ids[imp]] = True
        route = s["route"][ids]
        place_out = s["place_kind"][ids] == _PK_OUTSIDE
        # ---- 域外に居る体 ----
        out = st == 2
        oi = ids[out]
        if oi.size:
            po = place_out[out]
            far = oi[po]  # 家が舞台の中で約束の場所も域外(今も域外)=粗い域外の時間の後に場所に着く
            if far.size:
                arr = T + self._steps(s["d_out"][far])
                s["arr_T"][far] = arr
                s["arr_ready_T"][far] = arr
                s["arr_train"][far] = -1
                s["arr_cell"][far] = -1
                s["arr_trip"][far] = TRIP_GO
                self._phase(far, PH_GO_OUTSIDE)
            inn = oi[~po]
            if inn.size:
                d_out = np.where(s["route"][inn] == RT_LOCAL, s["lead"][inn], s["d_out"][inn])
                self._inbound(inn, T + self._steps(d_out), TRIP_GO)
        # ---- 舞台の中に居る体 ----
        here = ids[st == 0]
        if here.size:
            ph = place_out[st == 0]
            self._start_walk(here[~ph], s["place_cell"][here[~ph]], WK_PLACE, TRIP_GO, T, started)
            self._start_leave(here[ph], TRIP_GO, T, started)
        del route, cur

    def _inbound(self, ids: np.ndarray, ready: np.ndarray, trip: int) -> None:
        """域外から舞台へ: ``ready`` より後に最初にホームへ入る自分の路線の便(来た電車)で着く。路線が無い体は駅の口へ。"""
        s = self.cal_store
        cur = self.cal_meter["cur"]
        line = s["line"][ids].astype(np.int64)
        trains = np.full(ids.size, -1, dtype=np.int64)
        arr = np.asarray(ready, dtype=np.int64).copy()
        cell = s["exit_cell"][ids].astype(np.int64)
        rail_on = self.rail is not None and bool(getattr(self.rail, "active", False))
        if rail_on:
            enter = np.asarray(self.rail.enter_tick, dtype=np.int64)
            pcell = np.asarray(self.rail.platform_cell, dtype=np.int64)
            for j in np.flatnonzero(line >= 0).tolist():  # 逐次ループ宣言: 出発した体の数ぶん(この刻み)
                k = self.first_train(int(line[j]), int(arr[j]))
                trains[j] = k
                if k >= 0:
                    arr[j] = int(enter[k])
                    cell[j] = int(pcell[k])
        none = (line >= 0) & rail_on & (trains < 0)
        if none.any():
            cur["no_train"] += int(none.sum())
            self._phase(ids[none], PH_STRANDED)
        ok = ~none
        sel = ids[ok]
        s["arr_T"][sel] = arr[ok]
        s["arr_ready_T"][sel] = np.asarray(ready, dtype=np.int64)[ok]
        s["arr_train"][sel] = trains[ok]
        s["arr_cell"][sel] = cell[ok].astype(np.int32)
        s["arr_trip"][sel] = np.int8(trip)
        self._phase(sel, PH_GO_OUTSIDE if trip == TRIP_GO else PH_BACK_OUTSIDE)

    def _return(self, ids: np.ndarray, T: int, started: list[np.ndarray]) -> None:
        """帰る(本人の判断の後の実行)。舞台の中: 家が域外ならホームへ・家が舞台の中なら家へ歩く。域外: 家が舞台の中なら来た便で。"""
        s = self.cal_store
        st = np.asarray(self.agents.registry.transit_state)[ids]
        s["back_T"][ids[s["back_T"][ids] < 0]] = T
        home_out = s["home_cell"][ids] < 0
        here = st == 0
        self._start_leave(ids[here & home_out], TRIP_BACK, T, started)
        hi = ids[here & ~home_out]
        self._start_walk(hi, s["home_cell"][hi], WK_HOME, TRIP_BACK, T, started)
        out = st == 2
        oh = ids[out & home_out]
        if oh.size:  # 家も域外=粗い域外の時間の後に家に着く
            arr = T + self._steps(s["d_out"][oh])
            s["arr_T"][oh] = arr
            s["arr_ready_T"][oh] = arr
            s["arr_train"][oh] = -1
            s["arr_cell"][oh] = -1
            s["arr_trip"][oh] = TRIP_BACK
            self._phase(oh, PH_BACK_OUTSIDE)
        oi = ids[out & ~home_out]
        if oi.size:
            self._inbound(oi, T + self._steps(s["d_out"][oi]), TRIP_BACK)

    # ------------------------------------------------------------------ 計器
    def _sample(self, T: int) -> None:
        s = self.cal_store
        cur = self.cal_meter["cur"]
        t0 = int(T) - int(cur["day"]) * self.tpd
        if t0 < 0:
            return
        minute = int(self._minutes(t0))
        if int(self._steps(minute)) != t0:
            return
        man = s["managed"]
        den = int(man.sum())
        hit15 = minute % SLOT_MIN == 0 and minute // SLOT_MIN < len(cur["at_rate15"])
        hit60 = minute % MINUTES_PER_HOUR == 0 and minute // MINUTES_PER_HOUR < len(cur["plan_match"])
        if not (hit15 or hit60):
            return
        # 〔検収 H1〕体の位置で数える: 舞台の中の約束の場所は「在圏で約束の場所のセルに居る」・域外の約束の場所は「域外で約束の
        # 場所の段」。段だけで数えた値は *_phase の欄(前の版の数え方)
        r = self.agents.registry
        st = np.asarray(r.transit_state)
        cell = np.asarray(r.cell, dtype=np.int64)
        pout = s["place_kind"] == _PK_OUTSIDE
        pos = man & np.where(pout, (st == 2) & (s["phase"] == PH_AT), (st == 0) & (cell == s["place_cell"]))
        ph = man & (s["phase"] == PH_AT)
        if hit15:
            k15 = minute // SLOT_MIN
            cur["at_rate15"][k15] = round(int(pos.sum()) / den, 5) if den else None
            cur["at_rate15_phase"][k15] = round(int(ph.sum()) / den, 5) if den else None
        if hit60:
            on = man & (s["start_T"] <= T) & (s["end_T"] > T)
            k = int(on.sum())
            h = minute // MINUTES_PER_HOUR
            cur["plan_match"][h] = round(int(np.count_nonzero(on & pos)) / k, 5) if k else None
            cur["plan_match_phase"][h] = round(int(np.count_nonzero(on & ph)) / k, 5) if k else None

    def _summary(self, cur: Mapping[str, Any]) -> dict[str, Any]:
        """その日の計器の記録(CA8・合否なし)。器の今の値と、その日に控えた行から作る。"""
        s = self.cal_store
        d = int(cur["day"])
        man = s["managed"] & (s["day"] == d)
        t0 = d * self.tpd

        def rel(x: np.ndarray) -> np.ndarray:
            return self._minutes(np.asarray(x, dtype=np.int64) - t0)

        go = man & (s["go_T"] >= 0)
        arr = man & (s["arrive_T"] >= 0)
        back = man & (s["back_T"] >= 0)
        home = man & (s["home_T"] >= 0)
        diff = rel(s["arrive_T"][arr]) - rel(s["start_T"][arr])
        early5 = int(np.count_nonzero(diff <= -5))
        late = int(np.count_nonzero(diff > 0))
        now = int(self.cal_meter.get("last_T", -1))
        missed = man & (s["go_T"] < 0) & ((s["phase"] == PH_FORGOT) | (s["end_T"] <= now))  # 約束の終わりまで出なかった
        forgot = {PLACEMENTS[k]: int(np.count_nonzero(missed & (s["placement"] == k))) for k in range(len(PLACEMENTS))}
        by_pl = {PLACEMENTS[k]: int(np.count_nonzero(man & (s["placement"] == k))) for k in range(len(PLACEMENTS))}
        gt = np.asarray(cur["go_trips"], dtype=np.float64).reshape(-1, 7) if cur["go_trips"] else np.zeros((0, 7))
        bt = np.asarray(cur["back_trips"], dtype=np.float64).reshape(-1, 3) if cur["back_trips"] else np.zeros((0, 3))
        sw = s["switches"][man]
        out = {k: (dict(v) if isinstance(v, Mapping) else (list(v) if isinstance(v, list) else v))
               for k, v in cur.items() if k not in ("go_trips", "back_trips", "trips", "inbound")}
        out["decisions"] = {k: (dict(v) if isinstance(v, Mapping) else v) for k, v in cur["decisions"].items()}
        out["go"] = {
            "decided": int(go.sum()), "decide_hist15": _CS._hist15(rel(s["go_T"][go]).astype(np.int64)),
            "arrived": int(arr.sum()), "arrive_hist15": _CS._hist15(rel(s["arrive_T"][arr]).astype(np.int64)),
            "arrive_minus_start": _CS._stats(diff), "early5": early5, "late": late,
            "late_rate": round(late / int(arr.sum()), 5) if int(arr.sum()) else None,
            "impossible": int(np.count_nonzero(man & s["impossible"])),
            "forgot": forgot, "forgot_rate": {k: (round(forgot[k] / by_pl[k], 5) if by_pl[k] else None) for k in forgot},
            "stranded": int(np.count_nonzero(man & (s["phase"] == PH_STRANDED))),
            "not_departed_yet": int(np.count_nonzero(man & (s["go_T"] < 0) & ~missed)),
            "not_arrived": int(np.count_nonzero(go & ~arr)),
        }
        out["back"] = {
            "decided": int(back.sum()), "decide_hist15": _CS._hist15(rel(s["back_T"][back]).astype(np.int64)),
            "decide_minus_end": _CS._stats(rel(s["back_T"][back]) - rel(s["end_T"][back])),
            "home": int(home.sum()), "home_hist15": _CS._hist15(rel(s["home_T"][home]).astype(np.int64)),
            "trip_min": _CS._stats(bt[:, 2]) if bt.size else _CS._stats(np.zeros(0)),
        }
        out["commute"] = {
            "trips": int(gt.shape[0]),
            "actual": _CS._stats(gt[:, 2]), "wait": _CS._stats(gt[:, 3]), "felt": _CS._stats(gt[:, 4]),
            "estimate_center": _CS._stats(gt[:, 5]), "actual_minus_estimate": _CS._stats(gt[:, 2] - gt[:, 5]),
            "felt_minus_actual": _CS._stats(gt[:, 4] - gt[:, 2]),
            "by_route": {ROUTES[k]: _CS._stats(gt[gt[:, 1] == k, 2]) for k in (RT_IN, RT_OUT, RT_LOCAL)},
        }
        out["phases"] = {PHASES[k]: int(np.count_nonzero(man & (s["phase"] == k))) for k in range(len(PHASES))}
        out["away"] = {"left_bodies": int(np.count_nonzero(man & (s["away_n"] > 0))),
                       "returned_bodies": int(np.count_nonzero(man & (s["away_n"] > 0) & (s["back_n"] > 0))),
                       "left": int(cur["left_at_work"]), "returned": int(cur["back_to_work"])}
        out["trips_logged"] = {"go": int(sum(1 for x in cur["trips"]["trip"] if x == TRIP_GO)),
                               "back": int(sum(1 for x in cur["trips"]["trip"] if x == TRIP_BACK))}
        out["switches"] = {"total": int(sw.sum()), "per_body_mean": round(float(sw.mean()), 4) if sw.size else None}
        return out

    def manifest(self) -> dict[str, Any]:
        from shibuya.engine.bridging import ledger as _BR

        m = self.cal_meter
        days = [m["days"][k] for k in sorted(m["days"], key=int)]
        if m["cur"]:
            days.append(self._summary(m["cur"]))
        tot: dict[str, Any] = {"managed": 0, "go_decided": 0, "go_arrived": 0, "back_decided": 0, "home": 0,
                               "early5": 0, "late": 0, "impossible": 0, "decisions": 0, "suppressed_w17_arrive": 0,
                               "suppressed_w17_depart": 0, "interrupts": 0, "left_at_work": 0, "back_to_work": 0}
        for r in days:  # 逐次ループ宣言: 日の数ぶん
            tot["managed"] += int(r["managed"])
            tot["go_decided"] += int(r["go"]["decided"])
            tot["go_arrived"] += int(r["go"]["arrived"])
            tot["back_decided"] += int(r["back"]["decided"])
            tot["home"] += int(r["back"]["home"])
            tot["early5"] += int(r["go"]["early5"])
            tot["late"] += int(r["go"]["late"])
            tot["impossible"] += int(r["go"]["impossible"])
            tot["decisions"] += int(r["decisions"]["total"])
            tot["suppressed_w17_arrive"] += int(r["suppressed_w17"]["arrive"])
            tot["suppressed_w17_depart"] += int(r["suppressed_w17"]["depart"])
            tot["interrupts"] += int(r["interrupts"])
            tot["left_at_work"] += int(r["left_at_work"])
            tot["back_to_work"] += int(r["back_to_work"])
        try:
            led = _BR.default_ledger()
            have = {b.id: b.status for b in led}
        except Exception:  # noqa: BLE001  台帳が読めない木(HEAD の写しなど)=件数は空欄
            have = {}
        return {
            "schema": SCHEMA, "mode": self.source, "port": self.port.name, "w20": dict(_CS._thaw(self.table.version)),
            "placements": list(PLACEMENTS), "look_interval_min": LOOK_INTERVAL_MIN, "margins_min": list(MARGINS_MIN),
            "recent_k": RECENT_K, "round_min": ROUND_MIN, "approx_round_min": APPROX_ROUND_MIN,
            "felt": {"wait_intercept": FELT_WAIT_INTERCEPT, "wait_slope": FELT_WAIT_SLOPE, "other_ratio": 1.0,
                     "basis": "R-111 §1-2 #1 Watkins 2011(待ち)・§1-3(待ち以外は空欄=比 1)"},
            "bridges": {"count": _BR.bridges_count(), "rows": {b: have.get(b) for b in BRIDGES}},
            "days": days, "totals": {**tot, "trips_logged": int(m["trips_total"])}, "checks": dict(m["checks"]),
        }


def manifest_fields(layer: CalendarSelf | None) -> dict[str, Any]:
    """manifest の末尾に足す欄(腕 1b のランだけ ``{"calendar_1b": …}``・既定は空=manifest は今のまま)。"""
    if layer is None:
        return {}
    return {MANIFEST_KEY: layer.manifest()}


def build(world_dir: Any, pop: Any, *, calendar: Any, agents: Any, world: Any, presence: Any, classical: Any,
          seed: int | str, day_key0: int, step_seconds: int, steps_per_day: int, events: Any = None,
          tools: Any = None, hop_steps: Any = None) -> CalendarSelf | None:
    """組み立ての口: 腕 1b のランの層を作り、0 日目を張り、計画実行層に口を挿す(腕 w17 は ``None``)。

    Raises:
        ValueError: 腕 1b で母集団(W16)か計画実行層の無いラン。
        FileNotFoundError: W20 の週の表が無い(``engine.calendar_shadow.resolve_path`` と同じ置き場)。
    """
    if not is_on():
        return None
    if pop is None or presence is None:
        raise ValueError("腕 --calendar 1b は母集団(W16)と計画実行層のあるランだけ(出入りを本人へ渡す相手が要る)")
    path = _CS.resolve_path(world_dir)
    if path is None:
        raise FileNotFoundError("腕 --calendar 1b には世界資産の置き場(world_dir)か SHIBUYA_CALENDAR_W20 が要る")
    table = _CS.load_table(path, np.asarray(pop.source_agent_id, dtype=np.int64))
    pkw = dict(seed=seed, day_key0=int(day_key0), step_seconds=int(step_seconds))
    port: DecisionPort = CommuteClassicalPort(**pkw) if classical is not None else CommuteMockPort(**pkw)
    layer = CalendarSelf(table, calendar=calendar, agents=agents, world=world, presence=presence, port=port,
                         agent_key=pop.source_agent_id, seed=seed, step_seconds=step_seconds,
                         steps_per_day=steps_per_day, events=events, tools=tools, hop_steps=hop_steps)
    layer.relay_day(0)
    presence.io_hook = layer
    return layer

