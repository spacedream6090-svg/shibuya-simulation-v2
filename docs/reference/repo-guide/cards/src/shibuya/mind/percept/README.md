# src/shibuya/mind/percept

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/mind/percept/__init__.py)

(冒頭の説明なし)

## [attention.py](../../../../../../../../src/shibuya/mind/percept/attention.py)

mind.percept.attention — 割る段で ``perception/attention.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `gate_stage1`(関数): 段1 の一発ベルヌーイ(決定論・``core.rng.stream`` のドメイン分離)。
  - `p_see`(関数): 媒体 → 視認確率(§4 段1)。
- import している内部モジュール: `shibuya.foundation.rng`
- 呼び手: `shibuya.mind.memory.familiarity`・`shibuya.perception.renderer`
- 読む試験: `tests/engine/test_familiarity.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/test_attention.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_signage_p_see_gate.py`
- 決定の ID: 11-03
