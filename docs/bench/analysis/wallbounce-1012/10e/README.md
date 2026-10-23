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

〔改訂(第330)〕E3 は第330 で切替口の裏に仕上げた(既定は変えていない)=§第330-E3。

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

〔改訂(第330・RET)〕この表の切替口(旧 pickle の口は E2 で消した)と K15 の 2 列は、第330 の RET で全部消した(§RET-1・§締め-2)。

| 切替口 | 何を再現するか | 消すときに書き直す試験 |
|---|---|---|
| `--hash-scheme full`(`Checkpoint.legacy_combined`・`core.soa.retired_columns_in_hash`・`Registry.retire`・`agents/state.py` の 3 行) | 10e より前の final | `AgentState.state_hash` を差し替えて腕の欄を除く 9 か所 / 段ごとの旧値(`test_presence_executor` の段 2c・3 段目・5 段目・`*_pre10e`・`test_relations_tenure` の full の行・`test_classical_social` の `_PRE10E`・`test_near_tiebreak`・`test_10a_review_fixes` の +2)/ `PRE10E_SYN`・`test_e1_retired_columns_…`。`test_ledger_wiring` の 2 本は `legacy_combined` の欄を使う |
| `--rng-scheme stateful`(`k19_counters` の旧の並び・salient と dispatch の Generator・`K19_ALLOW` の `stateful` の扱い) | E4 の前の乱数(10e より前の既定) | 上の段ごとの旧値の試験の全部・`*_stateful`・10c の stateful を明示した試験・K19 の stateful の分 |
| `--calendar-weekday day_index` | (E3 をやっていないので今も既定) | — |
| 〔第330〕`--world-assets-pre10e`(`AssetSource`・`PRE10E_FAMILIES`) | 10e で動いた量を資産ごとに測る(旧資産の退避先) | `test_assets_10e_b0_b1.py` の B1 の 4 件。**版上げ 1 回目の直後に消す**(答え 1-5) |
| 〔第330〕`--weather-scheme legacy`・`CALENDAR_UNIFIED=False` | 暦の一本化の前(世界の日付=再生日) | §第330-E3 の「張り替える golden」 |
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

### E6-6 段ごとの commit と記録の対応(第330・ユーザーの指示=[回答 10-12b](../../../design/v2-answers-2026-10-12b.md) §7 の 2 (1): 切り直しはしない)

4 つの段の commit は、親の重ね書きの道具の欠陥(一覧ファイルの改行が CRLF で `git add` が末尾の 1 本にしか効かなかった)で**試験 1 本ずつしか入っていない**。実体は訂正 commit `0389689` に 1 つで入っている。段ごとの帰属は次の表のとおり(ファイルの一覧は `0389689` の commit メッセージ)。

| 段 | 段の commit(中身=試験 1 本) | 実体の commit | 記録(動いてはいけない量・動いた量) | 節 |
|---|---|---|---|---|
| E1 | `e57c982` | `0389689` | `e1_vs_head.json`・`e1_full_vs_head.json`・`e1_vs_head_minus.json`・`sides/` | §E1 |
| E2 | `90e4a75` | `0389689` | `e2_vs_e1.json`・`e2_counter_vs_e2.json`・`budget_10e.json` | §E2 |
| E4 | `1f734fb` | `0389689` | `e4_vs_e2.json`・`e4_stateful_vs_e2.json`・`e4_vs_e2_counter.json`・[住人の入れ替わりの分布の比較](population_swap_check.md)(第330) | §E4 |
| E5 | `b0c7ddf` | `0389689` | `e5_vs_e4.json`・§E5-3 のテープの表 | §E5 |
| 文書 | `0e366cc` | — | IMPLEMENTED #87・PENDING・devlog・[検収の記録](review-10e-engine.md) | — |

再発防止はリポの仕組みにした(第330): `.gitattributes` は `* text=auto eol=lf` で改行を固定済み(事故は**リポの外**の一覧ファイルが原因)。`tools/commit_check.py` が「入れるはずのファイルの一覧(改行は正規化)」と `git diff --cached --name-only` を突き合わせ、`.githooks/pre-commit` が一覧ファイルがあるときに同じ検査と、記録の絶対パスの検査を行う。手順は README の「コミットの前」。

### E6-5 テスト

**全体(検収の直しの後に 1 回・作業木=E5・`python -m pytest -q -p no:cacheprovider -o addopts="" -rf`・この機械・51 分)**: **3,797 件を集めて 3,795 passed・0 failed・1 skipped・1 xfailed**(発注の時点の 3,769 件から +28・検収の前の 3,788 件から +9)。警告は 3 件(既知の暦の 2 件と、テープの脇の meta を消して旧テープを再生する 10a の試験の `RngSchemeWarning` 1 件=予定どおり)。

段ごとの木(HEAD `18ff37f` に各段のスナップショットを重ねた写し・`data` はリポへのつなぎ)でも回した:

| 段 | 回したもの | 結果 |
|---|---|---|
| E1 | E1 の対象の 25 ファイル(521 件) | 519 passed・1 skipped・2 failed=子プロセスを使う 2 件(子が木でなくリポの src を読む=写しの都合)。`PYTHONPATH` を木の src にして回し直して 2 passed |
| E2 | E1 の対象+E2 の 7 ファイル(665 件) | 661 passed・1 skipped・3 failed=同じ理由の 3 件 → 回し直して 3 passed |
| E4 | 全体(`PYTHONPATH` を木の src に・3,790 件) | 3,786 passed・2 skipped・1 xfailed・1 failed=`tests/vocab/test_registry_from_tape.py` のテープの道筋が相対パスにならない(木の `data` がリポへのつなぎのため・作業木では通る) |

新しい試験の置き場: `tests/engine/test_version_bump_10e.py`(E2 4・E4 11・E5 7=22 件)と、既存のファイルに足した E1 の 8 件(R1 の 2 件・T2 の 2 件を含む)・E2 の 3 件・K19 の書き直し。

## 第330 B0・B1・E3・B6(エンジン側)

> 実行役(Opus 5.5)の記録。親の検収の前・commit していない(親が snap_B0 → B1 → E3 → B6eng の順に重ねて commit する)。発注: 第330(親 Fable 5.1)。ユーザーの答え: [v2-answers-2026-10-12b.md](../../../../design/v2-answers-2026-10-12b.md) §1(1-3・1-4・1-5)。材料: [10e-build-side-prep.md](../10e-build-side-prep.md) §3・§4-2・§4-5・§5・§6。構築側(W12・W10 ON・W13 の年間化・W9 の影の日付・W7 の PH)は別の実行役。
> byte-check の基準は HEAD `0389689` の写し(`git archive`・[sides/head_0389689.json](sides/head_0389689.json))。各段は作業木の src をその段の時点で写した木で回した(手順は §1 と同じ・`--jobs 4〜5`)。HEAD の final は §E6-2 の E5 の列と 19/19 同じ。

### 第330-B0 資産の指紋(◎ 不変)

- **変えたこと**: manifest の `frozen_sources` に、ランが実際に読んだファイルの sha256 を、読み手ごとの印を付けて足した。`world:`=世界の資産(`world.assets._noise_stage_per_cell`)が読んだ騒音の地図 3 本(`w10_noise_stage_day.npy`・`w10_noise_stage_night.npy`・`w10_street_points.parquet`)/`perception:`=知覚(`perception.renderer._street_aggregate`)が読んだ同じ 3 本と W13 の時別/`process:`=世界過程が読んだ W13 の 2 本・W12 の 2 本(時刻表・方面ノード)・影の点の対応に使う W10 の街路点・**開いた影** `w9_shadow_<日付>.npy`(複数日は開いた日の全部)。騒音の 2 つの読み手には集約後のセル別の段(昼・夜)の補助の指紋 `noise_stage_cells` も出す=**2 つが同じ地図を読んだことが記録から分かる**。W14/W15 の凍結文の欄(印なし)は今のまま。
- 10f の表は足していない(`frozen_sources` は設定の節・子の鍵は道筋 1 つ)。
- **動いてはいけない量**: [b0_vs_head.json](b0_vs_head.json) = 19/19 で動いたのは `frozen_sources` だけ(final・呼数・行動・blocks・テープの列・behavior/full・締めの後の 2 本・暦の欄は同じ)。
- **動いた量**: manifest の `frozen_sources` だけ。既定 v3 の値(先頭 16 桁): `world:`/`perception:` の `w10_noise_stage_day.npy` `d4d02af1a770016f`・`night` `33ba443230ecb050`・`w10_street_points.parquet` `de1340b15bda281c`・`noise_stage_cells` `4649c1ca48b097ba`(両方同じ)・`process:w12_timetables.parquet` `154021c2e072a383`・`process:w12_external_nodes.parquet` `031fe09e9a566eff`・`process:w13_weather_days.parquet` `dcdd0989870c5123`・`w13_weather_hourly.parquet` `2552d1887fe831de`・`process:w9_shadow_2026-07-28.npy` `ad8b6c0e2579a7f8`。
- **試験**(`tests/engine/test_assets_10e_b0_b1.py`): 合成の W10 で指紋(同じ中身=同じ・1 点変えると変わる)/世界資産で 2 つの読み手の sha と段の指紋が一致しファイルの sha256 と一致/sha を偽の値にしても final・全 checkpoint・呼数が同じ。
- 発注の 3 本+W13+W9 に加えて、W12 の 2 本と影の点の対応の W10 街路点(世界過程の読み手)も足した(B1 の切替口で読んだ場所の証拠になる・manifest だけ)。

### 第330-B1 旧資産の切替口(◎ 不変)

- **変えたこと**: `--world-assets-pre10e <dir>`(`run_day(world_assets_pre10e=…)`・`cli.run`・`engine.run` の main)。読む場所の口は 1 つ(`world.assets.AssetSource`・`asset_source`)で、世界の資産(騒音)・知覚(騒音と W13)・世界過程(W13・W12・影の点・影)・計画実行層の資産がすべてこの口の `path` を通す。退避先の中で**ファイルがそろっている族だけ**を退避先から読む(`PRE10E_FAMILIES`: W10=騒音の段 2 本と街路点/W12=時刻表と方面ノード/W13=天気 2 本/W9=影)。`data/world/v2_pre_10e_2026-10-12`(構築役が写す)は 4 族とも、段ごとの写し `data/world/v2_10e_steps/<段>` はその段の族だけになる。族の一部だけ・退避先が無い・4 族のどれも無い=止める。**騒音の地図を読む 2 か所の集約後の段が違えば止める**(片方だけ旧い地図=`world` を退避先なしで読んで `run_day` に退避先を渡したとき)。manifest の `world_assets_pre10e`(退避先と族)は使ったランだけ出る。指紋(再開)には使ったときだけ載る(中身で同定=`PATH_ARGS`)。docstring・CLI の help・定数の注に「**版上げ 1 回目の直後に消す**」。
- **動いてはいけない量**: 既定=[b1_vs_b0.json](b1_vs_b0.json) 19/19 全欄同じ。切替口あり(今の資産の写しを一時の退避先に置いた・3 構成)=[b1_pre_vs_b1.json](b1_pre_vs_b1.json) 3/3 全欄同じ(final・呼数・行動・テープ・`frozen_sources`)。記録の退避先の場所は `<一時の写し>` に伏せた。
- **動いた量**: なし。10f の設定の節の表に `world_assets_pre10e` の 1 行(`CONFIG_PATHS_SHA256` `c2d09b29…` → `6e81ca53…`)。
- **試験**: 族の振り分けと止める 3 つ/今の資産を退避先から読んだランが既定と同じ/昼の騒音を全部「段 3」にした退避先で 2 つの読み手が同じ地図を読み、`world` だけ今の資産のときは止まる/CLI。
- W7(`w7_plan_spec.parquet`)は族に入れていない(答え 1-5 は 4 つ)。構築側の B6 で W7 の PH が動くので、W7 も分けて測るなら族を足す(親が決める)。

### 第330-E3 暦の一本化(切替口の裏・既定は不変)

- **切り替えは 1 か所**: `engine/calendar.py` の `CALENDAR_UNIFIED`(いま `False`)。`True` にすると `DEFAULT_WEEKDAY_MODE` が `real`・`DEFAULT_WEATHER_SCHEME` が `calendar` になり、`run_day`・CLI(`--calendar-weekday`・`--weather-scheme`)の既定がそろって変わる。開始日を渡さないランの暦の 0 日目は `DEFAULT_WORLD_START`(2026-07-13(月)・答え 1-4)+ `day_index` 日。試験は定数 1 つを書き換えた写しで既定がそろって変わることを確かめる。
- **世界の日付と再生日を分けた**(`engine/run.py`): `world_start`(暦)と `replay_date0`(0 日目の天気の行の日)は別の変数。`weather_scheme="calendar"` では世界の日付は暦のまま(再生日に置き換えない)。`legacy`(旧値の再現)だけが今までどおり「既定の開始日 + day_index」を再生日に置き換える。`calendar` では `real` でも開始日を渡さずに回せる(既定の開始日を使う)。
- **W7 の PH**: `SimCalendar.opening_row`(`real` の祝日=`OPENING_ROW_PH`=7・ほかは `table_weekday`)を W7 の行(0 日目・日の頭の張り直し・閉店中の店の翌日)で使う。`opening.rows_of_day` は PH の規則を持つ店は PH の区間、持たない店は日曜の行(10a の「祝日は土休扱い」のまま)。**資産の形は実行役の提案**: 営業時間の週の 8 つ目の要素=PH(`[]`=祝日は休み・`null`/無し=規則なし・`ProcessAssets.plan_ph_poi`)。**構築役の W7 の形と合わせる必要がある**。今の W7 は 7 要素なので何も動かない。曜日 7 日の表(W17・古典・mock 日課)の祝日=日曜は変えていない。
- **動いてはいけない量**: [e3_vs_b1.json](e3_vs_b1.json) 19/19 全欄同じ。
- **試験**(`tests/engine/test_calendar_10e_e3.py` 6 件): 定数 1 つの切り替え/既定の引数/内閣府 CSV で 7/20(海の日)=PH の行/PH の区間か日曜の行/W7 の 8 つ目の要素の読み口/世界資産の 2 日のラン(`real`+`calendar`)で日付が 07-13 → 07-14 と進み、W7・W17(計画実行層)・鉄道・古典の曜日の行が legacy の 2 日のランと同じ(月曜始まり)。既存の `test_calendar_sites.py::test_runner_reads_the_real_calendar` の祝日の行の期待を「6」→「PH の行(PH の無い店は日曜の行)」に直した(定義の変更)。

**切り替えたときに動く所**(`CALENDAR_UNIFIED=True`・開始日なし・`day_index=0`):

| 何が | 今(legacy・day_index) | 切り替え後(calendar・real) | 根拠 |
|---|---|---|---|
| 世界の日付(manifest の `start_sim_datetime`・`calendar.days`) | 再生日(07-28) | 2026-07-13 + day_index 日 | `engine/run.py` の暦の 0 日目 |
| 曜日・土休 | day_index・祝日を見ない | 実の曜日+内閣府の祝日(祝日=土休・曜日 7 日の表は日曜・W7 は PH の行) | `SimCalendar` |
| 日ごとの乱数の鍵(`day_key`) | day_index + 日 | 日番号(day_index=0 なら同じ) | `SimCalendar.day_key` |
| 開始日の検査 | 違反は警告 | 違反で止める: 0 日目が月曜でない(day_index ≠ 0)・複数日が平日に収まらない(6 日以上のラン)・学校の長期休み | `check_start` |
| 天気の再生日 | 層から一様(影のある日に絞る=07-28) | 暦の日付の実際の天気。窓の外(今の 35 日では 07-13)は夏×平日の層から日数の割合で | §第330-B6 |
| 日の出・日の入り・太陽高度 | 再生日の W13 の行 | 暦の日付から計算(07-13 は 04:35/18:59) | `engine.solar` |
| 体感温度(WBGT・暑さ段) | 再生日の W13 の値 | 再生日の気象 × 暦の日付の太陽高度 | 同上 |
| 影 | 再生日の影 | 暦の日付の影(無ければ近い日+警告) | 同上 |
| 描画 B3 | 再生日の行の語 | 天候=再生日・日照=暦の日付・暑さ=体感温度と同じ段 | `renderer.weather_words_fn` |
| 合成世界(気象資産なし) | 日の出 5:00・日の入り 19:00 の固定 | 暦の日付の日の出と日の入り(体感温度は 5 の固定のまま) | `EnvironmentProcess._pick_day_calendar` |
| 再開の指紋 | — | `weather_scheme="calendar"` が載る(切り替え前の状態のファイルからは再開できない=止まる) | `run_day` の指紋 |
| テープの再生 | — | 切り替え前に録ったテープは `weather_scheme="legacy"`・`calendar_weekday="day_index"` を渡して再生する(テープの meta にまだ記録していない) | 親に確かめてほしい点 |

