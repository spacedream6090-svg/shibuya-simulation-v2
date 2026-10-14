# 第 1 期 1-8 候補の口 J0 の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-8/decision-port`(HEAD `f60b0a6`=T0・1-3・1-4・1-6・1-9・1-2 を取り込んだ後)。commit は親。
- 正: [口の約束 1-8](../../../../design/v2-foundation-contracts-2026-10-13.md)(〔決定〕=「その他」の割合の既定は R-108 の値・驚きと迷いは空で始める)・[計画 1-8](../../../../design/v2-implementation-plan-2026-10-12.md)・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-7(DM-0・DM4・DM5・DM13)・§4-12 C-2・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §4-2・§0-3・[判断モデルの草案](../../../../design/v2-decision-model-design-round-draft.md) の〔答え〕・[R-108](../../../../research/v2-r108-option-format-bias-and-llm-persona-drift.md) §1-5・§3・[R-113](../../../../research/v2-r113-e1-foundations-existing-implementations.md) §9。
- 先例(形だけ借りた・コードは写していない): Concordia(Apache-2.0)`concordia/document/interactive_document.py` の `multiple_choice_question`(候補を並べ替えて記号を振り、選ばれた記号を元の番号に戻す)と `language_model.sample_choice`(実 LLM と mock が同じ入口)。違い: 並べ替えは乱数の鍵(10c の counter=`core.rng.k19_counters`)から決める(Concordia は rng を渡さないと種なし)。
- 数は実測。生の出力(テープ・side の JSON)は作業木の `_bc/`(git の外)。比べた結果と道具だけをこのフォルダに置く。道具は `tools/`(`cause_bytes.py`=原因の表の 1 呼あたりの保持バイト・`arm_pair.py`=腕 legacy/port を同じ構成で回して判断の番号列と計器と壁時計を比べる)。byte-check は既存の `10e/byte_check_10e.py`。

## 0. 結論

