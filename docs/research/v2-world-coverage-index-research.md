# レーンWC 答申: 「世界の再現度」指標(World Coverage Index)の設計

> **親検収(Fable・2026-09-07)**: 主要根拠を親が一次確認した。✔=親が実読して一致。
> - ✔ ODDプロトコル第2版(Grimm et al. 2020・JASSS 23(2)7実読): 要素2「Entities, state variables and scales」=実体型(空間単位・エージェント・環境)ごとに状態変数を列挙し、時間・空間の解像度と範囲を定める。世界カタログの列挙様式として妥当。
> - ✔ Barrington-Leigh & Millard-Ball 2017 PLoS One(実読): 「globally, OSM is ∼83% complete」(95%CI 81-84%)・185か国中77か国が95%超・分母はシグモイド当てはめで飽和水準を推定=「被覆率の分母を外挿する」先行実装として妥当。
> - CityGML 3.0本標準はサイズ超過で親も未読(OGC概要ページで代替確認=別途)。ISO 19157/30173/23247・Gemini原則・PLATEAU LOD定義は答申申告どおり空欄/二次(親も未確認)。
> - 設計主張(分母凍結・REACH/VERIFIEDは深度と直交・REACHは実測・commission/orphansのみゲート・加重和にしない)は答申の判断であり文献の逐語ではない=expedient(答申(d)の登録簿どおり)。素点C≈0.65/D≈0.35/V≈0.21は答申の試算(親未再計算)。
> - 正典化: docs/research/v2-world-coverage-index-research.md(世界再現度指標の根拠)。


> 作成: 2026-09-07 / 実行=Opus 5 リサーチサブ / 子サブ起動なし / リポは読み取りのみ / Webからのダウンロードなし
> 表記規律: **【実読】**=当該ページを本レーンで実際に開いて得た文/数値。**【検索要約】**=検索エンジンの要約経由で一次ページ本文は未読(確度中)。**空欄(未確認)**=読めなかった。**【推測】**=根拠のない推論。
> 注記: 本レーンでは iso.org(30173/19157/37120)・MDPI・Springer・ANSI webstore が **403**、CDBB Gemini Principles PDF と OGC CityGML 3.0 本標準(10MB超)が**本文抽出不可**だった。該当項目は「確度中」または「空欄」で通してある(記憶で埋めていない)。

---

## 要約(10行)

1. **同名の先行指標は存在しない**。DTの成熟度モデル(Gemini/CDBB・Atkins-IET/Arup 6段・ISO 23247)は**組織とデータ連携の成熟**を測るもので、「世界に存在するものがどれだけ実装されているか」を測らない。ユーザー提案の指標は**空白地**にある。
2. ただし部品は全部揃っている: **数え方=ISO 19157の completeness(omission/commission の二面計上)**、**深さ=CityGML/PLATEAUのLOD と Atkins-IET成熟度6段**、**漏れの防止=オントロジーの competency questions**、**分母の作り方=都市代謝(urban metabolism)の inflow/outflow/accumulation 勘定**、**列挙の様式=ODDの要素2「Entities, state variables and scales」**。
3. **最重要の設計判断は「分母(世界カタログ)を先に凍結する」こと**。分母が動く被覆率は必ず虚栄指標化する。カタログは実装前に版を切り、追加はユーザー承認+版番号(holdoutと同じ扱い)。
4. **数えるのは憲法5(D-R2-4)の門を通った要素のみ**——`reaches` か `contributes` が非空、かつ参照先が実在(CIビルド時検査)。これは既に設計書で決定済みの機構をそのまま流用できる。
5. **v1の失敗形(実装したが知覚が読まなかった)は commission として減点**する。ISO 19157 が completeness を omission と commission の**両方**で測るのと同型。片側だけ報告する指標は作らない。
6. **「宣言された到達」でなく「実測された到達」で数える**。`reaches` が宣言されていても、ランでその知覚チャネルからの実読回数が0なら **orphan** として別掲し被覆から外す。v1の屋内SFM座標に直接効く処方。
7. **段階(深度)は6段(d0-d5)を推奨**するが、「知覚に届く」は行動実装の上位段階ではなく**直交フラグ**である(順序尺度に混ぜると誤導する)。d0-d4=実装深度の順序尺度、reaches/verified=別フラグ、で報告する。
8. **報告は単一スコアに潰さず5値ベクトル**: 被覆率C・数量整合Q・深度D・検証済み率V・過剰率X(commission)+ orphan数。Goodhart 4分類(Regressional/Extremal/Causal/Adversarial)のうち Extremal と Adversarial への直接の対処。
9. **世界カタログ初版**は34クラスで起草した(節6b)。うち**現実数量が公的統計で取れるのは18クラス**、**存在の有無のみ数えるのが16クラス**(自販機・街路灯・広告面・ごみ集積所など=渋谷の実数が空欄)。
10. v2現状の**素点(本レーンの見積・要親検算)**: 憲法5の門を通った34クラス中、d≥1が22、d≥3が9、verified が7 → **C≈0.65 / D≈0.35 / V≈0.21**。第1陣(モノの保存則+補充+収集+断面交通+屋内占有)が入ると **C≈0.79 / D≈0.50 / V≈0.32** 【推測・本レーンの試算】。

---

## 問い1. 先行の指標・枠組み(何を数え/どう重み付けし/どう報告するか)

