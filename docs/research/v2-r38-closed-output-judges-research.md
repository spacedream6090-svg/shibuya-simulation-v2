# R-38 答申: 「閉じた出力」の判断層に何を置けるか(分類器の系譜 / logprob / cascade / 社会シミュ先行)

<!-- hdr:v1 -->
- **一次確認: サブが実読(親未確認)**
- **分野**: 自然言語処理・機械学習 #27 / LLM サービング #31 / ABM方法論 #21 | **重要度**: P0(判断層の実装候補を決めるため)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)
- **担当**: リサーチサブ(Opus 5)・**子サブ不使用**・Web は**読むだけ**(ダウンロード実行なし)・**コミットせず**・**台帳を編集せず**
- **制約の前提**(2026-09-22 確定): GPU サーバー喪失。使えるのは **CPU** と **RTX 5070(12 GB)1 枚**のみ。§3 の比較表に評価軸として入れた。 **(第254 撤回・ユーザー指示 09-23「計算資源は設計判断の軸にしない」)**: §3 の「RTX 5070 で動くか」列は**資源の事実としてのみ残し、候補の順位には使わない**。
- **依頼外**: Jev / Open-Jev(TypeSafe 社)は**親の担当**。本答申では調査していない(§5 参照)。

> **設計は書かない**。事実と、事実から直接出る含意だけを書く。

確認の別: **原典**=論文/公式ドキュメントの本文を自分で読んだ / **カード**=HuggingFace の公式モデルカードを読んだ / **抄録**=abs ページのみ / **二次**=検索要約経由(本文未読) / **未読**=到達できず。

---

> **親検収(2026-09-23・第253・Fable 5.1)**: サブの申告どおり原典に当たり、**結論を変える 4 件を親が逐語で確認した**。
> - **✓ GenWorld(arXiv:2606.27650)**: abs で 題名「GenWorld: Empirically Grounded Urban Simulation Infrastructure for Scalable LLM-Agent Studies」・投稿 2026-06-26・「grounds **196,608** synthetic residents」「**Higashihiroshima, Japan**」「**offline compilation of LLM-derived decision signals into lookup policies**」を確認。本文(HTML v1)で **教師 = Gemma 3 27B**(「a single teacher model (Gemma 3 27B)」)・**K=10–30**・意図空間「fixed to {home, duty, leisure, maintenance}」・**「Python lookup achieves 1.85M queries/s (0.54μs per query)」「Intel Core i5-14600K CPU」**・「N=200,000 agents … T=96 and thus **1.92×10^7 calls** for a single day」・**端から端の高速化は未報告**(「profiling under varying agent counts is **ongoing work**」)を逐語確認。**サブの記述と一致**。
> - **✓ Light Society(arXiv:2506.12078)**: abs で 題名「Modeling Earth-Scale Human-Like Societies with One Billion Agents」・著者 13 名・**v1 2025-06-07 / v2 2026-06-28**・「**mixture-of-models engine that combines full LLMs with distilled surrogates**」「over **one billion** agents」を確認。**ただし routing policies(all-LLM / all-surrogate / per-sample weighted)・macro F1 0.84〜0.85・教師 Gemini 2.0 Flash は abstract に無い=本文の主張**で、**親は本文を未確認**(サブは v2 実読と申告)。設計書に写すときは親が本文を読むこと。
> - **✓ vLLM の logprob(最重要)**: 公式 FAQ に逐語 **「vLLM does not guarantee stable log probabilities (logprobs) for the output tokens.」** を確認。原因は「numerical instability in Torch operations」と**バッチの組み方の違い**で、「can lead to slightly different logit/logprob values at each step」→「Once a different token is sampled, further divergence is likely」。緩和は float32・float16・request seeds のみで、**完全な決定論・bit 再現は謳っていない**。→ ~~**v2 の受入「同 seed で bit 一致」と正面から衝突する**~~ **第254 訂正(親)**: v2 の艦隊は `VLLM_BATCH_INVARIANT=1` で起動し(検証ランは manifest 規則 (c) で必須)、[B14](../bench/b14_batch_invariance/README.md)(09-07・A5000・vLLM 0.28.0・8B INT8)で **logprobs の一致 32/32(OFF では 0/32)**を実測済み。FAQ の非保証は既定モードの話で、**v2 の構成では衝突しない**。第253 の判定は親が既存ベンチを確認せずに書いた誤り(§2-4)。§5 の含意もこの訂正で読むこと。
> - **✓ 日本語ゼロショットの実在**: `Formzu/bert-base-japanese-jsnli` のモデルカードで **JSNLI 評価 Accuracy 0.9288**・**cc-by-sa-4.0**・base `cl-tohoku/bert-base-japanese-v2`・zero-shot パイプラインの例と **hypothesis_template「この例は{}です。」** を逐語確認。**サブの記述と一致**。
> - **△ 未確認 1 件**: `akiFQC/bert-base-japanese-v3-nli-jsnli-jnli-jsick`(JNLI val 0.914)は **HF が HTTP 401 を返し親は読めなかった**。モデルが存在しないという意味ではない=**親未確認**として扱う。
>
> **サブの確認依頼 5 件への親の回答**: ① 「RTX 5070 で動く」列が全て判定(実測ゼロ)なのは**正しい扱い**。そのまま。② vLLM の sm_120 対応が公式から確認できないのも**正しい**(推測で埋めない)。③ **R-39 の線引きの引き直しは妥当**(§5 で採用)。④ Light Society の「5 手法 F1 横並び」は**本文未確認なので設計には使わない**(参考に留める)。⑤ **PMI_DC が常に良いわけではない**という注意は正しい=採用。

## 1. 一次確認の等級と調べ方

**等級: B**(出典あり・実読多数・空欄を明示)。**親は未確認**。

### 1-1. 実読したもの(本文または公式ドキュメント本体)

| # | 対象 | 到達方法 | 何を取ったか |
|---|---|---|---|
| 1 | Yin, Hay & Roth 2019(arXiv:1909.00161) | ar5iv HTML | Table 6/7 の label-fully-unseen 数値・使った含意モデル |
| 2 | Tunstall ら 2022 SetFit(arXiv:2209.11055v1) | arXiv HTML | Table 1〜5・学習時間/費用・多言語 MARC(日本語含む) |
| 3 | Sanh ら 2019 DistilBERT(arXiv:1910.01108) | ar5iv HTML | Table 1/3 のパラメータ数・CPU 推論秒数・GLUE |
| 4 | Holtzman ら 2021(arXiv:2104.08315 / ACL D 2021.emnlp-main.564) | ar5iv HTML + ACL | Table 1/2/6 の PMI_DC 数値・逆に悪化する列 |
| 5 | Xiong ら ICLR 2024(arXiv:2306.13063v1) | arXiv HTML | Table 1 の ECE / AUROC(口頭 confidence の過信) |
| 6 | Chen, Zaharia & Zou 2023 FrugalGPT(arXiv:2305.05176) | ar5iv HTML | scoring function = DistilBERT・閾値 0.96/0.37・Table 1/3 |
| 7 | Ong ら 2024 RouteLLM(arXiv:2406.18665v4) | arXiv HTML | 4 ルータの構成・Table 6 の節約率・Table 7 のルータ自身の費用 |
| 8 | Gupta ら 2024(arXiv:2404.10136v1) | arXiv HTML | Chow-* の長さバイアス・学習 deferral の AUC-DF |
| 9 | Chopra ら 2024 AgentTorch/LLM archetypes(arXiv:2409.10568v3) | arXiv HTML | 8.4M 体・約 400 クエリ・Table 1 の MSE |
| 10 | Kaiya ら 2023 Lyfe Agents(arXiv:2310.02172) | arXiv HTML | option-action の実体・$0.5/体/人時 |
| 11 | Light Society(arXiv:2506.12078v2) | arXiv HTML | 5 種の代理モデルの F1・ルーティング方式・lookup 表の形 |
| 12 | GenWorld(arXiv:2606.27650) | arXiv HTML | K=10〜30 の Monte Carlo 蒸留・lookup 1.85M queries/s |
| 13 | APS(arXiv:2605.27419v1) | arXiv HTML | 適応予算配分・381.1 倍・JSD 0.094・LS-Surrogate の数値 |
| 14 | vLLM 公式: structured outputs / pooling models / FAQ / batch invariance | docs.vllm.ai | choice の API 名・backend・logprob 非保証・VLLM_BATCH_INVARIANT |
| 15 | PyTorch 公式 Reproducibility(2.14)/ PyTorch 2.7 リリースブログ | docs.pytorch.org / pytorch.org | 「完全な再現は保証しない」・Blackwell は 2.7 で prototype 対応 |
| 16 | sbert.net 公式(Cross-Encoder 応用) | sbert.net | bi/cross の使い分け・65 時間 vs 5 秒 |
| 17 | 公式モデルカード 6 本 | huggingface.co | bart-large-mnli / mDeBERTa-xnli / akiFQC / Formzu / ruri-v3-310m / Qwen3-0.6B |
| 18 | NVIDIA 公式 CUDA GPUs 一覧 | developer.nvidia.com | RTX 5070 = compute capability **12.0** |

