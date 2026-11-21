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

〔第 1 期 1-2 知覚の分離(決定 10-12 §1-13)〕 描画は「状態 → 知覚の事実 ``perception.facts.Percept`` → 文」の 2 段。
``Renderer.perceive`` が状態(個体 SoA・世界・層の口)を読んで ``Percept`` を作り、``Renderer.render_percept`` が
``Percept`` だけから B0〜B6 を描く(文はその描き方の 1 つ=``Renderer.draw``)。``render`` は 2 つを続けて呼ぶ口のまま
(描画のバイトは 1-2 の前と同じ=``tests/perception/facts/test_render_from_percept_bytes.py`` と byte-check 19 構成)。
描く側が引くのは、``Percept`` と、状態でない物(テンプレ・知覚の静的資産=名・帯・凍結文・店の営業時間と値段・時計の関数)と、
キャッシュ(セル・刻みで決まる事実を描いた文)だけ。残した直接読みは記録
``docs/bench/analysis/wallbounce-1012/p12/README.md`` の表(B4b の文は ``prepare_tick`` が描いた物をセルで引く)。

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
- 〔A48・第347〕天候の行が W13 に無い日付・時刻は**止める**(黙って埋めない=その時刻の最頻値の補いは消した)。
  **合成の世界**(試験用)だけは決まった天気(晴・日照は時から・暑さ「やや暑い」)を宣言して使い、manifest の
  ``weather.declared`` に出す(体の側の体感は 5 の固定=見せる暑さと 1 段ずれる。直していない)。
- **W14/W15 の凍結静的文への切替**(C5): ``world_dir`` に ``w14_signage.parquet`` /
  ``w15_cell_static.parquet`` が在ればその文面を使い、無ければ従来の合成文へ落ちる
  (**テンプレ本体と ``template_sha256`` は不変**)。凍結文の置き場所は
  W14 → ``B2.signage`` の本文(§3.2 の 25 tok 枠)・W15 → ``B2.visible`` の ``{items}``。
  W15 を B2 に**足す**と群予算(B2+B4+B4b ≤250)を超えるので、可視物リストを**置き換える**
  形にした。W15 側の上限は 45 tok(= B2 ブロック予算 150 − 実資産での他行最大)で、
  仕様 §1 W15 の「150 tok」は B2 ブロック全体の予算と読む(=**親判断待ち**・〔11-03 棚卸し A §4-2〕未決のまま=仕分け待ち)。
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

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, ClassVar, Final, Mapping, Sequence
import numpy as np
from shibuya.foundation.vocab.agent_codes import (
    INTENT_NONE,
    INTEROCEPTION_FIELDS,
    INTERO_UP_EDGES,
    Activity,
    ActivityKind,
    ResultCode,
)
from shibuya.foundation.hashing import blake3_hex, blake3_u64, xxh64
from shibuya.foundation.text import channels as ch
from shibuya.foundation.text import hashes as H
from shibuya.foundation.text import normalize as N
from shibuya.foundation.text import templates as T
from shibuya.foundation.text.salience import SalientItem, rank_by_saliency
from shibuya.foundation.ports.percept import (
    BodyView,
    IntentView,
    Percept,
    SceneView,
    SeenObject,
    SeenPerson,
    SelfView,
    Sound,
    TimeView,
    WakeView,
)
from shibuya.world.model.assets import CELL_SIZE_M, WorldAssets, array_sha256, file_sha256
from shibuya.world.model.state import LANDMARK_CATS, World
from shibuya.foundation.time_consts import MINUTES_PER_HOUR, NS_PER_SECOND, SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from shibuya.foundation.text.percept_words import (
    NAMED_CLOSED_FALLBACK_NAME,
    activity_line,
    named_closed_note,
    near_person_text,
)

__all__ = [
    "DEFAULT_START_DATETIME", "SYNTHETIC_WEATHER_NOTE", "WALKABLE_FRACTION_SYNTHETIC", "STREET_POINT_AREA_M2",
    "PerceptionAssets",
]


#: 既定の世界内開始日時(W13 の最初の日=2026-07-28)。``clock_fn`` を渡さないときに使う。
DEFAULT_START_DATETIME: Final[datetime] = datetime(2026, 7, 28, 0, 0)

#: 〔A48・第347〕合成の世界(試験用)の決まった天気の宣言(manifest の ``weather.declared`` の ``note``)。値は
#: :meth:`PerceptionAssets.synthetic` の表(A48 の前の表のまま)。体の側の体感の固定との 1 段のずれは直していない。
SYNTHETIC_WEATHER_NOTE: Final[str] = (
    "合成の世界(試験用)の決まった天気: 天候は晴・日照は時から(5〜18 時は日中・19 時からは日没後・4 時までは夜明け前)・"
    "暑さは「やや暑い」。体の側の体感は 5 の固定(気象の資産が無い世界の値)で、見せる暑さと 1 段ずれる(直していない)。"
)

