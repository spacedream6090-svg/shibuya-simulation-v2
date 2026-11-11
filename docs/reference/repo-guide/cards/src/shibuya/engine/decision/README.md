# src/shibuya/engine/decision

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/decision/__init__.py)

engine.decision — 候補の口 J0(第 1 期 1-8・DM-0・DM4・DM5・DM13・C-2)。

## [layer.py](../../../../../../../../src/shibuya/engine/decision/layer.py)

engine.decision.layer — 候補の口 J0 の腕と層(1 呼の判断を口に通す・候補の源の計器・判断の出来事)(第 1 期 1-8)。

- 公開の関数とクラス
  - `DecisionLayer`(クラス): 候補の口の層(腕 ``port`` のランだけ組み立てが作る=``Layers.decision``)。
  - `arm`(関数): いまの腕(``legacy``=既定・``port``=候補の口)。組み立てのときに読む。
  - `manifest_fields`(関数): manifest の ``decision_port``(腕が legacy のランは層が無い=観測の子は null)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--decision-port``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
- import している内部モジュール: `shibuya.economy.stage2_bind`・`shibuya.engine.commit`・`shibuya.engine.decision.sources`・`shibuya.engine.tools.registry`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.rng`・`shibuya.foundation.vocab.events`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`
- 読む試験: `tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_other_ratio_field.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`
- 読む試験(道筋で): `tests/engine/speech/test_speech_writers_ast.py`・`tests/engine/time/test_t0_rng_key.py`
- 状態台帳の行
  - 持ち主 `decision`(`DecisionLayer`)
    - `J0` DecisionLayer(候補の口 J0 の計器・刻みごとの営業中の店の控え・第 1 期 1-8)(挙動 diag・復元 discardable) 道筋 `decision._aff_any`・`decision._aff_eatery`・`decision._aff_shop`・`decision._aff_step`・`decision._s2_hints`・`decision.meter` 書ける系: decide
- 環境変数: `SHIBUYA_DECISION_PORT`
- 決定の ID: R-108

## [persona.py](../../../../../../../../src/shibuya/engine/decision/persona.py)

engine.decision.persona — 人物の欄(第 4 期 4-3 段 10・親の判断 仮-33 (6)=判断の入力に短い版・LLM の入力に長い版)。

- 公開の関数とクラス
  - `PersonaError`(クラス): 人物の欄の読み・差し替えの口の誤り(表に無い体・空の出どころ・列の欠け・人の番号の重なり)。
  - `PersonaTable`(クラス): ランの体の並びごとの人物の文(読むだけ)。``texts[版]`` は SoA の行の並びの文(文の無い体は空)。
  - `load_persona`(関数): 段 9 の文の表を読み、ランの体の並び(``person_id``=母集団の ``w21_person_id``・−1=W16 の残す行=文なし)に引き直す。
  - `override`(関数): 差し替えの口(4-1b の腕「LLM が書いた人物像」): 体の行 ``rows`` の ``version`` の文を ``texts`` に替えた新しい表を返す
  - `persona_blocks`(関数): ``compose`` に渡す人物の欄(``{BLOCK_SHORT: 短い版}`` か ``{BLOCK_LONG: 長い版}``・文の無い体と表の無いランは空の辞書)。
- 読む試験: `tests/engine/test_pop_w21_world.py`
- 決定の ID: 10-12/§4-7

## [ports.py](../../../../../../../../src/shibuya/engine/decision/ports.py)

engine.decision.ports — 候補の口の 3 つの実装(同じ入口 ``DecisionPort.choose``)(第 1 期 1-8 J0)。

- 公開の関数とクラス
  - `ClassicalPort`(クラス): 古典の方策 G の答えの行動の語を候補に写す実装。
  - `LlmPort`(クラス): 口の後ろに今の LLM の道(``bridge``=``engine.llm_bridge.LLMBridge``)を置く実装。
  - `MockPort`(クラス): 今の mock(``llm.mock.MockLLM``)と同じ鍵から同じ番号を選ぶ実装(判断モデルの代役)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.ports.decision`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.engine.systems.build`
- 読む試験: `tests/economy/stage2/test_stage2_calls.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_other_ratio_field.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/speech/test_speech_choice_utterance.py`
- 決定の ID: R-113

## [sources.py](../../../../../../../../src/shibuya/engine/decision/sources.py)

engine.decision.sources — 候補を 5 つの源から作る(第 1 期 1-8 J0・DM-0)。

- 公開の関数とクラス
  - `build_candidates`(関数): 5 つの源と語彙の残りから候補の列を作る(作る側は番号を振らない=``present`` が振る)。読むだけ。
  - `memory_kind_words`(関数): 記憶の種類 → 行為の語(``engine.memory.ACTION_KIND``=行動コード → 種類 の逆)。
- import している内部モジュール: `shibuya.engine.memory`・`shibuya.foundation.ports.decision`
- 呼び手: `shibuya.engine.calendar_self`・`shibuya.engine.decision.layer`・`tools/instruments/dm_eval/situations.py`
- 読む試験: `tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`
- 決定の ID: 10-12/§4-7
