# 10f 環境の欄・manifest の設定と観測の分離・小さな直し(第 1 段)

> 実行役(Opus 5.5)の記録。親の検収の前。commit していない。
> 先に読んだもの: [10f のアジェンダ](../../../../design/v2-d102-10f-agenda.md)(K20〜K26 は親推奨で確定=ユーザー決定 2026-10-06)・[10f の材料](../10f-prep.md)・[10d の記録](../../wallbounce-1003/10d/README.md)・[review-10c.md](../../wallbounce-1003/review-10c.md)・検収の記録 [review-10f-stage1.md](review-10f-stage1.md)。
> 範囲: アジェンダ §2 の 1(環境の欄・K26 (a)+(1))・2 の一部(K22 (a)=manifest の設定と観測の分離)・6(小さな直し)。salt の道具・AST の検査・K19・保存の形式は第 2 段以降。
> 測った機械: Windows 11・x86-64・論理 CPU 20。パスは `src/shibuya/` を省き、絶対パスは書かない。
> 本書は検収の後の直し(N1〜N9 と §8 の答え)を反映した版。直したことは §9、検収の指摘ごとの扱いは §10。

## 第 1 段

### 1. 変えたファイル

| ファイル | 何を |
|---|---|
| `engine/resume.py` | `environment_fields()` を足し、`platform_fields()` はその全体を返す形に広げた(表 1)。`EnvironmentMismatchWarning` と `warn_if_other_environment()`(再開と再生の元を書いた環境が違えば警告 1 行)。docstring の「`sessions` と `_of_agent` が同じ `Session` を指す」に〔訂正(10f)〕を添えた |
| `engine/run.py` | `RunResult.env_fields` を足した。ランの頭で `environment_fields()` を呼び、manifest(`env_id`・`environment`)・状態の見出し(`platform`・`env_id`)・テープの `run_meta.json`(`env_id`・`environment`)の 3 か所に同じ値を書く(どれも深い写し)。manifest の末尾に `env_id`・`environment`・`manifest_sections` の 3 欄を足した(既存の欄は名前も順も値も変えない)。再開(`resume_from`)と再生で環境の違いを警告 |
| `engine/manifest_sections.py`(新) | manifest の欄の節(設定・観測・環境)の表・最も長く一致する道筋で節を引く関数・混ざった辞書の葉の網羅の検査(`unlisted_in_mixed`)・設定の道筋の一覧(`config_paths`) |
| `engine/state_ledger.py` | O75 から `flow_dir8`・`coherence` を外して O95(軸 1 diag・軸 2 は O75 と同じ unknown)にした。台帳の版を `state-ledger/10f` に上げた(193 行) |
| `tools/c7/seed_exchangeability.py` | manifest に節の表があれば設定の節だけを比べる(`mode: sections`)。観測の差は数えるだけ、環境の差は警告だけ。表の無い古い manifest は従来どおり(`mode: legacy`) |
| `tests/golden_env.py`(新) | golden を `{platform_id: 値}` の行で持つ小道具(行の取り出し・A/A・未登録の警告 `GoldenUnregisteredWarning`・標準エラーへの 1 回だけの報告 `announce_once`) |
| `tests/engine/test_env_and_sections_10f.py`(新) | 21 件(§7) |
| `tests/engine/test_presence_executor.py`・`test_presence_derive_v2.py`・`test_relations_tenure.py`・`test_classical_social.py`・`tests/perception/test_near_tiebreak.py` | golden の辞書(`W17_GOLDEN`・`REAL_GOLDEN`・`REL_ON_5000_GOLDEN`・`CLASSICAL_1500_GOLDEN`・`CLASSICAL_1500_GOLDEN_ACQ`)を `*_BY_ENV = {platform_id: 元の値}` に移し、今の環境の行を登録した。行の無い環境では警告を出して A/A だけを見る。値は 1 つも変えていない |
| `tests/engine/test_state_ledger_10b.py` | 行の数の試験を 193 行(外の状態 95)に。T7 の final の直書き(`993276d5…`)は登録した環境だけで比べ、未登録なら警告 |
| `tests/engine/test_10a_review_fixes.py` | `run_meta.json` の完全一致の試験 3 か所を「環境の 2 欄を除いた形が今までと同じ」と「鍵は 4 つ」に |
| `docs/bench/analysis/wallbounce-1003/10d/README.md` | §4-1 の pickle の注に〔訂正(10f)〕・§11-1 の「10e で比べるのはこの値」に〔訂正(10f)〕(元の文は残した) |
| `docs/bench/analysis/wallbounce-1003/review-10c.md` | 「372 層」に〔注(10f)〕(372 は流れの数・層は 186) |
| `10f/manifest_check_10f.py`(新)・`10f/manifest_check.json`・`10f/byte_check.json` | 記録(§4・§5) |

### 2. 環境の欄の中身(今の環境の実値)

表 1: `environment_fields()`。`platform`・`runtime` はプロセスごとに 1 回集める(初回 約 0.14 s。git の呼び出しと依存の一覧の読み取りが大半)。`code` は git の index・HEAD・今の枝の ref の更新時刻が変わったら取り直す。取れない欄は空の値(`""`・`None`・空の list)にして欄は残す。

| 節 | 欄 | 値(この機械) | 取り方 |
|---|---|---|---|
| `platform` | `python`・`python_implementation` | 3.12.10・CPython | `sys.version`・`platform` |
| | `numpy`・`numba`・`llvmlite`・`blake3` | 2.5.3・0.67.0・0.49.0・1.0.9 | numpy は `np.__version__`、ほかは `importlib.metadata.version`(import しない) |
| | `os`・`os_release`・`os_version` | Windows・11・10.0.26200 | `platform.system/release/version` |
| | `machine` | 種類だけ: x86-64(`AMD64`) | `platform.machine()`(機械の名前 `platform.node()` は入れない=テストで確かめる) |
| | `cpu` | 種類だけ: Intel の x86-64(型番の文字列) | `platform.processor()` |
| | `numpy_simd` | 基線 `X86_V2`・実行時に見つかった `X86_V3` | `np.show_config(mode="dicts")["SIMD Extensions"]` |
| | `deps`・`deps_sha256`・`deps_count` | 「名前==版」の 48 行・`sha256:e71efcf6…`・48 | `importlib.metadata.distributions()`(名前は小文字・`_` を `-` に・昇順・重複なし)。sha256 は行を改行でつなぎ末尾にも改行(`pip` は呼ばない) |
| `runtime` | `numba_threads`・`numba_threads_env` | 20・`""` | `numba.config.NUMBA_NUM_THREADS`(既定のスレッド数。途中の `set_num_threads` は映らない)と環境変数 |
| `code` | `git_commit`・`git_dirty`・`git_diff_sha256` | 40 桁(表では頭 8 桁 `8c8a77c2`)・true・`sha256:…`(dirty のとき) | `git --no-optional-locks`。`rev-parse --show-toplevel` がパッケージの根と同じときだけ値を入れる。dirty は追跡しているファイルだけ(`status --porcelain --untracked-files=no`)。差分は `git diff HEAD --binary` の sha256。git が無い・根が違うときは `""`・`None` |
| ID | `platform_id` | **`43cd89305417b52e`** | `platform` のうちビットに効きうる 12 欄(`PLATFORM_ID_KEYS`=Python と実装・numpy・numba・llvmlite・blake3・OS と版の 3 欄・machine・cpu・numpy の命令セット)の正準の JSON の blake3 の頭 16 桁。golden の行の鍵。依存の一覧・commit・dirty・スレッド数は入れない |
| | `env_id` | `f95555fd09778abf`(記録のランの時点) | `schema`・`platform`・`runtime`・`code` の正準の JSON(鍵を昇順・区切り `,` `:`・`ensure_ascii=False`)の blake3 の頭 16 桁。commit と作業木の差分で変わる |

- **3 か所の一致**: (1) 同じプロセス: 合成世界 20 体の 2 日のランを日の境目で止め、manifest・状態のファイルの見出し(`.pkl` の中と写しの `.json`)・`run_meta.json` の `env_id` と `environment` が同じ。(2) 別々のプロセス(T1): 2 回のサブプロセスで、書かれたファイル(checkpoints の JSON の manifest・見出しの写し・`run_meta.json`)を読んで、6 ファイルの `env_id` が全部同じ。(3) 5,000 体の 7 本(§4)の manifest の `env_id` は全部 `f95555fd09778abf`。
- **golden の行**: 5 つの辞書と T7 の直書きを `platform_id` = `43cd89305417b52e` の行として登録した。第 1 段の版の鍵 `2c54e621365e279a` は依存の一覧を含んでいた(検収 N2)。

### 3. manifest の節(K22 (a))

- 形: manifest に表 `manifest_sections`(`{"schema", "rule": "longest-prefix", "paths": {道筋: 節}}`)を 1 つ足した。道筋は入れ子の鍵を `.` でつないだもので、最も長く一致する道筋の節を使う。一番上の欄は全部載せた。観測と設定が混ざった辞書 21 個(`energy`・`energy.home_meal`・`relations`・`relations.init`・`memory_summary.recall` など)は**子の鍵を全部**表に書いた(表の全体は 384 道筋・うち設定 151)。混ざった辞書の下の葉が、表の上では混ざった辞書そのものにしか当たらない(=節を決めていない新しい鍵)ときはテストが落ちる。中身が全部観測の子(`energy.counts` など・鍵が動的なもの)は、子の道筋 1 つで中身全部を表す。
- **`relations.init`(検収 N1)**: 観測の節にし、定数の 7 葉(`density`・`k`・`slot_minutes`・`tiebreak`・`tenure_weeks`・`tenure_hash`・`w17_single_day`)だけを設定にした。群の数・候補の対・τ で落ちた辺・壁時計(`init_seconds_nondeterministic`)・`reason` は観測。
- **設定の道筋の一覧を固定**: `config_paths()` の sha256(`170e1c30…`)をテストの golden にした(環境に依らない)。節を変えたらこの値の更新が要る(設定 → 観測の黙った付け替えを捕まえる)。
- **節ごとの入れ子にしなかった理由**: `run_manifest_fields()["rng_scheme"]` の形で読むテストと道具が 150 か所あまりある。表を足す形なら欄は 1 つも動かず、表を読まない読み手には今と同じ manifest に見える。`tests/test_manifest_roundtrip.py`・`test_manifest_rules_extra.py` は `manifest/schema.py` の `RunManifest` を見るもので別(どちらも通る)。
- 節の振り分けは実行役が欄の中身を読んで決めた(**未リサーチ(expedient)**)。確かめ方: 関係の初期化が実際に走る mock 5,000 体の記憶+関係・classical+記憶+関係と、既定 v3・記憶+店の記憶の seed 1 と 2 で、設定の葉が seed で動かないこと(§5)。第 1 段の版の「300 体 4 構成で差 0」は関係の初期化が空のランで、関係については何も確かめていなかった(検収 N1)。葉の網羅は、合成世界の全腕 2 日・世界資産 300 体の全腕・classical・v2+edge・5,000 体の 7 本で確かめた。
- 環境の節(`env_id`・`environment`)は比べるが、違っても警告だけ(`environment_warning`)。

### 4. byte-check(19 構成)

- 手順(10d README §8 と同じに、写しへの祝日の CSV を足した):
  ```
  git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
  mkdir -p $W/head_src/data/calendar && cp data/calendar/syukujitsu.csv $W/head_src/data/calendar/   # 写しの src は祝日の CSV を写しの根から探す
  python docs/bench/analysis/wallbounce-1003/10c/byte_check_10c.py side --src $W/head_src/src --label head --scratch $W --out $W/head.json --jobs 4
  python docs/bench/analysis/wallbounce-1003/10c/byte_check_10c.py side --label work --scratch $W --out $W/work.json --jobs 4
  python docs/bench/analysis/wallbounce-1003/10b/byte_check_10b.py compare --head $W/head.json --work $W/work.json --head-label 8c8a77c --out $D/byte_check.json
  python $D/manifest_check_10f.py hashes --head $W/head.json --work $W/work.json --byte-check $D/byte_check.json
  ```
  HEAD `8c8a77c`(src は 10d の後で変わっていない)。mock/classical 5,000 体・seed 1・1 シミュ日・テープつき。
- 結果: **19/19 一致**(final・呼数・blocks・calls の 14 列)・`src_checks` ok([byte_check.json](byte_check.json))。19 構成の final と呼数は 10d の [byte_check.json](../../wallbounce-1003/10d/byte_check.json) とも全部同じ。
- **behavior-hash と full-hash** は O95 の分割(§6)で 19 構成すべて変わる(final・テープ・呼数は不変)。前と後の値は `byte_check.json` の `state_hashes_before`・`state_hashes_after` に 19 構成とも入れた。主な 3 構成:

| 構成 | final | 呼数 | behavior-hash 前 → 後 | full-hash 前 → 後 |
|---|---|---|---|---|
| 既定 v3(`w6_v3_default`) | `993276d5e5bb5cbe` | 69,978 | `b3ccfa6797f2c418` → `1f4d96b1d8dfa701` | `fa168793db2b6433` → `64f2aa138e8a6bfe` |
| 帰無(`w6_golden_null_arm`) | `72cb9cd52982da74` | 100,439 | `aa2a2b3818f33362` → `ed827fd4e312264d` | `c38b7abc37211bd6` → `6242009e11760745` |
| relations-on(`v3_mem_rel`) | `40409ebed834126b` | 72,930 | `2817c8ed4bc17c88` → `b2e49d9cc5c2ccce` | `165666b6c42034f3` → `8f25c6b0f453bb4b` |

- 「前」は 10d §11-1 の記録と同じ。**10e で比べる値は `state_hashes_after` に置き換わる**(10d の README の該当行に〔訂正(10f)〕を添えた)。
- **manifest**(`manifest_check_10f.py`・[manifest_check.json](manifest_check.json)): 既定 v3 の seed 1/2・帰無・記憶+関係の seed 1/2・classical+記憶+関係の seed 1/2 の 7 本で、作業木の manifest から 10f の 3 欄を抜き、平坦化した全部の欄(606〜1,143 欄)を HEAD と比べた。一番上の欄の並びは同じ。違ったのは `state_hashes`(behavior・full・`ledger_version`・行ごとのバイト数の O75 と O95)・`state_hashes_end_of_day`・`daily` の中の日の締めの後の 2 本だけ(予定どおり)。`daily` のそれ以外は同じ。壁時計の 2 欄(`relations.wall_seconds_nondeterministic`・`relations.init.init_seconds_nondeterministic`)は比べていない。

### 5. `seed_exchangeability` の前後

mock 5,000 体・1 日・seed 1 と 2([manifest_check.json](manifest_check.json) の `seed_exchangeability_s1_s2`)。「第 1 段の表」は検収の前の表(`relations.init` を丸ごと設定にしていた)で、同じ 5,000 体のランの manifest に当てた値。

| 構成 | HEAD(legacy) | 第 1 段の表 | 直した後 | 観測の差(数えるだけ) |
|---|---|---|---|---|
| 既定 v3 | False(未説明 316) | True | **True**(未説明 0) | 316 |
| 記憶+関係(`v3_mem_rel`) | False(未説明 743) | **False**(未説明 9=`relations.init` の 8 欄と壁時計) | **True**(未説明 0) | 743 |
| classical+記憶+関係(`v3_classical_mem_rel`) | False(未説明 698) | **False**(未説明 9) | **True**(未説明 0) | 698 |
| 記憶+店の記憶(`v3_mem_store`・scratch の確認) | 測っていない | True | True(未説明 0) | 719 |

- どれも許容の差は `seed`・`run_id`・`final_hash` だけ、表に無い欄 0、環境の警告なし。
- 母集団のハッシュは seed で違う(`population_seed_independent=False`=K21 の項。第 1 段では変えていない)。
- テスト: `test_relations_on_5000_seeds_are_exchangeable_and_config_leaves_do_not_move`(`slow` の印・5,000 体の記憶+関係の seed 1/2 で PASS・設定の葉 100 欄以上が全部一致・関係の初期化が空でないこと)。

### 6. 小さな直し

- **(a) O75 の `flow_dir8`・`coherence`**: 読み手の grep(src・tools・tests の `*.py`・`getattr` の文字列を含む)。src で 2 つの名前を書くのは `engine/processes/crowd.py`(作る・0 に戻す・書く)と台帳だけ。tools は 0。tests は `tests/engine/processes/test_crowd.py` の 3 か所(過程の単体の試験)。`coherence` は流れの 3 値を作る途中の局所変数 `coh` として使われ、属性は読まれない。10f の材料 §3-3 の AST の走査でも読み手 0。→ O75 から外して **O95**(軸 1 diag・軸 2 は O75 と同じ unknown=保存の範囲は変えない)にし、根拠を行の注に書いた。描画が読む `flow` は O75(behavior)に残した。台帳は 193 行(SoA 98・外の状態 95)・版 `state-ledger/10f`。網羅の検査(未カバー 0)と AST の検査(`test_state_ledger_10b.py` 全件)は通る。版を上げたので 10d の版で書いた状態のファイルは読み口で止まる(リポの中にそういうファイルは無い=検収 §3-4)。
- **(b) docstring と 10d の README**: `_of_agent` は体 → 会話の番号の整数の辞書(`engine/conversation.py:281`)。どちらも元の文を残して〔訂正(10f)〕を添えた。
- **(c) review-10c.md の「372 層」**: 〔注(10f)〕を添えた(372 は抽出が 2 回走るための流れの数で、層は 186。10f の材料 §4-2 表 8 の数え方)。

### 7. 試験

新しいテスト `tests/engine/test_env_and_sections_10f.py`(21 件):

| 試験 | 中身 |
|---|---|
| `test_environment_fields_shape_and_ids` | 欄の集合・`env_id` と `platform_id` を正準の JSON から計算し直して一致・依存の一覧が昇順で sha256 と本数を計算し直せる・毎回新しい写し・機械の名前が入らない |
| `test_missing_git_gives_empty_values_and_keeps_the_fields` | git が無いと `""`・`None` |
| `test_git_values_only_when_the_toplevel_is_the_package_root` | 根がリポの根と違えば空(N7)・commit は 40 桁・差分の sha256 は dirty のときだけ |
| `test_git_commands_take_no_optional_locks_and_ignore_untracked` | git の呼び出しはすべて `--no-optional-locks`・status は `--untracked-files=no`(N6・N7) |
| `test_platform_id_ignores_commit_threads_and_dependency_versions` | commit・スレッド数・依存に `pytest==99.0` を足しても `platform_id` は同じ・`env_id` は変わる(N2 の再現 a2) |
| `test_env_id_is_the_same_in_the_three_places` | 同じプロセスの 3 か所の一致・manifest の環境の欄は深い写し(N9) |
| `test_t1_two_processes_write_the_same_env_id_and_final_to_the_files` | T1: 別々のプロセスで 2 回・書かれたファイルを読んで `env_id`・final・見出しのハッシュ・manifest(環境の欄とラン ID を除く)が一致・新しい 3 欄は末尾(N9) |
| `test_resume_from_another_environment_warns_once_and_keeps_going` | 同じ環境の再開は警告なし・別の `platform_id` の状態のファイルからの再開で警告 1 回・final は同じ(§8 の 6) |
| `test_replay_of_a_tape_from_another_environment_warns_once` | 再生でも同じ・環境の欄の無い古いテープは何も言わない |
| `test_unregistered_environment_warns_and_falls_back_to_aa` | 未登録の `platform_id` で行が `None` と警告・標準エラーに 1 回だけ・A/A は 2 回回して比べ違えば落ちる・登録済みなら警告なし(N2) |
| `test_removing_a_bit_relevant_field_makes_the_golden_check_loud` | `cpu` を空にすると `platform_id` が変わり、golden の行の取り出しが警告(N2 の再現 a1) |
| `test_golden_tables_are_keyed_by_platform_and_values_unchanged` | この環境が登録済み・5 つの表の鍵が登録した環境だけ・値が 10f の前と同じ |
| `test_every_top_level_manifest_field_has_a_section` | 一番上の欄が全部表に載る・最も長く一致する道筋の規則 |
| `test_relations_init_is_observed_with_constant_leaves_as_config` | N1 の節 |
| `test_config_paths_are_frozen` | 設定の道筋の一覧の sha256(N3 の 3) |
| `test_mixed_dict_leaves_are_all_listed_synthetic` | 合成世界の全腕 2 日で混ざった辞書の葉が全部載る・わざと足した鍵は捕まる(N3 の 1) |
| `test_mixed_dict_leaves_are_all_listed_world` | 世界資産 300 体の全腕・classical・v2+edge で同じ |
| `test_seed_exchangeability_passes_for_v3_seeds_and_fails_on_a_config_change` | 世界資産 300 体・240 tick: 既定 v3 の seed 1/2 で PASS・出勤率を変えたランで FAIL・表を抜いた manifest(legacy)は FAIL |
| `test_relations_on_5000_seeds_are_exchangeable_and_config_leaves_do_not_move` | `slow`: §5(N1・N3 の 2) |
| `test_seed_exchangeability_sections_mode_on_synthetic_runs` | 観測の欄だけの差は PASS・設定の欄(`rng_scheme`・`memory_n`・`l4_scale`・`attendance_rate`・混ざった辞書の中の `state_hashes.ledger_version`・`energy.rate`・`intent.max_ticks`)の差は FAIL・環境の欄の差は警告だけで PASS・表に無い欄の差は FAIL で名前が出る |
| `test_o75_split_flow_dir8_and_coherence_are_diag` | O75/O95 の中身と軸・behavior に入らず full に入る・src の読み手 0 |

テストの数(`python -m pytest -q tests`・`-o addopts=""` で集計の行を出した):

| | 集めた数 | passed | failed | skipped |
|---|---|---|---|---|
| 前(変更の前・作業木) | 3,635 | 終了コード 0(集計の行が出なかった。数は不明) | 0 | 不明 |
| 第 1 段(検収の前) | 3,646 | 3,644 | 0 | 1(ほかに xfailed 1) |
| 直した後 | 3,656(+10) | **3,654** | **0** | 1(ほかに xfailed 1・44 分・警告は既知の 1 件だけ=golden 未登録の警告は出ていない) |

### 8. 親に確かめる点(第 1 段の版)と答え

| # | 点 | 答え(検収 §2 と親の判断) |
|---|---|---|
| 1 | golden の行の鍵 | `platform_id`(`env_id` ではなく)で受け入れ。依存の一覧は鍵から外し、未登録は警告=§9 の N2 |
| 2 | `git_dirty` の数え方 | 追跡しているファイルだけ+差分の sha256=§9 の N6 |
| 3 | 混ざった辞書の寄せ方 | どちらにも寄せず葉まで明示=§9 の N3 |
| 4 | 振り分けの迷い | 受け入れ。`relations.init` は誤り=§9 の N1 |
| 5 | O95 で hash が全構成で動く | 受け入れ。10d の記録へ伝播=§9 の N8 |
| 6 | 再開と再生で環境の違い | 警告 1 行(挙動は変えない)=§9 |
| 7 | byte-check の写しの手順 | 祝日の CSV を写す行を手順に足した(§4) |
| 8 | numba のスレッド数 | 受け入れ(docstring に「途中の `set_num_threads` は映らない」と書いた) |
| 9 | 未登録の環境の費用 | 受け入れ(費用より黙ること=N2 が問題) |

### 9. 検収の後に直したこと

1. **N1**: `relations.init` を観測の節に、定数の 7 葉だけを設定に(§3)。5,000 体の記憶+関係・classical+記憶+関係の seed 1/2 で FAIL(未説明 9)→ PASS(§5)。
2. **N2**: `platform_id` を `PLATFORM_ID_KEYS` の 12 欄だけにした(依存の一覧を外した)。新しい値 `43cd89305417b52e`。未登録の環境では `tests/golden_env.py` が `GoldenUnregisteredWarning` を出し(pytest の要約に残る)、標準エラーに登録の有無を 1 回だけ書く。fail にはしない。検収役の再現 a1(`cpu` を抜く)は警告が出る、a2(依存に 1 行足す)は `platform_id` が変わらない(どちらもテスト)。
3. **N3**: 混ざった辞書 21 個の子の鍵を全部表に書き、表に無い葉はテストで落とす。設定の葉が seed で動かないことを 5,000 体の関係 on で確かめるテスト(`slow`)。設定の道筋の一覧の sha256 を golden で固定。
4. **N4**: `environment.platform.deps` に「名前==版」の 48 行(manifest・状態の見出し・`run_meta.json` に入る)。sha256 と本数も残した。
5. **N5**: byte-check を 19 構成で(§4)。写しに祝日の CSV を足す手順を書いた。
6. **N6・N7**: `git_dirty` は追跡しているファイルだけ・dirty のときは `git_diff_sha256`・すべての git の呼び出しに `--no-optional-locks`・`rev-parse --show-toplevel` がパッケージの根と同じときだけ値を入れる。
7. **N8**: 10d の README §11-1 の「10e で比べるのはこの値」に〔訂正(10f)〕を添え、本書 §4 と `byte_check.json` の `state_hashes_after` を指した。
8. **N9**: (a) T1 は別々のプロセスで書かれたファイルを読んで比べる形にした。(b) `test_near_tiebreak.py` の A/A では `mid` を回さず、`new != old`(切替が効く)を残した。(c) manifest・`run_meta.json`・状態の見出しの環境の欄は深い写し。(d) `code` は git の index・HEAD・今の枝の ref の更新時刻が変われば取り直す(長く動くプロセスでコミットした後のランが古い commit を書かない。索引に載せていない作業木の編集だけでは取り直さない=宣言)。(e) 表 1 の `git_commit` は表示の省略で、欄は 40 桁と注記した。
9. **§8 の 6**: 再開(`resume_from`)と再生で、元を書いた環境の `platform_id` が今と違えば `EnvironmentMismatchWarning` を 1 行(挙動は変えない)。環境の欄の無い古いファイルは何も言わない。

