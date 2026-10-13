# 1-0 run_day の分解(結果不変)の実装の記録

- 実装役 Opus 5.5。作業木 `1-0/run-day-decomp`(HEAD `ee3abc7`)。commit は親。設計の正: [草案](../../../../design/v2-run-day-decomposition-draft.md)(受入・ユーザー承認 2026-10-13)。
- 数は実測。「推測」=確かめていない読み。生の出力(大きい JSON・テープ)は git の外の `data/runs/1-0_*` に置いた。
- 道具はこのフォルダ: `probe_run.py`(系ごとの差と指紋・HEAD と 1-0)・`local_assignment.py`(局所の割り当ての表)・`multi_writers.py`(複数の系が書く列)・`guard_runs.py`(書きの検査の正と負)・`resume_19x2.py`(再開の 19×2)・`manifest_check_1_0.py`(manifest)・`arms_check.py`(19 構成に無い腕)。

## 0. 結論

- `run_day` は署名と説明(HEAD のまま)+本体 4 行(`_call_args = dict(locals())` → `conduct(_call_args)`)になった。組み立て・tick のループ・ランの終わりは `engine/systems/` の 25 個のモジュール(系 31 個の宣言の表・状態の箱・進行役・書きの検査・系ごとの差の測り)。`engine/run.py` は 5,188 行 → 2,484 行。
- **結果不変**: byte-check 19 構成(5,000 体・seed 1・1 日・テープつき)の全 25 欄・2 日のラン(final `912446bd2b42b6ab`・140,913 呼・テープの中身)・再開の 19×2(38 本とも checkpoint の全点・呼数・final)・manifest 7 本(環境の 5 欄=git の commit と汚れ・env_id を除く全欄と鍵の集合)・19 構成に無い腕 12 本が HEAD と同じ。**系ごとの指紋**(1,000 体・全 tick・6 構成)は全部の系・全部の tick で HEAD と同じ(2 構成は文字列のハッシュの種を両側で固定したとき=HEAD からある並びの揺れ・§3-3)。
- 「宣言の外を書いたら落ちる」は既定で入る(段 A ①②=実行時の SoA・段 C=scratch・段 D=pytest の AST・段 B=試験のときの全欄の差)。負の対照 12 本(世界資産 1,000 体)はどれも書いた行で落ちた(§3-4)。T5 で閉包の漏れ 1 つ(close_final の計画の印)と持ち主をまたぐ別名の書き 1 つ(食事で古典の門の H)を見つけて宣言に足した(§3-5・§3-6)。
- 複数の系が書く列の一覧(ユーザーの条件): [multi-writer-columns.md](multi-writer-columns.md)(SoA で 2 系以上=観測 33・宣言 56・外の状態の行=観測 30〔段 FIX の後は 32〕)。
- 段は A → CB → DEF の 3 つにした(草案の A〜F の 6 段から変えた=§1-1)。
- **〔段 FIX〕** 独立の検収([review-impl-1-0.md](review-impl-1-0.md)・条件つき受入)の §1 の 1〜10 を直した(§7)。外の状態の行の観測は 30 → 32(段 FIX の測りを足した・`O61`・`O63`)。

## 1. 段と門

| 段 | 中身 | スナップショット | byte-check 19 構成(HEAD と全欄) | 全体の pytest |
|---|---|---|---|---|
| A | 書きの許可・配列単位の `_require_thawed`・静的な検査 D④〜⑦・閉包の道具・系ごとの差の測り | `scratchpad/331/snap_A`(13 ファイル) | 19/19 同じ(門 A1・A2) | A2: 3,855 passed・1 failed(既知=下) |
| CB | 状態の箱・局所の割り当ての表・束縛し直す名前を箱へ・読むだけの系(observe・checkpoint・report)・宣言の表と進行役の口 | `snap_CB`(31) | 19/19 同じ(門 CB1) | 3,863 passed・1 failed(既知) |
| DEF | 書く系の全部(tick の系・日の境目・ランの終わり)・組み立て・進行役のループ・run.py の import の整理・試験の付け替え・T1〜T5 | `snap_DEF`(累積) | 19/19 同じ(門 DEF1・DEF2) | DEF1: 3,942 passed・5 failed → 4 件を直した(§3-5)→ DEF2: 3,946 passed・1 failed(既知) |

- 門は「HEAD + 段のスナップショット」の写し(作業木の隣の置き場 `wt1_0_gate/<名>`)で回した(作業木の編集と並べるため)。byte-check の HEAD の側は本体の src(`ee3abc7` と同じ中身)。
- 既知の 1 件 `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` は、写し(と作業木)の `data` が本体への junction であることによる道筋の落ち=10e の親検収の記録の「作業木で落ちた既知のテープの道筋の 1 件(本体では通る)」と同じ。

### 1-1. 草案と違えた段の順と切り方

- **A → C → B**(草案は A → B → C): B の系は箱を引数に取る口で切るので、箱(C)を先に作った。C と B は 1 つの段 CB にした。
- **D・E・F を 1 つの段 DEF にした**: D と E の間・E と F の間の状態は「run_day に残った区間と系の間の受け渡しの糊」を持つ仮の形で、糊は次の段で消える。中間の状態では quick(500 体・2 日・5 構成=v3・golden・記憶+関係+店+同席・古典+記憶+関係・v2 edge)の final と呼数が HEAD と同じことだけを確かめ、全体の門(byte-check 19・pytest・指紋)は DEF の最後の状態で回した。D・E の中間のスナップショットは作っていない(要るなら `scratchpad/331/gen_systems.py`・`apply_systems.py` と `run_before_D.py`・`run_before_E.py` から機械で作れる)。
- A1 の落ち 5 件のうち 4 件は段 A の中の不足(probe の `View.stats` が外の状態の属性の名と衝突・`_require_thawed(world, world.pois.revenue)` が軸 1 diag の列の読みに数えられた・probe の `getattr(v, f.name)` が解決できない読み)。直したものを `snap_A` にした(門 A2)。

## 2. 作ったもの(最後の状態)

### 2-1. 状態の箱(草案 §2-3)

`engine/systems/boxes.py`: `RunConfig`(凍結・85 欄)・`SoAState`・`Layers`(持ち主 19 個+導く 2 個=`undefined`・`run_day`。名は HEAD の `_hash_owners` の鍵・順も同じ)・`LlmIo`・`DayTables`・`Buffers`(`focus_request`・tick の頭で空にしない=R1)・`TickScratch`(34 欄・`__setattr__` で系の宣言の外の欄を落とす=段 C)・`TickScratchStrict`(番兵=T4)・`RunStats`・`Fixtures`・`Box`・`TickCtx`。

