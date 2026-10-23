# 10f 第 1 段の検収(別の検収役・Opus 5.5)

> 対象: 未コミットの作業木(HEAD `8c8a77c`)。実装役の報告([README.md](README.md))は信用せず、別の方法で確かめた。
> src・tools・tests の既存ファイルは編集していない。わざと壊す検査は作業木ではなくスクラッチに写した src・tests で行った(親の全体テストが走っている最中だったため。§4)。パスは `src/shibuya/` を省く。

## 結論

- **条件つき受入**。既定の結果は不変(final・呼数・テープの parquet が HEAD とバイトで同じ)で、環境の欄の 3 か所の一致と O75 → O95 の分割も確かめた。
- ただし 2 件の重い欠陥がある。(N1) `relations.init` が設定の節に入っているため、関係 on の腕は 5,000 体で seed 1/2 が交換不可能と判定される(実装役の 300 体の確認は関係の初期化が空のランで、何も試していなかった)。(N2) 依存の版が 1 つ変わるだけで golden の試験 10 か所が警告なしに A/A に落ちる。テストは緑のまま golden の検査が消える。
- N1・N2 を直し、N3〜N5 の扱いを親が決めれば受入できる。N6 以下は記録と手順の直し。

## 1. 欠陥(重さ順)

### N1(高): `relations.init` が設定の節にあり、関係 on の腕で seed の交換可能性が落ちる

- どこ: `engine/manifest_sections.py:95-96`(`relations.{k}` の設定の一覧に `"init"` がある)。
- 中身: `relations.init` の下には定数(`density`・`k`・`tiebreak`・`tenure_hash` など)と、**seed で動く観測**(`groups.household/work/school`・`candidate_pairs`・`candidate_pairs_all`・`candidate_pairs_copresent`・`edges_before_tau`・`dropped_by_tau`)と、**壁時計**(`init_seconds_nondeterministic`)が混ざっている。表は `relations.init` を丸ごと設定にしているので、全部が設定として比べられる。
- 再現: mock 5,000 体・世界資産・1 日・`v3_mem_rel`(`vocab_version=v3, memory=on, relations=on`)の seed 1 と 2 を `cli.checkpoints_payload` にして `seed_exchangeability.compare` に渡すと、`mode=sections`・**`exchangeable=False`**・未説明 9 欄(上の 8 欄と `init_seconds_nondeterministic` 0.065 対 0.068)。
- 実装役の確認で漏れた理由: README §3 の「世界資産 300 体・1 日で 4 構成(… 記憶+関係 …)の seed 1/2 で設定の節の差が 0」は、300 体では関係の初期化が `{"groups": {}, "candidate_pairs_all": 0, "reason": "no_groups", "init_seconds_nondeterministic": 0.0}` になり、何も試していなかった(検収役が 300 体・240 tick で確認)。`manifest_check_10f.py` の交換可能性は既定 v3 しか比べていない。
- 直し方の案: `relations.init` は観測を親にし、定数の鍵(`density`・`k`・`slot_minutes`・`tiebreak`・`tenure_weeks`・`tenure_hash`・`w17_single_day`)だけを子の道筋で設定にする。壁時計の欄(`*_nondeterministic`)は観測の節(または比べない節)に明示する。直した後、5,000 体の関係 on の腕と classical+関係 の腕で seed 1/2 の PASS を記録に足す(§3 に classical と店の記憶の結果)。

### N2(高): golden の行の鍵に依存の一覧の sha256 があるので、pytest などの版を上げると golden の検査が黙って消える

