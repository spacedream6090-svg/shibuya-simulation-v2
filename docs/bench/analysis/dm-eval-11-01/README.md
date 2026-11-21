# dm_eval 11-01 — 消費の場面・当て口の口・比べの列(段 1 の 3 の器・GPU の前の分)

正典: 指示 `docs/design/prompt-2026-11-01.md` 段 1 の 3、`docs/design/prompt-2026-11-01-5070.md` の「柔軟にしてほしい所」(dm_eval の場面・比較の列)と「安全の規則」1〜2、回答 `docs/design/v2-answers-2026-11-01.md` §2(消費の 4 判断点)・§11(選び方の列)、`docs/reference/decision-routing-2026-11-01.md` §5(語彙に足す行為)。前の段の器は `docs/bench/analysis/wallbounce-1012/dm61/README.md`。独立の検収は `review.md`(条件つき受入)で、その指摘はすべて直した(§9)。

この段では重みを取らず、GPU とネットワークも使わない。モデルの口の試験は偽の口で回す。`src/` は変えていない。1-10 の記録 `dm61/result.json` の digest(`c33a261c…c1d0`)は変わらない。

> **注(親の判断 11-01)**: 判断に要る事実は、場面の側で短い版に入る B6 に置いた(§2-1)。DM4 の短い版に状態の欄を足す(src 側)は段 3 の問いで、親が決める。**それを直すまで、消費の場面の (G) との一致を判断モデルの選定の根拠にしない。**

## 1. 作ったもの

| ファイル | 中身 |
|---|---|
| `tools/instruments/dm_eval/scenes/consumption_v1.jsonl` | 消費の場面 44 件(4 判断点 × 11)。1-10 と同じ形の行(`situation_from_row` が読む)に、候補の欄 `candidates` と判断点の欄 `point` を足した。語彙は v3 |
| `tools/instruments/dm_eval/scenes/consumption_v1.b0.json` | 場面の前置き B0(自前・1 本) |
| `tools/instruments/dm_eval/scenes/consumption_v1.md5` | 上の 2 本の md5。jsonl `9081ccaaae185aca32e38dc922c63148`・b0 `c1eff9a10442e3af3b6108ea43b237ca` |
| `tools/instruments/dm_eval/scenes/make_consumption_v1.py` | 場面を作り直すスクリプト(決定的=同梱の 3 本とバイトで同じ物を出す。試験 `test_make_consumption_v1_reproduces_the_shipped_files`)。**jsonl が正・スクリプトは再現用** |
| `situations.py` に追加 | 読み口 `load_scene_file(path)`(md5 を照らす・候補と欄を検査する)・`SceneSet`・`DECISION_POINTS`・`CONSUMPTION_WORDS`・`CONSUMPTION_WORD_LABELS`・`CONSUMPTION_VOCAB_VERSION` |
| `backends/`(新しい部分パッケージ) | 抽象 `ChoiceBackend`・`FreeTextBackend`、推論の形 `ChoiceForm`、当て口 `LogprobChoiceScorer`・`FreeTextScorer`、自由記述の当て方 `match_free_text`、(a) `hf.HFCausalChoiceScorer`、(b) `vllm.VLLMLogprobScorer` |
| `judge.py` に追加 | 当て口の欄 `form`・`uses_gpu`・`prompt_length`、失敗の型 `ScoreFailed`、`strict_check(..., repeats=2)`、`determinism_check(..., repeats=32)`、古典の当て口の `vocab_version` と同じ語の候補への等分 |
| `bias.py` に追加 | `score_orders(..., failures=箱)`(場面ごとに失敗を捕まえる) |
| `table.py` に追加 | 列 9 本を表の末尾に(§4)。既存の 25 列は位置も見出しも変えない |
| `cli.py` | `--scenes evalset|consumption|both`(既定 evalset)・`--length short|long`・比べの節 `compare`・欄 `scene_set` と `material`・`--determinism-*`・(G) の口 `--vllm-*`・候補の口 `--hf-*`・数の指標 `qty_measures` |
| `consumption/` | 消費の場面を CPU の当て口(mock・古典)だけで 1 回通した記録 |
| `tests/tools/test_dm_eval.py` | 34 本を末尾に足した(既存の 41 本は変えていない) |

