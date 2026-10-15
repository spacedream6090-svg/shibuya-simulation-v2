# 第 3 期 3-3b 反実仮想の器の残りの実装の記録

- 実装役 Opus 5.5。作業木の枝 `3-3b/counterfactual-rest`(土台 `0239a3b`=3-5 の取り込みの後 → 独立検収の後に本体 `76d3899`=3-1・6-1 の取り込みの後へ rebase・§15)。commit は親。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-5(CP5-1〜CP5-6・CP12・CP14・探索と確認・複数ランの作り方)・§2 の 3(未来は分布)・PENDING 仮-20・**仮-24**(親の判断=答申 R-117 の扱い)・[答申 R-117](../../../../research/v2-r117-e2-counterfactual-ensemble-warmup-precedents.md) §1・§2・§3・§4-6・§5・§6-1・[答申 R-71](../../../../research/v2-r71-stochastic-comparison-statistics.md)(4 つの確認・最低 6 対)・3-3 の記録 [cf33](../cf33/README.md)・3-2 の記録 [tm32](../tm32/README.md)(窓の待ち行列)・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(新しい問いは既定 off の腕で仮採用)。
- 数は実測。生の出力(テープ・状態のファイル・side の JSON)は作業木の `_bc/`(git の外・取り込みの前に消す)。検収の後の直しと rebase の scratch は `_bc2/`(終わったら中身を消した・§15)。比べた結果と道具だけをこのフォルダに置く。道具は `tools/switch_example.py`(§2 の分岐の例)・`tools/two_day_resume.py`(§8 の 2 日と再開)。byte-check は既存の `10e/byte_check_10e.py`。

## 0. 結論