**親が既定を切り替えるときの手順**: (1) 構築側を取り込む(W13 の年間化=07-13 が窓の中・W9 の 07-13〜07-17 の影・W7 の PH の形をこの節の形にそろえる)(2) `engine/calendar.py` の `CALENDAR_UNIFIED` を `True` にする(この 1 行だけ)(3) 下の golden を張り替える(4) byte-check 19 構成で動いた量を記録する(下の B6 の表は今の資産=07-13 が窓の外での値)。

**張り替える golden の一覧**(定数を `True` にした写しで全体テストを回して落ちたもの・写し=作業木の最終の版に `CALENDAR_UNIFIED=True` の 1 行だけを替えた木・`data` は本体へのつなぎ・51 分・3,789 passed / 29 failed / 2 skipped / 1 xfailed):

29 件(全体 3,821 件のうち)=A 12 件+B 14 件+C 3 件。A・B は作業木の既定(`False`)では通る。

- **A. final・呼数の golden(張り替え・値の前後を記録に)12 件**: `test_presence_executor.py` の 6 件(`test_null_arm_reproduces_the_recorded_checkpoint`・`test_v3_default_reproduces_the_recorded_checkpoint`・`test_l4_scale_1_reproduces_the_stage_2c_checkpoints`・`test_hunger_model_v1_reproduces_the_stage_3_checkpoints`・`test_leave_effect_off_reproduces_the_stage_5_checkpoints`・`test_hash_scheme_full_reproduces_the_pre_10e_checkpoints`)/`test_classical_social.py::test_run_golden_and_arms`/`test_relations_tenure.py::test_relations_on_arm_golden_old_and_new`/`test_intent_chooser.py::test_poi_target_legacy_reproduces_the_pre_2a_checkpoints_q13`/`perception/test_near_tiebreak.py::test_classical_checkpoint_moves_with_hash_and_id_reproduces_the_old_one`/`test_state_checks_10f.py::test_k19_runtime_default_v3_5000_known_counts`/`test_state_ledger_10b.py::test_t7_hash_cost_within_the_declared_cap[v3_default]`(T7 の final)。旧値の再現の golden(段 2c・3 段目・5 段目・`full`)は、`weather_scheme="legacy"`・`calendar_weekday="day_index"` を渡して旧値を保つか、張り替えるかを親が決める。
- **B. 今の既定の約束を書いた試験(明示の引数を足すか書き直す)14 件**: `test_calendar_10e_e3.py::test_e3_defaults_come_from_one_constant`(切り替えの試験そのもの)/`test_calendar_sites.py::test_cli_switches_and_defaults`/`test_calendar.py::test_day_index_mode_ignores_holidays_and_keeps_the_old_values`/`test_10a_review_fixes.py` の 3 件(`test_start_check_runs_on_the_calendar_after_the_weather_date`・`test_unreadable_csv_stops_real_and_nulls_the_manifest_in_day_index`・`test_real_day_key_is_the_day_number`)/`test_sim_time_T.py` の 4 件(`test_manifest_records_tick_seconds_and_start`・`test_real_calendar_run_needs_a_valid_start`・`test_start_date_moves_the_prompt_clock`・`test_school_holiday_in_day_index_mode_only_warns`)/`day_index ≠ 0` を real の既定で回して開始日の検査で止まる 2 件(`processes/test_rng_scheme_10c.py::test_run_day_passes_day_key0_to_the_counter_key`・`test_salt_seed_split_10f.py::test_road_works_day_key_with_nonzero_day_index`)/seed の交換可能性の 2 件(`test_env_and_sections_10f.py::test_seed_exchangeability_passes_for_v3_seeds_and_fails_on_a_config_change`・`test_relations_on_5000_seeds_are_exchangeable_and_config_leaves_do_not_move`=今の W13 では 07-13 が窓の外で、層からの抽選の鍵が環境の seed=seed なので seed 1 と 2 で再生日が違う。W13 の年間化の後は 07-13 が窓の中=実際の天気になり、この 2 件は落ちない見込み=推測)。
- **C. 写しの木と環境の都合(切り替えとは関係ない)3 件**: `test_resume_10d.py::test_resume_in_a_fresh_process_with_empty_caches`(子のプロセスが写しでなく本体の src を読み、指紋が親と違う)・`vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(`data` がつなぎのためテープの道筋が相対にならない・作業木でも落ちる)・`test_env_and_sections_10f.py::test_t1_two_processes_write_the_same_env_id_and_final_to_the_files`(子のプロセスの env_id が親と違う=写しには `.git` が無い・作業木でも全体テストの中で 1 回落ちた=下の全体テストの注)。

### 第330-B6 天気=再生日・太陽と影=暦の日付(エンジン側・切替口の裏・既定 legacy)

- **切替口**: `--weather-scheme {legacy,calendar}`(`run_day(weather_scheme=None)`=`DEFAULT_WEATHER_SCHEME`=いま `legacy`)と、揺らす口 `--weather-perturb`(`run_day(weather_perturb=False)`)。
- **規則**(答え 1-3・`engine/processes/environment.py` の注 1〜6):
  1. 天気(雨・気温・湿度・天候型・WBGT の入力)は**再生日**の W13 の行。日の出・日の入り・太陽高度・影は**暦の日付**から(`engine/solar.py`=構築段 `build.field.w13_weather` と同じ式の写し・同じ入力で同じ浮動小数を返すことを試験で固定)。WBGT は「再生日の気温・湿度・風・日照 × 暦の日付の太陽高度」で計算し直す(W13 の時別の 4 列を読む)。
  2. 再生日の既定は**その日の実際の天気**(暦の日付に W13 の行があれば再生日=暦の日付)。
  3. **揺らすとき**=`--weather-perturb`(アンサンブルはこれを付けて環境の seed を変えて回す)と、**暦の日付が窓の外のとき**は、同じ季節(気象庁の区分)× 平日/土休 の中から、天候型を窓の中の日数の割合で引き、その型の日を一様に引く(`sample_calendar_day`・鍵は環境の seed と `blake3("calendar|季節|平日/土休|日番号")`)。層が空なら隣の季節 → 全季節 → 平日/土休を問わず、と広げて警告(`WeatherWarning`・**expedient**・未リサーチ)。「再生日は影のある日に絞る」は calendar では使わない。
  4. 暦の日付の影が無いときは、いちばん近い日付の影(同じ近さなら前の日)を読み、警告と manifest の記録(`weather.days[].shadow_fallback`)を残す(**expedient**)。
  5. 描画の B3: `engine.run` が `renderer.weather_words_fn` を差し込む(天候の語=レンダラの W13 の表を再生日で引く・日照の語=暦の日付の日の出と日の入りを時の中ほどと比べる・暑さの語=体感温度と同じ暑さ段)。
  6. 複数日のランは日ごとに暦の日付が進み、その日の規則で引き直す。乱数は環境の seed だけ(母集団の seed・動きの seed では動かない)。
- **manifest**: 新しい欄 `weather`(`scheme`・`perturbed`・日ごとの `calendar_date`・`replay_date`・`stratum`・`how`(actual/sampled/legacy)・`widened`・`shadow_date`・`shadow_fallback`・日の出と日の入り・`warnings`)。設定の節(`replay_date` と同じ)・`CONFIG_PATHS_SHA256` `6e81ca53…` → `8e53b145…`・manifest の末尾の欄の試験の `E10_KEYS` に `weather`。
- 乱数の監査: `sample_calendar_day` の流れを `rng_audit.SAFE_SITES` に足した(鍵 1 語・引く語数 2・15 → 16 か所・`test_state_checks_10f.py` の数を直した)。seed の近くのハッシュの場所の表(`test_salt_seed_split_10f.py::_HASH_SITES`)にも「層の名前と日番号を数にするだけ」で足した。
- 状態台帳: 新しい属性はすべて `EXCLUDED`(環境の過程の `weather_scheme`・`perturbed`=CONST/`_cal_wbgt`・`_cal_stage`・`_sun_exact`・`weather_days`・`weather_warnings`・`shadow_sources`=CACHE/レンダラの `weather_words_fn`・`weather_words_key_fn`=REF)。表の行と軸は変えていない(既定の behavior-hash は不変)。
- **動いてはいけない量**(既定 legacy): [b6_vs_e3.json](b6_vs_e3.json) 19/19 全欄同じ。
- **既知の答え**: 世界資産 200 体・1 日で、`calendar`+開始日 2026-07-28(窓の中=実際の天気・再生日=暦の日付)のランは、legacy のランと **O56 の `stratum`(層の名前「夏|平日|雨」/「平日|雨」)のほかは全 checkpoint の全行が同じ**(呼数も同じ)。実資産の 35 日すべてで、暦の日付=再生日なら計算し直した WBGT(2 桁)・暑さ段・日の出・日の入りが W13 の値と一致。
- **切り替えたときに動く量**(今の資産=W13 は 35 日・07-13 は窓の外・影は 07-28 だけ。`weather_scheme=calendar`・`calendar_weekday=real`・開始日なし・[b6_unified_vs_b6.json](b6_unified_vs_b6.json)): 19 構成とも世界の日付 2026-07-13・再生日 **2026-08-31**(夏×平日の層から引いた・層を広げていない)・影は 07-28(近い日・警告 1 件)・日の出 04:35/日の入り 18:59。顕著行為 10・出動 5 は同じ。

| 構成 | 既定(B6)final / 呼数 | 切り替え後 final / 呼数 | 気づいた延べの差 | 食事の差 |
|---|---|---|---|---|
| w6_v3_default | `4fbf61616af1e3d2` / 70,421 | `de954c74b2153515` / 65,604 | +73 | -117 |
| w6_v3_activity_off | `6ef311ea2bcabbaa` / 58,495 | `8dbc024aa57236d7` / 49,941 | -19 | -335 |
| w6_v1_default | `9180ff01f380448a` / 60,899 | `5bbbb130dacbe29e` / 52,104 | -390 | +0 |
| w6_v1_derive_v2_1 | `d69cc0795cb27294` / 54,491 | `4f9a9dea5d3a9c08` / 45,502 | +62 | +0 |
| w6_v2 | `88dc42eabbc8623e` / 60,758 | `a6376b105ad3e1af` / 52,381 | +51 | -264 |
| w6_v1_edge | `abd6801c4e3ce142` / 54,313 | `9f328dfdca6cc58c` / 46,370 | -67 | +0 |
| w6_v2_edge | `00c7b8d57be27d15` / 54,326 | `285a095143ec9453` / 46,695 | +464 | -159 |
| w6_v1_edge_plateau | `a289e41bf7383db0` / 55,505 | `71a56784549fb3b5` / 48,657 | +157 | +0 |
| w6_old_v1_default | `fb7b4b4755eb90c1` / 60,899 | `fb9f2d2153adb66c` / 52,104 | -390 | +0 |
| w6_old_v1_derive_v2_1 | `ef68f751065530ad` / 54,491 | `9fac7c8ac99efbc6` / 45,502 | +62 | +0 |
| w6_old_v2 | `4eacbf3c1a141d89` / 60,758 | `70e53e9fc7f32690` / 52,381 | +51 | -264 |
| w6_old_v1_edge | `2722cf8449b984bf` / 54,313 | `b76dee513ec8c223` / 46,370 | -67 | +0 |
| w6_old_v2_edge | `14aff5b3c963e363` / 54,326 | `868a896ee5564ba4` / 46,695 | +464 | -159 |
| w6_old_v1_edge_plateau | `79149e728b5e85a2` / 55,505 | `77a1282e45dfb402` / 48,657 | +157 | +0 |
| w6_golden_null_arm | `6c81c5ad8a99437a` / 101,969 | `67e4e5a2c3478c8b` / 98,192 | -1,185 | +0 |
| v3_mem_store | `785b26683ed45a35` / 70,421 | `2151a9d1841ada99` / 65,604 | +73 | -117 |
| v3_mem_rel | `64f48b6571ec2ea1` / 74,616 | `2f211f760d4fd165` / 69,403 | -117 | -127 |
| v3_classical | `1470f952565a5d31` / 96,961 | `4f1177b44185fa7e` / 93,829 | +838 | -38 |
| v3_classical_mem_rel | `e9a4fa4d2403acbb` / 111,194 | `ccf54a1ee81cd500` / 107,088 | +864 | -132 |

- **試験**(`tests/engine/test_weather_calendar_10e.py` 11 件): 太陽の式=構築段/35 日の WBGT・暑さ段・日の出と日の入りが W13 と同じ/合成の W13(2025-09-01〜2026-08-31)で: 窓の中=実際の天気と暦の日付の太陽/揺らしたときの天候型が日数の割合(夏の平日の猛暑・晴・雨がおよそ 3:2:1)に沿う(1,200 回)/窓の外=層から・冬の無い W13 で隣の季節へ広げて警告/影は暦の日付・無ければ近い日と警告/WBGT は再生日の気象 × 暦の日付の太陽/日が進む・揺らさない限り seed を変えても実際の天気・揺らすと環境の seed だけで引き直す(動きの seed・母集団の seed では動かない)/legacy は今のまま/世界資産の既知の答え(上)/**B3・体感温度・日の出と日の入りの語が同じ規則**(README §E6-1 B6 のための注 (1)〜(3)・07-13=窓の外で層から引き警告が出る)。

### 第330 テスト・スナップショット・親に確かめてほしい点

- **全体テスト**(作業木・`python -m pytest -q -p no:cacheprovider -o addopts="" -rf`): **3,821 件を集めて 3,817 passed・2 failed・1 skipped・1 xfailed**(58 分・この機械)。落ちた 2 件はどちらも環境の都合で、今回の変更とは関係しない: (1) `vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(`data` が本体へのつなぎのためテープの道筋が相対にならない=§E6-5 の E4 の段の注と同じ)/(2) `test_env_and_sections_10f.py::test_t1_two_processes_write_the_same_env_id_and_final_to_the_files`(子のプロセス `python -c` が作業木でなく本体の src=editable の版を読むので env_id の git の欄が親と違う。HEAD の試験ファイル `test_area_source_c9c.py` の後に回しても落ち、`PYTHONPATH=<作業木>/src` を付けた回(関係する 66 件・この試験を含む)では通った)。全体の前の版(`--weather-perturb` に直す前)の全体テストでは、ほかに `test_change_detect_p6.py::test_p6_change_detection_under_2ms_at_400k_agents`(並べて回した負荷で 3.4 ms)と、直した 2 件(seed の近くのハッシュの表・K19 の静的な安全な呼び手)が落ちた。
- スナップショット: `snap_B0`・`snap_B1`・`snap_E3`・`snap_B6eng`(HEAD からの累積)。
- 親に確かめてほしい点:
  1. **W7 の PH の形**(週の 8 つ目の要素)は実行役の提案。構築役の W7 と合わせる。
  2. **「揺らす」の口**: 発注の「`--environment-seed` を変えたとき」を、明示の切替口 `--weather-perturb` にした(揺らすときは環境の seed を変える)。最初は「環境の seed が動きの seed と違えば揺らす」で作ったが、10f の salt の比較(環境の seed を固定し動きの seed だけを変える)で salt ごとに `weather.perturbed` が変わり、`test_t3_runner_first_diff_matches_first_diff_py_and_crn_checks` の交換可能性が落ちた(calendar では salt ごとに天気が揺れて共通の乱数が崩れる)。「環境の seed を明示したら揺らす」も 10f の「省略と同じ値の明示は同じラン」に反する。暦の日付が窓の外のときの抽選の鍵は、揺らさなくても環境の seed。
  3. 層を広げる順(隣の季節 → 全季節 → 平日/土休を問わず)と、近い日の影の選び方(同じ近さなら前の日)は expedient。
  4. 切り替え後は合成世界(気象資産なし)でも日の出と日の入りが暦の日付になる(物理の規則を優先した・固定の 5:00/19:00 にしたいなら 1 行で戻せる)。
  5. 切り替え前に録ったテープを切り替え後に再生するときは `weather_scheme="legacy"`・`calendar_weekday="day_index"` を渡す必要がある(テープの meta への記録は入れていない)。
  6. B0 で W12 と影の点の W10 街路点の指紋も足した(発注より広い・manifest だけ)。B1 の族に W7 は入れていない。