〔草案と違えた点〕
1. `Fixtures` を足した(組み立てで作り読むだけの物 12: 暦・日課・週次表・資源の空間・幾何・描画の口・艦隊ほか)。
2. `prev_sessions`・`prev_tape_misses` は `LlmIo` でなく `RunStats` に置いた(どちらも診断の行の差分の基準)。
3. **名の衝突を避けた改名**(状態台帳の外の軸 1 の AST は、外の状態の行の属性の名と同じ名の属性を持つクラスを「衝突」として扱い、衝突の表に足すと持ち主を指さない受け手の読みが全部素通りになる=検査が弱まる。なので名を変えた): `Box.stats` → `Box.runstats`・`RunStats.sleep_counts` → `sleep_tally`・probe の `View.stats` → `View.tally`・`Access.stats` → `Access.tally`・`SystemSpec.slot` → `timing`(O29 の `energy.out_of_area.slot`)・scratch の `d_agent/d_cond/d_class` → `det_*`(O30)・`n_parse_errors` → `parse_errors`(O86)。系の関数の中の局所の名は HEAD のまま(箱の欄の名だけ違う)。

局所の割り当ての表 [local-assignment.json](local-assignment.json)(`local_assignment.py`): HEAD の run_day の局所 450 個(引数 113 を含む)に**割り当て無し 0**(段 C の門・試験 `test_boxes.py`)。内訳: 箱の欄 199(cfg 85・soa 2・layers 19・llm 5・day 6・buffers 1・scratch 34・stats 35・fx 12)・組み立ての局所 105・系の局所 86・同じ名の別の一時 16(`t0`・`i`・`k` など。系ごとに別の束縛で、読む系はどれも先に書く)・ランの終わりの系の局所 26・入れ子の関数 16(`state_io`・`llm_io` の関数へ)・時刻 2(`TickCtx`)。

### 2-2. 系と表(草案 §2-2・§2-5)

- `engine/systems/table.py` の `SYSTEMS`(呼ぶ順の 1 つの表・31 個): build(R1)・day_head(D1)・tick の中 25(body・world・presence・perceive_prepare・llm_receive・apply_responses・detect・plan_boundary・home_meal・wake_sources・wake_filter・relations_wake・wake_assemble・arbiter・decide・phase_a・phase_b・phase_c・conversation・activity_intent・memory・familiarity・energy_after・observe・checkpoint)・day_close(D2)・drain(R2)・close_final・report(R3)。群は名札(体・世界・知覚・判断・会話・行為の解決・記憶・計器・暦・組み立て)。
- 〔草案と違えた点〕最後の日の締め `close_final` を `day_close` と別の系にした(草案の擬似コード §2-4 の `DAY_CLOSE_FINAL` と同じ。§2-2 の表は D2 に「L24・E1 の締め」をまとめていた)。書く欄(最後の便を流す・result の欄)が違うため。
- `SystemSpec`(`spec.py`): name・group・timing・fn・reads(`box`=箱の属性の参照・`scratch`・`buffers`)・writes(`soa`=**resolve_ops の静的な閉包を `make` が機械で作る**・`paths`=`鍵:道筋`(`*` と `[...]` の型)・`scratch`・`buffers`・`tally`)・resolve_ops(手で書く表)・calls_llm・when・origin。
- `reads.box` は系のコードの静的な読みから道具(`static_check.py`)で下書きして表に書いた。`resolve_ops` は 6 構成の観測+層のメソッドの静的な到達(class の中の閉包)+読んだ経路から手で書いた。`writes.paths` は HEAD の系ごとの差の測り(6 構成・全 tick)と草案 §2-2 から手で書いた。
- 系の関数(`sys_<名>(ctx, b)`)は HEAD の区間の文をそのまま本体にし、外から来る名前を箱から結ぶ前置きと scratch へ書く後置きだけを足した(生成の道具 `scratchpad/331/gen_systems.py`)。`engine.run` で定義された補助(`_split_due`・`_call_ref` ほか)は呼ぶ時に `engine.run` から引く。
- 入れ子の関数: `_utter`・`_receive_arrivals` → `llm_io.utter`・`receive_arrivals`、状態と日の口 14 個 → `state_io`。描画と方策へ差し込む関数(`_classical_acq`・`_classical_partner`・`_session_partners`・`_b3_words`・無名関数 3 つ)は組み立て(`build.py`)の中の入れ子の def のまま(捕まえる物の同一性=草案 §3-3 の 6)。
- `llm_receive` は 1 つの系で、進行役が `response_delay` で位置を選ぶ(1=perceive_prepare の後・2=wake_sources の後)。HEAD は位置 A で 0 を入れ位置 B で受け取る形=同じ値。
- 世界過程 18 本は `world` の 1 つの系の中(下位の系の宣言は書いていない。world の宣言はその和)。

### 2-3. 進行役(草案 §2-4)

`conductor.py`: `conduct(_call_args)` = `build` → tick ごとに `TickCtx`・scratch を空に → 日の頭(`td == 0 and T > 0`)→ tick の系の並び(`tick_plan`=表の順・`when` で立たない系を外す・llm_receive の位置)→ 日の終わり(`td == tpd - 1 and T != total_ticks - 1`)→ drain・close_final・report。`run_system(spec, ctx, box)` が系ごとに試験の境目(probe)・書きの許可(guard)・系ごとの壁時計(`RunStats.system_seconds`。`phase` の鍵の集合は変えない=§3-3 の 22)を包む。`build` は守らない(箱が無い)。

### 2-4. 宣言の外を書いたら落ちる(草案 §2-6)

| 段 | 作ったもの | 既定 |
|---|---|---|
| A ① | `core/write_permit.py`(いまの系の許可)+解除口 `AgentState.thaw`・`World.thaw`・`PerceptionState._set_writeable` が許可の列だけを解く | 入れる(切替口 `SHIBUYA_WRITE_GUARD=off`・`write_permit.set_enabled(False)`) |
| A ② | `resolve._require_thawed(*objs)` が配列を渡されたら配列ごとに `flags.writeable` を見る。ufunc.at の 5 か所が書く配列を渡す | 入れる |
| C | `TickScratch.__setattr__`(`guard.SCRATCH_PERMIT`)〔段 FIX: `Buffers.__setattr__`(`guard.BUFFERS_PERMIT`)も=§7〕 | 入れる(同じ切替口) |
| D | `tests/engine/systems/test_stage_a_guard.py`(④⑤⑥⑦)・`test_systems_table.py`(①②③⑧・順・scratch の受け渡しの順)・`test_two_phase.py` の hot path に systems を足した | pytest |
| B | `probe.py`(系の境目ごとに全欄の digest・差を系に帰属)+`conductor.declared_check`。`SHIBUYA_SYSTEMS_CHECK=<間引き>` で既存の試験の上でも回る(T5) | 試験のときだけ |