#: 第 1 期 1-2: 通しの時刻[ns] の換算(時計の原点との差 ÷ 1 µs × 1 µs の ns)。
_ONE_MICROSECOND: Final[timedelta] = timedelta(microseconds=1)
_NS_PER_MICROSECOND: Final[int] = NS_PER_SECOND // 1_000_000
#: 合成世界の歩行可能面積の割合(expedient)。
WALKABLE_FRACTION_SYNTHETIC: Final[float] = 0.15
#: W10 街路点 1 点が代表する面積[m²](2.5 m 格子)。
STREET_POINT_AREA_M2: Final[float] = 6.25



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
    #: 〔A48・第347〕時 → (天候, 日照, 暑さ)=**合成の世界だけ**の宣言した決まった天気(:data:`SYNTHETIC_WEATHER_NOTE`)。
    #: 実データの資産では空(前の「365 日のその時の最頻値」の補いの表 ``weather_by_hour`` は消した)。
    declared_weather_by_hour: Mapping[int, tuple[str, str, str]]
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
    #: 10e(B0): 知覚が読んだ騒音の地図(W10 の 3 本)と天気(W13 の時別)のファイル → sha256、集約後のセル別の段の
    #: 補助の指紋 ``noise_stage_cells``。``engine.run`` が manifest の ``frozen_sources`` に ``perception:`` を付けて写す
    #: (世界の側 ``world:`` と同じ値なら、2 つの読み手が同じ地図を読んだ=10e B0)。
    asset_sources: Mapping[str, str] = field(default_factory=dict)

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

    @property
    def is_synthetic(self) -> bool:
        """〔A48〕合成の世界(試験用)の資産か(決まった天気を宣言して使う)。"""
        return self.source == "synthetic"

    def weather(self, when: datetime) -> tuple[str, str, str]:
        """世界内日時 → (天候, 日照, 暑さ)。

        〔A48・第347〕W13 の表に ``(日付, 時)`` の行が無いとき、合成の世界は宣言した決まった天気
        (``declared_weather_by_hour``)を返し、それ以外は日付と時を書いて止める(``ValueError``=黙って埋めない)。
        前の「その時の最頻値」の補いは消した(旧値の再現は安定版のタグ)。〔検収 低-6〕合成の世界でも、宣言した表にその時が
        無ければ止める(宣言していない定数で埋めない=宣言の表は 0〜23 時がそろうので今の道では当たらない)。
        """
        key = (when.strftime("%Y-%m-%d"), int(when.hour))
        got = self.weather_by_date_hour.get(key)
        if got is not None:
            return got
        if self.is_synthetic:
            got = self.declared_weather_by_hour.get(key[1])
            if got is not None:
                return got
        raise ValueError(
            f"天気の行が無い: {key[0]} {key[1]} 時(W13 の時の表・合成の世界は宣言の表・黙って埋めない=A48)"
        )

    def missing_weather_hours(self, date: str) -> tuple[int, ...]:
        """〔A48〕``date``(``YYYY-MM-DD``)のうち W13 の時の表に行の無い時(0〜23・昇順)。合成の世界は空(宣言の天気)。"""
        if self.is_synthetic:
            return ()
        d = str(date)[:10]
        return tuple(h for h in range(24) if (d, h) not in self.weather_by_date_hour)

    def require_weather_days(self, dates: Sequence[str]) -> None:
        """〔A48〕日付の列のどの日も 24 時の行がそろうかを確かめる(欠けたら日付と時を書いて止める=黙って埋めない)。

        組み立て(引きうる再生日の全部)と日の頭(その日に引いた再生日)が呼ぶ。合成の世界は何もしない。
        逐次ループ宣言: 日付の数 × 24 時(組み立てに 1 回=W13 で 365 × 24・日の頭に 1 日分)。
        """
        if self.is_synthetic:
            return
        missing = [(str(d)[:10], hs) for d in dates if (hs := self.missing_weather_hours(str(d)))]
        if missing:
            head = "・".join(f"{d} の {','.join(map(str, hs))} 時" for d, hs in missing[:5])
            more = f" ほか {len(missing) - 5} 日" if len(missing) > 5 else ""
            raise ValueError(f"天気の行が無い: {head}{more}(W13 の時の表・黙って埋めない=A48)")

    def declared_weather_manifest(self) -> dict[str, object]:
        """〔A48〕合成の世界の宣言した決まった天気(manifest の ``weather.declared``)。"""
        return {
            "note": SYNTHETIC_WEATHER_NOTE,
            "by_hour": [list(self.declared_weather_by_hour[h]) for h in sorted(self.declared_weather_by_hour)],
        }

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
            # 〔A48〕合成の世界の宣言した決まった天気(値は A48 の前の表のまま=SYNTHETIC_WEATHER_NOTE)
            declared_weather_by_hour={
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
    def load_or_synthetic(
        cls, path: str | Path | None, world: World
    ) -> "PerceptionAssets":
        """資産があれば読み、無ければ合成へ落ちる(``World.load_or_synthetic`` と同じ作法)。"""
        if cls.available(path) and world.assets.source != "synthetic":
            return cls.load(path, world)  # type: ignore[arg-type]
        return cls.synthetic(world)

    @classmethod
    def load(
        cls, path: str | Path, world: World
    ) -> "PerceptionAssets":
        """``data/world/v2`` から読む(W2/W6/W8/W10/W11/W13)。

        Note:
            逐次ループ宣言(P4)3: 可視性表の行数ぶんの集約 1 本(**起動時 1 回**)。
        """
        import pyarrow.parquet as pq

        p = Path(path)
        asset_sources: dict[str, str] = {}
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
        area, has_street, ns_day, ns_night = _street_aggregate(p, world.assets, n, sources=asset_sources)

        # ---- W14/W15 の凍結静的文(在れば使う・無ければ従来の合成文) ----
        frozen_sources: dict[str, str] = {}
        poi_signage = _load_frozen_text(
            p, "w14_signage.parquet", "poi_id", [str(s) for s in poi["poi_id"]], frozen_sources
        )
        cell_static = _load_frozen_text(
            p, "w15_cell_static.parquet", "place_id", list(place_ids), frozen_sources
        )

        # ---- W13 天候 ----
        f13 = p / "w13_weather_hourly.parquet"
        asset_sources[f13.name] = file_sha256(f13)
        w13 = pq.read_table(
            f13,
            columns=["date", "hour", "weather", "daylight", "heat_stage"],
        ).to_pydict()
        by_dh: dict[tuple[str, int], tuple[str, str, str]] = {}
        for d, h, w, dl, hs in zip(
            w13["date"], w13["hour"], w13["weather"], w13["daylight"], w13["heat_stage"]
        ):
            key = (str(d)[:10], int(h))
            val = (str(w), str(dl), str(hs))
            by_dh[key] = val
        # 〔A48・第347〕その時の最頻値の補いの表は作らない(行が無ければ ``weather`` が止める)

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
            declared_weather_by_hour={},
            noise_stage_day=ns_day,
            noise_stage_night=ns_night,
            poi_signage=poi_signage,
            cell_static=cell_static,
            frozen_sources=frozen_sources,
            asset_sources=asset_sources,
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
    path: Path, assets: WorldAssets, n_cells: int, *,
    sources: dict[str, str] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """W10 街路点 → (歩行可能面積, 街路の有無, 昼騒音段, 夜騒音段)。全てベクトル演算。

    10e(B0): 読んだファイルの sha256 と集約後の騒音の段の指紋(``noise_stage_cells``)を ``sources`` に書く。
    """
    import pyarrow.parquet as pq

    root = Path(path)
    f_pts = root / "w10_street_points.parquet"
    if sources is not None:
        sources[f_pts.name] = file_sha256(f_pts)
    d = pq.read_table(f_pts, columns=["x", "y", "band"]).to_pydict()
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
    read_both = True
    for name, out in (("w10_noise_stage_day.npy", ns_day), ("w10_noise_stage_night.npy", ns_night)):
        f = root / name
        if not f.exists():
            read_both = False
            continue
        if sources is not None:
            sources[name] = file_sha256(f)
        stage = np.load(f)
        # セル×段の度数 → 最頻値(段は 0..3)
        n_stage = 4
        flat = cell_of_point[valid] * n_stage + np.clip(stage[valid].astype(np.int64), 0, n_stage - 1)
        tab = np.bincount(flat, minlength=n_cells * n_stage).reshape(n_cells, n_stage)
        out[:] = tab.argmax(axis=1).astype(np.uint8)
    if sources is not None and read_both:
        sources["noise_stage_cells"] = array_sha256(ns_day, ns_night)
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
    #: 第 1 期 1-2: 時刻の見方の材料(その日の中の秒・通しの時刻[ns]・暦の日の種類=``day_kind_fn`` が無ければ None)。
    tod_s: int = 0
    t_ns: int = 0
    day_kind: str | None = None
    #: 第 1 期 1-2: セル → その場の事実(``SceneView``・その刻みに初めて引いたときに作る=刻みの中の一時)。
    scenes: dict = field(default_factory=dict)
    #: 第 1 期 1-2: B3 のキャッシュの鍵 → その刻みの ``TimeView``(同じ刻みの全員で同じ物)と、``TimeView`` → B3 の文
    #: (描く入力の値で引く=刻みの中の一時のキャッシュ)。
    time_views: dict = field(default_factory=dict)
    b3_text: dict = field(default_factory=dict)
    #: 〔第 1 期 1-8b〕届いた発話の目印 → (話し手, 本文)(``perceive`` が ``heard_fn`` から受け取った物=刻みの中の一時・
    #: ``render_percept`` が B6 の末尾に描く材料。腕 off のランは空のまま)。
    heard: dict = field(default_factory=dict)
    #: 〔1-8b 検収 低8〕届いた発話を口へ報告した体(同じ刻みに同じ体を 2 度数えない)。
    heard_reported: set = field(default_factory=set)
    #: 〔第 2 期 2-2 段 11a〕腕 ``--proximity distance`` の ``engine.proximity.NearView``(判定の規則・この刻みの近傍の索引・
    #: 気づいた印の読み口=知覚の層は engine を import しない=形だけ使う)。既定 None=今の B5。
    near: object = None


#: B5 近接行の**距離の同点**の切り方(第300 Q107・小さいもの①)。``hash``(既定)= run_salt の決定論ハッシュ
#: (観る体 × 相手の組)で撹拌 / ``id``= 旧挙動(セル内の並び=体の行番号の順に近い k 人で切る=旧 golden)。
#: 同点が k 人目の境で起きない描画は**両方で 1 バイトも変わらない**(採る人の集合が一意)。
NEAR_TIEBREAKS: Final[tuple[str, ...]] = ("hash", "id")
#: 同点の撹拌の鍵の用途タグ(``core.hashing`` の 3 バイトの規約に揃える=他の用途と同じ値にならない)。
_NEAR_TIE_TAG: Final[bytes] = b"nt\x00"
_U64_MASK: Final[int] = (1 << 64) - 1


def near_tie_salt64(run_salt: bytes) -> int:
    """``blake3(run_salt ‖ b"nt\\x00")`` の先頭 8 バイト(u64)。1 ランに 1 回だけ作る。"""
    return int(blake3_u64(bytes(run_salt) + _NEAR_TIE_TAG))


def near_tie_keys(salt64: int, observer: int, ids: np.ndarray) -> np.ndarray:
    """観る体 ``observer`` から見た相手 ``ids`` の撹拌鍵(u64・splitmix64 の仕上げ・配列演算)。

    **同点の順だけ**に使う(値そのものに意味は無い)。観る体ごとに順が変わる(同じ相手が全員から
    いつも先に選ばれることはない)・同じ salt・同じ組なら常に同じ(テープから再現できる)。
    tick は混ぜない(位置が変わらない間は同じ人が見え続ける=宣言)。
    """
    base = (int(salt64) ^ ((int(observer) * 0x9E3779B97F4A7C15) & _U64_MASK)) & _U64_MASK
    with np.errstate(over="ignore"):
        x = np.asarray(ids, dtype=np.int64).astype(np.uint64) * np.uint64(0xBF58476D1CE4E5B9)
        x ^= np.uint64(base)
        x ^= x >> np.uint64(30)
        x *= np.uint64(0xBF58476D1CE4E5B9)
        x ^= x >> np.uint64(27)
        x *= np.uint64(0x94D049BB133111EB)
        x ^= x >> np.uint64(31)
    return x


#: B5 近接行の**並び**(第304 Q130・小さいもの 第 2 批①)。``distance``(既定)= 距離の昇順・同点は
#: ``near_tiebreak`` の順(``hash``= ``near_tie_keys``・``id``= 行番号)/ ``id``= 旧挙動(行番号の昇順=旧 golden)。
#: 焦点の先頭・知人の常時掲載・会話の参加者の掲載は両方で同じ。文面は変えない。
NEAR_ORDERS: Final[tuple[str, ...]] = ("distance", "id")


def check_near_order(mode: str) -> str:
    if str(mode) not in NEAR_ORDERS:
        raise ValueError(f"near_order は {NEAR_ORDERS} のどれか(いま {mode!r})")
    return str(mode)


def check_near_tiebreak(mode: str) -> str:
    if str(mode) not in NEAR_TIEBREAKS:
        raise ValueError(f"near_tiebreak は {NEAR_TIEBREAKS} のどれか(いま {mode!r})")
    return str(mode)


class PerceptScene:
    """知覚の場面(世界の側=前計算・知覚の事実を作る)。"""

    def __init__(self, world, agents, assets, clock_fn, seed, *, acquaintances, watched_by, signage_enabled,
                 near_tiebreak, near_salt, near_order, day_kind_fn) -> None:
        """世界の側の欄を置く。"""
        self.world = world
        self.agents = agents
        self.assets = assets if assets is not None else PerceptionAssets.synthetic(world)
        self.clock_fn = clock_fn or (lambda t: DEFAULT_START_DATETIME + timedelta(minutes=int(t)))
        self.acquaintances = dict(acquaintances or {})
        self.watched_by = watched_by
        self.signage_enabled = bool(signage_enabled)
        #: 記憶 第 1 段 6b: 想起の口 ``(体, tick, 起床条件, 招待者) → [RecallItem…]``(``engine.run`` が
        #: ``--memory on`` のランだけ差し込む)。``None``(既定)=記憶の行を描かない=1 バイトも変わらない。
        self.memory_recall: Callable[[int, int, int, int], Sequence[object]] | None = None
        #: 小さいもの①(第300 Q107): 近接行の距離の同点の切り方と、撹拌の salt(u64)。
        self.near_tiebreak = check_near_tiebreak(near_tiebreak)
        self.near_order = check_near_order(near_order)
        #: 並べた近接行のうち、距離が同じ人が 2 人以上いた描画の数(並びの同点を鍵で切った=計測の口)。
        self.near_order_ties = 0
        if near_salt is None:
            _text = f"i:{int(seed)}" if not isinstance(seed, str) else f"s:{seed}"
            near_salt = bytes.fromhex(blake3_hex(f"{_text}\x1fengine".encode("utf-8"), length=16))
        self._near_salt64 = near_tie_salt64(near_salt)
        #: 同点を撹拌で切った描画の回数・そのときの同点の人数の延べ(``hash`` のランだけ数える=計測の口)。
        self.near_tie_breaks = 0
        self.near_tie_candidates = 0

        self._tickc = _TickCache()
        #: **注意の焦点**の欄(C9b G4)。``attention_columns`` のランだけ在る配列を 1 度だけ
        #: 掴む(``AgentState`` の配列は freeze/thaw で差し替わらない)。``None``= 焦点の無い
        #: ラン=**B5 の描画は 1 バイトも変わらない**。
        #: **B2(地物)は共有ブロック**(§2.4 ⑧ + §5 の共有 prefix)なので焦点で並べ替えない
        #: ——地物の焦点は描画に出さない(親へ報告済みの空欄)。
        self._focus_target: np.ndarray | None = (
            agents.focus_target if getattr(agents, "attention_columns", False) else None
        )
        #: C10 8a: 関係辺の知人の口 ``(体, tick) → 相手の配列``(``--relations on`` のランだけ・既定 None=
        #: 構築時の ``acquaintances``=空=1 バイトも変わらない)。
        self.acquaintance_fn: Callable[[int, int], Sequence[int]] | None = None
        #: C10 8a(3 人会話の口): ``体 → 会話の参加者``(``--conv-max-participants 3`` のランだけ・既定 None)。
        self.session_partner_fn: Callable[[int], Sequence[int]] | None = None
        #: 個体 → (知人の集合, 知人の id 配列)。**構築時に固定**なので 1 度作れば使い回せる(C7)。
        self._acq_cache: dict[int, tuple[frozenset[int], np.ndarray]] = {}
        #: 10d: 鍵は ``(世界内の日付, 5 分帯)``(5 分帯だけだと複数日のランで 0 日目の天候の行を 2 日目も使い回す)。
        #: 第 1 期 1-2: 値は描いた文ではなく(天候, 日照, 暑さ)の語(文は刻みの中だけ ``_TickCache.b3_text`` で引く)。
        self._b3_cache: dict[tuple, tuple[str, str, str]] = {}
        #: 段 2c Q25: 名指しの即時閉店の補足(体 → (POI, 失敗の tick, 開店の分))。``engine.run`` が
        #: 意図の層のあるランだけ差し込む(``None``=従来どおり=描画は 1 バイトも変わらない)。
        self.named_closed_lookup: Callable[[int], tuple[int, int, int] | None] | None = None
        #: 10d 検収 D1: B3 の天候を引く日(``YYYY-MM-DD``)を返す口。``engine.run`` が世界過程の再生の実日
        #: (``environment.replay_date``=体の暑さと同じ源)を差し込む。``None`` か空なら今までどおり暦の日付で引く。
        self.weather_date_fn: Callable[[], str | None] | None = None
        #: 10e(B6): 天気の規則 ``calendar`` で ``engine.run`` が差し込む口(世界内日時 → (天候, 日照, 暑さ) の語・
        #: 天候=再生日の行・日照=暦の日付・暑さ=体感温度と同じ段)と、キャッシュの鍵(再生日・暦の日付)。``None``=今まで。
        self.weather_words_fn: Callable[[datetime], tuple[str, str, str]] | None = None
        self.weather_words_key_fn: Callable[[datetime], tuple] | None = None
        #: 〔A48・第347〕世界過程の無いランで、組み立てが置く「天気の日を引いて B3 の語を出すだけの環境の過程」(体感温度は
        #: 書かない)。日の頭の張り直しがその日の再生日を引き直し、manifest の ``weather`` もここから書く。``None``=置かない
        #: (世界過程のあるランは世界過程の環境の過程を使う)。参照だけ(状態は資産・暦・日番号・環境の seed から作り直せる)。
        self.weather_env: object | None = None
        #: 第 1 期 1-2: 暦の日の種類を返す口(``Percept.time_view.day_kind``・刻みに 1 回引く・描画の文は読まない)。
        self.day_kind_fn: Callable[[int], str] | None = day_kind_fn
        self.named_closed_notes = 0
        #: 4 段目(M17 露出): 看板行が載った (体, POI) の控え(``engine.run`` が tick ごとに取り出す)。
        #: ``None``=控えない(既定)。
        self.signage_exposures: list[tuple[int, int]] | None = None
        #: 〔第 1 期 1-8b 発話の口〕届いた発話を受け取る口 ``(体, 刻みの番号) → ((目印, 話し手, 本文), …)``(組み立てが腕 on の
        #: ランだけ ``SpeechPort.take_heard`` を差し込む=呼ぶと未読から外れる)。``None``(既定)=``Percept.heard_speech`` は
        #: None のまま=描画は 1 バイトも変わらない。
        self.heard_fn: Callable[[int, int], Sequence[tuple[tuple[int, int], int, str]]] | None = None
        #: 〔第 6 期 6-4 C1〕連絡の道具の口 ``Percept → Percept``(組み立てが腕 c1 のランだけ ``ContactLayer.percept_hook`` を
        #: 差し込む=目と心の向き・道具の状態を知覚の事実に入れる)。``None``(既定)=描画は 1 バイトも変わらない。
        self.contact_fn: Callable[[Percept], Percept] | None = None

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
        activity_rows: Mapping[int, Sequence[tuple[str, int]]] | None = None,
        near: object = None,
        los_stage: np.ndarray | None = None,
    ) -> None:
        """この tick のセル配列とハッシュを作る(**セル数ぶんの xxh64 が 1 本**)。

        Args:
            queues: B4b の材料 ``(POI, 表示名, 人数)`` の列
                (``engine.processes.crowd.CrowdProcess.queue_rows``)。セルあたり上位 1 件を
                「<店名>の行列に<人数>人」として ``B4b.near`` に載せる。
            activity_rows: **二層の段 2** の B4b の材料「セル → ((活動文, 人数), …)」
                (``engine.activity.ActivityLayer.cell_rows``)。``activity_line`` の 1 行を
                行列の行の**後**に足す(B4b の予算 40 tok に収まるときだけ)。行列も活動も無い
                セルは従来の固定文言。``None``(既定)では 1 バイトも変わらない。
                **起床条件 (i) の欄(B4 ダイジェスト)には混ぜない**(活動の変化を場所の変化
                として起床させない=新しい起床の源を足さない・expedient)。固定枠の描画だけに
                載せる(単一ランキングの腕には載せない・expedient)。
            near: 〔第 2 期 2-2 段 11a〕腕 ``--proximity distance`` の ``NearView``(規則・この刻みの索引・印の読み口)。渡すと B5 の
                近接行を「同じ層・半径の中・同じ B5 の単位」の体から選ぶ(:meth:`_nearby_people_distance`)。``None``
                (既定)では 1 バイトも変わらない。
            los_stage: 〔段 5-1b〕密度の段(Fruin の LOS)を外から渡す(nav1 のラン=``world.cells.density_stage``=
                ``NavSpace.per_m2`` の推定=段と Kladek と同じ 1 つの密度)。``None``(legacy)は今の ``density ÷ 歩ける面積``。
        """
        w = self.world
        n = w.n_cells
        when = self.clock_fn(int(tick))
        if los_stage is not None:
            los = np.asarray(los_stage, dtype=np.uint8).copy()
        else:
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

        if activity_rows:
            b4b = self._merge_activity_lines(b4b, activity_rows)
        rows = H.b4_field_row(los, ns, fl, digest)
        # C7: セル順の連続座標(1 tick 1 回の gather)。個体数ぶんの 3 配列
        # =24 byte/体(390,067 体で 9.4 MB)。1 呼あたりのセル在席者ぶんの gather を消す。
        idx = _cell_index(self.agents.cell, n)
        xy_all = np.asarray(self.agents.xy, dtype=np.float64)
        order = idx["cell_order"]
        # 第 1 期 1-2: 時刻の見方の材料(通しの時刻=時計の原点からの差・その日の中の秒・暦の日の種類)
        since = when - self.clock_fn(0)
        self._tickc = _TickCache(
            tick=int(tick),
            when=when,
            band5=N.time_band(when),
            tod_s=int(when.hour) * SECONDS_PER_HOUR + int(when.minute) * SECONDS_PER_MINUTE + int(when.second),
            t_ns=int(since // _ONE_MICROSECOND) * _NS_PER_MICROSECOND,
            day_kind=(str(self.day_kind_fn(int(tick))) if self.day_kind_fn is not None else None),
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
            near=near,
            **idx,
        )

    @property
    def b4_field_rows(self) -> np.ndarray:
        """直近の ``prepare_tick`` が作った B4 描画欄 ``(n_cells, 4)`` int32。

        **エンジンの変化検出器(起床条件 (i))はこの 1 本を読む**。描画と検出が同じ欄を見るので
        「(i) が鳴らないのに文面が変わる」取りこぼしが構造的に 0 になる(§2.2/§5 の三役)。
        """
        return self._tickc.b4_field_rows

    # ---------------------------------------------------------- 第 1 期 1-2: 状態 → 知覚の事実
    def perceive(
        self,
        agent_id: int,
        step: int,
        wake_reason: int | str = 3,
        last_result: int | None = None,
        last_action: str | None = None,
        inviter: int | None = None,
    ) -> Percept:
        """状態 → 1 体・1 刻みの知覚の事実(``facts.Percept``)。``step``=通しの刻みの番号(``render`` の ``tick`` と同じ値)。
        ほかの引数は ``render`` と同じ。

        読むもの: 個体 SoA(セル・種別・内受容・所持金・手・行為・直前の結果・意図・近くの人の位置と行為)・刻みの前計算
        (``prepare_tick``)・層の口(知人・会話の参加者・名指しの閉店・想起・天気)。副作用は 1-2 の前の ``render`` と同じ
        回数・同じ条件・同じ順(看板の注視の抽選と計数 → 露出の控え → 閉店の 1 句 → B3 の命中の計数と天気 → 近接の同点の
        計数 → 想起)。描画の文は作らない。

        Note:
            逐次ループ宣言(P4): 1 起床につき 1 回(近接は ``_nearby_people`` の宣言のまま)。
        """
        if self._tickc.tick != int(step):
            self.prepare_tick(int(step))
        tc = self._tickc
        a = self.agents
        i = int(agent_id)
        cell = int(a.cell[i])
        # D-59 (b): 看板の注視ゲート(§4 段1)。既定 p_see=1.0 では常に True=抽選も引かない。
        seen = self._signage_seen(i, cell, int(step))
        # 4 段目(M17 露出): 注視ゲートを通って B2 に看板行が載った POI を控える(``--familiarity on``
        # のランだけ ``engine.run`` が list を差し込む=既定 None では 1 行も通らない・描画は不変)。
        if self.signage_exposures is not None and seen:
            _sp = self._signage_poi(cell)
            if _sp >= 0:
                self.signage_exposures.append((i, int(_sp)))
        scene = self._scene(cell, tc)
        objects = scene.with_signage if seen else scene.objects
        reg = a.registry
        vals = tuple(int(reg.field(nm)[i]) for nm in INTEROCEPTION_FIELDS)
        stages = tuple(sum(1 for e in INTERO_UP_EDGES if v >= e) for v in vals)
        me = SelfView(
            kind=int(a.kind[i]), money=int(a.money[i]), hands_full=int(a.holdings[i]) > 0,
            activity=int(a.activity[i]),
        )
        wake = self._wake_view(i, cell, wake_reason, last_result, last_action, inviter)
        tv = self._time_view(tc)
        people = tuple(self._nearby_people(i, cell, tc))
        intent = self._intent_view(i)
        memories: tuple[object, ...] | None = None
        if self.memory_recall is not None:
            # 記憶 第 1 段 6b: 想起の口(on のランだけ)。0 件でも空の列(描画は行を出さない)
            cond = int(wake_reason) if isinstance(wake_reason, (int, np.integer)) else -1
            memories = tuple(self.memory_recall(i, int(step), cond, -1 if inviter is None else int(inviter)))
        heard: tuple[tuple[int, int], ...] | None = None
        if self.heard_fn is not None:
            # 第 1 期 1-8b: 届いた発話(相手の次の入力=この呼び出し・1 回だけ)。目印を Percept に・本文は刻みの中の控えに
            got = tuple(self.heard_fn(i, int(step)))
            for eid, who, text in got:  # 逐次ループ宣言: 届いた発話の数ぶん(≤ 3)
                tc.heard[(int(eid[0]), int(eid[1]))] = (int(who), str(text))
            heard = tuple((int(e[0]), int(e[1])) for e, _w, _t in got)
        p = Percept(
            agent_id=i, step=int(step), t_ns=int(tc.t_ns), cell=cell, self_view=me,
            seen_objects=objects, seen_people=people, sounds=scene.sounds, time_view=tv,
            body=BodyView(*vals, *stages), wake=wake, intent=intent, memories=memories,
            signage_shown=bool(seen),
            watched_n=0 if self.watched_by is None else int(self.watched_by[i]),
            scene=scene, heard_speech=heard,
        )
        if self.contact_fn is not None:  # 〔第 6 期 6-4 C1〕腕 c1 のランだけ: 目と心の向き・道具の状態の形にする
            p = self.contact_fn(p)
        return p

    def _scene(self, cell: int, tc: _TickCache) -> SceneView:
        """セル → その場の事実(``SceneView``)。刻みの中で 1 回だけ作り ``tc.scenes`` に置く(刻みの頭で空になる)。

        材料: 知覚の静的資産(見える店・目印の名)と刻みの前計算(密度の段・流れ・騒音の段・顕著な出来事・近景の項目・
        B4 の欄の指紋)。逐次ループ宣言(P4): 見える物の数ぶん(≤ 12)。
        """
        got = tc.scenes.get(int(cell))
        if got is not None:
            return got
        A = self.assets
        objs: list[SeenObject] = []
        if 0 <= cell < A.n_cells:
            for j in A.visible_poi[cell]:
                objs.append(SeenObject(int(j), "poi", name=str(A.poi_name[int(j)])))
            for nm in A.visible_landmark[cell]:
                objs.append(SeenObject(-1, "landmark", name=str(nm)))
        in_area = 0 <= cell < tc.los_stage.size
        j = int(self._signage_poi(cell))
        objects = tuple(objs)
        if j >= 0:
            names = A.poi_name
            sign = SeenObject(j, "signage", name=str(names[j]) if 0 <= j < len(names) else "")
            with_signage = objects + (sign,)
        else:
            with_signage = objects
        sc = SceneView(
            cell=int(cell),
            in_area=bool(in_area),
            objects=objects,
            signage_poi=j,
            crowd_stage=int(tc.los_stage[cell]) if in_area else 0,
            flow=int(tc.flow[cell]) if in_area else 0,
            sounds=(Sound("noise", int(tc.noise_stage[cell]) if in_area else 0),),
            salient=tuple(str(s) for s in tc.salient.get(int(cell), ())) if in_area else (),
            near_items=tuple(str(s) for s in tc.b4b_items.get(int(cell), ())) if in_area else (),
            field_hash=int(tc.b4_field_hash[cell]) if 0 <= cell < tc.b4_field_hash.size else -1,
            with_signage=with_signage,
        )
        tc.scenes[int(cell)] = sc
        return sc

    def _wake_view(
        self, i: int, cell: int, wake_reason: int | str, last_result: int | None, last_action: str | None,
        inviter: int | None,
    ) -> WakeView:
        """起きた理由と直前の結果(B6 の材料)。観測値は 1-2 の前の ``_observation`` と同じ条件でだけ引く。"""
        a = self.agents
        code = int(a.last_result[i]) if last_result is None else int(last_result)
        known = not (int(a.last_result_tick[i]) < 0 and last_result is None)
        cheapest, nxt, note = 0, None, ""
        if known and code != int(ResultCode.OK):
            if code == int(ResultCode.MONEY_SHORT):
                cheapest = self._cheapest_price(cell)
            elif code == int(ResultCode.CLOSED):
                note = self._named_closed_text(i)
                if not note:
                    nxt = self._next_open_hour(cell)
        reason = int(wake_reason) if isinstance(wake_reason, (int, np.integer)) else wake_reason
        return WakeView(
            reason=reason, inviter=None if inviter is None else int(inviter), result=code, result_known=known,
            last_action=last_action, cheapest_price=int(cheapest), next_open_hour=nxt, closed_note=note,
        )

    def _intent_view(self, i: int) -> IntentView | None:
        """意図を持つ体の意図(持たなければ None)。SoA の意図の欄を読むだけ。"""
        arrays = self.agents.registry.arrays
        if "intent_action" not in arrays:
            return None
        code = int(arrays["intent_action"][i])
        if code == INTENT_NONE:
            return None
        return IntentView(
            action=code, target_kind=int(arrays["intent_kind"][i]), target=int(arrays["intent_target"][i]),
        )

    def _time_view(self, tc: _TickCache) -> TimeView:
        """刻み → 時刻の見方(``TimeView``)。天候・日照・暑さは B3 のキャッシュの鍵ごとに 1 回だけ引く(1-2 の前の B3 と
        同じ鍵・同じ命中の計数=1 描画に 1 回)。時と分は 5 分に切り捨て(鍵の 5 分帯と同じ値)。"""
        wdate = None
        if self.weather_words_fn is not None:  # 10e(B6): 天気=再生日・太陽=暦の日付(体の暑さと同じ規則)
            key = ("calendar",) + tuple(self.weather_words_key_fn(tc.when)) + (int(tc.band5),)  # type: ignore[misc]
        else:
            # 10d 検収 D1: 天候は「その日の再生の実日」の W13 の行で引く(体の暑さ=環境の過程と同じ行)。
            # 再生の実日が無ければ(合成世界)暦の日付で引く。
            wdate = self.weather_date_fn() if self.weather_date_fn is not None else None
            key = (str(wdate) if wdate else tc.when.toordinal(), int(tc.band5))
        got = self._b3_cache.get(key)
        if got is not None:
            self.cache_hits += 1
            weather, daylight, heat = got
        else:
            self.cache_misses += 1
            if self.weather_words_fn is not None:
                weather, daylight, heat = self.weather_words_fn(tc.when)
            elif wdate:
                weather, daylight, heat = self.assets.weather(
                    datetime.strptime(str(wdate)[:10], "%Y-%m-%d").replace(hour=int(tc.when.hour))
                )
            else:
                weather, daylight, heat = self.assets.weather(tc.when)
            self._b3_cache[key] = (weather, daylight, heat)
        tv = tc.time_views.get(key)
        if tv is None or (tv.weather, tv.daylight, tv.heat) != (weather, daylight, heat):
            h, m = N.round_time_5min(tc.when)
            tv = TimeView(
                tod_s=int(tc.tod_s), day_kind=tc.day_kind, band5=int(tc.band5), hour=int(h), minute=int(m),
                weather=weather, daylight=daylight, heat=heat,
            )
            tc.time_views[key] = tv
        return tv

    def _signage_poi(self, cell: int) -> int:
        """看板(a)に使う **POI の index**(無ければ ``-1``)。

        **看板の選び方はこの 1 本**(``_signage_body`` もここを通る)なので、注視ゲートが
        抽選に使う ``poi_id`` と実際に描かれる看板は常に同じものを指す。
        """
        if not self.signage_enabled:
            return -1
        A = self.assets
        if not (0 <= cell < A.n_cells):
            return -1
        n_poi = self.world.n_poi
        for j in A.visible_poi[cell]:
            if int(j) < n_poi:
                return int(j)
        return -1

    def signage_poi_by_cell(self) -> np.ndarray:
        """セル → B2 の看板行に出す POI(``_signage_poi`` と同じ 1 件・無ければ −1)。

        4 段目(M17 露出・親決定 (f)): 「セルに入った回 × そのセルの看板」の露出を数える側
        (``engine.familiarity``)が、描画と**同じ集合**を読むための口。起動時 1 回(セル数ぶん)。
        ``signage_enabled=False``(ablation ⑥)なら全部 −1。
        """
        n = int(self.assets.n_cells)
        return np.fromiter((self._signage_poi(c) for c in range(n)), dtype=np.int64, count=n)

    def activity_class_of(self, agent_id: int) -> int:
        """体 → 活動の種別の索引(:data:`P_SEE_ACTIVITY_KINDS`・5c・宣言・親しみの層の露出の計数の鍵)。

        1. 会話の成立(``Activity.CONVERSING``)→ 連れとの会話中 2. (通話/スマホ操作中の旗は無い)
        3. 活動層のあるラン: ``activity_kind``(目的地つき移動/あたり/在店/その場・なし=その場)
        4. 活動層の無いラン: 歩行中=目的地つき移動・在店(``SHOPPING``)=在店・他=その場。
        """
        r = self.agents.registry
        act = int(r.activity[agent_id])
        if act == int(Activity.CONVERSING):
            return 5
        if "activity_kind" in r.arrays:
            k = int(r.activity_kind[agent_id])
            return {int(ActivityKind.MOVE_TO): 0, int(ActivityKind.WANDER): 1,
                    int(ActivityKind.IN_SHOP): 2}.get(k, 3)
        if act == int(Activity.MOVING):
            return 0
        if act == int(Activity.SHOPPING):
            return 2
        return 3

    def activity_classes(self, agent_ids: np.ndarray) -> np.ndarray:
        """体の配列 → 活動の種別の索引の配列(:meth:`activity_class_of` の配列版・配列演算)。"""
        a = np.asarray(agent_ids, dtype=np.int64)
        r = self.agents.registry
        act = np.asarray(r.activity)[a]
        out = np.full(a.size, 3, dtype=np.int64)
        if "activity_kind" in r.arrays:
            k = np.asarray(r.activity_kind)[a]
            out[k == int(ActivityKind.MOVE_TO)] = 0
            out[k == int(ActivityKind.WANDER)] = 1
            out[k == int(ActivityKind.IN_SHOP)] = 2
        else:
            out[act == int(Activity.MOVING)] = 0
            out[act == int(Activity.SHOPPING)] = 2
        out[act == int(Activity.CONVERSING)] = 5
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

    def _merge_activity_lines(
        self, b4b: Mapping[int, bytes], activity_rows: Mapping[int, Sequence[tuple[str, int]]]
    ) -> dict[int, bytes]:
        """行列の B4b にセルの活動の 1 行を足す(二層の段 2)。B4b 40 tok を超えるなら足さない。

        逐次ループ宣言(P4): 活動の行があるセルの数ぶん(≤ セル数)。
        """
        out = dict(b4b)
        budget = int(T.BLOCK_TOKEN_BUDGET["B4b"])
        for c, rows in activity_rows.items():
            line = activity_line(rows)
            if not line:
                continue
            prev = out.get(int(c))
            if prev is None:
                out[int(c)] = N.canonical_whitespace(line).encode("utf-8")
                continue
            merged = N.join_lines([prev.decode("utf-8"), N.canonical_whitespace(line)])
            if ch.estimate_tokens(merged) <= budget:
                out[int(c)] = merged.encode("utf-8")
        return out

    def _nearby(self, i: int, cell: int, tc: _TickCache) -> list[str]:
        """同一セル在席者から近接上位 k(密度逓減)+知人常掲を作る。"""
        return [text for text, _d in self._nearby_items(i, cell, tc)]

    def _nearby_items(self, i: int, cell: int, tc: _TickCache) -> list[tuple[str, float]]:
        """``_nearby`` の各行と**その距離[m]**(単一ランキングの視角に使う)。

        第 1 期 1-2: 選び方は ``_nearby_people``(構造のある事実=``SeenPerson``)。本メソッドはその文の形
        (``near_person_text``)と距離の組(1-2 の前と同じ値・同じ並び)。
        """
        return [(near_person_text(sp), sp.distance_m) for sp in self._nearby_people(i, cell, tc)]

    def _nearby_people(self, i: int, cell: int, tc: _TickCache) -> list[SeenPerson]:
        """同一セル在席者から近接上位 k(密度逓減)+知人常掲+会話の参加者+注意の焦点=見えた人(``SeenPerson``)。

        第 1 期 1-2: 1-2 の前の ``_nearby_items`` の本体(選び方・並び・距離は 1 ビットも変えない)。返すのは
        (id・向き=空・行為=相手の ``activity``・距離・知人か)。

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
        if tc.near is not None:  # 第 2 期 2-2 段 11a: 腕 --proximity distance(今の道は下のまま)
            return self._nearby_people_distance(i, cell, tc)
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
        if peers.size > take:
            sel = self._near_take(i, peers, d2, take)
        else:
            sel = peers
        friends, friend_ids = self._acquaintances_of(i, int(tc.tick))
        chosen_set = {int(x) for x in sel}
        if self.session_partner_fn is not None:  # C10 8a(3 人会話): 会話の参加者は同セルなら常に載せる
            sp = np.asarray(self.session_partner_fn(i), dtype=np.int64)
            sp = sp[(sp >= 0) & (sp < int(a.n)) & (sp != i)]
            if sp.size:
                ps_ = tc.cell_pos[sp]
                chosen_set |= {int(x) for x in sp[(ps_ >= lo) & (ps_ < hi)]}
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
        if focus >= 0:  # 焦点だけ先頭へ(残りの並びは id 昇順か距離順=下)
            chosen = [focus] + [x for x in chosen if x != focus]
        q = tc.cell_pos[np.asarray(chosen, dtype=np.int64)] - lo
        if 0 <= p < m:
            q = q - (q > p)  # 自分の行を外したぶん詰める
        if self.near_order == "distance" and len(chosen) > 1:
            chosen, q = self._near_sort(i, chosen, q, d2, 1 if focus >= 0 else 0)
        dist = np.sqrt(d2[q])  # 採った数件だけ sqrt(旧: セル在席者ぶんの辞書)
        act = a.activity
        return [
            SeenPerson(
                id=int(j), direction=None, action=int(act[j]), distance_m=max(float(dv), 0.1),
                acquainted=(j in friends),
            )
            for j, dv in zip(chosen, dist)
        ]

    def _nearby_people_distance(self, i: int, cell: int, tc: _TickCache) -> list[SeenPerson]:
        """〔第 2 期 2-2 段 11a〕腕 ``--proximity distance`` の B5 近接行(見えた人)。

        候補=刻みの頭の近傍の索引(``tc.near``)のうち、同じ層で半径(規則の ``b5_radius_m``=10.3 m・仮採用)の中の体と、
        同じ B5 の単位の体(自分を除く・単位は索引の単位=店のセルの中の体)。人数は今と同じ密度逓減 3/2/1(知覚契約 §3
        人物④・自分のセルの密度の段)で、近い順(同点は ``near_tiebreak``)。それに足す: **気づいている知人で半径の中の体**
        (同じ層・半径の中で、関係の層の気づいた印が切れていない相手=``NearView.aware``・描画ごとに引き直さない=検収 L1。
        半径の外の知人は載せない=気づいたままの印は起床の条件にだけ使う=親の判断 10-14 の 3。印の無いラン=知人出現の
        起床が無いランは足さない)・会話の参加者と注意の焦点(候補の中に居れば)。並び・焦点の先頭・距離の値の作り方(``max(d, 0.1)``)は今と同じ。自分の位置はいまの値・相手は索引の値
        (今の B5 のセル順の座標と同じ取り方)。舞台の外(セル < 0)の体は誰も見ない(今と同じ)。
        逐次ループ宣言: なし(索引の近傍の格子の数ぶんの配列演算・載る数人)。
        """
        a = self.agents
        nv = tc.near
        rule, idx = nv.rule, nv.index  # type: ignore[attr-defined]
        if not (0 <= cell < tc.los_stage.size):
            return []
        # 〔第 2 期 2-4 V2〕自分の層はセルの層から導く(SoA の派生の列 agents.band=軸 1 no を読まない・値は同じ)
        xi, yi = float(a.xy[i, 0]), float(a.xy[i, 1])
        _c = int(a.cell[i])
        bi = int(self.world.assets.cell_band[_c]) if _c >= 0 else 0
        _q, ids, _d = idx.query_many(xi, yi, bi, float(rule.b5_radius_m))
        pi = int(idx.pos[i]) if 0 <= i < idx.pos.size else -1
        um = idx.unit_members(int(idx.unit[pi])) if pi >= 0 else np.zeros(0, dtype=np.int64)
        peers = (np.union1d(ids, um) if um.size else np.sort(ids)).astype(np.int64)  # id の昇順・重なりなし
        peers = peers[peers != int(i)]
        pp = idx.pos[peers]
        dx = idx.x[pp] - xi
        dy = idx.y[pp] - yi
        d2 = dx * dx + dy * dy
        los = int(tc.los_stage[cell])
        k = 3 if los <= 1 else (2 if los <= 3 else 1)  # 疎3/中2/密1(今と同じ)
        take = min(k, peers.size)
        sel = self._near_take(i, peers, d2, take) if peers.size > take else peers
        peer_set = {int(x) for x in peers.tolist()}
        chosen_set = {int(x) for x in sel}
        if self.session_partner_fn is not None:  # 会話の参加者は候補の中に居れば常に載せる
            sp = np.asarray(self.session_partner_fn(i), dtype=np.int64)
            chosen_set |= {int(x) for x in sp.tolist() if int(x) in peer_set}
        friends, friend_ids = self._acquaintances_of(i, int(tc.tick))
        aware = nv.aware  # type: ignore[attr-defined]
        if friend_ids.size and aware is not None:  # 気づいている知人で半径の中(B4・関係の層の印を読むだけ)
            f = friend_ids[friend_ids != int(i)]
            pf = idx.pos[f]
            f, pf = f[pf >= 0], pf[pf >= 0]
            if f.size:
                fd = np.sqrt((idx.x[pf] - xi) ** 2 + (idx.y[pf] - yi) ** 2)
                inr = (idx.bands[pf] == bi) & (fd <= float(rule.b5_radius_m))
                if bool(inr.any()):
                    hit = np.asarray(aware(int(i), f[inr], int(tc.tick)), dtype=bool)
                    chosen_set |= {int(x) for x in f[inr][hit].tolist()}
        focus = -1
        if self._focus_target is not None:
            fo = int(self._focus_target[i])
            if 0 <= fo < int(a.n) and fo != i and fo in peer_set:
                focus = fo
                chosen_set.add(fo)
        if not chosen_set:
            return []
        chosen = sorted(chosen_set)
        if focus >= 0:
            chosen = [focus] + [x for x in chosen if x != focus]
        pc = idx.pos[np.asarray(chosen, dtype=np.int64)]
        d2c = (idx.x[pc] - xi) ** 2 + (idx.y[pc] - yi) ** 2
        q = np.arange(len(chosen), dtype=np.int64)
        if self.near_order == "distance" and len(chosen) > 1:
            chosen, q = self._near_sort(i, chosen, q, d2c, 1 if focus >= 0 else 0)
        dist = np.sqrt(d2c[q])
        act = a.activity
        return [
            SeenPerson(
                id=int(j), direction=None, action=int(act[j]), distance_m=max(float(dv), 0.1),
                acquainted=(j in friends),
            )
            for j, dv in zip(chosen, dist)
        ]

    def _near_sort(self, i: int, chosen: list[int], q: np.ndarray, d2: np.ndarray,
                   head: int) -> tuple[list[int], np.ndarray]:
        """第304 Q130: 近接行を**距離の昇順**に並べる(先頭 ``head`` 人=焦点は動かさない)。

        同点は ``near_tiebreak`` の順(``hash``= 撹拌鍵の小さい順・``id``= 行番号の順)。距離は ``d2``(旧実装と
        同じ値)で比べる。逐次ループ宣言: なし(載る数人の配列)。
        """
        ids = chosen[head:]
        qq = q[head:]
        dd = d2[qq].tolist()  # 載る数人だけ=Python の sort が numpy の呼び出しより速い(1 呼 +数 µs)
        if len(set(dd)) == len(dd):  # 同点なし=距離だけで順が決まる(鍵は作らない)
            order = sorted(range(len(ids)), key=dd.__getitem__)
        else:
            self.near_order_ties += 1
            if self.near_tiebreak == "hash":
                key = near_tie_keys(self._near_salt64, i, np.asarray(ids, dtype=np.int64)).tolist()
            else:
                key = list(ids)
            order = sorted(range(len(ids)), key=lambda t: (dd[t], key[t]))
        sel = np.asarray(order, dtype=np.int64)
        return chosen[:head] + [ids[t] for t in order], np.concatenate([q[:head], qq[sel]])

    def _near_take(self, i: int, peers: np.ndarray, d2: np.ndarray, take: int) -> np.ndarray:
        """近接 k 人の採り方。``id``= 旧実装(``np.argpartition`` がセル内の並びで同点を切る)=1 ビットも変えない。

        ``hash``: k 人目の距離 ``thr`` より近い人は全員・``thr`` と同点の人から足りない分を撹拌鍵の小さい順に。
        同点が境に無ければ採る集合は ``id`` と同じ(k 最小の集合が一意)。逐次ループ宣言: なし(セル在席者の配列)。
        """
        if self.near_tiebreak == "id":
            return peers[np.argpartition(d2, take - 1)[:take]]
        thr = np.partition(d2, take - 1)[take - 1]
        inside = d2 < thr
        tie = np.flatnonzero(d2 == thr)
        need = take - int(np.count_nonzero(inside))
        if tie.size > need:
            self.near_tie_breaks += 1
            self.near_tie_candidates += int(tie.size)
            key = near_tie_keys(self._near_salt64, i, peers[tie])
            tie = tie[np.argpartition(key, need - 1)[:need]] if need < tie.size else tie
        return np.concatenate([peers[inside], peers[tie]])

    def _acquaintances_of(self, i: int, tick: int = -1) -> tuple[frozenset[int], np.ndarray]:
        """個体 → (知人の集合, 知人 id の配列)。**1 度作って使い回す**(C7)。

        知人表は ``Renderer`` の構築時に固定される(§3 人物④「知人は常に掲載」)ので、
        毎呼 ``set(...)`` を組み直す必要がない。範囲外の id はここで落とす
        (旧実装では同セル集合との積で自然に落ちていた)。

        C10 8a: ``acquaintance_fn``(``engine.run`` が ``--relations on`` のランだけ差し込む)があれば、
        関係辺の生きている相手(A ≥ τ_rel・強さの降順・≤ k)を**呼ごとに**引く(辺は相互作用で変わる=
        キャッシュしない・体 × k の配列演算)。
        """
        if self.acquaintance_fn is not None:
            arr = np.asarray(self.acquaintance_fn(i, int(tick)), dtype=np.int64)
            n = int(self.agents.n)
            arr = arr[(arr >= 0) & (arr < n)]
            return frozenset(int(x) for x in arr.tolist()), arr
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

    def _named_closed_text(self, i: int) -> str:
        """Q25: 名指しの店が見えるが閉店で歩かずに失敗した体だけの補足の 1 句(それ以外は ``""``)。

        ``named_closed_lookup``(``engine.run`` が渡す・体 → ``(POI, 失敗の tick, 開店の分)``)が
        返した tick が ``last_result_tick`` と一致するときだけ載せる(=その失敗の直後の起床だけ)。
        """
        look = self.named_closed_lookup
        if look is None:
            return ""
        got = look(int(i))
        if not got:
            return ""
        poi, t, opens = (int(x) for x in got)
        if int(self.agents.last_result_tick[i]) != t:
            return ""
        names = self.assets.poi_name
        name = str(names[poi]) if 0 <= poi < len(names) else NAMED_CLOSED_FALLBACK_NAME
        self.named_closed_notes += 1
        return named_closed_note(name, opens)

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
        return int(self.world.pois.open_from[m].min()) // MINUTES_PER_HOUR


def _noise_stage(scene: SceneView) -> int:
    """その場の騒音の段(``SceneView.sounds`` の ``noise``・無ければ 0)。"""
    for s in scene.sounds:
        if s.kind == "noise":
            return int(s.stage)
    return 0


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
