# src/shibuya/build/pop

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 24 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/build/pop/__init__.py)

build.pop — 世界データ構築 W16(母集団合成)。

- 呼び手: `shibuya.build.pop.run`・`shibuya.build.run`
- 読む試験: `tests/build_pop/test_w21_build_real.py`・`tests/build_pop/test_w21_stage4_7.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [attr_fns.py](../../../../../../../../src/shibuya/build/pop/attr_fns.py)

「属性から作る関数」の置き場(計画 第 4 期の注・答申 R-116 §3-3・W21 段 3)。

- 公開の関数とクラス
  - `AttrFn`(クラス): 登録表の 1 行。
  - `AttrKey`(クラス): 乱数の鍵(seed・ドメイン・人ごとの鍵の語 (n, ≤3))。
  - `AttrTables`(クラス): 材料の表から作った確率の表(書き込み禁止)と、町丁目 × 男女の周辺の割合。
  - `AttrTablesB`(クラス): 段 4〜7 の材料の表(書き込み禁止)。金額は円・時間は時間。``md5`` は材料の表の id → md5。
  - `AttrTablesC`(クラス): 段 9〜10 の材料の表(書き込み禁止)。``nationality_names``/``nationality_w``=渋谷区の外国人の国籍(住民基本台帳
  - `age17`(関数): 各歳 → 就業の表の年齢 17 階級(15-19 … 90-94・95 歳以上)。15 歳未満は −1。
  - `calendar_inputs`(関数): 3-1 の W20(``calendar_from_attributes``)に渡す 5 属性(``kind``・``age``・``industry_key``・
  - `calendar_inputs_b`(関数): **段 10 の材料**(W20 の入力そのものではない): 段 4〜7 の人の表(``w21_people``=住民+外から来て働く人)の 5 列
  - `call`(関数): 登録表の関数を呼ぶ(入力の列がそろっていなければ止める)。
  - `f_blank_int`(関数): 空欄(−1)を返すだけの関数(財布の現金・カードの有無・口座の有無=構築側の錨が無い=R-107 §1-7・回答 10-12b §3 (2))。
  - `f_commuter_age`(関数): 外から来て働く人の年齢(同じ表・5 歳階級の中は一様=宣言)。
  - `f_commuter_sex`(関数): 外から来て働く人の男女(従業地 第11-1表・``tables`` は段 3 の :class:`AttrTables`)。
  - `f_commuter_status_split`(関数): 外から来て働く人の従業上の地位(段 3 の ``emp_status`` の番号)のうち、段 3 が「雇用者でない人」を寄せた雇人のない業主
  - `f_consumer_credit`(関数): 貸金業の残高[円]\(JICC 2026-08 末=引)。20 歳以上だけ・有無=残高のある人 ÷ 全国の 20 歳以上人口(国勢調査 2025)・
  - `f_duty_role`(関数): 職務の役割(店長・正社員・パートなど)。段 4(PS5)まで空欄(v1 の在庫は使わない=R-116 §5)。
  - `f_duty_role_org`(関数): ②群(開店・補充・配送・運転・駅員・車掌・運転士)を受け持つ体の語(規則の表=自前・expedient・W16 の語に寄せた)。
  - `f_emp_status`(関数): 従業上の地位(就業者)。住民: 第3-1表を事前の重みに町丁目の第10表(雇用者・自営業主・家族従業者)へ寄せる。
  - `f_employment_status`(関数): W20 に渡す粗い区分(写像 :data:`EMPLOYMENT_OF_STATUS`)。空欄は ""。
  - `f_entry_node`(関数): 舞台の出入りの駅の口(W12 の鉄道の外の口)。外から来て働く人と、舞台の外で働く住民(区の残り・区の外)だけ。重み=
  - `f_first_language`(関数): 第一言語(ISO 639-1)=国籍の写像(:data:`NATIONALITY_LANGUAGE`)。写像に無い国籍と空欄の国籍は空欄。
  - `f_household_debt`(関数): 世帯の金融負債残高[円]。有無=全国の年齢 × 種類の負債保有率 × 東京都の貯蓄の階級ごとの負債保有率 ÷ 東京都の全体の率
  - `f_household_deposits`(関数): 世帯の通貨性預貯金[円]=貯蓄 × 通貨性預貯金の平均 ÷ 貯蓄の平均(全国 第4-4表・世帯の種類 × 年齢・比は一定=宣言)。
  - `f_household_savings`(関数): 世帯の金融資産残高(貯蓄現在高)[円]\(全国家計構造調査 2024・世帯の単位)。**階級の度数をそのまま**(R-107 結論 2):
  - `f_industry_key`(関数): W16 の 15 語(写像 :data:`INDUSTRY_KEY_OF_MAJOR`・N は LS/AM を経済センサスの比で)。空欄は ""。
  - `f_industry_major`(関数): 産業大分類。住民: 第5-1表(男女 × 年齢 × 地位)を事前の重みに町丁目の第11表へ。通勤: 従業地の第11-1表。
  - `f_japanese_level`(関数): 日本語の会話の程度(:data:`JAPANESE_LEVELS` の番号・−1=空欄)。外国籍で 18 歳以上の人だけ、国籍の行(無ければ
  - `f_known_places`(関数): 行ったことのある場所の数 L=C ×(住んでいる週 ÷ 20 週)^0.6(Song 2010 の μ・20 週=容量の窓)。住んでいる年数が空欄の
  - `f_labour_status`(関数): 労働力状態(住民の 15 歳以上)。事前の重み=区の就業率(男女 × 年齢 × 配偶関係)・周辺=町丁目の第9・10表。
  - `f_nationality`(関数): 国籍の語。住民の外国人(``is_foreign``)=渋谷区の国籍の人数の比で引く(年齢・男女で条件づけない=宣言)・住民の日本人=
  - `f_occupation_major`(関数): 職業大分類。住民: 第10-1表(男女 × 年齢 × 産業)を事前の重みに町丁目の第12表へ。通勤: 第16-1表(男女 × 産業)。
  - `f_org_role`(関数): 従業上の地位 → 組織の中の役割の語(:data:`ROLE_OF_STATUS`・就業者でない人は "")。頭の語は ``w21_org`` が上書きする。
  - `f_origin_muni`(関数): 常住地(市区町村の 5 桁)。外から来て働く人=第4表の流入元の重み(渋谷区の残りの町丁目=輪は区の行の重み)・住民=13113。
  - `f_place_capacity`(関数): なじみの場所の数(容量)C=round(正規(25, 25 × CV))を [5, 60] に切る(平均=Alessandretti 2018・幅=expedient)。
  - `f_residence_period`(関数): 居住期間(住民)。事前の重み=年齢で上限を切った一様・周辺=町丁目の第18表。
  - `f_residence_years`(関数): 住んでいる年数(第18表の区分の中で一様=宣言・出生時から=年齢・20 年以上の上の端=年齢)。区分が空欄の人は NaN。
  - `f_school_kind`(関数): 在学・未就学の種類。住民: 事前の重み=年齢の窓(:data:`SCHOOL_AGE_WEIGHTS`)・周辺=町丁目の第14表。
  - `f_school_place`(関数): 通学地(住民の 15 歳以上の在学者=高校・短大高専・大学・大学院)。周辺=町丁目の第16-3表。15 歳未満は空欄。
  - `f_student_in_age`(関数): 外から来る通学者の年齢(同じ表・5 歳階級の中は一様=宣言)。
  - `f_student_in_sex`(関数): 外から来る通学者の男女(第1-3表の「うち他市区町村に常住」・通学地=渋谷区)。
  - `f_w16_employment`(関数): ``employment_status`` → W16 の ``employment`` の 6 値(:data:`W16_EMPLOYMENT_OF`・None と空欄は「非就業」)。
  - `f_w16_kind`(関数): (層, 役割)→ W16 の kind の番号(:data:`W16_KIND`・表に無い組は −1)。
  - `f_wage_annual`(関数): 年の賃金[円]=12 × 月+年間賞与(同じ鍵で ``wage_monthly`` と同じ人の値)。
  - `f_wage_hourly`(関数): 時間あたりの所定内給与[円]\(同じ鍵で ``wage_monthly`` と同じ人の値)。
  - `f_wage_monthly`(関数): 所定内給与[円/月]\(賃金構造 令和 7 年)。雇われて働く人で職業が分かる人だけ・ほかは −1(空欄)。
  - `f_weekly_hours`(関数): 週の所定内の時間の目安(権利台帳の雇用の行・段 4)。一般=第9表の所定内実労働時間(月)× 12 ÷ 52.1775 週・短時間=
  - `f_workplace_kind`(関数): 従業地(住民の就業者・常住地から見た)。事前の重み=第8表(地位の組 × 産業)・周辺=町丁目の第16-2表。
  - `rake_draw`(関数): 人ごとの事前の重み(n, K)を、組ごとの周辺の割合(G, M)へ寄せてから引く(−1=重みが無い人)。
  - `registry_versions`(関数): 登録表の名 → 版(``stages`` の段の関数だけ・登録の順)。
  - `savings_class`(関数): 貯蓄[円] → 貯蓄現在高の階級(0=25 万円未満=0 円を含む)。
  - `walk_seconds`(関数): 歩く道のり[m] → 秒(参照の速さで割るだけ・−1 と負は NaN)。人物の文(分に四捨五入=丸めた言葉)と W20 の片道の時間
- import している内部モジュール: `shibuya.core.rng`・`shibuya.core.wage_formula`
- 呼び手: `shibuya.build.pop.w21_apply`・`shibuya.build.pop.w21_attrs`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`・`shibuya.build.pop.w21_check`・`shibuya.build.pop.w21_money`・`shibuya.build.pop.w21_org`・`shibuya.build.pop.w21_persona`・`shibuya.build.pop.w21_port10`・`shibuya.build.pop.w21_prior`・`shibuya.build.sched.w20_w21_port`
- 読む試験: `tests/build_pop/test_w21_attr_fns.py`・`tests/build_pop/test_w21_stage4_7.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/build_sched/test_w20_w21_port.py`・`tests/economy/test_wage_occupation.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-12b/§3・R-80・R-107・R-110・R-116

## [fitting.py](../../../../../../../../src/shibuya/build/pop/fitting.py)

build.pop.fitting — IPF(raking)・整数配分・適合度指標(SRMSE / JSD)。

- 公開の関数とクラス
  - `IPFResult`(クラス): ``(table, n_iter, max_residual)`` の名前つきタプル。
  - `ipf`(関数): 2 次元 IPF(iterative proportional fitting)。
  - `jsd`(関数): Jensen-Shannon divergence(既定 log2 = 0..1 の範囲)。
  - `largest_remainder`(関数): 重み → 合計が厳密に ``total`` になる非負整数の配分(最大剰余法)。
  - `srmse`(関数): 標準化 RMSE。``sim``/``obs`` はカウントでも割合でもよい(内部で割合に直す)。
- 呼び手: `shibuya.build.pop.w16_population`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_households`・`shibuya.build.pop.w21_org`・`shibuya.build.pop.w21_tables`・`tools/c8/sensitivity.py`
- 読む試験: `tests/build_pop/test_pop_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [pool.py](../../../../../../../../src/shibuya/build/pop/pool.py)

build.pop.pool — v1 ペルソナプール(素材)の読み取りと列化。

- 公開の関数とクラス
  - `Pool`(クラス): 全層。``meta`` は ``meta.json`` の中身。
  - `PoolLayer`(クラス): 1 層ぶんの列(行順=ファイル順=``pool_index``)。
  - `layer_files`(関数): 層の part ファイル(名前順=決定論)。
  - `read_layer`(関数): 1 層を読んで列化する。逐次ループ宣言(P4): プール行数ぶん。
  - `read_pool`(関数): ``data/persona_pool_v2`` を読む。
- 呼び手: `shibuya.build.pop.w16_population`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [run.py](../../../../../../../../src/shibuya/build/pop/run.py)

build.pop.run — 母集団レーンの段階を W 番号順に実行する CLI。

- 公開の関数とクラス
  - `main`(関数)
  - `run_stages`(関数): 段階を順に実行してヘッダを書く(geo.run.run_stages と同形)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.geo.run`・`shibuya.build.pop`・`shibuya.build.pop.w16_population`
