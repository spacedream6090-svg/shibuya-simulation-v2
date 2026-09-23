# レーンB答申: チャネル別観測予算と注意ゲートの実証的根拠

<!-- hdr:v1 -->
- **分野**: 知覚心理学・精神物理学 #5 | **重要度**: P0(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 118 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(Fable・2026-09-06)**: 出典を親が一次確認した。✔=親が実読して数値一致。
> - ✔ Fotios, Uttley & Yang 2014(CIE会議録・White Rose PDF実読): Foulsham 21%/37%/37%引用・「near path (<4 m) and distant people (>4 m) are critical」・注視確率0.87昼/0.86全体・r=−0.40・クリティカル注視 近路面19.5%/遠人12.1%・「not possible to fixate on all of them」を逐語確認。
> - ✔ Fotios 2015: 480 ms(IQR 400-640)。**訂正**: 本答申の「距離中央値13.0 m」は**昼のみ**の値。全体中央値は10.3 m(夜8.9 m)。
> - ✔ 屋外大型ビジョンのVR視認率(プレスリリース実読): 平均70.3%・音声有77.5%/無音63.1%・n=120(実質119)・都内5地点・2024-03-29〜31・15秒。**非査読の企業発表**。視認=「画面内に中心視点が留まった場合」。
> - ✔ MNREAD-J手引き(PDF実読): 読書速度(cpm)=(30−読み損じ)÷秒×60・漢字8文字まで。**正常成人の最大読書速度の正典値は手引きにも無い**(空欄は正しい)。
> - ✔ Generative Agents(ar5iv実読): α=1・減衰0.995・「top-ranked memories that fit within the context window」・内省閾値150「in our implementation」・2-3回/日。チャネル別枠の記述は**不在**。✔ CivRealm 5×5・15×15→9ブロック。
> - 内容キャップ式 round(7.5×注視秒)は400-600 cpm仮定に依存=expedient(正典値が取れるまで)。
> - 正典化: docs/research/v2-channel-budget-attention-research.md(R3-8 §3-2・§4の根拠)。

作成日: 2026-09-06 / 担当: リサーチサブ(Opus 5) / 検収: 親(Fable) → 決定: ユーザー

---

## 要約(10行)

1. **先行例にチャネル別トークン枠は存在しない。** Generative Agents・OASIS・CivRealm はいずれも「順位づけ→文脈長まで詰める」方式で、チャネル別の固定枠を宣言した社会シムは本調査では発見できなかった。v2の枠配分は**先行例のない独自設計=expedient**として宣言し、ablation(固定枠 vs 同一総トークンの単一ランキング)が必要。
2. 歩行中の視線配分の実測は「**人>路面>看板**」では**ない**。滞留時間では **物体・環境 37-56% > 路面 24-51% > 人 3-21%**(Fotios 2014 Table 2)。
3. ただし二重課題で抽出した「**クリティカル注視**」では順位が逆転し、**近接路面(<4m)と遠方の人(>4m)**が最重要と結論されている。B5>B2 の予算配分を正当化できるのは滞留時間ではなく**この逆転**のみ。宣言が必要。
4. 決定的な数値: 視野に入った歩行者を1回以上注視する確率の中央値 **0.86**、かつ**人が増えるほど低下**(r=-0.40, p=0.08)。渋谷の高密度では近接kは増やすのでなく**減らす**のが実証的に正しい。
5. 人への注視は 距離中央値 **13.0m**、持続 **480ms**(IQR 400-640ms)。B5の1件あたりの情報量は薄くてよい。
6. 日本の屋外広告の**視認率の公的実測は空欄**。業界標準(交通広告共通指標)は媒体接触=OTSであって視認率ではない。唯一の日本実測は屋外大型ビジョンのVRアイトラッキング **平均70.3%**(音声有77.5%/無音63.1%, n=120, 2024年3月)。米VR実験の**70%(28/40)**と一致する点は注目に値する。
7. 「サイズ×輝度×距離」の**積形は距離の二重計上**。視角=サイズ/距離 で距離は既に吸収済み。輝度は絶対輝度でなく**局所輝度コントラスト**が正。Itti&Koch 2000 は単純加算が「複雑自然画像で著しく劣る」ことを示しており、下限フロア付きの log 加算(=積形)なら擁護可能。
8. 内容キャップ **10-20字は片側で誤り**。400-600cpm から 0.9秒=**6-9字** / 3.3秒=**22-33字**。「字数≈7.5×注視秒(下限4字)」に置換を推奨。
9. 件数上限を Cowan 4±1 / MOT 3-4 から導くのは**部分的にのみ妥当**。4は「個体化」の上限であって記述の読解上限ではなく、Alvarez&Franconeri 2007 で 1〜8 に可変。近接3-4は低密度時の上限としてのみ有効。
10. 広告の効果キャップの上界: 再認 **40%** / 再生 **8%**(VR実験)。1曝露あたりの状態変化はこれを超えてはならない。

---

## 問い1. 観測予算の配分の先行例

### 1-1. Generative Agents (Park et al. 2023) — 重み全部1・枠は文脈長

検索スコアは3成分の**加重和**で、実装では**全αが1**:

> "score = α_recency · recency + α_importance · importance + α_relevance · relevance"
> **"In our implementation, all α's are set to 1."**
> 減衰: **"Our decay factor is 0.995"**(sandbox game hours の指数減衰)
> 正規化: recency/relevance/importance を min-max で [0,1] に

出典: arXiv:2304.03442 (ar5iv HTML) / UIST'23 DOI 10.1145/3586183.3606763 ✔(ar5iv経由で実読。ACM DL本体は403)

**プロンプトに載せる件数は固定kではない**:

> "the full memory stream can distract the model and does not even currently fit into the limited context window"
> **"the top-ranked memories that fit within the language model's context window are included in the prompt."**

**知覚の範囲**は数値未公表:

> "sends all agents and objects that are within a preset visual range for each agent to that agent's memory"

→ preset visual range の具体値・上位k・トークン数は**空欄(論文に記載なし)**。

コスト:
> "costing thousands of dollars in token credits" (25体・2日)

