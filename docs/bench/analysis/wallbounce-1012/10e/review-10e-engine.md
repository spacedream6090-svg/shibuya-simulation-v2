# 10e エンジン側(E1・E2・E4・E5・E6)の検収(実装を見ていない検収役・Opus 5.5)

> 対象: 作業木の未 commit の差分(HEAD `18ff37f` からの累積=E1〜E5)と `<scratchpad>/10e/snap_E1・E2・E4・E5`、記録 [README.md](README.md)。
> 検収役は追跡しているファイルを書き換えていない。独立のランは HEAD の写し(`git archive HEAD`)と、HEAD に各スナップショットを重ねた写し(`tree_E1・E2・E4`)をスクラッチで回した。パスは `src/shibuya/` を省く。
> 注意(手順): スクラッチの長いパスでは numba のキャッシュの書き込みが Windows のパス長の上限で落ちる。写しは 8.3 の短いパスから回した(実装役の手順の「短いディレクトリ」と同じ理由)。

## 0. 判定

**条件つき受入**。挙動(呼数・行動・テープ・乱数の重なり)の主張は独立のランで全部再現した。結果(判定)を動かす欠陥が 1 件ある。既定の final は艦隊の録画と再生で一致しない(§1 R1)。直し方は小さく、検証済み。ほかに K15 の取りこぼしの問いがある(§5 Q1)。

## 1. 結果を動かす欠陥

### R1 既定の final(behavior-hash)が、艦隊で録画したランとその再生で一致しない(普通に終わるランでも)

- 実測(偽 vLLM 2 台・合成世界 120 体・語彙 v3・checkpoint 4 tick ごと):
  - キュー満杯の設定(40 tick・呼 33・繰り延べ 0・終わりの未回答 0): **checkpoint 10/10 と final が録画と再生で違う**。`legacy_combined` は 10/10 一致・テープの miss 0・呼数 33/33。
  - タイムアウトの設定(12 tick・全部繰り延べ・終わりの未回答 1): 3/3 が違う。
- 食い違う行は `checkpoint_detail` で特定した。behavior の行では **O44 の `run_day.replay_inbox` だけ**(ほかに O88 の `fleet_bridge._interned` も違うが、軸 1 が no なので behavior-hash には入らない)。再生では、テープの `observed_tick` が先の応答が `replay_inbox` に入る。録画では同じ応答が艦隊の中(O65=no)にあるので、表し方が両側で揃わない。最後の checkpoint の tick に応答が 1 つでも飛んでいれば final も違う。
- README §E6-4 の 1(と §E1-4、`test_tape_deferred.py` の注)は「ランの終わりに待ちが残るとき(タイムアウトのランなど)は final も違う」と書くが、範囲が狭すぎる。待ちが残らない普通のランでも、最後の tick に在途の呼があれば final が違う。途中の checkpoint は、在途の呼があれば必ず違う。
- mock では出ない(確かめた): 合成世界の 3 構成(記憶+関係・v1・応答の遅れ 2)で、mock の録画と再生の behavior-hash は全 checkpoint で一致した。HEAD の写しでも同じ形。
- **直し方(小さい・検証済み)**: `run_day.replay_inbox` だけを behavior-hash の項から外す(台帳の O44 を分け、`replay_inbox` を軸 1 no・軸 2 required に)。`fleet_waiting`・`fleet_deferred` は残す。`state_ledger.behavior_items` から 1 項だけ除いた写しで回すと、上の 2 設定で **10/10・3/3 が一致**した。応答がいつ届くかはテープから来る外の入力(LLM の応答そのものと同じ扱い)で、録画側はこれを checkpoint の時点で知り得ないので、外すのが筋。
- 代償: 項を 1 つ外すと全構成の behavior-hash が動く(空の辞書の直列化が抜ける)。E1 で final はどのみち全部動くので、**E1 の commit の前に入れれば golden の張り替えは 1 回で済む**。失うもの: 「E1 の final=10f の `byte_check.json` の behavior-hash(19/19)」の照合。直した後は、`test_tape_deferred`・`test_response_delay` の比べ方を `legacy_combined` から既定の `combined` に戻せる(T2 を既定の final で見られる)。
- 影響: シミュの挙動は変わらない。ただし実 LLM のランの T2(録画=再生)を既定の final で判定すると、誤って不一致になる。GPU が無い今は潜在だが、版上げで final の定義を替えるのは E1 なので、ここで直すのが安い。

## 2. 潜在の欠陥

