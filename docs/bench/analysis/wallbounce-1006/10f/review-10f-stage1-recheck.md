# 10f 第 1 段の再検収(N1〜N9 の直しの確認・Opus 5.5)

> 対象: 未コミットの作業木(HEAD `8c8a77c`)。前回の検収 [review-10f-stage1.md](review-10f-stage1.md) の N1〜N9 と、実装役の報告 [README.md](README.md) §9・§10。報告は信用せず、自分のランとファイルで確かめた。
> 作業木の src・tests・tools は編集していない。わざと壊す検査は、スクラッチに写した src・tests(`data/` はジャンクション)で行った。パスは `src/shibuya/` を省く。

## 結論

- **受入**(重い欠陥なし)。N1〜N5・N7〜N9 は直っている。N6 は宣言つきの一部の直し(未追跡の src は差分のハッシュに入らない)。
- 既定 v3 と relations-on は、HEAD の写しと作業木で final・呼数・テープの parquet 2 本が生のバイトで一致した。関係 on の 2 構成(記憶+関係・classical+記憶+関係)は、5,000 体の seed 1/2 で `seed_exchangeability` が PASS した。
- 見つけた欠陥は 4 件で、どれも低い(R1〜R4)。いずれも記録の直しか小さな追加で済み、受入を妨げない。

## 1. 欠陥(重さ順)

### R1(低): N6 の残り。未追跡の src は `env_id` に入らない(今の `manifest_sections.py` がそれに当たる)

- どこ: `engine/resume.py` の `_git_state`(`status --untracked-files=no`・`git diff HEAD --binary`)。
- 中身: 未追跡のファイルは `git_dirty` にも `git_diff_sha256` にも入らない。いまの作業木では、節の表の本体 `engine/manifest_sections.py` が未追跡なので、この表の中身が違うランどうしでも `env_id` が同じになる。逆に、追跡している文書(docs)の編集だけで `git_diff_sha256` は変わり、`env_id` も変わる。README §10 の N6 の行には「src・tools に絞った欄は作っていない=未追跡の src は差分に入らない」と書いてあり、宣言はある。表で「直した」と書いている点だけが言い過ぎ。
- 直し方の案: `git ls-files -o --exclude-standard -- src tools` で出たファイルの中身を、差分のハッシュに足す(または `code.untracked_src_sha256` の欄を足す)。最小の直しなら、README §10 の N6 を「一部(宣言)」に改める。コミットの後は未追跡の src が無くなるので、実害が出るのはコミット前のランだけ。

### R2(低): 未登録の環境で、どの golden の表を飛ばしたのかが pytest の要約から分からない。標準エラーへの報告も pytest の下では見えない

- 再現(スクラッチの写しで `cpu` に `-other` を足し、`platform_id` を `6ac071a265e9a128` にした): `test_v2_rule_on_the_real_w17…`・`test_derive_folding…`・`test_classical_social::test_run_golden_and_arms`・`test_relations_on_arm_golden_old_and_new` は **4 passed・3 warnings**。要約に `GoldenUnregisteredWarning` が出る(**黙らない=N2 の直しは効いている**)。ただし、
  - 収集のときの警告(5 つの表の `GE.row`)は、場所が `tests\golden_env.py:71` の 1 項目にまとまる。文言は「golden の表の行」だけで、どの表かは出ない。`test_presence_derive_v2` と `test_derive_folding` の A/A の枝は、この収集のときの警告しか出さない。
  - `announce_once` の標準エラーの 1 行(`[tests.golden_env] …`)は、収集の間は pytest が捕まえるため画面に出ない(`-k` で 1 本だけ回して確かめた)。README §9 の「標準エラーに登録の有無を 1 回だけ書く」はコードとしては正しいが、見える経路は警告の要約だけになる。
- 直し方の案: `row(table, name)` で表の名前を受けて文言に入れる。あるいは `stacklevel=3` にして呼んだモジュールの行を要約に出す。README の記述は「要約に警告が 1 項目出る」に合わせる。

### R3(低): `PLATFORM_ID_KEYS` に、ビットの経路にある配布の一部が入っていない

- 中身: `core/hashing.py` は `xxhash` と `cbor2` を使い(xxh64 と `sha256_cbor`)、`pyarrow` は世界資産を読み、テープを書く。この 3 つは `deps` には載るが、鍵の 12 欄には入っていない。前回の検収の案(N2 の 1)も `pyarrow` を挙げていた。
- 安全側かどうか: 安全側。これらの版が変わっても行は外れず、golden と比べ続ける。値が変われば試験は大きな音で落ちる。困るのは、落ちた原因が「環境の違い」だと分かりにくいことだけ。
- 直し方の案: 3 つを `PLATFORM_ID_KEYS` に足す(足せば `platform_id` が変わるので、行の登録をし直す)。足さないなら、README §2 の「ビットに効きうる 12 欄」を「主なもの」に改め、残りは `deps` で追えると書く。

