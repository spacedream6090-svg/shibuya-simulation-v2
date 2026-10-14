# 第 2 期 2-2 近接 11a → 11c の実装の記録

- 実装役 Opus 5.5。作業木の枝 `2-2/proximity`(土台は最初 `2bc7a4b`=第 1 期の 1-0〜1-9 のうち 1-7・1-8b を除く取り込み済み。§15 で本体 `db40de2` へ rebase した)。commit は親。
- 正: [実装アジェンダ](../../../../design/v2-proximity-distance-implementation-agenda.md) §0〜§2(段 11a)・§4(段 11c)・§7(予算)・末尾の「ユーザー決定(2026-10-03)」B1〜B8・[決定 10-03](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §4(4-2 気づく確率)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) 第 2 期 2-2・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(新しい問い=既定 off の腕で仮採用)。
- 前の読み直し: [近接系の node/edge 読み直し](../../proximity-edge-2026-09-30/README.md)(計器の作りと 600 点の検算をそのまま借りた)。
- 先例: 近傍の列挙は前の読み直しの計器 `pairs_within`(格子+`searchsorted`)を口にしたもの。scipy の cKDTree は依存に無い(足すには許可が要る)ので使っていない。格子の幅 2.5 m は知覚契約の可視性格子と同じ。
- 数は実測。生の出力(テープ・side の JSON・ランの全計数)は作業木の `_bc/`・`_bc2/`・`_bc3/`(git の外・検収 L7 と同じく直しの後に消した)。比べた結果と道具だけをこのフォルダに置く。道具は `tools/`(`reread_11c.py`=11c の読み直し・`index_cost.py`=39 万体の費用・`probe_poi_ref.py`=B5 の単位に残る歩いている体の探り)。byte-check は既存の `10e/byte_check_10e.py`。

## 0. 結論

