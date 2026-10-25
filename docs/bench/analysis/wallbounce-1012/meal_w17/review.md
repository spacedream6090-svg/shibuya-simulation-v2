# 第 18-1 表の置き換え(meal_w17)の検収の記録

検収役(実装は見ていない)。対象: 作業木の枝 `vu/meal-default-from-w17`(土台 `32fb262`・commit の無い変更 22 ファイル+新規 3)。
正: 回答 10-13b §7 の 2・§0-6・§0-7・実装役への発注文・実装役の記録 [README.md](README.md)。

**検証側の錨のファイル(`hunger_energy_validation_anchors_v0.json`)は開いていない**。旧値の腕のランでエンジンがそのファイルを開くのは
エンジンの読みで、検収役は値を画面に出していない(B の分解のランは旧値の腕の既定の時刻を構築側の値で上書きした)。封印の層・
`tests/c7` は触っていない。

## 判定

**条件つき受入**(高 0・中 2・低 9)。挙動の本体(分布の出どころ・引き・初期の空腹・検証側を読まない・旧値の再現・性能)は
検収役の独立の再計算とすべて一致した。中の 2 件は、旧値の再現と byte-check の物証を試験と記録に残す直し。

## 1〜8 の確認

| # | 項 | 判定 | 根拠 |
|---|---|---|---|
| 1 | 結果不変(旧値の腕) | ✓ | 実装役の 19 構成の JSON(写し対作業木の validation): 19/19 構成・25 欄すべて同じ。検収役の 4 構成(下の表)も土台の写しと作業木の validation で 25 欄同じ。検収役の side の 12 行は実装役の side の同じ行と 25 欄すべて同じ |
| 2 | 口と約束 | ✓(△ 1) | `--meal-default {w17,validation}`(既定 None=環境変数 `SHIBUYA_MEAL_DEFAULT`・既定 w17)・`load_anchors(mode=)`・`anchors_paths`・`MealStartDistribution.from_weekly/frozen/draw`・`OutOfAreaMeals(seed=, distribution=)`・`EnergyLayer.initial_dinner_min`・manifest `energy.meal_default`・`meal_default_source`・`meal_default_use`。△: 旧値の再現を守る pytest が無い(中 M1) |
| 3 | 発注の各項 | 1 ✓・2 ✓・3 ✓(印は計器だけ・5a の report は範囲外と申告)・4 ✓・5 △(M1)・6 ✓ | 「できなかったこと」(5a の report に印を写していない・状態の漏れ)は実態と合う |
| 4 | 守り | ✓(△ 低 L2) | 書く口: 体ごとの既定の時刻は `OutOfAreaMeals.__init__` の 1 か所・`ate_default` は `EnergyLayer` の食事の 1 行(O28 の `energy.*` の宣言の中)。負の対照: 実装役の試験 2 本+検収役が AST と実データのランの両方で植えた(下)。凍結の表は普通の dict で書き換えられる(L2) |
| 5 | 宣言と凍結 | ✓ | 状態台帳 O28 に `energy.ate_default`(diag・discardable)・除外の表に範囲外の予定の 6 属性。`writes.paths` は `O28:energy.*` の glob で覆われる。凍結の表は増えた分だけ(`SAFE_SITES` +1=17・`POPULATION_RNG_DOMAINS` +1・つなぎの台帳 +4・`CONFIG_PATHS_SHA256` は 2 本を足した分)。manifest の既存の欄: 合成の世界の 1 日で、土台の写しと作業木の validation の energy の節を欄ごとの sha で比べ、既存の 32 欄すべて同じ・足したのは 3 欄だけ |
| 6 | 同値 | ✓ | 下の「独立の再計算」の (b) の分解=既定 w17 の道と旧値の道は、時刻と初期の空腹を同じ値にすれば final まで一致 |
| 7 | 試験 | ✓(前からの失敗 1・状態の漏れ 1) | 範囲の試験 3,017 passed・2 failed・1 skipped(下)。lint-imports 5 kept・0 broken |
| 8 | 抜け道と記録 | ✓(△ 中 M2・低) | (a)〜(f) は下。記録に絶対パス・ホスト名は無い。触った共有ファイルの一覧は `git diff --stat` の 22 本と一致 |

