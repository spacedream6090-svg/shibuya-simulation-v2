# src/shibuya/engine/systems

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/engine/systems/__init__.py)

(冒頭の説明なし)

## [overrides.py](../../../../../../../../src/shibuya/engine/systems/overrides.py)

engine.systems.overrides — 試験の負の対照のための宣言の差し替え(第 1 期 1-0・草案 §3-1 の T1〜T3)。**試験のときだけ**。

- 公開の関数とクラス
  - `drop_path`(関数)
  - `drop_scratch`(関数)
  - `drop_soa`(関数)
  - `replace_spec`(関数): 系 ``name`` の ``writes`` の欄を差し替えた宣言で回す(``SYSTEMS`` と ``SPECS`` の両方)。
  - `wrap_fn`(関数): 系 ``name`` の関数を包み、T 以後の最初の 1 回だけ ``inject(ctx, b)`` を前か後に呼ぶ(段 FIX の負の対照)。
- import している内部モジュール: `shibuya.runtime.systems.table`
- 読む試験: `tests/economy/cp2/test_cp2_writes_declared.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`

## [static_check.py](../../../../../../../../src/shibuya/engine/systems/static_check.py)

engine.systems.static_check — 系の宣言と系のコードを AST で突き合わせる(第 1 期 1-0・草案 §2-6 の D ①②③)。

- 公開の関数とクラス
  - `SystemCode`(クラス)
  - `analyze`(関数): 系の関数(か箱を受け取る補助)の本体を推移的に読む。
  - `analyze_spec`(関数)
  - `source_root`(関数): このモジュールのあるディレクトリ(〔移す段 2-2〕``core.paths.module_dir``)。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.foundation.paths`・`shibuya.runtime.systems.allow`
- 読む試験: `tests/engine/state/test_move_prep_stage2.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_systems_table.py`