### R4(低): `git diff` の出力が利用者の git の設定で変わりうる

- どこ: `_git(root, "diff", "HEAD", "--binary")`。
- 中身: `diff.external`・`color.diff=always`・`diff.noprefix` などの設定があると、出力のバイトが変わる。同じコードでも `git_diff_sha256` と `env_id` が変わる。決定論の結果には効かず、`env_id` の安定性だけの問題。この機械の設定は見ていない。git の挙動は記憶に基づく(Web は使っていない)。
- 直し方の案: `--no-ext-diff --no-color --no-textconv --src-prefix=a/ --dst-prefix=b/` を付ける。

### 参考(欠陥ではない・宣言どおり)

- `code` の取り直し: スクラッチの git リポで確かめた。索引に載せていない編集だけでは取り直さない(宣言どおり)。`git add` の後は新しい差分のハッシュになり、コミットの後は新しい commit と `git_dirty=False` になり、`reset --hard` の後は clean に戻った。普通の `git status` を挟むと index が書き直されて取り直すことがある(1 回目の試行ではそうなり、2 回目ではならなかった)。
- `.git` がファイル(git worktree)のときは `_git_stamp` が `None` を返し、キャッシュを使わず毎回 git を呼ぶ。正しさは保たれ、費用だけが増える。

## 2. N1〜N9 の確認

| # | 判定 | 一言(確かめ方) |
|---|---|---|
| N1 | 直った | 5,000 体・世界資産・1 日・テープつきの `v3_mem_rel` と `v3_classical_mem_rel` の seed 1/2 で `mode=sections`・`exchangeable=True`・未説明 0・`unlisted` 0・環境の警告なし。関係の初期化の `groups` は空でない。設定の葉(538 欄・557 欄)の seed 間の差は 0 |
| N2 | 直った | 鍵は `PLATFORM_ID_KEYS` の 12 欄で `43cd89305417b52e`。依存に `pytest==99.0` を足しても `platform_id` は同じで、`env_id` だけ変わる(自分のプロセスで確かめた)。未登録の環境では警告が pytest の要約に出る(R2 は文言の細部) |
| N3 | 直った | 写しの `run.py` で `leave_effects` に表に無い葉 `probe_new_cfg` を足すと、`test_mixed_dict_leaves_are_all_listed_synthetic` と `…_world` の 2 本が落ちて名前が出る。設定の道筋の一覧の sha256 は `170e1c30…`(テストの値と同じ) |
| N4 | 直った | `environment.platform.deps` に 48 行。sha256 と本数は一覧から計算し直せる |
| N5 | 直った | `byte_check.json` は 19 行で全部 `all_equal`・`all_ok=True`。`state_hashes_before/after` は 19 構成とも値がある(空 0)。既定 v3 と relations-on は自分でも回して一致(§3) |
| N6 | 一部 | dirty は追跡ファイルだけ・`git_diff_sha256` あり(私の `git diff` の sha256 と同じ値)。未追跡の src は入らない(R1) |
| N7 | 直った | git の呼び出しは全部 `--no-optional-locks`。toplevel が根と違えば空(テストあり・コードを読んで確かめた) |
| N8 | 直った | 10d README §11-1 に〔訂正(10f)〕があり、10f の表と `state_hashes_after` を指す。§4-1 の pickle の注にも〔訂正(10f)〕がある |
| N9 | 直った | (a) T1 は別々のプロセスで書かれたファイルを読む (b) `mid` は A/A では回さず `new != old` を残す (c) manifest・`run_meta`・見出しは深い写し (d) `code` は git の更新時刻で取り直す(上の参考) (e) 表に 40 桁の注あり |

## 3. 確かめたこと

### 3-1 既定の結果の不変(作業木 対 HEAD の写し)

- 写し: `git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28` を展開し、`data/calendar/syukujitsu.csv` を足した(README §4 の手順)。`PYTHONPATH` で写しの src を使い、`shibuya.__file__` が写しを指すことを確かめた。
- `cli.run(n_agents=5000, seed=1, world_dir="data/world/v2", tape_path=…, **構成)` を、自前のスクリプトで 1 本ずつ回した(10b・10c の道具は使っていない)。

| 構成 | final(HEAD/作業木) | 呼数 | blocks.parquet | calls.parquet | run_meta.json | process_counters |
|---|---|---|---|---|---|---|
| 既定 v3 | `993276d5e5bb5cbe` / 同じ | 69,978 / 同じ | バイトで同じ | バイトで同じ | 環境の 2 欄を抜けば同じ | 同じ |
| relations-on | `40409ebed834126b` / 同じ | 72,930 / 同じ | バイトで同じ | バイトで同じ | 同上 | 同じ |

