# R-88 答申: LLM の人間らしさ・熟考の頻度・画像による知覚

<!-- hdr:v1 -->
- **分野**: 自然言語処理・機械学習 #27 / 計算社会科学 #25 / 認知科学 #12 / 知覚心理学 #5 / ABM方法論 #21 | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §7-3・§7-4・§11 第 3 群「LLM の人間らしさ」「熟考の頻度」、§7-4 の画像による知覚)
- **一次確認**: **B**(サブ実読。本文を自分で抽出した原典 6・取得ツール経由の本文 6・抄録または二次 29・空欄 15 件は §7)・親検収 済(第319・2026-10-03: Park 2024 の 68.85 ÷ 81.25 = 85%(v1)と v3 の 83/82/86% の版差・Wood 2002 の 43%・Killingsworth 2010 の 46.9% は既知の値と一致。「1 日 35,000 回の決定」を根拠なしとして使わない扱いは妥当。△ 29 本の抄録は親未読。等級 B+)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は取得ツールが保存した写しを pymupdf で抽出)・コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: LLM 社会シミュレーションの全文確認 = [R-2](v2-r2-llm-social-sim-fulltext-check.md) / 閉じた出力の判定器 = [R-38](v2-r38-closed-output-judges-research.md) / 判断の割合と System 1・2 = [R-39](v2-r39-judgment-share-research.md)(Hofmann 2012 の 21% はここ)/ 思考頻度の錨 H1〜H9 = [思考頻度ノート](v2-thought-frequency-anchors-note.md) / Jev 型の決定モデル = [R-83](v2-r83-jev-type-decision-models.md)(H8-6 の評価の形) / 気づく要因 = [R-79](v2-r79-noticing-factors-conversation-distance.md) / 広告・看板 = [広告答申](v2-ad-information-research.md)・[R-51](v2-r51-mere-exposure-incidental-ads-research.md)。本書は重なる値を再掲せずリンクし、足りない値だけを足す。

## 結論(5 行)

1. **A 人間らしさ**: Park ほか 2024 の 1,052 人の生成エージェントは、GSS で本人の 2 週間後の再回答の 85% の正しさでした(生の正答 68.85% ÷ 本人の再現 81.25%・原典)。属性だけのエージェントは 0.71 でした。最新版 v3(2026-06)の抄録では、数値が 83%/82%/86% に改訂されています。弱点は 4 つとも原典か抄録で確かめました。ばらつきが小さすぎる点では、Bisbee 2024 で係数の 48% が実データと有意に違い、そのうち 32% は符号が逆でした。協力的すぎる点では、囚人のジレンマでの協力が GPT-3.5 は約 65%、人は 37% でした(人の研究どうしの幅は 0.04〜0.84)。ステレオタイプ化は Cheng 2023・Wang 2025、言い回しへの敏感さは Sclar 2024(最大 76 点差)・選択肢の順序(13〜85% の差)です。
2. **8B 級**: 「小さいほど人間らしくない」とは言い切れません。小さいモデルは同じ問いへの答えが散りますが、これは人のばらつきとは別の雑音です。大きいモデルでも、属性の影響を実際より大きく見積もる誤りは直りませんでした(2026 年の 8B〜最上位の比較)。基盤モデルか指示調整済みかの違いの方が影響が大きいという報告もあります(二次)。
3. **検証の 3 段と摂動の試験**: 個体・小集団・群衆の 3 段に分けて頑健性を監査する先行があります(TRAILS 2026。人の形式を少し変えただけで協力率が最大 76 ポイント動いた)。摂動の試験には床が 2 つ要ります。1 つは何も変えずに再実行したときのぶれ(2.5〜23.7%)、もう 1 つは意味を変えない言い換えでのぶれです(性別を変えた 14.9% と言い換えの 14.1% は区別できなかった)。
4. **B 熟考の頻度**: 「人が立ち止まって考える割合」を直接測った値は見つかりませんでした。監視に使える近い値は次のとおりです。日記で習慣と分類された行動は 35%/43%(Wood 2002・原典)、習慣でない行動の間は考えが行動と一致した割合が 70%/60% でした。棚の前の滞在は平均 12 秒で、選んだ品の値段を見たのは 58%、他の品の値段を比べたのは 22% 未満でした(Dickson & Sawyer)。心のさまよいは 46.9%(Killingsworth)・32%(Kane)ですが、答えの選択肢しだいで 10〜60% まで動きます(Seli 2018)。「1 日 35,000 回」と「95% は無意識」には測定の出どころがありません。
5. **C 画像の腕**: 画像 1 枚のトークンは、Qwen2-VL では 224×224 で 66、LLaVA-1.5 では 576 [再計算] です。Clef の枚数あたりのトークン数は空欄です。渋谷のテクスチャ付き LOD2 は、ブラウザ(Cesium)での表示でも最低 1〜3 FPS・メモリ約 1.1〜1.7 GB で、条件によっては描画に失敗しました(国交省の技術レポート・原典)。壁面のテクスチャは直下視の航空写真(20〜25 cm)を引き伸ばしたもので、看板の文字は写りにくいです。人の側の錨は避難誘導標識の実験で、視認範囲にあっても気づいたのは 38%(31/82)、気づいた人の 97% が従いました(Xie 2011・原典)。看板 1 つに絞った GPU 後の腕の案を §4-4 に置きます(費用は推測)。

