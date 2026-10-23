"""engine.duties.knowledge — 店の決まり(営業時間)の問い合わせの口(第 6 期 6-6 ② 第 1 部・決定 10-12 §1-4)。

正: 決定 10-12 §1-4(人の手続きはコードに書かず住人の知識から出す)・§4-1 CA11(店の決まりは組織の口が知らせる=カレンダー 3 の
``engine.calendar3.knowledge.StoreRules`` の形)・CP6(エンジンは表を読んで開閉しない)。

:class:`ShopRules`(``StoreRules`` の子=店の決まりの口に「営業時間」を足した): 店の営業時間の表(W7=世界過程の開閉の過程の
その日の行列 ``OpeningProcess.open_matrix``=曜日と祝日の行・申込書の決定 L1 の差し替えを含む)を、**その店の担当(権利台帳の
雇用の行=体 → 店)だけ**が引ける形にした(担当でない体には答えない=知らない)。エンジンはこの口を開閉の判断に使わない(使うのは
本人の候補の口=``engine.duties.layer``)。状態を持たない(引いた数は持ち主の計器)。常識の文の 1 行 :func:`rules_line` は判断の
入力の常識の文に足す形(仮のモデルは文を読まない=manifest に例を出す)。

〔検収 M3〕答えには出どころの印を付ける(:meth:`ShopRules.source`=W7 の列 ``src``=``osm_opening_hours``(実データ)・
``chain_default``・``category_default``(どちらも構築側の既定=作り物の印)・列の無い資産は ``unknown``)。常識の文にも印を出し、
持ち主の計器は出どころで分ける(1-7 の看板の作り物の印 ``signboard:synthetic`` と同じ形=記録の ``origin`` に
``store_rules:<出どころ>``)。

〔検収 L6〕先読み(``at`` に分+幅を渡す)が夜中をまたぐと、次の日の曜日の行ではなく今日の行列を巻き戻して読む(開閉の過程の
つなぎも今日の行列=食い違いは無い=宣言 ``DOC-du1-shop-window``)。

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-du1-store-rules``): 店の決まりを知る人=その店の雇用の行の体(組織の雇用の行
から店を引く口は無い=カレンダー 3 の単位の「店」と同じ行)。表の無い店(W7 に行の無い店・合成の世界)は決まりが無い=答えない。

逐次ループ宣言: なし(配列の読み 1 回)。
"""

from __future__ import annotations

from typing import Any, Final

import numpy as np

from shibuya.core.time_consts import MINUTES_PER_DAY, MINUTES_PER_HOUR
from shibuya.engine.calendar3.knowledge import StoreRules

__all__ = ["ShopRules", "rules_line", "UNKNOWN", "SRC_UNKNOWN", "REAL_SOURCES", "origin_mark"]

#: 決まりを知らない(担当でない・表の無い店)の答え。
UNKNOWN: Final[int] = -1
#: 〔検収 M3〕出どころの無い店(W7 の列 src の無い資産・行の無い店)の印。
SRC_UNKNOWN: Final[str] = "unknown"
#: 実データの出どころ(ほかは構築側の既定=作り物の印)。
REAL_SOURCES: Final[frozenset[str]] = frozenset({"osm_opening_hours"})


def origin_mark(src: str) -> str:
    """記録の ``origin`` に入れる出どころの印(``store_rules:<出どころ>``)。"""
    return f"store_rules:{src}"


def _hhmm(minute: int) -> str:
    m = int(minute)
    return f"{m // MINUTES_PER_HOUR}:{m % MINUTES_PER_HOUR:02d}"