### 1-2. 抄録のみ・本文未読

| 対象 | 状態 |
|---|---|
| Yue ら 2024(arXiv:2310.03094・LLM cascade with Mixture of Thoughts) | **抄録のみ**。「GPT-4 単独の 40% の費用」は抄録の逐語。データセット別の数値は未取得 |
| Poor Man's Agentic Modeling(arXiv:2608.11215) | **抄録のみ**。本文の数値(N・誤差の傾き)は未取得 |
| Should LLM Agents Decide in Social Simulations?(arXiv:2606.12369) | **抄録のみ**。JSD の実数値は未取得 |
| Park ら 2024 Grammar-Aligned Decoding(arXiv:2405.21047) | **抄録+検索要約**。本文の実験数値は未取得 |
| Beurer-Kellner ら 2024 DOMINO(arXiv:2403.06988) | **抄録+検索要約**。本文の精度低下の実数値は未取得 |

### 1-3. できなかったこと

- **RTX 5070(12 GB)での実測値はどこにも無い**。本答申の「動くか」列は、原典が書いた必要 VRAM / 必要 GPU と、NVIDIA・PyTorch・vLLM の公式要件からの**判定**であって、**実測ではない**。
- 日本語での SetFit / NLI ゼロショットの**ベンチマーク数値**は、SetFit 論文の MARC(日本語 MAE×100 = 93.2)と akiFQC の JNLI 0.914、Formzu の JSNLI 0.9288 以外に見つからなかった。**「渋谷の行動選択」に近いタスクでの日本語数値はゼロ**。
- Light Society の**絶対トークン数・GPU 台数・金額**は本文に無い(図のみ)。

---

## 2. Q1〜Q4 の答

### Q1 閉じた出力の分類器の系譜

#### 2-1-1. NLI ゼロショット分類(元祖と現在)

**Yin, Hay & Roth 2019**(EMNLP 2019, pp.3914–3923)。仕組みは「分類したい文を **premise**、ラベル文字列から作った仮説を **hypothesis** として含意判定に帰着させる」。含意モデルは **BERT-base** を **MNLI / GLUE RTE / FEVER** それぞれで学習した 3 本と、その **ensemble**(softmax 後の確率を足して再 softmax)。仮説の作り方は label 名(word)/ WordNet 定義(def)/ 両方(comb)。

**Table 6「Label-fully-unseen evaluation」**(topic は accuracy、emotion / situation は label-wise weighted F1。逐語):

| 方法 | topic | emotion | situation | 合計 |
|---|---|---|---|---|
| Majority | 10.0 | 5.9 | 11.0 | 26.9 |
| Word2Vec | 35.7 | 6.9 | 15.6 | 58.2 |
| ESA | 28.6 | 8.0 | 26.0 | 62.6 |
| Wiki-based | 52.1 | 21.2 | 27.7 | 101.0 |
| entail. MNLI | 37.9 | 22.3 | 15.4 | 75.6 |
| entail. FEVER | 40.1 | 24.7 | 21.0 | 85.8 |
| entail. RTE | 43.8 | 12.6 | 37.2 | 93.6 |
| **ensemble** | **45.7** | **25.2** | **38.0** | **108.9** |

出典 <https://aclanthology.org/D19-1404/> / <https://arxiv.org/abs/1909.00161>(ar5iv 本文実読)。

**含意(事実のみ)**: **学習データを一切見ないゼロショットの絶対精度は低い**。topic(10 ラベル)で 45.7%、emotion で F1 25.2。論文自身が fully-unseen では RTE > FEVER > MNLI で、fine-tune 後の partially-unseen とは**順序が逆**になると報告している。つまり「どの NLI コーパスで学習した含意モデルが良いか」は用途で入れ替わる。

**その後の代表実装**:

| 実装 | パラメータ | ライセンス | 学習 | 報告精度 | 出典 |
|---|---|---|---|---|---|
| `facebook/bart-large-mnli` | 0.4B | MIT | MNLI | **カードに精度の記載なし**(例示スコアのみ) | <https://huggingface.co/facebook/bart-large-mnli>(カード実読) |
| `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | 0.3B(約 279M) | MIT | multilingual-nli-26lang-2mil7(2,730,000 対)+ XNLI val、計 3,287,280 対。**微調整言語に `ja` を含む** | XNLI テスト: en 0.871 / de 0.824 / zh 0.803 / ur 0.744。**日本語の数値は無い**(XNLI に ja が無いため)。MNLI-m 0.857 | <https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7>(カード実読) |

カードの注意書きとして **mDeBERTa は fp16 非対応**と明記されている(実読)。

#### 2-1-2. 日本語で使えるか(実在する)

| モデル | ベース | 学習 | 報告精度 | パラメータ | ライセンス | 出典 |
|---|---|---|---|---|---|---|
| `akiFQC/bert-base-japanese-v3_nli-jsnli-jnli-jsick` | tohoku-nlp/bert-base-japanese-v3 | JSNLI + JNLI(train)+ JSICK(train)、SentenceTransformers **CrossEncoder** で学習 | **JGLUE-JNLI validation accuracy 0.914** | **0.1B** | CC-BY-SA-4.0 | <https://huggingface.co/akiFQC/bert-base-japanese-v3_nli-jsnli-jnli-jsick>(カード実読) |
| `Formzu/bert-base-japanese-jsnli` | cl-tohoku/bert-base-japanese-v2 | JSNLI | eval **Accuracy 0.9288**(Loss 0.2085・3 epoch) | カードに記載なし(BERT-base 相当) | CC-BY-SA-4.0 | <https://huggingface.co/Formzu/bert-base-japanese-jsnli>(カード実読) |

いずれも `pipeline("zero-shot-classification", ...)` が直接動く。**Formzu 側は `hypothesis_template="この例は{}です。"` を明示**(既定は英語テンプレートなので日本語では必ず差し替えが要る)。akiFQC のカードには hypothesis_template の記載が無く、コード例のモデル ID も別物(`_nli-jsnli`)を指している — **カード自体の不整合**(実読で確認)。

日本語の埋め込み側(SetFit の body に使える):

| モデル | #Params | #Params(埋め込み除く) | 次元 | 層 | **Avg. JMTEB** | ライセンス |
|---|---|---|---|---|---|---|
| `cl-nagoya/ruri-v3-30m` | 37M | 10M | 256 | 10 | 74.51 | Apache-2.0 |
| `cl-nagoya/ruri-v3-70m` | 70M | 31M | 384 | 13 | 75.48 | Apache-2.0 |
| `cl-nagoya/ruri-v3-130m` | 132M | 80M | 512 | 19 | 76.55 | Apache-2.0 |
| `cl-nagoya/ruri-v3-310m` | 315M | 236M | 768 | 25 | 77.24 | Apache-2.0 |

ベースは ModernBERT-ja、最大系列長 **8192**(v1/v2 は 512 だった)。論文は Tsukagoshi & Sasano 2024(arXiv:2409.07737)。出典 <https://huggingface.co/cl-nagoya/ruri-v3-310m>(カード実読)。

#### 2-1-3. SetFit(少数例の微調整)

**Tunstall ら 2022**(arXiv:2209.11055)。ST を対比学習で微調整 →埋め込み →分類ヘッド。プロンプト・verbalizer 不要。

**Table 1 のモデル**: SetFit-RoBERTa(all-roberta-large-v1)**355M** / SetFit-MPNet(paraphrase-mpnet-base-v2)**110M** / SetFit-MiniLM(paraphrase-MiniLM-L3-v2)**15M**。T-Few 11B は「80GB A100 が要る」ので実行していないと明記。

**Table 2 平均(†列)**:

| 方法 | N=8/class | N=64/class |
|---|---|---|
| FineTune(RoBERTa-Large) | 43.0 | 69.7 |
| Perfect | 48.7 | 72.7 |
| Adapet | 58.3 | 73.8 |
| T-Few 3B | 63.4 | 70.3 |
| **SetFit-MPNet** | **62.3** | **75.3** |
| FineTune(全データ) | 84.8 | — |

論文の逐語: N=64 で T-Few 3B を平均 5 点上回り、「**27 倍以上小さい**」。

**Table 5(費用)**:

| 方法 | 推論 FLOPs | 学習 FLOPs | 速度比 | スコア(N=8) |
|---|---|---|---|---|
| T-Few 3B | 1.6e11 | 3.9e15 | 1× | 63.4 |
| SetFit-MPNet | 8.3e9 | 2.0e14 | **19×** | 62.3 |
| SetFit-MiniLM | 1.3e9 | 3.2e13 | **123×** | 60.3 |

**§7.2 の実測(逐語相当)**: SetFit-MPNet は N=8 で **p3.2xlarge(16 GB GPU)上 約 30 秒・分割あたり約 $0.025**。T-Few 3B は **40 GB 以上の GPU メモリが必要**で約 **700 秒・約 $0.7**。チェックポイントは **70 MB(MiniLM)/ 420 MB(MPNet)** 対 T0-3B の **11.4 GB**。

**Table 4 多言語 MARC(MAE×100・低いほど良い)**: SetFit(multilingual MPNet)は各設定 86.6 / 86.4 / 88.3 で、FineTune(XLM-R base)121.9 / 117.7 / 117.2 と Adapet 134.9 / 152.0 / 146.0 を全設定で上回る。**言語別(en で学習した設定)では En 82.6・De 83.4・Fr 82.2・Es 83.4 に対し Ja 93.2・Zh 93.9** = **日本語は 6 言語中で最下位側**。

**Table 3 RAFT**: SetFit-RoBERTa 71.3(355M)> PET 69.6(235M)> SetFit-MPNet 66.9(110M)> GPT-3 62.7(**175B**)。人間 73.5、T-Few 11B 75.8。

実装側(公式): ライセンス **Apache-2.0**、既定ヘッドは scikit-learn の **LogisticRegression**(`use_differentiable_head=True` で Torch の `SetFitHead` に切替、`temperature` 引数あり)。**`predict_proba` が公式 API にある** — 戻りは `[INPUT_LENGTH, NUM_CLASSES]`(公式 doc 実読)。出典 <https://github.com/huggingface/setfit> / <https://huggingface.co/docs/setfit/en/reference/main>。

**含意**: SetFit は **3 つの質問の型のうち (i) 少数択 と (iii) yes/no を直接、(ii) 0〜1 の確率も `predict_proba` で**返せる、という点で判断層の要求に形が合う。ただし**日本語での品質は英語より明確に落ちる**(MARC の 93.2 vs En 82.6)ことが原典に出ている。

#### 2-1-4. cross-encoder と bi-encoder / 蒸留小型分類器

公式 Sentence Transformers ドキュメントの逐語:
- 「A Cross-Encoder does not produce a sentence embedding」
- 「Cross-Encoder achieve better performances than Bi-Encoders」だが「do not scale well for large datasets」
- 具体数値: **10,000 文をクラスタリングすると約 5,000 万ペア = cross-encoder で約 65 時間**。一方 **bi-encoder なら埋め込み計算が 5 秒**。
- 推奨パターン: bi-encoder で top-100 を取り、cross-encoder で再ランク。

出典 <https://sbert.net/examples/cross_encoder/applications/README.html>(実読)。

**判断層への含意(事実の含意)**: NLI ゼロショットは **cross-encoder**(文×ラベルの組を毎回まとめて通す)なので、**選択肢数 K に比例して前向き計算が K 回**増える。SetFit / bi-encoder は**文の埋め込み 1 回 + 線形ヘッド**なので K に依存しない。渋谷の (i) は 2〜10 択なので、cross-encoder なら **1 決定あたり 2〜10 回の BERT 前向き**になる。

**DistilBERT**(Sanh ら 2019, arXiv:1910.01108)**Table 3**(caption: "DistilBERT is significantly smaller while being constantly faster."):

| モデル | パラメータ | STS-B 全走査(CPU・batch 1・Xeon E5-2690 v3 @2.9GHz) |
|---|---|---|
| ELMo | 180M | 895 s |
| BERT-base | 110M | 668 s |
| **DistilBERT** | **66M** | **410 s** |

**Table 1**: GLUE dev 平均 BERT-base 79.5 / DistilBERT 77.0 = 「retains 97% of BERT performance」。端末実測は iPhone 7 Plus で「Excluding the tokenization step, DistilBERT is **71% faster** than BERT」、**端末上のモデルサイズ 207 MB**。**絶対のミリ秒値は論文に無い**。

---

### Q2 LLM の logprob から確率を取る方法

#### 2-2-1. Surface form competition(最大の落とし穴)

**Holtzman ら 2021**(EMNLP 2021, pp.7038–7051 / arXiv:2104.08315)。逐語の主張は「**different surface forms compete for probability mass, even if they represent the same underlying concept**」(例: "computer" と "PC")。確率の総量は固定なので、**選択肢に挙がっていない別の言い方**が質量を吸い、正解の選択肢のスコアが不当に下がる。

対策は **Domain Conditional PMI(PMI_DC)** = 候補を「そのタスクの文脈での事前の出やすさ」で割り戻す。

**Table 1(GPT-3 175B)の抜粋**(LM = 素の文字列確率 / Avg = 長さ正規化 / PMI_DC):

| データセット | LM | Avg | PMI_DC |
|---|---|---|---|
| OBQA | 33.2 | 43.8 | **58.0** |
| CQA | 61.0 | 57.4 | **66.7** |
| TREC | 47.2 | 25.4 | **58.4** |
| COPA | 85.2 | 82.8 | **89.2** |
| **ARC-E** | **73.5** | 67.0 | 63.3 ← **PMI_DC が悪化** |
| **HellaSwag** | 57.6 | **77.2** | 53.5 ← **PMI_DC が悪化** |
| **BoolQ** | 62.5 | 62.5 | 64.0(Unc 37.8) |

**Table 2**(勝ち/引き分けのデータセット割合 %)では PMI_DC が 125M〜175B の全サイズで最多(62.50〜86.66%)。ただし論文は「**does not imply that PMI_DC is always better**」と明記し、HellaSwag(Avg 勝ち)・ARC-E(LM 勝ち)・BoolQ(Unc 勝ち)を例外として挙げている。**平均の改善点数は論文に無い**(勝率でしか集計していない)。

**含意**: 「選択肢トークンの logprob をそのまま確率にする」は**言い換えの数で系統的に歪む**。歪み方は**タスク依存**で、補正(PMI_DC / 較正)は**万能ではなく、悪化する列がある**。したがって判断層で logprob を使うなら、**渋谷の選択肢集合ごとに較正を測り直す**必要がある(どの補正が勝つかを事前に決められない、という事実)。

#### 2-2-2. 較正(calibration)

- **Zhao ら 2021**(arXiv:2102.09690, ICML 2021)**contextual calibration**: 内容の無い入力("N/A")を入れたときの予測をラベル一様にするアフィン変換を当てる。報告は「平均精度を**最大 30.0% 絶対**改善し、プロンプト選択に対する分散も下げる」。例示: 感情プロンプトで "Amazing." を "N/A" に置換すると **62% Positive** と出る。※**抄録+検索要約経由**(本文未読)。
- **Guo ら 2017**(arXiv:1706.04599, ICML 2017): 「**modern neural networks, unlike those from a decade ago, are poorly calibrated**」。深さ・幅・weight decay・BatchNorm が較正に効く。推奨は **temperature scaling**(Platt Scaling の 1 パラメータ版)で「surprisingly effective」。※**抄録実読**。
- Holtzman らは PMI_DC が「calibrated(=Zhao らの CC)と uncalibrated の両方に対して一貫して勝つ」と主張しており、**Table 1 の CC 列でも PMI_DC が優勢**(例 175B TREC: CC 57.4 vs PMI_DC 58.4、SST-2: CC 75.8 vs PMI_DC 71.4 = ここは CC 勝ち)。

**含意**: **判断層の (ii) 0〜1 の確率**を作るなら、素の softmax でも logprob でもなく、**後処理の較正(temperature scaling が最も単純)を必ず挟む**ことが 2017 年以来の標準。较正を測るには**ラベル付きの検証集合が要る**(= 渋谷では holdout の扱いが効いてくる)。

#### 2-2-3. 制約デコードとの違い

**vLLM 公式**(structured outputs)が提供するのは 5 つ:
- `choice`: 「the output will be exactly one of the choices.」 ← **判断層の (i) に直接対応**
- `regex` / `json` / `grammar` / `structural_tag`

API は `extra_body` の `structured_outputs` キー(オフラインは `StructuredOutputsParams(choice=...)`)。**`guided_json` などの旧 `guided_*` は v0.12.0 で削除**。バックエンドは **xgrammar または guidance**(既定は `auto`)、regex については outlines / lm-format-enforcer にも言及。**このページに性能オーバーヘッドの記述は無い**。出典 <https://docs.vllm.ai/en/latest/features/structured_outputs/>(実読)。

**logprob を読む方式との本質的な違い(原典に基づく 2 点)**:

1. **制約デコードは分布を歪める。** Park ら 2024(NeurIPS 37, pp.24547–24568 / arXiv:2405.21047)の逐語主張: GCD 等の制約デコードは「**can distort the LLM's distribution, leading to outputs that are grammatical but appear with likelihoods that are not proportional to the ones given by the LLM**」。彼らは正しい目標を **grammar-aligned decoding (GAD)** と名づけ、ASAp を提案している。※**抄録+検索要約**(本文未読)。
2. **サブワードの不整合が精度を落とす。** Beurer-Kellner ら 2024(arXiv:2403.06988, ETH Zurich)の逐語主張: 制約デコードの多くは「**significantly impair task accuracy, if they do not correctly align the underlying LLM sub-word vocabularies with external constraints**」。図 1 の例は、無制約なら `·"` を選ぶところを、素朴に JSON 終端記号だけに絞ると `\t` を選んでしまう、というもの。DOMINO は部分語整合で解き、無制約比で最大約 2 倍の高速化と報告。※**抄録+検索要約**(本文未読)。