---

# 10e 構築側(第330・B2〜B6)

> 実行役(Opus 5.5)の記録。親の検収の前。commit していない(親が snap_B2 → B3 → B4 → B5 → B6build の順に重ねて commit する)。作業木 `10e/build-b2-b5`(HEAD `0389689`=E5)。
> 発注: 第330(親 Fable 5.1)。ユーザーの答え: [回答 10-12b](../../../../design/v2-answers-2026-10-12b.md) §1(1-1〜1-6)。材料: [10e の構築側の材料](../10e-build-side-prep.md)。手順書: [第 2 波 §W10](../../wave2-2026-09-30/README.md)。
> 世界の資産は作業木の**私有の写し** `data/world/v2`(本体から robocopy した 194 ファイル)で作り直した。エンジン側(`engine/`・`perception/`・`world/`・`cli.py`)は触っていない。byte-check はこの作業木のエンジン(=E5)で回した。

## B0 退避と基準

- **退避**(B の何よりも先・1 回): W9(影 1 日+面の表)・W10 の 6 本・W12 の 3 本・W13 の 2 本・W18〜W20 の出力と各ヘッダ・`build_manifest.json` を `data/world/v2_pre_10e_2026-10-12/` に同じ名前で写し、`MANIFEST.sha256`(31 行)を置いた。各出力の sha256 はヘッダの宣言と一致し、W10 の 6 本は材料 §1-2 の 1 の先頭 16 桁と一致した(`d4d02af1a770016f`・`33ba443230ecb050`・`6f3e3b0f2b4c674f`・`4d682d3ac1eba0c4`・`de1340b15bda281c`・`c4c93313aa89aa19`)。W9 の面の表 `w9_shadow_planes.parquet` と `build_manifest.json` は発注の一覧の外だが、旧値の再現に要るので足した。
- **基準の再構築**(何も変える前・私有の写しで 1 回・41.6 秒): データの出力はすべて本体と sha256 一致。違ったのは **W12 と W16 のヘッダの `input_hash` だけ**(と、それを写す W18・W19・W20・manifest)。原因は本体の作業コピーの `docs/bench/pt_shibuya/pt6_summary_core0241.json` が **CRLF**(755 行=755 バイト多い)で、作業木は git の中身どおり **LF**。本体の資産はその CRLF の写しで構築されていた。**中身は同じで改行だけが違う**(`git show HEAD:` の sha256 は作業木と一致)。以下の「前」は、この基準(LF)の値。
- **byte-check の基準**: 基準の写しで 19 構成を回した side(`base`)は、E5 の記録 `sides/e5.json` と **19/19 構成の全欄が一致**した(`compare` の差 0)。以下の段ごとの比べは `base` を前に取る(ファイル名は発注の例に合わせて `b3_vs_e5.json` ほか)。

## B2 W12 の切替口を効くようにする(◎ 資産のバイトも不変)

