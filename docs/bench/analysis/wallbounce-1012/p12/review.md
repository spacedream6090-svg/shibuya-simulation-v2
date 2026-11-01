# 第 1 期 1-2 知覚の分離 の検収の記録(検収役)

- 検収役 Opus 5.5。実装は見ていない。対象は作業木の枝 `1-2/percept`(土台 `136fdbb`)の未 commit の差分(変更 21 ファイル+新規 `src/shibuya/perception/facts.py`・`tests/perception/facts/`・記録 `p12/`)。
- 正: 口の約束 `v2-foundation-contracts-2026-10-13.md` の「1-2 知覚の分離」と冒頭の共通の約束・実装役への発注文・1-0/T0/1-3 の規則。
- 比べた HEAD は本体 HEAD `bf00c2f`(1-4・1-6 を取り込み済み)。`src/shibuya/perception/renderer.py` の blob は `136fdbb` と `bf00c2f` で同じ(sha256 `b1d82c4f…586cbfe`)。
- 作業用の道具とラン(4 構成の byte-check・描画の書き出し・艦隊のテープの再生・負の対照)は作業木の中の一時の置き場で回し、終わってから消した。このフォルダに足したのは本書だけ。

## 判定: 条件つき受入

描画のバイト不変・係数の削除・結果不変(4 構成と 2 構成 × 300 体の独立の比べ)は確かめられた。ただし約束 (3)「`Percept` は刻みの中の一時(軸 2 discardable)」が、艦隊で録ったテープの再生では破れていて、HEAD と full-hash が変わる(M1)。M1 を直し、その試験を足すことが受入の条件。

## 欠陥(重さ順)

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `src/shibuya/engine/llm_bridge.py` の `BridgeResult.percept`(欄の追加)・`engine/systems/decide.py:122`(`replay_inbox.setdefault(...).append((False, res))`) | 艦隊で録ったテープの再生(D-58)では、応答が後の刻みに届く `BridgeResult` を `run_day.replay_inbox`(状態台帳 O96=軸 2 required=full-hash と状態のファイルに入る)に置く。1-2 で `BridgeResult` に欄 `percept` を足したため、(a) 本物の描画では `Percept` がその刻みの外まで残り、O96 を通って状態のファイルに入る(約束 (3) 違反)。(b) 欄が None でも dataclass の直列化(`state_hashes._feed` は欄の数と名を流す)が変わる。実測(下の 6)= 合成 120 体・40 刻み・4 刻みごとの checkpoint で、behavior-hash と final は HEAD と 10/10 同じだが、full-hash は 6/10 の checkpoint(到着待ちが空でない刻み)で違う。描画がスタブでも本物でも同じ。直列化で `percept` の欄だけを飛ばすと 10/10 が HEAD とそろう(原因はこの欄だけ)。19 構成の byte-check は mock で到着待ちが空なので捕まらない | `BridgeResult`(と鏡の `FleetBridgeResult`)に欄を足さない。`Percept` は刻みの中だけの道で decide に渡す(例: `RenderedPrompt`/`Rendered` にだけ持たせ、`LLMBridge.call` は刻みの中の一時の属性に置き、状態台帳の除外か discardable の行に載せる)。試験を 2 本足す: 艦隊のテープの再生で checkpoint の full-hash が HEAD の写しと同じ(`tests/engine/test_tape_deferred.py` の偽 vLLM の形で回せる)/`replay_inbox` に `Percept` が入らない |
| L1 | 低 | 記録 `p12/README.md` | §1 の表は「試験 4 本(87 件)」、§0・§7 は 85 件。収集は 85 件(5+8+23+49)。§8 の凍結の表の行で `manifest_keys_frozen.json` が 2 回出る | 数を 85 にそろえる |
| L2 | 低 | `run.py` の `percept` の注釈・`manifest_sections.py` の `"percept": _C` の注釈 | 「係数の腕」が残る(腕は消した) | 注釈から消す |
| L3 | 低 | `renderer.py` の `_b3_cache` の型注釈(`dict[tuple[object, int], bytes]`) | 値は 1-2 で語の組に変わった | 注釈を直す |
| L4 | 低 | `engine/resolve.py:2749`・`perception/state.py:102` の docstring | 「p_notice の m_load が読む」が残る(m_load は消した) | 文を直す |
| L5 | 低 | `engine/systems/report.py:79-80` | `p_see_activity_identity`・`p_see_activity_table` を読むが使わない(死んだ局所) | 消すか、1-0 の割り当てとして残すなら注釈 |
| L6 | 低 | `Renderer.perceive(…, tick, …)` | 新しい口の引数名に凍結の名 `tick` を使う(`render` と同じ引数にそろえるため)。T0 の「tick を新しい識別子に入れない」とは食い違う | 親の判断(残すなら記録の仮採用に・直すなら `step`) |
| L7 | 低 | 記録 §10・P4(性能予算) | 描画 1 回 +14 µs(+14%)は測ってあるが、P4 の「ms/シミュ分@基準規模」の宣言と性能の回帰の試験が無い。壁時計の古典+記憶+関係は HEAD 58.1・57.1 秒/後 63.2・62.5 秒で 2 回とも +9%(記録は負荷の揺れとする)。cProfile の全体 44.83 秒と 44.79 秒は、描画の累計 +1.3 秒と合わない(揺れが 1 秒より大きい) | 静かな機械で 1 回測り直すか、宣言の行を足す |
| L8 | 低 | `test_percept_is_scratch.py` の「刻みの外で残らない」 | 残っていないかを描画の属性だけで見る。橋の結果と到着待ち(M1 の道)を見ていない | M1 の試験で補う |
| L9 | 低 | `Percept.t_ns`・`TimeView.tod_s` | 世界内日時から作る(`(日時 − 原点) // 1 µs × 1,000`・時分秒)。`TickCtx.t_ns`・`TickCtx.tod_s`(T と幅から)と、開始が 0 時で暦が線形な今のランでは同じ値になるが、同じ値だと確かめる試験が無い | `ctx.t_ns` との一致の試験を 1 本足すか、T から作る |