- **口**: `src/shibuya/engine/decision/`(`port.py`=型と提示・`sources.py`=5 つの源から候補・`ports.py`=3 つの実装・`layer.py`=腕と層)。`DecisionPort.choose(ctx, candidates) -> Choice` の 1 つの口に `MockPort`・`ClassicalPort`・`LlmPort` が同じ入口で乗る(3 つとも `choose` を上書きしない=並べ替えと元の id への戻しは土台のクラス)。
- **腕** `--decision-port {legacy,port}`(環境変数 `SHIBUYA_DECISION_PORT`・既定 legacy=今の道=層を作らない)。port で判断の系の 1 呼を「前半(知覚の事実まで=`LLMBridge.begin`)→ 候補(5 つの源)→ 口 → 後半(`LLMBridge.finish`=今の「文 → 2 行形 → パーサ → 語彙」・プロンプトは変えない)」にし、**口が選んだ候補の行為のコードを適用する**(今の道のコードと違えば計器 `mismatch` に数える)。
- **結果不変**: byte-check 19/19 構成で 25 欄とも HEAD と同じ(既定 legacy)。**腕 port の 4 構成も 25 欄とも HEAD と同じ**(テープの全部の列・behavior/full の最後・締めの後の 2 本を含む)。5,000 体の 1 日で判断の番号列(呼ごとの刻み・体・適用したコード)が腕 on/off で一致(mock 65,597 呼・古典+記憶+関係 106,565 呼)・`mismatch` 0(§6)。負の対照(mock の番号を 1 つずらす)は `mismatch` が出て final が動く。
- **1-3 の検収 M2(原因の表を列に)**: `engine/events/log.py` の原因の表を列(種類・参照・call_id の 3 整数・入力の出来事 id の範囲・選んだ候補の源と提示の番号)+入力の id の 2 列にした。1 呼あたり HEAD 198〜1,002 B(入力 0〜8 個)→ 列の幅 39 B+12 B/入力(倍化の余りを含む実測 64〜221 B)。39 万体 7 日の見積りは 7.1〜35.8 GB → 1.4〜4.8 GB(§5)。読み口 `event(i).cause` は今の 3 型を組み立てて返し、1-3 の既存の試験(`tests/engine/events` 90 本)は assert を変えずに通る。
- **候補の源の記録**: 腕 port のランは判断 1 つに出来事 1 行(`行為:<語>`・`cause=LlmCall(call_id, 候補の元の出来事 id, source=選んだ源, number=提示の番号)`=call_id はテープの call_id と同じ)。源の分布・「その他」の割合・選んだ提示の番号の集計は manifest の `decision_port`(計器)。
- **独立検収(review.md)=条件つき受入 → M1・M2・L1・L2・L4 を直した**(§13)。H1(1-5 の `CAUSE_PROCESS_NAMES`)は rebase の後に直す。
- 試験: 新しい試験 58 本+slow 1 本(`tests/engine/decision/`・§7・検収の直しで 51 → 58)。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/decision/port.py`(新) | `Candidate`・`Choice`・`Hesitation`・`DecisionContext`・`DecisionPort`・`present`/`present_rng`(順のシャッフルと番号)・`options_text`・`compose`(短い版と長い版)・定数(5 つの源・「その他」・驚きの 6 語・「その他」の既定と出典) |
| `src/shibuya/engine/decision/sources.py`(新) | `build_candidates`(5 つの源+語彙の残り=つなぎの印 `vocab`)・`memory_kind_words`(記憶の種類 → 語=`engine.memory.ACTION_KIND` の逆) |
| `src/shibuya/engine/decision/ports.py`(新) | `LlmPort`・`MockPort`・`ClassicalPort`(§3) |
| `src/shibuya/engine/decision/layer.py`(新) | 腕(`arm`・`set_arm`・`SHIBUYA_DECISION_PORT`)・`DecisionLayer`(1 呼を口に通す `decide_one`・周りが示すできること `affordance_words`・計器 `meter` と `observed`・判断の出来事)・`manifest_fields` |
| `src/shibuya/engine/events/log.py` | 原因の表を列に(M2・§5)。`CAUSE_ROW_BYTES`(37)・`INPUT_ID_BYTES`(12)・`cause_nbytes` |
| `src/shibuya/engine/llm_bridge.py` | `CallStart`・`LLMBridge.begin`/`finish`/`code_of_word`・`call` の描画の後を `_after_render` に出した(文は同じ・`finish` は応答の口 `complete` を差し替えられる)。`PerceptionRendererAdapter.perceive_call`/`render_call`(`render` を前半と後半に分けた口・`render` は今のまま=共通の後半を `_wrap` に出しただけ) |
| `src/shibuya/engine/classical.py` | `ClassicalPolicy.render` の中身を `answer`(5 つの答え)に移し、`render`=`answer` を並べた文・`complete_with_answer`(応答・計数は `complete` と同じ+答えの 5 つ) |
| `src/shibuya/llm/mock.py` | `MockLLM.action_draw`(`render` と同じ鍵・同じ形で行為の抽選の 1 語目を引き直す) |
| `src/shibuya/engine/systems/decide.py` | 腕 port のときだけ `decision_layer.decide_one`(既定の道は `bridge.call` のまま)・艦隊の道は数えるだけ |
| `src/shibuya/engine/systems/build.py` | 腕 port のときだけ層を作る(方策で実装を選ぶ)・`Layers(decision=…)` |
| `src/shibuya/engine/systems/boxes.py`・`state_io.py`・`run_end.py` | `Layers.decision`(既定 None)・持ち主の名の末尾に `decision`・結果に `decision_layer` |
| `src/shibuya/engine/systems/table.py` | decide の `paths` に `J0:decision.* E:events.*`・`reads` に `layers.decision`・close_final の `reads` に `layers.decision` |
| `src/shibuya/engine/state_ledger.py` | 行 `J0`(§4)・行 `E` の道筋の名(原因の表の列)・持ち主 `decision`・除外 3 行 |
| `src/shibuya/engine/run.py`・`manifest_sections.py` | manifest の末尾に `decision_port`(混ざった辞書=設定 7・観測 12)・乱数の用途名 `decision.present`(動きの側) |
| `src/shibuya/engine/rng_audit.py` | 決まらない呼び手に `present_rng`・安全な呼び手の場所 `ClassicalPolicy.render` → `answer`・作り直しの許可に `llm.mock`(MockPort) |
| `src/shibuya/cli.py` | `--decision-port {legacy,port}`(指定したときだけ置く=環境変数より強い) |
| `docs/design/bridging-ledger.json` | つなぎの台帳に 4 行(§8) |
| 凍結の表と試験(増えた分だけ) | §9 |

## 2. 口の型

| 型 | 欄 | 約束 |
|---|---|---|
| `Candidate`(凍結・slots) | `id`・`kind`(行為の語か「よく考える」)・`text`(頭に浮かんだこととしての見せ方)・`source`(5 つの源・J0 だけ `vocab`)・`number`(提示の番号=`present` が**最後に**振る・作る側は None)・`basis`(元の出来事 id=1-3 の `EventId`) | id は「その他」の id を使えない・id の重なりは提示で落ちる |
| `Choice`(凍結・slots) | `candidate_id`・`number`(選んだ提示の番号)・`kind`・`other_text`(「その他」の自由記述)・`surprise`(0〜5・**空で始める**)・`hesitation`(迷い=1 位と 2 位の差+エントロピー・**空**)・`continuous`(DM13 の連続値の欄・**空**)・`reason`・`reason_first`(理由を先に=C-2 の 2・LLM の側だけ True)・`utterance`(**1-8b の欄・空**)・`backend`(口の後ろの今の道の結果・比べない) | 「その他」は `kind` なし・自由記述は「その他」だけ |
| `DecisionContext`(凍結・slots) | 呼の鍵(体・刻み・`t_ns`・級・起床の条件・セル・`call_id`)・**`percept`(今の観測=1-2 の `Percept`)と `prediction`(本人の予想=今は空)を並べて**・`memory`(記憶の見え方=`Percept.memories`)・`tools`(1-7 の後=今は空)・`inviter`・`last_action`・`request`(今の道の前半 `CallStart`) | `perception.facts.PerceptCarrier` の形。口は値を解釈しない(予想を入れても答えは同じ=試験) |
| `DecisionPort` | `choose(ctx, candidates) -> Choice` | 並べ替え → 実装の `_answer`(提示の候補の id か「その他」)→ 元の id と提示の番号に戻す。提示に無い id は `ValueError` |

- 短い版と長い版(DM4): `compose(blocks, presented, length)` 1 つの関数で、共通部分(描画の共有ブロック B0〜B4b)→ 人ごと(短い版 B6・長い版 B5+B6)→ 提示(「頭に浮かんだこと:」・番号つき・最後に「その他(自由に書く)」)→ 長い版だけ「先に理由を自由に書き、最後に番号をひとつ書く」。同じ状態から両方の先頭(共通部分)が同じバイト(試験)。**J0 のランでは使わない**(プロンプトは今のまま)。
- 驚きの言葉(DM5 の答えのまま): 予想どおり・少し違う・違う・かなり意外・とても意外・ありえない(`SURPRISE_WORDS`)。迷いは `Hesitation.of(分布)`(判断モデルが分布を返す段で使う)。

## 3. 3 つの実装(同じ入口)

| 実装 | 選び方 | 口の後ろ |
|---|---|---|
| `MockPort`(方策 mock・記録のラン) | `MockLLM.action_draw`=**今の mock と同じ鍵**(`llm.mock`・(刻み, 体, 起床の級))の 1 語目 `a`。候補のうち mock の語彙の語を語彙の順に並べ、`a % 数` の候補を選ぶ=中身で選ぶ(提示の並べ替えに左右されない)。語彙の全部が候補にあれば今の mock と同じ語 | 今の mock の本文を通す(対象・活動・まで・テープの行) |
| `ClassicalPort`(方策 classical) | 古典の方策 G の答えの 5 つ(`answer`)の行動の語を同じ種類の候補に写す(本文を読み直さない)。再生のラン(方策を呼ばない)は今の道の語 | 同じ方策の口を包んで渡す(`complete_with_answer`=応答・計数・副作用は `complete` と同じ) |
| `LlmPort`(テープの再生・注入の LLM) | 今の道の答えの行為の語(2 行形のパーサの `action`)を同じ種類の候補に写す。どの候補にも当たらない答え(語彙の外・役割語・未定義の語・書式の誤り)は「その他」=`other_text` に答えの語 | 今の「文 → 2 行形 → パーサ → 語彙」(プロンプトは変えない) |

適用するコード: 候補を選んだら `LLMBridge.code_of_word(語)`(`call` がパーサの語に当てるのと同じ=役割語は安全弁)、「その他」と「よく考える」は今の道のコード(未定義行動の段 0 の辞書と記録を通った値)。LLM の口は作りから今の道と同じコード。

- 艦隊の道(`fleet_bridge`)は J0 では口を通さない(呼の数を `fleet_legacy` に数える)。再生の繰り延べと後の刻みに届く答えは今の道のまま(到着の刻みで今の道が適用=`late` に数える)。
- 驚き・迷い・連続値・ひと言は 3 つとも空(〔決定〕・1-8b)。

## 4. 候補の 5 つの源と記録

`build_candidates`(読むだけ・並びは 1 → 5・同じ語は先の源の 1 つだけ):

1. 続ける(`continue`): その版の安全弁の語(v3 の「なし」・v1/v2 の「待機」)。
2. 近い予定(`plan`): `Percept.intent` の行為(今の意図)。
3. 本人の経験(`experience`): 想起した記憶(`Percept.memories`)の種類を行為の語に戻した物(`engine.memory.ACTION_KIND` の逆)。元の出来事 id(1-6 の器の行で出どころが記録 `log` の物)を `basis` に。
4. 周りが示すできること(`affordance`): **場所の種類と営業時間から機械的に作る仮の源**(親の補足=1-7 が未着手のため・つなぎの台帳 1-7 で外す)。移動=いつでも・乗車=路線のホームのセル・購入=セルに営業中の飲食店でない店・食事=営業中の飲食店・並ぶ=営業中の店・会話=見えた人がいる・就寝=自宅のセル・断る=招待がある。営業中の店は刻みごとに 1 回 `world.open_mask` から作る。
5. よく考える(`deliberate`): 1 つ(行為の語ではない=エンジンは実行しない・mock と古典と今の LLM の道は選ばない)。

どの源も出さなかった語彙の横断語は **`vocab`(つなぎの印)** で残す(DM-0 は「設計者の一覧ではなく 5 つの源から」だが、約束 (2)「腕 on で mock の行動の分布が今と同じ」には語彙の全語が候補に要る=仮採用・§10)。

**記録**(約束 (3)):

- 判断の出来事: 腕 port のランで適用した判断ごとに 1 行(`who`=体・`what`=`行為:<語>`・`where`=セル・`cause=LlmCall(call_id, 候補の basis の和, source=選んだ候補の源, number=提示の番号)`)。call_id はテープの `call_id` 列と同じ値(試験)。**選んだ源と提示の番号は判断ごとに原因に残る**(検収 M1 の直し=§13。原因の表の列 `_cz_src`・`_cz_num` の 2 B/判断。分布は口の計器と同じ=試験)。出来事の語彙表(v3 の行為 12 語)に無い語(v1/v2 の降車・待機・休憩)と「その他」は書かず `events_unlogged` に数える。J0 では元の出来事 id を持つ候補が無い(1-6 の器の行は全部 `legacy`=仮の行)ので `input_event_ids` は全部空。
- 計器(manifest `decision_port`・状態台帳の行 J0=軸 1 diag・軸 2 discardable): 判断の数・`late`・`fleet_legacy`・提示した候補の源の分布・選んだ候補の源の分布(と「その他」)・「その他」の数と割合・選んだ提示の番号の分布(位置の偏りの記録=R-108 §3-1 (i)「ID の事前分布を記録するだけ」)・候補の数の分布・`mismatch`・判断の出来事の行。腕 legacy のランは観測の子が null。

5,000 体・1 日の腕 port([arm_pair_j0.json](arm_pair_j0.json)):

| 構成 | 判断 | 提示の源(experience / affordance / plan / continue / deliberate / vocab) | 選んだ源(同じ順・other) | 選んだ番号 1〜13 の件数 |
|---|---|---|---|---|
| mock・既定 v3 | 65,597 | 0 / 270,496 / 126 / 65,597 / 65,597 / 450,945 | 0 / 22,685 / 9 / 5,350 / 0 / 37,553 / 0 | 4,952〜5,148(ほぼ一様) |
| 古典+記憶+関係 | 106,565 | 102,924 / 373,193 / 546 / 106,565 / 106,565 / 695,552 | 13,289 / 19,665 / 229 / 69,784 / 0 / 3,598 / 0 | 7,987〜8,377 |

候補は毎回 13(語彙 12+よく考える)。mock の「選んだ源」の 57% が `vocab`(語彙の残り)=J0 の候補の集合が今の道の語彙のままであることを数で示す(6-1 で減らす相手)。

## 5. 原因の表の列化(1-3 の検収 M2)

| | HEAD(呼び出しごとの Python の物) | J0(列) |
|---|---|---|
| 持ち方 | `list[原因]`+`dict[原因 → 番号]` | 原因の表の列 9 本(`_cz_kind` i1・`_cz_ref` i4・`_cz_call_t` i8・`_cz_call_agent` i8・`_cz_call_cls` i4・`_cz_in_start` i8・`_cz_in_len` i4・`_cz_src` i1・`_cz_num` i1=**39 B/行**)+入力の id の 2 列(`_ci_t` i8・`_ci_seq` i4=**12 B/個**) |
| 1 呼あたり(入力 0 / 2 / 8 個・tracemalloc・2 万呼) | **198 / 402 / 1,002 B** | 64 / 103 / 221 B(倍化の余りを含む実測)・列の幅は 39 / 63 / 135 B |
| 39 万体 7 日(13.1 呼/体/日) | 7.1 / 14.4 / 35.8 GB | 実測 2.3 / 3.7 / 7.9 GB・列の幅 **1.4 / 2.3 / 4.8 GB** |

検収 M1 の直しの前(列 7 本=37 B/行)の実測は 61 / 100 / 218 B だった(+2 B/行=選んだ源と提示の番号)。

[cause_bytes_j0.json](cause_bytes_j0.json)(道具 `tools/cause_bytes.py` を HEAD の src と作業木の src で回した)。1-3 の検収 M2 の見積り(221〜525 B/呼・7.9〜18.8 GB)は入力 0〜2 個の範囲で HEAD の実測と同じ桁。

- 読み口 `event(i).cause` は 3 型を組み立てる: `LlmCall` は列から(テープの形 `"{T}:{体}:{級}"` の call_id は 3 つの整数・そうでない call_id=試験だけは文字列の小さな表)・`Process` は過程の名の番号から・`Experiment` は口 `gate.admit` が作った物を条件の名ごとに 1 つ持って返す(口の外で作らない=CP12 のまま)。
- 同じ原因の行は 1 つ: 過程と実験は名で(名の数で頭打ち)・LLM の呼び出しは「直前に書いた呼び出しと同じ」ときだけ(呼び出しごとの dict を持たない)。HEAD の dict は離れた行の同じ呼び出しもまとめた=表の行の数(`n_causes`)はその場合だけ HEAD より多くなる(今のランでは呼び出し 1 つに出来事 1 行=差は無い)。
- 保持窓の詰め直しは列の添字の演算(`np.unique`・`np.repeat`)。無作為の書き込みと素朴な写しの突き合わせ(5 日・保持窓 2 日)で読み返しと種類の分布が同じ(試験)。
- **腕 port で増える量(新しい成長)**: 判断の出来事は 13.1 行/体/日 → 39 万体 7 日で出来事の行 72 B × 3,576 万行=2.6 GB+原因の表 1.4 GB=約 4.0 GB(M8=24 GB の約 17%)。既定の腕では増えない。**成長の宣言**(`EventLog.growth_declaration(decision_rows_per_agent_day=…)`)は腕 port のときだけ判断の出来事の行(1 行=72+39 B)を足す=口の層の `DecisionLayer.event_growth()`(値は mock・既定 v3 の実測 13.1 行/体/日=`DECISION_EVENT_ROWS_PER_AGENT_DAY`・古典+記憶+関係は 21.3)。腕 legacy の宣言は今のまま(検収 L2=§13)。

## 6. 結果不変

| 確かめ | 方法 | 結果 |
|---|---|---|
| byte-check([byte_check_j0.json](byte_check_j0.json)) | `10e/byte_check_10e.py`・19 構成・5,000 体・seed 1・1 日・テープつき。head=本体 HEAD `f60b0a6` の src の写し・j0=作業木の src(`src_is_worktree` 真・腕は既定 legacy) | **19/19 構成で 25 欄とも同じ**(final・呼数・blocks・calls の全部の列の sha・行動の件数・起床の内訳・顕著行為・出動・食事・behavior/full の最後・締めの後の 2 本・暦・frozen_sources ほか)。既定 v3 の final `5f7ae9ff24005314` |
| 腕 port の 4 構成([byte_check_j0_port_4cfg.json](byte_check_j0_port_4cfg.json)) | 同じ道具・作業木の最後の src・`SHIBUYA_DECISION_PORT=port`・`w6_v3_default`・`w6_v1_default`・`v3_mem_rel`・`v3_classical_mem_rel` を HEAD の同じ 4 構成と比べた | **4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`24375ee3dab349e8`・`73a78288ab5e1498`・`4c512a1fdc2a70c0`・テープの全部の列の sha・full の最後と締めの後を含む=J0 の行と判断の出来事はどちらのハッシュにも入らない) |
| 判断の番号列([arm_pair_j0.json](arm_pair_j0.json)) | `tools/arm_pair.py`・5,000 体・世界資産・1 日・同じプロセスで legacy → port。今の道は `LLMBridge.call`、口の道は `decide_one` の結果を包んで (刻み・体・適用したコード) を集めた | 2 構成とも番号列が一致(mock 既定 v3 65,597 呼・古典+記憶+関係 106,565 呼)・final と呼数が同じ・`mismatch` 0・`other` 0・`late` 0 |
| 試験 `test_j0_mock_equivalence.py` | 合成の世界 120 体 × 5 構成(v3・v1・v2・記憶+関係・古典+記憶+関係)で腕 on/off の final・呼数・行動の件数・テープの全部の列・判断の番号列が同じ。manifest の葉の違いは `decision_port` と日次の出来事の計器だけ(壁時計の葉と環境の節は除く)。単体で MockPort の語=mock の本文の語(v1・v2・v3・1,000 通り超)。5,000 体の 1 日(slow・世界資産) | 通った。**負の対照**: MockPort の番号を 1 つずらすと `mismatch` > 0 で final が動く(口の答えが本当に適用されている) |
| 段 B(`test_j0_writes_declared.py`) | 腕 port のランで系の前後の差 ⊆ 宣言 | 宣言の外 0。decide の宣言から `J0:decision.*` を外すと段 B が見つけ、`E:events.*` を外すと判断の出来事を書く所で出来事の記録の検査が落ちる |
| 乱数の流れ(K19・実行時) | `rng_audit.StreamRecorder` で腕 legacy/port を回す | 並べ替えの流れ `decision.present` は 0 語目を空けた鍵(k19)で重なり 0。mock の鍵の作り直し(MockPort=同じ鍵から同じ番号)の許可は**腕 port の検査だけ**に渡す(`rng_audit.K19_RECREATED_DECISION_PORT`・`recreated_for(decision_port=True)`=検収 M2)。既定の腕の表 `K19_RECREATED` には無い=既定の腕では作り直し 0 を実行時に強制(世界資産の K19 の試験 2 本に足した)。腕 port のランを既定の表で検査すると落ちる(負の対照) |

- 性能(腕 port だけ・[arm_pair_j0.json](arm_pair_j0.json)・1 本ずつ・ほかの作業木と同時): mock 既定 v3 のランの壁時計 35.6 → 48.7 秒(判断の系の時間 22.9 → 35.4 秒=+191 µs/呼)・古典+記憶+関係 75.8 → 87.9 秒(+118 µs/呼)。最初の版(候補と提示を毎回検査つきで作り直す)より候補を源と語で使い回し、提示の写しの検査を省いて縮めた(cProfile で候補 90 → 33 µs/呼・提示 113 → 46 µs/呼)。残りの大きい所は乱数の鍵の blake3(並べ替えと MockPort の引き直しで 2 回/呼)と判断の出来事の 1 行。既定の腕は変わらない(byte-check の側の壁時計は負荷が違うので比べていない)。

## 7. 試験

- 新しい試験(`tests/engine/decision/`・51 本+slow 1 本): `test_j0_port_schema.py`(14・欄と凍結・空で始める欄・予想を解釈しない×3・3 つの実装が同じ入口(AST)・提示と番号・元の id への戻し・候補の源・短い版と長い版・提示の文に数字の例が無い)・`test_j0_mock_equivalence.py`(11+slow 1・§6)・`test_j0_shuffle_invariance.py`(8・候補の順を入れ替えても mock/古典/LLM の選択が同じ中身で提示の番号は変わる・巡回の並べ替えの試験で位置が散る・鍵の材料・小さな集合の全部の並べ替え・K19 の実行時)・`test_j0_other_ratio_field.py`(4・既定は値なしと R-108 の出典・LLM の口の「その他」と自由記述・古典の「その他」・manifest の欄)・`test_j0_cause_columns.py`(8・列の幅・3 型の往復・まとめ方・保持窓の詰め直しの突き合わせ・1 呼あたり < 100 B・判断の出来事の call_id がテープの call_id)・`test_j0_writes_declared.py`(3・段 B と負の対照 2 本)・`test_j0_cli.py`(3・CLI が環境変数より強い)。4 並列で約 15 秒。
- 1-3 の既存の試験(`tests/engine/events`・90 本)は列化の後も assert を変えずに通った(凍結の表 `writes_paths_events.json` に decide を足しただけ)。
- 関わる範囲(`tests/engine/systems tests/engine/time tests/engine/events tests/engine/bridging tests/perception/facts tests/engine/test_state_ledger_10b.py tests/engine/test_env_and_sections_10f.py tests/engine/test_state_checks_10f.py tests/test_cli.py tests/engine/test_salt_seed_split_10f.py tests/engine/test_version_bump_10e.py tests/llm tests/engine/test_classical_policy.py tests/engine/test_classical_social.py tests/engine/test_llm_mock.py tests/engine/test_mock_day_w2.py`): 凍結の表を直す前 942 passed・14 failed(どれも §9 の凍結の表)→ 直した後、落ちた 14 本を含むファイルと新しい試験で 368 passed。
- 全体(`-m "not gpu and not slow" -n 4 --dist loadfile`)と slow の 5,000 体の試験: §12。

## 8. つなぎの台帳に足した行(`docs/design/bridging-ledger.json`)

| id | 外す段 | 中身 |
|---|---|---|
| `HD-engine.decision.port-1af925f4` | 6-1 | `port.py` の見出し「expedient(本モジュール分)」の項 3 個(「その他」を最後に置く・番号は 1 から・驚きの 6 語・短い版と長い版のブロックの分け方) |
| `HD-engine.decision.sources-2eb55c6e` | 6-1 | `sources.py` の見出しの項 2 個(見せ方の文=「語(源の注)」・続ける=安全弁の語/近い予定=今の意図だけ/同じ語は先の源) |
| `HD-engine.decision.layer-2d3672ba` | 1-7 | `layer.py` の見出し「expedient(周りが示すできること=1-7 の道具の台帳で外す)」の項 1 個(場所の種類と営業時間と知覚から機械的に作る仮の源) |
| `DOC-j0-candidates-vocab` | 6-1 | 候補の集合=5 つの源+語彙の残り(印 `vocab`)。この記録の §4 |

`remove_basis` はどれも `inferred`(実装役が段を当てた=親が確かめる)。

## 9. 触った共有ファイル

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/systems/table.py` | decide の `paths` の末尾に `J0:decision.* E:events.*`・`reads` に `layers.decision`・close_final の `reads` の末尾に `layers.decision` |
| `src/shibuya/engine/state_ledger.py`(状態台帳) | 行 `J0` を `P` の後に・行 `E` の `items`(`_ev_causes`・`_ev_cause_codes` を消し原因の表の列ほか 16 個を足した)と `dtype`・`note`・`OWNER_CLASSES` の末尾に `decision`・`EXCLUDED` の末尾に `decision` の 3 行・docstring の行の数(193)と版の注釈 1 行。版は上げない |
| `src/shibuya/engine/systems/boxes.py` | `OWNER_NAMES` の末尾に `decision`・`Layers.decision`(既定 None)。scratch の欄は足していない |
| `src/shibuya/cli.py` | `--decision-port` と腕を置く 3 行 |
| `src/shibuya/engine/run.py`・`manifest_sections.py` | manifest の末尾(percept の後)に `decision_port`・import 1 行・`MOTION_RNG_DOMAINS` に 1 行 |
| `src/shibuya/engine/llm_bridge.py`・`classical.py`・`llm/mock.py` | §1(既定の道の文は変えない=描画の後と方策の答えを関数に出しただけ) |
| `src/shibuya/engine/rng_audit.py` | §1 の 3 行 |
| テープの列 | 変えていない |
| 凍結の表(増えた分だけ) | `tests/engine/time/manifest_keys_frozen.json`(113 → 114 個・末尾に `decision_port`)・`tests/engine/events/writes_paths_events.json`(decide)・`tests/engine/test_env_and_sections_10f.py`(`J08_KEYS`・末尾の並び・`CONFIG_PATHS_SHA256` `4d75732b…92174dc5` → `89e426b3…df47dae50b9065`=decision_port の設定の子 7 つ)・`tests/engine/time/test_t0_tm9_fields.py`・`tests/perception/facts/test_percept_schema.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`(末尾の並び=TM9 → 1-4 → economy → percept → decision_port)・`tests/engine/test_state_ledger_10b.py`(外の状態 101 → 102・全体 192 → 193・鍵の末尾 `J0`・行 J0 の軸)・`tests/engine/test_state_checks_10f.py`(決まらない呼び手 12 → 13)・`tests/engine/bridging/test_bridging_ledger.py`(見出し 74 → 77・ファイル 71 → 74・項 337 → 343・HD 行 77) |