## 2. 場面の設計

### 2-1 共通の作り

- 店・品・人はすべて架空にした。店は「パン屋」「定食屋」のような種類の語だけで、固有の名を付けない。実在の店名・施設名・地名・人名・催しの名は使わない(漏洩の検査 段 1 の 4 と分けるため)。試験 `test_consumption_scenes_use_no_real_names` が禁止語の一覧で検査する。
- 値段は丸い仮の値で、50 円刻み(100〜5,000 円)。所持金は 100 円刻み。現実の値段の分布ではない。
- **判断に要る事実は短い版に入るブロックに置いた**(検収 高 1 (a))。DM4 の短い版(`port.compose`)は B6 だけを人ごとの部分として含むので、所持金・体・事情・直前の結果はすべて B6 に置き、B5 は使わない(`input_missing` は `["B5"]`)。長い版は短い版の末尾に指示の 1 行が付くだけになる。
  - B1 種別: 来街者・居住者・通勤者・従業者。
  - B2: 場所・可視・値札。値札は看板と同じく素性の印を付けた(`〔素性: 店頭表示・命令文除去済〕`)。routing #38 の「値段を買う前に見せる知覚」の代わり。
  - B3: 時刻・天候・体感。B4: 混み具合(店の外の場面は歩行者密度)・目につく出来事。B4b: 近景。
  - B6: 起床(判断の契機の文)・所持(所持金)・体(空腹・のどの渇き・疲れ・満腹)・事情(前に払った値段や事情=場面によって無し)・結果(判断点 4 だけ)・問い。`[B6 所持]`・`[B6 体]`・`[B6 事情]` の頭は engine の行テンプレ(`perception/templates.py`)の外の自前。
- 層(`strata`)の鍵は 1-10 と同じ heat・kind・scene・time_band・wake(検収 低 3)。time_band は 1-10 と同じ 4 時間の区切り(`00-03`…`20-23`)、scene は「店の中」か「店の前」、wake は「-1 消費の契機」。判断点と店の種類は `facts`(`decision_point`・`shop_kind`)にある。
- **語彙は v3**(検収 中 4)。待機は v3 で欠番なので使わず、続ける系の候補は「なし」にした。足した語は電車の「見送る」と字面がぶつからない名にし、見せ方の文の頭に routing §5 の語を置いた:

| 語(`Candidate.kind`) | 見せ方の文の頭(routing §5) | 判断点 |
|---|---|---|
| `buy_skip` | 見送る | 買うか見送るか・何をいくつ |
| `price_skip` | 値段を見て見送る | 値段を見て見送る |
| `revisit` | また行く | 満足して同じ店にまた行くか |
| `no_revisit` | また行かない | 同上 |

- 何をいくつは語ではなく、購入の候補の欄(`item`・`qty`・`price_yen`)で持つ(routing §5 の「欄」)。
- 候補は場面ごとに 6 つで、最後に「その他」(番号 7)が付く。PBS が 1 つの候補数で定義できるよう、数をそろえた。最後の候補はいつも「よく考える」(源 deliberate)。

### 2-2 判断点ごとの設計

