# src/shibuya/world/facts/rules

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../../src/shibuya/world/facts/rules/__init__.py)

(冒頭の説明なし)

## [table.py](../../../../../../../../../src/shibuya/world/facts/rules/table.py)

engine.rules.table — 規則の表(第 1 期 1-4・CP10・決定 10-12 §1-12「現実の法と制度に基づいて実装する」)。

- 公開の関数とクラス
  - `Rule`(クラス): 規則の表の 1 行(凍結)。
  - `RuleNotInForce`(クラス): ``asof`` の日に効いている版が表に無い(施行の前・または表に版が無い)。
  - `Rules`(クラス): 規則の表(読むだけ)。行の差し替え・属性の付け替えはできない(1-3 検収 L2 の守り)。
  - `Source`(クラス): 規則の出典 1 つ(法令名・条・版・URL は必須)。
  - `canonical_sha`(関数): 正規化した JSON(鍵の昇順・区切りの空白なし・UTF-8)の sha256 の先頭 16 桁(改行の違いに左右されない)。
  - `default_path`(関数): リポの表の道筋(``<リポの根>/docs/design/rules-table.json``)。
  - `default_rules`(関数): リポの表(1 回だけ読む)。
  - `load`(関数): 表を読む(形式の版・欄の検査つき)。
  - `rules_version`(関数): manifest と日次の記録の ``rules_version``(表の sha)。表のファイルが無い写しでは ``None``(ランは止めない)。
- import している内部モジュール: `shibuya.foundation.paths`
- 呼び手: `shibuya.economy.anchors`・`shibuya.economy.taxes`・`shibuya.engine.calendar3.layer`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/economy/test_min_wage_human_bridge.py`・`tests/economy/test_rules42_credit.py`・`tests/economy/test_rules42_payroll.py`・`tests/economy/test_rules42b_payroll.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/rules/test_rules42_table.py`・`tests/engine/rules/test_rules_table_schema.py`・`tests/engine/state/test_move_prep_stage2.py`
- 決定の ID: 10-12/§1-12・R-106・R-113・R-118
