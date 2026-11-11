# src/shibuya/engine/bridging

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/bridging/__init__.py)

(冒頭の説明なし)

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
- import している内部モジュール: `shibuya.foundation.decl.ledger_paths`・`shibuya.foundation.paths`・`shibuya.world.ledger.first_batch`・`shibuya.world.ledger.registry`
- 読む試験: `tests/engine/body/test_body_rules_sources.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/state/test_move_prep_stage2.py`
- 決定の ID: 第 334
