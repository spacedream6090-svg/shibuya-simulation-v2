# 第 2 期 2-2 近接 11a → 11c の独立検収

- 検収役 Opus 5.5(実装は見ていない)。対象=作業木の枝 `2-2/proximity`(土台 `2bc7a4b`)の未 commit の差分 28 ファイル+新規(`engine/proximity.py`・`tests/engine/proximity/`・記録 `prox22/`)。本体は HEAD `bf52089`(1-7 を含む)を読むだけ。
- 書いたのはこの 1 本だけ。検収の一時の物(HEAD の写し・ランの出力・負の対照の写し)は作業木の `_bc_review/` に置き、終わりに消した。封印の層(`kddi_la`・`shibuya_jinryu`・`boundary_counts.json`・`data/realworld_live/`・PT の検証側・`presence_anchors_v0.json`・`diversity_anchors_v0.json`)は開いていない。HEAD の写しには、エンジンが開く錨 2 本(`ssb2021_activity_prior_v0.json`・`hunger_energy_anchors_v0.json`)と `commute_time_dist_r3.json` だけを入れた。
- 要件の正: 発注文と実装アジェンダ(§2・§2-1・§4・§7・末尾の B1〜B8)。**口の約束の書類 `v2-foundation-contracts-2026-10-13.md` には「## 2-2 近接 11a → 11c」の節が無い**(本体 HEAD にも作業木にも無い。節は 1-1〜1-9 と「受入の順と門」だけ)。そのため 2 は発注文の「作るもの」とアジェンダの決定に照らした。

## 判定

**条件つき受入。** 結果不変は確かめた。byte-check 4 構成は 25 欄とも同じで、1,000 体の描画 11,928 回のバイトと設定の節の値も同じだった。不変条件 7 本と p(d) の 2 点は、自分で数え直しても成り立つ。守りの負の対照は 4 本とも検査で落ちた。

ただし次の 3 つを直してから取り込む。
- M1: 腕 cell で保存した状態を腕 distance で再開しても止まらない(逆も同じ)。
- M2: 39 万体の費用の宣言に、毎刻みの費用 2 つが入っていない。
- M3: 11c の「B5 の単位の在室人数の最大 30」は席の上限で止まった値なのに、記録はこれを「ハブになっていない」と読んでいる。

## 1. 結果不変 ✓