### 10. 検収の指摘ごとの扱い

| # | 扱い | 一言 |
|---|---|---|
| N1 | 直した | `relations.init` は観測・定数 7 葉だけ設定。関係 on の 2 構成が 5,000 体の seed 1/2 で PASS |
| N2 | 直した | 鍵から依存の一覧を外し(`43cd89305417b52e`)、未登録は警告+標準エラーに 1 回(fail にはしない=K26 (1)) |
| N3 | 直した | 混ざった辞書の葉を全部明示・表に無い葉で落とす・設定の葉の seed 不変を 5,000 体で・設定の一覧を golden に |
| N4 | 直した | `platform.deps` に 48 行の一覧 |
| N5 | 直した | 19/19 一致・祝日の CSV の手順・前後のハッシュを JSON に |
| N6 | 直した | dirty は追跡ファイルだけ・`git_diff_sha256`(範囲は作業木の全体。src・tools に絞った欄は作っていない=未追跡の src は差分に入らない) |
| N7 | 直した | `--no-optional-locks`・toplevel の一致 |
| N8 | 直した | 10d の README に〔訂正(10f)〕・`state_hashes_after` |
| N9 | 直した | 5 点とも(§9 の 8) |

## 親の検収(第325・2026-10-07)

- 親: byte_check.json の 19 構成で final と呼数が HEAD と一致・対象のテスト 98 件を回して緑。全体のテストは実装役の 3,654 passed(直す前の作業木を親が回して exit 0)。
- 別のサブの再検収([review-10f-stage1-recheck.md](review-10f-stage1-recheck.md)): **受入**。N1〜N5・N7〜N9 は直った・N6 は一部。
- 残す低い欠陥(第 2 段以降で扱う・既定の結果に影響なし): R1 未追跡の src は `env_id` に入らない(§10 の N6「直した」は「一部」に読み替える)/ R2 未登録の警告でどの golden の表を飛ばしたかが要約から分からない / R3 `PLATFORM_ID_KEYS` に pyarrow・xxhash・cbor2 が無い(版が変われば試験は大きな音で落ちる。「ビットに効きうる 12 欄」は言い過ぎ)/ R4 `git diff` に `--no-ext-diff --no-color` が無い。

## 第 2 段(seed の分離・salt の道具・CRN の健全性)

> 実行役(Opus 5.5)の記録。親の検収の前。commit していない。範囲はアジェンダ §2 の 2(K20 (a)・K21 (a))と §4 の T2・T3。
> **検収の後の直し**: 検収 [review-10f-stage2.md](review-10f-stage2.md)(条件つき受入・S1 1・S2 1・S3 8)を受けて直した。seed は母集団・環境・動きの 3 つになった(§9)。§1〜§8 は直す前の記録で、§2 の表・§6 の数・§7 のテストの数は §9 と §11 が新しい。
> 先に読んだもの: [アジェンダ](../../../../design/v2-d102-10f-agenda.md) §2〜§5・[R-71](../../../../research/v2-r71-stochastic-comparison-statistics.md)・[10f の材料](../10f-prep.md) §2・第 1 段(上)・[first_diff.py](../../wallbounce-1003/10d/first_diff.py)。

### 1. 変えたファイル

| ファイル | 何を |
|---|---|
| `engine/run.py` | `run_day(population_seed=None)` を足した(省略時は `seed` と同じ値)。母集団の側の乱数を `population_seed` から引く。用途名の表 `POPULATION_RNG_DOMAINS`・`MOTION_RNG_DOMAINS`・`MOTION_SALTS` と `resolve_population_seed()`。`RunResult.population_seed` と manifest の末尾の欄 `population_seed`。設定の指紋には `seed` と違うときだけ載せる(既定のランの状態のファイルの見出しは 1 欄も増えない)。`python -m shibuya.engine.run --population-seed` |
| `cli.py` | `--population-seed`(省略=`--seed` と同じ)。`cli.run(population_seed=…)` は合成世界と世帯の財布(W16 の抽出を含む)に使い、`run_day` に渡す |
| `engine/processes/runner.py` | `population_seed` を受け、気象の再生実日(`EnvironmentProcess`)と域外居住(`RailProcess`)の `master_seed` に渡す(属性には持たない=状態台帳は不変) |
| `engine/geometry.py` | `EdgeGeometry(population_seed=…)`: 希望歩行速度だけを母集団の seed から(属性は増やさない) |
| `engine/manifest_sections.py` | `population_seed` を設定の節に |
| `tools/c7/seed_exchangeability.py` | `manifest.population_seed` の差を許容に入れ、`population_seed_varies` で報告(省略のランでは seed と一緒に違う=今までの seed の比較と同じ意味) |
| `tools/c7/salt_runs.py`(新) | 回す役。1 本ずつ別のプロセスで `shibuya.cli.run` を呼び、`checkpoints_payload` を書くだけ。`--aa`・`--first-diff` |
| `tools/c7/salt_compare.py`(新) | 読む役(純関数)。R-71 の手順と CRN の健全性 |
| `tests/c7/test_salt_compare_10f.py`(新) | T2 ほか 20 件 |
| `tests/engine/test_salt_seed_split_10f.py`(新) | seed の分離と T3 の 10 件 |
| `tests/engine/test_env_and_sections_10f.py` | 末尾の欄が 1 つ増えた(`STAGE2_KEYS`)・設定の道筋の sha256 を `3fe95edb…` に更新(前 `170e1c30…`。`population_seed` を足したため) |
| `10f/byte_check_stage2.json`・`10f/stage2_5000/`(新) | 記録(§5・§6) |

### 2. seed の分離の表(K21 (a))

〔訂正(検収の後)〕気象の再生実日は環境の側に移した。表の新しい形は §9 の表 9-1。

振り分けの規則は実行役の構成(**未リサーチ(expedient)**・親の確認待ち): (1) 体の属性(誰が居るか・体の定数・財布・日課)を決める流れと、(2) manifest の設定の節に載る値を決める流れ(`replay_date`)を母集団の側にした。動きの seed(salt)を変えても (1)(2) は動かない。

| 用途名(`core.rng` の domain) | 側 | 何を決めるか |
|---|---|---|
| `w16.sample.reserved`・`w16.sample.stratum` | 母集団 | W16 母集団の抽出(定員先取り層・統計層) |
| `wallet.initial` | 母集団 | 世帯の初期財布 |
| `agent.schedule` | 母集団 | mock 日課(拠点・境界の時刻・mock の初期所持金。W16 の体は拠点と種別を上書き) |
| `body.weight`・`body.eer` | 母集団 | 体重と EER のばらつき |
| `geometry.desired_speed` | 母集団 | 希望歩行速度(`--geometry edge` のときだけ) |
| `engine.processes.rail` | 母集団 | 域外居住の通勤者の抽選(計画実行層の無いランだけ) |
| `engine.processes.environment` | 母集団 | 気象の再生実日(manifest の `replay_date`=設定の節) |
| `world.synthetic` | 母集団 | 合成小世界(世界資産が無いときだけ) |
| `engine.chooser` | 動き | 店・行き先の選び手(`poi_target`・`store_choice` も同じ流れ) |
| `policy.classical` | 動き | 古典の方策 |
| `conversation.invite` | 動き | 会話の招待 |
| `llm.mock`・`llm.mock.move_target`・`llm.mock.out_of_cell_target` | 動き | mock の応答と対象 |
| `perception.attention.p_see`・`perception.p_notice` | 動き | 注視ゲート・顕著行為に気づくか |
| `world.salient`(`.counter`)・`world.public_service_dispatch`(`.counter`)・`world.large_event`・`world.delivery_inbound`・`world.delivery_last_mile`・`world.road_works` | 動き | 世界の出来事 |
| (用途名なし)`run_salt`・出勤の抽選の塩・艦隊の呼ごとの種 | 動き | アービタの同点・適用の順・近接行の同点・歩きの行き先・関係の招待・出勤率・デコードの種 |

- 網羅: `src/shibuya`(`build/` を除く)の `stream`・`philox`・`derive_key` の呼び出しを AST で拾い、全部の用途名が表のどちらか 1 つに載ることをテストで固定した(表に無い新しい流れと、src に無い古い行で落ちる)。
- 実行時: `core.rng.derive_key` を包み、`seed=3`・`population_seed=7` のランで鍵に使った seed を用途名ごとに数えた。母集団の側は全部 7、動きの側は全部 3(合成世界・世界資産 300 体の既定 v3・帰無・edge の 4 通り)。

### 3. 道具の使い方

```
# 回す役(母集団の seed を固定して salt だけ変える)
python tools/c7/salt_runs.py plan --arms '{"v3_default": {...}, "null_arm": {...}}' --base v3_default --arm null_arm \
    --salts 1,2,3 --population-seed 1 --agents 5000 --world data/world/v2 --scratch $W --out $W/runs.json \
    --aa --first-diff --jobs 3
# 読む役
python tools/c7/salt_compare.py --runs $W/runs.json --metrics metrics.json --out report.json
python tools/c7/salt_compare.py --values values.json --metrics metrics.json --out report.json   # 計器の値の組から
```

- 指標の一覧(`metrics.json`): 主要 1 つ(`primary`)・副次(`secondary`=Holm)・探索(`exploratory`=BH)。片側は `direction` と `preregistered: true` の両方があるときだけ(無ければ両側)。`arm_keys_derived`(任意)は、腕の引数から導かれて変わる設定の欄の宣言(理由つき・報告に残る)。
- 出力の線: p の下限(片側 1/2^n・両側 2/2^n)がその指標の線(主要 α・副次 α/k・探索 α)以下のときだけ「検定」。届かなければ「記述のみ(本数不足)」。3 対は必ず記述のみ、5 対は事前登録の片側なら検定、6 対から両側で検定。符号反転は n ≤ 20 で全列挙。
- 差・幅・差 ÷ 幅: 幅=t(1 − α/(2m), n−1)·s_D/√n(m=指標の数=家族)。**幅に対の差の SD を使うのは実行役の構成(expedient)**。各腕の SD で同じ式にした `width_base`・`width_arm` も並べる。
- ほか: ρ と Var(D)/(Var(基準)+Var(腕))(5 対未満は `rho_readable: false`・比 > 1 で警告)・D-46 の 2 通り(基準の CV と対の差の CV で `n_relative_se` と `n_halfwidth95`)・t 区間と並べ替えの反転区間(到達できる水準 1 − 2k/2^n を明記。作れないときは k=1 の区間を `interval_below` に)・生の差・比・差の SD・CRN の対の d_z・d_av。
- CRN の健全性: 入力の一致(対の間の設定の節の差が腕の欄か宣言の中だけ・同じ腕の salt の間は `seed_exchangeability` で交換可能・全部のランで母集団の seed と、最初の checkpoint の母集団と日課のハッシュが同じ)・T0 前の behavior-hash・最初の食い違い・A/A。腕の欄のうち manifest の設定に出てこないものは `arm_keys_unseen` に出す(落とさない)。
- 最初の食い違いの探し方(アジェンダ §3 の親の宣言): 60 tick ごとの checkpoint で最初に食い違った区間 (t_p, t_m] だけを毎 tick で回し直す。区間の前は `stop_at_tick=t_p+1` で止めて状態を書き(10d の口)、`resume_from` で再開して毎 tick の checkpoint を取る。最初の区間なら 0 から毎 tick で回す。比べるのは `first_diff.compare`。

### 4. 試験(T2・T3・seed の分離)

