# 第 3 期 3-3 反実仮想の器の検収の記録

- 検収役 Opus 5.5(実装は見ていない)。作業木の枝 `3-3/experiment-form`(土台 `740508c`・未 commit)を読み、本体 HEAD `fea27d2`(1-8b・2-2・2-1 を含む)は読むだけ。
- 正: 発注文(3-3)・決定 10-12 §4-5(CP5-1〜CP5-6・CP12・CP14・探索と確認・複数ランの作り方)・§1-1(実験が入れるのは「決定」だけ)・答申 R-71 §1-6(4 つの確認)・§2(対の並べ替え検定・最低 6 対)・1-3 の CP12。
- 数は実測。生の出力は作業木の `_bc_review/`(git の外・検収の後に消した)。封印した層は読んでいない。`tests/c7` は回していない。

## 判定

**条件つき受入**(高 0・中 4・低 10)。

使わないときの不変(19/19 と自分の 4 構成)・申込書・効かせる口・分岐と R-71 の 4 つの確認(自分の申込書で独立に再現・負の対照 3 本)・試験(894 passed)は通った。中の 4 件のうち 2 件(M1 封印をランの口で効かせる・M4 持ち主の守り)は取り込みの前に直す。残りの 2 件(M2 封印の単位・M3 つなぎが実行した改変の扱い)は親が判断する。

## 1〜9 の確かめ

### 1. 使わないとき不変 ✓