## 10. 限界と仮採用(10-13b §0-3=戻せる形・PENDING §1-1 の候補)

1. **候補の集合は語彙の全語のまま**(5 つの源+つなぎの印 `vocab`)。約束 (2) の同値に要る。源の決め方(続ける=安全弁の語・近い予定=今の意図・経験=想起の種類・同じ語は先の源)と見せ方の文も仮(台帳 6-1)。
2. **周りが示すできることは機械的な仮の源**(台帳 1-7)。1-7 の取り込みの後、道具の台帳から作る形に結ぶ(親の補足)。
3. 「その他」の割合の既定は**値を置かない**(R-108 §1-5・空欄 R108-1=測った原典なし)。〔決定〕の「R-108 の値」をこう読んだ(§11)。「その他」は並べ替えず最後(番号 n+1)。
4. **「候補の id を `LlmCall` の入力に」は「候補の元の出来事 id(`basis`)の和」と読んだ**。J0 では元の出来事 id を持つ候補が無い(1-6 の器の行は全部 `legacy`)=入力は全部空。〔検収 M1 の直し〕選んだ候補の源と提示の番号は `LlmCall.source`・`number`(原因の表の列 2 B/判断)で判断ごとに残す。提示した全部の候補の源は計器の集計だけ。
5. 判断の出来事は腕 port のランだけ書く(既定の腕では出来事の記録は 1 行も変わらない)。v1/v2 の語彙の語のうち出来事の語彙表に無い 3 語と「その他」は書かない(`events_unlogged`・既定 v3 では 0)。
6. 艦隊の道は J0 では口を通さない・再生の遅れて届く答えは今の道のまま(`fleet_legacy`・`late` に数える)。
7. 腕は環境変数と CLI だけ(`run_day` の引数にしない=設定の指紋と `run_kind` に入れない=1-6 の記憶の器の腕と同じ扱い)。腕の名は manifest の `decision_port.arm`(設定の節)。
8. 状態台帳の版は上げない(行 J0 は diag・discardable=どちらのハッシュにも状態のファイルにも入らない=1-3・1-6・1-9・1-2 と同じ理由)。
9. `LLMBridge.call` を前半(`begin`)と後半(`finish`)に分けられる口を足した(既定の `call` は今のまま 1 回で描く)。腕 port の描画は `Renderer.perceive` と `render_percept` を続けて呼ぶ=`Rendered.cache_hits`・`cache_misses`(1 描画の命中の数=bridge は読まない)だけが前半の分を含まない。
10. 古典の方策の `render` の中身を `answer` に移した(乱数の場所の名が `ClassicalPolicy.answer` に替わった=`SAFE_SITES` の名を直した)。**G の中はまだプロンプトの文を正規表現で読み直している**(近接行の人=計画の行 201)。ClassicalPort は G の構造の答えを写すが、G が `ctx.percept.seen_people` を読む形にするのは次の段(B5 の近接行は予算で切り詰められうる=`seen_people` と同じとは限らない=同値を測ってから)。
11. 原因の表の LLM の呼び出しは「直前と同じ」ときだけまとめる(§5)。
12. MockPort は mock の鍵の流れを作り直す(作り直しの許可は腕 port の検査だけ=検収 M2)。
13. `compose`(短い版と長い版)は器だけで、ランでは使わない。長さ 300/1,000 の腕(DM4)は 6-1。
14. **1-8 で外す予定だったつなぎの台帳の 3 行は外していない**(〔第334・親の判断〕外す段を 2-1・2-3 に付け替えた=§16): `DOC-memory-store-legacy`(器の仮の出来事)・`DOC-money-fare-cause-rail`(運賃の原因=過程 rail)・`DOC-money-uncaused-rows`(購入・食事の金の行に原因が無い)。どれも call_id を適用の口(`IntentBatch` → `resolve` → `economy.purchase_many`)まで運ぶ配線が要り、発注の「作るもの」の外。腕 port の判断の出来事(call_id つき)はできたので、次の段で結べる。
15. 成長の宣言は腕 port のときだけ判断の出来事の行を足す形にした(§5・検収 L2)。ランの成長の報告(`check_growth`)にはまだ載せていない(1-3 の宣言と同じ)。
16. **性能の予算の宣言と回帰の試験は無い**: 腕 port は判断 1 呼あたり +118〜191 µs(§6・mock 既定 v3 のランの壁時計 35.6 → 48.7 秒)。腕を既定にする段の前に予算(予算宣言の設計書=親)を宣言する。乱数の鍵の blake3 を用途名ごとに覚えれば(`core.rng.derive_key` の結果のキャッシュ=純関数)縮む見込み(共有の core を触るので親の判断)。
17. 不応期を外した腕の計測(口の約束の〔第333 追加〕)は計画の 2-0b(この段ではやっていない)。

