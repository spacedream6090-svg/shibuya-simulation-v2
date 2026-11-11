# src/shibuya/foundation/decl

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/foundation/decl/__init__.py)

(冒頭の説明なし)

## [bridging.py](../../../../../../../../src/shibuya/foundation/decl/bridging.py)

engine.bridging.ledger — つなぎの台帳(第 1 期 1-4・CA8・計器の最初)。

- 公開の関数とクラス
  - `Bridge`(クラス): つなぎの台帳の 1 行(凍結)。
  - `BridgeLedger`(クラス): つなぎの台帳(読むだけ)。行の差し替え・属性の付け替えはできない(1-3 検収 L2 の守り)。
  - `bridges_count`(関数): manifest と日次の記録の ``bridges_count``(active の行の数)。台帳のファイルが無い写し(``git archive`` で
  - `bridges_version`(関数): manifest の ``bridges_version``(台帳の中身の sha=検収 L1)。台帳のファイルが無い写しでは ``None``。
  - `canonical_sha`(関数): 正規化した JSON(鍵の昇順・区切りの空白なし・UTF-8)の sha256 の先頭 16 桁(改行の違いに左右されない)。
  - `code_mismatch`(関数): コードの宣言(``scan`` の ``declared_in`` の並び)と台帳の active の行の突き合わせ。
  - `default_ledger`(関数): リポの台帳(1 回だけ読む)。
  - `default_path`(関数): リポの台帳の道筋(``<リポの根>/docs/design/bridging-ledger.json``)。
  - `load`(関数): 台帳を読む(形式の版・欄の検査つき。壊れた JSON・知らない欄・不正な値は ``ValueError``)。
- import している内部モジュール: `shibuya.foundation.paths`
- 呼び手: `shibuya.engine.calendar_self`・`shibuya.engine.run`・`shibuya.engine.tools.registry`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/bridging/test_decision_rows_1101.py`・`tests/economy/test_min_wage_human_bridge.py`・`tests/engine/body/test_body_rules_sources.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/multiday/test_md23_w9_window.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/engine/tools/test_c0_tool_registry.py`
- 決定の ID: 10-12/§1・10-12/§2・10-13b/§0-6・10-13b/§3・10-13b/§4-2・11-01・11-01/§3・11-01p・R-113・第 340

## [ledger_paths.py](../../../../../../../../src/shibuya/foundation/decl/ledger_paths.py)

engine.bridging.ledger_paths — 今の道 → つなぎの台帳に書いてある道の対応(移す段 4 の下ごしらえ・親の決定 1=案 (b))。

- 公開の関数とクラス
  - `current_path`(関数): 台帳に書いてある道 → 今の道(表に無ければそのまま)。表の値が重なれば ``ValueError``。
  - `ledger_path`(関数): 今の道 → 台帳に書いてある道(表に無ければそのまま)。
- 呼び手: `shibuya.validation.static.bridging_scan`
- 読む試験: `tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`
