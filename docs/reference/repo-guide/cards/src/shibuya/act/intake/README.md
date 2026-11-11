# src/shibuya/act/intake

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/act/intake/__init__.py)

(冒頭の説明なし)

## [parser.py](../../../../../../../../src/shibuya/act/intake/parser.py)

llm.parser — 2行形の**ラベル基準・寛容行指向**パーサ(知覚契約書 §2.5 の正典実装)。

- 公開の関数とクラス
  - `ParseResult`(クラス): 1応答の解釈結果。
  - `find_action_word`(関数): テキスト中で**最初に現れる**語彙語(同位置なら最長)を返す。
  - `parse_two_line`(関数): 2行形(および4行形)を寛容に読む。**例外を投げない**。
- import している内部モジュール: `shibuya.foundation.vocab.actions`・`shibuya.llm.undefined`
- 呼び手: `shibuya.engine.commit`・`shibuya.engine.llm_bridge`・`shibuya.llm.fleet`・`tools/c6/c6lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/instruments/dm_eval/situations.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_parser_contract.py`・`tests/llm/test_mock_v3.py`・`tests/llm/test_parser.py`・`tests/llm/test_vocab_v2.py`・`tests/perception/test_b6_invite.py`
- 決定の ID: D-71・D-113・D-116・第 266・第 274・第 275
