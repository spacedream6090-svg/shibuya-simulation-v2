# R5 認知詳細レーン答申(δ_think上限 / U19思考トークン方式 / T0-T1-T2昇格条件 / 記憶U1細部)

> **親検収(Fable・2026-09-07)**: 出典を親が一次確認した。✔=親が実読して数値一致。
> - ✔ Rubinstein 2007 Economic Journal(PDF実読): Ex.1 n=2,029 中央値41秒(T 37/B 50)・Ex.2 n=2,543 96秒(A 64/B 161/C 76/D 83)・Ex.4 Cat.A 126(22選択者157)/B 89/C 70・Ex.5 n=1,361(132/80/163/123秒)。「読解込みの応答時間」の定義文は抽出で見つからず(答申が引用した文言は親未確認)。同一問題内の選択肢差分=純熟慮増分13/56/83秒の算術は妥当。
> - ✔ Anthropic公式(実読): 「The budget is a target rather than a strict cap. … `max_tokens` remains the hard ceiling on total output.」(世界規則予算/生成制御/インフラ上限の3層分離の先例)。
> - ✔ Murre & Dros 2015 PLoS One(実読): 再現の節約率 20分0.547/1時間0.455/9時間0.380/**1日0.408**/2日0.418/6日0.344/31日0.041。「the classic forgetting curve … does show a jump at the 1 day retention interval」(睡眠固定の示唆)。**注**: 答申の「24h後保持0.21」は原典の値ではない(節約率は0.41)=GA 0.995/時(24hで0.887)との不一致という主張の方向は正しいが数値は訂正。
> - ✔ arXiv 2508.12140(実読): 「most models showing rapid improvement up to 256 tokens and diminishing returns beyond 512 tokens」(医療推論・Qwen3 1.7B-235B/DeepSeek-R1 1.5B-70B)。✔ arXiv 2505.11423(実読): 「explicit reasoning through CoT prompting can negatively impact the instruction-following abilities」・15モデル・IFEval/ComplexBench・classifier-selective reasoningが最良。
> - ✔ cl-nagoya/ruri-v3-30m(HF実読): 256次元・37Mパラメータ・Apache-2.0・JMTEB平均74.51・最大8,192トークン。
> - 既存台帳の「熟慮30-75秒」がForssbergの避難前時間由来という指摘は、既存台帳側の記述と整合(用途外流用=答申の判断は妥当)。Hoyer 1984の「13秒」は空欄のまま。arXiv 2506.07712・2604.10739・UCCI・FrugalGPT/RouteLLMは答申が実読と申告(親は未再読)。
> - 正典化: docs/research/v2-cognition-detail-research.md(R5の根拠)。


> 2026-09-07・Opus 5 リサーチサブ・全出典URL付き。**未確認は「空欄(未確認)」と明記**。推測は【推測】。
> リポジトリは読み取りのみ。子サブ未起動。

## 要約(10行)

1. **既存台帳の「熟慮30-75秒」の出典は Forssberg 2019(避難前時間)= 緊急時の用途**。日常の熟慮への流用であり、根拠としては弱い。
2. **代替の一次錨を発見: Rubinstein 2007(Economic Journal・n=2,029〜2,985/問・PDF全文実読)**。応答時間中央値 **41〜96秒**、「本能的」対「認知的」で **37 vs 50秒**・**70 vs 126-157秒**。
3. Rubinstein の応答時間は**読解込み**。ただし**同一問題内の選択肢間の差分**は読解が相殺されるので純熟慮時間になる → **Δ = 13〜83秒**。これが δ_think の直接錨。
4. **推奨 δ_think上限: T1 ≤ 325tok(13秒)/ T2通常 ≤ 2,048tok(82秒)/ T2重大 ≤ 7,500tok(300秒=既決の中断分割点と一致)**。α=0.04秒/tok は既決値を使用。
5. **U19: T1の思考トークン=0(非thinkingで2行形のまま)を推奨**。根拠3本(小モデルの長CoT劣化 / 予算飽和は256tok / CoTは書式順守を下げる)+ **予算の一次項が出力長**(o64→o128で+5.6h/シミュ日=W1直撃)。
6. **U19: T2は「世界規則としては上限なし」でよい**。実効上限は既決の7,500tok/ブロック分割規則が担う。艦隊予算は**打ち切りでなくクォータ(昇格閾値の引き上げ)**で守る(打ち切りは世界を歪める)。
7. **インフラ保護リミット分離には明確な先例**: Anthropic公式ドキュメント "The budget is a target rather than a strict cap … `max_tokens` remains the hard ceiling"。3層(世界規則予算 / 生成制御=Qwen3の停止句挿入・s1のbudget forcing / インフラ`max_tokens`)に分離。
8. **昇格条件**: FrugalGPT/RouteLLM/UCCI の閾値最適化(θ* = argmin コスト s.t. 制約)+ Generative Agents の「重要度和≥150で内省」を合成。閾値は **expedient**。
9. **記憶**: GAの指数減衰0.995/時は忘却曲線と定量的に合わない(24時間で0.887 vs 実測保持0.21)。**べき/対数族(ACT-R d=0.5)+T2統合済みの「24時間ブースト」**を推奨(Murre&Dros 2015)。
10. **埋め込みは Ruri-v3-30m(256次元・JMTEB 74.51・Apache-2.0)を推奨** → int8で12本=3.1KB/体、既決7.7KBを下回り **6.1KB/体・40万体で2.4GB**。

---

## 1. δ_think(熟慮時間)の上限

### 1-1. 既存台帳「熟慮30-75秒」の出典確認 → **緊急時の用途外流用**

`docs/research/v2-perception-latency-research.md` L14/L429/L469 が根拠。原典は **Forssberg et al. 2019, Fire Technology 55(6):2491-2513** の **pre-movement time(避難前時間)**:事務所64.4秒/映画館30.0-44.0秒/百貨店35.9秒/学校74.9秒、実験40件・n=2,486。

- **問題**: これは「火災警報が鳴ってから動き出すまで」であり、日常の購買・行き先変更・誘いへの応答とは事象クラスが違う。同答申自身が C5 を「**expedient(用途流用)**」と自己申告している(L469)。
- **本ラウンドでの再確認**: 論文PDF本体は **空欄(未確認)**(既存答申も springerprofessional のプレビュー数表のみ。n合計が2,468で本文2,486と18ずれる旨も既記載)。今回も本体は取得できず。
- **結論**: 30-75秒は **避難・介入レーン(C5)の値としては維持**。ただし **日常の熟慮の根拠には使えない**。日常用には1-2の錨を新設すべき。

