# 第 3 期 3-2 TM T1 計算のまとめ(tm32)の検収の記録

> 検収役(Opus 5.5)。実装は見ていない。対象は作業木の枝 `3-2/tm-t1-batching` の未 commit の変更(土台 `d35a9b6`・`git diff --stat` の 18 本と新しい 6 項=`engine/batching.py`・`tests/engine/batching/`・`tests/tools/test_batch_width_gauge.py`・`tools/instruments/batch_width_gauge.py`・記録 `tm32/`・作業用の `_bc/`)。本体の HEAD は `44cfba5`。
> **封印の規律**: 封印の層と検証側の錨の値は読んでいない(HEAD の写しには `byte_check_10e.py` の `HEAD_TREE_FILES` のとおり錨 3 本を `git archive` で写しただけ)。`tests/c7` は回していない。作業用の置き場は `_bc_review/`(終わりに消す・本体の data へのつなぎは .NET の `Directory.Delete` で外す)。

## 判定

**条件つき受入**。結果不変は自分の 4 構成(本体 `44cfba5` の写しと作業木で 25 欄とも同じ)、進行役だけを HEAD の刻みのループに戻した独立の再計算、W=5 の 1 構成、版をまたぐ再開で確かめた。負の対照(境目で届ける 80 秒の事象)も自分の合成の世界で再現した。
条件は中 M1 の 1 つ。窓の待ち行列 `WindowQueue` に実行時の守りが無い(1-3 の教訓の未適用)。取り込みの前に守りと負の対照の試験を足すこと。低 L1〜L9 は記録の直し・試験の追加・親の判断で済む。

## 欠陥(重さ順)