- 呼び手: `shibuya.build.run`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`: 入力データ根(既定 data)
  - `--out`: 出力ディレクトリ(例 data/world/v2)
  - `--quiet`
  - `--stage`: 実行する段階(既定=全段階)

## [shapefile.py](../../../../../../../../src/shibuya/build/pop/shapefile.py)

build.pop.shapefile — ESRI Shapefile(.shp/.dbf)の最小パーサと点包含・被覆率。

- 公開の関数とクラス
  - `Polygon`(クラス): 1 レコード=1 ポリゴン(複数リング可)。
  - `assign_points_to_polygons`(関数): 点 → 最初に包含したポリゴンの添字(見つからなければ −1)。
  - `coverage_fraction`(関数): ポリゴンを固定格子で標本化し、``inside_fn(x, y) -> bool 配列`` が真の面積割合を返す。
  - `points_in_polygon`(関数): 全パートの交差数の総和の偶奇(穴つきポリゴンでも正しい)。
  - `points_in_ring`(関数): レイキャスティング(crossing number)の**交差の偶奇**を bool で返す。
  - `polygon_area`(関数): パートの符号つき面積の総和の絶対値(穴は符号が逆なので引かれる)。
  - `read_dbf`(関数): .dbf → レコード辞書のリスト(フィールド順は宣言順・値は str または float/int)。
  - `read_shp`(関数): .shp → Polygon のリスト(レコード順)。
  - `ring_area`(関数): 符号つき面積(反時計回りが正)。
- 呼び手: `shibuya.build.field.w10_ruler`・`shibuya.build.pop.w16_population`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`tools/c8/sensitivity.py`
- 読む試験: `tests/build_field/test_w10_ruler.py`・`tests/build_pop/test_pop_units.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w16_population.py](../../../../../../../../src/shibuya/build/pop/w16_population.py)

