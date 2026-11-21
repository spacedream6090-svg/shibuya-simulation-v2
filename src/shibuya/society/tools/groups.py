"""engine.tools.groups — グループの一覧(第 1 期 1-7 C0・CT10・CT5 の「グループの一覧を持つ」)。

決定 10-12 §4-4 CT5: グループの一覧を持つ。家族と職場は実データ、友人は慣らし期間で本人たちが作る(友人の分は後の段)。

- 家族=W16 の世帯(``Population.household_id``・``w16_households.parquet`` の行)・職場=W16 の事業所(``Population.org_id``
  =W6 の組織台帳 ``w6_org.parquet`` の行)。**行の数=世帯の数+事業所の数**(ランの体に 1 人でも成員がいるもの)。全母集団
  (390,067 体)では 27,404+9,872=37,276 行(試験 ``tests/engine/tools/test_c0_groups_from_w16.py`` が parquet と突き合わせる)。
- 形は CSR(行ごとの種類・出どころの番号・成員の始まりの位置=行の数+1 個と成員の体の番号)。並び=家族(世帯の番号の昇順)→ 職場(組織の
  番号の昇順)・成員は体の番号の昇順。
- 書く口は無い(組み立ての ``from_population`` だけが作る・中身は名を変えた slot の読み取り専用の配列)。C0 では誰も読まない
  (読み手は manifest の ``tools.groups``)。グループのメッセージは C1(計画 6-4)。
- 範囲の外の家族(同じ世帯で W16 の体になっていない人)と、ランの体に成員のいない世帯・事業所は入らない(体の無い人は C1 に
  入れない=決定 CT4 の宣言)。

逐次ループ宣言: なし(組み立ては配列演算・1 回)。
"""

from __future__ import annotations

from typing import Any, Final

import numpy as np

__all__ = ["FAMILY", "WORKPLACE", "GROUP_KINDS", "GroupList"]

FAMILY: Final[str] = "家族"
WORKPLACE: Final[str] = "職場"
#: グループの種類(並びが列のコード)。
GROUP_KINDS: Final[tuple[str, ...]] = (FAMILY, WORKPLACE)
#: 種類 → 出どころ(manifest の記録)。
_SOURCES: Final[tuple[str, ...]] = ("w16_population.household_id", "w16_population.org_id")


def _ro(a: np.ndarray) -> np.ndarray:
    a = np.ascontiguousarray(a)
    a.flags.writeable = False
    return a


class _GroupStore:
    """一覧の中身(``GroupList`` の名を変えた slot ``_GroupList__grp`` だけが持つ)。"""

    __slots__ = ("kind", "source_id", "offsets", "members", "n_agents")

    def __init__(self, kind: np.ndarray, source_id: np.ndarray, offsets: np.ndarray, members: np.ndarray,
                 n_agents: int) -> None:
        self.kind = _ro(kind.astype(np.int8))
        self.source_id = _ro(source_id.astype(np.int64))
        self.offsets = _ro(offsets.astype(np.int64))
        self.members = _ro(members.astype(np.int64))
        self.n_agents = int(n_agents)


