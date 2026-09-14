# D-R2-2改訂案 敵対的検証レポート

<!-- hdr:v1 -->
- **分野**: ABM方法論 #21 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 66 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

対象: `docs/design/v2-world-process-design.md` の D-R2-2 改訂案(世界過程+計画データの単一台帳統合・2軸分類)
実施: 2026-09-02 / Webリサーチによる反証優先の検証
方針: 支持材料と反証材料を両方探し、どちらが強いかを明示。

---

## ① 結論

### 総合判定: **要修正(結論は残せるが、論拠と分類軸を組み直す必要がある)**

骨子ごとの判定:

| 骨子 | 判定 | 反証の強さ |
|---|---|---|
| 1. 世界過程と計画データを**単一台帳**に統合 | **条件付き支持** | 拮抗。ただし「単一の**レコード形**」は反証される |
| 2. **2軸**(実行様態 × 可変性/改訂権者)で足りる | **反証(不足)** | 強い。4系統の先行研究が独立に第3軸を要求 |
| 3. 決定打「**同じ実体が両方の顔を持つ**」(ダイヤ=計画/フォールバック時=世界過程) | **反証** | 強い。先行例はすべて「別カテゴリの2実体+明示的関係」を採る |
| 4. A/B/C を**導出ラベルに格下げ** | **部分反証** | 中。brute fact / institutional fact の区別は格下げすると失う |

### 修正案(具体・6項目)

**(a) 台帳は1つ、レコード型は3つに分ける。**
先行標準の一致した解は「概念モデルは単一・実装/ストアは分離」。Transmodel(EN 12896)が唯一の概念モデルでありながら、計画は NeTEx、実時間は SIRI、実績は OpRa という**3つの別実装**に落ちるのが典型。したがって:

```
台帳(1つの名前空間・1つのID体系)の中に、3つのレコード型:
  WorldProcess : 状態の定義 / 更新規則 / 時計 / 状態成長宣言 / executor
  PlanSpec     : 有効期間(valid time) / 版(transaction time) / 改訂権者 /
                 規範種別 / 違反可能性 / 公示範囲
  ActualLog    : 追記専用・不変 / 保持窓 / 索引 / 逸脱語彙
関係(第1級):
  realizes(WorldProcess | AgentAction, PlanSpec)
  records(ActualLog, WorldProcess | AgentAction)
  revises(Agent, PlanSpec)      ← 運転整理・値上げはここ
  counts_as(PhysicalFact, InstitutionalFact, Context)   ← 構成的規則
```
現行§2のフィールド構成(`状態の定義 / 更新規則 / 時計 / 状態成長宣言`)は WorldProcess 専用のもので、PlanSpec に押し込むと「ダイヤの更新規則」「価格表の状態成長」という無意味な欄が生まれる。ここが単一レコード形の破綻点。

**(b) 論拠3を差し替える(最重要)。**
「同じ実体が両方の顔を持つ」は分析ミス。フォールバック時に変わっているのは**ダイヤではなく実行主体**である。ダイヤは常に PlanSpec のまま、それを realize する主体が `llm_agent`(乗務員)か `engine_rule`(フォールバック)かが切り替わるだけ。正しい定式化は:

> 一つの PlanSpec に対し、それを実現する executor が差し替わる。
> `executor: {llm_agent | engine_rule | none}` は PlanSpec の属性ではなく、
> realizes 関係のフィールド。

これは §2 が既に持っている「エージェント化計画」フィールドと同じものであり、**設計は自分の中に正解を持っていながら、論拠として誤った方(実体が変質する)を採用している**。この差し替えは統合の結論を壊さない——むしろ conf宣言つきフォールバック台帳(§1末尾)と realizes 関係が一本化され、カバー率・返済期限の管理が自然になる。

**(c) 「逸脱語彙」を最初から第1級に置く。**
遅延をスカラー delay だけで持ってはいけない。GTFS-Realtime は `schedule_relationship` として `SCHEDULED / UNSCHEDULED / CANCELED / REPLACEMENT / DUPLICATED / NEW / DELETED`(trip側)、`SCHEDULED / SKIPPED / NO_DATA / UNSCHEDULED`(stop側)という**列挙型**を持つ。特に `NO_DATA`(実績不明)は、シミュレーションの観測欠損と現実データの観測欠損を同じ語彙で扱えるようにする。D10駅利用者数との照合は「計画との差分」ではなく「この語彙の分布」で見るほうが強い。

**(d) 第3軸(規範種別)と第4軸(違反可能性)を追加。** 詳細は④。

**(e) 軸1に第4の値 `static-affordance`(物理インフラ)を足す。**
道路網・線路・階段・建物は、エンジンが進めるでも、規範でもなく、行動から導出されるでもない。MATSim が `network.xml` を `plans.xml`/`transitSchedule.xml` と別に持ち、railML が Infrastructure サブスキーマを Timetable と分けているのはこの理由。現行案では「路線図」と「線路」が同じ行に入ってしまう(前者は記述=PlanSpec、後者は brute fact)。

**(f) ActualLog に §3-2 の O(t) 禁止則を明示適用。**
実績ログは定義上 O(t) で成長する唯一の実体。OpRa の定義が「**もはや変更できない、運行の記録された現実**」である以上、追記専用・保持窓・増分索引の宣言を型レベルで強制する。runB を殺した構造の最有力再発地点。