## 1. 結果不変 ✓

- 実装役の byte-check の JSON 4 本を読んだ: `byte_check_p12.json`(腕があった時・既定 on)・`byte_check_p12_coefs_off.json`(腕 off)・`coefs_measure_head_copy.json`(HEAD の写しの係数を 1.0)はどれも 19 構成・25 欄とも同じ(動いた欄 0)。`byte_check_p12_coefs_removed_4cfg.json`(係数を消した後)は 4 構成・25 欄とも同じ。どの JSON も両側が `src: 写し`(`--src` を渡した=作業木の src を読んだ)。
- 自分の byte-check(4 構成 `w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`・5,000 体・seed 1・1 日・`10e/byte_check_10e.py`): A=本体 HEAD `bf00c2f` の src の写し・B=作業木の最後の src(`--src` で渡した=`src_is_worktree` 真)。**4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`=記録と同じ・full_last も同じ)。
- 注意(手順の落とし穴): 作業木の根で `--src` を渡さずに side を回すと、共有の venv の editable install が本体の src を読む(`src_is_worktree` 偽)。最初の 1 回でこれを踏んだので回し直した。記録 §12 の手順は `--src src` を渡しているので正しい。
- 2 日のラン(`two_day_p12.json`): final `912446bd2b42b6ab`・140,913 呼・calls/blocks の sha が同じ(読んだだけ)。系ごとの指紋(`probe_p12.json`)も読んだだけ。

## 2. 口と約束 ✓(約束 (3) は M1 を除いて)

- 口: `perception/facts.py` の `Percept`(凍結・slots・25 欄)。見えた物 `SeenObject`(id・種類・距離・向き)・見えた人 `SeenPerson`(id・向き・行為)・音 `Sound`(段)・時刻の見方 `TimeView`(`tod_s`・`day_kind` ほか)・体の段 `BodyView`。欄だけの 9 欄(`eye_dir`・`mind_dir`・`belongings`・`tool_state`・`watched_by`・`heard_speech`=`EventRef` の列・`nearby_change`・`acquaintance_seen`・`prediction`)は既定 None。口の約束と 10-13b §4-2 の名とそろう。`renderer` は `perceive`(状態 → `Percept`)と `render_percept`/`draw`(`Percept` → 文)に分かれ、`render` は 2 つを続けて呼ぶ。
- 約束 (1) 描画のバイト不変: 試験 (A)(合成の場面 13 種)と (B)(19 構成 × 300 体)・道具(19 構成 × 1,000 体・201,536 描画・差 0)・下の 6 の独立の比べ。✓
- 約束 (2) 先に測る: `coefs_measure_head_copy.json`(HEAD の写しで係数を 1.0・19/19 同じ)。✓
- 約束 (3) 刻みの中の一時: `TickScratch.percepts`・行 P・段 C の守りは ✓。艦隊のテープの再生の道で破れる(M1)。
- 受入の試験: `test_percept_schema.py`・`test_render_from_percept_bytes.py`・`test_coef_removed.py`(名は発注文どおり `test_coef_removed_or_armed.py`)・`test_percept_is_scratch.py`・byte-check。全部ある。
- 〔決定〕「最初に測る・動けば ▲」: 動かなかったので消した(親の判断)。▲ ではない。✓

## 3. 発注文の各項

| 項 | 判定 | 根拠 |
|---|---|---|
| 1 `facts.py` の `Percept` | ✓ | 欄・凍結・空の欄。`TickScratch` の欄+行 P |
| 2 描画の分離・バイト不変・残した直接読みの一覧 | ✓ | 記録 §3。下の 4 の実行時の確かめで、`render_percept` は個体 SoA と層の口を読まない(キャッシュの外れの道も) |
| 3 係数を先に測る・動かなければ消す | ✓ | 測り(19/19 同じ)→ 消した。src に 0.46・0.49・1.39 のリテラル 0(AST・負の対照は下の 4)。`--p-see-activity`・`--percept-coefs`・`SHIBUYA_PERCEPT_COEFS` は src に無い。manifest の `p_see_activity` は欄を残して null。`run_day(p_see_activity=…)` は None 以外で `ValueError`(試験あり) |
| 4 判断の入力に載せる形 | ✓ | `PerceptCarrier`(`ctx.percept`)・`prediction`・`with_prediction`(型だけ) |
| 5 manifest | ✓ | `percept`(版・欄の数 25・名・空の欄 9)を TM9 の前に。既存の欄は `p_see_activity` の値(段の決定)のほか不変 |
| 記録 | △ | 中身は揃う。試験の数が 2 か所で食い違う(L1) |
| できなかったことの申告 | ✓ | 削除の後の全体の試験と 19 構成の byte-check は回していないと申告どおり(4 構成と指定の集合だけ) |

## 4. 守り ✓

- 書く口: `TickScratch.percepts` を書く系は decide だけ(`writes.scratch`)。ほかの系が書くと段 C が `AttributeError`(試験 `test_stage_c_stops_a_write_from_another_system`)。値は `MappingProxyType`・中身は凍結の dataclass。`Percept` の欄への代入は `FrozenInstanceError`。
- 描く側が状態を読まないこと(独立に確かめた): 合成の場面 13 種 × 4 刻み × 120 体(6,240 描画)で、`render` の後に描画の `agents` を「触ると落ちる物」に、層の口 8 つ(知人・会話の参加者・閉店・想起・天気 3 つ・暦)を「呼ぶと落ちる関数」に差し替え、B1/B2/B4/単一ランキングのキャッシュと B3 の文の覚えを空にしてから `render_percept` を呼んだ=落ちた 0・文の違い 0。対照: 同じ差し替えで `render`(=`perceive` を通る)は `agents.cell` で落ちる。
- 係数のリテラルの AST の検査の負の対照(自分で植えた): src の写しに `0.46`・`0.49`・`1.39` をそれぞれ別の形(組の要素・既定の引数・辞書の値)で植えると試験の関数が 3 つとも落ち、植えない写しでは通る。
- 空振りだった試験の的(`test_nearby_vectorized.py`): 作業木の src で 100 回描くと、旧の的 `_nearby_items` は 0 回・新しい的 `_nearby_people` は 100 回呼ばれる=旧の試験は 1-2 の後では空振り、直した試験は効く。試験の中にも呼ばれた回数の確かめと負の対照(知人の印を反転すると指紋が変わる)がある。✓

## 5. 宣言と凍結 ✓

- `SYSTEMS` の decide に `scratch_w=parse_errors percepts`・`reads` に `scratch.percepts`。`SCRATCH_FIELDS` 34 → 35。状態台帳に行 P(軸 1 no・軸 2 discardable・道筋なし)・除外に `renderer.day_kind_fn`(参照)。消した属性(`signage_by_kind`・`signage_effective_p`・`p_see_activity`・`_p_see_mult`・`_p_see_identity`・`fam_layer.p_see_fn`)を台帳から消した。版は上げない(行 E と同じ理由・仮採用)。
- 凍結の表: `manifest_keys_frozen.json` は `percept` を 1 つ足しただけ。`test_env_and_sections_10f.py` は `P12_KEYS`・末尾の並びの式・`CONFIG_PATHS_SHA256`(`percept` を足し `p_see_activity` の子の道筋 4 つを欄そのものに)。`test_state_ledger_10b.py` は数(外 97 → 98・全体 188 → 189)と行 P。`local-assignment.json` は `percepts` を `note` つきで足し、`n_locals`・`kinds` は HEAD のまま。どれも増えた分と段の決定から動く所だけ。
- manifest の既存の欄の値: `p_see_activity` が辞書 → null(段の決定)。ほかは byte-check の `frozen_sources` ほかで同じ。

## 6. 同値と独立の再計算

- 実装役の試験 (A)(B) は「同じプロセスの中の HEAD の描画の写し(双子)」と比べる。写し `tests/perception/facts/head_renderer_136fdbb.py` の sha256 は `b1d82c4f05b90d36172d7cf8dc1b998e2fd8f599d3130df86b99981ac586cbfe`=本体の `136fdbb`・`bf00c2f`・枝の HEAD の `renderer.py` の blob と一致(自分で計算)。
- **独立の再計算(双子を使わない)**: src を丸ごと入れ替えた 2 本のラン(本体 HEAD `bf00c2f` の写しと作業木)を別のプロセスで回し、ランの中の全部の描画(刻み・体・`prompt_hash`・本文の sha256・ブロックごとの sha・トークン・群のトークン・切り詰め・想起の行・知人の列)と描画の計数 17 種を書き出して比べた。2 構成 × 300 体 × 1 日(1,440 刻み):

| 構成 | 描画 | 違い | 計数 | final |
|---|---|---|---|---|
| `v3_classical_mem_rel` | 3,730(956 刻み・記憶の行 3,227) | 0 | 同じ | `e1ef333f7320c318`(両側) |
| `w6_v1_edge_plateau` | 2,477(635 刻み) | 0 | 同じ | `c3a232155dbe23fd`(両側) |

- **M1 の再計算**: 偽 vLLM 2 台(`tests/llm/test_fleet.py` の `FakeVLLM`・受理枠 8・遅れ 0.02 秒)で合成 120 体・40 刻み・語彙 v3・予算 30 を作業木の src で録り、同じテープを HEAD の写しと作業木の src で再生(4 刻みごとの checkpoint)。到着待ちに入った結果 200 件(本物の描画では 200 件とも `Percept` つき)。behavior-hash 10/10 同じ・final 同じ・full-hash は刻み 3・7・11・31・35・39 で違う(6/10)。作業木の再生で直列化だけ `BridgeResult.percept` の欄を飛ばすと 10/10 同じ。

## 7. 試験

- 指定の集合(`tests/perception tests/engine/systems tests/engine/time tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_familiarity.py tests/llm/test_fleet_contract.py tests/test_cli.py tests/engine/test_env_and_sections_10f.py`・`-n 2 --dist loadfile -m "not slow"`・作業木): **719 passed**(7 分 38 秒・data が無くて飛ばした 0 件・ほかの理由で飛ばした 0 件)。実装役の記録 §7 の 719 と同じ。新しい試験は収集で 85 件。M1 を捕まえる試験はこの集合に無い
- `lint-imports`(作業木の src): 5 kept・0 broken(190 ファイル)。
- 秘密の検査(`tools/scan_secrets.py`・変えたファイルと新しいファイル): CLEAN。改行は新しいファイルと記録がどれも LF。

## 8. 抜け道と記録

- (a) 描画のバイト不変: 上の 1・6。✓
- (b) 係数の削除: 上の 3・4。注視のゲートの抽選は `gate_stage1(1, p_see, (刻み, 体, 看板))` の 1 つの値だけ(試験 `test_signage_gate_is_one_p_for_every_activity`)。乗数の表が全部 1.0 だった HEAD と同じ抽選・同じ乱数の列であることは、試験 (A) の `p_see_gate` の場面(p_see 0.3・活動の列あり)で抽選の計数まで双子と同じことと、byte-check で確かめられる。歩きスマホの旗は src のどこでも立たない(顕著行為の過程は TALKING か FREE だけを書く=`processes/salient.py:430`)。✓
- (c) `Percept` の 25 欄と空の 9 欄は口の約束と 10-13b §4-2 に合う。✓
- (d) `TickScratch.percepts` は decide だけ・段 C の守り・行 P(no・discardable)。✓(M1 の道を除く)
- (e) `test_nearby_vectorized.py` の的は今は効く(上の 4)。✓
- (f) 範囲の外の既存の試験の書き換え: `test_p_notice.py`(`M_LOAD` の釘を消し、負荷の係数が無い試験を足した)・`test_p_see_activity.py`(表・腕・CLI の旗が無い形に書き直し・活動の種別の読みと親しみの層のスカラー p_see の試験は残る)・10f(`P12_KEYS`・並びの式・設定の節の sha)は段の決定(係数を消す・`percept` を足す)から動く所だけ。`test_nearby_vectorized.py` は係数ではなく描画の分離から動く所(空振りを直した)。✓
- (g) 性能: 記録 §10 に描画 1 回 98.2 → 112.2 µs(+14 µs・11 回の中央値・範囲は重ならない)・内訳・5,000 体の既定 v3 で約 0.9 秒(壁時計の約 3%)の見込みがある。既定 v3 の壁時計は 2 回とも数 % の範囲。古典+記憶+関係の +9% の説明は弱い(L7)。
- 記録に絶対パス・ホスト名・個人名は無い(記録・道具・新しい試験・HEAD の写しを grep)。触った共有ファイルの一覧(記録 §1・§8)は `git diff --stat` の 21 ファイルと合う。

## 親に確かめてほしいこと(取り込みの順で必ず動く所)

1. M1 の直し方(`BridgeResult` に欄を足さない道)の選択。
2. 1-4 との rebase: 1-2 は `p_notice` の docstring の expedient の項を 6 → 5 にした。1-4 のつなぎの台帳の行 `HD-perception.p_notice-16ea5cb3` は「項 6 個」で、`tests/engine/bridging/test_bridging_ledger.py:119`(項の合計 338)と `:164`(「項 N 個」の一致)が落ちる(本体の scan で作業木の `p_notice.py` を読むと 5 個)。消えた項(`m_load`)を台帳にどう残すかも親の判断。
3. 1-4 は manifest の末尾に `rules_version` ほかを足した。1-2 の `percept` は「TM9 の前」に置き、`test_percept_schema.py` の `keys.index("percept") == len(keys) - 5` と 10f の `_tail`・`manifest_keys_frozen.json`・`CONFIG_PATHS_SHA256` が取り込みの後に合わなくなる。
4. 1-6 の行 M0・M0R と 1-2 の行 P で状態台帳の数・並び(`test_state_ledger_10b.py`)と `local-assignment.json` がぶつかる。
5. 削除の後の全体の試験と、係数を消した後の 19 構成の byte-check(実装役は 4 構成だけ)。