### 2-5. 試験の付け替え(草案 §3-3 の 15)

- `full_state_hash` の差し替え(`test_state_ledger_10b`・`discard_probe`・`test_rng_scheme_10c`・`test_version_bump_10e`): 的を `engine.systems.state_io.full_state_hash` にした(checkpoint・日の締めの後・状態の書き出し・再開の検算がどれもこの名を通す)。差し替えが使われたことの確かめを足した(`test_version_bump_10e` の purge_runs・`test_state_ledger_10b` の揺らし)。
- 組み立ての名(`FleetBridge`・`PerceptionRendererAdapter`・`WorldProcessRunner`・`Arbiter`・`ConversationManager`・`MemoryLayer.enable_relations`): 的を `engine.systems.build` にした(`test_sim_time_T`・`test_fleet_wiring`・`test_renderer_wiring`・`test_10a_review_fixes`)。`test_response_delay` は `FleetBridge.submit` をクラスで差し替え。`test_10a_review_fixes` に差し替えが使われた確かめを足した。
- `_split_due`・`_call_ref`・`sample_population` は `engine.run` に残した(系は呼ぶ時に `engine.run` から引く)=試験はそのまま効く。`test_t2_call_id` の道の表は (ファイル, 行) にした(§3-5)。
- `engine/run.py` から使わなくなった import を外した〔段 FIX で訂正: 「104 個」は誤り。頂上の import 187 → 88=99 個・関数の中を含めた異なる名前 202 → 100=103 個=§7-1 の 10〕(古い的を突く差し替えは `monkeypatch.setattr` が AttributeError で落ちる=黙って通らない)。
- 状態台帳の AST の場所ごとの許可(`EXT_AST_ALLOW`・`_ALLOW_REVENUE`・`RESULT_FILES`)を系の置き場と関数名に付け替えた(弱めない=対象を広げる・当たる数と関数名は固定のまま)。

### 2-6. 危ない所 22(草案 §3-3)をどう潰したか

| # | 危ない所 | 1-0 での扱い | 確かめ |
|---|---|---|---|
| 1 | `pending` の束縛し直し | `LlmIo.pending` の欄。読み書きは使う時に `b.llm.pending` を引く。持ち主 `run_day` は `hash_owners` が呼ばれた時の `pending` で `_RunDayLocals` を作る(HEAD の遅い束縛と同じ) | 系ごとの指紋の O43 が全 tick で同じ |
| 2 | ハッシュに名が入る | 持ち主の名・順(`OWNER_NAMES`)・道筋・`_RunDayLocals` の置き場(`engine.run`)・状態に入る値のクラスはどれも動かしていない | `test_owner_names_match_the_hash_owners`・final/behavior/full の一致 |
| 3 | 設定の指紋 | `run_day` の署名と最初の文 `_call_args = dict(locals())` は HEAD のまま。組み立ては引数 113 個を全部 `_call_args` から結ぶ | `test_run_day_signature_is_unchanged_and_build_unpacks_every_argument`・再開の 19×2 |
| 4 | `prev_sessions`・`prev_tape_misses` | `RunStats` の欄(observe が書き、再開で build が戻す) | 系ごとの指紋の stats |
| 5 | `_relay_tables` の nonlocal | `DayTables` の欄(`state_io.relay_tables` が書く)。層が起動時に写した表はそのまま | 2 日のラン・v3 既定 2 日の指紋 |
| 6 | 差し込んだ関数 | 組み立て(`build`)の中の入れ子の def のまま | 古典+記憶+関係・記憶+関係の指紋 |
| 7 | `_utter` の 2 か所の呼び手 | `llm_io.utter(b, …)` を `receive_arrivals` と `decide` が呼ぶ | 艦隊・再生の試験(T5 の口つき) |
| 8・9 | 順の注がある所 | 表の順=HEAD の実行順(1 つも入れ替えない) | `test_order_and_counts`・指紋 |
| 10 | 2 つ以上先へ届く受け渡し | scratch の欄の書き手と読み手を宣言 | `test_scratch_is_written_before_it_is_read_in_tick_order` |
| 11 | 持ち主をまたぐ書き | world の `writes.paths` に O36・O37・O70・O74 を宣言(親の決め)。T5 で見つけた O21(§3-6)も同じ扱い | 段 B(6 構成・全 tick・12 腕で宣言の外 0) |
| 12 | 1 つの列の書き手が多い | [multi-writer-columns.md](multi-writer-columns.md) | — |
| 13 | 乱数と順 | 順を変えていない・`PROCESS_ORDER` に触れていない | 指紋 |
| 14 | 日の締めの 2 つの形 | `day_close`(途中・`flush_rail=False`)と `close_final`(最後)を別の系にした。止めたランの書き出しは `drain` の頭(HEAD と同じ位置) | 再開の 19×2・2 日のラン |
| 15 | 試験の差し替えの的 | §2-5 | 付け替えた試験の全部が通る・差し替えが使われた確かめ |
| 16 | 検査の表が run.py の名を持つ | 状態台帳の AST の許可・`RESULT_FILES`・`test_two_phase` の hot path を系の置き場へ広げた | 状態台帳の試験 |
| 17 | `focus_request` | `Buffers`(tick の頭で空にしない・同じ物を phase_c へ) | v2 edge(注視の腕)の指紋 |
| 18 | ufunc.at | 配列ごとの `_require_thawed` | 負の対照(refractory_until・revenue・stock・holdings) |
| 19 | 旗の直書きとビュー | D⑤⑥ の AST | `test_stage_a_guard.py` |
| 20 | 条件つきの代入の古い束縛 | 番兵の scratch(T4)。生成の道具は「区間の中で読む前に書く名前」だけを局所にした(書かれない道筋は UnboundLocalError で大きく落ちる) | `test_strict_scratch_no_stale_reads`・`SHIBUYA_SYSTEMS_CHECK` の 19 構成・12 腕・艦隊/再生/遅れ 2 の試験 |
| 21 | 箱から漏れた局所 | 局所の割り当ての表(漏れ 0) | `test_every_local_of_run_day_is_assigned` |
| 22 | 計時の鍵 | `phase` の鍵の集合は変えない。系ごとの壁時計は別の欄 `RunStats.system_seconds`(manifest に出さない) | manifest の鍵の集合の一致 |

## 3. 結果不変の確かめ(DEF の最後の状態)

HEAD の側はどれも本体の src(`ee3abc7` と同じ中身。本体の HEAD は作業の間に `263b1ff`・`f8e5ddf` へ進んだが `git diff ee3abc7 HEAD -- src tests` は空)。