---

## ② ユーザーがまず読む大枠

- **「予定(ダイヤ・営業時間)と実際に起きたこと(遅延・臨時休業)を分けて持つ」という考え方そのものは、交通・都市・制度の標準そのままで、正しい。** GTFS(世界標準の交通データ)も、欧州の公共交通標準も、3D都市モデル標準も、全部この分け方をしている。
- ただし**「一つの台帳にまとめる」は半分だけ正しい**。標準はどれも「意味の定義は一つ、保存する場所は3つ(予定/いま/実績)」という形をとっている。予定は「版と有効期間を持つ文書」、実績は「もう書き換えられない記録」で、性質が違いすぎて同じ形の行に収まらない。
- **「ダイヤはエージェントがいるときは予定、いないときは世界過程になる」という決め手の論拠は、たぶん間違っている。** 変わっているのはダイヤではなく「誰が実行するか」。ダイヤはずっとダイヤのまま。設計書の別の場所(「エージェント化計画」欄)がすでに正しい形を持っているので、そちらに寄せれば統合の結論は保てる。
- **2つの軸では足りない。** 少なくとも「破れる規範か、そもそも破れない仕組みか」(信号無視はできるが、所持金を超えた支払いはできない)という軸が要る。これは設計書の「不可逆な資源移動はエンジン」という原則そのもので、すでにあるものを軸として表に出すだけ。
- もう一つ、「そもそも何かを何かとして数える規則」(制服を着た人を駅員として扱う、等)は、予定でも過程でもない第3の種類として、哲学・制度分析・マルチエージェント研究の4系統が独立に必要としている。
- **危険な副作用が一つ**: 実績ログは時間とともに必ず膨らむ唯一の実体で、v1のrunBを止めた構造そのもの。ここに保持窓と索引の宣言を最初から義務づけるべき。

---

## ③ 方面ごとの証拠

### 3-1. MATSim: 計画/実行の分離は交通シミュの標準 —— ただし「計画」が2種類ある

**支持:** MATSim の共進化ループは Initialization → **Mobsim(実行)** → **Scoring** → **Replanning** の反復で、「エージェントは1つの選択された plan を持ち、Mobsim がそれを合成現実の中で**実行**し、**実行された plan の実際の performance** からスコアを計算する」。計画と実行の分離、および両者の差分(実績)からのフィードバックは、交通シミュレーションの標準アーキテクチャである。
- MATSim book (open access): https://www.jstor.org/content/oa_book_edited/j.ctv3t5r7p / PDF: https://library.oapen.org/bitstream/id/859157dd-5478-4089-9fca-b3df7a7a39d4/613715.pdf

**反証(重要):** MATSim は「計画」を**一枚岩にしていない**。入力は少なくとも3系統に分かれる:
- `network.xml` = 物理インフラ(brute fact・誰の計画でもない)
- `transitSchedule.xml` = **世界側の計画**(ダイヤ。運行事業者の規範)
- `plans.xml`(population) = **エージェント側の私的計画**(個人の一日の予定)

本仮説の「計画データ」は2番目だけを指すが、軸1の値 `参照専用(規範)` は1番目と3番目も吸い込みうる形になっている。物理インフラは規範ではない(brute fact)し、個人の予定は世界側の台帳に置くものではない。
- transitSchedule 実例: https://github.com/matsim-org/matsim-libs/blob/master/examples/scenarios/pt-tutorial/transitschedule.xml

**追加の反証(逸脱のコスト):** MATSim の素の設計では、エージェントは Mobsim 実行中に計画から逸脱できない。逸脱を可能にするために **Within-Day Replanning** という専用機構(WithinDayEngine)を後から追加している。
- MATSim book Ch.30 Within-Day Replanning: https://www.jstor.org/stable/j.ctv3t5r7p.37
- Dobler & Nagel, Enhancing MATSim with capabilities of within-day re-planning

→ **v2への含意**: 「ダイヤどおり運行を乗務員のT0習慣に植え、例外時のみLLM昇格」(§1 D-R2-1-2)は within-day replanning そのもの。MATSim では**これが最も重い拡張だった**。予算宣言表(R1)でここのコストを別枠に立てるべき。「運行従事者は数千規模だからコスト影響は限定的」という現行の見積もりは、体数ではなく**昇格イベント頻度**で見直す必要がある(障害1件で全線の乗務員が同時昇格する)。

### 3-2. GTFS / GTFS-Realtime: 計画と実績は別データセット、IDで結合、権威は計画側

**支持(「同じ実体が2つの顔」に部分的に有利):** realtime のエンティティは静的フィードの `trip_id` / `route_id` / `stop_id` と一致しなければならず、`feed_version` でどの静的データセットに整合しているかを示す。つまり**同一の識別子空間**を共有する。
- https://gtfs.org/resources/mobilitydata-recommendations/gtfs-schedule-vs-gtfs-realtime/

