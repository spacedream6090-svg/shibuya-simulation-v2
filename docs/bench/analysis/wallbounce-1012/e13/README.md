# 第 1 期 1-3 出来事の記録(CP12・CT9・5W1H)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-3/events`(HEAD `4998174`=T0 を取り込んだ後)。commit は親。
- 正: [口の約束 1-3](../../../../design/v2-foundation-contracts-2026-10-13.md)・[計画 1-3](../../../../design/v2-implementation-plan-2026-10-12.md)・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-5 CP12・§4-4 CT9・§1-4・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(仮採用)。先例は [R-113](../../../../research/v2-r113-e1-foundations-existing-implementations.md) §3(AI Town の外からの入力の番号つきの 1 本の表=MIT・MATSim/SUMO の時刻順の events)。借りたのは形だけで、コードは写していない。
- 数は実測。生の出力(テープ・side の JSON)は git の外の作業用の置き場(作業木の `_bc/`)に置いた。比べた結果と道具だけをこのフォルダに置く(道具は `tools/`・絶対パスなし)。
- 道具(`tools/`・使い方は各ファイルの冒頭): `probe_e13.py`(系ごとの指紋を HEAD と作業木で比べる)・`manifest_check_e13.py`(10f の manifest の 2 つの側を比べる・T0 の道具の写し)・`day_rows_e13.py`(1 日の行数とバイト)。byte-check と 2 日のランは既存の道具(`10e/byte_check_10e.py`・`10e/two_day_check_act.py`)。

## 0. 結論