- **L1 `rng_scheme="counter"` の意味が版で変わったのに、印が無い**。10c〜10f の counter(K19 の並べ方の前)と 10e の counter は母集団の抽出と体の定数まで違う。テープの脇の meta には `rng_scheme=counter` としか残らない。10c〜10f に `--rng-scheme counter` で録った mock のテープを 10e で再生すると、明示の止まり方ではなく miss で外れる。実 LLM のテープ 17 本は meta が無く stateful 扱いなので当たらない。手当ての案: テープの版が 4 より前で `rng_scheme=counter` なら止める。
- **L2 母集団の抽出の既定が呼び手ごとにずれうる**。`agents/population.py` の `load_population(..., n=<整数>)` は `sample_population` を `rng_scheme` なしで呼ぶので、いつも counter になる(engine は n=None で読んでから方式を渡すので今は当たらない)。`tools/c7/attr_arms.py` と `docs/bench` の測りのスクリプト数本も `sample_population(pop, n, seed)` のまま。`docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py` は 3 引数の関数で `sample_population` を差し替えるので、10e の engine から `rng_scheme=` 付きで呼ばれると TypeError になる(凍結した測りの道具)。
- **L3 CLI の checkpoints の JSON**(`shibuya.cli/checkpoints/1`)は `combined` の意味が behavior-hash に変わったのに版を上げていない。`cli.py` の注「final=combined には混ぜない」も古い。manifest に `hash_scheme` が載るので見分けはつく。
- **L4 展開の上限 8 GiB**: 数字は再計算で合う(全腕 6,179.4 B/体 × 390,067 = 2.41 GB > 2 GiB、8 GiB はその約 3.6 倍)。ただし外から来たファイルへの防御なので、体数に比例する上限(見出しの体数 × 体あたりの上限)の方が筋が良い。外挿は 1 日目の終わりの状態からの線形(宣言どおり推測)。
- **L5 リポの根に空のファイル `overlay_paths.txt`**(追跡外・0 B)がある。スナップショットには入っていない。commit に混ぜない(誰が作ったかは不明)。
- **L6 `fail_streak`**: 宣言の文に「4 回で打ち切り(行動契約書 §6)」とあるが、読み手は 0(台帳の注のとおり)。契約の打ち切りが実装されていない状態が続いている(K15 と一緒に扱う=§5 Q1)。

## 3. 記録の誤り

- **D1** README §E6-4 の 1・§E1-4・`test_tape_deferred.py` の注: 「待ちが残るとき(タイムアウトのラン)だけ final が違う」→ 実際は「最後の checkpoint の tick に在途の呼があれば違う・途中の checkpoint は在途の呼があれば必ず違う」(§1 R1)。
- **D2** 台帳 `engine/state_ledger.py` の `fail_streak`・`plan_activity` の注は「K15 の答えで直す欄」のまま。K15 は 10-06 に答えが出ている(§5 Q1)。
- **D3** `snap_E1/status.txt` に、後で `snap_E1/files` へ足した 3 ファイル(`test_ledger_wiring`・`test_response_delay`・`test_tape_deferred`)が無い。中身は `files/` にあり、summary にも書いてある。
- **D4** README は `snap_E5` にしか無い(E1〜E4 の commit には記録が付かない)。親が E5 で入れるなら問題ない。
- **D5** README §E2-4 の保存の予算(`budget_10e.json`)は E2 の時点(stateful・E4 の前の母集団)の計測。表に段の注が無い。
- **D6** 「旧版(版 3)の実 LLM テープ 17 本」(発注書の言い方): 手元の `data/` の実テープ 53 本のうち読めた 52 本は版 1(19)と版 2(33)で、版 3 は 0。版 4 の読み口で全部読め、新しい 7 列は空、`Replay` も組めた。`c7-day-1` の calls.parquet は Parquet の印が無く読めない(10e より前からの破損・10e のせいではない)。

## 4. テストの欠け