def _groups_of(ids: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """体ごとの番号(-1=無し)→ (出どころの番号の昇順・始まりの位置・成員=体の番号)。"""
    ids = np.asarray(ids, dtype=np.int64)
    agents = np.flatnonzero(ids >= 0)
    if agents.size == 0:
        return np.zeros(0, np.int64), np.zeros(1, np.int64), np.zeros(0, np.int64)
    key = ids[agents]
    order = np.lexsort((agents, key))       # 番号の昇順 → 体の番号の昇順
    key_s = key[order]
    uniq, counts = np.unique(key_s, return_counts=True)
    offsets = np.concatenate(([0], np.cumsum(counts))).astype(np.int64)
    return uniq.astype(np.int64), offsets, agents[order].astype(np.int64)


class GroupList:
    """グループの一覧(家族と職場)。書く口は無い(``from_population`` で作る)。"""

    __slots__ = ("__grp",)

    def __init__(self, *, household_id: np.ndarray, org_id: np.ndarray) -> None:
        try:  # 検収 L2: 作った後に __init__ を呼び直して中身を入れ替えない
            object.__getattribute__(self, "_GroupList__grp")
        except AttributeError:
            pass
        else:
            raise RuntimeError("GroupList は作った後に __init__ を呼び直せない(中身を入れ替えない)")
        hh = np.asarray(household_id, dtype=np.int64)
        org = np.asarray(org_id, dtype=np.int64)
        if hh.shape != org.shape or hh.ndim != 1:
            raise ValueError("household_id と org_id は同じ長さの 1 次元(体ごと)")
        h_ids, h_off, h_mem = _groups_of(hh)
        o_ids, o_off, o_mem = _groups_of(org)
        kind = np.concatenate((np.zeros(h_ids.size, np.int8), np.ones(o_ids.size, np.int8)))
        source_id = np.concatenate((h_ids, o_ids))
        offsets = np.concatenate((h_off[:-1], o_off + h_off[-1]))
        members = np.concatenate((h_mem, o_mem))
        object.__setattr__(self, "_GroupList__grp", _GroupStore(kind, source_id, offsets, members, hh.size))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"GroupList は組み立ての後に書けない({name})")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"GroupList は組み立ての後に書けない({name})")

    @classmethod
    def from_population(cls, pop: Any, n_agents: int | None = None) -> "GroupList":
        """W16 の母集団(``agents.population.Population``・行=体の番号の順)の先頭 ``n_agents`` 体から作る。"""
        n = int(pop.n if n_agents is None else min(int(n_agents), int(pop.n)))
        return cls(household_id=np.asarray(pop.household_id)[:n], org_id=np.asarray(pop.org_id)[:n])

    @classmethod
    def empty(cls, n_agents: int = 0) -> "GroupList":
        z = np.full(int(n_agents), -1, dtype=np.int64)
        return cls(household_id=z, org_id=z)

    # ------------------------------------------------------------------ 読む口
    def __len__(self) -> int:
        return int(self.__grp.kind.size)

    @property
    def n_family(self) -> int:
        return int(np.count_nonzero(self.__grp.kind == 0))

    @property
    def n_workplace(self) -> int:
        return int(np.count_nonzero(self.__grp.kind == 1))

    @property
    def kinds(self) -> np.ndarray:
        """行ごとの種類のコード(0=家族・1=職場・読み取り専用)。"""
        return self.__grp.kind

    @property
    def source_ids(self) -> np.ndarray:
        """行ごとの出どころの番号(家族=世帯の番号・職場=組織の番号・読み取り専用)。"""
        return self.__grp.source_id

    def kind_of(self, g: int) -> str:
        return GROUP_KINDS[int(self.__grp.kind[int(g)])]

    def members(self, g: int) -> np.ndarray:
        """行 ``g`` の成員の体の番号(昇順・読み取り専用)。"""
        st = self.__grp
        g = int(g)
        if not 0 <= g < st.kind.size:
            raise IndexError(g)
        return st.members[int(st.offsets[g]):int(st.offsets[g + 1])]

    def n_members(self) -> np.ndarray:
        """行ごとの成員の数(``offsets`` は行の数+1 個=最後は成員の総数)。"""
        return np.diff(self.__grp.offsets).astype(np.int64)

    def tally(self) -> dict[str, Any]:
        """manifest の ``tools.groups``。"""
        st = self.__grp
        nm = self.n_members()
        fam = st.kind == 0
        return {
            "rows": len(self),
            "family": self.n_family,
            "workplace": self.n_workplace,
            "members": {FAMILY: int(nm[fam].sum()), WORKPLACE: int(nm[~fam].sum())},
            "max_members": {FAMILY: int(nm[fam].max()) if fam.any() else 0,
                            WORKPLACE: int(nm[~fam].max()) if (~fam).any() else 0},
            "source": {FAMILY: _SOURCES[0], WORKPLACE: _SOURCES[1]},
            "n_agents": st.n_agents,
            "bytes": int(st.kind.nbytes + st.source_id.nbytes + st.offsets.nbytes + st.members.nbytes),
        }
