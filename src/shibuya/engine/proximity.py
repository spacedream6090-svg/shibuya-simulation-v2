"""engine.proximity — 会話と近接を実距離で判定する切替口(第 2 期 2-2・段 11a)。

正: 実装アジェンダ ``docs/design/v2-proximity-distance-implementation-agenda.md`` §2(段 11a)・末尾の「ユーザー決定
(2026-10-03)」B1〜B8・決定 ``docs/design/v2-wallbounce-decisions-2026-10-03.md`` §4(4-2 気づく確率)。

腕(切替口): ``--proximity {cell,distance}``(環境変数 ``SHIBUYA_PROXIMITY``・:func:`set_arm`)と会話の距離 d の感度の腕
``--proximity-d {1.0,2.0,2.5}``(環境変数 ``SHIBUYA_PROXIMITY_D``・:func:`set_d`)。〔第 2 期 2-4 V2・版上げ 2 回目〕既定は
``distance``(:data:`DEFAULT_MODE`=10-03 §4 の決定どおり・d=2.0 m)。``cell``=2-2 までの判定(同じセル)=層を作らない=
**切替口**(旧値の再現=2-4 の記録 ``docs/bench/analysis/wallbounce-1012/vb24/README.md`` の V2)。腕は組み立てのときに読む
(``run_day`` の引数にしない=設定の指紋に入れない=記憶の器と候補の口の腕と同じ扱い)。腕の名と値は manifest の
``proximity`` と状態のファイルの見出しの ``proximity`` に出る(再開のときに今の腕と違えば止める=組み立て。見出しに無い
状態のファイル=2-4 より前の既定の cell のラン)。

``distance`` の判定(:meth:`ProximityRule.reach`):

- 会話が届く=「舞台の中(セル ≥ 0)・同じ層(``band``)・距離 ≤ d」か「同じ B5 の単位の中」(B5 (a)=空間の段 2 までの
  つなぎ=同じ単位の中なら距離を見ずに会話できる)。B5 の単位=在席の印 ``poi_ref`` があり**その店のセルの中に居る**体
  (:meth:`ProximityRule.units`・親の判断 10-14 の 2=在席の印は歩き出しでは解かれず、店を出て歩いている体にも残るため)。
  同じセルの条件は外す(別セルの 1 m 隣は話せ、同じセルの 3 m は話せない)。層をまたぐ 1 m は話せない(地下・地上・デッキ)。3 次元の実装(階ごとの面)が入ったら階に読み替える。
- 対象: 会話の開始(``resolve._apply_talk``)・返事待ち(``run._settle_pending_invites``)・3 人会話(``systems.talk``)・
  離脱(``ConversationManager.step`` の ``near_fn``=:meth:`ProximityRule.stay`)・招待の相手の候補(``commit`` の名指しと
  フォールバック・``relations.choose_talk_partners``・古典の交際の候補)・偶然の出会い(届く知人)・知人出現の起床
  (``relations._acq_notice``=気づく確率)・同席(``relations.copresent_step``)・B5 近接行(``perception.renderer``)。
- 知人に気づく確率(B4): R-62 の 2 点(10.4 m で 75%・23.5 m で 25%=Loftus & Harley 2005)を通るロジスティック
  p(d) = 1 / (1 + exp((d − 16.95) / 5.96))(R-79 §8-1 の再計算と同じ)。抽選は 10c の counter の流れ
  (``core.rng.stream(seed, "proximity.notice", *k19_counters(時刻の鍵, 体, 相手))`` の 1 語・動きの側の seed・
  K19 の重なりの検査の控えに載る)を ``core.rng.philox_array`` で辺をまとめて引く(1 本ずつ引いた値と同じ=試験・
  親の判断 10-14 の 1)。同じ層・舞台の中・打ち切りの距離の中だけ。
- 体 × k の辺は刻みに 1 回だけなめる(:meth:`ProximityRule.edge_view`=気づく範囲と距離と届くを 1 回で作り、同席と
  知人出現が共有する)。

近傍の索引は ``engine.spatial_index.SpatialIndex``(刻みごとに作って捨てる=``TickScratch.near_index``・状態台帳の行
``PX0``)。描画は :class:`NearView`(規則・索引・気づいた印の読み口)を描画の前計算で受け取る。

層(:class:`ProximityLayer`・状態台帳の行 ``PX``=軸 1 diag・軸 2 discardable): 判定の規則(凍結)と計器(索引を作った
回数・索引の体の数・B5 の単位の在室人数の分布と最大)と、気づいた印の読み口(関係の層・読むだけ)。腕 ``distance``
のランだけ組み立てが作る(既定 None)。欄は組み立ての 1 回だけ置ける(付け替え・消すのは断る)。

「暫定」の印(B6・B8): 位置の出どころは node の座標(立っている体は node に重なる・edge 幾何でも立ち止まった体は node)
=近接の量はどれも「暫定・node 座標」。建物の中(B5 の単位)の体の位置は店に入る前に居たノードのまま(店の位置に
移らない=同じ店の体どうしが店のセルの中で離れうる)=建物の中の仮想空間の距離は測れない=同じ印(B5 の単位で距離を見ない)。
node 幾何の歩く速さ(1 刻み 1 node=0.41 m/s)に基づく量(移動中の分・群れ歩き・同行)は「暫定・node の歩く速さ」。
印は manifest の ``proximity.marks`` とつなぎの台帳(外す段 5-1)。

逐次ループ宣言(P4): 体数・辺の数に比例する Python のループは無い(気づく抽選は ``philox_array`` の配列演算=段の数 10 の
ループだけ・親の判断 10-14 の 1 で 1 組ずつの流れから替えた)。

expedient(本モジュール分)
- 会話の距離 d=2 m の決め打ち(B3・宣言)・感度の腕 1.0 m と 2.5 m。空間の段 3 で音の伝わり方の計算に置き換える。
- 離脱の距離=d+1 m(C9b G7 の成立 2 m・離脱 3 m のヒステリシスの幅を写した)。
- 知人に気づく抽選は 100 m で打ち切る(p < 1e-6)。
- B5 近接行の半径 10.3 m(Fotios ほか 2015 の他の歩行者を注視する距離の中央値・p_notice 答申・仮採用)。人数は知覚契約の密度逓減 3/2/1 のまま。
- 索引の格子 2.5 m(知覚契約の可視性格子と同じ幅・``engine.spatial_index``)。
"""

