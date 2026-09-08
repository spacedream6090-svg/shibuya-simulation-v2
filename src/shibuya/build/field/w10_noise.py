"""W10 静的騒音場(§1 W10・D-W11)。

式(ASJ RTN-Model 2018・親一次確認済み)
  ``L_WA = a + b·lg V``。**一般道=非定常交通流**(10≤V≤60 km/h)・密粒舗装 Table 2.3:
  Light 82.3 / Heavy(2区分) 88.8・b=10。排水性舗装 Table A4.1: Light 76.6 / Heavy 84.9。
  首都高等の**定常交通流**は Light 45.8 / Heavy 53.2・b=30。
  伝搬 ``L_A = L_WA − 8 − 20·lg r + ΔL``(ΔL=0=expedient)。
  1時間の等価騒音レベルは、直線・定速の通過をエネルギー積分した標準形
  ``L_Aeq,1h = L_A,max + 10·lg(π r / v) + 10·lg N − 10·lg 3600``(v[m/s]・N=当該時間の台数)
  を車線ごとに立て、車線・車種でパワー和する。

入力
  - 道路交通センサス R3 東京都 箇所別基本表 ``kasyo13.csv``(cp932・159列・3,335区間)。
    使用列(**ヘッダ名で探す**): 昼間12時間自動車類交通量(上下合計)/合計・24時間同・
    昼間12時間大型車混入率(％)・昼間12時間平均旅行速度(上り/下り)・幅員構成/車道幅員(ｍ)・車線数。
  - 都環境局 令和5年度 常時監視測定地点 ``r5_joji_kanshi_points.csv``(較正 7 点)。
  - W1 歩行グラフ(街路格子=D-W9 の 2.5m 格子・8m バッファ)。

**手動対応表(edge → センサス区間)について**: 現行の ``w1_edges.parquet`` にも上流の
``shibuya_osm_wide_v8.json`` の edges にも**道路名(name/ref)が無く**、``kasyo13.csv`` にも
**座標が無い**ため、名寄せも幾何近接も成立しない。よって対応表は**空**で、全エッジが
klass 別既定交通量にフォールバックする(件数をゲートに出す。調整はしない)。
既定表そのものは渋谷区のセンサス実測行から導く(道路種別3/4→primary・6→secondary)。

expedient(すべて感度試験対象)
- klass → AADT 既定表(tertiary 以下の公的既定表は存在しない=D-W11 の空欄)。
- 時間帯配分=昼間12h(7-18時)と残り12h(19-6時)をそれぞれ一様に割る。
- 大型車混入率は昼夜同一(昼間12h の値を夜にも当てる)。
- 旅行速度は昼夜同一(夜間の実測が無い)。
- 舗装種別=既定は密粒(排水性の分布が不明)。較正点だけ CSV の低騒音舗装欄を使う。
- ΔL(回折・反射・地表面)=0。街渓谷反射・遮音壁を見ない。
- 等価単一線音源ではなく**車線別線音源**とし、交通量を車線数で等分する。
- バンド遮蔽 UG −20 dB(根拠なし)。DECK 0 dB。
- B4 騒音段階の境界は環境基準(道路に面する地域)の値に釘付け(語彙の割当は expedient)。
"""

from __future__ import annotations

import csv
import io
import math
from collections import Counter
from typing import Any, Sequence

import numpy as np

from . import common as C
from .street_grid import segment_arrays, street_points

STAGE = "W10"
STAGE_VERSION = "1.0.0"

KASYO = ("realworld", "road_census_r3", "kasyo13.csv")
R5_POINTS = ("realworld", "tokyo_noise", "r5_joji_kanshi_points.csv")

# --- ASJ RTN-Model 2018 係数(親実読・Table 2.3 / Table A4.1)------------------------------
ASJ_COEFF: dict[str, dict[str, float]] = {
    # 非定常交通流・密粒舗装(Table 2.3)
    "nonsteady_dense": {"light": 82.3, "heavy": 88.8, "b": 10.0},
    # 非定常交通流・排水性舗装(Table A4.1・c/y の経年項は未適用=新設時相当)
    "nonsteady_drain": {"light": 76.6, "heavy": 84.9, "b": 10.0},
    # 定常交通流(首都高等・Table 2.3 の定常側)
    "steady_dense": {"light": 45.8, "heavy": 53.2, "b": 30.0},
}
V_MIN_NONSTEADY = 10.0
V_MAX_NONSTEADY = 60.0
PROPAGATION_OFFSET_DB = 8.0  # L_A = L_WA − 8 − 20 lg r
DELTA_L_DB = 0.0  # 回折・反射・地表面(expedient)