- どこ: `engine/resume.py` の `environment_fields()`(`platform` に `deps_sha256`・`deps_count`)/`tests/golden_env.py`(行が無ければ A/A だけ)/golden を使う 6 本のテスト。
- 中身: 今の依存の一覧(48 本)には `pip`・`pytest`・`hypothesis`・`rich`・`certifi`・`matplotlib`・`shibuya-sim` 自身など、結果のビットに効かない配布が入っている。どれか 1 つの版が変わると `platform_id` が変わり、golden の 5 つの表(10 か所)は全部 A/A だけになる。テストは **PASS のまま**で、skip も警告も出ない。T7 の `993276d5…` の直書き(`test_state_ledger_10b.py:723`)は A/A も無く、比べずに通る。
- 再現(スクラッチの写し・§4 の a2): `_deps_digest` に `pytest==99.0` の 1 行を足すと `platform_id` が `2c54e621365e279a` → `364626a7ff29e0a7` に変わる。`test_env_and_sections_10f.py` 全件と golden の 3 本(`test_presence_derive_v2::test_v2_rule_on_the_real_w17…`・`test_presence_executor::test_derive_folding…`・`test_relations_tenure::test_relations_on_arm_golden_old_and_new`)は **14 passed・警告 0**。`platform` から `cpu` を抜いた場合(a1)も golden は全部 PASS。落ちたのは欄の集合を固定した `test_environment_fields_shape_and_ids` だけ。
- 「安全側」かどうか: 安全側ではない。誤って一致と言うことは無いが、検査が消えたことに誰も気づかない(fail-open)。A/A は「同じ環境で 2 回同じ」しか見ないので、版の変更と既定の挙動の退行が同じコミットで起きても捕まらない。
- 直し方の案(どれか、または組み合わせ):
  1. 行の鍵(`platform_id`)はビットに効くものだけにする(Python・numpy・numba・llvmlite・blake3・pyarrow など明示した一覧・OS・machine・numpy の命令セット)。`deps_sha256` は環境の欄に残すが鍵には入れない。
  2. 今の環境が未登録なら**大きな音を出す**: 未登録を報告する専用のテスト(`pytest.fail`、または既定は fail で環境変数 `SHIBUYA_GOLDEN_AA_OK=1` のときだけ skip にする)と、`assert_aa` の中の `warnings.warn`。全体テストの要約に必ず残す形にする。
  3. 依存の一覧そのもの(下の N4)を記録し、鍵が外れたときにどの配布が変わったかを差で示せるようにする。

### N3(中): 混ざった辞書で、表に無い鍵は親の節を継ぐ。観測を親にした辞書に設定の鍵を足しても、どのテストも落ちない

- どこ: `engine/manifest_sections.py` の規則(最も長く一致する道筋)と、観測を親にした 18 個の辞書(`energy`・`classical`・`relations`・`store_choice` など)。
- 再現(検収役の探り): 実ランの manifest に `energy.brand_new_cfg = 1`・`classical.new_param = "x"` を片方だけ足すと、`exchangeable=True` のまま(観測の差に数えられるだけ)。表の向きを逆に変えても、捕まるのは spot check の欄だけ。スクラッチの写しで (i) `attendance_rate` を観測に変えると、合成世界のテスト 2 本は PASS(捕まえるのは世界資産のある `test_seed_exchangeability_passes_for_v3…` だけ)。(ii) `energy` 全体を設定に変えても、合成世界の節のテストは PASS(合成世界では `energy` が seed で動かない)。
- 実装役のテストの範囲: 一番上の欄は全部載っている(`test_every_top_level_manifest_field_has_a_section`・§4 の b で落ちることを確かめた)。一番上の欄は静的な辞書で、`l4_audit_fields()` の欄も固定なので、mock と実艦隊・`sim_days>1` で増える一番上の欄は無い(`run.py:1156-1296` を読んで確かめた)。入れ子の鍵は網羅を見ていない。
- 捕まえ方の案:
  1. **混ざった辞書は葉まで明示する**: 18 個の辞書の葉(動的な鍵は `group_size_minutes.*` のような wildcard)を全部表に書き、代表のラン(既定 v3・帰無・記憶+関係・記憶+店・classical+記憶+関係・`sim_days=2`・5,000 体の関係 on)を平坦化して、混ざった辞書の下で明示の道筋に当たらない葉があれば落ちるテストにする。
  2. **設定の葉は seed で動かない**: 上の代表のランを seed 1/2 で回し、設定に分けた葉が全部一致することを確かめるテスト(N1 の型を捕まえる)。5,000 体の関係 on は重いので、全体テストの束か夜間の検査に置く。
  3. **表の固定**: 設定の節の道筋の一覧の sha を golden にし、節を変えたら理由つきで更新を求める(設定 → 観測の黙った付け替えを捕まえる)。道具は manifest の中の表を信じる作りなので、表そのものの固定は src 側のテストでしか守れない。

### N4(中): 指示の「`pip freeze` の写し」が残っていない。依存は sha256 と本数だけ

- どこ: `engine/resume.py` の `_deps_digest`。アジェンダ K26 の親推奨の文言は「今は `pip freeze` の写しと sha256 だけ」。
- 影響: `platform_id` が外れたとき、どの配布が変わったかを後から言えない。N2 の 3 と合わせて、一覧の本体を manifest の環境の欄か、状態の見出しとテープの脇のファイルに残す(48 行で約 1 KB)。

