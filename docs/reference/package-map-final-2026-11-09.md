# コードの区分の最終の表と、移す段の計画 2026-11-09

> [返事その 7](../design/prompt-2026-11-09-reply7.md) §4-2 の 1 と 3〜5 に答える文書です。設計役(Opus 5.5)が作りました。ファイルは 1 本も動かしていません(表と計画を書いただけです)。
> 付属は 3 つです。[全ファイルの表](package-map-final-2026-11-09-files.md)(src の追跡ファイル 324 本)、[心の読みの数え直し](mind-world-reads-2026-11-09.md)と同じ中身の [json](mind-world-reads-2026-11-09.json) です。
> 読んだもの: 返事その 7 §4、[照らし合わせ](package-map-reconcile-2026-11-05.md)、[案 K](package-map-claude-code-2026-11-05.md) と[その付属の表](package-map-claude-code-2026-11-05-files.md)、[壁打ちの記録](wallbounce-record-2026-11-02_05.md) 2-21・2-27・2-33〜2-36、[v3 の核の設計書](../design/v3-core-design-2026-11-03.md) 題 10、[返事その 6](../design/prompt-2026-11-05-reply6.md) §2 題 10・§3-2・§4、src のコード(必要な所)。`data/`・IMPLEMENTED.md・build-report・門 1 の計画・パターン台帳・検証の錨は開いていません。Web は使っていません。
> コードの版は作業木 `stage/pkgtable` の HEAD `14b151a` です。src と pyproject.toml は、案 K が読んだ `15b6bbd` と同じです(`git diff` で確かめました)。
> 数えたスクリプトは作業用の場所に置き、リポには入れていません。関数の単位の割り先は、案 K の作業の表(記号ごとの割り先)を引きました。
> 印: 【確認】=コードか数えで確かめた。【未確認】=確かめていない。【見立て】=この役の判断。

## 0. 要旨

1. src の追跡ファイル 324 本の最終の置き場を決めました(付属の表)。土台は照らし合わせ §7 の合わせた案で、そこに返事その 7 §4-1 の決着を当てました。包みは原則の 11 と、一時の区分 1 つで 12 です。
2. 包みごとの数は foundation 40・runtime 41・world 59・mind 32・act 7・economy 18・society 11・一時の区分 17・experiments 10・validation 6・interfaces 1・build 79・根 1・消す 2 です。合わせた案との差は、world −1・society −16・一時の区分 +17 だけです。
3. 一時の区分の名は `interim_bundles` にしました。「interim」が一時の物と分かる語で、「bundles」は決着の語「束ね」です。束ねの 5 つとその部品のほかは入れない範囲も、名から読めます。
4. `engine/calendar_shadow.py` は、W20 の週の表の読み口を `world/facts/w20_calendar_reader.py` に、暦 1a の影の計器を `society/calendar_shadow.py` に割ります。計器はランの中で組み立てが作り、日の頭に張り直すので、ランより上の層の validation には置けません。society の決まり「器と計器だけ」に当たります。
5. 案 K の迷い 12 は決まりました。ランの側(`build/` の外の src)は、`w19_freeze` も `w21_sources` も 1 か所も import していません【確認】。2 つは build に置いたままにし、`validation/sealed` は作りません。封印の守りは、両案が揃って出した直し(封印の語の AST の検査と、ランを `sealed_only` で包む試験)で入れます。
6. 案 K と置き場が違うのは 37 本です。包みが変わるのは 24 本で、そのうち 17 本は束ねを一時の区分へ移したものです。残りの 13 本は、包みは同じで置き場の名か割り方が違うものです(society の副包みを外した 10 本・`calendar_shadow` の割り・出来事の記録の名・`resolve` の関数 1 つ)。その関数 `apply_detection` は世界の欄 `cells.b4_hash` を書くので、11-09 の書きの文に合わせて act へ移しました。
7. 割らずに移すだけの状態で数えると、包みをまたぐ辺は 676 本、包みの単位の循環は 1 組(6 つの包み)、原則に反する対は 28 本です。28 本のうち 23 本は割る段で消えます(うち 2 本は注釈だけの辺が残る見込み)。残るのは例外 T4・T5・T7・T8 の 4 本と、注釈だけの 1 本です。割った後の数は関数の単位の割り先が要るので、割る段で数えます。案 K の 35 本の内訳から引くと、16 本の見込みです【見立て】。
8. 心の区分が外の列を読む所は、走査の道具の数で 82 か所でした。同じ名の別物 8 か所を除き、道具が数えない店の値段の 1 か所を足すと 75 か所です(別紙)。
9. 移す段は段 1〜段 8 で、段 5 だけ 2 つに分けます。段 1 で固定の表(クラス → 今の名前)を入れます。名前を変えてはいけない文字列は、クラスの名 480(固定の表)・乱数の領域の名 42(そのうち今のモジュールの道と同じ形が 8)・版の ID 70 か所(52 本)・ハッシュと指紋の見出しのバイト列 9 です。
10. 聞きたいことは 7 つです(§8-1)。

## 1. 包みと層

### 1-1 12 の包み

| 包み | 中身 | 本数 |
|---|---|---:|
| foundation | 時間・乱数・ハッシュ・SoA・manifest・語彙・口の型・文の道具・予約の列・出来事の記録・腕の切替口 | 40 |
| runtime | 時計・状態の保存とハッシュ・推論の口・系・組み立て・ランと結果 | 41 |
| world | 事実(`facts`)・台帳(`ledger`)・状態と資産(`model`)・持ち物(`things`)・体(`body`)・法則とつなぎ(`laws`) | 59 |
| mind | 判断(`judge`)・記憶(`memory`)・知覚の描き方(`percept`)・予定(`plan`)・関係(`relations`)・System 1(`system1`)・心の欄の書き手(`ops`) | 32 |
| act | 判断の結果の入口・取り合いの裁定・言葉の読み(`intake`)・世界の欄の書き手(`ops`)・意図と活動 | 7 |
| economy | 今の `economy/` と、賃金の式・経済の規則の口・段階 2 の口 | 18 |
| society | 器と計器だけ(会話・発話・道具の台帳・グループ・規範の計器・暦 1a の影の計器) | 11 |
| interim_bundles | 一時の区分。カレンダー 2・カレンダー 3・カレンダー 1b・連絡・店の仕事の束ねと部品(v3 で割る) | 17 |
| experiments | 申込書と世界に入る口(`port`)・分岐と切り替えの駆動(`drive`) | 10 |
| validation | 試験だけが呼ぶ検査(`static`) | 6 |
| interfaces | CLI | 1 |
| build | 今の `build/` のまま(ランで読まれない) | 79 |

ほかに根の `__init__.py` が 1 本、消すものが 2 本(`agents/__init__.py`・`census/__init__.py`)あります。

### 1-2 層(上が下を読む。`|` は互いに読まない)

```text
interfaces
validation.static
experiments.drive
runtime
interim_bundles                 ← 12 番目の一時の区分(案 K の society.arms の位置)
world.laws
mind | act | society
world.body
world.model | world.things | economy
world.facts | world.ledger | experiments.port
foundation

build は横に置く。ランの側からは読まれない。
```

- 案 K の層との違いは 3 つです。`society.arms` の位置に一時の区分を置きました。`society.vessels` を `society` にしました。`world.things`(持ち物)を `world.model` と同じ高さに足しました。
- `world.things` は今は `contact/device.py` の 1 本です。読むのは foundation だけで、読み手は一時の区分の連絡の束ねだけです【確認】。

### 1-3 一時の区分の名

**`interim_bundles` を選びました**。理由は 3 つです。

1. 「interim」は「当座の・一時の」を表す語で、決着の「名前に一時の物と分かる語を入れる」に当たります。
2. 「bundles」は返事その 7 §4-1 の問い 4 の語「束ね」そのものです。中身の範囲(束ねの 5 つとその部品)が名から読めるので、ほかの一時の物の置き場になりにくくなります。
3. 「腕」(arm)の語を避けました。このリポで「腕」は切替口を指し、切替口 4 本は `foundation/arms/` に置きます。案 K と照らし合わせの例の `arms` を名にすると、2 つが紛れます。

採らなかった名: `transitional`(何の一時の置き場かが名から分からない)・`legacy_*`(消す前の古いコードに読めるが、中身は既定のランで動くコード)・`arms`(上の 3)。