**したがって**: 「`choice` で選択肢に縛る」と「選択肢トークンの logprob を読んで確率にする」は**別物**。前者は**必ず妥当な出力**を返すが**返る確率が元の分布に比例する保証がない**。後者は**分布の形は取れるが surface form competition で歪む**。**両方とも較正なしでは (ii) の確率として使えない**(これは 3 本の原典の主張の重ね合わせ)。

#### 2-2-4. vLLM で logprob を取るときの決定論

**vLLM 公式 FAQ** の逐語: 「**vLLM does not guarantee stable log probabilities (logprobs) for the output tokens.**」理由は Torch 演算の数値的不安定性と、**バッチの組み方が変わることによる非決定性**(「other concurrent requests, changes in batch size, or batch expansion in speculative decoding」)。差は累積し、いずれ別トークンが選ばれ、「Once a different token is sampled, further divergence is likely」。緩和策として **float32**(メモリ増)、`temperature > 0` では **request seed** を挙げるが、精度由来のずれは残ると警告。出典 <https://docs.vllm.ai/en/v0.9.0/usage/faq.html>(実読)。

**vLLM 公式 Batch Invariance**: `VLLM_BATCH_INVARIANT=1` で「**deterministic and independent of the batch size or the order of requests in a batch**」を得られる。要件は **NVIDIA compute capability 8.0 以上**(または Triton 対応の Intel XPU)。「Enabling batch invariance **may impact performance** compared to the default non-deterministic mode. This trade-off is intentional to guarantee reproducibility.」**ベータ**。**このページには logprob に関する記述は一切ない**(= logprob まで保証されるかは公式に未記載 = **未確認**)。出典 <https://docs.vllm.ai/en/latest/features/batch_invariance/>(実読)。

比較のため **PyTorch 公式 Reproducibility** の逐語: 「**Completely reproducible results are not guaranteed across PyTorch releases, individual commits, or different platforms.**」「results may not be reproducible between CPU and GPU executions, even when using identical seeds」。ノブは `torch.use_deterministic_algorithms()`(`warn_only=False` で強制)、`torch.backends.cudnn.benchmark=False`、`torch.backends.cudnn.deterministic=True`。「**Deterministic operations are often slower than nondeterministic operations.**」出典 <https://docs.pytorch.org/docs/2.14/notes/randomness.html>(実読)。

**含意**: **小さな分類器を置いても「決定論」は自動では付いてこない**。PyTorch 側でも明示のノブと速度の代償が要る。ただし **CPU 上の固定重み・固定バッチの推論**、および **lookup 表**(§2-4)は、この問題を構造的に回避する(後者は配列参照なので数値演算が無い)。

---

### Q3 「安い器で LLM を呼ぶかどうかを決める」先行(cascade / routing)

#### 2-3-1. 何を判定に使っているか(原典ベース)

| 研究 | 判定に使うもの | 学習の有無 | 出典 |
|---|---|---|---|
| **FrugalGPT**(Chen, Zaharia & Zou 2023) | **自前の scoring model**。逐語「We employ a **DistilBERT** tailored to regression as the scoring function」。(query, answer) → [0,1] の信頼度。学習した閾値 τ を超えたら採用、超えなければ次の API | **学習する**(回帰。分布が近いラベル付きデータが必要) | <https://arxiv.org/abs/2305.05176>(ar5iv 実読) |
| **RouteLLM**(Ong ら 2024) | **学習した router** 4 種: ① 類似度重み付きランキング(Bradley-Terry・学習不要で推論時に解く)② 行列分解 ③ **BERT_BASE 分類器**(CLS → logistic ヘッド)④ Llama 3 8B の causal LLM 分類器。すべて P(強モデルが勝つ \| q) を出し、閾値 α で振り分け | **学習する**(人の選好データ) | <https://arxiv.org/html/2406.18665v4>(実読) |
| **LLM cascade with Mixture of Thoughts**(Yue ら 2024, ICLR) | **弱モデルの「answer consistency」**(自己申告 confidence ではない)。CoT と PoT の 2 表現を混ぜてサンプルし、一致度を難易度の信号にする | 一部学習(decision maker) | <https://arxiv.org/abs/2310.03094>(**抄録のみ**) |
| **Language Model Cascades: token-level uncertainty**(Gupta ら 2024) | **トークン単位の不確かさの分位ベクトル**を入力にした **5 層 MLP の学習 deferral rule**。小モデルの最終埋め込みと大モデルの第 1 層埋め込みを足すとさらに改善 | **学習する** | <https://arxiv.org/html/2404.10136v1>(実読) |

#### 2-3-2. 報告されている費用削減と精度(原典の数値)

**FrugalGPT Table 3「Cost savings by FrugalGPT to match the best individual LLM's performance」**:

| データセット | 最良の単独 LLM | 最良 LLM の費用 | FrugalGPT の費用 | 節約 |
|---|---|---|---|---|
| HEADLINES | GPT-4 | 33.1 | 0.6 | **98.3%** |
| OVERRULING | GPT-4 | 9.7 | 2.6 | **73.3%** |
| COQA | GPT-3 | 72.5 | 29.6 | **59.2%** |

抄録の逐語は「**up to 98% cost reduction**」「**improve the accuracy over GPT-4 by 4% with the same cost**」。学習された HEADLINES のカスケードは **GPT-J → J1-L → GPT-4**、閾値は **0.96 / 0.37**(実読)。Table 1 の API 価格は **10M 入力トークンあたり GPT-J $0.2 対 GPT-4 $30 = 2 桁の差**(2023 年 3 月時点)。

