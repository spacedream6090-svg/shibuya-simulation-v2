# R17 倫理・コンテンツ安全の運用規則 — ギャップ埋め答申(正典化)

> **親検収(Fable・2026-09-08)**: サブ(Opus 5・子サブなし・リポ書込なし・ハーネスがファイル書込を遮断=テキスト返答を親が保存)の最重要5件を親が原典で確認した。✔=一致。
> - ✔ **CitySim(arXiv 2506.21805・Bougie & Watanabe・Woven by Toyota)**: "We now assess CitySim's ability to reproduce real-world patterns of pedestrian concentration across Shibuya (Japan)."・エージェント属性は "a proprietary survey-based dataset, conducted in Japan"+OpenStreetMap。§7 Ethics Statement 全文を親が取得(バイアス増幅/不公平の再生産/行動誘導と同意・自律/実住民・利害関係者・専門家の関与の周縁化→"complement, not replace")。
> - ✔ **CityReal(arXiv 2608.16897・Bougie, Ye & Watanabe・2026-07-08)**: "We assess CityReal's ability to reproduce pedestrian concentration patterns across Shibuya, Tokyo."・Ethics Statement 全文取得("they should not be treated as a substitute for real residents, stakeholders, or domain experts"・"complement, rather than replace, participatory design, empirical studies, and expert review")・Limitations "the reproducibility of some experiments is constrained by the use of non-public datasets"。
> - ✔ **PPC FAQ Q15-1**(個人情報保護委員会): 統計情報は集団の傾向を数量的に示すのみで特定個人との対応関係が排斥されている限り「個人に関する情報」に該当せず個人情報保護法の対象外。ただし特定個人が識別できる情報は個人情報(親WebFetch=要約一致・逐語は後日原文で再確認)。
> - ✔ **PoliSim(arXiv 2604.07838・Luo, Arora, Guirado・UC Berkeley)**: §2の3前提見出し("Do Not Treat Simulations of Marginalized Populations as Neutral Technical Outputs"/"Do Not Simulate Populations Without Their Participation"/"Do Not Simulate Without Accountability")・decision chain の可読性要件(責任者の特定・独立した検証・救済経路)・Simulation Development and Deployment Reports の要求項目(開発主体と協議過程・検証方法と十分性・解釈指針と範囲・展開履歴・継続更新)。
> - ✔ **医学系指針(厚労省 t_doc 00012250)**: 第2(1)定義=ア(健康保持増進・傷病回復・QOL: 成因/病態/予防/診断治療)またはイ(ヒトゲノム・遺伝子)を目的とする活動。第3 適用範囲の除外=ア法令の規定により実施/イ法令基準の適用範囲/ウ①学術的価値が定まり一般入手可能な試料・情報②**個人に関する情報に該当しない既存の情報**③既に作成された匿名加工情報のみを用いる研究。
> - 空欄のまま(親も未読): OASIS付録I全文(親WebFetchで再試行=下記)・Generative Agents §8.3残り・日本心理学会倫理規程・Five Safes原文・EU AI Act 50条原文・HFデータセットカード原文・C2PA適用例。
> - 適用先: 倫理・安全運用設計書(草案) docs/design/v2-ethics-safety-operations.md。

> 作成: 2026-09-08 / 実行=Opus 5 リサーチサブ / 既存答申(U-K content-safety・U-N publication-ethics・legal-licensing・ad-information)との重複は除外。