- **T1 艦隊の経路のテープ版 4**(`FleetBridge._tape_v4`・応答の行と繰り延べの行)を見る試験が無い。手で確かめた: 応答 33/33・繰り延べ 10/10 の行に B5 と B6 が入り、`prompt_hash` を本文から作り直せた。
- **T2** 艦隊の録画=再生を既定の final で見る試験が無い(`legacy_combined` に替えたため)。R1 を直したら既定の `combined` で比べる形に戻す。
- **T3** `test_e5_recalled_memory_identity_and_acquaintances` は長さ・`kind > 0`・`first_tick <= tick` しか見ない。同定の 3 つを記憶の表と突き合わせていないので、並びのずれや種類と対象の取り違えは落ちない。
- **T4** `test_t1_deleting_the_dead_columns_changes_nothing`: `beh_old` を取り出しているが比べていない。`_observed(new) == _observed(old)` の枝は 5 構成とも `CUR_SYN != STATEFUL_SYN` で走らない。E1 の「行動の件数・prompt_hash は不変」は、既定の試験の束では呼数だけで見ている(byte-check の JSON では一度見た)。
- 「壊したら落ちる」は読んで確かめた: E2 の掃除の単体(全部の t で読みが同じ)・掃除を止めたランとの比較・U2 の既知の答え(旧の並びは 36 語が一致、counter は 4,000 語と 40 語で交わらない)・2 日のランの重なり 0・B5+B6 からの `prompt_hash` の作り直し。どれも、壊せば落ちる形になっている。

## 5. 問い

- **Q1 K15 の取りこぼし**: 指示書 10-06 §6 の K15 の答えは「推奨どおり=読み手 0 の 2 列は消す」。10b のアジェンダ §3 の推奨 (a) は「`fail_streak`・`plan_activity` を Q9 と一緒に死蔵として消す(A4 の範囲を 2 列広げる)」。E1(Q9 の削除)はこの 2 列を消しておらず、`fail_streak` を AST の陽性対照に使い直している。E1 に足すか、別の commit に回すかを親が決める。足す場合、軸 1 は no なので behavior-hash は動かない。`--hash-scheme full` の再現には `retire` を 2 行足せば済む。
- **Q2 E4 は「動く変更」を 2 つ束ねている**: (a) 顕著行為と出動の乱数を counter に(10c の切替)、(b) K19 の鍵の並べ替え(W16 の層の抽出・体の定数・気づき・日の鍵)。(b) で 5,000 体の標本そのもの、つまり既定のランの住人が入れ替わる(W17 の在圏ブロックの数え 8,589 → 8,542 など)。K19 の「重なりを直す」に w16 の抽出が入るのは 10f のアジェンダ §1 の K19 の行(w16 185)から読めるので、決定の範囲の中ではある。ただし A6 の 2 つ目「カウンタ型への切替で動くのは顕著行為と出動の件数だけ」とは食い違う。A6 の「変更ごとに commit を分けて原因を切り分ける」に沿うなら、(a) と (b) を別の commit に分ける案がある(`k19_counters` の切替を `rng_scheme` から切り離す必要がある)。少なくとも「母集団の標本が変わる」ことは、版上げの前の確認(10-03 §3-3)でユーザーに伝える事項だと考える。
- **Q3** R1 の直しを E1 に入れるか(親推奨の材料: 入れれば張り替えは 1 回・T2 を既定の final で見られる)。

## 6. 独立に確かめたこと(実装役の json は使っていない)

| 確かめたこと | 結果 |
|---|---|
| HEAD の写し 4 構成(w6_v3_default・v3_mem_rel・v3_classical・w6_v1_edge)と、作業木の `hash_scheme=full`+`rng_scheme=stateful` | final・呼数・行動の件数とその中身・顕著行為・出動・気づき・食事・全 checkpoint の legacy が **4/4 で HEAD と同じ**。テープの版 3 の 14 列の中身も 4/4 で同じ |
| E1 だけの写し(HEAD+snap_E1)の w6_v3_default | 既定の final `1f4d96b1d8dfa701` は HEAD の最後の behavior-hash と同じ。全 checkpoint の behavior-hash・full-hash・呼数・テープが HEAD と同じ。`full` は全 checkpoint で HEAD の final を再現 |
| 作業木の既定/`stateful` | 既定の final・呼数は README の E5 の値と 3/3 一致(`31fd9324…`/70,421・`e1231f35…`/74,616・`ca630f05…`/96,961)。`stateful` は README の E2 の値と 3/3 一致 |
| 死蔵 5 列の読み手 | src・tools・docs の .py に残っていない(残りは試験の「無いこと」の確かめと 10b の凍結した道具だけ) |
| pickle の口 | src に `pickle.loads` も `import pickle` も無い。`np.load` はどれも `allow_pickle=False` |
| E2 の掃除 | 3 つの辞書の読み手は `refused_recently`・`invite_blocked_by_refractory` の 2 つだけで、どちらも今の tick で「tick < 期限」としか読まない=期限切れの項を読む経路は無い。`stateful` のランの呼数と行動の件数とその中身は HEAD と同じ |
| K19(rng_audit に頼らない数え=4 語のカウンタの区間の交わり) | counter: 合成世界 率 ×1000・2 日/世界資産 300 体・2 日(記憶+関係)/既定 v3 5,000 体・1 日で**重なり 0**。stateful: 5,000 体で w16 185・body.weight 1・body.eer 1(既知の答えと同じ)、2 日で配送・工事・salient が重なる。同じ鍵の作り直しは w16 の 186(cli の財布と run_day の 2 回=設計どおり)だけ |
| 数値の突き合わせ | 呼数 69,978 → 70,421・O39 159,138 → 2,490 B・テープの増分(1 呼あたり 25.7/49.4/21.3 B)・checkpoint の割合 0.12%(4 本を並べた中)。README と合う |
| スナップショット | `snap_E1/files` に E2 以降の変更は混ざっていない。`snap_E5/files` は作業木と一致。HEAD+snap_E1 で E1 の試験の束(slow を除く・2 プロセスの env 試験は写しの都合で除外)は 432 passed・10 skipped・1 xfailed・0 failed。HEAD+snap_E2 で E1→E2 に変わった試験 7 ファイルは 199 passed・1 skipped、HEAD+snap_E4 で E2→E4 に変わった試験 14 ファイルは 308 passed(どれも slow を除く・数には検収役の場所の確かめ 1 件を含む) |

