# 10e 版上げ 1 回目(エンジン側): behavior-hash の final・死蔵の列・期限つきの辞書・counter と K19・テープ版 4

> 実行役(Opus 5.5)の記録。親の検収の前。commit していない(親が snap_E1 → E2 → E4 → E5 の順に重ねて commit する)。**この版は E5 までの記録**(各スナップショットに累積で入れる=検収 D4)。
> 発注: 第329(親 Fable 5.1)。ユーザーの確認: [回答 6-4](../../../../design/v2-plan-answers-2026-10-12.md)。正典: [実装の計画](../../../../design/v2-implementation-plan-2026-10-12.md) §2 第 0 期・[D-102 のアジェンダ](../../../../design/v2-d102-foundation-implementation-agenda.md) §5・§6・[指示書 10-03](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §3(A6・A8)・[指示書 10-06](../../../../design/v2-wallbounce-decisions-2026-10-06.md) §6(K1・K7・K8・K15・K19)・[10f のアジェンダ](../../../../design/v2-d102-10f-agenda.md) §6-2。
> **範囲**: E1・E2・E4・E5・E6。**E3(暦の既定の一本化と既定の開始日)は親の指示の変更でやらない**(W13 の年間化と開始日の決定が先に要る=B6 に回す)。`--calendar-weekday` の既定は `day_index` のまま。構築側(W10 ON・W12・山手線・騒音の指紋・W13 の年間化)は別の発注。
> **検収を受けた直し**([review-10e-engine.md](review-10e-engine.md)=条件つき受入)を入れた版。直した番号: R1(とその続き 2 件)・T1〜T4・L1〜L3・Q2・D1〜D6。**K15(Q1)は止めた**(§E1-6)→ 親の決定で `--hash-scheme full` を消す commit に送った。
> 測った機械: Windows 11・x86-64・論理 CPU 20(10f と同じ)。パスは `src/shibuya/` を省く。絶対パスは書かない。スナップショットの基準は HEAD `18ff37f`(その後の親の commit は STATUS と devlog だけ)。byte-check の基準の写しは `66472a0`(`18ff37f` と src・tests は同じ)。

## 0. 結論

1. **E1**: 既定の final を behavior-hash に切り替え(`--hash-scheme {behavior,full}`・既定 behavior)、死蔵の 5 列を SoA と状態台帳から消した。19 構成で**呼数・行動の件数・blocks・テープの 14 列は不変**。`--hash-scheme full` は 19/19 で HEAD の final を再現する。
   - **検収 R1 を直した**: 艦隊で録ったランとその再生で既定の final が食い違っていた。再生の到着待ち(`run_day.replay_inbox`)を O44 から O96(軸 1 no・軸 2 required)に分け、適用待ちの応答(O43 `run_day.pending`)と艦隊の繰り延べ(O44 `run_day.fleet_deferred`)の list は並びを状態から外した(多重集合でハッシュ)。台帳は **189 行**。録画=再生を既定の final で見る試験(T2)が通る。
   - そのため E1 の final は「10f の `byte_check.json` の behavior-hash」とは一致しなくなった。代わりに **HEAD の写しで O96 を外し O43・O44 を多重集合にして計算した behavior-hash と 19/19 一致**する(§E1-3)。
2. **E2**: 会話の管理の期限つきの辞書 3 つの掃除(tick ごと)・旧 pickle の口の削除・保存の予算の再宣言(読み口の上限 2 GiB → 8 GiB=**expedient**)・O64 は no のまま・V3・T7 の門を「シミュ全体の壁時計に占める割合 ≤ 1%」に。**呼数・行動の件数・テープは不変**。O39(会話の管理)は軸 1 behavior の行なので、掃除で final が会話の起きる 18 構成で動く(発注書の「final 不変」の予想は成り立たない)。
3. **E4**: 既定の乱数を counter に。K19 の 8 用途名は counter では鍵の 0 語目を空けた(`core.rng.k19_counters`)=隣の鍵・次の日の流れと重ならない(U2 を直した)。`--rng-scheme stateful` は 19 構成で E2 の全欄を再現する。
   - **既定のランの住人が入れ替わる**: W16 の層の並べ替え(`w16.sample.stratum`)の鍵が変わるので、5,000 体の標本のうち **4,191 体が別の人**になる(残る 809 体のうち 769 体は定員先取り層)。1,500 体では 729 体、300 体では 0 体(定員先取り層だけで埋まる)。体重と EER の抽選も変わる。**A6 の文言「動くのは顕著行為と出動の件数だけ」は成り立たない**。動いた量は 3 段に分けた(§E4-3)。
   - 検収の L1〜L3 を直した: テープの meta に鍵の配置の印 `rng_layout: "10e"`(10c〜10f の counter のテープは再生で止める)・母集団の抽出の既定を揃えた・CLI の checkpoints の JSON を版 2 に。
4. **E5**: テープ版 4(`shibuya.tape/4`)。版 3 の 14 列の後ろに 7 列。19 構成で final・呼数・行動・版 3 までの 14 列の中身は不変。テープは 1 呼あたり約 21〜50 B 増える。艦隊の経路の行(T1)と、引いた記憶の同定を記憶の表と突き合わせる試験(T3)を足した。
5. **全体テスト**: §E6-5。
6. **親に確かめてほしい点**: §E6-4。

## 1. 手順(byte-check)

```
git archive 66472a0 src docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
mkdir -p $W/head_src/data/calendar && cp data/calendar/syukujitsu.csv $W/head_src/data/calendar/
D=docs/bench/analysis/wallbounce-1012/10e
python $D/byte_check_10e.py side --src $W/head_src/src --label head --scratch $W --out $W/head.json
python $D/byte_check_10e.py side --src $W/head_src/src --label head_minus --drop-behavior-item run_day.replay_inbox \
    --multiset-items run_day.pending,run_day.fleet_deferred --scratch $W --out $W/head_minus.json   # 検収 R1 の照合
python $D/byte_check_10e.py side --src <段の木の src> --label e1 --scratch $W --out $W/e1.json
python $D/byte_check_10e.py side --src <段の木の src> --label e1_old --kw '{"hash_scheme": "full"}' --scratch $W --out $W/e1_full.json
python $D/byte_check_10e.py compare --a $W/head.json --b $W/e1.json --out $D/e1_vs_head.json
```

- `byte_check_10e.py`(新): 10c の `one`・`side` に、行動の件数(`action_usage`)・起床の内訳・最後の checkpoint の behavior-hash と full-hash(全桁)・締めの後の 2 本・checkpoint の時間・暦の欄・テープの列の名前と大きさを足した。`--kw` で旧値の再現の切替口を渡す。`--drop-behavior-item`・`--multiset-items` は HEAD の写しで behavior-hash の定義を E1 に合わせる口(検収 R1 の照合だけ)。`compare` は欄ごとに「同じ/動いた」と前後の値を書く。19 構成・mock/classical 5,000 体・seed 1・1 シミュ日・テープつき(10f と同じ)。
- 各段の値は、HEAD に各段のスナップショットを重ねた木で回した(段ごとに直しを入れた後の値)。置き場: `sides/`(head・head_minus・e1・e1_full・e2・e2_counter・e4・e4_stateful・e5)と各段の比べの JSON。

## E1 既定の final を behavior-hash に・死蔵の 5 列を消す(Q1・Q9・A4)

### E1-1 変えたこと

| ファイル | 何を |
|---|---|
| `core/soa.py` | `Registry.retire(after, field, dtype, fill)`(消した列を「元の位置にあった列」として控える・配列は確保しない)と `retired_columns_in_hash()`(この中の `state_hash` だけが控えた列を初期値の配列として元の位置に混ぜる)。既定は off=消した列はどこにも出ない |
| `agents/state.py` | 死蔵の 3 列(`plan_cursor` i2・`invocation_distance` u2・`wake_pending_class` i1=Q9)の宣言と初期値 −1 の行を消し、`retire` で元の位置に控えた。宣言は 5 B/体 減る |
| `perception/state.py` | 死蔵の `last_b2_hash`・`last_b4_hash`(u8 ×2=16 B/体・A4)を消した。知覚 SoA の既定は 2 B/体 |
| `engine/state_ledger.py` | 死蔵の 5 行を消した・O44 から `run_day.replay_inbox` を O96(軸 1 no・軸 2 required)に分けた・O43 と O44 の list に `multiset` の印(R1)。**189 行**(SoA 93=agents 76・cells 5・pois 9・知覚 3/外の状態 96)。版 `state-ledger/10e` |
| `engine/state_hashes.py` | `HASH_SCHEMES = ("behavior", "full")`・既定 `behavior`・`check_hash_scheme`。`multiset` の印のある list は要素の直列化の昇順でハッシュ(R1) |
| `engine/run.py` | `Checkpoint.hash_scheme`・`legacy_combined`(10e より前の組み立て)・`combined`=既定は `behavior_hash`(空なら止める)/`full` は `legacy_combined`。`run_day(hash_scheme=…)`・`RunResult.hash_scheme`・manifest の末尾に `hash_scheme`(設定の節)・CLI `--hash-scheme` |
| `engine/resume.py`・`engine/manifest_sections.py` | `hash_scheme` を再開の指紋に入れない(挙動に効かない)・設定の節に |

- **旧値の再現の仕組み**: 旧い final は SoA の全列を宣言順に並べたハッシュ。消した 3 列は書き手が無く初期値のまま(src の書き込みは初期値 −1 の 1 行だけ・10b の AST)だったので、`full` のハッシュの中で同じ位置に同じ初期値の配列を並べ直せば、消す前と同じバイト列になる。試験で「消す前の宣言を組み直した Registry」と同じハッシュ(除外つきも)になることを確かめた。
- `AgentState.state_hash` を差し替えて腕の欄を除く既存の試験(9 か所)は旧い組み立てでだけ効くので、`hash_scheme="full"` を渡した(§E6-1)。

### E1-2 検収 R1 と直し(D1 の経緯を残す)

- **欠陥**(検収役が偽 vLLM 2 台・合成世界 120 体で見つけた): 既定の final(behavior-hash)が、艦隊で録ったランとその再生で一致しない。初版の記録は「ランの終わりに待ちが残るとき(タイムアウトのランなど)は final も違う」と書いていたが、範囲が狭すぎた。正しくは「**途中の checkpoint は在途の呼があれば必ず違い、最後の tick に在途の呼があれば final も違う**」(検収 D1)。初版では、録画と再生を比べる試験 4 本と台帳の有無を比べる試験 2 本の比べ方を `legacy_combined` に替えて通していた。
- **原因**: behavior-hash に、録画と再生で表し方の違う 3 つの値が入っていた。(1) 再生の到着待ち `run_day.replay_inbox`(録画の側では同じ応答は艦隊の中=O65 にある)(2) 艦隊の繰り延べ `run_day.fleet_deferred` の list の並び(録画は艦隊が返した順・再生はテープの行の順)(3) 適用待ちの応答 `run_day.pending` の list の並び(応答の遅れ 2 の経路で残る)。(2)(3) は検収の設定(キュー満杯で繰り延べ 0)では出ず、直しの後に既存の試験(繰り延べのあるキュー満杯・応答の遅れ 2)で見つけた。
- **直し**: (1) は O44 から O96 に分け、軸 1 no・軸 2 required にした(応答がいつ届くかはテープから来る外の入力で世界の挙動ではない・再開には要る)。(2)(3) は台帳の行に `multiset` の印を足し、ハッシュを要素の多重集合で取る(並びに依らない)。適用は `(t_apply, 級, 撹拌鍵, 体)` の lexsort・再投入は配列にして候補へ混ぜるだけで、どちらも並びに依らない(録画と再生で呼数と legacy の final が一致していた)。保存と再開は並びのまま。
- **結果**: 録画と再生を比べる 4 本は既定の `combined` の比べ方に戻した(HEAD の版のまま)。T2 の試験 `test_t2_fleet_record_equals_replay_on_the_default_final`(検収役の設定=キュー満杯 40 tick・タイムアウト 12 tick)を足した。陽性対照として O96 を behavior-hash に戻すと食い違うことも見る。台帳の有無を比べる `test_ledger_wiring` の 2 本は `legacy_combined` のまま(behavior-hash には金と物の台帳の行が入り、台帳の有無で違うのは定義どおり=R1 とは別の理由)。

### E1-3 動いてはいけない量(19 構成・HEAD `66472a0` の写しと)

| 量 | 結果 |
|---|---|
| 呼数・行動の件数・起床の内訳・blocks の行と中身・テープの 14 列の名前と中身・顕著行為と出動・気づいた延べ・食事 | **19/19 不変** |
| full-hash | 動いた(O44 を分けて外の状態の項の並びが変わったため・中身は同じ)。締めの後の full-hash も同じ理由で動く |
| `--hash-scheme full` の final(と全欄) | **19/19 が HEAD と同じ**([e1_full_vs_head.json](e1_full_vs_head.json)) |
| 既定の final | 19/19 動いた(定義の変更)。**HEAD の写しで behavior-hash の定義を E1 に合わせた値(O96 を外し・O43 と O44 を多重集合)と 19/19 一致**(下の表・[e1_vs_head_minus.json](e1_vs_head_minus.json)=final・呼数・テープ・行動の全欄が同じ)。検収の前の版の「10f の `byte_check.json` の behavior-hash と 19/19 一致」の照合は、定義が変わったので失われた |

| 構成 | HEAD の behavior-hash | HEAD の写しで O96 を外し O43・O44 を多重集合にした値 | E1 の final |
|---|---|---|---|
| w6_v3_default | `1f4d96b1d8dfa701` | `3264c9fc190b3eb9` | `3264c9fc190b3eb9` |
| w6_v3_activity_off | `9a88751e6c7151c8` | `eb83e5b0c6c285e4` | `eb83e5b0c6c285e4` |
| w6_v1_default | `1281a1b032e67f57` | `aa721b19707f25e4` | `aa721b19707f25e4` |
| w6_v1_derive_v2_1 | `ccf1c15625349493` | `37557aa76c8d9f29` | `37557aa76c8d9f29` |
| w6_v2 | `dbcf5abb17394ffc` | `52899ac1ad9657a6` | `52899ac1ad9657a6` |
| w6_v1_edge | `a7f8c7e10f40ece2` | `7d06c9e0c3e7d3bb` | `7d06c9e0c3e7d3bb` |
| w6_v2_edge | `3d88d8852b5aec40` | `87035b6d3eef8aad` | `87035b6d3eef8aad` |
| w6_v1_edge_plateau | `d2f2f7e00454b99f` | `b3b181cbc50d6b1b` | `b3b181cbc50d6b1b` |
| w6_old_v1_default | `f9a301c75e4d7efe` | `d10606e9f87af856` | `d10606e9f87af856` |
| w6_old_v1_derive_v2_1 | `00284e20eb8d5c2a` | `48e493b4c6d16adb` | `48e493b4c6d16adb` |
| w6_old_v2 | `28fb189675e2e571` | `2ffe172806a6291b` | `2ffe172806a6291b` |
| w6_old_v1_edge | `fe05d60d2fbea1a3` | `bd96d0c4a29d606f` | `bd96d0c4a29d606f` |
| w6_old_v2_edge | `24c03c11e246e929` | `610e8c13468fea39` | `610e8c13468fea39` |
| w6_old_v1_edge_plateau | `08e7c3c499aa7c63` | `43856c5b613ddfbd` | `43856c5b613ddfbd` |
| w6_golden_null_arm | `ed827fd4e312264d` | `db765499cec1fef5` | `db765499cec1fef5` |
| v3_mem_store | `23e7abd0d7734b74` | `899dd4222a8cda75` | `899dd4222a8cda75` |
| v3_mem_rel | `b2e49d9cc5c2ccce` | `e27e45f3e9b62749` | `e27e45f3e9b62749` |
| v3_classical | `e8ab16915d89415c` | `4a67879d2d9f8d49` | `4a67879d2d9f8d49` |
| v3_classical_mem_rel | `127a82cd158cd829` | `ae86702196975458` | `ae86702196975458` |

### E1-4 動いた量

final だけ(全 19 構成の前後は §E6-2)。5,000 体以外の golden: classical 1,500 体(既定 acquaintance)`4f78f3c0…` → `d8eee505…`(呼数 25,808 は同じ)。合成世界 100 体の 5 構成は試験 `PRE10E_SYN`(HEAD の写しの final と、E1 の定義の behavior-hash)と `CUR_SYN`(今の既定の final)に固定した。

### E1-5 試験

- 張り替え: `W17_GOLDEN`(帰無・v3 の既定=behavior-hash・旧値は `*_pre10e`)・`REL_ON_5000_GOLDEN`(鍵を (寿命のハッシュの版, final の定義) に)・`CLASSICAL_1500_GOLDEN_ACQ`(旧値は `_PRE10E`)・T7 の final・K19 の slow の final・10f の golden の表の試験・manifest の末尾の欄と設定の道筋の sha256。
- 段ごとの旧値の再現の試験(段 2c・3 段目・5 段目・Q13・近接の同点の旧値・10a の +2・関係の v1)は `hash_scheme="full"` で比べる(10e より前の定義で録った値)。
- 新しい試験: `test_hash_scheme_full_reproduces_the_pre_10e_checkpoints`・`test_checkpoint_combined_follows_the_hash_scheme`・`test_e1_retired_columns_reproduce_the_old_registry_hash`・`test_e1_dead_columns_are_gone_from_the_soa`・`test_e1_r1_replay_inbox_is_out_of_the_behavior_hash`・`test_e1_r1_fleet_deferred_is_hashed_as_a_multiset`・`test_t2_fleet_record_equals_replay_on_the_default_final`(2 件)・`test_t1_deleting_the_dead_columns_changes_nothing`(5 構成)。
- **検収 T4 の直し**: `test_t1_deleting_…` は (1) 既定の final=`CUR_SYN` (2) `hash_scheme="full"` に替えても挙動(呼数・行動・prompt・behavior-hash)が同じ (3) `full`+`stateful` が HEAD の final を再現 (4) **10e で挙動を動かした 2 つ(E2 の会話の控えの掃除・E4 の乱数の既定)を止めたラン**(`purge_expired` を何もしない・`rng_scheme="stateful"`)の behavior-hash が `PRE10E_SYN` の `beh_old` と同じ、を見る形にした。どの段でも `beh_old` と `_observed` の比べが実行される。

### E1-6 K15(検収 Q1)は止めた

- 親の指示は「`fail_streak`・`plan_activity` を E1 で消し、`retire` を 2 行足して `--hash-scheme full` の再現を保つ」。しかし 2 列とも**ランの途中で書かれる**(`fail_streak` は resolve の 6 か所で失敗の連続を数え・0 に戻す/`plan_activity` は計画実行層が日の頭とイベントで書く)。`retire` は初期値の配列を並べ直すだけなので、消すと `full` の final は 10e より前の値を再現できない(死蔵の 5 列は書き手が無かったので再現できた)。
- 案: (a) E1 で消し、`full` の旧値の再現をあきらめる(`*_pre10e`・段ごとの旧値の試験を全部張り替え=旧値の再現の試験が消える)/ (b) **版上げの最後(`--hash-scheme full` を消す commit)で消す**(親推奨の材料: 旧値の再現を保てる・消すときの final は behavior-hash なので動かない=軸 1 no)/ (c) 2 列の書き手を残したまま値を保つ(列を消したことにならない)。実行役は (b) を推した。
- **親の決定(第329)**: (b)。K15 の 2 列の削除は `--hash-scheme full` を消す commit に送る(その時点で final は behavior-hash で、2 列は軸 1 no なので何も動かない)。台帳の注(検収 D2)は「10-06 K15 で削除と決定。`--hash-scheme full` を消す commit で消す(動く量なし)」に直した(行数と軸は変えていない)。

## E2 期限つきの辞書の掃除・旧 pickle の口・保存の予算・O64・V3・T7 の門

### E2-1 変えたこと

| ファイル | 何を |
|---|---|
| `engine/conversation.py` | `purge_expired(tick)`: `_refusal_until`・`_pair_invite_until`・`_speaker_invite_until` から期限 ≤ tick の項を落とす(読みはどれも「tick < 期限なら抑止」=期限切れは「無い」と同じ)。計数 `n_expired_purged`(O41・diag) |
| `engine/run.py` | 会話の段の終わり(`purge_terminal` の後)で tick ごとに `purge_expired`。掃除の時刻は T だけで決まる。旧 pickle の切替口(`resume_legacy_pickle`・`--resume-legacy-pickle`)を消した |
| `engine/resume.py` | 旧 pickle の読み口(`_read_state_pickle`・`write_state_pickle`・`LegacyStateFormatWarning`・`STATE_FORMAT_PICKLE`・`STATE_NAME_PICKLE`・`import pickle`)を消した。中身が pickle なら名前に関係なく開かずに止める |
| `engine/state_codec.py` | `MAX_UNCOMPRESSED_BYTES` 2 GiB → 8 GiB(§E2-4・**expedient**) |
| `engine/state_ledger.py` | O39 の注(掃除)・O41 に `conv.n_expired_purged`・O64 の注(no のままの理由) |
| `engine/state_ledger_ast.py` | V3: `ExtAllow.funcs`(当たる行の関数の名前の並び)。数に加えて関数の名前で落とす |
| 文書 | D-102 のアジェンダ §7 に〔改訂(第329)〕(保存の予算の再宣言)・10f のアジェンダ §6-2 に〔改訂(第329)〕(T7 の門の形と実測) |

### E2-2 動いてはいけない量(19 構成・E1 と比べた・[e2_vs_e1.json](e2_vs_e1.json))

- 呼数・行動の件数・起床の内訳・blocks・テープの 14 列・顕著行為と出動・気づいた延べ・食事: **19/19 不変**。
- 合成世界 300 体・2 日で、掃除を止めた(`purge_expired` を何もしない)ランと、呼数・行動の件数・起床の内訳・各呼の prompt_hash が同じ(試験)。

### E2-3 動いた量

final(=behavior-hash)・full-hash・締めの後の 2 本が、会話の起きる **18 構成で動いた**(v3_classical だけ不変=会話の控えに掃除の対象が無い)。O39 は軸 1 behavior の行(会話の管理は挙動に効く)なので、辞書の中身が変われば behavior-hash も変わる。挙動(呼数・行動・prompt)は変わっていない。

| 構成 | O39 の直列化 E1 → E2 [B] | final E1 → E2 |
|---|---|---|
| w6_v3_default | 159,138 → 2,490 | `3264c9fc190b3eb9` → `4985ff2fb3c771c4` |
| w6_v3_activity_off | 111,834 → 1,178 | `eb83e5b0c6c285e4` → `dbccca304e5b5484` |
| w6_v1_default | 124,586 → 1,234 | `aa721b19707f25e4` → `cd6e1283bb5931fd` |
| w6_v1_derive_v2_1 | 102,906 → 1,282 | `37557aa76c8d9f29` → `9ca7cb0fd1b149a2` |
| w6_v2 | 113,562 → 1,442 | `52899ac1ad9657a6` → `0eb03d0870ad0983` |
| w6_v1_edge | 110,058 → 890 | `7d06c9e0c3e7d3bb` → `ad7c60995dac93a5` |
| w6_v2_edge | 81,561 → 937 | `87035b6d3eef8aad` → `45e4636595c75d4b` |
| w6_v1_edge_plateau | 107,378 → 882 | `b3b181cbc50d6b1b` → `96b18f5301cf8483` |
| w6_old_v1_default | 124,586 → 1,234 | `d10606e9f87af856` → `58af81db49bedbaf` |
| w6_old_v1_derive_v2_1 | 102,906 → 1,282 | `48e493b4c6d16adb` → `5a1649b91e97eedb` |
| w6_old_v2 | 113,562 → 1,442 | `2ffe172806a6291b` → `c2d7ab766cafcee9` |
| w6_old_v1_edge | 110,058 → 890 | `bd96d0c4a29d606f` → `d77cafef2e580fa5` |
| w6_old_v2_edge | 81,561 → 937 | `610e8c13468fea39` → `6f71c723a474e837` |
| w6_old_v1_edge_plateau | 107,378 → 882 | `43856c5b613ddfbd` → `b716d5aaee17e4b2` |
| w6_golden_null_arm | 181,576 → 5,384 | `db765499cec1fef5` → `065a36d238aae477` |
| v3_mem_store | 159,138 → 2,490 | `899dd4222a8cda75` → `0ae357f5d7f8b280` |
| v3_mem_rel | 168,978 → 2,210 | `e27e45f3e9b62749` → `fe19250259a7058d` |
| v3_classical | 64 → 64 | `4a67879d2d9f8d49` → `4a67879d2d9f8d49` |
| v3_classical_mem_rel | 9,898 → 66 | `ae86702196975458` → `8b85c6b5f82babba` |

辞書の大きさ(合成世界 300 体・2 日・seed 3・checkpoint と日の締めの後): 掃除あり 0〜14 項、止めたランは 3 → 464 項(日数に比例して増える)。

### E2-4 保存の予算の再宣言([budget_10e.json](budget_10e.json)・`budget_10e.py`)

**注(検収 D5)**: この表は E2 の時点の作業木(乱数 stateful=E4 の前の母集団・検収の直しの前)で測った。E4 で 5,000 体の標本が入れ替わるので値は少し動く見込み(測り直していない)。mock 5,000 体・seed 1・2 日のランを日の境目 T=1440 で止めた状態のファイル(npz+json)。39 万体(W16 の 390,067 人)は線形の外挿(**推測**)。

| 構成 | ファイル(圧縮) | 39 万体 | 展開した後 | 39 万体 | 書き/読み(中央値 3 回) |
|---|---|---|---|---|---|
| 既定 v3 | 618,989 B=124 B/体 | 約 48 MB | 815 B/体 | 約 318 MB | 0.108 / 0.039 s |
| 記憶+関係 | 1,298,157 B=260 B/体 | 約 101 MB | 4,333 B/体 | 約 1.69 GB | 0.257 / 0.069 s |
| 全腕(記憶・関係・店の記憶・親しみ) | 2,080,935 B=416 B/体 | 約 162 MB | 6,179 B/体 | 約 2.41 GB | 0.437 / 0.083 s |

- 10d の pickle は 861 B/体(39 万体で約 336 MB)、10f の npz+json(既定 v3)は 768,757 B。E2 で 618,989 B に下がったのは主に会話の管理の掃除。
- **見つけた欠陥**: 全腕の 39 万体の展開した後の大きさ(約 2.41 GB)が、読み口の上限 `MAX_UNCOMPRESSED_BYTES`(10f の 2 GiB=2.15 GB)を超えていた。全腕の外挿の約 3.6 倍の **8 GiB** に上げた(**expedient**・検収 L4)。検収の案「見出しの体数 × 体あたりの上限」の方が筋は良い(外から来たファイルへの防御なので体数に比例させる)。決めるのは親。meta(JSON)の部品は全腕でも 39 万体で約 11 MB(上限 512 MiB のまま)。

### E2-5 O64(`renderer.signage_exposures`)

親案のとおり軸 1 **no のまま**(軸 2 discardable)。理由を O64 の行の注に書いた(tick の中だけの口で、checkpoint と日の境目の保存の時点では常に空)。試験 `test_e2_o64_signage_exposures_are_empty_at_every_checkpoint`。

### E2-6 V3

`ExtAllow` に `funcs`(当たる行がある関数の名前の並び)を足し、数が同じでも関数の名前が違えば落とす。今の 17 項の関数は `run_day` 15 項(うち 1 項は 2 か所)・`TargetResolver.resolve` 1 項・`SimClock.to_tick_offset` 1 項。**残る限界**: 同じ関数の中で移したものは見えない(15 項が `run_day` の中)。

### E2-7 T7 の門(10f のアジェンダ §6-2)

- 門=checkpoint の壁時計の合計がシミュ全体の壁時計に占める割合 ≤ **1%**(`T7_SHARE_CAP`・**未リサーチ(expedient)**)。宣言値(5,000 体で 1 回 ≤ 100 ms)は**目標**として残し、超えたら警告だけ出す。宣言の 3 倍の門は消した。
- 3 倍にした経緯(第321・`tests/engine/test_state_ledger_10b.py` の注釈から写した): 「宣言の上限は 100 ms(10b のアジェンダ §3 K-T7)。全体テストの大きな束の中では壁時計が揺れる(第321 で all_arms が 1 回だけ超え、単独では通った)ので、ここでは宣言の 3 倍を門にし、宣言値そのものは毎晩の性能テスト(指示書 10-03 §6 6-5)で見る」。指示書 10-06 §6 の「つなぎ」で期限を付けることになり、10e で割合の形に替えた。
- 実測(T7 の試験・5,000 体・1 シミュ日・E2 の時点): 既定 v3 は checkpoint の合計 **35.1 ms/日**・シム日の壁時計 32.8 s・割合 0.11%・最大 10.6 ms、全腕は 167.0 ms/日・55.0 s・0.30%・最大 46.6 ms。10b の 85.8 ms/日は 10b-1 の既定 v3 の値。

## E3 暦の既定の一本化(やらない)

親の指示の変更(第329)で本発注からは外した。`--calendar-weekday` の既定は `day_index` のまま。B6 のための注は §E6-1 の最後。

## E4 既定の乱数を counter に・K19・U2・U8

### E4-1 変えたこと

| ファイル | 何を |
|---|---|
| `core/rng.py` | `DEFAULT_RNG_SCHEME = "counter"`・`k19_counters(rng_scheme, *words)`(counter は `(0, *words)`=0 語目を空ける / stateful は旧の並び) |
| `agents/population.py` | `sample_population(..., rng_scheme=)`・`load_population(..., rng_scheme=)`(検収 L2) |
| `engine/energy.py`・`engine/resolve.py` | 体重と EER の抽選 |
| `perception/p_notice.py`・`engine/processes/salient.py` | 気づきの引き(事象の番号) |
| `engine/processes/goods_flow.py`・`logistics.py`・`runner.py` | 日の鍵の流れ(配送・工事=U2) |
| `engine/run.py` | `resolve_rng_scheme`(`None`=未指定は録画・mock で counter・再生ではテープの値)・母集団の抽出とエネルギーの初期化に方式・CLI の既定 None・テープの meta に `rng_layout: "10e"`(検収 L1) |
| `cli.py` | 世帯の財布の抽出も同じ方式・checkpoints の JSON を版 2 に(検収 L3) |
| `engine/rng_audit.py` | 許可の表の扱いを `stateful`(旧値の再現のランでだけ重なりを許す)と `latent` に・`overlap` を消した・束ねる鍵に master seed(U8)・同じ鍵の作り直しは `K19_RECREATED` の用途名だけ |
| `tools/c7/attr_arms.py`・`docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py` | 検収 L2: 抽出の鍵の並べ方を engine と揃える(`population_for(..., rng_scheme=)`)・3 引数の差し替えが engine から呼べる(TypeError を無くした) |

### E4-2 動いてはいけない量

- `--rng-scheme stateful` の 19 構成: E2 の**全欄と 19/19 同じ**([e4_stateful_vs_e2.json](e4_stateful_vs_e2.json))。
- K19: 既定(counter)では実際の重なり 0(合成世界 率 ×1000・2 日/世界資産 300 体・2 日/既定 v3 5,000 体・1 日)。

### E4-3 動いた量(検収 Q2: 3 段に分けた)

K19 は指示書 10-06 で「版上げ 1 回目に束ねて直す」と決まった 1 つの束なので commit は分けない。代わりに、動いた量を 3 段で切り分ける: **(a) E2 の既定(stateful)→ (b) counter・10c の鍵の配置**(E2 の木で `--rng-scheme counter`=顕著行為と出動の乱数だけを替える)**→ (c) counter・10e の鍵の配置**(E4=K19 の並べ方で母集団の抽出・体の定数・気づき・日の鍵も替わる)。比べの JSON: [e2_counter_vs_e2.json](e2_counter_vs_e2.json)・[e4_vs_e2_counter.json](e4_vs_e2_counter.json)・[e4_vs_e2.json](e4_vs_e2.json)。

| 構成 | (a) E2 の既定(stateful)final / 呼数 | (b) counter・10c の鍵の配置 final / 呼数 | (c) counter・10e の配置(E4)final / 呼数 | 顕著行為 a / b / c | 出動 a / b / c | 気づいた延べ a / b / c |
|---|---|---|---|---|---|---|
| w6_v3_default | `4985ff2fb3c771c4` / 69,978 | `7c19b750af92125e` / 69,796 | `4fbf61616af1e3d2` / 70,421 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 352 / 383 |
| w6_v3_activity_off | `dbccca304e5b5484` / 58,570 | `49aa348aa260e3a4` / 59,231 | `6ef311ea2bcabbaa` / 58,495 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 290 / 487 |
| w6_v1_default | `cd6e1283bb5931fd` / 60,970 | `35bdaadb1d919ffd` / 61,931 | `9180ff01f380448a` / 60,899 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 609 / 791 |
| w6_v1_derive_v2_1 | `9ca7cb0fd1b149a2` / 54,285 | `87e4f4f4a8e5bf86` / 54,786 | `d69cc0795cb27294` / 54,491 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 634 / 527 |
| w6_v2 | `0eb03d0870ad0983` / 60,901 | `264861a9ad54ab4b` / 61,135 | `88dc42eabbc8623e` / 60,758 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 536 / 294 |
| w6_v1_edge | `ad7c60995dac93a5` / 54,150 | `ccf5f94c9e26e7ef` / 54,121 | `abd6801c4e3ce142` / 54,313 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 789 / 565 |
| w6_v2_edge | `45e4636595c75d4b` / 54,170 | `aa33bcc874d0e100` / 53,985 | `00c7b8d57be27d15` / 54,326 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 786 / 273 |
| w6_v1_edge_plateau | `96b18f5301cf8483` / 55,173 | `1af9ed3decf5aedc` / 55,304 | `a289e41bf7383db0` / 55,505 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 471 / 326 |
| w6_old_v1_default | `58af81db49bedbaf` / 60,970 | `3d16cb29276fed0f` / 61,931 | `fb7b4b4755eb90c1` / 60,899 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 609 / 791 |
| w6_old_v1_derive_v2_1 | `5a1649b91e97eedb` / 54,285 | `15e9388d8158c020` / 54,786 | `ef68f751065530ad` / 54,491 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 634 / 527 |
| w6_old_v2 | `c2d7ab766cafcee9` / 60,901 | `f951ebac76b73a81` / 61,135 | `4eacbf3c1a141d89` / 60,758 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 536 / 294 |
| w6_old_v1_edge | `d77cafef2e580fa5` / 54,150 | `7114e97004a301a2` / 54,121 | `2722cf8449b984bf` / 54,313 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 789 / 565 |
| w6_old_v2_edge | `6f71c723a474e837` / 54,170 | `777e17e89e6fe8d1` / 53,985 | `14aff5b3c963e363` / 54,326 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 786 / 273 |
| w6_old_v1_edge_plateau | `b716d5aaee17e4b2` / 55,173 | `8f1108b79d2369af` / 55,304 | `79149e728b5e85a2` / 55,505 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 471 / 326 |
| w6_golden_null_arm | `065a36d238aae477` / 100,439 | `882609f5177f1b11` / 100,947 | `6c81c5ad8a99437a` / 101,969 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 1151 / 2439 |
| v3_mem_store | `0ae357f5d7f8b280` / 69,978 | `e3811d0aa40f8f0c` / 69,796 | `785b26683ed45a35` / 70,421 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 352 / 383 |
| v3_mem_rel | `fe19250259a7058d` / 72,930 | `0692286de6b8cde0` / 73,468 | `64f48b6571ec2ea1` / 74,616 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 472 / 642 |
| v3_classical | `4a67879d2d9f8d49` / 97,563 | `81370e667c6857d1` / 97,903 | `1470f952565a5d31` / 96,961 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 432 / 103 |
| v3_classical_mem_rel | `8b85c6b5f82babba` / 110,395 | `9bfde9db9d668f5d` / 111,839 | `e9a4fa4d2403acbb` / 111,194 | 0 / 10 / 10 | 0 / 5 / 5 | 0 / 523 / 98 |

- **(a)→(b)**: 顕著行為 0 → 10・出動 0 → 5 が出て、気づいた体が起きるので呼数・final が動く(10c §4 のとおり)。母集団は同じ。
- **(b)→(c)**: **W16 の標本(5,000 体の住人)が入れ替わる**。`sample_population(全体, 5000, seed 1)` の stateful と counter で、**4,191 体の id が違う**(共通 809 体=定員先取り層 769 体+統計層 40 体)。1,500 体は 729 体、300 体は 0 体(定員先取り層 769 体の中から取るので層の並べ替えを使わない)。体重と EER の抽選・p_notice の引き・配送と工事の日の鍵も替わる。W17 の 5,000 体の標本の在圏ブロックの数えは 8,589 → 8,542 本。
- E2 → E4 の差(呼数・行動の件数など)の表:

| 構成 | 呼数 E2 → E4(差) | 行動の件数の差 | blocks の行の差 | 顕著行為 | 出動 | 気づいた延べ | 平均の遅れ[分] | 食事の差 |
|---|---|---|---|---|---|---|---|---|
| w6_v3_default | 69,978 → 70,421(+443) | -2,021 | +79 | 0 → 10 | 0 → 5 | 0 → 383 | 7.6 | +168 |
| w6_v3_activity_off | 58,570 → 58,495(-75) | +3,641 | -1 | 0 → 10 | 0 → 5 | 0 → 487 | 10.2 | -96 |
| w6_v1_default | 60,970 → 60,899(-71) | +1,010 | +7 | 0 → 10 | 0 → 5 | 0 → 791 | 8.8 | +0 |
| w6_v1_derive_v2_1 | 54,285 → 54,491(+206) | +155 | -2 | 0 → 10 | 0 → 5 | 0 → 527 | 6.4 | +0 |
| w6_v2 | 60,901 → 60,758(-143) | -2,556 | +20 | 0 → 10 | 0 → 5 | 0 → 294 | 9.8 | +5 |
| w6_v1_edge | 54,150 → 54,313(+163) | -100 | -4 | 0 → 10 | 0 → 5 | 0 → 565 | 7.0 | +0 |
| w6_v2_edge | 54,170 → 54,326(+156) | +432 | +13 | 0 → 10 | 0 → 5 | 0 → 273 | 8.2 | -59 |
| w6_v1_edge_plateau | 55,173 → 55,505(+332) | +720 | -8 | 0 → 10 | 0 → 5 | 0 → 326 | 6.2 | +0 |
| w6_old_v1_default | 60,970 → 60,899(-71) | +1,010 | +7 | 0 → 10 | 0 → 5 | 0 → 791 | 8.8 | +0 |
| w6_old_v1_derive_v2_1 | 54,285 → 54,491(+206) | +155 | -2 | 0 → 10 | 0 → 5 | 0 → 527 | 6.4 | +0 |
| w6_old_v2 | 60,901 → 60,758(-143) | -2,556 | +20 | 0 → 10 | 0 → 5 | 0 → 294 | 9.8 | +5 |
| w6_old_v1_edge | 54,150 → 54,313(+163) | -100 | -4 | 0 → 10 | 0 → 5 | 0 → 565 | 7.0 | +0 |
| w6_old_v2_edge | 54,170 → 54,326(+156) | +432 | +13 | 0 → 10 | 0 → 5 | 0 → 273 | 8.2 | -59 |
| w6_old_v1_edge_plateau | 55,173 → 55,505(+332) | +720 | -8 | 0 → 10 | 0 → 5 | 0 → 326 | 6.2 | +0 |
| w6_golden_null_arm | 100,439 → 101,969(+1,530) | +8,158 | -1 | 0 → 10 | 0 → 5 | 0 → 2439 | 8.6 | +0 |
| v3_mem_store | 69,978 → 70,421(+443) | -2,021 | +79 | 0 → 10 | 0 → 5 | 0 → 383 | 7.6 | +168 |
| v3_mem_rel | 72,930 → 74,616(+1,686) | +144 | +213 | 0 → 10 | 0 → 5 | 0 → 642 | 9.4 | +185 |
| v3_classical | 97,563 → 96,961(-602) | -3,778 | +151 | 0 → 10 | 0 → 5 | 0 → 103 | 9.2 | -146 |
| v3_classical_mem_rel | 110,395 → 111,194(+799) | +3,558 | +86 | 0 → 10 | 0 → 5 | 0 → 98 | 10.6 | -31 |

- 5,000 体以外: classical 1,500 体 `d8eee505…`/25,808 → `4c8a9e08…`/26,156。合成世界の 5 構成は `CUR_SYN` に固定した。

### E4-4 U2(日の鍵の流れが次の日に 1 ブロック重なる)

- 既知の答え(試験・5 用途名): 旧の並びでは「鍵 d+1 の流れ」が「鍵 d の流れを 4 語ずらした写し」(36 語が完全一致)。counter では鍵 d の流れを 4,000 語引いても鍵 d+1 の 40 語と 1 語も同じにならない。2 日のラン(合成世界 120 体・既定 counter)で実際の重なり 0。
- これで「2 日以上のランの日ごとの差」を主張に使ってよい。ただし K9 のつなぎ(火〜金も月曜の予定)と曜日の比較の制限はそのまま。

### E4-5 検収 L1〜L3

- **L1**: テープの脇の meta に `rng_layout: "10e"` を書く。再生で、テープの `rng_scheme` が counter なのに印が無ければ(10c〜10f の counter の鍵の配置で録ったテープ)**明示の例外で止める**(未指定でも counter を明示しても)。meta の無い実テープ(stateful 扱い)と、印の無い stateful のテープは今のまま回る。試験 `test_e4_l1_…`。
- **L2**: `load_population(n=…)` に `rng_scheme`(既定 counter=engine と同じ)。`tools/c7/attr_arms.py` の `population_for` に `rng_scheme`。凍結した測りの道具 `rel8b_measure.py` の 3 引数の差し替えは `rng_scheme` を受けて使わない形にした(engine から呼んで TypeError にならない)。ほかの測りのスクリプト(`rel_measure.py`・`q111_measure.py`・`payroll_scale.py`)は 3 引数で呼ぶので既定の counter=engine の既定と同じ(10e より前の値の再現には stateful を渡す必要がある=凍結した道具なので直していない)。試験 `test_e4_l2_…`。
- **L3**: `cli.checkpoints_payload` の `schema` を `shibuya.cli/checkpoints/2` に(`combined` は既定で behavior-hash)・注を直した。読み手(`tools/c7`)は `schema` を見ない。試験 `test_e4_l3_…`。

### E4-6 試験

- 新しい既定に合わせた試験: 10c の 8 件・10a の meta(`rng_layout` の欄)・暦の口の CLI の既定・10f の交換可能性・日の表の張り直し・T3(率 100 → 1,000)。旧値の再現(10e より前)は `hash_scheme="full", rng_scheme="stateful"` を両方渡す。
- 張り替え: 帰無 `6c81c5ad8a99437a`/101,969・v3 `4fbf61616af1e3d2`/70,421(E2 の値は `*_stateful`)・関係 on `64f48b6571ec2ea1`/74,616・5,000 体の標本の在圏ブロックの数え・T7 と K19 の final。
- 新しい試験(`test_version_bump_10e.py`): 既定と切替口・U2 の既知の答え 5 用途名・2 日のランの重なり 0・U8・L1・L2・L3。K19 の試験の書き直し(counter で重なり 0・stateful だけ許す・slow の 5,000 体で作り直し 186)。

## E5 テープ版 4(A8・K1)

### E5-1 変えたこと

| ファイル | 何を |
|---|---|
| `engine/tape.py` | `TAPE_SCHEMA_VERSION = "shibuya.tape/4"`。版 3 の 14 列の後ろに 7 列: `recalled_first_tick`・`recalled_kind`・`recalled_object`・`recalled_source`(予約=空)・`acquaintance_ids`・`b5_text`・`b6_block_id`。`CALLS_SCHEMA_V4_DEFAULTS`(旧テープは空で読む)・`tape_v4_fields` |
| `engine/memory.py` | `RecallItem.first_tick`(エピソードは `mem_tick`・店の行は `sm_first`) |
| `perception/renderer.py` | `Rendered` に同定の 3 つと `acquaintance_ids`。`acquaintance_ids_in(b5)`: B5 の本文から `P-<id>(知人)` を拾う(見せた相手だけ) |
| `engine/llm_bridge.py` | `RenderedPrompt` に同定・知人・B5/B6 の本文。テープの行に 7 列 |
| `llm/fleet.py`・`engine/run.py` | `LLMCall` と `FleetTapeRow` に同じ欄。艦隊の応答行と繰り延べ行に 7 列(B6 は intern) |

- **鍵に日**(A8 の 1): テープの鍵の `tick` は 10a から通しの T。列は足さず、2 日のテープで tick が 1,440 以上になり鍵が日をまたいで衝突しないことを試験で確かめた。旧テープ(版 1〜3)は T = 日の中の tick=「日=0」として読める。
- **引いた記憶の同定**(A8 の 2)・**出どころの予約**(A8 の 3)・**B5・B6**(A8 の 4・K1): 上の 7 列。共有ブロック 6 本+B5+B6 の本文から、テープの鍵の `prompt_hash`(本文の sha256_cbor)を作り直せる。
- **手元の実テープ**(検収 D6): 発注書の「旧版(版 3)の実 LLM テープ 17 本」は言い方が違った。検収役の確かめでは、`data/` の実テープ 53 本のうち読めた 52 本は版 1(19 本)と版 2(33 本)で、版 3 は 0 本。全部が版 4 の読み口で読め、新しい 7 列は空、`Replay` も組めた。`c7-day-1` の calls.parquet は Parquet の印が無く読めない(10e より前からの破損)。

### E5-2 動いてはいけない量(19 構成・E4 と比べた・[e5_vs_e4.json](e5_vs_e4.json))

final・呼数・行動の件数・起床の内訳・顕著行為・出動・気づき・食事・ハッシュ: **19/19 不変**。テープの版 3 までの 14 列の名前・順・中身: **19/19 同じ**。

### E5-3 動いた量(テープの列と大きさ・5,000 体・1 日)

| 構成 | 呼数 | calls.parquet E4 → E5 [B] | blocks.parquet E4 → E5 [B] | blocks の行 E4 → E5 | 1 呼あたりの増分 [B] |
|---|---|---|---|---|---|
| w6_v3_default | 70,421 | 4,291,201 → 5,994,655 | 200,757 → 310,962 | 5,473 → 8,286 | 25.8 |
| w6_v3_activity_off | 58,495 | 3,281,311 → 4,665,224 | 51,914 → 125,027 | 778 → 2,838 | 24.9 |
| w6_v1_default | 60,899 | 3,247,632 → 4,717,998 | 51,264 → 126,221 | 766 → 2,890 | 25.4 |
| w6_v1_derive_v2_1 | 54,491 | 2,895,721 → 4,202,473 | 51,106 → 118,536 | 761 → 2,669 | 25.2 |
| w6_v2 | 60,758 | 3,247,771 → 4,709,712 | 51,063 → 123,418 | 765 → 2,799 | 25.3 |
| w6_v1_edge | 54,313 | 2,882,264 → 4,177,122 | 51,009 → 116,443 | 756 → 2,597 | 25.0 |
| w6_v2_edge | 54,326 | 2,894,833 → 4,185,427 | 51,075 → 103,181 | 758 → 2,187 | 24.7 |
| w6_v1_edge_plateau | 55,505 | 2,953,275 → 4,281,236 | 51,260 → 117,032 | 763 → 2,617 | 25.1 |
| w6_old_v1_default | 60,899 | 3,237,750 → 4,708,049 | 51,264 → 125,419 | 766 → 2,888 | 25.4 |
| w6_old_v1_derive_v2_1 | 54,491 | 2,893,720 → 4,200,330 | 51,106 → 117,916 | 761 → 2,665 | 25.2 |
| w6_old_v2 | 60,758 | 3,244,018 → 4,705,883 | 51,063 → 122,911 | 765 → 2,797 | 25.2 |
| w6_old_v1_edge | 54,313 | 2,875,147 → 4,169,940 | 51,009 → 115,939 | 756 → 2,595 | 25.0 |
| w6_old_v2_edge | 54,326 | 2,893,848 → 4,184,335 | 51,075 → 102,621 | 758 → 2,184 | 24.7 |
| w6_old_v1_edge_plateau | 55,505 | 2,961,630 → 4,289,572 | 51,260 → 116,546 | 763 → 2,616 | 25.1 |
| w6_golden_null_arm | 101,969 | 5,450,774 → 7,893,056 | 54,997 → 164,974 | 842 → 4,042 | 25.0 |
| v3_mem_store | 70,421 | 4,385,030 → 7,694,795 | 200,757 → 310,962 | 5,473 → 8,286 | 48.6 |
| v3_mem_rel | 74,616 | 4,633,081 → 8,218,843 | 208,453 → 331,524 | 5,719 → 8,891 | 49.7 |
| v3_classical | 96,961 | 5,519,325 → 7,580,801 | 289,715 → 293,616 | 8,403 → 8,484 | 21.3 |
| v3_classical_mem_rel | 111,194 | 6,436,918 → 11,635,089 | 295,646 → 308,882 | 8,543 → 8,846 | 46.9 |

1 呼あたりの増分は記憶の無い構成で約 21〜26 B、記憶 on で約 47〜50 B(zstd の後・calls と blocks の合計)。

### E5-4 試験

`test_version_bump_10e.py` の E5 の 5 件と、検収の T1・T3:
- **T1** `test_e5_t1_fleet_rows_carry_b5_b6_and_rebuild_the_prompt_hash`: 艦隊の経路(偽 vLLM 2 台・キュー満杯)の応答の行と繰り延べの行の全部に B5・B6 が入り、本文から `prompt_hash` を作り直せる。
- **T3** `test_e5_t3_recalled_identity_matches_the_memory_table`: 想起した時点の記憶の表(`mem_tick`・`mem_kind`・`mem_object`/店の行は `sm_first`・`sm_poi`)を控え、テープの同定 3 列と行番号ごとに突き合わせる(並びのずれ・種類と対象の取り違えで落ちる)。記憶+店の記憶の 1 日で店の行も含む。

## E6 締め

### E6-1 「版上げの最後に消す」切替口の一覧(消していない=親が決める)

| 切替口 | 何を再現するか | 消すときに書き直す試験 |
|---|---|---|
| `--hash-scheme full`(`Checkpoint.legacy_combined`・`core.soa.retired_columns_in_hash`・`Registry.retire`・`agents/state.py` の 3 行) | 10e より前の final | `AgentState.state_hash` を差し替えて腕の欄を除く 9 か所 / 段ごとの旧値(`test_presence_executor` の段 2c・3 段目・5 段目・`*_pre10e`・`test_relations_tenure` の full の行・`test_classical_social` の `_PRE10E`・`test_near_tiebreak`・`test_10a_review_fixes` の +2)/ `PRE10E_SYN`・`test_e1_retired_columns_…`。`test_ledger_wiring` の 2 本は `legacy_combined` の欄を使う |
| `--rng-scheme stateful`(`k19_counters` の旧の並び・salient と dispatch の Generator・`K19_ALLOW` の `stateful` の扱い) | E4 の前の乱数(10e より前の既定) | 上の段ごとの旧値の試験の全部・`*_stateful`・10c の stateful を明示した試験・K19 の stateful の分 |
| `--calendar-weekday day_index` | (E3 をやっていないので今も既定) | — |
| 旧 pickle の口 | — | **E2 で消した**(発注書 E2 の指示・10f の K23 (a)「10e まで」) |
| (K15)`fail_streak`・`plan_activity` | — | **K15 の 2 列の削除もここで**(親の決定=§E1-6・動く量なし) |

- **B6 のための注**(親の指示・コードは変えていない): 描画の天気は暦の日付で引く(`perception/renderer.py` の `weather()`=`when.strftime("%Y-%m-%d")` の鍵)が、体感温度は再生日の天気を使う。今は `engine/run.py` の `world_start` が再生日と同じなので合っているが、暦を一本化すると「描画は開始日の実際の天気、体感温度は再生日の天気」とずれる。B6 で両方を同じ日の行で引く形にする必要がある。

### E6-2 全体の動いた量(19 構成・final と呼数・段ごと)

E1 は final の定義だけ・E2 は O39 の掃除(呼数は不変)・E4 は乱数(呼数も動く)・E5 は不変。

| 構成 | HEAD final / 呼数 | E1 final | E2 final | E4 final / 呼数 | E5 final |
|---|---|---|---|---|---|
| w6_v3_default | `993276d5e5bb5cbe` / 69,978 | `3264c9fc190b3eb9` | `4985ff2fb3c771c4` | `4fbf61616af1e3d2` / 70,421 | `4fbf61616af1e3d2` |
| w6_v3_activity_off | `f746406eb78b024a` / 58,570 | `eb83e5b0c6c285e4` | `dbccca304e5b5484` | `6ef311ea2bcabbaa` / 58,495 | `6ef311ea2bcabbaa` |
| w6_v1_default | `0a52a4d3a90fa79f` / 60,970 | `aa721b19707f25e4` | `cd6e1283bb5931fd` | `9180ff01f380448a` / 60,899 | `9180ff01f380448a` |
| w6_v1_derive_v2_1 | `faada6a938570ef1` / 54,285 | `37557aa76c8d9f29` | `9ca7cb0fd1b149a2` | `d69cc0795cb27294` / 54,491 | `d69cc0795cb27294` |
| w6_v2 | `f4382c82dfa21764` / 60,901 | `52899ac1ad9657a6` | `0eb03d0870ad0983` | `88dc42eabbc8623e` / 60,758 | `88dc42eabbc8623e` |
| w6_v1_edge | `6db51cbd2b401129` / 54,150 | `7d06c9e0c3e7d3bb` | `ad7c60995dac93a5` | `abd6801c4e3ce142` / 54,313 | `abd6801c4e3ce142` |
| w6_v2_edge | `d61923edade6f05c` / 54,170 | `87035b6d3eef8aad` | `45e4636595c75d4b` | `00c7b8d57be27d15` / 54,326 | `00c7b8d57be27d15` |
| w6_v1_edge_plateau | `e32d69e91ff45e66` / 55,173 | `b3b181cbc50d6b1b` | `96b18f5301cf8483` | `a289e41bf7383db0` / 55,505 | `a289e41bf7383db0` |
| w6_old_v1_default | `e1fcd39b618dc768` / 60,970 | `d10606e9f87af856` | `58af81db49bedbaf` | `fb7b4b4755eb90c1` / 60,899 | `fb7b4b4755eb90c1` |
| w6_old_v1_derive_v2_1 | `46ca40a12eb54d58` / 54,285 | `48e493b4c6d16adb` | `5a1649b91e97eedb` | `ef68f751065530ad` / 54,491 | `ef68f751065530ad` |
| w6_old_v2 | `7c7d2423307fe571` / 60,901 | `2ffe172806a6291b` | `c2d7ab766cafcee9` | `4eacbf3c1a141d89` / 60,758 | `4eacbf3c1a141d89` |
| w6_old_v1_edge | `951af158650b2fc2` / 54,150 | `bd96d0c4a29d606f` | `d77cafef2e580fa5` | `2722cf8449b984bf` / 54,313 | `2722cf8449b984bf` |
| w6_old_v2_edge | `cf01958883d07209` / 54,170 | `610e8c13468fea39` | `6f71c723a474e837` | `14aff5b3c963e363` / 54,326 | `14aff5b3c963e363` |
| w6_old_v1_edge_plateau | `b94df1eb4c5b5557` / 55,173 | `43856c5b613ddfbd` | `b716d5aaee17e4b2` | `79149e728b5e85a2` / 55,505 | `79149e728b5e85a2` |
| w6_golden_null_arm | `72cb9cd52982da74` / 100,439 | `db765499cec1fef5` | `065a36d238aae477` | `6c81c5ad8a99437a` / 101,969 | `6c81c5ad8a99437a` |
| v3_mem_store | `e89fc1cdc327cf57` / 69,978 | `899dd4222a8cda75` | `0ae357f5d7f8b280` | `785b26683ed45a35` / 70,421 | `785b26683ed45a35` |
| v3_mem_rel | `40409ebed834126b` / 72,930 | `e27e45f3e9b62749` | `fe19250259a7058d` | `64f48b6571ec2ea1` / 74,616 | `64f48b6571ec2ea1` |
| v3_classical | `3390e3ec02d392a9` / 97,563 | `4a67879d2d9f8d49` | `4a67879d2d9f8d49` | `1470f952565a5d31` / 96,961 | `1470f952565a5d31` |
| v3_classical_mem_rel | `28ea80375e7ee646` / 110,395 | `ae86702196975458` | `8b85c6b5f82babba` | `e9a4fa4d2403acbb` / 111,194 | `e9a4fa4d2403acbb` |

### E6-3 予算表(5,000 体)

| 項目 | 10e の値 | 宣言・門 |
|---|---|---|
| SoA(agents)の宣言 | −5 B/体(死蔵の 3 列) | M1 ≤30 KB/体 |
| 知覚 SoA の宣言 | 18 → 2 B/体 | 自主の上限 24 B/体 |
| 状態のファイル(既定 v3・圧縮/展開) | 124 / 815 B/体(E2 の時点) | アジェンダ §7 を〔改訂(第329)〕で再宣言 |
| 状態のファイル(全腕・展開) | 6,179 B/体(39 万体で約 2.41 GB) | 読み口の上限 8 GiB(expedient) |
| テープ(版 4) | 1 呼あたり +21〜50 B | アジェンダ §7 の「最大 39 B+知人」は B5 の本文を数えていない(書き直しは親) |
| checkpoint のハッシュ(T7) | 下の表 | 門: 割合 ≤ 1%・目標: 1 回 ≤ 100 ms |

| 構成 | checkpoint の合計 [ms/日](E5) | ランの壁時計 [s] | 割合 | 最大 [ms] |
|---|---|---|---|---|
| w6_v3_default | 44.6 | 32.9 | 0.136% | 16.0 |
| w6_v3_activity_off | 17.7 | 25.2 | 0.070% | 5.3 |
| w6_v1_default | 15.0 | 23.6 | 0.064% | 4.3 |
| w6_v1_derive_v2_1 | 14.7 | 21.4 | 0.069% | 4.3 |
| w6_v2 | 16.5 | 24.1 | 0.068% | 4.9 |
| w6_v1_edge | 17.3 | 22.6 | 0.076% | 6.7 |
| w6_v2_edge | 14.6 | 23.2 | 0.063% | 4.3 |
| w6_v1_edge_plateau | 17.3 | 22.5 | 0.077% | 6.5 |
| w6_old_v1_default | 15.2 | 23.2 | 0.065% | 4.3 |
| w6_old_v1_derive_v2_1 | 15.0 | 21.0 | 0.071% | 4.4 |
| w6_old_v2 | 17.9 | 24.0 | 0.075% | 6.7 |
| w6_old_v1_edge | 16.1 | 22.3 | 0.072% | 5.1 |
| w6_old_v2_edge | 16.8 | 22.6 | 0.074% | 5.9 |
| w6_old_v1_edge_plateau | 20.3 | 22.7 | 0.089% | 8.0 |
| w6_golden_null_arm | 19.6 | 35.9 | 0.055% | 6.3 |
| v3_mem_store | 92.9 | 47.0 | 0.198% | 27.0 |
| v3_mem_rel | 91.6 | 44.8 | 0.205% | 25.5 |
| v3_classical | 65.0 | 42.8 | 0.152% | 22.2 |
| v3_classical_mem_rel | 102.6 | 62.1 | 0.165% | 35.3 |

### E6-4 親に確かめてほしい点

1. **K15(§E1-6)**: 指示の形(`retire` で `full` の再現を保つ)は成り立たない。→ 親の決定で (b)(`full` を消す commit で消す)。
2. **R1 の直しの範囲**: 検収の直し(O96)に加えて、O43・O44 の list の並びを状態から外した(多重集合)。→ 親の決定で R1 の一部として受け入れ(台帳の注に理由=適用は lexsort の順・繰り延べは配列で再投入)。
3. **E4 で住人が入れ替わる**(§E4-3): 4,191/5,000 体。→ 親からユーザーに伝える(第329)。
4. **E2 の「final は不変」の予想**: O39 が behavior の行なので掃除で final が動いた。挙動は不変。
5. **`run_day(rng_scheme=None)`**: 既定を counter にすると、`rng_scheme` の記録の無い旧テープ(=stateful)を既定のまま再生すると止まった。`response_delay` と同じ「未指定はテープの値」にした。
6. **展開の上限 8 GiB**(検収 L4)と **T7 の門 1%** は実行役の数(expedient)。
7. **テープの宣言**: §E6-3 の注(B5 の本文の分)。
8. **V3 の限界**: 同じ関数の中の移動は見えない。
9. リポの根の空のファイル `overlay_paths.txt`(検収 L5)は実行役が作ったものではない。スナップショットにも入れていない。

### E6-5 テスト

**全体(検収の直しの後に 1 回・作業木=E5・`python -m pytest -q -p no:cacheprovider -o addopts="" -rf`・この機械・51 分)**: **3,797 件を集めて 3,795 passed・0 failed・1 skipped・1 xfailed**(発注の時点の 3,769 件から +28・検収の前の 3,788 件から +9)。警告は 3 件(既知の暦の 2 件と、テープの脇の meta を消して旧テープを再生する 10a の試験の `RngSchemeWarning` 1 件=予定どおり)。

段ごとの木(HEAD `18ff37f` に各段のスナップショットを重ねた写し・`data` はリポへのつなぎ)でも回した:

| 段 | 回したもの | 結果 |
|---|---|---|
| E1 | E1 の対象の 25 ファイル(521 件) | 519 passed・1 skipped・2 failed=子プロセスを使う 2 件(子が木でなくリポの src を読む=写しの都合)。`PYTHONPATH` を木の src にして回し直して 2 passed |
| E2 | E1 の対象+E2 の 7 ファイル(665 件) | 661 passed・1 skipped・3 failed=同じ理由の 3 件 → 回し直して 3 passed |
| E4 | 全体(`PYTHONPATH` を木の src に・3,790 件) | 3,786 passed・2 skipped・1 xfailed・1 failed=`tests/vocab/test_registry_from_tape.py` のテープの道筋が相対パスにならない(木の `data` がリポへのつなぎのため・作業木では通る) |

新しい試験の置き場: `tests/engine/test_version_bump_10e.py`(E2 4・E4 11・E5 7=22 件)と、既存のファイルに足した E1 の 8 件(R1 の 2 件・T2 の 2 件を含む)・E2 の 3 件・K19 の書き直し。
