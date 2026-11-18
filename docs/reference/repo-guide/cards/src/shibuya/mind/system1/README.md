# src/shibuya/mind/system1

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/mind/system1/__init__.py)

(冒頭の説明なし)

## [change_detect.py](../../../../../../../../src/shibuya/mind/system1/change_detect.py)

engine.change_detect — 起床条件 (i)(ii) の検出器(予算行 **P6**)。

- 公開の関数とクラス
  - `B5Crossing`(クラス): 1 変数ぶんの閾値跨ぎ(``resolve`` が段を書き戻すための最小情報)。
  - `ChangeDetector`(クラス): B4 ハッシュと B5 閾値の変化検出器(scratch を持ち回して確保を避ける)。
  - `DetectResult`(クラス): 1 tick 分の検出結果(**世界には書かない**)。
- import している内部モジュール: `shibuya.foundation.vocab.agent_codes`・`shibuya.world.model.agent_table`・`shibuya.world.model.scene_hash`・`shibuya.world.model.state`
- 呼び手: `shibuya.engine.resolve`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`
- 状態台帳の行
  - 持ち主 `detector`(`ChangeDetector`)
    - `O45` ChangeDetector _prev_raw(挙動 behavior・復元 required) 道筋 `detector._prev_raw` 書ける系: detect
- 決定の ID: 10-13b/§4-2

## [wake.py](../../../../../../../../src/shibuya/mind/system1/wake.py)

mind.system1.wake — 割る段で ``engine/arbiter.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `WakeCandidates`(クラス): 1 tick 分の起床候補(全て同じ長さの配列)。
- 呼び手: `shibuya.runtime.arbiter`・`shibuya.runtime.systems.judge`
- 読む試験: `tests/bench/test_refr20b_tool.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/test_arbiter.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_two_layer_activity.py`
- 決定の ID: D-56