- 出来事の記録の口を作った: `Event`(口の約束の 12 欄・凍結)・原因は 3 型だけ(`LlmCall`・`Process`・実験の条件)・書く口は `EventLog.append` の 1 つ・語彙表 55 語(閉じた表)・id=`(t_ns, seq)`。
- **CP12**: 実験の条件の原因を作れるのは `engine/experiment/gate.py` の `admit` だけ。実行時(呼び手のフレームの検査・書きの検査を切っても外れない)と静的(src の全ファイルの AST・別名 12 形の負の対照)の両方で強制した。
- **配線**: 世界過程(world・close_final の最後の便)の ActualLog の行ごとに 1 行(原因=過程)と、E(診断)の区切りの行(日の締め・checkpoint)。4 系の `writes.paths` に `E:events.*` を宣言し、段 B と段 C と同じ実行時の検査で宣言の外を落とす。体・お金・物・判断(LLM)の系は残した(§4)。
- **目印**: ActualLog の行と出来事が 1 対 1(合成の世界と世界資産 200 体のランで試験)。テープと金・物の生ログには列を足していない(§5・仮採用)。
- **計器**: manifest の日次の記録に `events`(行数・バイト・種類の分布)。5,000 体の既定 v3 で 1 日 28,835 行・2,076,120 B(1 行 72 B)。今の行はほぼ世界過程の ActualLog の行(28,830)で、世界の大きさで決まる。
- **結果不変**: byte-check 19/19 構成で 25 欄とも HEAD と同じ(記録は既定 on)・記録 on/off も 19/19 で同じ・系ごとの指紋は 3 構成で全部の系・全部の刻みで同じ・manifest は 7 本とも既存の欄が全部同じ(足したのは日次の記録の `events` だけ)・2 日のラン(final `912446bd2b42b6ab`・140,913 呼・テープの sha)も HEAD の記録と同じ・再開は既存の試験と新しい試験(id が通しのランと同じ)で通った。
- 試験: 新しい試験 87 本(`tests/engine/events/`・86 本で約 21 秒)。全体は 4,096 passed・1 failed(junction 由来の既知)・1 xfailed(13 分 27 秒)。仮採用は 11 件(§10)。発注の「編集してよい」一覧の外を 1 つ直した(`tests/engine/test_state_ledger_10b.py` の行の数・§10)。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/events/log.py`(新) | `Event`(凍結の dataclass・`slots`・欄は口の約束の 12 個)・原因の 3 型(`LlmCall`・`Process`・実験の条件)・`EventLog`(書く口は `append` の 1 つ・列ごとの配列 13 本・1 行 72 B)・切替口 `enabled`/`set_enabled`(環境変数 `SHIBUYA_EVENTS`) |
| `src/shibuya/engine/events/vocab.py`(新) | `what` の語彙表(閉じた表・55 語)・`via`(CT9 の 6 語)・`where` の種類(3 つ) |
| `src/shibuya/engine/events/links.py`(新) | `ActualLogLink`=ActualLog の行ごとに出来事を 1 行書き、id を返す口 |
| `src/shibuya/engine/experiment/gate.py`(新) | CP12 の口 `admit`(実験の条件の原因を作れる唯一の関数)・`ADMIT_CODE` |
| `src/shibuya/world/processes/actual_log.py` | 行ごとの出来事の id の目印の列 2 本(`_event_t_ns`・`_event_seq`)と口 `event_sink`・`event_ids()`。固定幅のレコード(凍結)と `nbytes` は変えない。保持窓で行を落とすと目印も同じ行を残す |
| `src/shibuya/engine/processes/runner.py` | `attach_events`(台帳の過程の id → 実行器の過程の名の表を作り、ActualLog の口に `ActualLogLink` を置く。実行器の属性は増やさない) |
| `src/shibuya/engine/systems/build.py` | `EventLog` を作り(切替口を読む)、実行器に挿し、`Layers.events` に置く |
| `src/shibuya/engine/systems/boxes.py` | `Layers.events`(末尾・既定 `None`)・`OWNER_NAMES` の末尾に `events` |
| `src/shibuya/engine/systems/state_io.py` | `hash_owners` の末尾に `events`・`mark_boundary`(E の区切りの行)・`day_record` で日の締めの行と日次の記録の欄 `events`(計器)と保持窓 |
| `src/shibuya/engine/systems/conductor.py` | 刻みの頭で記録の時計を置く(`begin_step(ctx.t_ns)`)・系を呼ぶ間に `writes.paths` を書きの許可に渡す |
| `src/shibuya/engine/systems/guard.py` | `PATHS_PERMIT`・`events_write_allowed()`(段 C と同じ実行時の検査を出来事の記録にも) |
| `src/shibuya/engine/systems/observe.py` | checkpoint の系がハッシュの後に E の区切りの行を書く |
| `src/shibuya/engine/systems/run_end.py` | `result.event_log`(後付けの属性=`result.runner` と同じ。`RunResult` の欄は増やさない) |
| `src/shibuya/engine/systems/table.py` | world・checkpoint・day_close・close_final の `writes.paths` に `E:events.*`・checkpoint・day_close・close_final の `reads` に `layers.events` |
| `src/shibuya/engine/state_ledger.py` | 行 `E`(軸 1 diag・軸 2 discardable・道筋 23 個)・持ち主のクラス `events`・除外(設定 2 つ)。版は上げない(§10 の仮採用) |
| `src/shibuya/cli.py` | `--events {on,off}`(既定 on・`set_enabled(False)` を呼ぶだけ=`cli.run` と `run_day` の引数は変えない) |
| `tests/engine/events/`(新) | 試験のファイル 7 つ(87 本・§9)と凍結の表 2 つ(`writes_paths_events.json`・`manifest_events_keys_frozen.json`) |
| `tests/engine/test_state_ledger_10b.py` | 台帳の行の数の試験だけ(外の状態 96 → 97・全体 187 → 188・鍵の列の末尾に `E`・行 `E` の軸)。発注の「編集してよい」一覧の外=§10 で報告 |

## 2. `Event` の欄と原因の 3 型

- 欄(名と順は口の約束のとおり・`EVENT_FIELDS`): `id`・`t_ns`・`who`・`what`・`whom`・`where`・`how_much`・`via`・`received_ns`・`read_ns`・`origin`・`cause`。凍結・`__slots__`。書き手は `id` を付けない(`append` が付ける)。
  - `id`=`(t_ns, seq)`。`seq` は同じ `t_ns` の中の通し(0 から)。並べると時刻順。決定的で、刻みの境目からの再開でも通しのランと同じ id になる(再開のランは空の記録から書く=記録は discardable)。ランの通しの行数は `n_appended`。
  - `t_ns`=`SimTime`(0 以上の整数)。記録の時計(進行役が刻みの頭で置く)より前の時刻は書けない(CP12 の「書き込むその場で直接の原因を記録する」)。
  - `who`=体の id(0 以上の整数)か持ち主の名(文字列)。`whom` は同じ形か `None`。
  - `what`=語彙表の語(§3。表の外は `ValueError`)。
  - `where`=`(種類, 番号)`(種類はセル・ノード・POI)か `None`。`how_much`=整数か `None`。
  - `via`=CT9 の道具の欄(対面・通話・メッセージ・グループ・SNS・無し。既定は無し)。
  - `received_ns`・`read_ns`=届いた・読んだ時刻(`t_ns` ≤ 届いた ≤ 読んだ。読んだは届いた後だけ)。`origin`=範囲の外からの印(空でない文字列か `None`)。
- 原因は 3 型だけ(`CAUSE_TYPES`・種類の名 `llm_call`・`process`・`experiment`):
  - `LlmCall(call_id, input_event_ids)`: `call_id` はテープの `call_id` 列と同じ値(`"{発射の刻み}:{体}:{起床の種類}"`)。`input_event_ids` は入力に入っていた出来事の id の組。
  - `Process(name)`: 名は過程の名の表(世界過程 18 個+区切り 2 個)だけ。
  - 実験の条件(`cond_id`): **作れるのは `engine/experiment/gate.py` の `admit` だけ**。
- 第 4 の型は作れない: 根 `_Cause` の `__init_subclass__` が「この置き場の 3 つの名で、根の直接の子」以外を落とし、3 つを定義した後は封じる(3 つの型の子も作れない)。`Event` と `append` は原因の型を完全一致で見る(凍結を破って差し替えても書く口が落とす)。
- CP12 の 2 重の検査:
  - 実行時: 実験の条件の型の `__init__` が、最初に呼び手のフレームのコードが `gate.admit` のコード(`ADMIT_CODE`)かを見て、違えば `PermissionError`(先に見るので、既存の物の `__init__` を呼び直しても中身は書き換わらない)。`dataclasses.replace`・型から作る・別名・`getattr` も同じ所で落ちる。pickle は `TypeError`、`copy` は同じ物を返す。**書きの検査の切替口(`SHIBUYA_WRITE_GUARD=off`)でも外さない**: 書きの検査は値を変えない検査で、重さを測るために外せる。CP12 の検査は記録の原因の正しさそのもので、外すと実験でない出来事に実験の印が付き、分岐の差の帰属が壊れる。実験の口を通る回数は少ないので、重さの理由も無い。
  - 静的: `tests/engine/events/test_e_cause_three_kinds.py` が `src/shibuya` の全ファイルを AST で見て、型の定義の置き場(`log.py`)と口(`gate.py`)の外で、型の名の参照・import・`*` の import・文字列の名・記録の置き場の別名からの動的な `getattr`・`vars`・`__dict__` を落とす。負の対照は別名 12 形(発注の 3 本=直接・別名・getattr+属性・パッケージの属性・点つきの名・動的な getattr・vars・`__dict__`・`*`・importlib・`object.__new__`)。正の対照=許した 2 か所が実際に型の名を書いていること。
- 口 `gate.admit(log, cond_id, *, what, who, ...)`: 実験の条件を原因とする出来事を記録の時計の時刻で 1 行書くだけ(世界の状態は書かない。実験で世界に入れるのは決定だけ=CP6)。1-3 では src に呼び手は無い(口と試験だけ。申込書の仕組み=CP5-4 は後の段)。

## 3. 語彙表(`what`・55 語・閉じた表)

決定(口の約束 1-3〔空欄 1〕=親案・回答 10-13b §3)の 4 つの族。語は `族:語`(例 `行為:移動`・`過程:rail`・`金:賃金`・`物:販売`)。

| 族 | 数 | 中身 | 元の表 |
|---|---|---|---|
| 行為 | 12 | 移動・乗車・購入・食事・会話・退去・通報・手伝い・断る・就寝・並ぶ・なし | `llm.contract.ACTION_VOCAB_V3`(import) |
| 過程 | 20 | 世界過程 18(environment・rail・opening・crowd・traffic・delivery_inbound・shelf・waste・street_cleaning・last_mile・bus_taxi・road_works・hotel・infra・press・large_event・dispatch・salient)+区切り 2(day_close・checkpoint) | `engine.processes.runner.PROCESS_ORDER`(写し) |
| 金 | 15 | お金の科目(消費支出・賃金・域外仕入・税・利子・家賃・預金純増・来街者持込・持ち出し・参入資本・配当/内部留保・減価償却・残差科目・退蔵項・逸脱比例コスト) | `economy.accounts.ACCOUNT_NAMES`(写し) |
| 物 | 8 | 物の出入り(域外仕入・持込物・販売・廃棄ビンへ・消費・廃棄搬出・返品/域外出荷・棚卸差異) | `economy.goods.GOODS_CODE_NAMES`(写し) |

- 族を付けた理由: 金と物に同じ語「域外仕入」がある。
- 写しにした理由: engine は economy を import できない(層の契約 `economy > engine`)。過程は runner を import すると世界過程の全モジュールを読む。写しの食い違いは `test_e_vocab_is_closed.py` が元の表と突き合わせて落とす。
- `via` の 6 語は決定 10-12 §4-4 CT9 (b) の 5 つ+無し。`where` の種類はセル・ノード・POI。

## 4. 配線した系と残した系

| 群 | 系 | 1-3 の配線 | 原因 |
|---|---|---|---|
| 世界 | world(世界過程 18 本) | ActualLog の行ごとに 1 行(`ActualLogLink`)。`who="runner.<過程>"`・`what="過程:<過程>"` | `Process(<過程>)` |
| 暦(日の終わり) | day_close・close_final | 日の締めの E の行(`過程:day_close`)・close_final は最後の便の ActualLog の行も。日次の記録の計器と保持窓 | `Process("day_close")` |
| 計器 | checkpoint | checkpoint の E の行(`過程:checkpoint`・ハッシュの後) | `Process("checkpoint")` |
| 体・お金・物・判断 | body・presence・phase_c ほか・decide/llm_receive(LLM の呼び出し) | **残した**(後の段で載せ替える) | — |

- 宣言: 4 系の `writes.paths` に `E:events.*`(凍結の表 `tests/engine/events/writes_paths_events.json`)。SoA の書く列の凍結(`writes_soa_frozen.json`)は変わらない(記録は SoA を書かない)。
- 宣言の外の書き: 段 B(試験のときの全欄の差)に加えて、段 C と同じ実行時の検査を足した(`guard.PATHS_PERMIT`・`events_write_allowed`・既定で入る・切替口は書きの検査と同じ)。負の対照: world と checkpoint の宣言から外すと書いた所で `PermissionError`・実行時の検査を外すと段 B が checkpoint に `E:` の道筋の変化を出す。
- 残した系の載せ替えの先: お金と物の行は 1-9(`transfer(from, to, amount, what, cause)` が出来事を書く=CP2)・行為と LLM の呼び出し(`LlmCall`)は判断の口の段(1-8・1-8b)が候補。〔親に確かめてほしい点〕

## 5. 既存の記録との目印

- ActualLog: 行ごとに出来事の id の 2 列(`_event_t_ns`・`_event_seq`・目印の無い行は seq=-1)を、固定幅のレコード(列の順と型は凍結)の外の並びの列として持つ。`append`・`append_many` の直後に口 `event_sink` を呼んで目印を書く。保持窓で畳むと目印も同じ行を残す。`nbytes`(成長の宣言の実測)には入れない。試験 `test_e_log_links_actual.py`: 合成の世界のランと世界資産の 200 体のランで、生存行の全部に目印があり、目印はどれも記録にある別々の id で、出来事の `what`・`who`・`cause` が行の過程から決まる値と同じ・過程の出来事の数=ActualLog に書いた行の数(1 対 1)。
- テープ: **列を足していない**。LLM の呼び出しの原因 `LlmCall` が `call_id`(テープの `call_id` 列と同じ値)を持つので、テープの行と出来事は既存の列で結べる。列を足すと byte-check の `calls_column_names` が動き、1-3 では LLM の呼び出しを配線していないので全部空の列になる。〔仮採用・親に確かめてほしい点〕
- 金と物の生ログ: **列を足していない**。1-3 では書き手(phase_c の買い物・世界過程の補充と運賃)の原因を持たない。生ログの持ち主のクラスに属性を足すと、既存の台帳の行(O58・O60)の道筋を変えるか行を足すことになる。1-9 の `transfer(..., cause)` が出来事を書く所で、同じ形の目印を付けるのが筋。〔仮採用・親に確かめてほしい点〕

## 6. 記録の状態と manifest(計器)

- 状態台帳の行 `E`(足す前に軸を決めた): 軸 1 diag(読み手は日次の記録の計器と試験だけ)・軸 2 discardable(どちらのハッシュにも状態のファイル=`full_items` にも入らない)。道筋は `events._ev_*` の 23 個(列 13・行数・名と原因の表・時計・seq の表・日の起点・積算)。設定 2 つ(`enabled`・`retention_days`)は除外の一覧。行の鍵は O の通し番号でなく `E`(系の宣言 `E:events.*` と同じ)。外の状態の軸 1 の AST(10f)・持ち主のクラスの属性の網羅(AST と実行時)は通る。
- 持ち主 `events` を `OWNER_NAMES` と `hash_owners` の末尾に足した(既存の 21 個の名と順は変えない)。2 つのハッシュは軸で選んだ行の道筋だけを読むので値は変わらない。段 B の全欄の差は `E:` の道筋を見る。
- manifest: 一番上の鍵は足していない(T0 の凍結の表のまま)。日次の記録(`daily` の各行)の末尾に `events` を足した: `on`・`rows`(その日に書いた行)・`bytes`(行 × 72)・`by_what`(語彙表の順)・`by_cause`(原因の種類)・`live_rows`・`live_bytes`(保持窓の中の行)・`evicted`。鍵は `tests/engine/events/manifest_events_keys_frozen.json` に凍結。`daily` は節の表で観測なので節の表は変えない。記録しないとき(off)も同じ形(`on: false`・0)。
- 保持窓 7 日(ActualLog の D-R2-6 と同じ・expedient)。日の締めで窓の外の行を落とし、原因の表を生きている行の分に詰め直す(LLM の呼び出しは 1 回ごとに原因が 1 つなので、詰めないと表が伸び続ける)。成長の宣言(D-R2-6 の 5 欄)は `EventLog.growth_declaration()` に書いたが、ランの成長の報告にはまだ載せていない(§10)。

## 7. 1 日の行数とバイト(mock 5,000 体・世界資産・既定 v3・1 日)

[day_rows_e13.json](day_rows_e13.json)(`tools/day_rows_e13.py`・`cli.run` に `vocab_version="v3"`=byte-check の `w6_v3_default` と同じ構成・final `5f7ae9ff24005314`・65,597 呼。記録 on と off で final と呼数が同じ):

| 量 | 実測 |
|---|---|
| 1 日の行 | **28,835 行**(過程 28,830=ActualLog の行と同じ数+E の区切り 5=日の締め 1・checkpoint 4) |
| 1 日のバイト(記録の列) | **2,076,120 B**(行 × 72 B=約 2.1 MB/日)。名の表 13・原因の表 14 |
| 種類の分布 | bus_taxi 12,954・opening 6,546・rail 3,911・last_mile 2,758・delivery_inbound 2,337・waste 234・shelf 56・road_works 12・dispatch 10・large_event 6・hotel 3・press 3・day_close 1・checkpoint 4(原因はどれも過程) |
| ActualLog の目印の列 | 28,830 行の全部に目印・目印の列 345,960 B(12 B/行) |
| 体あたり | 5.77 行/体/日(ただし今の行はほぼ世界の大きさで決まる=体の数に比べない。世界資産 200 体でも 26,153 行) |
| 壁時計 | on 25.2 秒・off 24.8 秒(1 本ずつ・ばらつきは測っていない) |

- 見込み(1-3 の分): 1 日 約 2.9 万行・約 2.1 MB・保持窓 7 日で生きている行は最大 約 20 万行・約 15 MB。体・お金・物・判断の系を載せると、お金の行だけで 4.07 行/体/日(10b-prep #20 の実測)=5,000 体で約 2 万行/日が足される。行為と LLM の呼び出しも体の数に比例する。全部を載せた段で 1 日の実測から成長の宣言を作り直す(§10)。

## 8. 結果不変の確かめ

| 確かめ | やり方 | 結果 |
|---|---|---|
| byte-check([byte_check_e13.json](byte_check_e13.json)) | `10e/byte_check_10e.py`・19 構成・5,000 体・seed 1・1 日・テープつき。HEAD の側は本体の src(`4998174`)、e13 の側は作業木の src(`src_is_worktree` 真・記録は既定の on) | **19/19 構成で 25 欄とも同じ**(final・呼数・blocks・calls の列の名と sha・行動の件数・起床の内訳・顕著行為・出動・食事・behavior/full の最後・締めの後の 2 本・暦・frozen_sources ほか)。既定 v3 の final `5f7ae9ff24005314`(T0 の記録と同じ) |
| 記録 on/off([byte_check_e13_on_off.json](byte_check_e13_on_off.json)) | 同じ道具で作業木の src を `SHIBUYA_EVENTS=off` で回した側と比べた | **19/19 構成で 25 欄とも同じ**。ランの壁時計の差(on − off)は −0.18〜+0.87 秒・平均 +0.16 秒(19 本の和 493.7 秒 と 490.6 秒=+0.6%。4 並列の同時のラン・1 本ずつ=ばらつきは測っていない) |
| 系ごとの指紋([probe_e13.json](probe_e13.json)) | `tools/probe_e13.py`(1-0 の probe・全部の刻み・`PYTHONHASHSEED=0`)。合成の世界 80 体 720 刻み(記憶+関係+同席+店の記憶)・世界資産 300 体の既定 v3 と記憶+関係。作業木の側は 1-3 で足した物(`E:` の道筋・ActualLog の目印の 3 欄・日次の記録の `events`)を外した。両側とも digest から物の番号(`id`)を外した(段 FIX の digest は 1 本のランの中の差し替えを見るために番号を入れる=別のプロセスの 2 本では揃わない) | **3 構成とも全部の系・全部の刻みで同じ**(並び 5,945・14,159・16,271・最初の食い違い無し)。ActualLog の行の中身(固定幅の行・索引・集約)も同じ |
| manifest([manifest_check_e13.json](manifest_check_e13.json)) | 10f の `manifest_check_10f.py side` の 7 本(既定 v3 の seed 1・2・帰無腕・記憶+関係・古典+記憶+関係)。両側 `PYTHONHASHSEED=0`。`tools/manifest_check_e13.py` で平坦にした全欄を比べ、壁時計は除いた | **7/7 で final が同じ・既存の欄 1,709〜2,225 個がどれも同じ・一番上の鍵の並びも同じ**。足したのは日次の記録の `events` の下の葉(20〜21 個)だけ。違う環境の欄は `env_id`・`environment.env_id`・`git_diff_sha256`(作業木の差分)だけ |
| 記録 on/off(試験・世界資産 300 体の 19 構成) | `test_e_log_invariance.py::test_nineteen_configs_on_and_off_give_the_same_final`(`slow`・毎晩の段) | 19/19 で final と呼数が同じ(156 秒) |
| 再開 | 既存の試験 `test_resume_10d.py`(全部)・`test_e_log_schema.py` の再開(刻みの境目から再開したランの id が通しのランと同じ)・`test_e_log_invariance.py` の 2 日(状態のファイルの full-hash が on/off で同じ) | 通った(§9) |
| 2 日のラン | `10e/two_day_check_act.py one`・5,000 体・seed 1・既定 v3・テープつき・作業木の src(記録 on) | final `912446bd2b42b6ab`・140,913 呼・テープの calls `cb330e76b4b8a573`・blocks `7f09f3dc78d84ac4`・暦 2026-07-13 → 07-14(1-0・T0 の記録の HEAD の値と同じ) |

## 9. 試験

新しい試験 `tests/engine/events/`(87 本=86 本+`slow` 1 本・data が要るのは 2 本だけ=`requires_data("world_v2:w17_schedule.parquet")`・ほかは合成の世界・86 本で約 21 秒):

- `test_e_log_schema.py`(28): 欄の名と順・凍結・`__slots__`・id=`(t_ns, seq)`(同じ時刻の中の通し・刻みで 0 から・時刻順)・書き手は id を付けられない・過去の時刻は書けない・全欄の往復・不正な欄 17 通り・numpy の整数を整数に・off の記録は何も書かない・日の締めの計器と保持窓(原因の表の詰め直しを含む)・同じランの 2 回で同じ id の列(E の行の数=checkpoint の数と日の数)・刻みの境目から再開したランの id が通しのランと同じ・1 行 72 B と成長の宣言。
- `test_e_cause_three_kinds.py`(26): 3 種類だけ・第 4 の型を作れない(根と 3 つの型の子 4 通り×名と置き場の真似)・偽の原因を `Event` と `append` が落とす・**静的(AST)**: src の全ファイルで口の外に型の名が無い・許した 2 か所は実際に名を書いている(正の対照)・別名 12 形を全部見つける(負の対照・発注の 3 本=直接・別名・getattr を含む)・**実行時**: 口を通せば書ける(正の対照)・直接・別名・getattr の 3 本(負の対照)・replace・型から作る・`__init__` の呼び直し(中身は変わらない)・pickle・copy・書きの検査を切っても外れない。
- `test_e_log_invariance.py`(3): 合成の世界で on/off の final・呼数・checkpoint の 3 本・締めの後の 2 本・manifest の既存の欄(`events` を除く全部)が同じ・2 日と状態のファイルの full-hash が同じ・(`slow`)世界資産 300 体の 19 構成で final と呼数が同じ。
- `test_e_log_links_actual.py`(6): 口の単体(1 対 1・保持窓で落としても目印が行に付いたまま・口が無い/off は目印なし・知らない過程の id と語彙表の外はエラー)・合成の世界のランと世界資産 200 体のランで ActualLog の行と出来事が 1 対 1。
- `test_e_vocab_is_closed.py`(14): 4 つの族が元の表と同じ(行為=v3・過程=`PROCESS_ORDER`・金=`ACCOUNT_NAMES`・物=`GOODS_CODE_NAMES`)・55 語で重なり無し・表の外 8 通りがエラー・表の全部の語は書ける・過程の名が閉じている・`via` と `where` が閉じている。
- `test_e_writes_declared.py`(7): `E:events.*` を宣言した系が凍結の表と同じ・書きの許可の読み・宣言を外した world と checkpoint が書いた所で落ちる(実行時)・実行時の検査を外すと段 B が checkpoint に `E:` の変化を出す・宣言どおりなら段 B の宣言の外 0・`PATHS_PERMIT` を書き換えるのは guard だけ(AST)。
- `test_e_manifest_events.py`(3): manifest の一番上の鍵は T0 の凍結の表のまま・日次の記録の既存の欄の並びは同じで末尾に `events`(鍵は凍結の表と同じ・節は観測)・`rows`=`by_what` の和=`by_cause` の和・`bytes`=行×72・日の和=書いた行の数。

既存の試験(1-3 に関わるもの): `tests/engine/systems`(173 本・`tests/engine/time` を含む)・`test_state_ledger_10b.py`(行の数の試験を直した後・73 本)・`test_resume_10d.py`・`test_t0_tm9_fields.py`・`test_env_and_sections_10f.py`(65 本・8 分 14 秒)はどれも通った。`lint-imports` は 5 契約とも守られている(189 ファイル)。秘密の走査(`tools/scan_secrets.py`・変えたファイルと新しいファイル)は CLEAN。

### 9-1. 全体の試験

`-m "not gpu and not slow" -n 4 --dist loadfile`(data あり・作業木): **4,096 passed・1 failed・1 xfailed(13 分 27 秒)**。T0 の記録の 4,010 passed に新しい試験の 86 本を足した数と同じ。落ちた 1 件は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(テープの道筋が `data/tape/` で始まらない)で、作業木の `data` が本体への junction であることで起きる既知の落ち([1-0 の記録](../run-day-decomp/impl-1-0.md) §1・T0 の記録 §6-1 と同じ。本体では通る)。`slow` の 1 本(19 構成の on/off)は別に回して通った(§8)。

## 10. 限界・空欄・仮採用・親に確かめてほしい点

- **仮採用(10-13b §0-3)**: 既存の決定と原文から答えが出なかったので、親の推奨に近い案で進めた。どれも記録の側の形で、既定の final は動かない(§8)。戻すときは記録の物と試験を直すだけ。
  1. **id=`(t_ns, seq)`**(発注の 2 案のうち): ランの中の連番は再開のランで 0 から数え直す(記録は discardable=続きの数を持たない)。`(t_ns, seq)` は刻みの境目からの再開でも通しのランと同じ値になる(1-6 の記憶の目印が再開をまたいで指せる)。
  2. **区切りの名(`day_close`・`checkpoint`)を語彙の「過程」の族に入れた**・語の形を `族:語` にした(金と物に同じ語「域外仕入」がある)。
  3. **`who` の書き方**: 世界過程の行は持ち主の名 `runner.<過程>`(状態台帳の持ち主の道筋)、区切りの行は `engine`。ActualLog の行の出来事は `what=過程:<過程>`・`whom`・`where`・`how_much` は空(対象の id・予定の刻み・逸脱の語・遅れは ActualLog の行に残し、目印で引く=載せ替えは後の段)。
  4. **状態台帳の版を上げない**(行 `E` を足したが `state-ledger/10e-ret` のまま)。行 `E` はどちらのハッシュにも状態のファイルにも入らない。上げると manifest の `state_hashes.ledger_version` の値が動き、前の版で書いた状態のファイルから再開できなくなる(中身は同じ)。
  5. **行の鍵を `E`**(O の通し番号 O97 でなく)にした。発注の宣言の形 `E:events.*` に合わせた。
  6. **持ち主 `events` を `OWNER_NAMES`・`hash_owners` の末尾に足した**(既存の 21 個の名と順は変えない)。発注の「持ち主は変えない」の「足す」側と読んだ。ハッシュの値は変わらない(§8 の byte-check・2 日・再開)。
  7. **出来事の記録の書きにも段 C と同じ実行時の検査を足した**(`guard.PATHS_PERMIT`・既定で入る・切替口は書きの検査と同じ `SHIBUYA_WRITE_GUARD=off`)。口の約束は段 B だけを求める。1-0 の「宣言の外を書いたら落ちる」は既定で入る、に合わせた。
  8. **切替口は `run_day` の引数にしなかった**(環境変数 `SHIBUYA_EVENTS`・`set_enabled`・CLI `--events`)。`run_day` の引数は設定の指紋に入り、113 個の署名は 1-0 の試験が固定している。記録は結果を変えないので、書きの検査の切替口と同じ扱いにした。記録したかは manifest の日次の記録 `events.on` に出る。
  9. **manifest は日次の記録の欄だけ**(一番上の鍵は足さない)。T0 の凍結の表と「TM9 が末尾」の試験を変えずに済み、「1 日の行数と種類の分布」は日次の記録が自然な置き場。ランの合計は日次の和。
  10. **テープ・金と物の生ログに目印の列を足していない**(§5)。テープは `LlmCall.call_id` で結べる・金と物は 1-9 の `transfer(..., cause)` で付けるのが筋。発注の 4 の文面(列を足す)とは違う=親の判断を仰ぐ。
  11. **保持窓 7 日**(ActualLog と同じ)。
- **発注の「編集してよい」一覧の外を 1 つ変えた**: `tests/engine/test_state_ledger_10b.py` の行の数の試験(台帳の行を足すと必ず落ちる=「状態台帳の行の追加」に伴う最小の直し)。試験の名は `..._187_...` のまま。
- **残した系**: 体・お金・物・判断(LLM の呼び出し)は配線していない(§4)。A〜D を毎回書く約束は、1-3 では世界過程(ActualLog)と区切りだけ。載せ替えの段は親が決める(候補: お金と物=1-9・行為と `LlmCall`=1-8/1-8b)。
- **成長の宣言**: `EventLog.growth_declaration()` は書いたが、ランの成長の報告(`check_growth`)に載せていない。載せると成長の報告(manifest には出ない)と予算の門が変わる。全部の系を載せた段で 1 日の実測から宣言し直して載せる。
- **静的な検査の限界**(CP12): 記録の置き場の別名を介さない動的な取り出し(引数で受け取ったモジュールへの `getattr`)は見えない=実行時の検査が受け持つ。`type(x).__new__` で `__init__` を飛ばして作る形は、実行時にも捕まらない(型の名を書かないので静的にも見えない)。CP12 の 2 つの検査は、うっかりと近道を止めるもので、わざと壊すコードは止めない。
- **段 B の帰属の限界(1-0 からの既存)**: 間引いた刻みで差を測ると、刻みの最後の系(checkpoint)の差は次の刻みの頭が測る刻みに入っていないと帰属しない。試験は checkpoint の刻みとその次を測る刻みに足した。
- **用語集**: 新しい語は「出来事の記録」「目印」「区切り」(口の約束と計画の語)。用語集との照合はしていない(親の検収で)。

## 11. 親の検収(第334・2026-10-14)

- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・w6_v3_default/w6_v3_activity_off/w6_v1_default/v3_mem_rel・記録は既定 on): final が同じ 4/4・動いた欄 0(parent_head_vs_e13_4cfg.json)。
- 親が作業木で tests/engine/events(not slow)を実行: 86 passed(52 秒)。CP12 の門の形(admit の 1 関数・実行時は呼び手のフレーム)と状態台帳の行 E の試験の直しを読んだ。
- 独立検収(review.md)の判定は §12。M1・L3・L7 の直しの後、親が作業木で events・systems・time・test_cli・state_ledger_10b を再実行: 350 passed(4 並列・2 分 47 秒)・lint-imports 5 kept。

## 12. 独立検収(review.md)と親の直し(第334・2026-10-14)

- **判定: 条件つき受入**(検収役は実装を見ていない。byte-check 4 構成=25 欄とも同じ・on/off も同じ・合成の世界の manifest 2,444 葉に差なし・負の対照=静的 3 本が落ちる・実行時 5 形が止まる・第 4 の型 4 形が止まる・指定の試験 371 passed)。
- **M1(中・親が直した)**: 書くときに門を確かめていなかった(型を作るときだけ)。`EventLog.append` で原因が `Experiment` なら呼び手のフレームが `gate.admit` かを確かめる(書きの検査の切替口でも外さない)。負の対照 3 本を足した(読み戻した原因の使い回し・`object.__new__`・`type(e).__new__`・書きの検査 off でも同じ)。
- **M2(中・記録に足す)**: 39 万体の見積り(検収役の算術): 1-3 で配線した分(世界過程と区切り)は世界の大きさで決まり約 143 MB=M8(RSS ≤ 24 GB)の約 0.6%。**後の段の問題**: 原因の表は LLM の呼び出しごとに Python の物を 1 つ持つ形(1 件 221〜525 B の実測)。mock の 13.1 呼/体/日で外挿すると 7 日分で 7.9〜18.8 GB=M8 の 33〜78%。**`LlmCall` を配線する前(1-8)に原因の表を列の形に直す**(PENDING §2 に残す)。
- **L3(低・親が直した)**: CLI の `--events on` が環境変数 `SHIBUYA_EVENTS=off` を上書きしなかった → CLI を優先。
- **L7(低・親が直した)**: `VOCAB_CODES`・`VIA_CODES` を `MappingProxyType` にして実行時に語を足せなくした。
- **検収役の確認 2〜5 への親の答え**: (2) テープと金・物の生ログに目印の列を足さなかったのは認める(仮採用 10。テープは `call_id` で結ぶ・金と物は 1-9 の `transfer(..., cause)` で付ける=口の約束 (2) の「載せ替えは後の段」の範囲)。(3) 仮採用 11 件は認める(台帳の版は上げない=行 E はハッシュにも状態のファイルにも入らない・持ち主 `events` を末尾に足すのは「足す」側・切替口を `run_day` の引数にしないのは設定の指紋を守るため)。(4) `test_state_ledger_10b.py` の行数の試験の編集は「凍結の表(増えた分だけ)」の範囲として認める(名の `_187_` は履歴として残す)。(5) M2 の列化は PENDING §2 の 1-8 の前提に。
- **残る低(記録だけ)**: L1 静的な検査が `eval`・`sys.modules`・`importlib`・`attrgetter`・`exec` を見逃す(実行時の検査が止める)/ L2 `EventLog` に段 C のような `__setattr__` の守りが無い(試験は段 B が捕まえる)/ L4 上の (4) / L5 台帳の版(仮採用 4)/ L6 日次の `events` の数は再開をまたがない(diag)/ L8 目印の列のバイトが成長の宣言に無い(1-9 で列を足すときに宣言)/ L9 保持窓の基準が ActualLog(行の刻み)と出来事(書いた時刻)で違い、7 日の境目で目印が落ちた出来事を指しうる(保持窓を合わせるのは 2-3 複数日の mock で)。
- 親の検収: §11 のとおり(byte-check 4 構成 同じ・events 86 passed)。直した後の試験は親が作業木で再実行(§11 に追記)。