- 実装役の `byte_check_prox22.json`: 19/19 構成で 25 欄(`COMPARE_KEYS`)が全部同じ(head=`2bc7a4b` の写し・b=作業木の最後のコード)。`byte_check_prox22_distance.json` は 4 構成とも final・呼数・テープ・行動の件数・起床の内訳・`behavior_last`・`full_last`・`end_of_day` が動き、テープの列の名・顕著行為・出動・暦・資産の指紋は動かない。腕の裏として説明がつく。
- **自分の byte-check 4 構成**(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`。本体 HEAD `bf52089` の src の写しと作業木の src。`10e/byte_check_10e.py side` → `compare`・4 並び): **4/4 構成で 25 欄とも同じ。** final と呼数は順に `5f7ae9ff24005314`/65,597・`e0054a837c6ec4c1`/50,301・`24375ee3dab349e8`/51,835・`73a78288ab5e1498`/69,111。`src_is_worktree` は head が偽、作業木が真。HEAD は 1-7 を含むが、既定の結果は同じだった(`2bc7a4b` との差は 1-7 の分だけ)。
- 腕の既定: 環境変数 `SHIBUYA_PROXIMITY`・`SHIBUYA_PROXIMITY_D` は空で回した。腕 distance では同じ構成の final が動く(実装役の distance の JSON と下の 6 の (vi))ので、byte-check は cell の道を回したと言える。

## 2. 口と約束(発注文とアジェンダに照らす)

| 項 | 判定 | 根拠 |
|---|---|---|
| `SpatialIndex.build(xy, band)`・`.within(i, d)`・`.pairs(d)` | △ | 口の形は発注どおり(`ids`・`unit`・`n_total`・`cell_m` の引数と `query_many`・`unit_members`・`unit_counts` を足した)。**置き場所が発注の `engine/spatial_index.py` ではなく `engine/proximity.py`**。記録に理由が無い(空間の段 1・2 で使い回す部品なので、別のモジュールの方が引きやすい)=L4 |
| `--proximity {cell,distance}`・`SHIBUYA_PROXIMITY`・`run_day` の引数にしない | ✓ | `cli.py`・`proximity.arm/set_arm`。CLI が環境変数より強い(試験あり) |
| `--proximity-d {1.0,2.0,2.5}` | ✓ | `set_d` が 3 値の外を断る(試験あり) |
| 判定=同じ層 ∧ 距離 ≤ d(+舞台の中)・B5 の単位 | ✓ | `ProximityRule.reach/stay/by_unit`。「舞台の中(セル ≥ 0)」は今の判定と同じ扱いで足してある |
| 知人に気づく p(d)=R-62 の 2 点 | ✓ | `notice_p`・`NOTICE_D50_M`=16.95・`NOTICE_SCALE_M`=5.9621 |
| 鍵=「10c の counter の鍵」 | △ | 材料(相手の id・刻み)は入っている。ただし Philox の counter(`core.rng.stream`)ではなく splitmix64 の混ぜ方(8 の (c))。記録 §10 の 4・§11 の 1 で申告済み |
| manifest の `proximity`(末尾)・印 B6/B8 | ✓ | `manifest_fields`・`marks_for`。cell では観測の子が null |

約束と試験の対応(アジェンダ §2-1 と発注の受入):

| 約束 | 試験 |
|---|---|
| 別セルの 1 m は話せる・同セルの 3 m は話せない・層の違う 1 m は話せない | `test_rule.py` の合成の 2 体(今の判定の負の対照つき) |
| 成立した会話の相手は必ず d 以内(1 日の全会話) | `test_runs.py::test_every_opened_conversation_is_within_reach`(世界資産 1,500 体)・slow で 1.0/2.5 |
| 近傍の列挙は総当たりと一致(600 点・重なり) | `test_index.py`(d=1.0/2.0/2.5/10.3・2 m で 781 組) |
| `--proximity cell` は今と同じ | byte-check 19 構成+`test_cell_arm_equals_the_head_golden`(300 体) |
| 同じ入力で同じ結果 | `test_same_input_same_result_and_the_arm_moves_the_run`・再開 == 通し |
| p(d) が 2 点を通る・感度の腕・B5 の単位 | `test_rule.py`(4 本) |

**試験の無い約束**: (i) 腕の違う再開を止める試験(止める仕組みが無い=M1)。(ii) 再開の試験は合成の世界だけで、1 日の気づく抽選が 6 回しかない。印(`_acq_until`)が戻らなくても通る見込みが高く、検出の力が弱い(L2。世界資産で自分が確かめた結果は 6 の (iv))。(iii) 描画の B5 の知人と、起床の「気づいたまま」の印が一致するかの試験が無い(L1)。

〔決定〕B1〜B8 の反映: B1・B2(11a だけ・11b なし)✓。B3(2 m の決め打ち・1.0/2.5 の腕・宣言=つなぎの台帳の HD 行)✓。B4(連続の確率)✓。B5(a)(単位=在席中の POI の区画・台帳 `DOC-prox22-b5-unit`・外す段 5-2)✓。B6(位置の出どころの印・建物の中も同じ印・`DOC-prox22-b6-node-position`・5-1)✓。B7 は文書の直しで実装の対象ではない(記録 §5-3 は「空間の段 1・2 の後に測る」と書いている)✓。B8(node 幾何だけ `marks.B8`・`DOC-prox22-b8-node-walk-speed`・5-1)✓。

## 3. 発注文の各項

| # | 判定 | 根拠 |
|---|---|---|
| 1 近傍の索引 | △ | 中身・試験・刻みごとに捨てる(`TickScratch.near_index`・行 PX0)は ✓。置き場所だけ発注と違う(2 の表) |
| 2 判定の切替口 | ✓ | 対象 9 つを全部切り替えた(記録 §2-1)。漏れの一覧あり(8 の (d)) |
| 3 気づく確率 | △ | 曲線・距離の打ち切り・腕 distance だけは ✓。鍵が Philox の counter でない(申告済み)。R-62 の出典は manifest と記録にはあるが、つなぎの台帳の行(HD 行の why)には書いていない(L5) |
| 4 「暫定」の印 | ✓ | manifest の `position_source`・`marks` と台帳 2 行 |
| 5 11c の読み直し | △ | 計器・表・cell の検算は ✓(8 の (e))。読みに誤りがある(M3・L6) |
| 6 manifest | ✓ | 末尾に `proximity`。cell では既存の欄の値は不変(5) |
| 受入の試験・byte-check 19・distance 4 構成 | ✓ | distance の表に「会話の数」は無く、会話の起床の呼だけ(セッションの数は 11c の表にある。軽微) |
| 記録 | △ | 構成は発注どおり。数の誤り 2 か所(L6) |

「できなかったこと」(記録 §11)の申告=鍵の形・B5 の半径・刻みごとの抽選と気づいたまま・名指しの相手に近づく口・並行の段との当たり。実態と合う。全体の試験で落ちた 3 本の扱い(既知の junction 1 本・直した 2 本)も記録どおり。

## 4. 守り ✓(実行時の守りは L3)

- 書く口: 計器 `ProximityLayer.meter` を書くのは `build_index` だけで、呼ぶのは `perceive_prepare` だけ。気づいた印は `relations._acq_notice` が `_acq_until`(O17)に書く。呼ぶのは `relations_wake` で、宣言 `O1[6-9]:rel_layer.*` の中。`layers.proximity` を読む系 6 つ(perceive_prepare・apply_responses・relations_wake・phase_c・conversation・close_final)は、どれも `reads` の宣言と一致する(grep で突き合わせた)。
- **負の対照**(作業木の src の一時の写しを書き換え、腕 distance の合成 80 体 240 刻みで回した。写しは消した):

| 植えたもの | 結果 |
|---|---|
| NC1: `perceive_prepare` の `paths` から `PX:proximity.*` を外す | 段 B の Probe が違反 35 件(`(0, 'perceive_prepare', 'PX:proximity.meter')` ほか)。元のままは 0 件 |
| NC2: `scratch_w` から `near_index` を外す | `STRICT_SCRATCH` で `AttributeError: 系 perceive_prepare は scratch.near_index を書く宣言を持たない(段 C)`。元のままは通る |
| NC3: `engine/relations.py` に `agents.registry.band` の読みを 1 つ足す | 状態台帳の AST 検査が 1 件(`agents.band: 軸 1 が no なのに読み手がある ['engine/relations.py:944']`)。元のままは 0 件 |
| NC4: `ProximityRule.reach` の頭で例外を投げる | 腕 cell のランは例外なしで終わる。腕 distance のランは例外で止まる=既定の道は新しい規則に 1 度も触らない |

- 実行時の物: `ProximityRule` は `frozen=True, slots=True`。`_row_spans` の配列は書けない。腕の表(`D_ARMS`・`OCC_BINS`・`CONFIG_KEYS`)は tuple。**`ProximityLayer` には `__slots__` も `__setattr__` の守りも無い**。`meter` は素の dict で、`layer.rule` も差し替えられる。`SpatialIndex` の配列(`x`・`y`・`ids` など)も書ける(L3。1-3・1-7 の教訓の形にそろっていない)。

## 5. 宣言と凍結 ✓(記録の数 1 か所は L6)

- 状態台帳: 行 `PX`(軸 1 diag・軸 2 discardable・items `proximity.meter`)・`PX0`(no・discardable・items なし)・`OWNER_CLASSES["proximity"]`・`EXCLUDED` の `proximity.rule`(CONST)・`_ALLOW_BAND` に 2 つ。版を上げない理由も書いてある。✓
- 凍結の表: `CONFIG_PATHS_SHA256` を計算し直した。作業木の `config_paths()` から `proximity.*` の 12 本を除いた sha256 は前の値 `89e426b3…df47dae50b9065` と同じで、12 本を入れると新しい値 `58e69d8f…` になる。**更新は proximity の設定の子 12 本の追加だけで説明できる**(CLI の引数そのものは設定の道筋に入らない)。manifest の鍵の凍結は 115 → 116 個(記録 §9 は「114 → 115」と書いている=L6)。状態台帳の数 193 → 195・つなぎの台帳の見出し 79 → 80 と項 348 → 355 は差分どおり。
- manifest の既存の欄(cell): 1,000 体・語彙 v3・記憶+関係+同席で、本体 HEAD の写しと作業木の manifest の設定の節を比べた。違ったのは `bridges_count`(288 ↔ 290)・`bridges_version`(つなぎの台帳の行が 1-7 と 2-2 で違う=想定どおり)・`manifest_sections.paths`(proximity の道筋)・`relations.init` の壁時計(観測の葉)だけだった。

## 6. 同値(試験を読んだ+独立の再計算)

試験: 腕 on/off(`test_same_input_same_result_and_the_arm_moves_the_run`)・HEAD の golden(`test_cell_arm_equals_the_head_golden`=`2bc7a4b` の 300 体の final と呼数)・置き換えの前後(`test_rule_none_and_cell_mode_keep_the_current_judgement`)・書きの検査の on/off(`test_guards_hold_on_the_distance_arm`)。どれも比べ方は妥当。

独立の再計算(道具は自分で書いた。実装の判定の関数は使っていない):

- (i) **描画のバイト(既定 cell)**: `Renderer.render` を包み、描画ごとに(刻み・体・`prompt_hash`・本文の sha256・全ブロックのバイト・`recalled_rows`)を 1 本の sha256 に積んだ。1,000 体・1 日・語彙 v3・記憶+関係+同席。HEAD の写しと作業木で **11,928 回の digest が同じ**(`f68d45a6…`)。final `7c401f6e…` と呼数 11,928 も同じ。
- (ii) **設定の指紋**: 組み立ての `cfg.fp` の sha256 は、HEAD・作業木の cell・作業木の distance の 3 つで同じ(`c459a3cf…`)。発注どおり、腕は指紋に入らない(M1 の原因)。
- (iii) **ランの種類**: CLI(合成 40 体)で `SHIBUYA_PROXIMITY=cell` → `reproduction`、`=distance` → `arm`、`--proximity distance` → `arm`。`--proximity-d 2.5` だけなら `reproduction` で、`d_m` は null(腕 cell では効かない)。
- (iv) **再開(世界資産)**: 腕 distance・1,000 体・止める刻み 750。再開と通しで final・750 以降の checkpoint(behavior と full)・呼数の和が同じ。**負の対照**: 再開の最初の知人出現の呼び出しで `_acq_until` を −1 に消すと(気づいた印 9 本)、final が通しと違った。印は結果に効き、再開で戻っている。
- (v) **索引と総当たり**: 900 点(150 点はほかの点にぴったり重ねる・30 点は格子の線の上・層 3 つ・索引は 700 点の部分集合)。d=1.0/2.0/2.5/3.7/10.3 で `pairs` と総当たりの組が一致した(84・227・324・649・4,327 組・重複 0・距離 0 の組 41)。`within`(120 体)と `query_many`(50 点)の不一致も 0。
- (vi) **決定論**: 腕 distance の 1,000 体の final `51f7c3e51f34a7d8` が、別のプロセスの 2 回(描画の digest のランと再開の通し)で同じ。

## 7. 試験

- 指定の範囲(`tests/engine/proximity tests/engine/systems tests/engine/events tests/engine/decision tests/engine/time` と会話・関係・再開・状態台帳・設定の節・版上げ・`tests/perception`)・`-n 2 --dist loadfile -m "not slow"`・作業木: **971 passed**(落ち 0・飛ばし 0=data が無くて飛ばした試験も 0)・23 分 25 秒(ほかの検収のランと同居)。
- `lint-imports`(作業木の src): 5 kept・0 broken(208 ファイル)。
- `tests/c7` は回していない。

## 8. 本段に固有の確認

### (a) 不変条件 7 本 ✓

- 合成の 3 本は `test_rule.py` を読んだ(今の判定の負の対照つき)。
- **全会話の距離を自分で数えた**: 腕 distance・5,000 体・語彙 v3・記憶+関係+同席・mock・1 日。`set_conversing` と `join_conversation` を包み、registry の `cell`・`band`・`xy`・`poi_ref` から直に数えた。成立 205 件・3 人会話 0 件。舞台の外 0・層違いで単位も違う 0・d 超で単位も違う 0。**単位でない 200 件の距離は全部 0 m ちょうど**(最大 0.0 m=node への重なり。B6 の印のとおり)。単位の組は 5 件で、そのうち単位だけで届いたのは 1 件(17.7 m)。
- 近傍の列挙は 6 の (v)。cell は 1。同じ入力で同じ結果は 6 の (vi) と (iv)。

### (b) p(d)・打ち切り・気づいたまま ✓(M1・L1 に注意)

- 独立の再計算: 50% の点 (10.4+23.5)/2=16.95 m、尺度 (23.5−10.4)/(2 ln 3)=5.96207 m。p(10.4)=0.75・p(23.5)=0.25・p(0)=0.945・p(2)=0.925・p(100)=8.9e-7。
- 気づいたまま: 範囲の中で印が切れていない欄は引き直さず、`max(今の値, T+2)` で延ばす。範囲の外に 1 刻みでも出ると、戻った刻みには印が残っておらず引き直す(記録の「範囲の外に出ると切れ」と同じ)。起床の後 60 分の不応期と同じ配列なので、起床の後も範囲の中なら気づいたまま。
- **cell では書かれない**: `_acq_notice` を呼ぶのは腕 distance だけ(NC4・byte-check の `full_last` が同じ=O17 の値も同じ)。ただし同居のため、腕 distance では `_acq_until` が「不応期の終わり」と「気づいている刻みの終わり」の 2 つの意味を持つ。腕を混ぜた再開(M1)では、cell の不応期の値が distance で「気づいている」と読まれる。
- 描画の B5 の知人は描画ごとに同じ鍵で引き直し、印(気づいたまま)を見ない。同じ刻みの起床とは一致するが、その後の描画では、気づいている知人が 10.3 m の外にいると載ったり消えたりする(L1)。

### (c) 気づく抽選の鍵(事実だけ)

- 作り方: 塩 = `blake3(run_salt ‖ b"an\x00")` の先頭 8 バイト(u64)。時刻の鍵 = `run_tick_key(day_key0, T, 60)` = `day_key0 × 1440 + T`(`day_key0` は組み立ての `day_index`=1-8 の口と同じ)。鍵 = `mix(mix(mix(塩 XOR 時刻の鍵) XOR 体) XOR 相手)`(`mix`=splitmix64 の 1 段)。一様乱数 = 上位 53 ビット ÷ 2^53。
- 同じ入力で同じ値: ✓(同じ配列で 2 回同じ・1 組だけ引いても同じ・Python の整数で書き直した計算と 200/200 一致)。
- **対称性**: 体と相手を入れ替えると 3,000 組中 2,999 組で別の値になった(同じ値は体 = 相手の 1 組だけ)=向きで別の値。
- **K19 の外にある根拠**: K19 の重なりの検査(`engine/rng_audit.py` の `StreamRecorder`・`check_overlaps`・`K19_RECREATED`)は `core.rng.stream`(Philox)の呼び出しだけを控える。気づく抽選は `stream` を呼ばないので、控えに載らない。`k19_counters`(0 語目を空ける並べ方)も使っていない。`tests/engine/test_version_bump_10e.py` の K19 の試験は `k19_counters` の並びと、名を挙げた用途(`world.delivery_inbound` ほか)の流れだけを見る。
- そのほかの事実: 用途の印 `b"an\x00"` は `engine/proximity.py` の中で定義しており、`core/hashing.py` の印の一覧(`pk`・`ak`・`wk`・`wd`・`ri`)に載っていない。塩と時刻の鍵を XOR でまとめるので、(塩 ^ x, 時刻 ^ x) は同じ鍵になる(1 つのランの中では塩が 1 つなので起きない)。同じ混ぜ方の先例 `renderer.near_tie_keys` は、同点の順だけに使っていて抽選ではない。描画の B5 の知人の抽選も同じ鍵を使い、起床の抽選と同じ値になる(わざとそうしている)。

### (d) 切り替えの漏れ ✓(記録に無い漏れは見つからなかった)

`cell ==`・`same_cell`・`cell_of`・`_same_cell_hits`・`partners_in_cell`・`_nearby`・`neighbors`・`in_cell` を `src/shibuya` 全体で grep した。記録 §2-2 の一覧の外で、人どうしの近さを同じセルで決めている所は無かった。残りのセルの比較は場所の判定だった: 店の対象(`poi_target`・`commit._poi_in_cell`)・開店の店員(`processes/opening.py:243`)・乗車のホーム(`resolve` の `_cell_of_node`)・記憶の場所の想起(`memory.py`・`memory_store.py`)・退出の計器(`presence.py`)・到着(`intent.py`)・古典の家/職場(`classical.py:564`)。古典の会話の相手は B5 の近接行の文から取る(`_near_strangers`・`_near_persons`)ので、切り替わっている。漏れではないが一致しない所は L1(描画の知人と気づいた印)。

### (e) 11c の読み直し(✓ と M3・L6)

- **cell が HEAD と一致**: `mock/rel_on/node/cell`(5,000 体)を本体 HEAD `bf52089` の写しと作業木の src で回した(実装役の `reread_11c.py runs --only`)。壁時計と腕の節を除く 232 の葉が全部一致した。final は `aa67a7ad4d4d0fc9`・呼数 79,898・セッション 305。実装役の `2bc7a4b` の記録の同じ行とも全部の葉が一致した。
- **在室人数の最大 30**: `runs_11c_head.json`(6 行)と `runs_11c_wt.json`(24 行)の全 30 行で `max_in_room` は 30。最小も 30 だった。上位の単位は飲食の POI 23・186・694・733・740 で、どれも 30 で止まっている。**30 は `engine/processes/crowd.py` の席数**(`seats_for_categories`: 飲食の床面積 60 m² ÷ 1 人 2.0 m²=30・expedient)。席が埋まると `admit` が入店を断るので、この上限を超えない。記録の「席 4 の飲食店」の 4 は POI の別の欄 `capacity` で、在室の上限ではない。10-03 §4 の懸念(百貨店や大きなオフィスビルが 1 つの単位で数千人のハブになる)は、いまの単位の定義(在席中の店だけ・事務所と家は単位を持たない)と席の表のために測れていない(M3)。
- **同じ点に重なる体**: 全 30 行の最大は 159〜520。記録の「225〜520」は関係 off の行(227・225・230・237・504・520)の値で、関係 on/同席の mock の行は 159〜227(L6)。
- **屋内の会話の損失の数え方**: 腕 cell のランで成立した組を、成立の時点の位置で腕 distance の式(計器の側の写し `reach_d`=`ProximityRule.reach` と同じ式・`check_11c.json` で突き合わせ済み)にかけ、届かない組を「失われる」と数える(反実仮想の数え方。腕 distance を実際に回したときの減り方とは別の量で、記録はこの 2 つを書き分けている)。屋内の分類は計器の側の自前(在店=`poi_ref ≥ 0`・自宅/職場/学校のセルで止まっている)=未リサーチ(expedient) と宣言済み。数え直し: mock 305 件のうち届くのは 170 件で、届かない 135 件の内訳は屋外 90・片方屋内 34・両方屋内 11。classical 460 件のうち届くのは 274 件で、届かない 186 件の内訳は屋外 37・片方屋内 33・両方屋内 116(職場どうし 93)。記録の表と同じ。

### (f) 既定 cell の描画・設定の指紋・CONFIG_PATHS_SHA256 ✓

6 の (i)〜(iii) と 5 のとおり。

### (g) 費用(M2)

- 測り直し(39 万体・W1 のノードに一様・関係辺 15 本/体・壁時計は決定論でない): 索引の組み立て 61 ms(記録 60 ms)・知人に気づく判定 176 ms(記録 170 ms)。記録の値と合う。
- **記録 §6 の宣言に入っていない毎刻みの費用が 2 つある**:
  1. 同席(`relations.copresent_step` → `_reach_hits`)は、空でない辺の全部(5,265,778 本)に `ProximityRule.reach` をかける=**396 ms/刻み**。cell の道は同セルの辺の集めを同席と知人出現で 1 回に共有しているが、distance は同席と気づく判定で全辺を 2 回なめる。
  2. `ProximityRule._parts` は呼ぶたびに `np.asarray(r.xy, dtype=np.float64)` で全員の座標を写す。39 万体では 1 組だけの判定でも **1.67 ms**(5,000 体では 0.005 ms)。離脱の判定 `ConversationManager._left_reach` は、開いている会話ごとに毎刻みこれを呼ぶ。cell の道の離脱(`_left_cell`)は写しを作らない。返事待ちと 3 人会話の判定も 1 組ずつ呼ぶ(今の cell の `talk_within_reach` も `cell` を int64 に写すので 1.54 ms で、こちらは前からある形)。
- 逐次ループ: 新設なし。`for` は `OCC_BINS` の 8 回と、描画 1 回の候補(半径 10.3 m の中の数人〜数百人)の set の作り方だけ。体数に比例するループは無い。

### (h) 状態台帳 ✓

行 PX・PX0 の軸と items は 5 のとおり。`agents.band` の読みの許可は 2 つ(`engine/proximity.py` の 1 か所・`perception/renderer.py` の自分の層)で、AST 検査は 0 件。NC3 では新しい読みを捕まえた。band がセルの層から導く派生だという主張は、5,000 体・node 幾何の腕 distance のランで、会話の成立の時点ごとに舞台の中の全員を比べて確かめた。`band == cell_band[cell]` は 472,531 回中 472,531 回成り立った(台帳の行の根拠は `cell_band[cell]` と書くが、node 幾何のコードは `node_band[node]` から書く。値は同じ)。

### 記録の書き方・触った共有ファイル

- `prox22/` の README・JSON・道具に絶対パス・ホスト名・個人名は無い(grep)。README は LF。
- 記録 §1・§9 の一覧は `git diff --stat`(28 ファイル)と合う。
- 作業木に追跡されていない `_bc/`(実装役の scratch)が残っている。中の HEAD の写しに `docs/bench/anchors/presence_anchors_v0.json` と `diversity_anchors_v0.json` の写しが入っている(10e の byte-check の手順が `git archive … docs/bench/anchors` を丸ごと写すため。エンジンが開くのは 2 本だけ)。中身は読んでいない(L7)。

## 欠陥(重さ順)

| # | 重さ | 所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `engine/systems/build.py`(組み立て)・`engine/resume.py`(再開の見出し) | 腕 cell で保存した状態を、腕 distance で再開できてしまう(逆も同じ)。合成 100 体で確かめた: 再開は止まらず、manifest は `mode: distance`・`index_builds` 690 で後半だけ distance になった。腕は結果を変えるのに、設定の指紋(発注どおり)にも状態のファイルの見出しにも入っていない。`_acq_until` の意味も腕で違う(b) | 設定の指紋は変えずに、状態のファイルの見出し(または `resume` の節)に `proximity.mode` と `d_m` を書く。再開のときに今の腕と違えば止める(`ValueError`)。試験=cell → distance の再開が止まる・同じ腕は通る |
| M2 | 中 | `engine/proximity.py` `ProximityRule._parts`・`engine/relations.py` `_reach_hits`・記録 §6 | P4 の宣言(索引 60 ms+気づく判定 170 ms)に、同席の全辺の reach(39 万体で 396 ms/刻み)と、1 組ごとの全員の座標の写し(1.67 ms/呼び出し×開いている会話の数)が入っていない | `_parts` は添字で集めてから float64 にする(全員の写しを作らない)。同席と気づく判定で辺の集めと距離を 1 回に共有する。§6 の宣言を測り直して書き直す |
| M3 | 中(記録) | 記録 §0・§5-1・§5-3 | 「B5 の単位の在室人数の最大は 30 人・席 4 の飲食店・数千人のハブにはなっていない」の 30 は、crowd の席数(飲食 60 m² ÷ 2.0 m²=30・expedient)で止まった値。4 は POI の `capacity` の欄。いまの単位は在席中の店だけなので、10-03 §4 の懸念(百貨店・大きなオフィスビル)は測れていない | 読みを書き直す: 最大は席の表の上限そのもの・上限のある店でしか単位を作っていない・事務所と家の単位は空間の段 2 まで測れない(懸念は未確認として残す) |
| L1 | 低 | `perception/renderer.py` `_nearby_people_distance` | 描画の B5 の知人は描画ごとに引き直し、関係の層の「気づいたまま」の印を見ない。10.3 m の外にいる気づいている知人が、描画ごとに出たり消えたりする | 印の読み取り専用の口を描画に渡すか、記録の限界に足す |
| L2 | 低 | `tests/engine/proximity/test_runs.py` の再開の試験 | 合成の世界では 1 日の気づく抽選が 6 回しかなく、印が戻らない欠陥を見つける力が弱い | 世界資産の腕 distance の再開と、印を消すと final が動く負の対照を足す(6 の (iv) の形) |
| L3 | 低 | `engine/proximity.py` `ProximityLayer`・`SpatialIndex` | `__slots__` と `__setattr__` の守りが無い。`meter` は素の dict で、索引の配列も書ける | `__slots__` と、組み立ての後の差し替えを断る `__setattr__`。索引の配列は `setflags(write=False)` |
| L4 | 低 | `engine/proximity.py` | `SpatialIndex` の置き場所が発注(`engine/spatial_index.py`)と違い、記録に理由が無い | 別のモジュールに分けるか、記録に理由を書く |
| L5 | 低 | `docs/design/bridging-ledger.json` の `HD-engine.proximity-1af925f4` | 発注は「値の出典(R-62)を記録と台帳に」だが、台帳の行に R-62 が無い | HD 行の why に R-62(Loftus & Harley 2005)を足す |
| L6 | 低 | 記録 §9・§0・§5-3 | manifest の鍵は 115 → 116(記録は 114 → 115)。同じ点の重なりの「225〜520」は関係 off の行だけ(全行では 159〜520) | 数を直す |
| L7 | 低 | 作業木の `_bc/`・10e の byte-check の手順 | 追跡外の scratch に封印の錨 2 本の写しが残っている | 取り込みの前に `_bc/` を消す。手順の `git archive` をエンジンが開く錨だけに絞る |
| L8 | 低 | `engine/relations.py` の新しい docstring(`_reach_hits`・`_acq_notice`) | 「毎 tick」の語(T0 の規則。自動の検査は `core/` と `engine/systems/` だけを見るので落ちない) | 「毎刻み」に直す |
| L9 | 低 | `engine/proximity.py` `_NOTICE_TAG` | 用途の印 `b"an\x00"` が `core/hashing.py` の印の一覧に無い | 一覧に載せる(Philox に載せ替えるなら不要) |

## 親に確かめてほしいこと

1. 口の約束の書類に 2-2 の節が無い(発注文とアジェンダで照らした)。節を足すかどうか。
2. 気づく抽選の鍵を Philox の counter に載せ替えるか(8 の (c) の事実)。載せ替えるなら、辺ごとの流れの費用と K19 の登録が要る。
3. M1 の止め方: 見出しに腕を書いて止める形でよいか(設定の指紋は変えない)。
4. M3 の読み: 10-03 §4 の懸念(大きな単位のハブ)を「いまは測れない」として残すか。
5. 本体 HEAD `bf52089`(1-7)との当たり: manifest の末尾(1-7 の `tools` の後に `proximity`=鍵 117 個)・状態台帳の数(1-7 で 194 → 2-2 を足して 196)・つなぎの台帳の数と項・`OWNER_NAMES`・`SCRATCH_FIELDS`・`table.py`・`relations.py`(1-7 の連絡先の印)・凍結の試験 7 本。既定の結果は `bf52089` でも同じだった(1)。
