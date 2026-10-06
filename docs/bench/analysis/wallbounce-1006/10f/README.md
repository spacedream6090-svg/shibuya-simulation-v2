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