**反証(「単一台帳/単一レコード形」に不利):**
1. 両者は**別フォーマット・別フィード・別更新周期・別発行系統**。「GTFS Realtime は予定データを**置き換えるものではなく**、実サービスが計画から乖離した場合を除いて」補完する。
2. 権威は計画側にある: 「事業者は GTFS Schedule を**主かつ権威ある**サービス情報源として既定とすべき」。→ 本仮説の「参照専用」という表現は弱すぎる。計画データは**既定の真理**であって、単なる参照材料ではない。
3. 乖離の表現は差分スカラーではなく**列挙型**: `ScheduleRelationship` = SCHEDULED / UNSCHEDULED / CANCELED / REPLACEMENT / DUPLICATED / NEW / DELETED、停留所側は SCHEDULED / SKIPPED / NO_DATA / UNSCHEDULED。遅延は `delay`(秒・正負)または絶対 POSIX 時刻。
   - https://gtfs.org/documentation/realtime/reference/
   - https://developers.google.com/transit/gtfs-realtime
4. さらに近年、**計画そのものを実行時に書き換える**ための仕様(Trip Modifications = 迂回等)が追加されている。計画は「参照専用」ではなく実行時に改訂される。
   - https://github.com/google/transit/blob/master/gtfs-realtime/spec/en/trip-modifications.md

**判定:** GTFS は「一つのID体系・別々のストア」。仮説の「一つの台帳」は**識別子とオントロジーのレベルでは支持され、ストアとレコード形のレベルでは反証される**。

### 3-3. Transmodel / NeTEx / SIRI / OpRa —— 本件で最も直接的な先行例

**支持(最強):** Transmodel(EN 12896)は公共交通の**単一の参照データモデル**で、「ある概念はどの Transmodel ドメインでも同一かつ一意の意味を持つ」という意味的相互運用性を提供する。10部構成(Part 1 共通概念 / Part 2 ネットワーク / Part 3 タイミングと車両運用 / Part 4 運行監視制御 / Part 5 運賃 / Part 6 旅客情報(計画+実時間) / Part 7 乗務員管理 / Part 8 管理情報と統計 …)。**計画・実時間・実績を一つの概念モデルが貫いている** —— 仮説1の直接的な先行例。
- https://transmodel-cen.eu/index.php/about/
- https://data4pt-project.eu/data-models/transmodel/

**同時に反証(実装は3分割):** 「Transmodel のデータ構造は、計画(静的)データ用の **NeTEx**、実時間(動的)データ用の **SIRI**、観測データ用の **OpRa** という交換標準として実装される」。
- https://data4pt-project.eu/data-models/

**OpRa の定義が決定的:** OpRa は「**実際の・計測された情報であって、もはや将来変更されえないもの**、すなわち遅延やキャンセルされた車両ジャーニーのような、記録された運行の現実」を対象とする。
- https://transmodel-cen.eu/index.php/opra/
- CEN プロジェクト計画: https://www.cencenelec.eu/media/CEN-CENELEC/News/CallForTender/Documents/2023/OpRa/opraprojectplan.pdf
- CEN/TR 17370

→ **計画は改訂可能・実績は不変**。これは可変性軸の1点ではなく、**書き込みモードの型的な違い**(revisable document vs append-only log)。

**「2つの顔」への最良の回答:** Transmodel は同一実体に2つの顔を持たせるのではなく、**型を分けて関係で結ぶ**。`ServiceJourney`(計画上の運行=型)に対し、`DatedVehicleJourney` = 「特定の運行日に適用された、計画のスケジューリング過程で構成された正確な写像」。そして「DatedVehicleJourney は実時間に追加・変更されうるため、主に SIRI のスコープにある」。
- https://entur.atlassian.net/wiki/spaces/PUBLIC/pages/728760393/timetable
- https://github.com/NeTEx-CEN/NeTEx/issues/292

→ **v2への直輸入**: `PlanSpec(ダイヤ型)` → `DatedInstance(運行日ごとの実体)` → `ActualLog(実績)`。この3段が業界の答え。

### 3-4. 規範的MAS(normative MAS / electronic institutions / OperA / SAI): 規範表現の必須属性

**規範表現に必須とされている属性(仮説の2軸に無いもの):**
- **義務種別(deontic)**: 義務 / 許可 / 禁止。これが無いと「ダイヤどおり走る**べき**」と「ダイヤどおり走**れる**」を区別できない。
- **条件・期限(deadline)**、**制裁(sanction)/報酬(reward)**。
- **ライフサイクル**: 生成 → 拡散 → 内面化 → 忘却 → 変換(あるいは 生成/同定/採用/伝播/創発)。
- **公示・認知(promulgation / norm awareness)**: 「規範がドメインで有効であるためには、エージェントがまずその存在を**検知**しなければならない」。新規エージェントは社会の規範を知らされる必要がある。
  - Dagstuhl Seminar 07122 Normative MAS: https://www.dagstuhl.de/07122/
  - Towards an Adaptive and Normative MAS Metamodel: https://arxiv.org/pdf/2111.13084
  - 規範創発の系統的レビュー: https://arxiv.org/html/2412.10609v1

**強制様態の二分法(仮説に無い・かつ v2 の engine/LLM 線引きに直結):**
Grossi / Aldewereld / Dignum, *Ubi Lex, Ibi Poena: Designing Norm Enforcement in E-Institutions*:
> **regimentation** は、違反を**そもそも不可能にする**ことで期待どおりに振る舞わせる戦略。
> **enforcement** は、違反が**起こりうる**前提で、監視エージェントが検知し制裁/報酬を適用する反応。
- https://link.springer.com/chapter/10.1007/978-3-540-74459-7_7
- Norm enforceability in Electronic Institutions (IIIA): https://www.iiia.csic.es/media/filer_public/b1/d3/b1d3d503-7cad-44c8-97dc-f3e4e8bfb547/4547.pdf

