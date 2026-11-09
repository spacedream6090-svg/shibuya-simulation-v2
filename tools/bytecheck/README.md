# tools/bytecheck — byte-check(決定論の確かめ)

基準の commit と比べる側の src で同じ構成を回し、下の「比べるもの」が両側で同じかを確かめる道具。比べるのは、25 欄・
テープの置き場の全ファイルのバイト(sha256)と 2 表のスキーマ・manifest と `run_meta.json` の全欄(比べない欄は名前と
理由つきの一覧で外す)・全 checkpoint の値。発注は [返事その 7 §2 の 4](../../docs/design/prompt-2026-11-09-reply7.md)。
前の道具 [byte_check_10e.py](../../docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py) の働きを引き継いだ
(前の道具は記録の再現のために残してある)。第346 の検収(H1・M1〜M4・L 群)で比べるものと確かめを足した。

> **CI が緑でも決定論は確かめていない。** byte-check は data(gitignore の下)と 1 回 7 分ほどのラン(38 本)が要るので、
> CI では回せない。**作者の機械で回す。** CI の ci-1 が回すのは、この道具の試験(`tests/tools/test_bytecheck.py`=構成の
> 表・比べ方・写すファイルの一覧・つなぎの扱い・偽のエンジンで回す `one` と `side`・`run` の配線)だけ。

## 版上げのときに回す 1 行

リポの根(作業木の根)で、venv の python で:

```
python tools/bytecheck/cli.py run --work C:\bc<N> --out-dir <記録の置き場>/bytecheck --jobs 6
```

- `--work` は短い道筋で、無いか空のディレクトリ(Windows の道筋の長さの上限を避ける)。**git の作業木の中は断る**
  (写しの木の根を上へ辿る読み口が作業木の docs を読みうる)。`<N>` は devlog の番号など。
- 基準は既定で `HEAD`(`--base <commit>` で替える)。比べる側は既定で作業木の `src`(`--src <道筋>` で替える)。
  commit の前に回せば「この変更で比べるものが 1 つも動かないか」を確かめられる。
- 終了コード: **0=全構成で比べるものがすべて同じ**・**1=動いた欄がある**・**2=誤り**(引数・`--kw` が JSON の辞書で
  ない・ランの誤り・写しの木の不足・読んだ src の違い・写しの一覧に無いファイルを開いた・写しの木の上の階を開いた・
  両側の条件の違い・前のランの JSON・つなぎを外せなかった)。
- 呼び手の環境に `SHIBUYA_` の変数があると止まる(構成が黙って変わらないように。続けるなら `--inherit-env`)。

ほかの組:

```
python tools/bytecheck/cli.py run --work C:\bc<N>p --out-dir <置き場> --set parent4 --jobs 4   # 親の 4 構成
python tools/bytecheck/cli.py run --work C:\bc<N>a --out-dir <置き場> --set arms --jobs 2      # 腕 on の 2 構成と 7 変数
```

## 何を確かめるか

- 構成: 19 構成(`--set all19`)=W6 の 15 腕(現行 8・旧 6・golden の帰無腕 1)+店の記憶・関係・古典・古典+記憶+関係。
  表は `configs.py`(前の道具の `wave2_bytecheck.configs()` と同じ並びと引数=試験で確かめる)。
  `parent4`=w6_v3_default・v3_mem_store・v3_classical・v3_classical_mem_rel。`arms`=w6_v3_default・v3_classical を、
  両側とも `SHIBUYA_DECISION_PORT=port`・`SHIBUYA_CONTACT=c1`・`SHIBUYA_CONTACT_HABIT=on`・`SHIBUYA_CALENDAR=1b`・
  `SHIBUYA_CALENDAR_2=arm`・`SHIBUYA_CALENDAR_3=arm`・`SHIBUYA_DUTIES=arm` で回す(v3-0a の README §4 の追加の確かめ)。
- 条件: mock(古典の構成は古典の方策)・5,000 体・seed 1・1 シミュ日・テープつき(`--agents`・`--seed`・`--world` で替えられる)。
  両側の `PYTHONHASHSEED` を `0` に置く(呼び手の値に任せない・side の JSON の `pythonhashseed` に残す)。
- 比べ方: 値の正準の JSON(鍵を並べる)が同じなら同じ。辞書の鍵の並びは見ない。`0` と `0.0`・`True` と `1` は違う値、
  `NaN` は両側にあれば同じ。

### 比べるもの

