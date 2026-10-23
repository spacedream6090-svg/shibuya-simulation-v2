# run_day の分解の口の案(第 1 期 1-0・紙の設計・草案)

> **〔実装済(第331・#89)〕** ユーザー承認(2026-10-13・[回答 10-13](v2-answers-2026-10-13.md) の 1)の後に実装した。実装と草案の違い(段の順 A → CB → DEF・`Fixtures` の箱・`close_final` を別の系・改名 7 か所・指紋は新しい道具 `probe.py`・世界過程 18 本は `world` の 1 つの系の中)と限界の表は [impl-1-0.md](../bench/analysis/wallbounce-1012/run-day-decomp/impl-1-0.md) §5-2・§7-3。行番号は起草時の HEAD `0389689` のもの。

- 第330・調査役 Opus 5.5 起草。別の検収役の判定は「条件つき受入」([検収の記録](../bench/analysis/wallbounce-1012/run-day-decomp/review-decomposition-draft.md))。本版はその条件と親の決定で直した版。**再検収(2 回目)=受入**([記録](../bench/analysis/wallbounce-1012/run-day-decomp/review-decomposition-draft-round2.md)・正 7 本と負の対照 10 本を検収役が再現)・親が §0〜§3 を読んで受入(第330)。**切るのはユーザーへの報告(§0-1 の問い 1 件)の後**([回答 10-12b](v2-answers-2026-10-12b.md) §6-1・§6-7)。
- 指示の正: [回答 10-12b](v2-answers-2026-10-12b.md) §6(6-1〜6-7)。計画: [実装の計画 2026-10-12](v2-implementation-plan-2026-10-12.md) §1・第 1 期。
- 行番号はすべて HEAD `0389689` の `engine/run.py`(`src/shibuya/` は省く)。数は実測。測った道具と生の記録は [run-day-decomp/](../bench/analysis/wallbounce-1012/run-day-decomp/)(§5)。
- 印: 「推測」=確かめていない読み。「未リサーチ(expedient)」=先例や答申に根拠の無い自前の構成。

〔改訂(第330・検収の後)〕直した箇所の一覧(番号は検収の記録の番号):

| 番号 | 直したこと | 場所 |
|---|---|---|
| R1 | `focus_request` を毎 tick 空にする `TickScratch` から外し、使い回すバッファの箱 `Buffers` に置いた(tick の頭で空にしない) | §2-3・§3-3 の 17 |
| K1 | 段 A を numpy の旗だけに頼らない形にした(resolve の口の中で書く配列ごとに旗を見る+静的な閉包+試験のときの SoA の差の検査)。ufunc.at の列の負の対照を試作に足し、落ちることを確かめた | §2-6 |
| K2・K3 | 旗の直書き 3 か所・ビュー・局所の別名の抜け道を、どの段が捕まえるかの表を足した | §2-6 |
| K4 | 宣言の正を静的な閉包にし、動的な観測は漏れの検査に回した。見えない 55 行の扱いを書いた | §2-5・§2-6・§1-5 |
| K5 | 指紋を「系ごとの全欄の差」にした。測りの境目を系に合わせた。RunStats と呼数は試験のときだけ指紋に入れる | §2-7・§5 |
| K6 | 読む欄の検査は 1-0 では静的な読み(箱の属性の参照)の AST だけ・実行時の読みは見ないと明記 | §2-5・§2-6 |
| K7 | drain と最後の締めも系として同じ検査を通す(試作で確かめた) | §2-4・§2-6 |
| K8 | `talk_stats` を箱(RunStats)に入れた・局所を箱へ割り当てる表で漏れを 0 にする約束 | §2-3 |
| K9 | 外の状態の検査は道筋(`鍵:道筋`)の単位(行は割らない)=親の判断へ移した | §0-2・§2-6 |
| 記録の誤り 1 | 静的な書き手の無い列は 4(`hunger_stage` は誤り) | §1-6 |
| 記録の誤り 2 | `_relay_tables` の nonlocal は 5(`w17_substituted` は `append` で中身を変えるだけ) | §1-3 |
| 記録の誤り 3 | 無名関数は 3(3074・3143・3193)。3065 は工場関数の戻り値・3184・3155・3169 は入れ子の def | §1-3・§3-3 の 6 |
| 記録の誤り 4 | 描画は想起で SoA を書かない(想起は読むだけ・書くのは計数)。L14 の記憶の書きは `_utter` → `note_utterance` → `write_memory` | §1-2・§1-3・§2-2・§3-3 の 6 |
| 記録の誤り 5 | 「書き手は resolve.py だけ」に `economy/ledger.py:_apply_cash` の例外(別名で `agents.money` を `np.add.at`)と resolve の局所の別名 2 か所を併記 | §0・§1-6 |
| 記録の誤り 6・7 | 「numpy が ValueError を投げる」「区間=系なので」を直した | §2-6・§2-7 |
| 記録の誤り 8 | §2-8 の見出しを「土台(1-1〜1-9 の 9 段)」に | §2-8 |
| 記録の誤り 9 | `guard_results.jsonl` に v3 既定 1 日の行を入れた(作り直し) | §5 |
| 記録の誤り 10 | flecs の phase に OnStart・MATSim の listener の呼び名と `doSimStep` の継承 | §4 |
| 試験の欠け T1〜T5 | §3-1 の門に足した | §3-1 |
| §6 の言い換え | ユーザーへの問いを 1 件にまとめ、残りを親の判断へ | §0-1・§0-2 |
| 〔親の注・再検収の残る小さな点〕 | (1) 手で書く別名の表 `alias_writes.json` に `_board_riders`(運賃: `rail.pay_fares` → `_apply_cash`)と `initialize`(`endow_households`)の台帳を通した `agents.money` の書きが載っていない(どちらも money を直接書く関数なので今の許可は変わらない=1-0 の実装で表に足す)。(2) §0 の「8 本の正のラン」は正しくは「正 7 本+書きの起きない負の対照 1 本」。(3) 閉包は上限なので許可は観測より広い(world は閉包 23 列・観測 12 列)=「宣言の外」は「閉包の外」の意味 | §0・§2-6 |

## 0. 要約

- `run_day` は 3,052 行(1928〜4979。うち署名と説明 483 行)。引数 115・局所の名前 449・入れ子の関数 21(直下 17+内側 4)。tick のループは 3631〜4531 の 901 行。
- 書き口はほぼ 1 本にまとまっている。SoA の列の静的な書き手は、確保と初期値(`agents/state.py`・`world/state.py`)を除けば `engine/resolve.py` の関数 63 本で(列名 91 のうち 87 に書き手)、SoA は `freeze()` で読み取り専用にして `with agents.writable():` の中だけで解く仕組みが既にある。例外は 3 つある。`economy/ledger.py:_apply_cash` は世帯の現金として採用した `agents.money` を別名で `np.add.at` する(resolve の窓の中から呼ばれる)。resolve の中にも局所の別名で書く所が 2 つある(`set_refractory` の `cur`・`consume` の `holdings`)。`np.<ufunc>.at` は numpy の書き込みの旗を見ない(numpy 2.5.3)。resolve の口 49 種を 17 ファイルが呼ぶ。分解は「書く場所を作る」作業ではなく、「誰がいつ resolve を呼んでよいか」を宣言して縛る作業になる。
- 案: tick の中の系 25・日の境目の系 2・ランの単位 3(組み立て・吸い切り・結果)。系の境目は今の実行順の区間(§2-2)。移動・知覚・判断・会話・お金・鉄道の話題は、系の上の「群」の名札にする(§0-1 のユーザーの判断)。
- 口は宣言の表 1 本(`SystemSpec`)。書く SoA の列は、系が呼んでよい resolve の口の静的な書き集合の閉包から機械で作る(宣言の正)。動的な観測は閉包の漏れの検査に使う。欄の名は状態台帳の鍵(`agents.cell`・`O39:conv.sessions`)と同じ語彙にする。
- 「宣言の外を書いたら落ちる」は 3 つを合わせて保証する。(A) resolve の口の中で書く配列ごとに書き込みの旗を見る(`ufunc.at` も含む)+解除を系の書く列だけにする、(D) 静的な閉包と抜け道の禁止の AST、(B) 試験のときに系の前後の全欄(SoA と外の状態の道筋)の digest で宣言の外の変化を落とす。試作では正のラン 7 本(と書きの起きない負の対照 1 本)が final 不変で通り、負の対照 10 本(ufunc.at の 3 列と最後の締めを含む)がどれも書いた行で落ちた(§2-6)。
- 危ない所は 22 か所(§3-3)。いちばん重いのは、ハッシュに台帳の道筋の文字列(`run_day.pending` など)とクラスの置き場(module.qualname)が入ること。持ち主の名・道筋・値のクラスの置き場を 1-0 で変えると、挙動が同じでも final が動く。

### 0-1. ユーザーに確かめてほしい点(1 件)

系の切り方について 1 点だけ確かめたい。ご指示では系の例として「移動・知覚・判断・会話・お金・鉄道」を挙げていただいた。1-0 では、これを系そのものにせず、今の処理の順のまま 25 の系に切り、話題は系に付ける名札にしたい。理由は、同じ欄(たとえば「何をしているか」の欄 `activity`)を 7 か所が順に書いていて、話題ごとにまとめ直すと順が変わり、結果が変わってしまうため。このため「移動」と「お金」は、行為の解決(Phase C=`resolve.apply`)という 1 つの系の中に残る。話題ごとのまとめ直しは、事象の待ち行列(T1)の後の版上げで、結果が変わることを前提に行う。この進め方でよいか(ユーザーの例示からの手段の変更=CLAUDE.md §2-6)。

あわせて伝えること(問いではない): 「宣言の外を書いたら落ちる」の強さは 2 段になる。SoA(個体・セル・店の列)は実行のたびに書いた行で止まる。外の状態(層の中の表)は試験のときに系の前後を比べて落とすので、試験の人数と時刻の範囲でしか見えない。

### 0-2. 親の判断に任せる点(親の決めを含む)

- 〔親の決め〕書きの検査(段 A)は既定で入れ、切替口で外せる形にする。重さは版の予算表に載せる(試作の重さは §2-6・本実装は未計測)。
- 〔親の決め〕外の状態の検査は道筋(`鍵:道筋`。`state_hashes.item_digest(owners, key, path)` が道筋ごとに取れる)の単位にし、台帳の行は割らない(割るとハッシュの札が変わり final が動く)。
- 〔親の決め〕世界過程が持ち主をまたいで書く所(鉄道と大きな催しが計画実行層の O36・O37・O70 と鉄道の O74 を書く=§1-7)は、1-0 では宣言で認める。口を通す形に直すのは第 3 期以降(直す段で「過程が他の層の状態を書いてよいか」をユーザーに聞く)。
- 〔親の決め〕K1 の直し(resolve の口の中で配列ごとに旗を見る)は 1-0 の設計の中に入れる(§2-6・§3-2 の段 A)。
- 〔親の決め〕宣言の正は静的な閉包。動的な観測は漏れの検査(§2-5)。
- 〔親の決め〕系ごとの指紋は全欄の差。RunStats と呼数は試験のときだけ指紋に入れる(§2-7)。
- 〔親の決め〕読む欄の検査は 1-0 では静的な読み(箱の属性の参照)の AST だけ。実行時の読みは見ない(§2-5)。
- Phase C を 1 つの系のまま置く(§0-1 の説明に含めた)。
- 置き場とファイル名(案 `engine/systems/`)・宣言を表にするかデコレータで表に登録するか(案は表)・`run_day` の署名を残す包み方。
- 切る順の中の細かな順(§3-2 の段の中)・各段の commit の切り方。
- 試験が `shibuya.engine.run` の名前を差し替えている 20 か所(§3-3 の 15)の付け替え方。
- 閉包の表(系 → 呼んでよい resolve の口)を誰がどう書くか(案: 道具で下書き=`build_allow.py`・手で直す)。
- 系ごとの指紋の道具を `checkpoint_detail` と first_diff の延長にするか、新しく作るか。
- 土台が足す状態(出来事のログ・規則の表・権利台帳・道具の台帳)の状態台帳の軸を、足す前に決める(§2-8 の注)。

## 1. 今の構造の地図(HEAD `0389689`)

### 1-1. 大きさ(AST で数えた)

| 項目 | 値 |
|---|---|
| `run_day` の行 | 1928〜4979(3,052 行)。署名と説明 1928〜2410(483 行)・本体 2411〜4979(2,569 行) |
| 引数 | 115 |
| 局所の名前 | 449(内包表記の変数を含む) |
| 入れ子の関数 | 直下 17(`_onoff`・`_utter`・`_receive_arrivals`・`_hash_owners`・`_pst_now`・`_act_hash_now`・`_eod_hashes`・`_money_now`・`_bodies_now`・`_w17_weekday`・`_relay_tables`・`_start_day`・`_ledger_close`・`_day_record`・`_close_day_midrun`・`_save_state`・`_rebuild_derived`)+ if の中とループの中に 4(`_classical_acq`・`_classical_partner`・`_session_partners`・`_revert`)=21 |
| tick のループ | 3631〜4531(901 行)。ループ本体の最上位の文 112 |
| ループの中の名前 | ループの外で作り中身を変える 24・前の tick の束縛を読む 3(`pending`・`prev_sessions`・`prev_tape_misses`)・積算 11・tick の中だけ 148・読むだけ 82(〔改訂(第330・K8)〕「読むだけ」には引数やメソッド越しに中身が変わる物が入る。例 `talk_stats` は `intents_from_responses(stats=talk_stats)` で書かれる。層の物も同じ) |
| ループの中で書く `result` の欄 | 23(`llm_calls`・`fares_paid`・`n_boarded` など) |

### 1-2. 区間の表(系の境目の材料)

区間は「ループ本体の最上位の文」で切った。書く状態は §1-5 の動的な測り(6 構成)。「resolve」はその区間で実際に呼ばれた resolve の口(6 構成の和)。

| 区間 | 行 | 行数 | 中身 | 書く状態(SoA の列・外の状態の行) | resolve | LLM |
|---|---|---|---|---|---|---|
| S0〜S8 | 2411〜3630 | 1,220 | 指紋・暦・再開の見出し・腕の検査・SoA の確保・初期化・層の組み立て・入れ子の関数・再開の復元 | 全部(組み立て) | initialize ほか | — |
| L0 | 3632〜3635 | 4 | 日の頭(`_relay_tables`・`_start_day`) | plan_activity・O37・O38・O50・O55・計画境界の表 b_* | set_plan_state | 無 |
| L1 | 3636〜3651 | 16 | 体の時間・範囲外の食事 | hunger・fatigue・energy_balance・since_meal_kcal・O28 | advance_body ほか | 無 |
| L2 | 3652〜3657 | 6 | 世界過程 18 本 `runner.step` | 12 列(activity・cell・transit_state・thermal・pois.open_now ほか)・22 行 | 13 種 | 無 |
| L3 | 3658〜3670 | 13 | 計画実行層 `presence.step` | 12 列・O36・O70 | rail_arrive ほか | 無 |
| L4 | 3671〜3691 | 21 | 知覚の前計算 `prepare_tick` | (台帳の行は動かず=描画のキャッシュは除外の一覧) | — | 無 |
| L5 | 3692〜3695 | 4 | 艦隊/再生の到着の受け取り(遅れ 1) | O43・O44・O96(mock では空) | — | 受 |
| L6 | 3696〜3812 | 117 | ① 応答の反映・招待の解決・`intents_from_responses`・焦点 | activity・talk_partner・会話 O39/O41/O91・意図 O5/O6・O13・O19・O25・O26・O34・O43・talk_stats | set_conversing ほか | 無 |
| L7 | 3813〜3840 | 28 | ② 変化検出・活動/意図の抑止・満了入口 | 段の 3 列・cells.b4_hash・O45・O6・O66 | apply_detection | 無 |
| L8 | 3841〜3886 | 46 | 計画境界の起床と就寝 | activity・board_line・plan_activity・sleep_pending・target_node・O70 | begin_planned_sleep ほか | 無 |
| L9 | 3887〜3894 | 8 | 自宅の食事 | (腕 on のときだけ) | energy_home_meal | 無 |
| L10 | 3895〜3911 | 17 | 会話ターン・顕著行為の起床候補 | (読むだけ) | — | 無 |
| L11 | 3912〜3938 | 27 | 到着(遅れ 2)・艦隊の再投入 | refractory_until(再投入のとき)・O44 | clear_refractory | 受 |
| L12 | 3939〜4005 | 67 | 抑止の例外・歩く退出・同席と知人出現・候補の組み立て | rel_* 6 列・O16・O18・O19 | write_relations | 無 |
| L13 | 4006〜4026 | 21 | ③ アービタ・起床率 | O42・O71 | — | 無 |
| L14 | 4027〜4154 | 128 | ④ 呼(mock・再生・艦隊)と会話ターンの発話 | refractory_until・mem_* 9 列(〔改訂(第330)〕会話ターンの発話 `_utter` → `note_utterance` → `write_memory`。描画の想起は SoA を書かない)・会話 O39/O41・O43・O8/O9/O11・O15・O17・O19・方策 O20/O22/O23/O69・描画 O63/O64/O84・O86 | set_refractory・write_memory | 発 |
| L15 | 4155〜4183 | 29 | ⑤ Phase A | O5・O6・O66 | intent_kept_by | 無 |
| L16 | 4184〜4190 | 7 | ⑥ Phase B | (読むだけ) | — | 無 |
| L17 | 4191〜4249 | 59 | ⑦ Phase C(`resolve.apply`)と結果の積算 | 36 列(移動・購入・食事・乗車・お金・在庫)・O28・O50・金と物の台帳 9 行 | apply ほか 29 種 | 無 |
| L18 | 4250〜4383 | 134 | 会話セッション | activity・talk_partner・O19・O39・O41 | revert_conversation ほか | 無 |
| L19 | 4384〜4394 | 11 | 活動層・意図の後処理 | activity_kind・activity_until・intent_* 4 列・O1・O2・O4・O5・O6・O66 | set_activity ほか | 無 |
| L20 | 4395〜4428 | 34 | 記憶・親しみ・エネルギーの tick の後 | mem_* 9・rel_* 6・sm_* 7・O9〜O12・O19・O28・O64・O68 | write_memory ほか | 無 |
| L21 | 4429〜4460 | 32 | 診断の行 | (診断の積算だけ) | — | 無 |
| L22 | 4461〜4477 | 17 | 在圏の標本・規範の計器・在圏 journal | O34・O70 | — | 無 |
| L23 | 4478〜4526 | 49 | checkpoint | (読むだけ) | — | 無 |
| L24 | 4527〜4532 | 6 | 途中の日の締めと状態の保存 | 金と物の台帳 7 行 | — | 無 |
| E0〜E4 | 4533〜4979 | 447 | 吸い切り・最後の締め・結果の組み立て・成長の検査・書き出し | E1: activity・transit_*・10 行 | — | 吸 |

### 1-3. 入れ子の関数(自由変数=クロージャで捕まえているもの)

| 関数 | 行 | 読む自由変数 | 書き換える自由変数 |
|---|---|---|---|
| `_utter` | 3198〜3223 | agents・conv・mem_layer・wom_ex・store_wom_on・vocab_version | (中で conv・記憶の SoA・口コミを書く) |
| `_receive_arrivals` | 3298〜3360 | _utter・conv・fleet_bridge・fleet_wait_s・tick_seconds | pending・fleet_deferred・fleet_waiting・fleet_inflight・replay_inbox・phase |
| `_hash_owners` | 3363〜3374 | 層と持ち主 21 個(台帳の `items` の根の鍵)・pending・fleet_deferred・fleet_waiting・replay_inbox | — |
| `_relay_tables` | 3433〜3470 | calendar・weekly・schedule・runner・presence・act_layer・classical_policy・poi_resolver・ticks・tpd | **nonlocal** 5 つ(b_agent・b_cond・b_tick・b_cell・b_start)。〔改訂(第330)〕`w17_substituted` は束縛し直さず `append` で中身を変えるだけ(3445) |
| `_start_day`・`_day_record` | 3472・3516 | presence・tpd・ledger・result | day_heads・daily_records |
| `_ledger_close`・`_close_day_midrun` | 3482・3528 | calendar・ledger・census_out・sim_days・runner・checkpoint_every | result の 7 欄 |
| `_save_state` | 3542〜3578 | agents・world・schedule・_fp・_env_fields・run_id・parent_run・pending・fleet_inflight | state_files |
| `_eod_hashes`・`_act_hash_now`・`_pst_now`・`_money_now`・`_bodies_now`・`_w17_weekday`・`_rebuild_derived`・`_onoff` | — | 読むだけ | — |
| `_classical_acq`・`_classical_partner`・`_session_partners` | 3145・3160・3180 | rel_layer・agents・conv(描画と方策に差し込む) | — |
| `_revert` | 4260〜4268 | conv | reverted |

〔改訂(第330・記録の誤り 3・4)〕組み立ての中で描画と方策へ差し込む関数は 7 つ。無名関数(lambda)は 3 つ(3074 天候の日・3143 知人・3193 想起)。ほかは 3065 の工場関数 `_named_closed_lookup(...)` の戻り値(閉店の補足)・3184 の入れ子の def `_session_partners`(会話の参加者)・3155・3169 の入れ子の def を `classical_policy.acq_fn`・`partner_fn` に代入したもの。描画(④ の中)はこれを通して記憶・関係・会話を読む。想起(`MemoryLayer.recall`・memory.py:326〜)は SoA を読むだけで、書くのは想起の計数(外の状態)。

### 1-4. tick をまたいで共有される変数

- 前の tick の束縛を読む 3 つ: `pending`(3702 で束縛し直す。`_receive_arrivals` と `_hash_owners` は遅れて名前を引くので新しいリストを見る)・`prev_sessions`・`prev_tape_misses`(4454〜4455 で束縛し直し、再開では 3615〜3616 で置く)。
- ループの外で作り中身を変える 24: conv・rel_layer・result・phase・layer_counts・sleep_counts・diag_rows・fleet_deferred・fleet_waiting・fleet_inflight・replay_inbox・focus_request・awake_sum・awake_ticks・leave_counts・per_action_total・occ_*(4)・_fam_renderer・day_heads・state_files・w17_substituted。
- 積算 11: calls_by_cond・geometry_hops・geometry_jammed・leave_closed・n_fleet_reinjected・n_fleet_resent・n_outside_calls・n_undefined_total・peak_backlog・peak_intents・peak_pending。
- 引数越しに書かれる物(〔改訂(第330・K8)〕): `talk_stats`(L6 の `intents_from_responses(stats=...)` が書き、E2 が読む)・`intero_cross`(L7 の `_count_intero_crossings` が書く)。
- tick の中の受け渡し(系の間を流れる値・主なもの 15): field_rows(L4→L7)・llm_intents(L6→L15)・applied_now(L6→L18)・applied_activity(L6→L19)・focus_request(L6→L17。〔改訂(第330・R1)〕個体数ぶんの 1 本のバッファを使い回し、L6 のどの分岐でも `FOCUS_NONE` で埋め直す)・d/e/p/c/s/f/a の候補(L7〜L12→L12)・cands(L12→L13・L21)・decision(L13→L14・L21)・n_parse_errors_fleet(L5/L11→L14)・intents(L15→L16・L21)・plan(L16→L17・L18・L20・L21)・outcome(L17→L18・L20・L21)・_exp(L20 の中)・n_undefined(L6→L21)・n_parse_errors(L14→L21)。

### 1-5. 状態台帳 189 行との対応

- 台帳は SoA 93 行+外の状態 96 行。系ごとに書き手を測った表は [ledger_writers.md](../bench/analysis/wallbounce-1012/run-day-decomp/ledger_writers.md)(189 行・系・世界過程・resolve の口)。
- 測り方: `sys.monitoring` の LINE 事象を `run_day` の code だけに張り、系の先頭の文に来るたびに SoA の全列・外の状態の全道筋・診断の積算の digest を取り、差を直前の系に帰属させた。〔改訂(第330・K5 (a))〕境目は区間でなく §2-2 の系に合わせた(L11・L12・L20 を系で割った)。6 構成(v3 既定 2 日・v3 記憶+関係+店+同席・v3 古典+記憶+関係・v1 edge・v2 edge・golden の帰無腕)・1,000 体・seed 1・1 日 66 tick の窓。測りを入れても 6 構成の final と呼数は入れないランと一致した(§5)。
- 結果: 書き手が見えた行は 134(SoA 69/93・外 65/96)。2 つ以上の系が書く SoA の列は 28、外の状態の行は 27。`activity` は 7 か所(world・presence・apply_responses・plan_boundary・phase_c・conversation・close_final)、`transit_state`・`transit_ref` は 4、`talk_partner`・`target_node`・`cell` ほかは 3。O19(関係の招待の塩)と O70(計画実行層の計数)は 5 か所。書き手が多い列は、系の順を 1 つも入れ替えられないことを示す。
- 〔改訂(第330・K4)〕見えない 55 行(SoA 24・外 31)の扱い: この 6 構成と窓で値が変わらなかった行で、書き手が無いとは限らない(艦隊・再生・遅れ 2・再開・止めたラン・6 構成で立たない腕=親しみ・注視・行列の満席・hotel・dispatch など)。宣言はこの観測から作らない。SoA の列は静的な閉包(§2-5)で宣言に入り、外の状態の道筋は系ごとの手で書く表で宣言する。どちらも、19 構成と艦隊・再生・遅れ 2・再開の試験で段 A・B を回したときに漏れが見つかれば足す(§3-1 の段 1)。

### 1-6. SoA の書き口(静的)

- AST の書き(代入の左辺・`X.c[...] =`・`np.*.at`・`fill`・`out=`)を `engine/state_ledger_ast._is_write` で数えた([soa_writers_ast.json](../bench/analysis/wallbounce-1012/run-day-decomp/soa_writers_ast.json))。列名 91 のうち 87 に静的な書き手。ファイル別では `engine/resolve.py` 83 列・`agents/state.py` 29 列(確保と初期値)・`world/state.py` 8 列(`World.__init__`)。
- 〔改訂(第330・記録の誤り 1)〕静的な書き手の無い列は 4: `fatigue_stage`・`thermal_stage`(`apply_detection` が `field(変数)` で書く=動的には detect で見えた)・`noise_stage`・`invocation_distance`。
- 〔改訂(第330・記録の誤り 5)〕属性の名の AST に出ない書きが 3 つある。① `economy/ledger.py:_apply_cash`(:640)が、世帯の現金として採用した同じ配列 `agents.money` を `np.add.at(cash_p, ...)` で書く(resolve の `_complete_buy`・`_complete_eat` の窓の中から呼ばれる)。② resolve の局所の別名 `cur = agents.registry.refractory_until` → `np.maximum.at(cur, ...)`(`set_refractory`・820)。③ 同じく `holdings = agents.registry.holdings` → `np.add.at(holdings, ...)`(`consume`・2717)。②③ は改訂した `build_allow.py` が別名をたどって拾う。① は手で書く別名の表([alias_writes.json](../bench/analysis/wallbounce-1012/run-day-decomp/alias_writes.json))に載せた。
- 強制の仕組みは既にある。`AgentState.freeze()`(agents/state.py:786)と `writable()`(:802)・`World` と `PerceptionState` も同じ形。`writable()` を呼んでよいのは resolve だけ(`tests/engine/test_two_phase.py` の静的検査)。ただし解くのは全列なので、「どの列を書いてよいか」はまだ縛っていない。`np.<ufunc>.at` は書き込みの旗を見ないので、resolve は `_require_thawed`(resolve.py:329)で状態の物の `frozen` を見て塞いでいる(配列ごとではない)。台帳は `_apply_cash` で配列の旗を見ている。

### 1-7. `engine/processes/` の口(世界過程 18 本)

- 口の形: 各過程のクラスは `process_ids`(台帳の行)・`ablation_id`・`step(tick)`・一部は `relay_day`。実行器 `WorldProcessRunner.step` が `PROCESS_ORDER`(runner.py:86・18 本)の順に呼ぶ。書きは resolve の口を通す(runner.py の説明 §3 実装原則 3)。読み書きの宣言はまだ無い。
- 実測(3 構成・1,000 体・窓の tick・過程の `step` の前後の digest)と、読む SoA の列(ファイル単位の静的な読み):

| 過程 | ファイル | 書いた SoA の列 | 書いた外の状態の行 | 読む SoA の列(静的・ファイル単位) |
|---|---|---|---|---|
| environment | environment.py | thermal | O56・O73・O76 | cell |
| rail | rail.py | activity・band・cell・node・transit_ref・transit_state・xy | O50・O74・O73・**O36・O70(計画実行層)** | transit_ref・transit_state |
| opening | opening.py | pois.open_now | O73 | cell・kind・open_now |
| crowd | crowd.py | activity・poi_ref・poi_since | O73・O75・O95 | activity・cell・density・poi_ref ほか 9 |
| traffic | traffic.py | — | O55(LastMile・BusTaxi・Traffic を束ねた行) | — |
| delivery_inbound・shelf・waste・street_cleaning | goods_flow.py | (静的には consume で holdings) | O52・O53・O59・O60・O80・O81・O93・O73 | cell・density・holdings・kind・stock |
| last_mile・bus_taxi・road_works | logistics.py | — | O54・O55・O73 | — |
| hotel・infra・press・large_event・dispatch | civic.py | large_event: activity・band・cell・node・plan_flags・transit_*・xy | O49・O55・O73・**O37・O70(計画実行層)・O74(鉄道)** | cell・kind・transit_ref・transit_state |
| salient | salient.py | (知覚 SoA の heading・task_flag を書く口を持つ) | O46・O72 | activity・cell・density ほか 8 |

- dispatch・hotel・shelf は窓の中で値が変わらなかった。

## 2. 系の切り方の案

### 2-1. 方針

1. 1-0 は結果不変。系の境目は今の実行順の区間に合わせ、順は 1 つも入れ替えない(§1-5 のとおり 1 つの列を 7 つの系が書くため)。
2. 話題(体・世界・知覚・判断・行為の解決・会話・記憶・計器)は系の上の群の名札にする(Unity の SystemGroup・flecs の phase に当たる。§4)。
3. 状態は「箱」に集め、系は箱を引数で受け取る関数にする。クロージャは無くす。
4. 書きは今までどおり resolve の口だけ。系の宣言は「呼んでよい resolve の口」を持ち、書く SoA の列はその口の静的な書き集合の閉包から機械で作る。
5. ハッシュに入る名(台帳の鍵・道筋・持ち主の名・値のクラスの置き場)は変えない(§3-3 の 2)。
6. 物の同一性を保つ(使い回すバッファ・差し込んだ関数が組み立ての時点で捕まえた物)。

### 2-2. 系の一覧(呼ぶ順)

「群」は名札。「元」は §1-2 の区間。「書く」は §1-5・§1-6 から作った宣言の素案(SoA は [allow.json](../bench/analysis/wallbounce-1012/run-day-decomp/allow.json) の `allow`=静的な閉包)。「積算」は試験のときだけ指紋に入れる RunStats の欄(動的に変わったもの)。

| # | 系 | 群 | 元 | 時 | 読む(主なもの) | 書く(主なもの) | LLM |
|---|---|---|---|---|---|---|---|
| D1 | day_head | 暦 | L0 | 日の頭 | calendar・weekly・schedule | 計画境界の表(DayTables)・presence の今日の写し・runner の日の表・plan_activity | 無 |
| 1 | body | 体 | L1 | tick | agents の体の列・energy | hunger・fatigue・energy_balance・since_meal_kcal・O28 | 無 |
| 2 | world | 世界 | L2 | tick | 過程ごとの宣言の和(18 本の下位の系) | §1-7 の和(SoA 23 列=閉包・22 行) | 無 |
| 3 | presence | 体 | L3 | tick | presence・act_layer | 12 列・O36・O70・積算 layer_counts | 無 |
| 4 | perceive_prepare | 知覚 | L4 | tick | runner の流れ・行列・騒音・活動の行 | scratch.field_rows・描画のキャッシュ(除外の一覧の行) | 無 |
| 5 | llm_receive | 判断 | L5(遅れ 1)/ L11 前半(遅れ 2) | tick | fleet_bridge・replay_inbox | O43 pending・O44・O96・会話と記憶(会話ターンの発話)・scratch.n_parse_errors_fleet | 受 |
| 6 | apply_responses | 判断 | L6 | tick | O43・schedule・poi_resolver・intent・rel | activity・talk_partner・会話 O39/O41/O91・O5/O6・O13・O19・O25・O26・O34・scratch.llm_intents/applied_now/applied_activity・Buffers.focus_request・積算 talk_stats | 無 |
| 7 | detect | 知覚 | L7 | tick | scratch.field_rows・体の列・cells.density | 段の 3 列・cells.b4_hash・O45・O6・O66・scratch.d_*/e_*・積算 intero_cross | 無 |
| 8 | plan_boundary | 体 | L8 | tick | DayTables・presence | activity・board_line・plan_activity・sleep_pending・target_node・O70・scratch.p_*・積算 layer_counts・sleep_counts | 無 |
| 9 | home_meal | 体 | L9 | tick | energy.home_meals | hunger_stage ほか(腕 on のとき) | 無 |
| 10 | wake_sources | 判断 | L10 | tick | conv・runner.salient | scratch.c_*/s_* | 無 |
| 11 | wake_filter | 判断 | L11 後半+L12 前半 | tick | fleet_deferred・presence | refractory_until(再投入)・O44・scratch.f_*・d/p/e の歩く退出の抑止 | 無 |
| 12 | relations_wake | 会話 | L12 中 | tick | rel_layer・activity・transit_state | rel_* 6 列・O16・O18・O19・scratch.a_* | 無 |
| 13 | wake_assemble | 判断 | L12 後半 | tick | scratch の候補 | scratch.cands | 無 |
| 14 | arbiter | 判断 | L13 | tick | scratch.cands・refractory_until・activity・transit_state | O42・O71・scratch.decision・積算 awake_* | 無 |
| 15 | decide | 判断 | L14 | tick | scratch.decision・描画に要る全部(B0〜B6) | refractory_until・O43・O44・O96・mem_* 9 列(`_utter` の発話)・会話・O8/O9/O11・O15・O17・O19・方策 4 行・描画 3 行・O86・テープ・積算 calls_by_cond・layer_counts・n_outside_calls・peak_pending・result(呼数) | **発** |
| 16 | phase_a | 行為の解決 | L15 | tick | scratch.llm_intents・act・intent | O5・O6・O66・scratch.intents・積算 layer_counts・peak_intents | 無 |
| 17 | phase_b | 行為の解決 | L16 | tick | scratch.intents・pois.stock・capacity | scratch.plan | 無 |
| 18 | phase_c | 行為の解決 | L17 | tick | scratch.plan・Buffers.focus_request・runner の 4 過程 | 40 列=閉包(移動・購入・食事・乗車・お金・在庫・焦点・意図)・O28・O50・金と物の台帳 9 行・scratch.outcome・積算 geometry_*・leave_counts・per_action_total・result | 無 |
| 19 | conversation | 会話 | L18 | tick | scratch.plan・applied_now・outcome | activity・talk_partner・O19・O39・O41 | 無 |
| 20 | activity_intent | 体 | L19 | tick | scratch.applied_activity・conv | activity_kind・activity_until・intent_*・last_action・O1・O2・O4〜O6・O66 | 無 |
| 21 | memory | 記憶 | L20 前半 | tick | scratch.plan/outcome・conv・salient・描画の露出の控え | mem_*・sm_*・rel_*(エピソードの書き手)・O9〜O12・O19・O64・O68・scratch.exposures | 無 |
| 22 | familiarity | 記憶 | L20 中 | tick | scratch.outcome・exposures | fam_* 5 列(腕 on のとき=6 構成では立たない・閉包に手で足す) | 無 |
| 23 | energy_after | 体 | L20 後半 | tick | energy | O28(診断の延べ) | 無 |
| 24 | observe | 計器 | L21+L22 | tick | scratch の全部・conv・bridge | 診断の行・O34・O70(presence.sample)・在圏 journal・積算 diag_rows・prev_sessions・sleep_counts | 無 |
| 25 | checkpoint | 計器 | L23 | tick | 台帳の全部(読むだけ) | result.checkpoints | 無 |
| D2 | day_close | 暦・お金 | L24・E1 の締め | 日の終わり | runner・ledger | 金と物の台帳・runner の日の締め(最後の日は鉄道の最後の便を流す=activity・transit_*)・締めの後のハッシュ・状態のファイル | 無 |
| R1 | build | 組み立て | S0〜S8 | ランの頭 | 引数 | 状態の箱の全部 | — |
| R2 | drain | 判断 | E0 | ランの終わり | fleet_bridge・replay_inbox | O43・O44・O96 | 吸 |
| R3 | report | 計器 | E1 の残り〜E4 | ランの終わり | 全部(読むだけ) | RunResult・積算 sleep_counts(計画実行層の分を足す) | — |

- 数: tick の中の系 25・日の境目 2・ランの単位 3。世界過程 18 本は `world` の下位の系。
- `llm_receive` は 1 つの系で、置く位置が 2 つある(`response_delay=1` は 5 の位置、`2` は 10 と 11 の間)。進行役が設定で位置を選ぶ。
- 「移動」は phase_c(と world の鉄道・presence)、「お金」は phase_c と day_close、「鉄道」は world の下位の系 rail。ユーザーの挙げた話題は群の名札でたどれる。
- `phase_c` の中の行為ごとの分割、`decide` の中の描画と候補の口の分離は 1-0 の外(土台 1-2・1-8 で行う)。

### 2-3. 状態の箱

未リサーチ(expedient)。名は案。〔改訂(第330・K8)〕run_day の局所 449 個を全部、下のどれか(か「tick の中の一時」)に割り当てる表を作り、割り当ての無い局所を 0 にしてから切る(表は段 C の門)。

| 箱 | 中身 | 台帳 |
|---|---|---|
| `RunConfig`(凍結) | 検査済みの腕と値(S0〜S1 の結果)・tpd・total_ticks・t_begin/t_end | 対象外(設定。指紋 `_call_args` はここから作らず、今の位置で作る) |
| `SoAState` | agents・world(cells・pois)・pstate(知覚) | SoA 93 行 |
| `Layers` | 台帳の持ち主 21 個(`_hash_owners` の鍵と同じ名: act_layer・intent_layer・fam_layer・mem_layer・poi_resolver・wom・rel_layer・classical・energy・norm_meter・presence・conv・arbiter・detector・runner・ledger・undefined・renderer・bridge・fleet_bridge・run_day) | 外の状態 96 行 |
| `LlmIo` | pending・fleet_deferred・fleet_waiting・fleet_inflight・replay_inbox・prev_tape_misses | O43・O44・O96(持ち主の名 `run_day` を残す) |
| `DayTables` | b_agent・b_cond・b_tick・b_cell・b_start・w17_substituted | 対象外(資産と暦から作り直せる。再開は `_relay_tables` を過去の日に回して作る) |
| `Buffers`(〔改訂(第330・R1)〕) | 使い回すバッファ: `focus_request`(個体数ぶん 1 本・注視の腕のときだけ確保)。tick の頭で空にしない。中身の埋め直しは今と同じく apply_responses の各分岐で `FOCUS_NONE` を書く。物は 1 回だけ作り、同じ物を phase_c に渡す | 対象外(tick の中だけの中身だが物は使い回す) |
| `TickScratch` | §1-4 の受け渡しの値(約 25 欄・推測)。tick の頭で空にする(試験では「読んだら落ちる番兵」で埋める=T4) | 対象外(tick の中だけ=軸 2 の discardable に当たる)。欄ごとに書き手の系を宣言 |
| `RunStats` | phase・diag_rows・layer_counts・sleep_counts・awake_*・peak_*・積算 11・`talk_stats`(〔改訂(第330・K8)〕)・`intero_cross`・result の積算 23 欄・occ_* | 対象外(診断。manifest と診断の表はここから作る) |

### 2-4. 進行役(擬似コード)

```python
def run_day(n_agents=5_000, seed=1, world=None, *, ...):  # 署名は今のまま(_call_args の指紋を変えない)
    _call_args = dict(locals())                              # 今と同じ位置・同じ中身
    cfg = RunConfig.check(_call_args)                        # S0〜S1
    box = build(cfg)                                          # S2〜S8(状態の箱・再開の復元)
    plan = Schedule.of(SYSTEMS, cfg)                          # 立つ系だけ・llm_receive の位置
    for T in range(cfg.t_begin, cfg.t_end):
        ctx = TickCtx(T=T, td=T % cfg.tpd, day=T // cfg.tpd)
        if ctx.td == 0 and T > 0:
            run_system(DAY_HEAD, ctx, box)
        box.scratch.reset()                                   # Buffers は空にしない(R1)
        for spec in plan.tick:
            run_system(spec, ctx, box)
        if ctx.td == cfg.tpd - 1 and T != cfg.total_ticks - 1:
            run_system(DAY_CLOSE, ctx, box)
    run_system(DRAIN, None, box)                              # ランの終わりも同じ検査(K7)
    run_system(DAY_CLOSE_FINAL, None, box)
    return run_system(REPORT, None, box)

def run_system(spec, ctx, box):
    with box.guard.only(spec), box.stats.timer(spec.phase_key):   # 書いてよい列だけ解く
        out = spec.fn(ctx, box)
    if box.fingerprint is not None:                                  # 試験のときだけ
        box.fingerprint.update(spec, ctx, box)                       # 全欄の差を系に帰属
    return out
```

### 2-5. 口(インターフェース)

宣言は 1 つの表(状態台帳と同じく機械が読む 1 ファイル)。デコレータで登録しても、行き先は同じ表にする。未リサーチ(expedient)。

```python
@dataclass(frozen=True)
class Access:
    soa: frozenset[str] = frozenset()      # "agents.cell"・"cells.b4_hash"(状態台帳の SoA の鍵)
    paths: frozenset[str] = frozenset()    # "O39:conv.sessions"(状態台帳の外の状態の 鍵:道筋。行は割らない)
    scratch: frozenset[str] = frozenset()  # "applied_now"(TickScratch の欄)
    buffers: frozenset[str] = frozenset()  # "focus_request"(Buffers の欄)
    stats: frozenset[str] = frozenset()    # "layer_counts"(RunStats の欄・診断)

@dataclass(frozen=True)
class SystemSpec:
    name: str                     # "phase_c"
    group: str                    # "行為の解決"(名札)
    slot: str                     # "tick" | "day_head" | "day_end" | "run_head" | "run_end"
    fn: Callable[[TickCtx, Box], Any]
    reads: Access                 # 静的な読み(箱の属性の参照)だけを AST で確かめる
    writes: Access                # soa は resolve_ops の閉包から機械で作る(手で書かない)
    resolve_ops: frozenset[str]   # 呼んでよい resolve の口("apply" ほか)=手で書く(道具で下書き)
    calls_llm: str                # "" | "send" | "receive" | "drain"
    when: str                     # 立つ条件の名(例 "act_layer")
    origin: str                   # 元の区間("L17・run.py:4191-4249 @0389689")

SYSTEMS: tuple[SystemSpec, ...] = (...)   # 並び=呼ぶ順(進行役はこの順にしか呼ばない)
```

- 系は「受け取る」= `TickCtx`(時刻)と `Box`。「返す」= 無し(書きは箱へ・tick の中の受け渡しは `TickScratch` へ。report だけ RunResult を返す)。返り値で渡さないのは、今の受け渡しの多く(applied_now・focus_request)が 2 つ以上先の系に届くため。
- 〔改訂(第330・K4)〕宣言の正は静的な閉包。`writes.soa` = `resolve_ops` から resolve.py の中の呼び出し(名前の参照と、`_APPLY` のような表を通す呼び出しを含む)をたどった関数の、AST で見える書き(局所の別名をたどる)+手で書く別名の表(`_apply_cash` の `agents.money`・`apply_detection` の `field(変数)` の 3 列)。道具の下書きは [build_allow.py](../bench/analysis/wallbounce-1012/run-day-decomp/build_allow.py)。`resolve_ops` は手で書く表(下書きは 6 構成で実際に呼ばれた口・6 構成で立たない腕の口=親しみの `write_familiarity` などは手で足す)。描画と方策へ差し込んだ関数(§1-3 の 7 つ)を通る経路は AST でたどれないので、その経路の口は手で書き、段 A・B の実行時の検査と突き合わせる。
- 〔改訂(第330・K4)〕動的な観測は漏れの検査に使う。「試験のランで系の前後に変わった SoA の列 ⊆ `writes.soa`」を確かめ、外れた列があれば閉包の規則か別名の表の欠けとして直す。試作の閉包の最初の版では、局所の別名(`refractory_until`)と `_APPLY` の表を通す呼び出し(`fatigue`・`talk_partner`)の 3 列が漏れ、規則を足して 0 になった(§2-6)。
- 〔改訂(第330・K6)〕読む欄(`reads`)は、1-0 では静的な読み(系のモジュールの中の箱の属性の参照)を AST で確かめるだけにする。層のメソッドの中の読みと実行時の読みは見ない(落とすのは書きだけ)。
- 副作用の宣言 = `writes`(SoA・道筋・scratch・buffers・stats)と `resolve_ops` と `calls_llm`。テープ・艦隊・ファイルへの書きは `calls_llm` と `slot` で表す。
- `when` は腕で立たない系を表から外す(今の `if act_layer is not None:` を進行役が持つ)。系の中の分岐(腕の値)は今のまま系の中に残す。

### 2-6. 宣言の外を書いたら落ちる検査

〔改訂(第330・K1〜K3・K7・K9)〕段 A は numpy の旗だけでは保証にならない(numpy 2.5.3 で、読み取り専用の配列にも `np.add.at`・`np.maximum.at` は書ける・凍結の前に作ったビューも書ける=検収役の実測を親が再現)。「宣言の外を書いたら落ちる」は、次の A・D・B の 3 つを合わせて保証する。C は scratch の分。

| 段 | 対象 | 作り方 | いつ |
|---|---|---|---|
| A 実行時(SoA) | SoA 93 行 | ① 解除口 `writable()` の解除を「いまの系の `writes.soa` だけ解く」にする。② resolve の口の中の `_require_thawed` を、状態の物の `frozen` でなく**書く配列ごとに** `flags.writeable` を見る形にする(ufunc.at の前に必ず呼ぶ。`economy/ledger.py:_apply_cash` の形と同じ)。宣言の外の列を書くと、添字の代入・`fill`・`out=` は numpy が、`ufunc.at` は ② が `ValueError` を投げ、書いた行で止まる | いつも(既定で入れる・切替口で外せる=§0-2) |
| D 静的(AST) | 系のモジュールと resolve | ① 系が呼ぶ resolve の口 ⊆ `resolve_ops` ② `writes.soa` は閉包から機械で作り、手で書いた値と食い違えば落とす ③ 系が触る箱の属性 ⊆ `reads ∪ writes` ④ `writable()`・`thaw` を系から呼ばない(`test_two_phase` の延長)⑤ `flags.writeable =`・`setflags(write=...)` の直書きは決まったファイル(状態のモジュール・`economy/ledger.py`・`economy/goods.py`・resolve の復元 `_restore_array_into`)だけ ⑥ SoA の配列の切り出し・ビュー・別名を層の属性に持たせない(状態のモジュールと resolve の外で `X.registry.<列>` を属性に代入しない)⑦ `ufunc.at` の前に配列単位の `_require_thawed` がある(`tests/engine/test_add_at_guard.py` の延長)⑧ `SYSTEMS` の書く鍵が状態台帳に全部ある | pytest |
| B 実行時(全欄の差) | SoA 93 行+外の状態の道筋+RunStats | 試験のとき、系の前後で全欄の digest を取り、変わった欄 ⊆ `writes` を確かめる(SoA にも広げる=A をすり抜けた書きもここで落ちる)。外の状態は道筋の単位(`item_digest(owners, key, path)`)。重いので小さな人数と標本の tick で | 試験(段 1) |
| C 実行時(scratch・buffers) | TickScratch・Buffers | `__setattr__` で、いまの系の `writes.scratch`・`writes.buffers` に無い欄の書きを落とす | いつも(軽い) |

抜け道ごとに、どの段が捕まえるか:

| 抜け道 | 実例(HEAD `0389689`) | A | D | B |
|---|---|---|---|---|
| `np.<ufunc>.at` は旗を見ない | resolve の `refractory_until`(820)・`pois.stock`(2262)・`pois.revenue`(2264・2362)・`holdings`(2717)・`_apply_cash` の `agents.money` | ② で止まる(試作で確かめた) | ⑦ | 変わった列で落ちる |
| 旗の直書き(thaw を通らない解除) | `economy/goods.py:446`(在庫の窓)・`economy/ledger.py:298`(台帳の窓・世帯の現金の行は飛ばす)・`resolve.py:3224 _restore_array_into`(再開の復元) | 効かない(自分で解く) | ⑤ で場所を固定 | 台帳と在庫の道筋の変化で落ちる |
| 凍結の前に作ったビュー・別名を層が持つ | 今は無い(`attach_household_cash` は同じ配列そのもの=旗が効く)。推測で将来の層 | 効かない | ⑥ | 変わった列で落ちる |
| resolve の局所の別名 | `set_refractory` の `cur`・`consume` の `holdings` | ① ② で止まる(同じ配列) | 閉包が別名をたどる | — |
| `field(変数)` の書き | `apply_detection` の段の 3 列 | ① で止まる | 手で書く別名の表 | 変わった列で落ちる |
| 外の状態(層の中の表)の書き | 鉄道が O36・O70 を書く など | 効かない | ③(箱の属性の単位) | 道筋の変化で落ちる |

試作(コードは変えず、走らせるときに差し替えた。[guard_poc.py](../bench/analysis/wallbounce-1012/run-day-decomp/guard_poc.py)): ① `AgentState.thaw`・`World.thaw`・`PerceptionState._set_writeable` を「いまの系の許可の列だけ解く」に、② resolve の中の `np` を代理に替えて `<ufunc>.at(arr, ...)` の前に `arr.flags.writeable` を見る。許可の列は静的な閉包([allow.json](../bench/analysis/wallbounce-1012/run-day-decomp/allow.json) の `allow`)。守る範囲はループの中の系に加えて drain・最後の締め・report(組み立ては守らない)。1,000 体・seed 1。

| 構成 | 外した列 | 結果 | final・落ちた所 |
|---|---|---|---|
| v3 既定・1 日 | — | 通った | `a2edde01b409d6a1`(入れないランと同じ) |
| v3 既定・2 日 | — | 通った | `08013362b035909d`(同じ) |
| v3 記憶+関係+店+同席 | — | 通った | `28a316167605d410`(同じ) |
| v3 古典+記憶+関係 | — | 通った | `a7c16d0fd2d59a0a`(同じ) |
| v1 edge | — | 通った | `9a7c5f0b66359886`(同じ) |
| v2 edge | — | 通った | `5c881f69e0894b50`(同じ) |
| golden の帰無腕 | — | 通った | `bee59e96a1849734`(同じ) |
| v3 既定 | world:agents.thermal | 落ちた | `environment.py:299 step → resolve.py:2742 set_thermal` |
| v3 既定 | phase_c:agents.money | 落ちた | `resolve.py:2224 _complete_buy → ledger.py:640 _apply_cash`(台帳の自前の旗の検査) |
| v3 記憶+関係+店 | decide:agents.mem_last | 落ちた | `memory.py:611 note_utterance → resolve.py:954 write_memory` |
| v3 記憶+関係+店 | relations_wake:agents.rel_last | 落ちた | `relations.py:976 copresent_step → resolve.py:1004 write_relations` |
| v3 既定 | decide:agents.refractory_until(ufunc.at) | 落ちた | `run.py:4044 → resolve.py:820 set_refractory`(配列単位の検査) |
| v3 既定 | phase_c:pois.revenue(ufunc.at) | 落ちた | `resolve.py:2264 _complete_buy`(配列単位の検査) |
| v3 既定 | world:agents.holdings(ufunc.at) | 落ちた | `goods_flow.py:498 _household_consumption → resolve.py:2717 consume`(配列単位の検査) |
| v3 既定 | phase_c:pois.stock | 落ちた | `resolve.py:2257 _complete_buy`(添字の代入) |
| golden の帰無腕 | close_final:agents.transit_state | 落ちた | `run.py:4590 → runner.py:432 end_of_day → rail.py:785 → resolve.py:2836 rail_depart` |
| v3 既定・2 日 | close_final:agents.transit_state | 落ちた | 同じ所 |
| v3 既定・1 日 | close_final:agents.transit_state | 落ちない(通った) | この 1 日のランでは最後の締めで鉄道が誰も動かさない=書きが起きない。負の対照は書きが起きる構成で回す |

- 改訂前の試作(ufunc.at を見ない形)では、検収役の負の対照 `refractory_until`・`pois.revenue` が落ちなかった。改訂後は落ちる。
- 改訂の後に許可を静的な閉包に替えたら、改訂前の許可(動的な観測 ∪ 区間で呼ばれた口の直接の書き)に無かった `holdings`(world の `consume`)が要ると分かった。6 構成の窓の tick では値が変わらず、動的な観測では見えなかった列。② を入れた最初の試行で world が落ちて見つかった(K4 の実例)。
- 「動的に変わった列だけを許可」にすると v3 既定 1 日が phase_c(`resolve.py:2278 _complete_buy`)で落ちる(検収の F20 を scratch で再現した。値が同じでも書き込みはする)。
- 重さ: 改訂前の試作で、v3 記憶+関係+店・1,000 体・1 日のプロセス全体の壁時計が、入れない 15.1〜15.7 秒・入れる 18.3〜19.5 秒(2 回ずつ・+16〜29%)。改訂後の試作(ufunc.at の代理を足した形)と本実装の重さは未計測。

### 2-7. 系ごとの出力の指紋

- 〔改訂(第330・K5)〕形: 系ごとに「全欄の digest の差」を取る。系の前後で SoA の全列・外の状態の全道筋・scratch・buffers の digest を取り、変わった欄の (欄, 後の digest) を集めて `fp[系] = blake3(fp[系] ‖ T ‖ 変わった欄の並び)` を tick ごとに鎖でつなぐ。宣言の外の書きも、書いた系の指紋に出る(宣言した欄だけの digest にすると、宣言の外の書きは後でそれを読む系の指紋に初めて出て、差の場所を誤る)。日ごとに 1 本を記録に出し、2 本のランを突き合わせて「最初に食い違った (T, 系, 欄)」を出す(`checkpoint_detail` と `10d/first_diff.py` の延長)。
- 〔改訂(第330・K5 (c))〕RunStats(診断の積算)と呼数(result の積算 23 欄)は、試験のときだけ指紋に入れる(宣言)。試作の測り([dyn_writers.py](../bench/analysis/wallbounce-1012/run-day-decomp/dyn_writers.py))は `stats.*` として取っている(例: decide で calls_by_cond・layer_counts・n_outside_calls・peak_pending・result が変わる)。
- 指紋で見えない差: (i) 台帳の `multiset` の行と順を持たない辞書・集合は並べ替えてから digest を取るので、並びの差は消える(台帳が正しければ挙動に効かない)。(ii) 台帳の外のキャッシュ(描画のキャッシュは除外の一覧)。(iii) テープ・艦隊。(iii) は byte-check のテープの列の sha で見る。
- 1-0 の切る前の値: 改訂した測りは境目を系に合わせた(`BOUNDS` が §2-2 の系の名・L11・L12・L20 を系で割った)。HEAD に当てた系ごとの差が、切った後の系の指紋の基準値になる。段 1 では小さな人数で全部の tick を取る(今の記録は 1 日 66 tick の窓だけ)。
- 重さ: 改訂後の測り(全欄+積算)は 1,000 体で 1 回あたり約 9〜14 ms(1 日の構成は 1,918 回で 18.0〜27.6 秒)。

### 2-8. 土台(1-1〜1-9 の 9 段)がどの口に乗るか

〔改訂(第330・記録の誤り 8)〕計画の書き方は「T0(1-1)+残りの土台 1-2〜1-9」。

| 土台 | 乗る系・口 |
|---|---|
| 1-1 時計 T0 | 進行役の `TickCtx`(T を秒・ナノ秒の整数に)。系は `ctx` からだけ時刻を読む(今は 115 引数の `tick_seconds` を各所で掛けている)。T1 の事象の待ち行列は進行役のループを置き換える |
| 1-2 知覚の分離 | `perceive_prepare` と `decide` の中の描画。構造のある事実を `TickScratch.percepts` に書く系を `decide` の前に立て、文の描画は `decide` の読み手にする |
| 1-3 出来事の記録 | 箱に共有の出来事ログを置き、書きの種類に「追記」を足す(どの系も追記できる・消せない)。実験の条件を書いてよい系は 1 つだけ(`writes` の検査で強制=CP12)。〔改訂(第330)〕追記は段 B の「変わった欄 ⊆ 書く欄」では検査できない(どの系も変える)ので、「前の分が変わらず長さだけ増える」の検査を別に置く |
| 1-4 規則の表とつなぎの台帳 | 箱の読むだけの表(`reads` に載せる)。版とハッシュは `report` が manifest へ |
| 1-5 権利台帳 | 箱の表。書くのは `world`(雇用など)と resolve の口。`phase_c` の止める検査を縮めるときの読み手 |
| 1-6 記憶の器 M0 | `memory`・`decide`(会話ターンの発話)・`llm_receive`(発話)の書く欄に、出来事ログへの目印を足す |
| 1-7 道具の台帳 | 箱の表。`decide`・`perceive_prepare` が読む |
| 1-8 候補の口 J0 | `decide` の中の口(mock・古典・LLM を同じ入口の別実装に)。`decide` の宣言は変えずに中を差し替えられる |
| 1-9 お金の基本操作 | resolve の口「移す」。`phase_c`・`world`・`day_close` の `resolve_ops` を「移す」に寄せ、段 D の ① で他の口からの書きを落とす。〔改訂(第330)〕台帳の別名の書き(`_apply_cash`)は AST で見えないので、実行時は台帳の自前の旗の検査と段 A の ② が頼り |

〔改訂(第330)〕土台が足す状態(出来事のログ・規則の表・権利台帳・道具の台帳)は状態台帳の行になる。軸 1 を behavior にすると final が動くので、行の軸を足す前に決める(§0-2)。

## 3. 結果不変の確かめ方

### 3-1. 門(回答 10-12b §6-4 の段に合わせる)

| 段 | いつ | 中身 |
|---|---|---|
| 0 | 保存のたび | 切った系の単体の試験(箱の fake で回す)+段 D の静的な検査 |
| 1 | 段の途中 | 段 A・B・C を入れたラン+系ごとの指紋(1,000 体・6 構成・全部の tick)を HEAD の系ごとの差と突き合わせ+byte-check の 3〜4 構成(過去に差が出た v3 既定・v3 記憶+関係・古典+記憶+関係・golden の帰無腕)。〔改訂(第330・試験の欠け)〕次の 5 つを足す。**T1** ufunc.at で書く列ごとの負の対照(refractory_until・pois.revenue・pois.stock・holdings・agents.money)。**T2** 段 B(外の道筋を 1 本外すと落ちる)・段 C(scratch の欄を 1 つ外すと落ちる)・段 D(閉包と手の値の食い違い・旗の直書き・ビューを層に持たせる、をそれぞれ 1 本わざと書くと落ちる)の負の対照。**T3** 系の外(drain・最後の締め・report)の段 A の正と負の対照(試作で最後の締めは確かめた)。**T4** `TickScratch.reset()` の値を「読んだら落ちる番兵」にして、条件つきでしか代入しない局所の古い束縛を読む所を見つける。**T5** 段 A・B を byte-check の 19 構成と、艦隊・再生・`response_delay=2`・再開の既存の試験(`test_fleet_wiring`・`test_tape_deferred`・`test_response_delay`・`resume_19x2`)の上で回し、閉包の漏れを宣言に足す |
| 2 | 取り込みの前 | byte-check 19 構成(`byte_check_10e.py` の side/compare=final・呼数・テープの列の sha・blocks・behavior/full-hash・締めの後の 2 本)+2 日のラン(5,000 体・v3 既定・final と呼数とテープ)+再開の 19×2(10f の `resume_19x2` と同じ形・状態の保存と復元を動かすため)+manifest の一致(`manifest_check_10f.py`)。どれも段 A を入れた形で回す |
| 3 | commit の前 | 全体の pytest(今 3,795 passed)。段 A を入れた形で |

### 3-2. 切る順(安全なものから)

| 段 | 切るもの | 理由・門の重点 |
|---|---|---|
| A | 計器と守りを先に入れる: 系ごとの差の測り・HEAD の基準値(6 構成+19 構成)・〔改訂(第330・K1)〕resolve の `_require_thawed` を配列単位に(振る舞いは変えない想定・byte-check 19 で不変を確かめる)・段 D の静的な検査 ④〜⑦・閉包の道具 | 結果を変えない。ここで T1・T2 の負の対照を作る |
| B | 読むだけの系: checkpoint(L23)・observe(L21〜L22)・report(E2〜E4) | 書かないので指紋は空のまま。ただし observe は O34・O70 を書く(§1-2)=宣言に載せる |
| C | 箱だけ作る: 局所 449 個の割り当ての表(漏れ 0)・`RunStats`・`TickScratch`・`Buffers`・`LlmIo`・`DayTables` に局所の名前を移す(関数は動かさない) | クロージャの遅い束縛(`pending`)と nonlocal(b_*)と使い回すバッファ(`focus_request`)を先に片づける。§3-3 の 1・4・5・17・21 |
| D | 書く系のうち入出力が少ないもの: body・world・presence・perceive_prepare・detect・plan_boundary・home_meal・arbiter・phase_a・phase_b・phase_c | resolve の口が少なく、scratch の受け渡しが 1〜2 本 |
| E | 絡みの多いもの: llm_receive・decide・drain(艦隊・再生・テープ)・apply_responses・conversation・wake_*・relations_wake・activity_intent・memory・familiarity | 会話と記憶を 3〜4 つの系が書く。艦隊と再生は mock で通らないので既存の試験(`test_fleet_wiring`・`test_tape_deferred`・`test_response_delay`)が門 |
| F | 日の境目と組み立て: day_head・day_close・build(S0〜S8・再開の復元)・進行役 | 署名と `_call_args` の指紋・状態のファイルの互換。2 日のランと再開の 19×2 が門 |

### 3-3. 危ない所(22)

1. **`pending` の束縛し直し**(3702)。`_receive_arrivals`(3316)と `_hash_owners`(3373・O43)は名前を遅れて引くので新しいリストを見ている。箱の欄に移すとき、O43 の道筋 `run_day.pending` が同じものを指し続けるようにする。
2. **ハッシュに名が入る**。`external_digest` は `行の鍵:道筋` の文字列を札として流し(state_hashes.py:327)、値のクラスは `module.qualname` を流す(`_qual`・state_hashes.py:94)。final は behavior-hash なので、持ち主の名(`run_day`・`runner`・`classical` …)・道筋・状態に入る値のクラス(活動の payload・対象・会話のセッションなど)の置き場を変えると、挙動が同じでも final が動く。1-0 では変えない。変えるなら版上げにする。
3. **設定の指紋**。`_call_args = dict(locals())`(2411)は関数の頭で全引数を写す。包む関数の署名や既定値が 1 つでも違うと、指紋・ラン ID・再開の見出しの突き合わせが変わる。
4. **`prev_sessions`・`prev_tape_misses`**(3280〜3281・4454〜4455・再開で 3615〜3616)。前の tick の値を読む。診断の行の差分に使う。
5. **計画境界の表の nonlocal**(`_relay_tables` 3439・3469〜3470・5 つ)。活動層・古典の方策・想起優先の候補合成は起動時に表を写して持つ(3044・3024・3122)ので、日で表が変わると 3461〜3468 で止める。箱に移しても「写して持つ」の形は残す。
6. **描画と方策に差し込んだ関数**(〔改訂(第330)〕lambda 3 つ=3074・3143・3193、工場関数の戻り値 3065、入れ子の def 3184・3155・3169)。`decide` の描画はこれを通して記憶・関係・会話を読み、想起の計数(外の状態)を書く。差し込んだ時点で捕まえた物(`agents`・`rel_layer`・`mem_layer`・`conv`)の同一性を保つ。記憶の SoA を書くのは描画ではなく 7 の `_utter`。
7. **`_utter` の 2 か所の呼び手**(到着 3324・3357 と呼の 4089)。会話・記憶の SoA(`note_utterance` → `write_memory`)・口コミを書く。`llm_receive` と `decide` の両方が会話と記憶の書き手になる。
8. **招待の解決を Phase C より前に**(L6・3758〜3766 の注)。順が意図されている。
9. **順の注がある所**。記憶は親しみより前(4401 の注=看板の初見を親しみの表の書きより前に見る)。活動層は resolve と会話の後(4385 の注)。世界過程は ⓪ の前(3653 の注)。
10. **tick の中の受け渡しが 2 つ以上先へ届く**(applied_now L6→L18・focus_request L6→L17・plan L16→L18・L20・L21 ほか)。scratch の欄の書き手と読み手を宣言で固定する。
11. **持ち主をまたぐ書き**。鉄道と大きな催しが計画実行層の O36・O37・O70 と鉄道の O74 を書く(§1-7)。O55 は 3 つの持ち主を 1 行に束ねていて、traffic と infra も書き手に見える。〔改訂(第330・K9)〕行は割らず(ハッシュの札が変わる)、検査と宣言は道筋の単位にする(例 `O55:runner.traffic.*` のように持ち主ごとに分けられる)。
12. **1 つの列の書き手が多い**(activity 7 系・transit_* 4 系・28 列が 2 系以上)。系の順を入れ替えると結果が動く。Bevy の ambiguity_detection に当たる「同じ列を書く系の対の一覧」を記録に出し、順を宣言で固定する。
13. **乱数と順(K19)**。乱数は `core.rng.stream(seed, 用途, tick, 体, …)` の counter で引く(mock・会話の招待・選び手・古典・注視・体の定数)ので、tick の中の呼ぶ順に依らない。例外は `--rng-scheme stateful` の顕著行為(salient.py:171・196)と出動(civic.py:134・150)が日の頭の Generator を進める形で、過程の中の引く順に依る。`PROCESS_ORDER` を変えない。アービタは `lexsort` で全部の鍵を並べる(arbiter.py:440・455)ので候補を連結する順(p・d・c・s・f・e)には依らない(推測。完全な同点だけ残る。候補の順を入れ替える試験で確かめる)。
14. **日の締めが 2 つの形**(途中の日 L24=`flush_rail=False`・最後 E1=`True`)。`day_close` に旗を持たせる。止めたラン(`stop_at_tick`)の保存の位置も同じ所にある。
15. **試験が `shibuya.engine.run` の名前を差し替えている**(9 ファイル 20 か所: FleetBridge・PerceptionRendererAdapter・WorldProcessRunner・Arbiter・ConversationManager・full_state_hash・_split_due・_call_ref・sample_population・MemoryLayer.enable_relations)。作る場所が別のモジュールへ移ると、差し替えが効かないまま試験が通るおそれがある。付け替えと「差し替えたものが使われた」の確かめを同じ段で入れる。
16. **検査の表が `engine/run.py` の名を持つ**(`state_ledger_ast.py` に 19 か所・`state_ledger.py` に 1 か所・`DIAG_EXITS` の `RunResult.*`・`test_two_phase` の `_HOT_PATHS`)。切った先のファイルを足す(弱めない=対象を広げる)。
17. 〔改訂(第330・R1)〕**使い回すバッファ `focus_request`**(3273・3796〜3810・4210)。個体数ぶんの 1 本を毎 tick `FOCUS_NONE` で埋め直して phase_c に渡す。`TickScratch` の空(`None`)にすると、注視の腕で L6 の `if focus_request is not None` が飛び、phase_c に `None` が渡って結果が動く(推測。6 構成に注視の腕が無く、測りでは出ない)。`Buffers` に置く。
18. 〔改訂(第330・K1)〕**`ufunc.at` は書き込みの旗を見ない**(numpy 2.5.3)。今の `_require_thawed` は状態の物の `frozen` を見るので、列ごとの許可を入れると素通りする。配列単位に直す(§2-6 の A ②)。
19. 〔改訂(第330・K2・K3)〕**旗の直書きとビュー**。`economy/goods.py:446`・`economy/ledger.py:298`・`resolve.py:3224` は thaw を通らずに旗を立てる。凍結の前に作ったビューは元を凍結しても書ける。段 D ⑤⑥ で場所を固定し、段 B で変化を落とす。
20. 〔改訂(第330・T4)〕**条件つきの代入の古い束縛**。条件つきでしか代入しない局所を後の文が読むと、今は前の tick の値を読む。`TickScratch` を空にすると挙動が変わる。主な受け渡し(`field_rows`・d/e/p/f の候補・`applied_now`・`focus_request`)はどの分岐でも代入すること(検収役が確かめた)。全部の局所は番兵で確かめる(§3-1 の T4)。
21. 〔改訂(第330・K8)〕**箱から漏れた局所**。`talk_stats` のように引数越しに書かれる物は「読むだけ」に分類されていた。局所を全部箱へ割り当てる表で漏れを 0 にする(§2-3)。
22. 〔改訂(第330)〕**計時の鍵**(推測)。進行役が系ごとに時間を測ると、`phase` の鍵の並び(今は `phase["llm"]` を L5・L11・L14 で足し込む)が変わる。`phase_seconds` は壁時計で決定論ではないが、manifest や診断の表の形(鍵の集合)に効くかは確かめていない。鍵の集合は今のまま残す。

## 4. 先例の比較表(状態の表+処理の系)

| 先例 | 状態の表 | 処理の単位 | 読み書きの宣言 | 並び順 | 宣言の外の検出 | ライセンス(写せるか) | 採ったもの |
|---|---|---|---|---|---|---|---|
| UE5 MassEntity | Fragment(archetype の chunk に並ぶ) | Processor(状態を持たないクラス) | `FMassEntityQuery` に `AddRequirement<T>(EMassFragmentAccess, EMassFragmentPresence)`。`ConfigureQueries` は「依存の解き手が処理を見る前」に呼ばれる | `EMassProcessingPhase`(PrePhysics〜FrameEnd)・`ExecutionOrder.ExecuteInGroup/ExecuteBefore/ExecuteAfter`。`BuildFlatProcessingGraph` で多スレッドの実行の図 | 宣言を依存の解き手に使う(実行時の書きの検査は資料で確かめられず) | Unreal Engine EULA(OSS でない・読むだけ。EULA の頁は 403 で未一次確認) | 系ごとの要求の一覧・群(group)・前後の宣言 |
| Unity Entities(DOTS) | Component(chunk) | System(`ISystem`・`SystemBase`) | `RefRO<T>`・`RefRW<T>`・読み取り専用の指定。「システムが読み書きする component から依存を解析する」 | `InitializationSystemGroup`・`SimulationSystemGroup`・`PresentationSystemGroup`・`[UpdateInGroup]`・`[UpdateBefore]`・`[UpdateAfter]`・`OrderFirst/OrderLast` | ジョブの安全の仕組み(並列の書き)。依存はシステム単位なので要らない待ちが出る(公式の注) | Unity Companion License(Unity に依る作品だけ・読むだけ) | 群の名札・前後の宣言。粒度が粗いと要らない依存が出る点 |
| Bevy ECS | Component・Resource | System(関数) | 引数の型 `Query<&T>`/`Query<&mut T>` が宣言。`System::initialize` が `SystemAccess` を返す。同じ系の中の食い違う引数は初期化で panic(出典は Query の頁) | `.before()`/`.after()`・SystemSet。`ScheduleBuildSettings.ambiguity_detection`=「食い違う読み書きで順が決まらない系の対」を知らせる(既定は無視) | 初期化時の検査+順の曖昧さの報告 | MIT または Apache-2.0(出典つきで写せる。外から来た一部のコードは crate ごとの別の条件) | 同じ欄を書く系の対の一覧(§3-3 の 12)・宣言から読み書きを機械で出す |
| flecs | Component(archetype の表) | System(query つき) | query の項に `[in]`・`[out]`。書きの宣言は同期点を入れる場所を決める | 〔改訂(第330)〕組み込みの phase(OnStart=最初の `progress()` だけ・OnLoad・PostLoad・PreUpdate・OnUpdate・OnValidate・PostUpdate・PreStore・OnStore)を DependsOn で位相ソート。phase の中は entity id 順(決定論のため・保証はしない注あり) | 宣言の無い書きは同期点を作らない(遅らせた命令は既定でフレームの終わりに混ぜる) | MIT(出典つきで写せる) | slot(日の頭・tick・日の終わり)を phase として表す・in/out の語 |
| EnTT `organizer` | registry の pool | 登録した関数 | 関数の引数の const が読み取り専用・非 const が読み書き。テンプレート引数で上書きできる | 依存の図(隣接リスト・`top_level`・`children`)を作るだけで実行はしない | 図を作るだけ(検出はしない) | MIT(出典つきで写せる) | 宣言の表から依存の図を作って記録に出す(実行は今の順のまま) |
| Mesa 3(Python) | Agent の属性 | `Model.step`・`AgentSet.do`/`shuffle_do` | 無し | 書いた順。Mesa 3 で scheduler(RandomActivation・StagedActivation)を廃止して AgentSet の呼び分けに(移行の手引き) | 無し | Apache-2.0(出典つきで写せる) | 対照: Python の ABM でも順は明示の呼び出しで書く=進行役の形 |
| MATSim QSim(mobsim と events) | 網とエージェントの状態 | `MobsimEngine`(〔改訂(第330)〕`doSimStep(now)` は `Steppable` から受け継ぐ) | 無し(events で出力を出す) | 登録した順のリストを毎 step 回す。〔改訂(第330)〕前後に `listenerManager.fireQueueSimulationBeforeSimStepEvent`/`fireQueueSimulationAfterSimStepEvent`(listener の型は `MobsimBeforeSimStepListener` など)・`events.afterSimStep` | 無し | GPL-2.0 以降(読むだけ) | 計器と checkpoint を step の後の listener と同じ位置に置く・出来事の記録(1-3)の先例 |
| Agents.jl | agent の struct | `agent_step!`・`model_step!` | 無し | scheduler(既定は最速・`Schedulers.Randomly`・`ByProperty`) | 無し | MIT(出典つきで写せる) | 対照のみ |

まとめ: ゲームの ECS 4 つ(MassEntity・Unity・Bevy・flecs)は、どれも「系が読む型と書く型を宣言し、宣言から順と並列を決める」。ABM の 3 つ(Mesa・MATSim・Agents.jl)は宣言を持たず、順を明示の呼び出しで書く。本案は、宣言を持つ形(ECS 側)を採り、並列には使わず決定論と原因の場所(どの系が書いたか)に使う。強制は Bevy の初期化の検査と Unity の安全の仕組みに近いが、今のコードに既にある numpy の書き込みの可否の旗(`freeze`/`writable`)に、旗を見ない `ufunc.at` の配列単位の検査を足して行う。写したコードは無い(写すときは MIT/Apache の出典を付ける)。

出典(読んだ頁):
- UE5: [ConfigureQueries](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/MassEntity/UMassCompositeProcessor/ConfigureQueries)・[FMassProcessorExecutionOrder](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/MassEntity/FMassProcessorExecutionOrder)・[AddRequirement](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/MassEntity/FMassFragmentRequirements/AddRequirement)・[MassEntity の概要](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-mass-entity-in-unreal-engine)。`EMassProcessingPhase` の値の一覧と `BuildFlatProcessingGraph` の説明は検索の要約からで、頁は未一次確認。
- Unity: [System の更新順](https://docs.unity3d.com/Packages/com.unity.entities@1.3/manual/systems-update-order.html)・[ジョブの依存](https://docs.unity3d.com/Packages/com.unity.entities@1.4/manual/scheduling-jobs-dependencies.html)・[RefRO](https://docs.unity3d.com/Packages/com.unity.entities@1.3/api/Unity.Entities.RefRO-1.html)・[ライセンス](https://docs.unity3d.com/Packages/com.unity.entities@1.0/license/LICENSE.html)。
- Bevy: [ScheduleBuildSettings](https://docs.rs/bevy_ecs/latest/bevy_ecs/schedule/struct.ScheduleBuildSettings.html)・[System](https://docs.rs/bevy_ecs/latest/bevy_ecs/system/trait.System.html)・[Query](https://docs.rs/bevy_ecs/latest/bevy_ecs/system/struct.Query.html)・ライセンスは [README](https://github.com/bevyengine/bevy)。
- flecs: [Systems](https://www.flecs.dev/flecs/Systems.html)・[LICENSE](https://github.com/SanderMertens/flecs/blob/master/LICENSE)。
- EnTT: [entity.md の Organizer](https://github.com/skypjack/entt/blob/master/docs/md/entity.md)・[LICENSE](https://github.com/skypjack/entt/blob/master/LICENSE)。
- Mesa: [移行の手引き](https://mesa.readthedocs.io/latest/migration_guide.html)・[LICENSE](https://github.com/projectmesa/mesa/blob/main/LICENSE)。
- MATSim: [QSim.java](https://matsim.org/doxygen/_q_sim_8java_source.html)(GPL の頭書きと `doSimStep` の回し方)・[MobsimEngine.java](https://matsim.org/doxygen/_mobsim_engine_8java_source.html)。
- Agents.jl: [tutorial](https://juliadynamics.github.io/Agents.jl/stable/tutorial/)・[LICENSE](https://github.com/JuliaDynamics/Agents.jl/blob/main/LICENSE.md)。

## 5. 記録と再現

置き場: [run-day-decomp/](../bench/analysis/wallbounce-1012/run-day-decomp/)(どれもコードを変えずに HEAD `0389689` の上で走らせる)。〔改訂(第330)〕測りと試作を作り直した(系の境目・積算・静的な閉包・ufunc.at の検査・ランの終わりの守り)。

| 道具 | 出すもの | 生の数 |
|---|---|---|
| `static_map.py` | 区間・入れ子の関数・共有の名前([static_map.json](../bench/analysis/wallbounce-1012/run-day-decomp/static_map.json)) | §1-1・§1-3・§1-4 |
| `soa_writers_ast.py` | SoA の列の静的な書き手 | 列名 91・書き手あり 87・resolve の関数 63 本 |
| `resolve_callers.py` | resolve の口の呼び手 | 口 49 種・ファイル 17 |
| `dyn_writers.py`+`agg.py` | 系ごとの全欄の差(SoA・外の道筋・積算・6 構成) | 行 134/189・2 系以上の列 28・行 27 |
| `dyn_process.py` | 世界過程ごとの書き(3 構成) | §1-7 |
| `resolve_calls_by_seg.py`+`build_allow.py` | 系ごとの resolve の呼び出し・静的な閉包・漏れの検査([allow.json](../bench/analysis/wallbounce-1012/run-day-decomp/allow.json)・[alias_writes.json](../bench/analysis/wallbounce-1012/run-day-decomp/alias_writes.json)) | 閉包で許可のある系 14・漏れ 0(規則を足す前は 3 列) |
| `guard_poc.py` | 書きの検査の試作 | [guard_results.jsonl](../bench/analysis/wallbounce-1012/run-day-decomp/guard_results.jsonl)(18 行=正 7・負 10・書きの起きない負 1) |
| `ledger_writers.py` | 台帳 189 行 × 書き手(系) | [ledger_writers.md](../bench/analysis/wallbounce-1012/run-day-decomp/ledger_writers.md) |
| `noprobe.py` | 測りを入れないラン(final の突き合わせ) | 7 構成とも測りありと一致 |

測りを入れても結果が変わらないことの確かめ(1,000 体・seed 1):

| 構成 | 測りなし final・呼数 | 系ごとの差の測り | 書きの検査あり(改訂後) |
|---|---|---|---|
| v3 既定・2 日 | `08013362b035909d`・25,814 | 同じ | 同じ |
| v3 既定・1 日 | `a2edde01b409d6a1`・12,614 | 同じ(過程ごとの測り) | 同じ |
| v3 記憶+関係+店+同席 | `28a316167605d410`・12,698 | 同じ | 同じ |
| v3 古典+記憶+関係 | `a7c16d0fd2d59a0a`・15,836 | 同じ | 同じ |
| v1 edge | `9a7c5f0b66359886`・10,142 | 同じ | 同じ |
| v2 edge | `5c881f69e0894b50`・9,942 | 同じ | 同じ |
| golden の帰無腕 | `bee59e96a1849734`・19,144 | 同じ | 同じ |

走らせ方(リポの根で・`D=docs/bench/analysis/wallbounce-1012/run-day-decomp`): `python $D/dyn_writers.py v3_default 1000 2 $D/dyn_v3_default_2d.json` → `python $D/agg.py $D` → `python $D/resolve_calls_by_seg.py v3_default 1000 2 $D/rcalls_v3_default.json` → `python $D/build_allow.py $D` → `python $D/guard_poc.py v3_default 1000 1 decide:agents.refractory_until`(負の対照・ufunc.at)。同時に多く走らせるとページングファイルが足りず落ちる(16 本で落ちた・4 本ずつなら通った)。

## 6. 限界と未確認

- 動的な測りは mock と古典の 6 構成・1,000 体・窓の tick だけ。艦隊・再生・`response_delay=2`・再開・止めたランの経路は通っていない。そこは静的な閉包と既存の試験で見る(§3-1 の T5)。
- 静的な閉包は resolve.py の中の名前の参照と表をたどる。描画と方策へ差し込んだ関数を通る経路は手で書く表に頼る(§2-5)。6 構成で立たない腕(親しみ・注視ほか)の口は、試作の `allow.json` にまだ入っていない。
- 試作の段 A は、走らせるときの差し替え(resolve の `np` の代理)で配列単位の検査を真似た。本実装(`_require_thawed` を配列単位に)は書いていない。
- 段 B・C・D の試作は無い(段 B は SoA と外の道筋の差の測りだけあり、宣言との突き合わせで落とす形は作っていない)。
- 書きの検査の本実装の重さ・系ごとの指紋の重さは未計測(試作の値だけ)。
- 系の「読む」は箱の属性の単位でしか確かめない(K6)。
- 比較表のうち UE5 の EULA(403)・`EMassProcessingPhase` の値・`BuildFlatProcessingGraph` の説明は未一次確認。
- 用語: 「指紋」「口」は用語集で言い換えを勧める語(用語集の 179・183 行)だが、ユーザーの指示(回答 10-12b §6)の語に合わせた。
