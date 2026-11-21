# tools/night5070

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 2 本(このディレクトリの直下)

その他のファイル: `README.md`・`experiments.json`

## [night_run.py](../../../../../../tools/night5070/night_run.py)

5070 の夜の実験を 1 コマンドで回す(回答 10-25 §6-0 の 1)。

- 公開の関数とクラス
  - `NightFailure`(クラス): 段の失敗(要約に書いて止める)。
  - `Step`(クラス)
  - `StepTimer`(クラス)
  - `all_holes`(関数): 設定全体の穴(名ごとに使われる所)と、見積りが空欄の実験。
  - `build_metrics`(関数): 計測の分離の一覧(回答 10-25 §6-7)。ランの出力から取れる欄だけ埋め、取れない欄は「未計測」。
  - `check_health`(関数): 各口で ``/v1/models`` が返るまで待ち(上限 ``wait_s``)、completion を 1 本投げて 1 行返るかを見る。
  - `error_head`(関数): エラーの先頭 n 行(Traceback があれば最初の Traceback から・無ければ標準エラーの頭から)。
  - `expand_argv`(関数): コマンドの並びを埋める。要素がちょうど ``{{名}}`` で値が並びなら、その並びを差し込む。
  - `expand_str`(関数): 文字列の中の ``{{名}}`` を埋める(埋まらない名はそのまま残す)。値の中の ``{{名}}`` も埋める。
  - `experiment_parts`(関数): 実験 1 本で使う設定の部分(艦隊の節は艦隊を使う実験だけ)。
  - `find_holes`(関数): ``obj`` の文字列の中の ``{{名}}`` のうち、``vars_`` で埋まらない名(値が null か名が無い)。
  - `flag_abbreviations`(関数): ``flags`` のどれかの真の接頭辞になっている旗の語(``--hos`` など)。
  - `flag_uses`(関数): 語の並びの中の ``flag`` の値(``--flag 値``・``--flag=値``)。値の無い末尾は None。
  - `get_flag`(関数): 引数(文字列か並び)の ``--flag 値``・``--flag=値`` の値(最後のもの・無ければ None)。
  - `holes_for`(関数): 実験 1 本を回すのに埋まっていない穴の一覧(重複は 1 つに)。
  - `http_json`(関数): HTTP で JSON を送って JSON を受ける(標準ライブラリだけ)。``api_key`` は ``Authorization: Bearer`` で付ける。
  - `icacls_argv`(関数): 鍵のファイルを本人だけに絞る ``icacls`` の引数(継承を外し、本人に全部の権限を与え直す)。
  - `keep_awake`(関数): ラン中のスリープを止める(on)/戻す(off)。Windows 以外では何もしない。戻り値=呼べたか。
  - `load_config`(関数): 設定の JSON を読む。
  - `main`(関数)
  - `make_run_dir`(関数): 小さな記録の置き場(作る)と大きな出力の置き場(dry-run では作らない)。どちらにも無い名を選ぶ。
  - `mask_paths`(関数): 要約と計測の一覧に絶対パスと鍵を残さない(リポの根・python・ホーム・ランごとの API key)。
  - `mask_secrets`(関数): 登録した鍵の値を ``<API_KEY>`` に置き換える。
  - `metrics_markdown`(関数)
  - `parse_stdout`(関数): ``shibuya.cli`` の標準出力(``RunResult.summary`` と艦隊の行)から取れる数。取れない鍵は入れない。
  - `parse_vram`(関数): ``nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader,nounits`` の 1 行目(MiB)。
  - `plan_vram`(関数): 空き VRAM から ``--gpu-memory-utilization`` と ``--max-num-seqs`` を決める(GB は GiB=1,024 MiB)。
  - `query_vram`(関数): 起動の前の VRAM(読み取りだけ)。``nvidia-smi`` が無い・読めないなら None(=未計測)。GPU が複数なら 1 枚目。
  - `read_tape`(関数): テープの ``calls.parquet`` の集計(pyarrow が無い・ファイルが無いなら None)。
  - `read_wslconfig`(関数): ホームの ``.wslconfig`` の中身(無ければ None・読み取りだけ)。
  - `register_secret`(関数): 記録とログから消す値を登録する(空は無視)。
  - `rel_or_abs`(関数): リポの中ならリポの根からの相対(posix)・外なら posix の絶対。
  - `restrict_key_acl`(関数): Windows で鍵のファイルの ACL を本人だけに絞る(失敗しても続ける)。戻り値=要約に書く注(名は書かない)。
  - `run_logged`(関数): コマンドを回し、標準出力と標準エラーを ``log_dir`` に書く。戻り値=(終了コード, 出力, エラー, 失敗の理由)。
  - `run_night`(関数): 夜の 1 本。戻り値=0(成功・dry-run)/ 1(失敗)/ 2(実験の名が無い・smoke の定義が無い)/ 3(設定の穴)/
  - `safety_checks`(関数): 安全の規則 1・2・4 の機械の検査(艦隊を立てる前)。どれかが ``ok=False`` なら艦隊を立てない(終了コード 5)。
  - `scrub_logs`(関数): ``log_dir`` の下のログから鍵の値を消す(背後で起動した艦隊のログなど、最後の掃除)。戻り値=直したファイルの名。
  - `secret_like_names`(関数): 鍵らしい名(``*_KEY``・``*_TOKEN``・``*_SECRET``・``PASSWORD``・``PASSWD``・``APIKEY``・``CREDENTIAL(S)``)。
  - `set_flag`(関数): 引数の ``--flag`` の値を置き換える(無ければ末尾に足す)。並びは並びのまま返す。
  - `split_command`(関数): 起動のコマンドを語に切る。空白を含む要素(``bash -lc`` の文字列など)は ``shlex`` でさらに切る(最大 depth 段)。
  - `wait_vram_settle`(関数): ``poll_s`` ごとに VRAM を読み、使用量が連続 2 回同じになるか ``limit_s`` 秒で打ち切る。
  - `write_api_key`(関数): 鍵をファイルに書く(新しく作る・本人だけが読める権限に絞る)。戻り値=権限の注。
  - `write_summary`(関数): 朝に読む 1 枚(成功/失敗・時刻・壁時計・呼数・エラーの先頭・結果のパス・見積り)。
  - `wslenv_names`(関数): ``WSLENV`` に並ぶ名(``名/旗`` の旗は外す)。値は読まない(``WSLENV`` は名の並びだけを持つ)。