**25 欄**(前の道具と同じ・`configs.COMPARE_KEYS`): `final`・`calls`・`blocks_rows`・`blocks_sha`・`calls_rows`・
`calls_column_names`・`calls_columns_sha`・`action_usage_total`・`action_usage_sha`・`calls_by_condition`・
`salient_events`・`collapse`・`noticed`・`dispatches`・`arrived`・`mean_delay_min`・`meals`・`behavior_last`・
`full_last`・`end_of_day`・`start_sim_datetime`・`replay_date`・`calendar_weekday`・`rng_scheme`・`frozen_sources`。
`blocks_sha` と `calls_columns_sha` は列の値の list のハッシュなので、Arrow の型とスキーマの見出しは映らない(下で補う)。

**第346 で足した 12 欄**(`fields.NEW_KEYS`):

| 欄 | 中身 |
|---|---|
| `tape_files` | テープの置き場の全ファイルの名(増えた・消えたが分かる) |
| `tape_sha256` | テープの置き場の全ファイルのバイトの sha256(`run_meta.json` を除く=git の commit を持つので下で欄ごとに) |
| `calls_schema`・`blocks_schema` | 2 表の Arrow のスキーマ(列の名・型・null の可否・列とスキーマの metadata) |
| `manifest_sha` | manifest(`RunResult.run_manifest_fields()`)から比べない欄を除いた正準の JSON の sha256 |
| `manifest_fields_sha` | manifest の一番上の欄ごとのハッシュ(どの欄が動いたかを出す) |
| `manifest_skipped` | 除いた欄の道筋の一覧(値は比べないが、欄が増えた・消えたは比べる) |
| `run_meta_sha`・`run_meta_fields_sha`・`run_meta_skipped` | テープの脇の `run_meta.json` の同じ 3 つ |
| `checkpoints` | 全 checkpoint の全欄(25 欄の `behavior_last`・`full_last` は最後の 1 点だけ) |
| `n_checkpoints` | checkpoint の数 |

### 比べない欄(名前と理由つきの一覧・`fields.py`)

manifest(`fields.MANIFEST_SKIP`):

| 欄 | 理由 |
|---|---|
| `env_id` | environment の code(git の commit・dirty・差分の sha)を含めて作る ID=写しの木は git の外で空の値・比べる側は作業木の HEAD |
| `environment.code` | git の commit・dirty・差分の sha256(両側で違って当然) |
| `environment.env_id` | `env_id` と同じ値 |
| `resume.read_seconds` | 壁時計の秒(状態を読んだ時間) |
| `resume.restore_seconds` | 壁時計の秒(状態を戻した時間) |

`run_meta.json`(`fields.RUN_META_SKIP`): `env_id`・`environment.code`・`environment.env_id`(理由は同じ)。

どの深さでも鍵の名が `_nondeterministic` で終わる欄(`fields.SKIP_SUFFIXES`=エンジンが壁時計と宣言した欄:
`relations.wall_seconds_nondeterministic`・`relations.init.init_seconds_nondeterministic`・
`step_scope.detect_seconds_nondeterministic`)。ただし `manifest_sections`(`fields.SUFFIX_EXEMPT`=manifest の欄を節に
分ける表。鍵は欄の道筋で値は節の名=壁時計でない)の下には当てない(比べる)。

`environment` の残り(`platform`=Python と依存の版・OS・CPU、`runtime`=numba のスレッド数、`platform_id`・`schema`)は
比べる(両側は同じ機械と同じ venv で回る=違えば条件が違う)。一覧に載っていない欄が片側だけにある・値が違う、は「動いた」。

side の行には次も残すが、比べない: 壁時計(`wall_s`・`run_wall_s`・`checkpoint_s`・`checkpoint_total_s`)・
`tape_bytes`(バイトは `tape_sha256` が見る)・`final_full`・`hash_scheme`・`weather`・`world_assets_pre10e`・
`action_usage`・`full_external_bytes`(・`_by_row`)・`manifest_scalars`・`run_meta_scalars`(動いた欄の前後の値を
読むため)・読んだもの(下)。

### 両側の条件(違えば誤り=2)

`set`・`kw`・`agents`・`seed`・`world`・`env`(切替口の値)・`env_hidden`(値を書かない変数の名・艦隊の鍵を除く)・
`drop_behavior_item`・`multiset_items`(behavior-hash を弱める口が片側だけ、を含む)・`pythonhashseed`。
構成が 0・どちらかにしか無い構成・25 欄の欠け(片側でも両側でも)も誤り。

### 古い記録を比べるとき(compare)