### 1-4 society の副包みを外した

案 K は society を `vessels`(器)と `arms`(束ね)に分けていました。束ねが一時の区分へ出たので、society に残るのは器と計器だけです。副包みに分けておく理由(契約の層が重ならないようにする)が無くなったので、`society/vessels/…` を `society/…` にしました。器という名の副包みに計器(`norm_meter`・暦 1a の影)が入る食い違いも無くなります。

## 2. 包みごとの数(照らし合わせ §7-1 の形)

割るファイルは主な割り先(いちばん大きい割り先)で数えました。

| 包み | 最終 | 案 K | 合わせた案 | 合わせた案との差 | 差の元 |
|---|---:|---:|---:|---:|---|
| foundation | 40 | 37 | 40 | 0 | — |
| runtime | 41 | 41 | 41 | 0 | — |
| world | 59 | 60 | 60 | −1 | `calendar_shadow` の主な割り先が計器(society)になった |
| mind | 32 | 32 | 32 | 0 | — |
| act | 7 | 7 | 7 | 0 | `apply_detection` は resolve の中の関数なので本数は変わらない |
| economy | 18 | 18 | 18 | 0 | — |
| society | 11 | 30 | 27 | −16 | 束ね 17 本を一時の区分へ(−17)・`calendar_shadow`(+1) |
| interim_bundles | 17 | — | — | +17 | 問い 4 の決着 |
| experiments | 10 | 10 | 10 | 0 | — |
| validation | 6 | 6 | 6 | 0 | — |
| interfaces | 1 | 1 | 1 | 0 | — |
| build | 79 | 79 | 79 | 0 | 動かさない |
| 根 | 1 | 1 | 1 | 0 | — |
| 消す | 2 | 2 | 2 | 0 | 案 K は `census` と `engine/events` の頭、最終は `agents` と `census` の頭 |
| 計 | 324 | 324 | 324 | | |

これから動きうる分は 2 つです。聞きたいこと 1 で連絡の器 4 本を今 society に置くなら、society +4・一時の区分 −4 です。返事その 6 §3-2 の削除で切替口のファイルが消えれば、その行が消えます(候補は `engine/defect_fixes_1103.py`=runtime・`engine/absent_processes.py` と `engine/rate_rules.py`=world)。

割るファイルは 24 本です(案 K の 23 本に `calendar_shadow` を足した)。照らし合わせが v3 に回した案 F の割り(`constitution` の検査と定数・`conversation` の 4 つ・`experiment/gate` の依存の逆転・`llm/contract` の書式の切り出し)は、この表に入れていません(§8-2)。

## 3. 案 K からの差

案 K と置き場が違うのは 37 本です【確認】。

| まとまり | 本数 | ファイル | 案 K | 最終 | 元 |
|---|---:|---|---|---|---|
| 束ね | 17 | `engine/calendar2/{__init__,layer}`・`calendar3/{__init__,knowledge,layer,roster}`・`calendar_self`・`contact/{__init__,book,calls,chat_state,deliver,layer,tools}`・`duties/{__init__,knowledge,layer}` | `society/arms/…` | `interim_bundles/…` | 11-09(問い 4) |
| 暦 1a の影 | 1 | `engine/calendar_shadow.py` | `society/vessels/calendar_shadow.py`(割らない) | `society/calendar_shadow.py` 197・`world/facts/w20_calendar_reader.py` 115 | 11-09(読み違いの直し) |
| 持ち物 | 1 | `engine/contact/device.py` | `society/arms/contact/device.py` | `world/things/device.py` | F |
| 欠陥 4 件の切替口 | 1 | `engine/defect_fixes_1103.py` | `world/laws/switch_defects.py` | `runtime/switch_defects.py` | F |
| 体の出来事の口 | 1 | `engine/events/body.py` | `society/vessels/tools/body_events.py`・語の変換を `foundation/vocab/events.py` | `mind/memory/body_events.py`・語の変換は同じ | F |
| 出来事の記録の小包み | 3 | `engine/events/{__init__,links,log}.py` | 消す・`world/model/journal_links.py`・`foundation/journal.py` | `foundation/journal/{__init__,links,log}.py` | F・F・K(名だけ) |
| manifest の欄の分け方 | 1 | `engine/manifest_sections.py` | `runtime/state/manifest_sections.py` | `foundation/manifest/sections.py` | F |
| 頭 | 1 | `agents/__init__.py` | `mind/__init__.py`(空にする) | 消す | 照らし合わせ |
| society の副包みを外す | 10 | `engine/conversation`・`norm_meter`・`speech/{__init__,layer,port}`・`tools/{__init__,groups,places,record,registry}` | `society/vessels/…` | `society/…` | K(名だけ) |
| 書き手の割り | 1 | `engine/resolve.py` | `apply_detection` を `mind/ops.py` | `apply_detection` を `act/ops/detect_writes.py`(10 行) | K(関数 1 つは 11-09 の書きの文) |

- 照らし合わせが案 F に寄せた 7 本のうち 6 本は案 F の置き場のままです。`calendar_shadow` だけは返事その 7 の直し(表を読む口と計器に割る)を当てたので、元を 11-09 にしました。
- `apply_detection` は `world.cells.b4_hash`(世界の欄)と内受容の段の 3 列(心の欄)を 1 つの関数で書きます(`resolve.py` の `apply_detection`)【確認】。案 K の書き手の表では、act の外が世界の欄を書くのはこの 1 か所だけでした(案 K §4-6)。11-09 の書きの文「世界の欄を書く関数は act だけが持つ」(記録 2-34)に合わせて act へ置きました。割るかどうかは聞きたいこと 2 です。
- 置き場の名の決め方: 案 F の置き場は照らし合わせの要約にしか無いので、包みは案 F に合わせ、道は案 K の名の付け方(`switch_*`・`foundation/manifest/…` など)に寄せました【見立て】。

## 4. 決着の当て方

| 問い(照らし合わせ §4) | 決着 | 表への当て方 | 移す段で入れるもの | 到達点(書き添え) |
|---|---|---|---|---|
| 1 心が世界を直接読まないことの守り | 推し A(記録 2-33) | `agents/state.py` の表は `world/model/agent_table.py`、語彙は `foundation/vocab/agent_codes.py`(案 K)。心の区分は 32 本 | ① 心の区分が世界の区分を使えない import の決まり(§6-4 の 3)を段 4 の終わりから入れる ② 心が読んでよい欄の一覧(別紙の 82 か所)を試験で固定し、減らす向きにだけ動かす。状態台帳の SoA の行に持ち主の欄を足すのも同じ時(案 K §5-1 の ②)。③ 読むだけの窓口と ④ かき乱しの試験は 9-2 と一緒なので、この計画には入れない | 心に渡すのは知覚だけ |
| 2 世界を書ける範囲 | 推し A(記録 2-34) | resolve の書き手は `act/apply.py`・`act/ops/*` へ(案 K)。`apply_detection` も act へ(§3)。世界の法則 9 本と束ね 3 本は act の関数を呼ぶ形のまま | 決まり 4(act の書く関数を呼べるのは act・world.laws・interim_bundles・runtime・interfaces)。宣言する書きの例外は、表の組み立ての初期値(`AgentState`・`World` の 40 か所)・再開の復元(`runtime/state/restore.py`)・給料日のような経済の過程・お金と物の基本の操作(economy)。原因の印の割合の計器は計器を足す作業なので、移す段の外 | 法則は差分を返し、act が当てる |
| 3 関係と約束の置き場 | 推し A(記録 2-35) | 世界の事実=最初の結びつき(`world/facts/initial_ties.py`)・権利(`world/facts/rights/`)・W20 の表(`world/facts/w20_calendar_reader.py`)。運ぶ器=会話(`society/conversation.py`)・グループ(`society/tools/groups.py`)。配達は今は一時の区分(聞きたいこと 1)。本人の理解=関係の記憶(`mind/relations/`)・約束の帳面(`mind/plan/promise_book.py`)・頭の中の予定(`mind/plan/head_recall.py`)。持ち物=`world/things/device.py` | 写しは始めの 1 回(`relations.initial_edges` から記憶の初期値へ)。今のコードの形のまま | 連絡帳(`contact/book.py`)と手帳・アプリの予定を `world/things/` へ。今の `contact/book.py` は心の関係の層を読むので、今 world に置くと world から mind への辺になる |
| 4 束ねの一時の置き場 | 12 番目の一時の区分 | `interim_bundles` に 17 本。society は器と計器だけ(11 本) | 層の位置=runtime の下・world.laws の上。読み手を runtime と interfaces に限る決まりの案(§6-6・聞きたいこと 7) | v3 で割る |
| 5 実行中の意図と活動 | 推し A(記録 2-36) | `engine/intent.py` → `act/intent.py`・`engine/activity.py` → `act/activity.py`・意図の書きは `act/ops/intent_writes.py`(案 K) | — | 意図と予定は心・実行の仕組みは act(9-2・9-5 で割る) |
| 6 System 1 の「届いたか」 | 推し A(移す段は案 K の置き場・記録 2-27) | `perception/p_notice.py` → `world/model/notice_reach.py`・`perception/state.py` → `world/model/percept_state.py`・`attention` の `p_see` と `gate_stage1` → `mind/percept/attention.py` | — | 9-3c の式を作り直すときに、届いたかは世界・振り分けは心に割る |
| 7 権利と規則の表 | world の事実の側 | `engine/rights/*`・`engine/rules/*` → `world/facts/`(案 K) | 決まり 6(economy は world.facts と foundation だけを読む) | — |
| §3 の直し 1 runtime | 採る | — | runtime の核の決まりの案(§6-6・聞きたいこと 3) | — |
| §3 の直し 2 書きの文 | 採る(問い 2) | 問い 2 と同じ | 問い 2 と同じ | — |
| §3 の直し 3 心の読みの守り | 採る(問い 1) | 問い 1 と同じ | 問い 1 と同じ | — |
| §3 の直し 4 封印 | 採る | 迷い 12 の結論(§5-3) | 段 2 の 2 つの試験(§7-3 の 2-6) | — |
| foundation と contracts に割るか | 移した後に決める | 今は foundation のまま(40 本) | — | — |

