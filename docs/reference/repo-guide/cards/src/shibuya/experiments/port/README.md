# src/shibuya/experiments/port

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/experiments/port/__init__.py)

(冒頭の説明なし)

## [apply.py](../../../../../../../../src/shibuya/experiments/port/apply.py)

engine.experiment.apply — 申込書の改変を世界に入れる口 ``apply``(第 3 期 3-3・決定 10-12 §1-1 CP6・§4-5 CP5・CP12)。

- 公開の関数とクラス
  - `ApplyRecord`(クラス): 申込書の改変の控え(持ち主 ``experiment`` の ``handle.rec``・状態台帳の行 ``X``=軸 1 diag・軸 2 discardable)。
  - `WorldHandle`(クラス): 口 ``apply`` が触る世界の物(組み立てが 1 回だけ作る・物はそのまま指す)。
  - `apply`(関数): 申込書 ``form`` の改変を時刻 ``t``(ナノ秒・刻みの頭)の世界に入れる(**唯一の口**)。表を変えた回数を返す。
  - `cond_id_of`(関数): 実験の条件の名(``<申込書の指紋の先頭 16 字>:<決定の番号か notice>``)。
  - `hours_mask`(関数): 営業時間の区間の列 → 1 日の分の真偽の列(閉じる分が 1 日を超える区間は同じ日の頭へ回す=W7 の畳み方と同じ)。
  - `targets_of`(関数): 対象の店の番号(昇順・空もある)。読むだけ(分岐の報告の実行の内訳が使う)。