| 番 | 重さ | ファイル・行 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `src/shibuya/engine/batching.py` の `WindowQueue`(133 行〜・`__init__` 149 行・表 164・166 行・`register` 179 行) | 実行時の守りが無い。`__setattr__`・`__delattr__` が無く、表 `_bw_kinds` は素の dict、`_bw_rank` は書ける ndarray で、`register` はランの途中でも呼べる。一時の写しで植えた 7 通り(`_bw_head`・`_bw_carry`・`width_ns` の付け替え・`_bw_rank[0]`・`_bw_kinds`・`_bw_meter` の書き・ランの途中の `register`)が全部通った(`_bc_review/plant_guard.py`)。待ち行列は進行役のループそのもの(`_bw_head`・`_bw_carry` を書けば刻みが飛ぶ・繰り返す)なので、行 BW が軸 1 diag でも結果を動かせる。系の中からの書きは段 B が捕まえる(植えた書き → 違反 `[5, "body", "BW:batching._bw_meter"]`)が、試験のときだけの網で、実行時の守りの負の対照の試験も無い | `__setattr__` で組み立ての後の付け替えを禁じる(状態の欄は中で `object.__setattr__`・3-3 の `ExperimentLayer`・2-2 の `ProximityLayer` の形)。`__delattr__` も禁じる。最初の `run_window` で種類の表を閉じる(`_bw_rank.setflags(write=False)`・`_bw_kinds` を `MappingProxyType` に・閉じた後の `register` は `AttributeError`)。種類の名の重複も `register` で落とす(`manifest_fields` の `kinds` は名で引くので、同じ名は黙って上書きになる)。試験: 外からの付け替え・閉じた後の `register`・系の中からの書き(段 B の違反)の 3 本の負の対照 |
| L1 | 低 | `src/shibuya/engine/systems/conductor.py` の `declared_check`(40〜62 行)・`WINDOW_MARK`(70 行) | `(window)` は系ではないので、宣言の検査 `check` は `specs.get(name) is None` で何でも通す(`agents.cell`・`O39:conv.sessions` も真=`plant_guard.py`)。`(window)` の差が行 BW だけであることは試験 `test_window_changes_are_attributed_to_the_window_mark_and_fingerprints_do_not_move` が合成の 1 構成(150 刻み・W=60/10)で見るだけで、`SHIBUYA_SYSTEMS_CHECK` の段 B(`_conduct_checked`)は見ない。`TICK_HEAD` も同じ素通り(本段の前から) | `check` で `name == WINDOW_MARK` のときは `BW:` で始まる鍵だけを通す(負の対照: `(window)` に `agents.cell` の差を植えて落ちる)。`TICK_HEAD` の素通りは親が別に決める |
| L2 | 低 | `tools/instruments/batch_width_gauge.py`(62 行 `DEFAULT_REF_WIDTH = 60`・213 行 `_CHILD` の `/ 1e9`)・`tm32/tools/perf_tm32.py`(`STEPS = 1_440`) | 時間の直書き(T0 の規則)。src の AST の試験の外なので落ちない | `STEP_SECONDS`・`NS_PER_SECOND`・`STEPS_PER_DAY` を `core/time_consts` から読む(道具の子プロセスは shibuya を import する) |
| L3 | 低 | `byte_check_tm32_w{30,10,5}_vs_w60.json` | 10e の `SWITCH_ENV` に `SHIBUYA_BATCH_WIDTH_S` が無く、`one` も manifest の `batching` を出さない=JSON には幅がラベルにしか残らない(`env: {}`)。腕が本当に効いていたかを JSON から読めない。検収では W=5 のランを別の道で回し、manifest の `batching.windows` 17,280・`run_kind` arm を見た(§6) | 本体の 10e の `SWITCH_ENV` に `SHIBUYA_BATCH_WIDTH_S` を足すか、`one` に `batching.width_s` を出させる(本段の編集の範囲の外=親) |
| L4 | 低 | 記録 §0 の最後・§5-1・§12 の 5 つ目 | 「HEAD の写しに rules-table.json と OSM の 2 本が要る・10e の docstring は古い」は、本体 `44cfba5`(2-3c の検収 L4)の 10e で `HEAD_TREE_FILES` と docstring に直っている。土台 `d35a9b6` の時点の発見としては正しい | 取り込みのときに「本体では 2-3c の L4 で直った」の 1 行と、rebase の後の土台の hash を足す |
| L5 | 低 | 記録 §5 の表の「再開」の行 | 「W=60 と W=30 で、刻み 1,440 と刻み 2,211 で止めて再開」とあるが、`two_day_tm32.json` の再開は `w60_day`・`w60_mid`・`w30_mid` の 3 本で、W=30 の日の境目(1,440)は無い(合成の世界の試験 `test_two_days_and_resume_match_the_straight_run_for_the_arm` にはある) | 「W=60 は 1,440 と 2,211・W=30 は 2,211(日の境目は合成の世界の試験)」に直す |
| L6 | 低 | `tests/engine/batching/test_window_queue.py` | 窓の待ち行列の輪(2 刻みぶん=`HORIZON_STEPS`)の外の予約が `Scheduler` の遠未来の heapq を通って輪に戻る道を、どの試験も通らない(合成の試験の予約は全部輪の中)。検収の一時の写し(`_bc_review/far_future.py`=5 刻み後・1 時間後・窓の中から 3 刻み後と 7 刻み後)では W=60・30・10・5・1 で順も時刻も同じ・終わりに残り 0 だった。上限に当たった後の `manifest_fields()` の `carried`・`cap_hits` を直接見る試験も無い(計器は同じ dict) | 遠未来の予約の単体を 1 本(T2 で会話の番や体の変化の予約が入ると主な道になる)。上限の単体に `manifest_fields()` の 2 欄を足す |
| L7 | 低 | 記録 §3・つなぎの台帳 `DOC-tm32-same-time-body-order` | 同じ時刻の束を処理している間に同じ時刻へ足した事象(0 の遅れ)は、束の残りの後に回る=宣言の「時刻 → 体の番号」が崩れる。例: 10 秒の束 [体 5 の A・体 9 の B] で体 5 の処理が体 3 の A を 10 秒に足すと、順は 5 → 9 → 3(W=60・10 とも同じ=幅には依らない・`_bc_review` の一時の写し) | 規則として記録 §3 の表と台帳の行の `what` に 1 文足す(「処理の中で同じ時刻に足した事象は、その時刻の束の後に回す」)。T2 で会話の 0 の遅れの返事を入れるときに決め直す |
| L8 | 低 | 予算 P4・記録 §8 | 窓の待ち行列の手間の実測(刻みあたり µs)はあるが、性能の回帰の試験(CLAUDE.md §4「性能予算…テストでゲート」)と ms/シミュ分@基準規模の宣言の行が無い。手間は体の数に依らず、W=60 で刻みあたり約 0.04 ms(検収の測り=§8)=P2 の 5 ms/フレームの 1% 未満 | 親の判断: slow の印で「待ち行列だけの 1 日・W=1 で上限 X ms」の試験を 1 本足すか、記録の宣言で足りるとするか |
| L9 | 低 | 作業木の直下の `_bc/` | `.gitignore` に無い(実装役の申告どおり)。中につなぎ(junction)は無い(深さ 2 まで見た) | commit の前に親が消す(`git add` は明示の道筋だけなので混ざりはしない) |

