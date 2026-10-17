# 土台 8 つの口の約束と受入の試験(第 1 期 1-1〜1-9+1-8b・確定・2026-10-13)

- 位置づけ: [回答 10-12b](v2-answers-2026-10-12b.md) §6-2「口の約束を先に」=実装役に渡す前に、親が各土台の **口(型・関数・欄の名)・約束(不変条件と結果不変の範囲)・受入の試験** を書く。段の中身は [実装の計画](v2-implementation-plan-2026-10-12.md) 第 1 期の表が正。決定は [指示書 10-12](v2-wallbounce-decisions-2026-10-12.md)(§0-3 土台の一覧・CP12・CP4・CP2・TM7・TM8・DM-0・CT0/CT5/CT9/CT10・MR-0/MR11/MR16・§1-13)。
- 乗せ先: 1-0 の箱と系([impl-1-0.md](../bench/analysis/wallbounce-1012/run-day-decomp/impl-1-0.md))。土台が足す状態は、状態台帳の軸(軸 1 behavior/diag/no・軸 2 required/discardable)を**足す前に決めて**宣言する(草案 §2-8 の注)。
- 状態: **確定(第333)**=[回答 10-13b](v2-answers-2026-10-13b.md) §3 で〔空欄〕を全部決定(各段の末尾の〔決定〕)・§1 1-5 で 1-8b(発話の口)を追加・§4-2 で 1-2 の知覚の欄を追加・§3 の K17 は親案を変更。試験の名は案(実装役が記録で確定)。順は依存の順(1-1 → 1-3 → 1-4 → 1-5 → 1-2/1-6/1-7 → 1-8 → 1-8b → 1-9)。T0(1-1)だけ先に 1 本で通し、残りは実装役ごとの作業木で並べる(§6-3)。作業木を並べる前に 1-0b(3-2-4 の試験の整備)を 1 commit で(第333)。自律運転(10-13b §0): 止まる地点 S1〜S8 以外は親が進め、仮採用は PENDING §1-1 に残す。
- 全部に共通の約束: **◎ 結果不変**(byte-check 19 構成・2 日・再開・系ごとの指紋が HEAD と同じ。切替口で新しい道を選ばない限り既定の final は 1 バイトも動かない)/ 新しい状態は状態台帳に行を足し、`SYSTEMS` の宣言(`writes.soa`・`writes.paths`)に書き手を足す(段 B で宣言の外 0)/ 新しいつなぎは台帳(1-4)に「外す段」つきで載せる / 用語は [用語集](v2-glossary.md)。

## 1-1 時計 T0(TM7・TM8)

- **口**: `core/types.py` の時刻の型(ナノ秒の整数=既存)を `SimTime`(別名)として正にし、`TickCtx` に `t_ns`(通しのナノ秒)・`day`・`tod_s`(その日の秒)を足す。既存の `T`(tick)・`td` は**残す**(1-1 では値の意味を変えない=60 秒で同じ値)。時間の定数は `core/time_consts.py` に集め(`SECONDS_PER_DAY`・`TICK_SECONDS=60` ほか)、`1440`・`// 60`・`* 60` の直書きを置き換える。乱数の鍵は 10c の counter のまま(TM7 (d)「出来事の時刻と中身に結びつける」は鍵の**材料**を `t_ns` に替える準備だけ=鍵の値は不変)。
- **約束**: (1) `tod_s == td * 60` と `t_ns == T * 60 * 1e9` が全 tick で成り立つ(試験の道具で検算)。(2) 直書きの数は 0(AST の試験が数える。残すものは allow の表に理由つき)。(3) 「tick」の語はコードの識別子と docstring から消し「刻み」「計算のまとめ」に(名の置き換えは別名で段階的に・ハッシュに入る名=台帳の鍵・道筋・持ち主は**変えない**=1-0 の規則)。(4) byte-check 19 構成 不変。
- **受入の試験**: `test_t0_time_consts.py`(定数の値と直書き 0)・`test_t0_tickctx_equivalence.py`(T/td と t_ns/tod_s の同値)・`test_t0_no_tick_word.py`(識別子の語の検査・allow 表)・既存の 10a/10d の時刻の試験が全部通る・byte-check。
- **依存**: 1-0。**空欄**: 〔1〕「tick」の語をハッシュの鍵に持つ道筋(`tick_ms_max` など)は変えないので語が残る=allow 表に載せる(ユーザー確認は不要・報告だけ)。〔2〕`phase` の計時の鍵(壁時計)は語の置き換えの対象外。**〔決定(10-13b §3)〕〔1〕〔2〕とも親案どおり(allow 表と報告だけ)。** 〔第333 追加〕TM9 の欄(GPU 無し: 判断モデルと LLM を分けた呼び出し数・時計の種類・つなぎの台帳の数)を manifest と日次の記録に 10f と一体で足す(計画 1-1)。

