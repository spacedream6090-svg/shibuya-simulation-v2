# 第347 止めた切替口 3 本の削除と、`--space legacy`・`--hunger-model v1` を試験の中だけの口に(switch-removal-347)

> 整理の段(既定のランの結果を 1 バイトも変えない段)。発注: [返事その 8](../../../design/prompt-2026-11-16-reply8.md) §1-1(b)・
> §1-2 Q7(d)・§1-10(第346 の仮採用)。前例: [delete-346](../delete-346/README.md) §3(止めた 3 本と、旧道を使う試験の一覧)。
> 土台は作業の木の枝 `work/switch-removal-347`(① は頭 `ff28372d`=段 4-10 まで・①c の前に頭 `d42fbba0`=段 4-12 まで入った本体へ
> 移した=§7)。実装役 Opus 5.5。byte-check・範囲の試験・commit とタグ(`stable-v2-before-switch-removal-347`=②a の前の
> commit)は親。

段の並び(親の裁定): ① 試験の書き直し(切替口はまだ在る・src は変えない)→ ②a 経済の段階 2 の off → ②b 率の規則と「無い」の
過程(組で)→ ③a `--space` → ③b `--hunger-model` の旗。**本書は ①(手順 0・①a・①b・①c)と ②a と、① の検収の直しと ②b まで**
(②a は §9・検収の直しは §10・②b の作業の一覧は §11・②b は §12・試験ごとの行は付録 A)。

## 0. 要点(① まで)

- **手順 0: 部品 none は off と同じではなかった。** 5 構成とも、体の SoA・呼数・購入・世帯の現金・店の売上・保存則・検算②は
  同じ。ただし台帳が違った。段階 2 の初期の預金が部品に依らず入る(世帯の預金 0 → 3,420 万〜8,104 万円)。購入の行に金の
  出来事の目印が付き、生ログの方法の列も埋まる。世界資産のランでは雇用主の口が 1 → 9,872 になる。外の状態を含む final と
  full-hash も違った(§1)。
- **ユーザーへの説明(親の答え・①c)**: ユーザーの答えは「旧道を使う試験を、過程の単体試験(段階 2 on)に書き直す」だった。
  しかし段階 2 を on にすると、部品 none でも台帳の値が off と違う(§1 の表=世帯の預金・faucet・金の出来事・生ログの行と
  方法の列・雇用主の口・final と full-hash)。そこで、off を基準に使っていた 5 か所(E1 の off の行・E2・E4・E11 の 2 本・E13)と
  再開の 2 本(E8・E9)は、off と同じ値になる「段階 2 の外の束」(試験の中だけの口)で書き直した。**確かめる値は前と同じ**(§4)。
  根拠は第346 の仮決定「部品の単体試験の基準の口は残す(ランの口からは選べない)」(返事その 8 §1-10)。外の束は、src に残る
  構造の道(`attach_stage2` を持たない台帳)を試験の中だけで選ぶ。
- **ユーザーの指示の字面(段階 2 on)に当たる試験も置いた(検収 M2・§4-4)。** off を基準にしていた試験の 1 本ずつについて、
  同じことを段階 2 on の道(今のランが通る道)で確かめる試験を探した。在るものは名を表に書いた。無かった E1 と E4 は、段階 2 on の
  試験を足した(期待値は段階 2 on のランから取り直した)。E3(HEAD の写しとの同値)と、段階 2 の外にしか無い性質(E9・E11 の
  1 本目・E8 の外の台帳への再開)は、段階 2 on では成り立たない。外の束の試験は基準の口として残してある。残すか消すかはユーザーに
  聞く(仮採用・戻し方=外の束の試験と助け `tests/economy/_stage2_outside.py` を消す)。
- **段階 2 の外の束は off と同じだった。** 段階 2 の口(`attach_stage2`)を持たない台帳=試験の中だけの束(§2-1)は、5 構成とも
  38 欄すべてが off と同じ。E3(HEAD の写しとの 5,000 体の同値)はこの束で書き直した(裁定 3)。
- **試験の中だけの助けも、ランの結果は切替口と同じだった。** 実行器と計画実行層の初期化を包んで部品の口(旧道)を挿す助け(§2-2)は、
  2 構成(合成 2 日の倒れる・出動・再開の形/世界資産 200 体の率の規則の旧道)で final・checkpoint・件数・過程の計数がすべて
  同じだった。違ったのは、組み立ての腕(既定の off・stopped)を書く欄だけ: manifest の `rate_rules.mode`・`absent_processes.mode`
  と印(`rate_rules.removed` の 7 欄・`absent_processes.stopped` の 5 欄が 0 → 1)、状態のファイルの見出し(§1・§2-2。〔検収 M1〕
  前の版は「mode の欄だけ」と書いていた=道具が印の欄を外していた)。これで、率の規則と「無い」の過程の旧道を駆動に使う試験を、
  確かめる範囲を減らさずに書き直した(裁定 1)。
- 書き直した試験は §3(①a・①b)と §4(①c)。試験のファイル 26 本と、前から在る助け `tests/engine/multiday/_md.py`(合わせて
  27 本)・新しい助け 2 本(tests の下の差分は 29 ファイル)。src は変えていない(§7)。
- 見つけた欠陥を直した: `tests/engine/test_removed_switches_346.py::_system_frames` は空振りしていた。負の対照も足した(§5)。
- manifest・つなぎの台帳・世界の台帳のハッシュが動く直しは、今回はしない。一覧は §6。

## 1. 手順 0: 部品 none は off と同じか(書き直しの形を決める確かめ)

道具 [tools/step0_parts_none.py](tools/step0_parts_none.py)。腕は 3 つ: `off`=切替口 off/`none`=段階 2 on・部品 none/
`noattach`=段階 2 on のまま、台帳を段階 2 の外の束(§2-1)にする。比べた欄は 38 個。final・checkpoint の
behavior-hash・full-hash・試験の側の SoA の組み立て・呼数・購入・世帯の現金・店の売上・保存則(毎日)・検算②・
`money_stage2_in`・センサスの行・台帳の大きさ・取引の件数・生ログの行と目印と方法の列・日ごとの流れ・部門ごとの現金・世帯の
預金・物の在庫と納品の行と目印・faucet と sink の科目・manifest の `economy` の鍵・出来事の語ごとの件数。

| 構成 | 欄の数 | 部品 none と off で違う欄 | 段階 2 の外の束と off で違う欄 | final(off / none / 外の束) | 呼数 | 世帯の預金 off→none | 金の出来事 off→none | 生ログの行 off→none |
|---|---:|---:|---:|---|---|---|---|---|
| E4 `test_ledger_wiring` の `wired`(合成 64 セル・500 体・1 日・台帳を直に作る) | 38 | 19 | 0 | `6cd7caf1cbd40722` / `aa8851447ae5c452` / `6cd7caf1cbd40722` | 3,477 / 3,477 | 0 → 81,039,000 | 0 → 169 | 669 → 1,407 |
| E4 同・物の過程を切ったラン(状態ハッシュ不変の試験) | 38 | 19 | 0 | `5a8d2078899416ee` / `2bcc74e6c4d481d5` / `5a8d2078899416ee` | 3,477 / 3,477 | 0 → 81,039,000 | 0 → 169 | 669 → 1,407 |
| E1 `test_cp2_event_links`(世界資産 200 体・1 日・率の規則の旧道) | 38 | 20 | 0 | `8d678b39707f7c8e` / `6cef88e7f4926bc2` / `8d678b39707f7c8e` | 1,922 / 1,922 | 0 → 34,200,000 | 122 → 375 | 2,912 → 3,312 |
| E11 `test_stage2_runs::_run`(合成・300 体・2 日・小さな財布・ATM を置く) | 38 | 14 | 0 | `20cb3e191085f3b2` / `3b1c6e13a443fcc4` / `20cb3e191085f3b2` | 4,464 / 4,464 | 0 → 48,831,000 | 0 → 0 | 300 → 742 |
| E13 `test_stage2_world_two_day` の縮小(世界資産 300 体・2 日・給料日をまたぐ) | 38 | 18 | 0 | `936a3e6a45a5ed4b` / `080510173a438f07` / `936a3e6a45a5ed4b` | 5,605 / 5,605 | 0 → 51,300,000 | 348 → 1,106 | 3,743 → 4,343 |

- 部品 none で違ったものは 3 つ。(1) 段階 2 の初期の預金(科目「預金純増」=世帯 → 銀行)は部品に依らず入る。faucet の
  来街者持込も同じ額だけ増える。(2) 購入の行に金の出来事の目印が付き(「金:消費支出」)、生ログの方法の列が埋まる。(3) cli の台帳は
  雇用主の口 9,872・輪の係数 16.0 で作られる。体の動き(SoA・呼数・購入)は 5 構成とも同じ。外の状態を含む final と full-hash は違う。
- 部品 none の欄の差の一覧(E4 の wired): 出来事の語・部門ごとの現金・センサスの行・checkpoint の behavior-hash と full-hash・
  日ごとの記録の economy・世帯の預金・faucet と sink・final・日ごとの流れ・manifest の `economy` の鍵(`stage2` が足される)・
  金の出来事の数・生ログの行の数・目印の無い行の数・取引の件数・生ログの目印と行・方法の列・段階 2 が挿さったか。
- 段階 2 の外の束(`noattach`)は 5 構成とも 38 欄すべて off と同じ(E11 は `_SmallWallets` を `outside` で包んで回した)。

手順 0 の続き [tools/step0_legacy_helper.py](tools/step0_legacy_helper.py)(切替口の腕 legacy と、§2-2 の助けの比べ):

| 構成 | 同じ欄 | 違う欄(切替口 → 助け) |
|---|---|---|
| r4=`test_resume_10d::test_counter_rng_resume_draws_once` の通し(合成 25 セル・200 体・2 日・倒れる率 3,000・両方の旧道) | final・呼数・全 checkpoint(288 個の combined と full-hash)・顕著行為 238・出動 119・気づき・過程の計数(全部の鍵。名に removed・stopped を含む 12 個も同じ)・manifest の `rate_rules.counts`・`absent_processes.counts`・`waste_sink`(10 欄) | manifest の `rate_rules.mode`(legacy → off)・`absent_processes.mode`(legacy → stopped)・`rate_rules.removed`(9 欄のうち 7 欄が 0 → 1)・`absent_processes.stopped`(5 欄すべて 0 → 1)(4 欄) |
| r11=`test_rate_rules_1101::day_runs` の legacy(世界資産 200 体・台帳つき・1 日・率の規則の旧道) | 上と同じ 10 欄+`absent_processes.mode`・`absent_processes.stopped`(12 欄) | manifest の `rate_rules.mode`(legacy → off)・`rate_rules.removed`(9 欄のうち 7 欄が 0 → 1)(2 欄) |

- 違う欄は、どれも組み立ての腕(設定の箱の `cfg.rate_rules`・`cfg.absent_processes`=既定のまま)を書く欄。過程そのものの印
  (過程の計数の `salient.rate_rule_collapse_removed`・`dispatch.absent_dispatch_stopped` ほか 12 個)は、実行器の腕(助けが替えた
  旧道)を書くので切替口と同じ。状態のファイルの見出し(`rate_rules`・`absent_processes`)も組み立ての腕を書く(§2-2 の注)。
- 〔検収 M1〕前の版の道具は過程の計数から名に removed・stopped を含む鍵を外し、manifest の印の節も比べていなかった。このため
  前の表は「mode の欄だけ」と書いていた。外すのをやめ、印の節を足して回し直した(上の表=回し直した結果・本段の commit の前の
  頭 `231d9fd0`)。検収役が manifest の全部の欄を比べた結果(切替口を 2 回回して揺れ 0 を確かめてから助けと比べた)とも合う。

結果の JSON は作業の機械のスクラッチに置いた(リポに入れない)。

## 2. 試験の中だけの助け(tests の下・src に足さない)

### 2-1 段階 2 の外の束 `tests/economy/_stage2_outside.py`

- `outside(cls)`: 台帳の型の子で、`attach_stage2` を「無い」に見せる(`hasattr` が偽)。`economy.stage2_bind.attach` は台帳が
  `attach_stage2` を持たなければ何もしない。再開の検査は `effective=False` になる。どちらも切替口 off を消した後も残る組み立ての
  構造で、HEAD の台帳の写しと同じ扱い。