| 枠組み | 何を数えるか | 重み付け | 報告形 | 確度 |
|---|---|---|---|---|
| **Gemini Principles(CDBB 2018)** | 数えない。DTが満たすべき**9原則**(public good / value creation / insight ‖ security / openness / quality ‖ federation / curation / evolution)を Purpose・Trust・Function の3見出しに配置 | なし(原則の充足) | 定性の宣言 | 【検索要約】CDBB公式PDFは画像PDFで本文抽出不可=**逐語未確認** |
| **Gemini原則ベースDT成熟度モデル(Sustainability 13:8224, 2021)** | Gemini原則を**3次元×9サブ次元×27ルーブリック**に展開して資産管理DTを採点 | ルーブリック等重み(記載範囲では) | 次元別スコア | 【実読・逐語】「three main dimensions consisting of nine sub-dimensions have been defined firstly, which were further articulated by 27 rubrics」(UCL Discovery版PDF) |
| **Atkins/IET・Arup「DT maturity spectrum」** | DTの**能力段階**を6段で: **Reality capture(0) / Replication(1) / Connection(2) / Synchronization(3) / Interaction(4) / Autonomous(5)** | なし(単一の段階) | 単一レベル | 【検索要約】一次ホワイトペーパー本文は未読 |
| **ISO/IEC 30173:2023 (DT概念と用語)** | 空欄(未確認・iso.org 403) | 空欄 | 空欄 | — |
| **ISO 23247(製造DTフレームワーク)** | **Observable Manufacturing Element (OME)** を単位に数える。OMEの型= personnel / equipment / material / process / facility / environment / product / supporting document。DT定義=「fit for purpose digital representation of an observable manufacturing element **with synchronization** between the element and its digital representation」 | なし | 参照アーキテクチャの層(OME層が最下層) | 【検索要約】ANSIプレビューPDFは403=**逐語未確認**。ただし「観測可能な実体を型で列挙し、それが分母になる」構造は本答申の骨格と一致 |
| **ISO 19157(地理情報のデータ品質)** | 品質要素= completeness / logical consistency / positional accuracy / thematic accuracy / temporal quality。**completeness は omission(現実にあるがデータに無い)と commission(データにあるが現実に無い)の2サブ要素**で測る | 「data quality scope」単位で測定・報告 | 品質尺度ごとの測定値+品質報告 | 【検索要約】ISO原文403・ISO/TC211草案PDFは抽出空。**二面計上の構造のみ確度高(複数二次が一致)**、逐語は未確認 |
| **CityGML 3.0 (OGC)** | 「defines a conceptual model and exchange format for the representation, storage and exchange of virtual 3D city models」。**主題モジュール**= Building, Transportation, Vegetation, WaterBody, CityFurniture, LandUse, Relief, Tunnel, Bridge, **Dynamizer**, **Versioning** | なし | モジュール別のスキーマ充足 | 【実読】OGC標準ページ。**LOD0-3の逐語定義と LOD4 廃止の記述は本標準(docs.ogc.org/is/20-010)が10MB超で取得不能=空欄(未確認)** |
| **PLATEAU 3D都市モデル標準製品仕様書 v5.1(2024-03-19)** | 地物型ごとに**詳細度LOD**を規定 | — | — | 【実読】目次のみ(版・日付)。**LOD定義の逐語は本文PDF未読=空欄(未確認)** |
| **OSM completeness(Barrington-Leigh & Millard-Ball 2017)** | **道路エッジ数/延長**の完全性。手法2本: (a)各国45点の層化標本を衛星画像と重ねて欠落エッジを目視計数 (b)各国の道路延長時系列に**飽和(ロジスティック)曲線**を当てて総量を外挿 | 国レベル回帰(GDP・ネット普及・ガバナンス) | 「全球約83%(CI 81-84)」「185か国中77か国が95%超」「総延長約3,970万km」 | 【実読】PLOS ONE本文ページ |
| **オントロジーの competency questions(Grüninger & Fox 1995)** | 要件を「そのオントロジーが答えられねばならない**質問**」の集合として先に書き、**完全性定理**で充足を判定 | なし | 質問ごとの可否 | 【検索要約】著者サイトPDFは証明書エラーで未読 |
| **ODD protocol 2020(Grimm et al., JASSS 23(2)7)** | 要素2「Entities, state variables and scales」が**実体型の列挙**を要求。「lists the different types of entities represented in the model, such as spatial units, agents, and the overall environment」/「For each entity type, the state variables that characterize it are defined. These are variables that may vary among entities of the same type or vary over time」 | なし | 7要素(1 Purpose and patterns / 2 Entities… / 3 Process overview and scheduling / 4 Design concepts / 5 Initialization / 6 Input data / 7 Submodels) | 【実読・要約器経由の引用=親が逐語再確認推奨】 |
| **都市代謝(urban metabolism)** | 都市への**inflow / outflow / accumulation(蓄積)**を資源種別(水・エネルギー・物質・食料)で会計。Kennedy 2007 の定義=「the sum total of the technical and socio-economic process that occur in cities, resulting in growth, production of energy and elimination of waste」 | 物量単位(t, kWh, m³) | 収支表 | 【検索要約】Wiley本文未読 |
| **ISO 37120:2018(都市指標)** | **104指標×19テーマ**、core/supporting/profileの3種 | テーマ別 | 指標票 | 【検索要約】iso.org 403 |
| **ゲームの「シミュレーション深度」(Dwarf Fortress等)** | 体系化された指標は**見つからなかった**。二次記事レベルで「身体部位ごとの皮膚/脂肪/筋/骨/神経」「個体ごとのストレス・記憶・嗜好・食性」といった**系統列挙**で語られるのみ | — | — | 【検索要約・二次記事】学術的な「深度指標」は空欄(未確認) |

