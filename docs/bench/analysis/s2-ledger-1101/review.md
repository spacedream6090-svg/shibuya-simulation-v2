# 独立検収 段 2 の 2・6・7(枝 stage/s2ledger-1101・土台 a09809c・作業木の HEAD c0729a4 の上の未 commit の差分)

検収役(Opus 5.5)。実装を見ていない立場で、差分・試験・自分の対照で確かめた。書いたのは本記録だけ(commit・add・ネットワークなし)。

## 判定: 条件つき受入

規律(既定の結果は不変・src は `world/processes/` だけ・既存の台帳の行とパターン台帳の既存のセルは不変・識別子・LF)は全部守られている。自己申告の数はすべて再現した。ただし、循環の検査には構造上見えない経路がある。入力の宣言にはエンジンと食い違う写しが 1 件、外す段の当て方には食い違いがある。中 4 件を直すか、親が扱いを決めてから取り込むのがよい。

## 1. 差分の範囲

- `git diff --stat HEAD`: `bridging-ledger.json`(+1869/−1=末尾の `]` だけ)・`v2-pattern-ledger.md`(95/95=表の行の末尾に 2 セル)・`src/shibuya/world/processes/` の `__init__.py`・`first_batch.py`・`records.py`。新しいファイルは `absent.py`・`inputs.py`・`circularity.py`・`tools/ledger/` の 2 本・`tools/instruments/absent_declarations.py`・試験 4 本・本記録の README と一覧。
- src の変更は `world/processes` の中だけ。消した行は無い。既存の試験も変えていない。
- 新しいファイルと変えたファイルは全部 LF。秘密スキャンは CLEAN。import-linter は 5 契約とも KEPT。識別子に `open`/`tick` は無い(コメントと文字列、既存の id `store_opening` だけ)。記録に絶対パスは無い。

## 2. 試験

| 範囲 | 本数 | 結果 |
|---|---|---|
| `tests/bridging`・`tests/world`・`tests/tools/test_absent_declarations.py`・`tests/c8`・`tests/engine/processes`・`tests/engine/test_state_checks_10f.py`・`tests/engine/bridging` | 585 | 全部通る(落ち 0・飛ばし 0) |
| うち新しい試験(`tests/bridging` 18・`test_declarations_1101.py` 11・`test_absent_declarations.py` 3) | 32 | 全部通る |
| data の無い写し(追跡と未追跡のファイルだけを scratchpad に写した)で `-m "not gpu and not slow"`(新しい試験+`tests/world`) | 157 | 通る(飛ばし 2=既存の requires_data)。ci-1 の既定の範囲で回る |

`tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` は作業木では落ちる(本体の src を当てても落ちる)。本体のリポでは通る。原因は作業木のテープの道筋(`data/tape/` の読み)で、この段とは関係ない。自己申告の「本体でも落ちる」は「作業木では本体の src でも落ちる」の意味に読めば正しい。

## 3. 自分の対照

| 対照 | 結果 |
|---|---|
| (a) 既存の行 | 土台の 673 行は、id ごとの JSON が全部同じで、順も同じ。頭の `schema`・`note` も同じ。足した鍵は `row_fields_note`・`row_fields` だけ |
| (a) DEC の行 | 112 行。`routing_row` は #1〜#112 を 1 回ずつ持つ。id は全部 `DEC-<#>-<camelCase>` |
| (a) 行き先の件数 | routing §1 の表を自分で数えた結果: L1 残す 9・L1.5 55・L2 7・初期の予定 8・代打 1・無いと宣言 6・要判断 26(計 112)。§2-1 と DEC の `why` の両方と一致。行ごとの行き先の写しの食い違いも 0 |
| (a) `row_fields` | 140 行=drives_from 36・world_process 47・decided 41・contributes 2・calibration_declined 2。全部が active の行に付いている |
| (b) パターン台帳 | 本体の HEAD の版と比べた。行数は同じ 270 行。変わった行はどれも「旧の行+末尾の 2 セル」で、旧の部分はバイトまで同じ。触った表は 10(階層 A〜E・G=8→10 セル・F=7→9・§9=8→10・§10-1・§10-2=4→6)。表でない行の変更は 0。触っていない表は §2 の封印表ほか 4 つ |
| (c) 冪等 | 土台の台帳の写しに `add_decision_rows_1101.py` を 2 回回すと、2 回とも作業木の台帳とバイトまで一致。本体の HEAD のパターン台帳に `add_pattern_columns_1101.py` を回すと 1 回目で一致し(10 表)、2 回目は 0 表で不変 |
| (d) 計器 | 出力は記録の `absent_declarations.md` とバイトまで一致。指紋 `79782bea9a830725` を再現した。一覧は 24 件。routing §3 の文案 23 件と照らすと、21 件は原文どおり。納品と発注の 2 件は指示書 段 2 の 6 で置き換えた文。電気と水は文案が無く実装役の文(`source` に明記)。絶対パスは無い |
| (e) 負の対照 | 写しの台帳で `DEC-24-whatAction` に drives_from=W2・contributes=W2 を足すと `test_no_unexpected_circularity` が落ちた。過程の写しで `hotel_room_inventory` の drives_from を W6(burned=要確認)にしても落ちた。`DEC-21-skipTrain`(口が無いの宣言のある行)に D10′ の重なりを作ると、主の検査は「absent」で通る。落ちたのは固定の一覧の試験だけだった(低-2) |
| (f) registry_hash | 土台(`git archive HEAD src`)と作業木の両方で `1a5fcb8c…31095743`。`to_json` の sha256 も同じ。`PlanSpec.revised` の `replace` は新しい欄を持ち越すだけで、hash には入らない |

