<!-- hdr:v1 | 等級: B−(第348 親の一次確認=末尾の表。主な数値の一部を原典で確かめた。残りは未確認) | 作成: 2026-11-21 | 範囲: 返事その 9(11-20)§5-7 R-156 言葉以外の伝え方 -->
# R-156 言葉以外の伝え方(LLM の住民に、文のトークン以外で情報を渡す方法の先例と検証のしかた・vLLM の prompt embeds と頭の使い回しの不具合の今の状態・人が体の状態と場の空気をどこまで意識し言葉にできるかのデータ)

- **分野**: 自然言語処理・機械学習 #27 / 計算機科学(並列・決定論) #28 / 認知科学 #12 / 人格心理学 #13 | **重要度**: 発注文に記載なし(親が付ける)。材料にする所は [返事その 9(11-20)](../design/prompt-2026-11-20-reply9.md) §5-7 の R-156 と、[壁打ちの記録](../reference/wallbounce-record-2026-11-02_05.md) 2-70 ②③④
- **一次確認**: B−(第348 親の一次確認=末尾の表。主な数値の一部を原典で確かめた。残りは未確認)。筆者がこの回に読んだ出典は 42 本(◎ 20・○ 19・△ 2・書誌だけ 1)。既存答申からの引用は R-141・R-141 の追補・R-153・R-149・R-126(番号と節で引き、読み直していない)。読めなかったものは §7。
- **索引**: [INDEX.md](INDEX.md)(索引の行の追加は親が行う) ・ **残務**: [research-backlog.md](research-backlog.md)

> **注(発注文の定め・必ず冒頭に書く)**
> - 内部の向きを傾ける形(persona vectors など)は、重みを変えないが、LLM の中身に手を入れる点で重みの加工に近い。**調べるのはよいが、使う前にユーザーの了承を取る(重みの加工と同じ扱い)**(返事その 9 §5-7 の注)。
> - Qwen3-8B 用の SAE の重みのファイル(`.pt`)は取らない・読まない(返事その 8 §1-9)。モデルカードや論文の頁を読むのはよい。本書では SAE の頁も重みも開いていない。

> 作成 2026-11-21・リサーチ役(Opus 5.5)。子サブは起動していない。作ったのは本書 1 本だけで、コード・台帳・設計書・INDEX は 1 バイトも変えていない。commit も git add もしていない。封印の層(holdout・test の層)には触れていない。発注文が開かないと定めた文書(IMPLEMENTED.md・build-report-C7*/C8*・G1 のバックテストの計画・パターン台帳)は開いていない。重み・データセットの取得はしていない。
> **取り方の注**: 頁は WebSearch と WebFetch で読んだ。WebFetch は頁を小さなモデルに通して答えを返すので、引用は写しの段を 1 つ経ている(短い逐語の断片だけを頼み、長い文は要約として扱った)。GitHub は robots.txt を先に読んだ(`/*/*/issues`・`/*/*/pull`・`/*/*/releases` は許され、`/*/*/compare`・`/*/tree/`・`/*/*/commits/`・`?q=` つきの検索は禁じられている)。禁じられた形(比較・コミットの一覧・検索)は開いていない。そのため「どの PR がどの版に入ったか」をタグの比較で確かめることはしていない(§3 の表の「入った版」はリリースノートの読めた範囲と合流の日からの【推測】を分けて書いた)。arXiv は `/abs` と `/html` だけを読んだ。雑誌の論文の要旨は公開の索引(Europe PMC の REST・OpenAlex)で読んだ。curl と gh は使っていない。作業の途中で Web の道具が利用の上限に 2 回当たり、そのたびに止まって、親の再開の合図の後に同じ道具で続けた(§7 の U1)。
> 等級: ◎=原典か公式の文書・課題票の本文を読んだ/○=要旨だけ(索引の要旨を含む)/△=検索の抜粋だけ。筆者の組み立ては【見立て】、根拠のない置き方は【推測】と書く。**推薦は書かない**。決めるのはユーザー。
> 既存答申との関係(重ねない): persona vectors・CAA・RepE・価と覚醒の部分空間・Role Steering・activation capping・vLLM の 0.28.0 時点の機能の表・操舵の道具(hotwire-vllm・vllm-lens・EasySteer)は [R-141](v2-r141-persistent-state-vectors-and-steering.md) §2〜§5(**B**)、persona vectors の取り出しの手順と Qwen3-8B の監査(層 20・係数 0〜2.5)と Qwen3-8B 用の SAE の一覧は [R-141 の追補](v2-r141-addendum-sae-and-persona-vectors.md) §2・§3(**B**)、User-LLM と NPA と注意の門の候補 D は [R-153](v2-r153-attention-gate-and-person-information-relevance.md) §2・§6(**B**)、人物の持ち方の小・中・大は [R-154](v2-r154-persona-forms-and-primary-check.md) §4、言い回しへの敏感さ・数と時刻の偏り・出力の形の縛りの副作用は [R-149](v2-r149-llm-judge-model-biases-and-remedies.md) §2・§3(**B**)を正とする。本書は値を再掲せず番号で引き、足りない分だけを足す。

## §0 要旨