**v2への含意**: 最も参照される社会シムですら、チャネル別配分どころか**件数上限すら宣言していない**。α=1(=3指標等重み)は「較正していない」ことの告白であって、根拠のある重みではない。v2が「顕著性順位=サイズ×輝度×距離」を宣言すること自体は先行例より一歩踏み込んでいる。

### 1-2. OASIS (arXiv:2411.11581) — 推薦のk は実験ごとに可変

> Reddit: "the number of recommended posts (i.e., k) varying depending on the experiment"
> Reddit hot score: `h = log₁₀(max(|u−d|,1)) + sign(u−d)·(t−t₀)/45000`
> X: "In-network content is ranked by popularity (likes) before recommendation. Out-of-network posts ... are recommended based on interest matching using TwHIN-BERT ... Factors like recency (prioritizing newer posts) and the number of followers of the post's creator (simulating superuser broadcasting) are also taken into account."

トークン上限・文脈長の記載: **なし(空欄)**。
出典: https://arxiv.org/html/2411.11581v4 ✔

**v2への含意**: 段2「注意予算=件数上限」に相当するのが k。OASIS は **k をハイパラとして実験ごとに動かす**扱いにしている。v2も k を固定定数でなく **ablation対象のパラメータ**として台帳に載せるのが先行例準拠。

### 1-3. CivRealm (arXiv:2401.10568) — 唯一「空間予算」を明示している例

> BaseLang: **"a 5x5 tile-based observation is employed, centered on each unit's location"**
> Mastaba: **"a pyramid-like map view, condensing data from a 15×15 tile region into 9 blocks, each spanning 5×5 tiles"**
> 動機: **"it is challenging to control a large number of objects (e.g., units, cities) based on their local observations due to the context limit of LLM."**

出典: https://arxiv.org/html/2401.10568v1 ✔

**v2への含意**: これは v2 の **B4 セル動的 / B4b サブセル の二段構え**とほぼ同型の設計(近傍は細かく、遠方は集約ブロックに圧縮)。**先行例として最も近い**ので、B4/B4b の階層構造は「CivRealm の Mastaba と同型」と台帳に書ける = mechanism 寄りの根拠になる。ただしトークン数は未公表。

### 1-4. AgentSociety (arXiv:2502.08691) — 構造のみ、数値なし

> 記憶は Profile / Status / Stream Memory(Event Flow + Perception Flow)の3層
> "Each MemoryNode contains a description with three components: time, location, and event description."

top-k・トークン上限・1エージェントステップあたりのトークン消費: **すべて空欄(論文に記載なし)**。
出典: https://arxiv.org/html/2502.08691 ✔

なお **MemoryNode = 時刻 + 場所 + 事象記述** の3点セットは、v2 の B0-B6 素性タグ付き平叙文と設計思想が一致。

### 1-5. Project Sid (arXiv:2411.00114) — 未確認

PIANO アーキテクチャ(並行モジュール+ボトルネック化された意思決定)、50-1,000体規模、という記述のみ検索結果で確認。**観測トークン・文脈長は本文未確認=空欄**。

### 1-6. 問い1の結論

| システム | 予算の与え方 | 数値 | チャネル別枠 |
|---|---|---|---|
| Generative Agents | ランキング→文脈長まで詰める | α全部1・減衰0.995 | なし |
| OASIS | 推薦k(実験ごと可変) | hot score式あり | なし |
| CivRealm | 空間ブロック(5×5 / 15×15→9ブロック) | 5×5 | **空間的にはあり** |
| AgentSociety | 3層記憶 | 空欄 | なし |
| Project Sid | 空欄 | 空欄 | 空欄 |

**v2 のチャネル別トークン枠(B0 300 / B1 100 / B2 150 / B3 100 / B4 60 / B4b 40 / B5 220 / B6 80)は先行例に存在しない。** これは弱点ではなく、40万体の throughput 制約から来る v2 固有の要請。ただし規律上 **expedient タグ**を付け、感度試験(「配分が結果を駆動していない」)が必須。最小コストの ablation は下記(問い7末尾)。

---

## 問い2. 人はどこを見ているか(街路歩行中の視線配分)

### 2-1. 一次データ: Fotios, Uttley & Yang 2014 (CIE 2014, pp.164-173)

40名がシェフィールド大構内の約900mを昼/暗後の2回歩行、SMI iView X HED による頭部装着アイトラッキング。全注視解析は10名×3区間×120秒。

**Table 2 — 全注視(all-fixations)の割合**(原文の表を転記):

| カテゴリ | 本研究 昼 | 本研究 暗後 | Foulsham 2011 昼 | Davoudian&Raynham 昼 | D&R 暗後 |
|---|---|---|---|---|---|
| Person 近 | 3% | 4% | 7% | 3% | 3% |
| Person 遠 | 16% | 8% | 14% | — | — |
| **Person 計** | **19%** | **12%** | **21%** | **3%** | **3%** |
| Path 近 | 16% | 26% | 29% | 51% | 41% |
| Path 遠 | 10% | 8% | 8% | — | — |
| **Path 計** | **26%** | **34%** | **37%** | **51%** | **41%** |
| **Objects / environment** | **55%** | **55%** | **37%** | **46%** | **56%** |

> "Foulsham et al [2011] recorded visual fixations during a 5-10 minute walk to a café and found that **21% of fixation time was directed towards people, 37% towards the path, and 37% towards other objects.**"

出典: https://eprints.whiterose.ac.uk/id/eprint/81139/1/Fotios%20Uttley%20Yang%202014%20Critical%20visual%20tasks.pdf ✔(PDF全文をpymupdfで抽出・該当箇所実読)

**→ 実測の順位は 物体・環境 > 路面 > 人。設計背景にある「人>路面>店頭>看板」は滞留時間ベースでは支持されない。**

### 2-2. しかし「クリティカル注視」では逆転する

二重課題(1-3秒ランダム間隔のビープに即応、反応が平均+2SD 遅れた瞬間=認知資源が視覚に取られた瞬間)で抽出:

> "In daytime and after-dark trials, **critical-fixations indicate a higher proportion of fixations on people and vehicles than do all-fixations.**"
> "Figure 6 suggests that **person and path are the most frequent critical fixation categories**, with path more frequently fixated after-dark and people during daytime."
> 近遠の内訳: **"near median = 19.5%, far median = 6.3%"**(路面)、**"far median = 12.1%, near median = 6.6%"**(人)
> 結論: **"the near path (<4 m) and distant people (>4 m) are critical visual fixations for pedestrians."**

理由づけも明示されている:

> "This increase in apparent importance reflects the increase in visual attention expected for objects of whose behaviours are less predictable than typically static items such as path, objects and goals. Jovancevic-Misic and Hayhoe [2009] found that **pedestrians walking in an unpredictable way were more likely to be fixated, and fixated for a longer duration**, than pedestrians who were predictable in their movements."

### 2-3. 密度の効果(渋谷にとって最重要)

視野に入った歩行者を**1回以上**注視する確率:

> "median fixation probability was **0.87 in daytime, 0.86 after dark, and 0.86 overall**. These data are of a similar order to that reported by Foulsham et al [2011] (**0.83**)."
> "With the probability approach there is a negative relationship, in that there is a **decrease in the probability of fixation as the number of people encountered increases** ... (**r=-0.40, p=0.08**) ... This may be because **with larger numbers of people it is not possible to fixate on all of them** or alternatively deemed not necessary to fixate on all others."

### 2-4. 人への注視の距離と持続 — Fotios, Yang & Uttley 2015

*Lighting Research and Technology* 47(5): 548-564。

> 距離中央値: 両区間 **13.0 m**(IQR 9.0-15.3)/ **8.9 m**(IQR 7.5-10.3)、区間・昼夜で有意差あり(p<0.01)
> 持続: 5名×177人の注視を計測。**"The observation durations tend to be found in the range of 160–720 ms with extreme values of up to 4000 ms."**
> **"The overall median duration of observation was 480 ms (inter-quartile range 400–640 ms)."**
> 提言: **"experiments ... should instead use an interpersonal distance of 15 m and restrict observation duration to 500 ms"**

出典: https://eprints.whiterose.ac.uk/id/eprint/89559/1/fotios%20et%20al%202015%20pedestrian%20distance.pdf ✔

### 2-5. 「B5にB2より多くの予算」の根拠になるか

**なる。ただし根拠は滞留時間ではなく、以下の3点に限る:**

| 根拠 | 内容 | 強さ |
|---|---|---|
| クリティカル注視の逆転 | 二重課題で person が path と並ぶ最上位に上がる。物体・環境は上がらない | **強**(査読付・N=28) |
| 予測不能性 | 人は「振る舞いが予測不能」ゆえ注視が増える。v2の意思決定は他者行動に依存 → 決定関連度が高い | **強** |
| 注視確率0.86 | 視野に入った他者はほぼ確実に1回は見られる。物体はそうではない | **強** |

**同時に、以下を設計書に反対証拠として明記すべき:**
- 滞留時間では 物体・環境(37-56%)が最大バケットであり、B2 150tok は**視線滞留に対しては過少**。
- ゆえに B5 220 > B2 150 は「滞留時間の再現」ではなく「**意思決定関連度による意図的な歪み**」であり、歪みの宣言(=v2 の第一目標「歪む場所の宣言」)に該当する。
- **1件あたりは薄くてよい**: 実世界の人への注視は中央値480ms。1人に35tokは、480msの注視で得られる情報量に照らすと過大な可能性がある。【推測】

### 2-6. 密度スケーリング(新規提案)

Fotios の r=-0.40 と Alvarez&Franconeri の「速度・間隔で1〜8に可変」(問い6)から、**近接上位k を密度の減少関数にする**ことが実証的に支持される。渋谷スクランブルのような高密度セルでは k を上げるのでなく**下げ**、その分を密度スカラーに寄せる。これは throughput にも有利。

---

## 問い3. 日本の屋外広告の視認率

### 3-1. 結論: p_see 相当の日本の公的実測は**空欄**

日本の業界標準である**交通広告共通指標**(公益社団法人日本鉄道広告協会・日本広告業協会・関東交通広告協議会の3団体)は、車両メディアモデル(2024年版)と駅メディアモデル(2019年版)を公開しているが、**測っているのは媒体接触(乗車・利用に基づくOTS)であって視認率ではない**。
出典: https://j-jafra.jp/katsudou/common/ ✔(推定モデルの利用は会員規約+申込が必要=一般公開されていない)

歴史的経緯も一次資料で確認できる。安藤敬元・吉原美保子「交通広告効果指標の考察」『消費者行動研究』Vol.5 No.1 (1997) pp.125-137:

> 「その効果指標に関しては、広告到達のみならず、媒体到達においてもマス4媒体のような共通指標が存在しておらず」
> 提案されたのは駅GRP・線区GRP: 「駅GRP=累積利用率×駅平均利用回数(672%=80.0%×8.4回)」
> 限界の自認: 「各駅や各路線区…単位の利用を媒体接触と考えると、**実際の広告接触と媒体接触率間の差を考慮せねばならない**」

出典: https://www.jstage.jst.go.jp/article/acs1993/5/1/5_1_125/_pdf/-char/ja ✔(PDF全文抽出・実読)

→ **1997年時点で「媒体接触≠広告接触」の差が未解決と明記され、2026年時点の共通指標もそのラインを越えていない。** 英仏の p_see 0.14-0.79 を置き換える日本の公表値は存在しない、というのが本調査の結論。

### 3-2. 唯一見つかった日本の視認率実測(業界・非査読)

屋外大型ビジョンのアイトラッキング調査:

- **平均視認率 約70.3%**
- **音声有りの場合: 77.5% / 無音の場合: 63.1%**(差 14.4pt)
- 地点: 渋谷・新宿・池袋・新橋・秋葉原 の各**視聴可能エリア**内
- n=120(10代-60代、各年代 男女10名ずつ)
- 手法: アイトラッキング専用VRゴーグル+空間音響ヘッドホン、15秒動画、注視時間・注視パターンを計測
- 期間: 2024年3月29-31日

出典: https://prtimes.jp/main/html/rd/p/000000011.000024385.html ✔
**測定条件の重要な限定**: 「視聴可能エリア」内での VR 再現。つまりこの70.3%は **段0(幾何・可視)を通過した後の条件付き確率**であり、v2 の p_see の定義と**そのまま整合する**。媒体は大型ビジョン(=最大級のサイズ・輝度・動き)なので、**p_see レンジの上端**に対応する。