v30a の記録(`docs/bench/analysis/v3-2026-11/v30a/bytecheck/`)のように新しい欄が無い side は、compare で 25 欄
(と `n_checkpoints`)を比べ、無い欄は行の `not_compared` と要約の `not_compared` に出す(**同じとは数えない**:
要約の `all_same` でなく `same_partial` に数え、`result` は「比べた欄は同じ(古い記録で比べていない欄がある=1 バイト
までは確かめていない)」)。このときの終了コードは、比べた欄で決める(0 か 1)。条件の欄が記録に無いものは
`conditions_not_compared` に出す。`compare --strict` なら、比べていない欄や条件があれば 2。**run は常に strict**
(両側を今の道具で回すので、欄が無ければ道具の誤り)。

## 確かめないこと

- 壁時計・刻みの時間・checkpoint の時間(記録はするが比べない)。性能は別に測る。
- `RunResult` の欄のうち manifest にも 25 欄にも入らないもの(`diagnostics` の配列など)。
- 艦隊の道と判断モデルの中身(19 構成は mock と古典。腕の判断の口も mock が答える)。
- 組に入っていない腕と切替口(`arms` の 7 変数の外)。2 日以上・別の seed・別の体数。
- data の中身の変化(両側が同じ data を読む=data が変わっても両側は同じに動く)。
- GPU。
- `PYTHONHASHSEED` の値による違い(両側を同じ値で回す=値に依る非決定は映らない)。

## run がすること

1. 基準の commit の `src` と、エンジンが読む `src` の外の追跡ファイル(`tree.TRACKED_READS`=8 本)と `--extra-path` を
   `<work>/tree` へ `git archive` で写す。
2. `<work>/tree/data` を道具のリポの `data` へのつなぎ(junction)にする(`_winapi.CreateJunction`=cmd を通さない)。
3. 基準の側(写しの `src`)と比べる側の side を回す。どちらも `PYTHONPATH` に読む `src` を置く(venv の editable の道が
   本体の src を指していても、渡した src を読む。各ランが `src_as_expected` で確かめる)。両側に同じ印(nonce)を渡す。
4. 確かめる: 両側の JSON の印がこのランのもの(前のランの JSON と取り違えない)・基準の側が写しの src を読んだ・
   両側が読んだ `shibuya` のモジュールのファイルの digest(`src_files`)が、それぞれの src の今のファイルと同じ
   (基準の側=写しの木)。違えば 2。
5. compare(strict)を書く。
6. **つなぎだけを外す**(つなぎであることを確かめてから `os.rmdir`=つなぎそのものを外す・中に入らない。中は消さない)。
   外せなければ終了コード 2 と、手で外す手順を出す。

写しの木とテープは `<work>` に残る。後始末は、つなぎが残っていないことを `cmd /c dir /AL /S <work>` で確かめてから、
`<work>` だけを指す 1 つのコマンドで消す。

## 写すファイルの一覧の決め方と、取りこぼしの防ぎ方

エンジンは `src` の外の追跡ファイルをリポの根から読む(`Path(__file__).parents[k]`・`resolve_repo_path`・`_repo_root`・
`*_RELPATH` の定数)。写しの木にそれが無いと、規則の表が空になったり錨が無かったりして、final が基準と違って見える。

- `tree.TRACKED_READS`(写す)・`tree.DATA_READS`(つなぎで見せる・有無だけ確かめる)・`tree.NOT_COPIED`(src に道筋の
  文字列として現れるが写さない=引用の文字列・構築側・19 構成が使わない腕。理由つき)・`tree.ROOT_READERS`(リポの根を
  求めるファイルと、それが読むもの)。
