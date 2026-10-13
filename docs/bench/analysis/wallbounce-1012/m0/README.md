# 第 1 期 1-6 記憶の器 M0(MR-0・MR11・MR16)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-6/memory-m0`(HEAD `136fdbb`=T0 と 1-3 を取り込んだ後)。commit は親。
- 正: [口の約束 1-6](../../../../design/v2-foundation-contracts-2026-10-13.md)・[計画 1-6](../../../../design/v2-implementation-plan-2026-10-12.md)(M0 は器と出どころだけ)・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-6 MR-0・MR11 (b)・MR16・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(仮採用)・§3 1-6(テープの列は版 4 の中で可)・[記憶の草案](../../../../design/v2-memory-rework-design-round-draft.md) の〔答え〕。先例は [R-113](../../../../research/v2-r113-e1-foundations-existing-implementations.md) の 1-6 の節(AI Town の `memoryFields`=共有の会話を `conversationId` で指し、本人視点の要約・重要度・最後に引いた時刻を持つ=MIT)。借りたのは形だけで、コードは写していない。
- 数は実測。生の出力(テープ・side の JSON)は git の外の作業用の置き場(作業木の `_bc/`)に置いた。比べた結果と道具だけをこのフォルダに置く(道具は `tools/`・絶対パスなし)。
- 道具: `tools/recall_equivalence_m0.py`(5,000 体の想起の突き合わせの数)。byte-check は既存の道具(`10e/byte_check_10e.py`)。

## 0. 結論

