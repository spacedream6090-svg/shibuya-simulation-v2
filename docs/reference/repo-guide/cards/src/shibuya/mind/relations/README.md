# src/shibuya/mind/relations

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/mind/relations/__init__.py)

(冒頭の説明なし)

## [layer.py](../../../../../../../../src/shibuya/mind/relations/layer.py)

engine.relations — **関係辺の表と導出**(C10 8a・第299)+**会話の起点と相手選択**(C10 8b)。

- 公開の関数とクラス
  - `RelationLayer`(クラス): 関係辺の書き手と読み口(``MemoryLayer`` が持つ・``--relations on`` のランだけ)。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.vocab.contact_flags`・`shibuya.foundation.vocab.relations`・`shibuya.mind.ops`・`shibuya.world.model.proximity`
- 呼び手: `shibuya.mind.memory.memory`・`shibuya.mind.relations.people`
- 読む試験: `tests/engine/memory/test_m4_m5_people.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`
- 読む試験(道筋で): `tests/engine/tools/contacts_writers.py`
- 状態台帳の行
  - 持ち主 `rel_layer`(`RelationLayer`)
    - `CT5` RelationLayer contact_flags(個人の連絡先の手段ごとの印・第 1 期 1-7)(挙動 diag・復元 derivable) 道筋 `rel_layer._contact_flags` 書ける系: memory
    - `O16` RelationLayer _prev_cell(挙動 behavior・復元 required) 道筋 `rel_layer._prev_cell` 書ける系: memory・relations_wake
    - `O17` RelationLayer _acq_until(挙動 behavior・復元 required) 道筋 `rel_layer._acq_until` 書ける系: decide・memory・relations_wake
    - `O18` RelationLayer _co_since・_co_day・_co_active(挙動 behavior・復元 required) 道筋 `rel_layer._co_active`・`rel_layer._co_day`・`rel_layer._co_since` 書ける系: memory・relations_wake
    - `O19` RelationLayer _invite_salt・chosen_count・origin_of・stats ほか(挙動 diag・復元 discardable) 道筋 `rel_layer._invite_salt`・`rel_layer.chosen_count`・`rel_layer.init_audit`・`rel_layer.origin_of`・`rel_layer.stats`・`rel_layer.wall` 書ける系: apply_responses・conversation・decide・memory・relations_wake
- 決定の ID: 10-12/§4-4・R-36・R-62・D-31・D-93・第 299・第 300

## [people.py](../../../../../../../../src/shibuya/mind/relations/people.py)

engine.relations_people — 人も記憶の一つ(第 6 期 6-5・腕 ``--memory-people memory``)の関係の読み口。

- 公開の関数とクラス
  - `PeopleRelationLayer`(クラス): 人も記憶の一つの腕の関係の読み口(器の人の行・関係の表を読まない)。``store`` は ``MemoryStore``(上限なし・M1)。
- import している内部モジュール: `shibuya.foundation.vocab.contact_flags`・`shibuya.foundation.vocab.relations`・`shibuya.mind.memory.memory_m1`・`shibuya.mind.relations.layer`
- 呼び手: `shibuya.interim_bundles.contact.book`・`shibuya.mind.memory.memory`
- 読む試験: `tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`
- 状態台帳の行
  - 持ち主 `rel_layer` の別のクラス `PeopleRelationLayer`(行は `shibuya.mind.relations.layer` のカードを見る)
- 決定の ID: 10-12/§4-6
