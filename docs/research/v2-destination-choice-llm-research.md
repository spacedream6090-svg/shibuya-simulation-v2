# v2-destination-choice-llm-research — 行き先選択に LLM の思考を入れる(候補提示型・R-37 答申・実装なし)

<!-- hdr:v1 -->
- **分野**: 人間移動科学 #3 / 自然言語処理・機械学習 #27 / 計量経済(離散選択) / 消費者行動 / 計算社会科学 #25 | **重要度**: **P1**(D-88 ④ の材料。ユーザー意向「行き先を考えることも思考の一部」と P3 答申の推奨(選好はエンジンの数値)が正面から食い違う点を埋める)
- **一次確認**: **B** = サブ(Opus 5)が原典の本文・表・付録を実読。**親の一次確認前**。**実読 12 本**(arXiv HTML 6・PDF→pymupdf 4・OUP/arXiv abs 2)・**抄録のみ 3 本**・**取得不能 3 本**(§6)。逐語は「」で括り 125 字以内。 **→ 親確認 3 件+実物確認 1 件(第232)**: When Plausible(arXiv 2606.13835v1 HTML §5.1・Table 1/2)「STVD W1 equals 607.69±5.88 for AgentSociety and 748.71±23.00 for CitySim」「the simpler gravity-based destination selection used in AgentSociety outperforms CitySim's LLM-driven POI-selection strategy」「Δr error decreases from 14.83 km … to 7.53 km」「radius of gyration error decreases from 7.29 km to 3.47 km」✓(付録 B.5 の「3–5 candidate Neighborhoods・γ=2.0」は HTML が途中で切れ**親未確認**)/ LLM-Move(arXiv 2404.01855v2 HTML Table II/IV)「Dist 0.3702」「LLMmove 0.5200」「Dist-asc 0.5200 / Dist-des 0.2000 / Rand 0.3250」✓ / **実物確認**: `world/assets.py hash_free_cat_code` は food/飲食/restaurant/cafe だけ飲食コード 1 → W6 の nightlife 259 件は `eatery_mask` 外 ✓(W6 サブへ追加指示)。Honka 2019・Zheng 2023・Turpin 2023 は親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md) ・ **文献メモ**: [lit/](lit/README.md)
- **兄弟答申**: [v2-preference-vector-research.md](v2-preference-vector-research.md)(P3・EPR/Dubé)・[v2-hobby-preference-research.md](v2-hobby-preference-research.md)(P1・趣味)・[v2-llm-mobility-research.md](v2-llm-mobility-research.md)(**D 等級=§0-2 参照**)

> **問い**: いま「移動」の行き先は `commit.py:_poi_in_cell` の**セル内 id 最小の POI**で決まっており、選好は 1 バイトも無い。P3 答申はここをエンジンの数値(EPR + Dubé 効用)で埋めることを推奨した。ユーザーは「**行き先を考えることも思考の一部**」であり LLM を入れたいと言う。**親案 H(混成)= エンジンが候補 3〜5 を作り、LLM が既存の「対象」欄で 1 つ選ぶ(追加呼 0)**は成立するか。
>
> **答え(5 行)**:
> **(i) 候補提示型は先行の主流であり、しかも「誰が候補を作り、誰が選ぶか」は先行では H と逆向きに落ち着いている。** AgentSociety も CoPB も CitySim も TrajGenAgent も「**LLM が意図・カテゴリ・半径・候補領域を出し、エンジン(重力則/スコア)が POI を決める**」。**H(エンジンが候補、LLM が選ぶ)をやった先行は、予測タスク側(LLM-Move・LLM-ZS)にしか無く、シミュレーション側には見つからなかった。**
> **(ii) その先行が、H の方向を直接不利に評価している。** 同一データ・同一枠で AgentSociety(単純な重力)と CitySim(LLM 主導の POI 選択)を比べた研究は「**単純な重力則のほうが、よく訪れられる市街地の再現では勝つ**」と結論した(STVD W₁ 607.69 vs 748.71)。ただし**個体レベルの距離分布は LLM 主導のほうが良い**(Δr 誤差 14.83→7.53 km)=**集計と個体で符号が逆**。
> **(iii) 候補提示は 8B にとって強い交絡を持ち込む。** 候補の**並べ替えだけ**で Acc@1 が 0.52→0.20(2.6 倍)動いた実測がある(LLM-Move・候補 101 件)。選択肢 ID への偏り(RStd)は **llama-2-7B 23.0 / llama-2-70B 4.1**=**小さいモデルほど大きい**。そして LLM は**その偏りを理由文に一度も書かない**(Turpin 2023・精度が最大 36% 落ちても)。→ **H を入れるなら「候補順の乱択」は対照ではなく必須の機構**。
> **(iv) 候補数 3〜5 には一次の裏づけがある。** 消費者行動の実証は「**通常 2〜5 件**」(Honka ほか 2019 の総説・実読)、Hauser & Wernerfelt 1990 の集計は「**ほとんどが 3〜5 銘柄**」。同じ 3〜5 が、LLM 都市シミュレーション側でも独立に採られている(「**LLM が 3〜5 の候補 Neighborhood を選ぶ**」)。**ただし渋谷の実データでは、候補の母数が足りない**——POI を持つセルの中央値は **4 件**(食事は 2 件)なので、「セル内 k 件」は事実上「セル内全部」。**H を意味あるものにするには、候補は複数セルに跨る必要がある**。
> **(v) 費用は小さいが、予算表の改訂は避けられない。** 候補行 1 本は k=4 で **28 tok**(本 repo の見積規約 = 文字数÷2)。個体部に足すと BN-2C 実測の **−8.1%/100tok** で**スループット −2.3%**。ただし **B5 220 + B6 80 = 300 = 個体部の上限ちょうど**なので、**予算 delta か、等級 E の行(B5 被注視 15 / B5 自己状態 65 / B2 地物 25)との差し替え**が要る。**候補行を B2(セル共有)に置くと、個体ごとの「馴染み」を書けない代わりにバイト共有が保てる**(差分観測の禁止=実測 −38% の理由と同じ)。

---

## §0 重複調査を避けるために先に確認したこと

### 0-1 既存答申でカバー済み(再掲しない)

| 項目 | 既存の場所 | 本書での扱い |
|---|---|---|
| EPR の 2 式(`P_new = ρ S^{-γ}`・`Π_i = f_i`)と ρ=0.6・γ=0.21・α=0.55・δ=1+γ | [v2-preference-vector-research.md](v2-preference-vector-research.md) §1-1・[lit/mobility__song2010_epr.md](lit/mobility__song2010_epr.md)(親確認済) | **再掲しない**。§2-3 で「候補生成規則の材料」としてだけ引く |
| returners/explorers の二等分法・均衡 k=4・d-EPR | 同 §1-2 | 再掲しない |
| 訪問の普遍則 `ρ_i(r,f)=μ_i/(rf)^η`・η≈2 | 同 §1-3 | **§4 の照合先としてだけ引く**(§4-1 で「先行もこれを検証指標に使っている」ことを足す) |
| 選好と習慣の分離(Dubé 2010 の `u=α_j+η·p+γ·I{s=j}+ε`)・二重計上の検査 T-A〜T-E | 同 §3-1・§4 | **再掲しない**。本書は「α_j を LLM に出させる」案の可否だけを扱う |
| 趣味を公的統計から配る案・P1/P3 の衝突と調停 | [v2-hobby-preference-research.md](v2-hobby-preference-research.md) §7-4 | 再掲しない。§5-2 で「趣味は候補**生成**に効かせ、選択確率には掛けない」線だけ再確認 |
| CitySim のブランド POI 偏り | [lit/leisure__bougie2025_citysim-shibuya-poi.md](lit/leisure__bougie2025_citysim-shibuya-poi.md)(サブ実読) | **§5-3「見せる情報」の制約としてだけ引く** |
| LLM 判断層は規則ベースの 2.6〜5.1 倍 | [lit/compute__alves2026_llm-urban-mobility.md](lit/compute__alves2026_llm-urban-mobility.md)(親確認済) | **§4-4 で「H は追加呼 0 なのでこの倍率はかからない」ことの対比にだけ使う** |
| メニュー効果(白リスト vs 自由文) | `docs/bench/c8/ablation/ab7_s1_parent_report.md`・`ab7c_s1_parent_report.md`(本 repo 実測) | **§3-4 で再掲**(本件の主要な内部証拠) |