- 記憶の器 `engine/memory_store.py` を作った(口の約束の置き場 `engine/memory/store.py` から、親の判断で 1 本のモジュールへ移した=§12 仮採用 1)。記憶の行は、目印 `event_id`(1-3 の `EventId`)・強さ(System 1 の数=回数・重要度・最初の時刻)・注釈・出どころ・録画(最後に見せた時刻)を持つ。体ごとの行の範囲を持つ SoA の列にした。書く口は `remember` と `mark_shown` の 2 つ。`__setattr__` は欄の付け替えを落とす。読み口 `recall(agent, t_ns, k)` は `MemoryView` の組を返す。`MemoryView` は LLM に見せる形で、言葉(はっきり/うろ覚え)・中身の粗さ・中身の ID だけを持ち、強さの数は持たない(MR-0)。
- 腕 `--memory-store events`(既定 `mem`=今の `mem_*` だけ・器を作らない)。腕 on では、今の表に書く所で同じ出来事を器にも書き、想起を器から引く。器は今の表と同じ規則の写しで、行が食い違えば `_write` が落とす。
- **目印の先は 100% `legacy`**: 1-3 の出来事の記録には世界過程と区切りしか載っておらず、体の出来事(行為・会話・気づき・看板)は無い。記憶の行は全部、記録に無い出来事の仮の行(`origin="legacy"`)になった。5,000 体・1 日で 52,422〜55,465 行(§5)。
- **同値**: 腕 on で今の表の想起と器の想起が同じ候補を返した。合成の世界は全部の刻みの全部の想起、5,000 体の 3 構成は刻みの 1/7 の全部の想起(3 構成で 34,116 呼び出し・59,599 項)を突き合わせ、食い違いは 0(§4)。
- **録画(MR16)**: 描き方が B5 に載せた記憶の行に、最後に見せた時刻を付ける。テープには腕 on のランだけ列 `recalled_event_ids`(list<string>・`recalled_rows` と同じ並びの `"t_ns:seq"`)を足した。版は 4 のまま。既定 off では列を足さない(§6)。
- **描き方の口** `render_memories(views)`: 今の B5「記憶」の 1 行とバイトで同じ(合成の世界の全部の描画で確かめた・§4-3)。`Percept` への結線は 1-2 の取り込みの後。
- **結果不変**: byte-check 19/19 構成で 25 欄とも HEAD と同じ(既定 off)。独立検収の直しの後も 4 構成で同じ(§9)。腕 on の 4 構成では、テープの既存の 21 列(`recalled_rows`・`recalled_first_tick`・`recalled_kind`・`recalled_object`・`b5_text`・`prompt_hash` を含む)の sha が全部の呼び出しで同じで、増えたのは列 `recalled_event_ids` だけ。final も同じだが、mock の final は想起の中身に鈍い(検収の負の対照: 重要度を 1 ずらして想起の 114/787 が食い違っても final は同じ)ので、同値の根拠は final ではなく、テープの既存の列の一致と直接の突き合わせ(§4)と、書くたびの値の突き合わせ(§3)。
- 試験: 新しい試験 44 本(`tests/engine/memory/`・`slow` 2 本を含む)。全体は 4,128 passed・4 failed(1-6 の 3 件は直して回し直し 56 passed・残る 1 件は junction 由来の既知)・1 xfailed(§10)。独立検収(review.md)の直しは §13。仮採用は §12。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/memory_store.py`(新) | `MemoryStore`(記憶の行の列 7 本 32 B/行+仮の出来事の表 5 本 14 B/行・注釈・録画の控え・計数)・`MemoryView`・`Cue`・`LegacyEvent`・`ShopPool`・`RecallReport`・`render_memories`・`clarity_of`・腕の切替口(`arm`・`set_arm`・環境変数 `SHIBUYA_MEMORY_STORE`)・書きの実行時の検査(`_check_permit`) |
| `src/shibuya/engine/memory.py` | `MemoryLayer.memory_store`・`enable_memory_store`・`on_shown`・`tape_event_ids`・`rebuild_memory_store`・`_recall_from_store`(腕の想起)・`_write`(器にも覚えさせ、行の食い違いを落とす)・`record(annotation=)`・`note_utterance`(要旨を先に決めて器の注釈に渡す=表の書き順と値と計数は前と同じ)・`summary` の末尾に `memory_store`(腕のランだけ)。純粋な取り出し 2 つ: `_query`(想起の手がかり q)・`_shop_arrays`(7c の店の行の配列と計数)。既定の道の文は前と同じ |
| `src/shibuya/engine/llm_bridge.py` | `PerceptionRendererAdapter.memory_shown`(既定 None)と、描画の後に呼ぶ 1 か所(見せた行の録画) |
| `src/shibuya/engine/tape.py` | `ARM_COLUMNS`(腕の列の閉じた表)・`TapeWriter.arm_columns`(既定は空=列を足さない)・`_arm_values`・`calls_schema()`・`Tape.column` の空の読み |
| `src/shibuya/engine/systems/build.py` | 腕 on のとき器を作り、描画の口とテープの列を置く・再開で器を作り直す |
| `src/shibuya/engine/systems/table.py` | memory・decide・llm_receive の `writes.paths` に `M0*:mem_layer.memory_store.*`・drain に `M0R:mem_layer.memory_store.*` |
| `src/shibuya/engine/state_ledger.py` | 行 `M0`・`M0R`(§7)・`_M0_ITEMS`・O87 の items に `bridge.tape._arm_values`・持ち主 `mem_layer.memory_store`・除外 2 項(器の設定・テープの腕の列の口) |
| `src/shibuya/engine/manifest_sections.py` | `memory_summary.memory_store`=観測(§8) |
| `src/shibuya/cli.py` | `--memory-store {mem,events}`(指定したときだけ切替口を置く=環境変数より強い) |
| `tests/engine/memory/`(新) | 試験 6 ファイル 44 本(§10)と共通の `_m0.py` |
| `tests/engine/test_state_ledger_10b.py` | 台帳の行の数の試験だけ(外の状態 97 → 99・全体 188 → 190・鍵の列の末尾に `M0`・`M0R`・2 行の軸)。発注の「編集してよい」一覧の外=凍結の表の増えた分(1-3 と同じ扱い) |

## 2. 記憶の行の欄

| 欄 | 列(型) | 中身 |
|---|---|---|
| 目印 `event_id` | `_ms_ev_t_ns`(i8)・`_ms_ev_seq`(i4) | 出来事の id `(t_ns, seq)`。同じ鍵の出来事を重ねた行は**最後の回**を指す(今の表の `mem_last`・`mem_cell` と同じ「最後の回」)。仮の出来事は seq が負(`−1 − 番地`)=記録の id(seq ≥ 0)と重ならない |
| 強さ(System 1 の数・MR-0) | `_ms_n`(u2)・`_ms_imp`(u1)・`_ms_first_ns`(i8) | 回数・重要度・最初に書かれた時刻。強さ A はこれと「いま」から計算する(M0=今の式 `activation_rows`・刻みの単位の近似 #56)。LLM には見せない |
| 出どころ `origin` | `_ms_origin`(i1・−1=空の行) | `None`(記録にある出来事への目印)/`"legacy"`(記録に無い出来事の仮の行)。閉じた表 `ORIGINS` |
| 録画 `shown` | `_ms_shown_ns`(i8・−1=まだ) | 最後に LLM に見せた時刻。この呼び出しで見せたか=その呼び出しの時刻と同じか |
| 注釈 `annotation` | `_ms_note`(番地 → 文字列)・`_ms_note_order` | 一人ずつの注釈=会話の要旨(今の `gist` と同じ 40 字・体あたり 16 件・古い順に落とす・追い出した行は落とす) |
| 仮の出来事の表 | `_lg_kind`(u1)・`_lg_partner`(i4)・`_lg_object`(i4)・`_lg_result`(u1)・`_lg_cell`(i4) | 記録に無い出来事の中身。行と同じ番地(行あたり 1 件・追い出しで上書き)。体の出来事が記録に載る段で記録の目印に置き換わり、この表は消える。仮の行はつなぎ=外す段は親が台帳(1-4)で決める(候補 1-8) |

- 行の範囲: 体 `a` は番地 `[a × n_rows, (a + 1) × n_rows)`(`rows_of`)。`n_rows` は今の表と同じ 128(容量の廃止は M1)。5,000 体で 640,000 行 × 46 B=29.4 MB(腕のランだけ確保・ランの間は一定)。
- `remember(agent, event_id, strength, origin, *, annotation=None)`: 1 回の呼びで 1 体 1 件(今の書き手と同じ回の分け方・配列で受ける)。`origin="legacy"` の目印は `LegacyEvent`(仮の出来事の中身と時刻)で渡し、器が番地に書いて目印を付ける。`strength` は重要度の固定表の base で、器が新しい行に初回 +1・上限 4 を掛ける(今の規則 M3 (b)・Q56)。置き場の規則も今の表と同じ(同じ鍵は重ねる → 空の行 → 満杯なら score 最小を追い出す・同点は番号の小さい方・score は float32 に丸める)。M0 で `origin=None`(記録の出来事への目印)は書けない(`ValueError`=中身の写像は体の出来事を記録に載せる段で足す・段は親が台帳で決める・候補 1-8)。
- `mark_shown(agent, rows, t_ns, *, call=None)`: 描き方が載せた行(`n_rows` 以上=器の外の店の行は印を付けない)に時刻を付け、目印の文字列を返す。テープに列を足すランは、呼び出しの鍵 `(体, t_ns, 起床の級)` でテープの列へ渡すまで控える(`take_shown`)。
- `recall(agent, t_ns, k, *, cue, pool=None, tau=None)`: 今の 6b・7c と同じ選び方(手がかり q に一致する `A ≥ τ` の行を score の降順に k 件 → 足りなければ残りから補う。`pool`=7c の店の評価の行を同じ score の順で競わせ、同じ店は先に選んだ方だけ)。計数は `last_recall`。
- `MemoryView` の欄: `row`・`event_id`・`origin`・`clarity`(はっきり/うろ覚え)・`grain`(そのまま)・`kind`・`partner`・`obj`・`result`・`cell`・`annotation`・`when_ns`・`first_ns`・`valence`・`source`。強さの数(回数・重要度・A・score)は持たない。`row`・`event_id`・`origin`・`first_ns` は録画の同定で、描き方に渡さない(`first_ns` は強さの 1 列の写しでもある=検収 L5・§13 の限界)。
- `render_memories(views, *, clock, poi_names, place_ids, now_ns=0)`: 今の描き方(`memory_item_text` と `compose_memory_line`・テンプレ v1.3)で B5「記憶」の 1 行にする。チャネル 60 tok までが描き方。個体枠 300 との突き合わせは B5・B6 の本文が要るので描画の側に残る。M0 の言葉は全部「はっきり」、粗さは全部「そのまま」で、それ以外は `ValueError`(今のテンプレには言葉の欄が無い=描き方は M1 以降)。

## 3. 腕と配線

- 切替口: 環境変数 `SHIBUYA_MEMORY_STORE`(`mem`=既定・`events`)・`store.set_arm`・CLI `--memory-store`(指定したときだけ置く=環境変数より強い)。組み立て(`build`)のときに読む。`run_day` の引数にはしない(設定の指紋に入れない=出来事の記録の切替口と同じ扱い・§12 仮採用 7)。腕の名は manifest の `memory_summary.memory_store.arm` に出る。
- 腕 on かつ `--memory on` のランだけ器を作る(`MemoryLayer.enable_memory_store`)。記憶 off のランは腕を立てても何もしない(byte-check の `w6_v3_default` で確かめた)。
- 書き: `MemoryLayer._write` が今の表に書いた直後に、同じ出来事を `remember` に渡す。器の選んだ行が表の行と違えば `RuntimeError`。さらに書いた番地の器の値(仮の出来事 5 列・回数・重要度・最初の時刻・目印の時刻と seq・出どころ)を表の値と配列で突き合わせ(`MemoryStore.check_against_table`)、違えば `RuntimeError`(書きの検査の切替口でも外さない=器はハッシュに入らないので、ずれても final とハッシュに出ない。検収 M1)。会話の要旨を置いた後は、器の注釈と表の要旨も比べる。会話の要旨は `note_utterance` が先に決めて `record(annotation=)` で同じ回に渡す。
- 想起: `MemoryLayer.recall` は、器があれば `_recall_from_store` へ行く。手がかり q・k・入口の名・計数は今の道と同じ。器の `MemoryView` を `RecallItem`(刻みの番号に戻す)にして描画へ返す。描画のバイトは変わらない。
- 録画: `PerceptionRendererAdapter.render` が描画の直後に `memory_shown(体, 刻み, 起床の級, recalled_rows)` を呼ぶ(mock の道も艦隊の道もこのアダプタを通る)。テープの書き手は 1 行ごとに `arm_columns["recalled_event_ids"](row)` を呼び、控えを取り出す。
- 再開: 器は戻した記憶の表と要旨から作り直す(`rebuild_memory_store`=`restore_items` の後)。M0 の行は全部が表の写しで、仮の出来事の番地も表の行と同じなので、目印(seq を含む)も通しのランと同じ値に戻る。録画と計数は空から(行 M0R=捨ててよい)。

## 4. 同値の確かめ(約束 (2))

突き合わせ方: 腕 on のランで `MemoryLayer.recall` を包み、抜き取った刻みの**全部の想起**を 2 通りに引く。(a) 器を外した今の表の道(既定の道)と、(b) 器の道。描き方に渡す `RecallItem` の列(候補の集合・順・中身=行・時刻・種類・相手・対象・結果・セル・要旨・店の行の向きと出どころ・最初の時刻)が同じかを見る。(a) で増えた計数は戻す。ランの終わりには、全部の体・全部の行で、器の行と記憶の表が同じかを見る(仮の出来事・回数・重要度・最初と最後の時刻・目印の seq・出どころ・注釈とその順)。

### 4-1. 合成の世界(試験・data 無し・80 体・720 刻み・記憶+関係+同席・店の記憶 on/off)

- 全部の刻みの全部の想起で食い違い 0。表と器の行は全部同じ。final・呼数・想起の計数(`memory_summary.recall`)は腕 on/off で同じ(`test_synthetic_every_recall_is_the_same`)。
- manifest: 腕 on/off で既存の葉は全部同じ。足したのは `memory_summary.memory_store` の下の葉だけ(`test_manifest_differs_only_by_the_store_instrument`)。
- 再開(2 日・12:30 で止めて再開・腕 on): 再開の後の想起も食い違い 0。器は作り直され(`rebuilt_rows` > 0)、表と同じ。再開の後の checkpoint(behavior・full)・final・テープの `recalled_event_ids` と `recalled_rows` が通しのランと同じ(`test_synthetic_two_days_resume_rebuilds_the_store`)。

### 4-2. 世界資産 5,000 体(mock・seed 1・1 日・刻みの 1/7=`T % 7 == 0` を抜き取り)

[recall_equivalence_m0.json](recall_equivalence_m0.json)(`tools/recall_equivalence_m0.py`)。試験 `test_world_5000_sampled_recalls_are_the_same`(`slow`・v3_mem_rel と v3_mem_store)も同じ突き合わせで通った(213 秒)。

| 構成 | 突き合わせた刻み | 呼び出し | うち候補あり | 項 | うち店の行 | 食い違い | final(off=on) | 呼数 |
|---|---|---|---|---|---|---|---|---|
| v3_mem_rel | 179 | 9,787 | 9,008 | 17,779 | 0 | **0** | `73a78288ab5e1498` | 69,111 |
| v3_mem_store | 179 | 9,214 | 8,468 | 16,501 | 1,600 | **0** | `f7ff0a6953fb9a38` | 65,597 |
| v3_classical_mem_rel | 192 | 15,115 | 13,942 | 25,319 | 0 | **0** | `4c512a1fdc2a70c0` | 106,565 |

- 刻みの数は「想起が器を通った刻み」(1/7 の 206 刻みのうち、記憶のある体の呼び出しがあった刻み)。3 構成とも想起の計数(`memory_summary.recall`)も腕 on/off で同じ。
- 壁時計(参考・1 本ずつ・ばらつきは測っていない・on は想起を 2 回引く分を含む): v3_mem_rel 54.7 → 64.2 秒・v3_mem_store 83.2 → 99.6 秒・v3_classical_mem_rel 115.7 → 129.4 秒。

### 4-3. 描き方のバイト(`test_m0_render_bytes.py`)

- 合成の世界(店の記憶 on/off)の全部の描画で、器が返した `MemoryView` を `render_memories` で文にすると、描画が B5 の最後に載せた「記憶」の 1 行とバイトで同じ(個体枠で末尾の項を削った呼び出しは、載せた項の数までの `MemoryView`)。
- 腕 on/off で、全部の描画の B5 の本文と載せた行が同じ。

## 5. `legacy` の行の数

1-3 の出来事の記録に載るのは、世界過程の ActualLog の行と区切り(日の締め・checkpoint)だけで、記憶が書く体の出来事(行為の成否・会話・顕著行為への気づき・看板の初見)は載っていない。だから M0 の記憶の行は全部、記録に無い出来事の仮の行(`origin="legacy"`)になった。記録の出来事への目印(`origin=None`)の行は 0。

| 構成(5,000 体・1 日・腕 on) | 生きている行 | うち legacy | 記録の目印 | 覚えた出来事(`remember`) | 重ねた | 新しい行 | 注釈 | 見せた行の印(のべ) |
|---|---|---|---|---|---|---|---|---|
| v3_mem_rel | 55,465 | 55,465 | 0 | 72,354 | 16,889 | 55,465 | 452 | 124,656 |
| v3_mem_store | 53,234 | 53,234 | 0 | 69,304 | 16,070 | 53,234 | 433 | 105,413 |
| v3_classical_mem_rel | 52,422 | 52,422 | 0 | 62,050 | 9,628 | 52,422 | 365 | 179,024 |

- 合成の世界(80 体・720 刻み): 721 行・全部 legacy。
- 記録の目印に置き換えられそうな出来事: 顕著行為の「警察」(出動 dispatch)と「報道」(press)は世界過程の ActualLog の行=記録の出来事になっている。ただし顕著行為の物(`SalientEvent`)は記録の id を持たないので、気づきの記憶から目印を引けない。世界過程の側に id を渡す配線が要る(1-3 の段の範囲・§12 の限界)。

## 6. テープの列

- 名: `recalled_event_ids`。型: `list<string>`(nullable でない)。値: `recalled_rows` と同じ並びの、見せた記憶の行の目印 `"t_ns:seq"`。器の外の行(7c の店の評価の行=`recalled_rows` の `n_rows` 以上)は空文字。M0 の値は全部仮の出来事なので seq は `−1 − (体 × n_rows + 行)`、`t_ns` はその行の最後の回の時刻(呼び出しの時刻以前)。
- 版: `shibuya.tape/4` のまま(回答 10-13b §3 1-6)。腕を立てたランだけ `calls.parquet` の末尾(22 列目)に足す。**既定 off では列を足さない**(21 列のまま=byte-check の `calls_column_names` は動かない)。列の無いテープを読むと、行ごとに空の list で埋める(`Tape.column`)。再生(`Replay`)は列を読まない。
- 腕の列の表 `ARM_COLUMNS` は閉じた表(`TapeWriter.arm_columns` に表の外の名を置くと `ValueError`)。
- 5,000 体の腕 on の byte-check(§9): `calls_column_names` は 21 → 22 列(末尾に `recalled_event_ids`)・既存の 21 列の sha は全部同じ。
- 予約の列 `recalled_source`(版 4 の「記憶の出どころの欄の予約」)は埋めていない(親の判断=M1 で・§12)。

## 7. 状態台帳と系の宣言

- 行 `M0`(足す前に軸を決めた): 軸 1 **no**(派生と宣言=M0 の器は記憶の表 `mem_*`(behavior・required)と要旨 O8 の写しで、想起の中身は既に behavior-hash に入っている)・軸 2 **derivable**(再開では戻した `mem_*` と O8 から作り直す)・中身は**全部 hash_skip**(作り直せる表=キャッシュと同じ扱い)。道筋 13 個(記憶の行の列 6・仮の出来事の表 5・注釈 2)。
- 行 `M0R`: 軸 1 diag(録画と計数=読み手はテープの列と manifest の計器だけ)・軸 2 discardable。道筋 4 個(`_ms_shown_ns`・`_ms_tape`・`_ms_stats`・`_ms_last`)。
- どちらの行も behavior-hash・full-hash・状態のファイル(`full_items`)に入らない。腕を足しても、腕 off でも on でも、既定の final とハッシュの欄は変わらない(§9)。版は上げない(`state-ledger/10e-ret` のまま・1-3 と同じ仮採用)。全体 188 → 190 行。
- 持ち主 `mem_layer.memory_store` → `engine/memory_store.py` の `MemoryStore`。設定 9 個(`n`・`n_rows`・`ns_per_step`・`minutes_per_step`・`d`・`w_r`・`w_i`・`tau`・`tape_on`)は除外の一覧(定数)。`MemoryLayer.memory_store` は子の持ち主の鍵で網羅される。テープの書き手の `arm_columns` は除外(参照)・`_arm_values` は O87(no・discardable)の items。AST の網羅と実行時の網羅(器ありの `MemoryLayer`)とも漏れ 0。
- 系の宣言: memory・decide・llm_receive に `M0*:mem_layer.memory_store.*`(覚える=行と、計数と新しい行の録画の印を書く・想起の計数・見せた行の録画・テープの列の控え)・drain に `M0R:mem_layer.memory_store.*`(艦隊の残りの呼のテープの行)。段 B(腕 on の合成の世界・全部の欄)で宣言の外の変化 0。器の口(`remember`・`mark_shown`・`take_shown`・`recall`・`rebuild`)は、出来事の記録と同じ形の実行時の検査(`_check_permit`=系の `writes.paths`)を持つ。宣言から外すと書いた所で `PermissionError`(負の対照 2 本)。最初の版では memory に `M0` だけを宣言していて、段 B が `_ms_stats`(M0R)の変化を見つけたので `M0*` に直した。
- SoA の書く列の凍結(`writes_soa_frozen.json`)は変わらない(器は SoA を書かない)。

## 8. manifest(計器)

- `memory_summary.memory_store`(腕 on のランだけ): `arm`・`n_rows`・`row_bytes`(32)・`legacy_row_bytes`(14)・`rows`・`agents_with_rows`・`origins`(`log`・`legacy`)・`annotations`・`shown_rows_live`・`tape_pending`・`counts`(`remember`・`merged`・`new_rows`・`evictions`・`legacy_events`・`recall_calls`・`shown_calls`・`shown_rows`・`tape_rows`・`notes_dropped` ほか)。
- 既存の欄は不変(腕 off でも on でも・§4-1)。
- 節の表(`manifest_sections`)に道筋を 1 つ足した(`memory_summary.memory_store`=観測)。足さないと腕 on のランで「混ざった辞書の節の決まっていない鍵」の試験が落ちる。腕の名も計器の一部として観測に置いた(設定の節の golden `CONFIG_PATHS_SHA256` を変えないため・§12 仮採用 11)。**既定のランの manifest でも `manifest_sections.paths` の葉が 1 つ増える**(既存の葉は不変)。

## 9. 結果不変の確かめ

| 確かめ | やり方 | 結果 |
|---|---|---|
| byte-check([byte_check_m0.json](byte_check_m0.json)) | `10e/byte_check_10e.py`・19 構成・5,000 体・seed 1・1 日・テープつき。head の側は本体 HEAD(`136fdbb`)の src の写し(`git archive`)、m0 の側は作業木の src(`src_is_worktree` 真・腕は既定の mem) | **19/19 構成で 25 欄とも同じ**(final・呼数・blocks・calls の列の名と sha・行動の件数・起床の内訳・顕著行為・出動・食事・behavior/full の最後・締めの後の 2 本・暦・frozen_sources ほか)。既定 v3 の final `5f7ae9ff24005314`(T0・1-3 の記録と同じ) |
| 腕 on の 4 構成([byte_check_m0_arm_on.json](byte_check_m0_arm_on.json)) | 同じ道具で作業木の src を `SHIBUYA_MEMORY_STORE=events` で回し、腕 mem の側と比べた(w6_v3_default・v3_mem_store・v3_mem_rel・v3_classical_mem_rel) | w6_v3_default(記憶 off)は 25 欄とも同じ。記憶の 3 構成で動いたのは `calls_column_names`(末尾に `recalled_event_ids`=21 → 22 列)と `calls_columns_sha`(足した列の分だけ)の 2 欄だけ=「列が増えただけ」。**同値の根拠はテープの既存の 21 列の sha が全部の呼び出しで同じこと**(`recalled_rows`・`recalled_first_tick`・`recalled_kind`・`recalled_object`=見せた記憶の同定・`b5_text`=B5 の本文・`prompt_hash`=プロンプト全体)。final・behavior/full の最後・締めの後の 2 本も同じだが、mock の final は想起の中身に鈍いので根拠にしない(§0) |
| 5,000 体の腕 on/off(§4-2) | 3 構成・ランの中で今の表の道と器の道を直接突き合わせ | 想起の食い違い 0(34,116 呼び出し)・想起の計数が同じ |
| 再開(腕 on) | 合成の世界の 2 日・12:30 で止めて再開(§4-1) | 再開の後の checkpoint・final・テープの列が通しのランと同じ |
| 既存の再開・状態台帳・系の試験 | 全体の試験(§10) | 通った |
| 独立検収の直しの後の 4 構成([byte_check_m0_review_fix_4cfg.json](byte_check_m0_review_fix_4cfg.json)) | §13 の直しの後、本体 HEAD(`fbe2c06`=`136fdbb` と src が同じ)の src の写しと作業木の src(腕は既定の mem)で w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel を回して比べた | **4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`) |
| 置き場を移した後の 4 構成([byte_check_m0_relocated_4cfg.json](byte_check_m0_relocated_4cfg.json)) | 器を `engine/memory_store.py` に移した後、作業木の src(腕は既定の mem)で w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel を回し、上の 19 構成の head の側の同じ 4 構成と比べた(親の指定=移したのは置き場だけなので 19 構成は回し直さない) | **4/4 構成で 25 欄とも同じ** |

