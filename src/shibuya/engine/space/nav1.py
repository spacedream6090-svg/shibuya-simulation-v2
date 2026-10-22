"""engine.space.nav1 — 第 5 期 空間の段 1: ナビメッシュの上を衝突なしで進む移動(切替口 ``--space {legacy,nav1}``)。

正: 空間の設計の下書き ``docs/design/v2-spatial-design-round-draft.md`` §4 段 1/指示書 10-03 §8 3-1(位置は (x, y, 階)
の連続値)・3-2 (c)(ナビメッシュの上を衝突なしで進む=つなぎ・既定の切り替えは 1 回)/指示書 10-06 SR11 (a)+(d)・
SR12 (a)+(d)/記録 ``docs/bench/analysis/spatial-2026-10/sp1/README.md``。

**何をするか**(移動の中身だけ=行き先・到着の後・到達の判定は今のエンジンのまま):

- 経路: 出発の点 (x, y, 階) → 行き先の W1 の節の面の上の点(資産 ``nav1_anchors``)。通りの選びは W1 の向きつきの辺の
  Dijkstra(**SR12 (a)**: 曲がる 1 回 = 50 m・上り 1 m = 3.8 m)、面の上の線は帯の A* と funnel
  (``world.navmesh_route.NavPlanner``)。経路の選びは本人の判断(段 3/判断モデルの後)=今は既定の重み(つなぎ)。
- 時間: 歩く区間は本人の歩く速さ(体の属性=``engine.geometry.desired_speeds``=10f K21 (a))× 坂の係数(**SR12 (d)**:
  Wood 2023 の舗装路の式・腕 Tobler)。区間は 5 m 以下に切って DEM の勾配を当てる。混み具合は前の刻みのセルの人数 ÷
  ナビメッシュのセルの歩ける面積で Kladek の式(C9 G2 (b) と同じ)。
- 接続口(**SR11 (a)+(d)**): 階段=高さ ÷ 上下の速さ(Fujiyama & Tyler 2004 の 24.6° の階段のふつうの速さの水平成分 ×
  tan・本人の速さの比を掛ける)・エスカレーター=高さ ÷ sin30° ÷ 30 m/分・エレベーター=高さ ÷ かごの速さ + 待ち(運行の
  間隔の半分)・スロープ=歩く(勾配は ±1/8 で切る)。階段・エスカレーター・エレベーターの水平の長さのうち段の水平の分を
  超える残りは平らに歩く(両端の離れた接続口で水平に速く動かない)。容量=1 分あたりの人数(資産 ``cap_per_min``)を刻みの長さで割り当て、超えた分は接続口の
  前で待つ(先着順=待ち始めた刻み → 体の番号)。
- 位置: (xy, 階)。セルは面から導く(``world.navmesh.cell_of``=(列, 行, 層) → W2 のセル・その層のセルが無ければ地上の
  セル)。層は ``cell_band[cell]``(11c の形)。

**状態**(``agents.state`` の 8 欄・``nav_columns``)は経路の出発の点・行き先・進んだ時間など。経路の形と時間の並び
(:class:`RoutePool`)は状態から作り直せる派生の値(再開で引き直す=同じ形・同じ時間)。

逐次ループ宣言(P4):
- :meth:`NavSpace.ensure_routes`: **新しく経路の要る体の数ぶん**の Python のループ(経路の形の探索は numba・同じ
  (出発の点, 行き先, 重み) の組は形のキャッシュで 1 回)。毎刻みの全員のループではない。
- :func:`advance_kernel`: 移動中の体の数ぶんの numba のループ(体ごとに経路の区間の数ぶん)。
- 接続口の割り当て: その刻みに接続口の前に居る体の数ぶん(並べ替え 1 回)。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import numba as nb
import numpy as np

from shibuya.agents.state import Activity
from shibuya.core.rng import derive_key
from shibuya.core.time_consts import SECONDS_PER_MINUTE
from shibuya.engine.geometry import DESIRED_SPEED_MIN_MS, desired_speeds, kladek_speed_factor
from shibuya.world.navmesh import (
    LINK_ELEVATOR,
    LINK_ESCALATOR,
    LINK_KINDS,
    LINK_RAMP,
    LINK_STAIRS,
    NavMesh,
    area_by_cell,
    cell_lookup_table,
    cell_of,
    dem_z,
    load_navmesh,
    navmesh_available,
)
from shibuya.world.navmesh_route import NavPlanner, RouteGeom

__all__ = [
    "SPACE_MODES",
    "DEFAULT_SPACE",
    "SLOPE_MODELS",
    "DEFAULT_SLOPE_MODEL",
    "TURN_WEIGHT_MODES",
    "DEFAULT_TURN_WEIGHT_MODE",
    "TURN_WEIGHT_M",
    "TURN_WEIGHT_PERSON_RANGE_M",
    "CLIMB_WEIGHT_M_PER_M",
    "PIECE_MAX_M",
    "NAV1_EXPEDIENTS",
    "check_space",
    "check_slope_model",
    "check_turn_weight_mode",
    "slope_speed_factor",
    "slope_factor_max",
    "NavSpace",
    "RoutePool",
    "advance_kernel",
    "space_available",
    "is_production_world",
]

#: 切替口の値(``legacy``=今のセルの移動・``nav1``=ナビメッシュの移動の腕)。〔段 1 の再検収 H1・親の判断〕段 1 は既定 legacy の
#: 腕として着地する(nav1 は抽出のランの密度の詰まり=H1 を段 5-1b で直し、確かめてから小さな版上げで既定にする=§0-6)。
SPACE_MODES: Final[tuple[str, ...]] = ("legacy", "nav1")
DEFAULT_SPACE: Final[str] = "legacy"
#: 坂の速さの式(SR12 (d): Wood 2023 の舗装路を既定・Tobler を腕)。
SLOPE_MODELS: Final[tuple[str, ...]] = ("wood", "tobler")
DEFAULT_SLOPE_MODEL: Final[str] = "wood"
#: 曲がる重み(SR12 (a): 既定 50 m・腕 person=人ごとに 32〜62 m の一様)。
TURN_WEIGHT_MODES: Final[tuple[str, ...]] = ("fixed", "person")
DEFAULT_TURN_WEIGHT_MODE: Final[str] = "fixed"
#: 曲がる 1 回の重み[m](R-61 §3 のフロア 32〜62 m の中ほど・指示書 10-06 SR12 (a))。
TURN_WEIGHT_M: Final[float] = 50.0
#: 人ごとの曲がる重みの幅[m](R-61 結論 2 の都市の間の幅・SR12 の腕)。
TURN_WEIGHT_PERSON_RANGE_M: Final[tuple[float, float]] = (32.0, 62.0)
#: 上り 1 m の重み[m](R-61 §3 の坂 1 m = 3.8 m・SR12 (a))。
CLIMB_WEIGHT_M_PER_M: Final[float] = 3.8
#: 人ごとの曲がる重みを引く決定論のドメイン。
TURN_WEIGHT_DOMAIN: Final[str] = "space.nav1.turn_weight"
#: 歩く区間を切る長さ[m](DEM の 2 m 格子に対して坂を拾う細かさ)。
PIECE_MAX_M: Final[float] = 5.0
#: 勾配をならす基線[m](経路に沿って前後 10 m の標高の差=DEM の壁・のり面の 2 m のとがりを拾わない)。5 m の基線では
#: 長さの 1.5% が勾配 20% 超で時間を 33% 延ばした(記録 sp1 §2-3)=つなぎ(NAV1_EXPEDIENTS の 6)。
SLOPE_BASELINE_M: Final[float] = 20.0

#: Wood ら 2023 の舗装路の係数(v = exp(a + bφ + cθ + dθ²) km/h・φ=|θ|・θ=歩く向きの勾配の角[度]・R-63 §1-2)。
WOOD_PAVED: Final[tuple[float, float, float, float]] = (1.580, -0.00389, -0.00726, -0.00218)
#: Tobler(W = 6 exp(−3.5 |S + 0.05|) km/h・S=勾配・R-63 §1-1=式は二次)。
TOBLER: Final[tuple[float, float, float]] = (6.0, 3.5, 0.05)
#: 階段の水平の速さ[m/s](Fujiyama & Tyler 2004 表 3 の階段 4=24.6°・ふつう・若年=R-63 §2-1)と、その表の平地の速さ。
STAIRS_ANGLE_DEG: Final[float] = 24.6
STAIRS_H_SPEED_UP_MS: Final[float] = 0.76
STAIRS_H_SPEED_DOWN_MS: Final[float] = 0.87
STAIRS_FLAT_REF_MS: Final[float] = 1.40
#: エスカレーターの段の速さ[m/s](30 m/分)と勾配[度](施行令の上限 30°・R-64 §1-3)。
ESCALATOR_SPEED_MS: Final[float] = 0.5
ESCALATOR_ANGLE_DEG: Final[float] = 30.0
#: エレベーターのかごの速さ[m/s](45 m/分=仮・駅の実測は空欄=R-64 §1-7)。
ELEVATOR_SPEED_MS: Final[float] = 0.75
#: スロープの勾配の上限(Wood の式の外=大きな角で速さが 0 に落ちるのを防ぐ・構築は 1/8 を超えると階段にする)。
RAMP_GRADE_CLIP: Final[float] = 0.125
#: 経路の重みの基準の速さ[m/s](接続口の時間を距離に直す=Weidmann の自由速度・engine.geometry.SPEED_REFERENCE_MS と同じ)。
WEIGHT_REFERENCE_MS: Final[float] = 1.34

#: つなぎの台帳の行(``docs/design/bridging-ledger.json``・外す段つき)。
NAV1_EXPEDIENTS: Final[tuple[str, ...]] = (
    "経路の選びは既定の重み(曲がる 1 回 50 m・上り 1 m 3.8 m・SR12 (a))で引く=本人の判断ではない(外す段: 段 3 と判断モデルの回"
    "=NavPlanner.candidates の 3 つの候補を本人が選ぶ)",
    "移動は衝突なし(人と人はぶつからない・混み具合は前の刻みのセルの人数で Kladek の減速だけ)(外す段: 5-5 の物理=D 層)",
    "接続口の階段は高さ ÷ 上下の速さ(24.6° の階段のふつうの速さ × 本人の速さ ÷ 1.40)・水平の長さのうち段の水平の分を超える"
    "残りは平らに歩く・エレベーターのかごの速さ 0.75 m/s(仮)・容量を超えた分は先着順で前で待つ・階段と ES と EV の中に居る間は"
    "入口の端(所要時間の半分まで)か出口の端に居る=半分で跳ぶ(外す段: 5-5 の物理と縦の照合=SR17)",
    "新しい行動を選んだ体はその場に止まり、node は面の上の点に最も近い W1 の節にする(建物の中は段 2 まで入口の点=節の点)"
    "(外す段: 5-2 の場所の表と建物の中)",
    "合成の世界(build_manifest.json の build_hash を持たない世界)で nav1 を頼んだランは今のセルの移動で回し、manifest の "
    "space.effective に legacy と書く(本番の世界で資産が無ければ止める)(外す段: 次の版上げ=legacy の切替口を消すとき)",
    "坂の勾配は経路に沿った前後 10 m(基線 20 m)の DEM の標高の差でならす(DEM の 2 m の壁・のり面のとがりを拾わない・"
    "外す段: 点群の床の高さ=SR1 の承認の後)",
    "回廊(W1 の道筋から 40 m)の中で着けない経路は全面の A*(広い探索)に落ちる=そのときは曲がる重みが効かない(1 日の新しい"
    "経路の約 1 割)(外す段: 回廊の幅の感度=5,000 体のスクリーニングの後)",
    "密度(人/m²)の分母はナビメッシュのセルの歩ける面積 × 抽出の割合(体の数 ÷ 母集団の総数=経済の population_scale と同じ値・"
    "全数のランと合成の世界は 1)=体 1 つが 1/割合 の人を代表する・分子=面の上に居て建物の中でない体だけ(在店・並び・購入・就寝と、"
    "経路の外で入口の点に立ち止まった体は数えない=建物の中は段 2・駅の中は段 4 まで入口の点)・あたりで節に着いて立ち止まった体も"
    "建物の中に数える=通りの混み具合を少なめに数える向き(L8)・Fruin の段の境と Kladek の式は変えない(外す段: 全数=39 万体の"
    "ラン・抽出のランの詰まり H1 は段 5-1b)",
)


def check_space(value: str) -> str:
    text = str(value)
    if text not in SPACE_MODES:
        raise ValueError(f"space は {SPACE_MODES} のどれか(いま {value!r})")
    return text


def check_slope_model(value: str) -> str:
    text = str(value)
    if text not in SLOPE_MODELS:
        raise ValueError(f"slope は {SLOPE_MODELS} のどれか(いま {value!r})")
    return text


def check_turn_weight_mode(value: str) -> str:
    text = str(value)
    if text not in TURN_WEIGHT_MODES:
        raise ValueError(f"turn_weight は {TURN_WEIGHT_MODES} のどれか(いま {value!r})")
    return text


def space_available(world_dir: Any) -> bool:
    """この世界の置き場で nav1 が回せるか(ナビメッシュの資産が全部ある)。"""
    return navmesh_available(world_dir)


def is_production_world(world_dir: Any) -> bool:
    """本番の世界か(``build_manifest.json`` に ``build_hash`` を持つ世界=構築の段で組んだ世界・〔段 1 の検収 問い 4〕)。"""
    if world_dir is None:
        return False
    p = Path(world_dir) / "build_manifest.json"
    if not p.exists():
        return False
    try:
        import json

        return bool(json.loads(p.read_text(encoding="utf-8")).get("build_hash"))
    except (OSError, ValueError):
        return False


def slope_speed_factor(model: str, grade) -> np.ndarray:
    """勾配(上り正)→ 平地に対する歩く速さの比(Wood 2023 舗装路 / Tobler)。

    >>> round(float(slope_speed_factor("wood", 0.0)), 6)
    1.0
    >>> float(slope_speed_factor("tobler", 0.0)) == 1.0
    True
    """
    g = np.asarray(grade, dtype=np.float64)
    if model == "wood":
        _a, b, c, d = WOOD_PAVED
        th = np.degrees(np.arctan(g))
        return np.exp(b * np.abs(th) + c * th + d * th * th)
    w0, k, s0 = TOBLER
    return np.exp(-k * np.abs(g + s0)) / math.exp(-k * s0)


def slope_factor_max(model: str) -> float:
    """坂の係数の最大(下りのゆるい坂で平地より速い=受入の試験の速さの上限に掛ける)。"""
    if model == "wood":
        _a, b, c, d = WOOD_PAVED
        th = np.linspace(-20.0, 20.0, 400001)
        return float(np.exp(b * np.abs(th) + c * th + d * th * th).max())
    return float(1.0 / math.exp(-TOBLER[1] * TOBLER[2]))


def turn_weights(mode: str, seed: int | str, n_agents: int) -> np.ndarray:
    """体ごとの曲がる重み[m](fixed=50 m・person=32〜62 m の一様=母集団の seed と体の番号だけの決定論・ランの乱数列を引かない)。"""
    if mode == "fixed":
        return np.full(int(n_agents), TURN_WEIGHT_M, dtype=np.float64)
    k0, _ = derive_key(seed, TURN_WEIGHT_DOMAIN)
    ids = np.arange(int(n_agents), dtype=np.uint64)
    v = ids ^ np.uint64(k0 & ((1 << 64) - 1))
    with np.errstate(over="ignore"):
        v ^= v >> np.uint64(33)
        v *= np.uint64(0xFF51AFD7ED558CCD)
        v ^= v >> np.uint64(33)
        v *= np.uint64(0xC4CEB9FE1A85EC53)
        v ^= v >> np.uint64(33)
    u = (v >> np.uint64(11)).astype(np.float64) / float(1 << 53)
    lo, hi = TURN_WEIGHT_PERSON_RANGE_M
    return lo + (hi - lo) * u


# ====================================================================== 経路の置き場(派生の値)
class RoutePool:
    """体ごとの経路の点の並び(点・階・その点までの時間・区間の接続口・通った W1 の節)。状態ではない(作り直せる)。"""

    def __init__(self, n_agents: int, cap: int = 1 << 16) -> None:
        self.x = np.zeros(cap)
        self.y = np.zeros(cap)
        self.fi = np.zeros(cap, dtype=np.int8)
        self.t = np.zeros(cap)
        self.link = np.full(cap, -1, dtype=np.int32)
        self.ldir = np.zeros(cap, dtype=np.int8)
        self.node = np.full(cap, -1, dtype=np.int32)
        self.size = 0
        self.r_start = np.full(int(n_agents), -1, dtype=np.int64)
        self.r_len = np.zeros(int(n_agents), dtype=np.int64)
        self.live = 0

    def _grow(self, need: int) -> None:
        cap = self.x.size
        if self.size + need <= cap:
            return
        if self.size - self.live > self.live and self.size + need - (self.size - self.live) <= cap:
            self.compact()
            if self.size + need <= cap:
                return
        new = max(cap * 2, self.size + need)
        for name in ("x", "y", "fi", "t", "link", "ldir", "node"):
            a = getattr(self, name)
            b = np.zeros(new, dtype=a.dtype) if name not in ("link", "node") else np.full(new, -1, dtype=a.dtype)
            b[: self.size] = a[: self.size]
            setattr(self, name, b)

    def compact(self) -> None:
        """使っている経路だけを前に詰める(結果は変わらない=置き場だけ)。"""
        order = np.flatnonzero(self.r_start >= 0)
        pos = 0
        for name in ("x", "y", "fi", "t", "link", "ldir", "node"):
            setattr(self, "_tmp_" + name, getattr(self, name).copy())
        for a in order:  # 逐次ループ宣言: 経路を持つ体の数ぶん(置き場が半分を超えて空いたときだけ)
            s, n = int(self.r_start[a]), int(self.r_len[a])
            for name in ("x", "y", "fi", "t", "link", "ldir", "node"):
                getattr(self, name)[pos:pos + n] = getattr(self, "_tmp_" + name)[s:s + n]
            self.r_start[a] = pos
            pos += n
        for name in ("x", "y", "fi", "t", "link", "ldir", "node"):
            delattr(self, "_tmp_" + name)
        self.size = pos

    def put(self, agent: int, x, y, fi, t, link, ldir, node) -> None:
        n = int(np.asarray(x).size)
        self.drop(agent)
        self._grow(n)
        s = self.size
        self.x[s:s + n] = x
        self.y[s:s + n] = y
        self.fi[s:s + n] = fi
        self.t[s:s + n] = t
        self.link[s:s + n] = link
        self.ldir[s:s + n] = ldir
        self.node[s:s + n] = node
        self.r_start[agent] = s
        self.r_len[agent] = n
        self.size += n
        self.live += n

    def drop(self, agent: int) -> None:
        if self.r_start[agent] >= 0:
            self.live -= int(self.r_len[agent])
        self.r_start[agent] = -1
        self.r_len[agent] = 0

    def has(self, agent) -> np.ndarray:
        return self.r_start[np.asarray(agent, dtype=np.int64)] >= 0


# ====================================================================== numba の部品
@nb.njit(cache=True)
def _pieces(px, py, pfi, seg_link, floor_code, dem, dox, doy, dres, piece_max):
    """経路の点 → 5 m 以下に切った点(歩く区間だけ切る)と、区間ごとの水平の長さ・勾配。"""
    k = px.shape[0]
    cnt = 1
    for s in range(k - 1):
        if seg_link[s] >= 0:
            cnt += 1
        else:
            L = math.sqrt((px[s + 1] - px[s]) ** 2 + (py[s + 1] - py[s]) ** 2)
            cnt += max(1, int(math.ceil(L / piece_max)))
    ox = np.empty(cnt)
    oy = np.empty(cnt)
    ofi = np.empty(cnt, dtype=np.int8)
    olink = np.full(cnt, -1, dtype=np.int32)
    ograde = np.zeros(cnt)
    olen = np.zeros(cnt)
    src_v = np.full(cnt, -1, dtype=np.int64)
    q = 0
    ox[0] = px[0]
    oy[0] = py[0]
    ofi[0] = pfi[0]
    src_v[0] = 0
    for s in range(k - 1):
        if seg_link[s] >= 0:
            olink[q] = seg_link[s]
            olen[q] = math.sqrt((px[s + 1] - px[s]) ** 2 + (py[s + 1] - py[s]) ** 2)
            q += 1
            ox[q] = px[s + 1]
            oy[q] = py[s + 1]
            ofi[q] = pfi[s + 1]
            src_v[q] = s + 1
            continue
        L = math.sqrt((px[s + 1] - px[s]) ** 2 + (py[s + 1] - py[s]) ** 2)
        m = max(1, int(math.ceil(L / piece_max)))
        ground = floor_code[pfi[s]] == 0
        for t in range(1, m + 1):
            x0 = ox[q]
            y0 = oy[q]
            x1 = px[s] + (px[s + 1] - px[s]) * t / m
            y1 = py[s] + (py[s + 1] - py[s]) * t / m
            d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            olen[q] = d
            if ground and d > 1e-9:
                z0 = dem_z(dem, dox, doy, dres, x0, y0)
                z1 = dem_z(dem, dox, doy, dres, x1, y1)
                ograde[q] = (z1 - z0) / d
            q += 1
            ox[q] = x1
            oy[q] = y1
            ofi[q] = pfi[s + 1]
            src_v[q] = s + 1 if t == m else -1
    return ox[: q + 1], oy[: q + 1], ofi[: q + 1], olink[: q + 1], ograde[: q + 1], olen[: q + 1], src_v[: q + 1]


@nb.njit(cache=True)
def advance_kernel(t_in, r_start, r_len, px, py, pfi, pt, plink, pnode, factor, wall_in, admitted, link_is_ramp,
                   out_t, out_x, out_y, out_fi, out_node, out_arrived, out_req, out_wall, out_walked, out_links):
    """移動中の体を 1 刻みぶん進める(体ごとに経路の区間を進む・接続口の前で許しが無ければ止まる)。

    ``out_req``=許しを待つ接続口(-1=無い)・``out_node``=この刻みに通った最後の W1 の節(-1=無い)・
    ``out_walked``=歩いた長さ[m]・``out_links``=通り抜けた接続口の数。
    """
    eps = 1e-9
    for q in range(t_in.shape[0]):
        s = r_start[q]
        n = r_len[q]
        t = t_in[q]
        wall = wall_in[q]
        f = factor[q]
        node_passed = -1
        arrived = False
        req = -1
        walked = 0.0
        nlinks = 0
        # 区間 k(pt[s+k] <= t の最後)
        lo = 0
        hi = n - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if pt[s + mid] <= t + eps:
                lo = mid
            else:
                hi = mid - 1
        k = lo
        adm = admitted[q]
        while True:
            if k >= n - 1:
                arrived = True
                t = pt[s + n - 1]
                break
            L = plink[s + k]
            t0 = pt[s + k]
            t1 = pt[s + k + 1]
            seg = t1 - t0
            dx = px[s + k + 1] - px[s + k]
            dy = py[s + k + 1] - py[s + k]
            dist = math.sqrt(dx * dx + dy * dy)
            if L < 0:
                if f <= 0.0:
                    break
                rem = t1 - t
                avail = wall * f
                if avail >= rem - eps:
                    if seg > 0:
                        walked += dist * rem / seg
                    t = t1
                    wall -= rem / f
                    k += 1
                    if pnode[s + k] >= 0:
                        node_passed = pnode[s + k]
                else:
                    if seg > 0:
                        walked += dist * avail / seg
                    t += avail
                    wall = 0.0
                    break
            else:
                at_entrance = t <= t0 + eps
                if at_entrance and adm != L:
                    req = L
                    break
                rem = t1 - t
                if wall >= rem - eps:
                    t = t1
                    wall -= rem
                    k += 1
                    nlinks += 1
                    adm = -1
                    if pnode[s + k] >= 0:
                        node_passed = pnode[s + k]
                else:
                    t += max(wall, 1e-3) if at_entrance else wall
                    wall = 0.0
                    adm = -1
                    break
            if wall <= eps:
                break
        # 位置
        if k >= n - 1:
            out_x[q] = px[s + n - 1]
            out_y[q] = py[s + n - 1]
            out_fi[q] = pfi[s + n - 1]
        else:
            t0 = pt[s + k]
            t1 = pt[s + k + 1]
            fr = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            if fr < 0.0:
                fr = 0.0
            elif fr > 1.0:
                fr = 1.0
            if plink[s + k] >= 0 and link_is_ramp[plink[s + k]] == 0:
                # 階段・ES・EV の中: 位置は入口の端(半分まで)か出口の端(半分から)=面の上の点(跳びは宣言 BR-NAV1-E3)
                j = s + k if fr < 0.5 else s + k + 1
                out_x[q] = px[j]
                out_y[q] = py[j]
                out_fi[q] = pfi[j]
            elif plink[s + k] >= 0:
                # 〔段 1 の検収 L3〕スロープの中: 両端を結ぶ線の上を時間の割合で進む(1 刻みの動きは速さ × 刻みの長さの中)・
                # 階は半分まで入口・半分から出口
                out_x[q] = px[s + k] + fr * (px[s + k + 1] - px[s + k])
                out_y[q] = py[s + k] + fr * (py[s + k + 1] - py[s + k])
                out_fi[q] = pfi[s + k] if fr < 0.5 else pfi[s + k + 1]
            else:
                out_x[q] = px[s + k] + fr * (px[s + k + 1] - px[s + k])
                out_y[q] = py[s + k] + fr * (py[s + k + 1] - py[s + k])
                out_fi[q] = pfi[s + k]
        out_t[q] = t
        out_node[q] = node_passed
        out_arrived[q] = arrived
        out_req[q] = req
        out_wall[q] = wall
        out_walked[q] = walked
        out_links[q] = nlinks


@nb.njit(cache=True)
def _dem_many(dem, dox, doy, dres, xs, ys):
    out = np.empty(xs.shape[0])
    for q in range(xs.shape[0]):
        out[q] = dem_z(dem, dox, doy, dres, xs[q], ys[q])
    return out


@nb.njit(cache=True)
def _cells_of(lut, cx0, cy0, cell_m, xs, ys, fis, floor_band, out):
    for q in range(xs.shape[0]):
        f = fis[q]
        if f < 0:
            out[q] = -1
        else:
            out[q] = cell_of(lut, cx0, cy0, cell_m, xs[q], ys[q], floor_band[f])


# ====================================================================== 計器
@dataclass
class NavMeter:
    """移動の計器(ランの通算・manifest の ``space`` と記録の材料)。"""

    routes_planned: int = 0
    routes_from_cache: int = 0
    routes_corridor: int = 0
    routes_wide: int = 0
    routes_failed: int = 0
    replans_on_resume: int = 0
    expanded_total: int = 0
    trips_arrived: int = 0
    walked_m: float = 0.0
    trip_time_s_sum: float = 0.0
    trip_len_m_sum: float = 0.0
    link_traversals: int = 0
    link_traversals_by_kind: dict = field(default_factory=lambda: {k: 0 for k in LINK_KINDS})
    link_wait_agent_steps: int = 0
    link_admitted: int = 0
    stops_mid_route: int = 0
    placed_at_anchor: int = 0
    slope_time_s_sum: float = 0.0
    flat_time_s_sum: float = 0.0
    jammed_agent_steps: int = 0

    def as_dict(self) -> dict[str, Any]:
        d = dict(self.__dict__)
        d["link_traversals_by_kind"] = dict(self.link_traversals_by_kind)
        return d


# ====================================================================== 本体
class NavSpace:
    """段 1 の移動の道具(1 つのランで 1 つ)。書き込みはしない=新しい値を返し、書くのは ``engine.resolve``。"""

    is_nav = True

    def __init__(self, mesh: NavMesh, assets: Any, *, world_dir: Any, seed: int | str, n_agents: int,
                 tick_seconds: int, population_seed: int | str | None = None,
                 slope_model: str = DEFAULT_SLOPE_MODEL, turn_weight_mode: str = DEFAULT_TURN_WEIGHT_MODE,
                 population_scale: float = 1.0) -> None:
        self.mesh = mesh
        self.assets = assets
        self.n_agents = int(n_agents)
        self.tick_seconds = int(tick_seconds)
        #: 〔段 1 の検収 M4〕抽出の割合(体の数 ÷ 母集団の総数・経済の population_scale と同じ値・全数のランと合成の世界は 1)。
        #: 人/m² の分母は「ナビメッシュの面積 × 抽出の割合」(体 1 つが 1/割合 の人を代表する=つなぎ BR-NAV1-DENSITY-SAMPLE-SCALE)
        self.population_scale = float(population_scale) if population_scale and population_scale > 0 else 1.0
        self.slope_model = check_slope_model(slope_model)
        self.turn_weight_mode = check_turn_weight_mode(turn_weight_mode)
        self.v_desired = desired_speeds(seed if population_seed is None else population_seed,
                                        np.arange(self.n_agents, dtype=np.int64))
        # 人ごとの曲がる重みは体の属性=母集団の seed から(希望歩行速度と同じ・10f K21 (a))
        self.turn_w = turn_weights(self.turn_weight_mode, seed if population_seed is None else population_seed,
                                   self.n_agents)
        self.climb_w = CLIMB_WEIGHT_M_PER_M
        self.factor_max = slope_factor_max(self.slope_model)
        # セルの写し
        # 〔段 1 の検収 M3〕セルの無い升(つなぎの帯だけが通る)は最も近い W2 のセルへ倒す
        self.lut, self.cx0, self.cy0 = cell_lookup_table(assets.cell_ix, assets.cell_iy, assets.cell_band,
                                                         fill_nearest=True)
        self.cell_band = np.asarray(assets.cell_band, dtype=np.int8)
        area = area_by_cell(self.lut, self.cx0, self.cy0, 100.0, mesh.run_floor, mesh.run_row, mesh.run_x0,
                            mesh.run_x1, mesh.floor_band, mesh.floor_ox, mesh.floor_oy, mesh.res, int(assets.n_cells))
        self.walkable_area_m2 = np.maximum(area, 1.0)
        self.walkable_area_raw_m2 = area
        #: 密度の分母[m²](物理の面積 × 抽出の割合)
        self.density_area_m2 = self.walkable_area_m2 * self.population_scale
        # 接続口の時間(基準の速さ)と重み
        self.link_t_ab, self.link_t_ba = self.link_times(np.full(mesh.n_links, WEIGHT_REFERENCE_MS))
        rise = np.asarray(mesh.link_rise_m, dtype=np.float64)
        lc_ab = self.link_t_ab * WEIGHT_REFERENCE_MS + self.climb_w * np.maximum(rise, 0.0)
        lc_ba = self.link_t_ba * WEIGHT_REFERENCE_MS + self.climb_w * np.maximum(-rise, 0.0)
        geom = None
        if world_dir is not None and (Path(world_dir) / "w1_edge_geometry.npz").exists():
            g = np.load(Path(world_dir) / "w1_edge_geometry.npz")
            geom = (g["coords"], g["offsets"])
        self.planner = NavPlanner(mesh, assets.node_xy, assets.edge_u, assets.edge_v, assets.edge_len_m, geom,
                                  lc_ab, lc_ba)
        self.pool = RoutePool(self.n_agents)
        self._shape_cache: dict[tuple, RouteGeom | None] = {}
        self._shape_cache_cap = 50_000
        self.nav_meter = NavMeter()
        self.cap_step = np.where(np.asarray(mesh.link_cap_per_min) > 0,
                                 np.maximum(1, np.floor(np.asarray(mesh.link_cap_per_min, dtype=np.float64)
                                                        * self.tick_seconds / float(SECONDS_PER_MINUTE))), 0).astype(np.int64)
        self.link_kind = np.asarray(mesh.link_kind, dtype=np.int64)
        self.link_is_ramp = (self.link_kind == LINK_RAMP).astype(np.uint8)
        # 〔段 1 の検収 L3〕スロープの中は両端を結ぶ線の上を進む。ただし線が W2 のセルの無い升を通るスロープは端の点(跳び)のまま
        # (面の上の体のセルを -1 にしない=M3)
        self.ramp_lines_outside_cells = 0
        for L in np.flatnonzero(self.link_is_ramp).tolist():  # 逐次ループ宣言: スロープの数ぶん(組み立ての 1 回)
            xs = mesh.link_ax[L] + np.linspace(0.0, 1.0, 64) * (mesh.link_bx[L] - mesh.link_ax[L])
            ys = mesh.link_ay[L] + np.linspace(0.0, 1.0, 64) * (mesh.link_by[L] - mesh.link_ay[L])
            for fi in (int(mesh.link_afi[L]), int(mesh.link_bfi[L])):
                c, _b = self.cells(xs, ys, np.full(xs.size, fi))
                if (c < 0).any():
                    self.link_is_ramp[L] = 0
                # 〔段 1 の再検収 L9〕線の上から面の最も近い点までが、最も遅い体の 1 刻みの上限(DESIRED_SPEED_MIN_MS × 刻み)を
                # 超えうるスロープも端の点(止まった体の寄せが速さの上限を超えない=式でなく引いて確かめる)
                far = max(mesh.nearest(fi, float(x), float(y), 1.0e4)[3] for x, y in zip(xs, ys))
                if far > DESIRED_SPEED_MIN_MS * self.tick_seconds:
                    self.link_is_ramp[L] = 0
            self.ramp_lines_outside_cells += int(self.link_is_ramp[L] == 0)
        #: 受入の試験の材料(刻みごとの位置の変化の検査を呼び手がするための控え・既定は控えない)
        self.trace: list[dict[str, np.ndarray]] | None = None

    # ------------------------------------------------------------------ 接続口
    def link_times(self, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """接続口ごとの所要時間[s](a→b・b→a)。``v``=接続口ごとの歩く速さ[m/s](人の速さ)。"""
        m = self.mesh
        kind = np.asarray(m.link_kind, dtype=np.int64)
        h = np.asarray(m.link_rise_m, dtype=np.float64)
        L = np.maximum(np.asarray(m.link_len_m, dtype=np.float64), 0.1)
        v = np.asarray(v, dtype=np.float64)
        tan_s = math.tan(math.radians(STAIRS_ANGLE_DEG))
        ratio = v / STAIRS_FLAT_REF_MS
        up = np.abs(h) / (STAIRS_H_SPEED_UP_MS * tan_s * ratio)
        down = np.abs(h) / (STAIRS_H_SPEED_DOWN_MS * tan_s * ratio)
        # 接続口の水平の長さのうち、段(傾き)の水平の分を超える残りは平らに歩く(両端が離れた接続口で水平に速く動かない)
        flat_st = np.maximum(L - np.abs(h) / tan_s, 0.0) / v
        tan_e = math.tan(math.radians(ESCALATOR_ANGLE_DEG))
        flat_es = np.maximum(L - np.abs(h) / tan_e, 0.0) / v
        st_ab = np.where(h >= 0, up, down) + flat_st
        st_ba = np.where(h >= 0, down, up) + flat_st
        esc = np.abs(h) / math.sin(math.radians(ESCALATOR_ANGLE_DEG)) / ESCALATOR_SPEED_MS + flat_es
        ev = np.abs(h) / ELEVATOR_SPEED_MS + np.asarray(m.link_wait_s, dtype=np.float64) + L / v
        g = np.clip(h / L, -RAMP_GRADE_CLIP, RAMP_GRADE_CLIP)
        ramp_ab = L / (v * slope_speed_factor(self.slope_model, g))
        ramp_ba = L / (v * slope_speed_factor(self.slope_model, -g))
        t_ab = np.select([kind == LINK_STAIRS, kind == LINK_ESCALATOR, kind == LINK_ELEVATOR], [st_ab, esc, ev],
                         ramp_ab)
        t_ba = np.select([kind == LINK_STAIRS, kind == LINK_ESCALATOR, kind == LINK_ELEVATOR], [st_ba, esc, ev],
                         ramp_ba)
        return np.maximum(t_ab, 1.0), np.maximum(t_ba, 1.0)

    # ------------------------------------------------------------------ 位置 → セル
    def cells(self, x, y, fi) -> tuple[np.ndarray, np.ndarray]:
        x = np.ascontiguousarray(x, dtype=np.float64)
        y = np.ascontiguousarray(y, dtype=np.float64)
        f = np.ascontiguousarray(fi, dtype=np.int64)
        out = np.empty(x.size, dtype=np.int64)
        _cells_of(self.lut, self.cx0, self.cy0, 100.0, x, y, f, self.mesh.floor_band, out)
        band = np.where(out >= 0, self.cell_band[np.maximum(out, 0)], 0).astype(np.int8)
        return out.astype(np.int32), band

    def anchor_of(self, node) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        nd = np.asarray(node, dtype=np.int64)
        ok = (nd >= 0) & (nd < self.mesh.anchor_x.size)
        safe = np.where(ok, nd, 0)
        x = np.where(ok, self.mesh.anchor_x[safe], np.nan)
        y = np.where(ok, self.mesh.anchor_y[safe], np.nan)
        f = np.where(ok, self.mesh.anchor_fi[safe], -1).astype(np.int8)
        return x, y, f

    def onto_surface(self, x, y, fi) -> tuple[np.ndarray, np.ndarray]:
        """面の外の点(スロープの中で止まった体=〔段 1 の検収 L3〕線の上)→ 同じ階の面の最も近い点(面の上の点はそのまま)。
        逐次ループ宣言: 呼び手が渡す体の数ぶん(止まった体だけ)。"""
        xs = np.asarray(x, dtype=np.float64).copy()
        ys = np.asarray(y, dtype=np.float64).copy()
        m = self.mesh
        for q, ff in enumerate(np.asarray(fi).tolist()):
            if ff < 0 or m.locate(int(ff), xs[q], ys[q]) >= 0:
                continue
            r, px, py, _d = m.nearest(int(ff), xs[q], ys[q], 1.0e4)
            if r >= 0:
                xs[q], ys[q] = px, py
        return xs, ys

    def nearest_nodes(self, x, y, fi) -> np.ndarray:
        """面の上の点 → 同じ階の最も近い W1 の節(逐次ループ宣言: 呼び手が渡す体の数ぶん・止まった体だけ)。"""
        out = np.empty(np.asarray(x).size, dtype=np.int32)
        for q, (xx, yy, ff) in enumerate(zip(np.asarray(x), np.asarray(y), np.asarray(fi))):
            out[q] = self.planner.nearest_node(float(xx), float(yy), int(ff))
        return out

    # ------------------------------------------------------------------ 経路
    def _shape(self, ox: float, oy: float, ofi: int, target: int, turn_w: float) -> RouteGeom | None:
        key = (np.float32(ox).tobytes(), np.float32(oy).tobytes(), int(ofi), int(target),
               np.float64(turn_w).tobytes())
        if key in self._shape_cache:
            self.nav_meter.routes_from_cache += 1
            return self._shape_cache[key]
        r = self.planner.plan(float(np.float32(ox)), float(np.float32(oy)), int(ofi), int(target),
                              turn_w=float(turn_w), climb_w=self.climb_w)
        self.nav_meter.routes_planned += 1
        if r is None:
            self.nav_meter.routes_failed += 1
        else:
            self.nav_meter.expanded_total += int(r.expanded)
            if r.mode == 0:
                self.nav_meter.routes_corridor += 1
            else:
                self.nav_meter.routes_wide += 1
        if len(self._shape_cache) >= self._shape_cache_cap:
            self._shape_cache.pop(next(iter(self._shape_cache)))
        self._shape_cache[key] = r
        return r

    def _timed(self, agent: int, r: RouteGeom) -> None:
        """経路の形 → 体の速さで時間を載せて置き場へ。"""
        m = self.mesh
        px, py, pfi, plink, pgrade, plen, src_v = _pieces(
            np.ascontiguousarray(r.pts[:, 0]), np.ascontiguousarray(r.pts[:, 1]),
            np.ascontiguousarray(r.fi.astype(np.int64)), np.ascontiguousarray(r.seg_link.astype(np.int64)),
            m.floor_code, m.dem_z, m.dem_ox, m.dem_oy, m.dem_res, PIECE_MAX_M)
        v = float(self.v_desired[agent])
        n = px.size
        dt = np.zeros(n)
        walk = plink < 0
        if n > 1:
            seg_walk = walk[:-1]
            fac = slope_speed_factor(self.slope_model, self._smooth_grade(px, py, pfi, plen))
            dt[:-1] = np.where(seg_walk, plen[:-1] / (v * fac), 0.0)
            flat = np.where(seg_walk, plen[:-1] / v, 0.0)
            self.nav_meter.slope_time_s_sum += float(dt[:-1][seg_walk].sum())
            self.nav_meter.flat_time_s_sum += float(flat[seg_walk].sum())
        ldir = np.zeros(n, dtype=np.int8)
        seg_idx = np.flatnonzero(~walk[:-1]) if n > 1 else np.zeros(0, np.int64)
        if seg_idx.size:
            # 区間の向き(r.seg_dir は元の区間の順=接続口の区間だけ取り出して並べる)
            dirs = r.seg_dir[r.seg_link >= 0]
            lk = plink[seg_idx].astype(np.int64)
            ldir[seg_idx] = dirs[: seg_idx.size]
            tab, tba = self.link_times(np.full(m.n_links, v))
            dt[seg_idx] = np.where(dirs[: seg_idx.size] == 0, tab[lk], tba[lk])
        t = np.concatenate([[0.0], np.cumsum(dt[:-1])]) if n > 1 else np.zeros(1)
        node = np.full(n, -1, dtype=np.int32)
        # W1 の節を通った点(元の点の添字 → 切った後の点)
        if r.ck_vertex.size:
            pos = np.full(int(r.pts.shape[0]), -1, dtype=np.int64)
            sv = np.flatnonzero(src_v >= 0)
            pos[src_v[sv]] = sv
            for v_, nd in zip(r.ck_vertex, r.ck_node):
                p = pos[int(v_)] if int(v_) < pos.size else -1
                if p >= 0:
                    node[p] = int(nd)
        self.pool.put(agent, px, py, pfi, t, plink, ldir, node)

    def _smooth_grade(self, px, py, pfi, plen) -> np.ndarray:
        """区間ごとの勾配(地上の歩く区間だけ・前後 SLOPE_BASELINE_M/2 の標高の差 ÷ 経路の長さ)。ほかの階は 0。"""
        m = self.mesh
        n = px.size
        if n < 2:
            return np.zeros(0)
        S = np.concatenate([[0.0], np.cumsum(plen[:-1])])
        z = _dem_many(m.dem_z, m.dem_ox, m.dem_oy, m.dem_res, np.ascontiguousarray(px), np.ascontiguousarray(py))
        mid = 0.5 * (S[:-1] + S[1:])
        h = 0.5 * SLOPE_BASELINE_M
        lo = np.maximum(mid - h, 0.0)
        hi = np.minimum(mid + h, S[-1])
        g = (np.interp(hi, S, z) - np.interp(lo, S, z)) / np.maximum(hi - lo, 1e-9)
        ground = m.floor_code[pfi[:-1].astype(np.int64)] == 0
        return np.where(ground & (hi - lo > 1e-9), g, 0.0)

    def ensure_routes(self, aid, x, y, fi, target, route_tgt, ox, oy, of_):
        """経路の要る体(行き先が変わった・置き場に無い)を見つけて経路を引く。

        返り値: ``(new_origin マスク, ox, oy, of, ok マスク)``=出発の点を今の位置に置き直した体と、経路が引けたか。
        逐次ループ宣言: 経路の要る体の数ぶん(行き先が変わった体+再開で置き場が空の体)。
        """
        aid = np.asarray(aid, dtype=np.int64)
        tgt = np.asarray(target, dtype=np.int64)
        changed = np.asarray(route_tgt, dtype=np.int64) != tgt
        missing = ~self.pool.has(aid)
        need = changed | missing
        nox = np.asarray(ox, dtype=np.float32).copy()
        noy = np.asarray(oy, dtype=np.float32).copy()
        nof = np.asarray(of_, dtype=np.int8).copy()
        nox[changed] = np.asarray(x, dtype=np.float32)[changed]
        noy[changed] = np.asarray(y, dtype=np.float32)[changed]
        nof[changed] = np.asarray(fi, dtype=np.int8)[changed]
        ok = np.ones(aid.size, dtype=bool)
        for q in np.flatnonzero(need):
            a = int(aid[q])
            if not changed[q]:
                self.nav_meter.replans_on_resume += 1
            r = self._shape(float(nox[q]), float(noy[q]), int(nof[q]), int(tgt[q]), float(self.turn_w[a]))
            if r is None:
                ok[q] = False
                self.pool.drop(a)
                continue
            self._timed(a, r)
        return changed, nox, noy, nof, ok

    def surface_counts(self, registry: Any) -> np.ndarray:
        """〔段 1 の検収 M4 (a)〕密度の分子=セルごとの「面の上に居て建物の中でない体」の数。

        建物の中と数える体: 在店(``poi_ref``)・並び(``queue_poi``)・購入・就寝、と、経路の外で入口の点(W1 の節の点)に
        立ち止まった体(建物の中は段 2・駅の中は段 4 まで入口の点=つなぎ BR-NAV1-DENSITY-SAMPLE-SCALE)。域外・車内は数えない。
        """
        r = registry
        n_cells = self.walkable_area_m2.size
        fi = np.asarray(r.nav_fi)
        node = np.asarray(r.node, dtype=np.int64)
        cell = np.asarray(r.cell, dtype=np.int64)
        on = (fi >= 0) & (node >= 0) & (cell >= 0) & (cell < n_cells)
        act = np.asarray(r.activity)
        ax, ay, _af = self.anchor_of(np.where(on, node, -1))
        xy = np.asarray(r.xy, dtype=np.float64)
        at_entrance = (np.asarray(r.nav_tgt) < 0) & (np.abs(xy[:, 0] - ax) <= 1e-3) & (np.abs(xy[:, 1] - ay) <= 1e-3)
        inside = ((np.asarray(r.poi_ref) >= 0) | (np.asarray(r.queue_poi) >= 0) | (act == int(Activity.SHOPPING))
                  | (act == int(Activity.SLEEPING)) | (at_entrance & (act != int(Activity.MOVING))))
        sel = on & ~inside
        return np.bincount(cell[sel], minlength=n_cells).astype(np.float64)

    def kladek_factor(self, cell, density) -> np.ndarray:
        c = np.asarray(cell, dtype=np.int64)
        d = np.asarray(density, dtype=np.float64)
        fac_cell = kladek_speed_factor(d / self.density_area_m2)
        return np.where((c >= 0) & (c < fac_cell.size), fac_cell[np.clip(c, 0, max(fac_cell.size - 1, 0))], 1.0)

    def density_stage(self, density) -> np.ndarray:
        from shibuya.world.state import DENSITY_STAGE_EDGES_PER_M2

        per_m2 = np.asarray(density, dtype=np.float64) / self.density_area_m2
        return np.searchsorted(np.asarray(DENSITY_STAGE_EDGES_PER_M2), per_m2, side="right").astype(np.uint8)

    def advance(self, aid, t_in, factor, nav_wait, tick: int):
        """移動中の体を 1 刻み進める(接続口の割り当てを含む)。返り値は辞書(t・x・y・fi・node・arrived・wait)。"""
        aid = np.asarray(aid, dtype=np.int64)
        k = aid.size
        rs = self.pool.r_start[aid]
        rl = self.pool.r_len[aid]
        t = np.asarray(t_in, dtype=np.float64).copy()
        wall = np.full(k, float(self.tick_seconds))
        admitted = np.full(k, -1, dtype=np.int64)
        fac = np.asarray(factor, dtype=np.float64)
        out = {n: np.zeros(k) for n in ("t", "x", "y", "wall", "walked")}
        out["fi"] = np.zeros(k, dtype=np.int64)
        out["node"] = np.full(k, -1, dtype=np.int64)
        out["arrived"] = np.zeros(k, dtype=np.bool_)
        out["req"] = np.full(k, -1, dtype=np.int64)
        out["links"] = np.zeros(k, dtype=np.int64)
        wait = np.asarray(nav_wait, dtype=np.int64).copy()
        used = np.zeros(self.mesh.n_links, dtype=np.int64)
        active = np.arange(k)
        node_last = np.full(k, -1, dtype=np.int64)
        walked = np.zeros(k)
        links = np.zeros(k, dtype=np.int64)
        for _pass in range(4):
            if active.size == 0:
                break
            ot = np.zeros(active.size); ox = np.zeros(active.size); oy = np.zeros(active.size)
            ofi = np.zeros(active.size, dtype=np.int64); onode = np.full(active.size, -1, dtype=np.int64)
            oarr = np.zeros(active.size, dtype=np.bool_); oreq = np.full(active.size, -1, dtype=np.int64)
            owall = np.zeros(active.size); owalk = np.zeros(active.size); olinks = np.zeros(active.size, np.int64)
            p = self.pool
            advance_kernel(t[active], rs[active], rl[active], p.x, p.y, p.fi, p.t, p.link, p.node, fac[active],
                           wall[active], admitted[active], self.link_is_ramp, ot, ox, oy, ofi, onode, oarr, oreq,
                           owall, owalk, olinks)
            t[active] = ot
            wall[active] = owall
            out["x"][active] = ox
            out["y"][active] = oy
            out["fi"][active] = ofi
            out["arrived"][active] = oarr
            out["req"][active] = oreq
            node_last[active] = np.where(onode >= 0, onode, node_last[active])
            walked[active] += owalk
            links[active] += olinks
            req_q = active[oreq >= 0]
            if req_q.size == 0:
                break
            # 割り当て: 接続口ごとに先着順(待ち始めた刻み → 体の番号)
            first = np.where(wait[req_q] >= 0, wait[req_q], int(tick))
            order = np.lexsort((aid[req_q], first, out["req"][req_q]))
            req_q = req_q[order]
            lk = out["req"][req_q]
            grant = np.zeros(req_q.size, dtype=bool)
            for j in range(req_q.size):  # 逐次ループ宣言: 接続口の前に居る体の数ぶん
                L = int(lk[j])
                cap = int(self.cap_step[L])
                if cap == 0 or used[L] < cap:
                    grant[j] = True
                    used[L] += 1
            g = req_q[grant]
            ng = req_q[~grant]
            wait[ng] = np.where(wait[ng] >= 0, wait[ng], int(tick))
            wait[g] = -1
            admitted[:] = -1
            admitted[g] = out["req"][g]
            out["req"][g] = -1
            self.nav_meter.link_admitted += int(g.size)
            active = g
        # 待ちの体(許しが無いまま止まった)の数
        self.nav_meter.link_wait_agent_steps += int(np.count_nonzero(out["req"] >= 0))
        out["t"] = t
        out["node"] = node_last
        out["wait"] = wait
        out["walked"] = walked
        out["links"] = links
        self.nav_meter.walked_m += float(walked.sum())
        self.nav_meter.link_traversals += int(links.sum())
        return out

    def trip_done(self, aid) -> None:
        """着いた体の経路を置き場から外す(時間と長さは計器へ)。"""
        for a in np.asarray(aid, dtype=np.int64):  # 逐次ループ宣言: 着いた体の数ぶん
            s, n = int(self.pool.r_start[a]), int(self.pool.r_len[a])
            if s >= 0 and n > 0:
                self.nav_meter.trips_arrived += 1
                self.nav_meter.trip_time_s_sum += float(self.pool.t[s + n - 1])
                xs = self.pool.x[s:s + n]
                ys = self.pool.y[s:s + n]
                lk = self.pool.link[s:s + n - 1]
                d = np.hypot(np.diff(xs), np.diff(ys))
                self.nav_meter.trip_len_m_sum += float(d[lk < 0].sum())
                for L in lk[lk >= 0]:
                    self.nav_meter.link_traversals_by_kind[LINK_KINDS[int(self.link_kind[int(L)])]] += 1
            self.pool.drop(int(a))

    def drop(self, aid) -> None:
        for a in np.asarray(aid, dtype=np.int64):  # 逐次ループ宣言: 経路を捨てる体の数ぶん
            self.pool.drop(int(a))

    def manifest_fields(self) -> dict[str, Any]:
        m = self.mesh
        return {
            "schema": "shibuya.space.nav1/1",
            "slope_model": self.slope_model,
            "turn_weight_mode": self.turn_weight_mode,
            "turn_weight_m": TURN_WEIGHT_M if self.turn_weight_mode == "fixed" else list(TURN_WEIGHT_PERSON_RANGE_M),
            "climb_weight_m_per_m": self.climb_w,
            "navmesh": {"runs": m.run_count, "strips": m.n_strips, "links": m.n_links, "floors": m.n_floors,
                        "stage_version": str(m.meta.get("stage_version", "")),
                        "density_population_scale": self.population_scale,
                        "ramps_on_end_points": int(self.ramp_lines_outside_cells)},
            "meter": self.nav_meter.as_dict(),
        }


def load_space(world_dir: Any, assets: Any, *, seed, n_agents, tick_seconds, population_seed, slope_model,
               turn_weight_mode, population_scale: float = 1.0) -> NavSpace:
    mesh = load_navmesh(world_dir)
    return NavSpace(mesh, assets, world_dir=world_dir, seed=seed, n_agents=n_agents, tick_seconds=tick_seconds,
                    population_seed=population_seed, slope_model=slope_model, turn_weight_mode=turn_weight_mode,
                    population_scale=population_scale)


# ====================================================================== 腕(環境変数と CLI)・manifest・要約
import os  # noqa: E402

_SLOPE: str = check_slope_model(os.environ.get("SHIBUYA_SLOPE", DEFAULT_SLOPE_MODEL).strip().lower()
                                 or DEFAULT_SLOPE_MODEL)
_TURN: str = check_turn_weight_mode(os.environ.get("SHIBUYA_TURN_WEIGHT", DEFAULT_TURN_WEIGHT_MODE).strip().lower()
                                    or DEFAULT_TURN_WEIGHT_MODE)


def space_env_override(value: str | None) -> str:
    """頼んだ移動の値: 引数(``run_day(space=…)``・``--space``)があればそれ・無ければ環境変数 ``SHIBUYA_SPACE``・それも無ければ
    既定(〔段 1 の検収 L4〕指定は環境変数より強い=坂と曲がる重みの腕と同じ)。"""
    if value is not None and str(value) != "":
        return str(value)
    env = os.environ.get("SHIBUYA_SPACE", "").strip().lower()
    return env if env else DEFAULT_SPACE


def slope_arm() -> str:
    """坂の式の腕(``wood``=既定・``tobler``)。組み立てのときに読む(環境変数 ``SHIBUYA_SLOPE``・``--slope``)。"""
    return _SLOPE


def turn_arm() -> str:
    """曲がる重みの腕(``fixed``=既定 50 m・``person``=人ごとに 32〜62 m)。環境変数 ``SHIBUYA_TURN_WEIGHT``・``--turn-weight``。"""
    return _TURN


def set_slope_arm(name: str) -> None:
    global _SLOPE
    _SLOPE = check_slope_model(name)


def set_turn_arm(name: str) -> None:
    global _TURN
    _TURN = check_turn_weight_mode(name)


def arms_on() -> bool:
    """坂と曲がる重みの腕が既定と違うか(ランの種類を arm にする=結果が変わる腕)。"""
    return _SLOPE != DEFAULT_SLOPE_MODEL or _TURN != DEFAULT_TURN_WEIGHT_MODE


def add_space_args(ap: Any) -> None:
    """CLI の旗 ``--space``・``--slope``・``--turn-weight``。"""
    ap.add_argument("--space", choices=SPACE_MODES, default=None,
                    help="第 5 期 空間の段 1 の移動の切替口。legacy=今のセルの移動(既定)/nav1=ナビメッシュの上を衝突なしで"
                         "進む腕(位置は (x, y, 階)・合成の世界では legacy で回して manifest の space.effective に書く・本番の"
                         "世界で資産 nav1_* が無ければ止める・既知の欠陥 H1=抽出のランの密度の詰まり=段 5-1b)。環境変数 "
                         "SHIBUYA_SPACE より強い")
    ap.add_argument("--slope", choices=SLOPE_MODELS, default=None,
                    help="坂の速さの式の腕(SR12 (d)・既定 wood=Wood 2023 舗装路・tobler=Tobler・環境変数 SHIBUYA_SLOPE と同じ)")
    ap.add_argument("--turn-weight", choices=TURN_WEIGHT_MODES, default=None,
                    help="曲がる重みの腕(SR12 (a)・既定 fixed=50 m・person=人ごとに 32〜62 m の一様・環境変数 "
                         "SHIBUYA_TURN_WEIGHT と同じ)")


def space_from_args(args: Any) -> str | None:
    """CLI の値 → ``run_day(space=…)``。坂と曲がる重みの腕はここで選ぶ(組み立てが読む・指定は環境変数より強い)。"""
    if getattr(args, "slope", None) is not None:
        set_slope_arm(str(args.slope))
    if getattr(args, "turn_weight", None) is not None:
        set_turn_arm(str(args.turn_weight))
    v = getattr(args, "space", None)
    return None if v is None else check_space(str(v))


def manifest_section(requested: str, effective: str, reason: str, layer: Any) -> dict[str, Any]:
    """manifest の ``space``(設定=頼んだ値・実際の値・理由・坂の式・曲がる重み・ナビメッシュの大きさ/観測=計器)。"""
    out: dict[str, Any] = {"requested": str(requested), "effective": str(effective), "reason": str(reason),
                           "schema": None, "slope_model": None, "turn_weight_mode": None, "turn_weight_m": None,
                           "climb_weight_m_per_m": None, "navmesh": None, "expedients": list(NAV1_EXPEDIENTS),
                           "meter": None}
    if layer is not None:
        out.update(layer.manifest_fields())
    return out


def summary_line(layer: Any) -> str:
    if layer is None:
        return "移動 nav1(道具なし)"
    m = layer.nav_meter
    trips = max(1, m.trips_arrived)
    return (f"移動 nav1(坂 {layer.slope_model}・曲がる重み {layer.turn_weight_mode})/経路 {m.routes_planned:,} 本"
            f"(通り道の中 {m.routes_corridor:,}・広げた {m.routes_wide:,}・引けない {m.routes_failed:,})/着いた "
            f"{m.trips_arrived:,} 回・平均 {m.trip_len_m_sum / trips:,.0f} m・{m.trip_time_s_sum / trips:,.0f} s/接続口 "
            f"{m.link_traversals:,} 回・待ち {m.link_wait_agent_steps:,} 体刻み/歩いた {m.walked_m / 1000:,.1f} km")