## 自分の byte-check(4 構成・mock 5,000 体・seed 1・1 日・1 本ずつ)

土台 `32fb262` の写し(`git archive` で src と `HEAD_TREE_FILES` の追跡ファイル+data へのつなぎ)対作業木。

| 構成 | 土台の写し final / 呼数 | 作業木 validation | 25 欄 | 作業木 w17(既定) | 実装役の w17 と |
|---|---|---|---|---|---|
| w6_v3_default | b8eadcb51e8705e7 / 64,528 | 同じ | 同じ | 333b1820f7849b00 / 64,024 | 25 欄同じ |
| w6_v3_activity_off | c88ba9104f45f897 / 50,006 | 同じ | 同じ | fe3f46d90e1203f1 / 48,898 | 25 欄同じ |
| w6_v1_default | e1288e092ddaca86 / 51,655 | 同じ | 同じ | 210318331d8bb5dc / 49,787 | 25 欄同じ |
| v3_mem_rel | 768b2262e3b0999e / 67,794 | 同じ | 同じ | bf212900153818d2 / 66,844 | 25 欄同じ |

w17 で動いた欄は実装役の表と同じ(final・呼数・テープ・行動の件数・checkpoint の 2 本・日の締め・通報の遅れ・気づき・食事)。
起床の条件ごとの呼数の差(w17 − 土台): w6_v3_default は内受容 −522・セルの区画 +163・会話 −92。w6_v1_default は内受容 −1,126・
セルの区画 −744。気づきは 181 → 578(w6_v3_default)・804 → 771・620 → 473・486 → 557=向きがそろわない。

## 独立の再計算(自分の値と実装役の値の対)

方法: W17 の parquet を pyarrow で直に読み(実装役の `MealStartDistribution`・`OutOfAreaMeals` は使わない)、月曜 d0・活動語「食事」
(索引 6)・窓(朝 300〜659・昼 660〜959・夕 1020〜1439 分)で数えた。体ごとの引きは `core.rng` の原始関数
(`philox_array`・`k19_counter_array`・`unit_float`)だけを使い、分位は自分で並べた値の ⌊u·N⌋ 番目で取った。

| 量 | 自分 | 実装役 | 一致 |
|---|---|---|---|
| W17 の sha256 | 361801d2…317908 | `W17V2_FROZEN_SOURCE` と同じ | ✓ |
| 体の数 | 390,067 | 390,067 | ✓ |
| 食事の行 朝 / 昼 / 夕 | 10,972 / 109,189 / 168,967 | 同じ | ✓ |
| 朝の分位 p5/p25/p50/p75/p95 | 360/420/450/540/644 | 同じ | ✓ |
| 昼の分位 | 689/720/739/764/870 | 同じ | ✓ |
| 夕の分位 | 1028/1080/1140/1200/1320 | 同じ | ✓ |
| 15 分の度数(3 窓) | 72 区間すべて | `W17V2_MEAL_START_HIST_15MIN` と同じ | ✓ |
| 朝の行を持つ体 | 10,886 体=2.79% | 2.8% | ✓ |
| 引いた時刻と W17 の分布の JSD(1 分刻み・39 万体・seed 1) | 朝 0.000135・昼 0.000165・夕 0.000227 bit | 試験の閾値 朝 < 0.02・昼と夕 < 0.005 | ✓ |
| 39 万体 どれかの窓が既定 | 389,996(99.98%) | 389,996(99.98%) | ✓ |
| 39 万体 3 つとも既定 | 127,658(32.7%) | 127,658(32.7%) | ✓ |
| 39 万体 窓ごとの既定 朝/昼/夕 | 97.21/72.40/57.81% | 97.2/72.4/57.8% | ✓ |
| 初期の空腹の段(39 万体・seed 1) 満腹/ふつう/空腹/とても空腹 | 4.98/69.31/25.71/0% | 5.0/69.3/25.7% | ✓ |
| 前夜の夕食に自分の行を使う体 | 42.19% | 42.2% | ✓ |
| 5,000 体 どれかの窓が既定(ランの `restrict_to` に渡った体の id から parquet で数え直し) | 4,999(99.98%) | 4,999 | ✓ |
| 5,000 体 3 つとも既定 | 1,767(35.3%) | 1,767 | ✓ |
| 5,000 体 窓ごと 朝/昼/夕 | 97.86/76.08/57.36% | 97.9/76.1/57.4% | ✓ |
| 5,000 体 計画の無い体 | 0 | 0 | ✓ |
| 範囲外で既定の時刻に食べた体・回数 w17 | 3,816(76.32%)・5,978 回 | 3,816・5,978 | ✓ |
| 同 validation | 4,054(81.08%)・6,379 回 | 4,054・6,379 | ✓ |

