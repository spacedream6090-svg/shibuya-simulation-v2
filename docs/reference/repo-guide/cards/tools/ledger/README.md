# tools/ledger

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [add_decision_rows_1101.py](../../../../../../tools/ledger/add_decision_rows_1101.py)

add_decision_rows_1101 — つなぎの台帳に判断ごとの行(``DEC-…``)を足す(第340 段 2 の 2)。

- 公開の関数とクラス
  - `build`(関数)
  - `dec_row`(関数)
  - `dumps`(関数): 台帳の書式(1 字下げ・ensure_ascii=False・末尾に改行=既存のファイルと同じ)。
  - `main`(関数)
  - `parse_routing`(関数): routing §1(「## §1」から「## §2」の前まで)の 112 行(7 つのセル)。
  - `stage_of`(関数): DEC の行の外す段(上の表の規則)。
- 読む試験(道筋で): `tests/bridging/test_decision_rows_1101.py`
- CLI の引数
  - `sys.argv` を直接読む
- 決定の ID: 11-01・11-01/§2・11-01/§3・11-01/§10-1・11-01/§10-2・11-02r/§1・11-02r/§1 #7・第 340

## [add_pattern_columns_1101.py](../../../../../../tools/ledger/add_pattern_columns_1101.py)

add_pattern_columns_1101 — パターン台帳に「採点する系」と ``burned`` の 2 列を足す(第340 段 2 の 2)。

- 公開の関数とクラス
  - `main`(関数)
  - `transform`(関数): 台帳の文を変換する。戻り値=(新しい文, 列を足した表の数)。
- 読む試験(道筋で): `tests/bridging/test_decision_rows_1101.py`
- CLI の引数
  - `sys.argv` を直接読む
- 決定の ID: 11-01・11-01/§3・11-01/§4・11-01/§8・11-02r/§1・11-02r/§1 #6・第 340・第 342

## [fix_pattern_rows_1102.py](../../../../../../tools/ledger/fix_pattern_rows_1102.py)

fix_pattern_rows_1102 — パターン台帳の D5′ と E5 の行を検証の側へ移す(11-02r/§1 #6・第341 段 2)。

- 公開の関数とクラス
  - `main`(関数)
  - `transform`(関数): 台帳の文を変換する。戻り値=(新しい文, 直したセルと行の数)。
- CLI の引数
  - `sys.argv` を直接読む
- 決定の ID: 11-01/§3・11-01/§8・11-02・11-02r/§1・11-02r/§1 #6・第 341・第 342