#: 交通を持つ klass(騒音源)。footway/pedestrian/steps/path/cycleway/corridor/elevator は非音源。
ROAD_KLASSES: tuple[str, ...] = (
    "primary",
    "secondary",
    "tertiary",
    "residential",
    "unclassified",
    "living_street",
    "service",
)

#: klass → 既定交通量の作り方。``from_census`` は渋谷区センサス行の中央値、``scale_of`` は
#: 別 klass の交通量に係数を掛ける(expedient・D-W11 の空欄)。
KLASS_DEFAULT_RULE: dict[str, dict[str, Any]] = {
    "primary": {"from_census": (3, 4)},  # 道路種別 3=一般国道・4=主要地方道
    "secondary": {"from_census": (6,)},  # 6=一般都道
    "tertiary": {"scale_of": "secondary", "q": 0.30, "v": 20.0, "width_m": 7.0, "lanes": 2},
    "residential": {"scale_of": "secondary", "q": 0.10, "v": 20.0, "width_m": 5.5, "lanes": 2},
    "unclassified": {"scale_of": "secondary", "q": 0.10, "v": 20.0, "width_m": 5.5, "lanes": 2},
    "living_street": {"scale_of": "secondary", "q": 0.05, "v": 15.0, "width_m": 5.0, "lanes": 1},
    "service": {"scale_of": "secondary", "q": 0.03, "v": 15.0, "width_m": 4.0, "lanes": 1},
}

#: バンド別の遮蔽(expedient・根拠なし)。
BAND_SHIELDING_DB: dict[str, float] = {"GL": 0.0, "DECK": 0.0, "UG": -20.0}

#: B4 騒音段階(知覚契約書 §2.4 ⑤「段階語彙は法定/LOS境界に釘付け」)。
#: 境界=環境基本法 環境基準「道路に面する地域」A/B類型(昼60/夜55)・C類型(昼65/夜60)・
#: 幹線道路近接空間(昼70/夜65)。語彙の割当そのものは expedient(契約書に語彙表が無い)。
NOISE_STAGE_VOCAB: tuple[str, ...] = ("静か", "普通", "騒がしい", "うるさい")
NOISE_STAGE_BOUNDS_DAY: tuple[float, float, float] = (60.0, 65.0, 70.0)
NOISE_STAGE_BOUNDS_NIGHT: tuple[float, float, float] = (55.0, 60.0, 65.0)

#: 昼(6-22時)・夜(22-6時)= 環境基準の時間区分。
DAY_HOURS: tuple[int, ...] = tuple(range(6, 22))
NIGHT_HOURS: tuple[int, ...] = (22, 23, 0, 1, 2, 3, 4, 5)
#: センサスの「昼間12時間」= 7-18時(19時まで)とみなす(expedient)。
CENSUS_DAY12_HOURS: tuple[int, ...] = tuple(range(7, 19))

#: 総務省 全国地方公共団体コード(較正点の住所から市区町村を引くための最小表)。
CITY_CODE: dict[str, str] = {"渋谷区": "13113", "目黒区": "13110", "世田谷区": "13112"}


# --- kasyo13.csv --------------------------------------------------------------------------
def _col(header: Sequence[str], name: str) -> int:
    for i, h in enumerate(header):
        if h == name:
            return i
    raise KeyError(f"kasyo13.csv に列が無い: {name}")