- **親の判断 10-14 の直し(§14)**: 気づく抽選を `core.rng.philox_array` で辺をまとめて引く(1 組ずつ引いた値と同じ)・腕 distance の B5 の単位を「同じ `poi_ref` かつ店のセルの中に居る体」に絞った・B5 の近接行の知人は「気づいていて半径 10.3 m の中」だけ。この下の 11c と費用の値は直しの前の回の値で、直しの後の値は §14 に置いた。
- **腕** `--proximity {cell,distance}`(環境変数 `SHIBUYA_PROXIMITY`・既定 cell=今の判定=層を作らない)と会話の距離の感度の腕 `--proximity-d {1.0,2.0,2.5}`(`SHIBUYA_PROXIMITY_D`・既定 2.0)。`run_day` の引数にしない=設定の指紋に入れない。腕の名と値は manifest の末尾の `proximity`。
- **判定**(腕 distance): 「舞台の中・同じ層(`band`)・距離 ≤ d」か「同じ B5 の単位(在席中の POI の区画=`poi_ref`)」。同じセルの条件は外す。会話の開始・返事待ち・3 人会話・離脱(d+1 m)・招待の相手の候補・偶然の出会い・同席・B5 の近接行を切り替え、知人出現の起床は R-62 の 2 点を通るロジスティック p(d) の抽選にした(§2)。
- **近傍の索引** `engine/spatial_index.py` の `SpatialIndex`(検収 L4 で `proximity.py` から分けた・2.5 m の格子・層ごと・`build`/`within`/`query_many`/`pairs`)。総当たりと一致(重なった点を含む 600 点・d=1.0/2.0/2.5/10.3 m・2 m で 781 組=前の記録と同じ)。刻みごとに作って捨てる(`TickScratch.near_index`・状態台帳の行 `PX0`)。
- **結果不変(既定 cell)**: byte-check 19/19 構成で 25 欄とも本体 HEAD `2bc7a4b` の src と同じ(§7)。11c の計器も cell では HEAD と全部の値が一致(6/6)。腕 distance の 4 構成は動いた(腕の裏)。検収の直しの後も、本体 HEAD `bf52089` の src(錨は 3 本だけ写した)と作業木の src で 4 構成 25 欄とも同じ(§7-2)。
- **11c**(§5): 会話の成立時の距離が 2 m を超える割合は mock 関係 on で 45.3% → 2.8%(残りは全部 B5 の単位=同じ店の中)・classical 40.7% → 0.8%。知人出現の起床の時点の距離の中央値は 24.7 m → 2.7 m(腕 distance の値は検収の直しの後に回し直した)。**B5 の単位の在室人数の最大 30 人は crowd の席数の上限(飲食 60 m² ÷ 2.0 m²=30・expedient)で頭打ちの値**で、ハブにならない証拠ではない。10-03 §4 のハブの懸念(百貨店・大きなオフィスビル)は、いまの単位(在席中の店だけ)では**測れない**(つなぎの台帳に宣言・外す段 5-2)。**同じ点(node)に重なる体**は最大 173〜520 体(全行・直しの後の回)。**B5 の単位に、店を出て歩いている体が残る**(在席の印 `poi_ref` は歩き出しでは解かれず、滞在の上限 30 分か退出・乗車で解かれる=エンジンの今の挙動)。腕 distance では同じ単位で成立した会話の相手が最大 418 m(node)・498 m(edge)離れていた(§2-1・§5-3・親の判断)。**今の判定で成立した会話のうち、腕 distance では届かない会話**は mock 関係 on で 305 件中 135 件(44%・両方屋内 11 件)・classical 関係 on で 460 件中 186 件(40%・両方屋内 116 件=職場どうし 93 件)。
- **費用**(§6・検収 M2 で測り直した): 39 万体の見積りは刻みあたり 索引 80〜90 ms+関係辺の集め 0.13〜0.17 s+辺の見え方(同席と知人出現で共有)0.16〜0.20 s。1 組の判定(離脱・返事待ち・3 人会話)は 1.1〜1.5 ms → 0.008 ms。**鍵を counter の流れに載せ替えた分は増えた**: 気づく抽選は 1 組 1 本 13〜19 µs で、範囲の中で気づいていない辺は毎刻み引く=39 万体の上側で刻みあたり 0.7〜1.0 s(5,000 体の 1 日の実測は 1 日 29〜88 万本=刻みあたり 200〜610 本=3〜8 ms)。5,000 体・1 日の壁時計は既定に対して +7〜10%(検収の前の値・描画の B5 の近接行の問い合わせが主)。
- 試験(§8): 新しい試験 60 本(`tests/engine/proximity/`・slow 2 本を含む・検収の直しで 49 → 60)。直しの後の全体 **4,619 passed・1 failed(既知の junction の 1 本)・1 xfailed**・slow 2 passed・範囲 593 passed・`lint-imports` 5 kept。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/proximity.py`(新) | 腕(`arm`・`set_arm`・`d`・`set_d`)・判定の規則 `ProximityRule`(`reach`=届く・`stay`=離脱しない・`by_unit`・`notice_range`・`edge_view`=辺の見え方の共有・`notice_u`=counter の流れ・`noticed`)・描画への読み口 `NearView`・届く束の体のフォールバック `batch_partners`・層 `ProximityLayer`(計器・守り)・`manifest_fields`・状態のファイルの見出し `header_fields` と再開の検査 `check_resume`・気づく曲線 `notice_p`・〔10-14〕B5 の単位 `ProximityRule.units`(在席の印 ∧ 店のセルの中) |
| `src/shibuya/engine/spatial_index.py`(新・検収 L4) | 近傍の索引 `SpatialIndex`(`build`・`within`・`query_many`・`pairs`・`unit_members`・`unit_members_many`・`unit_counts`・配列は読み取り専用) |
| `src/shibuya/engine/resolve.py` | `talk_within_reach(…, rule=None)`(rule が distance なら `rule.reach`)・`ResolveOutcome.proximity`・`apply(proximity=None)`・`_apply_talk` が規則を渡す(腕 distance は実距離の成立も数える=`n_talk_by_distance`) |
| `src/shibuya/engine/conversation.py` | `ConversationManager.step(near_fn=None)`(離脱を `rule.stay` で)・`_left_reach` |
| `src/shibuya/engine/relations.py` | `choose_talk_partners(proximity=)`(同セルの辺と 2 m の知人を「届く辺」に)・`copresent_step(proximity=)`(届く辺)・`acquaintance_candidates(proximity=)` → `_acq_notice`(気づく抽選・印)・`_acq_finish`(今の道と共有の仕上げ)・`_edges`・`_edge_view`(刻みに 1 回の辺の見え方の控え=同席と知人出現が共有・検収 M2)・`aware_of`(描画が読む気づいた印・読むだけ=検収 L1) |
| `src/shibuya/engine/commit.py` | `intents_from_responses(proximity=)`・`_talk_partners_reach`(名指しは届くときだけ・フォールバックは届く束の体)・`_reach_rows`(届く名指しは別セルでも歩く意図にしない) |
| `src/shibuya/engine/run.py` | `_settle_pending_invites(…, rule=None)`・`classical_acq_addressable(…, rule=None)`・manifest の末尾に `proximity`・`MOTION_RNG_DOMAINS` に `proximity.notice`(親の判断 A1) |
| `src/shibuya/engine/rng_audit.py` | `SAFE_SITES` に `ProximityRule.notice_u`(用途名 `proximity.notice`・14 → 15 か所)・〔10-14〕`RNG_FUNCS` に `philox_array`(静的な走査は語数=`words`・`StreamRecorder` は 1 行を 1 本の流れとして控える) |
| `src/shibuya/core/rng.py`(〔10-14〕足しただけ) | `philox_array`(Philox4x64-10 を配列で回す=numpy と同じ出力)・`k19_counter_array`・`unit_float` |
| `src/shibuya/perception/renderer.py` | `_TickCache.near`・`prepare_tick(near=None)`・`_nearby_people` の頭で腕 distance なら `_nearby_people_distance`(今の道の文は 1 字も変えない) |
| `src/shibuya/engine/systems/{build,perceive,judge,act,talk,run_end,state_io,boxes,table}.py` | 組み立てで層を作る(腕 distance だけ)・perceive_prepare が索引を作り描画の前計算に渡す・規則を各系の呼び出しに渡す・`Layers.proximity`・`OWNER_NAMES` の末尾に `proximity`・`SCRATCH_FIELDS` の末尾に `near_index`・状態のファイルの見出しに `proximity`(腕 distance だけ)を書き、再開で今の腕と比べる(検収 M1)・宣言(§9) |
| `src/shibuya/engine/state_ledger.py` | 行 `PX`(層の計器・diag・discardable)と `PX0`(`TickScratch.near_index`・no・discardable)・持ち主 `proximity`・除外 `rule`・`agents.band` の読みの許可 2 つ(§9) |
| `src/shibuya/engine/manifest_sections.py` | `proximity`(設定 12・観測 5) |
| `src/shibuya/cli.py` | `--proximity`・`--proximity-d`(指定したときだけ置く=環境変数より強い)・腕 distance のランは `run_kind` が arm |
| `docs/design/bridging-ledger.json` | 7 行(§4) |
| `tests/engine/proximity/`(新) | §8 |
| 凍結の表(増えた分だけ) | §9 |

## 2. 判定を切り替えた対象と漏れ

### 2-1 切り替えた対象(腕 distance だけ・既定 cell は今の道)

| 対象(アジェンダ §2 の 3) | 場所 | 腕 distance の判定 |
|---|---|---|
| 会話の開始 | `resolve._apply_talk` → `talk_within_reach(rule=)` | 届く(同じ層・≤ d・または同じ B5 の単位) |
| 返事待ち(承諾) | `run._settle_pending_invites(rule=)` | 同上 |
| 招待・相互指名・返事待ちの登録 | `systems/talk.py`(`conv.invite`・`conv.register_pending` に渡す `same_cell`) | 同上 |
| 3 人会話 | `systems/talk.py` の `conv.join` の前 | 同上 |
| 離脱 | `ConversationManager.step(near_fn=rule.stay)` | 同じ層・≤ d+1 m・または同じ B5 の単位(d=2 で G7 と同じ 3 m) |
| 招待の相手の候補(LLM・mock) | `commit._talk_partners_reach`・`proximity.batch_partners` | 名指しは届くときだけ・フォールバックは届く束の体のうち並びの鍵が最小(今の「同じセルの束の鍵の最小」の版) |
| 招待の相手の候補(関係辺) | `relations.choose_talk_partners(proximity=)` | 同セルの辺と 2 m の知人を 1 つに=届く辺の相手(届く知人が居ればその中から=偶然) |
| 招待の相手の候補(古典) | `classical_acq_addressable(rule=)`・`_classical_partner` | 届かない相手は −inf・関係辺の選び手は届く辺 |
| 偶然の出会い | 同上(起点 chance=届く知人) | 届く |
| 知人出現の起床 | `relations._acq_notice` | 気づく範囲(舞台の中・同じ層・≤ 100 m)で、まだ気づいていない辺だけ p(d) で引く・気づいた欄は印(下) |
| 同席 | `relations.copresent_step(proximity=)` | 届く辺(同セル・2 m の条件の代わり) |
| B5 近接行 | `renderer._nearby_people_distance` | 同じ層で半径 10.3 m の中+同じ B5 の単位の体から密度逓減 3/2/1 の近い順+**気づいている知人で半径の中の体**(関係の層の印を読むだけ=`NearView.aware`・描画ごとに引き直さない=検収 L1・半径の外の知人は載せない=親の判断 10-14 の 3・印の無いランは足さない)+会話の参加者と焦点(候補の中に居れば) |

- **知人出現の印**: 気づいた辺の同一相手の不応期の配列 `_acq_until`(状態台帳 O17=保存される)に `max(今の値, T+2)` を置く=範囲の中に居る間は毎刻み延び、引き直さない(同じ家の 0 m の家族で毎刻み起きない)。範囲の外に出ると切れ、次に入ったら引き直す。起床の後 60 分の不応期も同じ配列なので「気づいている」と同じに扱う(今と同じ 60 分)。1 刻み目は印だけ置いて出さない(今と同じ宣言)。新しい状態の欄は足していない(足すと full-hash の項が増え、既定の腕の値が動く)。
- **気づく抽選の鍵**(親の判断 A1): 10c の counter の流れ `core.rng.stream(seed, "proximity.notice", *k19_counters(時刻の鍵, 体, 相手)).random()`(動きの側の seed・0 語目を空けて 1〜3 語目に時刻の鍵 `run_tick_key`・体・相手・1 語だけ引く=1 組 1 本)。用途名は `engine.run.MOTION_RNG_DOMAINS`、呼び手は `rng_audit.SAFE_SITES` に載り、K19 の重なりの検査の控え(`StreamRecorder`)に載る(重なり 0・作り直し 0=試験)。引くのは「範囲の中で、まだ気づいていない辺」だけ。splitmix64 の混ぜ方と用途の印 `b"an\x00"` は消した(検収 L9 は対象が無くなった)。**親の判断 10-14 の 1**: 同じ流れの 1 語目を `core.rng.philox_array` で組をまとめて引く(Philox4x64-10 を配列で回す・値は 1 組ずつの `stream(…).random()` と同じ=試験とランの中の全刻みで突き合わせた・逐次ループは無くなった=§14-1)。
- **辺の見え方の共有**(検収 M2): `ProximityRule.edge_view` が体 × k の辺を刻みに 1 回だけなめて(気づく範囲・距離・届く)を作り、同席と知人出現が共有する(`RelationLayer._edge_view`・同じ刻みの 2 回目は控え)。届くは `reach` と同じ答え(試験)。`_parts` は添字で集めてから float64 にする(全員の座標の写しを作らない)=離脱・返事待ち・3 人会話の 1 組の判定も同じ口。
- **B5 の単位**: 在席中の POI(`poi_ref`)で、**体のセルがその POI のセルと同じ体だけ**(`ProximityRule.units`・親の判断 10-14 の 2=§14-2。以下の段落は絞る前の探り)。店に入っても体の xy は入る前のノードのまま(店の位置に移らない)なので、同じ店の体どうしが離れている。**さらに在席の印は歩き出し(`resolve._apply_move`)では解かれない**(解くのは滞在の上限 `crowd.DWELL_MAX_TICKS`=30 分・退出・乗車・帰る支度)=店を出て歩いている体も最大 30 分は単位に残る。腕 cell・5,000 体・1 日の探り(語彙 v3・記憶 on・関係 off・`tools/probe_poi_ref.py`): 在席の体 × 刻み 241,438 のうち 4.3%(10,279)が店のセルの外・4.7% が歩いている途中・同じ単位の組 × 刻み 861,946 のうち 7.9%(68,238)がその体を含む。11c で成立時に 2 m を超えた会話は全部同じ単位で、最大 418 m(node)・498 m(edge)=§5。直すのは親の判断(腕 distance だけで「店のセルの中に居る体だけを単位に数える」か、エンジンで歩き出しに在席を解くか=後者は既定の結果も動く(席の数え方))。

### 2-2 漏れ(切り替えていない・切り替えられない所)

| 所 | 今の判定 | 扱い |
|---|---|---|
| 名指しの相手へ歩く意図(段 2c) | 相手の**セル**へ歩く(相手のノードへは歩かない)。同じセルで d より遠い名指しは、腕 distance では届く別の体に替わる | 近づく口が無い=空間の段 1・2(位置と移動)で直す。B5 の半径 10.3 m の中で d より遠い人を名指しすると話せない |
| 群れ歩き・同行の計器(`norm_meter`) | 同セル ∧ 同じ行き先 ∧ 2 m | 計器(判定ではない)なので変えていない=11c の表の値は両方の腕で同じ定義 |
| B4b の活動の行・セルの描写(B2・B4) | セル | 近接の人の判定ではない(場の描写)。セル廃止の段の対象 |
| 古典の方策の「セルで食べている人数」(`classical._eating_by_cell`) | セル | 社会的な影響の材料で近接の判定ではない |
| `Percept.acquaintance_seen`・`nearby_change` | 空 | 値は入れていない(B5 の近接行の `acquainted` から作れる。空間の段 3 の知覚の個人化で) |
| `RelationLayer.partners_in_cell` | セル | 呼び手が無い(使われていない読み口) |
| `Session.cell`・`GateResult` の理由 `not_same_cell`・計数の理由 `left_cell` | 名前だけ | 腕 distance では「届かない」の意味(名と計数の鍵は変えない規則) |

## 3. d・離脱・p(d)・B5 の半径の出典

| 値 | 既定 | 出典 | 扱い |
|---|---|---|---|
| 会話の距離 d | 2.0 m(感度の腕 1.0・2.5) | 10-03 B3(2 m の決め打ちを既定にし宣言)。`resolve.TALK_OPEN_METERS` と同じ値(試験で突き合わせる) | expedient(空間の段 3 の音の伝わり方で置き換える) |
| 離脱の距離 | d+1 m | C9b G7 の成立 2 m・離脱 3 m の幅 | expedient |
| 気づく確率 p(d) | 1/(1+exp((d−16.95)/5.962)) | R-62 §1-2(Loftus & Harley 2005: 75% = 34 ft = 10.4 m・25% = 77 ft = 23.5 m)・R-79 §8-1 の再計算(2 m で 0.925) | 2 点を通る(試験)。近くでも 1 にならない(0 m で 0.945)=上限を 1 に寄せない(R-79 §8-1 の宣言を「寄せない」で置いた) |
| 気づく抽選の打ち切り | 100 m(p < 1e-6) | 自前(p(100) ≈ 9e-7) | expedient |
| 一度気づいた相手は範囲の中で気づいたまま・印を `_acq_until` に同居 | — | 自前 | expedient(つなぎの台帳 `DOC-prox22-notice-sticky`・外す段 T3=親の判断 A4) |
| B5 近接行の半径 | 10.3 m | Fotios, Yang & Uttley 2015 の他の歩行者を注視する距離の中央値(p_notice 答申) | **仮採用**(10-03 §4-2「11a のアジェンダで決める」=決まっていない=10-13b §0-3)。人数は知覚契約の密度逓減 3/2/1 のまま |
| B5 の単位 | 在席中の POI の区画 | 10-03 B5(手元で使える一番小さい単位) | つなぎ(外す段 5-2) |
| 索引の格子 | 2.5 m | 知覚契約の可視性格子 | expedient |

## 4. つなぎの台帳の行(7 行)

| id | 外す段 | 中身 |
|---|---|---|
| `HD-engine.proximity-1af925f4` | 5-3(inferred) | `proximity.py` の見出し「expedient(本モジュール分)」の項 5 個(d=2 m と感度の腕・離脱 d+1 m・打ち切り 100 m・B5 の半径 10.3 m・格子 2.5 m)。why に R-62(Loftus & Harley 2005)と Fotios ほか 2015 の出典(検収 L5・親の判断 A2) |
| `DOC-prox22-named-partner-no-approach` | 5-2(inferred) | 名指しの相手へは相手のセルへ歩く=d の中へ寄る口は無い(親の判断 A3) |
| `DOC-prox22-notice-sticky` | T3(inferred) | 一度気づいた相手は範囲の中で気づいたまま・印を `_acq_until` に同居(親の判断 A4) |
| `DOC-prox22-b5-unit-hub-unmeasured` | 5-2(inferred) | B5 の単位のハブの懸念はいまの単位では測れない=在室は席数の上限で頭打ち(検収 M3) |
| `DOC-prox22-b5-unit` | 5-2(plan) | B5 (a): 同じ単位の中は距離を見ずに会話できる |
| `DOC-prox22-b6-node-position` | 5-1(plan) | B6: 位置の出どころ=node の座標・建物の中の体は店に入る前のノードのまま=「暫定・node 座標」(manifest の `proximity.marks.B6`) |
| `DOC-prox22-b8-node-walk-speed` | 5-1(plan) | B8: node の歩く速さ 0.41 m/s に基づく量=「暫定・node の歩く速さ」(`proximity.marks.B8`・node 幾何のランだけ) |

## 5. 11c の読み直し(この節の表=[reread_11c_review.json](reread_11c_review.json)=親の判断 10-14 の前の回。[reread_11c.json](reread_11c.json) は 10-14 の後の回=§14・生の行 [runs_11c_head.json](runs_11c_head.json)・[runs_11c_wt.json](runs_11c_wt.json)=検収の前・[runs_11c_wt_distance_review.json](runs_11c_wt_distance_review.json)・[runs_11c_wt_cell_review.json](runs_11c_wt_cell_review.json)=直しの後)

条件は前の読み直しと同じ(層化 5,000 体・seed 1・語彙 v3・記憶 on・呼数無制限・1 日)。腕は関係 off / on / on+同席。計器の検算([check_11c.json](check_11c.json)): 格子の列挙=総当たり(600 点・781 組)・計器の側に写した判定の式=`ProximityRule.reach`・`by_unit`(300 体の全組)・距離の箱。**既定 cell の計器は本体 HEAD の src と作業木の src で全部の値が一致**(壁時計と腕の節を除く・node の 6 本・直しの後に回し直しても一致)。**腕 distance の列は直しの後(鍵の載せ替え・描画の知人の印)に回し直した値**(表の道具は同じ鍵の行を後のファイルで置き換える)。

**値は全部「暫定・node 座標」(B6)。群れ歩きと同行は「暫定・node の歩く速さ」(B8)も付く**。

### 5-1 node 幾何

| 量 | mock cell | mock distance | classical cell | classical distance |
|---|---|---|---|---|
| 会話の成立時の距離が 2 m 超(関係 off) | 0.2941 | 0.0252 | — | — |
| 同(関係 on) | 0.4525 | 0.0278 | 0.4065 | 0.008 |
| 同・10 m 超(関係 off) | 0.1961 | 0.0126 | — | — |
| 同・10 m 超(関係 on) | 0.2984 | 0.0231 | 0.3565 | 0.008 |
| 同・最大[m](関係 off) | 66.2 | 80.8 | — | — |
| 同・最大[m](関係 on) | 121.6 | 80.8 | 119.9 | 47.8 |
| 2 m 内なのに別セルの組(刻みあたり・関係 off) | 10.8 | 10.8 | 2.5 | 2.5 |
| 偶然の出会い(2 m/届く知人が載った行・関係 on) | 1,019 | 1,154 | 2 | 14 |
| 同・相手の距離が 0 m ちょうど | 1.0 | 0.9778 | 1.0 | 0.9897 |
| 知人出現の起床の呼(関係 on) | 11,196 | 9,357 | 39,280 | 35,830 |
| 同・起床の時点の知人の距離(中央値・m) | 24.7 | 2.7 | 28.4 | 0 |
| 会話セッション(関係 off) | 204 | 159 | 0 | 0 |
| 会話セッション(関係 on) | 305 | 216 | 460 | 373 |
| セッションの増え方(on ÷ off − 1) | +49.5% | +35.8% | — | — |
| 同席の書き込み(関係 on+同席) | 4,117 | 4,876 | 26,531 | 29,400 |
| 同・検出の距離が 0 m | 0.9993 | 0.9813 | 0.9989 | 0.994 |
| 瞬間の群れ歩き(歩行者・関係 off) | 0.2614 | 0.2634 | 0.2061 | 0.2061 |
| 5 分連続の同行(歩行者・関係 off) | 0.1033 | 0.1054 | 0.0357 | 0.0357 |
| B5 近接行の人数/描画(関係 on) | 3.2 | 2.9 | 6.0 | 5.7 |
| 同・相手が 2 m 内の割合 | 0.797 | 0.8889 | 0.7091 | 0.8133 |
| 同・相手が 10 m 超の割合 | 0.1535 | 0.0578 | 0.2402 | 0.1307 |
| B5 の単位の在室人数の最大(=席数の上限 30 で頭打ち) | 30 | 30 | 30 | 30 |
| 同じ点(node)に重なった体の最大 | 227 | 225 | 504 | 504 |

- classical の関係 off は会話が 0(いまのエンジンでは古典の交際の相手が関係辺から来る)=腕 cell と distance で final も同じ(`40365ccb…`)。前の記録(09-30)の 707 件はその時点のエンジンの値。

### 5-2 edge 幾何(作業木だけ)

| 量 | mock cell | mock distance | classical cell | classical distance |
|---|---|---|---|---|
| 会話の成立時の距離が 2 m 超(関係 off) | 0.1279 | 0.0124 | — | — |
| 同(関係 on) | 0.1928 | 0.0132 | 0.1701 | 0.0073 |
| 同・最大[m](関係 on) | 81.7 | 498.4 | 115.7 | 200.5 |
| 2 m 内なのに別セルの組(刻みあたり・関係 off) | 1.2 | 2.0 | 0.346 | 0.346 |
| 偶然の出会い(関係 on) | 1,302 | 1,313 | 1 | 4 |
| 知人出現の起床の呼(関係 on) | 10,158 | 7,928 | 41,086 | 38,532 |
| 同・起床の時点の知人の距離(中央値・m) | 19.3 | 0 | 19.2 | 0 |
| 会話セッション(関係 off / on) | 172 / 249 | 161 / 227 | 0 / 488 | 0 / 410 |
| 同席の書き込み | 5,573 | 5,981 | 33,137 | 33,911 |
| 瞬間の群れ歩き / 5 分連続の同行 | 0.0177 / 0.0004 | 0.0192 / 0.0004 | 0.0125 / 0 | 0.0125 / 0 |
| B5 近接行の人数/描画(関係 on) | 3.1 | 2.9 | 6.4 | 6.2 |
| 同じ点(node)に重なった体の最大 | 230 | 237 | 520 | 520 |

### 5-3 読み

- **会話の距離**: 腕 distance で成立時に 2 m を超えた会話(mock 関係 on 2.8%・classical 0.8%)は**全部が同じ B5 の単位**(`reach_by_unit_only`=成立 216 件中 6 件・373 件中 3 件・d を超えて単位でもない会話=全部の構成で 0 件)。店の中の体の xy が入る前のノードのまま=店の中の距離は測れない(B6)。最大 418 m(node・mock 関係 on+同席)・498 m(edge・mock 関係 on)は、在席の印が付いたまま店を出て歩いている体(§2-1)=単位の定義の穴(親の判断)。腕 distance の不変条件「成立した会話の相手は必ず届く」は 1 日の全会話で成り立った(試験 §8 も同じ)。
- **知人出現**: 起床の時点の距離の中央値 24.7 m → 2.7 m(classical 28.4 → 0 m)。起床の呼は −16%(mock)・−9%(classical)。「同じ 100 m 升目に入った」から「気づいた」に替わった。
- **会話の量**: セッション mock 関係 on 305 → 216(−29%)・classical 460 → 373(−19%)。関係 off でも 204 → 159(−22%)。偶然の出会いの行はむしろ増えた(1,019 → 1,154)=届く知人が相手の第一候補になるため。
- **同席**: 書き込みは増えた(4,117 → 4,876・26,531 → 29,400)。今の判定は同セル ∧ 2 m、腕 distance は層 ∧ 2 m ∨ 単位=別セルの 2 m 内と同じ店の体が足される。検出の 98〜99% が 0 m のまま(=立っている体は node に重なる=11b を作っていないので「同じノード」と同義のまま=B7 のとおり空間の段 1・2 の後に測る)。
- **群れ歩き・同行**: 計器の定義が同セルのままなので、腕でほぼ動かない(動いた分は生活の動きの差)。
- **B5 の単位の在室人数**(10-03 §4 の確かめ・検収 M3 で読みを直した): 単位 × 刻みの分布は 1 人 46,844・2〜4 人 20,517・5〜9 人 8,702・10〜49 人 5,801・50 人以上 0(mock 関係 off・node・cell)。全 30 行で最大も最小も **30 人**=`engine/processes/crowd.py` の席数(`seats_for_categories`: 飲食の床面積 60 m² ÷ 1 人 2.0 m²=30・expedient)で頭打ちの値(席が埋まると `admit` が入店を断る)。POI の欄 `capacity`(4)は在室の上限ではない(前の版の「席 4 の飲食店」は誤り)。**いまの単位は在席中の店だけ(事務所・家・学校は単位を持たない)なので、10-03 §4 の懸念(百貨店や大きなオフィスビルが 1 つの単位で数千人のハブになる)は測れない**=つなぎの台帳 `DOC-prox22-b5-unit-hub-unmeasured`(外す段 5-2=屋内の単位が入ったら測る)。別の量として、**同じ点(node)に重なる体**は全 30 行で最大 173〜520 体(直しの後の回・関係 off の行 225〜520・関係 on/同席の mock の行 173〜206)=立っている体の node への重なり(B5 の単位の外の問題・空間の段 1・2)。
- **屋内の体の会話の損失**(10-03 §4・指示書 09-30 §3-2 F の穴): 今の判定(cell)で成立した会話を、その時点の位置で腕 distance の判定にかけた数(`lost_under_distance_*`)。屋内=在店・自宅/職場/学校のセルに止まっている体(計器の側の自前の分類=未リサーチ(expedient))。

| 構成(node・関係 on・cell) | 成立 | 届かない | うち両方屋内(届かない/成立) | 片方屋内 | 屋外 | 主な組(届かない) |
|---|---|---|---|---|---|---|
| mock | 305 | 135(44%) | 11 / 47 | 34 / 67 | 90 / 191 | 止まっている体どうし 51・移動中と止まっている 36・在店と止まっている 22・職場どうし 9 |
| classical | 460 | 186(40%) | 116 / 370 | 33 / 41 | 37 / 49 | 職場どうし 93・職場と在店 20・在店と止まっている 19 |

  腕 distance を実際に回すと(直しの後)、両方屋内の会話は mock 47 → 54・classical 370 → 357(相手が同じノードの同僚に替わる)。**屋内の会話の件数はほとんど失われないが、話せる相手は「同じノードに居る同僚・家族」に縮む**(同じ職場のセルでも別のノードの同僚とは話せない)。箱の中の社会(F)の穴の大きさは「件数」より「相手の幅」に出る。classical の職場どうしの 93 件(関係 on の成立の 20%)が、今の判定でだけ届いていた分。edge 幾何では届かない会話が mock 46/249・classical 82/488(両方屋内 1・45)に減る(歩いている体が辺の上に居るため)。

## 6. 索引の費用(P4 の宣言・[index_cost.json](index_cost.json)・検収 M2 の後に測り直した)

(親の判断 10-14 の 1 で気づく抽選を配列で引くようにした後の値と P4 の宣言は §14-1。この節の表の索引・辺・1 組の判定の値は直しの前の回)

39 万体(390,067)を W1 のノードの座標に置いた見積り(uniform=ノードを一様に・hub=体の 2 割を上位 50 ノードに)。関係辺は体あたり 15 本(1 割は空・相手は一様)。壁時計は決定論でない(同じ PC・ほかの作業木のランと同居)。「検収の前」は同じ配置で前の形(同席が全辺に `reach`・`_parts` が全員の座標を float64 に写す)を道具の中で回した値(答えは今の形と同じ=道具の中で突き合わせた)。

| 量 | uniform | hub | 検収の前 |
|---|---|---|---|
| 索引を作る(刻みに 1 回) | 87 ms | 78 ms | 60 ms(前の回・負荷が違う) |
| 索引の大きさ(刻みの中だけ・捨てる) | 21.8 MB(56 B/体=7 本の配列) | 同じ | — |
| B5 の近接行の問い合わせ(1 描画・半径 10.3 m) | 0.083 ms(候補 280 体) | 0.063 ms(候補 541 体) | 0.030〜0.035 ms(前の回) |
| 関係辺を集める(舞台の中の辺 527 万本・刻みに 1 回) | 0.168 s | 0.128 s | 同席と知人出現で 2 回 |
| 辺の見え方(気づく範囲・距離・届く=同席と知人出現が共有・刻みに 1 回) | 0.197 s(範囲の中 5.0 万本・届く 1,559 本) | 0.163 s(5.5 万本・5,908 本) | 知人出現 170 ms(前の回)+同席の全辺の `reach` 0.547 s・0.537 s |
| 1 組の判定(離脱・返事待ち・3 人会話=開いている会話ごと) | 0.0082 ms | 0.0084 ms | 1.478 ms・1.146 ms |
| 気づく抽選(1 組 1 本の counter の流れ) | 13.5 µs/組 | 19.1 µs/組 | splitmix64 の配列演算(知人出現の 170 ms の内) |
| 同・刻みあたりの上側(範囲の中の辺が全部まだ気づいていない) | 0.68 s(5.0 万本) | 1.05 s(5.5 万本) | — |
| 2 m 内の組の列挙(試験と道具の口・ランでは使わない) | 1.3 s(2,283 万組・前の回) | 測らない(組が数千万) | — |

- **宣言(腕 distance だけ・既定 cell は 0)**: 刻みあたり 索引 ≤ 90 ms+関係辺の集め ≤ 0.17 s+辺の見え方 ≤ 0.20 s+気づく抽選 13〜19 µs × 範囲の中で気づいていない辺の数(39 万体の上側 0.7〜1.0 s)(関係 on・全員が舞台の中の上側=実際のランは舞台の外の体の辺を先に落とす)+開いている会話 1 つあたり 0.01 ms+描画 1 回あたり +0.06〜0.08 ms。
- **気づく抽選は鍵の載せ替え(A1)で重くなった**: 遠い辺(30〜100 m)は p が小さく気づかないので、範囲の中に居る間は毎刻み引き直す。1 本ごとに `core.rng.stream` で Philox の生成器を作る(約 13〜19 µs)ので、splitmix64 の配列演算(前の回は範囲の判定を含めて 170 ms)より重い。5,000 体・1 日の実測は 1 日 29〜88 万本(11c の腕 distance の関係 on の 8 本・刻みあたり 200〜610 本=3〜8 ms・1 日 4〜12 s)。39 万体では辺の数に比例して上の上側に近づく。縮める案(親の判断): (a) Philox を配列で回す口(`np.random.Philox` と同じ出力を返すことを試験で確かめる)・(b) 遠い辺を引く間隔をあける(意味が変わる)・(c) このまま P4 に載せる。
- 逐次ループの新設は気づく抽選の 1 か所(1 組 1 本の流れ=引く組の数ぶん・コードに宣言)。格子の近傍は 2r+1 個の範囲の `searchsorted`。
- 5,000 体・1 日(検収の前・作業木・続けて 1 本ずつ): classical+記憶+関係 cell 73.1 s → distance 78.4〜80.5 s(+7〜10%・主に判断の系の描画=B5 の近接行)。直しの後の 5,000 体の壁時計は、ほかの作業木のランと同居したので比べていない。
- 費用を縮める余地(未着手): 上の (a)(b)・索引を舞台の中で動いた体だけ作り直す。

## 7. byte-check

### 7-1 最初の回(検収の前)

- **既定 cell(19 構成)**: [byte_check_prox22.json](byte_check_prox22.json)=本体 HEAD `2bc7a4b` の src の写し(head)と作業木の src(`--src`)。**19/19 構成で 25 欄とも同じ**(final・呼数・テープの全部の列・行動の件数・起床の内訳・behavior/full の最後・締めの後の 2 本・暦・資産の指紋)。最初の 1 回の後に腕 distance の道だけを速くした(索引の範囲の引き方・気づく判定の先の打ち切り・描画の並べ方)ので、作業木の側を最後のコードで回し直した値(2 回とも 19/19 同じ)。
- **腕 distance(4 構成)**: [byte_check_prox22_distance.json](byte_check_prox22_distance.json)(a=HEAD の既定・b=作業木の腕 distance・d=2 m・最後のコード)。速くする前の 1 回と final・呼数・テープの列・行動の件数・起床の内訳が全部同じ(速くした所は答えを変えていない)。動いた量(腕の裏=動いて当然):

| 構成 | final(HEAD → 腕) | 呼数の差 | 会話の起床の呼 | 知人出現の呼 | 食事 | 壁時計 cell → distance(最後の回・並べて回した値) |
|---|---|---|---|---|---|---|
| w6_v3_default | 5f7ae9ff → 1db45a1f | −320 | 3,592 → 2,989 | 0 → 0 | 4,559 → 4,380 | 41.1 → 45.3 s |
| w6_v1_default | 24375ee3 → 9d7cc9d6 | −362 | 2,540 → 2,044 | 0 → 0 | 0 → 0 | 28.3 → 31.7 s |
| v3_mem_rel | 73a78288 → b1b93881 | −623 | 3,897 → 3,148 | 3,069 → 2,791 | 4,658 → 4,554 | 54.5 → 62.9 s |
| v3_classical_mem_rel | 4c512a1f → 5e4c6915 | −894 | 1,287 → 967 | 11,674 → 10,206 | 9,802 → 9,793 | 78.1 → 96.6 s |

  動かなかった欄: テープの列の名・顕著行為と出動・暦・資産の指紋(どの構成も)。語彙 v1(関係 off)も動くのは、会話の開始と離脱と B5 の近接行が腕で替わるため。壁時計は cell の 19 構成(4 並び)と distance の 4 構成(2 並び)を同時に回した値=決定論でない(続けて 1 本ずつ回した値は §6)。

### 7-2 検収の直しの後(既定 cell・4 構成)

[byte_check_prox22_review_cell4.json](byte_check_prox22_review_cell4.json): 本体 HEAD `bf52089` の src の写し(錨はエンジンが開く 3 本だけ写した=検収 L7)と、直しの後の作業木の src。**4/4 構成で 25 欄とも同じ**。

| 構成 | final | 呼数 |
|---|---|---|
| w6_v3_default | 5f7ae9ff | 65,597 |
| w6_v3_activity_off | e0054a83 | 50,301 |
| w6_v1_default | 24375ee3 | 51,835 |
| v3_mem_rel | 73a78288 | 69,111 |

### 7-3 腕 distance(直しの後)と鍵の載せ替えで動いた量

[byte_check_prox22_distance.json](byte_check_prox22_distance.json)(a=本体 HEAD `2bc7a4b` の既定・b=直しの後の作業木の腕 distance・d=2 m):

| 構成 | final(HEAD → 腕) | 呼数 | 会話の起床の呼 | 知人出現の呼 | 食事 |
|---|---|---|---|---|---|
| w6_v3_default | 5f7ae9ff → 1db45a1f | 65,597 → 65,277 | 3,592 → 2,989 | 0 → 0 | 4,559 → 4,380 |
| w6_v1_default | 24375ee3 → 9d7cc9d6 | 51,835 → 51,473 | 2,540 → 2,044 | 0 → 0 | 0 → 0 |
| v3_mem_rel | 73a78288 → 4b530319 | 69,111 → 68,244 | 3,897 → 3,143 | 3,069 → 2,893 | 4,658 → 4,603 |
| v3_classical_mem_rel | 4c512a1f → 48c38ddf | 106,565 → 105,451 | 1,287 → 908 | 11,674 → 10,183 | 9,802 → 9,841 |

[byte_check_prox22_keyswitch.json](byte_check_prox22_keyswitch.json)(a=検収の前の腕 distance・b=直しの後の腕 distance)=鍵の載せ替え(A1)と描画の知人の印(L1)で動いた量(M2 は答えを変えない形=試験で `reach` と突き合わせた):

| 構成 | final | 呼数 | 会話の起床の呼 | 知人出現の呼 | 食事 |
|---|---|---|---|---|---|
| w6_v3_default(関係 off) | 1db45a1f → 1db45a1f | 同じ | 同じ | 0 → 0 | 同じ |
| w6_v1_default(関係 off) | 9d7cc9d6 → 9d7cc9d6 | 同じ | 同じ | 0 → 0 | 同じ |
| v3_mem_rel | b1b93881 → 4b530319 | 68,488 → 68,244(−0.4%) | 3,148 → 3,143 | 2,791 → 2,893(+3.7%) | 4,554 → 4,603 |
| v3_classical_mem_rel | 5e4c6915 → 48c38ddf | 105,671 → 105,451(−0.2%) | 967 → 908 | 10,206 → 10,183(−0.2%) | 9,793 → 9,841 |

- 関係 off の 2 構成はテープの列まで 25 欄とも同じ(気づく抽選と描画の知人の印は関係の層が無いと動かない)。関係 on の 2 構成の動きは、抽選の乱数が替わった分と、描画の知人が「描画ごとの引き直し」から「気づいた印」に替わった分を合わせた量(2 つは分けて測っていない)。
- 壁時計はほかの作業木のランと同居したので載せない。

## 8. 試験

- 新しい試験 `tests/engine/proximity/`(60 本・slow 2 本を含む。検収の前は 49 本=下の「〔直し〕」が足した分):
  - `test_index.py`(13): 総当たりとの一致(600 点・d=1.0/2.0/2.5/10.3・2 m で 781 組)・層をまたがない・`within`/`query_many`・部分集合と点からの問い合わせ・B5 の単位・座標の範囲の外を断る。〔直し〕配列は読み取り専用で欄の付け替えと消すのを断る(L3)・`unit_members_many` が 1 つずつ引いたのと同じ。
  - `test_rule.py`(20): アジェンダ §2-1 の合成の 2 体(別セルの 1 m は話せる・同セルの 3 m は話せない・層が違う 1 m は話せない)・B5 の単位・舞台の外・境の 2 m・rule=None と cell は今のまま(負の対照)・感度の腕 1.0/2.5 と離脱のヒステリシス・d と `TALK_OPEN_METERS` の一致・p(d) が R-62 の 2 点を通る・`notice_range` の先の打ち切りが全部を見たときと同じ・切替口の検査・manifest の節・層の計器。〔直し〕抽選は 10c の counter の流れ(`stream(seed, "proximity.notice", *k19_counters(…))` と同じ値・状態を持たず一様・時刻/向き/seed で変わる・規模に依らない=A1)・K19 の控えに載り重なり 0・呼び手は `SAFE_SITES` の静的な判定・`edge_view` の届く == `reach`(M2)・再開の腕の検査と見出し(M1)・計器は読み取り専用・層の欄の付け替えを断る(L3)。
  - `test_switch_sites.py`(9): 離脱(別セルでも近ければ続く・d+1 m で切れる)・同席(別セルの 1 m を数え同セルの 3 m を数えない・今の判定の負の対照)・偶然と招待の相手(届く知人が第一候補)・知人出現(1 刻み目は出さない・気づいたまま=各向き高々 1 回・範囲に入って気づく・起床の後 60 分・出て戻ると引き直す・80 m と別の層は気づかない)・`batch_partners` が総当たりと一致・commit の名指しは届くときだけ。〔直し〕描画が読む `aware_of` は印を読むだけ(L1)。
  - `test_runs.py`(18): 世界資産 1,500 体 1 日の腕 distance で**成立と 3 人会話の全部が届く・d を超えて単位でもない会話 0**・B5 の近接行の全員が半径の中か単位か気づいた知人・**腕 cell は HEAD の golden と同じ**(300 体 1 日 final `f0503a35…` 呼数 3,062)・同じ入力で同じ結果・**再開 == 通し**(腕 distance・合成 2 日・止める 750 と 1440)・書きの検査(on/off で final が同じ・scratch の番兵・段 B=系の前後の変化 ⊆ 宣言)・CLI の `--proximity` が環境変数より強い・`--proximity-d`。slow(5,000 体): 感度の腕 1.0/2.5 で全会話が各 d の中。〔直し〕B5 の近接行の半径の外の知人は印が切れていない(L1)・腕の違う再開は止まり同じ腕は通る(cell → distance・distance → cell・d 2.0 → 2.5=M1)・世界資産 1,000 体の再開 == 通し(止める 750)+印を消すと final が動く負の対照(L2)・ランの中の抽選の流れが K19 の検査を通る(A1)。
  - 検収の前: `tests/engine/proximity` 47 passed(37 秒・`-n 4`)・slow 2 passed(61 秒・`-n 2`)。直しの後: 58 passed(全体の回の中)・slow 2 passed(113 秒・`-n 2`・ほかの作業木のランと同居)。
- **検収の直しの後**:
  - 範囲(`tests/engine/proximity tests/engine/bridging tests/engine/time tests/engine/systems tests/engine/test_state_ledger_10b.py tests/engine/test_env_and_sections_10f.py tests/engine/rights/test_rights_manifest.py tests/perception/facts tests/engine/test_relations_8b.py tests/engine/test_conversation.py tests/engine/test_salt_seed_split_10f.py tests/test_cli.py tests/engine/test_state_checks_10f.py tests/engine/test_version_bump_10e.py`): **593 passed**(10 分 40 秒)。
  - 全体(`-m "not gpu and not slow" -n 4 --dist loadfile`・作業木): **4,619 passed・1 failed・1 xfailed**(38 分 44 秒・11c のランとほかの作業木のランと同居)。落ちた 1 本は junction 由来の既知の `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`。
  - `lint-imports` 5 kept(知覚の層は engine を import しない=描画は `NearView` の形だけを使う)。
- 検収の前の回:
  - 関わる既存の試験(会話・関係・C9b・描画・古典の社会・意図・知覚・出来事): 658 passed(8 分 27 秒)。凍結の表の試験(状態台帳・manifest の鍵・設定の道筋の sha・つなぎの台帳・時間の語・系の表): 通過。
  - 全体(`-m "not gpu and not slow" -n 4 --dist loadfile`・作業木): **4,605 passed・3 failed・1 xfailed**(24 分 49 秒・11c のランと同居)。落ちた 3 本: junction 由来の既知の `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`・`tests/engine/rights/test_rights_manifest.py::test_rights_is_the_last_key_and_observed`(末尾の並びの凍結=`proximity` を足して直した)・`tests/engine/bridging/test_manifest_rules_bridges.py::test_values_match_the_ledger_and_the_table`(試験を回している間につなぎの台帳の行の文を直したため=回し直して通過)。直した後の 2 ファイル=16 passed。
  - 最後のコード(腕 distance の道を速くした後)で回し直した範囲(`tests/engine/proximity tests/engine/bridging tests/engine/time tests/engine/systems tests/engine/test_state_ledger_10b.py tests/engine/test_env_and_sections_10f.py tests/engine/rights/test_rights_manifest.py tests/perception/facts tests/engine/test_relations_8b.py tests/engine/test_conversation.py tests/engine/test_salt_seed_split_10f.py tests/test_cli.py`): **536 passed**(4 分 3 秒)。
  - `lint-imports` 5 kept(知覚の層は engine を import しない=描画は規則と索引の形だけを使う)。

## 9. 触った共有ファイル

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/systems/table.py` | perceive_prepare の `paths` に `PX:proximity.*`・`scratch_w` に `near_index`・`reads` に `layers.proximity scratch.near_index`/apply_responses・relations_wake・phase_c・conversation・close_final・day_close・drain の `reads` の末尾に `layers.proximity`(day_close と drain は状態のファイルの見出しのため=検収 M1) |
| `src/shibuya/engine/state_ledger.py`(状態台帳) | 行 `PX`・`PX0` を J0 の後に・`OWNER_CLASSES` の末尾に `proximity`・`EXCLUDED` の末尾に `proximity.rule`(設定)・`_ALLOW_BAND` に読みの許可 2 つ(`engine/proximity.py` の 1 か所に集めた読み・`perception/renderer.py` の自分の層。`agents.band` はセルの層から導く派生=軸 1 no のまま)・docstring の行数と版の注釈。版は上げない |
| `src/shibuya/engine/systems/boxes.py` | `OWNER_NAMES` の末尾に `proximity`・`Layers.proximity`(既定 None)・`SCRATCH_FIELDS` の末尾に `near_index` |
| `src/shibuya/engine/systems/state_io.py`・`run_end.py` | 持ち主の末尾に `proximity`・結果に `proximity_layer`・状態のファイルの見出しに `proximity`(腕 distance だけ・検収 M1) |
| `src/shibuya/cli.py` | `--proximity`・`--proximity-d` と腕を置く行・`run_kind` の腕の判定に環境変数の腕を足した 1 行 |
| `src/shibuya/engine/run.py`・`manifest_sections.py` | manifest の末尾(decision_port の後)に `proximity`・import 1 行・`MOTION_RNG_DOMAINS` に 1 語 |
| `src/shibuya/engine/rng_audit.py` | `SAFE_SITES` に 1 か所・〔10-14〕`RNG_FUNCS` に `philox_array`・`StreamRecorder` が包む |
| `src/shibuya/core/rng.py` | 〔10-14〕`__all__` の末尾に 3 つ・関数を末尾に足しただけ(既存の関数は不変) |
| `tests/engine/test_salt_seed_split_10f.py` | 〔10-14〕用途名の走査の `_RNG_FUNCS` に `philox_array`(足しただけ) |
| テープの列 | 変えていない |
| 凍結の表(増えた分だけ) | `tests/engine/time/manifest_keys_frozen.json`(115 → 116 個・末尾に `proximity`)・`tests/engine/test_env_and_sections_10f.py`(`PX22_KEYS`・末尾の並び・`CONFIG_PATHS_SHA256` `89e426b3…df47dae50b9065` → `58e69d8f…4633ee218f22cf3`=proximity の設定の子 12)・`tests/engine/time/test_t0_tm9_fields.py`・`tests/perception/facts/test_percept_schema.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/rights/test_rights_manifest.py`(末尾の並び)・`tests/engine/test_state_ledger_10b.py`(外の状態 102 → 104・全体 193 → 195・鍵の末尾 `PX`・`PX0`・行の軸・`agents.band` の許可 1 → 3)・`tests/engine/bridging/test_bridging_ledger.py`(見出し 79 → 80・ファイル 76 → 77・項 348 → 353・HD 行 80)・`tests/engine/test_state_checks_10f.py`(`SAFE_SITES` 14 → 15)・`docs/bench/analysis/wallbounce-1012/run-day-decomp/local-assignment.json`(`near_index` の 1 項=HEAD の局所ではない注つき) |
| `docs/design/bridging-ledger.json` | 末尾に 7 行(§4) |

