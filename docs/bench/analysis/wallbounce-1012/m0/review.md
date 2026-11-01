# 第 1 期 1-6 記憶の器 M0 の独立検収

- 検収役 Opus 5.5(実装は見ていない)。作業木の枝 `1-6/memory-m0`(基点 `136fdbb`・未 commit)。本体の HEAD は `fbe2c06`(`136fdbb` からの差に `src` を含まない=src は同じ)。
- 正: 口の約束 `docs/design/v2-foundation-contracts-2026-10-13.md` の「1-6 記憶の器 M0」と冒頭の共通の約束・実装役への発注文・実装役の記録 [README.md](README.md)。
- 作業用の出力(テープ・side の JSON・試験のログ)は作業木の `_bc_review/` に置き、終わったら消した。比べた数はこの文書に写した。
- 判定: **条件つき受入**(高 0・中 2・低 10)。結果不変と同値は独立に確かめられた。条件は中 M1(器の値の食い違いを実行時に落とす)と中 M2(仮の行=つなぎを 1-4 の台帳に「外す段」つきで載せる。親の作業)。

## 1. 結果不変 ✓

- 実装役の byte-check 19 構成(`byte_check_m0.json`): 19/19 構成で 25 欄とも同じ(`moved` 0)。腕は既定の `mem`、m0 の側は作業木の src。置き場を移した後の 4 構成(`byte_check_m0_relocated_4cfg.json`)も 4/4 で 25 欄とも同じ。
- 腕 on の 4 構成(`byte_check_m0_arm_on.json`): w6_v3_default(記憶 off)は 25 欄とも同じ。記憶の 3 構成で動いたのは `calls_column_names`(21 → 22 列・末尾に `recalled_event_ids`・前の 21 列の並びは同じ)と `calls_columns_sha`(食い違うのは `recalled_event_ids` の 1 列だけ)の 2 欄だけ。
- **検収役の byte-check 4 構成**(`w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`・5,000 体・seed 1・1 日・テープつき): head=本体 HEAD の src の写し(`git archive`)、m0=作業木の src(`src_is_worktree` 真・腕は既定)。`compare` で **4/4 構成・25 欄とも同じ**。final は `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`。m0 の側の `calls_column_names` は 4 構成とも 21 列。
- 検収役の腕 on(`SHIBUYA_MEMORY_STORE=events`・v3_mem_rel): final `73a78288ab5e1498`(off と同じ)。動いたのは `calls_column_names`(22 列目 `recalled_event_ids`)と `calls_columns_sha`(`recalled_event_ids` だけ)。前の 21 列(`recalled_rows`・`recalled_first_tick`・`recalled_kind`・`recalled_object`・`b5_text`・`prompt_hash` を含む)の sha は 69,111 呼び出しの全部で同じ。

## 2. 口と約束 ✓(違いは下に)

| 口の約束 | 実装 | 判定 |
|---|---|---|
| 置き場 `engine/memory/store.py` | `engine/memory_store.py`(1 本のモジュール) | △ 親の判断(記録 §12 仮採用 1)。`engine/memory.py` に `__path__` の細工は無い・`engine/memory/` は無い |
| 行=`event_id`+`strength`+`annotation`+`origin`+`shown` | `_ms_ev_t_ns`/`_ms_ev_seq`(目印)・`_ms_n`/`_ms_imp`/`_ms_first_ns`(強さ=3 列)・`_ms_note`(注釈)・`_ms_origin`(None/legacy)・`_ms_shown_ns`(録画) | ✓(`strength` は 1 欄でなく 3 列。`remember` の `strength` 引数は重要度の base) |
| `mem_*` は残す・新しい器は腕 `--memory-store events` | 腕 `mem`(既定)/`events`・環境変数 `SHIBUYA_MEMORY_STORE`・CLI | ✓ |
| LLM に見せるのは言葉と中身の粗さ(MR-0) | `MemoryView.clarity`(はっきり/うろ覚え)・`grain`(そのまま)。回数・重要度・A・score は持たない | ✓(ただし低 L5) |
| `render_memories(views) -> str` | `render_memories(views, *, clock, poi_names, place_ids, now_ns=0, ns_per_step=…)` | △ 描くのに資産と時計が要るので引数が増えた(1-2 の結線のときに合わせる) |

