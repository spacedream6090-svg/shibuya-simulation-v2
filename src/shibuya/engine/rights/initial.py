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

〔第 4 期 4-3 段 10〕差し替えの母集団(``w21_person_id`` の列がある=``build.pop.w21_apply``)の世界は、初期の行の表
``w21_rights_run.parquet``(:func:`load_run_rows`)を読む: (a′) 店の担当は丸振りをやめて表の「体 → 店」の雇用の行(W21c=店の
持ち主の組織に所属した体・店ごとの最初の行=担当)・(d) 住まいは表の「世帯主 → 住まい」の所有と賃借の行(W21b=国勢調査の
住宅の所有の関係)。(a) 雇用と (c) 店の賃借は今の口のまま(母集団の ``org_id``=W21 の所属・POI)。ランに居ない体(抽出で
外れた体)の行は入れない。表の無い世界(本体の v2)は今のまま(1 バイトも変えない)。〔検収の直し〕表の担当のいない店は今の
丸振り(出どころの語 ``SOURCE_STAFF``=表の行は ``w21c:…``)・(a″) 外の雇用主=勤め先のセルはあるが組織の無い体の雇用の行
(体 → 組織の番号 :data:`OUTSIDE_EMPLOYER_ORG`=閉じた表の外の番号・給料日は外界から払う=``economy.stage2``)・表の店の番号が POI の
数の外なら止める(黙って捨てない)。

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
from shibuya.engine.rights.ledger import AGENT, DWELLING, EMPLOY, LEASE, ORG, OWN, PARCEL, STORE, Right, Rights