## 再検収(R1 ほかの直しの後・同じ検収役)

対象: 作り直したスナップショット `snap_E1・E2・E4・E5`(HEAD `18ff37f` からの累積)と作業木。追跡しているファイルは書き換えていない。独立のランは前回と同じく、短いパスの写し(HEAD の写し・HEAD に各スナップショットを重ねた写し)で回した。

### 判定: **受入**(残る指摘はどれも低い・下の番号)

### (a) R1: 艦隊の録画=再生と、多重集合の印

| 設定(偽 vLLM 2 台・checkpoint 4 tick ごと) | 繰り延べ(満杯/時間切れ)・再投入・終わりの未回答 | 既定の final(全 checkpoint) | 多重集合の印を外すと |
|---|---|---|---|
| 前回のキュー満杯(合成 120 体・v3・描画あり・40 tick) | 0/0・0・0 | 10/10 一致 | — |
| 前回のタイムアウト(12 tick) | 0/10・0・1 | 3/3 一致 | — |
| 試験と同じキュー満杯(描画 stub・予算 30・40 tick・遅れ 1) | 538/0・516・22 | 10/10 一致 | 4/10 |
| 同じ・遅れ 2 | 538/0・516・22 | 10/10 一致 | 3/10 |
| 受理枠 1+2・遅れ 2 | 1,520/0・1,482・38 | 10/10 一致 | 0/10 |
| 満杯と時間切れの混在・遅れ 2(24 tick) | 624/96・690・30 | 6/6 一致 | 0/6 |
| 描画ありの 3 設定(遅れ 2・40 tick/遅れ 2 の混在・30 tick/記憶+関係 on・60 tick) | 0/0・0・0 | 10/10・8/8・15/15 一致 | — |

- どの設定でも final は一致し、`legacy_combined` も一致・miss 0・呼数一致。多重集合の印は要る(外すと、繰り延べのある設定で食い違う=実装役の見つけた O43・O44 の並びの差を再現した)。
- 印の波及: `_MULTISET` は台帳の `multiset` の欄からだけ作られ、載っているのは `run_day.pending` と `run_day.fleet_deferred` の 2 本だけ。`item_digest` の中で list のときだけ直列化の昇順に並べる。状態のファイルへの書き出しの順は変えない(ハッシュだけ)。
- 並びが挙動に効かないことの確かめ: `fleet_deferred` はアービタの同一体の合流で (体, 実効の級, 待ち, 撹拌鍵, 条件) の lexsort にかかり、全部の鍵が同じ行は中身も同じ=並びに依らない。`pending` は適用の lexsort (t_apply, 級, 撹拌鍵, 体) にかかる。
- O96 を外したことによる「挙動の情報の漏れ」: `replay_inbox` の中身はテープ(外の入力)と、発射した呼から決まる。発射した体は `fleet_waiting`(behavior)に残る。録画の側でも在途の呼は艦隊の中(O65=no)にあるので、扱いは両側で対称。full-hash と状態のファイルには O96(required)として入る=再生の再開は守られる。残る限界は下の 1。
- 独立の照合: HEAD の写しに検収役の手で R1 の定義(behavior の項から `replay_inbox` を外す・O43/O44 を多重集合)を当てて回した。w6_v3_default と v3_mem_rel で、全 checkpoint の behavior-hash が、HEAD+snap_E1 の写しの既定の final(`3264c9fc…`・`e27e45f3…`)と一致した。呼数も同じ。full-hash は O44 → O96 の付け替えで項の札が変わるので動く(README §E1 の表の記載どおり)。