## 1-3 出来事の記録(CP12・CT9・5W1H)

- **口**: `engine/events/log.py`: `Event`(凍結の dataclass: `id`(通し・決定的)・`t_ns`・`who`(体の id か持ち主の名)・`what`(種類の語=小さな語彙表)・`whom`・`where`(セル/ノード/POI)・`how_much`・`via`(道具の欄 CT9: 対面/通話/メッセージ/グループ/SNS/無し)・`received_ns`/`read_ns`(届いた/読んだ)・`origin`(範囲の外からの印)・**`cause`**=3 種類だけ(`llm_call(call_id, input_event_ids)`・`process(name)`・`experiment(cond_id)`))。書く口は `EventLog.append(ev)` 1 つ。**実験の条件 `experiment` を書けるのは `engine/experiment/gate.py` の 1 関数だけ**(CP12=他の場所から `cause=experiment` を作れないことを AST と実行時の両方で強制)。A〜D(体・世界・お金・物)は毎回、E(診断)は区切りで。
- **約束**: (1) 記録の有無で final・テープ・behavior-hash 不変(記録は軸 1 diag・軸 2 discardable=状態台帳の新しい行)。(2) 既存の ActualLog・金と物の生ログ・テープは消さず、`Event.id` への目印で結ぶ(載せ替えは後の段)。(3) 1 日の記録の行数と種類の分布を manifest に出す(計器)。(4) 記録の書き口は系の宣言 `writes.paths` に `E:events.*` として載せ、段 B で捕まる。
- **受入の試験**: `test_e_log_schema.py`(欄・凍結・id の決定性)・`test_e_cause_three_kinds.py`(第 4 の種類を作れない・`experiment` を gate の外から作ると AST と実行時で落ちる=負の対照 3 本)・`test_e_log_invariance.py`(記録 on/off で final 同じ・19 構成の byte-check)・`test_e_log_links_actual.py`(ActualLog の行と 1 対 1 に目印が付く)。
- **依存**: 1-1(時刻の型)。**空欄**: 〔1〕`what` の語彙表の最初の中身(行為の語彙 12 語+過程の名+お金の科目+物の出入り=親案)。〔2〕E(診断)の「意味のある区切り」の定義(日の締め・checkpoint=親案)。**〔決定(10-13b §3)〕〔1〕〔2〕とも親案どおり。** 1-8b の発話(届け先の行)もこのログに書く。

## 1-4 規則の表とつなぎの台帳(CP10・CP5-5・PlanSpec)