__all__ = [
    "SOURCE_W16_ORG", "SOURCE_STAFF", "SOURCE_POI", "SOURCES", "BLANK_BRIDGES",
    "staff_assignment", "build_initial", "staff_of_poi", "RUN_ROWS_FILE", "RUN_BLOCKS", "InitialRows",
    "load_run_rows", "OUTSIDE_EMPLOYER_ORG", "SOURCE_OUTSIDE_EMPLOYER",
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


#: 〔段 10〕差し替えの世界の初期の行の表(``<world_dir>/w21_rights_run.parquet``)と読む塊。
RUN_ROWS_FILE: Final[str] = "w21_rights_run.parquet"
RUN_BLOCKS: Final[tuple[str, ...]] = ("store_staff", "dwelling", "outside_employer")
#: 〔検収 M3〕外の雇用主の組織の番号(W6 の組織の番号の外=閉じた表の外・``build.pop.w21_apply.OUTSIDE_EMPLOYER_ORG`` と同じ値)。
OUTSIDE_EMPLOYER_ORG: Final[int] = (1 << 31) - 1
SOURCE_OUTSIDE_EMPLOYER: Final[str] = "w21apply:外の雇用主(席の外=勤め先のセルはあるが組織が無い・閉じた表の外の番号)"


class InitialRows:
    """〔段 10〕初期の行(体の番号=ランの SoA の行・読むだけ)。``block`` は :data:`RUN_BLOCKS` のどれか。"""

    __slots__ = ("holder", "object_kind", "object_id", "kind", "source", "block", "dropped")

    def __init__(self, holder: Any, object_kind: Any, object_id: Any, kind: Any, source: Any, block: Any,
                 dropped: int) -> None:
        self.holder = np.asarray(holder, dtype=np.int64)
        self.object_kind = np.asarray(object_kind, dtype=object)
        self.object_id = np.asarray(object_id, dtype=np.int64)
        self.kind = np.asarray(kind, dtype=object)
        self.source = np.asarray(source, dtype=object)
        self.block = np.asarray(block, dtype=object)
        #: ランに居ない体の行の数(抽出で外れた体=入れない)。
        self.dropped = int(dropped)
        for a in (self.holder, self.object_kind, self.object_id, self.kind, self.source, self.block):
            a.setflags(write=False)

    def __len__(self) -> int:
        return int(self.holder.size)


def load_run_rows(world_dir: Any, agent_ids: Any) -> InitialRows | None:
    """差し替えの世界の初期の行の表を読み、体の番号(母集団の ``agent_id``)をランの SoA の行へ引き直す(表が無ければ ``None``)。

    ``agent_ids`` はランの体の並び(``Population.source_agent_id``)。表の塊が :data:`RUN_BLOCKS` の外・種類が閉じた表の外なら
    止める(黙って捨てない)。逐次ループ宣言: なし(配列演算)。
    """
    from pathlib import Path

    if world_dir is None:
        return None
    path = Path(world_dir) / RUN_ROWS_FILE
    if not path.exists():
        return None
    import pyarrow.parquet as pq  # 遅延 import(表の無いランに読み込ませない)

    t = pq.read_table(path, columns=["holder_agent_id", "object_kind", "object_id", "kind", "source", "block"])
    col = {n: np.asarray(t.column(n).to_pylist(), dtype=object) if n in ("object_kind", "kind", "source", "block")
           else t.column(n).to_numpy(zero_copy_only=False) for n in t.schema.names}
    block = col["block"]
    bad = sorted(set(block.tolist()) - set(RUN_BLOCKS))
    if bad:
        raise ValueError(f"{RUN_ROWS_FILE} に知らない塊: {bad}")
    ok_staff = (block == "store_staff") & (col["kind"] == EMPLOY) & (col["object_kind"] == STORE)
    ok_dw = (block == "dwelling") & np.isin(col["kind"], [OWN, LEASE]) & (col["object_kind"] == DWELLING)
    ok_oe = ((block == "outside_employer") & (col["kind"] == EMPLOY) & (col["object_kind"] == ORG)
             & (np.asarray(col["object_id"], dtype=np.int64) == OUTSIDE_EMPLOYER_ORG))
    if not np.all(ok_staff | ok_dw | ok_oe):
        raise ValueError(f"{RUN_ROWS_FILE} の行の種類が閉じた表(体 → 店の雇用・体 → 住まいの所有と賃借・体 → 外の雇用主)の外")
    aid = np.asarray(agent_ids, dtype=np.int64)
    order = np.argsort(aid, kind="stable")
    holder = np.asarray(col["holder_agent_id"], dtype=np.int64)
    if aid.size == 0 or holder.size == 0:
        present = np.zeros(holder.size, dtype=bool)
        row = np.full(holder.size, -1, dtype=np.int64)
    else:
        k = np.clip(np.searchsorted(aid[order], holder), 0, aid.size - 1)
        present = aid[order][k] == holder
        row = np.where(present, order[k], -1)
    keep = row >= 0
    return InitialRows(row[keep], col["object_kind"][keep], np.asarray(col["object_id"], dtype=np.int64)[keep],
                       col["kind"][keep], col["source"][keep], block[keep], int((~keep).sum()))


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


def build_initial(kind: Any, n_poi: int, org_of_agent: Any | None = None,
                  rows: InitialRows | None = None) -> Rights:
    """最初の中身の権利台帳を作る(行の順: (a) 雇用 → (a′) 担当従業者 → (c) 店の賃借 → (d) 住まい)。

    Args:
        kind: 体の種別の列(SoA の ``kind``)。
        n_poi: POI の数(=店の数=区画の数)。
        org_of_agent: 体 → W16 の ``org_id``(-1=組織なし・``None``=母集団の無いラン=(a) の行なし)。
        rows: 〔段 10〕差し替えの世界の初期の行(:func:`load_run_rows`)。``None``=今の口((a′) は丸振り・(d) は 0 行)。
            あれば (a′) は表の「体 → 店」の行(表の順=店ごとの最初の行が担当)・(d) は表の住まいの行。
    """
    k = np.asarray(kind)
    org = None if org_of_agent is None else np.asarray(org_of_agent, dtype=np.int64).ravel()
    staff = staff_assignment(k, int(n_poi))
    st_store = np.flatnonzero(staff >= 0)
    st_holder = staff[st_store]
    st_src = np.full(st_store.size, SOURCE_STAFF, dtype=object)
    dw = np.zeros(0, dtype=np.int64)
    oe = np.zeros(0, dtype=np.int64)
    if rows is not None:
        sel = np.flatnonzero(rows.block == "store_staff")
        if sel.size and (rows.object_id[sel].min() < 0 or rows.object_id[sel].max() >= int(n_poi)):
            raise ValueError(f"{RUN_ROWS_FILE} の店の担当の行に POI の数({int(n_poi)})の外の店の番号がある(黙って捨てない)")
        # 表の担当のいる店は表の行(表の順=店ごとの最初の行が担当)・いない店は今の丸振り(出どころの語を分ける)
        rr = ~np.isin(st_store, rows.object_id[sel])
        st_holder = np.concatenate([rows.holder[sel], st_holder[rr]])
        st_store = np.concatenate([rows.object_id[sel], st_store[rr]])
        st_src = np.concatenate([rows.source[sel], st_src[rr]])
        dw = np.flatnonzero(rows.block == "dwelling")
        oe = np.flatnonzero(rows.block == "outside_employer")
    n_rows = (int(np.count_nonzero(org >= 0) if org is not None else 0) + int(oe.size) + int(st_holder.size)
              + int(n_poi) + int(dw.size))
    rights = Rights(capacity=max(1, n_rows))
    if org is not None:
        # 逐次ループ: 組織を持つ体ぶん(組み立てで 1 回)
        for a in np.flatnonzero(org >= 0).tolist():
            rights.grant(Right(holder=(AGENT, a), object=(ORG, int(org[a])), kind=EMPLOY, source=SOURCE_W16_ORG))
    # 逐次ループ: 〔検収 M3〕外の雇用主の行ぶん(差し替えの世界だけ)
    for i in oe.tolist():
        rights.grant(Right(holder=(AGENT, int(rows.holder[i])), object=(ORG, OUTSIDE_EMPLOYER_ORG), kind=EMPLOY,
                           source=str(rows.source[i])))
    # 逐次ループ: 担当の行ぶん
    for h, j, src in zip(st_holder.tolist(), st_store.tolist(), st_src.tolist()):
        rights.grant(Right(holder=(AGENT, int(h)), object=(STORE, int(j)), kind=EMPLOY, source=str(src)))
    # 逐次ループ: POI ぶん
    for j in range(int(n_poi)):
        rights.grant(Right(holder=(STORE, j), object=(PARCEL, j), kind=LEASE, source=SOURCE_POI))
    # 逐次ループ: 〔段 10〕住まいの行ぶん(差し替えの世界だけ)
    if rows is not None:
        for i in dw.tolist():
            rights.grant(Right(holder=(AGENT, int(rows.holder[i])), object=(DWELLING, int(rows.object_id[i])),
                               kind=str(rows.kind[i]), source=str(rows.source[i])))
    return rights


def staff_of_poi(rights: Rights, n_poi: int, t_ns: int) -> np.ndarray:
    """権利台帳の ``employ`` の行(体 → 店)から、店(POI)→ 担当の体の表を読む(-1=担当なし・複数なら最初の行)。"""
    return rights.holder_table(int(n_poi), kind=EMPLOY, holder_kind=AGENT, object_kind=STORE, t_ns=int(t_ns))