def _num(text: str) -> float | None:
    text = text.strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def read_kasyo(path) -> list[dict[str, Any]]:
    """箇所別基本表 → 区間辞書のリスト(必要列のみ・ヘッダ名で探す)。"""
    raw = path.read_bytes().decode("cp932")
    rows = list(csv.reader(io.StringIO(raw)))
    hdr = rows[0]
    idx = {
        "section_id": _col(hdr, "交通調査基本区間番号"),
        "road_kind": _col(hdr, "道路種別"),
        "route_no": _col(hdr, "路線番号"),
        "route_name": _col(hdr, "路線名"),
        "city": _col(hdr, "市区町村コード"),
        "q12": _col(hdr, "昼間１２時間自動車類交通量（上下合計）／合計（台）"),
        "q24": _col(hdr, "２４時間自動車類交通量（上下合計）／合計（台）"),
        "heavy_pct": _col(hdr, "昼間１２時間大型車混入率（％）"),
        "v_up": _col(hdr, "昼間１２時間平均旅行速度（時間帯別交通量加重）／上り（ｋｍ／ｈ）"),
        "v_dn": _col(hdr, "昼間１２時間平均旅行速度（時間帯別交通量加重）／下り（ｋｍ／ｈ）"),
        "width_m": _col(hdr, "幅員構成／車道幅員（ｍ）"),
        "lanes": _col(hdr, "車線数"),
    }
    out: list[dict[str, Any]] = []
    for r in rows[1:]:
        if len(r) <= idx["lanes"]:
            continue
        vs = [v for v in (_num(r[idx["v_up"]]), _num(r[idx["v_dn"]])) if v is not None and v > 0]
        out.append(
            {
                "section_id": r[idx["section_id"]].strip(),
                "road_kind": r[idx["road_kind"]].strip(),
                "route_no": r[idx["route_no"]].strip(),
                "route_name": r[idx["route_name"]].strip(),
                "route_key": C.normalize_jp(r[idx["route_name"]]),
                "city": r[idx["city"]].strip(),
                "q12": _num(r[idx["q12"]]),
                "q24": _num(r[idx["q24"]]),
                "heavy_pct": _num(r[idx["heavy_pct"]]),
                "v_kmh": (sum(vs) / len(vs)) if vs else None,
                "width_m": _num(r[idx["width_m"]]),
                "lanes": _num(r[idx["lanes"]]),
            }
        )
    return out


def _usable(sec: dict[str, Any]) -> bool:
    return all(
        sec[k] is not None and sec[k] > 0
        for k in ("q12", "q24", "v_kmh", "width_m", "lanes")
    ) and sec["heavy_pct"] is not None


def median_section(secs: Sequence[dict[str, Any]]) -> dict[str, float]:
    """区間群 → 列ごとの中央値(決定論のため下側中央値)。"""
    ok = [s for s in secs if _usable(s)]
    if not ok:
        raise ValueError("使える区間が無い")
    return {
        "q12": C.median([s["q12"] for s in ok]),
        "q24": C.median([s["q24"] for s in ok]),
        "heavy_pct": C.median([s["heavy_pct"] for s in ok]),
        "v_kmh": C.median([s["v_kmh"] for s in ok]),
        "width_m": C.median([s["width_m"] for s in ok]),
        "lanes": C.median([s["lanes"] for s in ok]),
        "n": float(len(ok)),
    }


def route_match(sections: Sequence[dict[str, Any]], name: str, city: str | None) -> list[dict]:
    """路線名(+市区町村)でセンサス区間を引く。正規化一致→末尾「線」を落とした前方一致。"""
    key = C.normalize_jp(name)
    hits = [s for s in sections if s["route_key"] == key]
    if not hits:
        stem = key[:-1] if key.endswith("線") else key
        hits = [
            s
            for s in sections
            if (s["route_key"][:-1] if s["route_key"].endswith("線") else s["route_key"]).startswith(
                stem
            )
            or stem.startswith(s["route_key"][:-1] if s["route_key"].endswith("線") else s["route_key"])
        ]
    if city:
        in_city = [s for s in hits if s["city"] == city]
        if in_city:
            return in_city
    return hits


# --- ASJ 音響モデル ------------------------------------------------------------------------
def l_wa(vehicle: str, v_kmh: float, regime: str = "nonsteady_dense") -> float:
    """ASJ RTN-Model 2018 の音響パワーレベル ``L_WA = a + b·lg V`` [dB]。"""
    co = ASJ_COEFF[regime]
    v = v_kmh
    if regime.startswith("nonsteady"):
        v = C.clamp(v, V_MIN_NONSTEADY, V_MAX_NONSTEADY)
    if v <= 0:
        raise ValueError("V>0 が必要")
    return co[vehicle] + co["b"] * math.log10(v)


def l_a_max(power_level_db: float, r_m: float) -> float:
    """伝搬 ``L_A = L_WA − 8 − 20·lg r + ΔL``(点音源・反射面上)。"""
    if r_m <= 0:
        raise ValueError("r>0 が必要")
    return power_level_db - PROPAGATION_OFFSET_DB - 20.0 * math.log10(r_m) + DELTA_L_DB


