# Abootorabi et al. 2026 — Steering Geometry: Validating Human Value Geometry in LLM Steering Space

- リンク: https://arxiv.org/abs/2609.06289 | 分野: 自然言語処理 #27 / 人格心理学 #13 | 重要度: **P2**(この repo は「中をいじる道」を採らないため)
- **一次確認**: **実読**(2026-09-16・サブが WebFetch で abs + `arxiv.org/html/2609.06289v1` 本文を取得。**付録 D のスケール別数値は切れている**)。**親未確認**。v1 のみ(2026-09-05)。Comments 欄「**Accepted to EMNLP 2026 Main Conference (top 15.4%)**」。著者 Mohammad Mahdi Abootorabi 他 7 名。

## 主張(claim)

活性化ステアリングのベクトルが、**人間の価値の理論的構造(Schwartz の円環)を再現するか**を測った。①**分布駆動の手法は再現する**(Spearman ρ 最大 0.51・p<10⁻¹³)②**行動中心の手法は同じくらい操作できるのに幾何は再現しない** ③**幾何の忠実度はモデル規模とともに上がるが、指示チューニング後に落ちる**。

## R-2 の問い「指示微調整後の劣化の程度」

**Table 1(Qwen3.5-9B・理論順位相関 ρ_T・Spearman・括弧は p)**

| 手法 | Base ρ_T | Instruct ρ_T | 落差 |
|---|---|---|---|
| 生の活性空間 | 0.2228 (2.0e-3) | 0.1253 (8.5e-2) | −0.098 |
| OPT | 0.1138 (1.2e-1) | 0.0615 (4.0e-1) | −0.052 |
| Cold-Steer (FD) | 0.0265 (7.2e-1) | **−0.0568** (4.4e-1) | −0.083 |
| BiPO | 0.1188 (1.0e-1) | **−0.0104** (8.9e-1) | −0.129 |
| ODESteer | 0.2730 (1.4e-4) | 0.2055 (3.7e-3) | −0.068 |
| SphericalSteer | 0.3962 (1.5e-8) | 0.2048 (4.6e-3) | **−0.191** |
| CAA | 0.4606 (2.3e-11) | 0.2351 (1.1e-3) | **−0.226** |
| SAS | **0.5069** (8.5e-14) | 0.3256 (4.6e-6) | **−0.181** |

- 他の指標も同じ向き: SAS の r_T 0.5061 → 0.3331、ρ_H 0.3910 → 0.2058。
- 逐語(≤125 字): 「**All methods show consistent degradation when moving from base to instruction-tuned models (Table 1).**」/ 抄録「**Geometric fidelity improves with model scale but drops after instruction tuning.**」。著者はこれを「value geometry drift」と呼ぶ。
- **base vs instruct の比較は Qwen3.5-9B 1 モデルだけ**(Llama3.1-8B は付録 C・Table 6 で base のみ)。→ **「製品版は崩れている」を一般化する根拠は 1 モデル分しかない。**

## その他の数値

- 規模則(Fig. 3・いずれも CAA・逐語 ≤125 字): 「**ρT rises sharply from Falcon-7B (0.20) to Mistral-7B (0.32), Llama-3.1-8B (0.37), and Qwen3.5-9B (0.46)**」。能力との乖離: 「**Gemma-4-31B, despite being one of the strongest open models, achieves a lower ρT (0.38) than Qwen3.5-4B (0.41)**」。
- ベンチ: Schwartz の 20 価値・約 **26K 標本**。
- 指標の定義(§3.3.1・付録 H): 20 価値それぞれのステアリングベクトルを**平均中心化**(20 本の平均を引く)・単位正規化 → 経験行列 E = 対ごとのコサイン類似度。理論行列 **T_bb′ = cos(min(\|b−b′\|, 20−\|b−b′\|) × 18°)**(円環の角度)。**ρ_T** = E と T の Spearman(順序)/ **r_T** = Pearson(線形)/ **ρ_H** = 4 段の階層距離(1/2/5/10)との相関 / **Δpol** = 同族内平均類似度 − 対立群平均類似度。

## 効く箇所(seam)

**該当せず(採らない道の確認)。** この repo は「状態と集約はエンジン、意思決定と発話だけ LLM」の分業なので、**活性化に介入する道は憲法上採らない**。本論文の値は**その判断を裏づける材料**として置く。

副次的に効く点が 1 つある: **この repo は Qwen3-8B INT8 の instruct 版を使っている**。本論文が示すのは「instruct 後に価値の幾何が壊れる」ことなので、**個体差を「価値」で作ろうとする設計(第2陣の候補)は instruct モデルでは弱い**という予測が立つ。多様性は LLM から自ずと出す方針(ユーザー選好)と整合するが、**価値ベースの個体差は避けるべき**という含意がある。

## 「結論でなく機構として」の入れ方

借りるものは**ほぼ無い**。1 つだけ: **「理論の構造を行列にして、実測の構造との順位相関を取る」という検証の形**。この repo で言えば、**5 エリア × 24 時間の構造を理論(PT 調査の活動連鎖)と実測(KDDI)で行列化し、順位相関で見る**という物差しの作り方。H1 の JSD とは別の角度。

## コスト/スケール含意

26K 標本 × 20 価値 × 8 手法 × 複数モデル。**この repo では回さない**。

## 批判・限界

- **base vs instruct が 1 モデル**。一般化の根拠が薄い。
- 「幾何の忠実度が高い = 良い」は**Schwartz 理論が正しい**という前提の上にある。
- ρ_T 0.51 は「最大」であって強くはない(説明率 26%)。
- 有志の要約「動かすと壊れる」は**本論文の主張ではない**(壊れているのは指示チューニング後の幾何であって、ステアリング操作の副作用ではない)。親の読み(#17 △)が正しい。

## 関連

[[nlp__choi2025_identity-drift]] ・ [[nlp__taubenfeld2024_debate-biases]] ・ `../v2-llm-social-sim-timeline-seed.md` #17