初期の空腹の段は EER に依らない(比 since/(eer/3)=3(1440 − 前夜の夕食の分)/1440)ので、前夜の夕食の分だけから段を決めた。

### (a) 検証側の錨を開かない

- 実データのラン(5,000 体・w6_v3_default)を open の監査フックつきで回し、開いた錨の名を数えた: w17=構築側 1 本だけ(検証側 0 回・
  在圏の検証側 0 回)。validation=検証側を 1 回開く(フックが働いている確かめ)。**負の対照**: w17 の腕に `anchors_paths` が 2 本を
  返す行を植えると、検証側を 1 回開いたのをフックが見つけた。植えても final は 333b1820f7849b00 のまま=結果では見分けられず、
  フックだけが見つける。
- AST: src の全ファイルで検証側の空腹の錨の名・文字列・`ANCHORS_VALIDATION_PATH`/`ANCHORS_PATHS`/`ANCHORS_REL` の参照は
  `engine/energy.py` と `build/pop/w21_sources.py`(封印の語の一覧)だけ。`anchors_paths` は「validation のときだけ 2 本・ほかは構築側
  1 本」の形、`load_anchors` は 2 本の名を直に読まない=合格。**負の対照**: 一時の写しの `anchors_paths` を「いつも 2 本」に
  書き換えると AST の検査が落ちた。

### (b) 旧値の再現と差の由来(w6_v3_default・5,000 体)

共通の定数 c(凍結の表の中央値=朝 452・昼 739・夕 1143=構築側の値)を両方の道に入れた。

| ケース | 道 | 既定の時刻 | 前夜の夕食 | final | 呼数 |
|---|---|---|---|---|---|
| W | w17 | 体ごとに引く | 体ごと | 333b1820f7849b00 | 64,024 |
| A | w17 | 全員 c | 全員 c の夕 | 7703cedd510452db | 64,407 |
| B | validation | 全員 c(旧の値を上書き) | 全員 c の夕 | 7703cedd510452db | 64,407 |
| C | w17 | 体ごとに引く | 全員 c の夕 | f23b89833c685b58 | 64,111 |
| D | w17 | 全員 c | 体ごと | d8724f3b56a08b4c | 64,579 |

A=B: 新しい道と旧の道は、時刻と初期の空腹の値を同じにすれば final まで一致する=差は**食事の時刻と初期の空腹の値だけ**から
来る(ほかの系への別の経路・乱数の流れのずれは無い)。C と D で両方が効いている(呼数の動きは時刻のばらけが大きい)。

### (e) 性能(§0-7・5,000 体・1 日・seed 1・w6_v3_default・別のプロセスで交互に 2 回・機械は他の作業木と並走)

