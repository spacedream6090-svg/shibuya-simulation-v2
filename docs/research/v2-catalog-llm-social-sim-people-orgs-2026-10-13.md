<!-- hdr:v1 | 等級: C(ユーザーが claude.ai で集めた一覧・一次確認は 20 件だけ) | 分野: 横断(人・研究室・企業・コミュニティ) | 重要度: P2(手がかり) -->
> 〔保存の注記(第332・親・2026-10-13)〕 ユーザーが claude.ai の別のチャットで集めた「LLM 社会シミュレーションの人・研究室・企業・コミュニティ」の一覧(214 件)をそのまま保存した(文言は変えていない)。**決定ではない。設計書に直接写さない。** 一次確認が済んでいるのは主要 20 件だけで、残りは調べものの手がかりとして扱い、使う前に原典で確かめる(CLAUDE.md §5)。組み込み先: [リサーチ残務台帳](research-backlog.md) §3g(ユーザーが特に効きそうとしたもの 10 件を手がかりとして登録)・E1 の既存実装の比較表・各草案の比較表。人への連絡や締め切りの項目は記録だけ(ユーザーの手の作業)。

# LLM社会シミュレーション 人・研究室・企業・コミュニティ カタログ(全件)

- 作成: 2026-10-13(Claude による調査・shibuya-simulation-v2 の詰まりどころ (1)〜(8) と対応づけ)
- 214 件(241 件から重複 27 件をまとめた)。URL は調査時に WebSearch/WebFetch で確認できたものだけ。「未確認」は確認できなかった項目。企業の数値は自己申告。
- 詰まりどころ: (1)空腹偏重・行動更新頻度 (2)会話の発生率と中身 (3)来街者比・ピーク時刻の較正 (4)複数日ラン・記憶・ペルソナドリフト (5)39万体の推論コスト・GPU (6)LLMが人を再現しているかの検証 (7)物理・群衆の空間層 (8)事業化
- 主要 20 件は別の確認役が一次確認済み(16 一致・3 修正・PLATEAU AWARD の締切はプレエントリー 11/6・本エントリー 11/19 で確定)。

## 1. 研究室(海外)


調査日: 2026-10-13。WebSearch/WebFetch で確認できた URL のみ記載。確認できない項目は「未確認」。
既出判定は known_arxiv.txt / known_github.txt との突合による。

---

#### Stanford HCI Group — Joon Sung Park / Michael Bernstein / Percy Liang(Generative Agents 系)
- 種別: 研究室
- 中心人物: Joon Sung Park(Stanford HCI/NLP/SAIL、Simile CEO)、Michael S. Bernstein(Stanford CS 教授)、Percy Liang(Stanford CRFM)
- 代表的な成果: Generative Agents arXiv 2304.03442 / Generative Agent Simulations of 1,000 People arXiv 2411.10109 / **Finetuning LLMs for Human Behavior Prediction in Social Science Experiments arXiv 2509.05830(EMNLP 2025 oral)** / Creating General User Models from Computer Use arXiv 2505.10831(UIST 2025 Best Paper HM)/ Position: LLM Social Simulations Are a Promising Research Method arXiv 2504.02234(ICML 2025)/ Bernstein: Learning Next Action Predictors from Human-Computer Interaction(CoLM 2026)/ github.com/joonspk-research/generative_agents
- 窓口・発信: Park 個人サイト https://www.joonsungpark.com/ (更新一覧 https://www.joonsungpark.com/all_updates )/ X https://twitter.com/joon_s_pk / Bernstein https://hci.stanford.edu/msb/ / 2509.05830 のプロジェクトページ https://stanfordhci.github.io/socrates
- 活動状況: 活動中。Park の博士論文「Generative Agent Simulations of Human Behavior」が 2026年6月に Stanford Arthur Samuel Award(最優秀博士論文)。2025年5月 Stanford HAI ポリシーブリーフ「Simulating Human Behavior with AI Agents」(Park, Zou, Shaw, Hill, Cai, Morris, Willer, Liang, Bernstein)。CHI 2025 でシミュレーション×HCI ワークショップ共催。中心メンバーは Simile に移行(下記)。
- 渋谷シムへの使いどころ: (6) 1,000人インタビュー→エージェント化と「本人の2週間後再回答との一致率で正規化する」評価法(GSS で約85%)は、LLM が人を再現しているかの検証設計の手本。(2)(4) 2509.05830 の「社会科学実験データで LLM を微調整して行動予測」は System 1.5 の軽量判断モデルを学習させる方針の直接参考。
- 既出: 既出(論文 2304.03442 / 2411.10109 / 2504.02234、コード generative_agents)。2509.05830 / 2505.10831 は新規
- 出典: https://www.joonsungpark.com/ , https://www.joonsungpark.com/all_updates , https://hci.stanford.edu/msb/ , https://hai.stanford.edu/policy/simulating-human-behavior-with-ai-agents

#### Stanford CS222「AI Agents and Simulations」(公開講義)
- 種別: その他(大学講義・公開教材)
- 中心人物: Joon Sung Park(講師)、TA Carolyn Zou / Helena Vasconcelos
- 代表的な成果: 2024年秋学期の全14回スライド PDF・必読文献リスト・課題・AgentBank 演習が公開。ゲスト講義 Meredith Ringel Morris / Serina Chang
- 窓口・発信: https://joonspk-research.github.io/cs222-fall24/index.html / Stanford Bulletin https://bulletin.stanford.edu/courses/2263691
- 活動状況: Bulletin に 2026-27 Autumn として掲載はあるが「No Sections Found」(開講未確定)。公開資料は 2024 年版のみ確認。
- 渋谷シムへの使いどころ: (6)(1) 講義回「Believability vs. Accuracy」「Models of Individuals」「Generative Agent-Based Models」「Equilibria and Butterflies」は、空腹偏重などの行動設計と検証の整理にそのまま使える体系的リーディングリスト。未踏の説明資料の参考文献整理にも。
- 既出: 新規
- 出典: https://joonspk-research.github.io/cs222-fall24/index.html , https://bulletin.stanford.edu/courses/2263691

#### Simile(Stanford 生成エージェント組のスピンアウト企業)
- 重複のため「企業」タブの同名項目にまとめた

#### 清華大学 FIB Lab(Future Intelligence laB)— AgentSociety / AgentSociety 2
- 種別: 研究室
- 中心人物: Yong Li(李勇、清華大電子工学系)、Fengli Xu、Jinghua Piao、Jun Zhang ほか
- 代表的な成果: AgentSociety arXiv 2502.08691 / **AgentSociety 2: An Integrated Research Environment for Executable Social Science arXiv 2607.11895(2026-07-15)** / github.com/tsinghua-fib-lab/AgentSociety(約1.2k stars)/ LLM_for_Polarization(2026-07 更新)/ AutoSOTA / AI-Urban-Scientist
- 窓口・発信: ラボサイト http://fi.ee.tsinghua.edu.cn/ / AgentSociety 2 サイト https://agentsociety2.fiblab.net/ / ドキュメント https://agentsociety2.readthedocs.io (v2.9.3)/ PyPI https://pypi.org/project/agentsociety2/ / GitHub org https://github.com/tsinghua-fib-lab(296 repo)/ 連絡先 liyong07@tsinghua.edu.cn。Discord・WeChat は確認できず
- 活動状況: 活発。AgentSociety 2 は「AI社会科学者+シリコン被験者」の二役構成、スキル型エージェント、予算考慮型コンテキスト圧縮、**CodeGenRouter(意図→Python コード化+セマンティックキャッシュで LLM 呼び出しの7割超を不要化)**。NeurIPS 2025 に9本採択(2025-09)。
- 渋谷シムへの使いどころ: (5) CodeGenRouter は System 1/1.5 へのオフロード設計と同発想で、39万体の推論コスト削減の直接参考。(4) 段階要約によるメモリ圧縮+全履歴の外部ログは複数日ランの記憶設計に。v1 は既にコードまで読了済みなので v2 の差分読みが効率的。
- 既出: 既出(論文 2502.08691 / 2607.11895、コード AgentSociety)。v2 ドキュメントサイト・PyPI は新規
- 出典: https://www.alphaxiv.org/abs/2607.11895 , https://github.com/tsinghua-fib-lab , https://github.com/tsinghua-fib-lab/AgentSociety , https://agentsociety2.readthedocs.io , http://fi.ee.tsinghua.edu.cn/

#### 清華大 都市科学・計算研究センター(FIB Lab 都市系: CityGPT / CityBench / UrbanWorld / EmbodiedCity)
- 種別: 研究室
- 中心人物: Yong Li、Fengli Xu、Yu Zheng(博士課程)、Tianhui Liu ほか。共同: MIT Senseable City Lab(Carlo Ratti, Paolo Santi)、Northeastern(Qi R. Wang)
- 代表的な成果: CityBench arXiv 2406.13945 / CityGPT / UrbanLLaVA / UrbanWorld2.0(ACM MM 2026)/ EmbodiedCity(github.com/tsinghua-fib-lab/EmbodiedCity)/ RoadBench(ECCV 2026)/ Nature Computational Science 2025 の LLM 駆動・人間協働型都市計画フレームワーク
- 窓口・発信: http://fi.ee.tsinghua.edu.cn/ / https://github.com/tsinghua-fib-lab
- 活動状況: 活発(2026年6〜7月に複数 repo 更新)。
- 渋谷シムへの使いどころ: (7)(8) UrbanWorld2.0 / EmbodiedCity は都市3D世界生成・エンボディド層の参考、行政・再開発向けの「計画案評価」ユースケース(Nature Comput. Sci. 論文)は事業化の論拠に。CityBench は LLM の都市空間理解の評価に。
- 既出: 新規(CityBench 2406.13945 は known_arxiv に無し)
- 出典: https://eu.36kr.com/en/p/3463004755334529 , https://github.com/tsinghua-fib-lab , https://arxiv.org/html/2406.13945v3

#### CAMEL-AI(OASIS / OWL / Eigent)
- 種別: OSSコミュニティ / 企業
- 中心人物: Guohao Li(創設者)ほか 100名超の研究者コミュニティ
- 代表的な成果: OASIS: Open Agent Social Interaction Simulations with One Million Agents arXiv 2411.11581 / github.com/camel-ai/oasis(約4.9k stars)/ OWL(NeurIPS 2025)/ LOONG / CRAB / 派生研究 MultiAgent4Collusion, MultiAgent4Fraud, CUBE(Unity3D 環境)
- 窓口・発信: https://www.camel-ai.org/ / OASIS ブログ https://www.camel-ai.org/blogs/oasis / OASIS ドキュメント https://docs.oasis.camel-ai.org / Discord https://discord.camel-ai.org (OASIS ドキュメント記載の招待 https://discord.com/invite/CNcNpquyDc )/ X https://x.com/CamelAIOrg / GitHub https://github.com/camel-ai / Reddit r/CamelAI / WeChat グループあり(README)/ camel.ai.team@gmail.com / Eigent https://eigent.ai
- 活動状況: OASIS 最新リリース v0.2.5(2025-12-04)。2025年に Interview Action(エージェントへの質問)、グループチャット、PettingZoo 型インターフェース追加。2026年の OASIS 新機能は確認できず。組織としては Eigent(「Open Source Cowork」)に軸足。資金調達情報は未確認。
- 渋谷シムへの使いどころ: (2) Interview Action / グループチャット機能は会話発生率 0.07% 問題への対照実装として。(5) 100万体を回すスケジューリング実装の参考(既読)。
- 既出: 既出(論文・コード OASIS)。Discord 等の窓口は新規
- 出典: https://www.camel-ai.org/ , https://github.com/camel-ai/oasis , https://docs.oasis.camel-ai.org/llms.txt