**RouteLLM Table 6(GPT-4 常用に対する費用節約比)**:

| ベンチマーク | CPT(50%) | CPT(80%) | 備考 |
|---|---|---|---|
| MT Bench | **3.66×** | 2.49× | CPT(50%) のスコア 8.8 = GPT-4 の 9.3 の **95%** |
| MMLU | **1.41×** | 1.14× | スコア 75 = GPT-4 81 の **92%** |
| GSM8K | **1.49×** | 1.27× | スコア 75 = GPT-4 86 の **87%** |

MT Bench の最良は行列分解(D_arena + D_judge): CPT(50%) **13.40%** 対 ランダム 49.03%、APGR 0.802(+60.4%)。**D_arena だけで学習すると MMLU ではほぼランダムになった**(= ルータは**対象分布のラベルが要る**、という原典の観察)。

**ルータ自身の費用**(Table 7・100 万リクエストあたり): 類似度重み付き $39.26(**2.9 req/s・CPU**)/ 行列分解 $3.32(**155.16 req/s**)/ **BERT $3.19(69.62 req/s)** / causal LLM $5.23(42.46 req/s)。最悪でも GPT-4 生成費の **0.4% 以下**。

**Gupta ら 2024 の AUC-DF**(FLAN-T5 Base → Large、括弧はランダム基準比):

| データセット | Chow-Sum | Chow-Average | Post-Hoc-Quantile | Post-Hoc-Embed-1+2 |
|---|---|---|---|---|
| MNLI | 0.627(**−2.63%**) | 0.642(−0.31%) | 0.711(+10.4%) | **0.722(+12.24%)** |
| TriviaQA | 0.073(**−13.09%**) | 0.087(+3.57%) | 0.097(+15.47%) | **0.100(+19.56%)** |
| ANLI-R1 | 0.524(+4.59%) | — | 0.534(+6.58%) | **0.563(+12.51%)** |
| WMT DE→FR | 0.390(+0.00%) | 0.392(+0.51%) | 0.404(+3.58%) | **0.404(+3.69%)** |

**注意(原典が明記)**: 学習 deferral は**常に勝つわけではない**。TyDiQA-SW は Chow-Sum 0.170(+9.67%)> Post-Hoc-Quantile 0.163(+5.16%)、TyDiQA-ID は 0.247 > 0.235、Lambada は 0.703 > 0.701。

#### 2-3-3. 「自己申告の confidence で振り分ける」への批判(**ある**)

| 出典 | 逐語または数値 | 確認 |
|---|---|---|
| **Gupta ら 2024**(arXiv:2404.10136) | 配列確率をそのまま deferral に使うと「**length bias problem**」= Chow-Sum は**長い出力を優先的に上位モデルへ送り**、Chow-Average は**逆に短い出力へ過剰補正する**。MNLI で Chow-Sum は**ランダムより悪い**(−2.63%)、TriviaQA では **−13.09%** | **原典実読** |
| **Xiong ら ICLR 2024**(arXiv:2306.13063) | 口頭 confidence の **ECE×100(Table 1)**: GPT-3 平均 **52.0**、Vicuna **46.1**、GPT-3.5 **37.7**、GPT-4 **18.0**。**AUROC×100 平均**: GPT-3 51.3 / Vicuna 52.5 / GPT-3.5 55.1 / **GPT-4 62.7**。信頼度は **5 の倍数で 80〜100% に集中**し、その区間の実正解率は 80% を大きく下回る。論文の逐語「LLMs tend to be **highly overconfident** when verbalizing their confidence」。また「**logits imply overconfidence in many cases**」とも述べ、logit 側も免罪されていない | **原典実読**(v1) |
| **Guo ら 2017**(arXiv:1706.04599) | 「modern neural networks ... are **poorly calibrated**」— 分類器側でも素の信頼度は使えない | **抄録実読** |
| **Yue ら 2024**(arXiv:2310.03094) | そもそも自己申告を使わず、**answer consistency** を難易度信号に採用。「accuracy comparable to using solely the stronger LLM but require only **40% of its cost**」 | **抄録のみ** |

**含意(事実の含意のみ)**: 「LLM 自身に『自信は?』と聞いて振り分ける」方式は、**原典 4 本が独立に否定的**。AUROC が平均 0.627(GPT-4)ということは、**判別としては偶然(0.5)からさほど遠くない**。判断層で (ii) 0〜1 の確率を作るなら、**自己申告ではなく、(a) 別に学習したスコアラ(FrugalGPT)(b) トークン単位不確かさの学習した集約(Gupta)(c) 複数サンプルの一致度(Yue)**のいずれかが原典に裏づけられた選択肢である。

---

### Q4 社会シミュレーション・エージェントでの先行

**結論: R-39 の結論は「学習した動的ルータ」に限れば維持されるが、「毎決定を小さな分類器/方策に振り分けた先行」については反証が見つかった。2025〜2026 に集中的に出ている。**

| 研究 | 何を LLM の代わりに置いたか | ルーティングは動的か | 数値(原典) | 確認 |
|---|---|---|---|---|
| **Light Society**(arXiv:2506.12078v2、10 億体) | 教師 LLM(Gemini 2.0 Flash)から**蒸留した代理モデル**。5 種を比較: softmax 回帰 / LightGBM(生の WVS 属性)/ **MLP**(text-embedding-3-large 埋め込み・隠れ層 512,256)/ Transformer / **Qwen3-0.6B の SFT**。本番は MLP を選び、**[10,000 × 10,000 × 3 × 3] の事前計算 lookup 表(9 億通り)**に畳んだ = 1 回の配列参照 | **いいえ(設定可能な固定ポリシー)**。逐語「three routing policies, namely **all-LLM, all-surrogate, and per-sample weighted routing**」。**学習したルータではない** | 教師データ 1 話題あたり**約 400,000 組**。macro F1 は火星都市で **0.84〜0.85(5 手法とも)**、大量失業で **0.75〜0.77**。置換率 0/25/50/75/100% で軌跡は「near-identical inflection points」。10 億ノード BA グラフ・100 ラウンド・毎回 1% 抽出。**GPU 台数・トークン総数・金額は本文に無い(図のみ)** | **原典実読** |
| **GenWorld**(arXiv:2606.27650、**日本・東広島**、196,608 体) | 教師(**Gemma 3 27B**)に**同一の文脈キーを K=10〜30 回**問い、平均スコアを categorical 分布に正規化して**lookup policy にコンパイル**。文脈キー = (人物ビン、状態ビン、質問種別、平日/休日)。意図空間は {home, duty, leisure, maintenance} に固定、スコアは 0〜10 の整数 | **いいえ(オフライン compile → オンラインは lookup のみ)** | **Python の lookup で 1.85M queries/s = 1 件 0.54 μs**(Intel Core i5-14600K の **CPU**)。回避したオンライン呼数は **200,000 体 × 96 決定点 = 1.92×10⁷ 回/日**。オンライン LLM は「0.5〜2 s(ローカル 7B)」。**端から端までの高速化倍率は未報告**(著者が「ongoing work」と明記) | **原典実読** |
| **APS**(arXiv:2605.27419v1、1,000 万体) | LLM を遷移オラクルとして残したまま、**毎ラウンド呼ぶ相手を絞る**: ① 中核プロトタイプ ② 単独尾部エージェント ③ shadow-audit エージェント。非照会エージェントは近傍プロトタイプから補間 | **部分的に動的(ただし学習ではなく統計量)**。層別予算を前ラウンドの **残差リスク R(残差分散・支持域距離×曲率・監査不一致率・稀状態再現)**に比例配分。固定配分との比較で JSD が全率で改善 | 10M 体 × 8 ラウンド = 総当たり 8,000 万呼 → **20.99 万呼 = 381.1 倍削減**、最終 **JSD 0.094**、exact 0.544。**壁時計 26.64 時間 対 全 LLM 参照 9.56 日**。LS-Surrogate(Light Society 由来)を 10M で **10.0 倍削減・JSD 0.264・exact 0.411** と再現 | **原典実読** |
| **AgentTorch / LLM archetypes**(arXiv:2409.10568v3, AAMAS 2025、840 万体) | **原型(archetype)単位で LLM に M 回聞いて yes/no の確率 p を作り、個体は Bernoulli(p) で引く**。個体ごとの分類器は**無い** | いいえ(静的な階層) | **M=3 で約 400 クエリ / 840 万体**(週次 1 決定)。ベンチは**プロンプト予算 300 クエリ/step** に固定。Table 1(MSE↓): Archetype 失業 24.59 / 感染 95.17、Heuristic 41.05 / 2914.73、LLM-as-agent 56.98 / 4311.70。**実行時間は LLM-as-agents 比 95% 減** | **原典実読** |
| **OASIS**(arXiv:2411.11581、100 万体) | **Time Engine = 24 次元の時間帯別活動確率**で、その step に LLM を呼ぶ体を確率的に選ぶ(門は**確率表であって分類器ではない**) | いいえ(固定の確率表) | 100 万体で **1 step あたり 18.0 時間・A100 27 台**。アブレーション: 活動確率を全部 1 にすると実データの伝播パターンを再現できない = **門は費用だけでなく忠実度のため** | **検索要約経由**(本文未読・数値は要再確認) |
| **Lyfe Agents**(arXiv:2310.02172) | **option-action**: 高レベルの option 選択**そのものは LLM 呼び**だが、毎 step ではなく option 単位。**非 LLM なのは終了判定だけ**(時間トリガ・会話の反復検出) | いいえ | **$0.5 / 体 / 人時**(GPT-3.5)。Park ら 2023 の見積 $25/体/人時 に対し約 50 倍(抄録は「10-100 times lower」)。アブレーション: 毎 step 呼んでも性能は上がらず費用だけ増えた(会話継続 70.3±13.2 s 対 23.8±1.5 s) | **原典実読** |
| **Poor Man's Agentic Modeling**(arXiv:2608.11215) | 各エージェントを「**数百〜数千回の安いクエリから当てた低パラメータモデル**」に置換し、任意の N を**ラップトップで**回す | — | 逐語「replace each LLM agent by a **low-parameter model fitted from a few hundred to a few thousand cheap queries**」。教師は主に DeepSeek で「for a few dollars」。EconAgent の再実装+7 本の既存 LLM シミュで検証 | **抄録のみ** |
| **Should LLM Agents Decide in Social Simulations?**(arXiv:2606.12369) | **逆向きの検証**: 有限状態機械(1 次マルコフ)を正解方針とし、LLM の行動選択がそれを再現できるかを測る | — | 1,000 体・**10,000 決定**・LLaMA 3.1 / GPT-OSS / Mistral 24B × 3 プロンプト。逐語「**LLMs can approximate the reference policy in some configurations, but do not preserve it reliably**」「additional guidance can **introduce systematic action biases**」。最良の LLM 構成でも「**several hundred times slower** than direct Markov chain sampling」 | **抄録のみ** |