| 腕 | 回 | final | 実行時間[s] | 1 刻み[ms] | 最大 RSS(作業集合)[MiB] | 判断モデル | LLM |
|---|---|---|---|---|---|---|---|
| validation | 1 | b8eadcb51e8705e7 | 40.81 | 28.34 | 493.3 | 0 | 64,528 |
| w17 | 1 | 333b1820f7849b00 | 40.44 | 28.08 | 488.5 | 0 | 64,024 |
| validation | 2 | b8eadcb51e8705e7 | 40.91 | 28.41 | 482.9 | 0 | 64,528 |
| w17 | 2 | 333b1820f7849b00 | 41.16 | 28.58 | 466.3 | 0 | 64,024 |

記録の表(31.1〜35.0 ms・468〜490 MiB)と同じ向き=悪くなっていない。壁時計の絶対値は機械の混み具合で違う。

### (f) つなぎの行と無効の印・再開

- つなぎの台帳 +4 行(467 → 471)。外す段: `BR-MEAL-DEFAULT-W17`・`-FROZEN`・`-INITIAL-HUNGER`=6-6(計画の表の
  「① 人の選択を判断モデルへ」)・`-VALIDATION-ARM`=4-3。§0-6 の「次の版上げで消す」は宣言されている。4-3 は計画では
  「版上げ 3 回目: 母集団が動く」で、記録の「切替口の整理」という呼び名は計画に無い(L6)。
- 無効の印: `anchor_gauge.meal_time_validation_mark` は腕の欄と record の段で開いた錨の名だけで決め、第 18-1 表とは比べない。
  欄の無い前の版と validation は「無効」、w17 で検証側を開いていなければ「検証可」、w17 でも開いていれば無効(負の対照の試験あり)。
  5a の report(第 18-1 表と比べる道具)には印が写っていない=親の判断の材料。
- 再開=通し: 試験 `test_two_day_run_resume_equals_straight`(合成 80 体 2 日 × 両方の腕)と
  `test_world_two_day_resume_equals_straight`(世界 300 体 2 日 × 両方の腕)が範囲の試験の中で通った。腕の違う再開は設定の指紋で止まる。

### (g) 状態の漏れ(本段の外・事実の確認)

事実。`docs/bench/analysis/wallbounce-1012/md23/tools/multiday_md23.py` の `set_arms("default")` は
`PX.set_arm(arms.get("proximity", "cell"))`・`ES2.set_arm(arms.get("economy_stage2", "off"))` で、今の既定(distance・on)ではなく
2-4 V2・V4 の前の既定に戻す。`tests/engine/multiday/test_md23_tool.py::test_the_tool_collects_three_synthetic_days`(data 不要)は
最後に `md.set_arms("default")` を呼び、戻さない。

最小の再現(作業木の根・`PYTHONPATH` に作業木の src・1 つのプロセス):

```
python -c "from tests.engine.multiday._md import tool; from shibuya.engine import proximity as PX, economy_stage2 as ES2; tool().set_arms('default'); print(PX.arm(), ES2.arm())"
# → cell off(既定は distance on)
python -m pytest -q -p no:cacheprovider -o addopts="" -p no:xdist tests/engine/multiday/test_md23_tool.py::test_the_tool_collects_three_synthetic_days tests/engine/test_classical_social.py::test_run_golden_and_arms
# → 1 failed(final ed6d1832…・呼数 24,877 は同じ)。test_run_golden_and_arms を単独で回すと 1 passed
```

範囲の試験(`-n 2 --dist loadfile`)で落ちた `test_classical_social::test_run_golden_and_arms` の値も同じ `ed6d1832…` だった=この漏れ。
道具と試験は土台と本体 `2eee9b2` で変わっていない=前からある(本体の commit の注「test_classical_social の golden=並列の順序依存の
疑い」と同じ形)。直し方の案: `set_arms` を「前の腕を控えて戻す」文脈にする(`tests/engine/multiday/_md.py` の `arms()` と同じ形)、
または既定を各モジュールの `DEFAULT_*` から取る。

### (h) rebase の見込み(本体 `2eee9b2` との差)

