# src/shibuya/world/processes

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/world/processes/__init__.py)

(冒頭の説明なし)

## [circularity.py](../../../../../../../../src/shibuya/world/processes/circularity.py)

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

## [deletion_candidates.py](../../../../../../../../src/shibuya/world/processes/deletion_candidates.py)

world.processes.deletion_candidates — 「削除候補」台帳ファイルの追記器(D-R2-4)。

- 公開の関数とクラス
  - `append_candidates`(関数): 削除候補を台帳へ**冪等に**追記する。
  - `load_candidates`(関数): 台帳ファイルを読む(無ければ空タプル)。
  - `write_candidates`(関数): 台帳ファイルを丸ごと書き直す(並びは ``(subject_id, reason)`` 昇順=決定論)。
- import している内部モジュール: `shibuya.world.ledger.constitution`
- 読む試験: `tests/world/processes/test_deletion_candidates.py`