- **T からの切り替えの口(CP5-2 の完成)**: `engine/experiment/switch.py` の `ReplaySwitch`(3-3 の `BranchClient` の上)。T までは基準のランのテープを再生して LLM を呼ばず、T からだけ仮のモデル(mock・古典=ランの口、または注入した口)が答える。**T は計算のまとめの窓の頭**(3-2 の窓の待ち行列=ランの始めから幅 W ずつ・W は基準の manifest の `batching.width_s`)でなければ止める。刻みの外へ物を持ち越さない**守りの本体**は、テープに T をまたいで届く行(艦隊で録った到着待ちの行=状態台帳 O96 `run_day.replay_inbox` に残る物)があれば切り替えを拒むこと。口の中の**箱の計器**(今の刻みに再生した答えの文だけ・刻みが替わると空にする)は空にしてから数えるので刻みをまたいで残った数と切り替えの刻みに残っていた数は**作りから 0**=空にする処理の退化を捕まえる計器で、(b) はこの 2 つが 0 であることも条件にした(〔検収 L1〕§2)。`run_branch` は既定でこの口を通る(3-3 の欄はそのまま・足しただけ)。
- **(d) の分け(仮-24)**: 「決定論の確認」(`d_determinism`=mock・古典では A/A の枝 2 本が厳密に同じ・T からの口がランの口そのものなら A/A の final=基準)と「床の分布」(`d_floor`=T 以後の A/A の枝 2 本の差・各メンバーの対を `ensemble.floor_values`/`floor_summary` に並べると分布)。非決定の口は厳密一致を求めず T より前の一致だけ。注入した口は属性 `deterministic`(真偽)で決定論を宣言でき、宣言があれば決定論の確認をかける(宣言の無い注入の口は非決定のまま=〔検収 L2〕§3)。**(c)** に A/A の枝 2 本の最初の食い違いと改変の枝の最初の食い違いの刻みの差(`vs_aa`)を足した。
- **CP5-1**: 始まり 0 で改変があり告知が無い(または申込書に `unexpected: true`)ものは警告(`ExperimentWarning`)と記録(manifest の `experiment.start0`)。拒まない。「最初から」の順番は宣言と欄だけ(`order_implemented=false`=4-1 段 6 の後)。
- **CP5-3**: 申込書に自己申告の欄 `known_to_model`(LLM が実在の出来事として知っている改変の語・空でよい)を足し、名指しの機械の検査と同じ 1 つの道具(`checks.naming_hits`)でペルソナの文の名指しと混入の疑いを探す口を作った(ランの中では走らない=呼び手が文を渡す)。
- **CP5-6 慣らしの器**: `tools/instruments/warmup_gauge.py`(読むだけ・記録に JSON)。MSER(1 バッチ=1 シム日)を**差の系列**に当てる(問い 1=開始日から − k 日前から慣れたラン・問い 2=改変の枝 − A/A の枝)。規則と parameter は `engine/experiment/warmup.py` の `RULE`(**事前登録=日付ではなく規則**・manifest の `experiment.warmup` と事前登録の記録に同じ記録)。合成の系列で、植えた日数に当たる・後半の無効と延長・未収束・累積の負の対照・差の系列 vs 原系列の腕を確かめた(§5)。ランの頭からの累計(会話の始まり)は累計の印で日ごとの差に直し、印の無い累計は拒む(〔検収 M1〕)。慣らしの日数は系列の頭の日から数える(在庫と累計は d* + 1=〔検収 L3〕)。
- **技量スコアの隣の生の点数(CP14)**: 器(`ensemble.skill_container`)に `raw`(fair CRPS・基準の CRPS・rank histogram・広がりと誤差の比=√((M+1)/M) の補正)の欄を足し、計器 `tools/instruments/skill_gauge.py` が埋める。事前登録の記録に封印の証拠の欄(手元の git+公開リポへの push・値は空)。
- **HM の直接判定の器**: `tools/instruments/hm_gauge.py`(候補は離散の seed の組だけ・較正側の観測だけ・閾値 3・2 番目に大きい値)。器だけ(候補の初期状態は 4-1 の後)。
- **使わないとき不変**: 申込書を渡さないランは byte-check **19/19 構成で 25 欄とも HEAD と同じ**(§8)。2 日のラン(5,000 体)は HEAD と final・呼数・全 checkpoint が同じ・1 日目の終わりで止めて再開=通し(HEAD と作業木の両方・§8)。
- 試験: 新規 45 本(`tests/engine/experiment/test_cf33b_*.py` 29・`test_x33_branch.py` に 1・`tests/tools/test_{warmup,skill,hm}_gauge.py` 15)。範囲の試験 1,919 passed+子のプロセスの落ち 1(単独で回し直して通った)・slow の 5,000 体の分岐 1 passed・`lint-imports` 5 契約 KEPT(§9)。〔検収の後・rebase の後〕新規 +10 本=55 本・発注の範囲の試験 682 passed・failed 0(c8 の 186 を含む・11 分 12 秒)・byte-check 1 構成 final 同じ(§15)。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/experiment/switch.py`(新) | `SwitchSpec`(`BranchSpec` に T の時刻・窓の幅・刻みの幅・仮のモデルの札・決定論の宣言・T からの口を作る関数 `live` を足した形)・`ReplaySwitch`(T からの切り替えの口・再生の箱)・`window_head_step`・`tape_crossing`・`model_label`・`is_deterministic`・`vs_aa`・`determinism`・`DETERMINISTIC_MODELS`(mock・古典) |
| `src/shibuya/engine/experiment/checks.py`(新) | CP5-1 `start0_check`・`warn_start0`・`ExperimentWarning`/CP5-3 `naming_hits`(1 つの道具)・`persona_naming`・`contamination` |
| `src/shibuya/engine/experiment/warmup.py`(新) | 慣らしの判定の規則 `RULE`・印 `MARKS`(mechanism/expedient/未リサーチ)・`rule_record`・`rule_sha256` |
| `src/shibuya/engine/experiment/form.py` | 省略できる欄 `OPTIONAL_FIELDS=("unexpected", "known_to_model")`(既定のときは正準の形に書かない=3-3 の申込書の指紋は変わらない) |
| `src/shibuya/engine/experiment/branch.py` | `BranchSpec.make_client`(3-3 の形)・`run_branch` は `SwitchSpec` で回す(引数 `model`・`live`・`deterministic` を足した)・T の窓の頭の検査とテープの到着待ちの行の検査を回す前に・(b) に A/A の枝 b(`aa_b`)と再生の箱(`box_left`)・(c) に `aa_coarse`・`vs_aa`・(d) に `d_determinism`・`d_floor`・summary に `model`・`deterministic`・`c_aa_step`・`c_gap_steps`・`d_floor_zero`・報告に `switch`。summary の `d` は `d_determinism.ok`(決定論の札でランの口そのもの=3-3 と同じ値) |
| `src/shibuya/engine/experiment/layer.py` | 組み立ては `st.branch.make_client(bridge.client)` で包む・CP5-1 の点検(警告と記録)・`MANIFEST_CONFIG` の末尾に 4 欄(`switch`・`start0`・`known_to_model`・`warmup`) |
| `src/shibuya/engine/experiment/ensemble.py` | 技量スコアの器の隣の生の点数の欄 `raw`・`RAW_SCORES`・事前登録の記録の `evidence`(`evidence_container`)と `warmup`・床の分布 `floor_values`・`floor_summary` |
| `src/shibuya/engine/experiment/__init__.py` | 置き場の説明に 3 つのモジュール |
| `src/shibuya/engine/manifest_sections.py` | `experiment` の設定の子の末尾に 4 つ |
| `tools/instruments/warmup_gauge.py`(新) | 慣らしの判定の器(§5) |
| `tools/instruments/skill_gauge.py`(新) | 技量スコアの隣の生の点数(§6) |
| `tools/instruments/hm_gauge.py`(新) | HM の直接判定の器(§7) |
| `docs/design/bridging-ledger.json` | 末尾に 9 行(§11) |
| `tests/engine/test_env_and_sections_10f.py` | `CONFIG_PATHS_SHA256` を計算し直した(凍結の表=増えた分だけ) |
| `tests/engine/experiment/`・`tests/tools/` | §9 |

## 2. T からの切り替えの形(再生 → 仮のモデル)

| 時刻 | 答える口 | 確かめ |
|---|---|---|
| T より前・状態を持たない口(mock・注入した口) | テープの完全一致(`Replay.lookup`)=LLM を呼ばない。テープ外は数えて空の応答(3-3 と同じ) | (b) テープ外 0 |
| T より前・古典の方策(内部の状態を持つ) | 方策に答えさせて状態を進め、テープの答えとの食い違いを数える(3-3 と同じ) | (b) 食い違い 0 |
| T から | 仮のモデル=`SwitchSpec.live` が無ければランの口そのもの(mock・古典)・あれば `live(ランの口)` | (c)(d) |

- **T は窓の頭**: `window_head_step(T, W, 刻み)`。窓の頭はランの始め(通しの 0)から W ずつ(3-2 の `WindowQueue`)。窓の頭でなければ `ValueError`。T1 の世界の事象は刻みの事象だけ(刻みの頭=いつも窓の頭)なので、W < 刻みの幅のとき刻みの途中の窓の頭も受け、切り替わるのは T 以後の最初の刻み(`ExperimentForm.start_step` の切り上げと同じ)。W は基準のランの manifest の `batching.width_s`(無ければ刻みの幅)。〔親の判断 5〕3-3 では刻みの頭でない T を切り上げて受けていた=3-3b で止める形に変えた(申込書の T を黙って丸めない・CLI の `--experiment-branch` の help にも書いた)。
- **守りの本体=到着待ちの行を拒む**: テープの行のうち T より前に出して後で届く行(`deferred` か `observed_tick` ≥ 0)が 1 行でもあれば、`run_branch` が回す前に止める(`ReplaySwitch` も組み立てで止める)。同期の答えでは基準の到着の時刻を作れず、T をまたぐ行はプロジェクトの語の「再生の箱」=再生の到着待ち(状態台帳 O96 `run_day.replay_inbox`)に残る。分岐のランでは橋は口の道を通る(`observed_tick`=−1)ので O96 に物は入らない(作りから空)。艦隊の分岐は 6-7(`DOC-cf33-branch-fleet`)。〔検収 L1〕O96 を T の刻みで読む口は無い(系 `experiment` の読む欄は系の表で `layers.experiment` だけ・系の表はこの段の範囲の外)ので、(b) の条件に O96 は入れていない=**(b) の本体は艦隊のテープの到着待ちの行を拒む守り**(宣言)。
- **口の中の箱の計器**: `ReplaySwitch._box` は今の刻みに再生した答え(鍵 → 文の文字列)だけ。刻みが替わる最初の呼で空にする(`_box_reset`)。計器 `box_carried`(刻みをまたいで残った数)・`box_at_switch`(切り替えの刻みに残っていた数)・`box_peak`・`box_repeats`。〔検収 L1〕`box_carried` と `box_at_switch` は空にしてから数えるので**作りから 0**(箱はどこからも読まれない=答えはテープか仮のモデルが返す)。空にする処理の退化を捕まえる計器で、(b) は `box_left = box_carried + box_at_switch = 0` も条件にした(負の対照=空にしない写しは口の単体でも合成の世界の分岐でも (b) が落ちる・ランの動きは変わらない)。箱は文字列だけで、`Percept` のような刻みの中の物は持たない(1-2 の検収 M1 の教訓)。計器の数は読み取り専用の属性(〔検収 L8〕外からの代入は `AttributeError`=3-3 の `BranchClient` の再生の数も同じ)。
- 保存の間隔は日の境目のまま(変えていない)。
- manifest: 設定 `experiment.switch`(形式・T の時刻と刻み・窓の幅・刻みの幅・札・決定論か・T からの口がランの口そのものか)・観測 `experiment.replay` に計器(札・決定論か・箱の 4 つ・最初に仮のモデルが答えた刻み・到着待ちの行の数)を足した(3-3 の欄はそのまま)。

**分岐の例**(世界資産 1,000 体・seed 1・2 日・語彙 v3・checkpoint 60 刻み・T0=2 日目の正午・200 店の休業=cf33 §4 と同じ申込書・道具 `tools/switch_example.py`・[switch_example.json](switch_example.json)):

| | mock(T からの口=ランの口) | 非決定の口(作るたびに種の違う mock・札 `llm_stand_in`) |
|---|---|---|
| summary | a・b・d・ok が真・札 mock・決定論・床 0 | a・b・d・ok が真・札 `llm_stand_in`・非決定・床 0 でない |
| (b) | 3 本(A/A の枝 a・b・改変の枝)とも T より前の checkpoint 12 本が基準と同じ・テープ外 0・箱 0 | 同じ |
| 再生の計器(改変の枝) | テープから答えた呼 5,190・T から仮のモデル 8,502・箱の最大 358・刻みをまたいで残った数 0・切り替えの刻みに残っていた数 0・最初に仮のモデルが答えた刻み 2,160 | テープから 5,190・T から 8,381・箱は同じく 0 |
| (c) | 粗い比べ=刻み 2,219・世界=刻み 2,160・系 `world`・欄 `pois.open_now`・`O73:runner.opening.n_events`・`n_fallback`(3-3 と同じ)。A/A の枝 2 本は食い違わない=`vs_aa` は「床 0=改変の枝の食い違いは床の外」 | 粗い比べ=2,219・世界=2,160・系 `world`(同じ欄)。A/A の枝 2 本も 2,219 で食い違う=刻みの差 0(「床に埋もれる」=checkpoint の粒度の比べ) |
| (d-1) 決定論の確認 | A/A が厳密に同じ・A/A の final=基準 `425c22a3…`=通る | 厳密一致は求めない・T より前に A/A の枝 2 本が同じ=通る(A/A の final は `286162d3…` と `3353f2f8…`) |
| (d-2) 床 | T 以後の checkpoint 12 本で違い 0・呼数の差 0 | T 以後の checkpoint 12 本が全部違う(最初 2,219)・呼数の差 −5(1 対) |
| 呼数(A/A → 改変) | 13,633 → 13,692 | 13,549・13,544 → 13,571 |
| 壁時計 | 基準 29.3 秒・分岐の 4 本 146.2 秒 | 分岐の 4 本 164.0 秒 |

- 1,000 体の世界資産は担当の従業者が 0 人=休業の開け閉めは全部つなぎ(`executed_by_agents` は偽=3-3 と同じ・6-6 まで宣言)。
- 壁時計は 2 日のラン 2 本(HEAD と作業木の 5,000 体)と並べて回した値。

## 3. 4 つの確認の (c)(d) の分け(仮-24)

| 確認 | 3-3 の欄(そのまま) | 3-3b で足した欄 | 合格の条件 |
|---|---|---|---|
| (a) 入力の一致 | `a_input_match` | — | 3-3 と同じ(`experiment.*` は腕の欄) |
| (b) T より前の一致 | `b_pre_t0.aa`・`branch`・`resume_state` | `b_pre_t0.aa_b`(A/A の枝 b)・各行の `box_left` | 全部同じ・テープ外 0・古典の食い違い 0・箱 0 |
| (c) 最初の食い違い | `coarse`・`world`・`any`・窓 | `aa_coarse`(A/A の枝 2 本の粗い比べ)・`vs_aa`(A/A の最初 − 改変の枝の最初の刻みの差 `gap_steps` と読み) | 報告(合否なし) |
| (d-1) 決定論の確認 | `d_aa`(A/A 2 本と final・final=基準) | `d_determinism`(札・決定論か・A/A が厳密に同じか・final=基準か・それぞれ求めるか) | 決定論の札: A/A が厳密に同じ(T からの口がランの口そのものなら final=基準も)/非決定: T より前に A/A の枝 2 本が同じ |
| (d-2) 床の分布 | — | `d_floor`(指標ごとの A/A の差 b − a の要約・T 以後の checkpoint で behavior が違う数・最初の刻み・床 0 か) | 報告(合否なし)。アンサンブルの各メンバーの対を並べて分布 |

- summary の `ok` は (a)・(b)・(d-1) が通ること(3-3 と同じ形)。`d` は `d_determinism.ok`。決定論の札(mock・古典)でランの口そのものなら 3-3 の `d` と同じ値。
- 決定論の札は `DETERMINISTIC_MODELS=("mock", "classical")`(未リサーチ=expedient)。宣言(`deterministic=`)で上書きできる。
- 〔検収 L2・親の判断 2〕決定論かを決める順: ① `run_branch` の引数 `deterministic`(指定)② **注入した口の宣言**(属性 `deterministic` が真偽の値のときだけ=試験の stub などの決定論の口が自分で宣言する)③ 札。宣言があれば (d-1) の厳密一致を求める(宣言した決定論の口は A/A が厳密に同じで通る・宣言したのに実は非決定の口は (d) が落ちる=負の対照)。宣言の無い注入の口は非決定のまま(既定は変えない)。どれで決めたかは manifest の `experiment.switch.deterministic_by`(`spec`・`port`・`label`)に書く。

## 4. CP5-1 の点検・CP5-3 の混入の欄

- **CP5-1**(`checks.start0_check`): 旗=始まり 0・改変がある・(告知が無い か `unexpected: true`)。組み立て(`make_layer`)が `warn_start0` で `ExperimentWarning` を出し、manifest の `experiment.start0`(旗・理由・規則の文・「最初から」の順番の文・`order_implemented=false`)に記録する。**拒まない**(ランは回る=試験)。途中から(T0 > 0)の `unexpected: true`・告知のある予期した改変・A/A は旗を立てない。
- **CP5-3**(`checks`): 名指しの機械の検査は部分一致の 1 つの道具 `naming_hits(文, 名の列)`(名は呼び手が渡す=コードに地名や業種名を書かない)。`persona_naming(ペルソナの文, 改変した物の名)`=CP5-3 の名指し・`contamination(申込書, 文)`=自己申告の語 `known_to_model` が文に出るか(混入の疑い)。申込書の欄は省略でき、空なら正準の形に書かない。manifest の `experiment.known_to_model` に写す。ランの中では走らない(ペルソナの文は 4-1 の後に組み立てで渡す=`DOC-cf33b-persona-check-caller`)。

| 申込書の欄(3-3b) | 型 | 既定 | 正準の形 |
|---|---|---|---|
| `unexpected` | 真偽 | `null`(書かない) | 既定でないときだけ末尾に |
| `known_to_model` | 空でない文の列(昇順・重なりは 1 つ) | 空(書かない) | 空でないときだけ末尾に |

## 5. 慣らしの器(CP5-6)の規則と parameter(事前登録の形)・合成の試験

**事前登録の形**: 規則と parameter は `engine/experiment/warmup.py` の `RULE`(読み取り専用)と印 `MARKS`。manifest の `experiment.warmup`(申込書つきのランは全部)と事前登録の記録(`ensemble.preregister` の `warmup`)に `rule_record()`(規則・印・指紋 `rule_sha256`・判定の道具の名・`registered=rule_not_dates`)を写す。計器は規則をエンジンの側の 1 か所から読み、出力に `rule_sha256` と指標の表の指紋 `metrics_sha256` を書く。日付は登録しない。

| 項 | 値 | 印 |
|---|---|---|
| 方法 | MSER(n, d) = Σ_{i>d}(y_i − Ȳ(n,d))² / (n − d)²・d* = argmin(同点は小さい d) | mechanism |
| 系列 | 差の系列(本則)・原系列(感度の腕+宣言=暦と天気で動き続ける) | expedient |
| まとめ | 1 バッチ=1 シム日 | expedient |
| 候補 | d ≤ n − 5 | mechanism(出所は親未確認=△) |
| 候補の数え方(宣言) | 〔親の判断 4〕d ≤ n − 5 のまま。R-117 §4-4 の記述では pymser は候補を n − 3 番目まで(=最後の 2 つを除く)とする。同じ数え方なら「最後の 5 つを除く」は d ≤ n − 6 になり、**1 つずれる**(pymser のコードは読んでいない=R-117 の記述による・規則の項 `exclude_last_counting`) | 未リサーチ |
| 無効 | d* > n/2 → 10% 延ばす(切り上げ・最低 1 日)・延ばす先のデータが無ければ「要延長」・3 回無効で「未収束」 | 後半=mechanism・最低 1 日と 3 回=expedient |
| 複数本 | 本ごとの差を日ごとに平均してから当てる。問い 1 は 5 本・問い 2 は 6 対(足りなければ `pairs_enough=false`) | 平均=mechanism・5 本=expedient・6 対=R-71 |
| 束ね | W=有効だった指標の慣らしの日数の最大・測る期間 W 以上・全体 2W 以上 | 最大=expedient・W と 2W=mechanism |
| 慣らしの日数 | 〔検収 L3〕系列の頭の日(直す前の系列の最初の日・問い 2 は実行の日)から数えた日数=最初の日 + d* − 頭の日(在庫と累計は流量に直すと最初の日が落ちるので d* + 1)・規則の項 `warmup_days` | mechanism |
| 累積 | 使わない(`kind: cumulative` は `ValueError`) | mechanism |
| 累計 | 〔検収 M1〕ランの頭からの累計(md23 の probe の `conv.opened`・`conv.closed`・`conv.joined`=`CUMULATIVE_PATHS`)は累計の印(`kind: counter`)を付けて日ごとの差に直す。印の無い累計の道筋は `ValueError`(流量・在庫と宣言しても)。最初の記録の日は落とす(累計は再開で引き継ぐ=状態台帳 O91・記録の頭が 0 とは限らない) | 直す・拒む=mechanism・最初の日を落とす=expedient |
| 在庫 | 流量に直す(総流量の欄が無い間は日ごとの差=純流量) | 直す=mechanism・純流量=expedient |
| 月の周期 | 慣らしの対象から外し推移の指標(系列だけ報告) | expedient |
| 最低の日数 | 7 日 | 未リサーチ |
| 問い 1 の先行 | 28 日 | expedient |
| 問い 2 の区間 | 構え=告知の日〜実行の日・切り替わり=実行の日〜実行の日 + d*・新しい日常=その後〜終わり | 決定 10-12 CP5-6 |

- 〔検収 L5〕`RULE` の全部の項に印がある(初めの版は `statistic`・`q1.series`・`q2.series`・`q2.bounds` に印が無かった=式の文 mechanism・問いごとの系列の名 expedient・区間の境 mechanism を足した・試験 `test_every_rule_item_has_a_mark` が `RULE` の葉の項と `MARKS` の鍵を突き合わせる)。問い 2 の `fine_steps: 15`(刻みの数で 15 分を書いた直書き・計算に使っていない)は消した。
- MSER の式は原典(White 1997・Franklin & White 2008・Hoad & Robinson 2011=R-117 §4-1)から書いた。pymser(BSD-3)は写していない(候補の範囲・小さい値の置き換え・75% の警告が Hoad の作法と違う=R-117 §4-4)・依存も増やしていない。

**指標の表**(計器の側 `METRICS`・CA8 の一覧に流量の欄を足した・道筋は 2-3 の md23 の道具のランの記録の形):

| 速さ | 指標 | 道筋 | 種類 |
|---|---|---|---|
| 速い | 外出(到着の数の代わり)・訪問(店で払った行の代わり)・呼数 | `gauge.arrivals_n`・`daily.stage2.payment.cash_rows`・`daily.llm_calls` | 流量 |
| 速い | 会話の始まり | `probe.conv.opened`(`ConversationManager.n_opened`=ランの頭からの累計) | 累計 → 日ごとの差(〔検収 M1〕初めの版は流量と誤って宣言していた) |
| 速い | 食事の回数 | 置き場(null) | 流量 |
| 遅い | 新しく結んだ約束・グループ | 置き場 | 流量・在庫 |
| 遅い | 知り合いの数・生きている関係の辺 | `probe.relations.acquaintance_edges`・`probe.relations.edges_live` | 在庫 → 流量 |
| 遅い | 新しく知った数・忘れた数 | 置き場(**計器の側に足す欄**=総流量) | 流量 |
| 推移 | 給料・所持金の合計 | `daily.stage2.wages.amount`・`probe.money.cash_total` | 月の周期=判定しない |

**合成の系列の試験の結果**(`tests/tools/test_warmup_gauge.py`・決まった種):

| 確かめ | 結果 |
|---|---|
| 植えた慣らし(7 日・偏り 3.0・雑音 0.5・5 本の平均・40 日) | 種 1 で d*=7(有効)。300 種で d* が 7 を下回ったのは 0・ちょうど 7 は 182/300(60.7%)・中央値 7・90 分位 19(MSER は長めに出ることがある=Hoad ら 2008)。1 本だけに当てると 164/300(54.7%)=平均してから当てるほうが当たる |
| 後半の無効と延長 | 12 日の慣らし・初めの長さ 20 日 → n=20 で d*=12(無効)→ 22 で 16(無効)→ 25 で 12(有効)(〔検収 L4〕初めの版は「22 で 12」と誤記)。下がり続ける系列は 3 回無効で「未収束」。延ばす先のデータが無ければ「要延長」(必要な長さ 22) |
| 累積の負の対照 | 偏りの無い系列(60 日)で、累積の平均に当てると打ち切り点が後半に出たのは 50 種中 42、原系列は 2(Hoad & Robinson 2011 の「累積は使わない」の理由)。指標の `kind: cumulative` は拒む |
| 差の系列 vs 原系列の腕 | 週の周期と天気(A と B に共通)+ A だけの慣らし 7 日・5 本・28 日の先行: 差の系列は種 0 で d*=7・40 種中 27 で 7。原系列の腕は 40 種中 0(d*=0・2・3・4=週の周期と天気に紛れる) |
| 在庫と推移と置き場 | 在庫は日ごとの差に直す(最初の日が落ちる)・月の周期の指標は推移の指標(判定しない)・置き場の指標は null・束ね W=有効な指標の慣らしの日数の最大(在庫 4 日ふえる=d* 4・慣らしの日数 5・W 5) |
| 累計(〔検収 M1〕) | md23 の形(5 対・先行 28 日・1 日 20 件+慣らし 7 日に 6 件多い・累計の `conv.opened`): 累計の印で日ごとの差に直すと種 0 で最初の日 1・d* 6・慣らしの日数 7(有効)・40 種中 22 で 7・7 を下回る種 0。負の対照(道筋の名を変えて守りを外し、印の無い累計を流量として当てた写し)は 40 種中 1 だけ 7・26 が「要延長」。印の無い累計の道筋(流量・在庫と宣言)は `ValueError` |
| 在庫の慣らしの日数(〔検収 L3〕) | 6 日ふえる在庫(1〜6 日目に 1 日 5・7 日目から定常・流量に雑音・5 対): 最初の日 1・d* 6・慣らしの日数 7・W 7(前の束ね=d* の最大なら 6=1 日短い) |
| 問い 2 | 実行の日 10・告知の日 8・切り替わり 5 日を植えた 6 対 → d*=5・区間 構え [8, 10]・切り替わり [10, 15]・新しい日常 [15, 終わり] |

- 入力は md23 の道具のランの記録の形(`daily`・`probe`・`gauge` の日ごとの行)。無い列はデータ無し(落ちない)。実際のランの対(開始日のランと慣れたラン・改変の枝と A/A の枝の 6 対以上)は本段では回していない(§12)。

## 6. 技量スコアの隣の生の点数・封印の証拠(CP14)

- 器(`ensemble.skill_container`): 3-3 の欄(`error`・`baseline_error`・`skill`)の隣に `raw`(`crps_fair`・`baseline_crps`(点の予測=絶対誤差)・`rank_histogram`・`spread_skill`・`members`)と `raw_scores`・`error_measure="crps"`・`spread_skill_correction="sqrt((M + 1) / M)"`・`raw_note`(技量スコアは proper でない=優劣は生の点数で決める=Gneiting & Raftery 2007 の式 (8) の注意)。値は空。
- 計器 `tools/instruments/skill_gauge.py`: fair CRPS=(1/M)Σ|x_i − y| − 1/(2M(M−1))ΣΣ|x_i − x_j|(scoringrules の `estimator="fair"` と同じ式・コードは写していない)・通常の CRPS も並べる・点の予測は絶対誤差・技量スコア=1 − fair CRPS/基準の CRPS(`ensemble.skill_score`)・rank histogram(同じ値は seed つきの乱数で割る)・広がりと誤差の比=√((M+1)/M)·広がり/RMSE(Fortin ら 2014 の式 15)。`fill` が器を埋める(元の器は変えない)。〔検収 L7〕入力の道筋に読む守り(`read_guard.deny_hit`=慣らしと HM の計器と同じ線=較正側だけ・封印と検証側の語は開く前に落とす)。答え合わせの段(第 7 期)で検証側の観測を読む線はその段で決める。
- 既知の値の試験: [1, 2, 3] と観測 2 の fair CRPS 0・通常 2/9・[0, 0] と観測 1 は 1・広がりと誤差の比は手で計算した値。mock のアンサンブル(合成の世界 20 体 600 刻み・偶然の seed 5 本+観測の代わり 1 本の呼数)で点数が出る(rank histogram は 6 つの枠に 1・メンバーの値が動く)。
- **封印の証拠**(仮-24): 事前登録の記録に `evidence`(`kind="git+push"`・`git_commit`・`pushed_to`・`pushed_at`=値は空=公開する呼び手が埋める・`third_party_timestamp=false`)。ランの manifest の `git_commit`・`git_dirty`・`git_diff_sha256` は今の形のまま。

## 7. HM の直接判定の器

- `tools/instruments/hm_gauge.py`: I_k = |z_k − Ē_k| / √(Var_ens,k + Var_obs,k + Var_disc,k)(代理モデル無し=候補ごとの複数本の平均と標本分散・1 本は Var_ens=0)・束ねは 2 つ以上なら 2 番目に大きい値(mogp-emulator の既定)・1 つなら最大・閾値 3。残りが空なら警告(Vernon ら)。コードは写していない(式から書いた)。
- 守り: 候補の欄は `population_seed`・`environment_seed` だけ(係数の欄・整数でない値は `ValueError`)・観測は `side: "calibration"` だけ(検証側は `PermissionError`)・入力の道筋に封印と検証側の語(`read_guard.GAUGE_DENY_TOKENS`)があれば開く前に落とす(〔検収 M2〕照らすのは `read_guard.deny_hit`=小文字にそろえた生の道筋と、当たらなければ実体の道筋=つなぎ・symlink を解いた形。初めの版は渡した文字列そのままを大文字小文字を区別して照らしていたので、大文字の形と名に語を含まないつなぎが抜けた=慣らしの計器も同じ)。
- 試験は合成の値だけ(式・束ね・閾値・負の対照 4 形・CLI)。候補の初期状態は 4-1 の後(`DOC-cf33b-hm-container`)。

## 8. 結果不変(byte-check・2 日・再開)

- **byte-check 19/19 構成・25 欄とも同じ**([byte_check_cf33b.json](byte_check_cf33b.json)・`10e/byte_check_10e.py`・5,000 体・seed 1・1 日・テープつき・申込書なし)。head=本体 HEAD `0239a3b` の src の写し(`git archive`・錨はエンジンが開く 3 本・`HEAD_TREE_FILES` は全部そろう=`tree_missing` 空・data はつなぎ・`src_is_worktree` 19 本とも偽)・cf33b=作業木の src(19 本とも真)。比べた欄: final・呼数・blocks・テープの全部の列の sha と列の名・行動の件数・起床の内訳・顕著行為・出動・食事・behavior/full の最後・締めの後の 2 本・暦・frozen_sources。既定 v3 の final `b8eadcb51e8705e7`。壁時計は side ごとに約 4 分(4 並列)。
- **2 日のラン・再開=通し**([two_day_resume.json](two_day_resume.json)・道具 `tools/two_day_resume.py`・世界資産 5,000 体・seed 1・語彙 v3・checkpoint 360 刻み): HEAD の写しと作業木で通しのランの final `b346bb6e…`・呼数 138,946・checkpoint 8 本が全部同じ。どちらの木でも 1 日目の終わり(刻み 1,440)で止めて状態から再開したランの final と 2 日目の checkpoint 4 本が通しと同じ。manifest の `experiment` は両方 null。
- 〔rebase の後〕本体 `76d3899` の写しと作業木で 1 構成(`w6_v3_default`・5,000 体・seed 1・1 日・テープつき・申込書なし)の 25 欄が全部同じ([byte_check_cf33b_after_rebase_1cfg.json](byte_check_cf33b_after_rebase_1cfg.json)・final `b8eadcb51e8705e7`・呼数 64,528・head は `src_is_worktree` 偽・作業木は真)。4 構成は親が回す(§15)。
- 既定のランで変わるもの(byte-check の欄の外): `bridges_count`(398 → 407・rebase の後は本体 411 → 420)と `bridges_version`(つなぎの台帳の行を足したため)。manifest の一番上の鍵・状態のファイル・テープ・2 つのハッシュは変わらない(申込書の無いランは `experiment` が null のまま=足した設定の 4 欄は申込書つきのランにだけ出る)。

## 9. 試験

新しい試験 45 本(〔検収の後〕+10 本=55 本・§15):

| ファイル | 本数 | 中身 |
|---|---|---|
| `tests/engine/experiment/test_cf33b_switch.py` | 11(+3=14) | 窓の頭(負の対照 3 形)・窓の頭でない T と到着待ちの行のあるテープを `run_branch` が止める・再生の箱が刻みごとに空(口の単体)・空にしない写しは (b) が落ちる(単体と合成の世界の分岐)・T からの口を作る関数・札と決定論と `vs_aa`・`determinism`・合成の世界の分岐 3 形(mock=決定論・注入した非決定の口=床・古典) |
| `tests/engine/experiment/test_cf33b_form_checks.py` | 12 | 省略できる欄(3-3 の指紋は変わらない・往復・誤り 5 形)・A/A が宣言を引き継ぐ・CP5-1(旗の 6 形・警告・拒まない=ランが回る)・CP5-3(1 つの道具で名指しと混入・負の対照)・manifest の `known_to_model` |
| `tests/engine/experiment/test_cf33b_manifest.py` | 6(+1=7) | 設定の 4 欄は末尾(3-3 の欄の名と並びは同じ)・申込書つきのランの欄・慣らしの規則(日付なし・読み取り専用)・生の点数の欄・封印の証拠と規則の写し・床の分布(6 対の既知の値) |
| `tests/engine/experiment/test_x33_branch.py` | +1 | 世界資産 1,000 体の分岐(3-3 の fixture)が切り替えの口を通る: 札 mock・決定論・床 0・`vs_aa`・窓・箱 0 |
| `tests/tools/test_warmup_gauge.py` | 8(+4=12) | §5・§15 |
| `tests/tools/test_skill_gauge.py` | 4(+1=5) | §6・§15 |
| `tests/tools/test_hm_gauge.py` | 3(+1=4) | §7・§15 |

- **範囲の試験**(`tests/engine/experiment`・`systems`・`batching`・`body`・`time`・`events`・`bridging`・`test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/tools`・`tests/economy/cp2`・`tests/c8`・`tests/test_cli.py`・`tests/llm`・`tests/engine/rights`・`tests/engine/tools`・`tests/engine/decision`・`tests/perception/facts`・`tests/engine/speech`・`tests/engine/proximity`・`-m "not gpu and not slow"`・6 並列・`--dist loadfile`): **1,919 passed・1 failed(12 分 30 秒)**。落ちた 1 本は `test_state_checks_10f.py::test_axis2_discardable_reset_keeps_the_run_synthetic[1441]` の**子のプロセスの落ち**(`worker 'gw1' crashed`=試験の失敗ではない)。そのファイルを単独で回し直して 24 passed(7 分 6 秒)。発注の範囲だけの 1 回目(上から `tests/llm` まで)は 1,412 passed・0 failed(12 分 51 秒)。
- **slow**: `test_x33_branch.py::test_world_branch_with_staff_5000`(担当のいる 5,000 体の分岐=切り替えの口を通る)1 passed(8 分 19 秒)。
- `tests/c8` と `tests/economy/cp2` は範囲に含めて通った(c8 の読みのグラフは作り直し不要)。`tests/c7` は回していない。
- `lint-imports`(作業木の src・248 ファイル): 5 契約とも KEPT。
- 〔検収の後・rebase の後〕範囲(`tests/engine/experiment`・`tests/tools`・`tests/engine/bridging`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/economy/cp2`・`tests/c8`・`-m "not slow"`・2 並列・`--dist loadfile`): **682 passed・failed 0(11 分 12 秒)**=experiment 123・tools 120・bridging 49・状態台帳 73・10f の 2 本 24+20・cp2 87・c8 186。c8 の読みのグラフは作り直し不要。`lint-imports`(rebase の後の src・250 ファイル)5 契約とも KEPT・0 broken。