## 1. 結果不変 ✓

- **実装役の 19 構成**: `byte_check_tm32.json` は 19 構成 × 25 欄で全部「同じ」(a=HEAD `d35a9b6` の写し・b=作業木の W=60)。`byte_check_tm32_junction.json`(写しの根に本体の data へのつなぎ+規則の表)も 19/19。W=60 の side は `env: {}`・CLI の既定 `None` → 腕の既定は今の道(W=60)。
- **自分の 4 構成**(`w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`・5,000 体・seed 1・1 日・テープつき): 本体 `44cfba5` の `src` と、`HEAD_TREE_FILES` の追跡ファイル 8 本と `w6-regen-2026-09-28` を `git archive` で写し、`data` は本体の data へのつなぎ(`New-Item -ItemType Junction`)にした。`HEAD_TREE_FILES` の 11 項が写しと作業木の両方にあることを先に確かめた(規則の表は作業木と同じバイト)。両側とも `--src` で渡し(`SHIBUYA_BUDGET_MD` も両側同じ)、cwd は作業木(data は本体へのつなぎ=両側とも本体の v2 の資産)。`compare` → **4/4 構成で 25 欄とも同じ**(`_bc_review/cmp_head_vs_wt.json`)。

| 構成 | final | 呼数 |
|---|---|---:|
| w6_v3_default | `b8eadcb51e8705e7` | 64,528 |
| w6_v3_activity_off | `c88ba9104f45f897` | 50,006 |
| w6_v1_default | `e1288e092ddaca86` | 51,655 |
| v3_mem_rel | `768b2262e3b0999e` | 67,794 |

  どれも実装役の 19 構成の値と同じ。実装役の HEAD は `d35a9b6`、検収は `44cfba5` なので、その間の `c252892`・`e7bbc3e`(2-3c)もこの 4 構成の結果を動かしていない。
- **版をまたぐ再開**: HEAD の写しの src で 2 日のラン(合成の世界 30 体)を刻み 1,811 で止めて書いた状態のファイルを、作業木の src で再開した。final は HEAD の通し・作業木の通しと同じ(`c777add0…`)、窓は 1,069(=2,880 − 1,811)。状態のファイルに行 BW が入らず、既定の指紋も変わらないので、前の版の状態のファイルから続けられる。

## 2. 口と約束 ✓(M1・L6 を除く)

段 3-2 の口の約束は 10-13 の口の約束の文書に無い(第 1 期だけ)ので、発注文の「作るもの」を約束として読んだ。

