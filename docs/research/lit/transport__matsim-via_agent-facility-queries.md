# MATSim events と Simunto Via — 個体カルテ(agent plan)と場所カルテ(Facility Analysis)の既製の型

- リンク: https://www.matsim.org/files/book/partOne-latest.pdf(MATSim User Guide・2026-08-25 コンパイル版・216 頁。<https://www.matsim.org/docs/> から辿れる「MATSim 本の抜粋と更新」)| 分野: 交通工学 #2 / ソフトウェア工学 #29 | 重要度: **P1**
- **一次確認**: **実読(サブ)**(2026-09-17・PDF を curl → システム python の pymupdf で全 216 頁抽出し、§15.1(出力ファイル)と第 5 章 Simunto Via の §5.2〜§5.4.5 を逐語照合)。**親未確認**。
  - **未読**: §26.5(Events の詳細章)、MATSim 本体(<https://www.matsim.org/the-book>)、Via の製品ドキュメント、SimWrapper の章。
  - **Via は非オープンソースの商用製品**(Simunto GmbH・元は Senozon AG が開発)。無償の制限版あり。

## 主張(claim)

**1 行 =(時刻・体 ID・場所 ID・種別)のイベント列**を 1 本持てば、そこから **個体カルテ(agent plan クエリ)** と **場所カルテ(Select Facility Analysis)** の両方が引ける。**記録があることと読めることは別**であり、読み口(Via)は記録の後から別製品として生まれた。

## 機構(mechanism)

### 記録の最小行(§15.1)

- "**Every action in the simulation is recorded as a MATSim event**, be it an activity start or change of network link"
- "Each event possesses one or multiple attributes. By default, **the time when the event occurred** is included."
- "Additionally, information like **the ID of the agent triggering the event, or the link ID where the event occurred**, could be included."
- "**The events file is an important base for post-analyses, like the visualizers.**"

同じ出力フォルダに並ぶもの: `output_events.xml.gz` / Plans("the current state of the population, with the agents' plans, is printed" ・任意の反復で)/ Leg Histogram(手段別の出発・到着・移動中の数)/ Stopwatch(壁時計時間)。**個体の記録(events・plans)と集計の記録(histogram)が最初から別ファイル**。

### なぜ読み口が要ったか(§5.2)

- "**Explaining to customers that all answers to their questions were contained in a huge events file was not satisfactory**; pictures or even animations made it much easier for them to understand."

Via は 2011 年 7 月に初版。当初は社内ツールの予定だった。

### 個体カルテ = agent plan クエリ(§5.3)

- Via は **データソース**(`network.xml`・`events.xml` 等)と **レイヤ**(表示の仕方)を分ける。「1 レイヤが複数データソースを使える/1 データソースが複数レイヤに使われる」。
- "Elements shown in the visualization area like the network or vehicles **can be queried**."
- "**One query is special, globally available, and not linked to a layer: querying an agent plan.**" ← **個体クエリだけがレイヤから独立した特別扱い**
- クエリ結果から次のクエリへ辿れる: "Select Link Analysis given a link, **Select Facility Analysis** given a facility, List Transit Lines that use a given link, or **List Passengers** if a transit vehicle was queried"

### 場所カルテ = Facility Analysis(§5.4.2)

- "**For each facility, a detailed analysis can be performed showing the number of agents arriving at, departing from, or staying at a facility over the simulated time.**"
- "The numbers can be **differentiated by the type of activity** the agents perform at the facility, **by the transport mode** they arrive or depart with, **or by other arbitrary agent attributes** loaded by users."
- Select Facility Analysis = "shows the combined link loads produced by agents arriving or departing at a facility, **showing the starting location for agents visiting a specific facility and what routes they use**"

### 個体と集計の分離(§5.4.5)

- "**While MATSim requires and produces a lot of disaggregated data, it is still often necessary to aggregate data** to make statements or predictions about a simulated scenario."
- 集計先は "a **rectangular or hexagonal grid**, where the **cell-size can be specified by the user**" または ESRI shapefile のゾーン。点データ(活動地点・トリップ始終点)と OD データの両方を集計できる。

### 腕の比較(§5.4.4)

- "Via allows comparison of the link volumes of **two scenarios** visually by coloring the network with the **absolute or relative difference** of the link volumes between two models."
- "The differences are time-dependent, **aggregated over time intervals as small as 15 minutes**."

### 体の可視化(§5.4.1)

- `network.xml` + `events.xml` の 2 つだけで動く。`population.xml` を足すと活動地点の座標が細かくなる("MATSim's events file does not contain coordinates for activities, only the assigned link ID")。
- "It is also possible to **load arbitrary attributes for agents** and then use those attributes for visualization purposes"(就業者・高所得・年齢帯で色を変える)。

## 効く箇所(seam)

- **v2 の「個体カルテ / 場所カルテ」は新しい発明ではない**。Via が 2011 年から持っている 2 つのクエリに相当する。
- **場所カルテの列はそのまま写せる**: 到着数 / 出発数 / 滞在数 × 時刻ビン × (活動種別・移動手段・任意の個体属性)。
- **ビンは 15 分**(Via の差分の最小粒度)= v2 の既存の物差し M3(15 分ビン)と一致する。
- **分離すべきは「保存」ではなく「見せ方」**: 同じイベント列から個体も集計も引く。v2 のテープ + カルテ生成器という構成の外部裏づけ。
- **記録の最小行の形**: v2 のテープ(1 呼 = 1 行)に**エンジン側イベントの行**(時刻・体 ID・place_id・種別)を足せば MATSim と同じ形になる。

## 「結論でなく機構として」の入れ方

- **借りない**: GUI・Cesium/OSM 背景・商用製品そのもの。
- **借りる**: (1) **個体クエリを一級の機能として独立させる**(レイヤの付属物にしない)。(2) **場所カルテの列の型**(到着/出発/滞在 × 時刻 × 属性)。(3) **クエリから次のクエリへ辿れる**(体 → その体が行った場所 → その場所に来た他の体)。(4) **腕の差を場所の上に描く**。

## 数値(出所つき)

- 集計の時間粒度の下限 = **15 分**(§5.4.4)。
- Via 初版 = **2011 年 7 月**(§5.2)。ベータは 2011 年春。2018 年初に所有が Simunto GmbH へ移った。
- **バイト数・イベント数の記載は無い**(空欄)。

## コスト/スケール含意

- Via のマニュアルは「小さい events ファイルから始めよ」と書く("it's usually best to add a network and **(small) events file** from MATSim to Via")=**巨大なイベント列をそのまま読ませるのは想定外**。v2 の 40 万体でも同じ制約がかかる(答申 §2 O4・O6 の抽出の議論)。

## 批判・限界

- **Via は商用・非オープンソース**。実装を借りることはできず、借りるのは設計の型だけ。
- 交通シミュのイベントは**LLM 呼のような可変長テキストを含まない**。v2 のカルテは prompt/応答を持つので 1 行あたりのバイトが桁違いに重い(答申 §2 O10 の切替口が要る理由)。
- §26.5(Events の詳細)と MATSim 本体は未読。イベント型の一覧は確認していない。

## 関連

[[agents__concordia_structured-logging]](同じ 2 軸を API で持つ例)・[[abm__grimm2020_odd-observation]](観察の ODD 上の位置)・[[compute__matsim2020_hermes]](同じ MATSim の並列側)・`../v2-micro-observation-research.md` §1-5