約束と試験の対応: (1) 既定の final 不変=byte-check(19+4)・(2) 腕 on で同じ候補=`test_m0_recall_equivalence.py`(合成の世界は全部の想起・5,000 体は `slow`)・(3) 録画が列に増えるだけ=`test_m0_shown_recorded.py`。〔決定〕「版 4 の中で列を足してよい」は反映(版の印は `shibuya.tape/4` のまま)。対応する試験の無い約束は無い。

## 3. 発注文の各項

| 項 | 判定 | 根拠 |
|---|---|---|
| 1 器(行の欄・SoA・体ごとの範囲・書く口 2 つ・`__setattr__`・`recall`・`MemoryView`) | △ | 欄・範囲・読み口は ✓。書く口は `remember`・`mark_shown` のほかに `rebuild`(M0 を書く)・`take_shown`(M0R)・`recall`(M0R の計数)がある(記録と docstring に明記)。`__setattr__` の守りに `del` の抜け道(低 L1) |
| 2 腕 `--memory-store events`・legacy の仮の行・on/off で同じ候補 | ✓ | 器の行は 100% legacy(記録 §5)。同値は §6 で独立に確かめた |
| 3 `shown` の録画・腕 on だけ列を 1 つ・既定 off で列を足さない | ✓ | 列の名・型・既定の値(空の list)は記録 §6。既定の 21 列は byte-check で確かめた |
| 4 `render_memories`(今の描き方とバイト一致)・結線は 1-2 の後 | ✓ | 試験のほかに、検収役も別の構成(seed 7・`memory_n=4`・店の記憶 on)で 761/761 の描画が一致 |
| 5 manifest(腕の名・行数・origin の分布) | ✓ | `memory_summary.memory_store`。既定のランの manifest は葉が 1 つ増える(低 L7) |
| 記録・道具 | ✓ | README §0〜§12・`tools/recall_equivalence_m0.py`(絶対パスなし) |

「できなかったこと」の申告(艦隊の道の録画の試験・気づきの記憶を記録の目印にする配線・記録の保持と再開・MR16 (c) の器の外の録画・`Percept` への結線)は実態と合う。

## 4. 守り △

- 書く口: 行(M0)を書くのは `remember` と `rebuild`。録画(M0R)は `mark_shown`・`take_shown`・`recall`(計数)・`remember`(新しい行の印)。どの口も `_check_permit`(系の `writes.paths`)を通る。
- 検収役の探り(一時のプロセスの中だけ): 欄の付け替え `ms._ms_n = …` は落ちた(✓)。通った抜け道は次のとおり。
  - `del ms._ms_origin` のあとに付け替える(`hasattr` が偽になり `__setattr__` を通る)=低 L1。
  - `ms.tape_on`・`ms._ms_last` の付け替え(`_REBIND`)=低 L4。
  - 配列の中身・注釈の dict の直書き=記録 §12 の限界どおり(1-3 の L2 と同じ)。
  - `rebuild` を `M0` だけの宣言で呼ぶと、M0R の控えと計数も消す(検査は `M0` の 1 本だけ)=低 L3。
  - `tape.ARM_COLUMNS`(閉じた表)は素の dict で、名を足せる=低 L2(1-3 の L7 の教訓=`MappingProxyType`)。
- 負の対照: 宣言を外すと書いた所で落ちる(`test_m0_writes_declared.py` の 2 本・`test_m0_store_schema.py` の宣言の外 3 通り+片方だけの宣言)。検収役は器を一時的に壊して次を確かめた。
  - 追い出しの score を逆にした → `_write` の行の食い違いの検査で `RuntimeError`(✓)。
  - 想起の順を逆にした → 自前の突き合わせで 635/787 呼び出しが食い違った(突き合わせは効く)。**final は同じだった**。
  - 新しい行の重要度から 1 を引いた → 行の番号は同じなので `_write` は落ちず、114/787 呼び出しの想起が食い違った。**final は同じだった**(中 M1)。

## 5. 宣言と凍結 ✓

- `writes.paths`: memory・decide・llm_receive に `M0*:mem_layer.memory_store.*`・drain に `M0R:mem_layer.memory_store.*`。ほかの系は器を宣言しない(`test_systems_declare_the_store_paths`)。段 B(腕 on・全部の欄)で宣言の外 0。`writes.soa` は変わらない(器は SoA を書かない)。
- 状態台帳: 行 M0(軸 1 no・軸 2 derivable・中身は全部 hash_skip)と M0R(diag・discardable)。full/behavior の項に `memory_store` は入らない。O87 の items に `bridge.tape._arm_values`・除外に `arm_columns`(参照)と器の設定 10 個。持ち主の網羅は AST と実行時とも漏れ 0。版は `state-ledger/10e-ret` のまま(1-3 と同じ仮採用)。
- 凍結の表(`writes_soa_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`・`manifest_keys_frozen.json`・`writes_paths_events.json`・`CONFIG_PATHS_SHA256`)は変わっていない。
- manifest: 検収役は合成の世界(60 体・720 刻み・記憶+関係+同席+店の記憶)を HEAD の src と作業木の src(既定の腕)で回し、平らにした葉を比べた。final は同じ(`f546636950155777`)。既存の葉の値は全部同じで、増えた葉は `manifest_sections.paths.memory_summary.memory_store` の 1 つだけ(2,271 → 2,272)。

