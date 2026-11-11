# src/shibuya/engine/bridging

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/bridging/__init__.py)

engine.bridging — つなぎの台帳(第 1 期 1-4・CA8・計器の最初)。

## [ledger.py](../../../../../../../../src/shibuya/engine/bridging/ledger.py)

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
- import している内部モジュール: `shibuya.core.paths`
- 呼び手: `shibuya.engine.calendar_self`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.state_io`・`shibuya.engine.tools.registry`
- 読む試験: `tests/bridging/test_decision_rows_1101.py`・`tests/economy/test_min_wage_human_bridge.py`・`tests/engine/body/test_body_rules_sources.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/contact/test_c2_charge.py`・`tests/engine/multiday/test_md23_w9_window.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/engine/tools/test_c0_tool_registry.py`
- 決定の ID: 10-12/§1・10-12/§2・10-13b/§0-6・10-13b/§3・10-13b/§4-2・11-01・11-01/§3・11-01p・R-113・第 340

## [ledger_paths.py](../../../../../../../../src/shibuya/engine/bridging/ledger_paths.py)

engine.bridging.ledger_paths — 今の道 → つなぎの台帳に書いてある道の対応(移す段 4 の下ごしらえ・親の決定 1=案 (b))。

- 公開の関数とクラス
  - `current_path`(関数): 台帳に書いてある道 → 今の道(表に無ければそのまま)。表の値が重なれば ``ValueError``。
  - `ledger_path`(関数): 今の道 → 台帳に書いてある道(表に無ければそのまま)。
- 呼び手: `shibuya.engine.bridging.scan`
- 読む試験: `tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`

## [scan.py](../../../../../../../../src/shibuya/engine/bridging/scan.py)

engine.bridging.scan — コードの expedient の宣言を AST で数える(第 1 期 1-4・つなぎの台帳との 1 対 1)。

- 公開の関数とクラス
  - `Declaration`(クラス): コードの expedient の宣言 1 つ(``items`` は見出しの形のときだけ=見出しの下の項の数)。
  - `count_by_form`(関数): 形ごとの件数(6 形とも鍵を持つ)。
  - `declared_in_of`(関数): 宣言の同定の文字列(台帳の ``declared_in`` と同じ形)。道筋は台帳に書いてある道(〔移す段 4 の下ごしらえ〕移した
  - `fallback_declarations`(関数): F: フォールバック台帳の行(``rows`` を省くと ``first_batch.build_registry().fallback_ledger()`` を実行して読む)。
  - `scan_package`(関数): このパッケージ(``src/shibuya``)の宣言(A〜E は AST・F はフォールバック台帳を実行して読む)。道筋は
  - `scan_source`(関数): 1 つのファイルの宣言(``path`` はリポの根からの道筋=``declared_in`` に入る)。
  - `scan_tree`(関数): ``root`` の下の ``*.py`` を全部見る(道筋は ``rel_to`` からの posix の相対=既定は ``root`` の親の親)。
- import している内部モジュール: `shibuya.core.paths`・`shibuya.engine.bridging.ledger_paths`・`shibuya.world.processes.first_batch`・`shibuya.world.processes.registry`
- 読む試験: `tests/engine/body/test_body_rules_sources.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/state/test_move_prep_stage2.py`
- 決定の ID: 第 334