### (b) L1: 10c〜10f の配置の counter テープは止まるか

HEAD の写し(10f)で `rng_scheme="counter"` の mock テープを 1 本録り、作業木で再生した。`run_day` の未指定・counter・stateful の 3 通りと `cli.run` の再生のどれも、`ValueError`(「10c〜10f の counter の鍵の配置で録られている(rng_layout='10e' が無い)」)で止まった。

### (c) T1・T3・T4 は「壊したら落ちる」形か(読んで判定)

- T1(`test_e5_t1_fleet_rows_…`): 応答の行と繰り延べの行が両方あることを先に確かめ、全行で B5・B6 の有無と `prompt_hash` の作り直しを見る。艦隊の経路の 7 列が抜ければ落ちる。
- T3(`test_e5_t3_recalled_identity_…`): `MemoryLayer.recall` を包み、想起した時点の記憶の表(`mem_tick`・`mem_kind`・`mem_object`/店の行は `sm_first`・`sm_poi`)から同定を独立に作り直して、テープの (行, 3 つ組) の並びと突き合わせる。店の行が 1 つ以上あることも見る。並びのずれと種類と対象の取り違えで落ちる。
- T4(`test_t1_deleting_…`): `beh_old` を、掃除を止めた stateful のランの behavior-hash と比べ、behavior 以外の観測量(呼数・行動・prompt など)を 10e の前の再現と比べる。`hash_scheme` の切替で挙動が動かないことも見る。どれも壊せば落ちる。
- T2 の試験(`test_t2_fleet_record_equals_replay_on_the_default_final`)は O96 の陽性対照つき。多重集合の陽性対照は無いが、キュー満杯の設定は印を外すと 4/10 で食い違う設定と同じなので、印を外せばこの試験が落ちる。

### (d) スナップショット

- 4 段とも `files.txt` と `files/` の中身が一致し、`deleted.txt` は空。`snap_E5` は作業木と全ファイルが同じ。
- `snap_E1` は E1 だけ: src と試験の HEAD との差分に `k19_counters`・`purge_expired`(実装)・テープ版 4・`rng_layout` は無い。`test_state_ledger_10b.py` の T4 は `purge_expired` を `raising=False` で差し替えるだけなので、E1 の木でも成り立つ。`snap_E1/status.txt` に、前回 D3 で指摘した 3 ファイルも載った。
- HEAD に各段を重ねた写しで、その段で変わった試験を回した(slow を除く・2 プロセスの env 試験は写しの都合で除外)。E1 の束は 427 passed・1 skipped、E1→E2 で変わった 7 ファイルは 201 passed・1 skipped、E2→E4 で変わった 14 ファイルは 313 passed(どれも 0 failed・数には検収役の場所の確かめ 1 件を含む)。

### (e) 入れ替わる住人

`load_population(全体)` → `sample_population(5,000・seed 1)` を stateful と counter で引き、`source_agent_id` を比べた。共通は 809 体で、**4,191 体が入れ替わる**(README の値と一致)。種別ごとの人数は同じ。

### 残る指摘(低い)

1. **在途の呼の中身は、behavior-hash に両側とも入らない**(潜在・対称)。録画では艦隊の中、再生では O96 にあり、behavior には「待っている体の集合」(`fleet_waiting`)だけが残る。発射の時刻や条件だけが違う 2 つの状態は、behavior-hash では区別されない。10b の設計からの限界で、10e で悪くなったわけではない。記録に 1 行で宣言するのが良い。
2. **`pending` の適用の lexsort に、同じ体・同じ t_apply・同じ級の完全な同点が出うる**(潜在)。艦隊の再送などで同じ体の応答が 2 つ同じ tick に届く場合で、そのときは list の順が適用の順を決める。多重集合のハッシュはこの順を見ないので、順だけが違う 2 つの状態を同じとみなす。今回の設定ではどれも再送 0 で、起きていない。直すなら lexsort の最後の鍵に call_id を足す(同点のときだけ挙動が変わる)。
3. `PRE10E_SYN` の注は「`replay_inbox` を外して計算した」とだけ書き、O43/O44 の多重集合に触れていない(値は今の試験で通っているので、注の書き漏れ)。
4. K15(`fail_streak`・`plan_activity` の削除)は `--hash-scheme full` を消す commit に延ばした(親の決定)。PENDING などで追えるようにしておく。
