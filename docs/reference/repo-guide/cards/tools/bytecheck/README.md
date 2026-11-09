# tools/bytecheck

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 1 本(このディレクトリの直下)

その他のファイル: `README.md`

## [__init__.py](../../../../../../tools/bytecheck/__init__.py)

bytecheck — 決定論の確かめ(byte-check)の道具。基準の commit と比べる側の src で同じ構成を回し、25 欄とテープ・manifest・run_meta.json・全 checkpoint を比べる。

- 決定の ID: 第 346

## [check.py](../../../../../../tools/bytecheck/check.py)

bytecheck.check — 1 構成のラン(``one``)・片側の 19 構成(``side``)・2 つの side の比べ(``compare``)・基準の commit との 1 回通し(``run``)。

- 公開の関数とクラス
  - `cmd_one`(関数): 1 構成を回し、比べる欄を 1 行の JSON で標準出力に出す(``byte_check_10e.cmd_one`` の欄+開いたファイル+H1 の欄)。
  - `compare`(関数): side の JSON 2 本を比べて compare の JSON を書く。戻り値=0 同じ / 1 動いた欄がある / 2 誤り。
  - `compare_docs`(関数): 2 つの side を構成ごとに比べる(欄ごとに同じ/動いた・前後の値)。戻り値=(compare の JSON, 終了コード)。
  - `compare_row`(関数): 1 構成の比べ(25 欄と新しい欄=正準の JSON で同じか・新しい欄が片側か両側に無ければ ``not_compared``)。
  - `condition_checks`(関数): 2 つの side の条件(:data:`CONDITION_KEYS`)の違い(誤り)と、片側か両側の記録に無くて比べていない条件の名。
  - `drop_package_metadata`(関数): 包みの名札(``*.egg-info``・``*.dist-info``)を外す(第346 親)。
  - `loaded_src_files`(関数): 読み込んだ ``shibuya`` のモジュールのファイルの digest(``src_root`` からの posix の道筋 → バイトの sha256 の頭 16 桁)と、
  - `mask_outside`(関数): リポと写しの木の外の道筋を伏せる(知っている置き場は名に・それ以外は ``<abs>/…``=ドライブと頭の ``/`` を外す)。
  - `mask_paths`(関数): ``text`` の中の道筋を伏せる(``(道筋, 置き換え)`` の並び・長いものから・``\`` と ``/`` の両方の書き方)。
  - `opened_outside`(関数): ``root`` の下で開いたファイル(``skip_tops`` の最上位と ``skip_dirs`` の下を除く)の、``root`` からの posix の道筋。
  - `parse_kw`(関数): ``--kw`` の JSON を読む(JSON の辞書でなければ ``ValueError``=ランの前に止める・検収 L3)。
  - `resolve_names`(関数): 回す構成の並び(``only`` があればそれ・無ければ組の並び)。知らない名は ``KeyError``。
  - `run`(関数): 基準の commit と比べる側の src を 1 回で比べる。戻り値=0 同じ / 1 動いた欄がある / 2 誤り。
  - `side`(関数): 片側の構成を回して side の JSON を書く。戻り値=0(誤りなし)/ 2(ランの誤り・写しの木の不足・開いたファイルの問題)。
  - `side_checks`(関数): side の JSON の誤り(ランの誤り・読んだ src の違い・開いたファイルの問題)。古い記録で欄が無いものは見ない。
  - `sort_reads`(関数): 監査フックの記録(開いたファイル)を仕分ける。
  - `stray_env`(関数): 呼び手の環境に置かれた ``SHIBUYA_`` の変数の名(run は既定で止める=構成が黙って変わらないように)。
  - `tree_label`(関数): 読む src の親の伏せ字(道具のリポなら ``<repo>``・写しの木なら ``<tree>``=検収 L8: 比べる側の誤りの文が ``<tree>`` に見えない)。
  - `verify_sides`(関数): run の確かめ(検収 M1): 基準の側が写しの src を読んだ・比べる側が渡した src を読んだ・両側の読んだ ``shibuya`` の
  - `worktree_commit`(関数): 比べる側が作業木の src なら、その HEAD の commit(src と、エンジンが読む追跡ファイル=``TRACKED_READS`` と
- import している内部モジュール: `shibuya`・`shibuya.cli`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`tools/bytecheck/configs.py`・`tools/bytecheck/fields.py`・`tools/bytecheck/tree.py`
- 呼び手: `tools/bytecheck/cli.py`
- 読む試験: `tests/tools/test_bytecheck.py`
- 環境変数: `SHIBUYA_FLEET_API_KEY`・`os.environ` をまるごと使う
- 決定の ID: 第 346

## [cli.py](../../../../../../tools/bytecheck/cli.py)

bytecheck.cli — byte-check の入口(``python tools/bytecheck/cli.py {run,side,compare,one} …``・リポの根で)。

- 公開の関数とクラス
  - `build_parser`(関数): 引数の解析器。
  - `main`(関数): 入口。終了コード 0 同じ / 1 動いた / 2 誤り。
- import している内部モジュール: `tools/bytecheck/check.py`・`tools/bytecheck/configs.py`
- 読む試験: `tests/tools/test_bytecheck.py`
- CLI の引数
  - サブコマンド `compare`
  - サブコマンド `one`
  - サブコマンド `run`
  - サブコマンド `side`
  - `--a`
  - `--agents`
  - `--allow-incomplete-tree`
  - `--b`
  - `--base`: 基準の commit(既定 HEAD)
  - `--commit`: side の JSON に書く commit(記録だけ)
  - `--config`
  - `--drop-behavior-item`
  - `--expect-src`
  - `--extra-path`: 写しの一覧に足す追跡ファイル(run の --extra-path と同じ=開いても一覧に無いとは数えない)
  - `--inherit-env`: 呼び手の SHIBUYA_ の変数をそのまま両側に渡す
  - `--jobs`: 同時に回すランの数
  - `--kw`: 構成の引数に足す JSON(旧値の再現の切替口を渡す口・10e と同じ)
  - `--label`
  - `--multiset-items`
  - `--note`
  - `--only`: 構成の名をカンマで(組の並びの代わり)
  - `--out`
  - `--out-dir`: side 2 本と compare を書く置き場
  - `--scratch`
  - `--seed`
  - `--set`: 構成の組(all19=19 構成・parent4=親の 4 構成・arms=腕 on の 2 構成と 7 変数)
  - `--src`: 読む src(既定は道具のリポ=作業木の src)
  - `--strict`: 新しい欄や条件の欄が記録に無いことも誤り(2)にする(run は常に strict)
  - `--tape`
  - `--work`: 作業の置き場(短い道筋・空か無いこと。写しの木とテープが残る)
  - `--world`: 世界資産の置き場(道具のリポの根からの相対)

## [configs.py](../../../../../../tools/bytecheck/configs.py)

bytecheck.configs — byte-check の構成の表・構成の組・比べる 25 欄・記録に残す切替口の環境変数。

- 公開の関数とクラス
  - `configs`(関数): 19 構成(名 → ``shibuya.cli.run`` に渡す引数)。並びは ``wave2_bytecheck.configs()`` と同じ。
  - `hidden_env_names`(関数): ``env`` に置かれた ``SHIBUYA_`` の変数のうち、値を記録しないもの(:data:`SWITCH_ENV` の外)の名。
  - `set_configs`(関数): 構成の組の構成の並び(無い組の名は ``KeyError``)。
  - `set_env`(関数): 構成の組が両側に置く環境変数(写し)。
  - `switch_env`(関数): ``env`` のうち :data:`SWITCH_ENV` の値(置かれていたものだけ・一覧の並び)。
- 呼び手: `tools/bytecheck/check.py`・`tools/bytecheck/cli.py`
- 読む試験: `tests/tools/test_bytecheck.py`
- 環境変数: `SHIBUYA_ABSENT_PROCESSES`・`SHIBUYA_BATCH_WIDTH_S`・`SHIBUYA_BODY_BOUNDARY_GAUGE`・`SHIBUYA_BODY_SCHEDULE`・`SHIBUYA_BUDGET_MD`・`SHIBUYA_CALENDAR`・`SHIBUYA_CALENDAR_2`・`SHIBUYA_CALENDAR_3`・`SHIBUYA_CALENDAR_3_TRIAL`・`SHIBUYA_CALENDAR_SHADOW`・`SHIBUYA_CALENDAR_W20`・`SHIBUYA_CLOCK`・`SHIBUYA_CONTACT`・`SHIBUYA_CONTACT_HABIT`・`SHIBUYA_CONTACT_SEND`・`SHIBUYA_CONTACT_UNNOTICED`・`SHIBUYA_DECISION_PORT`・`SHIBUYA_DEFECT_FIXES_1103`・`SHIBUYA_DUTIES`・`SHIBUYA_ECONOMY_STAGE2`・`SHIBUYA_ECONOMY_STAGE2_PARTS`・`SHIBUYA_EVENTS`・`SHIBUYA_FLEET_API_KEY`・`SHIBUYA_MEAL_DEFAULT`・`SHIBUYA_MEMORY_CUE`・`SHIBUYA_MEMORY_EMBED_MODEL`・`SHIBUYA_MEMORY_GRAIN`・`SHIBUYA_MEMORY_MODEL`・`SHIBUYA_MEMORY_PEOPLE`・`SHIBUYA_MEMORY_STORE`・`SHIBUYA_NAV1_DENSITY`・`SHIBUYA_PATTERN_LEDGER_MD`・`SHIBUYA_PERCEPTION_MD`・`SHIBUYA_PROXIMITY`・`SHIBUYA_PROXIMITY_D`・`SHIBUYA_RATE_RULES`・`SHIBUYA_RULES_42`・`SHIBUYA_RULES_42B`・`SHIBUYA_SEAT_RELEASE`・`SHIBUYA_SLOPE`・`SHIBUYA_SPACE`・`SHIBUYA_SPEECH_PORT`・`SHIBUYA_STEP_SCOPE`・`SHIBUYA_SYSTEMS_CHECK`・`SHIBUYA_TALK_CLOCK`・`SHIBUYA_TOOL_EVENTS`・`SHIBUYA_TURN_WEIGHT`・`SHIBUYA_WAGE`・`SHIBUYA_WARD_AREA_M2`・`SHIBUYA_WRITE_GUARD`
- 決定の ID: 第 346

## [fields.py](../../../../../../tools/bytecheck/fields.py)

bytecheck.fields — 25 欄の外に足した比べるもの・比べない欄の名前つきの一覧・正準の JSON のハッシュ・差の書き方。

- 公開の関数とクラス
  - `arrow_schema`(関数): Arrow のスキーマ(列の名・型・null の可否・列の metadata・スキーマの metadata。``ARROW:schema`` の塊は除く)。
  - `canon`(関数): 正準の JSON(鍵を並べる・区切りの空白なし・UTF-8)。
  - `checkpoint_rows`(関数): 全 checkpoint の値(dataclass なら全欄・それ以外は属性)。
  - `diff`(関数): 動いた欄の差(辞書は違う鍵だけ・list は違う位置だけ・それ以外は前後の値)。
  - `field_digest`(関数): manifest・run_meta の比べる形: 全体の sha256・一番上の欄ごとのハッシュ・短い値・除いた欄。
  - `file_sha256`(関数): ファイルのバイトの sha256(全桁)。
  - `named_moves`(関数): ``<prefix>_fields_sha`` の動いた欄の名と前後の値(短い値ならその値・長ければハッシュ)。
  - `same_value`(関数): 2 つの値が同じか(正準の JSON が同じ=辞書の並びは見ない・型の違いは違い・NaN は同じ)。
  - `sha16`(関数): 正準の JSON の sha256 の頭 16 桁。
  - `strip_skipped`(関数): ``doc`` から比べない欄を除いた写しと、除いた欄の道筋(``a.b``・list の中は ``a[0].b``)。
  - `tape_files`(関数): テープの置き場の全ファイル(置き場からの posix の道筋・並べる)。
  - `tape_sha256`(関数): テープの置き場の全ファイルの sha256(``fieldwise`` の名のファイルは欄ごとに比べるので除く)。
- 呼び手: `tools/bytecheck/check.py`
- 読む試験: `tests/tools/test_bytecheck.py`
- 決定の ID: 第 346

## [tree.py](../../../../../../tools/bytecheck/tree.py)

bytecheck.tree — 基準の commit の写しの木を作る(git archive)・data へのつなぎを置いて外す・写すファイルの一覧と src の走査。

- 公開の関数とクラス
  - `NotALinkError`(クラス): 外そうとした道筋がつなぎでない(何もしていない)。
  - `PathRef`(クラス): src に現れた、リポの根からの道筋の文字列 1 つ。
  - `archive_paths`(関数): 写しの木へ git archive で写す道筋(``src``+:data:`TRACKED_READS`+``extra``・重なりを除く)。
  - `chain_path`(関数): ``/`` の鎖の部品から道筋を作る(最初の ``docs``・``data``・``tools``・``tests`` から。後の未知の部品は ``{}``)。
  - `classify_reads`(関数): ランで開いた ``src`` の外の追跡ファイル(リポの根からの道筋)を仕分ける。
  - `concat_path`(関数): ``+`` でつないだ文字列の部品から道筋を作る(最初に ``docs/`` などで始まる部品から。未知の部品は ``{}``)。
  - `git`(関数): ``git -C repo …``(出力はバイト)。
  - `git_archive`(関数): commit の ``paths`` を ``dest`` へ展開する(``git archive`` の tar を Python の tarfile で読む・data の filter)。
  - `in_git_worktree`(関数): ``path``(無ければ在る一番近い親)が git の作業木の中か(検収 M4: 写しの木が作業木の中にあると、根を上へ辿る読み口が
  - `is_link`(関数): つなぎ(junction)か記号のリンクか。
  - `lead_path`(関数): 文字列の頭の道筋(``docs``・``data``・``tools``・``tests`` で始まるもの)。無ければ None。
  - `norm_text`(関数): 道筋の文字列の書き方をそろえる(``\`` を ``/`` に・頭の ``./`` を外す・書式の差し込みを ``{}`` に)。
  - `paths_in_commit`(関数): ``paths`` のうち commit にあるもの・無いもの(``git ls-tree``)。
  - `place_data_link`(関数): ``tree_root/data`` を ``target`` へのつなぎにする(Windows は junction・それ以外は記号のリンク)。
  - `python_prefixes`(関数): Python の置き場(開いたファイルの記録から外す)。
  - `remove_link`(関数): つなぎ(か記号のリンク)だけを外す。つなぎでなければ :class:`NotALinkError`(何も消さない)。
  - `resolve_commit`(関数): ``rev`` の commit の全桁。無ければ ``ValueError``。
  - `scan_path_refs`(関数): src の全 ``.py`` から、リポの根からの道筋の文字列を集める(AST だけ=import しない)。
  - `scan_root_anchors`(関数): src の中でリポの根を求めるファイル(src からの道筋 → 行)。
  - `src_files_digest`(関数): ``src_dir`` の下のファイル(``src_dir`` からの posix の道筋)のバイトの sha256 の頭 16 桁(無ければ None)。
  - `tracked_refs`(関数): 道筋のうち追跡ファイルの側(``docs``・``tools``・``tests``)のもの。
  - `tree_missing`(関数): 写しの木(``src`` の親)に足りないもの。
  - `tuple_path`(関数): 文字列の定数だけの tuple か list(``("..", "docs", "bench", …)``)を道筋にする(先頭の ``..`` は飛ばす)。
  - `unclassified_refs`(関数): 追跡ファイルの側の道筋のうち、:data:`TRACKED_READS` にも :data:`NOT_COPIED` にも無いもの(道筋 → 現れた所)。
- 呼び手: `tools/bytecheck/check.py`
- 読む試験: `tests/tools/test_bytecheck.py`