### 1-2. 新しい一次錨: Rubinstein 2007(PDF全文抽出・実読)

Ariel Rubinstein, "Instinctive and Cognitive Reasoning: A Study of Response Times", *The Economic Journal* 117(523):1243-1259 (2007). PDF: https://arielrubinstein.tau.ac.il/papers/78.pdf (pymupdfで本文抽出・実読)

抄録の引用:

> "Lecture audiences and students were asked to respond to virtual decision and game situations at gametheory.tau.ac.il. Several thousand observations were collected and the response time for each answer was recorded. … choices made instinctively, that is, on the basis of an emotional response, require less response time than choices that require the use of cognitive reasoning."

測定定義(重要):

> "Response time is defined here as the number of seconds between the moment that our server receives the request for a problem until the moment that an answer is returned to the server."

→ **読解時間を含む**。生の中央値をそのまま δ_think にしてはいけない。

| 例 | 課題 | n | 全体中央値 | 選択肢別中央値 |
|---|---|---|---|---|
| Ex.1 | 2×2ゲーム | 2,029 | **41秒** | 本能的T=**37秒** / 認知的B=**50秒** |
| Ex.2 | 支配戦略の逐次消去 | 2,543 | **96秒** | A=64 / B=**161秒** / C=76 / D=83 |
| Ex.3 | Traveler's dilemma | 2,985(講演)/1,573(授業) | 77秒 / 88秒 | 180=87-99秒 / 300=72-80秒 |
| Ex.4 | Centipede型 | 2,423 | 86秒 | Cat.A(深い推論)=**126秒**(22選択者は**157秒**) / Cat.B=89秒 / Cat.C(無思考)=**70秒** |
| Ex.5 | — | 1,361 | — | 本能的101=123秒 / 認知的98-100=**163秒** / 無思考2-97=80秒 |

**読解を相殺した純熟慮増分 Δ(同一問題内の選択肢間差)**:

- Ex.1: 50 − 37 = **13秒**
- Ex.4: 126 − 70 = **56秒**(157 − 70 = 87秒)
- Ex.5: 163 − 80 = **83秒**

→ **Δ ≈ 13〜83秒**。「同じ文章を読んだうえで、追加でどれだけ考えたか」の実測帯。同一刺激内の差分なので読解速度の個人差も一次的に相殺される。

**独立の裏付け(帯が重なる)**: Forssberg の避難前時間 30-75秒、Darley&Latané 1968 の通報潜時 52/93/166秒(既存台帳L424)、既存台帳のCRT中央値19-25秒。**13-83秒という帯は3系統に挟まれる**。

### 1-3. 低関与の日常購買(短い側の錨)

- Hoyer, Wayne D. (1984) "An Examination of Consumer Decision Making for a Common Repeat Purchase Product", *Journal of Consumer Research* 11(3):822-829, https://doi.org/10.1086/209017 —— **書誌・抄録は実読**。ただし **「洗剤選択に平均13秒・多くは1パッケージのみ手に取る」という数値は本文未確認=二次(検索要約・業界サイト経由)**。Oxfordの抄録頁に秒数の記載はない(実読で確認)。→ **一次確認が必要(親の確認リスト#5)**。
- 同帯の二次情報: 「店頭でのブランド選択の平均13秒」(Ehrenberg-Bass由来として流通)、「1パッケージへの注視1.9秒」(EyeSee)。**いずれも査読一次未確認=空欄**。

### 1-4. 誘いへの応答(会話レーン)

- Kendrick K.H. & Torreira F. (2015) "The Timing and Construction of Preference: A Quantitative Study". **PDF抽出に失敗=一次未確認(空欄)**。検索要約では「195件の選好/非選好応答を分析。**700ms以上の間隙**で非選好応答の比率が明確に高くなる」。
- 既決の δ_min=0.2秒(Stivers 2009)と整合。**誘いへの応答は熟慮レーンでなく会話レーン**(0.2-0.7秒)で扱い、「断る/迷う」は δ_think を伸ばすのでなく **間隙クラスの選択**として表現するのが実測に合う。

### 1-5. 感覚運動レーンと熟慮レーンを分ける根拠

1. **実測分布が2桁離れる**: 単純反応時間213-231ms(Woods 2015・既存台帳で実読)対 熟慮増分13-83秒。
2. **同一被験者・同一刺激で選択肢によって時間が1.35-2.2倍変わる**(Rubinstein Ex.1/Ex.4/Ex.5)=「速い経路」と「遅い経路」が同一課題内で共存する直接証拠。
3. **アーキテクチャの先例**: Talker-Reasoner(arXiv:2410.08328・抄録実読)——
   > "a 'Talker' agent (System 1) that is fast and intuitive, and tasked with synthesizing the conversational response; and a 'Reasoner' agent (System 2) that is slower, more deliberative, and more logical, and is tasked with multi-step reasoning and planning"

   既存台帳の Reflex First, Reflect Later(arXiv:2506.07223)と合わせて2本。
4. **注意**: Rubinstein の「無思考(reasonless)」カテゴリが70-80秒である事実は、「速い=数百ms」ではなく「速い=読解時間+α」であることを示す。**レーン分離は正しいが、遅い側の床は0でなく読解時間**。

### 1-6. 実装上の矛盾候補(親へ・要判断)

**観測プレフィックス(B0-B4・共有1000tok+個体500tok)に α_read=0.18秒/tok を掛けてはならない。** 掛けると1回の起床で 1,500tok × 0.18 = **270秒**となり、δ_think(13-83秒)を桁で上回って世界が止まる。

- 提案: **δ_read は「今回新しく到着した情報」にのみ課金**(看板・掲示・受信メッセージ・会話相手の発話)。プレフィックスは「既にその場にいる者の常在的な気づき」であり読解行為ではない。
- これは知覚契約 §1条3(観測は起床時点の現在形)と整合するが、**明文化されていない**ので契約書に1条追加すべき。

---

## 2. U19 思考トークン方式

### 2-1. (a) 小型モデルで思考トークンを絞ったときの実証

**① 予算は256トークンで飽和し、512超は逓減**

"Exploring Efficiency Frontiers of Thinking Budget in Medical Reasoning: Scaling Laws between Computational Resources and Reasoning Quality" arXiv:2508.12140 (2025-08-16) https://arxiv.org/html/2508.12140v1 (HTML実読)