| 試験 | 中身 |
|---|---|
| T2 既知の 2 腕 | 基準 10,12,14・腕 11,15,16(差 1,3,2): 差 2・幅 t(0.975,2)·1/√3・差 ÷ 幅・各腕の幅・Var の比 1/11・ρ = 10/(4√7)(ピアソンの相関とも一致)・比・d_z 2・d_av・t 区間・反転区間(95% は作れず、75% で [1, 3])が手計算と一致。家族 5 本で t(0.995, 2)=9.925 |
| T2 本数の線 | 3 対は「記述のみ(本数不足)」(p の下限 1/8)・5 対は事前登録の片側で 1/32 → 検定、印が無ければ両側 2/32 → 記述のみ・**6 対で p の下限 2/64**・n=3〜8 の表(R-71 §2-3)・Holm で副次 5 本は 7 対で記述のみ・8 対で検定 |
| T2 Holm と BH | p = 0.01, 0.04, 0.03, 0.005: Holm の調整 0.03, 0.06, 0.06, 0.02・棄却 2 つ / BH の q 0.02, 0.04, 0.04, 0.02・k̂=4。もう 1 例(k̂=2) |
| T2 そのほか | t 分位が表と一致・D-46 の 2 通り(CV 0.0325 で 3/13 本と 11/44 本)・符号反転の p が itertools の総当たりと一致(0 の差と同点を含む)・6 対の反転区間が [最小, 最大] で 96.875%・負の相関で比 > 1 の警告・主要は 1 つ・CRN の合成の例(T0 前・最初の食い違い・A/A・入力の不一致 4 通り) |
| T3 | 合成世界 200 体・基準 対 顕著行為の率 100 の腕・salt 1 と 2・母集団の seed 1。回す役の 2 段の探し方の最初の tick(salt 1 は区間 [120, 179] の 176・salt 2 は [0, 59] の 44)が、**毎 tick で通しに回した 2 本を `first_diff.py` の `dump`・`compare` で比べた tick と一致**。T0 = その tick なら T0 前の behavior-hash が一致し、T0 を 60 遅らせると落ちて最初の悪い tick がその tick になる。入力の一致・A/A・全体の `ok` |
| seed の分離 | 省略と `population_seed=seed` で final・呼数・manifest が同じ / 設定の指紋は省略と同じ値の明示で同じ・違う値なら `population_seed` の 1 欄だけ違う / 用途名の網羅(AST)と実行時の鍵の seed(4 通り)/ 世界資産 300 体: 動きの seed だけ変えると、日課の欄(拠点・種別・年齢・性・方向・初期所持金・境界の時刻)と SoA の体の定数(種別・年齢・性・体重・EER)の配列が全部一致し、母集団と日課のハッシュと `replay_date` も同じ・final は違う / 母集団の seed だけ変えると、母集団のハッシュ・拠点・体重が変わる / 型の悪い `population_seed`(bool・負・空)は止める |

### 5. byte-check(19 構成)

- 第 1 段 §4 と同じ手順(HEAD `74d6da8` の写しに祝日の CSV を写す)。
- 結果: **19/19 一致**(final・呼数・blocks・calls の 14 列)・`src_checks` ok([byte_check_stage2.json](byte_check_stage2.json))。最後の checkpoint の behavior-hash と full-hash も 19 構成すべて HEAD と同じ(設定の指紋は hash に入らない)。既定 v3 は `993276d5e5bb5cbe`・69,978 呼・behavior `1f4d96b1d8dfa701`(第 1 段の後の値と同じ)。

### 6. 5,000 体 mock の実例(既定 v3 対 帰無・salt 3 本)

〔訂正(検収の後)〕この節の数は直す前の道具で、環境が salt とともに変わる形(今の `--environment-mode salt`)と同じランだった。置き場の `stage2_5000/` は「天気は同じ(fixed)」で回し直した記録に置き換え、同じ形のランは `stage2_5000_env_salt/` に置いた(§9 の 9-6)。

置き場は [stage2_5000/](stage2_5000/)(索引 `runs.json`・指標 `metrics.json`・報告 `report.json`・checkpoints の JSON 7 本)。腕は byte-check と同じ `w6_v3_default`・`w6_golden_null_arm` の引数。母集団の seed 1・salt 1, 2, 3・`--aa --first-diff --jobs 3`。

- 時間(この機械・並列 3): 7 本(6 本+A/A 1 本)で 99.9 秒(1 本 31.9〜33.4 秒)、最初の食い違いの探し方 14.6 秒(3 対・区間は全部 [0, 59])、計 1 分 55 秒。
- salt 1 の final は byte-check の値と同じ(既定 v3 `993276d5…`・帰無 `72cb9cd5…`)。省略と `population_seed=1` は同じランになる。
- 道具の出力(主要=呼数の総数、副次=域内の食事・域外の食事・間食):

| 指標 | 基準(v3)の 3 本 | 腕(帰無)の 3 本 | 差 | 幅(家族 95%・m=4) | 差 ÷ 幅 | p(下限) | 出力 |
|---|---|---|---|---|---|---|---|
| 呼数の総数 | 69,978・69,380・69,552 | 100,439・102,094・103,947 | +32,523 | 10,097 | 3.22 | 0.25(0.25) | 記述のみ(本数不足) |
| 域内の食事 | 4,497・4,662・4,630 | 0・0・0 | −4,596 | 448 | −10.27 | 0.25(0.25) | 記述のみ(本数不足) |
| 域外の食事 | 7,785・7,809・7,816 | 2,027・1,993・1,956 | −5,811 | 262 | −22.21 | 0.25(0.25) | 記述のみ(本数不足) |
| 間食 | 2,292・2,387・2,315 | 2,412・2,351・2,445 | +71 | 476 | 0.15 | 0.5(0.25) | 記述のみ(本数不足) |

- 呼数の ρ は −0.67・Var の比 1.23(比 > 1 の警告。ただし 3 対なので `rho_readable: false`=読まない)。域外の食事 −0.95・間食 −0.83 も負。この 2 腕は最初の tick から別物(最初の食い違いは 3 対とも tick 0)なので、CRN が効かないのは R-71 §1-2 の読みと矛盾しない(推測)。
- CRN の健全性: 最初の読みでは入力の一致が **FAIL** した。腕の欄の外の設定の差が 4 つ(`synonym_table_version`・`outside_suppression`・`presence_exit.exit_mode`・`intent.max_ticks`)あった。どれも腕の引数から導かれる値(語彙の版から辞書の版が決まる・計画実行層が off の腕では抑止が効かない・層が無いと辞書が空)なので、`arm_keys_derived` に理由つきで宣言して読み直し、`ok: true` になった(母集団の seed 1 で固定・母集団と日課のハッシュが 6 本で同じ・同じ腕の salt の間は交換可能・A/A 一致)。`report_precondition` は manifest に載っていない腕の欄として `arm_keys_unseen` に出た。

### 7. テストの数

| | 集めた数 | passed | failed | skipped |
|---|---|---|---|---|
| 前(第 1 段の後・上の §7) | 3,656 | 3,654 | 0 | 1(ほかに xfailed 1) |
| 第 2 段(全体を 1 回・48 分) | 3,686(+30) | 3,683 | **1** | 1(ほかに xfailed 1・警告は既知の 1 件) |

- 落ちた 1 件は `test_relations_on_5000_seeds_are_exchangeable_and_config_leaves_do_not_move`(`slow`)。seed 1 と 2 を省略の形で回すので `population_seed` も 1 と 2 になり、「設定の葉が全部一致」で落ちた(予定どおりの差=許容)。試験を「`population_seed` は (1, 2) で `population_seed_varies` が真・ほかの設定の葉は全部一致」に直し、この 1 件と新しい 2 ファイルを回し直して 31 passed。全体は直した後に回し直していない(直したのは試験の 1 か所だけ)。
- 対象のテスト: `tests/c7/test_salt_compare_10f.py` 20 件・`tests/engine/test_salt_seed_split_10f.py` 10 件(新しい 30 件)。

### 8. 親に確かめる点

1. **母集団の側の範囲**: 体の属性に加えて、気象の再生実日(`engine.processes.environment`)と合成世界も母集団の seed の側にした。理由は、`replay_date` が設定の節の欄で、salt で変わると salt の間の入力の一致が崩れるため。気象を salt のばらつきに含めたいなら動きの側へ戻す(1 行)。mock 日課(`agent.schedule`)を母集団の側にしたのは、W17 の日課が seed に依らない(体の ID で決まる)のに合わせたため。名前は `population_seed` のままにした(中身は「入力の seed」に近い)。
2. **幅の定義**: 設計書 §5 の「salt 間の幅(家族 95%)」を、対の差の SD を使う t(1 − α/(2m), n−1)·s_D/√n にした(m=指標の数)。各腕の SD での幅も並べた。どちらを「幅」の列にするかは未決のまま(材料 §2-1)。
3. **最初の食い違いの探し方**: 区間の前は止めて状態を書き、再開してから毎 tick にした(区間の前の毎 tick のハッシュを省く)。再開が通しと同じことは 10d の試験に頼っている。T3 は合成世界の 2 例で、通しの毎 tick と一致することを確かめた。
4. **manifest に載っていない腕の欄**: `salient_rate_per_10k`・`report_precondition` は manifest に欄が無く、入力の一致の検査では見えない(`arm_keys_unseen` で報告するだけ)。manifest に足すかは別の判断(既定の欄が増える)。
5. **導かれる設定の差の宣言**: 腕から導かれる設定の欄は、読む役の `arm_keys_derived` に人が理由を書いて宣言する形にした(自動で許すと本当の設定の漏れを見逃す)。
6. 設定の指紋に `population_seed` を載せるのは `seed` と違うときだけにした(既定のランの状態のファイルの見出しを動かさないため)。
7. 回す役は `python -m shibuya.cli` ではなく、`shibuya.cli.run` を別のプロセスで呼ぶ(腕の引数を Python の引数のまま渡すため・byte-check の道具と同じ形)。CLI に `--stop-at-tick` などは足していない。

### 9. 検収の後に直したこと

#### 9-1 S1: seed を母集団・環境・動きの 3 つに(ユーザー決定 2026-10-07)

- `run_day(environment_seed=None)`・`cli.run(environment_seed=…)`・`--environment-seed`(`shibuya.cli` と `shibuya.engine.run`)を足した。省略すると `seed` と同じ値で、今と同じランになる。設定の指紋には `seed` と違うときだけ載せる(`population_seed` と同じ)。manifest の末尾に `environment_seed`(設定の節)を足した。設定の道筋の sha256 は `457d8666…`(前 `3fe95edb…`)。
- `engine/processes/runner.py`: 気象(`EnvironmentProcess`)・大きな催し(`LargeEventProcess`)・道路工事(`RoadWorksProcess`)の `master_seed` に環境の seed を渡す。域外居住(`RailProcess`)は母集団の seed のまま。どの過程も属性は増やしていない(状態台帳は不変)。
- 表は `POPULATION_RNG_DOMAINS`・`ENVIRONMENT_RNG_DOMAINS`・`MOTION_RNG_DOMAINS` の 3 つ(`engine/run.py`)。`resolve_sub_seed()` を足し、`resolve_population_seed()`・`resolve_environment_seed()` はその別名にした。

表 9-1: 用途名と側(直した後)。

| 用途名 | 側 | 何を決めるか |
|---|---|---|
| `w16.sample.reserved`・`w16.sample.stratum`・`wallet.initial`・`agent.schedule`・`body.weight`・`body.eer`・`geometry.desired_speed`・`engine.processes.rail` | 母集団 | 体の属性(抽出・財布・mock 日課・体の定数・希望歩行速度・域外居住) |
| `world.synthetic` | 母集団 | 合成小世界の店の種別と在庫(世界資産が無いときだけ) |
| `engine.processes.environment` | **環境** | 気象の再生実日の層と日(manifest の `replay_date`・`start_sim_datetime`・`calendar`) |
| `world.large_event` | **環境** | 大きな催しの会場(日ごと) |
| `world.road_works` | **環境** | 道路工事の辺(日ごと) |
| `world.delivery_inbound` | 動き | 入荷の抽選。**つなぎ**(下の注) |
| そのほかの用途名と `run_salt`・出勤の塩・艦隊の呼ごとの種 | 動き | §2 の表と同じ |