## 5. 読み違いの直しと、迷い 12

### 5-1 `engine/calendar_shadow.py`(表を読む口と計器に割る)

- 表を読む口(→ `world/facts/w20_calendar_reader.py`・115 行): `CalendarTable`・`load_table`・`resolve_path` と補助 `_readonly`・`_freeze`・`_thaw`・`_sha256`、定数 `FILE_NAME`・`STAGE_DIR`・`HEADER_NAME`・`WEEK0_MONDAY`・`N_DAYS`・`COMMIT_WORK`・`COMMIT_SCHOOL`・`_COLS`。読み手は束ねの `calendar_self.py`(:86 で import・出勤と通学を決める)と `calendar3/roster.py`(:188)、計器の `tools/instruments/anchor_gauge.py`(`FILE_NAME`・`STAGE_DIR`)です【確認】。W17 の読み口 `agents/weekly.py` を `world/facts/weekly_reader.py` に置いた案 K の扱いと揃えました。
- 計器(→ `society/calendar_shadow.py`・197 行): `CalendarShadow`・`build`・`manifest_fields`・補助 `_hist15`・`_stats`・`_active15`・`_w17_work_span`、腕の切替口 `arm`・`set_arm`・`is_on`、定数 `MODE_*`・`SCHEMA`・`SLOT_MIN`・`N_SLOTS`・`W17_WORK_CODE`・`MANIFEST_*`。

**計器の置き場は society を選びました**。理由は 3 つです。

1. 計器はランの中で動きます。組み立て(`systems/build.py:876` の `build`)が作り、日の頭に `systems/state_io.py:176-178` が `relay_day` で張り直し、結果(`run.py:1442` の `manifest_fields`)が読みます【確認】。validation は runtime より上の層(`validation.static`=試験だけが呼ぶ検査)なので、ここに置くと runtime から validation への上向きの辺が 3 本できます。
2. 束ねの `calendar_self.py` が計器の補助 `_hist15`・`_stats` を 19 か所で使います【確認】。だから計器は一時の区分より下の層に要ります。society はその下です。
3. society の決まり「器と計器だけ」に当たり、群と規範の計器 `norm_meter` と同じ形です。読む先は world.facts(W17 と W20 の読み口)と foundation だけです【確認】。

腕の切替口は計器と一緒に置きました。読み手は CLI と組み立てだけで、どちらも society より上です。

### 5-2 `perception/attention.py`(案 K の割り方)

案 K のとおり、文と目立ちの道具(`feature_tag`・`strip_imperatives`・`tag_world_text`・`SalientItem`・`rank_by_saliency`・`apply_budget` ほか)を `foundation/text/salience.py`(182 行)へ、気づきの門(`p_see`・`gate_stage1`・`P_SEE_*`)を `mind/percept/attention.py`(45 行)へ割ります。世界の過程が使うのは道具の側だけです(`civic.py:250-251` の `feature_tag`・`strip_imperatives`、`salient.py:384-403` の `SalientItem`・`rank_by_saliency`・`apply_budget`)【確認】。構築の `build/lang/common.py:40` も `strip_imperatives` を読みます。乱数の領域の名 `perception.attention.p_see`(`attention.py:227`)は名を変えません(§7-2)。

### 5-3 案 K の迷い 12(封印を読む部品)

- 確かめたこと: `build/` の外の src の全部の import(頭・関数の中・`importlib.import_module` の文字列)を AST で見ました。`shibuya.build` を読む所は 0 でした【確認】。`w19_freeze`・`w21_sources`・`HOLDOUT_TOKENS`・`W21Guard` の名がランの側に出るのは、`economy/wages.py` の docstring とコメント(:15・:102)と `world/processes/circularity.py` の docstring(:4)だけです。
- 使っているのは build(`w21_*` の組み立て)と試験 5 本(`tests/build_audit/`・`tests/build_pop/`・`tests/economy/test_wage_occupation.py`)です。tools の `c7/holdout_compare.py`・`fig/fig_presence_24h.py` はファイル名 `w19_freeze.json` を文字列で持つだけで、2 つの部品は import しません。
- 結論: 2 つは build に置いたままにします(案 K の (a))。ランの側が読まないので `validation/sealed` は作らず、案 K の契約 9 はコメントのままにします。ランの側から build を読めない決まり(§6-4 の 8)が、今の import の守りになります。
- 封印の守り(§3 の直し 4)は §7-3 の 2-6 で入れます。今のランの側の封印の語は 3 か所です(`engine/energy.py:7` の docstring・`:230` の定数 `ANCHORS_VALIDATION_PATH`・`world/processes/inputs.py:86` の宣言の文)【確認】。
- 封印の語の表は 2 つあります。`build/audit/w19_freeze.HOLDOUT_TOKENS` と `tools/instruments/read_guard.SEALED_TOKENS` で、互いに import していません【確認・値は開いていない】。検査をどちらで書くかは聞きたいこと 5 です。

## 6. 辺の数(この表で数え直せる範囲)

### 6-1 数え方

- import をモジュールの対(重複なし)で数えました。同じ対に頭の import と関数の中の import があるときは強い方(頭 > 関数の中 > `TYPE_CHECKING`)で 1 本にします。
- 再輸出の頭を通る import は、元のモジュールまで追いました。空にする頭と消す頭(合わせて 25 本)と、`llm/__init__.py` の再輸出(`mock`・`parser`・`undefined`・`fleet`)から出る対(合わせて 45 本)は数えていません。どれも移す段で消えるためです。
- 割るファイルは、最上位の文の割り先(案 K の既定の割り先)へ丸ごと置いた「割らずに移すだけ」の状態で数えました。関数の単位の割り先が要る「割った後」は、割る段で数えます(§6-5)。
- 今の木の数は、import の名 2,523(頭 2,152・関数の中 370・`TYPE_CHECKING` 1)、モジュールの対 1,251(頭 1,032・関数の中 218・`TYPE_CHECKING` 1)で、案 K と照らし合わせの数と合いました【確認】。
- 案 K の数え方(使う名前を追い、注釈だけの辺を分ける)とは違います。案 K の「割らずに移すだけ」の 662 本と、この数はそのまま比べられません。

### 6-2 包みをまたぐ辺(割らずに移すだけ)

包みをまたぐ対は **676 本**(頭 532・関数の中 144)です。表の中は「頭 / 関数の中」です。