#### Google DeepMind Concordia チーム
- 種別: 研究室(企業研究所)
- 中心人物: Joel Z. Leibo(GDM Senior Staff Research Scientist、King's College London 客員教授)、Alexander Sasha Vezhnevets
- 代表的な成果: Concordia tech report arXiv 2312.03664 / **Multi-Actor Generative AI as a Game Engine arXiv 2507.08892(2025-07)** / Evaluating Generalization ... Using Concordia arXiv 2512.03318 / **Virtual Agent Economies arXiv 2509.10147** / **Persona Generators: Generating Diverse Synthetic Personas for Arbitrary Contexts arXiv 2602.03545(2026-02)** / **A Case Study on Emergent Cheating and Whistleblowing in Autonomous Research Swarms arXiv 2609.04170(2026-09)** / github.com/google-deepmind/concordia(約1.6k stars、PyPI gdm-concordia)
- 窓口・発信: GitHub https://github.com/google-deepmind/concordia / YouTube チュートリアル https://www.youtube.com/watch?v=2FO5g65mu2I / Leibo の論文一覧 https://www.alphaxiv.org/@joel-z-leibo
- 活動状況: 活発。**Concordia v2.0(2025-08-21)**: Entity-Component 設計、Game Master もエンティティ化、Prefab 導入、シリアライズ/チェックポイント対応。
- 渋谷シムへの使いどころ: (4) v2.0 のチェックポイント機能と GM 設計は複数日ランの状態保存に。(1)(4) 2602.03545 Persona Generators は 39万体の多様なペルソナ生成とペルソナドリフト対策の新しい参照点。
- 既出: 既出(コード concordia、論文 2312.03664 / 2512.03318)。2507.08892 / 2509.10147 / 2602.03545 / 2609.04170 は新規
- 出典: https://www.cooperativeai.com/post/google-deepmind-releases-concordia-library-v2-0 , https://github.com/google-deepmind/concordia , https://www.alphaxiv.org/@joel-z-leibo

#### Cooperative AI Foundation — Concordia Contest
- 種別: 学会・ワークショップ(コンペ)/ 財団
- 中心人物: Cooperative AI Foundation、共催 Google DeepMind・MIT・UC Berkeley・UCL、ハッカソン共催 Apart Research
- 代表的な成果: NeurIPS 2024 Concordia Contest(参加197名、提出878件、GDM が $33,000 の計算資源支援)。上位: Taehun Cha(Korea Univ.)ほか。提案書 OpenReview https://openreview.net/forum?id=dfeFy1PSSw
- 窓口・発信: コンテスト頁 https://www.cooperativeai.com/post/concordia-contest / メーリングリスト https://cooperativeai.us1.list-manage.com/subscribe?u=22ce01d188f00846e96e67e13&id=eddc79e400 / NeurIPS リプレイ https://neurips.cc/virtual/2024/competition/84791 / パネル(Diyi Yang, Hernández-Orallo, Fei Fang, Leibo) https://neurips.cc/virtual/2024/108501
- 活動状況: コンテスト報告論文を NeurIPS 2025 に投稿予定と記載。2025/2026 年版開催は未確認。
- 渋谷シムへの使いどころ: (2) 混合動機シナリオでの協調エージェント設計例は会話・交渉の中身を濃くする参考。メーリングリストで次回コンペ情報を受け取れる。
- 既出: 新規
- 出典: https://www.cooperativeai.com/post/concordia-contest , https://www.cooperativeai.com/post/google-deepmind-releases-concordia-library-v2-0

#### MIT Media Lab Camera Culture — Large Population Models / AgentTorch(Ayush Chopra, Ramesh Raskar)
- 種別: 研究室
- 中心人物: Ayush Chopra(MIT Media Lab 博士課程、Ramesh Raskar 指導)、Ramesh Raskar
- 代表的な成果: Large Population Models arXiv 2507.09901 / On the limits of agency in agent-based models arXiv 2409.10568(AAMAS 2025)/ github.com/AgentTorch/AgentTorch(約651 stars、PyPI v0.6.0)
- 窓口・発信: プロジェクト https://www.media.mit.edu/projects/ai-lpm/overview/ / ドキュメント https://agenttorch.github.io/AgentTorch/ , https://lpm.media.mit.edu/docs / **Slack https://join.slack.com/t/largepopulationmodels/shared_invite/zt-2jalzf9ki-n9nXG5FryVSMaPmEL7Wm2w** / X @ayushchopra96 / 個人頁 https://web.media.mit.edu/~ayushc/index.html
- 活動状況: 博士論文審査イベントページあり(日付は取得失敗)。単一 GPU で 840万体、微分可能シミュレーションで較正 3000倍高速を主張。スピンアウト企業は確認できず(個人頁に「Enterprise Pitch」の記載のみ)。
- 渋谷シムへの使いどころ: (3)(5) 微分可能 ABM による較正は KDDI 人流の形(来街者比・ピーク時刻)へのフィッティングに直結。LLM を「アーキタイプ」単位で呼んで個体はテンソル化する方式は 39万体のコスト削減策。Slack で直接質問可能。
- 既出: 既出(論文 2507.09901 / 2409.10568、コード agenttorch)。Slack・ドキュメントは新規
- 出典: https://www.media.mit.edu/projects/ai-lpm/overview/ , https://github.com/AgentTorch/AgentTorch , https://web.media.mit.edu/~ayushc/index.html

#### John J. Horton(MIT Sloan)/ Expected Parrot
- 種別: 個人(研究者)/ スタートアップ
- 中心人物: John J. Horton(MIT Sloan Chrysler Professor、NBER)、Robin Horton(共同創業者)、Benjamin Manning
- 代表的な成果: Homo Silicus arXiv 2301.07543 / Automated social science: Language models as scientist and subjects(ACM EC 2026)/ General social agents(Econometrica R&R)/ Learning from synthetic labs: LMs as auction participants / Simulating the Survey of Professional Forecasters / github.com/expectedparrot/edsl(約494 stars、MIT)
- 窓口・発信: 個人 https://john-joseph-horton.com/ / X @johnjhorton / 会社 https://www.expectedparrot.com / ドキュメント https://docs.expectedparrot.com / ブログ(Substack) https://blog.expectedparrot.com / **Discord https://discord.com/invite/mxAYkjfy9m** / X https://x.com/ExpectedParrot
- 活動状況: Expected Parrot は 2024 年創業、**Y Combinator Fall 2025 バッチ**。Horton は 2025-08 から MIT Sloan TIES/IT 兼任。資金調達額は未確認。
- 渋谷シムへの使いどころ: (6) 「AI 被験者+実人間調査を並走させて仮定を検証」という EDSL のワークフローは、渋谷来街者アンケートとの突き合わせ設計に。(8) 社会科学者向け SaaS という事業モデルの比較対象。
- 既出: 既出(論文 2301.07543)。EDSL・Expected Parrot・Discord は新規
- 出典: https://john-joseph-horton.com/ , https://github.com/expectedparrot/edsl , https://www.expectedparrot.com

#### Petter Törnberg(University of Amsterdam, ILLC)
- 種別: 個人(研究者)
- 中心人物: Petter Törnberg(UvA 計算社会科学 准教授)、Maik Larooij
- 代表的な成果: Simulating Social Media Using LLMs to Evaluate Alternative News Feed Algorithms arXiv 2310.05984 / **Can We Fix Social Media? Testing Prosocial Interventions using Generative Social Simulation arXiv 2508.03385(2025-08)** / **Validation is the central challenge for generative social simulation(Artificial Intelligence Review 59, 2026、DOI 10.1007/s10462-025-11412-6)** / 書籍『Seeing Like a Platform』(2025)
- 窓口・発信: https://pettertornberg.com/ / UvA 頁 https://www.uva.nl/profiel/t/o/p.tornberg/k.p.tornberg.html / Bluesky https://bsky.app/profile/pettertornberg.com(X は確認できず)
- 活動状況: 活動中。2026 年は「AI summaries in social media improve dialogue but reduce engagement」「Political bias audits of LLMs capture sycophancy to the inferred auditor」など。
- 渋谷シムへの使いどころ: (6) 2026 年の検証レビュー(目的整合・外部根拠・頑健性の3基準)は holdout 0/4 NOT PASS の説明と検証計画書の骨格にそのまま使える。
- 既出: 既出(Törnberg 系として)。2508.03385 / 2310.05984 は known_arxiv に無く新規
- 出典: https://www.uva.nl/profiel/t/o/p.tornberg/k.p.tornberg.html , https://pettertornberg.com/ , https://arxiv.org/abs/2508.03385v1 , https://link.springer.com/article/10.1007/s10462-025-11412-6

#### Duke Polarization Lab(Chris Bail)
- 種別: 研究室
- 中心人物: Chris Bail(Duke)。Törnberg の LLM ソーシャルメディア・シミュ 2310.05984 および 2026 年 AI 要約論文の共著者
- 代表的な成果: 『Breaking the Social Media Prism』/ Social Media Accelerator / 2310.05984(共著)
- 窓口・発信: https://www.polarizationlab.com / X https://twitter.com/polarizationlab / ツール頁 https://www.polarizationlab.com/our-tools
- 活動状況: サイトは 2021 表記のまま。2025〜2026 の LLM シミュ関連ニュースはサイトでは未確認(論文共著は継続)。
- 渋谷シムへの使いどころ: (8) 直接の使い道は薄い。社会実験用プラットフォーム運用の先行例として。
- 既出: 新規
- 出典: https://www.polarizationlab.com/ , https://www.uva.nl/profiel/t/o/p.tornberg/k.p.tornberg.html

#### Jacy Reese Anthis(Sentience Institute / University of Chicago)
- 種別: 個人(研究者)
- 中心人物: Jacy Reese Anthis
- 代表的な成果: Position: LLM Social Simulations Are a Promising Research Method arXiv 2504.02234(ICML 2025、Brynjolfsson・Evans・Bernstein ら共著)/ CompanionSim(AIES 2026)/ HumanAgencyBench(EMNLP Findings 2026)/ Digital Companionship(CHI 2026)
- 窓口・発信: https://jacyanthis.com / ブログ https://jacyanthis.com/blog.html / X https://twitter.com/JacyAnthis / Medium https://medium.com/@jacyanthis / Sentience Institute https://sentienceinstitute.org/jacy-reese-anthis / サイト上にメール登録フォームあり
- 活動状況: 活動中(2026 年論文多数)。
- 渋谷シムへの使いどころ: (6) Position 論文の「5つの課題と方向性」は未踏の申請書・説明で「なぜ LLM シミュが科学的に成り立つか」を語る際の引用元。
- 既出: 既出(Anthis 系)
- 出典: https://jacyanthis.com , https://proceedings.mlr.press/v267/anthis25a.html

#### PIMMUR Principles 著者群(CUHK / JHU / CMU / Fudan / Stanford / Renmin)
- 種別: その他(複数機関の研究者グループ)
- 中心人物: Jiaxu Zhou(CUHK)、Jen-tse Huang(JHU)、Xuhui Zhou(CMU)、Xintao Wang(Fudan)、Hao Zhu(Stanford)、Wenxuan Wang(Renmin)、Maarten Sap(CMU)
- 代表的な成果: The PIMMUR Principles: Ensuring Validity in Collective Behavior of LLM Societies arXiv 2509.18052(v2 2026-01-26)
- 窓口・発信: 論文のみ確認。プロジェクトページ・GitHub は論文内に無し(未確認)。連絡先は論文記載の通り(Xintao Wang, Maarten Sap)
- 活動状況: v2 が 2026-01 に更新。
- 渋谷シムへの使いどころ: (6) 集団行動の妥当性6原則(Profile, Interaction, Memory, Minimal-Control, Unawareness, Realism)は渋谷シムの検証チェックリストに。特に「LLM が実験だと気づかない」「最小限の制御」は空腹偏重など設計バイアスの自己点検に。
- 既出: 既出(論文)
- 出典: https://arxiv.org/html/2509.18052v2

#### CMU Maarten Sap ラボ / Sotopia Lab
- 種別: 研究室 / OSSコミュニティ
- 中心人物: Maarten Sap(CMU LTI)、Xuhui Zhou(CMU)、Hao Zhu(Stanford)
- 代表的な成果: Sotopia(ICLR 2024 spotlight)github.com/sotopia-lab/sotopia / Sotopia-π / Sotopia-RL / **SOTOPIA-S4: user-friendly system for large-scale social simulation arXiv 2504.16122(NAACL 2025 demo)** / Agent vs Storyteller / **awesome-social-agents(2026-06 更新)** https://github.com/sotopia-lab/awesome-social-agents
- 窓口・発信: https://sotopia.world/ / ドキュメント https://docs.sotopia.world / デモ https://demo.sotopia.world / GitHub org https://github.com/sotopia-lab / GitHub Discussions。Discord は確認できず
- 活動状況: 活動中(sotopia 本体 2026-06 更新、sotopia-rl 2026-04、sotopia-verifiable 2026-02)。
- 渋谷シムへの使いどころ: (2) 会話の「中身」の社会的知性評価(目標達成・関係・秘密保持などの多次元評価)は会話品質の自動採点に転用可。「Agent vs Storyteller」(全知ナレーション型シミュは現実の人間相互作用と異なる)は会話生成の設計原則に。awesome-social-agents は人・組織収集の追加ソース。
- 既出: 新規(Sotopia 系 repo・2504.16122 は known に無し)
- 出典: https://sotopia.world , https://github.com/sotopia-lab , https://github.com/sotopia-lab/sotopia , https://arxiv.org/abs/2504.16122v1

#### Social Simulation with LLMs ワークショップ(Social Sim @ COLM)
- 重複のため「コミュニティ・学会」タブの同名項目にまとめた

#### 中国人民大学 高瓴人工智能学院 — YuLan-OneSim / S-Researcher(Xu Chen, Ji-Rong Wen)
- 種別: 研究室
- 中心人物: Xu Chen(陈旭)、Ji-Rong Wen(文继荣)、Lei Wang、Heyang Gao、Xiaohe Bo
- 代表的な成果: **YuLan-OneSim: Towards the Next Generation of Social Simulator with LLMs arXiv 2505.07581(NeurIPS 2025)** / github.com/RUC-GSAI/YuLan-OneSim(約245 stars)/ **LLM Agents as Social Scientists: S-Researcher arXiv 2604.01520(2026-04)** / RecAgent(ユーザー行動シミュ、既出系)
- 窓口・発信: ドキュメント https://ruc-gsai.github.io/YuLan-OneSim/ / Web サービス http://www.yulan-onesim.cn/ / Docker https://hub.docker.com/repository/docker/ptss/yulan-onesim/general / デモ動画 https://youtu.be/GSW2A76FIyw(英)https://youtu.be/NUxZQleeEIc(中)/ Xu Chen 学内頁 https://gsai.ruc.edu.cn/english/chenxu。Discord 等は確認できず
- 活動状況: 2025-05 公開、2025-06 ドキュメント・Docker 公開。2026-04 に OneSim 上の S-Researcher を発表。
- 渋谷シムへの使いどころ: (8) 自然言語からシナリオ自動生成するコードレス設計は、顧客(小売・行政)が自分で what-if を書ける UI の参考。(6) S-Researcher の人間協働型の仮説検証ループ。
- 既出: 2604.01520 は既出(論文)。2505.07581・YuLan-OneSim repo は新規
- 出典: https://arxiv.org/abs/2505.07581v3 , https://arxiv.org/html/2604.01520v1 , https://github.com/RUC-GSAI/YuLan-OneSim , https://neurips.cc/virtual/2025/124609

#### GenSim(人民大 + Alibaba + UCL)
- 種別: 研究室(共同)
- 中心人物: Jiakai Tang、Heyang Gao、Xuchen Pan、Xu Chen、Ji-Rong Wen(人民大)、Yaliang Li・Bolin Ding・Jingren Zhou(Alibaba)、Jun Wang(UCL)
- 代表的な成果: GenSim: A General Social Simulation Platform with LLM based Agents arXiv 2410.04360(NAACL 2025 demo、最大10万体)/ github.com/TangJiakai/GenSim
- 窓口・発信: GitHub https://github.com/TangJiakai/GenSim のみ確認
- 活動状況: v3 が 2025-07 改訂。以降の更新は未確認。
- 渋谷シムへの使いどころ: (5) A100×8 で10万体という実測構成は 39万体のGPU見積もりの比較点。誤り訂正(エラー時の自己修正)機構は長時間ランの安定化に。
- 既出: 新規
- 出典: https://arxiv.org/html/2410.04360v3

#### AgentScope(Alibaba Tongyi Lab)— 超大規模マルチエージェント・シミュレーション
- 種別: 企業(研究所)/ OSSコミュニティ
- 中心人物: Dawei Gao、Xuchen Pan、Yuexiang Xie、Yaliang Li、Bolin Ding、Jingren Zhou(Alibaba)、Ji-Rong Wen(人民大)
- 代表的な成果: Very Large-Scale Multi-Agent Simulation in AgentScope arXiv 2407.17789(サンプル: github.com/modelscope/agentscope/tree/main/examples/paper_large_scale_simulation)/ AgentScope 1.0 arXiv 2508.16279 / github.com/agentscope-ai/agentscope(約33.1k stars)
- 窓口・発信: ドキュメント https://docs.agentscope.io / Discord https://discord.gg/eYMpfnkG8h / DingTalk(README の QR)
- 活動状況: 非常に活発(2026-09〜10 に A2A 対応、Realtime 音声、TeamPipeline 等)。ただし現行ニュースにシミュレーション機能の記載は無く、汎用エージェント基盤に軸足。
- 渋谷シムへの使いどころ: (5) 2407.17789 の「アクターベース分散で大量エージェントを並列実行」実装は推論サーバ分散の参考。
- 既出: 新規
- 出典: https://arxiv.org/html/2407.17789v2 , https://arxiv.org/abs/2508.16279 , https://github.com/agentscope-ai/agentscope

#### 復旦大学 DISC / 上海創智学院(SII)— SocioVerse / SocioVerse2
- 種別: 研究室
- 中心人物: Zhongyu Wei(魏忠钰、Fudan、責任著者)、Xinnong Zhang、Jiayu Lin、Jia Wang ほか(KCL・Oxford も参加)
- 代表的な成果: SocioVerse: A World Model for Social Simulation Powered by LLM Agents and A Pool of 10 Million Real-World Users arXiv 2504.10157 / **SocioVerse2: A Longitudinal Dynamic Social Simulation Framework under a Human-AI Co-evolutionary Paradigm arXiv 2609.24911(2026-09)** / **github.com/sii-research/SocioVerse2(v0.2.0, 2026-09-25 公開)** / 付随 ABM github.com/Lishi905/SocioVerse-ABM
- 窓口・発信: https://socioverse.fudan-disc.com/ / ドキュメント https://socioverse.fudan-disc.com/docs/ / ホステッド Workbench https://socioverse.fudan-disc.com/studies / PyPI https://pypi.org/project/socioverse2/ / contact@socioverse.fudan-disc.com / **SocioVerse Challenge 2026 https://socioverse.fudan-disc.com/challenge/(CIKM 2026 LASS ワークショップ併催・ローマ、授賞 11/8、賞金等 $17,600、参加登録後にコミュニティグループ招待)** / challenge26@socioverse.fudan-disc.com
- 活動状況: 非常に新しい(2026-09〜10)。SocioVerse2 は固定IDの人口が変化する環境を逐次経験し、各ステップを DuckDB パネルデータ化、任意時点で介入して反事実ブランチ(親のアクションをリプレイ)。Claude Code / Codex 用 `/sv-*` スキル同梱。
- 渋谷シムへの使いどころ: (4) 持続 ID・縦断パネル・反事実ブランチは複数日ランとアンサンブル予測(多ラン分布)の設計そのもの。(3) 実世界シグナル(ニュース・FRED・価格)で環境を駆動する構成は較正の参考。Challenge は国際発表の場として検討余地。
- 既出: 2504.10157 は既出(論文)。SocioVerse2(2609.24911・repo・Challenge)は新規
- 出典: https://github.com/sii-research/SocioVerse2 , https://socioverse.fudan-disc.com/ , https://socioverse.fudan-disc.com/challenge/ , https://www.besthub.dev/articles/socioverse2-longitudinal-social-simulation-with-counterfactual-branching-9e1632246da4

#### Y Social(Giulio Rossetti, CNR-ISTI / Pisa)
- 種別: OSSコミュニティ / 研究室
- 中心人物: Giulio Rossetti(CNR-ISTI 上級研究員、ピサ大 KDD Lab)、Erica Cau、Andrea Failla
- 代表的な成果: Y Social: an LLM-powered Social Media Digital Twin arXiv 2408.00818 / GitHub org https://github.com/YSocialTwin(YSocial, YServer, YClient, YClientReddit, YPhotoSharing, ysights 等 13 repo)/ Docker https://hub.docker.com/r/rossetti/ysocial
- 窓口・発信: https://y-not.social (Blog「News from the Agents」あり)/ https://YSocialTwin.github.io / GitHub Discussions https://github.com/orgs/YSocialTwin/discussions / Rossetti 個人 https://giuliorossetti.github.io/ / X https://twitter.com/giuliorossetti / Mastodon https://mastodon.uno/@giuliorossetti
- 活動状況: 活発(YSocial 2026-10-03 更新、多数 repo 2026-09 更新)。Sage Concept Grants 受賞。
- 渋谷シムへの使いどころ: (8) ノーコード Web UI+分析モジュール(ysights)の構成は、顧客向けダッシュボードの参考。(2) Reddit 型・写真共有型など複数の相互作用様式のクライアント分離設計。
- 既出: 既出(論文 2408.00818)。GitHub org・サイトは新規
- 出典: https://github.com/YSocialTwin , http://y-not.social , https://giuliorossetti.github.io/

#### Humanoid Agents(Zhilin Wang ほか)
- 種別: 個人(研究者)/ OSS
- 中心人物: Zhilin Wang、Yu Ying Chiu、Yu Cheung Chiu
- 代表的な成果: Humanoid Agents arXiv 2310.05418(EMNLP 2023 demo)/ github.com/HumanoidAgents/HumanoidAgents(約322 stars)
- 窓口・発信: http://www.humanoidagents.com/ (Unity WebGL デモ)
- 活動状況: repo は 24 コミットで停滞気味。2025〜2026 の新作は未確認。
- 渋谷シムへの使いどころ: (1) 基本欲求(空腹・睡眠・社交など)+感情+関係親密度を状態変数として持つ設計は既読だが、空腹偏重問題では「複数欲求の満足度を同列に扱い減衰率を分ける」点を再確認する価値あり。
- 既出: 既出(論文・コード)
- 出典: https://github.com/HumanoidAgents/HumanoidAgents , https://arxiv.org/abs/2310.05418v1

#### Lyfe Agents → Altera → Fundamental Research Labs(Guangyu Robert Yang)
- 重複のため「企業」タブの同名項目にまとめた

#### Navid Ghaffarzadegan ほか — Generative Agent-Based Modeling(GABM)
- 種別: 個人(研究者)
- 中心人物: Navid Ghaffarzadegan、Aritra Majumdar、Ross Williams、Niyousha Hosseinichimeh(所属は Virginia Tech と記憶するが本調査では未確認)
- 代表的な成果: Generative ABM: Unveiling Social System Dynamics through Coupling Mechanistic Models with Generative AI arXiv 2309.11456 / Generative agent-based modeling: an introduction and tutorial(System Dynamics Review 2024、arXiv 2307.04986)/ Designing Reliable Experiments with GABM: A Comprehensive Guide Using Concordia arXiv 2411.07038
- 窓口・発信: 未確認(論文のみ)
- 活動状況: 2025〜2026 の新作は未確認。
- 渋谷シムへの使いどころ: (1)(7) 「機械論モデル(システムダイナミクス)+LLM の意思決定」の結合は、群衆物理層と LLM 判断を分ける設計の理論的根拠。
- 既出: 2411.07038 は既出。2309.11456 / 2307.04986 は新規
- 出典: https://arxiv.org/abs/2309.11456v1 , https://ideas.repec.org/p/arx/papers/2307.04986.html , https://arxiv.org/pdf/2411.07038

#### Complexity Science Hub Vienna — Social Simulation With LLMs ワークショップ
- 種別: 学会・ワークショップ / 研究所
- 中心人物: David Garcia、Mirta Galesic、Henrik Olsson(主催)。講演: Markus Strohmaier・Georg Ahnert・Max Pellert(Mannheim)、Indira Sen・Giordano De Marzo(Konstanz)、Jana Lasser(Graz)、Chris Bail(Duke)、Gaël Le Mens(UPF)、Bob West(EPFL)ほか
- 代表的な成果: CSH Workshop「Social Simulation With Large Language Models」(2024-05-27〜29、ウィーン)
- 窓口・発信: アジェンダ PDF https://csh.ac.at/wp-content/uploads/2024/05/Agenda-Workshop-Social-Simulation-With-Large-Language-Models-1.pdf
- 活動状況: 2025〜2026 の後継開催は未確認。欧州の LLM×ABM 研究者ネットワーク(Mannheim/Konstanz/Graz)を俯瞰できる名簿として有用。
- 渋谷シムへの使いどころ: (6) 講演者の個別研究(LLM の人口代表性・バイアス)は検証方法の追加文献源。
- 既出: 新規
- 出典: https://csh.ac.at/wp-content/uploads/2024/05/Agenda-Workshop-Social-Simulation-With-Large-Language-Models-1.pdf

#### ESSA SIG-LLM4ABM(European Social Simulation Association)
- 重複のため「コミュニティ・学会」タブの同名項目にまとめた

#### Helmholtz Munich Institute for Human-Centered AI — Centaur(Marcel Binz, Eric Schulz)
- 重複のため「検証・ペルソナ・記憶・推論」タブの同名項目にまとめた

#### Microsoft TinyTroupe(Paulo Salem ほか)
- 重複のため「企業」タブの同名項目にまとめた

#### Serina Chang(UC Berkeley EECS / BAIR)
- 種別: 個人(研究者)
- 中心人物: Serina Chang(UC Berkeley 助教、CS222 ゲスト講師)
- 代表的な成果: **Learning demographic-conditioned mobility trajectories with aggregate supervision arXiv 2603.03275(2026)** / **Graph-based alternatives to LLMs for human simulation arXiv 2511.02135(ACL 2026)** / **Allocating human samples toward fine-tuning vs. post-hoc statistical corrections in LLM survey simulations arXiv 2510.11408(ACL 2026)** / What do LLMs know about opinions?(ICLR 2026)/ 世論分布予測の微調整(ACL 2025)/ COVID 期のモビリティネットワーク研究
- 窓口・発信: https://serinachang5.github.io/ / X https://x.com/serinachang5
- 活動状況: 活発。2026 夏開始のポスドク募集中。
- 渋谷シムへの使いどころ: (3) **集計データ(人流)だけを教師に属性別の移動軌跡を学習する 2603.03275 は、KDDI 人流(集計)に合わせて来街者比・時刻分布を較正する問題とほぼ同型**。(5)(6) 2511.02135 の「LLM でなくグラフモデルで人間シミュ」は System 1.5 の代替案、2510.11408 は少量の実人間データの使い方(微調整 vs 事後補正)の指針。
- 既出: 新規
- 出典: https://serinachang5.github.io/

#### SimBench(Cambridge / Bocconi ほか)
- 重複のため「検証・ペルソナ・記憶・推論」タブの同名項目にまとめた

#### Stanford SALT Lab(Diyi Yang)
- 種別: 研究室
- 中心人物: Diyi Yang(Stanford NLP)
- 代表的な成果: Concordia Contest パネル登壇、Anthis らの position 論文周辺の人間-エージェント協働評価研究(個別のシミュ論文は本調査では未特定)
- 窓口・発信: https://saltlab.stanford.edu/ / https://cs.stanford.edu/~diyiy/index.html / メンバー一覧 https://cs.stanford.edu/~diyiy/group.html
- 活動状況: 活動中(詳細未確認)。
- 渋谷シムへの使いどころ: (2) 社会的言語技術・対話の評価枠組みは会話品質評価の補助文献。優先度低。
- 既出: 新規
- 出典: https://cs.stanford.edu/~diyiy/group.html , https://www.cooperativeai.com/post/concordia-contest

#### 東京大学 空間情報科学研究センター — Renhe Jiang(LLM エージェント移動生成)
- 重複のため「都市・人流・群衆」タブの同名項目にまとめた

#### Yiming Li & Dacheng Tao — "AI Agents Alone Are Not (Yet) Sufficient for Social Simulation"
- 種別: その他(position 論文)
- 中心人物: Yiming Li、Dacheng Tao
- 代表的な成果: arXiv 2603.00113(2026-02)
- 窓口・発信: 未確認
- 活動状況: 2026-02 公開。
- 渋谷シムへの使いどころ: (2)(6) 「結果がエージェントでなくスケジューリング・相互作用プロトコル・初期情報で決まってしまう」という指摘は、会話 0.07% の原因が遭遇スケジューリング側にないかの点検に。環境込みマルコフゲームとしての定式化は論文化時の枠組みに。
- 既出: 既出(論文)
- 出典: https://arxiv.org/abs/2603.00113v1

---

### 担当範囲で見つからなかった/確認できなかったもの
- WebSearch の上限(全エージェント共有 200 回)に途中で達したため、以下は検索で裏が取れず記載を見送り/未確認とした: 北京大・上海 AI Lab の大規模エージェント研究、Shanghai AI Lab 系の社会シミュ、Oxford/Cambridge/UW の個別グループ(SimBench 以外)、Santa Fe Institute の LLM×ABM 活動、MiroFish 等の OASIS 派生、Lyfe Agents 著者の所属、Ghaffarzadegan の現所属、Simile 以外の Stanford スピンアウトの有無。
- Ayush Chopra の博士論文審査日・修了後の進路、AgentTorch の企業化は確認できず(MIT 頁はエラー)。
- Expected Parrot の調達額、CAMEL-AI / Eigent の資金調達、FIB Lab・人民大・復旦の Discord/WeChat 公開窓口は確認できず。
- CS222 の 2025 年以降の開講・資料公開は確認できず(2026-27 秋は Bulletin 掲載のみ)。
- joonspk-research/genagents(1,000人エージェントバンクのコード)の repo 頁は取得エラーで未確認。


## 2. 企業・スタートアップ


調査日: 2026-10-13。全エントリは WebSearch / WebFetch で確認した URL のみ記載。数値(精度・顧客数など)は**各社の自己申告**であり第三者検証ではない点に注意。
注: 調査途中で WebSearch の上限(1ターン 200 回、全エージェント共有)に達したため、後半は公式サイトの直接 WebFetch で裏取りした。検索し切れなかったものは末尾に記載。

---

### A. 合成消費者・合成パネル(「人の反応」を売る)系 — 詰まりどころ8(事業化)の直接の先行事例

#### Simile
- 種別: スタートアップ
- 中心人物: Joon Sung Park(CEO、Generative Agents/Smallville の筆頭著者、Stanford PhD)、Michael Bernstein(Stanford)、Percy Liang(Stanford)、Lainie Yallen(ビジネス側共同創業者、元 Hebbia)。エンジェルに Andrej Karpathy、Fei-Fei Li
- 代表的な成果: Generative Agents (arXiv 2304.03442)/Generative Agent Simulations of 1,000 People (arXiv 2411.10109)/Social Simulacra (UIST 2022, arXiv 2208.04024)/Finetuning LLMs for Human Behavior Prediction in Social Science Experiments(EMNLP 2025、210実験・290万回答で微調整)。製品は「人間行動の基盤モデル」による "agentic twins"
- 窓口・発信: https://www.simile.com/ / ブログ https://www.simile.com/blog / X https://x.com/simile_ai / LinkedIn https://www.linkedin.com/company/simile-ai-inc/ / 求人 https://jobs.ashbyhq.com/simile
- 活動状況: 2026-02-12 ステルス解除と同時に $100M(Index Ventures リード、Bain Capital Ventures, A*, Hanabi)。2026-07-30 Series B $200M、評価額 $2B(Greenoaks リード、Index, Hanabi, BCV, A*, Factory, Definition, CVS Health Ventures)。累計約 $300M、従業員50人超、ローンチ5か月で売上5倍。顧客: CVS Health(40万体の agentic twin で服薬アドヒアランス検討)、Wealthfront、Gallup(提携・代表パネル)、Itaú、Deloitte、Suntory Beverages & Food、Telstra など。価格は「パネルが大きいほど高い」のみ公開。ブログは 2026-09 まで更新(Itaú 事例、"Building the What-If Machine"、"Building confidence in Simile")。週7,000件超の対人間評価、各シミュに精度予測を付ける confidence model、ドリフト監視とデータ再収集を謳う
- 渋谷シムへの使いどころ: (6)(8) 「1,000人インタビュー→個人ツイン→人間の test-retest 一致率で正規化した精度(85%)」という検証設計と、結果ごとに予測精度を付ける confidence model は、渋谷シムの holdout 照合の出し方の手本。(8) 顧客が小売・ヘルスケア・金融で「出店・価格・施策の事前リハーサル」に払っている実例。(4) ドリフト監視の考え方
- 既出: 論文は既出(2304.03442, 2411.10109, 2208.04024)。会社としては新規
- 出典: https://www.implicator.ai/the-stanford-team-that-invented-generative-agents-wants-to-kill-the-focus-group.md / https://dealroom.co/news/142224-simile-raises-200m-series-b-at-2b-valuation-to-survey-ai-twins-of-consum/ / https://techcrunch.com/?p=3148353 / https://www.simile.com/ / https://www.simile.com/blog / https://www.simile.com/blog/the-simulation-company

#### Aaru
- 種別: スタートアップ
- 中心人物: Cameron (Cam) Fink、Ned Koh、John Kessler(CTO、MIT City Science Lab でシミュレーション研究)
- 代表的な成果: "Population simulation at the replication floor"(2026-09-24、2,993問・186調査・9業界で検証、平均 TVD 7.62pt/MAE 3.53pt、Pearson 0.970、クレカ購買パネル340ブランド対で順序正答92.4%、自己推定信頼度の AUROC 0.845)。EY Global Wealth Study、Breakwater(4万体の模擬投資家)事例
- 窓口・発信: https://aaru.com/ / 論文・リサーチノート https://aaru.com/publications / X https://x.com/aaruhq / LinkedIn https://www.linkedin.com/company/aaru-ai
- 活動状況: 2024-03 創業。2025-12 Series A(Redpoint リード、$50M超と報道、一部株式は $1B「ヘッドライン」評価額、ブレンドでは $1B未満、ARR は $10M 未満と報道)。既存投資家 A*, Abstract, Felicis, General Catalyst, Accenture Ventures, Z Fellows, K5 Global, Nordstar。顧客 Accenture, EY, IPG、政治キャンペーン(2024 NY 民主党予備選を的中と報道)。拠点 NY・シンガポール・SF
- 渋谷シムへの使いどころ: (6) 「人間同士の再調査ばらつき(replication floor)を精度の床とみなす」発想は、KDDI 人流照合の合格ラインを"人流データ自体の日次ばらつき"で決める根拠に使える。(6) 質問ごとに誤差を事前推定し確信度の高い半分だけ出す方法も流用可。(8) CTO が MIT City Science 出身=都市シム→消費者シムへの事業転換例
- 既出: 新規
- 出典: https://techcrunch.com/2025/12/05/ai-synthetic-research-startup-aaru-raised-a-series-a-at-a-1b-headline-valuation / https://aaru.com/ / https://aaru.com/about / https://aaru.com/publications / https://aaru.com/publications/population-simulation-at-the-replication-floor-summary

#### Expected Parrot(EDSL)
- 種別: スタートアップ / OSSコミュニティ
- 中心人物: John J. Horton(CTO、MIT Sloan 准教授・経済学者、"Homo silicus" 論の提唱者)、Robin Horton(CEO、元 Uber)
- 代表的な成果: EDSL(MIT ライセンス、AIエージェント×多LLMで調査・実験を回す Python DSL)https://github.com/expectedparrot/edsl(約494★)
- 窓口・発信: https://www.expectedparrot.com/ / Docs https://docs.expectedparrot.com / Discord https://discord.com/invite/mxAYkjfy9m / Substack https://blog.expectedparrot.com / X https://x.com/ExpectedParrot / Horton 個人ページ https://john-joseph-horton.com/expected-parrot.html
- 活動状況: YC Fall 2025、ボストン、5名、Active。研究者にはクレジット提供(メールで申請)。Horton 個人ページは 2026-08-28 更新、2026-07 に投稿あり。Prolific 連携・"Humanize" で人間回答を併取できる
- 渋谷シムへの使いどころ: (6) 同じ質問票を LLM と人間に同時投入して比較する仕組み(人間-in-the-loop)が既製で、渋谷シムのペルソナ妥当性検査(来街目的・滞在意向アンケート)をそのまま作れる。(5) リモートキャッシュで同一プロンプトの再計算を省く設計も参考。研究者クレジットは未踏期間中の推論費の足しになり得る
- 既出: 新規
- 出典: https://ycombinator.com/companies/expected-parrot / https://john-joseph-horton.com/expected-parrot.html / https://github.com/expectedparrot/edsl / https://docs.expectedparrot.com/en/latest/

#### Artificial Societies
- 種別: スタートアップ
- 中心人物: James He(CEO、計算社会科学)、Patrick Sharpe(CPO、応用行動科学)、Tom Whittle(創業エンジニア)
- 代表的な成果: 製品 Radiant(社会=ペルソナ同士がつながり影響し合うネットワークで反応を予測)、Live Focus Group / Live Society。評価ページで分布精度 86%(人間の自己再現上限 91%、伝記プロンプトLLM 67%)、自己矛盾率 <2%、1,000件の実調査で検証(2026-01レポート)、9種の既製LLMと 68,280 回答で比較
- 窓口・発信: https://societies.ai/(旧 societies.io)/ 評価 https://societies.ai/eval / X https://x.com/societies_ai / LinkedIn https://www.linkedin.com/company/artificial-societies / GitHub https://github.com/artificial-societies
- 活動状況: 2024 ロンドン創業、YC W25、18名。2025-08 に pre-seed+seed 計 $5.35M(Kindred Capital・Point72 Ventures リード、YC, Pioneer Fund 他、エンジェルに Taro Fukuyama ほか)。初期は1社会 20〜300 ペルソナ、無料3クレジット→Pro 無制限のセルフサーブ。現在は社会 12〜3,500 ペルソナ、デモ予約制のエンタープライズ(GDPR/SOC2、EU ホスティング)へ移行
- 渋谷シムへの使いどころ: (2) 「ペルソナ同士の関係・影響パターンでクラスタ化した社会」に議論させる設計=会話が起きない問題への別アプローチ(場所での偶然の会話ではなく、社会ネットワーク上で話題を流す)。(8) 低価格セルフサーブ→エンタープライズへの移行という価格戦略の変遷
- 既出: 新規
- 出典: https://www.unite.ai/artificial-societies-raises-5-35m-to-make-ai-powered-social-simulations-universally-accessible/ / https://siliconcanals.com/yc-backed-artificial-societies-bags-e4-5m/ / https://finance.yahoo.com/news/y-combinator-startup-using-ai-080002341.html / https://www.ycombinator.com/companies/artificial-societies / https://societies.ai/ / https://societies.ai/eval

#### Electric Twin
- 種別: スタートアップ
- 中心人物: Alex Cooper(CEO、元英国 Covid 大量検査担当)、Dr Ben Warner(元英首相 デジタル・データ首席顧問)。LSE の Michael Muthukrishna と検証研究
- 代表的な成果: 顧客の調査データから synthetic audience を作る。ホールドアウト検証(調査データを2分割、片方で構築・他方で照合)、指標 1-MAE 最大96%、分布指標 NDAM 92%(GPT-5 は65%、人間の再回答上限94%)。6,000万回答・280データセットで評価と主張
- 窓口・発信: https://www.electrictwin.com/ / 精度 https://www.electrictwin.com/accuracy / ブログ https://www.electrictwin.com/blog
- 活動状況: 2026-02-12/13 に $10M(Atomico リード、LocalGlobe, Mercuri, Samos、エンジェルに Marc Andreessen, Cal Henderson, Palantir UK の Louis Mosley ほか)、未公表 pre-seed $4M と合わせ累計 $14M。顧客 News UK(The Times)、Lebara、Virgin、Wingstop、Sage など。価格は「ライセンス料で質問無制限、クエリ課金なし」
- 渋谷シムへの使いどころ: (6) 「データ分割→片側で構築→未見側で照合」「平均一致(MAE)と分布一致(NDAM)を分けて報告」「人間の再回答一致を上限として併記」の3点セットは、KDDI 人流 holdout 照合レポートの書式としてそのまま使える。(8) 公共政策出身者が企業向けに売っている例
- 既出: 新規
- 出典: https://itbrief.co.uk/story/electric-twin-raises-usd-14m-to-scale-ai-audiences / https://www.research-live.com/article/news/electric-twin-raises-10m-in-funding-round/id/5146836 / https://www.electrictwin.com/ / https://www.electrictwin.com/accuracy

#### Synthetic Users
- 種別: スタートアップ
- 中心人物: Kwame Ferreira(CEO)、Artur Ventura(CTO)、Hugo Alves(共同創業者・Lead PM、ポッドキャストで発信)
- 代表的な成果: 合成ユーザーへの UX インタビュー・テスト(画像・動画・実Webサイトも対象)
- 窓口・発信: https://www.syntheticusers.com/ / チーム https://www.syntheticusers.com/team / 価格 https://www.syntheticusers.com/pricing / Hugo Alves 出演回 https://oneknightinproduct.podbean.com/e/hugo-alves-lets-get-real-about-synthetic-users-with-hugo-alves-co-founder-synthetic-users/(2026-02-21)
- 活動状況: 稼働中。価格は年額 $12,500〜(トークンプール制、10問インタビュー≒1,250トークン、1インタビュー $2〜60、未使用20%繰越、シート無制限)。資金調達額は未確認
- 渋谷シムへの使いどころ: (8) 価格が公開されている数少ない例。「年額ライセンス+従量トークン」の価格設計は、渋谷シムを出店検討向けに売る際の価格表のたたき台になる
- 既出: 新規
- 出典: https://www.syntheticusers.com/team / https://www.syntheticusers.com/pricing / https://oneknightinproduct.podbean.com/e/hugo-alves-lets-get-real-about-synthetic-users-with-hugo-alves-co-founder-synthetic-users/

#### Evidenza
- 種別: スタートアップ
- 中心人物: Peter Weinberg、Jon Lombardo(ともに元 LinkedIn B2B Institute)、Brian Watroba。アドバイザーに Mark Ritson、Stefano Puntoni(Wharton)
- 代表的な成果: B2B 購買者(CIO/CFO 等)の合成パネル "impersonas"。100件超の検証で類似度スコア 88% と主張。ServiceNow・Salesforce・EY 事例
- 窓口・発信: https://www.evidenza.ai/ / リサーチ https://www.evidenza.ai/research / YouTube @LabGrownMarketing
- 活動状況: 外部調達なし・ブートストラップで黒字と報道(2025-06)。顧客100社超。現在はコンサル型 Full Service(72時間納品)、Self Service は waitlist
- 渋谷シムへの使いどころ: (8) VC資金なしで「コンサル納品型」で黒字化した例。渋谷シムも最初はツール販売ではなく「出店検討レポート納品」型で売る選択肢の根拠になる
- 既出: 新規
- 出典: https://www.thedrum.com/news/2025/06/04/lab-grown-marketing-it-s-already-here-and-it-s-synthetic-scalable-and-very-real / https://www.evidenza.ai/

#### Subconscious.ai
- 種別: スタートアップ
- 中心人物: Avi Yashchin(ポッドキャストで発信、創業者と推定されるが役職は未確認)
- 代表的な成果: 模擬購買者による因果実験(コンジョイント、MaxDiff、価格テスト)。Working paper "Causal fidelity"(2026-07、査読前、43件の人間実験とパラメータ順位一致 0.73)https://fidelity.subconscious.ai/papers/causal-fidelity/causal_fidelity_paper.pdf 。World Simulator https://world.subconscious.ai 、MCP 連携
- 窓口・発信: https://www.subconscious.ai/ / Docs https://docs.subconscious.ai / ニュースレター https://newsletter.subconscious.ai / ポッドキャスト https://www.pragmaticinstitute.com/resources/podcasts/product/ai-behavioral-economics-and-the-future-of-market-research-with-avi-yashchin/
- 活動状況: UChicago Polsky Transform Cohort 2(2023)。2026-07 に論文公開、サイト稼働中。調達額は未確認
- 渋谷シムへの使いどころ: (6) 「水準の一致」ではなく「施策の効果の向き・順位が人間実験と一致するか」で検証する方針は、渋谷シムで「新店舗を置いたら来街が増えるか」の介入効果の妥当性を測る指標設計に使える
- 既出: 新規
- 出典: https://www.subconscious.ai/ / https://polsky.uchicago.edu/2023/11/15/meet-the-transform-cohort-2-startups-subconciousai/ / https://www.pragmaticinstitute.com/resources/podcasts/product/ai-behavioral-economics-and-the-future-of-market-research-with-avi-yashchin/

#### CulturePulse
- 種別: スタートアップ
- 中心人物: Justin E. Lane(CEO)、F. LeRon Shults、Brian Swichkow、Maja Roknic
- 代表的な成果: ARES(聴衆の行動・心理デジタルツイン、50カテゴリ超×70言語)。マルチエージェント社会シミュレーション研究の系譜(Lane/Shults は宗教・紛争の ABM 研究者)だが、製品に LLM エージェントを使うかは未確認
- 窓口・発信: https://www.culturepulse.ai/
- 活動状況: 2021 創業、米・スロバキア。2023 に $1M(Zero Gravity Capital)、2025-02 Series A €1.45〜1.5M(Rockaway Ventures リード)
- 渋谷シムへの使いどころ: (8) 安全保障・リスク予測という別市場。行政向けに売る際の比較対象
- 既出: 新規
- 出典: https://en.ain.ua/2025/02/07/culturepulse-raises-eur145m / https://www.culturepulse.ai/

#### Keplar
- 種別: スタートアップ(隣接領域:合成ではなく AI 音声インタビュアー)
- 中心人物: Dhruv Guliani(元 Google 音声AI)、William Wen
- 代表的な成果: 実在顧客に AI が音声で聞き取り、レポート・スライドを自動生成
- 窓口・発信: 未確認(公式URLは未取得)
- 活動状況: 2025-09 シード $3.2〜3.4M(Kleiner Perkins リード、SV Angel, South Park Commons)。顧客 Clorox、Intercom。競合として Outset($17M、8VC)、Listen Labs($27M、Sequoia)が挙がる
- 渋谷シムへの使いどころ: (6) 検証用の「本物の人の声」を安く集める手段。渋谷来街者への短時間インタビューを AI で回し、エージェントの来街理由と照合するデータ源になり得る
- 既出: 新規
- 出典: https://techcrunch.com/2025/09/17/kleiner-perkins-backed-voice-ai-startup-keplar-aims-to-replace-traditional-market-research

#### Qualtrics(Edge Audiences の合成パネル)
- 種別: 企業
- 中心人物: 未確認(企業発表)
- 代表的な成果: 市場調査向けに微調整した独自 LLM による米国合成消費者パネル(2026-03 X4 サミットで発表、第三者の2億人超の回答者データに基づくと報道、汎用LLMの12倍精度と主張)。2025-10 の TMRE ブログで検証4段階(一般化・形・多様性・転移性)
- 窓口・発信: https://www.qualtrics.com/articles/strategy-research/synthetic-research-breakthrough/ / https://www.qualtrics.com/articles/news/new-market-research-capabilities-x4-2026/
- 活動状況: 2026 上期に英・愛・加・豪・NZ へ拡大予定と発表。価格非公開
- 渋谷シムへの使いどころ: (8) 大手調査会社が「合成+人間のブレンド」を標準化しつつある=渋谷シムも「実調査を置き換える」より「実調査の前段の安いスクリーニング」と位置づけると既存予算に乗りやすい
- 既出: 新規
- 出典: https://siliconangle.com/2026/03/18/qualtrics-adds-ai-powered-synthetic-data-research-tools-speed-customer-insights/ / https://www.qualtrics.com/articles/strategy-research/synthetic-research-breakthrough/

#### Toluna(HarmonAIze Personas)
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: 米国パネル 1,940万人の一次データから「個人の回答」を模倣する合成ペルソナ(セグメント平均ではなく個人単位)。Toluna Start のクレームテストに統合
- 窓口・発信: https://tolunacorporate.com/transforming-consumer-insights-meet-tolunas-next-gen-synthetic-respondents/
- 活動状況: 2025-02-05 米国で提供開始、英仏に拡大予定(2026年の続報は未確認)
- 渋谷シムへの使いどころ: (8)(6) 「大規模実パネルを持つ者が合成で勝つ」構図の例。日本なら同様のパネル保有者(調査会社・ポイント事業者)との提携が較正データ確保の近道
- 既出: 新規
- 出典: https://www.research-live.com/article/news/toluna-releases-synthetic-personas-in-us/id/5135503 / https://tolunacorporate.com/transforming-consumer-insights-meet-tolunas-next-gen-synthetic-respondents/

#### Ipsos(PersonaBot)
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: セグメンテーション調査+定性データ+マルチメディアから生成AIペルソナを作り社内で対話させる PersonaBot。POV "Personas in the Age of AI"(2025-08)
- 窓口・発信: https://www.ipsos.com/en-vn/discover-ipsos-personabot / https://www.ipsos.com/sites/default/files/ct/publication/documents/2025-08/Personas%20In%20The%20Age%20Of%20AI.pdf
- 活動状況: 2025-07 頃からグローバル展開。合成データ webinar も開催。2026年の新展開は未確認
- 渋谷シムへの使いどころ: (8) 既存のセグメント調査を「話せるペルソナ」に変える付加価値売り。渋谷シムのエージェントを「出店者が話しかけられる来街者ペルソナ」として見せるデモの参考
- 既出: 新規
- 出典: https://www.ipsos.com/en-vn/discover-ipsos-personabot / https://www.ipsos.com/en-us/node/1049781

---

### B. 仮想世界・エージェント社会(研究/エンタメ)系

#### Fundamental Research Labs(旧 Altera)
- 種別: スタートアップ
- 中心人物: Dr. Robert (Guangyu Robert) Yang(元 MIT 教員、計算神経科学)
- 代表的な成果: Project Sid: Many-agent simulations toward AI civilization(arXiv 2411.00114、PIANO アーキテクチャ、Minecraft で最大1,000体)https://github.com/altera-al/project-sid(論文・動画のみ、コード非公開、約1.4k★)。現製品は Shortcut(表計算 AI アナリスト)http://shortcut.ai/ と Fairies
- 窓口・発信: https://fundamentalresearchlabs.com/ / ブログ https://fundamentalresearchlabs.com/blog / Project Sid 記事 https://fundamentalresearchlabs.com/blog/project-sid
- 活動状況: **2025-05-27 に Altera から改名、事業は生産性アプリへピボット**。2024 シード $9M(First Spark, Patron, a16z Speedrun, Eric Schmidt)、2025-08 Series A $33M(Prosus リード、Patrick Collison)、累計 $40M 超。ゲームチームは残存。Project Sid の続報は 2024-11 以降ブログに無い
- 渋谷シムへの使いどころ: (4)(5) PIANO(並列モジュール+認知コントローラで発話と行動の一貫性を保つ)は渋谷の System 1〜2β 階層と比較対象。(8) 「エージェント文明」研究から収益化のため業務エージェントへピボットした実例=研究デモだけでは売れないという警告
- 既出: 論文は既出(Project Sid)。会社の現況(改名・ピボット)は新規
- 出典: https://techcrunch.com/2025/08/01/fundamental-research-labs-nabs-30-million-from-prosus-to-build-ai-agents-for-multiple-verticals / https://fundamentalresearchlabs.com/ / https://github.com/altera-al/project-sid

#### Emergence AI(Emergence World)
- 種別: スタートアップ
- 中心人物: Satya Nitta(CEO、元 IBM Research)
- 代表的な成果: Emergence World(10体×5並行世界×15日、40以上の場所、120以上のツール、NYC の天気・実ニュース連動、エピソード記憶+日記型リフレクション+関係状態の3層記憶、憲法改正・投票・通貨 ComputeCredits)。Claude 版のみ全員生存・犯罪ゼロ、Gemini 3 Flash 版は15日で683件の犯罪、Grok 版は4日で全滅。リポジトリ https://github.com/EmergenceAI/Emergence-World(CC BY-NC 4.0、約570★、React Three Fiber+FastAPI+PostgreSQL)
- 窓口・発信: https://emergence.ai/ / ブログ https://emergence.ai/blog/emergence-world-a-laboratory-for-evaluating-long-horizon-agent-autonomy / world@emergence.ai / サイト world.emergence.ai
- 活動状況: 2026-05 公開(Fortune 2026-05-28 報道)。本業は半導体向け検証済み自律エージェント。資金調達額は今回未確認
- 渋谷シムへの使いどころ: (4) 複数日連続運転で「社会が徐々に劣化せず、ある点で一気に崩壊/協調する相転移」が観察された点、および3層記憶(エピソード/日記/関係)は、渋谷の複数日ラン・関係持続の設計と評価観点に直結。(1) GPT-5-mini 版でエージェントが自己の生存を忘れて7日で終了=欲求の重み付けの逆側の失敗例
- 既出: 新規
- 出典: https://www.fortune.com/2026/05/28/ai-model-simulation-claude-chatgpt-grok-gemini/ / https://emergence.ai/blog/emergence-world-a-laboratory-for-evaluating-long-horizon-agent-autonomy / https://github.com/EmergenceAI/Emergence-World / https://emergence.ai/

#### MiroFish(盛大集団/Shanda 出資)
- 種別: OSSプロジェクト / スタートアップ
- 中心人物: 郭航江 Guo Hangjiang("Baifu"、北京郵電大学の学部4年、20歳、前作は世論分析ツール BettaFish)。出資者 陳天橋 Chen Tianqiao(盛大集団創業者)
- 代表的な成果: https://github.com/666ghj/MiroFish(AGPL-3.0、約75.8k★)。ニュース・政策案などを種に GraphRAG で知識グラフ→数千体の人格付きエージェント生成→CAMEL-AI OASIS 上で SNS 型相互作用→予測レポート。記憶は Zep、推奨 LLM は Qwen-plus。ローカルGPU 版のフォーク "MiroFish-Offline" あり
- 窓口・発信: GitHub のみ確認
- 活動状況: 2026-03 に GitHub トレンド1位、バイラル直後に 3,000万元(約$4.1M)のシード。README は「高消費、まず40ラウンド未満で試せ」と警告
- 渋谷シムへの使いどころ: (8) 「予測」を前面に出した OSS が短期で巨大な注目と資金を得た事例(ただし批評記事は「予測ではなくシナリオ」と指摘)。(5) 推論コスト警告とローカル版フォークの存在は、コスト問題が普遍的であることの裏付け
- 既出: 新規(下敷きの OASIS は既出)
- 出典: https://perplexityaimagazine.com/ai-news/mirofish-ai-swarm-simulation-2026/ / https://github.com/666ghj/MiroFish

#### CAMEL-AI / Eigent
- 重複のため「研究室」タブの同名項目にまとめた

#### Microsoft TinyTroupe
- 種別: 企業(Microsoft の OSS)
- 中心人物: Paulo Salem(作者・リード)、Christopher Olsen、Yi Ding、Prerit Saxena、Robert Sim(アドバイザー)
- 代表的な成果: TinyTroupe: An LLM-powered Multiagent Persona Simulation Toolkit(arXiv 2507.09788)https://github.com/microsoft/TinyTroupe(約7.6k★、v0.7.0 2026-03-28 で画像入力対応)。TinyPerson / TinyWorld で広告評価・フォーカスグループ・合成データ
- 窓口・発信: GitHub
- 活動状況: 2026-03 にリリースあり、活動中
- 渋谷シムへの使いどころ: (2)(6) ペルソナ仕様の書き方、会話の抽出・検証ユーティリティ、ビジネス用途テンプレ(広告評価)を参考に、店舗前での会話・評判伝播の小規模実験を先に作れる
- 既出: 新規(arXiv 2507.09788 は known_arxiv に無し)
- 出典: https://github.com/microsoft/TinyTroupe

#### Fable Simulation(旧 Fable Studio / The Simulation)— Showrunner
- 種別: スタートアップ
- 中心人物: Edward Saatchi(CEO、元 Oculus Story Studio)、Pete Billington(共同創業)、Frank Carey(CTO)、Jacob Madden(技術責任者)
- 代表的な成果: SHOW-1(エージェント社会から TV エピソード生成、2023-07)、SAGA: Skill to Action Generation for Agents https://github.com/fablestudio/fable-saga(MIT、約85★)、マルチエージェント Gym "Thistle Gulch"(西部の町17体)https://github.com/fablestudio/thistle-gulch 。現製品 Showrunner(AI生成アニメ配信・制作、独自モデル SHOW-2)
- 窓口・発信: https://www.showrunnerstudio.com/(旧 showrunner.xyz)/ Discord https://discord.gg/ymf4v2Gfa9 / X https://twitter.com/fablesimulation
- 活動状況: 2025-07-30 Amazon が出資(額非公開、Day One, 8VC, Greycroft も)。Showrunner は無料開始→クリエイター月$10〜20 想定。2026年時点でサイト稼働中
- 渋谷シムへの使いどころ: (8) 「シミュレーション世界」をエンタメ消費財として売る路線。北極星(AI住民のいるメタバース)との接続を考えるなら最も近い事業例。SAGA の「スキル候補生成→スコア→実行」は System 2 の行動選択 API の参考
- 既出: 新規
- 出典: https://getcoai.com/news/amazon-backs-fables-ai-platform-that-turns-text-into-tv-episodes/ / https://gamesbeat.com/the-simulation-by-fable-open-sources-ai-tool-to-power-westworlds-of-the-future/ / https://en.wikipedia.org/wiki/Fable_Studio / https://github.com/fablestudio/fable-saga / https://github.com/fablestudio/thistle-gulch / https://www.showrunnerstudio.com/

#### a16z AI Town / AI Stack Devs
- 重複のため「コミュニティ・学会」タブの同名項目にまとめた

#### Moltbook(Meta が買収)
- 種別: その他(AIエージェント専用SNS)
- 中心人物: Matt Schlicht(@mattprd)、Ben Parr
- 代表的な成果: OpenClaw(旧 Moltbot)エージェントが投稿・投票する Reddit 型 SNS
- 窓口・発信: https://www.moltbook.com/
- 活動状況: 2026-01〜02 にバイラル、**2026-03 Meta が買収発表**(条件非公開、両創業者は Meta 入り)。OpenClaw 作者 Peter Steinberger は OpenAI に参加
- 渋谷シムへの使いどころ: (2) 実際の多種 LLM エージェントが自発的に会話する「野生のデータ」の例。シム内の会話が薄い問題を、実エージェント SNS のログと比較する観点。(8) エージェント社会そのものが大手に買われた事例
- 既出: 新規
- 出典: https://broadbandbreakfast.com/meta-to-acquire-moltbook-the-social-network-for-ai-agents.md / https://www.news4jax.com/business/2026/03/10/meta-to-acquire-moltbook-the-social-network-for-ai-agents/ / https://www.moltbook.com/

---

### C. NPC・キャラクター AI 系

#### Inworld AI
- 種別: スタートアップ
- 中心人物: Kylan Gibbs(CEO、元 DeepMind PM)、Ilya Gelfenbeyn(会長、API.AI 創業)、Michael Ermolenko
- 代表的な成果: Character Engine(2021)→ TTS-1(2025-08)、TTS 1.5(2026-01)、Realtime TTS-2(2026-05)、Agent Runtime、Realtime Router。GitHub https://github.com/inworld-ai
- 窓口・発信: https://inworld.ai/ / ブログ https://inworld.ai/blog / X https://x.com/inworld / Docs https://docs.inworld.ai/docs/introduction
- 活動状況: 累計 $100M超(2023-08 評価額 $500M超)。**ゲーム NPC から「コンシューマ規模のリアルタイム音声 AI 推論プロバイダ」へピボット**、Ultravox 買収を告知。価格: TTS $12.50/100万文字、LLM ルーティング手数料0%、専用GPU $5/GPU時〜
- 渋谷シムへの使いどころ: (5) NPC 会社が「推論コストと遅延」を事業の核に据え直した=大量エージェントの推論インフラが本当のボトルネックという示唆。専用GPU時間単価は GPU 調達の比較材料。(8) NPC 単体では事業が細いという教訓
- 既出: 新規
- 出典: https://aiwiki.ai/wiki/inworld_ai / https://inworld.ai/ / https://www.pocketgamer.biz/ai-startup-inworld-raises-another-50-million-for-a-500-million-valuation

#### Convai
- 種別: スタートアップ
- 中心人物: Purnendu Mukherjee(CEO、元 NVIDIA)、Prashant Mishra
- 代表的な成果: 3D 環境を知覚し行動する会話キャラ(長期記憶、感情、ナラティブ設計、Unity/Unreal/Roblox/NVIDIA ACE 連携)
- 窓口・発信: https://convai.com/ / Docs https://docs.convai.com/api-docs / フォーラム https://forum.convai.com/
- 活動状況: 2022 創業、シード約 $5M(2022-10)。フリーミアム、有料 $22/月〜(第三者まとめ)。2026年の新規調達は未確認
- 渋谷シムへの使いどころ: (7) 3D 空間を「見て」行動するキャラの実装は、PLATEAU 3D 上で可視化デモを作る際の部品候補
- 既出: 新規
- 出典: https://neuronfeed.com/startups/convai / https://convai.com/

#### Artificial Agency
- 種別: スタートアップ
- 中心人物: Brian Tanner(CEO)、Alex Kearney(元 DeepMind 研究者ら)
- 代表的な成果: Behavior Engine(NPC に動機・ルール・目標を与えて自律行動、Llama 3 等の OSS モデル使用)。2026-03 に記憶・マルチプレイ・Unity 対応、2026-04 Reflection Tree 買収(**完全オンデバイス実行**へ)、2026-09 Owlchemy Labs "Dimensional Double Shift" に搭載=「初の商用エージェント挙動ゲーム」と主張
- 窓口・発信: https://www.artificial.agency / ニュース https://www.artificial.agency/news / X https://x.com/ArtificialAgncy / YouTube https://www.youtube.com/@artificialagencyai
- 活動状況: 2024-07 に計 $16M(Radical Ventures, Toyota Ventures 共同リード)。2026-06 COO 就任。活発
- 渋谷シムへの使いどころ: (5) 小型モデルのオンデバイス化へ舵を切った=39万体を回すコストの解として「小モデル+ゲームループ」路線の実戦例。(1) 動機・目標ベースの行動選択設計
- 既出: 新規
- 出典: https://techcrunch.com/2024/07/18/artificial-agency-raises-video-game-npcs-ai / https://artificial.agency/

---

### D. 大規模シミュレーション基盤・デジタルツイン(LLM 以前からの企業)

#### Improbable
- 種別: 企業
- 中心人物: Herman Narula(CEO)
- 代表的な成果: SpatialOS(分散シミュレーション基盤、現在は歴史的扱い)、MSquared / Morpheus(大人数同時接続)、Somnia L1 ブロックチェーン開発受託
- 窓口・発信: https://www.improbable.io/
- 活動状況: 2023-09 にベンチャービルダー化。2025-09 Somnia メインネット、2025-11 FY2024 売上 £10M・現金 £162.8M、2025-12 Imporium と Unreal Creator Platform を Yuga Labs に売却、2026-02 AI と Web3 に注力を表明。防衛部門は以前に売却済み
- 渋谷シムへの使いどころ: (5)(8) 「大規模エージェント世界の基盤」を売る事業が、ゲーム→防衛→メタバース→Web3 と何度も転身した歴史。インフラ単体で売ることの難しさの教訓
- 既出: 新規
- 出典: https://yespress.io/improbable.md / https://www.improbable.io/ / https://www.theblock.co/post/254870/improbables-pivot-to-metaverse-experiences-is-paying-off-says-ceo-narula

#### Hadean
- 種別: スタートアップ(防衛)
- 中心人物: Craig Beddis(CEO)
- 代表的な成果: populAI(訓練・ウォーゲーム用に民間人・SNS・交通・インフラを含む「生きた環境」を AI で生成)、dominAI、optimAI
- 窓口・発信: https://hadean.com/ / ニュース https://hadean.com/news/ / ブログ https://hadean.com/blog/
- 活動状況: 2022 Series A $30M、2026-03 ブリッジラウンド(British Business Bank £2.1M、Booz Allen Ventures, EF, Twin Track)で Series B 準備中。2026-07 NATO DIANA 選出。顧客 英国防省・米国防総省。Palantir、Booz Allen と提携
- 渋谷シムへの使いどころ: (8) 「群衆・民間人の生活パターン」を合成する需要は防衛・防災にもある。行政・再開発向けの延長として「災害時の渋谷駅避難リハーサル」用途の比較対象。(7) 群衆層
- 既出: 新規
- 出典: https://www.uktech.news/defence-tech/ai-conflict-simulation-firm-hadean-secures-bridge-round-20260312 / https://hadean.com/ / https://hadean.com/populai/

#### Cosmo Tech
- 種別: 企業
- 中心人物: Phillip Hazen(CEO、元 Accenture、2024-12 就任)
- 代表的な成果: 組織・サプライチェーン全体のデジタルツインで what-if シミュレーション(Renault、Groupe E 事例)
- 窓口・発信: https://cosmotech.com/
- 活動状況: 2024-12 Insight Partners が過半数出資(額非公開)。サイト 2026-04 更新、Gartner Hype Cycle の "AI Simulation" を掲げる。LLM エージェント機能はサイトに記載なし
- 渋谷シムへの使いどころ: (8) 「シミュレーション=意思決定支援 SaaS」として月次更新で使われる(Renault は毎月ツインを更新)。渋谷シムも「毎月の人流で較正し直すサブスク」型の参考
- 既出: 新規
- 出典: https://pulse2.com/cosmo-tech-majority-investment-secured-from-insight-partners-and-former-accenture-execs / https://cosmotech.com/

#### Simudyne
- 種別: 企業
- 中心人物: Justin Lyon(CEO)
- 代表的な成果: 金融市場のエージェントベース・シミュレーション(Pulse、Echo)。2026-09 BMLL と提携し板情報で "Large Market Models"(注文フローの生成モデル)を事前学習、反応する市場シムを提供
- 窓口・発信: https://www.simudyne.com/ / ニュース simudyne.com/news/
- 活動状況: 2017 Barclays Techstars 卒。2026-09-30 BMLL 提携発表。LLM の明示はなく、板データの基盤モデル+ABM
- 渋谷シムへの使いどころ: (3)(6) 「過去を再生する」のではなく「介入に反応する」シムを、実データで事前学習した生成モデル+ABM で作る構成。渋谷の人流でも「人流データで学習した行動生成モデル+LLM」の分担を考える材料
- 既出: 新規
- 出典: https://a-teaminsight.com/blog/bmll-and-simudyne-bring-reactive-ai-simulation-to-trading-and-market-structure/ / https://www.marketsmedia.com/ceo-chat-justin-lyon-simudyne/ / https://www.simudyne.com/

#### Replica(Sidewalk Labs 発)
- 種別: 企業
- 中心人物: 未確認(今回の資料では CEO 名なし)
- 代表的な成果: 全米の合成人口(国勢調査+消費者データ)×携帯位置データから ML で作る「ペルソナ」(活動順序・目的地選択・手段選択)→ エージェント単位の活動ベース交通シミュレーション → 実測交通量で大規模最適化較正(ground truth の一部を holdout)。方法論ドキュメント公開
- 窓口・発信: https://www.replicahq.com/ / 方法論 https://documentation.replicahq.com/docs/seasonal-mobility-model-methodology-summary-places
- 活動状況: 2019 Sidewalk Labs からスピンアウト、2019 $11M、2021-04 Series B $41M(Founders Fund リード)。公共交通機関・自治体向けに稼働中
- 渋谷シムへの使いどころ: (3)(6) 渋谷シムとほぼ同じ構成(合成人口→行動モデル→較正)を LLM なしで商用化している先行例。「季節ごとに合成人口を作り直す」「ground truth の一部を holdout」「顧客が自分の観測値を追加して較正」は、来街ピーク時刻ずれの較正手順として最優先で読むべき。(8) 行政が顧客として払う実例
- 既出: 新規
- 出典: https://documentation.replicahq.com/docs/seasonal-mobility-model-methodology-summary-places / https://govtech.com/biz/replica-dealer-in-synthetic-urban-data-raises-41m

#### PTV Group / Umovity(Visum・Vissim・Viswalk)
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: PTV Visum(マクロ交通計画)、Vissim(ミクロ交通)、Viswalk(歩行者シミュレーション)、PTV Flows(交通予測)
- 窓口・発信: https://www.ptvgroup.com/en / https://www.umovity.com/
- 活動状況: Econolite と統合した "Umovity" ブランドで約2,900都市・130か国超に展開(サイト記載)。LLM エージェント機能は未確認
- 渋谷シムへの使いどころ: (7) Viswalk は駅構内・交差点の群衆流の業界標準。渋谷スクランブル交差点の物理層をどう検証するかの比較基準
- 既出: 新規
- 出典: https://www.ptvgroup.com/en / https://www.umovity.com/

#### Aimsun
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: Aimsun Next 26(交通シミュレーション)、Aimsun Start(TomTom データで数日で較正可能な既製モデル)、Aimsun Live(リアルタイム交通デジタルツイン)
- 窓口・発信: https://www.aimsun.com/
- 活動状況: 2026-08 サイト更新、Next 26 リリース。親会社・LLM 機能は未確認
- 渋谷シムへの使いどころ: (8) 「既製モデルを数日で納品」という商品設計は、渋谷シムを他駅(天神・博多など)に横展開する時の売り方の参考
- 既出: 新規
- 出典: https://www.aimsun.com/

#### Fujitsu Social Digital Twin / Digital Rehearsal
- 重複のため「日本」タブの同名項目にまとめた

### E. 都市・人口規模シミュレーションの研究拠点(事業化の源流)

#### MIT Media Lab — Large Population Models(AgentTorch)
- 重複のため「研究室」タブの同名項目にまとめた

#### MIT City Science(CityScope)
- 重複のため「都市・人流・群衆」タブの同名項目にまとめた

### 担当範囲で見つからなかった/確認できなかったもの
- **WebSearch の上限(200回、全エージェント共有)に途中で達した**ため、以下は検索で裏取りできず未収録または未確認: Unlimited(公式サイトが robots で取得不可)、AnyLogic の LLM 機能、Helm(Simile の競合として名前のみ確認)、Listen Labs / Outset(Keplar 記事で名前と調達額のみ)、Semilattice、Altera/FRL の 2026 年の最新動向(2025-08 以降の調達・Project Sid の続報)、Aaru の 2026 年追加調達、Emergence AI の資金調達額、Inworld の 2025〜26 年の調達、Replica の 2022 年以降の調達・CEO、PTV/Aimsun の親会社と LLM 機能、MIT LPM 系のスピンオフ企業の有無。必要なら追加ターンで検索可能。
- Simile ブログ個別記事(Building the What-If Machine など)は取得エラーで本文未確認。
- 「digital twin of society」系の 2025〜26 調達の網羅検索は1回しかできず、上記以外の新興企業(中国の10億人規模シムの主体を含む)は特定できなかった。


## 3. コミュニティ・学会・ブログ・まとめ


調査日: 2026-10-13。URL は WebSearch/WebFetch で確認できたものだけ記載。
**今から間に合う締切・参加機会(2026-10-13 時点)を先にまとめる:**

| 日付 | 何 | 種別 |
|---|---|---|
| 2026-10-29 AoE | AAMAS 2027 ワークショップ企画提案の締切(本会議 2027-05-03〜07 ハノイ) | 企画提案 |
| 2026-10-29〜11-01 | CSSSA 2026 年次大会(Santa Fe)。投稿は締切済み、参加登録は 10/23 まで | 参加 |
| 2026-11-03 | ACM SIGSPATIAL 2026 ワークショップ日(GeoSim / UMFM / UrbanAI / OASIS 学生チャレンジ / HuMob) | 参加 |
| **2026-11-20 AoE** | **Social Sim'27 @ AAAI 2027(「From Proxies to Populations」)論文締切**。通知 12/2、カメラレディ 12/9、WS 当日は 2027-02-22 か 23(モントリオール) | **論文投稿(最重要)** |
| 2026-11-20 | AAAI-27 の全ワークショップ投稿の標準締切(47 WS。個別ページで要確認) | 論文投稿 |
| 2026-11-23〜25 | GAMA Days 2026(オンライン・無料。アブスト締切 9/25 は終了) | 参加 |
| 2026-12-06〜09 | Winter Simulation Conference 2026(グラスゴー) | 参加 |
| 2026-12-12〜13 | NeurIPS 2026 の SocialAgent WS(アトランタ)/ FAST WS(パリ、12/12)。投稿は締切済み | 参加・聴講 |

---

### A. 学会・ワークショップ

#### SocialAgent: Second Workshop on LLMs for Social Reasoning and Simulation(NeurIPS 2026)/ SocialLLM(ICWSM 2026)
- 種別: 学会・ワークショップ
- 中心人物: Xiangjue Dong(TAMU / Microsoft)、Jiseon Kim(Vector Institute)、Yunah Jang(Seoul National University)、Tim G. J. Rudner(University of Toronto / Vector)、Alice Oh(KAIST)
- 代表的な成果: 3本柱は「社会的推論・認知(心の理論、道徳判断など)」「社会シミュレーションの妥当性(個人や集団の代理としての LLM、因果推論の落とし穴、persona drift、ABM の検証基準)」「多元的アラインメントと評価」
- 窓口・発信: https://social-llm-workshop.github.io/ (Slack 招待リンクがあり、推奨窓口とされている)/ social.llm.workshop@gmail.com / https://neurips.cc/virtual/2026/workshop/137570
- 活動状況: 活動中。NeurIPS 2026 版は投稿締切 2026-08-29(延長後)、通知 9/29、開催 2026-12-12〜13(アトランタ)。前段として ICWSM 2026 の SocialLLM(2026-05-26、LA)と ACL 2026 の Birds of a Feather(2026-07-05)を開催
- 渋谷シムへの使いどころ: (4)(6) persona drift と「ABM の検証基準」をそのまま議題にしている。採択論文リストは検証手法の最新カタログとして使える。Slack は質問先になる
- 既出: 新規(コミュニティとして)
- 出典: https://neurips.cc/virtual/2026/workshop/137570 , https://social-llm-workshop.github.io/

#### Social Simulation with LLMs ワークショップシリーズ(COLM 2025 → COLM 2026 → AAAI 2027「Social Sim'27」)
- 種別: 学会・ワークショップ
- 中心人物: 2025 年は Zachary Yang(McGill / Mila)、Jean-François Godbout(Université de Montréal / Mila)、Kellin Pelrine(FAR.AI)、Petter Törnberg(University of Amsterdam)、Maximilian Puelma Touzel(Mila)、Reihaneh Rabbany(McGill / Mila)、Dan Zhao(NYU)、William Cunningham(University of Toronto / Google DeepMind)。2026 年は CMU の Maarten Sap、Xuhui Zhou、Yunze Xiao、Lynnette Ng が加わり、Zachary Yang は Ubisoft La Forge 所属に
- 代表的な成果: COLM 2026 版は 2026-10-09 にサンフランシスコで開催、共有タスク「Many Worlds」を併催(下の項目)
- 窓口・発信: https://sites.google.com/view/social-sims-with-llms/social-sim25 , https://sites.google.com/view/social-sims-with-llms/social-sim26 , https://sites.google.com/view/social-sims-with-llms/social-sim27
- 活動状況: 活動中・毎年開催。**Social Sim'27 は AAAI 2027(モントリオール)で開催: 投稿締切 2026-11-20 AoE、通知 12/2、カメラレディ 12/9、WS は 2027-02-22 か 23**
- 渋谷シムへの使いどころ: (6)(8) Törnberg ら既出の著者陣が運営する中心的な場で、副題「From Proxies to Populations」は 39 万体の母集団シムと合致する。holdout 不合格(0/4)という否定的な結果も含めた「検証手法」の論文として投稿先の第一候補
- 既出: 運営者は既出(Törnberg 系)。WS 自体は新規
- 出典: 上記 3 URL

#### Many Worlds 共有タスク(COLM 2026 Social Sim WS)/ silisocs / sandbox-social / ComplexDataLab
- 種別: その他(共有タスク + OSS シミュレータ)
- 中心人物: 個人名は未記載。GitHub 組織 sandbox-social、HF 組織 ComplexDataLab(Rabbany 研、McGill / Mila と推定されるが未確認)
- 代表的な成果: 5 シナリオ・計 5,213 ランのシミュレーションログ(beauty_contest / iterated_pd / polarization / observed_norms(WVS 4 か国)/ persona_expression)。「ログから仮説の支持・不支持を判定する評価法を作る」タスクでリーダーボードはない。シミュレータ silisocs(`pip install silisocs==0.2.0`)と評価キット socsim_eval(MIT)。生成モデルは Qwen3.5 27B/9B/4B と Gemma-4 31B のローカル重み
- 窓口・発信: https://github.com/sandbox-social/socsim26_sharedtask / https://huggingface.co/datasets/ComplexDataLab/socsim26-sharedtask / Slack: STAMINA の #social-sim-26-shared-task(招待 URL は未確認)
- 活動状況: 締切は 2026-08-07(終了)。主催者の観測量・予測は事前登録として伏せられており、締切後に公開予定
- 渋谷シムへの使いどころ: (6)(4) 「多ラン分布から仮説を判定する」設計は渋谷シムのアンサンブル予測と同型。persona_expression スタディは母集団の多様性の出どころを調べており、ペルソナドリフト対策の参考になる。小〜中型のオープン重みで大量ランを回す運用例でもある (5)
- 既出: 新規
- 出典: https://huggingface.co/datasets/ComplexDataLab/socsim26-sharedtask/blob/main/README.md?code=true , https://github.com/sandbox-social/socsim26_sharedtask

#### Workshop on Agent Behavior(WAB @ COLM 2026)
- 種別: 学会・ワークショップ
- 中心人物: Manuel Cherep(MIT)、Hao Zhu(Stanford)、Yanzhe Zhang(Georgia Tech / Stanford)、Benjamin Manning(MIT)、Pattie Maes(MIT)、Nikhil Singh(Dartmouth)ほか。基調講演は Natasha Jaques、Diyi Yang、Colin Camerer など
- 代表的な成果: 2026-10-09 にサンフランシスコで開催された第 1 回。ポスター約 100 件 + スポットライト 6 件。テーマは「行動の評価」「サーベイ回答から実際の行動生成へ」「Behavior foundation model(多様な母集団の行動シミュレーション)」
- 窓口・発信: https://www.aiagentbehavior.com / pc@aiagentbehavior.com
- 活動状況: 2026-10 に開催済み。次回は未告知
- 渋谷シムへの使いどころ: (1)(6) 「サーベイ回答ではなく行動を出す」方向は来街・回遊行動の生成と直結する。採択ポスター約 100 件は関連研究者リストとして使える
- 既出: 新規
- 出典: https://www.aclweb.org/portal/content/agent-behavior-workshop-colm-2026 , https://www.aiagentbehavior.com

#### FAST: Foundations of Agentic Systems Theory(NeurIPS 2026 パリ会場)
- 種別: 学会・ワークショップ
- 中心人物: Erik Miehling(IBM Research)、Madeline Reinecke(Oxford)、Irina Rish(Mila)、Djallel Bouneffouf(IBM)ほか
- 代表的な成果: テーマはエージェント集団での創発、規範・慣習の形成と集団バイアス、エージェント集団の観測可能性と制御性
- 窓口・発信: https://fast-workshop.github.io
- 活動状況: 投稿締切 2026-09-05(終了)。開催 2026-12-12(パリ)
- 渋谷シムへの使いどころ: (2)(4) 規範・慣習の創発や集団の監視可能性は、会話の発生率や関係の持続を分析する観点として使える
- 既出: 新規
- 出典: https://fast-workshop.github.io

#### NeurIPS 2026 ワークショップ一覧(YLfan99/neurips2026-workshops)
- 種別: その他(まとめリポジトリ)
- 中心人物: GitHub ユーザー YLfan99
- 代表的な成果: NeurIPS 2026 の WS をアトランタ / シドニー / パリの会場別に一覧化。エージェント系は IAB(エージェント行動の解釈)、AIWILD、IAEval、SLM-Agents(小型 LM によるエージェント)、RAAAI(資源制約下のエージェント AI)など
- 窓口・発信: https://github.com/YLfan99/neurips2026-workshops
- 活動状況: 2026 年版。締切情報は載っていない
- 渋谷シムへの使いどころ: (5) SLM-Agents(https://slmw2026.github.io/)と RAAAI(https://resource-aware-workshop.github.io/)は「小 LLM を 39 万体で安く回す」問題と直結する
- 既出: 新規
- 出典: https://github.com/YLfan99/neurips2026-workshops

#### MemAgents: Memory for LLM-Based Agentic Systems(ICLR 2026 WS)
- 種別: 学会・ワークショップ
- 中心人物: Yunpu Ma、Ercong Nie、Wenyue Hua、Karolina Stanczak、Matthew E. Taylor、Hinrich Schütze ほか
- 代表的な成果: エピソード記憶・グラフ記憶・階層記憶、記憶の統合(consolidation)、長期記憶のベンチマーク
- 窓口・発信: https://sites.google.com/view/memagent-iclr26/ / https://iclr.cc/virtual/2026/workshop/10000792
- 活動状況: 2026-04-27 に開催済み(リオ)
- 渋谷シムへの使いどころ: (4) 複数日ランで記憶を統合・圧縮する設計の文献源になる
- 既出: 新規
- 出典: https://iclr.cc/virtual/2026/workshop/10000792

#### AAMAS 2027(International Conference on Autonomous Agents and Multiagent Systems)
- 種別: 学会・ワークショップ
- 中心人物: 2027 年はウォーリック大学(英国)が運営ページを持つ
- 代表的な成果: マルチエージェント分野のトップ会議。ABM 系の MABS(Multi-Agent-Based Simulation)WS は毎年併催されている(2025 年は第 26 回)
- 窓口・発信: https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/call-for-workshops/ / https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/call-for-main-track/
- 活動状況: 本会議は 2027-05-03〜07 ハノイ(対面)。アブスト締切 2026-10-01、本文締切 2026-10-08(ともに終了)。**WS 企画提案の締切は 2026-10-29 AoE**(通知 11/28、WS は 5/3〜4)。各 WS の論文締切は例年 2 月ごろ(未確認)
- 渋谷シムへの使いどころ: (6)(7) 2027 年春の MABS などの WS 論文募集が、渋谷シムの中間成果を出す現実的な投稿先になる
- 既出: 新規
- 出典: https://ispr.info/2026/08/24/call-aamas-2027-intl-conf-on-autonomous-agents-and-multiagent-systems/ , https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/call-for-workshops/ , https://forum.comses.net/t/mabs-2025-the-26th-international-workshop-on-multi-agent-based-simulation/10852

#### AAAI-27 ワークショップ群
- 種別: 学会・ワークショップ
- 中心人物: AAAI
- 代表的な成果: 47 WS。上記の Social Sim'27 を含む
- 窓口・発信: https://aaai.org/conference/aaai/aaai-27/workshops-call/(一覧ページ https://aaai.org/conference/aaai/aaai-27/aaai-27-workshop-program-list/ は取得時にレート制限で読めなかった)
- 活動状況: AAAI-27 は 2027-02-16〜23(モントリオール)、WS は 2/22〜23。**WS 投稿の標準締切は 2026-11-20、通知は 12/2**
- 渋谷シムへの使いどころ: (6)(8) Social Sim'27 以外にも、都市・モビリティ系やマルチエージェント系の WS があれば同じ時期に投稿できる(一覧の確認が必要)
- 既出: 新規
- 出典: https://aaai.org/conference/aaai/aaai-27/workshops-call/

#### IC2S2(International Conference on Computational Social Science)
- 種別: 学会・ワークショップ
- 中心人物: International Society for Computational Social Science(ISCSS)。2026 年は Vermont Complex Systems Institute(University of Vermont)がホスト
- 代表的な成果: CSS 分野の最大の年次会議。2015 年以降ヘルシンキ → … → 2025 年ノルショーピング → 2026 年バーリントン
- 窓口・発信: https://dev.cmplxsys.w3.uvm.edu/ / IC2S2@uvm.edu
- 活動状況: 2026-07-28〜31 に開催済み(アブスト締切は 2026-03-03)。**2027 年の開催地・日程は未発表**(例年 12 月に投稿受付が始まり、3 月上旬が締切)
- 渋谷シムへの使いどころ: (6)(8) LLM 社会シミュレーションの妥当性をめぐる議論の中心地の一つ。2027 年の 3 月締切に向けて 2 ページのアブストで出せる
- 既出: 新規
- 出典: https://dev.cmplxsys.w3.uvm.edu/ , https://dev.cmplxsys.w3.uvm.edu/about/

#### Social Simulation Conference(SSC)/ ESSA(European Social Simulation Association)
- 種別: 学会・ワークショップ
- 中心人物: ESSA。SSC2026 は Durham University がホスト
- 代表的な成果: 欧州の社会シミュレーション(ABM)の本流。SSC2025 はデルフト、SSC2026 のテーマは「Embracing the social in computational social science」
- 窓口・発信: https://essa.eu.org/event/social-simulation-conference-2026-ssc2026/ / https://www.durham.ac.uk/research/institutes-and-centres/research-methods/social-simulation-conference-2026 / management@essa.eu.org / 入会: https://essa.wildapricot.org/join-us
- 活動状況: SSC2026 は 2026-08-24〜28(対面のみ、論文締切 2026-04-12、開催済み)。SSC2027 は未発表(例年 4 月締切・8〜9 月開催)
- 渋谷シムへの使いどころ: (6)(7) ODD プロトコルや検証・較正の伝統が強く、「LLM エージェントを古典 ABM の作法で検証する」視点が得られる
- 既出: 新規
- 出典: https://essa.eu.org/event/social-simulation-conference-2026-ssc2026/ , https://www.durham.ac.uk/research/institutes-and-centres/research-methods/social-simulation-conference-2026

#### ESSA SIG-LLM4ABM(Large Language Models for Agent-Based Modelling 分科会)
- 種別: OSSコミュニティ(学会内の研究グループ)
- 中心人物: Peer-Olaf Siebers(University of Nottingham)
- 代表的な成果: "Large Language Models for Agent-Based Modelling: Current and possible uses across the modelling cycle" arXiv:2507.05723(SSC2025 で発表)
- 窓口・発信: https://essa.eu.org/sig/sig-llm4abm-large-language-models-for-agent-based-modelling/ (参加は Siebers 氏に直接連絡。メーリングリストや Discord は記載なし)/ https://people.cs.nott.ac.uk/pszps/
- 活動状況: 活動中。**月 1 回のオンライン会合**で最新動向と 1 テーマを深掘りする
- 渋谷シムへの使いどころ: (6)(1) 「定性的な知識を行動ルールへ変換する」をモデリングサイクル全体で扱っており、System 1 の習慣ルールを LLM で作る工程に直結する。オンライン参加なので福岡からでも加われる可能性がある
- 既出: 新規(arXiv:2507.05723 は known_arxiv に無い)
- 出典: https://essa.eu.org/sig/sig-llm4abm-large-language-models-for-agent-based-modelling/

#### CSSSA(Computational Social Science Society of the Americas)年次大会
- 種別: 学会・ワークショップ
- 中心人物: CSSSA。2026 年の基調講演は Marco Janssen(コモンズのガバナンス)
- 代表的な成果: 募集トピックに「NLP and LLMs in CSS Research」「AI-Assisted Model Generation and Evaluation」「Hybrid ABM + ML」
- 窓口・発信: https://computationalsocialscience.org/conferences/css-2026-santa-fe/ / https://www.comses.net/events/798/
- 活動状況: 2026-10-29〜11-01、Santa Fe(対面)。投稿締切 2026-07-15(終了)、参加登録締切 10/23
- 渋谷シムへの使いどころ: (6) ABM と ML のハイブリッドや検証の議論。サンタフェの複雑系コミュニティとの接点になる
- 既出: 新規
- 出典: https://www.comses.net/events/798/ , https://forum.comses.net/t/call-for-papers-the-2026-international-conference-of-the-computational-social-science-society-of-the-americas-csssa/11061

#### Winter Simulation Conference(WSC 2026)
- 種別: 学会・ワークショップ
- 中心人物: INFORMS ほか。Agent-Based Simulation トラック(Andrew Collins、Martijn Mes、Zhou He)、Simulation and AI トラック(Mohammad Dehghani ほか)
- 代表的な成果: ABS トラックは ODD 記述と検証評価の添付を求める。AI トラックは LLM によるシミュレーションコード生成やエージェント型の自律実験を扱う
- 窓口・発信: https://meetings.informs.org/wordpress/wsc2026/tracks / https://connect.informs.org/discussion/2026-winter-simulation-conference-save-the-dates
- 活動状況: 2026-12-06〜09、グラスゴー。テーマは Simulation for Climate Resilience。論文締切 2026-04-05、ポスター・Industry Track の拡張アブスト 7/31(いずれも終了)
- 渋谷シムへの使いどころ: (7)(5)(8) 歩行者・交通・群衆シミュレーションの工学寄りの層が厚い。Industry Track は事業化事例の参考になる
- 既出: 新規
- 出典: https://meetings.informs.org/wordpress/wsc2026/tracks , https://connect.informs.org/discussion/2026-winter-simulation-conference-save-the-dates

#### ACM SIGSPATIAL 2026 ワークショップ群(GeoSim / UMFM / UrbanAI / OASIS 学生チャレンジ / HuMob)
- 重複のため「都市・人流・群衆」タブの同名項目にまとめた

#### ALIFE 2026
- 種別: 学会・ワークショップ
- 中心人物: ISAL。2026 年は University of Waterloo と Wilfrid Laurier University
- 代表的な成果: テーマは「Living and Lifelike Complex Adaptive Systems」
- 窓口・発信: https://2026.alife.org/
- 活動状況: 2026-08-17〜21、ウォータールー(ハイブリッド)。開催済み。LLM 社会専用のセッションは未確認
- 渋谷シムへの使いどころ: 北極星である「AI 住人が生きるメタバース」の思想的な系譜(人工生命、オープンエンド性)。渋谷シムの (4) 長期ランにも関係する
- 既出: 新規
- 出典: https://2026.alife.org/

### B. ジャーナル・メーリングリスト・モデル共有基盤

#### JASSS(Journal of Artificial Societies and Social Simulation)
- 種別: その他(オープンアクセス誌)
- 中心人物: University of Surrey(CRESS)系が発祥
- 代表的な成果: LLM 関連では "Synthetic Social Media Influence Experimentation Via an Agentic RL LLM Bot"(28(3)、Jin & Guo)、"From Concepts to Model: Automating Feature Extraction of ABMs Using LLMs"(28(3)、Khatami & Frantz)、"GPLab: A Generative Agent-Based Framework for Policy Simulation and Evaluation"(29(1))
- 窓口・発信: https://www.jasss.org/index_by_issue.html
- 活動状況: 最新号は 29(3)(2026-06-30)
- 渋谷シムへの使いどころ: (6)(8) 政策シミュレーション(GPLab)は行政向けの用途を説明する前例になる。査読付きの投稿先としても有力
- 既出: 新規
- 出典: https://www.jasss.org/index_by_issue.html

#### SIMSOC メーリングリスト(JISCMail)
- 種別: その他(メーリングリスト)
- 中心人物: 社会シミュレーション研究者コミュニティ(Surrey CRESS が案内)
- 代表的な成果: 社会科学シミュレーションの告知(CFP、求人、イベント)の古参 ML
- 窓口・発信: 登録ページ http://www.jiscmail.ac.uk/lists/simsoc.html (CRESS の案内ページ経由で確認)
- 活動状況: 2026 年の流量は未確認
- 渋谷シムへの使いどころ: 学会やスクールの CFP を拾う受信箱として使う
- 既出: 新規
- 出典: https://cress.soc.surrey.ac.uk/s4ss/links.html

#### CoMSES Network(旧 OpenABM)— Computational Model Library と フォーラム
- 種別: OSSコミュニティ
- 中心人物: 国際執行委員会。Allen Lee(ASU)が LLM エージェントのワークフロー基盤を開発
- 代表的な成果: ABM のコード公開リポジトリ(FAIR 準拠)、イベント・求人の掲示板。Allen Lee の講演「lessons learned from developing an agentic workflow and orchestration platform」(2026-04-01、ASU RSE セミナー、LLM を CoMSES のモデルライブラリに組み込む話)。フォーラムには 2026-10-08 に「A Benchmark Test for LLM Persona Agents in a Macroeconomic Simulation」が投稿されている
- 窓口・発信: https://comses.net/about / https://forum.comses.net / https://www.comses.net/community/
- 活動状況: 活動中(フォーラムは 2026-10 時点で投稿あり)
- 渋谷シムへの使いどころ: (6)(8) 渋谷シムの公開版を ODD 付きで登録すれば ABM 界隈に可視化できる。SSC・MABS・CSSSA などの CFP 情報もここに集まる
- 既出: 新規
- 出典: https://comses.net/about , https://forum.comses.net/ , https://rse.asu.edu/events/2025-12-19-enabling-research-llms.html

### C. OSS コミュニティ(Discord / Slack / Matrix)

#### Mesa / mesa-llm
- 種別: OSSコミュニティ
- 中心人物: Mesa Team(maintainers@projectmesa.dev)。JOSS の Mesa 3 論文著者は E. ter Hoeven、J. Kwakkel、V. Hess、T. Pike、B. Wang、rht、J. Kazil。mesa-llm の PyPI 管理者は boyuw
- 代表的な成果: https://github.com/mesa/mesa(3.9k★、Mesa 4 開発中)/ https://github.com/mesa/mesa-llm(v0.3.2、2026-04-26。OpenAI・Anthropic・Ollama などの LLM を Mesa のエージェントに組み込む)。GSoC 2025 で Mesa-LLM 統合を実施
- 窓口・発信: Discord https://discord.gg/UUGJvdtEJu / Matrix https://matrix.to/#/#mesa-llm:matrix.org / GitHub Discussions https://github.com/mesa/mesa-llm/discussions / 月例の dev セッション(https://github.com/mesa/mesa/discussions で告知)
- 活動状況: 活動中。GSoC 2026 にも参加(https://github.com/projectmesa/mesa/wiki/Google-Summer-of-Code-2026)
- 渋谷シムへの使いどころ: (1)(5) 「ルールベースのエージェントに LLM 判断を差し込む」設計は System 1 と 2 の混成と同じ構造。月例の dev セッションで設計相談ができる
- 既出: 既出(Mesa は論文として既出)。mesa-llm とコミュニティ窓口は新規
- 出典: https://pypi.org/project/mesa-llm/ , https://github.com/mesa/mesa

#### CAMEL-AI / Eigent.AI(OASIS の母体)
- 重複のため「研究室」タブの同名項目にまとめた

#### AgentScope(agentscope-ai)
- 重複のため「研究室」タブの同名項目にまとめた

#### MetaGPT / DeepWisdom(深度赋智)
- 種別: スタートアップ / OSSコミュニティ
- 中心人物: 吴承霖(Wu Chenglin、CEO)
- 代表的な成果: MetaGPT(約 6 万★)、MGX(2025-02 公開)の後継 Atoms(2026-01-13 発表)
- 窓口・発信: https://www.linkedin.com/showcase/atoms-dev(Discord は未確認)
- 活動状況: 2025 年上半期に 2 ラウンドで約 2.2 億元を調達(蚂蚁集团、凯辉基金、锦秋基金、BV 百度风投など)。事業はコーディングエージェントに軸足を移しており、社会シミュレーションからは遠ざかっている
- 渋谷シムへの使いどころ: (8) 「OSS の多エージェント基盤 → 商用プロダクト」へ転換した資金調達の事例。シム技術そのものとの関係は薄い
- 既出: 新規
- 出典: https://www.36kr.com/p/3640426144812417

#### AI Town / AI Stack Devs Discord(a16z-infra)
- 種別: OSSコミュニティ
- 中心人物: a16z-infra。Convex が共同開発
- 代表的な成果: https://github.com/a16z-infra/ai-town(10.5k★)
- 窓口・発信: Discord「AI Stack Devs」https://discord.gg/PQUmTBTGmT / Convex の Discord 質問アーカイブ https://discord-questions.convex.dev/
- 活動状況: リポジトリの最終更新日は確認できず。Convex 側の Q&A アーカイブには 2026 年の投稿 ID がある
- 渋谷シムへの使いどころ: 北極星(メタバースの AI 住人)寄り。(2) 会話トリガーの実装を持ち寄る場として使える
- 既出: 既出(コード読了済み)。Discord は新規
- 出典: https://github.com/a16z-infra/ai-town/

#### AgentTorch / Large Population Models(MIT Media Lab)
- 重複のため「研究室」タブの同名項目にまとめた

#### Concordia(Google DeepMind)と Cooperative AI Foundation の Concordia Contest
- 重複のため「研究室」タブの同名項目にまとめた

#### GAMA Platform と GAMA Days
- 種別: OSSコミュニティ
- 中心人物: IRD(フランス)系の GAMA 開発チーム
- 代表的な成果: 空間明示型 ABM の基盤(GIS 連携が強い)。最新版は 2025-06
- 窓口・発信: https://gama-platform.org/ / ML gama-platform@googlegroups.com(ユーザー)と gama-dev@googlegroups.com(開発者)/ https://github.com/gama-platform / YouTube と LinkedIn
- 活動状況: **GAMA Days 2026 は 2026-11-23〜25 にオンライン・無料で開催**(アブスト締切 9/25 は終了)。LLM プラグインは公式サイトでは確認できず
- 渋谷シムへの使いどころ: (7) GIS と建物データ上で群衆・交通を扱う空間層の設計の参考になる。PLATEAU のような 3D 都市データとの接続例を探す場
- 既出: 新規
- 出典: https://gama-platform.org/

#### NetLogo コミュニティ
- 種別: OSSコミュニティ
- 中心人物: Northwestern University CCL(サイトは netlogo.org に移転)
- 代表的な成果: 古典 ABM 言語。LLM 連携の研究として "Multi-Agent Systems Powered by LLMs: Applications in Swarm Intelligence" arXiv:2503.03800(NetLogo と GPT の結合)、Frontiers in AI 2025(10.3389/frai.2025.1593017)
- 窓口・発信: https://forum.netlogo.org/ / https://groups.google.com/g/netlogo-users / https://github.com/NetLogo/ / https://www.modelingcommons.org/
- 活動状況: サイト移転を確認。LLM 拡張の公式情報は未確認
- 渋谷シムへの使いどころ: (1) ルール型の行動と LLM 判断の切り替え例
- 既出: 新規
- 出典: https://www.netlogo.org/index , https://www.arxiv.org/abs/2503.03800

#### Sotopia Lab(CMU 系)と awesome-social-agents
- 種別: 研究室 / OSSコミュニティ
- 中心人物: Xuhui Zhou、Hao Zhu(ProKil)ら(CMU の Maarten Sap 周辺。GitHub ページ上で所属は明記されていない)
- 代表的な成果: https://github.com/sotopia-lab/sotopia(337★、2026-06 更新)/ sotopia-rl(2026-04)/ https://github.com/sotopia-lab/awesome-social-agents(116★、2026-06-14 更新、サーベイ論文を準備中)
- 窓口・発信: https://sotopia.world/ / https://sotopia-lab.github.io/awesome-social-agents/
- 活動状況: 活動中(2026 年に更新あり)
- 渋谷シムへの使いどころ: (2) 会話の「中身」を目標達成度や関係性などで採点する評価軸(Sotopia-Eval)は、会話の質を測る指標にそのまま使える
- 既出: 新規
- 出典: https://www.github.com/sotopia-lab , https://github.com/sotopia-lab/awesome-social-agents

### D. awesome リスト・まとめリポジトリ

#### awesome-llm-human-simulation
- 種別: その他(まとめリポジトリ)
- 中心人物: Qian Wang
- 代表的な成果: サーベイ "LLM-based Human Simulations Have Not Yet Been Reliable" arXiv:2501.08579。章立ては人間行動シミュレーション、バイアス・価値、応用(経済、政治、消費者など)、評価、認知・心理、社会シミュレーション、学会
- 窓口・発信: https://github.com/Persdre/awesome-llm-human-simulation
- 活動状況: 「Last updated: 2026.08」、169★
- 渋谷シムへの使いどころ: (6) 「LLM による人間再現はまだ信頼できない」という立場のまとめで、検証設計の反証チェックリストとして使える
- 既出: 新規(2501.08579 は known_arxiv に無い)
- 出典: https://github.com/Persdre/awesome-llm-human-simulation

#### LLM-Agent-Based-Modeling-and-Simulation(清華大 FIB Lab)
- 種別: その他(まとめリポジトリ)
- 中心人物: Chen Gao、Yong Li ら(清華大 FIB Lab。AgentSociety と同じ研究室)
- 代表的な成果: サーベイ "LLM empowered agent-based modeling and simulation: a survey and perspectives" arXiv:2312.11970(Humanities and Social Sciences Communications 2024)
- 窓口・発信: https://github.com/tsinghua-fib-lab/LLM-Agent-Based-Modeling-and-Simulation
- 活動状況: 303★。最終更新日は未確認
- 渋谷シムへの使いどころ: (7)(1) 物理・社会・サイバー・ハイブリッドの 4 領域分類で、都市移動系の先行研究を探す索引になる
- 既出: 論文は既出(2312.11970)。リポジトリは新規
- 出典: https://github.com/tsinghua-fib-lab/LLM-Agent-Based-Modeling-and-Simulation

#### LLM-Agents-for-Simulation
- 種別: その他(まとめリポジトリ)
- 中心人物: Gian Marco Orlando(giammy677dev)
- 代表的な成果: 医療、推薦、社会ダイナミクス、SNS、経済の各領域の論文とフレームワークの一覧
- 窓口・発信: https://github.com/giammy677dev/LLM-Agents-for-Simulation
- 活動状況: 53★、28 commits。最終更新日は未確認
- 渋谷シムへの使いどころ: 先行研究の網羅チェック (6)
- 既出: 新規
- 出典: https://github.com/giammy677dev/LLM-Agents-for-Simulation

#### Awesome-LLM-in-Social-Science(ValueByte-AI)
- 種別: その他(まとめリポジトリ)
- 中心人物: Haoran Ye、Guojie Song ら
- 代表的な成果: サーベイ "LLM Psychometrics" arXiv:2505.08245。評価(価値、性格、道徳、意見)、アラインメント、シミュレーションの章
- 窓口・発信: https://github.com/ValueByte-AI/Awesome-LLM-in-Social-Science
- 活動状況: 648★、195 commits
- 渋谷シムへの使いどころ: (4)(6) ペルソナの性格・価値観の一貫性を心理測定で検証する方法がまとまっている
- 既出: 新規
- 出典: https://github.com/ValueByte-AI/Awesome-LLM-in-Social-Science

#### サーベイ「From Individual to Society」(社会シミュレーションの総説)
- 種別: その他(サーベイ論文)
- 中心人物: Fudan 系の著者陣(詳細は未確認)
- 代表的な成果: "From Individual to Society: A Survey on Social Simulation Driven by LLM-based Agents" arXiv:2412.03563(ACM Computing Surveys 掲載とする記事あり)
- 窓口・発信: https://arxiv.org/abs/2412.03563v1 / https://huggingface.co/papers/2412.03563.md
- 活動状況: 2024-12 初出
- 渋谷シムへの使いどころ: (6) 個人・シナリオ・社会の 3 階層の分類で、渋谷シムの位置付けを説明するのに使える
- 既出: 新規(2412.03563 は known_arxiv に無い)
- 出典: https://arxiv.org/html/2412.03563v1

### E. 企業・ブログ・ニュースレター・ポッドキャスト・講座

#### Simile(Simile AI, Inc.)— Generative Agents の商用化
- 重複のため「企業」タブの同名項目にまとめた

#### Latent Space Podcast:「Simulation: the new Scaling Law — Joon Sung Park, Simile AI」
- 種別: ニュースレター(ポッドキャスト)
- 中心人物: Latent Space(swyx、Alessio)。ゲストは Joon Sung Park
- 代表的な成果: Simile の手法(長時間インタビュー + 取引・観察データ + RCT で事後学習)の解説。2026-08-21 配信とする記事あり
- 窓口・発信: https://latent.space/p/simile
- 活動状況: 2026 年の回
- 渋谷シムへの使いどころ: (6)(8) 行動データで小型モデルを事後学習する方針は、System 1.5 の軽量判断モデルの作り方の参考になる
- 既出: 新規
- 出典: https://latent.space/p/simile , https://singularitymoments.com/content/beyond-web-text-inside-simile-ais-bet-on-behavioral-scaling-and-social-simulat/

#### Sequoia「Training Data」Ep.89:Simulating Humans at Scale(Joon Sung Park)
- 種別: ニュースレター(ポッドキャスト)
- 中心人物: Sequoia Capital。ゲストは Joon Sung Park
- 代表的な成果: 「人間社会の CERN」構想。取り付け騒ぎ、気候協力、民主主義の崩壊などへの応用を語る
- 窓口・発信: https://sequoiacap.com/podcast/simulating-humans-at-scale-similes-joon-sung-park
- 活動状況: 2026 年
- 渋谷シムへの使いどころ: (8) 投資家に「社会シミュレーション」の事業を説明するときの語彙の参考になる
- 既出: 新規
- 出典: https://sequoiacap.com/podcast/simulating-humans-at-scale-similes-joon-sung-park

#### TWIML AI Podcast #632「Modeling Human Behavior with Generative Agents」/ TED「A simulation of human reality, powered by AI」
- 種別: ニュースレター(ポッドキャスト)/ その他(講演)
- 中心人物: Joon Sung Park
- 代表的な成果: 長期記憶モジュール、知識グラフによる想起、多数のエージェントで生じるコミュニティ行動のスケーリング(2023-06-05)
- 窓口・発信: https://twimlai.com/podcast/twimlai/modeling-human-behavior-with-generative-agents / https://www.ted.com/talks/joon_sung_park_a_simulation_of_human_reality_powered_by_ai
- 活動状況: アーカイブ
- 渋谷シムへの使いどころ: (4) 記憶設計の原点を確認する用途
- 既出: 新規
- 出典: 上記 URL

#### Stanford CS222「AI Agents and Simulations」
- 重複のため「研究室」タブの同名項目にまとめた

#### AI Village(Sage Future Inc. / AI Digest)
- 種別: ブログ / ニュースレター / その他(長期稼働のエージェント実験)
- 中心人物: Adam Binksmith、Shoshannah Tekofsky(Sage Future Inc.、慈善団体)
- 代表的な成果: 15 体超のフロンティアモデル・エージェントが各自 Linux PC を持ち、共有チャットで長期目標に取り組む。2025-04-01 から平日に毎日 4 時間稼働、月約 1 万ドル。1 年超の全トランスクリプトを HuggingFace で研究者向けに公開。2025 年の教訓は「幻覚は社会的に伝播する」「1 体の弱いエージェントがチーム全体を劣化させる」「強いモデルは単独の方が強い場合がある」
- 窓口・発信: https://theaidigest.org/village/blog/how-the-ai-village-works / Substack https://aivillageblog.substack.com/(購読者 1.9 万超)/ タイムライン https://theaidigest.org/village/timeline / X @aidigest_
- 活動状況: 2026 年も稼働中
- 渋谷シムへの使いどころ: (2)(4) 偽情報の社会的伝播や、長期稼働でのドリフトの実例集。北極星(AI 住人が暮らす世界)の運営実例として最も近い
- 既出: 新規
- 出典: https://theaidigest.org/village/blog/how-the-ai-village-works , https://aivillageblog.substack.com/p/what-we-learned-2025

#### Lil'Log(Lilian Weng)「LLM Powered Autonomous Agents」
- 種別: ブログ
- 中心人物: Lilian Weng
- 代表的な成果: 2023-06-23 の記事。記憶の分類(感覚・短期・長期)、MIPS(最大内積探索)による検索、Generative Agents のケーススタディ(記憶ストリーム、想起スコアリング、リフレクション)
- 窓口・発信: https://lilianweng.github.io/posts/2023-06-23-agent/
- 活動状況: 定番記事(アーカイブ)
- 渋谷シムへの使いどころ: (4) 記憶と想起の設計の基礎文献
- 既出: 新規
- 出典: https://lilianweng.github.io/posts/2023-06-23-agent/

#### Interconnects(Nathan Lambert)
- 種別: ニュースレター
- 中心人物: Nathan Lambert(Ai2 の post-training リード)
- 代表的な成果: オープンモデル(OLMo など)、RLHF、推論モデルの動向。週 1〜3 本
- 窓口・発信: https://www.interconnects.ai/about
- 活動状況: 活動中
- 渋谷シムへの使いどころ: (5) System 2α 用の小さなオープン重みモデルの選定、量子化や事後学習の動向を追うのに使う。社会シミュレーション専門ではない
- 既出: 新規
- 出典: https://www.interconnects.ai/about

#### Complexity Explorer(Santa Fe Institute)「Introduction to Agent-Based Modeling」
- 種別: その他(オンライン講座)
- 中心人物: Bill Rand(講座作成・動画)、Anamaria Berea(リード講師)
- 代表的な成果: NetLogo による ABM 入門(前提知識不要、2,051 人が受講)
- 窓口・発信: https://www.complexityexplorer.org/courses/217-introduction-to-agent-based-modeling
- 活動状況: 直近の開講は 2026-05-18〜08-08(終了)。定期的に再開講されている
- 渋谷シムへの使いどころ: (6)(7) ABM の古典的な検証・感度分析の作法を体系的に学べる
- 既出: 新規
- 出典: https://www.complexityexplorer.org/courses/217-introduction-to-agent-based-modeling

#### AWS HPC Blog「LLMs: the new frontier in generative agent-based simulation」
- 種別: ブログ
- 中心人物: Ilan Gleiser、Charunethran Panchalam Govindarajan(AWS)
- 代表的な成果: AWS Batch で数千本のレプリケートを並列実行し、Spot インスタンスでコストを下げる構成例(2024-10-02)
- 窓口・発信: https://aws.amazon.com/blogs/hpc/llms-the-new-frontier-in-generative-agent-based-simulation/
- 活動状況: 単発記事
- 渋谷シムへの使いどころ: (5) GPU が無い期間のクラウドでのアンサンブル実行の設計例。Spot と Batch の組み合わせ
- 既出: 新規
- 出典: 上記 URL

#### TUM Data Innovation Lab「Social Simulation with Large Language Models」(SS26)
- 種別: 研究室(学生プロジェクト)
- 中心人物: Ricardo Acevedo Cabra、Shanshan Bai、Matthias Kahl(TUM Chair of Data Science in Earth Observation)
- 代表的な成果: 住環境に対する人々の知覚を LLM でシミュレートし、実データと比べてバイアスを分析する
- 窓口・発信: https://www.mdsi.tum.de/di-lab/projekte/ss26-tum-data-science-in-earth-observation-social-simulation-with-large-language-models
- 活動状況: 2026 年夏学期
- 渋谷シムへの使いどころ: (6) 都市環境の知覚を実データと照合する小さな検証設計の例
- 既出: 新規
- 出典: 上記 URL

---

### 担当範囲で見つからなかった / 確認できなかったもの
- **検索の上限**: WebSearch の上限(1 ターン 200 回、全エージェント共有)に途中で達したため、以下は追加検索できなかった。続きの調査が必要なら、次のメッセージで再開できる。
  - AAAI-27 の全 47 WS 一覧(該当ページがレート制限 429 で読めず)。
  - SIGSPATIAL の UMFM と OASIS 2026 の運営者・締切。
  - IC2S2 2027 と SSC2027 の開催地・日程(いずれも未発表と思われる)。
  - CSCW、WWW、ICWSM 2027 の関連 WS。
  - Latent Space の他の関連回、Generative Agents 系の Substack。
- **未確認の個別項目**: Stanford CS222 の公式 YouTube 講義動画は確認できなかった(Bulletin に講義の登録のみ)。Concordia の公式 Discord やフォーラムは見つからず(GitHub の Issues / PR のみ)。Concordia Contest の 2025〜2026 年の再開催は確認できなかった。AgentTorch の LPM Slack の招待 URL は取得できなかった。NetLogo の LLM 公式拡張は確認できなかった。CAMEL-AI / Eigent の資金調達額も未確認。
- **既出範囲との重複**: HuMob は別担当なので軽く触れるにとどめた。


## 4. 都市・人流・交通・群衆


調査日: 2026-10-13。WebSearch の上限(1ターン200回、全エージェント共有)に途中で達したため、後半は公式サイトの WebFetch で裏取りした。確認できない項目は「未確認」と書いた。
既出判定には known_arxiv.txt と known_github.txt を使った。

---

### A. LLM × 人流生成・予測(研究室・個人)

#### HuMob Challenge / ACM SIGSPATIAL GIS Cup(人流予測データチャレンジ)
- 種別: 学会・ワークショップ(データコンペ)
- 中心人物: Takahiro Yabe(NYU)、Kota Tsubouchi・Toru Shimizu(LY Corporation)、Yoshihide Sekimoto・Kaoru Sezaki(東大)、Esteban Moro(Northeastern)、Bruno Lepri・Massimiliano Luca(FBK、2024)、Alex Pentland(MIT、2023)
- 代表的な成果: YJMob100K データ記述論文 arXiv:2307.03401(Scientific Data 2024)。GIS Cup 2025 のデータは Zenodo で全公開(CC BY 4.0、4都市 A〜D、約542MB、POI CSV 付き): https://zenodo.org/records/18050604
- 窓口・発信: 2023 https://connection.mit.edu/humob-challenge-2023 / 2024 https://wp.nyu.edu/humobchallenge2024 / 2025 https://sigspatial2025.sigspatial.org/giscup/index.html / 連絡先 takahiroyabe@nyu.edu
- 活動状況:
  - 2023: 10万人×90日。SIGSPATIAL 2023(ハンブルク、2023-11-13)のワークショップで発表。
  - 2024: 4都市・75日分。データ公開 2024-07-20、最終提出 9/20、ワークショップ 2024-10-29(アトランタ)。
  - 2025: SIGSPATIAL Cup として開催。LY と NYU の共催で120チーム超が参加。データ公開 4/30、最終提出 9/10、発表 2025-11-05。優勝は PolyU の Mobility Science Lab(Xu Yang 准教授の指導、「HuMob Predictor」)。
  - 2026: SIGSPATIAL 2026(Riverside, CA、11/3〜6)のワークショップ一覧に「HuMob 2026(第4回)」が 11/3 開催で載っている。GIS Cup 2026 のページは取得できず、テーマと締切は未確認。
- 渋谷シムへの使いどころ: (3)(6) 日本の都市の擬似人流(500mグリッド×30分)を使って、来街ピーク時刻を較正したりホールドアウト検証したりできる。GEO-BLEU / DTW という評価指標はそのまま流用できる。(4) 75日分の長期データがあるので、複数日ランの検証にも使える。
- 既出: 新規(arXiv:2307.03401 は未掲載)
- 出典: https://sigspatial2025.sigspatial.org/giscup/index.html , https://research.lycorp.co.jp/en/news/338 , https://www.polyu.edu.hk/publications/innovationdigest/issue/202604/student-corner/team-of-four-polyu-phd-students-wins-championship-at-acm-sigspatial-cup-2025 , https://sigspatial2026.sigspatial.org/workshops.html , https://zenodo.org/records/18050604

#### Resilient Urban Networks (RUN) Lab(Takahiro Yabe 研、NYU Tandon)
- 種別: 研究室
- 中心人物: 矢部貴大 Takahiro Yabe(NYU Tandon TMI / CUSP 助教)
- 代表的な成果: YJMob100K(arXiv:2307.03401)、Pseudo-PFLOW の共著(arXiv:2205.00657)、HuMob/GIS Cup の主催
- 窓口・発信: https://www.takayabe.net/ / https://engineering.nyu.edu/faculty/takahiro-yabe / メール takahiroyabe@nyu.edu(X・GitHub はサイトに記載なし)
- 活動状況: 2026年も活動中で、メンバーページ members-2026 がある。2025-10-28 には東大 CSIS と共催で「Urban AI Symposium」を開いた。Yabe 自身はそこで「AI で人の行動をシミュレートして都市レジリエンスを予測する」と講演している。
- 渋谷シムへの使いどころ: (6)(3) 日本人の研究者で、LY の人流データと LLM による行動シミュレーションの両方を扱う。相談相手としていちばん近い。東大 CSIS(関本研)ともつながっている。
- 既出: 新規
- 出典: https://engineering.nyu.edu/faculty/takahiro-yabe , https://www.takayabe.net/ , https://engineering.nyu.edu/news/urban-ai-symposium-nyu-tandon-brings-together-global-experts

#### LY Corporation Research(旧 Yahoo! JAPAN 研究所)
- 種別: 企業
- 中心人物: 坪内孝太 Kota Tsubouchi、清水徹 Toru Shimizu
- 代表的な成果: HuMob / GIS Cup 向けの擬似人流データ(LY のアプリの位置情報から合成したもの)
- 窓口・発信: https://research.lycorp.co.jp/en/news/338
- 活動状況: 2025-11-05 に GIS Cup 2025 の開催報告を出している。研究公開ページは 2026年も更新されている(publications/1915 を確認)。
- 渋谷シムへの使いどころ: (3)(6) 日本の位置情報データをオープンにしている数少ない企業。KDDI 人流とは別系統のデータとしてクロスチェックに使える。
- 既出: 新規
- 出典: https://research.lycorp.co.jp/en/news/338

#### Renhe Jiang(東京大学 空間情報科学研究センター 講師)と LLMob/ELLMob/CausalMob/Llama-Mob 系
- 種別: 個人(研究室)
- 中心人物: Renhe Jiang(東大 CSIS 講師、2023/4〜)。共著者に Jiawei Wang、Chuang Yang、Chuan Xiao、Ryosuke Shibasaki(柴崎亮介)、Noboru Koshizuka(越塚登)、Kaoru Sezaki(瀬崎薫)
- 代表的な成果:
  - LLMob(NeurIPS 2024)arXiv:2402.14744 https://github.com/Wangjw6/LLMob
  - ELLMob(ICLR 2026)arXiv:2603.07946 https://github.com/deepkashiwa20/ELLMob。台風 Hagibis、COVID-19、東京2021五輪のイベント注釈付き人流データを使い、「習慣」と「イベントによる制約」の葛藤を Fuzzy-Trace Theory で整合させて軌跡を生成する。
  - CausalMob(KDD 2025)arXiv:2412.02155。ニュースから LLM で抽出した「人の意図」を因果処置として扱い、イベント時の人流を予測する。
  - Llama-Mob(HuMob 2024 優勝)arXiv:2410.23692 https://github.com/TANGHULU6/Llama3-8B-Mob。Llama-3-8B を指示チューニングし、15日先までの軌跡を予測する。
  - TrajGPT-R(TR Part C 2026)arXiv:2602.20643
- 窓口・発信: https://www.renhejiang.com/ / https://researchmap.jp/renhejiang / GitHub https://github.com/deepkashiwa20 / Google Scholar http://scholar.google.com/citations?user=Yo2lwasAAAAJ
- 活動状況: 非常に活発。2026年は ICLR に3本、WWW に1本、ACL に3本、ICML に1本、KDD 2026 に2本、TR-C に1本採録されている。KDD 2025 で Best Student Paper も受賞。
- 渋谷シムへの使いどころ: (1)(3)(4) ELLMob の「習慣とイベントの葛藤」の扱いは、空腹が行動を支配しすぎる問題に効く。系列全体が東京のデータで評価されている。Llama-Mob は 8B モデルで都市規模の予測ができることを示しており、(5) GPU コストの判断材料になる。東大なので日本語でコンタクトしやすい。
- 既出: LLMob は既出(論文)。ELLMob・CausalMob・Llama-Mob・TrajGPT-R は新規。人物情報は新規。
- 出典: https://researchmap.jp/renhejiang , https://www.renhejiang.com/ , https://github.com/Wangjw6/LLMob , https://arxiv.org/abs/2603.07946 , https://arxiv.org/abs/2410.23692 , https://arxiv.org/abs/2412.02155

#### 清華大学 Future Intelligence laB(FIB, tsinghua-fib-lab / Yong Li 李勇)
- 重複のため「研究室」タブの同名項目にまとめた

#### CoPB(Chain-of-Planned-Behavior、KDD 2026 版)
- 種別: その他(論文/リポジトリ)
- 中心人物: Chenyang Shao、Bingbing Fan、Jingtao Ding、Yuan Yuan、Meng Wang、Fengli Xu(清華大学 / 合肥工業大学)
- 代表的な成果: arXiv:2402.09836 → KDD 2026「Generating Realistic Human Mobility Data with Hybrid Large Language Model Agent」(DOI 10.1145/3770854.3785685)。コードは https://github.com/tsinghua-fib-lab/CoPB
- 窓口・発信: 未確認
- 活動状況: 2026-04 に KDD 2026 版が出ている。計画行動理論で次の「意図」を LLM に推論させ、条件付き拡散モデルで軌跡に変換する構成。安価に回すための蒸留小型 LM や物理ベースモデルへの差し替えも用意されている。
- 渋谷シムへの使いどころ: (1)(5) 「意図は LLM、軌跡は軽量モデル」という分業と蒸留モデルの扱いは、System 1.5 の設計にそのまま参考になる。
- 既出: 既出(論文 2402.09836)。KDD 2026 版とコードは新規。
- 出典: https://chatpaper.com/paper/280885 , https://arxiv.org/abs/2402.09836

#### AgentMove(NAACL 2025)
- 種別: その他(論文/リポジトリ)
- 中心人物: Jie Feng、Yuwei Du、Jie Zhao、Yong Li(清華 FIB)
- 代表的な成果: arXiv:2408.13986 / https://github.com/tsinghua-fib-lab/AgentMove(52 stars)
- 窓口・発信: 未確認
- 活動状況: 最後に日付が確認できる更新は 2025-02(論文の新版)。
- 渋谷シムへの使いどころ: (6) ゼロショットで次の訪問地を予測するエージェント。12都市のベンチマークで比較でき、「LLM が人の移動を再現しているか」を測る土台になる。
- 既出: 新規
- 出典: https://github.com/tsinghua-fib-lab/AgentMove , https://arxiv.org/html/2408.13986v2

#### CityGPT / CityBench / UrbanLLaVA(都市空間認知 LLM)
- 種別: その他(論文/リポジトリ)
- 中心人物: Jie Feng、Yong Li ほか(清華 FIB)
- 代表的な成果: CityGPT(KDD 2025)arXiv:2406.13948 https://github.com/tsinghua-fib-lab/CityGPT 、CityBench arXiv:2406.13945、UrbanLLaVA(ICCV 2025)
- 窓口・発信: 未確認
- 活動状況: KDD 2025 に採録されている。
- 渋谷シムへの使いどころ: (6)(7) LLM の都市空間認知(道順・距離・POI)の弱さを評価して補う方法がわかる。System 2 に地理推論をさせる場合の注意点になる。
- 既出: 新規
- 出典: https://github.com/tsinghua-fib-lab/CityGPT , https://arxiv.org/abs/2406.13945

#### 関本研究室(東京大学 CSIS / 生産技術研究所)と Pseudo-PFLOW
- 種別: 研究室
- 中心人物: 関本義秀 Yoshihide Sekimoto、龐岩博 Yanbo Pang、樫山武浩 Takehiro Kashiyama(大阪経済大)、澁谷遊野 Yuya Shibuya
- 代表的な成果: Pseudo-PFLOW arXiv:2205.00657(全国の擬似人流)。Pseudo-PFLOW 2.0 では住民 DB を ZmapTown II に、POI を約1279万件に増やし、交通手段の選択に時刻表と運賃を入れた。過去の系譜として PFLOW、Open PFLOW(TR-C 2017)がある。
- 窓口・発信: https://sekilab.iis.u-tokyo.ac.jp/ (Facebook / LinkedIn「UT-SekimotoLab」)。データは JoRAS https://joras.csis.u-tokyo.ac.jp/ から、共同研究申請を経て研究用途に限り市区町村別 CSV で提供される。
- 活動状況: 2026-10 時点で活動中。新メンバーが加入し、TBS で熊本地震の人流分析が放映された。JoRAS には 2026-09 に「実人流データ(東京都、2026年5月)」が追加されている。
- 渋谷シムへの使いどころ: (3)(6) 渋谷の来街者の OD と時刻分布を初期化・較正するときの外部基準になる。PT 調査から合成人口を作る方法論が自分の C 工程とほぼ同じなので、比較対象としてちょうどいい。
- 既出: 既出(論文 2205.00657)。研究室・JoRAS・2.0 は新規。
- 出典: https://sekilab.iis.u-tokyo.ac.jp/ , https://sekilab.iis.u-tokyo.ac.jp/wp-content/uploads/poster_pseudo_pflow2.0_sekilab-1.pdf , https://joras.csis.u-tokyo.ac.jp/ , https://arxiv.org/abs/2205.00657

#### TrajLLM(Flora Salim ら、UNSW)
- 種別: その他(論文/リポジトリ)
- 中心人物: Chenlu Ju、Jiaxin Liu、Shobhit Sinha、Hao Xue、Flora Salim
- 代表的な成果: arXiv:2502.18712 / https://github.com/cju0/TrajLLM(14 stars)。ペルソナ・活動・目的地・記憶の4モジュール構成で、デモには東京の Foursquare データを使っている。
- 窓口・発信: 未確認(個人サイトは robots で取得不可)
- 活動状況: 未確認
- 渋谷シムへの使いどころ: (4) 重み付き密度で記憶を要約してメモリを抑える工夫は、複数日ランでの記憶肥大の対策になる。
- 既出: 既出(論文)。リポジトリは新規。
- 出典: https://arxiv.org/abs/2502.18712 , https://github.com/cju0/TrajLLM

#### ActivityEditor(物理的に妥当な人流合成)
- 種別: その他(論文)
- 中心人物: Chenjie Yang、Yutian Jiang、Anqi Liang、Wei Qi、Chenyu Wu、Junbo Zhang
- 代表的な成果: arXiv:2604.05529。意図を出すエージェントと、それを編集するエージェントの二段構成。編集側は物理制約の報酬で強化学習している。コード https://anonymous.4open.science/r/ActivityEditor-066B
- 窓口・発信: 未確認
- 活動状況: 2026-04 の arXiv 投稿
- 渋谷シムへの使いどころ: (3)(7) LLM が出す活動連鎖を物理制約で修正するという発想は、ピーク時刻のずれの是正に使える。
- 既出: 新規
- 出典: https://arxiv.org/abs/2604.05529

#### LLM-Mob(Xinglei Wang / Tao Cheng、UCL SpaceTimeLab)
- 種別: その他(論文/リポジトリ)
- 中心人物: Xinglei Wang、Meng Fang、Zichao Zeng、Tao Cheng
- 代表的な成果: arXiv:2308.15197「Where Would I Go Next? LLMs as Human Mobility Predictors」 https://github.com/xlwang233/LLM-Mob(65 stars)
- 窓口・発信: 未確認
- 活動状況: 未確認。CityGPT の謝辞で引用されている。
- 渋谷シムへの使いどころ: (6) 「LLM を移動予測器として使う」初期のベースライン。
- 既出: 新規
- 出典: https://github.com/xlwang233/LLM-Mob

#### TrajGenAgent(Emory AIMS, Li Xiong)
- 種別: その他(論文/リポジトリ)
- 中心人物: Siyu Li、Toan Tran、Lingyi Zhao、Khurram Shafique、Li Xiong
- 代表的な成果: arXiv:2606.12657。ファインチューニングなしの階層的 LLM エージェントで、活動連鎖を作ったあと決定論的なワークフローで POI・時間を決める。異常検知による妥当性評価も提案している。
- 窓口・発信: 未確認
- 活動状況: 2026-06 の arXiv
- 渋谷シムへの使いどころ: (6) 異常検知を使って「人らしくない軌跡」を検出する評価は、総量統計だけでは見えない破綻を拾える。
- 既出: 既出(論文・github)
- 出典: https://papers.cool/arxiv/2606.12657

#### UrbanLLM(NTU, Gao Cong)
- 種別: その他(論文)
- 中心人物: Yue Jiang、Qin Chao、Yile Chen、Xiucheng Li、Shuai Liu、Gao Cong
- 代表的な成果: arXiv:2406.12360。ファインチューニングした LLM が都市クエリをサブタスクに分け、時空間 AI モデルを選んで呼び出す。
- 窓口・発信: 未確認(コードへのリンクなし)
- 活動状況: 未確認
- 渋谷シムへの使いどころ: (8) 「自然言語で都市シナリオを聞くと内部モデルを呼ぶ」という形は、顧客向けインターフェースの参考になる。
- 既出: 新規
- 出典: https://arxiv.org/abs/2406.12360

#### Esteban Moro(Northeastern University)
- 種別: 個人
- 中心人物: Esteban Moro
- 代表的な成果: HuMob 共催。人流の普遍則からの逸脱を扱った PNAS Nexus 2026-09。生成 AI と都市科学のレビュー(Nature Cities 2026-08、共著)。人流データで経験的な都市格差を測った研究(Nature Human Behaviour 2025)。
- 窓口・発信: https://estebanmoro.org/ / X https://twitter.com/estebanmoro / GitHub https://github.com/emoro / Mastodon https://datasci.social/@estebanmoro
- 活動状況: 2026年も活発
- 渋谷シムへの使いどころ: (3)(6) 「重力モデルのような単純な規則では外れる部分」を扱っているので、較正ターゲットの選び方に効く。ブログが読みやすい。
- 既出: 新規
- 出典: https://www.estebanmoro.org/

---

### B. 交通・活動ベース・土地利用シミュレーションのコミュニティ

#### MATSim Association / MATSim User Meeting(MUM)
- 種別: OSSコミュニティ / 学会
- 中心人物: Kai Nagel(TU Berlin VSP)ほか。MUM2026 のホストは Latifa Oukhellou と Mostafa Ameli。
- 代表的な成果: https://github.com/matsim-org/matsim-libs
- 窓口・発信: https://matsim.org/news/ / LinkedIn / RSS / association@matsim.org
- 活動状況:
  - MUM2026 は 2026-09-28 にパリのソルボンヌ大学で開催された(hEART 2026 の前日)。発表43件。Best Paper は Nico Kuehnel(MOIA)。
  - LLM 関連の発表として、Jingjun Li らの「LLM-based Persona Labelling for MATSim Synthetic Populations」、Kaddoura・Kohl・Balmer の「MobilityStudio: Conversational, AI-Assisted Transport Planning」があった。
  - 較正セッションの発表: Sallard & Balac(PT の運賃・経路パラメータ最適化)、Samaei ら(マルチソース較正)、Ashutosh ら(クラウドソース優先の較正)、Dib & Balac(確率的バッチ最適化によるオンライン較正)。
  - 日本関連: Nazamuddin・Alolabi・Chikaraishi(東広島の活動ベース需要モデル)。
  - 2026-08-13 に会員向けセミナー「From Prompt to Pull Request」、2026-07 に FreighTSim 2026 の募集があった。年次総会(AGM)はリモート開催に延期。
- 渋谷シムへの使いどころ: (3) 較正セッションの4本(特に Dib & Balac のオンライン較正)は、ピーク時刻較正の手法としてそのまま参考になる。(4)(5) LLM ペルソナを合成人口に付ける流れは、自分のシムと同じ問題を解いている。
- 既出: 既出(MATSim 論文・コード)。MUM・Association は新規。
- 出典: https://www.matsim.org/conferences/mum2026/ , https://matsim.org/news/

#### SUMO(Eclipse SUMO / DLR)と SUMO User Conference
- 種別: OSSコミュニティ / 学会
- 中心人物: DLR 交通システム研究所。2026年の基調講演は Carolina Osorio(生成モデル×交通科学)。
- 代表的な成果: https://github.com/eclipse-sumo/sumo(4.2k stars)
- 窓口・発信: https://sumo.dlr.de/hugo/2026 / sumo-conference@dlr.de / ML: sumo-user@eclipse.org、sumo-announce@eclipse.org
- 活動状況: SUMO Conference 2026 は 2026-06-01〜04 にベルリン・アドラースホフ(WISTA)で開催。2013年から毎年ベルリンで開かれている。2026年のポスターに「Toward an Agentic AI Framework for Integrated MATSim-SUMO Policy Evaluation」(Micallef, Bondin, Dingli)と「LLM-Driven Agents for Evacuation Simulation in SUMO」(Michael Jones)があった。2027年の日程は未確認。
- 渋谷シムへの使いどころ: (7) 車両と歩行者のミクロ物理層。JuPedSim と連成したシナリオが PedestrianDynamics/SUMO-JuPedSim-Simulations にある。LLM エージェントと結合した実例も出始めている。
- 既出: 新規
- 出典: https://sumo.dlr.de/hugo/2026 , https://www.dlr.de/en/ts/latest/events/2026/sumo-conference-2026 , https://github.com/eclipse-sumo/sumo

#### ActivitySim コンソーシアム / Zephyr Foundation
- 種別: OSSコミュニティ(非営利財団)
- 中心人物: AMPO(米国の都市圏計画機関の協会)と ActivitySim コンソーシアム。Zephyr Foundation は 501(c)(3) の非営利法人。
- 代表的な成果: https://github.com/ActivitySim/activitysim
- 窓口・発信: https://zephyrtransport.org/ (Discord・Forum・YouTube・Medium・ニュースレター)。TMIP メーリングリストは約1,600人。MoMo(Modeling Mobility)会議がある。
- 活動状況: wiki に2025-07までの開発会議の記録がある。Zephyr の活動一覧には ActivitySim と UrbanSim Community が含まれる。2026年のイベント日程は未確認(events ページの取得に失敗)。
- 渋谷シムへの使いどころ: (3)(6) 活動ベースモデルの実務的な較正と検証の文化を学べる。Discord で実務者に質問できる。
- 既出: ActivitySim は既出。Zephyr は新規。
- 出典: https://zephyrtransport.org/ , https://github.com/ActivitySim/activitysim/wiki/Current-Development

#### UrbanSim(Paul Waddell / UrbanSim Inc. / UDST)
- 種別: 企業 / OSSコミュニティ / 研究室
- 中心人物: Paul Waddell(UC Berkeley 都市地域計画、Urban Analytics Lab)
- 代表的な成果: https://github.com/UDST/urbansim(540 stars、最終更新 2023-12)、pandana、synthpop。商用版は UrbanSim Cloud Platform 3.13.1 と UrbanCanvas。
- 窓口・発信: https://cloud.urbansim.com/docs/ / https://www.ual.berkeley.edu/projects
- 活動状況: OSS は 2023年末から更新が止まっている。会社の 2026年の状況は未確認。
- 渋谷シムへの使いどころ: (8) 土地利用・再開発の顧客(行政・ディベロッパー)にシミュレーションを売ってきた先例。課金モデルの参考になる。
- 既出: 新規
- 出典: https://github.com/UDST , https://cloud.urbansim.com/docs/general/documentation/urbansim.html

#### awesome-llm4tr(LLM for Transportation サーベイ)
- 種別: その他(キュレーションリスト)
- 中心人物: Tong Nie、Jian Sun、Wei Ma
- 代表的な成果: arXiv:2503.21411 / https://github.com/tongnie/awesome-llm4tr(77 stars)
- 窓口・発信: GitHub
- 活動状況: 2025-06 に Artificial Intelligence for Transportation 誌に掲載
- 渋谷シムへの使いどころ: (8) 交通分野で LLM がどう使われているかの見取り図になる。
- 既出: 新規
- 出典: https://github.com/tongnie/awesome-llm4tr

#### Awesome-Urban-Foundation-Models(HKUST-GZ USAIL)
- 種別: その他(キュレーションリスト)
- 中心人物: Weijia Zhang、Hao Liu、Hui Xiong ほか
- 代表的な成果: arXiv:2402.01749 / https://github.com/usail-hkust/Awesome-Urban-Foundation-Models(223 stars)
- 窓口・発信: GitHub
- 活動状況: 2026-03 に ACM TIST に採録
- 渋谷シムへの使いどころ: (6) 都市基盤モデル全般の文献網羅
- 既出: 新規
- 出典: https://github.com/usail-hkust/Awesome-Urban-Foundation-Models

---

### C. 群衆・歩行者・避難(物理層)

#### JuPedSim / PedestrianDynamics(Forschungszentrum Jülich IAS-7)
- 種別: OSSコミュニティ / 研究室
- 中心人物: Mohcine Chraibi ほか(Jülich IAS-7 市民安全研究所)
- 代表的な成果: https://github.com/PedestrianDynamics/jupedsim(v1.4.2、2026-05-21 リリース、LGPLv3)、PedPy(軌跡解析)、jupedsim-scenarios、SUMO-JuPedSim-Simulations、crowd-accidents(1900〜2024年の群衆事故リスト)、pyFDS-Evac(火災時の避難)
- 窓口・発信: https://www.jupedsim.org / https://pedestriandynamics.org/ / ブラウザ版 app.jupedsim.org / GitHub Discussions(jupedsim-web-community)
- 活動状況: 2026-07 時点で複数リポジトリを更新中。DXF/IFC を取り込める Web 版も公開した。
- 渋谷シムへの使いどころ: (7) LLM が目的地を決め、JuPedSim が歩行物理を担う、という分業がそのまま組める。PedPy の基本図(fundamental diagram)解析は群衆層の検証に使える。
- 既出: jupedsim は既出(github)。PedPy・Web 版・コミュニティは新規。
- 出典: https://pypi.org/project/jupedsim , https://github.com/PedestrianDynamics , https://github.com/PedestrianDynamics/jupedsim-web-community , https://pedestriandynamics.org/

#### PED(Pedestrian and Evacuation Dynamics)国際会議
- 種別: 学会(隔年開催)
- 中心人物: PED2027 の組織委員は Tao Chen・Wenguo Weng(清華)、Mohcine Chraibi(Jülich)、Ruggiero Lovreglio(Massey)ほか
- 代表的な成果: Proceedings(Collective Dynamics 誌、Acta Polytechnica CTU Proceedings)
- 窓口・発信: https://ped2027.tsinghua.edu.cn/ / 過去の Proceedings は https://collective-dynamics.eu/index.php/cod/ped
- 活動状況: PED2025 は 2025-09-09〜12 にプラハの CTU で開催(初日は PhD Workshop)。PED2027 は 2027-09-26〜29 で、参加登録開始 2027-01-01、アブストラクト締切 2027-02-28、採否通知 4/30、フルペーパー締切 7/31(いずれも暫定)。主催は清華大学で、会場ページは未確認。
- 渋谷シムへの使いどころ: (7) 群衆物理の専門家が集まる場。PED2025 では LLM 生成エージェントによる群衆の発表が出ている(下記 Geraerts)。2027年のアブストラクト投稿も現実的。
- 既出: 新規
- 出典: https://ped2027.tsinghua.edu.cn/Key_Dates.htm , https://www.ojs.cvut.cz/ojs/index.php/APP/article/view/11545

#### Roland Geraerts(Utrecht University)/ uCrowds — 「Generative Agents in Crowd Simulation」
- 種別: 研究室 / スタートアップ
- 中心人物: Roland Geraerts(ユトレヒト大学 准教授、uCrowds の創業者)、Nizar Ntarouis
- 代表的な成果: Ntarouis & Geraerts「Generative Agents in Crowd Simulation: A Cognitive Approach with LLMs」(Acta Polytechnica CTU Proceedings 57, 2026、PED2025)。商用の群衆シミュレータ SimCrowds(uCrowds)。
- 窓口・発信: https://webspace.science.uu.nl/~gerae101/ (YouTube・Twitter・LinkedIn へのリンクあり)
- 活動状況: 2026年に論文が掲載された。uCrowds の現況は未確認。
- 渋谷シムへの使いどころ: (7)(1) System 1/2 の二重過程で LLM に目標を決めさせ、経路と衝突回避は既存の群衆エンジンに任せる構成。自分のシムとほぼ同じ設計思想。250体までで API レート制限がボトルネックになった点、協調が弱く群集の追従(herding)が出なかった点など、限界の報告がそのまま参考になる。
- 既出: 新規
- 出典: https://webspace.science.uu.nl/~gerae101/pdf/Generative_Agents_in_Crowd_Simulation_PED2025-2026.pdf , https://webspace.science.uu.nl/~gerae101/

#### Emergent Crowds Dynamics from Language-Driven Multi-Agent Interactions
- 種別: その他(論文)
- 中心人物: Yibo Liu、Liam Shatzel、Brandon Haworth、Teseo Schneider
- 代表的な成果: arXiv:2508.15047。近くにいるエージェント同士が LLM で会話し、その会話・感情・視界が歩行に反映される。集団が自然にまとまったり離れたりする。
- 窓口・発信: 未確認
- 活動状況: 2025-08 の arXiv
- 渋谷シムへの使いどころ: (2)(7) 「近接したら会話が起きる」トリガーと、会話が移動に効く仕組みは、会話率 0.07% 問題に直接効く。
- 既出: 既出(論文)
- 出典: https://arxiv.org/abs/2508.15047

#### Hirokazu Shirado ら — LLM エージェントによる緊急時の群衆シミュレーションの政策実装
- 種別: その他(論文)
- 中心人物: Yuxuan Li、Sauvik Das、Hirokazu Shirado(白土寛和、CMU)
- 代表的な成果: arXiv:2509.21868「What Makes LLM Agent Simulations Useful for Policy Practice?」。大学の防災チームと1年かけて共同設計し、13,000体の群衆移動と情報伝達をシミュレーションした。
- 窓口・発信: 未確認(個人サイトは robots で取得不可)
- 活動状況: 2025-09 の arXiv
- 渋谷シムへの使いどころ: (8)(6) 「正確な予測よりも意思決定の材料として使う」「検証できるシナリオから始めて信頼を得る」という3原則は、行政・再開発の顧客に提案するときの型になる。
- 既出: 新規
- 出典: https://arxiv.org/abs/2509.21868

#### 清華大学 土木系 — LLM 強化 ABM による災害時の群衆避難(EGU26)
- 種別: 研究室
- 中心人物: Sen Yang、Chen Gu(清華大学 土木工学系)、Yi Zhang(東南大学)
- 代表的な成果: EGU26-3725「LLM-Enhanced Agent-Based Modeling for Intelligent Crowd Evacuation under Disaster Scenarios」。バッチプロンプトと並列計算で規模を広げ、歩行者と車両の両方を扱う。
- 窓口・発信: https://meetingorganizer.copernicus.org/EGU26/EGU26-3725.html
- 活動状況: EGU 2026(2026-03 更新)
- 渋谷シムへの使いどころ: (5)(7) 大規模群衆で LLM 呼び出しをバッチ化する実装上の工夫が参考になる。
- 既出: 新規
- 出典: https://meetingorganizer.copernicus.org/EGU26/EGU26-3725.html

#### Vadere / CrowNet(Munich University of Applied Sciences, Gerta Köster)
- 種別: OSSコミュニティ / 研究室
- 中心人物: Gerta Köster
- 代表的な成果: Vadere(Social Force、Optimal Steps など複数の歩行モデルを持つ OSS)、CrowNet(Vadere と無線通信モデルの連成)
- 窓口・発信: https://www.vadere.org/
- 活動状況: 最新リリースは未確認
- 渋谷シムへの使いどころ: (7) 歩行モデルを比べる基準実装になる。CrowNet の「スマホで歩行者を誘導する」シナリオは、渋谷の混雑誘導という用途(8)に近い。
- 既出: 新規
- 出典: https://www.vadere.org/ , https://www.vadere.org/crownet/

#### Dirk Helbing — ETH Zurich Computational Social Science(COSS)
- 種別: 研究室 / 個人
- 中心人物: Dirk Helbing(ETH 教授、Complexity Science Hub Vienna の外部教員)
- 代表的な成果: Social Force Model(PRE 1995)、Escape panic(Nature 2000)、Crowd disasters(PRE 2007)
- 窓口・発信: https://coss.ethz.ch/ / X https://twitter.com/coss_eth / YouTube https://www.youtube.com/@coss_eth
- 活動状況: 進行中のプロジェクトとして DIT4Tram、CoCi、SoBigData++ が載っている(日付は未確認)
- 渋谷シムへの使いどころ: (7) 社会力モデルの本家。群衆乱流など「密度の閾値」を検証する基準になる。
- 既出: 既出(論文 0802.1284 など Helbing 系が known_arxiv にある可能性。人物・研究室としては新規)
- 出典: https://coss.ethz.ch/ , https://en.wikipedia.org/wiki/Dirk_Helbing

---

### D. 都市デジタルツイン・都市科学ラボ

#### MIT Media Lab City Science Group / CityScope
- 種別: 研究室 / OSSコミュニティ
- 中心人物: Kent Larson(Professor of the Practice)、Luis Alberto Alonso Pastor、Ariel Noyman、Markus Elkatsha、Arnaud Grignard(GAMA)ほか
- 代表的な成果: https://github.com/CityScope (81リポジトリ、cityscopeJS など)
- 窓口・発信: https://cityscope.media.mit.edu (GitHub に記載)/ 講義 MAS.552 City Science Fall 2026
- 活動状況: GitHub は 2026-10-06 にも更新(CS_CityIO_uptime、MineScope、transitLOS など)。City Science Lab のネットワークがハンブルク HCU などにある。
- 渋谷シムへの使いどころ: (8) 「シミュレーションを模型や投影で見せて、住民・行政の合意形成に使う」という先例。顧客向けデモの形として参考になる。
- 既出: 新規
- 出典: https://github.com/CityScope , https://www.media.mit.edu/projects/cityscope/people/ , https://www.media.mit.edu/courses/mas-552-city-science-fall-2026/

#### MIT Senseable City Lab
- 種別: 研究室
- 中心人物: 未確認(サイト本文を取得できなかった)
- 代表的な成果: 未確認
- 窓口・発信: https://senseable.mit.edu/
- 活動状況: 未確認
- 渋谷シムへの使いどころ: (6) 都市センシングデータ。詳細は要再調査。
- 既出: 新規
- 出典: https://senseable.mit.edu/

#### NYU Tandon CUSP / Urban AI Symposium(2025-10-28、東大 CSIS と共催)
- 種別: 学会・ワークショップ
- 中心人物: Takahiro Yabe(主催)。登壇者に関本義秀(東大、神戸のバス路線計画に合成人流を使った事例)、Paul Torrens(NYU、AI と歩行者行動・EEG)、Cláudio Silva(StreetAware)ほか
- 代表的な成果: シンポジウム自体
- 窓口・発信: https://engineering.nyu.edu/news/urban-ai-symposium-nyu-tandon-brings-together-global-experts
- 活動状況: 2025年に開催。次回は未確認。
- 渋谷シムへの使いどころ: (7)(6) Paul Torrens の歩行者行動研究と、関本研の合成人流の実務適用がつながる場。日米の人脈ハブになっている。
- 既出: 新規
- 出典: 上記 URL

#### NVIDIA Omniverse Blueprint for Smart City AI
- 種別: 企業
- 中心人物: NVIDIA。初期採用企業は Bentley、Cesium、Linker Vision、AVES Reality、K2K、Milestone Systems、SNCF Gares&Connexions、Trimble など
- 代表的な成果: Omniverse(都市デジタルツイン)、Cosmos(合成データ)、Metropolis(映像解析エージェント)、NeMo を組み合わせた参照構成
- 窓口・発信: https://blogs.nvidia.com/blog/smart-city-ai-blueprint-europe/
- 活動状況: 2025-06-11 に発表。高雄、パレルモ、ジェノヴァ、デトロイト、クリーブランドで導入事例がある。
- 渋谷シムへの使いどころ: (7)(5) 物理層と可視化を GPU デジタルツインに載せる方向。主眼は映像 AI エージェントで、LLM 住民シミュレーションではない。
- 既出: 新規(warp / PhysX は既出)
- 出典: https://blogs.nvidia.com/blog/smart-city-ai-blueprint-europe/ , https://www.nvidia.com/en-us/omniverse/

---

### E. 日本の都市データ・コンペ・学会

#### Project PLATEAU(国交省)— PLATEAU AWARD 2026 / PLATEAU Hack Challenge 2026
- 種別: その他(官民プロジェクト / コンペ)
- 中心人物: 国土交通省 都市局。運営には ASCII STARTUP / KADOKAWA が関わる。
- 代表的な成果: https://github.com/Project-PLATEAU (120リポジトリ。2026年に更新されたものに PLATEAU-VIEW-5.0、Fire-Spread-Simulator、Fluid-dynamics-simulator、Earthquake-simulation-tools、PLATEAU ストリーミング用のエージェント skills がある)
- 窓口・発信: AWARD https://www.mlit.go.jp/plateau-next/award/ / Hack Challenge の申込 connpass https://asciistartup.connpass.com/event/407000/
- 活動状況:
  - **PLATEAU AWARD 2026**: 本エントリー 2026-08-28〜**2026-11-19(木)締切**。プレエントリーは **11/6** まで(公式ページ https://www.mlit.go.jp/plateau-next/award/ )。応募資格は問わない(未成年は保護者の同意が必要)。賞金総額200万円以上。自治体部門のオンライン発表は 12/5〜6。最終審査と授賞式は 2027年2月下旬〜3月上旬に東京で予定。
  - **PLATEAU Hack Challenge 2026 in Tokyo**: 2026-09-26〜27 に TUNNEL TOKYO(大崎)で開催済み(申込締切 9/24)。
  - リポジトリに人流シミュレーションの公開物は見当たらなかった(上位10件の範囲で)。
- 渋谷シムへの使いどころ: (8)(7) 渋谷の建物ジオメトリはもう PLATEAU から取り込んでいる。**AWARD 2026 は 11/19 締切で、高校生でも応募できる**ので、成果発表と顧客獲得の場として現実的。
- 既出: PLATEAU SDK・Converter は既出。AWARD・Hack は新規。
- 出典: https://koubo.jp/contest/349361 , https://dime.jp/company_news/detail/?pr=2714602 , https://github.com/Project-PLATEAU

#### 公共交通オープンデータ協議会(ODPT)— 公共交通オープンデータチャレンジ 2026
- 種別: その他(協議会 / コンペ)
- 中心人物: 坂村健(会長、YRP ユビキタス・ネットワーキング研究所 所長)。共催は国交省、INIAD cHUB、東大、AIGID。
- 代表的な成果: 開発者サイト https://developer.odpt.org 、GTFS データリポジトリ
- 窓口・発信: https://www.odpt.org/ / チャレンジ https://challenge2026.odpt.org/ / 事務局 odpt-office@ubin.jp
- 活動状況: コンテスト期間は 2026-07-01〜2027-03-12。**応募受付 2026-10-01〜2027-01-11**。1次審査 2027-01-23〜24、最終審査と表彰 2027-02-20。賞金は最大300万円。2026年に京王のリアルタイム車両位置(9/14)、都営大江戸線12駅の構内図・経路(9/17)、JR東日本(7/17)、東急・小田急・京急・西武・東武などのデータが公開された。ODPT 自体も 2026-10 時点で会員を増やし続けている。
- 渋谷シムへの使いどころ: (3)(7) 渋谷に乗り入れる京王・東急の時刻表とリアルタイムデータで、駅への到着波を外から与えれば来街ピーク時刻の較正に直接使える。チャレンジへの応募は(8)の実績づくりにもなる。
- 既出: 新規(google/transit は既出)
- 出典: https://challenge2026.odpt.org/ , https://prtimes.jp/main/html/rd/p/000000020.000146050.html , https://www.odpt.org/

#### 東京都 デジタルツイン実現プロジェクト
- 種別: その他(行政)
- 中心人物: 東京都 デジタルサービス局
- 代表的な成果: 東京都デジタルツイン 3D ビューア(都営バスのリアルタイム位置などを重ねて表示、ソースコード公開)、データ連携基盤
- 窓口・発信: https://info.tokyo-digitaltwin.metro.tokyo.lg.jp/
- 活動状況: 2026-09-25 に小笠原村のデータを追加、2026-08・07 にもデータを追加。社会実装ロードマップは第3版。2030年に全面実装をめざしている。人流シミュレーションの具体的な公開物はなし。
- 渋谷シムへの使いどころ: (8) 行政を顧客にするときの入口。データ追加のペースが速い。
- 既出: 新規
- 出典: https://info.tokyo-digitaltwin.metro.tokyo.lg.jp/

#### 株式会社Agoop(人流データ企業)
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: マチレポ(エリアの来訪者分析)、流動人口データ、コンプレノ(人と車の動きの動画化)
- 窓口・発信: https://www.agoop.co.jp/
- 活動状況: 2026年も製品更新が続いている。マチレポ 7.6.0、コンプレノ 3.12.0、9/14 に公共交通の徒歩圏レイヤーを追加。近鉄 GHD の事例もある。
- 渋谷シムへの使いどころ: (3)(8) KDDI 人流とは別系統のデータ源。また「出店検討の小売向け人流分析」を既に売っている競合でもある。自分のシムとの違い(what-if ができる点)を言語化するときの比較対象になる。
- 既出: 新規
- 出典: https://www.agoop.co.jp/

#### Replica(米国)
- 重複のため「企業」タブの同名項目にまとめた

#### 日本都市計画学会 2026年度全国大会(第61回 論文発表会)
- 種別: 学会
- 中心人物: 日本都市計画学会
- 代表的な成果: 都市計画論文集
- 窓口・発信: https://www.cpij.or.jp/event/conf/2026.html / 特設サイト https://pub.confit.atlas.jp/ja/event/annuconfcpij2026 / annual-conference@cpij.or.jp
- 活動状況: **2026-10-30(金)〜11-01(日)、北海道大学 札幌キャンパス**で対面のみ開催。参加費は学生1,100円、非会員9,900円で、事前のオンライン登録が必須。シンポジウムのテーマは「開かれた都市計画に向けて」。
- 渋谷シムへの使いどころ: (8) 行政・再開発の実務者と研究者に会える場。
- 既出: 新規
- 出典: https://www.cpij.or.jp/ , https://www.cpij.or.jp/event/conf/2026.html

#### 土木学会 土木計画学研究発表会 / 交通工学研究会(JSTE)
- 種別: 学会
- 中心人物: 土木学会 土木計画学研究委員会 / 一般社団法人 交通工学研究会
- 代表的な成果: 土木計画学研究・講演集、交通工学論文集
- 窓口・発信: https://committees.jsce.or.jp/ip/ / https://www.jste.or.jp/
- 活動状況: 2026年の土木計画学秋大会の日程と会場は**未確認**(公式ページの取得失敗、検索の上限にも到達)。慣例では11月下旬の土日に開かれる(例: 第68回は 2023-11-25〜26、東京都立大学)。JSTE では「第46回交通工学研究発表会」が予定に載っているが、日程は未掲載。そのほか第8回 JSTE シンポジウム(長野)、第50回交通技術セミナー(2026-10 告知)がある。
- 渋谷シムへの使いどころ: (3)(7) 日本の交通計画・人流モデルの研究者(活動ベースモデル、PT 調査の専門家)に会える。PT 調査の扱いや較正について相談できる。
- 既出: 新規
- 出典: https://planner.t.u-tokyo.ac.jp/archives/3959 , https://www.jste.or.jp/

---

### F. ACM SIGSPATIAL 2026 周辺ワークショップ(2026-11-03、Riverside, CA)

#### UMFM(Urban Mobility Foundation Models)ワークショップ
- 種別: 学会・ワークショップ
- 中心人物: 未確認(2025年の案内ページは rsvp.withgoogle.com にあるが、主催者名は記載なし)
- 代表的な成果: 2025年に第1回、2026年に第2回
- 窓口・発信: https://rsvp.withgoogle.com/events/sigspatial-2025-umfm-workshop
- 活動状況: 2026-11-03 開催(第2回)。締切は未確認(おそらく過ぎている)。
- 渋谷シムへの使いどころ: (6) 人流基盤モデルの研究者が集まる場。
- 既出: 新規
- 出典: https://sigspatial2026.sigspatial.org/workshops.html

#### GeoSim(GeoSpatial Simulation)ワークショップ
- 種別: 学会・ワークショップ
- 中心人物: 未確認
- 代表的な成果: 合成空間データのリポジトリ
- 窓口・発信: https://geosim.org/
- 活動状況: 第9回が 2026-11-03 に開催。投稿締切は 2026-08-22(延長後)で、すでに過ぎている。メタバースへの言及がある。
- 渋谷シムへの使いどころ: (7)(3) 地理空間 ABM の研究者コミュニティ。2027年の投稿先候補。
- 既出: 新規
- 出典: https://geosim.org/

#### UrbanAI 2026(Advances in Urban-AI)
- 種別: 学会・ワークショップ
- 中心人物: ORNL 系(主催者名は未確認)
- 代表的な成果: なし
- 窓口・発信: https://events.ornl.gov/urbanai2026
- 活動状況: 第4回、2026-11 に Riverside で開催。投稿締切は 2026-08-28 で過ぎている。トピックに agentic AI、foundation model、都市デジタルツインが入っている。
- 渋谷シムへの使いどころ: (8) 2027年の投稿先候補。
- 既出: 新規
- 出典: https://events.ornl.gov/urbanai2026

#### GeoGenAgent(Generative and Agentic AI for Multi-Modality Space-Time Intelligence)
- 種別: 学会・ワークショップ
- 中心人物: Yanjie Fu(ASU)、Kunpeng Liu、Pengyang Wang、Dongjie Wang、Zhongren Peng ほか
- 代表的な成果: 2025年のワークショップ(Guang Wang が合成人間活動トレースについて基調講演)
- 窓口・発信: https://geogenagent.github.io/SIGSPATIAL2025-Workshop/
- 活動状況: 2025-11-03 にミネアポリスで開催。2026年の開催は未確認(SIGSPATIAL 2026 の一覧に名前が見当たらない)。
- 渋谷シムへの使いどころ: (6) 生成 AI と時空間の交差領域の研究者。
- 既出: 新規
- 出典: https://geogenagent.github.io/SIGSPATIAL2025-Workshop/

---

### 担当範囲で見つからなかった/確認できなかったもの
- **WebSearch の上限(200回、全エージェント共有)に到達した**ため、以下は検索で裏が取れなかった。
  - 柴崎研(東大)の現況
  - Carolina Osorio の現所属
  - MIT Senseable City Lab の 2026年の動向
  - Replica の 2026年の資金調達
  - ActivitySim と Zephyr の 2026年イベント日程
  - 土木計画学 2026年秋大会の日程
  - 交通工学研究発表会の日程
  - GIS Cup 2026 のテーマ
- 「MobAgent」「Mobility-LLM」という名前の主要プロジェクトは特定できなかった。近い系統として TrajLLM、TrajGenAgent、ActivityEditor、CoPB の KDD 2026 版を収録した。
- PLATEAU 公式サイトは robots で取得できなかった。PLATEAU の Discord・Slack などのコミュニティ窓口は未確認。
- 東京都デジタルツインで人流シミュレーションを公開した例は見当たらなかった。
- 「LLM for transportation」を名乗る独立したワークショップ(TRB、ITSC など)の 2026年の開催情報は確認できなかった。代わりに SIGSPATIAL 系(UMFM、UrbanAI、GeoSim)と SUMO、MUM の LLM 関連発表を収録した。


## 5. 検証・ペルソナ・記憶・推論コスト


調査日: 2026-10-13。担当範囲は「LLM が人を再現できるかの検証」「ペルソナの安定性(ドリフト)」「エージェント記憶」「大規模推論コスト」に関わる人・研究室・企業・コミュニティ。対応する詰まりどころは主に (2) 会話 / (4) 複数日・記憶・ペルソナドリフト / (5) GPU・推論コスト / (6) 検証方法。
「既出」は known_arxiv.txt / known_github.txt との突き合わせ結果。

凡例(渋谷シムの検証二軸):
- **believability(もっともらしさ)**: 個々のエージェントの言動が人間らしく、設定と矛盾しないか(ミクロ、主観評価・一貫性)
- **accuracy(正確さ)**: 集団の分布・効果量・時系列が実データと合うか(マクロ、holdout 照合)

---

### A. 「LLM は人を再現できるか」— 検証研究の人と組織

#### Helmholtz Munich, Institute for Human-Centered AI(Centaur / Psych-101)
- 種別: 研究室
- 中心人物: Marcel Binz(筆頭著者・ポスドク、ERC Starting Grant「MIDAS」)、Eric Schulz(研究所長)。共著に Elif Akata, Matthias Bethge ほか
- 代表的な成果: 「A foundation model to predict and capture human cognition」Nature 644, 1002–1009 (2025年7月2日), arXiv 2410.20268。Llama 3.1 70B を Psych-101(160実験・60,092人・約1,070万選択)で QLoRA 微調整した Centaur。8B 版 Minitaur(https://huggingface.co/marcelbinz/Llama-3.1-Minitaur-8B)。データ https://huggingface.co/datasets/marcelbinz/Psych-101(Apache-2.0、テスト集合は CC-BY-ND でゲート付き)、モデル https://huggingface.co/marcelbinz/Llama-3.1-Centaur-70B
- 窓口・発信: Helmholtz Munich ニュース https://www.helmholtz-munich.de/en/newsroom/news-all/artikel/ai-that-thinks-like-us-and-could-help-explain-how-we-think / Hugging Face(marcelbinz)。X・Discord は未確認
- 活動状況: 2026年も活動中。Psych-101 から派生した微調整モデルが HF 上に 124 件(第三者による Qwentaur-0.6B/8B、Olmotaur-7B などを含む)。Psych-101 に属性・心理特性を追加する計画が公表されている
- 渋谷シムへの使いどころ: (6)(5) 「1人の選択の対数尤度で人間行動を当てられるか」という accuracy の評価枠組み(保持した参加者に対する NLL、分布外課題)は、System 1.5(軽量判断モデル)の評価設計にそのまま転用できる。Minitaur 8B と 0.6B 級の派生モデルは「人間らしい選択に寄せた小型モデル」なので、System 1.5/2α の候補になる
- 既出: 新規
- 出典: https://www.helmholtz-munich.de/en/newsroom/news-all/artikel/ai-that-thinks-like-us-and-could-help-explain-how-we-think , https://www.nature.com/articles/s41586-025-09215-4 , https://huggingface.co/datasets/marcelbinz/Psych-101

#### Simile(Joon Sung Park / Michael Bernstein / Percy Liang)
- 種別: スタートアップ
- 中心人物: Joon Sung Park(共同創業者 CEO、Generative Agents の作者)、Michael Bernstein(共同創業者・Chief Data Officer)、Percy Liang(共同創業者・Chief Scientist)
- 代表的な成果: 「LLM Agents Grounded in Self-Reports Enable General-Purpose Simulation of Individuals」(旧題 Generative Agent Simulations of 1,000 People)arXiv 2411.10109。2時間インタビューから作った 1,052 人分のエージェントで、GSS の保持項目について本人の2週間後の再回答一致率の 83〜86% に到達(属性だけのエージェントは 74%)
- 窓口・発信: https://www.simile.com / ブログ https://www.simile.com/blog / X https://x.com/simile_ai / LinkedIn https://www.linkedin.com/company/simile-ai-inc/
- 活動状況: 2026年7月30日に Series B $200M(評価額 $2B、Greenoaks リード)。その約5か月前に Series A $100M。顧客: CVS Health, Wealthfront, Banco Itaú, Suntory Beverages & Food, Gallup, Deloitte など。2026年8月25日のブログ「Building confidence in Simile」で、TVD(全変動距離)による検証と「誤差予測モデル」による信頼度の付け方を公開
- 渋谷シムへの使いどころ: (6) accuracy 評価の業界標準になりつつある「本人の再回答一致率(test-retest)で正規化した精度」と「分布の TVD」の2つを、KDDI 人流の holdout 照合に加える指標として採用できる。とくに「結果ごとに予測誤差を別モデルで推定し、信頼度ラベルを付ける」方式は、アンサンブル予測を顧客(小売・行政)に出すときの見せ方として参考になる。(8) 日本の先行競合・顧客像(Suntory)の把握にも使える
- 既出: 既出(論文 2411.10109)。会社としては新規
- 出典: https://www.simile.com , https://www.simile.com/blog/confidence , https://runtimewire.com/article/simile-raises-200m-series-b-2b-valuation , https://arxiv.org/abs/2411.10109

#### Aaru
- 重複のため「企業」タブの同名項目にまとめた

#### Expected Parrot(EDSL)/ John J. Horton
- 重複のため「企業」タブの同名項目にまとめた

#### Benjamin S. Manning(MIT Sloan)
- 種別: 個人(研究者)
- 中心人物: Benjamin Manning(MIT Sloan 博士課程、IT グループ、MIT IDE)
- 代表的な成果: 「General Social Agents」arXiv 2508.17407(Horton と共著。少数の「シードゲーム」の人間データでエージェントを作り、88万3,320種の新しいゲームから 1,500 種を抽出して事前登録した実験で、人の初手を cognitive hierarchy や均衡より正確に予測)/「Automated Social Science: Language Models as Scientist and Subjects」arXiv 2404.11794
- 窓口・発信: https://benjaminmanning.io / X @BenSManning / MIT IDE https://ide.mit.edu/people/benjamin-manning/
- 活動状況: 2026年6月に General Social Agents の改訂版、2026年4月にプロンプト適応の論文
- 渋谷シムへの使いどころ: (6)(3) 「少ない実データ(シード)で調整したエージェントが、未見の状況でも当たるか」を事前登録して確かめる手順は、来街者ピークの較正(3)と holdout 照合(6)を分けて設計するときの見本になる。較正に使ったデータと検証に使うデータを分けるという考え方そのもの
- 既出: 新規(2508.17407, 2404.11794 とも未掲載)
- 出典: https://ide.mit.edu/people/benjamin-manning/ , https://arxiv.org/abs/2508.17407 , https://dspace.mit.edu/handle/1721.1/157089

#### Lisa Argyle(Purdue 大学、元 BYU)/ BYU「silicon samples」グループ
- 種別: 個人(研究者)
- 中心人物: Lisa Argyle(Purdue 大学政治学准教授、元 BYU 教員、Cooperative Election Study 副 PI)。共著者 David Wingate(BYU)の現況は今回は未確認
- 代表的な成果: 「Out of One, Many: Using Language Models to Simulate Human Samples」(silicon samples)arXiv 2209.06899。2025年に PNAS(チャットによる介入で政治的不寛容が下がる)、Nature Computational Science(生成モデルを研究に責任をもって使う枠組み: 検証・透明性・推論の限界)、PNAS「Testing theories of political persuasion using AI」を発表
- 窓口・発信: Purdue 紹介 https://www.cla.purdue.edu/academic/polsci/news/lisa-argyle.html / https://sail.byu.edu/directory/lisa-argyle 。X は未確認
- 活動状況: 2025〜2026年に Purdue へ移籍(正確な日付は未確認)。AI 音声エージェントとの電話会話実験を進めている
- 渋谷シムへの使いどころ: (6) silicon sampling が「代表性」を確かめる基準として使った「代数的忠実性(algorithmic fidelity)」の4条件(人間の回答と区別できない / 前後の一貫性 / 条件ごとの回答パターンの再現 / 属性間の関係構造の再現)は、believability と accuracy の中間にある評価観点としてそのまま流用できる
- 既出: 既出(論文 2209.06899)。人としては新規
- 出典: https://www.cla.purdue.edu/academic/polsci/news/lisa-argyle.html , https://sail.byu.edu/directory/lisa-argyle

#### Gati Aher / Rosa Arriaga / Adam Tauman Kalai(Turing Experiments)
- 種別: 個人(研究者)
- 中心人物: Gati Aher, Rosa I. Arriaga, Adam Tauman Kalai(Microsoft Research に掲載された論文)
- 代表的な成果: 「Using Large Language Models to Simulate Multiple Humans and Replicate Human Subject Studies」ICML 2023, arXiv 2208.10264。最後通牒ゲーム・袋小路文・ミルグラム実験は再現できたが、Wisdom of Crowds では「hyper-accuracy distortion(人より正確すぎる歪み)」が出た
- 窓口・発信: https://www.microsoft.com/en-us/research/publication/using-large-language-models-to-simulate-multiple-humans-and-replicate-human-subject-studies/ / 講演動画 https://slideslive.com/39002948/using-large-language-models-to-simulate-multiple-humans-and-replicate-human-subject-studies 。コードのリンクは確認できず
- 活動状況: 論文は2023年。著者の2026年の動向は未確認
- 渋谷シムへの使いどころ: (6)(1) 「LLM 住人が人より合理的・正確すぎる」という歪み(例: 空腹にきっちり反応しすぎる、最短経路を選びすぎる)を検出する観点。渋谷シムで空腹が行動の主因になりすぎる問題(1)も、この「hyper-accuracy」の一種として整理できる
- 既出: 既出(論文 2208.10264)
- 出典: https://www.microsoft.com/en-us/research/publication/using-large-language-models-to-simulate-multiple-humans-and-replicate-human-subject-studies/ , https://proceedings.mlr.press/v202/aher23a.html

#### OpinionQA(Stanford tatsu-lab: Santurkar / Durmus / Hashimoto / Liang)
- 種別: 研究室
- 中心人物: Shibani Santurkar(リポジトリ管理者)、Esin Durmus, Faisal Ladhak, Cinoo Lee, Percy Liang, Tatsunori Hashimoto
- 代表的な成果: 「Whose Opinions Do Language Models Reflect?」ICML 2023, arXiv 2303.17548。Pew American Trends Panel をもとにした 1,498 問と個人回答 https://github.com/tatsu-lab/opinions_qa
- 窓口・発信: GitHub https://github.com/tatsu-lab/opinions_qa / OpenAI Forum 講演 https://forum.openai.com/public/events/whose-opinions-do-language-models-reflect-2023-08-17
- 活動状況: データセットとしては定番化。リポジトリの最新更新は未確認
- 渋谷シムへの使いどころ: (6) 「回答分布同士の距離(Wasserstein 系)で属性グループごとの代表性を測る」という手法。渋谷シムでは「年齢×居住地(来街者/住民/通勤者)」の層ごとに、行動分布の距離を出す設計に応用できる
- 既出: 既出(論文 2303.17548)
- 出典: https://github.com/tatsu-lab/opinions_qa , https://arxiv.org/abs/2303.17548

#### GlobalOpinionQA(Anthropic Societal Impacts: Esin Durmus ほか)
- 種別: 企業(研究チーム)
- 中心人物: Esin Durmus(筆頭)、Deep Ganguli, Jack Clark, Amanda Askell ほか(Anthropic)
- 代表的な成果: 「Towards Measuring the Representation of Subjective Global Opinions in Language Models」arXiv 2306.16388。データ https://huggingface.co/datasets/Anthropic/llm_global_opinions 。国ごとの意見との一致度を測ると、既定では米国と一部の欧州・南米に寄る。「〇〇国の人として答えて」と指示すると近づくがステレオタイプも出る。翻訳しても一致はしない
- 窓口・発信: Hugging Face(上記)。チーム単位の X は未確認
- 活動状況: データセットは公開済み。2026年の後継は未確認
- 渋谷シムへの使いどころ: (6)(2) 「日本語で聞けば日本人らしくなるわけではない」という知見は、日本語プロンプトで渋谷の住人を作るときの注意点になる。日本の行動分布との距離を必ず測るべき根拠になる
- 既出: 新規
- 出典: https://arxiv.org/abs/2306.16388

#### Hewitt / Ashokkumar / Willer — 社会科学実験の結果予測
- 種別: 研究室(所属研究室名は未確認)
- 中心人物: Luke Hewitt, Ashwini Ashokkumar(共同筆頭)、Isaias Ghezae, Robb Willer
- 代表的な成果: 「Large language models can predict the results of social science experiments」Nature 2026(プレプリントは OSF/PsyArXiv)。サーベイ実験では予測効果量と実際の効果量が r=.85。大規模メガスタディ(フィールド実験を含む)では r=.34 で、専門家予測(r=.26)と同程度
- 窓口・発信: デモ https://www.treatmenteffect.app
- 活動状況: 2026年に Nature で出版
- 渋谷シムへの使いどころ: (6) 「サーベイ実験では高精度でも、フィールド実験では精度が大きく落ちる」という差は、渋谷シム(フィールドに相当)の accuracy 目標を現実的に置く根拠になる。「介入(新店舗・イベント)による人流の差」を効果量として予測・検証する枠組みは、出店検討の顧客向けの検証設計にそのまま使える
- 既出: 新規(arXiv ID なし)
- 出典: https://www.treatmenteffect.app

#### Twin-2K-500(Columbia Business School: Olivier Toubia ほか)
- 種別: 研究室
- 中心人物: Olivier Toubia, George Z. Gui, Tianyi Peng, Daniel J. Merlau, Ang Li, Haozhe Chen
- 代表的な成果: 「Twin-2K-500: A dataset for building digital twins of over 2,000 people based on their answers to over 500 questions」arXiv 2505.17479。米国 2,058 人 × 500 問 × 4 波。最終波で再回答させて test-retest の基準線を用意
- 窓口・発信: arXiv のみ確認。データの配布 URL は未確認
- 活動状況: 2025年公開
- 渋谷シムへの使いどころ: (6)(4) 「同じ人に時間をおいて再回答させる波」を含むので、「人間自身のゆらぎ」を上限として精度を正規化する手法の練習台になる。渋谷シムの複数日ランでも「同一エージェントの日ごとの行動のゆらぎ」と人間のゆらぎを比べる設計が考えられる
- 既出: 新規
- 出典: https://arxiv.org/abs/2505.17479

#### SimBench(Tiancheng Hu / Nigel Collier / Dirk Hovy / Paul Röttger ほか)
- 種別: 研究室(Cambridge LTL、Bocconi MilaNLP などの共同。所属は論文ページで未確認)
- 中心人物: Tiancheng Hu, Joachim Baumann, Lorenzo Lupo, Nigel Collier, Dirk Hovy, Paul Röttger
- 代表的な成果: 「SimBench: Benchmarking the Ability of Large Language Models to Simulate Human Behaviors」arXiv 2510.17516。20データセットを統合。最良モデルでも 40.8/100。規模で伸びるが推論時計算では伸びない。指示調整は「意見が割れる質問」で逆効果。特定の属性グループの再現が最も苦手
- 窓口・発信: arXiv のみ確認
- 活動状況: v4 まで改訂(2025〜2026年)
- 渋谷シムへの使いどころ: (6)(5) 「推論時計算(思考を長くする)は人間らしさの再現に効かず、モデル規模は効く」という知見は、System 2α/2β への予算配分(長い思考より大きめのモデルを短く)を決める判断材料になる
- 既出: 新規
- 出典: https://arxiv.org/abs/2510.17516

#### Be.FM(行動の基盤モデル)
- 種別: 研究室(所属は未確認)
- 中心人物: 未確認(取得したページに著者一覧がなかった)
- 代表的な成果: Be.FM、arXiv 2505.23058。Llama 3.1 8B/70B を、行動科学文献(American Economic Review)、MobLab の経済ゲーム実験データ、Big Five 調査で SFT/LoRA 微調整。経済ゲームの行動分布がベースモデルや商用モデルより人間に近い
- 窓口・発信: 未確認
- 活動状況: 2025年公開。今後 RL とデータ追加を予定
- 渋谷シムへの使いどころ: (5)(6) Centaur と並ぶ「人間行動に寄せた 8B 級オープンモデル」の候補。8B で 39万体を回している現状のモデルの差し替え候補として、比較実験の対象にできる
- 既出: 新規
- 出典: https://arxiv.org/abs/2505.23058

#### SimulateBench(believability ベンチマーク)
- 種別: 研究室(所属は arXiv ページで未確認。著者に Pengfei Liu, Wenjie Li)
- 中心人物: Yang Xiao, Yi Cheng, Jinlan Fu, Jiashuo Wang, Wenjie Li, Pengfei Liu
- 代表的な成果: 「How Far Are LLMs from Believable AI? A Benchmark for Evaluating the Believability of Human Behavior Simulation」arXiv 2312.17115。believability を「一貫性(プロフィールと矛盾しない)」と「頑健性(入力を揺らしても行動が安定)」の2つに分解。65人のプロフィール・8,400問
- 窓口・発信: arXiv のみ確認
- 活動状況: v2(2024年6月)
- 渋谷シムへの使いどころ: (6)(4) believability 軸を「一貫性」と「頑健性」に分けて測る枠組みは、そのまま渋谷シムの believability 評価表になる。複数日ランでのペルソナドリフトは「一貫性」の時間方向の劣化として測れる
- 既出: 新規
- 出典: https://arxiv.org/abs/2312.17115

#### TinyTroupe(Microsoft)
- 重複のため「企業」タブの同名項目にまとめた

### B. 批判・頑健性監査・分散崩壊(variance collapse)

#### M. J. Crockett & Lisa Messeri(Yale)
- 種別: 個人(研究者)
- 中心人物: Molly J. Crockett(心理学)、Lisa Messeri(人類学)
- 代表的な成果: 「AI Surrogates and illusions of generalizability in cognitive science」Trends in Cognitive Sciences 2025(DOI 10.1016/j.tics.2025.09.012)。「AI で人間参加者を代替すれば多様な集団を扱える」という主張は、かえって「一般化できているという錯覚」を生むと批判
- 窓口・発信: ポッドキャスト Many Minds「Science, AI, and illusions of understanding」https://manyminds.libsyn.com/science-ai-and-illusions-of-understanding
- 活動状況: 2025年に論文。2026年の動向は未確認
- 渋谷シムへの使いどころ: (6)(8) 行政・再開発の顧客に出すとき、「シムで当たった」ことの射程(どこまで一般化してよいか)を明記する根拠。未踏の審査で想定される批判への備えにもなる
- 既出: 新規
- 出典: https://collaborate.princeton.edu/en/publications/ai-surrogates-and-illusions-of-generalizability-in-cognitive-scie/ , https://manyminds.libsyn.com/science-ai-and-illusions-of-understanding

#### 「The Illusion of Artificial Inclusion」(Google Research 掲載論文)
- 種別: 研究室
- 中心人物: 未確認(Google Research の論文ページに掲載。著者名は今回取得したページで確認できず)
- 代表的な成果: 「The illusion of artificial inclusion」arXiv 2401.08572。人間参加者を LLM で置き換える提案は、参加型研究の価値(当事者の代表・包摂)を損なうと論じる
- 窓口・発信: https://research.google/pubs/the-illusion-of-artificial-inclusion/
- 活動状況: 2024年発表
- 渋谷シムへの使いどころ: (6)(8) 「住民の声をシムで代替する」と受け取られないよう、行政向けには「実地調査を置き換えるのではなく、調査の前に絞り込む道具」と位置づける根拠
- 既出: 新規
- 出典: https://arxiv.org/html/2401.08572v3 , https://research.google/pubs/the-illusion-of-artificial-inclusion/

#### Wang / Morgenstern / Dickerson(identity group の flattening)
- 種別: 研究室
- 中心人物: Angelina Wang, Jamie Morgenstern, John P. Dickerson
- 代表的な成果: 「Large language models that replace human participants can harmfully misportray and flatten identity groups」arXiv 2402.01908(掲載誌は今回未確認)
- 窓口・発信: 未確認
- 活動状況: 2024年公開。2025〜2026年の分散崩壊研究から引用されている
- 渋谷シムへの使いどころ: (6) 「属性ラベルだけで作ったエージェントは、グループ内の多様性が潰れる」。渋谷シムでペルソナを国勢調査の属性から作っている部分について、グループ内の分散を必ず測るべき根拠
- 既出: 既出(論文)
- 出典: https://arxiv.org/pdf/2402.01908

#### 「Consensus collapse」— Rojin Ziaei
- 種別: 個人(研究者、所属は未確認)
- 中心人物: Rojin Ziaei
- 代表的な成果: 「The Limits of Simulated Societies: How Post-Training and Survey Fine-Tuning Erase Cross-Cultural Variance」arXiv 2609.25760(2026年9月22日)。12か国の World Values Survey 1万組で、11モデル+微調整5モデルを比較。アライメント後の学習で「グループごとにステレオタイプ1つに収束する」consensus collapse が起き、SFT で分散の約半分が失われる。温度を上げても GRPO でも回復しない
- 窓口・発信: arXiv のみ
- 活動状況: 2026年9月の新着
- 渋谷シムへの使いどころ: (6)(1)(2) 「精度(平均)だけでなく、人間の分散をどれだけ保てたか」を2本目の指標に入れるべき直接の根拠。渋谷シムの「空腹で全員同じ時刻に動く」「会話が起きない」は、分散崩壊の症状として整理できる。温度調整では直らないという知見も重要
- 既出: 新規
- 出典: https://arxiv.org/abs/2609.25760

#### Murthy / Ullman / Hu(アライメントが概念多様性を減らす)
- 種別: 研究室
- 中心人物: Sonia K. Murthy, Tomer Ullman, Jennifer Hu
- 代表的な成果: 「One fish, two fish, but not the whole sea: Alignment reduces language models' conceptual diversity」arXiv 2411.04427。個体内のゆらぎと集団全体のゆらぎを比べる方法を提案。どのモデルも人間レベルの多様性に届かず、アライメント済みモデルのほうが多様性が低い
- 窓口・発信: arXiv のみ確認
- 活動状況: v3 まで改訂
- 渋谷シムへの使いどころ: (6)(5) 「1体のエージェント内のばらつき」と「集団全体のばらつき」を分けて測る手法は、39万体を少数のペルソナ型から複製している場合の診断に使える。指示調整前のベースモデルを System 1.5 に使う選択肢の根拠にもなる
- 既出: 新規
- 出典: https://arxiv.org/abs/2411.04427

#### Jamie Cummins(analytic flexibility)
- 種別: 個人(研究者、所属は未確認)
- 中心人物: Jamie Cummins
- 代表的な成果: 「The threat of analytic flexibility in using large language models to simulate human data」arXiv 2509.13397。252通りの設定を比べると、順位の再現・分布の一致・尺度間相関の再現がそれぞれ別の設定で最良になる。Argyle et al. の Study 3 を 66 通りで再分析すると、人間との相関が r=.23〜.84 まで振れる
- 窓口・発信: arXiv のみ
- 活動状況: 2025年9月
- 渋谷シムへの使いどころ: (6) 「良い設定を選んでから当たったと言う」ことの危うさ。holdout 照合では、設定(モデル・温度・プロンプト)を照合前に固定して記録する事前登録型の運用にすべき根拠
- 既出: 新規
- 出典: https://arxiv.org/abs/2509.13397

#### Jinyi Ye / Emilio Ferrara(USC ISI)— robustness audit / TRAILS
- 種別: 研究室
- 中心人物: Jinyi Ye, Lei Cao, Ding Chen, Emilio Ferrara
- 代表的な成果: 「Stop Drawing Scientific Claims from LLM Social Simulations Without Robustness Audits」arXiv 2605.18890。囚人のジレンマで、ペルソナの書式や指示の言い回しを少し変えるだけで協力率が最大 76 ポイント動く。頑健性監査の分類 TRAILS を提案
- 窓口・発信: https://www.isi.edu/results/publications/66808/stop-drawing-scientific-claims-from-llm-social-simulations-without-robustness-audits
- 活動状況: 2026年
- 渋谷シムへの使いどころ: (6) TRAILS の分類を、渋谷シムの「結論ごと・モデルごとの頑健性チェックリスト」として使える。8B を別モデルに替えたときに結論が変わるかを必ず報告する
- 既出: 既出(論文)。研究室としては新規
- 出典: https://www.isi.edu/results/publications/66808/stop-drawing-scientific-claims-from-llm-social-simulations-without-robustness-audits

#### Gao / Lee / Burtch / Fazelpour(Scylla Ex Machina)
- 種別: 個人(研究者)
- 中心人物: Yuan Gao, Dokyun Lee, Gordon Burtch, Sina Fazelpour
- 代表的な成果: 「Take Caution in Using LLMs as Human Surrogates: Scylla Ex Machina」arXiv 2410.19599。11-20 money request game で、高度な手法を含め多くのモデルが人間の行動分布を再現できない。失敗の原因は入力言語・役割指定・安全対策などにばらばらに依存し、予測しにくい
- 窓口・発信: arXiv のみ
- 活動状況: v3(2025年1月)
- 渋谷シムへの使いどころ: (6) 「言語(日本語/英語)を変えると再現性が変わる」ので、日本語プロンプトと英語プロンプトの両方で同じ holdout 照合をして差を見る、という検証項目の根拠
- 既出: 新規
- 出典: https://arxiv.org/abs/2410.19599

#### Huang / Wu / Wang(「LLM は何人分の回答者に相当するか」)
- 種別: 研究室(所属は未確認)
- 中心人物: Chengpiao Huang, Yuhang Wu, Kaizheng Wang
- 代表的な成果: 「How Many Human Survey Respondents is a Large Language Model Worth? An Uncertainty Quantification Perspective」arXiv 2502.17773。シミュレーション回答から、人間母集団の値に対する信頼集合を作る。シミュレーション数を多くしすぎると信頼区間が狭くなりすぎる問題を、データ駆動で適切な数を選ぶことで解決。選ばれた数が「LLM が代表できる実効人数」になる
- 窓口・発信: arXiv のみ
- 活動状況: 2025年
- 渋谷シムへの使いどころ: (6)(5) 39万体を回しても「実効的には何人分の情報か」は別問題、という見方を与える。アンサンブル予測の区間幅を過信しないための補正方法として使える。GPU 予算を削る根拠にもなる
- 既出: 新規
- 出典: https://arxiv.org/abs/2502.17773

#### 少量の人間データでの微調整・較正(Wang / Hunt / Tang / Joseph と Choi ほか)
- 種別: 研究室(所属は未確認)
- 中心人物: Steven Wang, Kyle Hunt, Shaojie Tang, Kenneth Joseph / Eun Cheol Choi, Youngrae Kim ほか
- 代表的な成果: 「Can Finetuing LLMs on Small Human Samples Increase Heterogeneity, Alignment, and Belief-Action Coherence?」arXiv 2511.21218(改善はするが、回帰係数までは再現できない)/「Beyond the Mean: Three-Axis Fidelity for Aligning LLM-Based Survey Simulators from Small Pilot Data」arXiv 2606.28963(構造・周辺分布・個人の3軸で評価。少量パイロットでの微調整が最もバランスが良いが、サブグループごとに差がある)
- 窓口・発信: arXiv のみ
- 活動状況: 2025年11月、2026年6月
- 渋谷シムへの使いどころ: (3)(6) 小さな実データ(例: 渋谷での小規模アンケートや PT 調査の一部)で System 1.5 を微調整し、残りで検証するという較正の方針を支える。評価を「構造(関係)・周辺分布(時刻別人数)・個人(個票)」の3軸に分ける考え方は、0/4 NOT PASS の原因の切り分けに使える
- 既出: 新規
- 出典: https://arxiv.org/abs/2511.21218 , https://arxiv.org/abs/2606.28963

---

### C. ペルソナの安定性・ドリフト・activation steering

#### Persona Vectors(Anthropic Fellows / safety-research)
- 種別: 企業(研究プログラム)
- 中心人物: Anthropic Fellows Program の参加者が主導(ページに個人名の記載なし)
- 代表的な成果: 「Persona vectors: Monitoring and controlling character traits in language models」arXiv 2507.21509。コード https://github.com/safety-research/persona_vectors (Apache-2.0、例は Qwen2.5-7B-Instruct)。特性(悪意・迎合・幻覚など)ごとに、出る/出ないときの活性化の平均差からベクトルを作り、監視と制御に使う。応答の前に活性化が現れるので、ペルソナの変化を事前に検知できる
- 窓口・発信: https://www.anthropic.com/research/persona-vectors / Anthropic Fellows 募集 https://alignment.anthropic.com/2025/anthropic-fellows-program-2026/
- 活動状況: 2025年8月公開。Fellows Program は 2026年も募集
- 渋谷シムへの使いどころ: (4)(2) オープンな 7〜8B モデルなら、「社交性」「せっかちさ」などの性格特性を persona vector として取り出し、プロンプトではなく活性化に足すことでペルソナを固定できる可能性がある。プロンプトが短くなるので prefix 共有と組み合わせやすく、(5) にも効く。複数日ランで各エージェントの特性ベクトルへの射影を記録すれば、ドリフトを数値で監視できる
- 既出: 既出(論文 2507.21509)。リポジトリは新規
- 出典: https://www.anthropic.com/research/persona-vectors , https://github.com/safety-research/persona_vectors

#### The Assistant Axis(Anthropic / MATS / Oxford: Christina Lu, Jack Lindsey ほか)
- 種別: 企業(研究チーム)
- 中心人物: Christina Lu, Jack Gallagher, Jonathan Michala, Kyle Fish, Jack Lindsey
- 代表的な成果: 「The Assistant Axis: Situating and Stabilizing the Default Persona of Language Models」arXiv 2601.10387(2026年1月)。Gemma 2 / Qwen 3 / Llama 3.3 で 275 の役割を調べ、「アシスタントらしさ」の主軸を特定。セラピー風・AI の意識をめぐる哲学的な会話で、ペルソナが少しずつドリフトする。活性化をこの軸の正常範囲に抑える activation capping で、有害な応答を約60%減らした
- 窓口・発信: Neuronpedia にデモ(Assistant Axis ツール)https://www.neuronpedia.org/
- 活動状況: 2026年1月公開
- 渋谷シムへの使いどころ: (4)(2) 渋谷シムでは逆向きの問題が起きている(住人がアシスタント口調に引き戻されて会話の中身が薄くなる)。この軸から離す方向にステアリングすると「アシスタント臭さ」を抜ける可能性がある。複数日ランで、軸上の位置を「住人らしさの劣化」の監視指標として記録できる
- 既出: 新規
- 出典: https://arxiv.org/abs/2601.10387 , https://the-decoder.com/anthropic-study-finds-that-role-prompts-can-push-ai-chatbots-out-of-their-trained-helper-identity/

#### Kenneth Li ほか(persona drift の測定と制御)
- 種別: 個人(研究者、Harvard)
- 中心人物: Kenneth Li ほか(論文ページは Harvard VCG に掲載。共著者の全員と現所属は未確認)
- 代表的な成果: 「Measuring and Controlling Persona Drift in Language Model Dialogs」arXiv 2402.10962(COLM 2024)。コード https://github.com/likenneth/persona_drift 。原因を「システムプロンプトへの注意の減衰」とし、軽量な対策 split-softmax を提案
- 窓口・発信: Harvard VCG の論文ページ https://vcg.seas.harvard.edu/publications/measuring-and-controlling-persona-drift-in-language-model-dialogs
- 活動状況: リポジトリは2コミットのみで、更新は止まっている模様
- 渋谷シムへの使いどころ: (4) 「長い対話の後半で、システムプロンプトに書いたペルソナが効かなくなる」測定手順(2体の LLM に自己対話させ、ターンごとにペルソナ順守度を測る)は、渋谷シムの会話・日をまたぐ記憶付与後のドリフト評価にそのまま使える
- 既出: 既出(論文 2402.10962)
- 出典: https://github.com/likenneth/persona_drift , https://vcg.seas.harvard.edu/publications/measuring-and-controlling-persona-drift-in-language-model-dialogs

#### Anthropic Alignment Science Blog
- 種別: ブログ
- 中心人物: Anthropic Alignment Science チーム
- 代表的な成果: 「The Persona Selection Model: Why AI Assistants might Behave like Humans」(2026年2月)、「Abstractive Red-Teaming of Language Model Character」(2026年3月)、「Subliminal Learning」(2025年7月)、「Activation Oracles」(2025年12月)
- 窓口・発信: https://alignment.anthropic.com/
- 活動状況: 2026年8月にも投稿あり
- 渋谷シムへの使いどころ: (4) 「LLM は物語の登場人物を演じている」と捉える Persona Selection Model は、住人ペルソナがなぜ崩れるか(どの文脈で別人格が選ばれるか)を考える理論の枠組みになる。Abstractive Red-Teaming は「キャラクターが崩れる問いかけの種類を自動で探す」手法で、住人ペルソナの崩れる条件を洗い出す自動テストに応用できる
- 既出: 新規
- 出典: https://alignment.anthropic.com/

#### Neuronpedia(Johnny Lin)
- 種別: OSSコミュニティ
- 中心人物: Johnny Lin(作者)。支援: Decode Research, Open Philanthropy, Long Term Future Fund, Anthropic, Manifund など
- 代表的な成果: オープンソースの解釈可能性プラットフォーム https://github.com/hijohnnylin/neuronpedia 。Steer(潜在特徴・任意ベクトルによる活性化ステアリング)、SAE 特徴の検索、Assistant Axis ツール、Circuit Tracer、Gemma Scope 2
- 窓口・発信: https://www.neuronpedia.org/ / X https://twitter.com/neuronpedia / Slack「opensourcemechanistic」(招待リンクはサイト経由、URL は未確認)
- 活動状況: 2026年時点で Assistant Axis 等の新ツールを追加
- 渋谷シムへの使いどころ: (4)(2) コードを書く前に、ブラウザ上で「どの特徴を足すと住人の口調・社交性が変わるか」を試せる。persona steering を本採用するかの事前調査に最適
- 既出: 新規
- 出典: https://www.neuronpedia.org/

#### Transluce
- 種別: その他(非営利研究機関)
- 中心人物: Jacob Steinhardt(UC Berkeley)、Sarah Schwettmann(元 MIT CSAIL)
- 代表的な成果: Docent(エージェントの大量の実行ログを分析する道具)https://transluce.org/docent 、Behavior Reports https://behaviors.transluce.org 、Investigator(解釈可能性ツール)
- 窓口・発信: https://transluce.org / Docent ブログ https://transluce.org/docent/blog / X https://x.com/TransluceAI / GitHub https://github.com/TransluceAI/
- 活動状況: 2026年9月30日まで投稿が続く(政府サイトを狙った AI エージェントの調査、メンタルヘルス評価など)。Open Philanthropy などの寄付で運営
- 渋谷シムへの使いどころ: (6)(2) Docent は「大量のエージェントログから、おかしな振る舞いのパターンを LLM で要約・検索する」道具。39万体×1日のログから「会話が起きなかった場面」「空腹で行動が決まった場面」を抽出して分類するという、believability の定性分析を効率化できる
- 既出: 新規
- 出典: https://transluce.org , https://nextomoro.com/transluce/

#### Activation Addition(Alex Turner ほか)
- 種別: 個人(研究者)
- 中心人物: Alex Turner(TurnTrout)、Monte MacDiarmid, David Udell, Lisa Thiergart, Ulisse Mini
- 代表的な成果: 「Steering GPT-2-XL by adding an activation vector」(AI Alignment Forum、2023年5月13日)。対になるプロンプトの活性化の差(例: Love − Hate)を足すだけで出力を誘導する手法で、最適化が不要。persona vectors の源流
- 窓口・発信: https://www.alignmentforum.org/posts/5spBue2z2tw4JuDCx/steering-gpt-2-xl-by-adding-an-activation-vector
- 活動状況: 2023年の古典
- 渋谷シムへの使いどころ: (4)(5) 最小限の実装で「性格の差」を活性化で入れる最初の実験に向いている(学習不要、vLLM のカスタムフックで足せる)
- 既出: 新規
- 出典: https://www.alignmentforum.org/posts/5spBue2z2tw4JuDCx/steering-gpt-2-xl-by-adding-an-activation-vector

---

### D. Generative Agents の記憶設計の後継(メモリ層の会社・OSS)

#### Letta(旧 MemGPT)
- 種別: スタートアップ / OSSコミュニティ
- 中心人物: Charles Packer(共同創業者)、Sarah Wooders(sleep-time 論文の共著者。MemGPT は UC Berkeley の研究プロジェクトとして始まった)
- 代表的な成果: MemGPT arXiv 2310.08560。「Sleep-time Compute」arXiv 2504.13171(Lin, Snell, Wang, Packer, Wooders, Stoica, Gonzalez。ユーザーが問いかける前のオフライン時間に文脈を前処理し、回答時の計算を約5分の1に削減)。https://github.com/letta-ai/letta (約25.1k stars、旧 V1 サーバーは archive 化)→ 現行は letta-code
- 窓口・発信: ブログ https://www.letta.com/blog/ / Discord https://discord.gg/letta / X https://x.com/letta_ai / GitHub https://github.com/letta-ai
- 活動状況: 2026年9月15日に letta-code v0.32.11。記憶を git 管理の Markdown ファイル(MemFS)として持ち、`/sleeptime` で設定する背景の振り返り「Dreaming」を実装。資金調達の詳細は今回確認できず
- 渋谷シムへの使いどころ: (4)(5) 「夜のあいだに記憶を整理(要約・統合)して翌日の文脈を短くする」sleep-time の発想は、渋谷シムの複数日ランにそのまま合う。夜間(人流が少ない時間帯)に GPU を回して全エージェントの記憶を圧縮すれば、昼のピーク時の推論コストを下げられる。記憶を「常にプロンプトに入れる core」と「必要時に読む archival」に分ける設計も参考になる
- 既出: 既出(論文 2310.08560, 2504.13171)。会社・コミュニティは新規
- 出典: https://letta.com/blog/memgpt-and-letta , https://github.com/letta-ai/letta , https://rywalker.com/research/letta , https://arxiv.org/abs/2504.13171

#### Mem0
- 種別: スタートアップ / OSSコミュニティ
- 中心人物: Taranjeet Singh(CEO)、Deshraj Yadav(論文共著)
- 代表的な成果: https://github.com/mem0ai/mem0 (2026年時点でサイト表示 約62.6k stars)。「Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory」arXiv 2504.19413(LOCOMO で OpenAI 比 26% の相対改善、全文脈方式に比べ p95 遅延 91% 減・トークン 90% 以上減)
- 窓口・発信: https://mem0.ai / Discord https://discord.com/invite/skNhacB39h / X https://x.com/mem0ai
- 活動状況: 2025年10月28日に Seed+Series A 合計 $24M(Seed は Kindred Ventures、Series A は Basis Set Ventures がリード。Peak XV, GitHub Fund, YC が参加)
- 渋谷シムへの使いどころ: (4)(5) 「会話から事実を抽出して追加・更新・削除する」記憶の書き込み方式は、エージェント間の関係(誰と会ったか・印象)を日をまたいで保つ最小構成になる。全文脈方式よりトークンを9割減らせるという数値は、39万体規模で記憶を持たせるときの予算見積もりに使える
- 既出: 新規
- 出典: https://mem0.ai/series-a , https://arxiv.org/abs/2504.19413

#### Zep / Graphiti
- 種別: スタートアップ / OSSコミュニティ
- 中心人物: 未確認(公式ページに創業者名の記載なし)
- 代表的な成果: Graphiti https://github.com/getzep/graphiti (約29k stars、時間情報つき知識グラフ)。「Zep: A Temporal Knowledge Graph Architecture for Agent Memory」arXiv 2501.13956
- 窓口・発信: https://www.getzep.com/ / ブログ https://www.getzep.com/blog/ / X https://x.com/zep_ai / Discord https://discord.com/invite/W8Kw6bsgXQ (#graphiti)
- 活動状況: 2026年6月8日に Graphiti v0.29.2。2026年は「Context Lake」「Konig」(グラフ DB サービス)などの企業向け製品に拡大。451 Research のレポート(2026年4月)あり。公称値は LoCoMo 94.7%、LongMemEval 90.2%
- 渋谷シムへの使いどころ: (4) 「関係がいつ成り立ち、いつ無効になったか」を辺に持つ二時間(bi-temporal)グラフは、渋谷シムの人間関係(知り合った日・最後に会った日・関係の変化)を表すデータ構造としてそのまま使える。39万体分の LLM 抽出は重いので、構造だけを借りてルールで書き込むのが現実的
- 既出: 新規
- 出典: https://github.com/getzep/graphiti , https://www.getzep.com/ , https://arxiv.org/abs/2501.13956

#### Cognee
- 種別: スタートアップ / OSSコミュニティ
- 中心人物: Vasilije Markovic(創業者・CEO、ベルリン)
- 代表的な成果: https://github.com/topoteretes/cognee (OSS のメモリエンジン。関係 DB・ベクトル・グラフを一体化した知識グラフ)
- 窓口・発信: https://www.cognee.ai / ブログ https://www.cognee.ai/blog/fundamentals/how-cognee-builds-ai-memory / Discord https://discord.gg/m63hxKsp4p / X https://x.com/cognee_ / AI Engineer 講演者ページ https://www.ai.engineer/speakers/vasilije-markovic
- 活動状況: 2026年2月19日に Seed $7.5M(Pebblebed リード、42CAP, Vermilion Ventures が参加)
- 渋谷シムへの使いどころ: (4) 「フィードバックで記憶グラフを改良する」仕組みは、住人が場所(店・広場)について持つ印象を、訪問経験で更新する設計の参考になる。Discord が比較的小規模で、質問しやすい
- 既出: 新規
- 出典: https://www.cognee.ai/cognee-raises-seven-million-five-hundred-thousand-dollars-seed

#### LangMem(LangChain)
- 種別: OSSコミュニティ / 企業
- 中心人物: LangChain チーム(個人名は未確認)
- 代表的な成果: LangMem SDK(2025年2月18日リリース)。記憶を semantic(事実)/ episodic(過去の経験、few-shot 例)/ procedural(行動のルール、プロンプト自体の更新)の3種に分ける。`create_memory_manager`、`create_prompt_optimizer`
- 窓口・発信: ブログ https://www.langchain.com/blog/langmem-sdk-launch / ドキュメント https://langchain-ai.github.io/langmem/
- 活動状況: 2025年リリース。2026年の更新は未確認
- 渋谷シムへの使いどころ: (4)(1) procedural memory(経験から行動ルールを書き換える)は、System 1(習慣・コード)を経験から更新する仕組みとして対応がとれる。例: 「この店は昼に混む」と学んだ住人が、翌日から昼食時刻をずらす
- 既出: 新規
- 出典: https://www.langchain.com/blog/langmem-sdk-launch

#### AGI Research(Rutgers: Yongfeng Zhang)— AIOS / A-MEM
- 種別: 研究室 / OSSコミュニティ
- 中心人物: Yongfeng Zhang(Rutgers)、Kai Mei, Wujiang Xu, Xi Zhu ほか
- 代表的な成果: 「AIOS: LLM Agent Operating System」arXiv 2403.16971(COLM 2025)https://github.com/agiresearch/AIOS (約6.4k stars)。LLM 呼び出しのスケジューリング・文脈切り替え・記憶管理を OS のように扱う。「A-MEM: Agentic Memory for LLM Agents」arXiv 2502.12110 https://github.com/agiresearch/A-mem (約1.1k stars、Zettelkasten 式に記憶同士をつなぎ、新しい記憶で古い記憶のタグを更新)
- 窓口・発信: Discord https://discord.gg/B2HFxEgTJX / GitHub https://github.com/agiresearch
- 活動状況: README 上の最新ニュースは 2025年7月(COLM 採択、Berkeley RDI AgentX 決勝)。2026年の新着は確認できず
- 渋谷シムへの使いどころ: (5) 多数のエージェントの LLM 呼び出しを、カーネルがキュー管理・スケジューリングする設計は、System 2α/2β の呼び出しを優先度つきで捌く「推論スケジューラ」の参考になる。(4) A-MEM の「記憶の進化(新しい記憶が古い記憶の意味づけを書き換える)」は関係の持続に使える
- 既出: 新規
- 出典: https://github.com/agiresearch/AIOS , https://github.com/agiresearch/A-mem

#### LoCoMo(Snap Research / UNC / USC)
- 種別: 研究室 / 企業
- 中心人物: Adyasha Maharana, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, Yuwei Fang
- 代表的な成果: 「Evaluating Very Long-Term Conversational Memory of LLM Agents」arXiv 2402.17753。https://github.com/snap-research/LoCoMo 。長期会話記憶のベンチマーク(単一ホップ・複数ホップ・時間・常識・敵対的質問)。Mem0・Zep などが成績を競う共通指標になっている
- 窓口・発信: https://snap-research.github.io/locomo/
- 活動状況: 2024年公開。2026年も記憶製品の比較基準として使われている
- 渋谷シムへの使いどころ: (4) 渋谷シムの複数日ランで「3日前に会った人を覚えているか」「時間の前後を正しく扱えるか」を測る質問セットを作るときの型
- 既出: 新規
- 出典: https://snap-research.github.io/locomo/ , https://arxiv.org/abs/2402.17753

#### LongMemEval(Di Wu ほか)
- 種別: 研究室
- 中心人物: Di Wu, Hongwei Wang, Wenhao Yu, Yuwei Zhang, Kai-Wei Chang, Dong Yu
- 代表的な成果: 「LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory」arXiv 2410.10813。https://github.com/xiaowu0162/LongMemEval 。5能力(抽出・セッション横断推論・時間推論・知識更新・回答保留)。記憶設計を「索引・検索・読み出し」の3段階に分解
- 窓口・発信: GitHub(上記)
- 活動状況: Zep などが 2026年も公称値を出す指標
- 渋谷シムへの使いどころ: (4) 「知識更新(店が閉店した、友人が引っ越した)」と「回答保留(知らないことは知らないと言う)」の評価は、住人が古い情報で行動し続けるという不自然さの検出に効く
- 既出: 新規
- 出典: https://arxiv.org/abs/2410.10813

---

### E. 大規模エージェント推論の効率化

#### vLLM / Inferact
- 種別: OSSコミュニティ / スタートアップ
- 中心人物: Woosuk Kwon(Inferact 共同創業者)、Ion Stoica(UC Berkeley Sky Computing Lab、Databricks 共同創業者)
- 代表的な成果: https://github.com/vllm-project/vllm (PagedAttention、自動 prefix caching)
- 窓口・発信: Slack https://slack.vllm.ai / フォーラム https://discuss.vllm.ai / X https://x.com/vllm_project / ブログ https://blog.vllm.ai/ / イベント https://vllm.ai/events / Inferact https://inferact.ai/
- 活動状況: 2026年1月22日に Inferact が Seed $150M(評価額 $800M、a16z と Lightspeed がリード)で vLLM の商用化を開始。コントリビューターは 2,000 人超
- 渋谷シムへの使いどころ: (5) すでに使用中と思われる。Slack の #performance 系チャンネルや Meetup で「数十万の短いリクエストを、共通の長いプレフィックスつきで流す」という渋谷シム特有の負荷を相談できる。ペルソナ・世界状態の共通部分をプロンプト先頭に固定する設計にすると、prefix caching が効く
- 既出: 既出(GitHub)。Inferact・コミュニティ窓口は新規
- 出典: https://github.com/vllm-project/vllm , https://siliconangle.com/2026/01/22/inferact-launches-150m-funding-commercialize-vllm/

#### SGLang / RadixArk(LMSYS 発)
- 種別: OSSコミュニティ / スタートアップ
- 中心人物: SGLang コアチーム(Ying Sheng, Banghua Zhu などとされる。RadixArk の経営陣は未確認)
- 代表的な成果: https://github.com/sgl-project/sglang (約31.7k stars)。RadixAttention(基数木による KV キャッシュ共有で、共通プレフィックスを持つ大量リクエストに強い)
- 窓口・発信: Slack https://slack.sglang.io/ / ブログ https://lmsys.org/blog/ / 週次コミュニティコール(リンクは未確認)
- 活動状況: 2026年5月に RadixArk が Seed $100M(評価額 $400M、Accel リード、Spark Capital 共同リード。NVentures, AMD, MediaTek が参加)。2026年7月に Google と TPU 対応、Kimi K3 に初日対応、DFlash などの投機的デコーディング
- 渋谷シムへの使いどころ: (5) 「同じ世界状態プレフィックス+エージェントごとの短い差分」という渋谷シムの呼び出しパターンは RadixAttention が最も得意とする形。構造化出力(JSON 制約デコード)も速いので、System 2α の行動選択出力を制約付きで生成すると、パース失敗の再試行がなくなる。vLLM との比較ベンチを取る価値がある
- 既出: 新規
- 出典: https://github.com/sgl-project/sglang , https://nextomoro.com/sglang/

#### EcoLANG(Zhongyu Wei ほか)
- 種別: 研究室
- 中心人物: Xinyi Mou, Chen Qian, Wei Liu, Xuanjing Huang, Zhongyu Wei(所属は arXiv ページで未確認)
- 代表的な成果: 「EcoLANG: Efficient and Effective Agent Communication Language Induction for Social Simulation」arXiv 2505.06904。同義語の除去と文レベル規則の進化で、エージェント間のやりとり用の言語を作り、シミュレーション精度を落とさずにトークンを 20% 以上削減
- 窓口・発信: arXiv のみ確認
- 活動状況: 2025年
- 渋谷シムへの使いどころ: (5)(2) 会話量を増やす(2)と推論コスト(5)が衝突するところで、「会話の中身(意味)は保ちつつ、エージェント間の内部表現だけ圧縮する」という逃げ道を示している。人に見せる会話ログは別途デコードする、という二段構えが考えられる
- 既出: 新規
- 出典: https://arxiv.org/abs/2505.06904

#### Inference-Time Distillation(Stanford: Kayvon Fatahalian 研究室)
- 種別: 研究室
- 中心人物: Vishnu Sarukkai, Asanshay Gupta, James Hong, Michaël Gharbi, Kayvon Fatahalian
- 代表的な成果: 「Inference-Time Distillation: Cost-Efficient Agents Without Fine-Tuning or Manual Prompt Engineering」arXiv 2512.02543。大モデル(教師)が一部の課題で作った実演を、小モデル(生徒)が検索して in-context で使う。生徒の複数サンプルが一致すれば採用し、割れたら教師に回すカスケード。ALFWorld で教師と同精度のまま約2.5倍安い
- 窓口・発信: arXiv のみ確認
- 活動状況: 2025年12月
- 渋谷シムへの使いどころ: (5) 渋谷シムの System 2α(小)→2β(大)の振り分けを「生徒の自己一致度」で決めるという具体的な基準を与える。学習なしで実装できるので、GPU が戻ったらすぐ試せる。大モデルの判断ログを蓄積すれば、そのまま System 1.5 の蒸留データにもなる
- 既出: 新規
- 出典: https://arxiv.org/abs/2512.02543

#### PersonaHub(Tencent AI Lab)
- 種別: 企業(研究チーム)
- 中心人物: Tencent AI Lab(個人名は今回未確認)
- 代表的な成果: 「Scaling Synthetic Data Creation with 1,000,000,000 Personas」arXiv 2406.20094。https://github.com/tencent-ailab/persona-hub (約1.6k stars)。20万件のプレビューと 3.7億件の「elite personas」を公開(2025年2月18日)
- 窓口・発信: GitHub(上記)
- 活動状況: 2025年2月に追加公開
- 渋谷シムへの使いどころ: (4)(6) 国勢調査の属性だけで作ったペルソナが均質化する問題(B 節の flattening)に対し、職業・関心が多様なペルソナ文を大量に借りて、属性に合わせて割り当てる材料になる。ただし英語中心で、日本の分布とは一致しない
- 既出: 新規
- 出典: https://github.com/tencent-ailab/persona-hub

#### Nemotron-Personas-Japan(NVIDIA)
- 種別: 企業
- 中心人物: NVIDIA(個人名は未確認)
- 代表的な成果: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Japan 。日本語の合成ペルソナ 100万件(CC-BY-4.0)。性別・年齢・婚姻・学歴・職業・地域・都道府県と、職業・趣味・文化的背景などの自由記述を含む
- 窓口・発信: Hugging Face(上記)
- 活動状況: 公開日はページで未確認。日本の統計にもとづいて作られたかどうかもページからは確認できず
- 渋谷シムへの使いどころ: (4)(2) 都道府県・年齢・職業で絞り込めるので、渋谷の来街者(居住都道府県の分布)に合わせてペルソナ文を抽出し、エージェントに割り当てられる。会話の中身が薄い問題(2)に対して、話題の種(趣味・関心)を与える材料になる
- 既出: 新規
- 出典: https://huggingface.co/datasets/nvidia/Nemotron-Personas-Japan

---

### F. 会話の自然さ・ターンテイキング

#### MaAI / VAP(京都大学 河原研系: Koji Inoue / KTH: Erik Ekstedt, Gabriel Skantze)
- 種別: 研究室 / OSSコミュニティ
- 中心人物: 井上昂治(Koji Inoue、京都大学。共同研究の窓口)、河原達也(Tatsuya Kawahara)、Erik Ekstedt と Gabriel Skantze(KTH)
- 代表的な成果: Voice Activity Projection(「Voice Activity Projection: Self-supervised Learning of Turn-taking Events」Interspeech 2022, arXiv 2205.09812)https://github.com/ErikEkstedt/VoiceActivityProjection 。リアルタイム版 https://github.com/inokoj/VAP-Realtime (日本語モデル・ERICA データの相槌/うなずきモデルあり)→ 統合先 MaAI https://github.com/MaAI-Kyoto/MaAI (`pip install maai`、英・中・日対応。ターンテイキング・相槌・うなずき予測)
- 窓口・発信: GitHub(上記)。X・Discord は未確認
- 活動状況: VAP-Realtime は MaAI へ統合済みで、いずれアーカイブ予定。MaAI は PyPI で配布中
- 渋谷シムへの使いどころ: (2) 音声前提の研究だが、「誰がいつ話し始めるか・相槌を打つか」を予測モデルで決めるという発想は、渋谷シムの会話の発生(0.07%)を LLM まかせにせず、軽量モデル(System 1.5)で「会話を始める・続ける」を判定する設計の参考になる。将来メタバース(北極星)で音声住人を作るときには直接使える。日本の研究者なので連絡しやすい
- 既出: 新規
- 出典: https://github.com/MaAI-Kyoto/MaAI , https://github.com/inokoj/VAP-Realtime , https://github.com/ErikEkstedt/VoiceActivityProjection

---

### 渋谷シムの検証設計への要約(担当範囲から)

- **accuracy 軸**: (a) 時刻別人流の分布距離(TVD / Wasserstein。Simile・Aaru・OpinionQA 方式)、(b) 分散の保持率(consensus collapse、Murthy ら)、(c) 介入効果量の予測相関(Hewitt/Willer 方式)、(d) 人間自身のゆらぎで正規化(Simile の test-retest、Twin-2K-500)。較正データと検証データを分け、設定を照合前に固定する(Manning/Horton、Cummins)。
- **believability 軸**: 一貫性と頑健性(SimulateBench)、ペルソナ順守と自己一貫性の LLM 判定(TinyTroupe Propositions)、ドリフトの時間変化(Kenneth Li、Assistant Axis)、大量ログの定性分析(Transluce Docent)。
- **頑健性**: モデル・言語・プロンプト書式を入れ替えても結論が保たれるか(Ye/Ferrara TRAILS、Gao ら)。
- **コスト**: プレフィックス共有(SGLang/vLLM)、自己一致度で大小モデルを振り分けるカスケード(Fatahalian)、夜間の記憶圧縮(Letta sleep-time)、人間行動に寄せた小型モデル(Minitaur・Be.FM)。

### 担当範囲で見つからなかった/確認できなかったもの

- 共有の WebSearch 上限(200回)に途中で達したため、後半は一次 URL への WebFetch だけで裏を取った。以下は検索できず未掲載: David Wingate(BYU)の 2026 年の所属と研究室名、Kenneth Li の現所属、Sakana AI の対話・ターンテイキング研究、Anthropic Fellows 以外の activation steering 系コミュニティ(EleutherAI の steering 系 Discord など)、「行動の基盤モデル」を掲げる他の企業、LLM 社会シミュに prefix caching・バッチ推論を適用した専用論文(AI Metropolis 2411.03519 と 1B 規模の 2506.12078 は既出)。
- Be.FM の著者・所属、Twin-2K-500 のデータ配布 URL、Letta の資金調達額、Zep の創業者名、RadixArk の経営陣は、取得できたページに記載がなく未確認。
- genagents リポジトリ(joonspk-research/genagents、1,000人エージェントバンク)は取得エラーで、内容と公開条件を確認できず。
- Expected Parrot の GitHub は 494 stars と確認できたが、リリース日は未確認。


## 6. 日本の研究者・企業・コミュニティ


調査日: 2026-10-13。WebSearch/WebFetch で確認できた範囲のみ記載。確認できない項目は「未確認」。
注: 調査途中で WebSearch の上限(1ターン200回、全エージェント共有)に達したため、後半は公式ページを直接 WebFetch して裏を取った。connpass・JSAI 公式・Zenn 検索は robots 制限でクロールできなかった。

---

### A. 直近の学会・イベント日程(2026-10 以降)早見表

| 日付 | イベント | 場所 | 締切・メモ | 高校生 |
|---|---|---|---|---|
| 2026-10-13〜16 | CEATEC 2026 富士通ブース(ソーシャルデジタルツイン「デジタルリハーサル」展示) | 幕張メッセ ホール6 | 展示のみ | 来場可 |
| 2026-10-17〜21 | AIWolfDial 2026(人狼知能・自然言語部門)/INLG 2026 併催 | オランダ・ユトレヒト | 投稿締切は終了 | — |
| 2026-10-20, 11-17, 12-15, 2027-01-19, 02-16, 03-23(火) | LLM-jp 勉強会(月1回) | 未確認(ハイブリッドかどうかは不明) | グループ単位で参加申請 | 研究室・企業チーム単位が前提 |
| 2026-10-23 | NLP2027 招待講演・チュートリアルの意見募集締切 | — | Google フォーム | 誰でも |
| 2026-11-04 | NLP2027 テーマセッション/ワークショップ提案締切 | — | テーマセッションは非会員も発表可 | — |
| 2026-11-10 | MAKIS 2026 ワークショップ(KSE 2026 併催、LLM マルチエージェント) | 金沢 | 投稿は終了 | 聴講のみ |
| 2026-12-04 15:00 | 情報処理学会 第89回全国大会 一般講演の申込締切(受付は 10/9 開始) | — | — | **第9回 中高生情報学研究コンテスト**(ポスター)が併催。締切・条件は未確認 |
| 2026-12-14〜17 | ABCSS2026(IEEE BigData 併催、鳥海ほかが主催) | 米国フェニックス(ハイブリッド) | 論文締切 10/12(延長後)は**終了済み** | — |
| 2026-12-18〜2027-01-15 15:00 | **NLP2027(言語処理学会第33回年次大会)** 発表申込・論文締切 | **福岡国際会議場** | 大会は 2027-03-15〜19 | 学生・高校生の参加費は未公表。若手奨励賞の対象は 30 歳未満の第一著者 |
| 2027-03-01〜03 | **CSSJ2027(第6回 計算社会科学会大会)** | 滋賀大学 | 申込締切は未掲載(前回は大会の約1か月前) | 学会の入会費・年会費は無料 |
| 2027-03-04〜06 | 情報処理学会 第89回全国大会 | 名城大学 天白キャンパス(ハイブリッド) | 上記のとおり | 中高生情報学研究コンテストあり |
| 2027-03(例年) | SICE 社会システム部会研究会(第40回) | 未確認 | 第39回は 2026-03-09〜10 | — |
| 2027-06(例年) | JSAI2027 全国大会 | 未確認(公式は robots で取得不可) | JSAI2026 は 6/8〜12 に Gメッセ群馬で開催。発表申込は 12〜1 月だった | JSAI2026 にジュニアセッションがあったかは未確認 |

**福岡の依頼者にとって一番大きいのは NLP2027 が福岡国際会議場で開かれること。** 発表申込は 2026-12-18〜2027-01-15。LLM エージェント・ペルソナ・社会シミュレーション系の発表者に直接会える。

---

### B. エントリ

#### 鳥海研究室(東京大学 大学院工学系研究科 システム創成学専攻)
- 種別: 研究室
- 中心人物: 鳥海不二夫(教授)
- 代表的な成果: 他者意見推定モデルによる分極化・多元的無知のシミュレーション、人狼知能プロジェクト(書籍の共著)、交通手段選択のマルチエージェント強化学習。科研費では「ゼロ情報コスト社会における過剰制裁とリスク低減の社会デザイン」(2019–22、代表)。2026–29 年度は生成 AI 時代の情報リテラシーの国際共同研究に分担者として参加
- 窓口・発信: 研究室資料に連絡先 tori@sys.t.u-tokyo.ac.jp が掲載(https://www.sys.t.u-tokyo.ac.jp/labinfo/doc/doc_f_toriumi.pdf)。研究室サイトは robots 制限で取得不可
- 活動状況: 2026 年も教授として在籍。ABCSS2026(IEEE BigData 2026 併催ワークショップ、12/14〜17)の Main Chair
- 渋谷シムへの使いどころ: (2)(6) 噂・意見の伝播と分極化のエージェントモデル、人狼知能(説得・嘘)の会話設計の知見が会話の薄さ対策に使える。(8) 計算社会科学コミュニティの中心人物なので、CSSJ で研究を見てもらう相手として有力
- 既出: 新規(人物・研究室)
- 出典: https://nrid.nii.ac.jp/nrid/1000030377775 , https://www.sys.t.u-tokyo.ac.jp/labinfo/doc/doc_f_toriumi.pdf , https://css-japan.com/abcss2026/

#### 池上研究室(東京大学 大学院総合文化研究科)/高田亮介・増森淳
- 種別: 研究室
- 中心人物: 池上高志(教授)、高田亮介、増森淳(Atsushi Masumori)
- 代表的な成果: "Spontaneous Emergence of Agent Individuality through Social Interactions in LLM-Based Communities" arXiv:2411.03252(Llama-2-7b、10 体、50×50 空間、100 step)/"Emergent Social Dynamics of LLM Agents in the El Farol Bar Problem" arXiv:2509.04537(空間付きエル・ファロル問題、cs.MA)/Sakana AI との共著 Shachi arXiv:2509.21862
- 窓口・発信: 研究室サイト https://sacral.c.u-tokyo.ac.jp/(更新は古く、LLM の記載なし)
- 活動状況: 2025-09 にエル・ファロル論文 v3 を公開。2026-03-05 に OIST の "Hybrid Agencies" で講演した資料あり(PDF は取得失敗)。JSAI2026 では高田亮介ほか「LLM ペルソナエージェントにおける内的発話の導入と社会的調整能力の検証」が和泉研のニュースに掲載
- 渋谷シムへの使いどころ: (2)(4) 同じペルソナから会話を通じて個性が分化する過程、「内的発話」で社会的調整がどう変わるか、が会話の頻度・中身とペルソナドリフトに直結する。(3) エル・ファロル問題(混むなら行かない)は来街者ピークの較正問題の簡略版として参考になる
- 既出: 2411.03252 は既出(論文)。2509.04537 と 2509.21862 は新規
- 出典: https://arxiv.org/abs/2411.03252 , https://arxiv.org/html/2411.03252v1 , https://arxiv.org/abs/2509.04537v3 , https://sacral.c.u-tokyo.ac.jp/

#### 株式会社オルタナティヴ・マシン(Alternative Machine)
- 種別: スタートアップ
- 中心人物: 池上高志(関与。代表者の名前はサイトに記載なし)
- 代表的な成果: ALIFE Engine のライセンス提供、Plantbot、Neuroshoes、Wild Wordless World(山田うん×池上高志)など
- 窓口・発信: https://alternativemachine.co.jp/ / X https://twitter.com/alter_machine_ / YouTube https://www.youtube.com/channel/UCLAmqAjtPlFOtF5NWn6Albg/ / Instagram、Facebook
- 活動状況: サイトの最新ニュースは 2024-07(ALIFE 発表)。2026 年の活動は未確認。LLM エージェント事業はサイト上で確認できず
- 渋谷シムへの使いどころ: (8) ALife を社会実装する会社のモデルとして参考になる。北極星(AI 住民のいるメタバース)と思想が最も近い国内企業の一つ
- 既出: 新規
- 出典: https://alternativemachine.co.jp/ , https://www.alternativemachine.co.jp/news

#### Sakana AI(東京)— Shachi / CoffeeBench / MASS / Digital Ecosystems
- 種別: 企業(スタートアップ)
- 中心人物: So Kuroki、Yujin Tang、Takuya Akiba ほか(Shachi)。Issa Sugiura ほか(CoffeeBench)
- 代表的な成果: Shachi(LLM-ABM のモジュール型フレームワーク)arXiv:2509.21862 / https://github.com/SakanaAI/shachi(Apache-2.0、約48★。PsychoBench・Sotopia・EconAgent・OASIS など10ベンチを同梱し、「Carrying Memory to the Next Life」「Living in Multiple Worlds」などの探索研究も入っている)/CoffeeBench(6 社 90 日のコーヒー供給網経済、長期エージェントのベンチマーク)arXiv:2606.16613 / https://github.com/SakanaAI/CoffeeBench / MASS(集団知による再帰的自己改善)arXiv:2610.12176 / https://github.com/SakanaAI/mass / Digital Ecosystems(ブラウザで動くマルチエージェント NCA)https://github.com/SakanaAI/digital-ecosystem / AI Picbreeder(VLM エージェント集団のオープンエンド性。GECCO 2026、MIT・NYU と共著)arXiv:2605.23908
- 窓口・発信: ブログ https://sakana.ai/blog/ 、技術ブログ https://pub.sakana.ai/
- 活動状況: 非常に活発。2026-10-12 に MASS を公開、2026-06 に Fugu、2026-04 に SMBC と複数エージェントの共同開発
- 渋谷シムへの使いどころ: (4) Shachi の「記憶を環境間で持ち越す」「複数世界に同時に住む」実験は、複数日ランでの記憶・ドリフトの設計参考になる。(1) CoffeeBench の「idle-drift」(何もしなくなる故障モード)と「コミュニケーション量が多いほど成績が良い」という結果は、会話 0.07% 問題と行動更新の議論に使える。(8) 経済の実フロー設計の参考にもなる
- 既出: 新規(Shachi・CoffeeBench・MASS・Picbreeder の論文と GitHub はいずれも known リストになし)
- 出典: https://arxiv.org/abs/2509.21862 , https://github.com/SakanaAI/shachi , https://sakana.ai/coffee-bench/ , https://arxiv.org/abs/2606.16613 , https://sakana.ai/mass/ , https://sakana.ai/digital-ecosystem/ , https://sakana.ai/picbreeder-ai/

#### 和泉研究室(東京大学 大学院工学系研究科)— 人工市場 × LLM エージェント
- 種別: 研究室
- 中心人物: 和泉潔(教授)、橋本龍二、池上暁雄、村山友理
- 代表的な成果: Hashimoto et al. "LLM agents reveal how human bias shapes path-dependent market dynamics"(Journal of Computational Social Science Vol.9, 2026)/"Financial Market as a Self-Organized Ecosystem…"(Artificial Life Vol.32, 2026)/JSAI2026 での発表「不均一な顧客分布下における LLM エージェントの空間的価格競争戦略」(池上暁雄ほか)、「経済環境に接地した LLM エージェントによる意見ダイナミクスのシミュレーション」(橋本龍二ほか)/人工市場シミュレータ Plham
- 窓口・発信: https://sites.google.com/socsim.org/izumi-lab(旧 http://socsim.t.u-tokyo.ac.jp からリダイレクト)。研究室見学会を開催している
- 活動状況: 2026 年に論文多数。SIG-FIN(人工知能学会 金融情報学研究会)の中心
- 渋谷シムへの使いどころ: (8) 「不均一な顧客分布の中で LLM 店舗エージェントが空間的に価格競争する」研究は、出店検討という最初の顧客の用途にほぼそのまま対応する。(2) 経済に接地した意見ダイナミクスは、会話の中身を経済行動と結びつける参考になる
- 既出: 新規
- 出典: https://sites.google.com/socsim.org/izumi-lab , https://www.sys.t.u-tokyo.ac.jp/labinfo/doc/doc_k_izumi.pdf

#### 松尾・岩澤研究室(東京大学)— LLM 社会シミュレーションのサーベイ
- 種別: 研究室
- 中心人物: 森隆太郎、原田憲旺(同等貢献の筆頭)、大西直、松尾豊、岩澤有祐
- 代表的な成果: 「大規模言語モデル時代の社会シミュレーション:『再現』と『理解』の目的別に見る研究動向」人工知能学会論文誌 41巻4号(2026、学会設立40周年記念論文)。目的を「特定の実社会システムの再現(実データでの検証・較正が課題)」と「理論モデル」に分け、長期の方向として「高次元科学」を提案
- 窓口・発信: https://weblab.t.u-tokyo.ac.jp/(問い合わせフォームあり)/ニュース https://weblab.t.u-tokyo.ac.jp/?p=13017
- 活動状況: 2026-04-22 に採録を告知。研究室は NeurIPS 2026 に 5 本採択(2026-10)。GCI など公開講座あり(高校生が受講できるかは未確認)
- 渋谷シムへの使いどころ: (6) 「再現」型シミュレーションの検証・較正の論点が日本語でまとまっており、未踏の二次審査や提案書で先行研究として引ける。(3) 較正の位置づけの整理にも使える
- 既出: 新規(日本語サーベイ。arXiv 版は未確認)
- 出典: https://weblab.t.u-tokyo.ac.jp/?p=13017 , https://www.jstage.jst.go.jp/browse/tjsai/-char/ja

#### 松尾研究所 テックブログ(Zenn: mkj)
- 種別: ブログ(企業)
- 中心人物: 大西直(シニアデータサイエンティスト)、髙田賢、長谷航記ほか
- 代表的な成果: 「AI エージェントによる社会シミュレーション - Generative Agents, AgentSociety, CitySim の紹介」(2025-07-11)/「【JSAI2026】松尾研究所 参加レポート」(2026-07-14)。後者では JSAI2026 の「大規模言語モデルを用いたマルチドメイン行動ログの統合と行動予測」(髙田・渡邊・長谷ほか、CCC・V ポイントマーケティングと共同、LLM でペルソナを生成)を紹介
- 窓口・発信: https://zenn.dev/p/mkj (RSS https://zenn.dev/p/mkj/feed)
- 活動状況: 活発(2026-10 まで毎週更新)
- 渋谷シムへの使いどころ: (6)(8) 実購買ログから LLM でペルソナを作り行動を予測する事例は、ペルソナの較正と小売顧客への説明に使える。CitySim の紹介も参考になる
- 既出: 新規(ブログ)
- 出典: https://zenn.dev/mkj/articles/efb017f7a440ca , https://zenn.dev/mkj/articles/jsai2026-report_20260619 , https://zenn.dev/p/mkj/feed

#### 計算社会科学会(CSSJ)
- 種別: 学会
- 中心人物: 運営は鳥海不二夫・吉田光男・岡田勇・澁谷遊野ら(ABCSS の Chair として確認)
- 代表的な成果: 年次大会 CSSJ。CSSJ2026(第5回、2026-03-02〜04、クリエート浜松)は発表数・参加者数とも前年を上回った。国際ワークショップ ABCSS(IEEE BigData 併催)、HSoC2026(HICSS 併催)、「ウェブ・ソーシャルメディア論文読み会」を後援
- 窓口・発信: https://css-japan.com/ / メーリングリスト(サイト内の案内ページ)/問い合わせ abcss [at] css-japan.com
- 活動状況: **CSSJ2027(第6回)は 2027-03-01〜03、滋賀大学で開催予定**。申込締切は未掲載(CSSJ2025 では発表申込が大会の約1か月前、原稿が約1週間前。発表は現地のみ、聴講はハイブリッド)。入会費・年会費は無料
- 渋谷シムへの使いどころ: (6)(8) 計算社会科学者に「LLM が人を再現しているか」の検証方法を問える場。入会は無料なので、まず ML に登録して CSSJ2027 で発表するのが現実的
- 既出: 新規
- 出典: https://css-japan.com/ , https://css-japan.com/abcss2026/ , https://dbjapan.dbsj.org/mailman3/hyperkitty/list/dbjapan@dbsj.org/thread/AD3INXX7UAXDXSIGMQBHMF3WRHHBJNJL

#### 言語処理学会 第33回年次大会(NLP2027)— 福岡開催
- 種別: 学会・ワークショップ
- 中心人物: 言語処理学会
- 代表的な成果: NLP2026(宇都宮、2026-03-09〜13)では、インテージ「LLM を用いたアンケート回答生成における精度の要因分析」(C1-22)、名大 宮﨑・有田・鈴木「視覚言語モデルの主観的評価に基づく仮想生物進化」(C2-19)、岡山理大「教員・学生特性の抽出に基づく多様な授業シミュレーションの構築」(C1-9)、東大/理研「LLM の知能は人間と同様の構造を持つか?」(B1-2)、テーマセッション「人狼知能:嘘を見破り説得する会話ゲームと LLM」など
- 窓口・発信: https://www.anlp.jp/nlp2027/ / https://www.anlp.jp/
- 活動状況: **2027-03-15〜19、福岡国際会議場(本会議は 3/15 午後〜3/18、3/19 はワークショップ)。発表申込は 2026-12-18 開始、発表申込・論文の締切は 2027-01-15 15:00。** テーマセッション提案は 2026-11-04 まで(非会員も発表可)。招待講演・チュートリアルへの意見募集は 10-23 まで。ハイブリッド(ただし現地ポスターはオンラインで聴講不可)。参加費は未公表
- 渋谷シムへの使いどころ: (2)(4)(6) 会話の質・ペルソナ・人間らしさの評価をやっている NLP 研究者に、地元福岡で直接会える最大の機会。会話生成とドリフトの検証を「日本語 LLM エージェントの会話分析」として発表する道もある
- 既出: 新規
- 出典: https://www.anlp.jp/nlp2027/ , https://www.anlp.jp/proceedings/annual_meeting/2026/

#### 人工知能学会(JSAI)全国大会/栗原聡 会長
- 種別: 学会
- 中心人物: 栗原聡(慶應義塾大学 教授、人工知能学会 会長。学会は 2026 年で設立40周年)
- 代表的な成果: JSAI2026(第40回、2026-06-08〜12、Gメッセ群馬)。栗原氏はニューラルの基盤モデルを記号ネットワークに変換する「NSX(Neural Symbolic Transformation)」構想をインタビューで提唱(LLM マルチエージェントへの直接の言及はなし)
- 窓口・発信: https://www.ai-gakkai.or.jp/(robots 制限で JSAI2027 と SIG ページは取得できず)
- 活動状況: JSAI2026 は発表申込 2025-12-23〜2026-01-28、論文 01-29〜02-18 だった。JSAI2027 の日程・会場は未確認(例年 6 月、申込は 12〜1 月)
- 渋谷シムへの使いどころ: (6)(8) 国内で LLM エージェント・社会シミュレーション発表が最も多い場。12〜1 月の申込に間に合えば JSAI2027 で発表できる。(2) NSX の「動機の芯」の議論は、行動を空腹だけで動かさないための考え方として参考になる
- 既出: 新規
- 出典: https://www.ai-gakkai.or.jp/jsai2026/en/important-dates , https://www.techno-edge.net/article/2026/06/02/5131.html , https://zenn.dev/mkj/articles/jsai2026-report_20260619

#### 計測自動制御学会(SICE)社会システム部会研究会(SocSys)
- 種別: 学会・ワークショップ
- 中心人物: 部会の運営は未確認。LLM 関連の発表者: 岡本貴大・原田拓弥、田鍋史生・佐藤里恵・林久志、市川学・藤田進太郎・藤田楓、吉見武・大堀耕太郎・後藤裕介、北島悠吾・村田忠彦、酒井和・坂田明信・高橋真吾
- 代表的な成果(第39回、2026-03-09〜10): 「LLM 駆動型社会シミュレーションに向けた合成人口データへの個性の割り当て」(岡本・原田)/「合成人口データへの Big Five 性格特性の付与」(北島・村田)/「LLM はエージェントベースシミュレーションのミクロ・マクロリンクを推論できるか」(吉見・大堀・後藤)/「AI エージェントを用いた SOARS での社会シミュレーションモデル構築の試行」(市川ほか)/「生成 AI マルチエージェントによる社会イベント参加と交通手段選択の集団意思決定」(田鍋・佐藤・林)/「市民の行動特性からのロールプレイ用ペルソナ生成(対話型 GA × 生成 AI)」(酒井・坂田・高橋)/位置情報による観光客エージェントと混雑モデルの改良(岡本・國領・貝原)
- 窓口・発信: プログラム https://easychair.org/smart-program/SocSys039/(SICE の部会ページは取得できず)
- 活動状況: 毎年 3 月に開催。第40回(2027-03)の詳細は未確認
- 渋谷シムへの使いどころ: (4)(6) **国勢調査ベースの合成人口に LLM 用の個性・Big Five を割り当てる研究が直接の先行例**(39万体のペルソナ生成と同じ問題)。(3) 観光客エージェントの位置情報による較正は来街者ピークの較正に使える。日本の ABM コミュニティ(SOARS、関西大 村田研、神戸大 貝原研)の中心的な場
- 既出: 新規
- 出典: https://easychair.org/smart-program/SocSys039/2026-03-10.html , https://easychair.org/smart-program/SocSys039/2026-03-09.html

#### 村田忠彦研究室(関西大学)— 合成人口
- 種別: 研究室
- 中心人物: 村田忠彦(関西大学 教授)、原田拓弥
- 代表的な成果: 「基盤地図情報による合成した世帯構成への位置情報の付加」(原田・村田、SICE 社会システム部会で最優秀論文賞)/第39回 SocSys での合成人口への Big Five 付与(北島・村田)、日常活動を連続的に生成する機械学習(松村・村田)
- 窓口・発信: http://www.res.kutc.kansai-u.ac.jp/~murata/(連絡先の記載なし)
- 活動状況: 2026-03 の SocSys で複数発表あり
- 渋谷シムへの使いどころ: (4)(6) 日本の国勢調査から世帯・位置つきの合成人口を作る手法の国内第一人者。39万体の母集団生成の妥当性を相談できる
- 既出: 新規
- 出典: http://www.res.kutc.kansai-u.ac.jp/~murata/ , https://easychair.org/smart-program/SocSys039/2026-03-09.html

#### 産業技術大学院大学 人工知能・エージェントシステム研究所(AIIT)
- 種別: 研究室(研究所)
- 中心人物: 林久志(所長)
- 代表的な成果: 2026-04-01 設立(〜2031-03)。グループ①は LLM 会話による集団意思決定のモデリングと会話シミュレーション、グループ②はマルチエージェントシミュレーション×強化学習×LLM(歩行者群集の制御を含む)。SocSys039 で江津市の地方創生 AI 実装を発表
- 窓口・発信: https://aiit.ac.jp/documents/jp/research_collab/research/2025-2026/research_09_2026_hayashi.pdf
- 活動状況: 2026 年度に新設され、活動中
- 渋谷シムへの使いどころ: (2)(7) 会話シミュレーションと歩行者群集の制御の両方を扱う、珍しい組み合わせ。(8) 自治体連携の実績が行政向け用途の参考になる
- 既出: 新規
- 出典: https://aiit.ac.jp/documents/jp/research_collab/research/2025-2026/research_09_2026_hayashi.pdf

#### 大阪大学 天野辰哉・山口弘純(情報科学研究科)— LLM 駆動の都市交通シミュレーション
- 種別: 研究室
- 中心人物: 天野辰哉(助教)、山口弘純(教授)、矢野敦大、Yu Yasuda、Masashi Uegaki
- 代表的な成果: JST さきがけ「大規模言語モデル駆動の都市交通シミュレーション基盤」。GPS・交通・SNS・アンケートを自然言語にして LLM エージェントに統合。Agent-Navigation。地方観光地の次訪問 POI 予測で精度 49.1%。「実データ同化型シミュレーションに向けた LLM による観光客行動の予測手法」(JSAI 研究会 2025)/「先見シミュレーションに非同期観測を同化する人流デジタルツイン」/LiDAR による人流デジタルツイン/駅ホームの群衆流のデジタルツイン(SMARTCOMP)
- 窓口・発信: https://mc.net.ist.osaka-u.ac.jp/ja/projects/presto-llm
- 活動状況: 2026-03 の阪大資料に掲載あり、進行中。今後は大規模イベント時の混雑・新モビリティ・避難誘導の3シナリオで検証予定
- 渋谷シムへの使いどころ: (3)(6)(7) **国内で最も近い研究**。実人流(LiDAR・定点観測)を LLM エージェントにデータ同化する手法は、holdout 0/4 の較正問題に直接効く。駅ホームの群衆デジタルツインは物理層の導入の参考になる。連絡先の最優先候補
- 既出: 新規
- 出典: https://mc.net.ist.osaka-u.ac.jp/ja/projects/presto-llm , https://www.ccb.osaka-u.ac.jp/wpccb_handle/wp-content/uploads/2026/03/AmanoTatsuya2026JP.pdf , https://www.ccb.osaka-u.ac.jp/wpccb_handle/wp-content/uploads/2026/03/NextGenerationResearch_2026.pdf

#### Chuan Xiao・Zengqing Wu(大阪大学/名古屋大学/京都大学)
- 種別: 研究室
- 中心人物: Chuan Xiao(大阪大学・名古屋大学)、Zengqing Wu(大阪大学・京都大学)、鬼塚真(大阪大学)、伊藤孝行(京都大学、EMNLP 2025 の共著者)
- 代表的な成果: "Shall We Team Up: Exploring Spontaneous Cooperation of Competing LLM Agents"(Findings of EMNLP 2024)arXiv:2402.12327 / https://github.com/wuzengqing001225/SABM_ShallWeTeamUp / "The Hidden Strength of Disagreement: …Consensus-Diversity Tradeoff in Adaptive Multi-Agent Systems"(EMNLP 2025、Wu & Ito)/"Predicting the scale limits of social mechanisms in agent societies" arXiv:2608.22884(2026、互恵性・合意・罰・噂がエージェント数を増やしたときに壊れる規模を事前に予測)
- 窓口・発信: https://aclanthology.org/people/zengqing-wu
- 活動状況: 2026-08 に新論文
- 渋谷シムへの使いどころ: (2)(5)(6) 「小規模で効く社会メカニズムが数千体で壊れる規模を、メッセージの到達範囲と持続時間から予測する」研究は、39万体で会話・噂が機能するかを本番ラン前に見積もる方法としてそのまま使える。「件数で見せるか割合で見せるか」でエージェントの反応が変わるという知見も、知覚設計に効く
- 既出: 新規(2402.12327、2608.22884 とも known リストになし)
- 出典: https://arxiv.org/html/2402.12327v2 , https://arxiv.org/abs/2608.22884 , https://aclanthology.org/people/zengqing-wu

#### 名古屋大学 有田隆也・鈴木麗璽 研究室
- 種別: 研究室
- 中心人物: 有田隆也、鈴木麗璽
- 代表的な成果: "An evolutionary model of personality traits related to cooperative behavior using a large language model" arXiv:2310.05976 / NLP2026「視覚言語モデルの主観的評価に基づく仮想生物進化」(宮﨑・有田・鈴木)
- 窓口・発信: 未確認
- 活動状況: 2026-03 の NLP2026 で発表
- 渋谷シムへの使いどころ: (4) LLM エージェントの性格特性が集団の中で進化・変化するモデルは、複数日ランでのペルソナドリフトを「ノイズ」ではなく「適応」と見る視点を与える
- 既出: 新規
- 出典: https://arxiv.org/abs/2310.05976 , https://www.anlp.jp/proceedings/annual_meeting/2026/

#### 立命館大学 服部宏充 研究室/吉添衛(滋賀県立大学)
- 種別: 研究室
- 中心人物: 服部宏充(立命館大学 教授)、吉添衛(滋賀県立大学 特任講師、元立命館 助教)
- 代表的な成果: 科研費「インタラクティブシミュレーションに基づく人間中心の都市空間デザインの実践」(国際共同研究強化(B) 2023–27。成果に LLM ベースのエージェントモデルとマルチエージェント社会シミュレーションを含む)/「人と AI の共創のための多元的社会デザインプラットフォームの開発」(基盤(B) 2026–28)
- 窓口・発信: 研究室サイトは取得できず(未確認)
- 活動状況: 2026 年に新しい科研費が始まっている
- 渋谷シムへの使いどころ: (8) 都市空間デザインを LLM エージェントシミュレーションで市民と一緒に検討する研究は、行政・再開発向けの用途設計の参考になる
- 既出: 新規
- 出典: https://nrid.nii.ac.jp/nrid/1000070982304/

#### 富士通 ソーシャルデジタルツイン/デジタルリハーサル(+名古屋大学 共同研究部門)
- 種別: 企業
- 中心人物: 植木美和(富士通研究所 リサーチディレクター)、森川高行(名古屋大学 特任教授)。富士通研究所コンバージングテクノロジー研究所 ソーシャルデジタルツイン CPJ の杉本崇尚、郭兆功、野田政秀ら
- 代表的な成果: 施策を実行する前に、人や社会の振る舞いをデジタル空間で再現して効果を評価する「デジタルリハーサル」。富士通-名古屋大学ソーシャルデジタルツイン研究部門(2023-09 設置、名大 NIC)。シェアドモビリティの最適配置など
- 窓口・発信: https://global.fujitsu/ja-jp/technology/research/srl/nagoya-u , https://global.fujitsu/ja-JP/technology/key-technologies/converging-technologies
- 活動状況: **CEATEC 2026(2026-10-13〜16、幕張メッセ ホール6)で川崎駅周辺のゴジラ避難誘導デジタルリハーサルを体験展示**(2026-10-01 発表)。公開情報では LLM 利用は確認できず
- 渋谷シムへの使いどころ: (8) 「行政・再開発向けの事前検証シミュレータ」の最大の国内先行・競合。ポジショニング(LLM 認知+実データ較正という差分)を説明するときの比較対象になる
- 既出: 新規
- 出典: https://global.fujitsu/ja-JP/pr/news/2026/10/01-01 , https://global.fujitsu/ja-jp/technology/research/srl/nagoya-u , https://global.fujitsu/ja-jp/technology/research/article/researcherinterview/202408-social-digital-twin

#### 構造計画研究所(KKE)— artisoc / PLATEAU の LLM マルチエージェントシミュレーション
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: MAS プラットフォーム artisoc / artisoc Cloud(2026-09 にアップデート)。国交省 PLATEAU ユースケース uc25-05「AI を活用したマルチエージェントシミュレーション技術等の開発業務」(2025 年度、熊本市 桜町・花畑と豊橋駅周辺)。Ollama のローカル LLM で設定チャットボット・視覚入力による経路選択・エージェントへの Q&A を実装し、Unity + PLATEAU SDK で一人称視点を表示。自治体職員11名の評価では「結果に納得できる」が 4/11 にとどまり、RAG と実測での較正が今後の課題とされた
- 窓口・発信: https://mas.kke.co.jp/(MAS コミュニティ、YouTube・X・Facebook へのリンクあり)/ https://www.mlit.go.jp/plateau/use-case/uc25-05/
- 活動状況: 活動中。MAS コンペティションは第20回(2020)で止まっている
- 渋谷シムへの使いどころ: (6)(8) **PLATEAU × LLM エージェント × 自治体という同じ領域の先行事例で、「納得感 4/11」という失敗データが貴重**。較正で差別化する根拠として使える。(7) 視覚入力による経路選択の実装は物理・空間層の参考になる
- 既出: 新規(PLATEAU SDK は既出)
- 出典: https://www.mlit.go.jp/plateau/use-case/uc25-05/ , https://www.mlit.go.jp/plateau/tag/cfd , https://mas.kke.co.jp/ , https://mas.kke.co.jp/masc/

#### 博報堂 DY グループ「バーチャル生活者」
- 種別: 企業
- 中心人物: 博報堂 DY ホールディングス/博報堂テクノロジーズ
- 代表的な成果: 約20万人の調査パネル(Querida)の属性・意識・実行動データから、AI で生活者を再現する「エビデンスベースド」なバーチャル生活者。複数の生活者と同時にチャットでき、画像・動画を見せて意見を聞ける
- 窓口・発信: 未確認(報道のみ)
- 活動状況: 2025-11-13 発表、グループ全社員に提供。外部への単体提供は公表されていない
- 渋谷シムへの使いどころ: (6)(8) 実パネルに接地した合成生活者は、ペルソナの較正方法と広告用途の競合として参考になる
- 既出: 新規
- 出典: https://webtan.impress.co.jp/n/2025/11/14/50424 , https://ai-revolution.co.jp/media/ai-in-advertising/

#### 電通「AI For Growth」(AI For Growth Talk / AI マーケットツイン)
- 種別: 企業
- 中心人物: 電通/電通デジタル(JSAI2026 では日野恭佑・佐々木一が AI ペルソナとの協働を発表)
- 代表的な成果: AI For Growth Talk(旧 AIQQQ TALK、2026-04-06 刷新。約750パターンのペルソナと特化型 AI ペルソナ。ペルソナ同士の会話によるグループインタビューもできる。People Model ベース)/AI For Growth Suite「AI マーケットツイン」(2026-05-25 発表、「1億人規模の AI ペルソナ」で施策の反応を事前に試算)/未来ファインダー for AI(2026-10-02)
- 窓口・発信: 未確認(報道のみ。電通のリリース一覧ページは取得できず)
- 活動状況: 活発。一部機能を年内にブラウザ SaaS として外部提供する予定
- 渋谷シムへの使いどころ: (8) 「1億人の AI ペルソナで施策を事前試算」は、広告・媒体価値の用途で最も近い商用競合。(2) ペルソナ同士の会話によるグループインタビュー機能は会話設計の参考になる
- 既出: 新規
- 出典: https://cloud.watch.impress.co.jp/docs/news/2099321.html , https://ai-revolution.co.jp/media/ai-in-advertising/ , https://zenn.dev/mkj/articles/jsai2026-report_20260619

#### NTT データ「LITRON Multi Agent Simulation」
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: 仮想顧客の AI エージェントにグループ討議をさせるシミュレーション。JAL カードのダイレクトメール施策で実証
- 窓口・発信: 未確認(NTT データのリリースページは取得できず)
- 活動状況: 2025-07 時点で報道あり。2026 年の状況は未確認
- 渋谷シムへの使いどころ: (8) 合成顧客の議論で施策を評価する B2B 事例。顧客にどう売っているかの参考になる
- 既出: 新規
- 出典: https://www.cio.com/article/4028825/%E4%BA%8B%E4%BE%8B%E3%81%8B%E3%82%89%E8%80%83%E3%81%88%E3%82%8Bllm%E3%82%A8%E3%83%BC%E3%82%B8%E3%82%A7%E3%83%B3%E3%83%88%E3%82%B7%E3%83%9F%E3%83%A5%E3%83%AC%E3%83%BC%E3%82%B7%E3%83%A7%E3%83%B3.html

#### インテージ(合成調査・LLM アンケート回答生成)
- 種別: 企業
- 中心人物: 尾城奈緒子、アフィカ アディラ、小田虎之介(インテージ)
- 代表的な成果: NLP2026 C1-22「LLM を用いたアンケート回答生成における精度の要因分析」
- 窓口・発信: 未確認
- 活動状況: 2026-03 に発表
- 渋谷シムへの使いどころ: (6) LLM の回答が人の調査とどこで、なぜずれるかの要因分析は、「LLM が人を再現しているか」を検証する方法論の国内事例として使える
- 既出: 新規
- 出典: https://www.anlp.jp/proceedings/annual_meeting/2026/

#### 富士フイルムビジネスイノベーション「ペルソナ AI」
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: Revoria Cloud Marketing の新機能。日本の人口分布統計で学習したモデルで、仮想消費者による模擬市場調査とペルソナ生成を行う(2026-01-08 にβ版開始)
- 窓口・発信: 未確認
- 活動状況: 2026-01 にβ版を開始
- 渋谷シムへの使いどころ: (8) 統計に接地した仮想消費者の商用化事例(競合調査用)
- 既出: 新規
- 出典: https://dempa-digital.com/?p=704708

#### LY Corporation(LINE ヤフー)× NYU 矢部貴大 — HuMob / SIGSPATIAL GISCUP 人流データ
- 重複のため「都市・人流・群衆」タブの同名項目にまとめた

#### 関本・中居研究室(東京大学 空間情報科学研究センター CSIS)
- 重複のため「都市・人流・群衆」タブの同名項目にまとめた

#### KDDI 総合研究所
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: 「人流データを活用し移動リスクの発生を高精度に AI で予測する技術」(2025-03-31)/「人間の応対を学習し高精度に再現する AI エージェント」(2025-11-26。応対パターンを構造化してファクトチェックする手法。au チャットサポートに導入)
- 窓口・発信: https://www.kddi-research.jp/
- 活動状況: 活動中。LLM 社会シミュレーションそのものの公開事例は確認できず
- 渋谷シムへの使いどころ: (3) KDDI 人流データの提供元側の研究組織。「過去の人の応対パターンを構造化して LLM 出力を縛る」手法は、System 1/1.5 の習慣を実データから作る発想と通じる
- 既出: 新規
- 出典: https://www.kddi-research.jp/ , https://www.kddi-research.jp/newsrelease/2025/112601.html

#### 人狼知能プロジェクト/AIWolfDial(人狼知能大会 自然言語部門)
- 種別: OSS コミュニティ・競技会
- 中心人物: 狩野芳伸、大槻恭士、園田亜斗夢、中田洋平、箕輪峻、鳥海不二夫(書籍の著者)
- 代表的な成果: LLM エージェント同士で人狼(説得・嘘・推理)を対戦させる大会。NLP2026 にテーマセッションあり
- 窓口・発信: https://aiwolf.org/ / https://aiwolfdial.github.io/aiwolf-nlp/ / X @aiwolfdial_nlp / GitHub aiwolfdial
- 活動状況: AIWolfDial 2026 は INLG 2026 併催で 2026-10-17〜21(ユトレヒト)。国際大会は英語のみ。国内大会(2025 春季)もあり。参加資格は明記されていない
- 渋谷シムへの使いどころ: (2) 多人数の LLM 会話で説得・情報の隠蔽・信頼形成を起こすプロンプトと評価の蓄積があり、会話が薄い問題の参考になる。誰でも出られる競技会なら実戦経験にもなる
- 既出: 新規
- 出典: https://aiwolf.org/ , https://aiwolfdial.github.io/aiwolf-nlp/ , https://www.anlp.jp/proceedings/annual_meeting/2026/

#### LLM-jp(NII 大規模言語モデル研究開発センター)
- 種別: OSS コミュニティ
- 中心人物: NII LLM 研究開発センター(黒橋禎夫ら。人物はページで未確認)
- 代表的な成果: LLM-jp-4.1 シリーズ(2026-09-28 公開)/コーパス・評価ツール
- 窓口・発信: https://llm-jp.nii.ac.jp/ / X https://x.com/llm_jp / GitHub https://github.com/llm-jp / HF https://huggingface.co/llm-jp / YouTube https://www.youtube.com/@LLM-jp/videos
- 活動状況: 活発。LLM 勉強会は毎月1回(火 14:30〜18:00)、残りの日程は 2026-10-20、11-17、12-15、2027-01-19、02-16、03-23。参加は Google フォームからグループ単位で申請
- 渋谷シムへの使いどころ: (5) 日本語に強いオープンモデルで System 2α/2β の候補になる。勉強会は日本の LLM 研究者・企業が一堂に会する場
- 既出: 新規
- 出典: https://llm-jp.nii.ac.jp/ , https://llm-jp.nii.ac.jp/join/

#### Swallow LLM(東京科学大学 岡崎研・横田研+産総研)
- 種別: OSS コミュニティ
- 中心人物: 岡崎直観、横田理央(東京科学大学 教授)、高村大也(産総研)
- 代表的な成果: Qwen3 Swallow(8B / 30B-A3B / 32B)、GPT-OSS Swallow(20B / 120B)、Gemma-2-Llama Swallow、Llama 3.3 Swallow 70B、Swallow Leaderboard v2(2026-03 時点で累計約241万ダウンロード)
- 窓口・発信: https://swallow-llm.github.io/index.ja.html (Hugging Face で公開、商用利用可)
- 活動状況: 活発
- 渋谷シムへの使いどころ: (5)(2) 日本語の会話の質を上げたいとき、8B 級の Qwen3 Swallow や 30B-A3B(MoE)は、39万体の推論コストと日本語会話の質の両方で、System 2α の第一候補になる
- 既出: 新規
- 出典: https://swallow-llm.github.io/index.ja.html

#### SB Intuitions(Sarashina)
- 種別: 企業
- 中心人物: 未確認
- 代表的な成果: 日本語特化 LLM「Sarashina」(2026 年の最新版はページ上で未確認)
- 窓口・発信: https://www.sbintuitions.co.jp/ / X twitter.com/sbintuitions / note sb_intuitions
- 活動状況: 活動中
- 渋谷シムへの使いどころ: (5) 日本語モデルの選択肢の一つ
- 既出: 新規
- 出典: https://www.sbintuitions.co.jp/

#### MAKIS 2026(KSE 2026 併催 ワークショップ、金沢)
- 種別: 学会・ワークショップ
- 中心人物: Qiang Ma、Yijun Duan、Yun Liu(京都工芸繊維大学)、Nguyen Le Minh(JAIST)
- 代表的な成果: LLM マルチエージェント×知識グラフのワークショップ
- 窓口・発信: https://kse2026.kse-conferences.org/workshop-makis/ (連絡先 liuyun@kit.ac.jp)
- 活動状況: ワークショップは 2026-11-10。投稿は締切済み
- 渋谷シムへの使いどころ: (4) 知識グラフによるエージェントの記憶構造の参考。国内開催なので聴講できる
- 既出: 新規
- 出典: https://kse2026.kse-conferences.org/workshop-makis/ , https://dbjapan.dbsj.org/mailman3/hyperkitty/list/dbjapan@dbsj.org/thread/22K5HM7P6GJU6NBQK2JLUOJFWDDV7F3S/

#### 情報処理学会 第89回全国大会/第9回 中高生情報学研究コンテスト
- 種別: 学会(高校生が発表できる)
- 中心人物: 情報処理学会
- 代表的な成果: —
- 窓口・発信: https://www.ipsj.or.jp/event/taikai/89/ / コンテスト https://www.ipsj.or.jp/event/taikai/89/89PosterSession/
- 活動状況: 大会は 2027-03-04〜06、名城大学 天白キャンパス(ハイブリッド)。一般講演の申込は 2026-10-09〜12-04 15:00。**中高生情報学研究コンテスト(ポスター)**は 2026-05-08 に案内が公開済みだが、締切・応募条件は取得できず未確認
- 渋谷シムへの使いどころ: (8) 高校生として発表・受賞できる正規の学会枠。卒業前(2027-03)の実績づくりになる。中高生枠の締切は早めに要確認
- 既出: 新規
- 出典: https://www.ipsj.or.jp/event/taikai/89/ , https://www.ipsj.or.jp/event/taikai/89/appli_paper.html

#### Cross Labs(京都)→ Nooma Labs / ALife Japan
- 種別: 研究室(民間)/コミュニティ
- 中心人物: Olaf Witkowski
- 代表的な成果: 集団的予測符号化による人間-AI 共創の生態系(Artificial Life 誌)、エージェント型 AI の「神経多様性的な影響されやすさ」(PNAS Nexus)、Cross Roads 講演シリーズ。ALife Japan は Future Talent Program(次世代 ALife 研究者への資金・メンター支援)を運営
- 窓口・発信: https://www.crosslabs.org/ (アーカイブ)/ https://alife-japan.org/
- 活動状況: **Cross Labs は 2026-08-31 に閉鎖**し、研究プログラムは独立研究所 Nooma Labs が引き継いだ。ALife Japan は活動中
- 渋谷シムへの使いどころ: (8) 北極星(AI 住民のいる世界)向けの ALife コミュニティ。Future Talent Program は若手(高校生が対象かは未確認)向けの資金源候補
- 既出: 新規
- 出典: https://www.crosslabs.org/ , https://alife-japan.org/

#### 九州大学 荒川研究室(HumanoPhilic Systems Lab)— 福岡
- 種別: 研究室
- 中心人物: 荒川豊(教授)
- 代表的な成果: センサーと機械学習による行動認識、感情・ストレス推定、行動変容支援システム(BCSS)。NTT ドコモ、KDDI、富士通、トヨタなどと共同研究。2023 年度の学生数は51名で、九大システム情報科学研究院で最大のグループ
- 窓口・発信: https://arakawa-lab.com/
- 活動状況: 活動中(最新ニュースの日付は未確認)。LLM や人流シミュレーションの明示はなし
- 渋谷シムへの使いどころ: (1)(6) 人の実際の行動データ(いつ食事・休憩・移動するか)に基づく行動モデルの知見は、空腹が行動の主因になりすぎる問題と行動更新頻度の較正に使える。**福岡で直接会える大学の研究者として最有力**
- 既出: 新規
- 出典: https://arakawa-lab.com/

#### Zenn / Qiita の個人・企業ブログ(生成エージェント・社会シミュレーション)
- 種別: ブログ
- 中心人物: 権藤(doo12、ルミナイ株式会社 R&D。東大発、六本木、2026-07 に名古屋支社開設)/rintaro(fumofumo3、GitHub RintaroMatsumoto)/othelloman(Qiita)/sesseki-kurage(Qiita)
- 代表的な成果: 「LLM で人工社会を創る:Generative Agents が実現した創発的社会行動」(2025-12-02)https://zenn.dev/lluminai_tech/articles/98979a5ec62344 /「#09 愛の感染」(2026-04-20、AI 人格実験シリーズ。6体での「愛」の伝播・世代継承・反愛エージェント。Zenodo プレプリント DOI 10.5281/zenodo.19273577)https://zenn.dev/fumofumo3/articles/09-love-contagion と人間らしい応答タイミング・文体ゆらぎの OSS https://github.com/RintaroMatsumoto/human-persona (AGPL-3.0、1★)/「Generative Agents を動かして遊ぶ」(2025-12-23)https://qiita.com/othelloman/items/7ed46bf59b7e1c7adf6e /「Generative Agents の LLM を Llama2 で実装してみた」(2024-05-23)https://qiita.com/sesseki-kurage/items/f39cece127ee92257928
- 窓口・発信: 上記 URL
- 活動状況: 2025-12〜2026-04 に更新あり
- 渋谷シムへの使いどころ: (2) human-persona の「応答タイミング・文体のゆらぎ・文脈への言及」は、会話を人間らしくするための小さな部品として流用を検討できる。日本の個人開発者とつながる入口にもなる
- 既出: 新規(Generative Agents 本体は既出)
- 出典: https://zenn.dev/api/articles?topicname=社会シミュレーション&order=latest , https://qiita.com/tags/generativeagents/feed , https://www.lluminai.co.jp/ , https://github.com/RintaroMatsumoto/human-persona

#### メタデータラボ株式会社(GPU クラウド)
- 種別: 企業
- 中心人物: 未確認(既知の窓口はやなぎさん)
- 代表的な成果: AI サーバー・GPU クラウドのレンタル、データセンター構築、AI コミュニティの運営、「GPU Router」構想
- 窓口・発信: https://metadatalab.net/
- 活動状況: 活動中。サイト上に AUTOMATA の記載はなし
- 渋谷シムへの使いどころ: (5) A5000×7 の貸与元。有償の GPU レンタル窓口として再交渉の候補
- 既出: 新規(人物は memory 既知)
- 出典: https://metadatalab.net/

#### Fukuoka Growth Next(FGN、福岡市)
- 種別: その他(スタートアップ支援拠点)
- 中心人物: 福岡市
- 代表的な成果: 起業相談・支援プログラム・ワークスペース・イベント
- 窓口・発信: https://growth-next.com/
- 活動状況: サイトから 2026-10 以降のイベントや AI 関連プログラムは取得できず(未確認)
- 渋谷シムへの使いどころ: (8) 天神版デモや福岡県未来 IT アワードに向けた地元の行政・企業とのつながり。既に関わりがある
- 既出: 新規
- 出典: https://growth-next.com/

---

### C. 担当範囲で見つからなかった/確認できなかったもの
- **WebSearch の上限に達したため未調査**: 倉橋節也(筑波)、山本仁志、瀧川裕貴、笹原和俊の 2026 年の LLM エージェント研究(検索では LLM との関連が出てこなかった)/日立・NEC・NTT 人間情報研・tsuzumi の社会シミュレーション事例/マクロミルの合成調査/日本の合成顧客スタートアップ(AI ペルソナ SaaS 各社)/九工大・九大マス・フォア・インダストリ研究所の ABM 研究者/福岡の AI コミュニティ(connpass は robots 制限で取得不可)/AUTOMATA・Singulabo の公式サイト(robots 制限)。
- **JSAI 公式(ai-gakkai.or.jp)は robots 制限**で、JSAI2027 の日程、SIG(社会における AI、SIG-FIN など)の 2026-10 以降の研究会、ジュニアセッションの有無を確認できなかった。
- **中高生情報学研究コンテスト(IPSJ)の締切・条件**、NLP2027 の高校生参加費、CSSJ2027 の申込締切は未掲載または取得できず。
- 池上研の 2026 年の新論文、Alternative Machine の 2025〜26 年の活動、鳥海研の LLM エージェント論文の具体名(研究室サイトは robots 制限)は未確認。
- Zenn の「生成エージェント」トピックと Qiita の検索は API の制約でほぼ取得できず(社会シミュレーショントピックは 2 件のみ)。