→ v2 の原則1「不可逆な資源移動はエンジン(不足時は無効化)」= **regimentation**。原則6「裁定は判例化」= **enforcement**。設計にはすでに両方があるが、**台帳の分類軸として露出していない**。

**構成的/規制的の二分(4系統目の独立支持):**
OperA は「組織構造を**構成する** constitutive norms と、役割の権利義務を**定める** regulative norms」を明示的に区別する。
- Dignum, Organizing Multiagent Systems: https://link.springer.com/article/10.1007/s10458-005-1673-9
- OperA 博士論文: https://dspace.library.uu.nl/bitstream/handle/1874/890/full.pdf

**Situated Artificial Institutions (de Brito / Hübner / Boissier) —— v2 に最も近い設計:**
> SAI の概念モデルは **2つの軸**に沿って構造化される: **norms** と **constitutive rules**。
> 規範は **status function** を参照する。status function は constitutive rules を通じた**環境的事実の制度的解釈**である。
> 制度が situated であるとは、それが行う規制の全体が、エージェントが行為する環境で生じる事実に基づいていること。
- 概念モデル: https://link.springer.com/chapter/10.1007/978-3-319-09764-0_3
- AAMAS journal 版: https://link.springer.com/article/10.1007/s10458-017-9379-3
- 規制次元と構成次元の結合: https://link.springer.com/chapter/10.1007/978-3-319-33509-4_25

→ **SAI もまた「2軸」を採るが、その2軸は本仮説の2軸と違う**。SAI の2軸は (規範, 構成的規則)。本仮説の2軸は (実行様態, 可変性)。SAI は「環境の生の事実 → 制度的事実」の変換規則を第1級に置いており、これが本仮説に完全に欠けている。

### 3-5. Crawford & Ostrom ADICO と Institutional Grammar 2.0

**ADICO(1995):** Attribute / Deontic / aIm / Conditions / **Or else**。
- **共有戦略** = AIC(deontic も制裁もない)
- **規範** = ADIC(deontic あり、制裁なし)
- **ルール** = ADICO(制裁あり)
- https://www.semanticscholar.org/paper/A-Grammar-of-Institutions-Crawford-Ostrom/e2582728285ec5ceceeb904176b496cf94a46753
- 適用手順: Basurto et al. 2010, https://journals.sagepub.com/doi/10.1177/1065912909334430

→ **本仮説の「計画データ」は、この階梯の3段すべてを1つのラベルに潰している**: ダイヤ(事業者内では制裁つきルール、乗客には情報)、営業時間表(規範~共有戦略)、価格表(情報~戦略)、路線図(記述であって規範ですらない)。可変性軸ではこの3段は区別できない(改訂権者が同じでも deontic 強度は違う)。

**反証材料(制裁軸をそのまま使うことへの警告):** Schlüter & Theesfeld は「**or else の同定の困難**」を指摘。「or else だけを弁別因子とすると、たとえばある国の法律が or else を欠くというだけで法ではなく規範になってしまう」「戦略や規範にはしばしば**暗黙の or else** がある」。
- https://journals.sagepub.com/doi/10.1177/1043463110377299

→ **含意**: 制裁の有無を軸にするなら、「明示された制裁」ではなく「**誰が検知し誰が反応するか**」(監視主体と反応主体)としてオペレーショナルに定義すべき。v2 では 16行表の行12(検知確率=エンジン)/行14(裁定=LLM+判例)がすでにその実体を持っている。

**IG 2.0(Frantz & Siddiki 2021)—— 「2軸で足りるか」への直接の答え:**
> 規制的言明の符号化に加え、IG 2.0 は**構成的**制度言明、および構成的性格と規制的性格の**両方**を示す言明の符号化を導入する。構成的言明は規制的言明と構造的・意味的性質において**異なる**。
> 構成的言明は制度的セッティングを**パラメータ化**し、アクターの地位や役割、それに伴うアフォーダンス、過程、環境的特性、対象物・人工物といった制度システムの特徴を導入・修正・構成する。
- arXiv Codebook: https://arxiv.org/abs/2008.08937
- Public Administration 誌: https://onlinelibrary.wiley.com/doi/10.1111/padm.12719
- 構成的言明シンタックス解説: https://institutionalgrammar.org/research_seminar/constitutive-statement-syntax-under-the-institutional-grammar-2-0/

→ **制度分析の分野は、ADICO 一本(=規制的言明のみ)では足りないと結論し、25年かけて第2のシンタックスを追加した**。本仮説が「可変性軸」1本で規範側を畳もうとしているのは、この歴史を踏み外す方向。

### 3-6. Searle: 制度的事実 —— 「参照専用の規範が現実に存在する」の哲学的基礎