ほかの段(1-7・1-8b・2-0)と当たる所(取り込みの順は 1-8b の後=親の判断 A5・rebase は親の合図の後): `MOTION_RNG_DOMAINS` と `SAFE_SITES` の数・manifest の末尾の並び・状態台帳の行の並びと数・持ち主の名の末尾・`SCRATCH_FIELDS` の末尾・`CONFIG_PATHS_SHA256`・つなぎの台帳の見出しの数と項・`table.py` の perceive_prepare/apply_responses/conversation の宣言。

## 10. 限界と仮採用(10-13b §0-3=既定 off の腕・戻せる形)

1. **B5 近接行の半径 10.3 m は仮採用**(10-03 §4-2 で「11a のアジェンダで決める」とされたが決まっていない)。人数の切り方(密度逓減 3/2/1)は知覚契約の 09-06 の決定のまま=「k が隠れた定数」(10-03 §4-2 の指摘)は半径で届く距離を止めただけで、k そのものは残る。
2. **知人に気づく抽選は刻みごと**(発注の鍵=相手の id と刻み)。一度気づいた相手は範囲(100 m・同じ層)の中に居る間は気づいたまま=刻みごとに引き直さない(引き直すと 0 m の家族が 5.5% の刻みで「見失って」毎時起きる)。R-62 の値は「その距離で 1 回見たときの見分け」の割合なので、刻みごとの抽選は遠い知人に早めに気づく向きに歪む(30 m で p=0.10/分=10 分ほどで気づく)。上限を 1 に寄せる宣言(R-79 §8-1)は「寄せない」で置いた。
3. **気づいた印は同一相手の不応期の配列に同居**(新しい保存の欄を足すと既定の腕の full-hash が動くため)。腕 distance では `_acq_until` が「不応期の終わり」と「気づいている刻みの終わり」の両方の意味を持つ。
4. **気づく抽選は 1 組 1 本の counter の流れ**(親の判断 A1 で splitmix64 から載せ替えた)を `philox_array` で組をまとめて引く(親の判断 10-14 の 1・値は同じ)。引くのは範囲の中で気づいていない辺だけ。遠い辺は気づかないまま毎刻み引き直す(費用は §14-1)。
5. **B5 の単位は在席中の POI だけ**(家・職場・学校は単位を持たない=node の座標で測る)。店に入っても体の xy は移らない=同じ店の体は店のセルの中で離れていても話せる(つなぎ)。在席の印は歩き出しでは解かれない(エンジンの今の挙動)ので、腕 distance では店のセルの中に居る体だけを単位に数える(親の判断 10-14 の 2・§14-2)。エンジン側の直し(歩き出しで在席を解く=既定の席の数え方が動く)は親が PENDING §2 の 2-4 の候補に載せる。
6. **名指しの相手に近づく口が無い**(§2-2)。同じセルで d より遠い名指しは届く別の体に替わる(LLM のランで「見えている 8 m 先の人」に話しかけられない)。
7. **立っている体は node に重なる**(11b は作らない=B1・B2)。同席と偶然の 98〜100% が 0 m・同じ点に最大 520 体。腕 distance の判定の値は「同じノードに居るか」とほぼ同じ意味(前の記録 §0-1 と同じ)=空間の段 1・2 の後に測り直す(B7)。11c の値は全部「暫定・node 座標」。
8. 腕は環境変数と CLI だけ(`run_day` の引数にしない=設定の指紋と `run_kind` の引数の比べに入らない)。CLI の `cli.run` では環境変数の腕も `run_kind=arm` にした(結果が変わる腕なので)。
9. 状態台帳の版は上げない(行 PX・PX0 はどちらのハッシュにも状態のファイルにも入らない=1-3・1-6・1-9・1-2・1-8 と同じ理由)。腕 distance の再開では層の計器が 0 から(診断)。
10. 腕 distance の費用は §6 の宣言のとおり。既定にする段の前に予算(予算宣言の設計書=親)へ載せる。
11. 屋内の分類(在店・自宅/職場/学校のセルに止まっている)は計器の側の自前の分類(未リサーチ(expedient))。

