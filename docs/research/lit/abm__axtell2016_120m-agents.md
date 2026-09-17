# Axtell 2016 — 120 Million Agents Self-Organize into 6 Million Firms: A Model of the U.S. Private Sector

- リンク: AAMAS 2016 予稿集 pp.806–816(IFAAMAS)。**DOI/ACM DL の恒久リンクは未確認** | 分野: ABM方法論 #21 / 計算機科学(並列)#28 / SFCマクロ経済学 #10 | 重要度: **P0**
- **一次確認**: **実読(サブ・pymupdf 11 頁)・親未確認**(2026-09-17)。取得先は公開アーカイブ `cmepr.gmu.edu/wp-content/uploads/2017/09/Axtell-AAMAS-p806.pdf`(**正規ドメインではない**)。Proceedings of the 15th International Conference on Autonomous Agents and Multiagent Systems (AAMAS 2016), May 9–13, 2016, Singapore。単著。

## 主張(claim)

**米国民間部門を 1 対 1 の実寸(約 1 億 2,000 万体)で回した**エージェントモデル。外生ショックを入れずに、企業規模・年齢・成長率・勤続年数・労働移動など**2 ダース近い経験的事実**を同時に再現する。

## 数値(出所つき・本メモの核)

### 規模と計算資源(§4 "REALIZING 120 MILLION AGENTS"・逐語 ≤125 字)

- 体数: 「**some 120 million agents**」(要旨)。対応する実世界の値は本文 §1 で「over the last decade the U.S. private sector workforce has ranged from 115 to 120 million employees」。企業数 570〜600 万。
- 却下された計算機構成: 「**Many HPC architectures turns out to not be useful, such as cloud computing, running a single instance of the model on multiple machines, vector supercomputers and even GPUs.**」理由は「the dense interactions between agents in this model make inter-process communication voluminous and, because it is slow, prohibitive」。GPU/ベクトル機は「**computational artifacts that had no meaningful interpretation**」を生んだ。
- 採った構成: 「**a single dedicated workstation, with 32 cores and 256 GB of RAM, proved the most successful architecture**」。実装は最適化 C/C++ + スレッドライブラリ。
- 所要時間: 「**reaches a near steady-state condition from the initial conditions of table 1 in approximately half a day a day of wall time**」(原文ママ・"half a day a day" は誤植と思われる)。
- 較正: 「**the parameter optimization that led to the specification of table 1 was obtained heuristically**」= **自動最適化ではなく手作業**。理由は「Given the expense of these model runs」。

### 較正と照合の量(§3 末尾・逐語 ≤125 字)

「**calibrated to data using approximately a dozen parameters (table 1), has been shown here to closely reproduce nearly two dozen empirical facts concerning the U.S. economy**」

図は 27 枚。照合対象として本文に図がある量: 企業数の時系列・平均企業規模・努力水準・効用・月次の職-職移動/雇用創出・**企業規模分布(従業員数/産出)**・労働生産性(米国 Census データと突合)・**企業年齢分布(米国データ 2000–2011)**・企業寿命分布・生存確率・成長率 g の分布と規模/年齢依存・g の標準偏差の規模/年齢依存・賃金分布・**勤続年数(指数分布)**・**労働フロー網の次数分布**(フィンランドとメキシコのデータと突合)。

### 実世界側の回転率(§1)

月あたり約 300 万人が転職(40 人に 1 人)、年あたり 570〜600 万社のうち月 10 万社が退出し同数が開業(60 社に 1 社)。

## 機構(mechanism)

規模に関する収穫逓増のもとでの**連合形成(coalition formation)**モデル。産出 `O(E) = aE + bE^β, β > 1`。等分配・Cobb-Douglas 選好・努力は観測不能。大企業では報酬が努力に鈍感になりフリーライドが生じ、生産的な個体が離脱して企業は衰退する。**ナッシュ均衡は十分大きな連合では動的に不安定**。個体水準は恒常的な非均衡、集計水準は定常に近づく。

## 効く箇所(seam)

- **「1 対 1 の実寸」は古典 ABM 側では 2016 年に既に達成されている**(1.2 億体・ワークステーション 1 台・半日)。40 万体という規模そのものは新規性の根拠にならない。**新規性は「全個体を LLM で駆動し全入出力を保存する」という質の側にしか置けない**([[compute__matsim2020_hermes]] の 730 万体、[[mas__yang2024_oasis]] の 100 万体と並べて読む)。
- **費用の桁の対比**: 1.2 億体・半日・CPU 32 コア(古典)対 100 万体・1 step 18 時間・A100 27 枚(OASIS)。**体あたり・step あたりで 5〜6 桁の差**がある(正確な正規化は単位が揃わないので親が計算すること)。
- **「約 12 母数で約 24 の事実」**は、パターン台帳ゲートの**比の目安**を与える唯一の実寸級の先行。母数より照合するパターンのほうが多い、という関係([[abm__grimm-railsback2012_pom-multiscope]] の多重照合の実装形)。
- **較正が手作業(heuristic)**と正直に書かれている = 実寸級では自動較正が回らないことの先例。この repo が history matching を採るなら代理モデルが要る([[stats__ogara2025_history-matching-abm]])という判断と整合。
- **GPU/ベクトル機が「意味のない計算アーティファクト」を生んだ**という報告は、同期実行が経路依存の系を歪めるという警告。この repo の決定論設計に効く。

## 「結論でなく機構として」の入れ方

- **借りない**: 連合形成の経済モデルそのもの。
- **借りる**: (1) **「母数の数 vs 照合する事実の数」を答申の頭に書く**。(2) **規模の主張は「実寸か」で書く**(最大かではなく)。(3) **計算機構成を却下理由つきで書く**(何が駄目だったか)。

## コスト/スケール含意

1.2 億体 × 定常到達まで ≈ 半日 / 32 コア・256 GB。**LLM を使わない ABM の実寸の値段はこの桁**。ここに LLM 推論を入れた瞬間に桁が変わる、というのがこの分野の分水嶺。

## 批判・限界

- **査読会議の予稿**(AAMAS は査読あり)。頁は 806–816。恒久 DOI は未確認。
- 「half a day a day」という誤植があり、**半日なのか 1 日なのか確定できない**=空欄。
- **seed 数・反復数の記載が見当たらない**(取得範囲)。分布の再現を主張しているが、ラン間分散の報告は未確認。
- 較正が heuristic で、手続きが再現できない。
- 比較対象の米国データの出所(Census/BDS/QCEW の別)は図の説明にしか無く、**本文で明示されていない**=空欄。

## 関連

[[compute__matsim2020_hermes]] ・ [[mas__yang2024_oasis]] ・ [[abm__grimm-railsback2012_pom-multiscope]] ・ [[stats__ogara2025_history-matching-abm]] ・ `../v2-classical-vs-llm-simulation-research.md`