### 3-1. byte-check 19 構成

- [sides/head.json](sides/head.json)(HEAD)・[sides/1-0.json](sides/1-0.json)(門 DEF2 の写し)・比較 [byte_check_1-0_vs_head.json](byte_check_1-0_vs_head.json): 19/19 で `byte_check_10e.py compare` の 25 欄(final・呼数・blocks・calls の列の sha・行動の件数・起床の内訳・顕著行為・出動・食事・behavior/full の最後・締めの後の 2 本・暦・frozen_sources ほか)が全部同じ。書きの検査は既定で入っている。HEAD の final は 10e の `sides/act.json` と 19/19 同じ。
- 300 体で「書きの検査+段 B(2 tick ごと)+番兵の scratch」を入れた 19 構成([byte_check_300_systems_check.json](byte_check_300_systems_check.json)): 19/19 で宣言の外の変化 0・番兵の読み 0・全 25 欄が HEAD の 300 体と同じ。

### 3-2. 2 日のラン・再開・manifest

- 2 日のラン([two_day_check.json](two_day_check.json)・`two_day_check_act.py one`・5,000 体・既定 v3・テープつき): 暦・天気・final `912446bd2b42b6ab`・140,913 呼・テープの calls と blocks の sha が HEAD と同じ(10e README の値とも同じ)。
- 再開の 19×2([resume_19x2.json](resume_19x2.json)・`resume_19x2.py`・世界資産 300 体・2 日・checkpoint 60・T=750 と 1440 で止めて再開): 38 本とも再開=通し(checkpoint の全点・final・呼数の合計)。通しの final と呼数は 19/19 HEAD と同じ。状態のファイルの大きさは HEAD と 40 B ほど違う=見出しの環境の欄(git の commit・汚れ・diff の sha・env_id)と `run_id`(時刻の印)だけ(見出しを突き合わせて確かめた)。
- manifest([manifest_check.json](manifest_check.json)・10f の `manifest_check_10f.py side` の 7 本+`manifest_check_1_0.py`・両側 `PYTHONHASHSEED=0`): 7 本とも final・全欄(1,053〜1,576 欄)・頂上の鍵の順・壁時計の欄を含む鍵の集合が同じ。違うのは環境の 5 欄(`env_id`・`environment.code.git_commit/git_diff_sha256/git_dirty`・`environment.env_id`)だけ。
- 既存の実 LLM テープの再生: **空欄**。手元の実 LLM テープは 10e の RET で再生不可(10e の記録)。mock の録画→再生は全体の pytest(`test_tape_wiring` ほか)で通った。

### 3-3. 系ごとの指紋([probe_compare.json](probe_compare.json))

- `probe_run.py`: HEAD は `sys.monitoring` で HEAD の run_day の系の先頭の行に張り、1-0 は進行役の境目で、同じ `probe.snapshot`(SoA の全列・外の状態の全道筋・積算・buffers)を取り、(T, 系, 変わった欄の digest) の並びと系ごとの指紋を比べた。1,000 体・seed 1・全 tick。
- v3 既定 2 日・古典+記憶+関係・v1 edge・golden の帰無腕: 全部の系・全部の tick で同じ(並び 31,292・17,476・12,917・13,622)。v3 記憶+関係+店+同席・v2 edge: 最後の report の 1 件だけ違った → 両側を `PYTHONHASHSEED=0` にすると全部同じ。原因は HEAD にもある揺れ: `LedgerBundle.growth_parts` が `set(...) & set(...)` の順で辞書を作るので、成長の検査の行の並び(`RunResult.growth_report`)が文字列のハッシュの種で変わる(値は同じ・HEAD と 1-0 の別のプロセスで確かめた)。
- 壁時計の道筋(`O73:runner.phase_seconds`・`O34:norm_meter.seconds/tick_ms_max`・`O19:rel_layer.wall/init_audit`)は指紋から外した(`tick_ms_max` は最大の更新の有無そのものが揃わない)。
- 1-0 の側では段 B(変わった欄 ⊆ 宣言)も見た: 6 構成とも宣言の外 0。

### 3-4. 書きの検査の正と負([guard_results_1-0.jsonl](guard_results_1-0.jsonl)・`guard_runs.py`・世界資産 1,000 体)

| 構成 | 外した列 | 結果 | 落ちた所 |
|---|---|---|---|
| v3 既定 1 日・2 日・記憶+関係+店+同席・古典+記憶+関係・v1 edge・v2 edge・golden | — | 7 本とも通った・final と呼数が HEAD と同じ(`ba70447d…`・`fc2fde3a…`・`4857a414…`・`0fa6d560…`・`5c330f7c…`・`1b83226c…`・`4af63f98…`) | — |
| v3 既定 | world:agents.thermal | 落ちた | `environment.py → resolve.set_thermal` |
| v3 既定 | phase_c:agents.money | 落ちた | `ledger.py:640 _apply_cash`(台帳の旗の検査) |
| 記憶+関係+店 | decide:agents.mem_last | 落ちた | `memory.note_utterance → resolve.write_memory` |
| 記憶+関係+店 | relations_wake:agents.rel_last | 落ちた | `relations.copresent_step → resolve.write_relations` |
| v3 既定 | decide:agents.refractory_until(ufunc.at) | 落ちた | `resolve._require_thawed`(配列ごと) |
| v3 既定 | phase_c:pois.revenue(ufunc.at) | 落ちた | 同上 |
| v3 既定 | world:agents.holdings(ufunc.at) | 落ちた | 同上(`consume`) |
| v3 既定 | phase_c:pois.stock | 落ちた | `resolve._complete_buy` |
| golden 1 日・v3 既定 1 日・v3 既定 2 日 | close_final:agents.transit_state(T3) | 3 本とも落ちた | `run_end.sys_close_final → runner.end_of_day → rail_depart` |
| v3 既定 | presence:agents.cell | 落ちた | `presence → resolve.rail_arrive` |
| v3 既定 2 日 | day_close:agents.transit_state | 通った=書きの起きない負の対照(途中の日の締めは最後の便を流さない) | — |

- 草案の試作(HEAD `0389689`)では v3 既定 1 日の close_final は書かなかったが、`ee3abc7` では書く(10e の後)。
- 合成世界の小さなランの負の対照 10 本・scratch の負・道筋の負・正・T4 は pytest `tests/engine/systems/test_guard_runs.py`。

### 3-5. 門 DEF1 で落ちた 4 件と直し