- **`world.synthetic` を母集団の側に残した理由**: 中身(`world/assets.py` の `synthetic_assets`)は、格子の上の店の種別と初期在庫を引くだけ。世界資産(固定のデータ)の代わりの「舞台の構造」で、日ごとに変わる出来事ではない。環境の側に置くと、「天気も変える」salt の比較で地図そのものが salt ごとに変わってしまう。また mock の日課の拠点はこの世界のセルの上に引くので、母集団と組にしておく方が筋が通る。合成世界は世界資産が無いときだけ使う(既定のランでは使わない)。
- **つなぎ(親が台帳に写す)**: `world.delivery_inbound`(入荷の抽選)は、本来は店の発注と配達員(エージェントの行動)で決まるもの。今はエンジンの処理によるつなぎなので、動きの側に置いた(ユーザー決定 2026-10-07)。表の説明にも「つなぎ」と書いた。台帳の行の案: 「入荷の抽選(`world.delivery_inbound`)はエンジンの処理によるつなぎ。店の発注と配達員の行動が入ったら置き換える。乱数は動きの seed」。
- **気象の再生実日についての事実**: 既定のランは影のある日に絞る(W9 は 1 再生日ぶん=`EnvironmentProcess` の `prefer_shadow_days`)。このため世界資産では、環境の seed を変えても実日は 2026-07-28 の 1 日に決まる(環境の seed 1〜5 で確かめた)。環境の seed で動くのは、今は大きな催しの会場と工事の辺。影の絞りを外して同じ過程を作ると、環境の seed 1〜6 で実日は 5 通りに分かれた(試験で固定)。
- **salt の道具**: `salt_runs.py plan --environment-mode fixed|salt`。`fixed`(既定)は「天気は同じで動きだけ変える」で、環境の seed を `--environment-seed`(省略=母集団の seed)に固定する。`salt` は「天気も変える」で、環境の seed を salt と同じ値にする。索引に `environment_mode`・`environment_seed` を書く。読む役の入力の一致は、対の間で環境の seed が同じこと、`fixed` なら全部のランで同じことを確かめる。`salt` では同じ腕の salt の間の `replay_date`・`start_sim_datetime`・`calendar.*` の差を許し、`environment_derived_diffs` に出す。
- `seed_exchangeability`: `manifest.environment_seed` の差を許容に入れ、`environment_seed_varies` で報告する。
- 試験: 環境の seed だけ変えると、大きな催しの会場と工事の辺が変わり、体の属性の 16 列と、環境の側以外の用途名の鍵の seed の組が同じ。動きの seed だけ変えると、気象(実日・層・開始日時)と催しと工事が同じ。母集団の seed だけ変えても環境は同じ。鍵の seed の記録は 3 つの seed(動き 3・母集団 7・環境 11)で 4 構成とも振り分けどおり。

#### 9-2 S2: CRN の健全性の「未検査」

- 全体の `ok` を 3 つの値にした: `True`(全部確かめて通った)・`False`(どれかが落ちた)・`None`(落ちたものは無いが確かめていないものがある)。`status` に `ok`・`fail`・`未検査`、`unchecked` に確かめていないものを書く。
- A/A のランが無いと `未検査`。T0 > 0 で T0 より前の checkpoint が 1 本も無い対は `pre_t0` が `ok: None`・`status: 未検査`。T0 = 0 は `対象外`(`ok: True`)。落ちたものがあれば、未検査があっても `fail`。

#### 9-3 S3 の 8 件

1. **静的な網羅の試験の穴**: (1) `from shibuya.core.rng import stream as _s`・`from shibuya.core import rng as R` の別名を追う (2) 名前つきの `domain=` を読む (3) seed を引数に持つ関数の中のハッシュ(blake3・xxh64)の呼び出しを全部拾い、場所ごとに分類した表と突き合わせる(乱数の塩は `MOTION_SALTS` の 3 つと一致・新しい場所が出たら落ちる)(4) `self.domain` の手書きの対応を、`ConversationManager`・`MockLLM` の実物の既定の値と突き合わせる。(1)(2) はわざと書いた断片で拾えることを試験にした。
2. **差 ÷ 幅の読み**: 全部の行に `diff_over_width_reading`(「差 ÷ 幅は記述。幅に対の差の SD を使うので、|差 ÷ 幅| > 1 は対の差の t 検定を α/m で棄却するのと同じ意味になるが、K20 (a) の検定ではない」)を付けた。記述のみの行の `status_note` にも「差 ÷ 幅が 1 を超えても K20 (a) の検定ではない」と書いた。
3. **導かれる差の宣言の値**: `arm_keys_derived` を `{道筋: {"base": 値, "arm": 値, "reason": 理由}}` の形にした。対ごとに実際の値と照らし、違えば `arm_keys_derived_mismatch` に出して落とす。理由だけの古い形は止める。対ごとの設定の差の値(基準と腕)を `config_diff_values` に出す。
4. **腕の欄の決め方**: 2 つの腕で値が違う引数(片方だけにある引数を含む)だけを腕の欄にする(`arm_keys_of`)。道筋は完全一致で比べ、下の木(`名前.鍵`)を許すのは値が辞書の引数だけ(`arm_tree_keys`)。
5. **ρ の警告**: `warn_ratio_over_1` は 5 対以上のときだけ立てる。5 対未満で比が 1 を超えたら `ratio_over_1_unread`(読まない印)だけを立てる。§6 の「比 > 1 の警告」は、この形では警告にならない(3 対)。
6. **スクラッチの使い回し**: `salt_runs.py plan` は `--scratch` が空でなければ止める。最初の食い違いの探し方の置き場(`fine_*`)も空でなければ止める(前のランの状態のファイルを拾わない)。
7. **試験の注記**: 「比 15/12」を「比 14/12(腕の平均 14・基準の平均 12)」に直した(式は前から 14/12)。
8. **seed の型**: 読む役の seed の比べ方を `seed_key()`(型と値)にした。`1` と `"1"` は別とみなす(`core.rng` で `i:1` と `s:1` の別の鍵)。対の間の母集団の seed・環境の seed もこれで比べる。

#### 9-4 変えたファイル(直し)

| ファイル | 何を |
|---|---|
| `engine/run.py` | 環境の seed(9-1)・3 つの表・`resolve_sub_seed` |
| `cli.py` | `--environment-seed`・`cli.run(environment_seed=…)` |
| `engine/processes/runner.py` | 気象・大きな催し・道路工事に環境の seed |
| `engine/manifest_sections.py` | `environment_seed` を設定の節に |
| `tools/c7/seed_exchangeability.py` | `environment_seed` の許容と `environment_seed_varies` |
| `tools/c7/salt_runs.py` | `--environment-mode`・`--environment-seed`・置き場が空でなければ止める |
| `tools/c7/salt_compare.py` | S2・S3-2〜S3-5・S3-8・環境の seed の入力の一致 |
| `tests/c7/test_salt_compare_10f.py` | 20 → 27 件(S2・S3-2〜S3-5・S3-7・S3-8・環境の seed の形) |
| `tests/engine/test_salt_seed_split_10f.py` | 10 → 15 件(S1・S3-1・S3-6) |
| `tests/engine/test_env_and_sections_10f.py` | 末尾の欄 2 つ・設定の道筋の sha256・関係 on の 5,000 体の試験で環境の seed も (1, 2) |
| `10f/byte_check_stage2_fix.json`・`10f/stage2_5000/`(置き換え)・`10f/stage2_5000_env_salt/`(新) | 記録(9-5・9-6) |

#### 9-5 byte-check(直した後・19 構成)

- 第 1 段 §4 と同じ手順(HEAD `74d6da8` の写しに祝日の CSV)。**19/19 一致**(final・呼数・blocks・calls の 14 列)・`src_checks` ok([byte_check_stage2_fix.json](byte_check_stage2_fix.json))。最後の checkpoint の behavior-hash と full-hash も 19 構成すべて HEAD と同じ。

#### 9-6 5,000 体 mock の実例(回し直し)

腕と母集団の seed は §6 と同じ。並列 3。

| | 置き場 | 7 本の時間 | 最初の食い違いの探し方 | CRN の健全性 |
|---|---|---|---|---|
| 天気は同じ(`--environment-mode fixed`・環境の seed 1) | [stage2_5000/](stage2_5000/) | 87.7 秒(1 本 27.5〜30.5 秒) | 15.6 秒(3 対とも tick 0) | `ok: true`・`status: ok`・環境の seed は全部 1・導かれる 4 欄の宣言と実際の値が一致 |
| 天気も変える(`--environment-mode salt`) | [stage2_5000_env_salt/](stage2_5000_env_salt/) | 91.0 秒 | 回していない | `ok: true`・環境の seed は 1, 2, 3 |

- 「天気も変える」の 6 本の final は §6 と同じ(直す前の salt は環境も一緒に変えていたため)。数も §6 の表と同じ。
- 「天気は同じ」の主要(呼数の総数): 基準 69,978・69,498・69,613 / 腕 100,439・101,195・102,809。差 +31,785・幅 7,006・差 ÷ 幅 4.54・p 0.25(下限 0.25)=記述のみ(本数不足)。副次: 域内の食事 −4,573(差 ÷ 幅 −13.3)・域外の食事 −5,818(−19.9)・間食 +61(0.15)。呼数の幅は 10,097 → 7,006 に狭まった(3 対なので読みには使わない)。
- ρ の比が 1 を超えた 3 指標は、3 対なので `ratio_over_1_unread` だけが立ち、警告は出ない(S3-5)。
- 導かれる 4 欄の宣言: `synonym_table_version` は `undefined-synonyms-v5` / `undefined-synonyms-v2`、`outside_suppression` は true / false、`presence_exit.exit_mode` は `immediate` / なし、`intent.max_ticks` は 60 / なし([stage2_5000/metrics.json](stage2_5000/metrics.json))。

### 10. 検収の指摘ごとの扱い

| # | 扱い | 一言 |
|---|---|---|
| S1 | 直した(ユーザー決定 2026-10-07) | seed を母集団・環境・動きの 3 つに。環境=気象・大きな催し・道路工事。配送は動き(つなぎ)。合成世界は母集団(9-1 の理由) |
| S2 | 直した | `ok` は True・False・None(`status: 未検査`)。A/A なし・T0 前の checkpoint なしは未検査 |
| S3-1 | 直した | 別名・`domain=`・seed の近くのハッシュの場所の表・`self.domain` の実物との突き合わせ |
| S3-2 | 直した | `diff_over_width_reading` と `status_note` の 1 行 |
| S3-3 | 直した | `{base, arm, reason}` の宣言と実際の値の照合・`config_diff_values` |
| S3-4 | 直した | 値の違う引数だけ・下の木は値が辞書の引数だけ |
| S3-5 | 直した | 警告は 5 対以上・5 対未満は `ratio_over_1_unread` |
| S3-6 | 直した | 置き場が空でなければ止める |
| S3-7 | 直した | 注記を 14/12 に |
| S3-8 | 直した | `seed_key()`(型と値) |

### 11. 設計書 §5 への注記の案文(親が書く)

[再開と決定論 v0.1](../../../../design/v2-resume-determinism-draft.md) §5 の表の下に置く案(〔訂正(再検収 T3)〕気象・39 万体の文を事実に合わせて直した版):

> 〔注(10f・K21 (a)・2026-10-07 ユーザー決定)〕salt は 10f から「動きの seed」を指す。母集団の seed(W16 の抽出・体の属性)と環境の seed(気象の再生実日・大きな催し・道路工事)は別に渡せ、省略すると salt と同じ値になる。上の 3 本の根拠(salt 間 JSD)は 10f より前の値で、母集団の抽出(5,000 体のとき)と、大きな催しの会場・道路工事の抽選のばらつきを含む幅である。気象の再生実日は影のある日への絞りで seed に依らず同じ日だった。39 万体の行は W16 の母集団 390,067 人のほぼ全数なので、抽出の揺れは小さい。10f 以後の salt の比較は既定で母集団と環境を固定し、動きのばらつきだけの幅を出す(`tools/c7/salt_runs.py --environment-mode fixed`)。環境も変える幅が要るときは `--environment-mode salt` で回し、どちらの幅かを報告に書く。入荷の抽選は動きの側(エンジンの処理によるつなぎ)。

### 12. テストの数(直した後)

| | 集めた数 | passed | failed | skipped |
|---|---|---|---|---|
| 直す前(親が回した作業木) | 3,686 | 3,684 | 0 | 1(ほかに xfailed 1) |
| 直した後(全体を 1 回・39 分) | 3,698(+12) | 3,695 | **1** | 1(ほかに xfailed 1・警告は既知の 1 件) |

- 新しい試験は `tests/c7/test_salt_compare_10f.py` 27 件(+7)と `tests/engine/test_salt_seed_split_10f.py` 15 件(+5)。
- 落ちた 1 件は第 1 段の `test_platform_id_ignores_commit_threads_and_dependency_versions`。全体を回している間に、実行役がこの README(git で追跡しているファイル)を書き換えたため、試験の前後で git の差分の sha256 が変わり、`env_id` が一致しなかった。コードの欠陥ではない(1 件だけを回し直して passed)。試験は「試験の間に追跡しているファイルが変わらない」ことを前提にしている(第 1 段の検収の R1 と同じ種類の注意・直していない)。全体は回し直していない。
- 対象のテスト: 新しい 2 ファイル 42 passed・`test_env_and_sections_10f.py`(slow を含む)・`test_seed_exchangeability.py` は全体のランで passed(上の 1 件を除く)。

### 13. 再検収の後に直したこと(T1〜T5)

再検収 [review-10f-stage2-recheck.md](review-10f-stage2-recheck.md)(条件つき受入・T1 が条件・T2〜T5 は低い)を受けて直した。全体のテストは親が回す(実行役は対象のテストだけ)。