| 元 ＼ 先 | foundation | world | mind | act | economy | society | interim_bundles | runtime | experiments | validation | interfaces | build | 計 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| foundation |  |  |  |  |  |  |  |  |  |  |  |  | 0 |
| world | 79/2 |  | 2/0 | 9/0 |  |  |  |  |  |  |  |  | 92 |
| mind | 67/4 | 5/1 |  | 5/2 | 1/0 | 1/1 |  | 2/0 |  |  |  |  | 89 |
| act | 18/1 | 7/1 | 2/0 |  | 0/1 |  |  | 0/3 |  |  |  |  | 33 |
| economy | 10/4 | 0/6 |  |  |  |  |  |  |  |  |  |  | 20 |
| society | 14/2 | 1/0 | 0/1 |  |  |  |  | 1/0 |  |  |  |  | 19 |
| interim_bundles | 45/3 | 4/8 | 11/2 | 3/0 |  | 9/2 |  | 1/0 |  |  |  |  | 88 |
| runtime | 68/21 | 29/14 | 22/5 | 24/1 | 1/1 | 4/6 | 5/11 |  | 2/3 |  |  |  | 217 |
| experiments | 7/1 | 0/1 | 0/2 |  |  |  |  | 0/3 |  |  |  |  | 14 |
| validation | 0/1 | 4/2 |  |  |  |  |  | 1/0 |  |  |  |  | 8 |
| interfaces | 5/7 | 6/5 | 6/3 | 3/1 | 8/0 | 0/2 | 0/1 | 2/4 | 1/3 |  |  |  | 57 |
| build | 33/1 | 2/0 |  |  | 2/0 |  |  |  | 0/1 |  |  |  | 39 |

一時の区分へ入る辺は 17 本で、全部 runtime(16)と interfaces(1)からです【確認】。

### 6-3 循環(割らずに移すだけ)

| 単位 | 頭の import だけ | 関数の中を含む |
|---|---|---|
| 包み | 1 組(act・interim_bundles・mind・runtime・society・world) | 1 組(上に economy・experiments を足した 8) |
| 副包み | 1 組(act・interim_bundles・mind・runtime・society・world.body・world.laws・world.model) | 同じ 1 組 |
| モジュール | 0 組(今の木の `llm`・`llm.fleet`・`llm.mock` の 1 組は、頭の再輸出を消すので無くなる) | 9 組(最大 16 本) |

包みの単位の循環を作るのは、丸ごと置いた割るファイルです。例えば `llm.mock` の定数 `MOCK_UTTERANCE` を mind・society・一時の区分が読み(→ runtime)、`act.apply`(resolve の丸ごと)が runtime の状態の部品を関数の中で読みます。どれも割る段で外れます(§6-4 の表の「消える段」)。割った後の循環は割る段で数えます。案 K の模擬では、割った後の包みの単位に 2 組(economy・act・world と runtime・experiments)、例外 T1〜T8 を除いた副包みに 0 組でした。

### 6-4 原則に反する辺(割らずに移すだけ)

使った決まりは、案 K §3 の 8 つの契約を最終の表に合わせたものです。

1. 層(§1-2 の順。下から上と、`|` の兄弟の間を読まない)
2. foundation は何も読まない
3. mind は foundation(と mind)だけを読む
4. act の書く関数(`act.apply`・`act.ops`)を読めるのは act・world.laws・interim_bundles・runtime・interfaces だけ
5. お金と物の書き手(`economy.ops`・`economy.goods`・`economy.ledger`)を読めるのは economy・interfaces だけ
6. economy は world.facts と foundation だけを読む
7. society は act・mind・runtime・world.laws・interim_bundles を読まない
8. ランの側は build を読まない

当たった対は **28 本**(頭 20・関数の中 8)です。決まりへの当たりは延べ 45 です(1 本が 2〜3 の決まりに当たることがある)。決まり 2・5・6・8 に当たる対は 0 本でした【確認】。

| # | 読む側 | 読まれる側 | 形 | 当たる決まり | 読む名前 | 消える段 | 注 |
|---:|---|---|---|---|---|---|---|
| 1 | `act.apply` | `mind.system1.change_detect` | 頭 | 1 | `DetectResult`、`INTERO_UP_EDGES` | 段 6 | 注釈だけの 1 本(`DetectResult`)が残る見込み |
| 2 | `act.apply` | `runtime.state.hashes` | 関数の中 | 1 | `_ABSENT`、`resolve_item` | 段 6 | 復元の関数が runtime/state/restore.py へ出る |
| 3 | `act.apply` | `runtime.state.ledger` | 関数の中 | 1 | `state_ledger` | 段 6 | 同じ |
| 4 | `act.apply` | `runtime.state.resume` | 関数の中 | 1 | `ABSENT_MARK` | 段 6 | 同じ |
| 5 | `act.target` | `mind.judge.chooser` | 頭 | 1 | `ChoiceContext`、`Chooser`、`draw_index`、`entropy_bits` | 段 5a | 選び手の口が foundation/ports/choice.py へ |
| 6 | `interim_bundles.calendar2.layer` | `runtime.inference.mock` | 頭 | 1 | `MOCK_UTTERANCE` | 段 5a | `MOCK_UTTERANCE` が foundation/vocab/actions.py へ |
| 7 | `mind.judge.classical` | `runtime.inference.mock` | 頭 | 1・3 | `MOCK_UTTERANCE` | 段 5a | 同じ |
| 8 | `mind.judge.classical` | `world.facts.calendar` | 頭 | 3 | `ticks_per_day` | 段 5a | `ticks_per_day` が foundation/types.py へ |
| 9 | `mind.judge.decision.layer` | `act.commit` | 関数の中 | 1・3 | `commit` | 段 5b | `ACT_*` が foundation/vocab/act_codes.py へ |
| 10 | `mind.judge.decision.layer` | `economy.stage2_bind` | 頭 | 3 | `economy_stage2` | 残る | 例外 T4 |
| 11 | `mind.judge.decision.layer` | `society.tools.registry` | 関数の中 | 1・3 | `affordance_words` | 残る | 例外 T7 |
| 12 | `mind.memory.body_events` | `society.tools.record` | 頭 | 1・3 | `SIGNBOARD_CAUSE`、`SIGNBOARD_ORIGIN`、`SIGNBOARD_WHAT` | 段 5a | `SIGNBOARD_*` が foundation/vocab/events.py へ |
| 13 | `mind.memory.familiarity` | `act.apply` | 頭 | 1・3・4 | `resolve` | 段 6 | 書きの関数が mind/ops.py へ |
| 14 | `mind.memory.memory` | `act.apply` | 頭 | 1・3・4 | `resolve` | 段 6 | 同じ |
| 15 | `mind.memory.memory` | `act.commit` | 関数の中 | 1・3 | `commit` | 段 5b | `ACT_*` が語彙へ |
| 16 | `mind.memory.store_memory` | `act.apply` | 頭 | 1・3・4 | `resolve` | 段 6 | 書きの関数が mind/ops.py へ |
| 17 | `mind.memory.wom` | `act.target` | 頭 | 1・3 | `BUYABLE_CATS`、`CATEGORY_WORDS`、`GENERIC_WORDS`、`SYNTHETIC_BUYABLE_CATS` | 段 5a | 店の語が foundation/vocab/place_words.py へ |
| 18 | `mind.percept.draw` | `world.model.assets` | 頭 | 3 | `CELL_SIZE_M`、`WorldAssets`、`array_sha256`、`file_sha256` | 段 7 | 使うのは world/model/percept_scene.py の側だけ |
| 19 | `mind.percept.draw` | `world.model.state` | 頭 | 3 | `LANDMARK_CATS`、`World` | 段 7 | `World` の注釈だけが残る見込み |
| 20 | `mind.plan.contact_port` | `runtime.inference.mock` | 頭 | 1・3 | `MOCK_UTTERANCE` | 段 5a | `MOCK_UTTERANCE` が語彙へ |
| 21 | `mind.relations.layer` | `act.apply` | 頭 | 1・3・4 | `resolve` | 段 6 | 書きの関数が mind/ops.py へ |
| 22 | `mind.relations.layer` | `world.model.proximity` | 関数の中 | 3 | `notice_p` | 残る | 例外 T5 |
| 23 | `mind.system1.change_detect` | `world.model.assets` | 頭 | 3 | `CELL_SIZE_M` | 段 5a | 使うのは world/model/scene_hash.py の側だけ |
| 24 | `mind.system1.change_detect` | `world.model.state` | 頭 | 3 | `World` | 注釈だけ | `World` の注釈だけ。`if TYPE_CHECKING:` へ移せば消える(案 K の注釈だけ 7 本の 1 つ) |
| 25 | `society.speech.layer` | `mind.memory.wom` | 関数の中 | 1・7 | `hear` | 残る | 例外 T8 |
| 26 | `society.speech.layer` | `runtime.inference.mock` | 頭 | 1・7 | `MOCK_UTTERANCE` | 段 5a | `MOCK_UTTERANCE` が語彙へ |
| 27 | `world.body.rules` | `mind.system1.change_detect` | 頭 | 1 | `INTERO_UP_EDGES` | 段 5a | `INTERO_UP_EDGES` が foundation/vocab/agent_codes.py へ |
| 28 | `world.model.geometry` | `mind.system1.change_detect` | 頭 | 1 | `DEFAULT_WALKABLE_AREA_M2` | 段 5a | `DEFAULT_WALKABLE_AREA_M2` が world/model/scene_hash.py へ |

