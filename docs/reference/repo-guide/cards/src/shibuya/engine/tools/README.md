# src/shibuya/engine/tools

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/tools/__init__.py)

(冒頭の説明なし)

## [record.py](../../../../../../../../src/shibuya/engine/tools/record.py)

engine.tools.record — 道具の記録の欄(CT9)と、ランの道具の一式・manifest の ``tools``(第 1 期 1-7 C0)。

- 公開の関数とクラス
  - `SignboardReadLink`(クラス): 看板を読んだ出来事を書く口(判断の系が刻みの終わりに知覚の事実を渡す)。
  - `ToolsFixture`(クラス): ランの道具の一式(組み立てで作り、ランの間は読むだけ)。
  - `arm_from_env`(関数): 環境変数の値 → 腕を入れるか(``on``・``1``・``true``・``yes`` だけ真=既定 off)。
  - `build_fixture`(関数): 組み立て: 台帳(最初の中身)・グループの一覧(W16 の母集団から)・店の番号の表(空)・看板の口(腕のときだけ)。
  - `enabled`(関数): 看板を読んだ出来事を書くか(切替口 ``SHIBUYA_TOOL_EVENTS``・``set_enabled``。既定 off)。
  - `manifest_fields`(関数): manifest の ``tools``(計器): 道具の数と名・登録だけの道具・グループの数・連絡先の印の数・店の番号の表・看板の印。
  - `set_enabled`(関数): 腕を入れる/外す(組み立ての時に読む=ランの途中で変えても、そのランは変わらない)。
- import している内部モジュール: `shibuya.engine.tools.registry`・`shibuya.foundation.journal.log`・`shibuya.foundation.vocab.events`・`shibuya.society.tools.groups`・`shibuya.society.tools.places`
- 呼び手: `shibuya.engine.events.body`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar3/_ca3.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 環境変数: `SHIBUYA_TOOL_EVENTS`
- 決定の ID: 10-12/§4-4・R-113

## [registry.py](../../../../../../../../src/shibuya/engine/tools/registry.py)

engine.tools.registry — 道具の台帳(第 1 期 1-7 C0・CT0)。

- 公開の関数とクラス
  - `KnownBy`(クラス): 道具を知っている体の集合の表し方(凍結)。``kind``=``all``(全員)・``none``(誰も)・``set``(``members`` の体だけ)。
  - `Tool`(クラス): 道具の台帳の 1 行(凍結)。欄の名と順は口の約束 1-7 の 6 欄+将来の欄・出どころ・段・つなぎの行。
  - `ToolRegistry`(クラス): 道具の台帳。**書く口は ``register`` の 1 つ**(足すだけ)。
  - `affordance_words`(関数): 体 ``agent`` が使える道具を、``TOOL_ACTION_WORDS`` で判断の語彙の語に写した語(台帳の並び・重ねない)。
  - `default_registry`(関数): 最初の中身の台帳(呼ぶたびに新しい物=ランごとに 1 つ)。
- import している内部モジュール: `shibuya.foundation.decl.bridging`
- 呼び手: `shibuya.engine.calendar_self`・`shibuya.engine.contact.tools`・`shibuya.engine.tools.record`・`shibuya.mind.judge.decision.layer`・`shibuya.society.tools.places`
- 読む試験: `tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/engine/tools/test_c0_init_recall.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/engine/tools/test_c0_tool_registry.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-12/§1-13・10-12/§4-4・10-13b/§1・R-85・R-113
