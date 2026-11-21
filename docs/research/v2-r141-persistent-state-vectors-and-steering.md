<!-- hdr:v1 | 等級: B(第344 親の一次確認=末尾の表) | 作成: 2026-11-04 | 範囲: 指示書 11-04 §5-1(題 9-1 の状態ベクトルの研究) -->
# R-141 持続する状態ベクトルと操舵(本人ごとの性格と気分の数値を出来事ごとに更新し、LLM を呼ぶときに効かせる形の先例と、vLLM でどこまでできるか)

- **分野**: 自然言語処理・機械学習 #27 / 認知科学(記憶・習慣) #12 / 人格心理学 #13 / 計算機科学(並列・決定論) #28 / ソフトウェア工学 #29 | **重要度**: P1([返事その 4(11-04)](../design/prompt-2026-11-04-reply4.md) §5 の 1。題 9-1 の「状態ベクトル」の中身を決める材料)
- **一次確認**: B(第344・親=末尾の表)。筆者がこの回に読んだ出典は 53 本(◎ 22・○ 30・△ 1)。既存答申からの引用は 4 本(R-126・性格の答申・R-123・R-135)と回答 10-25・指示書 11-04。読めなかったものは §10 に挙げた。
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-11-04・リサーチ役(Opus 5.5)。子サブは起動していない。Web は読むだけ。WebFetch と WebSearch は最初の 1 回から利用の上限で使えなかったので、公式の文書・arXiv・GitHub の頁は curl と gh(GitHub の API)で標準出力に取り、HTML を剥がして grep で該当の文を確かめた。リポにも data/ にも何も保存していない(作業の写しはリポの外の一時の場所だけ)。コードは読むだけで写していない(hotwire-vllm・vllm-lens・steering-mechanics は MIT、EasySteer は Apache-2.0)。pip も重みの取得もしていない。封印の層(holdout・test の層)には触れていない。コード・台帳・設計書・INDEX は 1 バイトも変えていない。
> 断られた頁: ACM のデジタル図書館(ALMA の論文の DOI の転送先)が 403 を返したので、名乗り・経路・写しを変えずにそこで止めた(§10)。
> 等級: ◎=原典か公式の文書・ソース・課題票の本文を読んだ(該当の文を grep で確かめた)/○=抄録・要旨・題と状態だけ・既存答申の孫引き/△=検索の抜粋だけ。筆者の組み立ては【見立て】、根拠の無い置き方は【推測】と書く。**推薦は書かない**。決めるのはユーザー。
> 既存答申との関係: PPlug・CAA・persona vectors・RepE の基本の形と、probe の限界(対照課題・amnesic probing・分布のずれ)、感情ベクトルが「局所」であること(Anthropic 2026)、「本人のベクトルだけ変えたとき読み出しが動くか」の検査の手順は [R-126](v2-r126-second-gen-decision-model-activations-heads.md) §3-3・§3-6・§7(等級 B)を正とし、ここでは繰り返さずに引く。Big Five の規準(川本 2015)と「性格を B5 に 1 バイトも載せない」案、操舵と prefix KV の衝突の指摘は [性格の答申](v2-personality-traits-research.md) §(b)(等級 B)、5070 の vLLM の版(0.28.0)とバッチ不変の検証の手順は [R-123](v2-r123-rtx5070-qwen3-8b-runbook.md)(等級 B)、心のモジュールの調停と共有の状態は [R-135](v2-r135-mind-modules-precedents.md)(等級 B)にある。一貫性の手法の比較(回答 [10-25](../design/v2-answers-2026-10-25.md) §5 の R-G・番号は未付与)は本書と範囲が重なる。本書は R-G のうち「操舵ベクトルの Qwen3 での実例と vLLM への入れ方・複数 LoRA の限界・バッチ不変との関係」を扱い、PPlug 型の符号器の学習と dm_eval での崩れの測り方の設計は扱わない。活性をテープに残す道(11-04 §5 の 2)は別の答申の範囲なので、本書では読み出しの輪に要る範囲だけ触れる。

## §0 要旨