- CLI の引数
  - `--config`: 設定の JSON(既定 tools/night5070/experiments.json)
  - `--data-out`: 大きな出力とログの根(既定 data/night5070=gitignore の中・相対はリポの根から)
  - `--deadline-hours`: 全体の締め切り[時間]\(既定=設定の deadline_hours=9.5。タスクからは上限 − 0.5 が渡る)
  - `--dry-run`: 艦隊を立てずコマンドも回さず、何をするかを並べて要約を書く
  - `--experiment`: 実験の名(設定の experiments の鍵・例 E1)
  - `--keep-fleet`: 終わっても艦隊を落とさない(朝に手で落とす)
  - `--out`: 小さな記録の根(既定 docs/bench/night5070・相対はリポの根から)
  - `--smoke`: 試走: 実験の定義の smoke.vars(E1 は 500 体 × 120 刻み)を vars に重ねる。--dry-run と併せられる
  - `--start-at`: 予定の開始の時刻 HH:MM(要約の終わりの時刻の表に使う)
- 環境変数: `SHIBUYA_FLEET_API_KEY`・`USERNAME`・`os.environ` をまるごと使う
- 決定の ID: 10-25/§6-0・10-25/§6-7

## [register_task.py](../../../../../../tools/night5070/register_task.py)

夜の実験をタスクスケジューラに登録する(回答 10-25 §6-0 の 2)。

- 公開の関数とクラス
  - `build_xml`(関数): タスクの XML(文字列)。書き出すときは UTF-16。締め切りが上限以上・主体がユーザー権限でないなら ValueError。
  - `check_principal_xml`(関数): 安全の規則 5: XML の主体がユーザー権限か(``<UserId>``・``<LogonType>``・``<RunLevel>``・``<GroupId>`` が無い)。
  - `check_user_id`(関数): 安全の規則 5: ユーザー権限の主体か(SYSTEM などでない・機械のアカウントでない)。違えば ValueError。
  - `create_command`(関数)
  - `current_user_id`(関数): 登録する本人(``USERDOMAIN\USERNAME``。分からなければ空)。
  - `delete_command`(関数)
  - `main`(関数)
  - `mask_home`(関数): 表示用にホームの道筋を ``<HOME>`` に置き換える(XML の中では ``&lt;HOME&gt;``=読むと ``<HOME>``)。
  - `mask_user`(関数): 表示用に ``<UserId>`` の中身を ``<USER>`` に置き換える。
  - `next_start`(関数): ``HH:MM`` → 次にその時刻になる日時(今より後)。
  - `night_args`(関数): night_run.py に渡す引数(リポの根からの相対の道筋だけ)。
  - `ps_arguments`(関数): powershell.exe の Arguments(ODPT のタスクと同じ形・ログは log_root/_scheduler.log に足す)。
  - `worktree_reason`(関数): ``root`` が作業木なら理由(道筋の部分が ``wt_`` で始まる・``.git`` がファイル=git worktree)。本体なら空。
- CLI の引数
  - `--at`: 始める時刻 HH:MM(既定の案 01:00=ユーザーが決める)
  - `--config`: night_run に渡す --config(リポの根からの相対)
  - `--daily`: 毎日回す(既定は次の 1 回だけ)
  - `--deadline-hours`: night_run の締め切り[時間]\(既定=上限 − 0.5。上限以上なら登録しない)
  - `--delete`: タスクを消す
  - `--experiment`: 実験の名(例 E1)
  - `--max-hours`: 実行時間の上限[時間]\(既定 10)
  - `--name`: (help を読めない)
  - `--out`: night_run に渡す --out(リポの根からの相対)
  - `--print-only`: XML とコマンドを出すだけで登録しない
  - `--wake`: スリープから起こして始める(WakeToRun=true)
- 環境変数: `USERDOMAIN`・`USERNAME`
- 決定の ID: 10-25/§6-0