- `use_outside_bundle(mp, ledger_cls=…, wallet_cls=…, goods_cls=…)`: `shibuya.cli` の台帳の型を差し替える。`cli.build_ledger_bundle`
  が作る台帳を、切替口 off の分かれと同じ形にする(雇用主の口 1・輪の係数は台帳の既定 `economy.ledger.TRANSFERS_PER_AGENT_PER_DAY`)。
  組み立ての残り(世帯の財布・物の台帳・参入資本・センサスの口)は本物のまま。HEAD の写しの型を渡せばその上に作る。
- ランの口(CLI・環境変数・`run_day` の引数・設定の箱の欄)には触らない。

### 2-2 率の規則と「無い」の過程の旧道の助け `tests/engine/_legacy_world.py`

- `legacy_world_rules(mp, *, rate=True, absent=True, salient_rate=None)`: `world.laws.runner.WorldProcessRunner.__init__` を包み、
  組み立てが渡す `rate_rules`・`absent_processes`・`salient_rate_per_10k` を部品の口の旧道に替える。`rate` のときは
  `engine.presence.PlanExecutor.__init__` の `rate_rules` も替える(E8 の到着の分散)。第346 の検収 M2(`proximity.rule_from` を
  試験の中で差し替えた)と同じ形。
- 注: 組み立てが読む腕(設定の箱の `cfg.rate_rules`・`cfg.absent_processes`)は既定のままになる。このため manifest の
  `rate_rules.mode`・`absent_processes.mode` と印(`rate_rules.removed`・`absent_processes.stopped`)と状態のファイルの見出しは
  既定(off・stopped)を書き、計数(`counts`)と過程の計数だけが旧道の件数と印を持つ(§1)。manifest の mode を見ていた 2 本は、
  実行器の腕と過程の印を見る形に替えた(§3 の R11b・A3)。その 2 本は manifest の mode が既定を書くことを期待値に置いた(§11 の L5)。

## 3. 書き直した試験の表(前に確かめていたこと → 後に確かめること)

「同じ」=前と同じことを確かめる。旧道はどれも部品の口(過程の引数)で回す。切替口が在る今の木で、どれも前の値のまま通る(§7)。

### 3-1 `--economy-stage2 off`(①a)

| 試験 | 前 | 後 | 同じか |
|---|---|---|---|
| `tests/economy/cp2/test_cp2_nine_ops_equivalence.py::test_5k_mock_day_matches_head[6.5・3.0]`(slow) | 切替口 off で、HEAD 136fdbb の台帳の写しと今の台帳の 5,000 体・1 日の final・呼数・金と物の台帳の状態・世帯の現金が同じ(輪の係数 6.5 は溢れ 0・3.0 は溢れを数える) | 段階 2 の外の束(§2-1。HEAD の側は写しの型の上・今の側は `outside` の型)で同じ比べ。「本当に HEAD の台帳で回した」は型の名の比べから isinstance に替え、今の台帳に段階 2 が挿さっていないことも見る | 同じ |
| `tests/engine/multiday/_md.py::arms()`(使う試験: `test_md23_resume.py::test_synthetic_two_days_resume_at_the_day_boundary[mem・events]`・`test_md23_body_events.py` の `runs` と `test_legacy_path_with_the_log_off_is_the_1_6_form`) | 経済の段階 2 の腕を off にして、合成の 2 日の再開=通しと記憶の器を見る | 腕の引数を外した。これらのランは金の台帳を渡さないので、段階 2 は腕に依らず挿さらない | 同じ(結果も同じ) |
| 既定と同じ値に腕を押さえる行を消した 7 ファイル・9 か所(〔検収 L8〕前の版は「8 本」と書いていた。試験ごとの行は付録 A-1): `test_stage2_default_2_4.py` 2・`test_rules42b_ledger.py` 2・`test_stage2_resume.py`(slow)・`test_wage_occupation_runs.py`(slow)・`test_wage_occupation.py`・`test_rules42_runs.py`・`test_stage2_calls.py`(off にする 1 行と、続けて on に戻す `set_arm("on")` の 1 行) | 段階 2 on(既定)の各試験 | 腕を既定の on に書く行を消した(②a で属性が無くなる)。消した行は `monkeypatch.setattr(ES2, "_ARM", …)` 9 行と `ES2.set_arm("on")` 1 行 | 同じ |

### 3-2 `--rate-rules legacy` と `--absent-processes legacy`(①b)

| 試験 | 前 | 後 | 同じか |
|---|---|---|---|
| `tests/engine/processes/test_salient.py`(12 本) | モジュールの autouse で両方の切替口の腕を legacy にし、過程の既定で旧道を回す(倒れる → 気づく → 起こす・予算・ablation・出動と到着・B4 の行) | 過程の部品の口(`SalientProcess(rate_rules="legacy")`・`PublicServiceDispatchProcess(absent_processes="legacy")`)を明示 | 同じ |
| `tests/engine/processes/test_rng_scheme_10c.py` のランの外の 14 本(過程を直に作る 10 本と関数の 4 本・試験ごとの行は付録 A-2) | 同じ autouse で、counter の流れ・出動の遅れ・T だけで引く・id の昇順・ポアソンの z | 過程を直に作る所(出動 10 か所=子の型 `Spy` の 1 か所を含む・顕著行為 6 か所)に部品の口を明示(〔検収 L8〕前の版は「9 本」「出動 9 か所」と書いていた) | 同じ |
| 同 ランの 7 本(`test_run_day_passes_day_key0_to_the_counter_key`・`test_run_day_has_no_scheme_argument_and_writes_the_manifest`・`test_counter_run_twice_is_identical`・`test_two_day_counter_keys_carry_T`・`test_counter_adds_no_state_to_restore_and_drops_the_two_generators`・`test_the_tape_carries_the_scheme_and_the_replay_matches`・`test_a_tape_from_before_10e_is_not_replayed`) | 切替口の腕 legacy と `run_day(salient_rate_per_10k=…)` で、ランの中の倒れる・出動の鍵・決定論・状態の道筋・テープの再生 | autouse を §2-2 の助けにし、倒れる率は助けで渡す | 同じ |
| `tests/engine/test_ablation23_switches.py::test_d50_scale_reaches_the_salient_process_through_run_day` | 率の規則の旧道と率 4,000 で、`run_day` の d50 の倍率が顕著行為の過程に届く | 助け(率の規則・率 4,000) | 同じ |
| `tests/engine/test_resume_10d.py::test_counter_rng_resume_draws_once` | 両方の旧道と率 3,000 で、2 日のランの再開=通し・倒れる件数と出動の件数の和が通しと同じ | 助け(両方・率 3,000) | 同じ |
| 同 `::test_daily_tables_are_relaid_from_the_calendar_day` | 率の規則の旧道で、2 日目の頭に W7・納品・工事・宅配の表を暦の日で引き直す(2 日目も配る) | 助け(率の規則) | 同じ |
| `tests/engine/test_salt_seed_split_10f.py::test_population_and_motion_streams_use_their_own_seed_synthetic` | 率の規則の旧道と率 3,000 で、流れごとの seed の分け方(顕著行為の流れも動きの seed) | 助け(率の規則・率 3,000) | 同じ |
| 同 `::test_t3_runner_first_diff_matches_first_diff_py_and_crn_checks` | 回す役 `tools/c7/salt_runs.py`(子のプロセス)に腕「倒れる率 1,000」と環境変数で旧道を渡し、最初の食い違い(salt 1 が刻み 76・salt 2 が 30)・T0 の前の一致・区間の頭まで回して再開してからの細かい探し・CRN の検査・`arm_keys_unseen == ["salient_rate_per_10k"]` | 〔検収 H1 の直し・§10-1〕子のプロセスには助けが届かないので、腕を「納品の過程を切る」(`processes_disabled=["delivery_inbound"]`=05〜08 時の納品が無くなる)に替えた。最初の食い違いは salt 1 が刻み 300・salt 2 が刻み 301(粗い区間 [300, 359]=6 つ目)。退化を止める assert を足した(`want > 0`・どれかの salt で `interval[0] > 0`)。manifest の設定の節に載らない腕なので `arm_keys_unseen == ["processes_disabled"]`。腕から導かれる欄 `ablations`・`process_ids` は `derived_keys` で期待の値を宣言 | 同じ(T0 の前の一致と再開してからの細かい探しの 2 つの道を通る)。① の版(腕 `sleep_suppression=False`)は刻み 0 で食い違い、この 2 つの道を通らなかった=範囲が減っていた(§10-1) |
| 同 `::test_runner_environment_modes` | 同じ道具で環境の seed の決め方(fixed・salt)と空でない置き場で止まる | 腕を「就寝の抑止を切る」に替えた(この試験は腕の中身に依らない) | 同じ |
| `tests/engine/test_state_checks_10f.py::test_k19_runtime_overlaps_only_in_the_allow_list`・`::test_k19_empty_allow_list_reports_every_overlap`(助け `_record`・`k19_runs`) | 率の規則の旧道と率 3,000 の合成 2 日で、全部の乱数の流れの鍵の重なり 0(顕著行為・p_notice の流れを含む)・包まないランと final が同じ | 助け(率の規則・率 3,000。「無い」の過程は前と同じく既定)。`_record` の腕の分かれを消した | 同じ |
| `tests/engine/test_version_bump_10e.py::test_e4_l1_tape_meta_carries_the_rng_layout_and_old_counter_tapes_stop` | 率の規則の旧道と率 30,000 で、テープの脇の meta の印と古いテープの止め方 | 助け(率の規則・率 30,000) | 同じ |
| `tests/engine/test_waste_sink_report.py::test_run_summary_uses_the_store_band_and_lists_three_sources[off・legacy]`・`::test_monthly_census_uses_the_store_band_and_the_store_collected_mass[off・legacy]` | legacy は店の帯で OK/NG を判定する(要約の文・c7lib の読み・月次 MER)・off は非該当 | legacy は助け(率の規則)。月次 MER に渡す腕は切替口の腕から、そのランの実行器の腕に替えた | 同じ |
| `tests/engine/duties/test_du_runs.py::test_discard_is_a_closing_task_and_the_morning_bridge_skips_it` | 率の規則の旧道で、担当は閉店の後に捨て、05:00 のつなぎは担当が捨てた店を捨てない | 助け(率の規則) | 同じ |
| `tests/economy/cp2/test_cp2_event_links.py::test_run_rows_and_events_are_one_to_one` の率の規則の行 | 率の規則の旧道で補充の行を起こし、補充の物の行の目印=代金の行の出来事 | 助け(率の規則)。経済 off の行は止めた(§4) | 同じ |
| `tests/engine/processes/test_rate_rules_1101.py::test_run_manifest_counts_rise_in_legacy_and_are_zero_off`(`day_runs`) | 世界資産 200 体・1 日で、legacy は催し・売れ残り・ポイ捨て・宅配の件数が立ち(manifest の mode=legacy・宅配の印 0)、off は全部 0 | legacy は助け(率の規則)。件数は manifest の `counts` で前と同じに見る。mode の確かめは「実行器の腕=legacy・宅配の過程の印 0」と「manifest の mode は組み立ての腕=off」に替えた | 件数は同じ。manifest の mode=legacy の記録は切替口そのもの(②b で消える) |
| `tests/engine/processes/test_absent_processes_1102.py::test_run_manifest_section`(`tiny_runs`) | legacy の manifest の節(mode=legacy・止めた印 0・電気と水を数える) | legacy は助け(「無い」の過程)。件数は manifest の `counts` で同じに見る。mode の確かめは「実行器と 5 過程の腕=legacy」と「manifest の mode=stopped」に替えた | 件数は同じ。mode の記録は切替口そのもの |
| 同 `::test_runner_hands_the_arm_to_the_five_processes[stopped・legacy・None]` | 切替口の腕を stopped にしてから、実行器が 5 過程に腕を渡す(None=今の腕) | 腕を置く行を消した(None=既定 stopped) | 同じ |

## 4. ①c: off を基準に使う試験を、段階 2 の外の束で書き直した

親の裁定(問い 2)は「手順 0 で部品 none が off と同じなら『段階 2 on・部品 none』で書き直し、同じでなければ止まる」だった。
**部品 none は off と同じではなかった**(§1)ので、① ではいったん止めた。その後の親の答え(①c)で、off と 38/38 同じ値になる
**段階 2 の外の束**(§2-1・試験の中だけの口)で書き直した。部品 none で回す形は採らない(台帳の値が変わる)。切替口 off はまだ
在る(②a で消す)。