- テストした予算: **0, 64, 128, 256, 512, 1024, 無制限**。モデル: **Qwen3 1.7B / 4B / 8B / 14B / 32B / 235B** と DeepSeek-R1 1.5B〜70B。
- 引用: "most models show rapid improvement up to 256 tokens and diminishing returns beyond 512 tokens"
- 3レジーム: high-efficiency(0-256)/ balanced(256-512)/ high-accuracy(512+)。
- 小型ほど thinking の利得が大きい(**小型15-20% / 大型5-10%**)——ただしこれは「thinkingあり対なし」の差であり、「長くすればもっと良い」ではない。

**② 小モデルは長CoTで壊れる**

"Through the Valley: Path to Effective Long CoT Training for Small Language Models" arXiv:2506.07712 https://arxiv.org/html/2506.07712 (HTML実読)

- 引用: "small language models (SLMs; ≤3B parameters) trained on limited long CoT data experience significant performance deterioration" / "models trained on only 8k long CoT examples lose up to 75% of their original performance"
- Gemma3-1B はベースラインの約25%まで低下。Qwen2.5-14B でも50%→45%。

**③ CoTは書式順守(instruction following)を下げる**

"When Thinking Fails: The Pitfalls of Reasoning for Instruction-Following in LLMs" arXiv:2505.11423 (抄録実読)

- 引用: "Explicit CoT reasoning can significantly degrade instruction-following accuracy"(IFEval・ComplexBench、**15モデル**で確認)。理由は "neglect simple constraints or introduce unnecessary content"。緩和策として "classifier-selective reasoning"(=考えるかどうかを分類器で選ぶ)が最有効。
- **v2への直撃**: 品質プローブで「厳密JSONは推論を壊す/2行形は書式順守1.000」が既に実測済み。**T1でthinkingを開くと、その1.000が危険にさらされる**。③は我々の実測と同方向。

**④ 長すぎる思考は精度そのものを下げる(逆U字)**

"When More Thinking Hurts: Overthinking in LLM Test-Time Compute Scaling" arXiv:2604.10739 (2026-04-12) https://arxiv.org/html/2604.10739v1 (HTML実読)

- 引用: "Both models exhibit clear diminishing returns: early tokens provide substantial gains (+3.2% per 500 tokens for R1-32B), while beyond 12K tokens, marginal utility turns negative."
- R1-32B/AIME: 12Kトークンで55.8%がピーク、16Kで54.9%へ低下。最適予算は難易度依存で "from 1.0K tokens for Level 1 to 7.5K for Level 5"。
- **注意**: 検索エンジン要約が出した「1100→15980tokで87.3%→70.3%」は**本論文の測定値ではない**(本文では別論文の引用)。**採用しない**。

**⑤ 予算の一次項は出力長(v2固有の決定打)**

既決: W1内で **o128=20.4h / o64=14.8h/シミュ日**(知覚契約 BN-4/BN-5)。差 5.6h が出力64トークン分。

- T1に思考256トークンを与えると出力は 64→320(5倍)。線形外挿で **概算 14.8h × 5 ≈ 74h/シミュ日**【推測=線形外挿。prefill律速のため過大評価の可能性あり・要実測】→ **W1(≤24h/シミュ日)を大幅超過**。
- **したがってT1の思考予算は 0(または ≤32tok)しか成立しない**。これは文献より強い制約。

### 2-2. (b) 大型モデルで上限なしにしたときのコストと利得

- 利得: 上記④の通り、難問では 7.5K トークンまで単調に伸びる(Level 5)。Qwen3 技術報告も "Qwen3 demonstrates scalable and smooth performance improvements correlated to the allocated thinking budget"(HTML実読)。
- コスト(v2の実数): T2呼数 = 内省1.05回/体/日 × 40万体 = **42万呼/日**。1呼2,048思考トークンなら **8.6億トークン/日**。1呼7,500トークンなら **31.5億トークン/日**。
  - 現行T1の総出力は 400万呼 × 64tok = **2.56億トークン/日**で14.8h。→ **T2を無制限にすると桁で予算を割る**(32B AWQ はさらに遅い)。
- **結論**: 世界規則としての上限は置かなくてよいが、**艦隊予算は別途クォータで守る必要がある**(2-4・5-2)。

### 2-3. (c) 7,500tok毎の中断分割(既決)との両立

既決規則: 線形維持・対数圧縮不採用・**N>7,500tok(≈5分)は中断30秒-2分を挟んだ断続に分割**。

**両立の形**: 思考予算 B を「**1ブロックの上限**」として定義し、**総量ではなく分割の単位**にする。

- B_block = 7,500tok(= 300秒)。これを超える思考は物理的に生成しない。
- 続きが要るときは **世界時刻を30-120秒進め、中断イベントを挿入し、新しい1呼として再開**(前ブロックの結論を要約1行で引き継ぐ)。
- **技術的先例(実装手段そのもの)**:
  - s1 の budget forcing(arXiv:2501.19393・抄録実読): "forcefully terminating the model's thinking process or lengthening it by appending 'Wait' multiple times to the model's generation"。**中断=終了句の強制挿入、再開="Wait"相当の継続句**。
  - Qwen3 も同型の停止句を持つ(技術報告 HTML実読): "when the length of the model's thinking reaches a user-defined threshold, we manually halt the thinking process" + 挿入文 "Considering the limited time by the user, I have to give the solution based on the thinking directly now."
  - → **v2では挿入文を日本語の中断句に差し替える**(例: 「ここで一度考えるのをやめ、今わかっていることだけで決める。」)。**世界の因果(中断)と生成制御が一致する**形になる。
- **整合の要点**: 「予算=時間」なので、**1ブロック上限 7,500tok は δ_think ≤ 300秒/ブロックと同義**。新たに上限を決める必要はない。決めるべきは「**通常レーンの上限**」で、それが 2,048tok(82秒)。

### 2-4. (d) インフラ保護リミットと世界規則の分離: 先例

**Anthropic公式ドキュメント(実読)** https://platform.claude.com/docs/en/build-with-claude/extended-thinking

> "The `budget_tokens` parameter sets a **target** for how many tokens Claude can use for its internal reasoning process."
> "**The budget is a target rather than a strict cap.** Actual token usage varies with the task, and Claude may stop reasoning well before the budget is exhausted; **`max_tokens` remains the hard ceiling on total output**."
> 制約: "Minimum of 1,024 tokens." / "Less than `max_tokens`."

