"""W16 母集団合成(§1 W16・D-W16・決定台帳「母集団合成」7 段のうち ①〜⑥)。

7 段(⑦ スケジュール生成は **W17**=本段の範囲外)
  ① 在庫棚卸し     : v1 プール 100 万体の層別件数を ``meta.json`` と照合。
  ② 目標体数       : 公的値(国勢調査 2020 小地域・経済センサス 2021 町丁目別・PT 2018)から
                      **舞台(W2 セルの覆う範囲)** のコホート体数を積み上げる。
  ③ 層化抽出+追加生成: 層 L1-L5 から抽出し、不足層(住民・通勤・乗務・指令)は素材を種に生成。
  ④ 年齢×性別 raking: IPF。住民=国勢調査の **16 階級×性別の結合表**・従業者=経済センサス
                      (**KDDI 由来は一切使わない**)。
  ⑤ 方面 OD        : ``residence_line`` の一様事前を捨て、W12 の生成用重み(方面×目的)で引く。
  ⑥ セル割当       : 自宅=町丁目人口を**建物床面積按分**(D-W16)/勤務=組織(org)単位/
                      学校=学校 POI。

出力
- ``w16_population.parquet``  体の SoA(カタログ #13 住民・通勤者・来街者・従業者)
- ``w16_households.parquet``  世帯(カタログ #14)
- ``w16_duty_roster.parquet`` 職務者名簿(カタログ #15 乗務員・指令・公共サービス要員)
- ``w16_chome.parquet``       町丁目 80 行(人口・世帯・被覆率・割当結果)
- ``w16_gates.json``          全ゲートの実測値と合否
- ``w16_cohorts.json``        層別体数・目標値・出所(1 行 1 出典)

ゲート(決定台帳の合否ライン)
  SRMSE 性別 <0.01(住民・従業者)/ SRMSE 年齢 <0.13(住民)/ SRMSE 年齢×性別 結合 <0.13
  (閾値は年齢からの流用=expedient)/ 方面 JSD <0.01 /
  空セル 0%(=住居床面積>0 のセルに住民 0 が無い)。加えて構築側の機械検査
  (町丁目 80 件の JINKO 一致・組織の座席が過不足なく埋まる・体数の突き合わせ)。

**holdout 非接触**: 本段は国勢調査・経済センサス・大都市圏 PT・W2/W4/W6/W12 の出力だけを読む。
封印層のファイルは開かない(W19 の静的検査が本ファイルにも掛かる)。

逐次ループ宣言(P4)
- ``run``: 町丁目数(80)・年齢階級×性別セル(32)・コホート数(9)・産業キー数(15)ぶんのループ。
  **体数に比例するループは無い**(すべて NumPy のベクトル演算)。
- ``build.pop.shapefile`` / ``build.pop.pool`` の逐次ループはそれぞれの docstring で宣言。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np
import pyarrow as pa

from shibuya.core.rng import stream

from ..geo import common as C
from . import fitting as F
from . import pool as P
from . import shapefile as SH

STAGE = "W16"
STAGE_VERSION = "1.0.0"

# --------------------------------------------------------------------------- 入力
#: 本段の外部入力(W19 のデータ資産表に載る)。W2/W4/W6/W11/W12 の出力は段階間の受け渡し。
INPUT_FILES: Final[tuple[tuple[str, ...], ...]] = (
    ("realworld", "estat", "r2ka13113", "r2ka13113.shp"),
    ("realworld", "estat", "r2ka13113", "r2ka13113.dbf"),
    ("realworld", "estat", "国勢調査2020_小地域_男女別人口総数世帯総数_東京都_渋谷区抽出.json"),
    # 2026-09-09 差し替え: 旧「…渋谷区抽出.json」は cat01 が 0-4〜65-69 の 14 階級で切れて
    # いた(抽出側の欠落)。全 60 分類(総数16+男16+女16+区分12)を再取得したこちらを使う。
    # 旧ファイルはディスクに残す(取得記録・ライセンス台帳の行はそのまま)が入力にはしない。
    (
        "realworld", "estat",
        "国勢調査2020_小地域_年齢5歳階級男女別人口_東京都_渋谷区_全階級.json",
    ),
    ("realworld", "estat", "国勢調査2020_昼間人口夜間人口_渋谷区.json"),
    ("realworld", "census_r3", "station_area_industry.json"),
    ("persona_pool_v2", "meta.json"),
)
#: PT(第6回東京都市圏パーソントリップ・2018)の渋谷コアゾーン集計。data 根の外(W12 と同じ)。
PT_CORE: Final[tuple[str, ...]] = ("..", "docs", "bench", "pt_shibuya", "pt6_summary_core0241.json")
#: ペルソナプール根(data 根からの相対)。
POOL_DIR: Final[tuple[str, ...]] = ("persona_pool_v2",)

# --------------------------------------------------------------------------- 定数
#: 母集団合成の親シード(``core.rng`` の master_seed・param_hash に載る)。
MASTER_SEED: Final[int] = 20260909

#: 年齢階級の下端(国勢調査 5 歳階級 0-4 … 70-74 と「75 歳以上」= **16 階級**)。
AGE_EDGES: Final[np.ndarray] = np.array(
    [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75], dtype=np.int64
)
#: 国勢調査 小地域(年齢5歳階級)の cat01: 総数 0-4 … 70-74(0020-0160)+ 75 歳以上(0200)。
CENSUS_AGE_CATS: Final[tuple[str, ...]] = tuple(
    [f"{20 + 10 * i:04d}" for i in range(15)] + ["0200"]
)
#: 同・**男**の 16 階級(0220-0360 + 0400)。
CENSUS_AGE_CATS_MALE: Final[tuple[str, ...]] = tuple(
    [f"{220 + 10 * i:04d}" for i in range(15)] + ["0400"]
)
#: 同・**女**の 16 階級(0420-0560 + 0600)。
CENSUS_AGE_CATS_FEMALE: Final[tuple[str, ...]] = tuple(
    [f"{420 + 10 * i:04d}" for i in range(15)] + ["0600"]
)
#: 同・総数(年齢「不詳」含む)。総数 − Σ階級 = **年齢不詳**(2020 年調査は 25,380 人/区)。
CENSUS_AGE_TOTAL_CAT: Final[str] = "0010"
#: 同・男/女の総数(年齢不詳を含む)。不詳の男女内訳を測るためだけに読む。
CENSUS_AGE_SEX_TOTAL_CATS: Final[tuple[str, str]] = ("0210", "0410")
#: 男女別人口総数世帯総数の cat01(人口総数・男・女・世帯総数)。
CENSUS_SEX_CATS: Final[dict[str, str]] = {
    "total": "0010",
    "male": "0020",
    "female": "0030",
    "households": "0040",
}
#: 渋谷区の area コード。
WARD_AREA: Final[str] = "13113"

#: 住居系の建物 kind(W4 の ``kind`` 語彙)。**居住床**の判定に使う(expedient)。
RESIDENTIAL_KINDS: Final[tuple[str, ...]] = ("house?", "house", "residential", "generic")
#: 町丁目の被覆率を測る標本格子の刻み[m](expedient)。
COVERAGE_STEP_M: Final[float] = 10.0
#: OSM ``levels`` が無い建物の既定階数(W4 が既に埋めているので保険)。
DEFAULT_LEVELS: Final[int] = 2

#: 指令(運行指令所・警備指令)の体数。**公的値が無い=expedient**。
#: 内訳の建て = 鉄道事業者 4(JR東・東急・京王・メトロ)× 指令席 3 × 交代 2 = 24。
#: 感度試験は 1/3 倍・3 倍(答申 E-6)。
DISPATCHER_COUNT: Final[int] = 24
#: 鉄道の乗務・駅務(勤務セル=駅の格子セル。他の職務は街を巡回するので勤務セル −1)。
RAIL_CREW_ROLES: Final[tuple[str, ...]] = ("駅員", "電車運転士", "車掌")

#: 個体種別コード(``agents.state.AgentKind`` と**同じ値**・build は agents を import しない)。
KIND_COMMUTER: Final[int] = 0
KIND_VISITOR: Final[int] = 1
KIND_WORKER: Final[int] = 2
KIND_RESIDENT: Final[int] = 3
KIND_DISPATCHER: Final[int] = 4
KIND_STUDENT: Final[int] = 5
KIND_REGULAR_VISITOR: Final[int] = 6
KIND_FOREIGN_VISITOR: Final[int] = 7
KIND_CREW: Final[int] = 8
KIND_NAMES: Final[tuple[str, ...]] = (
    "通勤者", "来街者", "従業者", "居住者", "指令",
    "通学者", "定期来街者", "訪日来街者", "乗務員",
)

#: 目的コード(W17 の T0 生成入力・PT の目的種類と対応)。
PURPOSE_NAMES: Final[tuple[str, ...]] = ("勤務", "通学", "業務", "私事", "居住", "職務")
PUR_WORK, PUR_SCHOOL, PUR_BUSINESS, PUR_PRIVATE, PUR_HOME, PUR_DUTY = range(6)
#: 目的 → W12 生成用重みの PT 目的(方面の引き先)。
PURPOSE_TO_PT: Final[dict[int, str]] = {
    PUR_WORK: "自宅－勤務",
    PUR_SCHOOL: "自宅－通学",
    PUR_BUSINESS: "自宅－業務",
    PUR_PRIVATE: "自宅－私事",
    PUR_DUTY: "自宅－勤務",
}

#: 常住地による人口の就業区分(国勢調査 従業地・通学地集計 cat01)。
RESIDENT_WORK_CATS: Final[tuple[tuple[str, str], ...]] = (
    ("110", "none"),      # 従業も通学もしていない
    ("120", "at_home"),   # 自宅で従業
    ("130", "in_area"),   # 自宅外の自市区町村で従業・通学
    ("140", "out_area"),  # 他市区町村で従業・通学
)
#: 就業区分を当てる年齢帯(expedient・15 歳以上 75 歳未満)。
RESIDENT_WORK_AGE_MIN: Final[int] = 15
RESIDENT_WORK_AGE_MAX: Final[int] = 75
#: 通学セルを当てる年齢帯(expedient・6 歳以上 18 歳未満の住民)。
SCHOOL_AGE_MIN: Final[int] = 6
SCHOOL_AGE_MAX: Final[int] = 18
#: v1 プールの来街目的のうち「業務」に当たる語(``visit_purpose`` の実値)。
POOL_BUSINESS_PURPOSE: Final[str] = "ビジネス来訪"
#: 学校とみなす POI のカテゴリ。
SCHOOL_POI_CATS: Final[tuple[str, ...]] = ("school", "education")

#: 方面 JSD をゲートに掛けるコホートの最小体数(これ未満は標本誤差が支配=報告のみ)。
DIRECTION_GATE_MIN_N: Final[int] = 1_000

#: 合否ライン(決定台帳「母集団合成」)。
GATE_SRMSE_SEX: Final[float] = 0.01
GATE_SRMSE_AGE: Final[float] = 0.13
GATE_JSD_DIRECTION: Final[float] = 0.01


# --------------------------------------------------------------------------- 小道具
def _estat_values(doc: dict[str, Any]) -> dict[tuple[str, str], int]:
    """e-Stat API の ``values`` → ``(cat01, area) → 値``。"""
    out: dict[tuple[str, str], int] = {}
    for row in doc["values"]:
        try:
            out[(row["@cat01"], row["@area"])] = int(row["$"])
        except (KeyError, ValueError):
            continue
    return out


def _stats_data_values(doc: dict[str, Any]) -> dict[str, int]:
    """GET_STATS_DATA 形式 → ``cat01 → 値``(area が 1 つの表専用)。"""
    data = doc["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
    out: dict[str, int] = {}
    for row in data:
        try:
            out[str(row["@cat01"])] = int(row["$"])
        except (KeyError, ValueError):
            continue
    return out


def _age_bin(age: np.ndarray) -> np.ndarray:
    """年齢 → ``AGE_EDGES`` の階級番号(75 以上は最終階級)。"""
    return np.searchsorted(AGE_EDGES[1:], np.asarray(age), side="right").astype(np.int64)


def _perm(n: int, domain: str, *counters: int) -> np.ndarray:
    """Philox ストリームからの決定論的な置換(``core.rng`` 以外の乱数を使わない)。"""
    if n <= 0:
        return np.zeros(0, dtype=np.int64)
    return stream(MASTER_SEED, domain, *counters).permutation(n)


def _multinomial_assign(n: int, probs: np.ndarray, domain: str, *counters: int) -> np.ndarray:
    """``n`` 件をカテゴリ確率 ``probs`` で引く(戻り値=カテゴリ番号の配列)。"""
    if n <= 0:
        return np.zeros(0, dtype=np.int64)
    p = np.asarray(probs, dtype=np.float64)
    p = p / p.sum()
    u = stream(MASTER_SEED, domain, *counters).random(n)
    return np.searchsorted(np.cumsum(p), u, side="right").clip(0, p.size - 1)


def _deal(counts: np.ndarray, members: np.ndarray) -> list[np.ndarray]:
    """``members`` を ``counts`` の順に切り分ける(合計は一致していること)。"""
    edges = np.concatenate([[0], np.cumsum(np.asarray(counts, dtype=np.int64))])
    return [members[edges[i] : edges[i + 1]] for i in range(len(counts))]


@dataclass
class _Cohort:
    """1 コホートの合成結果(列は最後に連結する)。"""

    name: str
    kind: int
    purpose: int
    idx: np.ndarray  # プール内の行番号(-1 = 素材なしの新規生成)
    layer: int  # 1..5(0 = 素材なし)
    age: np.ndarray
    sex: np.ndarray
    synthetic: np.ndarray
    is_foreign: np.ndarray
    #: 体ごとに種別が割れるコホート(来街/訪日)だけ使う。None なら ``kind`` 一律。
    kind_vec: np.ndarray | None = None

    def kinds(self) -> np.ndarray:
        if self.kind_vec is not None:
            return np.asarray(self.kind_vec, dtype=np.int64)
        return np.full(self.n, self.kind, dtype=np.int64)

    @property
    def n(self) -> int:
        return int(self.age.size)


# --------------------------------------------------------------------------- 本体
def run(ctx: C.Ctx) -> C.StageResult:  # noqa: C901 (段階=1 本の手順書)
    out = ctx.out
    params: dict[str, Any] = {
        "master_seed": MASTER_SEED,
        "age_edges": AGE_EDGES.tolist(),
        # 住民の raking は 16 階級 × 性別の**結合表**(男女別の値が取れるので周辺ではない)。
        # 年齢不詳(総数 − Σ階級)は階級を作らず、**既知階級の比率で按分**する
        #(= 結合表を n へ正規化することと同値)。
        "age_sex_raking": "joint_16x2",
        "age_unknown_policy": "prorate_over_known_classes",
        "coverage_step_m": COVERAGE_STEP_M,
        "residential_kinds": list(RESIDENTIAL_KINDS),
        "dispatcher_count": DISPATCHER_COUNT,
        "resident_work_age": [RESIDENT_WORK_AGE_MIN, RESIDENT_WORK_AGE_MAX],
        "school_age": [SCHOOL_AGE_MIN, SCHOOL_AGE_MAX],
        "school_poi_cats": list(SCHOOL_POI_CATS),
        "direction_gate_min_n": DIRECTION_GATE_MIN_N,
        "gates": {
            "srmse_sex": GATE_SRMSE_SEX,
            "srmse_age": GATE_SRMSE_AGE,
            "jsd_direction": GATE_JSD_DIRECTION,
        },
        "spatial_support": "W2 の GL セル(453)が覆う範囲。区全域ではない",
    }

    # ---- 入力 -------------------------------------------------------------
    shp = ctx.path(*INPUT_FILES[0])
    dbf = ctx.path(*INPUT_FILES[1])
    sex_json = ctx.path(*INPUT_FILES[2])
    age_json = ctx.path(*INPUT_FILES[3])
    dn_json = ctx.path(*INPUT_FILES[4])
    industry_json = ctx.path(*INPUT_FILES[5])
    pool_meta = ctx.path(*INPUT_FILES[6])
    pt_path = ctx.data.joinpath(*PT_CORE).resolve()
    for p in (shp, dbf, sex_json, age_json, dn_json, industry_json, pool_meta, pt_path):
        if not p.exists():
            raise FileNotFoundError(f"W16 の入力が無い: {p}")

    cells_p = out / "w2_cells.parquet"
    bld_p = out / "w4_buildings.parquet"
    org_p = out / "w6_org.parquet"
    poi_p = out / "w6_poi.parquet"
    exits_p = out / "w11_station_exits.parquet"
    nodes_p = out / "w12_external_nodes.parquet"
    weights_p = out / "w12_generation_weights.parquet"
    for p in (cells_p, bld_p, org_p, poi_p, exits_p, nodes_p, weights_p):
        if not p.exists():
            raise FileNotFoundError(f"W16 は先行段階の出力を必要とする: {p}")

    cells = C.read_parquet_columns(cells_p, ["place_id", "ix", "iy", "band"])
    place_to_cell = {pid: i for i, pid in enumerate(cells["place_id"])}
    n_cells = len(cells["place_id"])

    bld = C.read_parquet_columns(
        bld_p, ["building_id", "kind", "levels", "area_m2", "centroid_x", "centroid_y"]
    )
    bx = np.asarray(bld["centroid_x"], dtype=np.float64)
    by = np.asarray(bld["centroid_y"], dtype=np.float64)
    b_area = np.asarray(bld["area_m2"], dtype=np.float64)
    b_levels = np.maximum(np.asarray(bld["levels"], dtype=np.int64), DEFAULT_LEVELS)
    b_res = np.isin(np.asarray(bld["kind"], dtype=object), np.asarray(RESIDENTIAL_KINDS))
    n_bld = bx.size
    # 建物 → セル(格子 GL・W2 に無い格子は −1)
    b_ix = np.floor(bx / C.CELL_M).astype(np.int64)
    b_iy = np.floor(by / C.CELL_M).astype(np.int64)
    b_cell = np.array(
        [place_to_cell.get(C.place_id(int(i), int(j), "GL"), -1) for i, j in zip(b_ix, b_iy)],
        dtype=np.int64,
    )

    org = C.read_parquet_columns(org_p, ["org_id", "employees", "industry_key", "place_id"])
    o_emp = np.asarray(org["employees"], dtype=np.int64)
    o_cell = np.array([place_to_cell.get(p, -1) for p in org["place_id"]], dtype=np.int64)
    o_ind = list(org["industry_key"])
    n_work_seats = int(o_emp.sum())

    poi = C.read_parquet_columns(poi_p, ["poi_id", "cat", "place_id"])
    school_cells = np.array(
        [
            place_to_cell.get(p, -1)
            for cat, p in zip(poi["cat"], poi["place_id"])
            if cat in SCHOOL_POI_CATS
        ],
        dtype=np.int64,
    )
    school_cells = school_cells[school_cells >= 0]

    exits = C.read_parquet_columns(exits_p, ["station_title", "own_grid_place_id"])
    dispatch_cell = _modal_cell(exits, place_to_cell)

    ext = C.read_parquet_columns(nodes_p, ["node_id", "kind", "direction_label"])
    node_ids = list(ext["node_id"])
    node_index = {nid: i for i, nid in enumerate(node_ids)}
    gw = C.read_parquet_columns(weights_p, ["node_id", "purpose", "weight"])
    direction_probs = _direction_probs(gw, node_index, len(node_ids))

    # ---- ① 在庫棚卸し ------------------------------------------------------
    pool = P.read_pool(ctx.path(*POOL_DIR))
    inventory_ok = pool.inventory_matches_meta()

    # ---- 町丁目(境界+人口+世帯)------------------------------------------
    polys_ll = SH.read_shp(shp)
    chome = SH.read_dbf(dbf)
    if len(polys_ll) != len(chome):
        raise ValueError(".shp と .dbf の件数が違う")
    polys = [
        p.transformed(
            lambda lon, lat: (
                (lon - C.ORIGIN_LATLON[1]) * C.M_PER_DEG_LON,
                (lat - C.ORIGIN_LATLON[0]) * C.M_PER_DEG_LAT,
            )
        )
        for p in polys_ll
    ]
    keys = [str(r["KEY_CODE"]) for r in chome]
    jinko = np.array([int(r["JINKO"] or 0) for r in chome], dtype=np.int64)
    setai = np.array([int(r["SETAI"] or 0) for r in chome], dtype=np.int64)
    dbf_area = np.array([float(r["AREA"] or 0.0) for r in chome], dtype=np.float64)

    sex_doc = C.load_json(sex_json)
    age_doc = C.load_json(age_json)
    sex_vals = _estat_values(sex_doc)
    age_vals = _estat_values(age_doc)
    estat_pop = np.array(
        [sex_vals.get((CENSUS_SEX_CATS["total"], k), -1) for k in keys], dtype=np.int64
    )
    # 年齢表(全階級・09-09 再取得)の町丁目総数も同じ値であることを**同じゲートで**要求する
    #(入力を差し替えたので、80 町丁目の突合は新旧どちらの表に対しても成り立たせる)。
    estat_age_pop = np.array(
        [age_vals.get((CENSUS_AGE_TOTAL_CAT, k), -1) for k in keys], dtype=np.int64
    )
    jinko_match = int(((estat_pop == jinko) & (estat_age_pop == jinko)).sum())
    chome_male = np.array(
        [sex_vals.get((CENSUS_SEX_CATS["male"], k), 0) for k in keys], dtype=np.int64
    )
    chome_female = np.array(
        [sex_vals.get((CENSUS_SEX_CATS["female"], k), 0) for k in keys], dtype=np.int64
    )

    # 被覆率(町丁目 × 世界セル)= 10m 標本格子(乱数なし)
    coverage, raster_area, cover_cells = _chome_coverage(polys, place_to_cell, COVERAGE_STEP_M)
    area_rel_err = float(
        abs(raster_area.sum() - dbf_area.sum()) / max(dbf_area.sum(), 1.0)
    )

    # 建物 → 町丁目
    b_chome = SH.assign_points_to_polygons(bx, by, polys)

    # ---- ② 目標体数 -------------------------------------------------------
    n_res_target = int(round(float((jinko * coverage).sum())))
    n_hh_target = int(round(float((setai * coverage).sum())))
    pt = C.load_json(pt_path)
    pt_arr = pt["arrive_purpose_x_mode"]
    pt_work = float(pt_arr["自宅－勤務"]["計"])
    ratio_school = float(pt_arr["自宅－通学"]["計"]) / pt_work
    ratio_business = float(pt_arr["自宅－業務"]["計"]) / pt_work
    ratio_private = float(pt_arr["自宅－私事"]["計"]) / pt_work
    n_student_target = int(round(n_work_seats * ratio_school))
    n_business_target = int(round(n_work_seats * ratio_business))
    n_private_target = int(round(n_work_seats * ratio_private))

    dn = _stats_data_values(C.load_json(dn_json))
    ward_night = dn.get("100", 0)
    ward_day = dn.get("180", 0)
    ward_inflow = dn.get("230", 0)
    work_cat = np.array([float(dn.get(code, 0)) for code, _ in RESIDENT_WORK_CATS])
    work_cat_share = work_cat / work_cat.sum()

    ind = C.load_json(industry_json)
    ind_sex = _industry_sex_targets(ind)
    worker_female_share = _overall_female_share(ind_sex)

    # ---- ④ 年齢×性別 raking の目標 --------------------------------------
    # 16 階級 × 性別の**結合表**(区・国勢調査2020)。周辺ではなく結合を種にする。
    ward_age_sex = np.array(
        [
            [
                age_vals.get((cm, WARD_AREA), 0),
                age_vals.get((cf, WARD_AREA), 0),
            ]
            for cm, cf in zip(CENSUS_AGE_CATS_MALE, CENSUS_AGE_CATS_FEMALE)
        ],
        dtype=np.float64,
    )
    ward_age_counts = np.array(
        [age_vals.get((c, WARD_AREA), 0) for c in CENSUS_AGE_CATS], dtype=np.float64
    )
    if not np.array_equal(ward_age_counts, ward_age_sex.sum(axis=1)):
        raise ValueError("年齢表の 総数 と 男+女 が階級ごとに一致しない(入力の版違い)")
    ward_age_total = float(age_vals.get((CENSUS_AGE_TOTAL_CAT, WARD_AREA), 0))
    #: 年齢不詳(総数 − Σ階級)。**階級を作らず既知階級の比率で配る**(= 正規化と同値)。
    ward_age_unknown = ward_age_total - float(ward_age_counts.sum())
    ward_age_unknown_by_sex = [
        float(age_vals.get((CENSUS_AGE_SEX_TOTAL_CATS[0], WARD_AREA), 0))
        - float(ward_age_sex[:, 0].sum()),
        float(age_vals.get((CENSUS_AGE_SEX_TOTAL_CATS[1], WARD_AREA), 0))
        - float(ward_age_sex[:, 1].sum()),
    ]
    ward_male = float(sex_vals.get((CENSUS_SEX_CATS["male"], WARD_AREA), 0))
    ward_female = float(sex_vals.get((CENSUS_SEX_CATS["female"], WARD_AREA), 0))

    l1 = pool.layers["L1"]
    l2 = pool.layers["L2"]
    l3 = pool.layers["L3"]
    l4 = pool.layers["L4"]
    l5 = pool.layers["L5"]

    # 種 = 区の**結合表**そのもの(旧: プール L1 の年齢×性別表)。行の目標 = 16 階級の
    # 周辺(不詳を按分済み)、列の目標 = 男女別人口総数(不詳のない表)。年齢が不詳の
    # 25,380 人は男女比が既知層と違う(男 13,538/女 11,842)ので、性別だけは総数表へ
    # 合わせ直す = IPF が 1 段の補正として吸収する。
    res_age_target = _age_target(n_res_target, ward_age_counts)
    res_sex_target = _sex_target(n_res_target, ward_male, ward_female)
    res_table = F.ipf(ward_age_sex, res_age_target, res_sex_target)
    res_counts = _round_table(res_table.table, n_res_target)

    residents = _draw_cohort(
        "resident", KIND_RESIDENT, PUR_HOME, l1, 1, res_counts, "w16.draw.resident"
    )

    # ---- ③+⑥ 住民の町丁目・建物・セル ------------------------------------
    res_by_chome = F.largest_remainder(jinko * coverage, n_res_target)
    male_idx = np.flatnonzero(residents.sex == 0)
    female_idx = np.flatnonzero(residents.sex == 1)
    male_idx = male_idx[_perm(male_idx.size, "w16.chome.male")]
    female_idx = female_idx[_perm(female_idx.size, "w16.chome.female")]
    chome_male_share = np.divide(
        chome_male, np.maximum(chome_male + chome_female, 1), dtype=np.float64
    )
    male_by_chome = F.largest_remainder(res_by_chome * chome_male_share, male_idx.size)
    male_by_chome = np.minimum(male_by_chome, res_by_chome)
    female_by_chome = res_by_chome - male_by_chome
    if int(female_by_chome.sum()) != female_idx.size:
        female_by_chome = F.largest_remainder(
            res_by_chome * (1.0 - chome_male_share), female_idx.size
        )
        male_by_chome = res_by_chome - female_by_chome

    res_chome = np.full(residents.n, -1, dtype=np.int64)
    for c, part in enumerate(_deal(male_by_chome, male_idx)):
        res_chome[part] = c
    for c, part in enumerate(_deal(female_by_chome, female_idx)):
        res_chome[part] = c

    res_building, res_cell, home_stats = _assign_home_buildings(
        res_chome, b_chome, b_cell, b_res, b_area, b_levels, len(chome), cover_cells
    )

    # 世帯(建物内で連番に切る・chome ごとの平均世帯人員に合わせる)
    hh_id, hh_table = _build_households(res_cell, res_building, res_chome, res_by_chome, setai, coverage, keys)

    # ---- 住民の就業区分(国勢調査 従業地・通学地集計の周辺へ)----------------
    workable = (residents.age >= RESIDENT_WORK_AGE_MIN) & (residents.age < RESIDENT_WORK_AGE_MAX)
    res_work_cat = np.full(residents.n, -1, dtype=np.int64)
    w_idx = np.flatnonzero(workable)
    res_work_cat[w_idx] = _multinomial_assign(
        w_idx.size, work_cat_share, "w16.resident.workcat"
    )
    res_in_area = np.flatnonzero(res_work_cat == 2)
    res_at_home = np.flatnonzero(res_work_cat == 1)
    res_out_area = np.flatnonzero(res_work_cat == 3)
    n_res_in_area = min(int(res_in_area.size), n_work_seats)
    res_in_area = res_in_area[:n_res_in_area]

    # ---- ③ 従業者(通勤者)------------------------------------------------
    n_commuter = n_work_seats - n_res_in_area
    worker_female_total = int(round(n_work_seats * worker_female_share))
    res_worker_female = int((residents.sex[res_in_area] == 1).sum())
    commuter_female = int(np.clip(worker_female_total - res_worker_female, 0, n_commuter))
    com_sex_target = np.array(
        [float(n_commuter - commuter_female), float(commuter_female)], dtype=np.float64
    )
    worker_age_counts = ward_age_counts.copy()
    worker_age_counts[: _age_bin(np.array([RESIDENT_WORK_AGE_MIN]))[0]] = 0.0
    com_age_target = _age_target(n_commuter, worker_age_counts)
    com_table = F.ipf(l2.age_sex_table(AGE_EDGES), com_age_target, com_sex_target)
    com_counts = _round_table(com_table.table, n_commuter)
    commuters = _draw_cohort(
        "commuter", KIND_COMMUTER, PUR_WORK, l2, 2, com_counts, "w16.draw.commuter"
    )

    # ---- ③ 通学者・来街者・職務者 -----------------------------------------
    students = _draw_cohort_free(
        "student", KIND_STUDENT, PUR_SCHOOL, l3, 3, n_student_target,
        "w16.draw.student", mask=np.asarray(l3.col("subtype")) == "student",
    )
    n_regular = min(n_private_target, int((np.asarray(l3.col("subtype")) == "regular").sum()))
    regulars = _draw_cohort_free(
        "regular_visitor", KIND_REGULAR_VISITOR, PUR_PRIVATE, l3, 3, n_regular,
        "w16.draw.regular", mask=np.asarray(l3.col("subtype")) == "regular",
    )
    l4_purpose = np.asarray(l4.col("visit_purpose"))
    business = _draw_cohort_free(
        "business_visitor", KIND_VISITOR, PUR_BUSINESS, l4, 4, n_business_target,
        "w16.draw.business", mask=l4_purpose == POOL_BUSINESS_PURPOSE,
    )
    n_l4_private = max(n_private_target - n_regular, 0)
    visitors = _draw_cohort_free(
        "visitor", KIND_VISITOR, PUR_PRIVATE, l4, 4, n_l4_private,
        "w16.draw.visitor", mask=l4_purpose != POOL_BUSINESS_PURPOSE,
    )
    # 訪日(is_foreign)は来街者の中の種別へ振り替える(E-2・プールの 30% をそのまま採る)
    visitors.kind_vec = np.where(visitors.is_foreign, KIND_FOREIGN_VISITOR, KIND_VISITOR)

    duty_mask = np.asarray(l5.col("presence")) == "duty"
    crew = _draw_cohort_free(
        "crew", KIND_CREW, PUR_DUTY, l5, 5, int(duty_mask.sum()), "w16.draw.crew", mask=duty_mask
    )
    council = _draw_cohort_free(
        "council", KIND_RESIDENT, PUR_HOME, l5, 5, int((~duty_mask).sum()),
        "w16.draw.council", mask=~duty_mask,
    )
    dispatchers = _make_dispatchers(com_counts, DISPATCHER_COUNT)

    # ---- 連結して SoA を組む ----------------------------------------------
    cohorts = [
        residents, commuters, students, regulars, business, visitors, crew, council, dispatchers
    ]
    n_total = sum(c.n for c in cohorts)
    kind = np.concatenate([c.kinds() for c in cohorts]).astype(np.int8)
    purpose = np.concatenate(
        [np.full(c.n, c.purpose, dtype=np.int8) for c in cohorts]
    )
    age = np.concatenate([c.age for c in cohorts]).astype(np.uint8)
    sex = np.concatenate([c.sex for c in cohorts]).astype(np.int8)
    pool_layer = np.concatenate(
        [np.full(c.n, c.layer, dtype=np.int8) for c in cohorts]
    )
    pool_index = np.concatenate([c.idx for c in cohorts]).astype(np.int32)
    synthetic = np.concatenate([c.synthetic for c in cohorts])
    is_foreign = np.concatenate([c.is_foreign for c in cohorts])
    offsets = np.concatenate([[0], np.cumsum([c.n for c in cohorts])]).astype(np.int64)
    span = {c.name: (int(offsets[i]), int(offsets[i + 1])) for i, c in enumerate(cohorts)}

    home_cell = np.full(n_total, -1, dtype=np.int64)
    work_cell = np.full(n_total, -1, dtype=np.int64)
    school_cell = np.full(n_total, -1, dtype=np.int64)
    home_building = np.full(n_total, -1, dtype=np.int64)
    household = np.full(n_total, -1, dtype=np.int64)
    org_ref = np.full(n_total, -1, dtype=np.int64)
    industry = np.full(n_total, "", dtype=object)
    chome_key = np.full(n_total, "", dtype=object)
    direction = np.full(n_total, -1, dtype=np.int64)

    r0, r1 = span["resident"]
    home_cell[r0:r1] = res_cell
    home_building[r0:r1] = res_building
    household[r0:r1] = hh_id
    chome_key[r0:r1] = np.asarray(keys, dtype=object)[res_chome]
    kind[r0:r1] = np.where(
        np.isin(np.arange(residents.n), res_in_area), KIND_WORKER, KIND_RESIDENT
    ).astype(np.int8)
    # 自宅で従業する住民は勤務セル=自宅セル
    work_cell[r0 + res_at_home] = res_cell[res_at_home]

    # ⑥ 勤務セル: 組織の座席を過不足なく埋める(通勤者 + 在区就業の住民)
    seats_org = np.repeat(np.arange(o_emp.size, dtype=np.int64), o_emp)
    seat_industry = np.asarray(o_ind, dtype=object)[seats_org]
    worker_rows = np.concatenate([r0 + res_in_area, np.arange(*span["commuter"])])
    seat_of_worker = _assign_seats_by_industry_sex(
        seats_org, seat_industry, sex[worker_rows], ind_sex
    )
    org_ref[worker_rows] = seats_org[seat_of_worker]
    work_cell[worker_rows] = o_cell[org_ref[worker_rows]]
    industry[worker_rows] = seat_industry[seat_of_worker]

    # ⑥ 学校セル(通学者と学齢の住民・学校 POI へ一様=expedient)
    stu0, stu1 = span["student"]
    if school_cells.size:
        school_cell[stu0:stu1] = school_cells[
            _multinomial_assign(stu1 - stu0, np.ones(school_cells.size), "w16.school.student")
        ]
        pupils = r0 + np.flatnonzero(
            (residents.age >= SCHOOL_AGE_MIN) & (residents.age < SCHOOL_AGE_MAX)
        )
        school_cell[pupils] = school_cells[
            _multinomial_assign(pupils.size, np.ones(school_cells.size), "w16.school.resident")
        ]
    d0, d1 = span["dispatchers"]
    work_cell[d0:d1] = dispatch_cell
    c0, c1 = span["council"]
    home_cell[c0:c1] = res_cell[_perm(res_cell.size, "w16.council.home")[: c1 - c0]]
    crew0, crew1 = span["crew"]
    crew_roles = np.asarray(l5.col("role"), dtype=object)[crew.idx]
    rail_crew = np.isin(crew_roles, np.asarray(RAIL_CREW_ROLES, dtype=object))
    work_cell[crew0 + np.flatnonzero(rail_crew)] = dispatch_cell

    # ---- 職務の役割名(定員先取り層の判定材料・``agents.population`` が読む列)--------
    # 二層抽出の「定員先取り層」は**役割**で決まる(答申 §Q6-b「機能に必要な最小定員」)。
    # プール層 L5 には路上生活者・ティッシュ配り・配信者など、機能定員でない役割も入って
    # いるので、層ではなく役割名を publish して判定は ``agents`` 側の表に持たせる。
    duty_role = np.full(n_total, "", dtype=object)
    duty_role[crew0:crew1] = crew_roles
    duty_role[c0:c1] = np.asarray(l5.col("role"), dtype=object)[council.idx]
    duty_role[d0:d1] = "指令"
    _roles, _rc = np.unique(duty_role[duty_role != ""].astype(str), return_counts=True)
    duty_role_counts = {str(r): int(c) for r, c in sorted(zip(_roles.tolist(), _rc.tolist()))}

    # ---- ⑤ 方面 ----------------------------------------------------------
    direction_report: dict[str, Any] = {}
    for name, (a, b) in span.items():
        if name in ("resident", "council"):
            continue
        pt_purpose = PURPOSE_TO_PT[int(purpose[a])]
        probs = direction_probs[pt_purpose]
        direction[a:b] = _multinomial_assign(b - a, probs, f"w16.direction.{name}")
        direction_report[name] = _direction_stats(direction[a:b], probs, len(node_ids))
    # 域外へ通う住民は「自宅－勤務」の方面を使う(到着側の重みを流用=expedient)
    out_rows = r0 + res_out_area
    if out_rows.size:
        probs = direction_probs["自宅－勤務"]
        direction[out_rows] = _multinomial_assign(
            out_rows.size, probs, "w16.direction.resident_out"
        )
        direction_report["resident_out_area"] = _direction_stats(
            direction[out_rows], probs, len(node_ids)
        )

    # ---- ゲート ------------------------------------------------------------
    res_rows = np.arange(r0, r1)
    srmse_sex_res = F.srmse(
        np.bincount(sex[res_rows].astype(np.int64), minlength=2), [ward_male, ward_female]
    )
    sim_age = np.bincount(_age_bin(age[res_rows]), minlength=AGE_EDGES.size)
    srmse_age_res = F.srmse(sim_age, ward_age_counts)
    # 結合(16 階級 × 性別 = 32 セル)の一致。閾値は年齢の 0.13 を**流用**(結合の公的な
    # 合否ラインは答申にない=expedient・SRMSE の定義は周辺と同じ割合ベース)。
    sim_joint = np.zeros((AGE_EDGES.size, 2), dtype=np.int64)
    np.add.at(
        sim_joint,
        (_age_bin(age[res_rows]), np.clip(sex[res_rows].astype(np.int64), 0, 1)),
        1,
    )
    srmse_joint_res = F.srmse(sim_joint, ward_age_sex)
    w_sex = np.bincount(sex[worker_rows].astype(np.int64), minlength=2)
    srmse_sex_work = F.srmse(
        w_sex, [1.0 - worker_female_share, worker_female_share]
    )
    jsd_gated = [
        v["jsd"] for v in direction_report.values() if v["n"] >= DIRECTION_GATE_MIN_N
    ]
    jsd_max = max(jsd_gated) if jsd_gated else 0.0

    # 空セル 0%(決定台帳の合否ライン)の定義:
    #   「住居床面積>0 のセルに住民 0 が無い」。ただし**人口の出所がある**セルに限る
    #   ——世界の bbox は区界をまたぐので、渋谷区外(港区・新宿区側)の建物しか無いセルには
    #   当てるべき町丁目人口が存在しない。そこを「空セル」と数えると、数えているのは
    #   合成の失敗ではなく**入力データの空間支持**になる(別立てで報告する)。
    res_floor = np.where(b_res, b_area * b_levels, 0.0)
    _bc = np.clip(b_chome, 0, len(chome) - 1)
    supported = (b_chome >= 0) & (coverage[_bc] > 0) & (jinko[_bc] > 0)
    cell_floor = np.zeros(n_cells, dtype=np.float64)
    cell_floor_supported = np.zeros(n_cells, dtype=np.float64)
    ok_b = b_cell >= 0
    np.add.at(cell_floor, b_cell[ok_b], res_floor[ok_b])
    np.add.at(
        cell_floor_supported, b_cell[ok_b & supported], res_floor[ok_b & supported]
    )
    cell_pop = np.bincount(res_cell[res_cell >= 0], minlength=n_cells)
    empty_cells = int(((cell_floor_supported > 0) & (cell_pop == 0)).sum())
    n_res_cells = int((cell_floor > 0).sum())
    n_res_cells_supported = int((cell_floor_supported > 0).sum())
    cells_outside_support = int(((cell_floor > 0) & (cell_floor_supported == 0)).sum())
    residents_without_cell = int((res_cell < 0).sum())

    # ---- 出力 --------------------------------------------------------------
    inputs = [
        shp, dbf, sex_json, age_json, dn_json, industry_json, pool_meta, pt_path,
        cells_p, bld_p, org_p, poi_p, exits_p, nodes_p, weights_p,
    ]
    for name in P.LAYERS:
        inputs.extend(P.layer_files(ctx.path(*POOL_DIR), name))

    cohort_rows = _cohort_rows(
        span, cohorts, kind, n_res_target, n_work_seats, n_res_in_area, n_commuter,
        n_student_target, n_business_target, n_private_target, n_regular,
        DISPATCHER_COUNT, ward_night, ward_day, ward_inflow,
    )

    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(inputs),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=[
            "住民・通勤者・来街者・従業者",
            "世帯",
            "乗務員・指令・公共サービス要員",
        ],
        expedients=[
            "目標体数の空間支持=W2 セルが覆う範囲(区全域の公的値を町丁目被覆率で按分)",
            "町丁目被覆率=10m 標本格子でのセル被覆面積割合",
            "町丁目→セル=住居系建物の床面積(area_m2×levels)按分(D-W16)",
            "住居系 kind = house?/house/residential/generic(W4 の kind は用途の推定・generic を住居側に入れている)",
            "住民の年齢不詳(区計 25,380 人)は階級を作らず**既知階級の比率で按分**"
            "(男女で不詳率が違う=男 13,538/女 11,842 ので、性別だけは男女別人口総数へ"
            "IPF で合わせ直す)",
            "結合 SRMSE の閾値は決定台帳の年齢 0.13 を流用(結合の公的な合否ラインが無い)",
            "従業者の年齢目標=区の 15 歳以上の年齢分布(公的な従業者年齢表は未取得)",
            "来街者・通学者の年齢×性別は raking しない(較正に使える公的表が無い)",
            "通学者・業務来街・私事来街の体数=PT(2018)の目的別到着比を従業者数へ当てた値",
            "指令の体数 24(=鉄道4事業者×指令席3×交代2)・勤務セル=渋谷駅出口の最頻セル",
            "学校セルは学校 POI へ一様(定員データが無い)",
            "住民の就業区分は国勢調査の 4 区分へ多項抽選(15 歳以上 75 歳未満)",
            "域外へ通う住民の方面は到着側(自宅－勤務)の重みを流用",
            "世帯は建物内の連番切り分け(世帯構成は再現しない)",
            "空セル 0% の分母=渋谷区の町丁目(人口>0・被覆率>0)に属する建物が持つ住居床のセル"
            "(区外の建物しか無いセルは当てる人口が無いので別立てで報告)",
        ],
        notes={
            "pool_counts": pool.counts(),
            "pool_meta_counts": pool.meta_counts(),
            "chome_polygons": len(chome),
            "chome_area_relative_error": round(area_rel_err, 6),
            "chome_covered": int((coverage > 0).sum()),
            "chome_fully_covered": int((coverage >= 0.999).sum()),
            "buildings_assigned_to_chome": int((b_chome >= 0).sum()),
            "buildings_outside_ward": int((b_chome < 0).sum()),
            "buildings_without_gl_cell": int((b_cell < 0).sum()),
            "residents_by_residential_floor": home_stats["by_floor"],
            "residents_by_any_building": home_stats["by_any_building"],
            "residents_by_covered_area": home_stats["by_covered_area"],
            "empty_cell_repairs": home_stats["repairs"],
            "residential_cells": n_res_cells,
            "residential_cells_with_census_support": n_res_cells_supported,
            "residential_cells_outside_census_support": cells_outside_support,
            "residents_without_home_cell": residents_without_cell,
            "org_seats": n_work_seats,
            "school_poi_cells": int(school_cells.size),
            "ipf_iterations": {"resident": res_table.n_iter, "commuter": com_table.n_iter},
            "ipf_residual": {
                "resident": round(res_table.max_residual, 12),
                "commuter": round(com_table.max_residual, 12),
            },
            "pt_ratios_to_home_work": {
                "自宅－通学": round(ratio_school, 6),
                "自宅－業務": round(ratio_business, 6),
                "自宅－私事": round(ratio_private, 6),
            },
            "ward_anchors": {
                "夜間人口": ward_night, "昼間人口": ward_day, "流入": ward_inflow,
                "従業者(区・経済センサス2021)": 516541,
            },
            "worker_female_share_target": round(worker_female_share, 6),
            "ward_age_classes": int(AGE_EDGES.size),
            "ward_age_unknown": int(ward_age_unknown),
            "ward_age_unknown_by_sex": [int(v) for v in ward_age_unknown_by_sex],
            "ward_age_sex_joint": ward_age_sex.astype(np.int64).tolist(),
            "duty_role_counts": duty_role_counts,
            "direction": direction_report,
            "n_total": n_total,
            "population_bytes": None,
            "bytes_per_agent": None,
        },
    )

    res.outputs.append(
        C.write_parquet(
            out,
            "w16_population.parquet",
            {
                "agent_id": np.arange(n_total, dtype=np.int32),
                "kind": kind,
                "purpose": purpose,
                "age": age,
                "sex": sex,
                "home_cell": home_cell.astype(np.int32),
                "work_cell": work_cell.astype(np.int32),
                "school_cell": school_cell.astype(np.int32),
                "direction_node": direction.astype(np.int32),
                "chome_key": pa.array(chome_key.tolist(), type=pa.string()),
                "household_id": household.astype(np.int32),
                "home_building": home_building.astype(np.int32),
                "org_id": org_ref.astype(np.int32),
                "industry_key": pa.array(industry.tolist(), type=pa.string()),
                "duty_role": pa.array(duty_role.tolist(), type=pa.string()),
                "pool_layer": pool_layer,
                "pool_index": pool_index,
                "synthetic": synthetic,
                "is_foreign": is_foreign,
            },
        )
    )
    res.outputs.append(C.write_parquet(out, "w16_households.parquet", hh_table))
    res.outputs.append(
        C.write_parquet(
            out,
            "w16_duty_roster.parquet",
            _duty_roster(span, kind, age, sex, work_cell, direction, l5, crew, dispatchers),
        )
    )
    res.outputs.append(
        C.write_parquet(
            out,
            "w16_chome.parquet",
            {
                "key_code": keys,
                "s_name": [str(r["S_NAME"]) for r in chome],
                "jinko": jinko,
                "setai": setai,
                "estat_pop": estat_pop,
                "area_m2": dbf_area,
                "coverage": np.round(coverage, 6),
                "residents": res_by_chome.astype(np.int32),
                "residents_male": male_by_chome.astype(np.int32),
                "residents_female": female_by_chome.astype(np.int32),
            },
        )
    )
    gates_json = {
        "srmse_sex_resident": srmse_sex_res,
        "srmse_age_resident": srmse_age_res,
        "srmse_age_sex_joint_resident": srmse_joint_res,
        "srmse_sex_worker": srmse_sex_work,
        "jsd_direction_max": jsd_max,
        "empty_residential_cells": empty_cells,
        "residential_cells_with_census_support": n_res_cells_supported,
        "residential_cells_outside_census_support": cells_outside_support,
        "residents_without_home_cell": residents_without_cell,
        "chome_jinko_match": jinko_match,
        "pool_inventory_matches_meta": inventory_ok,
        "worker_seats_filled": int(worker_rows.size),
        "org_seats": n_work_seats,
        "n_total": n_total,
        "limits": {
            "srmse_sex": GATE_SRMSE_SEX,
            "srmse_age": GATE_SRMSE_AGE,
            "srmse_age_sex_joint": GATE_SRMSE_AGE,
            "jsd_direction": GATE_JSD_DIRECTION,
        },
    }
    pop_bytes = int(res.outputs[0]["bytes"])
    res.notes["population_bytes"] = pop_bytes
    res.notes["bytes_per_agent"] = round(pop_bytes / max(n_total, 1), 3)
    gates_json["population_bytes"] = pop_bytes
    gates_json["bytes_per_agent"] = round(pop_bytes / max(n_total, 1), 3)
    res.outputs.append(C.write_json(out, "w16_gates.json", gates_json))
    res.outputs.append(C.write_json(out, "w16_cohorts.json", cohort_rows, rows=len(cohort_rows["cohorts"])))

    res.gates = [
        C.Gate("pool_inventory_matches_meta", inventory_ok, True),
        C.Gate("chome_jinko_match", jinko_match, len(chome)),
        C.Gate("srmse_sex_resident", round(srmse_sex_res, 6), None,
               passed=srmse_sex_res < GATE_SRMSE_SEX),
        C.Gate("srmse_age_resident", round(srmse_age_res, 6), None,
               passed=srmse_age_res < GATE_SRMSE_AGE),
        C.Gate("srmse_age_sex_joint_resident", round(srmse_joint_res, 6), None,
               passed=srmse_joint_res < GATE_SRMSE_AGE),
        C.Gate("srmse_sex_worker", round(srmse_sex_work, 6), None,
               passed=srmse_sex_work < GATE_SRMSE_SEX),
        C.Gate("jsd_direction_max", round(jsd_max, 8), None, passed=jsd_max < GATE_JSD_DIRECTION),
        C.Gate("empty_residential_cells", empty_cells, 0),
        C.Gate("residents_without_home_cell", residents_without_cell, 0),
        C.Gate("worker_seats_filled", int(worker_rows.size), n_work_seats),
        C.Gate("households_cover_all_residents", int(hh_table["size"].sum()), n_res_target),
        C.Gate("n_agents", n_total, None),
        C.Gate("n_residents", int(r1 - r0), n_res_target),
    ]
    return res


# --------------------------------------------------------------------------- 補助
def _modal_cell(exits: dict[str, list], place_to_cell: dict[str, int]) -> int:
    """駅出口が最も多い格子セル(指令・乗務員の勤務地・expedient)。"""
    counts: dict[int, int] = {}
    for pid in exits["own_grid_place_id"]:
        idx = place_to_cell.get(str(pid), -1)
        if idx >= 0:
            counts[idx] = counts.get(idx, 0) + 1
    if not counts:
        return -1
    return max(sorted(counts), key=lambda k: (counts[k], -k))


def _direction_probs(
    gw: dict[str, list], node_index: dict[str, int], n_nodes: int
) -> dict[str, np.ndarray]:
    """W12 生成用重み → 目的ごとの方面(外界ノード)確率。"""
    out: dict[str, np.ndarray] = {}
    for node_id, purpose, weight in zip(gw["node_id"], gw["purpose"], gw["weight"]):
        vec = out.setdefault(str(purpose), np.zeros(n_nodes, dtype=np.float64))
        idx = node_index.get(str(node_id), -1)
        if idx >= 0:
            vec[idx] += float(weight)
    total = np.zeros(n_nodes, dtype=np.float64)
    for vec in out.values():
        total += vec
    for key, vec in list(out.items()):
        out[key] = vec / vec.sum() if vec.sum() > 0 else total / max(total.sum(), 1.0)
    if total.sum() > 0:
        out.setdefault("計", total / total.sum())
    for pt_purpose in PURPOSE_TO_PT.values():
        out.setdefault(pt_purpose, out.get("計", np.full(n_nodes, 1.0 / n_nodes)))
    return out


def _direction_stats(assigned: np.ndarray, probs: np.ndarray, n_nodes: int) -> dict[str, Any]:
    n = int(assigned.size)
    hist = np.bincount(assigned[assigned >= 0], minlength=n_nodes).astype(np.float64)
    if n == 0:
        return {"n": 0, "jsd": 0.0, "shares": [], "target": [round(float(v), 6) for v in probs]}
    return {
        "n": n,
        "jsd": float(F.jsd(hist, probs)),
        "shares": [round(float(v), 6) for v in hist / hist.sum()],
        "target": [round(float(v), 6) for v in probs],
    }


def _age_target(n: int, ward_age_counts: np.ndarray) -> np.ndarray:
    """``AGE_EDGES`` の階級ごとの目標体数(最後の階級=75 歳以上)。

    公的表の階級カウントを ``n`` へ正規化するだけ = **年齢不詳を既知階級の比率で按分**した
    ことと同値(不詳の階級は作らない)。全階級が 0 のときだけ一様に置く。
    """
    target = np.zeros(AGE_EDGES.size, dtype=np.float64)
    if n <= 0:
        return target
    counts = np.asarray(ward_age_counts, dtype=np.float64)
    if counts.size != AGE_EDGES.size:
        raise ValueError(f"階級数が AGE_EDGES({AGE_EDGES.size})と違う: {counts.size}")
    if counts.sum() > 0:
        target[:] = counts / counts.sum() * float(n)
    else:
        target[:] = float(n) / AGE_EDGES.size
    return target


def _sex_target(n: int, male: float, female: float) -> np.ndarray:
    total = male + female
    if total <= 0:
        return np.array([n / 2.0, n / 2.0])
    return np.array([n * male / total, n * female / total], dtype=np.float64)


def _round_table(table: np.ndarray, total: int) -> np.ndarray:
    """IPF の実数表 → 合計が厳密に ``total`` の整数表。"""
    flat = F.largest_remainder(table.ravel(), total)
    return flat.reshape(table.shape)


def _draw_cohort(
    name: str, kind: int, purpose: int, layer: P.PoolLayer, layer_no: int,
    counts: np.ndarray, domain: str,
) -> _Cohort:
    """(年齢階級×性別)ごとの目標件数で層から抽出する。足りないセルは**追加生成**。

    追加生成 = 同じセルの素材を種に複製(``synthetic=True``)。セルが空なら層全体から
    種を引き、年齢を階級内で・性別をセルの値で引き直す。
    """
    bins = _age_bin(layer.age)
    n = int(counts.sum())
    idx = np.empty(n, dtype=np.int64)
    age = np.empty(n, dtype=np.int64)
    sex = np.empty(n, dtype=np.int64)
    syn = np.zeros(n, dtype=bool)
    pos = 0
    all_rows = np.arange(layer.n, dtype=np.int64)
    for a in range(counts.shape[0]):  # 逐次ループ宣言(P4): 年齢階級×性別 = 32 セル
        for s in range(counts.shape[1]):
            want = int(counts[a, s])
            if want <= 0:
                continue
            rows = np.flatnonzero((bins == a) & (layer.sex == s))
            take = min(want, rows.size)
            if take:
                chosen = rows[_perm(rows.size, f"{domain}.pick", a, s)[:take]]
                idx[pos : pos + take] = chosen
                age[pos : pos + take] = layer.age[chosen]
                sex[pos : pos + take] = s
            need = want - take
            if need:
                seeds = rows if rows.size else all_rows
                pick = stream(MASTER_SEED, f"{domain}.gen", a, s).integers(0, seeds.size, need)
                chosen = seeds[pick]
                idx[pos + take : pos + want] = chosen
                lo = int(AGE_EDGES[a])
                hi = int(AGE_EDGES[a + 1]) if a + 1 < AGE_EDGES.size else lo + 30
                age[pos + take : pos + want] = stream(
                    MASTER_SEED, f"{domain}.age", a, s
                ).integers(lo, hi, need)
                sex[pos + take : pos + want] = s
                syn[pos + take : pos + want] = True
            pos += want
    order = _perm(n, f"{domain}.shuffle")
    return _Cohort(
        name=name, kind=kind, purpose=purpose, idx=idx[order], layer=layer_no,
        age=age[order], sex=sex[order], synthetic=syn[order],
        is_foreign=layer.is_foreign[idx[order]],
    )


def _draw_cohort_free(
    name: str, kind: int, purpose: int, layer: P.PoolLayer, layer_no: int, n: int,
    domain: str, mask: np.ndarray | None = None,
) -> _Cohort:
    """raking せずに層(の部分集合)から抽出する。不足は複製(``synthetic``)。"""
    rows = np.flatnonzero(mask) if mask is not None else np.arange(layer.n, dtype=np.int64)
    n = int(max(n, 0))
    if rows.size == 0:
        empty = np.zeros(0, dtype=np.int64)
        return _Cohort(name, kind, purpose, empty, layer_no, empty, empty,
                       np.zeros(0, dtype=bool), np.zeros(0, dtype=bool))
    take = min(n, rows.size)
    chosen = rows[_perm(rows.size, f"{domain}.pick")[:take]]
    syn = np.zeros(n, dtype=bool)
    if n > take:
        extra = rows[stream(MASTER_SEED, f"{domain}.gen").integers(0, rows.size, n - take)]
        chosen = np.concatenate([chosen, extra])
        syn[take:] = True
    return _Cohort(
        name=name, kind=kind, purpose=purpose, idx=chosen, layer=layer_no,
        age=layer.age[chosen].astype(np.int64), sex=layer.sex[chosen].astype(np.int64),
        synthetic=syn, is_foreign=layer.is_foreign[chosen],
    )


def _make_dispatchers(worker_counts: np.ndarray, n: int) -> _Cohort:
    """指令(素材なし=完全な新規生成)。年齢×性別は従業者の結合分布から引く。"""
    flat = worker_counts.ravel().astype(np.float64)
    probs = flat / flat.sum() if flat.sum() > 0 else np.ones(flat.size) / flat.size
    cells = _multinomial_assign(n, probs, "w16.dispatcher.cell")
    a = cells // worker_counts.shape[1]
    s = cells % worker_counts.shape[1]
    lo = AGE_EDGES[np.clip(a, 0, AGE_EDGES.size - 1)]
    hi = np.where(a + 1 < AGE_EDGES.size, AGE_EDGES[np.clip(a + 1, 0, AGE_EDGES.size - 1)], lo + 30)
    frac = stream(MASTER_SEED, "w16.dispatcher.age").random(n)
    age = (lo + frac * np.maximum(hi - lo, 1)).astype(np.int64)
    return _Cohort(
        name="dispatchers", kind=KIND_DISPATCHER, purpose=PUR_DUTY,
        idx=np.full(n, -1, dtype=np.int64), layer=0, age=age, sex=s.astype(np.int64),
        synthetic=np.ones(n, dtype=bool), is_foreign=np.zeros(n, dtype=bool),
    )


def _chome_coverage(
    polys: list[SH.Polygon], place_to_cell: dict[str, int], step: float
) -> tuple[np.ndarray, np.ndarray, list[tuple[np.ndarray, np.ndarray]]]:
    """町丁目 × 世界セルの被覆(固定格子の標本化・乱数なし)。

    Returns:
        ``(被覆率[n], 標本面積[n], 町丁目ごとの (セル索引, 標本点数))``。

    逐次ループ宣言(P4): 町丁目数(80)ぶん。
    """
    cov = np.zeros(len(polys), dtype=np.float64)
    area = np.zeros(len(polys), dtype=np.float64)
    per_cell: list[tuple[np.ndarray, np.ndarray]] = []
    empty = (np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64))
    for k, poly in enumerate(polys):
        if poly.points.size == 0:
            per_cell.append(empty)
            continue
        xmin = float(poly.points[:, 0].min())
        ymin = float(poly.points[:, 1].min())
        xmax = float(poly.points[:, 0].max())
        ymax = float(poly.points[:, 1].max())
        gx = np.arange(np.floor(xmin / step) * step + step / 2.0, xmax + step, step)
        gy = np.arange(np.floor(ymin / step) * step + step / 2.0, ymax + step, step)
        mx, my = np.meshgrid(gx, gy)
        mx = mx.ravel()
        my = my.ravel()
        ins = SH.points_in_polygon(mx, my, poly)
        n_in = int(ins.sum())
        area[k] = n_in * step * step
        if n_in == 0:
            per_cell.append(empty)
            continue
        ix = np.floor(mx[ins] / C.CELL_M).astype(np.int64)
        iy = np.floor(my[ins] / C.CELL_M).astype(np.int64)
        idx = np.array(
            [place_to_cell.get(C.place_id(int(a), int(b), "GL"), -1)
             for a, b in zip(ix, iy)],
            dtype=np.int64,
        )
        hit = idx >= 0
        cov[k] = float(hit.sum()) / n_in
        cells, counts = np.unique(idx[hit], return_counts=True)
        per_cell.append((cells, counts.astype(np.int64)))
    return cov, area, per_cell


def _assign_home_buildings(
    res_chome: np.ndarray, b_chome: np.ndarray, b_cell: np.ndarray,
    b_res: np.ndarray, b_area: np.ndarray, b_levels: np.ndarray, n_chome: int,
    cover_cells: list[tuple[np.ndarray, np.ndarray]],
) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    """町丁目の住民を**住居系建物の床面積**で按分し、建物→セルへ落とす(D-W16)。

    落とし先の優先順(1 つの町丁目の中で完結・町丁目の合計体数は必ず保たれる)
      1. その町丁目の**住居系**建物(床面積=``area_m2 × levels``)
      2. 1 が世界内に無ければ、その町丁目の**全建物**(用途不問・延床で按分)
      3. 2 も無ければ、被覆した**セルの面積**で按分(建物 −1・OSM の建物抽出が
         その町丁目に届いていない場合)

    さらに「空セル 0%」(決定台帳の合否ライン)を満たすため、**同じ町丁目の中で**
    住居床があるのに 0 体になったセルへ、最大のセルから 1 体ずつ移す(expedient)。

    逐次ループ宣言(P4): 町丁目数(80)ぶん。
    """
    floor = np.where(b_res, b_area * b_levels, 0.0)
    building = np.full(res_chome.size, -1, dtype=np.int64)
    cell = np.full(res_chome.size, -1, dtype=np.int64)
    stats = {"by_floor": 0, "by_any_building": 0, "by_covered_area": 0, "repairs": 0}
    for c in range(n_chome):
        rows = np.flatnonzero(res_chome == c)
        if rows.size == 0:
            continue
        cand = np.flatnonzero((b_chome == c) & (b_cell >= 0) & (floor > 0))
        weights = floor[cand]
        mode = "by_floor"
        if cand.size == 0:
            cand = np.flatnonzero((b_chome == c) & (b_cell >= 0))
            weights = np.maximum(b_area[cand] * b_levels[cand], 1.0)
            mode = "by_any_building"
        if cand.size == 0:
            cells, counts = cover_cells[c]
            if cells.size == 0:
                continue
            per = F.largest_remainder(counts.astype(np.float64), rows.size)
            cell[rows] = np.repeat(cells, per)
            stats["by_covered_area"] += int(rows.size)
            continue
        per = F.largest_remainder(weights, rows.size)
        per, moved = _fill_empty_cells(per, b_cell[cand])
        stats[mode] += int(rows.size)
        stats["repairs"] += moved
        building[rows] = np.repeat(cand, per)
        cell[rows] = b_cell[building[rows]]
    return building, cell, stats


def _fill_empty_cells(per: np.ndarray, cells: np.ndarray) -> tuple[np.ndarray, int]:
    """建物ごとの配分 → 「候補建物のあるセルは必ず 1 体以上」へ直す(合計は不変)。

    逐次ループ宣言(P4): 空セル数ぶん(通常 0-数件)。
    """
    per = np.asarray(per, dtype=np.int64).copy()
    uniq = np.unique(cells)
    pos = np.searchsorted(uniq, cells)
    moved = 0
    for _ in range(uniq.size):
        totals = np.zeros(uniq.size, dtype=np.int64)
        np.add.at(totals, pos, per)
        empty_cells = np.flatnonzero(totals == 0)
        if empty_cells.size == 0:
            break
        donor = int(np.argmax(totals))
        if totals[donor] <= 1:
            break
        members = np.flatnonzero(pos == donor)
        give = members[int(np.argmax(per[members]))]
        target = np.flatnonzero(pos == empty_cells[0])[0]
        per[give] -= 1
        per[target] += 1
        moved += 1
    return per, moved


def _build_households(
    res_cell: np.ndarray, res_building: np.ndarray, res_chome: np.ndarray,
    res_by_chome: np.ndarray, setai: np.ndarray, coverage: np.ndarray, keys: list[str],
) -> tuple[np.ndarray, dict[str, Any]]:
    """建物内の住民を町丁目の平均世帯人員に合わせて切り分ける(expedient)。

    逐次ループ宣言(P4): 町丁目数(80)ぶん。
    """
    hh_id = np.full(res_cell.size, -1, dtype=np.int64)
    hh_chome: list[int] = []
    hh_cell: list[int] = []
    hh_building: list[int] = []
    hh_size: list[int] = []
    next_id = 0
    target_hh = F.largest_remainder(setai * coverage, int(round(float((setai * coverage).sum()))))
    for c in range(len(keys)):
        rows = np.flatnonzero(res_chome == c)
        if rows.size == 0:
            continue
        want = max(int(target_hh[c]), 1)
        want = min(want, rows.size)
        # 建物ごとに固まるよう並べ替えてから、世帯サイズの整数配分で切る
        rows = rows[np.argsort(res_building[rows], kind="stable")]
        sizes = F.largest_remainder(np.ones(want), rows.size)
        sizes = sizes[sizes > 0]
        for grp in _deal(sizes, rows):
            hh_id[grp] = next_id
            hh_chome.append(c)
            hh_cell.append(int(res_cell[grp[0]]))
            hh_building.append(int(res_building[grp[0]]))
            hh_size.append(int(grp.size))
            next_id += 1
    table = {
        "household_id": np.arange(next_id, dtype=np.int32),
        "chome_key": [keys[c] for c in hh_chome],
        "home_cell": np.asarray(hh_cell, dtype=np.int32),
        "home_building": np.asarray(hh_building, dtype=np.int32),
        "size": np.asarray(hh_size, dtype=np.int16),
    }
    return hh_id, table


def _industry_sex_targets(doc: dict[str, Any]) -> dict[str, tuple[float, float]]:
    """経済センサス(町丁目別・産業中分類)→ ``industry_key → (男, 女)``。"""
    middles = doc["by_middle"]
    mapping = doc["_meta"]["sim_mapping"]
    out: dict[str, tuple[float, float]] = {}
    for key, spec in mapping.items():
        majors = set(spec.get("majors") or spec.get("census_majors") or [])
        mids = set(spec.get("middles") or spec.get("census_middles") or [])
        male = female = 0.0
        for code, row in middles.items():
            hit = code in mids if mids else (row.get("major") in majors)
            if hit:
                male += float(row.get("employees_male") or 0)
                female += float(row.get("employees_female") or 0)
        out[key] = (male, female)
    return out


def _overall_female_share(ind_sex: dict[str, tuple[float, float]]) -> float:
    male = sum(v[0] for v in ind_sex.values())
    female = sum(v[1] for v in ind_sex.values())
    return female / (male + female) if male + female > 0 else 0.5


def _assign_seats_by_industry_sex(
    seats_org: np.ndarray, seat_industry: np.ndarray, worker_sex: np.ndarray,
    ind_sex: dict[str, tuple[float, float]],
) -> np.ndarray:
    """従業者 → 組織の座席。産業ごとの男女比を経済センサスへ合わせる。

    返り値は「従業者行 i がどの座席に座るか」の座席添字。座席数と従業者数は等しい。

    逐次ループ宣言(P4): 産業キー数(15)ぶん。
    """
    n = int(worker_sex.size)
    if int(seats_org.size) != n:
        raise ValueError("座席数と従業者数が違う")
    industries = sorted(set(seat_industry.tolist()))
    seat_of_worker = np.empty(n, dtype=np.int64)
    female_rows = np.flatnonzero(worker_sex == 1)
    male_rows = np.flatnonzero(worker_sex != 1)
    female_rows = female_rows[_perm(female_rows.size, "w16.seat.female")]
    male_rows = male_rows[_perm(male_rows.size, "w16.seat.male")]
    seats_by_ind = {k: np.flatnonzero(seat_industry == k) for k in industries}
    shares = []
    for k in industries:
        m, f = ind_sex.get(k, (1.0, 1.0))
        shares.append(f / (m + f) if m + f > 0 else 0.5)
    sizes = np.array([seats_by_ind[k].size for k in industries], dtype=np.float64)
    want_f = F.largest_remainder(sizes * np.asarray(shares), int(female_rows.size))
    want_f = np.minimum(want_f, sizes.astype(np.int64))
    short = int(female_rows.size) - int(want_f.sum())
    if short > 0:  # 端数の押し込み(容量の余っている産業へ)
        room = sizes.astype(np.int64) - want_f
        for i in np.argsort(-room):
            add = min(short, int(room[i]))
            want_f[i] += add
            short -= add
            if short <= 0:
                break
    fpos = mpos = 0
    for i, k in enumerate(industries):
        seats = seats_by_ind[k]
        nf = int(want_f[i])
        nm = int(seats.size) - nf
        rows = np.concatenate([female_rows[fpos : fpos + nf], male_rows[mpos : mpos + nm]])
        fpos += nf
        mpos += nm
        seat_of_worker[rows] = seats[: rows.size]
    return seat_of_worker


def _duty_roster(
    span: dict[str, tuple[int, int]], kind: np.ndarray, age: np.ndarray, sex: np.ndarray,
    work_cell: np.ndarray, direction: np.ndarray, l5: P.PoolLayer, crew: _Cohort,
    dispatchers: _Cohort,
) -> dict[str, Any]:
    """カタログ #15(乗務員・指令・公共サービス要員)の名簿。"""
    rows_crew = np.arange(*span["crew"])
    rows_disp = np.arange(*span["dispatchers"])
    rows = np.concatenate([rows_crew, rows_disp])
    roles = [str(r) for r in np.asarray(l5.col("role"), dtype=object)[crew.idx]]
    posts = [str(p) for p in np.asarray(l5.col("post"), dtype=object)[crew.idx]]
    roles += ["指令"] * dispatchers.n
    posts += ["運行指令所"] * dispatchers.n
    return {
        "agent_id": rows.astype(np.int32),
        "kind": kind[rows],
        "role": roles,
        "post": posts,
        "age": age[rows],
        "sex": sex[rows],
        "work_cell": work_cell[rows].astype(np.int32),
        "direction_node": direction[rows].astype(np.int32),
    }