## 10. 触った共有ファイル

| 共有のファイル | 触った所 |
|---|---|
| `src/shibuya/engine/manifest_sections.py` | `experiment` の設定の子の末尾に 4 つ(`switch`・`start0`・`known_to_model`・`warmup`)。観測の子は変えていない |
| `tests/engine/test_env_and_sections_10f.py` | `CONFIG_PATHS_SHA256` を `8c1610ad…5209d43` → `5de319d8…faee132b`(この 4 本を外すと前の値=確かめた)と注の 2 行。〔rebase の後〕本体 `76d3899` の `68c3ffd0…c55395`(3-1 の `calendar_shadow` の 4 本を足した値)→ `63a87f2f…40eab3ed`(rebase した src の `config_paths()` から計算し直した・3-3b の 4 本を外すと `68c3ffd0…` に戻る=確かめた)。注は本体の 3-1 の 2 行の後に 3-3b の 2 行 |
| `docs/design/bridging-ledger.json` | 末尾に 9 行(土台 398 → 407・既存の行は不変)。〔rebase の後〕本体の 411 行(3-1 の 12 行・6-1 の 1 行)の末尾に 9 行=**420 行**。〔検収の後〕3-3 の 3 行の文(`what`・`why` の末尾に「残り=…」)と 3-3b の行の文の空白の抜け 3 か所(§11) |
| `src/shibuya/engine/state_ledger.py` | 〔検収 L9〕行 `experiment` の参照 `branch` の説明の文だけ(「T0 で切り替える LLM の口 BranchClient」→「分岐の指定の make_client が作る口=3-3 の BranchClient か 3-3b の ReplaySwitch」)。行・鍵・道筋・持ち主は不変 |
| `src/shibuya/cli.py` | 〔親の判断 5〕`--experiment-branch` の help の文だけ(T0 は窓の頭でなければ止める・3-3 では切り上げて受けていた)。引数の名と既定は不変 |