## 11. 親に確かめてほしいこと

1. 「その他」の割合の既定(〔決定〕=R-108 の値)を「値を置かない(R108-1=原典なし)」と読んだこと(§10 の 3)。
2. 「候補の id を `LlmCall` の入力に」を「候補の元の出来事 id」と読んだこと(§10 の 4)。〔親の判断=検収 M1〕選んだ源と提示の番号を原因の列に足した(§13)。
3. 1-8 で外す予定だった台帳の 3 行(§10 の 14)を 1-8 の続きでやるか、外す段を付け替えるか。
4. 候補の集合が語彙のままであること(mock の選んだ源の 57% が `vocab`)を、6-1 まで残してよいか。
5. 腕 port の判断の出来事の成長(§5)は宣言に入れた(検収 L2)。ランの成長の報告に載せる段と、性能の予算(§10 の 16)の宣言は親。
6. 並べて進んでいるほかの段(1-5・1-7・1-8b)と取り込みの順で当たる所: 状態台帳の行の数と並び(J0 を P の後)・持ち主の名の末尾・manifest の末尾(`decision_port` を percept の後)・`CONFIG_PATHS_SHA256`・つなぎの台帳の見出しの数(77)と項(343)・decide の宣言。

## 12. 全体の試験

- 全体(`-m "not gpu and not slow" -n 4 --dist loadfile`・作業木): **4,446 passed・1 failed・1 xfailed**(17 分 58 秒・ほかの作業木と同時)。落ちた 1 本は junction 由来の既知の `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`。
- その後に口の側だけを片付けた(使っていない関数 1 つと import の置き場=腕 port の道だけ・既定の道と見出しの文は同じ)。片付けの後: `tests/engine/decision tests/engine/bridging tests/engine/time tests/engine/test_state_ledger_10b.py` で 219 passed(4 分 7 秒)・`lint-imports` 5 kept。
- slow: `test_5000_agents_one_day_same_decision_sequence`(5,000 体・世界資産・語彙 v3・腕 on/off で判断の番号列と final と呼数が同じ)1 passed(95 秒)。