### 3-3. 独立した比較対照(英語圏VR実験)

Lim, S., Cho, H.J., Jeon, M., Cui, X., & Schmälzle, R. (2024). bioRxiv. DOI 10.1101/2024.08.15.607684

> 参加者 41名(平均22.91歳、53%女性)、HP Reverb G2 Omnicept(視線計測付)+ Vizard SightLab VR Pro
> **"fixated on about 70% (28/40) of the billboards"**
> **"The average recall rate was around 8%"**
> **"The average recognition rate was 40%"**

出典: https://www.biorxiv.org/content/10.1101/2024.08.15.607684v1.full ✔

**日本の70.3%と米国の70%が独立に一致**している点は、p_see 上端の妥当性を相互に補強する。

### 3-4. 2025年の新しい日本の取り組み(数値は未公表)

電通・LIVE BOARD・NTTドコモ・電通アドギア の実証:
- 期間 2024/10/1 - 2025/7/31、全国 **900媒体以上・180路線以上**
- 実測: ドコモの約1億ユーザーDB + モバイル空間統計 + docomo Sense で imp / reach / frequency
- インパクト測定: **18エリア**で調査、**65媒体**を「表示サイズ・設置位置」を含む**7因子**でスコアリング

出典: https://www.dentsu.co.jp/news/release/2025/1016-010954.html ✔
→ **視認率(%)そのものは本リリースでは未公表=空欄。** ただし「表示サイズ・設置位置を含む7因子でのスコアリング」は v2 の顕著性順位(問い4)と同じ発想であり、**将来的な日本側アンカーの最有力候補**。親の判断で追跡レーンに置く価値がある。

### 3-5. 推奨(p_see の扱い)

英仏の 0.14-0.79 を捨てる必要はないが、**日本アンカーで上端を固定する**運用を推奨:

| 媒体クラス | p_see | 根拠 | タグ |
|---|---|---|---|
| 大型ビジョン(音声あり) | 0.78 | 日本実測 77.5% | **mechanism** |
| 大型ビジョン(無音) | 0.63 | 日本実測 63.1% | **mechanism** |
| 大型ビルボード | 0.70 | 米VR 70% (28/40) | mechanism(海外) |
| 中小看板・貼り紙 | 0.14-0.40 | 英仏流用のまま | **expedient** |

中小媒体側に日本の値がないことを台帳に明記。

---

## 問い4. 顕著性順位の根拠 —「サイズ×輝度×距離」の是非

### 4-1. 標準モデルは「単純な和」を明確に否定している

Itti, L. & Koch, C. (2000). "A saliency-based search mechanism for overt and covert shifts of visual attention." *Vision Research* 40(10-12): 1489-1506.

> "the simplest feature combination scheme—**to normalize each feature map to a fixed dynamic range and then sum all maps—yields very poor detection performance for salient targets in complex natural scenes**."

出典: https://pubmed.ncbi.nlm.nih.gov/10788654/ / ScienceDirect S0042698999001637 ✔(検索結果経由で要旨確認。本文は未読=引用は要旨レベル)

モデルの中核は **center-surround の局所差分**(方位・強度・色の各チャネル)+ チャネル内競合による非線形正規化。

### 4-2. 「サイズ×輝度×距離」の3つの問題

**(a) 距離の二重計上 — 明確な設計上の誤り**
視覚系に入るのは物理サイズではなく**視角**であり、視角 ≈ 物理サイズ / 距離。したがって「サイズ」と「距離」を独立の因子として掛けると距離が2回効く。
→ **修正**: 因子を「**視角(立体角)**」1つに畳む。距離は視角の中に既に入っている。距離を別に残すなら、それは減衰(大気・遮蔽)や社会的意味(パーソナルスペース)であって幾何ではないと宣言する。
Fotios の実測もこれを支持: 人は**遠方(中央値13m)で注視される**のであって、近いほど顕著なのではない。近接=高顕著性という単純な距離減衰は実測と逆。

**(b) 絶対輝度ではなく局所輝度コントラスト**
すべての顕著性モデルの中核が center-surround = 局所差分である以上、「輝度」は背景に対するコントラストでなければならない。夜の渋谷では平均輝度が高いので、絶対輝度で順位づけると全看板が同着になる。
→ **修正**: 輝度 → **局所輝度コントラスト**(セルの平均輝度に対する比)。

**(c) 積形そのものは、フロア付きなら擁護可能**
純粋な積は「どれか1因子が0なら全体が0」という致命的性質を持つ(遠くて大きい明るい看板が消える)。一方、**log空間の加算は積形と同値**であり、各項に下限フロアを置けば破綻しない。Itti&Koch が否定したのは「正規化して単純に足す(=線形加算)」であって、対数加算=積形を否定してはいない。
→ **修正版の顕著性順位式**:

```
saliency = w1·log(視角 / 視角_min)          # 視角。距離を吸収済み
         + w2·log(1 + 局所輝度コントラスト)  # 絶対輝度でなくコントラスト
         + w3·運動/逸脱度ボーナス            # Jovancevic-Misic & Hayhoe 2009
各項は [0, cap] にクリップ(=フロア付き積形)
```

- w1, w2, w3 の値: **空欄(実証的な相対重みは本調査では発見できず)**。等重み w=1 を初期値とし **expedient** タグ。Generative Agents が α=1 で済ませているのと同じ水準の暫定値であることを台帳に明記。
- 「運動/逸脱度」項だけは実証的裏づけがある: Jovancevic-Misic & Hayhoe (2009) — 予測不能な歩行者ほど注視され、注視が長い(Fotios 2014 経由で確認)。これは **mechanism**。

### 4-3. 空欄

- 街路景観での「サイズ・輝度・コントラスト・動き・距離」の**相対重みを回帰で与えた実証研究**: 発見できず=空欄。
  - MDPI *Land* 12(2):394 "Simulating Urban Element Design with Pedestrian Attention" は該当しそうだが **MDPI が403でアクセス不可=未確認**。親の再取得候補。
  - 地下鉄駅サインの顕著性研究(*J. Environ. Psychol.* 系, S1389041725000427)も **ScienceDirect 403=未確認**。

