# src/shibuya/mind

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [judge](judge/README.md)・[memory](memory/README.md)・[percept](percept/README.md)・[plan](plan/README.md)・[relations](relations/README.md)・[system1](system1/README.md)

## [__init__.py](../../../../../../../src/shibuya/mind/__init__.py)

(冒頭の説明なし)

## [ops.py](../../../../../../../src/shibuya/mind/ops.py)

mind.ops — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `clear_refractory`(関数): 呼んだ個体×条件の不応期タイマーを**戻す**(艦隊の繰り延べ=「呼が成立しなかった」)。
  - `normalized_refractory_scale`(関数): ``refractory_scale`` を manifest 欄用に正規化する(``{条件名: 倍率}``・名前昇順)。
  - `refractory_ticks`(関数): **ランの実効不応期表**[tick]\(知覚契約書 §6 の 11 行)。
  - `set_refractory`(関数): 呼んだ個体×条件の不応期タイマーを張る(知覚契約書 §6 運用規定②)。
  - `wake_condition_index`(関数): ``refractory_scale`` の鍵 → ``WakeCondition`` の列番号。
  - `write_familiarity`(関数): **親しみの表の行を書く**(4 段目・値と行の選び方は ``engine.familiarity`` が決める)。
  - `write_intero_stages`(関数): ``change_detect`` が返した内受容段を書き込む(心の欄 ``fatigue_stage``・``hunger_stage``・``thermal_stage``)。
  - `write_memory`(関数): **記憶の表の行を書く**(6 段目 6a・値と行の選び方は ``engine.memory`` が決める)。
  - `write_relations`(関数): **関係辺を書く**(C10 8a・値と辺の選び方は ``engine.relations`` が決める)。
  - `write_store_memory`(関数): **店の評価の記憶の行を書く**(D-120 7a・値と行の選び方は ``engine.memory`` が決める)。
- import している内部モジュール: `shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.write_guard`・`shibuya.mind.system1.change_detect`・`shibuya.world.model.agent_table`
- 呼び手: `shibuya.interfaces.cli.main`・`shibuya.mind.memory.familiarity`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.store_memory`・`shibuya.mind.relations.layer`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.decide`・`shibuya.runtime.systems.judge`・`shibuya.runtime.systems.perceive`
- 読む試験: `tests/bench/test_refr20b_tool.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/systems/test_systems_table.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_add_at_guard.py`・`tests/engine/test_detection_writes_split.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_two_layer_activity.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 書きの許可
  - `clear_refractory`: 直接の書き `agents.refractory_until` 口として持つ系: wake_filter
  - `set_refractory`: 直接の書き `agents.refractory_until` 口として持つ系: decide
  - `write_familiarity`: 直接の書き `agents.fam_exposures`・`agents.fam_first`・`agents.fam_last`・`agents.fam_thing`・`agents.fam_visits` 口として持つ系: familiarity
  - `write_intero_stages`: 直接の書き `agents.fatigue_stage`・`agents.hunger_stage`・`agents.thermal_stage` 口として持つ系: detect
  - `write_memory`: 直接の書き `agents.mem_cell`・`agents.mem_importance`・`agents.mem_kind`・`agents.mem_last`・`agents.mem_n`・`agents.mem_object`・`agents.mem_partner`・`agents.mem_result`・`agents.mem_tick` 口として持つ系: decide・llm_receive・memory
  - `write_relations`: 直接の書き `agents.rel_first`・`agents.rel_kind`・`agents.rel_last`・`agents.rel_n`・`agents.rel_partner`・`agents.rel_sign` 口として持つ系: build・memory・relations_wake
  - `write_store_memory`: 直接の書き `agents.sm_first`・`agents.sm_last`・`agents.sm_n`・`agents.sm_poi`・`agents.sm_precision`・`agents.sm_source`・`agents.sm_valence` 口として持つ系: decide・llm_receive・memory
- 決定の ID: D-120
