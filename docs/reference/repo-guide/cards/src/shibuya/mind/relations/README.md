# src/shibuya/mind/relations

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/mind/relations/__init__.py)

(冒頭の説明なし)

## [people.py](../../../../../../../../src/shibuya/mind/relations/people.py)

engine.relations_people — 人も記憶の一つ(第 6 期 6-5・腕 ``--memory-people memory``)の関係の読み口。

- 公開の関数とクラス
  - `PeopleRelationLayer`(クラス): 人も記憶の一つの腕の関係の読み口(器の人の行・関係の表を読まない)。``store`` は ``MemoryStore``(上限なし・M1)。
- import している内部モジュール: `shibuya.engine.relations`・`shibuya.foundation.vocab.contact_flags`・`shibuya.mind.memory.memory_m1`
- 呼び手: `shibuya.engine.contact.book`・`shibuya.mind.memory.memory`
- 読む試験: `tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`
- 状態台帳の行
  - 持ち主 `rel_layer` の別のクラス `PeopleRelationLayer`(行は `shibuya.engine.relations` のカードを見る)
- 決定の ID: 10-12/§4-6