def lane_energy_coeff(vehicle: str, v_kmh: float, n_per_hour: float, regime: str) -> float:
    """1車線・1時間・単位距離あたりのエネルギー係数 A(``LAeq = 10·lg(A/r)``)。

    ``LAeq,1h = L_WA − 8 − 20 lg r + 10 lg(π r / v) + 10 lg N − 10 lg 3600``
    の右辺を整理すると ``10·lg( 10^((L_WA−8)/10) · (π/v) · N / 3600 / r )``。
    """
    if n_per_hour <= 0:
        return 0.0
    v_ms = C.clamp(v_kmh, V_MIN_NONSTEADY, V_MAX_NONSTEADY) / 3.6
    return C.power_from_db(l_wa(vehicle, v_kmh, regime) - PROPAGATION_OFFSET_DB + DELTA_L_DB) * (
        math.pi / v_ms
    ) * n_per_hour / 3600.0


def lane_offsets(width_m: float, lanes: int) -> list[float]:
    """車道中心線から見た各車線中心の符号つき横位置(近い側が正・降順)。"""
    n = max(int(lanes), 1)
    w = width_m / n
    return [width_m / 2.0 - (i + 0.5) * w for i in range(n)]


def geometry_factor(d_m: float, width_m: float, lanes: int) -> float:
    """車線別線音源の幾何係数 ``Σ_i 1/r_i``(d=車道中心線からの距離)。

    ``r_i = max(d − x_i, w/2)``(w=1車線幅)。車道上の点でも半車線幅で床を打つ。
    """
    n = max(int(lanes), 1)
    w = width_m / n
    total = 0.0
    for x in lane_offsets(width_m, n):
        total += 1.0 / max(d_m - x, w / 2.0)
    return total


def hourly_flows(q12: float, q24: float, heavy_pct: float) -> dict[int, tuple[float, float]]:
    """時刻 → (小型車 台/h, 大型車 台/h)。昼間12h=7-18時・残りを 19-6時へ一様配分。"""
    q_day = q12 / 12.0
    q_night = max(q24 - q12, 0.0) / 12.0
    heavy = C.clamp(heavy_pct / 100.0, 0.0, 1.0)
    out: dict[int, tuple[float, float]] = {}
    for h in range(24):
        q = q_day if h in CENSUS_DAY12_HOURS else q_night
        out[h] = (q * (1.0 - heavy), q * heavy)
    return out


def energy_coeffs(sec: dict[str, float], regime: str) -> tuple[float, float]:
    """区間諸元 → (昼 A, 夜 A)。A は時間平均したエネルギー係数(``LAeq=10 lg(A·Σ1/r)``)。"""
    flows = hourly_flows(float(sec["q12"]), float(sec["q24"]), float(sec["heavy_pct"]))
    lanes = max(int(sec["lanes"]), 1)
    v = float(sec["v_kmh"])

    def avg(hours: Sequence[int]) -> float:
        total = 0.0
        for h in hours:
            n_light, n_heavy = flows[h]
            total += lane_energy_coeff("light", v, n_light / lanes, regime)
            total += lane_energy_coeff("heavy", v, n_heavy / lanes, regime)
        return total / len(hours)

    return avg(DAY_HOURS), avg(NIGHT_HOURS)


def laeq_at(sec: dict[str, float], d_m: float, regime: str) -> tuple[float, float]:
    """区間諸元+車道中心線からの距離 → (昼 LAeq, 夜 LAeq) [dB]。"""
    a_day, a_night = energy_coeffs(sec, regime)
    g = geometry_factor(d_m, float(sec["width_m"]), int(sec["lanes"]))
    return C.db_from_power(a_day * g), C.db_from_power(a_night * g)


def noise_stage(level_db: float, night: bool = False) -> int:
    """LAeq → B4 騒音段階の番号(0=静か .. 3=うるさい)。"""
    bounds = NOISE_STAGE_BOUNDS_NIGHT if night else NOISE_STAGE_BOUNDS_DAY
    for i, b in enumerate(bounds):
        if level_db < b:
            return i
    return len(bounds)


