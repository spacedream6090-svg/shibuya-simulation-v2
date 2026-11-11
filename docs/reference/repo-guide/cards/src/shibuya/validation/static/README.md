# src/shibuya/validation/static

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 7 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/validation/static/__init__.py)

(冒頭の説明なし)

## [bridging_scan.py](../../../../../../../../src/shibuya/validation/static/bridging_scan.py)

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

## [circularity.py](../../../../../../../../src/shibuya/validation/static/circularity.py)

world.processes.circularity — 循環(同じ値の系で動かして採点する)の機械検査(第340 段 2 の 2・回答 11-01 §3)。

- 公開の関数とクラス
  - `KnownCircularity`(クラス): 既知の循環の宣言 1 件(11-02r/§1 #6)。``remove_at`` が空の宣言は作れない(外す段つきだけが宣言)。
  - `Overlap`(クラス): 重なり 1 件。``exempt`` が空なら CI で落とす候補。
  - `PatternScoring`(クラス): パターン台帳の 1 行の「採点する系」と ``burned``。
  - `Subject`(クラス): 突き合わせの主体(世界過程・PlanSpec・つなぎの台帳の行)。
  - `classify`(関数): 例外の付かない重なりを (落とす=宣言の無い重なり, 警告=宣言つきの重なりと宣言) に分ける(11-02r/§1 #6)。
  - `find_overlaps`(関数): ``drives_from`` と「採点する系」の重なり(例外の印つき)。
  - `load_ledger_rows`(関数): つなぎの台帳の行(JSON の辞書のまま)。
  - `parse_pattern_scoring`(関数): パターン台帳の §1・§9 の表(先頭の列 ``ID``/``行``・§2 の封印表を除く)から 2 列を列の名で読む。
  - `stale_declarations`(関数): どの重なりにも当たらない宣言の主体(宣言だけが残った=循環が解けたか主体の名が変わった)。
  - `stand_in_overlap`(関数): 代打の条件 ⑤ の見方: 代打の出力が入る錨(``contributes``)と、疑いの錨の重なり。
  - `subjects_from_ledger`(関数): つなぎの台帳の active の行のうち ``drives_from`` を書いた行。``contributes`` は行の欄と、結んだ世界過程
  - `subjects_from_registry`(関数): 世界の台帳の過程と PlanSpec(``drives_from`` を書いたものだけ)。
  - `warning_lines`(関数): 警告の文(CI のログに出す 1 行ずつ=主体・系・行・外す段・決定)。
- import している内部モジュール: `shibuya.world.ledger.absent`・`shibuya.world.ledger.constitution`・`shibuya.world.ledger.records`
- 読む試験: `tests/bridging/test_drives_from_vs_scoring.py`
- 決定の ID: 11-01/§3・11-01/§10-1・11-02r/§1・11-02r/§1 #6・11-02r/§1 #8・第 340・第 340 #133・第 342

## [deletion_candidates.py](../../../../../../../../src/shibuya/validation/static/deletion_candidates.py)

world.processes.deletion_candidates — 「削除候補」台帳ファイルの追記器(D-R2-4)。

- 公開の関数とクラス
  - `append_candidates`(関数): 削除候補を台帳へ**冪等に**追記する。
  - `load_candidates`(関数): 台帳ファイルを読む(無ければ空タプル)。
  - `write_candidates`(関数): 台帳ファイルを丸ごと書き直す(並びは ``(subject_id, reason)`` 昇順=決定論)。
- import している内部モジュール: `shibuya.world.ledger.constitution`
- 読む試験: `tests/world/processes/test_deletion_candidates.py`

## [rng_audit.py](../../../../../../../../src/shibuya/validation/static/rng_audit.py)

K19 の検査(10f・K25 (a)): ``core.rng`` の流れが 1 ブロック(4 語)を超えて引き、隣の鍵の流れとブロックが重なるか。

- 公開の関数とクラス
  - `DomainStats`(クラス)
  - `StreamRecorder`(クラス): ``core.rng.philox`` を包んで、作った流れを全部覚える(``install`` で入れ、``uninstall`` で戻す)。
  - `StreamSite`(クラス)
  - `check_overlaps`(関数): 実行時の数えの検査(空なら合格)。
  - `check_sites`(関数): 静的な一覧の検査(空なら合格)。
  - `recreated_for`(関数): ``check_overlaps`` に渡す作り直しの許可(既定の腕=``K19_RECREATED`` だけ・腕 port のラン=口の分を足す)。
  - `scan_sites`(関数): ``root``(= ``src/shibuya``)の下の ``stream()``・``philox()`` の呼び手(``core/rng.py`` と ``build/`` を除く)。
- import している内部モジュール: `shibuya.foundation.rng`
- 読む試験: `tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/proximity/test_rule.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_version_bump_10e.py`
- 決定の ID: 第 330・第 346

## [system_overrides.py](../../../../../../../../src/shibuya/validation/static/system_overrides.py)

engine.systems.overrides — 試験の負の対照のための宣言の差し替え(第 1 期 1-0・草案 §3-1 の T1〜T3)。**試験のときだけ**。

- 公開の関数とクラス
  - `drop_path`(関数)
  - `drop_scratch`(関数)
  - `drop_soa`(関数)
  - `replace_spec`(関数): 系 ``name`` の ``writes`` の欄を差し替えた宣言で回す(``SYSTEMS`` と ``SPECS`` の両方)。
  - `wrap_fn`(関数): 系 ``name`` の関数を包み、T 以後の最初の 1 回だけ ``inject(ctx, b)`` を前か後に呼ぶ(段 FIX の負の対照)。
- import している内部モジュール: `shibuya.runtime.systems.table`
- 読む試験: `tests/economy/cp2/test_cp2_writes_declared.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`

## [system_static_check.py](../../../../../../../../src/shibuya/validation/static/system_static_check.py)

engine.systems.static_check — 系の宣言と系のコードを AST で突き合わせる(第 1 期 1-0・草案 §2-6 の D ①②③)。

- 公開の関数とクラス
  - `SystemCode`(クラス)
  - `analyze`(関数): 系の関数(か箱を受け取る補助)の本体を推移的に読む。
  - `analyze_spec`(関数)
  - `source_root`(関数): このモジュールのあるディレクトリ(〔移す段 2-2〕``core.paths.module_dir``)。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.foundation.paths`・`shibuya.runtime.systems.allow`
- 読む試験: `tests/engine/state/test_move_prep_stage2.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_systems_table.py`