**含意(重要)**: 上の全てが、**(i)実体型の列挙(ODD要素2 / ISO 23247 OME / CityGML モジュール)**、**(ii)欠落と過剰の二面計上(ISO 19157)**、**(iii)段階尺度(LOD / Atkins-IET 0-5)**、**(iv)収支での閉じ(都市代謝)**、**(v)要件を質問で先に固定(competency questions)** という5部品に分解できる。ユーザー提案の指標は**この5部品の組み合わせとして定義できる**——そして「エンジン側に現実の要素がどれだけ存在するか」を主目的に据えた先行指標は、本レーンの探索範囲では**見つからなかった**(空白地)。

---

## 問い2. 世界カタログの分類軸

### 推奨: 主軸1本(実体の存在論)+ 直交軸4本(既存決定の再利用)

**主軸(クラスの型)= 5型**。v2の既存決定(D-R2-2の3レコード型+関係)と、ISO 23247のOME型・CityGMLモジュールの両方に接続する形にした:

| 型 | 定義 | v2の受け皿 | 先行の対応 |
|---|---|---|---|
| **E 実体(Entity)** | 場所を占め、状態を持つもの(建物・道路・店・人・車・棚の在庫・広告面) | レジストリの静的地物+エージェント | ISO 23247 OME / CityGML の Building・Transportation・CityFurniture / ODD要素2 |
| **P 過程(Process)** | 状態を時間で変えるもの(天候・混雑・運行・補充・収集・価格改定) | `WorldProcess` + 層2の行動 | 都市代謝のフロー / ODD要素3 |
| **R 関係(Relation)** | 実体間の第1級の結び(所属・雇用・隣接・所有・接続) | 既存の関係4本(realizes/records/revises/counts_as)+社会関係グラフ | CityGML の空間関係 / オントロジーの関係 |
| **N 規範(Norm/Plan)** | 予定・規則・許認可(ダイヤ・営業時間・条例・価格表) | `PlanSpec` | Transmodel/NeTEx・IG2.0 |
| **I 情報(Information)** | 世界に存在する表示・信号・発信(看板・案内・運行情報・SNS投稿・口づて) | 知覚チャネル+AD群 | CityGML Dynamizer(時系列属性) |

**直交軸(既に v2 で決定済みのものをそのまま使う。新設しない)**:
- 軸1 実行様態(エンジン/参照/導出/物理アフォーダンス)・軸2 改訂権者・軸3 規範種別・軸4 違反可能性 …… D-R2-2 の4軸
- 憲法5の門: `reaches[]` / `contributes[]` …… D-R2-4
- `mechanism | expedient` タグ …… 方法論

**流用できる既存の骨格(評価)**:
- **CityGML 3.0 のモジュール分割**(Building/Transportation/Vegetation/WaterBody/CityFurniture/LandUse/Relief/Tunnel/Bridge)= **E型の網羅チェックリストとして最良**。渋谷 bbox にはWaterBody(渋谷川)・Relief(道玄坂の起伏)・Bridge(歩道橋・デッキ)が実在するので、モジュール名を横に並べるだけで漏れが1件見つかる(**v2は Relief=地形をまだ持っていない**)。
- **ISO 23247 の OME 型**(personnel/equipment/material/process/facility/environment/product/supporting document)= **「supporting document」に相当するのが v2 の PlanSpec** で、v2はここを既に持っている(先行より進んでいる箇所)。
- **ISO 37120 の19テーマ・104指標** = 都市の**出力側**指標なので、カタログの分母ではなく「照合行の候補源」として使うのが適切。ただし iso.org 403 で19テーマ名は**空欄(未確認)**。
- **Schema.org** = LocalBusiness/Place/Event/Product の語彙は POI カテゴリの正規化には使えるが、**過程・規範を型として持たない**ため主軸には不適(不採用推奨)。
- **競合質問(competency questions)** = カタログの網羅性検査に使う。「この世界は次の質問に答えられるか: 渋谷駅から○○までの終電後の帰り方は? 22時に開いている店は? 今日のごみは誰が出して誰が運ぶ?」——**答えられない質問=カタログの欠落**として登録する運用を推奨(「未知の未知」への唯一の実用的対処)。

---

## 問い3. 数量の取り方(現実の数が取れるもの/取れないもの)

**原則(ISO 19157由来)**: 現実数 `N_real` は **omission を測るための分母**である。取れないクラスは分母を作らず、**存在フラグのみ**(0/1)で数える。両者を混ぜた単一の被覆率は報告しない(必ず `C_quantified` と `C_all` の2本を出す)。

### (a) 現実数量が取れるクラス(18)