本体で動いたのは共有の 9 本(`systems/build.py`・`cli.py`・`state_ledger.py`・`manifest_sections.py`・`run.py`・つなぎの台帳・
`test_bridging_ledger`・`test_env_and_sections_10f`・`test_state_ledger_10b`)。`energy.py`・`body/rules.py`・`rng_audit.py`・
`anchor_gauge.py` と golden の試験の多くは本体で動いていない。一時の写しで `git merge-file`(本体=ours・土台=base・作業木=theirs)を
回した結果:

| ファイル | 衝突 | 中身 | 解き方 |
|---|---|---|---|
| `cli.py`・`manifest_sections.py`・`run.py`・`state_ledger.py`・`test_state_ledger_10b.py` | 0 | — | そのまま |
| `systems/build.py` | 1 | 設定の指紋の同じ場所に カレンダー 1b の段落と meal_default の段落 | 両方を残す |
| `bridging-ledger.json` | 1 | 末尾の追記どうし | 本体の 507 行の後に 4 行=511 行 |
| `test_bridging_ledger.py` | 1 | 第 2 形の数 236(本体)と 224(作業木) | 236+4=240 |
| `test_env_and_sections_10f.py` | 1 | `CONFIG_PATHS_SHA256` | どちらでもない新しい値(カレンダー 1b の 12 本+meal の 2 本)を計算し直す |

ほか: 本体の `test_state_ledger_10b` の腕の行の一覧(C1B・C1BM)と作業木の golden の張り替え(CUR_SYN・T7)は別の行=衝突しない。
本体で足された `tests/engine/calendar/test_ca1b_*` は再開=通しの比べで、既定の golden を持たない(読んだ範囲)=w17 で
動くのは腕 1b のランの値だけと見込む。rebase の後に byte-check 19 構成(validation=本体と同じ・w17=差の表と同じ)を取り直すこと。

## 欠陥

### 中

- **M1 旧値の再現を守る試験が無い**(`tests/engine/test_state_checks_10f.py:39` の `_K19_PRE_MEAL_W17`・
  `tests/engine/test_state_ledger_10b.py:57` の `_T7_V3_FINAL_PRE_MEAL_W17` は置いたが使っていない)。発注の受入の試験
  「切替口 validation で旧値」が byte-check(記録)だけで、腕を消すまでの間に旧値の腕が壊れても試験は気づかない。
  直し方: 世界資産の 1 本(w6_v3_default・5,000 体・`--meal-default validation`)で final と呼数がその定数と同じことを見る
  試験を 1 本足す(約 45 s)。
- **M2 byte-check の物証が記録に無い**。19 構成の side と compare の JSON は作業用の置き場(commit されない)にだけあり、
  記録の置き場に無い。しかも土台の版の `byte_check_10e.py` の `SWITCH_ENV` に `SHIBUYA_MEAL_DEFAULT` が無いので、validation の
  side の JSON の `env` は `{}`=どの腕で回したかが JSON から分からない(本体 `2eee9b2` の版には足してある)。直し方: compare の
  JSON 2 本(head 対 validation・head 対 w17)を記録の置き場に写し、rebase の後の版の道具で取り直す(env に腕が残る)。

### 低

- **L1** `src/shibuya/engine/energy.py:848` の `OutOfAreaMeals` の docstring が「既定の時刻(朝・昼・夕の 1 つずつの値)」のまま=
  w17 の挙動と食い違い、検証側の表の値がエンジンの docstring に残る。体ごとの引きの説明に書き換え、値を消す。
  (前からある試験 `tests/engine/test_meal_bundle_2b.py:30` の定数も同じ値を持つ=旧値の腕の試験なので残してよいが、注で示す)
- **L2** 凍結の表 `W17V2_MEAL_START_HIST_15MIN`・`W17V2_FROZEN_SOURCE` は普通の dict、`MealStartDistribution` の配列は書き込める
  (1-3 の教訓=表は `MappingProxyType`・配列は `writeable=False`)。data の無い CI では凍結の表の中身を確かめる試験が無い
  (世界の W17 との一致は data つきだけ)=表の sha を試験に固定する。