- 触っていない: 状態台帳の行(増やしていない=持ち主 `ExperimentLayer` の属性は変えていない・切り替えの口は参照 `branch` の先)・manifest の一番上の鍵・凍結の表の JSON・進行役・体の層・記憶の器・語彙・系の表・`tools/c8/sensitivity_v1.json`(tests/c8 は作り直しなしで通った)。
- 並行の作業木とぶつかりうる所: `CONFIG_PATHS_SHA256` の 1 行(ほかの段が設定の子を足せば取り込みの順に計算し直す)・つなぎの台帳の末尾。

## 11. つなぎの台帳の行(9 行・`declared_in`=この記録・2026-10-15)

| id | 中身 | 外す段 | 宣言 |
|---|---|---|---|
| `DOC-cf33b-start0-order` | 「最初から」の順番は宣言と欄だけ・点検は警告と記録 | 4-1 | plan |
| `DOC-cf33b-persona-check-caller` | ペルソナの名指しと混入の疑いの検査は道具だけ(呼び手が文を渡す)・部分一致 | 4-1 | inferred |
| `DOC-cf33b-warmup-difference-series` | 差の系列に当てる形・1 シム日・最大で束ねる・無効 3 回 | 7 | inferred |
| `DOC-cf33b-warmup-counts` | 問い 1 の 5 本・先行 28 日・最低 1 週間(未リサーチ) | 7 | inferred |
| `DOC-cf33b-warmup-stock-flow` | 在庫 → 純流量で代える・置き場の指標・月の周期は推移の指標 | 6-5 | inferred |
| `DOC-cf33b-hm-container` | HM は器だけ(候補は 4-1 の後) | 4-1 | plan |
| `DOC-cf33b-skill-raw` | 生の点数は計器が埋める・rank histogram の同じ値の割り方・封印の証拠の欄は空 | 7 | plan |
| `DOC-cf33b-floor-per-branch` | 1 回の分岐で A/A の対 1 つ・(c) の A/A との比べは checkpoint の粒度・決定論の札は mock と古典 | 6-7 | inferred |
| `DOC-cf33b-switch-fleet-tape` | 到着待ちの行のあるテープは拒む・T からの口は同期の口だけ | 6-7 | plan |

