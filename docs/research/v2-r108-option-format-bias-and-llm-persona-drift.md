# R-108 答申: 選択肢の形式の偏り(F7)と LLM が書いた人物像のずれ(F13)

<!-- hdr:v1 -->
- **分野**: 自然言語処理・機械学習 #27 / 計算社会科学 #25 / 人口学・合成人口論 #1 / 人格心理学 #13 | **重要度**: P1(指示書 10-12 §4-12 C-2 の「原典を確かめてください」・計画 §2 の 1-8 候補の口 J0・第 4 期 4-1b の根拠。リサーチの指示書 §2 F7 と冒頭の注記の F13)
- **一次確認**: **B+**(サブの自己評価。本文を PDF から自分で抽出して読んだ原典 11・抄録や二次や検索結果だけ 7・読めなかった 1(計 19)。F13 の効果の大きさは論文に表が無く、図を目で読んだ概数しか出せない=§2-3)・**親検収**: 済(第329・2026-10-12)。親が arXiv v4 の表 2・表 3 で RStd 5.5/3.8/4.5・23.0/4.1・Cyclic Perm ×4 −8.7/+4.9・PriDe ×1.15 を確認、Li ら 2503.16527 は v1 のみ・NeurIPS 2025 ポスターを確認。訂正の伝播 2 件(lit ノートの「総当り」→巡回・深掘り 面 2 の Meta>Tabular>Descriptive)を親が直した。等級 **B+** のまま
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-12・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ。arXiv の PDF はスクラッチに置いて pymupdf で本文を抽出した。NAACL 版の PDF(#3)は取得ツールが自動で残した写しを pymupdf で抽出した。リポの `data/` には何も取得していない(`data/research_cache/r108/` は作っていない)。コミットなし・台帳/設計書/草案/src は未編集。
> 既存答申との関係: Zheng 2024 の数値は [lit ノート](lit/nlp__zheng2023_selection-bias.md)(サブ実読・親未確認)と [目的地選びの答申](v2-destination-choice-llm-research.md) §3-1・§3-2 にある。本書はその**一次確認**(写し検査を含む §1-1)と、そこに無い項目(記号の変更・理由を先に・小さなモデル・「その他」)だけを足す。Tam 2024 の表 1・表 2 は [観測の形式の答申](v2-observation-format-research.md) 1-a にあり再掲しない(本書は理由と答えの順・反論だけ)。Pezeshkpour 2024 は R-88 #13 と目的地選びの答申が抄録だけで引いている(版の違いを §1-2 で整理)。Li ら 2025 は [ペルソナと人口の深掘り](v2-persona-population-deep-research.md) 面 2 と [D-68 の答申](v2-d68-behavioral-diversity-research.md) が要旨で引いている(§2-4 で写し検査)。即断ほかの段階の語の第 1 水準を避ける偏りは [R-94](v2-r94-judgment-model-candidates-update.md)、数の偏りは [R-97](v2-r97-llm-numeric-output-bias.md)、LLM と人の対の値は [R-104](v2-r104-llm-agent-human-gaps-and-transit-app-accuracy.md)、LLM の人間らしさは [R-88](v2-r88-llm-humanlikeness-deliberation-vision.md) が担当(重ねない)。
> 比べる相手: [指示書 10-12](../design/v2-wallbounce-decisions-2026-10-12.md) §4-7(DM-0・DM1・DM4・DM5)・§4-12 C-2・§4-10 PS3、[実装の計画](../design/v2-implementation-plan-2026-10-12.md) §2 の 1-8 と 4-1b、[判断モデルの草案](../design/v2-decision-model-design-round-draft.md) §2-3 の C-2、[計画への回答](../design/v2-plan-answers-2026-10-12.md) 2-0b。**設計書・草案の決定項は書き換えない。**
> データの時点: 論文は 2023-08〜2026-04。日本語で測った研究は 1 本も見つからなかった(§空欄)。

## 結論(5 行)

1. **選択肢の記号への偏りは原典どおり大きく、記号を変えても消えない**: Zheng ほか(ICLR 2024)は 20 モデル・4〜5 択で、選択肢 ID ごとの再現率の標準偏差(RStd)が llama-2-7B で 23.0、llama-2-70B で 4.1(MMLU・0-shot・付録の表 3)。A/B/C/D を 1/2/3/4 に変えても gpt-3.5-turbo の RStd は 5.5 → 3.8 で「目立った減少なし」(表 2)。並べ替えの平均(×4 回)か事前分布の推定(PriDe・×1.15)が効く。Pezeshkpour ほか(NAACL Findings 2024)は並べ替えで正答率が最大 85 ポイント動く(Llama-2-13b-chat・表 1)。
2. **「理由を先に書かせる」は偏りの対策としては当てにならない**: gpt-3.5-turbo の CoT は RStd 5.5 → 4.5 で小さい(Zheng 表 2)。説明を先に書かせる MEC は InstructGPT の正答率を 5 課題すべてで下げた(Pezeshkpour 表 5)。Llama-3-8B では CoT で偏りが大きく減った例もある(Choi ほか 表 2)。思考モードでは考える長さとともに位置の偏りが増える、という 7〜8B の報告がある(Wang 2026・未査読)。形式の縛りで推論が落ちる件(Tam 2024)は、理由より先に答えを書く順になることが一因と原典が書いているが、反論もある(dottxt)。
3. **「その他(自由記述)」の欄が選ばれる割合を測った研究は見つからない(空欄)**。近い証拠は「当てはまるものが無い(NA)」が正解のときに LLM がそれを選びにくいこと: 28 モデル平均で正答率 0.738 → 0.350(Tam ほか 2025)、並べ替えに強い問題だけでも Llama-3-8B は NA を 18.3% しか選ばない(Wang ほか COLING 2025 表 2)。人の側も、閉じた質問では候補に無い答えをほとんど自分から言わない(Schuman & Presser 1979・未読 △)。
4. **F13 の原典は実在し、主張の向きは合っているが、強さは図だけ**: Li・Chen・Namkoong・Peng「LLM Generated Persona is a Promise with a Catch」(arXiv 2503.16527 v1・NeurIPS 2025 のポスター)。人物像を 4 段(国勢調査から引くだけ/閉じた候補の項目を LLM が埋める/開いた項目も LLM が埋める/自由な文章)で作り、6 つの公開モデルで約 100 万人分を生成した。米大統領選の州別の得票と比べると、LLM が書く量が増えるほど民主党寄りにずれ、自由な文章では全州で民主党が勝った(図 4)。人物像の文は感情の極性が正に寄り(図 8)、苦労の語が見当たらない(図 9 のワードクラウド・質的)。数値の表・有意性の検定は無い。図 5 では「閉じた候補の項目を LLM が埋めた段」が「引くだけの段」より現実に近い枠もあり、単調ではない。
5. **v2 への当てはめ(親が判断する材料・未決)**: 番号で返す口の 4 つの対策のうち、順のシャッフルは偏りを消すのではなく雑音に変えるので、モデルごとの ID の事前分布を計器として記録する案(PriDe 型。判断モデルが分布を返すので適用先がある)。「その他」は低い割合が「候補で足りている」証拠にならないので、正解の候補を抜いた対照で測る案。4-1b の腕は、Li らの 4 段に合わせて「LLM が埋めた項目」を閉じた候補と開いた項目に分け、書かせるモデルと住人のモデルの組の表(図 5 の形)で比べる案。

## §0 出典の表

印: **○** 本文を自分で抽出して読んだ / **△** 抄録・二次・検索結果だけ / **×** 読めなかった

| # | 著者・機関 | 年 | 題名・会場 | URL | 印 | 何に使ったか | 時点 |
|---|---|---|---|---|---|---|---|
| 1 | Zheng C., Zhou H., Meng F., Zhou J., Huang M. | 2024 | Large Language Models Are Not Robust Multiple Choice Selectors(ICLR 2024 Spotlight) | https://arxiv.org/abs/2309.03882 (v4・2024-02-22) | ○ | 記号の偏り・記号の変更・CoT・並べ替え・PriDe・小さなモデル(表 1〜3) | 2024-02 |
| 2 | Pezeshkpour P., Hruschka E. | 2023 | Large Language Models Sensitivity to The Order of Options in Multiple-Choice Questions(arXiv v1) | https://arxiv.org/abs/2308.11483 | ○ | v1 の表 1〜5(GPT-4・InstructGPT) | 2023-08 |
| 3 | 同上 | 2024 | 同題(Findings of NAACL 2024・pp.2006-2017) | https://aclanthology.org/2024.findings-naacl.130/ | ○ | 公刊版で足された Llama-2-13b-chat の表 1・「85%」 | 2024-06 |
| 4 | Tam Z.R., Wu C.-K., Tsai Y.-L., Lin C.-Y., Lee H.-y., Chen Y.-N. | 2024 | Let Me Speak Freely?(EMNLP 2024 Industry Track・会場は検索結果で △) | https://arxiv.org/abs/2408.02442 (v3) | ○ | 理由と答えの順・NL-to-Format・分類課題では縛りが効く | 2024-10 |
| 5 | Kurt W.(.txt / dottxt) | 不明(頁に日付なし) | Say What You Mean: A Response to 'Let Me Speak Freely' | https://blog.dottxt.ai/say-what-you-mean.html | △ | #4 への反論(取得ツールの要約。利害のある企業) | 不明 |
| 6 | Li A., Chen H., Namkoong H., Peng T.(Columbia University) | 2025 | LLM Generated Persona is a Promise with a Catch(arXiv v1 のみ) | https://arxiv.org/abs/2503.16527 | ○ | F13 の本文・付録のプロンプト・図 4/5/8/9 | 2025-03 |
| 7 | NeurIPS 2025 の頁ほか | 2025 | 同論文のポスター頁・ML Anthology・proceedings.com の書誌 | https://neurips.cc/virtual/2025/poster/121924 ・ https://mlanthology.org/neurips/2025/li2025neurips-llm | △ | 採択の確認(ポスター・NeurIPS 2025)。proceedings.com の「pp.73875-73896・doi 10.52202/085713-2226」は検索結果の要約だけ | 2025 |
| 8 | NeurIPS 2025 の position paper の track の頁 | 2025 | ブログ 2 本 | https://blog.neurips.cc/2025/10/02/reflecting-on-the-inaugural-neurips-position-paper-track-a-pilot-year-journey/ | △ | 2025 年に position paper の track が新設・採択 40 本(約 8%)。#6 がこの track かは頁に明記なし | 2025-10 |
| 9 | OpenReview(forum qh9eGtMG4H) | 2025 | #6 の審査の頁・カメラレディ版 | https://openreview.net/forum?id=qh9eGtMG4H | × | ブラウザ確認の画面で読めず。公刊版に数値の表が足されたかは**空欄** | - |
| 10 | Tam Z.R., Wu C.-K., Lin C.-Y., Chen Y.-N. | 2025 | None of the Above, Less of the Right(ACL Findings 2025 は検索結果で △) | https://arxiv.org/abs/2503.01550 | ○ | NA が正解のときの落ち込み・28 モデル(1B〜671B)の表 6・表 7 | 2025-03 |
| 11 | Wang H., Zhao S., Qiang Z., Xi N., Qin B., Liu T. | 2025 | LLMs May Perform MCQA by Selecting the Least Incorrect Option(COLING 2025) | https://arxiv.org/abs/2402.01349 | ○ | 並べ替えに強い問題で NA を選ぶ率(表 2) | 2025 |
| 12 | Tjuatja L., Chen V., Wu S.T., Talwalkar A., Neubig G. | 2024 | Do LLMs exhibit human-like response biases? A case study in survey design(TACL 12・会場は検索結果で △) | https://arxiv.org/abs/2311.04076 (v5) | ○ | 「わからない」を足したときの変化(opinion float)・順の逆転(付録の表 3) | 2024-02 |
| 13 | Choi H.K., Xu W., Xue C., Eckman S., Reddy C.K. | 2025 | Mitigating Selection Bias with Node Pruning and Auxiliary Options(ACL 2025 Main) | https://arxiv.org/abs/2409.18857 (v2) | ○ | 「わからない」の候補を足す AOI・Llama-3-8B の CoT(表 1・表 2) | 2025-05 |
| 14 | Wang X. | 2026 | More Thinking, More Bias: Length-Driven Position Bias in Reasoning Models(未査読・単著) | https://arxiv.org/abs/2605.06672 | ○ | 思考の長さと位置の偏り(7〜8B・表 1・§5) | 2026-04 |
| 15 | Ahnert G., Haensch A.-C., Plank B., Strohmaier M. | 2026 | Survey Response Generation(ACL 2026) | https://arxiv.org/abs/2510.11586 (v2) | ○ | 答えの出させ方 8 種 × 10 モデル(1B〜70B)・表 3 | 2026-04 |
| 16 | Verasight | 2026 | Synthetic Sampling Report IV | https://verasight.io/reports/synthetic-omnibus-survey | △ | 複数回答の選択肢を LLM が選ばない(取得ツールの要約) | 2026-01 |
| 17 | Schuman H., Presser S. | 1979 | The Open and Closed Question(ASR 44(5):692-712) | https://doi.org/10.2307/2094521 | △ | 人の床(候補に無い答えを自分から言わない)。検索結果の要約だけで本文は未読 | 1979 |
| 18 | Ranaldi L., Zanzotto F.M. | 2024 | HANS, are you clever?(*SEM 2024) | https://aclanthology.org/2024.starsem-1.25 | △ | CoT で最初の位置への偏りが減ったという報告(検索結果の要約だけ) | 2024 |
| 19 | (著者は未確認) | 2025 | Too Open for Opinion?(arXiv 2510.13884・立場の論文) | https://arxiv.org/abs/2510.13884 | △ | 閉じた形式が答えを候補へ寄せるという主張(検索結果の要約だけ) | 2025 |

数え方: ○ 11(#1・#2・#3・#4・#6・#10〜#15)・△ 7(#5・#7・#8・#16〜#19)・× 1(#9)。

---

## §1 F7 選択肢の形式の偏り

### 1-1 Zheng ほか 2024(#1): 記号への偏り

**設定**(本文 §2.1・付録 C)
- 20 モデル: llama-7/13/30/65B・llama-2-7/13/70B・llama-2-chat-7/13/70B・vicuna-v1.3-7/13/33B・vicuna-v1.5-7/13B・falcon-7/40B・falcon-inst-7/40B・gpt-3.5-turbo。
- 課題: MMLU と ARC(4 択)・CommonsenseQA(5 択)。2 択・3 択は元の問題から作った。記号は A/B/C/D/E。
- 公開モデルは記号のトークンの確率の最大を答えとし、gpt-3.5-turbo は温度 0 の最初のトークン。主は 0-shot、5-shot も行う。
- 指標: 選択肢 ID ごとの再現率の標準偏差(RStd)。大きいほど偏る。

**効果の大きさ**
- 逐語(要旨): 「they prefer to select specific option IDs as answers (like "Option A")」「this behavioral bias primarily stems from LLMs' token bias」。
- 正解の数を A/B/C/D 各 250 にそろえた 1,000 問で、llama-30B は A/B/C/D を 34.6% / 27.3% / 22.3% / 15.8%、gpt-3.5-turbo は 22.5% / 25.6% / 32.3% / 19.6% 選んだ(§1・10 回の平均・χ² 検定 p ≪ 10⁻⁴)。
- 正解を 1 つの位置へ動かす攻撃(表 1・0-shot MMLU): llama-30B 53.1 → 68.2(A)/ 41.2(D)。gpt-3.5-turbo 67.2 → 74.2(C)/ 60.9(D)。
- RStd(付録の表 3・0-shot・MMLU): llama-7B 18.5・llama-2-7B 23.0・llama-2-13B 7.5・llama-2-70B 4.1・vicuna-v1.3-7B 5.3・falcon-7B 24.2・falcon-inst-7B 28.7・gpt-3.5-turbo 5.5。
- 著者は「同じ系列で大きさとともに一貫した型は見えない」と書く(§2.3 逐語「we do not observe consistent patterns of selection bias within the same model family」)。7B の値が大きい枠は多いが、法則としては引けない(lit ノートの但し書きと同じ)。

**対策とその効き**
- **記号の変更**(表 2・gpt-3.5-turbo・0-shot): MMLU の RStd は 既定 5.5・a/b/c/d 6.8・1/2/3/4 3.8・(A)/(B)/(C)/(D) 8.1。ARC は 3.3・2.1・2.1・4.0。本文 §2.4 の逐語「observe no remarkable reduction in RStd from the default one」。
- **記号を外して中身を直接選ばせる**: RStd は MMLU 5.5 → 1.0・ARC 3.3 → 0.6(表 2)と大きく減る。ただし公開モデルでは中身の尤度を比べる方式(cloze)になり、正答率は落ちることが多い(付録の表 3: llama-2-13B MMLU 50.8 → 44.7)。著者は実用の対策ではないとした(§2.5)。
- **ID を混ぜる**(B/D/A/C などに入れ替える): RStd はほとんど変わらない(MMLU 5.5 → 5.1)。著者はこれを、位置ではなく記号のトークンが主因である根拠にした。位置の偏りは「somewhat present but quite irregular」(§2.4)。
- **偏りを除く指示と CoT**(表 2・gpt-3.5-turbo): 指示 RStd 6.1・CoT 4.5(既定 5.5)。ARC は 3.9・3.4(既定 3.3)。§2.6 の逐語「the two prompting strategies cannot mitigate selection bias well」。
- **並べ替えの平均と PriDe**(付録の表 3・20 モデルの平均の変化・RStd / 正答率): MMLU で 記号を外す −6.4 / −2.1、Cyclic Perm(×4)−8.7 / +4.9、PriDe 5%(×1.15)−7.6 / +1.2、40%(×2.2)−8.9 / +2.6、80%(×3.4)−9.1 / +4.1。llama-2-7B の MMLU は PriDe 5% で RStd 23.0 → 5.5・正答率 35.8 → 40.2。
- PriDe は、問題の 5% で選択肢の中身を巡回で並べ替えて ID の事前分布を推定し、残りの問題の予測からそれを割り引く。ラベルは要らない。推定した事前分布は領域をまたいでも使える(図 5)。

**写し検査(既存答申との突き合わせ)**
- lit ノートの表 3 の値・PriDe の平均・llama-2-7B の 23.0 → 5.5・表 1 の値は本文と一致した。
- **訂正候補**: lit ノートの「総当り置換(×4)−8.7 / +4.9」は、原典では **Cyclic Perm(巡回の並べ替え・×4)** の値。総当り(Full Perm)は CSQA では費用のため行っておらず、表 3 にも列が無い。
- 目的地選びの答申 §6 ④ の「PriDe は v2 の対象欄が自由文なので適用先が無い」は、その時点の v2 の形では正しい。J0 で番号で返す口になると前提が変わる(§3-1)。

### 1-2 Pezeshkpour & Hruschka 2024(#2・#3): 並べ替えによる正答率の幅

**設定**
- プロンプト(逐語): 「Choose the answer to the question only from A, B, C, D, and E choices. Question: {question}. Choices: {options}. Answer:」。
- 課題 5 つ: CSQA(5 択)・MMLU の Abstract Algebra・High School Chemistry・Professional Law(4 択)・BIG-bench の Logical Deduction(3 択)。
- モデル: arXiv v1 は GPT-4 と InstructGPT(text-davinci-003)だけ。**NAACL 版で Llama-2-13b(chat)が足された**。
- 指標「sensitivity gap」: 正解を知った上で並べ替えたときの正答率の最大と最小の差。

**効果の大きさ**(表 1・0-shot・素の正答率 / 最小 / 最大)
- GPT-4: CSQA 84.3 / −12.6 / +10.3・Logical Deduction 92.3 / −8.1 / +5.0(差 13.1)・Abstract Algebra 57.0 / −30.0 / +23.0。
- InstructGPT: Logical Deduction 64.0 / −39.4 / +34.7(差 74.1)・Abstract Algebra 33.0 / −31.0 / +39.0。
- Llama-2-13b(NAACL 版だけ): CSQA 62.2 / −28.9 / +25.5・Abstract Algebra 32.0 / −32.0 / +53.0(差 85)。
- **版の違い**: 要旨の幅は arXiv v1 が「13% to 75%」、NAACL 版が「13% to 85%」。85 は Llama-2-13b の Abstract Algebra の差。目的地選びの答申の「75%」は v1、R-88 の「85%」は公刊版で、どちらも写し間違いではない。
- NAACL 版は Llama-2-13b を表 1 だけで扱い、以降の分析は GPT-4 と InstructGPT に限る(§3.1 逐語「in the remainder of paper, we only focus on InstructGPT and GPT-4」)。

**原因の見立て**(§4・推測を含む著者の conjecture): 上位 2〜3 の候補で迷っているときに、位置の偏りが勝負を決める。並べ替えで答えが変わる問題について「複数の候補がありうるか」と聞くと、94% 超で「yes」と答えた。

**対策とその効き**
- **置き方**: 上位 2 候補を最初と最後に置くと偏りが増え、隣り合わせに置くと減る(表 3・表 4)。増やす置き方は元の幅の 20〜72%、減らす置き方は 0.9〜38% を再現した。
- **10 回並べ替えて多数決**(表 5): GPT-4 は +0.0〜+2.0、InstructGPT は +1.0〜+8.0(最大 8 ポイント)。
- **説明を先に書かせてから答える MEC**(Wang ほか 2023b の方式・表 5): InstructGPT は 5 課題すべてで下がった(CSQA −5.0・Logical Deduction −6.9・Abstract Algebra −2.0・Chemistry −5.4・Law −1.4)。GPT-4 は −3.1〜+5.3 で多数決と向きが食い違う。arXiv v1 の §5 逐語「the act of asking the models to explain their reasoning amplifies their uncertainty (partly due to hallucination)」「frequently guides the models to opt for answer among the top choices, which is positioned earlier in the available options」。
- **小さなモデル**: 公開の小さなモデルは Llama-2-13b-chat の表 1 だけ。対策の効きは測られていない。

### 1-3 Tam ほか 2024(#4): 形式の縛りと理由の順

- 表 1・表 2 の値は観測の形式の答申 1-a のとおりで、本文と一致した(LLaMA-3-8B の GSM8K Text 75.13 → JSON + schema 48.90 など)。
- **設定の補い**: モデルは gpt-3.5-turbo-0125・claude-3-haiku・gemini-1.5-flash・LLaMA-3-8B-Instruct・Gemma-2-9B-Instruct。課題は推論 3 つ(GSM8K・Last Letter・Shuffled Objects)と分類 4 つ(DDXPlus 49 択・MultiFin 5 択・Sports・Task 280)。出力の欄は「理由」と「答え」の 2 つに絞り、欄の名前を入れ替えて 9 通りのプロンプトで平均した(§3.2・§3.4)。
- **理由と答えの順**(§4.1 逐語): 「100% of GPT 3.5 Turbo JSON-mode responses placed the "answer" key before the "reason" key, resulting in zero-shot direct answering instead of zero-shot chain-of-thought reasoning」。§5.2 も「JSON-mode failed to adhere to the order of reasoning first followed by answer causing a large drop in final performance」。
- **分類では縛りが効く**(§4.1): 「stringent formats may hinder reasoning-intensive tasks but enhance accuracy in classification tasks requiring structured outputs」。v2 の判断は候補から選ぶ分類に近い(推測)。
- **NL-to-Format**(文章で答えてから形式に直す 2 段): 素の文章とほぼ同じ。LLaMA-3-8B だけ変換で少し落ちた(§4.1)。
- **反論**(#5・△・取得ツールの要約): 構造化出力の道具を作る企業(dottxt)が、同じ Llama-3-8B-instruct で作り直した。文章と構造化で GSM8K 0.77 / 0.78・Last Letter 0.73 / 0.77・Shuffle Object 0.41 / 0.44 と、縛った方が同じか良かった。原論文の問題点として、文章と構造化でプロンプトが違うこと、JSON-mode のプロンプトに JSON も形式も書いていないこと、答えの取り出しに別の LLM を使ったことを挙げる。利害のある当事者の未査読のブログなので、「縛ると落ちる」は**争いのある所見**として扱うのが安全(推測)。
- **小さなモデル**: LLaMA-3-8B と Gemma-2-9B が入っている(上記)。

### 1-4 理由を先に書かせると偏りは減るか(小さなモデルを中心に)

| 出典 | モデル | 結果 | 印 |
|---|---|---|---|
| Zheng 表 2(#1) | gpt-3.5-turbo | CoT で RStd MMLU 5.5 → 4.5・ARC 3.3 → 3.4。正答率はほぼ同じ | ○ |
| Pezeshkpour 表 5(#3) | InstructGPT・GPT-4 | 説明を先に(MEC)で InstructGPT は 5 課題すべて低下。GPT-4 は混在 | ○ |
| Choi 表 2(#13) | Llama-3-8B-Instruct | CoT で ARC の CKLD 0.494 → 0.050・正答率 52.3 → 66.2。MMLU-Redux 0.589 → 0.124。CSQA 0.095 → 0.025 | ○ |
| Wang X. 2026 §5(#14・未査読) | Llama-3.1-8B-Instruct・Qwen2.5-7B-Instruct・R1 蒸留の 7B/8B・DeepSeek-R1 671B | Llama は CoT で位置の偏り(PBS)が MMLU 0.40 → 0.24・ARC 0.26 → 0.09・GPQA 0.61 → 0.41。Qwen は 0.18 → 0.18 で変わらない。思考モードでは長さとともに増える(R1-Qwen-7B の MMLU で長さの 4 分位ごとに 0.107 → 0.151 → 0.213 → 0.385。13 構成中 12 で偏相関 ρ = 0.11〜0.41・p < 0.05)。途中で切って続きを生成させると、後で切るほど好まれる位置(A)へ移る割合が 16% → 32% | ○ |
| Ranaldi & Zanzotto 2024(#18) | 不明 | CoT で最初の位置への偏りが減った | △ |
| Ahnert 2026 表 3(#15) | Llama 3(3B/8B/70B)・OLMo 2(1B/7B/32B)・Qwen 3(8B/32B)ほか計 10 | 調査の答えの一致(F1)で、理由を先に書かせて選ばせる方式は、選ばせるだけの方式と同じくらいか少し下(ANES 2016 で係数 .138 対 .148)。要旨の逐語「reasoning output does not consistently improve alignment」 | ○ |

- Wang 2026 の PBS は、4 通りの巡回の並べ替えで平均した「位置ごとの選択の分布」と一様分布との L2 の距離(§3.3)。4 択・MMLU 1,000 問・ARC 496 問・GPQA 198 問。公開モデルは Q4_K_M に量子化して貪欲の生成(§4)。
- まとめ: 理由を先に書かせると、Llama 系の小さなモデルでは偏りが減る例がある。ただし効かないモデル(Qwen2.5-7B)もあり、説明が迷いを増やして前の位置に寄る例(InstructGPT)や、思考が長いほど偏る例(未査読)もある。**理由を先にしても、順のシャッフルと並べ替え試験の代わりにはならない**(推測)。

### 1-5 「その他」が選ばれにくい傾向

**「その他(自由記述)」の欄を LLM が選ぶ割合を測った原典は見つからなかった(空欄 R108-1)。** 近いものを 4 つ置く。

1. **NA が正解のとき**(Tam ほか 2025・#10): MMLU の問題で正解を「None of the above」に置き換えた。28 モデル(1B〜671B・0-shot の CoT)の平均の正答率は、元 0.738・NA が正解 0.350・NA が外れの候補 0.674(付録の表 7)。小さなモデルは Llama-3.2-1B 0.365 → 0.116・Llama-3.1-8B 0.795 → 0.316・Qwen2.5-7B 0.842 → 0.412・gemma-2-9b 0.802 → 0.385・Mistral-7B-v0.3 0.274 → 0.083。大きなモデルでも DeepSeek-V3 0.908 → 0.657。NA を外れの候補として足したときは元の順位とほぼ同じ(r = 0.994・図 5)で、NA に票が流れるわけではない。要旨の逐語「a consistent 30-50% performance drop across models regardless of scale」。
2. **並べ替えに強い問題だけで見ても**(Wang ほか 2025・#11・表 2): 全部の並べ替えで正しく答えた問題の正解を NA に置き換えると、0-shot の MMLU で LLaMA 3 8B 18.3%・LLaMA 2 13B 17.2%・ChatGPT-4o 60.3% しか NA を選ばない。著者の見立ては「最も間違っていない候補を選ぶ」。
3. **「わからない」を足したとき**(Tjuatja ほか 2024・#12・付録の表 3): 5 段の尺度に「わからない」を足すと、人では中央の選択が減る(opinion float)。LLM の変化(¯∆b・中央の選択の回数の減りの問いごとの平均。各問 50 回を温度 1 で引いた。表 2 の定義)は Llama2 7b 4.27(p < 0.001)・13b 4.13・70b 2.44 で人と同じ向き、Llama2 7b-chat −1.25(p = 0.283)・13b-chat −0.19(p = 0.870)で変化なし、gpt-3.5-turbo −11.9(逆向き)。**「わからない」そのものを選んだ割合は表に無い(空欄)**。同じ表で、順の逆転(人は前の候補に寄る)は Llama2 13b 45.8 と大きく、7b-chat −9.8 と逆向き。著者は RLHF をかけたモデルほど人らしくないとまとめた。
4. **複数回答で LLM が選ばない候補**(Verasight 2026・#16・△): 人 2,000 人の調査の複数回答の 77 候補のうち 27(35%)は人の 5% 超が選んだのに LLM の補完では 1% 未満、24(31%)は一度も選ばれなかった。GPT-5.2 を使用。

- **人の床**(フロア併記): 人も、閉じた質問では候補に無い答えをほとんど自分から言わない(Schuman & Presser 1979・#17・△・本文は未読)。v2 で「その他」の割合を人と比べるなら、人の「その他」も低いことを並べて書く必要がある(推測)。数値は**空欄 R108-2**。
- **「わからない」の候補を足すと残りの候補の偏りが減る**(Choi ほか 2025・#13・AOI): 「I don't know」を足し、答えはそれを除いた中から確率最大で選ぶ。Llama-3-8B の ARC で正答率 52.3 → 60.7・CKLD 0.494 → 0.231。Mistral-7B で 67.4 → 69.8・0.040 → 0.019(表 1)。逃げ道の候補が他の候補の選び方を変えることを示す。「その他」の欄も同じように他の候補の分布を動かしうる(推測)。

### 1-6 使える形の錨(F7)

| 錨 | 値 | 出典 |
|---|---|---|
| 記号の偏りの大きさ(7B 級) | RStd 5.3〜28.7(MMLU・0-shot。vicuna-v1.3-7B 5.3・vicuna-v1.5-7B 10.9・llama-2-chat-7B 13.5・llama-7B 18.5・llama-2-7B 23.0・falcon-7B 24.2・falcon-inst-7B 28.7) | #1 付録の表 3 |
| 記号の偏りの大きさ(65〜70B 級) | RStd 4.1〜12.8(llama-2-70B 4.1・llama-65B 8.3・llama-2-chat-70B 12.8) | 同上 |
| 記号の変更の効き | 1/2/3/4 で RStd 5.5 → 3.8(gpt-3.5・MMLU)。「目立った減少なし」 | #1 表 2 |
| 並べ替えの平均 | 20 モデル平均で RStd −8.7・正答率 +4.9(×4 回) | #1 付録の表 3 |
| PriDe | 20 モデル平均で RStd −7.6・正答率 +1.2(×1.15) | 同上 |
| 並べ替えで動く正答率の幅 | GPT-4 で 13.1〜53、Llama-2-13b で 85 ポイントまで | #3 表 1 |
| NA が正解のときの落ち込み | 平均 0.738 → 0.350(28 モデル)・8B で 18.3% しか NA を選ばない | #10 表 7・#11 表 2 |

### 1-7 次に頼むべきこと(F7)

- 日本語の選択問題での記号の偏り(数字・「①②③」・「ア・イ・ウ」)を測った研究の探索(空欄 R108-3)。
- 「その他(自由記述)」の欄の選択率を測った研究の再探索。キーワードの候補は「other (please specify)」「write-in option」「open option」「LLM survey」(空欄 R108-1)。
- Schuman & Presser 1979 の本文(JSTOR・有料の可能性)か、1981 年の本の第 3 章の数値(空欄 R108-2)。

---

## §2 F13 Li ら 2025 の一次確認

### 2-1 書誌

- **題名**(逐語): 「LLM Generated Persona is a Promise with a Catch」。ML Anthology は「LLM Generated Persona Is a Promise with a Catch」と大文字で表記。
- **著者**: Ang Li・Haozhe Chen・Hongseok Namkoong・Tianyi Peng(Columbia University)。NeurIPS の頁では筆頭が「Leon Li」と表示される。
- **arXiv**: 2503.16527 v1(2025-03-18)だけ。改訂版は無い。ライセンス CC BY 4.0。
- **会場**: NeurIPS 2025 のポスター(#7 の頁に「Poster」「2025 Poster」・OpenReview の forum qh9eGtMG4H)。ML Anthology は「Advances in Neural Information Processing Systems (NeurIPS 2025)」とする。本文は自分を「this position paper」と書く。2025 年の NeurIPS には position paper の track が新設され、採択は 40 本・約 8%(#8)。**この論文がその track の採択かは、どの頁にも明記が無く確かめられなかった(空欄 R108-4)**。
- **読んだ版**: arXiv v1(26 頁)。NeurIPS のカメラレディ版(proceedings.com の書誌では 22 頁)は OpenReview がブラウザ確認の画面になり読めなかった(#9)。公刊版で数値の表が足されたかは**空欄 R108-5**。
- 生成した人物像は約 100 万件を Hugging Face(Tianyi-Lab/Personas)で公開している(要旨)。

### 2-2 人物像の生成の段階の定義

本文 §2.1・図 3・付録 B。図 3 の説明の逐語「We categorize existing persona generation approaches into four tiers. Each tier adds more information generated by LLMs in generated personas to the previous tier.」

| 段 | 名前 | 中身 | LLM の関わり |
|---|---|---|---|
| 1 | Meta Persona | 年齢・性別・人種・州を、米国勢調査の同時分布から引く | なし(逐語「No LLM is involved in generating them」) |
| 2 | Objective Tabular Persona | 段 1 に、祖先・家の言語・学歴・就業・職業・収入・婚姻・世帯・出生地・退役・障害・保険などを足す | LLM が埋める。ただし値は国勢調査の区分の一覧から選ばせる(付録 B.2 の逐語「DO NOT ADD EXTRA INFORMATION OR ELABORATION TO THE VALUES」)。収入だけ「$0-$1,000,000」の範囲 |
| 3 | Subjective Tabular Persona | 段 2 に、仕事の説明・Big Five の点・癖・振る舞い・余暇・生活の様子・思想・支持政党・宗教・認知や視聴覚の困難・英語の力・出生数を足す | 思想と支持政党は一覧から。ほかは「reasonable and succinct description」で LLM が自由に書く(付録 B.3) |
| 4 | Descriptive Persona | 段 1 を条件に、自由な文章で人物を書く | 全部 LLM(付録 B.4 の逐語「create a detailed, diverse, and vivid persona」「Ensure diversity in perspectives, backgrounds, and personality traits」) |

- 州ごとに 1,000 人を段 1 で引き、それぞれから段 2〜4 を作った(§2.1)。6 つの公開モデルで約 100 万人分(§1)。
- 生成のシステムプロンプトは「detailed and unbiased persona generation」を求めている(付録 B.1)。
- **v2 の計画との対応**: 計画 4-1b の 3 段(属性だけ/属性 + LLM が埋めた項目/自由な文章)は、Li らの段 1・段 2〜3・段 4 に当たる。Li らは「LLM が埋めた項目」を、閉じた一覧から選ぶ段 2 と、開いた文を書く段 3 に分けている。

### 2-3 何を測って「一方向にずれた」と言っているか

**模擬の手順**(§2.2・付録 A・B.5)
- モデル 6 つ: Athene-70B・Llama 3.1 8B・Llama 3.1 70B・Mixtral-8x7B-Instruct-v0.1・Nemotron-70B・Qwen2.5-72B。人物像を書いたモデルと、答えを模擬するモデルの組を全部試した(cross-simulation)。
- 選択式の問いに 1 回だけ答えさせる。プロンプトの逐語「Choose ONE option (A, B, C, or D depending on the number of options)」「Always pick an option, even in unclear cases - treat it as a forced-choice survey」「Output format: 'Answer: [Letter]' only, no explanation needed」。
- 選んだ記号の数を人口で集計する(付録 A.3)。**選択肢の順の入れ替え・温度・seed の記載は無い**(本文に shuffle・order・temperature・seed の語が出てこない)。中立を促すプロンプトの変種も試したが「no substantial performance differences」(§2.1)とだけある。

**指標と効果の大きさ**
1. **大統領選**(§3.1・図 4・図 5): 指標は Santurkar ほか 2023 の一致度 1 − W(p̂, p)(W は模擬の支持率と実際の得票率の Wasserstein 距離・高いほど現実に近い)。
   - 図 4(人物像と模擬がともに Llama 3.1 70B): 2024 年は、段 1 と段 2 は赤い州が多く現実に近い。段 3 は 1 州だけ赤く、段 4 は全州が青(民主党)。2016 年と 2020 年も同じ向きで、学習データに入っている過去の選挙でも直らなかった(本文の逐語「a similar pattern of leftward drift」)。図を見ると、段 1 でも 2016 年と 2020 年は現実より青い州が多い。LLM が書いていない段でも模擬の段階で既にずれている(図から読んだ・推測)。
   - 図 5(一致度・縦軸 0.45〜0.9・**数値の表は無く、以下は図を目で読んだ概数**): 段 2(紫)はおおむね 0.65〜0.9、段 3(橙)と段 4(赤)はおおむね 0.45〜0.65 に集まる。段 1(星)は 0.6〜0.9。差が最も大きいのは段 2 から段 3 への移り(0.2〜0.3 ほど)。段 3 と段 4 の上下は枠で入れ替わる。**段 2 が段 1 より高い枠もある**(例: 模擬が Llama-8B の 2016 年で段 1 約 0.78 に対し段 2 は約 0.81〜0.89。模擬が Qwen2.5-72B の 2020 年で約 0.79 に対し約 0.82〜0.88)。
   - 著者は図 5 から「this type of bias is not model-specific but rather universal」とする。有意性の検定・信頼区間は無い。
2. **5 領域 20 問**(§3.2・図 6): 気候・消費・教育・娯楽・技術。現実の正解は無く、傾きを見るだけの質的な比較。段 4 に近づくほど、環境に良い高い車・人文系の専攻・「La La Land」(対「Transformers」)を選ぶ側へ寄った。本文の逐語「shifts perspectives from traditional to progressive」。
3. **OpinionQA の最初の 500 問**(§3.2・図 7): 段ごとの一致度の値は図にも表にも無い。図 7 は「段の間で一致度がどれだけ散らばるか」の話題別の順位だけ(性の見方 約 0.77 が最大・「2050 年のアメリカ」約 0.05 が最小)。
4. **人物像の文そのもの**(§4・図 8・図 9): TextBlob で感情の極性と主観性を測った(段 2〜4 だけ)。図 8 を目で読むと、極性は 段 2 約 0.03・段 3 約 0.04・段 4 約 0.16、主観性は 約 0.17・約 0.36・約 0.44。本文は「significantly more positive」と書くが、検定は示していない。図 9 はフロリダの段 4 のワードクラウドで、逐語「Notably absent are terms reflecting life challenges, social difficulties, or negative experiences」。**「苦労の語が無い」は 1 州のワードクラウドからの質的な所見で、数えた値は無い。** なお本文 §4 は感情の図を「Figure 10」と呼ぶが、実際は図 8(図 10 は付録の Yi-34B の地図)。
5. **向きはモデルによって逆になる**(付録 A.2): Yi-34B-Chat は右寄りへ大きくずれた。著者の逐語「most language models exhibit a significant bias toward politically left-leaning perspectives」。

**まとめ**: 「LLM が書き足す量が増えるほど模擬の結果が一方向にずれた」は、段 1・段 2 と段 3・段 4 の間の差としては図で支えられる。各段の間で単調に悪くなるわけではない。「一方向」は米国の政治と意見で民主党寄り・進歩寄りの向きで、モデルによっては逆向き(Yi-34B)もある。「前向きで苦労の少ない人物像」は、感情の極性(図 8)とワードクラウド(図 9・質的)が根拠。

### 2-4 写し検査(設計書・既存答申の書き方との突き合わせ)

| 書かれている所 | 書き方 | 原典との突き合わせ |
|---|---|---|
| 計画 4-1b・回答 2-0b・ペルソナの設計書 | 「LLM が書き足す量が増えるほど模擬の結果が一方向にずれ、人物像が前向きで苦労の少ない方へ偏った」 | 向きは合う。強さの数値は原典に無い(図だけ)。「苦労の少ない」は質的。「一方向」は米国の政治の左寄りで、モデルで逆もある(§2-3)。NeurIPS 2025 の採択は確認(track の名前は空欄) |
| ペルソナと人口の深掘り 面 2 | 「Meta(実統計のみ)>Tabular>Descriptive(自由記述)の順で現実整合が良い」 | **一部が合わない**。図 5 では閉じた一覧の段 2 が段 1 と同じか上の枠がある。崩れるのは開いた項目と自由な文章(段 3・段 4)。Tabular を段 2 と段 3 に分けると原典に合う |
| 同上 | 「人生の困難・社会的困窮・ネガティブ経験の語が系統的に欠落=裾の片側切除」 | 「欠落」は図 9(フロリダ 1 州のワードクラウド)の質的な所見。「系統的」は著者の推測(逐語「suggesting LLMs may be systematically avoiding」)。数えた値は無い |
| D-68 の答申 | 「裾の片側切除(2503.16527)」 | 上と同じ。深掘りの再掲 |

### 2-5 4-1b の腕の設計に借りられる手順

1. **段を 4 つにする**: 「LLM が埋めた項目」を、閉じた一覧から選ぶ段(Li の段 2)と、開いた文を書く段(段 3)に分ける。原典で崩れが大きいのは段 3 からなので、3 段では原因が混ざる(§2-3)。
2. **書かせるモデルと住人のモデルの組の表**(Li の図 5): 「人物像を書いた LLM」を行、「住人として判断した LLM」を列にし、全部の組で一致度を出す。生成の偏りと模擬の偏りを分けて見られる。
3. **段 1 の値を床として必ず置く**: Li の図 4 では、LLM が書いていない段 1 でも現実から少しずれている。段ごとの差は段 1 との差で読む。
4. **人物像の文そのものの計器**: 感情の極性と主観性(Li は英語の TextBlob)。日本語で同じことをする辞書や道具は未リサーチ(空欄 R108-6)。苦労の語は、Li のようにワードクラウドを目で見るのでなく、v2 の合成人口の属性(失業・障害・病気・一人暮らしの高齢者・低所得など)の割合と、文に出てくる割合を突き合わせる形にできる(案・推測)。
5. **一致度の物差し**: Li は 1 − Wasserstein(Santurkar ほか 2023 と同じ)。v2 で比べる現実データは検証専用の一覧から事前登録で選ぶ(回答 2-0b)。
6. **Li にない手当て**: Li は選択肢の順を入れ替えず、記号で答えさせ、理由を書かせていない。腕の間で同じ偏りがかかるので段の間の差は大きくは崩れないと見られるが(推測)、v2 の腕では §1 の対策(順のシャッフル・並べ替え試験)を全段で同じにかける。

### 2-6 次に頼むべきこと(F13)

- NeurIPS のカメラレディ版(OpenReview か proceedings)の本文。数値の表と検定が足されたか。track の名前(空欄 R108-4・R108-5)。
- 著者の後続の研究(人物像の較正の方法)があるか。
- 日本語の文の感情の極性を測る辞書や道具(ライセンスを含む・空欄 R108-6)。

---

## §空欄

| # | 空欄 | 理由 | 次の手 |
|---|---|---|---|
| R108-1 | LLM が「その他(自由記述)」の欄を選ぶ割合 | 測った原典が見つからない。近いのは NA と「わからない」と複数回答だけ(§1-5) | キーワードを変えて再探索。見つからなければ v2 で測る(§3-3) |
| R108-2 | 人が閉じた質問で「その他」を使う割合の数値 | Schuman & Presser 1979 は検索結果の要約だけ。本文は JSTOR(有料の可能性) | 図書館か 1981 年の本の第 3 章。ユーザーの手作業 |
| R108-3 | 日本語の選択問題での記号の偏り(数字・丸数字・ア/イ/ウ) | 見つからない。全部の原典が英語の A/B/C/D か 1/2/3/4 | 日本語の LLM 評価(JGLUE など)の文献の探索。手元の GPU で即断や 8B で測る(先に聞く) |
| R108-4 | Li ら 2025 が NeurIPS 2025 のどの track で採択されたか | ポスターの頁・ML Anthology に track の記載なし。本文は position paper を自称 | OpenReview の頁(ブラウザで開く・ユーザーの手作業) |
| R108-5 | Li ら 2025 のカメラレディ版で数値の表や検定が足されたか | OpenReview がブラウザ確認の画面で読めない | 同上 |
| R108-6 | 日本語の人物像の文の感情の極性と主観性を測る道具 | 未リサーチ | 次の発注で(ライセンスの確認を含む) |
| R108-7 | 候補を「本人の頭に浮かんだこと」として見せる言い方と、メニューとして見せる言い方を比べた研究 | 検索で見つからない。近いのは「閉じた形式は答えを候補へ寄せる」という立場の論文(#19・△)と、答えの出させ方で分布が変わるという Ahnert 2026(#15) | v2 の評価セットの腕で測る |
| R108-8 | Tjuatja 2024 で「わからない」そのものが選ばれた割合 | 表 3 は中央の選択の変化だけ | 公開データ(著者が公開を予告)を読む |
| R108-9 | Zheng 2024 の 2 択・3 択の結果の数値 | 付録の図で示され、表を読んでいない | 必要なら付録 B を読む |

ユーザーの判断や手作業が要るもの: 2 件(R108-2 の本文を図書館などで読むか・R108-4/5 の OpenReview をブラウザで開くか)。手元の GPU で日本語の記号の偏りを測るか(R108-3)は親の判断で、pip と huggingface の許可の範囲内かの確認が要る。有償のデータは無い。

---

## §v2 への当てはめ(案・未決。親が判断する材料)

比べる相手は指示書 10-12 §4-12 C-2(番号で返す口の対策 4 つ)・§4-7(DM-0・DM1・DM4・DM5)・§4-10 PS3、計画の 1-8(J0)と 4-1b。以下は材料で、決定ではない。

### 3-1 対策 1「順のシャッフルと並べ替え試験」

- **原典との整合**: 並べ替えの平均と PriDe が効くことは原典で確認できた(§1-1)。記号の変更・偏りを除く指示・CoT では足りない(同)。C-2 の対策 1 は原典の向きに合う。
- **違う点(注意)**: 1 回の呼び出しで順を 1 度だけ混ぜても、記号の偏りは消えずに「どの候補に当たるか」の雑音に変わる(Zheng は混ぜても RStd がほぼ変わらないことを示した・付録の図 18)。人口の集計では、系統の偏りが候補の分布を一様の側へ均す誤差に変わる(推測)。v2 では人の分布の形そのものを見るので(DM6 のばらつきの比)、均される分を計器で見ておく必要がある(推測)。
- **借りられる点**: 判断モデルは候補の分布を返す(§4-7)ので、PriDe の「ID の事前分布」を推定できる適用先がある。目的地選びの答申 §6 ④ の「適用先が無い」は自由文の欄の時代の判断で、J0 では前提が変わる。案は 2 つ。(i) 補正には使わず、モデルと版ごとに ID の事前分布を推定して manifest と計器に記録するだけにする。(ii) 補正にも使う腕を置く。LLM の側も、vLLM で番号のトークンの確率が取れれば同じ形で推定できる(09-09 の構造化出力の実測の範囲。推測)。
- **並べ替え試験の物差しの候補**: 選択肢 ID ごとの再現率の標準偏差(RStd・#1)・答えの分布と正解の分布の KL(CKLD・#13)・位置ごとの選択の分布と一様との距離(PBS・#14)。v2 には正解が無いので、PBS 型(同じ問いを並べ替えた分布の一様からの距離)がそのまま使える(推測)。R-94 の「全選択肢を同じ文にした対照」(段階の語の第 1 水準を避ける偏り)も同じ枠に入る。
- **小さなモデルへの当てはめ**: 7B 級は偏りが大きい枠が多いが、系列で一貫しない(#1)。即断(約 3 億)と 9B 級の値はどの原典にも無いので、J0 の試験で測るしかない(推測)。

### 3-2 対策 2「LLM は理由を先に・番号は最後(じっくり考えるときは縛らない)」

- **原典との整合**: 正答率の面では、答えを先に書かせると推論が飛ぶ(Tam §4.1)ので、理由を先にする順は原典に合う。
- **違う点**: 偏りの対策としては当てにならない(§1-4)。Llama 系の 8B では CoT で偏りが減った例があるが、Qwen2.5-7B では変わらず、InstructGPT では説明を先にすると悪くなった。DM5 の「じっくり考える(思考モードあり)」では、考える長さとともに位置の偏りが増えるという未査読の報告がある(#14)。
- **案**: 思考モードの呼び出しでも順のシャッフルは外さない。計器に「選んだ位置」と「考えた長さ」を並べて記録し、長さと位置の偏りの相関を見る(#14 の偏相関の形)。DM5 の暴走止めの上限に当たった記録と同じ欄に置ける(推測)。
- 形式の縛りの強さ: 「縛ると落ちる」は反論があり(§1-3)、分類に近い課題では縛りが効く報告もある。番号を構造化出力で強制するのは、理由の欄を先に置く限り原典と矛盾しない(推測)。

### 3-3 対策 3「その他(自由記述)の欄を付け、選ばれる割合を測る」

- **原典との整合**: 欄を付けること自体を支える研究も否定する研究も見つからなかった(空欄 R108-1)。
- **違う点(注意)**: 近い証拠はどれも、LLM が候補の外へ出るのを嫌うことを示す(NA が正解でも 8B は 18.3% しか選ばない・#11)。人の側も候補に無い答えをあまり言わない(#17・△)。だから「その他」の割合が低くても、「候補で足りている」証拠にはならない(推測)。
- **案(既知の答えの検査)**: 評価セットに「いちばん当てはまる候補をわざと抜いた場面」を入れ、「その他」に流れる割合を測る(#10・#11 の NA を正解にする形)。これで、低い割合が候補の十分さによるのか、外へ出ない癖によるのかを分けられる。人の床は R108-2 の数値が入ってから並べる。
- **副作用の見張り**: 逃げ道の候補を足すと残りの候補の分布が動く(#13 の AOI)。「その他」の欄の有無を腕にして、残りの候補の分布の変化を測る案がある(推測)。

### 3-4 対策 4「候補はメニューではなく本人の頭に浮かんだこととして見せる」

- 直接比べた研究は見つからない(空欄 R108-7)。答えの出させ方で分布が大きく変わること(#15)と、閉じた形式が答えを候補へ寄せるという主張(#19・△)はある。評価セットの腕(言い方 2 通り)で測るのが原典から言える範囲(推測)。
- C-2 の (b)「文章で答えさせる方式」の腕について: Ahnert 2026 は、文章で答えさせてから分類する方式が、選ばせる方式と同じくらいか少し下だった(表 3)。分布の一致では、確率を言葉で書かせる方式が最も良かった(要旨)。R-97 の「分布を 1 回で書かせると人の調査との誤差が半分以下」と同じ向き。(b) の腕に「確率を書かせる」を 1 つ足すかは親の判断。

### 3-5 4-1b の腕(LLM が書いた人物像)

- **原典との整合**: PS3 (b)「作り物の生い立ちは使わない」は、Li らの所見と同じ向き。計画 9 見せ方の「人物の説明文は事実から決まった形で組み立て、LLM に書かせない」は、Li の段 1〜2 に当たり、原典で現実に近かった側。
- **違う点と借りられる点**: §2-5 の 6 つ。要点は次の 3 つ。
  1. 段を 4 つにする(閉じた一覧の段と開いた項目の段を分ける)。
  2. 書かせる LLM と住人の LLM の組の表で比べる(複数の LLM を混ぜた住人の腕・D-68 の画一性の腕と組める)。
  3. 段 1 を床として置き、全段に同じ偏りの対策をかける。
- **向きを決め打ちしない**: Li の「左寄り」は米国の政治の問いで、モデルによっては逆(Yi-34B)。v2 の比べる相手(行動の分布・店や場所の選び方・お金の使い方)で、どちらへずれるかは測るまで分からない(推測)。事前登録には「向き」ではなく「段 1 からの離れ方の大きさ」を主要な指標に置く案がある。
- **人物像の文の計器**: 日本語の感情の極性の道具は空欄(R108-6)。苦労の語は、合成人口の属性(失業・障害・病気・低所得など)の割合と、文の中で触れられる割合を突き合わせる形にできる(案)。

### 3-6 親に確かめてほしい点

1. lit ノート(`lit/nlp__zheng2023_selection-bias.md`)の「総当り置換(×4)」は原典では Cyclic Perm(訂正の伝播の候補)。
2. ペルソナと人口の深掘り 面 2 の「Meta>Tabular>Descriptive」は、図 5 では段 2 と段 1 の上下が枠で入れ替わる(写し検査・§2-4)。計画 4-1b の書き方は向きとしては合う。
3. Li らの図 5・図 8 の値は、図を目で読んだ概数(表が無い)。主張に使うときは「図から読んだ」と書く必要がある。
4. 目的地選びの答申の「13% to 75%」と R-88 の「13% to 85%」は版の違い(arXiv v1 と NAACL 版)で、どちらも原典どおり。