**Task Budgets(同社ドキュメント・実読)**:

> "A task budget gives Claude a token ceiling for an agentic loop so it paces itself and finishes gracefully instead of being cut off — **distinct from `max_tokens`, which is an enforced per-response ceiling the model is not aware of**."

→ **この2文が、求めていた分離の先例そのもの**。「モデルが認識して自分でペース配分する助言的予算」対「モデルが知らない強制的天井」。v2に写像すると:

| 層 | 名前 | 誰が知るか | 超えたら | v2の値 |
|---|---|---|---|---|
| ① 世界規則 | 思考予算 B_world | エージェント(プロンプト内で明示) | **中断イベント**(世界の因果として記録) | T1=0 / T2通常2,048 / T2重大7,500 |
| ② 生成制御 | 停止句注入 / budget forcing | サーバ側デコーダ | 思考を打ち切り2行形へ着地 | B_world 到達時 |
| ③ インフラ保護 | `max_tokens` / `max_model_len` | 誰も(世界外) | **インシデント**(ラン品質フラグ) | B_world × 1.5 + 出力余白 |

**規律**: ③が発火したステップは「世界規則でなくインフラで決まった」ので **`expedient` 汚染としてカウンタに計上し、ablationで結果を駆動していないことを示す**。③が常時発火する設定は、世界がGPUで決まっている状態=再現性の破壊(既存答申L319の「GPU速度で世界が変わる」批判と同じ穴)。

---

## 3. T0/T1/T2 の昇格条件(LOD)

### 3-1. 先行の規則と実測

| 系統 | 規則 | 実測 | 出典 |
|---|---|---|---|
| **カスケード(スコア閾値)** | 安いモデルで答え、スコアが閾値未満なら上位へ | GPT-4同等で**最大98%コスト減**、または同コストで**精度+4%** | FrugalGPT arXiv:2305.05176(抄録実読) |
| **ルータ(選好学習)** | クエリを見て強/弱モデルへ振り分け | "significantly reduces costs — by over 2 times in certain cases — without compromising the quality"(抄録実読)。**「MT Bench 85%減・GPT-4品質95%」は抄録に無い=二次(空欄)** | RouteLLM arXiv:2406.18665 |
| **較正済み不確実性** | 誤り確率 p̂(x)=g(u(x)) を等調回帰で較正し閾値 θ で分岐 | 75,000本の実運用NERクエリでF1=0.91時 コスト2.08(FrugalGPT型2.24より8%安・エントロピー2.31より11%安)。大モデル一択比で**31%削減(95%CI 27-35%)** | UCCI arXiv:2605.18796(HTML実読) |
| **二重過程アーキテクチャ** | Talker(S1)が常時応答、Reasoner(S2)が非同期に信念を更新 | 数値なし | arXiv:2410.08328(抄録実読) |
| **社会シム内の昇格** | **直近イベントの重要度スコア合計が閾値(150)を超えたら内省** | **1日2〜3回**発火 | Generative Agents arXiv:2304.03442(HTML実読) |

引用(GA):

> "reflections when the sum of the importance scores for the latest events perceived by the agents exceeds a threshold (150 in our implementation)"
> "In practice, our agents reflected roughly two or three times a day"

引用(UCCI):

> "θ* = argmin_θ Cost^(π_θ) s.t. Acc^(π_θ) ≥ τ" / "π_θ(x) = s if p̂(x) ≤ θ; ℓ if p̂(x) > θ"

**"When to Think Deeply: Inhibitory Deliberation" (arXiv:2606.06745, He & Feng, 2026-06-08)**: 取得した要約が当方のプロンプト語をそのまま反映しており信頼できないため **空欄(内容未確認)**。書誌のみ記載。

### 3-2. v2で使える閾値の形

**設計原則**: 昇格判定は **エンジン側の決定論的スコア**で行う(LLMに「考えるべきか」を聞かない)。理由 ①追加呼が要らない ②再現性(同seed同結果) ③憲法「状態と集約はエンジン」。UCCI が示すのは「較正された数値で閾値を切ると最安」であって「判定にLLMを使え」ではない。

```
S(e) = w1·surprise + w2·stake + w3·novelty + w4·recent_failures + w5·social_exposure
```

- **surprise**: 予測モジュール(D-R2)の予測と観測の乖離(既存出力の再利用=追加コスト0)
- **stake**: 可逆性・金額・関係の強度(エンジンが持つ台帳値)
- **novelty**: (場所ID, 行為種別)の本人内出現回数の逆数
- **recent_failures**: 直近k回の行動が意図と不一致だった回数
- **social_exposure**: 同席人数・被注視(知覚契約⑤)

昇格規則(GA型の**累積**とカスケード型の**即時**の併用):

- **即時昇格 T1→T2**: S(e) ≥ θ_imm(重大イベント)
- **累積昇格 T1→T2**: Σ_日 S(e) ≥ θ_cum(GAの150に相当)→ 日次内省とは別枠の「引っかかり内省」
- **降格 T1→T0**: 同一(文脈, 行動)対の連続一致が n 回 → 習慣化。ただし Lally 2010 の中央値66日はシミュ内時間では届かないので **ペルソナ種+由来フラグ**の既決を維持。

**θの決め方(expedient明示)**: θ は理論値でなく**予算方程式の解**として決める。

```
θ* = argmin_θ (T2呼数)   s.t. 昇格率 = 目標(0.02回/体/日) かつ ablationで主要指標が不変
```

UCCIと同型だが、**制約が精度でなく呼数予算**である点が違う。→ **`expedient` タグ必須・感度試験で「θが結果を駆動していない」ことを示す**。

**予算の目安**: 日次内省1.05回/体/日(既決)+ 昇格0.02回/体/日 → T2は **42.8万呼/日**。昇格を0.05にすると46.2万呼(+8%)。**昇格枠は内省枠の2〜5%に収める**のが現実的。

**観測可能性の規律**: 昇格した/しなかったを全件ログ(v1で「ルール層の決定は痕跡ゼロ=LLM被覆率が原理的に計算不能」という失敗があった・v1 IMPLEMENTED 第132)。

---

## 4. 記憶 U1 ハイブリッドの細部

### 4-1. (a) retrieval採点の重みと減衰

**GA原典(HTML実読)**:

> "Our decay factor is 0.995" / "On the scale of 1 to 10, where 1 is purely mundane … and 10 is extremely poignant" / relevance は "the cosine similarity between the memory's embedding vector and the query memory's embedding vector" / **"In our implementation, all α's are set to 1"**

**GA式の問題(本答申の指摘)**: 0.995^h は時間hの指数減衰。**24時間後 = 0.995^24 = 0.887**。一方 Ebbinghaus 系の実測保持は1日で **0.21**(4-2)。**31日(744h)では 0.995^744 = 0.024 で実測0.08より速い**。つまり **指数関数はそもそも忘却曲線の関数形ではない**(実測はべき/対数族)。GA自身はこれを認知的主張としては述べていない(検索用ヒューリスティック)。

**代替1: ACT-R base-level activation(認知アーキテクチャの標準)**

```
B_i = ln( Σ_j t_j^(−d) ),   d = 0.5
```

- 検索(実読要約): 「ACT-Rコミュニティで **0.5 が d の既定値**として広範な応用にわたり定着」。Anderson & Schooler (1991) の合理分析=環境の統計的規則性への適応。
- 長所: **べき法則**なので実測の関数形に合う。**再想起で t_j が増えるので「思い出すほど残る」が追加パラメータなしで出る**(既決の「想起で減衰定数を緩める」と同じ効果)。
- 出典: https://link.springer.com/article/10.1007/s42113-018-0015-3 (**書誌のみ・本文未読=空欄**) / https://www.ai.rug.nl/~niels/publications/taatgenLebiereAnderson.pdf (**未読=空欄**)

**代替2: MemoryBank(LLMエージェント側の先行)** — AAAI 2024, 38:19724-19731, https://ojs.aaai.org/index.php/AAAI/article/view/29946(**書誌のみ実読・本文未読=空欄**)。忘却曲線に着想した指数減衰で記憶強度を更新、頻繁にアクセスされ重要度の高い記憶は強化される。

**推奨採点式(v2)**:

```
score(m|q) = w_r · A(m) + w_i · importance(m) + w_v · relevance(m|q)
A(m)       = ln( Σ_j (Δt_j + 1)^(−d) )          # ACT-R base-level・Δt_j は想起履歴からの経過時間
```

- w は初期 (1,1,1)(GA準拠)で **expedient**、ablationで感度確認。
- **importance はLLM採点でなくエンジン採点**。GAはLLMに1-10を聞くが、40万体×日次では呼数が桁で増える。**S(e)(3-2)の離散化を流用すれば追加呼0**。

### 4-2. (b) 忘却曲線の代表値(Murre & Dros 2015・実読)

https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0120644 (PLOS ONE, 2015)

| 間隔 | Dros(再現) | Ebbinghaus(原典) | Mack & Seitz |
|---|---|---|---|
| 20分 | 0.42 | 0.58 | 0.57 |
| 1時間 | 0.36 | 0.45 | 0.40 |
| 9時間 | 0.26 | 0.26 | 0.22 |
| 1日 | 0.21 | 0.21 | 0.24 |
| 2日 | 0.20 | 0.18 | 0.22 |
| 6日 | 0.11 | 0.10 | 0.11 |
| 31日 | 0.04 | 0.08 | 0.09 |

当てはめ関数(引用):

- べき関数(Ebbinghaus 1880): **Q(t) = [1 − (2/t)^0.099]^0.51**(Drosの当てはめ指数は 0.523 と 0.101)
- 対数関数(Ebbinghaus 1885): **Q(t) = 1.84 / ((log t)^1.25 + 1.84)**
- **24時間ジャンプ**: "the forgetting curve is not completely smooth but most probably shows a jump upwards starting at the 24 hour data point"。boost の大きさは Ebbinghaus 0.030 / Mack 0.131。睡眠固定化と整合。

**v2への写像(既決設計を強化する形)**:

- 生エピソード = べき/対数族で減衰(ACT-R d=0.5 が良い近似)。
- **T2夜間統合を通過した gist は「24時間ブースト」を受け、減衰指数を下げる**(例 d: 0.5 → 0.25)。これは既決の「統合を通過した記憶は減衰が大幅に緩む」に**定量的根拠を与える**。
- boost の 0.030-0.131 は savings 尺度なので **そのままv2に入れられない=expedient**、ablationで幅を振る。

### 4-3. (c) バイト予算と日本語埋め込みモデル