| クラス | 現実数量 | 出所 | 確度 |
|---|---|---|---|
| 建物 | OSM 7,210 / PLATEAU 6,311棟(bbox定義が違う: PLATEAU bbox 1,872×1,539m ⊂ OSM広域 2,523×2,748m) | リポ実測(親検収済) | 高 |
| 道路(歩行グラフ) | ノード3,499 / エッジ4,944 / 総延長186.7km / 平均エッジ長37.8m | リポ実測(親再計算済) | 高 |
| 街区 | 1,242(Euler面数 F=E−V+C)・平均5,582m²(1辺約75m) | リポ実測 | 高 |
| セル(100m格子) | 広域453 / 核±600m 143 | リポ実測 | 高 |
| 層(地下・デッキ) | 地下エッジ190本5.0km / デッキ306本8.7km | リポ実測 | 高 |
| POI | 2,337(food 823 / shop 721 / nightlife 259 / office 124) | リポ実測 | 高 |
| 事業所(区全体) | 全産業33,398(2021)/ 民営27,624・従業者516,541 | e-Stat 経済センサス(親取得) | 高 |
| 夜間人口 / 昼間人口 | 243,883 / 551,344(国勢調査2020・流入363,883) | リポ §2.5(親取得) | 高 |
| 世帯 | 142,463世帯・人口230,656(令和6年2月1日) | 渋谷区ポータル | 中【検索要約】 |
| 区面積 | 15.11 km² | 同上 | 中【検索要約】 |
| 鉄道: 駅利用者 | JR東324,414(乗車のみ2024)/東急東横425,889・田都619,956/京王井の頭291,490/メトロ銀座196,339・半蔵門+副都心779,659 | 各社公式(台帳D10) | 高 |
| 鉄道: ダイヤ | ODPT 1,810本 | リポ(D-R2-1) | 高 |
| ごみ | 区 43,663 t/年(令和6年度・可燃40,810/不燃1,433/粗大1,421)= **119.6 t/日** | 渋谷区ポータル(親実読) | 高 |
| 宅配便 | 全国 50億3,147万個/年(令和6年度)→ 区按分は**expedient** | 国交省報道発表(親実読) | 高(全国値) |
| 救急 | 都 935,373件/年・搬送798,035人(令和6年)→ 区推定4-10件/日は【推測】 | 東京消防庁(親実読) | 高(都値) |
| 自動車断面交通 | 道路交通センサス令和3年度 箇所別・時間帯別CSV(bbox内の箇所数は**要確認**) | 国交省/東京都建設局 | 中 |
| 気象 | 手元35日(2026-07-28〜08-31)。過去日は気象庁から別取得が必要 | リポ実測 | 高 |
| 事業所規模分布 | 0人6,204/1-4人12,559/5-9人6,276/…/300人以上244(合計33,398) | e-Stat 表14 | 高 |

### (b) 現実数量が取れない/未取得のクラス(16=存在フラグのみ)

自動販売機・街路灯・信号機・横断歩道・ごみ集積所・公衆トイレ・ATM・駐輪場・喫煙所・防犯カメラ・**屋外広告面(OOH枚数)**・バス停/系統別乗車人員・タクシー台数・シェアサイクルポート・公園/緑地・ベンチ。
→ いずれも渋谷 bbox の実数は**空欄(未確認)**。**扱い**: `N_real=null` で存在フラグのみ計上、`w=1`(最小重み)、データ取得レーンの候補として台帳に残す。**このうち屋外広告面だけは AD群(AD2/AD3/S3)が既に照合行を持つので、実数取得の優先度が高い**(OSM `advertising=*` タグからの抽出が第一候補・被覆率は要実測)。

**取得できるのに未取得の重要2件**(親への申し送り): ① 駅出口の座標(ODPTは駅点のみ・OSMに `subway_entrance` 無し)=方面→出口セル表が作れない。② POIの営業時間・価格(手元2,337件に0件)。**この2件はカタログの「存在」ではなく「属性の完全性」の欠落**で、ISO 19157で言えば completeness ではなく thematic accuracy 側の穴として別記すべき。

---

## 問い4. 段階(深度)の定義

### 推奨する段階(d0-d5)+直交フラグ2本

| 段階 | 名 | 判定(機械検査可能な条件) | 先行の対応 |
|---|---|---|---|
| **d0** | 不在 | カタログにあるが実装なし | — |
| **d1** | 存在 | レジストリにIDと個体が生成され、個数が `N_real` に較正されている(または存在フラグ) | CityGML LOD0-1 / Atkins-IET **Reality capture(0)–Replication(1)** |
| **d2** | 状態 | 状態変数を1つ以上持つ(ODD要素2の state variable が定義され、初期化される) | ODD要素2 / CityGML の属性 |
| **d3** | 過程 | 状態が時間で変わる(`WorldProcess` またはエンジン規則が更新する) | Atkins-IET **Connection(2)–Synchronization(3)** / CityGML **Dynamizer** |
| **d4** | 行動由来 | 変化の原因が**エージェントの行動**である(`realizes(AgentAction, …)` / executor=llm_agent。engine_rule 代替はd3止まり) | Atkins-IET **Interaction(4)** / v2ドクトリン「世界の変化はエージェント行動の結果」 |
| **d5** | (欠番・下記参照) | — | Atkins-IET **Autonomous(5)** は v2 に対応物なし |

**直交フラグ(順序尺度に入れない)**:
- **REACH**: `reaches[]` が非空 **かつ** ランで当該知覚チャネルからの**実読回数 > 0**(宣言だけでは立たない)。
- **VERIFIED**: `contributes[]` が非空 **かつ** 参照先のパターン台帳行/観測出力が**現に判定を通っている**。

**なぜ「知覚に届く」を段階に入れないか(本答申の主要な設計上の主張)**: 天候(A類)は d3 だが REACH は立つ。逆に「モノの保存則の検算」は d3-d4 だが REACH は立たず VERIFIED だけが立つ(憲法5の(b)側)。**両者は順序関係にない**。順序尺度に混ぜると「知覚チャネルを1本足せば深度が上がる」という Adversarial Goodhart の穴を作る。したがって **d は実装の因果深度のみを測り、届き先は2本のフラグで別に報告する**。

