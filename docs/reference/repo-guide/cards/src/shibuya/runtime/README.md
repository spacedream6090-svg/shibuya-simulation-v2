# src/shibuya/runtime

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [clocks](clocks/README.md)・[inference](inference/README.md)・[state](state/README.md)・[systems](systems/README.md)

## [__init__.py](../../../../../../../src/shibuya/runtime/__init__.py)

(冒頭の説明なし)

## [clock.py](../../../../../../../src/shibuya/runtime/clock.py)

engine.clock — シミュレーション時計(壁時計に一切依存しない)。

- 公開の関数とクラス
  - `SimClock`(クラス): 開始時刻と tick 長だけを持つ不変の時計。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.types`
- 読む試験: `tests/engine/test_clock.py`
- 読む試験(道筋で): `tests/engine/test_state_checks_10f.py`・`tests/tools/test_pkgmove.py`

## [switch_defects.py](../../../../../../../src/shibuya/runtime/switch_defects.py)

engine.defect_fixes_1103 — 棚卸し B で見つけた欠陥 4 件の直しの宣言・計器・見出し(指示書 11-03 §3・小さな版上げ 1 回分)。

- 公開の関数とクラス
  - `check_resume`(関数): 再開のときに、保存したランの見出しの ``defect_fixes_1103``(無ければ legacy=版上げの前のラン)が on かを確かめる(違えば止める)。
  - `empty_counts`(関数): 計器の空の形(活動の名ごとの dict 2 本と整数 5 本)。
  - `header_fields`(関数): 状態のファイルの見出しの ``defect_fixes_1103``(ランは常に ``{"mode": "on"}``・on の外の名は None)。
  - `is_legacy`(関数): ``mode``(省略=ランの腕 on)が旧道(版上げの前の挙動=部品の口だけ)か。
  - `is_on`(関数): ``mode``(省略=ランの腕 on)が直した道か。
  - `manifest_fields`(関数): manifest の ``defect_fixes_1103``(設定=形の版・腕・4 件の宣言・直した印/観測=計器)。
  - `resolve`(関数): 引数の腕(``None``=ランの腕 ``on``)を名に直す(名の誤りは止める)。
- import している内部モジュール: `shibuya.engine.removed_switches`
- 呼び手: `shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/engine/test_defect_fixes_1103.py`
- 環境変数: `SHIBUYA_DEFECT_FIXES_1103`
- 決定の ID: 10-13b/§0-6・11-02r/§2-2・11-03・11-03/§3・第 346