**独立検収の直しの後(§13)**:

- 試験: `tests/engine/decision tests/engine/events tests/engine/systems tests/engine/time tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/test_cli.py tests/engine/bridging`(`-m "not gpu and not slow" -n 4 --dist loadfile`)=**501 passed**(9 分 18 秒)。slow の 2 本(`test_k19_runtime_default_v3_5000_known_counts`=既定の腕で `llm.mock` の作り直し 0 を足した・`test_5000_agents_one_day_same_decision_sequence`)=2 passed(3 分 2 秒)。`lint-imports` 5 kept。新しい試験は 58 本+slow 1 本(`test_j0_cause_columns.py` が 8 → 15)。
- byte-check 4 構成([byte_check_j0_review_fix_4cfg.json](byte_check_j0_review_fix_4cfg.json)・`w6_v3_default`・`w6_v1_default`・`v3_mem_rel`・`v3_classical_mem_rel`・本体 HEAD `f60b0a6` の src の写しと作業木の src・腕は既定 legacy): **4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`24375ee3dab349e8`・`73a78288ab5e1498`・`4c512a1fdc2a70c0`)。
- 原因の表の 1 呼あたりのバイトは測り直した([cause_bytes_j0.json](cause_bytes_j0.json)=64 / 103 / 221 B・§5)。