- 3-3 の行のうち、本段で一部が埋まったもの: `DOC-cf33-start-zero-order`(CP5-1 の点検と CP5-3 の道具ができた=順番の口と組み立ての中の点検が残る)・`DOC-cf33-burn-in-not-judged`(判定の器と規則の事前登録ができた=実際のランの対での判定が残る)・`DOC-cf33-skill-empty`(生の点数の欄と計器ができた=値と公開の置き場が残る)。〔親の判断 3〕3 行の「未実装」の文を「3-3b で…を入れた。残り=…(3-3b の行 id)」に書き直した(`what` の末尾と `why` の末尾に「残り=3-3b の行 …」・status は active のまま・行は消さない・`declared_in` と `remove_at` は不変)。指す行: start-zero-order → `DOC-cf33b-start0-order`・`DOC-cf33b-persona-check-caller`/burn-in-not-judged → `DOC-cf33b-warmup-difference-series`・`-counts`・`-stock-flow`/skill-empty → `DOC-cf33b-skill-raw`。
- 〔検収 L9〕3-3b の行の文の空白の抜け 3 か所を直した(「告知が無いか unexpected=true」・「checks の persona_naming」・「札は mock」)。

## 12. 限界と仮採用(10-13b §0-3=既定 off・戻せる形・PENDING §1-1 の候補)