| # | 扱い | 中身 |
|---|---|---|
| T1 | 直した | `engine/processes/runner.py` の道路工事の行で `day_index=day_key,` がコメントの中に入っていた。`master_seed=_env_seed, day_index=day_key,  # 10f(S1): 環境の側` の形に直した。試験 `test_road_works_day_key_with_nonzero_day_index`(世界資産 300 体・(環境の seed, day_index) = (1, 3)・(5, 3)・(5, 2))で、0 日目の工事の辺と大きな催しの会場が、その日の鍵と環境の seed で作った過程の値と同じこと(鍵 0 の値と違う例であること)を確かめる。直す前の行に戻した src の写しでは、この試験が `(1, 3)` で落ちることを確かめた |
| T1 の 2 日 | 確かめた | 5,000 体・seed 1・`sim_days=2` で、HEAD `74d6da8` の写しと作業木の final・呼数・最後の日の工事の辺と催しの会場が一致([two_day_check_stage2.json](two_day_check_stage2.json))。既定 v3(活動層 on)・`day_index=0` は `47e0a85b02797e23`・142,043 呼。`day_index=3` は活動層 off で `4d629b58b39305e0`・53,709 呼(活動層 on の 2 日のランは、1 日目の表が前の日と違うと K9 のつなぎで止まる=今の仕様なので off で回した) |
| T2 | 直した | 気象を母集団の側と書いた古い説明 3 か所(`run_day` の docstring の `population_seed`・`cli` の `--population-seed` の help・runner の `_pop_seed` の上のコメント)を 3 分割に合わせた(挙動は不変) |
| T3 | 直した | §11 の案文を記録 §5 の案のとおりにした: 根拠の幅は「母集団の抽出(5,000 体のとき)と、大きな催しの会場・道路工事の抽選のばらつき」を含む。気象の再生実日は影のある日への絞りで seed に依らず同じ日だった。39 万体はほぼ全数なので抽出の揺れは小さい |
| T4 | 直した(一部は残す) | 静的な網羅の試験で、用途名を変数で受け渡す呼び出し(`"?domain"`)を許すのは `core/rng.py` の中だけにした(外に足すと落ちる・わざと書いた断片で確かめる)。seed の近くのハッシュの検査は「関数の引数か呼び出しの式に `seed` の字がある」ものだけを見る形のまま(塩を別の名前の属性に持って後でハッシュする形・モジュールの直下の呼び出しは拾わない。今の src に該当は無い=残る穴として記録) |
| T5 | 直した | `salt_runs.py plan` は腕の引数に `seed`・`population_seed`・`environment_seed` があれば理由を出して止める(置き場を作る前)。`salt_compare.py` の `main` の終了コードは CRN の健全性が ok なら 0・fail なら 1・未検査なら 3(既存のファイルの拒否は 2・`--values` は 0) |
| 再検収 §2 の注 | 記録だけ | `world.synthetic` を母集団の側にした理由のうち「mock の拠点はこの世界のセルの上に引く」は弱い(`synthesize` はセルの数だけを読む)。理由の主は「世界資産の代わりの構造で、環境の側に置くと天気も変える比較で地図が変わる」の方 |

対象のテスト: `tests/c7/test_salt_compare_10f.py` 28 件(+1)・`tests/engine/test_salt_seed_split_10f.py` 17 件(+2)。結果は下の 1 行。

- 新しい 2 ファイル・`test_env_and_sections_10f.py`(slow を含む)・`test_seed_exchangeability.py`・`tests/engine/processes` をまとめて回して **243 passed**(0 failed・3 分)。全体は親が回す。

## 第 3 段(AST と実行時の検査・K19 の検査・保存の形式)

> 実行役(Opus 5.5)の記録。親の検収の前。commit していない。範囲はアジェンダ §2 の 3・4・5(K24 (a)・K25 (a)・K23 (a)=親推奨で確定)と §4 の T4・T5・T6。
> 先に読んだもの: [アジェンダ](../../../../design/v2-d102-10f-agenda.md) §1〜§4・[10f の材料](../10f-prep.md) §3〜§5・[10d の検収](../../wallbounce-1003/review-10d.md)・[10c の検収](../../wallbounce-1003/review-10c.md) の P1〜P3・R3・R4。numpy の `np.load` の文書(`allow_pickle` の項と警告の節)を numpy.org の 2.5 の版で読んだ。
> 測った機械: 第 1 段と同じ。パスは `src/shibuya/` を省く。

### 1. 変えたファイル

| ファイル | 何を |
|---|---|
| `engine/state_codec.py`(新) | 保存の形式 npz+json の書き手と読み手。印・許可したクラスの表・`np.load(allow_pickle=False)`(§4) |
| `engine/resume.py` | 状態のファイルを npz+json に(`STATE_FORMAT` は v2・名前は `state-T<T>.npz`)。写しの `.json` の `file` に sha256 とバイト数。旧の pickle(v1・`.pkl`)は先頭のバイトで見分けて読み、`LegacyStateFormatWarning` を出す(10e まで)。台帳の宣言との突き合わせ `check_bundle`・戻す前の型の突き合わせ `check_item_kinds`。試験用の `write_state_pickle`(旧の形式を書く・10e で消す)。指紋の `_canon` で Enum を str より先に見る(`BudgetMode` が str の子のため・値は同じ) |
| `engine/run.py` | 再開で戻す前に `RS.check_item_kinds` を呼ぶ(1 行)。docstring と CLI の help の `.pkl` を `.npz` に |
| `engine/state_ledger_ast.py` | 外の状態の軸 1 の AST(`scan_external`・`check_external`)と表(診断の出口 `DIAG_EXITS`・名前の衝突 `EXT_NAME_COLLISIONS`・場所ごとの許可 `EXT_AST_ALLOW`)(§2) |
| `engine/rng_audit.py`(新) | K19 の検査。静的な一覧(`scan_sites`・`SAFE_SITES` 15・`UNDETERMINED_SITES` 16)と実行時の計器(`StreamRecorder`)と許可の表(`K19_ALLOW`)(§3) |
| `tools/c7/salt_runs.py` | 最初の食い違いの探し方が拾う状態のファイルの名前を `.npz` に |
| `tests/engine/discard_probe.py`(新) | 軸 2 の実行時の検査「捨てて同じか」の道具 |
| `tests/engine/test_state_checks_10f.py`(新) | K24・K25 の試験 20 件 |
| `tests/engine/test_state_format_10f.py`(新) | K23 の試験 27 件 |
| `tests/engine/test_resume_10d.py` | 「自分が書いたものだけを読む」の試験を npz+json の形に書き直した(壊れた・印の無い・写しの無い・ラン ID の違うファイルを拒む)。台帳の版の試験のファイル名を `.npz` に |
| `tests/engine/test_env_and_sections_10f.py` | 状態のファイルの glob を `.npz` に。別の環境の試験は pickle を直に開かず `read_state` で読んで書き直す |

既定のランの挙動は変えていない(§5)。状態台帳の行・版(`state-ledger/10f`)は変えていない。

### 2. K24 (a) AST と実行時の検査

#### 2-1 軸 1(AST)

- 対象: 外の状態の行が指す持ち主のクラスの属性 437 のうち、全部の行で軸 1 が no/diag の 356 属性。持ち主のクラスの外の読み(属性 `obj.x` と `getattr(obj, "x")`)を集める。持ち主のクラスの中の `self.x` は数えない(目的が AST では分からない)。書き(代入の左辺・`x[...] =`・`del`)と自己更新(`o.x = getattr(o, "x", 0) + 1`)は読みに数えない。`x.clear()` などの変更のメソッドは読みに数える。
- 許す読み(規則): (1) 直列化・ハッシュ・保存と戻しの書き手(`state_hashes`・`resume`・`state_ledger*`・`state_codec`・`resolve.restore_*`)(2) 診断の出口の関数 12(`RunResult.*`・センサス・checkpoints の JSON・世界過程と描画と計画実行層の計数の要約 など)(3) `engine/run.py` の `result.…` への代入の文(4) 名前の衝突(同じ名前の属性かメソッドを持ち主の外のクラスも持つ)で、受け手の名前が持ち主を指さない読み(5) 場所ごとの許可(理由つき)。
- 名前の衝突: 軸 1 が no/diag の属性では **20 個**(材料 §3-3 の 52 は全部の属性の数)。表 `EXT_NAME_COLLISIONS` に相手のクラスを理由として書いた。受け手の名前(最後の名前・`OWNER_RECEIVER_ALIASES` の別名)が持ち主を指す読みは、衝突でも規則 (1)〜(3)・(5) で見る(例: `presence.n_arrivals` は衝突だが受け手が持ち主なので許可が要る)。
- 今の src の数: 持ち主の外の読み 238 か所(54 属性)。衝突 163・出口の関数 28・結果の組み立て 29・場所ごとの許可 18 か所(許可の項は 17・11 属性)。走査は約 1.0〜1.3 秒。
- 場所ごとの許可 17 項の中身: 層別の起床の数えと診断の行の差分の基準(`presence.n_arrivals`・`n_departures`・`bridge.n_tape_misses`)・再開に渡す台帳の検査(`ledger.money.n_transfers`)・結果の組み立てのうち `result.…` の文の外にある読み(`sleep_counts`・`stats` 2 か所・`text_id`)・店の決め手の名前(`chooser.last_habit`=O13 と O68 の diag にだけ入る)・tick の終わりに控えを捨てる書き(`rel_layer.origin_of.clear()`)・標準ライブラリの同名(`timedelta.seconds`)・**看板の露出 `renderer.signage_exposures`(下の §7 の 1)**。
- 古い許可(どの読みにも当たらない許可・衝突の表の余り・理由の空)も落とす。

#### 2-2 軸 2(実行時「捨てて同じか」)

- `tests/engine/discard_probe.py`: 通しのランの tick T の頭(`resolve.advance_body` の手前)で、軸 2 が discardable の外の状態の属性(208 道筋のうち持ち主が立っているもの)を、**ランの最初の tick の頭の値**に戻して続ける。T から後の checkpoint の final・behavior-hash・full-hash・tick ごとの呼数・診断の行・日の締め・呼数の合計を通しと比べる。
- 「新しいインスタンスの値」の近似(**未リサーチ(expedient)**): 最初は `__init__` の直後の値で試したが、配線で鍵を張る辞書(会話の `origin_counts`)が空に戻ってランが止まった。再開の新しいインスタンスは作った後の配線を通るので、ランの最初の tick の頭の値(配線と日の頭の初期化の後)にした。初期化の分の計数を含む(差は計数だけの見込み=推測)。その時点で無い属性(`chooser.last_habit`・`chooser.stats`=選び手が classical でない構成の別のクラス)は戻せないので報告に出す。値の写しは、配列は `copy`、数と文字列だけの容器は `deepcopy`、関数や参照はそのまま(`rel_layer._invite_salt` と描画の口 3 本)。
- SoA の discardable の列(全部が死蔵)は触らない(10b の AST が読み手 0 を見る)。除外の一覧の cache も触らない(再開では配線が作り直す=戻す値の近似が当たらない)。

#### 2-3 結果(T4)

| 試験 | 結果 |
|---|---|
| 軸 1: 今の src | 問題 0 |
| T4 軸 1: 実物の src の写しに「`act_layer.n_wander_bad`(O66 diag)を挙動の分岐で読む」と「`getattr(act_layer, "n_set")`」の断片を足す | 2 件で落ちる(場所と行の鍵 O66 が出る)。`run.py` の外の `result.…` は出口でないので 1 件残る |
| 軸 1: 衝突の扱い | `decision.n_calls`(相手のクラス)は許し、`arbiter.n_calls_total`(持ち主)は落とす |
| 軸 2: 合成世界 100 体・全腕・2 日・T=420・1320・1860 | 通しと全点一致(208 道筋のうち持ち主の立つものを全部戻した) |
| 軸 2: 世界資産 300 体・2 日(既定 v3 の T=750・classical+記憶+関係の T=1320) | 全点一致 |
| T4 軸 2: O91 `conv.n_opened` を discardable にした台帳(10d の 14 項目の 1 つ) | T=750 で戻すと behavior-hash・full-hash・診断の行・日の締めが食い違い、final も後で食い違う(落ちる) |
| T4 軸 2 の 2 例目: O92 `ledger.money._snap` を捨てる(世界資産・T=1860) | 2 日目の締めのセンサスが食い違う(落ちる)。0 日目の途中(T=750)では基準がランの頭の値のままなので食い違わない=2 日目で見る |

- 捨てる計器の時間: 合成世界 100 体・2 日・毎 tick の checkpoint で 1 本 約 16 秒(通しと同じ)。

### 3. K25 (a) K19 の検査

#### 3-1 静的(AST)