### 4-1 書き直した試験(前に確かめていたこと → 後に確かめること)

| 試験 | 前 | 後 | 同じか |
|---|---|---|---|
| `tests/economy/cp2/test_cp2_event_links.py::test_run_rows_and_events_are_one_to_one` | 切替口 off(と率の規則の旧道)で、世界資産 200 体・1 日の金の生ログの目印のある行と出来事の金の行が 1 対 1・原因は鉄道か棚・補充の物の行の目印=代金の行の出来事 | `use_outside_bundle`(cli の台帳を段階 2 の外の形で作る)と §2-2 の助け(率の規則)で同じ確かめ | 同じ |
| `tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py::test_5k_default_day_does_not_overflow`(slow) | 切替口 off の 5,000 体・1 日で、輪の容量 32,500(6.5 行/体/日)・溢れ 0・行/体/日 < 6.5 | `use_outside_bundle` で同じ確かめ | 同じ(下の 4-2 の注) |
| `tests/engine/test_ledger_wiring.py`(ランを回す 12 本=slow の W2 を含む・試験ごとの行は付録 A-3) | モジュールの autouse で切替口 off にして、C4 の帳簿(段階 2 の外)を合成のランに結線したときの状態ハッシュ不変・保存則・検算②・日次センサス・締めた日の行・O(t) の計測・棚の写し・W2 | autouse を外し、台帳を `outside(Ledger)` で作る(`_bundle`)。〔検収 M2〕同じ確かめを段階 2 on の形でも回す(§4-4) | 同じ |
| `tests/economy/stage2/test_stage2_runs.py::test_arm_off_changes_nothing_on_the_ledger` → `::test_a_ledger_outside_stage2_changes_nothing` | 切替口 off のランは段階 2 を挿さない・manifest に段階 2 の欄が無い・生ログの方法の列 0・保存則・`money_stage2_in == 0`・判断の口の段階 2 の欄が無い | 段階 2 の外の台帳(`_run(outside=True)`)で同じ確かめ(名を直した) | 同じ |
| 同 `::test_off_parts_spec_without_the_arm_is_ignored` → `::test_parts_spec_outside_stage2_is_ignored` | 切替口 off なら部品の指定(wages)は効かない(段階 2 が挿さらない) | 段階 2 の外の台帳では部品の指定が効かない(名を直した) | 同じ |
| 同 fixture `arm` と、段階 2 on の 5 本(全部品・部品を 1 つ止める ×5・閉じた ATM・判断の口・ATM の器) | 切替口の腕を off にしてから on に切り替える | 腕に触らない(既定 on)・部品と ATM の表だけ置く | 同じ |
| `tests/economy/stage2/test_stage2_world_two_day.py::test_world_two_days_without_the_arm` → `::test_world_two_days_outside_stage2`(slow) | 切替口 off の世界資産 5,000 体・2 日は段階 2 が挿さらない・雇用主の口 1・manifest に段階 2 の欄が無い・保存則・方法の列 0 | `use_outside_bundle` で同じ確かめ(名を直した) | 同じ |
| 同 `::test_world_two_days_with_the_arm`(slow) | 腕 on を書いてから回す | 腕を書く行を消した(既定 on) | 同じ |
| `tests/economy/stage2/test_stage2_resume_arm.py::test_resume_stops_when_the_arm_or_parts_differ`(E8) | 腕 on のファイルから、部品が違う・腕 off で再開すると止まる・そろえた再開=通し | 腕 off の代わりに、段階 2 の外の台帳で再開すると止まる(今の腕は off と同じ) | 同じ |
| 同 `::test_arm_off_state_files_keep_the_header_and_refuse_an_on_resume` → `::test_state_files_outside_stage2_keep_the_header_and_refuse_a_stage2_resume`(E9) | 腕 off のファイルは見出しに段階 2 を書かない・腕 on で再開すると止まる・見出しに無い=off と同じ | 段階 2 の外の台帳のランのファイルで同じ確かめ。最後は `check_resume(None, effective=False)`(名を直した) | 同じ |

〔検収 L3〕書き直した後は、外の束(助け)そのものを確かめている assert がある。正直に書いておく:

- E13 `test_world_two_days_outside_stage2` の `led.sizes[EMPLOYER] == 1` と、E2 `test_5k_default_day_does_not_overflow` の
  `raw_capacity == 32_500` は、外の束が cli の台帳を作るとき雇用主の口と輪の係数を捨てる(`use_outside_bundle` の型の差し替え)ので、
  必ず真になる。前(切替口 off)は cli の off の分かれがこの値を作っていたので、src の確かめだった。今は助けの確かめ。E2 の
  溢れ 0 と行/体/日 < 6.5 は実測なので、意味は残っている。
- `test_parts_spec_outside_stage2_is_ignored` は、外の台帳が部品の指定に依らず段階 2 を挿さない(`attach_stage2` が無い)ので、
  `test_a_ledger_outside_stage2_changes_nothing` の「段階 2 が挿さらない」と重なる。前(切替口 off)は「off の腕が部品の指定より
  先に効く」という src の分かれの確かめだった。その分かれは ②a で消えた。

### 4-2 切替口 off を消すと一緒に消える確かめ(②a で消す・残すもの)

| 確かめ | 置き場 | ②a の後 |
|---|---|---|
| 既定の腕が on・切替口 off で部品が空になる(`DEFAULT_ARM`・`arm()`・`_ARM`) | `test_stage2_default_2_4.py::test_default_arm_is_on_and_off_is_the_switch` | 消える。「off は消した(名が無い・環境変数で止まる・`active_parts()` は部品そのもの)」の確かめに替える |
| 腕の名の検査(`set_arm("maybe")` で止まる)と off → on の切り替え | `test_stage2_rules_credit_atm.py::test_arm_and_parts_switches` | 消える。部品の切り替えと名の検査は残す |
| cli が切替口 off のときに作る台帳の形(雇用主の口 1・係数 6.5)を、ランの口から選べること | E2・E13・E3(どれも off で cli を回していた) | ランの口からは選べなくなる。同じ形の台帳は試験の中だけの束で作る。E2 の「係数 6.5 で溢れない」は、段階 2 の外の台帳(HEAD の写しとの同値・台帳を直に作る試験)の器の確かめとして残る。ランで使う係数 16.0 は `test_nineteen_configs_stay_under_the_coefficient` が見る |
| 環境変数 `SHIBUYA_ECONOMY_STAGE2` と CLI の旗 `--economy-stage2` が効くこと | (切替口そのもの) | 消える。渡すと止まる、の試験に替える(②a) |

### 4-3 ②b で「消した」の試験にするもの(率と「無い」の過程の切替口そのもの)

`test_rate_rules_1101.py` の 2 本と `--rate-rules on` の 1 行・`test_absent_processes_1102.py` の 3 本(名の検査・見出しと再開・
再開の食い違い)と CLI の 1 本。再開の食い違いは、見出しの無いファイルからの再開で見る形に替える。

〔検収で足した 1 本〕書き直した 27 本の外で、切替口のモジュールの定数を読む試験:
`tests/bridging/test_drives_from_vs_scoring.py::test_engine_stopped_flags`(237〜258 行)。`switch_rate` の `DEFAULT_MODE`・
`MODE_OFF`・`RULES` と、`switch_absent` の `STOPPED_PROCESSES`・`DEFAULT_MODE`・`MODE_STOPPED`・`PROCESSES` を読み、「無い」の台帳の
`engine_stopped`・`engine_now`・`stage` と突き合わせる。②b でモジュールの定数を消すか動かすなら、この試験も書き直す。②b の
ほかの作業は §11。

### 4-4 off を基準にしていた試験と、段階 2 on の道の試験(検収 M2)

ユーザーの指示は「過程の単体試験(段階 2 on)に書き直す」。①c は、off と同じ値になる段階 2 の外の束で書き直した(§0・§4-1)。
親の方針で、**指示の字面どおりの試験(同じことを段階 2 on の道=今のランが通る道で確かめる試験)も在る形にした**。区別:

- **ユーザーの指示の字面(段階 2 on)に当たる試験**: 台帳が段階 2 の口を持ち、組み立てが段階 2 を挿す(既定のランと同じ道)。
  下の表の「段階 2 on の道の試験」の欄。
- **基準の口(外の束)に当たる試験**: 段階 2 の口を持たない台帳(試験の中だけの束 `tests/economy/_stage2_outside.py`)で、前の
  切替口 off と同じ値を確かめる。根拠は仮決定「部品の単体試験の基準の口は残す(ランの口からは選べない)」(返事その 8 §1-10・
  第346 の 6-1 メモ Q6)。下の表の「試験」の欄(①c で書き直したもの)。残すか消すかはユーザーに聞く(仮採用・戻し方=外の束の
  試験と助けを消す)。

