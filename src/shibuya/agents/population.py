"""agents.population — W16 母集団(``w16_population.parquet``)の読み込みと二層抽出。

位置づけ
- **W16(build.pop)が作った資産を、ランが読むだけ**の口。層契約により ``agents`` は
  ``build`` を import しない(実行時に build を触らない)ので、Parquet を直接読む。
- 資産が無ければ ``None`` を返し、呼び出し側(``engine.run`` / ``shibuya.cli``)は
  従来の合成個体(``agents.schedule.synthesize``)へ落ちる。

二層抽出(決定台帳「母集団合成」6-b・答申 Q6-b)
    40 万 → n 体の縮尺を**構成比の一様な縮尺コピー**でやると、乗務員 1,299→16・指令 0 になり
    「街が動かない」。そこで
      1. **定員先取り層**(縮尺しない): 職務者(プール層 L5=乗務・駅務・警察/消防・議員)と
         指令。機能に必要な最小定員をそのまま入れる。統計的代表性の対象ではない=expedient。
      2. **統計層**(縮尺する): 残りを ``(種別 × 年齢階級 × 性別)`` で層化し、最大剰余法で
         比例配分する(単純無作為ではない=希少セルの消失を防ぐ)。
    乱数は ``core.rng`` の Philox(ドメイン ``w16.sample.*``)だけ。同 seed 同結果。

逐次ループ宣言(P4)
- ``sample_population``: **層数**(種別 9 × 年齢階級 15 × 性別 2 のうち非空セル)ぶんのループ。
  体数には比例しない。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence

import numpy as np

from shibuya.core.hashing import blake3_hex
from shibuya.core.rng import stream

__all__ = [
    "POPULATION_FILE",
    "AGE_EDGES",
    "RESERVED_POOL_LAYER",
    "Population",
    "population_available",
    "load_population",
    "sample_population",
]

#: W16 の出力ファイル名(``<world_dir>/w16_population.parquet``)。
POPULATION_FILE: Final[str] = "w16_population.parquet"

#: 年齢階級の下端(``build.pop.w16_population.AGE_EDGES`` と同じ・層化抽出の層)。
AGE_EDGES: Final[np.ndarray] = np.array(
    [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70], dtype=np.int64
)

#: 定員先取り層になるプール層(L5=職務者。W16 の ``pool_layer`` 列)。
RESERVED_POOL_LAYER: Final[int] = 5
#: 定員先取り層になる種別(``AgentKind.DISPATCHER``。素材が無く新規生成された指令)。
RESERVED_KINDS: Final[tuple[int, ...]] = (4,)

_COLUMNS: Final[tuple[str, ...]] = (
    "agent_id", "kind", "purpose", "age", "sex", "home_cell", "work_cell", "school_cell",
    "direction_node", "household_id", "home_building", "org_id", "pool_layer", "pool_index",
    "synthetic", "is_foreign",
)


@dataclass(frozen=True)
class Population:
    """W16 母集団の列(行順=``agent_id`` の昇順)。

    Attributes:
        source: 読み出したファイル(``None``=部分集合)。
        source_agent_id: 元の ``agent_id``(抽出後も辿れるように残す)。
    """

    source: Path | None
    source_agent_id: np.ndarray
    kind: np.ndarray
    purpose: np.ndarray
    age: np.ndarray
    sex: np.ndarray
    home_cell: np.ndarray
    work_cell: np.ndarray
    school_cell: np.ndarray
    direction_node: np.ndarray
    household_id: np.ndarray
    home_building: np.ndarray
    org_id: np.ndarray
    pool_layer: np.ndarray
    pool_index: np.ndarray
    synthetic: np.ndarray
    is_foreign: np.ndarray

    def __len__(self) -> int:
        return int(self.kind.size)

    @property
    def n(self) -> int:
        return int(self.kind.size)

    # ---- 派生 ----
    @property
    def reserved_mask(self) -> np.ndarray:
        """定員先取り層(職務者+指令)の bool マスク。"""
        return (self.pool_layer == RESERVED_POOL_LAYER) | np.isin(
            self.kind, np.asarray(RESERVED_KINDS, dtype=self.kind.dtype)
        )

    def start_cell(self, fallback: int = -1) -> np.ndarray:
        """ランの初期セル。

        W17(週次スケジュール)が入るまでの繋ぎ(expedient): 自宅セルが無い体
        (域外常住の通勤・通学・来街・職務)は **勤務→通学→``fallback``** の順に置く。
        ``fallback`` は呼び出し側が「街の入口」に当たるセル(既定 −1=場外)を渡す。
        """
        cell = self.home_cell.copy()
        need = cell < 0
        cell = np.where(need & (self.work_cell >= 0), self.work_cell, cell)
        need = cell < 0
        cell = np.where(need & (self.school_cell >= 0), self.school_cell, cell)
        return np.where(cell < 0, int(fallback), cell).astype(np.int32)

    def age_bin(self) -> np.ndarray:
        return np.searchsorted(AGE_EDGES[1:], self.age, side="right").astype(np.int64)

    def counts_by_kind(self) -> dict[int, int]:
        vals, cnt = np.unique(self.kind, return_counts=True)
        return {int(v): int(c) for v, c in zip(vals, cnt)}

    def population_hash(self) -> str:
        """母集団の同定ハッシュ(状態ハッシュ T1/T2 に混ぜる)。"""
        h_parts: list[bytes] = [b"shibuya.agents.population/v1", str(self.n).encode("ascii")]
        for name in ("kind", "age", "sex", "home_cell", "work_cell", "school_cell",
                     "direction_node", "org_id", "source_agent_id"):
            arr = np.ascontiguousarray(getattr(self, name))
            h_parts.append(name.encode("ascii"))
            h_parts.append(arr.dtype.str.encode("ascii"))
            h_parts.append(arr.tobytes())
        return blake3_hex(b"\x1f".join(h_parts))

    def take(self, rows: np.ndarray) -> "Population":
        """行の部分集合(順序は ``rows`` のまま)。"""
        rows = np.asarray(rows, dtype=np.int64)
        return Population(
            source=self.source,
            **{
                name: np.asarray(getattr(self, name))[rows]
                for name in (
                    "source_agent_id", "kind", "purpose", "age", "sex", "home_cell",
                    "work_cell", "school_cell", "direction_node", "household_id",
                    "home_building", "org_id", "pool_layer", "pool_index", "synthetic",
                    "is_foreign",
                )
            },
        )


def population_available(world_dir: str | Path | None) -> bool:
    """``<world_dir>/w16_population.parquet`` があるか。"""
    if world_dir is None:
        return False
    return (Path(world_dir) / POPULATION_FILE).exists()


def load_population(
    world_dir: str | Path | None,
    n: int | None = None,
    seed: int | str = 1,
    *,
    n_cells: int | None = None,
) -> Population | None:
    """W16 母集団を読む。資産が無ければ ``None``。

    Args:
        world_dir: 世界資産ディレクトリ(``data/world/v2``)。
        n: 体数。``None`` で全件、整数なら ``sample_population`` で二層抽出。
        seed: 抽出の親シード(``core.rng`` の master_seed)。
        n_cells: 世界のセル数。与えると範囲外のセル索引を検出して例外にする
            (合成小世界に実データの母集団を載せる事故を止める)。

    Raises:
        ValueError: セル索引が ``n_cells`` の範囲外(世界と母集団の食い違い)。
    """
    if not population_available(world_dir):
        return None
    import pyarrow.parquet as pq  # 遅延 import(母集団が無いランに読み込ませない)

    path = Path(world_dir) / POPULATION_FILE
    table = pq.read_table(path, columns=list(_COLUMNS))
    cols = {name: np.asarray(table.column(name).to_numpy(zero_copy_only=False))
            for name in _COLUMNS}
    pop = Population(
        source=path,
        source_agent_id=cols["agent_id"].astype(np.int64),
        kind=cols["kind"].astype(np.int8),
        purpose=cols["purpose"].astype(np.int8),
        age=cols["age"].astype(np.uint8),
        sex=cols["sex"].astype(np.int8),
        home_cell=cols["home_cell"].astype(np.int32),
        work_cell=cols["work_cell"].astype(np.int32),
        school_cell=cols["school_cell"].astype(np.int32),
        direction_node=cols["direction_node"].astype(np.int32),
        household_id=cols["household_id"].astype(np.int32),
        home_building=cols["home_building"].astype(np.int32),
        org_id=cols["org_id"].astype(np.int32),
        pool_layer=cols["pool_layer"].astype(np.int8),
        pool_index=cols["pool_index"].astype(np.int32),
        synthetic=cols["synthetic"].astype(bool),
        is_foreign=cols["is_foreign"].astype(bool),
    )
    if n_cells is not None:
        for name in ("home_cell", "work_cell", "school_cell"):
            arr = getattr(pop, name)
            if arr.size and int(arr.max()) >= int(n_cells):
                raise ValueError(
                    f"母集団の {name} が世界のセル数({n_cells})を超える"
                    f"(最大 {int(arr.max())})。世界資産と母集団の版が違う"
                )
    if n is None or n >= pop.n:
        return pop
    return sample_population(pop, n, seed)


def sample_population(pop: Population, n: int, seed: int | str = 1) -> Population:
    """二層抽出(定員先取り層+統計層)。同 seed 同結果。

    Args:
        pop: 全体。
        n: 目標体数。
        seed: ``core.rng`` の master_seed。

    Returns:
        ``agent_id`` 昇順に並べ直した部分集合。

    Raises:
        ValueError: ``n`` が負。

    Note:
        ``n`` が定員先取り層より小さいときは、定員先取り層から ``n`` 体だけを取る
        (統計層は 0 体)。この場合「街が動く」保証は失われるので呼び出し側が判断する。

    Example:
        >>> import numpy as np
        >>> z = np.zeros(10, dtype=np.int32)
        >>> p = Population(None, np.arange(10), np.zeros(10, np.int8), np.zeros(10, np.int8),
        ...                np.full(10, 30, np.uint8), np.zeros(10, np.int8), z, z, z, z, z, z, z,
        ...                np.ones(10, np.int8), z, np.zeros(10, bool), np.zeros(10, bool))
        >>> len(sample_population(p, 4, seed=7))
        4
        >>> (sample_population(p, 4, seed=7).source_agent_id
        ...  == sample_population(p, 4, seed=7).source_agent_id).all()
        np.True_
    """
    n = int(n)
    if n < 0:
        raise ValueError("n は 0 以上")
    if n >= pop.n:
        return pop
    reserved = np.flatnonzero(pop.reserved_mask)
    if n <= reserved.size:
        order = stream(seed, "w16.sample.reserved").permutation(reserved.size)[:n]
        rows = np.sort(reserved[order])
        return pop.take(rows)

    rest = np.flatnonzero(~pop.reserved_mask)
    want = n - int(reserved.size)
    strata_key = (
        pop.kind[rest].astype(np.int64) * (AGE_EDGES.size * 2)
        + pop.age_bin()[rest] * 2
        + np.clip(pop.sex[rest].astype(np.int64), 0, 1)
    )
    uniq, inverse, counts = np.unique(strata_key, return_inverse=True, return_counts=True)
    quota = _largest_remainder(counts.astype(np.float64), want)
    picked: list[np.ndarray] = []
    for s in range(uniq.size):  # 逐次ループ宣言(P4): 層数ぶん(体数に比例しない)
        take = int(quota[s])
        if take <= 0:
            continue
        members = rest[inverse == s]
        order = stream(seed, "w16.sample.stratum", int(uniq[s])).permutation(members.size)
        picked.append(members[order[:take]])
    rows = np.sort(np.concatenate([reserved, *picked])) if picked else np.sort(reserved)
    return pop.take(rows)


def _largest_remainder(weights: Sequence[float], total: int) -> np.ndarray:
    """最大剰余法(``build.pop.fitting.largest_remainder`` と同じ規約・層契約のため二重定義)。"""
    w = np.asarray(weights, dtype=np.float64).ravel()
    total = int(total)
    if w.size == 0:
        return np.zeros(0, dtype=np.int64)
    s = w.sum()
    if s <= 0:
        w = np.ones_like(w)
        s = w.sum()
    exact = w * (total / s)
    base = np.floor(exact).astype(np.int64)
    rest = total - int(base.sum())
    if rest > 0:
        frac = exact - base
        order = np.lexsort((np.arange(w.size), -frac))
        base[order[:rest]] += 1
    # 層の在庫を超えないように押し戻す(超過分は在庫の余っている層へ)
    cap = np.asarray(weights, dtype=np.int64)
    over = np.maximum(base - cap, 0)
    if over.sum():
        base = np.minimum(base, cap)
        left = int(over.sum())
        room = cap - base
        for i in np.argsort(-room):
            add = min(left, int(room[i]))
            base[i] += add
            left -= add
            if left <= 0:
                break
    return base