# --- 較正点 -------------------------------------------------------------------------------
def read_r5_points(path) -> list[dict[str, Any]]:
    """常時監視測定地点 CSV → 渋谷区5点+隣接2点(D-W11 の較正点)。"""
    raw = path.read_bytes().decode("cp932")
    rows = list(csv.reader(io.StringIO(raw)))
    want = {"61", "75", "78", "79", "80", "81", "82"}
    out: list[dict[str, Any]] = []
    for r in rows[2:]:
        if not r or r[0].strip() not in want:
            continue
        address = r[1].strip()
        city = next((c for name, c in CITY_CODE.items() if name in address), None)
        out.append(
            {
                "no": r[0].strip(),
                "address": address,
                "route_name": r[4].strip(),
                "lanes": int(float(r[5])) if r[5].strip() else 0,
                "road_kind": r[6].strip(),
                "noise_barrier": r[7].strip(),
                "low_noise_pavement": r[8].strip(),
                "dist_from_carriageway_m": float(r[14]) if r[14].strip() else None,
                "height_m": float(r[16]) if r[16].strip() else None,
                "measured_day_db": float(r[17]) if r[17].strip() else None,
                "measured_night_db": float(r[18]) if r[18].strip() else None,
                "city": city,
            }
        )
    return sorted(out, key=lambda d: int(d["no"]))


def calibrate(sections: Sequence[dict[str, Any]], points: Sequence[dict[str, Any]]) -> list[dict]:
    """較正点ごとにモデル値と実測の残差を出す。座標を必要としない(路線名で突合)。"""
    rows: list[dict[str, Any]] = []
    for p in points:
        hits = route_match(sections, p["route_name"], p["city"])
        usable = [s for s in hits if _usable(s)]
        if not usable:
            rows.append(
                {
                    **{k: p[k] for k in ("no", "address", "route_name")},
                    "status": "NOT_EVALUABLE: センサスに同名路線の使える区間が無い",
                    "n_sections": len(hits),
                    "model_day_db": None,
                    "model_night_db": None,
                    "residual_day_db": None,
                    "residual_night_db": None,
                }
            )
            continue
        sec = median_section(usable)
        # 較正点は CSV 自身の車線数/舗装/車道端距離を使う(mechanism)。
        lanes = p["lanes"] or int(sec["lanes"])
        width = float(sec["width_m"])
        drain = p["low_noise_pavement"] == "○"
        steady = p["road_kind"] == "2" or "高速" in p["route_name"]
        regime = "steady_dense" if steady else ("nonsteady_drain" if drain else "nonsteady_dense")
        row_sec = {**sec, "lanes": lanes, "width_m": width}
        d = float(p["dist_from_carriageway_m"]) + width / 2.0  # 車道中心線からの距離
        day, night = laeq_at(row_sec, d, regime)
        rows.append(
            {
                **{k: p[k] for k in ("no", "address", "route_name")},
                "status": "OK",
                "n_sections": len(usable),
                "regime": regime,
                "lanes": lanes,
                "width_m": round(width, 1),
                "dist_from_carriageway_m": p["dist_from_carriageway_m"],
                "q12": sec["q12"],
                "q24": sec["q24"],
                "heavy_pct": sec["heavy_pct"],
                "v_kmh": round(sec["v_kmh"], 1),
                "model_day_db": round(day, 1),
                "model_night_db": round(night, 1),
                "measured_day_db": p["measured_day_db"],
                "measured_night_db": p["measured_night_db"],
                "residual_day_db": round(day - p["measured_day_db"], 1),
                "residual_night_db": round(night - p["measured_night_db"], 1),
            }
        )
    return rows