1. #56655(文と埋め込みを混ぜた入力で、頭の使い回しの鍵に印が入らず誤った出力を返す)は、2026-11-21 の時点で開いたままである。直す PR #56656 も開いたままで承認は 0、0.34.0(11-16)までのどの版にも入っていない。課題票に書かれた回避は「頭の使い回しを切る」だけ。関わる直し 3 本(#51899・#57006・#54509)は合流したが、印の欠けは直していない(§3-2)。
2. prompt embeds と罰則(repetition など)の #57719 も開いたまま(0.27.1 と 0.30 で再現)。直す PR #57762 は審査待ち。値によっては落ちずに誤った罰則を黙って掛ける。LoRA との #51122 は Llama 系だけで、Qwen3 は当たらないと報告者が書く(§3-2)。
3. 活性の操舵は vLLM 本体に無いまま。プラグインで差すと、0.33.0 と 0.34 系では前もって作ったコンパイルの写しが読まれ、操舵が黙って効かないことがある(Qwen3-0.6B で再現・vLLM #67566 は開いたまま・hotwire-vllm は 0.1.5 で回避)。0.34.0 で旧の実行器(V1)が消えた(§3-3)。
4. (a) 埋め込みの入力: PPlug の 1.4〜35.8% は、LaMP の 6 課題で最良の比べ相手(RSPG-Post)に対する相対の伸び(主は FlanT5-XXL 11B・Llama 2 7B も試した・Qwen は無い)。数の値を埋め込みにする 2601.09706 は、GPT-2 の形を一から学ばせた模型だけで試した(§2-1)。
5. (b) 内部の向き: Qwen3-8B の先例はある(R-141)。Llama 3.1 8B では、性格は操舵がプロンプトと同じか上(90.8 対 87.9)だが、人物の型(67.1 対 88.7)と有名人(51.4 対 89.1)は大きく下で、一貫性は 49.3 対 約 88 に落ちた。Qwen3-4B では、文で起こした感情は極端で加減が難しく、操舵は人らしいが当てになりにくく、考えることが押した感情を正当化しうる(§2-2)。
6. (c) 出口の制御: 気分や興奮で温度などの引き方を変えた先例は、検索の範囲では見つからなかった。vLLM の温度・top-p・logit の偏り・seed は要求ごとに変えられる(§2-3・§3-4)。
7. 検証のしかた: 3 つの型のどの先例も、課題の指標・判定役の LLM・人による出力の採点・人の研究の向きとの比べまでで、人の行動のデータの分布と比べたものは読めた範囲に無かった(§2-5)。
8. 人の自己報告は体の実際の値と弱くしか結びつかない。心拍の数え r=.16(572 人)・空腹の評定と食事の量 r≤0.26(549 人)・眠気の評定は 6 時間と 4 時間の睡眠を見分けなかった(48 人)。感情を言葉にしにくい人は約 1 割(フィンランド 5,454 人で 9.9%)。気分や体の感覚が意識にのぼるのは約 4 分の 1 の瞬間(大学生 30 人)。店の音楽は客が気づかないままワインの選択を変えた(§4)。
9. 記録 2-70 の文献 8 本は、合う 6・一部 2(確かめられないものは 0)。記録が原典より強い所は、「NeurIPS 2026」が本会議でなくワークショップ、2601.09706 が GPT-2 の形を一から学ばせた模型だけ、Dunn 2010 の結びつきが覚醒だけで快不快には無い(記録はこの限定を落とした)、の 3 点(§5)。
10. 親に確かめてほしい数値は §8 の末尾。

## §1 問いと前提

### 1-1 問い(返事その 9 §5-7・発注文)

1. 問い 1: 言葉以外の伝え方の 3 つの型 (a) 埋め込みの入力 (b) 内部の向き (c) 出口の制御の先例と、検証のしかた。§2。
2. 問い 2: R-141 が書いた「prompt embeds と vLLM の頭の使い回し(prefix caching)を一緒に使うと誤る不具合」の、版ごとの今の状態。§3。
3. 問い 3: 人が自分の体の状態や場の空気を、どこまで意識し言葉にできるかのデータ(記録 2-70 ④ の境目の材料)。§4。
4. 記録 2-70 の文献の列の一次確認(記録の文と原典が合うか)。§5。
5. 範囲の外: 判断モデルの設計・画像や音の入力・ファインチューニングのやり方そのもの・どの型を採るかの推薦。

### 1-2 前提

| 前提 | 中身 | 場所 |
|---|---|---|
| 住民の LLM | 8B 級の公開モデル(Qwen3-8B の 4 ビットが基準。候補に Gemma 4 E4B・Ministral 3 8B)を vLLM で動かす。数千〜数十万の住民を 1 つのモデルで回す | 発注文の背景 |
| 頭の使い回しと決定論 | vLLM の automatic prefix caching と、同じ入力なら同じ答え(バッチ不変 `VLLM_BATCH_INVARIANT=1`・B14 の 32/32) | R-123・R-141 §5-1 |
| 3 つの型の登録 | A 外で効かせる(範囲の外)/B 言葉でなく入れる(埋め込みの入力・内部の向き)/C 出口で効かせる | 記録 2-70 ② |
| 境目の候補 | 「LLM に言葉で渡すのは、人がその場で言葉にできる程度に意識しているものだけ」は検証する候補(境目を人のデータで測るのは難しい) | 記録 2-70 ④ |
| 原則 | 人の判断と心の働きを、構築者が手で決めた式で決めない(LLM・人のデータから学んだ部分・人のデータで較正した部分のどれか) | 記録 2-71 |
| 今の vLLM の版の並び | 0.28.0(2026-08-26)〜0.32.0(10-18)は R-141 §5-1。本書で 0.33.0(タグ `v0.33.0rc3`・11-02)と 0.34.0(11-16・Latest)を足した | R-141 [S50]・本書 [V1] |

## §2 問い 1 先例と検証のしかた

列の意味: 「重み」=本体の LLM の重みを変えるか・別の小さな部品を学ばせるか。「検証」=人のデータと比べたか・課題の正答率や判定役の点だけか。「vLLM」=推論のサーバーでそのまま使えるか(11-21 の状態は §3)。「既存」は既存答申の等級のまま引いたもの(読み直していない)。

### 2-1 (a) 埋め込みの入力(ソフトプロンプト・本人の埋め込み・連続の値を直接入れる)

| 研究(著者・年・場) | 何を伝えたか | 模型の大きさ(8B 級か) | 重み | 効き(数値・比べた相手・場所) | 検証 | 副作用 | vLLM | 等級と読んだ版 |
|---|---|---|---|---|---|---|---|---|
| PPlug(Liu ら・ACL 2025)[A1] | 利用者の履歴の全件を凍った符号器(BGE-base)で埋め込み、入力に合わせた softmax の重みで 1 本にまとめた「本人の埋め込み」+学ばせた指示の埋め込みを入力の前に置く | 主は FlanT5-XXL(11B)。§4.5 で FlanT5-XL(3B)と Llama 2 7B Chat も。Qwen は無い | LLM と履歴の符号器は凍結。入力の符号器・射影(2 層の MLP)・指示の埋め込みを学ばせる | 最良の比べ相手 RSPG-Post に対し相対で 1.4〜35.8%(§4.4・表 1。LaMP の 6 課題)。例: LaMP-2 の正答率 0.430 → 0.559。大きさの順に効く(11B > 7B > 3B)。検索と組み合わせると LaMP-2 を除いて伸びた(表 3) | LaMP の課題の指標(正答率・MAE・ROUGE)だけ。人のデータとの比べは無い | 読めた範囲に記述なし(空欄) | 1 本の埋め込みは prompt embeds で差せる形(R-141 §5-1)。ただし #56655 が開いたまま(§3) | ◎ arXiv の HTML v2(2026-06-03) |
| User-LLM(Ning ら・Google 2024) | 行動の列(50 件)を自己教師で学んだ符号器で埋め込み、交差注意か soft prompt で入れる | R-153 §2-3 にある | 符号器+差し込みの層(既定は LLM も学ぶ。凍らせても近い) | 文で渡すより最大 +16.33%、同じ表に −8.77% の課題もある(表 2) | 推薦・評価の課題の指標だけ | — | vLLM 本体に交差注意の口が無い(R-153 §6 の D) | 既存 ◎(R-153 [S2]・親確認) |
| PERSOMA(2024) | 対話の履歴をソフトプロンプトの埋め込みに圧縮 | R-141 §2-2 にある | 同左 | 抄録に数値なし | — | — | prompt embeds の形 | 既存 ○(R-141 [S45]) |
| 値を知る数の表し方(Dutulescu ら・arXiv 2601.09706)[P2] | 数の**値**から作った前置きのトークンの埋め込み(`<num>` の埋め込み=f(x)。MLP 版と GRU 版) | GPT-2 の形を**一から学ばせた**(大きさの記載なし)。学習済みの LLM は試していない | 模型全体を学ばせる | 数の課題(NUPA・38 課題)の完全一致で 0.687 → 0.720/0.724(表 1)。7 桁で 0.613 → 0.638/0.642(表 2) | 数の課題の正答率だけ | 掛け算は NumeroLogic(0.545)に負け(0.340/0.367)、剰余は少し悪化(0.076 → 0.059/0.051)(表 6)。学習の費用は 2 倍(前向きを 2 回) | 専用の模型の形なので、そのままでは使えない【見立て】 | ◎ arXiv の HTML v1 |
| xVal(Golkar ら・NeurIPS 2023 のワークショップ ML4PS)[X1] | 数を連続の値として 1 つのトークンで表す | 一から学ばせた特別な模型(大きさは要旨に無い) | 模型全体を学ばせる | 要旨は「generally outperforms other common numerical tokenization strategies」(分布の外への汎化と計算の効率) | 科学のデータの課題の指標 | 要旨に無い | そのままでは使えない【見立て】 | ○ arXiv の要旨 v2 |

### 2-2 (b) 内部の向き(活性の加算・persona vectors・感情の向き・表現の操作)

| 研究(著者・年・場) | 何を伝えたか | 模型の大きさ(8B 級か) | 重み | 効き(数値・比べた相手・場所) | 検証 | 副作用 | vLLM | 等級と読んだ版 |
|---|---|---|---|---|---|---|---|---|
| persona vectors(Chen ら 2025) | 特性(悪・追従・作り話ほか) | Qwen2.5-7B・Llama-3.1-8B | 重みは変えない。向きは対の答えの残差の平均の差 | R-141 追補 §3-1 にある(層 20/16・一貫性 75 以上を保つ) | 判定役の LLM の点+著者 2 人の人の判定 284/300(94.7%)。人の行動のデータとの比べは無い | 係数を大きくすると MMLU が落ちる(R-141 §2-1) | 本体に無い(§3-3) | 既存 ◎(R-141 追補 [S7]) |
| Qwen3-8B の persona vectors の監査(Zeng・Emami・Choi 2026) | 53 特性 | **Qwen3-8B**・gpt-oss-20b | 同上 | 一般の領域で 19 特性中 16 が操舵できた。層は 20 が最多(R-141 追補 §3-2) | 手元の判定役(gpt-oss-20b)の点だけ。特異性の対照なし(著者) | — | 同上 | 既存 ◎(R-141 追補 [S9]) |
| 価と覚醒の部分空間(arXiv 2604.03147) | 感情(価と覚醒の 2 軸) | Llama-3.1-8B・**Qwen3-8B**・Qwen3-14B | 同上 | Qwen3-8B の拒否率 α=−3.0 で 97.0%・0 で 89.5%・+3.0 で 67.0%。Qwen3 は Llama の約 7 倍の係数が要る(R-141 §3-1) | 生成文の価と覚醒の判定器・拒否率・MATH-500・IFEval。人のデータとの比べは無い | Qwen3-8B は α=+3.0 で分布の外の出力 17.0% | 同上 | 既存 ◎(R-141 [S27]) |
| 何を操舵できるか(Bas & Novak・arXiv 2511.18284)[B3] | 50 の振る舞い(人物の型・性格・ずれた振る舞い・文体・有名人) | Llama 3.1 8B の 15 層。プロンプトの比べ相手は同じ 8B と GPT-4 系 | 同上(Chen らの対の差の平均・係数 1〜20) | 分類ごとの平均の特性の点で、操舵 対 プロンプト(同じ 8B): 性格 90.8 対 87.9・ずれた振る舞い 71.3 対 69.4・人物の型 67.1 対 88.7・有名人 51.4 対 89.1(§6.1・図 4) | 判定役 GPT-4.1 だけ(人の評価なし。著者は判定役の偏りを限界に挙げる) | 係数を上げると一貫性と関わりの点が単調に落ち、大きな係数で 0 に近づく。一貫性 49.3 対 プロンプト 約 88、関わり 44.0 対 78.6/82.4。特性の点は係数に対して逆 U 字。向きの分かれ具合は効きを当てない(r=−0.045) | 同上 | ◎ arXiv の HTML v2 |
| 説得のための感情の操舵(Senthilnathan ら・NeurIPS 2026 ワークショップ)[B1] | 感情(凍った模型の感情の部分空間。会話の番ごとにどの感情を入れるかを強化学習の方策が選ぶ) | 頁に記載なし | 重みは変えない。方策を学ばせる | 同じ感情の目標をプロンプトで渡すより「consistently outperforms」。数値は頁に無い | 模擬の寄付の会話(人を相手にしたかは頁に無い) | 頁に記載なし | — | ○ 頁の要旨 |
| Sparks of Rationality(Tak ら・arXiv 2601.22329)[B2] | 感情(怒り・恐れ・悲しみなど)。文で起こす形(ICP)と表現の操舵(RLS)を比べた | 主は **Qwen3-4B**(8B は時間割引の付録だけ) | RLS は重みを変えない低ランクのベクトルを隠れ状態に注入(強さ 35) | ICP は強く動くが「often extreme and difficult to calibrate」(恐れで賭けがほぼ 0・損失回避が測れない)。RLS は「more psychologically plausible patterns but with lower reliability」で、量に応じて段階的に動いた(図 4〜8) | 人の既存の研究(最後通牒・独裁者・枠づけ・道徳の判断など)の**向き**と比べた定性の比べ。人の数値との突き合わせは本文の読めた範囲に無い。効果量は図 11 にだけある | 両方とも合理性の公理を守る率が少し下がる(図 2)。考えることが押し込まれた感情を正当化しうる | — | ◎ arXiv の HTML v1 の前半 10 万字 |
| E-STEER(Sun ら・arXiv 2604.00005)[B5] | 感情(VAD の連続の空間を隠れ状態に) | 頁に記載なし | 重みは変えない | 要旨: 感情と振る舞いの関係は単調でなく、心理学の理論と合う。ある感情は能力と安全を上げた | 推論・生成・安全・多段のエージェントの課題。人のデータとの直接の比べは要旨に無い | 要旨に数値なし | — | ○ 要旨 v1 |
| Role Steering(arXiv 2608.00023) | 社会シミュの役(275 役) | OLMo-3-7B | 重みは変えない | R-141 §2-1 にある | — | — | — | 既存 ○(R-141 [S32]) |
| 感情で揺らす小さな模型の判断(arXiv 2604.06562) | 感情 | 複数の系統 | 重みは変えない | 戦略の選択は系統的に変わるが、行動は不安定で人の期待と合わないことが多い(R-141 §3-1) | ゲーム理論の型の課題 | — | — | 既存 ○(R-141 [S33]) |
| Big Five の操舵(arXiv 2512.17639) | 性格 | Llama 3.3 70B | 重みは変えない | 選択式の問いには効くが、自由な生成と文脈の多いプロンプトでは効きが弱い(R-141 §2-1) | — | — | — | 既存 ○(R-141 [S34]) |
| 数の値の線形の表し(Zhu・Dai・Sui・arXiv 2401.03735v4)[P3] | 数の値(隠れ状態から線形に読み出せる・ベクトルの足し算で出力を動かせる) | 要旨に模型の名なし | 重みは変えない | 要旨は「LLMs encode the value of numbers linearly」 | 足し算の合成データの課題 | — | — | ○ 要旨 v4 |
| 感情の概念(Anthropic 2026) | 感情 171 語の向き | Claude | — | 向きは主に「局所」(今の文が扱う感情)で、持続する気分ではない(R-126 §3-6) | — | — | — | 既存 ○(R-126) |

### 2-3 (c) 出口の制御(温度・top-p・logit の偏り・文法の縛りを状態で変える)

| 研究・資料 | 何を伝えたか | 模型の大きさ(8B 級か) | 重み | 効き(数値・比べた相手・場所) | 検証 | 副作用 | vLLM | 等級と読んだ版 |
|---|---|---|---|---|---|---|---|---|
| **気分や興奮で引き方(温度など)を変えた先例** | — | — | — | **見つからなかった**。検索の抜粋の範囲では、感情の状態(VAD・PAD)はプロンプトの文か活性の操舵で入れ、引き方の温度に結び付けた論文は出なかった。温度は頑健さの確かめに振るだけ(arXiv 2607.25140)、温度は出力の分布のエントロピーを変えるもので人のばらつきを写すとは言わない(arXiv 2604.27345)という書き方は抜粋に出た | — | — | — | △ 検索の抜粋(§6 の 1) |
| 温度を上げる(R-149 の範囲) | 出力の散らばり | Qwen3-8B ほか | 変えない | Qwen3-8B は温度 0〜10 でも数を一様に散らせない。温度を上げても意味の多様さは人に届かず、GPT-4 は 1.4 で文が崩れた。温度は新しさに弱く、まとまりの無さに中くらいに相関(Peeperkorn ら)(R-149 §0 の 2・§5) | 適合の検定・多様さの物差し | 文が崩れる | 要求ごとに変えられる(§3-4) | 既存(R-149・B) |
| 出力の形を縛る(文法・正規表現) | 出力の形 | — | 変えない | R-149 §3 にある(型が作り話をさせる度合い・下書きしてから縛る) | — | R-149 §3 | `structured_outputs` の中身は要求ごと・後ろの仕組みはエンジンで 1 つ(§3-4) | 既存(R-149・B) |
| 文で起こした感情と順の判断(Ho ら・arXiv 2607.12631)[C1](比べのため・入れ方は文) | 想像で起こした感情(文脈) | 要旨に記載なし | 変えない | アイオワ・ギャンブル課題で、起こした感情は平均では判断の動きを有意に偏らせなかった(人とは違う)。怒りだけは条件つきで、罰への感度を下げ、序盤の探索を減らした | 人の振る舞いとの対比(要旨は人のデータの出どころを書かない) | — | — | ○ 要旨 v1 |
| logit の偏り・許すトークンの一覧を要求ごとに | — | — | 変えない | vLLM の `logit_bias`(±100 に切り詰め)・`allowed_token_ids`・`bad_words` は要求ごと(§3-4) | — | — | 要求ごと | ◎ [V14] |

### 2-4 比べのため: 状態を言葉にしてプロンプトに入れる型

| 研究 | 何を伝えたか | 模型 | 効き | 検証 | 等級 |
|---|---|---|---|---|---|
| Sentipolis(Fu ら)[B4] | PAD の連続の状態を、人の話し声の注釈(264,705 点)の k 近傍で感情の札にし、LLM が 1 段落の文にして入れる | GPT-4o-mini・GPT-5.2・Grok・Qwen3-235B-A22B ほか(7B/8B は無い) | もっともらしさは大きな模型で +25〜85%、GPT-4o-mini で −7〜−26%(表 1)。社会の決まりへの従いは少し下がった | 判定役の LLM 3 つ(互いの Spearman 0.887〜0.905)+言語学の大学院生が一部を採点(人どうしの α 0.575〜0.871・人と LLM の α 0.825)。人の行動のデータとの比べは無い | ◎ HTML v2 の前半 |
| Humanoid Agents | 基本の欲求・感情・関係の近さを文で | — | R-141 §2-4 | — | 既存 ○ |

### 2-5 検証のしかたの型(読んだ先例の中で)【見立て】

| 検証の型 | 使った先例 | 人のデータとの距離 |
|---|---|---|
| 課題の指標(正答率・MAE・ROUGE など) | PPlug・User-LLM・値を知る数の表し方・xVal | 人の行動とは比べていない |
| 判定役の LLM の点(特性・一貫性・関わり) | persona vectors・Qwen3-8B の監査・Bas & Novak・Sentipolis | 判定役の偏りが入る(Bas & Novak の限界の節) |
| 人が出力を採点 | persona vectors(284/300)・Sentipolis(一部・言語学の大学院生) | 「人らしく見えるか」で、人の行動の分布とは別 |
| 人の既存の研究の向きと比べる | Tak ら(最後通牒・独裁者・枠づけ・道徳)・Ho ら(アイオワ・ギャンブル課題) | 向きは比べるが、人の数値との突き合わせは読めた範囲に無い |
| 人の行動のデータの分布と比べる | **読んだ先例の中には無かった**(空欄) | — |

- 【見立て】3 つの型のどれにも、「人の行動のデータの分布に近づいたか」で確かめた先例は、本書の読めた範囲では見つからなかった。記録 2-75 の段 1(人の実験と同じ形の課題で答えの分布を人と比べる)の形で確かめた先例は空欄である。

### 2-6 比較の表(推薦なし)

| 観点 | (a) 埋め込みの入力 | (b) 内部の向き | (c) 出口の制御 | 比べ: 言葉にして入れる(今の形) |
|---|---|---|---|---|
| 8B 級の先例 | Llama 2 7B(PPlug の §4.5)。Qwen3 は無い | Qwen3-8B の先例あり(感情の 2 軸・53 特性の監査) | 温度の効きは Qwen3-8B で測った値あり(R-149)。状態で引き方を変えた先例は無い | 多い |
| 何を学ばせるか | 符号器・射影(PPlug)。値の埋め込みは模型全体(2601.09706) | 向きを作る(学習は無い)。方策を学ぶ形もある(説得の研究) | 無し | 無し |
| 状態の更新の費用 | 符号器の前向き計算 | 係数を足し引きするだけ(R-141 §7) | 欄の値を変えるだけ | 文を組み直す |
| 人のデータとの比べの先例 | 無し(課題の指標) | 向きの定性の比べ(Tak ら)・人の採点(persona vectors) | 無し | 判定役と人の採点(Sentipolis) |
| 主な副作用の報告 | 掛け算などで悪化(2601.09706)・記述なし(PPlug) | 一貫性と関わりの低下(Bas & Novak)・分布の外 17%(Qwen3-8B)・押した感情の正当化(Tak ら)・有名人と人物の型ではプロンプトより弱い | 温度で文が崩れる(R-149) | 言い回しへの敏感さ(Sclar ら)・数の写し(R-149) |
| vLLM(11-21) | prompt embeds は本体にある。#56655(頭の使い回しで誤る)と #57719(罰則で落ちる)が開いたまま | 本体に無い。プラグインは AOT のコンパイルの写しで黙って効かないことがある(#67566 開) | 要求ごとに変えられる。乱数は `seed` を付けないとバッチ不変でないことがある | そのまま |
| 頭の使い回し | 埋め込みの位置の鍵の不具合(#56655) | 道具しだい(R-141 §5-2) | 触らない(引き方は答えを書く段)【見立て】 | 共通部分を先に置けば使い回せる |
| ユーザーの了承 | — | **使う前に了承を取る(重みの加工と同じ扱い・返事その 9 §5-7 の注)** | — | — |

## §3 問い 2 prompt embeds と頭の使い回しの不具合の今の状態(確かめた日 2026-11-21)

### 3-1 R-141 が書いたこと

R-141 §0 の 9・§5-1 の表・§7 の表は、vLLM の prompt embeds について次の 3 件を「開いている」と書いた(読んだ日 2026-11-04)。親は第344 で #56655 が開いていることを GitHub の API で確かめた(R-141 末尾の表)。

- #56655(2026-09-13・main で再現): 文と埋め込みを混ぜたときの印が、頭の使い回しの鍵に入らず、前の要求の KV を使って誤った出力を返す。
- #57719(0.27.1): prompt embeds と罰則(repetition・presence・frequency)を一緒に使うとエンジンが落ちる。
- #51122(0.11.0・Llama): prompt embeds と LoRA を並行で使うと落ちる。

### 3-2 版ごとの今の状態の表

| 不具合 | 報告された版と日 | 中身(課題票の本文) | 直す PR と状態 | 入った版 | 回避のしかた | 出典・等級 |
|---|---|---|---|---|---|---|
| **#56655** 文と埋め込みを混ぜたときの印(`prompt_is_token_ids`)が頭の使い回しの鍵に入らない | 2026-09-13。版の番号は無く、main の `a2bc2ff…` で再現(関数は `e52be1a…` でも同じ)。再現のモデルは `Qwen/Qwen3-0.6B`・RTX 3090・FP16 | 「The prefix-cache key hashes the normalized token IDs and supplied tensor, but omits that selection mask.」埋め込みの位置はトークン ID 0 に直されるが、0 は本物の語彙の ID でもあるので、中身の違う 2 つの入力が同じ鍵になる。要求 A の後に B を送ると、B は 32 トークンを使い回して `[753] * 16` を返した(B だけなら `[9, 0] * 8`) | **#56656**「[Bugfix] Include mixed prompt embedding masks in prefix cache keys」(2026-09-13 に開く)は**開いたまま・承認 0**。11-13 に作者が `ae96937c5` の上に載せ直して試験が通ったと書いた。コードの持ち主 10 人の審査待ち | **どの版にも入っていない**(0.34.0 のリリースノートの読めた範囲に prompt embeds の行が無い) | 課題票の本文:「Temporarily disabling prefix caching avoids this erroneous reuse.」(頭の使い回しを切る) | [V2][V3] ◎ |
| 関わる直し: 頭の使い回しの鍵の部品に出どころの札を付ける | 課題 #44701 | 鍵の部品(LoRA の名・`cache_salt`・画像などの識別子・prompt embeds の要約)が札の無い 1 つの組に混ざっていて、LoRA `foo` の要求と `cache_salt="foo"` の要求が同じ鍵になりえた。札を付けて分けた(prompt embeds の要約は `("prompt_embeds", digest)` に) | **#51899**「[Core][BugFix] Tag prefix-cache extra keys by source」**合流 2026-09-30**。安全の勧告 GHSA-rh6f-3x46-j33q に結び付く | 0.31.0 の拾い上げ(cherry pick)の里程標に 10-01 に入った(頁の記述)。**#56655 の印の欠けは直していない**(#56655 の本文と #51899 の頁の両方がそう書く) | — | [V4] ◎ |
| 関わる直し: 印の長さが合わない入力を受付で断る | — | 印の長さが埋め込みの行の数と違うと、以前は `InputBatch.add_request()` の中で落ち、次の要求が `EngineDeadError` になった | **#57006**「[Bugfix][Frontend] Validate mixed prompt embedding mask lengths」**合流 2026-09-22**。確かめは A10・Qwen3.5-0.8B・旧と新の実行器で、**頭の使い回しは切って**行った | 合流の日からは 0.31.0 以降【推測】(リリースノートで確かめていない) | — | [V5] ◎ |
| 関わる直し: 切り詰めのときに印も切る | — | `truncate_prompt_tokens` を使うと印だけが元の長さのまま残り、落ちるか、左を切ると埋め込みの位置が黙ってずれた | **#54509**「[Bugfix][Frontend] Truncate prompt_is_token_ids with the prompt」**合流 2026-08-31** | 合流の日からは 0.29.0 以降【推測】(確かめていない) | — | [V6] ◎ |
| **#57719** prompt embeds と罰則でエンジンが落ちる | 0.27.1(2026-09-19)。作者は 0.30 でも再現(09-28)。モデルは `Qwen/Qwen3-0.6B`・bf16 | prompt embeds の要求ではプロンプトの位置のトークン ID の欄が書かれず、罰則の計算が前の要求の残りの値を本物の ID として数える。値が語彙の外ならエンジンが落ち、内なら**落ちずに誤った罰則を黙って掛ける**(どちらになるかはメモリの割り当てしだい)。条件は「長さの違う 2 つのプロンプト・埋め込みの要求が一番長い」 | **#57762**「[Bugfix][MRV1] Fix penalties with prompt embeddings」**開いたまま・承認 0・載せ直し待ち(11-07)**。別の人が再現と直りを確かめたが、正式の承認ではない | **どの版にも入っていない** | 公式の回避は無い。課題票の切り分けから読める回避は、罰則を prompt embeds と一緒に使わない【見立て】 | [V7][V8] ◎ |
| **#51122** prompt embeds と LoRA を並行で使うと落ちる | 0.11.0(2026-08-05)・Llama 系 | 埋め込みの道がバッチの一部だけを埋め込み、LoRA の目録はバッチ全体の長さで作られる。**Qwen3 は `embedding_modules` を宣言しないので害は無い**と報告者が書く | #51123 は開いたまま。課題票は 11-04 に「古い」の札が付き、30 日動きが無ければ自動で閉じる | 入っていない | `embed_tokens` と `lm_head` を LoRA の対象から外す(報告者) | [V9] ◎ |
| 関わる変化: 0.34.0 で旧の実行器(Model Runner V1)が消えた | 0.34.0(2026-11-16) | 「Model Runner V1 removed; MRV2 is the sole GPU runner」。ブロックの大きさの既定が 64 に。V1 の logits の処理器の API も落とした(#63373) | — | 0.34.0 | — | [V1] ◎ |

### 3-3 活性に手を入れる差し込みの不具合

| 不具合 | 報告された版と日 | 中身 | 直す PR と状態 | 回避のしかた | 出典・等級 |
|---|---|---|---|---|---|
| 一般のプラグイン(`vllm.general_plugins`)が差し込んだ処理が、前もって作ったコンパイルの写し(AOT)に入らない | 0.33.0 と 0.34.0rc1.dev441 で再現(Qwen3-0.6B・H200)。2026-11-13 | AOT のコンパイルのキャッシュの鍵が、プラグインが新しく通すファイルを数えない。プラグイン無しで温めたキャッシュがあると、それが読み込まれ「The plugin's change is silently missing from the model.」hotwire-vllm の試験で「steering changes output」と「mixed batch isolated」が失敗し、操舵なしの出力は変わらなかった。AOT は torch 2.10 から既定 | **vLLM #67566**「[Bugfix][Compile] Key the AOT compile cache on loaded general plugins」(11-13 に開く)は**開いたまま・承認 0** | hotwire-vllm 側は **PR #1**「Salt the compile cache key on vLLM 0.34 too」を 11-14 に合流し 0.1.5 として出した(鍵に塩を足す)。vLLM 側の PR の本文には回避の記述が無い | [V10][V11] ◎ |
| 観測の口の RFC と実装 | — | RFC #36998 は開いたまま。11-29 ごろに自動で閉じる見込みだったが、11-12〜13 の書き込みで延びた。PR #37002 は開いたまま・「古い」の札(10-29)。審査役の言葉は「too invasive without enough justification to consider landing upstream」(04-26) | 本体に操舵は入っていない(R-141 §5-1 と同じ) | — | [V12][V13] ◎ |

- 【見立て】本体の操舵の口は 11-21 の時点でも無い。プラグインで差すと、コンパイルの写しの古さで**操舵が黙って効かない**ことがある(0.33.0・0.34 系)。この型の失敗は、出力が操舵なしと同じになるだけで、落ちもしない。操舵の腕を試すなら「操舵で出力が変わったか」を毎回確かめる試験が要る【見立て】。

### 3-4 出口の制御(型 (c))が vLLM でどこまで要求ごとに変えられるか

`SamplingParams` の公式の API の頁(latest)を読んだ [V14] ◎。

| 欄 | 要求ごとか | 注 |
|---|---|---|
| `temperature`・`top_p`・`top_k`・`min_p` | 要求ごと | 温度は [0, 2]。0 は貪欲 |
| `seed` | 要求ごと | バッチ不変を入れているとき「Random sampling without an explicit seed may not be batch invariant. Set seed in SamplingParams or use temperature=0.」と警告する |
| `logit_bias`・`allowed_token_ids`・`bad_words` | 要求ごと | logit_bias は ±100 に切り詰め |
| `repetition_penalty`・`presence_penalty`・`frequency_penalty` | 要求ごと | prompt embeds と一緒に使うと #57719 に当たる |
| `structured_outputs` | 中身は要求ごと | 「Request-level structured output backend selection is not supported.」(後ろの仕組みはエンジンで 1 つ) |
| 任意の logits の処理器 | `SamplingParams` に欄は無い。`extra_args` を通す | 0.34.0 で V1 の logits の処理器の API が落ち、`vllm.v1.worker.gpu.sample.logits_processor` だけになった [V1] |

- 【見立て】温度・top-p・logit_bias は要求ごとに変えられ、入力の頭の使い回しにも触らない(使い回すのは入力を読む段の KV だけで、引き方は答えを書く段の話)。バッチ不変との関係は、`seed` を要求ごとに付けるかどうかで決まる [V14]。

## §4 問い 3 人が体の状態と場の空気をどこまで意識し言葉にできるか

列の「材料になる所」は、記録 2-70 ④ の 3 つの置き方(言葉で渡す/言葉でなく渡す/渡さない)のどれを考えるときの材料になるかだけを書いた。どれがよいかは書かない。原典の本文はどれも読めておらず、要旨(○)まで。人数や値が要旨に無いものは空欄にした。

### 4-1 内受容(空腹・疲れ・心拍・暑さ寒さ)に気づき、言葉で報告できる程度

| 研究 | 対象と人数 | 測ったもの | 主な数値(要旨) | 等級と読んだ版 | 材料になる所 |
|---|---|---|---|---|---|
| Garfinkel ら 2015 [H2] | 一般の標本 N=80 | 内受容の 3 つの次元: 正確さ(心拍を当てる課題の成績)・自分で感じていると思う度合い(質問紙)・気づき(自信が正確さを追う度合い=メタ認知) | 「all three dimensions were distinct and dissociable」。正確さは、気づきと自分の評定からは「only partly」しか予測できない。3 つが対応したのは、正確さが最も高い下位の群の中だけ | 索引の要旨 ○(Europe PMC。雑誌の版の要旨) | 言葉で渡す場合: 本人が「感じている」と言う程度と、体の実際の値は別の量になる。言葉でなく渡す場合: 体の値が本人の言葉を経ずに効く道を分けて持つ根拠の 1 つ |
| Zamariola ら 2018 [H3] | N=572 | 心拍を数える課題(手がかりなしで自分の心拍を数える)の数えた数と実際の数 | 実際の心拍と数えた心拍の相関は全体で r=.16。誤りの 95% 超が少なく数える側。正確さの上位 60% の中では力の差が見分けられない。点数は心拍数そのものに縛られる | 索引の要旨 ○ | 体の量の「正確な数」を本人が持っているかの床。数(0〜10)をそのまま見せる形と、感じの言葉に直す形の比べの材料(記録 2-70 ① の「体の状態の数を感じの言葉に直すか、見せずに外で効かせる」) |
| Dunn ら 2010 [H1] | 2 つの研究(人数は要旨に無い) | 研究 1: 感情の写真への心拍の反応と、主観の覚醒・快不快の評定の結びつき。研究 2: 直感の選択 | 心拍を正確に追える人ほど、心拍の反応と覚醒の評定が強く結びついた(快不快では結びつかない)。内受容の力は、体の先回りの信号の向きによって、直感の選択を助けもし妨げもした | 索引の要旨 ○ | 言葉で渡す場合: 覚醒を本人の言葉にどこまで載せるかは人によって違う(個人差の材料)。言葉でなく渡す場合: 体の信号が意識の言葉を経ずに選択を動かす例 |
| Van Dongen ら 2003 [H4] | 健康な成人 n=48(21〜38 歳)。床の時間 4・6・8 時間を 14 日、または 0 時間を 3 晩 | 認知の成績と、眠気の自己評定 | 4・6 時間の 2 週間で、成績は量に応じて積み上がって落ちた(6 時間以下は徹夜 2 晩ぶんまで)。眠気の評定は最初に上がった後は少ししか上がらず、6 時間と 4 時間を見分けなかった。「Sleepiness ratings suggest that subjects were largely unaware of these increasing cognitive deficits」 | 索引の要旨 ○(正誤表が Sleep 2004;27(4):600 にある。正誤表は読んでいない) | 疲れについて「本人が言葉にできる感じ」と「体と能力の実際」が日をまたいで離れていく例。言葉で渡す量と、言葉でなく(または渡さずに)世界の側で効かせる量を分ける材料 |
| Sadoul ら 2014 [H5] | 23 の無作為化試験・549 人を合わせた | 空腹などの視覚アナログ尺度(100 mm)と、その後の自由な食事の量 | 相関は有意だが小さく、最大 r=0.26。空腹・年齢・性別・体重・基礎代謝の模型で食事量のばらつきの 25%、空腹を抜くと 19%。食事量の差に確かに結びつく評定の差は 100 mm のうち 15〜25 mm 以上 | 索引の要旨 ○ | 空腹の言葉の評定は、行動(食べる量)を弱くしか予測しない。言葉で渡す空腹の段の粗さ(何段に分けるか)を考える材料 |
| 暑さ寒さの申告と物理の模型(Cheung ら 2019・ASHRAE の熱の快適さのデータベース II) [H14] | — | — | **空欄**(OpenAlex に要旨が無い。著者稿は大学の保管庫 eScholarship にあると索引が示すが、読んでいない) | 書誌だけ | — |

### 4-2 自分の気分や興奮を言葉にできる程度(一般の集団での値)

| 研究 | 対象と人数 | 測ったもの | 主な数値(要旨) | 等級と読んだ版 | 材料になる所 |
|---|---|---|---|---|---|
| Mattila ら 2006 [H6] | フィンランドの Health 2000 調査(元の標本 8,028 人)のうち TAS-20 に答えた 5,454 人・30〜97 歳 | アレキシサイミア(感情を見分け言葉にするのが苦手な傾向)・TAS-20 | 有病率 9.9%(男 11.9%・女 8.1%)。年齢が上がるほど多い。切り分けの点数は要旨に無い(61 以上が通例だが本書では確かめていない) | 索引の要旨 ○ | 言葉で渡す場合: 住民の 1 割ほどは、気分を言葉にするのが苦手な人として居うる(割合の床)。日本の集団の値は読んでいない(§6) |
| Mauss ら 2005 [H7] | 人数は要旨に無い(思春期と成人・男女) | 映画で起こした楽しさと悲しさの間の、主観の体験・顔の表出・末梢の生理(心拍・皮膚の電気反応)を 1 秒ごとに | 体験と顔の表出は強く結びついた。「physiological responses were only modestly associated with experience and behavior」。楽しさが強いほど表出と生理の結びつきが強い(悲しさでは無い) | 索引の要旨 ○ | 本人の言う気分と体の反応の結びつきは中くらい以下。言葉で渡す気分と、体の量として持つ興奮を別の量にする材料 |
| Heavey & Hurlburt 2008 [H8] | 層化した大学生 30 人 × 無作為の瞬間 10 回=300 の瞬間(記述的経験抽出法) | その瞬間の内的な体験の型(内なる声・内なる像・記号のない考え・気分・感覚への気づき) | 5 つの型は「each … occurred in approximately one quarter of sampled moments」。頻度は人によって大きく違い、性差は無い。内なる声が多い人ほど心理的な苦痛が少ない | 索引の要旨 ○ | ある瞬間に気分や体の感覚が意識にのぼっているのは約 4 分の 1 の瞬間(型ごとの細かい割合は要旨に無い)。呼ぶたびに気分の行を言葉で見せるかどうかの材料 |
| 感情の粒度(Barrett らの系統) | — | — | **調べていない**(一般の集団の分布の値を読めていない) | — | — |

### 4-3 場の空気(混み具合・騒がしさ・周りの様子)を意識せずに受け取って行動が変わる証拠と、後で言葉にできるか

| 研究 | 対象と人数 | 測ったもの | 主な数値(要旨) | 等級と読んだ版 | 材料になる所 |
|---|---|---|---|---|---|
| North, Hargreaves & McKendrick 1999 [H9] | スーパーの客(人数は要旨に無い)。2 週間、フランスとドイツの音楽を 1 日おきに | フランスとドイツのワインの売れ方と、客への問い | フランスの音楽の日はフランスのワインが多く売れ、ドイツの音楽の日は逆になった。問いへの答えは「customers were unaware of these effects of music on their product choices」 | 索引の要旨 ○(OpenAlex。本数・割合は要旨に無い) | 場の空気が意識されないまま選択を変え、後で本人が理由に挙げない例。言葉でなく渡す/渡さずに世界の側で効かせる、の材料 |
| Mathews & Canon 1975 [H10] | 実験室と路上の 2 つの実験で計 132 人 | 85 dB の白色雑音と、より静かな条件での、困っている人への手助け | 85 dB の雑音の下では手助けが少なかった。著者は、雑音による覚醒が注意の向け先を狭めると説明(気分と動因の説明も検討)。手助けの率は要旨に無い。本人が雑音を理由に挙げたかは要旨に無い | 索引の要旨 ○(OCR の崩れあり。「8S-db.」を 85 dB と読んだのは【見立て】) | 騒がしさが行動を変える例。意識されていたかは分からない(空欄) |
| Milliman 1982 [H11] | スーパーの客(要旨に数値なし) | 店の中の音楽のテンポ | 「music tempo variations can significantly affect the pace of in-store traffic flow and dollar sales volume」。客が音楽に気づいていたかは要旨に無い | 索引の要旨 ○ | 場の空気が歩く速さと買う量を変える例(気づきは空欄) |
| Keizer ら 2008(落書きと捨てる率) | — | — | 記録 2-72 にある値を引くだけ(本書では読み直していない) | 記録 2-72 | 周りの様子が規範の行動を変える例 |

### 4-4 自分の行動の理由を人がどこまで正しく言えるか

| 研究 | 対象と人数 | 測ったもの | 主な数値(要旨) | 等級と読んだ版 | 材料になる所 |
|---|---|---|---|---|---|
| Nisbett & Wilson 1977 [H12] | 総説(既存の実験を集めた) | 高い次の心の働きについての言葉の報告 | 「little or no direct introspective access to higher order cognitive processes」。報告は「a priori, implicit causal theories」に基づく。「Accurate reports will occur when influential stimuli are salient and are plausible causes of the responses they produce」 | 索引の要旨 ○(OpenAlex。被引用 13,501) | 住民の LLM に「理由」を書かせるとき、その文は人の報告と同じく「もっともらしい理由」になりうる。目立ち・もっともらしい刺激なら当たり、目立たない刺激なら外れる、という人の側の型と比べる材料 |
| Johansson ら 2005 [H13] | 人数は要旨に無い | 顔の対から魅力で選ばせ、こっそり選ばなかった方を見せる | 参加者は目立つ食い違いに気づかず、選ばなかった顔について「introspectively derived reasons」を述べた(選択盲)。気づいた割合は要旨に無い | 索引の要旨 ○ | 行動の理由の報告が、実際の選択と切り離されて作られうる例。言葉の理由の文を正解の札に使うかの材料 |
| その後の見直し(White 1980・Wilson & Stone 1985・Newell & Shanks 2014 など) | — | — | **調べていない** | — | — |

**ここから言えること【見立て】**

- 体の量について、人の自己報告は体の実際の値に弱くしか結びつかない(心拍の数え r=.16・空腹の評定と食事量 r≤0.26・眠気の評定は 6 時間と 4 時間を見分けない)。どれも「人がその場で言葉にできる量」と「体の実際の量」が別のものであることを示す。
- 気分の言葉と体の反応の結びつきは中くらい以下で(Mauss 2005)、言葉にするのが苦手な人が約 1 割いる(フィンランド 9.9%)。ある瞬間に気分や体の感覚が意識にのぼるのは約 4 分の 1 の瞬間(大学生 30 人)。
- 場の空気(音楽・雑音・テンポ)が行動を変えた例は多いが、後で言葉にできたかを数で測った研究は、本書が読めた範囲では North ら 1999 の「気づいていなかった」の 1 行だけで、割合は要旨に無い。
- 記録 2-70 ④ の「境目を人のデータで測るのは難しい」は、読んだ範囲と合う。値はどれも課題・集団・測り方ごとに違い、渋谷の住民の場面に直接当てはまる値は無い。

## §5 記録 2-70 の文献の列の一次確認(写し検査)

| # | 文献 | 記録 2-70 の文 | 読めた範囲と等級 | 合うか | 記録が原典より強く言っている所 |
|---|---|---|---|---|---|
| 1 | Sclar ら(ICLR 2024・arXiv 2310.11324v2) | 意味の同じ書き方の違いだけで正答率が最大 76 ポイント動き、モデルを大きくしても例を足しても残る。どの書き方が良いかはモデルどうしで弱くしか相関しない | arXiv の要旨 ○ [P1] | **合う**。「up to 76 accuracy points when evaluated using LLaMA-2-13B」「Sensitivity remains even when increasing model size, the number of few-shot examples, or performing instruction tuning」「format performance only weakly correlates between models」 | 76 は LLaMA-2-13B の数(記録は模型の名を落としている)。指示調整でも残る点は記録に無い(弱めてはいない) |
| 2 | arXiv 2601.09706(Dutulescu ら・v1 2026-01-14) | LLM は数を記号のトークンとして処理し、埋め込みが大きさを持たない | 要旨と HTML ◎ [P2] | **一部**。要旨の「numbers are processed as symbolic tokens whose embeddings do not explicitly encode numerical value」と合う。ただし本文の実験は **GPT-2 の形を一から学ばせた**小さな模型(数の課題だけ・語彙も数だけ)で、学習済みの LLM は試していない(著者の限界の節:「the results may not fully reflect performance in more complex scenarios involving large pretrained models」) | 「LLM は」と一般に言う所。別の研究は、LLM の隠れ状態から数の値が線形に読み出せ、ベクトルの足し算で出力を動かせたと書く(Zhu ら arXiv 2401.03735v4・要旨 ○ [P3])。2601.09706 の主張は「埋め込みの表に値が明示されていない」で、「中で大きさを表していない」ではない【見立て】 |
| 3 | vLLM の prompt embeds | 埋め込みの列を入力に受け付け、チャットの形で文と混ぜて任意の位置に入れられる(`--enable-prompt-embeds`・形を誤るとエンジンが落ちうる) | 公式の文書 latest(頁の日付 2026-10-29)◎ [V15] | **合う**。「Multiple `prompt_embeds` parts can appear in any message, in any position relative to text parts.」「The vLLM engine may crash if incorrect shape of embeddings is passed. Only enable this flag for trusted users!」 | 文書は頭の使い回しの不具合(#56655)に触れていない。記録 2-70 の【直し 11-16】が足した注のとおり |
| 4 | PPlug(Liu ら・ACL 2025 long 461・arXiv 2409.11901v2) | 履歴を 1 つの埋め込みにまとめて入力に付けるだけで、本体を変えずに 1.4〜35.8% 良い | arXiv の HTML v2 ◎ [A1]・ACL の書誌は検索の抜粋 △ | **合う**(数の出どころ)。「the relative improvements of PPlug over the best baseline (RSPG-Post) are from 1.4% to 35.8%」(§4.4)。要旨には数が無い | 「1.4〜35.8%」は**最良の比べ相手(RSPG-Post)に対する相対の伸び**で、LaMP の 6 課題・主の LLM は FlanT5-XXL(11B)。本体の LLM は凍らせるが、入力の符号器・射影(2 層の MLP)・指示の埋め込みは学ばせる |
| 5 | 「感情の目標は、プロンプトより内部の向きで押す方が一貫して良かった(NeurIPS 2026・説得の会話)」 | 同左 | NeurIPS の頁の要旨 ○ [B1] | **一部**。要旨は「consistently outperforms prompt-based delivery of the same emotional targets」と書く。ただし **NeurIPS 2026 の本会議ではなくワークショップ(PTA)のポスター**で、題は「Steering to Persuade: A Learned Policy over an LLM's Internal Emotion Representations」。相手は模擬の寄付の会話(人を相手にしたかは頁に無い)。模型の名・大きさ・数値は頁に無い | 「NeurIPS 2026」はワークショップの意。数値で確かめられない |
| 6 | arXiv 2601.22329(Tak ら「Sparks of Rationality」v1 2026-01-29) | 考える力と感情の押しの間には緊張関係があり、考えることが押し込まれた感情を正当化しうる | 要旨 ○・HTML の前半 ◎ [B2] | **合う**。要旨「a tension between reasoning and affective steering」。序論「reasoning can amplify vulnerability under emotional steering, allowing the model to rationalize the induced affect」 | 主の模型は **Qwen3-4B**(8B は時間割引の付録だけ)。人との比べは、既存の人の研究の向きと比べた定性の比べで、人の数値との突き合わせではない |
| 7 | Sentipolis(Fu ら・arXiv 2601.18027v2・2026-04-21) | 連続した感情の状態を人の基準点で感情の言葉に直し、短い文にしてプロンプトに入れる | 要旨 ○・HTML の前半 10 万字 ◎ [B4] | **合う**。状態は PAD(快・覚醒・支配)の連続値。人の話し声の注釈の集め(MSP-Podcast・264,705 点・PAD を [−1, 1] に直した)で k 近傍(k=3・ユークリッド距離)を引き、Plutchik 型の感情の札にする。札は多数決にせず全部を次の段に渡し、記憶と人物と合わせて LLM が 1 段落の文にしてプロンプトに入れる(例「Tom Moreno feels a buoyant surge of happiness…」) | 「短い文」は LLM が書く 1 段落の描写で、強さの語の決まった表は無い。速い更新(会話の番ごと)も遅い更新(振り返り)も、変化の量(Δ)は LLM が出す。減衰は半減期 120 分。主の模型は GPT-4o-mini・GPT-5.2・Grok など大きな API の模型で、**7B/8B は無い**。もっともらしさは大きな模型で +25〜85% 上がり、GPT-4o-mini で −7〜−26% 下がった(表 1・判定役 3 つ)。社会の決まりへの従いは少し下がった |
| 8 | Dunn B.D. ほか 2010(Psychol Sci 21(12): 1835–1844・PMID 21106893) | 心拍をより正確に追える人ほど、心拍の反応と主観的な興奮の結びつきが強い。体の感覚に敏感なことは、体の信号の向きによって直感の判断を助けもし妨げもした | Europe PMC の要旨 ○ [H1](PMC に全文なし・OA でない) | **合う**。研究 1: 心拍を正確に追える人ほど、感情の写真への心拍の反応と主観の覚醒の評定が強く結びついた。**快・不快の評定では結びつきは無かった**。研究 2: 内受容の力が高いと、体の先回りの信号が有利な選択を指すか不利な選択を指すかによって、直感の選択を助けもし妨げもした | 「覚醒だけで、快・不快では無い」の限定を記録は落としている。人数は要旨に無い(未確認) |

## §6 空欄(見つからなかったもの・調べていないもの)

1. 気分や興奮で温度などの引き方を変えた LLM のエージェントの先例。検索 1 回の抜粋の範囲では見つからなかった(状態はどれも文か活性の操舵で入れていた)。検索をもう 1〜2 回足せば出る可能性はある。
2. 3 つの型のどれかで、人の行動のデータの分布と比べて確かめた先例(§2-5)。
3. PPlug の副作用(考える力・文の崩れ)の記述。HTML v2 の読めた範囲に無かった。
4. prompt embeds・操舵のプラグインでのバッチ不変の確かめ(R-141 §10-2 の 3 から変わらず。本書でも見つからなかった)。
5. #57006・#54509・#51899 がどの版に入ったかのタグでの確かめ。GitHub の robots が比較の頁を禁じるので、合流の日と、#51899 の頁の「0.31.0 の拾い上げの里程標」の記述だけで書いた。
6. vLLM 0.33.0・0.32.0 以前のリリースノートの全文での prompt embeds の行の検索(一覧の頁の読めた範囲だけ)。
7. 暑さ寒さの申告の正確さ(Cheung ら 2019 は OpenAlex に要旨が無く、著者稿は読んでいない)。
8. 感情の粒度の一般の集団での分布(Barrett らの系統)・日本の集団のアレキシサイミアの値・Nisbett & Wilson 1977 の後の見直し(White 1980・Wilson & Stone 1985・Newell & Shanks 2014 など)。調べていない。
9. 混み具合を意識せずに受け取って行動が変わり、後で言葉にできたかを数で測った研究。調べていない(音楽と雑音の 3 本だけ)。
10. 要旨に無かった数: Dunn 2010 の人数・Mauss 2005 の人数と相関の値・Johansson 2005 の人数と気づいた割合・North 1999 の本数と問いに答えた人の割合・Mathews & Canon 1975 の手助けの率。

## §7 読めなかったもの・取り方の注

| # | 何が | 理由 | 本書への影響 |
|---|---|---|---|
| U1 | 全体 | 作業の途中で Web の道具が利用の上限に 2 回当たり、止まった(2 回目は Europe PMC の要旨の取得の途中)。別の道具に替えずに止まり、親の再開の合図の後に、同じ道具で同じ頁から続けた | 調べる範囲を絞った(§6 の 1・8・9) |
| U2 | GitHub の比較・コミットの一覧・`?q=` つきの検索 | robots.txt が禁じる | PR の入った版はタグの比較で確かめていない(§6 の 5) |
| U3 | 発行元の頁(APA・Elsevier・SAGE・Science) | 開いていない(索引の要旨で足りた) | 要旨だけ(○) |
| U4 | 著者稿・保管庫の原稿 | 開いていない | 発行元が断った論文を別の場所で読んだものは無い(取り方の注の 1 行ずつの記録は不要) |

- 断られた頁(403・robots・規約)は無かった。名乗り・経路・ミラー・キャッシュ・第三者の写し・web.archive.org は使っていない。
- 重みのファイル(SAE の `.pt` を含む)は開いていない・取っていない。

## §8 出典の表(読んだ日はすべて 2026-11-21)

| # | 出典 | URL | 読んだ範囲 | 等級 |
|---|---|---|---|---|
| V1 | vLLM のリリースの一覧と v0.34.0 のリリースノート | https://github.com/vllm-project/vllm/releases ・ https://github.com/vllm-project/vllm/releases/tag/v0.34.0 | 一覧の頁(0.32.0〜0.34.0 の題と日)・0.34.0 のノートの全文 | ◎ |
| V2 | Issue #56655「[Bug]: Mixed prompt embedding masks are omitted from prefix cache keys, causing incorrect outputs」 | https://github.com/vllm-project/vllm/issues/56655 | 本文と書き込みの全部 | ◎ |
| V3 | PR #56656「[Bugfix] Include mixed prompt embedding masks in prefix cache keys」 | https://github.com/vllm-project/vllm/pull/56656 | 頁の全体(状態・審査・書き込みの日) | ◎ |
| V4 | PR #51899「[Core][BugFix] Tag prefix-cache extra keys by source」 | https://github.com/vllm-project/vllm/pull/51899 | 頁の前半 10 万字 | ◎ |
| V5 | PR #57006「[Bugfix][Frontend] Validate mixed prompt embedding mask lengths」 | https://github.com/vllm-project/vllm/pull/57006 | 頁の前半 10 万字 | ◎ |
| V6 | PR #54509「[Bugfix][Frontend] Truncate prompt_is_token_ids with the prompt」 | https://github.com/vllm-project/vllm/pull/54509 | 頁の状態と要約 | ◎ |
| V7 | Issue #57719「[Bug]: prompt_embeds + any penalty kills the engine with a device-side assert ...」 | https://github.com/vllm-project/vllm/issues/57719 | 本文と書き込みの全部 | ◎ |
| V8 | PR #57762「[Bugfix][MRV1] Fix penalties with prompt embeddings」 | https://github.com/vllm-project/vllm/pull/57762 | 頁の状態と要約 | ◎ |
| V9 | Issue #51122「[Bug]: enable_prompt_embeds + enable_lora on Llama crashes ...」 | https://github.com/vllm-project/vllm/issues/51122 | 本文と書き込みの全部 | ◎ |
| V10 | PR #67566「[Bugfix][Compile] Key the AOT compile cache on loaded general plugins」 | https://github.com/vllm-project/vllm/pull/67566 | 頁の本文 | ◎ |
| V11 | hotwire-vllm PR #1「Salt the compile cache key on vLLM 0.34 too」 | https://github.com/moudrkat/hotwire-vllm/pull/1 | 頁の本文 | ◎ |
| V12 | RFC #36998「[RFC]: Observation Plugin for Intercepting & Routing on Activations」 | https://github.com/vllm-project/vllm/issues/36998 | 状態と最後の 5 件の書き込み | ◎ |
| V13 | PR #37002「[Core][Feature] Observation Plugin for Intercepting & Routing on Activations」 | https://github.com/vllm-project/vllm/pull/37002 | 状態と審査の要約 | ◎ |
| V14 | vLLM の API の頁「vllm.sampling_params.SamplingParams」(latest) | https://docs.vllm.ai/en/latest/api/vllm/sampling_params/ | 頁の前半 10 万字 | ◎ |
| V15 | vLLM「Prompt Embedding Inputs」(latest・頁の日付 2026-10-29) | https://docs.vllm.ai/en/latest/features/prompt_embeds/ | 頁の全体 | ◎ |
| V16 | github.com の robots.txt | https://github.com/robots.txt | 全体 | ◎(数に入れない) |
| P1 | Sclar M., Choi Y., Tsvetkov Y., Suhr A.「Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design」ICLR 2024・arXiv 2310.11324v2 | https://arxiv.org/abs/2310.11324 | 要旨と版の履歴 | ○ |
| P2 | Dutulescu A., Ruseti S., Dascalu M.「Value-Aware Numerical Representations for Transformer Language Models」arXiv 2601.09706v1 | https://arxiv.org/html/2601.09706v1 | 要旨と HTML の本文 | ◎ |
| P3 | Zhu F., Dai D., Sui Z.「Language Models Encode the Value of Numbers Linearly」arXiv 2401.03735v4 | https://arxiv.org/abs/2401.03735 | 要旨と版の履歴 | ○ |
| A1 | Liu J. ほか「LLMs + Persona-Plug = Personalized LLMs」ACL 2025(long 461・pp. 9373–9385)・arXiv 2409.11901v2 | https://arxiv.org/html/2409.11901v2 ・ https://aclanthology.org/2025.acl-long.461 | arXiv の HTML v2(§3・§4・表 1〜4)。ACL の書誌は検索の抜粋 | ◎ |
| B1 | Senthilnathan V., Karimpanal George T., Rana S.「Steering to Persuade: A Learned Policy over an LLM's Internal Emotion Representations」NeurIPS 2026 ワークショップ PTA のポスター | https://neurips.cc/virtual/2026/161970 | 頁の要旨 | ○ |
| B2 | Tak A.N. ほか「Sparks of Rationality: Do Reasoning LLMs Align with Human Judgment and Choice?」arXiv 2601.22329v1 | https://arxiv.org/html/2601.22329v1 | 要旨と HTML の前半 10 万字 | ◎ |
| B3 | Bas T., Novak K.「What Can We Actually Steer? A Multi-Behavior Study of Activation Control」arXiv 2511.18284v2 | https://arxiv.org/html/2511.18284v2 | 要旨と HTML | ◎ |
| B4 | Fu C. ほか「Sentipolis: Emotion-Aware Agents for Social Simulations」arXiv 2601.18027v2(2026-04-21) | https://arxiv.org/html/2601.18027v2 | 要旨と HTML の前半 10 万字(表 1・表 3・図 5) | ◎ |
| B5 | Sun M. ほか「How Emotion Shapes the Behavior of LLMs and Agents: A Mechanistic Study」(E-STEER)arXiv 2604.00005v1 | https://arxiv.org/abs/2604.00005 | 要旨 | ○ |
| C1 | Ho M.K. ほか「Can Induced Emotion Bias LLM Behaviors in Sequential Decision Making?」arXiv 2607.12631v1 | https://arxiv.org/abs/2607.12631 | 要旨 | ○ |
| X1 | Golkar S. ほか「xVal: A Continuous Numerical Tokenization for Scientific Language Models」arXiv 2310.02989v2(NeurIPS ワークショップ ML4PS) | https://arxiv.org/abs/2310.02989 | 要旨 | ○ |
| H1 | Dunn B.D. ほか「Listening to your heart. How interoception shapes emotion experience and intuitive decision making」Psychol Sci 21(12): 1835–1844(2010)・PMID 21106893 | https://doi.org/10.1177/0956797610389191 | Europe PMC の要旨 | ○ |
| H2 | Garfinkel S.N. ほか「Knowing your own heart: distinguishing interoceptive accuracy from interoceptive awareness」Biol Psychol 104: 65–74(2015)・PMID 25451381 | https://doi.org/10.1016/j.biopsycho.2014.11.004 | Europe PMC の要旨 | ○ |
| H3 | Zamariola G. ほか「Interoceptive accuracy scores from the heartbeat counting task are problematic: Evidence from simple bivariate correlations」Biol Psychol 137: 12–17(2018)・PMID 29944964 | https://doi.org/10.1016/j.biopsycho.2018.06.006 | Europe PMC の要旨 | ○ |
| H4 | Van Dongen H.P. ほか「The cumulative cost of additional wakefulness ...」Sleep 26(2): 117–126(2003)・PMID 12683469(正誤表 Sleep 2004;27(4):600 は未読) | https://doi.org/10.1093/sleep/26.2.117 | Europe PMC の要旨 | ○ |
| H5 | Sadoul B.C. ほか「The relationship between appetite scores and subsequent energy intake: an analysis based on 23 randomized controlled studies」Appetite 83: 153–159(2014)・PMID 25149199 | https://doi.org/10.1016/j.appet.2014.08.016 | Europe PMC の要旨 | ○ |
| H6 | Mattila A.K. ほか「Age is strongly associated with alexithymia in the general population」J Psychosom Res 61(5): 629–635(2006)・PMID 17084140 | https://doi.org/10.1016/j.jpsychores.2006.04.013 | Europe PMC の要旨 | ○ |
| H7 | Mauss I.B. ほか「The tie that binds? Coherence among emotion experience, behavior, and physiology」Emotion 5(2): 175–190(2005)・PMID 15982083 | https://doi.org/10.1037/1528-3542.5.2.175 | Europe PMC の要旨 | ○ |
| H8 | Heavey C.L., Hurlburt R.T.「The phenomena of inner experience」Conscious Cogn 17(3): 798–810(2008)・PMID 18258456 | https://doi.org/10.1016/j.concog.2007.12.006 | Europe PMC の要旨 | ○ |
| H9 | North A.C., Hargreaves D.J., McKendrick J.「The influence of in-store music on wine selections」J Appl Psychol 84(2): 271–276(1999) | https://doi.org/10.1037/0021-9010.84.2.271 | OpenAlex の要旨 | ○ |
| H10 | Mathews K.E., Canon L.K.「Environmental noise level as a determinant of helping behavior」JPSP 32(4): 571–577(1975) | https://doi.org/10.1037/0022-3514.32.4.571 | OpenAlex の要旨(OCR の崩れあり) | ○ |
| H11 | Milliman R.E.「Using Background Music to Affect the Behavior of Supermarket Shoppers」J Marketing 46(3): 86(1982。終わりの頁は索引に無い) | https://doi.org/10.1177/002224298204600313 | OpenAlex の要旨 | ○ |
| H12 | Nisbett R.E., Wilson T.D.「Telling more than we can know: Verbal reports on mental processes」Psychol Rev 84(3): 231–259(1977) | https://doi.org/10.1037/0033-295X.84.3.231 | OpenAlex の要旨 | ○ |
| H13 | Johansson P. ほか「Failure to detect mismatches between intention and outcome in a simple decision task」Science 310(5745): 116–119(2005)・PMID 16210542 | https://doi.org/10.1126/science.1111709 | Europe PMC の要旨 | ○ |
| H14 | Cheung T.C.T. ほか「Analysis of the accuracy on PMV – PPD model using the ASHRAE Global Thermal Comfort Database II」Building and Environment 153: 205–217(2019) | https://doi.org/10.1016/j.buildenv.2019.01.055 | OpenAlex の書誌だけ(要旨なし) | 書誌だけ |
| S1 | 検索の抜粋(気分・興奮と引き方の温度の先例の検索。arXiv 2607.25140・2604.27345・2601.16087・2504.14706・2503.02457 の題と抜粋) | (検索の結果) | 検索の抜粋 | △ |
| S2 | 検索の抜粋(PPlug の ACL Anthology の書誌: ACL 2025 long 461・pp. 9373–9385・DOI 10.18653/v1/2025.acl-long.461) | (検索の結果) | 検索の抜粋 | △ |

- 等級の数(robots の V16 を除く): ◎ 20(V1〜V15・P2・A1・B2・B3・B4)・○ 19(P1・P3・B1・B5・C1・X1・H1〜H13)・△ 2(S1・S2)・書誌だけ 1(H14)。計 42。
- 読んだ版: arXiv は各行の v の番号のとおり。雑誌の論文は、どれも公開の索引(Europe PMC・OpenAlex)が載せる雑誌の版の要旨で、著者稿は読んでいない。GitHub の頁は 2026-11-21 に読んだ時点の状態。
- 既存答申からの引用: R-141(B)§2〜§5・§7・§10、R-141 の追補(B)§3、R-153(B)§2-3・§6、R-149(B)§0・§3・§5、R-126(B)§3-6(R-141 経由)。読み直していない。D 等級の答申は根拠に使っていない。

### 親に確かめてほしい数値(5 つ)

1. #56655 と PR #56656 が 2026-11-21 の時点で開いたまま・承認 0、回避は「頭の使い回しを切る」[V2][V3]。#51899 の合流 2026-09-30 と、#56655 の印の欠けを直していないこと [V4]。
2. #57719 と PR #57762 が開いたまま(0.27.1 と 0.30 で再現)・#67566 が開いたまま(0.33.0 と 0.34.0rc1.dev441 で操舵が黙って効かない)・hotwire-vllm 0.1.5 [V7][V8][V10][V11]。
3. PPlug の「1.4〜35.8%」が最良の比べ相手 RSPG-Post に対する相対の伸び(§4.4)で、主の模型が FlanT5-XXL [A1]。
4. Bas & Novak の 90.8/87.9・67.1/88.7・51.4/89.1 と、一貫性 49.3 対 約 88(Llama 3.1 8B・15 層・判定役 GPT-4.1)[B3]。
5. Zamariola 2018 の r=.16・N=572、Sadoul 2014 の r≤0.26・549 人、Van Dongen 2003 の n=48 と「largely unaware」、Mattila 2006 の 9.9%(5,454 人)[H3][H5][H4][H6]。

## 親の一次確認(第348・2026-11-21)

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| vLLM の issue #56655(prompt embeds と頭の使い回しを一緒に使うと誤った出力を返す)は開いたまま・直す PR #56656 も開いたまま | 親が web の道具で GitHub の issue の頁を読んだ(2026-11-21) | 合う。題は「Mixed prompt embedding masks are omitted from prefix cache keys, causing incorrect outputs」。2026-09-13 に開かれ、状態は Open。PR #56656 も Open(issue の頁の表示。PR の頁そのものは読んでいない) |
| 断られた頁・取り方 | 答申の冒頭の注と §6 を読んだ | 断られた頁は無いと書かれている。GitHub の比較の頁は robots が禁じているので読んでいない、とある。Web の道具の上限に 2 回当たり、別の道具に替えずに止まった、とある |
| そのほかの数値(PPlug の 1.4〜35.8%・Bas & Novak の値・人の側の値・#57719 ほかの状態) | 確かめていない | 未確認 |
