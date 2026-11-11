# src/shibuya/experiments/drive

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/experiments/drive/__init__.py)

(冒頭の説明なし)

## [branch.py](../../../../../../../../src/shibuya/experiments/drive/branch.py)

engine.experiment.branch — 「T0 までテープを再生して T0 から今の方策」の分岐と R-71 の 4 つの確認(第 3 期 3-3・CP5-2)。

- 公開の関数とクラス
  - `BranchClient`(クラス): LLM の口(``LLMClient`` 契約=``complete``)を T0 で切り替える。T0 より前はテープ・T0 からは今の方策。
  - `BranchOutcome`(クラス): ``run_branch`` の結果(報告と 4 本のランの結果=A/A の枝 2 本・改変の枝 2 本(指紋の窓の回し直し))。
  - `BranchSpec`(クラス): 分岐の指定(基準のランのテープのディレクトリ・T0 の刻み)。``cli.run`` が組み立てに渡す(``layer.staged``)。
  - `aa_match`(関数): (d) A/A: 全 checkpoint(刻み・behavior・full)と final と系ごとの指紋が厳密に同じか。
  - `choose_state`(関数): T0 より前(next_T < T0)の最後の日の境目の状態(``finished: false``)と見出しの写し。無ければ ``(None, None)``=0 から。
  - `executed_by_agents`(関数): 〔親の判断 M3〕決定 10-12 §1-1「分岐の実験ではエンジンが代わりに実行する仕組みを使わない」の判定(4 つの確認とは別の欄)。
  - `execution_breakdown`(関数): 〔親の判断 M3〕対象の店の T0 以後の開け閉めの実行の内訳(ActualLog の ``store_opening`` の行=担当の従業者の役割行動 /
  - `first_divergence_coarse`(関数): (c) の粗い比べ: 刻み ≥ ``from_step`` の checkpoint で最初に behavior-hash が違う刻みと、違うハッシュの名。
  - `input_match`(関数): (a) 入力の一致(基準と枝の manifest の設定の節の差が腕の欄と導かれる欄だけ・seed と母集団と日課が同じ)。
  - `nonportable_keys`(関数): ランをまたいで比べられない digest の欄の名(報告の限界の表)。
  - `payload_of`(関数): ``RunResult`` → checkpoint の 2 つのハッシュと manifest(``cli.checkpoints_payload`` と同じ鍵の部分)。
  - `pre_t0_match`(関数): (b) T0 より前の checkpoint(刻み < T0)の behavior-hash が全部基準と同じ・テープ外 0・古典の食い違い 0。
  - `probe_first_divergence`(関数): 2 本の系ごとの指紋の行(``(刻み, 系, ((欄, digest), …))``)の最初の食い違い(同じなら ``None``)。
  - `run_branch`(関数): 基準のランの記録 ``base_dir`` から申込書 ``form`` の分岐を回し、4 つの確認をして ``branch_report.json`` を書く。
- import している内部モジュール: `shibuya.experiments.drive.switch`・`shibuya.experiments.port.ensemble`・`shibuya.experiments.port.form`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.time_consts`・`shibuya.llm`・`shibuya.mind.judge.classical`・`shibuya.runtime.inference.tape`・`shibuya.runtime.systems.probe`・`shibuya.world.ledger.records`
- 呼び手: `shibuya.cli`・`shibuya.experiments.drive.switch`
- 読む試験: `tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/experiment/test_x33_form.py`
- 決定の ID: 10-12/§1-1・10-12/§4-5・R-71

## [switch.py](../../../../../../../../src/shibuya/experiments/drive/switch.py)

engine.experiment.switch — T からの切り替えの口(第 3 期 3-3b・CP5-2 の完成)と 4 つの確認の (c)(d) の分け(仮-24)。

- 公開の関数とクラス
  - `ReplaySwitch`(クラス): T からの切り替えの口(T より前=テープの再生(古典の方策は状態を進めて食い違いを数える)・T から=仮のモデル)。
  - `SwitchSpec`(クラス): T からの切り替えの指定(``BranchSpec`` に窓と仮のモデルを足した形)。``cli.run`` の ``experiment_branch`` で渡す。
  - `declared_determinism`(関数): 〔検収 L2〕口が自分で宣言した決定論(属性 ``DETERMINISM_ATTR`` が真偽の値のときだけ・無ければ ``None``=宣言なし)。
  - `determinism`(関数): (d) の 1=決定論の確認。
  - `is_deterministic`(関数): 決定論の確認をかけるか(宣言があれば宣言・無ければ札が ``DETERMINISTIC_MODELS`` にあるか)。
  - `model_label`(関数): 口の札(古典の方策=``classical``・mock=``mock``・ほかは ``source`` の欄か型の名)。
  - `tape_crossing`(関数): テープの行のうち T0 より前に出した艦隊の到着待ちの行(``deferred`` か ``observed_tick`` ≥ 0)の数と、そのうち T0 以後に
  - `vs_aa`(関数): (c) 改変の枝の最初の食い違い(A/A の枝 a との比べ)と A/A の枝 2 本の最初の食い違いの刻みの差(A/A − 改変)。
  - `window_head_step`(関数): T0 が計算のまとめの窓の頭か(窓の頭=ランの始め 0 から ``window_ns`` ずつ)を確かめ、切り替わる刻み(T0 以後の最初の
- import している内部モジュール: `shibuya.experiments.drive.branch`・`shibuya.llm.mock`・`shibuya.mind.judge.classical`
- 呼び手: `shibuya.experiments.drive.branch`
- 読む試験: `tests/engine/experiment/test_cf33b_switch.py`
- 決定の ID: 10-12/§4-5・R-71・R-117