| 口 | 実装 | 違い |
|---|---|---|
| まとめの幅の抽象 | `engine.batching.WindowQueue`(`register`・`schedule`・`run_window`・`manifest_fields`・`head_ns`・`window_counts`・`pending`)・進行役 `conduct` の窓のループ | 発注の名 `step_ns` は進行役の刻みの幅の局所の名に残り、窓の幅は `width_s`/`width_ns`(「tick」を避けた名) |
| 幅の腕 | `--batch-width-s`(`choices`=刻みの幅の約数 12 通り・既定 `None`=環境変数か 60)・`SHIBUYA_BATCH_WIDTH_S`(import のときに読む・誤りは import で落ちる)・`arm`・`set_arm`・`is_default`・`parse_width` | 発注の `{60,30,10,…}` を約数 12 通りに広げた(仮採用 §9-1 の 1) |
| 指紋とランの種類 | 既定は指紋に入れない・腕のときだけ `batch_width_s`・`cli.run` で腕は `arm` | なし |
| manifest | 末尾に `batching`(設定 8・観測 12)。発注の 4 欄=`width_s`・`windows`・`carried`・`cap_hits` | 発注は「観測」。設定と観測の混ざった辞書にした(仮採用 §9-1 の 6・`CONFIG_PATHS_SHA256` を更新) |
| 状態台帳 | 行 `BW`(外・diag・discardable)・持ち主 `batching` | なし |
| 道具 | `tools/instruments/batch_width_gauge.py`(`run`・`table`・`markdown`) | なし |
| つなぎの台帳 | 4 行(発注の 3 行+上限の値) | なし |

約束の項と試験の対応(無いものだけ書く): 遠未来の予約の道(L6)・上限の後の manifest の 2 欄(L6)・実行時の守り(M1)。HEAD の写しとの比べは記録(byte-check・探り)にあり、試験には「前のループの並びを組み立て直して比べる」1 本がある。

〔決定〕の反映: TM3 (f)(窓の中は時刻順に順番に・窓の中に予約した事象は同じ窓で・持ち越す・上限は安全装置で記録)✓・TM3「1 つの会話の中はまとめない」はつなぎの台帳の行で T2 へ ✓・TM4(既定の幅は試験で・正解=まとめ無しの時刻順・(f)(g)・遅刻と待ち合わせの置き場)は道具の形 ✓・TM6 の T1(幅 60 秒で今と同じ・試験の道具)✓・TM1「電話は窓の境目で届ける」は届け方 `boundary`(T1 の世界では使わない=仮採用 §9-1 の 5)✓・「tick」の語は新しい識別子と docstring に無い ✓。

## 3. 発注文の各項

| 項 | 判定 | 根拠 |
|---|---|---|
| 1 まとめの幅の抽象 | ✓ | §8(b)。W=60 で 19/19・自分の 4/4・独立の再計算 |
| 2 幅の腕 | ✓ | W=30・10・5 で 19/19(L3 の注)・自分の W=5・窓の中の順と持ち越しの単体 |
| 3 TM4 の道具 | ✓ | 表の形・`salt_compare.paired_stats` の `width_base`・(f)・置き場・合成の 3 つの幅の単体 7 本(L2) |
| 4 manifest・状態台帳・凍結 | ✓ | §5 |
| 5 つなぎの台帳 4 行 | ✓ | `remove_at` T2・conf は 4 行とも expedient(語彙は expedient/mechanism の 2 つ)・`remove_basis` は plan 2・inferred 2・`declared_in` は記録(実在) |
| 受入の試験 | ✓ | 新しい 43 本(20+16+7=数えて合う)。§7 |
| 記録 | △ | 中身は揃う。L4・L5 の直し |

「できなかったこと」の申告(遅刻と待ち合わせは置き場・10e の docstring は古い・`_bc/` は `.gitignore` に無い)は実態と合う。10e の件は本体で直っている(L4)。