1. `test_presence_exit_walk`・`test_resume_10d[walk_exit]`(**T5 が見つけた閉包の漏れ**): 歩いて乗る退出の腕では、最後の日の締めの鉄道の発車が計画実行層へ知らせ(`presence.notify_departed_by_plan` → `set_plan_state`)、`agents.plan_flags` を書く。`close_final` と `day_close` の `resolve_ops` に `set_plan_state`・`rail_arrive` を足した(world の鉄道と同じ口)。6 構成の観測と既定の腕では通らない道。
2. `test_salt_seed_split_10f::test_seeded_hash_sites_are_classified`: seed を引数に持つ関数の中のハッシュの場所の表から HEAD の `(engine/run.py, run_day)`(活動層のハッシュ)が消えた(checkpoint の系へ移り、その関数は seed を持たない)。表から外し注を書いた。
3. `test_state_ledger_10b::test_t2_call_id_on_the_fleet_and_replay_paths`: `*_call_ref(` の 5 か所を run_day の行から探していた → 3 つの系の関数(到着の受け取り・呼・ランの終わり)から (ファイル, 行) で探す形に直した。
4. 既知の 1 件(`test_ab7_seed1_open_matches_the_parent_report`)。

### 3-6. 追加の腕(T5・[arms_check.json](arms_check.json)・`arms_check.py`)

19 構成に無い腕 12(歩いて乗る退出・親しみ・自宅の食事と就寝の遅らせ・3 人会話・出勤率 0.7・口コミの旧の源・古典の per_hour の門・mock の対象の確率・v2 edge+PLATEAU の面積・計画実行層なし・応答の遅れ 2・センサスの書き出し)を 300 体・1 日で、書きの検査+段 B(3 tick ごと)+番兵を入れて回した。最初の回で古典の per_hour の門だけ段 B が落ちた(**持ち主をまたぐ別名の書き**: `resolve._energy_meal` が `EnergyLayer.meal_reset`=`ClassicalPolicy._gate_hazard` と同じ配列に 0 を書く=O21)。phase_c と home_meal の `writes.paths` に `O21:classical._gate_hazard` を足した後、12 本とも検査を通り、final と呼数が HEAD と同じ。

### 3-7. 艦隊・再生・遅れ 2・再開の既存の試験(T5)

- 全体の pytest は書きの検査を既定で入れた形で回る(`test_fleet_wiring`・`test_tape_deferred`・`test_response_delay`・`test_resume_10d` を含む)。
- `SHIBUYA_SYSTEMS_CHECK=1`(段 B+番兵)で `test_response_delay.py`・`test_tape_deferred.py` を回した: 18 passed(宣言の外 0・番兵の読み 0)。この口がわざと外した道筋で落ちることも確かめた。

### 3-8. 検査と進行役の重さ(版の予算表の材料)

[timing_1-0.jsonl](timing_1-0.jsonl)。v3 既定・5,000 体・1 日・同じ機械(門の pytest を並べて回している最中=雑音が大きい):

| 形 | 壁時計(秒) |
|---|---|
| 1-0・書きの検査あり(既定) | 33.6・33.3 |
| 1-0・書きの検査なし(`SHIBUYA_WRITE_GUARD=off`) | 32.0・33.7 |
| HEAD と 1-0(既定)を交互に | HEAD 30.2・31.5 / 1-0 33.1・33.0 |

- 書きの検査の重さは雑音の幅の中(±2 秒)。進行役ほかの形(系ごとの包み・前置き・scratch の書きの検査)を含めた 1-0 の全体は HEAD より約 +5〜9%(推測: 雑音が大きいので静かな機械で測り直す=§5)。

### 3-9. 門 DEF2(直した後の最後の状態)

- byte-check 19 構成: 19/19 全欄同じ(§3-1 の `sides/1-0.json` はこの門の値)。
- 全体の pytest(書きの検査を既定で入れた形): 3,946 passed・1 failed(既知の junction の 1 件)・1 skipped・1 xfailed(63 分)。

## 4. 複数の系が書く列(ユーザーの条件)

[multi-writer-columns.md](multi-writer-columns.md)・[multi-writer-columns.json](multi-writer-columns.json)(`multi_writers.py`)。宣言(閉包=上限)と観測(1-0 のラン・6 構成・1,000 体・全 tick)を並べた。SoA の列で 2 系以上が書く=宣言 56・観測 33(草案 §1-5 は 28=窓の tick だけ)。外の状態の行で 2 系以上=観測 30(草案は 27)。`agents.activity` は観測で 7 系(world → presence → apply_responses → plan_boundary → phase_c → conversation → close_final)・宣言で 9 系。後で話題ごとにまとめ直すときの課題の一覧として使う。

## 5. 空欄・未確認・親に確かめてほしい点

### 5-1. 空欄

- 段 D・E の中間の状態のスナップショットと門(§1-1)。
- 既存の実 LLM テープの再生(手元に再生できる実 LLM テープが無い=10e の RET)。
- 静かな機械での重さの測り直し(§3-8 は門の pytest と並べて測った)。
- 草案 §2-6 D③ の「読む欄」の検査は系のコード(と systems の中の補助)の箱の属性の参照だけ。層のメソッドの中の読みは見ない(草案 K6 のとおり)。

### 5-2. 草案と違えた点(まとめ)

1. 段の順と数 A → CB → DEF(§1-1)。
2. `Fixtures` の箱を足した・`prev_*` は `RunStats`・名の衝突を避けた改名 7 つ(§2-1)。
3. `close_final` を `day_close` と別の系にした(§2-2)。
4. 系ごとの指紋は checkpoint_detail と first_diff の延長でなく新しい道具 `probe.py`(checkpoint_detail は checkpoint の時刻と full-hash の範囲だけで、系の境目ごと・全欄の差には足りない。digest の取り方 `item_digest` は同じ)。
5. 世界過程 18 本は `world` の 1 つの系の中(§2-2)。
6. `resolve_ops` は観測+層のメソッドの静的な到達+読んだ経路から手で書いた。閉包は上限なので、宣言の外=閉包の外。

### 5-3. 親に確かめてほしい点