from __future__ import annotations

import functools
import math
import os
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping

import numpy as np

from shibuya.core.rng import k19_counter_array, philox_array, run_tick_key, unit_float
from shibuya.engine.spatial_index import INDEX_CELL_M, SpatialIndex

__all__ = [
    "MODE_CELL", "MODE_DISTANCE", "MODES", "DEFAULT_MODE", "D_DEFAULT", "D_ARMS", "LEAVE_MARGIN_M", "NOTICE_D75_M", "NOTICE_D25_M",
    "NOTICE_D50_M", "NOTICE_SCALE_M", "NOTICE_CUTOFF_M", "NOTICE_SOURCE", "NOTICE_DOMAIN", "B5_RADIUS_M",
    "B5_RADIUS_SOURCE", "INDEX_CELL_M", "UNIT_SOURCE", "SCHEMA", "arm", "set_arm", "d", "set_d", "notice_p",
    "ProximityRule", "NearView", "ProximityLayer", "manifest_fields", "CONFIG_KEYS", "OBSERVED_KEYS",
    "batch_partners", "marks_for", "rule_from", "OCC_BINS", "header_fields", "check_resume",
]

MODE_CELL: Final[str] = "cell"
MODE_DISTANCE: Final[str] = "distance"
MODES: Final[tuple[str, ...]] = (MODE_CELL, MODE_DISTANCE)
#: 〔第 2 期 2-4 V2〕既定の腕(10-03 §4 の決定=11a を版上げ 2 回目で既定に)。``cell`` は切替口(2-2 までの値の再現)。
DEFAULT_MODE: Final[str] = MODE_DISTANCE
#: 会話の距離 d[m](B3: 2 m の決め打ちを既定にし宣言=``engine.resolve.TALK_OPEN_METERS`` と同じ値・試験で突き合わせる)。
D_DEFAULT: Final[float] = 2.0
#: 感度の腕(B3)。
D_ARMS: Final[tuple[float, ...]] = (1.0, 2.0, 2.5)
#: 離脱の距離の余り[m](G7 の離脱 3 m − 成立 2 m)。
LEAVE_MARGIN_M: Final[float] = 1.0
#: 知人に気づく曲線の 2 点(R-62: Loftus & Harley 2005・実験 3 本の平均・75% = 34 ft・25% = 77 ft)。
NOTICE_D75_M: Final[float] = 10.4
NOTICE_D25_M: Final[float] = 23.5
#: 50% の距離と尺度(2 点から: 50% 点は 2 点の中点・尺度は 2 点の幅 ÷ (2 ln 3))。
NOTICE_D50_M: Final[float] = (NOTICE_D75_M + NOTICE_D25_M) / 2.0
NOTICE_SCALE_M: Final[float] = (NOTICE_D25_M - NOTICE_D75_M) / (2.0 * math.log(3.0))
#: 気づく抽選を打ち切る距離[m](p(100) ≈ 9e-7 < 1e-6・expedient)。
NOTICE_CUTOFF_M: Final[float] = 100.0
NOTICE_SOURCE: Final[str] = ("R-62(docs/research/v2-r62-field-of-view-anchors.md §1-2・Loftus & Harley 2005)・"
                             "R-79 §8-1(曲線の再計算)")