## 13. 独立検収(review.md)の指摘と直し(親の判断・第334)

| # | 直したこと | 確かめ |
|---|---|---|
| M1 | 原因の表の列に「選んだ候補の源」`_cz_src`(i1・`CANDIDATE_SOURCES`=5 つの源+`vocab` の番号)と「提示の番号」`_cz_num`(i1・1〜127)を足した(39 B/行=+2 B/判断)。`LlmCall` に欄 `source`・`number`(既定 None=口を通らない呼び出しは今のまま)を足し、読み口 `event(i).cause` が組み立てて返す。腕 port の判断の出来事は `LlmCall(call_id, basis, source=選んだ源, number=提示の番号)`。源の並びは `engine.events.log.CANDIDATE_SOURCES` と `engine.decision.port.ALL_SOURCES` が同じ(口の層の組み立てで検査・試験) | `test_decision_events_carry_the_source_and_the_number`(腕 port の出来事を読むと判断ごとに源と番号が取れ、分布が口の計器 `chosen_by_source`・`chosen_number` と同じ)・`test_llm_call_source_and_number_are_checked`(表の外の源・番号 0/128/真偽値/小数は `ValueError`)・3 型の往復の試験に源と番号つきの行を 1 つ。1-3 の既存の試験は assert を変えずに通った |
| M2 | `K19_RECREATED` から `llm.mock` を外し、腕 port の検査だけに渡す表 `K19_RECREATED_DECISION_PORT`(`MappingProxyType`)と `recreated_for(decision_port=…)` を足した | `tests/engine/test_state_checks_10f.py` の世界資産の K19 の試験 2 本(300 体 2 日・5,000 体 1 日=slow)に「既定の腕で `llm.mock` の作り直し 0」を足した。`test_k19_runtime_audit_on_the_port_arm`: 既定の腕は作り直し 0・腕 port は口の分の許可で合格・腕 port を既定の表だけで検査すると `llm.mock` の 1 件で落ちる |
| L1 | `log.py` の `_PROC_CODE` を `MappingProxyType` に(源の表 `_SRC_CODE` も) | — |
| L2 | 成長の宣言に腕 port の判断の出来事を足した(§5)。性能の予算の数は限界に書いた(§10 の 16) | `test_growth_declaration_adds_the_decision_events_only_on_the_port_arm`(腕 legacy の宣言は今のまま・腕 port は 1 判断 72+39 B・口の層の `event_growth`) |
| L4 | `LLMBridge._after_render` の刻みの引数を `tick` → `step`(T0 の規則・呼び手は位置で渡す=値は同じ)。`MockLLM.action_draw`・`decision/ports.py` の docstring の「tick」を「刻み」に | `tests/engine/time`(tick の語の検査) |
| H1(rebase 後) | **rebase の後に直した(§16)**。直す前の記録: 本体(1-5 取り込み済み)では `Process` の検査が `V.CAUSE_PROCESS_NAMES`(`PROCESS_NAMES`+`"rights"`)に広がった。`log.py` の `_PROC_CODE`(過程の名 → 番号)と `_cause_at`(`V.PROCESS_NAMES[ref]`)は `PROCESS_NAMES` から作るので、併合の後に `Process("rights")` を書くと `KeyError`(テキストの併合は衝突しない=見落としやすい)。rebase の後に両方を `Process.__post_init__` の検査と同じ 1 つの定数(`V.CAUSE_PROCESS_NAMES`)から作る形に直し、`tests/engine/rights` と `tests/engine/decision/test_j0_cause_columns.py` を回す | — |