### N5(中): T1 の byte-check が 3 構成だけ。アジェンダは 19 構成

- どこ: アジェンダ §4 T1「既定の byte-check は 19 構成で不変」/README §4 は 3 構成。
- 検収役は既定 v3 と relations-on の 2 構成で、テープのディレクトリの全ファイル(blocks.parquet・calls.parquet)を生のバイトの sha256 で HEAD と比べた(一致)。O95 の分割は全構成の behavior/full-hash を動かし、`run.py` の manifest は全構成で欄が増えるので、19 構成の byte-check(10d と同じ手順)を回して記録に残すのがよい。

### N6(中〜低): `env_id` は dirty の作業木の中身を区別しない

- どこ: `engine/resume.py` の `_git_state`(`git_commit` と `git_dirty` の真偽だけ)。
- 中身: 同じ commit の上で src の未コミットの変更が違う 2 本のランは、`env_id` が同じになる。今回の 10f のランは全部 `git_dirty=true`(`manifest_sections.py` が未追跡)なので、`env_id` から使ったコードを特定できない。
- 案: `git diff HEAD -- src tools` と未追跡の `src/**/*.py` の中身から作るハッシュ(`code.src_diff_sha`)を足す。`git_dirty` は README §8 の 2 への意見(下)のとおり、範囲を src に絞った欄と全体の欄に分ける。

### N7(低): `git status` が index のロックを取りうる

- どこ: `engine/resume.py` の `_git_state`(`git status --porcelain`)。
- 中身: `git status` は index を更新するとき、必須でないロック(`index.lock`)を取ることがある。全体テストや並列のランの最中に親が `git add`・`commit` すると、ロックがぶつかって親の git が失敗しうる。git の推奨どおり `git --no-optional-locks status --porcelain`(または環境変数 `GIT_OPTIONAL_LOCKS=0`)にする。git の挙動は記憶に基づく(この場では未確認・Web は使っていない)。
- あわせて: `git -C <写しの根>` は、写しが別の git リポの中に置かれていると外のリポの commit を拾う。`git rev-parse --show-toplevel` が写しの根と一致するかを確かめる形が安全。

### N8(低): 10d の記録の「10e で比べるのはこの値」に訂正の伝播が無い

- どこ: `docs/bench/analysis/wallbounce-1003/10d/README.md:357`(behavior-hash `b3ccfa6797f2c418` ほか・full-hash `fa168793db2b6433` ほか)。
- 10f で全構成の値が置き換わった(検収役も既定 v3 `1f4d96b1d8dfa701`/`64f2aa138e8a6bfe`・relations-on `b2e49d9cc5c2ccce`/`8f25c6b0f453bb4b` を再現)。CLAUDE.md §5 の訂正の伝播の検査に従い、10d の該当行に〔訂正(10f)〕と 10f の表へのリンクを添える。README §4 の表の「後」の値は `byte_check.json` に入っていない(`state_hashes_10b` が全部 null)ので、値を JSON にも残す。

### N9(低): テストの細部

- `test_t1_two_runs_in_the_same_environment_agree` の `env_id` の一致は、同じプロセスのキャッシュ(`_ENV_CACHE`)を読むだけなので必ず通る。別プロセスの一致は検収役が確かめた(5,000 体の 10 プロセスで全部 `af8485f03221839b`)。テストにするならサブプロセスで 2 回。
- `test_near_tiebreak.py` の A/A では、`mid`・`old` の 2 本を回したあと比べずに捨てる(5,000 体ではないが 1,500 体 × 2 本の無駄)。A/A のときは少なくとも `new != old`(切替が効く)を残すか、回さない。
- `run.py` で `result.env_fields` とテープの `run_meta` が同じ辞書を共有し、`run_manifest_fields()` の `dict(self.env_fields)` は浅い写しなので、manifest の `environment.platform` を書き換えると結果の側も変わる。深い写しにする。
- `_ENV_CACHE` はプロセスの寿命の間ずっと残る。長く動くプロセス(対話の環境・常駐の艦隊)でコミットした後のランは、古い `git_commit` を書く。`run_day` の頭では `code` だけ毎回取り直すのがよい。
- README §2 の表の `git_commit` の値「`8c8a77c2`(頭 8 桁)」は表示の省略で、欄に入るのは 40 桁。表で注記する。