- 消える段の内訳は、段 5a 11 本・段 5b 2 本・段 6 8 本・段 7 2 本・残る 4 本・注釈だけ 1 本です。消える段は、読む名前の割り先(付属の表 §4)から決めました【確認=割り先の表を引いた】。
- 残る 4 本は案 K の例外 T4・T5・T7・T8 です。T1・T2・T3・T6 は renderer と change_detect を割ったときに初めて出る辺なので、この表には出ません。
- 照らし合わせ §7-1 が「新しい違反を足さない【見立て・模擬はしていない】」とした 3 本(`defect_fixes_1103`=runtime・`contact/device`=world.things・`events/body`=mind)は、移すだけの状態で `events/body` の 1 本(#12)だけが当たり、段 5a で消えます【確認】。

### 6-5 割った後(割る段で数える)

割った後の包みをまたぐ辺・循環・原則に反する辺は、関数の単位の割り先が要るので、割る段ごとに数えます(段 5a・5b・6・7 の終わりと段 8)。

見込み【見立て】: 案 K の 35 本は、例外 T1〜T8 の 8 本・束ねの 20 本・注釈だけの 7 本でした(案 K §4-5)。束ねの 20 本は、一時の区分が world.laws・mind・world.body・world.ledger より上の層に入るので、層の上から下への辺になり、原則に反しなくなります。足されるのは `apply_detection` を act に置いた分の注釈だけの辺 1 本(`act.ops.detect_writes` → `mind.system1.change_detect` の `DetectResult`)です。だから 8+7+1=16 本の見込みです。

### 6-6 足す決まりの案

1. **一時の区分を読めるのは runtime と interfaces だけ**(protected の契約): 束ねに新しい読み手が付かなければ、v3 で割るときに直す先が増えません。移すだけの状態で、外の読み手は runtime と interfaces の 17 本だけでした【確認】。足すかは聞きたいこと 7 です。
2. **runtime の核は中身を読まない**(§3 の直し 1): 核の候補は、時計(`runtime/clock.py`・`runtime/clocks/*`)・状態の保存とハッシュ(`runtime/state/*`)・テープ(`runtime/inference/tape.py`)・進行役と系の宣言の型(`runtime/systems/{conductor,spec,boxes,day}.py`)です【見立て】。中身の包み(world・mind・act・economy・society・interim_bundles・experiments)を読む辺は、移すだけの状態で 3 本でした。

| 核の候補 | 読む先 | 名前 | 割った後 |
|---|---|---|---|
| `runtime/clocks/speech.py`(今の `engine/speech_clock.py`) | `society/speech/port.py` | `mora_count` | 残る(聞きたいこと 3) |
| `runtime/clocks/step_scope.py` | `mind/system1/change_detect.py` | `INTERO_VARS` | 段 5a で `foundation/vocab/agent_codes.py` へ出るので消える |
| `runtime/state/resume.py` | `world/facts/calendar.py`(関数の中) | `resolve_repo_path` | 段 2 で `core/paths.py` へ出す案(§7-3 の 2-2)なら消える |

組み立て(`runtime/systems/assemble.py`)・系(`runtime/systems/*` のほか)・結果(`runtime/result.py`)・ラン(`runtime/run.py`)・推論の口は、中身を読んでよい側に入ります。

## 7. 移す段の計画(設計だけ)

### 7-0 前提と止め方

- 順は返事その 7 §4-2 の 5 のとおりです。返事その 7 §2 の段 2 の直し → 返事その 6 §3-2 の削除 → この移動です。§3-2 で消えたファイルは、段 1 に入る前に付属の表から行を消します。
- 各段の終わりに byte-check 19 構成(`tools/bytecheck/`)を回します。別の役が本体の作業木に置いている途中の版(未 commit)の README と表の頭だけを読みました。基準の commit と比べる側の src で 19 構成を回し、final を含む 25 欄を比べます(1 回 7 分ほどのランを 38 本)。final が 1 つでも変わったら、そこで止めて報告します。戻すのは、その段の前の commit です。
- 各段で pytest の全体と CI を回します。段 4 の終わりからは新しい import の決まりで lint-imports も回します。
- 整理の段なので、版上げの記録(安定版のタグ・戻す手順 1 行・性能の記録。CLAUDE.md §4)を段ごとに残します。
- 1 段 1 commit を基本にします。段 4 だけは包みごとに分けます。

### 7-1 段 1 固定の表(クラス → 今の名前)

#### なぜ要るか

`engine/state_hashes.py` の `_qual`(:89-91)は `型.__module__ + "." + 型.__qualname__` を、Enum(:155)・dataclass(:181)・名前つきの組(:187)・値のクラス(:218-220)のバイトに流します。final の定義は behavior-hash です(:42)【確認】。同じ形の名は、状態のファイル(`engine/state_codec.py` の `qualname` :124-126 と `allowed_class` :131-145。名から `importlib` で組み立て直す)、設定の指紋(`engine/resume.py` の `_canon` :90)、試験だけの系ごとの指紋(`engine/systems/probe.py` の `plain` :129)にも入ります。案 K の実測(300 体・120 刻みの mock)では、名に接頭辞を足すと final が `ca1c761a…` から `9d7fd317…` に変わりました(案 K の値。この役は回していない【未確認】)。

#### 足すファイル

`src/shibuya/engine/class_ids.py`(段 4 で `runtime/state/class_ids.py` へ移す)。

#### 表の形

```python
#: クラスの名の固定の表。鍵=今の「モジュール.クラス名」、値=凍結の名(ハッシュ・状態のファイル・設定の指紋に入る文字列)。
#: 段 1 では鍵と値が同じ。移す道具が鍵だけを書き換え、値は変えない。
CLASS_IDS: Final[Mapping[str, str]] = MappingProxyType({
    "shibuya.engine.arbiter.WakeCandidates": "shibuya.engine.arbiter.WakeCandidates",
    # … src(build を除く)の全部のクラス 480 行(道具で作る)
})
_PATH_OF: Final[Mapping[str, str]] = MappingProxyType({v: k for k, v in CLASS_IDS.items()})


def class_id(t: type) -> str:
    """型の凍結の名。"""
    name = f"{t.__module__}.{t.__qualname__}"
    return CLASS_IDS.get(name, name)


def class_path(frozen: str) -> str:
    """凍結の名 → 今の「モジュール.クラス名」(状態のファイルを読むときに import する先)。"""
    return _PATH_OF.get(frozen, frozen)
```

- 表に載せるのは src(build を除く)の全部のクラス 480 個(168 本)です【確認=AST】。そのうちハッシュに流れうる形が分かっているのは Enum 37・dataclass 211・名前つきの組 21 と、`VALUE_CLASSES` の値のクラス 4 です。全部を載せるのは、`_canon` が引数の物ならどの型でも名にするので、流れる型を前もって絞れないからです。表は AST の道具で作り、手で書きません。
- 代わりの案は、流れうる型(上の 269+4)だけを載せる形です。表は小さくなりますが、漏れた型は移したときに初めて byte-check で分かります。

#### 変える関数(4 ファイルの 5 つ)

| ファイル | 関数 | 今 | 段 1 の後 |
|---|---|---|---|
| `engine/state_hashes.py` | `_qual`(:89-91) | `f"{t.__module__}.{t.__qualname__}"` | `class_id(type(obj))` |
| `engine/state_codec.py` | `qualname`(:124-126) | 同じ形 | `class_id(t)` |
| `engine/state_codec.py` | `allowed_class`(:131-145) | 名を `rpartition` して import | `class_path(name)` を import し、`class_id(obj) == name` を確かめる |
| `engine/resume.py` | `_canon` の最後の行(:90) | `f"<{type(v).__module__}.{type(v).__qualname__}>"` | `f"<{class_id(type(v))}>"` |
| `engine/systems/probe.py` | `plain` の最後の行(:129) | `("obj", type(v).__module__ + "." + type(v).__qualname__)` | `("obj", class_id(type(v)))` |

変えないもの: `ALLOWED_CLASSES`(17)・`CLASS_FIELDS`(2)・`VALUE_CLASSES`(4)の鍵は凍結の名のまま残します。`engine/events/log.py:113` の `cls.__module__ != __name__` は同じモジュールの中の検査で、移すと両方が一緒に変わるので触りません。`systems/static_check.py` の `__module__` の比べは道の検査なので、段 2 と段 6 で直します。

#### 試験の形

`tests/engine/state/test_class_ids.py` と、凍結の JSON `tests/engine/state/class_ids_frozen.json` を足します(置き場は案)。

1. 網羅: src(build を除く)の全部のクラス(AST)の「モジュール.クラス名」が、表の鍵の集合と一致する。
2. 凍結: 表の値の集合が凍結の JSON(今の名 480)と一致する。値は足すだけで、変えない。
3. 1 対 1: 値が重ならない。`class_path(class_id(t))` が `t` の今の名に戻る。
4. 入口: 上の 5 つの関数が `class_id`・`class_path` を通る。4 ファイルに `__module__` と `__qualname__` を連ねる式が残っていない(AST)。
5. 動かしたふり: 試験の中で、値のクラス 1 つ(例 `WakeCandidates`)と Enum 1 つの `__module__` を書き換え、表の鍵をそれに合わせる。behavior-hash・full-hash・状態のファイルの中身・設定の指紋が、書き換える前と同じになる(案 K の実測を逆に確かめる形)。
6. 往復: `ALLOWED_CLASSES` の 17 の名が、全部 `allowed_class` で組み立てられる。

#### 見積り

src に足すファイル 1・変える関数 5(4 ファイル)・試験 1 本と JSON 1 本。import の書き換えは無く、4 ファイルに import を 1 行ずつ足すだけです。段 1 の表は鍵と値が同じなので、値は変わらない見込みです。byte-check 19 構成で確かめます。

### 7-2 名前を変えてはいけない文字列(段 2-1 で凍結する)

見た目はモジュールの道ですが、中身は ID です。移す道具が機械で置き換えると、乱数の列やハッシュが変わります。

| 種類 | 数 | どこ | 凍結の形 |
|---|---:|---|---|
| クラスの名 | 480 | 段 1 の表 | 段 1 の試験 |
| 乱数の領域の名 | 42 | `engine/run.py` の 3 つの表(母集団 `POPULATION_RNG_DOMAINS` 15・環境 `ENVIRONMENT_RNG_DOMAINS` 3・動き `MOTION_RNG_DOMAINS` 24) | 3 つの表の鍵の集合を JSON に凍結 |
| そのうち今のモジュールの道と同じ形 | 8 | `engine.processes.rail`(`rail.py:162`)・`engine.processes.environment`(`environment.py:112`)・`engine.chooser`(`chooser.py:64`)・`perception.attention.p_see`(`attention.py:227`・`renderer.py:171`)・`perception.p_notice`(`p_notice.py:477`)・`llm.mock`(`mock.py:70`)・`llm.mock.move_target` と `llm.mock.out_of_cell_target`(`mock.py` の接尾 `_MOVE_TARGET_DOMAIN_SUFFIX`・`_SHOP_TARGET_DOMAIN_SUFFIX`)。同じ文字列は `rng_audit.py` の表(:238・239・243・247・310・312・477・482)と `run.py` の表にもある | 定義の 7 か所と接尾 2 つの値を JSON に凍結(道によらず値で引く) |
| 版の ID | 70 か所・52 本(build を除くと 41 本) | 引用符つきの `shibuya.〜/〜` の grep(docstring を含む)。docstring の外の AST では文字列 61 か所とバイト列 8 か所で、残りの 1 か所は docstring の中(`build/sched/trial.py:137`) | 値の多重集合を JSON に凍結(道によらない) |
| ハッシュと指紋の見出し(バイト列) | 9 | ランの側 7: `agents/population.py:219`・`agents/weekly.py:245`・`core/soa.py:398`・`economy/ledger.py:951`・`engine/state_hashes.py:39`・`engine/tape.py:128`・`perception/hashes.py:52`。build 2: `build/sched/trial.py:131`・`build/sched/w17_schedule.py:90` | 同じ JSON。案 K は `state_hashes` の 1 つだけを挙げていた |
| 道と同じ形のほかの名 | 2 | manifest の節の名 `economy.stage2`(`manifest_sections.py:197`)・`shibuya.cache_salt`(`llm/fleet.py:200`) | 同じ JSON |

- 凍結の試験は `tests/engine/time/manifest_keys_frozen.json` と同じ形にします(案 K §6-2)。src を AST で見て、値の集合が JSON と同じことを確かめます。道や行の番号は鍵にしません。
- 移す道具の除外の一覧には、この表の値を全部入れます(42+70+9+2。重なりは除く)。道具の試験で、除外の値が 1 つも書き換わらないことを確かめます。

### 7-3 段 2 の残り(下ごしらえ・結果は変えない)

- **2-2 根の道を 1 か所に**: `core/paths.py` を足し(段 4 で `foundation/paths.py` へ)、リポの根と包みの根を返す関数を置きます。集めるのは、ランの側で `Path(__file__)` を使う 11 行です。深さを決め打ちした 9 行は `bridging/ledger.py:294`(parents[4])・`bridging/scan.py:293`(parents[2]=包みの根)・`calendar.py:150`(parents[3])・`classical.py:91`(parents[3])・`energy.py:228`(parents[3])・`resume.py:221`(parents[3])・`rules/table.py:260`(parents[4])・`systems/allow.py:70`(parents[2]=包みの根)・`systems/static_check.py:225`(parent)です。`here` から辿る 2 行は `core/budget.py:71`・`world/processes/constitution.py:142` です。`calendar.py` の `REPO_ROOT` と `resolve_repo_path`(読み手は `economy/wages.py:159`・`economy_stage2.py:383`・`:582`・`resume.py:106` と試験 1 本)も paths へ出す案です。こうすると economy から暦への辺と、runtime の核から暦への辺(§6-6)が消えます。build の 7 行は動かないので触りません。
- **2-3 書きの許可の一覧の形**: `systems/allow.py` の `index` は `base / "engine" / "resolve.py"` の 1 本を AST で読みます。これをファイルの一覧(案 K の `RESOLVE_FILES`)を読む形にします。段 2 では一覧は 1 本で、段 6 で割り先を全部載せます。`systems/static_check.py` の `RESOLVE_MODULE`(:37 `shibuya.engine.resolve`)・接頭 `shibuya.engine.systems.`(:62・:208)・`shibuya.engine`(:79)は、モジュールの `__name__` から作る形にします。試験は、書きの許可の集合が段の前と同じことを確かめます。
- **2-4 乱数の検査の道**: `engine/rng_audit.py` の `endswith("core.rng")`(:80)と `"shibuya.core.rng"`(:406・:409)を、`core.rng.__name__` から作る形にします。直さないと、移した後に検査が呼び手を見落とします。道の表 44 行は段 4 の道具で直し、用途名は変えません。
- **2-5 世界カタログの包みの名**: `manifest/world_catalog.py:61` は `importlib.resources` に包みの名 `shibuya.manifest` を渡します。`__package__` から作る形にしておき、段 4 で JSON(`manifest/frozen/world_catalog_v0_2.json`)と pyproject の `package-data` を一緒に動かします。
- **2-6 封印の守り(§3 の直し 4・試験だけ)**: ① 封印の語の AST の検査を足します。ランの側の src の文字列に封印の語を置かない検査で、今の 3 か所(§5-3)は理由つきの許可の一覧に載せます。② mock の短いランを `ReadGuard.sealed_only()`(`tools/instruments/read_guard.py:168`)で包み、封印の層を開かないことを確かめる試験を足します。`tests/build_sched/test_w20_calendar_1a.py:565` と同じ形です。語の表をどちらにするかは聞きたいこと 5 です。
- 段 2 の終わりに byte-check 19 構成を回します。

### 7-4 段 3〜段 8 と見積り

直す import の文は、`shibuya` を読む import の文のうち、その段で動くモジュールを読むものの数です(文の数。名の数ではない)。

| 段 | 中身 | 動かすファイル | 直す import の文(src / build / tests / tools) | ほかに直すもの | 試験と止める所 |
|---|---|---:|---|---|---|
| 3 | 移す道具 `tools/pkgmove/`(新)。最終の表から作る対応表 TOML 1 本(今の道 → 新しい道・割る記号の割り先)。AST で import を書き換え、再輸出の頭を通る import は元のモジュールへ向ける。道の文字列の表(§7-5)を書き換える。§7-2 の除外の一覧は触らない。書き換えの報告を出す | 0(src は変えない) | — | — | 道具の試験(一時のコピーの木で回し、import の文と道の文字列の行のほかは 1 バイトも変わらない・除外の値が残る) |
| 4 | 割らないファイルを移す。包みごとに 10 の小さな段(foundation 38 → world 54 → economy 3 → act 3 → mind 27 → society 8 → interim_bundles 17 → runtime 36 → experiments 10 → validation 6。消す 2 本は最後) | 204(`.py` 201・JSON 1・消す 2)。道が変わらない 16 本(economy の 15 本と `world/__init__.py`)は動かさない | 855(179 本)/ 38(30 本)/ 1,378(349 本)/ 52(28 本)。再輸出の頭を通る import は別に 10 / 14 / 40 / 3 | 新しい頭 28(付属の表に無いディレクトリ)。古い頭は空にし、古い包みに割るファイルが残る間は残す(再輸出の口は残さない。10-13b §0-6)。固定の表の鍵。道の文字列(§7-5) | 小さな段ごとに byte-check。段 4 の終わりに pyproject の import の決まりを差し替える(§6-4 の 8 つと §6-6 の 2 つ。移すだけの 28 本は「消える段」の注つきで ignore に載せる)。心の読みの一覧の試験(別紙 §9)を新しい道で入れる |
| 5a | 語彙・型・定数を下ろす割り(17 本: `agents/state`・`poi_target`・`change_detect`・`calendar`・`events/body`・`tools/record`・`tools/registry`・`world/assets`・`llm/mock`・`llm/undefined`・`llm/__init__`・`llm/fleet`・`llm_bridge`・`chooser`・`attention`・`relations`・`arbiter`) | 17 本を割る | 200(84 本)/ 1 / 339(180 本)/ 13(9 本) | 固定の表の鍵を割り先に合わせる(`WakeCandidates`・`AgentState` ほか) | ファイルごとに byte-check。ignore から 11 本を消す |
| 5b | 大きな部品の割り(5 本: `commit`・`presence`・`run`・`cli`・`calendar_shadow`)。`shibuya/cli.py` は入口の 1 行として残す | 5 本を割る | 43(23 本)/ 0 / 389(189 本)/ 11(6 本) | 同上 | ファイルごとに byte-check。ignore から 2 本を消す |
| 6 | `engine/resolve.py` を 18 の割り先へ | 1 本を割る | 27(27 本)/ 0 / 59(55 本)/ 3 | `systems/allow.py` の一覧に、割り先の書き手のファイルを全部載せる | byte-check。書きの許可の集合が同じ試験。ignore から 8 本を消す |
| 7 | `perception/renderer.py` を 7 の割り先へ。先に `perceive` の副作用の順の試験を入れる(下の注) | 1 本を割る | 10(7 本)/ 0 / 52(40 本)/ 1 | `prepare_tick` と `__init__` を world の側と mind の側に分ける | 副作用の順の試験を割る前の commit で通す。byte-check。ignore から 2 本を消す |
| 8 | 古い頭と古いディレクトリを消す(`engine/`・`perception/`・`llm/`・`agents/`・`core/`・`manifest/`・`census/`)。tests の置き場を変える(案 K の付属の表 §3) | 古い頭 | tests の `parents[N]` 128 か所(124 本)と `conftest.py` の `REPO_ROOT` | ignore を例外 T1〜T8 と注釈だけ(`TYPE_CHECKING` へ移す)にする | byte-check。割った後の辺・循環・原則に反する辺をここで数える |

- 段 7 の注(照らし合わせの案 F の注意書き): `perceive` の docstring(`renderer.py:1466-1468`)は副作用の順を「看板の注視の抽選と計数 → 露出の控え → 閉店の 1 句 → B3 の命中の計数と天気 → 近接の同点の計数 → 想起」と書いています。割る前に、乱数の引きの列・計数の列・呼ばれた口の順を記録して比べる試験で、この順を固定します。`Renderer` を割るのは最後です。
- 段 4 を包みごとに分けるのは、1 つの段の差を読める大きさにするためです【見立て】。import の書き換えは道具がするので、順には依存しません。byte-check の費用が重ければ、まとめて 1 段にもできます。
- 割るファイルは、その割りの段まで古い置き場に残ります。だから段 4 の後は、古い `engine/` などに割るファイルだけが残る途中の形になります。
- import の時に表へ足す形(登録の順で中身が決まる形)は、src に見当たりませんでした【確認=grep】。`engine/events/log.py` の原因の型の検査(`__init_subclass__`)は置き場に依らない形です。それでも、頭の再輸出を消すと import の順が変わるので、段 4 の byte-check で確かめます。

### 7-5 道筋を文字列で持つ所の数と直し方(案 K §6-3 の数え直し)

| 場所 | 案 K | 数え直し | 働き | 直し方 |
|---|---|---|---|---|
| `engine/state_ledger.py` の `OWNER_CLASSES`・`OWNER_ALT_CLASSES`・`_ALLOW_*` | 91(76・6・9) | 92(76・7・9) | 機能する(クラスの属性の網羅・読み手の許可) | 段 3 の道具で直す。割るファイルは、`contains` の文字列を含む新しいファイルを AST で探す |
| 同じファイルの `basis`(`_SOA`・`_EXT`) | 279(105・174) | 文字列 186(99・87)・道の出てくる数 273(105・168) | 記録の文。試験は空でないことだけを見る | 直さない。当時の記録だと見出しに書く |
| `engine/state_ledger_ast.py` | 51 | 53(`EXT_AST_ALLOW` 18・`DIAG_EXITS` 16・`UNRESOLVED_ALLOW` 7・`GENERIC_FILES` 5・`DECL_FILES` 3・`RESULT_FILES` 3・関数の中 1) | 機能する | 段 3 の道具で直す。検査 4 が「当たらない許可」を落とすので、漏れは試験で分かる |
| `engine/rng_audit.py` | 43 | 道 44(`SAFE_SITES` 26・`UNDETERMINED_SITES` 17・関数の中 1)と、`core.rng` の名 3(:80・:406・:409) | 機能する(道・関数・用途名) | 道は段 3 の道具。`core.rng` の 3 つは段 2-4。用途名は変えない |
| `engine/systems/allow.py`・`static_check.py` | 5 | allow: 道の結合 1・`parents` 1。static_check: `RESOLVE_MODULE` 1・接頭 2・`shibuya.engine` 1 | 機能する(起動時に AST で読む) | 段 2-3 と段 6 |
| `engine/state_codec.py`・`state_hashes.py` のクラスの名 | 23 | 23(17・2・4) | ハッシュと状態のファイル | 段 1 の固定の表(鍵は凍結の名のまま) |
| `world/processes/absent.py`・`inputs.py`・`engine/body/rules.py`・`bridging/scan.py`・`events/log.py`・`defect_fixes_1103.py`・`cli.py` | 31 | 30(14・10・2・1・1・1・1) | 宣言の文・根拠の文【試験が読むかは確かめていない】 | 段 3 の道具で直すか、当時の記録と書く |
| `manifest/world_catalog.py` の `importlib.resources` の包みの名 | (pyproject の側で数えた) | 1(:61) | 機能する | 段 2-5 |
| `Path(__file__)` | src 14 行(ほかに `here` 4 行) | ランの側 11 行(深さの決め打ち 9・`here` から辿る 2)・build 7 行(動かない) | 機能する(`docs/`・`data/` への道) | 段 2-2 |
| src の docstring の中の道 | (別) | 91 か所(61 本) | 記録 | 直さない |
| src の import の文 | (名で 2,523) | 1,181 文(192 本・build を除く)。build の 38 文も動くモジュールを読む | import | 段 3 の道具 |
| tests の道の文字列 | 205(50 本) | 250(定数 229・文の中 21・56 本) | AST の検査・読み手の表 | 段 3 の道具の対応表 |
| tests の `/ "engine" / "x.py"` の結合 | 98(32 本) | 144(79 本。src の上の段の名を含む `/` の連鎖を数えた) | 同上 | 同上 |
| tests の点の区切りの道 | 130(39 本) | 126(定数 69・文の中 57・36 本。版の ID は除いた) | 同上 | 同上。ID は除く |
| tests の import の文 | 2,556(394 本) | 2,605(401 本) | import | 段 3 の道具 |
| tests の `parents[N]` | 133 行 | 128 か所(124 本)。`Path(__file__)` の行は 149 | 試験の根の道 | 段 8 まで tests を動かさないので変えない |
| tools の Python | 道 6・結合 4・点の道 6・import 97(33 本) | 道 12(7 本)・結合 6(4 本)・点の道 7(5 本)・import 109(44 本)・`Path(__file__)` 19 | 同上 | 段 3 の道具 |
| tools の Python でないファイル | 道 59・点の道 17(3 本) | `shibuya.` か `src/shibuya` を含むファイル 7 本(`night5070/experiments.json`・`night5070/README.md`・`c7`・`c8` の JSON 4 本・`vocab/synonym_policy_v0.json`) | 文字列の引数(`-m shibuya.cli` など) | `shibuya/cli.py` の入口を残せば多くは要らない。残りは段 3 の報告で見る |
| `pyproject.toml` | 34 | `shibuya` を含む 21 行(import の決まり 5 つ・`package-data` の `shibuya.manifest`・`filterwarnings`) | 決まりと資産 | 段 4 の終わりに差し替える |
| `.github/workflows/ci.yml` | 0 | `lint-imports` の 1 行 | — | 要らない |
| docs | 273 本 | 462 本(`src/shibuya/` か `engine/〜.py` に触れる) | 記録 | 直さない。索引に今の道と新しい道の対応表を 1 枚置く |
| 系の表の属性の道(`O39:conv.sessions` など) | なし | 数えていない | ファイルに依らない | 変えない |
| byte-check の道具 `tools/bytecheck/tree.py` の `ROOT_READERS`(リポの根から読む src のファイル) | (案 K の後にできた) | 15(ランの側 11・build 4) | 機能する(道具の試験が src の AST と突き合わせる) | 段 2-2 と段 4 で直す。道具は別の役の持ち物なので、その役と一緒に直す |

数え方が案 K と違う所があるので(この役は文字列の定数を単位にし、build の道と版の ID を外した)、数が少しずれています。どの行も、直す必要があるかの判断は案 K と同じです。

## 8. 残る問いと聞きたいこと

### 8-1 聞きたいこと

1. **連絡の器 4 本の置き場**: `contact/deliver.py`・`calls.py`・`chat_state.py`・`tools.py` は、問い 3 の「運ぶ器(配達)」に当たります。import は foundation と society(会話・発話の口・道具の台帳)だけで、今 society に置いても新しい違反は出ません【確認】。この表は照らし合わせの数(束ねの 17 本を一時の区分へ)に従い、一時の区分に置きました。今 society に置くか、v3 で割るときまで一時の区分に置くかを決めてください。
2. **`apply_detection` の扱い**: (a) act に置く(この表)。心の欄の内受容の段 3 列も act が書く形が残ります(案 K の表では、act はもともと焦点の列と `hunger_stage` を書いています)。(b) 段 6 で 2 つの関数に割る(`cells.b4_hash` は act・段の列は `mind/ops.py`)。呼ぶ順を保てば結果は変わらない見込みですが、移すだけではなくなります。(c) 案 K のとおり `mind/ops.py` に置き、書きの文の例外として宣言する。
3. **runtime の核の範囲と、残る 1 本**: 核を §6-6 の候補(時計・状態の保存とハッシュ・テープ・進行役と系の宣言の型)とすることでよいか。残る `runtime/clocks/speech.py` → `society/speech/port.py` の `mora_count`(モーラの数を数える文の道具)を、割る段で foundation の文の道具へ下ろすか、例外として宣言するか。
4. **走査の道具の自己更新の規則を直すか**: `state_ledger_ast._is_self_update` は、左辺が `self.price` でも右辺の `world.pois.price` を自己更新と見なして外します(別紙 §4-1)。直せば店の値段の 1 か所が strict に入ります。直すなら、心の読みの一覧を試験で固定する前(段 4 の前)に直すのがよいと考えます【見立て】。直す作業は src の変更で、検査の結果だけが動き、ランの値は変わらない見込みです。
5. **封印の語の表が 2 つある**: `build/audit/w19_freeze.HOLDOUT_TOKENS` と `tools/instruments/read_guard.SEALED_TOKENS` は別々の表です。段 2-6 の AST の検査はどちらを正にするか、1 つにまとめるか。中身は開いていないので、2 つが同じかは確かめていません。封印の層に触る作業なので、先に聞きます。
6. **`python -m shibuya.engine.run` の入口**: 案 K は「interfaces へ移すか消す」と残しました。今この入口を文字列で使うのは `tests/c7/test_accept_table.py` の 1 か所だけです(grep で見つけただけで、中身は開いていない)。移すか消すかを決めてください。
7. **一時の区分の読み手を限る決まり**: 一時の区分を読めるのは runtime と interfaces だけ、という決まり(§6-6 の 1)を足すか。今は外の読み手がこの 2 つだけなので、足してもコードは変わりません。

### 8-2 残る問い(今は決めなくてよいもの)

- 返事その 6 §3-2 の削除の結果: 切替口のファイル(`absent_processes`・`rate_rules`・`defect_fixes_1103` ほか。10-25 §6-1 の (i) の一覧はこの役は読んでいない)がファイルごと消えるか、中の旧道だけが消えるかで、付属の表の行が変わります。
- foundation を foundation と contracts に割るか(案 K の異論 4): 移した後に決めます(返事その 7 §4-1)。
- v3 の段に回したもの: 例外 T1〜T8 の消し方(案 K §4-5)・`presence` を 3 つに割る案(案 K §2-8)・`conversation` の 4 つの割り(案 F)・`constitution` の検査と定数の割り(案 F)・`experiment/gate` の依存の逆転(案 F)・`llm/contract` の書式の切り出し(案 F)・連絡帳と予定の持ち物への移し(問い 3 の到達点)。
- 到達点(問い 1・2・5・6 の C の形)は、9-2・9-3c・9-5 と v3 の段で入れます。

## 9. 確かめていないこと・限界

- byte-check の道具(`tools/bytecheck/`)はこの作業木に無く、本体の作業木の途中の版(未 commit)の README と表の頭だけを読みました。19 構成の中身と、道具が移した後の木でそのまま回るかは確かめていません。
- ラン・pytest・lint-imports は回していません。1 バイト不変かは確かめていません。案 K のハッシュの実測(`ca1c761a…` → `9d7fd317…`)も回していません。
- 辺はモジュールの対で数えました。案 K の名前を追う数え方(注釈だけを分ける)とは違います。割った後の数は数えていません(§6-5 は見込み)。
- 関数の単位の割り先は案 K の作業の表を引きました。付属の表の行数は案 K の数で、この役の数えとは割り先によって少しずれます(例えば `renderer.py` の `world/model/percept_scene.py` は案 K 1,137 行・この役 1,332 行)。どの記号がどこへ行くかは同じです。
- 案 F の文書そのものは読んでいません。案 F の置き場は照らし合わせの要約から取りました。
- 返事その 6 §3-2 の削除の対象の全部は読んでいません。
- tests/c7 は中身を開いていません(grep の当たりのファイル名だけ)。
- 列の持ち主の分け方は案 K のままです。
