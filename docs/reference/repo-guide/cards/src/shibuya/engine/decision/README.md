# src/shibuya/engine/decision

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/decision/__init__.py)

engine.decision — 候補の口 J0(第 1 期 1-8・DM-0・DM4・DM5・DM13・C-2)。

## [layer.py](../../../../../../../../src/shibuya/engine/decision/layer.py)

engine.decision.layer — 候補の口 J0 の腕と層(1 呼の判断を口に通す・候補の源の計器・判断の出来事)(第 1 期 1-8)。

- 公開の関数とクラス
  - `DecisionLayer`(クラス): 候補の口の層(腕 ``port`` のランだけ組み立てが作る=``Layers.decision``)。
  - `arm`(関数): いまの腕(``legacy``=既定・``port``=候補の口)。組み立てのときに読む。
  - `manifest_fields`(関数): manifest の ``decision_port``(腕が legacy のランは層が無い=観測の子は null)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--decision-port``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.engine.commit`・`shibuya.engine.decision.port`・`shibuya.engine.decision.sources`・`shibuya.engine.economy_stage2`・`shibuya.engine.events.log`・`shibuya.engine.events.vocab`・`shibuya.engine.tools.registry`
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

## [port.py](../../../../../../../../src/shibuya/engine/decision/port.py)

engine.decision.port — 候補の口 J0 の型と、提示(順のシャッフルと番号)の仕組み(第 1 期 1-8・DM-0・DM4・DM5・DM13・C-2)。

- 公開の関数とクラス
  - `Candidate`(クラス): 候補 1 つ(``number`` は提示のときに振る=作る側は ``None``)。
  - `Choice`(クラス): 口の答え(``choose`` が返す)。驚き・迷い・連続値・ひと言は空(None)で始める(〔決定〕と 1-8b)。
  - `DecisionContext`(クラス): 判断の入力(``perception.facts.PerceptCarrier`` の形)。口は値を解釈しない。
  - `DecisionPort`(クラス): 候補の口(判断モデルと LLM で 1 つ)。実装は ``_answer`` だけを書く。
  - `Hesitation`(クラス): 迷い(DM5): 1 位と 2 位の確率の差(``margin``)と分布のエントロピー(``entropy``・自然対数)。
  - `compose`(関数): 判断の入力の文(DM4: 短い版と長い版を 1 つの仕組みで・共通部分を前に)。J0 では使わない(プロンプトは今のまま)。
  - `options_text`(関数): 提示の文(候補は「頭に浮かんだこと」として・番号つき・最後に「その他」)。C-2 の 3・4。
  - `present`(関数): 候補を並べ替え、提示の番号(1〜n)を**最後に**振った写しを返す(C-2 の 1・Concordia の形)。
  - `present_rng`(関数): 並べ替えの乱数(10c の counter の鍵=``core.rng.k19_counters``(刻みの鍵・体・候補の数))。
- import している内部モジュール: `shibuya.core.rng`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.calendar2.port`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar3.port`・`shibuya.engine.calendar_self`・`shibuya.engine.contact.layer`・`shibuya.engine.contact.port`・`shibuya.engine.decision.layer`・`shibuya.engine.decision.ports`・`shibuya.engine.decision.sources`・`shibuya.engine.duties.layer`・`shibuya.engine.duties.port`・`tools/instruments/dm_eval/backends/base.py`・`tools/instruments/dm_eval/bias.py`・`tools/instruments/dm_eval/cli.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`
- 読む試験: `tests/build_pop/test_w21_stage8_9.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_other_ratio_field.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/duties/test_du_units.py`・`tests/engine/test_pop_w21_world.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/tools/test_dm_eval.py`
- 読む試験(道筋で): `tests/engine/time/test_t0_rng_key.py`
- 決定の ID: 10-12/§4-7・10-13b/§4-2・R-108・R-113

## [ports.py](../../../../../../../../src/shibuya/engine/decision/ports.py)

engine.decision.ports — 候補の口の 3 つの実装(同じ入口 ``DecisionPort.choose``)(第 1 期 1-8 J0)。

- 公開の関数とクラス
  - `ClassicalPort`(クラス): 古典の方策 G の答えの行動の語を候補に写す実装。
  - `LlmPort`(クラス): 口の後ろに今の LLM の道(``bridge``=``engine.llm_bridge.LLMBridge``)を置く実装。
  - `MockPort`(クラス): 今の mock(``llm.mock.MockLLM``)と同じ鍵から同じ番号を選ぶ実装(判断モデルの代役)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.decision.port`・`shibuya.llm.contract`
- 呼び手: `shibuya.engine.systems.build`
- 読む試験: `tests/economy/stage2/test_stage2_calls.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_other_ratio_field.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/speech/test_speech_choice_utterance.py`
- 決定の ID: R-113

## [sources.py](../../../../../../../../src/shibuya/engine/decision/sources.py)

engine.decision.sources — 候補を 5 つの源から作る(第 1 期 1-8 J0・DM-0)。

- 公開の関数とクラス
  - `build_candidates`(関数): 5 つの源と語彙の残りから候補の列を作る(作る側は番号を振らない=``present`` が振る)。読むだけ。
  - `memory_kind_words`(関数): 記憶の種類 → 行為の語(``engine.memory.ACTION_KIND``=行動コード → 種類 の逆)。
- import している内部モジュール: `shibuya.engine.decision.port`・`shibuya.engine.memory`
- 呼び手: `shibuya.engine.calendar_self`・`shibuya.engine.decision.layer`・`tools/instruments/dm_eval/situations.py`
- 読む試験: `tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`
- 決定の ID: 10-12/§4-7
