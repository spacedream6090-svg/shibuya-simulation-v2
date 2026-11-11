# src/shibuya/society/tools

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/society/tools/__init__.py)

(冒頭の説明なし)

## [groups.py](../../../../../../../../src/shibuya/society/tools/groups.py)

engine.tools.groups — グループの一覧(第 1 期 1-7 C0・CT10・CT5 の「グループの一覧を持つ」)。

- 公開の関数とクラス
  - `GroupList`(クラス): グループの一覧(家族と職場)。書く口は無い(``from_population`` で作る)。
- 呼び手: `shibuya.engine.contact.book`・`shibuya.engine.contact.layer`・`shibuya.engine.tools.record`
- 読む試験: `tests/engine/calendar2/_ca2.py`・`tests/engine/calendar3/_ca3.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/tools/test_c0_groups_from_w16.py`・`tests/engine/tools/test_c0_init_recall.py`
- 決定の ID: 10-12/§4-4

## [places.py](../../../../../../../../src/shibuya/society/tools/places.py)

engine.tools.places — 店の番号の場所の表(第 1 期 1-7 C0・CT5 の「店や組織の番号は場所の表の側」)。

- 公開の関数とクラス
  - `PhoneTable`(クラス): 店の番号の場所の表(POI の番号 → 電話番号)。C0 は空。作った後は書けない。
  - `osm_phone_of`(関数): OSM の要素のタグ → 電話番号の文字列(``phone`` を先に・無ければ ``contact:phone``・空は ``None``)。
- import している内部モジュール: `shibuya.engine.tools.registry`
- 呼び手: `shibuya.engine.tools.record`
- 読む試験: `tests/engine/contact/test_c2_exchange.py`・`tests/engine/tools/test_c0_init_recall.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`
- 決定の ID: 10-13b/§3
