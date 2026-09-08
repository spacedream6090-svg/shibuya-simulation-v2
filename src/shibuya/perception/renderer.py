"""perception.renderer — 観測レコード → B0-B6 の決定論描画(知覚契約書 §2)。

正典
- §2.1「エンジンが構造化レコードを作り、決定論テンプレで**素性タグ付きの短い平叙文**
  (1行1事実・固定順序)に描画する。生JSONは渡さない。」
- §2.2 ブロック表と順序(変化率の昇順=``templates.BLOCK_IDS``)+v1 予算
  (共有静的 500-750・セル依存 ≤250・個体 ≤300・出力 o64)。
- §2.4 正規化規約9項(``normalize``)。§3.2 チャネル別上限(``channels``)。
- §5「B2 は**セル代表点**(またはセル内多数点)から見える物」「B5 には位置依存の差分だけ
  (**通常は空**)」「B0-B4 は同セル・同時間帯の全員でバイト一致」。
- §6 起床理由(B6)・R4 §6「直前の結果」=失敗理由+観測値+いま可能な行動3語。
- R5(認知設計書)§5「δ_read は**新着情報にのみ課金**・常在の観測プレフィクスには課さない」
  → 本モジュールは δ_read を返さない(新着=看板/傍受/受信は呼び出し側が数える)。

逐次ループ宣言(P4)
1. ``Renderer.render``: **起床した個体 1 体につき 1 回**の呼び出し(=1呼1描画)。
   個体数ぶんの Python ループは持たない(呼ぶ側が起床集合ぶん回す)。
   1 回の中で回るのは「同一セル在席者ぶんの距離計算」(NumPy・ループなし)と
   「行数ぶんの format」(1 桁)。
2. ``Renderer.prepare_tick``: **セル数**ぶんの xxh64(``hashes.field_row_hashes``・宣言済み)。
3. ``PerceptionAssets.load``: 可視性表の行数(43,479)ぶんの集約 1 本(**起動時 1 回**)。

expedient(本モジュール分)
- **歩行可能面積**(密度→人/m² の分母)。W2 に「歩ける面積」の欄が無いので、
  実データでは W10 街路点(2.5 m 格子=1 点 6.25 m²)の数から作り、合成世界では
  ``CELL_SIZE_M² × 0.15`` を使う。Fruin LOS の**境界**は mechanism、**分母**は expedient。
- 近接 k の密度逓減の写像: LOS A/B→疎(k=3)・C/D→中(k=2)・E/F→密(k=1)
  (契約書は「疎3/中2/密1」としか書かず、疎中密の境界を与えていない)。
- 内受容の閾値 ``INTERO_UP_EDGES=(4,7,9)``(``engine.change_detect`` と同値の二重定義。
  層契約により import できない)。
- 「いま可能な行動3語」の表 ``RESULT_OPTIONS``(契約書は「3語」としか書かない)。
- B4b は C3 では**固定の空文言**(サブセル 25 m 級のデータが無い)。C4 で**待ち行列だけ**
  差し込み口を付けた(``prepare_tick(queues=…)``)。行列は POI 単位=**セル共有**なので
  規約⑧(B0-B4b に個体依存語を置かない)は保たれる。行列が無いセルは従来の固定文言のまま。
- 流れ(B4)は既定 0(「一定です」)。方向データが無い。
- 天候が W13 に無い日付は**その時刻の最頻値**へ落とす(決定論)。

**解決した曖昧点(親へ報告・黙って解決していない)**
1. §2.4 ⑧「同セル同時間帯の2体で B0-B4 のバイト差分がゼロ」対 §2.2「B1=種別(約10)」。
   同一セルに種別の違う2体が居れば B1 は必ず違う → 検査は **(セル, 5分帯, 種別)** で行う。
2. §2.2 の「B0 300 tok」対 §2.2 の「共有静的(B0+B1+B3)≈500-750」+「共有静的は長くてよい」
   +§2.5「B0 に**条例の適用規則を明記する方針を維持**」。v0 の system ブロック(1,171字≒586 tok)
   を維持すると B0 単体では 300 を超えるので、**実効ゲートはグループ予算**
   (共有静的 ≤750・セル依存 ≤250・個体 ≤300)にした。B0 単体の超過は報告値として出す。
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, ClassVar, Final, Mapping, Sequence

import numpy as np

from shibuya.agents.state import (
    INTEROCEPTION_FIELDS,
    RESULT_TEXT,
    AgentState,
    ResultCode,
)
from shibuya.core.hashing import blake3_hex, xxh64
from shibuya.perception import channels as ch
from shibuya.perception import hashes as H
from shibuya.perception import normalize as N
from shibuya.perception import templates as T
from shibuya.perception.attention import strip_imperatives
from shibuya.world.assets import CELL_SIZE_M, WorldAssets
from shibuya.world.state import World

__all__ = [
    "DEFAULT_START_DATETIME",
    "WALKABLE_FRACTION_SYNTHETIC",
    "STREET_POINT_AREA_M2",
    "INTERO_UP_EDGES",
    "RESULT_OPTIONS",
    "ACTIVITY_WORDS",
    "Rendered",
    "PerceptionAssets",
    "Renderer",
]

#: 既定の世界内開始日時(W13 の最初の日=2026-07-28)。``clock_fn`` を渡さないときに使う。
DEFAULT_START_DATETIME: Final[datetime] = datetime(2026, 7, 28, 0, 0)
#: 合成世界の歩行可能面積の割合(expedient)。
WALKABLE_FRACTION_SYNTHETIC: Final[float] = 0.15
#: W10 街路点 1 点が代表する面積[m²](2.5 m 格子)。
STREET_POINT_AREA_M2: Final[float] = 6.25
#: 内受容の閾値(``engine.change_detect.INTERO_UP_EDGES`` と同値・層契約により二重定義)。
INTERO_UP_EDGES: Final[tuple[int, ...]] = (4, 7, 9)

#: ``Activity`` → 日本語(B5 直近の行動・B6 直前の結果)。
ACTIVITY_WORDS: Final[tuple[str, ...]] = (
    "待機", "移動", "待機", "休憩", "就寝", "購入", "会話", "乗車",
)

#: 失敗コード → 「いま可能」3語(行動契約書 §6・**待機を必ず含む**=失敗しない行動・expedient)。
RESULT_OPTIONS: Final[Mapping[int, tuple[str, str, str]]] = {
    ResultCode.MONEY_SHORT: ("移動", "待機", "休憩"),
    ResultCode.OUT_OF_STOCK: ("移動", "待機", "購入"),
    ResultCode.CLOSED: ("移動", "待機", "休憩"),
    ResultCode.TRAIN_FULL: ("待機", "移動", "休憩"),
    ResultCode.FARE_SHORT: ("移動", "待機", "休憩"),
    ResultCode.NO_TRAIN: ("待機", "移動", "休憩"),
    ResultCode.NO_STOP: ("移動", "待機", "乗車"),
    ResultCode.UNREACHABLE: ("移動", "待機", "休憩"),
    ResultCode.INTERRUPTED: ("移動", "待機", "休憩"),
    ResultCode.PARTNER_BUSY: ("待機", "移動", "会話"),
    ResultCode.REFUSED: ("移動", "待機", "退去"),
    ResultCode.PARTNER_GONE: ("移動", "待機", "会話"),
    ResultCode.NO_BED: ("移動", "待機", "休憩"),
    ResultCode.NO_PERMISSION: ("移動", "待機", "退去"),
    ResultCode.LOST_ARBITRATION: ("待機", "移動", "休憩"),
    ResultCode.UNDEFINED_ACTION: ("移動", "待機", "休憩"),
    ResultCode.BAD_TARGET: ("移動", "待機", "休憩"),
}


# ------------------------------------------------------------------ 描画結果
@dataclass(frozen=True)
class Rendered:
    """1 起床ぶんの描画結果。

    Attributes:
        agent_id / tick: どの個体のどの tick か。
        blocks: ブロック id → 描画バイト列(**順序=``templates.BLOCK_IDS``**)。
        text: 連結した本文(ブロック間は LF)。
        block_hashes: ブロック id → xxh64(三役の 1 本目)。
        prefix_key: ブロックハッシュ列の合成鍵(prefix キャッシュ鍵)。
        prompt_hash: 連結バイト列の blake3(16 進・再現性の指紋)。
        tokens_est: ブロック id → 推定トークン。
        group_tokens: 予算グループ → 推定トークン(実効ゲート)。
        truncations: チャネル切り詰めの記録。
        cache_hits / cache_misses: この描画で引いた共有ブロックの命中数。
    """

    agent_id: int
    tick: int
    blocks: "OrderedDict[str, bytes]"
    text: str
    block_hashes: Mapping[str, int]
    prefix_key: int
    prompt_hash: str
    tokens_est: Mapping[str, int]
    group_tokens: Mapping[str, int]
    truncations: tuple[ch.TruncationReport, ...] = ()
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def tokens_total(self) -> int:
        return int(sum(self.tokens_est.values()))

    def within_group_budgets(self) -> bool:
        return all(v <= T.GROUP_TOKEN_BUDGET[k] for k, v in self.group_tokens.items())

    def shared_static_bytes(self) -> bytes:
        """B0-B4b の連結(§2.4 ⑧ のバイト一致検査に使う)。"""
        return b"\n".join(self.blocks[b] for b in T.BLOCK_IDS if b not in ("B5", "B6"))


# ------------------------------------------------------------------ 知覚側の静的資産
@dataclass(frozen=True)
class PerceptionAssets:
    """描画に要る静的資産(セル代表点からの可視物・名称・歩行可能面積・天候表)。

    ``World``/``WorldAssets``(C2)は名称・可視性・天候を持たないので、知覚側で読む。
    """

    source: str
    place_ids: tuple[str, ...]
    walkable_area_m2: np.ndarray
    has_street: np.ndarray
    #: セル → 可視の店舗・施設(POI 索引・可視視点数の降順→ID 昇順)
    visible_poi: tuple[tuple[int, ...], ...]
    #: セル → 可視のランドマーク/出口の表示名(同順)
    visible_landmark: tuple[tuple[str, ...], ...]
    poi_name: tuple[str, ...]
    poi_cat: tuple[str, ...]
    #: (日付文字列, 時) → (天候, 日照, 暑さ)
    weather_by_date_hour: Mapping[tuple[str, int], tuple[str, str, str]]
    #: 時 → (天候, 日照, 暑さ)の最頻値(日付が表に無いときの決定論フォールバック)
    weather_by_hour: Mapping[int, tuple[str, str, str]]
    #: セル別の騒音段階(昼/夜・W10 街路点の最頻値)
    noise_stage_day: np.ndarray
    noise_stage_night: np.ndarray

    @property
    def n_cells(self) -> int:
        return len(self.place_ids)

    def noise_stage_for_tick(self, when: datetime) -> np.ndarray:
        """時刻 → セル別騒音段階(環境基準の昼 6-22 時 / 夜 22-6 時)。"""
        return self.noise_stage_day if 6 <= when.hour < 22 else self.noise_stage_night

    def weather(self, when: datetime) -> tuple[str, str, str]:
        """世界内日時 → (天候, 日照, 暑さ)。"""
        key = (when.strftime("%Y-%m-%d"), int(when.hour))
        got = self.weather_by_date_hour.get(key)
        if got is not None:
            return got
        return self.weather_by_hour.get(
            int(when.hour), (T.WEATHER_WORDS[0], T.DAYLIGHT_WORDS[1], T.HEAT_STAGE_WORDS[0])
        )

    # ---------------------------------------------------------- 生成
    @classmethod
    def synthetic(cls, world: World) -> "PerceptionAssets":
        """合成世界(または資産が無い実行)用。POI 名は ``カテゴリ+連番``。"""
        a = world.assets
        n = a.n_cells
        band_word = {-1: "UG", 0: "GL", 1: "DECK"}
        place_ids = tuple(
            f"g{int(a.cell_ix[i])}_{int(a.cell_iy[i])}_{band_word[int(a.cell_band[i])]}"
            for i in range(n)
        )
        names = tuple(f"{a.poi_cat[j]}{j:04d}" for j in range(a.n_poi))
        vis_poi: list[tuple[int, ...]] = [() for _ in range(n)]
        for c in range(n):
            hit = np.flatnonzero(a.poi_cell == c)
            vis_poi[c] = tuple(int(j) for j in hit[:8])
        area = np.full(n, CELL_SIZE_M * CELL_SIZE_M * WALKABLE_FRACTION_SYNTHETIC, np.float64)
        return cls(
            source="synthetic",
            place_ids=place_ids,
            walkable_area_m2=area,
            has_street=np.ones(n, dtype=bool),
            visible_poi=tuple(vis_poi),
            visible_landmark=tuple(() for _ in range(n)),
            poi_name=names,
            poi_cat=tuple(a.poi_cat),
            weather_by_date_hour={},
            weather_by_hour={
                h: (
                    T.WEATHER_WORDS[0],
                    T.DAYLIGHT_WORDS[1] if 5 <= h < 19 else T.DAYLIGHT_WORDS[2 if h >= 19 else 0],
                    T.HEAT_STAGE_WORDS[1],
                )
                for h in range(24)
            },
            noise_stage_day=np.ones(n, dtype=np.uint8),
            noise_stage_night=np.zeros(n, dtype=np.uint8),
        )

    #: ``load`` が要る資産ファイル(1 つでも欠けたら ``load_or_synthetic`` は合成へ落ちる)。
    REQUIRED_FILES: ClassVar[tuple[str, ...]] = (
        "w2_cells.parquet",
        "w6_poi.parquet",
        "w8_targets.parquet",
        "w8_t1_cell.parquet",
        "w10_street_points.parquet",
        "w11_station_exits.parquet",
        "w13_weather_hourly.parquet",
    )

    @classmethod
    def available(cls, path: str | Path | None) -> bool:
        """``load`` に必要なファイルが揃っているか。"""
        if path is None:
            return False
        p = Path(path)
        return p.is_dir() and all((p / f).exists() for f in cls.REQUIRED_FILES)

    @classmethod
    def load_or_synthetic(cls, path: str | Path | None, world: World) -> "PerceptionAssets":
        """資産があれば読み、無ければ合成へ落ちる(``World.load_or_synthetic`` と同じ作法)。"""
        if cls.available(path) and world.assets.source != "synthetic":
            return cls.load(path, world)  # type: ignore[arg-type]
        return cls.synthetic(world)

    @classmethod
    def load(cls, path: str | Path, world: World) -> "PerceptionAssets":
        """``data/world/v2`` から読む(W2/W6/W8/W10/W11/W13)。

        Note:
            逐次ループ宣言(P4)3: 可視性表の行数ぶんの集約 1 本(**起動時 1 回**)。
        """
        import pyarrow.parquet as pq

        p = Path(path)
        cells = pq.read_table(p / "w2_cells.parquet", columns=["place_id"]).to_pydict()
        place_ids = tuple(str(s) for s in cells["place_id"])
        n = len(place_ids)
        if n != world.n_cells:
            raise ValueError(f"セル数不一致: 資産 {n} vs World {world.n_cells}")

        poi = pq.read_table(
            p / "w6_poi.parquet", columns=["poi_id", "name", "cat"]
        ).to_pydict()
        poi_name = tuple(str(s) for s in poi["name"])
        poi_cat = tuple(str(s) for s in poi["cat"])
        poi_index = {str(pid): i for i, pid in enumerate(poi["poi_id"])}

        exits = pq.read_table(
            p / "w11_station_exits.parquet", columns=["exit_id", "exit_name", "station_title"]
        ).to_pydict()
        exit_label = {
            str(e): f"{str(st)}{str(nm)}"
            for e, nm, st in zip(exits["exit_id"], exits["exit_name"], exits["station_title"])
        }

        tgt = pq.read_table(
            p / "w8_targets.parquet", columns=["target_id", "kind", "ref_id"]
        ).to_pydict()
        tgt_kind = list(map(str, tgt["kind"]))
        tgt_ref = list(map(str, tgt["ref_id"]))

        t1 = pq.read_table(
            p / "w8_t1_cell.parquet", columns=["place_idx", "target_id", "n_viewpoints"]
        ).to_pydict()
        pidx = np.asarray(t1["place_idx"], dtype=np.int64)
        tid = np.asarray(t1["target_id"], dtype=np.int64)
        nvp = np.asarray(t1["n_viewpoints"], dtype=np.int64)
        # 可視視点数の降順 → target_id 昇順(§2.4 ② の決定論的な順序)
        order = np.lexsort((tid, -nvp, pidx))
        pidx, tid = pidx[order], tid[order]
        starts = np.searchsorted(pidx, np.arange(n), side="left")
        ends = np.searchsorted(pidx, np.arange(n), side="right")

        vis_poi: list[tuple[int, ...]] = []
        vis_land: list[tuple[str, ...]] = []
        for c in range(n):
            pois: list[int] = []
            lands: list[str] = []
            for t in tid[starts[c] : ends[c]]:
                k = tgt_kind[int(t)]
                ref = tgt_ref[int(t)]
                if k == "poi":
                    j = poi_index.get(ref)
                    if j is None:
                        continue
                    if poi_cat[j] in ("landmark", "attraction"):
                        if len(lands) < 4:
                            lands.append(poi_name[j])
                    elif len(pois) < 8:
                        pois.append(j)
                elif k == "exit":
                    if len(lands) < 4:
                        lands.append(exit_label.get(ref, "駅出入口"))
                if len(pois) >= 8 and len(lands) >= 4:
                    break
            vis_poi.append(tuple(pois))
            vis_land.append(tuple(lands))

        # ---- W10 街路点 → セル別 歩行可能面積・騒音段階(最頻値) ----
        area, has_street, ns_day, ns_night = _street_aggregate(p, world.assets, n)

        # ---- W13 天候 ----
        w13 = pq.read_table(
            p / "w13_weather_hourly.parquet",
            columns=["date", "hour", "weather", "daylight", "heat_stage"],
        ).to_pydict()
        by_dh: dict[tuple[str, int], tuple[str, str, str]] = {}
        per_hour: dict[int, list[tuple[str, str, str]]] = {}
        for d, h, w, dl, hs in zip(
            w13["date"], w13["hour"], w13["weather"], w13["daylight"], w13["heat_stage"]
        ):
            key = (str(d)[:10], int(h))
            val = (str(w), str(dl), str(hs))
            by_dh[key] = val
            per_hour.setdefault(int(h), []).append(val)
        by_hour = {
            h: max(sorted(set(v)), key=lambda x: (v.count(x), x)) for h, v in per_hour.items()
        }

        return cls(
            source=str(p),
            place_ids=place_ids,
            walkable_area_m2=area,
            has_street=has_street,
            visible_poi=tuple(vis_poi),
            visible_landmark=tuple(vis_land),
            poi_name=poi_name,
            poi_cat=poi_cat,
            weather_by_date_hour=by_dh,
            weather_by_hour=by_hour,
            noise_stage_day=ns_day,
            noise_stage_night=ns_night,
        )


def _street_aggregate(
    path: Path, assets: WorldAssets, n_cells: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """W10 街路点 → (歩行可能面積, 街路の有無, 昼騒音段, 夜騒音段)。全てベクトル演算。"""
    import pyarrow.parquet as pq

    d = pq.read_table(path / "w10_street_points.parquet", columns=["x", "y", "band"]).to_pydict()
    sx = np.asarray(d["x"], dtype=np.float64)
    sy = np.asarray(d["y"], dtype=np.float64)
    band_code = {"UG": -1, "GL": 0, "DECK": 1}
    sb = np.array([band_code[str(b)] for b in d["band"]], dtype=np.int8)
    ix = np.floor(sx / CELL_SIZE_M).astype(np.int64)
    iy = np.floor(sy / CELL_SIZE_M).astype(np.int64)

    def key(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
        return (a + 1_000_000) * 8_000_000 + (b + 1_000_000) * 4 + (c + 1)

    ck = key(assets.cell_ix.astype(np.int64), assets.cell_iy.astype(np.int64),
             assets.cell_band.astype(np.int64))
    order = np.argsort(ck, kind="stable")
    sk = ck[order]
    q = key(ix, iy, sb.astype(np.int64))
    pos = np.clip(np.searchsorted(sk, q), 0, sk.size - 1)
    hit = sk[pos] == q
    cell_of_point = np.where(hit, order[pos], -1)

    valid = cell_of_point >= 0
    counts = np.bincount(cell_of_point[valid], minlength=n_cells).astype(np.float64)
    area = np.maximum(counts * STREET_POINT_AREA_M2,
                      CELL_SIZE_M * CELL_SIZE_M * WALKABLE_FRACTION_SYNTHETIC)
    has_street = counts > 0

    ns_day = np.zeros(n_cells, dtype=np.uint8)
    ns_night = np.zeros(n_cells, dtype=np.uint8)
    for name, out in (("w10_noise_stage_day.npy", ns_day), ("w10_noise_stage_night.npy", ns_night)):
        f = path / name
        if not f.exists():
            continue
        stage = np.load(f)
        # セル×段の度数 → 最頻値(段は 0..3)
        n_stage = 4
        flat = cell_of_point[valid] * n_stage + np.clip(stage[valid].astype(np.int64), 0, n_stage - 1)
        tab = np.bincount(flat, minlength=n_cells * n_stage).reshape(n_cells, n_stage)
        out[:] = tab.argmax(axis=1).astype(np.uint8)
    return area, has_street, ns_day, ns_night


# ------------------------------------------------------------------ レンダラ
@dataclass
class _TickCache:
    """1 tick ぶんの前計算(セル配列とハッシュ)。"""

    tick: int = -1
    when: datetime = DEFAULT_START_DATETIME
    band5: int = -1
    los_stage: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint8))
    noise_stage: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint8))
    flow: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint8))
    salient: Mapping[int, tuple[str, ...]] = field(default_factory=dict)
    salient_digest: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int32))
    #: セル → B4b「近景」の描画バイト(行列がある セルだけ。無ければ固定文言)。
    b4b: Mapping[int, bytes] = field(default_factory=dict)
    #: ``hashes.b4_field_row`` の生欄 ``(n_cells, 4)`` int32(エンジンの変化検出器が読む)。
    b4_field_rows: np.ndarray = field(default_factory=lambda: np.zeros((0, 4), np.int32))
    b4_field_hash: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint64))
    cell_order: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    cell_start: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    cell_end: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))


class Renderer:
    """観測レンダラ(1 起床=1 呼び出し)。

    Example:
        >>> from shibuya.world.state import World
        >>> from shibuya.agents.state import AgentState
        >>> w = World.synthetic(n_cells=9, seed=1)
        >>> a = AgentState(4)
        >>> a.cell[:] = 0
        >>> r = Renderer(w, a, seed=7)
        >>> out = r.render(0, tick=750, wake_reason=3)
        >>> out.text.splitlines()[0].startswith("あなたは渋谷の街にいる")
        True
    """

    def __init__(
        self,
        world: World,
        agents: AgentState,
        assets: PerceptionAssets | None = None,
        clock_fn: Callable[[int], datetime] | None = None,
        seed: int | str = 0,
        *,
        acquaintances: Mapping[int, Sequence[int]] | None = None,
        watched_by: np.ndarray | None = None,
        budget_mode: ch.BudgetMode = ch.BudgetMode.FIXED_SLOTS,
        strict_group_budget: bool = True,
    ) -> None:
        """
        Args:
            world: 世界状態(セル密度・騒音段・POI 営業)。
            agents: 個体 SoA。
            assets: 知覚側資産。None なら ``PerceptionAssets.synthetic(world)``。
            clock_fn: tick → 世界内日時。None なら ``DEFAULT_START_DATETIME + tick 分``。
            seed: 乱数のマスターシード(注意ゲートの抽選に使う)。
            acquaintances: 個体 → 知人の agent_id(§3 人物④「知人は常に掲載」)。
            watched_by: ``(n,)`` 被注視人数(T2 の転置。None なら 0)。
            budget_mode: §3.2 の義務 ablation の切替。
            strict_group_budget: True でグループ予算超過を例外にする(既定)。
        """
        self.world = world
        self.agents = agents
        self.assets = assets if assets is not None else PerceptionAssets.synthetic(world)
        self.clock_fn = clock_fn or (lambda t: DEFAULT_START_DATETIME + timedelta(minutes=int(t)))
        self.seed = seed
        self.acquaintances = dict(acquaintances or {})
        self.watched_by = watched_by
        self.budget_mode = budget_mode
        self.strict_group_budget = strict_group_budget

        self._tickc = _TickCache()
        self._b0 = N.canonical_whitespace(T.TEMPLATES["B0.system"]).encode("utf-8")
        self._b4b = N.canonical_whitespace(
            T.TEMPLATES["B4b.near_empty"]
        ).encode("utf-8")
        self._b1_cache: dict[int, bytes] = {}
        self._b2_cache: dict[int, bytes] = {}
        self._b3_cache: dict[int, bytes] = {}
        self._b4_cache: dict[tuple[int, int], bytes] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.renders = 0
        self.truncation_count = 0

    # ---------------------------------------------------------- 前計算(1 tick 1 回)
    def prepare_tick(
        self,
        tick: int,
        *,
        salient_events: Mapping[int, Sequence[str]] | None = None,
        flow: np.ndarray | None = None,
        density: np.ndarray | None = None,
        noise_stage: np.ndarray | None = None,
        queues: Sequence[tuple[int, str, int]] | None = None,
    ) -> None:
        """この tick のセル配列とハッシュを作る(**セル数ぶんの xxh64 が 1 本**)。

        Args:
            queues: B4b の材料 ``(POI, 表示名, 人数)`` の列
                (``engine.processes.crowd.CrowdProcess.queue_rows``)。セルあたり上位 1 件を
                「<店名>の行列に<人数>人」として ``B4b.near`` に載せる。
        """
        w = self.world
        n = w.n_cells
        when = self.clock_fn(int(tick))
        dens = w.cells.density if density is None else np.asarray(density)
        per_m2 = np.asarray(dens, dtype=np.float64) / np.maximum(
            self.assets.walkable_area_m2, 1.0
        )
        los = N.peg_stage_array(per_m2, T.DENSITY_LOS_EDGES_PER_M2)

        if noise_stage is not None:
            ns = np.asarray(noise_stage, dtype=np.uint8)
        elif np.any(w.cells.noise_stage):
            ns = np.asarray(w.cells.noise_stage, dtype=np.uint8)
        else:
            ns = self.assets.noise_stage_for_tick(when).astype(np.uint8)

        fl = np.zeros(n, dtype=np.uint8) if flow is None else np.asarray(flow, dtype=np.uint8)

        sal: dict[int, tuple[str, ...]] = {}
        digest = np.zeros(n, dtype=np.int32)
        if salient_events:
            for c, items in salient_events.items():
                lines = tuple(str(s) for s in items)
                if not lines:
                    continue
                sal[int(c)] = lines
                digest[int(c)] = int(xxh64("\x1f".join(lines).encode("utf-8")) & 0x7FFF_FFFF)

        # B4b(行列)は**セル動的**なので、変化検出器が読む欄(``b4_field_row`` の第4列)へ
        # 混ぜる。混ぜないと「B4b の文面が変わったのに起床条件(i) が鳴らない」取りこぼしが
        # 生まれる(C3 で B4 について潰した穴と同じ形)。列を増やすと ``hashes.b4_field_row``
        # の凍結形が動くので、**同じ列にダイジェストを畳む**(行列が無ければ従来どおり 0)。
        b4b = self._b4b_lines(queues)
        for c, blob in b4b.items():
            mixed = int(xxh64(blob) & 0x7FFF_FFFF)
            digest[int(c)] = int((int(digest[int(c)]) * 31 + mixed) & 0x7FFF_FFFF)

        rows = H.b4_field_row(los, ns, fl, digest)
        self._tickc = _TickCache(
            tick=int(tick),
            when=when,
            band5=N.time_band(when),
            los_stage=los,
            noise_stage=ns,
            flow=fl,
            salient=sal,
            salient_digest=digest,
            b4b=b4b,
            b4_field_rows=rows,
            b4_field_hash=H.field_row_hashes(rows),
            **_cell_index(self.agents.cell, n),
        )

    @property
    def b4_field_rows(self) -> np.ndarray:
        """直近の ``prepare_tick`` が作った B4 描画欄 ``(n_cells, 4)`` int32。

        **エンジンの変化検出器(起床条件 (i))はこの 1 本を読む**。描画と検出が同じ欄を見るので
        「(i) が鳴らないのに文面が変わる」取りこぼしが構造的に 0 になる(§2.2/§5 の三役)。
        """
        return self._tickc.b4_field_rows

    # ---------------------------------------------------------- 本体
    def render(
        self,
        agent_id: int,
        tick: int,
        wake_reason: int | str = 3,
        last_result: int | None = None,
        last_action: str | None = None,
    ) -> Rendered:
        """1 個体・1 起床ぶんの観測を描画する。

        Args:
            agent_id: 起床した個体。
            tick: 起床 tick。
            wake_reason: ``agents.state.WakeCondition`` の値、または文言そのもの。
            last_result: ``ResultCode``(None なら ``agents.last_result`` を読む)。
            last_action: 直前に**試みた**行動語(None なら ``agents.activity`` で代用)。
                C2 の SoA は「直前に試みた行動」を持たない(``activity`` は現在の状態)ので、
                正確な文面には engine 側からの受け渡しが要る(親への hook 要求)。

        Note:
            逐次ループ宣言(P4)1: **1 起床につき 1 回**。個体数ぶんのループは持たない。
        """
        if self._tickc.tick != int(tick):
            self.prepare_tick(int(tick))
        tc = self._tickc
        a = self.agents
        i = int(agent_id)
        cell = int(a.cell[i])
        kind = int(a.kind[i])
        hits0, misses0 = self.cache_hits, self.cache_misses

        blocks: "OrderedDict[str, bytes]" = OrderedDict()
        trunc: list[ch.TruncationReport] = []
        blocks["B0"] = self._b0
        blocks["B1"] = self._b1(kind)
        blocks["B2"] = self._b2(cell, trunc)
        blocks["B3"] = self._b3(tc)
        blocks["B4"] = self._b4(cell, tc, trunc)
        blocks["B4b"] = tc.b4b.get(cell, self._b4b)
        blocks["B5"] = self._b5(i, cell, tc, trunc)
        blocks["B6"] = self._b6(i, wake_reason, last_result, cell, tc, last_action)

        # §2.4 ⑧: B0-B4b に個体依存語が無いこと(機械検査)
        shared_ids = [b for b in T.BLOCK_IDS if b not in ("B5", "B6")]
        shared = b"\n".join(blocks[b] for b in shared_ids)
        N.assert_no_agent_dependent_words(shared.decode("utf-8"))
        # §2.4 ⑥: 列挙ブロックに省略記法が無いこと(層2指摘で描画経路に結線)。
        # B2 は OSM 由来の固有名詞(「…等」を含む店名)が乗るため対象外=テンプレ側の列挙構造にのみ課す(expedient・登録簿)。
        for b in ("B4", "B4b", "B5"):
            N.assert_no_abbreviation(blocks[b].decode("utf-8"), b)

        tokens = {b: ch.estimate_tokens(blocks[b].decode("utf-8")) for b in T.BLOCK_IDS}
        groups: dict[str, int] = {"shared_static": 0, "cell": 0, "individual": 0}
        for b, t in tokens.items():
            groups[T.BLOCK_GROUP[b]] += t
        if self.strict_group_budget:
            for g, v in groups.items():
                if v > T.GROUP_TOKEN_BUDGET[g]:
                    raise ValueError(
                        f"§2.2 予算超過: グループ {g} が {v} tok(上限 {T.GROUP_TOKEN_BUDGET[g]})"
                    )

        bh = {b: H.block_hash(blocks[b]) for b in T.BLOCK_IDS}
        text = "\n".join(blocks[b].decode("utf-8") for b in T.BLOCK_IDS)
        self.renders += 1
        self.truncation_count += sum(1 for r in trunc if r.truncated)
        return Rendered(
            agent_id=i,
            tick=int(tick),
            blocks=blocks,
            text=text,
            block_hashes=bh,
            prefix_key=H.prefix_key([bh[b] for b in shared_ids], shared_ids),  # 共有 prefix(B0-B4b)のみ=§5
            prompt_hash=blake3_hex(b"\n".join(blocks[b] for b in T.BLOCK_IDS)),
            tokens_est=tokens,
            group_tokens=groups,
            truncations=tuple(trunc),
            cache_hits=self.cache_hits - hits0,
            cache_misses=self.cache_misses - misses0,
        )

    # ---------------------------------------------------------- 各ブロック
    def _b1(self, kind: int) -> bytes:
        got = self._b1_cache.get(kind)
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        word = T.KIND_WORDS[kind] if 0 <= kind < len(T.KIND_WORDS) else T.KIND_WORDS[1]
        out = N.canonical_whitespace(T.TEMPLATES["B1.kind"].format(kind=word)).encode("utf-8")
        self._b1_cache[kind] = out
        return out

    def _b2(self, cell: int, trunc: list[ch.TruncationReport]) -> bytes:
        got = self._b2_cache.get(cell)
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        A = self.assets
        lines: list[str] = []
        if 0 <= cell < A.n_cells:
            band = int(self.world.assets.cell_band[cell])
            lines.append(
                T.TEMPLATES["B2.place"].format(
                    place_id=A.place_ids[cell], band=T.BAND_WORDS.get(band, "地上")
                )
            )
            ground = T.GROUND_WORDS.get(band, T.GROUND_WORDS[0]) if bool(
                A.has_street[cell]
            ) else T.GROUND_NO_STREET
            kept, rep = ch.truncate_lines([ground], "B2.ground")
            trunc.append(rep)
            if kept:
                lines.append(T.TEMPLATES["B2.ground"].format(ground=kept[0]))
            # 可視物 上位3(可視視点数の降順→ID 昇順は資産側で確定済み)
            names = [A.poi_name[j] + "の店頭" for j in A.visible_poi[cell]]
            kept, rep = ch.truncate_lines(names, "B2.visible")
            trunc.append(rep)
            lines.append(
                T.TEMPLATES["B2.visible"].format(items=N.LIST_SEPARATOR.join(kept))
                if kept
                else T.TEMPLATES["B2.visible_empty"]
            )
            # 看板(a)=店舗基本属性 1 件(素性タグは凍結テンプレ側・命令文除去を掛ける)
            lines.append(self._signage(cell))
            # 地物・ランドマーク・出口
            kept, rep = ch.truncate_lines(list(A.visible_landmark[cell]), "B2.landmark")
            trunc.append(rep)
            lines.append(
                T.TEMPLATES["B2.landmark"].format(items=N.LIST_SEPARATOR.join(kept))
                if kept
                else T.TEMPLATES["B2.landmark_empty"]
            )
        else:
            lines.append(T.TEMPLATES["B2.place"].format(place_id="なし", band="地上"))
            lines.append(T.TEMPLATES["B2.visible_empty"])
            lines.append(T.TEMPLATES["B2.signage_empty"])
            lines.append(T.TEMPLATES["B2.landmark_empty"])
        out = N.join_lines(lines).encode("utf-8")
        self._b2_cache[cell] = out
        return out

    def _signage(self, cell: int) -> str:
        """看板(a): そのセルで最も可視の店舗 1 件の営業時間表示。

        §3.2 の「看板・広告面1件 25 tok」は**内容**(店名+属性)に掛ける。ブロックラベルと
        凍結された素性タグは全描画に共通の固定オーバーヘッドなので、ブロック総額(B2 150)側で
        見る(解決した曖昧点・親へ報告)。
        """
        A = self.assets
        w = self.world
        for j in A.visible_poi[cell]:
            if j >= w.n_poi:
                continue
            frm = int(w.pois.open_from[j]) // 60
            to = int(w.pois.open_to[j]) // 60
            body = strip_imperatives(f"{A.poi_name[j]}の表示。営業は{frm}時から{to}時。").kept
            kept, _ = ch.truncate_lines([body], "B2.signage")
            if kept:
                return T.TEMPLATES["B2.signage"].format(body=kept[0])
            return T.TEMPLATES["B2.signage_empty"]
        return T.TEMPLATES["B2.signage_empty"]

    def _b3(self, tc: _TickCache) -> bytes:
        got = self._b3_cache.get(tc.band5)
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        h, m = N.format_time(tc.when)
        weather, daylight, heat = self.assets.weather(tc.when)
        lines = [
            T.TEMPLATES["B3.time"].format(hour=h, minute=m),
            T.TEMPLATES["B3.weather"].format(weather=weather, daylight=daylight),
            T.TEMPLATES["B3.heat"].format(heat=heat),
        ]
        out = N.join_lines(lines).encode("utf-8")
        self._b3_cache[tc.band5] = out
        return out

    def _b4b_lines(
        self, queues: Sequence[tuple[int, str, int]] | None
    ) -> dict[int, bytes]:
        """待ち行列 → セル別の B4b 描画バイト(セルあたり上位 1 件)。

        Note:
            逐次ループ宣言(P4): **行列行数**ぶん(``queue_rows(k)`` の k・既定 1-3)。
            セル数・個体数には比例しない。
        """
        if not queues:
            return {}
        poi_cell = np.asarray(self.world.pois.cell, dtype=np.int64)
        best: dict[int, tuple[int, str]] = {}
        for poi, name, count in queues:  # 逐次: 行列行数ぶん
            j = int(poi)
            if not (0 <= j < poi_cell.size) or int(count) <= 0:
                continue
            c = int(poi_cell[j])
            if c < 0:
                continue
            prev = best.get(c)
            if prev is None or int(count) > prev[0]:
                best[c] = (int(count), str(name))
        out: dict[int, bytes] = {}
        for c, (count, name) in best.items():
            item = f"{name}の行列に{count}人"
            kept, _ = ch.truncate_lines([item], "B4b.near")
            if not kept:
                continue
            out[c] = N.canonical_whitespace(
                T.TEMPLATES["B4b.near"].format(items=N.LIST_SEPARATOR.join(kept))
            ).encode("utf-8")
        return out

    def _b4(self, cell: int, tc: _TickCache, trunc: list[ch.TruncationReport]) -> bytes:
        if not (0 <= cell < tc.los_stage.size):
            return N.join_lines(
                [
                    T.TEMPLATES["B4.density"].format(
                        stage=T.DENSITY_LOS_LETTERS[0], flow=T.FLOW_WORDS[0]
                    ),
                    T.TEMPLATES["B4.noise"].format(
                        stage=T.NOISE_STAGE_VOCAB[0], band=T.NOISE_BAND_WORDS[0]
                    ),
                    T.TEMPLATES["B4.salient_empty"],
                ]
            ).encode("utf-8")
        key = (cell, int(tc.b4_field_hash[cell]))
        got = self._b4_cache.get(key)
        if got is not None:
            self.cache_hits += 1
            return got
        self.cache_misses += 1
        los = int(min(tc.los_stage[cell], len(T.DENSITY_LOS_LETTERS) - 1))
        ns = int(min(tc.noise_stage[cell], len(T.NOISE_STAGE_VOCAB) - 1))
        lines = [
            T.TEMPLATES["B4.density"].format(
                stage=T.DENSITY_LOS_LETTERS[los], flow=T.FLOW_WORDS[int(tc.flow[cell])]
            ),
            T.TEMPLATES["B4.noise"].format(
                stage=T.NOISE_STAGE_VOCAB[ns], band=T.NOISE_BAND_WORDS[ns]
            ),
        ]
        items = list(tc.salient.get(cell, ()))
        kept, rep = ch.truncate_lines(items, "B4.salient")
        trunc.append(rep)
        lines.append(
            T.TEMPLATES["B4.salient"].format(items=N.LIST_SEPARATOR.join(kept))
            if kept
            else T.TEMPLATES["B4.salient_empty"]
        )
        out = N.join_lines(lines).encode("utf-8")
        self._b4_cache[key] = out
        return out

    def _b5(
        self, i: int, cell: int, tc: _TickCache, trunc: list[ch.TruncationReport]
    ) -> bytes:
        a = self.agents
        lines: list[str] = []
        # 内受容(閾値割れ分のみ)
        crossed = []
        for name, label in zip(INTEROCEPTION_FIELDS, ("空腹", "体力", "体感温度")):
            v = int(a.registry.field(name)[i])
            if v >= INTERO_UP_EDGES[0]:
                crossed.append(f"{label}は{v}で閾値を超えています。")
        kept, rep = ch.truncate_lines(crossed, "B5.intero")
        trunc.append(rep)
        lines.append(
            T.TEMPLATES["B5.intero"].format(items="".join(kept))
            if kept
            else T.TEMPLATES["B5.intero_empty"]
        )
        # 自己状態・所持・直近行動
        self_lines = [
            T.TEMPLATES["B5.holding"].format(
                money=f"{int(a.money[i]):,}",
                hands=T.HANDS_WORDS[1 if int(a.holdings[i]) > 0 else 0],
            ),
            T.TEMPLATES["B5.recent"].format(activity=_activity_word(int(a.activity[i]))),
        ]
        kept, rep = ch.truncate_lines(self_lines, "B5.self", max_items=2)
        lines += kept
        trunc.append(rep)
        # 近接人物 上位k(密度逓減 3/2/1)+知人は常に掲載
        near = self._nearby(i, cell, tc)
        kept, rep = ch.truncate_lines(near, "B5.near_person", max_items=len(near) or None)
        trunc.append(rep)
        lines.append(
            T.TEMPLATES["B5.near_person"].format(items=N.LIST_SEPARATOR.join(kept))
            if kept
            else T.TEMPLATES["B5.near_person_empty"]
        )
        # 被注視(T2 の転置。無ければ固定文言)
        nw = 0 if self.watched_by is None else int(self.watched_by[i])
        lines.append(
            T.TEMPLATES["B5.watched"].format(n=nw) if nw > 0 else T.TEMPLATES["B5.watched_empty"]
        )
        return N.join_lines(lines).encode("utf-8")

    def _nearby(self, i: int, cell: int, tc: _TickCache) -> list[str]:
        """同一セル在席者から近接上位 k(密度逓減)+知人常掲を作る。"""
        a = self.agents
        if not (0 <= cell < tc.los_stage.size) or tc.cell_start.size == 0:
            return []
        lo, hi = int(tc.cell_start[cell]), int(tc.cell_end[cell])
        peers = tc.cell_order[lo:hi]
        peers = peers[peers != i]
        if peers.size == 0:
            return []
        los = int(tc.los_stage[cell])
        k = 3 if los <= 1 else (2 if los <= 3 else 1)  # 疎3/中2/密1(境界は expedient)
        xy = np.asarray(a.xy, dtype=np.float64)
        d2 = ((xy[peers] - xy[i]) ** 2).sum(axis=1)
        take = min(k, peers.size)
        sel = peers[np.argpartition(d2, take - 1)[:take]] if peers.size > take else peers
        friends = set(int(x) for x in self.acquaintances.get(i, ()))
        chosen = sorted(set(int(x) for x in sel) | (friends & set(int(x) for x in peers)))
        return [f"P-{j}({'知人' if j in friends else '未知'})" for j in chosen]

    def _b6(
        self,
        i: int,
        wake_reason: int | str,
        last_result: int | None,
        cell: int,
        tc: _TickCache,
        last_action: str | None = None,
    ) -> bytes:
        a = self.agents
        if isinstance(wake_reason, str):
            reason = wake_reason
        else:
            r = int(wake_reason)
            reason = T.WAKE_REASON_TEXT[r] if 0 <= r < len(T.WAKE_REASON_TEXT) else (
                T.WAKE_REASON_TEXT[3]
            )
        lines = [T.TEMPLATES["B6.wake"].format(reason=reason)]
        code = int(a.last_result[i]) if last_result is None else int(last_result)
        acted = last_action or _activity_word(int(a.activity[i]))
        if int(a.last_result_tick[i]) < 0 and last_result is None:
            lines.append(T.TEMPLATES["B6.result_none"])
        elif code == int(ResultCode.OK):
            lines.append(T.TEMPLATES["B6.result_ok"].format(action=acted))
        else:
            why = RESULT_TEXT.get(code, "不明な理由")
            observed = self._observation(i, code, cell, tc)
            options = RESULT_OPTIONS.get(code, T.DEFAULT_OPTIONS)
            lines.append(
                T.TEMPLATES["B6.result_fail"].format(
                    action=acted,
                    why=why,
                    observed=observed,
                    options=N.LIST_SEPARATOR.join(options),
                )
            )
        lines.append(T.TEMPLATES["B6.question"])
        return N.join_lines(lines).encode("utf-8")

    def _observation(self, i: int, code: int, cell: int, tc: _TickCache) -> str:
        """R4 §6「失敗理由+**観測値**」。現在値から再構成する(C2 は詳細を持たない)。"""
        a = self.agents
        w = self.world
        if code == int(ResultCode.MONEY_SHORT):
            price = self._cheapest_price(cell)
            money = N.format_money(int(a.money[i]))
            return f"(所持金{money}・最も安い品は{N.format_money(price)})" if price else f"(所持金{money})"
        if code == int(ResultCode.CLOSED):
            nxt = self._next_open_hour(cell)
            return f"(次の開店は{nxt}時)" if nxt is not None else ""
        if code == int(ResultCode.FARE_SHORT):
            return f"(所持金{N.format_money(int(a.money[i]))})"
        return ""

    def _cheapest_price(self, cell: int) -> int:
        if not (0 <= cell < self.world.n_cells):
            return 0
        m = self.world.pois.cell == cell
        return int(self.world.pois.price[m].min()) if m.any() else 0

    def _next_open_hour(self, cell: int) -> int | None:
        if not (0 <= cell < self.world.n_cells):
            return None
        m = self.world.pois.cell == cell
        if not m.any():
            return None
        return int(self.world.pois.open_from[m].min()) // 60

    # ---------------------------------------------------------- 監査
    @property
    def cache_hit_rate(self) -> float:
        """共有ブロック(B1/B2/B3/B4)のキャッシュ命中率。"""
        total = self.cache_hits + self.cache_misses
        return float(self.cache_hits) / total if total else 0.0

    def report(self) -> str:
        """診断行 1 本。"""
        return (
            f"[perception.renderer] renders={self.renders} "
            f"cache_hit_rate={self.cache_hit_rate:.3f} "
            f"(hits={self.cache_hits} misses={self.cache_misses}) "
            f"truncated_channels={self.truncation_count} "
            f"template_sha256={T.template_sha256()[:16]}"
        )


# ------------------------------------------------------------------ 補助
def _activity_word(code: int) -> str:
    return ACTIVITY_WORDS[code] if 0 <= code < len(ACTIVITY_WORDS) else ACTIVITY_WORDS[0]


def _cell_index(cell: np.ndarray, n_cells: int) -> dict[str, np.ndarray]:
    """セル → 在席個体の CSR(1 tick 1 回・ベクトル演算)。"""
    c = np.asarray(cell, dtype=np.int64)
    order = np.argsort(c, kind="stable")
    sorted_c = c[order]
    idx = np.arange(n_cells, dtype=np.int64)
    return {
        "cell_order": order,
        "cell_start": np.searchsorted(sorted_c, idx, side="left"),
        "cell_end": np.searchsorted(sorted_c, idx, side="right"),
    }