## 11. 親に確かめてほしいこと

1〜4 は親の判断を受けた(§13)。残りは並んで進んでいる段との当たり(§9 の最後・取り込みは 1-8b の後=親の合図)。

## 12. 再現

```
D=docs/bench/analysis/wallbounce-1012/prox22
B=docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py
# byte-check(本体 HEAD の写し=git archive <HEAD> src と、エンジンが開く錨 3 本だけ+budget+w6-regen と祝日の表・作業木の src)
# 〔検収 L7〕10e の手順は docs/bench/anchors を丸ごと写す(封印の錨の写しが scratch に残る)=次からは錨を
#  ssb2021_activity_prior_v0.json・hunger_energy_anchors_v0.json・commute_time_dist_r3.json の 3 本に絞る(この段の直しで実施)
python $B side --src <HEAD の写し>/src --label head --scratch <scratch> --out <scratch>/head.json
python $B side --src src --label prox22 --scratch <scratch> --out <scratch>/prox22.json
python $B compare --a <scratch>/head.json --b <scratch>/prox22.json --out $D/byte_check_prox22.json
SHIBUYA_PROXIMITY=distance python $B side --src src --label prox22dist \
    --only w6_v3_default,w6_v1_default,v3_mem_rel,v3_classical_mem_rel --scratch <scratch> --out <scratch>/dist.json
# 11c(計器の検算・HEAD の cell・作業木の cell と distance・表)
python $D/tools/reread_11c.py check --out $D/check_11c.json
python $D/tools/reread_11c.py runs --label head --src <HEAD の写し>/src --modes cell --out <scratch>/r11c_head.json
python $D/tools/reread_11c.py runs --label wt --src src --modes cell,distance --geometries node,edge --out <scratch>/r11c_wt.json
python $D/tools/reread_11c.py table --runs <scratch>/r11c_head.json <scratch>/r11c_wt.json --out $D/reread_11c.json
# B5 の単位に残る歩いている体の探り(腕 cell・5,000 体・1 日・§2-1)
python $D/tools/probe_poi_ref.py cell
# 39 万体の費用
python $D/tools/index_cost.py --out $D/index_cost.json
# 〔親の判断 10-14〕5,000 体 1 日の気づく抽選の刻みあたりの時間(配列 vs 1 組ずつ・値の突き合わせつき)
PYTHONPATH=src python $D/tools/notice_cost.py --out $D/notice_cost.json
# 〔親の判断 10-14 の後〕byte-check(本体 HEAD 533846b の写し=錨 3 本)と 11c の全部(HEAD の cell・作業木の cell と distance)
python $B side --src <533846b の写し>/src --label head533 --only $F --scratch <scratch> --out <scratch>/head533_4.json
python $B side --src src --label r2 --only $F --scratch <scratch> --out <scratch>/r2_cell_4.json
python $B compare --a <scratch>/head533_4.json --b <scratch>/r2_cell_4.json --out $D/byte_check_prox22_r2_cell4.json
SHIBUYA_PROXIMITY=distance python $B side --src src --label r2dist \
    --only w6_v3_default,w6_v1_default,v3_mem_rel,v3_classical_mem_rel --scratch <scratch> --out <scratch>/r2_dist_4.json
python $B compare --a <scratch>/head533_dist.json --b <scratch>/r2_dist_4.json --out $D/byte_check_prox22_r2_distance.json
#  (head533_dist.json=head533_4.json の 3 構成+同じ写しで回した v3_classical_mem_rel)
python $D/tools/reread_11c.py runs --label head --src <533846b の写し>/src --modes cell --out <scratch>/r11c_head3.json
python $D/tools/reread_11c.py runs --label wt --src src --modes distance --geometries node,edge --out <scratch>/r11c_wt_dist3.json
python $D/tools/reread_11c.py runs --label wt --src src --modes cell --geometries node,edge --out <scratch>/r11c_wt_cell3.json
python $D/tools/reread_11c.py table --runs <scratch>/r11c_head3.json <scratch>/r11c_wt_cell3.json \
    <scratch>/r11c_wt_dist3.json --out $D/reread_11c.json
#  (記録の生の行: r11c_head3 → runs_11c_head_1014・r11c_wt_cell3 → runs_11c_wt_cell_1014・
#   r11c_wt_dist3 → runs_11c_wt_distance_1014・前の回の表 → reread_11c_review.json)
# 検収の直しの後(既定 cell 4 構成=本体 HEAD bf52089 の写し・錨 3 本/腕 distance 4 構成/鍵の載せ替えの前後)
F=w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel
python $B side --src <bf52089 の写し>/src --label headbf --only $F --scratch <scratch> --out <scratch>/headbf_4.json
python $B side --src src --label rv --only $F --scratch <scratch> --out <scratch>/rv_cell_4.json
python $B compare --a <scratch>/headbf_4.json --b <scratch>/rv_cell_4.json --out $D/byte_check_prox22_review_cell4.json
SHIBUYA_PROXIMITY=distance python $B side --src src --label rvdist \
    --only w6_v3_default,w6_v1_default,v3_mem_rel,v3_classical_mem_rel --scratch <scratch> --out <scratch>/rv_dist_4.json
python $B compare --a <scratch>/head.json --b <scratch>/rv_dist_4.json --out $D/byte_check_prox22_distance.json
python $B compare --a <scratch>/dist.json --b <scratch>/rv_dist_4.json --out $D/byte_check_prox22_keyswitch.json
python $D/tools/reread_11c.py runs --label wt --src src --modes distance --geometries node,edge --out <scratch>/r11c_wt_dist2.json
python $D/tools/reread_11c.py runs --label wt --src src --modes cell --geometries node --out <scratch>/r11c_wt_cell2.json
python $D/tools/reread_11c.py table --runs <scratch>/r11c_head.json <scratch>/r11c_wt.json <scratch>/r11c_wt_dist2.json \
    <scratch>/r11c_wt_cell2.json --out $D/reread_11c.json   # 同じ鍵の行は後のファイルが勝つ=直しの後の回
# 記録の生の行: r11c_head → runs_11c_head・r11c_wt → runs_11c_wt・r11c_wt_dist2 → runs_11c_wt_distance_review・
#  r11c_wt_cell2 → runs_11c_wt_cell_review
```