| 判断点(`point`) | 件数 | 契機(B6 起床) | 候補 6 つ | 値段の置き方 |
|---|---|---|---|---|
| 買うか見送るか(`buy_or_skip`) | 11 | 棚の前で品を手に取った | 購入(品 1 つ)・`buy_skip`・なし(店を見て回る)・移動(別の店)・会話(店員に尋ねる)・よく考える | 値札 1 枚(150〜3,000 円)。所持金は値段の 1.6〜20 倍 |
| 何をいくつ(`what_how_many`) | 11 | 買う品の前に立った | 購入 品 A × 3 段の数(1/2/3・1/3/5・1/2/4・1/2/5・1/2/6)・購入 品 B × 1・`buy_skip`・よく考える | 値札 2 枚(1 つの値段)。数は候補の欄 `qty` |
| 値段を見て見送る(`price_skip`) | 11 | 値札を見た | 購入(値段どおり)・`price_skip`・購入(安いほうの品)・移動(別の店で探す)・なし(迷う)・よく考える | 高い品と安い品の 2 枚(差は 1.25〜15 倍)。B6 事情に前に払った値段(4 件)か事情(3 件) |
| 満足して同じ店にまた行くか(`revisit`) | 11 | 店を出た | `revisit`・`no_revisit`・会話(感想を伝える)・移動(次の行き先へ)・なし(店の前で休む)・よく考える | 値札なし。払った値段は B6 結果の文(300〜5,000 円) |

満足の手がかり(味・待ち時間・接客・品切れ・遠さ)は判断点 4 の B6 結果の文に入れた。良い点と悪い点の組み合わせは場面ごとに変えた(採点の正解としては使わない)。

### 2-3 候補の源(expedient・未リサーチ)

購入・移動・会話は「周りが示すできること」(affordance)、`buy_skip`・`price_skip`・なし と判断点 4 の移動は「続ける」(continue)、`revisit`/`no_revisit` は「本人の経験」(experience)、よく考えるは deliberate に置いた。どれも自前の割り当てで、DM-0 の 5 つの源の組み立て(`build_candidates`)は使っていない。

### 2-4 長さと数字の計器(CPU で測った)

| 腕/版 | 字数の中央(最小〜最大) | 目安を超えた件 | 時刻・お金の外の数字(中央/最大) |
|---|---|---|---|
| t300/short | 487.5(459〜553) | 44 / 44 | 1 / 3 |
| t300/long | 526.5(498〜592) | 44 / 44 | 1 / 3 |
| t1000/short | 700.5(672〜766) | 0 / 44 | 1 / 3 |
| t1000/long | 739.5(711〜805) | 0 / 44 | 1 / 3 |

時刻・お金の外の数字は、近景の「25メートル」と値札の「1つ」の「1」。t300 は B0 を外しても全件が目安(1 字 = 1 トークンの仮定・expedient)を超える。

## 3. 当て口の口(重みは取らない)

- **`ChoiceBackend`**(推論の形 Choice/Score): 文に続く候補の文字列の logprob を返す口。分布は `LogprobChoiceScorer` が `ChoiceForm` で作る(まとめた値の softmax・「その他」は番号 n+1)。
- **`FreeTextBackend`**(推論の形 Noul): 自由記述を返す口。`FreeTextScorer` が `match_free_text` で候補に当てる(§3-1)。
- **推論の形は差し替えられる**: 既定の 4 つは `choice_number`(番号の文字列の logprob の和)・`choice_number_first`(番号の 1 トークン目=R-83 §5 の (G) の形)・`score_text_sum`・`score_text_mean`(見せ方の文の和と平均)。候補ごとの形は答申 R-125 が決めるので、ここでは決めない。答えの頭の文・包み方(`plain`・`chatml_nothink`)・「その他」を入れるか・後ろに付ける文も、形の欄で変えられる。
- **読む文の版**: `--length short|long`(既定 short)で、(G)(`--vllm-*`)と候補(`--hf-*`)の両方の口が読む DM4 の版を選ぶ。
- **(a) `HFCausalChoiceScorer`**: transformers の causal LM。import は最初に使うときまで遅らせる(本体の venv には transformers も torch も無い)。手元の道筋だけを読み(`local_files_only=True`)、`trust_remote_code=False` と `use_safetensors=True` に固定する(安全の規則 2)。候補ごとに 1 回前向きに通し、まとめない。logits から logprob を出す計算は numpy の関数に分け、試験はそこを回す。
- **(b) `VLLMLogprobScorer`**: OpenAI 互換 `/v1/completions`。宛先は `127.0.0.1` に固定し、ほかの宛先は作るときに落とす(安全の規則 1)。API key は環境変数(既定 `DM_EVAL_VLLM_API_KEY`)から呼ぶたびに読み、`Authorization: Bearer` のヘッダにだけ載せる。記録・`describe`・例外の文には書かない。
  - 取り方の既定は `prompt_logprobs`(`prompt_logprobs=0`・各トークンの `decoded_token` の長さを**後ろから**引いて頭の位置を出す=末尾の候補の位置が前の日本語の文の切れ目に左右されない)。`echo`(`echo=true`・`text_offset`)は腕に下げた(検収 中 3)。
  - どちらも、切り出したトークンの文字列の連結が候補の文字列と同じかを先に確かめる。違えば `TokenBoundaryError` を投げ、破綻に数え、その場面は失敗として採点から外す(黙って別のトークンを使わない)。
  - 1 トークン目の形は `top_logprobs[0]` を使う(前後の空白を除いて同じトークンの logsumexp)。