直しの後の確かめ: §12 の後ろ(直しの後の試験と byte-check)。

## 14. 再現の手順(リポの根で・`$D`=このフォルダ・`$W`=作業用の短いディレクトリ)

    git archive f60b0a6 src docs/bench/anchors docs/design/v2-budget-declaration.md \
        docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
    mkdir -p $W/head_src/data/calendar && cp data/calendar/syukujitsu.csv $W/head_src/data/calendar/
    B=docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py
    python $B side --src $W/head_src/src --label head --scratch $W --out $W/head.json
    python $B side --src src --label j0 --scratch $W --out $W/j0.json
    python $B compare --a $W/head.json --b $W/j0.json --out $D/byte_check_j0.json
    # 腕 port の 4 構成(HEAD の側は head.json から同じ 4 構成を抜いた head4.json)
    SHIBUYA_DECISION_PORT=port python $B side --src src --label j0port \
        --only w6_v3_default,w6_v1_default,v3_mem_rel,v3_classical_mem_rel --scratch $W --out $W/j0port.json
    python $B compare --a $W/head4.json --b $W/j0port.json --out $D/byte_check_j0_port_4cfg.json
    # 判断の番号列と計器と壁時計(5,000 体・2 構成)
    PYTHONPATH=src python $D/tools/arm_pair.py $D/arm_pair_j0.json w6_v3_default v3_classical_mem_rel
    # 原因の表の 1 呼あたりのバイト(HEAD と作業木)
    PYTHONPATH=$W/head_src/src python $D/tools/cause_bytes.py head $W/cause_bytes_head.json
    PYTHONPATH=src python $D/tools/cause_bytes.py j0 $W/cause_bytes_j0.json

## 15. 親の検収(第334・2026-10-14)