#: 気づく抽選の乱数の用途名(10c の counter の流れ・動きの側=``engine.run.MOTION_RNG_DOMAINS``)。
NOTICE_DOMAIN: Final[str] = "proximity.notice"
#: B5 近接行の半径[m](仮採用・expedient)。
B5_RADIUS_M: Final[float] = 10.3
B5_RADIUS_SOURCE: Final[str] = ("Fotios, Yang & Uttley 2015 の他の歩行者を注視する距離の中央値"
                                "(docs/research/v2-p-notice-research.md)・仮採用(10-13b §0-3)")
#: B5 の単位の出どころ(在席中の POI の区画)。
UNIT_SOURCE: Final[str] = "agents.poi_ref(在席中の POI の区画 id)∧ 体のセル == その POI のセル(world.pois.cell)"
#: manifest の ``proximity.schema``(欄を足したり意味を変えたりしたら上げる)。2: 気づく抽選を counter の流れにした。
#: 3: B5 の単位を店のセルの中の体に絞った・描画の知人は半径の中だけ・抽選を配列で引く(値は同じ)=親の判断 10-14。
SCHEMA: Final[str] = "shibuya.proximity/3"

# ------------------------------------------------------------------ 腕(組み立てのときに読む)
_ARM: str = os.environ.get("SHIBUYA_PROXIMITY", DEFAULT_MODE).strip().lower() or DEFAULT_MODE
if _ARM not in MODES:
    raise ValueError(f"SHIBUYA_PROXIMITY は {MODES} のどれか(いま {_ARM!r})")


def _check_d(value: Any) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"--proximity-d は {D_ARMS} のどれか(いま {value!r})") from None
    if v not in D_ARMS:
        raise ValueError(f"--proximity-d は {D_ARMS} のどれか(いま {value!r})")
    return v


_D: float = _check_d(os.environ.get("SHIBUYA_PROXIMITY_D", str(D_DEFAULT)).strip() or D_DEFAULT)


