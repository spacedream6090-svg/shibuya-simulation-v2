# O'Gara, Kerr, Klein, Binois, Garnett & Hammond 2025 — Improving Policy-Oriented Agent-Based Modeling with History Matching: A Case Study

- リンク: https://arxiv.org/abs/2501.00616 | 分野: 統計学・因果推論 #23 / ABM 方法論 #21 / 不確実性定量化 #22 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが WebFetch で PDF を取得し、システム python の pymupdf で全 24 頁の本文抽出。手法節・表 1・ソフトウェア節を逐語照合)。**親未確認**。arXiv:2501.00616・**v1 提出 2024-12-31**・CC BY 4.0・stat.AP。**残務台帳 R-14 の「History Matching for ABM(2501.00616)」はこのメモで閉じる**。

## 主張(claim)

高解像度 ABM の較正は計算費用で詰まる。**代理モデル(emulator)+ history matching** で「データと合いそうにないパラメタ領域を波ごとに削る」と、実機なら年単位の探索が数分で済む。

逐語(≤125 字):
- "**History matching is a technique that uses emulator models to rule out regions of the parameter space which are unlikely to match empirical data**"

## 機構(mechanism)— 非含意度で削る

1. **生成過程を宣言**: Y = g(θ) + σ²_MD(θ) + σ²_ε(σ²_MD = **モデル乖離**、σ²_ε = 観測雑音)。
2. **代理を当てる**: 異分散ガウス過程(hetGP)。設計点ごとに**反復**を取って平均と分散を別々に推定。
3. **非含意度(implausibility)**: |Y − μ̂_g(θ)| / √(σ̂²_g(θ) + σ̂²_MD + σ̂²_ε) ≥ I(θ) なら**除外**。
4. **多出力は最大値**: "we use the maximum implausibility measure across Q outputs I_M(θ) = max_{i∈Q} I_i(θ)"
5. 残った点 = "**Not Yet Ruled Out (NROY)**"。次の波はその中に設計点を撒き直し(maximin)、閾値を締める。
6. **NROY が空になったら**: "this would require revisiting both the model itself and the model discrepancy"(= モデルそのものを疑う合図)。

**閾値 3 の出所**(逐語): "**A common cutoff value I(θ) is 3, inspired from (Pukelsheim 1994) showing that at least 95% of any continuous unimodal distribution is contained within three standard deviations**"

## 効く箇所(seam)

- **σ²_MD が「歪む場所の宣言」の数量形**。本論文は σ_MD = 0 と置いている(「原著の多数の軌跡が経験データを満たしたから」)。**我々は 0 と置けない**(D-72 ①⑦ の法規上限の一律適用・D-67 の昼間 1.13×・D-52 の廃棄)。分母が大きい = **削られにくい** = NROY が広く残る。逆に言えば、**「歪む場所」を数量化しないと history matching が使えない**。
- 出力の選び方が我々の H1〜H5 と同型(**少数のスカラーを時刻で切る**)。本論文は累積診断数・累積死亡数・活動感染数を 3〜4 時点で。
- **反復数の理由が明快**: "model replicates are essential to separate signal from noise" → 20〜25 反復/設計点。**我々の seed 3 本はこの用途には足りない**。
- **代理とセットでしか成立しない**——D-70 (c)(15 分/シミュ日の低忠実度層)の前提条件。

## 「結論でなく機構として」の入れ方

- **借りない**: Covasim・hetGPy・ABC の実装。
- **借りる**: (1) **非含意度の式の形**(分母に「モデル乖離 + 観測誤差」を足す)——**「歪む場所」を分母に入れる**という発想は、我々の宣言を初めて計算に使える形にする。(2) **多出力は最大値を取る**(H1〜H5 のうち最悪の指標で判定する=Bonferroni 的な保守性)。(3) **波を重ねて閾値を締める**(3.0 → 2.7 → 2.5)。(4) **NROY が空 = モデルを疑う**という出口条件。

## 数値(出所つき)

- 1 ラン **約 30 秒**(Covasim)。
- 第 1 波: maximin ラテン超方格 **50 設計点 × 25 反復**。第 2 波以降: **50 × 20 反復**。
- 代理面の評価格子: **40⁴ = 2,560,000 点**。実機なら "**nearly 2.5 years of computing time**" が "**a matter of minutes**"。
- **表 1(4 波)**: 閾値 I(θ) = 3.0 / 3.0 / 2.7 / 2.5、NROY 標本 184,974 / 142,813 / 54,848 / **21,114**、パラメタ体積比 **7.23% / 5.58% / 2.14% / 0.82%**。
- 反復数の選び方: "**wanting at least at least 10 parameter locations per**"(原文ママ)…"we found that **20 replicates** modeled the variance more robustly"。
- ABC: 5 鎖 × 2,000 = **10,000 事後標本**・ε=5。
- 比較対象(原著の較正): 不一致度の閾値 30 で **15,092 本**が合格(+ 移動データなしで 8,821 本)。

## コスト/スケール含意

- **1 波 = 50 × 20 = 1,000 ラン**。
  - 1 ラン 30 秒 → 8.3 h/波(本論文)。
  - **我々 39 万体 9.17 h/ラン → 9,170 h/波 = 382 日。1 波も回せない**。
  - **我々 5,000 体 0.5 h/ラン → 500 h/波 = 20.8 日**。これでも 4 波は無理。
- → **代理層(surrogate)が先。それ無しに history matching は着手不能**。

## 批判・限界

- **σ_MD = 0 という強い仮定**を置いている(自分で「専門家聴取や別モデルで推定できる」とも書いている)。
- 事例 1 本(Covasim / シアトル都市圏)。一般化の主張は弱い。
- 代理は 4 パラメタのみ。**k=122 のような高次元では格子評価(40⁴)が成立しない**。
- 反復数 20 の根拠は「分散がより頑健にモデル化できた」という経験則(事前の計算はしていない)。
- arXiv v1 のみ・査読の有無は頁に記載なし。

## 関連

[[stats__myllymaki2024_global-envelopes]](曲線の帯という別解)・Dyer et al. 2023 arXiv:2312.11158(代理を作るときの禁則=介入下で学習せよ。lit 未作成・答申 §1-3(a) に記載)・[[stats__tenbroeke2016_sensitivity-abm]]・`../v2-statistics-causal-research.md` §1-3(c)・計器盤 G-8