- HTTP は指示の `urllib` ではなく、標準ライブラリの `http.client` で送る(親の確認 11-01 で可)。urllib の送り口の名には禁じた語(o-p-e-n)が入り、識別子の規則と両立しないため。宛先が固定の 1 本の接続なので、proxy の環境変数も通らない。試験は `http.client.HTTPConnection` を monkeypatch で偽の接続に替える。
- 重みは当て口の間で共有する。厳密モードの検査は当て口を作り直すが、重み(口の後ろ)は 1 回だけ読む。
- **失敗**(検収 低 4): モデルの口の後ろの例外(`BackendError`・`BackendUnavailable`・`TokenBoundaryError`=どれも `judge.ScoreFailed`)は場面ごとに捕まえ、`compare.scorers[名].failures[腕]`(数と最初の 20 件の状況の id・並び・型の名)に記録する。記録に残すのは型の名と短い分類(timeout・http・boundary・parse・unavailable・other)だけで、例外の文の本文は写さない(艦隊がエラーの文に入力を引き写す場合に備える=再検収 新 低 1)。その場面は採点から外し、全体は止めない。表の注に「失敗 N 場面」を書く。厳密モードと決定論の検査が落ちたときは、その当て口の欄を「失敗」(型の名と分類)にする。

### 3-1 自由記述の当て方(`match_free_text`・検収 中 2)

順に試す。

前処理: NFKC(全角を半角に)・助数詞(つ・個・本 など)の前の漢数字を数に(「二つ」→ 2 つ・「三個」→ 3 個。「一緒」「一番」は読まない)・数の後ろの「個」を「つ」と同じに読む(再検収 新 低 2)。

1. 後ろの行から、番号として読める 1〜n+1 の整数を探す。数字の後ろに単位・順位の語(円・個・つ・位・本・袋 など)が空白を挟んで続く物は番号に読まない(「クロワッサン 2 個」「1位は」は番号でない)。
2. **否定の答え**(再検収 新 中 1): 肯定の候補の動詞が答えの中で否定の形(〜ない・〜ません・〜なかった・〜ませんでした・〜ず・〜て(い)ない。「もう〜ない」を含む)で出ていて、ほかの肯定の候補には当たらないときは、肯定の候補には当てない。否定された候補の語に対応する否定の候補(購入 → `buy_skip`・`price_skip`、`revisit` → `no_revisit`)に当て、対応する否定の候補が無ければ**破綻**とする(例: 「もう来ない」「この店には来ないと思う」→ また行かない・「買いません」→ 見送る・「店員には尋ねない」→ 破綻)。「迷わずに安いほうを買います」のように別の肯定の候補にも当たる答えは、否定された候補を外して 3 で当てる。
3. 候補の見せ方の文を句に分け、句の末尾の動詞の当たりの形のどれかが答えにあれば当たりとする。肯定の動詞の当たりの形は丁寧語・過去・て形だけで、否定の形は入れない。否定の候補の文の動詞(「行かない」など)は否定の形(〜ません・〜なかった)で当てる。五段・一段・来る・する を扱う。句の内容の語(品の名・数など)が答えにある数だけ強くし、最も強い候補が 1 つだけのとき当てる(例: 「クロワッサンを2つ買います。」「クロワッサンを二つ買います」→ 2 つ買う・「別の店で探します」→ 別の店で探す・「また来ます」→ また行く(この店にまた来る)・「高いのでやめます」→ 値段を見て見送る(買わずにやめる))。
4. 語彙の語(「なし」と ASCII の名を除く)がちょうど 1 つの候補に当たる。
5. 「その他」の語。
6. どれにも当たらない=**破綻**。