## 13. 検収の直しと親の判断

検収([review.md](review.md))=条件つき受入。親の判断(A1〜A6)と欠陥(M1〜M3・L1〜L9)を次のとおり直した。rebase はしていない(1-8b の取り込みの後に親の合図)。

| 項 | 中身 | 直し |
|---|---|---|
| A1(必須) | 気づく抽選の鍵を 10c の counter に | `ProximityRule.notice_u` を `core.rng.stream(seed, "proximity.notice", *k19_counters(時刻の鍵, 体, 相手)).random()` に(seed は動きの側)。`MOTION_RNG_DOMAINS`・`SAFE_SITES` に載せ、K19 の控え(`StreamRecorder`)に載る試験を単体とランの中の 2 本。splitmix64 の混ぜ方・`notice_salt64`・用途の印 `b"an\x00"` は消した。動いた量は §7-3(関係 off は不変・関係 on は呼数 −0.2〜−0.4%)。費用は増えた(§6) |
| A2 | HD 行に R-62 と Fotios | `HD-engine.proximity-1af925f4` の why に R-62(Loftus & Harley 2005)と Fotios, Yang & Uttley 2015(検収 L5 も同じ) |
| A3 | 名指しの相手へ寄る口が無い | `DOC-prox22-named-partner-no-approach`(外す段 5-2・expedient・inferred) |
| A4 | 気づいたまま・印の同居 | `DOC-prox22-notice-sticky`(外す段 T3) |
| A5 | 取り込みの順 | 1-8b の後(manifest の末尾 … → decision_port → tools → speech_port → proximity・状態台帳の末尾 … CT5・S8・S8M・PX・PX0)。rebase は親の合図の後(未実施) |
| A6 | 口の約束の節 | 親が足す(作業木では触っていない) |
| M1 | 腕の違う再開が止まらない | 状態のファイルの見出しに `proximity`(`mode`・`d_m`・腕 distance のときだけ書く=腕 cell の見出しは今のまま)。再開の組み立てで `check_resume` が今の腕と比べ、違えば `ValueError`(見出しに無い=cell)。設定の指紋は変えない。day_close と drain の宣言に `layers.proximity`。試験=cell → distance・distance → cell・d 2.0 → 2.5 が止まり同じ腕は通る(3 通り)+単体 |
| M2 | 毎刻みの費用 2 つが宣言に無い | `RelationLayer._edge_view` が刻みに 1 回だけ辺を集め、`ProximityRule.edge_view`(範囲・距離・届く)を同席と知人出現で共有。`_parts` は添字で集めてから float64(全員の写しを作らない)=離脱(`_left_reach`)・返事待ち・3 人会話も同じ口。`_reach_hits` は消した。§6 を測り直した(同席の全辺 0.54 s → 共有の見え方 0.16〜0.20 s・1 組 1.1〜1.5 ms → 0.008 ms) |
| M3 | 「最大 30」の読み | 30 は crowd の席数の上限(飲食 60 m² ÷ 2.0 m²)・「席 4」は `capacity` の欄で在室の上限ではない、と読みを直した(§0・§5)。ハブの懸念はいまの単位では測れないと宣言=`DOC-prox22-b5-unit-hub-unmeasured`(外す段 5-2) |
| L1 | 描画の知人が印を見ない | 描画は関係の層の印を読むだけ(`RelationLayer.aware_of` を `NearView.aware` で渡す・描画ごとに引き直さない・印の無いランは足さない)。試験=読むだけ・ランの中で半径の外の知人は印が切れていない |
| L2 | 再開の試験の力が弱い | 世界資産 1,000 体の腕 distance の再開 == 通し(止める 750)+負の対照(再開の最初に印を消すと final が動く)。1 日の抽選は 124 本(試験の下限は 50) |
| L3 | 実行時の守り | `ProximityLayer` に `__slots__` と `__setattr__`(最初の 1 回だけ)・`__delattr__` の守り。計器は `meter_view`(入れ子まで読み取り専用の写し。`meter` の名は外の名と衝突したので替えた)。`SpatialIndex` も `__slots__` と守り・配列は `setflags(write=False)` |
| L4 | 索引の置き場所 | `engine/spatial_index.py` に分けた |
| L5 | HD 行に R-62 | A2 と同じ |
| L6 | 記録の数 | manifest の鍵 115 → 116(§9)・同じ点の重なりは全行で(検収の時点 159〜520・直しの後の回 173〜520)(§0・§5-3) |
| L7 | `_bc/` の錨の写し | 直しの後に `_bc/` を消した(中身は読んでいない)。直しの byte-check は錨を 3 本だけ写した。§12 に「10e の手順は `docs/bench/anchors` を丸ごと写す=次からは 3 本に絞る」 |
| L8 | 「毎 tick」の語 | 新しい docstring は「毎刻み」 |
| L9 | 用途の印が一覧に無い | Philox に載せ替えたので対象が無くなった(印は消した) |

