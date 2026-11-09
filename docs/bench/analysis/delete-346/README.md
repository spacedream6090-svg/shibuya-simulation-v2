# 第346 旧道の切替口と死んだ道の削除(返事その 6 §3-2 の 1・2/返事その 7 §2 の 5)

> 整理の段(既定の結果を変えない段=byte-check の 25 欄は 1 バイトも動かない・§5 の 37 欄では manifest の台帳の数と版だけが
> 想定どおり動く)。発注: [返事その 6](../../../design/prompt-2026-11-05-reply6.md) §3-2 の 1・2、
> [返事その 7](../../../design/prompt-2026-11-09-reply7.md) §2 の 5。手順の正: [6-1 のメモ](../../../design/v2-prep-6-1-notes-2026-10-25.md)
> §2(2-0 共通の手順)。前例: [pop43 §19](../wallbounce-1012/pop43/README.md)(#118 第 2 部)。
> 土台 `6753891`(枝 `stage/delete`)。実装役 Opus 5.5。commit とタグは親。親の仮採用(Q6・見出しの鍵・Q12)は §2 の通り。

## 0. 要点

- 10 本のうち **7 本を消した**: 1 `SHIBUYA_RULES_42B`・2 `SHIBUYA_RULES_42`・3 `--seat-release legacy`・4 `--proximity cell`・
  8 `--defect-fixes-1103 legacy`・9 会話の応答率 0.8 の抽選・10 重要度上位の +2 呼。消すたびに byte-check 19 構成 25 欄が
  **19/19 同じ**(final `w6_v3_default` = `c8d68704b7b0760d` / 60,939 呼・§5)。検収の直し(§9)の後も 19/19 同じ。
- 親の新しい 37 欄の道具(本体 `05be3f1` の `tools/bytecheck`)では、19 構成で 25 欄・テープの全ファイルの sha256・calls と
  blocks の型と見出し・run_meta・全 checkpoint は同じ。動いたのは manifest の `bridges_count`(763 → 758)・`bridges_version`
  (`f863a81abc920fb7` → `f3124555db1edc23`)・それを写す `daily[*].bridges_count` の 3 欄だけ(arms の組では
  `calendar_1b.bridges.count` も)=つなぎの台帳の 5 行を removed にした結果で想定どおり。道具の終了コードは 1(動いた欄がある)
  になる(§5)。
- **3 本は止めた**: 5 `--economy-stage2 off`・6 `--rate-rules legacy`・7 `--absent-processes legacy`。旧道が旧値の再現だけでなく、
  ほかの試験の**駆動か基準**に使われている(§3)。消し方(試験を消す/書き直す/試験だけの口を残す)に親の判断が要る。
- 旧値の再現は安定版のタグ **`stable-v2-before-switch-removal-346`**(親が `6753891` に打つ)。
  **戻す手順**: `git checkout stable-v2-before-switch-removal-346`。
- 消した切替口を渡すと止まる。環境変数はランの入口(組み立て `systems/build.py` の `build()` の最初=刻みの前)と、切替口を
  持っていたモジュールの読み込みで `ValueError`(文に「消した切替口」とタグの名・値によらない)。一覧と止める文は
  `engine/removed_switches.py` の 1 か所。CLI の旗は表に出さない旗として受けて引数の誤り(`SystemExit` 2・略記でも)。
  見出しに旧道の値が無い状態のファイルは、再開で止まる(文にタグの名)。
- 触らないもの(発注どおり): `--space legacy`(6-1 のメモ Q7 が未決)・`--hunger-model v1`(Q13 が未決)。

## 1. 消したもの(項目ごと)

| # | 切替口 | 消したもの | 渡したら |
|---|---|---|---|
| 1 | `SHIBUYA_RULES_42B`(4-2 の値の再現) | `economy_rules` の `ENV_42B`・`DEFAULT_ARM_42B`・`_ARM_42B`・`arm_42b`・`set_arm_42b`。組み立ては常に `PayrollInputs.rules_42b=True`(欄の既定)。再開の検査は見出しの `rules_42b` が `on` かだけを見る | 環境変数=ランの入口と読み込みで止まる(値によらず・段階 2 の台帳の無いランでも)・見出しに `rules_42b=on` の無い状態のファイル=再開で止まる |
| 2 | `SHIBUYA_RULES_42`(4-2 の前の値の再現) | `economy_rules` の `ARMS`・`DEFAULT_ARM`・`_ARM`・`arm`・`set_arm`。組み立て(`economy_stage2.attach`)は常に `law=payroll_inputs(...)`。再開の検査は `rules_42` が `on` かだけ | 同上(`rules_42`) |
| 3 | `--seat-release legacy`(`SHIBUYA_SEAT_RELEASE`) | `seat_release` の `MODES`・`_ARM`・`arm`・`set_arm`・`is_walk`/CLI の旗と腕の数え/設定の箱の欄 `seat_release`/`act` は常に `seat_release_walk=True`/manifest の `leave_effects.seat_release` は `"walk"` に固定/見出しは常に `{"mode": "walk"}`/系の表の読み `cfg.seat_release`(5 か所) | 環境変数=止まる・CLI=引数の誤り・見出しに無い(2-4 より前)=再開で止まる |
| 4 | `--proximity cell`(`SHIBUYA_PROXIMITY`) | `proximity` の `_ARM`・`arm`・`set_arm`/CLI の旗と腕の数え/組み立ては常に近接の規則と層を作る/再開の検査は今の腕を `distance` に固定(d の違いは `--proximity-d` の文で止める)/古い注(「切替口 cell は None=同じセル」4 か所と会話の docstring の 1 行) | 環境変数=止まる・CLI=引数の誤り・見出しに無い(cell のラン)=再開で止まる |
| 8 | `--defect-fixes-1103 legacy`(`SHIBUYA_DEFECT_FIXES_1103`) | `defect_fixes_1103` の `_ARM`・`arm`・`set_arm`(`resolve(None)` は `on`)/CLI の旗と腕の数え/設定の箱の欄 `defect_fixes_1103`/系 `talk.py` の旧道の分かれ 2 か所(全員を IDLE に戻す `resolve.revert_conversation`)/`act`・`judge` は常に直した道(`defect_fixes=True`・`drop_unreachable=True`・`keep_activity=True`)/組み立ては常に `count_unreachable=True`/manifest の `mode` は `on` に固定/見出しは常に `{"mode": "on"}`/系の表の読み(7 か所) | 環境変数=止まる・CLI=引数の誤り・見出しに無い(版上げの前)=再開で止まる |
| 9 | 死んだ道: 会話の応答率 0.8 の抽選 | `conversation` の `ACCEPT_PROBABILITY`・`_accepts`・引数と欄 `accept_probability`・乱数の用途名の引数と欄 `domain`・`INVITE_RNG_DOMAIN`/`invite` の `answered` は必ず渡す(既定なし)/乱数の静的な呼び手の表 `rng_audit.SAFE_SITES` の 1 行/動きの側の用途名の表 `run.MOTION_RNG_DOMAINS` の `conversation.invite`/状態台帳の会話の器の設定の欄(`accept_probability`・`domain`=3 行)/docstring の expedient の見出しの項 1 つ | `ConversationManager(accept_probability=…)`・`invite(...)` で `answered` を渡さない=`TypeError` |
| 10 | 死んだ道: 重要度上位の +2 呼 | `conversation` の `IMPORTANT_EXTRA_TURNS`・引数と欄 `important`・`extra_turns_for_important`/`max_turns_for` は全員 `max_turns`/状態台帳の会話の器の設定の欄(3 行) | `ConversationManager(important=…)`=`TypeError` |

旧値の再現は、どの項目も安定版のタグ `stable-v2-before-switch-removal-346`。
戻す手順は 1 行で `git checkout stable-v2-before-switch-removal-346`。

## 2. 残したもの(理由)と親の仮採用の当て方

### 2-1 Q6=部品の単体試験の基準の口は残す(ランの口=CLI・環境変数・`run_day` の引数・設定の箱の欄からは選べない)

| # | 残した口 | 使う試験 |
|---|---|---|
| 1 | `PayrollInputs(rules_42b=False)` を直に作る物・`taxes.payroll_tables(r42b=False)`(4-2 の式)・`EMPLOYER_ITEMS_42` | `test_rules42_payroll.py`(手計算 13 本)・`test_rules42b_payroll.py`・`test_rules42b_ledger.py` の部品の口の 2 本 |
| 2 | `law` の無い `Stage2Plan`(`MoneyStage2` の 4-2 の前の値の道=天引き 0・税は売った時点) | `test_rules42_ledger.py::test_without_law_the_old_values_are_kept` |
| 3 | `resolve.apply(seat_release_walk=False)`(関数の既定) | `test_seat_release_2_4.py` の対の試験 |
| 4 | `ProximityRule(mode=MODE_CELL)`・下の関数の `proximity=None` の道(`act`・`judge`・`perceive`・`talk`) | `tests/engine/proximity/test_rule.py` ほか |
| 8 | `resolve.apply(defect_fixes=False)`・`run._settle_pending_invites(drop_unreachable=False, keep_activity=False)`・`ConversationManager(count_unreachable=False)`・`defect_fixes_1103.manifest_fields("legacy")` | `test_defect_fixes_1103.py` の `fix`・`keep` の対の試験 |

### 2-2 manifest と状態のファイルの見出しの鍵は値を既定の 1 つに固定して残した

`economy_stage2.rules_42`・`rules_42b`(見出し)・`economy.stage2.plan.rules_42b`(manifest)・`leave_effects.seat_release`=`walk`・
`proximity.mode`=`distance`・`defect_fixes_1103.mode`=`on`・見出しの `seat_release`・`proximity`・`defect_fixes_1103`。
`CONFIG_PATHS_SHA256`(`test_env_and_sections_10f.py`)は張り替えていない=試験が通る。状態台帳の腕の行 TXD の腕の名
`rules-42` も残した(印。`alloc` の説明の文だけ直した)。

### 2-3 Q12=つなぎの台帳

行のある切替口は removed にした(§5)。行の無い 2 本(3 `--seat-release legacy`・4 `--proximity cell`=vb24 の腕)は、台帳に行を
足さず、ここに書くだけにした。

### 2-4 そのほか残したもの

- 感度の腕: `--proximity-d`(会話の距離 d)・`--economy-stage2-parts`(発注どおり)。
- `ConversationManager(master_seed, …)` の位置の引数 `master_seed`: 抽選は消したので今は記録だけ。呼び手の互換のため残した。
- 記録の道具(docs/bench の下): `rules42/tools/runs_rules42.py`・`rules42b/tools/runs_rules42b.py`(環境変数で腕を選ぶ)・
  `prox22/tools/*`・`vb24/tools/*`(`set_arm` を呼ぶ)は直していない。今の src では止まる。旧値の記録の再現は安定版の
  タグで回す。md23 の道具 `multiday_md23.py` の `set_arms` だけは試験が読むので直した(近接の腕は置かない。cell を
  頼むと止まる)。
- 試験の定数 `tests/engine/proximity/test_runs.py` の `HEAD_GOLDEN`(cell の腕の値)は、使う試験と一緒に消さずに記録の値として残した。
- src の注に「腕 `--proximity distance`」の言い方が 20 か所ほど残る(経緯の注)。今の既定と食い違う文(「切替口 cell は None」)
  だけ直した。

## 3. 止めた項目(5・6・7)

### 3-1 `--economy-stage2 off`(5)

- ランの口: `economy_stage2.py:90-92`(環境変数)・`:130-140`(`arm`・`set_arm`)・`:154`(`active_parts` が `_ARM` を見る)・
  `:172-187`(`check_resume` の `effective`)・`:778`(`attach` は off なら None)・`cli.py:293`(off なら台帳の雇用主 1 口・
  輪の係数 6.5)・`:508`(腕の数え)・`:1425`(旗)・`:1673`(`set_arm`)・`build.py:420-421`。
- 止めた理由: off を「段階 2 の外の台帳を見る基準」に使う試験がある。旧値の再現の試験ではないので、消すと覆いが減る。
  - `tests/economy/cp2/test_cp2_event_links.py::test_run_rows_and_events_are_one_to_one`(世界資産 200 体・率の規則の旧道とも組む)
  - `tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py::test_5k_default_day_does_not_overflow`(5,000 体・off の係数 6.5)
  - `tests/economy/cp2/test_cp2_nine_ops_equivalence.py::_mock_day`(slow・1-9 の台帳と HEAD の写しの同値=段階 2 の外でしか成り立たない)
  - `tests/engine/test_ledger_wiring.py`(モジュール全体が autouse で off=C4 の台帳の配線・faucet と sink の集合・容量の値)
  - `tests/engine/multiday/_md.py` の `arms()` の既定 off と md23 の道具の組 c・d
  - `tests/economy/stage2/` の 6 本(`test_stage2_default_2_4`・`test_stage2_resume_arm`・`test_stage2_rules_credit_atm`・
    `test_stage2_runs`=器の既定が off・`test_stage2_world_two_day`・`test_stage2_calls`)
- 案: (a) 段階 2 の外を見る試験を消す(旧値と同じ扱い)/(b) 段階 2 on で書き直す(期待値が変わる。HEAD の写しとの同値は
  成り立たない)/(c) 試験だけの口を残す(Q6 と同じ考え。例: `attach_stage2` を持たない台帳の物を渡す)。`cli.py:293` の
  台帳の作り方の分かれも、同じ判断に従う。

### 3-2 `--rate-rules legacy`(6)と `--absent-processes legacy`(7)

- 止めた理由: 倒れる率の試験の口 `run_day(salient_rate_per_10k=)` は旧道でだけ効く(`salient.py:180`)。出動は「無い」の過程の
  旧道でだけ動く。ランの中で「倒れる → 出動 → 到着 → 顕著行為」と、ごみ・補充の行を動かす試験が、この 2 つの旧道を駆動に
  使っている。
  - 率の規則: `test_salient`・`test_rng_scheme_10c`・`test_ablation23_switches`・`test_resume_10d`(378・499)・
    `test_salt_seed_split_10f`(276・423-424・471-472=子のプロセス `tools/c7/salt_runs.py` へ環境変数で渡す)・
    `test_state_checks_10f`(362・397)・`test_version_bump_10e`(323)・`test_waste_sink_report`(51・104)・`test_du_runs`(265)・
    `test_cp2_event_links`(142)。
  - 「無い」の過程: `test_rng_scheme_10c`(49)・`test_salient`(36)・`test_resume_10d`(381)。
  - 部品の口(過程の引数 `rate_rules="legacy"`・`absent_processes="legacy"`)を使う試験は `test_civic`・`test_goods_flow`・
    `test_logistics`・`test_rail_return`・`test_presence_executor`・`test_absent_processes_1102`(部品の口は残せる)。
- 案: (a) 駆動の試験を消す/(b) 過程の単体試験へ移す(部品の口は残す)/(c) 試験の口 `salient_rate_per_10k` を既定でも効く
  ようにする(挙動を足すので先に聞く)。6 と 7 は組で決めるのが筋。片方だけ消すと、倒れても出動しない形か、出動の駆動だけ残る
  形になる。台帳の行 `DOC-s2rates-legacy-switch` と `DOC-s2e-absent-legacy-switch` の why に、書き直す試験の一覧がある。
- 書き直す一覧には、切替口そのものの試験 `tests/engine/processes/test_rate_rules_1101.py`(既定の腕・名の検査・見出し・再開・
  manifest・CLI)と `tests/engine/processes/test_absent_processes_1102.py`(同じ形・legacy の側)も入る。
- 版上げの前の値の試験 `test_t7_legacy_switch_reproduces_the_pre_bump_final`(3 つの切替口を全部 legacy)は、8 と一緒に消した(§7)。

## 4. 既定のランで通らないことの確かめ(どの項目も同じ 3 つ)

1. byte-check の 19 構成の引数(`tools/bytecheck/configs.py`)は、どれも消した切替口を渡さない。消した切替口は `run_day` の
   引数ではなく、環境変数か CLI の旗でしか選べなかった。道具の `one` は `shibuya.cli.run(**引数)` を呼ぶ(argparse を通らない=
   旗は渡らない)。
2. 組 `all19` の両側の環境変数は空(`configs.set_env("all19") == {}`)。道具の `run` は、呼び手の環境に `SHIBUYA_` の変数があると
   止まる。各 byte-check の side の JSON の `env`・`env_hidden` は全部 `{}`・`[]`(確かめの道具の出力=§4 の表の各回)。
3. src の呼び手: 腕を選ぶ口(`set_arm`・`set_arm_42b`)を呼んでいたのは `cli.py`(旗の処理)と試験だけ(カード
   `docs/reference/repo-guide/cards/src/shibuya/engine/README.md` の呼び手と grep で確かめた)。基準 `6753891` の既定の値は、
   どれも新しい道(`rules_42`・`rules_42b`=on・`seat_release`=walk・`proximity`=distance・`defect_fixes_1103`=on)。
   死んだ道の 2 本(9・10)は、呼び手(会話の系 `systems/talk.py`・連絡の道具 `contact/layer.py`)が全部 `answered=True` を渡し、
   組み立て(`systems/build.py`)は `important` を渡さない(台帳の行の確かめと grep で確かめた)。

## 5. byte-check(19 構成・25 欄・5,000 体・seed 1・1 日・mock・本体の世界 W21)

道具 `python tools/bytecheck/cli.py run --base 6753891 --work C:\bcdel --set all19 --jobs 6`(比べる側は作業木の src)。結果の
JSON は [bytecheck/](bytecheck/) に写した(絶対パスは無い)。

| 項目 | 一致 | final(w6_v3_default) | 壁時計 |
|---|---|---|---|
| 1 `SHIBUYA_RULES_42B` | 19/19 | `c8d68704b7b0760d` / 60,939 | 421 秒 |
| 2 `SHIBUYA_RULES_42` | 19/19 | 同じ | 412 秒 |
| 3 `--seat-release legacy` | 19/19 | 同じ | 413 秒 |
| 4 `--proximity cell` | 19/19 | 同じ | 403 秒 |
| 8 `--defect-fixes-1103 legacy` | 19/19 | 同じ | 413 秒 |
| 9 応答率 0.8 の抽選 | 19/19 | 同じ | 414 秒 |
| 10 重要度上位の +2 呼 | 19/19 | 同じ | 417 秒 |

- どの回も、基準の側と比べる側の 19 構成で、25 欄すべてが同じ・動いた 0・誤り 0(終了コード 0)。
- 置いた JSON: 項目ごとの compare(`item<番号>_<名>_compare.json`=7 本)と、基準の side(`all19_base_6753891.json`=どの回も同じ
  構成・同じ値)・最後の回(項目 10 の後=今の作業木)の比べる側の side(`item10_all19_work.json`)。ほかの回の side はスクラッチに
  置いた(1 本 154 KB)。
- 各回の side の `env`・`env_hidden` は全部 `{}`・`[]`(§4 の 2)。

### 5-1 親の 37 欄の道具での確かめ(検収の後・親が回した)

本体 `05be3f1` の新しい `tools/bytecheck`(37 欄)で、基準=`05be3f1` の写し・比べる側=本段の作業木(検収の直しの前)の
19 構成を親が回した。結果 [bytecheck/parent37_compare_base_05be3f1_vs_work.json](bytecheck/parent37_compare_base_05be3f1_vs_work.json)
(side の 2 本はスクラッチに置いた)。

- 同じ: 19 構成すべてで、25 欄・テープの全ファイルの sha256・calls と blocks の型と見出し・run_meta・全 checkpoint。
- 動いた: manifest の `bridges_count`(763 → 758)・`bridges_version`(`f863a81abc920fb7` → `f3124555db1edc23`)・それを写す
  `daily[*].bridges_count` の 3 欄だけ(要約は `manifest_sha` と `manifest_fields_sha` の 2 つ=19/19)。arms の組では
  `calendar_1b.bridges.count` も動く。つなぎの台帳の 5 行を removed にした結果で、想定どおり。
- そのため道具の終了コードは **1**(動いた欄がある)になる。この 3 欄(arms では 4 欄)の外は動いていない。

## 6. 台帳

- 道具 [tools/ledger_delete346.py](tools/ledger_delete346.py)(冪等=2 回目は変化 0)。行の数は 794 のまま。
- removed にした行(why の末尾に「〔第346 旧道の切替口と死んだ道の削除〕閉じた: …。旧値の再現は安定版のタグ
  stable-v2-before-switch-removal-346」): `DOC-rules42b-legacy-switch`・`DOC-rules42-legacy-switch`・`DOC-fix4-defect-legacy-switch`・
  `DOC-fix4-dead-accept-probability`・`DOC-fix4-dead-important-extra-turns`。
- 文を改めた行: `HD-engine.conversation-1af925f4`(見出しの下の項 7 → 6=応答確率 0.8 の項を消した)。見出しの項の合計
  368 → 367(`tests/engine/bridging/test_bridging_ledger.py`)。
- 行の無い切替口(3・4)は §2-3。止めた 3 本の行(`DOC-s2rates-legacy-switch`・`DOC-s2e-absent-legacy-switch`)は active のまま。
- 台帳は manifest の `bridges_count`・`bridges_version` に写る=5 行を removed にしたので、この 2 欄(と日ごとの写し)は動く
  (§5-1。25 欄と final には入らない)。

## 7. 張り替えた試験

- 旧値の再現の試験 → 「切替口が無い・渡すと止まる」試験: `test_rules42b_ledger.py`(`test_removed_rules_42b_switch_env_stops`・
  `test_resume_refuses_a_header_without_rules_42b`・合成の 2 日は 4-2b だけ)・`test_rules42_runs.py`(`test_removed_rules_42_switch_env_stops`・
  `test_resume_refuses_a_header_without_rules_42`・off のランと on/off の比べを消した)・`test_seat_release_2_4.py`
  (`test_removed_seat_release_switch_env_and_cli_flag_stop`・見出しの検査・legacy のランを消した)・`proximity/test_rule.py`
  (`test_d_switch_is_checked_and_the_cell_switch_is_removed`・再開の検査)・`proximity/test_runs.py`(cell の golden の試験を消した・
  CLI は既定 distance と旗の誤り・再開は d の違いだけ)・`test_defect_fixes_1103.py`(`test_removed_defect_fixes_switch_env_and_cli_flag_stop`・
  系の試験の legacy の側を消した・ランの組は on だけ)・`test_conversation.py`(抽選の 3 本 → `test_the_dead_accept_lottery_is_removed`・
  +2 呼 → `test_the_dead_important_extra_calls_are_removed`)。
- 比べ方を変えた試験: `test_c9b_targets_attention.py`(cell で見ていた「C9b の計数が 0」を、近づく・焦点の 2 つで見る)・
  `test_render_from_percept_bytes.py`(19 構成のランの中の描画を HEAD 136fdbb の双子と比べる試験 (B) は、試験の中だけ
  `engine.proximity.rule_from` を None を返す物に差し替えて残した=組み立ての「規則の無い」枝で回す=検収 M2・§9)。
- 消した試験: `test_state_ledger_10b.py::test_t7_legacy_switch_reproduces_the_pre_bump_final` と定数 `T7_V3_FINAL_RATE_RULES_LEGACY`。
- 数の張り替え: 見出しの項の合計 368 → 367・`rng_audit.SAFE_SITES` 26 → 25(`test_state_checks_10f.py`)・乱数の用途名の対応
  `self.domain` → `{"llm.mock"}`(`test_salt_seed_split_10f.py`)。
- 見出しの期待(`test_stage2_default_2_4.py`・`test_stage2_resume_arm.py`・`test_wage_occupation.py`): 腕で分けず `rules_42`・
  `rules_42b`=`on` を書く。
- 多日の試験の共通 `tests/engine/multiday/_md.py` の `arms()`: 近接の引数を消したので、近接の既定が **cell から distance に
  変わった**。md23 の 2 本(`test_md23_resume.py`・`test_md23_body_events.py` の `arms()` を使う所)は今は distance で回る
  (ハッシュの定数は無い=再開と通しの一致・器の中身を見る試験)。
- 道具: `tools/bytecheck/configs.py` の `SWITCH_ENV` から 5 本を外し、`REMOVED_ENV` に移した(試験 `tests/tools/test_bytecheck.py`:
  前の道具の一覧との差=道筋の 1 本+消した分・`REMOVED_ENV` の名が src に残る=止める文)。`tests/engine/multiday/_md.py` の `arms()`
  から近接の引数を消した。

## 8. 試験

| 試験 | 結果 |
|---|---|
| 項目ごとの試験(変えたモジュールと関わる試験・`-m "not gpu and not slow"`) | 1: 通った・2: 604 passed・3: 333+56 passed・4: 481 passed・8: 628 passed・9: 652(1 本=`SAFE_SITES` の数を直して再実行 24 passed)・10: 583 passed |
| 範囲 `tests/engine tests/economy tests/perception tests/tools tests/test_cli*.py tests/vocab tests/llm tests/core`(`-m "not gpu and not slow" -n 4 --dist loadfile`・30 分 52 秒) | **4,912 passed・1 failed・0 errors・1 skipped**(収集の errors 0=junit の errors も 0) |
| 落ちた 1 本 `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` | 作業木の data がつなぎでテープの相対の道筋が作れない。基準 `6753891` の src の写しで同じ試験を回しても同じく落ちる=消した切替口と無関係(pop43 §19-6 と同じ) |
| `lint-imports`(作業木の src) | 5 契約とも KEPT・0 broken |
| カード `python tools/repo_guide/build.py` → `--check` | 作り直した(121 本)→ `--check` は「最新」。data の一覧 `cards/data.md` は本体の data の大きさの変化(`realworld_live` ほか)でも動いた(本段と無関係) |
| 秘密の走査(変えた・足したファイル 58 本) | CLEAN |
| `tests/c7` | 回していない(発注どおり) |

〔検収の直しの後〕

| 試験 | 結果 |
|---|---|
| 範囲を広げた全体 `tests --ignore=tests/c7`(`-m "not gpu and not slow" -n 4 --dist loadfile`=前の範囲に tests/bridging・c6・c8・build_*・world・agents・bench・fig・w17 と根の試験を足した) | **6,581 passed・4 failed・0 errors・2 skipped**(収集の errors 0) |
| 落ちた 4 本のうち本段が起こした 1 本 | `tests/bridging/test_decision_rows_1101.py::test_base_rows_are_byte_identical`=台帳の DEC の外の行の指紋の定数。5 行を removed にし見出しの行の項を直したので指紋が動いた(行数 682 のまま)=定数を張り替えて注を書いた(前例の形) → 再実行で通った |
| 落ちた 4 本のうち前からの 3 本 | `tests/world/processes/test_declarations_1101.py::test_routing_absent_rows_all_have_a_declaration`(routing の「無い」の行が 102 を欠く)・`tests/bridging/test_decision_rows_1101.py::test_tool_is_idempotent_on_the_current_ledger`(道具が routing の行の文を引けず KeyError)=どちらも基準 `6753891` の木の写し(`git archive`)で回しても同じく落ちる(11-09 の文書の直しの後から。本段と無関係)。`tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`=作業木の data がつなぎ(前と同じ) |
| 張り替えの後の再実行 `tests/bridging tests/world` | 163 passed・2 failed(上の前からの 2 本)・0 errors |
| 変えた試験のファイルの slow(`test_rules42_runs`・`test_rules42b_ledger`・`proximity/test_runs`・`test_state_checks_10f`) | 6 passed(6 分 2 秒) |
| 検収の直しの試験(`test_removed_switches_346.py` ほか関わる試験) | 455 passed(`tests/engine/systems` ほか)・新しい試験 19 passed |
| `lint-imports` | 5 契約とも KEPT |
| カード `build.py` → `--check` | 作り直した(121 本)→「最新」 |

## 9. 検収の直し(別の検収役の判定=条件つき受入)

| 指摘 | 直し方 |
|---|---|
| H1 消した環境変数がふつうのランの入口で止まらない(`SHIBUYA_SEAT_RELEASE` は保存も再開も無いランで黙って既定・`SHIBUYA_DEFECT_FIXES_1103` は最後の report で落ちる・`SHIBUYA_RULES_42`/`42B` は段階 2 の台帳の無いランで無視) | 一覧と止める文を `src/shibuya/engine/removed_switches.py` の 1 か所に置いた(`REMOVED_ENV`・`REMOVED_CLI_FLAGS`・`stop_if_set`・`check_environment`)。組み立て `systems/build.py` の `build()` の最初で `check_environment()` を呼ぶ(既定の結果は変えない=§5 の byte-check)。各モジュールの読み込みの止めも同じ文(`stop_if_set`)。試験 `tests/engine/test_removed_switches_346.py`: 5 本 × 値 2 つ × 入口 2 つ(`run_day`・`cli.main`)を子のプロセスで回し、非ゼロで終わる・文に名とタグ・traceback の系の置き場が進行役と組み立てだけ(刻みの系と report に入っていない) |
| L1 `--proximity` が argparse の略記で `--proximity-d` と読まれる | 消した 3 本の旗(`--seat-release`・`--proximity`・`--defect-fixes-1103`)を表に出さない旗(`help=SUPPRESS`)として受け、渡されたら「消した切替口・タグ」の文で引数の誤り(`SystemExit` 2)。`allow_abbrev=False` は入れていない。今の旗と、これまでに消した旗(`--wage`・`--meal-default`・`--leave-effect`・`--poi-target`・`--near-tiebreak`・`--near-order`・`--rel-tenure-hash`・`--response-delay`・`--attendance-rate`)の略記の重なりを調べた=今の旗の頭に重なるのは `--proximity`(`--proximity-d`)だけ(止めた 5 の `--economy-stage2` も `--economy-stage2-parts` に重なるが旗はまだある)。試験は略記(`--seat-rel`・`--defect`)と `--proximity 1.0` を含む |
| M2 percept_bytes の (B) を消した | 戻した(案 (a)): 試験の中だけ `proximity.rule_from` を None にする。build.py の `_px_rule is None` の枝は試験の口として残し、注を付けた |
| M3 再開を止める試験が名前どおりに見ていない | 保存の間だけ `<mod>.header_fields` を None(規則の表は `economy_stage2.header_fields` から鍵を外す)にし、戻してから `run_day(resume_from=…)` が ValueError(文にタグ)になることを見る形に: `test_seat_release_2_4.py::test_resume_without_the_seat_header_is_refused`・`test_defect_fixes_1103.py::test_resume_without_the_header_is_refused`・`proximity/test_runs.py::test_resume_without_the_proximity_header_is_refused`・`test_rules42_runs.py::test_resume_from_a_state_without_the_rules_key_is_refused`(`rules_42`・`rules_42b`)。正の対照(見出しのある保存は通る)も付けた |
| L2 古い文 | `proximity.py` の冒頭の docstring・状態台帳の行 PX・PX0 の `alloc` と注・系の表 `apply_responses` と `conversation` の `resolve_ops` から `revert_conversation` を外した(ランでは呼ばない・書く列の閉包は同じ=`writes.soa` は不変を確かめた)・本書 §3-2 の「(§6)」→「(§7)」 |
| L3 死んだ枝 | `test_defect_fixes_1103.py` の `parametrize("mode", ["on"])` と legacy の else を消した。build.py の `_px_rule is None` の枝は M2 で使う=注を付けて残した |
| M1 「1 バイトも」 | §0・§5-1・§6 に親の 37 欄の道具の結果を書き足した |
| L4 | md23 の近接の既定の変化を §7 に書いた。試験の範囲を広げた(§8 の続き) |
| 止めた 3 本 | §3-2 に `test_rate_rules_1101`・`test_absent_processes_1102` を書き足した |

byte-check(作業木の 25 欄の道具・基準 `6753891`・all19): 直しの後も 19/19 同じ([bytecheck/review_fixes_compare.json](bytecheck/review_fixes_compare.json))。