- **試験で防ぐ**: `tree.scan_path_refs` が src の AST から道筋の文字列(`"docs/…"`・`root / "docs" / …`・
  `("docs", "bench", …)`・`["docs", …]`・f 文字列・`joinpath(*T, NAME)`・`os.path.join(…)`・`"/".join([…])`・
  `Path("docs") / …`・`"docs/" + NAME`・`"docs/x/%s.json"`・`\` 区切り・頭の `./`・定数の名を通した結合)を集める。
  試験は、`docs`・`tools`・`tests` の道筋がすべて `TRACKED_READS` か `NOT_COPIED` に載ること、`tree.scan_root_anchors`
  の見つけたファイルが `ROOT_READERS` と同じこと、一覧の行が今も src に現れることを確かめる。src がリポの根から新しい
  ファイルを読み始めると CI の ci-1 が落ち、一覧に足すまで通らない。走査が見つけない形: 別のモジュールから import した
  名を通した結合(ランの記録で拾う)。
- **ランで防ぐ**: 各ランは監査フックで開いたファイルを記録する(`check.sort_reads`)。side は「`TRACKED_READS` と
  `--extra-path` に無い追跡ファイルを開いた」(`tree_reads_unlisted`)・「写しの木に無いファイルを開こうとした」
  (`tree_reads_absent`)・「写しの側が道具のリポのファイルを開いた」(`foreign_reads`)・「読む src の親の上の階の
  `docs`・`tools`・`tests`・`src`・`data` の下を開いた」(`outside_above_tree`=根を上へ辿る読み口が写しの木の外を
  読んだ)・「渡した src の外から `shibuya` を読んだ」(`src_loaded_outside`)を誤りにする。リポと写しの木の外で開いた
  ファイルは `outside_reads` に記録する(誤りにしない・道筋は `<home>` などに伏せ、知らない置き場は `<abs>/…`)。

古い commit を基準にするときに、その版のエンジンが今の一覧に無いファイルを読むなら(例: 2-4 V6 より前の錨
`hunger_energy_anchors_v0.json`)、`--extra-path docs/bench/anchors/hunger_energy_anchors_v0.json` で足す(両側の
写しの一覧に入る=開いても「一覧に無い」に数えない)。追跡ファイルを動かした版を比べるときも、基準の側が読む古い道筋を
`--extra-path` で渡す。今の版に無い引数を持つ構成は、`--kw` で旧値の再現の切替口を渡す(前の道具と同じ口)。

## 出力の読み方

`--out-dir` に 3 本(絶対パスは書かない。道筋は `<repo>`・`<tree>`・`<scratch>`・`<tape>`・`<home>`・`<python>`・
`<abs>` に伏せる):

- `<組>_base_<commit 7 桁>.json`・`<組>_<label>.json`(side): `runs` に構成ごとの全欄。`tool`(JSON の形の版)・`src`
  (写し/作業木)・`commit`(比べる側は作業木の HEAD。src か `TRACKED_READS` か `--extra-path` に未 commit の変更が
  あれば `+dirty`)・`nonce`・条件の欄・`env_hidden`(値を書かない変数の名)・`tree_reads`・`outside_reads`・
  `src_files`(読んだ `shibuya` のモジュールの digest。行には数 `src_files_n` と全体のハッシュ `src_files_sha`)。
  `--only` で回したときは `<組>_only_…`。
- `<組>_compare_base_<commit>_vs_<label>.json`: `summary`(構成の数・すべて同じ・一部を比べていない・動いた・誤り・
  final が同じ・`not_compared`・`result`・`exit_code`)・`checks`(両側の誤り・条件・compare・run の確かめ)・`rows`
  (構成ごとの `same`・`moved`=動いた欄と前後の値・`not_compared`・`manifest_moved` と `run_meta_moved`=動いた欄の名と
  前後の値・呼数などの差)・`not_compared_fields`(比べない欄の一覧)。

標準出力の最後に要約が出る。動いた構成は名と動いた欄の名が出て、manifest と `run_meta.json` は動いた欄の名と前後の値、
テープは動いたファイルの名、checkpoint は何番目が動いたかが続く。

## 所要時間の目安

この機械(Core Ultra 7 265K・20 コア・31 GB)で `--set all19 --jobs 6`(2026-11-09・HEAD 14b151a): 基準の側 210 秒・
比べる側 203 秒・全体 414 秒(約 7 分)。1 ランは 31〜93 秒。1 ランの最大メモリは約 0.53 GB(v3-0a の §5)。`<work>` に
残るのは写しの木 約 19 MB とテープ 約 174 MB。`--jobs` を上げると速くなるが、壁時計は比べないので結果は変わらない。

19 構成のランで写しの木から開いた `src` の外の追跡ファイルは 5 本(規則の表・つなぎの台帳・予算の宣言・空腹の構築側の錨・
活動の事前分布)。`TRACKED_READS` の残り 3 本(検証側の錨・知覚の契約・パターン台帳)は、src の静的な読み口から載せている
(このランでは開かれなかった)。

## 下の口

```
python tools/bytecheck/cli.py side --label <名> --scratch <テープの置き場> --out <side.json> [--src <src>] [--set …] [--only …] [--jobs N] [--kw …] [--extra-path …]
python tools/bytecheck/cli.py compare --a <side.json> --b <side.json> --out <compare.json> [--note …] [--strict]
```

意味は前の道具と同じ。違い: `--src` が無いときも作業木の `src` を `PYTHONPATH` に置く・`SHIBUYA_BUDGET_MD` を置かない
(写しの木の宣言の表を読む)・誤りがあれば終了コード 2。前の道具の side の JSON(v3-0a の記録など)も compare で比べられる
(上の「古い記録を比べるとき」)。