**支持:** 「Searle によれば、制度的事実は、既存の対象・人・事態への status-function(地位機能)の**集団的付与**によって作られる」。構成的規則の構文は **X counts as Y in context C**。
- Searle, Constitutive Rules (Argumenta): https://www.argumenta.org/wp-content/uploads/2018/11/4-Argumenta-41-John-R.-Searle-Constitutive-Rules.pdf
- Hindriks, Constitutive Rules, Language, and Ontology: https://link.springer.com/article/10.1007/s10670-009-9178-6
- Sileno, Revisiting Constitutive Rules: https://pure.uva.nl/ws/files/39126704/Sileno2018_Chapter_RevisitingConstitutiveRules.pdf
- Searle 理論の解説(Buffalo): http://ontology.buffalo.edu/FARBER/atria.html

**反証(骨子4への打撃):** Searle は **brute fact / institutional fact** を第1級の区別として立てる。「制度から独立に存在する事実は brute fact」であり、制度的事実は構成的規則を**前提とする**。

これは本仮説の A類(天候)と計画データ(ダイヤ)の違いそのものであり、**「導出ラベルに格下げ」してよい種類の区別ではない**。実装上の差は決定的:
- 天候は、全エージェントが天気を知らなくても雨が降る(brute)。
- ダイヤは、誰も参照しなくなれば**存在をやめる**(institutional・集団的受容に依存)。

さらに Searle は**構成的規則と規制的規則**を区別する:「規制的規則は先行的・独立に存在する行動形式を規制する。構成的規則は単に規制するのではなく、新しい行動形式を**創造ないし定義**する」。ダイヤは規制的、「これは駅である」「この紙は運賃である」は構成的。

**Bicchieri からの追加の反証(規範の所在):** 社会規範への同調選好は「**経験的期待**(他者がその行動をとるという一次的信念)」と「**規範的期待**(他者がそうすべきだと信じているという二次的信念)」に**条件づけられている**。慣習は規範的側面を欠く点で社会規範と異なる。
- Stanford Encyclopedia, Social Norms: https://plato.stanford.edu/entries/social-norms/
- Bicchieri, Measuring Social Norms: https://www.irh.org/wp-content/uploads/2016/09/Bicchieri_MeasuringSocialNorms.pdf

→ **含意**: 規範を「世界側の台帳のレコード」として置くだけでは、規範として機能しない。規範の拘束力は**エージェント側の期待分布**にある。v2 の憲法5(知覚契約経由で届く)はこれに近いが、**届いた後にエージェント集団の期待になっているか**は別問題。台帳の PlanSpec には「公示範囲(誰に届く)」だけでなく「**遵守率の観測欄**」が要る(規範が死んでいることを検出できないと、歪みの宣言ができない)。

### 3-7. 上位オントロジー(BFO/IAO・DOLCE): 「同じ実体が両方の顔」への最も鋭い反証

**IAO / BFO(生物医学領域の事実上の標準):**
- `plan specification` は **directive information entity** の下位クラスで、「action specification と objective specification を部分として持ち、**具体化された(concretized)とき**に、担い手が指定された行為をとって目的を達成しようとする**過程において実現される(realized)**指令的情報実体」。
- `planned process` は「あらかじめ定められた計画に従って遂行される過程」を包含する bfo:process の特殊型。
- BFO は実体を **Continuant(持続体)** と **Occurrent(生起体・時間的部分を持つ)** に分ける。
- 計画仕様と過程は **realizable concretization** を介して結ばれる。
- Concretizing plan specifications as realizables within the OBO foundry (J. Biomedical Semantics 2024): https://link.springer.com/article/10.1186/s13326-024-00315-0 / https://pmc.ncbi.nlm.nih.gov/articles/PMC11334599/

**DOLCE の Descriptions & Situations:**
> Situation は S-Description を「**満たす(satisfy)**」。Description は **Non-Physical-Endurant** の下位範疇である。
> Situation は表象(description)の「**現実の(actual)**」対応物である。
- DOLCE (Applied Ontology 2022): https://dl.acm.org/doi/abs/10.3233/AO-210259 / https://www.danieleporello.net/papers/BorgoEtAlAO2022.pdf
- Gangemi, Norms and plans as unification criteria for social collectives: https://link.springer.com/article/10.1007/s10458-008-9038-9

**判定:** 少なくとも2つの主要な上位オントロジー体系が、**計画(記述・持続体・情報実体)と過程(生起体)を最上位で別カテゴリとして分け、明示的な関係(realizes / satisfies / concretizes)で結ぶ**。「同じ実体が両方の顔を持つ」という定式化を採る先行例は見つからなかった。すべて「2実体+関係」である。

**ただし v2 に有利な読み替え:** 「一つの台帳」を「**一つのオントロジー**」と読むなら支持される。DOLCE も IAO も、Description と Situation を**同じオントロジーの中に**置いている。分けているのは**カテゴリ**であってリポジトリではない。→ 修正案(a)はこの読み替え。

### 3-8. 都市デジタルツインのオントロジー

