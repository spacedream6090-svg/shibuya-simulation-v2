"""W21 段 10 の材料(第 4 期 4-1・差し替えそのもの=版上げ 3 回目は別の発注)。

正: 発注 段 8〜10 の「段 10 の材料」・PENDING 仮-31(親の判断: W20 への口は段 10 で W21 から ``Attributes`` を作る関数・
担当は勤め先が舞台の中の体だけ・段 3 の役員/業主は第6-2表の比で分ける・W16 の運輸の行は段 10 で残す)・記録 pop41b §14。

1. **地位の分けと席の数え直し**(:func:`status_split_table`・:func:`seat_recount`): 段 3 の外から来て働く人の「雇用者で
   ない人」(雇人のない業主に寄せた)を ``attr_fns.commuter_status_split``(第6-2表の有給役員・個人業主・無給の家族従業者の
   比)で分け、段 4 の席への所属(``w21_org.fill_seats_by_role``=同じ乱数の鍵 ``w21b.org.seat``)を数え直す。段 1〜7 の資産は
   書かない=差し替えは段 10。分けの前の地位で数え直すと段 4 の所属と同じになる(試験=写しの検査)。
2. **権利台帳の「体 → 店」の雇用の行**(:func:`store_staff_rows`=engine の ``rights.initial.staff_of_poi`` が読む形=口の約束
   1-5 の閉じた表の ``employ`` → ``store``): 段 4 の店の持ち主(組織 → 店)の組織に所属した体を、その組織の店へ順に振る
   (組織の長 → 部署の長 → 人の番号の順・店が 2 つ以上なら順に回す)。店ごとの最初の行=担当(``staff_of_poi`` は最初の行を
   読む)。店の番号は店の賃借の行(店 → 区画)と同じ W6 の POI の番号。持ち主の無い店は行なし(数える)。
3. **W16 の在庫の行をどう残すかの表**(:func:`w16_keep_table`): 運輸(鉄道・バス・タクシー=W6 に会社が無い)は残す・W21 の
   体がある群(住民・区内で働く住民・外から来て働く人・担当の語が W21 にある乗務員など)は外す・W21 に替わりの無い群(来街・
   通学・指令・路上の役割ほか)は残す(どれも案=段 10 の発注で親が決める)。

当てはめの宣言は ``w21_build_c.W21C_EXPEDIENTS``(つなぎの台帳と 1 対 1)。

逐次ループ宣言(P4): 業種の数ぶん(20)・W16 の群の数ぶん(≤ 40)。体の数に比例するループは無い。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np
import pyarrow as pa

from shibuya.core.rng import k19_counter_array, philox_array, unit_float

from . import attr_fns as A
from . import w21_checks as WC
from . import w21_org as O

__all__ = ["STATUS_SPLIT_SOURCE", "status_split_table", "seat_recount", "store_staff_rows", "w16_keep_table",
           "W16_KIND_WORDS", "W16_TRANSPORT_KEEP", "STORE_STAFF_SOURCE", "STORE_STAFF_NOTE"]

STATUS_SPLIT_SOURCE: Final[str] = "経済センサス2021 第6-2表(渋谷区・産業大分類・民営)の有給役員・個人業主・無給の家族従業者の人数"
STORE_STAFF_SOURCE: Final[str] = "w21c:店の持ち主の組織に所属した体(体 → 店・段 4 の所属と店の持ち主)"
STORE_STAFF_NOTE: Final[str] = "店の番号=店の賃借の行(店 → 区画)と同じ W6 の POI の番号・店ごとの最初の行=担当(staff_of_poi)"
#: W16 の種別の番号 → 語(``agents.state.AgentKind`` と同じ並び=段 3 の ``attr_fns.W16_KIND`` の値)。
W16_KIND_WORDS: Final[Mapping[int, str]] = MappingProxyType({0: "commuter", 1: "visitor", 2: "worker", 3: "resident",
                                                             4: "dispatcher", 5: "student", 6: "regular_visitor",
                                                             7: "foreign_visitor", 8: "crew"})
#: 残す W16 の運輸の担当(W6 に鉄道・バス・タクシーの会社が無い=親の判断 仮-31)。
W16_TRANSPORT_KEEP: Final[tuple[str, ...]] = ("駅員", "車掌", "電車運転士", "バス運転士", "タクシー運転手")


def status_split_table(rows62: list[list[Any]], items62: tuple[str, ...]) -> np.ndarray:
    """第6-2表(渋谷区・産業大分類の行)→ (産業大分類 20, 3) の人数(:data:`attr_fns.STATUS_SPLIT_COLUMNS` の並び)。
    民営の表なので公務(S)と分類不能(T)の行は 0(分けない=元の地位のまま)。"""
    col = [items62.index(f"{lab}|従業者数_男女計") for lab in A.STATUS_SPLIT_COLUMNS]
    major = {str(r[3]): r[-1] for r in rows62 if str(r[2]) == "2"}
    out = np.zeros((len(A.INDUSTRY_MAJORS), len(col)))
    for i, m in enumerate(A.INDUSTRY_MAJORS):  # 逐次: 産業大分類(20)
        v = major.get(m)
        if v is not None:
            out[i] = [float(v[j] or 0) for j in col]
    return out


def _u(seed: int | str, domain: str, ids: np.ndarray) -> np.ndarray:
    return unit_float(philox_array(seed, domain, k19_counter_array(np.asarray(ids, dtype=np.int64)), words=1))[:, 0]


def seat_recount(people: Mapping[str, Any], org_industry: np.ndarray, org_seats: np.ndarray, rows62: list[list[Any]],
                 items62: tuple[str, ...], emp_status_words: np.ndarray, seed: int | str
                 ) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    """段 4 の席への所属を ``emp_status_words``(人ごとの従業上の地位の語)で数え直す(段 4 と同じ席・同じ乱数の鍵)。
    返り値=(人 → 組織の番号 −1, 組織ごとの埋まった数, 業種ごとの数)。"""
    o_ind = np.asarray(org_industry, dtype=object).astype(str)
    shares = O.ecen_status_shares(rows62, items62)
    uk, inv = np.unique(o_ind, return_inverse=True)
    lut = np.stack([shares.get(k, np.full(5, 0.2)) for k in uk.tolist()]) if uk.size else np.zeros((0, 5))  # 逐次: 業種
    sh_org = lut[np.asarray(inv).reshape(-1)] if uk.size else np.zeros((0, 5))
    pid = np.asarray(people["person_id"], dtype=np.int64)
    area = np.asarray(people["workplace_area"], dtype=object).astype(str)
    ik = np.asarray(people["industry_key"], dtype=object).astype(str)
    p_ind = np.where(area == "stage", ik, "")
    st = np.asarray(emp_status_words, dtype=object).astype(str)
    su, sinv = np.unique(st, return_inverse=True)
    pcls = np.array([WC.CENSUS_TO_ECEN5.get(x, -1) for x in su.tolist()], dtype=np.int64)[np.asarray(sinv).reshape(-1)]
    useat = _u(seed, "w21b.org.seat", pid)
    return O.fill_seats_by_role(o_ind, O.class_seats(np.asarray(org_seats, dtype=np.int64), sh_org), p_ind, pcls, useat)


def store_staff_rows(people: Mapping[str, Any], rights: Mapping[str, Any]) -> dict[str, Any]:
    """権利台帳の「体 → 店」の雇用の行(口の約束 1-5 の 8 欄+役割・週の時間・閉じた表に入るか・注=``O.RIGHT_COLUMNS``)。"""
    hk = np.asarray(rights["holder_kind"], dtype=object).astype(str)
    ok_ = np.asarray(rights["object_kind"], dtype=object).astype(str)
    kd = np.asarray(rights["kind"], dtype=object).astype(str)
    own = (hk == "org") & (ok_ == "store") & (kd == "own")
    s_org = np.asarray(rights["holder_id"], dtype=np.int64)[own]
    s_store = np.asarray(rights["object_id"], dtype=np.int64)[own]
    o = np.lexsort((s_store, s_org))
    s_org, s_store = s_org[o], s_store[o]
    pid = np.asarray(people["person_id"], dtype=np.int64)
    org = np.asarray(people["org_index"], dtype=np.int64)
    n_org = int(max(org.max() if org.size else -1, s_org.max() if s_org.size else -1)) + 1
    k = np.bincount(s_org, minlength=n_org) if s_org.size else np.zeros(n_org, dtype=np.int64)
    start = np.r_[0, np.cumsum(k)[:-1]] if n_org else np.zeros(0, dtype=np.int64)
    sel = np.flatnonzero((org >= 0) & (k[np.clip(org, 0, None)] > 0)) if n_org else np.zeros(0, dtype=np.int64)
    head = np.asarray(people["is_org_head"], dtype=bool)
    dhead = np.asarray(people["is_dept_head"], dtype=bool)
    order = sel[np.lexsort((pid[sel], ~dhead[sel], ~head[sel], org[sel]))]
    og = org[order]
    first = np.r_[True, og[1:] != og[:-1]] if og.size else np.zeros(0, dtype=bool)
    starts = np.flatnonzero(first)
    rank = np.arange(og.size) - np.repeat(starts, np.diff(np.r_[starts, og.size])) if og.size else og
    store = s_store[start[og] + rank % k[og]] if og.size else og
    o2 = np.lexsort((rank, store))
    holder, store, rank = pid[order][o2], store[o2], rank[o2]
    roles = np.asarray(people["org_role"], dtype=object)[order][o2]
    hours = np.asarray(people["weekly_hours_hint"], dtype=np.float64)[order][o2]
    m = int(holder.size)
    out: dict[str, Any] = {
        "right_id": np.arange(m, dtype=np.int64), "holder_kind": np.full(m, "agent", dtype=object),
        "holder_id": holder.astype(np.int64), "object_kind": np.full(m, "store", dtype=object),
        "object_id": store.astype(np.int64), "kind": np.full(m, "employ", dtype=object),
        "since_ns": pa.nulls(m, type=pa.int64()), "until_ns": pa.nulls(m, type=pa.int64()),
        "counterparty_kind": np.full(m, "", dtype=object), "counterparty_id": np.full(m, -1, dtype=np.int64),
        "source": np.full(m, STORE_STAFF_SOURCE, dtype=object),
        "cause": pa.nulls(m, type=pa.struct([("t_ns", pa.int64()), ("seq", pa.int64())])),
        "role": roles, "weekly_hours_hint": hours.astype(np.float32), "in_closed_table": np.ones(m, dtype=bool),
        "note": np.full(m, STORE_STAFF_NOTE, dtype=object),
    }
    return {k_: out[k_] for k_ in O.RIGHT_COLUMNS}


def w16_keep_table(w16_kind: np.ndarray, w16_duty: np.ndarray, w16_synthetic: np.ndarray,
                   w21_duty_counts: Mapping[str, int], w21_counts: Mapping[str, int]) -> dict[str, Any]:
    """W16 の在庫の行を(種別, 担当の語)の群ごとに数え、段 10 での扱いの案(残す/外す)と W21 の体の数を並べる。"""
    kind = np.asarray(w16_kind, dtype=np.int64)
    duty = np.asarray(w16_duty, dtype=object)
    duty = np.where(np.equal(duty, None), "", duty).astype(str)
    syn = np.asarray(w16_synthetic, dtype=bool)
    key = np.char.add(np.char.add(kind.astype(str), "|"), duty)
    uk, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    inv = np.asarray(inv).reshape(-1)
    syn_n = np.bincount(inv, weights=syn.astype(np.float64), minlength=uk.size)
    rows = []
    for g, c, s in zip(uk.tolist(), cnt.tolist(), syn_n.tolist()):  # 逐次: 群の数(≤ 40)
        k, d = g.split("|", 1)
        kw = W16_KIND_WORDS.get(int(k), k)
        w21 = int(w21_duty_counts.get(d, 0)) if d else None
        if kw in ("commuter", "worker") or (kw == "resident" and not d):
            act, note = "replace", "W21 の体がある(住民・区内で働く住民・外から来て働く人)"
            w21 = int(w21_counts.get("residents" if kw != "commuter" else "commuters", 0))
        elif kw == "resident" and d:
            act, note = "replace_no_equivalent", "住民の行は W21 の住民に替わる=この担当の語は W21 に無い(親の判断)"
        elif d in W16_TRANSPORT_KEEP:
            act, note = "keep_transport", "W6 に鉄道・バス・タクシーの会社が無い=W16 の運輸の行を残す(仮-31)"
        elif d and w21:
            act, note = "replace", "W21 の担当に同じ語がある(勤め先が舞台の中の体)"
        else:
            act, note = "keep_no_w21", "W21 に体が無い(来街・通学・指令・路上の役割ほか=段 7 は層の表だけ)"
        rows.append({"w16_kind": int(k), "kind_word": kw, "duty_role": d, "w16_rows": int(c), "w16_synthetic": int(s),
                     "w21_bodies": w21, "action": act, "note": note})
    out_rows = sum(r["w16_rows"] for r in rows if r["action"].startswith("replace"))
    kept = sum(r["w16_rows"] for r in rows if r["action"].startswith("keep"))
    dup = {d: int(w21_duty_counts.get(d, 0)) for d in W16_TRANSPORT_KEEP if int(w21_duty_counts.get(d, 0)) > 0}
    return {"rows": rows, "w16_total": int(kind.size), "rows_removed_stage10": int(out_rows), "rows_kept": int(kept),
            "w21_duty_double_with_kept_transport": dup,
            "note": "action は案(段 10 の発注で親が決める)。運輸を残すと W21 の駅員・電車運転士・車掌の体と二重になる"}