| 試験(基準の口=外の束) | 確かめていること | 段階 2 on の道の試験 | 足したか・期待値の出どころ |
|---|---|---|---|
| E1 `tests/economy/cp2/test_cp2_event_links.py::test_run_rows_and_events_are_one_to_one` | 世界資産 200 体・1 日のランで、金の生ログの目印のある行=出来事の金の行(1 対 1)・語と科目・額・原因(rail か shelf)・日次の記録の数・補充の物の行の目印=代金の行の出来事 | `tests/economy/cp2/test_cp2_event_links.py::test_run_rows_and_events_are_one_to_one_on_stage2`(新) | **足した**。前は無かった(段階 2 の単体の試験 `test_stage2_calls.py` は台帳を直に作って行ごとの原因を見るだけで、ランの 1 対 1 は見ていない)。同じ 1 対 1 に、段階 2 の語(カード・引き出し=科目は預金純増)と原因(呼・ATM)を足した。期待値は段階 2 on のラン(世界資産 200 体・seed 1・既定 v3・1 日・率の規則の旧道の助け・部品は全部・ATM は OSM の表)から取り直した: 金の出来事 503 行=消費支出 253(原因=呼)・カード 121(rail)・持ち出し 121(rail)・引き出し 7(呼 6・ATM 1)・域外仕入 1(shelf)・原因の無い行 2,937・生ログ 3,440 行・溢れ 0。語ごとに許す原因の表 `_STAGE2_CAUSES` に置いた |
| E2 `tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py::test_5k_default_day_does_not_overflow`(slow) | 5,000 体・1 日で、輪の容量 32,500(6.5 行/体/日)・溢れ 0・行/体/日 < 6.5 | `tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py::test_nineteen_configs_stay_under_the_coefficient[19 構成]`(slow・5,000 体・容量 80,000=16.0 行/体/日・溢れ 0・行/体/日 < 16.0)と `tests/economy/stage2/test_stage2_world_two_day.py::test_world_two_days_with_the_arm`(slow・5,000 体・2 日・容量 80,000・溢れ 0) | 在る(足していない) |
| E3 `tests/economy/cp2/test_cp2_nine_ops_equivalence.py::test_5k_mock_day_matches_head[6.5・3.0]`(slow) | HEAD 136fdbb の台帳の写しと今の台帳の 5,000 体・1 日の final・呼数・金と物の台帳の状態・世帯の現金が同じ | — | **段階 2 on では成り立たない**(HEAD の写しは段階 2 を持たない=段階 2 on の台帳は初期の預金から違う)。外の束でだけ確かめられる |
| E4 `tests/engine/test_ledger_wiring.py`(ランを回す 12 本と、組み立てを通らない 4 本) | 合成のランに C4 の帳簿を結線したときの状態ハッシュ不変・保存則・検算②・日次センサス・締めた日の行・O(t) の計測・棚の写し・W2・手回しの刻みの検算②・補充・廃棄物・消費 | 同じファイルの同じ試験の `[stage2]` の場合(新)・状態ハッシュ不変は `[stage2_parts_none]`(新)。名は付録 A-3 | **足した**。前は無かった(段階 2 on のランの試験 `tests/economy/stage2/test_stage2_runs.py` は段階 2 の流れと保存則を見るが、C4 の帳簿の配線=検算②・センサスの締めた日の行・O(t)・棚の写し・W2 は見ていない)。同じ試験を台帳の 2 つの形で回す(`KINDS`)。段階 2 on は、ランでは素の `Ledger`(組み立てが段階 2 を挿す・部品は全部)、組み立てを通らない 4 本では試験の代役の組み立ての物で挿す。取り直した期待値(合成 64 セル・500 体・seed 2・1 日): 店の現金 134,800=売上の写し 122,616+レジの税 12,184−域外仕入 0(段階 2 の外は 138,200=売上)・消費支出(世帯 → 店)134,800=売上+税。状態ハッシュ不変は、部品が全部だと引き出し・口座払い・税で世帯の現金と購入が動く(購入 168 対 169・世帯の現金 3,622,366 対 3,351,439)ので、段階 2 on・部品 none(初期の預金だけ=手順 0 で体の動きが off と同じ形)で見る。そのほかの値(検算②・センサス・faucet と sink の科目・O(t)・棚の写し・溢れ 0)は 2 つの形で同じ期待値のまま通った |
| E8 `tests/economy/stage2/test_stage2_resume_arm.py::test_resume_stops_when_the_arm_or_parts_differ` | 段階 2 on のファイルの見出し(腕・部品・賃金・規則)・部品が違う再開は止まる・**外の台帳への再開は止まる**・そろえた再開=通し | 同じ試験の段階 2 on の部分(見出し・部品の違いで止まる・そろえた再開=通し)と `tests/economy/stage2/test_stage2_resume.py::test_resume_equals_straight_with_the_arm[1440・2190]`(slow) | 在る(足していない)。外の台帳への再開(太字)は段階 2 の外が要る=段階 2 on だけでは成り立たない |
| E9 `tests/economy/stage2/test_stage2_resume_arm.py::test_state_files_outside_stage2_keep_the_header_and_refuse_a_stage2_resume` | 段階 2 の外のランのファイルは見出しに段階 2 を書かない・段階 2 on で再開すると止まる・見出しに無い=外どうし | 段階 2 on の側(見出しに書く・そろえた再開は通る)は E8 の同じ試験 | **段階 2 on では成り立たない**(段階 2 の外のファイルの性質)。外の束でだけ確かめられる |
| E11 `tests/economy/stage2/test_stage2_runs.py::test_a_ledger_outside_stage2_changes_nothing` | 段階 2 の外の台帳のランは段階 2 を挿さない・manifest に段階 2 の欄が無い・方法の列 0・保存則・`money_stage2_in == 0`・判断の口の段階 2 の欄が無い | 段階 2 on の側(段階 2 が挿さる・manifest の段階 2 の欄・保存則・`money_stage2_in`=現金の項 − レジの税・`conserved`)は `tests/economy/stage2/test_stage2_runs.py::test_all_parts_move_money_and_keep_the_books`。方法の列(口座=1)は単体の `tests/economy/stage2/test_stage2_account_and_conservation.py::test_account_payee_puts_the_money_in_the_deposit_and_leaves_cash_alone` が見る(ランでは見ていない) | 「何も変えない」は**段階 2 on では成り立たない**(段階 2 は台帳を変えるのが役目)。段階 2 on の側の欄は在る(足していない) |
| E11 `tests/economy/stage2/test_stage2_runs.py::test_parts_spec_outside_stage2_is_ignored` | 段階 2 の外の台帳では部品の指定が効かない | 段階 2 on では部品の指定が効く: `tests/economy/stage2/test_stage2_runs.py::test_turning_one_part_off_zeroes_its_flow[wages・withdraw・payment・tax・visitors]` と `tests/economy/stage2/test_stage2_rules_credit_atm.py::test_parts_switches` | 在る(足していない)。外の束の側は §4-1 の注のとおり 1 本目と重なる |
| E13 `tests/economy/stage2/test_stage2_world_two_day.py::test_world_two_days_outside_stage2`(slow) | 世界資産 5,000 体・2 日の段階 2 の外の台帳: 段階 2 が挿さらない・雇用主の口 1・manifest に段階 2 の欄が無い・保存則・方法の列 0 | `tests/economy/stage2/test_stage2_world_two_day.py::test_world_two_days_with_the_arm`(slow・同じラン・雇用主の口 9,872・保存則・給料日・容量 80,000) | 在る(足していない) |

- E1 の off の行の「off」は、①c の前の `test_run_rows_and_events_are_one_to_one` が切替口 off で回っていたこと。E11 の 2 本の前の
  名は `test_arm_off_changes_nothing_on_the_ledger`・`test_off_parts_spec_without_the_arm_is_ignored`。
- 足した試験の結果は §10-4。

## 5. 見つけた欠陥の直し(`tests/engine/test_removed_switches_346.py::_system_frames` の空振り)

- 欠陥: traceback から系の置き場を拾う文字列が `/engine/systems/`、刻みの前の置き場が `{"conductor.py", "build.py"}` だった。
  移す段 4(`engine/systems/build.py` → `runtime/systems/assemble.py`)の後は何も拾わない。このため「消した切替口の環境変数は
  刻みの前で止まる」の確かめ(`set(frames) <= _BEFORE_TICKS`)が、いつも空の集合で通っていた。
- 直し: 置き場の文字列と刻みの前の名を、モジュールの名(`shibuya.runtime.systems.conductor`・`…assemble`)から作る。置き場が
  動いても追う。`frames[-1] == "build.py"` も `assemble.py` に。
- 負の対照 `test_the_frame_check_catches_a_stop_inside_the_ticks` を足した。子のプロセスで `resolve.advance_body`(本人の体の系が
  毎刻み呼ぶ)を止めると、拾う置き場に刻みの中の `body.py` が出て、刻みの前の確かめが落ちる形になることを見る。
- 直す前と後の確かめ(同じ子のプロセスの traceback): 直す前の文字列で拾った置き場は `[]` で、確かめ `set(frames) <= {conductor.py,
  build.py}` は**真=空振り**。直した後は `['conductor.py', 'conductor.py', 'conductor.py', 'body.py']` で、確かめ
  `set(frames) <= {conductor.py, assemble.py}` は**偽=刻みの中の止まりを見つける**。直した後も、消した切替口 5 本 × 値 2 つ × 入口 2 つの
  試験は通った(止まった所は組み立ての最初か読み込み)。

## 6. 次の版上げで扱う行(今回は触らない=manifest・つなぎの台帳・世界の台帳のハッシュが動く)

親の裁定(問い 6・②b の台帳の 3 行・問い 7・8)により、次の行と文は今回は触らない。②a〜③b でも manifest・つなぎの台帳・
世界の台帳のハッシュを動かさないため。

