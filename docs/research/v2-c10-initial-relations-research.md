# 答申: 関係の強さは「記憶の基底活性」から導けるか / 初期の関係網はラン前の会話で作れるか — 社会ネットワーク科学 #14(2026-09-17・C10 着手前ラウンド)

<!-- hdr:v1 -->
- **分野**: 社会ネットワーク科学 #14 / 認知科学(記憶・習慣)#12 / ABM方法論 #21 / 自然言語処理・機械学習 #27 | **重要度**: **P1**(C10 の着手条件 3 つの指紋①②③をユーザーが差し戻した件の直接材料。**単独で決定できる**のは §6(i) の表まで。ウォームアップの採否は §6(iii) の 5,000 体腕を回してからが正しい)
- **一次確認**: **B**(リサーチサブ Opus 5 が 22 出典を当たった。**私自身が本文を機械抽出して逐語を確認した = 8 本**(Gilbert & Karahalios 2009・Saramäki 2014 arXiv 版・Dunbar 2020 ORA 版・Zhao 2012 CogSci・CitySim 2025・Learning to Make Friends 2025・Li 2026 scoring bias・内閣官房 R5 概要)。**WebFetch の読み取り器経由で本文を読んだ = 4 本**(Roberts & Dunbar 2015 PMC・Hamill & Gilbert 2009 JASSS・Generative Agents HTML・Grading Scale 抄録)。**検索要約のみ = 6 本**(OASIS・AgentSociety・Sotopia・Concordia・LLM-SocioPol・McPherson 2001)。**取得不能 = 2 本**(Zhou et al. 2005 = royalsocietypublishing 403・IPSS 図表5-3 の図中数値)。**親一次確認は未了**——§「親確認の要請」に 5 件を置いた) **→ 親確認 3 件+実物確認 2 件(第230)**: Gilbert & Karahalios 2009(CHI・PDF・親 pymupdf)「R2 = 0.534」「Days since last communication −0.76」「Days since first communication 0.755」「2,184 rated Facebook friendships」「35 participants」「The two Days since variables have such high coefficients due to friends that never communicated via Facebook」✓ / Zhao et al. 2012(CogSci 34・eScholarship PDF・親 pymupdf)「ACT-R and its memory equations replicated an effect similar to that of Dunbar's (1998) number」「800 versus 1,336」「memory activation thresholds」「40 agents」✓ / Li et al. 2026(arXiv 2506.22316v4・HTML 本文)Table 3「Qwen3-8B | Descending-Numeric | 46.22」「Qwen3-32B … 28.56」「possibly due to its small size」✓(FR=flip rate・BiGGen Bench)。**実物確認**: `engine/conversation.py` `ConversationManager(max_participants=2 既定・上限 3)`+`talk_partner` 1 本=既定では 3 人会話 0%(上限 3 は引数で可)/ 行動契約 §5 半減期 90 日 vs C10 議題書 30 日=齟齬あり ✓。Dunbar 2020・内閣官房 R5 は親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **lit**: [lit/README.md](lit/README.md)(本答申と同時に **8 本**) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)
- **既存答申との関係**: [v2-c10-relations-brief.md](../design/v2-c10-relations-brief.md)(材料・重複しない)/ [v2-c10-relations-agenda.md](../design/v2-c10-relations-agenda.md) §5(本答申が答える 3 つの指紋)/ [v2-memory-retrieval-research.md](v2-memory-retrieval-research.md)(記憶の U1・**等級 D = 一次確認が丸ごと残る**ので本書は認知設計書 §4 の式だけを引く)/ [v2-personality-traits-research.md](v2-personality-traits-research.md) §3-2/§3-3(Contreras 2026 の自己申告=行動の乖離・写しの 47%。**再調査しない・参照のみ**)/ [v2-action-conversation-contract-research.md](v2-action-conversation-contract-research.md)(E1〜E5・約束の遵守率は空欄)/ [v2-ad-information-research.md](v2-ad-information-research.md)(看板=単純感染 / 口コミ=複雑感染)

> **問い**: ユーザーの 2 つの問い。**問 A** = 関係の好悪(①3 値尺度)と辺の増減(②Δ と半減期)を、**わざわざ数で定義せず**、エージェントに記憶を組み込めば会話から自ずと生まれるのではないか。あるいはランの中で経験から設定してよいのではないか。**問 B** = 初期の関係性(③組織内 15 人中 5 本を一様乱択)を、**ランの前にランダムに選んだエージェント同士を会話させて**構築してはどうか。
>
> **答え(要旨)**。6 つ分かった。
>
> **(i) 問 A はほぼ正しい。②(Δ 5 個+半減期 30 日)は丸ごと消せる。** 関係の強さを相互作用の履歴から予測した最良の実証(Gilbert & Karahalios 2009・2,184 友人関係・70 超の変数)で、**標準化 β が最大の予測子は「最終接触からの日数」(β=−0.76)、2 位が「初回接触からの日数」(β=0.755)**。すなわち**再帰性(recency)と履歴の長さ(duration)だけで半分以上**が説明される(Adj R²=0.534・上位 15 変数で「半分以上の情報」と著者が明記)。これは **ACT-R 基底活性 A(m)=ln Σ(Δt_j+1)^(−d) が計算している量そのもの**である。Dunbar 2020 は層(5/15/50/150)自体が**接触頻度で定義される**と書く。つまり Δ の重みも半減期も、**「エピソードを 1 本足す」以外の数を設計者が置く必要がない**。しかも認知設計書 §4 で **d=0.5 は既に決定済み**=新しい数ではない。
>
> **(ii) ただし「ゼロ」にはならない。残るのは 3 つ。** (a) **符号**(基底活性は符号を持たない。毎週喧嘩する相手も活性は高い)(b) **検索閾値 τ**(何本までが「辺」か。Zhao ら 2012 が ACT-R でやった唯一の先行では、**設計者が置いた数は τ 1 個だけ**で Dunbar 様の上限が出た)(c) **エピソードの粒度**(1 発話ブロック=1 本か、1 セッション=1 本か)。**5 個の数 → 2 個の定義**。しかも τ は A1/B3/B4/Dunbar 層に対して**較正できる**=指紋でなく較正パラメータに格下げできる。
>
> **(iii) ①(3 値尺度)は「未リサーチ」ではなかった——先行がある。しかも 8B に数値を書かせる側の危険は実測で出ている。** CitySim(Bougie & Watanabe 2025・**渋谷の POI 人気と群集密度を照合対象にしている**)は、会話後に **positive / neutral / negative の 3 分類**を取り出して affinity/trust/familiarity を更新する、と本文に明記している=**親案①と同型の先例**。一方、8B 級に 5 段階の点を書かせる側は悪い: 採点規準の並び順を変えただけで **Qwen3-8B は 46.22% の点が壊れ**、著者は「小さいためと思われる」と名指しする(Qwen3-32B は 28.56%・GPT-4o は 25% 未満)。→ **数値尺度は避ける。語のカテゴリ(3 値)にするか、もっと良いのは「符号をエンジンの ResultCode から取る」**(断る/すっぽかし/`PARTNER_NO_SHOW` は既に engine 側の事実。LLM の自己申告を通さない=CLAUDE.md §3「状態と集約はエンジン」と一致)。
>
> **(iv) 問 B には先行が無い。**「ラン前にペアを組ませて会話させ、その結果を初期関係網にした」LLM 社会シミュレーションは、**8 系統を当たって 1 本も見つからなかった**(§3-1 の表)。実態は 4 通りしかない——手書き散文(Generative Agents・25 体)/ LLM 生成+人手修正(Sotopia・90 ペア)/ 実データ取り込み+合成増殖(OASIS)/ 冷スタート(Learning to Make Friends・E₀=∅)。**AgentSociety は抄録に記述が無い**(空欄)。「ウォームアップ」という語を使う先行(LLM-SocioPol)はあるが、それは**活動量を定常にするための burn-in** であって関係網を作る目的ではない。つまり問 B は**先行のない新規案**である(新規であること自体は悪くない。ただし「先行がある」とは書けない)。
>
> **(v) 指紋の比較は、正直に言うと引き分けではなく「ウォームアップの勝ち、ただし条件つき」。** 「5 本を一様乱択」は次数分布をほぼ正則にする——Hamill & Gilbert 2009 が「ランダムグラフは実社会網の悪いモデル」と切って捨てた性質そのもの(同調性が解析的にゼロ・次数がほぼ揃う)。一方ウォームアップは「誰と誰を組ませるか」を設計者が決める、という指摘は正しい。**しかし本 repo には抜け道がある**: 組ませ方を **W17 のスケジュール + C9 の幾何(同一セル・距離 2 m)**に任せれば、ペアリング規則は**現実の建物・組織規模・町丁目・時刻**が決めるので、設計者は 0 個。これは Hamill & Gilbert の social circles を**架空の半径でなく実際の渋谷で**回すことに等しい。**条件**: 現行の会話成立率(410 セッション/日 = **0.0021 会話/体/日**)では、k=3 本の辺を作るのに**約 1,400 シミュ日**かかる=世界内ウォームアップは**いま不可能**。
>
> **(vi) 費用は障害にならない。ただし「どのウォームアップか」で 2 桁違う。** 強制ペアの 1 回きりウォームアップは、関係の種を持つ **292,745 体**[再計算]に k=3・4 ブロックで **1,756,470 呼 = 艦隊(78 応答/s)6.26 h = L4 の 0.44 日分**。5,000 体の先行実験なら **6.4 分**。一方、世界内ウォームアップは 1 シミュ日あたり **9.64 h**(c7-day-4 の実測 2,706,593 呼)。どちらも **I1「初期化予算(1 回限り・W1 の対象外)」**に載せる話であって L4 を食わない。

---

## §0 本答申が新しく足すもの / 既存で足りているもの

| 論点 | 既存 | 本答申 |
|---|---|---|
| Dunbar 層 5/15/50/150・重み 40/20/40 | 行動契約 §5(「Dunbar 2020 逐語・mechanism」と記載) | **§1-4 で原典を機械抽出して逐語照合 = 写し検査 PASS**(下の「写し検査」節) |
| 内層の年間入替 1〜4%/年 | パターン台帳 B3(Roy et al. 2022・親 PMC 確認済み) | **再調査しない**。§6 で照合先として再利用 |
| 会話グループサイズ 2 人 53.9% | パターン台帳 A1(強・holdout) | 再調査しない。§6 で照合先 |
| 交際・付き合い 10 分/日 | パターン台帳 A4(社会生活基本調査 R3・親確認済み) | 再調査しない。**§5 で「A4 を満たす会話量は L4 をほぼ使い切る」という算術だけ新しく出す** |
| 日本人の接触頻度の中央値 | v1 資産 `initial-relations-improvement` §8.2(**v1 のメモ=一次でない**) | **§3-3 で内閣官房 R5 概要 PDF を機械抽出して分布を復元**(v1 の 9.2% / 16.3% は正しかった) |
| 初期関係の 4 方式 | 同 §6.1(v1 のメモ) | **§3-1 で 8 系統を当たり直し、原典の逐語に差し替え。Sotopia/Concordia/CitySim/LLM-SocioPol は v1 に無い** |
| 記憶の U1(ACT-R 基底活性 d=0.5) | 認知設計書 §4(決定済み) | **§1-6 で「基底活性を社会関係に転用した先行」を特定**(Zhao et al. 2012 CogSci・PSU)。v2 にも v1 にも無かった |
| LLM-as-judge の系統誤差 | 人格答申 §3-2(Contreras 2026) | 参照のみ。**§2-2 で「8B の数値尺度」に特化した実測を足す**(Li et al. 2026・DASFAA) |