- import している内部モジュール: `shibuya.experiments.port.form`・`shibuya.foundation.ports.experiment_gate`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.experiments.port.layer`
- 読む試験: `tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/experiment/test_x33_form.py`
- 決定の ID: 10-12/§1-1

## [checks.py](../../../../../../../../src/shibuya/experiments/port/checks.py)

engine.experiment.checks — 申込書の点検(第 3 期 3-3b・CP5-1 の「始まり 0 の予期しない改変」・CP5-3 の名指しと混入の疑い)。

- 公開の関数とクラス
  - `ExperimentWarning`(クラス): 申込書の点検の警告(拒まない=仮-24)。
  - `contamination`(関数): CP5-3: 混入の疑い(申込書の ``known_to_model``=LLM が実在の出来事として知っている改変の語の自己申告)。
  - `naming_hits`(関数): 文 ``text`` に含まれる名(部分一致・昇順)。名の一覧は呼び手が渡す(コードに地名や業種名を書かない)。
  - `persona_naming`(関数): CP5-3: ペルソナの文(id → 文)が改変した物の名(``names``)を名指ししていないか。見つけた文と名の行を返す。
  - `start0_check`(関数): CP5-1: 始まり 0 の予期しない改変の点検(manifest の ``experiment.start0``)。旗 ``warning`` は真偽・理由は文。
  - `warn_start0`(関数): ``start0_check`` の旗が立っていれば ``ExperimentWarning`` を出す(拒まない)。記録を返す。
- import している内部モジュール: `shibuya.experiments.port.form`
- 呼び手: `shibuya.build.pop.w21_persona`・`shibuya.experiments.port.layer`
- 読む試験: `tests/engine/experiment/test_cf33b_form_checks.py`
- 決定の ID: 10-12/§4-5・R-117

## [ensemble.py](../../../../../../../../src/shibuya/experiments/port/ensemble.py)

engine.experiment.ensemble — 探索と確認・アンサンブルの封印・事前登録(CP14)・対の差の形・技量スコアの器(第 3 期 3-3)。

- 公開の関数とクラス
  - `Member`(クラス): アンサンブルの 1 本(初期状態の番号・モデルの札・偶然の番号と、それぞれの seed)。
  - `Seal`(クラス): 封印(回す前に作る・**単位=初期状態**=母集団と環境の seed の組)。公開するのは指紋と数だけ。
  - `entrance`(関数): ランの入口の封印の検査(組み立てが呼ぶ): このランの seed の 3 つとモデルの札がアンサンブルのどのメンバーで、どちらの
  - `evidence_container`(関数): 〔3-3b・仮-24〕CP14 の封印の証拠の欄(手元の git の commit と公開リポへの push の記録・第三者の時刻印は無し)。値は空=
  - `floor_summary`(関数): 床の分布の要約(指標ごと: 対の数・平均・標準偏差(n − 1)・最小・最大・絶対値の最大・差 0 の割合・差の列)。
  - `floor_values`(関数): A/A の枝 2 本の組 (a, b) の列(各メンバーの T 以後の 2 本の checkpoints の JSON)→ 指標ごとの値と差 b − a。
  - `get_path`(関数): ``a.b.c`` の道筋で入れ子の辞書を引く(無ければ ``KeyError``)。
  - `members`(関数): 申込書が回してよいメンバー(**自分の半分だけ**=探索は封印していない半分・確認は封印した半分)。
  - `metrics_spec`(関数): ``salt_compare.py --metrics`` の形(主=1 つ・副=Holm。向きの事前登録の印は確認の申込書だけ)。
  - `paired_values`(関数): (基準の枝, 改変の枝) の checkpoints の JSON の組の列(salt の順)→ ``salt_compare.py --values`` の形。
  - `pairs_status`(関数): 対の数が R-71 の最低に届くか(両側 6 対・向きを事前登録した片側 5 対)。
  - `preregister`(関数): 確認のランの事前登録: 下書き(申込書の辞書・事前登録の欄なし)→(公開の記録の JSON, 確認の申込書)。
  - `seal`(関数): アンサンブルの半分を封印する(単位=初期状態・決定的=同じアンサンブルなら探索と確認の申込書で同じ封印)。
  - `seal_record`(関数): 封印の記録(封印の中身は書かない=指紋と数と、探索の申込書なら封印していない半分)。
  - `skill_container`(関数): 技量スコアの器(指標ごとに単純な基準 3 つの誤差と値の欄・**値は空**=答え合わせの段で埋める)。
  - `skill_score`(関数): CP14 の技量スコア=1 − 誤差/基準の誤差(気象と同じ。基準の誤差 0 は ``ValueError``)。
- import している内部モジュール: `shibuya.experiments.port.form`・`shibuya.experiments.port.warmup`
- 呼び手: `shibuya.experiments.drive.branch`・`shibuya.experiments.port.layer`・`tools/instruments/skill_gauge.py`
- 読む試験: `tests/engine/experiment/test_cf33b_manifest.py`・`tests/engine/experiment/test_x33_ensemble.py`・`tests/engine/experiment/test_x33_form.py`・`tests/engine/experiment/test_x33_run.py`・`tests/tools/test_skill_gauge.py`
- 決定の ID: 10-12/§4-5・R-71・R-117

## [form.py](../../../../../../../../src/shibuya/experiments/port/form.py)

engine.experiment.form — 反実仮想の申込書 ``ExperimentForm``(第 3 期 3-3・決定 10-12 §4-5 CP5-4・探索と確認・CP14)。

- 公開の関数とクラス
  - `DecisionSpec`(クラス): 決定の種類 1 つ(水準・欄の名と型の検査・実装したか)。``params`` は欄の名 → (検査の名, 必須か, 既定)。
  - `ExperimentForm`(クラス): 反実仮想の申込書(凍結・入れ子も読み取り専用)。作るのは ``from_dict``・``from_json``・``load``。
  - `canonical_json`(関数): 決定的な JSON(鍵の昇順・区切りの空白なし・ASCII の外もそのまま)。
  - `sha256_hex`(関数): ``canonical_json`` の UTF-8 の sha256(16 進 64 字)。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`
- 呼び手: `shibuya.cli`・`shibuya.experiments.drive.branch`・`shibuya.experiments.port.apply`・`shibuya.experiments.port.checks`・`shibuya.experiments.port.ensemble`・`shibuya.experiments.port.layer`・`shibuya.experiments.port.warmup`
- 読む試験: `tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_cf33b_form_checks.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/experiment/test_x33_ensemble.py`・`tests/engine/experiment/test_x33_form.py`
- 決定の ID: 10-12/§4-5

## [layer.py](../../../../../../../../src/shibuya/experiments/port/layer.py)

engine.experiment.layer — 申込書をランに置く口(組み立て)・系 ``experiment``・manifest の節(第 3 期 3-3)。

