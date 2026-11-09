# src/shibuya

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [agents](agents/README.md)・[build](build/README.md)・[census](census/README.md)・[core](core/README.md)・[economy](economy/README.md)・[engine](engine/README.md)・[llm](llm/README.md)・[manifest](manifest/README.md)・[perception](perception/README.md)・[world](world/README.md)

## [__init__.py](../../../../../../src/shibuya/__init__.py)

shibuya-simulation-v2: 現実の渋谷を舞台にしたLLM社会シミュレーション第2世代(エンジン)。

- 呼び手: `tools/bytecheck/check.py`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/test_child_imports_this_tree.py`
- 読む試験(道筋で): `tests/tools/test_bytecheck.py`・`tests/tools/test_dm_eval.py`・`tests/tools/test_repo_guide.py`

## [cli.py](../../../../../../src/shibuya/cli.py)

shibuya.cli — 実行入口(層外の組立コード・C4 出口で追加)。

- 公開の関数とクラス
  - `apply_fleet_queue_default`(関数): 第289 Q28(D-55): 艦隊 × 呼数無制限 × 受理待ち枠 未指定 → 枠の既定を**体数**にする。
  - `arm_baseline`(関数): 腕の比べの元=CLI の既定の ``run_day`` の引数(``run_day`` の既定に、CLI と ``cli.run`` が違う既定を重ねた)。
  - `build_ledger_bundle`(関数): 世界から金/物の台帳とセンサス呼び出しを組み立てる(engine/ledger_api の Protocol を満たす)。
  - `checkpoints_payload`(関数): T2(決定論)行の入力 = checkpoint 列を JSON にできる形で返す(**純関数**)。
  - `fleet_queue_note`(関数): 艦隊 × 無制限で受理待ち枠が未指定かつ体数より小さいなら注記の文(それ以外は ``""``・D-55)。
  - `household_wallets`(関数): W16 母集団の種別から初期財布[円]を引く(母集団が使えないランは ``None``)。
  - `main`(関数)
  - `parse_refractory_scale`(関数): ``--refractory-scale COND=FACTOR`` の並び → ``{条件名: 倍率}``(ablation ③)。
  - `run`(関数): 台帳つきの 1 シミュ日ラン(C4 の標準入口)。
  - `run_arms`(関数): ``cli.run`` に渡された引数のうち、CLI の既定と違う腕の名(昇順)。渡さなかった引数は ``run_day`` の既定で比べる
  - `store_capital_array`(関数): 店舗ごとの参入資本[円]の配列(``(n_poi,)`` int64)。
  - `store_capital_report`(関数): 参入資本の検算行(合計・大分類別・貨幣供給比)。ランを回さずに作れる。
  - `undefined_registry_payload`(関数): 未定義行動台帳(``llm.UndefinedActionRegistry``)→ 段2 起草バッチの入力 JSON(**純関数**)。
  - `write_census_files`(関数): 日次センサス(§2.4 軽量)と月次 MER(EVE 型の固定表 + 部門軸)を ``out_dir`` へ書く。
- import している内部モジュール: `shibuya.agents.population`・`shibuya.agents.state`・`shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.economy`・`shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.census`・`shibuya.economy.entry_capital`・`shibuya.economy.ledger`・`shibuya.economy.stage2`・`shibuya.engine.absent_processes`・`shibuya.engine.arbiter`・`shibuya.engine.batching`・`shibuya.engine.body`・`shibuya.engine.calendar2.arm`・`shibuya.engine.calendar3.arm`・`shibuya.engine.calendar_self`・`shibuya.engine.calendar_shadow`・`shibuya.engine.chooser`・`shibuya.engine.classical`・`shibuya.engine.contact.arm`・`shibuya.engine.decision.layer`・`shibuya.engine.duties.arm`・`shibuya.engine.economy_stage2`・`shibuya.engine.energy`・`shibuya.engine.events.log`・`shibuya.engine.experiment.branch`・`shibuya.engine.experiment.form`・`shibuya.engine.experiment.layer`・`shibuya.engine.familiarity`・`shibuya.engine.geometry`・`shibuya.engine.intent`・`shibuya.engine.ledger_api`・`shibuya.engine.memory`・`shibuya.engine.memory_m1`・`shibuya.engine.memory_store`・`shibuya.engine.poi_target`・`shibuya.engine.proximity`・`shibuya.engine.rate_rules`・`shibuya.engine.regional_clock`・`shibuya.engine.removed_switches`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.run_kind`・`shibuya.engine.space.nav1`・`shibuya.engine.speech.layer`・`shibuya.engine.speech_clock`・`shibuya.engine.step_scope`・`shibuya.engine.store_memory`・`shibuya.llm.undefined`・`shibuya.perception.channels`・`shibuya.perception.renderer`・`shibuya.perception.templates`・`shibuya.world.assets`・`shibuya.world.state`
- 呼び手: `tools/bytecheck/check.py`・`tools/c6/c6lib.py`・`tools/c7/salt_runs.py`・`tools/instruments/anchor_gauge.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/bench/test_refr20b_tool.py`・`tests/c6/test_l4_l6_budget.py`・`tests/c6/test_t9_diagnostics.py`・`tests/c8/test_ablations_ab8.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_default_2_4.py`・`tests/economy/stage2/test_stage2_resume.py`・`tests/economy/stage2/test_stage2_world_two_day.py`・`tests/economy/stage2/test_wage_occupation_runs.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_wage_occupation.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/body/test_meal_default_w17.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar2/test_ca2_world.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_world.py`・`tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c1_world.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/duties/_du.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/duties/test_du_world.py`・`tests/engine/events/test_e_log_invariance.py`・`tests/engine/events/test_e_log_links_actual.py`・`tests/engine/experiment/test_cf33b_form_checks.py`・`tests/engine/experiment/test_cf33b_manifest.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/multiday/test_md23_resume.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/rights/test_no_permission_count.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/space/test_nav1_world.py`・`tests/engine/speech/test_speech_cli.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_census_out.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_norm_meter.py`・`tests/engine/test_pop_w21_world.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_removed_switches_346.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_t3_manifest.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/test_waste_sink_report.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/engine/test_wom.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/perception/facts/test_render_from_percept_bytes.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/test_cli.py`・`tests/test_cli_help.py`・`tests/test_cli_intent_mode.py`・`tests/test_cli_l4_scale.py`・`tests/test_cli_vocab_version.py`・`tests/tools/test_skill_gauge.py`・`tests/vocab/test_adjudicate.py`・`tests/vocab/test_registry_from_tape.py`・`tests/vocab/test_undefined_out.py`
- 読む試験(道筋で): `tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_store_memory.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/test_p_see_activity.py`・`tests/tools/test_bytecheck.py`
- 状態台帳の行
  - 持ち主 `ledger.money` の別のクラス `_HouseholdWalletLedger`(行は `shibuya.economy.ledger` のカードを見る)
