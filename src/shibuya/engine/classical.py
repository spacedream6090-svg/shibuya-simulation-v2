"""engine.classical — System 1.5 の古典的選択モデル=方策 ``classical``(5 段目 5b・D-119 L1〜L8・第292)。

正典
- ``docs/design/v2-energy-classical-implementation-agenda.md`` §2(段 5b の 1〜6)。
- 草案 ``docs/design/v2-hunger-choice-attention-draft.md`` §2-2(案 v1)・§2-6(L1〜L8)・§1-3 K6 (i)。
- 錨 ``docs/bench/anchors/ssb2021_activity_prior_v0.json``(追跡・``tools/hunger/build_activity_prior.py``
  が令和3年社会生活基本調査 時間帯編 第8-1/8-2/8-3表から決定論で生成)。**エンジンは data/ を読まない**。

「古典だけ」腕(L5 (a)): ``--policy classical`` で LLM(mock)を呼ばず、起床ごとに
  1. **食事の門**(K6 (i)・§1-2 6): ``P(食事) = 語(満腹 0/ふつう 0.1/空腹 0.6/とても空腹 0.9)×
     カレンダー(次の予定まで ≥30 分 ×1・未満 ×0.3)× 周囲(見える飲食店 無し ×0.5・同じセルに食事中の人
     ×1.2)``(上限 1)。通れば 行動 食事・対象 飲食店(店は ``engine.chooser`` の選び手が決める)。
     **社会生活基本調査は使わない**(食事の時刻分布を純粋な照合にする)。
  2. 通らなければ **ActivityChooser**(L2 (a)・L7 (a)): 事前分布 P(活動 | 15 分帯・曜日・性・年齢階級・
     就業状態)=錨の行動者率(食事 03 を除く 19 種)を正規化 × 状態の乗数 m(場所の種別)・m(次の予定まで)・
     m(直前の活動)(**初期 1.0**=感度腕)× 時間帯ごとの定数 c_t(周辺分布を事前分布に戻す 1 次元 IPF)。
  3. 選んだ活動を **対応表 v0**(:data:`ACTIVITY_MAP_V0`・宣言・ユーザーが直す前提)で 5 ラベルの応答文
     (理由=定型・行動・対象・活動・まで)にして既存の経路(パーサ → コミット)へ流す。
  を返す。``MockLLM(form="v3")`` と golden は**凍結**(既定は mock のまま=既定 checkpoint 不変)。

本クラスは ``LLMClient`` 契約(``complete(request) -> LLMResponse``)を満たす=ブリッジから見ると
クライアントの 1 つ。世界と体は**読むだけ**(書き込みは応答 → コミット → ``engine.resolve``)。

逐次ループ宣言(P4)
1. ``ActivityPrior.__init__``: 錨の層の数ぶん(曜日 × 地域 × 性 × 就業 × 年齢 ≤ 4×2×16=64・起動時 1 回)。
2. ``ClassicalPolicy.bind``: なし(配列演算)。
3. ``ClassicalPolicy.complete``: なし(1 呼=1 回・候補は 19 種の配列演算)。
4. ``ClassicalPolicy._eating_by_cell``: tick ごとに 1 回の bincount(体数の配列演算)。

expedient(宣言・問いつき)
- 対応表 v0(社会生活基本調査 20 種 → v3 の行為/対象/活動/まで)・理由の定型文・「まで」の語。
- 食事の門の定数(語 0/0.1/0.6/0.9・カレンダー 30 分と ×0.3・周囲 ×0.5/×1.2)。
- 就業状態=勤め先がある(W16 ``work_cell`` ≥ 0)か 種別が 通勤者/従業者/指令/乗務員。15 歳未満は 15〜19 歳の行。
  性別不明は男女の行の平均。層のサンプルが 0 か行が全部 0 なら同じ性 × 就業の年齢総数の行(それも 0 なら一様)。
- 行動者率の正規化(同時行動で和が 100% を超える・食事を抜いた残り)=1 から引かずに比にする。
- 状態の乗数は全部 1.0(=c_t も 1)。場所の種別=駅(路線のホームのセル)/店(在店中)/街路。
- 交際・付き合い(符号 18)の相手(第2波 §2A 項 3-1・``social``): 既定 ``acquaintance``=B5 近接行の知人のうち
  活性 A が最大の人(同点は近接行の順=未リサーチの決め)・居なければ「なし・待つ 30分」。旧 ``near_first``。
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Mapping

import numpy as np

from shibuya.agents.state import Activity, AgentKind, WakeCondition
from shibuya.core.rng import stream
from shibuya.engine.calendar import ticks_per_day as _ticks_per_day
from shibuya.llm import LLMRequest, LLMResponse, estimate_tokens
from shibuya.llm.contract import TARGET_WANDER, format_two_line_v3

__all__ = [
    "ACTIVITY_PRIOR_PATH",
    "POLICIES",
    "DEFAULT_POLICY",
    "ACTIVITY_REGIONS",
    "DEFAULT_ACTIVITY_REGION",
    "SSB_ACTIVITY_CODES",
    "ACTIVITY_MAP_V0",
    "MEAL_WORD_P",
    "MEAL_CALENDAR_MIN",
    "MEAL_CALENDAR_FACTOR",
    "MEAL_NO_EATERY_FACTOR",
    "MEAL_EATING_PEOPLE_FACTOR",
    "MEAL_GATES",
    "DEFAULT_MEAL_GATE",
    "check_meal_gate",
    "meal_gate_interval_p",
    "PLACE_KINDS",
    "CLASSICAL_SOCIAL_MODES",
    "DEFAULT_CLASSICAL_SOCIAL",
    "check_classical_social",
    "check_policy",
    "check_activity_region",
    "load_activity_prior",
    "ipf_constants",
    "ActivityPrior",
    "ClassicalPolicy",
]

ACTIVITY_PRIOR_PATH: Final[Path] = (
    Path(__file__).resolve().parents[3] / "docs" / "bench" / "anchors" / "ssb2021_activity_prior_v0.json"
)
#: 方策(``--policy``)。``mock``=凍結の ``MockLLM``(既定)/ ``classical``=本モジュール(LLM 0 呼)。
POLICIES: Final[tuple[str, ...]] = ("mock", "classical")
DEFAULT_POLICY: Final[str] = POLICIES[0]
#: 事前分布の地域(``--activity-region``)→ 錨の地域の符号。既定 関東大都市圏(宣言)。
ACTIVITY_REGIONS: Final[dict[str, str]] = {"kanto": "03", "national": "00"}
DEFAULT_ACTIVITY_REGION: Final[str] = "kanto"
#: 錨の行動の符号(食事 03 を除く 19 種・社会生活基本調査の行動の種類)。
SSB_ACTIVITY_CODES: Final[tuple[str, ...]] = tuple(f"{i:02d}" for i in range(1, 21) if i != 3)

# ---- 食事の門(K6 (i)・§1-2 6・宣言) ----
#: 語の段(満腹/ふつう/空腹/とても空腹)→ 食事の確率の基底。
MEAL_WORD_P: Final[tuple[float, float, float, float]] = (0.0, 0.1, 0.6, 0.9)
#: カレンダー: 次の予定までの残りがこの分未満なら ``MEAL_CALENDAR_FACTOR`` を掛ける。
MEAL_CALENDAR_MIN: Final[int] = 30
MEAL_CALENDAR_FACTOR: Final[float] = 0.3
#: 周囲: 見える飲食店(同じセル or W8 の可視物)が無ければ ×0.5・同じセルに食事中の人がいれば ×1.2。
MEAL_NO_EATERY_FACTOR: Final[float] = 0.5
MEAL_EATING_PEOPLE_FACTOR: Final[float] = 1.2
#: 食事の門の確率の読み方(第2波 §2A 項 4・Q48 (a)・指示書 §0-2): ``per_wake``=旧(**既定**・起床ごとの確率=起床の
#: 頻度に比例して食べる)/ ``per_hour``=語の段の確率 ``MEAL_WORD_P`` を **1 時間あたり**と読み、前回の門の後に
#: その体が**範囲内で起きていた各 tick の段**でハザード H=Σ −ln(1 − p_h) × 分/60 を積算し、門で ``p = 1 − exp(−H)`` に
#: カレンダーと周囲の係数を掛ける(**第2波 §2B の親の決定**=§2A の「起きていた分 × 評価時の段」を置き換えた・定数の値は
#: 動かさない)。既定の切り替えは食事の束の版上げでユーザーに確認する(指示書 §8-2)。
MEAL_GATES: Final[tuple[str, ...]] = ("per_wake", "per_hour")
DEFAULT_MEAL_GATE: Final[str] = "per_wake"

#: 交際・付き合い(符号 18)の相手の選び方(第2波 §2A 項 3-1・Q42 (b)): ``acquaintance``(既定)=B5 近接行に載っている
#: **知人**(生きている関係辺の相手=A ≥ τ_rel)のうち活性 A が最大の人(同点は近接行の順)・知人が居なければ
#: 「なし・待つ」(関係の腕が off のランでは知人が居ない=会話を始めない)/ ``near_first``=旧(近接行の最初の人=
#: 見知らぬ人・関係 on のランは C10 8b の重みつき抽選)。遠くの知人を誘う仕組み(約束・待ち合わせ)は C10 8d の後。
CLASSICAL_SOCIAL_MODES: Final[tuple[str, ...]] = ("acquaintance", "near_first")
DEFAULT_CLASSICAL_SOCIAL: Final[str] = "acquaintance"
#: 状態の乗数の場所の種別(m(場所)の行)。
PLACE_KINDS: Final[tuple[str, ...]] = ("station", "shop", "street")
#: 就業状態を「有業」とみなす種別(W16 の勤め先が無くても)。
_EMPLOYED_KINDS: Final[tuple[int, ...]] = (
    int(AgentKind.COMMUTER), int(AgentKind.WORKER), int(AgentKind.DISPATCHER), int(AgentKind.CREW),
)
#: 起床条件 → 起床入口(層の記録と同じ 6 つ)。
_PLAN_CONDITIONS: Final[frozenset[int]] = frozenset({
    int(WakeCondition.PLAN_SLEEPING), int(WakeCondition.PLAN_WORKING),
    int(WakeCondition.PLAN_GENERAL), int(WakeCondition.PLAN_TRANSIT),
})

# ---- 対応表 v0(社会生活基本調査の行動 → v3 の応答・宣言・ユーザーが直す前提) ----
#: 符号 → (種類, 行動, 対象, 活動, まで)。種類が ``home``/``work``/``school`` の行は場所の規則で
#: 「そこに居ればその場の活動・居なければ 移動 対象 自宅/職場/学校 まで 到着」に変える(:meth:`_respond`)。
ACTIVITY_MAP_V0: Final[dict[str, tuple[str, str, str, str, str]]] = {
    "01": ("home", "就寝", "なし", "眠る", "次の予定"),          # 睡眠
    "02": ("here", "なし", "なし", "身支度", "30分"),            # 身の回りの用事
    "04": ("commute", "移動", "なし", "通勤", "到着"),           # 通勤・通学
    "05": ("work", "なし", "なし", "仕事", "次の予定"),          # 仕事
    "06": ("school", "なし", "なし", "勉強", "次の予定"),        # 学業
    "07": ("home", "なし", "なし", "家事", "30分"),              # 家事
    "08": ("here", "なし", "なし", "介護", "30分"),              # 介護・看護
    "09": ("here", "なし", "なし", "育児", "30分"),              # 育児
    "10": ("here", "購入", "物販店", "買い物", "30分"),          # 買い物
    "11": ("here", "移動", TARGET_WANDER, "移動", "30分"),       # 移動(通勤・通学を除く)
    "12": ("here", "なし", "なし", "新聞を読む", "30分"),        # テレビ・ラジオ・新聞・雑誌
    "13": ("here", "なし", "なし", "休む", "30分"),              # 休養・くつろぎ
    "14": ("here", "なし", "なし", "勉強", "30分"),              # 学習・自己啓発・訓練(学業以外)
    "15": ("here", "移動", TARGET_WANDER, "店を見る", "30分"),   # 趣味・娯楽
    "16": ("here", "移動", TARGET_WANDER, "散歩", "30分"),       # スポーツ
    "17": ("here", "なし", "なし", "用事", "30分"),              # ボランティア活動・社会参加活動
    "18": ("talk", "会話", "なし", "話す", "30分"),              # 交際・付き合い(相手は ``social``)
    "19": ("here", "なし", "なし", "通院", "30分"),              # 受診・療養
    "20": ("here", "なし", "なし", "用事", "30分"),              # その他
}
#: 理由の定型文(宣言)。
REASON_MEAL_HUNGRY: Final[str] = "空腹を感じたから"
REASON_MEAL: Final[str] = "食事の時間だから"
REASON_ACTIVITY: Final[str] = "この時間にいつもすることだから"
REASON_GO: Final[str] = "そのための場所へ行くから"
REASON_REPLY: Final[str] = "話しかけられたから"
_PERSON_PREFIX: Final[str] = "P-"
#: B5 の近接行(「[B5 近接] 近くの人物: P-12(…)、…」)=見えている人。会話の相手はここから選ぶ(知覚だけを読む)。
_NEAR_LINE: Final[str] = "[B5 近接]"
_PERSON_ID: Final[re.Pattern[str]] = re.compile(r"P-(\d+)")


def check_policy(name: str) -> str:
    n = str(name)
    if n not in POLICIES:
        raise ValueError(f"policy は {POLICIES} のどれか(いま {name!r})")
    return n


def check_classical_social(name: str) -> str:
    n = str(name)
    if n not in CLASSICAL_SOCIAL_MODES:
        raise ValueError(f"classical_social は {CLASSICAL_SOCIAL_MODES} のどれか(いま {name!r})")
    return n


def check_meal_gate(name: str) -> str:
    n = str(name)
    if n not in MEAL_GATES:
        raise ValueError(f"meal_gate は {MEAL_GATES} のどれか(いま {name!r})")
    return n


#: 語の段の刻み(``chooser.hunger_stage_of`` と同じ・``INTERO_UP_EDGES``)と、段 → 1 時間あたりのハザード
#: ``−ln(1 − MEAL_WORD_P)``(p=1 は ∞=必ず通る)。``per_hour`` の積算が引く表(定数の値は ``MEAL_WORD_P`` のまま)。
_HUNGER_EDGES: Final[tuple[int, int, int]] = (4, 7, 9)
with np.errstate(divide="ignore"):
    _HAZARD_PER_HOUR: Final[np.ndarray] = -np.log1p(-np.asarray(MEAL_WORD_P, dtype=np.float64))


def meal_gate_interval_p(p_hour: float, dt_minutes: float) -> float:
    """1 時間あたりの確率 ``p_hour`` → 経過 ``dt_minutes`` 分の間に 1 回以上通る確率 ``1 − (1 − p)^(Δt/60)``。

    分け方に依らない(60 分を 1 分ずつ 60 回評価しても、60 分後に 1 回評価しても、1 回以上通る確率は ``p_hour``)。

    Example:
        >>> round(meal_gate_interval_p(0.1, 60.0), 12)
        0.1
        >>> meal_gate_interval_p(1.0, 1.0), meal_gate_interval_p(0.5, 0.0)
        (1.0, 0.0)
    """
    p = min(1.0, max(0.0, float(p_hour)))
    dt = max(0.0, float(dt_minutes))
    if p >= 1.0:
        return 1.0 if dt > 0.0 else 0.0
    return float(1.0 - (1.0 - p) ** (dt / 60.0))


def check_activity_region(name: str) -> str:
    n = str(name)
    if n not in ACTIVITY_REGIONS:
        raise ValueError(f"activity_region は {tuple(ACTIVITY_REGIONS)} のどれか(いま {name!r})")
    return n


def load_activity_prior(path: str | Path | None = None) -> tuple[dict[str, Any], str]:
    """事前分布の錨(追跡ファイル)を読む → ``(辞書, md5)``。"""
    p = Path(path) if path is not None else ACTIVITY_PRIOR_PATH
    raw = p.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.md5(raw).hexdigest()


def day_kind_of(day_index: int) -> str:
    """``day_index``(0=月曜)→ 錨の曜日の鍵(平日/土曜/日曜)。"""
    d = int(day_index) % 7
    return "weekday" if d < 5 else ("saturday" if d == 5 else "sunday")


def ipf_constants(p0: np.ndarray, m: np.ndarray) -> np.ndarray:
    """1 次元 IPF(L7 (a)): 乗数を掛けたあとの**集団の周辺**を事前分布の周辺に戻す定数 c(活動ごと)。

    ``p0``/``m`` は ``(体, 活動)``。``c[a] = Σ_i p0[i,a] / Σ_i p0[i,a]·m[i,a]`` とすると
    ``Σ_i p0[i,a]·m[i,a]·c[a] = Σ_i p0[i,a]``(活動 a を選ぶ人数の期待値が事前分布のまま)。
    分母が 0 の活動は 1(宣言)。体ごとの正規化は呼び側(=「誰がするか」だけを乗数が動かす)。

    Example:
        >>> p0 = np.array([[0.5, 0.5], [0.2, 0.8]]); m = np.array([[2.0, 1.0], [2.0, 1.0]])
        >>> ipf_constants(p0, m).tolist()
        [0.5, 1.0]
    """
    a = np.asarray(p0, dtype=np.float64)
    b = a * np.asarray(m, dtype=np.float64)
    num = a.sum(axis=0)
    den = b.sum(axis=0)
    return np.where(den > 0, num / np.where(den > 0, den, 1.0), 1.0)


class ActivityPrior:
    """錨 → 配列 ``rates[性 2, 就業 2, 年齢 16(0=総数), 活動 19, 時刻 96]``(行動者率 %)。"""

    def __init__(self, anchors: Mapping[str, Any], day_kind: str, region: str) -> None:
        tables = anchors["tables"]
        if day_kind not in tables:
            raise ValueError(f"錨に曜日 {day_kind!r} が無い")
        code = ACTIVITY_REGIONS[check_activity_region(region)]
        block = tables[day_kind].get(code)
        if block is None:
            raise ValueError(f"錨に {day_kind} × 地域 {region}({code})が無い(builder の宣言を見る)")
        if tuple(anchors["activity_codes"]) != SSB_ACTIVITY_CODES:
            raise ValueError("錨の行動の符号が対応表と合わない")
        ages = ("00",) + tuple(anchors["age_codes"])
        self.age_lo = np.asarray(anchors["age_lo"], dtype=np.int64)
        self.rates = np.zeros((2, 2, len(ages), len(SSB_ACTIVITY_CODES), int(anchors["n_slots"])))
        self.sample = np.zeros((2, 2, len(ages)), dtype=np.int64)
        for si, s in enumerate(("1", "2")):
            for ei, e in enumerate(("1", "2")):
                for ai, age in enumerate(ages):  # 逐次ループ宣言 1(起動時・層の数ぶん)
                    st = block[f"{s}-{e}"][age]
                    self.rates[si, ei, ai] = np.asarray(st["rates"], dtype=np.float64) / 100.0
                    self.sample[si, ei, ai] = int(st["sample"])
        self.day_kind = day_kind
        self.region = region

    def age_index(self, age: np.ndarray) -> np.ndarray:
        """年齢 → 1〜15(15 歳未満は 15〜19 歳=1)。"""
        a = np.asarray(age, dtype=np.int64)
        return np.clip(np.searchsorted(self.age_lo, a, side="right"), 1, self.age_lo.size)

    def row(self, sex: int, employed: bool, age: int, slot: int) -> np.ndarray:
        """1 体の P0(活動 | 15 分帯)(19 種・和 1)。落とし方はモジュール注記。"""
        ei = 0 if employed else 1
        ai = int(self.age_index(np.asarray([age]))[0])
        sexes = (0, 1) if int(sex) not in (0, 1) else (int(sex),)
        vec = np.zeros(len(SSB_ACTIVITY_CODES), dtype=np.float64)
        for si in sexes:  # 1〜2 回
            r = self.rates[si, ei, ai, :, int(slot)]
            if self.sample[si, ei, ai] <= 0 or not (r.sum() > 0):
                r = self.rates[si, ei, 0, :, int(slot)]
            vec += r
        s = float(vec.sum())
        if not (s > 0):
            return np.full(len(SSB_ACTIVITY_CODES), 1.0 / len(SSB_ACTIVITY_CODES))
        return vec / s


@dataclass
class ClassicalPolicy:
    """方策 ``classical``(LLM 0 呼)。``bind`` のあとで ``complete`` が使える。"""

    seed: int | str
    prior: ActivityPrior
    prior_md5: str = ""
    #: 状態の乗数(初期 1.0=感度腕)。行=場所の種別 3・次の予定まで 30 分未満か 2・直前の活動 20(0=なし)。
    m_place: np.ndarray = field(default_factory=lambda: np.ones((3, len(SSB_ACTIVITY_CODES))))
    m_next: np.ndarray = field(default_factory=lambda: np.ones((2, len(SSB_ACTIVITY_CODES))))
    m_prev: np.ndarray = field(default_factory=lambda: np.ones((len(SSB_ACTIVITY_CODES) + 1,
                                                               len(SSB_ACTIVITY_CODES))))
    source: str = "classical"
    #: 交際の相手の選び方(:data:`CLASSICAL_SOCIAL_MODES`・既定 ``acquaintance``)。
    social: str = DEFAULT_CLASSICAL_SOCIAL
    #: 食事の門の確率の読み方(:data:`MEAL_GATES`・既定 ``per_wake``=旧)。
    meal_gate: str = DEFAULT_MEAL_GATE
    n_calls: int = 0
    counts: dict[str, int] = field(default_factory=dict)
    #: 層の記録の補助: 時(0〜23)× {食事の門を通った, 活動の選択} の件数。
    by_hour: np.ndarray = field(default_factory=lambda: np.zeros((24, 2), dtype=np.int64))

    # ---- ランの状態への結び付け(run_day が SoA と世界を作ったあとで 1 回) ----
    def bind(
        self,
        *,
        agents: Any,
        world: Any,
        home_cell: np.ndarray,
        work_cell: np.ndarray,
        school_cell: np.ndarray | None,
        has_work: np.ndarray,
        boundary_agent: np.ndarray,
        boundary_tick: np.ndarray,
        tick_seconds: int = 60,
        station_cells: np.ndarray | None = None,
    ) -> None:
        n = int(agents.n)
        self.agents = agents
        self.world = world
        self.minutes_per_tick = float(tick_seconds) / 60.0
        self._tpd = _ticks_per_day(int(tick_seconds))  # 10a: 計画境界は日の中の tick で引く
        self.home_cell = np.asarray(home_cell, dtype=np.int64)
        self.work_cell = np.asarray(work_cell, dtype=np.int64)
        self.school_cell = (
            np.asarray(school_cell, dtype=np.int64) if school_cell is not None
            else np.full(n, -1, dtype=np.int64)
        )
        kind = np.asarray(agents.registry.field("kind"), dtype=np.int64)
        self.employed = np.asarray(has_work, dtype=bool) | np.isin(kind, _EMPLOYED_KINDS)
        self.has_work = np.asarray(has_work, dtype=bool)
        # 次の予定(計画境界)の tick を体ごとに(CSR)
        ba = np.asarray(boundary_agent, dtype=np.int64)
        bt = np.asarray(boundary_tick, dtype=np.int64)
        order = np.lexsort((bt, ba))
        self._b_tick = bt[order]
        counts = np.bincount(ba[order], minlength=n)[:n] if ba.size else np.zeros(n, dtype=np.int64)
        self._b_off = np.zeros(n + 1, dtype=np.int64)
        np.cumsum(counts, out=self._b_off[1:])
        self._station = np.zeros(int(world.n_cells), dtype=bool)
        if station_cells is not None:
            sc = np.asarray(station_cells, dtype=np.int64)
            sc = sc[(sc >= 0) & (sc < self._station.size)]
            self._station[sc] = True
        self._eatery = np.asarray(world.eatery_mask, dtype=bool)
        poi_cell = np.asarray(world.pois.cell, dtype=np.int64)
        self._cell_has_eatery = np.zeros(int(world.n_cells), dtype=bool)
        ok = self._eatery & (poi_cell >= 0) & (poi_cell < int(world.n_cells))
        self._cell_has_eatery[poi_cell[ok]] = True
        self._prev = np.zeros(n, dtype=np.int64)  # 直前の活動(0=なし・1〜19=SSB_ACTIVITY_CODES+1)
        self._eating_tick = -1
        self._eating_cells = np.zeros(int(world.n_cells), dtype=np.int64)
        self._identity = bool(
            np.all(self.m_place == 1.0) and np.all(self.m_next == 1.0) and np.all(self.m_prev == 1.0)
        )
        #: 10d: 鍵は ``(日, 15 分帯)``(帯だけだと複数日のランで 0 日目の c_t を 2 日目も使い回す)。
        self._ipf_cache: dict[tuple[int, int], np.ndarray] = {}
        self._condition: dict[int, tuple[int, int]] = {}
        #: C10 8b(Q98 の解消): 会話の相手の選び手 ``(体, tick, 近接行の「未知」の人の id 列) → 相手 or −1``
        #: (``--relations on`` のランだけ ``engine.run`` が差し込む=関係辺の重み・残りの層=未知の人から seed つき
        #: ハッシュ順=D-31 (a)・既定 None=従来の「近接行の最初の人」)。
        self.partner_fn: Any = None
        #: 第2波 §2A 項 3-1: 知人の活性 ``(体, tick, 近接行の人の id 列) → A の配列``(生きている辺の相手でなければ
        #: −inf)。``--relations on`` のランだけ ``engine.run`` が差し込む(既定 None=知人は居ない)。
        self.acq_fn: Any = None
        check_classical_social(self.social)
        #: 第2波 §2B(親の決定・§2A 項 4 の規則を置き換え): ``per_hour`` の腕だけ、体ごとの**ハザードの積算** H
        #: (float32=**4 B/体**・腕の中だけ・ラン開始は 0)。:meth:`accrue_awake` が毎 tick、範囲内で起きている体に
        #: ``−ln(1 − p_h(その tick の語の段)) × 分/60`` を足し、門を引くと 0 に戻す。``per_wake`` は持たない(0 B)。
        self._gate_hazard: np.ndarray | None = (
            np.zeros(n, dtype=np.float32) if check_meal_gate(self.meal_gate) == "per_hour" else None
        )
        self._tick = -1

    def rebuild_derived(self) -> None:
        """10d: SoA の ``kind`` から作る表(``employed``)を今の SoA から作り直す(再開で保存した SoA を戻した後)。

        ``bind`` は起動時の SoA(``initialize`` の後)を読む。再開では初期化を呼ばないので、戻した SoA から作る。
        """
        kind = np.asarray(self.agents.registry.field("kind"), dtype=np.int64)
        self.employed = np.asarray(self.has_work, dtype=bool) | np.isin(kind, _EMPLOYED_KINDS)

    def set_call(self, agent_id: int, condition: int, inviter: int = -1) -> None:
        """run のループが ``bridge.call`` の直前に起床条件と招待者を渡す(応答文の型が読む)。"""
        self._condition[int(agent_id)] = (int(condition), int(inviter))

    # ---- 状態 ----
    def _minute(self, tick: int) -> int:
        return int(int(tick) * self.minutes_per_tick) % 1440

    def _next_plan_minutes(self, aid: int, tick: int) -> int:
        lo, hi = int(self._b_off[aid]), int(self._b_off[aid + 1])
        if hi <= lo:
            return 10_000
        td = int(tick) % self._tpd  # 10a: 通しの時刻 T → 日の中の tick
        k = lo + int(np.searchsorted(self._b_tick[lo:hi], td, side="right"))
        if k >= hi:
            return 10_000
        return int((int(self._b_tick[k]) - td) * self.minutes_per_tick)

    def _eating_by_cell(self, tick: int) -> np.ndarray:
        """同じセルで食事中の人の数(在店 ∧ 飲食店)。tick ごとに 1 回(逐次ループ宣言 4)。"""
        if self._eating_tick != int(tick):
            r = self.agents.registry
            ref = np.asarray(r.poi_ref, dtype=np.int64)
            ok = (ref >= 0) & (np.asarray(r.activity) == int(Activity.SHOPPING))
            ok[ok] = self._eatery[ref[ok]]
            cell = np.asarray(r.cell, dtype=np.int64)
            ok &= cell >= 0
            self._eating_cells = np.bincount(cell[ok], minlength=self._station.size)
            self._eating_tick = int(tick)
        return self._eating_cells

    def _place_kind(self, aid: int, cell: int) -> int:
        r = self.agents.registry
        if int(r.poi_ref[aid]) >= 0:
            return 1
        if 0 <= cell < self._station.size and self._station[cell]:
            return 0
        return 2

    def meal_probability(self, aid: int, tick: int) -> tuple[float, int]:
        """食事の門の確率と語の段(K6 (i)・§1-2 6)。

        ``per_hour``(**第2波 §2B の親の決定**=§2A 項 4 の「起きていた分 × 評価時の段」を置き換え): 語の段の
        ``MEAL_WORD_P`` を 1 時間あたりの確率 p_h と読み、前回の門の後に範囲内で起きていた各 tick の段の p_h で
        ハザード H=Σ −ln(1 − p_h) × 分/60 を積算(:meth:`accrue_awake`)。門では ``p = 1 − exp(−H)`` に
        カレンダーと周囲の係数を旧と同じ順序で掛け(上限 1)、H を 0 に戻す(p が 0 でも)。満腹(p_h=0)の時間・
        就寝中・範囲外は H に入らない。段は評価時の段(計数用)。
        **Q-2B-6(親の決定)**: (iii) 評価の時点で満腹(p_h=0)なら p=0・H=0。(ii) 食事(``since_meal`` を 0 に
        戻す摂取=飲食店・範囲外・自宅の食事)のたびに H=0(``resolve._energy_meal`` が ``EnergyLayer.meal_reset``
        を通して戻す=:meth:`meal_reset_array`)。軽食・飲料では戻さない。
        """
        if self._gate_hazard is None:
            return self._meal_p_word(aid, tick)
        from shibuya.engine.chooser import hunger_stage_of

        h = float(self._gate_hazard[aid])
        self._gate_hazard[aid] = 0.0
        stage = hunger_stage_of(int(self.agents.registry.hunger[aid]))
        if MEAL_WORD_P[stage] <= 0.0:
            # 第2波 §2B Q-2B-6 (iii)(親の決定): いま満腹(p_h=0)なら食事に行く決定は起きない=p=0・H=0
            return 0.0, stage
        base = 1.0 if math.isinf(h) else float(-math.expm1(-h))
        return self._meal_p_word(aid, tick, base=base)[0], stage

    def meal_reset_array(self) -> np.ndarray | None:
        """Q-2B-6 (ii): 食事で 0 に戻す配列(``per_hour`` の H・``per_wake`` は None)。``engine.run`` が
        ``EnergyLayer.meal_reset`` に渡す。"""
        return self._gate_hazard

    def accrue_awake(self) -> None:
        """``per_hour`` の腕だけ: この tick に範囲内で起きている体(活動が就寝でなく ``transit_state==0``=エネルギー層の
        診断 ``awake_in_area`` と同じ判定)の H に ``−ln(1 − p_h(語の段)) × 分/60`` を足す(満腹は p_h=0=足さない)。
        毎 tick 1 回・体数の配列演算(段の表引き+対数の表引き=逐次ループなし)。p_h=1 の段があれば H=∞=
        「必ず通る」(上限を置かない・宣言。いまの ``MEAL_WORD_P`` の最大は 0.9)。"""
        if self._gate_hazard is None:
            return
        r = self.agents.registry
        ok = (np.asarray(r.activity) != int(Activity.SLEEPING)) & (np.asarray(r.transit_state) == 0)
        if not ok.any():
            return
        stage = np.searchsorted(np.asarray(_HUNGER_EDGES, dtype=np.int64),
                                np.asarray(r.hunger, dtype=np.int64)[ok], side="right")
        self._gate_hazard[ok] += (_HAZARD_PER_HOUR[stage] * (self.minutes_per_tick / 60.0)).astype(np.float32)

    def _meal_p_word(self, aid: int, tick: int, base: float | None = None) -> tuple[float, int]:
        """語 × カレンダー × 周囲(上限 1)。``per_wake`` ではこれがそのまま門の確率。``base`` を渡すと語の値の代わりに
        それを使う(``per_hour`` の ``1 − exp(−H)``)。"""
        from shibuya.engine.chooser import hunger_stage_of

        r = self.agents.registry
        stage = hunger_stage_of(int(r.hunger[aid]))
        p = MEAL_WORD_P[stage] if base is None else float(base)
        if p <= 0.0:
            return 0.0, stage
        if self._next_plan_minutes(aid, tick) < MEAL_CALENDAR_MIN:
            p *= MEAL_CALENDAR_FACTOR
        cell = int(r.cell[aid])
        seen = bool(0 <= cell < self._cell_has_eatery.size and self._cell_has_eatery[cell])
        if not seen and cell >= 0:
            vp, _vn = self.world.visible_pois(cell)
            seen = bool(vp.size and self._eatery[np.asarray(vp, dtype=np.int64)].any())
        if not seen:
            p *= MEAL_NO_EATERY_FACTOR
        if cell >= 0:
            eating = self._eating_by_cell(tick)
            me = int(ok_self(r, aid, self._eatery))
            if int(eating[cell]) - me > 0:
                p *= MEAL_EATING_PEOPLE_FACTOR
        return min(1.0, float(p)), stage

    def activity_probs(self, aid: int, tick: int) -> np.ndarray:
        """ActivityChooser(L2・L7): P0 × m(場所)× m(次の予定)× m(直前)× c_t → 正規化(19 種)。"""
        r = self.agents.registry
        slot = self._minute(tick) // 15
        p0 = self.prior.row(int(r.sex[aid]), bool(self.employed[aid]), int(r.age[aid]), slot)
        if self._identity:
            return p0
        cell = int(r.cell[aid])
        m = (self.m_place[self._place_kind(aid, cell)]
             * self.m_next[1 if self._next_plan_minutes(aid, tick) < MEAL_CALENDAR_MIN else 0]
             * self.m_prev[int(self._prev[aid])])
        c = self._ipf(slot, tick)
        p = p0 * m * c
        s = float(p.sum())
        return p / s if s > 0 else p0

    def _ipf(self, slot: int, tick: int) -> np.ndarray:
        """c_t(slot)=起きて範囲内に居る体の P0 と乗数から 1 次元 IPF(帯ごとに 1 回・乗数が 1 でないときだけ)。"""
        key = (int(tick) // self._tpd, int(slot))  # 10d: 日を足した(1 日のランは日 0 だけ=同じ値)
        got = self._ipf_cache.get(key)
        if got is not None:
            return got
        r = self.agents.registry
        ids = np.flatnonzero((np.asarray(r.transit_state) == 0)
                             & (np.asarray(r.activity) != int(Activity.SLEEPING)))
        if ids.size == 0:
            c = np.ones(len(SSB_ACTIVITY_CODES))
        else:
            p0 = np.stack([self.prior.row(int(r.sex[i]), bool(self.employed[i]), int(r.age[i]), slot)
                           for i in ids.tolist()])  # 帯ごとに 1 回・乗数が 1 のランは通らない
            m = np.stack([
                self.m_place[self._place_kind(int(i), int(r.cell[i]))]
                * self.m_next[1 if self._next_plan_minutes(int(i), tick) < MEAL_CALENDAR_MIN else 0]
                * self.m_prev[int(self._prev[i])]
                for i in ids.tolist()
            ])
            c = ipf_constants(p0, m)
        self._ipf_cache[key] = c
        return c

    # ---- 応答文 ----
    def _respond(self, code: str, aid: int, cell: int, prompt: str,
                 inviter: int) -> tuple[str, str, str, str, str]:
        """対応表 v0 の 1 行 → (理由, 行動, 対象, 活動, まで)。場所の規則は :data:`ACTIVITY_MAP_V0` の注記。"""
        kind, action, target, activity, until = ACTIVITY_MAP_V0[code]
        home = int(self.home_cell[aid])
        if kind == "home":
            if cell == home and home >= 0:
                return REASON_ACTIVITY, action, target, activity, until
            if home >= 0:
                return REASON_GO, "移動", "自宅", "帰宅", "到着"
            return REASON_ACTIVITY, "なし", "なし", "休む", "30分"  # 自宅が範囲外=その場で休む
        if kind in ("work", "school"):
            place = int(self.work_cell[aid]) if kind == "work" else int(self.school_cell[aid])
            has = bool(self.has_work[aid]) if kind == "work" else place >= 0
            if has and place >= 0 and cell != place:
                return REASON_GO, "移動", "職場" if kind == "work" else "学校", "通勤", "到着"
            return REASON_ACTIVITY, action, target, activity, until
        if kind == "commute":
            if bool(self.has_work[aid]) and int(self.work_cell[aid]) >= 0 and cell != int(self.work_cell[aid]):
                return REASON_GO, "移動", "職場", "通勤", "到着"
            sc = int(self.school_cell[aid])
            if sc >= 0 and cell != sc:
                return REASON_GO, "移動", "学校", "通学", "到着"
            return REASON_ACTIVITY, "なし", "なし", "待つ", "30分"
        if kind == "talk" and self.social == "acquaintance":
            if inviter >= 0:
                who = f"{_PERSON_PREFIX}{inviter}"
            else:
                pid = self._best_acquaintance(aid, prompt)
                who = f"{_PERSON_PREFIX}{pid}" if pid >= 0 else ""
            if who:
                self.counts["talk_acquaintance"] = self.counts.get("talk_acquaintance", 0) + 1
                return REASON_ACTIVITY, "会話", who, activity, until
            self.counts["talk_no_acquaintance"] = self.counts.get("talk_no_acquaintance", 0) + 1
            return REASON_ACTIVITY, "なし", "なし", "待つ", "30分"  # 近くに知人が居ない
        if kind == "talk":
            if inviter < 0 and self.partner_fn is not None:  # C10 8b: 関係辺の重み(残り=最初の「未知」の人)
                pid = int(self.partner_fn(aid, self._tick, _near_strangers(prompt, aid)))
                who = f"{_PERSON_PREFIX}{pid}" if pid >= 0 else ""
            else:
                who = f"{_PERSON_PREFIX}{inviter}" if inviter >= 0 else _first_near_person(prompt, aid)
            if who:
                return REASON_ACTIVITY, "会話", who, activity, until
            return REASON_ACTIVITY, "なし", "なし", "待つ", "30分"  # 話す相手が見えない
        return REASON_ACTIVITY, action, target, activity, until

    def _best_acquaintance(self, aid: int, prompt: str) -> int:
        """近接行の人のうち知人(A ≥ τ)で A が最大の人の id(同点は行の順)・居なければ −1。"""
        if self.acq_fn is None:
            return -1
        ids = _near_persons(prompt, aid)
        if not ids:
            return -1
        A = np.asarray(self.acq_fn(int(aid), int(self._tick), ids), dtype=np.float64)
        if A.size == 0 or not bool(np.isfinite(A).any()):
            return -1
        return int(ids[int(np.argmax(np.where(np.isfinite(A), A, -np.inf)))])  # argmax=最初の最大=行の順

    def render(self, request: LLMRequest) -> str:
        aid = int(request.agent_id)
        tick = int(request.tick)
        r = self.agents.registry
        cond, inviter = self._condition.pop(aid, (-1, -1))
        self._tick = tick
        cell = int(r.cell[aid])
        g = stream(self.seed, "policy.classical", tick, aid, max(0, cond))
        u_meal, u_act = float(g.random()), float(g.random())
        hour = self._minute(tick) // 60
        if cond == int(WakeCondition.CONVERSATION_TURN) and inviter >= 0:
            self.counts["reply_talk"] = self.counts.get("reply_talk", 0) + 1
            self.by_hour[hour, 1] += 1
            return format_two_line_v3(REASON_REPLY, "会話", f"{_PERSON_PREFIX}{inviter}", "話す", "30分")
        p_meal, stage = self.meal_probability(aid, tick)
        if u_meal < p_meal:
            self.counts["meal"] = self.counts.get("meal", 0) + 1
            self.counts[f"meal_stage:{stage}"] = self.counts.get(f"meal_stage:{stage}", 0) + 1
            self.by_hour[hour, 0] += 1
            reason = REASON_MEAL_HUNGRY if stage >= 2 else REASON_MEAL
            return format_two_line_v3(reason, "食事", "飲食店", "食事", "30分")
        p = self.activity_probs(aid, tick)
        k = int(np.searchsorted(np.cumsum(p), u_act * float(p.sum()), side="right"))
        k = min(k, len(SSB_ACTIVITY_CODES) - 1)
        code = SSB_ACTIVITY_CODES[k]
        self._prev[aid] = k + 1
        self.counts[f"activity:{code}"] = self.counts.get(f"activity:{code}", 0) + 1
        self.by_hour[hour, 1] += 1
        reason, action, target, activity, until = self._respond(
            code, aid, cell, str(request.prompt), inviter
        )
        return format_two_line_v3(reason, action, target, activity, until)

    def complete(self, request: LLMRequest) -> LLMResponse:
        """``LLMClient`` 契約の同期実装(LLM は呼ばない)。"""
        text = self.render(request)
        self.n_calls += 1
        return LLMResponse(text=text, tokens_in=0, tokens_out=estimate_tokens(text), source=self.source)

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        return self.complete(request)

    def manifest_fields(self) -> dict[str, Any]:
        return {
            "policy": "classical",
            "prior": {"anchors": "docs/bench/anchors/ssb2021_activity_prior_v0.json",
                      "anchors_md5": self.prior_md5, "day_kind": self.prior.day_kind,
                      "region": self.prior.region},
            "meal_gate": {"mode": str(self.meal_gate), "word_p": list(MEAL_WORD_P),
                          "per_hour_rule": "hazard: H += -ln(1-p_h(stage of each awake-in-area tick)) x min/60; "
                                           "p = 1 - exp(-H) x calendar x surroundings (wave2 2B)",
                          "calendar_min": MEAL_CALENDAR_MIN,
                          "calendar_factor": MEAL_CALENDAR_FACTOR,
                          "no_eatery_factor": MEAL_NO_EATERY_FACTOR,
                          "eating_people_factor": MEAL_EATING_PEOPLE_FACTOR},
            "social": str(self.social),
            "multipliers_identity": bool(self._identity),
            "activity_map": "v0",
            "counts": dict(sorted(self.counts.items())),
            "calls": int(self.n_calls),
        }


def _first_near_person(prompt: str, aid: int) -> str:
    """B5 の近接行の最初の人(自分を除く)→ ``P-<id>``。見えなければ ``""``。"""
    for line in prompt.splitlines():
        if line.startswith(_NEAR_LINE):
            for m in _PERSON_ID.finditer(line):
                if int(m.group(1)) != int(aid):
                    return f"{_PERSON_PREFIX}{m.group(1)}"
            break
    return ""


def _near_persons(prompt: str, aid: int) -> list[int]:
    """B5 の近接行の人(自分を除く)の id(行の順=距離の順)。"""
    for line in prompt.splitlines():
        if line.startswith(_NEAR_LINE):
            return [int(m.group(1)) for m in _PERSON_ID.finditer(line) if int(m.group(1)) != int(aid)]
    return []


def _near_strangers(prompt: str, aid: int) -> list[int]:
    """B5 の近接行で印が「未知」の人(自分を除く)の id(行の順)。C10 8b の「残り」の層の候補。"""
    from shibuya.perception.templates import NEAR_PERSON_MARKS

    mark = f"({NEAR_PERSON_MARKS[0]})"
    out: list[int] = []
    for line in prompt.splitlines():
        if line.startswith(_NEAR_LINE):
            for m in _PERSON_ID.finditer(line):  # 近接行の人数ぶん(≤ 数人)
                if int(m.group(1)) != int(aid) and line[m.end():m.end() + len(mark)] == mark:
                    out.append(int(m.group(1)))
            break
    return out


def ok_self(r: Any, aid: int, eatery: np.ndarray) -> bool:
    """体 ``aid`` 自身が食事中か(同じセルの食事中の人数から自分を引くため)。"""
    ref = int(r.poi_ref[aid])
    return bool(ref >= 0 and int(r.activity[aid]) == int(Activity.SHOPPING) and eatery[ref])