W16 母集団合成(§1 W16・D-W16・決定台帳「母集団合成」7 段のうち ①〜⑥)。

- 公開の関数とクラス
  - `run`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.fitting`・`shibuya.build.pop.pool`・`shibuya.build.pop.shapefile`・`shibuya.core.rng`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.pop.run`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_tables`・`shibuya.build.sched.trial`・`shibuya.build.sched.w17_schedule`・`shibuya.build.sched.w20_calendar_1a`・`tools/c8/sensitivity.py`
- 読む試験: `tests/build_pop/test_pop_pipeline.py`・`tests/build_pop/test_pop_units.py`・`tests/build_sched/test_trial.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w21_apply.py](../../../../../../../../src/shibuya/build/pop/w21_apply.py)

W21 段 10「差し替え」(第 4 期 4-1 段 10=4-3 版上げ 3 回目)の組み立て。版 1.1.0(検収の直し=通学者を残す・担当の体の機能定員と種別 8・乗務員の提供者・外の雇用主の雇用の行・提供者の使い回しの門)。

- 公開の関数とクラス
  - `ProtectedOutputErrorApply`(クラス): ``--out`` が本体の v2・読む世界資産の中・差し替えの資産の置き場の外を指している(何も書かずに止める)。
  - `UnknownW16GroupError`(クラス): W16 の在庫の群(種別, 担当の語)が :data:`W16_GROUP_ACTION` に無い(黙って残さない・外さない)。
  - `apply`(関数): 段 10 の差し替えを ``out`` に組む。返り値は(見出し, manifest)。
  - `check_out_apply`(関数): 出力先の検査: 本体の ``data/world/v2``・``--world`` の中なら止める。``data/world`` の下なら置き場の名が
  - `donor_schedules`(関数): W21 の人(受け手)に外す W16 の体(提供者)の 7 日の行を写す。
  - `main`(関数)
  - `merge_population`(関数): W16 の残す行(``agent_id`` 不変)+W21 の行 → 母集団の列(``agent_id`` の昇順)。番号が重なれば止める。
  - `rights_run_rows`(関数): engine の ``rights.initial`` が読む行(体の番号=ランの ``agent_id``): 店の担当(W21c の体 → 店)と住まい(W21b の
  - `select_crews`(関数): 〔検収 M2〕W21 の担当の体のうち機能定員(``quota``=担当の語 → 数)まで選ぶ(人ごとの Philox の順で先頭から)。
  - `w16_actions`(関数): W16 の行ごとの扱い(``True``=残す)と群の表(種別|担当 → 行の数・扱い)。知らない群は止める。
  - `w21_population_columns`(関数): W21 の人の表(``w21_people``・段 1〜3 の ``w21_persons``・段 5 の ``w21_money``)→ W16 の母集団の列(:data:`POPULATION_COLUMNS`
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`・`shibuya.build.pop.w21_sources`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.build.sched.w20_w21_port`・`shibuya.core.rng`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`
  - `--out`
  - `--seed`
  - `--world`: 元の W16・W17 の世界資産(既定 <data>/world/v2・読むだけ)

## [w21_attrs.py](../../../../../../../../src/shibuya/build/pop/w21_attrs.py)

W21 段 3「属性」: 材料の表から ``attr_fns.AttrTables`` を組み、住民に「属性から作る関数」をかける。

- 公開の関数とクラス
  - `apply_attrs`(関数): 住民の列(``kind``・``sex``・``age``・``marital``・``chome``・``persona_kind``・``role``)に段 3 の関数をかけ、
  - `build_tables`(関数): 材料の表 → ``AttrTables``(凍結)と、町丁目の「不詳」を割り振った人数(2020 の町丁目の不詳 × 被覆率)。
  - `words`(関数): 番号 → 語(−1 は "")。
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_sources`・`shibuya.build.pop.w21_tables`
- 呼び手: `shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`
- 読む試験: `tests/build_pop/test_w21_attr_fns.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: R-116

## [w21_build.py](../../../../../../../../src/shibuya/build/pop/w21_build.py)

W21(第 4 期 4-1 段 1〜3「人数の枠・世帯と人・属性」)の組み立て。版 1.0.0。

- 公開の関数とクラス
  - `ProtectedOutputError`(クラス): ``--out`` が本体の v2・読む世界資産・既存の資産の置き場の中を指している(何も書かずに止める)。
  - `build`(関数): W21 を組んで ``out`` に書く。返り値は(見出し, manifest)。``out`` は :func:`check_out` で先に確かめる。
  - `check_out`(関数): 出力先の検査: 本体の ``data/world/v2``・``--world`` の中と、``data/world`` の下の既存の置き場(W21 の段の資産
  - `main`(関数)
  - `prepare`(関数): 町丁目の境界・被覆率・建物と、段 2 の手順 1・2(区の雛形と町丁目の目標)。段 4〜7(``w21_build_b``)も同じ値を使う。
  - `source_world`(関数): W21(段 1〜10)を組む元の世界(W16 1.0.0 の世界)。〔段 10〕活性化の後の本体の v2(W16 が W21 に替わった世界=
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.attr_fns`・`shibuya.build.pop.fitting`・`shibuya.build.pop.shapefile`・`shibuya.build.pop.w16_population`・`shibuya.build.pop.w21_attrs`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_frame`・`shibuya.build.pop.w21_households`・`shibuya.build.pop.w21_sources`・`shibuya.build.pop.w21_tables`・`shibuya.core.rng`
- 呼び手: `shibuya.build.pop.w21_apply`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`
- 読む試験: `tests/build_pop/test_w21_attr_fns.py`・`tests/build_pop/test_w21_build_real.py`・`tests/build_pop/test_w21_sources.py`・`tests/build_sched/test_w20_calendar_1a.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--anneal-iter`
  - `--data`
  - `--out`
  - `--seed`
  - `--w21-anneal`
  - `--world`: 読む世界資産(既定 <data>/world/v2・読むだけ)

## [w21_build_b.py](../../../../../../../../src/shibuya/build/pop/w21_build_b.py)

W21 段 4〜7(第 4 期 4-1「組織と関係・お金・開始前の経験・外の人」)の組み立て。版 1.2.0(1.1.0 に第 4 期 4-3 段 10 の地位の分け=外から来て働く人の役員・業主・家族従業者を席の前に=親の判断 仮-33 (2))。

- 公開の関数とクラス
  - `ParamsB`(クラス): 段 4〜7 の腕(既定は宣言の値)。
  - `ProtectedOutputErrorB`(クラス): ``--out`` が本体の v2・読む世界資産・段 1〜3 の資産・既存の置き場の中を指している(何も書かずに止める)。
  - `build_b`(関数): 段 4〜7 を組んで ``out`` に書く。返り値は(見出し, manifest)。
  - `check_out_b`(関数): 出力先の検査: 本体の ``data/world/v2``・``--world``・``--base``(段 1〜3 の資産)の中と、``data/world`` の下の既存の
  - `main`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.attr_fns`・`shibuya.build.pop.shapefile`・`shibuya.build.pop.w21_attrs`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_money`・`shibuya.build.pop.w21_org`・`shibuya.build.pop.w21_outside`・`shibuya.build.pop.w21_port10`・`shibuya.build.pop.w21_prior`・`shibuya.build.pop.w21_sources`・`shibuya.build.pop.w21_tables`・`shibuya.core.rng`
- 呼び手: `shibuya.build.pop.w21_apply`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_pop/test_w21_stage4_7.py`・`tests/build_pop/test_w21_stage8_9.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--affinity`
  - `--base`: 段 1〜3 の資産(既定 <data>/world/v2_stage_4-1・読むだけ)
  - `--data`
  - `--division-arm`
  - `--out`
  - `--seat-roles`
  - `--seed`
  - `--world`: 読む世界資産(既定 <data>/world/v2・読むだけ)
- 決定の ID: R-80・R-107・R-110・R-116・R-116 #17

## [w21_build_c.py](../../../../../../../../src/shibuya/build/pop/w21_build_c.py)

W21 段 8〜9 と段 10 の材料(第 4 期 4-1「点検・見せ方・差し替えの材料」)の組み立て。版 1.2.0。

- 公開の関数とクラス
  - `ProtectedOutputErrorC`(クラス): ``--out`` が本体の v2・読む世界資産・段 1〜7 の資産・既存の置き場の中を指している(何も書かずに止める)。
  - `build_c`(関数): 段 8〜9 と段 10 の材料を組んで ``out`` に書く。返り値は(見出し, manifest)。
  - `check_out_c`(関数): 出力先の検査: 本体の ``data/world/v2``・``--world``・``--base``(段 1〜7)・段 1〜3 の資産の中と、``data/world`` の下の
  - `language_columns`(関数): 段 9 の言語の列(国籍・第一言語・日本語の程度=``people`` の並び)。
  - `load_inputs`(関数): 段 1〜7 の資産(sha256 を manifest と照らす)・世界資産の列・材料の表を読む。
  - `main`(関数)
  - `persona_facts`(関数): 段 9 の事実の表(``w21_persona.facts_from_w21`` に資産の表を渡すだけ)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_attrs`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_check`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_outside`・`shibuya.build.pop.w21_persona`・`shibuya.build.pop.w21_port10`・`shibuya.build.pop.w21_sources`・`shibuya.build.sched.w20_w21_port`
- 呼び手: `shibuya.build.pop.w21_apply`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/engine/test_pop_w21_world.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--base`: 段 1〜7 の資産(既定 <data>/world/v2_stage_4-1b・読むだけ)
  - `--data`
  - `--in-place`: 段 10 の差し替えの資産を組むとき(--base と --out が同じ置き場=段 4〜7 を組み直した置き場)
  - `--out`
  - `--seed`
  - `--world`: 読む世界資産(既定 <data>/world/v2・読むだけ)
- 決定の ID: R-110・R-110 §3-2 #25

## [w21_check.py](../../../../../../../../src/shibuya/build/pop/w21_check.py)

W21 段 8「点検」(PS6): 段 1〜7 の資産(住民・外から来て働く人・世帯・組織・権利・関係・お金・なじみの場所・外の人の層)を点検の表にする。**合否は付けない**(CA8 と同じ=診断)。出力 ``w21_check.json``。

- 公開の関数とクラス
  - `couple_children`(関数): 夫婦(世帯主と配偶者)のいる世帯の夫の年齢・子(続き柄が子)の数・最年少の子の年齢(子のいない世帯は −1)。
  - `distribution_rows`(関数): (a) の点検の行(住民の年齢 × 男女 … 日本語の程度)。
  - `diversity_vs_w16`(関数): (d) 住人の似通い(D-68): 属性(年齢 5 歳・男女・産業の語・世帯の人数・家のセル・勤め先のセル)の多様性を、W21 と
  - `double_rows`(関数): (b) 二重の数(合否なし)。``keep`` は ``w21_port10.w16_keep_table`` の返り値。
  - `read_jukiki`(関数): 東京都の外国人人口の CSV(UTF-8・見出し 1 行)→ 渋谷区の行の国・地域ごとの人数(大陸の小計・総数・男・女・前年同月の
  - `uniqueness`(関数): (c) 属性の組の重複と、文まで同じ(区別できない)組。組=年齢・性別・世帯(家族類型の区分 × 人員・外から来る人は空)・
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_sources`・`shibuya.build.pop.w21_tables`
- 呼び手: `shibuya.build.pop.w21_build_c`
- 読む試験: `tests/build_pop/test_w21_stage8_9.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: R-110・D-68

## [w21_checks.py](../../../../../../../../src/shibuya/build/pop/w21_checks.py)

W21 の計器(答申 R-116 §3-4=段 8 の先取り・**合否は付けない**)。出力 ``w21_checks.json``。

- 公開の関数とクラス
  - `blanks`(関数)
  - `counts_by`(関数)
  - `degree_summary`(関数)
  - `diversity`(関数): 属性ごとと属性の組のエントロピー(ビット)・規格化(÷ log2(区分の数))・組の種類・他の人と同じ組を持つ人の割合。
  - `entropy_bits`(関数): 区分の分布のシャノン・エントロピー(ビット)。
  - `family`(関数)
  - `fit_cells`(関数): 区分ごとの数(``sim``)と表の数(``tgt``・割合でもよい)の点検: SRMSE・JSD・最大の差の区分(割合の差)。
  - `length_summary`(関数): 長さの分布(人数・最小・10/50/90% 点・最大・平均)。0 の文(欄だけ)は除く。
  - `loglog_slope`(関数)
  - `overlap`(関数)
  - `pair_distance`(関数): 属性の組(``codes``=(人, 属性) の番号)の無作為なペアのハミング距離の分布(0〜属性の数)。ペアは Philox の鍵
  - `role_distribution`(関数): 席に座った人の地位(5 区分)の分布と、経済センサス 第6-2表(渋谷区・産業大分類)の分布(点検だけ・合否なし)。
  - `savings_class_fit`(関数): 世帯の貯蓄の階級の分布(0 円は 25 万円未満の階級へ)と東京都の世帯数分布(第31-0表)の点検(合否なし)。
  - `share_target`(関数): 属性の番号 → (組 × 区分の数え, 組の大きさ × 割合の目標)。
  - `table_fit`(関数): {表の名: (数え, 目標)} → 表ごとの点検(目標が割合の表は呼び手が数に直して渡す)。
  - `tuple_duplicates`(関数): 属性の組(``keys``=人ごとの組の語)の重複の数と、重複の中で文まで同じ=区別できない組の数(``text_group``=同じ文の
  - `uniqueness`(関数)
- import している内部モジュール: `shibuya.build.pop.fitting`・`shibuya.core.rng`
- 呼び手: `shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`・`shibuya.build.pop.w21_check`・`shibuya.build.pop.w21_org`・`shibuya.build.pop.w21_port10`
- 読む試験: `tests/build_pop/test_w21_stage4_7.py`・`tests/build_pop/test_w21_stage8_9.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: R-109・R-116

## [w21_frame.py](../../../../../../../../src/shibuya/build/pop/w21_frame.py)

W21 段 1「人数の枠」: 層 × 人数の目安を 1 行 1 出典で ``w21_frame.json`` に書く(構築側だけ)。

- 公開の関数とクラス
  - `build_frame`(関数): 枠の表(JSON の中身)。``computed:*`` の値を計算の値で置き換える。
  - `freeze`(関数): 辞書は読み取り専用の写像に・リストはタプルに(入れ子も)=表を書き換えられないようにする(検収 L3)。
  - `thaw`(関数): ``freeze`` の逆(JSON に書くため)。
- 呼び手: `shibuya.build.pop.w21_build`
- 読む試験: `tests/build_pop/test_w21_attr_fns.py`・`tests/build_pop/test_w21_build_real.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-13b/§1・R-99・R-100・R-109・R-116

## [w21_households.py](../../../../../../../../src/shibuya/build/pop/w21_households.py)

W21 段 2「世帯と人」(答申 R-116 §3-2 の手順 3〜7・標本なしの組み立て+焼きなましの詰め)。

- 公開の関数とクラス
  - `AnnealParams`(クラス): 焼きなましのパラメータ(自前の値・感度試験の前=宣言)。
  - `HouseholdDraw`(クラス): 世帯と世帯員(SoA)。``hh_*`` は世帯・``m_*`` は世帯員。``m_hh`` は世帯の行の番号。
  - `anneal`(関数): 同じ家族類型・同じ世帯人員の世帯どうしで町丁目を入れ替える焼きなまし(``hd.hh_chome`` を書き換える)。
  - `anneal_targets`(関数)
  - `anneal_vectors`(関数): 世帯ごとの誤差のベクトル(年齢 16 × 男女 32+配偶 3 × 男女 6)=世帯員の数え。
  - `assign_categories`(関数): 町丁目ごとに、``mask`` の世帯へ分類(列)を整数の数(最大剰余)で割り当てる(並びは乱数 ``u`` の順)。
  - `choose_foreign`(関数): 町丁目ごとの外国人の数へ、世帯ごとに選ぶ(重み=世帯員の「日本人でない」割合の平均・Efraimidis–Spirakis の鍵)。
  - `compose_members`(関数): 世帯の行 → 世帯員の行(世帯の順・世帯員の番号の順)と枠。
  - `draw_members`(関数): 世帯員の続き柄・男女・年齢・配偶関係を引く(世帯主 → 配偶者 → ほかの順)。
  - `feasible_other`(関数): 他の親族の続き柄(``OTHER_REL_CODES`` の順)ごとに、世帯主の年齢で窓が空にならないか((n, 5) の真偽)。
  - `household_cells`(関数): 町丁目 × 家族類型 16 × 世帯人員 7 の世帯数(整数)と実数の表。
  - `make_households`(関数): 整数の表 → 世帯の行(町丁目 → 家族類型 → 世帯人員の順・通し番号は町丁目の中の順)+施設等の人(1 人 1 世帯)。
  - `place_households`(関数): 世帯 → 建物とセル(建て方の階の区分ごとに、町丁目の住居系の建物の床面積で配る=W16#3 と同じ床面積)。
  - `windows`(関数): 世帯員の年齢の窓 [lo, hi]\(世帯主・配偶者・父母の年齢から)。−1 は「その親がいない」。
- import している内部モジュール: `shibuya.build.pop.fitting`・`shibuya.build.pop.w21_tables`・`shibuya.core.rng`
- 呼び手: `shibuya.build.pop.w21_build`
- 読む試験: `tests/build_pop/test_w21_attr_fns.py`・`tests/build_pop/test_w21_build_real.py`・`tests/build_pop/test_w21_households.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: R-116

## [w21_money.py](../../../../../../../../src/shibuya/build/pop/w21_money.py)

W21 段 5「お金」(EC2・決定 10-12 §4-11・計画 第 4 期 段 5・回答 2-2 の 1「属性から作る関数」)。版 1.1.0。

- 公開の関数とクラス
  - `build_money`(関数): 体ごとと世帯ごとのお金の列(円・空欄は −1)。``people`` は段 4 の人の表(住民+外から来て働く人)、``households`` は
  - `household_type`(関数): 段 2 の家族類型 → 全国家計構造調査の世帯の種類(1 二人以上・2 単身=単独世帯 "3" と施設等)。
  - `jicc_holder_rate`(関数): JICC の残高のある人(引)÷ 全国の 20 歳以上人口(国勢調査 2025 第2-5表【不詳補完値】の全国の行)。返り値=(率, 分母)。
  - `load_asset_tables`(関数): 全国家計構造調査 2024(東京都 第31-0・23-0 表・全国 第4-4 表)→ ``AttrTablesB`` の資産の欄(円・%)。
  - `load_wage_tables`(関数): 賃金構造 令和 7 年(第9・6・18 表と短時間 第2表)→ ``AttrTablesB`` の賃金の欄(企業規模計・円と時間)。
  - `solve_tilt`(関数): 重み base × mean^λ の平均が target になる λ(二分法・届かなければ端)。
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_sources`・`shibuya.core.wage_formula`
- 呼び手: `shibuya.build.pop.w21_build_b`
- 読む試験: `tests/build_pop/test_w21_stage4_7.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/economy/test_wage_occupation.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-12/§4-11・10-12b/§3・R-107・R-116・R-116 §1-4 #46

## [w21_org.py](../../../../../../../../src/shibuya/build/pop/w21_org.py)

W21 段 4「組織と関係」(PS5・設計書 §2-5・§2-7・計画 第 4 期 段 4)。版 1.1.0。

- 公開の関数とクラス
  - `assign_resident_workplaces`(関数): 住民の就業者の勤め先の場所(:data:`WORKPLACE_AREAS` の番号)と舞台の町丁目(舞台の中の番号・−1)。
  - `chome_employees`(関数): 経済センサス 第28表の写し → (80 町丁目の民営の従業者, 区の従業者, 当てはまらなかった末端の行の名)。
  - `class_seats`(関数): 組織ごとの席を地位 5 区分へ割合で分ける(組織ごとの最大剰余・同じ端数なら区分の番号の順)。(組織, 5) の整数。
  - `departments`(関数): 部署(SR2 の決定 (a))と上司。人ごとに(部署の番号・組織の中の順位・頭か・上司の人の番号)を返す(組織の無い人は −1)。
  - `ecen_status_shares`(関数): 経済センサス 第6-2表(渋谷区・産業大分類)→ W16 の 15 語ごとの席の地位 5 区分の割合(個人業主・無給の家族従業者・
  - `fill_seats`(関数): 業種ごとに席(組織の従業者=経済センサス)へ人を入れる。返り値=(人 → 組織の番号 −1, 組織ごとの埋まった数, 業種ごとの数)。
  - `fill_seats_by_role`(関数): 業種 × 地位の区分ごとに席へ人を入れる(席の地位=経済センサス 第6-2表・人の地位=国勢調査=段 3)。
  - `normalize_chome_name`(関数): 経済センサスの町丁目名(全角の数字・異体字)→ 小地域の境界の名(漢数字)。
  - `relation_pairs`(関数): 同じ組(世帯・部署)の人の有向の組を全部(自分を除く)。``group`` は人ごとの組の番号(−1=組なし)。
  - `role_words`(関数): 役割の語。組織の長: 店(:data:`attr_fns.STORE_INDUSTRIES`)は「店長」・ほかは役員・業主なら「代表」・それ以外は
  - `stage_worker_targets`(関数): 舞台の町丁目ごとの「そこで働く人」の数(整数)と舞台の割合 s。人数=区で働く人(国勢調査)× 町丁目の従業者 × 被覆率 ÷
  - `store_owners`(関数): 店(POI)→ 持ち主の組織の番号(−1=見つからない)。同じ建物で業種の合う組織のうち、持つ店の数が少ない順(同じなら組織の
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.fitting`・`shibuya.build.pop.w21_checks`
- 呼び手: `shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_persona`・`shibuya.build.pop.w21_port10`
- 読む試験: `tests/build_pop/test_w21_stage4_7.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: R-80・R-116

## [w21_outside.py](../../../../../../../../src/shibuya/build/pop/w21_outside.py)

W21 段 7「外の人」(計画 第 4 期 段 7・設計書 §2-1 の 3 種類のペルソナ・PENDING 仮-23)。版 1.1.0。

- 公開の関数とクラス
  - `muni_population`(関数): 国勢調査 2025 第2-5表【不詳補完値】→ (市区町村, 男女 2, 年齢 5 歳 21) の人口と、表に無い符号の一覧。
  - `origins`(関数): 第4表(従業地=渋谷区)→ 流入元の市区町村(5 桁の符号・名・15 歳以上の就業者・通学者(15 歳未満を含む)・総数)と、
  - `outside_households`(関数): 体のない遠くの人(流入元の市区町村)の世帯の層: 第10表(家族類型の区分 6 × 世帯人員 7)と第12-3表(家族類型の区分 6
  - `outside_strata`(関数): 層の表(:data:`OUTSIDE_COLUMNS`)。``org`` は :func:`origins` の返り値・``pop`` は :func:`muni_population`・
- import している内部モジュール: `shibuya.build.pop.w21_sources`・`shibuya.build.pop.w21_tables`
- 呼び手: `shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`
- 読む試験: `tests/build_pop/test_w21_stage4_7.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: R-109・R-110・R-116・R-116 §1-5 #52

## [w21_persona.py](../../../../../../../../src/shibuya/build/pop/w21_persona.py)

W21 段 9「見せ方」(PS7・4-1b の器): 体ごとの人物の説明文を**事実から決まった形で組み立てる**(LLM に書かせない)。

- 公開の関数とクラス
  - `PersonaFacts`(クラス): 人物の文の材料(事実だけ)。``cols`` は体ごとの列(:data:`FACT_COLUMNS`)・``members`` は同居人の行(``owner``=
  - `PersonaOverrideError`(クラス): 差し替えの口に、表に無い体や空の出どころを渡した。
  - `age_words`(関数): 年齢と男女 → 言葉(13 歳未満は歳を漢数字・英語の綴りで・13〜19 歳は十代の前半/後半・20 歳以上は十年ごとの前半/後半)。
  - `build_tables`(関数): 短い版と長い版の表(体 × 版 × 文・長さ)。文の無い体(欄だけ)は文が空。``tipi_*`` は空欄(腕)。
  - `compose_blocks`(関数): 描画のブロックに人物の文を足す(``engine.decision.port.compose`` に渡す形)。engine に人物の欄が無いので、個体の
  - `english_number`(関数): 0〜9,999 の整数 → 英語の綴り。
  - `facts_from_w21`(関数): 段 1〜7 の資産の表 → 事実の表(読むだけ)。``people``=``w21_people``(並びが人の並び)・``persons``=段 1〜3 の
  - `kanji_number`(関数): 0〜9,999 の整数 → 漢数字(十・百・千の位取り)。
  - `money_en`(関数): 円 → 英語のお金の語(¥・100 万円以上は million)。
  - `money_ja`(関数): 円 → 日本語のお金の語(1 万円以上は「万円」・1 億円以上も「万円」の単位=計器の語に合わせた)。
  - `naming_check`(関数): CP5-3 の補助(番号の無い名だけ=番号のある POI と組織は :func:`naming_check_ids`): 人物の文が改変した物の名
  - `naming_check_ids`(関数): CP5-3 を**番号で**見る口(検収の後の親の判断): 改変した POI の番号(``poi``)・組織の番号(``org``)を、文に名の出る
  - `override`(関数): 人物の文を外から差し替える口(4-1b の腕「LLM が書いた人物像」を刺す)。返り値は(新しい表, manifest の欄)。
  - `persona_langs`(関数): 体ごとの文の言語(``ja``・``en``・空=欄だけ)と出どころの語。
  - `place_words`(関数): W6 の POI の(cat, subcat)→(日本語, 英語)の種類の語。
  - `prefix_mismatches`(関数): 短い版が長い版の頭でない文の数(長い版の頭の字数ぶんを pyarrow で切り出して比べる=配列の計算)。
  - `relation_category`(関数): (本人の続き柄, 同居人の続き柄)(どちらも世帯主から見た語)→ 本人から見た区分(:data:`HOUSEHOLD_CATEGORIES`)。
  - `render`(関数): 事実の表 → 全員の文(``lang`` の型・``version`` の版)。同じ入力からは同じ文(決定的)。長い版は短い版の文に足す行を
  - `text_groups`(関数): 同じ文の組の番号(``np.unique`` の逆引き=区別できない組の数え・記録に文を写さない)。
  - `with_big_five`(関数): Big Five(TIPI-J)の腕: 体の番号と 5 次元の得点((m, 5)・2〜14 点=川本ほか 2015 の尺度・並びは
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_org`・`shibuya.core.time_consts`・`shibuya.engine.experiment.checks`
- 呼び手: `shibuya.build.pop.w21_build_c`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_pop/test_w21_stage8_9.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-12/§4-7

## [w21_port10.py](../../../../../../../../src/shibuya/build/pop/w21_port10.py)

W21 段 10 の材料(第 4 期 4-1・差し替えそのもの=版上げ 3 回目は別の発注)。

- 公開の関数とクラス
  - `seat_recount`(関数): 段 4 の席への所属を ``emp_status_words``(人ごとの従業上の地位の語)で数え直す(段 4 と同じ席・同じ乱数の鍵)。
  - `status_split_table`(関数): 第6-2表(渋谷区・産業大分類の行)→ (産業大分類 20, 3) の人数(:data:`attr_fns.STATUS_SPLIT_COLUMNS` の並び)。
  - `store_staff_rows`(関数): 権利台帳の「体 → 店」の雇用の行(口の約束 1-5 の 8 欄+役割・週の時間・閉じた表に入るか・注=``O.RIGHT_COLUMNS``)。
  - `w16_keep_table`(関数): W16 の在庫の行を(種別, 担当の語)の群ごとに数え、段 10 での扱いの案(残す/外す)と W21 の体の数を並べる。
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.pop.w21_checks`・`shibuya.build.pop.w21_org`・`shibuya.core.rng`
- 呼び手: `shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`
- 読む試験: `tests/build_pop/test_w21_stage8_9.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w21_prior.py](../../../../../../../../src/shibuya/build/pop/w21_prior.py)

W21 段 6「開始前の経験」(PS4・設計書 §2-5・§2-6・計画 第 4 期 段 6)。版 1.1.0。

- 公開の関数とクラス
  - `affinity_matrix`(関数): (生活の段 5 × 2(小さい子のいる世帯か), POI)の重み。
  - `commute_facts`(関数): (通勤の手段の語, 舞台の中の歩く道のり[m]・−1=空欄)。住民の舞台の中の勤め先=歩き(家 → 勤め先)・自宅=家・舞台の外で
  - `familiar_places`(関数): なじみの場所(体 × 場所 × 順位)と、人ごとの数(載せた数・舞台の外の数・引けずに足りなかった数)。
  - `life_stage`(関数)
  - `rank_shares`(関数): 順位 k の頻度の割合 k^−1.2 / Σ_{j≤L} j^−1.2(L=行ったことのある場所の数)。
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.core.rng`
- 呼び手: `shibuya.build.pop.w21_build_b`
- 読む試験: `tests/build_pop/test_w21_stage4_7.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w21_sources.py](../../../../../../../../src/shibuya/build/pop/w21_sources.py)

W21(第 4 期 4-1 段 1〜3)の材料の台帳と読み口の守り(read_guard)。

- 公開の関数とクラス
  - `Derived`(クラス): xlsx の写し(渋谷区の行)。``table[次元の値の組] = 値の配列``(地域の次元は落とす)。
  - `MissingSourceError`(クラス): 材料の表が無いか、md5 が台帳と違う。
  - `NotAllowedError`(クラス): W21 の許可の一覧に無い道筋を開こうとした(開く前に止める)。
  - `SmallArea`(クラス): 小地域の表(渋谷区の行)。``values[sex]`` は ``(町丁目, 列)`` の配列(秘匿は nan)。
  - `Source`(クラス): 材料の表 1 本(構築側)。``derived`` は xlsx の渋谷区の行の写し(JSON)。
  - `VerificationSideError`(クラス): 検証側の表(R-116 §1 の 11 行・パターン台帳 §10)を開こうとした(開く前に止める)。
  - `VerifyRow`(クラス): R-116 §1 の「検証側=使わない」の 1 行。``tokens`` は道筋に現れたら止める語(小文字で照らす)。
  - `W21Guard`(クラス): W21 の読み口(許可の一覧と検証側の語)。
  - `pt_c2_layout`(関数): c-2 の見出しの行だけを文字として読み、列の位置を決める(値の行は読まない)。
  - `read_derived`(関数): 台帳の xlsx の写しを読む(写しの md5 と、写しに書かれた元の xlsx の md5 の両方を台帳と照らす)。
  - `read_derived_merged`(関数): 同じ形の写し(男・女の別表など)を 1 つの表に合わせる(次元と項目が同じこと・鍵の重なりは不可)。
  - `read_derived_rows`(関数): 写しを地域の次元も残して読む(市区町村ごとの表=段 7)。返り値は(次元の名, 項目名, 行=[次元の値..., [値...]])。
  - `read_estat_csv`(関数): e-Stat API の CSV(``"tab_code",...`` の見出しの行から下)→ 行の辞書の並び(md5 を台帳と照らす)。
  - `read_estat_json`(関数): e-Stat API の JSON(第1表・第3表)→ ``(cat01, area) → 値``(W16 と同じ読み方)。
  - `read_pt_c2_build_side`(関数): PT 2018 c-2 から構築側の列だけを返す〔検収 L1〕。
  - `read_small_area`(関数): 小地域の CSV(cp932)から渋谷区の行を読む。``keys`` は町丁目の鍵(11 桁=市区町村 5 桁+町丁字コード)の並び。
  - `source`(関数)
  - `verify_tokens`(関数): (行, 語)の組の全部(小文字)。
- import している内部モジュール: `shibuya.build.audit.w19_freeze`
- 呼び手: `shibuya.build.pop.w21_apply`・`shibuya.build.pop.w21_attrs`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_build_c`・`shibuya.build.pop.w21_check`・`shibuya.build.pop.w21_money`・`shibuya.build.pop.w21_outside`・`shibuya.build.pop.w21_tables`
- 読む試験: `tests/build_pop/test_w21_build_real.py`・`tests/build_pop/test_w21_sources.py`・`tests/build_pop/test_w21_stage4_7.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/economy/test_wage_occupation.py`・`tests/tools/test_seal_split_337.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-12b/§3・10-13b/§1・R-57・R-107・R-116・R-116 #38

## [w21_tables.py](../../../../../../../../src/shibuya/build/pop/w21_tables.py)

W21 の表の組み立て(段 2 の手順 1・2=区の雛形と町丁目への配分)。

- 公開の関数とクラス
  - `ChomeTables`(クラス): 町丁目(80)の 2020 の表。不詳は割り振り済み。``unknown`` は割り振った人数・世帯数(町丁目ごと)。
  - `Targets`(クラス): 舞台の目標(町丁目は被覆率 > 0 の分だけ・実数)。
  - `Ward2025`(クラス): 区の雛形(2025)と、町丁目の不詳を割り振る比(2020 の補完値 − 原数値)。
  - `age_class`(関数): 各歳 → 階級(``edges`` の下端・最後の階級は上が開いている)。下端より若い年齢は −1。
  - `expand_single_year`(関数): 階級の値(…, n_cls)→ 各歳(…, N_AGE)。階級の中は ``shape``(N_AGE)の比で配る(形が 0 の階級は一様)。
  - `fill_unknown`(関数): 年齢・配偶関係・家族類型の不詳を区の比(2020 の補完値 − 原数値)で割り振った表を返す。
  - `load_chome`(関数): 町丁目の表を読み、年齢・配偶関係・家族類型の不詳は**まだ割り振らない**(区の比が要るので 2 段で)。
  - `load_ward`(関数): 区の雛形(2025)と不詳を割り振る比。``raw_*`` は町丁目の表の区の行(2020 の原数値・既知の分類)。
  - `make_targets`(関数): 2020 の町丁目の形 × 2025 の区の総数 → 舞台の目標。
  - `rake_chome_to_ward`(関数): 町丁目 × 分類(2020 の形)を、行=町丁目の総数・列=区の分類ごとの総数(和は行に合わせる)へ IPF で合わせる。
- import している内部モジュール: `shibuya.build.pop.fitting`・`shibuya.build.pop.w16_population`・`shibuya.build.pop.w21_sources`
- 呼び手: `shibuya.build.pop.w21_attrs`・`shibuya.build.pop.w21_build`・`shibuya.build.pop.w21_build_b`・`shibuya.build.pop.w21_check`・`shibuya.build.pop.w21_households`・`shibuya.build.pop.w21_outside`
- 読む試験: `tests/build_pop/test_w21_attr_fns.py`・`tests/build_pop/test_w21_households.py`・`tests/build_pop/test_w21_stage8_9.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: R-116