## §0 出典の表

等級: **◎** 原典の本文テキストを自分で抽出して数値まで逐語確認 / **○** 原典の本文を取得ツール経由で読んだ(逐語は取得ツールの引用) / **△** 抄録・二次 / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Park J.S. ほか 2024「Generative Agent Simulations of 1,000 People」arXiv:2411.10109 v1(v3 は題名を「LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals」に改題・2026-06-28) | https://arxiv.org/abs/2411.10109 | ◎(v1 PDF)/ △(v3 は抄録のみ) | v1 PDF の結果の節と表・v1/v3 の抄録 |
| 2 | Santurkar S. ほか 2023「Whose Opinions Do Language Models Reflect?」arXiv:2303.17548 | https://arxiv.org/abs/2303.17548 | △ | 抄録〔注(第324): 本文は [R-104](v2-r104-llm-agent-human-gaps-and-transit-app-accuracy.md) で読んだ(○)。本書の記述は抄録の範囲のまま〕 |
| 3 | Argyle L.P. ほか 2023「Out of One, Many: Using Language Models to Simulate Human Samples」Political Analysis(arXiv:2209.06899) | https://arxiv.org/abs/2209.06899 | △ | 抄録 |
| 4 | Bisbee J. ほか 2024「Synthetic Replacements for Human Survey Data? The Perils of Large Language Models」Political Analysis 32(4):401-416 | https://doi.org/10.1017/pan.2024.5 | ○ | 出版社ページの本文(取得ツールの引用) |
| 5 | Aher G., Arriaga R.I., Kalai A.T. 2023「Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies」ICML 2023(arXiv:2208.10264) | https://arxiv.org/abs/2208.10264 | △〔注(第324): 本文は R-104 で読んだ(○)〕 | 抄録 |
| 6 | Cheng M., Durmus E., Jurafsky D. 2023「Marked Personas」ACL 2023(arXiv:2305.18189) | https://arxiv.org/abs/2305.18189 | △ | 抄録 |
| 7 | Wang A., Morgenstern J., Dickerson J.P.「Large language models that replace human participants can harmfully misportray and flatten identity groups」Nature Machine Intelligence 採録(arXiv:2402.01908 v3・2025-02) | https://arxiv.org/abs/2402.01908 | △ | 抄録 |
| 8 | Horton J.J., Filippas A., Manning B.S.「Large Language Models as Simulated Economic Agents: What Can We Learn from Homo Silicus?」arXiv:2301.07543(v2 2026-02) | https://arxiv.org/abs/2301.07543 | △ | 抄録 |
| 9 | Brookins P., DeBacker J. 2024「Playing games with GPT」Economics Bulletin 44(1):25-37 | http://www.accessecon.com/Pubs/EB/2024/Volume44/EB-24-V44-I1-P3.pdf | ◎ | PDF 全文 |
| 10 | Mei Q., Xie Y., Yuan W., Jackson M.O. 2024「A Turing test of whether AI chatbots are behaviorally similar to humans」PNAS 121(9):e2313925121 | https://doi.org/10.1073/pnas.2313925121 | △ | 抄録と要旨(検索経由。出版社ページは 403) |
| 11 | Sclar M. ほか 2024「Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design」ICLR 2024(arXiv:2310.11324) | https://arxiv.org/abs/2310.11324 | △ | 抄録 |
| 12 | Tjuatja L. ほか 2024「Do LLMs exhibit human-like response biases? A case study in survey design」(arXiv:2311.04076) | https://arxiv.org/abs/2311.04076 | △ | 抄録 |
| 13 | Pezeshkpour P., Hruschka E. 2024「Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions」Findings of NAACL 2024 | https://aclanthology.org/2024.findings-naacl.130/ | △ | 抄録 |
| 14 | Rupprecht J., Ahnert G., Strohmaier M. 2025「Prompt Perturbations Reveal Human-Like Biases in Large Language Model Survey Responses」arXiv:2507.07188 | https://arxiv.org/abs/2507.07188 | △ | 抄録 |
| 15 | Chen Z., Zhu D., Zheng L.N. 2026「When Synthetic Users Fail: A Cross-Domain Benchmark of LLM-Simulated Human Survey Responses」arXiv:2607.26348 | https://arxiv.org/abs/2607.26348 | △ | 抄録 |
| 16 | Larooij M., Törnberg P. 2026「Validation is the central challenge for generative social simulation」Artificial Intelligence Review 59(1):15(arXiv:2504.03274) | https://doi.org/10.1007/s10462-025-11412-6 | △ | 検索要約と抄録 |
| 17 | Ye J., Cao L., Chen D., Ferrara E. 2026「Stop Drawing Scientific Claims from LLM Social Simulations Without Robustness Audits」arXiv:2605.18890 | https://arxiv.org/abs/2605.18890 | △ | 抄録 |
| 18 | Yang Z., Levy M., Goldberg Y., Wallace B.C. 2026「Compared to What? Baselines and Metrics for Counterfactual Prompting」COLM 2026(arXiv:2605.01048) | https://arxiv.org/abs/2605.01048 | △ | 抄録 |
| 19 | Bellibatlu R.R. ほか 2026「Instability Floors: Separating Bias from Noise in Fairness Audits of Clinical LLM Agents with FairMedAgent」arXiv:2609.03221 v3 | https://arxiv.org/abs/2609.03221 | △ | 抄録 |
| 20 | Veitch V. ほか 2021「Counterfactual Invariance to Spurious Correlations」NeurIPS 2021(arXiv:2106.00545) | https://arxiv.org/abs/2106.00545 | △ | 抄録 |
| 21 | Wood W., Quinn J.M., Kashy D.A. 2002「Habits in Everyday Life: Thought, Emotion, and Action」JPSP 83(6):1281-1297 | https://dornsife.usc.edu/wendy-wood/wp-content/uploads/sites/183/2023/10/Wood.Quinn_.Kashy_.2002_Habits_in_everyday_life.pdf | ◎ | PDF 全文 |
| 22 | Killingsworth M.A., Gilbert D.T. 2010「A Wandering Mind Is an Unhappy Mind」Science 330:932 | https://doi.org/10.1126/science.1192439 | ○ | Fermat's Library の注釈版本文(取得ツールの引用)。出版社ページは 403 |
| 23 | Kane M.J. ほか 2017「For Whom the Mind Wanders, and When, Varies Across Laboratory and Daily-Life Settings」Psychological Science(PMC5591044) | https://pmc.ncbi.nlm.nih.gov/articles/PMC5591044/ | ○ | PMC 本文(取得ツールの引用)。Kane ほか 2007 の 30% はこの本文の再掲 |
| 24 | Seli P. ほか 2018「How pervasive is mind wandering, really?」Consciousness and Cognition 66:74-78 | https://doi.org/10.1016/j.concog.2018.10.002 | △ | 抄録(Penn State の書誌ページ) |
| 25 | Dickson P.R., Sawyer A.G. 1990「The Price Knowledge and Search of Supermarket Shoppers」Journal of Marketing 54(3):42-53 と、同じ調査の MSI ワーキングペーパー(1986) | https://www.msi.org/working-papers/pointofpurchase-behavior-and-price-perceptions-of-supermarket-shoppers/ | ○ | MSI の要約ページ(取得ツールの引用)。JM 論文の本文は未読 |
| 26 | Nieuwenstein M.R. ほか 2015「On making the right choice: A meta-analysis and large-scale replication attempt of the unconscious thought advantage」JDM 10(1):1-17 | https://doi.org/10.1017/S1930297500003144 | △ | PDF の抄録を自分で抽出 |
| 27 | Kahneman D. 2011『Thinking, Fast and Slow』第 1 章の一文 | なし | △ | 読者の抜き書き(二次) |
| 28 | Zaltman G. 2003『How Customers Think』の「95%」 | なし | △ | 二次(ブログ・検索要約) |
| 29 | Wang P. ほか 2024「Qwen2-VL」arXiv:2409.12191 | https://arxiv.org/html/2409.12191 | ○ | 本文 HTML §2・§2.1(取得ツールの引用) |
| 30 | Liu H. ほか 2024「Improved Baselines with Visual Instruction Tuning」CVPR 2024(arXiv:2310.03744) | https://arxiv.org/abs/2310.03744 | △ | 抄録(576 は再計算) |
| 31 | Cloudflare Workers AI「clef」 | https://developers.cloudflare.com/workers-ai/models/clef/ | ○ | 画像の上限・価格・文脈長 |
| 32 | Savva M. ほか 2019「Habitat: A Platform for Embodied AI Research」ICCV 2019(arXiv:1904.01201) | https://arxiv.org/abs/1904.01201 | △ | 抄録 |
| 33 | Chen H. ほか 2019「Touchdown」CVPR 2019(arXiv:1811.12354) | https://arxiv.org/abs/1811.12354 | △ | 抄録 |
| 34 | Mirowski P. ほか 2018「Learning to Navigate in Cities Without a Map」NeurIPS 2018(arXiv:1804.00168) | https://arxiv.org/abs/1804.00168 | △ | 抄録 |
| 35 | Gao C. ほか 2024「EmbodiedCity」arXiv:2410.09604 | https://arxiv.org/abs/2410.09604 | △ | 検索要約 |
| 36 | Watanabe K. ほか 2026「360CityArena」ECCV 2026(arXiv:2608.08814) | https://arxiv.org/abs/2608.08814 | △ | 抄録 |
| 37 | Dubey A. ほか 2016「Deep Learning the City」ECCV 2016(arXiv:1608.01769) | https://arxiv.org/abs/1608.01769 | △ | 抄録 |
| 38 | Ertler C. ほか 2020「The Mapillary Traffic Sign Dataset for Detection and Classification on a Global Scale」arXiv:1909.04422 | https://arxiv.org/abs/1909.04422 | △ | 抄録 |
| 39 | Xie H. 2011 博士論文「Investigation into the interaction of people with signage systems and its implementation within evacuation models」University of Greenwich | https://gala.gre.ac.uk/id/eprint/8080/1/Hui_Xie_2011.pdf | ◎ | PDF の第 7 章(検知率・従った率・人数) |
| 40 | 国交省 PLATEAU 技術調査レポート「3D 都市モデルのテクスチャ高解像度化手法及び描画パフォーマンス向上に関する技術調査レポート」(plateau_tech_doc_0062) | https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_tech_doc_0062_ver01.pdf | ◎ | §2.1.2・§2.2.2・§2.3.4・表 3-11 |
| 41 | 国交省 PLATEAU「3D 都市モデル整備のための測量マニュアル」第 24 条 | https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_doc_0010_ver02.pdf | ◎ | 第 24 条 |