親に確かめてほしいこと(直しで新しく出たもの)=親の判断 10-14 で決まった(§14): (1) 気づく抽選の費用(§6 の (a)〜(c))。(2) B5 の単位に店を出て歩いている体が残る(在席の印が歩き出しで解かれない・§2-1)。腕 distance だけで単位を「店のセルの中に居る体」に絞るか、エンジンで歩き出しに在席を解くか(既定の結果も動く)。(3) 描画の知人を印で読むようにした分、B5 の近接行の 10 m 超の割合が増えた(mock 0.031 → 0.058・classical 0.046 → 0.131=気づいている遠い知人と起床の後 60 分の不応期の相手が、100 m の中に居る間は毎描画に載る)。

## 14. 親の判断 10-14 の直し(1〜3)

rebase はしていない(1-8b の取り込みの後に親の合図)。既定の腕 cell の道は触っていない(§14-4 の byte-check)。

### 14-1 気づく抽選を配列で引く(案 (a))

- `core.rng.philox_array(master_seed, domain, counters, *, words=1) -> (行の数, words) の uint64`: Philox4x64-10 を numpy の配列演算で回す(定数は Random123・numpy の `philox.h` と同じ・64×64 → 128 bit の積は 32 bit に割って掛ける)。鍵は `derive_key`(1 回)・行ごとのカウンタは 4 語に詰める(`philox` と同じ)。numpy は引く前にカウンタを 1 進める(繰り上がりつき)ので、b ブロック目は「行のカウンタ + b + 1」。ほかに `k19_counter_array`(`k19_counters` の配列の版=0 語目を空ける)と `unit_float`(`Generator.random()` と同じ写し方)。既存の関数は変えていない。
- 気づく抽選 `ProximityRule.notice_u` は `philox_array(seed, "proximity.notice", k19_counter_array(時刻の鍵, 体, 相手))` の 1 語を `unit_float` に=鍵・語の並び・値は前と同じ。逐次ループ(1 組ずつ)は無くなった。
- K19: 静的な走査(`rng_audit.scan_sites`)が `philox_array` を読む(引く語数=`words`=1 → 「静的に 4 語以内」・`SAFE_SITES` は同じ 15 か所)。`StreamRecorder` は `philox_array` も包み、1 行を 1 本の流れとして控える(使ったブロック=`ceil(words / 4)`)=今までの K19 の試験(単体・ランの中)がそのまま通る。用途名の表の試験の `_RNG_FUNCS` に `philox_array` を足した。
- 試験([test_philox_array.py](../../../../../tests/engine/proximity/test_philox_array.py)): 1 万行 × 語数 1/2/4/5/8/9 で `philox(…).random_raw(語数)` と全部一致(0 語目・1 語目の繰り上がりの境と全部 0 を含む)・直に作った `np.random.Philox(key=…, counter=…)` とも一致・`unit_float` が `Generator.random()` と 1 万行で一致・`k19_counter_array` の並び・行を抜き出しても同じ値・入力の検査。`notice_u` は 1 組ずつ `stream` で引いた値と 4,000 組で一致。ランの中でも全刻みで一致([notice_cost.json](notice_cost.json)=違えば止まる)。
- **時間**(壁時計は決定論でない・ほかの作業木のランと同居):

