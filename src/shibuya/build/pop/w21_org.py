"""W21 段 4「組織と関係」(PS5・設計書 §2-5・§2-7・計画 第 4 期 段 4)。版 1.1.0。

正: 設計書 §2-5 PS5(会社と店=法人番号と経済センサス・役割=雇用形態の統計・部署=SR2・権利台帳=CP4・働く人のエージェント
=②群)・§2-7(組織は人の関係と権利台帳で表す・雇用=W16・営業許可=区のオープンデータ・店の賃借=区画にいること(家賃は空欄)・
住まい=国勢調査の割合)・PENDING 仮-23(**席は経済センサス・人数は国勢調査**)・答申 R-116 §1-4・R-80(部署の大きさ)・
SR2 の決定(S = 1 + 業種別の課長 1 人あたりの部下・部の段は腕)。

やること(どれも配列の演算=体ごとの for は無い)
1. **舞台で働く人の数(国勢調査)**: 区で働く 15 歳以上の就業者(従業地 第4表 375,270)× 舞台の割合(経済センサス 第28表の
   町丁目の従業者 × 被覆率 ÷ 区の従業者)。町丁目ごとに整数にする(:func:`stage_worker_targets`)。
2. **住民の勤め先**: 自宅で従業=自宅のセル。自宅外の区内=区の町丁目を経済センサスの従業者の比で引き、被覆率の確率で舞台の
   中(:func:`assign_resident_workplaces`)。区の外=舞台の外(駅まで歩く)。
3. **外から来て働く人(体あり)**: 町丁目ごとの「数 − 舞台で働く住民」を作り、段 3 の関数(従業地 第11-1・8・16-1 表)で
   男女・年齢・産業・地位・職業を引く。常住地は第4表の流入元の重み・駅の口は W12 の鉄道の流入の比。
4. **席(W6=経済センサス)への所属**: 席の地位(経済センサス 第6-2表の 5 区分=個人業主・家族従業者・役員・無期・有期と
   臨時)を組織ごとの従業者に割合で割り振り(:func:`class_seats`)、業種(``industry_key``)× 地位の区分ごとに「席の数」と
   「人の数(国勢調査の地位)」の小さい方を埋める。雇われる人の残りは同じ業種の雇われる人の空いた席へ(:func:`fill_seats_by_role`)。
   人が多い区分の残りは「席の外」(組織は空欄=自分の事業・派遣先など)、席が多い区分の残りは「空席」。腕(``--seat-roles off``)
   は業種だけで埋める(:func:`fill_seats`)。
5. **部署(SR2)**: 組織の人数 n・S = 1 + 課長の部下(R-80)・部署の数 k = max(1, round(n/S))。頭は役割の順(役員・業主 →
   正社員 → …・同じなら年上)で上から k 人。残りは順に部署へ回す(人数は均等)。上司は 1 人(組織の長は 0 人)(:func:`departments`)。
6. **役割**: 地位 → 正社員・派遣社員・パート・アルバイト・役員・業主・家族従業者。組織の長は店なら「店長」・ほかは
   「代表」(役員・業主)か「責任者」。部署の長は「部署長」(部の段の腕では「部長」)。
7. **②群の担当**(``duty_role``): 規則の表(``attr_fns.f_duty_role_org``=expedient)。W16 の在庫(駅員 300 など)は参考=二重。
8. **権利台帳の開始時点の行**(口の約束 1-5 の欄+役割と週の時間): 雇用(体 → 組織)・店の賃借(店 → 区画・家賃は空欄)・
   住まい(世帯主 → 住まい=所有か賃借・段 2 の ``tenure``)・**店の持ち主(組織 → 店)**=同じ建物で業種の合う組織(宣言・
   台帳の閉じた表に「所有 → 店」が無い=``in_closed_table`` が偽)。営業許可は 0 行(区のオープンデータは未取得=空欄)。
9. **関係の行**(1-6 の関係の層の初期値の形): 家族(同じ世帯・種別 1)・同僚(同じ組織の同じ部署・種別 2)・上司と部下(部署の
   長 ↔ 組織の長)。強さ・回数・最初と最後(``rel_n``・``rel_first``・``rel_last``)は空欄=ラン開始時に W17 の共在から
   エンジンが作る(``engine.relations.initial_edges``)。

逐次ループ宣言(P4): 店(POI)ごとの持ち主の当てはめ(POI の数=2,337)と、規則と業種の数ぶん(≤ 20)。体の数に比例する
ループは無い。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

from . import attr_fns as A
from . import fitting as F
from . import w21_checks as WC

__all__ = [
    "SEAT_STATUS", "WORKPLACE_AREAS", "TENURE_RIGHT", "POI_INDUSTRY", "normalize_chome_name",
    "chome_employees", "stage_worker_targets", "assign_resident_workplaces", "fill_seats", "departments",
    "role_words", "relation_pairs", "store_owners", "RIGHT_COLUMNS", "ecen_status_shares", "class_seats",
    "fill_seats_by_role", "EMPLOYEE_CLASSES",
]

#: 席の状態の語。
SEAT_STATUS: Final[tuple[str, ...]] = ("seated", "no_seat_overflow", "no_seat_industry", "home", "outside_stage", "")
#: 勤め先の場所の語(``workplace_area``)。
WORKPLACE_AREAS: Final[tuple[str, ...]] = ("home", "stage", "ward_outside_stage", "outside_ward", "")
#: 住宅の所有の関係(段 2 の ``tenure``)→ 権利の種類(所有/賃借/空欄)。
TENURE_RIGHT: Final[Mapping[str, str]] = MappingProxyType({
    "owned": "own", "public_rent": "lease", "private_rent": "lease", "company_housing": "lease", "room_rent": "lease",
})
#: POI の種類(W6 の ``cat``・``subcat``)→ 店の持ち主を探す組織の業種(W16 の 15 語)。自前(expedient)。
POI_INDUSTRY: Final[Mapping[str, str]] = MappingProxyType({
    "food": "FB", "nightlife": "FB", "hotel": "FB", "shop": "WR", "service": "SV", "leisure": "AM", "cinema": "AM",
    "hall": "AM", "attraction": "AM", "school": "ED", "education": "ED",
    "service|hospital": "MW", "school|childcare": "MW", "leisure|gym": "LS", "nightlife|karaoke": "AM",
    "nightlife|club": "AM", "nightlife|sauna": "LS", "shop|pachinko": "AM",
})
#: 権利台帳の行の欄(口の約束 1-5 の 8 欄を列にした形+役割・週の時間・閉じた表に入るか・注)。
RIGHT_COLUMNS: Final[tuple[str, ...]] = (
    "right_id", "holder_kind", "holder_id", "object_kind", "object_id", "kind", "since_ns", "until_ns",
    "counterparty_kind", "counterparty_id", "source", "cause", "role", "weekly_hours_hint", "in_closed_table", "note",
)

_KANJI = dict(zip("１２３４５６７８９", "一二三四五六七八九"))
_VARIANTS = {"濤": "涛", "鶯": "鴬", "ヶ": "ケ", "ｹ": "ケ"}


def normalize_chome_name(name: str) -> str:
    """経済センサスの町丁目名(全角の数字・異体字)→ 小地域の境界の名(漢数字)。"""
    s = "".join(_KANJI.get(c, c) for c in str(name).strip())
    for a, b in _VARIANTS.items():
        s = s.replace(a, b)
    return s.replace(" ", "").replace("　", "")


def chome_employees(rows: list[list[Any]], items: tuple[str, ...], names80: tuple[str, ...]
                    ) -> tuple[np.ndarray, float, list[str]]:
    """経済センサス 第28表の写し → (80 町丁目の民営の従業者, 区の従業者, 当てはまらなかった末端の行の名)。

    末端の行=丁目の行と、丁目を持たない町の行(町の行は丁目の子がある町なら使わない)。
    """
    j = items.index("総数_従業者数")
    towns_with_children = {r[1] for r in rows if r[0] == "chome"}
    index = {normalize_chome_name(n): i for i, n in enumerate(names80)}
    emp = np.zeros(len(names80))
    ward = 0.0
    miss: list[str] = []
    for r in rows:  # 逐次: 表の行の数ぶん(≈100)
        level, town, chome, vals = r[0], r[1], r[2], r[3]
        v = float(vals[j] or 0.0)
        if level == "ward":
            ward = ward or v
            continue
        if level == "town" and town in towns_with_children:
            continue
        name = chome if level == "chome" else town
        i = index.get(normalize_chome_name(name))
        if i is None:
            miss.append(name)
            continue
        emp[i] += v
    return emp, ward, miss


def stage_worker_targets(emp80: np.ndarray, ward_emp: float, stage_idx: np.ndarray, coverage: np.ndarray,
                         workers_in_ward: float) -> tuple[np.ndarray, float]:
    """舞台の町丁目ごとの「そこで働く人」の数(整数)と舞台の割合 s。人数=区で働く人(国勢調査)× 町丁目の従業者 × 被覆率 ÷
    区の従業者(経済センサス)=席の配分は経済センサス・人数は国勢調査(仮-23)。"""
    share = emp80[stage_idx] * coverage / max(ward_emp, 1.0)
    s = float(share.sum())
    target = workers_in_ward * share
    return F.largest_remainder(target, int(round(float(target.sum())))), s


def assign_resident_workplaces(workplace_kind: np.ndarray, home_chome: np.ndarray, emp80: np.ndarray,
                               stage_idx: np.ndarray, coverage: np.ndarray, u: np.ndarray
                               ) -> tuple[np.ndarray, np.ndarray]:
    """住民の就業者の勤め先の場所(:data:`WORKPLACE_AREAS` の番号)と舞台の町丁目(舞台の中の番号・−1)。

    ``workplace_kind``: 段 3 の従業地(0 自宅・1 自宅外の区内・2 都内の他・3 他県・−1 就業者でない)。``home_chome`` は舞台の
    町丁目の番号。区内の人は区の 80 町丁目を経済センサスの従業者の比で引き(1 つ目の乱数)、その町丁目の被覆率の確率
    (2 つ目の乱数)で舞台の中=距離で重みを付けない(expedient)。
    """
    wk = np.asarray(workplace_kind, dtype=np.int64)
    n = wk.size
    area = np.full(n, WORKPLACE_AREAS.index(""), dtype=np.int64)
    chome = np.full(n, -1, dtype=np.int64)
    home = wk == 0
    area[home] = WORKPLACE_AREAS.index("home")
    chome[home] = np.asarray(home_chome, dtype=np.int64)[home]
    area[(wk == 2) | (wk == 3)] = WORKPLACE_AREAS.index("outside_ward")
    inw = wk == 1
    if inw.any():
        cov80 = np.zeros(emp80.size)
        cov80[stage_idx] = coverage
        pos80 = np.full(emp80.size, -1, dtype=np.int64)
        pos80[stage_idx] = np.arange(stage_idx.size)
        c = np.cumsum(emp80)
        k = np.minimum(np.searchsorted(c / c[-1], u[inw, 0], side="right"), emp80.size - 1)
        in_stage = u[inw, 1] < cov80[k]
        a = np.where(in_stage, WORKPLACE_AREAS.index("stage"), WORKPLACE_AREAS.index("ward_outside_stage"))
        area[inw] = a
        chome[inw] = np.where(in_stage, pos80[k], -1)
    return area, chome


def fill_seats(org_industry: np.ndarray, org_seats: np.ndarray, person_industry: np.ndarray, u: np.ndarray
               ) -> tuple[np.ndarray, np.ndarray, dict[str, dict[str, int]]]:
    """業種ごとに席(組織の従業者=経済センサス)へ人を入れる。返り値=(人 → 組織の番号 −1, 組織ごとの埋まった数, 業種ごとの数)。

    業種 k の席の数 S と人の数 P のうち min(S, P) を埋める。組織ごとの数=席 × min/S の最大剰余(組織の番号の順)。人の順は
    人ごとの乱数 ``u`` の昇順(同じ鍵で同じ順)。業種が空欄・席の無い業種の人は −1。
    """
    oi = np.asarray(org_industry).astype(str)
    os_ = np.asarray(org_seats, dtype=np.int64)
    pi = np.asarray(person_industry).astype(str)
    org_of = np.full(pi.size, -1, dtype=np.int64)
    filled = np.zeros(os_.size, dtype=np.int64)
    report: dict[str, dict[str, int]] = {}
    for k in sorted(set(oi.tolist()) | set(pi.tolist()) - {""}):  # 逐次: 業種の数ぶん(≤ 16)
        orgs = np.flatnonzero(oi == k)
        people = np.flatnonzero(pi == k)
        S = int(os_[orgs].sum())
        P = int(people.size)
        m = min(S, P)
        report[k] = {"seats": S, "people": P, "filled": m, "vacant": S - m, "overflow": P - m}
        if m == 0:
            continue
        quota = F.largest_remainder(os_[orgs] * (m / S), m)
        slots = np.repeat(orgs, quota)
        order = people[np.lexsort((people, u[people]))]
        org_of[order[:m]] = slots
        filled[orgs] = quota
    return org_of, filled, report


def ecen_status_shares(rows62: list[list[Any]], items62: tuple[str, ...]) -> dict[str, np.ndarray]:
    """経済センサス 第6-2表(渋谷区・産業大分類)→ W16 の 15 語ごとの席の地位 5 区分の割合(個人業主・無給の家族従業者・
    有給役員・無期雇用者・有期と臨時の雇用者)。LS と AM はどちらも N(生活関連と娯楽をまとめた大分類)。"""
    col = {lab: items62.index(f"{lab}|従業者数_男女計") for lab in
           ("1_個人業主", "2_無給の家族従業者", "3_有給役員", "41_無期雇用者", "42_有期雇用者", "5_臨時雇用者")}
    major = {str(r[3]): r[-1] for r in rows62 if str(r[2]) == "2"}
    out: dict[str, np.ndarray] = {}
    for key, m in WC.ECEN_MAJOR_OF_KEY.items():  # 逐次: 業種の数ぶん(15)
        v = major.get(m)
        if v is None:
            continue
        x = np.array([v[col["1_個人業主"]] or 0, v[col["2_無給の家族従業者"]] or 0, v[col["3_有給役員"]] or 0,
                      v[col["41_無期雇用者"]] or 0, (v[col["42_有期雇用者"]] or 0) + (v[col["5_臨時雇用者"]] or 0)],
                     dtype=np.float64)
        out[key] = x / max(x.sum(), 1.0)
    return out


def class_seats(org_seats: np.ndarray, shares: np.ndarray) -> np.ndarray:
    """組織ごとの席を地位 5 区分へ割合で分ける(組織ごとの最大剰余・同じ端数なら区分の番号の順)。(組織, 5) の整数。"""
    e = np.asarray(org_seats, dtype=np.int64)
    x = e[:, None] * np.asarray(shares, dtype=np.float64)
    fl = np.floor(x + 1e-9).astype(np.int64)
    r = e - fl.sum(axis=1)
    order = np.argsort(-(x - fl), axis=1, kind="stable")
    rank = np.empty_like(order)
    np.put_along_axis(rank, order, np.arange(x.shape[1])[None, :].repeat(x.shape[0], axis=0), axis=1)
    return fl + (rank < r[:, None]).astype(np.int64)


#: 雇われる人の区分(無期・有期と臨時)=空いた席を相互に使える(2 回目の詰め)。業主・役員・家族従業者は使わない。
EMPLOYEE_CLASSES: Final[tuple[int, ...]] = (3, 4)


def fill_seats_by_role(org_industry: np.ndarray, org_class_seats: np.ndarray, person_industry: np.ndarray,
                       person_class: np.ndarray, u: np.ndarray
                       ) -> tuple[np.ndarray, np.ndarray, dict[str, dict[str, Any]]]:
    """業種 × 地位の区分ごとに席へ人を入れる(席の地位=経済センサス 第6-2表・人の地位=国勢調査=段 3)。

    1 回目: 業種 k・区分 c の席と人の少ない方を埋める(組織ごとの数=その区分の席に比例の最大剰余・人の順は乱数 ``u``)。
    2 回目: 雇われる人(無期・有期と臨時)の残りを、同じ業種の雇われる人の空いた席へ(組織ごとの空きに比例)。業主・役員・
    家族従業者の残りは「席の外」(自分の事業・派遣先など=宣言)。返り値=(人 → 組織 −1, 組織ごとの埋まった数, 業種ごとの数)。
    """
    oi = np.asarray(org_industry).astype(str)
    cs = np.asarray(org_class_seats, dtype=np.int64)
    pi = np.asarray(person_industry).astype(str)
    pc = np.asarray(person_class, dtype=np.int64)
    org_of = np.full(pi.size, -1, dtype=np.int64)
    fcls = np.zeros_like(cs)
    report: dict[str, dict[str, Any]] = {}

    def put(orgs: np.ndarray, cap: np.ndarray, people: np.ndarray) -> np.ndarray:
        S = int(cap.sum())
        m = min(S, int(people.size))
        if m == 0:
            return np.zeros(orgs.size, dtype=np.int64)
        quota = F.largest_remainder(cap * (m / S), m)
        order = people[np.lexsort((people, u[people]))]
        org_of[order[:m]] = np.repeat(orgs, quota)
        return quota

    for k in sorted(set(oi.tolist()) | set(pi.tolist()) - {""}):  # 逐次: 業種の数ぶん(≤ 16)
        orgs = np.flatnonzero(oi == k)
        rep: dict[str, Any] = {"seats": int(cs[orgs].sum()), "people": int((pi == k).sum())}
        by = {}
        for c in range(cs.shape[1]):  # 逐次: 区分の数(5)
            people = np.flatnonzero((pi == k) & (pc == c))
            q = put(orgs, cs[orgs, c], people)
            fcls[orgs, c] += q
            by[WC.ECEN_STATUS5[c]] = {"seats": int(cs[orgs, c].sum()), "people": int(people.size), "filled": int(q.sum())}
        rest = np.flatnonzero((pi == k) & np.isin(pc, EMPLOYEE_CLASSES) & (org_of < 0))
        free = (cs[orgs][:, list(EMPLOYEE_CLASSES)] - fcls[orgs][:, list(EMPLOYEE_CLASSES)]).sum(axis=1)
        q2 = put(orgs, np.maximum(free, 0), rest)
        fcls[orgs, EMPLOYEE_CLASSES[1]] += q2  # 区分をまたいだ分(数えるだけ)
        filled = int(fcls[orgs].sum())
        rep.update({"filled": filled, "vacant": rep["seats"] - filled, "overflow": rep["people"] - filled,
                    "second_pass_employees": int(q2.sum()), "by_class": by})
        report[k] = rep
    return org_of, fcls.sum(axis=1), report


def departments(org_of: np.ndarray, rank: np.ndarray, age: np.ndarray, org_industry: np.ndarray, *,
                division_arm: bool = False) -> dict[str, np.ndarray]:
    """部署(SR2 の決定 (a))と上司。人ごとに(部署の番号・組織の中の順位・頭か・上司の人の番号)を返す(組織の無い人は −1)。

    組織 o の人数 n・S = 1 + R-80 の課長の部下(業種)・部署の数 k = max(1, floor(n/S + 0.5))(≤ n)。順位=役割の順(``rank``
    小さいほど先)→ 年上 → 人の番号。順位 0 が組織の長・1〜k−1 が部署の長・残りは順位の順に部署 0..k−1 へ回す。上司: 組織の
    長は −1・部署の長は組織の長・ほかは自分の部署の長。部の段の腕(``division_arm``): 部の数 g = max(1, floor(n/26.6 + 0.5))
    が 1 < g < k なら部署 d の長の上司は部署 d mod g の長(d ≥ g)=部 0..g−1 の長が「部長」(上司は組織の長)。
    """
    org = np.asarray(org_of, dtype=np.int64)
    n = org.size
    pid = np.arange(n, dtype=np.int64)
    out = {"department": np.full(n, -1, dtype=np.int64), "local_rank": np.full(n, -1, dtype=np.int64),
           "is_org_head": np.zeros(n, dtype=bool), "is_dept_head": np.zeros(n, dtype=bool),
           "is_division_head": np.zeros(n, dtype=bool), "supervisor": np.full(n, -1, dtype=np.int64),
           "n_departments_of_org": np.zeros(int(org.max()) + 1 if n and org.max() >= 0 else 0, dtype=np.int64)}
    m = np.flatnonzero(org >= 0)
    if m.size == 0:
        return out
    order = m[np.lexsort((pid[m], -np.asarray(age, dtype=np.int64)[m], np.asarray(rank, dtype=np.int64)[m], org[m]))]
    og = org[order]
    starts = np.flatnonzero(np.r_[True, og[1:] != og[:-1]])
    sizes = np.diff(np.r_[starts, og.size])
    seg = np.repeat(np.arange(starts.size), sizes)
    r = np.arange(og.size) - starts[seg]
    ind = np.asarray(org_industry).astype(str)[og[starts]]
    S = 1.0 + np.array([A.R80_SUBORDINATES.get(k, 12.6) for k in ind.tolist()])  # 逐次: 組織の数ぶん(写像の引き)
    k = np.minimum(np.maximum(1, np.floor(sizes / S + 0.5).astype(np.int64)), sizes)
    kk = k[seg]
    local_dept = np.where(r < kk, r, (r - kk) % np.maximum(kk, 1))
    base = np.r_[0, np.cumsum(k)[:-1]]
    out["department"][order] = base[seg] + local_dept
    out["local_rank"][order] = r
    head_of_org = order[starts]
    dept_head = order[starts[seg] + local_dept]  # 部署 d の長=順位 d の人
    sup = np.where(r == 0, -1, np.where(r < kk, head_of_org[seg], dept_head))
    if division_arm:
        g = np.maximum(1, np.floor(sizes / (1.0 + A.R80_DIVISION_SUBORDINATES) + 0.5).astype(np.int64))
        gg = g[seg]
        use = (gg > 1) & (gg < kk)
        lower_head = use & (r >= gg) & (r < kk)
        sup = np.where(lower_head, order[starts[seg] + (r % np.maximum(gg, 1))], sup)
        out["is_division_head"][order] = use & (r >= 1) & (r < gg)
    out["supervisor"][order] = sup
    out["is_org_head"][order] = r == 0
    out["is_dept_head"][order] = r < kk
    out["n_departments_of_org"][og[starts]] = k
    return out


def role_words(base_role: np.ndarray, deps: Mapping[str, np.ndarray], org_of: np.ndarray, org_industry: np.ndarray,
               rank: np.ndarray) -> np.ndarray:
    """役割の語。組織の長: 店(:data:`attr_fns.STORE_INDUSTRIES`)は「店長」・ほかは役員・業主なら「代表」・それ以外は
    「責任者」。部の長(腕)は「部長」・部署の長は「部署長」・ほかは地位の語(``base_role``)。"""
    out = np.asarray(base_role, dtype=object).copy()
    org = np.asarray(org_of, dtype=np.int64)
    ind = np.where(org >= 0, np.asarray(org_industry).astype(str)[np.clip(org, 0, None)], "")
    store = np.isin(ind, A.STORE_INDUSTRIES)
    oh = deps["is_org_head"]
    out[oh & store] = "店長"
    out[oh & ~store & (np.asarray(rank) == 0)] = "代表"
    out[oh & ~store & (np.asarray(rank) != 0)] = "責任者"
    out[deps["is_dept_head"] & ~oh] = "部署長"
    out[deps["is_division_head"] & ~oh] = "部長"
    return out


def relation_pairs(group: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """同じ組(世帯・部署)の人の有向の組を全部(自分を除く)。``group`` は人ごとの組の番号(−1=組なし)。"""
    g = np.asarray(group, dtype=np.int64)
    m = np.flatnonzero(g >= 0)
    if m.size == 0:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64)
    order = m[np.lexsort((m, g[m]))]
    gg = g[order]
    starts = np.flatnonzero(np.r_[True, gg[1:] != gg[:-1]])
    sizes = np.diff(np.r_[starts, gg.size])
    seg = np.repeat(np.arange(starts.size), sizes)
    pos = np.arange(gg.size) - starts[seg]
    cnt = sizes[seg] - 1
    u = np.repeat(order, cnt)
    rs = np.repeat(np.arange(gg.size), cnt)
    first = np.r_[0, np.cumsum(cnt)[:-1]]
    q = np.arange(int(cnt.sum())) - np.repeat(first, cnt)
    q = q + (q >= pos[rs])
    v = order[starts[seg[rs]] + q]
    return u, v


def store_owners(poi_cat: np.ndarray, poi_subcat: np.ndarray, poi_building: np.ndarray, org_industry: np.ndarray,
                 org_building: np.ndarray) -> np.ndarray:
    """店(POI)→ 持ち主の組織の番号(−1=見つからない)。同じ建物で業種の合う組織のうち、持つ店の数が少ない順(同じなら組織の
    番号)。自前の規則(expedient・宣言)。"""
    cat = np.asarray(poi_cat).astype(str)
    sub = np.asarray(poi_subcat).astype(str)
    pb = np.asarray(poi_building).astype(str)
    oi = np.asarray(org_industry).astype(str)
    ob = np.asarray(org_building).astype(str)
    by_key: dict[tuple[str, str], list[int]] = {}
    for i, (b, k) in enumerate(zip(ob.tolist(), oi.tolist())):  # 逐次: 組織の数ぶん(索引を作る)
        by_key.setdefault((b, k), []).append(i)
    owned = np.zeros(oi.size, dtype=np.int64)
    out = np.full(cat.size, -1, dtype=np.int64)
    for j in range(cat.size):  # 逐次: POI の数ぶん(2,337)
        ind = POI_INDUSTRY.get(f"{cat[j]}|{sub[j]}") or POI_INDUSTRY.get(cat[j])
        if not ind or pb[j] in ("", "None", "nan"):
            continue
        cand = by_key.get((pb[j], ind))
        if not cand:
            continue
        best = min(cand, key=lambda o: (owned[o], o))
        out[j] = best
        owned[best] += 1
    return out