## 4. 比べの列(表)

既存の 25 列(dm61 と同じ位置・同じ見出し)の後ろに、次の 9 列を足した(検収 低 1)。

| 指示の列 | 表の列 | 状態 |
|---|---|---|
| (推論の形) | `form`「推論の形」 | 規則・記録・Choice・Score・Noul。口だけの行は「GPU の後で埋める」 |
| 8B の logprob との一致(1 位の一致率・JSD) | `jsd_vs_g`(既存)・`top1_agree_vs_g`(新) | (G) の当て口(`--vllm-model` で作る `g_<モデル>`)があれば埋まる。今は「GPU の後で埋める」 |
| 決定論(同一入力 32 回の一致率) | `determinism_rate`・`determinism_repeats` | 埋まる(CPU の当て口は 1.0)。1 つの当て口で各件を続けて 32 回・まとめない |
| 日本語での破綻率 | `breakdown_rate` | 定義は下。規則の行は「該当なし(モデルの答えでない)」 |
| VRAM | `vram_gb` | 欄だけ。モデルの行は「GPU の後で埋める」、規則の行は「該当なし(GPU を使わない)」 |
| 何をいくつの数(検収 低 7) | `qty_mean`・`qty_agree_vs_g`・`qty_absdiff_vs_g` | 数を選ぶ場面(何をいくつの 11 件)だけ。1-10 の行は「該当なし(数の候補なし)」 |
| 分布の広がり | `entropy_mean`(既存「迷い エントロピー(平均)」) | 埋まる(脚注で対応を書いた) |
| 位置の偏り(巡回・PBS) | 既存の 5 列 | 埋まる |
| 1 判断の秒 | `wall_s_per_item`(既存) | 埋まる(GPU の当て口の行は注に「GPU の口の実測」) |

列の定義:

- **日本語での破綻率**:
  - Noul: 自由記述が、丁寧語と活用を正規化した後で(§3-1)、提示の候補にも「その他」にも当たらない率。
  - Choice/Score: 提示の候補(「その他」を含む)の文字列の確率の和(まとめる前の logprob の和の exp。1 トークン目の形は 1 トークン目の exp)が下限 1e-3 未満の件と、切り出しが字面と違った件を合わせた率(親の判断 11-01・下限は expedient)。
  - 分母は採点した呼の数(状況 × 並び)。
- **その他の率**: Noul の行では、明示の「その他」だけを数える。破綻の答えは分布では「その他」に確率 1 を置くが、この列の分子には入れない(破綻率と 2 回数えない=検収 低 5)。ほかの行は今までどおり(並び 0 の分布の「その他」の確率の平均)。
- **数の平均**: 場面ごとに、数の候補の中で数の期待値を分布で重みづけして出し、場面で平均した値。
- **数の一致率**: (G) の 1 位が数の候補の場面で、当て口の 1 位の数が同じ率(品は問わない)。
- **数の差の平均**: 期待値の差の絶対値の平均。

そのほか:

- 新しい列の値は比べの節 `compare` に置き、`compare_digest` を別に持つ。`digest` は `compare`・`scene_set`・`material` を含まないので、1-10 の記録の golden は変わらない(試験 `test_real_evalset_once_matches_recorded_golden` が通る)。`SCHEMA` は据え置き。
- 結果の欄 `scene_set`(cli の `--scenes`=evalset/consumption/both)と `material`(その結果の材料)で見分ける(検収 低 2)。
- `strict_check` は回数を引数 `repeats` で受ける(既定 2 は 1-10 の記録の形)。32 回の一致率は `determinism_check` が出す。
- 消費の場面にはテープ(8B の記録)が無いので、テープの当て口を外した。テープの列は「該当なし(基準の記録なし)」になる。古典の当て口は語彙 v3 で読む。
- 古典の当て口は、同じ語の候補が 2 つ以上あるとき(消費の場面の「購入」)、語の質量を id の順に等分する(検収 中 1)。提示の並びで分布は変わらない(試験で 44 件の全部を確認)。1-10 の材料は語が候補ごとに別なので値は今までと同じ。

## 5. CPU の記録(`consumption/`)

`python tools/instruments/dm_eval/cli.py run --scenes consumption --out-dir docs/bench/analysis/dm-eval-11-01/consumption` で書いた。digest `dfa07917133503ec1b87ccc404fdccd90f08403ba521c864aa68bddcbb60aad0`・compare_digest `b6749f75d7976dd4f8c5207c91b6e7c12f7bc99ceb063838bbfeac485101cacc`。試験 `test_cli_main_consumption` が digest を照らす。

| 当て口 | その他の率 | 1 位が変わる率 | エントロピーの平均 | 決定論(32 回) | 数の平均(何をいくつ) |
|---|---|---|---|---|---|
| mock(対照) | 0 | 0 | 1.445 | 1.0 | 2.27 |
| 古典(基準・語彙 v3) | 0.250 | 0 | 0.608 | 1.0 | 2.07 |

PBS の帰無の床(候補 6・44 件・巡回 4 通り・1 万回): 平均 0.039・5〜95% 0.007〜0.076。古典の当て口は足した語(`buy_skip` など)を「その他」に入れるので、基準としては弱い(限界に書いた)。

## 6. 空欄と GPU の後に埋める欄

- (G) との比べ(`jsd_vs_g`・`top1_agree_vs_g`・`qty_agree_vs_g`・`qty_absdiff_vs_g`)と、(G) の行の全部: 艦隊を立てて `--vllm-model` を付けた後。
- 候補の判断モデル(S1MB の 4B 以下)の行: 重みの取得(R-J)の後に `--hf-model` で。
- VRAM(`vram_gb`): 全部の行。測り方(`torch.cuda.max_memory_allocated` か `nvidia-smi`)は未定。
- 入力トークン(`tokens_in`)と 1 シム日あたりの GPU 時間: モデルの行。
- 決定論が無いときの「分岐と A/A に要る seed の本数」(`determinism_check` の `seeds_needed`): 式が未定。
- 日本語での破綻率: モデルの口が入った後。
- 人のデータとの照合: 検証側のまま(値を入れない)。住人の第一言語: 材料なし。

## 7. 使い方

```
# 1-10 の 340 件(今のまま)
python tools/instruments/dm_eval/cli.py run --out-dir <dir>
# 消費の場面だけ / 両方(<dir>/evalset と <dir>/consumption)
python tools/instruments/dm_eval/cli.py run --scenes consumption --out-dir <dir>
python tools/instruments/dm_eval/cli.py run --scenes both --out-dir <dir>
# GPU の後: (G)=127.0.0.1 の艦隊・候補=手元の重み・読む版は短い版(既定)か長い版
python tools/instruments/dm_eval/cli.py run --scenes both --out-dir <dir> --length short \
  --vllm-model <名> --vllm-port 8000 --vllm-mode prompt_logprobs --vllm-form choice_number \
  --hf-model <重みの道筋> --hf-form choice_number
```

## 8. 限界と expedient