### 0-2 **循環参照検査の結果(重要・親への申し送り 1 件目)**

任務は「既存答申 `v2-llm-mobility-research.md` がカバー済みの部分は『既存答申 §X』と書いて再調査しない(循環参照検査: **その答申が D 等級でないことを確認**)」だった。

**確認した結果、`v2-llm-mobility-research.md` は D 等級である**(同書ヘッダ逐語: 「**一次確認**: **D** = **出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る — 出典痕跡 3 件・URL 0 件」)。CLAUDE.md §5 の循環参照検査の定義(「X が D 等級なら一次は無いと判定する」)により、**同書を「カバー済み」として引くことはできない**。

→ 本書は **LLMob・CoPB・TrajGenAgent・COMPASS・When Plausible の 5 本を、URL と逐語つきで一次から取り直した**(§1・§4)。その結果、同書の記述に対する**確認 3 件と訂正候補 2 件**が出た:

| 同書の記述 | 本書の一次確認 | 判定 |
|---|---|---|
| 「LLMob: 時空間分布 JSD 0.559=空間が最弱」 | Setting 1・LLMob-E の STVD **0.559**(Step distance 0.053 / Step interval 0.046 / DARD 0.125)。出典 <https://arxiv.org/html/2402.14744v2> | **一致** |
| 「CoPB: 意図誤り 57.8%→19.4%・トークン 97.7% 削減」 | 抄録逐語「reduces the error rate of mobility intention generation from 57.8% to 19.4%」「reduce the token cost by 97.7%」。出典 <https://arxiv.org/abs/2402.09836> | **一致** |
| 「TrajGenAgent: LLM を活動チェーン構造だけに限定し距離 JSD 0.0006」 | Table VI・NumoSim の Distance **0.0006**(MobilitySyn は 0.0028)。ただし**「LLM を活動チェーンだけに限定」は不正確**——Stage 2 の**時刻**も LLM が出す(「LLM augmented kinematics-aware temporal generation」)。**行き先(POI)だけがエンジン**。出典 <https://arxiv.org/pdf/2606.12657> | **数値一致・記述に訂正候補** |
| 「Song+2010 EPR(S(t)~t^μ, μ=0.6±0.02・**Zipf ζ=1.2±0.1**)」+ 第221 の写し訂正「原典の記号は δ」 | **ζ の出所が分かった**: COMPASS(2602.16726)本文が「ζ≈1.2±0.1」と書き Song 2010 を引いている。**サブの写し間違いではなく、後続文献側の記号の揺れ**。第221 の訂正(δ が原典)はそのまま正しい | **訂正の由来が判明** |
| 任務文の前提「**EPR の『探索は距離の逆冪』(既存答申の δ 1.2)**」 | **別の量である**。EPR の距離の逆冪は **α = 0.55 ± 0.05**(`P(Δr) ~ Δr^{-1-α}`)。δ=1.2±0.1 は**訪問頻度の Zipf**(`f_k ~ k^{-δ}`・δ=1+γ)。出典 [lit/mobility__song2010_epr.md](lit/mobility__song2010_epr.md)(親確認済) | **訂正候補**(候補生成で距離冪を使うなら α であって δ ではない) |

---

## §1 候補提示型の LLM 行き先選択の先行

### 1-1 一覧(任務の (a)〜(f) を列に持つ)

**表の読み方**: 「**誰が候補を作り、誰が選ぶか**」の欄が本件の中心。**Sim** = 社会シミュレーション、**Pred** = 次地点予測(履歴があって正解がある問題)。

| # | 研究 | 種 | (a) 候補の作り方 | (b) k | (c) 見せた情報 | (d) 精度・規則ベースとの差 | (e) 規模 | (f) 理由文 | 一次 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **LLM-Move**(Feng ほか 2024・"Where to Move Next") | Pred | **正解 1 + 無作為 100**(推薦評価の慣行)。**距離昇順に並べてから**見せる | **101** | id・カテゴリ・**現在地からの距離(エンジンが事前計算)** | NYC Acc@1 **.5200** / TKY .4200。**最近傍だけの規則(Dist)が .3702 / .2700 で、先行の LLM 系を全部上回る**。距離を消すと .4800 | gpt-3.5-turbo のみ | 段階推論あり・検証なし | **実読**(HTML) |
| 2 | **LLM-ZS**(Beneduce ほか 2024・"Zero-Shot Next Location Predictors") | Pred | **明示の候補集合なし**。履歴 15 + 文脈 6 の訪問列だけ。候補は「履歴に出た id」 | — | 時刻・曜日・venue id **のみ**(カテゴリ・座標・距離は渡さない) | ACC@5 最大 .338〜.341。**小モデルは落ちる**(Llama 2 7B **.077**) | **15 モデル超**・7B〜405B | **出す**。ただし「**定量評価は無し**」(質的観察のみ) | **実読**(HTML) |
| 3 | **AgentMove**(Feng ほか 2024・NAACL 2025) | Pred | 3 経路の合流: ①LLM が生成した「潜在的な場所」(district/block/street/POI 名)②**共起グラフの 1-hop 近傍**(他人の行動)③本人の履歴 | 出力は上位 5 | id→カテゴリ表・時刻別頻度・遷移・住所 | Tokyo Acc@1 .185 / Acc@5 .465。**FPMC(マルコフ)は .060/.165** | GPT-4o-mini 既定・**Llama3-8B も検証**(WKG 有で返答率 94%) | **JSON に `reason` 欄**(検証は無し) | **実読**(HTML) |
| 4 | **LLMob**(Wang ほか 2024・NeurIPS) | Sim | 履歴から「**最頻訪問地点**」を作り `<<INPUT 2>>` に差し込む(+「時々行く場所」) | 明示なし | 「Park#2457」「Soba Restaurant#955」= **種別 + 通し番号** | STVD **0.559**(最弱)・DARD 0.125。マルコフ機構モデル(MM)は DARD 0.644 | GPT-3.5-turbo **のみ** | **`reason` 欄あり**+自己整合性で**候補パターン 10 本**を採点 | **実読**(HTML) |
| 5 | **CoPB**(Shao ほか 2024) | Sim | **候補を出さない**。LLM は意図(TPB の態度/規範/統制)だけ。**行き先は重力則** | — | — | 意図誤り **57.8%→19.4%**・**トークン −97.7%** | GPT-4-turbo で教師、**LLaMA 3-8B へ蒸留** | 推論鎖あり | 抄録のみ |
| 6 | **AgentSociety**(Piao ほか 2025) | Sim | **4 段**: 意図→**POI 種別**→**許容半径**→**重力則が POI を選ぶ**。`P_ij = (S_j/D_ij^β) / Σ_k(S_k/D_ik^β)` | — | — | (本書では未取得) | >10k 体・500 交流/体/日 | — | **実読**(HTML) |
| 7 | **CitySim**(Bougie & Watanabe 2025) | Sim | **LLM が 3〜5 の候補 Neighborhood を選ぶ**(ペルソナ・7 日の訪問履歴・該当 POI 密度から)。**その中でエンジンが信念重みつき重力則**で POI を決める | **3〜5**(領域) | ペルソナ・7 日履歴・POI 密度 | 渋谷 POI 人気の Spearman は Figure のみ。**ブランド POI への正の偏り**を自己申告 | GPT-4o-mini・1,000 体 | — | 実読([lit メモ](lit/leisure__bougie2025_citysim-shibuya-poi.md)) |
| 8 | **TrajGenAgent**(Li ほか 2026) | Sim | **本人の履歴の実行可能集合 `P_u(a)` ∪ 類似個体 top-K の集合 `P_sim(a)`**。全 POI 空間からは引かない | 明示なし(α で混合) | — | **Distance JSD 0.0006**(NumoSim)。**POI 選択は LLM ではなくスコア `S(p)=λ_f·s_freq+λ_d·s_dist` の確率抽出** | Qwen2.5-32B-Instruct | — | **実読**(PDF) |
| 9 | **COMPASS**(Yan ほか 2026) | Sim | 候補提示なし。プロンプトを **MCTS で書き換える**(統計則を報酬に) | — | — | Beijing JSD: **探索 0.3895(LLMob)→0.0756・回帰 0.2531→0.0614** | Qwen2.5-72B ほか | — | **実読**(HTML) |
| 10 | **When Plausible Is Not Realistic**(Santos ほか 2026・SIGSPATIAL) | 評価 | 上記 6・7 を同一データで比較 | — | — | **§5-1**: 単純な重力の AgentSociety が STVD で勝つ(607.69 vs 748.71) | — | — | **実読**(PDF) |
| 11 | **Distilling Aggregate Mobility Statistics**(Amano & Yamaguchi 2026・SIGSPATIAL) | Sim | LLM 方策 5 種 vs **CMA-ES で較正した規則**・LLMob・**古典重力則**の総当り | — | — | **格子相関は較正後どれも ≈0.75 で区別がつかない**。行き先構成比の誤差だけが分ける | — | — | **実読**(HTML) |

