"""engine.contact.book — 宛先(連絡先とグループ)の持ち主(第 6 期 6-4 C1・C2・決定 10-12 §4-4 CT5・口の約束 1-7 の器)。

正: CT5 (c)「個人の連絡先は、関係の記憶(§4-6)に手段ごとの印で持つ。家族と職場は初めから持たせる。店や組織の番号は場所の表の側。
店の番号を調べる(検索・看板・地図)、保存する、連絡先を交換する(「LINE 交換しよう」)は本人の行動。グループの一覧を持つ。家族と
職場は実データ、友人は慣らし期間で本人たちが作る。交換の頻度は空欄で、計器だけ」・CT4「体の無い人は C1 では入れない(宣言)」。
1-7 の器(``engine.tools.contacts`` の印・``engine.tools.groups`` の一覧・``engine.tools.places`` の店の番号の表)を読む。

個人の連絡先(手段のビット ``engine.tools.contacts.MEANS_BITS`` ごと)の出どころ(ランの構成で 1 つ)+〔C2〕本人が交換した連絡先:

1. 関係の層(``engine.relations.RelationLayer``・``--relations on``): 辺の欄の相手と連絡先の印(``contact_flags``=家族と職場は
   初めの辺の種別から)。辺の強さ(思い出せるか)は見ない(電話の連絡先は思い出せなくても残る)。
2. 人も記憶の腕(``engine.relations_people.PeopleRelationLayer``): 印の配列を持たない=思い浮かぶ人(``edges``=A ≥ τ)の関係の
   種類から印を作る(``flags_from_kinds``)=仮採用。
3. 関係の層の無いラン: グループの一覧の家族(同じ世帯の体)だけ=印は家族の初めの印。職場の 1 対 1 の連絡先は持たない(職場は
   グループのメッセージだけ=仮採用・職場の全員を連絡先にしない)。
4. 〔C2〕本人が交換した連絡先 ``_exchanged``(体 → 相手 → 手段のビット)。対面の会話の番で本人が持ちかけ・相手が応じたときだけ
   両方の帳に足す(``engine.contact.layer``)。関係の層の辺の欄(k=15)の外の相手も持てる=関係の記憶の側の手段の印の写し
   (関係の層の欄に書くのは §4-6 の段=仮採用)。

グループ: グループの一覧(``GroupList``=W16 の世帯と事業所=実データ)のうち、その体が成員の行(家族・職場)+〔C2〕本人たちが
作った友人のグループ ``_made``(番号 → ``[作った人, 成員の列]``・番号=実データの行の数の後ろの通し番号 ``_made_next``)と、体 →
成員のグループの索引 ``_member_of``(``groups_of`` を作ったグループの数で回さない=日数で重くならない)。作る・招く・入る・断る・
抜けるは本人の判断(``engine.contact.layer``)。〔検収 L7〕抜けて成員が 0 人になったグループは無くなる(物理=誰もいないグループは
無い・そのグループへの招待も消える)。家族と職場の行は実データのまま(抜けない・招かない)。招待は ``_invites``(体 → グループの
番号の列=招かれた体が画面を見たときに答える)。

〔C2〕店の番号: 場所の表(``engine.tools.places.PhoneTable``=W6 の POI の行の欄・本段は空欄=つなぎ ``BR-PHONE-TABLE-BLANK``)を
読み、本人が調べて保存した店の番号 ``_places``(体 → POI の番号の列)を持つ(空欄の間は誰も調べられない=0)。

体の無い人(4-1 段 7 の ``bodiless_contact`` ほか): 宛先はいつもランの体(0 ≤ 番号 < 体の数)だけ=それ以外の番号は落として数える
(``bodiless_dropped``)。

状態台帳: 腕の行 ``CT1B``(``_exchanged``・``_made``・``_made_next``・``_member_of``・``_invites``・``_places``=behavior・required)・計数 ``bodiless_dropped``
は行 ``CT1M``(diag)。

逐次ループ宣言: :meth:`ContactBook.personal` は 1 体の辺の欄の数ぶん(≤ k=15 か器の行の幅)+交換した相手の数ぶん・
:meth:`groups_of` はその体が成員のグループの数ぶん(索引)・組み立ては配列演算で 1 回。
"""

from __future__ import annotations

from typing import Any, Final

import numpy as np

from shibuya.engine.contact.arm import LEDGER_ARM
from shibuya.engine.tools import contacts as _CT
from shibuya.engine.tools.groups import FAMILY, GROUP_KINDS

__all__ = ["ContactBook", "FRIEND"]