def _cohort_rows(
    span: dict[str, tuple[int, int]], cohorts: list[_Cohort], kind: np.ndarray,
    n_res_target: int, n_work_seats: int, n_res_in_area: int, n_commuter: int,
    n_student: int, n_business: int, n_private: int, n_regular: int, n_dispatch: int,
    ward_night: int, ward_day: int, ward_inflow: int,
) -> dict[str, Any]:
    """層別体数・目標値・出所(1 コホート 1 行)。"""
    sources = {
        "resident": "国勢調査2020 小地域(町丁目人口 × 世界セル被覆率)",
        "commuter": "経済センサス2021 町丁目別 従業者数 − 在区就業の住民",
        "student": "PT2018 自宅－通学/自宅－勤務 の到着比 × 従業者数",
        "regular_visitor": "PT2018 自宅－私事 比 × 従業者数(在庫上限=L3 regular)",
        "business_visitor": "PT2018 自宅－業務/自宅－勤務 の到着比 × 従業者数",
        "visitor": "PT2018 自宅－私事/自宅－勤務 の到着比 × 従業者数(定期来街を除く)",
        "crew": "v1 プール L5 の職務者在庫(公的な要員規模は未取得)",
        "council": "v1 プール L5 の議員 34(渋谷区議会定数)",
        "dispatchers": "expedient(鉄道4事業者×指令席3×交代2)",
    }
    targets = {
        "resident": n_res_target,
        "commuter": n_commuter,
        "student": n_student,
        "regular_visitor": n_regular,
        "business_visitor": n_business,
        "visitor": max(n_private - n_regular, 0),
        "crew": None,
        "council": None,
        "dispatchers": n_dispatch,
    }
    rows = []
    for c in cohorts:
        a, b = span[c.name]
        rows.append(
            {
                "cohort": c.name,
                "n": int(b - a),
                "target": targets.get(c.name),
                "pool_layer": c.layer,
                "synthetic": int(c.synthetic.sum()),
                "source": sources.get(c.name, ""),
            }
        )
    return {
        "cohorts": rows,
        "n_total": int(sum(r["n"] for r in rows)),
        "org_seats": n_work_seats,
        "residents_working_in_area": n_res_in_area,
        "ward_anchors": {
            "夜間人口": ward_night,
            "昼間人口": ward_day,
            "流入(他市区町村常住)": ward_inflow,
            "従業者(区・経済センサス2021)": 516541,
        },
        "note": "40 万体は目標ではなく結果(答申 §3-1 案C)。空間支持は W2 セルの覆う範囲。",
    }
