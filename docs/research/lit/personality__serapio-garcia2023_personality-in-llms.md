# Serapio-García et al. 2023 — Personality Traits in Large Language Models

- リンク: https://arxiv.org/abs/2307.00184 (コード: https://github.com/google-deepmind/personality_in_llms) | 分野: 自然言語処理・機械学習 #27 / 人格心理学 #13 | 重要度: **P2**
- **一次確認**: **抄録のみ**(2026-09-17・サブが arXiv 抄録ページを実読。**本文 PDF は未取得**)。**以下の「数値」節は検索要約由来=二次**。**親未確認**。arXiv:2307.00184 v1 2023-07-01 / v4 2025-03-11・CC BY 4.0。著者: Greg Serapio-García, Mustafa Safdari, Clément Crepy, Luning Sun, Stephen Fitz, Peter Romero, Marwa Abdulhai, Aleksandra Faust, Maja Matarić。

## 主張(claim)

LLM に人間の性格検査を実施し、**心理測定的に妥当・信頼できる形で測る方法論**と、**生成テキストの性格を目標次元へ形づくる方法論**を提案。18 モデルに適用。要旨の 3 点:
1. 特定のプロンプト構成のもとでは、一部の LLM の出力における性格測定は信頼性・妥当性がある。
2. 信頼性・妥当性の証拠は「**大きく、instruction fine-tuned なモデルほど強い**」。
3. LLM 出力の性格は「**望む次元に沿って形づくり、特定の性格プロファイルを模倣させられる**」。

## 数値(**すべて二次=検索要約由来・親と本メモ作成者のいずれも本文未確認**)

- 18 モデル。Flan-PaLM 62B / Flan-PaLMChilla 62B は信頼性指標が平均 0.90 台後半。**PaLM 62B(事前学習のみ)は −0.55 ≤ α ≤ 0.67 と不安定**。Mistral 7B Instruct は base の約 2.7 倍の信頼性。
- 弁別的妥当性はモデル規模とともに上昇(Flan-PaLM 8B で 0.23 → 540B で 0.51)。
- 基準関連妥当性: Flan-PaLM 540B で PVQ-RR の ACHV / CONF / SCRT に対し 0.74 / 0.73 / 0.59。
- **単一特性の形成**: 目標順位と観測 IPIP-NEO 得点の Spearman ρ ≥ 0.90。大モデルは最低/最高プロンプト間の分布距離 Δs ≥ 3.00。
- **並行多特性の形成は難しい**。大モデルでも平均 2.5 点の移動。
- 外向性は小モデルでも形成しやすい。**下流の生成課題(SNS 投稿)では、開放性だけ目標との相関が中程度どまり**(n=450/特性・すべて p<0.0001)。
- 後に *Nature Machine Intelligence* に "A psychometric framework for evaluating and shaping personality traits in large language models"(s42256-025-01115-6)として公刊されたとの情報があるが、**arXiv ページには掲載情報が無く未確認**。

## 機構(mechanism)

指示チューニングが、**プロンプトで指定された性格を出力の表層に反映させる能力**を作る。規模が大きいほど、その反映が一貫する。

## 効く箇所(seam)

- 「LLM に性格は付けられる」側の代表として引く。**ただし [[personality__han2025_llm-personality-illusion]] と [[personality__contreras2026_llm-selfreport-behavior-gap]] が示すとおり、付くのは自己申告と文体であって行動ではない**。この 3 本は**セットで引く**。
- 本 repo は 8B 級・instruction-tuned を使う。本論文の傾向からは「小さいほど不安定」側。**性格をプロンプトに書く路線を採らない判断を補強する**。

## 「結論でなく機構として」の入れ方

「形づくれる」を理由に性格語をプロンプトに書かない。**形づくられるのは測定値と文体であり、我々が照合するのは行動の分布**である、という区別を持つ。

## コスト/スケール含意

18 モデル × 複数プロンプト構成の心理測定は、本 repo では再現しない(艦隊時間の使い道として優先度が低い)。

## 批判・限界

1. **本メモの数値はすべて二次**。使う前に PDF を pymupdf で抽出して確認すること(答申 §7-1 K-7)。
2. 測定対象は**自己申告(IPIP-NEO への回答)**であって行動ではない。
3. 評価対象モデルが Google 系に偏る。
4. 書式・選択肢順への感受性(Gupta et al. 2024 ほか)を統制しているかは未確認。

## 関連

- [[personality__han2025_llm-personality-illusion]]
- [[personality__contreras2026_llm-selfreport-behavior-gap]]
- [[nlp__choi2025_identity-drift]] / [[nlp__taubenfeld2024_debate-biases]]
- 答申 [v2-personality-traits-research](../v2-personality-traits-research.md) §3-1