**UrbanLLM(2406.12360)・GeoLLM(2310.06213)は該当なし**: 前者は都市クエリを時空間 AI モデルへ振り分けるオーケストレータ、後者は OSM から地理知識を抽出する表現学習であり、**「候補を見せて行き先を選ばせる」設計を持たない**(検索要約で確認・本文未読=§6 ②)。

### 1-2 いちばん効く 1 本: **LLM-Move**(候補提示の設計が全部書いてある)

出典: Shanshan Feng, Haoming Lyu, Caishun Chen, Yew-Soon Ong, "Where to Move Next: Zero-shot Generalization of LLMs for Next POI Recommendation", arXiv:2404.01855(v1 2024-04-02 / v2 2024-04-22)。<https://arxiv.org/abs/2404.01855> / 本文 <https://arxiv.org/html/2404.01855v2>。**[実読]**

- **候補集合**(逐語): 「the candidate set comprises the ground truth POI and **100 randomly sampled POIs**」。POI は `⟨Id, Cat, Lat, Lon⟩`。
- **距離はエンジンが計算して渡す**(逐語): 「Hence, we **calculate the distances and utilize them as input**.」——座標から LLM に距離を出させる試みは「cannot obtain accurate results」で失敗した。抄録(逐語): 「LLMs **cannot accurately comprehend geographical context information**」。
- **結果(Table II・NYC / TKY の Acc@1)**: Popu(人気順).0500/.2300・**Dist(最近傍).3702/.2700**・LLMRank .0400/.0100・LLMMob .3600/.3350・**LLMmove .5200/.4200**。
  → **(1) 最近傍という 1 行の規則が、先行の LLM 零ショット推薦を全部上回る。(2) しかし候補+距離+選好を全部見せた LLM はその規則をさらに上回る。** ← **H を支持する唯一の定量証拠**。ただし**予測タスクであり、正解が候補集合に必ず入っている**(§4-5 の注意)。
- **並び順の実測(Table IV・NYC)**: Dist昇順 **.5200** / Dist降順 **.2000** / 無作為 **.3250** / 頻度昇順 .3600 / 頻度降順 .4400。著者(逐語): 「the **order of the candidate set significantly affects** the recommendation performance」。→ **§3 へ**。

### 1-3 いちばん効く 2 本目: **When Plausible Is Not Realistic**(H と逆向きの設計が、H の方向に不利な結果を出した)

