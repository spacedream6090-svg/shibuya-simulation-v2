# 第 1 期 1-8 候補の口 J0 の独立検収(review)

- 検収役 Opus 5.5(実装は見ていない)。対象=作業木の枝 `1-8/decision-port`(土台 `f60b0a6`)の未 commit の変更 25 ファイル+新しい置き場 3 つ(`src/shibuya/engine/decision/`・`tests/engine/decision/`・この記録の置き場)。本体 HEAD `ccaf2c1`(1-5 を取り込んだ後)は読むだけ。
- 正: 口の約束 `docs/design/v2-foundation-contracts-2026-10-13.md` の「1-8 候補の口 J0」と冒頭の共通の約束・実装役への発注文・実装役の記録 [README.md](README.md)。
- 検収の道具は検収役の scratch に置いた(作業木には置いていない)。生の出力は作業木の `_bc_review/`(git の外・終わったら消す)。

## 判定

**条件つき受入。** 既定の腕の結果不変(自分の byte-check 4/4・25 欄)・腕 port の同値(自分の独立の再計算=合成の世界 300 体・seed 11・3 構成で番号列と final とテープが一致・負の対照で final が動く)・原因の表の列化(1 呼 61/100/218 B を容量の倍化から再計算で一致・CP12 の門は弱っていない)はどれも確かめた。条件は H1(取り込みのときに直す)と M1・M2 の親の判断。

## 欠陥(重さの順)

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| H1 | 高(取り込みの時) | `src/shibuya/engine/events/log.py` 302 行(`_PROC_CODE`)・523 行(`_cause_at` の `V.PROCESS_NAMES[ref]`) | 列化した原因の表は過程の名の番号を `V.PROCESS_NAMES` から作る。本体 HEAD(1-5 取り込み済み)では `Process` の検査が `V.CAUSE_PROCESS_NAMES`(`PROCESS_NAMES`+`"rights"`)に広がっている。`log.py` を 3-way で併合すると**衝突なしで通り**、1-5 の `Process("rights")`(出来事「行為:許可のない行動」)を書くと `KeyError: 'rights'`(土台・作業木・HEAD の 3 本から `git merge-file` で作った写しで再現)。19 構成の byte-check では NO_PERMISSION=0 なので見えない。1-5 の試験 `tests/engine/rights/test_rights_events.py` が落ちるはず | 取り込みのときに `_PROC_CODE` と `_cause_at` を `V.CAUSE_PROCESS_NAMES` にする。名の表は `Process.__post_init__` の検査と同じ 1 つの定数から作る(L1 と一緒に) |
| M1 | 中(親の判断) | 約束 (3)・`engine/decision/layer.py` `_write_event` | 「候補の源のどれから来たかを記録」が、判断ごとには残らない。出来事の行は `行為:<語>` と `LlmCall(call_id, 候補の basis の和)` だけで、J0 では basis が全部空(1-6 の器の行が全部 `legacy`)。源は manifest の集計(`presented_by_source`・`chosen_by_source`・`chosen_number`)にしか無い。実装役も記録 §11-2 で親に確かめを求めている | 親が読み方を決める。案: 原因の表の列に「選んだ候補の源」(i1)と「提示の番号」(i1)を足す(1 判断 1 行の LlmCall の行なので 2 B/判断。R-108 §3-1 の位置の偏りを判断ごとに引ける) |
| M2 | 中 | `src/shibuya/engine/rng_audit.py` 403 行(`K19_RECREATED["llm.mock"]`) | 許可を用途名ごと足したので、**既定の腕**の実行時の検査(`check_overlaps`)も `llm.mock` の同じ鍵の作り直しを通すようになった(既定の腕で mock を同じ鍵で 2 回引く欠陥を見落とす)。既定の腕で 0 を見る試験は合成 120 体の 1 本(`test_k19_runtime_audit_on_the_port_arm`)だけで、世界資産の 300 体 2 日・5,000 体の K19 の試験は「⊆ 許可の表」しか見ない | 既定の腕の K19 の試験(`tests/engine/test_state_checks_10f.py` の世界資産の 2 本)に `llm.mock` の作り直し 0 を足す。または許可を表に置かず、腕 port の検査だけ `check_overlaps(..., recreated={**K19_RECREATED, "llm.mock": …})` で渡す |
| L1 | 低 | `log.py` 302 行 | `_PROC_CODE` は素の dict(表は `MappingProxyType` という 1-3 の検収の教訓) | H1 と一緒に `MappingProxyType` に |
| L2 | 低(自己申告どおり) | 記録 §10-15・16 | 腕 port の性能の予算(+118〜191 µs/呼)と、判断の出来事の成長の宣言(39 万体 7 日で約 3.9 GB)が無い | 腕を既定にする段の前に宣言する(PENDING に残す) |
| L3 | 低(自己申告どおり) | `docs/design/bridging-ledger.json` | 外す段 1-8 のつなぎの 3 行(`DOC-memory-store-legacy`・`DOC-money-fare-cause-rail`・`DOC-money-uncaused-rows`)が active のまま(台帳で確かめた) | 外す段を付け替えるか 1-8 の続きでやるかを親が決める |
| L4 | 低 | `llm_bridge.py` `_after_render` の引数 `tick`・`llm/mock.py` `action_draw` と `decision/ports.py` の docstring | T0 の「新しいコードは刻み系の名」に対し、`call` の本体を出した新しい関数の引数が `tick` のまま(名は既存の許可の表にあり試験は通る)。docstring の `tick` は検査の範囲(core・systems)の外 | 名を替える段でまとめて(今は直さなくてよい) |