- CLI の引数
  - `--ablate`: 無効化する過程 id / AB-* id
  - `--absent-processes`: 〔11-02r §1 #7〕「無い」と宣言した過程 5 件の切替口(既定 stopped・環境変数 SHIBUYA_ABSENT_PROCESSES と同じ。指定すれば環境変数より強い)。stopped=ごみの収集・街路の清掃・道路工事・救急と警察の出動・電気と水の負荷を止めた状態(宣言は world/processes/absent.py・切替は engine.absent_processes)。legacy=版上げの前の値の再現のためだけの道(次の版上げで消す)。腕は設定の指紋に入れない(manifest の absent_processes に出る・既定と違えばランの種類は arm)
  - `--activity`: 行為と活動の二層の活動層(段 2・D-116・既定 on)。立つのは --vocab-version v3 のときだけ(v1/v2 では活動欄が来ない=実質無効・checkpoint 不変)。on=満了入口・活動中は場所の変化で起こさない・あたり歩行・B4b の活動の 1 行。off=抑止も満了も無効=現行
  - `--activity-region`: --policy classical の事前分布の地域(kanto=関東大都市圏・既定/national=全国)
  - `--agents`
  - `--area-source`: 歩行可能面積の出所(C9c-1・G8 (b)・docs/research/v2-c9-geometry-capacity-research.md §2-1)。legacy=W10 街路点数 × 6.25 m²・床 1,500 m²(既定・**checkpoint はバイト不変**・6.25 は 2.5 m 格子の目の面積=expedient)/ plateau=c9c_walkable_area.parquet(PLATEAU tran 歩道部の面 + OSM 線 × 道路構造令の既定幅員で実測・tools/build_geo/walkable_area.py が作る)
  - `--batch-width-s`: 第 3 期 3-2 計算のまとめの幅[秒]\(既定 60=刻みの幅=今と同じ・環境変数 SHIBUYA_BATCH_WIDTH_S と同じ。指定すれば環境変数より強い)。刻みの幅の約数だけ選べる。進行役は窓 [t, t+W) の中の事象を時刻順に処理する(T1 の世界の事象は刻みの事象だけ=どの幅でも同じ結果)。既定と違えば設定の指紋に入り、ランの種類は arm(manifest の batching に出る)
  - `--body-schedule`: 第 3 期 3-5 TM5 の体の予約の腕(既定 sweep・環境変数 SHIBUYA_BODY_SCHEDULE と同じ。指定すれば環境変数より強い)。sweep=毎刻み全員の体を規則に通す(今の形)。reserve=体ごとに次に段の境目(空腹・疲れ・暑さ)を越える刻みを予約し、予約の来た体と入力の変わった体だけを規則に通す(結果は sweep と同じでなければならない=T3 で有効)。腕は設定の指紋に入れない(manifest の body に出る・既定と違えばランの種類は arm)
  - `--budget-mode`: 知覚のトークン配分(知覚契約書 §3.2 ablation ①)。fixed=チャネル固定枠(既定)/ranking=同一総トークンの単一ランキング
  - `--calendar`: 第 6 期 6-2 カレンダー 1b の腕(既定 w17・環境変数 SHIBUYA_CALENDAR と同じ。指定すれば環境変数より強い)。1b=W20 の時刻つきの勤務の約束を持つ体の出入り(出発するか・いつか・帰るか)を本人の判断(仮のモデル=mock/古典)へ渡す(その体の W17 の到着・退出は実行しない・就寝と起床は W17 のまま)。W20 の週の表は <world>/w20_calendar_1a.parquetか SHIBUYA_CALENDAR_W20。manifest の末尾に calendar_1b・1b のランだけ設定の指紋に入る・ランの種類は arm
  - `--calendar-2`: 第 6 期 6-2 カレンダー 2 の腕(既定 off=今の道・環境変数 SHIBUYA_CALENDAR_2 と同じ。指定すれば環境変数より強い)。arm=会話(対面・通話・メッセージ・チャット)から生まれる約束を各自が自分の行として持つ・置き場所と確かさと元の会話・壊れた予定だけ拒む・頭の中の予定は記憶で思い出せたときだけ見える・本人が約束の場所へ歩く(判断は仮のモデル)。arm は結果を変えるので設定の指紋に入り、ランの種類は腕(manifest の calendar_2 に出る)
  - `--calendar-3`: 第 6 期 6-2 カレンダー 3 の腕(既定 off=今の道・環境変数 SHIBUYA_CALENDAR_3 と同じ。指定すれば環境変数より強い)。arm=雇い主(組織の担当のうち店長か最初の担当=つなぎ)が週の最後の日に非正規とシフト勤務の働く人の翌週の枠を選び、C3 の職場の連絡(C1 の口)で知らせる・働く人はカレンダー 2 の形で自分の行に書く・休みの申し出と返事・遅れの連絡・祝日は暦の常識(判断は仮のモデル)。--contact c1 と --calendar-2 arm が要る。試験用の印は環境変数 SHIBUYA_CALENDAR_3_TRIAL=on(日曜始まり・祝日を含むランを分析に使わない印で回す)。arm は結果を変えるので設定の指紋に入り、ランの種類は腕(manifest の calendar_3 に出る)
  - `--calendar-shadow`: 第 3 期 3-1 暦 1a の影の腕(既定 w17・環境変数 SHIBUYA_CALENDAR_SHADOW と同じ。指定すれば環境変数より強い)。1a=計画実行層の勤務と授業の影を W20 の週の表(<world>/w20_calendar_1a.parquet・SHIBUYA_CALENDAR_W20)から作り、manifest の calendar_shadow に出す(計器だけ=出入りは今の W17 のまま・1a のランだけ設定の指紋に入る・ランの種類は arm)
  - `--cells`: 合成世界のセル数
  - `--census-out`: (help を読めない)
  - `--checkpoint-every`
  - `--checkpoints-out`: checkpoint 列(tick・agents/world/population/schedule ハッシュ・combined)と final_hash を JSON で書く(C7 受入 T2-a/b/c の入力。既定=書かない)
  - `--chooser`: 段 2a(D-114 (a)): 購入/食事/並ぶの対象の選び手。候補=現在セルの営業中・意図に合う POI。nearest=距離の昇順 → 可視(W8 の視点数)の降順 → POI 索引(既定・憲法⑥の宣言つき暫定。候補が現在セルだけなので距離は全部同じ=実際は可視の降順 → POI 索引で決まる)/classical=5 段目 5b の古典的選択モデル(習慣 p_h+空腹の語で動く願望水準+可視順の揺らぎ τ)
  - `--classical-habit-p`: --chooser classical の習慣の確率 p_h(宣言 0.5・感度 0.25/0.75・--familiarity on のときだけ効く)
  - `--classical-social`: 第2波 §2A 項 3-1(Q42): --policy classical の交際・付き合いの相手。acquaintance=B5 近接行の知人(関係辺の相手)のうち活性 A が最大の人・居なければ待つ(既定・関係 off では会話を始めない)/near_first=旧(近接行の最初の人=見知らぬ人)
  - `--classical-tau`: --chooser classical の満足化の走査順の揺らぎ τ(宣言 1.0・感度 0.5/2.0)
  - `--clock`: 第 6 期 6-3 時計の段 T4 場所ごとの時計の腕(既定 global・環境変数 SHIBUYA_CLOCK と同じ。指定すれば環境変数より強い)。regional=区域(セルの重心の 500 m の塊)ごとに窓を進め、区域をまたぐ事象は境目で届ける(結果は global と同じでなければならない)。mixed=口だけ(値は空欄=選ぶと止める)。既定と違えば設定の指紋に入り、ランの種類は arm(manifest の clock・clock_kind)
  - `--contact`: 第 6 期 6-4 連絡の道具 C1 の腕(既定 off=今の道・環境変数 SHIBUYA_CONTACT と同じ。指定すれば環境変数より強い)。c1=1 対 1 とグループのメッセージ・電話・チャットの会話の状態・目と心の向き(届くのはエンジン・気づく/読む/返す/出る/切るは本人の判断の口=仮のモデル)。下の腕は環境変数だけ(SHIBUYA_CONTACT_UNNOTICED=i/ii/iii・SHIBUYA_CONTACT_SEND=b/c)。c1 は結果を変えるので設定の指紋に入り、ランの種類は腕(manifest の contact_c1 に出る)
  - `--conv-max-participants`: C10 8a(D-93 (d)): 会話の参加上限(既定 2・3=会話中の相手に話しかけた体が加わる)
  - `--decision-port`: 第 1 期 1-8 候補の口 J0 の腕(既定 legacy=今の道・環境変数 SHIBUYA_DECISION_PORT と同じ。指定すれば環境変数より強い)。port で判断の 1 呼を候補の口に通す(候補は 5 つの源・順のシャッフル・番号で返す・mock と古典は今と同じ番号=結果は同じ)。口は結果を変えないので設定の指紋には入らない(manifest の decision_port に出る)
  - `--derive-rule`: 在圏ブロックの読み口(設計書 §2 追補 2026-09-12)。v2=域外居住者の自宅側の行(乗車前の「移動 駅」・帰りの乗車後の店)を在圏に読まない。v2.1=v2+乗車に隣接しない先頭/末尾の移動・支度をブロックから落とす(移動行=行程全体)。v1=原則のまま
  - `--duties`: 第 6 期 6-6 ② 第 1 部 店の仕事の腕(既定 off=今の道・環境変数 SHIBUYA_DUTIES と同じ。指定すれば環境変数より強い)。arm=開閉店・補充(品出し)・売れ残りの廃棄を、担当(雇用の行)が店に居る店では本人の判断にする(店の決まり=営業時間は担当が知る・棚が減ったら気づく・閉めた店の売れ残りを捨てる・判断は仮のモデル)。担当が居ない店は今の conf 宣言つきのつなぎ。arm は結果を変えるので設定の指紋に入り、ランの種類は腕(manifest の duties に出る)
  - `--eatery`: 段 1b(D-96 nightlife (b)): 行動語「食事」が成立する飲食店の集合。food=現行(cat の価格帯「飲食」・既定・checkpoint はバイト不変)/place_food=W17 の場所語「飲食店」と同じ集合(food+nightlife のうち club/karaoke/sauna/net_cafe でないもの)。価格は動かさない
  - `--economy-stage2`: 第 2 期 2-1 経済の段階 2 の腕(〔2-4 V4〕既定 on・環境変数 SHIBUYA_ECONOMY_STAGE2 と同じ。指定すれば環境変数より強い)。on で賃金(給料日)・引き出し(ATM)・支払いの方法(現金/口座)・レジの消費税・来街者の口座を動かす(manifest の economy.stage2 に出る・設定の指紋には入らない)。off=2-1 までの既定=切替口(旧値の再現)
  - `--economy-stage2-parts`: 第 2 期 2-1 経済の段階 2 の部品(カンマ区切り・既定=全部 wages,withdraw,payment,tax,visitors・環境変数 SHIBUYA_ECONOMY_STAGE2_PARTS と同じ)。1 つずつ測るため
  - `--energy-rate`: 消費の式(--hunger-model energy のときだけ効く)。eer=EER/1440×METs/基準日の平均 METs(既定・K1 (c))/bmr=基礎代謝量×METs(感度腕・K1 (a))
  - `--environment-seed`: 10f 環境の seed(気象の再生実日・大きな催し・道路工事。省略=--seed と同じ=今と同じ)。天気は同じで動きだけ変える比較では固定する
  - `--events`: 第 1 期 1-3: 出来事の記録(既定 on)。off で記録しない(環境変数 SHIBUYA_EVENTS=off と同じ)。記録は結果を変えないので設定の指紋には入らない(manifest の日次の記録 events.on に出る)
  - `--exit-mode`: 退出の実行形(設計書 §10-3)。immediate(既定=即時)/ walk_to_platform(9a=その体の路線のホームへ歩いて受容関数を通して乗る)・board_intent は予約(NotImplementedError)
  - `--experiment`: 第 3 期 3-3 反実仮想の申込書(JSON のパス・engine.experiment.form)。既定なし=今と同じ。渡すとランの種類は counterfactual・申込書の指紋は manifest の experiment に出る(設定の指紋には入らない)
  - `--experiment-aa`: 第 3 期 3-3 改変を空にした A/A の枝として回す(--experiment-branch と一緒なら 3 本とも A/A)
  - `--experiment-branch`: 第 3 期 3-3 分岐の基準のランの記録(tape/・state/・checkpoints.json のあるディレクトリ)。--experiment と一緒に使う。T0 までテープを再生して T0 から今の方策で続け、A/A の枝 2 本と改変の枝 1 本を回して R-71 の 4 つの確認を書く(<記録>/branches/<申込書の指紋の先頭 16 字>/branch_report.json)。〔3-3b〕申込書の T0 は計算のまとめの窓の頭(基準のランの batching.width_s ずつ)でなければ止める(3-3 では刻みの頭でない T0 を切り上げて受けていた=3-3b で止める形に変えた・申込書の T0 を黙って丸めない)
  - `--experiment-model`: 第 3 期 3-3 申込書のアンサンブルのモデルの札(札が 2 つ以上のときに渡す・封印の入口で seed の 3 つと合わせて照合)
  - `--familiarity`: 4 段目(記憶の先行部品=M13 訪問+M17 露出): 体×K 行の親しみの表を確保して、訪問・看板の露出・セルに入った回を数える(本段では誰も読まない)。既定 off=表を確保しない=既定の checkpoint 不変
  - `--familiarity-k`: 親しみの表の体あたりの行数(既定 64・宣言・感度 32/128)
  - `--geometry`: 位置幾何(C9 G1/G2・docs/design/v2-c9-geometry-agenda.md §4)。node=現行の 1 tick=1 ノード(既定・checkpoint はバイト不変)/edge=辺上の連続位置(edge_id・辺上距離・向き)+希望速度 Uniform(1.00,1.60) m/s+Kladek 式の密度減速。edge では密度段が人/m² の Fruin LOS 段になる
  - `--group-norms`: 第309(Q150): 群・規範の計器(D-107 (a)・読むだけ=final は変わらない)を回すか(既定 on)
  - `--home-meal`: 第2波 §2B 項 2(Q35 (a)): 範囲内の自宅の食事行。off=旧(食事は飲食店でしか成立しない・既定)/plan=行の開始に自宅に居て起きていれば予定の実行として食べる(金と物は動かさない・照合から外す)
  - `--hunger-model`: 5 段目 5a(D-118): 空腹のモデル。energy=体のエネルギー収支(既定・体重と EER・活動の METs で消費・食事/軽食/飲料で摂取・B5 は語)/v1=旧規則(+1/30 分・購入/食事で −4)=旧 checkpoint の再現
  - `--hunger-words`: 第2波 §2B 項 3(Q31 (b)): B5 の空腹の語。hungry=空腹以上だけ描く(既定=旧)/all=満腹・ふつうも描く
  - `--intent-max-ticks`: 段 2c(意図の保持・D-112 ①): セル外の対象へ歩く意図の上限[tick]。超えたら TOO_FAR(既定 60・宣言・expedient・感度腕 30/120)
  - `--intent-mode`: 行動の出させ方(AB7 自由意図の腕・docs/design/v2-open-intent-arm-spec.md §2)。vocab=24 語のホワイトリストを B0 で見せる(既定・現行のバイト)/open=語彙を見せず『いま自分がしたいこと』を 10 字以内の動詞句で書かせ、接地はエンジン側(行動契約書 §7 段0〜1)に任せる/hint=語彙を例として見せたうえで、当てはまる語が無いときだけ 10 字以内の自由文を許す(AB7b・vocab と open の中間)
  - `--l4-scale`: 呼数の上限の倍率。**既定 0=無制限**(3 段目・D-99 (a′)・D-110=L4 は監査線・manifest に llm_calls_per_agent_day と l4_exceeded)。1.0=旧挙動(L4 400 万呼/日を体数按分・持ち越し 2 tick)・0.5/2.0=半分/倍。PENDING D-99 AB8 の腕
  - `--meal-gate`: 第2波 §2A 項 4(Q48): --policy classical の食事の門の確率の読み方。per_wake=起床ごと(既定=旧)/per_hour=1 時間あたりと読み前回の門からの経過分で換算(既定の切り替えは食事の束の版上げで確認)
  - `--meal-sleep-defer`: 第2波 §2B 項 1(Q34 (b)): 範囲外の既定の食事時刻に W17 で就寝中の体。off=旧(そのまま食べる・既定)/on=起床の時刻へ遅らせ、時間帯の窓の中なら食べる(過ぎていれば無し)。--hunger-model energy のときだけ効く
  - `--memory`: 6 段目 6a/6b(記憶 第 1 段): 体×N 行の記憶の表を確保して、行動の成否・会話・気づき・強い看板(初見)を書き(6a)、各呼で k 件を想起して B5 の最後に「記憶」の 1 行を載せる(6b)。既定 off=表を確保しない=既定の checkpoint も描画バイトも不変
  - `--memory-cue`: 第 6 期 6-5 想起の手がかりの腕(既定 id=その場の手がかり=ID の一致・環境変数 SHIBUYA_MEMORY_CUE)。embed=意味の手がかり(埋め込み=--memory-embed-model・会話中は相手の直前の発言・ほかは本人の直前の理由)
  - `--memory-embed-model`: 第 6 期 6-5 埋め込みのモデル(既定 ruri-v3-30m・環境変数 SHIBUYA_MEMORY_EMBED_MODEL)。Ruri の重みは data/models/ruri/ に版を固定して置く(本段では未取得)。ngram-test は重みの要らない試験用の代わり(意味ではない)
  - `--memory-grain`: 第 6 期 6-5 体の出来事を記録へ書く粒度の腕(既定 each=1 回 1 行・環境変数 SHIBUYA_MEMORY_GRAIN)。day=同じ記憶の行は日に 1 行(2-3 の 14.6 行/体/日を減らす案)。再開には対応しない
  - `--memory-model`: 第 6 期 6-5 記憶の強さの式の腕(既定 m0=今の式・環境変数 SHIBUYA_MEMORY_MODEL と同じ。指定すれば環境変数より強い)。m1=ACT-R の折衷形(時刻は秒・+1 なし・最短の符号化時間・忘れる速さの人ごとのばらつき 15%%・境目 τ は仮の値)。--memory-store events のランだけ効く(記憶 off のランで立てると止める・結果を変える腕=ランの種類は腕・manifest の設定の節 memory_summary.mr65_arms と設定の指紋に入る・計器は memory_summary.memory_store.mr65)
  - `--memory-n`: 記憶の表の体あたりの行数(既定 128・宣言・感度 64/256)
  - `--memory-people`: 第 6 期 6-5 人も記憶の一つの腕(既定 table=今の関係の層・環境変数 SHIBUYA_MEMORY_PEOPLE)。memory=人を同じ器・同じ式(出来事 128・店 32 の固定の上限を外し、種類ごとの上限 256 まで幅を倍に・上限で思い浮かぶ強さの一番低い行を消す・忘れる=消す・関係の表を読まない)。--memory-model m1 が前提・再開には対応しない
  - `--memory-store`: 第 1 期 1-6 記憶の器 M0 の腕(既定 mem=今の記憶の表だけ・環境変数 SHIBUYA_MEMORY_STORE と同じ。指定すれば環境変数より強い)。events で --memory on のランに記憶の器(出来事の記録への目印)を作り、想起を器から引き、テープに列 recalled_event_ids を足す。器は結果を変えないので設定の指紋には入らない(manifest の memory_summary.memory_store に出る)
  - `--memory-tau`: 6b(想起): A ≥ τ の行だけ想起する閾値(既定 −2.0・第295 の決め・--memory on のときだけ効く)
  - `--move-search-radius`: 段 2b(D-112 ②): 移動の対象がカテゴリ語のとき、現在セル・見えている POI に候補が無ければ cell_dist の近い順に見るセルの数(既定 5・宣言・0=近傍探索しない)
  - `--no-outside-suppression`: D-66 域外抑止を切る(域外滞在・乗車中の体にも LLM を呼ぶ=D-66 前の挙動・帰無腕)
  - `--no-plan-executor`: D-66 計画実行層(engine.presence)を切る(=rail の乱数 12%% + D-61 帰りの便 + D-62 の run.py 発火=現行挙動・帰無腕)
  - `--no-plan-sleep`: D-62「就寝は計画の実行」を切る(就寝境界も LLM に判断させ・tick 0 は全員 SLEEPING=D-62 前の挙動・帰無腕)
  - `--no-population`: W16 母集団を使わず合成個体で回す(下限対照・世帯財布も mock のまま)
  - `--no-signage`: 看板・広告面(B2.signage)を全セルで空にする(§8 第1陣 ⑥「広告ゼロ」の腕)
  - `--no-sleep-suppression`: D-56 就寝抑止を切る(就寝中の個体も内受容/セル変化で呼ぶ=D-56 前の挙動・帰無腕)
  - `--occupancy-every`: 在圏 journal の記録間隔[tick]\(0=書かない・C7 受入計器の入力・毎正時なら 60)
  - `--occupancy-out`: 在圏 journal の出力 .npz
  - `--pnotice-d50-scale・--p-notice-d50-scale`: p_notice の d50 を倍率で振る(知覚契約書 §8 第1陣 ② の腕。既定 1.0=40 m・0.5=20 m・2.0=80 m。2.0 は打ち切り 80 m と同値になる)
  - `--policy`: 5 段目 5b(D-119 L5): 起床ごとの応答を作る方策。mock=凍結の MockLLM(既定)/classical=LLM 0 呼の古典的選択モデル(食事の門+社会生活基本調査の活動の事前分布+対応表 v0・語彙 v3 だけ)
  - `--population-seed`: 10f(K21 (a))母集団の seed(W16 の抽出・mock 日課・体の定数・財布・域外居住・合成世界。気象は--environment-seed。省略=--seed と同じ=今と同じ)。--seed は動きの seed(salt)。salt の比較では母集団の seed を固定して --seed だけを変える
  - `--proximity-d`: 第 2 期 2-2 段 11a 会話の距離 d[m] の感度の腕(既定 2.0=B3 の決め打ち・環境変数 SHIBUYA_PROXIMITY_D と同じ。近接の判定=同じ層・距離 ≤ d の d。〔第346〕--proximity cell の切替口は消した)
  - `--queue-service`: D-113 ③: 満席で並んだ体を席が空いた分だけ並んだ順に席へ入れる(既定 on)。off=第267 以前の挙動(誰も捌かず 15 tick で INTERRUPTED)
  - `--rate-rules`: 〔11-01 段 2 の 4〕率の形の規則の切替口(既定 off・環境変数 SHIBUYA_RATE_RULES と同じ。指定すれば環境変数より強い)。off=率の形の規則を外した状態(催しの 200 人注入・E8 の到着の分散・乗車の受け入れ確率・ポイ捨て・売れ残りの廃棄率・宅配・倒れる率が無い=宣言は engine.rate_rules)。legacy=版上げの前の値の再現のためだけの道(次の版上げで消す)。出勤率のくじ(旧 --attendance-rate)はどちらにも無い=全員出勤。腕は設定の指紋に入れない(manifest の rate_rules に出る・既定と違えばランの種類は arm)
  - `--refractory-scale`: §6 不応期表を条件ごとに倍率で振る(§8 第1陣 ③ の腕。繰り返し可。例 --refractory-scale PROXIMITY_SWAP=0.5。条件名は WakeCondition の 11 行)
  - `--rel-acq-wake`: C10 8b(R7 (a)): 知人出現の起床(同一相手 60 分・--relations on のときだけ効く・既定 on)
  - `--rel-copresent`: C10 8b(Q91): 同席の書き手(同セル・2 m 内・連続 5 分で 1 本・相手ごと 1 日 1 本・既定 off)
  - `--rel-d`: 関係辺の A の減衰 d(既定 0.5=記憶と同じ・感度 0.25/0.75)
  - `--rel-init-density`: 初期網の密度の腕(0.5=共在が中央値以上・1.0=共在 > 0・2.0=共在 0 の組も入れる)
  - `--rel-invite`: C10 8b: 名指しの無い会話の相手を関係辺の重み(5 人 40%%・10 人 20%%・残り 40%%)で引く(--relations on のときだけ効く・既定 on)
  - `--rel-k`: 関係辺の数(既定 15・感度 5/50)
  - `--rel-tau`: 辺として残る A の閾値 τ_rel(既定=在職期間のハッシュ v2 での全母集団の逆算 −2.322・感度 ±0.5)
  - `--rel-tenure-weeks`: C10 8b(Q89/Q90): 初期辺の在職期間 T_uv の上限[週]\(既定 13・感度 26)
  - `--relations`: C10 8a(関係辺): 体×15 辺の関係の表を確保し、W16+W17 の共在で初期化・会話/手伝いのエピソードから書き、B5 近接行の「知人」の印に結線する(--memory on のときだけ)。既定 off=既定の checkpoint 不変
  - `--replay`: 録画テープのディレクトリを与えると mode=replay(テープ完全一致・LLM 呼なし)で回す(C7 T2-c: 本番テープの再生で checkpoint 列を復元する)
  - `--report-precondition`: D-113 ②: 通報の前提「当該事象を知覚済み」の検査(既定 on)。off=従来どおり必ず成功(第266 以前の checkpoint ba01bd0b を再現する帰無腕)
  - `--role-words`: D-113 ④: B0 の末尾に役割語 12 語の 1 行を足す(既定 on・行動契約書 §2.2)。off=第268 以前の B0(それ以前に録ったテープの再生・帰無腕)
  - `--seat-area-eatery`: 飲食(food/nightlife)の 1 人あたり床面積[m²]の感度腕(既定=現行 2.0 のまま)。法定: 消防法施行規則 1 条の 3(三)項ロ **3.0** / 建告1441 飲食室 0.7 人/m² **1.43**
  - `--seat-area-retail`: 物販その他の 1 人あたり床面積[m²]の感度腕(既定=現行 4.0 のまま)。法定: 消防法施行規則 1 条の 3(四)項ロ **4.0** / 建告1441 売場 0.5 人/m² **2.0**
  - `--seed`
  - `--signage-p-see`: 看板の注視ゲート(知覚契約書 §4 段1 の視認確率 p_see・D-59 (b)・腕 AB6b-AD-NOTICE)。在圏セルの看板行を観測へ入れるかを 体×看板×tick の決定論的ベルヌーイで決める。既定 1.0=常に載せる(現行のバイト)・0.30/0.14=実測帯 0.14-0.79 の下側・0.0=⑥ 広告ゼロと同じ描画
  - `--speech-port`: 第 1 期 1-8b 発話の口の腕(既定 off=今の道・環境変数 SHIBUYA_SPEECH_PORT と同じ。指定すれば環境変数より強い)。on で会話の番の呼び出しだけ B6 の末尾に ひと言 の欄を求め(語彙 v3)、答えの ひと言 を発話の口に通す(出来事の記録に 1 行・相手の次の入力の B6 に素性タグと命令文の除去つきで載る・口コミの抽出に渡す)。on は結果を変えるので設定の指紋に入り、ランの種類は腕(manifest の speech_port に出る)
  - `--step-scope`: 第 6 期 6-3 時計の段 T3 何かあった体だけの腕(既定 all・環境変数 SHIBUYA_STEP_SCOPE と同じ。指定すれば環境変数より強い)。changed=体の反映を TM5 の予約(3-5 の reserve)にし、内受容の段の跨ぎの判定を変化の印の体だけに通す(結果はall と同じでなければならない=一致の確認)。既定と違えば設定の指紋に入り、ランの種類は arm(manifest の step_scope)
  - `--store-capital`: 店舗の参入資本を一律[円/店]で上書き(既定=経済センサス按分・D-13)
  - `--store-decay`: 店の評価の減衰の形(既定 actr=ACT-R d=0.5・ga=0.995/時・citysim=中立回帰 0.03/日=感度腕)
  - `--store-memory`: D-120 7a(店の評価の記憶): 体×32 行の店の評価の表を確保し、記憶のエピソード(購入/食事/並ぶの成否・看板の初見)から書く(本段では誰も読まない)。--memory on のときだけ。既定 off=表を確保しない=既定の checkpoint 不変
  - `--store-memory-n`: 店の評価の表の体あたりの行数(既定 32・宣言・感度 16/64)
  - `--store-recall-scope`: D-120 7c: B5 の想起で店の行を候補にする入口(既定 all=全入口・conversation=会話だけ=感度腕)
  - `--store-sigma`: 出どころ別の雑音 σ(例 '{"self": 1, "wom": 1, "signage": 1, "net": 1}'・既定 自分 1/伝聞 2/看板 4/ネット 2=宣言・感度腕)
  - `--store-signage`: D-120 7c(N8 の腕): 看板の初見から店の行を書くか(N2 (iii)・既定 on)
  - `--store-wom`: D-120 7c(N8 の腕): 口コミ(7b の聞き手への転写)を使うか(既定 on・--store-memory on のときだけ)
  - `--talk-clock`: 第 6 期 6-3 時計の段 T2 会話の時計の腕(既定 table・環境変数 SHIBUYA_TALK_CLOCK と同じ。指定すれば環境変数より強い)。table=今の 1 ターンの長さの表(1 呼=1 発話ブロック=刻み 1 つ)。mora=発言の長さをモーラ数 × その人の話す速さ(人ごとの値+発言ごとの揺れ・R-111 §3)で数え、会話ごとの時計(間=日本語の平均 7 ms)を窓の待ち行列の事象として時刻順に処理する(計器だけ=会話の番は今も刻みに 1 回)。既定と違えば設定の指紋に入り、ランの種類は arm(manifest のtalk_clock に出る)
  - `--ticks`
  - `--undefined-out`: 未定義行動台帳(行動契約書 §7 段1)を JSON で書く(D-71 段2 起草バッチ tools/vocab/adjudicate.py の入力)。空=書かない(既定・出力は 1 バイトも増えない)。**ランの中では裁定しない**(語彙成長の設計 v0 §2: ラン後オフライン)
  - `--vocab-version`: 行動語彙の版(語彙成長 v0・docs/design/v2-vocab-growth-design.md §3 F)。v1=24 語(D-113 以前からの既定・v1 の checkpoint を再現するときは明示)/v2=24 語 + 横断語「食事」(飲食店オブジェクトの affordance)/v3=行為と活動の二層(D-116・**CLI の既定**=第277): 横断 11 語+なし・5 ラベル形(理由・行動・対象・活動・まで)・活動層(--activity)・段0 辞書 v5。v3 は --intent-mode vocab だけ
  - `--wom-source`: 第2波 §2A 項 1(Q57): 口コミの抽出の源。utterance=発話の欄(ひと言)だけ(既定・いまの語彙 v3 にはひと言欄が無い=抽出 0)/ reason-target=旧(v3 で理由欄+対象欄=本人の内心が聞き手に漏れる欠陥・旧の再現用)。--store-memory on のときだけ効く
  - `--world`
  - 名前を読めない呼び出し 1 か所
- 決定の ID: 09-25・11-01・11-02r・11-02r/§1・11-02r/§1 #7・R-71・R-111・D-13・D-53・D-55・D-56・D-58・D-59・D-61・D-62・D-66・D-71・D-76・D-93・D-96・D-99・D-107・D-110・D-112・D-113・D-114・D-116・D-118・D-119・D-120・第 175・第 204・第 205・第 266・第 267・第 268・第 277・第 289・第 291・第 295・第 309・第 330・第 346