## 10. 試験

新しい試験 `tests/engine/memory/`(44 本=`slow` 2 本を含む・data が要るのは `slow` の 2 本だけ。独立検収の直しで 10 本足した):

- `test_m0_store_schema.py`(21): 置き場(`shibuya.engine.memory_store`=1 本のモジュール・`engine/memory.py` は package にしない)・器の import が層の契約の中(import-linter と同じ向きを AST でも)・列の型と範囲・`MemoryView` に強さの数が無い・言葉の段・`__setattr__` と `__slots__` の守り・`remember`(新しい行・重ねる・目印は最後の回・満杯の追い出しが今の表と同じ行・M0 で書けないもの 5 通り)・注釈の規則(16 件・古い順・置き直し)・重要度の上限・`mark_shown` と控え(古い順・テープの無いランは控えない)・実行時の検査(宣言の外 3 通りと `M0`・`M0R` の片方だけの宣言)・系の宣言・状態台帳の行(軸・ハッシュと状態のファイルの外・持ち主の欄の網羅)・実行時の網羅・作り直し(行 M0 だけ・系の外だけ)・切替口・〔検収の直し〕器の値が表とずれたら書いた所で落ちる(負の対照=重要度を 1 減らす)・`del` の抜け道・閉じた表が書き換えられない。
- `test_m0_recall_equivalence.py`(8): 合成の世界の全部の想起(店の記憶 on/off・`memory_n` 128 と、追い出しが 100 回を超える 4 と 3)・manifest の差は器の計器だけ・2 日の再開・(`slow`)5,000 体の 2 構成。
- `test_m0_shown_recorded.py`(4): 腕 on で版 4 の中に 1 列(既存の 21 列は 1 つも動かない・列の無いテープは空で読む・再生の索引の数が同じ)・目印の並びと値(番地・時刻)と計数・最後に見せた時刻がテープと同じ・テープの書き手の腕の列の表が閉じている。
- `test_m0_render_bytes.py`(4): `render_memories` が B5 の記憶の行とバイトで同じ(店の記憶 on/off)・腕 on/off で B5 の本文が同じ・空と M0 の外の言葉。
- `test_m0_writes_declared.py`(3): 段 B(腕 on・全部の欄)で宣言の外 0・宣言を外すと書いた所で落ちる(memory・decide)。
- `test_m0_cli.py`(4): CLI の `--memory-store` が環境変数 `SHIBUYA_MEMORY_STORE` より強い(子のプロセス・テープの列の数で見る)。