## 4. 欠陥

### 中

**中-1 「採点する系」が全 48 行で行の ID と同じなので、`data:<id>` で書いた drives_from はどの行とも重ならない(系での突き合わせが働かない)**
- 再現: `circularity.parse_pattern_scoring()` を読むと、`scoring != id` の行は 0。drives_from が `data:` の主体は weather・rail の 2 つ・static_noise_field・opening の 2 つ・W17 の系の 7 行・祝日で、どれも重なりの対象にならない。
- 同じ道路交通センサス R3 が `data:road_census_r3`(騒音)と `D5′`(車)の 2 つの語で書いてある。系の名がそろっていないので、系ごとに突き合わせられない。
- 具体例: `static_noise_field` の contributes は D12′。パターン台帳の D12′ の用途欄には「W10 静的騒音場の較正(残差≤3 dB 宣言)」とあり、`w10_noise.calibrate` がこの 7 点で残差を出している。それなのに drives_from が `data:road_census_r3` なので、CI は何も言わない(burned=要確認は例外にならないのに、検出もされない)。
- 自己申告の 11(D5′→D5)と 6(W17→A5〜A7)も同じ根にある。
- 案: 「採点する系」に照合値の出典の系(`data:<id>`)を併記する。drives_from には、較正や残差の照合に使った錨も書く(騒音なら D12′)。同じ調査の語は 1 つにそろえる。

**中-2 入力の宣言 `input.weather` の細かさと補間がエンジンと食い違う(写しの誤り)**
- 宣言は「10 分値・tick 単位に線形補間」と書いている。エンジンの `environment.py` の `_heat_now` は、時別の配列 `hourly_heat_stage[row, hour]`・`hourly_wbgt[row, hour]` を 5 分ごとに引き、次の更新まで値を保つ(補間はしない)。
- 宣言の文は、`first_batch` の weather の `update_rule` の文を写したもの。単位の「℃・mm・m/s・%」も、エンジンが読む暑さ段と WBGT とは違う。
- CLAUDE.md §5 の写し検査(コードと設計書に残す)の対象になる。

**中-3 「無い」の例外が、規則がまだ動く過程にも効く=W2 の循環が既定のエンジンで動いたまま CI が緑になる(自己申告 §4-2 あり)**
- `delivery_last_mile` は 27,000 個/日=W2 の値で動き、W2(burned=—)で採点される。CI は「absent」の例外で通す。
- S2-rates が先に取り込まれる保証は無い。取り込みの順が逆なら、本体は動いている循環を緑で抱える。
- 案: `engine_now` が「規則がまだ動く」の間は例外を効かせない(W2 に `外す(S2-rates まで)` を付ける)か、S2-rates と同じ取り込みで入れる。