- `stream()`・`philox()` の呼び手(別名の import と `domain=` を拾う・httpx の `client.stream` は拾わない)31 か所を、行番号でなく(ファイル・関数・用途名)で同定した。
- **静的に安全 15 か所**(1 語目が無いか定数 7・引く語数が定数で 4 以内 8)を `SAFE_SITES` に固定した。増えても減っても落ちる。
- **静的に決まらない 16 か所**は `UNDETERMINED_SITES` に、実行時の検査での扱いを理由として書いた。ここに無い呼び手が出たら落ちる(新しい呼び手を実行時の検査に回す合図)。
- 「静的に 4 語を超える」(1 語目が値で、定数の語数が 5 以上)は、表に関係なく落ちる。

#### 3-2 実行時の計器

- `StreamRecorder`: `core.rng.philox` と、それを直に import したモジュールの名前を包み、作った流れを全部覚える。「使ったブロック」=作った時と終わりのカウンタの 0 語目の差。同じ(用途名・1〜3 語目)で 0 語目の違う流れどうしの、使ったブロックの区間の重なりを「実際の重なり」とした(材料 §4-2 と同じ数え方)。
- 許可の表 `K19_ALLOW`(用途名 → 扱いと理由)。実際の重なりは扱い `overlap` だけ、「1 語目に値を置いて 2 ブロック以上」(潜在)は `overlap` か `latent` が要る。

表 3-1: 実測(実際の重なりのある用途名)。

| 構成 | 実際の重なり(用途名: 数) |
|---|---|
| 既定 v3・世界資産 5,000 体・seed 1・1 日 | `w16.sample.stratum` 185(最大 2,602 ブロック)・`body.weight` 1・`body.eer` 1。final `993276d5e5bb5cbe`・69,978 呼(包まないランと同じ) |
| 既定 v3・世界資産 300 体・2 日 | `world.delivery_inbound` 1・`world.road_works` 1・`world.salient` 1 |
| 合成世界 200〜300 体・全腕・率 ×1000・2 日・stateful(既定) | `perception.p_notice` 15〜22・`world.delivery_inbound` 1・`world.salient` 1・`world.public_service_dispatch` 1 |
| 同・counter | `perception.p_notice` 15・`world.delivery_inbound` 1(counter の 2 本は 1 語目が 0 で隣が無い) |

- 許可の表は 8 用途名、どれも扱い `overlap`・理由の頭に「10e で直す」。既定 v3 の 3 つ(P1・R3)のほかに、P2(`p_notice`)・P3(`delivery_inbound`)・R4(`road_works`)と、stateful の日の Generator 2 本(`world.salient`・`world.public_service_dispatch`)を載せた。**重なりの修正はしていない**(10e)。
- **気づいたこと**: 10c の検収の P3・R4 は「`--day` が 1 違う別のランの間」の重なりだったが、10d の複数日のランでは **1 本のランの中で** 0 日目と 1 日目の流れが実際に重なる(配送・工事・stateful の顕著行為と出動)。日をまたいだ乱数の相関なので、10e で直すときの範囲に入る(§7 の 2)。
- 計器の費用: 包む処理は 1 本の時間の 1 割未満(5,000 体・1 日で 約 43 秒=材料の 29 秒より長いのは並べて回したため・数えは 1 秒未満)。

#### 3-3 結果(T5)

| 試験 | 結果 |
|---|---|
| 静的: 今の src | 15 と 16 の表と一致 |
| T5 静的: 断片 `stream(seed, "…", agent, tick).random(5)` | 「静的に 4 語を超えて引く」で落ちる。`g = R.stream(…); g.random(n)` は「決まらない呼び手が増えた」で落ちる。`random((2, 2))` は安全 |
| 実行時: 合成世界・率 ×1000・2 日(stateful と counter) | 許可の表の中だけ。計器で包んでも final は同じ |
| 実行時: 世界資産 300 体・2 日 | 許可の表の中だけ |
| 実行時: 既定 v3・5,000 体・1 日(`slow`) | 185・1・1 と final・呼数が既知の答えと一致。ほかの重なり 0 |
| T5 実行時: 体ごとの流れ(1 語目=体)から 5 語引く呼び手を足す | 最大 2 ブロック・重なり > 0 で落ちる(許可の表の外の 1 件だけ) |
| 空の許可の表 | 全部の重なりが「許可の表に無い」で出る |

### 4. K23 (a) 保存の形式(npz+json)

#### 4-1 形

- 1 つの npz(`np.savez_compressed`)に、配列 `a0`・`a1`・… と、`meta`(UTF-8 の JSON を uint8 の配列にしたもの)。JSON は `{"codec", "doc": {"header", "soa", "items", "inflight"}}` の値の木。見出しは素の JSON に限る(写しの `.json` と同じ値)。
- 印: `__t`(タプル)・`__s`(集合・要素の正準の JSON の昇順・`fz` で frozenset)・`__d`(鍵が文字列でない辞書と辞書の子クラス・挿入順・`c` は OrderedDict・Counter・defaultdict)・`__o`(許可したクラス+欄・NamedTuple は要素・Enum は値)・`__nd`(配列の参照)・`__g`(Generator の state)。**実行役が足した印 4 つ**(未リサーチ(expedient)): `__ns`(numpy のスカラー。np.float32 などの型を保つ・浮動小数は `float.hex`)・`__f`(有限でない浮動小数。JSON の外の NaN を書かない)・`__q`(deque)・`__r`(同じ可変の値を 2 か所以上から指す=最初の 1 回に中身・2 回目から番号)。
- 同一性: 同じ配列は同じ `__nd` の名前、同じ list・辞書・集合・許可したクラスの値・Generator は `__r` で 1 つのまま戻る(pickle と同じ範囲)。集合の要素と辞書の鍵は並べ替えるので `__r` を使わない(中身の写し)。循環は書くときに止める。
- 許可したクラスの表 `ALLOWED_CLASSES` は 17(`ActivityPayload`・`Target`・`TargetKind`・`PlanBlocks`・`WakeCandidates`・`DeferralQueue`・`EventClass`・`WakeCondition`・`EventBudget`・`Counters`・`DayClose`・`GoodsRef`・`InboundStarts`・`Session`・`PendingInvite`・`ConvState`・`LLMCall`)。表の全部が import でき、独自の pickle の口(`__reduce__`・`__getstate__`・`__setstate__` など)を持たないことを試験で見る。`InboundStarts`(`runner.rail._inbound`)は 10d の帰無の腕の再開の試験で見つかった(材料 §5-2 の 11 道筋の数えには無かった)。
- ビット生成器は Philox・PCG64・PCG64DXSM・MT19937・SFC64 だけ。種 0 で作ってから状態を置く(OS の乱数を引かない)。

#### 4-2 読み(読むだけでコードが動かない)

- `np.load(io.BytesIO(data), allow_pickle=False)`。numpy の文書(2.5): `allow_pickle` は「pickle を許さないなら object の配列の読みは失敗する」・既定 False、警告の節は「信用できない出どころには allow_pickle=False」。object の配列は numpy が ValueError で拒み、`StateFormatError` にする。meta の JSON は NaN・Infinity を拒む(`parse_constant`)。
- クラスは許可の表の名前だけ。`importlib.import_module` は表に書いたモジュールだけに使う(表の外の名前は import もしない=試験で確かめた)。組み立ては `cls.__new__(cls)` に属性を置く形(`__init__`・`__post_init__`・`__setstate__` を呼ばない)・Enum は `cls(値)`・NamedTuple は `_make`。dataclass は欄が全部そろうこと、属性の名前は識別子であることを見る。
- どこからも指されない配列が npz にあれば拒む。印が 2 つ以上・定義の前の `__r`・数でない `__ns` の dtype も拒む。
- **台帳の宣言との突き合わせ**(`check_bundle`): 見出しの必須の欄と型・SoA の置き場と列が台帳の行(discardable でない列)・dtype と形が行の型の宣言(`i4x11` なら `(体数, 11)`)・同じ置き場の列の長さ・外の状態の道筋の集合と順が `full_items`。**戻す前**(`check_item_kinds`)に保存の値と今の値の型を比べる(数は Python と numpy の整数・浮動小数を同じ仲間・配列は dtype と次元の数・辞書は型と、今の値に鍵があるときは鍵の型の組)。
- 壊れた・取り違えたファイルは写しの sha256 とバイト数・ラン ID・形式の版で止める。

#### 4-3 旧の pickle

- 〔訂正(検収 U1)〕下の「先頭のバイトで選ぶ」形では、外から来たファイルでも pickle が開かれた。今は切替口と拡張子 `.pkl` がそろったときだけ開く(§8)。§4-2 の「読むだけでコードが動かない」は npz+json の読み口についての主張。
- 先頭のバイトが `SHIBUYA-STATE ` なら 10d の読み口(先頭の行の sha256・写しのラン ID を pickle を開く前に検査)で読み、`LegacyStateFormatWarning` を出す。読んだ後も `check_bundle` を通す。
- HEAD `129da80` の写しの src で書いた `.pkl`(合成世界 100 体・記憶+関係・T=750)を作業木で再開して、通しと 36 点の checkpoint が全部一致・警告が出ることを確かめた。

#### 4-4 結果(T6)

| 試験 | 結果 |
|---|---|
| resume == straight(`tests/engine/test_resume_10d.py` の全部・npz+json で書いて読む) | 38 passed(合成世界の全腕の毎 tick・世界資産の毎 tick・6 構成・別のプロセス・艦隊の未着の呼・counter など) |
| 19 構成 × 世界資産 300 体 × 2 日 × 止める時刻 2 つ(T=750・1440)の再開 | 38 本とも checkpoint の全点と呼数の合計が通しと一致(状態のファイル 90〜161 KB) |
| 印の往復 | 型・挿入順・float32 の演算・NaN・2^70・印と同じ名前の普通の鍵・Enum・dataclass・Generator の続きの乱数が一致 |
| 同一性 | 凍結した `Target` を 3 か所から・配列を 2 か所から・list を 2 か所から指す値が 1 つのまま。世界資産 300 体の日の境目の実物の状態で、共有の組(`_last_close` を含む)が書く前と読んだ後で同じ・外の状態の値の直列化が全部同じ |
| `allow_pickle=False` | `np.load` の呼び出しは `allow_pickle=False` の 1 回だけ・`pickle.loads`・`load`・`Unpickler` を呼ばない(呼べば落ちる仕掛けで確かめた) |
| 拒否 | `os.system`・`subprocess.Popen`・`builtins.eval`・許可の外のビット生成器・辞書の型・defaultdict の作り手・無い配列・印 2 つ・定義の前の参照・object の dtype・Enum の値・dataclass の欄の不足・object の配列・NaN・形式の版・余った配列 |
| 台帳の宣言 | dtype(int32 → int64)・2 次元目の幅・列の長さ・discardable の列・道筋の不足で `read_state` が止める。辞書 → list・配列の dtype の違いで再開が止める |
| 旧の pickle | 警告が出て読め、再開が通しと一致。壊れたものは sha256 で止める |
| 大きさ(5,000 体・`slow`) | 下の表 4-1。1.1 MB 以下 |

表 4-1: 既定 v3・5,000 体・seed 1・テープつき・2 日のランを T=1440 で止めた状態(中央値 5 回・この機械・ほかのランと並べて回した)。

| 構成 | npz+json | pickle(旧) | 比 | 書き(npz/pickle) | 読み(npz/pickle・検査込み) |
|---|---|---|---|---|---|
| 既定 v3 | 768,757 B | 4,306,062 B | 0.179(−82%) | 0.162 / 0.014 s | 0.040 / 0.009 s |
| 記憶+関係 | 1,452,997 B | 21,870,395 B | 0.066(−93%) | 0.313 / 0.047 s | 0.076 / 0.027 s |

- 既定 v3 の npz+json は 1 体あたり 154 B(10d の pickle は 861 B/体・材料の試作は 205 B/体)。材料の試作(1.03 MB)より小さいのは、meta の JSON も npz の中で圧縮したため。
- 予算(アジェンダ §7 の「状態の書き出し 137 B/体」)は今も超えている。再宣言は 10e の項のまま。

### 5. byte-check(19 構成)と 2 日のラン

- 手順は第 1 段 §4 と同じ(HEAD `129da80` の写しに祝日の CSV を写す)。mock/classical 5,000 体・seed 1・1 シミュ日・テープつき。
- 結果: **19/19 一致**(final・呼数・blocks・calls の 14 列)・`src_checks` ok([byte_check_stage3.json](byte_check_stage3.json))。既定 v3 は `993276d5e5bb5cbe`・69,978 呼、帰無 `72cb9cd52982da74`・100,439 呼、記憶+関係 `40409ebed834126b`・72,930 呼(第 2 段と同じ)。
- **2 日のラン**: 5,000 体・seed 1・`sim_days=2`・既定 v3(活動層 on・day_index 0)・テープつきで、HEAD の写しと作業木の final `47e0a85b02797e23`・142,043 呼・テープの calls と blocks の中身の sha256 が一致([two_day_check_stage3.json](two_day_check_stage3.json)。第 2 段の記録とも同じ)。
- 状態を書くランの final も変わらない: 5,000 体・2 日を T=1440 で止めたランの final は 1 日のランと同じ `993276d5e5bb5cbe`(表 4-1 の測り)。
- 記録: [k19_runtime_stage3.json](k19_runtime_stage3.json)(表 3-1 の 4 本)・[resume_19x2_stage3.json](resume_19x2_stage3.json)(§4-4 の 19 構成 × 2 時点)。