- 実装役の `byte_check_cf33.json`: 19 構成 × 25 欄が全部同じ(moved 0・`calls_delta` 0)。作業木の側の side(`_bc/cf33g.json`)の `src_is_worktree` は 19 本とも真。
- **自分の 4 構成**(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`・5,000 体・seed 1・1 日・テープつき・`10e/byte_check_10e.py`)。head は本体 HEAD `fea27d2` の src の写しで、`git archive` で作り、錨はエンジンが開く 3 本だけを写した。wt は作業木の src で、子プロセスの `PYTHONPATH` に渡した。`compare` の結果は **4/4 構成で 25 欄とも同じ**。`src_is_worktree` は head が 4 本とも偽、wt が 4 本とも真。final は `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498` で、`w6_v3_default` は実装役の記録と同じ値。2-1・2-2 の入った本体 HEAD と比べても、既定のランは変わらない。
- 申込書なしのランでは、組み立てで `layer.current()` が None になり、`make_layer` も None を返し、`Layers.experiment` は None のまま残る。系 `experiment` は `conductor.WHEN` の条件で立たない。`hash_owners` の `experiment` は None で、行 X は軸 1 diag・軸 2 discardable なので、どちらのハッシュにも状態のファイルにも入らない。`save_state` の見出しには、`state_header(None)` が None なので何も足さない。
- 300 体・1 日の既定のランで、manifest の全部の葉を `740508c` の写しと作業木で比べた。増えたのは、一番上の鍵の末尾の `experiment: null` と、`manifest_sections.paths` の `experiment.*` の 22 行だけ。final は同じ(`f4466eb1…`)。`bridges_count`・`rules_version` も違ったが、これは写しの側に `docs/design` の台帳を写さなかったための欠けで、比べの外とした。

### 2. 申込書(CP5-4) ✓(低 2)

- 欄は `schema`・`kind`(探索/確認)・`subject`(`level` L0〜L4・`ids`・`category`)・`content`(決定の列)・`start`・`end`・`notice`(`to`・`at`・`via`)・`question`・`metrics`(`primary` 1 つ・`secondary`)・`ensemble`・`preregistration`。
- 自分で確かめたこと。知らない欄は、一番上・`subject`・決定の欄・`metrics.primary` のどこに置いても `ValueError` になる。`primary` を列にしても、`primary` が無くても `ValueError`(主は 1 つ)。`start=1.5` も `ValueError`。`from_json(to_json())` は同じ申込書と同じ sha256 を返し、鍵の順を逆にしても sha256 は変わらない。`ids` は昇順で、重なりは消える。欄の付け替えは `FrozenInstanceError`、入れ子は mappingproxy。
- 地名と業種名: `engine/experiment/*.py` を、地名・施設名・駅と路線・業種名の約 60 語で grep した。当たったのは package 名 `shibuya` と「メンバー」の「バー」だけ。試験の側の一覧と AST の検査も通る。対象は番号か種別名(`category` を W7 の `poi_cat_names` と照合)で受ける形になっている。
- 低 L3・L4 は欠陥の一覧へ。

### 3. 効かせる口(CP12・§1-1) ✓(中 1・低 2)

- 口は `apply` の 1 つ。呼び手は `layer` だけで、系 `experiment` の `step` と組み立ての `prime` から呼ぶ。`gate.admit` と表の書き口 3 つ(`set_plan_rows`・`restore_plan_rows`・`set_replay_date`)を呼ぶのも `apply.py` だけ(AST の試験・負の対照つき)。実行時は、`Experiment` の原因を gate の外で作れない。この 1-3 の試験(`test_e_cause_three_kinds`・`test_the_cause_still_cannot_be_made_outside_the_gate`)は残っていて、通った。
- 入れる物: 営業時間の表 `open_matrix` の行(制度の決定)・天気の再生日(L0 の自然)・暦の祝日の表(L0 の社会の決まり)・出来事ログの行だけ。体の状態(心)・物理の法則・空間は書かない(コードを読んで確かめた)。
- L0 と L1 が効くことの確かめ。合成の世界の試験(`test_x33_apply` 21 本)に加えて、**世界資産 300 体・1 日のランで、休業(7 つおきの 571 店)と天気の差し替え(W13 の 365 日の中ほど)を刻み 600 で当て、段 B(系の前後の変化 ⊆ 宣言)を刻み 599〜601 で回した**。宣言の外の書きは 0 件で、どちらも `applied` 1・出来事 1 行。段 B の試験は `event` だけで回すので、表を書く決定の段 B はこれで補った。
- 分岐(§4)では、営業時間の変更が `実験:改変`(原因 `Experiment`・`cond_id`=申込書の指紋の先頭 16 字 + `:0`)で、告知が宛先ごとの `実験:届いた情報`(`via` SNS)で書かれた。
- 効かせていない改変は、理由の鍵 11 種の行を残して続く(試験 8 形)。L2〜L4 は `DECISIONS` で `implemented=False` とし、行 `not_implemented` を残して続く(宣言して未実装)。
- 中 M3・低 L5・L6 は欠陥の一覧へ。

### 4. 分岐(CP5-2・R-71 §1-6) ✓

自分で回した(作業木の src・mock・世界資産 1,000 体・seed 1・2 日・語彙 v3・checkpoint 60 刻み・試験の外=ランの種類が出る)。基準のランは 18.8 秒で、状態 `state-T00001440`・`state-T00002880` を書いた。T0 は 2 日目の正午(刻み 2,160)。**申込書は実装役のものと変えた**: 正午に W7 で開いている 2,059 店から 5 つおきに選んだ 412 店の営業時間を 9:00〜11:00 にする(L1 `opening_hours`)。告知は体 10・20 へ SNS で送る。分岐の 3 本は 48.0 秒。

| 確認 | `branch_report.json` | 自分の目で |
|---|---|---|
| (a) 入力の一致 | ok/ok。設定の差は `experiment.*` 14 個・`run_kind`(reproduction → counterfactual)・`group_norms.cost.ticks`(2,880 → 1,440) | 基準と枝の manifest を平らにして設定の節の差を自分で数えた。同じ 16 個。seed の 3 つは同じ |
| (b) T0 より前 | ok。再開は `state-T00001440`。T0 より前の checkpoint 12 本(1,499〜2,159)が同じ。テープから 5,260 呼・テープ外 0 | 12 本の behavior-hash は基準と同じ。full-hash は違う。申込書なしの素の再開(同じ状態から)でも 24 本全部で full-hash だけ違い、final は同じだった(10d の discardable)。だから (b) を behavior-hash で比べるのは正しい |
| (c) 最初の食い違い | 世界の最初の食い違い=刻み 2,160・系 `world`・欄 `pois.open_now`・`O73:runner.opening.n_events`・`n_fallback`。全部の最初=刻み 2,160・系 `experiment`(`E:events.*`)。粗い比べ=2,219 で 5 つのハッシュ | A/A と改変の枝の checkpoint を自分で比べた。最初の食い違いは 2,219 で、5 つとも違う |
| (d) A/A | ok。A/A の 2 本の final `fc2fde3a…` が基準の final と同じ | A/A の 2 本は全 checkpoint の 5 ハッシュと final が同じ。A/A の final は基準と同じ。改変の枝の final は `6c40e7d6…`(基準と違う) |

負の対照:
- **改変を空にした枝**(`content` 空・告知なし)を改変の枝として回した。final は基準と同じ `fc2fde3a…`、summary は ok、`c_step` は null。
- **T0 より前を変えた写し**: 分岐の口が T0 より前に返す答えのうち、刻み 1,500 以後の 40 個を空にした。最初の 1 本(A/A の a)にだけ当たった。(b) の aa は fail(最初の食い違い 1,559・テープ外 4,124=T0 より前の動きがずれ、テープの鍵が外れた)・(d) は fail・summary の ok は False。手を入れなかった改変の枝の (b) は ok だった。
- 基準の checkpoints の、T0 より前の 1 本の behavior-hash を書き換えた写しでは `pre_t0_match` の ok が False になる。状態のファイル(npz)そのものを書き換えた写しは、読み口(写しの sha256・戻した後の full-hash の検算=`resume.read_state`・`build` の再開)が止めるので、(b) までは届かない(コードを読んで確かめた)。
- 計器: `experiment.replay` は `replayed_before_t0` 5,260・`live_from_t0` 8,500・`tape_miss_before_t0` 0。出来事は `実験:改変` 1 行・`実験:届いた情報` 2 行(体 10・20)。営業時間の過程は events 4,299・役割行動 0・つなぎ 4,299・担当のいる店 0(実装役の記録と同じ傾向=M3)。
- 低 L1・L2 は欠陥の一覧へ。

### 5. 探索と確認・封印(CP14) △(中 2)

- 封印の指紋は決定的だった。同じ申込書でも、JSON を往復した後でも、`sealed_sha256` と開いた半分が同じ。12 本(initial 3 × model 2 × chance 2)を、封印 6 本・開 6 本に分ける。
- 探索の申込書で `members_for(half="sealed")` を呼ぶと `PermissionError`。確認の申込書で開いた半分を求めても `PermissionError`。事前登録の封印の指紋が違っても `PermissionError`。
- 事前登録の記録は鍵 11 個(`schema`・`registration_sha256`・`registration_blake3`・`seal_sha256`・`ensemble_sha256`・`question`・`metrics`・`form_sha256`・`registered_at`・`skill`・`record_sha256`)。JSON の往復で同じ形に戻る。`registered_at` を変えても `record_sha256` は同じ。確認の申込書の問いを書き換えると `ValueError` になる。
- `paired_values` と `metrics_spec` を `tools/c7/salt_compare.py` の `analyze` に渡した(読み込んだのは道具だけで、試験 `tests/c7` は回していない)。6 対で overall「検定」、3 対で「記述のみ(本数不足)」。`pairs_status(6)` の `p_floor` は 0.03125。
- 技量スコアは器だけ(値は全部 null・式は `1 - error / baseline_error`)。
- 中 M1・M2 は欠陥の一覧へ。

### 6. ランの種類と manifest ✓

- 申込書を渡した `cli.run` は `counterfactual`。試験の外で回した自分の分岐で、枝が `counterfactual`、基準が `reproduction` になった。決め方の順は、試験 > 反実仮想 > 腕 > 再現。申込書は設定の指紋(`build` の `_fp`)に入れない。基準の状態から分岐を再開できた(指紋の差で止まらない)ことで確かめた。
- manifest の `experiment` は一番上の鍵の末尾(118 個目)。既存の 117 個は順も同じ(自分の比べ)。凍結の表の増えた分は末尾の 1 行。
- `run_day` の引数は変わらない(`run.py` の差は import と manifest の 1 欄だけ)。CLI の既存の引数の名も変わらない(足したのは `--experiment`・`--experiment-branch`・`--experiment-aa`)。`main` は `run(...)` を `run_kwargs` に組んでから呼ぶ形にしたが、渡す引数は同じ。

### 7. 守りと宣言 △(中 1・低 2)

- 系の `writes.paths` は `X:experiment.* E:events.* O56:runner.environment.*`。段 B は、試験(`event`)と自分の世界資産のラン(休業・天気)の両方で宣言の外 0 件。
- 状態台帳の行 X(diag・discardable)・`OWNER_CLASSES`・`EXCLUDED` 2 行(定数 5・参照 1)・実行時の網羅の試験がある。
- 凍結の表は増えた分だけ(`writes_soa_frozen` に `experiment: []`、`writes_paths_events` に `experiment`、`manifest_keys_frozen` の末尾)。
- 新しい識別子に tick は無い。出てくるのは既存の名(`request.tick`・checkpoint の `tick`・`Probe` の `ticks`・timing の `"tick"`)だけ。時間の直書きも無く、`core.time_consts` を使う。逐次ループは各ファイルの docstring に宣言がある。
- 申込書は凍結され、`DECISIONS` は `MappingProxyType`。
- 中 M4・低 L6・L7 は欠陥の一覧へ。

### 8. 試験 ✓

- 作業木で `tests/engine/experiment tests/engine/events tests/engine/systems tests/engine/time tests/engine/bridging tests/llm tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py` を回した(`-m "not slow" -n 2 --dist loadfile`)。**894 passed・0 failed(11 分 38 秒)**。data が無くて飛ばした試験は 0 件。
- `tests/engine/experiment` は 82 本を集め、slow は 0 本(記録の数と同じ)。
- `lint-imports`(作業木の src・222 ファイル): 5 契約とも KEPT。

### 9. 記録 △(低 3)

- `README.md`・`branch_example.json`・`byte_check_cf33.json`・`tools/branch_example.py` に絶対パス・ホスト名・個人名は無い(grep)。改行は LF。
- 触った共有ファイルの一覧(§1・§9)は `git diff --stat` の 32 本と合う。§9 の「数を固定した既存の試験」に 1 本の漏れがある(L8)。
- 実装役の申告(§12 の 5): 1 回目の全体の試験(作業用の置き場の記録)は 4,858 passed で、`tests/c7` を含んでいた。`tests/c7` には、封印した層の名を引く試験が 3 本(`test_presence_yardstick`・`test_holdout_compare`・`test_prereg_v13`)あるので、封印した層を読んだ可能性が高い。判断は親に送る(実装役は、中身を記録と報告に使っていないと申告している)。
- 低 L8〜L10 は欠陥の一覧へ。

## 欠陥の一覧(重さ順)

| 番号 | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `engine/experiment/ensemble.py` 96(`Seal.members_for`)・121(`seal`)・`layer.py` 132(`make_layer`) | 封印がランの口で効かない。`cli.run` と組み立ては、探索の申込書が封印した半分の seed で回っても止めない(`seal`・`members_for` を呼ぶ src が無い)。manifest に、どのメンバーか・どちらの半分かの欄が無い。`Seal._sealed` は公開の属性として読め、`members(form)` は全部を返す。holdout の規律が API の約束だけに留まる | 組み立て(か `cli.run`)で `seal(form)` を引き、探索なら開いた半分、確認なら封印した半分の seed の 3 つでなければ止める(か、`unapplied` のように行を残す)。manifest の `experiment` に `member`・`half` を足す。負の対照の試験を足す |
| M2 | 中(親の判断) | `ensemble.py` 121(`seal`) | 封印の単位が 1 本のメンバー(初期状態 × モデル × 偶然)。モデルの札が 2 つ以上あると、同じ(母集団の seed, 動きの seed)が両方の半分に入る(initial 3 × model 2 × chance 2 では 6 組のうち 4 組)。初期状態は、モデルが 1 つでも両方の半分に入る。探索で見た世界と偶然で確認することになる | 封印の単位(初期状態ごと・(初期状態, 偶然) ごと・メンバーごと)を親が決め、つなぎの台帳の行 `DOC-cf33-ensemble-seeds` に単位を書く |
| M3 | 中(親の判断・宣言済み) | `branch.py` 470(`summary`)・`apply.py`(docstring)・台帳 `DOC-cf33-fallback-executes` | 分岐の改変を実行したのは、全部がつなぎ(conf 0.5)。§1-1 は「分岐の実験ではフォールバックを使わない」「実行されなかった改変は再現度の欠陥として数える」と決めている。自分の分岐でも役割行動 0・つなぎ 4,299・担当のいる店 0。なのに `branch_report` の summary は ok=True で、実行の内訳(人か、つなぎか)を書かない。読み手が「人が閉めた」と読み違える | 少なくとも `branch_report` と manifest の `experiment` に「決定の実行の内訳(役割行動/つなぎ)」を足し、つなぎの実行を再現度の欠陥の候補として数える。つなぎを止める腕を 6-6 まで待つなら、宣言はこのままでよい |
| M4 | 中 | `layer.py` 79(`ExperimentLayer`)・`branch.py` 486(`lay_m.xchecks = …`) | 持ち主に `__setattr__` の守りが無い。1-8b の `SpeechPort` などは、組み立てで 1 回だけ置ける形。`form`・`handle`・`branch`・`xchecks` を外から付け替えられ、自分で付け替えて通った。ランの途中で `form` を替えれば、`staged`・`check_resume` を通らずに当てる決定が変わる。`xchecks` は `run_branch` がランの後に外から書くので、状態台帳の行 X の注「書く系は experiment だけ」と合わない。控え `ApplyRecord` の列と集合も外から書ける | `SpeechPort` と同じ `__setattr__`・`__delattr__` の守りを付ける。`xchecks` は持ち主のメソッド(1 回だけ書ける)を書く口にして、台帳の行 X の注に書く。負の対照の試験を足す |
| L1 | 低 | `branch.py` 67(`PROBE_STEPS`)・425 | (c) の窓が T0 から 15 刻みに固定されている。効き目が後で出る決定(翌日の祝日・夕方からの営業時間・後の `at` の告知)は窓の外になり、`c.world=None`・summary の `c_step=None` になる(粗い比べの刻みだけが出る。コードを読んだ・未実測) | 窓を、粗い比べの最初の食い違いの直前の checkpoint から取り直す。または未検出を「窓の外」と書き分ける |
| L2 | 低 | `branch.py` 442(`resume_check`) | (b) の `resume_state.behavior_hash_same` が比べるのは、基準の状態の見出しと基準の manifest の日ごとの記録。基準の自己一致で、枝が戻した状態の検算ではない(枝の側は `build` の full-hash の検算が担う) | 報告の名と注を、基準の自己一致と分かる形に直す |
| L3 | 低 | `form.py` 340 | `ExperimentForm(...)` を直に作ると検査を通らない。`kind="nonsense"`・`start=-5` が作れて、`staged` に渡せる(docstring は「作るのは `from_dict` だけ」) | `__post_init__` で検査するか、`staged` で `from_dict(to_dict())` を通す |
| L4 | 低 | `form.py` 443(`aa`) | 確認の申込書の `.aa()` は、事前登録の指紋が中身と合わなくなる。`to_json`→`from_json` が `ValueError` になり、A/A の枝の manifest で `registration_sha256` と `preregistration_sha256` が食い違う | A/A の枝の扱い(事前登録を外すか、元の登録の指紋を別の欄に残すか)を決めて試験を足す |
| L5 | 低 | `apply.py` 221(`days[d] = …`)・試験の `TABLE_WRITERS` | 表の書き口 3 つは AST の検査だけで、実行時の守りが無い(`getattr` で呼ぶ形は検査に掛からない)。祝日は `calendar.holidays.days` の辞書を直に書くので、書き口の一覧に無く、ほかの場所から暦を書いても検査に掛からない | 暦を書く口を 1 つ作って一覧に足す(親の判断 §12 の 4 と合わせる) |
| L6 | 低 | `apply.py` 60(`REASONS`)・232(`_IMPL`)・`branch.py` 71(`DERIVED_BY_DECISION`)・81(`RESUME_DERIVED`) | モジュールの表が素の dict(`MappingProxyType` でない)。実行時に、決定の中身を差し替えられる | `MappingProxyType` で包む |
| L7 | 低 | `engine/systems/table.py` の `day_close` の `reads` | `state_io.save_state` は見出しのために `layers.experiment` を読むのに、`day_close` の `reads` に宣言が無い(`close_final` には有る)。2-2 は、同じ見出しの書きのために `layers.proximity` を両方に宣言した(2-2 の検収 M1) | `day_close` の `reads` に `layers.experiment` を足す |
| L8 | 低 | `cf33/README.md` §9 | 「数を固定した既存の試験」の一覧に `tests/engine/tools/test_c0_tool_registry.py` が無い(`git diff` には有り、§8 の文には出る) | 一覧に足す |
| L9 | 低 | `cf33/branch_example.json` 6 行 | `world_dir` が `"data\\world\\v2"`(Windows の区切り) | posix の形で書く |
| L10 | 低 | 作業木の `_bc/` | 実装役の作業用の置き場(git の外・gitignore されていない。head の写し・side 3 回分・テープ)が作業木に残っている | 取り込みの前に消す(`git add` しない) |

## rebase の後の並びの案(本体 HEAD `fea27d2` に 2-2・2-1 が先に入っている)

- **語彙**(`engine/events/vocab.py`): 本体では `金:引き出し`=58・`金:カード`=59・版 `events-vocab/2-1`。3-3 の 2 語は、その後ろの `実験:改変`=60・`実験:届いた情報`=61 にし、版は `events-vocab/3-3`。族の並びの末尾に `実験` を足す(2-1 は族を足していない)。直す試験: `test_e_vocab_is_closed`(62 語・末尾 7 語)・`test_x33_apply::test_vocabulary_has_the_two_words`(60/61)・`test_speech_port_schema`・`test_rights_events`・`test_c0_tool_registry`。
- **manifest の一番上の鍵**: 本体は `… speech_port, proximity`(118 個)。`experiment` は `proximity` の後ろの 119 個目にする(`run.py` の並び・`manifest_keys_frozen.json`・`test_t0_tm9_fields`・`test_env_and_sections_10f`・`test_manifest_rules_bridges`・`test_rights_manifest`・`test_c0_phone_table_empty_and_declared`・`test_percept_schema` の末尾の列)。記録の「鍵 118」は 119 に直す。
- **manifest の節の表**(`manifest_sections.py`): `experiment` の混ざった辞書は `proximity` の後ろに置く。`CONFIG_PATHS_SHA256` は本体の `f78dd574…`(2-2 と 2-1 の後)から計算し直す。
- **状態台帳**: 本体は外の行 111・全体 202(PX・PX0・EC・ATM・CR・EM)。行 X を足して、外 112・全体 203。`OWNER_CLASSES` の `experiment` は `proximity` の後ろ。
- **箱**(`boxes.py`): `OWNER_NAMES` は `… "speech", "proximity", "experiment"`。`Layers.experiment` は `proximity` の後ろ、`Fixtures.experiment` は 2-1 の `atms` の後ろ。
- **`state_io`**: `hash_owners` の `experiment` は `proximity` の後ろ。`save_state` の見出しは本体の `proximity`・`economy_stage2` の後ろに `experiment` を置く。
- **系の表**(`table.py`): 刻みの中の系は本体でも 25 なので、`experiment` を足して 26。`close_final` の `reads` は本体の `layers.proximity` の後ろに `layers.experiment`(L7 を直すなら `day_close` も同じ)。
- **`cli.py`**: `cli.run` の `_RK.decide` は、本体の `arms_on=… or _proximity.arm() != MODE_CELL` に `counterfactual=exp_form is not None` を足して合わせる。`main` の `run(...)` を `run_kwargs` に組む形は、本体で増えた `--proximity`・`--proximity-d`・`--economy-stage2`・`--economy-stage2-parts` の扱い(環境変数の口で、`run` の引数ではない)を壊さないことを確かめる。
- **`build.py`**: `make_layer` は 2-2 の近接の層・2-1 の経済の段階 2 の組み立ての後に置き、`Layers(... experiment=)`・`Fixtures(... experiment=)` を足す。
- **つなぎの台帳**: 本体は 328 行。3-3 の 12 行は末尾に足して 340 行(`bridges_count` を確かめる)。
- **凍結の表**: `writes_soa_frozen.json` と `writes_paths_events.json` に `experiment` を足すだけ(本体の 2-1・2-2 は、この 2 つに系を足していない)。
- rebase の後で、byte-check を 4 構成以上(既定は不変のはず)・`tests/engine/experiment` の全部・分岐の試験(世界資産 1,000 体)を回し直す。腕を on にした 2-1・2-2 のランで申込書つきの分岐を回すと、(a) で設定の差が腕の欄に出ないこと(環境変数の腕は 3 本で同じ)も確かめたい。

## 親に確かめてほしいこと

1. M2 封印の単位(メンバーごと・初期状態ごと・(初期状態, 偶然) ごと)。
2. M3 分岐の改変をつなぎが実行すること: §1-1 の「フォールバックを使わない」を 6-6 まで宣言のまま置くか。そのあいだ、報告に実行の内訳を出すか。
3. 実装役の 1 回目の全体の試験が `tests/c7`(封印した層の名を引く試験 3 本)を回したこと(§9)。
4. 実装役の §12 の 2(`group_norms.cost.ticks` が設定の節にあり、再開で必ず動く=(a) は宣言した値でだけ許した)と §12 の 4(祝日の辞書を直に書く形=L5)。