- 場面・B0・判断の契機の文・B6 の自前の頭(所持・体・事情)・候補の源の割り当て・値段は自前(未リサーチ)。人の正解は無い。
- `match_free_text` の当て方と活用の表・否定の対応の表(`NEGATION_OF`)・漢数字の読み・破綻の下限 1e-3 は自前(下限は親の指示の値・原典なし)。
- `chatml_nothink` は Qwen3 の考えない形の頭を手で書いた物。tokenizer の chat template から作る形にするかは R-125 で決める。
- 番号の 1 トークン目の形は、候補が 10 以上の 340 件では「1」と「10〜14」の頭が重なる。消費の場面(番号 1〜7)では重ならない。
- vLLM の `decoded_token` と `text_offset` は文字の位置として読む。字面の確認で止めるが、実機の答えの形は未確認。
- (G) の要求は `temperature=0`・`seed=0`(expedient)。親の判断 11-01 のとおり、(G) は logprob の採点で生成ではないので、住民の LLM のランの「生成の設定は既定のまま」とは別に扱う。
- 長い版を Choice の形で読むと、末尾の指示「先に理由を自由に書き、最後に番号」と、直後の「答え: 」+番号の logprob が食い違う(検収 高 1 の注)。`--length long` はこの食い違いを含む腕として読む。
- 場面の正は jsonl と md5。`scenes/make_consumption_v1.py` は再現用(同じ入力で同じバイト)。

## 9. 検収(`review.md`)の指摘と直したこと

| 番号 | 直したこと |
|---|---|
| 高 1 | 所持金・体・事情を B6 に置き直した(全 44 件・B5 は使わない)。`--length short|long` を足し、(G) と候補の両方に効かせた。冒頭の注と限界に「DM4 の短い版に状態の欄を足す(src 側)は段 3 の問い=親」「直すまで (G) との一致を選定の根拠にしない」を書いた |
| 中 1 | 古典の当て口が、同じ語の候補に質量を id の順で等分するようにした。並びで変わらないことを試験で確かめ、1-10 の golden も不変 |
| 中 2 | `match_free_text` を作り直した(活用の正規化・空白入りの数と順位を番号に読まない)。破綻率の定義を §4 に書いた |
| 中 3 | vLLM の既定を `prompt_logprobs` にし、`echo` は腕に下げた。切り出しの前に字面を確かめ、違えば破綻に数える |
| 中 4 | 場面を語彙 v3 で書き直した(待機 → なし)。足した語を `buy_skip`・`price_skip`・`revisit`・`no_revisit` にし、見せ方の文の頭は routing §5 の語のまま |
| 低 1 | 壁時計の列の見出しを元に戻し、新しい列は表の末尾に置いた |
| 低 2 | 結果の欄 `scene_set` と `material` を足した(digest の外・SCHEMA は据え置き) |
| 低 3 | `strata` の鍵と time_band の区切りを 1-10 と同じにした |
| 低 4 | 口の後ろの例外を場面ごとに捕まえて記録し、全体は止めない |
| 低 5 | Noul の行の「その他の率」から破綻の答えを外した |
| 低 6 | 場面の行の鍵 `"tick"` を外した(読み口は既定の -1 で読む) |
| 低 7 | 何をいくつの数の列(数の平均・(G) との数の一致率と差の平均)を足した |
| 問い 4 | logprob の形の破綻=候補の確率の和が 1e-3 未満(と字面の不一致)。定義を §4 に書いた |
| 問い 5 | `temperature=0`・`seed=0` は (G) の採点の expedient として §8 に書いた |

再検収(`review.md` §再検収)の指摘:

| 番号 | 直したこと |
|---|---|
| 新 中 1 | 肯定の候補の当たりの形から否定の形を外した。否定の答えは対応する否定の候補に当て、無ければ破綻(§3-1 の 2・3) |
| 新 低 1 | 失敗の記録の `message` を、例外の文から短い分類(timeout・http・boundary・parse・unavailable・other)に替えた。HTTP の例外の文にも艦隊の答えの本文を入れない |
| 新 低 2 | 助数詞の前の漢数字を数に読む(§3-1 の前処理) |