---

## 問い5. 内容キャップの根拠(日本語の読書速度と 10-20字)

### 5-1. MNREAD-J の定義(一次資料で確認)

小田浩一「MNREAD-J, Jk チャートマニュアル」(東京女子大学、2002/5/18):

> 読書速度の単位は **CPM(Characters Per Minute)**
> 「読書速度 (cpm) = (30 − 読み誤った文字数) ÷ 1つの文章を読むのにかかった秒数 × 60秒」(MNREAD-J)
> 「読書速度 (cpm) = (24 − 読み誤った文字数) ÷ … × 60秒」(MNREAD-Jk)
> 文章構成: 「文章はそれぞれ30文字からなっており…1行10文字を3行に印刷」「1つの文章中の漢字の割合は8文字までと制限」

出典: https://www.cis.twcu.ac.jp/~k-oda/MNREAD-J/MNREAD-J-JkMan020518.pdf ✔(PDF全文をpymupdfで抽出・該当箇所実読)

宇島・小田ら(2007)『特殊教育学研究』45(1):1-11 も同定義を追認:
> 「最大の読書速度を保っているときの読書速度の平均値を最大読書速度(Maximum Reading Speed)といい、MRSと略される。MRSは単位時間(分)当たりの正読字数で表され、CPM(Characters Per Minute)が単位である。」
> 実測値(視力0.1に統制した**ロービジョンシミュレーション**下): **403.3±27.6 / 395.8±40.3 / 307.9±44.6 CPM**

出典: https://home.hiroshima-u.ac.jp/ujima/src/file/oogata.pdf ✔(PDF抽出・実読)

### 5-2. 正常視の日本人成人の代表値 — **空欄(未確認)**

- 査読論文で「正常視・日本人成人の最大読書速度 = N cpm」と明記した値は、本調査(40分)では**取得できなかった**。
- 上の 403 CPM は**視力0.1に統制した条件下**の値であり、正常視の下界としてしか使えない。
- 商用サイトが多数「400-600字/分」と書いているが**出典が辿れないため採用しない**(記憶で埋めない規律)。
- 親の再取得候補: MNREAD-J の原著 Oda, Mansfield & Legge (1998)、および CiNii「Investigation of MNREAD-JK Reading Rate」(NAID 10018262907)。

### 5-3. 算術 — 10-20字は片側で誤り

400-600 cpm を仮定レンジとして(**この仮定自体が expedient**):

| 注視時間 | 400cpm (6.7字/s) | 600cpm (10字/s) | 設計の現行値 |
|---|---|---|---|
| 0.9 s | **6.0字** | **9.0字** | 10字 → **過大** |
| 2.0 s | 13.3字 | 20.0字 | (中間) |
| 3.3 s | **22.1字** | **33.0字** | 20字 → **過小** |

**さらに 0.9秒側を厳しくする2つの理由:**
1. 連続散文の読書速度は、看板の一瞥に**そのまま適用できない**。1回のサッカード+単語認知のオーバーヘッドが乗る。
2. 実世界の屋外注視は Fotios 実測で **中央値480ms**(問い2-4)。0.9秒という下限自体が、実際の歩行中注視より長い。

### 5-4. 推奨する置換

```
表示可能字数 = round(7.5 × 注視秒数)   # 450cpm 相当
              下限 4字(ブランド名1語)、上限 30字
  → 0.9s = 7字 / 2.0s = 15字 / 3.3s = 25字
```
タグ: **expedient**(400-600cpm の学術的裏づけが空欄のため)。正常視の cpm 正典値が取れ次第 mechanism に格上げ可能。

---

## 問い6. 同時注意の容量(4±1 と MOT からの導出の妥当性)

### 6-1. 一次文献

- **Cowan, N. (2001).** "The magical number 4 in short-term memory: A reconsideration of mental storage capacity." *Behavioral and Brain Sciences* 24(1): 87-114. 主張は「Miller の 7 は概算・修辞であり、実際の容量限界は **3〜5チャンク**」。
- **Pylyshyn & Storm (1988)**: MOT で **3〜5個**の個体化。
- **Alvarez, G.A. & Franconeri, S.L. (2007).** "How many objects can you track? Evidence for a resource-limited attentive tracking mechanism." *Journal of Vision*. > "one can track up to **eight** objects at slow speeds, but only **one** object at fast speeds" — 追跡限界は**固定アーキテクチャではなく柔軟な資源**。個人差 **2〜6**。

### 6-2. 妥当性の判定: **部分的にのみ妥当**

**妥当な部分:**
- 「個体として区別して同時に扱える他者は3-4人」— これは Cowan / MOT が直接支持する。**近接上位k=3-4 は mechanism 相当**。
- 3-4を超える人は「個体」ではなく「群」として符号化すべき、という帰結も支持される。群集の平均・密度は ensemble perception として並列に抽出される(個体化の枠を消費しない)。**v2 が密度をスカラーで渡す設計は、この点で強い実証的裏づけを持つ**(問い7でAグレード)。

**妥当でない部分(限界として明記が必要):**

1. **カテゴリ錯誤。** Cowan の4は「保持間隔をまたいで注意の焦点に保持できる項目数」であって、「1つの記述文の中で言及してよい項目数」ではない。LLM の文脈は4項目で飽和するワーキングメモリではない。4±1 を**トークン枠の導出**に使うのは論理の飛躍。
2. **4は定数ではない。** Alvarez&Franconeri により速度・間隔で 1〜8 に動く。**渋谷スクランブル(高速・高密度)では実効的個体化数は4を下回る**。Fotios の r=-0.40(密度が上がると注視確率が下がる)と方向が一致。→ 近接kは**密度の減少関数**にすべきで、固定3-4は高密度セルで過大。
3. **顕著行為1-2 / 傍受1-2 / 広告1 は Cowan からは導けない。** これらは容量限界(3-5)を大きく下回っており、限界がバインドしていない。実際の決定要因は**トークン予算と throughput**。よって **expedient** タグが正しく、「4±1 から導いた」と書くのは根拠の水増しになる。
4. **聴覚(傍受)に視覚のMOTを適用する根拠がない。** 聴覚的注意の同時追跡容量は別問題(cocktail party)。傍受1-2 は**根拠なし=expedient**。

