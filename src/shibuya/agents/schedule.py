"""agents.schedule — **mock 専用**の合成 T0 週次スケジュール(計画境界の生成器)。

位置づけ(**mock / expedient・正典ではない**)
    本物の個体スケジュールは世界データ構築仕様の **W17(T1・40万呼で生成)** が作る(C5)。
    本モジュールが作るのは C2 の mock ラン(予算行 W2: 5,000 体×1日・mock LLM ≤10 分)を
    回すためだけの**合成日課**であり、実データに寄せる意図はない——寄せると mock が
    暗黙の行動モデルになり較正の汚染源になる(``llm.mock`` と同じ理由)。
    したがって時刻の分布・セルの選び方は**すべて expedient**。

決定論(運用設計書 §1.4 T4「n=5,000 と 5,001 で既存個体の乱数列が不変」)
    個体 i の抽選は ``core.rng.philox(master_seed, "agent.schedule", i*BLOCKS_PER_AGENT)`` の
    生語 ``WORDS_PER_AGENT`` 本だけで決まる。Philox4x64 は 1 カウンタ=4 語なので、
    カウンタ 0 から ``4·k`` 語まとめて生成した列の ``[WORDS_PER_AGENT·i : …]`` 区間は
    個体ごとに引いた列と**バイト一致**する(``tests/agents/test_schedule.py`` で機械検査)。
    → 一括生成(ベクトル化)と個体別生成(T4 の定義)が同値なので、**両方を提供して
    一括を既定にする**(40万体で約70 ms)。

逐次ループ宣言(P4)
- ``draw_words_per_agent``(参照実装・テスト専用)のみ個体数ぶんのループを持つ。
  既定の ``draw_words`` は 1 回の ``random_raw`` = ループなし。

expedient(本モジュール分)
- 1日 5 境界(起床・外出・昼・帰宅・就寝)という粗い日課。実在の活動連鎖(PT 調査の
  目的別トリップ)には合わせていない。**呼数の桁**(計画境界起床≈5 呼/体/日)を
  L4「平均10呼/体/日」の半分に置き、残りを個体変化・セル変化に空けるのが唯一の設計意図。
- 平日/休日の 2 パターンのみ(週 7 日表 = C4 の PlanSpec + C5 の W17)。
- 時刻帯の値(起床 5:00-8:00 など)は自前。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np

from shibuya.agents.state import MOCK_KIND_COUNT, Activity
from shibuya.core.rng import philox

__all__ = [
    "SCHEDULE_DOMAIN",
    "WORDS_PER_AGENT",
    "BLOCKS_PER_AGENT",
    "N_BOUNDARIES",
    "BOUNDARY_NAMES",
    "draw_words",
    "draw_words_per_agent",
    "MockWeeklySchedule",
    "synthesize",
]

#: ``core.rng`` のドメイン名(manifest の ``rng.domain_table_version`` の表の1項)。
SCHEDULE_DOMAIN: Final[str] = "agent.schedule"
#: 1 個体あたりの生語数(Philox4x64 の 1 カウンタ=4 語 → 2 ブロック)。
WORDS_PER_AGENT: Final[int] = 8
BLOCKS_PER_AGENT: Final[int] = WORDS_PER_AGENT // 4

#: 1 日の計画境界の数と名前(expedient)。
N_BOUNDARIES: Final[int] = 5
BOUNDARY_NAMES: Final[tuple[str, ...]] = ("起床", "外出", "昼", "帰宅", "就寝")

_MINUTES_PER_DAY: Final[int] = 1_440


def draw_words(master_seed: int | str, n_agents: int, *, start_agent: int = 0) -> np.ndarray:
    """個体 ``start_agent..start_agent+n_agents-1`` の生語を一括生成する(ループなし)。

    Returns:
        形 ``(n_agents, WORDS_PER_AGENT)`` の uint64 配列。
    """
    if n_agents < 0 or start_agent < 0:
        raise ValueError("n_agents・start_agent は 0 以上")
    if n_agents == 0:
        return np.empty((0, WORDS_PER_AGENT), dtype=np.uint64)
    bg = philox(master_seed, SCHEDULE_DOMAIN, int(start_agent) * BLOCKS_PER_AGENT)
    raw = bg.random_raw(n_agents * WORDS_PER_AGENT)
    return np.asarray(raw, dtype=np.uint64).reshape(n_agents, WORDS_PER_AGENT)


def draw_words_per_agent(master_seed: int | str, agent_ids) -> np.ndarray:
    """**参照実装**(T4 の定義そのまま): 個体ごとに独立の Philox から引く。

    逐次ループ宣言(P4): 個体数ぶんのループ。テストと検証専用で、ランでは使わない。
    """
    ids = [int(a) for a in np.asarray(agent_ids).ravel().tolist()]
    out = np.empty((len(ids), WORDS_PER_AGENT), dtype=np.uint64)
    for row, aid in enumerate(ids):
        bg = philox(master_seed, SCHEDULE_DOMAIN, aid * BLOCKS_PER_AGENT)
        out[row] = bg.random_raw(WORDS_PER_AGENT)
    return out


def _spread(word: np.ndarray, lo: int, span: int) -> np.ndarray:
    """u64 語 → ``lo..lo+span-1`` の一様整数(mod・expedient=剰余バイアスは無視できる幅)。"""
    return (lo + (word % np.uint64(max(1, span))).astype(np.int64)).astype(np.int32)


@dataclass(frozen=True)
class MockWeeklySchedule:
    """合成日課(mock)。全て個体ごとの配列で持つ(個体オブジェクトを作らない)。

    Attributes:
        n_agents / n_cells: 規模。
        master_seed: 抽選の親シード。
        home_cell / work_cell / leisure_cell: 拠点セル(place_id 索引)。
        kind: ``AgentKind``(mock は 0..MOCK_KIND_COUNT-1)。
        initial_money: 初期所持金[円]。
        base_ticks: 形 ``(n, 5)`` の平日の境界 tick(0-1439・昇順)。
        weekend_ticks: 形 ``(n, 5)`` の休日の境界 tick。
        age / sex / direction_node: W16 母集団の素性(mock 単独では ``None``)。
        population_hash: W16 母集団の同定ハッシュ(``""``=母集団なし)。
    """

    n_agents: int
    n_cells: int
    master_seed: int | str
    home_cell: np.ndarray
    work_cell: np.ndarray
    leisure_cell: np.ndarray
    kind: np.ndarray
    initial_money: np.ndarray
    base_ticks: np.ndarray
    weekend_ticks: np.ndarray
    #: 以下は **W16 母集団を載せたときだけ**入る(mock 単独では None / "")。
    #: **学校セル**(W16 ``school_cell``・``-1``=学校なし)。C9b G5 の対象ヒント ``school``
    #: の解決先。mock 単独では ``None``=ヒントは効かない(行き先は現行のまま)。
    school_cell: np.ndarray | None = None
    age: np.ndarray | None = None
    sex: np.ndarray | None = None
    direction_node: np.ndarray | None = None
    population_hash: str = ""

    # ---- 1 日ぶんの取り出し ----
    def is_weekend(self, day_index: int) -> bool:
        """day 0 を月曜とみなす(expedient)。5,6=土日。"""
        return int(day_index) % 7 >= 5

    def boundary_ticks(self, day_index: int = 0) -> np.ndarray:
        """その日の境界 tick 配列 ``(n, 5)``。"""
        return self.weekend_ticks if self.is_weekend(day_index) else self.base_ticks

    def target_cell(self, day_index: int = 0) -> np.ndarray:
        """その日の「外出」先セル(平日=職場・休日=余暇先)。"""
        return self.leisure_cell if self.is_weekend(day_index) else self.work_cell

    def boundary_activities(self) -> np.ndarray:
        """境界ごとに始まる ``Activity``(全個体共通・形 ``(5,)``)。"""
        return np.array(
            [
                int(Activity.IDLE),  # 起床
                int(Activity.MOVING),  # 外出(職場/余暇先へ)
                int(Activity.SHOPPING),  # 昼(購入)
                int(Activity.MOVING),  # 帰宅
                int(Activity.SLEEPING),  # 就寝
            ],
            dtype=np.int8,
        )

    def events_of_day(self, day_index: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """その日の全境界を ``(tick 昇順の agent_id, 境界番号, tick)`` に平坦化する。

        run.py が tick ごとに ``np.searchsorted`` で切り出すための形。ループなし。
        """
        ticks = self.boundary_ticks(day_index)
        n, k = ticks.shape
        agent = np.repeat(np.arange(n, dtype=np.int64), k)
        slot = np.tile(np.arange(k, dtype=np.int64), n)
        flat = ticks.reshape(-1).astype(np.int64)
        order = np.lexsort((slot, agent, flat))  # tick 昇順・同 tick は agent→slot
        return agent[order], slot[order], flat[order]


def synthesize(
    n_agents: int,
    master_seed: int | str,
    n_cells: int,
    *,
    start_agent: int = 0,
) -> MockWeeklySchedule:
    """合成日課を作る(**mock 専用**)。

    Args:
        n_agents: 個体数。
        master_seed: manifest の ``master_seed``。
        n_cells: 世界のセル数(拠点セルの抽選範囲)。
        start_agent: 先頭の agent_id(既定 0)。

    Returns:
        ``MockWeeklySchedule``。
    """
    if n_cells <= 0:
        raise ValueError("n_cells は正")
    w = draw_words(master_seed, n_agents, start_agent=start_agent)
    if n_agents == 0:
        empty_i32 = np.empty(0, dtype=np.int32)
        return MockWeeklySchedule(
            0, n_cells, master_seed, empty_i32, empty_i32, empty_i32,
            np.empty(0, dtype=np.int8), empty_i32,
            np.empty((0, N_BOUNDARIES), dtype=np.int32),
            np.empty((0, N_BOUNDARIES), dtype=np.int32),
        )

    home = _spread(w[:, 0], 0, n_cells)
    work = _spread(w[:, 1], 0, n_cells)
    leisure = _spread(w[:, 2], 0, n_cells)
    # 指令以降(W16 で足した種別を含む)は mock では出さない。``len(AgentKind)`` を使うと
    # 種別を足したときに既存の mock 乱数列が動くので、定数 MOCK_KIND_COUNT で釘付ける。
    kind = (w[:, 3] % np.uint64(MOCK_KIND_COUNT)).astype(np.int8)
    money = _spread(w[:, 4], 2_000, 10_001)

    # 平日(expedient な時刻帯)
    wake = _spread(w[:, 5], 300, 181)  # 5:00-8:00
    depart = wake + _spread(w[:, 6], 30, 61)  # 起床 +30..90 分
    lunch = _spread(w[:, 7], 690, 121)  # 11:30-13:30
    ret = _spread(w[:, 5] >> np.uint64(13), 1_020, 241)  # 17:00-21:00
    sleep = _spread(w[:, 6] >> np.uint64(13), 1_320, 111)  # 22:00-23:50

    base = np.stack([wake, depart, lunch, ret, sleep], axis=1).astype(np.int32)
    # 休日: 起床+90 分・外出は遅く・帰宅は早い(expedient)
    wknd = base.copy()
    wknd[:, 0] = base[:, 0] + 90
    wknd[:, 1] = wknd[:, 0] + _spread(w[:, 7] >> np.uint64(11), 60, 121)
    wknd[:, 3] = base[:, 3] - _spread(w[:, 4] >> np.uint64(17), 60, 121)
    for arr in (base, wknd):
        # 厳密昇順を機械的に保証(逐次ループ宣言: 境界数 5 ぶん・個体数に比例しない)
        for j in range(1, N_BOUNDARIES):
            np.maximum(arr[:, j], arr[:, j - 1] + 1, out=arr[:, j])
        np.clip(arr, 0, _MINUTES_PER_DAY - 1, out=arr)
    return MockWeeklySchedule(
        n_agents=int(n_agents),
        n_cells=int(n_cells),
        master_seed=master_seed,
        home_cell=home,
        work_cell=work,
        leisure_cell=leisure,
        kind=kind,
        initial_money=money,
        base_ticks=base,
        weekend_ticks=wknd,
    )