**CityGML 3.0 —— 「速い変化」と「遅い変化」を別モジュールにした:**
- **Dynamizer モジュール**: 「都市オブジェクトの属性についての時変データを表現・交換する概念(例: 一日の日射)、およびセンサを3D都市モデルに統合する概念を定義」。データ源はインラインの時系列、外部ファイル、センサWebサービス。
- **Versioning モジュール**: 「都市オブジェクトの複数の版(例: 履歴や**代替設計**)を一つの都市モデルデータセット内で明示的に表現・交換することを可能にする」。「**すべてのオブジェクトが bitemporal な lifespan データを持てる**」。
- 「**速い動的変化は Dynamizer が、遅い変化は Versioning が扱う**」。
- OGC CityGML 3.0 Users Guide: https://docs.ogc.org/guides/20-066.html (§7.6 Modeling Dynamic Data, §7.6.1 Versioning and Histories, §7.6.2 Dynamizers, §8.6 Dynamizer, §8.13 Versioning)
- TUM: https://www.asg.ed.tum.de/en/gis/projects/citygml-30/
- Kutzner/Chaturvedi/Kolbe, CityGML 3.0: New Functions Open Up New Applications (PFG 2020): https://link.springer.com/article/10.1007/s41064-020-00095-z

→ **仮説にとっての含意(両刃)**: (支持)Dynamizer は静的属性に動的値を「重ねる」= 同一オブジェクトが静的な顔と動的な顔を持つ。(反証)しかし**変化速度で別モジュールに分けている**。しかも Versioning は **bitemporal**(有効時間 × 記録時間)を要求する。1つのレコード形では bitemporal を扱えない。

**INSPIRE Land Use —— 計画と現況を別の application schema にした:**
INSPIRE の Land Use は `ExistingLandUse`(現況)と `PlannedLandUse`(計画)を**別々のアプリケーションスキーマ**として定義する。土地利用は「現在および将来の計画された機能的次元」で特徴づけられる領域と定義される。
- Data Specification on Land Use (D2.8.III.4): https://inspire-mif.github.io/technical-guidelines/data/lu/dataspecification_lu.pdf
- Feature Catalogue: https://inspire-mif.github.io/uml-models/draft/fc/

→ **反証**: 都市の「現況」と「計画」を統合せず、意図的に別スキーマにした欧州の判断。同じ地物(この街区)が現況と計画の両方の顔を持つのに、である。理由は改訂主体・法的効力・更新周期が違うから。**v2の渋谷でいえば、都市計画決定の用途地域と実際の店舗分布を同じレコード型に入れてはいけない**。

**railML:** Infrastructure(IS)/ Interlocking(IL)/ Timetable(TT)/ Rollingstock(RS)/ Common(CO) の**サブスキーマ分割**。物理インフラと運行制御ロジックと時刻表が別。
- https://wiki3.railml.org/wiki/Main_Page

**NGSI-LD / FIWARE:** `observedAt`(その値が有効になった/観測された時刻)と `createdAt`/`modifiedAt`(システムに投入された/修正された時刻)を**別のメタデータとして**区別する。=bitemporal の簡易版。「計画 vs 実績」の第1級の区別は無い(ここは弱い先行例)。
- ETSI White Paper No.42, Guidelines for Modelling with NGSI-LD: https://www.etsi.org/images/files/ETSIWhitePapers/etsi_wp_42_NGSI_LD.pdf

**PLATEAU:** CityGML + i-UR(i-Urban Regeneration)技術仕様を採用し、都市計画情報等を Domain Extension で拡張。
- https://www.mlit.go.jp/plateau/
- 導入ガイダンス: https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_doc_0000_ver04.pdf
- ※ 都市計画決定情報が独立の feature type かは一次資料で未確認(⑤参照)

### 3-9. 鉄道運行の現実: 「参照専用」という語が現実と衝突する

障害時、「多数の列車が本来のダイヤから逸脱せざるを得ず、運行整理は指令員が**計画ダイヤを実時間で調整する**ことを要求する。順序変更(reordering)・時刻変更(retiming)・経路変更(rerouting)といった戦略による」。実時間の再スケジューリングは「実行可能な到着・出発時刻の**新しいダイヤを再計算する**」。
- A Railway Timetable Rescheduling Approach for Handling Large-Scale Disruptions (Transportation Science): https://dl.acm.org/doi/abs/10.1287/trsc.2015.0618
- Train rescheduling for large-scale disruptions: https://www.sciencedirect.com/science/article/abs/pii/S019126152300111X
- Real-time Railway Traffic Management (Dispatching): https://link.springer.com/article/10.1007/s11067-008-9088-1

→ **v2への含意**: 遅延・見合わせ・増発が乗務員個体の判断から創発する、という D-R2-1-2 の設計は**現実と食い違う**。実務では**指令員(運行管理者)という単一の改訂権者が計画そのものを書き換え**、乗務員はその改訂版に従う。渋谷の各社に「指令エージェント」を1体ずつ置き、`revises(指令, PlanSpec)` を発火させる形にしないと、乗務員個体の局所判断からは現実の運転整理パターン(順序変更・折り返し)は出てこない。これはパターン台帳の照合精度に直結する。

### 3-10. 検証可能性(横断的な警告)

LLMベース社会シミュレーションのレビューは「**検証(validation)が生成的社会シミュレーションの中心的課題**」であり、「研究はしばしば表面妥当性や、基礎メカニズムに緩くしか結びつかないアウトカム指標に依存する」「LLM の使用は、そのブラックボックス構造・文化的バイアス・確率的出力ゆえに、ABM の検証課題を**緩和するどころか悪化させうる**」と指摘する。
- Validation is the central challenge for generative social simulation (AI Review 2025): https://link.springer.com/article/10.1007/s10462-025-11412-6
- Do LLMs Solve the Problems of Agent-Based Modeling?: https://arxiv.org/pdf/2504.03274
- Epstein, Generative social science: https://onlinelibrary.wiley.com/doi/10.1002/(SICI)1099-0526(199905/06)4:5%3C41::AID-CPLX9%3E3.0.CO;2-F