## 4. 守り

- **書く口** ✓: 書くのは `schedule`・`run_window`・`register` だけ。src で `layers.batching` を触るのは進行役だけ(grep)。系の中から待ち行列に書くと段 B が違反にする(植えた書き → `[5, "body", "BW:batching._bw_meter"]`)。`window_counts` は写しを返す。
- **実行時の守り** ✗(M1): 外からの付け替え・表の書き・ランの途中の `register` が全部通る。
- **負の対照**: 段 B の帰属の試験と、境目で届ける種類の順の試験はある。実行時の守りの負の対照は無い(M1)。`(window)` の素通り(L1)。

## 5. 宣言と凍結 ✓

- 系の `writes.paths`/`writes.soa`: 行 BW を書く系は無い(`(window)` は系ではない)ので、宣言の変更は要らない。`systems/table.py` は触っていない。
- 状態台帳の行 BW: 外・`DIAG`・`DISCARDABLE`・`dead=False`・`arm=""`。`WindowQueue` の欄 13 個=道筋 4(`_bw_sched`・`_bw_carry`・`_bw_head`・`_bw_meter`)+除外 9(定数 4・参照 2・窓の中だけの作業の値 3)で、漏れも重なりも無い。`OWNER_CLASSES`・`OWNER_NAMES`・`Layers.batching`・`hash_owners` はどれも末尾に足しただけ。`LEDGER_VERSION` は上げない(3-3 の X と同じ・どちらのハッシュにも状態のファイルにも入らない)。
- 凍結の表は増えた分だけ: `manifest_keys_frozen.json`(+`batching`)・末尾の並びの試験 5 本(+`batching`)・`test_env_and_sections_10f.py`(`TM32_KEYS`・`CONFIG_PATHS_SHA256` `417f0818…` → `564d5c72…`)・`test_state_ledger_10b.py`(113 → 114・204 → 205・鍵の並びの末尾に BW・BW の 2 軸)。消した行・変えた値は無い。
- manifest の既存の欄: byte-check の 25 欄は全部同じ。値が動くのは、表そのものを載せる `manifest_sections`(`batching` の道筋が増える)と `bridges_count`(つなぎの台帳の active の行が 4 増える)だけ=前の段と同じ型の「列追加」。

## 6. 同値(独立の再計算)✓

- **方法**: 作業木の src のまま、一時の写し(`_bc_review/recalc.py`)で `conductor.conduct` を HEAD の刻みのループの本体の写し(`for T in range(t_begin, t_end)`・同じモジュールの `run_system`・`tick_plan`)に差し替え、`w6_v3_default`(5,000 体・seed 1・1 日)を回した。窓のループ(W=60)と W=5 のランを別のプロセスで並べ、final(64 桁)・呼数・4 つの checkpoint の 2 本のハッシュ・日の終わりのハッシュ・行動の件数を比べた。
- **結果**: 3 本とも全部同じ(final `b8eadcb51e8705e7…`・64,528 呼)。W=5 の manifest は `width_s` 5・窓 17,280・事象 1,440・処理 1,440・持ち越し 0・上限 0・`run_kind` arm(腕が効いていた)。同じ木で進行役だけを替えた比べなので、差があれば進行役の書き換えに帰属できる。
- 10e の side でも W=5 の `w6_v3_default` は W=60 と 25 欄とも同じ。
- 実装役の試験は、腕の on/off(W=30・10・5・1 で系の呼ぶ順・final・checkpoint)・前のループの並びの組み立て直し・2 日と再開を読んだ。

## 7. 試験