| 量 | 1 組ずつ(前) | 配列(後) |
|---|---|---|
| 5,000 体・1 日・mock(v3_mem_rel の構成・抽選 97,282 本=刻みあたり平均 93 本・最大 209) | 刻みあたり 平均 1.28 ms・p95 2.49 ms・最大 5.7 ms・1 日 1.33 s | 平均 0.34 ms・p95 0.39 ms・最大 2.0 ms・1 日 0.35 s |
| 5,000 体・1 日・classical(v3_classical_mem_rel・149,010 本=平均 144 本・最大 369) | 平均 1.95 ms・p95 4.02 ms・最大 10.2 ms・1 日 2.02 s | 平均 0.35 ms・p95 0.41 ms・最大 1.5 ms・1 日 0.36 s |
| 39 万体・範囲の中の辺を全部引く上側(uniform 5.0 万本・hub 5.7 万本)([index_cost.json](index_cost.json)) | 1 組 8.3〜9.9 µs(=刻みあたり 0.42〜0.56 s) | **刻みあたり 27〜30 ms**(1 組 0.52〜0.53 µs) |

- **P4 の宣言(腕 distance・39 万体・刻みあたり・上側)**: 索引 60〜63 ms+関係辺の集め 0.13 s+辺の見え方(同席と知人出現で共有)0.14〜0.15 s+気づく抽選 0.03 s+開いている会話 1 つあたり 0.02 ms+描画 1 回あたり +0.03 ms(B5 の近接行)。気づく抽選は 0.3 s を大きく下回る=(c) は要らない。案 (b) は採っていない。辺の見え方は B5 の単位の絞り(14-2)を入れた後に、単位を体の数ぶん 1 回だけ作って辺に配るようにした(辺ごとに印とセルを集め直さない・答えは同じ=試験と下の確かめ)。

### 14-2 B5 の単位を「同じ poi_ref かつ店のセルの中に居る体」に絞る(腕 distance だけ)

- `ProximityRule` に `poi_cell`(`world.pois.cell` の読むだけの写し・比べない欄)と `units(agents)`・`_unit_at` を足した。単位=在席の印 `poi_ref` があり、体のセルがその POI のセルと同じ体(ほかは −1)。判定(`reach`・`stay`・`by_unit`・`edge_view`)・刻みの索引の単位(描画の B5 の単位の仲間・計器の在室人数)・束の相手の候補(`batch_partners`)が全部この単位を使う。組み立ての口 `rule_from` は `poi_cell` を必ず受け取る(None は断る)。試験の合成の体だけが `poi_cell=None`(印をそのまま単位)。manifest の `proximity.schema` を `shibuya.proximity/3` に、`unit_source` を絞った定義に。
- つなぎの台帳 `DOC-prox22-b5-unit` の what に絞りを書いた。**エンジン側の直し(歩き出しで在席 `poi_ref` を解く=既定の席の数え方が変わる)は親が PENDING §2 の 2-4 の候補に載せる**。その材料の探りの数(腕 cell・5,000 体・1 日・[tools/probe_poi_ref.py](tools/probe_poi_ref.py)): 在席の体 × 刻み 241,438 のうち **4.3%(10,279)が店のセルの外**・4.7% が歩いている途中・同じ単位の組 × 刻み 861,946 のうち **7.9%(68,238)がその体を含む**・絞る前の腕 distance では同じ単位で成立した会話の相手が**最大 418 m(node)・498 m(edge)**。11c の計器で数え直すと、在席の体 × 刻みのうち店のセルの外は mock 3.6〜4.7%・classical 9.3〜13.4%。
- **11c の distance の列**(10-14 の前の回 → 後・[reread_11c.json](reread_11c.json)・前の回は [reread_11c_review.json](reread_11c_review.json)):

| 量(関係 on) | mock node | classical node | mock edge | classical edge |
|---|---|---|---|---|
| 会話の成立時の距離が 2 m 超の割合 | 0.0278 → 0.023 | 0.008 → 0.0029 | 0.0132 → 0.0048 | 0.0073 → 0 |
| 同・最大[m](関係 on / on+同席) | 80.8 / 418.0 → 80.8 / 80.8 | 47.8 / 187.3 → 26.5 / 26.5 | 498.4 / 498.4 → 28.3 / 0 | 200.5 / 200.5 → 0 / 0 |
| 単位だけで届いた会話 / 成立 | 6 / 216 → 5 / 217 | 3 / 373 → 1 / 349 | 3 / 227 → 1 / 209 | 3 / 410 → 0 / 419 |
| d を超えて単位でもない会話 | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| B5 の単位の在室人数の最大(絞った単位・絞る前の印) | 30 → 30(印 30) | 30 → 30(印 30) | 30 → 30(印 30) | 30 → 30(印 30) |
| 両方屋内の会話(node) | 54 → 51 | 357 → 331 | — | — |

  在室の最大は絞っても 30(crowd の席数の上限で止まる店の中の体は店のセルに居る)。残った 80.8 m(mock node)は同じ店のセルの中で、店に入る前のノードの位置のまま離れている体どうし(B6=つなぎのまま)。
- 11c の cell の列は HEAD(`533846b` の写し)と作業木で全部の値が一致(node の 6 本・新しい計器で回し直した)。cell の列の計器の定義(在店の分類・「腕 distance では届かない会話」)も絞った単位で数え直した(mock は変わらず・classical node は届かない 186 件のうち両方屋内 116 → 114 などの分類の移り)。

### 14-3 B5 の近接行は半径 10.3 m の中だけ

- 描画が近接行に足す知人は「関係の層の気づいた印があり、かつ同じ層で半径 10.3 m の中」だけ。気づいたままの印は知人出現の起床の条件にだけ使う(つなぎの台帳 `DOC-prox22-notice-sticky` の what に書いた)。B5 の単位の仲間も索引の単位(絞った単位)から引く。試験: 世界資産 1,500 体の腕 distance で、近接行の全員が半径の中か単位の仲間・半径の外の知人 0・単位の仲間は店のセルの中。
- **10 m 超の割合**(関係 on・B5 の近接行の相手):

| 構成 | L1 の前(検収の前の回) | L1 の後(10-14 の前の回) | 10-14 の後 |
|---|---|---|---|
| mock node | 0.0306 | 0.0578 | **0.0050** |
| classical node | 0.0459 | 0.1307 | **0.0022** |
| mock edge | 0.0143 | 0.0248 | **0.0024** |
| classical edge | 0.0208 | 0.0567 | **0.0013** |

  L1 の前の値より下がった: L1 の前は描画ごとに p(d) を引いて 100 m の中の遠い知人も載せていた。いまは半径の外の知人を載せないので、残る 10 m 超は同じ単位の仲間(店のセルの中)と 10.0〜10.3 m の体だけ。ほかに、近接行の人数/描画は mock 2.95 → 2.79・classical 5.74 → 5.03、2 m 内の割合は 0.889 → 0.939・0.813 → 0.936、知人の行は 35,197 → 23,629・491,527 → 395,990。

### 14-4 byte-check と腕 distance の動いた量

- **既定 cell(4 構成)**: [byte_check_prox22_r2_cell4.json](byte_check_prox22_r2_cell4.json)=本体 HEAD `533846b` の src の写し(錨は 3 本だけ)と作業木の src。**4/4 構成で 25 欄とも同じ**(5f7ae9ff/65,597・e0054a83/50,301・24375ee3/51,835・73a78288/69,111)。
- **腕 distance(4 構成)**: [byte_check_prox22_r2_distance.json](byte_check_prox22_r2_distance.json)(a=`533846b` の既定・b=作業木の腕 distance・d=2 m)。括弧の中は 10-14 の前の回(§7-3)。