**Q4 への直接の答え(3 段に分ける)**:

1. **「エージェントの毎回の意思決定を、LLM ではなく小さな分類器/方策に置き換えた」先行は<ins>ある</ins>。** Light Society(MLP / LightGBM / Qwen3-0.6B を比較して lookup に畳む)、GenWorld(Monte Carlo 蒸留 → lookup、**日本の都市・196,608 体**)、Poor Man's(体ごとの低パラメータ代理)。**R-39 の「静的な階層が主流」という観察はこの層にも当たる**(蒸留は基本的に全置換=静的)。
2. **「実行時に 1 件ごとに、学習したルータが LLM を呼ぶか決める」社会シミュの先行は<ins>今回も見つからなかった</ins>。** 最も近いのは **APS の残差リスクによる適応的予算配分**(統計量であって学習モデルではない)と **Light Society の per-sample weighted routing**(設定可能なポリシー)。**R-39 の結論はこの狭い意味では維持される**。
3. **門(いつ LLM を呼ぶか)を確率表で持つ先行は<ins>ある</ins>**(OASIS の 24 次元活動確率)。しかもそれは**費用のためだけでなく、実データの伝播を再現するために必要**だったとアブレーションで示されている。

---

## 3. 候補の比較表(判断層の背後に置けるもの)

**列の読み方**: 質問の型 (i)=少数択 2〜10 / (ii)=0〜1 の確率 / (iii)=yes/no。**原典に無い数値は「未確認」**。VRAM の「導出」は本答申の算術(params × 2 バイト = fp16 重みのみ。KV キャッシュ・活性・実行時オーバーヘッドを含まない)であり、**実測ではない**。