出典: Gustavo H. Santos, Aline Carneiro Viana, Thiago H. Silva, "When Plausible Is Not Realistic: Evaluating Human Mobility in LLM-Based Urban Simulation", arXiv:2606.13835v1(SIGSPATIAL'26)。<https://arxiv.org/abs/2606.13835> / PDF <https://arxiv.org/pdf/2606.13835>(pymupdf で全 14 頁抽出)。**[実読]**

- **§3-1「Unconstrained POI selection」(本件の一次の根拠・逐語)**: 「needs-driven mobility actions could **select destinations from the full set of POIs available in the simulated map**, rather than from POIs **semantically consistent** with the active need and **spatially plausible**」。結果は「agents with low hunger satisfaction could be routed to semantically unrelated or distant POIs」。
  → **「候補集合を作る」こと自体は、先行が名指しした欠陥の是正であり、需要モデルの注入ではない**(`v2-llm-mobility-research.md` §4 の「到達可能性による候補集合の制約」= 許容、と同じ線)。
- **付録 B.5(CitySim 再実装・逐語)**: 「the LLM selects **3–5 candidate Neighborhoods** using the persona, **7-day visit history**, and matching-POI density. If this fails, the block **falls back to AOI-level selection ranked by distance and popularity**.」微視側は「belief-weighted gravity model」で `distance^{1+γ(b_j−0.5)}`・**γ=2.0**。
  → **順序が H と逆**(LLM が候補を作り、エンジンが選ぶ)。**同じ 3〜5 が出ている**のは §2 と独立に一致する。
- **§5-1(H の方向への否定的証拠・逐語)**: 「the **simpler gravity-based destination selection** used in AgentSociety **outperforms CitySim's LLM-driven POI-selection strategy** in reproducing the most frequently visited urban areas.」「**Increasing POI-selection complexity does not necessarily improve** the reproduction of highly visited urban areas.」数値: GreaterParis・H3 解像度 8 の STVD W₁ = **AgentSociety 607.69 ± 5.88 / CitySim 748.71 ± 23.00**。
- **同 §5-1(逆向きの証拠)**: 個体レベルでは CitySim が良い。GreaterParis の Δr 誤差 **14.83 km → 7.53 km**、回転半径誤差 **7.29 km → 3.47 km**。Shanghai は Δr 3.97・r_g 4.86。
  → **本書の最重要の含意**: **「LLM に行き先を考えさせる」と、個体の距離分布は良くなり、集計の訪問分布は悪くなる可能性がある。片方だけ測ると誤った合格が出る。**
- OD 一致は改善後も弱い(逐語): 「OD-matrix agreement remains weak, particularly in the GreaterParis dataset (**CPC H8 = 0.138 ± 0.018**)」。**フロア併記**(第210 の規律): 同論文 §5-1 Table 2 の実データ同士の参照標本は **H7 0.297 / H8 0.092 / H9 0.045** なので、**0.138 は H8 のフロア 0.092 を上回っている**(親が既に確認済=`v2-r23-primary-check-batch2.md` §16)。

### 1-4 **LLMob の「候補」は行き先の候補ではない**(任務の想定への訂正)

LLMob(Wang ほか 2024・NeurIPS 2024・<https://arxiv.org/html/2402.14744v2>)**[実読]**の「候補」は **10 本の候補**活動**パターン**(学生・教員・会社員などのペルソナごとに 1 本)であり、行き先 POI の候補ではない。行き先は `<<INPUT 2>>`(最頻訪問地点)の差し込みで**暗黙に**示されるだけ。

- 自己整合性(逐語の要約): 候補パターン cp を、本人の軌跡 `T_i` と他人の軌跡 `T_~i` に対して LLM に 1〜10 で採点させ、`score_cp = Σ_{t∈T_i} r_t − Σ_{t'∈T_~i} r_{t'}` が最大のものを採る。ablation「w/o SC」は「a candidate pattern is **randomly picked**」。
- **本 repo への含意**: 「候補を作って LLM に採点させる」という**この形なら追加呼が要る**(候補 10 本 × 軌跡数)。**H は採点ではなく 1 回の選択なので追加呼 0** という設計上の差は正しい。

### 1-5 **TrajGenAgent は「LLM に候補を並べさせない」ことを明文の設計判断にしている**

出典: Siyu Li, Toan Tran, Lingyi Zhao, Khurram Shafique, Li Xiong, "TrajGenAgent: A Hierarchical LLM Agent for Human Mobility Trajectory Generation", arXiv:2606.12657v1。<https://arxiv.org/pdf/2606.12657>(pymupdf 14 頁)。**[実読]**

- 逐語: 「without requiring the LLM to **directly rank or search over large POI candidate sets**」。
- 候補構成(逐語): 「we retrieve a candidate POI set **rather than sampling from the full location space**. We first build an **individual-specific feasible set** `P_u(a_i)` from historical visits」+「a **top-K similar-individual pool** obtained via similarity matching over mobility signatures」→ `P(a_i) = P_u(a_i) ∪ P_sim(a_i)`。**空なら明示の invalid マーカーを出す**(黙って抽選しない)。
- 選択はエンジン: `S(p) = λ_f·s_freq(p) + λ_d·s_dist(p)`、`s_freq = (1−α)P_u + α·P_sim`(**α = 探索ゲート**)、`s_dist = exp(−β·|dist(p_{i−1},p) − ℓ̄_u|)`。正規化して**確率抽出**。
- **α の感度(逐語)**: 「Moderate changes in α have limited impact on our statistical or anomaly metrics, but **α = 0 can yield near-copy trajectories**」。← **探索ゲートは「入れないと写しになる」が「値には鈍い」**=v2 の ρ_i の感度試験の事前予想になる。
- **自由形のツール呼びは崩れる(Table V)**: 同じ Qwen2.5-32B で「free-form tool calling」は**軌跡単位の成功率 9.8% / 訪問単位 59.3%**、決定論ワークフローは **100% / 100%**。← **8B で「LLM に候補の検索から選択まで任せる」道が塞がっている外部証拠**。

---

## §2 候補提示(choice set)の理論 — 「3〜5」はどこから来るか

### 2-1 二段構造の正典(Manski 1977 → Swait & Ben-Akiva 1987)

- **Manski 1977**: `P(i) = Σ_C P(i|C)·P(C)`(選択集合 C 自体が確率変数)。Charles F. Manski, "The Structure of Random Utility Models", *Theory and Decision* 8(3):229–254, 1977。DOI <https://doi.org/10.1007/BF00133443>。**[二次・本文未取得]**(Springer が認証を要求・§6 ①)。
- **Swait & Ben-Akiva 1987**: 選択集合の生成を「無作為な制約」(利用可能性・認知)としてモデル化。*Transportation Research Part B* 21(2):91–102。DOI <https://doi.org/10.1016/0191-2615(87)90009-9>。**[二次・本文未取得]**(§6 ①)。
- **目的地選択への適用(交通側の定式化・逐語)**: 「the actual choice set … may substantially differ from the **universal choice set** … one of the most relevant examples within transport demand simulation is probably the **choice of destination**, wherein the universal choice set normally includes hundreds of traffic zones」(Cascetta & Papola 2009, *Transportation Research Part A* 43(2):170–179・<https://ideas.repec.org/a/eee/transa/v43y2009i2p170-179.html> の抄録・**[二次]**)。
  → **v2 で言えば「universal choice set = 渋谷の 2,337 POI」であり、二段構造は交通需要側の標準である。**

### 2-2 「3〜5」の一次に最も近い実読

出典: Elisabeth Honka, Ali Hortaçsu, Matthijs Wildenbeest, "Empirical Search and Consideration Sets"(Current version: April 2019)。<https://host.kelley.iu.edu/mwildenb/handbook.pdf>(pymupdf 76 頁・**[実読]**)。**掲載先の書誌(Handbook of the Economics of Marketing 第 1 巻)は本 PDF に記載が無い=[二次・未確認]**。

- 逐語①(§1): 「empirical marketing research in the 1980s found that many consumers effectively choose from (or "consider") a surprisingly small number of alternatives – **usually 2 to 5** – before making a purchase decision」(引用先は Hauser & Wernerfelt 1990, Roberts & Lattin 1991, Shocker ほか 1991)。
- 逐語②(§3-1): 「Hauser and Wernerfelt (1990) also provide an overview table with mean or median consideration set sizes … They find **most consideration sets to include 3 to 5 brands**.」
- **散らばりも同じ節に書いてある(フロア併記)**: Roberts & Lattin 1991 は**中央値 14**(ただし逐語「they **equate consideration with awareness** and that **aided awareness** was used to elicit the considered brands」=定義が違う)。Siddarth ほか 1995 は**平均 4.2**。Bronnenberg & Vanhonacker 1996 は**忠実客 1.5 / 非忠実客 2.8**。Mehta ほか 2003 は**1.8〜2.8**(液体洗剤・ケチャップ)。
  → **「3〜5」は中心であって帯ではない。定義(認知か検討か)で 1.5〜14 まで動く。**
- **Hauser & Wernerfelt 1990 の原典(<https://doi.org/10.1086/209225> → OUP・<https://web.mit.edu/bwerner/www/papers/AnEvaluationCostModelofConsiderationSets.pdf>)は JSTOR の画像スキャン(JBIG2)で本文テキスト層が無く、Table 1 の品目別の値は取得できなかった=空欄**(§6 ③)。

### 2-3 候補生成に使える「距離の冪」は δ ではなく α

- **訂正**(§0-2 の 5 行目の再掲): EPR の探索の跳躍距離は `P(Δr) ~ Δr^{-1-α}`・**α = 0.55 ± 0.05**(Song ほか 2010・Fig.「Scaling Anomalies」・親確認済 [lit/mobility__song2010_epr.md](lit/mobility__song2010_epr.md))。**δ = 1.2 ± 0.1 は訪問頻度の Zipf**(`f_k ~ k^{-δ}`・`δ = 1+γ`)であって距離ではない。
- **ただし渋谷 2 km 四方では α をそのまま使えない**: 原典のカットオフは Δr ≈ 100 km。既存答申の注意「渋谷 2km 四方では距離べき則はカットオフ支配で β 検証は無意味」(`v2-llm-mobility-research.md` §5-4・**D 等級なので一次未確認だが、主張の向きは Song の Δr カットオフ 100 km から算術的に従う**)。
- **先行が実際に使っている候補生成の重み**は 3 種類しかない: ①**距離減衰**(重力則 `S_j/D_ij^β`=AgentSociety / `exp(−β|dist−ℓ̄|)`=TrajGenAgent / 距離昇順の並べ替え=LLM-Move)②**本人の頻度**(`Π_i=f_i` の EPR / `P_u(p|a)` の TrajGenAgent)③**他人の集合的人気**(d-EPR の `n_i n_j/r_ij²` / TrajGenAgent の `P_sim` / CitySim の「該当 POI 密度」)。
  → **親案 H の「馴染み K-1・探索 ρ・趣味 α」は ①②に対応し、③(集合的人気)が抜けている。** P3 答申 §3-4 は③を「観測(在圏密度・行列・看板)として LLM に見せる」と提案しており、**候補生成に③を直接入れるかどうかはユーザー判断の分岐点**(§5-4)。

---

## §3 8B にとっての候補提示の副作用

### 3-1 位置・順序バイアス — 数字は 4 系統で一致して大きい

| 出典 | 測った物 | 数値 | 一次 |
|---|---|---|---|
| **LLM-Move**(前掲・Table IV) | **POI 候補 101 件の並べ替え** | Acc@1 **.5200(距離昇順)→ .2000(距離降順)→ .3250(無作為)**。**2.6 倍** | **実読** |
| **Pezeshkpour & Hruschka 2023**(arXiv:2308.11483・<https://arxiv.org/abs/2308.11483>) | 選択肢の並べ替え | 逐語「a considerable performance gap of approximately **13% to 75%** in LLMs on different benchmarks」。**少数事例を足しても消えない**。緩和=上位 2 候補を**隣り合わせに置く**(最初と最後に置くと増幅)+較正で**最大 8 pt** | 抄録のみ |
| **Zheng ほか 2023**(ICLR 2024 Spotlight・arXiv:2309.03882・<https://arxiv.org/html/2309.03882v4>) | 選択肢 **ID** への偏り(RStd=選択肢別 recall の標準偏差)・20 モデル | **llama-2-7B 23.0 / llama-2-13B 7.5 / llama-2-70B 4.1**(MMLU・0-shot)。falcon-7B 24.2 / falcon-40B 6.7。**正解を A に寄せると llama-30B が 53.1→68.2(+15.2)、D に寄せると 41.2(−11.9)** | **実読** |
| **Hou ほか 2023**(ECIR 2024・arXiv:2305.08845・<https://arxiv.org/html/2305.08845v2>) | 推薦候補 **m=20** の中の正解位置 {0,5,10,15,19} | 逐語「the ranking performance **drops significantly when the ground-truth items appear at the last few positions**」。加えて**人気バイアス**「popular items tend to be ranked at higher positions」 | **実読**(数値は図のみ=空欄) |

**Zheng の但し書き(逐語)**: 原因は位置ではなく**トークン**寄り——「The model may favor options presented at specific ordering positions」は「somewhat present but **quite irregular**」で、主因は「a priori assign more probabilistic mass to specific ID tokens (such as A or C)」。
→ **設計への含意**: 「1 2 3 4」「A B C D」のような**番号ラベルを付けると、ラベル自体が偏りを持ち込む**。**ラベルを付けずに項目そのものを書かせる**(v2 の「対象」欄は自由文なのでこれができる)ほうが、この経路は細い。ただし**位置バイアスは残る**(LLM-Move の実測は並べ替えだけで 2.6 倍)。

### 3-2 緩和策の先行(そのまま腕にできる)

- **並べ替えの反復集約(bootstrapping)**: Hou 2023(逐語)「rank the set repeatedly B times with **candidates randomly shuffled at each round**」・実験は **3 回**。→ **v2 では呼数が 3 倍になるので採れない**。代わりに**体ごとに 1 回だけ順序を撹拌する**(= 集団平均では一様、個体では固定)。
- **前置きの事前補正(PriDe)**: Zheng 2023。5% の標本で選択肢 ID の事前分布を推定して除く。**llama-2-7B で RStd 23.0→5.5・精度 35.8→40.2**。→ **v2 の「対象」欄は自由文でロジット後処理をしていないので直接は使えない**(§6 ④)。
- **repo に既に同型の機構がある**: `commit.py:702-710` の会話相手選びは「セル内の並びは **blake3 撹拌**(ID 順バイアス=v1 C-8 を断つ・T5 の監査点)」。**候補の並びにも同じ撹拌をかけるのが最小の実装**。

### 3-3 理由文は「後付け」である — 検証の先行はほぼゼロ

- **Turpin ほか 2023**(NeurIPS 2023・arXiv:2305.04388・<https://arxiv.org/abs/2305.04388>)**[抄録のみ・逐語は abs から]**: 「by **reordering the multiple-choice options** in a few-shot prompt to make the answer always "(A)"」という偏りを入れると「accuracy to drop by as much as **36%** on a suite of 13 tasks from BIG-Bench Hard」。そして**モデルはその偏りを説明文に一度も書かない**(「models **systematically fail to mention** in their explanations」)。結論(逐語)「CoT explanations can be **plausible yet misleading**」。
- **LLM-ZS**(前掲)の理由文の評価は**質的のみ**(逐語の要約: 大きいモデルは具体的 id を挙げ、小さいモデルは一般論を言う。**尺度・人手評価・忠実性スコアは無い**)。
- **AgentMove / LLMob** は `reason` 欄を出すが**検証していない**。
→ **含意**: **「理由文が書けたから思考が入った」は証拠にならない。** 本 repo が理由文で主張できるのは「①書式として成立したか ②理由文に現れた語が候補の属性(距離・馴染み・種別)を指しているか」までであり、**「その理由で選んだ」は測れない**。測るなら**介入**(候補から 1 件抜いて選択が動くか)しかない(§4-3)。

### 3-4 本 repo の内部証拠(メニュー効果・例示の写し)

- **メニュー効果**(AB7・第201・`docs/bench/c8/ablation/ab7_s1_parent_report.md`): 白リスト 12 語を見せると 8 語が出る(エントロピー **1.564 bits**)が、自由文にすると「行く・食べる」の 2 語に 90% 集中(**1.137 bits**)。**乗車 907 → 1**。親の読み(逐語)「ホワイトリストは**メニュー効果**で細かい動詞(乗車・休憩・待機・退去)を選ばせていた」。
- **語彙 v2 でも同じ向き**(AB7c・第227・`ab7c_s1_parent_report.md`): open_v2 の移動 67.5% / 乗車 **0**。逐語「『メニュー効果』は語彙 v2 でも同じ向き」。
- **欄名の写し**: AB7 で「行動」と書いた体が 90。第223 では**観測テンプレの欄の説明語をそのまま対象欄に書いた応答が「物のカテゴリ」9,055 呼・「セルID」398 呼**(`contract.py:856-861` の `TARGET_PLACEHOLDERS` はこれを吸うための後付け)。
- **例示の具体値の写し 47%**(W17 v2 第 1 回・第164)。
→ **候補提示の副作用の予想(v2 固有)**: **①候補に書いた語がそのまま対象欄に返る**(これは狙いどおり=接地率が上がる)。**②候補の並びの 1 番目が過剰に選ばれる**(位置バイアス)。**③候補に無い店が選ばれなくなる**(メニュー効果の裏面=候補集合の作り方が分布を決める。AB7 で「辞書 `SYNONYMS` が実質の語彙になった」のと同型)。**③が最大のリスク**——候補生成規則が**設計者の指紋そのもの**になる。

---

## §4 検証設計 — 何を測れば「LLM の思考が入った」と言えるか

### 4-1 照合先(P3 答申 §6-1 の 5 行を、先行が実際に使っているかで格付けし直す)

| 案(P3 §6-1) | 照合値 | **先行での使用** | 1 日ランで測れるか |
|---|---|---|---|
| **P-1 訪問の普遍則** `ρ_i(r,f)=μ_i/(rf)^η`・η≈2 | Schläpfer 2021 | **使われている**: When Plausible の Table 6 に「Distance-frequency [32] `ρ_i(r,f)=μ_i/(rf)^η`」が検証指標として載る | **✗**(f=訪問日数。1 日では f∈{0,1}) |
| **P-2 訪問頻度 Zipf** δ=1.2±0.1 | Song 2010 | **使われている**: COMPASS の「Visit-Freq」(ζ)・When Plausible の「Visitation frequency」 | △(店あたり訪問者数の傾きなら 1 日で出る。ただし**日をまたぐ頻度ではない**) |
| **P-3 returners/explorers** | Pappalardo 2015 | **使われている**: When Plausible の「Mobility profiles = GMM(Intermittency, Deg. of Return) → Scouters/Regulars/Routiners」 | **✗**(複数日) |
| **P-4 業態別リピート率** | 外食総研 2018 | 該当なし(日本固有) | **✗**(複数日) |
| **P-5 人気と距離の無相関** R²<0.03 | Schläpfer 2021 | 該当を確認できず | **○**(訪問者数 vs 平均自宅距離。1 日で計算可) |

**新規に足す候補(本書)**:

| 案 | 照合値 | 判定型 | 1 日 | 根拠 |
|---|---|---|---|---|
| **P-6 到達 POI 被覆率** | **基線の理論上限を超えること**。現行 `_poi_in_cell` は**セル内 id 最小の 1 件**しか返さないので、購入で到達しうる distinct POI は **315 / 2,337 = 13.5%**、食事は **206 / 823 = 25.0%**(サブが `w6_poi.parquet` を再集計・親検算可) | existence(1 本の数字で落ちる門) | **○** | 本 repo の実装。**H/EPR どちらも、この天井を破らなければ「行き先を選んでいる」と言えない** |
| **P-7 提示順位別の選択率** | 候補の**提示順位 r ごとの選択率**。帰無 = 一様 1/k | shape(**負の対照**) | **○** | LLM-Move Table IV・Hou 2023 Fig.3(a) |
| **P-8 店あたり訪問者数の Zipf 傾き** | `f_rank ~ rank^{-s}` の s。基線は極端に集中(1 セル 1 店) | shape | **○** | COMPASS の Visit-Freq の 1 日版 |

### 4-2 **「集計指標は方策を区別しない」という一次の警告(§4 の設計を決める)**

出典: Tatsuya Amano, Hirozumi Yamaguchi, "Distilling Aggregate Mobility Statistics into a Language Model Policy for Post-Event Crowd Simulation", arXiv:2608.19778v1(SIGSPATIAL 2026)。<https://arxiv.org/html/2608.19778>。**[実読]**

- 比較対象(逐語): 「four LLM-based variants (no grounding, naive SFT, IPF at inference, and GRPO)」+「a **rule simulator tuned by CMA-ES**」+「an LLM prompting agent (**LLMob**)」+「a **classical gravity model**」。
- 結論(図 3 のキャプション・逐語): 「**Grid correlation is insensitive across calibrated policies, whereas destination-share error separates them.**」本文(逐語)「the grid correlation is similar across all behavioural priors, landing near **0.75**」「so this metric alone **leaves them indistinguishable**」「grid-count correlation alone can **hide important behavioural differences** between policies」。
- 分けた指標: 行き先の構成比(station / mall / other の観測比 **0.744 / 0.064 / 0.192**)の絶対差の和。微調整方策は mall 比を **0.02 → 0.09**(観測 0.06)へ持ち上げ、誤差を **25%** 削った。
→ **v2 への直訳**: **在圏カーブ(D1′)や密度段階では、基線/EPR/H の差は出ない可能性が高い。差が出るのは「どの店が選ばれたか」の構成比**(= P-6・P-8)。**D1′ を H の合否に使ってはいけない。**

### 4-3 腕の定義(5,000 体 × 1 日・実 LLM・node/edge は現行既定に合わせる)

| 腕 | 行き先の決め方 | 目的 |
|---|---|---|
| **A0 基線** | 現行(`_poi_in_cell` のセル内 id 最小) | 天井 13.5% / 25.0% の確認・帰無 |
| **A1 EPR 単独** | エンジンが `P_new = ρ_i·S_i^{-γ}`(ρ_i〜N(0.6,·)・γ=0.21)で探索/回帰を決め、回帰先 `Π_i=f_i`・探索先は候補プールから距離で抽選。**LLM は行き先を見ない**(観測も変えない=バイト不変) | **H の対照**。P3 答申の推奨形 |
| **A2 H** | エンジンが候補 k=4 を作り(§5-1)、観測に 1 行足し、**LLM が既存の「対象」欄で 1 つ選ぶ**。追加呼 0 | 本命 |
| **A3 H + 順序乱択** | A2 と同一。**候補の並びだけ blake3(run_salt‖agent_id‖tick)で撹拌** | **位置バイアスの対照**(A2 との差が位置バイアスの大きさ) |
| **A4 H − 名前**(任意) | A3 と同一だが候補に**店名を出さず種別+馴染みだけ** | CitySim の「ブランド POI への正の偏り」の対照 |

- **帰無参照(フロア)**: 既存の実測をそのまま使う——**行動分布 JSD の seed 差 0.0035 bits**(AB7)・**3 seed 帰無参照 0.000178 bits**(第220)。**腕間の差がこれを超えなければ何も言えない。**
- **A2 vs A3 の差が P-7 の主張**。A3 で P-7 が一様に近づき、かつ P-6/P-8 が A2 と変わらなければ「**選んでいるのは順序ではなく中身**」と言える。逆に A3 で P-6/P-8 が崩れれば「**選択は順序が駆動していた**」= H は棄却。
- **理由文の「使った」検査(§3-3 の唯一の道)**: A2 の応答テープから、**候補 1 件を抜いた反実仮想を同一 seed で再生**する(`engine/tape.py` の再生+`causal__shah2026_agent-replay` の point-of-commitment 則)。抜いた候補を選んでいた体が**別の候補へ移るか、待機へ落ちるか**を数える。→ **これは新しい計器が要る(先に聞く拡張)。**

### 4-4 費用の算術(**追加呼 0 を保つ実装案**)

**前提(本 repo の実測)**:
- トークン見積規約: `perception/channels.py:73` `estimate_tokens(text) = max(1, len(text)//2)`。
- ブロック予算(知覚契約書 §2.2): **B5 220 + B6 80 = 300 = 個体部の上限ちょうど**。**B2 150 + B4 60 + B4b 40 = 250 = セル依存部の上限ちょうど**。
- BN-2C 実測: **個体末尾 300→800 は −8.1%/100tok**・**共有 600→1400 は −1.6%/100tok**・個体→共有へ 200 tok 移すと **+23.8%**。
- 現況: 5,000 体 × 1 日で **36,906〜37,165 呼(7.38〜7.43 呼/体/日)・約 38 min/腕**(AB7c 第227)。L4 上限は 400 万呼/日。

**候補行の実測見積(サブが実 POI 名で作文して文字数を数えた・親検算可)**:

| 書式 | 例 | 字 | tok | 個体側 | 共有側 |
|---|---|---|---|---|---|
| A 名前+訪問回数 k=3 | `[B5 候補] 行ける店: 1 ローソン(3回)2 チャングミ(初)3 観世能楽堂(初)。` | 45 | **22** | **−1.8%** | −0.4% |
| A 名前+訪問回数 **k=4** | 同(4 件) | 57 | **28** | **−2.3%** | −0.4% |
| A 名前+訪問回数 k=5 | 同(5 件) | 70 | **35** | **−2.8%** | −0.6% |
| B 種別+方角+馴染み k=4 | `[B5 候補] 行ける先: 1 コンビニ 北 よく行く 2 ラーメン 東 初 …` | 58 | **29** | −2.3% | −0.5% |
| C 種別のみ k=4 | `[B5 候補] 行ける先: 1 コンビニ 2 ラーメン 3 カフェ 4 書店。` | 39 | **19** | −1.5% | −0.3% |
| D 名前のみ k=4(**セル共有可**) | `[B2 候補] この区画の店: ローソン、チャングミ、…。` | 41 | **20** | — | **−0.3%** |

**結論(3 点)**:
1. **追加呼は 0 にできる**(既存の「対象」欄で答えるので呼数は変わらない)。**スループット費用は −1.5〜−2.8%**=38 min/腕なら **1 分未満**。L4 400 万呼/日の門には触れない。
2. **しかし予算表の上限に余白が無い**。取れる道は 3 つ: **(α) 個体部の予算 delta を宣言する(300→328)**・**(β) 等級 E の行と差し替える**(B5 被注視 15 tok・E / B5 自己状態 65 tok・E / B2 地物 25 tok・E)・**(γ) 候補行をセル共有の B2 に置き、馴染みは書かない**(書式 D)。**(β) が最も安い**——E 行は「結果を駆動していない証明」が元から義務づけられている。
3. **馴染み(K-1 の訪問回数)を書いた瞬間、その行は個体固有になり B2 のバイト共有が壊れる**(知覚契約書 §1-3 の差分観測禁止と同じ理由=実測 −38%)。**「候補は共有・馴染みは個体」に分ける**なら、B2 に候補名・B5 に「よく行く店: ローソン」の 1 行、という 2 行構成になる(合計 tok は増えるが、重いほうが共有側に乗る)。

### 4-5 予測タスクの数字を設計根拠に使うときの注意(**親が受け取るときの警戒**)

§1 の (d) 列の Acc@k は**全部「次にどこへ行くか」を当てる予測タスク**であり、
- **正解が候補集合に必ず入っている**(LLM-Move は「ground truth POI + 100 random」)。v2 には正解が無い。
- **holdout に相当するものを持っていない**(本 repo の事前登録の主張とは別の土俵)。
- LLM-Move の .52 は **gpt-3.5-turbo**、AgentMove の Llama3-8B は**返答率**だけが報告されている。**8B での Acc は先行に無い**(§6 ⑤)。
→ **「LLM-Move が規則に勝った」を H の根拠に使うのは越権**。使えるのは**設計の形**(距離をエンジンが計算して渡す・並び順が効く)までである。

---

## §5 推奨 — H を採るときの候補生成規則

**表記**: **[根拠あり]** = §1〜§4 の一次に支えられる。**[未リサーチ(expedient)]** = サブの自前構成で、外部の裏づけを取っていない。

### 5-1 候補の作り方

| 項 | 推奨 | 等級 |
|---|---|---|
| **k(候補数)** | **4**(3〜5 の中央)。**ただし可用数で打ち切る**(セル内 POI の中央値は 4・食事は 2) | **[根拠あり]** 消費者行動「2〜5」「ほとんどが 3〜5」(§2-2)+ CitySim 再実装の「3–5 candidate Neighborhoods」(§1-3)。**k を 1 つに固定するのではなく、k∈{2,4,8} を感度腕にする**のが安い |
| **母集合(いちばん重要)** | **現在セルに閉じない**。`P(a) = P_u(a)(K-1 の訪問履歴)∪ P_near(a)(現在セルと隣接 8 セルの該当種別 POI)` | **[根拠あり]** TrajGenAgent の `P_u ∪ P_sim`(§1-5)+ When Plausible の「full set から選ばせるな」(§1-3)。**ただし v2 は `P_sim`(類似個体)を持たないので `P_near`(近傍)で置換=[未リサーチ]** |
| **内訳(3 枠)** | **馴染み 2 枠**(K-1 の訪問回数上位=`Π_i=f_i`)+ **探索 1 枠**(未訪問から距離重み `Δr^{-1-α}`・α=0.55 で抽選)+ **趣味 1 枠**(P1 の種目 → 対応 POI 集合から抽選) | **[根拠あり]**(3 種の重みは §2-3 の①②)/ **枠の配分 2:1:1 は [未リサーチ(expedient)]** |
| **集合的人気(③)** | **候補生成には入れない**。人気は「行列」「密度」として **B4 の観測**に既に載っている | **[根拠あり]**(P3 §3-4 の線・「世界の変化はエージェント行動の結果」)。ただし d-EPR/PEPR が「人気を入れて初めて二分が出る」と言っている以上、**P-3 が出ないときの第一容疑者**として登録する |
| **並べ方** | **体ごと・tick ごとに blake3 撹拌**(`commit.py:702-710` の `wake_tiebreak_array` と同じ salt 規約) | **[根拠あり]** LLM-Move 2.6 倍・Hou の bootstrapping・repo 内の先例(会話相手) |
| **番号ラベル** | **付けない**。候補は読点区切りの名詞列だけ | **[根拠あり]** Zheng 2023「主因はトークンバイアス(A/C に確率質量)」 |
| **空のとき** | **候補行を出さない**(「なし」も書かない)。**黙って抽選しない** | **[根拠あり]** TrajGenAgent「emit an explicit invalid marker (rather than silently sampling)」 |

### 5-2 見せる情報

| 欄 | 推奨 | 理由 |
|---|---|---|
| 名前 | **出す。ただし A4 腕(名前なし)を同時に回す** | CitySim の「ブランド POI への正の偏り」(既存 lit メモ)。**渋谷は実在ブランドの塊なので、この汚染は v2 で最大級** |
| 種別 | **出す** | 語彙 v2 の「食事/購入」と対象欄の `ITEM_CATEGORY` が既に種別で繋がっている |
| **距離** | **エンジンが計算した語(「すぐ近く」「1 区画先」)で出す。数値 m は出さない** | LLM-Move「距離は我々が計算して入力にする」+「LLM は地理文脈を正確に理解できない」。**数値を出すと W17 の「例示の具体値を 47% 写す」と同型の事故が起きうる**=[未リサーチ] の判断 |
| **訪問回数** | **回数の数字ではなく段階語(「よく行く」「前に行った」「はじめて」)** | 同上(数字の写し)。段階の刻みは **[未リサーチ(expedient)]** |
| 価格・評判 | **出さない** | 経済の保存則・広告レーンと二重になる |

### 5-3 理由の書式

**既存の 2 行形を変えない。**(`templates.py` の出力規約「理由: … / 行動: … 対象: … ひと言: …」)。**候補を選んだ理由は「理由」欄に自然に出るものだけを見る。専用の欄を足さない。**
- 根拠: §3-3(理由文は後付けで、偏りを書かない)。**専用欄を足せば書式は増えるが、忠実性は増えない。**
- 測るのは「理由文に候補の属性語(馴染み語・種別語・距離語)が現れた率」まで=**記述統計であって主張ではない**と宣言する。

### 5-4 **ユーザー判断の分岐点(3 つ)**

1. **H を採るか、P3 答申の推奨(エンジン単独)を採るか。** 本書の一次調査は**両論**を出した——**H に不利**: When Plausible §5-1(単純な重力が LLM 主導に勝つ・STVD 607.69 vs 748.71)・TrajGenAgent の設計判断(LLM に候補を並べさせない)・Zheng の 7B の RStd 23.0。**H に有利**: LLM-Move の Acc@1 .52 > 最近傍 .3702・When Plausible §5-1 の個体距離(14.83→7.53 km)・そしてユーザー意向そのもの。**決め手になる新事実は本書では出せなかった**。だから **A1 と A2 を同じ日に回して測る**のが本書の推奨。
2. **候補生成に「集合的人気」を入れるか**(§5-1 の③)。入れないと P-3(returners/explorers の二分)が出ない可能性が高いことを、Pappalardo と Schläpfer が別々に言っている(P3 答申 §1-2・§1-3)。**入れると「重力則の外生注入」になり `v2-llm-mobility-research.md` §4 の「不可」に触れる**。
3. **予算の取り方**(§4-4 の α/β/γ)。**(β) E 行との差し替え**を推奨するが、被注視 15 tok は「社会的創発の素地」として置かれた行なので、削ると別の主張に影響する。

---

## §6 空欄・親の一次確認が要る項目

| # | 項目 | 状態 | 次の手 |
|---|---|---|---|
| ① | **Manski 1977 / Swait & Ben-Akiva 1987 の本文** | **[二次]**。Springer が認証を要求(`idp.springer.com` へ 303)・Elsevier も同様 | 大学図書館経由か、Ben-Akiva & Lerman 1985 *Discrete Choice Analysis*(MIT Press)第 ? 章で代替 |
| ② | **UrbanLLM(2406.12360)・GeoLLM(2310.06213)の本文** | **未読**(検索要約で「該当なし」と判断) | 該当なしの判断を覆す材料が出たら読む。優先度低 |
| ③ | **Hauser & Wernerfelt 1990 Table 1 の品目別の値** | **取得不能**。<https://web.mit.edu/bwerner/www/papers/AnEvaluationCostModelofConsiderationSets.pdf> は JSTOR の**画像スキャン(JBIG2)でテキスト層が無い** | OCR するか、「3〜5」は Honka ほか 2019(§2-2・実読)の逐語で足りると判断する |
| ④ | **PriDe 型の事前補正が自由文欄に適用できるか** | **空欄**。先行は全部「選択肢 ID のロジット」を前提 | v2 は対象欄が自由文なので、**適用先が無い**可能性が高い。順序撹拌(A3)で代替する前提で進める |
| ⑤ | **8B 級での候補提示型の Acc** | **空欄**。LLM-Move は gpt-3.5 のみ・AgentMove は Llama3-8B の**返答率**(94% / 75.6%)だけ・LLM-ZS の Llama 3.1 8B の値は SI の図のみ | **先行に無い=v2 の A2 腕が最初の測定になる**。これは新規性でもある |
| ⑥ | **LLM-Move Table IV の Acc@5/@10 と TKY 側の順序 ablation** | **部分**(NYC の Acc@1/@5/@10/MRR は取得済・TKY の並べ替え表は未取得) | 必要なら HTML の Table IV を再読 |
| ⑦ | **Hou 2023 の位置バイアスの数値** | **図のみ**(Fig.3(a)(b) は HTML に描画されない) | PDF から図を読むか、数値は引かない |
| ⑧ | **When Plausible の Shanghai 側の STVD 数値** | **空欄**(本文は「also lower for AgentSociety」とだけ) | 表 2 を再読 |
| ⑨ | **Honka ほか 2019 の掲載書誌** | **[二次]**。PDF 自身に Handbook 名の記載が無い(表紙は "Current version: April 2019") | Elsevier の *Handbook of the Economics of Marketing* Vol.1 の目次で確認 |
| ⑩ | **`eatery_mask` の分類の穴(サブ発見・親検収対象)** | `world/assets.py:491` の `hash_free_cat_code` は `food` のみ 1(飲食)。**`nightlife` 259 件は飲食に入らない**(2 に落ちる)。候補集合を「食事」で作るとこの 259 件が永久に外れる | 候補生成の前に、**種別 → 候補母集合**の写像表を 1 枚作る(D-88 ② の公園欠陥と同型の穴) |

**ダウンロード**: 政府・公的機関ドメインからのデータ取得は**行っていない**(ライセンス台帳への追記は不要)。読んだ PDF は WebFetch が一時領域へ保存したものを pymupdf で抽出しただけで、**リポジトリ内には 1 バイトも置いていない**。

---

## lit README 追記行

(`docs/research/lit/README.md` の索引表へ親が貼る。**新規出典のみ**。メモ本体は本答申と同時に作成した。)

```markdown
| [mobility__feng2024_llm-move-candidate-order](mobility__feng2024_llm-move-candidate-order.md) | 人間移動科学 #3 / 自然言語処理 #27 | **実読**(サブ・親未確認) | **候補提示型の設計が全部書いてある 1 本**。候補 101・距離はエンジンが計算・**並べ替えだけで Acc@1 .52→.20**(順序の負の対照の原典) |
| [mobility__santos2026_unconstrained-poi](mobility__santos2026_unconstrained-poi.md) | 人間移動科学 #3 / 検証とV&V #22 | **実読**(サブ・親一部確認済=第210) | 「**無制約 POI 選択**」の逐語(候補集合を作る正当化)と、**単純な重力が LLM 主導の POI 選択に勝つ**(STVD 607.69 vs 748.71)/個体距離は逆 |
| [mobility__li2026_trajgenagent-candidates](mobility__li2026_trajgenagent-candidates.md) | 人間移動科学 #3 / ABM方法論 #21 | **実読**(サブ・親未確認) | 候補 = 履歴 ∪ 類似個体・**選ぶのはエンジン**(「LLM に大きな候補集合を順位づけさせない」)・**自由形ツール呼びは軌跡成功率 9.8%** |
| [nlp__zheng2023_selection-bias](nlp__zheng2023_selection-bias.md) | 自然言語処理 #27 | **実読**(サブ・親未確認) | **選択肢 ID への偏りは小さいモデルほど大きい**(llama-2-7B RStd 23.0 / 70B 4.1)・主因は位置でなく**トークン**=番号ラベルを付けない根拠 |
| [nlp__turpin2023_unfaithful-cot](nlp__turpin2023_unfaithful-cot.md) | 自然言語処理 #27 / 科学哲学 #26 | **抄録のみ**(サブ・親未確認) | **理由文は偏りを書かない**(並べ替えの偏りで精度 −36% でも言及ゼロ)=「理由が書けた」を証拠にしない根拠 |
| [econ__honka2019_consideration-sets](econ__honka2019_consideration-sets.md) | 計量経済(離散選択) / 消費者行動 | **実読**(サブ・親未確認) | **候補数「2〜5」「ほとんどが 3〜5」の逐語**と、定義差で 1.5〜14 まで動く散らばり(フロア併記) |
| [mas__amano2026_aggregate-stats-distill](mas__amano2026_aggregate-stats-distill.md) | 計算社会科学 #25 / 検証とV&V #22 | **実読**(サブ・親未確認) | **集計指標(格子相関 ≈0.75)は方策を区別しない**・行き先構成比だけが分ける=H の合否に D1′ を使えない根拠 |
```

---

## 親確認の要請(上位 5 件)

1. **`v2-llm-mobility-research.md` が D 等級であること**(同書ヘッダ)。→ **本書 §0-2 の扱い(カバー済みとして引かず、5 本を取り直した)を承認するか**。併せて §0-2 の表の **訂正候補 2 件**(TrajGenAgent の「活動チェーンだけ」は不正確・**EPR の距離冪は α=0.55 であって δ=1.2 ではない**)を設計書へ伝播させるか判断。出典 <https://arxiv.org/pdf/2606.12657> / [lit/mobility__song2010_epr.md](lit/mobility__song2010_epr.md)。
2. **When Plausible §5-1 の 2 つの逐語と 4 つの数値**(「simpler gravity-based destination selection … outperforms CitySim's LLM-driven POI-selection strategy」/ STVD W₁ **607.69 ± 5.88 vs 748.71 ± 23.00** / Δr 誤差 **14.83 → 7.53 km** / r_g **7.29 → 3.47 km**)。**H の可否を左右する唯一の直接比較**。出典 <https://arxiv.org/pdf/2606.13835>(pymupdf・付録 B.5 と §5-1)。
3. **LLM-Move Table II / Table IV**(Acc@1 NYC: **Dist .3702 / LLMmove .5200**、順序 **Dist昇順 .5200 / 降順 .2000 / 無作為 .3250**)。**候補提示の効果と、順序の危険の両方がこの 1 表にある**。出典 <https://arxiv.org/html/2404.01855v2>。
4. **候補数 3〜5 の一次**(逐語「usually **2 to 5**」「most consideration sets to include **3 to 5** brands」+ 散らばり Roberts & Lattin **中央値 14**/Siddarth **4.2**/Mehta **1.8〜2.8**)。出典 <https://host.kelley.iu.edu/mwildenb/handbook.pdf>(pymupdf 76 頁)。**Hauser & Wernerfelt 原典は画像スキャンで抽出不可=§6 ③**。
5. **費用と予算の算術**(候補行 k=4 = **28 tok** / 個体側 **−2.3%** / **B5 220+B6 80=300 = 上限ちょうど**)と、**基線の到達 POI 天井 13.5%(315/2,337)・食事 25.0%(206/823)**。前者は `perception/channels.py:73` + 知覚契約書 §2.2 の BN-2C 実測、後者は `w6_poi.parquet` のサブ再集計(親が再計算可: POI 2,337・POI を持つセル 315・中央値 4・p90 19・最大 52 / food 823・206 セル・中央値 2)。