## 2. 実装役の §8 の 9 件への意見

1. 鍵を `env_id` でなく `platform_id` にしたのは妥当(`env_id` だとコミットのたびに外れる)。ただし `deps_sha256` は鍵から外し、未登録は大きな音を出す(N2)。
2. 未追跡のファイルも数えるのは必要(今回の `manifest_sections.py` は未追跡の src)。ただし文書の未追跡でも true になって意味が薄い。範囲を src・tools に絞った欄と差分のハッシュを足す(N6)。
3. どちらにも寄せず、混ざった辞書は葉まで明示し、明示に当たらない葉はテストで落とす(N3 の 1)。どうしても片方なら、品質最優先の方針に合わせて「設定を親」(大きな音)。
4. 振り分けは、`relations.init` が誤り(N1)。そのほかは既定 v3 と relations-on の 5,000 体の seed 1/2 で、設定の節に seed で動く葉は無かった(classical と店の記憶は §3)。
5. 予定どおりで、検収役も値を再現した。10d の記録への伝播が漏れている(N8)。
6. 再開では、親と子で `platform_id` が違えば警告を出す(決定論の保証は同じ環境だけ)。再開の欄に親の `env_id` も残す。
7. 書き足すべき。検収役も写しに `data/calendar/syukujitsu.csv` を足して回した(暦の 2 欄は作業木と一致)。
8. 妥当。docstring のとおり、途中の `set_num_threads` は映らないと明記してあればよい。
9. 費用は許容できる。問題は費用より、黙って A/A に落ちること(N2)。

## 3. 確かめたこと(コマンドと結果)

### 3-1 既定の結果は不変(検査 1)

- 手順: `git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28` をスクラッチに展開し、`data/calendar/syukujitsu.csv` を足した(写しの src のファイルの一覧が `git ls-tree HEAD src` と一致することも確かめた)。写し(`PYTHONPATH` で指定)と作業木で、`cli.run(n_agents=5000, seed=1, world_dir="data/world/v2", tape_path=…, **構成)` を 1 本ずつ回し、テープのディレクトリの全ファイルを生のバイトの sha256 で比べた。あわせて manifest・`process_counters`・checkpoint を比べた(10b・10c の 14 列の道具は使っていない)。
- 既定 v3(`w6_v3_default`): final `993276d5e5bb5cbe`(10d の記録と一致)・69,978 呼。`blocks.parquet`・`calls.parquet` はバイトで同じ。違うのは `run_meta.json` だけで、環境の 2 欄を抜くと HEAD と同じ。`process_counters` は同じ。
- relations-on(`v3_mem_rel`): final `40409ebed834126b`・72,930 呼。同じく parquet 2 本はバイトで同じ。
- manifest(10f の 3 欄を抜いて平坦化): 違うのは `daily`(締めの後の状態ハッシュ)・`state_hashes.{behavior_hash, full_hash, ledger_version, full_external_bytes_by_row.O75/O95}`・`state_hashes_end_of_day.{behavior_hash, full_hash}` だけ。relations-on では壁時計の 2 欄も違う(決定論でない欄)。実装役の `manifest_check.json` と同じ。
- checkpoints の JSON(`checkpoints_payload`): 4 点の `behavior_hash`・`full_hash` が動く(O95 の分割で予定どおり)。`combined` 系は同じ。**c7 の道具で 10d の checkpoints と 10f の checkpoints を突き合わせると、この 2 欄は食い違う**。
- 気づいたこと: 同じ構成でも、テープを書くかどうかで full-hash が変わる(`bridge._interned`=O85 のバイト)。実装役の seed の比較(テープなし)で観測の差が 316 欄、検収役(テープあり)で 317 欄になったのはこのため。欠陥ではない。

### 3-2 `env_id` の 3 か所(検査 2)