- **変えたこと**(`build/field/w12_external_nodes.py`): 定数 `PM_PEAK_TRAINS_PER_HOUR`(既定 **None**=表は無い)と `pm_peak_for_line()`。`PM_PEAK_ASSUMED_EQUAL_TO_AM=False` のとき `run()` は表の値を夕ピーク(17〜19 時)に渡す。False で表が無い・線が無いときは **ValueError**(親案の「None → 夕=朝」を、False のときは止める形にした。False が黙って夕=朝に戻ると、直した欠陥と同じことが起きるため)。他社の比(メトロの 0.79)は使わない(答え 1-2)。既定(True)の params に鍵を足さない。False のときだけ params と notes に `pm_peak_trains_per_hour` を足し、expedient の文言を切り替える。
- **不変の確認**: W12 段だけを一時ディレクトリで走らせ、3 本の出力と `W12.header.json` の sha256 が基準と一致(時刻表 `154021c2e072a383`・方面ノード `031fe09e9a566eff`・重み `eb85f8acf5a20809`・ヘッダ `b867a87687ce5e77`)。
- **試験**(新 `tests/build_field/test_w12_pm_peak_switch.py`・4 件): 規則の単体/既定の表が無い/**`run()` の出力**で 5 線の夕ピークが試験の表(10 本/時)になり、朝ピークとメトロの実ダイヤの行は動かない/False で表なし=ValueError。

## B3 丸め(▲ 動く・再構築 1 回目)

- **変えたこと**: `equal_interval_departures` を「時刻を**有理数(`fractions.Fraction`)で積み**、出す分だけ切り捨てる」に直した(答え 1-1 の (i))。浮動小数で積むと誤差で 1 時間の本数が 1 本ずれうるので有理数にした。W12 の `STAGE_VERSION` 1.0.0 → **1.1.0**。
- **試験**: `test_equal_interval_departures_hourly_count_equals_declared`(18・19・24・27 本/時)を足した。間隔が一定の日(比 1.0)は 5〜23 時の**どの 1 時間も宣言の本数ちょうど**。ピークとオフピークが入れ替わる日は、ピークの真ん中の時(8・18 時台)が宣言どおりで、境の時(7・9・17・19 時台)は入る時刻の端数で宣言から 1 本までずれうる(小数で積む規則の性質・下の表の 7 時台)。既存の `test_equal_interval_departures_headways`(20 本/時)はそのまま通る。B2 の試験は夕と朝を真ん中の時で比べる形にした。
- **再構築 ×2**(`python -m shibuya.build.run --out data/world/v2 --data data --keep-stage W17`・各約 30 秒・終了コード 1=既知の 3 ゲート): 2 回の 116 ファイルの sha256 が全部一致。
- **動いた量**(基準 → B3): `w12_timetables.parquet` `154021c2e072a383` → **`c548b2bb7ecd5c21`**(9,574 → **9,014** 行・等間隔 7,978 → **7,418**・メトロの実ダイヤ 1,596 行は同じ)。ヘッダ W12・W18・W19・W20、`wc_index.json`(W18 の被覆の表の「鉄道運行」の `n_sim` 9,574 → 9,014=発注の「動く量」の一覧に無かった)・`w19_freeze.json`・受入パックの `gate_table.md`・`summary.json`・`build_manifest.json`。**動かなかった**: `w12_external_nodes`・`w12_generation_weights`・W16・W17・W10・W13 ほか 106 ファイル。

| 線(上り・平日の本/時は 1 方向) | 平日 1 日 旧→新 | 土休 1 日 旧→新 | 平日 7/8/9 時 旧→新 | 平日 10 時 旧→新 | 平日 17/18/19 時 旧→新 |
|---|---|---|---|---|---|
| 田園都市線(宣言 27) | 380→357 | 580→514 | 30/30/30→27/27/27 | 15→15 | 30/30/30→26/27/27 |
| 東横線(24) | 340→317 | 447→457 | 30/30/30→24/24/24 | 12→13 | 30/30/30→24/24/24 |
| 井の頭線(27) | 380→357 | 580→514 | 30/30/30→27/27/27 | 15→15 | 30/30/30→26/27/27 |
| 山手線(18) | 254→237 | 387→343 | 20/20/20→17/18/18 | 10→10 | 20/20/20→17/18/18 |
| 埼京線(19) | 254→251 | 387→362 | 20/20/20→18/19/19 | 10→11 | 20/20/20→19/19/19 |

  平日 1 日の値は材料 §2-2 の見込み(380→357・340→317・380→357・254→237・254→251)と一致。東横線の土休は増える(旧は 23.5 本/時が 2.5 分→3 分に丸められて 20 本/時)。上り・下りは全線で同数。
- **エンジンの動いた量**(19 構成・[b3_vs_e5.json](b3_vs_e5.json)): **19/19 構成で final が動いた**。呼数の合計 1,264,661 → 1,265,034(+373)。既定 v3 70,421 → 70,500・v3 活動層 off 58,495 → 58,900・v1 既定 60,899 → 61,918。気づき(`noticed`)が大きく動く構成がある(golden の空の腕 2,439 → 624・古典 103 → 927)。構成ごとの表は §B6-4。
- **D-44 の判定の前提が変わる**(答え 1-1): [D-44 の記録](../../d44-controls-2026-09-30/README.md) の W12#5(山手線 18 vs 16/20)と W12#7(夕ピーク)は、間隔の丸めで「18 と 20 が同じダイヤ」・「夕の切替口が効かない」資産の上で「駆動しえない」と判定した。直した後は 18・16・20 が別のダイヤになり、夕の切替口も効く。回し直すかは感度試験の段で決める(10e の外)。
- **宣言の台帳**: `tools/c8/sensitivity_v1.json` の S-W14-JRPHASE の `declared` を「9,574 便(うち等間隔 7,978)」→「**9,014 便(うち等間隔 7,418)**」に直し、〔改訂(第330 B3)〕の注で「下の result は直す前の資産で測った値(2026-09-10)」と書いた。result の数値は変えていない。
- 段の後の出力: `data/world/v2_10e_steps/B3/`(動いた 10 ファイル+`MANIFEST.sha256`)。

## B4 W10 ON+Q7(▲ 動く・再構築 2 回目)

- **変えたこと**(`build/field/w10_noise.py`・第 2 波 W10-6 の手順書 1〜3): `USE_ROAD_NAME_MATCH=True`・`ROAD_NAME_REQUIRE_NAMED_SAME_CLASS=True`(Q9 は False のまま)・`STAGE_VERSION` 1.1.0 → **1.2.0**。docstring と定数の注の「既定 OFF」を直し、`road_name_match_off_reason` は OFF のとき「旧値の再現の切替口・段 1c の時点の理由」と書く形にした。**交通の過程との食い違いの宣言**(10-03 §9-4 の 1・3-2・第 2 波 Q-W10e)を ON のときだけ expedients と notes(`traffic_process_mismatch`)に 1 行足した: 「静的な騒音場は区間別・動く車(`engine/processes/traffic.py`)は klass 既定のまま=食い違いを宣言して進む(車の段 R-67 まで)」。
- **再構築 ×2**: 2 回の 116 ファイルの sha256 が全部一致。W10 の出力は第 2 波の ON+Q7 と一致: `w10_noise_stage_day.npy` **`e760a6dcbcb08003`**・`w10_noise_stage_night.npy` **`9cd06ebd13d2feb9`**・`w10_noise_day.npy` **`022121e08d508d5d`**・`w10_noise_night.npy` **`f8cccfd4376613e1`**・`w10_edge_section.parquet` **`6bd90df450347d18`**・街路点 `de1340b15bda281c`(不変)。ゲート `primary_secondary_sections_matched` 0 → **202(PASS)**・当てた辺 0 → 225・`calibration_max_abs_residual_db` は **7.3 のまま**(FAIL・終了コード 1 は今と同じ)。落ちるゲートは W10 の較正と W9 の容量の 2 つになった。
- **動かなかった**(B3 の後と比べて 102 ファイルが同じ): 街路点・W8・W9・W12・W13・W15・W16・W17・W18 の `wc_index.json`/`wc_reverse_index.json`。**動いた** 14 ファイル: W10 の 5 本とヘッダ・W18〜W20 のヘッダ・`w19_freeze.json`・受入パックの `noise_day.png`・`gate_table.md`・`summary.json`・`build_manifest.json`。
- **騒音段階が変わるセル**(エンジンの集約 `world.assets._noise_stage_per_cell` で退避先の資産と比べた・[b4_w10_cell_stage_diff.json](b4_w10_cell_stage_diff.json)): 520 セルのうち**昼 27・夜 22**(第 2 波の値と同じ)。昼は「騒がしい→うるさい」10・「うるさい→騒がしい」6 ほか、夜は「騒がしい→うるさい」15 ほか。道具 [w10_cell_stage_diff.py](w10_cell_stage_diff.py)。
- **主の物差し(診断・答え 1-6 の 3)**: [w10_primary_ruler.py](w10_primary_ruler.py)・[b4_w10_primary_ruler.json](b4_w10_primary_ruler.json)。W10 の段には結線しない(`w10_ruler.py` と同じ扱い)。W10 のヘッダの notes には入れない。
  - 作り方(**未リサーチ(expedient)**): ON の世界の対応表で、点の路線(No.61=`6:423:渋谷経堂線`・No.79=`4:317:環状六号線`)に当てた辺を集め、辺ごとに「その辺に当てた区間の諸元」で、距離 d=実測の車道端距離+区間の幅員/2 の LAeq を `laeq_at` で出す。舗装は騒音場と同じ密粒。**路線の辺が複数あるときは辺ごとの値の下側中央値**(親案)。OFF の値は同じ辺に klass 既定を当てて並べた(OFF の騒音場がその辺に当てる値)。klass 既定表は `run()` と同じ作り方で作り直し、ヘッダの `census_defaults` と一致することを道具の中で確かめた。

    | 点 | 辺 | 実測 昼/夜 | ON の残差 昼/夜 | OFF の残差 昼/夜 | 較正の残差 昼/夜(ヘッダ) |
    |---|---|---|---|---|---|
    | No.61 渋谷経堂線 | secondary 8 | 64/60 | **+5.1/+4.5** | +6.6/+6.6 | +5.1/+4.5 |
    | No.79 環状六号線 | primary 33 | 67/66 | **+6.0/+3.8** | +5.9/+3.8 | +1.0/−1.2 |

  - **循環である**: ON の辺に当てる値は較正 `calibrate()` と同じ `median_section`(路線名で引いたセンサスの区間の中央値)なので、ON の残差は較正の残差と**同じ計算**になる。No.61 は較正と一致した(+5.1/+4.5)。No.79 の差(+6.0 と +1.0)は舗装だけ(較正は点の CSV の低騒音舗装欄=排水性・ここは騒音場と同じ密粒)。路線の辺はどれも同じ値なので、中央値の規則はここでは効いていない(範囲が 1 点)。**現実との照合にはならない**。意味があるのは OFF との差だけ(No.61 で −1.5/−2.1 dB・No.79 で +0.1/0.0 dB)。
  - **現実との照合**は、較正に使っていない別の測定点で行う(リサーチ F6・10e の外)。
- **エンジンの動いた量**(19 構成・B3 の後と比べた・[b4_vs_b3.json](b4_vs_b3.json)): **19/19 構成で final が動いた**(騒音段階は B4 の文面とハッシュに入る・場所の起床が動く)。呼数の合計 1,265,034 → 1,267,129(+2,095)。既定 v3 70,500 → 70,501・v3 活動層 off 58,900 → 58,958・v1 既定 61,918 → 60,591。古典(v3_classical)は呼数・行動の件数・食事・気づきが同じで final だけ動いた。構成ごとの表は §B6-4。
- **張り替えた試験**(W10 の既定が ON+Q7 になったため・値は第 2 波の記録と同じ):
  - `tests/build_field/test_w10_road_names.py`: `test_w10_declares_the_switch_and_the_input`(既定 True/True/False・版 1.2.0)・`test_w10_road_name_match_on_real_data`(段 1c の規則=Q7 を False と明示)・`test_w10_default_off_…` → `test_w10_off_noise_field_equals_the_pre_1c_asset`(OFF を明示)。
  - `tests/build_field/test_w10_ruler.py`: `test_switch_off_reproduces_the_promoted_w10_outputs` を 2 本に分けた=`test_default_on_q7_reproduces_the_promoted_w10_outputs`(既定=昇格版の manifest と一致+ON+Q7 の先頭 12 桁)と `test_switch_off_reproduces_the_pre_10e_w10_outputs`(OFF=退避先の先頭 12 桁)。`test_ruler_values_on_the_promoted_field` → `test_ruler_values_on_the_off_field`(OFF の騒音場を一時ディレクトリに作って測る・値は同じ)。
  - `tests/build_field/test_field_pipeline.py`: 既知の落ちるゲートから `("W10", "primary_secondary_sections_matched")` を外した(202/202 で PASS)。
- 段の後の出力: `data/world/v2_10e_steps/B4/`(W10 の 6 本とヘッダ・W18〜W20 のヘッダと出力・受入パック・manifest=17 ファイル+`MANIFEST.sha256`)。

## B5 W13 の年間化(◎ のはず → 挙動は ◎・final は動いた・再構築 3 回目)

### B5-1 取得の記録(気象庁 etrn・`data.jma.go.jp` だけ)

- **頁**: 東京(`prec_no=44`・`block_no=47662`)の 10 分値 `https://www.data.jma.go.jp/stats/etrn/view/10min_s1.php?prec_no=44&block_no=47662&year={y}&month={m}&day={d}&view=p1` と時別値 `…/hourly_s1.php?…`(同じ引数)。窓 **2025-09-01〜2026-08-31**。
- **取った数**: 10 分値 **365 頁**(2026-10-12 07:52〜08:04 UTC・25,865,592 B)・時別値 **330 頁**(08:04〜08:15 UTC・7,561,109 B)。時別値の 2026-07-28〜08-31 の 35 頁は前回(2026-09-08・親)の頁をそのまま使った(取り直していない)。**2 秒に 1 回**。転送(3xx)は追わない作りにした(`tools/realworld_fetch/jma_etrn.py` の `_NoRedirect`)=**転送も失敗も 0 件**(695 頁すべて 200・`www.data.jma.go.jp` のまま)。
- **置き場と md5**: 頁 `data/realworld/jma_etrn/raw10min/tokyo47662_10min_<日付>.html`・`data/realworld/jma_etrn/raw/tokyo47662_<日付>.html`(前回と同じ名前)。**頁ごとの md5・バイト数・取得時刻・URL** は `data/realworld/jma_etrn/MANIFEST_10min.tsv`(365 行)と `MANIFEST_hourly.tsv`(330 行)。表にした CSV は `tokyo47662_10min_2025-09-01_2026-08-31.csv`(52,560 行・md5 `f015172cdc346e32f12d0ac4fba38a5f`)と `tokyo47662_hourly_2025-09-01_2026-08-31.csv`(8,760 行・md5 `19f21ed8da90da6b07e78c4c1e60d7bc`)。ライセンス台帳の行は親が足す。
- **規約と robots の要点**(読むだけ): `www.data.jma.go.jp/robots.txt` は **404(置かれていない)**。気象庁ホームページの利用規約(`www.jma.go.jp/jma/kishou/info/coment.html`・WebFetch で読んだ・保存していない)は「公共データ利用規約(第 1.0 版)」に準拠=出典の記載が要る(「出典:気象庁ホームページ(当該ページの URL)」)・編集や加工をしたらその旨を書く・国が作ったように見せない。数値データ固有の定めは無く、気象業務法 17 条(予報業務の許可)・23 条(警報の制限)の注意がある。機械による取得・頻度・負荷についての記載は無い。
- **読み方の検算**: 道具の時別値の読み方で前回の 35 日の頁を読み直すと、前回の CSV と改行を除いて 1 文字も違わなかった。

### B5-2 35 日の検算(etrn の 10 分値 × アメダスの JSON)

- [w13_amedas_crosscheck.py](w13_amedas_crosscheck.py)・[b5_w13_amedas_crosscheck.json](b5_w13_amedas_crosscheck.json)。アメダスの JSON 35 本の 3,219 記録(10 分ごと)を etrn の同じ時刻の行と比べた。
- **気温・相対湿度・平均風速・10 分間降水量は 3,219/3,219 一致**。日照は 1,865 一致・1,354 不一致で、**不一致は全部「etrn が空欄・アメダスが 0」**(夜)。etrn の日照の空欄は 1 年ぶんで 25,620 行あり、日の出から日の入りの間には 1 行も無い(夜だけ)。そこで 10 分値の日照の空欄は 0 分として畳む(アメダスの慣行と同じ・expedient として宣言)。これで 3,219 記録はすべて同じ値になる。
- アメダスの JSON は 35 日で 3,219 記録しか無い(35 × 144=5,040 のうち)。足りない時間は、これまで etrn の時別値(正時の値)で補っていた(301 時間)。

### B5-3 変えたこと

- `build/field/w13_weather.py`(`STAGE_VERSION` 1.0.0 → **1.1.0**): 窓 `WINDOW=("2025-09-01","2026-08-31")` を定数で持ち、入力は窓の名前の CSV 2 本と祝日の CSV だけ(`INPUT_FILES`)。`rglob` をやめた(`data/realworld/amedas` も `data/realworld_live` も読まない)。**主=etrn の 10 分値**(時の分け方はアメダスの JSON と同じ「観測の時刻の時」・頁の `24:00` は翌日の 0 時台・窓の外へ出る 2026-08-31 24:00 の 1 行は捨てる・窓の最初の日の 0 時台は 5 本)。**時別値は欠けの補完**(時ごと・値ごと。この窓では補完 0 時間=10 分値に欠けた時が無い)。祝日は内閣府の CSV(`build/field/common.py` の `read_holidays_csv`・CSV の範囲が窓の終わりに届かなければ止める)。季節は列に足さない(エンジンの契約)。notes に「季節 × 平日/土休 × 天候型」の日数の表(`season_weekday_type_counts`)・足りない組(`season_weekday_type_missing`)・入力の sha256 の先頭(`input_files`)。
- **ゲートの作り直し**: 日数のゲートは窓の日数(365)。「先頭の日の出 < 末尾の日の出」は年間の窓で意味を失う(9/1 と 8/31 はほぼ同じ)ので、物理の検算 3 つに替えた=日の出の最も早い日が 6 月(2026-06)・最も遅い日が 1 月(2026-01)・昼の最も長い日が夏至の ±3 日(2026-06-23)。報告だけのゲート `every_season_has_each_weekday_type`(値=足りない組の数)。
- `build/audit/w19_freeze.py`: W13 の資産は `w13_weather.INPUT_FILES` だけを載せる(旧はアメダスの 35 本を rglob)。資産表は 99 → **66 行**(アメダスの JSON 35 本と旧の時別値 CSV が外れ、CSV 2 本と祝日 CSV が入った)。`realworld_live` は 0 件。
- `build/vis/w9_shadow.py`: 影を作る日を定数 `SHADOW_DATES`(B5 では `("2026-07-28",)`)にした(旧は W13 の先頭の日=窓を変えると黙って 2025-09-01 の影になった)。先頭を「主の日」とし、面の表 `w9_shadow_planes.parquet` と notes の `replay_date` は主の日の値(ほかの日は notes の `per_date`)。**古い出力の規則**: エンジンは `w9_shadow_*.npy` を glob するので、W9 は `out` にある影のファイルのうち一覧に無い日を消す(残すと前の構築の日が黙って影ありの日になる)。消したことはヘッダに書かない(再構築のバイト一致のため・docstring に書いた)。
- `build/audit/w20_acceptance_pack.py`: 正午の影の図は W9 の主の日を描く(影の日が増えても図が変わらないように)。
- 試験: `test_field_units.py`(`weekday_kind` に祝日の表を渡す形・窓と入力の定数・季節の表がエンジンの `engine.calendar.SEASON_OF_MONTH` と一致・10 分値の畳み方・祝日 CSV の読み方)・`test_field_pipeline.py::test_w13_weather`(365 日・季節の表の合計 365・物理のゲート)・`test_audit_units.py::test_w19_assets_are_only_the_files_w13_reads`(`realworld_live` と `realworld/amedas` が data 根に在っても資産表に載らない)・`test_vis_pipeline.py::test_w9_shadow_planes`(影の日=定数・ディスクの影のファイル=一覧)。

### B5-4 不変の確認と動いた量

- **再構築 ×2**: 116 ファイル一致。B4 の後と比べて動いたのは 12 ファイル: W13 の 2 本とヘッダ・W9 のヘッダ(params・notes・input_hash)・W18〜W20 のヘッダ・`wc_index.json`・`w19_freeze.json`・受入パックの表 2 本・manifest。**W9 の影 `w9_shadow_2026-07-28.npy` `ad8b6c0e2579a7f8` と面の表 `0d3680f94546d207` は不変**。W12・W10・W16・W17 ほかも不変。
- **W18 の被覆の表**: 「天候・気温」の行の `n_sim` 35 → 365。カタログの現実の数 `n_real` は 35(カタログの欄「アメダス35日」)のままなので、**過剰の指標 X(`wc5_world_commission_X`)が 0.004056 → 0.184787**(報告だけのゲート)。カタログの欄の直しは凍結カタログの改訂になる=本発注の範囲の外(親に)。
- **W13 の 07-28 の行は今と同じにはならない**([w13_rows_diff.py](w13_rows_diff.py)・[b5_w13_rows_diff.json](b5_w13_rows_diff.json)): 旧の 840 行のうち、アメダスが出どころの 539 行は **535 行が全列同じ**(違う 4 行=07-29 10 時・08-04 12 時・08-04 15 時・08-05 13 時は、アメダスの JSON が 1 時間に 2〜3 本しか無かった時。etrn は 6 本そろう)。etrn の時別値が出どころだった 301 行は全部動く(正時の値 → 10 分値の平均)。**07-28 は 0〜8 時の 9 行が動く**(気温・湿度・風速・日照(空欄 → 0)・WBGT。例 0 時の WBGT 21.27 → 21.23・2 時の降水 2.0 → 1.5 mm)。天気の語・日照の語・暑さの段・天候型・層は 07-28 の全 24 行で同じ。日の表は 35 日とも天候型・層・曜日の種別・祝日・日の出と日の入りが同じで、日最高・日最低気温・日照の合計・WBGT の最大が動いた。
- **エンジンの動いた量**(19 構成・B4 の後と比べた・[b5_vs_b4.json](b5_vs_b4.json)): **呼数・行動の件数・食事・気づき・blocks・テープの全列は 19/19 構成で同じ**。**final は 19/19 で動いた**。外部の状態の行で**大きさが変わったのは O56 だけ**(`runner.environment._row`=天気の表の中の再生日の行番号。再生日は 07-28 のままで、表が 35 日 → 365 日になり行番号が 0 → 330 に変わった=外部のバイト 595 → 597)。ほかの行の中身が動いたかは、行ごとのハッシュが byte-check の記録に無いので**確かめていない**(推測: O76 の WBGT の今の値は日の終わりの 23 時台の値=アメダスと同じなので同じ)。**親の判定の材料**: 挙動は ◎(呼数・行動・テープが同じ)、final は ▲(行番号)。
- **季節 × 平日/土休 × 天候型の日数**(W13 の notes `season_weekday_type_counts`・365 日):

  | 季節 | 平日 晴/曇/雨/猛暑 | 土休 晴/曇/雨/猛暑 |
  |---|---|---|
  | 春(3〜5 月) | 27 / 9 / 24 / **0** | 20 / 5 / 7 / 0 |
  | 夏(6〜8 月) | 19 / 14 / 27 / 4 | 6 / 4 / 15 / 3 |
  | 秋(9〜11 月) | 22 / 18 / 17 / 3 | 11 / 9 / 11 / 0 |
  | 冬(12〜2 月) | 41 / 12 / 8 / **0** | 21 / 2 / 6 / 0 |

  **報告だけのゲート**: 平日の各天候型が 1 日以上ある季節は夏と秋だけ。春と冬の平日に猛暑の日が無い(日最高 35 ℃ 以上=気象庁の定義・春と冬に無いのは物理として自然)。足りない組は `春|平日|猛暑`・`冬|平日|猛暑` の 2 つ。合計 平日 245・土休 120(祝日 18 日を含む)・晴 167・曇 73・雨 115・猛暑 10。
- 段の後の出力: `data/world/v2_10e_steps/B5/`(W13 の 2 本とヘッダ・W9 の影と面の表とヘッダ・W18〜W20・受入パック・manifest=14 ファイル+`MANIFEST.sha256`)。

## B6 構築側(影の日付・W7 の祝日)(W7 は ◎=ランは不変・影 5 日は既定のランを動かすので既定にする前で止めた・再構築 4〜5 回目)

### B6-1 変えたこと

- `build/vis/w9_shadow.py`: 発注どおり `SHADOW_DATES` を **2026-07-28(先頭=主の日・旧値の再現用)+ 2026-07-13〜07-17 の 5 日**にして影を作り(1 日 約 1 秒=W9 段 5.75 秒・1 日 12,842,624 B・容量のゲート 10 MB/日は FAIL のまま=今と同じ)、測った(§B6-3)。**既定のランが動くと分かったので、最後のコードでは `SHADOW_DATES` を `("2026-07-28",)` に戻した**(5 日を足すのは 1 行・注に書いた)。作った影 5 本は `data/world/v2_10e_steps/B6/` にある。一覧に無い日の影を消す規則は `remove_stale_shadows()` に分けて試験を足した(`test_vis_units.py::test_remove_stale_shadows_keeps_only_the_listed_days`)。
- `build/field/w7_planspec.py`(`STAGE_VERSION` 1.0.0 → **1.1.0**): OSM の `opening_hours` の **PH(祝日)の規則**を捨てずに読む `parse_holiday_hours()`。祝日の 1 日ぶんの区間を**新しい列 `holiday_content`**(最後の列・`[[開,閉],…]` の JSON・PH の規則が無い POI は空文字・`PH off` は `[]`)に入れ、法規上限の窓で週表と同じように切る。**週表 `content` は変えない**(エンジン=`poi_id`・`kind`・`content` だけを読む・W14=`content` が 7 日でないと止まる・W17 の構築=7 日でない行を捨てる、の 3 つを壊さないため)。入力に内閣府の CSV を足し(W19 の資産表に載る)、CSV の範囲を notes に書く。どの日が祝日かは内閣府の CSV(エンジンの暦の口)で決まり、PH の規則の無い POI の祝日はエンジンの宣言(親案=土休扱い)に従う。
  - **解釈(親に確かめてほしい)**: 発注の「W7 の `PH`(祝日)の行を内閣府の CSV で拾い直す」を「OSM の PH の規則を祝日の行(列)として拾い、祝日の日付は CSV で引く」と読んだ。W7 自身は祝日の日付を使っていない(週の表なので日付に依らない)。
- 試験: `test_field_units.py::test_parse_holiday_hours`(`Su,PH`・`PH off`・`Mo-Su,PH`・PH なし・`24/7`・2 区間・週表は不変・入力に CSV)・`test_field_pipeline.py::test_w7_plan_spec`(`holiday_content` が 2,337 行・ゲートの値と一致)。

### B6-2 再構築と動いた量(資産)

- **影 6 日の版の再構築 ×2**: 121 ファイル(影 5 本が増えた)の sha256 が全部一致。B5 の後と比べて動いたのは 16 ファイル: `w7_plan_spec.parquet` `e904d8e64a6d69ba` → **`7a6014e0cc84203e`**(列が 1 本増えただけ=ほかの 18 列は全行同じことを確かめた)・W7 のヘッダ・**影 5 本**(`w9_shadow_2026-07-13.npy` `8200c6dbe83baa3d` ほか=§B6 の段の `MANIFEST.sha256`)・W9 のヘッダ・W14 のヘッダ(`input_hash` だけ=W7 の parquet が入力のため。W14 の出力は不変)・W18〜W20 のヘッダ・`w19_freeze.json`・受入パックの表 2 本・manifest。**07-28 の影 `ad8b6c0e2579a7f8` と面の表 `0d3680f94546d207` は不変**。
- PH の規則を持つ POI は **40**(うち `PH off` 1)。法規上限で切られた祝日の区間は 0。
- **最後の版(影は 07-28 だけ)の再構築 ×2**: 116 ファイル一致(W9 が影 5 本を消した)。B5 の後と比べて動いたのは 10 ファイル(W7 の parquet とヘッダ・W14 のヘッダ・W18〜W20 のヘッダ・`w19_freeze.json`・受入パックの表 2 本・manifest)。**エンジンは 19/19 構成で全欄が B5 の後と同じ**([b6build_final_vs_b5.json](b6build_final_vs_b5.json)・`sides/final.json`)=W7 の新しい列はランに効かない。`build_hash` `89fd7376a70d004c…`(影 6 日の版は `5ff1bacf7fd9c773…`)。

### B6-3 影を 6 日にすると既定のランは不変ではない(発注の見込みと違う=既定にする前で止めた)

- 影 6 日の世界で 19 構成を回すと、**19/19 構成で再生日が 2026-07-28 → 2026-07-14 に動いた**(世界の日付 `start_sim_datetime` も 07-14)。呼数の合計 1,267,129 → **1,330,624(+63,495)**。既定 v3 70,501 → 73,039・v3 活動層 off 58,958 → 62,852・v1 既定 60,591 → 65,103([b6shadow6_vs_b5.json](b6shadow6_vs_b5.json)・`sides/b6_shadow6.json`)。
- **原因**: エンジンの天気の再生日の選び方(`engine/processes/environment.py` の `_pick_day`・`prefer_shadow_days`)が「**影のある日を引ける層に絞る**」expedient を持つ(材料 §4-2 の (ii))。影が 07-28(平日|雨)だけのときは平日の天候型が雨に絞られて 07-28 しか引けなかったが、影が 07-13(雨)・07-14(晴)・07-15(晴)・07-16(曇)・07-17(雨)に増えたので、平日の天候型の候補が {雨・晴・曇} に広がり、seed 1 では「晴」→ 07-14 を引いた。
- **W7 の列は効いていない**ことを確かめた: 影 5 本だけを一時的に世界から外して既定 v3 と古典の 2 構成を回すと、final(behavior・full とも)と呼数が B5 の後と一致した(W7 の新しい列はエンジンが読まない)。
- **止めた理由**: 発注の「資産が増えるだけで、既定のラン(07-28)は不変」はエンジンの `prefer_shadow_days` があるので成り立たない。既定のランを動かす変更は共通の約束(範囲を超える変更の前で止める)に当たるので、影 5 日を既定にするのは親の判断に回した。影を暦の日付で引く(答え 1-3)エンジン側 B6 が入れば、この絞り込みは外れる見込み(推測)。
- 段の後の出力: `data/world/v2_10e_steps/B6/`=**影 6 日の版**(影 6 本と面の表・W7・W9・W14・W18〜W20・受入パック・manifest=18 ファイル+`MANIFEST.sha256`)。最後の版(影 07-28 だけ)の資産は作業木の `data/world/v2` そのもの(§B7)。

### B6-4 段ごとの final と呼数(19 構成・5,000 体・seed 1・1 シミュ日・既定の引数)

side の全体は `sides/base.json`・`sides/b3.json`・`sides/b4.json`・`sides/b5.json`・`sides/final.json`・`sides/b6_shadow6.json`(`base`=B の前の私有の写し=E5 の side と全欄一致・`final`=最後の版=B5 と全欄一致)。

| 構成 | 前(=E5) final・呼数 | B3 | B4 | B5(=最後の版) | B6 影 6 日の版(既定にしていない) |
|---|---|---|---|---|---|
| w6_v3_default | `4fbf61616af1` 70,421 | `e1bf096f58bc` 70,500 | `54ba78d0bdf6` 70,501 | `0483d1165e24` 70,501 | `4fb81d6171c0` 73,039 |
| w6_v3_activity_off | `6ef311ea2bca` 58,495 | `fa332cbf1b69` 58,900 | `48746516b74a` 58,958 | `125f16335476` 58,958 | `944bb3098287` 62,852 |
| w6_v1_default | `9180ff01f380` 60,899 | `dfce0df1fef1` 61,918 | `2332c2a0494b` 60,591 | `9f6cfcf54cd8` 60,591 | `39f81c57cfe9` 65,103 |
| w6_v1_derive_v2_1 | `d69cc0795cb2` 54,491 | `594ae8f623d6` 54,510 | `726bdb1c5279` 55,424 | `fa483a24c61e` 55,424 | `4a1b930d15d2` 58,914 |
| w6_v2 | `88dc42eabbc8` 60,758 | `d2c9512e7ff4` 59,405 | `8561a179544b` 60,579 | `40dab07ad9c3` 60,579 | `99e9557389b6` 64,130 |
| w6_v1_edge | `abd6801c4e3c` 54,313 | `b12661407798` 54,239 | `acd67c6ded32` 54,302 | `582d7f934096` 54,302 | `098f9d1f64ab` 57,820 |
| w6_v2_edge | `00c7b8d57be2` 54,326 | `857e3f8b176e` 54,453 | `192dd1ca1408` 54,348 | `f55b97e6cae9` 54,348 | `2cc4b6462389` 57,883 |
| w6_v1_edge_plateau | `a289e41bf738` 55,505 | `ff4ae9791a12` 55,987 | `8a69a1dc66bb` 56,038 | `3c8cd47b8cd7` 56,038 | `640bdd9bd4de` 59,866 |
| w6_old_v1_default | `fb7b4b4755eb` 60,899 | `66b77fc56361` 61,918 | `e0bda39963bc` 60,591 | `8c6bd89ef728` 60,591 | `b7ca9a494b81` 65,103 |
| w6_old_v1_derive_v2_1 | `ef68f7510655` 54,491 | `b6db72a0207f` 54,510 | `a37781b7970c` 55,424 | `ebced6f597ac` 55,424 | `710217d23a33` 58,914 |
| w6_old_v2 | `4eacbf3c1a14` 60,758 | `1acf942d8f1c` 59,405 | `6b2ea0a13907` 60,579 | `8072feee6c51` 60,579 | `75c31b229a09` 64,130 |
| w6_old_v1_edge | `2722cf8449b9` 54,313 | `2356b0ae0991` 54,239 | `9de90c2edee2` 54,302 | `8465cffa5f83` 54,302 | `20fdd8bb886f` 57,820 |
| w6_old_v2_edge | `14aff5b3c963` 54,326 | `c8427e46c5b8` 54,453 | `9e7e05eb85ec` 54,348 | `8e52736a2422` 54,348 | `452e89af78c8` 57,883 |
| w6_old_v1_edge_plateau | `79149e728b5e` 55,505 | `191cdf645f77` 55,987 | `77f12806589c` 56,038 | `a0a319c992a2` 56,038 | `361a0e813b11` 59,866 |
| w6_golden_null_arm | `6c81c5ad8a99` 101,969 | `91439d0c2276` 101,278 | `3fc1395865db` 101,773 | `aaaa89d936f1` 101,773 | `6f55e3638514` 104,740 |
| v3_mem_store | `785b26683ed4` 70,421 | `e805142cefe5` 70,500 | `d331a4bf51d2` 70,501 | `a16b260e4f8b` 70,501 | `cace303dc995` 73,039 |
| v3_mem_rel | `64f48b6571ec` 74,616 | `4f4ba4a07a96` 74,055 | `33775324bae3` 74,056 | `25b5ce1304f6` 74,056 | `cc2cd858bfe4` 76,671 |
| v3_classical | `1470f952565a` 96,961 | `aa18b0055065` 97,766 | `f29552bb8057` 97,766 | `a514cf85402d` 97,766 | `5f76ab03e79a` 100,236 |
| v3_classical_mem_rel | `e9a4fa4d2403` 111,194 | `29737492000a` 111,011 | `82678093dfbd` 111,010 | `f6f5ec7b706b` 111,010 | `3e4a57ce6299` 112,615 |
| 呼数の合計 | 1,264,661 | 1,265,034 | 1,267,129 | 1,267,129 | 1,330,624 |

- 影 6 日の版の `v3_mem_store` は 6 本同時の回で numpy の確保に失敗した(`_ArrayMemoryError` 4.88 MiB=同じ機械でエンジン側の実行役の byte-check も回っていたためのメモリの圧迫)ので、1 本で回し直して差し替えた(`sides/b6_shadow6.json` の `note_rerun`)。

## B7 取り込みの手順(親へ)

1. **本体の改行の直し(先に)**: 本体の作業コピーの `docs/bench/pt_shibuya/pt6_summary_core0241.json` は CRLF(§B0)。作業木の世界はこの LF の写しで作ったので、W12・W16 のヘッダの `input_hash` が本体の今の資産と違う。取り込む前に本体のこのファイルを git の中身(LF)に揃える(`.gitattributes` の作業=親の予定と同じ)。揃えないまま本体で再構築すると、W12・W16 以降のヘッダが作業木の値とずれる。
2. **段ごとに写す場合**: `data/world/v2_10e_steps/<段>/` の `MANIFEST.sha256` に載ったファイルを本体の `data/world/v2/` へ写す(B3 → B4 → B5 → B6final の順・各段のファイルは前の段からの差分+指定のヘッダ)。`B6final`=最後の版(W7 の PH・影は 07-28 だけ)。`B6`=影 6 日の版(既定にしていない・写すなら親の判断の後)。B の前の差分(W12・W16 のヘッダの `input_hash`)は `v2_10e_steps/base/` のヘッダ一式にある。
3. **最後の状態だけを写す場合**(作業木の私有の写しと本体の今の資産の差=25 ファイル): ヘッダ `W7`・`W9`・`W10`・`W12`・`W13`・`W14`・`W16`・`W18`・`W19`・`W20`/出力 `w7_plan_spec.parquet`・`w10_edge_section.parquet`・`w10_noise_day.npy`・`w10_noise_night.npy`・`w10_noise_stage_day.npy`・`w10_noise_stage_night.npy`・`w12_timetables.parquet`・`w13_weather_days.parquet`・`w13_weather_hourly.parquet`・`w19_freeze.json`・`wc_index.json`・`build_manifest.json`・`acceptance/gate_table.md`・`acceptance/noise_day.png`・`acceptance/summary.json`。写した後に本体で `python -m shibuya.build.run --out data/world/v2 --data data --keep-stage W17` を回し、`build_manifest.json` の `build_hash` が作業木の **`89fd7376a70d004c…`**(ファイルの sha256 は `2f9ce268ead0e9e0…`)と一致することを確かめる(1. の改行を揃えた後)。
4. **B6 の影 5 本は既定のランを動かす**(§B6-3)ので最後の版に入れていない。エンジン側の B6(影を暦の日付で引く)と一緒に入れるなら、`SHADOW_DATES` に 5 日を並べて再構築する(または `v2_10e_steps/B6/` の影 5 本と W9 のヘッダを写す)。
5. **取得したデータ**(`data/realworld/jma_etrn/`・本体への junction の先=すでに本体にある): `raw10min/` 365 本・`raw/` に 330 本を足した・`MANIFEST_10min.tsv`・`MANIFEST_hourly.tsv`・CSV 2 本。ライセンス台帳に行を足す(§B5-1)。

## B8 試験と張り替えた golden

### B8-1 足した・直した試験(構築側)

- `tests/build_field/test_w12_pm_peak_switch.py`(新・4 件・B2)・`test_field_units.py`(18/19/24/27 本/時・W13 の窓と入力・季節の表とエンジンの一致・10 分値の畳み方・祝日 CSV・PH の規則)・`test_field_pipeline.py`(W10 の既知の落ちるゲート・W13 の 365 日と物理のゲート・W7 の `holiday_content`)・`test_w10_road_names.py`・`test_w10_ruler.py`(§B4)・`tests/build_audit/test_audit_units.py`(W19 の資産表=W13 が読むファイルだけ・`realworld_live` を載せない)・`tests/build_vis/test_vis_pipeline.py`(影の日=定数・ディスクの影=一覧)・`test_vis_units.py`(古い影を消す規則)。

### B8-2 張り替えた golden(既定の値だけ・世界の資産が動いたため)

| 試験 | 定数 | 前(E5) | 後(10e 構築側=B5 の後=最後の版) |
|---|---|---|---|
| `tests/engine/test_presence_executor.py` | `W17_GOLDEN["3113e9ba7abb"]["null_arm_final"]`・`null_arm_llm_calls` | `6c81c5ad8a99437a` / 101,969 | **`aaaa89d936f1674e` / 101,773** |
| 同 | `v3_default_final`・`v3_default_llm_calls` | `4fbf61616af1e3d2` / 70,421 | **`0483d1165e245bed` / 70,501** |
| `tests/engine/test_state_checks_10f.py` | `K19_V3_FINAL_COUNTER` | `4fbf61616af1e3d2` | **`0483d1165e245bed`** |
| `tests/engine/test_state_ledger_10b.py` | `T7_V3_FINAL` | `4fbf61616af1e3d2` | **`0483d1165e245bed`** |
| `tests/engine/test_classical_social.py` | `CLASSICAL_1500_GOLDEN_ACQ_BY_ENV` | `4c8a9e08…916c5` / 26,156 | **`e9ef51cc…6b8d07` / 26,043** |
| `tests/engine/test_relations_tenure.py` | `REL_ON_5000_GOLDEN[("v2","behavior")]` | `64f48b6571ec2ea1` / 74,616 | **`25b5ce1304f6db68` / 74,056** |
| `tests/c8/test_sensitivity_ledger.py` | `test_w13_and_w12_real_assets` の時の数 | 840 | **8,760**(B5) |
| 同 | `PRE_D44_DIGESTS["rows"]`(台帳の 19 行の digest) | `5a34eefd…` | **`e3483f9f…`**(B3 で S-W14-JRPHASE の `declared` を直したため) |

値はこの作業木のエンジンで同じ引数のランを回して取った(`sides/final.json` の同じ構成の値と一致: 既定 v3 `0483d1165e245bed` 70,501・golden の空の腕 `aaaa89d936f1` 101,773・関係 on `25b5ce1304f6` 74,056)。各定数の脇に〔改訂(第330)〕の注で前の値を残した。

### B8-3 張り替えなかった golden(旧い世界の資産で録った「旧値の再現」=エンジン側 B1 の切替口で再現する)

次の試験は、切替口(`hash_scheme="full"`・`rng_scheme="stateful"`・`hunger_model="v1"`・`leave_effect=False`・`l4_scale=1.0`・`poi_target="legacy"`・`near_tiebreak="id"` ほか)で**10e より前の値**を再現する試験で、値は 10e より前の世界の資産(W10 OFF・丸めの前の W12・35 日の W13)で録られている。構築側で資産が動いたので、エンジンの切替口だけでは再現できない。**旧資産を読む切替口(エンジン側 B1・置き場 `data/world/v2_pre_10e_2026-10-12/`・答え 1-5)を通せば再現できるはず**(推測)なので、張り替えず(弱めず)に残した=最後の版では落ちる:

- `test_presence_executor.py`: `test_l4_scale_1_reproduces_the_stage_2c_checkpoints`・`test_hunger_model_v1_reproduces_the_stage_3_checkpoints`・`test_leave_effect_off_reproduces_the_stage_5_checkpoints`・`test_hash_scheme_full_reproduces_the_pre_10e_checkpoints`(`*_stateful` の行を含む)
- `test_intent_chooser.py::test_poi_target_legacy_reproduces_the_pre_2a_checkpoints_q13`
- `tests/perception/test_near_tiebreak.py::test_classical_checkpoint_moves_with_hash_and_id_reproduces_the_old_one`
- `test_state_checks_10f.py::test_k19_runtime_default_v3_5000_known_counts`(既定の部分は通る・`stateful` の部分=E2 の値が落ちる)
- `test_classical_social.py::test_run_golden_and_arms`(既定の部分は通る・`*_PRE10E` が落ちる)
- `test_relations_tenure.py::test_relations_on_arm_golden_old_and_new`(既定の行は通る・`full` の 2 行が落ちる)

### B8-4 そのほかの落ちる試験

- `tests/c8/test_sensitivity_ledger.py::test_manifest_judgment_matches_the_live_manifest`: 感度の台帳の判定の表(`build_manifest_judgment`)は世界の manifest の expedient の全行を写したもの。構築側で **expedient が 6 行増え 4 行消えた**(増えた: W10 の交通の過程との食い違い・W13 の日照の空欄=0・W13 の補完の文言・W13 の窓の最初の日の 0 時台・W7 の PH・W9 の影の日の定数/消えた: W13 の旧い補完の文言・W13 の手書きの祝日・W7 の PH を無視・W9 の再生日=W13 の先頭)うえに `manifest_build_hash` も変わった。新しい行の 3 分類(triage)と D-44 の列は親の判断が要るので、台帳は作り直していない。
- `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`: E6-5 に書いた既知の落ち方(作業木の `data` が本体へのつなぎのため・テープの道筋が相対にならない)。構築側の変更とは関係しない。

### B8-5 全体テスト(最後に 1 回)

- **最後の版(作業木の data/world/v2=影 07-28 だけ・コードは snap_B6build と同じ)・6 組に分けて同時に回した**(`python -m pytest -q -p no:cacheprovider -o addopts="" -rfE <組のファイル>` を 6 本・ディレクトリごとに同じ組・壁時計 1,127 秒): **3,813 件を集めて 3,798 passed・13 failed・1 skipped・1 xfailed**。同じ機械でエンジン側の実行役のランも回っていた。
- 13 件のうち `test_env_and_sections_10f.py::test_golden_tables_are_keyed_by_platform_and_values_unchanged`(golden の表の値の見張り)は、B8-2 の張り替えに合わせて同じ値に直し、単独で通ることを確かめた(〔改訂(第330)〕の注)。
- 残る 12 件: B8-3 の **9 件**(旧値の再現=エンジン側 B1 待ち)・B8-4 の 2 件(感度の台帳の判定の表・テープの道筋)・`tests/engine/test_change_detect_p6.py::test_p6_change_detection_under_2ms_at_400k_agents`(400k 体の合成の時間の門 2 ms に 2.08〜2.65 ms。**HEAD のコード(本体の src・`7f18733`)でも同じ時刻に 2.36〜2.52 ms で落ちた**=機械の混み具合。エンジンのコードは触っていない。影 6 日の版の全体テスト(40 分前)では通っていた)。
- 影 6 日の版(§B6-3)でも全体を 1 回回した: 3,811 件・3,789 passed・**21 failed**。内訳=既定の golden だけの 3 件(帰無腕・v3 既定・T7)・既定と旧値の両方を持つ 3 件(K19・古典・関係 on)・旧値の再現だけの 6 件(`test_presence_executor.py` の 2c/3 段目/5 段目/10e 前・`test_intent_chooser.py`・`test_near_tiebreak.py`)・感度の台帳 4 件(W13 の時の数・判定の表・読み口のグラフ=影のファイルの一覧・digest)・影で再生日が動いて落ちた 3 件(`test_env_and_sections_10f.py` の seed の交換可能性 2 件・`test_presence_exit_walk.py` の 1 件=最後の版では通る)・W7 の試験の書き間違い 1 件(直した)・テープの道筋 1 件。


# 第330 ACT 版上げ 1 回目の活性化(既定の切り替え・影 6 日・W7 の形の整合・試験の直し)

> 実行役(Opus 5.5)の記録。親の検収の前・commit していない(親が snap_ACT → snap_RET の順に重ねて commit する)。発注: 第330 発注 H(親 Fable 5.1)。ユーザーの答え: [v2-answers-2026-10-12b.md](../../../../design/v2-answers-2026-10-12b.md) §1(1-3・1-4・1-5)。作業木 `10e/activation`(HEAD `a5eec83`)。
> **試験と byte-check の世界**: 作業木の `data` は本体へのつなぎで、本体の `data/world/v2` は書き換えない約束なので、ACT の資産(`data/world/v2` に下の影 5 本と W9・W18〜W20 のヘッダほか 13 ファイルを重ねたもの)で回す試験と byte-check は、作業用の写しの木で回した(コードは作業木と同じ・`data/world/v2` だけが ACT の資産の写し・ほかの `data` はつなぎ)。**親が本体へ写すまで、作業木そのものの全体テストは ACT の golden で落ちる**(§ACT-7)。

## ACT-1 変えたこと

| ファイル | 何を |
|---|---|
| `engine/calendar.py` | `CALENDAR_UNIFIED=True`(=`--calendar-weekday real`・`--weather-scheme calendar`・開始日を渡さないランの暦の 0 日目は 2026-07-13(月)+`day_index` 日)。docstring の既定の記述 |
| `build/vis/w9_shadow.py` | `SHADOW_DATES` = 2026-07-28(先頭=主の日・旧値の再現用)+ 2026-07-13〜07-17 の 5 日 |
| `world/assets.py` | W7 の PH の読みを構築側の列 `holiday_content` に直した(親の決定 (1))。`[]`=祝日は休み・空文字=規則なし=日曜の行・列の無い W7(1.1.0 より前・合成)は規則なし。週表 `content` は曜日 0〜6 の 7 要素だけ読む(前: 週の 8 つ目の要素=実行役の提案の形) |
| `engine/run.py` | `resolve_calendar_schemes`(親の決定 (5)=`rng_scheme` と同じ形): テープの脇の meta に `calendar_weekday`・`weather_scheme` を書き、再生では meta の値を既定にする。明示の値が違えば止める。記録の無いテープ(活性化より前の録画)は `day_index`・`legacy` とみなして `CalendarSchemeWarning` を 1 回。`run_day(calendar_weekday=None)`・CLI `--calendar-weekday` の既定 None(指紋には決めた値) |
| `engine/processes/environment.py` | `WEATHER_EXPEDIENTS`(層を広げる順・同じ近さの影は前の日)を manifest の `weather.expedients` に載せる(calendar のランだけ・親の決定 (3)) |
| `tools/c8/sensitivity.py`・`sensitivity_v1.json`・`expedient_triage_v1.json`・`docs/bench/c8/sensitivity_v1.*` | 感度の台帳の判定の表を ACT の build_manifest(`5ff1bacf…`・123 行)で作り直した(§ACT-5) |
| `docs/.../d44-controls-2026-09-30/d44_controls.py` | `c_w7_7` の祝日の判定を暦の口(内閣府 CSV=`engine.calendar.load_holidays`)に(W13 の `HOLIDAYS_2026` は B5 で消した)。D-44 は回し直していない(07-28 で同じ値=JSD 0 と 2.98e-06 を確かめた) |
| `tests/golden_env.py` | `PRE10E_ASSETS`・`PRE10E_RUN_KW`(`world_assets_pre10e`+`day_index`+`legacy`)・`needs_pre10e`(退避先が無ければ skip・理由つき)。**RET で消す** |
| 試験 | §ACT-6 |
| `docs/.../10e/two_day_check_act.py`(新) | 2 日のランの控えと検査 |

## ACT-2 W9 の影 6 日(ステージング)

- 作り方: `data/world/v2` の 1 階のファイルと `acceptance/` を作業用の場所に 2 つ写し、`SHADOW_DATES` を 6 日にした作業木のコードで `python -m shibuya.build.run --out <写し> --data data --keep-stage W17` を 2 回(各約 30 秒・終了コード 1=既知の 2 ゲート=W10 の較正 7.3・W9 の容量 12,842,624 B/日)。
- **2 回の 121 ファイルの sha256 が全部一致**。`build_hash` **`5ff1bacf7fd9c773…`**(構築役の §B6-2 の影 6 日の版と同じ値)。
- 今の `data/world/v2`(116 ファイル)と比べて **108 ファイルが同じ**(W0〜W17 の出力・W7 1.1.0 ほか=今の資産を作り直しで再現した)。動いたのは 13 ファイル: 影 5 本(追加)・W9・W18・W19・W20 のヘッダ・`w19_freeze.json`・受入パックの `gate_table.md`・`summary.json`・`build_manifest.json`。**07-28 の影 `ad8b6c0e2579a7f8` と面の表 `0d3680f94546d207` は不変**(先頭=主の日のまま)。
- ステージング: `data/world/v2_10e_steps/ACT/`(13 ファイル+`MANIFEST.sha256`=sha256・パス・added/moved)。影の sha(先頭 16 桁): 07-13 `8200c6dbe83baa3d`・07-14 `5f49667b17d0c3ab`・07-15 `98e0b40836193879`・07-16 `a3ba8f19b38cb32e`・07-17 `b561e2f7691f2340`(構築役の `v2_10e_steps/B6` と同じ値)。
- **親の取り込み**: `v2_10e_steps/ACT/MANIFEST.sha256` の 13 ファイルを `data/world/v2/` へ写す(影 5 本は追加・ほかは置き換え)。写した後の `build_manifest.json` の `build_hash` が `5ff1bacf7fd9c773…` になることを確かめる。

## ACT-3 W7 の PH(親の決定 (1))

- 世界資産: PH の規則を持つ店 **40**(うち休み `[]` 1)。祝日の行の営業の行列を parquet の列から直に作った値と一致(試験)。日曜の行と違う店は 1(休みの店・1,140 分)。
- 既定の開始日 07-13〜17 に祝日は無い(次の祝日は 07-20 海の日・08-11 山の日)=**既定のランでは W7 の PH は効かない**(動いた量の理由に入らない)。

## ACT-4 テープの meta(親の決定 (5))

- 録画: `run_meta.json` に `calendar_weekday`・`weather_scheme`(既定 `real`・`calendar`)。
- 再生: 未指定は meta の値。明示の値が違えば止める(文言に両方の値)。**記録の無い旧テープ(手元の版 1〜4・活性化より前の録画)は `day_index`・`legacy` とみなし警告 1 回で、録画と同じ final・テープの取りこぼし 0 で再生される**(試験 `test_activation_10e.py`=世界資産 60 体・480 tick で `day_index`+`legacy` で録って meta の 2 欄を消したテープ)。合成世界では暦の規則で値が動かないので、世界資産で確かめた。

## ACT-5 感度の台帳の判定の表(§B8-4・親の決定)

- 構築側で build_manifest の expedient が **121 → 123 行**(+6・−4)。`--judge-manifest → --read-graph → --triage → --d44` で作り直した(ACT の manifest)。**同じ文言の行は、鍵が `W13#6 → W13#5` に変わった 1 行のほか全欄が前と同じ**(突き合わせた)。
- 増えた・文言の変わった行の 3 分類は実装役の案(未リサーチ)=`W7#7` i・`W9#5` i・`W10#11` ii・`W13#6` i・`W13#7` i・`W13#8` iii(窓の境界の宣言=対照を定義できない)。表の注に前の行の値を残した。
- D-44 の列: 6 つ目の値 **`pending`(未判定・D-44 の後に増えた行)** を足した(`sensitivity.D44_PENDING`=増えた・文言の変わった 6 行。(iii) の `W13#8` は今までの規則どおり `no_control`)。番号のずれた `W13#5` は D-44 の結果を前の鍵 `W13#6` から引く(`D44_KEY_REMAP`)。同じ鍵の古い結果(別の文言の行のもの)を当てない。
- 集計: 判定不能 105 → **107**・読む 96 → **98**・3 分類 i 66 / ii 13 → 14 / iii 17 → 18・D-44 駆動しえない 39 → 38・ラン対照へ 27 → 25・測れない 13 → 12・対照を定義できない 17 → 18・対象外 9・**未判定 5**。
- 試験の張り替え(`tests/c8/test_sensitivity_ledger.py`): 121 → 123・105 → 107・96 → 98・分類の数・digest 3 つ(`build_manifest_expedients` `036a4bd1…` → `309a443e…`・`judgment_rows_without_d44` `541acb8c…` → `ffc43608…`・`judgment_rest_without_d44` `eb70c08c…` → `1fc90c5f…`)。新しい試験 1 件(番号のずれと未判定の行)。

## ACT-6 試験の直し

**落ちる 29+12 件の行き先**(§第330-E3・§B8-3・§B8-4 の一覧):

| 一覧 | 件数 | 直し方 |
|---|---|---|
| A. final・呼数の golden | 12 | 既定の値は**張り替え**(下の表)。旧値の再現(段 2c・3 段目・5 段目・`full`・Q13・近接の同点・K19 の stateful・古典の `_PRE10E`・関係の full)は `GE.PRE10E_RUN_KW`(退避先の資産+`day_index`+`legacy`)を渡して**旧値のまま通る**(張り替えない・退避先が無い環境は skip) |
| B. 今の既定の約束を書いた試験 | 14 | 切り替えの試験・CLI の既定・`SimCalendar` の既定・manifest の開始日は新しい既定に直した(前の値は注)。`day_index` を鍵にする規則の確かめ(`day_index≠0` の 2 件・10a の 3 件・学校の休み)は `day_index`・`legacy` を明示。seed の交換可能性の 2 件は直さずに通った(W13 の年間化で 07-13 が窓の中=推測どおり) |
| C. 写しの木と環境 | 3 | §ACT-7 |
| §B8-3 の旧値の再現 | 9 | 上の A と同じ(9 件とも通る) |
| §B8-4 | 2 | 感度の台帳=§ACT-5。テープの道筋=環境(§ACT-7) |
| P6 の時間の門 | 1 | 環境(§ACT-7) |

ほかに活性化で落ちた試験(一覧の外): `test_weather_calendar_10e.py` の 2 件(B6 のエンジン側の試験は 35 日の W13・影 07-28 だけで書かれていた=07-13 が窓の外の前提。既知の答えは「legacy の再生日に暦を合わせる」形に、B3 の語の試験は「既定=実際の天気(警告なし)+揺らしたランで再生日と暦を分ける」形に直した)・`test_salt_seed_split_10f.py::test_population_and_motion_streams_use_their_own_seed_world` 3 件(calendar で窓の中の日は気象の層を引かない=環境の流れを引かせるため `weather_perturb=True`)・`test_10a_review_fixes.py` のテープの meta の形 2 件(2 欄を足した)。

**張り替えた golden(既定の値・前 → 後)**:

| 試験 | 定数 | 前(B6build) | 後(ACT) |
|---|---|---|---|
| `test_presence_executor.py` | `null_arm_final`・`null_arm_llm_calls` | `aaaa89d936f1674e` / 101,773 | **`354f49ca9a61b986` / 97,234** |
| 同 | `v3_default_final`・`v3_default_llm_calls` | `0483d1165e245bed` / 70,501 | **`5f7ae9ff24005314` / 65,597** |
| `test_state_checks_10f.py` | `K19_V3_FINAL_COUNTER` | `0483d1165e245bed` | **`5f7ae9ff24005314`** |
| `test_state_ledger_10b.py` | `T7_V3_FINAL` | `0483d1165e245bed` | **`5f7ae9ff24005314`** |
| `test_classical_social.py` | `CLASSICAL_1500_GOLDEN_ACQ` | `e9ef51cc…6b8d07` / 26,043 | **`78399f8c…e48b41` / 25,082** |
| `test_relations_tenure.py` | `REL_ON_5000_GOLDEN[("v2","behavior")]` | `25b5ce1304f6db68` / 74,056 | **`73a78288ab5e1498` / 69,111** |
| `test_env_and_sections_10f.py` | golden の表の見張り(上の 3 行の写し) | 同上 | 同上 |
| `test_sim_time_T.py` | 開始日・暦の欄(2 か所) | `2026-07-28`・`day_index` | **`2026-07-13`・`real`** |
| `tests/c8/test_sensitivity_ledger.py` | 行数・分類・digest 3 | §ACT-5 | §ACT-5 |

値は byte-check の ACT の side(`sides/act.json`)の同じ構成と一致(古典 1,500 体は同じ写しの木で 1 本回した)。

## ACT-7 動いた量(19 構成・5,000 体・seed 1・1 日・既定の引数)

- 前=HEAD `a5eec83` の写し+今の `data/world/v2`(B6build の最後の版・影 07-28 だけ)=[sides/b6build_head.json](sides/b6build_head.json)。§B6-4 の B5(最後の版)の side と 19/19 で `frozen_sources` のほか全欄同じ(B0 の欄)。
- 後=ACT の作業木+ACT の資産(写しの木)=[sides/act.json](sides/act.json)。比べ: [act_vs_b6build.json](act_vs_b6build.json)。
- **19/19 構成で final が動いた**。呼数の合計 1,267,129 → **1,129,811(−137,318)**。顕著行為 10・出動 5 は 19/19 同じ。世界の日付 07-28 → **07-13**・再生日 07-28 → **07-13**(その日の実際の天気・`how=actual`)・影 07-28 → **07-13**(近い日の代用なし・警告 0)・暦の曜日 `day_index` → `real`(どちらも月曜)・`frozen_sources` の影の行が `w9_shadow_2026-07-13.npy`。

| 構成 | 前 final / 呼数 | 後 final / 呼数 | 呼数の差 | 気づいた延べ | 食事 | 行動の件数 | blocks の行 |
|---|---|---|---|---|---|---|---|
| w6_v3_default | `0483d1165e245bed` / 70,501 | `5f7ae9ff24005314` / 65,597 | -4,904 | 310 → 237 | 4,664 → 4,559 | 313,774 → 291,935 | 8,128 → 7,975 |
| w6_v3_activity_off | `125f163354761be2` / 58,958 | `e0054a837c6ec4c1` / 50,301 | -8,657 | 562 → 719 | 3,756 → 3,342 | 196,407 → 173,688 | 2,862 → 2,660 |
| w6_v1_default | `9f6cfcf54cd847f3` / 60,591 | `24375ee3dab349e8` / 51,835 | -8,756 | 447 → 692 | 0 → 0 | 206,554 → 180,082 | 2,854 → 2,731 |
| w6_v1_derive_v2_1 | `fa483a24c61e9c22` / 55,424 | `59329a9a3611c16c` / 46,032 | -9,392 | 649 → 570 | 0 → 0 | 190,741 → 166,461 | 2,680 → 2,461 |
| w6_v2 | `40dab07ad9c33534` / 60,579 | `7e3a16b4190c10b5` / 52,268 | -8,311 | 270 → 575 | 2,367 → 2,100 | 193,663 → 170,829 | 2,789 → 2,607 |
| w6_v1_edge | `582d7f9340963ff1` / 54,302 | `0e0430daa24c109e` / 46,325 | -7,977 | 470 → 438 | 0 → 0 | 107,543 → 95,066 | 2,608 → 2,514 |
| w6_v2_edge | `f55b97e6cae96873` / 54,348 | `8151c3ee812ef412` / 46,601 | -7,747 | 514 → 376 | 2,096 → 1,886 | 104,815 → 91,998 | 2,218 → 2,139 |
| w6_v1_edge_plateau | `3c8cd47b8cd74cb8` / 56,038 | `a9d0c78a8e3bb079` / 47,912 | -8,126 | 940 → 407 | 0 → 0 | 111,816 → 98,226 | 2,634 → 2,527 |
| w6_old_v1_default | `8c6bd89ef728528c` / 60,591 | `5f3665e29e8c55e1` / 51,835 | -8,756 | 447 → 692 | 0 → 0 | 206,554 → 180,082 | 2,851 → 2,726 |
| w6_old_v1_derive_v2_1 | `ebced6f597ac9ac7` / 55,424 | `f1ac9740ef2d04ca` / 46,032 | -9,392 | 649 → 570 | 0 → 0 | 190,741 → 166,461 | 2,677 → 2,458 |
| w6_old_v2 | `8072feee6c517738` / 60,579 | `24efbaa77c1ce701` / 52,268 | -8,311 | 270 → 575 | 2,367 → 2,100 | 193,663 → 170,829 | 2,785 → 2,603 |
| w6_old_v1_edge | `8465cffa5f8317a4` / 54,302 | `607b93b4cef8f716` / 46,325 | -7,977 | 470 → 438 | 0 → 0 | 107,543 → 95,066 | 2,606 → 2,510 |
| w6_old_v2_edge | `8e52736a242225c8` / 54,348 | `c1056e6fda20f2c5` / 46,601 | -7,747 | 514 → 376 | 2,096 → 1,886 | 104,815 → 91,998 | 2,216 → 2,136 |
| w6_old_v1_edge_plateau | `a0a319c992a27900` / 56,038 | `8a15b93709c7ebdf` / 47,912 | -8,126 | 940 → 407 | 0 → 0 | 111,816 → 98,226 | 2,632 → 2,524 |
| w6_golden_null_arm | `aaaa89d936f1674e` / 101,773 | `354f49ca9a61b986` / 97,234 | -4,539 | 1,278 → 563 | 0 → 0 | 298,104 → 290,189 | 4,048 → 3,939 |
| v3_mem_store | `a16b260e4f8bc0ff` / 70,501 | `f7ff0a6953fb9a38` / 65,597 | -4,904 | 310 → 237 | 4,664 → 4,559 | 313,774 → 291,935 | 8,128 → 7,975 |
| v3_mem_rel | `25b5ce1304f6db68` / 74,056 | `73a78288ab5e1498` / 69,111 | -4,945 | 517 → 396 | 4,752 → 4,658 | 311,994 → 298,472 | 8,874 → 8,544 |
| v3_classical | `a514cf85402d8ed7` / 97,766 | `202a05a22c5bd8e1` / 93,460 | -4,306 | 927 → 901 | 9,457 → 9,298 | 441,078 → 433,042 | 8,550 → 8,566 |
| v3_classical_mem_rel | `f6f5ec7b706bc086` / 111,010 | `4c512a1fdc2a70c0` / 106,565 | -4,445 | 910 → 906 | 9,871 → 9,802 | 474,645 → 461,935 | 8,880 → 8,969 |
| 呼数の合計 | 1,267,129 | 1,129,811 | -137,318 | | | | |

- **動く理由**(前と後で違うのは「何日の天気と太陽と影か」だけ=曜日の行・日の鍵・母集団は同じ): (1) **再生日**: 07-28(雨・6.5 mm・日照 1.3 h・日最高 28.6 ℃)→ 07-13(雨・1.0 mm・日照 0 h・日最高 29.0 ℃・暑さ段「暑い」が 6 時からで 07-28 より 4 時間早い)。どちらも層は「平日|雨」。(2) **日の出と日の入り**: W13 の 07-28 の行(04:45/18:50)→ 暦の日付の 07-13(04:35/18:59)。(3) **影**: 07-13 の影。(4) W7 の PH は 07-13 に祝日が無いので効かない。呼数が減る主因がどれかは分けて測っていない(**推測**: 暑さ段が早く上がる・日照 0 の日の扱い)。既知の答え(試験): ACT の資産でも、暦の日付を legacy の再生日に合わせた calendar のランは legacy と O56 の層の名前のほか全行が同じ=動いたのは日付の違いだけ。
- **2 日のラン**([two_day_check_act.json](two_day_check_act.json)・`two_day_check_act.py`): 5,000 体・seed 1・`sim_days=2`・既定 v3・テープつき。暦の日付 **2026-07-13 → 07-14**(月・火)・各日の再生日=暦の日付(`actual`)・07-13 は「夏|平日|雨」・07-14 は「夏|平日|晴」(W13 の行の天候型と一致)・影も各日の暦の日付(代用なし)・日の出と日の入り 04:35/18:59 → 04:35/18:58。final `912446bd2b42b6ab`・140,913 呼。検査 `check` は問題 0。

## ACT-8 全体テスト

**全体(ACT の写しの木・`python -m pytest -q -p no:cacheprovider -o addopts="" -rfEs` を 6 組に分けて同時に・`tests/engine` はファイルごと・ほかはディレクトリごとの組・壁時計 1,016 秒)**: **3,847 件を集めて 3,843 passed・1 failed・2 skipped・1 xfailed**。落ちた 1 件は `vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(既知=`data` が本体へのつなぎのためテープの道筋が相対にならない・§E6-5)。

- この全体テストの後に足した manifest の `weather.expedients`(§ACT-1)と試験 1 件は、関係する 5 ファイルを回し直した: **116 件・115 passed・1 skipped**(skip は `test_state_format_10f.py` の「commit 129da80 が無い」=作業木の外の写しの木に git が無い・全体テストでも同じ)。
- 比べ: 活性化の前の基準(HEAD `a5eec83` の写し+今の `data/world/v2`・同じ回し方)は **3,842 件・3,825 passed・14 failed・2 skipped・1 xfailed**。14 件=§B8-3 の旧値の再現 9・§B8-4 の 2(感度の台帳・テープの道筋)・`test_weather_calendar_10e.py::test_b6_b3_words_body_heat_and_sun_follow_one_rule`(B6 のエンジン側の試験が W13 の年間化の資産と合わない=HEAD の時点で落ちる・一覧の外)・`test_env_and_sections_10f.py::test_t1_two_processes_write_the_same_env_id_and_final_to_the_files`(子のプロセスが本体の src を読んだ・写しの木の都合)・P6 の時間の門(機械の混み具合)。ACT ではこのうち 13 件が通り、テープの道筋の 1 件だけが残る。件数の差 +5 は ACT で足した試験(`test_activation_10e.py` の 3・W7 の PH の 2・感度の台帳の 1 から、置き換えた W7 の読みの試験 1 を引いた数)。
- 組の分け方: ファイルごとに分けると `tests/build_sched`・`tests/c7`・`tests/c8` で conftest の fixture が見えず誤って落ちる(46 件の error)ので、`tests/engine` のほかはディレクトリごとの組にした(基準もこの分け方で回し直した)。子のプロセスを使う試験のため `PYTHONPATH` は写しの木の `src` の絶対パスにした。

## ACT-9 親に確かめてほしい点

1. **取り込みの順**: 本体の `data/world/v2` へ `v2_10e_steps/ACT/` の 13 ファイルを写すまで、作業木(と本体)の全体テストは ACT の golden(§ACT-6 の表)と `tests/build_vis` の影の一覧で落ちる。写した後に `build_hash` `5ff1bacf7fd9c773…` を確かめる。
2. **D-44 の 6 つ目の値 `pending`**: 「D-44 の列は未判定の印」を、既存の 5 値のどれかに寄せず新しい値にした(測れない=口が無い、とは意味が違うため)。
3. **増えた 6 行の 3 分類**は実装役の案(未リサーチ)。`W10#11`(交通の過程との食い違い)を ii、`W13#8`(窓の最初の日の 0 時台)を iii にした。
4. **W7 の PH の読みの粒度**: `holiday_content` の JSON が壊れていればその店の PH は無し(週表の壊れと同じ扱い=黙って飛ばす)。止める形にするかは親が決める。
5. **呼数が 19/19 で 6〜17% 減る**(既定 v3 −7.0%・v1 −14.5%)。日付の違いだけで動いたことは既知の答えで確かめたが、どの要素が効いたかは分けていない。

# 第330 RET 切替口と K15 の削除(版上げ 1 回目の後・◎ 動く量なし)

> 実行役(Opus 5.5)の記録。親の検収の前・commit していない(snap_ACT の上に重ねる)。発注: 第330 発注 H の RET。ユーザーの答え 1-5(旧資産の切替口は版上げ 1 回目の後に消す)・実装の計画 §2 第 0 期の注(切替口と K15 の削除の 1 commit)。

## RET-1 消したもの

| 切替口・列 | 消した中身 | 残したもの(記録だけ) |
|---|---|---|
| `--hash-scheme full` | `run_day(hash_scheme=…)`・CLI・`Checkpoint.hash_scheme`・`Checkpoint.legacy_combined`・`state_hashes.HASH_SCHEMES`・`check_hash_scheme`・`core.soa.retired_columns_in_hash`・`Registry.retire`(と `state_hash` の中の並べ直し)・`agents/state.py` の `retire` の 3 行・再開の指紋の除外の 1 行 | manifest の `hash_scheme`=`behavior`(`state_hashes.FINAL_DEFINITION`・final の定義の記録) |
| `--rng-scheme stateful` | `run_day(rng_scheme=…)`・CLI・`core.rng.RNG_SCHEMES`・`DEFAULT_RNG_SCHEME`・`check_rng_scheme`・`k19_counters` の方式の引数(旧の並び)・顕著行為と出動の日の頭の Generator(作る・日の頭で引き直す `relay_day`)・母集団・体の定数・配送・工事・p_notice・世帯の財布の `rng_scheme` の引数・`rng_audit` の扱い `stateful`(`K19_ALLOW` の 8 用途名・`STATEFUL_ONLY`・`check_overlaps(rng_scheme=…)`)・静的の一覧の 4 か所(Generator の作成と `relay_day`)・動きの側の乱数の表の 2 本 | manifest とテープの脇の meta の `rng_scheme`=`counter`(`core.rng.RNG_SCHEME`)・`rng_layout`。**`runner.salient.rng`・`runner.dispatch.rng` の属性は常に `None` で残した**(§RET-4 の 1) |
| `--calendar-weekday day_index` | `run_day(calendar_weekday=…)`・CLI・`SimCalendar.weekday_mode`(day_index の曜日・祝日を見ない・鍵 = day_index + 日・開始日の違反は警告だけ)・`WEEKDAY_MODES`・`DEFAULT_WEEKDAY_MODE`・`check_weekday_mode`・`SimCalendar.legacy`(→ `SimCalendar.default(day_index)`=2026-07-13 + day_index 日・祝日の表なし・real) | manifest とテープの meta の `calendar_weekday`=`real`(`calendar.WEEKDAY_MODE`) |
| `--weather-scheme legacy` | `run_day(weather_scheme=…)`・CLI・`WEATHER_SCHEMES`・`DEFAULT_WEATHER_SCHEME`・`check_weather_scheme`・環境の過程の legacy の実日の選び方(`select_day`・`prefer_shadow_days`・影のある日に絞る・日の出と日の入りを再生日の行から)・`run_day` の「世界の日付=再生日」の置き換え・`DEFAULT_START_DATETIME` の開始日 | manifest とテープの meta の `weather_scheme`=`calendar`(`calendar.WEATHER_SCHEME`) |
| `--world-assets-pre10e`(B1 の口ごと) | `run_day(world_assets_pre10e=…)`・CLI・`AssetSource`・`asset_source`・`PRE10E_FAMILIES`・`PRE10E_DEFAULT_DIR`・`load_assets`/`load_process_assets`/`PerceptionAssets.load`/`World.load` の `pre10e`・騒音の 2 つの読み手の食い違いの検査・manifest の欄と設定の節の行・再開の指紋の道筋の 1 行 | B0 の資産の指紋(`frozen_sources`)はそのまま。退避先 `data/world/v2_pre_10e_2026-10-12/` はそのまま(読むだけ・消していない) |
| `CALENDAR_UNIFIED` | 定数(True の側だけ残した=上の 2 つの名前) | — |
| K15 の 2 列 | `agents.fail_streak`(u1・resolve の 6 か所の書き込み)・`agents.plan_activity`(i1・計画実行層の `set_plan_state(activity=…)` と日の頭・境界の 3 か所の書き込み・`_plan_activity_at`)・状態台帳の 2 行(187 行・版 `state-ledger/10e` → **`state-ledger/10e-ret`**) | イベント列の `ev_act`(状態台帳の行の一部)は変えない |
| テープ | 再生の既定を meta から決める `resolve_rng_scheme`・`resolve_calendar_schemes`・`RngSchemeWarning`・`CalendarSchemeWarning`・旧テープを `stateful`/`day_index`/`legacy` とみなす口 | **`check_replay_tape`**: meta が `rng_scheme=counter`・`rng_layout=10e`・`calendar_weekday=real`・`weather_scheme=calendar` でないテープは止める(警告でなく例外・文言に違う欄)。`response_delay` の「値が無ければ 2」は残した |

**手元の 53 本の実テープ**(`data/` の下の `calls.parquet`・`realworld_live` を除く): どれも `run_meta.json` が無い(10a より前の録画)=**全部止まる**(`check_replay_tape` で 0/53 が通る)。ACT の commit では `stateful`・`day_index`・`legacy` とみなして警告つきで回った(§ACT-4)。再生が要るときは ACT の commit(か 10e より前の commit)で回す。

## RET-2 動いてはいけない量(19 構成・ACT と比べた)

[ret_vs_act.json](ret_vs_act.json)(前=[sides/act.json](sides/act.json)・後=[sides/ret.json](sides/ret.json)・どちらも ACT の資産の写しの木): **19/19 で final・呼数・行動の件数・blocks・テープの列と中身・顕著行為と出動・気づいた延べ・食事・behavior-hash・暦の欄・`frozen_sources` が同じ**。動いたのは `full_last`(最後の checkpoint の full-hash)と `end_of_day` の `full_hash` だけ=**K15 の 2 列が SoA の full から抜けた分**(`end_of_day` の behavior-hash と外の状態の直列化のバイト数 `full_external_bytes` は 19/19 同じ=外の状態は動いていない)。試験の直しの後の最後のコードでもう一度回し、計時の欄のほか全欄が 1 回目と同じだった(`sides/ret.json` は 2 回目)。

## RET-3 試験

- **消した旧値の再現の試験**(ACT の commit で `GE.PRE10E_RUN_KW`=退避先の資産+`day_index`+`legacy` と `hash_scheme="full"`・`rng_scheme="stateful"` を渡して**通った**=§ACT-8 の全体テストに入っている): `test_presence_executor.py::test_hash_scheme_full_reproduces_the_pre_10e_checkpoints` と `W17_GOLDEN` の `*_stateful`・`*_pre10e` の行/`test_classical_social.py` の `CLASSICAL_1500_GOLDEN_ACQ_PRE10E`/`test_relations_tenure.py` の `("v1","full")`・`("v2","full")`/`test_state_checks_10f.py` の stateful の既知の答え(w16 185・body 1・final `4985ff2f`)/`test_state_ledger_10b.py` の `PRE10E_SYN`(5 構成)と `test_e1_retired_columns_reproduce_the_old_registry_hash`/`test_activation_10e.py` の旧テープの再生(day_index・legacy)/`test_rng_scheme_10c.py` の stateful のテープの再生・stateful と counter の比べ/`test_weather_calendar_10e.py` の legacy と比べる 2 件/`test_calendar*.py` の day_index の暦の 3 件/`test_assets_10e_b0_b1.py` の B1 の 4 件/`processes/test_environment.py` の `select_day` の 3 件/`test_calendar_sites.py` の `select_day` の鍵の 1 件。どれも「切替口が無い」ことを見る試験か、今の規則の試験に置き換えた。
- **今の値に張り替えた**(生きている切替口=`l4_scale`・`hunger_model`・`leave_effect`・`poi_target`・`near_tiebreak`/`near_order`・`rel_tenure_hash` の値。前は 10e より前の定義・乱数・資産・暦の値):

| 試験 | 定数 | 前(10e より前の値) | 後(RET の今の値=final は behavior-hash) |
|---|---|---|---|
| `test_presence_executor.py` | `null_arm_final_l4x1`/呼数 | `ed1863e089c8480e` / 41,141 | **`f02d7fd4fbb4dc4f` / 40,979** |
| 同 | `v3_default_final_l4x1` | `6845e3acb8906210` / 36,502 | **`a18594506e4a0ea5` / 36,172** |
| 同 | `null_arm_final_hunger_v1` | `e0083baff1ff50b7` / 97,028 | **`f655d1eb601d7bb4` / 94,435** |
| 同 | `v3_default_final_hunger_v1` | `a1036ab5b06e461c` / 68,781 | **`1767737a4183a436` / 64,977** |
| 同 | `null_arm_final_leave_off` | `18f8807264d04018` / 100,509 | **`a33c00469ca28832` / 98,017** |
| 同 | `v3_default_final_leave_off` | `c9ab05383accca2e` / 69,603 | **`1761eef0e3c48dd5` / 65,634** |
| `test_intent_chooser.py`(Q13) | v3 / 帰無腕 | `02bd03126d5f41cb` / 36,460・`b4ad8140fe4176db` / 41,072 | **`9bc6929fbb0da5e8` / 36,275・`ce33abec7629c811` / 40,963** |
| `test_near_tiebreak.py` | `hash`・`hash_order_id`・`classical_tie_id` | `91732f34…` / 26,869・`e0a6f3f9…` / 26,845・`803f0441…` / 26,753 | **`87492778…` / 25,890・`b7697fca…` / 25,828・`49c3fae0…` / 25,877** |
| `test_relations_tenure.py` | `("v1","behavior")`(前 `("v1","full")`) | `e4f84d1d176e6ec0` / 72,940 | **`380e8651a96b1829` / 69,406** |
| `test_10a_review_fixes.py` | `HEAD_PLUS2_FINAL` | `79821d778ea4addf` | **`3dc9605f573de1be`**(2 回回して同じ) |
| `test_state_ledger_10b.py` | 台帳の行数・版 | 189 行(agents 76・SoA 93)・`state-ledger/10e` | **187 行(agents 74・SoA 91)・`state-ledger/10e-ret`** |
| `test_state_checks_10f.py` | `SAFE_SITES`・`UNDETERMINED_SITES` の数 | 16・16 | **14・12** |

  値は写しの木(RET のコード+ACT の資産)で 1 本ずつ回した(`ret_goldens.py` の記録は §RET-5)。
- **比べ方を変えた**(`AgentState.state_hash` を差し替えて腕の欄を除き「腕を足しても挙動は同じ」を見る試験=§E6-1 の 9 か所): 前は `hash_scheme="full"` で final を旧い組み立てにしていた。切替口を消したので、試験の側の **`tests/golden_env.py::soa_combined`**(checkpoint の `agents_hash`・`world_hash`・母集団・予定表・活動から 10e より前の式で組む)で比べる形にした(`test_familiarity`・`test_memory_recall`・`test_memory_record`・`test_relations`・`test_store_memory`・`test_wom` ×2・`test_ledger_wiring` ×2・`test_tape_deferred`・`test_two_layer_activity`)。
- **day_index の鍵の試験**(`test_rng_scheme_10c.py::test_run_day_passes_day_key0_to_the_counter_key`・`test_salt_seed_split_10f.py::test_road_works_day_key_with_nonzero_day_index`): real の暦の鍵(日番号=0)で見る形にした(`day_index=14`=2026-07-27・月曜)。
- **K15**: `fail_streak` を読んでいた 5 か所の確かめ(`test_resolve` ×2・`test_two_phase`・`test_conversation_invite`・`test_presence_exit_walk`)を消した(列が無い)。AST の試験の「読み手 0 の no の列」の例は `fail_streak` → `rel_last` に替えた。
- 残した記録用の道具(`docs/bench/analysis/wallbounce-1003/10c/*.py`・`10d/resume_check_10d.py`・`10b/hash_order_check.py`・`c10-relations…/rel8b_measure.py`・10e の `population_swap_check.py`・`tools/c7/attr_arms.py` の `population_for(rng_scheme=…)`)は消した切替口の名前を引数に持つ。過去の記録を作った道具なので直していない(今のコードで回すと止まる=**親に確かめてほしい点**)。

## RET-4 全体テスト

- **写しの木(RET のコード+ACT の資産)・1 プロセスで全部**(`python -m pytest -q -p no:cacheprovider -o addopts="" -rfEs`・壁時計 3,690 秒): **3,841 件を集めて 3,837 passed・1 failed・2 skipped・1 xfailed**。落ちた 1 件は `vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(既知=テープの道筋・§E6-5)。skip は `test_state_format_10f.py` の「commit 129da80 が無い」(写しの木に git が無い)ほか 1。
- その前に 6 組で回した回(1,115 秒)では、試験の直しの漏れ 4 件(`test_weather_calendar_10e.py` の既知の答えの開始日=火曜で開始日の検査に止められた・`test_resume_10d.py` の `k19_counters` の旧い引数・`test_env_and_sections_10f.py` の設定の節の sha と台帳の版)と、`test_version_bump_10e.py` の書き換えで飾り(parametrize)が二重になった集めの error 1 件(その組の 34 ファイルが回らなかった)が出た。直して上の 1 プロセスの全体で確かめた。
- 件数は ACT(§ACT-8 の 3,847 件+後から足した manifest の expedient の 1 件=3,848)から 7 件減った(消した旧値の再現の試験・B1 の 4 件・`select_day` の 3 件などと、置き換えた「切替口が無い」の試験の差し引き)。

## RET-5 スナップショットと値の出どころ

- `snap_RET`(HEAD `a5eec83` からの累積=ACT を含む)。
- 張り替えた値は [ret_goldens.py](ret_goldens.py)(写しの木で `cli.run` を 1 本ずつ・5 本同時)の出力=[ret_goldens.json](ret_goldens.json)。`HEAD_PLUS2_FINAL` は同じ木で偽 vLLM 3 台の +2 の経路を 2 回回して同じ値。

# 第330 締め(版上げ 1 回目)

## 締め-1 段ごとの動いた量(19 構成・5,000 体・seed 1・1 日・既定の引数)

| 段 | 何が | v3 既定 final / 呼数 | 帰無腕 final / 呼数 | 呼数の合計 | 記録 |
|---|---|---|---|---|---|
| HEAD(10e の前) | — | `993276d5e5bb5cbe` / 69,978 | `72cb9cd52982da74` / 100,439 | 1,259,151 | `sides/head.json` |
| E1 | final を behavior-hash に・死蔵の 5 列 | `3264c9fc190b3eb9` / 69,978 | `db765499cec1fef5` / 100,439 | 1,259,151 | §E1 |
| E2 | 会話の掃除(O39) | `4985ff2fb3c771c4` / 69,978 | `065a36d238aae477` / 100,439 | 1,259,151 | §E2 |
| E4 | 乱数 counter・K19(住人が入れ替わる) | `4fbf61616af1e3d2` / 70,421 | `6c81c5ad8a99437a` / 101,969 | 1,264,661 | §E4 |
| E5 | テープ版 4 | 同上 | 同上 | 1,264,661 | §E5 |
| B0・B1・E3・B6eng | 指紋・旧資産の口・暦と天気の切替口(既定不変) | 同上 | 同上 | 1,264,661 | §第330 |
| B3 | W12 の丸め | `e1bf096f58bce57f` / 70,500 | `91439d0c2276cbf1` / 101,278 | 1,265,034 | §B3 |
| B4 | W10 ON+Q7 | `54ba78d0bdf643b4` / 70,501 | `3fc1395865db177e` / 101,773 | 1,267,129 | §B4 |
| B5 | W13 の年間化(final だけ) | `0483d1165e245bed` / 70,501 | `aaaa89d936f1674e` / 101,773 | 1,267,129 | §B5 |
| B6build | W7 の PH の列(不変) | 同上 | 同上 | 1,267,129 | §B6 |
| **ACT** | 暦の一本化・開始日 07-13・影 6 日 | **`5f7ae9ff24005314` / 65,597** | **`354f49ca9a61b986` / 97,234** | **1,129,811** | §ACT |
| **RET** | 切替口と K15 の削除(full-hash だけ動く) | 同上 | 同上 | 1,129,811 | §RET |

## 締め-2 消した切替口(§E6-1 の表の行き先)

`--hash-scheme full`・`--rng-scheme stateful`・`--calendar-weekday day_index`(と `day_index` の暦)・`--weather-scheme legacy`(と legacy の実日の選び方)・`--world-assets-pre10e`(B1 の口ごと)・`CALENDAR_UNIFIED`・K15 の 2 列。旧 pickle の口は E2 で消した。残る 10e の切替口は `--weather-perturb`(アンサンブル・既定 off)だけ。

## 締め-3 予算表(5,000 体)

| 項目 | 10e の前 | 版上げ 1 回目の後 | 宣言・門 |
|---|---|---|---|
| agents の SoA(既定・実測) | 137 B/体(E1 で −5) | **131 B/体**(K15 で −1) | M1 ≤30 KB/体 |
| agents の SoA(計画実行層つき) | — | **132 B/体**(K15 で −2) | 同上 |
| agents の SoA(全腕) | — | **5,366 B/体**(K15 で −2) | 同上 |
| 知覚 SoA | 18 B/体 | 2 B/体(E1) | 自主の上限 24 B/体 |
| 状態のファイル・テープ・checkpoint の時間 | §E6-3 | 変えていない(K15 の 2 列の分だけ状態のファイルが小さくなる・測り直していない) | §E6-3 |
| W9 の影 | 1 日 12,842,624 B(07-28 だけ) | **6 日 77,055,744 B**(容量のゲート 10 MB/日は FAIL のまま) | D-W10 |

(SoA の値は `AgentState(1000)` の配列の合計 ÷ 体数=写しの木で測った。10e の前の 137 は E1 の記録の 132+5 から逆算=**推測**)

## 締め-4 つなぎの台帳に載せるもの(親へ・本書は書かない)

1. **W18 の X**(構築側 §B6 の発注 (4)・凍結カタログの改訂は 10e の外)。
2. **W12 の土休 > 平日**(等間隔の推定のダイヤで 1 日の本数が土休 > 平日=5 線とも・§B3 の表。実データの時刻表で直す=答え §2)。
3. **W11 の神泉の出口**(井の頭線の到着の元=答え §2-3 の表)。
4. **影の近い日**(暦の日付の影が無いときは近い日・同じ近さなら前の日=expedient・`WEATHER_EXPEDIENTS`・manifest の `weather.expedients`)。
5. **層を広げる順**(隣の季節 → 全季節 → 平日/土休を問わず=expedient・同上)。
6. (実行役から足す)W9 の影を作る日は `SHADOW_DATES` の 6 日だけ=7 月 18 日以降・別の開始日・2 日を超えるランは近い日の影(警告)。

## 締め-5 親に確かめてほしい点

1. **O46・O47 の `rng` の道筋を残した**: stateful を消すと `runner.salient.rng`・`runner.dispatch.rng` は常に `None` になるが、状態台帳の外の状態の行(behavior)に道筋として載っており、behavior-hash は「無い」の印を道筋の名前つきで混ぜる。道筋を消すと 19/19 で final が動く(発注の「RET は動く量なし」に反する)ので、属性(常に `None`)と台帳の道筋を残し、行の注に理由を書いた。消すなら final が動く変更として別に回す。
2. **状態台帳の版を `state-ledger/10e-ret` に上げた**(「列や行の判定を変えたら上げる」の規則)。ACT までの状態のファイルからは再開できない(列が違う)。
3. **手元の 53 本の実テープは今の版で再生できない**(§RET-1)。止める文言に違う欄が出る。
4. **ACT の資産の取り込み**: 本体の `data/world/v2` へ `v2_10e_steps/ACT/` の 13 ファイルを写すまで、作業木と本体の全体テストは ACT の golden で落ちる(§ACT-9 の 1)。
5. **旧い記録の道具**(§RET-3 の最後)は消した切替口の引数を持ったまま。直すか、凍結の印を付けるかは親が決める。
6. **`SimCalendar.default`**(暦を渡されない過程の暦)は 2026-07-13 + day_index 日で、日の鍵は日番号 0。前の `legacy` は鍵 = day_index。単体の試験で `day_index` を渡して過程を作ると、乱数の鍵が前と違う(実ランは暦を渡すので関係しない)。
7. **全体テストの回し方**: 本体の `data/world/v2` を書き換えない約束のため、ACT と RET の全体テストと byte-check は「作業木のコードの写し+ACT の資産の写し」の木で回した(作業木の `data` のつなぎを付け替える操作は権限で止められた)。

## 親検収(第330・版上げ 1 回目の締め)

- 段の commit: 実装役の累積スナップショットを作業木の枝に順に重ね、段ごとに「一覧=ステージ」を `tools/commit_check.py` で確かめて commit(エンジン側 4・構築側 5・ACT・RET)。本体の枝へは rebase と fast-forward(README の追記の衝突 1 回は両方を残す形で解決・試験 2 本は自動で合流)。
- 本体の作業木の CRLF: 追跡ファイル 206 本が CRLF(git の中身は LF・古い checkout の名残)で、W12/W16 の `input_hash` が構築役の作業木と食い違っていた。index から取り直して全部 LF にした(中身の差 0)。
- 資産: 最後の版(構築側・25 ファイル)と ACT の 13 ファイル(影 5 日・build_hash `5ff1bacf7fd9c773`)を本体の `data/world/v2` に写した(sha256 を MANIFEST と突き合わせ)。
- byte-check(親・本体・4 構成=v3 既定・v3 活動層 off・v1 既定・v3 記憶+関係): 構築側の最後の版=`sides/final.json` と全欄一致(違いは B0 の `frozen_sources` だけ)。ACT+RET の後=4 構成とも実行役の RET の記録 sides/ret.json と全欄一致(動いた量 0・parent_main_vs_ret_4cfg.json)。
- 全体テスト(親・本体・ACT の資産): 3,841 件を集めて 3,839 passed・0 failed・1 skipped・1 xfailed(61 分・本体・ACT の資産。作業木で落ちた既知のテープの道筋の 1 件は本体では通る)。
- 旧い記録の道具(10b〜10e・c10・`tools/c7/attr_arms.py`)は消した切替口の引数を持ったまま=凍結の印を付けず残す(回し直すときに直す・つなぎの台帳)。

## 〔答え(第331・2026-10-13)〕 ACT-9・締め-5 のユーザーの判断

- [回答 10-13](../../../../design/v2-answers-2026-10-13.md) の 6: **親案どおり**。(1) D-44 の列の `pending` を認める。(2) 手元の実 LLM テープ 53 本は消さず、「今の版で再生できない(meta 無し・再生は ACT の commit `d688cfd` か 10e より前の commit で)」をライセンス台帳でなく本記録 §RET-1 と IMPLEMENTED #88 に記す(読む用途=語彙の登録ほかは残る)。(3) 既定 v3 の呼数 70,501 → 65,597(−7%)の主因(暑さの段か日照 0 の日か)は第 2 期の前に 1 回だけ測る(07-13 と 07-28 の天気の行の差を表に)。
- 回答の 7: W12 の土休 > 平日の欠陥は 10e では直さず、実ダイヤへの置き換えを第 2 期の版上げ 2 回目に前倒しして解く(実装の計画 2-3b)。