- **L3** `test_two_day_w17_moves_the_result_and_validation_does_not_depend_on_the_draw` は 1 日で `w17 != validation` だけを見る=
  名前の「2 日」「引きに依らない」を確かめていない。名前を直すか、seed を変えても validation の既定の時刻が同じことを足す。
- **L4** w17 の manifest の `energy.default_meal_min` は凍結の表の中央値(世界の W17 のランでも)で、どの体にも使われない代表値。
  欄の意味が変わった=注を欄の隣(`initial_since_meal` のように文字で)か記録に書く。
- **L5** `energy.ate_default`(O28・diag・discardable)は日の締めで 0 に戻らず状態のファイルにも入らない=日の途中の再開の後の
  `meal_default_use.ate` は再開の後の分だけ、複数日では「どこかの日に食べた体」。O28 の他の配列と同じ扱い(注の「日の締めで 0 に
  戻す宣言」は O28 全体で実態と違う=前から)。計器の意味を記録に書く。
- **L6** `BR-MEAL-DEFAULT-VALIDATION-ARM` の外す段 4-3 は実装役の当て(remove_basis=inferred)。§0-6 の「次の版上げ」は 4-3 より前の
  小さな版上げかもしれない=親が決める。記録の「(切替口の整理)」は計画の 4-3 の行(母集団が動く)に無い呼び名。
- **L7** 書き直した `initial_since_meal` の docstring に「tick 0」が残る(T0 の規則=新しい docstring に tick を入れない)。
- **L8** W17 v2 は月曜(d0)の行しか無い(d1〜d6 は 0 行)=「その日に行の無い窓は全曜日をまとめる」は実際には月曜の行。
  月曜以外に始まるランでは範囲外の予定の表が全員「行なし」になる(前からの `BR-K9-MONDAY`)。記録の限界に 1 行。
- **L9** 朝の偏り(親の判断の材料): 朝の窓に食事の行を持つ体は 2.79%、朝の窓に「支度」の行があり食事の行の無い体は 65.15%
  (検収役の数え)=実装役の推測「朝の支度に含まれる」を支える。朝の既定は 2.8% の体の 10,972 行の分布(p50=450)から全員の
  97% に引かれる。記録の「未確認」を「支度 65% で裏づけ・朝食の時刻が支度の行の中に隠れる偏りは残る」に。

(参考・欠陥ではない) 体の引きの鍵は母集団の中の体の番号(0..n−1)で、`body.weight`・`body.eer` と同じ並べ方。同じ人でも
5,000 体と 39 万体で番号が違えば引く時刻が違う。

## 試験

- 範囲(`tests/engine/body tests/engine tests/c8 tests/engine/bridging tests/economy/cp2 tests/tools` と 10b・10f の 3 本・
  `-n 2 --dist loadfile -m "not slow"`・data つき): **3,017 passed・2 failed・1 skipped**(38 分 50 秒)。
  - `test_state_checks_10f::test_t4_axis2_required_made_discardable_fails`: 土台 `32fb262` の src で回しても落ちる=前から。
  - `test_classical_social::test_run_golden_and_arms`: (g) の状態の漏れ(順番で落ちる・単独で 1 passed・再現の手順は上)。
- `lint-imports`(作業木の src): 5 kept・0 broken。
- `tests/c7` は回していない。

## 親に確かめてほしいこと

1. M1・M2 を直してから取り込むか(M1 は 1 本・M2 は rebase の後の byte-check の取り直しと一緒にできる)。
2. 5a の report(第 18-1 表と比べる道具)に「無効/検証可」の印を写すか(計器は印だけを持つ)。
3. `BR-MEAL-DEFAULT-VALIDATION-ARM` の外す段(4-3 か、次の小さな版上げか)。
4. (g) の漏れを先に直すか(`set_arms` を戻す形にする)。直さないと data つきの 1 プロセスの全体試験で golden が順番で落ちる。
5. 朝の偏り(L9)を仮採用のまま進めるか(朝の既定は 2.8% の体の分布)。