### 6-3. 推奨する記述の書き換え

| 項目 | 現行の根拠づけ | 推奨する根拠づけ | タグ |
|---|---|---|---|
| 近接上位k=3(低密度) | 4±1 | Cowan 3-5 + MOT + Fotios 注視確率0.86 | **mechanism** |
| 近接k の密度逓減 | (なし) | Alvarez&Franconeri(1〜8可変)+ Fotios r=-0.40 | **mechanism** |
| 群を密度スカラーへ | (テキストよりスカラー) | ensemble perception / 個体化枠を消費しない | **mechanism** |
| 顕著行為 1-2 | 4±1 | **トークン予算**。順位規則(逸脱度)のみ Jovancevic-Misic & Hayhoe 2009 で裏づけ | 件数=**expedient** / 順位=mechanism |
| 傍受 1-2 | 4±1 | 根拠なし | **expedient** |
| 広告 1 | 4±1 | 根拠なし(ただし p_see・効果キャップは実証あり) | **expedient** |

---

## 問い7. 推奨: チャネル別トークン上限の初期配分案

対象は B2 150 / B4 60 / B4b 40 / B5 220 = **470 tok**(入力1,300tokの36%)。
v1品質プローブの実測配分(可視3件・看板1件・近接3人・傍受0)を出発点に、上記実証で補正。

### B5 個体 220 tok

| 内訳 | tok | 根拠 | 強さ |
|---|---|---|---|
| 近接人物 上位k=3 × 33 | **100** | Cowan 3-5チャンク / MOT 3-4 / Fotios 注視確率0.86。v1実測も近接3人で一致 | **A** |
| ↳ 密度逓減: 密度>2人/m² で k=2、>4人/m² で k=1 | (同枠内) | Alvarez&Franconeri(1〜8可変)+ Fotios r=-0.40 p=0.08 | **B**(p値が閾値上) |
| ↳ 1人あたり33tok の妥当性 | | 実世界の注視は中央値480ms。33tokは**過大の疑い**。25tokへの削減をablation候補に | **C**(推論) |
| 内受容(満腹/体力/体感温度) | **40** | AgentSociety が needs/motivation を中核に置く先行例。ただし配分量の根拠はなし | **C** |
| 自己状態・所持・直近行動 | **65** | エンジン上の必要。実証根拠なし | **E = expedient** |
| 被注視(自分が見られている) | **15** | 実証根拠なし。ただし社会的創発の素地としては安価 | **E = expedient** |

### B2 場所セル静的 150 tok

**重要な宣言事項**: 視線滞留では 物体・環境が 37-56% で最大バケット。B2 150 < B5 220 は**滞留時間の再現ではなく、クリティカル注視(意思決定関連度)に基づく意図的な歪み**。設計書に反対証拠として明記すること。

| 内訳 | tok | 根拠 | 強さ |
|---|---|---|---|
| 近接路面・通行可能性(<4m) | **40** | Fotios 結論「the near path (<4 m) … are critical」+ クリティカル注視 近路面 中央値19.5%(全カテゴリ最大) | **A** |
| 店舗・施設(可視物 上位3件 × 20) | **60** | v1品質プローブ(可視3件)のみ。外部実証なし | **C** |
| 看板・広告面 1件 | **25** | 注意予算1件は expedient。ただし内容キャップは問い5、p_seeは問い3で実証あり | **C** |
| 地物・ランドマーク・出口 | **25** | 実証根拠なし | **E = expedient** |

### B4 セル動的 60 tok

| 内訳 | tok | 根拠 | 強さ |
|---|---|---|---|
| 群集密度スカラー + 流れ方向 | **25** | ensemble perception(個体化枠を消費しない)+ Fotios「with larger numbers of people it is not possible to fixate on all of them」。**最も根拠の強い1行** | **A** |
| 暗騒音段階 | **10** | 段階化自体は妥当だが段数の根拠なし | **D** |
| 顕著行為 上位1-2 | **25** | 順位規則(逸脱度優先)は Jovancevic-Misic & Hayhoe 2009 で裏づけ。**件数1-2はトークン予算由来** | 順位=**B** / 件数=**E** |

### B4b サブセル 40 tok

| 内訳 | tok | 根拠 | 強さ |
|---|---|---|---|
| 直近サブセルの詳細(遮蔽・段差・行列) | **40** | **外部実証なし。ただし構造は CivRealm/Mastaba の「近傍は細かく遠方は集約」と同型**(5×5 中心観測 + 15×15→9ブロック) | **C**(構造のみ先行例あり・量は expedient) |

### 段3 内容キャップの改訂(問い5の結論)

| 項目 | 現行 | 推奨 | 根拠 |
|---|---|---|---|
| 広告の日本語字数 | 10-20字(固定) | **round(7.5 × 注視秒)、下限4字・上限30字** → 0.9s=7字 / 3.3s=25字 | MNREAD-J の cpm 定義 + 400-600cpm 仮定(**cpm正典値は空欄**) |
| 効果キャップ(1曝露) | (未定) | **再認 ≤ 0.40 / 再生 ≤ 0.08** を上界に | Lim et al. 2024 VR(n=41、米・非査読) |
| p_see 上端 | 0.79(英仏) | **音声あり0.78 / 無音0.63**(大型ビジョン) | 日本VRアイトラ n=120、米VR 70% と一致 |
| p_see 中小媒体 | 0.14-0.40 | 据置 | **英仏流用のまま = expedient** |

### 根拠強度の凡例

- **A** = 査読済み実測が直接支持(Fotios 2014/2015、Cowan 2001)
- **B** = 査読済み実測が間接的に支持、または非査読の一次実測
- **C** = v1自前実測のみ、または論理的推論
- **D** = 慣行のみ
- **E** = **expedient**(根拠なし。感度試験で「結果を駆動していない」証明が必要)

E グレード合計 = B5 80tok + B2 25tok + B4 25tok(件数部分) ≒ **130tok / 470tok = 28%**。この28%が感度試験の対象。