# --- 騒音場 -------------------------------------------------------------------------------
def _nearest_edges(
    px: np.ndarray,
    py: np.ndarray,
    seg: tuple[np.ndarray, ...],
    n_near: int,
    bucket_m: float,
    rings: int,
) -> tuple[np.ndarray, np.ndarray]:
    """各点から近い順に ``n_near`` 本の**別エッジ**とその距離を返す。

    Returns:
        (edge_idx[n_pts, n_near], dist[n_pts, n_near])。見つからない枠は edge=-1・dist=inf。
    """
    ax, ay, bx, by, own = seg
    n_seg = ax.shape[0]
    n_pts = px.shape[0]
    res_e = np.full((n_pts, n_near), -1, dtype=np.int32)
    res_d = np.full((n_pts, n_near), np.inf, dtype=np.float64)
    if n_seg == 0 or n_pts == 0:
        return res_e, res_d

    # 線分をバケットへ(bbox の触れる全バケット)
    buckets: dict[tuple[int, int], list[int]] = {}
    for i in range(n_seg):
        i0 = int(math.floor(min(ax[i], bx[i]) / bucket_m))
        i1 = int(math.floor(max(ax[i], bx[i]) / bucket_m))
        j0 = int(math.floor(min(ay[i], by[i]) / bucket_m))
        j1 = int(math.floor(max(ay[i], by[i]) / bucket_m))
        for ii in range(i0, i1 + 1):
            for jj in range(j0, j1 + 1):
                buckets.setdefault((ii, jj), []).append(i)

    pi = np.floor(px / bucket_m).astype(np.int64)
    pj = np.floor(py / bucket_m).astype(np.int64)
    order: dict[tuple[int, int], list[int]] = {}
    for k in range(n_pts):
        order.setdefault((int(pi[k]), int(pj[k])), []).append(k)

    for (bi, bj), members in sorted(order.items()):
        cand: set[int] = set()
        for ii in range(bi - rings, bi + rings + 1):
            for jj in range(bj - rings, bj + rings + 1):
                lst = buckets.get((ii, jj))
                if lst:
                    cand.update(lst)
        if not cand:
            continue
        cid = np.fromiter(sorted(cand), dtype=np.int64)
        idx = np.asarray(members, dtype=np.int64)
        qx = px[idx][:, None]
        qy = py[idx][:, None]
        sax = ax[cid][None, :]
        say = ay[cid][None, :]
        dx = (bx[cid] - ax[cid])[None, :]
        dy = (by[cid] - ay[cid])[None, :]
        den = dx * dx + dy * dy
        den = np.where(den <= 0.0, 1.0, den)
        t = np.clip(((qx - sax) * dx + (qy - say) * dy) / den, 0.0, 1.0)
        dist = np.hypot(qx - (sax + t * dx), qy - (say + t * dy))
        take = min(dist.shape[1], n_near * 6)
        part = np.argpartition(dist, take - 1, axis=1)[:, :take]
        rowi = np.arange(dist.shape[0])[:, None]
        sub = dist[rowi, part]
        sort = np.argsort(sub, axis=1, kind="stable")
        part = part[rowi, sort]
        sub = sub[rowi, sort]
        owners = own[cid[part]]
        for row in range(idx.shape[0]):
            seen: list[int] = []
            for col in range(take):
                e = int(owners[row, col])
                if e in seen:
                    continue
                seen.append(e)
                res_e[idx[row], len(seen) - 1] = e
                res_d[idx[row], len(seen) - 1] = float(sub[row, col])
                if len(seen) == n_near:
                    break
    return res_e, res_d