### 5-1. 行 M0・M0R の宣言の妥当性(EXTRA (f))

- 台帳の定義は「軸 1 `no` = 読まれない(**または派生として入れないと宣言した**)」。知覚の `heading`・`task_flag` が先例。M0 の器は記憶の表 `mem_*`(behavior・required)と要旨 O8 の写しで、`rebuild_memory_store` がそこから作り直す。だから「派生=no・derivable・中身は hash_skip」は台帳の語の中で筋が通る。M0R(録画・控え・計数)の読み手はテープの列と manifest だけで、diag・discardable は妥当。
- 器の中身が final に効かない根拠は次の 3 つ。(1) 既定の腕では器を作らない(byte-check 19+4)。(2) 腕 on では想起が表と同じ。5,000 体の腕 on で、描画の材料の列(`recalled_rows`・`b5_text`・`prompt_hash` ほか)の sha が全部の呼び出しで同じだった。(3) 再開は表から作り直して通しのランと同じ(`test_synthetic_two_days_resume_rebuilds_the_store`)。
- 弱い所(中 M1): mock では final が想起の中身に鈍い(§4 の負の対照で、想起が食い違っても final は同じ)。記録 §0・§9 の「腕 on の final が同じ(想起が同じなので)」は同値の根拠にならない。根拠は §6 の直接の突き合わせと、テープの前の 21 列の一致。さらに、実行時の検査は行の番号しか見ない。腕のランで器の値が表からずれても、ハッシュ(hash_skip)にも final にも出ない。

## 6. 同値(EXTRA (a))✓

- 実装役の方法: 腕 on のランの中で `MemoryLayer.recall` を包み、抜き取った刻みで「器を外した表の道」と「器の道」を両方引いて比べる。`recall_equivalence_m0.json` の数は記録 §4-2 の表と合う。v3_mem_rel 9,787 呼び出し・17,779 項、v3_mem_store 9,214・16,501(店の行 1,600)、v3_classical_mem_rel 15,115・25,319。合わせて 34,116 呼び出し・59,599 項・食い違い 0。final・呼数・想起の計数も on/off で同じ。
- **検収役の独立の再計算**(方法が違う): 腕 off のランと腕 on のランを**別々に**回し、`MemoryLayer.recall` の戻り(1 回だけ・包むだけ)を呼び出しの順に全部控えて、2 本の列を突き合わせた。記憶の表を小さくして追い出しを起こした。ランの終わりに、器の全部の行(仮の出来事 5 列・回数・重要度・最初の時刻・目印の時刻と seq=−1−番地・出どころ・空の行・注釈とその順)を、記憶の表と要旨から自前で作った期待と比べた。テープは列の数と前の 21 列の一致を見て、目印の文字列 `"t_ns:seq"` を自前で解いた(seq=−1−(体×N+行)・0 ≤ t_ns ≤ 呼び出しの時刻・店の行は空文字)。合成の世界・60 体・720 刻み・v3・記憶+関係+同席。

| memory_n | seed | 店の記憶 | 呼び出し | 項(うち店の行) | 追い出し(表=器) | 列の一致 | 器=表 | テープ(列・目印) |
|---|---|---|---|---|---|---|---|---|
| 6 | 3 | on | 787 | 1,377(142) | 382 | 同じ | 355 行・食い違い 0 | 21/22・1,235 件 OK |
| 3 | 5 | off | 730 | 1,239(0) | 511 | 同じ | 179 行・0 | 21/22・1,239 件 OK |
| 128 | 1 | on | 786 | 1,388(67) | 0 | 同じ | 559 行・0・注釈 6 | 21/22・1,321 件 OK |
| 4 | 7 | on | 824 | 1,431(197) | 764 | 同じ | 240 行・0 | 21/22・1,234 件 OK |