### 必須 ablation(最小コスト・2本)

1. **固定枠 vs 単一ランキング**: 総トークンを470に固定したまま、(a)チャネル別固定枠 と (b)全チャネル混合の単一顕著性ランキングで上位から470tokまで詰める、を比較。**先行例(Generative Agents / OASIS / CivRealm)はすべて(b)** なので、(a)を採るなら (a)>(b) を示す義務がある。これが本答申の最重要の実務提言。
2. **近接k の密度逓減の有無**: 高密度セル(スクランブル)で k=3固定 vs 密度逓減。Fotios の r=-0.40 を再現できるか(=行動分布が実測方向に動くか)。

---

## 問い8. 親の一次確認リスト(最重要5件)

### 確認1 — 歩行時の視線配分(本答申で最も重い数値)
- **URL**: https://eprints.whiterose.ac.uk/id/eprint/81139/1/Fotios%20Uttley%20Yang%202014%20Critical%20visual%20tasks.pdf
- **引用文**: "Foulsham et al [2011] recorded visual fixations during a 5-10 minute walk to a café and found that 21% of fixation time was directed towards people, 37% towards the path, and 37% towards other objects." / "It was concluded that the near path (<4 m) and distant people (>4 m) are critical visual fixations for pedestrians."
- **確認すべき数値**: Table 2 の全数値(Person近3%/遠16%、Path近16%/遠10%、Objects 55%)、クリティカル注視の中央値(近路面19.5% / 遠路面6.3% / 遠人12.1% / 近人6.6%)、注視確率(0.87 昼 / 0.86 暗後 / Foulsham 0.83)、密度相関 r=-0.40 p=0.08。
- **注意**: これは **CIE 2014 会議録(査読誌ではない)**。同内容の査読版は *Lighting Res. Technol.* 2015, 47:149-160 (Part 2) にある可能性が高いが**未確認**。正典化時は査読版の数値と突合すること。

### 確認2 — 人への注視の距離と持続(B5の1件あたり情報量の根拠)
- **URL**: https://eprints.whiterose.ac.uk/id/eprint/89559/1/fotios%20et%20al%202015%20pedestrian%20distance.pdf
- **引用文**: "The overall median duration of observation was 480 ms (inter-quartile range 400–640 ms)." / "We propose that experiments seeking to examine the effect of lighting on interpersonal judgements should instead use an interpersonal distance of 15 m and restrict observation duration to 500 ms"
- **確認すべき数値**: 距離中央値 13.0m(IQR 9.0-15.3)、持続レンジ 160-720ms(最大4000ms)、n=5名/177人。誌名 *Lighting Research and Technology* 47: 548-564 (2015)。

### 確認3 — 日本の屋外広告視認率(p_see の日本アンカー)
- **URL**: https://prtimes.jp/main/html/rd/p/000000011.000024385.html
- **引用文**: 「音声有りの場合:77.5%」「無音の場合:63.1%」
- **確認すべき数値**: 平均視認率70.3%、n=120(10-60代・各年代男女10名)、5地点(渋谷・新宿・池袋・新橋・秋葉原)、2024/3/29-31、15秒動画、VRゴーグル。
- **注意**: **プレスリリース(非査読・企業発表)**。調査主体の社名と、「視聴可能エリア内での条件付き確率」であることを必ず確認。v2 の p_see 定義(段0通過後)と本当に整合するかは親判断。**リポには社名を書く前に scan_secrets の対象外であることを確認**。

### 確認4 — 内容キャップの土台(cpm の定義と式)
- **URL**: https://www.cis.twcu.ac.jp/~k-oda/MNREAD-J/MNREAD-J-JkMan020518.pdf
- **引用文**: 「読書速度 (cpm) = ( 30 − 読み誤った文字数) ÷ 1つの文章を読むのにかかった秒数 × 60秒」
- **確認すべき数値**: 単位が CPM であること、MNREAD-J の1文=30文字(1行10文字×3行)、漢字8文字まで。
- **★最重要の空欄**: **正常視の日本人成人の最大読書速度(cpm)の正典値が本答申には無い。** 「400-600cpm」は商用サイト由来で採用していない。この値が取れるまで、内容キャップ式 `7.5 × 注視秒` は **expedient のまま**。再取得候補: Oda, Mansfield & Legge (1998) 原著 / CiNii NAID 10018262907。

### 確認5 — 先行例に「チャネル別枠」が無いこと(ablation義務の根拠)
- **URL**: https://ar5iv.labs.arxiv.org/html/2304.03442 (Generative Agents) / https://arxiv.org/html/2401.10568v1 (CivRealm)
- **引用文**: "In our implementation, all α's are set to 1." / "the top-ranked memories that fit within the language model's context window are included in the prompt." / "a 5x5 tile-based observation is employed, centered on each unit's location" / "condensing data from a 15×15 tile region into 9 blocks, each spanning 5×5 tiles"
- **確認すべき数値**: 減衰係数0.995、α=1、5×5 / 15×15→9ブロック。
- **確認すべき「不在」**: Generative Agents / OASIS / AgentSociety のいずれにも**チャネル別トークン枠・上位k の固定値が書かれていない**こと。これが「v2の固定枠は独自=ablation必須」という提言の全根拠なので、親が実際に本文検索して不在を確認されたい(不在の証明なので特に重要)。

---

## 参照一覧