## 要約(6行)
1. 渋谷を名指しで実験地にしたLLM社会シムの先行が2本(CitySim/CityReal・いずれもToyota系)あり、独立の Ethics Statement を持つ。内容は(a)合成エージェントのバイアス増幅(b)集合行動誘導への転用(c)実住民・利害関係者・専門家の代替禁止の3点に収束=v2の倫理節の最低ライン。
2. 「実在都市を使うこと自体」の正当化を書いた先行はなく、正当化はデータ由来(OSM+集計統計・個票なし)で行う。CrimeMind "SafeGraph data are aggregated at the CBG level, ensuring no individual-level or personally identifiable information is included."(要約経由)がKDDI/PT記述の型。
3. 日本の個情法: PPC FAQ Q15-1により集計統計は法の対象外→合成ペルソナは入口で対象外。残る実質論点は同定可能性の管理のみ。
4. 人を対象とする研究の該否: 医学系指針は目的限定(健康・傷病・ゲノム)+第3で「個人に関する情報に該当しない既存の情報」のみの研究を除外。識別テストの評価者は成果物の格付け者=二重に射程外。日本心理学会規程は空欄。
5. 犯罪・逸脱: CrimeMindは「LLMを犯行者でなく expert criminologist として推論させる」緩和(要約経由・「不完全」との自己申告あり)。PoliSimの3前提が説明責任設計の骨格。
6. 段階公開: Five Safes(projects/people/settings/data/outputs)はU-Kの4層(誰に)と軸が違い直交併用。C2PAは trainedAlgorithmicMedia(メディア)/c2pa.trainedAlgorithmicData(非メディア)。

## 1. LLMエージェント社会シムの倫理節(実例)
| 主張 | 出典 | 逐語 | 別 |
|---|---|---|---|
| CitySim §7 Ethics Statement(渋谷実験) | https://arxiv.org/html/2506.21805v1 | "The use of synthetic agents in urban simulation may inadvertently amplify biases, such as stereotypes about age, gender, occupation, or lifestyle…" / "…there is a risk that their deployment might marginalize the involvement of actual residents, stakeholders, and domain experts…" / "We recommend that synthetic humans be employed primarily to complement, not replace, human input" | 親実読(WebFetch全文) |
| CityReal §7 Ethics Statement | https://arxiv.org/html/2608.16897 | "Third, while synthetic agents are useful for early-stage exploration and low-cost evaluation of urban scenarios, they should not be treated as a substitute for real residents, stakeholders, or domain experts." / "We therefore recommend that synthetic agents be used to complement, rather than replace, participatory design, empirical studies, and expert review" | 親実読 |
| Generative Agents §8.3(パラソーシャル関係) | https://ar5iv.labs.arxiv.org/html/2304.03442 | "One risk is people forming parasocial relationships with generative agents, even when such relationships may not be appropriate." | 要約経由(冒頭のみ) |
| Sotopia-RL: 人間と区別不能な系を意図しない | https://arxiv.org/html/2508.03905v1 | "our intention is distinctly not to replicate human identity or create systems indistinguishable from human beings" | 要約経由(v2とは立場が異なる先行) |
| OASIS: uncensored使用の記述 | https://arxiv.org/html/2411.11581v5 | "The uncensored model has been stripped of its safety guardrails"(§3.3.2)。親再試行(WebFetch): 本文はuncensoredと aligned Llama-3-8B の比較を**実証結果として記述するのみで使用の正当化は書いていない**。付録I "Social Impact and Ethical Considerations" はHTML版に含まれず=空欄維持 | 親確認(§3.3.2)・付録I空欄 |
| AgentSociety: 独立の倫理節なし(データ源のみ) | https://arxiv.org/html/2502.08691v2 | "Road networks and AOIs are extracted from OpenStreetMap" | 要約経由 |