def run(ctx: C.Ctx) -> C.StageResult:
    kasyo_p = ctx.path(*KASYO)
    r5_p = ctx.path(*R5_POINTS)
    for p in (kasyo_p, r5_p):
        if not p.exists():
            raise FileNotFoundError(f"W10 入力が無い: {p}")
    edges_p = ctx.out / "w1_edges.parquet"
    geom_p = ctx.out / "w1_edge_geometry.npz"
    for p in (edges_p, geom_p):
        if not p.exists():
            raise FileNotFoundError(f"W10 は W1 の出力を必要とする: {p}")

    sections = read_kasyo(kasyo_p)
    r5 = read_r5_points(r5_p)
    edges = C.read_parquet_columns(
        edges_p, ["edge_idx", "klass", "band", "geom_start", "geom_count", "length_m"]
    )
    coords = np.load(geom_p)["coords"]

    # --- (a) 街路 2.5m 格子 ---
    grid = street_points(edges, coords)
    n_pts = len(grid)

    # --- (b) 交通量の割当 ---
    # 対応表: 道路名がどこにも無いので空(下の notes に診断を書く)。
    section_of_edge: dict[int, str] = {}
    shibuya = [s for s in sections if s["city"] == "13113"]
    census_defaults: dict[str, dict[str, float]] = {}
    for klass, rule in KLASS_DEFAULT_RULE.items():
        if "from_census" in rule:
            kinds = {str(k) for k in rule["from_census"]}
            census_defaults[klass] = median_section(
                [s for s in shibuya if s["road_kind"] in kinds]
            )
    for klass, rule in KLASS_DEFAULT_RULE.items():
        if "scale_of" in rule:
            base = census_defaults[rule["scale_of"]]
            census_defaults[klass] = {
                "q12": base["q12"] * rule["q"],
                "q24": base["q24"] * rule["q"],
                "heavy_pct": base["heavy_pct"],
                "v_kmh": float(rule["v"]),
                "width_m": float(rule["width_m"]),
                "lanes": float(rule["lanes"]),
                "n": 0.0,
            }

    # --- (c) 騒音場 ---
    road_mask = [k in ROAD_KLASSES for k in edges["klass"]]
    road_edges = [int(e) for e, m in zip(edges["edge_idx"], road_mask) if m]
    #: 交通を持つべきエッジ数を **入力(w1_edges の klass 列)から独立に**数える。
    #: 下の road_edges_with_traffic ゲートの期待値=これ(自明ゲートにしない)。
    n_edges_needing_traffic = sum(1 for k in edges["klass"] if k in ROAD_KLASSES)
    seg = segment_arrays(
        edges["edge_idx"], edges["geom_start"], edges["geom_count"], coords, keep=road_edges
    )
    klass_of_edge = {int(e): k for e, k in zip(edges["edge_idx"], edges["klass"])}

    a_day_of_edge: dict[int, float] = {}
    a_night_of_edge: dict[int, float] = {}
    geo_of_edge: dict[int, tuple[float, int]] = {}
    for e in road_edges:
        sec = census_defaults[klass_of_edge[e]]
        ad, an = energy_coeffs(sec, "nonsteady_dense")
        a_day_of_edge[e] = ad
        a_night_of_edge[e] = an
        geo_of_edge[e] = (float(sec["width_m"]), int(sec["lanes"]))

    near_e, near_d = _nearest_edges(
        grid.x.astype(np.float64), grid.y.astype(np.float64), seg, n_near=3, bucket_m=128.0, rings=2
    )
    day = np.zeros(n_pts, dtype=np.float64)
    night = np.zeros(n_pts, dtype=np.float64)
    for j in range(near_e.shape[1]):
        ecol = near_e[:, j]
        dcol = near_d[:, j]
        for k in range(n_pts):
            e = int(ecol[k])
            if e < 0:
                continue
            width, lanes = geo_of_edge[e]
            g = geometry_factor(float(dcol[k]), width, lanes)
            day[k] += a_day_of_edge[e] * g
            night[k] += a_night_of_edge[e] * g
    shield = np.array([BAND_SHIELDING_DB[b] for b in grid.band], dtype=np.float64)
    day_db = np.where(day > 0, 10.0 * np.log10(np.maximum(day, 1e-30)), 0.0) + shield
    night_db = np.where(night > 0, 10.0 * np.log10(np.maximum(night, 1e-30)), 0.0) + shield
    day_u8 = np.clip(np.rint(day_db), 0, 255).astype(np.uint8)
    night_u8 = np.clip(np.rint(night_db), 0, 255).astype(np.uint8)
    stage_day = np.array(
        [noise_stage(float(v), night=False) for v in day_db], dtype=np.uint8
    )
    stage_night = np.array(
        [noise_stage(float(v), night=True) for v in night_db], dtype=np.uint8
    )

    # --- (d) 較正 ---
    calib = calibrate(sections, r5)
    evaluable = [r for r in calib if r["status"] == "OK"]
    residuals = [
        abs(r[k]) for r in evaluable for k in ("residual_day_db", "residual_night_db")
    ]
    max_resid = max(residuals) if residuals else None

    params: dict[str, Any] = {
        "asj_coeff": ASJ_COEFF,
        "propagation": {"offset_db": PROPAGATION_OFFSET_DB, "delta_l_db": DELTA_L_DB},
        "v_clamp_kmh": [V_MIN_NONSTEADY, V_MAX_NONSTEADY],
        "grid": {"pitch_m": grid.pitch_m, "buffer_m": grid.buffer_m, "klasses": list(grid.klasses)},
        "road_klasses": list(ROAD_KLASSES),
        "klass_default_rule": KLASS_DEFAULT_RULE,
        "band_shielding_db": BAND_SHIELDING_DB,
        "stage_vocab": list(NOISE_STAGE_VOCAB),
        "stage_bounds_day": list(NOISE_STAGE_BOUNDS_DAY),
        "stage_bounds_night": list(NOISE_STAGE_BOUNDS_NIGHT),
        "day_hours": list(DAY_HOURS),
        "night_hours": list(NIGHT_HOURS),
        "census_day12_hours": list(CENSUS_DAY12_HOURS),
        "n_nearest_edges": 3,
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([kasyo_p, r5_p, edges_p, geom_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["街路面(可視・可聴の台)", "道路交通騒音場", "環境音(静的)"],
        expedients=[
            "klass→AADT 既定表(tertiary 以下の公的既定表なし=D-W11 の空欄)",
            "時間帯配分=昼間12h(7-18時)/残り12h を各一様",
            "大型車混入率・旅行速度は昼夜同一",
            "舗装種別の既定=密粒(排水性の分布不明)",
            "ΔL=0(回折・反射・地表面・遮音壁を見ない)",
            "車線別線音源+交通量の車線等分",
            "バンド遮蔽 UG −20 dB(根拠なし)",
            "B4 騒音段階の語彙割当(境界は環境基準に釘付け)",
            "街路格子のバッファ 8m・ピッチ 2.5m(D-W9 既決)",
        ],
        notes={
            "street_points_total": n_pts,
            "street_points_by_band": dict(sorted(Counter(grid.band).items())),
            "street_points_klasses": list(grid.klasses),
            "street_points_spec_reference": (
                "仕様書 §1 の 239,028 は v1 の klass 集合での値。本実装は w1_edges の全 klass"
                f"({len(grid.klasses)}種)を使うので一致しない(調整せず実測を出す)。"
            ),
            "census_rows_total": len(sections),
            "census_rows_shibuya": len(shibuya),
            "census_defaults": {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in census_defaults.items()},
            "road_edges": len(road_edges),
            "road_edges_needing_traffic": n_edges_needing_traffic,
            "road_edges_by_klass": dict(
                sorted(Counter(klass_of_edge[e] for e in road_edges).items())
            ),
            "road_klass_scope_note": (
                "音源とする klass=ROAD_KLASSES(primary/secondary/tertiary/residential/"
                "unclassified/living_street/service)。footway/pedestrian/steps/path/"
                "cycleway/corridor/elevator は非音源=交通行を持たない。"
            ),
            "section_match_diagnosis": (
                "手動対応表は作れない: w1_edges/OSM v8 の edges に道路名(name/ref)が無く、"
                "kasyo13.csv に座標が無い。名寄せ・幾何近接のいずれも成立しないため"
                "全エッジが klass 既定へフォールバック(primary 127 + secondary 75 の対応は未達)。"
            ),
            "expressway_absent": (
                "高速3号渋谷線等の高架は歩行グラフに motorway クラスが無く騒音場に不在(既知の欠落)。"
            ),
            "calibration_rows": calib,
            "calibration_note": (
                "R5 の CSV に座標が無く 町丁目境界も未取得のため、較正点を街路格子へ**置けない**。"
                "代わりに各点の路線名でセンサス区間を引き、CSV 自身の車道端距離・車線数・"
                "低騒音舗装で同じ式を評価した(格子への配置は NOT EVALUABLE)。"
            ),
            "day_db_percentiles": {
                p: round(float(np.percentile(day_db, p)), 1) for p in (5, 25, 50, 75, 95)
            },
            "night_db_percentiles": {
                p: round(float(np.percentile(night_db, p)), 1) for p in (5, 25, 50, 75, 95)
            },
            "stage_day_counts": {
                NOISE_STAGE_VOCAB[i]: int((stage_day == i).sum()) for i in range(4)
            },
            "stage_night_counts": {
                NOISE_STAGE_VOCAB[i]: int((stage_night == i).sum()) for i in range(4)
            },
        },
    )
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w10_street_points.parquet",
            {
                "x": grid.x,
                "y": grid.y,
                "band": grid.band,
                "nearest_edge_idx": grid.nearest_edge_idx,
            },
        )
    )
    res.outputs.append(C.write_npy(ctx.out, "w10_noise_day.npy", day_u8))
    res.outputs.append(C.write_npy(ctx.out, "w10_noise_night.npy", night_u8))
    res.outputs.append(C.write_npy(ctx.out, "w10_noise_stage_day.npy", stage_day))
    res.outputs.append(C.write_npy(ctx.out, "w10_noise_stage_night.npy", stage_night))
    res.gates = [
        C.Gate("street_points", n_pts, None),
        C.Gate("street_points_have_band", len(set(grid.band)), 3),
        C.Gate("noise_arrays_len", int(day_u8.shape[0]), n_pts),
        C.Gate("primary_secondary_sections_matched", len(section_of_edge), 202, passed=False),
        C.Gate("road_edges_with_traffic", len(a_day_of_edge), n_edges_needing_traffic),
        C.Gate("points_with_at_least_one_source", int((near_e[:, 0] >= 0).sum()), n_pts),
        C.Gate("calibration_points_evaluable", len(evaluable), None),
        C.Gate(
            "calibration_max_abs_residual_db",
            round(max_resid, 1) if max_resid is not None else None,
            None,
            passed=(max_resid is not None and max_resid <= 3.0),
        ),
    ]
    return res