| 行・文 | 置き場 | 次の版上げですること | 今回触らない理由 |
|---|---|---|---|
| `DOC-s2rates-legacy-switch`(next-bump) | `docs/design/bridging-ledger.json` | removed(切替口 `--rate-rules legacy` を消した・旧値の再現は安定版のタグ・部品の口は残る) | `bridges_count`・`bridges_version` が動く |
| `DOC-s2e-absent-legacy-switch`(next-bump) | 同 | removed(`--absent-processes legacy`) | 同 |
| `DOC-s2rates-collapse-test-knob`(next-bump) | 同 | removed(`run_day(salient_rate_per_10k=)` は None 以外で止める=案 k1・`SalientProcess` と実行器の部品の口は残る) | 同 |
| `BR-NAV1-LEGACY-SWITCH`(next-bump・コードの宣言) | 台帳と `src/shibuya/world/model/space/nav1.py` の `NAV1_EXPEDIENTS` の 1 項 | removed にして項を消す(または文を「試験の中だけの口」に) | manifest の `space.expedients` が動く・`declared_in` の sha |
| `DOC-nav1-arms-inert-edge-plateau`(next-bump) | 台帳 | edge と plateau の腕の扱いを決め直す(legacy のランでしか効かない) | 腕の扱いの判断(範囲の外) |
| `BR-NAV1-E5`(7・文に「legacy の切替口を消すとき」) | 台帳と `NAV1_EXPEDIENTS` の項 | 文の外す段を直す(合成の世界の戻り道は残る) | `declared_in` の sha・manifest の `space.expedients` |
| `world/ledger/absent.py` の `_RATE_OFF`・`_ABSENT_OFF` の文(「旧道 `--rate-rules legacy` では…が動く(1 版だけ)」)と各行の `stage="next-bump"` | `src/shibuya/world/ledger/absent.py` | 文を「部品の口だけ」に・外す段を直す | 世界の台帳のハッシュ(manifest の `registry_hash`)が動く |
| routing の DEC の next-bump の 15 行(#2・3・10・22・42・43・83・99・101・103・104・105・106・110・111) | 台帳 | (裁定 7=触らない) | 判断の行き先の行 |
| 経済の段階 2 の off・`--hunger-model v1` | (台帳に行は無い) | 記録だけ(Q12) | — |

## 7. 試験の結果

作業の木で、ファイルごとに `-m "not gpu and not slow"`・`-n` なしで回した。前=頭 `ff28372d`(書き直す前の同じファイル)。
①=頭 `ff28372d` で ①a・①b を当てた後。①c=頭 `d42fbba0`(段 4-12 まで)へ移した後(①a・①b・①c のすべて)。

〔検収 L8〕表は 28 行=書き直した試験のファイル 26 本と、変えていないが助け `_md.py` を読む md23 の 2 本
(`test_md23_resume.py`・`test_md23_body_events.py`)。助けのファイル(`_md.py`・`_stage2_outside.py`・`_legacy_world.py`)は
試験を持たないので載せていない。①c の欄の和は 421(26 本で 402+md23 の 2 本で 19)。commit 73c2f5fb の文の「418 passed」は、
親の手元の実行の記録(作業の機械のスクラッチの `pytest_step1.log`)の進みの点の数(要約の行が無い・失敗と skip の印は 0)。
26 本だけなら 402(commit 73c2f5fb の木でも同じ=今の木の集まり 425 から ②a の +7 と本段の +16 を引いた数)。これに
`tests/test_places_guard.py` の 16 本を足すと 418 で合う(本段の実行で places の試験は 16 本だった=§10-4)。ただし、その実行の
対象の範囲は記録に無いので、内訳は数の一致からの推測。本段(§10)の後の数は §10-4。

| ファイル | 前 | ① | ①c(移した後) | 本数の差 |
|---|---:|---:|---:|---|
| `tests/engine/test_removed_switches_346.py` | 19 | 20 | 20 | +1(負の対照 §5) |
| `tests/economy/cp2/test_cp2_nine_ops_equivalence.py` | 38 | 38 | 38 | 0(slow 2 は選ばない) |
| `tests/economy/cp2/test_cp2_event_links.py` | 9 | 9 | 9 | 0 |
| `tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py` | (同じ関数 9) | — | 15(slow 20 は選ばない) | 0(関数の数は同じ) |
| `tests/engine/test_ledger_wiring.py` | (同じ関数 17) | — | 16(slow 1 は選ばない) | 0 |
| `tests/economy/stage2/test_stage2_runs.py` | (同じ関数 7) | — | 11 | 0(名を直した 2 本を含む) |
| `tests/economy/stage2/test_stage2_resume_arm.py` | (同じ関数 2) | — | 2 | 0(名を直した 1 本を含む) |
| `tests/economy/stage2/test_stage2_world_two_day.py` | 0(全部 slow) | — | 0(slow は下で回した) | 0 |
| `tests/engine/multiday/test_md23_resume.py` | 4 | 4 | 4 | 0 |
| `tests/engine/multiday/test_md23_body_events.py` | 15 | 15 | 15 | 0 |
| `tests/economy/stage2/test_stage2_default_2_4.py` | 4 | 4 | 4 | 0 |
| `tests/economy/stage2/test_stage2_resume.py` | 0(全部 slow) | 0 | 0 | 0 |
| `tests/economy/stage2/test_wage_occupation_runs.py` | 0(全部 slow) | 0 | 0 | 0 |
| `tests/economy/test_wage_occupation.py` | 19 | 19 | 19 | 0 |
| `tests/economy/test_rules42b_ledger.py` | 7 | 7 | 7 | 0 |
| `tests/economy/test_rules42_runs.py` | 6 | 6 | 6 | 0 |
| `tests/economy/stage2/test_stage2_calls.py` | 8 | 8 | 8 | 0 |
| `tests/engine/processes/test_salient.py` | 12 | 12 | 12 | 0 |
| `tests/engine/processes/test_rng_scheme_10c.py` | 21 | 21 | 21 | 0 |
| `tests/engine/test_ablation23_switches.py` | 39 | 39 | 39 | 0 |
| `tests/engine/test_salt_seed_split_10f.py` | 17 | 17 | 17 | 0 |
| `tests/engine/test_version_bump_10e.py` | 22 | 22 | 22 | 0 |
| `tests/engine/test_waste_sink_report.py` | 6 | 6 | 6 | 0 |
| `tests/engine/processes/test_rate_rules_1101.py` | 20 | 20 | 20 | 0 |
| `tests/engine/processes/test_absent_processes_1102.py` | 22 | 22 | 22 | 0 |
| `tests/engine/test_resume_10d.py` | 38 | 38 | 38 | 0 |
| `tests/engine/test_state_checks_10f.py` | 24 | 24 | 24 | 0 |
| `tests/engine/duties/test_du_runs.py` | 26 | 26 | 26 | 0 |

- 落ちた試験 0・誤り 0。警告は `WageTablesAbsentWarning`(作業の木の data のつなぎに賃金の表の写しが無い)などで、前から出るもの。
- 「前」の欄が「同じ関数 N」の 4 ファイルは ①c で初めて書き直した。前の頭では回していない。関数の数(`def test_`)は前と同じ。
- slow(書き直した分は単独で回した): `test_cp2_nine_ops_equivalence.py::test_5k_mock_day_matches_head[6.5・3.0]`(E3)=2 passed
  (3 分 13 秒・頭 `ff28372d`)/`test_cp2_k17_capacity_and_overflow.py::test_5k_default_day_does_not_overflow`(E2)と
  `test_stage2_world_two_day.py` の 2 本(E13 ほか)=3 passed(4 分 5 秒・頭 `d42fbba0`)。`test_stage2_resume`・
  `test_wage_occupation_runs` は既定と同じ値を置く 1 行を消しただけで、回していない(集めて 2 本と 3 本)。
- src に差が無い: 実装役の確かめ(頭 `d42fbba0` で `git status --short src` は空・`tools/bytecheck/astsame.py --base HEAD` は
  「変わったファイル 0 本」=記録のファイルは残していない)。リポの [astsame_step1.json](astsame_step1.json) は親の記録で、base は
  `09365c41`(commit 73c2f5fb の親)・比べる側は作業の木(〔検収 L8〕前の版はこの 2 つを区別していなかった)。
- `tests/test_places_guard.py`・`tests/c8/test_places_rule_copies.py`: 26 passed。
- カード `tools/repo_guide/build.py` で作り直した(`cards/data.md` は戻した)。`--check` は「最新」(152 本=頭 `d42fbba0` の上の数。
  commit 73c2f5fb の頭は段 4-13 の後で census のカードが 1 本消えているので 151 本=commit の文の数。〔検収 L8〕)。
- 頭を移したとき(`stash push -u` → `merge --ff-only` → `stash pop`): 試験のファイルはぶつからなかった(`test_du_runs`・
  `test_removed_switches_346`・`test_salt_seed_split_10f` は自動で混ぜた=段 4 の import の書き換えと本段の変更が両方入った)。
  ぶつかったのはカード 5 本(`cards/README.md`・`docs.md`・`src/shibuya/engine/README.md`・`tests/engine/README.md`・
  `tests/engine/duties/README.md`)で、新しい頭の版を取ってから作り直した。stash の写しは確かめてから消した。

## 8. 道具

- [tools/step0_parts_none.py](tools/step0_parts_none.py): 手順 0 のラン(1 回 1 構成 1 腕=`off`・`none`・`noattach`)。
- [tools/step0_legacy_helper.py](tools/step0_legacy_helper.py): 手順 0 の続き(切替口の腕と §2-2 の助けが同じランになるか)。
- [tools/step0_compare.py](tools/step0_compare.py): 2 つの JSON の欄ごとの一致。
- どれも切替口が在る木(②a・②b の前)でだけ回る。結果の JSON はリポに入れていない。

## 9. ②a: 経済の段階 2 の切替口 off を消した(1 バイト不変の見込み・byte-check は親)

土台は頭 `73c2f5fb`(① の commit・安定版のタグ `stable-v2-before-switch-removal-347`=5 本の口が全部在る最後の commit)。
旧値の再現は `git checkout stable-v2-before-switch-removal-347`。

### 9-1 消した名・残した名・足した止め

| 置き場 | 消した | 残した(理由) | 足した |
|---|---|---|---|
| `src/shibuya/economy/stage2_bind.py` | 環境変数 `SHIBUYA_ECONOMY_STAGE2` の読み・`_ARM`・`arm`・`set_arm`・`DEFAULT_ARM`・`ARMS`(`__all__` から外した)・`active_parts` の off の分かれ(空を返す)・`attach` の早い戻り(off なら None)・`check_resume` の今の腕(`_ARM`)と文の旗の名 | `ARM_OFF`・`ARM_ON`(見出しの値と、見出しに無いときの読み)・見出しの鍵 `economy_stage2`(`header_fields`)・manifest の `economy.stage2.arm`="on"・部品の腕(`parts`・`set_parts`・`parse_parts`・`active_parts`・`SHIBUYA_ECONOMY_STAGE2_PARTS`)・`set_atm_table`・段階 2 の口を持たない台帳と金の台帳の無いランの道(`attach` が None・`check_resume(effective=False)`) | `ENV_REMOVED`="SHIBUYA_ECONOMY_STAGE2" と読み込みの止め(`stop_if_set`)・`check_resume` の文に安定版のタグ |
| `src/shibuya/cli.py` | `build_ledger_bundle` の off の分かれ(雇用主の口 1・輪の係数 6.5)・ランの種類の腕の数えの 1 項(`_ES2.arm() != DEFAULT_ARM`)・旗 `--economy-stage2`・`set_arm` の呼び出し | on の分かれ(雇用主の口=W6 の組織の数・係数 16.0)・`--economy-stage2-parts` | `--economy-stage2-parts` の help に「切替口 off は消した」 |
| `src/shibuya/foundation/arms/removed.py` | — | 第346 の行と文(前のまま) | `REMOVED_ENV` に `SHIBUYA_ECONOMY_STAGE2`・`REMOVED_CLI_FLAGS` に `--economy-stage2`(`--economy-stage2-parts` の頭=表に出さない旗で受けて止める)・安定版のタグを名ごとに引く `tag_of`・`REMOVED_SWITCH_TAG_347`。ランの入口の止め(`check_environment`)は一覧を見るので自動で入る |
| `src/shibuya/economy/stage2.py` | — | — | docstring の頭と腕の段落(「既定 off」「`--economy-stage2 {off,on}`」の古い文)を直した |
| `tools/bytecheck/configs.py` | `SWITCH_ENV` の `SHIBUYA_ECONOMY_STAGE2` | — | `REMOVED_ENV` に足した |
| `docs/bench/analysis/wallbounce-1012/md23/tools/multiday_md23.py` | `set_arms` の `ES2.set_arm` | 組 c・d の `economy_stage2: on`(記録の鍵) | `on` 以外は「消した切替口・タグ」で止める |

直していない注(経緯の注・`--economy-stage2 on` の言い方が残る): `runtime/systems/table.py:30`・`runtime/systems/boxes.py:473`・
`runtime/state/ledger.py:890・895・911・922`(状態台帳の alloc の文=manifest に出ない)・`mind/judge/decision/layer.py:243`・
`economy/accounts.py:278`・`economy/ops.py:45`・`economy/ledger.py:400`・`foundation/manifest/sections.py:194`。
直していない記録の道具(試験が読まない=346 の前例): `docs/bench/analysis/s2-rules-1101/tools/measure_shortfall.py`・
`wallbounce-1012/ec21/tools/stage2_two_day.py`・`wallbounce-1012/vb24/tools/resume_vb24.py`・本書の `tools/step0_parts_none.py`
(今の src では止まる・旧値は安定版のタグで回す)。

1 バイト不変の見込みの理由: 消した分かれは、どれも既定(on)では通らない分かれだった。19 構成は `cli.run` を直に呼ぶ
(argparse を通らない)。組 `all19` の環境変数は空。土台の側(`73c2f5f`)も同じ 19 構成を環境変数なしで回す(土台の
`stage2_bind` は `SHIBUYA_ECONOMY_STAGE2` が無ければ既定 on)。

### 9-2 替えた試験(前に確かめていたこと → 後に確かめること)

| 試験 | 前 | 後 | 同じか・減ったか |
|---|---|---|---|
| `tests/economy/stage2/test_stage2_default_2_4.py::test_default_arm_is_on_and_off_is_the_switch` → `::test_stage2_is_always_on_and_the_off_switch_is_removed` | 既定の腕が on・切替口 off で部品が空 | 腕を選ぶ名(`ARMS`・`DEFAULT_ARM`・`_ARM`・`arm`・`set_arm`)が無い・部品はいつも効く・消した環境変数の名とタグが止める一覧にある・`ARM_ON`/`ARM_OFF` は残る | 切替口そのものの確かめ=「消した」に替えた(off の道は消えた) |
| `tests/economy/stage2/test_stage2_rules_credit_atm.py::test_arm_and_parts_switches` → `::test_parts_switches` | 腕の off → on と名の検査・部品の切り替えと名の検査 | 部品の切り替えと名の検査(腕の行を消した) | 部品は同じ。腕の名の検査は消えた(腕が無い) |
| `tests/engine/test_removed_switches_346.py::test_the_list_and_the_message_are_in_one_place` | 一覧の集合(5 本・旗 3 本)・文にタグ(346) | 集合に経済の段階 2 の 1 本と旗 1 本を足した・名ごとのタグ(`tag_of`)・第346 の行の文は前のまま・第347 の行の文 | 同じ+足した名 |
| 同 `::test_a_run_with_a_removed_switch_env_stops_before_the_ticks` | 消した 5 本 × 値 2 × 入口 2(子のプロセス) | 6 本(`SHIBUYA_ECONOMY_STAGE2` が自動で入る)・文のタグは名ごと | 同じ+足した名 |
| 同 `::test_a_removed_cli_flag_stops_even_when_abbreviated` | 旗 3 本と略記 | `--economy-stage2 off`・`on`・`=off`・値なしを足した(部品の腕の略記として通らない) | 同じ+足した名 |
| 同 `::test_the_parts_flag_still_works_and_is_not_read_as_the_removed_flag`(新) | — | 残す `--economy-stage2-parts` の名の誤りは部品の文で止まる(消した切替口の文でない) | 足した |
| 同 `::test_the_hidden_flags_are_not_in_the_help` | 消した旗が help に出ない | `--economy-stage2` も一覧から自動で入る | 同じ+足した名 |

確かめる範囲が減った所: 切替口そのものの確かめ(腕の名・off → on の切り替え・off で部品が空)だけ。切替口 off を使って
基準を作っていた試験は ①c で段階 2 の外の束に移したので、確かめる値は減っていない(§4)。

### 9-3 試験の結果

- 1 本の pytest(`-m "not gpu and not slow"`・`-n 4 --dist loadfile`): `tests/economy/stage2`・`tests/economy/cp2`・
  `tests/economy/test_wage_occupation.py`・`test_rules42b_ledger.py`・`test_rules42_runs.py`・`tests/engine/test_removed_switches_346.py`・
  `tests/engine/test_ledger_wiring.py`・`tests/engine/multiday`(md23 の道具を読む)・`tests/tools/test_bytecheck.py`・`tests/test_cli*.py`
  (5 本)・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/test_pop_w21_world.py`・`tests/engine/state/test_class_ids.py`・
  `test_names_frozen.py`・`tests/test_places_guard.py` で **503 passed・0 failed・0 skipped**(3 分 6 秒)。警告は前から出る
  `WageTablesAbsentWarning`(作業の木の data のつなぎ)と W9 の影の `WeatherWarning`。
- `lint-imports`: 12 kept・0 broken。
- カード `tools/repo_guide/build.py` で作り直した(`cards/data.md` は戻した)。`--check` は「最新」(151 本)。
- byte-check の道具: 組 `all19`・`parent4` の環境変数は空。19 構成の引数に経済の腕は無い。`SHIBUYA_ECONOMY_STAGE2` は
  `REMOVED_ENV` へ移した。土台 `73c2f5f` の側も同じ 19 構成を環境変数なしで回す(土台の `stage2_bind` は環境変数が無ければ
  既定 on)。byte-check は親が回す。

### 9-4 親の確かめ(②a)

- byte-check: 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・final が同じ 19(基準 `73c2f5f`=① の commit・比べる側=②a の src。
  既定 `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。全体の壁時計 435 秒)。組は [bytecheck_2a/](bytecheck_2a/)。
- 範囲の試験(`tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`・linked の作業木): 6,826 passed・1 failed・
  21 skipped・1 xfailed(36 分 27 秒)。落ちた 1 本は前からの `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`
  (linked の作業木でだけ落ちる=段 4 の記録と同じ)。