1. **`run_branch` の既定を切り替えの口にした**(`SwitchSpec`/`ReplaySwitch`)。3-3 の `BranchSpec`/`BranchClient` は残した(`make_client`)。決定論の札でランの口そのものなら、T より前の答え・T からの答え・4 つの確認の値は 3-3 と同じ(世界資産 1,000 体の分岐の試験の 3-3 の値がそのまま通る)。
2. **T の窓の頭の検査を `run_branch` に入れた**: 3-3 では刻みの頭でない T を切り上げて受けていた。窓の頭でない T は止める(申込書そのものの `start` は今のまま=分岐でないランは切り上げ)。〔親の判断 5〕止める形のまま(申込書の T を黙って丸めない)。CLI の `--experiment-branch` の help に「3-3 では切り上げて受けていた=3-3b で止める形に変えた」と書いた。
3. **再生の箱の単位は刻み**・**到着待ちの行のあるテープは拒む**(艦隊の分岐は 6-7)。〔検収 L1〕口の中の箱の計器は作りから 0(空にする処理の退化の計器)。(b) の本体は艦隊のテープの到着待ちの行を拒む守りで、O96 `replay_inbox` を T の刻みで読む口は無い(系 `experiment` の読む欄は系の表で `layers.experiment` だけ=系の表は本段の範囲の外)ので (b) の条件に O96 は入れていない(分岐のランでは O96 は作りから空=橋は口の道を通り `observed_tick`=−1)。
4. **決定論の札は mock と古典だけ**(宣言で上書き可)。実 LLM の床の分布は、実 LLM を T から答えさせる口(6-7)と A/A の対の本数の決め方が要る。本段の非決定の試験は「作るたびに種の違う mock」で代えた。
   - 〔検収 L2・親の判断 2〕**3-3 の契約の約束 (4)(d)「A/A の差は厳密に 0」との差**: 3-3b では「mock・古典(と決定論を宣言した注入の口)=厳密に 0(`d_determinism`)・LLM(非決定の口)=T より前の一致と床の分布(`d_floor`)」に分けた。約束の文の書き換えは親がユーザーに確かめる(本段は触っていない)。注入した口は宣言(属性 `deterministic`=真偽)があれば決定論の確認をかけ、宣言が無ければ非決定のまま(既定は変えない)。summary の `d` は `None` もとりうる(非決定の口で T より前の checkpoint が無いとき)。
   - 〔検収 L6〕**非決定の口では (c) の回し直しも新しい種**で答える: 指紋の窓をかけた改変の枝の 2 本目も第 1 段の 1 本目と違う答えになるので `branch_repeat_same` は**作りから偽**・第 1 段の 2 本で決めた窓が 2 本目の対の食い違いを挟む保証も無い=(c) の系と欄は床の揺らぎと混ざる(報告だけ・合否に入れない)。
5. **(c) の A/A の枝 2 本との比べは checkpoint の粒度**(粗い比べ)。A/A の枝 2 本に系ごとの指紋はかけていない(かけるとランが 1 本増える)。
6. **(d) の床はランごとに 1 対**。分布は呼び手がアンサンブルの各メンバーの対を `floor_values` に並べて作る。
7. **CP5-1 は警告と記録だけ**(拒まない=仮-24)。旗は告知の有無と自己申告だけで決める(告知の時刻と中身は見ない)。「最初から」の順番の口は 4-1 段 6 の後。
8. **CP5-3 は道具だけ**(ランの中では走らない)・部分一致(表記の揺れは拾わない)・自己申告の欄の中身は空でよい。
9. **慣らしの判定は合成の系列でだけ確かめた**。実際のランの対(開始日のランと 28 日前から慣れたランを 5 本・改変の枝と A/A の枝を 6 対・各 14 日以上)は回していない(R-117 §4-6 の見積りで 5,000 体 mock なら 1 初期状態あたり約 3.1 時間=推測)。MSER の値は pymser と同じ入力で照合していない(写さず式から書いた・依存を増やさない)。〔親の判断 4〕候補の範囲は d ≤ n − 5 のまま。R-117 §4-4 の pymser の数え方(候補は n − 3 番目まで=最後の 2 つを除く)なら「最後の 5 つを除く」は d ≤ n − 6=1 つずれる(宣言・未リサーチ・規則の項 `exclude_last_counting`)。
10. **在庫の流量は純流量で代えた**(新しく知った数・忘れた数の総流量の欄は計器の側の置き場)・食事・約束・グループの数も置き場。速い指標の外出と訪問は到着の数と店で払った行で代えた。
11. **技量スコアの生の点数は計器が埋める**(値の出る口は外に出す予測の段)・rank histogram の同じ値は seed つきの乱数で割る。
12. **HM は器だけ**(候補・観測の値・モデルの食い違いの分散は無い)。
13. manifest の設定に 4 欄を足した=`CONFIG_PATHS_SHA256` が変わる(既定のランの `experiment` は null のまま)。
14. CLI の引数は足していない(仮のモデルの口 `live`・`model`・`deterministic` は Python の口 `run_branch` だけ)。

