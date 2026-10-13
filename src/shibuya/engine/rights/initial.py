"""engine.rights.initial — 権利台帳の最初の中身(第 1 期 1-5・計画 1-5 の 4 つ・決定 10-12 §4-5 CP4)。

世界の組み立てで 1 回作る(開閉の過程が持つ・再開では戻した SoA から作り直す)。中身は計画 1-5 の 4 つと、開閉の過程の
担当従業者(``staff_of_poi`` の丸振りを台帳からの読みに置き換えるための行):

| 中身 | 行 | 出どころ(``source``) |
|---|---|---|
| (a) 雇用 | W16 の ``org_id`` を持つ体ごとに 1 行(``employ``・holder=体・object=組織・開始前から) | ``w16_population.org_id`` |
| (a′) 担当従業者 | 店(POI)ごとに担当の体 1 人(``employ``・holder=体・object=店) | 宣言(下の expedient) |
| (b) 営業許可 | **0 行**(空欄)。区の「食品等営業許可・届出一覧」は記録の上ではある(R-76 #17・R-106 §2-1・SHIBUYA OPEN DATA・
  CC BY 4.0)が取得していない。POI との突き合わせの規則も決まっていない | ― |
| (c) 店の賃借 | 店(POI)ごとに 1 行(``lease``・holder=店・object=区画)。家賃と貸し手(相手)は空欄 | ``w6_poi`` |
| (d) 住まい | **0 行**(空欄)。国勢調査の住宅の所有の関係(表 18-4)は表の場所だけ分かり、値は未取得(R-106 §2-1) | ― |

空欄はつなぎの台帳の行に結ぶ(``BLANK_BRIDGES``=``docs/design/bridging-ledger.json`` の id)。

expedient(本モジュール分)
- 担当従業者の雇用の行: 種別 従業者 の体を店(POI)へ決定論で丸振りする(店 j → 従業者の j mod 人数 番目)。HEAD の
  ``engine.processes.opening.OpeningProcess._assign_staff`` の規則をそのまま移した(同じ割り当て=値は不変)。組織台帳
  (W6)と店の対応は無い(W16 の ``org_id`` の行とは別の行)。
- 店の賃借: すべての POI を店とみなし(お金の台帳の店舗の口座と同じ=店の数=POI の数)、区画の番号は POI の番号で
  代用する(1 店=1 区画)。家賃と貸し手は空欄。
- 最初の行の時刻: 開始前から終わりなし(``since_ns``・``until_ns`` とも ``None``)。原因は ``None``(初期状態)。

逐次ループ宣言: ``build_initial`` は行の数ぶん(体の数+POI の数の 2 倍・組み立てで 1 回=刻みに比例しない)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

from shibuya.agents.state import AgentKind
from shibuya.engine.rights.ledger import AGENT, EMPLOY, LEASE, ORG, PARCEL, STORE, Right, Rights

__all__ = [
    "SOURCE_W16_ORG", "SOURCE_STAFF", "SOURCE_POI", "SOURCES", "BLANK_BRIDGES",
    "staff_assignment", "build_initial", "staff_of_poi",
]

#: (a) の出どころ(W16 の列名)。
SOURCE_W16_ORG: Final[str] = "w16_population.org_id"
#: (a′) の出どころ(宣言=担当従業者の丸振り)。
SOURCE_STAFF: Final[str] = "宣言:担当従業者の丸振り(engine.rights.initial)"
#: (c) の出どころ(W6 の POI=区画にいること)。
SOURCE_POI: Final[str] = "w6_poi(区画にいること)"
SOURCES: Final[tuple[str, ...]] = (SOURCE_W16_ORG, SOURCE_STAFF, SOURCE_POI)

#: 空欄 → つなぎの台帳の行(``docs/design/bridging-ledger.json`` の id)。
BLANK_BRIDGES: Final[Mapping[str, str]] = MappingProxyType({
    "lease.rent": "BR-RENT-BLANK",             # (c) 家賃は空欄(1-4 で載せた行)
    "licence": "BR-RIGHTS-LICENCE-BLANK",      # (b) 営業許可の行は 0
    "dwelling": "BR-RIGHTS-DWELLING-BLANK",    # (d) 住まいの行は 0
})


def staff_assignment(kind: Any, n_store: int) -> np.ndarray:
    """店(POI)→ 担当の体(-1=担当なし)。種別 従業者 の体を決定論で丸振りする(HEAD の ``_assign_staff`` と同じ規則)。"""
    out = np.full(int(n_store), -1, dtype=np.int64)
    if int(n_store) == 0:
        return out
    workers = np.flatnonzero(np.asarray(kind) == int(AgentKind.WORKER)).astype(np.int64)
    if workers.size == 0:
        return out
    out[:] = workers[np.arange(int(n_store)) % workers.size]
    return out


def build_initial(kind: Any, n_poi: int, org_of_agent: Any | None = None) -> Rights:
    """最初の中身の権利台帳を作る(行の順: (a) 雇用 → (a′) 担当従業者 → (c) 店の賃借)。

    Args:
        kind: 体の種別の列(SoA の ``kind``)。
        n_poi: POI の数(=店の数=区画の数)。
        org_of_agent: 体 → W16 の ``org_id``(-1=組織なし・``None``=母集団の無いラン=(a) の行なし)。
    """
    k = np.asarray(kind)
    org = None if org_of_agent is None else np.asarray(org_of_agent, dtype=np.int64).ravel()
    staff = staff_assignment(k, int(n_poi))
    n_rows = int(np.count_nonzero(org >= 0) if org is not None else 0) + int(np.count_nonzero(staff >= 0)) + int(n_poi)
    rights = Rights(capacity=max(1, n_rows))
    if org is not None:
        # 逐次ループ: 組織を持つ体ぶん(組み立てで 1 回)
        for a in np.flatnonzero(org >= 0).tolist():
            rights.grant(Right(holder=(AGENT, a), object=(ORG, int(org[a])), kind=EMPLOY, source=SOURCE_W16_ORG))
    # 逐次ループ: 担当のいる店ぶん
    for j in np.flatnonzero(staff >= 0).tolist():
        rights.grant(Right(holder=(AGENT, int(staff[j])), object=(STORE, j), kind=EMPLOY, source=SOURCE_STAFF))
    # 逐次ループ: POI ぶん
    for j in range(int(n_poi)):
        rights.grant(Right(holder=(STORE, j), object=(PARCEL, j), kind=LEASE, source=SOURCE_POI))
    return rights


def staff_of_poi(rights: Rights, n_poi: int, t_ns: int) -> np.ndarray:
    """権利台帳の ``employ`` の行(体 → 店)から、店(POI)→ 担当の体の表を読む(-1=担当なし・複数なら最初の行)。"""
    return rights.holder_table(int(n_poi), kind=EMPLOY, holder_kind=AGENT, object_kind=STORE, t_ns=int(t_ns))