- 実装役のテスト `test_env_id_is_the_same_in_the_three_places`(合成世界 2 日・日の境目で止める)は通った。
- 別プロセスの一致: 5,000 体の作業木のラン 8 本(既定 v3 の seed 1/2・relations-on の seed 1/2 ほか)で、manifest と `run_meta.json` の `env_id` は全部 `af8485f03221839b`。
- 作業ディレクトリの違い: リポの根・ドライブの根・一時ディレクトリの 3 か所から `environment_fields()` を呼び、`platform_id` は全部 `2c54e621365e279a` で同じ(`src/shibuya_sim.egg-info` があっても依存の数は 48 のまま)。git の無い写しでも `platform_id` は同じで、`env_id` だけ変わる。
- キャッシュ: プロセスの中では写しを返す。`refresh=True` は 1 本のテスト(`test_commit_does_not_move_the_platform_id`)だけが使い、最後に取り直している。古い値を返しうるのは長く動くプロセスの場合だけ(N9)。

### 3-3 `seed_exchangeability`(検査 4)

| 試した入力 | 結果 | 実装役のテストで固定済みか |
|---|---|---|
| (a) 設定の欄を変える: `rng_scheme`・`memory_n`・`l4_scale`・`energy.rate`・`relations.k` | 全部 FAIL | `rng_scheme`・`state_hashes.ledger_version`・`attendance_rate`(世界資産)は固定。ほかは未固定 |
| (b) 観測だけ違う(合成世界・300 体 6 構成・5,000 体の既定 v3) | PASS(5,000 体の既定 v3 は観測の差 317 欄) | 合成世界と 300 体の既定 v3 は固定 |
| (b′) 5,000 体の relations-on の seed 1/2 | **FAIL**(N1) | 未固定 |
| (c) 表の無い manifest(legacy) | HEAD の道具と出力が同じ(`note` を除く全部の鍵・3 組) | 「legacy で FAIL」だけを固定 |
| (d) 環境だけ違う | 警告だけで PASS | 固定 |
| 観測を親にした辞書に新しい鍵 | PASS のまま(N3) | 未固定 |
| 両方の表で `rng_scheme` を観測に付け替え | PASS(表は manifest の中のものを信じる) | 未固定(N3 の 3) |

- 300 体・240 tick の 6 構成(既定 v3・記憶+関係・記憶+店・classical+記憶+関係・v1 edge・帰無)と合成世界の 2 日(関係 off/on)は全部 PASS。ただし 300 体では関係の初期化が空(N1)。

### 3-4 O75 → O95(検査 6)

- 読み手: `crowd.flow_dir8`・`crowd.coherence` を属性として読む所は src・tools に 0(書くのは `processes/crowd.py` だけ・ほかは台帳の行)。`getattr`・`vars`・`__dict__` で crowd を丸ごと読む所も無い。tests は `tests/engine/processes/test_crowd.py` の過程の単体の試験だけ。docs/bench は 10b の台帳の表の JSON(記録)だけ。
- 台帳: `test_state_ledger_10b.py` 全件が通る(193 行・外の状態 95・網羅と AST)。
- 版の上げ: リポの中(gitignore の下も)に `state-T*.pkl`・`state-T*.json` は無い。状態のファイルを読むのは `tests/engine/test_resume_10d.py`・`10d/resume_check_10d.py`・`10f/state_format_probe.py` で、どれもその場で書いて読む。古い版のファイルを読む経路は無い。

### 3-5 テスト

- `.venv/Scripts/python.exe -m pytest -q tests/engine/test_env_and_sections_10f.py tests/engine/test_state_ledger_10b.py tests/engine/test_10a_review_fixes.py tests/test_manifest_roundtrip.py tests/engine/processes/test_crowd.py -p no:cacheprovider -o addopts=""` → **131 passed・1 warning**(10c 以前のテープの既知の警告)・3 分 46 秒。
- 集めた数: `pytest --collect-only -q tests` → **3,646**(README の「集めた数 3,646」と一致)。passed 3,644 は全体を回していないので確かめていない(親の全体テストに任せる)。

### 3-6 記録の数の突き合わせ(検査 8)

| README の数 | 検収役 | 一致 |
|---|---|---|
| `env_id` `af8485f03221839b` | 同じ(10 プロセス) | 一致 |
| `platform_id` `2c54e621365e279a` | 同じ(3 か所の作業ディレクトリ・git の無い写し) | 一致 |
| 依存 48 本・`sha256:e71efcf6…` | 48 本・`sha256:e71efcf65b0f…` | 一致 |
| 既定 v3 `993276d5e5bb5cbe`/69,978・relations-on `40409ebed834126b`/72,930 | 同じ | 一致 |
| behavior/full の前 → 後(既定 v3・relations-on) | 同じ 8 値 | 一致(帰無は回していない) |
| 台帳 193 行 | テストで 193 | 一致 |
| 観測の差 316 欄 | 317 欄(テープありのため O85 が 1 欄多い・§3-1) | 説明がつく |
| 集めたテスト 3,646 | 3,646 | 一致 |