- 例外(ignore)の本数は変わらない(割る段ではない=31 本・延べ 45 行)。`lint-imports` 12 kept。

## 10. ① の検収の直し(試験と記録だけ・src は変えていない)

独立の検収役が ①(commit 73c2f5fb)を読み、条件つきの受け入れになった(高 1・中 2・低 10)。その直しを ②b の前に 1 つの段として
済ませた。土台は頭 `231d9fd0`(②a の commit)。src は変えていない。L10(commit の trailer)は親が扱う。

### 10-1 高 H1: T3 の試験の腕(確かめる範囲が減っていた)

- 何が起きていたか: ① で腕を `sleep_suppression=False` に替えた。この腕は salt 1・2 とも刻み 0 で食い違う。このため
  (1) T0 の前の一致(`pre_t0_match`)は 0 個の checkpoint を比べて真になり、(2) 回す役 `tools/c7/salt_runs.py::_fine_first_diff` の
  `start > 0` の道(区間の頭まで回して状態を書き、再開して毎刻みで回す)を通らず、(3) 細かい探しは区間 [0, 59] の左端を返すだけ
  だった。前の腕(旧道の倒れる率 1,000)は salt 1 が刻み 76・salt 2 が刻み 30 で、この 2 つの道を通っていた。① の記録は「同じ」
  「刻み 59」と書いていた(刻み 59 は粗い点で、細かい最初の食い違いは刻み 0)。
- 腕を探した(`run_day` の今の引数だけ・src に口は足していない)。どれも 200 体・合成の世界・母集団の seed 1・毎刻みの
  checkpoint の通しのランで、最初の食い違いの刻み:

| 腕(`run_day` の引数) | salt 1 | salt 2 | 試した者 |
|---|---:|---:|---|
| `processes_disabled=["delivery_inbound"]`(納品の過程を切る) | **300** | **301** | 実装役(**選んだ**) |
| `processes_disabled=["waste_collection"]` | 1,140 | 1,140 | 実装役 |
| `sleep_suppression=False`(① の腕) | 0 | 0 | ①・検収役 |
| `energy_rate="bmr"`・`memory="on"` | 0 | — | 実装役 |
| `budget=50` | 0 | 0 | 検収役 |
| `processes_disabled=["press"]`・`["shelf_stock_restock"]`・`["opening"]`・`seat_area_eatery_m2=0.5`・`eatery="place_food"`・`conv_max_participants=3`・`meal_sleep_defer="on"`・`weather_perturb=True`・`hunger_words="all"` | 1 日を通して食い違わない | (`shelf_stock_restock`・`opening` は salt 2 も同じ) | 実装役 |
| `p_notice_d50_scale=0.5`・`p_notice_ablation="A1"` | 1 日を通して食い違わない | 同じ | 検収役 |

- 選んだ腕: 納品の過程を切る。納品は 05:00〜08:00 の窓の中で日の鍵から引いた時刻に入る(`world/laws/goods_flow.py` の
  `DELIVERY_WINDOW`)ので、窓の頭から後だけ食い違う。salt 1 は刻み 300(粗い区間 [300, 359] の左端)、salt 2 は刻み 301
  (左端でない=端で間違える実装なら落ちる)。どちらも粗い区間の 6 つ目=T0 の前の 300 個・301 個の checkpoint を比べ、再開して
  からの細かい探しの道を通る。回す役の記録では、細かい探しは salt ごとに区間 [300, 359] の checkpoint 60 個を比べた。
- 足した assert: `want > 0`(salt ごと=T0 の前を比べる)と、どれかの salt で `index["first_diff_fine"][salt]["interval"][0] > 0`
  (再開の道を通る)。
- 「manifest の設定の節に載らない腕は報告に出る(落とさない)」も前の腕と同じ形で戻った: `processes_disabled` は設定の節に
  載らない=`arm_keys_unseen == ["processes_disabled"]`。ただし腕から導かれる設定の欄が 2 つある(`ablations` に過程 id と感度試験
  id `AB-DELIVERY-FREQ`・`process_ids` から過程が外れる)。CRN の検査の口 `derived_keys` に期待の値を書いて宣言し、宣言と実際の
  食い違い 0(`arm_keys_derived_mismatch == []`)を見る。① の版の「同じランの記録に載らない腕の名を足して `input_match` を呼ぶ」
  確かめは要らなくなったので外した。
- 回した: `test_t3_runner_first_diff_matches_first_diff_py_and_crn_checks` 1 passed(51 秒)。

### 10-2 中 M1: 助けで回した旧道のランの manifest

§0・§1・§2-2 の文を直した。道具 [tools/step0_legacy_helper.py](tools/step0_legacy_helper.py) は、過程の計数から名に removed・stopped を
含む鍵を外すのをやめ、manifest の印の節(`rate_rules.removed`・`absent_processes.stopped`)を出す形にして回し直した(§1 の表)。

### 10-3 中 M2・低 L1〜L3・L8・L9

- M2: §4-4 の表。足した試験は E1 の 1 本と E4 の段階 2 on の場合 16(付録 A-3)。
- L1: `test_ablation23_switches.py::test_d50_scale_reaches_the_salient_process_through_run_day` と
  `test_version_bump_10e.py::test_e4_l1_tape_meta_carries_the_rng_layout_and_old_counter_tapes_stop` に、助けが効いていることの正の
  assert を足した(実行器の腕=legacy・倒れる件数 > 0・旧道の印 0。d50 は気づく候補 > 0 も)。取り直した値: d50 は 300 体・30 刻みで
  倒れる 1・気づく候補 12。e4_l1 は 40 体・120 刻みで倒れる 10。助けを外すと倒れる 0・印 1 になる(同じ引数で回して確かめた)。
- L2: `test_stage2_default_2_4.py::test_revenue_is_tax_exclusive_on_a_synthetic_run` の条件つき skip(段階 2 が挿さらなければ
  飛ばす)を、落ちる assert に替えた。部品をモジュールの既定に押さえ、税 > 0 も見る。今の src で `stage2 is None` になるのは
  `stage2_bind.attach` が台帳に `attach_stage2` を見つけないときだけで、`cli.build_ledger_bundle` は段階 2 の口を持つ型
  (`Ledger`・`_HouseholdWalletLedger`)だけを作る=cli のランでは起きない(試験の中だけの束を差し込んだときだけ)。
- L3: §4-1 の表の後の注。
- L8: §0(27 本の数え方)・§3-1(7 ファイル・9 か所)・§3-2(出動 10 か所・過程を直に作る 10 本と関数の 4 本)・§7(28 行・カードの
  本数・astsame の base・「418 passed」)。
- L9: 付録 A。

### 10-4 試験の結果(本段)

- 1 本の pytest(`-m "not gpu and not slow"`・`-n 4 --dist loadfile`・作業の木・頭 `231d9fd0`): 変えた試験の 6 ファイル
  (`test_salt_seed_split_10f.py` 17・`test_cp2_event_links.py` 10・`test_ledger_wiring.py` 31・`test_ablation23_switches.py` 39・
  `test_version_bump_10e.py` 22・`test_stage2_default_2_4.py` 4)と `tests/test_places_guard.py` 16(記録の文の守り)で
  **139 passed・0 failed・0 skipped**(1 分 34 秒)。警告は前から出る `WageTablesAbsentWarning`(作業の木の data のつなぎ・段階 2 を
  代役の組み立ての物で挿した 4 本でも出る)と W9 の影の `WeatherWarning`。
- 本数の差: `test_ledger_wiring.py` 16 → 31(段階 2 on の場合 +15)・`test_cp2_event_links.py` 9 → 10(段階 2 on の 1 本)。
  ほかは本数が同じ(assert を足しただけ)。
- slow(単独で回した): `test_ledger_wiring.py::test_w2_five_thousand_agents_with_the_ledger_wired[outside・stage2]`=2 passed
  (2 分 23 秒。台帳ありの壁時計は外 18.05 秒・段階 2 on 18.10 秒・台帳なし 17.4 秒=報告閾値 60 秒の内)。
- 手順 0 の続きの道具を回し直した(§1 の表・§10-2)。
- src に差が無い: `git status --short src` は空(astsame は親が記録する)。
- カード `tools/repo_guide/build.py` で作り直した(`cards/data.md` は戻した)。`--check` は「最新」(151 本)。

## 11. ②b の作業の一覧(検収 L4・L5・L6 と §4-3 の続き・この段では src を直していない)

| # | 何を | 置き場(頭 `231d9fd0` の行) | ②b ですること |
|---|---|---|---|
| L4 | 月次 MER の呼び手が試験と src で違う。src の `cli.write_census_files` はモジュールの腕 `_RRC.is_legacy()` を渡し、試験はそのランの実行器の腕 `res.runner.rate_rules == "legacy"` を渡す。助けで回した旧道のランでは、センサスのファイルは「非該当」・要約は帯で判定、と食い違う | `src/shibuya/cli.py:344`・`tests/engine/test_waste_sink_report.py:117` | 率の規則の切替口を消すと `_RRC` が無くなる=src の呼び手を「そのランの実行器の腕」から取る形に直す(または帯の判定を常に非該当に)。同じ試験は定数 `RR.WASTE_BAND_NA` を読むために `switch_rate` を import している(`test_waste_sink_report.py:58`)=定数の置き場を決めて直す |
| L5 | 書き直した試験が、助けで回したランの manifest の mode(組み立ての腕)を期待値に置いた | `tests/engine/processes/test_rate_rules_1101.py:326`(`leg["mode"] == "off"`)・`tests/engine/processes/test_absent_processes_1102.py:285`(`leg["mode"] == "stopped"`) | manifest の mode の出どころを変えるなら、ここも直す(変えれば落ちる=黙って通らない) |
| L6 | 助け 2 本が頼っている src の形。消えれば落ちる(TypeError・AttributeError・試験の失敗)=黙って空振りはしない(検収の変異の試験で確かめた) | `economy/stage2_bind.py:775`(`attach` の `hasattr(money, "attach_stage2")`)・`runtime/systems/assemble.py:425-426`(再開の検査の `effective=…hasattr(…)`)・`cli.py:294-300`(`build_ledger_bundle` が `Ledger`・`_HouseholdWalletLedger`(非公開の名)・`GoodsLedger` をモジュールの名で引く・on の分かれの呼び方 `(n, n_poi, n_emp, rows_per_agent_day=…)` と `(n, n_poi, wallets, n_emp, rows_per_agent_day=…)`)・`economy/ledger.py:304-305`(`Ledger.__init__` が係数の既定 `TRANSFERS_PER_AGENT_PER_DAY` を呼ぶ時に読む=E3 の monkeypatch が効く前提)・`world/laws/runner.py:169・181・182`(`WorldProcessRunner.__init__` の `salient_rate_per_10k`・`rate_rules`・`absent_processes`)・`engine/presence.py:681`(`PlanExecutor.__init__` の `rate_rules`) | ②b でこれらの形を変えるときは、助け(`tests/economy/_stage2_outside.py`・`tests/engine/_legacy_world.py`)も一緒に直す。部品の口(過程の引数)は仮決定で残す |
| 4-3 | 切替口のモジュールの定数を読む試験(27 本の外) | `tests/bridging/test_drives_from_vs_scoring.py::test_engine_stopped_flags`(237〜258 行) | §4-3 |
| 4-3 | 切替口そのものの試験 | `test_rate_rules_1101.py` の 2 本と `--rate-rules on` の 1 行・`test_absent_processes_1102.py` の 3 本と CLI の 1 本 | 「消した」の試験に替える(§4-3) |

②b でどう扱ったかは §12-3。

## 12. ②b: 率の規則の旧道と「無い」の過程の旧道の切替口を組で消した(1 バイト不変の見込み・byte-check は親)

土台は頭 `17ad6ebc`(① の検収の直しの commit)。旧値の再現は `git checkout stable-v2-before-switch-removal-347`(5 本の口が全部在る
最後の commit=②a の前)。親の裁定(問い 5=案 k1・②b の台帳の 3 行は removed にしない・問い 8=`world/ledger/absent.py` の文に
触らない)のとおり。

### 12-1 消した名・残した名・足した止め