def arm() -> str:
    """いまの腕(``distance``=実距離=既定〔2-4 V2〕・``cell``=同じセル=切替口)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--proximity``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    global _ARM
    if str(name) not in MODES:
        raise ValueError(f"--proximity は {MODES} のどれか(いま {name!r})")
    _ARM = str(name)


def d() -> float:
    """いまの会話の距離 d[m](腕 ``distance`` のときだけ効く)。"""
    return _D


def set_d(value: Any) -> None:
    """会話の距離 d の感度の腕を選ぶ(CLI ``--proximity-d``・試験の切替口)。"""
    global _D
    _D = _check_d(value)


# ------------------------------------------------------------------ 状態のファイルの見出し(検収 M1)
def header_fields(layer: "ProximityLayer | None") -> dict[str, Any] | None:
    """状態のファイルの見出しの ``proximity``(腕 cell のランは書かない=None=今の見出しのまま)。"""
    if layer is None:
        return None
    return {"mode": layer.rule.mode, "d_m": float(layer.rule.d)}


def check_resume(saved: Any) -> None:
    """再開のときに、保存したランの腕(見出しの ``proximity``・無ければ cell)と今の腕が同じかを確かめる(違えば止める)。

    腕は設定の指紋に入れない(``run_day`` の引数ではない)ので、指紋の検査では見つからない=ここで見る。
    """
    s = saved if isinstance(saved, Mapping) else {}
    s_mode = str(s.get("mode", MODE_CELL))
    s_d = s.get("d_m")
    now_mode, now_d = arm(), (d() if arm() == MODE_DISTANCE else None)
    if s_mode != now_mode or (now_mode == MODE_DISTANCE and (s_d is None or float(s_d) != float(now_d))):
        raise ValueError(f"再開の近接の腕が親と違う(親 mode={s_mode} d={s_d}・今 mode={now_mode} d={now_d})"
                         "=--proximity・--proximity-d(環境変数 SHIBUYA_PROXIMITY・SHIBUYA_PROXIMITY_D)を親にそろえる")


# ------------------------------------------------------------------ 知人に気づく確率(B4)
def notice_p(dist: Any) -> np.ndarray:
    """R-62 の 2 点を通るロジスティック p(d)(距離[m] → 気づく確率)。"""
    x = (np.asarray(dist, dtype=np.float64) - NOTICE_D50_M) / NOTICE_SCALE_M
    return 1.0 / (1.0 + np.exp(np.clip(x, -700.0, 700.0)))


def _bands(r: Any, cell_band: Any = None) -> np.ndarray:
    """体の層=セルの層 ``cell_band[agents.cell]``(舞台の外は 0)。

    〔第 2 期 2-4 V2〕前は SoA の派生の列 ``agents.band``(状態台帳の軸 1 no・刻みの終わりの位置の確定で ``node_band`` から
    作り直す)を読んでいた。近接の既定が distance になると既定のランがこの列を読む=軸 1 no の列が挙動に効く(試験 T5 が
    落ちた)ので、behavior の列 ``agents.cell`` から導き直す(``node_band[n] == cell_band[node_cell[n]]``=資産と合成の世界で
    全ノード一致・値は同じ)。``cell_band`` を持たない規則(試験の合成の規則)だけ今までどおり列を読む。
    """
    if cell_band is None:
        return np.asarray(r.band)
    cell = np.asarray(r.cell).astype(np.int64)
    cb = np.asarray(cell_band)
    return np.where(cell >= 0, cb[np.maximum(cell, 0)], 0).astype(np.int8)


# ------------------------------------------------------------------ 判定の規則(凍結)
@dataclass(frozen=True, slots=True)
class ProximityRule:
    """腕 ``distance`` の判定の規則(組み立てで 1 回作る・ランの間は変えない)。``seed``=動きの側の seed。

    ``poi_cell``=POI ごとのセル(``world.pois.cell``・読むだけの写し)。B5 の単位は在席の印がありその店のセルの中に居る体
    (:meth:`units`)。None は試験の合成の体だけ(印をそのまま単位にする)=組み立て(:func:`rule_from`)は必ず渡す。
    """

    mode: str = MODE_DISTANCE
    d: float = D_DEFAULT
    b5_radius_m: float = B5_RADIUS_M
    notice_cutoff_m: float = NOTICE_CUTOFF_M
    seed: Any = 1
    day_key0: int = 0
    step_seconds: int = 60
    geometry: str = "node"
    poi_cell: Any = field(default=None, compare=False, repr=False)
    #: 〔第 2 期 2-4 V2〕セルの層(``world.assets.cell_band``・読むだけの写し)。体の層はここから導く(:func:`_bands`)。
    cell_band: Any = field(default=None, compare=False, repr=False)

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"mode は {MODES} のどれか(いま {self.mode!r})")
        if not (0.0 < self.d <= self.notice_cutoff_m):
            raise ValueError(f"d は 0 より大きく打ち切りの距離以下(いま {self.d!r})")
        if self.poi_cell is not None:
            pc = np.array(self.poi_cell, dtype=np.int64)
            pc.setflags(write=False)
            object.__setattr__(self, "poi_cell", pc)
        if self.cell_band is not None:
            cb = np.array(self.cell_band, dtype=np.int8)
            cb.setflags(write=False)
            object.__setattr__(self, "cell_band", cb)

    # ---------------------------------------------------------- B5 の単位(親の判断 10-14 の 2)
    def _unit_at(self, r: Any, ids: Any) -> np.ndarray:
        """体 ``ids`` の B5 の単位(在席の印がありその店のセルの中に居る体だけ・ほかは −1)。"""
        ids = np.asarray(ids, dtype=np.int64)
        u = np.asarray(r.poi_ref)[ids].astype(np.int64)
        pc = self.poi_cell
        if pc is None:
            return u
        ok = (u >= 0) & (u < pc.size)
        c = np.asarray(r.cell)[ids].astype(np.int64)
        ok &= c == pc[np.where(ok, u, 0)]
        return np.where(ok, u, -1)

    def units(self, agents: Any) -> np.ndarray:
        """全員の B5 の単位(``(n,)``・−1=単位なし)。索引と束の相手の候補が使う。"""
        r = agents.registry
        return self._unit_at(r, np.arange(int(np.asarray(r.poi_ref).shape[0]), dtype=np.int64))

    @property
    def is_distance(self) -> bool:
        return self.mode == MODE_DISTANCE

    @property
    def leave_m(self) -> float:
        """離脱の距離[m](d+1 m)。"""
        return float(self.d) + LEAVE_MARGIN_M

    def time_key(self, T: int) -> int:
        """気づく抽選の時刻の鍵(10c の counter と同じ ``run_tick_key``)。"""
        return run_tick_key(self.day_key0, int(T), self.step_seconds)

    # ---------------------------------------------------------- 組の判定(いまの SoA)
    def _parts(self, agents: Any, a: Any, b: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """(舞台の中・同じ層・距離[m]・同じ B5 の単位)。添字で集めてから float64 にする(全員の写しを作らない)。"""
        r = agents.registry
        a = np.asarray(a, dtype=np.int64)
        b = np.asarray(b, dtype=np.int64)
        cell = np.asarray(r.cell)
        on = (cell[a] >= 0) & (cell[b] >= 0)
        band = _bands(r, self.cell_band)
        same_band = band[a] == band[b]
        xy = np.asarray(r.xy)
        dd = xy[a].astype(np.float64) - xy[b].astype(np.float64)
        dist = np.sqrt((dd * dd).sum(axis=-1))
        ua = self._unit_at(r, a)
        same_unit = (ua >= 0) & (ua == self._unit_at(r, b))
        return on, same_band, dist, same_unit

    def _within(self, agents: Any, a: Any, b: Any, limit: float) -> np.ndarray:
        on, same_band, dist, same_unit = self._parts(agents, a, b)
        return on & ((same_band & (dist <= float(limit))) | same_unit)

    def reach(self, agents: Any, a: Any, b: Any) -> np.ndarray:
        """会話が届くか(舞台の中・同じ層・距離 ≤ d、または同じ B5 の単位)。"""
        return self._within(agents, a, b, self.d)

    def stay(self, agents: Any, a: Any, b: Any) -> np.ndarray:
        """会話を続けられるか(離脱の判定=距離 ≤ d+1 m、または同じ B5 の単位)。"""
        return self._within(agents, a, b, self.leave_m)

    def by_unit(self, agents: Any, a: Any, b: Any) -> np.ndarray:
        """届く組のうち、距離では届かず B5 の単位で届いた組(計器)。"""
        on, same_band, dist, same_unit = self._parts(agents, a, b)
        return on & same_unit & ~(same_band & (dist <= float(self.d)))

    # ---------------------------------------------------------- 体 × k の辺(刻みに 1 回)
    def notice_range(self, agents: Any, a: Any, b: Any) -> tuple[np.ndarray, np.ndarray]:
        """気づく範囲の中か(舞台の中・同じ層・距離 ≤ 打ち切り)と距離[m](範囲の外の距離は ``inf``)。

        体 × k の辺を毎刻み見るので、先に float32 の距離の 2 乗で打ち切り+1 m の外を落とし(上位集合)、残りだけを
        ``_parts`` と同じ float64 の式で決める(答えは ``_parts`` で全部を見たときと同じ=試験)。
        """
        a = np.asarray(a, dtype=np.int64)
        b = np.asarray(b, dtype=np.int64)
        a, b = np.broadcast_arrays(a, b)
        xy = np.asarray(agents.registry.xy)
        x = np.ascontiguousarray(xy[:, 0])
        y = np.ascontiguousarray(xy[:, 1])
        dx = x[a] - x[b]
        dy = y[a] - y[b]
        lim = float(self.notice_cutoff_m) + 1.0
        cand = np.flatnonzero((dx * dx + dy * dy <= lim * lim).ravel())
        inr = np.zeros(a.shape, dtype=bool)
        dist = np.full(a.shape, np.inf, dtype=np.float64)
        if cand.size:
            fa, fb = a.ravel()[cand], b.ravel()[cand]
            on, same_band, dc, _u = self._parts(agents, fa, fb)
            inr.ravel()[cand] = on & same_band & (dc <= float(self.notice_cutoff_m))
            dist.ravel()[cand] = dc
        return inr, dist

    def edge_view(self, agents: Any, a: Any, b: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """体 × k の辺を 1 回なめて (気づく範囲, 距離[m], 届く) を返す(同席と知人出現が共有する・検収 M2)。

        届く=:meth:`reach` と同じ答え(試験): 気づく範囲 ∧ 距離 ≤ d(d ≤ 打ち切り)か、舞台の中 ∧ 同じ B5 の単位。
        """
        a = np.asarray(a, dtype=np.int64)
        b = np.asarray(b, dtype=np.int64)
        inr, dist = self.notice_range(agents, a, b)
        cell = np.asarray(agents.registry.cell)
        u = self.units(agents)                                  # 体の数ぶん 1 回(辺ごとに印とセルを集め直さない)
        ua = u[a]
        su = (cell[a] >= 0) & (cell[b] >= 0) & (ua >= 0) & (ua == u[b])
        return inr, dist, (inr & (dist <= float(self.d))) | su

    # ---------------------------------------------------------- 気づく(B4)
    def notice_u(self, T: int, a: Any, b: Any) -> np.ndarray:
        """気づく抽選の一様乱数 [0, 1)=10c の counter の流れ 1 組 1 本(用途名 ``proximity.notice``・鍵の 3 語=時刻の
        鍵・体・相手=``k19_counters`` の並べ方・1 語だけ引く)を、``philox_array`` で組をまとめて引く(値は
        ``stream(seed, 用途名, *k19_counters(…)).random()`` と同じ=試験)。逐次ループ宣言: なし(配列演算)。"""
        aa = np.atleast_1d(np.asarray(a, dtype=np.int64))
        bb = np.atleast_1d(np.asarray(b, dtype=np.int64))
        tk = np.full(aa.size, self.time_key(T), dtype=np.uint64)
        raw = philox_array(self.seed, NOTICE_DOMAIN, k19_counter_array(tk, aa, bb), words=1)
        return unit_float(raw[:, 0])

    def noticed(self, agents: Any, T: int, a: Any, b: Any) -> np.ndarray:
        """体 ``a`` がこの刻みに相手 ``b`` に気づくか(範囲の中で ``u < p(d)``・配列・印は見ない=試験と道具の口)。"""
        aa, bb = np.broadcast_arrays(np.atleast_1d(np.asarray(a, dtype=np.int64)),
                                     np.atleast_1d(np.asarray(b, dtype=np.int64)))
        inr, dist = self.notice_range(agents, aa, bb)
        out = np.zeros(aa.shape, dtype=bool)
        if bool(np.any(inr)):
            out[inr] = self.notice_u(T, aa[inr], bb[inr]) < notice_p(dist[inr])
        return out


# ------------------------------------------------------------------ 描画へ渡す読み口
@dataclass(frozen=True, slots=True)
class NearView:
    """描画の前計算に渡す物(規則・この刻みの索引・気づいた印の読み口)。

    ``aware``=``(体, 相手の id の配列, 刻み) → 気づいている(印が切れていない)か``(関係の層の ``aware_of`` を読むだけ・
    関係の知人出現の起床が無いランは None=気づいた知人を足さない)。
    """

    rule: ProximityRule
    index: SpatialIndex
    aware: Callable[[int, np.ndarray, int], np.ndarray] | None = None


# ------------------------------------------------------------------ 届く相手のフォールバック(commit の pair_partners の腕)
def batch_partners(agents: Any, rule: ProximityRule, batch: Any, rows: Any, order_key: Any = None) -> np.ndarray:
    """適用の束 ``batch`` の中で、``rows``(束の中の位置)の体に届く束の体のうち並びの鍵が最小の体(届く体が無ければ −1)。

    ``commit.pair_partners``(同じセルの束の中で鍵の昇順の先頭・本人なら 2 番目)の腕 ``distance`` の版: 「同じセル」を
    「届く(:meth:`ProximityRule.reach`)」に替えた。鍵が同じなら体の id の小さい方。逐次ループ宣言: なし。
    """
    batch = np.asarray(batch, dtype=np.int64)
    rows = np.asarray(rows, dtype=np.int64)
    out = np.full(rows.size, -1, dtype=np.int64)
    if rows.size == 0 or batch.size < 2:
        return out
    r = agents.registry
    key = (batch.astype(np.uint64) if order_key is None
           else np.asarray(order_key).astype(np.uint64, copy=False))
    cell = np.asarray(r.cell)
    members = batch[cell[batch] >= 0]
    if members.size == 0:
        return out
    units = rule.units(agents)
    band = _bands(r, rule.cell_band)
    idx = SpatialIndex.build(r.xy, band, members, unit=units, n_total=int(agents.n))
    qa = batch[rows]
    xy = np.asarray(r.xy)
    q, cand, _d = idx.query_many(xy[qa, 0].astype(np.float64), xy[qa, 1].astype(np.float64), band[qa], rule.d)
    # B5 の単位の仲間(届く=距離を見ない・単位は店のセルの中の体)
    w, ids_u = idx.unit_members_many(units[qa])
    q = np.concatenate([q, w])
    cand = np.concatenate([cand, ids_u])
    keep = (cand != qa[q]) & (cell[qa[q]] >= 0)
    q, cand = q[keep], cand[keep]
    if q.size == 0:
        return out
    pos_in_batch = np.full(int(agents.n), -1, dtype=np.int64)
    pos_in_batch[batch] = np.arange(batch.size, dtype=np.int64)
    ck = key[pos_in_batch[cand]]
    order = np.lexsort((cand, ck, q))
    q, cand = q[order], cand[order]
    first = np.concatenate(([True], q[1:] != q[:-1]))
    out[q[first]] = cand[first]
    return out


# ------------------------------------------------------------------ 層(計器)と manifest
#: manifest の ``proximity`` の設定の子と観測の子(``engine.manifest_sections`` の混ざった辞書)。
CONFIG_KEYS: Final[tuple[str, ...]] = (
    "schema", "mode", "d_m", "d_arms", "leave_m", "b5_radius_m", "b5_radius_source", "notice", "unit_source",
    "index_cell_m", "position_source", "marks")
OBSERVED_KEYS: Final[tuple[str, ...]] = (
    "index_builds", "indexed_max", "unit_occupancy_max", "units_occupied_max", "unit_occupancy_hist")
#: B5 の単位の在室人数の箱(単位 × 刻みで数える)。
OCC_BINS: Final[tuple[tuple[int, int], ...]] = (
    (1, 1), (2, 4), (5, 9), (10, 49), (50, 99), (100, 499), (500, 999), (1000, 1 << 62))


def _occ_label(lo: int, hi: int) -> str:
    return f"{lo}" if lo == hi else (f"{lo}+" if hi >= (1 << 61) else f"{lo}-{hi}")


def marks_for(geometry: str) -> dict[str, str]:
    """「暫定」の印(B6・B8)。B6 は位置の出どころ(どの幾何でも立っている体は node)・B8 は node 幾何だけ。"""
    out = {"B6": "暫定・node 座標(位置の出どころ=node の座標。edge 幾何でも立ち止まった体は node・建物の中は"
                 "仮想空間の距離は測れない=在席中の体の xy は店に入る前のノードのまま=B5 の単位で距離を見ない)"}
    if str(geometry) == "node":
        out["B8"] = "暫定・node の歩く速さ(1 刻み 1 node=0.41 m/s に基づく量=移動中の分・群れ歩き・同行)"
    return out


class ProximityLayer:
    """腕 ``distance`` の層(判定の規則・計器・気づいた印の読み口)。組み立てが作る(既定の腕 cell では作らない=None)。

    欄は組み立ての 1 回だけ置ける(付け替え・消すのは断る=検収 L3)。計器は :attr:`meter_view`(読むだけの写し)。書く口は
    :meth:`build_index` だけ。``marks``=関係の層(``aware_of`` を読むだけ・知人出現の起床が無いランは None)。
    """

    __slots__ = ("rule", "_marks", "_meter")

    def __init__(self, rule: ProximityRule, *, marks: Any = None) -> None:
        self.rule = rule
        self._marks = marks
        self._meter = {
            "index_builds": 0, "indexed_max": 0, "unit_occupancy_max": 0, "units_occupied_max": 0,
            "unit_occupancy_hist": {_occ_label(lo, hi): 0 for lo, hi in OCC_BINS},
        }

    def __setattr__(self, name: str, value: Any) -> None:
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"近接の層の欄 {name} は付け替えられない(書く口は build_index だけ)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"近接の層の欄 {name} は消せない")

    @property
    def meter_view(self) -> Mapping[str, Any]:
        """計器の読むだけの写し。"""
        return MappingProxyType({k: (MappingProxyType(dict(v)) if isinstance(v, dict) else v)
                                 for k, v in self._meter.items()})

    def build_index(self, agents: Any) -> SpatialIndex:
        """この刻みの近傍の索引(舞台の中の体=セル ≥ 0)を作り、計器を数える。"""
        r = agents.registry
        ids = np.flatnonzero(np.asarray(r.cell) >= 0).astype(np.int64)
        idx = SpatialIndex.build(r.xy, _bands(r, self.rule.cell_band), ids, unit=self.rule.units(agents),
                                 n_total=int(agents.n))
        m = self._meter
        m["index_builds"] += 1
        m["indexed_max"] = max(int(m["indexed_max"]), int(ids.size))
        occ = idx.unit_counts()
        if occ.size:
            m["unit_occupancy_max"] = max(int(m["unit_occupancy_max"]), int(occ.max()))
            m["units_occupied_max"] = max(int(m["units_occupied_max"]), int(occ.size))
            h = m["unit_occupancy_hist"]
            for lo, hi in OCC_BINS:  # 逐次: 箱の数ぶん(8)
                h[_occ_label(lo, hi)] += int(np.count_nonzero((occ >= lo) & (occ <= hi)))
        return idx

    def view(self, agents: Any, index: SpatialIndex) -> NearView:
        """描画へ渡す読み口(気づいた印は関係の層を読むだけ)。"""
        aware = None if self._marks is None else functools.partial(self._marks.aware_of, agents)
        return NearView(self.rule, index, aware)

    def observed(self) -> dict[str, Any]:
        m = self._meter
        return {k: (dict(m[k]) if isinstance(m[k], dict) else int(m[k])) for k in OBSERVED_KEYS}


def manifest_fields(layer: "ProximityLayer | None") -> dict[str, Any]:
    """manifest の ``proximity``(腕 cell のランは層が無い=観測の子は null)。"""
    rule = None if layer is None else layer.rule
    cfg: dict[str, Any] = {
        "schema": SCHEMA,
        "mode": MODE_CELL if rule is None else rule.mode,
        "d_m": None if rule is None else float(rule.d),
        "d_arms": list(D_ARMS),
        "leave_m": None if rule is None else float(rule.leave_m),
        "b5_radius_m": None if rule is None else float(rule.b5_radius_m),
        "b5_radius_source": B5_RADIUS_SOURCE,
        "notice": {"d75_m": NOTICE_D75_M, "d25_m": NOTICE_D25_M, "d50_m": round(NOTICE_D50_M, 4),
                   "scale_m": round(NOTICE_SCALE_M, 4), "cutoff_m": NOTICE_CUTOFF_M, "source": NOTICE_SOURCE,
                   "rng": f"core.rng.philox_array(seed, {NOTICE_DOMAIN!r}, k19_counter_array(時刻の鍵, 体, 相手))・"
                          "1 語(stream(…, *k19_counters(…)).random() と同じ値)"},
        "unit_source": UNIT_SOURCE,
        "index_cell_m": INDEX_CELL_M,
        "position_source": None if rule is None else f"{rule.geometry} 幾何の xy(立っている体は node の座標)",
        "marks": None if rule is None else marks_for(rule.geometry),
    }
    if layer is None:
        return {**cfg, **{k: None for k in OBSERVED_KEYS}}
    return {**cfg, **layer.observed()}


def rule_from(*, mode: str, d_m: float, seed: Any, day_key0: int, step_seconds: int,
              geometry: str, poi_cell: Any, cell_band: Any = None) -> ProximityRule:
    """組み立ての口(``seed``=動きの側の seed=気づく抽選の counter の流れの鍵・``poi_cell``=``world.pois.cell``・
    ``cell_band``=``world.assets.cell_band``=体の層をセルから導く〔2-4 V2〕)。"""
    if poi_cell is None:
        raise ValueError("rule_from: poi_cell(world.pois.cell)が要る(B5 の単位を店のセルの中に絞る)")
    return ProximityRule(mode=str(mode), d=float(d_m), seed=seed, day_key0=int(day_key0),
                         step_seconds=int(step_seconds), geometry=str(geometry), poi_cell=poi_cell,
                         cell_band=cell_band)