1. **成長の検査の行の並びの揺れ(HEAD からある・1-0 の外)**: `LedgerBundle.growth_parts` の `set(...) & set(...)` の並びで `growth_report` の行の順が `PYTHONHASHSEED` によって変わる(値は同じ・final と checkpoint には入らない)。manifest に出るなら 2 回のランの manifest が揃わないことがある。直すかは親の判断。
2. **T5 で見つけて足した宣言 2 つ**(§3-5 の 1・§3-6): close_final・day_close の `set_plan_state`(歩いて乗る退出の腕)と、phase_c・home_meal の `O21:classical._gate_hazard`(食事で古典の門の H を戻す=層が他の層の配列を別名で持って書く)。後者は草案 §0-2 の「持ち主をまたぐ書き」(1-0 では宣言で認める)に入れた。
3. `O96 run_day.replay_inbox` は軸 1 が no だが、再生のランでは到着の受け取り(挙動)が読む(HEAD でも同じ。`run_day` の持ち主の行は外の軸 1 の AST の対象の外=`ext_attr_rows` が除く)。
4. 試験の差し替えの的を `engine.systems.state_io.full_state_hash`・`engine.systems.build.<名>` に付け替えた(§2-5)。`engine/run.py` から使わない import を外したので、古い的を突く `docs/bench/analysis/` の古い記録の道具 3 本(10a の `response_delay_measure.py`・intent-chooser の `intent_hold_measure.py`・10b の `hash_cost.py`)は回し直すときに直す(凍結の印は付けていない)。
5. このフォルダの試作の道具(`guard_poc.py`・`dyn_writers.py` ほか)は HEAD の run_day の行番号に張るので、1-0 の後は回らない(記録として残した)。
6. 門の写し(作業木の隣の置き場 `wt1_0_gate/<名>`)の `data` は本体の data への junction。消すときは junction を先に PowerShell の `(Get-Item <写し>\data).Delete()` で外す(`rm -rf` で中身を消さない)。生の出力は本体の `data/runs/1-0_*`(git の外)。

## 6. 段ごとに変わったファイル(親が段ごとに commit を切る)

各スナップショットの `list.txt`(HEAD から変わった・足したファイルの累積・消したファイルは無い)。

- A(13): `src/shibuya/core/write_permit.py`(新)・`agents/state.py`・`world/state.py`・`perception/state.py`・`engine/resolve.py`・`engine/state_ledger.py`・`engine/state_ledger_ast.py`・`engine/systems/__init__.py`・`allow.py`・`probe.py`(新)・`tests/engine/systems/__init__.py`・`test_stage_a_guard.py`(新)・`docs/.../run-day-decomp/probe_run.py`(新)。
- CB(31=A に足す): `engine/run.py`・`engine/systems/boxes.py`・`conductor.py`・`guard.py`・`observe.py`・`report.py`・`spec.py`・`state_io.py`・`table.py`(新)・`tests/engine/systems/test_boxes.py`(新)・`tests/engine/test_two_phase.py`・`test_state_ledger_10b.py`・`discard_probe.py`・`processes/test_rng_scheme_10c.py`・`test_version_bump_10e.py`・`test_state_checks_10f.py`・`docs/.../local_assignment.py`・`local-assignment.json`(新)。
- DEF(累積の最後): CB に加えて `engine/systems/act.py`・`body.py`・`build.py`・`day.py`・`decide.py`・`judge.py`・`llm_io.py`・`overrides.py`・`perceive.py`・`remember.py`・`run_end.py`・`static_check.py`・`talk.py`・`world.py`(新)・`tests/engine/systems/test_guard_runs.py`・`test_systems_table.py`(新)・`tests/engine/test_10a_review_fixes.py`・`test_fleet_wiring.py`・`test_renderer_wiring.py`・`test_response_delay.py`・`test_sim_time_T.py`・`test_salt_seed_split_10f.py`・記録と道具(この記録・`multi_writers.py`・`multi-writer-columns.*`・`guard_runs.py`・`resume_19x2.py`・`manifest_check_1_0.py`・`arms_check.py`・`sides/`・比較の JSON)。

## 7. 検収の後の直し(段 FIX)

独立の検収 [review-impl-1-0.md](review-impl-1-0.md) は「条件つき受入」だった。§1 の 1〜10(宣言の外を書いても落ちない穴と記録の食い違い)を、同じ作業木で段 FIX として直した。スナップショットは `snap_FIX`(HEAD からの累積)。

### 7-0. 結論

- 中の 3 件(箱の形の ufunc.at・scratch の中身の書き換え・許可を外す口)は、どれも「植えた行で落ちる」負の対照を付けて塞いだ。ただし ufunc.at と scratch の中身は、既定のランでは止まらない。止まるのは試験の形(段 B・静的な D)だけで、限界は §7-3 の表に書いた。
- 直したことで、宣言の漏れが 4 つ見つかった。どれも宣言を足して閉じた。値は変えていない。
  1. world の `O63:renderer._tickc`: `_tickc.flow` は `runner.flow` と同じ配列(別名)。
  2. checkpoint の `phase`
  3. report の `frozen_sources_map`
  4. observe の `occ_counts`・`occ_kind`・`occ_transit`
- 結果不変: 門 FIX1 の byte-check 19 構成は 19/19 で全 25 欄が同じ。全体の pytest は 3,961 passed で、落ちたのは既知の 1 件だけ(§7-4)。段 B の 6 構成(scratch の中身を含む・1,000 体・1 日)は宣言の外の変化が 0 件で、final は段 DEF の測りと同じ。

### 7-1. 項ごとの直し方と負の対照