- manifest: 一番上の欄の並びは、新しい 3 欄(末尾)を除けば HEAD と同じ。値の差は `state_hashes`(behavior・full・`ledger_version`・O75/O95 のバイト)・`state_hashes_end_of_day`・`daily` だけ。relations-on では、ほかに壁時計の 2 欄が違う。checkpoint の `combined` は全部同じ。
- 最後の behavior/full: 既定 v3 は `b3ccfa6797f2c418`/`fa168793db2b6433` → `1f4d96b1d8dfa701`/`64f2aa138e8a6bfe`、relations-on は `2817c8ed4bc17c88`/`165666b6c42034f3` → `b2e49d9cc5c2ccce`/`8f25c6b0f453bb4b`。README §4 の表と `byte_check.json` の値に一致する。

### 3-2 `env_id` の一致(書かれたファイルで)

- 5,000 体の作業木のラン 5 本(別々のプロセス)で、manifest の `env_id` は全部 `f95555fd09778abf`。テープの `run_meta.json` の `env_id`・`environment` は manifest と同じ値。
- 状態の見出し(`.pkl` と写しの `.json`)は、実装役のテスト `test_env_id_is_the_same_in_the_three_places` と T1(別プロセス)が書かれたファイルで比べており、どちらも通った。

### 3-3 再開と再生の警告

- `warn_if_other_environment` は `warnings.warn` を 1 回出すだけで、挙動は変えない。テスト(再開も再生も final が同じ)が通った。`pyproject.toml` の `filterwarnings` が error にするのは `DeprecationWarning` だけなので、pytest の下でも止まらない(`python -W error` で回すと止まる。これは普通の警告と同じ扱い)。

### 3-4 テスト

- `pytest -q -o addopts="" -p no:cacheprovider` で `test_env_and_sections_10f.py`(slow を含む 21 件)・`test_state_ledger_10b.py`・`test_10a_review_fixes.py`・`test_near_tiebreak.py`・`test_relations_tenure.py`・`test_classical_social.py`・`test_presence_derive_v2.py`・`test_presence_executor.py`・`tests/test_manifest_roundtrip.py`・`processes/test_crowd.py` → **214 passed・1 warning**(10c より前のテープの既知の警告。golden 未登録の警告は出ない=この環境は登録済み)・13 分 50 秒。
- 集めた数 `--collect-only` → **3,656**(README と一致)。passed 3,654 は全体を回していないので確かめていない。

### 3-5 記録の数の突き合わせ

| 記録の数 | 再検収 | 一致 |
|---|---|---|
| `platform_id` `43cd89305417b52e` | 同じ | 一致 |
| `env_id` `f95555fd09778abf` | 同じ(5 本と自分のプロセス) | 一致 |
| 表 384 道筋・設定 151・混ざった辞書 21 | 384・151・21 | 一致 |
| 設定の一覧の sha256 `170e1c30…` | 同じ | 一致 |
| 依存 48 本・`sha256:e71efcf6…` | 48・`sha256:e71efcf65b0f…` | 一致 |
| byte-check 19/19 | `byte_check.json` で 19 行すべて一致・自分で 2 構成 | 一致 |
| 観測の差 316・743・698(テストなし) | テープつきで 744・699(O85 の 1 欄=前回の検収 §3-1 と同じ理由) | 説明がつく |
| テスト 3,656 集めた・3,654 passed | 3,656 集めた | 集めた数は一致・passed は未確認 |

### 3-6 規律

- 環境の欄の実値: `cpu` は CPU の型番の文字列だけ、`os_version` は版番号だけ。`deps` の 48 行に `/`・`\`・`@`(パスや URL)は無い。機械の名前(`platform.node()`)とユーザー名は、環境の欄の JSON に含まれない(文字列で探して 0)。
- 変えたファイルと新しいファイル 12 本(README・JSON 2 本・manifest_check_10f.py・前回の検収・manifest_sections.py・新しいテスト・golden_env.py・10d README・review-10c・resume.py・run.py): ユーザー名・絶対パス・機械名の grep は 0(前回の検収の記録が CPU の型番を引用している 1 か所だけ。機械を特定する情報ではない)。CRLF は 0。`tools/scan_secrets.py` は CLEAN。

## 4. 作業木を触っていないこと

- 検査の前後で `git diff` の sha256 は `8d0e7e3e04cb5fca…` のまま。`git status --short` も同じ。
- わざと壊す検査(`cpu` の書き換え・`leave_effects` に葉を足す)はスクラッチの写しだけで行い、終わった後に `cmp` で作業木と同じ中身に戻したことを確かめた。`code` の取り直しの検査は、スクラッチに作った使い捨ての git リポで行った(プロジェクトのリポでは git の書き込みをしていない)。