- 範囲(発注文の 16 項=`tests/engine/batching`・`tests/tools/test_batch_width_gauge.py`・`tests/engine/systems`・`time`・`events`・`bridging`・`rights`・`tools`・`tests/perception`・`tests/engine/experiment`・`tests/llm`・`test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/engine/multiday`・`-m "not slow"`・`-n 2 --dist loadfile`・作業木): **1,532 passed・failed 0・skipped 0**(22 分 32 秒・warning 1 件=既知の W9 の影の日の近似)。data が無くて飛ばした試験 0 件。
- `lint-imports`(作業木の src・230 ファイル): 5 契約とも守られている・0 broken。
- `tests/c7` は回していない。全体は親が回す。
- 検収の一時の写し(`_bc_review/` の `negctl.py`・`plant_guard.py`・`far_future.py`・`recalc.py`・`cross_resume.py`)は作業木の追跡ファイルを変えずに作業木の src で回した(`git status` の M の 18 本は始めと同じ)。

## 8. 本段に固有の確かめ

**(a) 既定(W=60)の不変** ✓: §1。2 日と再開は実装役の `two_day_tm32.json`(final `b346bb6e…`・138,946 呼・L5 の注)と自分の版をまたぐ再開。系ごとの指紋で除いたものの理由は妥当: 行 BW は HEAD の写しに無い行で、`(window)` に帰属する差は BW だけ(行を外すと entries の数が 7,051/15,600/17,703 で HEAD と同じ)。日次の記録の `bridges_count` はつなぎの台帳の active の行の数(本段で 4 行足した)で、挙動ではない(ec21 と同じ扱い)。

**(b) 進行役の書き換え** ✓: 前後の差分を読んだ。刻みの事象の処理 `on_step` の中身は、前のループの 1 回の文の並び(`TickCtx.of` → `TICK_HEAD` → `scratch.reset` → `events.begin_step` → 日の頭 → 系の表 → 日の締め)と同じで、先頭に「次の刻みの事象の予約」1 行が足されただけ(`TICK_HEAD` の前=待ち行列の変化は `(window)` に帰属)。`T = t_ns // step_ns` で、W は刻みの幅の約数なので刻みの事象は窓の頭に乗る=`TickCtx` の時刻は前の `t_ns` と同じ。W は `batching.arm()`(`STEP_SECONDS` から)。新しい src に時間の直書きは無い(`1 << 24` は上限・`64` は種類の数)。「tick」が出るのは既存の口の名(`Scheduler` の `start_tick`・`tick_seconds`・`horizon_ticks`・`run_day` の `ticks`)と既存の境目の名 `TICK_HEAD` だけ。

**(c) 窓の中の順と持ち越し** ✓: 並べ替えは `np.lexsort((seq, rank, agent, t))`=時刻 → 体(世界 −1 が先)→ 順位 → 番号。同じ種類の続きは 1 回の処理(配列)。窓の中の予約は同じ窓で回り、上限 2^24 で持ち越して数える(止めない)。0 の遅れの例外は L7。**負の対照を自分で再現した**(`_bc_review/negctl.py`・実装役の試験を写さずに組み直した合成の世界=刻みの事象+体 2 の 95 秒の事象+刻み 60 秒の処理が 20 秒後に足す「境目で届ける」事象):

| W | 80 秒の事象が届く時刻 | 95 秒の事象より前か | 遅れの最大 | 窓の中で時刻どおりの正解と同じか |
|---|---:|---|---:|---|
| 60 | 120 秒 | いいえ(順が入れ替わる) | 40 秒 | いいえ |
| 30 | 90 秒 | はい | 10 秒 | いいえ |
| 10 | 80 秒 | はい | 0 | はい |
| 5 | 80 秒 | はい | 0 | はい |

  届け方を「窓の中で時刻どおり」にすると、W=30・10・5 とも W=60 と同じ順(10-03 §7-5)。

**(d) 幅の腕** ✓: 実装役の W=30・10・5 の 19/19(L3 の注)。自分の W=5 × 1 構成も final が W=60 と同じ(§6)。W は刻みの幅の約数に限る(`WIDTHS_S`・`parse_width`・CLI の `choices`・`WindowQueue` の検査・試験)。