- **口**: `engine/rules/table.py`: `Rule`(`id`・`kind`=機械が守らせる/人が取り締まる・`source`(法令名・条・版・URL)・`asof`・`params`・`applies_to`(PlanSpec の条件の形を参照))。読み口 `Rules.get(id, asof)`。中身は E4(R-106)の後に 4-2 で入れる=1-4 では**器と 2〜3 行の実在の規則**(例: 消費税 7.8%+地方 22/78・最低賃金 1,280 円 2026-10-01=R-106 で親検収済)だけ。`engine/bridging/ledger.py`: `Bridge`(`id`・`what`・`why`・`remove_at`(外す段)・`declared_in`・`conf`)と台帳の CSV/JSON(`docs/design/bridging-ledger.json` を git に=計器の最初・CA8)。manifest に `rules_version`(表の sha)・`bridges_count`・`run_kind`(CP5-5: 再現/反実仮想/腕/試験)。
- **約束**: (1) 規則の表を読んでも挙動は変わらない(1-4 では読み手を作るだけ・既存の直書きの係数は 4-2 まで残す=つなぎとして台帳へ)。(2) つなぎの台帳の件数が計器盤の最初に出る(#88 の 6 件+西武の 1 部屋+既存の 9 件=16 件=親の数え・確認要)。(3) manifest の鍵の集合が増えるだけで既存の欄の値は不変。
- **受入の試験**: `test_rules_table_schema.py`(出典と版が必須・asof で引ける)・`test_bridging_ledger.py`(全行に `remove_at` がある・コードの `expedient` の宣言と台帳の行が 1 対 1=AST で `conf="expedient"` を数えて突き合わせ)・`test_manifest_rules_bridges.py`・byte-check。
- **依存**: 1-3。**空欄**: 〔1〕つなぎの台帳を docs(git)に置くか data に置くか=親案 docs(件数が計器なので履歴が要る)。**〔決定(10-13b §3)〕docs(git)に置く。** 〔第333 追加〕不応期 11 種と起床条件のクラスは「T3 で外す」として台帳に載せる(10-13b §4-2 の 2)。

## 1-5 権利台帳の器(CP4・CP3)

- **口**: `engine/rights/ledger.py`: `Right`(`holder`・`object`・`kind`=所有/賃借/雇用/許可・`since_ns`/`until_ns`・`counterparty`・`source`・`cause`(5W1H=1-3 の Event.id))。読み口 `Rights.holds(holder, kind, object, t)`。最初の中身は計画 1-5 の 4 つ(雇用=W16 `org_id`・営業許可=区のオープンデータ(取得は許可の一覧の中・無ければ空欄)・店の賃借=区画にいること(家賃は空欄・宣言)・住まい=国勢調査の割合)。`staff_of_poi` の丸振りを台帳からの読みに置き換える。**権限で止める検査**(`resolve.py` の `NO_PERMISSION`・`llm_bridge.py` の役割語)は「物理と機械の決まった動き」だけに縮め、権利に反する行動は止めずに `Event(cause=…, what="unauthorized_act")` として記録。
- **約束**: (1) 今の既定で `NO_PERMISSION` が当たっている回数を**先に数える**(当たっていれば縮めると結果が動く=▲ として第 2 期へ=計画の門のとおり)。当たっていなければ ◎。(2) `staff_of_poi` の置き換えは同じ割り当てを返す(byte-check)。(3) 台帳の行数と種類の分布を manifest に。
- **受入の試験**: `test_rights_schema.py`・`test_rights_from_w16.py`(雇用の行数=W16 の `org_id` を持つ体の数)・`test_staff_of_poi_equivalence.py`・`test_no_permission_count.py`(19 構成で当たった回数=0 を確かめる・0 でなければ記録して止まる)・byte-check。
- **依存**: 1-3・1-4。**空欄**: 〔1〕営業許可の区のオープンデータの有無(`city-shibuya-data.opendata.arcgis.com` は許可の中)。〔2〕`NO_PERMISSION` が 0 でなかったときの扱い(計画どおり ▲ として第 2 期)。**〔決定(10-13b §3)〕親案どおり。営業許可のオープンデータは許可の一覧の中で探し、無ければ空。`NO_PERMISSION` が 0 でなければ ▲ として第 2 期に回す(1-5 の残りは止めず、縮める部分だけを腕にして進める)。**

## 1-2 知覚の分離(§1-13・B0〜B6 の構造化)

- **口**: `perception/facts.py`: `Percept`(構造のある事実=見えた物(id・種類・距離・向き)・人(id・向き・行為)・音(段)・時刻の見方・体の段)を描画の**前**に作り、`renderer` は `Percept → 文`(B0〜B6)の 1 つの描き方にする。目の向き・心の向き・持ち物・道具の状態の**欄だけ**用意(値は後の段=空)。**〔第333・10-13b §4-2〕起床 3 種(近接入替・被注視・傍受)と知人出現は起床の条件ではなく知覚の事実**: `Percept` に `watched_by`(誰が見ているか)・`heard_speech`(聞こえる会話=1-8b の `Utterance` への目印)・`nearby_change`(周りの顔ぶれの変化)・`acquaintance_seen`(知人の出現)の欄を作り、値は空で始める(値を作る仕組みは空間の段=距離・視線・遮蔽表)。「本人の予想」と「今の観測」を並べて判断の入力に載せる形は 1-8 と合わせてここで作る(驚くか・何をするか・よく考えるかは判断モデルが決める=10-03 §7)。`p_see × 0.49`・歩きスマホ `0.46` の係数は消す(値はパターン台帳 §10 の検証専用へ=§1-6)。
- **約束**: (1) 描画のバイトが 19 構成で不変(Percept を経由しても同じ文)。(2) 係数を消しても既定で結果が動かないことを**先に確かめる**(動くなら ▲=計画の門「描画のバイトが不変」に反するので止めて報告)。(3) `Percept` は軸 2 discardable(tick の中の一時=`TickScratch` の欄)。
- **受入の試験**: `test_percept_schema.py`・`test_render_from_percept_bytes.py`(19 構成 × 代表 tick で描画のバイト一致)・`test_coef_removed.py`(係数が無い・consts に残らない)・byte-check。
- **依存**: 1-0(scratch の欄)。1-1 と並べる。**空欄**: 〔1〕`p_see × 0.49` を消すと既定の結果が動くかは未計測=1-2 の最初に測る(動けば計画の門に従い ▲ として報告)。**〔決定(10-13b §3)〕最初に測る。動けば ▲ として報告し、10-13b §0-3 に従って進める(係数を消した道は腕・既定は今の値のまま=戻せる形)。**

## 1-6 記憶の器 M0(MR-0・MR11・MR16)

- **口**: `engine/memory/store.py`: 記憶の行は **出来事ログへの目印**(`event_id`)+`strength`(System 1 の数値=MR-0・LLM には見せない)+`annotation`(一人ずつの注釈)+`origin`(出どころの欄=範囲の外からの印)+`shown`(録画の欄=この呼び出しで見せたか MR16)。既存の `mem_*` 列(SoA 9 列)は**残し**、新しい器は腕 `--memory-store events`(既定は今のまま)。LLM に見せるのは言葉(はっきり/うろ覚え)と中身の粗さ(MR-0)=描き方は 1-2 の `Percept` の記憶の欄。
- **約束**: (1) 既定の final 不変(器は腕の裏)。(2) 腕 on で、今の `mem_*` の想起と新しい器の想起が同じ候補を返す(同値の試験)。(3) `shown` の録画がテープの列に増えるだけ(テープ版は上げない=列の追加は版 4 の中で可か〔空欄〕)。
- **受入の試験**: `test_m0_store_schema.py`・`test_m0_recall_equivalence.py`(腕 on/off で想起の候補が同じ)・`test_m0_shown_recorded.py`・byte-check(既定)。
- **依存**: 1-1・1-3。**空欄**: 〔1〕テープの列の追加が版 4 の中で許されるか(10e の E5 で版 4 に 7 列を足した形と同じなら可=親案 可)。**〔決定(10-13b §3)〕版 4 の中で可。**

## 1-7 道具の台帳 C0(CT0・CT5・CT9・CT10)

- **口**: `engine/tools/registry.py`: `Tool`(`name`・`known_by`(知っている/知らない)・`requires`(要るもの)・`affects`(体と知覚への影響の欄)・`owner`・`content_writer`(中身を書くのは誰か))。個人の連絡先は関係の記憶に手段ごとの印(CT5・家族と職場は初めから)。店の番号は場所の表。グループの一覧(家族・職場は実データ=W16)。記録の欄(CT9)は 1-3 の `Event.via`・`received_ns`/`read_ns`・`origin`。看板の文に「作り物」の印(つなぎの台帳へ)。
- **約束**: (1) 既定の final 不変(C0 は器だけ・C1 の会話とメッセージは第 6 期)。(2) グループの一覧の行数=W16 の世帯数+事業所数(検算)。(3) 看板の作り物の印は描画のバイトを変えない(印は記録にだけ)。
- **受入の試験**: `test_c0_tool_registry.py`・`test_c0_groups_from_w16.py`・`test_c0_contacts_in_relations.py`・`test_c0_signboard_mark_invariance.py`・byte-check。
- **依存**: 1-3・1-5・1-2。**空欄**: 〔1〕店の番号の「場所の表」の出どころ(OpenPOI か OSM の `phone` タグ=許可の中)。**〔決定(10-13b §3)〕OSM の `phone` タグから作る(ライセンスを増やさない)。**

## 1-8 候補の口 J0(DM-0・DM4・DM5・DM13・C-2)

- **口**: `engine/decision/port.py`: `Candidate`(`id`・`kind`・`text`・`source`=5 つの源(経験/周りが示すできること/近い予定/続ける/よく考える=DM-0)・`number`(番号は最後=C-2))と `DecisionPort.choose(ctx, candidates) → Choice`(番号で返す・「その他(自由記述)」の割合の欄・驚き 0〜5 と迷いの欄=DM5・連続値への変換 DM13)。**判断モデルと LLM で 1 つの口**。短い版と長い版は同じ仕組み(共通部分を前に=DM4)。mock と古典モデル(G)は同じ入口の別実装。今の「文 → 2 行形 → パーサ → 語彙」は口の後ろに残す(腕 `--decision-port`・既定は今の道)。順のシャッフルと並べ替えの試験(C-2 の対策 4 つ)。
- **約束**: (1) 既定の final 不変(腕の裏)。(2) 腕 on で mock の行動の分布が今と同じ(同じ乱数の鍵から同じ番号=同値の試験)。(3) 候補の源 5 つの**どれから来たか**を記録(1-3 の Event.cause の `llm_call` の入力の出来事に候補の id)。(4) 「ひと言」(発話)の欄は、会話の行だけに戻す=**1-8b(下)**(第332 の仕分け=語彙 v3 で消えた欄。10-13b §1 1-5 で第 1 期に置くと決定)。
- **受入の試験**: `test_j0_port_schema.py`・`test_j0_mock_equivalence.py`(腕 on/off で同じ final=19 構成)・`test_j0_shuffle_invariance.py`(候補の順を入れ替えても mock/古典の選択が同じ番号の中身)・`test_j0_other_ratio_field.py`・byte-check。
- **依存**: 1-2・1-6・1-7。**空欄**: 〔1〕「その他」の割合の既定(R-108 の答申の値)。〔2〕驚きと迷いの欄の既定値(空=未計測)。**〔決定(10-13b §3)〕〔1〕〔2〕とも親案どおり(R-108 の値・驚きと迷いは空で始める)。** 〔第333 追加〕不応期を外した腕を mock で回し判断の呼び出し数を測る(2-0b・記録だけ)。

## 1-8b 発話の口(Q57 (d)・10-03 §6 ⑤・10-13b §1 1-5)〔第333 追加〕

- **口**: `engine/speech/port.py`: `Utterance`(凍結の dataclass: `speaker`・`t_ns`・`text`(本文)・`addressees`(届け先=当面はセッションの参加者)・`via`(1-3 の `Event.via` と同じ語)・`mora`(本文のモーラ数=TM3 の入力)・`event_id`(1-3 の出来事ログの行)・`modality`(将来の音声・表情(VRM)のための欄=値は空))と **`SpeechPort.say(ctx, utterance)` 1 つ**。会話の番の呼び出しだけに発話の欄(ひと言)を足す(5 ラベルは変えない・書き方の指示は B6 に)。口は (a) 出来事ログに 1 回書く (b) 相手の次の入力(B6)に素性タグと命令文の除去つきで載せる (c) 口コミの抽出(`wom_source=utterance`)に渡す(パーサは v3 でも `comment` を受け取るので自動で戻る)。mock と古典も同じ口。腕 `--speech-port`(既定 off)。試験では毎回 on で通す。中身を誘導しない(Q57)・根拠の札を書かせない(MR11)。
- **約束**: (1) 既定 off で final・テープ 不変(19 構成)。(2) on で、本文が口を通って出来事ログに 1 回だけ書かれ、相手の次の入力に載る(届く範囲は当面セッションの参加者=つなぎの台帳に「11a と空間の段 3 で『聞こえた範囲』へ」)。(3) 本文の無い発話はエラー(TM3 はモーラ数を入力にする)。(4) 発話の欄を足しても共有部の prefix は変えない(B6 の末尾に足す・残り 5 tok の範囲)。(5) 既定にするのは GPU の後の版上げ(カレンダー段 2+C1)=S6。
- **受入の試験**: `test_speech_port_schema.py`・`test_speech_default_off_invariance.py`(19 構成の byte-check)・`test_speech_on_reaches_addressee.py`(mock: 本文 → ログ 1 行 → 相手の B6 に素性タグつきで載る・命令文は落ちる)・`test_speech_empty_text_errors.py`・`test_wom_from_utterance_roundtrip.py`(口コミの抽出が v3 でも動く)・`test_speech_modality_field_empty.py`。
- **依存**: 1-3・1-8。**決定(10-13b §1 1-5)**: 第 1 期に置く(腕・既定 off)。既定化は GPU の後。

## 1-9 お金の基本操作(CP2 の段階 1)

- **口**: `economy/ops.py`: 基本操作 **`transfer(from, to, amount, what, cause)`** 1 つ(A 湧かないもの)。帳簿 9 口(`economy/ledger.py` の口)をこの 1 つに載せ替える。コードの検査: A〜D(体・世界・お金・物)は基本操作からしか書けない(AST)。1 日の締めの検算(四重記入=既存)は **K17 を直してから**(K17=10b の問い「金の生ログ `_raw_*` の輪の宣言と容量」。10b の記録 §5-4 で「輪の溢れは日次センサスの金の項に効かない」と確認済み=センサスと締めは取引行列 `_flow` と残高を読む。1-9 では輪の容量と溢れの数を manifest に宣言し、溢れたら止めるか記録するかを**宣言つきで決める**=親案: 記録して続ける・件数を計器に)。**〔決定(10-13b §3・親案を変更)〕 K17: 輪の容量を実測 4.07 行/体/日(10b-prep #20)の 1.5 倍以上=`TRANSFERS_PER_AGENT_PER_DAY` を 3.0 → 6.5 行/体/日(≥ 6.1)に広げて宣言する。溢れた件数は manifest と計器に出す。試験では溢れが 0 件であることを条件にする。溢れた場合は記録して続ける(止めない)。**
- **約束**: (1) final・帳簿の残高・金と物の台帳の行が 19 構成で不変(載せ替えは◎)。(2) `_apply_cash` の別名の書き(1-0 の alias 表)は `transfer` の中に閉じる=`alias_writes.json` から行が消える。(3) 保存則の検算(faucet/sink の全登録・残差の科目)は 2-1 まで今のまま。
- **受入の試験**: `test_cp2_transfer_only_writer.py`(AST: お金の列の書き手は `transfer` だけ・負の対照)・`test_cp2_nine_ops_equivalence.py`(9 口 → transfer で同じ残高・同じ台帳の行)・byte-check・`test_two_phase` の hot path に `economy/ops.py` を足す。
- **依存**: 1-3。**空欄**: 〔1〕K17 の「溢れたら止めるか記録するか」(親案は記録して続ける=ユーザー確認)。**〔決定(10-13b §3)〕上の K17 のとおり(容量 1.5 倍以上・溢れ 0 件が試験の条件・溢れたら記録して続ける)。** 容量を広げると生ログの輪の大きさ(宣言の投影 D-R2-6)が変わる=バイト予算の宣言を更新し、final は不変(輪は診断=軸 1 diag)。

## 2-2 近接 11a → 11c(10-03 §4・アジェンダ §2-1 の不変条件 7 本と B1〜B8)〔第334 追加=口の約束の正は実装アジェンダ〕

- **口**: engine/proximity.py の ProximityRule(舞台の中・同じ層(band)・距離 ≤ d、または同じ B5 の単位)と近傍の索引(SpatialIndex=格子・層ごと・刻みごとに作って捨てる)。腕 --proximity {cell,distance}(既定 cell=今の判定・指紋に入れない)・--proximity-d {1.0,2.0,2.5}(既定 2.0 m=B3)。知人に気づく確率 p(d) は R-62 の 2 点(10.4 m で 75%・23.5 m で 25%)を通るロジスティック曲線・抽選は 10c の counter(Philox・K19 の配置に行を足す)。
- **約束**: (1) 既定 cell で final・テープ・描画のバイトが不変(19 構成)。(2) distance で成立した会話の相手は必ず d 以内か同じ単位(1 日のランの全会話)・層が違えば届かない。(3) 索引の列挙は総当たりと一致(重なった点を含む)。(4) 腕の違う状態からの再開は止める(見出しに腕と d を書く)。(5) 11c の読み直しは計器だけ(判定しない)・既定 cell の計器は HEAD と一致。
- **受入の試験**: tests/engine/proximity/(不変条件 7 本・p(d) の 2 点・感度の腕 1.0/2.5・B5 の単位・再開の一致と負の対照)。byte-check 19 構成(cell)。
- **依存**: 1-2・1-3・1-8。正は docs/design/v2-proximity-distance-implementation-agenda.md(§0〜§2・§4・§7・末尾のユーザー決定 B1〜B8)。既定にするのは 2-4 版上げ 2 回目の束(10-03 の決定)。

## 3-3 反実仮想の器(10-12 §4-5 CP5・CP12・CP14・R-71 §1-6)〔第334 追加=実装の後に口を写した〕

- **口**: engine/experiment/ の ExperimentForm(申込書=schema・kind(探索/確認)・subject(level L0〜L4・ids・category=申込書の値=地名や業種名はコードに書かない)・content(決定の列・空なら A/A)・start/end(ナノ秒)・notice(to・at・via)・question・metrics(主 1 つ・副)・ensemble・preregistration(確認だけ)。知らない欄はエラー)と **apply(form, world, t) 1 つ**(決定を表に入れるだけ・実行は世界の中の過程・出来事ログに 実験:改変 と 実験:届いた情報 を gate.admit 経由で)。分岐=branch(T0 までテープを再生・T0 で改変・T0 から今の方策・R-71 の 4 つの確認を毎回)。ensemble(半分を封印・探索/確認・対の差は salt_compare の形・技量スコアは器だけ)。腕 --experiment <申込書>・--experiment-branch <基準のラン>・--experiment-aa。
- **約束**: (1) 申込書を渡さないランは final・テープ・描画が不変(19 構成)。(2) 改変は決定だけ=人の心・物理の法則・空間を直接書かない。(3) 効かせていない改変は記録して続ける(unapplied)。(4) 4 つの確認=(a) 入力の一致 (b) T0 より前の全 checkpoint の状態 hash の一致 (c) T0 以後で最初に食い違った刻みと系 (d) A/A の差が厳密に 0。(5) 申込書の指紋を状態の見出しに書き再開で照合・run_kind=counterfactual。
- **受入の試験**: tests/engine/experiment/(申込書の欄・固有名詞の不在・L0/L1・unapplied・分岐の 4 つの確認・A/A・封印の指紋・対の差の形)。byte-check 19 構成(申込書なし)。
- **依存**: 1-3・1-4・10d・10f。正は決定 §4-5。実装の記録は docs/bench/analysis/wallbounce-1012/cf33/README.md。

## 受入の順と門(親)

| 順 | 段 | 門(◎=byte-check 19 構成+2 日+再開・系ごとの指紋) | 検収 |
|---|---|---|---|
| 1 | 1-1 T0 | ◎+直書き 0+同値 | 親+別の検収役(T0 だけ 1 本で通す) |
| 2 | 1-3 | ◎+負の対照 3 本(CP12) | 別の検収役 |
| 3 | 1-4 → 1-5 | ◎(1-5 は NO_PERMISSION=0 の確認が先) | 別の検収役 |
| 4 | 1-2 / 1-6 / 1-7(並列・作業木 3 本) | ◎+描画のバイト一致(1-2) | 別の検収役 ×1(3 本まとめ) |
| 5 | 1-8 → 1-8b → 1-9 | ◎+同値+AST の負の対照+1-8b は on で届く試験 | 別の検収役 |

- 作業木を並べる前に、**第332 の 3-2-4(data の無い作業木で回る最小の試験の集合と CI)** を片付ける(ユーザー指示)。〔第333〕=計画 1-0b として実施(記録は `docs/bench/analysis/wallbounce-1012/tests-3-2-4/`)。
- 〔第333〕各段の実装役への発注は本書の該当の段と計画の行を渡す。仮採用(10-13b §0-3)は段の記録と PENDING §1-1 に残す。
- 用語集との照合は各段の記録で(「口」「約束」「門」は既存の語)。