| 検収 §1 | 直し方 | 負の対照(植えた行で落ちる) |
|---|---|---|
| 1(中)resolve の外の箱の形の ufunc.at(L1) | `tests/engine/test_add_at_guard.py` の `STATE_ROOTS` に `b.soa`・`box.soa` を足した。局所の別名は不動点までたどる(組の代入・注釈つきの代入を含む)。別名は、行き先の根が状態の根かどうかで判定する。系のモジュール(`engine/systems/`)を全部走査する試験も足した | `test_box_rooted_and_aliased_ufunc_at_outside_resolve_is_found`: 植えた 4 つの形(`b.soa.agents.registry.money`・`r = b.soa.agents.registry; r.money`・組の別名・`box.soa.world.pois`)が全部見つかる。実行時の側は `test_guard_runs.py::test_box_rooted_ufunc_at_outside_resolve_is_caught_by_B`(perceive_prepare に植えると、段 B が `agents.money` を perceive_prepare に出す) |
| 2(中)scratch の中身をその場で書き換える(L4・L4b) | `probe.view_of` が scratch を渡す。段 B の族に `"scratch"` を足した(`SHIBUYA_SYSTEMS_CHECK` の `_conduct_checked`・試験)。scratch の digest は `objs=True`: dataclass・配列・辞書・列は中身を見る。根の知らない物は `__dict__`・`__slots__` を見る。入れ子の知らない物・関数・外の状態の持ち主・SoA は同一性(物の番号)だけを見る。tick の頭に境目 `(tick_head)` を置き、scratch を空にした差を前の系に帰属させない。`declared_check` の `scratch.` の分岐はこれで使われるようになった。L4b の `object.__setattr__` は、系のモジュール(`boxes.py` の外)で使わないことを静的に固定した | `test_scratch_in_place_write_by_a_non_writer_shows_in_B`: phase_c の前に `scratch.plan.confirmed.action_code[0] += 1` を植えると、段 B が `(phase_c, scratch.plan)` を出す。`test_bypass_setattr_check_catches_a_planted_line`: `object.__setattr__(b.scratch, "outcome", …)` が見つかる |
| 3(中〜低)許可を外す口(L2・L11) | `tests/engine/systems/test_fix_guards.py::test_permit_switches_are_called_only_from_known_places` を足した。`core.write_permit` を import してよいのは状態のモジュール 3 つ・`engine/systems/guard.py`・`write_permit.py` だけ。`scope`・`enabled` は guard だけ、`allows` は状態のモジュールだけが呼べる。`set_enabled`・`current` は src のどこからも呼ばない(切替口は環境変数と試験だけ)。`guard.system_scope` は conductor だけが呼べる。許可の大域(`_PERMIT`・`_ENABLED`・`SCRATCH_PERMIT`・`BUFFERS_PERMIT`・`CURRENT`)は、持ち主のモジュールの外で代入しない(`setattr` の定数の名も見る) | `test_permit_check_catches_planted_switches`: 系に `WP.scope(None)`・`set_enabled(False)`・`G.system_scope(…)`・`G.SCRATCH_PERMIT = None`・`WP._PERMIT = None` を植えると全部見つかる |
| 4(低)Buffers に段 C が無い(L5) | `Buffers.__setattr__` を足した。系の `writes.buffers` に無い欄を差し替えると `AttributeError` になる(`guard.BUFFERS_PERMIT`・`system_scope` の 4 つ目の引数)。§2-4 の C の行は「TickScratch」だけでなく「TickScratch・Buffers」になる | `test_buffers_replacement_outside_the_declaration_fails`: detect に `b.buffers.focus_request = …` を植えると `AttributeError` |
| 5(低)D⑥ の別名の形(L3) | `test_fix_guards.py::test_d6_no_layer_holds_a_soa_array_view_or_alias` を足した。見る形は `registry.arrays["x"]`・`getattr(r, "x")`・`r.field(変数)`・局所の別名(不動点)・`np.asarray`・`.view`・`.reshape`・`.ravel`・組の代入・辞書・列。新しく 1 件見つかった: `engine/processes/civic.py` の `self.bed_cell[got] = …`。層の ndarray の要素への代入で、値の写しなので別名にはならない。理由を付けて許可の表に入れた | `test_d6_finds_the_alias_forms`: 植えた 11 行のうち別名の 10 形が見つかり、`self.ok = 3` は見つからない。`np.asarray` は dtype によって写しにもビューにもなるので、見つける側に倒した |
| 6(低)D① の別名(L9) | `static_check` が resolve を指す名を全部集める。モジュールの頂上と関数の中の `from shibuya.engine import resolve as X`・`import shibuya.engine.resolve as X`、素の import の `from shibuya.engine.resolve import 口 [as y]` が対象 | `test_d1_sees_plain_imports_and_other_aliases`: 素の import・別名・関数の中の import で呼んだ口が `resolve_calls` に出る |
| 7(低)observe の積算と静的な検査 | `table.py` の observe の `writes.tally` に `occ_counts occ_kind occ_transit` を足した。probe の `STATS_NAMES` に `occ_counts`・`occ_kind`・`occ_transit`・`ledger_growth`・`state_files`(壁時計の `seconds` は外す)・`frozen_sources_map` を足した。`static_check` は RunStats の欄の別名をたどる: `x = b.runstats.f`・`x = rs.f`・組の代入、その別名への `x[...] =`・`x +=`・変更のメソッド・属性への代入。これで新しく 2 件見つかり、宣言を足した: checkpoint の `phase`(`result, phase = rs.result, rs.phase` の `phase["checkpoint"] +=`)と report の `frozen_sources_map`(`.update`) | `test_d3_tally_writes_through_tuple_aliases_are_seen`: 組の別名を通した書きが `tally_stores` に出る |
| 8(低)段 B が見えない外の道筋 7 本 | probe の外の道筋の digest で `item_digest` が例外になったら、`SH.resolve_item` で値を取る。取れたら `X:` の digest(`objs=True`・関数は名と物の番号)で見る。`ERR` のまま残るのは、持ち主に属性が無いときだけ(腕が立たない=値は変わらない) | 段 FIX の 6 構成(`data/runs/1-0_probe_fix2`)で変化を観測: `O25:poi_resolver.chooser.stats`(古典の腕・768 回)、`O61:runner.log`(1,147 回)、`O63:renderer._tickc`(2,6xx〜2,798 回)。world の `_tickc` の変化は、宣言の外として出た(上の結論 1・宣言を足して 0 件)。O64 の 3 本(組み立てで差し込む関数)は 1 本のランの中で変わらない。差し替えれば物の番号が変わるので B に出る |
| 9(設計の注)外の道筋の宣言が粗い | 直さない(1-0 は行を割らない約束)。数を [ext_coarse.json](ext_coarse.json)(`ext_coarse.py`)に残した。台帳の外の道筋は 489 行。`writes.paths` の宣言は 180 個(検収の 179 個+world の O63)で、そのうち `*` は 174 個。宣言上の (系, 道筋) は 2,197 対、観測は 383 対(段 DEF と段 FIX の測りの和)で、約 5.7 倍。道筋の単位に割るのは土台(話題ごとにまとめ直すとき)の課題 | — |
| 10(記録) | (1) run.py から外した import: §2-6 の「104 個」は誤り。頂上の import は 187 → 88 で **99 個**。関数の中の import を含めると、名前の数で 205 → 103(102 個)、異なる名前で 202 → 100(**103 個**=検収の数)。(2) `local-assignment.json` の `ledger_growth` を `box:stats.ledger_growth` に直した(`box:stats` 35 → 36・`end` 26 → 25)。(3) `SystemSpec.soa_declared` を消した。恒真だった `test_d2_detects_a_hand_written_mismatch` も消した。D② は凍結した表 `tests/engine/systems/writes_soa_frozen.json`(31 系の閉包)と、いまの閉包の突き合わせにした | `test_d2_detects_a_widened_or_narrowed_permit`: perceive_prepare の `resolve_ops` に `set_refractory` を足す(許可が広がる)・phase_c から口を 1 つ外す(狭まる)と、凍結の表と食い違ってその系の名が出る |

### 7-2. 直したことで見つかった宣言の漏れ(値は変えない)