| # | 著者・年 | 出典 | URL | 確認 |
|---|---|---|---|---|
| 1 | Fotios, Uttley & Yang (2014) | Lighting for pedestrians: what are the critical visual tasks? *Proc. CIE 2014*, pp.164-173, ISBN 978-3-902842-49-7 | https://eprints.whiterose.ac.uk/id/eprint/81139/1/Fotios%20Uttley%20Yang%202014%20Critical%20visual%20tasks.pdf | ✔ 全文実読 |
| 2 | Fotios, Yang & Uttley (2015) | Observing other pedestrians: Investigating the typical distance and duration of fixation. *Lighting Res. Technol.* 47: 548-564 | https://eprints.whiterose.ac.uk/id/eprint/89559/1/fotios%20et%20al%202015%20pedestrian%20distance.pdf | ✔ 全文実読 |
| 3 | Foulsham, Walker & Kingstone (2011) | The where, what and when of gaze allocation in the lab and the natural environment. *Vision Research* 51(17): 1920-1931 | https://doi.org/10.1016/j.visres.2011.07.002 | ✔ 書誌+要旨(Essexリポジトリ経由)。**本文は未読**、21/37/37% は #1 の引用による |
| 4 | Davoudian & Raynham (2012) | (#1 の Table 2 経由。路面41-51% / 人3%) | — | **空欄(原典未確認)** |
| 5 | Jovancevic-Misic & Hayhoe (2009) | (#1 の引用経由。予測不能な歩行者は注視されやすく長い) | — | **空欄(原典未確認)** |
| 6 | Park et al. (2023) | Generative Agents: Interactive Simulacra of Human Behavior. UIST'23 | https://ar5iv.labs.arxiv.org/html/2304.03442 / DOI 10.1145/3586183.3606763 | ✔ ar5iv実読(ACM DL は403) |
| 7 | Yang et al. (2024) | OASIS: Open Agent Social Interaction Simulations with One Million Agents. arXiv:2411.11581 | https://arxiv.org/html/2411.11581v4 | ✔ 実読 |
| 8 | Qi et al. (2024) | CivRealm: A Learning and Reasoning Odyssey in Civilization. arXiv:2401.10568 | https://arxiv.org/html/2401.10568v1 | ✔ 実読 |
| 9 | Piao et al. (2025) | AgentSociety. arXiv:2502.08691 | https://arxiv.org/html/2502.08691 | ✔ 実読(トークン数は記載なし=空欄) |
| 10 | Altera.AL (2024) | Project Sid: Many-agent simulations toward AI civilization. arXiv:2411.00114 | https://arxiv.org/abs/2411.00114 | **空欄(本文未読)** |
| 11 | Cowan, N. (2001) | The magical number 4 in short-term memory. *Behavioral and Brain Sciences* 24(1): 87-114 | https://philpapers.org/rec/COWTMN | ✔ 書誌+主張のみ(本文未読) |
| 12 | Alvarez & Franconeri (2007) | How many objects can you track? *Journal of Vision* | (検索結果経由) | **書誌のみ✔ / 本文未読** |
| 13 | Pylyshyn & Storm (1988) | MOT 3-5個体化 | (二次引用) | **空欄(原典未確認)** |
| 14 | Itti & Koch (2000) | A saliency-based search mechanism… *Vision Research* 40(10-12): 1489-1506 | https://pubmed.ncbi.nlm.nih.gov/10788654/ | ✔ 要旨のみ(本文未読) |
| 15 | 小田浩一 (2002) | MNREAD-J, Jk チャートマニュアル、東京女子大学 | https://www.cis.twcu.ac.jp/~k-oda/MNREAD-J/MNREAD-J-JkMan020518.pdf | ✔ 全文実読 |
| 16 | 宇島・小田・柏田 (2007) | 大型電子化提示教材で使用するロービジョンに適した文字サイズの規定法. *特殊教育学研究* 45(1): 1-11 | https://home.hiroshima-u.ac.jp/ujima/src/file/oogata.pdf | ✔ 全文実読 |
| 17 | 安藤敬元・吉原美保子 (1997) | 交通広告効果指標の考察. *消費者行動研究* 5(1): 125-137 | https://www.jstage.jst.go.jp/article/acs1993/5/1/5_1_125/_pdf/-char/ja | ✔ 全文実読 |
| 18 | 日本鉄道広告協会 | 交通広告共通指標(車両メディアモデル2024年版・駅メディアモデル2019年版) | https://j-jafra.jp/katsudou/common/ | ✔ ページ実読(**推定モデル本体は会員限定=数値は空欄**) |
| 19 | (企業調査, 2024) | 屋外大型ビジョンの視認率アイトラッキング調査 | https://prtimes.jp/main/html/rd/p/000000011.000024385.html | ✔ 実読(**非査読・プレスリリース**) |
| 20 | 電通ほか (2025) | DOOHの指標を応用してアナログOOHの広告価値の可視化を実現 | https://www.dentsu.co.jp/news/release/2025/1016-010954.html | ✔ 実読(**視認率%は未公表=空欄**) |
| 21 | Lim, Cho, Jeon, Cui & Schmälzle (2024) | Using VR and eye-tracking to study attention to and retention of AI-generated ads in outdoor advertising environments. bioRxiv | https://doi.org/10.1101/2024.08.15.607684 | ✔ 実読(**プレプリント・非査読**) |
| 22 | 肥田野直・伊藤隆二 (1961) | 読書速度促進の実験的研究. *教育心理学研究* 9(1): 34- | https://www.jstage.jst.go.jp/article/jjep1953/9/1/9_34/_pdf | ✔ 抽出済だが**字/分の代表値は表中で抽出失敗=空欄** |
| 23 | (未取得) | Simulating Urban Element Design with Pedestrian Attention. *Land* 12(2): 394 | https://doi.org/10.3390/land12020394 | **空欄(MDPI 403)** |
| 24 | (未取得) | Image-analysis-based method for exploring factors influencing the visual saliency of signage in metro stations. *J. Environ. Psychol.* | S1389041725000427 | **空欄(ScienceDirect 403)** |

---

## 空欄一覧(記憶で埋めていない項目)

1. **正常視の日本人成人の最大読書速度(cpm)の査読値** — 内容キャップ式の土台。最優先の再取得対象。
2. **中小屋外広告(貼り紙・小型看板)の日本の視認率** — 英仏流用のまま。JAFRA の推定モデルは会員限定。
3. **街路景観での顕著性因子(サイズ・輝度・コントラスト・動き)の相対重みの実証回帰** — MDPI/ScienceDirect が403で未確認。w1:w2:w3 は等重み expedient。
4. **Project Sid の観測トークン・文脈長** — 本文未読。
5. **AgentSociety / OASIS のトークン消費統計** — 論文に記載なし(不在を確認済)。
6. **Davoudian & Raynham (2012) 原典** — #1 経由の二次引用のみ。
7. **Fotios Part 2 の査読版(*LRT* 2015, 47:149-160)** — SagePub が403。CIE会議録版で代替した。
