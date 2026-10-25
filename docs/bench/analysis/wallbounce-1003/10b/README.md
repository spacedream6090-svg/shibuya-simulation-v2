# 10b の実装(K15〜K17 に左右されない部分): 状態台帳の 2 軸・AST の検査・behavior-hash と full-hash・保留の組の call_id(2026-10-03)

> 実行役(Opus 5.5)の記録。親の検収前。commit していない。着手の形: [10b のアジェンダ](../../../../design/v2-d102-10b-agenda.md) §2・§4、ユーザー決定: [指示書 10-03](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §3 A2・A3・A4、材料: [10b の材料](../10b-prep.md)。
> **やっていないこと**: 死蔵の列の削除(10e)/ final の定義の変更(10e)/ 原因の欄(① の記録のアジェンダ)/ `fail_streak`・`plan_activity` の扱いの変更(K15)/ リングの保存(K16)/ 金の生ログの宣言と容量(K17)。
> パスは `src/shibuya/` を省略。絶対パスは書かない。

## 0. 結論(10b-3=検収後の直しまで反映した今の値)

1. **既定の結果は動いていない**。基準は HEAD `bbe7e77`(src と tests は `120d147` と同じ=比較は有効)の `git archive` の写し。10b-1 で 19 構成が 19/19 一致([byte_check.json](byte_check.json))、10b-2・10b-3 で既定 v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439・関係 on `40409ebed834126b`/72,930 の 3 本が final・呼数・blocks・calls の 14 列で 3/3 一致([byte_check_after_answers.json](byte_check_after_answers.json)・[byte_check_after_review.json](byte_check_after_review.json))。classical 1,500 体の golden `4f78f3c0`/25,808 は既存のテストで一致。
2. **状態台帳は 187 行**(SoA 98+外の状態 89)・明示の除外の一覧 112 項 491 属性(キャッシュ・導出 127・定数・設定 258・参照 106。10b-2 の 111 項 490 属性に `ledger.money.wallets` を足した)。持ち主のクラス 46(+構成で入れ替わるクラス 2)の属性は、AST でも実行時の `vars()` でも**未カバー 0**。
3. **追加 C の AST の検査は合格**(違反 0)。検収の死角 4 つ(`getattr(持ち主, 変数)`・`.arrays.get`・`attrgetter`・組の代入の自己更新)も塞いだ。
4. **behavior-hash と full-hash** を checkpoint ごとに出し、日の締めの**後**の 2 本を manifest の `state_hashes_end_of_day` に別に出す(**10d の再開の判定は締めの後の full-hash を使う**。behavior-hash は挙動の等価の確認用で、再開の判定には使わない)。final は不変。
5. **費用**: 既定 v3 5,000 体で checkpoint ごとの最大 13.4 ms・全腕 39.3 ms(上限 100 ms)。2 本の合計は 1 回 12.0 ms・1 日 4 回の checkpoint は 41.0 ms。39 万体の線形の外挿は 1 日 3.2 s(上限 10 s・推測)。
6. **テスト**: `tests/engine/test_state_ledger_10b.py` 44 関数・パラメータ込み 70 件・全部合格。回帰の組(§11-6)も合格。
7. 10e へ送るもの: 会話の管理の期限つきの辞書 3 つの掃除(§11-3)。

> **§1〜§9 は 10b-1 の時点の記録**(§10=親の答えの反映・§11=検収後の直し)。食い違うところは後の節が正。10b-1 の結論は §12 に移した。

## 1. 入れたもの

| ファイル | 中身 |
|---|---|
| `engine/state_ledger.py`(新) | 状態台帳の表 `LEDGER`(163 行)と読み口(`rows`・`soa_rows`・`external_rows`・`row`・`behavior_excluded`・`behavior_columns`・`full_excluded`・`full_items`・`counts`)。版 `LEDGER_VERSION = "state-ledger/10b-1"` |
| `engine/state_ledger_ast.py`(新) | 追加 C の AST の検査(`scan`・`check`・`reader_counts`)。試作 [soa_readers_ast.py](soa_readers_ast.py) を元に、直書きの文字列の組を回すループの解決・解決できない読みの許可の表・古い許可の検出・宣言と台帳の列の突き合わせを足した |
| `engine/state_hashes.py`(新) | `behavior_hash`・`full_hash`・`external_digest`・`to_state`(外の状態の直列化の書き手)・`resolve_item` |
| `engine/run.py` | `Checkpoint` に `behavior_hash`・`full_hash` の欄(`combined` は不変)。checkpoint で 2 本を計算(読むだけ)。`RunResult.full_hash_bytes`・`state_hashes_fields()`・manifest の `state_hashes`。保留の組に発射の tick と call_id(`_call_ref`)・保留の組の分け方を関数 `_split_due` に出した(中身は同じ)・入れ物 `_RunDayLocals` |
| `cli.py` | `checkpoints_payload` の各 checkpoint に `behavior_hash`・`full_hash`(値があるときだけ) |
| `tests/engine/test_state_ledger_10b.py`(新) | 27 関数・45 件(§7) |
| 記録 `10b/` | [byte_check_10b.py](byte_check_10b.py)・[byte_check.json](byte_check.json)・[ledger_record.py](ledger_record.py)→[state_ledger_table.json](state_ledger_table.json)・[state_ledger_ast.json](state_ledger_ast.json)・[ledger_uncovered_attrs.json](ledger_uncovered_attrs.json)・[hash_cost.py](hash_cost.py)→[hash_cost_v3_5000.json](hash_cost_v3_5000.json) |

## 2. 状態台帳の宣言(A3)

- **場所**: `engine/state_ledger.py` の `LEDGER`(Python の表に統一。JSON は記録用に [state_ledger_table.json](state_ledger_table.json) へ書き出す)。行の欄: 鍵・名前・置き場・型・バイト・確保の条件・軸 1(`behavior`/`no`/`diag`)・軸 2(`required`/`derivable`/`discardable`/`unknown`)・死蔵・根拠(材料の表の `path:line`=a08109a の行番号)・外の状態の属性の道筋(`items`)・full に入れない属性(`hash_skip`)・AST の許可(`ast_allow`)・注記。
- **行数**: 163(SoA 98+外の状態 65)。

| 置き場 | behavior | no | diag | required | derivable | discardable | unknown |
|---|---|---|---|---|---|---|---|
| agents(79) | 70 | 8 | 1 | 68 | 6 | 3 | 2 |
| cells(5) | 3 | 2 | 0 | 0 | 5 | 0 | 0 |
| pois(9) | 8 | 0 | 1 | 3 | 6 | 0 | 0 |
| 知覚(5) | 0 | 5 | 0 | 0 | 2 | 3 | 0 |
| 外の状態(65) | 32 | 22 | 11 | 31 | 13 | 21 | 0 |

- 指示どおりの宣言: A2 (b) の 6 列(`age`・`sex`・`talk_partner`・`weight_kg`・`sm_last`・`mem_last`)は behavior/`revenue`・`energy_balance` は diag+required/知覚の `heading`・`task_flag` は no(派生=親の宣言)/`fail_streak`・`plan_activity` は no+**unknown**(K15 の欄。behavior-hash から外し full-hash には入れる)/`d_armed`(O31)は required/リング 3 行(O58・O60・O61)は discardable/死蔵は Q9 の 3 列+A4 の 2 列+知覚の `invocation_distance`。
- 材料の表で軸 2 が 2 つ書かれていた行(O23・O24・O26・O55・O63・O2)は、行の値を 1 つに決め、キャッシュと計数の属性を `hash_skip` に入れた(実行役の判断=問 4)。
- 表と実際の SoA: 全部の腕の列を確保した `AgentState`・合成の `World`・`PerceptionState(include_invocation_distance=True)` の宣言と、列名の集合・型(`i4x11` など)・バイトが一致する(テスト。列が増えたら失敗)。AST の検査でも宣言の列と台帳の列の集合を突き合わせる。

## 3. 追加 C の AST の検査([state_ledger_ast.json](state_ledger_ast.json))

- 走査: `src/shibuya` 全体(`build/` を除く)99 ファイル・0.9 秒。数え方は試作と同じ(書き・型の参照・自己更新は読みに数えない)。直書きの組を回すループ(`resolve.py:534` の `for value_field, stage_field in (("hunger", "hunger_stage"), ...)`)も解決するようにした。試作で解決できなかった engine の 4 か所のうち、`resolve.py:534` は解決し、`resolve.py:538`・`:786` は書き(`field(変数)[...] =`)なので読みから外し、残る `run.py` の 1 か所は許可の表に載せた。
- 規則: behavior の列は strict の読み手 ≥ 1、no/diag の列は loose(手前の式を問わない)の読み手 0(許可の場所は除く)、解決できない読みは許可の表に載ること、許可はどこかの読みに当たること(古い許可を残さない)、同名の列は軸 1 が同じこと、宣言と台帳の列が一致すること。
- 結果: **違反 0**。軸 1 が no/diag の 17 列の読み手:

| 列 | 軸 1 | loose の読み | 許可の根拠 |
|---|---|---|---|
| `agents.band` | no | 1(`world/assets.py` の `cells["band"]`) | 資産の表の列 band(SoA の列ではない)=材料 §2-4 の誤検出 1 |
| `cells.b4_hash` | no | 1(`world/state.py` のプロパティ `World.b4_hash` の中) | プロパティの呼び手 0(属性 `.b4_hash` の読みはこの 1 か所だけ=テストで固定)=誤検出 2 |
| `pois.revenue` | diag | 1(`engine/run.py` の `result.revenue_end =`) | 保存則の検査とラン要約だけ |
| `agents.energy_balance` | diag | 1(`engine/energy.py` の `EnergyLayer.summary`) | 日次センサスと要約だけ |
| `perception.heading` | no | 1(`engine/processes/salient.py`) | p_notice が読むが、事象の直前に毎回貼り直す派生の値(親の宣言) |
| `perception.task_flag` | no | 1(同) | 同上 |
| ほか 11 列(`plan_cursor`・`invocation_distance`×2・`wake_pending_class`・`fail_streak`・`plan_activity`・`fam_last`・`rel_last`・`open_count`・`last_b2_hash`・`last_b4_hash`) | no | 0 | (許可なし) |

- 解決できない `field(変数)` の読み 3 か所(許可の表 `UNRESOLVED_ALLOW`): `engine/run.py` の `_count_intero_crossings`(段の 3 列の診断の数え=どれも behavior)・`agents/state.py` と `perception/state.py` の `__getattr__` の転送。
- behavior の列で strict の読み手がいちばん少ないのは 1 件(`poi_since`・`pois.capacity`)。
- T3: `hunger` を no にする/`fatigue`(属性の読みは 0・名前の表 `INTERO_VARS`・`INTEROCEPTION_FIELDS` と直書きの組だけ)を no にする/`plan_cursor` を behavior にする/古い許可を足す/宣言に列を足す → どれも失敗。一時ファイルに `fail_streak` の読みを 5 通り(直接・一時変数・名前の表・直書きの組・文字列)書くと失敗し、書くだけ・自己更新では通る。解決できない読みを足すと失敗。

## 4. behavior-hash と full-hash(A2・A3)

- **final**: `Checkpoint.combined` は今の定義のまま(新しい欄を入れても `combined` が変わらないことをテストで固定)。
- **behavior-hash** = `blake3("\x1f".join([agents の state_hash(exclude=軸 1 が no/diag の列), world(cells・pois を同じく除外して今の World.state_hash と同じ組み立て), 母集団, 予定表 (, 活動と意図)]))`。今の `combined` と同じ組み立てで SoA の列だけを絞ったもの。外の状態は活動と意図(O1・O4、今の `activity_hash`)だけが入る(問 3)。
- **full-hash** = `blake3(見出し ‖ agents・cells・pois・知覚 SoA の state_hash(exclude=軸 2 が discardable の列) ‖ 母集団 ‖ 予定表 ‖ 外の状態の digest)`。外の状態の digest は、軸 2 が required・derivable・unknown の行の属性(122 本・`hash_skip` を除く)を台帳の宣言順に `to_state` で直列化したもの。持ち主は checkpoint のたびに `run_day` が組む `owners` の辞書(19 の根)から `runner.salient.rng` のようにたどる。途中の持ち主が `None`(腕が立っていない)なら「無い」の印、根の鍵が無い・属性が無いのは例外(黙って飛ばさない)。
- **直列化の書き手**(`to_state`・expedient): numpy の配列・数・文字列・dataclass・NamedTuple・辞書(鍵の直列化の昇順)・集合・`Generator`(`bit_generator.state`)・値のクラス 3 つ(`WakeCandidates`・`DeferralQueue`・`EventBudget`)。知らない型は `TypeError`。会話の管理(O39)は `Session`・`PendingInvite` の dataclass と辞書、保留の応答(O43)は 13 要素の組(`ActivityPayload`・`Target` を含む)をこの書き手で直列化する。
- **大きさ**(外の状態の直列化・1 回・5,000 体・既定 v3): 3.32 MB。大きい行は O38 予定の表 1.16 MB・O3 活動層の予定の表 0.74 MB・O39 会話の管理 0.30 MB・O29 範囲外の食事の予定 0.29 MB・O57 金の台帳 0.27 MB。O43 保留の応答は小さい(上位 15 の外)。構成ごとの値は [byte_check.json](byte_check.json) の `state_hashes_10b`(1.98〜3.93 MB)。
- **費用(T7)**([hash_cost_v3_5000.json](hash_cost_v3_5000.json)・この機械・中央値): 1 回あたり final の SoA 部分 0.55 ms・behavior-hash 0.48 ms・full-hash 30.0 ms(うち外の状態 28.9 ms・O39 会話の管理 22.5 ms・O1 活動の文 3.5 ms)。1 日 4 回の checkpoint の合計は **5.0 ms(HEAD・byte-check の値)→ 85.8 ms**(byte-check の 19 構成では HEAD 2.2〜31 ms → 作業木 37〜182 ms)。39 万体への線形の外挿(推測)は 1 日 6.7 s。宣言の上限はまだ無い(問 5)。
- **既知の答え**: 2 日の合成世界ラン(`run_day(sim_days=2)`・既定と全腕)で 8 回の checkpoint の全部に 2 本が出て、2 日目の最後は 1 日目の最後と違う。0 日目の 4 回は 1 日のランと behavior・full とも一致。同じ seed の 2 回のランで 3 本とも一致。manifest の `state_hashes` に最後の値・台帳の版・外の状態のバイトが出る。

### 4-1 T2 の手順(10e で比べる値)

10b の behavior-hash(最後の checkpoint・5,000 体・seed 1・1 シミュ日・`cli.run`):

| 構成 | final(今の定義) | behavior-hash | full-hash |
|---|---|---|---|
| w6_v3_default(golden v3) | `993276d5e5bb5cbe` | `3a56d85fb754b5eb3ecaf09b7ac09bb480a0f5f48ecd1549a075812c817fec48` | `531e665004fad914afb0b5276131d92c214a2010d5ee878fc6259abda0b76265` |
| w6_golden_null_arm(帰無) | `72cb9cd52982da74` | `408104d86f49c94d…` | `ab140d0cccdac717…` |
| v3_mem_rel(関係 on) | `40409ebed834126b` | `76182e3d72e3c317…` | `7bfc176fd8efcbb8…` |
| v3_classical | `3390e3ec02d392a9` | `ff23f19bfb4eeae5…` | `7d4864e9a8c9ffe1…` |

ほかの 15 構成と checkpoint ごとの値は [byte_check.json](byte_check.json) の `state_hashes_10b`。

10e の手順: (1) 死蔵 5 列を宣言から消し、final の定義を behavior-hash(`state_hashes.behavior_hash`=残る no/diag の列を `exclude`)に切り替える。(2) 同じ 19 構成を回し、10e の final が上の behavior-hash(全桁は `behavior_last`)と一致することを確かめる。一致の根拠は「`state_hash(exclude=S)` と S を宣言から消した `state_hash()` は同じバイト列」で、テスト `test_t2_exclude_equals_deleting_the_columns`・`test_t2_behavior_hash_equals_the_final_after_deleting_the_non_behavior_columns` で固定した(`Registry.state_hash` の見出しに列の数や列名の一覧を足すとこの 2 本が落ちる)。

## 5. byte-check([byte_check.json](byte_check.json))

- 手順: HEAD(当時 `120d147`・今の `bbe7e77` と src・tests は同じ)を `git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28` で OS の一時ディレクトリへ展開した写しと作業木で、19 構成を mock/classical 5,000 体・seed 1・1 シミュ日・テープつきで回した([byte_check_10b.py](byte_check_10b.py)。比べ方は wave2 の `compare` と同じ)。
- 結果: **19/19 一致**(final・呼数・blocks・calls の 14 列)・`src_checks` ok。

| 構成 | final | 呼数 |
|---|---|---|
| w6_v3_default(golden v3) | 993276d5e5bb5cbe | 69,978 |
| w6_golden_null_arm(帰無) | 72cb9cd52982da74 | 100,439 |
| v3_mem_rel(関係 on) | 40409ebed834126b | 72,930 |
| v3_classical | 3390e3ec02d392a9 | 97,563 |
| ほか 15 構成 | [byte_check.json](byte_check.json) | |

- classical 1,500 体の golden(`4f78f3c0`/25,808)は既存のテスト `tests/engine/test_classical_social.py` で一致(§7 の回帰の組)。
- 注意(手順): 写しを深い場所(作業用の一時ディレクトリの奥)に置くと、numba のキャッシュのファイル名が Windows のパスの長さの上限を超えて HEAD 側のランが落ちた。短い場所に置き直して回した。

```
D=docs/bench/analysis/wallbounce-1003/10b
python $D/byte_check_10b.py side --src <写しの src> --label head --scratch <作業用> --out <作業用>/head.json --jobs 3
python $D/byte_check_10b.py side --label work --scratch <作業用> --out <作業用>/work.json --jobs 3
python $D/byte_check_10b.py compare --head <作業用>/head.json --work <作業用>/work.json --head-label 120d147 --out $D/byte_check.json
```

## 6. 揺らし試験(T5)と T1 の準備

- 形: 各 tick の頭で `resolve.advance_body` の**直後**に、対象の列を乱数・最小値・最大値の順で上書きする(浮動小数は正規乱数×10⁶・±10³⁰)。知覚 SoA と world の参照は最初の checkpoint で控え、tick 360 以降に揺らす。比べるのは behavior-hash(4 回)・呼数・行動の件数(`action_usage`)・起床の内訳(`calls_by_condition`)・テープの prompt_hash の列。
- **T5**(軸 1 が no/diag の 17 列を 37 tick ごと): 合成世界 100 体の全腕・古典+全腕、実資産 300 体の v3 既定(計画実行層・エネルギーつき=`plan_activity`・`energy_balance`・知覚 4 列も揺らした)で **全部一致**。今の final は動く(no の列が今の final に入るので=揺らしが効いた証拠)。陽性対照の `hunger` ではどれも動く。
- **`weight_kg` の扱い**: behavior(A2 b)だが読むのは初期化だけ。途中で揺らすと behavior-hash だけが動き、呼数・行動の件数・prompt_hash は動かない(テストで固定)。陽性対照には使えず、揺らしの対象(no/diag の列)にも入れない。
- **T1 の準備**(死蔵 5 列を tick 360 から毎 tick 乱数で埋める=列を無視するモード): v1・v3・v2+edge(注意の腕)・全腕・古典の 5 構成と実資産で、呼数・行動の件数・起床の内訳・prompt_hash・behavior-hash が動かない。削除そのものは 10e。
- 気づいたこと: 最初は揺らしを `advance_body` の**直前**に置いていて、実資産の `hunger` の陽性対照が動かなかった。energy の空腹の腕(CLI 既定)では `hunger` が毎 tick 体の値(`since_meal_kcal`)から作り直されるため(問 6)。

## 7. テスト

`tests/engine/test_state_ledger_10b.py`(27 関数・パラメータ込み 45 件・**全部合格**・約 3 分)。回帰の組(`test_census_out`・`test_cli*`・`test_two_layer_activity`・`test_sim_time_T`・`test_10a_review_fixes`・`test_fleet_wiring`・`test_determinism_t1_t2_t4`・`test_classical_social`・`test_presence_executor`・`test_memory_record`・`test_conversation_invite`・`test_ledger_wiring`・`test_meal_bundle_2b`・`tests/perception`)も合格。全体のテストは親が回す。

## 8. 保留の組の形(① の前提)

- `(t_apply, class, agent, condition, text, action_code, target_person, target_hint, target_poi, activity, target, **fire_tick**, **call_id**)` の 13 要素。`fire_tick` は応答の `tick`(発射の tick)、`call_id` は `"{fire_tick}:{agent}:{wake_class}"`(`LLMBridge.call`・艦隊の発射と同じ式)。5 か所の追加口(mock・再生の到着・艦隊の到着・艦隊の終端の drain・再生の終端)すべてで `_call_ref(res)` を付ける。
- 読む側は無い(原因の欄は ①)。`_split_due` の差し替えで、適用の時点の全部の組が 13 要素・`fire_tick ≤ t_apply ≤ tick`・call_id が組の値と一致・テープの call_id 列に含まれ・呼ごとに一意であることを固定した。

## 9. 見つけた問い(10b-1 の時点・親の答えは §10)

1. **台帳の外の属性**([ledger_uncovered_attrs.json](ledger_uncovered_attrs.json)): 外の状態の行が指す持ち主のクラス 39 個の属性のうち、どの行の `items` にも無いものが 641 個ある。大半は設定・参照・計数だが、tick をまたぐ状態らしいものが混ざる(例: 金の台帳 `_foreign_cash`・`_flow`・`_snap0`・`_last_close`/物の台帳 `_shelf_age`・`_inflow`・`_outflow`・`_residual`・`_open_stock`/`CrowdProcess.occupancy`・`queue_len`・`seats`/`SalientProcess.events`・`noticed_agents`/`StreetCleaningProcess._cursor`/`PlanExecutor.managed`・`home_out`・`line_of_agent`/`ConversationManager._pair`/`EnvironmentProcess.daylight`・`heat_stage`・`wbgt`/`RailProcess.enter_tick`)。full-hash は材料の 65 行の範囲だけを見ているので、再開(10d)の前に分類して行に足すか決めたい。実行役は表を写す指示なので足していない。
2. **full-hash の SoA の範囲**: 指示は「SoA 全列+…」、アジェンダ §2-3 は「要る・導出できるの行だけ」。軸 2 の規則を SoA にも当て、discardable の SoA 列(死蔵 5 列+知覚の `invocation_distance`)を外した(10e で死蔵の列を消しても full-hash が動かない)。死蔵の列は値が初期値のままなので検出力は変わらない。逆にするなら 1 行の変更。
3. **behavior-hash に外の状態を入れるか**: 今は今の final と同じ組み立てで、外の状態は活動と意図(O1・O4)だけ。軸 1 が behavior の外の状態(O7 `prev_cell`・O39 会話の管理・O42 アービタ・O46 乱数 など 32 行)は behavior-hash に入っていない(full-hash には入る)。10e で final を behavior-hash に切り替えるとき、これらを入れるかは決定が要る(入れると 10b の記録値とは一致しなくなる)。
4. **材料で軸 2 が 2 つ書かれた行の判定**(実行役の判断・expedient): O2・O23・O24・O55・O63 は行を derivable にしてキャッシュ・計数・関数の属性を `hash_skip` に入れた。O26 は「キャッシュは作り直しで空・計数は捨てる」なので discardable に寄せた。O55 で full に入れたのは `last_mile._cum`・`traffic.cell_hourly`・`delivery_inbound.delay_minute` の 3 つ(どれが「日ごとの場と遅れの表」かは実行役の読み)。
5. **full-hash の費用の上限**: 既定 5,000 体で 1 日 85.8 ms(今の 5.0 ms の約 17 倍)、39 万体の線形の外挿で 6.7 s/日(推測)。75% は会話の管理(O39)の Python の辞書と dataclass の直列化。T7 の「宣言の上限」はまだ無いので、上限の値と、超えるなら O39 を配列の形で持つか(10d の直列化の形と一体)を決めたい。
6. **`hunger` の軸 2**: energy の空腹の腕(CLI 既定)では、`hunger` は毎 tick `advance_body` で体の値から作り直される(揺らしを直前に置くと消えた)。この構成では実質「導出できる」で、表の「要る」は v1 の空腹の腕のときの値。構成で軸 2 が変わる列の書き方(今の表は 1 値)を決めたい。

## 10. 親の答えの反映(10b-2)

### 10-1 答えと実施

| 問 | 親の答え | 実施 |
|---|---|---|
| 1 台帳の外の属性 | 10b で潰す。(i) 状態は行を足す・(ii) キャッシュ・導出/(iii) 定数・設定/(iv) 参照は理由つきの除外の一覧へ。未カバーが 1 つでも残ればテストが落ちる | 持ち主のクラスを 46 に広げ(材料の 39+`WorldProcessRunner`・`ActualLog`・`UndefinedActionRegistry`・`Renderer`・`LLMBridge`・`TapeWriter`・`FleetBridge`)、属性 1,010 個を全部分類した。行を 24 本足し(O66〜O89)、見出しが「ほか」「計数」・リングの行には属性を足した(O19・O33・O34・O41・O53・O58・O60)。除外の一覧 `EXCLUDED` は 111 項・490 属性(キャッシュ・導出 127・定数・設定 257・参照 106)。検査 `state_ledger_ast.coverage` で**未カバー 0・食い違い 0** |
| 2 SoA の軸 2 | 今の形(required/derivable だけ)でよい | 変更なし |
| 3 behavior-hash に外の状態 | 軸 1 が behavior の行も入れる | `behavior_hash` の末尾に外の状態の behavior の行(88 本の属性)の digest を足した。final は不変 |
| 4 2 つの値の 6 行 | 今の形でよい | 変更なし(理由は §9 の問 4) |
| 5 T7 の上限 | 5,000 体で 1 回の 2 本の合計 ≤ 100 ms・39 万体で 1 日 ≤ 10 s | テストで固定(5,000 体)。会話の管理の辞書を配列で流す速い道と、2 本で同じ属性を 2 度直列化しない控え(memo)を入れた |
| 6 `hunger` の軸 2 | 構成で変わる印 | 行の欄 `restore_by_config` を足し、`hunger` に `("hunger_model=energy", derivable)`。既定は required・full には入れる |

### 10-2 足した行(O66〜O89)

| 行 | 中身 | 軸 1 | 軸 2 |
|---|---|---|---|
| O74 | `RailProcess.arrival_train`・`external_line`(帰りの便の予約印・域外居住者の路線。乗車と帰着で書き換える) | behavior | required |
| O79 | `GoodsLedger._shelf_age`・`_household_sku`(廃棄の判定・世帯の在庫=消費の可否) | behavior | required |
| O76 | `EnvironmentProcess.daylight`・`heat_stage`・`wbgt`(5 分刻みで気象の行から作り直すが、更新の間も読まれる) | behavior | derivable |
| O75 | `CrowdProcess.occupancy`・`queue_len`・`flow`・`flow_dir8`・`coherence` | behavior | **unknown** |
| O77 | 金の台帳 `_flow`・`_last_change_day`・`_snap0`・`_last_close`(センサスと保存則の項) | diag | required |
| O80 | 物の台帳の保存則の項(`_row_sku`・`_waste_sku`・`_inflow`・`_outflow`・`_residual`・`_open_stock`・廃棄の g・`_last_close`) | diag | required |
| O82 | `UndefinedActionRegistry.proposals`・`vocabulary_extension`・`_agents` | no | **unknown** |
| O85・O88 | `LLMBridge._interned`・`FleetBridge._interned`(テープの共有ブロックを 1 回だけ書く印) | no | **unknown** |
| O87 | `TapeWriter` の書き出し待ちの行と計数 | no | discardable |
| O66〜O73・O78・O81・O83・O84・O86・O89 | 計数(活動層・親しみ・店の選び・古典・計画実行層・アービタ・顕著行為・世界の過程と実行器・金と物の台帳・未定義行動・描画・橋・艦隊) | diag | discardable |

既存の行に足した属性: O19 に `init_audit`・`wall`/O33 に範囲外の食事の計数 2 本/O34 に群の計器の計数 23 本/O41 に会話の管理の計数 14 本/O53 に `StreetCleaningProcess._cursor`/O58 に金の生ログのリングの残り 10 本/O60 に配達ログのリングの残り 8 本。

**「不明」(軸 2 が unknown・full-hash には入る)の一覧**: `agents.fail_streak`・`agents.plan_activity`(K15)・O75 混雑の場(毎 tick の step で SoA から作り直すが、作り直す前に読む口があるか未確認)・O82 未定義行動の提案と語彙の拡張(run_day は裁定器なし=起きない見込み・起きれば解析に効く)・O85/O88 テープの共有ブロックの印(同じテープに続けて書く再開なら要る)。

除外の判断で注意したもの: `SalientProcess.events`・`cell_lines`・`noticed_agents` は step の頭で空に戻す(キャッシュ)/`RelationLayer._acq_pending`・`_hits` は tick の中で使い切る/`TrafficProcess.hour` は場を作り直した印(−1 に戻すと同じ時の場を作り直す)/金と物の台帳の `_depth` は書き込み窓の入れ子(checkpoint では 0)/`Renderer._focus_target` は `agents.focus_target` のビュー/`EnergyLayer.meal_reset` は O21 と同じ配列。属性の列挙は `self.x = …`・`self.x += …`・`self.x[...] = …` とクラスの欄(添字や呼び出しの中の `self._pair(...)` のようなメソッドは数えない)。

### 10-3 新しい behavior-hash(10e で比べる値・§4-1 を置き換える)

| 構成 | final(不変) | behavior-hash(全桁) | full-hash |
|---|---|---|---|
| w6_v3_default(golden v3) | `993276d5e5bb5cbe` | `b315f03ad68b68c613caf61327d1256fb17d558f1d5676f7095f700052832a92` | `65fac29b7eba7724…` |
| w6_golden_null_arm(帰無) | `72cb9cd52982da74` | `3bd18625ff3d923ee776052cc8255fbe3f672f16de452f6cbdb7ffca1327bb52` | `0056a6cf66754f8c…` |
| v3_mem_rel(関係 on) | `40409ebed834126b` | `70089de493a21d4160e3a26aa3bbae215170dbd09176d9de5be3c9a9b1a99210` | `43da521085fb48b5…` |

[byte_check_after_answers.json](byte_check_after_answers.json)(checkpoint ごとの値もここ)。[byte_check.json](byte_check.json) の `state_hashes_10b` は 10b-1 の定義の値で、置き換わった(final・呼数・blocks・calls の 19/19 一致の記録としてはそのまま有効)。full-hash の定義も、属性ごとに digest を取ってから束ねる形に変わった(memo のため)。

10e の手順(書き直し): 死蔵 5 列を宣言から消し、final を `state_hashes.behavior_hash`(SoA は残る no/diag の列を `exclude`・末尾に外の状態の behavior の行の digest)に切り替え、上の 3 構成(と残りの 16 構成)で 10e の final が 10b の behavior-hash の全桁と一致することを確かめる。一致の根拠のテスト `test_t2_behavior_hash_equals_the_final_after_deleting_the_non_behavior_columns` を、外の状態の digest を末尾に足す形に直した。

### 10-4 byte-check(3 本)

HEAD(`bbe7e77`・src と tests は `120d147` と同じ)の写しの値と作業木: w6_v3_default `993276d5e5bb5cbe`/69,978・w6_golden_null_arm `72cb9cd52982da74`/100,439・v3_mem_rel `40409ebed834126b`/72,930 で final・呼数・blocks・calls の 14 列が **3/3 一致**(`ALL_OK`・[byte_check_after_answers.json](byte_check_after_answers.json))。HEAD 側は 10b-1 で回した [byte_check.json](byte_check.json) の同じ 3 行。

### 10-5 費用(T7)

[hash_cost_v3_5000.json](hash_cost_v3_5000.json)(既定 v3・5,000 体・この機械・中央値): 1 回の checkpoint で 2 本の合計(run_day の形=memo つき)**14.6 ms**(上限 100 ms)。単独では behavior 10.8 ms・full 12.3 ms。O39 会話の管理は 22.5 ms → 3.2 ms(鍵が整数の組・値が整数の辞書を numpy の配列 2 本で流す速い道=`_feed_int_table`。型が混ざれば普通の道)。1 日 4 回の checkpoint の時間(final を含む)は 85.8 ms → 48.9 ms。39 万体への線形の外挿は 1 日 3.8 s(上限 10 s・推測)。byte-check の 3 本では作業木の checkpoint の 1 日の合計が 39〜157 ms(並列 3 本の負荷つき)。

### 10-6 テスト

`tests/engine/test_state_ledger_10b.py` は 34 関数・パラメータ込み 52 件・全部合格(T7 の 5,000 体のランを含め約 4 分)。足したもの: 持ち主のクラスの属性の網羅(未カバー 0)/除外を 1 項外す・クラスに属性を足す・除外した属性を消すと失敗/`hunger` の構成の印/behavior-hash に入る外の状態の行/速い道の正準性/memo で値が変わらない/T7(5,000 体で 1 回 ≤ 100 ms)。T4 は外の状態の behavior の行で behavior-hash も動くこと、no/diag の行(`waste_g_collected`・金の `_flow`)では full だけが動くこと、不明の行(混雑の場)で両方動くことに直した。回帰の組(§7 と同じ)も合格。

## 11. 検収後の直し(10b-3・[検収](../review-10b.md))

### 11-1 潜在の欠陥

| # | 直したこと |
|---|---|
| P1(2-1) 辞書の挿入順 | 行の欄 `ordered` を足し、**O8**(記憶の要旨 `_gist_order`=`OrderedDict`・`popitem(last=False)` で古い順に落とす `memory.py:585-590`)と **O39**(会話の管理 `sessions`・`pending_invites` の走査の順が話し手と被招待の起床の順 `conversation.py:617,627`)に印。印の行の辞書は挿入順のまま(印 `W`・速い道は `U`)、`collections.OrderedDict` は印が無くても挿入順。印の無い辞書は今までどおり鍵の昇順 |
| P2(2-2) 締めの後 | `runner.end_of_day`・`ledger.end_of_day`(とセンサス)の後にもう 1 回 2 本を計算し、`RunResult.state_hashes_end_of_day` と manifest の `state_hashes_end_of_day` に出す(final も checkpoint の位置も不変)。**10d はこちらを使う**。台帳の無い合成世界では最後の checkpoint と同じ値、実資産では締めで台帳の日番号・当日の売れ行き・センサスの項が変わるので違う値 |
| P3(2-3) 期限つきの辞書 | **直していない**(§11-3) |
| P4(2-4) numpy の整数 | 速い道の判定を `numbers.Integral`(`bool`・`np.bool_` を除く)にし、値を `int()` で取り直して流す。`{1: 2}` と `{np.int64(1): np.int64(2)}` は同じバイト列。int64 に収まらない整数は普通の道 |
| P5(2-5) AST の死角 | (i) SoA らしい持ち主への `getattr(持ち主, 変数)` は名前の表で解決できなければ「解決できない動的な読み」=失敗(許可の一覧に足したのは自分の `state_hashes.py` の dataclass の欄の読み 1 か所・理由つき。src の他の 15 か所は SoA の持ち主ではないので当たらない)(ii) `X.arrays.get("c")` (iii) `operator.attrgetter("c")` は読みに数える (iv) 自己更新は「左辺と同じ列の右辺の読み」だけを外す(組の代入は要素を対にして見る)。検収の表の 5 つの書き方は全部捕まり、本当の自己更新 4 通りは読みに数えない(テスト) |
| P6(2-6) 実行時の網羅 | `state_ledger_ast.runtime_uncovered(owners)`: 各持ち主のインスタンスの `vars()` と `__slots__` を台帳+除外に突き合わせる。合成の全腕・古典、実資産 200 体の v3 既定と全腕+古典で未カバー 0。構成で入れ替わるクラス `OWNER_ALT_CLASSES`(`poi_resolver.chooser`=`NearestChooser`・`ledger.money`=`cli._HouseholdWalletLedger`)を AST の網羅にも足し、`wallets`(初期の財布=定数)を除外に足した |

**順序の洗い出し**(full と behavior に入る属性の、走査・`popitem`・`next(iter(...))`・`sorted`・`list` の箇所を grep した結果):

| 属性 | 使い方 | 判定 |
|---|---|---|
| `mem_layer._gist_order` | `OrderedDict` の `popitem(last=False)` | 順が挙動=**O8 に印** |
| `conv.sessions`・`conv.pending_invites` | `.values()`・`.items()` を回して話し手・被招待を並べる | 順が挙動=**O39 に印** |
| `conv._refusal_until`・`_pair_invite_until`・`_speaker_invite_until`・`_of_agent` | 鍵で引くだけ | 順は挙動に効かない(O39 の印で順も入る=安全側) |
| `intent_layer._payload` | 控えの掃除で回して消す(全部消すので順に依らない)・`state_hash` は `sorted` | 印なし |
| `ledger.money._lines` | `.items()` で足し合わせ(順に依らない) | 印なし |
| `undefined.proposals` | `.values()` で数えるだけ | 印なし |
| `run_day.replay_inbox` | `pop(tick)`・`sorted` | 印なし |
| `runner.rail._return_queue`・`presence._extra` | `pop(鍵)` だけ(値の list は順を持つ) | 印なし |
| `mem_layer.gist`・`_session_key` | 鍵で引くだけ | O8 の印で順も入る(安全側) |

### 11-2 記録の誤り

- R1: 除外の分類「キャッシュ」の説明を `state_ledger.py` で 3 通りに書き分けた((a) 毎 tick(か事象のある tick)作り直す作業の値・印 (b) 中身で引く覚え書き=ラン中残るが空から始めても同じ鍵で同じ値を作り直す (c) 資産・母集団・予定の表から初期化で作る表)。除外の判断は変えていない。覚え書きの側(`act_layer._digest_cache`・`renderer._b1_cache`〜・`poi_resolver._cat_mask_cache`)は行の `hash_skip`・O26 で扱っている。
- R2: 基準の書き方を「HEAD `bbe7e77`(src と tests は `120d147` と同じ)」に直した(§0・§5・§10-4)。
- R3: §0 を 10b-3 の数に直し、10b-1 の結論は §12 に移した。

### 11-3 10e へ送るもの

- **会話の管理の期限つきの辞書 3 つ**(`_refusal_until`・`_pair_invite_until`・`_speaker_invite_until`)は期限切れの項を消さず、日数に比例して増える(検収の再現: 合成 2,000 体・3 日で O39 の直列化 2,291 B → 253,229 B)。消すと behavior-hash も full-hash も変わるので、10e の版上げに束ねる。それまで **full-hash と再開の状態の大きさは日数に比例して増える**(宣言)。期限切れの項は挙動では「無い」と同じなので、10d の復元が期限切れを落とすと full-hash が食い違う点にも注意(10e で掃除を入れてから 10d の判定に使う)。

### 11-4 親の答え(問い 5-1〜5-4)

- 5-1: P2 のとおり(締めの後の 2 本を別に出す)。
- 5-2: O37 `_pulled_in_today` は behavior-hash に入れたまま。**behavior-hash は挙動の等価の確認用で、再開の判定には使わない**(10d の判定は締めの後の full-hash。O37 は軸 2 が discardable なので full には入らない)。
- 5-4 **金の生ログの溢れは日次センサスの金の項に効かない**: センサスと締めが読むのは取引行列 `_flow`(`Ledger._post` が取引ごとに足す・`economy/ledger.py:657`)と残高のスナップショットで、生ログの輪(`_raw_*`)は `_record` が書くだけ。輪を読む口 `Ledger.raw_rows()` は src に呼び手が無く(tests/economy だけ)、締めの `DayClose.raw_rows_kept` と `n_raw_dropped` も src の他所からは読まれない。だから落ちた 3,978 行は、輪から取引の行を読み出す使い手(① の出来事の記録)にだけ効く(K17 の材料)。

### 11-5 新しい値(10e で比べる値・§10-3 を置き換える)

| 構成 | final(不変) | behavior-hash(最後の checkpoint・全桁) | full-hash | 締めの後 behavior-hash(全桁) | 締めの後 full-hash |
|---|---|---|---|---|---|
| w6_v3_default | `993276d5e5bb5cbe` | `535b040a2fcc54117f0c0e6972ab790096261cf20e2b50a4599afa11ad8110de` | `0e64a658ddb8a2ee…` | `8730ff33fa5eab1aa9227d82a8b0e39aff2aeb1d7953562b77e11dcec33a5750` | `1e2426f4dc74e947…` |
| w6_golden_null_arm | `72cb9cd52982da74` | `aee7c77d4b78636d83dc754eb78c0b82aae85fb5bef34019dc95383bf9862e7b` | `11dcb05bcb25b041…` | `dae2c163d95d7d2987246539abdae94ea790d7ae96f48284c977307982aa2789` | `10c869e4838ce157…` |
| v3_mem_rel | `40409ebed834126b` | `20240d0eae4f8db757ce2a211d0d46bf66d8784f3f5c7b9657000901021820af` | `429ed43bdfd14cd9…` | `4b2a9226c719ba16f2c8f235b0f35102b5f8af4748908afc0acc93f0c3a6e0b1` | `4f0d9da96c65387a…` |

behavior-hash が 10b-2 から変わったのは、O8・O39 の順を入れたことと、速い道の印の付け方(`U`/`Q`)が変わったため。10e で比べるのは最後の checkpoint の behavior-hash(final の切り替えの検算)で、10d の再開の判定は締めの後の full-hash。[byte_check_after_review.json](byte_check_after_review.json)(checkpoint ごとの値と checkpoint ごとの最大の時間も)。

### 11-6 テスト

- 足したもの(10b-3): 順の印(OrderedDict と印の無い dict・印つきの行の並びを逆にすると full が動く)/numpy の整数の速い道/AST の死角 5 つ+本当の自己更新 4 つ/実行時の網羅(4 構成・属性を 1 つ足すと落ちる・子クラスと入れ替わるクラスが実際に入っている)/締めの後の 2 本(合成では最後の checkpoint と同じ・実資産では違い決定論)/call_id の 4 つの道(艦隊の到着・艦隊の終端の drain・再生の到着・再生の終端。艦隊の結果の `call_id` と式の値の一致)/T1 の準備の陽性対照(死蔵の列を揺らすと final が動く)/T7 を checkpoint ごとの最大で既定 v3 と全腕の 2 構成。
- 結果: 44 関数・70 件・全部合格。回帰の組(`test_census_out`・`test_cli`・`test_cli_l4_scale`・`test_cli_vocab_version`・`test_two_layer_activity`・`test_sim_time_T`・`test_10a_review_fixes`・`test_fleet_wiring`・`test_tape_deferred`・`test_tape_wiring`・`test_response_delay`・`test_determinism_t1_t2_t4`・`test_classical_social`・`test_presence_executor`・`test_memory_record`・`test_conversation_invite`・`test_ledger_wiring`・`test_meal_bundle_2b`・`tests/perception`)も合格。途中で AST の検査が自分の直列化の書き手の行の変更(`ordered` の引数)を「古い許可」として捕まえたので、許可の文字列を直した。

### 11-7 費用

[hash_cost_v3_5000.json](hash_cost_v3_5000.json): 2 本の合計(memo つき)1 回 12.0 ms・O39 は 7.7 ms(順を保つ道で並べ替えをしなくなった代わりに、sessions などを普通の道で流す)。checkpoint ごとの時間(final を含む): 既定 v3 [7.0, 9.1, 12.0, 13.4] ms・全腕(記憶・関係・店の記憶・親しみ・エネルギー・自宅の食事・就寝中の食事。古典は含めない)[19.5, 25.3, 29.5, 39.3] ms。

## 12. 経緯(10b-1 の結論・当時の値)


> **10b-2(親の答えの反映)で変わった点は §10**。台帳は 187 行・除外の一覧 111 項 490 属性・behavior-hash に外の状態の behavior の行を足した(値が変わった)・費用は 1 回 14.6 ms。下の §0〜§9 は 10b-1 の時点の記録で、§10 と食い違うところは §10 が正。


1. **既定の結果は動いていない**。HEAD `120d147` の `git archive` の写しと作業木で 19 構成(W6 再生成の 15 腕+店の記憶・関係・古典・古典+記憶+関係)を mock/classical 5,000 体・1 シミュ日・テープつきで回し、final・呼数・blocks・calls の 14 列(prompt_hash を含む)が **19/19 一致**([byte_check.json](byte_check.json)・§5)。classical 1,500 体の golden `4f78f3c0`/25,808 は既存のテスト `tests/engine/test_classical_social.py` で確かめた(§5)。
2. **状態台帳は 163 行の機械可読の表 1 つ**(`engine/state_ledger.py` の `LEDGER`)。SoA 98 列(agents 79・cells 5・pois 9・知覚 5)+外の状態 65 行(O1〜O65)。表と実際の SoA の列名・型・バイトはテストで一致を固定した。
3. **追加 C の AST の検査は今の src で合格**(違反 0)。軸 1 が no/diag の列の読み手は 6 か所あり、どれも根拠つきの許可(材料 §2-4 の誤検出 2 列=`band`・`b4_hash` を含む)。わざと `hunger`・`fatigue`(名前の表経由)を no にすると失敗し、一時変数・名前の表・直書きの組・文字列の読みを足しても失敗する(T3)。
4. **behavior-hash と full-hash を checkpoint ごとに出す**(`Checkpoint.behavior_hash`・`full_hash`・manifest の `state_hashes`・`--checkpoints-out` の JSON)。final(`combined`)には混ぜない。費用は既定 v3 5,000 体で checkpoint 4 回の合計 5.0 ms → 85.8 ms(behavior は 1 回 0.5 ms・full は 1 回 30 ms で、その 75% が会話の管理 O39 の直列化)。
5. **揺らし試験(T5)**: 軸 1 が no/diag の 17 列をランの途中で乱数と端の値で揺らしても、behavior-hash・呼数・行動の件数・起床の内訳・prompt_hash の列は 1 つも動かない(合成世界の全腕・古典、実資産 300 体)。陽性対照の `hunger` では動く。死蔵 5 列を毎 tick 乱数で埋める T1 の準備も 5 構成で動かない。
6. **保留の組は 13 要素**(末尾に発射の tick と call_id)。適用の時点で call_id が引け、テープの call_id 列に全部ある(テストで固定)。
7. **止めた問いは 6 件**(§8)。いちばん大きいのは「材料の 65 行が指す属性の外に、持ち主のクラスの属性が 641 個ある(設定・計数が大半だが、状態らしいものが混ざる)=full-hash の網羅は材料の表の範囲まで」(問 1)。

