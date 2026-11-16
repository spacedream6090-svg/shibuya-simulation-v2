# 第347 止めた切替口 3 本の削除と、`--space legacy`・`--hunger-model v1` を試験の中だけの口に(switch-removal-347)

> 整理の段(既定のランの結果を 1 バイトも変えない段)。発注: [返事その 8](../../../design/prompt-2026-11-16-reply8.md) §1-1(b)・
> §1-2 Q7(d)・§1-10(第346 の仮採用)。前例: [delete-346](../delete-346/README.md) §3(止めた 3 本と、旧道を使う試験の一覧)。
> 土台は作業の木の枝 `work/switch-removal-347`(① は頭 `ff28372d`=段 4-10 まで・①c の前に頭 `d42fbba0`=段 4-12 まで入った本体へ
> 移した=§7)。実装役 Opus 5.5。byte-check・範囲の試験・commit とタグ(`stable-v2-before-switch-removal-347`=②a の前の
> commit)は親。

段の並び(親の裁定): ① 試験の書き直し(切替口はまだ在る・src は変えない)→ ②a 経済の段階 2 の off → ②b 率の規則と「無い」の
過程(組で)→ ③a `--space` → ③b `--hunger-model` の旗。**本書は ①(手順 0・①a・①b・①c)まで**。

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
- **段階 2 の外の束は off と同じだった。** 段階 2 の口(`attach_stage2`)を持たない台帳=試験の中だけの束(§2-1)は、5 構成とも
  38 欄すべてが off と同じ。E3(HEAD の写しとの 5,000 体の同値)はこの束で書き直した(裁定 3)。
- **試験の中だけの助けも切替口と同じだった。** 実行器と計画実行層の初期化を包んで部品の口(旧道)を挿す助け(§2-2)は、2 構成
  (合成 2 日の倒れる・出動・再開の形/世界資産 200 体の率の規則の旧道)で final・checkpoint・件数・計数がすべて同じだった。
  違ったのは manifest の `mode` の欄だけ(組み立ての腕を書く)。これで、率の規則と「無い」の過程の旧道を駆動に使う試験を、
  確かめる範囲を減らさずに書き直した(裁定 1)。
- 書き直した試験は §3(①a・①b)と §4(①c)。合わせて試験 27 ファイル・新しい助け 2 本。src は変えていない(§7)。
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

| 構成 | 同じ欄 | 違う欄 |
|---|---|---|
| r4=`test_resume_10d::test_counter_rng_resume_draws_once` の通し(合成 25 セル・200 体・2 日・倒れる率 3,000・両方の旧道) | final・呼数・全 checkpoint(combined と full-hash)・顕著行為・出動・気づき・過程の計数・manifest の `rate_rules.counts`・`absent_processes.counts`・`waste_sink`(10 欄) | manifest の `rate_rules.mode`(legacy → off)・`absent_processes.mode`(legacy → stopped) |
| r11=`test_rate_rules_1101::day_runs` の legacy(世界資産 200 体・台帳つき・1 日・率の規則の旧道) | 上と同じ 10 欄+`absent_processes.mode` | manifest の `rate_rules.mode`(legacy → off) |

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
  `rate_rules.mode`・`absent_processes.mode` と状態のファイルの見出しは既定(off・stopped)を書き、計数(`counts`)だけが旧道の
  件数を持つ。manifest の mode を見ていた 2 本は、実行器の腕と過程の印を見る形に替えた(§3 の R11b・A3)。

## 3. 書き直した試験の表(前に確かめていたこと → 後に確かめること)

「同じ」=前と同じことを確かめる。旧道はどれも部品の口(過程の引数)で回す。切替口が在る今の木で、どれも前の値のまま通る(§7)。

### 3-1 `--economy-stage2 off`(①a)

