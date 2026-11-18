# src/shibuya/runtime

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [clocks](clocks/README.md)・[inference](inference/README.md)・[state](state/README.md)・[systems](systems/README.md)

## [__init__.py](../../../../../../../src/shibuya/runtime/__init__.py)

(冒頭の説明なし)

## [arbiter.py](../../../../../../../src/shibuya/runtime/arbiter.py)

engine.arbiter — 繰り延べアービタ(知覚契約書 §6 の裁定規則)。

- 公開の関数とクラス
  - `Arbiter`(クラス): 毎tick の裁定+保留の持ち越し+診断計数の積み上げ(1 シミュ日ぶん)。
  - `ArbiterDecision`(クラス): 1 tick 分の裁定結果(純関数 ``arbitrate`` の出力)。
  - `arbitrate`(関数): 繰り延べアービタの**純関数**本体(入力の並び順に依存しない)。
  - `call_budget_per_tick`(関数): 予算行 L4 を tick あたり・当該規模へ按分した呼数。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.foundation.vocab.agent_codes`・`shibuya.mind.system1.wake`
- 呼び手: `shibuya.engine.run`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/bench/test_refr20b_tool.py`・`tests/c6/test_l4_l6_budget.py`・`tests/c8/test_ablations_ab8.py`・`tests/c8/test_ablations_l4_pin.py`・`tests/economy/test_entry_capital.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_arbiter.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_two_layer_activity.py`・`tests/test_cli_l4_scale.py`
- 読む試験(道筋で): `tests/engine/test_add_at_guard.py`・`tests/engine/test_two_phase.py`
- 状態台帳の行
  - 持ち主 `arbiter`(`Arbiter`)
    - `O42` Arbiter _pending・_pool・queue・_last_tick(挙動 behavior・復元 required) 道筋 `arbiter._last_tick`・`arbiter._pending`・`arbiter._pool`・`arbiter.queue` 書ける系: arbiter
    - `O71` Arbiter の計数(挙動 diag・復元 discardable) 道筋 `arbiter._diag_total`・`arbiter._merged_total`・`arbiter._outside_total`・`arbiter._sleep_total`・`arbiter.budget_unused`・`arbiter.n_calls_total` 書ける系: arbiter
- 決定の ID: 09-25・D-56・D-66・D-99・D-110

## [clock.py](../../../../../../../src/shibuya/runtime/clock.py)

engine.clock — シミュレーション時計(壁時計に一切依存しない)。

- 公開の関数とクラス
  - `SimClock`(クラス): 開始時刻と tick 長だけを持つ不変の時計。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.types`
- 読む試験: `tests/engine/test_clock.py`
- 読む試験(道筋で): `tests/engine/test_state_checks_10f.py`・`tests/tools/test_pkgmove.py`

## [switch_defects.py](../../../../../../../src/shibuya/runtime/switch_defects.py)

engine.defect_fixes_1103 — 棚卸し B で見つけた欠陥 4 件の直しの宣言・計器・見出し(指示書 11-03 §3・小さな版上げ 1 回分)。

- 公開の関数とクラス
  - `check_resume`(関数): 再開のときに、保存したランの見出しの ``defect_fixes_1103``(無ければ legacy=版上げの前のラン)が on かを確かめる(違えば止める)。
  - `empty_counts`(関数): 計器の空の形(活動の名ごとの dict 2 本と整数 5 本)。
  - `header_fields`(関数): 状態のファイルの見出しの ``defect_fixes_1103``(ランは常に ``{"mode": "on"}``・on の外の名は None)。
  - `is_legacy`(関数): ``mode``(省略=ランの腕 on)が旧道(版上げの前の挙動=部品の口だけ)か。
  - `is_on`(関数): ``mode``(省略=ランの腕 on)が直した道か。
  - `manifest_fields`(関数): manifest の ``defect_fixes_1103``(設定=形の版・腕・4 件の宣言・直した印/観測=計器)。
  - `resolve`(関数): 引数の腕(``None``=ランの腕 ``on``)を名に直す(名の誤りは止める)。
- import している内部モジュール: `shibuya.foundation.arms.removed`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/engine/test_defect_fixes_1103.py`
- 環境変数: `SHIBUYA_DEFECT_FIXES_1103`
- 決定の ID: 10-13b/§0-6・11-02r/§2-2・11-03・11-03/§3・第 346
