# src/shibuya/core

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../src/shibuya/core/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [wage_formula.py](../../../../../../../src/shibuya/core/wage_formula.py)

core.wage_formula — 職業 × 性 × 年齢 × 雇用形態の賃金の式と表の読み解き(賃金構造基本統計調査 令和 7 年=R-107)。

- 公開の関数とクラス
  - `WageTables`(クラス): 実行時の賃金の表(配列は書き込み禁止)。欄の名と形は ``build.pop.attr_fns.AttrTablesB`` の賃金の欄と同じ。
  - `apply_floor`(関数): 〔検収 M1〕最低賃金法の床(4 条 2 項=足りない部分は最低賃金と同じ定めとみなす)。時給(月 ÷ 月の時間の目安)が床を
  - `median_check`(関数): 計器(構築側の点検=合否なし): 職種 × 性ごとの月の賃金の中央値と、第18表の中位数(一般労働者)との差。
  - `month_hours`(関数): 〔検収 M1〕体ごとの月の所定内の時間の目安[時]\(最低賃金の床=時給 × この時間)。
  - `occupation_wages`(関数): 体ごとの月の賃金[円]\(所定内給与)と出どころ(:data:`BASIS_NAMES` の番号)。純粋(表と入力を読むだけ)。
  - `parse_wage_tables`(関数): 賃金構造 令和 7 年(第9・6・18 表と短時間 第2表の写しの行)→ 賃金の欄(企業規模計・円と時間)。
  - `wage_quantile`(関数): 第18表の所定内給与額の階級の度数(職種 × 男女)から分位 u の値[円/月]\(階級の中は一様=宣言)。
  - `wage_uniform`(関数): 体ごとの分位 u(用途名 :data:`WAGE_DOMAIN`・``counters`` は (n, ≤3) の鍵の語・1 語だけ引く)。
  - `wage_values`(関数): (所定内給与[円/月], 時間あたり[円], 年の賃金[円])。対象外(``ok`` が偽)は −1。
- import している内部モジュール: `shibuya.foundation.rng`
- 呼び手: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_money`・`shibuya.economy.wages`
- 読む試験: `tests/economy/test_wage_occupation.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 決定の ID: 10-12/§4-11・10-13b/§7・R-107