## 2. 合成ペルソナと個人情報保護
- PPC FAQ Q15-1(https://www.ppc.go.jp/all_faq_index/faq1-q15-1/): 統計情報は個情法対象外・特定個人が識別できれば個人情報(親確認)。「合成データ」を名指ししたPPC指針は見つからず(空欄)。
- PPC 生成AI注意喚起(2023-06-02)は存在(別添1未読)。英ICO匿名化ガイダンス・EU AI Act 50条(2)(合成テキストの機械可読マーキング・2026-08-02適用)は要約経由=原文未確認。

## 3. 有害発話の観察と公開の分離
- HFデータセットカード "Considerations for Using the Data"(Social Impact/Biases/Limitations)・gated repo(要約経由)。
- 「介入せず観察」と「公開時フィルタ」の分離を明文化した先行は見つからず→v2の独自宣言(expedient)として台帳登録。
- C2PA 2.4 AI/ML: "For a generative model this will be trainedAlgorithmicMedia, and for output that is not a media asset, the c2pa.trainedAlgorithmicData designation would be appropriate."(要約経由)。C2PAは来歴であって真正性ではない(要約経由)。

## 4. 犯罪・逸脱の創発を扱う先行の倫理条件
- CrimeMind(https://arxiv.org/html/2506.05981v1)§A.3.1 "we design prompts that cast the LLM agent as an expert criminologist reasoning about offenders' decisions"・§A.3.2 "SafeGraph data are aggregated at the CBG level, ensuring no individual-level or personally identifiable information is included."(要約経由・親未読)。
- 犯罪学ABM(Groff/Birks・Annual Review of Criminology): 現実実験が倫理的に不可能な領域でのシム代替(要約経由・逐語空欄)。
- PoliSim(https://arxiv.org/html/2604.07838v1): 3前提+decision chainの可読性+Deployment Reports(親確認)。

## 5. 人を対象とする研究の該否
- 医学系指針 第2(1)・第3(親確認・上記)。日本心理学会倫理規程(https://psych.or.jp/wp-content/uploads/2017/09/rinri_kitei.pdf)=未読(空欄)。民間IRBはU-Nでカバー済み。

## 6. 段階公開と来歴
- Five Safes(UK Data Service/ONS): Safe projects/people/settings/data/outputs(要約経由・原文未取得)。社会シム出力へのC2PA適用例=未発見(空欄)。

## 未決①〜⑦への適用案(サブ案・親が設計書草案で採否を整理)
①4層(誰に)×Five Safes(何を担保)の直交併用・フィクション注記3箇所(常設表示・C2PA機械可読・データセットカード)/②censored/uncensored両ablation維持+実験ごとのモデル・改変有無の常時開示・uncensored生文はL0のみ/③「介入せず観察」と「公開時フィルタ」を台帳2行で分離・検出器は観測器(世界状態にフィードバックしない)・介入回数=0を毎ラン検証/④U18は扱う: 行動語彙に閉じた出力(手口の自由記述経路が構造的に無い)+伝播は存在と分布のみ+手口検出器/⑤PoliSim 3前提への逐条応答(被覆と歪みの開示・訂正受付窓口=最小の当事者参加・決定台帳とmanifestで決定連鎖の可読化・係争中の実在政策/事件は初回除外)/⑥倫理審査不要の3本立て(Common Rule "about whom"・医学系指針の目的限定・PPC Q15-1)/⑦Datasheet固定文3段(集計統計のみ・特定個人との対応関係なし・同定可能性管理)。

## 参照一覧
WebFetch(サブ): ar5iv 2304.03442・arxiv 2502.08691v2・2411.11581v5・2508.03905v1・2604.07838v1・2506.05981v1・2608.16897・2506.21805v1・ppc.go.jp faq1-q15-1・ppc 230602注意喚起・mhlw t_doc 00012250・spec.c2pa.org 2.4 ai_ml。WebSearchのみ(逐語不可): annualreviews 022222-033905・sciencedirect S0198971509000787・ukdataservice Five Safes・fivesafes.org・artificialintelligenceact.eu/article/50・digital-strategy.ec.europa.eu FAQ・ico.org.uk anonymisation・HF datasets-cards/gated/README_guide・psych.or.jp 倫理規程・arxiv 2601.13981・2411.00114・2604.24890v1。親再確認: 2506.21805v1・2608.16897・ppc Q15-1・2604.07838v1・mhlw 00012250。