- 親の byte-check 4 構成(本体 HEAD ccaf2c1 の src=1-5 取り込み済み vs 作業木の src・--src 指定・既定 legacy): final が同じ 4/4・動いた欄 0(parent_head_vs_j0_4cfg.json)。
- 親の答え: 「その他」の既定は None(R-108 に原典なし=仮採用)・候補の id は候補の元の出来事 id(仮採用)・外す段 1-8 の台帳 3 行(記憶の legacy・運賃の原因・原因の無い金の行)は call_id を IntentBatch → resolve → economy へ運ぶ配線が要るので外す段を付け替える(金の 2 行は 2-1・記憶の legacy は 2-3=取り込み後に親が台帳を直す)・腕 port の出来事の量(39 万体 7 日で約 3.9 GB)は port を既定にする段(6-1)で成長の宣言に・G の中の正規表現の読み直しは 6-1 の限界。独立検収(review.md)=条件つき受入 → M1(原因の列に選んだ源 _cz_src と提示の番号 _cz_num=2 B/判断・LlmCall に source/number)と M2(K19_RECREATED から llm.mock を外し腕 port の検査だけに=既定の腕で作り直し 0 を世界資産の試験 2 本で強制)と低 L1・L2・L4 を実装役が直した(§13)。H1(過程の名の表=本体の 1-5 の CAUSE_PROCESS_NAMES と併せる)は rebase 後。直しの後の試験 501 passed・byte-check 4 構成 同じ(実装役・土台 f60b0a6)。

## 16. 本体(1-5 取り込み済み・`ccaf2c1`)への rebase の衝突の解き方・H1・台帳の付け替え(第334)

衝突は 9 本。どれも**両方の追加を残した**(git の操作=`git add`・`rebase --continue`・commit は親)。

| ファイル | 解き方 |
|---|---|
| `docs/design/bridging-ledger.json` | 3 方向(土台・本体・1-8)の行の id で突き合わせ、本体の 282 行(1-5 の 5 行と opening の見出しの行の書き換えを含む)を全部残し、1-8 の 4 行(`HD-engine.decision.*` 3 行・`DOC-j0-candidates-vocab`)を末尾に足した=286 行。1-8 は既存の行を書き換えていない |
| `src/shibuya/engine/run.py` | manifest の末尾を `… → percept → rights(1-5)→ decision_port(1-8)` に(注の並びも) |
| `src/shibuya/engine/state_ledger.py` | 行 E の注: 書く系に 1-5 の「役割語は出来事を書かない」と 1-8 の decide(腕 port の判断の出来事)を両方。行 E の items(原因の表の列)・行 J0・持ち主 `decision`・除外は自動で合わさった(1-5 は行を足さず除外 3 か所だけ) |
| `tests/engine/bridging/test_bridging_ledger.py` | 見出し 76 → **79**・見出しのファイル 73 → **76**・項 342 → **348**・`HD-` 行 76 → **79**(本体の値に 1-8 の 3 見出し・項 3+2+1) |
| `tests/engine/bridging/test_manifest_rules_bridges.py` | 末尾の 4 つ=`economy`・`percept`・`rights`・`decision_port`・1-4 の 3 欄は末尾の 4 つ前まで |
| `tests/engine/test_env_and_sections_10f.py` | `R15_KEYS`(1-5)と `J08_KEYS`(1-8)を両方・末尾の並び `… + P12 + R15 + J08`。`CONFIG_PATHS_SHA256` は解いた後に試験で計算し直して `89e426b3…df47dae50b9065` のまま(1-5 の `rights` は観測の節=設定の道筋は変わらない) |
| `tests/engine/time/manifest_keys_frozen.json` | 鍵 114 → **115**(末尾 `rights` → `decision_port`)・注は本体の文に 1-8 の文をつないだ |
| `tests/engine/time/test_t0_tm9_fields.py` | TM9 の後ろ=`rules_version`・`run_kind`・`bridges_version`・`economy`・`percept`・`rights`・`decision_port` |
| `tests/perception/facts/test_percept_schema.py` | 末尾の 4 つ=`economy`・`percept`・`rights`・`decision_port` |

**合わせ(衝突の印の無い所)**:

1. `tests/engine/rights/test_rights_manifest.py` の `keys[-1] == "rights"` を `keys[-2:] == ["rights", "decision_port"]` に(1-5 の末尾の確かめ・試験の名は履歴のまま)。
2. **併合で入った 1-5 の行の引数名**: 1-5 が `LLMBridge.call` の本体に足した役割語の権利の確かめ `self.role_rights(int(agent_id), int(tick), …)` は、テキストの併合で 1-8 の `_after_render`(検収 L4 で刻みの引数を `step` にした)の中に入り、`tick` が未定義になっていた(役割語の答えが権利の口に届いたときに `NameError`)。`int(step)` に直した(`_after_render` の中に `int(tick)` は無い)。`tests/engine/rights` は 125 passed。

**H1(検収・高)**: `engine/events/log.py` の過程の名の番号の表 `_PROC_CODE` と読み口 `_cause_at` を、`Process.__post_init__` の検査と同じ 1 つの定数 `V.CAUSE_PROCESS_NAMES`(世界過程+区切り+1-5 の検査の名 `rights`)から作る形にした(前は `V.PROCESS_NAMES`=`Process("rights")` を書くと `KeyError`)。試験 `test_check_process_names_round_trip`(表の全部の名で書いて読み返す)を足した。`tests/engine/rights/test_rights_events.py`+`tests/engine/decision/test_j0_cause_columns.py`=32 passed。

**台帳の付け替え(親の判断)**: 外す段 1-8 の 3 行の `remove_at` を改め、`why` に理由を 1 行足した(`remove_basis` は `inferred` のまま)。外す段 1-8 の行は 0。

| id | 外す段 | 理由(`why` に足した文の要旨) |
|---|---|---|
| `DOC-money-fare-cause-rail` | 1-8 → **2-1** | 乗車の呼の call_id を適用の口(IntentBatch → resolve → economy)へ運ぶ配線は経済の段 2-1 で(1-8 J0 は腕 port の判断の出来事に call_id を付けたところまで) |
| `DOC-money-uncaused-rows` | 1-8 → **2-1** | 購入と食事の呼の call_id を IntentBatch → resolve → `economy.purchase_many` へ運ぶ配線は 2-1 で |
| `DOC-memory-store-legacy` | 1-8 → **2-3** | 記憶の器の目印を実の出来事に替えるのは、複数日の mock で確かめる段 2-3 で |

**試験**(解いた後・作業木): `tests/engine/decision tests/engine/events tests/engine/rights tests/engine/systems tests/engine/time tests/engine/bridging tests/engine/memory tests/perception tests/economy tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/test_cli.py`(`-m "not gpu and not slow" -n 4 --dist loadfile`)=**1,247 passed・1 failed**(9 分 52 秒)。落ちた 1 本は上の合わせ 1(`test_rights_is_the_last_key_and_observed`=1-5 の末尾の確かめ)で、直した後に `tests/engine/rights` を回して 125 passed。byte-check は親が回す。