| 試験 | 前 | 後 | 同じか |
|---|---|---|---|
| `tests/economy/cp2/test_cp2_nine_ops_equivalence.py::test_5k_mock_day_matches_head[6.5・3.0]`(slow) | 切替口 off で、HEAD 136fdbb の台帳の写しと今の台帳の 5,000 体・1 日の final・呼数・金と物の台帳の状態・世帯の現金が同じ(輪の係数 6.5 は溢れ 0・3.0 は溢れを数える) | 段階 2 の外の束(§2-1。HEAD の側は写しの型の上・今の側は `outside` の型)で同じ比べ。「本当に HEAD の台帳で回した」は型の名の比べから isinstance に替え、今の台帳に段階 2 が挿さっていないことも見る | 同じ |
| `tests/engine/multiday/_md.py::arms()`(使う試験: `test_md23_resume.py::test_synthetic_two_days_resume_at_the_day_boundary[mem・events]`・`test_md23_body_events.py` の `runs` と `test_legacy_path_with_the_log_off_is_the_1_6_form`) | 経済の段階 2 の腕を off にして、合成の 2 日の再開=通しと記憶の器を見る | 腕の引数を外した。これらのランは金の台帳を渡さないので、段階 2 は腕に依らず挿さらない | 同じ(結果も同じ) |
| 既定と同じ値の setattr を消した 8 本: `test_stage2_default_2_4.py::test_resume_check_uses_the_effective_arm`・`::test_revenue_is_tax_exclusive_on_a_synthetic_run`・`test_stage2_resume.py::test_resume_equals_straight_with_the_arm`(slow)・`test_wage_occupation_runs.py::_arm`(slow)・`test_wage_occupation.py::test_wage_path_header_and_resume_check`・`test_rules42b_ledger.py`(2 本)・`test_rules42_runs.py::law`・`test_stage2_calls.py::test_port_answers_reach_the_actions_in_a_run`(off にしてから on に戻す 2 行) | 段階 2 on(既定)の各試験 | 腕を既定の on に書く行を消した(②a で属性が無くなる) | 同じ |

### 3-2 `--rate-rules legacy` と `--absent-processes legacy`(①b)

