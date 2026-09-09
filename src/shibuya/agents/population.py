"""agents.population — W16 母集団(``w16_population.parquet``)の読み込みと二層抽出。

位置づけ
- **W16(build.pop)が作った資産を、ランが読むだけ**の口。層契約により ``agents`` は
  ``build`` を import しない(実行時に build を触らない)ので、Parquet を直接読む。
- 資産が無ければ ``None`` を返し、呼び出し側(``engine.run`` / ``shibuya.cli``)は
  従来の合成個体(``agents.schedule.synthesize``)へ落ちる。

二層抽出(決定台帳「母集団合成」6-b・答申 Q6-b)
    40 万 → n 体の縮尺を**構成比の一様な縮尺コピー**でやると、乗務員 1,299→16・指令 0 になり
    「街が動かない」。そこで
      1. **定員先取り層**(縮尺しない): 答申 §Q6-b の定義=「乗務員・指令・議員・警察/消防
         など**機能に必要な最小定員**」。判定は W16 の ``duty_role`` 列 ∈ ``RESERVED_ROLES``
         (下表)。統計的代表性の対象ではない=expedient。
      2. **統計層**(縮尺する): 残り(タクシー運転手・路上生活者・ティッシュ配り・配信者
         などの職務者を**含む**)を ``(種別 × 年齢階級 × 性別)`` で層化し、最大剰余法で
         比例配分する(単純無作為ではない=希少セルの消失を防ぐ)。
    乱数は ``core.rng`` の Philox(ドメイン ``w16.sample.*``)だけ。同 seed 同結果。

    2026-09-09 の訂正(C5-a 層2レビュー 中-1): 旧実装は「プール層 L5 の全件 ∪ 指令」を
    定員先取り層にしていた=1,316 体(5,000 体ランの 26%)。L5 には機能定員でない役割が
    混ざるので、**役割名の表**へ絞った。

逐次ループ宣言(P4)
- ``sample_population``: **層数**(種別 9 × 年齢階級 16 × 性別 2 のうち非空セル)ぶんのループ。
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
    "DUTY_POOL_LAYER",
    "RESERVED_ROLES",
    "RESERVED_KINDS",
    "Population",
    "population_available",
    "load_population",
    "sample_population",
]

#: W16 の出力ファイル名(``<world_dir>/w16_population.parquet``)。
POPULATION_FILE: Final[str] = "w16_population.parquet"

#: 年齢階級の下端(``build.pop.w16_population.AGE_EDGES`` と同じ・層化抽出の層)。
#: 2026-09-09 に 15 → **16 階級**(0-4 … 70-74・75+)へ拡張(国勢調査の全階級を再取得)。
AGE_EDGES: Final[np.ndarray] = np.array(
    [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75], dtype=np.int64
)

#: 職務者のプール層(L5)。**定員先取り層の判定には使わない**(役割で決める)。
DUTY_POOL_LAYER: Final[int] = 5

#: **定員先取り層になる役割**(W16 の ``duty_role`` 列の値)。答申 §Q6-b「機能に必要な
#: 最小定員」の読み: 公共交通の運行(鉄道乗務・駅務・バス)・運行/警備の指令・治安と救急
#: (警察/消防)・制度側(議員)。ここに無い職務者(タクシー運転手・路上生活者・
#: ティッシュ配り・配信者・清掃・納品・街頭など)は**統計層**=縮尺の対象。
#: **expedient**: 役割ごとの実定員は公表値が無く、v1 プール L5 の在庫体数をそのまま
#: 「最小定員」とみなしている(体数は登録簿に実測を記録)。
RESERVED_ROLES: Final[tuple[str, ...]] = (
    "駅員",          # 鉄道の駅務
    "電車運転士",    # 鉄道乗務
    "車掌",          # 鉄道乗務
    "バス運転士",    # 路線バスの運行
    "指令",          # 運行/警備の指令(W16 が新規生成)
    "警察官",        # 治安
    "消防士",        # 消防
    "救急隊員",      # 消防(救急)
    "議員",          # 制度側(渋谷区議会定数 34)
)
#: 役割名が空でも定員先取り層に入れる種別(``AgentKind.DISPATCHER``=素材なしの指令)。
#: ``duty_role`` の無い旧資産を読んだときの保険でもある。
RESERVED_KINDS: Final[tuple[int, ...]] = (4,)

_COLUMNS: Final[tuple[str, ...]] = (
    "agent_id", "kind", "purpose", "age", "sex", "home_cell", "work_cell", "school_cell",
    "direction_node", "household_id", "home_building", "org_id", "pool_layer", "pool_index",
    "synthetic", "is_foreign",
)
#: W16 が publish する役割名の列(旧資産には無いので**任意**扱いで読む)。
_DUTY_ROLE_COLUMN: Final[str] = "duty_role"


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
    #: 職務の役割名(``""``=職務者でない)。旧資産(列が無い)では ``None``。
    duty_role: np.ndarray | None = None

    def __len__(self) -> int:
        return int(self.kind.size)

    @property
    def n(self) -> int:
        return int(self.kind.size)

    # ---- 派生 ----
    @property
    def reserved_mask(self) -> np.ndarray:
        """定員先取り層(``RESERVED_ROLES`` の役割 ∪ 指令)の bool マスク。

        ``duty_role`` を持たない資産では**指令だけ**になる(旧 W16 出力への保険)。
        """
        mask = np.isin(self.kind, np.asarray(RESERVED_KINDS, dtype=self.kind.dtype))
        if self.duty_role is not None:
            roles = np.asarray(self.duty_role, dtype=object)
            mask = mask | np.isin(roles, np.asarray(RESERVED_ROLES, dtype=object))
        return mask

    def counts_by_duty_role(self) -> dict[str, int]:
        """役割名 → 体数(``""`` は除く)。定員先取り層の内訳を報告するための口。"""
        if self.duty_role is None:
            return {}
        roles = np.asarray(self.duty_role, dtype=object).astype(str)
        roles = roles[roles != ""]
        if roles.size == 0:
            return {}
        vals, cnt = np.unique(roles, return_counts=True)
        return {str(v): int(c) for v, c in zip(vals.tolist(), cnt.tolist())}

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
            duty_role=(
                None if self.duty_role is None
                else np.asarray(self.duty_role, dtype=object)[rows]
            ),
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
    have_role = _DUTY_ROLE_COLUMN in pq.read_schema(path).names
    want = list(_COLUMNS) + ([_DUTY_ROLE_COLUMN] if have_role else [])
    table = pq.read_table(path, columns=want)
    cols = {name: np.asarray(table.column(name).to_numpy(zero_copy_only=False))
            for name in want}
    pop = Population(
        source=path,
        duty_role=(
            np.asarray(cols[_DUTY_ROLE_COLUMN], dtype=object) if have_role else None
        ),
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