## 13. 親に確かめてほしいこと

〔検収の後〕1・2・3 は親の判断で決まった(1=止める形のまま・2=守りの本体は到着待ちの行を拒むこと・箱は退化の計器=§2・3=3 行の文を「残り=…」に書き直した=§11)。4・5 は残る。

1. **`run_branch` の T の窓の頭の検査**: 刻みの頭でない T を 3-3 は切り上げて受けた。止める形でよいか(§12 の 2)。
2. **再生の箱の読み**: 発注の「再生の箱に刻みの外の物を残さない(1-3 の教訓)」を、(i) 切り替えの口の箱を刻みごとに空にする(計器と (b) の条件)と (ii) T をまたいで届くテープの行(再生の到着待ち=`run_day.replay_inbox` に残る物)を拒む、の 2 つで実装した。教訓の出どころは 1-2 の検収 M1(`Percept` が到着待ちに残って full-hash が変わった)と読んだ。意図と違えば直す。
3. **3-3 のつなぎの台帳の 3 行**(§11 の末尾)を直すか。
4. **(c) の A/A との比べの粒度**(§12 の 5): 実 LLM の段(6-7)で A/A の枝にも指紋をかけるか。
5. 慣らしの計器の速い指標の代わり(到着の数=外出・店で払った行=訪問)でよいか。

## 14. 再現の手順(リポの根で・`$D`=このフォルダ・`$W`=作業用の短いディレクトリ・`PYTHONPATH` に作業木の `src`)

```
B=docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py
git archive 0239a3b src docs/design/rules-table.json docs/design/bridging-ledger.json docs/design/v2-budget-declaration.md \
    docs/design/v2-perception-contract.md docs/design/v2-pattern-ledger.md \
    docs/bench/anchors/hunger_energy_build_anchors_v0.json docs/bench/anchors/hunger_energy_validation_anchors_v0.json \
    docs/bench/anchors/ssb2021_activity_prior_v0.json docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
# data へのつなぎ(junction)を $W/head_src/data に置く(回し終えたら .NET でつなぎだけを外す)
python $B side --src $W/head_src/src --label head --scratch $W/bc --out $W/head.json --jobs 4
python $B side --label cf33b --scratch $W/bc --out $W/cf33b.json --jobs 4
python $B compare --a $W/head.json --b $W/cf33b.json --out $D/byte_check_cf33b.json
python $D/tools/two_day_resume.py side --src $W/head_src/src --label head --scratch $W/tdr --out $W/tdr_head.json
python $D/tools/two_day_resume.py side --src src --label cf33b --scratch $W/tdr --out $W/tdr_cf33b.json
python $D/tools/two_day_resume.py compare --a $W/tdr_head.json --b $W/tdr_cf33b.json --out $D/two_day_resume.json
python $D/tools/switch_example.py --scratch $W/sw --out $D/switch_example.json
python -m pytest -q -p no:cacheprovider -o addopts="" -rf -m "not gpu and not slow" tests/engine/experiment tests/tools
```

〔rebase の後の 1 構成〕`git archive 76d3899 …`(同じ道筋)で写し、`side … --only w6_v3_default --jobs 1` を head と作業木で回して `compare --out $D/byte_check_cf33b_after_rebase_1cfg.json`。

## 15. 独立検収の後の直しと rebase(検収 [review.md](review.md)=条件つき受入・親の判断の 6 項)

- 実装役が直した。scratch は作業木の `_bc2/`(終わったら中身を消した・つなぎは .NET の `Directory.Delete` で外した)。初めの byte-check の置き場 `_bc/` は触っていない(親が消す)。

| 欠陥 | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| M1 | `tools/instruments/warmup_gauge.py` の指標の表(`conversations`) | 道筋 `probe.conv.opened`(`n_opened`=ランの頭からの累計)に**累計の印** `kind: counter` を付け、日ごとの差に直す(最初の記録の日は落とす)。md23 の累計の道筋の一覧 `CUMULATIVE_PATHS`(`conv.opened`・`conv.closed`・`conv.joined`)は印が無ければ拒む(流量・在庫と宣言しても `ValueError`)。規則に `counter`・`counter_unmarked`・`counter_first_day` | `test_counter_paths_are_differenced_and_unmarked_ones_are_refused`(累計 → その日の数・印の無い累計は拒む・md23 の形で種 0 は慣らしの日数 7・40 種中 22 で 7・負の対照=守りを外した写しは 40 種中 1) |
| M2 | `warmup_gauge.check_path`・`hm_gauge.check_path` | 中身を `read_guard.deny_hit(path)` に替えた(小文字にそろえた生の道筋 → 当たらなければ実体の道筋)。前の照らし方は大文字の 4 形とつなぎの形を 5 つとも通した(scratch で確かめた) | 両方の計器に `test_read_guard_catches_upper_case_and_junction`(大文字 4 形・名に語を含まない junction の先が語を含むフォルダ・語の無い道筋は通る=正の対照) |
| L1 | `engine/experiment/switch.py`(`_box_enter`)・`branch.py`(`pre_t0_match` の注)・記録 §0・§2・§12 | 箱の計器は「作りから 0=空にする処理の退化を捕まえる計器」と書き分け、守りの本体は艦隊のテープの到着待ちの行を拒むこと(`tape_crossing`)と明記。O96 `replay_inbox` を T の刻みで読む口は無い(系 `experiment` の読む欄は系の表で `layers.experiment` だけ・系の表は範囲の外)=(b) に O96 は入れず宣言(分岐のランでは O96 は作りから空) | 既存(箱 0・空にしない写しで (b) が落ちる) |
| L2 | `switch.py`(`declared_determinism`・`DETERMINISM_ATTR`・`ReplaySwitch.deterministic_by`)・`branch.run_branch` の docstring | 注入した口が属性 `deterministic`(真偽)で決定論を宣言できる口を足した。決める順は指定 → 口の宣言 → 札。宣言があれば (d-1) の厳密一致を求める。宣言の無い注入の口は非決定のまま(既定は変えない)。manifest の `experiment.switch.deterministic_by`(足しただけ)。記録 §12 の 4 に「3-3 の約束 (4)(d) との差」 | `test_an_injected_port_can_declare_determinism`(単体=port・label・spec の順・真偽でない値は宣言でない)・`test_switch_with_a_declared_deterministic_port`(合成の世界の分岐=宣言した決定論の口は A/A が厳密に同じで通る・宣言したのに非決定の口は (d) が落ちる=負の対照) |
| L3 | `warmup_gauge._judge`・`_bundle`・問い 1/2 の `build` | 慣らしの日数=最初の日 + d* − 系列の頭の日(直す前の系列の最初の日・問い 2 は実行の日)を指標ごとに出し、束ねの W はその最大(`bundle.unit=days_from_series_head`)。規則に `warmup_days` | `test_stock_warmup_days_count_from_the_series_head`(6 日ふえる在庫=d* 6・慣らしの日数 7・W 7)・既存の表の試験を W 5(在庫 d* 4 + 1)に直した |
| L4 | 記録 §5・`tests/tools/test_warmup_gauge.py` の注 | 「22 で 12」→「22 で 16」。試験に試行ごとの d* `[12, 16, 12]` の主張を足した | `test_latter_half_is_invalid_and_extended` |
| L5 | `engine/experiment/warmup.py` | `q2.fine_steps: 15`(刻みの数で時間を書いた直書き・使っていない)を消した。印の無い 4 項(`statistic`・`q1.series`・`q2.series`・`q2.bounds`)に印。新しい項にも印。`rule_items()`・`MARK_VALUES` | `test_every_rule_item_has_a_mark`(`RULE` の葉の項と `MARKS` の鍵が同じ・語彙・`fine_steps` が無い) |
| L6 | 記録 §12 の 4 | 「非決定の口では (c) の回し直しも新しい種=`branch_repeat_same` は作りから偽・(c) の系と欄は床の揺らぎと混ざる」を宣言 | — |
| L7 | `tools/instruments/skill_gauge.py` | 入力の道筋に `read_guard.deny_hit` の守り(`check_path`・`main` が開く前に呼ぶ)=慣らし・HM と同じ線(較正側だけ) | `test_read_guard_on_the_input`(封印・大文字・holdout・検証側の錨の名・CLI は開く前に落ちる) |
| L8 | `switch.ReplaySwitch`・`branch.BranchClient`・`warmup_gauge.METRICS` | 計器の数(箱の 5 つ・再生の 5 つ)は読み取り専用の属性(中身は口の中の `_meters`)。`METRICS` は行を `MappingProxyType`・列を tuple に(指紋は前と同じ形で計算) | `test_meters_are_read_only`・`test_metric_table_is_read_only` |
| L9 | `src/shibuya/engine/state_ledger.py` の行 `experiment` の参照の説明・つなぎの台帳の 3-3b の行の文 | 説明の「BranchClient」→「分岐の指定の make_client が作る口=3-3 の BranchClient か 3-3b の ReplaySwitch」。空白の抜け 3 か所 | 範囲の試験(状態台帳・つなぎの台帳) |
| L10 | `_bc/` | 触っていない(親が .NET でつなぎを外してから消す) | — |
| 親の判断 3 | つなぎの台帳の 3-3 の 3 行 | 「未実装」の文を「3-3b で…を入れた。残り=…(3-3b の行 id)」に(§11) | 範囲の試験(つなぎの台帳) |
| 親の判断 4 | `warmup.RULE` の `exclude_last_counting`・記録 §5・§12 の 9 | 候補 d ≤ n − 5 のまま・pymser の数え方とは 1 つずれる宣言(未リサーチ) | `test_every_rule_item_has_a_mark` |
| 親の判断 5 | `cli.py` の `--experiment-branch` の help・記録 §2・§12 の 2 | 窓の頭でない T は止める形のまま・3-3 では切り上げて受けていた旨 | — |

