# src/shibuya/world/facts/rights

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../../src/shibuya/world/facts/rights/__init__.py)

(冒頭の説明なし)

## [initial.py](../../../../../../../../../src/shibuya/world/facts/rights/initial.py)

engine.rights.initial — 権利台帳の最初の中身(第 1 期 1-5・計画 1-5 の 4 つ・決定 10-12 §4-5 CP4)。

- 公開の関数とクラス
  - `InitialRows`(クラス): 〔段 10〕初期の行(体の番号=ランの SoA の行・読むだけ)。``block`` は :data:`RUN_BLOCKS` のどれか。
  - `build_initial`(関数): 最初の中身の権利台帳を作る(行の順: (a) 雇用 → (a′) 担当従業者 → (c) 店の賃借 → (d) 住まい)。
  - `load_run_rows`(関数): 差し替えの世界の初期の行の表を読み、体の番号(母集団の ``agent_id``)をランの SoA の行へ引き直す(表が無ければ ``None``)。
  - `staff_assignment`(関数): 店(POI)→ 担当の体(-1=担当なし)。種別 従業者 の体を決定論で丸振りする(HEAD の ``_assign_staff`` と同じ規則)。
  - `staff_of_poi`(関数): 権利台帳の ``employ`` の行(体 → 店)から、店(POI)→ 担当の体の表を読む(-1=担当なし・複数なら最初の行)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.world.facts.rights.ledger`
- 呼び手: `shibuya.engine.calendar3.roster`・`shibuya.engine.systems.build`・`shibuya.world.laws.opening`・`shibuya.world.laws.runner`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/economy/test_wage_occupation.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/duties/_du.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/rights/test_rules42_rights.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_pop_w21_world.py`
- 決定の ID: 10-12/§4-5・R-76・R-76 #17・R-106

## [ledger.py](../../../../../../../../../src/shibuya/world/facts/rights/ledger.py)

engine.rights.ledger — 権利台帳の器(第 1 期 1-5・CP4・CP3)。

- 公開の関数とクラス
  - `Right`(クラス): 権利台帳の 1 行(凍結)。欄の名と順は口の約束 1-5。
  - `Rights`(クラス): 権利台帳(列ごとの配列)。書く口は ``grant`` と ``revoke`` の 2 つだけ。
- import している内部モジュール: `shibuya.foundation.types`
- 呼び手: `shibuya.engine.calendar3.roster`・`shibuya.engine.duties.knowledge`・`shibuya.engine.duties.layer`・`shibuya.engine.economy_stage2`・`shibuya.world.facts.rights.initial`・`shibuya.world.facts.rights.record`・`shibuya.world.laws.opening`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_pop/test_w21_stage4_7.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/engine/duties/_du.py`・`tests/engine/duties/test_du_units.py`・`tests/engine/rights/rights_writers.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/rights/test_rights_schema.py`・`tests/engine/rights/test_rules42_rights.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/test_pop_w21_world.py`
- 決定の ID: 10-12/§4-5・R-113・R-118

## [record.py](../../../../../../../../../src/shibuya/world/facts/rights/record.py)

engine.rights.record — 許可のない行動の記録と、役割語の権利の確かめ(第 1 期 1-5・CP3・決定 10-12 §1-4)。

- 公開の関数とクラス
  - `RoleActCheck`(クラス): 役割語の行為の権利を確かめる(判定だけ・書かない)。``LLMBridge`` が役割語のときに呼び、数えは判断の口が持つ。
  - `events_of`(関数): 過程の ActualLog に挿した出来事の記録(``ActualLogLink.log``)。挿していなければ ``None``。
  - `manifest_fields`(関数): manifest の ``rights``: 実行器の権利台帳の欄に、判断の口の役割語の数え(許可なし・判定しない)を足す。
  - `record_unauthorized`(関数): 起きた許可のない行為を体ごとに 1 行書く(``events`` が ``None`` なら書かない)。行の数を返す。
- import している内部モジュール: `shibuya.foundation.journal.log`・`shibuya.foundation.types`・`shibuya.foundation.vocab.actions`・`shibuya.world.facts.rights.ledger`
- 呼び手: `shibuya.engine.run`・`shibuya.world.laws.opening`・`shibuya.world.laws.runner`
- 読む試験: `tests/engine/rights/test_rights_events.py`
- 決定の ID: 10-12/§1-4