- 公開の関数とクラス
  - `ExperimentLayer`(クラス): 申込書の持ち主(箱 ``Layers.experiment``・``hash_owners`` の鍵 ``experiment``・状態台帳の行 ``X``)。
  - `Staged`(クラス): ``cli.run`` が組み立てに渡す物(申込書・分岐なら T0 までのテープの切り替えの指定・申込書のモデルの札)。
  - `check_resume`(関数): 再開のランの申込書を親の状態のファイルの見出しと突き合わせる。親から引き継ぐなら ``True``。
  - `current`(関数): 組み立てが読む(申込書を渡さないランは ``None``)。
  - `entrance`(関数): 〔親の判断 M1〕ランの入口の封印の検査(組み立てが世界を触る前に呼ぶ)。申込書の無いランは ``None``。メンバーと半分の組を返す。
  - `make_layer`(関数): 組み立ての口: 申込書が無ければ ``None``(今の道)。分岐なら LLM の口を T0 で切り替える口に包む(``bridge.client``)。
  - `manifest_fields`(関数): manifest の ``experiment``(申込書を渡さないランは ``None``)。中身は持ち主のメソッド ``manifest``。
  - `staged`(関数): この中で呼んだ ``run_day`` の組み立てが申込書を受け取る(出るときに外す)。``model`` は申込書のアンサンブルのモデルの札
  - `state_header`(関数): 状態のファイルの見出しに書く欄(申込書の無いランは ``None``=見出しは今のまま)。
  - `sys_experiment`(関数): 系 ``experiment``(刻みの中の最初の系): 申込書の改変を効かせる口 ``apply`` を 1 回呼ぶ。
- import している内部モジュール: `shibuya.experiments.port.apply`・`shibuya.experiments.port.checks`・`shibuya.experiments.port.ensemble`・`shibuya.experiments.port.form`・`shibuya.experiments.port.warmup`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.state_io`・`shibuya.runtime.systems.table`
- 読む試験: `tests/engine/experiment/test_cf33b_manifest.py`・`tests/engine/experiment/test_x33_form.py`・`tests/engine/experiment/test_x33_run.py`
- 状態台帳の行
  - 持ち主 `experiment`(`ExperimentLayer`)
    - `X` ExperimentLayer(申込書の改変の控え・4 つの確認の結果・第 3 期 3-3)(挙動 diag・復元 discardable) 道筋 `experiment.handle`・`experiment.xchecks` 書ける系: experiment
- 書きの許可
  - 系 `experiment`(群 実験・時 `tick`・立つ条件 `experiment`・関数 `sys_experiment`)
    - 書いてよい外の道筋: `E:events.*`・`O56:runner.environment.*`・`X:experiment.*`

## [run_kind.py](../../../../../../../../src/shibuya/experiments/port/run_kind.py)

engine.run_kind — ランの種類(第 1 期 1-4・決定 10-12 §4-5 CP5-5「ランの種類を manifest に記録」)。

- 公開の関数とクラス
  - `check`(関数): 種類の名の検査(4 つの外は ``ValueError``)。
  - `decide`(関数): ``cli.run`` の規則: 試験 > 反実仮想(〔3-3〕申込書を渡した)> 腕 > 再現 の順。``testing`` を省くと ``in_test()``。
  - `in_test`(関数): pytest の試験の中か(``PYTEST_CURRENT_TEST`` が立っているか)。
  - `resolve`(関数): manifest に書く種類(``None``=決めていない=null のまま)。
- 呼び手: `shibuya.cli`・`shibuya.engine.run`
- 読む試験: `tests/engine/batching/test_conductor_windows.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/speech/test_speech_cli.py`
- 環境変数: `PYTEST_CURRENT_TEST`
- 決定の ID: 10-12/§4-5

## [warmup.py](../../../../../../../../src/shibuya/experiments/port/warmup.py)

engine.experiment.warmup — 慣らし(CP5-6)の自動判定の規則と parameter の事前登録(第 3 期 3-3b・仮-24・答申 R-117 §4-6)。

- 公開の関数とクラス
  - `rule_items`(関数): ``RULE`` の葉の項の名(入れ子の ``q1``・``q2`` は ``q1.…`` の形=``MARKS`` の鍵と同じ形)。
  - `rule_record`(関数): manifest の ``experiment.warmup``・事前登録の記録の ``warmup``(規則・印・指紋・判定の道具の名)。
  - `rule_sha256`(関数): 規則と印の正準の JSON の sha256(事前登録の指紋)。
- import している内部モジュール: `shibuya.experiments.port.form`
- 呼び手: `shibuya.experiments.port.ensemble`・`shibuya.experiments.port.layer`・`tools/instruments/warmup_gauge.py`
- 読む試験: `tests/engine/experiment/test_cf33b_manifest.py`・`tests/tools/test_warmup_gauge.py`
- 決定の ID: 10-12・10-12/§4-5・R-71・R-117