**(e) 抜け道** △: 外から書ける(M1)。`(window)` の後の待ち行列の変化は系に請求されない(試験と植えた書きで確かめた)。`Scheduler.reserve_seq` を呼ぶのは窓の待ち行列が中に持つ `Scheduler` だけ(grep)=起床の予約器の番号・行・件数は動かない。輪を 2 刻みぶんにしたのもその中の `Scheduler` だけで、エンジンの起床の予約器の地平(1,440)は変わらない。遠未来の heapq の道は試験に無いが、一時の写しで幅に依らないことを見た(L6)。行 BW は既定のランでも空ではない(次の刻みの事象 1 つ・頭・計器)が、刻みの番号から作り直せる派生で、進行役がランの始めに作り直す=状態のファイルに入れなくてよい(試験の再開と版をまたぐ再開で確かめた)。T2 で軸を見直すことは行の注とつなぎの台帳にある。

**(f) 道具** ✓: `table` は正解の幅との対の差・`width_base`(正解の腕の salt 間の幅 t·s/√n)・`paired_width`・(g)・(f)・候補・置き場の null と注。`run` は子プロセスに環境変数で幅を渡し、母集団の seed を固定する。単体は合成の記録 3 つの幅 × 6 salt。(g) の幅に `width_base` を当てたのは実装役の構成(expedient と道具の docstring にある)=TM4 の「salt 間のばらつき」の読みとして親が確かめる。時間の直書きは L2。

**(g) 性能** ✓(L8): 実装役の測り方は「系を呼ばない空の刻みの事象で 1 日ぶんの窓を回す」で、壁時計の前後は並行の段の負荷で読めないと宣言している(3 回の幅 44〜82 秒)。検収でも同じ形で測った(pytest 2 並列が同時に回る中・5 回の中央値): 刻みあたり W=60 41.7 µs・W=30 44.8・W=10 52.2・W=5 60.4・W=1 132.7 µs。実装役の値(43〜63・65・74・89・178 µs)と同じ桁で、刻みあたり約 35 ms の 0.1〜0.4%。体の数に依らない。

**(h) 共有ファイルと rebase の見込み** ✓:
- 本体 `44cfba5` への取り込み: 変えた 18 本を 1 本ずつ 3 方向で合わせた(土台 `d35a9b6`・本体 `44cfba5`・作業木・`git merge-file`)=**衝突 0**。17 本は本体で `d35a9b6` から変わっていない。`docs/design/bridging-ledger.json` は本体(2-3c)が途中の行を直し 1 行足し、本段は末尾に 4 行=自動で合う(active の行は 344 + 4 = 348 になる)。
- 3-1(作業木は読んでいない=発注文の範囲から)と重なる見込み: `run.py` の manifest の辞書の末尾・`manifest_sections.py` の `PATHS` の末尾・`state_ledger.py`(`_EXT` の末尾・`OWNER_CLASSES`・`EXCLUDED`・docstring の行の一覧・版の注)・3-1 が持ち主を足すなら `boxes.py`(`OWNER_NAMES`・`Layers`)と `state_io.py`(`hash_owners`)・`bridging-ledger.json` の末尾・`manifest_keys_frozen.json`・末尾の並びの試験 5 本・`test_env_and_sections_10f.py`(末尾の鍵と `CONFIG_PATHS_SHA256`)・`test_state_ledger_10b.py`(数と鍵の並び)・`cli.py`(引数の並び)。**`CONFIG_PATHS_SHA256` はどちらかを選ぶのではなく、合わせた後の表で計算し直す**。末尾の並びは「先に取り込んだ段 → 後の段」。
- 記録に絶対パス・ホスト名・個人名は無い(grep)。記録のファイルは全部 LF。記録 §11 の「触った共有ファイル」は `git diff --stat` の 18 本と合う(`table.py` は触っていない=正しい)。