| 試験 | 前 | 後 | 同じか |
|---|---|---|---|
| `tests/engine/processes/test_salient.py`(12 本) | モジュールの autouse で両方の切替口の腕を legacy にし、過程の既定で旧道を回す(倒れる → 気づく → 起こす・予算・ablation・出動と到着・B4 の行) | 過程の部品の口(`SalientProcess(rate_rules="legacy")`・`PublicServiceDispatchProcess(absent_processes="legacy")`)を明示 | 同じ |
| `tests/engine/processes/test_rng_scheme_10c.py` のランの外の 14 本(過程を直に作る 9 本と関数の試験) | 同じ autouse で、counter の流れ・出動の遅れ・T だけで引く・id の昇順・ポアソンの z | 過程を直に作る所(出動 9 か所・顕著行為 6 か所)に部品の口を明示 | 同じ |
| 同 ランの 7 本(`test_run_day_passes_day_key0_to_the_counter_key`・`test_run_day_has_no_scheme_argument_and_writes_the_manifest`・`test_counter_run_twice_is_identical`・`test_two_day_counter_keys_carry_T`・`test_counter_adds_no_state_to_restore_and_drops_the_two_generators`・`test_the_tape_carries_the_scheme_and_the_replay_matches`・`test_a_tape_from_before_10e_is_not_replayed`) | 切替口の腕 legacy と `run_day(salient_rate_per_10k=…)` で、ランの中の倒れる・出動の鍵・決定論・状態の道筋・テープの再生 | autouse を §2-2 の助けにし、倒れる率は助けで渡す | 同じ |
| `tests/engine/test_ablation23_switches.py::test_d50_scale_reaches_the_salient_process_through_run_day` | 率の規則の旧道と率 4,000 で、`run_day` の d50 の倍率が顕著行為の過程に届く | 助け(率の規則・率 4,000) | 同じ |
| `tests/engine/test_resume_10d.py::test_counter_rng_resume_draws_once` | 両方の旧道と率 3,000 で、2 日のランの再開=通し・倒れる件数と出動の件数の和が通しと同じ | 助け(両方・率 3,000) | 同じ |
| 同 `::test_daily_tables_are_relaid_from_the_calendar_day` | 率の規則の旧道で、2 日目の頭に W7・納品・工事・宅配の表を暦の日で引き直す(2 日目も配る) | 助け(率の規則) | 同じ |
| `tests/engine/test_salt_seed_split_10f.py::test_population_and_motion_streams_use_their_own_seed_synthetic` | 率の規則の旧道と率 3,000 で、流れごとの seed の分け方(顕著行為の流れも動きの seed) | 助け(率の規則・率 3,000) | 同じ |
| 同 `::test_t3_runner_first_diff_matches_first_diff_py_and_crn_checks` | 回す役 `tools/c7/salt_runs.py`(子のプロセス)に腕「倒れる率 1,000」と環境変数で旧道を渡し、最初の食い違い・T0 の前の一致・CRN の検査・`arm_keys_unseen == ["salient_rate_per_10k"]` | 子のプロセスには助けが届かないので、腕を「就寝の抑止を切る」(`sleep_suppression=False`)に替えた。この腕は 200 体・1 日・salt 1 と 2 のどちらでも最初の checkpoint(刻み 59)で食い違う。「manifest に載らない腕の報告」は、同じランの記録に `salient_rate_per_10k` の名を足して `salt_compare.input_match` を呼んで見る(報告に出る・ok のまま) | 道具の確かめは同じ(腕の中身だけが違う) |
| 同 `::test_runner_environment_modes` | 同じ道具で環境の seed の決め方(fixed・salt)と空でない置き場で止まる | 腕を同じく替えた(この試験は腕の中身に依らない) | 同じ |
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
| `tests/engine/test_ledger_wiring.py`(ランを回す 12 本) | モジュールの autouse で切替口 off にして、C4 の帳簿(段階 2 の外)を合成のランに結線したときの状態ハッシュ不変・保存則・検算②・日次センサス・締めた日の行・O(t) の計測・棚の写し・W2 | autouse を外し、台帳を `outside(Ledger)` で作る(`_bundle`) | 同じ |
| `tests/economy/stage2/test_stage2_runs.py::test_arm_off_changes_nothing_on_the_ledger` → `::test_a_ledger_outside_stage2_changes_nothing` | 切替口 off のランは段階 2 を挿さない・manifest に段階 2 の欄が無い・生ログの方法の列 0・保存則・`money_stage2_in == 0`・判断の口の段階 2 の欄が無い | 段階 2 の外の台帳(`_run(outside=True)`)で同じ確かめ(名を直した) | 同じ |
| 同 `::test_off_parts_spec_without_the_arm_is_ignored` → `::test_parts_spec_outside_stage2_is_ignored` | 切替口 off なら部品の指定(wages)は効かない(段階 2 が挿さらない) | 段階 2 の外の台帳では部品の指定が効かない(名を直した) | 同じ |
| 同 fixture `arm` と、段階 2 on の 5 本(全部品・部品を 1 つ止める ×5・閉じた ATM・判断の口・ATM の器) | 切替口の腕を off にしてから on に切り替える | 腕に触らない(既定 on)・部品と ATM の表だけ置く | 同じ |
| `tests/economy/stage2/test_stage2_world_two_day.py::test_world_two_days_without_the_arm` → `::test_world_two_days_outside_stage2`(slow) | 切替口 off の世界資産 5,000 体・2 日は段階 2 が挿さらない・雇用主の口 1・manifest に段階 2 の欄が無い・保存則・方法の列 0 | `use_outside_bundle` で同じ確かめ(名を直した) | 同じ |
| 同 `::test_world_two_days_with_the_arm`(slow) | 腕 on を書いてから回す | 腕を書く行を消した(既定 on) | 同じ |
| `tests/economy/stage2/test_stage2_resume_arm.py::test_resume_stops_when_the_arm_or_parts_differ`(E8) | 腕 on のファイルから、部品が違う・腕 off で再開すると止まる・そろえた再開=通し | 腕 off の代わりに、段階 2 の外の台帳で再開すると止まる(今の腕は off と同じ) | 同じ |
| 同 `::test_arm_off_state_files_keep_the_header_and_refuse_an_on_resume` → `::test_state_files_outside_stage2_keep_the_header_and_refuse_a_stage2_resume`(E9) | 腕 off のファイルは見出しに段階 2 を書かない・腕 on で再開すると止まる・見出しに無い=off と同じ | 段階 2 の外の台帳のランのファイルで同じ確かめ。最後は `check_resume(None, effective=False)`(名を直した) | 同じ |

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
- src に差が無い(頭 `d42fbba0` で): `git status --short src` は空。`tools/bytecheck/astsame.py --base HEAD` は「変わったファイル 0 本」。
- `tests/test_places_guard.py`・`tests/c8/test_places_rule_copies.py`: 26 passed。
- カード `tools/repo_guide/build.py` で作り直した(`cards/data.md` は戻した)。`--check` は「最新」(152 本)。
- 頭を移したとき(`stash push -u` → `merge --ff-only` → `stash pop`): 試験のファイルはぶつからなかった(`test_du_runs`・
  `test_removed_switches_346`・`test_salt_seed_split_10f` は自動で混ぜた=段 4 の import の書き換えと本段の変更が両方入った)。
  ぶつかったのはカード 5 本(`cards/README.md`・`docs.md`・`src/shibuya/engine/README.md`・`tests/engine/README.md`・
  `tests/engine/duties/README.md`)で、新しい頭の版を取ってから作り直した。stash の写しは確かめてから消した。

## 8. 道具

- [tools/step0_parts_none.py](tools/step0_parts_none.py): 手順 0 のラン(1 回 1 構成 1 腕=`off`・`none`・`noattach`)。
- [tools/step0_legacy_helper.py](tools/step0_legacy_helper.py): 手順 0 の続き(切替口の腕と §2-2 の助けが同じランになるか)。
- [tools/step0_compare.py](tools/step0_compare.py): 2 つの JSON の欄ごとの一致。
- どれも切替口が在る木(②a・②b の前)でだけ回る。結果の JSON はリポに入れていない。