#: 〔C2〕本人たちが作るグループの種類の語(実データの家族・職場の外)。
FRIEND: Final[str] = "友人"


class ContactBook:
    """宛先の持ち主(関係の層・グループの一覧を読む+〔C2〕本人が交換した連絡先・作ったグループ・招待・調べた店の番号)。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

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
        #: 実データのグループの行の数(作ったグループの番号はこの後ろ)。
        self._n_static = 0 if groups is None else int(len(groups))
        # ---- 〔C2〕本人の行動で動く帳(腕の行 CT1B) ----
        self._exchanged: dict[int, dict[int, int]] = {}
        self._made: dict[int, list[Any]] = {}
        self._made_next: list[int] = [self._n_static]
        self._member_of: dict[int, list[int]] = {}
        self._invites: dict[int, list[int]] = {}
        self._places: dict[int, list[int]] = {}

    def source(self) -> str:
        """個人の連絡先の出どころ(manifest の設定)。"""
        from shibuya.engine.relations_people import PeopleRelationLayer

        r = self.rel_layer
        if r is None:
            return "groups.family"
        return "relations.people_memory" if isinstance(r, PeopleRelationLayer) else "relations.contact_flags"

    # ------------------------------------------------------------------ グループ
    def groups_of(self, agent: int) -> tuple[int, ...]:
        """体が成員のグループ(実データの行の番号の昇順 → 作ったグループの番号の昇順)。"""
        a = int(agent)
        lo, hi = np.searchsorted(self._g_mem, [a, a + 1])
        out = [int(x) for x in self._g_row[lo:hi]]
        out += list(self._member_of.get(a, ()))
        return tuple(out)

    def made_groups_of(self, agent: int) -> tuple[int, ...]:
        """〔C2〕体が成員の、本人たちが作ったグループ(番号の昇順)。"""
        return tuple(self._member_of.get(int(agent), ()))

    def is_made(self, g: int) -> bool:
        return int(g) in self._made

    def group_kind(self, g: int) -> str:
        if int(g) in self._made:
            return FRIEND
        return GROUP_KINDS[int(self._g_kind[int(g)])]

    def members(self, g: int) -> tuple[int, ...]:
        """グループの成員(作ったグループで無くなったものは空)。"""
        if int(g) >= self._n_static:
            row = self._made.get(int(g))
            return () if row is None else tuple(int(x) for x in row[1])
        return tuple(int(x) for x in np.asarray(self.groups.members(int(g)), dtype=np.int64)) if self.groups is not None else ()

    def _join(self, g: int, a: int) -> None:
        row = self._made[int(g)]
        row[1] = sorted(row[1] + [int(a)])
        self._member_of[int(a)] = sorted(self._member_of.get(int(a), []) + [int(g)])

    def make_group(self, creator: int) -> int:
        """〔C2〕友人のグループを作る(本人の行動=作った人だけが成員)。番号を返す。"""
        g = int(self._made_next[0])
        self._made_next[0] = g + 1
        self._made[g] = [int(creator), []]
        self._join(g, int(creator))
        return g

    def invite(self, g: int, agent: int) -> bool:
        """〔C2〕作ったグループに招く(招かれた体の招待の列に足す)。もう成員か招かれていれば偽。"""
        a = int(agent)
        if int(g) not in self._made or a in self.members(g) or int(g) in self._invites.get(a, ()):
            return False
        self._invites.setdefault(a, []).append(int(g))
        return True

    def invites_of(self, agent: int) -> tuple[int, ...]:
        return tuple(self._invites.get(int(agent), ()))

    def _drop_invite(self, g: int, a: int) -> None:
        lst = self._invites.get(int(a))
        if lst is not None and int(g) in lst:
            lst.remove(int(g))
            if not lst:
                del self._invites[int(a)]

    def answer_invite(self, g: int, agent: int, join: bool) -> None:
        """〔C2〕招待に答える(入る/断る=本人の行動)。招待の列から落とす。"""
        a = int(agent)
        self._drop_invite(g, a)
        if join and int(g) in self._made and a not in self._made[int(g)][1]:
            self._join(g, a)

    def leave(self, g: int, agent: int) -> bool:
        """〔C2〕作ったグループを抜ける(本人の行動)。実データの行は抜けない(偽)。〔検収 L7〕成員が 0 人になったグループは無くなる
        (招待も消える)。"""
        a = int(agent)
        row = self._made.get(int(g))
        if row is None or a not in row[1]:
            return False
        row[1] = [m for m in row[1] if m != a]
        mine = [x for x in self._member_of.get(a, []) if x != int(g)]
        if mine:
            self._member_of[a] = mine
        else:
            self._member_of.pop(a, None)
        if not row[1]:
            del self._made[int(g)]
            for b in sorted(self._invites):  # 逐次: 招待のある体の数ぶん(無くなったグループへの招待を消す)
                self._drop_invite(g, b)
        return True

    # ------------------------------------------------------------------ 個人の連絡先
    def _bodies(self, ids: np.ndarray, agent: int) -> np.ndarray:
        ids = np.asarray(ids, dtype=np.int64)
        ok = (ids >= 0) & (ids < self.n) & (ids != int(agent))
        bad = int(np.count_nonzero((ids >= self.n) | ((ids < 0) & (ids != -1))))
        if bad:
            self.bodiless_dropped += bad
        return np.unique(ids[ok])

    def _base(self, agents: Any, a: int, means_bit: int, step: int) -> np.ndarray:
        from shibuya.engine.relations_people import PeopleRelationLayer

        r = self.rel_layer
        if r is None:
            fam = [g for g in self.groups_of(a) if g < self._n_static and self.group_kind(g) == FAMILY]
            if not fam or not (int(_CT.INITIAL_FLAGS_BY_KIND[_CT.KIND_HOUSEHOLD]) & int(means_bit)):
                return np.zeros(0, dtype=np.int64)
            return np.concatenate([np.asarray(self.groups.members(g), dtype=np.int64) for g in fam])
        if isinstance(r, PeopleRelationLayer):
            e = r.edges(agents, a, int(step))
            flags = _CT.flags_from_kinds(np.asarray(e.kind, dtype=np.int64), np.asarray(e.partner, dtype=np.int64))
            return np.asarray(e.partner, dtype=np.int64)[(flags & int(means_bit)) != 0]
        partner = np.asarray(r._partner_rows(agents, np.asarray([a]))[0], dtype=np.int64)
        flags = np.asarray(r.contact_flags[a], dtype=np.int64)
        return partner[(flags & int(means_bit)) != 0]

    def personal(self, agents: Any, agent: int, means_bit: int, step: int) -> tuple[int, ...]:
        """体の個人の連絡先のうち手段のビット ``means_bit`` の印のある相手(番号の昇順・体だけ)。〔C2〕交換した相手を足す。"""
        a = int(agent)
        ids = self._base(agents, a, means_bit, step)
        ex = self._exchanged.get(a)
        if ex:
            more = np.asarray([b for b, bits in sorted(ex.items()) if int(bits) & int(means_bit)], dtype=np.int64)
            ids = np.concatenate([ids, more]) if more.size else ids
        return tuple(int(x) for x in self._bodies(ids, a))

    def add_contact(self, agent: int, partner: int, means_bit: int) -> None:
        """〔C2〕本人の帳に手段の印を足す(交換に応じたとき=両方の帳)。"""
        d = self._exchanged.setdefault(int(agent), {})
        d[int(partner)] = int(d.get(int(partner), 0)) | int(means_bit)

    # ------------------------------------------------------------------ 店の番号(場所の表の側)
    def save_place(self, agent: int, poi: int) -> bool:
        """〔C2〕調べた店の番号を保存する(本人の行動)。もう保存していれば偽。"""
        lst = self._places.setdefault(int(agent), [])
        if int(poi) in lst:
            return False
        lst.append(int(poi))
        return True

    def places_of(self, agent: int) -> tuple[int, ...]:
        return tuple(self._places.get(int(agent), ()))

    # ------------------------------------------------------------------ 計器
    def dropped_count(self) -> int:
        """体の無い人を宛先から落とした数(計器=持ち主の数えの口)。"""
        return int(self.bodiless_dropped)

    def tally(self) -> dict[str, Any]:
        """〔C2〕計器: 交換した連絡先の数・作ったグループの数と成員の数の分布・招待の数・保存した店の番号の数。"""
        sizes: dict[str, int] = {}
        for _c, mem in self._made.values():  # 逐次: 作ったグループの数ぶん(計器=manifest だけ)
            k = str(len(mem))
            sizes[k] = sizes.get(k, 0) + 1
        return {
            "exchanged_pairs": int(sum(len(v) for v in self._exchanged.values())),
            "agents_with_exchanged": len(self._exchanged),
            "made_groups": len(self._made), "made_ever": int(self._made_next[0]) - self._n_static,
            "made_group_sizes": dict(sorted(sizes.items(), key=lambda kv: int(kv[0]))),
            "invites_waiting": int(sum(len(v) for v in self._invites.values())),
            "saved_places": int(sum(len(v) for v in self._places.values())),
        }