## 1. 結果不変 ✓

- 実装役の byte-check([byte_check_j0.json](byte_check_j0.json)): 19/19 構成で 25 欄とも同じ(動いた欄 0)。head=土台 `f60b0a6` の写し・j0=作業木の src。腕 port の 4 構成([byte_check_j0_port_4cfg.json](byte_check_j0_port_4cfg.json))も 4/4・25 欄とも同じ。腕の既定は層を作らない(`build.py` は `_DL.arm() == ARM_PORT` のときだけ層を作る・`decide.py` は層が None なら `bridge.call` のまま)。
- 自分の 4 構成(`w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`・5,000 体・seed 1・1 日・テープつき): 本体 HEAD `ccaf2c1` の src の写し(`git archive`)と作業木の src(`--src`・環境変数の腕は未設定=legacy)で `side` → `compare`。**4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`・final の全桁・behavior/full の最後・締めの後の 2 本・テープの全列)。`src_is_worktree` は head が偽・j0 が真。
- 追加で腕 port(`SHIBUYA_DECISION_PORT=port`)の 2 構成(`w6_v3_activity_off`=実装役の 4 構成に無い物・`v3_mem_rel`)を回し、HEAD と 25 欄とも同じ。壁時計は port が +10〜13 秒(腕が効いている印)。
- manifest の既存の欄(合成の世界 200 体・3 構成=v3・古典+記憶+関係+店の記憶+親しみ・v1 の 2 日、土台の写しと作業木の既定の腕を葉で比べた): 動いた葉は `bridges_count`(277 → 281=つなぎの台帳 +4 行)・`bridges_version`・`env_id`(コードの差分の指紋)だけ。鍵の並びは先頭 113 が同じで末尾に `decision_port` 1 つ。

## 2. 口と約束 ✓(違いは下)

- 型と名: `Candidate`(`id`・`kind`・`text`・`source`・`number`+足した `basis`)・`Choice`(`candidate_id`・`number`・`kind`・`other_text`・`surprise`・`hesitation`・`continuous`・`reason`・`reason_first`・`utterance`・`backend`)・`DecisionPort.choose(ctx, candidates) -> Choice`。3 つの実装は `choose` を上書きしない(AST と `cls.choose is DecisionPort.choose` の実行時の両方)。
- 約束の違い: (a) 発注の `ctx: Percept(+予想+記憶の見え方+道具)` は、`Percept` を直接でなく包む型 `DecisionContext`(`percept` と `prediction` が隣り合う・`memory`・`tools`・呼の鍵)。形として問題なし。(b) DM13 は欄 `continuous` だけで「連続値への変換」の関数は無い(〔決定〕で空で始めるので J0 では要らない)。(c) 約束 (3) は M1。
- 約束 → 試験: (1) 既定の final 不変=byte-check(記録)+`test_legacy_arm_builds_no_layer_and_keeps_the_bridge_call`。(2) 腕 on の同値=`test_arm_on_off_same_final_tape_and_decision_sequence`(5 構成)+slow の 5,000 体。(3) 源の記録=`test_decision_events_carry_the_tape_call_id`・`test_manifest_carries_the_ratio_field`(判断ごとの源の試験は無い=M1)。(4) ひと言の欄=`test_choice_fields_start_empty`。C-2 の 4 つ=`test_j0_shuffle_invariance.py`・`reason_first` と `compose` の長い版の指示・「その他」の欄と計器・提示の文の見出し「頭に浮かんだこと」。
- 〔決定〕: 「その他」の割合の既定=値なし(`None`)と出典 R-108 §1-5・空欄 R108-1。R-108 本文を読み、測った原典が無いこと・近い証拠の数(Wang ほか 2025 表 2 の 18.3%・Tam ほか 2025 付録の表 7 の 0.738 → 0.350)が写しと合うことを確かめた。驚き・迷い・連続値は空で始める ✓。

## 3. 発注文の各項

| # | 判定 | 根拠 |
|---|---|---|
| 1 port.py | ✓ | 型・提示(`present` が最後に番号を振る・作る側の番号は拒む・id の重なりは拒む)・鍵=`stream(seed, "decision.present", *k19_counters(run_tick_key, 体, 候補の数))`・`compose`(短い版と長い版の共通部分が先頭で同じ)・「その他」の既定と出典 |
| 2 3 つの実装と腕 | ✓ | `MockPort`=`MockLLM.action_draw`(mock の `render` と同じ鍵・同じ形の 1 語目)を語彙の順の候補に当てる・`ClassicalPort`=`complete_with_answer` の答えの語・`LlmPort`=パーサの語(当たらなければ「その他」)。`--decision-port {legacy,port}`(既定 legacy・CLI が環境変数より強い) |
| 3 原因の表の列化と配線 | △ | 列化は ✓(7 列 37 B+入力 12 B)。「候補の id を `LlmCall` に」は「候補の元の出来事 id の和」と読み、J0 では全部空(M1) |
| 4 知覚の事実と予想 | ✓ | `DecisionContext.percept`(1-2 の `Percept`)と `prediction`(空)。口は値を読まない(3 実装とも予想を入れて同じ答え) |
| 5 ひと言の欄 | ✓ | `Choice.utterance`(空) |
| 6 manifest | ✓ | `decision_port`(設定 7・観測 12)を末尾に。腕 legacy は観測の子が null。既存の欄は不変(§1) |
| 受入の試験 | ✓ | 5 本の名どおり+`test_j0_writes_declared.py`・`test_j0_cli.py`(51 本+slow 1 本・収集で 52) |
| byte-check 19・腕 port 4 | ✓ | §1 |
| 記録 | ✓ | §6 |

「できなかったこと」(記録 §10-14〜17)は実態と合う: 1-8 で外す予定の 3 行は台帳で active・成長の宣言は 1-3 の expedient のまま・性能の宣言なし・2-0b は未着手。

## 4. 守り ✓

- 書き手: `DecisionLayer` の計器と控えを書くのは `decide_one`・`note_fleet_calls`・`_write_event` だけで、呼ぶのは系 decide だけ(`grep`)。段 B の試験は `J0:decision.*` を外すと宣言の外を見つけ、`E:events.*` を外すと判断の出来事を書く所で `PermissionError`(負の対照 2 本)。
- 実行時の物: `Candidate`・`Choice`・`DecisionContext`・`Hesitation` は凍結(`slots`)・`Choice.continuous` と `SOURCE_NOTES`・`_INDIVIDUAL_BLOCKS` は `MappingProxyType`・manifest の観測は写しを返す。`DecisionLayer` に `__setattr__` の守りは無いが、行 J0 は diag・discardable で書く系は decide の 1 つ(1-3 の `EventLog` と同じ扱い)。素の dict の表は L1。
- 静的な検査の負の対照: 3 実装が `choose` を上書きしない検査は AST だけでは `choose = …` の代入を見ないが、実行時の `is` の比べが受け持つ(両方で 1 組)。

## 5. 宣言と凍結 ✓

土台 `f60b0a6` の写しと作業木で、表を JSON に出して比べた(道具は scratch)。

- 系の宣言: 変わったのは decide の `writes.paths` に `J0:decision.*`・`E:events.*`、`reads` に `layers.decision`、close_final の `reads` に `layers.decision` だけ。`writes.soa` と系の数・並び(31)は同じ。凍結の表 `writes_paths_events.json` に decide を足した(理由つき)。
- 状態台帳: 行 193(+`J0`=diag・discardable・持ち主 decision・道筋 5)。ほかの行で変わったのは `E` だけ(items の `_ev_causes`・`_ev_cause_codes` を消し原因の表の 16 個を足した・dtype と note)。behavior_items と full_items は同じ。`OWNER_CLASSES`・`OWNER_NAMES`・`EXCLUDED` は末尾に足しただけ(`DecisionLayer` の 19 属性は items 5+除外 14 で全部覆う)。版は上げない(1-3・1-6・1-2 と同じ理由)。
- manifest の凍結の鍵: 113 → 114(末尾に `decision_port`・先頭 113 は同じ)。`CONFIG_PATHS_SHA256`: 設定の道筋 164 → 171、足したのは `decision_port.{schema,arm,port,sources,bridge_source,other_share_default,other_share_basis}` の 7 つだけ(消えた物なし)。新しい値 `89e426b3…` を自分で再計算して一致。
- 乱数の表: `UNDETERMINED_SITES` 12 → 13(`present_rng`)・`SAFE_SITES` は名の付け替え 1 つ(`ClassicalPolicy.render` → `answer`・数は 14 のまま)・`K19_RECREATED` +`llm.mock`(M2)。`MOTION_RNG_DOMAINS` に `decision.present`。

## 6. 同値(独立の再計算) ✓

実装役の試験(`LLMBridge.call` と `decide_one` を包んで (刻み・体・適用したコード) を集める)と別の取り方で確かめた。合成の世界・**300 体・seed 11**・24 セル・1 日(1,440 刻み)・checkpoint 60 刻みごと。`DecisionPort.choose` と `present` を包んで、口の答えの語・番号・提示の並びを記録し、legacy のテープの応答をパースした語と call_id ごとに突き合わせた。

| 構成 | 呼 | final・24 個の checkpoint の behavior/full・テープの全列 | 口の語 = legacy のテープの語 | 番号 = 提示の位置 | 提示が元の並びのまま | mismatch | 判断の出来事(port / legacy) |
|---|---|---|---|---|---|---|---|
| mock v3 | 3,940 | 全部同じ | 不一致 0 | 全部 | 0 | 0 | 3,940 / 0 |
| mock v1 | 3,596 | 全部同じ | 不一致 0 | 全部 | 0 | 0 | 2,715 / 0(語彙表に無い 881=`events_unlogged`) |
| 古典+記憶+関係 | 6,193 | 全部同じ | 不一致 0 | 全部 | 0 | 0 | 6,193 / 0 |

- 選んだ番号の分布はほぼ一様(v3 で 1〜13 番が 269〜330)。manifest の `chosen_number` と自分の数えが一致。
- 判断の出来事は 1 判断 1 行・call_id はどれも legacy のテープにある・`what`=`行為:<口が選んだ語>`・`who`=call_id の体・`input_event_ids` は空。
- ランの水準の並べ替えの試験(実装役は単体だけ): 並べ替えの種だけをずらすと、番号は 3,940 呼のうち 3,632 呼で変わり、選んだ語の列と final は同じ。同じ構成を 2 回回すと番号の列が同じ(決定的)。
- **負の対照**: `MockLLM.action_draw` を +1 ずらす(実装役の「番号を 1 つずらす」と別の植え方)と `mismatch` 3,803・final が動く。

## 7. 試験

- 作業木で指定の範囲(`tests/engine/decision`・`events`・`systems`・`time`・`tests/perception`・`memory`・`bridging`・状態台帳と状態の検査と環境の節と再開の試験・`tests/test_cli.py`・`-m "not slow"`・`-n 2 --dist loadfile`): **960 passed**(落ち 0・17 分 16 秒・ほかの作業木と同時)。pytest は作業木の `src` を読む(`pythonpath` の設定と conftest の `PYTHONPATH`・`engine/decision` の試験が通ること自体が印)。
- 1-3 の試験は `tests/engine/events` で 90 本を収集。土台からの差は凍結の表 `writes_paths_events.json` の 1 行だけ(assert は変えていない)。
- `lint-imports`(作業木の src): 5 kept・0 broken。解析したファイル 198 → 203(`engine/decision` の 5 本が入っている)。

## 8. 抜け道と記録

- (a) 同値: §6。
- (b) C-2: 鍵は 10c の counter(`k19_counters(run_tick_key(day_key0, 刻み, 幅), 体, 候補の数)`=0 語目を空ける・用途名 `decision.present`)で決定的。番号は `present` が最後に振る(作る側の番号は拒む)。答えは `choose` が元の id に戻す。`MockPort.pick` は候補を(語彙の順, id)で並べ直してから引くので提示の並びに左右されない。`ClassicalPort` と `LlmPort` は語で候補を引く(同じ語の候補は `build_candidates` が 1 つにする)。鍵に起床の級は入らない(発注どおり)。
- (c) M2(列化): 列 7 本(i1+i4+i8+i8+i4+i8+i4=37 B)・入力の id 2 本(i8+i4=12 B)。1 呼 61/100/218 B は、2 万行に対する列の容量 32,768 行 × 37 B=60.6 B/呼、入力 2 個は 65,536 × 12 B=39.3 B/呼、入力 8 個は 262,144 × 12 B=157.3 B/呼の和で再計算して一致(60.6・99.9・217.9)。道具 `tools/cause_bytes.py` を HEAD の写しと作業木で回し直し、HEAD 198.4/402.3/1,002.3 B・作業木 60.5/99.8/217.9 B を再現。39 万体 7 日(13.1 呼/体/日)の列の幅での見積り 1.32/2.18/4.76 GB も再計算で一致。`event(i).cause` は 3 型を組み立てる(往復と保持窓の詰め直しの試験あり)。CP12 の門の負の対照 2 本(自分で植えた・HEAD の写しと作業木の両方): (i) 読み口が条件の名から `Experiment` を作り直す素朴な列化を差し込むと、読むときに `PermissionError`(実行時の門が効く)。本物の読み口は gate が作った物そのもの(`is`)を返す。(ii) 記録を pickle で運ぶと `TypeError`(HEAD と同じ。実験の原因が文字列だけに落ちていない)。直接作る形も従来どおり `PermissionError`。
- (d) 判断の出来事: §6(1 判断 1 行・call_id はテープと同じ)。既定 legacy では層を作らず `LlmCall` の行は 0(§6・試験)。
- (e) §5。
- (f) `K19_RECREATED` の `llm.mock`: 理由の文は規律に合う(同じ鍵から同じ番号を選ぶための設計)。ただし用途名ごとの許可で既定の腕の検査も緩む=M2。
- (g) 性能: [arm_pair_j0.json](arm_pair_j0.json) の判断の系の時間から再計算して (35.4−22.87)/65,597=191 µs・(72.51−59.9)/106,565=118 µs で一致。既定の腕は層を作らず、`call` の本体を関数に出しただけ。自分の byte-check(4 並列)の壁時計は HEAD と作業木で ±1.3 秒の中(38.7/37.9・28.5/27.7・26.7/25.5・52.0/53.3 秒)。腕 port の予算の宣言は無い(L2)。
- (h) 艦隊の道は口を通さず数えるだけ(`note_fleet_calls`・計器 `fleet_legacy`)。記録 §3 と §10-6 に限界として書いてある ✓。
- 記録に絶対パス・ホスト名・個人名は無い(`grep`)。記録・JSON・道具は LF。触った共有ファイルの一覧(§1・§9)は `git diff --stat` の 25 ファイルと合う(凍結の表と試験の 9 本も全部載っている)。`_bc/` は検収の時点で作業木に無かった。
- 発注の「台帳は触らない」に対し `docs/design/bridging-ledger.json` に 4 行を足した。口の約束の共通の約束(新しいつなぎは台帳に外す段つき)と試験 `test_code_declarations_and_ledger_rows_are_one_to_one` が求める物なので妥当と読んだ。

## 親に確かめてほしいこと

1. **H1**: 取り込み(1-5 の上への rebase)で `log.py` の `_PROC_CODE`・`_cause_at` を `V.CAUSE_PROCESS_NAMES` に。テキストの併合は衝突しないので見落としやすい。取り込みの後に `tests/engine/rights` と `tests/engine/decision/test_j0_cause_columns.py` を回す。
2. 取り込みで衝突する所(土台・作業木・HEAD の 3-way で確かめた): `bridging-ledger.json`(4 か所)・`run.py`(manifest の末尾=1-5 の `rights` と `decision_port` の並び)・`state_ledger.py`(1 か所)・試験の凍結の表(`manifest_keys_frozen.json`=114 → 115 になる見込み・`test_bridging_ledger.py` の見出しと項の数・`test_manifest_rules_bridges.py`・`test_env_and_sections_10f.py`・`test_t0_tm9_fields.py`・`test_percept_schema.py`)。`llm_bridge.py` と `build.py` は衝突せず、1-5 の役割語の数え(`role_rights`)は `_after_render` の中に入る(引数 `agent_id`・`tick` があるので動く)。`CONFIG_PATHS_SHA256` は 1-5 で変わっていないので作業木の値のまま。
3. M1(判断ごとの源の記録の形)と M2(既定の腕の K19 の守り)。
4. 実装役の §11 の 1〜5(「その他」の既定=値なし・候補の id の読み方・外す段 1-8 の 3 行・候補の集合が語彙のまま・成長の宣言の段)。
