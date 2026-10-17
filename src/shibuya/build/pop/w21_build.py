"""W21(第 4 期 4-1 段 1〜3「人数の枠・世帯と人・属性」)の組み立て。版 1.0.0。

    python -m shibuya.build.pop.w21_build --out data/world/v2_stage_4-1 --data data [--world data/world/v2]
        [--seed 20260909] [--w21-anneal {on,off}] [--anneal-iter 400000]

- 資産は ``--out`` に書く(本体の ``data/world/v2`` は書かない=既定は不変)。W21 は ``build.run`` の段の一覧
  (``pop.STAGES``)に入れない=本体の ``build_manifest.json`` と build_hash は動かない(W16 との差し替えは段 10=4-3)。
- 出力: ``w21_frame.json``(段 1)・``w21_households.parquet``・``w21_persons.parquet``(段 2・3)・``w21_checks.json``
  (計器)・``w21_manifest.json``(材料の表の statInfId と md5・seed・版・不詳の数・詰めの前後の誤差・出力の sha256 と
  ``w21_build_hash``)・``W21.header.json``(他の段と同じ見出しの形)。時刻など決まらない値は書かない(2 回組んで一致)。
- 読み口は ``w21_sources.W21Guard``(検証側の表と列は開く前に止める・守りの間は Python の ``open`` も検査)。
- 近似の宣言は :data:`W21_EXPEDIENTS`(つなぎの台帳に 1 行ずつ・``EX-build.pop.w21_build-<sha8>``)。

逐次ループ宣言(P4): 段の手順の数ぶん。各手順の宣言は各モジュール(``w21_tables``・``w21_households``・
``attr_fns``・``w21_attrs``・``w21_checks``)。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any, Final, Mapping

import numpy as np
import pyarrow as pa

from shibuya.core.rng import k19_counter_array, philox_array, unit_float

from ..geo import common as C
from . import attr_fns as A
from . import fitting as F
from . import shapefile as SH
from . import w16_population as W16
from . import w21_attrs as WA
from . import w21_checks as WC
from . import w21_frame as WF
from . import w21_households as H
from . import w21_sources as S
from . import w21_tables as T

__all__ = ["STAGE", "STAGE_VERSION", "DEFAULT_SEED", "W21_EXPEDIENTS", "OUTPUTS", "RELATION_WORDS", "build",
           "check_out", "ProtectedOutputError", "OWN_ASSET_PREFIX", "main"]

STAGE: Final[str] = "W21"
STAGE_VERSION: Final[str] = "1.0.0"
#: 母集団の seed(W16 と同じ親の seed・ドメインは ``w21.*``)。
DEFAULT_SEED: Final[int] = W16.MASTER_SEED
#: 出力(``w21_build_hash`` はこの順の sha256 を連ねた文字列の sha256)。
OUTPUTS: Final[tuple[str, ...]] = ("w21_frame.json", "w21_households.parquet", "w21_persons.parquet",
                                   "w21_checks.json")
MANIFEST_NAME: Final[str] = "w21_manifest.json"
#: 続き柄の番号(第13-1表)→ 人の列の語。
RELATION_WORDS: Final[Mapping[str, str]] = MappingProxyType({
    "01": "head", "02": "spouse", "03": "child", "04": "child_spouse", "05": "parent", "06": "parent_in_law",
    "07": "grandchild", "08": "grandparent", "09": "sibling", "10": "other_relative", "11": "live_in_employee",
    "12": "non_relative",
})

#: W21 の近似の宣言(つなぎの台帳の行と 1 対 1・時点と不詳の 4 行は 2025 の小地域の表の公表の後=4-3 以降)。
W21_EXPEDIENTS: Final[tuple[str, ...]] = (
    "時点の混ぜ方: 町丁目の表は 2020 の形のまま、区の 2025 の分類ごとの総数へ IPF で合わせる(2025 の小地域の表が出たら差し替える)",
    "町丁目の年齢・配偶関係・家族類型の「不詳」は、区の 2020 の遡及の不詳補完値と原数値の差の比で割り振る",
    "町丁目の労働力状態・従業上の地位・従業地・在学・居住期間・住居の種類の「不詳」は、町丁目 × 男女の既知の比で割り振る(不詳は無作為と仮定)",
    "2025 の区の表が無い町丁目の表(住宅の所有・建て方・就業・在学・居住期間)は 2020 の形のまま総数を人口・世帯の比で直す",
    "舞台の範囲は町丁目の被覆率(10m 標本格子)で按分する(W16#1・#2 と同じ)",
    "世帯員の続き柄の並びは家族類型と世帯人員から自前の表(COMPOSITION)で決め、他の親族の続き柄は区の第13-1表の比で引く",
    "年齢の窓: 子は若い方の親より 15 歳以上若く母より 50 歳・父より 65 歳以内、世帯主の父母は 15〜50 歳上、孫は 30 歳以上下、祖父母は 30 歳以上上、兄弟姉妹は ±20 歳(自前の値)",
    "ひとり親と子の世帯は親を世帯主にし、夫婦は異性とする(子が世帯主の世帯・同性の夫婦は作らない)",
    "15 歳未満の世帯主は作らない(区の第12-1表には 14 世帯ある)",
    "施設等の世帯の人は 1 人 1 世帯(家族類型 institution)・男女と年齢は区の総人口と一般世帯人員の差・配偶関係は単独世帯の世帯主の比",
    "世帯人員 7 人以上の世帯は 7 人として組む",
    "単独世帯の世帯主は、町丁目の年齢 × 男女の目標からほかの世帯員を引いた残りの比で数を決める(階級の中の各歳と配偶関係は第12-1表)",
    "詰め(焼きなまし)の回数 400,000・温度 2.0 から 0.02・目的関数は町丁目 × 年齢 16 階級 × 男女と配偶関係 3 区分 × 男女の誤差の絶対値の和・動かすのは同じ家族類型と世帯人員の世帯どうしの町丁目",
    "住宅の所有の関係と建て方は、町丁目の中で世帯の型と独立に割り当てる",
    "建て方から建物の階の区分へ(一戸建・長屋建・共同住宅 1・2 階=2 階以下、3〜5、6〜10、11 階以上)・区分の建物が無ければ町丁目の住居系の建物全部",
    "外国人は世帯ごとに選ぶ(重み=2025 の補完値の国籍総数 − 日本人の男女 × 年齢の割合)・数は第2表の町丁目の外国人 × 2025 の補完値の総数・国籍は空欄",
    "就業・従業上の地位・産業・職業・従業地は区の結合表(第3-1・5-1・10-1 表・従業地 第8表)を事前の重みにし、町丁目 × 男女の周辺へ寄せて引く(raking)",
    "完全失業者の年齢の重み(15〜69 歳 1・70 歳以上 0.3)と、就業率の事前の重み(就業者 ÷ 2020 の遡及の補完値の一般世帯人員)",
    "在学の年齢の窓(SCHOOL_AGE_WEIGHTS)は学年の区切りを年齢に当てた自前の表",
    "居住期間は年齢で上限を切るだけで、世帯員どうしをそろえない",
    "産業大分類から industry_key へ(N は経済センサスの駅周辺 13 町丁目の中分類の比で LS/AM・A・B・C・F・S・T は空欄)",
    "従業上の地位から employment_status へ(派遣・パートは non_regular・役員は executive・業主と家庭内職者は self_employed)",
    "外から来る人の地位は従業地の第8表の産業ごとの地位の組で、雇用者でない人は雇人のない業主に寄せる・職業は第16-1表(産業)だけで年齢を見ない",
    "年齢の上限 105 歳(各歳の表の 105 歳より上は 105 歳に寄せる)",
    "年齢の窓が空になる続き柄は引き直す: 孫と祖父母は世帯主と 30 歳(親子の最小の差 15 歳の 2 倍)以上離し、子の配偶者は世帯主 30 歳以上の世帯だけ・父母のいる世帯の世帯主は 90 歳まで・子の窓の下の端が上の端を越えたら下の端を外す",
    "外から来る通学者(通学地が渋谷区で他の市区町村に住む人)の男女と年齢は第1-3表(5 歳階級の中は一様・15 歳未満は 6〜14 歳)・在学の種類は年齢の窓の在学の 6 区分から・ほかの属性は空欄",
    "employment_status から W16 の employment の 6 値(正規・非正規・役員・自営業主・家族従業者・非就業)への写像(空欄と None は非就業)",
)

_TENURE_WORDS = T.TENURE
_BUILDING_WORDS = T.BUILDING


def _hh_uniform(seed: int | str, domain: str, keys: np.ndarray, serial: np.ndarray) -> np.ndarray:
    return unit_float(philox_array(seed, domain, k19_counter_array(keys, serial)))[:, 0]


#: W21 が書いてよい ``data/world`` の下の置き場の名の頭(段の資産)。ほかの既存の置き場(本体の v2・他の段の資産・
#: 退避)には書かない〔検収 M1〕。
OWN_ASSET_PREFIX: Final[str] = "v2_stage_4-1"


class ProtectedOutputError(ValueError):
    """``--out`` が本体の v2・読む世界資産・既存の資産の置き場の中を指している(何も書かずに止める)。"""


def check_out(data: Path, out: Path, world: Path) -> None:
    """出力先の検査: 本体の ``data/world/v2``・``--world`` の中と、``data/world`` の下の既存の置き場(W21 の段の資産
    ``v2_stage_4-1*`` を除く)の中なら止める。"""
    o = Path(out).resolve()
    v2 = (Path(data) / "world" / "v2").resolve()
    for root in (v2, Path(world).resolve()):
        if o == root or root in o.parents:
            raise ProtectedOutputError(f"W21 は本体の v2 と読む世界資産の中に書かない: {o.name}")
    wroot = (Path(data) / "world").resolve()
    if wroot in o.parents:
        top = o.relative_to(wroot).parts[0]
        if (wroot / top).exists() and not top.startswith(OWN_ASSET_PREFIX):
            raise ProtectedOutputError(f"W21 は既存の資産の置き場に書かない: {top}")


def build(data: Path, out: Path, *, world: Path | None = None, seed: int | str = DEFAULT_SEED,
          anneal: H.AnnealParams = H.AnnealParams()) -> tuple[C.StageResult, dict[str, Any]]:
    """W21 を組んで ``out`` に書く。返り値は(見出し, manifest)。``out`` は :func:`check_out` で先に確かめる。"""
    data, out = Path(data), Path(out)
    world = Path(world) if world is not None else data / "world" / "v2"
    check_out(data, out, world)
    out.mkdir(parents=True, exist_ok=True)
    guard = S.W21Guard.for_build(data, world=world, out=out)
    with guard.active():
        res, manifest = _build(guard, data, out, world, seed, anneal)
    return res, manifest


def prepare(guard: S.W21Guard, data: Path, world: Path) -> SimpleNamespace:
    """町丁目の境界・被覆率・建物と、段 2 の手順 1・2(区の雛形と町丁目の目標)。段 4〜7(``w21_build_b``)も同じ値を使う。"""
    # ---- 町丁目の境界・被覆率・建物(W16 と同じ読み方)
    shp = guard.check(data.joinpath(*S.source("sa_shp").path))
    dbf = guard.check(data.joinpath(*S.source("sa_dbf").path))
    guard.md5_only(shp, want_md5=S.source("sa_shp").md5)
    guard.md5_only(dbf, want_md5=S.source("sa_dbf").md5)
    polys_ll = SH.read_shp(shp)
    chome = SH.read_dbf(dbf)
    polys = [p.transformed(lambda lon, lat: ((lon - C.ORIGIN_LATLON[1]) * C.M_PER_DEG_LON,
                                             (lat - C.ORIGIN_LATLON[0]) * C.M_PER_DEG_LAT)) for p in polys_ll]
    keys80 = tuple(str(r["KEY_CODE"]) for r in chome)
    cells = guard.read_parquet(world / "w2_cells.parquet", ["place_id"])
    place_to_cell = {pid: i for i, pid in enumerate(cells["place_id"])}
    coverage, _area, cover_cells = W16._chome_coverage(polys, place_to_cell, W16.COVERAGE_STEP_M)
    bld = guard.read_parquet(world / "w4_buildings.parquet", ["kind", "levels", "area_m2", "centroid_x", "centroid_y"])
    bx = np.asarray(bld["centroid_x"], dtype=np.float64)
    by = np.asarray(bld["centroid_y"], dtype=np.float64)
    b_levels_raw = np.asarray(bld["levels"], dtype=np.int64)
    b_floor = np.asarray(bld["area_m2"], dtype=np.float64) * np.maximum(b_levels_raw, W16.DEFAULT_LEVELS)
    b_res = np.isin(np.asarray(bld["kind"], dtype=object), np.asarray(W16.RESIDENTIAL_KINDS))
    b_cell = np.array([place_to_cell.get(C.place_id(int(i), int(j), "GL"), -1)
                       for i, j in zip(np.floor(bx / C.CELL_M).astype(np.int64),
                                       np.floor(by / C.CELL_M).astype(np.int64))], dtype=np.int64)
    b_chome = SH.assign_points_to_polygons(bx, by, polys)

    # ---- 段 2 手順 1・2: 区の雛形と町丁目の目標
    ct, unk = T.load_chome(guard, keys80)
    ward = T.load_ward(guard, ct.ward_raw_age16, ct.ward_raw_marital3, ct.ward_raw_group)
    ct = T.fill_unknown(ct, unk, ward)
    tg = T.make_targets(ct, ward, coverage)
    return SimpleNamespace(polys=polys, chome=chome, keys80=keys80, place_to_cell=place_to_cell, coverage=coverage,
                           cover_cells=cover_cells, bx=bx, by=by, b_levels_raw=b_levels_raw, b_floor=b_floor,
                           b_res=b_res, b_cell=b_cell, b_chome=b_chome, ct=ct, unk=unk, ward=ward, tg=tg)


def _build(guard: S.W21Guard, data: Path, out: Path, world: Path, seed: int | str,
           anneal: H.AnnealParams) -> tuple[C.StageResult, dict[str, Any]]:
    g = prepare(guard, data, world)
    keys80, coverage, cover_cells = g.keys80, g.coverage, g.cover_cells
    b_levels_raw, b_floor, b_res, b_cell, b_chome = g.b_levels_raw, g.b_floor, g.b_res, g.b_cell, g.b_chome
    ct, unk, ward, tg = g.ct, g.unk, g.ward, g.tg
    C_ = tg.stage_idx.size
    stage_keys = [keys80[i] for i in tg.stage_idx]
    key_int = np.array([int(k) for k in stage_keys], dtype=np.int64)

    # ---- 手順 3・4: 世帯の数え → 世帯 → 世帯員
    ints, _real, cell_info = H.household_cells(tg, ward)
    inst_target = np.clip(tg.institution, 0.0, None)
    inst = F.largest_remainder(inst_target, int(round(float(inst_target.sum()))))
    hd = H.make_households(ints, inst, key_int)
    hd = H.compose_members(hd)
    hd = H.draw_members(hd, ward, seed, tg.age16_sex)

    # ---- 手順 5: 詰め
    target_vec = H.anneal_targets(tg)
    ainfo = H.anneal(hd, target_vec, anneal, seed)

    # ---- 住宅の所有・建て方 → 手順 6 建物 → 手順 7 外国人
    nonin = hd.hh_type >= 0
    u_t = _hh_uniform(seed, "w21.tenure", hd.hh_chome_key, hd.hh_serial)
    u_b = _hh_uniform(seed, "w21.building", hd.hh_chome_key, hd.hh_serial)
    u_p = _hh_uniform(seed, "w21.place", hd.hh_chome_key, hd.hh_serial)
    tenure = H.assign_categories(hd.hh_chome, tg.tenure, u_t, nonin)
    btype = H.assign_categories(hd.hh_chome, tg.building, u_b, nonin)
    btype_place = np.where(btype >= 0, btype, len(_BUILDING_WORDS) - 1)
    home_b, home_c, place_stats = H.place_households(hd.hh_chome, btype_place, tg.stage_idx, b_chome, b_cell, b_res,
                                                     b_floor, b_levels_raw, cover_cells, u_p)
    foreign = H.choose_foreign(hd, tg.foreign, ward, seed)

    # ---- 並べ方(町丁目の鍵 → 生まれた町丁目の鍵 → 通し番号)と id
    final_key = np.asarray(stage_keys, dtype=object)[hd.hh_chome]
    order = np.lexsort((hd.hh_serial, hd.hh_chome_key, final_key.astype(str)))
    rank = np.empty_like(order)
    rank[order] = np.arange(order.size)
    m_order = np.lexsort((hd.m_no, rank[hd.m_hh]))
    hh_id_of_member = rank[hd.m_hh][m_order]

    types = np.array([*T.FAMILY_TYPES, "institution"], dtype=object)
    ht = np.where(hd.hh_type >= 0, hd.hh_type, len(T.FAMILY_TYPES))
    fam = types[ht]
    grp = np.array([T.GROUP_OF_TYPE.get(t, "institution") for t in types], dtype=object)[ht]
    head_rows = np.flatnonzero(hd.m_slot == H.HEAD)
    head_of = np.full(hd.n_households, -1, dtype=np.int64)
    head_of[hd.m_hh[head_rows]] = head_rows

    m = m_order
    marital_words = np.array([*T.MARITAL, ""], dtype=object)
    rel_words = _map_words(hd.m_rel[m], RELATION_WORDS)
    in_inst = hd.hh_type[hd.m_hh[m]] < 0
    rel_words[in_inst] = "institution_resident"  # 施設等の世帯の人は世帯主にしない(15 歳未満の入所者がいる)
    persons: dict[str, Any] = {
        "kind": np.full(m.size, "resident", dtype=object),
        "sex": hd.m_sex[m],
        "age": hd.m_age[m],
        "marital": hd.m_marital[m],
        "chome": hd.hh_chome[hd.m_hh[m]],
        "persona_kind": np.full(m.size, "in_area", dtype=object),
        "role": np.full(m.size, "resident", dtype=object),
    }
    counters = np.stack([hd.hh_chome_key[hd.m_hh[m]], hd.hh_serial[hd.m_hh[m]], hd.m_no[m]], axis=1)

    # ---- 段 3: 属性
    tables, unk_attr = WA.build_tables(guard, keys80, tg.stage_idx, tg.coverage, tg.ratios["r_pop"])
    attrs = WA.apply_attrs(persons, tables, seed, counters)

    # ---- 出力の列
    hh_cols = {
        "household_id": rank[order].astype(np.int32),
        "chome_key": pa.array(final_key[order].tolist(), type=pa.string()),
        "home_building": home_b[order].astype(np.int32),
        "home_cell": home_c[order].astype(np.int32),
        "size": hd.hh_size[order].astype(np.int16),
        "family_type": pa.array(fam[order].tolist(), type=pa.string()),
        "family_group": pa.array(grp[order].tolist(), type=pa.string()),
        "head_sex": hd.m_sex[head_of[order]].astype(np.int8),
        "head_age": hd.m_age[head_of[order]].astype(np.int16),
        "tenure": pa.array(WA.words(tenure[order], _TENURE_WORDS).tolist(), type=pa.string()),
        "building_type": pa.array(WA.words(btype[order], _BUILDING_WORDS).tolist(), type=pa.string()),
    }
    str_cols = {name: WA.words(attrs[name], vocab) for name, vocab in WA.VOCAB.items()}
    p_cols = {
        "person_id": np.arange(m.size, dtype=np.int32),
        "household_id": hh_id_of_member.astype(np.int32),
        "member_no": hd.m_no[m].astype(np.int8),
        "relation": rel_words,
        "sex": hd.m_sex[m].astype(np.int8),
        "age": hd.m_age[m].astype(np.int16),
        "marital": marital_words[np.where(hd.m_marital[m] >= 0, hd.m_marital[m], len(T.MARITAL))],
        "is_foreign": foreign[m],
        "nationality_group": np.full(m.size, "", dtype=object),
        "persona_kind": persons["persona_kind"],
        "role": persons["role"],
        "kind": attrs["w16_kind"].astype(np.int8),
        "chome_key": final_key[hd.m_hh[m]],
        "home_building": home_b[hd.m_hh[m]].astype(np.int32),
        "home_cell": home_c[hd.m_hh[m]].astype(np.int32),
        **str_cols,
        "industry_key": attrs["industry_key"],
        "employment_status": attrs["employment_status"],
        "duty_role": attrs["duty_role"],
        "synthetic": np.zeros(m.size, dtype=bool),
    }
    p_out = {k: (pa.array(v.tolist(), type=pa.string()) if isinstance(v, np.ndarray) and v.dtype == object else v)
             for k, v in p_cols.items()}

    # ---- 計器
    group = persons["chome"] * 2 + persons["sex"]
    adult = persons["age"] >= 15
    emp = attrs["labour_status"] == 0
    a16 = T.age_class(persons["age"], T.AGE16_EDGES)
    sim_age = np.zeros((C_, 32))
    np.add.at(sim_age, (persons["chome"], a16 * 2 + persons["sex"]), 1.0)
    mar_ok = persons["marital"] >= 0
    sim_mar = np.zeros((C_, 6))
    np.add.at(sim_mar, (persons["chome"][mar_ok], T.MARITAL3_OF4[persons["marital"][mar_ok]] * 2
                        + persons["sex"][mar_ok]), 1.0)
    sim_size = np.zeros((C_, 7))
    np.add.at(sim_size, (hd.hh_chome[nonin], hd.hh_size[nonin] - 1), 1.0)
    g_idx = np.array([T.GROUPS.index(T.GROUP_OF_TYPE[t]) for t in T.FAMILY_TYPES])
    sim_grp = np.zeros((C_, 6))
    np.add.at(sim_grp, (hd.hh_chome[nonin], g_idx[hd.hh_type[nonin]]), 1.0)

    def cat(codes: np.ndarray, K: int, mask: np.ndarray) -> np.ndarray:
        s = np.zeros((C_, K))
        ok = mask & (codes >= 0)
        np.add.at(s, (hd.hh_chome[ok], codes[ok]), 1.0)
        return s

    sh = {
        "labour_status": (attrs["labour_status"], adult, tables.chome_labour),
        "emp_status": (np.array([0, 0, 0, 0, 1, 1, 2, 1, -1])[np.where(attrs["emp_status"] >= 0,
                                                                       attrs["emp_status"], 8)], emp,
                       tables.chome_status),
        "industry_major": (attrs["industry_major"], emp, tables.chome_industry),
        "occupation_major": (attrs["occupation_major"], emp, tables.chome_occupation),
        "workplace_kind": (attrs["workplace_kind"], emp, tables.chome_workplace),
        "school_kind": (attrs["school_kind"], np.ones(m.size, dtype=bool), tables.chome_school),
        "school_place": (attrs["school_place"], np.isin(attrs["school_kind"], [2, 3, 4, 5]) & adult,
                         tables.chome_school_place),
        "residence_period": (attrs["residence_period"], np.ones(m.size, dtype=bool), tables.chome_residence),
    }
    fit_in = {
        "t03_age16_sex": (sim_age, tg.age16_sex.reshape(C_, -1)),
        "t04_marital3_sex": (sim_mar, tg.marital3_sex.reshape(C_, -1)),
        "t05_2_household_size": (sim_size, tg.hh_size),
        "t06_1_family_group": (sim_grp, tg.hh_group),
        "t07_1_tenure": (cat(tenure, len(_TENURE_WORDS), nonin), tg.tenure),
        "t08_1_building_type": (cat(btype, len(_BUILDING_WORDS), nonin), tg.building),
    }
    for name, (codes, elig, share) in sh.items():
        fit_in[f"attr_{name}"] = WC.share_target(codes, group, elig, share)
    fits = WC.table_fit(fit_in)
    f_chome = np.bincount(persons["chome"][foreign[m]], minlength=C_).astype(np.float64)
    attr_cols = ("sex", "age", "marital", "relation", "chome_key", "labour_status", "emp_status",
                 "industry_major", "occupation_major", "workplace_kind", "school_kind", "residence_period")
    checks = {
        "schema": "w21.checks/1",
        "note": "段 8 の先取り・合否は付けない。構築に使った表との食い違いは点検だけで検証の証拠にしない",
        "distribution": fits,
        "foreign_by_chome": {"abs_error_sum": round(float(np.abs(f_chome - tg.foreign).sum()), 3),
                             "sim_total": int(f_chome.sum()), "target_total": round(float(tg.foreign.sum()), 3)},
        "anneal": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in ainfo.items()},
        "overlap": WC.overlap({k: p_cols[k] for k in ("workplace_kind", "emp_status", "industry_major")}),
        "uniqueness": WC.uniqueness(p_cols, attr_cols),
        "family": WC.family(p_cols),
        "unknown_allocated": {**{k: round(float((v[tg.stage_idx] * tg.coverage).sum()), 3)
                                 for k, v in ct.unknown.items()},
                              **{k: round(v, 3) for k, v in unk_attr.items()}},
        "blanks": WC.blanks(p_cols, ("marital", "labour_status", "emp_status", "employment_status",
                                     "industry_major", "industry_key", "occupation_major", "workplace_kind",
                                     "school_kind", "school_place", "residence_period", "nationality_group",
                                     "duty_role")),
        "placement": place_stats,
        "draw_fallbacks": hd.fallbacks,
        "commuters_w16": _commuter_check(guard, world, tables, seed),
        "students_in": _student_in_check(tables, seed),
        "w16_employment_of_residents": _dist(A.call("w16_employment", {"employment_status": attrs["employment_status"]},
                                                    tables, A.AttrKey(seed, "w21.attr.w16_employment", counters))),
    }

    # ---- 段 1 枠
    e11 = S.read_derived(guard, "c20_e11")
    workers_in_ward = float(e11.get("0_総数", "00_総数")[e11.item("0_総数")])
    frame = WF.build_frame(int(m.size), workers_in_ward, ward.pop_total, version=STAGE_VERSION)

    # ---- 書く
    outputs = [
        C.write_json(out, OUTPUTS[0], frame, rows=len(frame["rows"])),
        C.write_parquet(out, OUTPUTS[1], hh_cols),
        C.write_parquet(out, OUTPUTS[2], p_out),
        C.write_json(out, OUTPUTS[3], checks),
    ]
    build_hash = C.sha256_bytes("".join(o["sha256"] for o in outputs).encode("utf-8"))
    params = {
        "seed": seed, "anneal": {"enabled": anneal.enabled, "n_iter": anneal.n_iter, "t0": anneal.t0,
                                 "t1": anneal.t1},
        "max_age": T.MAX_AGE, "coverage_step_m": W16.COVERAGE_STEP_M,
        "rng_domains": ["w21.head", "w21.spouse", "w21.other_rel", "w21.member", "w21.single", "w21.anneal",
                        "w21.tenure", "w21.building", "w21.place", "w21.foreign", "w21.attr.<関数の名>"],
        "attr_fns": A.registry_versions(stages=(3,)),  # 段 1〜3 の関数だけ(段 4〜7 の関数は w21_build_b の manifest)
    }
    opened = dict(sorted(guard.opened.items()))
    manifest = {
        "schema": "w21.manifest/1",
        "stage": STAGE, "stage_version": STAGE_VERSION,
        "population_seed": seed,
        "params": params,
        "sources": [{"sid": s.sid, "title": s.title, "stat_inf_id": s.stat_inf_id, "path": s.rel, "md5": s.md5,
                     "derived": s.derived_rel, "derived_md5": s.derived_md5, "year": s.year,
                     "r116_row": s.r116_row, "side": s.side}
                    for s in S.SOURCES if s.rel in opened or (s.derived_rel and s.derived_rel in opened)],
        "verify_side_rows": [r.row for r in S.VERIFY_SIDE],  # 〔検収 L8〕id だけ(説明文は書かない)
        "opened": opened,
        "ratios": {k: float(v) for k, v in tg.ratios.items()},
        "ipf_residual": {**{k: float(v) for k, v in tg.ipf_residual.items()},
                         "household_cells": cell_info["ipf_max_residual"]},
        "counts": {"households": int(hd.n_households), "general_households": int(nonin.sum()),
                   "institution_persons": int(inst.sum()), "persons": int(m.size),
                   "foreign_persons": int(foreign.sum()), "stage_chome": int(C_)},
        "unknown_allocated": checks["unknown_allocated"],
        "anneal": checks["anneal"],
        "outputs": outputs,
        "w21_build_hash": build_hash,
        "expedients": list(W21_EXPEDIENTS),
    }
    C.write_json(out, MANIFEST_NAME, manifest)
    res = C.StageResult(
        stage=STAGE, stage_version=STAGE_VERSION,
        input_hash=C.input_hash([guard.opened_paths[p] for p in opened]),
        param_hash=C.param_hash(params), params=params, outputs=outputs,
        catalog_classes=["住民(世帯と人・属性)", "人数の枠"],
        expedients=list(W21_EXPEDIENTS),
        notes={"w21_build_hash": build_hash, "counts": manifest["counts"], "anneal": checks["anneal"]},
    )
    res.gates = [
        C.Gate("persons", int(m.size), None),
        C.Gate("households", int(hd.n_households), None),
        C.Gate("synthetic", int(p_cols["synthetic"].sum()), 0),
        C.Gate("person_id_duplicates", checks["uniqueness"]["person_id_duplicates"], 0),
        C.Gate("heads_under_15", checks["family"]["heads_under_15"], 0),
        C.Gate("children_older_than_a_parent", checks["family"]["children_older_than_a_parent"], 0),
    ]
    C.write_header(out, res)
    return res, manifest


def _map_words(codes: np.ndarray, table: Mapping[str, str]) -> np.ndarray:
    """語の配列を表で写す(表に無い語は "")。逐次: 語の種類の数ぶん。"""
    uniq, inv = np.unique(np.asarray(codes).astype(str), return_inverse=True)
    return np.array([table.get(u, "") for u in uniq.tolist()], dtype=object)[inv]


def _commuter_check(guard: S.W21Guard, world: Path, tables: A.AttrTables, seed: int | str) -> dict[str, Any]:
    """W16 の通勤者(kind 0)に外から来る人の関数をかけた分布(数えるだけ・資産に書かない)。"""
    p = world / "w16_population.parquet"
    try:
        w16 = guard.read_parquet(p, ["kind", "age", "sex"])
    except (FileNotFoundError, OSError):
        return {"available": False}
    kind = np.asarray(w16["kind"])
    sel = kind == W16.KIND_COMMUTER
    n = int(sel.sum())
    attrs: dict[str, Any] = {
        "kind": np.full(n, "commuter", dtype=object), "sex": np.asarray(w16["sex"])[sel].astype(np.int64),
        "age": np.asarray(w16["age"])[sel].astype(np.int64), "marital": np.full(n, -1), "chome": np.full(n, -1),
        "emp_status": np.full(n, -1),  # 外から来る人は産業を先に引き、地位は産業から(関数の中で)
    }
    cnt = np.stack([np.arange(n), np.zeros(n, dtype=np.int64), np.zeros(n, dtype=np.int64)], axis=1)
    for name in ("labour_status", "industry_major", "emp_status", "industry_key", "occupation_major",
                 "employment_status"):  # 逐次: 関数の数ぶん
        attrs[name] = A.call(name, attrs, tables, A.AttrKey(seed, f"w21.commuter.{name}", cnt))

    def dist(v: np.ndarray) -> dict[str, int]:
        u, c = np.unique(np.asarray(v).astype(str), return_counts=True)
        return {str(a): int(b) for a, b in zip(u, c)}

    return {
        "available": True, "n": n,
        "industry_key": dist(attrs["industry_key"]),
        "employment_status": dist(attrs["employment_status"]),
        "occupation_major": dist(WA.words(attrs["occupation_major"], A.OCCUPATION_MAJORS)),
        "note": "W16 の通勤者(複製を含む)の年齢と男女に従業地の表の関数をかけた分布。資産には書かない(段 7 で外の人を作るときに使う)",
    }


def _dist(v: np.ndarray) -> dict[str, int]:
    u, c = np.unique(np.asarray(v).astype(str), return_counts=True)
    return {str(a): int(b) for a, b in zip(u, c)}


#: 外から来る通学者の点検で引く人数(分布を見るだけ・資産に書かない)。
STUDENT_IN_CHECK_N: Final[int] = 10_000


def _student_in_check(tables: A.AttrTables, seed: int | str) -> dict[str, Any]:
    """外から来る通学者の関数(男女・年齢・在学の種類)を ``STUDENT_IN_CHECK_N`` 人に引いた分布(数えるだけ)。"""
    n = STUDENT_IN_CHECK_N
    attrs: dict[str, Any] = {"kind": np.full(n, A.STUDENT_IN_KIND, dtype=object), "chome": np.full(n, -1)}
    cnt = np.stack([np.arange(n), np.zeros(n, dtype=np.int64), np.zeros(n, dtype=np.int64)], axis=1)
    key = A.AttrKey(seed, "w21.student_in", cnt)
    attrs["sex"] = A.call("student_in_sex", attrs, tables, key)
    attrs["age"] = A.call("student_in_age", attrs, tables, key)
    attrs["school_kind"] = A.call("school_kind", attrs, tables, A.AttrKey(seed, "w21.student_in.school", cnt))
    a16 = T.age_class(attrs["age"], T.AGE16_EDGES)
    return {
        "n": n, "table_total": round(float(tables.student_in.sum()), 1),
        "male_share": round(float((attrs["sex"] == 0).mean()), 4),
        "age16": np.bincount(a16, minlength=16).astype(int).tolist(),
        "school_kind": _dist(WA.words(attrs["school_kind"], A.SCHOOL)),
        "blank_note": "外から来る通学者の通学地・居住期間・仕事は空欄(表が無い)",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.pop.w21_build")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--world", type=Path, default=None, help="読む世界資産(既定 <data>/world/v2・読むだけ)")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--w21-anneal", choices=("on", "off"), default="on")
    ap.add_argument("--anneal-iter", type=int, default=H.AnnealParams().n_iter)
    a = ap.parse_args(argv)
    params = H.AnnealParams(enabled=a.w21_anneal == "on", n_iter=a.anneal_iter)
    try:
        check_out(a.data.resolve(), a.out.resolve(), (a.world or a.data / "world" / "v2").resolve())
    except ProtectedOutputError as e:
        print(f"[W21] 止めた(何も書いていない): {e}", file=sys.stderr)
        return 2
    res, man = build(a.data.resolve(), a.out.resolve(), world=a.world.resolve() if a.world else None, seed=a.seed,
                     anneal=params)
    print(f"[W21] persons={man['counts']['persons']} households={man['counts']['households']} "
          f"anneal {man['anneal']['error_before']}→{man['anneal']['error_after']} "
          f"w21_build_hash={man['w21_build_hash']}")
    return 0 if res.all_passed else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