1. 状態を「数値で持ち、LLM の中に差す」先例は 4 型に分かれる。残差に方向を足す型(ActAdd・CAA・persona vectors・RepE)、入力の埋め込みに差す型(PPlug・PERSOMA)、重みを足す型(LoRA・Neeko・Text-to-LoRA)、表現を学習して差し替える型(LoReFT)。更新が数の足し算で済むのは 1 番目だけで、ほかは符号器の前向き計算か学習が要る。
2. 「ゆっくりの性格+速い気分」を数値で持ち出来事ごとに更新する先例は、LLM の外の感情モデル(ALMA など・本書では本文を読めていない)と、数値を文にしてプロンプトに書く Humanoid Agents にある。数値を操舵として LLM に差し、出来事ごとに係数を変える社会シミュの先例は見つからなかった(§10)。近いのは役ごとに操舵の係数を選ぶ Role Steering(OLMo-3-7B・275 役)だけ。
3. 気分の操舵は Qwen3-8B で実例がある。価と覚醒の 2 軸の部分空間は Qwen3-8B・14B でも現れ、覚醒の軸で拒否の率が動く。ただし Qwen3 は Llama の約 7 倍の係数(|α|≤3.0)が要り、Qwen3-8B は α=+3.0 で分布の外の出力が 17% に上がる [S27]。
4. 読み出しで状態を確かめる輪の先例は、probe で条件を見て操舵を入れる CAST、射影が普段の範囲を出たら切る Assistant Axis の activation capping、層をまたいで誤差を返す PID・LQR の操舵の 3 系統ある。capping は Qwen3-32B の 64 層のうち 46〜53 層、25 百分位の閾値で、有害な応答を約 6 割減らし能力を落とさなかった [S28]。
5. 層と強さの測り方の先例は、効き目の層の掃引(persona vectors=Qwen2.5-7B で 28 層中 20 層目)、判定役の LLM による一貫性の点(0〜100)、MMLU・IFEval・GSM8k・EQ-Bench、分布の外の率、相対量(係数×方向のノルム÷残差のノルム)である。日本語では言語の識別(FastText・LCB の行単位の合格率)と LaBSE の意味の保持が使われている。Qwen3 で日本語の生成を操舵して測った例は見つからなかった。
6. Big Five の操舵は、選択式の問いには効くが、自由な生成や文脈の多いプロンプトでは効きが弱いと報告されている(Llama 3.3 70B)[S34]。特性どうしは直交にしても互いに動く [S35]。v2 の判断の入力は文脈が長いので、この 2 点がそのまま当たる【見立て】。
7. vLLM 本体(0.28.0)にあるのは prompt embeds(`--enable-prompt-embeds`・チャットの本文の中に埋め込みを差せる)と複数 LoRA(`--enable-lora`・既定は 1 バッチに 1 本・rank は 512 まで)。**活性の操舵は本体に無い**。制御ベクトルの PR は 3 本とも採られずに閉じ、観測の口の RFC #36998 と PR #37002 は開いたまま止まっている。
8. 操舵はプラグインかフォークで入る。hotwire-vllm(CUDA グラフを保つ・Qwen3-8B-FP8 と Qwen3-14B-AWQ で確認・同じ層に 2 本は重ならない・係数ごとに枠を 1 つ使い切る)、vllm-lens(eager を強制・0.30.0 に固定)、EasySteer(0.29.0 のフォーク・接頭辞のキャッシュの鍵に操舵の設定が入る)。3 つとも、検証済みの vLLM の版が R-123 の 0.28.0 と違う。
9. バッチ不変は Qwen3-8B-AWQ で試験済みで、LoRA は v0.32.0 から決まった順で足す split-K=8 の道に替わった(それ以前は SPLIT_K=1)。prompt embeds と操舵のプラグインがバッチ不変を保つかを書いた資料は無い。prompt embeds と接頭辞のキャッシュの組み合わせには、誤った出力を返す未解決の不具合が 1 件ある(#56655)。
10. 今のコードとの接点は 4 か所【見立て】。艦隊の `_payload` は `params_extra` で任意の欄を足せる。判断の入力は共通 B0〜B4b → 人物 PS/PL → B5・B6 の順なので、「接頭辞の後ろにだけ足す」形が位置で決められる。体の欄に気分と性格の数は無く、TIPI の欄は空。記憶の埋め込み(Ruri 256 次元)は PPlug 型の入力に使える次元ではない。

## §1 問いと前提

### 1-1 問い(11-04 §5 の 1)

本人ごとの状態ベクトル(性格のゆっくり変わる部分と、気分の速く変わる部分)を出来事ごとに小さな計算で更新し、LLM を呼ぶときに操舵として効かせる形の先例。5 つの副問。

1. 先例ごとの状態の持ち方・更新・注入の場所・費用。
2. 気分の操舵と、返事の後の活性の読み出し(probe)で状態と食い違いがないかを確かめる輪の先例。
3. Qwen3 系で日本語の生成を壊さない層と強さの測り方。
4. vLLM で操舵・ソフトプロンプト(prompt embeds)・複数の LoRA がどこまで使えるか(版と機能の名を一次で)。
5. 今のコード(心と判断の口・`perception/renderer.py`・記憶)との接点。

### 1-2 前提(読んだもの)

| 前提 | 中身 | 場所 |
|---|---|---|
| 題 9-1 の仮決定 | 心の内に「状態ベクトル(性格のゆっくりの部分と気分の速い部分)」を置く。テープの腕は 1 呼につき 1 本の活性(1 層・最後のトークン・fp16 で約 8 KB)・既定 off | [11-04](../design/prompt-2026-11-04-reply4.md) §4 |
| 一貫性の手法の順 | 操舵ベクトル(学習なし・1 人 8〜24 KB)→ PPlug 型の埋め込み(共有の符号器・睡眠中に再計算)→ 型ごとの LoRA/LoReFT。1 人ずつの LoRA はしない。人ごとの差分は接頭辞の後ろに置く | [10-25](../design/v2-answers-2026-10-25.md) §4 の P6 |
| 5070 の構成 | vLLM 0.28.0・`Qwen/Qwen3-8B-AWQ`・`VLLM_BATCH_INVARIANT=1`・B14 の形で 32/32 を自検証 | [R-123](v2-r123-rtx5070-qwen3-8b-runbook.md) §0 の 2・3 |
| Qwen3-8B の形 | 36 層・隠れ次元 4096・注意の頭 32・KV の頭 8・頭の次元 128 | [S48] ◎ |
| 性格の数の置き場 | 5 float32 × 40 万体 = 8 MB。B5 には載せない(prefix を壊さないため) | [性格の答申](v2-personality-traits-research.md) の予算の行 |

## §2 先例: 状態の持ち方・更新・注入の場所・費用(副問 1)

### 2-1 残差に方向を足す型

| 手法 | 方向の作り方 | 注入の場所 | 状態の持ち方 | 更新の費用 | 出典 |
|---|---|---|---|---|---|
| ActAdd | 対のプロンプト 1 組(「Love」と「Hate」など)の中間の活性の差 | 前向き計算の途中の層に足す | 方向 1 本+係数 | 係数を変えるだけ | [S23] ○ |
| CAA | 正例と負例の対の残差の差の平均 | **ユーザーのプロンプトの後の全位置**に係数つきで足す | 行動ごとに 1 本 | 同上 | [S24] ○・R-126 §3-3 |
| RepE | 集団の表現を読む・足す(正直さ・害など) | 層の表現 | 概念ごとの方向 | 同上 | [S25] ○ |
| persona vectors | 特性の説明から対照のシステムプロンプトと質問を自動で作り、応答の残差の平均の差を取る | 層を 1 つ選んで足す。Qwen2.5-7B は 28 層中 20 層目(悪・追従)と 16 層目(作り話)、Llama-3.1-8B は 16 層目。層は「同じ係数で各層を操舵して特性の点が一番高い層」で選ぶ(付録 B.4) | 特性ごとに 1 本 | 同上 | [S26] ◎ |
| 価と覚醒の部分空間 | 感情ラベルつきの文 211,225 件から感情ベクトルを取り、主成分と ridge 回帰で価と覚醒の 2 軸を作る | **全層・全位置**に足す(貪欲のデコード) | 2 軸の座標(角度と強さ) | 同上 | [S27] ◎ |
| Role Steering(社会シミュ) | 役の像から役ごとの方向 | 係数 4 通りを掃引し、役ごとに合格か印を付ける | 役ごとに 1 本 | 同上 | [S32] ○ |

- 状態が係数の列なら、出来事ごとの更新は「係数を足し引きする」だけになる。体ごとの持ち物は軸の数 × 4 B(7 軸なら 28 B・35 万体で約 9.8 MB)で、合成した 1 層ぶんのベクトル(4096 × fp16=8,192 B)は呼ぶときに作れば持たなくてよい。合成済みを全員ぶん持つと 35 万体 × 8,192 B ≈ 2.9 GB【見立て・算術】。
- persona vectors の操舵には副作用がある。係数を大きくすると MMLU が落ち、論文は応答の一貫性の点(GPT-4.1-mini が 0〜100 で採点)を 75 以上に保った結果だけを示している [S26 ◎]。
- 特性どうしは独立に動かせない。Big Five の方向は直交化しても、1 つを操舵すると他の特性の行動も動く(LLaMA-3-8B・Mistral-8B)[S35 ○]。Llama 3.3 70B の Big Five の方向は probe としてはよく当たるが、操舵は選択式の課題に限って効き、自由な生成と「プロンプトに別の文脈があるとき」は効きが弱い [S34 ○]。
- 文脈で強さを変える形もある。固定の方向の強さを、今の隠れ状態から決めるゲートを学習する方法は、複数の言語と行動の組み合わせで一定の強さの操舵とプロンプトを上回ったと抄録が書く [S40 ○]。

### 2-2 入力の埋め込みに差す型(ソフトプロンプト)

| 手法 | 状態の持ち方 | 更新 | 注入の場所 | 費用 | 出典 |
|---|---|---|---|---|---|
| PPlug | 履歴の各件を凍った符号器(BGE-base)で埋め込み、入力との内積の softmax で重み付けして足した 1 本 | 履歴が変わったら符号器を回し直す | 入力の前に [指示の埋め込み; 本人の埋め込み] を置く。LLM は凍結。学習するのは符号器の上の 2 層 MLP の射影と指示の埋め込み | 符号器 1 回+1 トークン | R-126 §3-3(#14 ○) |
| PERSOMA | 対話の履歴を文のまま再標本化・圧縮して、ソフトプロンプトの埋め込みにする | 同上 | ソフトプロンプト | 抄録に数値なし | [S45] ○ |

- 出来事ごとに埋め込みを作り直すには、符号器の前向き計算が要る。10-25 §4 の P6 は「睡眠中に再計算」としている。気分のような速い部分を毎呼ごとに埋め込みで表す先例は見つからなかった【見立て】。

### 2-3 重みを足す型(LoRA)と表現を差し替える型(ReFT)

| 手法 | 状態の持ち方 | 更新 | 費用 | 出典 |
|---|---|---|---|---|
| S-LoRA | 主記憶に全アダプタを置き、走っている要求のぶんだけ GPU へ。KV と同じ統一ページングで管理 | 学習済みのアダプタを差し替える | 1 枚の GPU で数千のアダプタ。HF PEFT と素朴な vLLM より速い(抄録) | [S41] ○ |
| Punica | 違う LoRA の演算を 1 バッチで束ねる CUDA カーネル | 同上 | 処理量 12 倍・1 トークンあたり +2 ms(抄録) | [S42] ○ |
| Neeko | 登場人物ごとの LoRA の塊を動的に選ぶ | 新しい役は追加の学習 | 学習が要る | [S46] ○ |
| Text-to-LoRA | 課題の説明文からハイパーネットワークが LoRA を 1 回の前向き計算で作る | 文を変えれば作り直せる | 学習済みのハイパーネットワークが要る | [S44] ○ |
| LoReFT | 凍ったモデルの隠れ表現に低ランクの介入を学習する。LoRA より 15〜65 倍パラメータが少ない(抄録) | 学習 | 学習が要る | [S43] ○ |

- 1 人ずつの LoRA と人格の微調整はしない、と 10-25 §4 の P6 が決めている。本書の範囲では、LoRA は「型ごと」の器としてだけ比べる。

### 2-4 数値の状態を文にして渡す型(比較のため)

- Humanoid Agents は、基本の欲求(空腹・健康・活力)・感情・関係の近さの 3 つを System 1 の要素として持ち、日々の活動と会話を変える [S47 ○]。抄録の範囲では、状態は LLM の入力の文として渡している。今の v2 の内受容の行(B5 の空腹の語など)と同じ型である【見立て】。
- 性格をゆっくりの層、気分を速い層とし、気分が性格の決める基準へ戻る形の古典は ALMA(Gebhard 2005)にある。本書では本文を読めていない(§10)。

## §3 気分の操舵と、読み出しで確かめる輪(副問 2)

### 3-1 気分・感情の操舵の実例

| 研究 | モデル | 何を足したか | 結果 | 測り方 | 出典 |
|---|---|---|---|---|---|
| 価と覚醒の部分空間 | Llama-3.1-8B・**Qwen3-8B**・Qwen3-14B | 価と覚醒の 2 軸(12 方向 × 45 の強さ) | 円の形の幾何が 3 モデルで再現(半径 0.37・0.37・0.39)。覚醒で拒否の率が動く(Llama の HarmBench 87%→5% at α=+0.45)。Qwen3 は約 7 倍の係数が要る。Qwen3-8B の HarmBench の拒否率は α=−3.0 で 97.0%・0 で 89.5%・+3.0 で 67.0%、分布の外の出力は +3.0 で 17.0% | 生成文の価と覚醒(VAD-BERT・英語)・拒否率・追従率・分布の外の率・MATH-500・IFEval | [S27] ◎ |
| 感情で揺らす小さなモデルの判断 | 複数の系統(抄録に名なし) | 実際の感情を起こす文から作った方向 | 感情の揺らしは戦略の選択を系統的に変えるが、行動は不安定で人の期待と合わないことが多い | ゲーム理論の型の課題(Diplomacy・StarCraft II・ペルソナ) | [S33] ○ |
| 嫉妬の構成要素 | Llama・Qwen・Gemma の 8 モデル | 評価理論の 2 要因を直交化した方向 | 双方向の因果の操舵で判断が動く | RepE | [S52] ○ |
| Anthropic 2026(感情の概念) | Claude | 171 語の感情ベクトル | ベクトルは主に「局所」(今の文が扱う感情)で、持続する気分ではない | — | R-126 §3-6(#29 ○) |

- R-126 §3-6 の「局所」の性質と合わせると、持続する気分は LLM の中に残らない。エンジンの側で数値として持ち、呼ぶたびに差し直す形になる【見立て】。

### 3-2 読み出し(probe)で状態を確かめる輪

| 型 | 中身 | 読み出しの位置 | 何をするか | 出典 |
|---|---|---|---|---|
| 監視だけ | persona vectors: プロンプトの最後のトークンの射影が、続く応答の特性の点と r=0.75〜0.83 で相関 | 最後のプロンプトのトークン | 記録して見る | R-126 §3-3(#17・親が ◎ で確認) |
| 範囲を出たら切る | Assistant Axis の activation capping: 射影が普段の範囲(25 百分位)を下回ったら、その値まで戻す。複数の層に同時にかけないと効かない。Qwen3-32B は 64 層中 46〜53 層(8 層・12.5%)、Llama 3.3 70B は 80 層中 56〜71 層(16 層・20%) | 全トークン | 有害な応答を約 60% 減らし、IFEval・MMLU Pro・GSM8k・EQ-Bench を落とさなかった | [S28] ◎ |
| 条件で操舵を入れる | CAST: 入力の種類が隠れ状態の違う型を起こすことを使い、「X の話なら拒否」のような規則で操舵を入れるか決める | 入力 | 条件つきの操舵 | [S29] ○ |
| 閉ループ(層をまたぐ) | PID の操舵: 既存の操舵は比例(P)の制御にあたるとし、積分と微分の項を足す | 層の間 | 行き過ぎを抑える | [S30] ○ |
| 閉ループ(最適制御) | 層ごとのヤコビアンで局所線形とみなし、LQR で目標の意味の点へ引く | 層の間 | 設定点への追従の誤差に上界 | [S31] ○ |
| probe が発火したら操舵(実装) | RhizoNymph のフォーク: 活性を取る口と操舵を結び、全体と要求ごとの設定で「probe が発火したら操舵する」。最悪で数 % の処理量の低下(本人の申告) | 要求ごと | 本体には入っていない | [S14] ◎(RFC #36998 の 2026-07-12 のコメント) |

- 持続する persona の崩れを読む先例もある。Assistant Axis への射影は会話の領域ごとに動き(セラピーと哲学の会話で一番「Assistant らしくない」側へ寄る)、Qwen3 0.6B の埋め込みでユーザーの発話から次の応答の射影をよく当てられた [S28 ◎]。Qwen3-32B は Assistant から遠ざけると人の像を作って「経験年数」や出生地を語りがちだった [S28 ◎]。住民の役を演じさせる v2 では、この軸の向きの意味が逆になる(Assistant に寄ることが崩れにあたる)【見立て】。
- persona の座標で学んだ probe は、生の活性で学んだ probe より分布の外で汎化した(10 の評価データ)[S49 ○]。
- 「本人のベクトルだけ変えたとき読み出しが動くか」の検査(対照=状況の文の感情・同じノルムの無作為の方向・対照課題で学んだ probe、P0/P1 の床、amnesic の因果の確認)は R-126 §7 にある。状態ベクトルを操舵に使うと、読み出しの方向と操舵の方向が同じ空間に入る。そのまま読むと、足したものを読み返すだけになる恐れがある【推測】。R-126 §7 の対照 2(同じノルムの無作為の方向)がこれを分ける手段になる【見立て】。

## §4 Qwen3 系で日本語の生成を壊さない層と強さの測り方(副問 3)

### 4-1 層の選び方の先例

| 先例 | モデル | 選んだ層 | 選び方 | 出典 |
|---|---|---|---|---|
| persona vectors | Qwen2.5-7B(28 層) | 20(悪・追従)・16(作り話) | 各層を同じ係数で操舵し、特性の点が一番高い層 | [S26] ◎ |
| activation capping | Qwen3-32B(64 層) | 46〜53 | 中心の深さを 2 層おきに、幅を 4・8・16 層で掃引し、安全と能力の両立の前線で選ぶ | [S28] ◎ |
| 価と覚醒 | Qwen3-8B・14B | 全層 | — | [S27] ◎ |
| hotwire の例と steering-mechanics | Qwen3-4B | 20 層目(例) | 相対量の測定(下の 4-2) | [S17] ◎・[S22] ○ |
| SAE の言語の操舵 | Gemma-2B・9B(中国語・日本語・スペイン語・フランス語) | 中〜後ろの層が最も効く | 1 層の SAE の特徴 1 つで最大 90% 言語を切り替え | [S37] ○ |
| 多言語の SAE と層の規則 | LLaMA-3.1-8B・Gemma-2-9B | 「多言語の整列」と「言語の分離」が重なる深さ | 事前の規則で層を当てる | [S51] ○ |
| 日本語の敬語の表現 | TinySwallow-1.5B(28 層) | 敬語の区別は 15 層目の残差で均衡正答率 0.96 | 線形の probe | [S38] ○ |

- Qwen3-8B(36 層)への読み替え【見立て・算術】: persona vectors の 20/28(約 71%)は 25〜26 層、capping の 46〜53/64(約 72〜83%)は 26〜30 層にあたる。Qwen3-8B で日本語の生成を操舵して層を選んだ例は見つからなかった(§10)。

### 4-2 強さの規格

| 規格 | 中身 | 値の例 | 出典 |
|---|---|---|---|
| 生の係数 α | 方向に掛ける数 | Qwen3-8B の覚醒で ±3.0(Llama は ±0.45)。Llama は |α|≤0.20 で分布の外 2% 未満・|α|=0.45 で方向により 29〜94% | [S27] ◎ |
| 固定のノルム | 方向を正規化して決まった大きさで足す | persona vectors の方向の比較 | [S26] ◎ |
| ノルム合わせ | 足す量を「残差のノルム × 係数」にする(`norm_match`) | vllm-lens の引数 | [S18] ◎ |
| 相対量 | |係数| × ‖V‖ ÷ ‖h‖(その層の残差のノルム) | 一貫性の崩れは約 1.9 から、安全な作業点は約 0.7(Qwen3-4B・20 層・標本が少なく暫定と作者が書く)。短いプロンプトでは ‖h‖ を約 7 分の 1 に見積もる(注意の吸い込みのトークンのため) | [S17] ◎・[S22] ○ |
| 百分位の閾値 | 射影の分布の百分位で切る | 25 百分位(capping) | [S28] ◎ |

### 4-3 壊れたかを測る物差しの先例

| 物差し | 何を見るか | 使った先例 | 日本語に使えるか |
|---|---|---|---|
| 一貫性の点 | 判定役の LLM が 0〜100 で採点 | persona vectors(75 以上を保つ) | 判定役の日本語の力しだい【見立て】 |
| 能力の評価 | MMLU・MMLU Pro・IFEval・GSM8k・MATH-500・EQ-Bench | persona vectors・capping・価と覚醒 | 英語の評価。日本語の評価で操舵を測った例は無かった |
| 分布の外の率 | 意味をなさない出力の割合 | 価と覚醒 | 言語を問わない |
| 言語の取り違え | LCB の行単位の合格率(LPR)と語単位の合格率(WPR)。LCB は日本語を含む 15 言語。WPR は非ラテン文字の言語だけ | ReCoVeR(Llama 3.1 8B・Qwen 2.5 7B・Gemma 2) | 日本語に使える。Llama の言語ベクトルは中国語と日本語を近くに置いた [S36 ◎] |
| 言語の識別と意味の保持 | FastText の言語の識別・LaBSE の類似度 | SAE の言語の操舵(日本語を含む) | 使える |
| 語の多様さ | 語彙の多様さ | Role Steering(対照の方向は大きな係数で急に落ちた) | 使える |
| 言語の崩れ | 大きな英語のベクトルが資源の少ない言語の表現を圧倒して起きる「言語の崩れ」。多言語の平均でノルムが下がると和らぐ。事前学習で得意な言語は単一言語の語彙の方が強い | 多言語の語彙での感情の操舵 | 日本語のデータから方向を作る根拠の 1 つ【見立て】 |

- 今のリポにある床(P0=同じ入力の再実行・P1=言い換え)と dm_eval の 340 場面は、R-126 §7 の指標の床として既に挙がっている。操舵の崩れの物差しにも同じ床が使える【見立て】。

## §5 vLLM でどこまで使えるか(副問 4)

### 5-1 機能ごとの表(vLLM 本体)

| 機能 | 名前・欄 | 版 | Qwen3 | 他の機能との相性(公式の表) | 未解決の不具合 | 出典 |
|---|---|---|---|---|---|---|
| prompt embeds(オフライン) | `EmbedsPrompt` の `prompt_embeds`=(系列の長さ, 隠れ次元)のテンソル | 0.28.0 の文書にあり | 不具合の報告は Qwen3-0.6B で再現している(#56655) | 互換表で 連続バッチ ✅・接頭辞のキャッシュ ✅・LoRA ✅・CUDA グラフ ✅・logprobs ✅・投機的デコード ❌・プロンプトの logprobs ❌(表の頁の日付 2026-05-01) | — | [S1][S2] ◎ |
| prompt embeds(サーバー) | `--enable-prompt-embeds`(既定 False・「形を誤ると落ちる・信頼できる利用者だけ」)。Completions は `prompt_embeds`(base64 の torch テンソル・テンプレートは自分で)。**Chat Completions は本文の中に `{"type": "prompt_embeds", "data": ...}` を文と混ぜて置ける**(サーバーがテンプレートを巻く) | Chat の本文の部品は PR #40720(2026-05-01 合流)=0.28.0 に入っている | 同上 | 同上 | #56655(開)文と埋め込みを混ぜたときの印が接頭辞のキャッシュの鍵に入らず、前の要求の KV を使って誤った出力を返す(2026-09-13・main で再現)。#57719(開)prompt embeds+罰則(repetition・presence・frequency)でエンジンが落ちる(0.27.1) | [S1][S4][S9][S11][S12] |
| prompt embeds(新しい実行器 V2) | — | PR #42963(2026-08-17 合流)は 0.28.0 に**入っていない**・0.32.0 に入っている | — | — | — | [S10] ○ |
| 複数 LoRA | `--enable-lora`・`--max-loras`(1 バッチの本数・**既定 1**)・`--max-lora-rank`(1〜512・既定 16)・`--max-cpu-loras`(CPU の控え・max_loras 以上)・`--lora-target-modules`・要求の `model` に LoRA の名 | 0.28.0 | `Qwen3ForCausalLM` は LoRA ✅・PP ✅ | 連続バッチ ✅・接頭辞のキャッシュ ✅・CUDA グラフ ✅・投機的デコード ❌ | #51122(開)prompt embeds+LoRA が並行で落ちる(Llama・0.11.0 の報告) | [S3][S4][S6][S13] |
| LoRA の動的な読み込み | `VLLM_ALLOW_RUNTIME_LORA_UPDATING=True`・`/v1/load_lora_adapter`・`/v1/unload_lora_adapter`・`load_inplace`(同じ名で差し替え)・LoRAResolver のプラグイン(「本番では使わない」と警告) | 0.28.0 | — | — | — | [S3] ◎ |
| LoRA と量子化 | AWQ と GPTQ の量子化のモデルに LoRA を載せる例と試験(TinyLlama の AWQ・GPTQ) | 0.28.0 の木にある | Qwen3-8B-AWQ で試した記録は見つからない | — | — | [S7] ◎ |
| バッチ不変 | `VLLM_BATCH_INVARIANT=1`・CC 8.0 以上・試験済みに Qwen3-8B と Qwen3-8B-AWQ | 0.28.0(文書の日付 2026-07-16)・latest(2026-11-03) | ✅ | latest の文書は「LoRA の shrink の和を 8 つの決まった塊に分けて決まった順で足す」と書く | — | [S5] ◎ |
| LoRA のバッチ不変の道 | 以前は SPLIT_K=1。PR #59377 で決まった順の split-K=8 に替わり、**出力のビットが前の道と変わる**(どちらもバッチの組み方には不変) | 0.32.0 に入っている・0.28.0/0.30.0/0.31.0 には入っていない | Qwen3-4B+LoRA で試験 | — | — | [S8] ◎ |
| 活性の操舵 | **本体に無い** | 制御ベクトルの PR #5807・#7906・#12870 はどれも採られずに閉じた(放置で自動で閉じた・2025)。観測の口の RFC #36998 と PR #37002 は開いたまま(RFC は 2026-10-29 に古い印) | — | — | — | [S14][S15][S16] ◎ |

- 版の並び: 0.28.0(2026-08-26)・0.29.0(09-09)・0.30.0(09-22)・0.31.0(10-05)・0.32.0(10-18)・0.33.0rc3(11-02)[S50 ◎]。
- 1 人ぶんの埋め込みを 1 トークンで差す場合、1 要求の本文は 4096 × 2 B=8,192 B、base64 で約 10.9 KB 増える【見立て・算術。torch の直列化の頭の分は未計測】。

### 5-2 操舵を足す道具(本体の外)

| 道具 | 形 | 検証の版 | CUDA グラフ | 要求ごとの操舵 | 接頭辞のキャッシュ | 限界 | Qwen3 | ライセンス | 出典 |
|---|---|---|---|---|---|---|---|---|---|
| hotwire-vllm 0.1.2 | `vllm.general_plugins` のプラグイン。Triton の custom op を各デコーダ層の最後に置き、`hidden[tok] += scales[slot] * bank[slot]` | 0.25.1・0.29.0(README) | 保つ(PIECEWISE・FULL)。idle と全要求の操舵で TPOT が同じ(Qwen3-4B・4070 Ti SUPER・8 並列 1.78 ms/トークン、eager は 1.88) | `vllm_xargs` の `{"id","layer","scale"}`。ベクトルは起動時に `.pt` から読む(実行中の登録は予定)。`decode_only` で生成だけ | 文書に記述なし | **同じ層に 2 本は重ならない(後が勝つ)**。異なる (ベクトル, 層, 係数) ごとに枠を 1 つ使い、終わっても解放しない(既定 16 枠)。連続の係数は枠を使い切る。TP>1・投機的デコード・LoRA・GPTQ は未試験 | Qwen3-8B-FP8(2.27→2.28 ms)・Qwen3-14B-AWQ(1.91→1.91)・Qwen3-4B・0.6B で確認 | MIT | [S17] ◎ |
| vllm-lens | プラグイン。活性の取り出し・操舵(`SteeringVector`・`norm_match`・`position_indices`)・任意の Python のフック(HTTP では cloudpickle=任意のコードの実行) | **0.30.0 に固定**(H100 × 2 で検証) | **`enforce_eager=True` を強制**。V2 の実行器は拒否 | 要求ごと(`extra_args`・`vllm_xargs`) | 文書に記述なし | eager の費用(hotwire の測定で +2.3〜5.6%) | 「小さな Qwen の組で検証」(どの Qwen かは書いていない) | MIT | [S18] ◎ |
| EasySteer | vLLM 0.29.0 のフォーク(`vllm-steer/`)と、公式の wheel に Python のファイルを重ねる導入 | 0.29.0・V2 の実行器 | `in_graph`(単一ベクトル)・`split`(複数ベクトル・グラフを区切る)・eager | `SteeringSpec`・位置の選択(`prompt_positions=[-1]`・`prompt_window=(-k, None)`・`generation_window`)・既定の設定と要求ごとの上書き | **KV のキャッシュの鍵に、効いている操舵の設定が入る**。同じプロンプトと同じ設定だけが再利用できる | 複数ベクトルは split。ビームサーチとは併用不可。活性の取り出しのグラフは GPU 1 枚・LoRA なし・投機的デコードなしが条件 | 例は Qwen2.5-1.5B | Apache-2.0 | [S19] ◎・[S20] ○ |
| IBM vLLM Hook | プラグイン。受け身(観測)と能動(介入) | v1 の実行器(RFC のコメントで作者が説明) | — | — | — | — | — | — | [S21] ○・[S14] ◎ |
| RhizoNymph のフォーク | 不透明な torch op と常駐の GPU バッファ。全体と要求ごとの操舵を足し合わせる。probe の発火で操舵 | 記載なし | 保つ(本人の申告) | 混ぜたバッチに制約なし(本人の申告) | — | 本体の PR は閉じた | — | — | [S14][S16] ◎ |
| nnsight の vLLM 統合 | 任意の Python を任意のモジュールに | — | — | — | — | — | — | — | [S14] ◎(RFC のコメントだけ) |

- バッチ不変との関係: 3 つの道具の文書と README に、バッチ不変(`VLLM_BATCH_INVARIANT`)の語は無い(GitHub のコードの検索でも 0 件)。hotwire の op は 1 トークンごとの足し算なので、行どうしは独立しているように見える【推測】。それでも、コンパイルの中身が変わるので B14 の試験を通し直す必要がある【見立て】。
- 接頭辞のキャッシュとの関係【見立て】: EasySteer は操舵の設定を鍵に入れるので、人ごとに違う設定を使うと共通の接頭辞も人ごとに別の鍵になる。hotwire は KV の鍵について何も書いておらず、プラグインはコンパイルのキャッシュの鍵だけを塩で分けている。接頭辞の当たりで飛ばされた位置には操舵が入らず、逆に操舵して計算した位置の KV を操舵なしの要求が再利用しうる。要求ごとの `cache_salt`(今の艦隊が送っている欄)で分ける道はあるが、試した記録は見つからなかった(§10)。

## §6 本プロジェクトの今の形との接点(副問 5・すべて【見立て】)

コードの読みは HEAD `2160272`。

| 場所 | 今の形 | 状態ベクトルと操舵との接点 |
|---|---|---|
| `llm/fleet.py` の `_payload` | `messages`=system(`call.system`)+user。`seed`・`chat_template_kwargs`・`cache_salt` を送る。`call.params_extra` を辞書のまま足す(「診断・ablation 用」) | 操舵の指定(`vllm_xargs`)・LoRA の名(`model`)を渡す口はすでにある。足すと `params_hash` が変わり、既定のテープの再生が外れる(R-126 §親に聞きたいこと 4 と同じ型) |
| `engine/decision/port.py` の `compose` | 共通(B0〜B4b)→ 人ごと(短い版 PS+B6・長い版 PL+B5+B6)→ 提示 →(長い版だけ)指示 | 「共通の接頭辞の後ろにだけ足す」(10-25 P6・CAA の「プロンプトの後」)は、PS/PL の開始位置から後ろ、または `prompt_window=(-k, None)`(EasySteer)・`decode_only`(hotwire)で表せる。PS/PL の文と操舵が同じ性格を二重に伝えないかは別の題 |
| `engine/decision/persona.py`・`build/pop/w21_persona.py` | 人物の文(短い版と長い版)を読むだけの配列で持つ。TIPI-J の 5 欄は値が空(腕)で、値を入れたときだけ長い版に 1 行 | 性格の係数の初期値の置き場の候補。性格の答申は「B5 に 1 バイトも載せない」案だった |
| `agents/state.py` | 内受容の欄は `hunger`・`fatigue`・`thermal` の 3 つ。店の評価の記憶に `sm_valence`。気分と性格の欄は無い | 状態ベクトルは新しい SoA の欄と状態台帳の行になる。気分の減衰と評価の式は R-E(中核感情)の範囲 |
| `perception/renderer.py` | 状態 → 知覚の事実 `Percept` → B0〜B6 の文。`prefix_key` は B0〜B4b の合成鍵 | 11-04 §4 で知覚を「何があるか」と「何に気づくか」に分けた。気分が注意の選択に効く道(心の側・コード)と、気分が文の書き方に効く道(操舵・LLM の側)は別の口になる |
| `engine/memory_store.py`・`memory_m1.py`・`memory_embed.py` | 記憶の器(出来事・人・店の行)と ACT-R の折衷の強さ、意味の手がかりの埋め込み(Ruri-v3-30m・256 次元・腕) | PPlug 型の本人の埋め込みは履歴の埋め込みを重み付きで足す形なので、器の行と埋め込みが材料になる。ただし 256 次元から Qwen3-8B の 4096 次元への射影(PPlug の 2 層 MLP にあたる)を学習する必要がある |
| テープの腕(11-04 §4) | 1 呼に 1 本の活性(1 層・最後のトークン・8 KB)・既定 off | 読み出しの輪(§3-2)の入力と同じ形。用途の「感情や性格の読み出し・ペルソナの崩れの計器」に、Assistant Axis 型の射影と persona vectors 型の監視が当たる |

## §7 比較の表(推薦なし)

| 観点 | 残差への加算(操舵) | prompt embeds(PPlug 型) | 型ごとの LoRA | LoReFT | 文にして書く(今の形) |
|---|---|---|---|---|---|
| 状態の持ち方 | 軸ごとの係数(7 軸で 28 B/体)+共有の方向 | 本人の埋め込み 1〜数本(4096 次元 × トークン数) | 型の番号 | 型の番号 | 文(PS/PL・B5) |
| 出来事ごとの更新 | 係数の足し引き(数の計算だけ) | 符号器の前向き計算(10-25 は睡眠中) | 学習(型の付け替えだけなら番号を変えるだけ) | 学習 | 文の組み直し |
| 注入の場所 | 層 × 位置を選べる(全位置・プロンプトの後・最後の k・生成だけ) | 入力の埋め込みの位置 | 全層の重み | 層の表現 | 入力の文 |
| 気分の速い部分 | 先例あり(価と覚醒・Qwen3-8B) | 先例は見つからなかった | 向かない(学習が要る) | 向かない | 先例あり(Humanoid Agents) |
| vLLM 0.28.0 で | 本体に無い(プラグインかフォーク) | 本体にある(Chat の本文に混ぜられる) | 本体にある(既定 1 本/バッチ) | 本体に無い(EasySteer のフォークで pyreft の形を読む) | そのまま |
| 接頭辞の KV の共有 | 道具しだい(EasySteer は設定ごとに別の鍵) | 埋め込みを後ろに置けば前は共有できる見込み【推測】。混ぜたときの鍵の不具合 #56655 が未解決 | アダプタが違えば共有できない【推測】 | 同左【推測】 | 後ろに置けば共有できる(今の形) |
| バッチ不変 | 資料なし | 資料なし | 試験の道あり(0.32.0 で道が変わる) | 資料なし | 試験済み(Qwen3-8B-AWQ) |
| 日本語の崩れの先例 | 英語のベクトルによる言語の崩れの報告あり。Qwen3 の日本語の例は無い | 先例なし | 先例なし | 先例なし | — |
| 主な限界の報告 | 文脈が多いと効きが弱い・特性どうしが干渉・係数を大きくすると能力が落ちる | 符号器と射影の学習が要る | 1 人ずつは作らない(P6) | 学習が要る | 8B が数値や例示を写す(47% 事件) |
| 費用 | 加算 1 回/層。hotwire は CUDA グラフのままで差が測れない程度 | 要求が約 11 KB/トークン増える | Punica は +2 ms/トークン(抄録) | 抄録に数値なし | B5 のトークン |

## §8 決めるべき題(選択肢と根拠・推薦は書かない)

1. **状態ベクトルの表し方**: (a) 軸ごとの係数(性格 5 軸+気分 2 軸など)と共有の方向 /(b) 本人の埋め込み(PPlug 型)/(c) 文のまま /(d) 組み合わせ(ゆっくりの部分は埋め込み、速い部分は係数など)。根拠: §2・§7。
2. **注入の場所**: 層(1 層・連続した数層・全層)× 位置(プロンプトの後・最後の k トークン・生成だけ)。根拠: CAA は「プロンプトの後」、capping は 8 層連続、価と覚醒は全層全位置、hotwire は `decode_only`(§2-1・§4-1)。共通の接頭辞を保つかどうかと一緒に決まる。
3. **道具**: (a) vLLM 本体だけ(prompt embeds と LoRA)/(b) プラグイン(hotwire・vllm-lens)/(c) フォーク(EasySteer)/(d) HF transformers の別の道。どれも pip の許可が要る(CLAUDE.md §7・入れる前に聞く)。検証の版が R-123 の 0.28.0 と違う(hotwire 0.25.1・0.29.0、vllm-lens 0.30.0、EasySteer 0.29.0)ので、版を上げるか道具を合わせるかも題になる。
4. **強さの規格**: 生の係数 / ノルム合わせ / 相対量 / 百分位の閾値。係数を連続で持つか、決まった段の表(パレット)に丸めるか(hotwire は枠の数から段の表を勧めている)。
5. **方向の作り方**: 英語の対照データ / 日本語の対照データ / 本人の人物の文から自動で作る(persona vectors 型)/ 価と覚醒の部分空間。根拠: §4-3 の言語の崩れの報告。
6. **読み出しの輪**: なし / 監視だけ(テープの腕に載せて計器にする)/ 範囲を出たら切る(capping 型)/ 条件で操舵を入れる(CAST 型)/ 閉ループ(PID・LQR)。読み出しの方向と操舵の方向が重なる問題を、どの対照で分けるか(R-126 §7)。
7. **壊れたかの物差し**: 日本語の取り違え(LCB の LPR・WPR)・意味の保持(LaBSE)・一貫性の点(判定役)・dm_eval と P0/P1 の床・分布の外の率。どれを合格の線にするか。
8. **バッチ不変**: 操舵ありの腕で B14(32/32)を通すことを条件にするか。prompt embeds と LoRA も同じか。LoRA は 0.32.0 で出力のビットが変わる。
9. **テープへの記録**: 呼ごとに、使った状態ベクトルの版・係数・層・位置・道具の版を記録する欄(R-126 §5-2 の `persona_vec_id` の拡張)。`params_hash` に入れるか、腕の列にするか。
10. **R-G との分担**: 本書は R-G(10-25 §5)の一部を扱った。R-G を別に発注するか、本書で足りるとするか。

## §9 出典(読んだ日はすべて 2026-11-04)

等級: ◎=本文 / ○=要旨・二次・題と状態 / △=検索の抜粋

| # | 出典 | URL | 等級 |
|---|---|---|---|
| S1 | vLLM「Prompt Embedding Inputs」(latest・頁の日付 2026-10-29 と v0.28.0 の両方) | https://docs.vllm.ai/en/latest/features/prompt_embeds/ ・ https://docs.vllm.ai/en/v0.28.0/features/prompt_embeds/ | ◎ |
| S2 | vLLM「Features」互換表(v0.28.0・頁の日付 2026-05-01) | https://docs.vllm.ai/en/v0.28.0/features/ | ◎ |
| S3 | vLLM「LoRA Adapters」(v0.28.0) | https://docs.vllm.ai/en/v0.28.0/features/lora/ | ◎ |
| S4 | vLLM「Engine Arguments」(v0.28.0)の LoRA と prompt embeds と接頭辞のキャッシュの行 | https://docs.vllm.ai/en/v0.28.0/configuration/engine_args/ | ◎ |
| S5 | vLLM「Batch Invariance」(v0.28.0・2026-07-16 と latest・2026-11-03) | https://docs.vllm.ai/en/v0.28.0/features/batch_invariance/ ・ https://docs.vllm.ai/en/latest/features/batch_invariance/ | ◎ |
| S6 | vLLM「Supported Models」(v0.28.0)の Qwen3ForCausalLM の行 | https://docs.vllm.ai/en/v0.28.0/models/supported_models/ | ◎ |
| S7 | vLLM v0.28.0 の木の `examples/features/lora/lora_with_quantization_offline.py`・`tests/lora/test_quant_model.py` | https://github.com/vllm-project/vllm/tree/v0.28.0 | ◎(grep) |
| S8 | PR #59377「Add deterministic split-K=8 LoRA shrink for batch invariance」(2026-10-04 合流)と、タグとの比較 | https://github.com/vllm-project/vllm/pull/59377 | ◎ |
| S9 | PR #40720「Enable prompt_embeds Content Part Support in vLLM Chat Completions API」(2026-05-01 合流)と、タグとの比較 | https://github.com/vllm-project/vllm/pull/40720 | ○(題と合流と比較だけ) |
| S10 | PR #42963「[ModelRunnerV2] Support prompt embeds」(2026-08-17 合流)と、タグとの比較 | https://github.com/vllm-project/vllm/pull/42963 | ○(同上) |
| S11 | Issue #56655「Mixed prompt embedding masks are omitted from prefix cache keys, causing incorrect outputs」(開) | https://github.com/vllm-project/vllm/issues/56655 | ◎(本文の前半) |
| S12 | Issue #57719「prompt_embeds + any penalty kills the engine」(開・0.27.1) | https://github.com/vllm-project/vllm/issues/57719 | ◎(本文の要点) |
| S13 | Issue #51122「enable_prompt_embeds + enable_lora on Llama crashes ... under concurrency」(開・0.11.0)・修正の PR #51123(開) | https://github.com/vllm-project/vllm/issues/51122 | ○(題と版だけ) |
| S14 | RFC #36998「Observation Plugin for Intercepting & Routing on Activations」と全コメント・PR #37002(開) | https://github.com/vllm-project/vllm/issues/36998 | ◎ |
| S15 | 制御ベクトルの要望 #3451 と PR #5807・#7906・#12870(どれも合流なしで閉じた)と最後のコメント | https://github.com/vllm-project/vllm/pull/7906 ・ https://github.com/vllm-project/vllm/pull/12870 | ◎ |
| S16 | RhizoNymph の PR #38881・#42815〜#42818(合流なしで閉じた) | https://github.com/vllm-project/vllm/pull/42815 | ◎ |
| S17 | hotwire-vllm の README・CHANGELOG(0.1.2・2026-09-14)・pyproject(MIT) | https://github.com/moudrkat/hotwire-vllm | ◎ |
| S18 | vllm-lens の README・docs/compatibility.md(MIT) | https://github.com/UKGovernmentBEIS/vllm-lens | ◎ |
| S19 | EasySteer の README(Apache-2.0)と文書「Steering」「Graphs, caching, and performance」 | https://github.com/ZJU-REAL/EasySteer ・ https://zju-real.github.io/EasySteer/latest/user-guide/steering/ ・ https://zju-real.github.io/EasySteer/latest/user-guide/performance/ | ◎ |
| S20 | Xu ほか「EasySteer」arXiv 2509.25175v3(EMNLP 2026 System Demonstrations) | https://arxiv.org/abs/2509.25175 | ○ |
| S21 | Ko & Chen「vLLM Hook v0」arXiv 2603.06588 | https://arxiv.org/abs/2603.06588 | ○ |
| S22 | steering-mechanics の README(MIT) | https://github.com/moudrkat/steering-mechanics | ○(grep だけ) |
| S23 | Turner ほか「Steering Language Models With Activation Engineering」(ActAdd)arXiv 2308.10248 | https://arxiv.org/abs/2308.10248 | ○ |
| S24 | Panickssery ほか「Steering Llama 2 via Contrastive Activation Addition」arXiv 2312.06681 | https://arxiv.org/abs/2312.06681 | ○ |
| S25 | Zou ほか「Representation Engineering」arXiv 2310.01405 | https://arxiv.org/abs/2310.01405 | ○ |
| S26 | Chen ほか「Persona Vectors」arXiv 2507.21509v3(HTML。付録 B.4 の層の選び方を含む) | https://arxiv.org/html/2507.21509v3 | ◎ |
| S27 | 「Valence-Arousal Subspace in LLMs」arXiv 2604.03147v3(HTML。付録 F の表 10 を含む) | https://arxiv.org/html/2604.03147v3 | ◎ |
| S28 | Lu ほか「The Assistant Axis」arXiv 2601.10387v1(HTML) | https://arxiv.org/html/2601.10387v1 | ◎ |
| S29 | Lee ほか「Programming Refusal with Conditional Activation Steering」(CAST)arXiv 2409.05907 | https://arxiv.org/abs/2409.05907 | ○ |
| S30 | 「Activation Steering with a Feedback Controller」(PID)arXiv 2510.04309 | https://arxiv.org/abs/2510.04309 | ○ |
| S31 | 「Local Linearity of LLMs Enables Activation Steering via Model-Based Linear Optimal Control」arXiv 2604.19018 | https://arxiv.org/abs/2604.19018 | ○ |
| S32 | 「Role Steering of Language Models for Social Simulations」arXiv 2608.00023v2 | https://arxiv.org/abs/2608.00023 | ○ |
| S33 | 「On Emotion-Sensitive Decision Making of Small Language Model Agents」arXiv 2604.06562 | https://arxiv.org/abs/2604.06562 | ○ |
| S34 | 「Linear Personality Probing and Steering in LLMs: A Big Five Study」arXiv 2512.17639v2 | https://arxiv.org/abs/2512.17639 | ○(性格の答申の △ を抄録で確認) |
| S35 | 「Do Personality Traits Interfere? Geometric Limitations of Steering in LLMs」arXiv 2602.15847 | https://arxiv.org/abs/2602.15847 | ○(同上) |
| S36 | Sterz ほか「ReCoVeR the Target Language」arXiv 2509.14814v1(HTML) | https://arxiv.org/html/2509.14814v1 | ◎(grep) |
| S37 | 「Causal Language Control in Multilingual Transformers via Sparse Feature Steering」arXiv 2507.13410 | https://arxiv.org/abs/2507.13410 | ○ |
| S38 | 「Interpretable Cross-Lingual Alignment in Small Language Models ... Japanese-English Bilingual LLMs」(J-PragEval)arXiv 2608.14896 | https://arxiv.org/abs/2608.14896 | ○ |
| S39 | 「Steering with Multilingual Lexicons for Sentiment Control in Low-Resource Languages」arXiv 2611.03317 | https://arxiv.org/abs/2611.03317 | ○ |
| S40 | 「Compositional Activation Steering Across Languages and Behaviors with Contextual Gates」arXiv 2610.24906 | https://arxiv.org/abs/2610.24906 | ○ |
| S41 | Sheng ほか「S-LoRA」arXiv 2311.03285 | https://arxiv.org/abs/2311.03285 | ○ |
| S42 | Chen ほか「Punica」arXiv 2310.18547 | https://arxiv.org/abs/2310.18547 | ○ |
| S43 | Wu ほか「ReFT」arXiv 2404.03592 | https://arxiv.org/abs/2404.03592 | ○ |
| S44 | 「Text-to-LoRA」arXiv 2506.06105 | https://arxiv.org/abs/2506.06105 | ○ |
| S45 | 「PERSOMA」arXiv 2408.00960 | https://arxiv.org/abs/2408.00960 | ○ |
| S46 | 「Neeko」arXiv 2402.13717 | https://arxiv.org/abs/2402.13717 | ○ |
| S47 | Wang ほか「Humanoid Agents」arXiv 2310.05418 | https://arxiv.org/abs/2310.05418 | ○ |
| S48 | `Qwen/Qwen3-8B` の config.json | https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json | ◎ |
| S49 | 「Do Linear Probes Generalize Better in Persona Coordinates?」arXiv 2605.09391 | https://arxiv.org/abs/2605.09391 | ○ |
| S50 | vLLM のリリースの一覧(GitHub の API) | https://github.com/vllm-project/vllm/releases | ◎ |
| S51 | 「Multilingual Steering by Design」arXiv 2605.23036 | https://arxiv.org/abs/2605.23036 | ○ |
| S52 | 「Mechanistic Decoding of Cognitive Constructs in LLMs」arXiv 2604.14593 | https://arxiv.org/abs/2604.14593 | ○ |
| S53 | arXiv の検索の結果の題の一覧(ALMA・Japanese の操舵の検索) | https://export.arxiv.org/api/query | △ |

既存答申: R-126(等級 B・§3-3・§3-6・§5-2・§7)・性格の答申(B・§(b)・予算の行)・R-123(B・§0・版)・R-135(B)・回答 10-25 §4 の P5・P6 と §5 の R-G・指示書 11-04 §4・§5。D 等級の答申は根拠に使っていない。
## §10 読めなかったもの・確かめていないもの・空欄

### 10-1 読めなかったもの(取り方の注)

| 何 | どこ | どうなったか |
|---|---|---|
| ALMA(Gebhard 2005「ALMA: A Layered Model of Affect」AAMAS) | https://doi.org/10.1145/1082473.1082478 → dl.acm.org | **403**。名乗り・経路・写しを変えずに止めた。性格→既定の気分→感情の層の形は本文で確かめていない |
| WebFetch と WebSearch | 道具そのもの | 最初の呼びから利用の上限で使えなかった。公式の文書・arXiv・GitHub は curl と gh で直接読んだ。一般の Web の検索はしていない |

### 10-2 空欄(読んでいない・見つからなかった)

1. Qwen3(8B を含む)で日本語の生成を操舵し、層と強さを測った例。見つからなかった。§4-1 の Qwen3-8B の層は他のモデルからの読み替え。
2. 状態ベクトルを出来事ごとに更新し、操舵として LLM に差す社会シミュの先例。見つからなかった(Role Steering は役ごとに固定の係数)。
3. prompt embeds・hotwire・vllm-lens・EasySteer のどれかで、バッチ不変(B14 の形)を確かめた記録。
4. hotwire の操舵と vLLM の接頭辞のキャッシュの組み合わせの扱い(KV の鍵)。vllm-lens も同じ。
5. 0.28.0 で prompt embeds を使うとき、既定の実行器(V2)から V1 に落ちるのか(V2 の対応 #42963 は 0.32.0 から)。
6. AWQ_marlin(R-123 の起動の形)と LoRA の組み合わせ。0.28.0 の試験は `quantization="awq"` の TinyLlama だけ。
7. 接頭辞のキャッシュの鍵に LoRA の id が入るか(§7 の LoRA の行の「共有できない」は推測)。
8. hotwire の README の Qwen3-4B の層の数(20 層目の深さの割合を出せなかった)と、steering-mechanics の相対量 1.9 と 0.7 の標本の数。
9. Anthropic の感情の論文の全文(R-126 から引き続き)・persona vectors の付録の残り(係数の値の表)。
10. CAST・PID・LQR・Role Steering・Big Five の 2 本は抄録だけで、層と係数と日本語の扱いは読んでいない。
11. EasySteer の論文の 10.8〜22.3 倍の比較の相手と条件(抄録だけ)。
12. 11-04 §4 の「今の M0〜M5 の形」の M2〜M5 の定義。コードでは M2・M4 が検収の番号として出るだけで、記憶の段の名として確かめられなかった(§6 は器・強さ・埋め込みの 3 つで書いた)。

## 親の一次確認(第344・2026-11-04・親)

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| vLLM の prompt embeds を Chat の本文に混ぜる機能は PR #40720 | GitHub の API で PR を読んだ | **一致**(題「Enable `prompt_embeds` Content Part Support in vLLM Chat Completions API」・merge 2026-05-01)。0.28.0 に入ったという版は未確認 |
| LoRA の和を決まった順の split-K=8 に替えたのは PR #59377 | 同上 | **一致**(題「Add deterministic split-K=8 LoRA shrink for batch invariance」・merge 2026-10-04)。0.32.0 という版は未確認 |
| prompt embeds と接頭辞のキャッシュの不具合 #56655 は未解決 | GitHub の API で issue を読んだ | **一致**(「Mixed prompt embedding masks are omitted from prefix cache keys, causing incorrect outputs」・open) |
| ALMA の形(§2 の「性格をゆっくりの層、気分を速い層とし、基準へ戻る形」) | 答申の出典の表 | **出典なし**=本文は 403 で未読、ほかの出典にも当たっていない。研究役の記憶による記述として【推測】扱い(根拠に使わない) |
| 断られた頁 | 冒頭の注・§10 | ALMA の DOI の転送先(dl.acm.org)が 403=名乗り・経路を変えずに止めた。本文の内容は上の 1 文のほかに入っていない |