独立検収の直しの後: `tests/engine/memory`・`tests/engine/systems`・`tests/engine/time`・`tests/engine/events`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/test_cli.py`(`-m "not gpu"`=`slow` を含む・4 並列)で **420 passed**(5 分 42 秒)。`lint-imports` は 5 契約とも守られている。

非 slow の 32 本で約 1 分(4 並列なし)。`slow` の 2 本は 213 秒。

既存の試験(1-6 に関わるもの): `tests/engine/test_memory_recall.py`・`test_memory_record.py`・`test_store_memory.py`・`tests/engine/time`・`test_tape.py`・`test_tape_wiring.py`・`test_tape_deferred.py`(129 passed・36 秒)・`tests/engine/systems`・`tests/engine/events`・`test_state_ledger_10b.py`(not slow・行の数の試験を直した後)。`lint-imports` は 5 契約とも守られている(器を `engine/memory_store.py` に移した後=190 ファイル・706 の依存。grimp の図に `shibuya.engine.memory_store` が入り、器の import(`engine.memory`・`engine.events.log`・`engine.familiarity`・`engine.systems.guard`・`core.time_consts`・`agents.state`・`perception.normalize`・`perception.renderer`)と呼び手(`cli`・`engine.memory`・`engine.systems.build`)が検査の中にある)。

### 10-1. 全体の試験

`-m "not gpu and not slow" -n 4 --dist loadfile`(data あり・作業木): **4,128 passed・4 failed・1 xfailed(52 分 1 秒)**。同じ機械で 5,000 体の道具を回しながらだったので、時間は T0・1-3 の記録(13 分台)より長い。

- 落ちた 4 件のうち 3 件は 1-6 の不具合: `tests/engine/test_state_checks_10f.py` の外の状態の軸 1 の AST(10f)が、器の読み口のプロパティ名 `stats` を「ほかの持ち主の診断の欄 `stats`(O6・O11 ほか)を持ち主の外で読んだ」と「名前の衝突」として捕まえた。プロパティの名を `store_counts` に替えて直し、`tests/engine/test_state_checks_10f.py` と `tests/engine/memory`(not slow)を回し直して **56 passed**(4 並列・4 分 49 秒)。外の状態の軸 1 の AST の検査は 0 件。名を替えたのは byte-check(§9)と 5,000 体の道具(§4-2)を回した後。替えたのは計器の読み口の名だけで、既定の道も腕の道も値は変わらない(回し直してはいない)。
- 残る 1 件は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(テープの道筋が `data/tape/` で始まらない)。作業木の `data` が本体への junction であることで起きる既知の落ち([1-0 の記録](../run-day-decomp/impl-1-0.md) §1・T0 と 1-3 の記録と同じ。本体では通る)。
- 秘密の走査(`tools/scan_secrets.py`・変えたファイルと新しいファイル 22 本)は CLEAN。
- **置き場を移した後(親の判断・§12 仮採用 1)**: `tests/engine/memory`・`tests/engine/systems`・`tests/engine/time`・`tests/engine/events`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_ledger_10b.py`(`-m "not gpu"`=`slow` を含む・4 並列)で **395 passed**(6 分 10 秒・5,000 体の 2 本と 1-3 の 19 構成の on/off を含む)。ほかに `test_memory_recall.py`・`test_memory_record.py`・`test_store_memory.py`・`test_tape*.py`・`tests/test_cli.py` で 98 passed(36 秒)。`lint-imports` は 5 契約とも守られている(190 ファイル・器が図に入る)。