---

## §1 関係の強さを相互作用の履歴から導く先行(問 A ①②への外部証拠)

### 1-1 Granovetter 1973 の 4 要素 — 「時間量」が先頭で「情動」が 2 番目

- 出典: Granovetter, M. (1973) "The Strength of Weak Ties", *American Journal of Sociology* 78(6):1360–1380, DOI [10.1086/225469](https://doi.org/10.1086/225469)。**原典は未取得(有料)= 一次は Gilbert & Karahalios 2009 が引く逐語のみ**。
- 逐語(Gilbert & Karahalios 2009 p.211 の引用ブロック・私が PDF から機械抽出):
  > "The strength of a tie is a (probably linear) combination of the amount of time, the emotional intensity, the intimacy (mutual confiding), and the reciprocal services which characterize the tie."
- **本 repo にとっての意味**: 4 要素のうち **amount of time(時間量)は相互作用の履歴そのもの**、intimacy と reciprocal services も**行為の履歴**(打ち明けた/助けた)である。**設計者の数が要るのは emotional intensity(情動強度)だけ**——これが §1-7 の結論の骨格になる。

### 1-2 Gilbert & Karahalios 2009 — 70 超の変数を投げて、勝ったのは「最後に接触してからの日数」

- 出典: Gilbert, E. & Karahalios, K. (2009) "Predicting Tie Strength With Social Media", *CHI 2009*, pp.211–220, DOI [10.1145/1518701.1518736](https://doi.org/10.1145/1518701.1518736)。著者版 PDF([eegilbert.org](http://eegilbert.org/papers/chi09.tie.gilbert.pdf)は接続失敗)・**実読 = [UMBC ミラー PDF](https://userpages.umbc.edu/~skane/classes/is760/fall2011/c3/PredictTieStrength.pdf) を pymupdf で本文抽出**。
- 標本: **35 名の参加者 × 2,184 の友人関係**。逐語: "Table 1. Thirty-two of over seventy variables used to predict tie strength, collected for each of the 2,184 friendships in our dataset."
- 性能(逐語): "On the first tie strength question, How strong is your relationship with this person?, the model fits the data very well: **Adj. R2 = 0.534, p < 0.001**. It achieves a **Mean Absolute Error of 0.0994** on a continuous 0–1 scale"
- **Table 3(上位 15 変数の標準化 β・私が PDF から抽出)**:

| 変数 | β | F | p |
|---|---:|---:|---|
| **Days since last communication** | **−0.76** | 453 | <0.001 |
| **Days since first communication** | **0.755** | 7.55 | <0.001 |
| Intimacy × Structural | 0.4 | 12.37 | <0.001 |
| Wall words exchanged | 0.299 | 11.51 | <0.001 |
| Mean strength of mutual friends | 0.257 | 188.2 | <0.001 |
| Educational difference | −0.22 | 29.72 | <0.001 |
| Structural × Structural | 0.195 | 12.41 | <0.001 |
| Reciprocal Serv. × Reciprocal Serv. | −0.19 | 14.4 | <0.001 |
| Participant-initiated wall posts | 0.146 | 119.7 | <0.001 |
| Inbox thread depth | −0.14 | 1.09 | 0.29 |
| Participant's number of friends | −0.14 | 30.34 | <0.001 |
| **Inbox positive emotion words** | **0.135** | 3.64 | **0.05** |
| Social Distance × Structural | 0.13 | 34 | <0.001 |
| Participant's number of apps | −0.12 | 2.32 | 0.12 |
| Wall intimacy words | 0.111 | 18.15 | <0.001 |

- 逐語: "The utility distribution of the predictive variables forms a power-law distribution: **with only these fifteen variables, the model has over half of the information it needs to predict tie strength.**"
- **含意 1(最重要)**: **recency(最終接触からの日数)と duration(初回接触からの日数)が 1 位・2 位**。ACT-R 基底活性 `A = ln Σ_j (Δt_j+1)^(−d)` は、まさに「各エピソードの経過時間を冪で重みづけて足す」量であり、**recency(最新の項が支配)と frequency と duration(古い項の裾)を 1 本の式で同時に表す**。親案②の「会話 +1・同席 +0.5・約束成立 +2」は、この式の**Σ に入るエピソードを数える**ことで代替できる。
- **含意 2**: **情動語(positive emotion words)は 15 位中 12 位・β=0.135・p=0.05**。すなわち**好悪はゼロではないが、接触の履歴に比べて桁が小さい**。親案①の 3 値尺度に大きな重みを与えるのは、この実証に照らして**過剰**。
- **著者自身の注記(重要な限界)**: "The two Days since variables have such high coefficients due to friends that never communicated via Facebook. Those observations were assigned outlying values"。**一度も通信していないペアに外れ値を割り当てたせいで β が膨らんでいる**ことを著者が明示している。→ **「β=−0.76」は「recency が全てを決める」証拠ではなく、「接触が 1 回でもあるか / 無いか」の効果が大きいという証拠**として引くのが正しい(§「親確認の要請」#1)。
- 批判: 2009 年の Facebook・大学コミュニティの標本(著者も "that may reflect the university community from which we sampled participants" と注記)。日本・対面には外挿していない。

### 1-3 Roberts & Dunbar 2015 — 「最後に会ってからの日数」が親密さの**変化**を予測する(縦断)

- 出典: Roberts, S. G. B. & Dunbar, R. I. M. (2015) "Managing Relationship Decay: Network, Gender, and Contextual Effects", *Human Nature* 26(4):426–450, DOI [10.1007/s12110-015-9242-7](https://doi.org/10.1007/s12110-015-9242-7)・全文 [PMC4626528](https://pmc.ncbi.nlm.nih.gov/articles/PMC4626528/)(**一次確認 = WebFetch の読み取り器経由。私自身の機械抽出ではない**)。
- 数値(読み取り器が返した値。**親の再確認対象**):
  - Model 8: **接触頻度の変化(最終接触からの日数)が親密さの変化を予測 b = −0.71**(SE 0.17・95% CI −1.03〜−0.38・p<0.001)。性別交互作用 0.51(p<.05)=女性で強く男性で有意でない。
  - 友人との**平均「最終接触からの日数」28.41(T1)→ 69.31(T2)→ 128.78(T3)**(18 か月)。
  - 家族は **+0.27**(t=7.28・p<.001)と**上がり**、友人は **−0.62**(t=−15.23・p<.001)と**下がる**。
  - 内層に留まった割合: **kin 102/145 = 70.3% / friends 69/142 = 48.6%**。
  - 逐語: "even close friendships require active maintenance, whereas family relationships are more resistant to decay" / "To prevent this decay requires time-consuming maintenance behaviors, principally communication and joint activities"。
- **含意**: 半減期という「1 個の定数」を全種別に当てるのは実証に反する。**家族(世帯辺)と友人辺で減衰が逆向き**。基底活性方式なら、世帯辺は同居による**毎日のエピソード供給**で自動的に維持されるので、**種別ごとの半減期を置かずに家族/友人の差が出る**(=機構で出る。expedient で置かない)。

### 1-4 Dunbar 2020 — 層は「接触頻度」で定義される。40%/20% の写し検査も通った

- 出典: Dunbar, R. I. M. (2020) "Structure and function in human and primate social networks: implications for diffusion, network stability and health", *Proc. R. Soc. A* 476:20200446, DOI [10.1098/rspa.2020.0446](https://doi.org/10.1098/rspa.2020.0446)・CC BY 4.0・**実読(ORA 版 PDF を pymupdf で抽出)**。
- 逐語(層と頻度):
  > "This gives the network a layered structure, where individual alters in a given layer are contacted with more or less similar frequency and there is a sharp drop-off in contact frequencies to the next layer."
  > "Moreover, when counted cumulatively, they have a very distinct scaling ratio: **each layer is approximately three times the size of the layer immediately inside it** (figure 2)."
  > "**Each layer seems to correspond to a very specific frequency of interaction** (figure 3), and these frequencies are remarkably consistent across media [66]"
- 図 2 の層(逐語の並び): `EGO 1.5 intimates / 5 best friends / 15 good friends / 50 friends / 150 acquaintances / 500 known names / 1500 / 5000 = known faces`。
- 図 3 の説明(逐語): "Frequency per day with which people contacted individual members of each layer in their social network. Sample: **complete social networks of 251 UK and Belgian women**." 縦軸の目盛りは 0〜0.4/日(最内層 5 が **≈0.4 回/日**・以降単調減)。
- **写し検査(CLAUDE.md §5)**: 行動契約 §5 の「**内側 5 人 40%・次の 10 人 20%・残り 40%**(Dunbar 2020 逐語・mechanism)」を原典に当てた。原典逐語:
  > "Approximately **40% of all social effort** (whether indexed as the frequency or duration of interaction) is directed to the **five individuals in the closest layer**, with another **20% devoted to the remaining 10 members of the second layer**. Thus, **60% of social time is devoted to just 15 people**."
  → **一致。写し検査 PASS**。
- **写し注意(1 件)**: 行動契約 §5 の「**平時入替 1%/年**(mechanism)」。原典の該当文は
  > "A similar effect will occur when there is a terminal breakdown in a relationship. These seem to occur with a frequency of **about 1% of relationships per year**"
  = これは**関係の決裂(terminal breakdown)の発生率**であって「入替率」ではない。パターン台帳 B3 の「内層の年間入替 1〜4%/年」(Roy 2022)とは**別の量**。行動契約の語は「入替」なので、**定義を「決裂 1%/年 ⊂ 入替 1〜4%/年」に直すか、出典を B3 に付け替えるべき**(親判断)。
- **本答申が最も重く見る 1 文(ウォームアップの限界)**:
  > "By contrast, multilevel social structures of the kind found in many primates, and especially those with the specific layer sizes of human social networks, were **extremely rare (accounting for less than 1% of runs)**."
  (3,000 回超の ABM ラン・適応度関数の重みを系統的に振った結果)。→ **「相互作用に任せれば Dunbar 層が自ずと出る」とは期待できない**。層が出るのは「社会時間への高投資・選好的相互作用戦略・高い死亡リスク・急な繁殖差」が同時に揃うときだけ、と原典は書く。**ウォームアップを採るなら、層構造は「出るはず」でなく「出るか測る」対象**。

### 1-5 Saramäki et al. 2014 — 入れ替わるのは相手、残るのは**形**

- 出典: Saramäki, J., Leicht, E. A., López, E., Roberts, S. G. B., Reed-Tsochas, F. & Dunbar, R. I. M. (2014) "Persistence of social signatures in human communication", *PNAS* 111(3):942–947, DOI [10.1073/pnas.1308540110](https://doi.org/10.1073/pnas.1308540110)。**実読 = arXiv 版 [1204.5602v2](https://arxiv.org/abs/1204.5602) を pymupdf で抽出**(PNAS 本体は 403・Europe PMC は 403)。
- 標本(逐語): "tracked changes in the ego networks of **24 students over 18 months** as they made the transition from school to university or work"。18 か月を 6 か月 × 3 区間(I1/I2/I3)に分割。
- 結果(逐語):
  > "for a given ego, these social signatures tend to persist over time, despite considerable turnover in the identity of alters in the ego network. Thus as new network members are added, some old network members are either replaced or receive fewer calls, **preserving the overall distribution of calls across network members**."
  > "On average, for each ego, **82% ± 12%** of the distances to others d_ref were greater than d_self."
  > 平均: "⟨d_self⟩ = 0.036 ± 0.014 while the average distance to other egos is ⟨d_ref⟩ = 0.086 ± 0.055"(Jensen–Shannon 距離)。
- **入替の大きさ(フロア併記)**: 逐語 "⟨J(I1, I2)⟩ = **0.22 ± 0.09** and ⟨J(I2, I3)⟩ = **0.27 ± 0.09**"(全ネットワークの Jaccard)。上位 20 位に限っても "⟨J(I1, I2)⟩ = **0.36 ± 0.13**"。さらに "**even of the highest-ranked alters, only 42% retain their top rank from interval I1 to I2, and 54% from I2 to I3**"。
  - **注意(フロア)**: Dunbar 2020 は同じ研究を「18 か月で約 40% の入替」と要約しているが、**Jaccard 0.22 は 40% よりはるかに大きい入替**を意味する。**二次要約の「40%」でなく原典の Jaccard を引くこと**(行動契約 §5 の「激変時 18 か月で 40%」は Dunbar 2020 の要約経由)。
- **含意(C10 の合格線の形を変える)**: 検証すべきは「誰と誰が辺を持つか」ではなく「**注意の配分の形(順位 - 割合曲線)が個体ごとに保たれるか**」。これは 40 万体でも測れる量で、**初期網の与え方に依存しにくい**(=holdout に向く)。

### 1-6 Zhao et al. 2012(CogSci) — ACT-R 基底活性を社会関係に転用した唯一の先行

- 出典: Zhao, C., Kaulakis, R., Morgan, J. H., Hiam, J. W. & Ritter, F. E. (2012) "Modeling a Cognitively Limited Network in an Agent-Based Simulation", *Proceedings of the 34th Annual Meeting of the Cognitive Science Society*, pp.2603–2608。**実読 = [eScholarship 85t2040s](https://escholarship.org/uc/item/85t2040s) の PDF を pymupdf で抽出**。後続: Zhao et al. (2015) *Computational and Mathematical Organization Theory* 「Building social networks out of cognitive blocks」(**検索要約のみ**)。
- 逐語(抄録):
  > "We investigate how cognitive capacity limits the number of group relations that a person can maintain. The simulation experiment's results using ACT-R and its memory equations replicated **an effect similar to that of Dunbar's (1998) number**"
- 機構(逐語):
  > "Examining different **memory activation thresholds for links between agents** enables us to model not only the effects of memory retention on network formation but also provides us a means of representing **differences in the modeled social ties' quality**, as Dunbar defines this term"
  > "In other words, **higher quality relationships are associated with greater cognitive investment and higher memory strength**."
  > "According to the ACT-R theory, the activation threshold represents a memory limitation, meaning that **memory chunks with an activation value lower than the threshold cannot be retrieved**. ... **multiple exposures are required to remember another agent**."
- 規模と結果: 40 体・4 ラン・18 標本時点 → 2,880 個の自我中心網。**閾値 0.0 の網は 800 リンクで平衡**(=1 体あたり 20 本)、**閾値なしの網は 1,336 リンク**(理論上限 40×39=1,560)。
- 決定的な 1 文(ウォームアップの組ませ方の議論に直結):
  > "our results also imply, at least for our world, that **navigation strategies and environmental complexity do not significantly influence the number of friends that a person can maintain in memory (Dunbar's number)**, as the average number of relations were same for both networks. They do, however, suggest the **ecological factors significantly contribute to the degree of localization**"
- 著者の残課題(そのまま本 repo の課題):
  > "We suspect that one possible way to adjust the final size of the network is by changing the cognitive parameters in ACT-R, for instance **adjusting memory decay speed or base level learning activation**."
  > "Activations are not portable or easily interpretable in social terms. ... This normalization recasts activations as statements about the **'probability of recall' within a particular timeframe**."
- **含意**: (a) **「辺の強さ = 記憶チャンクの基底活性」は先例がある**。(b) **設計者が置いた数は検索閾値 τ 1 個だけ**で、Δ の重みも半減期も置いていない(1 回の遭遇 = 1 回のリハーサル)。(c) **地図と経路(=誰と誰を組ませるか)は上限数を変えず、局在性だけ変える**——これは §4 の「ウォームアップでも組ませ方が指紋になる」という懸念に対する**部分的な反証**。(d) 生の活性値は解釈できないので、**「想起確率」に正規化して持つ**べき(6 B の `rel_strength: uint8` は「活性の量子化」でなく「想起確率の量子化」にすべき)。
- 批判・限界: 40 体・机上の格子世界・査読は CogSci の短報。Dunbar 数の「再現」は 20 本/体であって 150 ではない。**τ の値が結果を決めている**(0.0 vs なしで 800 vs 1,336)ので、τ は感度試験の必須対象。

### 1-7 結論 — 何が消せて、何が残るか

| 親案(agenda §5) | 記憶の基底活性で置き換えられるか | 根拠 |
|---|---|---|
| ② 会話 +1 | **消せる**(会話セッション完了 = エピソード 1 本) | Gilbert β=−0.76/0.755・Zhao 2012(1 遭遇 = 1 リハーサル) |
| ② 同席 +0.5 | **消せる**(同席もエピソード 1 本。ただし**別種別のエピソード**として記録) | 同上。重み 0.5 の根拠はどこにも無い |
| ② 約束成立 +2 | **消せる**(約束成立はエピソード 1 本+`Promise` 表側の事実) | 同上 |
| ② 断る −1 / すっぽかし −2 | **半分消せる**。回数は活性に入る。**符号は別欄**(下記 a) | Granovetter の 4 要素で情動強度は独立軸 |
| ② 半減期 30 日 | **消せる**。既決の **d=0.5**(認知設計書 §4)がそのまま使える | ACT-R 冪法則。指数減衰を採らない決定は既にある |
| ① 3 値尺度(−1/0/+1) | **残る**(ただし §2 で「LLM に書かせない」形に置換可能) | 基底活性は符号を持たない |
| ③ 組織内 5 本乱択 | **残る**(§3〜§4 で扱う) | — |
| **(新規)検索閾値 τ** | **新しく要る。ただし較正可能** | Zhao 2012。A1/B3/B4/Dunbar 図 3 に対して較正 |
| **(新規)エピソードの粒度** | **新しく要る(定義であって数ではない)** | 本 repo の会話は 1 呼 = 1 発話ブロック |

**数の勘定: 設計者が置く数 5 個(3 値の刻み + Δ 4 種 + 半減期)→ 2 個(τ・粒度の定義)、うち τ は較正対象。** ユーザーの問 A は、外部証拠に照らして**支持される**。

**ユーザーの後半「あるいはシミュレーションを回す中で経験から設定してもよいのでは」について**: これは τ に対してだけ成り立つ。τ を「毎晩の内省(T2)で、その体が実際に何人を想起できたかから自己調整する」形は魅力的だが、**先行が見つからなかった**(Zhao 2012 は τ を固定)。**自己調整する τ は未リサーチ(expedient)**であり、C10 では固定 + 感度腕を推奨する(§6)。

---

## §2 好悪(valence)を語から取る — ① をどう置くか

### 2-1 先例はある: CitySim は「positive / neutral / negative」の 3 分類を使っている

- 出典: Bougie, N. & Watanabe, N. (2025) "CitySim: Modeling Urban Behaviors and City Dynamics with Large-Scale LLM-Driven Agent Simulation", arXiv:[2506.21805](https://arxiv.org/abs/2506.21805)。**実読(PDF を pymupdf で抽出)**。
- 逐語(§3.3 Social Behaviors):
  > "The foundation of our social module is a weighted social network where each edge encodes an agent's evolving social beliefs about others. Each agent u maintains a social belief vector b_{u,v} for every contact v, capturing dimensions: ∈ {**affinity, trust, familiarity**}. These beliefs are **initialized at simulation start based on demographic similarity and relationships**, then updated continuously."
  > "After an interaction, b_{u,v} is updated using **observed outcome (positive, neutral, negative)** for each dimension."
  > (付録 B)"Following each interaction, beliefs are updated by evaluating the sentiment and outcome of the exchange: **positive, neutral, or negative signals are extracted from the conversation** and used to incrementally adjust the affinity, trust, and familiarity scores between agents."
- 相手選択(逐語): "Agent u selects a conversation partner v according to their current belief score, with probability: p_v = b_{u,v} / Σ_{v'∈V} b_{u,v'}"。
- 規模と照合先(逐語): "the number of agents set to **1,000 located in Tokyo metropolitan area**"・GPT-4o-mini・AgentSociety 基盤。"we evaluate CitySim's as a predictive tool for real-world **POI popularity in Shibuya (Tokyo, Japan)**"・"CitySim's ability to reproduce real-world patterns of pedestrian concentration across **Shibuya (Japan)**"。
- **含意**: 親案①(3 値)は**未リサーチではない**。同じ渋谷を狙う直近の先行が**同じ 3 分類**を採っている。ただし CitySim は **b を 3 次元(affinity/trust/familiarity)に分けている**点が親案より細かく、**「1 回の更新量」は論文に数値が無い**("incrementally adjust" としか書かない)=**CitySim 自身が Δ を空欄にしている**。
- 批判: CitySim は GPT-4o-mini(8B ではない)・1,000 体・POI 人気の Spearman と群集密度の図以外に社会網の検証がない(Dunbar 層も会話グループサイズも照合していない)。**「3 値でよい」の根拠にはなるが「3 値で正しく動く」の根拠にはならない**。

### 2-2 8B に**数値**を書かせる側の危険 — 採点規準を並べ替えただけで 46% が壊れる

- 出典: Li, Q., Dou, S., Shao, K., Chen, C. & Hu, H. "Evaluating Scoring Bias in LLM-as-a-Judge", arXiv:[2506.22316](https://arxiv.org/abs/2506.22316)(v4・2026-02-03・**DASFAA 2026 採択**・CC BY 4.0)。**実読(PDF を pymupdf で抽出)**。
- 審査モデル(逐語): "They are **GPT-4o, DeepSeek-V3-671B, Qwen3-32B, Qwen3-8B, and Mistral-Small-24B-Instruct-2501**."
- 逐語(核心):
  > "An exception is **Qwen3-8B, whose score distribution is more significantly influenced by biases, possibly due to its small size**."
  > "Qwen3-8B, for example, suffers a **46.22% FR** on BiGGen Bench under a simple rubric reordering. The larger Qwen3-32B is far more stable (**28.56% FR**) under the same perturbation, confirming the link to model scale."
  (FR = flip rate。Qwen3-8B の MAD は 0.5296 = 5 段階で平均 0.53 点ずれる)
- 併せて: **中心化傾向**の逐語 "Under unbiased conditions, DeepSeek-V3-671B assigns a score of 5 to more than half of the instruction-response pairs. Compared to the human scoring distribution, Mistral-Small-24B-Instruct has a stronger tendency to assign a score of 4"。
- 尺度の刻み: Li, W. et al. (2026) "Grading Scale Impact on LLM-as-a-Judge: Human-LLM Alignment Is Highest on 0-5 Grading Scale", arXiv:[2601.03444](https://arxiv.org/abs/2601.03444)(**抄録のみ**)。逐語: "Aggregated over tasks, the grading scale of **0-5 yields the strongest human-LLM alignment**."
  - **注意**: これは「人間との一致」が最良の刻みであって「3 値 vs 5 値」の直接比較ではない。**8B について 3 値と 5 値を直接比べた研究は見つからなかった(空欄)**。親案「5 値は 8B の書式縮退が増える」は、上の 46.22% と整合はするが、**直接の一次証拠は無い**。

### 2-3 自己申告と LLM 審査は「人間が共有しない分散」を共有する(既存答申の再掲・再調査せず)

- 人格答申 §3-2 より(Contreras 2026・arXiv:[2606.09843](https://arxiv.org/abs/2606.09843)・サブ実読・親未確認): Responsiveness では**自己申告は LLM 審査と r=.53 で相関したが人間とは r=.04**。単一潜在構成の棄却 p=.007。
- **本件への含意**: 「会話後に LLM に気分を書かせ、それを別の LLM(または同じ LLM の T2 抽出)で検証する」ループは、**この共有分散に汚染される**。R9′(ii) の「ラン後のオフライン抽出(T2・温度 0)が会話記録から感情の印を付ける」は、**まさにこの形**。→ **T2 抽出の結果は、エンジン側の客観量(会話の再来率・同席の継続・断られた回数)と突き合わせて初めて使える**。

### 2-4 本 repo の実測 — 自由欄には「欄名」が写る

- `docs/bench/c8/ablation/ab7_s1_parent_report.md`(親報告・第227)より逐語:
  > "**「行動」と書く体が 90**(欄名の写し)= few-shot なしの自由欄で起きる書式縮退(第 W17 の「例示写し」と同型)。"
  表の行: `| **行動**(欄名の写し・未定義) | 90・90 体 | → 待機 |`
- メモリ `fewshot-time-anchoring-8b`: W17 v2 第 1 回で**段2 system の固定例示の時刻を 47% の体が写した**。
- **含意**: 「関係: +1/0/−1」という欄を足せば、**(a) 欄名「関係」をそのまま書く体**と **(b) テンプレに書いた例(たとえば「+1」)を写す体**が出る。**最頻値が例示値と一致していないかを、最初の受入で必ず確認する**(メモリの規律)。

### 2-5 結論 — 符号は要るが、LLM に数値で書かせる必要はない

3 案。**推奨は C 案**。

| 案 | 形 | 設計者の数 | 8B のリスク | 呼数 |
|---|---|---|---|---|
| A | 会話応答に `関係: +1/0/−1` 欄(親案①) | 刻み 3・欄の存在 | **高**(欄名写し・例示写し・46% FR と同型) | 0 増 |
| B | 会話応答に `気分: <語>` 欄 → parser が語彙表で 3 分類 | 語彙表の写像(= 語彙政策・D-73 と同じ台帳行) | 中(語は書式縮退しにくい・AB7 の open 腕は**書式が良かった**=厳密 2 行 93%) | 0 増 |
| **C(推奨)** | **符号は LLM から取らない。エンジンの `ResultCode` と行動語から取る**: 断る/`REFUSED` = 負・`PARTNER_NO_SHOW` = 負・手伝い/会話成立/約束成立 = 正・同席のみ = 0 | **0**(既存の 20 値 ResultCode と 24 語彙をそのまま使う) | **無**(LLM の自己申告を通さない) | 0 増 |

- **C 案の根拠**: (a) CLAUDE.md §3「状態と集約はエンジン、意思決定と発話だけ LLM」に正確に一致。(b) Gilbert の実証で情動語の β は 12 位・0.135 と小さく、**行為(断った/助けた)の方が Granovetter の reciprocal services として上位**。(c) Contreras 2026 の共有分散の罠を構造的に避ける。(d) 現状 `断る` は `_apply_record_only`・`手伝い` は必ず `BAD_TARGET` なので、**C10 で両方を動かすこと自体が既定のタスク**(R8)。
- **C 案の弱点(正直に)**: 「会話の中身が険悪だった」は取れない。R9′ の「関係を会話・感情・状態から取り出す抽出エンジン」というユーザーの案の一部を落とす。→ **B 案を C 案の上に**任意で重ねられる形にし(気分語は辺に**書くが強さには効かせない**・診断用)、**5,000 体腕で「気分語を効かせた腕」と「効かせない腕」の差を測る**(§6-iii の腕 4)。

---

## §3 ラン前のウォームアップで初期関係を作る先行(問 B)

### 3-1 (a) LLM エージェント社会シミュレーションの初期関係網 — 8 系統の実態

**結論を先に: 「ラン前に相互作用させて関係網を作った」例は 1 本も見つからなかった。**

| 系統 | 体数 | 初期の関係網の与え方 | 逐語/根拠 | 一次確認 |
|---|---:|---|---|---|
| **Generative Agents**(Park et al. 2023・arXiv:[2304.03442](https://arxiv.org/abs/2304.03442)) | 25 | **手書き散文**。1 体 1 段落を著者が書き、セミコロン区切りの各句を初期記憶に入れる | "We authored one paragraph of natural language description to depict each agent's identity" / "Each semicolon-delimited phrase is entered into the agent's initial memory as memories at the start of the simulation." / 網密度 **0.167 → 0.74**(2 ゲーム日) | **B**(HTML・WebFetch 読み取り器) |
| **Sotopia**(Zhou et al. ICLR 2024・arXiv:[2310.11667](https://arxiv.org/abs/2310.11667)) | 40 キャラ | **GPT-4 が生成し人手で修正**。5 型(family/friend/romantic/acquaintance/stranger)・**90 ペア**。関係型はプロフィール可視範囲も決める | "we randomly sampled 90 pairs of characters and prompted GPT-4 with their relationships" / 内訳 family 31・friends 30・romantic 30・acquaintance 29・stranger 30 | **C**(検索要約) |
| **Concordia**(DeepMind・arXiv:[2312.03664](https://arxiv.org/abs/2312.03664)) | 少数 | **型を持たない**。`formative_memories_initializer` が `shared_memories` と `player_specific_context`(自由文)から記憶を生成 | コンポーネント README: "This powerful component runs at the beginning of a simulation to generate rich backstories and formative memories" | **C**(検索要約) |
| **OASIS**(Yang et al.・arXiv:[2411.11581](https://arxiv.org/abs/2411.11581)) | 最大 100 万 | **実データ種 + 合成増殖**。Twitter15/16 の 198 事例(1 事例 100〜700 ユーザ)の実フォロー関係を取り込み、196 実ユーザから scale-free 性を保って 100 万まで生成 | Appendix E.2: "conventional data scraping methods fail to guarantee a realistic relationship network" / "preserving the scale-free nature of social networks" | **C**(検索要約) |
| **AgentSociety**(Piao et al.・arXiv:[2502.08691](https://arxiv.org/abs/2502.08691)) | 1 万超 | **抄録に記述なし = 空欄**(v1 資産は「ユーザーが与えると明言」と記録するが、本調査では抄録までしか確認できず) | 抄録: "over 10k agents" / "5 million interactions" | **空欄** |
| **CitySim**(Bougie & Watanabe 2025) | 1,000 | **人口統計的類似(homophily)+ 既存関係**で belief を初期化 | §3.3: "initialized at simulation start based on **demographic similarity and relationships**" | **A**(私が抽出) |
| **Learning to Make Friends**(Schneider, Tian & Rizoiu 2025・arXiv:[2510.19299](https://arxiv.org/abs/2510.19299)) | 小規模 | **冷スタート**。関係網を作ること自体が研究対象 | "At time t = 0, we observe the social network G0 = (V, E0, A0) with **E0 = ∅**, indicating that there are no edges and no prior knowledge among users in V" / 直前に "**a pre-survey assessment**"(=性格の検証であって関係の構築ではない) | **A**(私が抽出) |
| **LLM-SocioPol**(arXiv:[2510.26494](https://arxiv.org/abs/2510.26494)) | — | **warmup はあるが目的が違う**。活動量と content flow を定常化させる古典的 burn-in | "The early phase of the simulation includes a **warmup period**, during which agents' activity patterns and content flows stabilize before experimental treatments are introduced." | **C**(検索要約) |

**Learning to Make Friends の更新式(親案②との比較に重要・私が抽出した逐語)**:
> "the tie strength is updated using a **gated update rule** that differentiates between active and passive rounds. On active rounds, the tie is strengthened based on a scalar evidence score e_t(u→v) ∈ [0,1] ... On passive rounds—when no directed interaction from u to v occurs—the tie strength decays."
> `[A_{t+1}]_uv := [A_t]_uv + min(Δmax, (1−[A_t]_uv)[e_t(u→v) − ξ]_+)  if ζ_t = 1 ; (1−δ)·[A_t]_uv  if ζ_t = 0`
> "where **ξ ∈ [0,1) is a minimum-evidence threshold, Δmax ≥ 0 caps the per-round increase, δ ∈ [0,1) controls decay** ... To interpret δ, one can **parameterize it via a half-life h such that δ = 1 − 2^{−1/h}**."

→ **2025 年の最先端でも、辺の更新は設計者の数 3 個(ξ・Δmax・δ)+ 半減期 h で書かれている**。親案②は分野の標準であって異常ではない。**ただしそれは「消せない」ことの証明ではない**——Zhao 2012(§1-6)が 0 個(τ のみ)で回している。

### 3-2 (b) ABM の社会ネットワーク生成と burn-in の作法

- **Hamill & Gilbert 2009 "Social Circles"**, *JASSS* 12(2):3, [jasss.org/12/2/3.html](https://www.jasss.org/12/2/3.html)(**B**・WebFetch 読み取り器・逐語は 125 字制限内)。
  - 抄録冒頭(逐語): "**None of the standard network models fit well with sociological observations of real social networks.**"
  - ランダムグラフ(逐語): "**the assortativity index of a random graph can be shown analytically to be zero**"・次数がほぼ揃う。
  - small-world(逐語): "**the small-world model is not in general expected to be a very good model of real networks, including social networks**"。
  - scale-free(逐語): "**preferential attachment does not in general apply to social networks**"(人は誰が well-connected かを知らない)。
  - 機構: 各体に **social reach (sr)** を与え、**互いの reach 内にあるペアだけが辺を張る**(逐語: "Agents are only permitted to link with agents who can reciprocate; in other words, others whose reach includes ego.")。単一 reach 版の設計者パラメータは(逐語)"**the only parameters being population density and the size of the social reach**"。
  - **本 repo への含意(§4 の核心)**: Social Circles は**空間モデル**である。本 repo は **C9 で連続位置・距離 2 m・セルを持っている**ので、`social reach` を架空の半径で置く必要がない——**実際の建物・組織・学校・町丁目・W17 の時刻**が reach を決める。すなわち **Social Circles を「渋谷の実測の上で」回す**のが、本件のウォームアップの正体になる。
  - 後続: Applied Network Science (2025) "Tunable network properties with Hamill and Gilbert's Social Circles generator", DOI [10.1007/s41109-025-00744-5](https://doi.org/10.1007/s41109-025-00744-5)(**C**)——reach が長いほど密で経路が短く同調性が低い、と系統的に報告。
- **Homophily**: McPherson, M., Smith-Lovin, L. & Cook, J. M. (2001) "Birds of a Feather: Homophily in Social Networks", *Annual Review of Sociology* 27:415–444, DOI [10.1146/annurev.soc.27.1.415](https://doi.org/10.1146/annurev.soc.27.1.415)(**C**・検索要約)。強さの順(要約): 人種・民族 > 年齢 > 宗教 > 学歴 > 職業 > 性別。概念: **baseline homophily**(母集団構成から期待される分)と **inbreeding homophily**(それを超える分)。
  - **含意**: W16 の組織・学校・町丁目で組ませれば **baseline homophily はデータが与える**。**inbreeding homophily(選好)を設計者が足すと指紋になる**。→ **足さない**。測るだけ。
- **Propinquity**: Festinger, Schachter & Back (1950) *Social Pressures in Informal Groups*(**原典未取得**)。パターン台帳 B1「近接性による友人形成(隣室 41%)」に既に載っている(**再調査しない**)。
- **burn-in の作法**(**C**・検索要約。分野の定番):
  - STRESS 報告ガイドライン(Monks et al. 2018, *Journal of Simulation*, DOI [10.1080/17477778.2018.1442155](https://doi.org/10.1080/17477778.2018.1442155)): ABM は **warm-up 期間・warm-up 解析手順(Welch 法 / MSER-5)・初期条件・初期エージェント数と属性**を報告すること。
  - 「事前に burn-in を固定するな」(MultiVeStA・arXiv:[2102.05405](https://arxiv.org/abs/2102.05405)): 自動手続きで決めないと推定にバイアスが乗る。
  - 判定法: Welch 図示法・MSER-5・Schruben–Singh–Tierney 検定・batch means・CV 収束。**全出力変数の最大安定点 + 余裕**を取る。
  - **本 repo への含意**: ウォームアップを入れるなら、**「何本の会話で止めるか」を先に決め打ちしてはいけない**。**辺の分布(次数・強さ)が定常になるまで**を判定基準にする。これは既存の CV 収束の規律(`stats__lorscheid2012_replication-doe` ほか)と同じ道具で書ける。

### 3-3 (c) 現実アンカー — 日本の接触頻度・出会い経路・Dunbar 層

**(1) 対面接触の頻度分布(新規・私が PDF から復元)**

- 出典: 内閣官房孤独・孤立対策担当室「人々のつながりに関する基礎調査(令和5年) 調査結果の概要」令和6年3月、[cao.go.jp/kodoku_koritsu/.../r5/pdf/tyosakekka_gaiyo.pdf](https://www.cao.go.jp/kodoku_koritsu/torikumi/zenkokuchousa/r5/pdf/tyosakekka_gaiyo.pdf)。**実読(pymupdf)**。統計法に基づく一般統計調査。
- 標本(逐語): 「調査対象:全国の満16歳以上の個人」「調査対象者数:20,000人(住民基本台帳を母集団とした無作為抽出法により選定)」・**回答者 n=11,141**・層化2段抽出。
- **図1-25 の n から復元した「同居していない家族や友人たちと『直接会って話す』頻度」の分布**[再計算・n を 11,141 で割った]:

| 頻度 | n | 割合 | 累積 |
|---|---:|---:|---:|
| 週4〜5回以上 | 1,812 | **16.3%** | 16.3% |
| 週2〜3回程度 | 1,490 | 13.4% | 29.7% |
| 週1回程度 | 1,559 | 14.0% | 43.7% |
| 2週間に1回程度 | 1,129 | 10.1% | **53.8%(中央値はここ)** |
| 月1回程度 | 1,688 | 15.2% | 68.9% |
| 月1回未満 | 1,791 | 16.1% | 85.0% |
| **全くない** | 1,029 | **9.2%** | 94.2% |
| (不詳・合計外) | 643 | 5.8% | 100% |

- **v1 資産の照合**: v1 `initial-relations-improvement` §8.2 の「全くない 9.2%・週4-5回以上 16.3%・中央値は月1回〜2週に1回」は**一致した**(v1 のメモは正しかった)。
- 関連(同じ調査の 4 年分考察・[r6/pdf/kosatsu_r7.pdf](https://www.cao.go.jp/kodoku_koritsu/torikumi/zenkokuchousa/r6/pdf/kosatsu_r7.pdf)・**C**): 「他者との交流頻度が週１回程度(月8.6 回)以下を孤立状態とした場合、回答者の１割弱が該当」(2021:9.6% / 2022:8.9% / 2023:9.5% / 2024:9.2%)。
- **含意**: これは **C10 のウォームアップにも定常ランにも使える現実アンカー**で、いま `registry.yaml`(37 本)に関係・会話のアンカーが 1 本も無い穴を埋められる。ただし**渋谷の来街者には当たらない**(全国・16 歳以上・「同居していない家族や友人」限定)。

**(2) 出会いの経路(日本)**

- 出典: 国立社会保障・人口問題研究所「第16回出生動向基本調査(2021年)結果の概要」図表5-3、[ipss.go.jp/ps-doukou/j/doukou16/JNFS16gaiyo.pdf](https://www.ipss.go.jp/ps-doukou/j/doukou16/JNFS16gaiyo.pdf)。**PDF は暗号化されていたが pymupdf で本文抽出に成功。ただし図表5-3 の数値は図中に焼かれており本文テキストに無い = 25.9%(友人・兄弟姉妹を通じて)と 21.4%(職場や仕事で)は検索要約経由で未確認(空欄)**。
- **本文から確認できた逐語**(私が抽出): 「恋人や配偶者と知り合う場として**友人や職場を経由したものが減り**、SNS やマッチングアプリなど…2018 年後半から2021 年前半に結婚した夫婦の **13.6%** が、こうしたインターネットを使ったサービスを介して相手と知り合った(図表2-4、図表5-3)」。独身者調査は「男性11.9%、女性17.9%」。
- **含意**: 職場と友人経由が 2 大経路であることは本文が支持する(「友人や職場を経由したもの」と一括して書く)。**W16 の組織辺と「友人の友人」(三者閉包・台帳 B2)を初期網の 2 本柱にする根拠になる**。ネット経由 13.6% は v2 に SNS が無いので**再現できない部分として宣言**すべき(歪む場所)。

**(3) Dunbar 層の一次**

- §1-4 の Dunbar 2020(実読)で、層 1.5/5/15/50/150/500/1500/5000・**倍率 ≈3**・**40%/20%/60%** を原典から取った。
- Zhou, Sornette, Hill & Dunbar (2005) *Proc. R. Soc. B* 272:439–444, DOI [10.1098/rspb.2004.3008](https://doi.org/10.1098/rspb.2004.3008) は **403 で取得不能 = 空欄**(Dunbar 2020 が同じ倍率 3 を引いているので代用可)。Hill & Dunbar (2003) *Human Nature* 14:53–72 も**未取得 = 空欄**。

---

## §4 指紋の比較 — 「5 本乱択」(数)と「ウォームアップ会話」(過程)

**正直に書く。引き分けではない。ただしウォームアップの勝ちは条件つきで、しかも条件はいま満たされていない。**

### 4-1 「5 本を一様乱択」が持ち込むもの

| 何を決めているか | 指紋の重さ | 根拠 |
|---|---|---|
| **本数 5**(現実に対応する量が無い) | **重い**。Dunbar の内層 5 は「最も親しい 5 人」であって「組織内の知り合い 5 人」ではない。**転用は根拠がない** | Dunbar 2020 図 2(5 = best friends) |
| **一様**(誰と誰も等確率) | **重い**。次数がほぼ揃い、同調性が解析的にゼロになる=実社会網の悪いモデル | Hamill & Gilbert 2009 §2.3 |
| **組織内に閉じる**(組織を跨がない) | 中。W16 の組織は経済センサス由来なので**母集団は現実**。ただし「組織内でしか知り合わない」は現実に反する | McPherson 2001(foci)・出生動向調査(友人経由) |
| 決定論・再現性 | 軽い(seed で再現できる) | — |

**合計: 数 1 個 + 分布の形 1 個。しかも形の方が結果への影響が大きい**(v1 §6.3 の記録: Centola 2010 クラスタ 53% vs ランダム 38%・初期 homophily を少し上げると最終同調性 0.142 → 0.287)。

### 4-2 「ウォームアップ会話」が持ち込むもの

**ユーザーの懸念(「組ませ方は設計者の規則になる」)は正しい。ただし本 repo は 2 通りの逃げ道を持っている。**

| ウォームアップの型 | 組ませ方を決めるもの | 設計者の数 | 実行可能性 |
|---|---|---|---|
| **W-A 世界内**: 関係層 ON の通常ランを n 日回し、checkpoint を初期状態にする | **W17 のスケジュール + C9 の幾何**(同一セル・距離 2 m)。設計者は 0 | **0**(会話の起点規則は R5 で別途決まる) | **いま不可能**(§5-3)。C10 で会話率が 2〜3 桁上がってから |
| **W-B 強制ペア**: 1 回きりの専用フェーズ。母集団(組織/世帯/学校/町丁目)から抽選してペアを作り会話させる | **抽選の母集団定義 + k + T** | **3**(母集団定義・k・T) | **可能**(§5-1: 6.26 h) |
| **W-C 機械的初期化(会話なし)**= 現行 R2(a) | **抽出規則**(親案③) | 1〜2 | 可能・費用 0 |

- **W-A は設計者の数が本当に 0 になる**。理由: 誰と誰が同じセルに 2 m 以内で居るかは、**W16 の建物・組織・学校 + W17 の時刻 + C9 の幾何**が決める。これは Hamill & Gilbert の `social reach` を**実測の渋谷で置き換えた**ことに等しい。**しかも Zhao et al. 2012 は「地図と経路は維持できる関係数を変えない(局在性だけ変える)」と報告している**ので、幾何を実測に任せても上限側は歪まない見込みがある。
- **W-B は「5 本乱択」と同種の指紋**。母集団定義(= 誰と誰を組ませてよいか)は結局「同一組織・同一世帯・同一学校・同一町丁目」であり、**親案③の抽出規則そのもの**。**違いは「本数を決め打つ(5)」か「会話の結果として本数が決まる(τ 超えの本数)」かの 1 点だけ**。この 1 点は小さくない——次数分布が正則から自然な裾を持つ分布に変わるので、§4-1 の「形」の問題を解く。
- **ウォームアップ特有の新しい指紋**: (a) **ウォームアップの会話プロンプトは通常の B6 と同じか、別のものか**(別にすると凍結テンプレが 1 本増え、指紋になる。**同じにすべき**)(b) **ウォームアップ中に世界の状態(所持金・在庫・位置)を動かすか**(動かすと保存則に穴が開く。**動かさない=会話の効果は E1/E2/E3 のみ**という行動契約 §4 の既決で足りる)。

### 4-3 公的統計で「組ませ方」を置けるか — 置ける部分と置けない部分

| 組ませ方の軸 | 公的統計で置けるか | 出所 |
|---|---|---|
| **組織規模の分布** | **置ける(既に置いてある)**。W16 の 9,872 組織・中央値 6・**76.3% が 15 人以下**は経済センサス由来 | `w16_population.parquet` の `org_id`(brief §1.8) |
| **同一町丁目** | **置ける**。国勢調査小地域 80 町丁目・人口 243,883 | `data/realworld/estat/`・ライセンス台帳 :11,21,22 |
| **世帯** | **半分**。規模 1/2/3 は置けるが**続柄が無い**(W16 の expedient「世帯は建物内の連番切り分け」) | brief §1.8 |
| **学校** | **置けない**。53 セル・定員データが無く「学校 POI へ一様」= expedient。セルあたり中央値 524 人から 15 人を選ぶ規則は**設計者が置くしかない** | brief §1.8 |
| **同年代の homophily** | **置けない(空欄)**。McPherson 2001 は順位(年齢は 2 位)を与えるが**日本の職場・近隣における年齢同類性の係数は見つからなかった** | — |
| **職場内で誰と話すか** | **置けない(空欄)**。W16 に `duty_role` はあるが部署・チームの構造が無い | — |

→ **正直な結論: 組ませ方の 6 軸のうち公的統計で置けるのは 2.5 軸。残り 3.5 軸は W-A(幾何に任せる)なら消え、W-B(抽選)なら設計者が置く。**

---

## §5 費用の算術

### 5-1 強制ペアのウォームアップ(W-B)— 1 回きり

前提: **1 会話 = T ブロック**(交互・1 呼 = 1 発話ブロック = 実会話 30〜60 秒相当)。**会話本数 = N·k/2**(1 会話に 2 体)。**総呼数 = N·k·T/2**。艦隊の実処理量 **78 応答/秒**(c7-day-2 実測・`docs/ops/build-report-C7.md`「tick 周期 22.9 s ≈ 1,792 呼を 78 呼/s で捌く時間」)。L4 = 400 万呼/日。

**関係の種を持つ体数 = 292,745**(`household_id ≥ 0` 43,588 ∪ `org_id ≥ 0` 222,849 ∪ `school_cell ≥ 0` 36,592。種を 1 本も持たない体 = **97,322**)[再計算・`w16_population.parquet` 390,067 行を直接集計]。

| 対象 | k | T | 会話本数 | 総呼数 | L4 換算 | 艦隊時間 |
|---|---:|---:|---:|---:|---:|---:|
| 種あり 292,745 | 1 | 2 | 146,372 | **292,745** | 0.07 日 | **1.04 h** |
| 種あり 292,745 | 1 | 4 | 146,372 | 585,490 | 0.15 日 | 2.09 h |
| 種あり 292,745 | **3** | **4** | 439,117 | **1,756,470** | **0.44 日** | **6.26 h** |
| 種あり 292,745 | 5 | 4 | 731,862 | 2,927,450 | 0.73 日 | 10.43 h |
| 全体 390,067 | 3 | 4 | 585,100 | 2,340,402 | 0.59 日 | 8.33 h |
| 全体 390,067 | 5 | 4 | 975,167 | 3,900,670 | 0.98 日 | 13.89 h |

**5,000 体の先行実験**:

| k | T | 会話本数 | 呼数 | 艦隊時間 |
|---:|---:|---:|---:|---:|
| 1 | 2 | 2,500 | 5,000 | **1.1 分** |
| 3 | 4 | 7,500 | **30,000** | **6.4 分** |
| 5 | 4 | 12,500 | 50,000 | 10.7 分 |

→ **5,000 体なら 6 分。1 日で何本も腕が回せる。**

### 5-2 予算行はどこに載るか

- **L4(400 万呼/日)には載せない**。ウォームアップは日次ではないので、**I1「初期化予算(1 回限り・W1 の対象外)」に新しい行を足す**のが正しい(既に「週次活動スケジュール表の初回生成=7日フル生成…DP7 で約12h」が入っている)。k=3・T=4 の 6.26 h は **I1 の既存項(12〜24 h)と同オーダー**で、収まる。
- **L2(ablation 予約枠 = 総 GPU 時間の 20%・W1 24 h → 4.8 h)は超える**(6.26 h)。→ **感度腕を 40 万体で回すなら L2 の別枠が要る**。5,000 体腕(6.4 分)なら L2 に余裕で収まる。
- **M5(関係 ≤6 KB/体)**: 基底活性方式は **最終相互作用時刻とエピソード数**を辺ごとに持つ必要がある。`相手 int32(4) + 強さ uint8(1) + 種別 uint8(1) + last_t uint32(4) + n_ep uint8(1) = 11 B/辺`[再計算]。**k=15 → 165 B/体 = 64.4 MB(39 万体)**。M5(6 KB/体)の 2.7%・M8(24 GB)に対して 0.27%。**問題なし**(brief の 6 B/辺・35 MB の想定より 1.8 倍)。
  - **注意**: 厳密な ACT-R は全エピソードの時刻を保持する。**Σ を全部持つのは 40 万体では不可能**。標準的な近似(最適化 ACT-R の base-level learning: 最近 k 本を厳密に、残りを n と経過時間で近似)を使う。**これは近似 = `expedient` タグつきで登録し、感度試験で「結果を駆動していない」証明が要る**。

### 5-3 世界内ウォームアップ(W-A)がいま不可能である算術

- c7-day-4 の実測: **成立会話セッション 410 件/日・390,067 体**(`accept_c7-day-4/run_cli_summary.txt`・brief §1.5)。
- 1 体あたり: 410 × 2 ÷ 390,067 = **0.0021 会話/体/日**[再計算]。
- k=3 本の辺を作るのに必要な日数(1 会話 = 1 辺と仮に置く・楽観): 3 ÷ 0.0021 = **約 1,427 シミュ日**。艦隊時間 1,427 × 9.64 h = **13,756 h ≈ 1.6 年**。**不可能**。
- C10 の 3 経路(招待の重みづけ・偶然・約束)+ 知人結線 + `pair_partners` 置換で会話率が **100 倍**になったとしても **約 14 シミュ日 = 135 h**。**200 倍で 7 日 = 67 h**。
- **目標側の物差し(A4)**: 交際・付き合い **10 分/日**(社会生活基本調査 R3・パターン台帳 A4・親確認済み)。1 呼 = 1 ブロック = 30〜60 秒とすると **10〜20 ブロック/体/日 = 390 万〜780 万呼/日**。**L4(400 万)をほぼ使い切るか超える**。一方、行動契約 §5 の設計値は「会話 ≈ 4.5 呼/体/日 = 180 万呼/日 = 予算の 45%」= **3.4 分/日相当**で、**A4 の 1/3**。
  - → **これは既存文書間の未解決の緊張**であり、C10 の合格線を A4 に置くなら **L4 か A4 のどちらかの解釈を先に決める必要がある**(「交際・付き合い」は主行動としての会話であり、ながら会話を含まない、という定義差が候補)。§8 に矛盾として記録。

### 5-4 まとめ

| 型 | 呼数 | 艦隊時間 | 予算行 | 判定 |
|---|---:|---:|---|---|
| W-B 5,000 体(k=3・T=4) | 30,000 | **6.4 分** | L2 内 | **すぐ回せる** |
| W-B 292,745 体(k=3・T=4) | 1,756,470 | **6.26 h** | **I1 に新行** | 回せる(L2 は超える) |
| W-A(会話率 100 倍後・14 日) | 約 3,790 万 | **135 h** | I1 | **C10 の成果を見てから** |
| W-A(現行会話率) | 約 38.6 億 | **13,756 h** | — | **不可能** |

---

## §6 推奨

### 6-1 (i) 記憶からの導出で置き換えられる数と、残る数

**採るべき形(推奨)**: 辺の強さ = **相互作用エピソード列に対する ACT-R 基底活性**。

```
A(u,v) = ln( Σ_j (Δt_j + 1)^(−d) )        # Δt_j = エピソード j からの経過時間(分)
d = 0.5                                     # 認知設計書 §4 の既決値をそのまま使う(新しい数ではない)
辺として持つ条件: A(u,v) ≥ τ                # τ = 検索閾値(新規・較正対象)
rel_strength(uint8) = 想起確率 P = 1/(1+exp(−(A−τ)/s)) を 0..255 に量子化   # Zhao 2012 の正規化に倣う
```

| 親案 | 判定 | 置換後 |
|---|---|---|
| ① 3 値尺度(−1/0/+1) | **置換**(§2-5 C 案) | 符号は **ResultCode と行動語**から。LLM に書かせない。`rel_sign: int8` は持つが**値はエンジンが入れる** |
| ② 会話 +1 | **削除** | エピソード種別 `CONV` を 1 本追加 |
| ② 同席 +0.5 | **削除** | エピソード種別 `COPRESENT` を 1 本追加(**同席を全部記録すると爆発する**ので「同一セル 2 m 内で 5 分以上」等の粒度定義が要る=下記の残る数 2) |
| ② 約束成立 +2 | **削除** | エピソード種別 `PROMISE_KEPT` |
| ② 断る −1 | **削除**(回数)+**符号は残す** | `REFUSED` エピソード + 符号 − |
| ② すっぽかし −2 | **削除**(回数)+**符号は残す** | `PARTNER_NO_SHOW` エピソード + 符号 − |
| ② 半減期 30 日 | **削除** | d=0.5(既決)。**しかも §8 の矛盾を同時に解消する** |
| **残る数 1: τ** | **新規・較正対象** | 初期値は「k=15 の辺が残る τ」から逆算(= Dunbar L3)。感度腕 ± |
| **残る数 2: エピソードの粒度** | **新規・定義** | 会話 = 1 セッション 1 本(ブロック数ではない)/ 同席 = **未リサーチ(expedient)**・初期案「同セル・距離 2 m・連続 5 分」 |
| 既決の再確認 3: d=0.5 | **流用**(記憶から関係への転用は新しい仮定) | 感度腕 d ∈ {0.25, 0.5, 0.75} |

**ユーザーへの答え(問 A)**: **「わざわざ数字を定義する必要はある?」→ ②については、ありません。①については符号だけ要りますが、それも LLM に書かせずエンジンの結果コードから取れます。**「経験から設定してよいのでは」→ **τ の自己調整は魅力的だが先行が無い(未リサーチ・expedient)。C10 では固定 + 感度腕を推奨**。

### 6-2 (ii) ウォームアップの設計案

**推奨は「W-C を既定・W-B を 5,000 体で先に測る・W-A は C10 の会話率を見てから」。** 理由は §5-3(W-A はいま不可能)と §4-2(W-B は結局 5 本乱択と同種の指紋を持つ)。

**W-B の設計(5,000 体で測る版)**

| 項目 | 案 | タグ |
|---|---|---|
| **組ませ方** | **同一 org / 同一 household / 同一 school_cell / 同一 chome_key の 4 プールから、各体が「その日の W17 スケジュールで実際に同じセルに居た相手」を優先して抽選**。つまり抽選の重みは **C9 の共在時間**。共在が 0 の相手とは組ませない | **mechanism**(重みは実データ由来) |
| **会話数 k** | **3**(1・3・5 を腕にする) | **expedient**(§5 の費用からの選択。現実アンカー無し) |
| **ブロック数 T** | **4**(現行 `MAX_TURNS=3` + 締め。通常ランと同じ会話マネージャを使う) | **既存の expedient を流用**(新しい指紋を作らない) |
| **プロンプト** | **通常の B6 テンプレをそのまま使う**(`template_sha256` 不変)。ウォームアップ専用テンプレを作らない | **mechanism**(指紋を増やさない) |
| **世界への効果** | **E1(記憶転写)・E2(辺の強度)・E3(辺の追加)のみ**。所持金・在庫・位置は一切動かさない | 行動契約・答申 E1〜E5 の既決 |
| **何を辺に残すか** | 相手 id(int32)・想起確率(uint8)・種別(uint8)・**最終相互作用時刻(uint32)**・**エピソード数(uint8)**・符号(int8)= **12 B/辺**・k=15 で 180 B/体 = 70 MB | M5 内 |
| **停止則** | 決め打ちの k ではなく、**辺の次数分布と強さ分布が定常になるまで**(Welch 図示 + CV 収束)。ただし上限 k=5 | STRESS / MultiVeStA の作法 |
| **ウォームアップの時刻** | 全部を「ラン開始の 1 日前」に押し込むと、全エピソードの Δt が同じになり **基底活性が全辺同値**になる。→ **過去 90 日に散らして時刻スタンプを打つ**(散らし方は W17 の過去日スケジュールから) | **要注意・新しい落とし穴** |

**測る指標(パターン台帳との照合)**

| 指標 | 照合先 | 判定型 |
|---|---|---|
| 会話グループサイズ(2 人 53.9%・95% が 4 人以下) | **A1(強・holdout)** | shape+band |
| 交際・付き合い 10 分/日 | **A4(holdout)** | band(上界見張り) |
| 内層(相互 top5)の年間入替 1〜4%/年 | **B3(holdout)** | band |
| 内層 5 人の安定 | **B4(holdout)** | band |
| **層別の 1 日あたり接触率**(最内層 ≈0.4 回/日・以降単調減) | **Dunbar 2020 図 3(新規アンカー候補)** | shape |
| **努力配分 40%/20%/60%** | **Dunbar 2020(新規アンカー候補)** | band |
| **対面接触頻度の分布**(週4-5回以上 16.3% … 全くない 9.2%) | **内閣官房 R5(新規アンカー候補)** | shape |
| **social signature の形の持続**(d_self < d_ref が 82%±12%) | **Saramäki 2014(新規アンカー候補)** | shape |
| 三者閉包(共通接触でオッズ比 約 30 倍) | B2(holdout) | band |
| 近接性(隣室 41%) | B1(holdout) | ordinal |

→ **新しいアンカー候補 4 本**(Dunbar 図 3・Dunbar 40/20/60・内閣官房 R5 分布・Saramäki signature)。**registry.yaml に関係・会話のアンカーが 1 本も無い穴**(brief §6-2)を埋める。**holdout 分割は R14 の決定(台帳の該当行を封印)に従う**。

### 6-3 (iii) 5,000 体での検証実験の腕定義

**共通条件**: 5,000 体(W16 から層化抽出・既存の モック/先行実験の作法に合わせる)・実 LLM 8B INT8・温度 0.7・seed 2 本・ウォームアップ後に **7 シミュ日**の本ランを回して指標を測る。**holdout は開けない**(§6-2 の指標は事前登録 v2.0 に書いて封印)。

| 腕 | ウォームアップ | 辺の更新 | 符号 | 目的 |
|---|---|---|---|---|
| **R-C10-0(帰無)** | 無し | **辺なし**(現行) | — | 「辺がある」こと自体の効果を測る基準 |
| **R-C10-1(親案)** | 無し | W-C 機械的初期化(世帯 全ペア + 組織から **5 本を一様乱択**)+ **Δ 方式**(会話+1・同席+0.5・約束+2・断る−1・すっぽかし−2・半減期 30 日) | LLM が書く 3 値(①) | **親案 ①②③ をそのまま実装した腕**。比較の基準 |
| **R-C10-2(基底活性・機械初期化)** | 無し | W-C 機械的初期化(組織は**共在時間の重み**で抽選・本数は τ が決める)+ **基底活性方式**(d=0.5・τ) | **ResultCode 由来**(§2-5 C 案) | **問 A への答えを測る腕**。R-C10-1 との差 = 「数を消した効果」 |
| **R-C10-3(ウォームアップ)** | **W-B**(k=3・T=4・共在重み・時刻を過去 90 日に散らす) | 基底活性方式 | ResultCode 由来 | **問 B への答えを測る腕**。R-C10-2 との差 = 「会話で作った効果」 |
| **R-C10-4(気分語を効かせる)** | W-B | 基底活性方式 + **気分語(§2-5 B 案)を符号に加算** | ResultCode + 気分語 | R9′(i) のユーザー案を測る。R-C10-3 との差 = 「LLM の気分申告の効果」 |
| **感度 S1** | R-C10-3 と同じ | **τ ±**(k_eff が 8 / 15 / 30 になる 3 水準) | — | τ が結果を駆動していないかの証明 |
| **感度 S2** | R-C10-3 と同じ | **d ∈ {0.25, 0.5, 0.75}** | — | 記憶の d を関係に転用した仮定の検査 |
| **感度 S3** | **W-B の k ∈ {1,3,5}** | 基底活性方式 | — | 初期網密度(R2 の既決 感度 2 本と統合できる) |

**費用**: 5 腕 × 2 seed × (ウォームアップ 6.4 分 + 本ラン 7 日) + 感度 3 群。本ランの呼数は 5,000 体 × 7 日 × 6.94 呼/体/日 ≈ 243,000 呼 = **52 分**/腕・seed。**全体で約 12〜15 時間**[再計算]。**L2(4.8 h)を超えるので、第2波の別枠 4.8 h では足りない=ユーザー判断が要る**。削るなら感度 S2 を後回し(d は既決値の流用なので優先度が下がる)。

**事前の予想(事前登録に書く・外れてもよい)**:
1. **R-C10-1 と R-C10-2 の差は小さい**(どちらも網が出来ればよいので)。もし大きいなら「数の置き方が結果を駆動している」証拠で、それ自体が重要。
2. **R-C10-3 は次数分布が R-C10-1/2 より裾を持つ**(正則にならない)。
3. **Dunbar 層(5/15/50/150)はどの腕でも出ない**(Dunbar 2020: ABM で層構造が出るのは <1% の run)。
4. **R-C10-4 の気分語は最頻値が例示値と一致する**(メモリ `fewshot-time-anchoring-8b` の規律で最初に確認する)。
5. A1(会話グループサイズ 2 人 53.9%)は **2 人に張り付きすぎる**(会話マネージャが 2 体固定なので、3 人以上が構造的に出ない)。→ **A1 を合格線にするなら、3 人以上の会話を作る口が別途要る**。

---

## §7 空欄(読めなかった・見つからなかったもの)

1. **Zhou, Sornette, Hill & Dunbar 2005**(*Proc. R. Soc. B* 272:439–444)= royalsocietypublishing.org が 403。倍率 3 は Dunbar 2020 で代用した。**Hill & Dunbar 2003**(*Human Nature* 14:53–72)も未取得。
2. **IPSS 図表5-3 の数値**(友人・兄弟姉妹を通じて 25.9% / 職場や仕事で 21.4%)は**図中に焼かれており PDF 本文テキストに無い**。検索要約経由=**一次未確認**。ネット 13.6% は本文から確認済み。
3. **AgentSociety の社会網初期化**は抄録に記述なし。本文 PDF は未取得。v1 資産の「ユーザーが与えると明言」は**本調査では確認できなかった**。
4. **8B における「3 値 vs 5 値」の直接比較**は見つからなかった。Li 2026 の 0-5 最良は「人間との一致」であって刻みの縮退の比較ではない。
5. **日本の職場・近隣における年齢同類性の係数**(McPherson の順位は取れたが日本の数値は無し)。**職場内の部署・チーム構造**も W16 に無い。
6. **ウォームアップの先行**は 8 系統を当たって 0 本。「無い」の判定は**私の探索範囲内**であり、親が別の語(pre-training phase / bootstrapping phase / seeding interactions / social scaffolding)で再探索する価値がある。
7. **Roberts & Dunbar 2015 の数値**は WebFetch の読み取り器が返したもので、**私自身の機械抽出ではない**(PMC の HTML を pymupdf に通していない)。b=−0.71 と 70.3%/48.6% は親の再確認対象。
8. **Zhao et al. 2015 CMOT 版**(CogSci 2012 の拡張)は検索要約のみ。式 1・式 2 の本体は CogSci PDF でも**画像で、テキスト抽出できなかった**(本文の説明文だけ引いた)。
9. **約束の遵守率・対面口コミの伝播率**は既存答申が自ら空欄と申告しており(`v2-action-conversation-contract-research.md` :450-458)、本調査でも埋まらなかった。
10. **エピソードの粒度(同席をいつ 1 本と数えるか)**に先行が無い。Zhao 2012 は「部屋の共在 1 回」= 部屋の粒度。本 repo のセル(50 m)で同じことをすると 1 日で数千本になる。**未リサーチ(expedient)**。

---

## §8 検出した矛盾・齟齬(CLAUDE.md §2-1「矛盾は積極検出して確認」)

1. **半減期が 2 つある**。行動契約 §5(`docs/design/v2-action-contract.md:56-69`)= 「**減衰 半減期 90 日**(expedient)」。C10 決定アジェンダ §5 ②(`docs/design/v2-c10-relations-agenda.md:53`)= 「**半減期 30 日**」。**3 倍違う**。基底活性方式を採れば**両方消える**ので、この矛盾は解消と同時に片づく。採らない場合は**どちらかに寄せる必要がある**。実証側(Roberts & Dunbar 2015: 友人の「最終接触からの日数」28→69→129 日で親密さが下がる / Dunbar 2020「a matter of a few months」)は **90 日側**に近い。
2. **「平時入替 1%/年」の出典写しズレ**。行動契約 §5 は mechanism タグで「平時入替 1%/年」と書くが、Dunbar 2020 の原典文は「**関係の決裂(terminal breakdown)**が年 1% 程度」。パターン台帳 B3 の「内層の年間入替 1〜4%/年」(Roy 2022)とは別の量。→ 語か出典の修正が要る(§1-4)。
3. **「激変時 18 か月で 40%」のフロア併記漏れ**。Dunbar 2020 の要約値であり、原典 Saramäki 2014 の**Jaccard 0.22±0.09(全網)/ 0.36±0.13(上位 20)**はもっと大きな入替を意味する。→ 併記すべき(§1-5)。
4. **A4(交際 10 分/日)と L4(400 万呼/日)の緊張**。A4 を素直に呼数に換算すると 390 万〜780 万呼/日で L4 をほぼ使い切る。行動契約 §5 の設計値(4.5 呼/体/日 = 3.4 分相当)は A4 の 1/3。→ **C10 の合格線を A4 に置く前に、定義(主行動としての交際 vs ながら会話)を決める必要**(§5-3)。
5. **A1(会話グループサイズ)と会話マネージャの構造の不整合**。A1 は「2 人 53.9%・95% が 4 人以下」= **3 人以上が 4 割強**。現行の `ConversationManager` は 2 体固定(`talk_partner` 1 本)なので、**3 人以上が構造的に 0%**。A1 を第2陣の holdout 判定に使うなら(R14)、**3 人以上の会話を作る口**が C10 の実装項目に要る。brief にも agenda にも無い(**新規の欠落**)。
6. **`rel_strength` 6 B/辺の見積りが基底活性方式では足りない**。基底活性の再計算には**最終相互作用時刻とエピソード数**が要るので 11〜12 B/辺(§5-2)。M5 内だが、brief の 35 MB は 70 MB になる。

---

## lit README 追記行

> **注意: 本節は「追記行の案」であり、`docs/research/lit/README.md` は本調査では編集していない**(規律どおり)。実ファイルは `docs/research/lit/` 配下に 8 本作成済み。

| メモ | 分野 | 一次確認 | 何のために引くか |
|---|---|---|---|
| [relations__gilbert2009_tie-strength-prediction](lit/relations__gilbert2009_tie-strength-prediction.md) | 社会ネットワーク科学 #14 / 計算社会科学 #25 | **実読**(サブ・pymupdf・親未確認) | **辺の強さの最良予測子は「最終接触からの日数」β=−0.76**(Adj R²=0.534)。情動語は 12 位 β=0.135 = **好悪より履歴**。親案② を消す一次根拠 |
| [relations__zhao2012_actr-dunbar-network](lit/relations__zhao2012_actr-dunbar-network.md) | 社会ネットワーク科学 #14 / 認知科学 #12 / ABM方法論 #21 | **実読**(サブ・pymupdf・親未確認) | **ACT-R 基底活性を社会関係に転用した唯一の先行**。設計者が置いた数は**検索閾値 τ 1 個**。地図と経路は Dunbar 数を変えない |
| [relations__dunbar2020_structure-function](lit/relations__dunbar2020_structure-function.md) | 社会ネットワーク科学 #14 | **実読**(サブ・pymupdf・親未確認) | **層は接触頻度で定義される**・倍率 3・**40%/20%/60% の写し検査 PASS**・**ABM で層構造が出るのは <1% の run** |
| [relations__saramaki2014_social-signatures](lit/relations__saramaki2014_social-signatures.md) | 社会ネットワーク科学 #14 / 計算社会科学 #25 | **実読**(サブ・arXiv 版 pymupdf・親未確認) | **入れ替わるのは相手、残るのは注意配分の形**。Jaccard 0.22/0.27・82%±12%。**初期網の与え方に依存しにくい holdout 候補** |
| [relations__robertsdunbar2015_relationship-decay](lit/relations__robertsdunbar2015_relationship-decay.md) | 社会ネットワーク科学 #14 / 人格心理学 #13 | **B**(WebFetch 読み取り器・**私の機械抽出ではない**) | 「最終接触からの日数」が親密さの**変化**を予測 b=−0.71。**家族 +0.27 / 友人 −0.62 = 半減期を 1 個で置けない** |
| [relations__bougie2025_citysim-social](lit/relations__bougie2025_citysim-social.md) | 計算社会科学 #25 / 人間移動科学 #3 | **実読**(サブ・pymupdf・親未確認) | **positive/neutral/negative の 3 分類の先例**(親案①は未リサーチではない)・homophily 初期化・**渋谷の POI 人気と群集密度を照合している競合** |
| [relations__schneider2025_llm-emergent-ties](lit/relations__schneider2025_llm-emergent-ties.md) | 計算社会科学 #25 / 自然言語処理 #27 | **実読**(サブ・pymupdf・親未確認) | **E₀=∅ の冷スタート**・gated update 式(ξ・Δmax・δ・半減期 h)= **2025 年でも辺の更新は設計者の数 4 個**。親案②が分野標準であることの裏づけと、消せることの対比 |
| [relations__li2026_scoring-bias-8b](lit/relations__li2026_scoring-bias-8b.md) | 自然言語処理 #27 / 検証とV&V #22 | **実読**(サブ・pymupdf・親未確認) | **Qwen3-8B は採点規準の並び替えだけで 46.22% の点が壊れる**(32B は 28.56%)。**8B に数値尺度を書かせない**根拠 |

---

## 親確認の要請(上位 5 件)

| # | 主張 | 確認の手順 | URL |
|---|---|---|---|
| **1** | **Gilbert & Karahalios 2009 の β=−0.76 は「recency が支配」でなく「接触 0 回 vs 1 回以上」の効果で膨らんでいる**(著者自身が注記)。本答申の §1-2 はこの但し書きを付けて引いている。**§6-1 の「Δ を消せる」結論はこの但し書きに耐えるか** | PDF を pymupdf で開き `Table 3` 直後の "The two Days since variables have such high coefficients due to friends that never communicated via Facebook." を読む。Adj R²=0.534・MAE=0.0994 を再確認 | https://userpages.umbc.edu/~skane/classes/is760/fall2011/c3/PredictTieStrength.pdf |
| **2** | **Dunbar 2020 の 40%/20%/60% が行動契約 §5 の記載と一致する**(写し検査 PASS)。**かつ「平時入替 1%/年」は原典では「決裂 1%/年」で語が違う**(写しズレ) | ORA 版 PDF を pymupdf で開き "Approximately 40% of all social effort" と "about 1% of relationships per year" の 2 文を読み、`docs/design/v2-action-contract.md:56-69` と突き合わせる | https://ora.ox.ac.uk/objects/uuid:f56e97cb-c481-449c-b792-a76156550d9e/ (DOI 10.1098/rspa.2020.0446) |
| **3** | **Zhao et al. 2012 は「ACT-R 基底活性 = 辺」で設計者の数を τ 1 個に絞っている**(§6-1 の推奨の土台)。**かつ 40 体で 800 リンク(20 本/体)であって Dunbar 150 ではない** | eScholarship PDF を pymupdf で開き "the average number of relations were same for both networks" を含む結論節と "flattens when it reaches 1,336 ties" / "remains at 800 links" を読む | https://escholarship.org/uc/item/85t2040s |
| **4** | **Qwen3-8B は採点規準を並べ替えるだけで 46.22% の点が壊れる**(§2-5 で「LLM に数値を書かせない」を決める根拠) | arXiv v4 PDF を pymupdf で開き §4.2 の "An exception is Qwen3-8B, whose score distribution is more significantly influenced by biases, possibly due to its small size." と Table 3 の 46.22 / 0.5296 を読む | https://arxiv.org/abs/2506.22316 |
| **5** | **内閣官房 R5 の接触頻度分布**(週4-5回以上 16.3% … 全くない 9.2%・n=11,141)。**新しい現実アンカー候補として registry.yaml に足す価値があるか** | PDF を pymupdf で開き 図1-25 の凡例 `週４～５回以上（1,812）…全くない（1,029）` を読み、11,141 で割って本答申 §3-3 の表を再計算。ライセンス台帳への登録要否も判断 | https://www.cao.go.jp/kodoku_koritsu/torikumi/zenkokuchousa/r5/pdf/tyosakekka_gaiyo.pdf |
