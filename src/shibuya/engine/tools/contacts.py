"""engine.tools.contacts — 個人の連絡先の手段ごとの印(第 1 期 1-7 C0・CT5)。

決定 10-12 §4-4 CT5 (c): 個人の連絡先は、関係の記憶に手段ごとの印で持つ。家族と職場は初めから持たせる。店や組織の番号は
場所の表の側(``engine.tools.places``)。連絡先を調べる・保存する・交換するは本人の行動(C1=計画 6-4)。

- 印の欄は関係の記憶の ``RelationLayer.contact_flags``(体 × k 辺の ``uint8``・既存の ``rel_*`` 列と同じ形で欄の位置が
  そろう・既存の列は変えない)。書くのは ``RelationLayer`` の 1 つの口 ``_write_contacts`` だけ(初めの辺を書いたとき=
  種別から印・欄の相手が替わったとき=印を消す・再開で作り直すとき=種別から印)。本モジュールは値の作り方と数え方だけを
  持つ(``engine.relations`` を import しない=循環を作らない。種別の番号は写しで持ち、試験が ``REL_KINDS`` と突き合わせる)。
- C0 では誰も読まない(値は C1 で使う)。C0 では印は辺の種別の写像そのもの(``flags_from_kinds``)=状態台帳では導出
  (行 ``CT5``・軸 1 diag=読み手は持ち主の数えの口 ``contact_tally`` だけ・軸 2 derivable・中身は hash_skip=どちらのハッシュにも状態のファイルにも入らない)。C1 で本人が
  連絡先を交換し始めたら種別から作れなくなる=要る(required)へ移す(版上げ)。
- 手段は R-85 §5-1 案 (a) の 4 つ(電話番号=通話・メッセージ・メール・職場のチャット=職場の連絡)。

expedient(本モジュール分)
- 手段の印の 4 つ(通話・メッセージ・メール・職場の連絡)とビットの並び。SNS のつながり(C4)は印に入れていない。
- 初めの印の値: 世帯の辺=通話・メッセージ・メール/職場の辺=それに職場の連絡を足した 4 つ(手段ごとに「知っている」の
  錨は空欄=R-85 §5-1・§9。§2-6 の「最も使う手段」の分布は使う頻度で、知っているかではない)。
- 学校の辺(種別 3)・常連・知人の辺は初めの印なし(決定は「家族と職場」だけ)。

逐次ループ宣言: なし(印の写像と数えは配列演算)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

__all__ = [
    "MEANS", "MEANS_BITS", "CALL", "MESSAGE", "MAIL", "WORK", "ALL_PERSONAL", "KIND_HOUSEHOLD", "KIND_WORK",
    "KIND_NAMES", "INITIAL_FLAGS_BY_KIND", "FLAG_DTYPE", "flags_from_kinds", "tally",
]

#: 手段(印のビットの並び=``1 << 位置``)。
MEANS: Final[tuple[str, ...]] = ("通話", "メッセージ", "メール", "職場の連絡")
MEANS_BITS: Final[Mapping[str, int]] = MappingProxyType({m: 1 << i for i, m in enumerate(MEANS)})
CALL: Final[int] = MEANS_BITS["通話"]
MESSAGE: Final[int] = MEANS_BITS["メッセージ"]
MAIL: Final[int] = MEANS_BITS["メール"]
WORK: Final[int] = MEANS_BITS["職場の連絡"]
#: 個人の手段(職場の連絡を除く)。
ALL_PERSONAL: Final[int] = CALL | MESSAGE | MAIL

#: 辺の種別の番号(``engine.relations.REL_KINDS`` の写し=世帯 1・職場 2。一致は試験が見る)。
KIND_HOUSEHOLD: Final[int] = 1
KIND_WORK: Final[int] = 2
#: 種別の番号 → 名(``engine.relations.REL_KIND_NAMES`` の写し・数えの鍵)。
KIND_NAMES: Final[Mapping[int, str]] = MappingProxyType({
    1: "household", 2: "work", 3: "school", 4: "regular", 5: "acquaintance"})
#: 初めの印(家族=世帯の辺・職場=職場の辺。ほかの種別は 0)。
INITIAL_FLAGS_BY_KIND: Final[Mapping[int, int]] = MappingProxyType({
    KIND_HOUSEHOLD: ALL_PERSONAL,
    KIND_WORK: ALL_PERSONAL | WORK,
})
FLAG_DTYPE: Final[Any] = np.uint8

_LUT = np.zeros(256, dtype=FLAG_DTYPE)
for _k, _v in INITIAL_FLAGS_BY_KIND.items():
    _LUT[_k] = _v
_LUT.flags.writeable = False


def flags_from_kinds(kind: np.ndarray, partner: np.ndarray | None = None) -> np.ndarray:
    """辺の種別 → 初めの印(``uint8``・形は ``kind`` と同じ)。``partner`` を渡すと空の辺(-1)は 0。"""
    k = np.asarray(kind)
    if k.size and (int(k.min()) < 0 or int(k.max()) > 255):
        raise ValueError("辺の種別は 0〜255")
    out = _LUT[k.astype(np.int64)]
    if partner is not None:
        p = np.asarray(partner)
        if p.shape != k.shape:
            raise ValueError(f"partner の形 {p.shape} が kind の形 {k.shape} と違う")
        out = np.where(p >= 0, out, 0).astype(FLAG_DTYPE)
    return out


def tally(flags: np.ndarray, kind: np.ndarray, partner: np.ndarray) -> dict[str, Any]:
    """manifest の ``tools.contact_flags``: 印を持つ辺の数・手段ごとの辺の数・種別ごとの印を持つ辺の数・バイト。"""
    f = np.asarray(flags)
    live = np.asarray(partner) >= 0
    has = (f != 0) & live
    kinds = np.asarray(kind).astype(np.int64)
    by_kind = {name: int(np.count_nonzero(has & (kinds == code))) for code, name in KIND_NAMES.items()}
    return {
        "edges_with_contact": int(np.count_nonzero(has)),
        "edges_live": int(np.count_nonzero(live)),
        "by_means": {m: int(np.count_nonzero(((f & MEANS_BITS[m]) != 0) & live)) for m in MEANS},
        "by_kind": by_kind,
        "bytes": int(f.nbytes),
    }