- 4 本とも final・呼数・想起の計数が on/off で同じ。`tape_rows_without_shown` 0・`tape_pending` 0・出どころは全部 legacy。腕 off の manifest に `memory_store` は無い。
- 実装役の試験(合成は `memory_n=128`)と 5,000 体(1 日)では追い出しが 0 回で、追い出しの同値は単体の試験 1 本だけが見ていた(低 L10)。検収役の再計算で、追い出しの多いラン(382〜764 回)も同値と確かめた。

## 7. 試験 ✓

- 作業木で `tests/engine/memory tests/engine/systems tests/engine/time tests/engine/events tests/engine/test_state_checks_10f.py tests/engine/test_state_ledger_10b.py tests/engine/test_memory_recall.py tests/engine/test_store_memory.py tests/test_cli.py`(`-n 2 --dist loadfile -m "not slow"`): **439 passed・1 warning(607 秒)**。警告は `test_t7_hash_cost_within_the_declared_cap[all_arms]` の checkpoint の時間(最大 0.159 秒が目標 0.1 秒を超えた=警告だけ)。ほかの作業木の試験と同じ機械で回した負荷の影響と見る(器は既定のランで確保しない)。
- `lint-imports`(作業木の src・キャッシュなし): **190 ファイル・706 の依存・5 契約とも守られた**。HEAD の写しは 189 モジュールで、器の 1 本が増えた。grimp の図に `shibuya.engine.memory_store` が入っている。器が import するのは `agents.state`・`core.time_consts`・`engine.events.log`・`engine.familiarity`・`engine.memory`・`engine.systems.guard`・`perception.normalize`・`perception.renderer`。器を import するのは `cli`・`engine.memory`・`engine.systems.build`。
- CLI(検収役の確かめ・合成の世界 40 体・120 刻み・記憶 on・テープつき): 環境変数 `mem` に CLI `events` を重ねると 22 列、環境変数 `events` に CLI `mem` なら 21 列、CLI なしは環境変数のとおり(22/21)。CLI が環境変数より強い。ただし、この経路の試験はリポに無い(低 L9)。

## 8. 抜け道と記録

- (a) §6。(b) 既定 off で `calls_column_names` は 21 列のまま(実装役 19 構成・検収役 4 構成)。腕 on だけ 22 列目 `recalled_event_ids`。✓
- (c) `engine/memory.py` に `__path__`・`pkgutil`・`extend_path` は無い。`engine/memory/` のフォルダも無い。`lint-imports` は 190 ファイルで器を数える。✓
- (d) 目印の先は 100% legacy で、この限界は記録 §0・§5・§12 に明記がある。M0 で `origin=None` を書くと `ValueError` になる。置き換える段について、記録と docstring は「1-8・1-9」と書くが、計画(`v2-implementation-plan-2026-10-12.md`)に体の出来事を記録へ載せる段の記述は無く、実装役の推測。共通の約束「新しいつなぎは台帳(1-4)に外す段つきで」に当たる登録もまだ無い(1-4 は別の作業木)=中 M2。△
- (e) 書く口は `remember`・`mark_shown` の 2 つと言い切れない。ほかに `rebuild`(M0 の行を書く・ランの途中でも M0* を宣言した系から呼べる)・`take_shown`(M0R の控え)・`recall`(M0R の計数)がある。どれも実行時の検査を通るが、`rebuild` の検査は `M0` だけ(低 L3)。`del` の抜け道(低 L1)。△
- (f) §5-1。✓(ただし中 M1)
- (g) `tests/engine/test_state_ledger_10b.py`: 数(外の状態 97 → 99・全体 188 → 190)・鍵の列の末尾(`E`・`M0`・`M0R`)・M0/M0R の軸と hash_skip の 3 行の assert・docstring の 3 行。凍結の表の増えた分と、その行の軸の確かめだけ。✓
- 記録に絶対パス・ホスト名・個人名は無い(`grep` で 0 件。README の `_bc/` は作業木の中の相対の名)。LF。✓
- 触った共有ファイルの一覧(記録 §11 の 9 本)は `git diff --stat` の 9 本と一致する。✓
- T0: 新しい src に時間の直書きは無い(「60 tok」は docstring の字数)。新しい関数 `_shop_arrays`・`_recall_from_store` の引数名 `tick` は凍結の表に載る既存の名で、試験は通る(低 L6)。