| 置き場 | 消した | 残した(理由) | 足した |
|---|---|---|---|
| `src/shibuya/world/laws/switch_rate.py` | 環境変数 `SHIBUYA_RATE_RULES` の読み・`_ARM`・`arm`・`set_arm`(`__all__` から外した)・`resolve(None)` の「今の腕」・`check_resume` の今の腕(`_ARM`)と文の旗 | 部品の口とその道具(`MODE_OFF`・`MODE_LEGACY`・`MODES`・`DEFAULT_MODE`・`resolve`・`is_legacy`・`removed_flags`・`manifest_fields`・`header_fields`・`check_resume`)・定数(`SCHEMA`・`RULES`・`REMOVED_RULES`・`ALWAYS_REMOVED`・`WASTE_BAND_NA`)=過程の引数 `rate_rules` の基準の口(仮決定 Q6)と manifest・見出しの鍵(値は off に固定) | `ENV_REMOVED`="SHIBUYA_RATE_RULES" と読み込みの止め(`stop_if_set`)・`resolve(None)` は既定 off・`check_resume` は既定と比べ、文に消した切替口と安定版のタグ |
| `src/shibuya/world/laws/switch_absent.py` | 同じ形(`SHIBUYA_ABSENT_PROCESSES`・`_ARM`・`arm`・`set_arm`) | 同じ形(`MODE_STOPPED`・`MODE_LEGACY`・`MODES`・`DEFAULT_MODE`・`resolve`・`is_legacy`・`stopped_flags`・`manifest_fields`・`header_fields`・`check_resume`・`SCHEMA`・`PROCESSES`・`STOPPED_PROCESSES`) | 同じ形(`ENV_REMOVED`="SHIBUYA_ABSENT_PROCESSES") |
| `src/shibuya/cli.py` | 旗 `--rate-rules`・`--absent-processes`・`set_arm` の呼び出し 2 つ・ランの種類の腕の数えの 2 項 | `write_census_files` の `waste_band_applies=_RRC.is_legacy()`(下の L4) | 注 |
| `src/shibuya/runtime/systems/assemble.py` | 組み立てが腕を読む `_RRB.arm()`・`_APB.arm()` | 再開の検査の呼び出し(`check_resume`)・過程と計画実行層と箱へ腕を渡す形(値はいつも既定) | `rate_rules_mode = _RRB.DEFAULT_MODE`・`absent_mode = _APB.DEFAULT_MODE`。試験の口 `salient_rate_per_10k` が None 以外なら止める(案 k1・文に消した口とタグと部品の口の名) |
| `src/shibuya/engine/run.py` | — | 引数 `salient_rate_per_10k`(既定 None=設定の指紋と 1-0 の引数の数を変えない) | docstring を「消した口・None 以外は止める」に |
| `src/shibuya/foundation/arms/removed.py` | — | 第346 と ②a の行と文(前のまま) | `REMOVED_ENV` に `SHIBUYA_RATE_RULES`・`SHIBUYA_ABSENT_PROCESSES`・`REMOVED_CLI_FLAGS` に `--rate-rules`・`--absent-processes`・`_STEP_TAG` に 4 つの名(タグ `stable-v2-before-switch-removal-347`)。ランの入口の止めと表に出さない旗は一覧を見るので自動で入る |
| `tools/bytecheck/configs.py` | `SWITCH_ENV` の 2 本 | — | `REMOVED_ENV` に 2 本 |

- 残した部品の口(仮決定 Q6): 過程の引数 `rate_rules`・`absent_processes`(`None`=既定)・`SalientProcess(rate_per_10k_per_day=)`・
  `WorldProcessRunner(rate_rules=, absent_processes=, salient_rate_per_10k=)`・`PlanExecutor(rate_rules=)`・箱の欄 `cfg.rate_rules`・
  `cfg.absent_processes`。§11 の L6 の一覧(試験の助けが頼っている src の形)は変えていない。
- 1 バイト不変の見込みの理由: 消した分かれは、既定(off・stopped)では通らない分かれだけ。組み立てが読む腕は前も環境変数が無ければ
  既定で、今は既定そのもの。19 構成は `cli.run` を直に呼び(argparse を通らない)、`salient_rate_per_10k` を渡さず、組 `all19` の
  環境変数は空。manifest の `rate_rules`・`absent_processes` の節は組み立ての腕(既定)から作る=前と同じ値。設定の指紋の鍵も
  引数の数も変わらない。

### 12-2 替えた試験(前に確かめていたこと → 後に確かめること)

| 試験 | 前 | 後 | 同じか・減ったか |
|---|---|---|---|
| `tests/engine/processes/test_rate_rules_1101.py::test_the_default_arm_is_off_and_names_are_checked` → `::test_the_run_arm_is_off_and_the_switch_is_removed` | 既定 off・`resolve(None)` は今の腕・`set_arm("on")` で止まる・印と規則の表 | 腕を選ぶ名(`arm`・`set_arm`・`_ARM`)が無い・`resolve(None)` は既定 off・消した環境変数と旗とタグが止める一覧にある・部品の口の名の検査(`resolve("on")`)・印と規則の表は前のまま | 切替口そのものの確かめ=「消した」に替えた。印と表は同じ |
| 同 `::test_state_header_and_resume_check` | 腕 off で見出し off は通る・見出しに無いと止まる/腕 legacy で見出しに無いファイルは通る・見出し off は止まる | 見出し off は通る・見出しに無い(legacy)と legacy は止まる・文に消した切替口とタグ | legacy の腕からの再開は無くなった(切替口そのもの)。食い違いを止める確かめは同じ |
| 同 `::test_attendance_rate_is_gone_from_run_day_and_the_cli` | `--rate-rules on` は名の誤りで止まる | `--rate-rules` は値(on・legacy・off)に依らず、表に出さない旗で消した切替口の文で止まる | 同じ(止まる)+文を見る |
| 同 `::test_the_run_day_collapse_rate_port_is_removed`(新) | — | 案 k1: `run_day(salient_rate_per_10k=3000)` は文(消した口・タグ・部品の口の名)で止まる・引数の既定は None・None のランは回る | 足した |
| 同 `::test_run_manifest_counts_rise_in_legacy_and_are_zero_off`(変えていない) | 検収 L5: 助けで回した旧道のランの manifest の mode=off を期待値に置いている | 本段は manifest の mode の出どころ(組み立ての腕=既定)を変えないので、そのまま通る | 同じ |
| `tests/engine/processes/test_absent_processes_1102.py::test_the_default_arm_is_stopped_and_names_are_checked` → `::test_the_run_arm_is_stopped_and_the_switch_is_removed` | 既定 stopped・`resolve(None)` は今の腕・`set_arm("off")` で止まる・印・宣言との 1 対 1 | 率の規則と同じ形(名が無い・既定 stopped・一覧とタグ・部品の口の名の検査)・印・宣言との 1 対 1 は前のまま | 切替口そのもの=「消した」に替えた。印と宣言は同じ |
| 同 `::test_state_header_and_resume_check` | 率の規則と同じ形 | 率の規則と同じ形 | 率の規則と同じ |
| 同 `::test_resume_through_run_day_checks_the_arm` | 同じ腕の再開=通し・切替口の腕を legacy に置くと同じファイルからの再開が止まる | 同じ腕の再開=通し(見出しの `absent_processes` が stopped)・見出しに `absent_processes` の無いファイル(版上げの前=legacy のラン。保存の間だけ `header_fields` を None にして作る)からの再開は文(消した・タグ)で止まる | 同じ(食い違いを止める)。食い違いの作り方だけが違う |
| 同 `::test_cli_rejects_a_wrong_arm_name` → `::test_cli_flag_is_removed` | `--absent-processes off` は名の誤りで止まる | 値(off・legacy・stopped)に依らず、消した切替口の文で止まる | 同じ(止まる)+文を見る |
| 同 `::test_run_manifest_section`(変えていない) | 検収 L5: 助けで回したランの manifest の mode=stopped を期待値に置いている | そのまま通る(12-3) | 同じ |
| `tests/engine/test_removed_switches_346.py`(集合・タグの表・旗の場合) | 消した名 6 本・旗 4 本 | 8 本・旗 6 本(`SHIBUYA_RATE_RULES`・`SHIBUYA_ABSENT_PROCESSES`・`--rate-rules`・`--absent-processes`・タグは 347)。旗の場合に `--rate-rules legacy・off`・略記 `--rate-r`・`--absent-processes legacy・stopped`・略記 `--absent` を足した。環境変数の場合(子のプロセス)は一覧から自動で 2 本 × 値 2 × 入口 2 が入る | 同じ+足した名 |

確かめる範囲が減った所: 切替口そのものの確かめ(腕の名・legacy の腕からの再開・CLI の旗の値の名の検査)だけ。旧道を駆動に使う
試験は ① で部品の口と試験の中だけの助けへ移したので、確かめる値は減っていない(§3・§4)。

### 12-3 検収の L4・L5 と、§4-3 の続き

- L4(`cli.write_census_files` の腕の出どころ): `switch_rate` のモジュールは残した(部品の口の定数と道具)ので `_RRC` は無くならない。
  `_RRC.is_legacy()` は引数なし=`resolve(None)`=既定 off を読む=**常に偽**(cli のランの月次 MER の帯はいつも非該当)。cli の
  ランの腕はいつも既定なので、これは「そのランの腕」と同じ値。試験 `test_waste_sink_report.py` の legacy の 2 本はそのランの実行器
  の腕(助けで legacy)を渡して MER を作る。旧道は試験の中だけの助けのランにしかないので、食い違いは src の側では起きない。src の
  式は変えず、注に「常に偽・旧道は試験がそのランの実行器の腕から作る」と書いた。`test_waste_sink_report.py` が `switch_rate` から
  定数 `WASTE_BAND_NA` を読む形はそのまま(定数は残した)。
- L5(manifest の mode を期待値に置いた 2 か所): 本段は manifest の mode の出どころ(組み立ての腕=`b.cfg.rate_rules`・
  `b.cfg.absent_processes`=既定)を変えないので、2 か所とも変えずに通る(12-4)。
- `tests/bridging/test_drives_from_vs_scoring.py::test_engine_stopped_flags`: 読む定数(`DEFAULT_MODE`・`MODE_OFF`・`RULES`・
  `STOPPED_PROCESSES`・`MODE_STOPPED`・`PROCESSES`)は残したので、変えずに通る(12-4)。

### 12-4 試験の結果

- 1 本の pytest(`-m "not gpu and not slow"`・`-n 4 --dist loadfile`・作業の木・頭 `17ad6ebc`+本段): 変えた試験の 3 ファイル
  (`test_rate_rules_1101.py` 21=前 20+1・`test_absent_processes_1102.py` 22・`test_removed_switches_346.py` 37=前 27+10)と、消した
  名・旗・口を読む試験と変えた src の口を見る試験(`tests/bridging/test_drives_from_vs_scoring.py` 23・`tests/tools/test_bytecheck.py`
  123・`tests/engine/test_waste_sink_report.py` 6・`tests/test_cli*.py` 5 本 56・`tests/engine/systems/test_boxes.py` 9=run_day の
  引数の数・`tests/engine/bridging/test_bridging_ledger.py` 40・`tests/bridging/test_decision_rows_1101.py` 6=台帳の 3 行と
  `BASE_ROWS_SHA`・`tests/engine/state/test_names_frozen.py` 13・`tests/test_places_guard.py` 16)で **372 passed・0 failed・
  0 skipped**(1 分 18 秒)。警告は前から出る「既知の循環」の `UserWarning` だけ。
- L5 の 2 か所(`test_run_manifest_counts_rise_in_legacy_and_are_zero_off`・`test_run_manifest_section`)と
  `test_engine_stopped_flags` は、変えずに通った。台帳の行が指す切替口が無くなって落ちる試験は無かった。
- `lint-imports`: 12 kept・0 broken(`world.laws.switch_rate`・`switch_absent` が新しく `foundation.arms.removed` を読む)。
- カード `tools/repo_guide/build.py` で作り直した(`cards/data.md` は戻した)。`--check` は「最新」(151 本)。
- 回していない: byte-check と範囲の全体の試験(親)。旧道を部品の口と助けで回す試験(①・①c で書き直したもの)は本段で変えて
  いないので回していない(範囲の試験に入る)。`tests/c7` は開いていない(消した環境変数や旗を使うかは確かめていない)。

### 12-5 次の版上げで扱う行(本段では触らない)と、直していない注・止まる記録の道具