class ShopRules(StoreRules):
    """店の決まりの口(休業日の枠=親クラス+営業時間)。担当だけが自分の店の営業時間を引ける。"""

    def __init__(self, shops: Any) -> None:
        #: 世界過程の開閉の過程(営業時間の行列と権利台帳と資産の出どころの列を読むだけ)。
        self.shops = shops

    def source(self, poi: int) -> str:
        """〔検収 M3〕店の決まりの出どころ(W7 の列 src・無ければ :data:`SRC_UNKNOWN`)。"""
        a = getattr(self.shops, "assets", None)
        codes = getattr(a, "plan_poi_src", None)
        names = getattr(a, "plan_src_names", ())
        if codes is None or not (0 <= int(poi) < int(codes.size)) or int(codes[int(poi)]) < 0:
            return SRC_UNKNOWN
        return str(names[int(codes[int(poi)])])

    def _table(self) -> np.ndarray | None:
        m = getattr(self.shops, "open_matrix", None)
        if m is None or m.size == 0:
            return None
        return m

    def knows(self, agents: Any, pois: Any, t_ns: int) -> np.ndarray:
        """体 ``agents[i]`` が店 ``pois[i]`` の決まりを知っているか(雇用の行 体 → 店がある・表のある店)。"""
        from shibuya.engine.rights.ledger import AGENT, EMPLOY, STORE

        a = np.asarray(agents, dtype=np.int64).ravel()
        p = np.asarray(pois, dtype=np.int64).ravel()
        if a.size == 0 or self._table() is None:
            return np.zeros(a.size, dtype=bool)
        return np.asarray(self.shops.rights.holds_each(a, p, kind=EMPLOY, holder_kind=AGENT, object_kind=STORE,
                                                         t_ns=int(t_ns)), dtype=bool)

    def at(self, agents: Any, pois: Any, minutes: Any, t_ns: int) -> np.ndarray:
        """店の決まりで、その日のその分に営業か(1)・休みか(0)・知らない(:data:`UNKNOWN`)。分は 1 日で巻き戻す。"""
        a = np.asarray(agents, dtype=np.int64).ravel()
        p = np.asarray(pois, dtype=np.int64).ravel()
        out = np.full(a.size, UNKNOWN, dtype=np.int64)
        tab = self._table()
        if tab is None or a.size == 0:
            return out
        k = self.knows(a, p, t_ns)
        mm = np.asarray(minutes, dtype=np.int64).ravel() % MINUTES_PER_DAY
        if mm.size == 1 and a.size > 1:
            mm = np.full(a.size, int(mm[0]), dtype=np.int64)
        out[k] = tab[p[k], mm[k]].astype(np.int64)
        return out

    def edge(self, agent: int, poi: int, minute: int, t_ns: int, *, rising: bool) -> int | None:
        """その日の決まりの区切りのうち ``minute`` に一番近いもの(``rising``=営業の始まり・偽=終わり)の分。知らなければ
        ``None``。日をまたいで巻き戻す(前後半日の中の近い方)。"""
        tab = self._table()
        if tab is None or not bool(self.knows([agent], [poi], t_ns)[0]):
            return None
        row = np.asarray(tab[int(poi)], dtype=bool)
        prev = np.roll(row, 1)
        marks = np.flatnonzero(row & ~prev) if rising else np.flatnonzero(~row & prev)
        if marks.size == 0:
            return None
        d = (marks - int(minute) + MINUTES_PER_DAY // 2) % MINUTES_PER_DAY - MINUTES_PER_DAY // 2
        return int(marks[int(np.argmin(np.abs(d)))])

    def hours(self, agent: int, poi: int, t_ns: int) -> list[tuple[int, int]]:
        """その日の営業の区間 ``[(始まり[分], 終わり[分]), …]``(知らなければ空)。"""
        tab = self._table()
        if tab is None or not bool(self.knows([agent], [poi], t_ns)[0]):
            return []
        row = np.asarray(tab[int(poi)], dtype=bool)
        if row.all():
            return [(0, MINUTES_PER_DAY)]
        starts = np.flatnonzero(row & ~np.roll(row, 1)).tolist()
        ends = np.flatnonzero(~row & np.roll(row, 1)).tolist()
        out: list[tuple[int, int]] = []
        for s in starts:  # 逐次: その店のその日の区間の数ぶん(≤ 数個)
            later = [e for e in ends if e > s]
            e = later[0] if later else (ends[0] + MINUTES_PER_DAY if ends else MINUTES_PER_DAY)
            out.append((int(s), int(e)))
        return out


def rules_line(rules: ShopRules, agent: int, poi: int, t_ns: int) -> str:
    """常識の文の 1 行(「店の決まり: 営業 10:00〜22:00。」の形・知らなければ空)。"""
    hs = rules.hours(agent, poi, t_ns)
    if not hs:
        return ""
    src = rules.source(poi)
    mark = "" if src in REAL_SOURCES else ("(出どころ不明)" if src == SRC_UNKNOWN else f"(出どころ {src}=作り物の印)")
    return "店の決まり: 営業 " + "・".join(f"{_hhmm(s)}〜{_hhmm(e)}" for s, e in hs) + "。" + mark
