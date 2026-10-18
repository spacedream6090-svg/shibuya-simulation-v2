"""engine.contact.book — 宛先(連絡先とグループ)の読み口(第 6 期 6-4 C1・決定 10-12 §4-4 CT5・口の約束 1-7 の器)。

正: CT5 (c)「個人の連絡先は、関係の記憶(§4-6)に手段ごとの印で持つ。家族と職場は初めから持たせる。グループの一覧を持つ。家族と
職場は実データ」・CT4「体の無い人は C1 では入れない(宣言)」。1-7 の器(``engine.tools.contacts`` の印・``engine.tools.groups``
の一覧)をそのまま読む(状態は持たない=書く口は無い・連絡先の交換は本人の行動=本段に無い=つなぎの台帳 ``DOC-ct-c1-book-*``)。

個人の連絡先(手段のビット ``engine.tools.contacts.MEANS_BITS`` ごと)の出どころ(ランの構成で 1 つ):

1. 関係の層(``engine.relations.RelationLayer``・``--relations on``): 辺の欄の相手と連絡先の印(``contact_flags``=家族と職場は
   初めの辺の種別から)。辺の強さ(思い出せるか)は見ない(電話の連絡先は思い出せなくても残る)。
2. 人も記憶の腕(``engine.relations_people.PeopleRelationLayer``): 印の配列を持たない=思い浮かぶ人(``edges``=A ≥ τ)の関係の
   種類から印を作る(``flags_from_kinds``)=仮採用。
3. 関係の層の無いラン: グループの一覧の家族(同じ世帯の体)だけ=印は家族の初めの印。職場の 1 対 1 の連絡先は持たない(職場は
   グループのメッセージだけ=仮採用・職場の全員を連絡先にしない)。

グループ: グループの一覧(``GroupList``=W16 の世帯と事業所)のうち、その体が成員の行(家族・職場)。

体の無い人(4-1 段 7 の ``bodiless_contact`` ほか): 宛先はいつもランの体(0 ≤ 番号 < 体の数)だけ=それ以外の番号は落として数える
(``bodiless_dropped``)。

逐次ループ宣言: :meth:`ContactBook.personal` は 1 体の辺の欄の数ぶん(≤ k=15 か器の行の幅)・組み立ては配列演算で 1 回。
"""

from __future__ import annotations

from typing import Any

import numpy as np

from shibuya.engine.tools import contacts as _CT
from shibuya.engine.tools.groups import FAMILY, GROUP_KINDS

__all__ = ["ContactBook"]


class ContactBook:
    """宛先の読み口(関係の層・グループの一覧を読むだけ)。"""

    def __init__(self, n_agents: int, *, groups: Any = None, rel_layer: Any = None) -> None:
        self.n = int(n_agents)
        self.groups = groups
        self.rel_layer = rel_layer
        self.bodiless_dropped = 0
        # 体 → グループの行(CSR・体の番号の昇順 → 行の番号の昇順)
        if groups is not None and len(groups):
            gk = np.asarray(groups.kinds, dtype=np.int64)
            nm = groups.n_members()
            rows = np.repeat(np.arange(len(groups), dtype=np.int64), nm)
            mem = np.concatenate([np.asarray(groups.members(g), dtype=np.int64) for g in range(len(groups))])
            order = np.lexsort((rows, mem))
            self._g_mem, self._g_row = mem[order], rows[order]
            self._g_kind = gk
        else:
            self._g_mem = self._g_row = np.zeros(0, dtype=np.int64)
            self._g_kind = np.zeros(0, dtype=np.int64)

    def source(self) -> str:
        """個人の連絡先の出どころ(manifest の設定)。"""
        from shibuya.engine.relations_people import PeopleRelationLayer

        r = self.rel_layer
        if r is None:
            return "groups.family"
        return "relations.people_memory" if isinstance(r, PeopleRelationLayer) else "relations.contact_flags"

    def groups_of(self, agent: int) -> tuple[int, ...]:
        """体が成員のグループの行(番号の昇順)。"""
        a = int(agent)
        lo, hi = np.searchsorted(self._g_mem, [a, a + 1])
        return tuple(int(x) for x in self._g_row[lo:hi])

    def group_kind(self, g: int) -> str:
        return GROUP_KINDS[int(self._g_kind[int(g)])]

    def members(self, g: int) -> tuple[int, ...]:
        return tuple(int(x) for x in np.asarray(self.groups.members(int(g)), dtype=np.int64)) if self.groups is not None else ()

    def _bodies(self, ids: np.ndarray, agent: int) -> np.ndarray:
        ids = np.asarray(ids, dtype=np.int64)
        ok = (ids >= 0) & (ids < self.n) & (ids != int(agent))
        bad = int(np.count_nonzero((ids >= self.n) | ((ids < 0) & (ids != -1))))
        if bad:
            self.bodiless_dropped += bad
        return np.unique(ids[ok])

    def personal(self, agents: Any, agent: int, means_bit: int, step: int) -> tuple[int, ...]:
        """体の個人の連絡先のうち手段のビット ``means_bit`` の印のある相手(番号の昇順・体だけ)。"""
        from shibuya.engine.relations_people import PeopleRelationLayer

        a = int(agent)
        r = self.rel_layer
        if r is None:
            fam = [g for g in self.groups_of(a) if self.group_kind(g) == FAMILY]
            if not fam or not (int(_CT.INITIAL_FLAGS_BY_KIND[_CT.KIND_HOUSEHOLD]) & int(means_bit)):
                return ()
            ids = np.concatenate([np.asarray(self.groups.members(g), dtype=np.int64) for g in fam])
            return tuple(int(x) for x in self._bodies(ids, a))
        if isinstance(r, PeopleRelationLayer):
            e = r.edges(agents, a, int(step))
            flags = _CT.flags_from_kinds(np.asarray(e.kind, dtype=np.int64), np.asarray(e.partner, dtype=np.int64))
            ids = np.asarray(e.partner, dtype=np.int64)[(flags & int(means_bit)) != 0]
            return tuple(int(x) for x in self._bodies(ids, a))
        partner = np.asarray(r._partner_rows(agents, np.asarray([a]))[0], dtype=np.int64)
        flags = np.asarray(r.contact_flags[a], dtype=np.int64)
        ids = partner[(flags & int(means_bit)) != 0]
        return tuple(int(x) for x in self._bodies(ids, a))