- つなぎの台帳の 3 行(親の裁定=removed にしない・`bridges_count`・`bridges_version` と `BASE_ROWS_SHA` を動かさない):
  `DOC-s2rates-legacy-switch`・`DOC-s2e-absent-legacy-switch`・`DOC-s2rates-collapse-test-knob`。次の版上げで removed にする
  (why の末尾に「〔第347〕閉じた: 切替口と試験の口を消した・部品の口は残る・旧値の再現は安定版のタグ `stable-v2-before-switch-removal-347`」)。
  行が指す `code_at`(旧の道 `engine/rate_rules.py`・`engine/absent_processes.py`・`cli.py`・`engine/processes/salient.py`・
  `engine/run.py`)のファイルは残っているので、台帳の試験は落ちない(12-4)。
- `world/ledger/absent.py` の `_RATE_OFF`・`_ABSENT_OFF` の文(「旧道 `--rate-rules legacy` では…が動く(1 版だけ)」)と各行の
  `stage="next-bump"`(§6 の行・`registry_hash` が動く)。
- 直していない注(`--rate-rules legacy`・`--absent-processes legacy` の言い方が残る。docstring の見出しの項と宣言の文を動かさない
  ため): `world/laws/salient.py:46-47`・`engine/presence.py:39・56・85・121・887・998`・`world/laws/civic.py:21・25・27`・
  `world/laws/goods_flow.py:36・38・42・43`・`world/laws/logistics.py:13・21`・`world/laws/rail.py:68`。文書
  `docs/reference/repo-guide/catalog/a-body-and-town.md`(71・72・106・178・728・955・1185 行)・`b-people.md`(792・796・828 行)と
  `day-flow.md`(手で書く案内=試験が読まない)。
- 今の src で止まる記録の道具(試験が読まない=346 の前例。旧値は安定版のタグで回す):
  - 切替口の腕を置く: 本書の `tools/step0_legacy_helper.py`(`set_arm`・`run_day(salient_rate_per_10k=)`)・`tools/step0_parts_none.py`。
  - 消した旗を渡すと止まる(渡さなければ回る): `docs/bench/analysis/s2-rates-1101/tools/compare_s2rates.py`・`perf_s2rates.py`
    (`--rate-rules`)・`docs/bench/analysis/s2e-1102/tools/run_s2e.py`(`--absent-processes`・`--rate-rules`)。
  - `salient_rate_per_10k` を渡す: `docs/bench/analysis/memory-stage1-2026-09-28/memory_measure.py`(2 構成)・
    `small-fixes-2026-09-29/small_fixes_measure.py`・`wallbounce-1003/10c/count_dist_x1000.py`・`wallbounce-1003/10d/resume_check_10d.py`。
  - 許す鍵の一覧に残る: `tools/c8/ablation_runner.py` の `ALLOWED_KWARGS` の `salient_rate_per_10k`(腕の表に使う腕は無い=渡せば
    組み立てで止まる)。

## 付録 A. 試験ごとの行(検収 L9=§3・§4 でまとめた行を開いた)

### A-1 既定と同じ値に腕を押さえる行を消した 9 か所(§3-1)

| 試験(と、その行を通る試験) | 消した行 | 前 → 後 |
|---|---|---|
| `tests/economy/stage2/test_stage2_default_2_4.py::test_resume_check_uses_the_effective_arm` | `setattr(ES2, "_ARM", ES2.ARM_ON)` | 段階 2 on の再開の検査 → 同じ(既定 on) |
| 同 `::test_revenue_is_tax_exclusive_on_a_synthetic_run` | 同 | 合成の世界の売上の写しは税抜き → 同じ(§10-3 の L2 で skip を失敗に替えた) |
| `tests/economy/stage2/test_stage2_resume.py::test_resume_equals_straight_with_the_arm[1440・2190]`(slow) | 同 | 段階 2 on の再開=通し → 同じ |
| `tests/economy/stage2/test_wage_occupation_runs.py::_arm`(通る試験: fixture `two_arms` の `test_conservation_and_only_the_wage_accounts_move`・`test_median_matches_r107` と `test_resume_equals_straight`・どれも slow) | 同 | 賃金の道のラン → 同じ |
| `tests/economy/test_wage_occupation.py::test_wage_path_header_and_resume_check` | 同 | 賃金の道の見出しと再開の検査 → 同じ |
| `tests/economy/test_rules42b_ledger.py::test_resume_refuses_a_header_without_rules_42b` | 同 | 空欄 3 件の腕の見出しの検査 → 同じ |
| 同 fixture `law`(通る試験: `test_two_synthetic_days`・`test_payroll_inputs_are_always_4_2b_at_build_time`・`test_stage_b_payday_has_no_undeclared_writes`) | 同 | 4-2b の合成のラン → 同じ |
| `tests/economy/test_rules42_runs.py` の fixture `law`(通る試験: `test_on_keeps_the_register_tax_in_the_deposit_and_deducts_on_payday` ほか同じファイルの `law` を取る試験) | 同 | 4-2 の合成のラン → 同じ |
| `tests/economy/stage2/test_stage2_calls.py::test_port_answers_reach_the_actions_in_a_run` | `setattr(ES2, "_ARM", ES2.ARM_OFF)` と続く `ES2.set_arm("on")` | 口の答えがランの行為に届く → 同じ |

### A-2 `test_rng_scheme_10c.py` のランの外の 14 本(§3-2)

部品の口の欄は、その試験が直に作る過程の数(出動=`PublicServiceDispatchProcess(absent_processes=LEGACY)`・顕著行為=
`SalientProcess(rate_rules=LEGACY)`)。前は autouse で切替口の腕を legacy にして、過程の既定で旧道を回していた。

| 試験 | 確かめていること(前も後も同じ) | 部品の口(出動・顕著行為) |
|---|---|---|
| `test_scheme_values_and_default_is_counter` | 鍵の作り方の名と既定 counter | なし(関数) |
| `test_run_tick_key_is_day_key_times_ticks_per_day_plus_T` | 刻みの鍵=日の鍵 × 1 日の刻み数+T | なし(関数) |
| `test_run_tick_key_multiplies_by_the_ticks_per_day_not_1440` | 掛けるのは 1 日の刻み数(1,440 でない) | なし(関数) |
| `test_cli_flag_is_shared_by_engine_run_and_cli` | 旗が engine.run と cli で同じ | なし(関数) |
| `test_counter_streams_have_their_own_names_and_word0_is_zero` | counter の流れの名と 1 語目 0 | 1・1 |
| `test_day_key0_enters_the_key` | 日の鍵が鍵に入る | 1・0 |
| `test_counter_keeps_no_generator` | counter は Generator を持たない | 1・1 |
| `test_counter_dispatches_in_one_cell_and_tick_draw_different_delays` | 同じセルと刻みの出動が別の遅れを引く | 1・0 |
| `test_counter_dispatch_delay_depends_only_on_T_cell_k` | 出動の遅れは T・セル・k だけに依る | 2・0 |
| `test_counter_k_restarts_for_each_tick_and_cell` | k は刻みとセルごとに 0 から | 2・0 |
| `test_counter_collapse_at_T_does_not_depend_on_earlier_ticks` | T の倒れるは前の刻みに依らない | 0・2 |
| `test_counter_calls_the_dispatch_in_ascending_agent_id` | 出動を id の昇順で呼ぶ | 1(子の型 `Spy`)・1 |
| `test_per_tick_counts_match_the_known_poisson_rate` | 刻みごとの件数がポアソンの率に合う(助け `_per_tick_counts`) | 1・1(助けの中) |
| `test_poisson_z_catches_a_ten_percent_lower_rate` | 1 割低い率をポアソンの z が見つける(同じ助け) | (同じ助け) |

出動は 10 か所(上の 1+1+1+1+2+2+1+1=10)、顕著行為は 6 か所(1+1+2+1+1=6)。

### A-3 `test_ledger_wiring.py`(§4-1・§4-4)

「形」の欄: 外=段階 2 の外(基準の口)・2=段階 2 on(〔検収 M2〕で足した場合)・2 none=段階 2 on・部品 none。

| 試験 | ランを回すか | 確かめていること | 形 |
|---|---|---|---|
| `test_wiring_does_not_change_the_state_hashes_when_goods_processes_are_off` | 回す(500 体・1 日 ×2) | 物の過程を切れば、台帳を注入しても SoA の組み立て・世帯の現金・売上・購入が台帳なしと同じ | 外・2 none |
| `test_goods_processes_change_the_world` | `wired` | 物の過程で納品が立ち、棚が動く・売れ残りはビンに落ちない | 外・2 |
| `test_two_wired_runs_are_identical` | 回す(300 体 ×2) | 同じ入力の 2 本の final と金の台帳の状態ハッシュが同じ | 外・2 |
| `test_conservation_over_all_sectors_including_row` | `wired` | 全部門の現金の和 0・世帯の現金=`agents.money`(写しでない)・店の現金=売上(+段階 2 on はレジの税)−域外仕入・`conserved` | 外・2 |
| `test_purchases_are_booked_as_consumption` | `wired` | 世帯 → 店の消費支出=売上(+段階 2 on はレジの税)・取引の件数 ≥ 購入 | 外・2 |
| `test_check_two_holds_after_the_run` | `wired` | 検算②と流れの行列の釣り合い | 外・2 |
| `test_census_gate_passes_for_a_wired_day` | `wired` | 締めた日の日次センサスの門・faucet と廃棄が実数 | 外・2 |
| `test_run_result_census_row_is_the_closed_day` | `wired` | `census_row` は締めた日の行・faucet と sink の科目の集合・廃棄の質量・締め後の現在値は空虚 | 外・2 |
| `test_o_t_logs_of_both_ledgers_are_measured` | `wired` | 取引ログと納品ログの O(t) が成長の門に載る | 外・2 |
| `test_the_bundle_declaration_survives_the_c7_scale` | `wired`(後半) | 390,067 体の宣言が cap を超えない・小さいランも溢れない | 外・2 |
| `test_world_stock_is_a_mirror_of_the_shelf` | `wired` | `world.pois.stock` は棚の写し・SKU の収支 | 外・2 |
| `test_w2_five_thousand_agents_with_the_ledger_wired`(slow) | 回す(5,000 体 ×4) | W2 の壁時計・物の過程を切った不変(段階 2 on は部品 none で)・保存則・検算②・センサス・成長の門 | 外・2 |
| `test_check_two_holds_at_every_checkpoint` | 回さない(手回しの刻み) | 検算②が 20 刻みごとに成り立つ(段階 2 on は初期の預金とレジの税が動くことも見る) | 外・2(代役の組み立ての物で挿す) |
| `test_restock_through_resolve_pays_and_updates_the_mirror` | 回さない | 補充が写しを更新し域外仕入を計上 | 外・2(同) |
| `test_collect_waste_through_resolve` | 回さない | 廃棄物の収集でビンが空・SKU の収支 | 外・2(同) |
| `test_consume_moves_holdings_into_the_sink` | 回さない | 消費で所持が減り SKU の sink へ | 外・2(同) |
| `test_restock_requires_a_goods_ledger` | 回さない | 物の台帳が無ければ補充は止まる | 台帳の形に依らない(1 本のまま) |

- 「ランを回す 12 本」(①c の表)=上の `wired` の 9 本・状態ハッシュ不変・2 本のランの同一・W2。
- 組み立てを通らない 4 本では、段階 2 の外の型も素の `Ledger` も段階 2 を挿さない(挿すのは組み立て `stage2_bind.attach` だけ)。
  このため段階 2 on の場合は、試験の代役の組み立ての物(`tests/economy/stage2/test_stage2_money_rules.py::_plan` と同じ形・部品は
  全部)で `attach_stage2` を呼んで挿した。補充・廃棄物・消費の 3 本は、段階 2 を挿しても同じ期待値で通った(この 3 つの操作は段階 2
  の部品の流れを通らない)。

### 12-6 親の確かめ(②b)

- byte-check: 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・final が同じ 19(基準 `ec2350b`=直前の commit・src は検収の直し `17ad6eb` と同じ。
  既定 `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。全体の壁時計 421 秒)。組は [bytecheck_2b/](bytecheck_2b/)。
- `tests/c7` は開かずに件数だけ数えた: 消した環境変数・旗・腕の名を使う所は 0。`salient_rate_per_10k` の 2 か所は、合成の
  `input_match` に渡す文字列の鍵で、ランを回さない(止める対象でない)。
- 範囲の全体の試験は、この段の commit の後に本体の木で回す(結果は次の段の節に書く)。
- 例外(ignore)の本数は変わらない(割る段ではない=31 本・延べ 45 行)。`lint-imports` 12 kept。
