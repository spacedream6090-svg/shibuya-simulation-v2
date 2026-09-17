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
- **W14/W15 の凍結静的文への切替**(C5): ``world_dir`` に ``w14_signage.parquet`` /
  ``w15_cell_static.parquet`` が在ればその文面を使い、無ければ従来の合成文へ落ちる
  (**テンプレ本体と ``template_sha256`` は不変**)。凍結文の置き場所は
  W14 → ``B2.signage`` の本文(§3.2 の 25 tok 枠)・W15 → ``B2.visible`` の ``{items}``。
  W15 を B2 に**足す**と群予算(B2+B4+B4b ≤250)を超えるので、可視物リストを**置き換える**
  形にした。W15 側の上限は 45 tok(= B2 ブロック予算 150 − 実資産での他行最大)で、
  仕様 §1 W15 の「150 tok」は B2 ブロック全体の予算と読む(=**親判断待ち**)。
  どの版の文面で走ったかは ``PerceptionAssets.frozen_sources``(ファイル名→sha256)に出る。

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
from shibuya.perception.attention import SalientItem, rank_by_saliency, strip_imperatives
from shibuya.world.assets import CELL_SIZE_M, WorldAssets
from shibuya.world.state import LANDMARK_CATS, World

__all__ = [
    "DEFAULT_START_DATETIME",
    "WALKABLE_FRACTION_SYNTHETIC",
    "STREET_POINT_AREA_M2",
    "INTERO_UP_EDGES",
    "RESULT_OPTIONS",
    "INVITE_REASON",
    "person_word",
    "ACTIVITY_WORDS",
    "RANKING_PRIOR_SCORES",
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

#: 被招待(§6 起床(ii))の起床理由=``B6.wake`` の ``{reason}`` に入る**値**。
#: **テンプレ本体ではない**(``templates.TEMPLATES``/``WAKE_REASON_TEXT`` は不変=
#: ``template_sha256`` は動かない)。``RESULT_OPTIONS``(いま可能3語)と同じ扱いで、
#: 文面は自前=**expedient**(契約書は起床条件(ii)を列挙するだけで文面を与えない)。
#: 招待者を名指せないと承諾できない(行動契約書 §1-2 対象スロット:
#: 承諾=「行動: 会話 **対象: 招待者**」・``engine.run._settle_pending_invites``)。
INVITE_REASON: Final[str] = (
    "{person}があなたに話しかけました。"
    "応じるなら 行動: 会話 対象: {person}、応じないなら別の行動を選びます。"
)

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



def _prior_scores() -> Mapping[str, float]:
    """チャネル既定素性そのものの顕著性スコア(**採った項目が無い行の並び**に使う)。

    ``attention.rank_by_saliency`` を 1 件ずつのダミーに掛けるだけ(起動時 1 回・12 件)。
    式を二重に書かないための実装(スコアの定義は attention 側の 1 か所だけ)。
    """
    items = [
        SalientItem(
            item_id=cid, text="", size_m=pr.size_m, distance_m=pr.distance_m,
            contrast=pr.contrast, motion=pr.motion, deviance=pr.deviance,
        )
        for cid, pr in ch.RANKING_PRIORS.items()
    ]
    ranked, scores = rank_by_saliency(items)
    return {it.item_id: float(sc) for it, sc in zip(ranked, scores)}


#: チャネル → 既定素性のスコア(ablation ① の行の並び・**起動時に 1 回だけ**計算)。
RANKING_PRIOR_SCORES: Final[Mapping[str, float]] = _prior_scores()

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
    #: POI → W14 で**凍結された看板(a)文面**(無い POI は空文字=合成文へフォールバック)。
    poi_signage: tuple[str, ...] = ()
    #: セル → W15 で**凍結された B2 セル静的文**(無いセルは空文字=合成の可視物リストへ)。
    cell_static: tuple[str, ...] = ()
    #: 凍結資産のファイル名 → sha256(**manifest へ記録する値**。切替は「ファイルが在るか」だけで
    #: 決まるので、どの版の文面で走ったかはこの SHA でしか特定できない)。
    frozen_sources: Mapping[str, str] = field(default_factory=dict)

    @property
    def n_cells(self) -> int:
        return len(self.place_ids)

    @property
    def uses_frozen_signage(self) -> bool:
        return any(self.poi_signage)

    @property
    def uses_frozen_cell_static(self) -> bool:
        return any(self.cell_static)

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
                    # C9b G6 a′: 目印の集合は**世界側と同じ 1 本**
                    # (``world.state.LANDMARK_CATS`` = ``World.landmark_mask`` の判定)。
                    if poi_cat[j] in LANDMARK_CATS:
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

        # ---- W14/W15 の凍結静的文(在れば使う・無ければ従来の合成文) ----
        frozen_sources: dict[str, str] = {}
        poi_signage = _load_frozen_text(
            p, "w14_signage.parquet", "poi_id", [str(s) for s in poi["poi_id"]], frozen_sources
        )
        cell_static = _load_frozen_text(
            p, "w15_cell_static.parquet", "place_id", list(place_ids), frozen_sources
        )

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
            poi_signage=poi_signage,
            cell_static=cell_static,
            frozen_sources=frozen_sources,
        )