本数: ◎ 6(#1・#9・#21・#39・#40・#41)・○ 6(#4・#22・#23・#25・#29・#31)・△ 29(#26 は PDF から抄録だけを抽出したので △)。読めなかったものは §7 の空欄に並べた。

## §1 A: LLM が人の行動をどこまで再現するか

### 1-1 個人の再現(Park ほか 2024)

| 量 | 値(原典 v1 の逐語) | 等級 |
|---|---|---|
| 対象 | 米国の 1,052 人。2 時間のインタビューから作ったエージェント。本人は 2 週間あけて同じ質問紙に 2 回答えた | ◎ |
| 正しさの定義 | 「normalized accuracy, calculated as the agent's accuracy in predicting the individual's responses divided by the individual's own replication accuracy」 | ◎ |
| GSS | 「average normalized accuracy of 0.85 (std = 0.11), calculated from a raw accuracy of 68.85% (std = 6.01) divided by participants' replication accuracy of 81.25% (std = 8.11)」。偶然の正答は 27.03%(1 問あたり平均 3.70 択) | ◎ |
| 比較 | 属性だけ(年齢・性別・人種・政治的立場)は 0.71(生 57.00%)、本人が書いた人物紹介は 0.70(生 56.79%) | ◎ |
| 経済ゲーム | 正規化した相関 0.66。経済ゲームの MAE は 3 種のエージェントで差がない(F(2, 3153) = 0.12, p = 0.89) | ◎ |
| 版の改訂 | v3(2026-06-28)の抄録は「interview-only, survey-only, and combined agents achieved accuracies equal to 83%, 82%, and 86%」「compared with 74% for demographics-only agents」。v1 の 85%/0.71 から変わっている | △ |

- **フロア**: 人が自分の答えを 2 週間後に再現できるのは 81.25% です。どのエージェントも、これを超える正しさは測れません。正規化の分母がこのフロアです。
- 読み方: GSS の 85% は「意見の質問紙」での値です。行動(移動・購入)の再現率は、この論文では経済ゲームと実験の再現だけでした。渋谷の判断(行き先・店・時刻)の再現率は空欄です。

### 1-2 繰り返し報告されている弱点

| 弱点 | 出典 | 値(原典か抄録の逐語) | 等級 |
|---|---|---|---|
| ばらつきが小さすぎる | Bisbee 2024(#4) | 「there is less variation in responses than in the real surveys」。係数は「48% of coefficients estimated from the ChatGPT responses are statistically significantly different」、そのうち「the sign of the effect flips 32% of the time」。同じ問いが 3 か月で「significantly different results」。検出力の計算では、ChatGPT の値なら 99% の検出力に要る人数は 33 人で、ANES の値によるものより「almost an order of magnitude less」 | ○ |
| 平均の再現と属性ごとのずれ | Argyle 2023(#3) | 条件づけすれば部分集団の答えの分布を再現できる(「algorithmic fidelity」)と主張。限界の数値は抄録に無い | △ |
| 意見の偏り | Santurkar 2023(#2) | 米国の 60 の属性集団と比べたずれは「on par with the Democrat-Republican divide on climate change」。集団を指定して誘導しても残る。65 歳以上・死別した人の意見が特に写らない | △ |
| 正確すぎる | Aher 2023(#5) | Wisdom of Crowds の再現で「hyper-accuracy distortion」(ChatGPT・GPT-4 を含む)。最後通牒ゲーム・ガーデンパス文・Milgram は再現 | △ |
| ステレオタイプ化 | Cheng 2023(#6) | GPT-3.5・GPT-4 の人物描写は、同じ指示で人が書いたものより人種のステレオタイプが多い | △ |
| 集団を平たくする | Wang 2025(#7) | 4 つの LLM・3,200 人・16 の属性で「misportray and flatten」を実証 | △ |
| 協力的すぎる | Brookins & DeBacker 2024(#9) | 囚人のジレンマで GPT-3.5 の協力は 65.4%(1,000 回超)、人は 37%(Mengel 2018 のメタ分析)。独裁者ゲームで 50-50 を約 70% | ◎ |
| 協力的すぎる(分布の端) | Mei 2024(#10) | GPT-4 は 108,314 人の分布の中に収まり「statistically indistinguishable」。平均から外れるときは「more altruistic and cooperative」の側。自分と相手の利得の平均を最大化しているように振る舞う | △ |
| 経済主体としての使い方 | Horton(#8) | LLM を Homo silicus として古典実験を再現し、質的に似た結果。協力性の数値は抄録に無い | △ |
| 言い回しへの敏感さ | Sclar 2024(#11) | 意味の同じ書式の違いで LLaMA-2-13B に「up to 76 accuracy points」。大きいモデル・例示の追加・指示調整でも消えない | △ |
| 人と同じ向きに動かない | Tjuatja 2024(#12) | 9 モデルで、質問紙の言い回しによる偏りを人のようには示さない。特に RLHF 済みで顕著。人が動かない摂動に動く | △ |
| 選択肢の順序 | Pezeshkpour 2024(#13) | 選択肢を並べ替えると「approximately 13% to 85%」の性能差 | △ |
| 最後の選択肢を選ぶ | Rupprecht 2025(#14) | 9 モデル・10 種の摂動・167,000 件超。全モデルに「consistent recency bias」 | △ |

- **フロア(人どうしのばらつき)**: Brookins の比較では、人の研究どうしの協力率の幅が 0.04〜0.84 でした(原典本文)。GPT の 65% はこの幅の中です。「人より協力的」は平均の比較の話で、研究ごとの違いの幅と並べて書く必要があります。

### 1-3 8B 級で弱点が強く出るか

| 報告 | 値 | 等級 |
|---|---|---|
| Rupprecht 2025(#14) | 「While larger models are generally more robust, all models remain sensitive to semantic variations like paraphrasing」 | △ |
| Chen 2026(#15) | 「four models spanning two families and an 8B-to-frontier capability range」で「Neither failure is remedied by a larger, more capable model」。モデルは属性を実際より強く効かせ、区分の間の差を 2〜4 倍にふくらませる | △ |
| 基盤モデルか指示調整済みか | 基盤モデルの方が人の答えの分布に近いという報告(Pew ATP・6 組の比較)と、Santurkar の同趣旨の観察 | △(検索要約のみ。原典の特定は空欄) |

- まとめ: 小さいモデルの「答えが散る」は雑音で、人のばらつきの再現ではありません。大きくしても、属性を過大に効かせる誤りや平たくする誤りは残ります。8B 級で弱点が特に強いと示した原典は見つかりませんでした(空欄)。

### 1-4 検証の 3 段と摂動の試験(先行例)

| 先行 | 中身 | 等級 |
|---|---|---|
| Larooij & Törnberg 2026(#16) | 生成 ABM の検証は「believability」の主観評価に頼るものが多く、厳密なものでも operational validity を十分に示していない。マクロの現象を説明できても、それは十分条件で必要条件ではない | △ |
| TRAILS(#17) | 頑健性の監査を「agent (micro-level), interaction (meso-level), and system (macro-level)」の 3 段に分ける。囚人のジレンマで人物の書式と指示の言い回しを少し変えただけで協力率が「up to 76 percentage points」動いた。同じ摂動が別のモデルでは 1 ポイントしか動かさなかった。「Robustness is therefore a property that should be measured per claim and per model」 | △ |
| Compared to What?(#18) | 1 つの要因だけを変える試験は、意味を変えない言い換えでのぶれと比べないと帰属できない。MedQA で患者の性別を変えた反転率 14.9% と、言い換えだけの 14.1% は統計的に区別できなかった。MedPerturb の再分析では有意は 120 中 5 | △ |
| Instability Floors(#19) | 何も変えずに 10 回再実行しただけで行動が 8.7% 変わった。行動ごとに 2.2〜17.9%、6 モデルで 2.5〜23.7%。「a flip rate inside the floor is not evidence of fairness」。5 回の多数決で床の 39% が消えた | △ |
| Counterfactual invariance(#20) | 無関係な部分を変えても予測が変わらないことを「counterfactual invariance」と定式化 | △ |

## §2 B: 人が立ち止まって考える頻度

### 2-1 「よく考える」の割合の監視に使える値

| # | 量 | 値 | 何の代わりになるか | 出典・等級 |
|---|---|---|---|---|
| B1 | 欲求のある瞬間の抵抗 | 応答の約 21%(派生値) | 熟考の下限の代わり | R-39(Hofmann 2012)・既存 |
| B2 | 習慣と分類された行動の割合 | Study 1 で 35%、Study 2 で 43%。逐語「between a third and a half of all behaviors listed were classified as habits」「This estimate was greater in Study 2 (43%) than in Study 1 (35%)」。学部生 70 人・209 人の 1 時間ごとの日記。習慣の定義は「just about every day and usually in the same location」 | 熟考しない行動の割合の上の目安。残り 57〜65% が習慣でない行動 [再計算] | #21 ◎ |
| B3 | 行動中に考えが行動と一致した割合 | 習慣でない行動では 70%(Study 1)・60%(Study 2)、習慣では 40%・44%(逐語「for nonhabitual behaviors, thoughts were more likely to correspond with behaviors (M = 70%)」) | 「今していることを考えている」割合。熟考そのものではない | #21 ◎ |
| B4 | 棚の前の滞在 | 平均 12 秒、見た銘柄は平均 1.2・大きさ 1.1。選んだ銘柄の値段を見たのは 58%、他の銘柄の値段を見たのは 22% 未満。800 人・4 店・4 品目 | 購入(H8-3 で最初に置き換える判断)で「比べた」割合 | #25 ○ |
| B5 | 心のさまよい | 標本の 46.9%(2,250 人)。性行為を除くどの活動でも 30% 以上 | 今の行動を考えていない割合の上限側 | #22 ○ |
| B6 | 心のさまよい(学生) | 週の平均 32%(SD 17%・範囲 2〜97%・274 人)。Kane 2007 の約 30% と一致 | 個人差の幅 | #23 ○ |
| B7 | 測り方による幅 | 答えの選択肢しだいで「from approximately 60% to 10%」 | B5・B6 の測定のフロア | #24 △ |
| B8 | 熟考なしの方が良いか | 熟考なしの方が良い選択になるとした Dijksterhuis 2006 は、N = 399 の再現で「no evidence for the UTA」 | 「考えない方が良い」を前提にしない根拠 | #26 △ |
| B9 | System 2 の割合 | Kahneman は数値を出していない。「most of what you (your System 2) think and do originates in your System 1」(二次の抜き書き) | 割合の錨にならない | #27 △ |
| B10 | 「95% は無意識」 | Zaltman 2003 の推定。測定ではない | 使わない | #28 △ |
| B11 | 「1 日 35,000 回の決定」 | 一次資料なし | 使わない | 既存(R-39・思考頻度ノート H9) |

- **フロア**: 心のさまよいは測り方だけで 10〜60% 動きます(B7)。同じ測り方でも人によって 2〜97% と散ります(B6)。「よく考える」の割合を 1 つの値に合わせるより、幅で監視するのが原典の示す扱いです。
- **Evans & Stanovich 2013 の定義**(Type 2 は作業記憶を要する。速さは定義ではない)は R-39 §1 の 5 にあるので再掲しない。

### 2-2 見つからなかったもの

- 「人が 1 日に何回、立ち止まって考えるか」の経験サンプリング: 見つからない(R-39 と同じ結論)。
- 消費者の熟考時間で、購入の種類ごと(食事・服・家電)に分けた日本の実測: 空欄。
- 行動のうち計画外の購入の割合(店内での決定): 業界調査の数値は見たが、原典を確かめていないので載せない(空欄)。

## §3 C: 画像による知覚

### 3-1 VLM の処理量と費用

| 量 | 値 | 出典・等級 |
|---|---|---|
| Qwen2-VL の画像トークン | 14 画素の切片を 2×2 で 1 トークンに縮める。「an image with a resolution of 224×224, encoded with a ViT using patch_size=14, will be compressed to 66 tokens」(64 + 開始と終了の 2)。視覚の部分は 675M パラメータで、言語モデルの大きさに関係なく同じ | #29 ○ |
| 解像度とトークン数の目安 | 1 トークン = 28×28 画素。448×448 なら 256 + 2 = 258 トークン [再計算] | #29 からの再計算 |
| LLaVA-1.5 | CLIP-ViT-L-336px。336 ÷ 14 = 24、24 × 24 = 576 トークン [再計算] | #30 △ |
| Clef(Workers AI) | 画像は 4 枚まで(「4 MiB and 16 megapixels each, 8 MiB total decoded」)。文脈長 65,536。入力 $0.24 / 100 万トークン。画像 1 枚あたりのトークン数は記載なし | #31 ○ |
| Clef の画像トークン数 | 空欄。基盤の Qwen3.8-27B が Qwen2-VL と同じ 28×28 画素/トークンなら 448×448 で約 258(推測) | なし |
| 自前ホストの処理量 | JEV-27B-VL: B200 1 枚で画像 6 枚つき 4,000 件を 316 秒(約 13 件/秒) | R-83 §2(既存) |

### 3-2 住民ごとの景色を描く費用

| 量 | 値 | 出典・等級 |
|---|---|---|
| 室内の具身シミュレータ | Habitat-Sim は Matterport3D の場面で「several thousand frames per second (fps) running single-threaded, and can reach over 10,000 fps multi-process」(GPU 1 枚) | #32 △ |
| 渋谷のテクスチャ付き LOD2 の表示 | Cesium(ブラウザ)で渋谷の 12 条件のうち 5 条件はメモリ上限を超えて描画に失敗した。描けた 7 条件では最低 1〜3 FPS・描画後 60 FPS・メモリ 1,058.4〜1,726.5 MB・初期読込 8.64〜15.27 秒。逐語「渋谷のような範囲当たりのテクスチャの量が多い場合には、画像のまとめ方での描画性能の向上では限度がみられた」 | #40 ◎(表 3-11) |
| 壁面のテクスチャの質 | 「LOD2 建物作成時に使用する一般的なデータセットは、航空写真の直下視画像（地上解像度20～25 cm 程度）である」「壁面は引き伸ばされた画像になりやすい」。超解像(6.25 cm 相当)でも、ボケの改善で A ランクは 51%、壁面らしい画像は約 62%(川崎市 544 棟) | #40 ◎ |
| 航空写真の規定 | 第 24 条: LOD2.0 は地上画素寸法 0.25 m 以内、LOD2.1 は 0.15 m 以内、LOD2.2 は 0.08 m 以内 | #41 ◎ |
| 都市の具身シミュレータ | EmbodiedCity: 北京の 2.8 km × 2.4 km を Unreal Engine 5.3 で作り込み、AirSim で一人称の RGB・深度を出す。描画の処理量は空欄 | #35 △ |
| 都市規模で 1 人 1 枚を描く処理量 | 空欄(PLATEAU の渋谷で 1 視点あたり何秒かの実測は見つからない) | なし |

### 3-3 先行例

| 先行 | 中身 | 等級 |
|---|---|---|
| Touchdown(#33) | 実在の街の画像環境で、英語の道案内 9,326 例。道をたどったあと、言葉で書かれた場所を見つける | △ |
| StreetLearn(#34) | Google StreetView の写真で都市の移動を強化学習。数 km 先の目的地まで、地図なしで移動を学ぶ | △ |
| 360CityArena(#36) | 東京・秋葉原を 360° 動画 602 本(85 の通り)で再構成。175 の課題で、人 77.3% に対し最良の Gemini 2.5 Flash は 17.1% | △ |
| Place Pulse 2.0(#37) | 56 都市の 110,988 枚に 1,170,000 の対比較。「安全」「にぎやか」など 6 つの印象 | △ |
| Mapillary 標識データ(#38) | 世界の街路画像 100K 枚・300 超の標識の種類 | △ |
| 避難誘導標識の検知(#39) | 「38% (31/82) of participants unfamiliar with the building layout and 30% (16/54) of participants familiar with the building layout are likely to perceive the sign」。気づいた人のうち 97%(30/31)・94%(15/16)が従った。0.1 × 0.3 m の反射式標識、照明は良好、開けた通路。被験者 68 人。視認範囲(VCA)の中で、標識の方へ動いているときの検知確率として buildingEXODUS に実装 | ◎ |

- 渋谷の商業看板に「気づく」割合の実測は見つからない(空欄)。#39 は避難時の誘導標識なので、商業看板にそのまま写せない。広告の注視の錨は[広告答申](v2-ad-information-research.md)と [R-51](v2-r51-mere-exposure-incidental-ads-research.md) にある。

### 3-4 描き方に設計者の恣意が入る点(整理)

文献の値ではなく、本書の整理(expedient・未リサーチ)です。

1. **何を描くか**: PLATEAU の LOD2 は壁面が直下視の写真を引き伸ばしたもので(#40)、看板の文字はほぼ写りません。看板を描き足すと、その位置・大きさ・色・明るさを設計者が決めることになります。
2. **どう写すか**: 目の高さ・画角・解像度・時刻の光の 4 つで見え方が変わります。解像度はトークン数も決めるので(§3-1)、費用の都合で解像度を下げると「見えない」が増えます。
3. **他人をどう描くか**: 混んで見えるかの判断には人の描画が要ります。人の形・服・密度の描き方は画像に直接出ます。
4. **VLM の癖**: 画像の判断も §1-2 と同じ弱点(言い回しへの敏感さ・順序効果)を持つと考えられます(推測)。360CityArena の人との差(77.3% 対 17.1%)は、街の画像の空間判断がまだ弱いことを示します。

## §4 D: v2 への当てはめ(親の案)

ここから下は親が設計ラウンドに出すための**案**で、決定ではありません。数値の見積りはすべて推測です。

### 4-1 検証の 3 段(認知の設計ラウンド H1・H7・H8 向け)

R-83 の H8-6(個体・小集団・群衆)に、本書の先行を足す形です。

| 段 | 何を比べるか | 錨・床 | 先行 |
|---|---|---|---|
| 個体 | 状況を固定した場面(D-100 の再問い評価器)で、選択の分布 | 床 1 = 同じ入力の再実行のぶれ(#19)。床 2 = 本人の再現性に当たるもの(#1 の 81.25%)。人の側の同じ場面の分布は PT 2018 など | #1・#19 |
| 小集団 | 世帯・職場・連れでの組み合わせ(誰と行くか・割り勘・待ち合わせ) | 協力・利他の偏り(#9・#10)。人の研究どうしの幅 0.04〜0.84 を併記 | #9・#10・#17 |
| 群衆 | 行き先・手段・時刻の割合(PT 2018・人流) | 既存の holdout(H1〜H5)。属性の過大な効き(#15)は区分ごとの差の比で監視 | #15・#16 |

- 3 段とも Jev 型・(G)・D-119 を並べる(R-83 H8-6 と同じ)。
- 監視の欄の案: 各段で「平均のずれ」に加えて「ばらつきの比(LLM の分散 ÷ 人の分散)」を出す。Bisbee の指摘(平均は合うがばらつきが小さい)を拾うため。

### 4-2 摂動の試験(counterfactual probing)の形

| 腕 | 変えるもの | 目的 |
|---|---|---|
| P0 再実行 | 何も変えない(同じ入力を N 回) | ぶれの床。#19 は 10 回 |
| P1 言い換え | 意味を変えない言い換え・書式・選択肢の順序 | 言い回しの床(#18)。順序効果(#13・#14)もここで測る |
| P2 1 要因 | 空腹・所持金・時刻・天気・同行者・年齢など 1 つだけ | 判断が「理由のある入力」に反応するか |
| P3 無関係 | 名前・ID・関係のない文 | 反応してはいけないものに反応しないか(#20 の不変性) |

- 判定: P2 の変化が P0 と P1 の床を統計的に超えたときだけ「その要因に反応した」とする(#18 の方法)。
- 人の向きとの照合: P2 の変化の向きを、人の錨(例: 空腹なら食事を選ぶ割合が上がる)と比べる。Tjuatja(#12)の「人が動かない摂動に動く」は P3 で拾う。
- 費用(推測): 1 場面 × 腕 4 × 10 回 × 要因 6 程度でも、Jev 型の 1 回の計算は数十 ms 台なので、数千場面でも GPU 1 枚で数時間以内と見込む(R-83 の Clef-flash 中央値 38.8 ms を根拠にした推測)。

### 4-3 熟考の割合の監視の欄

| 欄 | 中身 | 比べる錨 |
|---|---|---|
| deliberate_rate | 決定モデルが「よく考える」を選んだ割合(全体・判断の種類別) | 下限 B1(約 21%)。習慣でない行動の割合 57〜65%(B2 の残り)を上限側の目安にする(推測の解釈) |
| deliberate_rate_purchase | 購入の場面での「よく考える」の割合 | B4(他の値段を比べた 22% 未満・選んだ品の値段を見た 58%) |
| habit_share | 繰り返しの自動化で LLM を呼ばなかった割合 | B2(35%/43%) |
| conflict_when_deliberate | 「よく考える」を選んだ場面の葛藤と驚きの点数の分布 | §7-3 の記録。選ばなかった場面と比べる |
| person_spread | 人ごとの deliberate_rate の分布 | B6 の人ごとの幅(2〜97%)。全員が同じ割合なら画一性(D-68)の兆し |

- 1 つの値への合わせ込みはせず、幅(B1〜B2)に入っているかと、人ごとに散っているかを見る案です。

### 4-4 画像の腕(GPU 後・看板 1 つ)

- **問い**: 「この看板を見たか(はい/いいえ)」だけ。
- **腕**: (0) エンジンの規則(視認範囲の中で、標識の方へ動いているとき 38%。#39 の形を expedient で借りる) / (1) 文章の腕(看板の位置・大きさ・距離を文で渡す) / (2) 画像の腕(その人の位置と向きから描いた 1 枚を Jev 型の画像入力で渡す)。
- **恣意を減らす工夫**: 描き方の仕様(目の高さ・画角・解像度・光)を結果を見る前に固定して記録する。仕様を 2 通り用意して感度の腕にする。
- **人の錨**: 避難誘導標識の 38%/30%(#39)は形の参考にとどめる。商業看板の注視の錨は広告答申・R-51 から取る。
- **費用の見積り(すべて推測)**:
  - 画像 1 枚 448×448 で約 258 トークン(Qwen 系と同じ方式と仮定)。
  - 看板 1 つの視認範囲を通る人を 1 日 10 万回と置くと、10 万枚・約 2,600 万トークン。Workers AI の単価なら約 6 ドル/日。
  - 自前ホストで JEV-27B-VL 程度(約 13 件/秒・1 件に画像 6 枚)なら約 78 枚/秒で、10 万枚は約 21 分。
  - 39 万体 × 1 日 10 回の視覚判断に広げると 390 万枚で、約 14 時間(B200 1 枚)または約 240 ドル/日。
  - 描画の時間は空欄。渋谷のテクスチャ付きモデルは、ブラウザ表示でもメモリ上限に当たった(#40)。最初は看板のまわりだけを軽いモデルで描く案。

## §5 フロア併記の確認

- 「人より協力的」: 人の研究どうしの幅 0.04〜0.84(#9)を §1-2 に併記した。
- 「言い回しで答えが変わる」: 再実行の床 2.5〜23.7%(#19)と言い換えの床 14.1%(#18)を §1-4 に併記した。
- 「心のさまよい 46.9%」: 測り方の幅 10〜60%(#24)と人ごとの幅 2〜97%(#23)を §2-1 に併記した。
- 「Park の 85%」: 本人の再現 81.25% がフロア(分母)であることを §1-1 に書いた。

## §6 循環参照と版の検査

- Park 2024 は v1(85%)と v3(83%/82%/86%・属性だけ 74%)で数値が違う。設計書に写すときは版を書くこと。指示書 §7-3 の「85%」は v1 の値。
- Bisbee 2024 の「129 人と 16 人」は検索の要約にだけあり、出版社ページでは見つからなかった(99% の検出力で 33 人の記述はある)。本書には載せていない。
- Brookins & DeBacker の arXiv 番号として検索で出た 2305.07970 は、取得すると別の論文の抄録だった。本書は Economics Bulletin の PDF だけを出典にした。
- Kane 2007 の「30%」は、Kane 2017 の本文の再掲で確かめた。Killingsworth の 46.9% と混ぜて「30〜50%」と書く引用が多い(#24 が指摘)。
- Hui Xie の 2012 年の論文(Fire and Materials 36:367-382)は未読で、同じ値を博士論文(#39)で確かめた。

## §7 空欄

1. Park 2024 の 3 版の本文(v3 の 83%/82%/86% の内訳)
2. Park 2024 のエージェントが使った LLM の名前(v1 本文で GPT-4o の使用はインタビューの反省の生成で確認。エージェント本体は未確認)
3. 8B 級で弱点が特に強いと示した原典
4. 基盤モデルの方が人の分布に近いという報告(Pew ATP・6 組)の原典の特定
5. Mei 2024 の本文(出版社ページは 403)
6. Bisbee 2024 の ANES の値での必要人数
7. 人が 1 日に立ち止まって考える回数の実測
8. 購入の種類ごとの熟考時間の日本の実測
9. 計画外の購入の割合の原典
10. Clef の画像 1 枚あたりのトークン数
11. 渋谷の PLATEAU で 1 視点を描く時間
12. EmbodiedCity の描画の処理量
13. 渋谷の商業看板に気づく割合の実測
14. Kane 2007 の本文(30% は 2017 の本文の再掲で確認)
15. Xie ほか 2012(Fire and Materials)の本文
