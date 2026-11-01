# 段 2 の 5 最低賃金を human へ(つなぎの床と違反の記録の器)の独立検収

- 検収役 Opus 5.5(実装を見ていない)。作業木の枝 `stage/s2rules-1101`・土台 `c0729a4`。読んだもの: 差分の全部・記録
  README・発注の正(指示書 11-01 段 2 の 5・回答 11-01 §5・A1 の調べ §6 #4 と論点 5・R-118 §2)。
- 書いたのは本書だけ(commit・add なし・ネットワークなし・子サブなし)。自分の対照の生の出力とスクリプトは git の外の作業用の
  場所に置いた。本書に絶対パスは書かない。

## 0. 判定

**条件つき受入**。高 0・中 2・低 6。

- コードの挙動は自己申告どおりで、既定の結果は 1 バイト不変。自分で回した 2 日と 3 日のランで、前と後の manifest の差は
  `rules_version` と、新しい器の鍵と、環境の欄(commit・diff の sha・env_id)だけだった。
- 条件は 2 つの中(§2 M1・M2)の扱いを親が決めること。M1 は表の形の約束、M2 は記録の証拠の書き方で、どちらもコードの
  挙動の欠陥ではない。

## 1. 範囲と差分(やること 1)

- 変えたファイル: `docs/design/rules-table.json`・`src/shibuya/economy/{anchors,stage2,wages}.py`・`tests/engine/rules/` の 2 本。
  新しいファイル: `tests/economy/test_min_wage_human_bridge.py`・記録 `docs/bench/analysis/s2-rules-1101/`(README と tools 2 本)。
  `engine/`・`world/processes`・`bridging-ledger.json` は触っていない=規律の中。tools の `__pycache__` は gitignore に当たる。
- 規則の表を id と asof ごとに JSON で比べた: 30 行の並びと表の外の欄は同じ。違うのは `minimum_wage.tokyo` の 3 版だけで、
  欄は `kind`(machine → human)・`params`(`bridge` を除くと同じ=`yen_per_hour`・`area` は不変)・`note`(前の文の
  「=機械が守らせる側」を「=R-106 の振り分けでは機械が守らせる側」に変え、末尾に 1 文を足しただけ)。
- 変えた .py と記録の tools は全部 LF。絶対パスは無い(URL を除く)。
- 識別子の `open`/`tick`(AST): 新しく足した名前・属性・引数・器の鍵(`minimum_wage_shortfall`・`paydays`・`checked`・
  `below_*`・`lifted_*`・`violation_*`・`last` の下の 7 鍵)のどれにも無い。ファイルに元からある `tick`・
  `worst_case_ops_per_tick`・`CONSUMPTION_PROPENSITY` は差分の外。

## 2. 欠陥

### 中

**M1 表の中に「human の行の machine のつなぎ」の書き方が 2 通りある。** 前からの `consumption_tax.filing_deadline`
(human)は、機械のつなぎを note とつなぎの台帳 `DOC-rules42-tax-remit-machine` と `economy.taxes.BRIDGE_READ_RULES` で
持ち、`params.bridge` は無い。今回の `minimum_wage.tokyo` は `params.bridge` で持つ。しかも新しい試験
`test_the_repo_rows_are_human_with_a_machine_bridge` の `all(AN.rule_bridge(r) is None for r in others)` が、filing_deadline
に構造化したつなぎが無いことを固定している。表だけを読んでも「どの human の行が機械で代わりに動いているか」を一様に
拾えない。
- 再現: `rules-table.json` の filing_deadline の行の note と `taxes.py` の `_bridge_row` を読む。
- 直し方の案: (a) filing_deadline にも `params.bridge` を足し、試験の「ほかの行につなぎ無し」を「つなぎのある行の一覧」に
  直す(表の sha だけが動く) (b) 書き方を 1 つに決めるまで記録に 2 通りあることを書く。どちらにするかは親が決める
  (README の問い 2「行の欄に上げるか」と一緒に)。

**M2 記録が 1 バイト不変の証拠に挙げた `final_hash`・`state_hashes` は、この 2 日のランでは賃金の違いを見分けない。**
開始 2026-08-24 の 2 日のランでは、給料日は最後の日の締め(2026-08-25)で、manifest の `final_hash` と `state_hashes` は
その締めより前に取られる。自分の対照で、つなぎを外した表(賃金が 4,776,962 円少ない)でも `final_hash` 64cce6fd… と
`state_hashes` は全部同じだった(§3 (c))。README §0・§4 の「`final_hash`・`state_hashes` が同じ」は事実だが、賃金の
不変の証拠にはならない。証拠になるのは、README が一緒に挙げた流れの表の sha・保存則・賃金の計器と、日次の記録の
`daily[1].state_hashes_end_of_day`(つなぎを外すと変わる=見分ける)。
- 自分で 3 日のラン(給料日が途中に入る)を回し、前と後の `final_hash` a4e040d1… が同じで、つなぎを外すと 40c2b089… に
  変わることを確かめた。挙動の欠陥ではないので、直すのは記録の文(証拠の欄を日の締めの hash か 3 日のランにする)だけ。

### 低

- **L1 つなぎの欄の検査が、給料日に効いている版だけに掛かる。** `rule_bridge` を呼ぶのは `min_wage_terms` だけ(組み立て
  の点検 `_floor_record` で始めの日の版・給料日にその日の版)。後の版(例: 2026-10-01 の版)の `params.bridge` が壊れて
  いても、ランの始めでは落ちず、その版の最初の給料日の締めで `ValueError` で落ちる。前からの約束「壊れていればランの
  始めに落ちる」(`engine/systems/build.py` の検収 L10)とずれる。リポの表の 3 版は新しい試験が全部検査するので、いまの
  実害は無い。直し方の案: `MoneyStage2` の組み立てで `versions(MIN_WAGE_RULE_ID)` の全部に `rule_bridge` を掛ける。
- **L2 2-1 の道(賃金の表の無い写し)では、器の `last.enforced_by` が `bridge` になるのに床は当たらない。** 2-1 の道は
  前から床の式が無く、時給 `plan.hourly` が最低賃金より低いと `violation_*` が立つ(試験
  `test_the_hours_times_hourly_path_counts_but_has_no_floor` の 2 つ目)。そのとき `last.enforced_by="bridge"`・
  `violation_rows=3` が並び、`_count_min_wage_shortfall` の docstring「violation_* はつなぎの床がある間は 0」と食い違う。
  既定(data あり=occupation の道)と、data の無い CI の既定の時給では起きない。直し方の案: 2-1 の道では `last` に
  `enforced_by="none"` か `floor_applied: false` を書くか、docstring に「occupation の道だけ」と書く。
- **L3 再開(`--resume-from`)で器が 0 から数え直すことは、README §8 と状態台帳の EM 行の注にはあるが、器そのものには
  書いていない。** 再開したランの manifest の `paydays`・`below_*` は再開の後の分だけで、読み手は気づけない。直し方の案:
  `_empty_shortfall` の docstring に書くか、器に `scope`(例 `since_run_start`)の欄を 1 つ足す(観測の節なので
  CONFIG_PATHS_SHA256 は動かない)。
- **L4 つなぎの無い表では、組み立ての点検 `wage_build.floor_at_start` が「床に当たる体 0」と出る。** `_floor_record` は
  `min_wage_floor`(None)を使うので、つなぎを外した腕では、始めの日に何体が最低賃金を下回るかが記録から消える(器は
  給料日だけを数える)。腕を外すのは試験か将来の段だけなので低。直し方の案: `_floor_record` も `terms.yen_per_hour` で
  下回りを数える。
- **L5 端の値の扱い(前からの `apply_floor` を引き継ぐ・新しい欠陥ではない)。** 0 円で時間のある体は「下回り」に数えて床まで
  上げる。負の値の体と時間の無い体(NaN・0)は飛ばす。小数の月の賃金は int64 への型の変換で切り捨てる。自分の試験で
  確かめた(§3 (b))。0 円の体が「値の無い体」の印でないかは、構築の側で確かめる価値がある。
- **L6 訂正の伝播(本段で触ってよいファイルの外)。** 「最低賃金の床=machine」と読める文が R-118 の 3 か所(冒頭の要旨の
  2・最低賃金の行の表・判定の基準 2「法の効果が自動で起こるか → machine」)と、決定台帳 D-R2-3 の「行 6=最低賃金
  1,226 円フロア(mechanism)」に残る。D-R2-3 は床を mechanism と呼び、今回のつなぎは `conf: expedient` なので、conf の
  付け替えも決定として残す必要がある(問い 4)。

## 3. 自分の対照(やること 3)

計器は自分で書いた(README の `measure_shortfall.py` と同じ入口 `cli.run`・seed 1・世界資産・開始 2026-08-24・1,000 体・
既定の LLM の呼び口(mock・呼数 24,788)。manifest の全部と流れの表の sha と計器の sha を JSON に出して欄ごとに比べた)。
「前」は本体の作業木の src(土台 `c0729a4` と src と表が同じことを `git diff` で確かめた)、「後」は作業木の src。

**(a) 1 バイト不変**

| ラン | 前 `final_hash` | 後 `final_hash` | 流れの表の sha | 計器 `s2_meter.run` の sha | manifest の差(前 → 後) |
|---|---|---|---|---|---|
| 2 日 | 64cce6fd… | 64cce6fd… | b7dfa80b7448bb3e(同じ) | 1df7e372e4f19097(同じ) | `rules_version`(manifest と日次 2 行)・器の鍵・環境の欄 3 つ |
| 3 日 | a4e040d1… | a4e040d1… | 2092bb1216d63a9e(同じ) | 375b296cc44503be(同じ) | `rules_version`(manifest と日次 3 行)・器の鍵・環境の欄 3 つ |

- `state_hashes`(behavior・full・外のバイト数)・日次の `state_hashes_end_of_day`・保存則・`wage_model.floor`
  (raised 93・4,776,962 円)・`floor_at_start` も同じ。`rules_version` は `1490c5a2fdc8beb4` → `a07cb53eb82d29f8`
  (README と同じ)。
- 器(後): `checked` 614・`below_rows` 93・`below_amount` 4,776,962・`lifted` 同じ・`violation` 0・`last.enforced_by`
  `bridge`=README §4 の 1,000 体の行と同じ。5,000 体は回していない(README の 5,000 体の数は確かめていない)。

**(b) 正の対照(試験の外に自分で 7 本書いて回した=7 passed)**: 版の境(2024-09-30 は版なし・2024-10-01/2025-10-02 は
1,163・2025-10-03/2026-09-30 は 1,226・2026-10-01 は 1,280・つなぎ)・端の値(0 円・負・境の ±1 円・NaN と 0 時間・小数・
空の配列)・給料日の道で版の切り替わりの両側(2026-09-30 は 1,226 円・2026-10-01 は 1,280 円)に下回りが立ち、つなぎが
上げて違反 0・作業用の場所に写した「つなぎを外した表」で給料日に違反が立つ(`violation_*`=`below_*`>0・床なしで払う・
保存則 ok)・つなぎの台帳の道具を台帳の写しに 2 回回して同じバイト・`ledger.load` が読める・`code_mismatch` が空・
`declared_in` と `code_at` のファイルがある・前の行は不変で末尾に 1 行だけ足す・CR なし。

**(c) つなぎを外した表(作業用の場所の写し・3 版の `params.bridge` を消しただけ)**

| ラン | `final_hash` | 賃金の額(計器) | 器 | 保存則 |
|---|---|---|---|---|
| 2 日 | 64cce6fd…(つなぎありと同じ=M2) | 196,716,435(つなぎあり 201,493,397 との差 4,776,962) | below 93・lifted 0・violation 93・4,776,962 円・`enforced_by` none | ok |
| 3 日 | 40c2b089…(変わる) | 同じ差 | 同じ | 3 日とも residual 0 |

床は掛からず、下回ったまま払い、違反が数えられる。`wage_model.floor.source` は `human:rules:minimum_wage.tokyo@2025-10-03`。

**(d) 識別子の `open`/`tick`**: §1 のとおり無い。**(e) manifest の絶対パス**: 2 日のランの manifest の全文に、ドライブ名の
パス・ユーザー名・作業木の名は無い。

## 4. 試験(やること 2)

- `tests/economy tests/engine/rules tests/build_pop`(`--ignore=tests/c7`・`-n 8 --dist loadfile`・slow を含む・
  `PYTHONPATH` は作業木の src)= **697 本 全部通った**(失敗 0・data が無くて飛ばした 0)。
- `tests/engine/test_geometry_c9.py` と `tests/engine/bridging`(機械の負荷が軽いとき)= **75 本 全部通った**(300 ms の
  性能の門を含む)。bridging は、anchors の docstring の段落が expedient の宣言の走査に当たらないかを見るために足した。
- 新しい試験 `tests/economy/test_min_wage_human_bridge.py` は 18 本(自己申告どおり)。

## 5. 自己申告との差

- 食い違いは無い。表の行・器の鍵・数(1,000 体)・試験の本数・LF・`engine/` を触らないことは申告どおり。
- 申告に無かった点: M1(表の中の 2 通りの書き方)・M2(挙げた hash がこのランでは賃金を見分けない)・L1〜L5。
- 法定労働時間につなぎを付けない判断は妥当と見た。`labor.statutory_hours` は前から human で、機械が止める側は src に
  無い(`calendar3.labor_params` は `enforced: False`。`build/pop` の `weekly_hours` は統計の目安で上限で切らない)。超えた数は
  カレンダー 3 と持ち場の層が前から数える。
- `conf: expedient` は妥当と見た。リポのつなぎの台帳の語(`CONFS`)と合う。ただし発注文の例(0.5)や A1 の調べの
  #21・#23(conf 0.6・0.5)のような数の conf もリポにあり、語がそろっていない(問い 3)。

## 6. 問い

1. M1: human の行の machine のつなぎの書き方を 1 つにするか(filing_deadline にも `params.bridge` を足すか、行の欄に
   上げて表の形式の版を 3 にするか=README の問い 2)。
2. M2: 記録の 1 バイト不変の証拠を、日の締めの hash か 3 日のランに直すか(本書 §3 の 3 日の数を写してよい)。
3. conf の語: 規則の表のつなぎは `expedient`/`mechanism` の語、エンジンの代打は数(0.5・0.6)。表の側を語にそろえる
   ことで決めてよいか。
4. L6: R-118 の 3 か所と D-R2-3(床=mechanism → つなぎ=expedient)への訂正の伝播をいつ誰がするか。
5. 同じ基準「現実でその場で物理的に止まるか」を、残りの machine の行にも当てるか。たとえば `labor.overtime_premium`
   (割増の不払いは現実で起きる=最低賃金と同じ型)・`credit.interest_cap`。発注は最低賃金と法定労働時間だけなので、
   本段の外。
