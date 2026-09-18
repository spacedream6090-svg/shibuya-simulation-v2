# Jev(TypeSafe AI・System One モデル)の調査ノート(2026-09-18・第238・親の直読)

> 用途: ユーザー依頼「TypeSafe(Diogo Almeida)の Jev を Web で一度リサーチして詳細を理解する」。**親(Fable 5.1)が一次資料を直接読んだ**(サブ不使用)。ベンダーの主張と第三者の記事を分けて書く。Web からのファイル取得はしていない(読むだけ)。本ノートは答申ではなく、R-38(非 LLM モデルの混成)を起こすときの材料。

## 0. 一次確認の範囲

| 種別 | 読んだもの | 位置づけ |
|---|---|---|
| 一次(ベンダー) | TypeSafe ブログ「Introducing System One Models & Jev」・docs(Introduction / quickstart / primitives/choice / primitives/score / confidence)・評価ページ evals.typesafe.ai・GitHub `typesafe-ai/system-one-adapter-python` README | 仕様・主張の出所 |
| 二次(報道・解説) | The Register(09-16)・DataCamp(09-16)・BusinessWire プレスリリース(09-15)・Anthony Maio の Substack | 独立の検証は**無い**(全て一次の再掲+著者の所見) |
| 読めなかった | `typesafe.ai/docs`(404・正しくは `docs.typesafe.ai`)・Forbes(有料) | — |

## 1. 何か(事実として確認できたこと)

- **会社**: TypeSafe AI(サンフランシスコ・2024 年設立)。2026-09-15 にステルスを出て seed **$40M**(DCVC 主導)。創業者 Diogo Almeida(CEO・元 OpenAI/Google Brain・**InstructGPT 論文の共同筆頭著者の一人**・GPT-4 論文共著)、Erik Gafni(CTO)、Sasha Sheng(COO・元 Meta FAIR)。「ChatGPT の共同発明者」はベンダーの表現で、Substack 著者は「InstructGPT の equal-contribution 著者」が正確だと指摘。
- **Jev**: 同社の最初の公開モデル。名は Jevons のパラドックス(効率化が需要を増やす)から。2026-09-15 に早期アクセス(待機リスト)。**System One モデル**(Kahneman の速い思考)という新カテゴリを自称。
- **何をするか**: 「非構造の状態(state)を入れ、**型付きの確率的な判断**を返す関数呼び出し」。**文字列を生成しない**。出力は 3 つの原始型だけ。
  - **Choice**: 選択肢(名前+説明の map・**最大 255**)から 1 つ。返り値 `choice`・`probabilities`(合計 1)・`confidence`(0〜1・分布の形から計算・統計量は未公開)。
  - **Score**: 順序つき水準(**2〜10 段**・各段は「状況の記述」)。返り値 `score`(確率加重平均・連続値)・`probabilities`・`legend`・`confidence`。
  - **Noul**: 命題の真偽確率(0〜1)。confidence は付かない。
  - 1 回の呼び出しに複数の質問を混ぜられ、**全質問を同じ state に対して並列・独立に評価**(「質問を足しても応答時間はほとんど変わらない」)。API: `POST https://api.typesafe.ai/v1/systemone`・モデル名 `jev-latest`・Python/JS SDK・Claude Code 用スキルもある。
  - 文脈長・1 呼あたりの質問数上限・レート制限・モデル規模は**未公開**。
- **学習法**: 「Reinforcement Learning for Calibrated Decisions(RLCD)」。RLHF(人に好かれる)や RLVR(検証可能な出力)と対比し「認識論的に正直な確率」を目標にすると説明。**報酬・アーキテクチャ・較正の測り方は非公開・論文なし**。「新しいモデルアーキテクチャと並列サンプラー」とだけ書かれ、自己回帰でないこと以外は不明(エンコーダ型分類器かどうかは推測の域)。

## 2. 主張されている数値(ベンダー自身の測定・第三者検証なし)

| 項目 | 主張 | 注意 |
|---|---|---|
| 価格 | 入力 **$0.042 / MTok**・出力 無料 | 「補助金でないことは証明できない」と自認 |
| 遅延 | **70〜500 ms**(LLM は 3〜329 s と対比) | 測定は「西海岸の自社サーバー近くのラップトップから」 |
| 速度・費用比 | ホームページ 193.6 倍速・444.6 倍安(「実世界の上限側」と自認) | 比較対象は自社の System One アダプタ経由の LLM(素のプロンプトより遅く高い) |
| 幻覚・型エラー | **0%** | **経験値ではなく定義**(スキーマ一致で型エラーは構造的に無い。判断の誤りは別) |
| Doom デモ | テキスト化したゲーム状態で 10 判断/秒・約 $7/h | 画像ではない・スクリプト bot の方が強いと自認 |

**評価(evals.typesafe.ai)**: 4 つの業務ワークフロー(セキュリティ警報の処理・エージェント実行記録の監視・請求書処理・顧客対応)。**正解ラベルは人手ではなく「GPT-6 Astra と Claude Fable 5.1(高推論)の平均」との一致率**。件数・信頼区間は未記載。ワークフローは同社の能力チームが作成(選択バイアスを自認)。

| モデル | 一致率(4 課題平均) | $/件 | 秒/件 |
|---|---|---|---|
| Jev | 67.8% | 0.0004 | 0.4 |
| GPT-5.6 Terra | 67.9% | 0.0304 | 10.1 |
| GPT-5.6 Sol | 74.1% | 0.0836 | 23.3 |
| Claude Opus 5 | 73.1% | 0.1761 | 37.8 |

