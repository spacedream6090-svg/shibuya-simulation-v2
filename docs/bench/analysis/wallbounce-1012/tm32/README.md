# 第 3 期 3-2 時計の段 T1 計算のまとめ(バッチ)の導入の記録

- 実装役 Opus 5.5。作業木の枝 `3-2/tm-t1-batching`(土台 `d35a9b6`=2-4 版上げ 2 回目の取り込みの後)。commit は親。
- 正: [指示書 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-2(全員一斉の 1 分の刻みを廃止=残すのは計算のまとめだけで結果は変えない・「tick」の語は使わない・TM1・TM3 (f)・TM4・TM6 の T1)・[指示書 10-03](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §7-5・§7-6・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) の 3-2 の行・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3・[T0 の記録](../t0/README.md)・[時間のモデルの草案](../../../../design/v2-time-model-design-round-draft.md)(TM3 (f) の元の選択肢の文と §4 の段 T1)。
- 数は実測。生の出力(テープ・side の JSON・ログ)は作業木の `_bc/`(git の外)に置いた。比べた結果だけをこのフォルダに置く。道具は [tools/](tools/)。

## 0. 結論

- 進行役 `conduct` を、全員一斉の刻みのループ(`for T in range(t_begin, t_end)`)から「次に処理する時刻の窓 [t, t+W) の中の事象を時刻順に順番に処理する」形に書き換えた。待ち行列は `engine.scheduler.Scheduler`(バケットの輪+遠未来の heapq)を流用し、バケットの幅を W にした(新しいモジュール `engine/batching.py` の `WindowQueue`)。
- T1 の世界の事象は「刻みの事象」(世界の 1 回の系の並び=刻みの幅 60 秒ごと)だけ。W は刻みの幅の約数(既定 60 秒)なので、刻みの事象はいつも窓の頭に乗る。系に渡す時刻(`TickCtx`)は窓の頭で、前の `t_ns` と同じ。
- **既定 W=60 は結果不変**: byte-check は 19/19 構成で 25 欄とも HEAD と同じ([byte_check_tm32.json](byte_check_tm32.json))。2 日のラン・日の境目と日の途中からの再開・系ごとの指紋も同じ(§5)。
- **腕 W=30・10・5 も 19/19 構成で 25 欄とも W=60 と同じ**(§6)。事象の時刻の粒度が 60 秒の世界では、どの幅でも同じ結果になる(粒度を細かくするのは T2)。
- **負の対照**: 合成の世界で、窓の境目で届ける種類(TM1 の電話の形)の事象を 60 秒未満の時刻に 1 つ入れると、W で処理の順が変わる(遅れ ≤ W)。窓の中で時刻どおりに回す種類は、60 秒未満の事象と処理の中の予約の連鎖があっても、W によらず順も時刻も同じ(10-03 §7-5「窓の幅が結果を変えてはいけない」)。
- TM4 の試験の道具 `tools/instruments/batch_width_gauge.py` を作り、世界資産 300 体 × 4 つの幅 × 6 salt で最初の表を作った(差は全部 0・§7)。
- **byte-check の手順の発見(親に確かめてほしい・§5-1)**: 2-4 で経済の段階 2 が既定 on になってから、10e の手順の「HEAD の写し」では 19/19 とも final が違って見える。写しに `data/realworld/osm` の 2 本と `docs/design/rules-table.json` が要る(後者が無いと最低賃金と消費税が直書きの値に黙って戻る)。親の注意の「写しの根に本体の data への junction」だけでは足りず、規則の表も要った。10e の HEAD の写しの手順は本体 `44cfba5`(2-3c の検収 L4)で直っている(`byte_check_10e.py` の `HEAD_TREE_FILES`=規則の表と OSM の 2 本を含む)。

## 1. 作ったもの

| 項 | ファイル | 中身 |
|---|---|---|
| 1 窓と待ち行列 | `src/shibuya/engine/batching.py`(新規) | `WindowQueue`(`register`・`schedule`・`run_window`・`manifest_fields`)・幅の腕(`arm`・`set_arm`・`parse_width`・環境変数 `SHIBUYA_BATCH_WIDTH_S`)・定数(`DEFAULT_WIDTH_S = STEP_SECONDS`・`WIDTHS_S`=刻みの幅の約数・`DEFAULT_CAP_EVENTS = 2^24`・`WORLD = -1`・`KIND_STEP`・届け方 `in_window`/`boundary`・`HORIZON_STEPS = 2`)。時間の値は `core/time_consts` から(直書きなし) |
| 1 待ち行列の流用 | `src/shibuya/engine/scheduler.py` | `Scheduler.reserve_seq(n)` を足した(窓の中に予約した事象にも同じ番号の列から番号を振る口・予約の行と件数は変えない) |
| 1 進行役 | `src/shibuya/engine/systems/conductor.py` | `conduct` を窓のループに書き換え(§2)・窓の境目の名 `WINDOW_MARK = "(window)"`(試験の差の測りの帰属先)・〔検収 L1〕`declared_check` は `WINDOW_MARK` の差のうち `BW:` の鍵だけを通す(`TICK_HEAD` は前からの素通り) |
| 1 守り(検収 M1) | `src/shibuya/engine/batching.py` | `WindowQueue` の `__setattr__`・`__delattr__` の守り(3-3 の `ExperimentLayer` と同じ形・書く口は `__init__`・`register`・`schedule`・`run_window` の自分の文だけ=処理の関数と試験の境目を呼ぶ間は書けない)・種類の表は `MappingProxyType`・順位の表と持ち越しの行は書けない配列・計器は読み取り専用の辞書を置き換える形・`register` は最初の窓の後と番号か名の重複で落ちる。残る穴: 流用した `Scheduler` のメソッドを外から直に呼ぶ書き |
| 2 幅の腕 | `src/shibuya/cli.py` | `--batch-width-s {1,2,3,4,5,6,10,12,15,20,30,60}`(既定なし=環境変数か 60)・`cli.run` のランの種類の決め方に「幅が既定と違えば腕」を足した |
| 2 指紋 | `src/shibuya/engine/systems/build.py` | 幅が既定と違うときだけ設定の指紋に `batch_width_s`(既定のランの指紋は今のまま=1-8b の発話の口と同じ形) |
| 4 manifest | `src/shibuya/engine/run.py`・`manifest_sections.py` | 末尾(3-3 の `experiment` の後)に `batching`(§4)・節の表は混ざった辞書(設定 8・観測 12) |
| 4 状態台帳 | `src/shibuya/engine/state_ledger.py`・`systems/boxes.py`・`systems/state_io.py` | 行 `BW`(軸 1 diag・軸 2 discardable)・持ち主 `batching`(`OWNER_NAMES` の末尾・`Layers.batching`・`hash_owners`)・持ち主のクラスと除外の 3 行(定数・参照・窓の中だけの作業の値) |
| 5 つなぎの台帳 | `docs/design/bridging-ledger.json` | 4 行(§9-2) |
| 3 道具 | `tools/instruments/batch_width_gauge.py`(新規) | §7 |
| 試験 | `tests/engine/batching/`(新規 2 本)・`tests/tools/test_batch_width_gauge.py`(新規) | §10 |
| 凍結の表(増えた分だけ) | `tests/engine/time/manifest_keys_frozen.json`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/perception/facts/test_percept_schema.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/engine/rights/test_rights_manifest.py` | manifest の末尾の鍵 `batching`・設定の節の golden(`CONFIG_PATHS_SHA256` を `417f0818…` から `564d5c72…` に=`batching` の設定の子 8 本)・状態台帳の行の数(外の状態 113 → 114・全体 204 → 205)と鍵の並び |

## 2. 進行役の書き換え(前後の擬似コード)

前(HEAD):

```
box = build(call_args)
plan = tick_plan(box, SYSTEMS)
for T in range(t_begin, t_end):                 # 全員一斉の刻み
    ctx = TickCtx.of(T, tpd, step_s)
    probe.at(TICK_HEAD, T); scratch.reset(); events.begin_step(ctx.t_ns)
    if day_head_due(T, td): run_system(day_head)
    for spec in plan: run_system(spec)
    if day_close_due(T, td): run_system(day_close)
drain; close_final; report
```

後(3-2):

```
box = build(call_args)
queue = WindowQueue(width_s=W, start_ns=t_begin × step_ns)   # W=arm()(既定 60)
box.layers.batching = queue                                     # 状態台帳の行 BW
def on_step(t_ns, agents, seqs):                                # 刻みの事象=世界の 1 回の系の並び
    T = t_ns // step_ns
    if T + 1 < t_end: queue.schedule(t_ns + step_ns, WORLD, KIND_STEP)
    (ここから下は前の 1 回と同じ文)
queue.register(KIND_STEP, "step", on_step)
queue.schedule(t_begin × step_ns, WORLD, KIND_STEP)
while queue.head_ns < t_end × step_ns:                          # 窓の数ぶん
    queue.run_window(after_dispatch=probe.at(WINDOW_MARK, …))   # 窓の中を時刻順に
drain; close_final; report
```

`run_window` の中身(窓 [t, t+W)):

```
pending = 持ち越し ∪ 待ち行列のバケット t // W の事象      # 行=(t_ns, 体, 種類, 番号)
並べる(時刻 → 体の番号 → 種類の順位 → 番号)
while pending:                                             # 窓の中の相異なる時刻の数ぶん
    if 処理した数 ≥ 上限: 残りを持ち越して数える; break     # 安全装置・止めない
    同じ時刻の行を取り出す → 種類の続きごとに fn(t, 体の配列, 番号の配列)
    after_dispatch()                                       # 試験の境目
    処理の中で窓の中に予約した行を pending に入れて並べ直す   # TM3 (f)
頭を t+W に進める
```

- 系の呼ぶ順・刻み・系に渡す時刻は前と同じ(試験 `test_the_system_order_is_the_old_step_loop`=2 日のランを W=10 で回し、前のループの並びを組み立て直して比べた)。
- 試験の差の測り(1-0 の probe・段 B)の境目: 処理の関数を呼んだ後ごとに `WINDOW_MARK` を置く。窓の待ち行列と計器の変化(窓を閉じる・次の窓を開ける・次の刻みの事象の予約=`TICK_HEAD` の前)はこの境目に帰属し、前の系に帰属しない。系の差の帰属は前と同じ(§5 の系ごとの指紋)。既定のランでは `probe.at` は何もしない。

## 3. 窓と持ち越しの規則(T1 の宣言)

| 規則 | 中身 | 根拠 |
|---|---|---|
| 窓の頭 | ランの始め(通しのナノ秒)から W ずつ。W は刻みの幅の約数(既定 60) | 発注(TickCtx=窓の頭=今の `t_ns`)。約数に限るのは仮採用(§11) |
| 窓に入る事象 | 時刻が [t, t+W) の予約と、前の窓からの持ち越し | TM3 (f)・10-03 §7-5 |
| 窓の中の順 | 時刻 → 体の番号(世界 −1 が先)→ 種類の順位 → 予約の番号 | 発注の宣言(つなぎの台帳 `DOC-tm32-same-time-body-order`) |
| 同時刻の例外(検収 L7) | 同じ時刻の束を処理している間に同じ時刻へ足した事象は、束の残りの後(次の回)に回る(体 5・9 の束の中で体 3 を足すと 5 → 9 → 3)。挙動は変えずに規則として宣言 | 試験 `test_l7_same_time_event_added_inside_a_group_runs_after_the_rest_of_the_group`・つなぎの台帳の同じ行 |
| 処理の中の予約 | 窓の終わりより前は同じ窓で時刻順に続けて回す。窓の終わり以降は待ち行列へ。処理中の時刻より前は `ValueError` | TM3 (f) の元の選択肢の文「窓の中に収まるだけ続けて回し、収まらない分は次の窓へ持ち越す」と 10-03 §7-6「会話の往復は窓の中で続けて回す」 |
| 届け方 `boundary` | 時刻を窓の境目に切り上げ、処理中の窓の中なら次の窓の頭へ(遅れ ≤ W・計器 `boundary_delay_ns_*`) | TM1「電話は窓の境目で届け」。T1 の世界には使う種類が無い(合成の試験と道具だけ) |
| 上限 | 1 つの窓で処理する事象の数が `2^24` に届いたら、窓の中の残りを次の窓へ持ち越す(止めない・`carried`・`cap_hits` に数える) | TM3「上限は安全装置だけで、当たったら記録」。値は仮採用(つなぎの台帳 `DOC-tm32-window-cap`) |
| 同じ時刻・同じ種類 | 種類の続きを 1 回の処理(体の番号の配列)にまとめる=体ごとの Python のループは無い | 発注(窓の中の時刻順の処理は配列で) |

- 読み方の注: TM3 (f) の「持ち越し」を、草案の元の文のとおり「窓に収まらない分(窓の終わり以降の予約と上限の残り)は次の窓へ」と読んだ。処理の中で窓の中に予約した事象は同じ窓で回す。この読みでは、窓の中で時刻どおりに回す事象は W を変えても処理の順が変わらない(10-03 §7-5「窓の幅が結果を変えてはいけない」)。W で結果が変わりうるのは、境目で届ける種類(TM1)と、T2 で入る LLM のまとめ(違う会話どうしを 1 回で呼ぶ)だけになる。TM4 の差はそこから出る(「目標はメッセージの遅れ 10 秒以下」と同じ向き)。
- 逐次ループの宣言(`engine/batching.py` の docstring): 窓の数ぶん(進行役)・窓の中の相異なる時刻の数ぶん・種類の続きの数ぶん。

## 4. manifest・状態台帳・指紋・ランの種類

- manifest の末尾に `batching`(進行役を通らない結果は null)。
  - 設定: `schema`(`shibuya.engine.batching/1`)・`width_s`・`default_width_s`(60)・`step_s`・`cap_events`(16,777,216)・`order`・`world_id`(−1)・`kinds`(`{"step": {"kind": 0, "rank": 0, "delivery": "in_window"}}`)。
  - 観測: `windows`・`windows_with_events`・`events`・`dispatches`・`in_window`・`carried`・`cap_hits`・`max_events_window`・`boundary_events`・`boundary_delay_ns_max`・`boundary_delay_ns_sum`・`pending_at_end`。
  - 既定の 1 日のラン(5,000 体): 窓 1,440・事象 1,440・持ち越し 0・上限に当たった 0・終わりに残った 0。
- 状態台帳の行 `BW`(軸 1 diag・軸 2 discardable・版は上げない=どちらのハッシュにも状態のファイルにも入らない=3-3 の `X` と同じ扱い)。道筋は `batching._bw_sched`・`_bw_carry`・`_bw_head`・`_bw_meter`。除外は定数(`width_s`・`width_ns`・`cap`・`step_s`)・参照(`_bw_kinds`・`_bw_rank`)・窓の中だけの作業の値(`_bw_now`・`_bw_end`・`_bw_new`)。再開のランは進行役がランの始めの刻みから作り直す。T1 の待ち行列は次の刻みの事象だけ(刻みの番号から決まる派生)。T2 で刻みの外の事象が入ったら軸を見直す(行の注とつなぎの台帳)。
- 試験の差の測りの手間を小さくするため、待ち行列の輪は 2 刻みぶん(`HORIZON_STEPS`)にした(1 日ぶんの 1,440 の輪では 1 回の snapshot に約 1.0 ms・2 刻みぶんでは約 0.016 ms)。
- 設定の指紋: 既定(W=60)のランは今のまま。腕のときだけ `batch_width_s` が入る=幅の違う再開は「設定が親と違う」で止まる(試験)。
- ランの種類: `cli.run` で幅が既定と違えば `arm`(試験の外)。
- 進行役は組み立ての指紋の幅と今の腕が同じことを確かめる(違えば `RuntimeError`)。

## 5. 結果不変の確かめ

| 確かめ | 範囲 | 結果 |
|---|---|---|
| byte-check([byte_check_tm32.json](byte_check_tm32.json)) | `byte_check_10e.py`・19 構成・5,000 体・seed 1・1 日・テープつき。HEAD の側は `d35a9b6` の写しの src(§5-1 の写し)、作業木の側は作業木の src(`src_is_worktree` 真)・既定 W=60 | **19/19 構成で 25 欄とも同じ** |
| byte-check(親の注意の junction の形・[byte_check_tm32_junction.json](byte_check_tm32_junction.json)) | HEAD の写しの根に本体の data への junction を一時だけ置いた+`docs/design/rules-table.json`(junction は回した後に外した=本体の data は消えていない) | **19/19 構成で 25 欄とも同じ**。§5-1 の写しの形の HEAD の side とも 19/19 同じ |
| 2 日のラン([two_day_tm32.json](two_day_tm32.json)) | 5,000 体・seed 1・世界資産・既定 v3・activity・テープつき。HEAD(写し)・W=60・W=30 の通し | final `b346bb6e3ecc60af`・138,946 呼・8 つの checkpoint の behavior-hash・テープの calls と blocks の中身の sha がどれも同じ |
| 再開(同じ JSON) | 5,000 体: W=60 で刻み 1,440(日の境目)と刻み 2,211(2 日目の途中)・W=30 で刻み 2,211 で止めて再開。W=30 の日の境目からの再開は合成の世界の試験(`test_two_days_and_resume_match_the_straight_run_for_the_arm`)だけ(5,000 体のランには無い) | final はどれも `b346bb6e3ecc60af`・呼数は止めたランと再開のランの和で 138,946・再開の後の checkpoint は通しの末尾と同じ。窓の数は再開の刻みから(W=30・刻み 2,211 からなら 1,338) |
| 系ごとの指紋([probe_tm32_head_vs_w60.json](probe_tm32_head_vs_w60.json)・[probe_tm32_head_vs_w5.json](probe_tm32_head_vs_w5.json)) | 1-0 の probe(全部の刻み・系ごとの全欄の差と指紋)・合成の世界 80 体 720 刻みと世界資産 300 体 2 構成。作業木の側は行 BW を外し、両側とも日次の記録の `bridges_count` を外した | W=60 も W=5 も 3/3 構成で全部の系の指紋が同じ・最初の食い違い無し(§5-2) |
| 既存の試験 | `test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/engine/systems`(段 B・番兵)・`tests/engine/experiment`(分岐の 4 つの確認) | 通った(§10) |

### 5-1. byte-check の HEAD の写しに要るもの(発見)

- 10e の手順(`byte_check_10e.py` の docstring)の写し=src+エンジンが開く錨 3 本+budget+w6-regen+祝日の表で回すと、**19/19 構成とも final が違って見えた**(作業木の側の final は、`test_state_ledger_10b.py` の T7 の golden=既定 v3 の `b8eadcb51e8705e7` と同じだった=写しの側が違う)。
- 原因はエンジンがリポの根(パッケージの位置)から開く 2 つの物(src の差ではない)。
  1. `engine/economy_stage2.py` の ATM の表の材料 `data/realworld/osm/poi_tags_overpass_20260928.json`・`poi_opening_hours_overpass_20260907.json`(`calendar.resolve_repo_path`)。
  2. `economy/anchors.py` の最低賃金と消費税の率が読む `docs/design/rules-table.json`(`engine/rules/table.default_path`)。表が無い写しでは最低賃金が直書きの 1,226 円、消費税が 0 に**黙って戻る**(`FileNotFoundError` を受けて戻す作り)。
- 段階ごとの実測(19 構成・既定 W=60 の作業木の side と比べた final の一致の数): 錨だけの写し 0/19 → OSM の 2 本を足す 0/19 → さらに `docs/design` の表 5 本(規則の表・つなぎの台帳・知覚の契約・パターン台帳・世界カタログ)を足す **19/19**。親の注意の形(写しの根に本体の data への junction)だけでも 0/19(規則の表が無い)、junction+規則の表で **19/19**。
- 記録の形: 両側とも同じ data(本体の `data/world/v2` と OSM の 2 本)で回した。写しの side は `cwd`=作業木(`data` は本体への junction)・`PYTHONPATH`=写しの src、作業木の side は `PYTHONPATH`=作業木の src。
- 写しの組み立て方ごとの数: [byte_check_head_copy_variants.json](byte_check_head_copy_variants.json)。
- 2-4 の後の段の byte-check は、写しに `docs/design/rules-table.json` と OSM の 2 本(か本体の data への junction)を入れる必要がある。本段の土台 `d35a9b6` の `byte_check_10e.py` の docstring の手順は古いが、10e の HEAD の写しの手順は本体 `44cfba5`(2-3c の検収 L4)で直っている(`HEAD_TREE_FILES`)。

### 5-2. 系ごとの指紋

道具 [tools/probe_tm32.py](tools/probe_tm32.py)(2-1 の `probe_ec21.py` の形・`PYTHONHASHSEED=0`)。HEAD の写しの side と、作業木の W=60・W=5 の side を比べた。

| 構成 | final | entries(HEAD / W=60 / W=5) | 系の数 | 全部の系の指紋 | 最初の食い違い |
|---|---|---|---:|---|---|
| 合成の世界 80 体 720 刻み(記憶・関係・店の記憶) | `d5c5fde554f17dea` | 7,051 / 7,051 / 7,051 | 19 | 同じ(W=60・W=5) | 無し |
| 世界資産 300 体・既定 v3 | `3dfb30508605d14a` | 15,600 / 15,600 / 15,600 | 19 | 同じ(W=60・W=5) | 無し |
| 世界資産 300 体・記憶+関係 | `5cb03e3afb3d00f7` | 17,703 / 17,703 / 17,703 | 21 | 同じ(W=60・W=5) | 無し |

- 窓の境目 `(window)` に帰属する差は行 BW の道筋だけなので、行 BW を外すと entries に載らない(=系の境目の並びと各系の差は HEAD と同じ)。W=5 は窓が 12 倍(1 日 17,280)でも同じ。
- 1 回目の比べは 3/3 構成とも close_final の差の digest が違った。ランの終わりの境目ごとに欄を並べて調べると、違うのは日次の記録の `bridges_count`(つなぎの台帳の active の行の数 337 → 341=本段で 4 行足した)だけだった。ec21 と同じく、両側の日次の記録からこの欄を外して比べ直した(上の表)。
- 試験 `test_window_changes_are_attributed_to_the_window_mark_and_fingerprints_do_not_move` が同じことを合成の世界(W=60 と W=10)で毎回確かめる(宣言の外の書き 0・行 BW を書いた境目は `(window)` だけ・`(window)` の差は行 BW だけ・それ以外の entries と指紋は幅によらず同じ)。

## 6. W の腕で同じことの表

byte-check の 19 構成を、環境変数 `SHIBUYA_BATCH_WIDTH_S` で幅を変えて回し、既定 W=60 の side と比べた(どちらも作業木の src・最終のコード)。

| 幅 W | 窓の数(1 日) | 19 構成で 25 欄とも W=60 と同じ | 比べの JSON |
|---|---:|---|---|
| 60(既定) | 1,440 | HEAD と 19/19 | [byte_check_tm32.json](byte_check_tm32.json) |
| 30 | 2,880 | 19/19 | [byte_check_tm32_w30_vs_w60.json](byte_check_tm32_w30_vs_w60.json) |
| 10 | 8,640 | 19/19 | [byte_check_tm32_w10_vs_w60.json](byte_check_tm32_w10_vs_w60.json) |
| 5 | 17,280 | 19/19 | [byte_check_tm32_w5_vs_w60.json](byte_check_tm32_w5_vs_w60.json) |

- 19 構成の final(W によらず同じ): w6_v3_default `b8eadcb51e8705e7`・w6_v3_activity_off `c88ba9104f45f897`・w6_v1_default `e1288e092ddaca86`・w6_golden_null_arm `19ee17b1b1caf44c`・v3_mem_rel `768b2262e3b0999e`・v3_classical `ca25874a5e4acb79`・v3_classical_mem_rel `9dd9d5684891b57c` ほか(全部は JSON)。
- 試験(合成の世界・`tests/engine/batching/test_conductor_windows.py`): W=30・10・5・1 で、系の呼ぶ順(刻み・系の名・系に渡した時刻)・final・呼数・全 checkpoint の 2 本のハッシュが W=60 と同じ。窓の数は刻みの数 × 60/W。世界資産 300 体の W=10 も同じ。2 日の W=30 の通しと、日の境目と日の途中からの再開も同じ。
- 負の対照(`tests/engine/batching/test_window_queue.py`): 60 秒未満の時刻の事象と処理の中の予約の連鎖を入れた合成の世界で、窓の中で時刻どおりの種類は W=60・30・20・10・5・1 で処理の順も時刻も同じ。そこに境目で届ける種類の事象を 1 つ(80 秒)入れると、W=60 では 120 秒(次の窓の頭)に届いて 95 秒の事象と順が入れ替わる・W=30 では 90 秒・W=10 では 80 秒(時刻どおり=正解と同じ)。遅れの最大は 40・10・0 秒(W を細かくすると減る)。

## 7. TM4 の道具(`tools/instruments/batch_width_gauge.py`)の表の形

- `run`: 幅の列 × salt の列で `cli.run` を子プロセスで 1 本ずつ回し(環境変数で幅・母集団の seed は固定=共通乱数)、1 本 1 行の JSONL(final・呼数・行動の件数・manifest の `batching`・境目の遅れの最大[秒])。
- `table`: 正解の幅(既定 60=T1 の世界の事象の粒度)との対の差を幅ごとに。列は final が同じ salt の割合・指標ごとの「差/salt の幅/(g) 中か」・(f) 単調か・既定の幅の候補(記述=合否は書かない)。salt の幅は `tools/c7/salt_compare.paired_stats` の `width_base`(正解の腕の salt 間の幅)。遅刻と待ち合わせの成否は**置き場**(計る口がまだ無い=null と注)。
- 最初の表(世界資産 300 体・既定 v3・母集団の seed 1・salt 1〜6・幅 60・30・10・5・[batch_width_gauge_tm32.md](batch_width_gauge_tm32.md)・[JSON](batch_width_gauge_tm32.json)):

| 幅 W[秒] | salt の数 | final が同じ | 呼数 差 / salt の幅 / (g) | 行動の件数 差 / salt の幅 / (g) | 境目の遅れの最大[秒] | 遅刻 | 待ち合わせ |
|---|---|---|---|---|---|---|---|
| 60(正解) | 6 | 1 | 0 / 31.38 / 中 | 0 / 830.9 / 中 | 0 | 置き場 | 置き場 |
| 30 | 6 | 1 | 0 / 31.38 / 中 | 0 / 830.9 / 中 | 0 | 置き場 | 置き場 |
| 10 | 6 | 1 | 0 / 31.38 / 中 | 0 / 830.9 / 中 | 0 | 置き場 | 置き場 |
| 5 | 6 | 1 | 0 / 31.38 / 中 | 0 / 830.9 / 中 | 0 | 置き場 | 置き場 |

  (f) 単調=はい(差が全部 0)。既定の幅の候補(記述)=60 秒(T1 の世界ではどの幅でも差が 0 なので一番大きい幅)。T2 で事象の粒度が細かくなったら、正解の幅をその粒度に下げて同じ表を作る。
- (g) の幅に正解の腕の salt 間の SD を使うのは実装役の構成(未リサーチ=expedient・道具の docstring)。salt_compare の「幅」は対の差の SD なので、差が全部 0 だと幅も 0 になる。対の差の幅 `paired_width` も並べた。

## 8. 性能

道具 [tools/perf_tm32.py](tools/perf_tm32.py)・[perf_tm32.json](perf_tm32.json)。

- 1 日のラン(`w6_v3_default`・5,000 体・テープつき)を HEAD の写し・W=60・W=5 の順に交互に 3 回ずつ、1 本ずつ回した。ランの壁時計の中央値は HEAD 50.07 秒(刻みあたり 34.8 ms)・W=60 50.40 秒(35.0 ms・+0.7%)・W=5 45.65 秒(31.7 ms)。同じ側の 3 回の幅が 44〜82 秒あり(同じ機械で並行の段の作業が動いていた)、前後の差はこの揺れの中で読めない。final と呼数は 9 本とも同じ。
- 窓の待ち行列だけの手間(系を呼ばない空の刻みの事象で 1 日ぶん): W=60 で刻みあたり 43〜63 µs(静かなときと負荷のあるとき)・W=30 で 65 µs・W=10 で 74 µs・W=5 で 89 µs・W=1 で 178 µs(負荷のあるときの値)。刻みあたり約 35 ms の 0.2%(W=60)〜0.5%(W=1)。予算 P4(逐次ループ)の宣言は窓の数ぶん・窓の中の時刻の数ぶん・種類の続きの数ぶん(§3)。
- 試験の差の測り(段 B)の手間: 窓の境目を処理の後ごとに 1 つ足した(既定は刻みに 1 つ=1 刻みの境目 27 前後に 1 つ)。待ち行列の輪を 2 刻みぶんにして、行 BW の 1 回の digest を約 1.0 ms から約 0.016 ms にした(§4)。

## 9. つなぎの台帳と宣言

### 9-1. 仮採用(10-13b §0-3=既存の決定と原文から答えが一つに決まらない所・戻せる形)

1. 幅は刻みの幅の約数だけ(60 より細かい 12 通り)。60 より大きい幅は入れていない(刻みの事象が窓の頭に乗らなくなる=`TickCtx` の時刻が窓の頭でなくなる)。
2. 同じ時刻の順は体の番号順(世界 −1 が先)→ 種類の順位 → 予約の番号(発注の宣言)。運用設計書 §2.5 の順(時刻・種類の順位・blake3 の塩・体)とも、TM7 (d) の乱数の結び方とも違う。T1 の世界では窓に刻みの事象 1 つだけなので効かない。
3. 上限の値 2^24(1 つの窓の事象の数)。当たったら持ち越して数える・止めない。
4. 処理の中で窓の中に予約した事象は同じ窓で回す(§3 の読み方の注)。
5. 届け方 `boundary`(TM1 の電話)を種類の属性として入れた(T1 の世界では使わない・負の対照と TM4 の道具の「メッセージの遅れ」の列のため)。
6. manifest の `batching` は混ざった辞書(幅・上限・順・種類は設定、計器は観測)。発注の「観測」を、計器は観測・ランの前に決まる値は設定と読んだ(設定の節の golden を更新)。
7. 待ち行列の輪の地平 2 刻みぶん(`HORIZON_STEPS`)。
8. 窓の待ち行列の行 `BW` は軸 1 diag(発注どおり)。T1 では中身が刻みの番号から決まる派生なので挙動の読み手はいない、と読んだ。

### 9-2. つなぎの台帳(4 行・remove_at T2・`declared_in` はこの記録)

| id | 中身 | remove_basis |
|---|---|---|
| `DOC-tm32-event-time-60s` | 待ち行列に入る事象は刻みの事象だけ=事象の時刻の粒度は 60 秒・W は刻みの幅の約数だけ=幅の腕は今は結果に効かない | plan(TM6 の T2) |
| `DOC-tm32-same-time-body-order` | 同じ時刻の順は体の番号順(宣言) | inferred |
| `DOC-tm32-conversation-not-batched` | 「1 つの会話の中はまとめない」(TM3)を、会話の番が刻みに 1 回であることで自動で満たす=検査は T2 で足す | plan(TM3・TM6 の T2) |
| `DOC-tm32-window-cap` | 上限 2^24(安全装置)の値 | inferred |

つなぎの台帳の active の行は 337 → 341(manifest の `bridges_count`・日次の記録の `bridges_count` もこの分だけ動く=byte-check の 25 欄の外)。

## 10. 試験

新しい試験 43 本(data 不要 42・世界資産 1)。

- `tests/engine/batching/test_window_queue.py`(20 本・合成だけ・約 1 秒): 窓の中の順・同じ時刻と種類の配列・処理の中の予約(TM3 (f))・過去への予約・形の誤り・幅を変えても同じ(W=30・20・10・5・1)・負の対照(境目で届ける種類)・境目の次の窓の頭・上限と持ち越し・0 の遅れの連鎖でも止まる・幅の検査・腕・予約の番号・manifest の欄と節の表。
- `tests/engine/batching/test_conductor_windows.py`(16 本・約 20 秒・6 並列): 既定の窓と系に渡す時刻・W=30・10・5・1 の同じ・前のループの並び・2 日と再開(腕 30 秒)と幅の違う再開の拒否・指紋・ランの種類・段 B の帰属と系ごとの指紋(W=60 と W=10)・CLI(環境変数より強い・約数の外は使い方の誤り・環境変数の誤りは import で落ちる)・世界資産 300 体。
- `tests/tools/test_batch_width_gauge.py`(7 本): 合成の記録から表・salt の幅=`width_base`・差が大きい幅は候補にならない・final の食い違い・入力の誤り・`table` の CLI・子プロセスの 1 本の記録の形。
- 発注の範囲(`tests/engine/batching`・`tests/tools/test_batch_width_gauge.py`・`tests/engine/systems`・`tests/engine/time`・`tests/engine/events`・`test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/engine/experiment`・`tests/llm`・`tests/engine/test_scheduler*.py`・`tests/engine/bridging`・印で絞らない=slow を含む・8 並列): 1 回目 964 passed・6 failed(12 分 45 秒)。落ちた 6 本は凍結の表 3 本(manifest の末尾の鍵・状態台帳の行の数・設定の節の golden=本段で更新)・記録の README がまだ無かった 1 本(つなぎの台帳の `declared_in`)・名前の衝突 3 本(`WindowQueue` の読み口の名 `meter` が状態台帳の外の道筋の属性 `meter`=1-9・1-8・1-8b と同じ名 → `window_counts` に改名)。直した後に落ちたファイルと `tests/engine/batching` を回し直して **117 passed**。
- 全体(`-m "not gpu and not slow" -n 8 --dist loadfile --ignore=tests/c7`・作業木): **4,944 passed・4 failed・1 xfailed**(16 分 27 秒)。落ちた 4 本のうち 3 本は manifest の末尾の並びを凍結した試験(`tests/perception/facts/test_percept_schema.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/engine/rights/test_rights_manifest.py`=末尾に `batching` を足した分だけ直した→ 3 ファイル **34 passed**)。残りの 1 本は既知の `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(作業木の `data` が本体への junction=T0・2-4 の記録と同じ)。`tests/c7` は回していない。
- `lint-imports`: 5 契約とも守られている(230 ファイル・作業木の src)。

## 11. 触った共有ファイル(並行の 3-5 との突き合わせ用)

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/systems/conductor.py` | `conduct` の本体(刻みのループ → 窓のループ)・`WINDOW_MARK`・docstring(本段だけが触る約束) |
| `src/shibuya/engine/systems/boxes.py` | `OWNER_NAMES` の末尾に `batching`・`Layers` の末尾に `batching: Any = None` |
| `src/shibuya/engine/systems/table.py` | 触っていない(新しい系は無い) |
| `src/shibuya/engine/systems/state_io.py` | `hash_owners` の末尾に `batching` |
| `src/shibuya/engine/systems/build.py` | 発話の口の指紋の後に 4 行(幅の腕のときだけ指紋に足す) |
| `src/shibuya/engine/state_ledger.py` | 行 `BW`(`_EXT` の末尾=2-3 の `M0L` の後)・`OWNER_CLASSES` の末尾・`EXCLUDED` の末尾 3 行・版の注 1 行・docstring の一覧 |
| `src/shibuya/engine/run.py` | import 1 行(`_BATCHING`)・manifest の末尾に `batching`・docstring 2 行 |
| `src/shibuya/engine/manifest_sections.py` | `PATHS` の末尾に `batching` の混ざった辞書 |
| `src/shibuya/engine/scheduler.py` | `reserve_seq` を足しただけ |
| `src/shibuya/cli.py` | `--batch-width-s`(`--experiment` の前)・`_batch_widths`・`main` の腕の置き方・`cli.run` のランの種類の決め方に 1 条件 |
| `docs/design/bridging-ledger.json` | 末尾に 4 行 |
| 凍結の表 | §1 の最後の行の 8 本(どれも末尾に足しただけ・数を直しただけ) |

## 12. 限界・空欄・親に確かめてほしいこと

- 窓の幅は T1 の世界では結果に効かない(事象の粒度が 60 秒)。TM4 の試験が意味を持つのは T2 から。道具は表の形と 0 差の最初の表まで。
- 遅刻と待ち合わせの成否は計る口が無い(置き場)。
- 同時刻の順(体の番号順)・上限の値・幅を約数に限ること・処理の中の予約を同じ窓で回す読み方は仮採用(§9-1)。T2 の発注で決め直す。
- 待ち行列の行 `BW` は軸 2 discardable。T2 で刻みの外の事象(会話の番・届くメッセージ・体の変化の予約)が入ったら required にして状態のファイルに入れる必要がある(版上げ)。
- 土台 `d35a9b6` の `byte_check_10e.py` の docstring の HEAD の写しの手順は 2-4 の後は足りない(§5-1)。10e の HEAD の写しの手順は本体 `44cfba5`(2-3c の検収 L4)で直っている(`HEAD_TREE_FILES`)=本段は直していない。
- 作業用の置き場 `_bc/`(作業木の直下)は `.gitignore` に無い。親が消してほしい(テープ・side の JSON・HEAD の写し 2 つ。junction は外した)。

## 13. 検収の後の直し(検収役=条件つき受入)

| 番号 | 直したこと | 確かめ |
|---|---|---|
| 中 M1 | `WindowQueue` に実行時の守り(`__setattr__`・`__delattr__`=3-3 の `ExperimentLayer` と同じ形。書く口は `__init__`・`register`・`schedule`・`run_window` の自分の文だけで、処理の関数と試験の境目を呼ぶ間は書けない)。種類の表は `MappingProxyType`・順位の表と持ち越しの行は書けない配列・計器は読み取り専用の辞書を置き換える形。`register` は最初の窓が始まった後(処理の関数の中を含む)と番号か名の重複で落ちる | 負の対照 3 本(外からの代入 11 通り=欄の付け替え・新しい欄・`_bw_kinds`・`_bw_rank`・`_bw_meter`・`_bw_sched` ほか/表の中身の書き換え 4 通り/途中の `register`・名の重複・処理の関数の中の代入)。守りを外した写し(`__setattr__`・`__delattr__` と `register` を前の形に戻す)では M1 の 14 本が全部落ち、ほかの 22 本は通る |
| 低 L1 | `declared_check` は窓の境目 `(window)` の差のうち `BW:` の鍵だけを通す(`TICK_HEAD` は前からの素通り=docstring に理由)。段 B の `_conduct_checked` も同じ関数を使う | 試験 2 本(鍵ごとの判定/`SHIBUYA_SYSTEMS_CHECK=1` で窓の境目の直後に診断の積算を書き換えると「宣言の外の変化」で落ち、書き換えないランは通る)。前の判定(系でない名は全部通す)に戻すと同じランは落ちない(負の対照・調べ用のスクリプトで確かめた) |
| 低 L2 | 時間の直書きを `core/time_consts` から: 道具 `batch_width_gauge.py` の `DEFAULT_REF_WIDTH = STEP_SECONDS`・子プロセスの `/ NS_PER_SECOND`・記録の道具 `perf_tm32.py`(`STEPS_PER_DAY`・`NS_PER_STEP`)・`two_day_resume_tm32.py`(`STEPS_PER_DAY`)・試験の `TPD = STEPS_PER_DAY` | 道具の試験 7 本・道具の読み込みの確かめ |
| 低 L4 | §0・§5-1・§12 に「10e の HEAD の写しの手順は本体 `44cfba5`(2-3c の検収 L4)で直っている(`HEAD_TREE_FILES`)」 | — |
| 低 L5 | §5 の再開の行を直した(5,000 体の再開は W=60 の日の境目と日の途中・W=30 の日の途中だけ。W=30 の日の境目の再開は合成の世界の試験だけ) | — |
| 低 L6 | 試験 2 本: 輪(2 刻み)の外の予約が遠未来の heapq を通る道(最初の予約の 3 つ以上が heapq・順と時刻が W=60・30・10・5・1 で同じ)/上限に当たった後の `manifest_fields` の `carried`・`cap_hits`(と `events`・`pending_at_end`)の窓ごとの値 | 通った |
| 低 L7 | 同じ時刻の束を処理している間に同じ時刻へ足した事象は束の残りの後に回る(5 → 9 → 3)を規則として §3 とつなぎの台帳の行 `DOC-tm32-same-time-body-order` に書いた(挙動は変えない)。`run_window` の docstring にも | 試験 1 本(5 → 9 → 3・処理は 2 回) |

- 親が書くもの(触っていない): L3(10e の `SWITCH_ENV` に `SHIBUYA_BATCH_WIDTH_S`)・L8(P4 の性能=予算の宣言の行)・L9(`_bc/` は取り込みに載せない)。検収役の問い 3(TM4 (g) の salt 間のばらつき=正解の腕の `width_base`)は expedient の宣言のまま。
- byte-check(直しの後・既定 W=60・4 構成=w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel・HEAD の写しの条件は前と同じ・[byte_check_tm32_review4.json](byte_check_tm32_review4.json)): **4/4 構成で 25 欄とも同じ**(final は §6 の値と同じ)。
- 試験(直しの後): 新しい試験は 61 本(`test_window_queue.py` 36・`test_conductor_windows.py` 18・`test_batch_width_gauge.py` 7)。範囲(`tests/engine/batching`・`tests/engine/systems`・`tests/engine/time`・`tests/tools/test_batch_width_gauge.py`・`test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`tests/engine/bridging`・8 並列・slow を含む): **421 passed**(11 分 53 秒)。`lint-imports` は 5 契約とも守られている(230 ファイル)。