**先行 maturity モデルとの対応の注意**: Atkins-IET の 0-5 は「**現実の資産との同期と自律性**」の段階であり、v2は現実とリアルタイム同期しない(DT定義=スナップショット)。したがって **Level 3(Synchronization)以上はv2の目標ではない**。v2の d4「行動由来」は Atkins-IETの Interaction(4) と表面的に近いが、意味は「双方向の現実操作」ではなく「内因性(endogeneity)」である。**この違いを報告時に1行で明記しないと、外部読者に誤読される**。

---

## 問い5. 虚栄指標化の防止

**v1の失敗形の正体**: 実装クラス数は増えたが `REACH` が立っていなかった(屋内SFM座標を知覚が一度も読まなかった)+ `VERIFIED` が立っていなかった(機能3割死蔵)。つまり **d が上がっても REACH/VERIFIED が0のまま総合スコアが上がる指標を作ると、v1をそのまま再現する**。

### 処方7本

1. **分母の凍結**: 世界カタログは**実装前に版を切って凍結**する(`catalog_v1.yaml` + SHA)。クラスの追加はユーザー承認+版番号+「なぜ初版で漏れたか」1行。**分母が自由に伸びる被覆率は必ず虚栄化する**(Regressional/Extremal Goodhart への一次防御)。
2. **門の適用**: 憲法5(D-R2-4)の `reaches`/`contributes` が非空かつ参照先実在(ビルド時検査)のクラスのみ被覆に計上。**門を通らない実装はスコアに一切寄与しない**。
3. **二面計上(ISO 19157型)**: `omission`(現実にあるが無い)と **`commission`**(実装したが現実に対応物がない/知覚に読まれない/照合に寄与しない=死蔵)を**両方**報告し、**総合ベクトルに commission を減点項として持たせる**。機能を増やすだけでは総合が上がらない。
4. **宣言でなく実測での到達**: REACH はランタイムカウンタ(当該細部を読んだ知覚呼の回数)で判定。**N日連続で0回なら自動的に `orphan` へ移し、削除候補として台帳に載る**(D-R2-4のCI機構をそのまま使う)。
5. **未検証実装の別掲**: `implemented_but_unverified` は独立行として報告し、C・D には入れるが **V には入れない**。3つの数字が同時に上がらない限り「再現度が上がった」と言わない。
6. **単一スコア禁止**: 5値ベクトル+attrition表で報告(方法論の運用規則8「全パターン通過を成果と呼ばない」と同型)。**加重和の1数字を作らない**——作った瞬間に重み設計が攻撃対象になる(Adversarial Goodhart)。
7. **重み関数の事前登録と凍結**: `w` は実装状況から独立な**現実側の量**だけで決める(下記)。実装者が動かせる変数(パターン行数・知覚チャネル数)を重みに入れると、行を増やして重みを稼ぐ経路ができる。**重みの感度試験(一様重みでランキングが変わらないこと)をablationに含める**。

**先行のGoodhart回避**: Manheim & Garrabrant の4分類(**Regressional / Extremal / Causal / Adversarial**)【arXiv:1803.04585・分類名は確度高、逐語定義は本レーンで未確認】。上の処方は 1→Regressional・3/6→Adversarial・4→Causal(「実装したから届いている」という因果の飛躍を実測で切る)に対応する。ODD/POM 側の対応物は「全パターン通過を成果と呼ばない」(既にリポの運用規則8)。

---

## 問い6. 推奨

### (a) 指標の定義式

カタログ `WC = {i}`、各クラス i は `w_i`(重み)、`d_i ∈ {0..4}`(深度)、`N_real,i`・`N_sim,i`、フラグ `gate_i`(憲法5の門)・`REACH_i`・`VERIFIED_i`。

```
# 0. 計上対象(門を通ったものだけ)
G = { i ∈ WC : gate_i = true }                       # reaches∪contributes が非空かつ参照先実在

# 1. 被覆率(存在するか)
C_quantified = Σ_{i∈G, d_i≥1, N_real,i≠null} w_i / Σ_{i∈WC, N_real,i≠null} w_i
C_all        = Σ_{i∈G, d_i≥1} w_i / Σ_{i∈WC} w_i
   ※ 分母は凍結カタログ全体(実装済みだけでない)

# 2. 数量整合(どれだけの数あるか) ※上振れで得をさせない
Q = Σ_{i: N_real,i≠null} w_i · min(1, N_sim,i / N_real,i) / Σ_{i: N_real,i≠null} w_i
X_commission = Σ_{i: N_real,i≠null} w_i · max(0, N_sim,i/N_real,i − 1) / Σ w_i     # 過剰生成
   + クラス単位の commission: 実装済みだが N_real=null かつ VERIFIED=false のクラス数(死蔵候補)

# 3. 深度
D = Σ_{i∈G} w_i · d_i / (4 · Σ_{i∈WC} w_i)

# 4. 検証済み率(照合が現に通っているか)
V = Σ_{i∈G, VERIFIED_i} w_i / Σ_{i∈WC} w_i

# 5. 到達率(知覚が実際に読んだか)
Rreach = Σ_{i∈G, REACH_i} w_i / Σ_{i∈G, reaches宣言あり} w_i
orphans = |{ i : reaches宣言あり ∧ 実読回数=0 }|

# 重み(事前登録・凍結・実装状況から独立)
w_i = 1 + log10(1 + N_real,i)          # N_real がある場合(上限 w=6 でクリップ)
w_i = 1                                # N_real=null(存在フラグのみ)のクラス
```