| 構成 | final(HEAD → 腕) | 呼数 | 会話の起床の呼 | 知人出現の呼 | 食事 |
|---|---|---|---|---|---|
| w6_v3_default | 5f7ae9ff → 3f1358f0(1db45a1f) | 65,597 → 65,195(65,277) | 3,592 → 2,985(2,989) | 0 → 0 | 4,559 → 4,392(4,380) |
| w6_v1_default | 24375ee3 → fa283a5e(9d7cc9d6) | 51,835 → 51,472(51,473) | 2,540 → 2,043(2,044) | 0 → 0 | 0 → 0 |
| v3_mem_rel | 73a78288 → 5f842477(4b530319) | 69,111 → 68,171(68,244) | 3,897 → 3,130(3,143) | 3,069 → 2,890(2,893) | 4,658 → 4,589(4,603) |
| v3_classical_mem_rel | 4c512a1f → c61196ce(48c38ddf) | 106,565 → 105,426(105,451) | 1,287 → 907(908) | 11,674 → 10,183(10,183) | 9,802 → 9,845(9,841) |

  関係 off の 2 構成も動いた(単位の絞りが会話の届く・離脱・B5 の単位の仲間を替え、描画の知人の半径も替わるため)。抽選を配列にした分は値を変えない(試験とランの中の突き合わせ)。辺の見え方の単位の作り方を替えた後に腕 distance の 4 構成を回し直し、上の値と 4 構成とも 25 欄が同じだった(final も同じ)。

### 14-5 試験

- `tests/engine/proximity`: 68 passed(slow を除く・`test_philox_array.py` の 8 本と `test_rule.py` の 2 本=単位の絞り・`rule_from` を足した)・slow 2 passed。辺の見え方の単位の作り方を替えた後も 68 passed。
- 範囲(§8 の範囲の 14 ファイル・ディレクトリ): **603 passed**(6 分 41 秒)。ほかに `tests/engine/decision tests/core tests/perception`(`StreamRecorder` の呼び手を含む): 489 passed。
- `lint-imports` 5 kept。辺の見え方の単位の作り方を替えた後に、状態台帳・系の表・つなぎの台帳・状態の検査の試験を回し直した: 273 passed。

## 15. 本体の最新(`db40de2`)への rebase と再確認

土台を `2bc7a4b` から本体の HEAD `db40de2`(その間に 1-7・2-0・2-3b・2-0b・1-8b と文書が入った)へ移した。手順は 1-7 と同じ: 変えたファイルの控え(作業木の版・土台の版・本体の版)→ 変えたファイルを `checkout` で土台に戻す → 枝を `db40de2` へ早送り(commit は作らない)→ 両方が変えた 21 ファイルを 3 方向の `git merge-file` → 2-2 だけが変えたファイルは作業木の版を戻す。新しいファイル(`proximity.py`・`spatial_index.py`・`tests/engine/proximity/`・この記録)は本体に同じ道が無い。git add と commit はしていない。

| ファイル | 衝突 | 解き方 |
|---|---|---|
| `engine/relations.py`・`engine/resolve.py` | なし(自動で合わさった) | — |
| `engine/manifest_sections.py` | 末尾の節(1-8b の `speech_port` と 2-2 の `proximity`) | `speech_port` → `proximity` の順 |
| `engine/run.py` | import 1 行・manifest の末尾(1-7 の `tools`・1-8b の `speech_port` と 2-2 の `proximity`) | 両方の import・末尾は … → `decision_port` → `tools` → `speech_port` → `proximity`(注の並びも直した) |
| `cli.py` | ランの種類の判定・引数(`--speech-port` と `--proximity`・`--proximity-d`)・腕を置く行 | ランの種類は「発話の口の腕が on」か「近接の腕が cell でない」なら腕・引数と腕を置く行は 1-8b → 2-2 の順に両方 |
| `engine/state_ledger.py` | 見出しの行数・版の注・行(1-7 の `CT5`・1-8b の `S8`・`S8M` と 2-2 の `PX`・`PX0`)・持ち主・除外 | 行は … `J0`・`CT5`・`S8`・`S8M` → `PX`・`PX0`(198 行)・持ち主と除外は `speech` → `proximity` |
| `engine/systems/boxes.py` | `OWNER_NAMES` の末尾の 1 行・`Layers` の欄 | `…, "decision", "speech", "proximity"`(合わせた結果に 1 行が 2 回出たので 1 行にした)・欄は `speech` → `proximity` |
| `engine/systems/build.py` | 層の箱の引数の行 | `speech=speech_port, proximity=proximity_layer`(合わせた結果に同じ引数の行が 2 回出たので 1 回にした) |
| `engine/systems/run_end.py`・`state_io.py` | 結果へ渡す層・持ち主の表・docstring | `speech` → `proximity` の順に両方 |
| `engine/systems/table.py` | close_final の reads の末尾 | `"layers.speech "` → `"layers.proximity"`(文字列の連結の空白を足した) |
| `perception/renderer.py` | `_TickCache` の欄(1-8b の `heard`・`heard_reported` と 2-2 の `near`) | 1-8b の欄 → `near` |
| `docs/design/bridging-ledger.json` | 末尾の行(本体 303 行と 2-2 の 7 行) | 本体の版に 2-2 の 7 行を末尾に足して同じ書式で書いた(310 行・id は一意・本体の行は 1 文字も変えていない=往復の検査つき) |
| `tests/engine/time/manifest_keys_frozen.json` | 注と鍵の末尾 | 鍵 117 → 118(末尾に `proximity`)・注に 2-2 の 1 文 |
| `tests/engine/test_env_and_sections_10f.py` | 欄の組・`CONFIG_PATHS_SHA256`・末尾の並び | `PX22_KEYS` は `S8B_KEYS` の後・sha256 は 1-8b の `163fb104…71ba4eb8` → `1ec094a4…491503d3`(作業木の道筋から `proximity.*` の 12 本を除くと 1-8b の値と一致=増えたのは 12 本だけ) |
| `tests/engine/test_state_ledger_10b.py` | 行の数・行の鍵の並び・行の軸の検査 | 外の状態 105 → 107・全体 196 → 198・鍵の末尾 … `CT5`・`S8`・`S8M`・`PX`・`PX0`・両方の検査 |
| `tests/engine/bridging/test_bridging_ledger.py` | 見出しの数・項の数・HD 行の数 | 本体の値に 2-2 の分を足した: 見出し 82 → 83・見出しのファイル 79 → 80・項 357 → 362・HD 行 83 → 84(active 82 → 83)・expedients 143・docstring 6 は本体のまま |
| `tests/engine/bridging/test_manifest_rules_bridges.py`・`rights/test_rights_manifest.py`・`time/test_t0_tm9_fields.py`・`perception/facts/test_percept_schema.py` | manifest の末尾の並び | 末尾に `proximity`(1-4 の 3 欄の位置も 1 つずらした) |
| `tests/engine/tools/test_c0_phone_table_empty_and_declared.py`(1-7) | 衝突ではない(試験で落ちた) | 末尾の並び `[-2:] == ["tools", "speech_port"]` → `[-3:] == ["tools", "speech_port", "proximity"]` |

語彙の表は 2-2 では足していない(1-8b の 57 語のまま)。`core/rng.py` の `philox_array` などは 2-2 だけ(衝突なし)。

**再確認**:
- 試験: 指示の範囲(`tests/engine/proximity tests/engine/speech tests/engine/tools tests/engine/systems tests/engine/events tests/engine/decision tests/engine/time tests/engine/bridging tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/engine/test_salt_seed_split_10f.py tests/perception tests/llm`)= **1,524 passed・1 failed**(上の表の最後の 1 本=末尾の並び)→ 直して そのファイル 6 passed。`tests/engine/proximity` の slow 2 passed。`lint-imports` 5 kept。
- byte-check の既定 cell(4 構成): [byte_check_prox22_cell4_rebased.json](byte_check_prox22_cell4_rebased.json)=本体 HEAD `db40de2` の src の写し(錨 3 本だけ・子プロセスに PYTHONPATH)と作業木の src。**4/4 構成で 25 欄とも同じ**(5f7ae9ff/65,597・e0054a83/50,301・24375ee3/51,835・73a78288/69,111)。
- 腕 distance(4 構成): [byte_check_prox22_distance_rebased.json](byte_check_prox22_distance_rebased.json)。rebase の前(§14-4)と final・呼数・起床の内訳・食事が全部同じ(3f1358f0/65,195・fa283a5e/51,472・5f842477/68,171・c61196ce/105,426)=取り込んだ 1-7・1-8b(既定 off)・2-3b(資産は別の置き場)は腕 distance の結果を動かさない。
- 腕 distance の再開 == 通し(世界資産 1,000 体・止める 750): [resume_rebased.json](resume_rebased.json)=final `e0a62eaf…` が同じ・呼数 4,710+7,100=11,810・止めた後の checkpoint 12 本のハッシュが同じ・気づく抽選 141 本([tools/resume_check.py](tools/resume_check.py))。

**当たり(親の判断)**: 1-8b のつなぎの台帳の行 `DOC-s8b-reach-session`(発話の口の届く範囲=会話のセッションの参加者・距離を見ない)の外す段が `2-2` になっている。2-2 の発注には発話の口の届く範囲は入っていないので、この段では触っていない(行は active のまま)。外す段を動かすか、2-2 の続きで届く範囲を近接の判定に替えるかは親の判断。

## §16 親の検収(第334・Fable 5.1・rebase の後)

- 本体 db40de2 へ rebase(衝突 19 ファイルを実装役が手で解いた=本体の分 → 2-2 の分の順)。範囲の試験(proximity・speech・tools・systems・events・decision・time・bridging・再開・状態台帳・10f・salt・perception・llm)1,525 passed(10 分 46 秒)。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・既定 cell)=final 同じ・25 欄とも差なし(parent_head_vs_prox22_rebased_4cfg.json)。腕 distance の 4 構成は実装役の rebase の前後で同じ(byte_check_prox22_distance_rebased.json)=親は既定の不変だけを自分で確かめ、腕の値は実装役と検収役の記録を根拠にする。
- 独立検収(review.md)=条件つき受入(中 3・低 9)→ 全部直した+親の判断(鍵は Philox の配列の口・B5 の単位は店のセルの中・近接行は半径の中・ハブは測れないと宣言・名指しの相手へ寄る口は 5-2)。検収役の全会話の距離の数え直し・索引と総当たり 900 点・描画の digest 11,928 回・再開=通しの一致を受入の根拠にする。
- 親の判断(§15 の問い): 1-8b の台帳の行 DOC-s8b-reach-session(届く範囲=セッションの参加者・外す段 2-2)は**外す段を 5-3 に改める**(発話の届く範囲を「聞こえた範囲」にするのは音の場の段 5-3 と傍受 T3=2-2 の近接は会話の相手の判定)。親が取り込みの文書で台帳を直す。
- 2-4 の候補: 歩き出したときに在席の印 poi_ref を解く(既定の席の数え方が変わる=版上げで)。既定 distance にするのも 2-4 の束。
- 判定: 受入(第 2 期 2-2 の完了)。