**推奨: cl-nagoya/ruri-v3-30m**(モデルカード実読 https://huggingface.co/cl-nagoya/ruri-v3-30m)

- パラメータ **37M**(埋め込み除くと10M)、**出力256次元**、最大系列 **8192**、**JMTEB平均 74.51**、**Apache-2.0**。
- 上位: ruri-v3-70m=75.48 / 130m(512次元)=76.55 / 310m(768次元)=77.24。
- プレフィックス必須: 検索は "検索クエリ: " / "検索文書: "、分類は "トピック: "、汎用は空文字列。**書き込み・読み出しで固定すること**(取り違えると性能が落ちる)。

**既存答申との比較**: 既存候補は Ruri-small(768次元・JMTEB 71.53)/ mE5-small(384次元・67.71)。**Ruri v3-30m は 256次元でJMTEB 74.51 = 次元は1/3、スコアは上**。→ **乗り換え推奨**。

**バイト予算(再計算)**:

| 項目 | 既決 | 推奨(Ruri-v3-30m) |
|---|---|---|
| 構造化スロット | 3.0KB | 3.0KB |
| 統合ベクタ | 12本 × 388B(384次元int8+4B) = 4.7KB | 12本 × 260B(256次元int8+4B) = **3.1KB** |
| 合計/体 | **7.7KB** | **6.1KB** |
| 40万体 | 3.1GB | **2.4GB** |

**埋め込み生成のコスト**: 統合は夜間のみ、1体あたり新規gistは1-3本/晩 → **40万〜120万埋め込み/シミュ日**。37Mパラメータ・256次元は極小なので、**vLLMに同居させずONNX int8のCPU/別プロセスで回すことを推奨**(「埋め込み生成がLLM推論とGPUを奪い合う」という既存答申の核心的懸念への直接の答え)。**スループットは実測必須=空欄(未計測)**。

### 4-4. (c続き) 埋め込みなしで足りる範囲

**エンジンが生成した事象は埋め込み不要**。理由: 場所・人・物・行為はすべてIDを持つので、「同一事象を各人が別語で記録する」問題が原理的に起きない(既存答申が(a)案を退けた理由がここでは当てはまらない)。

→ **埋め込みが要るのは自由テキスト由来の記憶だけ**: ①会話の要約 ②噂・口コミ ③広告/掲示の文言 ④自書の内省文。

→ 推奨: **gist を「構造化ヘッダ(ID群・時刻・場所・関与者)+ 自由文1-2文」の二部構成にし、埋め込むのは自由文だけ**。検索は「ID一致で絞る → 残りをコサインで並べる」の2段。per-agent 8-16本なら全走査µs級(既存答申の結論を維持)。

### 4-5. (d) 日次内省でgist化する規則の先行例

| 先行 | 規則 | 数値 | 出典 |
|---|---|---|---|
| Generative Agents | 重要度和 ≥150 で reflection、記憶→高次の洞察へ | 1日2-3回 | arXiv:2304.03442(実読) |
| MemoryBank | 日次の会話要約・イベント要約・人格/気分評価を保存し、忘却曲線で強度更新 | — | AAAI 2024(**書誌のみ・本文未読**) |
| Lyfe Agents | Summarize-and-Forget(要約して捨てる) | — | arXiv:2310.02172(既存答申・**本ラウンド未確認**) |
| **Sleep-time compute** | アイドル中に raw context → learned context へ事前推論 | テスト時計算を約5倍削減、精度 GSM-Symbolic +13% / AIME +18%、関連クエリ間の償却でクエリ単価2.5倍削減 | arXiv:2504.13171(**検索要約のみ・抄録未実読=一次未確認**) |

→ **v2の「就寝同期の日次内省1.05回/日でgist化」は4系統に先例があり、独自ではない**。特に sleep-time compute は「夜に考えておくと昼の計算が減る」を数値で示しており、**内省をコストでなく投資として説明できる**(ただし数値は一次未確認)。

**推奨する内省の出力契約(呼数を増やさない形)**:

1. 当日の生イベント(構造化スロット)を入力に、**最大3本の gist** を出力(ヘッダ+自由文1-2文)。
2. gist は importance(1-10でなく S(e) の離散化)と ID群を必ず持つ。
3. 生イベントは**捨てず縮める**(構造化スロットのまま、自由文だけ落とす)= 既決の「統合前の生イベントの意味的想起は失う」と整合。
4. gist 生成時に **24時間ブースト**を付与(4-2)。

---

## 5. 推奨(決定案)

### 5-1. δ_think の上限(レーン別)

α_think = 0.04秒/tok(既決)を用いる。

| レーン | 起動 | 思考トークン上限 B | δ_think上限 | 根拠 |
|---|---|---|---|---|
| **L0 反射/習慣(T0)** | 予期あり・既習慣 | 0 | **0**(δ_percのみ) | Evans&Stanovich・Stivers(既決) |
| **L1 速い判断(T1)** | 通常の起床 | 出力64tok(2行形)・思考0 | **2.6秒**(頭打ち325tok=13秒) | Rubinstein Ex.1 の純熟慮増分 **13秒** |
| **L2 通常熟慮(T2)** | 昇格・日次内省 | **2,048tok** | **82秒** | Rubinstein Ex.5 の増分 **83秒**(Ex.4は56/87秒) |
| **L3 重大熟慮(T2)** | 重大イベント・避難/介入 | **7,500tok/ブロック**(既決の分割点) | **300秒/ブロック**・中断30-120秒・最大3ブロック | 既決(Moxley 2012)+ Forssberg 30-75秒/Darley&Latané 52-166秒が内側に収まる |
| **L4 会話応答** | ターン交替 | — | δ_min 0.2秒・非選好は0.7秒級の間隙 | Stivers 2009(既決)+ Kendrick&Torreira(**一次未確認**) |

- **δ_think の絶対上限 = 300秒/ブロック、900秒/事象(3ブロック)**。それを超える思考は世界に存在しない(=翌日の内省へ回す)。
- **L1の325tokは「頭打ち」であって既定値ではない**。既定は o64(2.6秒)。
- **expedient明示**: L2の2,048tok は Rubinstein の**上側の増分**を採った値。中央値を採るなら56秒(1,400tok)。**ablationで {1,024 / 2,048 / 4,096} を振り、結果が動かないことを示すまで expedient**。

### 5-2. U19 の定式化

```
# ① 世界規則(プロンプトに明示・エージェントが認識する)
B_world(T1)            = 0       # 非thinking。理由行が思考の代替
B_world(T2, routine)   = 2048    # 82秒
B_world(T2, critical)  = 7500    # 300秒 = 1ブロック(既決の分割点)

# ② 生成制御(サーバ側・budget forcing)
if thinking_tokens >= B_world:
    inject("<日本語の中断句>")            -> 2行形へ強制着地
    emit WorldEvent(interrupted=True, at = t + α_think * B_world)

# ③ インフラ保護(世界外・モデルは知らない)
max_tokens    = ceil(1.5 * B_world) + 96
max_model_len = 忠実度プロファイル固定値
if stop_reason == "length" (max_tokensによる):
    counter["infra_clip"] += 1        # インシデント。expedient汚染として計上・ablation対象

# ④ 艦隊予算(打ち切りでなくクォータ)
if 日次T2トークン残高 < 閾値:  θ_imm/θ_cum を引き上げて昇格率を下げる(run manifestに記録)
```

- **T1 = 思考0**: ①256tok飽和(2508.12140)②小モデル長CoT劣化(2506.07712)③CoTが書式順守を下げる(2505.11423)④**予算**(o64→o320でW1超過)。**④が決定的**。
- **T1の絞り値の較正(親評価④への答え)**: 出力長感度は o64/o128 で取得済み。追加で **{0, 32, 64, 128} 思考トークン × 品質プローブ(書式順守・行動妥当性)** を回す。**思考>0にした瞬間に書式順守1.000が崩れるか**が実質的な合否。
- **T2 = 世界規則上は上限なし**(ユーザー提案を採用)。実効上限は既決の7,500tok/ブロック分割規則が担うので、**新たな上限を置かない**(親評価①への答え)。
- **艦隊予算は打ち切りでなくクォータで守る**: 生成途中の打ち切りは**禁止**(世界が歪む・再現性が壊れる)。枯渇時は「T2に行かない」で調整する。
- **会話中のT2長考の場面規則(親評価③への答え)**: 会話ターン中は B_world(T2, routine) を使わない。会話は L4(δ_min 0.2秒)で回し、長考が要る場合は
  - (a) **「考える」を行為として発話**(「ちょっと考えさせて」)→ 相手側に間隙イベントを生成、
  - (b) **その場では L1 で答え、T2昇格は事後に非同期**(Talker-Reasonerと同型・信念だけ後から更新)。
  - **既定は (b)**。(a) は stake が閾値超のときのみ。理由: 会話中に82秒沈黙するエージェントが多発すると会話が壊れる(実測: 非選好応答でも700ms級)。

### 5-3. 昇格条件の式

```
S(e) = w1·surprise + w2·stake + w3·novelty + w4·recent_failures + w5·social_exposure   # 全項エンジン算出
T0 -> T1 : 文脈が習慣の前提条件から外れた(決定論)
T1 -> T2 : S(e) >= θ_imm                (即時)
           OR  Σ_日 S(e) >= θ_cum       (累積・GAの150に相当)
T1 -> T0 : 同一(文脈, 行動)対が n 回連続一致(習慣化)
θ_imm, θ_cum := argmin (T2呼数)  s.t.  昇格率 = 0.02回/体/日  かつ  ablationで主要指標が不変
```

- **w1..w5 と θ は全て `expedient`**。文献に対応値はない(UCCIは較正手順を、GAは閾値150という1例を与えるだけ)。
- **感度試験**: θ を ±50% 振って主要指標(移動分布・経済フロー・情報伝播)が動かないことを示す。動くなら θ が世界を駆動している=不採用。

### 5-4. 記憶の採点式・減衰・バイト予算・埋め込み方針

```
score(m|q) = w_r·A(m) + w_i·importance(m) + w_v·relevance(m|q)      # w=(1,1,1) 初期・expedient
A(m)       = ln( Σ_j (Δt_j + 1)^(−d) )                              # ACT-R base-level
d          = 0.5  (生エピソード)  /  0.25 (T2統合済みgist = 24hブースト)
importance = S(e) の離散化(LLM採点しない=呼数0)
relevance  = cos(Ruri-v3-30m 埋め込み)   ※自由文部分のみ
```

- **バイト予算: 6.1KB/体(構造化3.0KB + 12本×260B)・40万体で2.4GB**(既決7.7KB/3.1GBから削減)。
- **埋め込み: cl-nagoya/ruri-v3-30m(256次元・JMTEB 74.51・Apache-2.0)**。プレフィックス "検索文書: "/"検索クエリ: " を固定。**GPUはLLM専用にし、埋め込みはCPU/ONNX int8の別プロセス**(スループット実測1本が採用条件=既存答申の宿題を継承)。
- **埋め込む対象は自由テキスト由来のみ**(会話要約・噂・広告文言・内省文)。エンジン生成事象はID一致で引く。
- **日次内省**: 最大3 gist/晩、ヘッダ(ID群)+自由文1-2文、24hブースト付与、生イベントは構造化のまま保持し自由文だけ落とす。

### 5-5. 根拠が無い/弱い部分(expedient宣言が必須の項目)

| 項目 | 状態 |
|---|---|
| L2 = 2,048tok(82秒) | Rubinstein の上側増分。**expedient**・ablation {1024/2048/4096} |
| θ_imm / θ_cum / w1..w5 | 文献値なし。**expedient**・予算方程式の解・感度試験必須 |
| 記憶採点の w=(1,1,1) | GA踏襲のみ。**expedient** |
| d=0.5 → 0.25 のブースト量 | Murre&Dros の boost は savings 尺度。**expedient** |
| T1 思考>0 時の艦隊時間 74h | **【推測】線形外挿**。実測必須 |
| Ruri-v3-30m のスループット | **未計測** |
| δ_read の課金対象(新着情報のみ) | 本答申の提案。**未決・契約書へ条を追加すべき** |

---

## 6. 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 引用文 | 確認すべき数値 |
|---|---|---|---|---|
| 1 | 日常/戦略的熟慮の応答時間中央値は41-96秒、読解を相殺した純熟慮増分は13-83秒 | https://arielrubinstein.tau.ac.il/papers/78.pdf | "The median response time (MRT) of the subjects choosing B was 50 seconds, which was much higher than the MRT for T which was only 37 seconds." / Table 4: "A 15% 126 sec … C 36% 70 sec" | Table 1: n=2,029・全体41秒/T=37/B=50。Table 4: n=2,423・A=126・22選択者=157・C=70。Table 5: n=1,361・98-100=163秒/2-97=80秒。**差分13/56/83秒の再計算** |
| 2 | 思考予算は256トークンで飽和、512超は逓減。Qwen3 1.7B-235Bで検証 | https://arxiv.org/html/2508.12140v1 | "most models show rapid improvement up to 256 tokens and diminishing returns beyond 512 tokens" | 予算水準 0/64/128/256/512/1024/inf、モデル一覧に Qwen3-8B が含まれるか、"小型15-20% vs 大型5-10%" の帰属先 |
| 3 | 助言的な思考予算と強制的天井は別物(インフラ分離の先例) | https://platform.claude.com/docs/en/build-with-claude/extended-thinking | "The budget is a target rather than a strict cap. … `max_tokens` remains the hard ceiling on total output." | 最小1,024・"Less than max_tokens" 制約・Task Budgets の "distinct from max_tokens, which is an enforced per-response ceiling the model is not aware of" |
| 4 | 忘却曲線は指数でなくべき/対数族。24時間で保持0.21。24hブーストあり | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0120644 | "the forgetting curve is not completely smooth but most probably shows a jump upwards starting at the 24 hour data point" | 保持値表(20分0.42-0.58 … 31日0.04-0.09)、Q(t)=[1−(2/t)^0.099]^0.51、boost 0.030/0.131。**GAの 0.995^24=0.887 との乖離の再計算** |
| 5 | Hoyer 1984 の「洗剤選択13秒・1パッケージのみ」= **未確認**(書誌のみ確認済み) | https://doi.org/10.1086/209017 | (Oxford抄録に秒数の記載なし・実読で確認) | 本文の平均秒数・検査パッケージ数。**取れなければ日常購買レーンの錨は空欄のままにし、Rubinsteinのみで組む** |

**併せて確認したい2件(重要度は下)**:

1. Forssberg 2019 本体PDF(30-75秒の分布パラメータの表記規約・n=2,486 vs 2,468 のずれ)—— 既存答申からの持ち越しで**本ラウンドも未確認**。
2. Generative Agents の "all α's are set to 1" / "threshold (150)" / "two or three times a day"(https://arxiv.org/html/2304.03442v2 ・HTML実読済みだが引用位置の確認を推奨)。

---

## 参照一覧

| 文献 | URL | 確認状況 |
|---|---|---|
| Rubinstein A. (2007) *Instinctive and Cognitive Reasoning: A Study of Response Times*, Economic Journal 117(523):1243-1259 | https://arielrubinstein.tau.ac.il/papers/78.pdf | ✔ PDF全文抽出・実読(表1-5の数値取得) |
| Hoyer W.D. (1984) JCR 11(3):822-829 | https://doi.org/10.1086/209017 / https://academic.oup.com/jcr/article-abstract/11/3/822/1791921 | ✔ 書誌・抄録実読 / **秒数は空欄(未確認)** |
| Forssberg M. et al. (2019) Fire Technology 55(6):2491-2513, DOI 10.1007/s10694-019-00881-1 | https://lup.lub.lu.se/search/publication/2d4e39fa-71da-4ea4-a79d-9723c48333a5 | 空欄(本文未読・既存答申からの持ち越し) |
| Kendrick K.H. & Torreira F. (2015) *The Timing and Construction of Preference* | https://eprints.whiterose.ac.uk/id/eprint/116177/1/Kendrick_and_Torreira_2015_.pdf | 空欄(PDF抽出失敗・700ms は検索要約のみ) |
| Murre J.M.J. & Dros J. (2015) *Replication and Analysis of Ebbinghaus' Forgetting Curve*, PLOS ONE | https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0120644 | ✔ 実読(保持値表・当てはめ式・24hブースト) |
| ACT-R base-level decay d=0.5(Anderson & Schooler 1991 由来) | https://link.springer.com/article/10.1007/s42113-018-0015-3 / https://www.ai.rug.nl/~niels/publications/taatgenLebiereAnderson.pdf | △ 検索要約のみ(「0.5が既定値」)・**本文未読** |
| Park J.S. et al. (2023) *Generative Agents*, arXiv:2304.03442 | https://arxiv.org/html/2304.03442v2 | ✔ HTML実読(0.995・α=1・閾値150・1日2-3回) |
| Zhong W. et al. (2024) *MemoryBank*, AAAI 38:19724-19731 | https://ojs.aaai.org/index.php/AAAI/article/view/29946 | △ 書誌のみ・本文未読 |
| Lin K. et al. (2025) *Sleep-time Compute*, arXiv:2504.13171 | https://arxiv.org/abs/2504.13171 | △ 検索要約のみ(5x/13%/18%/2.5x は**一次未確認**) |
| Qwen Team (2025) *Qwen3 Technical Report*, arXiv:2505.09388 | https://arxiv.org/html/2505.09388v1 | ✔ HTML実読(停止句挿入の機構)/ Fig.2の具体数値は空欄 |
| *Exploring Efficiency Frontiers of Thinking Budget in Medical Reasoning*, arXiv:2508.12140 | https://arxiv.org/html/2508.12140v1 | ✔ HTML実読(0-1024の予算水準・256飽和・512逓減・Qwen3 6サイズ) |
| *Through the Valley: Long CoT for Small LMs*, arXiv:2506.07712 | https://arxiv.org/html/2506.07712 | ✔ HTML実読(≤3B・8k例で最大75%劣化) |
| *When Thinking Fails: Pitfalls of Reasoning for Instruction-Following*, arXiv:2505.11423 | https://arxiv.org/abs/2505.11423 | ✔ 抄録実読(15モデル・CoTが書式順守を下げる) |
| *When More Thinking Hurts*, arXiv:2604.10739 (2026-04-12) | https://arxiv.org/html/2604.10739v1 | ✔ HTML実読(R1-32B 12K=55.8%→16K=54.9%・最適1.0K-7.5K) |
| Muennighoff N. et al. (2025) *s1: Simple test-time scaling*, arXiv:2501.19393 | https://arxiv.org/abs/2501.19393 | ✔ 抄録実読(budget forcing・"Wait"・AIME24 50%→57%) |
| Chen L., Zaharia M., Zou J. (2023) *FrugalGPT*, arXiv:2305.05176 | https://arxiv.org/abs/2305.05176 | ✔ 抄録実読(最大98%コスト減 or 同コストで+4%) |
| Ong I. et al. (2024) *RouteLLM*, arXiv:2406.18665 | https://arxiv.org/abs/2406.18665 | ✔ 抄録実読(">2倍のコスト減")/ 「MT Bench 85%減・95%品質」は空欄 |
| Kotte V. (2026) *UCCI: Calibrated Uncertainty for Cost-Optimal LLM Cascade Routing*, arXiv:2605.18796 | https://arxiv.org/html/2605.18796 | ✔ HTML実読(θ*の定式・コスト2.08 vs 2.24・31%削減) |
| *Agents Thinking Fast and Slow: A Talker-Reasoner Architecture*, arXiv:2410.08328 | https://arxiv.org/abs/2410.08328 | ✔ 抄録実読 |
| He Z., Feng Y. (2026) *When to Think Deeply: Inhibitory Deliberation*, arXiv:2606.06745 | https://arxiv.org/pdf/2606.06745 | 空欄(内容未確認・取得要約が信頼できず) |
| cl-nagoya/ruri-v3-30m モデルカード | https://huggingface.co/cl-nagoya/ruri-v3-30m | ✔ 実読(37M・256次元・8192・JMTEB 74.51・Apache-2.0・プレフィックス) |
| Ruri: Japanese General Text Embeddings, arXiv:2409.07737 | https://arxiv.org/pdf/2409.07737 | △ 既存答申の出典・本ラウンド未読 |
| Anthropic 公式ドキュメント Extended thinking | https://platform.claude.com/docs/en/build-with-claude/extended-thinking | ✔ 実読(target vs hard ceiling・最小1024・max_tokens未満) |

**未確認一覧(記憶で埋めていない項目)**: Forssberg本体 / Hoyerの秒数 / Kendrick&Torreiraの700ms / arXiv:2606.06745の内容 / Qwen3 Fig.2の具体値 / Sleep-time computeの数値 / ACT-R論文本文 / MemoryBank本文 / Lyfe Agents / Ruri-v3-30mの実機スループット / T1思考>0時の艦隊時間(線形外挿=【推測】)。