**rebase**(本体 `76d3899`=土台 `0239a3b` の後に 3-1=`47749f2`/`5924be9`/`35aa748`・6-1=`908d361`/`76d3899`):
- 手順: 追跡の変更 9 本の枝の版と土台の版を `_bc2/` に控え → `git checkout -- .` → `git merge --ff-only build/spatial-d102-prep`(枝が `76d3899` に)→ 9 本それぞれ `git merge-file`。未追跡の新規は checkout で消えない(本体の新規のファイルと名は重ならない)。
- 衝突は 2 本: `docs/design/bridging-ledger.json`(6 か所)=本体の版の JSON を読み、3-3b の 9 行(id が `DOC-cf33b-`・枝は既存の行を変えていない=土台の 398 行と同じを確かめた)を末尾に足して書き直した(本体の書き方=`indent=1`・`ensure_ascii=False`・末尾の改行が同じバイト列で再現できることを確かめてから)=**420 行**。`tests/engine/test_env_and_sections_10f.py`(1 か所)=`CONFIG_PATHS_SHA256` を rebase した src の `MS.config_paths()` から計算し直して `63a87f2f1fcfd2e7dcd14e17f8f7bfe03338785a46282fff31ec1d0d40eab3ed`(本体 `68c3ffd0…c55395`・3-3b の 4 本を外すと本体の値に戻る=確かめた。検収役の予測と同じ値=道筋の一覧は並べ替えてから指紋を取るので足す順によらない)。
- 自動でまとまった 7 本: `engine/experiment/` の 5 本・`manifest_sections.py`(本体の 3-1 は `calendar_shadow` の塊・3-3b は `experiment` の子の末尾=別の塊)・`tests/engine/experiment/test_x33_branch.py`。状態台帳の行は 3-3b が足していない(説明の文の直しは rebase の後に本体の版へ)。
- rebase の直後の `git diff --stat`=9 本・345 行足し 22 行消し(rebase の前と同じ)。全部 LF。

**試験**(rebase と直しの後): 発注の範囲 **682 passed・failed 0・11 分 12 秒**(`-n 2 --dist loadfile -m "not slow"`・内訳 §9)。c8 は 186 passed(読みのグラフの作り直し不要)。`lint-imports` 5 契約 KEPT・0 broken(250 ファイル)。範囲の試験の途中で直した文の 2 か所(`branch.py` の注の空行・`warmup_gauge.question2` の docstring)の後に `tests/engine/experiment` と 3 つの計器の試験を回し直した=**144 passed・failed 0(4 分 33 秒)**。

**byte-check(1 構成)**: 本体 `76d3899` の写し(`git archive` の src と `HEAD_TREE_FILES` の追跡ファイル+本体の data へのつなぎ=回し終えて .NET で外した)と作業木で `w6_v3_default`(5,000 体・seed 1・1 日・テープつき・申込書なし)=**25 欄とも同じ**・final `b8eadcb51e8705e7`・呼数 64,528・head は `src_is_worktree` 偽・作業木は真([byte_check_cf33b_after_rebase_1cfg.json](byte_check_cf33b_after_rebase_1cfg.json))。4 構成は親が回す。

**できなかったこと**: O96 `replay_inbox` を T の刻みで読んで (b) の条件に入れること(読む口が無い=系の表は範囲の外・宣言で代えた)。3-3 の契約の約束 (4)(d) の文の書き換え(親がユーザーに確かめる)。

## §親の検収(第336・Fable 5.1・rebase の後)

- 本体 ed7155c(6-1 の文書の後)へ rebase=衝突なし(直し役が 76d3899 へ控え+早送り+merge-file で rebase 済み=つなぎの台帳の末尾(420 行)と `CONFIG_PATHS_SHA256`(68c3ffd0 → 63a87f2f)の 2 本を手で解いた)・810b9eb。範囲の試験(experiment・tools・bridging・状態台帳・10f・cp2・**c8**)**682 passed**(417 秒)。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src)=**final 同じ・25 欄とも差なし**(`parent_head_vs_cf33b_4cfg.json`)。申込書なしのランは 3-3b の口をどこも通らない(検収役の AST)。
- **data 無しの写し(detached の作業木・junction なし)で CI-1 と同じ引数の全体試験(tests/c7 を含む)=**5,168 passed・254 skipped・failed 0**(1,224 秒・CI の印=`-m "not gpu and not slow" -n 2 --dist loadfile`)**。
- 独立検収([review.md](review.md))=条件つき受入(中 2=累計の指標 `probe.conv.opened` を流量として扱っていた・計器の読む守りが大文字と junction を通していた/ 低 10)→ 全部直した(§15)。検収役の独立の再計算(1,000 体の分岐の 4 つの確認・MSER の別実装 300/300・fair CRPS・HM・2 日のラン・`CONFIG_PATHS_SHA256`)は全部一致。親の判断: 注入した口は決定論を宣言できる口を足し宣言が無ければ非決定のまま・慣らしの候補は d ≤ n−5 のまま(pymser と 1 つずれる=宣言)・窓の頭でない T は止める(3-3 の切り上げを置き換え)・3-3 の台帳 3 行は「残り=3-3b の行」に(status 不変)・**口の約束 3-3 (4)(d) の文の改めはユーザーに確認(PENDING §1-1)**・O96 `replay_inbox` を (b) の条件に入れる読む口は無い=宣言で代える。
- 判定: **受入**(第 3 期 3-3b=既定(申込書なし)は不変・CLI の引数は足していない)。