→ **PlanSpec / ActualLog の分離は、実は検証装置として最も価値がある**。計画と実績を分けて持つと「計画からの逸脱分布」が直接の観測量になり、現実の遅延分布(ODPT)と突き合わせられる。統合して1つの状態にすると、この検証量が失われる。**分離を維持する最強の理由は、オントロジーではなく検証可能性**。

---

## ④ 2軸で畳めない反例・欠けている軸の候補

### 反例(現行2軸では区別できないが実装が異なるペア)

| # | 反例 | 2軸ではどうなるか | なぜ畳めないか |
|---|---|---|---|
| R1 | **所持金の保存則** vs **一方通行標識** | どちらも「参照専用(規範)」× 「改訂権者=制度/不可」 | 前者は**違反不能**(engine が無効化)、後者は**違反可能**(検知確率+裁定)。実装経路が完全に別。→ regimentation vs enforcement |
| R2 | **線路・道路網・階段** | 軸1のどの値にも入らない | エンジンが進めない・規範ではない・行動から導出でもない。brute fact の物理アフォーダンス。MATSim `network.xml`・railML IS が別扱いする理由 |
| R3 | **「制服を着た者は駅員として扱われる」** | 軸1に受け皿なし | 状態を変えず、参照されるだけでもない。**他実体の分類を決める**構成的規則(X counts as Y in C)。IG2.0 が別シンタックスを起こし、OperA と SAI が別次元を立てた対象 |
| R4 | **混雑場(集約)** vs **遅延実績ログ** | どちらも「行動から導出(集約)」 | 前者は O(1) 状態(グリッド密度)、後者は **O(t) の不変追記記録**。OpRa 定義「もはや変更されえない」。同じ扱いにすると runB を殺した構造がそのまま復活する(§3-2 の直接適用先) |
| R5 | **ダイヤ** vs **営業時間表** vs **路線図** | すべて「計画データ」 | ADICO 階梯で ルール(制裁つき) / 規範 / 単なる記述。deontic 強度が3段違う。改訂権者が同じでも従属の強さが違う |
| R6 | **価格表** | §1 では計画データ、§4行5 では店主LLMのスカラー出力 | 改訂権者が**それに従う当人**。規範として機能するには他者の期待(Bicchieri の経験的/規範的期待)が要る。自己改訂可能な「規範」は規範でなく戦略 |
| R7 | **障害時のダイヤ** | 「参照専用」のはずが実行時に書き換わる | 運転整理・GTFS-RT ADDED/REPLACEMENT/DELETED。軸1の値名「参照専用」が誤導的。正しくは「**エンジンが自律的に進めない**」であって「読み取り専用」ではない |
| R8 | **天候** vs **ダイヤ** | 骨子4で両方「導出ラベル」に格下げ | brute fact vs institutional fact。誰も知らなくても雨は降るが、誰も参照しないダイヤは存在をやめる。存在条件が違う |

### 欠けている軸の候補(優先順)

**軸3(最優先): 規範種別 = `constitutive` / `regulative` / `brute-physical` / `descriptive-only`**
- 独立支持4系統: Searle(構成的/規制的)・OperA(constitutive norms / regulative norms)・IG 2.0(構成的言明の別シンタックス)・SAI(2軸=norms × constitutive rules)。
- 分野が4つとも独立に同じ結論に到達している = v2 の他の設計判断(4答申の独立収束を採用理由にした前例)と同じ強度の証拠。
- 実装上の意味: 構成的規則は `counts_as(PhysicalFact, InstitutionalFact, Context)` としてエンジンの解釈層になる(=SAI の「制度的解釈」)。これは 16行表のどの行にも無い。

**軸4(次点): 違反可能性・強制様態 = `regimented`(違反不能) / `enforced`(違反可能+検知+制裁) / `unenforced`(逸脱自由)**
- Grossi/Aldewereld/Dignum。可変性軸と**直交**する(R1が示す)。
- v2 にはすでに実体がある(原則1 = regimentation、原則6+行12+行14 = enforcement)。**新概念の追加ではなく、既存の暗黙構造を軸として露出させるだけ**なので導入コストが低い。
- 制裁を「明示された or else」で定義すると Schlüter & Theesfeld の指摘する曖昧性に陥るので、「**誰が検知し誰が反応するか**」で定義すること。

**軸5: 時間意味論 = `continuous-state` / `versioned-document(bitemporal)` / `append-only-event`**
- CityGML の bitemporal lifespan、OpRa の不変性、GTFS の feed_version、NGSI-LD の observedAt vs modifiedAt、bitemporal DB の valid time / transaction time が全部これ。
- **§3-2「状態成長の宣言」と直結**: append-only は定義上 O(t)。ここに保持窓と増分索引を型で強制できる。予算宣言表 P4 との接続点(D-R2-6)がここで自然に決まる。

**補助軸: 公示・到達性 = `who knows` × `遵守率の観測`**
- norm-aware MAS が必須とする promulgation。憲法5(知覚契約経由で届く)は「届くか」を宣言するが、「届いた結果、集団の期待になっているか」は測っていない。
- 規範が死んでいることを検出できないと「歪む場所の宣言」ができない。