## 欠陥

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `src/shibuya/engine/memory.py` `_write`(器の `remember` の直後)・記録 §0・§9 | 実行時の検査は行の番号しか見ない。器の値(回数・重要度・時刻・中身)が表からずれても落ちず、器は hash_skip なのでハッシュにも出ず、mock の final にも出ない(負の対照: 重要度 −1 で想起 114/787 が食い違い、final は同じ)。M0=no・derivable の宣言は「器=表の写し」に乗っているのに、それを実行時に守っていない。記録の「腕 on の final が同じ(想起が同じなので)」も根拠として弱い | `_write` で、書いた番地 `g` の器の値を表と配列で突き合わせて `RuntimeError` にする(1 回の書きで ≤ 体の数の比べ)。負の対照(重要度をずらすと落ちる)を 1 本。記録 §0・§9 は「final は mock では想起に鈍い。根拠はテープの前の 21 列(`recalled_*`・`b5_text`・`prompt_hash`)の一致と直接の突き合わせ」と直す |
| M2 | 中 | 記録 §2・§12・`memory_store.py` の `remember` の文 | 仮の行(legacy)はつなぎなのに、1-4 の台帳に「外す段」つきで載っていない。置き換える段「1-8・1-9」は計画に根拠が無い | 1-4 の取り込みの後に親が台帳へ載せ、外す段(体の出来事を出来事の記録へ載せる段)を決める。決まるまで記録と文は「段は未定(親が決める)」にする |
| L1 | 低 | `memory_store.py` `MemoryStore.__setattr__` | `__delattr__` が守られていない。`del` のあとに欄を付け替えられる | `__delattr__` で `AttributeError` を出す・負の対照 1 本 |
| L2 | 低 | `src/shibuya/engine/tape.py` `ARM_COLUMNS`・`memory_store.py` `_COL_SPEC` | 閉じた表が素の dict で、名を足せる(1-3 L7 の教訓) | `MappingProxyType` で包む |
| L3 | 低 | `memory_store.py` `rebuild` | 検査は `M0` だけなのに `_ms_tape`・`_ms_stats`(M0R)も書く。ランの途中でも M0* を宣言した系から呼べる | `SHOWN_PATH` も検査する。再開の外で呼べないようにする(系の外=`PATHS_PERMIT is None` のときだけ)か、記録に限界として書く |
| L4 | 低 | `memory_store.py` `_REBIND` | `tape_on` を外から付け替えられる(途中で外すと控えが止まる) | `attach_tape` の中だけで `object.__setattr__` を使い、`_REBIND` から外す |
| L5 | 低 | `memory_store.py` `MemoryView` | 「LLM に見せる形」に強さの成分 `first_ns`(記録 §2 で強さの 1 列)と同定の欄が入っている。描き方は使わない | 同定の欄を別の組に分けるか、docstring と記録で「描き方に渡さない欄」と明記する |
| L6 | 低 | `memory.py` `_shop_arrays`・`_recall_from_store` | 新しい関数の引数名が `tick`(凍結の名の再利用で試験は通る) | 周りの関数に合わせた判断として記録に書くか、`step` にする |
| L7 | 低 | `manifest_sections.py` | 既定のランの manifest でも葉が 1 つ増える(`manifest_sections.paths.memory_summary.memory_store`)。既存の値は不変(検収役の比べ) | 「既存の欄は不変」の範囲内と親が認めるか確かめる(記録 §8 に明記はある) |
| L8 | 低 | `llm_bridge.py`・`memory.py` `tape_event_ids` | 艦隊の道(再送・落ちた呼)の録画の控えは試験が無い。残った控えは `_ms_tape` に溜まる | 偽 vLLM の道の試験を足すか、日の締めで `tape_pending` を計器に出して 0 を確かめる |
| L9 | 低 | `tests/test_cli.py` | `--memory-store` が環境変数より強いことの試験が無い(1-3 L3 の再発防止) | 合成の世界の小さな CLI の試験を 1 本(テープの列の数で見る) |
| L10 | 低 | `tests/engine/memory/_m0.py` の `KW` | 同値の試験(合成)は `memory_n=128` で追い出しが 0 回。追い出しの同値は単体の試験 1 本だけ | `memory_n=4` 前後の構成を同値の試験の parametrize に足す |

## 判定

**条件つき受入**。結果不変(19+4 構成と検収役の 4 構成)・同値(実装役の 34,116 呼び出しと、検収役の別の方法・追い出しありの 4 本)・描き方のバイト一致・宣言と台帳・試験・lint を確かめた。条件は M1(実行時の値の突き合わせと記録の直し)。M2 は親の台帳の作業。低い 10 件は取り込みの前でも後でもよい。
