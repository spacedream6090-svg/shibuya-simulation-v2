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