| 系 | 足した宣言 | どこで見つかったか | 理由 |
|---|---|---|---|
| world | `paths` に `O63:renderer._tickc` | 段 B(§1 の 8 の代わりの digest) | 前の tick の描画の前計算 `_tickc.flow` は `runner.flow` と同じ配列(`prepare_tick` の `np.asarray(flow, uint8)` は写さない)。世界過程が流れの段をその場で書くと見える=持ち主をまたぐ別名(O21 と同じ型) |
| checkpoint | `tally` に `phase` | D③(§1 の 7 の組の別名) | `phase["checkpoint"] += …`(壁時計・`STATS_NAMES` に入れない=段 B では見ない) |
| report | `tally` に `frozen_sources_map` | D③(欄の別名の変更のメソッド) | `frozen_sources_map.update(…)` |
| observe | `tally` に `occ_counts occ_kind occ_transit` | 検収 §1 の 7 | `append` |

ほかに、scratch の中身を見るようにした最初の測りで、`scratch.outcome` が memory・activity_intent・energy_after・close_final に出た。原因は `Outcome` が世界過程・台帳・層への参照(`rail`・`crowd`・`hotel`・`salient`・`ledger`・`energy`)を持つことで、参照の先の持ち主の変化が outcome の digest に入っていた。scratch の書きではないので、宣言は足していない。digest の側で、持ち主と入れ子の知らない物を同一性だけで見るように直した(持ち主の中身は外の道筋の族で見る)。

### 7-3. 限界(直せなかったもの・試験の形だけのもの)

| 穴 | 既定のラン(A・C) | 試験(B) | 静的(D) | 残る理由 |
|---|---|---|---|---|
| resolve の外の ufunc.at(L1) | 止まらない(numpy の `ufunc.at` は `writeable` を見ない) | 書いた系に出る | `test_add_at_guard`: 状態の根・`b.soa`・`box.soa`・局所の別名 | 実行時に止めるには、`ufunc.at` を包むか、状態の配列を numpy の外の型にする必要がある(1-0 の外)。D の形の外(関数の引数や戻り値で渡した配列・`getattr` で取った配列)は B だけが見る |
| scratch・buffers の中身のその場の書き換え(L4) | 止まらない(段 C は欄の差し替えだけ) | 書いた系に出る(試験のときだけ・`SHIBUYA_SYSTEMS_CHECK`) | `object.__setattr__` の素通りだけ | 毎 tick 全欄の digest を取るのは既定のランには重い。入れ子の知らない物(dataclass でない層の物)の中身は同一性だけで見る。物の番号は、古い物が消えて同じ番号に新しい物が来ると見逃す |
| 許可を外す口の動的な呼び出し | — | — | 静的に置き場を固定(import・属性・素の名・`setattr` の定数の名) | `importlib`・`getattr(WP, 変数)`・`sys.modules` 経由は見ない |
| D⑥ の残りの形 | — | B が書きを出す | 10 形 | 関数をまたぐ別名(引数・戻り値)・別のメソッドで足す入れ物(`self.xs.append(view)`)・`setattr(self, 変数, …)`。的が `X[i]`(添字の代入)だと、配列(値の写し)か辞書(参照)かを AST では決められない(見つける側に倒し、`civic.py` の 1 件は許可の表へ) |
| D① の残りの形 | 列が許可の外なら A が止める | — | 素の import・モジュールの別名 | `getattr(R, 変数)`・口を値として渡す(`partial(R.x)` など) |
| 段 B の外の道筋で `ERR` のまま | — | 持ち主に属性が無い腕だけ(値は変わらない) | — | — |
| 外の道筋の宣言の粗さ(§1 の 9) | — | `*` の中の書きは宣言の中として通る | — | 1-0 は台帳の行を割らない。道筋の単位に割るのは土台の課題(宣言 180 個のうち `*` は 174 個・宣言 2,197 対/観測 383 対) |

### 7-4. 結果不変と試験(段 FIX の最後の状態)

- 門 FIX1(HEAD+`snap_FIX` の写し・`gate.sh`): byte-check 19 構成は **19/19 で全 25 欄が HEAD と同じ**([byte_check_FIX_vs_head.json](byte_check_FIX_vs_head.json))。全体の pytest は 3,961 passed・1 failed。落ちた 1 件は既知の `test_ab7_seed1_open_matches_the_parent_report`(写しの junction で起きる・DEF2 と同じ)。門のスナップショットの後に、`test_fix_guards.py` の D② の負の対照を作り直した(`test_d2_detects_a_widened_or_narrowed_permit`)。この 1 本は作業木で回して通った(10 passed)。
- 段 B の 6 構成(`probe_run.py run --families soa,ext,stats,buffers,scratch`・1,000 体・1 日・`data/runs/1-0_probe_fix2`): 宣言の外の変化は 6 構成とも 0 件。final は段 DEF の測り(`data/runs/1-0_probe`)と同じ(v3_default は段 DEF が 2 日なので比べていない)。
- systems の試験と `test_add_at_guard.py`: 130 passed(新しい負の対照を含む)。状態台帳の AST の検査(`test_state_ledger_10b.py`)は、probe の `getattr` の 2 行を許可の表 `UNRESOLVED_ALLOW` に合わせた(文字列が変わった 1 行と、`__slots__` の 1 行を足した)。
- 注: `probe_compare.json`(HEAD と 1-0 の系ごとの指紋の一致・§3-3)は段 FIX の前の測り。段 FIX は `STATS_NAMES` に 6 つ足し、`objs=True` の digest を足した。既定の digest(`objs=False`)の取り方は変えていない。HEAD との比べは回し直していない(空欄)。
- `multi-writer-columns.md`・`.json` は、段 DEF と段 FIX の測りの和で作り直した。SoA の観測は 33 列のまま。外の道筋の観測は 64 → 66(行の単位 30 → 32)で、`O61`・`O63` が足された。

### 7-5. 段 FIX で変わったファイル(`snap_FIX/list.txt` は HEAD からの累積)

- src: `engine/systems/boxes.py`(Buffers の段 C)・`guard.py`(`BUFFERS_PERMIT`)・`conductor.py`(buffers の許可・`(tick_head)` の境目・段 B の族に scratch)・`overrides.py`(`wrap_fn`)・`probe.py`(scratch・積算の欄・代わりの digest・同一性)・`spec.py`(`soa_declared` を消した)・`static_check.py`(作り直し)・`table.py`(宣言 4 つ)・`engine/state_ledger_ast.py`(許可の表 2 行)。
- tests: `tests/engine/test_add_at_guard.py`・`tests/engine/systems/test_fix_guards.py`(新)・`writes_soa_frozen.json`(新)・`test_guard_runs.py`(負の対照 3 つと scratch を含む正)・`test_systems_table.py`(恒真の試験を消した)。
- 記録と道具: この記録・`local_assignment.py`・`local-assignment.json`・`multi_writers.py`・`multi-writer-columns.*`・`probe_run.py`(`--families`)・`ext_coarse.py`(新)・`ext_coarse.json`(新)・`byte_check_FIX_vs_head.json`(新)。