**軸の数について:** 軸を5本に増やすのは運用上重い。実際には **軸1(実行様態・4値に拡張)+ 軸2(可変性・改訂権者)+ 軸3(規範種別)+ 軸4(違反可能性)** の4軸で、軸5は WorldProcess/PlanSpec/ActualLog という**レコード型そのもの**が担うので独立の軸にしなくてよい(修正案(a)を採るなら)。

---

## ⑤ 未発見・不確実項目(正直な列挙)

**一次資料に当たれなかったもの:**
1. **IG 2.0 の構成的シンタックスの正確なコンポーネント記号**(E=Constituted Entity, M=Modal, F=Constitutive Function, P=Constituting Properties と推定)。arXiv abstract と解説ページ止まりで、Codebook 本文 PDF を読んでいない。「構成的言明という別シンタックスが必要とされた」事実は確認済みだが、その内部構造は未確認。
2. **CityGML 3.0 Dynamizer が静的属性値を「上書きする」という規範的文言**。TUM ページと解説論文の記述に依拠。OGC 標準本文(20-010)の該当節を未確認。「動的値が静的値をオーバーライドする」は解説側の表現。
3. **railML における planned / actual の区別**。TT サブスキーマ内に実績データを持つのか、別の仕組みかを確認できなかった。サブスキーマ分割(IS/IL/TT/RS)は確認済み。
4. **PLATEAU の都市計画決定情報が独立の feature type かどうか**。i-UR 仕様書の一次確認をしていない。日本ローカルの先行例として本来最も重要だが、検索が仕様書本文に届かなかった。
5. **Transmodel の Part 番号と NeTEx/SIRI の対応**。about ページの記述に依拠しており、出典間で Part 4(運行監視制御)と Part 6(旅客情報)のどちらが SIRI に対応するかの記述にずれがある。Part の存在自体は確実だが番号の対応は要確認。
6. **日本の運転整理の実務仕様**(JR東・東京メトロ等の指令システムの意思決定構造)。学術論文経由の一般論のみ。渋谷の実際の指令体制(会社ごとの指令所の粒度、乗務員への伝達経路)は未調査だが、これは D-R2-1-2 のエージェント設計に直結する。
7. **Barry Smith による Searle 批判**(free-standing Y terms: 物理的担い手を持たない制度的対象)。存在は認識しているが確認していない。「計画データは物理的担い手を必要とするか」という問いに関わる。

**構造的に不確実なもの(見つからなかったこと自体が情報):**
8. **「計画と実績を単一のレコード型に統合して失敗した事例」の直接証拠は見つからなかった。** 反証の強度は「主要標準がすべて分離を選んでいる」という**業界慣行の一致**によるものであり、決定的な失敗実験ではない。単一レコード形が実際に破綻することの直接証明はしていない。この点で私の反証は「強い状況証拠」であって「証明」ではない。
9. **「同じ実体が両方の顔を持つ」を採る先行例を探したが見つからなかった。** ただし「無いことの証明」はできていない。特にゲーム/シミュレーション実装(除外指定された領域)には存在するかもしれない。
10. **LLM エージェントが規範文書(ダイヤ・営業時間)を参照して行動する際の忠実度**の実証研究を調べていない。「T0習慣として植え、例外時のみ昇格」の妥当性は未検証。within-day replanning のコスト推定(3-1)は MATSim の経験からの類推であり、LLM エージェントでの実測ではない。
11. **軸を4本に増やしたときの運用負荷**(パターン台帳との二重門前条件の記入コスト)を見積もっていない。軸の増加は R1 予算宣言表の記入項目増につながる。

---

## 付録: 判定の要約(支持 vs 反証のどちらが強いか)

- **骨子1(単一台帳)**: 支持(Transmodel の単一概念モデル・GTFS の単一ID空間・DOLCE/IAO が同一オントロジー内)と 反証(NeTEx/SIRI/OpRa の3実装・GTFS の別フィード・INSPIRE の別スキーマ・railML の別サブスキーマ・CityGML の別モジュール)が**拮抗**。→ 「概念1・レコード型3」で両立可能。**支持がわずかに強い**が、無条件の統合は反証される。
- **骨子2(2軸)**: **反証が明確に強い**。Searle / OperA / IG 2.0 / SAI の4系統が独立に第3軸を要求し、Grossi et al. が第4軸を要求する。反例 R1-R8 のうち R1・R2・R3・R4 は2軸では原理的に畳めない。
- **骨子3(同じ実体が両方の顔)**: **反証が強い**。IAO(plan specification / planned process + concretizes)、DOLCE(Description / Situation + satisfies)、Transmodel(ServiceJourney / DatedVehicleJourney)、GTFS(static trip / TripDescriptor + schedule_relationship)——調べた全先行例が「2実体+関係」を採る。加えて、この論拠の内部にも欠陥がある(変わるのは実体ではなく executor)。**論拠としては使えない**が、結論(統合)は別の論拠(Transmodel の単一概念モデル)で支えられる。
- **骨子4(A/B/C の格下げ)**: **部分反証**。導出ラベルにしてよいのは B類(域外)と C類(集約)。A類(自然過程)と計画データの違いは Searle の brute/institutional であり、存在条件が違うため第1級の区別として残すべき。