- `git_dirty` は未追跡のファイルも数えるので、今の作業木では常に true(`docs/bench/analysis/wallbounce-1006/10f/` が未追跡)。`env_id` が文書の追加だけで変わることはない(dirty の真偽は同じ)が、逆に dirty の中身の違いも区別しない(N6)。

### 3-7 規律(検査 9)

- 環境の欄の実値: `cpu` は「Intel64 Family 6 Model 198 Stepping 2, GenuineIntel」(型番だけ)・`os_version` は版番号だけ。機械の名前(`platform.node()`)とユーザー名は環境の欄の JSON に含まれない(検収役が両方を文字列で探して 0)。
- 新しいファイルと変更した記録: 絶対パス・ユーザー名・機械名の grep は 0。`tools/scan_secrets.py` に変更と新規のファイル 10 本を渡して CLEAN。新しいファイルは全部 LF。

## 4. わざと壊した検査

作業木は親の全体テストが走っている最中だったので、作業木の src・tests・tools・pyproject と、テストが読む docs(予算の宣言・錨・w6 の再生成)をスクラッチに写した。`data/` はジャンクションでつなぎ、`PYTHONPATH` で写しの src を使って壊した(`shibuya.__file__` が写しを指すことを確かめた)。壊す前の写しで対象のテストが通ることも確かめた。最初の 1 回は docs が無いために落ちたので数えず、docs を足して回し直した。

| | 壊し方 | 期待 | 結果 | 戻した |
|---|---|---|---|---|
| a1 | `environment_fields` の `platform` から `cpu` を抜く | golden が A/A に落ちたことを報告する | `platform_id` → `6bf9ad7eb7e9d20f`。golden の 2 本は**黙って PASS**。落ちたのは欄の集合を固定した形の試験 1 本だけ | 写しを元に戻し、`cmp` で作業木と同じ |
| a2 | 依存の一覧に `pytest==99.0` を 1 行足す(版上げの模擬) | 同上 | `platform_id` → `364626a7ff29e0a7`。**14 passed・警告 0**(golden 3 本を含む)= N2 | 同上 |
| b | `PATHS` から `rng_scheme` を消す | 一番上の欄のテストが落ちる | 落ちる(「節の決まっていない manifest の欄: ['rng_scheme']」) | 同上 |
| c | `llm_calls_total` を設定の節にする | seed 違いの 2 本で FAIL に戻る | 落ちる(合成世界の節のテストの最初の assert) | 同上 |
| c2 | `daily` を設定の節にする | 同上 | 落ちる | 同上 |
| c3 | `energy` を丸ごと設定の節にする | 同上 | **合成世界のテストは PASS**(合成世界では energy が seed で動かない)。捕まえるのは世界資産のテストだけ(N3) | 同上 |
| c4 | `rng_scheme` を観測の節にする | 落ちる | 落ちる(spot check の assert) | 同上 |
| c5 | `attendance_rate` を観測の節にする | 落ちる | 合成世界の 2 本は PASS。世界資産の 1 本だけが捕まえる | 同上 |

- 作業木は一度も編集していない。検査の前後で `git diff` の sha256 は `df3fce239691960b…` のまま、未追跡の 3 ファイルの sha256 も同じ、`git status --short` も同じ。

## 5. 追記: classical と店の記憶の 5,000 体(N1 の範囲)

mock 5,000 体・世界資産・1 日・テープつき・seed 1 と 2(作業木)。

| 構成 | final(seed 1 / 2) | 呼数 | 交換可能 | 未説明の差 |
|---|---|---|---|---|
| `v3_classical_mem_rel` | `28ea80375e7ee646` / `98a92a962599f29c` | 110,395 / 110,866 | **False** | N1 と同じ `relations.init.*` の 9 欄だけ(観測の差 690) |
| `v3_mem_store` | `e89fc1cdc327cf57` / `34884cba55e952e5` | 69,978 / 69,849 | True | 0(観測の差 720) |

- N1 は関係 on の腕すべて(classical の有無によらない)に及ぶ。classical と店の記憶の辞書(`classical.*`・`store_memory_summary.*`・`store_choice.*`)の設定の葉には、seed で動くものは無かった。