### 6. テストの数(対象のテスト)

| ファイル | 件数 | 結果 |
|---|---|---|
| `tests/engine/test_state_checks_10f.py`(新) | 20(`slow` 1 を含む) | 20 passed(約 5 分) |
| `tests/engine/test_state_format_10f.py`(新) | 27(`slow` 1 を含む) | 27 passed(約 1 分) |
| `tests/engine/test_resume_10d.py` | 38 | 38 passed(約 9 分) |
| `tests/engine/test_state_ledger_10b.py` | 70 | 70 passed(AST の検査の許可に `state_codec.py` の `__slots__` の読みを 1 つ足した後) |
| `tests/engine/test_env_and_sections_10f.py`・`tests/c7/test_salt_compare_10f.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/c7/test_seed_exchangeability.py` | 73 | 73 passed |

新しい 2 ファイルと 10b は 1 回にまとめて 117 passed(9 分)。全体は親が回す(実行役は回していない)。`test_platform_id_ignores_commit_threads_and_dependency_versions` は試験の間に追跡しているファイルが変わると落ちる(第 2 段 §12 と同じ注意)。

### 7. 親に確かめる点

1. **看板の露出 `renderer.signage_exposures`(O64・軸 1 no・軸 2 discardable)は挙動の読み**: 描画が集めた看板の露出を、同じ tick の 6 段目で記憶と親しみの層が読んで空にする(`engine/run.py`)。tick の中だけの口で checkpoint の時点では常に空なので、ハッシュと再開には効かない。軸 1 を behavior にすると behavior-hash が全構成で動くので、今は理由つきの許可に置いた。行の判定を直すか(10e の版上げに束ねるか)の判断を仰ぎたい。
2. **K19 の日をまたぐ重なり**: 10d の複数日のランでは、配送・工事・stateful の顕著行為と出動の日の流れが、1 本のランの中で 0 日目と 1 日目で重なる(§3-2)。10e で直す範囲に P1・P2・R3 と並べて入れるか。
3. **軸 2 の「新しいインスタンスの値」**: ランの最初の tick の頭の値で近似した(§2-2)。再開の新しいインスタンスとの差(日の頭の初期化の分の計数)は計数だけの見込みだが確かめていない。除外の一覧の cache は検査の外。
4. **印を 4 つ足した**(`__ns`・`__f`・`__q`・`__r`)。アジェンダの 6 つでは numpy のスカラーの型と同一性(`Target` の 12 か所)を保てないため。
5. **許可したクラスの表に `InboundStarts` を足した**(材料の 11 道筋の外)。表に載らない型は書く時点で場所つきで止まる(`/items/runner.rail._inbound` のように出る)。19 構成 × 2 時点の再開で、ほかに足りない型は出なかった。日の途中の会話(`Session`・`PendingInvite`)と艦隊の未着の呼(`LLMCall`)は 10d の試験で通る。
6. **型の突き合わせの弱いところ**: 辞書の鍵の型は今の値に鍵があるときだけ比べる。再開の新しいインスタンスの辞書は空のことが多く、ほとんどの道筋で比べられない。値の中身の検査は、戻した後の full-hash が見出しの値と同じかの検算(10d)だけ。
7. 旧の pickle の読み口と `write_state_pickle` は 10e で消す前提(K23 (a))。
8. **写しの `.json` の名前**: 状態のファイルの写しは拡張子を `.json` に替えた名前なので、同じディレクトリに同じ T の `.npz` と旧の `.pkl` があると写しを共有する(後に書いた方の写しになる)。もう片方はラン ID か sha256 の違いで読み口が止まる(黙って読み違えることは無い)。新しいコードは `.pkl` を書かないので、古いランの置き場に新しいランの状態を書いたときだけ起きる。

### 8. 検収の後に直したこと(U1〜U7)

検収 [review-10f-stage3.md](review-10f-stage3.md)(条件つき受入・条件は U1)を受けて直した。親の全体のテスト(直す前の作業木)は 3,746 passed・0 failed。

| # | 扱い | 中身 |
|---|---|---|
| U1(条件) | 直した | 中身の先頭のバイトで旧の pickle の口を選ぶのをやめた。`read_state(path, *, allow_legacy_pickle=False)`・`run_day(resume_legacy_pickle=False)`・CLI の `--resume-legacy-pickle`(`shibuya.engine.run` と `shibuya.cli` で同じ綴り)。**切替口と拡張子 `.pkl` がそろったときだけ** pickle を開く。それ以外で中身が pickle(10d の先頭の行か pickle の印 0x80)なら、開かずに `StateFormatError`。切替口は指紋に入れない(`FINGERPRINT_SKIP`)。`resume.py` の docstring を「npz+json は外から来たファイルでもコードを動かさない/旧の pickle は切替口つきで、自分のファイルに限る(先頭の行の sha256 と写しは出どころの証明にならない)」と書き分けた |
| U1 の試験 | 足した | 検収役の再現(`__reduce__` で印のファイルを作る pickle・10d の形の先頭の行・ラン ID の合う写し)を 5 通りで: 名前 `.npz`/切替口あり+名前 `.npz`/名前 `.pkl`+切替口なし/先頭の行の無い生の pickle 2 通り。どれも `StateFormatError` で、`pickle.loads` は呼ばれず、印のファイルはできない。`run_day` の再開でも同じ。旧の形式の往復の試験は切替口つきに直し、切替口なしでは止まることも見る。**`129da80`(第 3 段の前の HEAD)の `git archive` の写しで書いた `.pkl` から、切替口つきで再開すると通しと全点一致**する試験を足した(git か commit が無ければ飛ばす・10e で消す) |
| U2 | 直さない(親の判断・10e で K19 と一緒に) | 日の鍵の流れは、次の日に 1 ブロック(4 語)ずれた**写し**になる。`K19_ALLOW` の上の注と §3-2・§7 の 2 に書いた。**10e まで、2 日以上のランの配送・工事・顕著行為・出動の日ごとの差を主張に使わない** |
| U3 | 直した | `__o` の組み立て: 欄の名前が `__` で始まるか識別子でなければ拒む。欄の集合が宣言と**一致**すること(dataclass は `fields`・dataclass でない値のクラスは新しい表 `CLASS_FIELDS`=`DeferralQueue` 8 欄・`EventBudget` 4 欄)。書く側も同じ一致を見る(違えば書く時点で止める)。`CLASS_FIELDS` がクラスの属性(AST)と同じことを試験で見る |
| U4 | 直した | `loads` の組み立ての部分を広く包み、拒否を全部 `StateFormatError` にそろえた(桁あふれ・ビット生成器の状態の形・Enum の型・深い JSON の `RecursionError` など)。`read_state` の拒否(写し・見出し・台帳の版・`check_bundle`)も `StateFormatError`(`ValueError` の子)。**開く前の部品の検査**を足した: 部品は npy だけ・npy の見出しの形 × 型の大きさ+見出しの長さが部品の大きさと一致(巨大な形を宣言する見出しで numpy が先に確保するのを止める)・object の dtype を拒む・展開した後の合計の上限 `MAX_UNCOMPRESSED_BYTES` 2 GiB(39 万体の見込みの約 6 倍・**未リサーチ(expedient)**・10e の予算の再宣言で見直す)・meta の上限 512 MiB |
| U5 | 直した | 場所ごとの許可を `ExtAllow(属性, 当たる数, 場所)` にして、当たる数が宣言と違えば落とす(今は 17 項・18 か所・`prev_tape_misses = bridge.n_tape_misses` だけが 2)。許可した行と同じ文字列の行を `run.py` の別の関数に写すと落ちる試験を足した |
| U6 | 書いた | 下の §8-1 と `state_ledger_ast.py` の限界のコメント。衝突の属性を持ち主と違う名前の受け手で読むと見えないことを試験で固定した(持ち主の名前なら落ちる) |
| U7 | 直した | 合成世界の「捨てて同じか」の T に日の境目の前後(1439・1441)を足した(全点一致)。乗数を 1.5 にした classical の腕で O90 `_ipf_cache` をわざと discardable にして帯の途中(T=757)で捨てると、behavior-hash と日の締めが食い違って**捕まる**(final と呼数は同じ=作り直した c_t がこのランでは同じ値。軸 1 が behavior の行なので属性そのもののハッシュで捕まる)。O37 `_pulled_in_today` は T=750・1439・1441 のどれでも**捕まらない**: 読み手は O70 の計数(discardable・比べない)だけで、discardable にすると full-hash からも外れる=この検査の外。日の途中の再開で要ることは再開の試験(10d)が見る。どちらも試験に残した |
| U8 | 直していない(依頼の外) | K19 の束ねる鍵に seed を入れること・作り直しの数の固定は 10e の K19 と一緒に |

#### 8-1 検査の限界(U6・U7)

- **軸 1(AST)**: 名前の衝突の 20 属性は、受け手の名前が持ち主と違えば(`conv_mgr.n_blocks` など)衝突として許すので見えない。受け手の名前が持ち主を指せば(`conv.n_blocks`)落ちる。衝突でない属性は別名の受け手でも落ちる。`getattr(obj, 変数)`・`vars()`・持ち主ごと関数に渡した先・持ち主の中の `self.x` の目的は見えない。
- **軸 2(実行時)**: その構成とその T で働く漏れしか拾わない。合成世界には金の台帳・物の台帳・計画実行層が無く、合成世界の試験ではこれらの道筋を触っていない(`absent_owner`)。世界資産の試験(既定 v3・classical+記憶+関係・`_snap`)が金の台帳と計画実行層を見る。読み手が discardable の計数だけの行(O37)はこの検査では見えない。戻す値の近似(ランの最初の tick の頭の値)が再開の新しいインスタンスと違うのは、金の台帳の生の行の 5 配列だけ(検収の測り)で、それらは再開の試験が本物の値で見る。

#### 8-2 確かめ(直した後)

- byte-check(19 構成・HEAD `129da80` の写しと直した後の作業木): **19/19 一致**・`src_checks` ok([byte_check_stage3_fix.json](byte_check_stage3_fix.json))。
- 2 日のラン(5,000 体・既定 v3): final `47e0a85b02797e23`・142,043 呼・テープの calls と blocks の中身が HEAD と一致([two_day_check_stage3_fix.json](two_day_check_stage3_fix.json))。
- 対象のテスト: `test_state_checks_10f.py` 25・`test_state_format_10f.py` 43・`test_state_ledger_10b.py` 70・`test_env_and_sections_10f.py`・`test_salt_seed_split_10f.py`・`tests/c7/test_salt_compare_10f.py` をまとめて **204 passed**(11 分・警告は既知の暦の 2 件)。`test_resume_10d.py` **38 passed**。全体は親が回す。
- 新しい試験の数: `test_state_checks_10f.py` 20 → 25(U5 1・U7 の T 2・U7 の項目 2)、`test_state_format_10f.py` 27 → 43(U1 7・U3 4+1・U4 3+1)。

## 親の検収(第327・2026-10-07・第 3 段)

- 親: 全体のテスト **3,769 件(3,767 passed・failed 0・skipped 1・xfailed 1)**(直した後の作業木)。`test_u1_resume_from_a_pkl…` もこの作業木では通った(再検収役の機械ではパスの長さで落ちた=環境の問題)。
- 別のサブの検収: 1 回目 条件つき受入([review-10f-stage3.md](review-10f-stage3.md)・U1 旧 pickle を中身の先頭のバイトで自動で開く=`.npz` という名前の悪い pickle でコードが動いた)→ 直し → 2 回目 **受入**([review-10f-stage3-recheck.md](review-10f-stage3-recheck.md)・24 経路で pickle は開かれない)。
- 残す低い欠陥(10e で扱う): V1 §3-2・§7 の 2 に U2 の注が無い(本節で補う: **10e まで、2 日以上のランの日ごとの差を主張に使わない**。日の鍵の流れが次の日に 1 ブロックずれて重なるため=U2・K19 と一緒に 10e で直す)/ V2 写しの `.json` が壊れていると `JSONDecodeError`・`UnicodeDecodeError` がそのまま出る(読みは止まりコードは動かない)/ V3 場所ごとの許可は当たる数だけを固定し、許可した行を挙動の場所に移しても数が同じなら通る / U8 K19 の実行時の数え方の細部 / 屋外広告の接触(O64)の軸 1 の分類。