**報告の作法**: `(C_all, Q, D, V, Rreach)` の5値 + `X_commission` + `orphans` + カタログ版SHA。**加重和にしない**。

### (b) 世界カタログ初版(v0.1・34クラス)

> `d` は本レーンの見積(リポの設計書ベース・**要親検算**)。`gate` は憲法5(D-R2-4)を通せるかの見込み。第1陣後は世界過程答申の陣分けを反映。

| # | 型 | クラス | 現実数量(bbox/区) | 出所 | v2現在 d | reach | verified | 第1陣後 d |
|---|---|---|---|---|---|---|---|---|
| 1 | E | 建物 | 7,210(OSM)/6,311棟(PLATEAU) | リポ実測 | 1 | ✔ | — | 2 |
| 2 | E | 街路(歩行グラフ) | 4,944エッジ/186.7km | リポ実測 | 2 | ✔ | D4′ | 2 |
| 3 | E | 街区 | 1,242 | リポ実測 | 1 | — | — | 1 |
| 4 | E | セル(場所) | 453 / 核143 | リポ実測 | 3 | ✔ | D1′ | 3 |
| 5 | E | 層(地下/デッキ) | 190本+306本 | リポ実測 | 1 | ✔ | — | 2 |
| 6 | E | 地形(Relief) | 空欄(未確認・PLATEAU DEMあり) | — | **0** | — | — | 0 |
| 7 | E | 河川(渋谷川) | 空欄(未確認) | — | **0** | — | — | 0 |
| 8 | E | POI/店舗 | 2,337 | リポ実測 | 2 | ✔ | E1 | 3 |
| 9 | E | 事業所(組織) | 33,398(区)/9,872(13町丁目) | e-Stat | 2 | — | E1 | 3 |
| 10 | E | 住民(エージェント) | 243,883(夜間)/551,344(昼間) | 国勢調査 | 4 | ✔ | F1-3/A群 | 4 |
| 11 | E | 世帯 | 142,463 | 区ポータル【中】 | 1 | — | — | 2 |
| 12 | E | 駅 | 6事業者(渋谷駅) | 各社公式 | 2 | ✔ | D10 | 3 |
| 13 | E | 列車 | ダイヤ1,810本 | ODPT | 3 | ✔ | D10 | 4 |
| 14 | E | バス/タクシー | 空欄(未確認) | — | **0** | — | — | 0(第2陣) |
| 15 | E | 自動車(通過交通) | 道路交通センサスR3 断面 | 国交省 | **0** | — | D5(弱) | 3 |
| 16 | E | 棚在庫(モノ) | 空欄(SKU定義未) | — | **0** | — | — | **4** |
| 17 | E | 廃棄物ストック | 119.6 t/日(区) | 区ポータル | **0** | — | — | **4** |
| 18 | E | 貨幣・口座 | 消費支出 約29万円/月 | 家計調査 | 3 | — | E5/E6 | 4 |
| 19 | E | 屋外広告面 | 空欄(未確認) | — | 0 | — | AD2/3 | 0(第2陣) |
| 20 | E | 都市設備(自販機・街灯・信号・トイレ・ごみ集積所) | 空欄(未確認) | — | **0** | — | — | 0 |
| 21 | P | 天候・気温 | 気象35日 | 手元 | 3 | ✔ | — | 3 |
| 22 | P | 昼夜・日照 | 天文計算 | — | 3 | ✔ | — | 3 |
| 23 | P | 混雑場(密度) | D1′ 24時カーブ | KDDI | 3 | ✔ | D1′ | 3 |
| 24 | P | 騒音場 | ASJ RTN-Model(静的) | — | 3 | ✔ | — | 3 |
| 25 | P | 鉄道運行 | ODPT実ダイヤ | ODPT | 3 | ✔ | D10 | 4 |
| 26 | P | 営業(開閉店) | POI営業時間0件(既定値) | — | 2 | ✔ | — | **4** |
| 27 | P | 補充・納品 | 卸小売6,311事業所・年商1.32億/店 | 経済センサス | **0** | — | — | **4** |
| 28 | P | 廃棄物収集 | 43,663 t/年 | 区 | **0** | — | (新W1) | **4** |
| 29 | P | 宅配ラストマイル | 全国50.3億個/年 | 国交省 | **0** | — | — | 0(第2陣) |
| 30 | P | 価格改定 | 店舗間SD 19-36% | E7 | 2 | — | E7 | 3 |
| 31 | P | 救急・警察出動 | 都935,373件/年 | 東京消防庁 | **0** | — | — | 0(第2陣) |
| 32 | N | ダイヤ・営業時間・価格表(PlanSpec) | 1,810本+営業時間表 | ODPT/既定 | 3 | ✔ | — | 3 |
| 33 | N | 条例・路上規制 | 区例規(路上飲酒禁止) | 区【要一次】 | **0** | — | — | 0(Phase 3) |
| 34 | I | 情報(SNS・口づて・運行情報) | カスケード99%単世代 | C1 | 3 | ✔ | C1/AD5 | 3 |

**素点(w=1の単純版・門を通る見込みのクラスのみ・本レーンの試算)**:
- 現在: d≥1 が 22/34 → **C_all ≈ 0.65**、Σd/(4·34)=48/136 → **D ≈ 0.35**、VERIFIED 7 → **V ≈ 0.21**
- 第1陣(モノの保存則+補充/納品+収集+断面交通+屋内占有)後: d≥1 が 27/34 → **C ≈ 0.79**、Σd=68 → **D ≈ 0.50**、VERIFIED 11 → **V ≈ 0.32**
- **最も安く C と D を上げるのは #6地形・#7河川・#11世帯・#20都市設備の「存在(d1)化」**だが、これらは REACH/VERIFIED が立たないので **V は上がらない**——この指標はまさにそれを可視化するために作る(「安い被覆稼ぎ」を数字の上で無害化する)。

