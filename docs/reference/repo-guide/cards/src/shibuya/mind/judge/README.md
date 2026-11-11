# src/shibuya/mind/judge

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [decision](decision/README.md)

## [__init__.py](../../../../../../../../src/shibuya/mind/judge/__init__.py)

(冒頭の説明なし)

## [classical.py](../../../../../../../../src/shibuya/mind/judge/classical.py)

engine.classical — System 1.5 の古典的選択モデル=方策 ``classical``(5 段目 5b・D-119 L1〜L8・第292)。

- 公開の関数とクラス
  - `ActivityPrior`(クラス): 錨 → 配列 ``rates[性 2, 就業 2, 年齢 16(0=総数), 活動 19, 時刻 96]``(行動者率 %)。
  - `ClassicalPolicy`(クラス): 方策 ``classical``(LLM 0 呼)。``bind`` のあとで ``complete`` が使える。
  - `check_activity_region`(関数)
  - `check_classical_social`(関数)
  - `check_meal_gate`(関数)
  - `check_policy`(関数)
  - `day_kind_of`(関数): ``day_index``(0=月曜)→ 錨の曜日の鍵(平日/土曜/日曜)。
  - `ipf_constants`(関数): 1 次元 IPF(L7 (a)): 乗数を掛けたあとの**集団の周辺**を事前分布の周辺に戻す定数 c(活動ごと)。
  - `load_activity_prior`(関数): 事前分布の錨(追跡ファイル)を読む → ``(辞書, md5)``。
  - `meal_gate_interval_p`(関数): 1 時間あたりの確率 ``p_hour`` → 経過 ``dt_minutes`` 分の間に 1 回以上通る確率 ``1 − (1 − p)^(Δt/60)``。
  - `ok_self`(関数): 体 ``aid`` 自身が食事中か(同じセルの食事中の人数から自分を引くため)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar`・`shibuya.engine.chooser`・`shibuya.foundation.paths`・`shibuya.foundation.rng`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.mock`
- 呼び手: `shibuya.cli`・`shibuya.engine.experiment.branch`・`shibuya.engine.experiment.switch`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`tools/instruments/dm_eval/judge.py`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_calendar.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_state_checks_10f.py`
- 状態台帳の行
  - 持ち主 `classical`(`ClassicalPolicy`)
    - `O20` ClassicalPolicy _prev(挙動 behavior・復元 required) 道筋 `classical._prev` 書ける系: decide
    - `O21` ClassicalPolicy _gate_hazard(EnergyLayer meal_reset と同じ配列)(挙動 behavior・復元 required) 道筋 `classical._gate_hazard` 書ける系: body・decide・home_meal・phase_c
    - `O22` ClassicalPolicy _condition・_tick・_eating_tick・_eating_cells(挙動 no・復元 discardable) 道筋 `classical._condition`・`classical._eating_cells`・`classical._eating_tick`・`classical._tick` 書ける系: decide
    - `O23` ClassicalPolicy _b_tick・_b_off・counts・by_hour(挙動 no・復元 derivable) 道筋 `classical._b_off`・`classical._b_tick`・`classical.by_hour`・`classical.counts` 書ける系: decide
    - `O24` ClassicalPolicy home_cell・acq_fn(挙動 no・復元 derivable) 道筋 `classical.acq_fn`・`classical.home_cell` 書ける系: decide
    - `O69` ClassicalPolicy n_calls(挙動 diag・復元 discardable) 道筋 `classical.n_calls` 書ける系: decide
    - `O90` ClassicalPolicy _ipf_cache(15 分帯ごとの c_t の覚え書き)(挙動 behavior・復元 required) 道筋 `classical._ipf_cache` 書ける系: decide
- 決定の ID: D-31・D-119・第 292

## [store_choice.py](../../../../../../../../src/shibuya/mind/judge/store_choice.py)

engine.store_choice — **想起優先の候補合成**と**決め手の記録**(D-120 7c・N6 (a)・N7 (a)・N8 (a)・第298)。

- 公開の関数とクラス
  - `StoreChoice`(クラス): 想起優先の候補合成と決め手の記録(1 ランに 1 つ・``TargetResolver`` が持つ)。
  - `walk_m_per_tick`(関数): 体ごとの歩速[m/tick]\(エンジンの移動の物差し)。node=W1 の辺長の平均・edge と nav1=希望速度 × tick 秒。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.chooser`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.store_memory`
- 呼び手: `shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/test_sim_time_T.py`・`tests/engine/test_store_choice.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`
- 状態台帳の行
  - 持ち主 `poi_resolver.store_choice`(`StoreChoice`)
    - `O13` StoreChoice choice_poi・choice_reason・stats・by_hour(挙動 diag・復元 discardable) 道筋 `poi_resolver.store_choice.by_hour`・`poi_resolver.store_choice.choice_poi`・`poi_resolver.store_choice.choice_reason`・`poi_resolver.store_choice.stats` 書ける系: apply_responses・memory
    - `O14` StoreChoice _b_tick・_b_off(挙動 no・復元 derivable) 道筋 `poi_resolver.store_choice._b_off`・`poi_resolver.store_choice._b_tick` 書ける系: memory
    - `O68` StoreChoice first_by_reason・visits_by_reason(挙動 diag・復元 discardable) 道筋 `poi_resolver.store_choice.first_by_reason`・`poi_resolver.store_choice.visits_by_reason` 書ける系: apply_responses・memory
- 決定の ID: D-120・D-121・第 296・第 298