## 11. 触った共有ファイル(親が取り込み順に rebase するときの一覧)

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/systems/table.py` | memory・decide・llm_receive・drain の `paths=` の末尾に 1 項ずつ(4 か所)・冒頭の docstring に 1 段落 |
| `src/shibuya/engine/state_ledger.py` | 冒頭の docstring の行数・`LEDGER_VERSION` の注(版は不変)・`_M0_ITEMS`(`_EXT` の直前)・O87 の items に 1 項・`_EXT` の末尾(行 E の後)に行 M0・M0R・`OWNER_CLASSES` に 1 項(`mem_layer.store` の直後)・`EXCLUDED` に 2 項(`mem_layer.store` の後と `bridge.tape` の後) |
| `tests/engine/test_state_ledger_10b.py` | `test_ledger_has_187_rows_in_two_axes` の数と鍵の列(凍結の表の増えた分) |
| `src/shibuya/cli.py` | `--events` の直後に `--memory-store`・`run(...)` の直前に切替口を置く 4 行 |
| テープの列 `src/shibuya/engine/tape.py` | 冒頭の docstring・`ARM_COLUMNS`・`TapeWriter` の欄 2 つと `calls_schema`・`append`・`flush`(列の辞書を変数に・字下げは前のまま)・`close`・`Tape.column`・`__all__` |
| `src/shibuya/engine/systems/build.py` | 6b の τ の直後に器の配線(10 行)・再開の `restore_items` の直後に 2 行 |
| `src/shibuya/engine/llm_bridge.py` | `PerceptionRendererAdapter.__init__` に 1 欄・`render` に 3 行・`typing` の import |
| `src/shibuya/engine/manifest_sections.py` | `memory_summary.recall` の後に 1 道筋 |
| `src/shibuya/engine/memory.py` | (1-6 の持ち場)`MemoryLayer` の器の口と腕の想起・`_query`・`_shop_arrays` の取り出し・`_write`・`record`・`note_utterance`・`summary` |

凍結の表(`writes_soa_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`・`manifest_keys_frozen.json`・`writes_paths_events.json`・`CONFIG_PATHS_SHA256`)は変えていない。描画(`perception/renderer.py`)は触っていない。

## 12. 限界・仮採用・親に確かめてほしい点

**仮採用(10-13b §0-3)**: 既存の決定と原文から答えが出なかった所。どれも腕の裏で、既定の final は動かない(§9)。

1. **置き場=`engine/memory_store.py`(1 本のモジュール・親の判断・第 1 期 1-6 の検収)**。口の約束の置き場は `engine/memory/store.py` だが、今の `engine/memory.py` があるので、そのままでは置けない。最初の版は `engine/memory.py` に `__path__` を置いて下の `memory/store.py` を引いたが、`memory/` に `__init__.py` が無いので import-linter(grimp)と setuptools の package の発見の外になり、層の契約の検査が効かなかった(lint は 189 ファイルのまま)。親の判断(10-13b §0-3「既存のコードにこだわらない」=構造の素直さを優先)で 1 本のモジュールに移し、`__path__` を消した(`engine/memory.py` は HEAD の中身+器の口だけ)。移した後は lint が 190 ファイルで器を見る(§10)。`memory.py` を package に移す案は、既存の試験 2 本(`engine/memory.py` を AST で読む)と状態台帳の持ち主の道筋が変わるので取らない。状態台帳の道筋 `mem_layer.memory_store.*` は持ち主の属性の名なので変えない。
2. **目印は「最後の回」の出来事**: 同じ鍵の出来事を重ねた行は最後の回を指し、最初の時刻は強さの数に持つ(今の表の `mem_last`・`mem_cell` と `mem_tick` に合わせた)。M1 の「直近の数回は本当の時刻」(MR1)は、行に回の列を持たせるか記録の目印を複数にするかで決め直す。
3. **強さの欄**: 回数・重要度・最初の時刻の 3 列。`remember` の `strength` 引数は重要度の固定表の base(器が初回 +1・上限を掛ける)。
4. **仮の出来事の表は行と同じ番地**(目印 `(t_ns, −1 − 番地)`)。再開で作り直しても同じ id になる。追い出すと上書き。
5. **器の置き場の規則は器自身が持つ**(今の表と同じ規則の写し)。今の表の書き手が選んだ行と、書いた番地の値が違えば `RuntimeError`(腕 on のランは毎回の書きで同値を確かめる・検収 M1)。
6. **状態台帳 M0=no・derivable・中身は全部 hash_skip**(作り直せる表)・M0R=diag・discardable・版は上げない。A2 (b) の「どれかの腕で描画に使う読み手があれば behavior」に対し、「派生として入れない」と宣言した(想起の中身は mem_* と O8 で既に behavior-hash に入る)。M1 で器を既定の記憶にする段で behavior・required に移す(版上げ)。
7. **切替口は環境変数と CLI**(`run_day` の引数にしない=設定の指紋に入れない)。器は結果を変えない(同値)ので、出来事の記録の切替口と同じ扱い。M1 で式を変える腕は結果を変えるので、そのときは `run_day` の引数(設定の指紋)にする。
8. **テープの列の値は文字列** `"t_ns:seq"`(id の組を 1 列に入れるため)。器の外の行は空文字。
9. **録画の口は描画のアダプタ**(`PerceptionRendererAdapter.memory_shown`)と**テープの書き手**(`TapeWriter.arm_columns`)。描画(`perception/renderer.py`)は 1-2 が作り直している最中なので触らなかった。艦隊の道(非同期)は控えの鍵 `(体, t_ns, 起床の級)` で結ぶが、艦隊の道の試験はしていない(偽 vLLM の道は未確認)。
10. **言葉の段の境目は τ**(A ≥ τ=はっきり)。M0 の想起は A ≥ τ の行だけを返すので、全部「はっきり」になる。粗さは「そのまま」だけ。`render_memories` は M0 の外の言葉と粗さを `ValueError` にした(描き方を足すのは M1 以降)。
11. **manifest の計器は観測の節**(腕の名を含む)。節の表に道筋が 1 つ増え、既定のランの `manifest_sections` の葉も 1 つ増える。
12. **7c の店の評価の行(`sm_*`)は器の外**。器の想起の内側で同じ score の順に競わせる(`ShopPool`)。人・店・出来事を同じ器に入れるのは M1。
13. **器の口の実行時の検査**(`_check_permit`=系の `writes.paths`)を足した。口の約束は段 B だけを求めるが、1-3 の出来事の記録に合わせた。

**限界**:

- **出来事の記録は discardable・保持窓 7 日**(1-3): 記憶の行が記録の出来事を指す段になると、目印の先が再開と 7 日で消える。MR11 (b) を実の目印にする段で、記録の保持と再開(required にするか)を決め直す必要がある。M0 は全部 legacy なので今は困らない。
- MR16 (c)「System 1 と判断モデルが使った親しみまで録画」のうち、M0 で録るのは B5 に載せた記憶の行だけ。親しみ・関係辺・店の評価の行(器の外)の録画は範囲の外。
- `__setattr__`・`__delattr__` は欄の付け替えと削除を守る。配列の中身と注釈の dict は口の外からも書き換えられる(1-3 の L2 と同じ限界)。段 B と実行時の検査が系の宣言の外の書きを捕まえ、表とのずれは書くたびの値の突き合わせが捕まえる。
- 器は腕のランで 5,000 体あたり約 29 MB の配列を持つ(容量 128 行のまま)。
- 用語集との照合はしていない(新しい語は「記憶の器」「目印」「仮の行」「録画」=口の約束と決定の語)。

**親の判断(第 1 期 1-6 の検収・確かめてほしい点への答え)**:

1. 置き場: `__path__` をやめ、`engine/memory_store.py` に移す(仮採用 1 に反映)。
2. テープの予約の列 `recalled_source` に器の `origin` は**入れない**(腕 on で既存の列の値が動く=M1 で)。
3. `stats` → `store_counts` の改名は認める(§10-1)。
4. 次は「限界」のまま: 気づきの記憶を記録の目印にする配線(出動・報道の顕著行為の物に ActualLog の出来事の id を持たせる・§5)・艦隊の道(非同期)の録画の控えの試験・出来事の記録の保持と再開(実の目印にする段)・MR16 (c) の器の外の行の録画・`Percept` への結線(`render_memories` を 1-2 の `Percept` の記憶の欄から呼ぶ=1-2 の取り込みの後)。

## 14. 親の検収(第334・2026-10-14)

- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・既定 off・w6_v3_default/w6_v3_activity_off/w6_v1_default/v3_mem_rel・memory_store.py へ移した後): final が同じ 4/4・動いた欄 0(parent_head_vs_m0_4cfg.json)。
- 置き場を engine/memory_store.py に移す判断は親(__path__ の細工は import-linter の外になるため)。独立検収(review.md)=条件つき受入 → M1(器と表の値の突き合わせ)と低 L1・L2・L3・L4・L6・L9・L10 を実装役が直した(§13)。親の答え: L7(既定の manifest の葉が 1 つ増える=観測の節)は「既存の欄は不変」の範囲として認める・M2(legacy の行はつなぎ)は 1-4 の台帳に親が載せる(外す段=体の出来事を記録に載せる段・候補 1-8)。直しの後の試験 420 passed・byte-check 4 構成 同じ(実装役)。

## 13. 独立検収(review.md)と直し

- **判定: 条件つき受入**(高 0・中 2・低 10)。検収役は実装を見ずに、byte-check 4 構成(25 欄とも同じ)・腕 on・別の方法の同値(腕 off と on を別々に回して想起の列を突き合わせ・追い出しが 382〜764 回の 4 本・食い違い 0)・描き方のバイト・宣言と台帳・lint を確かめた。
- **M1(中・直した)**: `_write` の実行時の検査が行の番号しか見ていなかった(器の値がずれても、器は hash_skip なのでハッシュにも mock の final にも出ない)。書いた番地の器の値(仮の出来事 5 列・回数・重要度・最初の時刻・目印の時刻と seq・出どころ)を表の値と配列で突き合わせ、違えば `RuntimeError`(`MemoryStore.check_against_table`・読むだけ・書きの検査の切替口でも外さない)。会話の要旨を置いた後は注釈も比べる。負の対照 1 本(重要度を 1 減らすと「重要度」で落ちる)。記録 §0・§9 の書き方を、final でなくテープの既存の 21 列の一致と直接の突き合わせを根拠にする形に直した。
- **M2(中・親の台帳の作業)**: 仮の行(legacy)はつなぎ。1-4 を取り込んだ後に親が台帳に載せる(外す段=体の出来事を記録に載せる段)。記録 §2 と `memory_store.py` の「1-8・1-9」を「親が台帳で決める(候補 1-8)」に直した。
- **低の直し**:
  - L1: `__delattr__` も落とす(`del` の後に付け替える抜け道を閉じた・負の対照 1 本)。
  - L2: 閉じた表 `tape.ARM_COLUMNS`(既定の値も tuple に)と器の `_COL_SPEC` を `MappingProxyType` に(試験 1 本)。
  - L3: `rebuild` は行 M0 の欄だけを作り直し、録画・控え・計数(行 M0R)を触らない。作り直しの数は記憶の層の計数 `memory_store_rebuilt_rows` へ。系の中(ランの途中)では呼べない(`RuntimeError`・試験 1 本)。
  - L4: 付け替えてよい欄の表 `_REBIND` をなくした。テープの印 `tape_on` は `attach_tape` の中だけ、最後の想起の計数は `recall` の中だけで置く(試験で外からの付け替えが落ちる)。除外の一覧から `_REBIND` を消した(設定 9 個)。
  - L6: 新しい関数 `_shop_arrays`・`_recall_from_store` の引数名 `tick` を `step` に(T0 の規則)。
  - L9: CLI `--memory-store` が環境変数より強い試験 4 本(`test_m0_cli.py`・子のプロセス)。
  - L10: 同値の試験に `memory_n` 4 と 3 の構成を足した(追い出しが 100 回を超えることも確かめる)。
- **記録の限界にしたもの**:
  - L5: `MemoryView` に録画の同定の欄(`row`・`event_id`・`origin`・`first_ns`)が入っている。描き方には渡さない(§2)。`first_ns` は強さの 1 列の写しでもあるので、LLM に見せる形を厳密にするなら同定の欄を別の組に分ける(1-2 の `Percept` に結線するときに)。
  - L7: 既定のランの manifest でも `manifest_sections.paths` の葉が 1 つ増える(観測の節)。親が「既存の欄は不変」の範囲として認めた(§8)。
  - L8: 艦隊の道(再送・落ちた呼)の録画の控えは試験が無い。残った控えは `_ms_tape` に溜まる(計器 `tape_pending` に出る)。偽 vLLM の道の試験は後で。
- **rebase の後(第334)**: 枝を本体(1-4 取り込み済み 6b82be2)に rebase(衝突は cli.py の 1 か所=1-4 の run_kind の呼び口と 1-6 の腕の口・両方を残して親が解決)。rebase 後に親が試験の一部 516 passed(5 分 38 秒)と byte-check 4 構成(新しい本体の src と比べて final 同じ・動いた欄 0=parent_head_vs_m0_rebased_4cfg.json)を確かめた。