### (c) 報告形(計器盤R14の行・台帳との接続)

計器盤に **6行**を追加(1ランごと・カタログ版を明記):

| 行ID | 出力 | 定義 | 合否 |
|---|---|---|---|
| WC-1 | `world_coverage` | `C_all` / `C_quantified` の2値 | 報告のみ(合否なし) |
| WC-2 | `world_quantity_fit` | `Q`(上振れは加点しない) | 報告のみ |
| WC-3 | `world_depth` | `D`(0-1) | 報告のみ |
| WC-4 | `world_verified_ratio` | `V` | 報告のみ |
| WC-5 | `world_commission` | `X_commission` + 死蔵候補クラス数 | **ゲート**: 前ランより悪化したらPR警告 |
| WC-6 | `world_orphans` | reaches宣言ありで実読0のクラス一覧 | **ゲート**: 非空ならCIが削除候補行を台帳へ追記(D-R2-4の既存機構) |

**台帳との接続**: カタログの各行は `contributes[]` でパターン台帳39行を参照する。**逆引き表(パターン行 → それを支える世界クラス)を自動生成**し、「どのパターン行も支える世界クラスが0本でない」ことをCIで検査する(パターン台帳側の孤児検出)。カタログ行は `docs/design/v2-world-catalog.md`(新設・凍結版)+ `world_catalog.yaml`(機械可読)で二重に持ち、STATUS/PENDING の台帳3ファイルとは独立に版管理する。

### (d) expedient明示(感度試験が必要なもの)

| # | expedient | なぜ | 感度試験 |
|---|---|---|---|
| 1 | **カタログの網羅性そのもの** | 「現実に何があるか」の完全な列挙は不可能(未知の未知)。34クラスは本レーンの判断 | competency questions を20本書き、答えられない質問数を報告。第三者(ユーザー)による追加クラス提案の受け入れ回数を記録 |
| 2 | 重み関数 `w = 1+log10(1+N_real)` | 任意 | 一様重み `w=1` と「パターン依存重み」の3通りでランキングが変わらないことを確認 |
| 3 | 深度 d の順序性(d1<d2<d3<d4) | 「行動由来が過程より深い」はドクトリン由来であって観測ではない | d を順序でなく4フラグのベクトルとしても報告し、結論が変わらないか確認 |
| 4 | クラスの粒度 | 「都市設備」を1クラスにするか5クラスに割るかで C が動く | 粒度2倍/半分の2版でCの変化幅を報告 |
| 5 | 全国値→区への按分(宅配・救急・電力) | 按分係数は根拠なし | 按分を人口比/従業者比/昼間人口比の3通りで振る |
| 6 | bbox の定義差(OSM広域 vs PLATEAU vs 区全域) | 建物7,210 と 6,311 は同じ分母ではない | 分母を bbox・区全域の2本立てで併記(混ぜない) |

---

## 問い7. 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 引用文(本レーンが読んだ文) | 親が確認すべきこと |
|---|---|---|---|---|
| 1 | **ODD要素2が「実体型の列挙+型ごとの状態変数」を要求**——世界カタログの様式的根拠 | https://www.jasss.org/23/2/7.html | 「The element '2. Entities, state variables and scales' lists the different types of entities represented in the model, such as spatial units, agents, and the overall environment」/「For each entity type, the state variables that characterize it are defined. These are variables that may vary among entities of the same type or vary over time」 | (i)**逐語であること**(本レーンの引用は要約器経由=表現が丸められた可能性)(ii)7要素の番号と名称(iii)要素1「Purpose and patterns」がPOMと接続していること |
| 2 | **OSM completeness の測り方と数値**——「被覆率」の先行実装として唯一の定量例 | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0180698 (doi:10.1371/journal.pone.0180698) | 「a stratified and probability-weighted sample of 45 points in each country」/「growth in road length in OSM is characterized in each country by growing interest at the beginning and saturation at the end」/全球83%(CI 81-84)・185か国中77か国が95%超・総延長3,970万km | (i)83%が**エッジ数**基準か**延長**基準か(本文は「edges」と「length」を使い分けている)(ii)「missing edges tend to be shorter → 過小評価」の注記の有無(iii)分母(総道路延長)の推定法が飽和曲線であること=**v2の分母凍結方針との違い** |
| 3 | **ISO 19157 の completeness は omission と commission の二面**——本答申の減点機構の根拠 | https://www.iso.org/standard/78900.html (403) / ICA Wiki https://wiki.icaci.org/index.php?title=ISO_19157:2013_Geographic_information_-_Data_quality | 【検索要約】「Completeness … accounting for both commission (excess data) and omission (missing data)」。**ISO原文・ISO/TC211草案とも本レーンでは本文取得不可** | (i)**逐語定義**(ISO 19157-1:2023 の3.x項)(ii)品質要素5分類の正式名(iii)「data quality scope」の概念(v2の「クラス」に相当するか) |
| 4 | **Atkins/IET・Arup の DT成熟度は6段(Reality capture→Autonomous)**——深度段階の対応付けの根拠 | 検索経由。一次=IET/Atkins ホワイトペーパー(URL未特定)・Arup サイト | 【検索要約】「six successive maturity levels are proposed: Reality capture (level 0), Replication (level 1), Connection (level 2), Synchronization (level 3), Interaction (level 4) and Autonomous (level 5)」 | (i)**一次ホワイトペーパーのURLと段階名の逐語**(ii)段階の判定基準(何をもってLevel 2か)(iii)**v2は現実と同期しない(スナップショットDT)ので Level 3以上は目標でない**という本答申の解釈が妥当か |
| 5 | **CityGML 3.0 のモジュール一覧**(カタログE型の網羅チェックリスト)と**LOD定義の逐語** | https://www.ogc.org/standard/citygml/ (実読) / https://docs.ogc.org/is/20-010/20-010.html (**10MB超で本レーンは取得不能**) | 【実読】「defines a conceptual model and exchange format for the representation, storage and exchange of virtual 3D city models」/モジュール= Building, Transportation, Vegetation, WaterBody, CityFurniture, LandUse, Relief, Tunnel, Bridge, Dynamizer, Versioning | (i)**LOD0-3の逐語定義と LOD4 廃止(屋内をLODから分離)の記述**(ii)Space/Space Boundary の定義(iii)Dynamizer が「時系列で属性を動かす」機構であること=v2の `WorldProcess` との対応(iv)**v2に Relief(地形)と WaterBody(渋谷川)が無い**という本答申の指摘が正しいか |