| # | 候補 | 答えられる型 | パラメータ / 必要 VRAM | 速度(原典の数値) | 日本語 | 決定論 | ライセンス | オフライン | **RTX 5070 12GB 1 枚で動くか** |
|---|---|---|---|---|---|---|---|---|---|
| A | **NLI ゼロショット(英)** `facebook/bart-large-mnli` | (i)(ii)(iii) | 0.4B / 必要 VRAM **未確認**(導出 ≈0.8 GB fp16) | **未確認**(カードに記載なし) | ✕(英語テンプレート) | PyTorch 既定では**非保証**(公式) | MIT | ○ | **動く見込み**(0.4B。ただし実測未確認) |
| B | **NLI ゼロショット(多言語)** `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | (i)(ii)(iii) | 0.3B(≈279M)/ **未確認**(導出 ≈0.56 GB fp16) | **未確認** | △ 微調整 27 言語に **ja を含む**が **ja の精度は未報告** | 同上 | MIT | ○ | **動く見込み**。ただしカードが **fp16 非対応**と明記 = fp32 運用(導出 ≈1.1 GB) |
| C | **NLI ゼロショット(日)** `akiFQC/bert-base-japanese-v3_nli-jsnli-jnli-jsick` | (i)(ii)(iii) | **0.1B** / **未確認**(導出 ≈0.2 GB fp16) | **未確認** | ○ **JGLUE-JNLI val 0.914** | 同上 | **CC-BY-SA-4.0**(継承条項あり) | ○ | **動く見込み** |
| D | **NLI ゼロショット(日)** `Formzu/bert-base-japanese-jsnli` | (i)(ii)(iii) | 記載なし(BERT-base 相当)/ **未確認** | **未確認** | ○ **JSNLI eval acc 0.9288**・テンプレ「この例は{}です。」 | 同上 | CC-BY-SA-4.0 | ○ | **動く見込み** |
| E | **SetFit**(少数例微調整・bi-encoder + LogReg) | (i)(ii)(iii)(`predict_proba` が公式 API) | MPNet **110M** / MiniLM **15M** / RoBERTa 355M。チェックポイント **70 MB / 420 MB** | 学習: **N=8 で約 30 秒**(**16 GB GPU** = p3.2xlarge・$0.025/split)。推論 FLOPs **8.3e9**(MPNet)/ **1.3e9**(MiniLM) = T-Few 3B 比 **19× / 123×** | △ body を日本語 ST に差し替え可(ruri v3 等)。**原典の日本語実測は MARC MAE×100 = 93.2 で 6 言語中最下位側** | 同上 | **Apache-2.0**(body/ruri も Apache-2.0) | ○ | **動く**(原典が 16 GB GPU で学習済み。12 GB での実測は**未確認**) |
| F | **蒸留小型分類器**(DistilBERT 等を自前学習) | (i)(ii)(iii) | **66M** / **未確認**(導出 ≈0.13 GB fp16)。端末サイズ **207 MB** | **CPU・batch 1 で STS-B 全走査 410 s**(BERT-base 668 s)。iPhone 7 Plus で BERT 比 **71% 高速**(トークン化を除く) | △ 日本語版は別途(ruri / ModernBERT-ja 系を蒸留する必要・**先行の数値は未確認**) | 同上 | Apache-2.0(HF 実装) | ○ | **動く**(66M) |
| G | **同一 LLM の logprob を読む** | (i)(ii)(iii) | 追加ゼロ(LLM 本体のみ) | 追加の前向き計算は無し(生成 1 回分) | LLM 次第 | **vLLM 公式が明示的に非保証**。`VLLM_BATCH_INVARIANT=1`(CC 8.0+・ベータ・**性能低下**)で batch 不変にできるが **logprob への言及は公式に無い** | LLM 次第 | ○ | **LLM 本体が 12 GB に載るかに依存**(判断層自体の費用はゼロ) |
| H | **制約デコード(`choice`)** vLLM structured outputs | (i)(iii)。**(ii) は返らない**(選択肢を強制するだけ) | 追加ゼロ | **公式ページに性能オーバーヘッドの記述なし** | LLM 次第 | 上に同じ+**分布の歪み**(Park ら)・**サブワード不整合**(Beurer-Kellner ら) | Apache-2.0(vLLM) | ○ | 同上 |
| I | **小型 LM を判断器に SFT**(例 Qwen3-0.6B) | (i)(ii)(iii) | **0.6B**(非埋め込み 0.44B)・28 層・文脈 32,768 / **未確認**(導出 ≈1.2 GB fp16) | **未確認** | Qwen3 は多言語だが**日本語判断タスクの数値は未確認** | 生成モデルなので G と同じ問題 | **Apache-2.0** | ○ | **動く見込み**。要 `transformers>=4.51.0` / `vllm>=0.8.5` |
| J | **蒸留 lookup 表**(GenWorld 方式) | (i)(ii)(iii)(カテゴリ分布をそのまま持てる) | **ニューラルネット不要**。表のサイズは文脈キーの粒度次第(Light Society は [10,000×10,000×3×3] = 9 億セル) | **1.85M queries/s = 0.54 μs/件(CPU・i5-14600K)** | 教師 LLM 次第(GenWorld は **Gemma 3 27B**・日本の都市で実施) | **完全に決定論**(配列参照。サンプリングを入れるなら seed のみ) | 実装次第 | ○ | **GPU 不要**(オフライン蒸留時だけ教師 LLM が要る) |
| K | **蒸留 MLP / GBDT**(Light Society 方式) | (i)(ii)(iii) | MLP 隠れ層 (512,256)・入力 6,150 次元 / **未確認**(小さい) | **未確認**(本文に秒数なし) | 教師 LLM 次第 | PyTorch 既定では非保証(§2-2-4) | 実装次第 | ○ | **動く**(教師での蒸留時のみ LLM が要る) |
| L | **学習ルータ**(RouteLLM の BERT 分類器) | (ii) 主。閾値で (iii) | BERT_BASE(110M)。学習は **L4 24GB×2** | **69.62 req/s**・100 万リクエスト **$3.19** | **未確認**(英語の選好データで学習) | PyTorch 既定では非保証 | **未確認**(本答申でリポジトリのライセンスを確認していない) | ○ | **推論は動く見込み**。**学習は原典が 24GB×2 を使用 = 12 GB 1 枚での再現は未確認** |
| M | **スコアラ方式**(FrugalGPT の DistilBERT 回帰) | (ii) 主。閾値で (iii) | DistilBERT(66M) | **未確認**(論文に秒数なし) | △ 日本語版は自前 | PyTorch 既定では非保証 | Apache-2.0(HF 実装) | ○ | **動く**(66M) |
| — | **T-Few 3B / 11B**(比較のため) | (i)(iii) | 3B は「**40 GB 以上の GPU メモリが必要**」、11B は「**80GB A100 が要る**」(原典逐語) | 学習 **約 700 秒・$0.7/split** | — | — | — | — | **✕ 載らない**(原典の必要量が 12 GB を超える) |

**RTX 5070 側の確定事実**(公式):
- **12 GB GDDR7・CUDA コア 6,144・Blackwell**(NVIDIA marketplace / 製品ページ)。
- **compute capability = 12.0**(NVIDIA 公式 CUDA GPUs 一覧。RTX 5070/5070 Ti/5080/5090 が 12.0 の見出しの下)。
- **PyTorch 2.7 で Blackwell 対応の prototype**。逐語「PyTorch 2.7 introduces support for NVIDIA's new Blackwell GPU architecture and ships pre-built wheels for CUDA 12.8」「PyTorch 2.7 includes Triton 3.3, which adds support for the Blackwell architecture with torch.compile compatibility」。導入は `--index-url .../whl/cu128`。
- **vLLM 公式のインストール要件は「compute capability 7.5 or higher」**で、Blackwell については **B200/GB200 が CUDA 12.8 以上**と書くのみ。**RTX 50 系 / sm_120 への言及は公式ページに無い = 未確認**。Python は 3.10〜3.13、**Linux のみ**(Windows は WSL か community fork)。
- **`VLLM_BATCH_INVARIANT=1` の要件は compute capability 8.0 以上** = 12.0 の RTX 5070 は数値上は満たす。ただし **RTX 50 系での動作確認は公式に記載が無い**。

---

## 4. 親への確認依頼(自信のない主張・名指し)

1. **「RTX 5070 12 GB で動く」列はすべて<ins>判定</ins>であって実測ではない。** 特に E(SetFit)の「動く」は原典が **16 GB の p3.2xlarge** で学習した事実からの外挿。**12 GB での学習可否は誰も測っていない**。親には「12 GB 前提の数値は本答申には 1 つも無い」ことを確認してほしい。
2. **vLLM が RTX 5070(sm_120)で動くかは、公式ドキュメントからは確認できなかった。** vLLM のインストール要件ページは CC 7.5+ と書き、Blackwell は B200/GB200 しか挙げていない。「vLLM は 7.5+ だから 12.0 も動く」は**文面上はそう読めるが、公式の動作確認の記載ではない**。ここを実機で潰すべきかは親の判断。
3. **Q4 で R-39 の結論を<ins>部分的に</ins>覆した。** 「毎決定を小分類器に置き換えた先行は無い」は**覆る**(Light Society / GenWorld / Poor Man's)。「毎決定の**学習した動的ルータ**は無い」は**維持**。この線引きが親の意図と合っているか確認してほしい。なお GenWorld・APS・Poor Man's・2606.12369 は **2026 年の新しい arXiv** で、abs ページのメタデータ(題・著者・投稿日)は自分で確認したが、**査読状態は未確認**。
4. **Light Society の代理モデル 5 種の F1 が「0.84〜0.85 で横並び」という結果**は、「線形回帰でも LLM 蒸留 SLM でも大差ない」という強い含意を持つ。ただしこれは **WVS の意見遷移という 3 択タスク**の話で、渋谷の (i) 2〜10 択に移るとは限らない。**この含意を設計に使うなら親の再検討が要る**。
5. **Holtzman らの PMI_DC は「常に良い」ではない。** ARC-E と HellaSwag では**素の LM スコアや長さ正規化のほうが良い**(175B で ARC-E 73.5 → 63.3)。本答申は「較正は必須」と書いたが、**どの較正が勝つかはタスクごとに測るしかない**というのが原典の立場。「logprob + PMI_DC を採れば解決」と読まないでほしい。

---

## 5. 空欄(調べられなかったこと)

| # | 空欄 | なぜ |
|---|---|---|
| 1 | **RTX 5070 12 GB 上での、いずれかの候補の実測レイテンシ / スループット / ピーク VRAM** | どの原典にも無い。ベンチマークは V100 16GB(SetFit)・Xeon CPU(DistilBERT)・i5-14600K CPU(GenWorld lookup)・L4/A100(RouteLLM)止まり |
| 2 | **日本語での「行動選択」タスクの分類器ベンチマーク** | JNLI / JSNLI / JMTEB / MARC しか見つからなかった。**渋谷の (i) に近い日本語タスクの数値はゼロ** |
| 3 | **NLI ゼロショット日本語モデルの推論速度・パラメータ数の一部** | Formzu のカードにはパラメータ数の記載が無い。どちらのカードにも速度の記載が無い |
| 4 | **`facebook/bart-large-mnli` の報告精度** | 公式カードに**ベンチマーク数値が一切ない**(例示スコアのみ)。Yin らの論文値は BERT-base での値であって BART の値ではない |
| 5 | **vLLM の batch invariance が logprob まで保証するか** | 公式ページに **logprob への言及が無い**。FAQ 側は「logprob は保証しない」と書いており、両ページの関係が公式に説明されていない |
| 6 | **制約デコード(`choice`)のオーバーヘッドの実数値** | vLLM 公式ページに記載なし。Park ら / Beurer-Kellner らの本文は未読で、精度低下の実数値も取れていない |
| 7 | **Light Society の GPU 台数・トークン総数・金額** | 本文に無い(図 3c のみ)。「orders of magnitude」という定性表現のみ |
| 8 | **GenWorld の端から端までの高速化倍率** | 著者自身が「per-step wall-clock profiling is ongoing work」と明記 |
| 9 | **Zhao ら 2021 の本文** | 抄録+検索要約のみ。「最大 30.0% 絶対」は**二次**扱い(原典の表を見ていない) |
| 10 | **OASIS 本文** | 検索要約のみ。「1M 体で 18.0 h/step・A100 27 台」「活動確率のアブレーション」は**二次**。数値を設計書に写すなら親の一次確認が必須 |
| 11 | **RouteLLM のコードのライセンス** | リポジトリを確認していない(論文のみ) |
| 12 | **Jev / Open-Jev の一次情報 URL** | **依頼どおり調査していない**。今回の検索で偶然にも**一次情報の URL は見かけなかった**(該当ゼロ) |
| 13 | **Xiong ら の「白箱 vs 黒箱 AUROC 0.522→0.605」** | arXiv **v1 の本文には無い**(検索要約が別版から引いたものと思われる)。**採らない** |

---

## 6. 参考文献(✓ = 本文または公式ドキュメント本体を実読)

### Q1 系
1. ✓ Yin, Hay & Roth 2019, *Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach*, EMNLP-IJCNLP 2019, pp.3914–3923 — <https://aclanthology.org/D19-1404/> / <https://arxiv.org/abs/1909.00161>(ar5iv 本文)
2. ✓ Tunstall ら 2022, *Efficient Few-Shot Learning Without Prompts*(SetFit) — <https://arxiv.org/abs/2209.11055> / 本文 <https://arxiv.org/html/2209.11055v1>
3. ✓ Sanh ら 2019, *DistilBERT, a distilled version of BERT* — <https://arxiv.org/abs/1910.01108>(ar5iv 本文)
4. ✓ Sentence Transformers 公式 — <https://sbert.net/examples/cross_encoder/applications/README.html>
5. ✓ `facebook/bart-large-mnli` — <https://huggingface.co/facebook/bart-large-mnli>
6. ✓ `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` — <https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7>
7. ✓ `akiFQC/bert-base-japanese-v3_nli-jsnli-jnli-jsick` — <https://huggingface.co/akiFQC/bert-base-japanese-v3_nli-jsnli-jnli-jsick>
8. ✓ `Formzu/bert-base-japanese-jsnli` — <https://huggingface.co/Formzu/bert-base-japanese-jsnli>
9. ✓ `cl-nagoya/ruri-v3-310m`(Ruri v3・JMTEB) — <https://huggingface.co/cl-nagoya/ruri-v3-310m> / 論文 <https://arxiv.org/abs/2409.07737>(**論文本文は未読**)
10. ✓ SetFit 公式 — <https://github.com/huggingface/setfit> / <https://huggingface.co/docs/setfit/en/reference/main>
11. ✓ `Qwen/Qwen3-0.6B` — <https://huggingface.co/Qwen/Qwen3-0.6B>

### Q2 系
12. ✓ Holtzman ら 2021, *Surface Form Competition* , EMNLP 2021 pp.7038–7051 — <https://aclanthology.org/2021.emnlp-main.564/> / <https://arxiv.org/abs/2104.08315>(ar5iv 本文)
13. ✓(抄録)Guo ら 2017, *On Calibration of Modern Neural Networks*, ICML 2017 — <https://arxiv.org/abs/1706.04599>
14. (抄録+二次)Zhao ら 2021, *Calibrate Before Use*, ICML 2021 — <https://arxiv.org/abs/2102.09690>
15. (抄録+二次)Park ら 2024, *Grammar-Aligned Decoding*, NeurIPS 37 pp.24547–24568 — <https://arxiv.org/abs/2405.21047> / <https://proceedings.neurips.cc/paper_files/paper/2024/hash/2bdc2267c3d7d01523e2e17ac0a754f3-Abstract-Conference.html>
16. (抄録+二次)Beurer-Kellner ら 2024, *Guiding LLMs The Right Way*(DOMINO) — <https://arxiv.org/abs/2403.06988>
17. ✓ vLLM 公式 Structured Outputs — <https://docs.vllm.ai/en/latest/features/structured_outputs/>
18. ✓ vLLM 公式 Pooling Models — <https://docs.vllm.ai/en/latest/models/pooling_models/>
19. ✓ vLLM 公式 FAQ(logprob 非保証) — <https://docs.vllm.ai/en/v0.9.0/usage/faq.html>
20. ✓ vLLM 公式 Batch Invariance — <https://docs.vllm.ai/en/latest/features/batch_invariance/>
21. ✓ PyTorch 公式 Reproducibility — <https://docs.pytorch.org/docs/2.14/notes/randomness.html>

### Q3 系
22. ✓ Chen, Zaharia & Zou 2023, *FrugalGPT* — <https://arxiv.org/abs/2305.05176>(ar5iv 本文)
23. ✓ Ong ら 2024, *RouteLLM* — <https://arxiv.org/abs/2406.18665> / 本文 <https://arxiv.org/html/2406.18665v4>
24. ✓ Gupta ら 2024, *Language Model Cascades: Token-level uncertainty and beyond* — <https://arxiv.org/abs/2404.10136> / 本文 <https://arxiv.org/html/2404.10136v1>
25. ✓ Xiong ら 2024(ICLR), *Can LLMs Express Their Uncertainty?* — <https://arxiv.org/abs/2306.13063> / 本文 v1 <https://arxiv.org/html/2306.13063v1>
26. (抄録)Yue ら 2024(ICLR), *Large Language Model Cascades with Mixture of Thoughts Representations* — <https://arxiv.org/abs/2310.03094>

### Q4 系
27. ✓ Light Society, *Modeling Earth-Scale Human-Like Societies with One Billion Agents* — <https://arxiv.org/abs/2506.12078> / 本文 <https://arxiv.org/html/2506.12078v2>
28. ✓ *GenWorld: Empirically Grounded Urban Simulation Infrastructure for Scalable LLM-Agent Studies* — <https://arxiv.org/abs/2606.27650> / 本文 <https://arxiv.org/html/2606.27650>
29. ✓ *APS: Bias-Controlled Adaptive Prototype Simulation for Population-Scale LLM Agents* — <https://arxiv.org/abs/2605.27419> / 本文 <https://arxiv.org/html/2605.27419v1>
30. ✓ Chopra ら 2024(AAMAS 2025), *On the limits of agency in agent-based models* — <https://arxiv.org/abs/2409.10568> / 本文 <https://arxiv.org/html/2409.10568v3>
31. ✓ Kaiya ら 2023, *Lyfe Agents* — <https://arxiv.org/abs/2310.02172> / 本文 <https://arxiv.org/html/2310.02172>
32. (二次)Yang ら 2024, *OASIS: Open Agent Social Interaction Simulations with One Million Agents* — <https://arxiv.org/abs/2411.11581>
33. (抄録)Itkin 2026, *Poor Man's Agentic Modeling* — <https://arxiv.org/abs/2608.11215>
34. (抄録)Buitrago López ら 2026, *Should LLM Agents Decide in Social Simulations?* — <https://arxiv.org/abs/2606.12369>

### ハードウェア
35. ✓ NVIDIA 公式 CUDA GPUs(RTX 5070 = CC 12.0) — <https://developer.nvidia.com/cuda-gpus>
36. ✓ NVIDIA 公式 RTX 5070 ファミリ / marketplace(12 GB GDDR7・6,144 CUDA コア) — <https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5070-family/> / <https://marketplace.nvidia.com/en-us/consumer/graphics-cards/geforce-rtx-5070-founders-edition/>
37. ✓ PyTorch 2.7 リリースブログ(Blackwell prototype・cu128) — <https://pytorch.org/blog/pytorch-2-7/>
38. ✓ vLLM 公式 GPU インストール要件 — <https://docs.vllm.ai/en/latest/getting_started/installation/gpu.html>