- 課題別では請求書処理で Jev 61.8% vs Sol 79.1% / Opus 5 78.4% と**多段の判断で差が開く**。顧客対応では Jev 76.0% で上位。
- 同じページの副産物: **全 LLM で「狭い型付き質問+コード規則のワークフロー」が「1 本のプロンプト」より一致率が高い**(Opus 5 64.8→73.1・haiku 4.5 18.1→53.6 など)。Substack 著者の指摘どおり「Jev の前に分解の効果を示している」。ただし参照ラベル自体がワークフローの質問に答えて作られており、循環の疑いがある。

## 3. 第三者の指摘(共通)

- 独立の再現・較正曲線・論文が無い。confidence の統計量が未公開。分布シフト・敵対入力での較正は未検証。
- 「幻覚しない」は出力の**形**の制約であって**判断**の制約ではない(The Register・Substack とも)。
- 説明(理由文)が出ないので、監査・デバッグ・異議申立てには別の LLM が要る。
- `jev-latest` にしきい値を結ぶとモデル更新で挙動が変わる(版の固定が要る)。

## 4. 本シミュレーションへの当てはめ(親の見立て・未リサーチ=expedient)

**合う場所(型付き判断で足りる呼)**
1. **行動語の選択**: 24 語(v2 は 25 語)の Choice(≤255 に収まる)。確率分布が返るので、**エンジン側の乱数で分布から抽選**すれば「LLM 由来の多様性」を保ったまま決定論(seed)にできる。
2. **行き先の選択**: R-37 の H(エンジンが候補 k=4 を出し LLM が選ぶ)は**そのまま Choice 質問**。
3. **起床の門**: 「この体はいま考え直すべきか」の Noul(驚き・関連度の判定)。L4 の枠を同じにして思考の質を上げる案(第235 の回答の「予測誤差で起こす」と同じ場所)。
4. **未定義行動の裁定(段2)**・**LLM 出力の検査(guardrail)**: ベンダーの想定用途そのもの。

**合わない場所**
- **発話(ひと言)・理由文**は出ない=会話・内省・テープの「理由」列(診断に使っている)は LLM のまま。判断主体が 2 つになると holdout の落ち方の帰属が濁る(第235 の回答と同じ懸念)。
- **外部 API**: 状態文が米国西海岸のサーバーへ出る。体は合成なので個人情報は無いが、**封印データや現実データの値を state に含めない**規律が要る。レート制限が未公開で 5,000 体×1,440 tick(3.7 万呼/日)の吞み込みは未知。艦隊(借用 GPU)は現状ほぼ無料なので費用の比較軸が違う。
- 待機リスト・API キー(環境変数のみ)・版固定が要る。ユーザー判断事項。

**先に試せること(Jev 無しで・自前艦隊で)**: 「型付き質問」の**インターフェース**はモデルから切り離せる。同社の adapter は任意の LLM に Choice/Score/Noul を答えさせる(確率は LLM が書いた値を正規化するだけ)。**vLLM なら logprobs から本物の分布が取れる**ので、Qwen3-8B に「行動語の Choice(24 語)+行き先の Choice(k=4)」を 1 呼で答えさせる腕を作り、現行の 2 行形と P-6/P-8・行動分布・呼あたり出力トークンで比べられる。これは 5,000 体 1 腕(約 40 分)で、外部依存なし。

## 5. 結論(要点 3 つ)

1. Jev は「文字列を生成しない、型付き判断だけを確率つきで返す」モデル。**新しいのはアルゴリズムより製品の形(インターフェース)**で、中身(アーキテクチャ・RLCD・較正法)は非公開・論文なし・第三者検証なし。
2. 数値は全てベンダー測定。一致率は中位(Terra 並み・Opus 5/Sol に 5〜6 点劣る)。費用と遅延の主張は桁違いだが補助金の可能性を自認。
3. 本シミュレーションでは「行動語・行き先・起床」の型付き判断に当てはまり、「発話・理由」には当てはまらない。**まず自前艦隊で型付き判断のインターフェースを 1 腕試す**のが安く、外部 API と帰属の問題を持ち込まずに効果を測れる。Jev 本体を試すかは、待機リスト・API キー・状態文の外部送信の 3 点でユーザー判断。

## 出典(全て 2026-09-18 に親が実読)

- TypeSafe AI ブログ: https://typesafe.ai/blog/introducing-system-one-models-and-jev
- TypeSafe docs: https://docs.typesafe.ai/ ・ https://docs.typesafe.ai/introduction/quickstart ・ https://docs.typesafe.ai/primitives/choice ・ https://docs.typesafe.ai/primitives/score ・ https://docs.typesafe.ai/confidence
- TypeSafe 評価ページ: https://evals.typesafe.ai/
- System One adapter(MIT): https://github.com/typesafe-ai/system-one-adapter-python
- BusinessWire プレスリリース(2026-09-15): https://www.businesswire.com/news/home/20260915525333/en/TypeSafe-AI-Emerges-From-Stealth-With-$40M-in-Funding-With-New-Model-for-Composable-AI
- The Register(2026-09-16): https://www.theregister.com/ai-and-ml/2026/09/16/typesafe-ai-debuts-model-for-machines-that-plays-doom/5296711
- DataCamp(2026-09-16): https://www.datacamp.com/blog/system-one-models-jev
- Anthony Maio, Substack: https://anthonymaio.substack.com/p/jev-the-language-model-that-wont