**併せて申し送る「未確認」**: ISO/IEC 30173:2023 の内容(iso.org 403)/ISO 23247-2 の逐語(ANSIプレビュー403)/ISO 37120 の19テーマ名(iso.org 403)/Gemini Principles 9原則の逐語(CDBB PDFが画像PDF)/PLATEAU LOD定義の逐語(仕様書PDF本文未読)/Grüninger & Fox の competency questions 逐語(著者サイト証明書エラー)/Manheim & Garrabrant の4分類の逐語定義/Kennedy 2007 の定義文(Wiley本文未読)/渋谷区の世帯数142,463・面積15.11km²(検索要約のみ)/ゲームの「シミュレーション深度」の学術的指標(存在を確認できず)。

---

## 参照一覧

**実読(本レーンでページを開いて内容を得たもの)**
- Grimm et al. 2020, "The ODD Protocol for Describing Agent-Based and Other Simulation Models: A Second Update", JASSS 23(2)7 — https://www.jasss.org/23/2/7.html
- Barrington-Leigh & Millard-Ball 2017, "The world's user-generated road map is more than 80% complete", PLOS ONE — https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0180698 (doi:10.1371/journal.pone.0180698)
- OGC, "CityGML" standard page — https://www.ogc.org/standard/citygml/
- 国土交通省 PLATEAU「3D都市モデル標準製品仕様書」(版5.1・2024-03-19・目次のみ) — https://www.mlit.go.jp/plateaudocument/
- Jiang et al. 2021, "Gemini Principles-Based Digital Twin Maturity Model for Asset Management", Sustainability 13(15):8224(UCL Discovery版PDF) — https://discovery.ucl.ac.uk/id/eprint/10133069/1/sustainability-13-08224.pdf (doi:10.3390/su13158224)
- Manheim & Garrabrant, "Categorizing Variants of Goodhart's Law" — https://arxiv.org/abs/1803.04585(4分類名のみ・逐語定義は未確認)

**検索要約のみ(確度中・一次本文未読)**
- CDBB "The Gemini Principles" — https://www.cdbb.cam.ac.uk/system/files/documents/TheGeminiPrinciples.pdf(画像PDFで抽出不可)
- Atkins/IET・Arup DT maturity spectrum(6段)— 一次URL未特定
- ISO/IEC 30173:2023 — https://www.iso.org/standard/81442.html(403)
- ISO 23247-1/-2:2021 — https://www.ap238.org/iso23247/ / https://webstore.ansi.org/preview-pages/ISO/preview_ISO+23247-2-2021.pdf(403)
- ISO 19157(-1) Geographic information — Data quality — https://www.iso.org/standard/78900.html(403)/ ICA Wiki 解説
- ISO 37120:2018 — https://www.iso.org/standard/68498.html(403)/ WCCD https://www.dataforcities.org/iso-37120
- Kennedy et al. 2007, "The Changing Metabolism of Cities", J. Industrial Ecology — https://onlinelibrary.wiley.com/doi/10.1162/jie.2007.1107 (doi:10.1162/jie.2007.1107)
- Grüninger & Fox 1995, "Methodology for the Design and Evaluation of Ontologies", IJCAI Workshop — 著者サイト http://eil.utoronto.ca/(証明書エラー)/ Springer https://link.springer.com/chapter/10.1007/978-0-387-34847-6_3
- OGC CityGML 3.0 Conceptual Model(本文)— https://docs.ogc.org/is/20-010/20-010.html(サイズ超過で取得不能)
- 渋谷区ポータル「世帯数及び男女別人口」 — https://www.city.shibuya.tokyo.jp/kusei/tokei_shibuya/setai_danjyo_betsu_jimko/

**リポ内(読み取り・親検収済みの数値の出所)**
- docs/design/v2-pattern-ledger.md(39行・強5本)/ v2-world-process-design.md(§2 3レコード型・§5 憲法5確定文・D-R2-4)/ v2-methodology.md
- docs/research/v2-world-process-inventory-research.md(過程棚卸し・ごみ43,663t・救急935,373件・宅配50.3億個・陣分け)
- docs/research/v2-world-data-build-research.md(OSM/PLATEAU/街区/セル/層/POIの実測値)
