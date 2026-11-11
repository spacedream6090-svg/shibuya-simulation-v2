# src/shibuya/engine/events

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/events/__init__.py)

(冒頭の説明なし)

## [body.py](../../../../../../../../src/shibuya/engine/events/body.py)

engine.events.body — 体の出来事を出来事の記録(1-3)に書く口(第 2 期 2-3・腕 ``--memory-store events`` のランだけ)。

- 公開の関数とクラス
  - `BodyEventLink`(クラス): 体の出来事の口(記憶の器が持つ=``MemoryStore.body_events``・組み立てが腕のランだけ作る)。
  - `kind_of_what`(関数): 出来事の語のコード → 記憶の種類(記憶の器の中身の写像の検査=``MemoryStore.remember``)。表の外は ``0``。
- import している内部モジュール: `shibuya.engine.tools.record`・`shibuya.foundation.journal.log`・`shibuya.foundation.vocab.events`
- 呼び手: `shibuya.mind.memory.memory_store`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/multiday/test_md23_body_events.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