**中-4 DEC の行の `remove_at` が、同じ過程の宣言と回答 §2 の「すぐ外す」と食い違う**
- 「無いと宣言」の 6 行(#102〜106・110)は 6-6(② 人の仕事を働く人へ)。一方、同じ過程の `Absence.remove_at` は「収集員の体を置く段(空欄)」などで、routing は #104・106・110 を「すぐ外せる」と書いている。#105 は指示書 段 2 の 3 で今外す。
- 回答 §2 で外す率の行(#2 出勤・#3 E8・#10 催し・#22・#42・#83・#99)も、6-6・6-2・7 のまま。台帳には既存の語 `next-bump`(10 行で使用)がある。
- 同じものの外す段が、DEC の行と Absence の 2 か所で違う値になっている。自己申告の 12(要判断 26 行が 7 のまま)とは別の件。

### 低

- **低-1** `burned=要確認` の 8 行のうち D11′ は、用途欄に「生成に使用=独立でない・holdout には使わない」、区分に「初期化」とある。回答 §4「初期化に使った法則は burned」に従えば `burned` が規則どおり。E5 は発注の指定なので除く。D12′ は中-1 と合わせて決める。
- **低-2** 「無い」の例外が主体ごとに効き、系を見ない。`routing_row` に口が無いの宣言がある DEC 行は、どの系の重なりも「absent」で通る(対照 e の 3 つ目)。いまは固定の一覧の試験だけが止める。例外は宣言の `keeps_anchor` か、その過程が入る錨に限るのが安全。
- **低-3** `test_existing_rows_are_kept` は既存の行の中身を比べない(HD- の 85 行と位置だけ)。不変は親の対照で確かめたが、試験では守っていない。既存の 673 の id → 行の sha の指紋を固定するとよい(並走の段が足した行は別に数える)。
- **低-4** 入力の宣言について 3 点。外界ノードの `one_way` 欄は、一方向であることを書かず、何であるかの説明になっている。外の売上は出典の行が `accounts.py`(科目の許可)で、実体の `stage2.py external_sales` と値 `EXTERNAL_STORE_SALES_YEN=0`(資料なし・腕だけ=いまは流れていない)が宣言から読めない。暦・外界ノード・外の売上の 3 本は世界の台帳のどの記録にも付かないので、突き合わせの主体が無い(指示書 段 2 の 7 は「WorldProcess/PlanSpec に足し、既存の入力に書く」)。
- **低-5** L1 残すの 9 行(mechanism 8)が active のつなぎとして `bridges_count` に入る。#85(不応期 30 分は exp)・#76(語の区切りは exp)・#88(器だけ)は mechanism と言い切れない(自己申告の問い 2 と重なる)。
- **低-6** L2 → 6-7 の当て方: #49・50・52(発話)は会話の段(6-4)の方が近い。#79(範囲外の食事)は輪の段が要るので、6-2 より 7 が近い(どれも inferred)。
- **低-7** 計器は「版上げごとに出す」が、版上げの手順のどこからも呼ばれていない(手で回す)。
- **低-8** 宣言の中で W3 の読みが二通りある。パターン台帳の W3 は「外す(体の式ができるまで)」。一方、Absence の文(routing の写し)は救急と倒れるの 2 件とも「W3 は検証の錨に残す」。計器の出力に両方が並ぶ(問い 1)。
- **低-9** バス→D11′ の読み「contributes に無い=循環なし」は結論として正しい。ただ、より強い理由は「D11′ は生成に使う錨で、そもそも検証に使わない」こと。

## 5. 自己申告との差

- 数はすべて一致した(673 行不変・DEC 112・行き先の件数・row_fields 140/36/47/41・10 表 2 列・冪等・24 件・指紋・32 本・registry_hash・E7 を drives_from に持つ主体 0・W2=無い・W3=外す)。
- 「例外で通らない重なり 1 件」は、系 D5′ の 1 件を主体 2 つ(vehicle_cross_section・DEC-109)で持つ。README §3 の表と同じ。
- 「burned の要確認 7 行」は E5 を除いた数で、E5 を含めると 8 行。
- 自己申告に無いもの: 中-1 の一般形(data の語が働かない・騒音と D12′ の具体例)・中-2・中-4・低-1〜4・低-6〜9。中-3 は自己申告の §4-2 にあるが、CI の規則を外す形なので欠陥に上げた。

## 6. 問い(親へ)

1. W3 の読み。指示書 段 2 の 3 は「率を外し…W3 は錨に残す」と書いている。率が S2-rates で外れれば W3 の循環は消えるので、印は「体の式ができるまで」でなく「S2-rates まで」で足りる、というのが検収役の読み。倒れる人は 0 になるので、W3 の不合格は回答 §2 の「短期の不合格の増加は受け入れる」で説明する。どちらにしますか。
2. 中-1 の直し(「採点する系」に出典の系を併記・騒音の drives_from に D12′・語の統一)を、この段で入れますか、それとも次に回しますか。
3. 中-4: 回答 §2 で外す行と「すぐ外せる」行の `remove_at` を `next-bump` に当て直しますか。