def _load_frozen_text(
    path: Path, name: str, key_col: str, keys: Sequence[str], sources: dict[str, str]
) -> tuple[str, ...]:
    """W14/W15 の凍結文 parquet → ``keys`` の順に並べた文面(無い鍵は空文字)。

    ファイルが無ければ全部空文字を返す(= **切替は world_dir のファイル有無で決まる**)。
    在るときは ``sources[name] = sha256`` を記録する(manifest 用)。

    Note:
        逐次ループ宣言(P4): 行数(POI 2,337 / セル 520)ぶんの辞書化 1 本。**起動時 1 回**。
    """
    import hashlib

    import pyarrow.parquet as pq

    f = Path(path) / name
    if not f.exists():
        return tuple("" for _ in keys)
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    sources[name] = h.hexdigest()
    d = pq.read_table(f, columns=[key_col, "text"]).to_pydict()
    table = {str(k): str(t) for k, t in zip(d[key_col], d["text"])}
    return tuple(table.get(str(k), "") for k in keys)


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
    #: セル → B4b の**生の項目**(単一ランキングが池へ入れる素材。固定枠では使わない)。
    b4b_items: Mapping[int, tuple[str, ...]] = field(default_factory=dict)
    #: ``hashes.b4_field_row`` の生欄 ``(n_cells, 4)`` int32(エンジンの変化検出器が読む)。
    b4_field_rows: np.ndarray = field(default_factory=lambda: np.zeros((0, 4), np.int32))
    b4_field_hash: np.ndarray = field(default_factory=lambda: np.zeros(0, np.uint64))
    cell_order: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    cell_start: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    cell_end: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    #: 個体 → ``cell_order`` の位置(逆置換)。自分の行を O(1) で外すために持つ(C7)。
    cell_pos: np.ndarray = field(default_factory=lambda: np.zeros(0, np.int64))
    #: ``cell_order`` の順に並べた x / y(**連続配列**)。1 呼あたりの gather を無くす(C7)。
    cell_x: np.ndarray = field(default_factory=lambda: np.zeros(0, np.float64))
    cell_y: np.ndarray = field(default_factory=lambda: np.zeros(0, np.float64))


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
        budget_mode: ch.BudgetMode | str = ch.BudgetMode.FIXED_SLOTS,
        strict_group_budget: bool = True,
        signage_enabled: bool = True,
        intent_mode: str = T.DEFAULT_INTENT_MODE,
        vocab_version: str = T.DEFAULT_VOCAB_VERSION,
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
            budget_mode: §3.2 の義務 ablation の切替(``ch.BudgetMode`` か
                ``"fixed"``/``"ranking"``)。既定=固定枠(現行の描画)。
            strict_group_budget: True でグループ予算超過を例外にする(既定)。
            signage_enabled: 看板・広告面(B2.signage)を描くか。知覚契約書 §8 第1陣 **⑥
                「広告ゼロ」**の切替口。``False`` で W14 凍結文も合成文も載せず、全セルで
                ``B2.signage_empty``(=「見える表示はありません」)にする。既定 True=
                現行の描画で**1 バイトも変わらない**。テンプレ本体は触らないので
                ``template_sha256`` は不変・規約⑧(セルの情報しか使わない)も不変。
            intent_mode: **AB7 自由意図の腕**の切替口(``"vocab"`` | ``"open"`` | ``"hint"``)。
                ``"open"`` で B0 の出力規約を ``templates.OUTPUT_SPEC_OPEN``(``行動:`` の
                1 行だけが「いま自分がしたいことを10字以内の動詞句で」)に差し替える。
                ``"hint"``(AB7b)は ``templates.OUTPUT_SPEC_HINT``= 語彙を例として見せた
                まま「当てはまる語が無いときだけ 10 字以内の動詞句で」を許す中間の腕。
                既定 ``"vocab"`` は現行の 24 語ホワイトリスト提示=**1 バイトも変わらない**。
                テンプレ本体(``TEMPLATES``)は触らないので ``template_sha256`` も不変。
                仕様書 ``docs/design/v2-open-intent-arm-spec.md`` §2。
            vocab_version: **行動語彙の版**(D-71 §3 F・``"v1"`` | ``"v2"``)。``"v2"`` で
                B0 の出力規約に 13 語目「食事」が載る(``templates.OUTPUT_SPEC_V2``)。
                既定 ``"v1"`` は現行の 24 語提示=**1 バイトも変わらない**。``"open"`` 腕は
                語彙を見せないので v1/v2 で B0 は同一(差は段0 辞書とエンジン側)。
        """
        self.world = world
        self.agents = agents
        self.assets = assets if assets is not None else PerceptionAssets.synthetic(world)
        self.clock_fn = clock_fn or (lambda t: DEFAULT_START_DATETIME + timedelta(minutes=int(t)))
        self.seed = seed
        self.acquaintances = dict(acquaintances or {})
        self.watched_by = watched_by
        self.budget_mode = ch.BudgetMode.parse(budget_mode)
        self.strict_group_budget = strict_group_budget
        self.signage_enabled = bool(signage_enabled)
        self.intent_mode = T.check_intent_mode(intent_mode)
        self.vocab_version = T.check_vocab_version(vocab_version)

        self._tickc = _TickCache()
        # 既定(vocab × v1)は ``TEMPLATES["B0.system"]`` と同一文字列=描画バイト不変
        # (AB7・語彙 v2)。
        self._b0 = N.canonical_whitespace(
            T.b0_system(self.intent_mode, self.vocab_version)
        ).encode("utf-8")
        self._b4b = N.canonical_whitespace(
            T.TEMPLATES["B4b.near_empty"]
        ).encode("utf-8")
        #: **注意の焦点**の欄(C9b G4)。``attention_columns`` のランだけ在る配列を 1 度だけ
        #: 掴む(``AgentState`` の配列は freeze/thaw で差し替わらない)。``None``= 焦点の無い
        #: ラン=**B5 の描画は 1 バイトも変わらない**。
        #: **B2(地物)は共有ブロック**(§2.4 ⑧ + §5 の共有 prefix)なので焦点で並べ替えない
        #: ——地物の焦点は描画に出さない(親へ報告済みの空欄)。
        self._focus_target: np.ndarray | None = (
            agents.focus_target if getattr(agents, "attention_columns", False) else None
        )
        #: 個体 → (知人の集合, 知人の id 配列)。**構築時に固定**なので 1 度作れば使い回せる(C7)。
        self._acq_cache: dict[int, tuple[frozenset[int], np.ndarray]] = {}
        self._b1_cache: dict[int, bytes] = {}
        self._b2_cache: dict[int, bytes] = {}
        self._b3_cache: dict[int, bytes] = {}
        self._b4_cache: dict[tuple[int, int], bytes] = {}
        #: ablation ①(単一ランキング)のセル依存ブロック。B2 が B4 と同じ池を分けるので
        #: 鍵は ``(セル, B4 欄ハッシュ)``(固定枠の ``_b2_cache`` はセルだけ)。
        self._rank_cell_cache: dict[
            tuple[int, int], tuple[dict[str, bytes], tuple[ch.TruncationReport, ...]]
        ] = {}
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
        b4b_items = self._b4b_raw(queues)
        b4b = self._b4b_lines(b4b_items)
        for c, blob in b4b.items():
            mixed = int(xxh64(blob) & 0x7FFF_FFFF)
            digest[int(c)] = int((int(digest[int(c)]) * 31 + mixed) & 0x7FFF_FFFF)

        rows = H.b4_field_row(los, ns, fl, digest)
        # C7: セル順の連続座標(1 tick 1 回の gather)。個体数ぶんの 3 配列
        # =24 byte/体(390,067 体で 9.4 MB)。1 呼あたりのセル在席者ぶんの gather を消す。
        idx = _cell_index(self.agents.cell, n)
        xy_all = np.asarray(self.agents.xy, dtype=np.float64)
        order = idx["cell_order"]
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
            b4b_items=b4b_items,
            b4_field_rows=rows,
            b4_field_hash=H.field_row_hashes(rows),
            cell_x=np.ascontiguousarray(xy_all[order, 0]),
            cell_y=np.ascontiguousarray(xy_all[order, 1]),
            **idx,
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
        inviter: int | None = None,
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
            inviter: **招待者の個体 id**(§6 起床(ii) 被招待。招待が無ければ None か負値)。
                与えると B6 起床行が ``INVITE_REASON``(招待者を名指す文)に替わる。
                ``wake_reason`` より優先する(被招待は起床理由そのものだから)。

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
        ranking = self.budget_mode is ch.BudgetMode.SINGLE_RANKING
        # ablation ①: セル依存(B2/B4/B4b)は**1 本の池**なので 3 ブロックを一緒に組む。
        cellb = self._cell_blocks_ranked(cell, tc, trunc) if ranking else None
        b6 = self._b6(i, wake_reason, last_result, cell, tc, last_action, inviter)
        blocks["B0"] = self._b0
        blocks["B1"] = self._b1(kind)
        blocks["B2"] = cellb["B2"] if cellb is not None else self._b2(cell, trunc)
        blocks["B3"] = self._b3(tc)
        blocks["B4"] = cellb["B4"] if cellb is not None else self._b4(cell, tc, trunc)
        blocks["B4b"] = cellb["B4b"] if cellb is not None else tc.b4b.get(cell, self._b4b)
        blocks["B5"] = (
            self._b5_ranked(i, cell, tc, trunc, ch.estimate_tokens(b6.decode("utf-8")))
            if ranking
            else self._b5(i, cell, tc, trunc)
        )
        blocks["B6"] = b6

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
            # 可視物: **W15 の凍結セル静的文が在ればそれ**・無ければ合成の可視物リスト。
            # 凍結文は ``B2.visible`` の枠(§3.2・60 tok)を占める(生成側の上限は 45 tok=
            # B2 予算 150 − 実資産での他行最大。枠を超えた文は切り詰めで落ち合成文へ戻る)。
            # テンプレは変えない。
            static = self._visible_static(cell)
            used_static = False
            if static:
                kept, rep = ch.truncate_lines([static], "B2.visible")
                trunc.append(rep)
                if kept:
                    lines.append(T.TEMPLATES["B2.visible"].format(items=kept[0]))
                    used_static = True
            if not used_static:
                # 可視物 上位3(可視視点数の降順→ID 昇順は資産側で確定済み)
                names = self._visible_names(cell)
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
        """看板(a): そのセルで最も可視の店舗 1 件の店頭表示。

        **W14 で凍結された文面が在ればそれを使い**、無ければ従来の合成文(店名+営業時間)を
        使う(切替は ``world_dir`` に ``w14_signage.parquet`` が在るかだけで決まる)。
        凍結文にも命令文除去とチャネル枠の切り詰めを掛ける(憲法6・多重防御。W14 のゲートを
        通っていれば no-op)。

        §3.2 の「看板・広告面1件 25 tok」は**内容**(店名+属性)に掛ける。ブロックラベルと
        凍結された素性タグは全描画に共通の固定オーバーヘッドなので、ブロック総額(B2 150)側で
        見る(解決した曖昧点・親へ報告)。
        """
        body = self._signage_body(cell)
        if body is None:
            return T.TEMPLATES["B2.signage_empty"]
        kept, _ = ch.truncate_lines([body], "B2.signage")
        if kept:
            return T.TEMPLATES["B2.signage"].format(body=kept[0])
        return T.TEMPLATES["B2.signage_empty"]

    # ---------------------------------------------------------- 素材(固定枠と単一ランキングで共有)
    def _visible_static(self, cell: int) -> str:
        """W15 の凍結セル静的文(無ければ空文字)。"""
        A = self.assets
        return A.cell_static[cell] if cell < len(A.cell_static) else ""

    def _visible_names(self, cell: int) -> list[str]:
        """可視の店舗・施設(可視視点数の降順→ID 昇順は資産側で確定済み)。"""
        A = self.assets
        return [A.poi_name[j] + "の店頭" for j in A.visible_poi[cell]]

    def _signage_body(self, cell: int) -> str | None:
        """看板(a)の**本文**(命令文除去済み・枠の切り詰め前)。

        ablation ⑥(§8 第1陣「広告ゼロ」)は ``signage_enabled=False`` でここを ``None`` に
        する。**固定枠と単一ランキングの両方**がこの 1 本を材料にしているので、腕は 1 箇所で
        効く(固定枠 → ``_signage`` が ``B2.signage_empty``・ランキング → 候補が空列)。

        Returns:
            見える表示が**無い**セルは ``None``、在るが命令文除去で本文が消えた場合は ``""``
            (この 2 つは描画が違う=前者は「見える表示はありません」・後者は素性タグだけの行)。
        """
        if not self.signage_enabled:
            return None
        A = self.assets
        w = self.world
        for j in A.visible_poi[cell]:
            if j >= w.n_poi:
                continue
            frozen = A.poi_signage[j] if j < len(A.poi_signage) else ""
            if frozen:
                return strip_imperatives(frozen).kept
            frm = int(w.pois.open_from[j]) // 60
            to = int(w.pois.open_to[j]) // 60
            return strip_imperatives(f"{A.poi_name[j]}の表示。営業は{frm}時から{to}時。").kept
        return None

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

    def _b4b_raw(
        self, queues: Sequence[tuple[int, str, int]] | None
    ) -> dict[int, tuple[str, ...]]:
        """待ち行列 → セル別の B4b **生の項目**(セルあたり上位 1 件)。

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
        return {c: (f"{name}の行列に{count}人",) for c, (count, name) in best.items()}

    def _b4b_lines(self, items: Mapping[int, tuple[str, ...]]) -> dict[int, bytes]:
        """B4b の生の項目 → セル別の描画バイト(固定枠の切り詰めを掛ける)。"""
        out: dict[int, bytes] = {}
        for c, raw in items.items():
            kept, _ = ch.truncate_lines(list(raw), "B4b.near")
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
        return [text for text, _d in self._nearby_items(i, cell, tc)]

    def _nearby_items(self, i: int, cell: int, tc: _TickCache) -> list[tuple[str, float]]:
        """``_nearby`` の各行と**その距離[m]**(単一ランキングの視角に使う)。

        近接 k の選び方(密度逓減 3/2/1・知人常掲)は §3 人物④の規則なので**両モード共通**。
        ablation ① が外すのは §3.2 のチャネル枠(トークン上限と件数)だけ。

        C7 性能修正(挙動不変): セル在席者ぶんの **Python 反復を全廃**した。
        以前は ① 距離の辞書(``{id: sqrt(d2)}``)と ② ``set(peers)`` を**毎呼**作っており、
        390,067 体(セル人口 1.4 万)で 1 呼 17 ms・llm 位相 46 s/tick になっていた
        (cProfile: 1 呼あたり 13,663 反復)。いまは
        ③ 座標は ``prepare_tick`` が作ったセル順の**連続配列**から取り(gather 無し)、
        ④ 自分の行は逆置換 ``cell_pos`` で O(1) に外し、
        ⑤ 知人の同セル判定は ``cell_pos`` の範囲比較(知人数ぶん)、
        ⑥ ``sqrt`` は**採った数件だけ**。
        **順序・同点処理・上位 k・距離の値は 1 ビットも変えていない**
        (``np.argpartition`` に渡す配列が旧実装と同一=``d2`` の並びまで同じ)。
        """
        a = self.agents
        if not (0 <= cell < tc.los_stage.size) or tc.cell_start.size == 0:
            return []
        lo, hi = int(tc.cell_start[cell]), int(tc.cell_end[cell])
        m = hi - lo
        if m <= 0:
            return []
        # d2 は「セル順の連続配列 − 自分」。旧実装の ``((xy[peers]-xy[i])**2).sum(1)`` と
        # **同じ順序・同じ丸め**(x²+y² の加算順まで同じ)。自分の座標は**2 スカラーだけ**読む
        # (``np.asarray(a.xy, float64)`` は float32 SoA の**全体コピー**=390,067 体で 1.6 ms/呼)。
        dx = tc.cell_x[lo:hi] - float(a.xy[i, 0])
        dy = tc.cell_y[lo:hi] - float(a.xy[i, 1])
        d2_full = dx * dx + dy * dy
        ids_full = tc.cell_order[lo:hi]
        p = int(tc.cell_pos[i]) - lo if 0 <= i < tc.cell_pos.size else -1
        if 0 <= p < m:  # 自分の行だけ外す(= 旧 ``peers[peers != i]``・順序は保たれる)
            peers = np.delete(ids_full, p)
            d2 = np.delete(d2_full, p)
        else:  # 自分がこの tick のセル索引に居ない(旧実装でも素通り)
            peers, d2 = ids_full, d2_full
        if peers.size == 0:
            return []
        los = int(tc.los_stage[cell])
        k = 3 if los <= 1 else (2 if los <= 3 else 1)  # 疎3/中2/密1(境界は expedient)
        take = min(k, peers.size)
        sel = peers[np.argpartition(d2, take - 1)[:take]] if peers.size > take else peers
        friends, friend_ids = self._acquaintances_of(i)
        chosen_set = {int(x) for x in sel}
        if friend_ids.size:  # 知人常掲(§3 人物④)= 同セルの知人を足す(知人数ぶん)
            pf = tc.cell_pos[friend_ids]
            chosen_set |= {
                int(x) for x in friend_ids[(pf >= lo) & (pf < hi) & (friend_ids != i)]
            }
        # C9b G4: **注意の焦点**が同じセルの人物なら常に載せ、**先頭に置く**
        # (UE AI Perception の ``Dominant Sense`` ではなく「焦点は優先して描く」だけ)。
        # ablation ①(``--budget-mode ranking``)では ``_rank_items`` が顕著性で並べ直すので
        # 先頭は保たれない——**掲載は保たれる**(順序は ablation の主題そのものなので譲る)。
        focus = -1
        if self._focus_target is not None:
            f = int(self._focus_target[i])
            if 0 <= f < int(a.n) and f != i:
                pf = int(tc.cell_pos[f])
                if lo <= pf < hi:
                    focus = f
                    chosen_set.add(f)
        chosen = sorted(chosen_set)
        if focus >= 0:  # 焦点だけ先頭へ(残りの並びは従来どおり id 昇順)
            chosen = [focus] + [x for x in chosen if x != focus]
        q = tc.cell_pos[np.asarray(chosen, dtype=np.int64)] - lo
        if 0 <= p < m:
            q = q - (q > p)  # 自分の行を外したぶん詰める
        dist = np.sqrt(d2[q])  # 採った数件だけ sqrt(旧: セル在席者ぶんの辞書)
        return [
            (
                f"{person_word(j)}({'知人' if j in friends else '未知'})",
                max(float(dv), 0.1),
            )
            for j, dv in zip(chosen, dist)
        ]

    def _acquaintances_of(self, i: int) -> tuple[frozenset[int], np.ndarray]:
        """個体 → (知人の集合, 知人 id の配列)。**1 度作って使い回す**(C7)。

        知人表は ``Renderer`` の構築時に固定される(§3 人物④「知人は常に掲載」)ので、
        毎呼 ``set(...)`` を組み直す必要がない。範囲外の id はここで落とす
        (旧実装では同セル集合との積で自然に落ちていた)。
        """
        got = self._acq_cache.get(i)
        if got is None:
            names = frozenset(int(x) for x in self.acquaintances.get(i, ()))
            arr = np.fromiter(sorted(names), dtype=np.int64, count=len(names))
            n = int(self.agents.n)
            if arr.size:
                arr = arr[(arr >= 0) & (arr < n)]
            got = (names, arr)
            self._acq_cache[i] = got
        return got

    # ---------------------------------------------------------- ablation ①(単一ランキング)
    def _rank_items(
        self,
        cand: Mapping[str, Sequence[str]],
        overrides: Mapping[tuple[str, int], Mapping[str, float]],
    ) -> list[tuple[str, str, float]]:
        """候補 → **顕著性の降順**(同点は item_id 昇順)の ``(channel_id, 行, スコア)``。

        顕著性は ``attention.rank_by_saliency`` そのもの(§4 のフロア付き対数加算)。
        素性はチャネル既定 ``channels.RANKING_PRIORS`` で、実測がある項目
        (近接人物の距離・内受容の閾値超過)は ``overrides`` が上書きする。

        Note:
            逐次ループ宣言(P4): 候補件数ぶんのループ1本(1 セル/1 個体で十数件)。
        """
        items: list[SalientItem] = []
        for cid in sorted(cand):  # 決定論: 入力の辞書順に依存しない
            prior = ch.RANKING_PRIORS[cid]
            for k, text in enumerate(cand[cid]):
                ov = dict(overrides.get((cid, k), {}))
                items.append(
                    SalientItem(
                        item_id=f"{cid}#{k:03d}",
                        text=text,
                        size_m=float(ov.get("size_m", prior.size_m)),
                        distance_m=float(ov.get("distance_m", prior.distance_m)),
                        contrast=float(ov.get("contrast", prior.contrast)),
                        motion=float(ov.get("motion", prior.motion)),
                        deviance=float(ov.get("deviance", prior.deviance)),
                    )
                )
        ranked, scores = rank_by_saliency(items)
        return [
            (it.item_id.split("#", 1)[0], it.text, float(sc)) for it, sc in zip(ranked, scores)
        ]

    def _pool_render(
        self,
        cand: Mapping[str, Sequence[str]],
        overrides: Mapping[tuple[str, int], Mapping[str, float]],
        blocks: Sequence[str],
        group: str,
        reserve_tokens: int,
        build: Callable[[Mapping[str, list[str]], Sequence[str]], dict[str, bytes]],
    ) -> tuple[dict[str, bytes], tuple[ch.TruncationReport, ...]]:
        """§3.2 の ablation ①: **1 本の池**で採否を決め、群予算に収まるまで最下位を落とす。

        1. 池の総額 = そのブロック群のチャネル上限の総和(§3.2「**同一総トークン**」)。
        2. 順位順に採る(``channels.take_within_pool``= 固定枠と同じ「行の途中で切らない」)。
        3. 実際の描画バイトが §2.2 のグループ予算を超えていたら、**最下位から 1 件ずつ**
           落として組み直す(ラベル等の固定オーバーヘッドは池の会計に入らないため)。

        Note:
            逐次ループ宣言(P4): 2 は候補件数ぶん・3 は採った件数が上限のループ。
            どちらも**個体数・セル数に比例しない**(1 セル/1 個体で十数件)。
        """
        ranked = self._rank_items(cand, overrides)
        n_fit, _used = ch.take_within_pool([t for _, t, _ in ranked], ch.pool_token_budget(blocks))
        kept: dict[str, list[str]] = {cid: [] for cid in cand}
        best: dict[str, float] = {}
        accepted: list[str] = []  # 採った項目のチャネル(順位順)
        for idx, (cid, text, score) in enumerate(ranked):
            if idx >= n_fit:
                break
            kept[cid].append(text)
            accepted.append(cid)
            best.setdefault(cid, score)
        budget = int(T.GROUP_TOKEN_BUDGET[group]) - int(reserve_tokens)
        while True:
            out = build(kept, self._channel_order(cand, best))
            total = sum(ch.estimate_tokens(b.decode("utf-8")) for b in out.values())
            if total <= budget or not accepted:
                break
            cid = accepted.pop()
            kept[cid].pop()
            if not kept[cid]:
                best.pop(cid, None)
        reports = tuple(
            ch.TruncationReport(
                channel_id=cid,
                kept=len(kept[cid]),
                dropped=len(cand[cid]) - len(kept[cid]),
                tokens_before=sum(ch.estimate_tokens(t) for t in cand[cid]),
                tokens_after=sum(ch.estimate_tokens(t) for t in kept[cid]),
            )
            for cid in sorted(cand)
        )
        return out, reports

    def _channel_order(
        self, cand: Mapping[str, Sequence[str]], best: Mapping[str, float]
    ) -> list[str]:
        """ブロック内の**行の並び**= チャネルの最上位項目のスコア降順(同点は id 昇順)。

        1 チャネル=1 行(``B5.self`` だけ 2 行)なので、これが「単一ランキングの順序」。
        採った項目が無いチャネル(空文言を出す行)はチャネル既定素性のスコアで並べる。
        """
        return sorted(
            cand,
            key=lambda cid: (-float(best.get(cid, RANKING_PRIOR_SCORES[cid])), cid),
        )

    def _lines_for(self, channel_id: str, items: Sequence[str]) -> list[str]:
        """チャネル + 採った項目 → 描画行(固定枠と**同じテンプレ**を使う)。"""
        if channel_id == "B2.ground":
            return [T.TEMPLATES["B2.ground"].format(ground=items[0])] if items else []
        if channel_id == "B2.visible":
            return [
                T.TEMPLATES["B2.visible"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B2.visible_empty"]
            ]
        if channel_id == "B2.signage":
            return [
                T.TEMPLATES["B2.signage"].format(body=items[0])
                if items
                else T.TEMPLATES["B2.signage_empty"]
            ]
        if channel_id == "B2.landmark":
            return [
                T.TEMPLATES["B2.landmark"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B2.landmark_empty"]
            ]
        if channel_id in ("B4.density", "B4.noise"):
            return [items[0]] if items else []
        if channel_id == "B4.salient":
            return [
                T.TEMPLATES["B4.salient"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B4.salient_empty"]
            ]
        if channel_id == "B4b.near":
            return [
                T.TEMPLATES["B4b.near"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B4b.near_empty"]
            ]
        if channel_id == "B5.intero":
            return [
                T.TEMPLATES["B5.intero"].format(items="".join(items))
                if items
                else T.TEMPLATES["B5.intero_empty"]
            ]
        if channel_id == "B5.self":
            return list(items)
        if channel_id == "B5.near_person":
            return [
                T.TEMPLATES["B5.near_person"].format(items=N.LIST_SEPARATOR.join(items))
                if items
                else T.TEMPLATES["B5.near_person_empty"]
            ]
        if channel_id == "B5.watched":
            return [items[0]] if items else [T.TEMPLATES["B5.watched_empty"]]
        raise KeyError(f"未登録チャネル: {channel_id!r}")

    def _cell_candidates(self, cell: int, tc: _TickCache) -> tuple[dict[str, list[str]], str]:
        """セル依存(B2/B4/B4b)の候補と、チャネルでない構造行(B2 場所)。"""
        A = self.assets
        cand: dict[str, list[str]] = {
            "B2.ground": [],
            "B2.visible": [],
            "B2.signage": [],
            "B2.landmark": [],
            "B4.density": [],
            "B4.noise": [],
            "B4.salient": [],
            "B4b.near": [],
        }
        if 0 <= cell < A.n_cells:
            band = int(self.world.assets.cell_band[cell])
            place = T.TEMPLATES["B2.place"].format(
                place_id=A.place_ids[cell], band=T.BAND_WORDS.get(band, "地上")
            )
            cand["B2.ground"] = [
                T.GROUND_WORDS.get(band, T.GROUND_WORDS[0])
                if bool(A.has_street[cell])
                else T.GROUND_NO_STREET
            ]
            static = self._visible_static(cell)
            cand["B2.visible"] = [static] if static else self._visible_names(cell)
            body = self._signage_body(cell)
            cand["B2.signage"] = [] if body is None else [body]
            cand["B2.landmark"] = list(A.visible_landmark[cell])
        else:
            place = T.TEMPLATES["B2.place"].format(place_id="なし", band="地上")
        if 0 <= cell < tc.los_stage.size:
            los = int(min(tc.los_stage[cell], len(T.DENSITY_LOS_LETTERS) - 1))
            ns = int(min(tc.noise_stage[cell], len(T.NOISE_STAGE_VOCAB) - 1))
            cand["B4.density"] = [
                T.TEMPLATES["B4.density"].format(
                    stage=T.DENSITY_LOS_LETTERS[los], flow=T.FLOW_WORDS[int(tc.flow[cell])]
                )
            ]
            cand["B4.noise"] = [
                T.TEMPLATES["B4.noise"].format(
                    stage=T.NOISE_STAGE_VOCAB[ns], band=T.NOISE_BAND_WORDS[ns]
                )
            ]
            cand["B4.salient"] = list(tc.salient.get(cell, ()))
            cand["B4b.near"] = list(tc.b4b_items.get(cell, ()))
        else:
            cand["B4.density"] = [
                T.TEMPLATES["B4.density"].format(
                    stage=T.DENSITY_LOS_LETTERS[0], flow=T.FLOW_WORDS[0]
                )
            ]
            cand["B4.noise"] = [
                T.TEMPLATES["B4.noise"].format(
                    stage=T.NOISE_STAGE_VOCAB[0], band=T.NOISE_BAND_WORDS[0]
                )
            ]
        return cand, place

    def _cell_blocks_ranked(
        self, cell: int, tc: _TickCache, trunc: list[ch.TruncationReport]
    ) -> dict[str, bytes]:
        """B2/B4/B4b を**セル依存の 1 本の池**(≤250 tok)で組む(ablation ①)。

        材料はセルの情報だけ(個体依存語は 1 語も入らない)ので、§2.4 ⑧「同セル同時間帯の
        2 体でバイト差分ゼロ」は固定枠と同じく成り立つ。キャッシュ鍵は ``(セル, B4 欄ハッシュ)``
        (固定枠の B2 はセルだけで足りるが、単一ランキングでは B4 の内容が B2 の採否を動かす)。
        """
        fh = int(tc.b4_field_hash[cell]) if 0 <= cell < tc.b4_field_hash.size else -1
        key = (int(cell), fh)
        got = self._rank_cell_cache.get(key)
        if got is not None:
            self.cache_hits += 1
            trunc.extend(got[1])
            return got[0]
        self.cache_misses += 1
        cand, place = self._cell_candidates(cell, tc)

        def build(kept: Mapping[str, list[str]], order: Sequence[str]) -> dict[str, bytes]:
            rows: dict[str, list[str]] = {"B2": [place], "B4": [], "B4b": []}
            for cid in order:
                block = "B4b" if cid.startswith("B4b.") else cid.split(".", 1)[0]
                rows[block].extend(self._lines_for(cid, kept[cid]))
            return {b: N.join_lines(rows[b]).encode("utf-8") for b in ("B2", "B4", "B4b")}

        out, reports = self._pool_render(cand, {}, ("B2", "B4", "B4b"), "cell", 0, build)
        self._rank_cell_cache[key] = (out, reports)
        trunc.extend(reports)
        return out

    def _b5_ranked(
        self,
        i: int,
        cell: int,
        tc: _TickCache,
        trunc: list[ch.TruncationReport],
        reserve_tokens: int,
    ) -> bytes:
        """B5 を**個体の 1 本の池**(≤220 tok)で組む(ablation ①)。

        群予算(個体 ≤300)から B6 の実測ぶんを差し引いた残りが上限になる。
        """
        a = self.agents
        overrides: dict[tuple[str, int], dict[str, float]] = {}
        crossed: list[str] = []
        span = max(1, T.INTERO_SCALE_MAX - INTERO_UP_EDGES[0])
        for name, label in zip(INTEROCEPTION_FIELDS, ("空腹", "体力", "体感温度")):
            v = int(a.registry.field(name)[i])
            if v >= INTERO_UP_EDGES[0]:
                overrides[("B5.intero", len(crossed))] = {
                    "deviance": min(1.0, (v - INTERO_UP_EDGES[0]) / span)
                }
                crossed.append(f"{label}は{v}で閾値を超えています。")
        near = self._nearby_items(i, cell, tc)
        for k, (_text, d) in enumerate(near):
            overrides[("B5.near_person", k)] = {"distance_m": float(d)}
        nw = 0 if self.watched_by is None else int(self.watched_by[i])
        cand: dict[str, list[str]] = {
            "B5.intero": crossed,
            "B5.self": [
                T.TEMPLATES["B5.holding"].format(
                    money=f"{int(a.money[i]):,}",
                    hands=T.HANDS_WORDS[1 if int(a.holdings[i]) > 0 else 0],
                ),
                T.TEMPLATES["B5.recent"].format(activity=_activity_word(int(a.activity[i]))),
            ],
            "B5.near_person": [t for t, _d in near],
            "B5.watched": [T.TEMPLATES["B5.watched"].format(n=nw)] if nw > 0 else [],
        }

        def build(kept: Mapping[str, list[str]], order: Sequence[str]) -> dict[str, bytes]:
            rows: list[str] = []
            for cid in order:
                rows.extend(self._lines_for(cid, kept[cid]))
            return {"B5": N.join_lines(rows).encode("utf-8")}

        out, reports = self._pool_render(
            cand, overrides, ("B5",), "individual", int(reserve_tokens), build
        )
        trunc.extend(reports)
        return out["B5"]

    def _b6(
        self,
        i: int,
        wake_reason: int | str,
        last_result: int | None,
        cell: int,
        tc: _TickCache,
        last_action: str | None = None,
        inviter: int | None = None,
    ) -> bytes:
        a = self.agents
        if inviter is not None and int(inviter) >= 0:
            # §6 起床(ii) 被招待: 誰に話しかけられたかを**個体ブロック**で名指す。
            # B6 は個体ブロックなので規約⑧(B0-B4b のバイト一致)には触れない。
            reason = INVITE_REASON.format(person=person_word(int(inviter)))
        elif isinstance(wake_reason, str):
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
        """診断行 1 本。

        凍結静的文(W14/W15)を使っているときは**その SHA を出す**(切替はファイルの有無で
        決まるので、どの版の文面で走ったかはこの値でしか特定できない=manifest へ記録する)。
        """
        frozen = "".join(
            f" {k}={v[:16]}" for k, v in sorted(self.assets.frozen_sources.items())
        )
        return (
            f"[perception.renderer] renders={self.renders} "
            f"cache_hit_rate={self.cache_hit_rate:.3f} "
            f"(hits={self.cache_hits} misses={self.cache_misses}) "
            f"truncated_channels={self.truncation_count} "
            f"template_sha256={T.template_sha256()[:16]}"
            f"{frozen}"
        )


# ------------------------------------------------------------------ 補助
def person_word(agent_id: int) -> str:
    """個体 id → 観測に出る人 ID の表層(``P-17``)。

    ``B5.near_person`` の ``P-<id>(未知/知人)`` と**同じ表層**にする(行動契約書 §1-2 の
    「対象: 人ID」・``llm.contract`` の ``_PERSON_RE`` が読む形)。
    """
    return f"P-{int(agent_id)}"


def _activity_word(code: int) -> str:
    return ACTIVITY_WORDS[code] if 0 <= code < len(ACTIVITY_WORDS) else ACTIVITY_WORDS[0]


def _cell_index(cell: np.ndarray, n_cells: int) -> dict[str, np.ndarray]:
    """セル → 在席個体の CSR(1 tick 1 回・ベクトル演算)。"""
    c = np.asarray(cell, dtype=np.int64)
    order = np.argsort(c, kind="stable")
    sorted_c = c[order]
    idx = np.arange(n_cells, dtype=np.int64)
    pos = np.empty(order.size, dtype=np.int64)  # 逆置換: 個体 → order 上の位置(C7)
    pos[order] = np.arange(order.size, dtype=np.int64)
    return {
        "cell_order": order,
        "cell_start": np.searchsorted(sorted_c, idx, side="left"),
        "cell_end": np.searchsorted(sorted_c, idx, side="right"),
        "cell_pos": pos,
    }
