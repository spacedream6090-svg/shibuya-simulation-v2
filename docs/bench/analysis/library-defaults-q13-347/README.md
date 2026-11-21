# Q13(第347)ライブラリの既定を CLI にそろえる(library-defaults-q13-347)

> 版上げ。発注: [返事その 8](../../../design/prompt-2026-11-16-reply8.md) §1-2 の Q13(決定の正は原文)、親の裁定(計画 `plan_bumps`
> §2-3 の Q13-1〜Q13-8・段 0 の後の裁定=語彙は (s1)・呼数の倍率は (a′))。作業の枝 `work/q13-defaults-347`。実装役 Opus 5.5。
> byte-check・範囲の全体の試験・commit・タグ・版上げの履歴への写しは親。commit ① は §0〜§3、commit ②(版上げ本体)は §4。

## 0. 要点(commit ①)

- commit ① は**試験の書き直しだけ**(src は変えない)。前のライブラリの既定(語彙 v1・空腹 v1・呼数 L4 の按分)に頼って
  **旧の性質**を確かめていた試験に、その引数を明示した。前の既定を明示するだけなので、今の src(前の既定)では 1 バイトも
  変わらない。版上げ(commit ②)で既定が変わっても、同じものを確かめ続ける(Q13-4 (a)・Q13-6・Q13-7)。
- 既定そのものを確かめる試験(8 本)・golden の張り替え・凍結の表に当たる試験(5 本)・試験の上限の直し(1 本)は commit ① に
  入れない(commit ② と親の判断)。区分の表は §2。
- 確かめ: 直した試験を、今の src(前の既定)と、版上げの src(既定を替えた形=腕 A と (a′))の両方で回した(§3)。

## 1. commit ① で直した試験(前に確かめていたこと → 後に確かめること)

どれも「前に確かめていたこと」と「後に確かめること」は**同じ**(前は既定で渡していた値を、明示で渡すようにした)。

| ファイル | 試験 | 足した引数 | 前 → 後 |
|---|---|---|---|
| `tests/engine/test_state_ledger_10b.py` | `test_t1_deleting_the_dead_columns_changes_nothing[v1/v3/v2_edge_attention]` | 語彙(v1 の行だけ)・空腹 v1 | 前の既定で録った final の行 `CUR_SYN` と同じ → 同じ(表は変えない) |
| `tests/engine/test_conversation.py` | `test_run_day_opens_conversation_sessions_when_resolve_creates_them` | 語彙 v1 | 語彙 v1 の台本で会話が開く → 同じ |
| `tests/engine/test_presence_executor.py` | `test_null_arm_reproduces_the_recorded_checkpoint`・`test_l4_scale_1_reproduces_the_stage_2c_checkpoints`・`test_hunger_model_v1_reproduces_the_stage_3_checkpoints` | 帰無腕の `cli.run` に語彙 v1(5 か所) | 帰無腕の golden(語彙 v1 で録った)と同じ → 同じ(v3 の行は前から語彙 v3 を渡している) |
| `tests/engine/test_two_layer_activity.py` | `test_v1_ignores_the_activity_switch` | 語彙 v1 | 語彙 v1 では活動の切替が効かない → 同じ |
| `tests/engine/test_fleet_wiring.py` | 助け `run_mock`・`run_fleet`(渡さなければ語彙 v1)と、夜の会話の試験の台本のラン | 語彙 v1 | 偽 vLLM・台本の語彙 v1 の 2 行形で艦隊の配管を見る → 同じ |
| `tests/engine/test_classical_policy.py` | `test_run_day_classical_arm_and_layers` の「語彙 v1 では止める」 | 語彙 v1 | 語彙 v1 × 古典の方策は止まる → 同じ |
| `tests/engine/test_intent_mode_open.py` | ファイルの全部(`SMALL`) | 語彙 v1 | open/hint の腕は語彙 v1(Q13-7) → 同じ |
| `tests/engine/test_vocab_v2_eat.py` | `test_v2_is_a_different_run_but_still_conserves`・`test_stage0_dictionary_v3_grounds_eating_into_the_new_word` | v1 のランに語彙 v1 | v1 と v2 の違い・「食べる」が v1 で購入 → 同じ |
| `tests/test_cli_intent_mode.py` | `test_cli_run_passes_intent_mode_through_kwargs[open/hint]` | 語彙 v1 | open/hint が manifest まで届く(Q13-7) → 同じ |
| `tests/engine/test_l4_budget.py` | `test_synthetic_run_stays_within_the_l4_cap`・`test_real_world_run_stays_within_the_l4_cap`(slow) | 倍率 1.0 | L4 の按分の上限が効く → 同じ |
| `tests/c6/test_l4_l6_budget.py` | `test_l4_cap_holds_for_a_5000_agent_day_on_the_synthetic_world` | 倍率 1.0 | 同上 → 同じ |
| `tests/c6/test_t9_diagnostics.py` | `test_t9_the_four_columns_actually_carry_numbers` | 倍率 1.0 | 需要 > 予算で繰り延べ・縮退が立つ → 同じ |
| `tests/perception/facts/test_percept_is_scratch.py` | `FLEET_KW`(このファイルのテープの試験) | 空腹 v1 | 古い src と今の src で同じテープの再生が同じ → 同じ(比べる 2 つの src の既定の違いを入れない) |
| `tests/engine/duties/_du.py` | `KW`(店の仕事のランの試験) | 空腹 v1 | 担当が開店の時刻に店に居る場面(空腹 v1 の 1 日で組んだ) → 同じ(energy の場面に組み直すかは親の判断待ち) |

- import の文は変えていない(割る段 5a の G1 が import の文を書き換えるので、ぶつからないように要る行だけを直した)。
- 版上げ(commit ②)で空腹 v1 を「試験の中だけの口」にする(Q13-3 (hs1))と、空腹 v1 を明示した試験(`test_state_ledger_10b`・
  `test_percept_is_scratch` の子のプロセス・店の仕事)には試験の印が要る。

## 2. commit ① に入れなかったもの

| 試験 | 本数 | わけ | どこで |
|---|---|---|---|
| 既定を確かめる試験(`test_energy_balance`・`test_vocab_v2_eat` の 2 本・`test_cli_vocab_version` の 3 本・`test_manifest_rules_bridges`・`test_cli_l4_scale` の後半) | 8 | 新しい既定へ書き換える | commit ② |
| `tests/c8/test_ablations_ab7.py` の 2 本・`test_ablations_ab6b.py` の 1 本 | 3 | 腕定義の表(`tools/c8/ablations_v1.json`)の AB7・AB7b のランに語彙が無い。足すと凍結の SHA が動く | 親が決める |
| `tests/engine/state/test_names_frozen.py` の 2 構成(`syn_default`・`syn_all_arms_classical`) | 2 | ランの出力の名が増えた(凍結の表) | 親が決める |
| `tests/engine/test_mock_day_w2.py::test_agents_end_in_valid_states` | 1 | 結果コードの上限が古い(語彙 v3 の正しい結果 19 で落ちる) | commit ② |

## 3. 確かめ

直したファイル(店の仕事は `tests/engine/duties/` の 3 本ごと)を 1 本の束で回した(`-n 4`・実装役の機械・data あり)。
src の当て外しは作業木の差分の patch の `git apply` / `git apply -R` だけ(stash・checkout・reset はしていない)。

| src | 結果 | 落ちたもの |
|---|---|---|
| 今の src(前の既定=本体と同じ・src の差 0 行) | 321 passed・1 skipped | なし(skip は艦隊の診断行の環境変数が無い 1 本=前から) |
| 版上げの src(既定を替えた形=腕 A と (a′)) | 319 passed・1 skipped・2 failed | 既定を確かめる 2 本(`test_vocab_v2_eat` の `test_the_default_run_is_byte_identical`・`test_action_usage_of_the_default_run_carries_the_v1_version`)=commit ② で書き換える |

- 版上げの src で、commit ① の対象の 38 本はどれも通った(既定を明示した値が、既定を替えた後も同じものを確かめる)。
- byte-check と範囲の全体の試験は親が回す(commit ① の時点は src の差 0=astsame で確かめる)。

### 3-1 親の確かめ(commit ①)

- src の差: `tools/bytecheck/astsame.py --base HEAD`=変わったファイル 0 本([astsame_c1.json](astsame_c1.json)・土台 `3befc11`)。byte-check は
  回していない(src を変えていない段)。
- 範囲の全体の試験(`tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`・linked の作業木・前の既定の src): 6,918 passed・
  1 failed・21 skipped・1 xfailed(36 分 49 秒)。落ちた 1 本は前からの
  `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(linked の作業木でだけ落ちる)。
- 既定だけを替えた src(版上げの前の数え)での範囲の全体の試験は 54 failed・6,831 passed だった(うち 1 本は上の前からの失敗=既定の変更で
  落ちるのは 53 本・24 ファイル)。53 本の区分: 既定を確かめる 8・旧の性質を確かめる 30・店の仕事の場面 8・腕定義の表 3・名の凍結 2・
  試験の上限 1・版上げの src の直しで消えた 1。本当の退化は 0。commit ① は、このうち旧の性質を確かめる 30 本と店の仕事の 8 本を、
  引数の明示で通す。残りは commit ② で扱う。
- 既定だけを替えた src の byte-check(版上げの前の数え・基準 `8c58d9f`): 19 構成のうち 18 は 37 欄すべて同じ・`w6_golden_null_arm` だけが
  動いた(17 欄・呼数 95,645 → 98,083)。commit ② のときに回し直して記録を置く。

## 4. commit ②(版上げ本体)

### 4-1 変えた既定(ランの入口=`run_day`・`cli.run`・`RunResult`)

| 既定 | 前 | 後 | 1 つの値の置き場 |
|---|---|---|---|
| 語彙 | v1 | **v3** | `engine.run.RUN_DEFAULT_VOCAB_VERSION`(`cli.CLI_DEFAULT_VOCAB_VERSION` がここから引く) |
| 空腹のモデル | v1 | **energy** | `world.body.energy.DEFAULT_HUNGER_MODEL`(`cli.CLI_DEFAULT_HUNGER_MODEL` は前からここを引く) |
| 呼数の倍率 | 1.0(L4 の按分・manifest に載せるだけ) | **渡さなければ 0=無制限・予算を渡したら 1.0**((a′)) | `engine.run.RUN_DEFAULT_L4_SCALE` と `resolve_l4_scale`(`cli.run` も同じ決め方) |
| 予算の式 | `cli.run` の中 | **`engine.run.l4_budget` の 1 か所**(0 → 体数・正 → `call_budget_per_tick × 倍率`)。予算を渡さない `run_day` は組み立てで同じ式 | — |

- 低い層の既定(`text.templates`・`vocab.actions` の `DEFAULT_VOCAB_VERSION`)は v1 のまま(Q13-1 (s1))。
- `arm_baseline` は語彙と空腹を重ねなくなった(`run_day` の既定と同じ値)。倍率は署名の既定が `None` なので、決めた値 0.0 を重ねる。
- `run_day` の頭の写し `_call_args = dict(locals())` はそのまま。写しの後で倍率を決めた値に置き直す=設定の指紋の鍵の集合は前と同じ・
  予算を渡したランの指紋の倍率は前と同じ 1.0・`cli.run` が渡す引数は前と同じ(倍率 1.0 は予算 None のまま渡す)。

### 4-2 空腹の旧規則 v1 は試験の中だけの口(Q13-3 (hs1))

- `run_day`・`cli.run` の引数 `hunger_model` は残る。`"v1"` は組み立ての入口(`world.body.energy.check_hunger_model`)で止める(文に
  消した口・安定版のタグ `stable-v2-before-library-defaults-q13`・試験の中だけの口の名)。
- 試験の中だけの口: `world.body.energy._HUNGER_V1_FOR_TESTS`(既定 False・`__all__` に入れない)と読み口 `hunger_v1_for_tests()`。
  立てるのは試験の助け `tests/engine/body/_hunger_v1.py`(`monkeypatch`・子のプロセスにはコードの頭に足す `CHILD_PRELUDE`)=切替口 ③a の
  `nav1._LEGACY_FOR_TESTS` と `tests/engine/space/_legacy.py` と同じ形。src に新しいファイルは足していない。
- 印を立てたランは `cli.run` のランの種類で腕に数える: `hunger_model="v1"` は CLI の既定(energy)と違う引数なので `run_arms` が腕に
  数える(試験 `test_cli_default_hunger_model_is_energy` で確かめた)。印だけでは挙動は変わらない(v1 を明示したランだけが通る)。
- `foundation/arms/removed.py` の `--hunger-model` の止める文の注を事実に直した(「Q13 まで残る」→「引数は残る・v1 は Q13 で止めた=
  試験の中だけの口」)。

### 4-3 書き換えた試験と張り替えた値(試験ごとに理由 1 行)

| 試験 | 書き換え | 理由 |
|---|---|---|
| `tests/engine/test_energy_balance.py::test_run_day_default_is_energy_and_v1_is_only_for_tests`(前 `…_default_is_v1_and_energy_is_an_arm`) | 既定 energy=明示の energy と同じ・v1 は印なしで止まり印で通る | 既定を確かめる試験(新しい既定へ) |
| `tests/engine/test_energy_balance.py::test_cli_default_hunger_model_is_energy` | v1 のランの前に印・v1 のランが腕に数えられること | 空腹 v1 は試験の中だけの口 |
| `tests/engine/test_vocab_v2_eat.py::test_the_default_run_is_byte_identical` | 既定=v3 の明示と同じ・v1 の明示では食事 0 | 既定を確かめる試験 |
| `tests/engine/test_vocab_v2_eat.py::test_action_usage_of_the_default_run_carries_the_v3_version`(前 `…_v1_version`) | 既定のランは v3・辞書 v5・v3 の 23 語の鍵。v1 の明示のランは前の値(辞書 v2・12 語) | 既定を確かめる試験 |
| `tests/test_cli_vocab_version.py::test_cli_run_defaults_to_v3`(前 `…_to_v1`) | `cli.run()` は v3・辞書 v5 | 既定を確かめる試験 |
| `tests/test_cli_vocab_version.py::test_the_default_run_is_byte_identical_with_the_explicit_v3`(前 `…_v1`) | 既定=v3 の明示 | 既定を確かめる試験 |
| `tests/test_cli_vocab_version.py::test_cli_and_run_default_vocab_are_one_value`(前 `test_cli_default_is_v3_but_the_library_default_stays_v1`) | CLI・`run_day`・`RunResult` の既定が同じ 1 つの値 v3・低い層の既定は v1 のまま | 既定を確かめる試験((s1)) |
| `tests/engine/bridging/test_manifest_rules_bridges.py::test_tool_configs_that_call_cli_run_are_arms` | 語彙を渡さない `cli.run` は腕でない(`()`) | 既定を確かめる試験 |
| `tests/test_cli_l4_scale.py::test_the_explicit_1_0_is_the_old_l4_share` | 按分は `run_day(l4_scale=1.0)`・既定は体数と 0.0・予算を渡すと 1.0 | 既定を確かめる試験((a′)) |
| `tests/engine/test_mock_day_w2.py::test_agents_end_in_valid_states` | 結果コードの上限を `max(ResultCode)` に | 上限が古い(語彙 v3 の正しい結果 `NOT_IN_EATERY`=19) |
| `tests/engine/test_mock_day_w2.py::test_w2_five_thousand_agents_one_sim_day_under_ten_minutes`(slow) | 倍率 1.0 を明示 | L4 の制御目標 10 呼/体/日を見る旧の性質(既定の無制限で 13.0 呼/体/日) |
| `tests/engine/test_processes_run.py::test_c4_second_half_on_the_real_world`(slow) | 倍率 1.0 を明示 | L4 の硬い上限を見る旧の性質 |
| `tests/engine/test_removed_switches_346.py`(止める文) | `--hunger-model` の注の文 | removed.py の注を事実に直した |
| 空腹 v1 を明示する試験(`test_state_ledger_10b` の t1 の 3 行・`test_presence_executor` の 2 本・`test_meal_bundle_2b` の 1 本・店の仕事の `_du.fresh`・`test_percept_is_scratch` の全部と子のプロセス) | 試験の助けで印を立てる | 空腹 v1 は試験の中だけの口(値は変えない) |

- golden の値(`tests/golden_env.py` の行・`CUR_SYN` ほか)は**張り替えていない**: 前の既定に頼っていた行は commit ① で引数を明示したので、
  値は前のまま通る。既定で回すランの golden の行が他に残っていれば、範囲の全体の試験(golden の行のある機械)で出る(親)。

### 4-4 名の凍結(`tests/engine/state/names_frozen.json`)で足した名(足すだけ・減った名は無い)

| 構成 | 源 | 足した名 | わけ |
|---|---|---|---|
| `syn_default` | manifest | `agents.weekly.WEEKLY_FILE` | 既定の空腹が energy になり、食事の既定(W17)の名が manifest に載る |
| `syn_all_arms_classical` | hash | `shibuya.engine.activity.ActivityPayload`・`shibuya.llm.contract.Target`・`shibuya.llm.contract.TargetKind` | 既定の呼数が無制限になり呼が増え、活動の層と対象の型が状態に入る |

- 確かめ: 台本(scratchpad の `probe_names_frozen.py`)で、旧の既定を明示すると差 0・版上げの既定では上の名だけが増える(ほかの源の差 0)。
  理由は試験 `test_run_outputs_contain_exactly_the_frozen_path_shaped_names` の注にも書いた。

### 4-5 腕定義の表(`tools/c8/ablations_v1.json`)

- 語彙を持たない 10 腕(AB1・AB2・AB3・AB6・AB7・AB7b・AB6b・AB8・AB6c・AB1b)の全ランに `vocab_version: "v1"` を明示し、表のトップに
  `vocab_version_pin`(版・腕・理由)を足した(第290 の `l4_scale_pin` と同じ形)。AB4・AB5(ランなし)・AB7c・AB7d(語彙を渡している)は
  不変。感度の表 `docs/bench/c8/sensitivity_v1.json` は変えていない。
- 前後で同じランになることの確かめ(道具を回さず表を比べた): 34 ランすべてで、`cli.run` に渡って効く引数(語彙・空腹・倍率と腕の
  kwargs)が前後で同じ(前=語彙は `run_day` の既定 v1・空腹は `cli.run` の既定 energy・倍率は全ランが明示/後=語彙は明示の v1)。
- 凍結の SHA を注つきで張り替えた: `tests/c8/test_ablations_ab7.py` の `FROZEN_ARM_SHA256`(AB1・AB2・AB3・AB6・AB7・AB7b の 6 本)と
  `tests/c8/test_ablations_ab8.py` の `FROZEN_AB6B_SHA256`。kwargs の並びを確かめる試験(ab7・ab6b・ab8)に `vocab_version` を足した。
  新しい試験 `tests/c8/test_ablations_vocab_pin.py`(全ランが語彙を明示・`vocab_version_pin` の腕・open の腕が v1 で回る)。
- 表のトップの `shared_baseline`(kwargs 空)は実行器が回さない(合計の数にだけ使う)ので変えていない。

### 4-6 道具

- `tools/c6/run_hash.py`: 台帳つきの道(`cli.run`)に語彙 v1(空腹と倍率は前から energy・0 で同じ)。直呼びの道(`--no-ledger`)に語彙 v1・
  倍率 1.0。**直呼びの道の空腹は energy になった**(空腹の旧規則 v1 は試験の中だけの口=道具からは選べない。T3 は同じ引数の 2 プロセスを
  突き合わせる道具なので、値の前後は比べない)。出力の `config` に `hunger_model`・`vocab_version` の欄を足した(ランの値は変えない)。
- `tools/c7/occupancy_series.py`: 語彙 v1・倍率 1.0 を明示。**空腹は energy になった**(同じ理由)=前のラン(空腹 v1)と違うランになる。
  前の値の再現は安定版のタグ `stable-v2-before-library-defaults-q13`。どの空腹のモデルで回したかが出力から分かるよう、`--record` の
  出力の meta(`c7_occupancy.json` と `c7_occupancy.npz`)に `hunger_model` の欄を足した(ランの値は変えない。`c7_checkpoints.json` は前から
  `run_manifest_fields` に持つ)。
- 〔検収 M1〕語彙を渡さずに `cli.run` を呼んでいた道具 7 本に語彙 v1 を明示した(前と同じラン・渡された値が勝つ)。出力に語彙の版の欄を
  足した(ランの値は変えない):
  - `tools/c6` の `run_smoke` を通る 5 本: `ablation1_fixed_vs_ranking.py`(腕の `extra` に足した・出力の腕の行に `vocab_version`)・
    `format_role_rates.py`(出力に `vocab_version`=テープ・応答を読むときは null)・`metric_b_rerun.py`(meta に `vocab_version`)・
    `t6_bit_reproduce.py`・`t7_distribution.py`(ランの行に `vocab_version`)。
  - `tools/c7/salt_runs.py`: 腕の引数に語彙が無ければ v1(`setdefault`=腕に書いた値が勝つ)・1 本の結果の行に `vocab_version`。
  - `tools/instruments/batch_width_gauge.py`: `--kw` に語彙が無ければ v1(`setdefault`=`--kw` が勝つ)・子の結果の行に `vocab_version`。
- 〔検収 M1〕数え直し(台本 scratchpad の `scan_tools_helpers.py`・AST): `tools/` と tests の助け(`test_*.py` でないファイル・c7 を除く)の
  `run_day`(語彙・空腹・倍率/予算)・`cli.run`/`run_smoke`(語彙)の呼び出しで、既定に頼るものは 11 か所・8 ファイル(うち `**kw` 8)。
  どれも前と同じランか、理由のあるもの:
  - `tools/bytecheck/check.py`(構成の表から渡す=全構成が語彙を明示)・`tools/c6/c6lib.py` の `run_smoke` の中の 3 か所(呼び手が全部
    語彙を渡す: 上の 5 本・`run_hash`・腕の実行器)・`tools/c8/ablation_runner.py`(腕の表の全ランが語彙を明示)・
    `tools/instruments/anchor_gauge.py`(腕の表が語彙 v3 を明示)。
  - `tools/c6/run_hash.py`・`tools/c7/occupancy_series.py`: 空腹だけ(上のとおり energy=決定の帰結)。
  - `tests/engine/state/shaped_names.py`: `syn_default` は既定のランそのものを見る構成(名の凍結を新しい既定で張り替えた)。
  - `tests/engine/speech/_s8b.py`(発話の口の試験の助け): 語彙 v3・予算を渡し、空腹だけ既定=前は空腹 v1・今は energy。試験は新しい
    既定で通る(範囲の全体の試験)。**親の裁定=空腹 energy のまま**(発話の口の試験は値の前後を比べる試験でなく、語彙 v3 の道の性質を見る
    試験。CLI の既定と同じ空腹で確かめるほうが、ランの入口の既定の道に近い。空腹 v1 は試験の中だけの口なので、ここへ広げない)。
- `docs/bench` の記録の道具は直さない。ランの既定に頼る呼び出し: 151 か所・93 ファイル(うち `**kw` で渡す 142 か所=中身は読まないと
  分からない)。`run_day` を直に呼ぶものは語彙・空腹・倍率の 3 つ、`cli.run` を呼ぶものは語彙だけが前と違う。一覧は scratchpad の
  `scan_bench_tools.json`(多い置き場: wallbounce-1012 78・wallbounce-1003 10・store-memory-2026-09-28 7・switch-removal-347 6)。

### 4-7 店の仕事の試験について分かったこと(事実・直していない)

- 店の仕事の試験 8 本(`tests/engine/duties/`)の場面(担当が開店の時刻に店に居る)は空腹 v1 の 1 日で組んだ。空腹のモデル energy では、
  担当が店に着くのが開店の後になり、開けるのはつなぎになる(段 B の場面で、開ける回数は v1 で本人 1・つなぎ 1、energy で本人 0・つなぎ 2。
  閉める・補充は energy でも本人。監査の違反は 0)。
- CLI の既定(energy)で店の仕事の腕を確かめる試験は、今は無い。試験は空腹 v1(試験の中だけの口)のまま残した(親の裁定)。

### 4-8 見つけた欠陥(直していない=ユーザーの判断待ち)〔第 348 で直した=§5〕

- `llm.fleet._format_ok` は語彙を渡さずに読む=艦隊の v3 のラン(CLI の既定)で「なし」「食事」の応答が書式の誤りになり、温度 0 の
  再生成が 1 呼増える。mock と byte-check には効かない。
- 低い層の既定 v1 に頼って読む所が 8 か所(パーサの `_parse` の 4・`_fill_positional` の 2・`commit.parse_action`・`fleet._format_ok`)。
  直し方の案=その 8 か所にランの語彙を渡し、低い層の既定を無くす(実 LLM のランの挙動が変わるので先に聞く)。

### 4-9 範囲の全体の試験に入らない slow の試験

範囲の全体の試験(`-m "not gpu and not slow"`)に入らない slow の試験のうち、ランの既定に頼る呼び出しを持つものが約 30 本ある(台本
`scan_slow_tests.py` の出力 49 行)。L4 の上限を確かめる 2 本(上の表)は直した。そのうえで、その試験を持つ 22 ファイルの slow の試験を
1 本の束で回した(`-m slow -n 4`・実装役の機械・data あり・版上げの src): **75 passed・1 skipped・失敗 0**(23 分 9 秒)。ほかは値の前後を
比べる試験(再開=通し・決定論・記録 on/off)と 5,000 体の時間・量の試験で、既定が変わっても同じ引数どうしを比べる形だった。

### 4-10 byte-check(親が埋める)

- 〔親の裁定の変更・Q13-5 (b)〕byte-check の構成 `w6_golden_null_arm` にも語彙 v1 を明示した(`tools/bytecheck/configs.py`・試験
  `tests/tools/test_bytecheck.py` は元の表との違いをこの 1 つに限って確かめる)。byte-check が見る範囲(語彙 v1 の帰無腕)を減らさないため。
  golden の試験 `test_null_arm_reproduces_the_recorded_checkpoint` も語彙 v1 を明示している(名と中身がそろう=検収 L-5)。
- **結果(親・作者の機械・この作業木の道具で)**: `python tools/bytecheck/cli.py run --base 25ca546 --src <作業木>/src --set all19 --jobs 6`
  = **19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・final が同じ 19**(終了コード 0・全体の壁時計 426 秒)。既定 `w6_v3_default` の
  final `c8d68704b7b0760d`・呼数 60,939(前と同じ)。帰無腕 `w6_golden_null_arm` は final `2875768fc19e02e8`・呼数 95,645(前と同じ)。
  基準 25ca546 は、割る段 5a の群 1 が入った本体の頭(src は bf0ccbb と同じ)。記録は [bytecheck/](bytecheck/)。
  全構成が語彙を明示し、空腹と倍率と予算は `cli.run` が前と同じ値で渡すので、ランの入口の既定を替えても 19 構成は動かない。
- 語彙を明示しない場合の動き方(既定の変更そのものの効き目)は別に測った(親・検収の直しの前の作業木・基準 9495521・元の構成の表の
  まま): 18 構成は 37 欄すべて同じ・`w6_golden_null_arm`(語彙を渡さない 1 構成)だけ 17 欄が動く(final `2875768fc19e02e8` →
  `d24a12d86ff16a6b`・呼数 95,645 → 98,083)。記録は [bytecheck_unpinned_base_9495521/](bytecheck_unpinned_base_9495521/)。
- byte-check が確かめていないこと: 語彙を渡さない `run_day` の直呼び(語彙・空腹・倍率の 3 つが変わる=§4-15)。その前後は §4-11 の
  性能の表の「既定で回す `run_day`」の行に final と呼数を書いた。

### 4-11 性能(親が埋める)

測り方は記録 `docs/bench/analysis/weather-a48-347/README.md` の性能の節と同じ(壁時計=ランの前後・刻みあたり=壁時計 ÷ 実行器の刻みの数
1,440・最大メモリ=Windows の最大の作業集合・10^6 B を MB・判断モデルの呼数は 0=mock)。5,000 体・1 日・seed 1・作者の機械。1 本ずつ
単独のプロセスで、土台(本体の頭 25ca546)→ 後(この作業木)の順に 2 巡。

| ラン | 土台(1 巡目/2 巡目) | 後(1 巡目/2 巡目) |
|---|---|---|
| CLI の既定のラン(`cli.main(["--llm", "mock"])`・世界過程あり) | 52.2/50.3 秒・36.3/34.9 ms/刻み・最大 523.5/539.9 MB・呼数 60,939・final `c8d68704b7b0760d` | 47.9/50.2 秒・33.3/34.8 ms/刻み・最大 529.6/530.3 MB・呼数 60,939・final 同じ |
| 既定で回す `run_day`(`n_agents=5000, seed=1, world_dir="data/world/v2", processes=False`=語彙・空腹・倍率を渡さない・世界過程なし) | 17.0/17.8 秒・11.8/12.4 ms/刻み・最大 518.2/492.3 MB・呼数 23,501・final `29e4139c65fa9610` | 44.5/45.2 秒・30.9/31.4 ms/刻み・最大 512.5/500.3 MB・呼数 62,251・final `70c25ac3e26e4e7d` |

- CLI の既定のランは、結果も性能も変わっていない(揺れの中)。
- 既定で回す `run_day` は**別のランになった**(語彙 v1 → v3・空腹 v1 → energy・呼数の上限 L4 の按分 → 無制限)。呼数が 2.6 倍(23,501 →
  62,251)になり、壁時計も 2.6 倍(約 17 秒 → 約 45 秒)になった。同じランの退化ではなく、既定の変更の帰結。最大メモリは揺れの中。
  引数を渡さずに `run_day` を呼ぶ試験と道具は、そのぶん遅くなる(範囲の全体の試験の所要は §4-17)。
- byte-check の帰無腕 `w6_golden_null_arm`(語彙 v1 を明示・6 本並列の中の壁時計=比べない参考値): 基準 59.6 秒・後 59.7 秒・呼数 95,645 で同じ。

### 4-12 版上げの履歴に書く 1 行

- 区分は「小」にした(親の決め)。回数を数える行(1〜4 回目)は、CLI の既定の結果が変わる大きな切り替えに使ってきた。この版上げは
  CLI の既定の結果を変えない(byte-check 19 構成すべて同じ)。
- 行の中身(`docs/ops/version-history.md`): ランの入口の既定を CLI にそろえた=語彙 v3・空腹 energy・呼数 無制限(予算を渡したら倍率
  1.0)・低い層の既定は v1 のまま・空腹 v1 は試験の中だけの口・前と同じランに保った所(byte-check の帰無腕・腕定義の表の 10 腕・
  道具 9 本)・byte-check の結果・性能(§4-11)・安定版のタグ `stable-v2-before-library-defaults-q13`(直前の commit)・戻し方
  `git checkout stable-v2-before-library-defaults-q13`(旧の既定=語彙 v1・空腹 v1・L4 の按分の値の再現)。

### 4-13 検収の低の指摘(記録だけのもの)

- L-1: `python -m shibuya.engine.run`(engine の入口の main)は語彙・空腹・倍率を渡さない=ランは 3 つとも変わる(語彙 v3・空腹 energy・
  予算 無制限)。tests と tools からこの入口を呼ぶ所は無い。
- L-2(直した): 予算を渡さないランの倍率が負・NaN・無限大なら `engine.run.l4_budget` が止める(文に値を書く・試験
  `tests/test_cli_l4_scale.py::test_a_non_finite_or_negative_factor_stops`)。
- L-4(直した): `hunger_v1_for_tests` の docstring(読むのは `check_hunger_model` だけ)・読み口は `__all__` から外した(星の import で
  読む所は無い)。
- L-5: byte-check の構成 `w6_golden_null_arm` は語彙 v1 を明示して前と同じランに保った(§4-10)。
- L-7: `cli.run_arms` を直に呼ぶと、空腹を渡さないときの答えが変わる(前は腕・今は腕でない)。`cli.run` の経路では起きない(空腹を
  `setdefault` する)=試験だけの話。

### 4-14 残した所

- L-3: 予算を直に渡したランの倍率は検査しない(`run_day(budget=3, l4_scale=0)` は manifest に 0 と書く・負も止まらない)。前からの形で、
  `cli.run` も同じ。
- L-6: `test_mock_day_w2::test_agents_end_in_valid_states` の上限 `max(ResultCode)` は「範囲の外の値が無い」を見るだけ(どのコードが出て
  よいか・負の値は見ていない)。前も見ていなかった。

### 4-15 前と答えが変わる頼み方(検収役の一覧を直した後の形に合わせた)

| 頼み方 | 前 | 今 |
|---|---|---|
| `run_day(...)` で語彙を渡さない | 語彙 v1 | 語彙 v3 |
| `run_day(...)` で空腹を渡さない | 空腹 v1 | 空腹 energy |
| `run_day(...)` で予算も倍率も渡さない | 予算=L4 の按分(5,000 体で 34.72/刻み)・manifest の倍率 1.0 | 予算=体数(無制限)・倍率 0.0 |
| `run_day(l4_scale=s)`(s≠1・予算なし) | 倍率は manifest の印だけ(予算は按分のまま) | 予算=按分×s(0 なら体数) |
| `run_day(l4_scale=負・NaN・無限大)`(予算なし) | 回った(印だけ・予算は按分) | ValueError(値を文に書く) |
| `run_day(hunger_model="v1")`・`cli.run(hunger_model="v1")` | 旧規則で回る | 止まる(試験の中だけの口) |
| `run_day(budget=X)` | 予算 X・倍率 1.0 | 同じ(語彙と空腹は上のとおり変わる) |
| `run_day(l4_scale=1.0)` | 按分 | 同じ(語彙と空腹は変わる) |
| `cli.run(...)` で語彙を渡さない | 語彙 v1・run_kind は arm(語彙) | 語彙 v3・ほかに腕が無ければ reproduction |
| `cli.run(...)` で語彙を渡す | — | 前と同じ(空腹 energy と倍率 0 は前から `cli.run` の既定) |
| CLI(`python -m shibuya.cli`) | v3・energy・無制限 | 同じ |
| `python -m shibuya.engine.run` | 語彙 v1・空腹 v1・按分 | 語彙 v3・空腹 energy・無制限 |
| `RunResult()` を直に作る | 欄の既定 v1・v1・1.0 | v3・energy・0.0(ランの結果は report が全部置くので影響なし) |
| 前の既定で書いた状態のファイルを既定で再開・テープを既定で再生 | 回った | 設定の指紋が違うので再開は止まる。再生は別のラン |
| byte-check の構成 `w6_golden_null_arm` | 語彙 v1 | 同じ(語彙 v1 を明示した) |
| `tools/c6/run_hash.py --no-ledger`・`tools/c7/occupancy_series.py` | 空腹 v1 | **空腹 energy**(語彙 v1・倍率 1.0 は明示して前と同じ) |
| `tools/c6` の `run_smoke` を通る 5 本・`tools/c7/salt_runs.py`・`tools/instruments/batch_width_gauge.py`(語彙を渡さない場合) | 語彙 v1 | 同じ(語彙 v1 を明示した・渡した値が勝つ) |
| `tools/c8/ablation_runner.py` の腕 | — | 同じ(10 腕に語彙 v1 を明示) |
| 試験の助け `tests/engine/speech/_s8b.py` | 空腹 v1 | 空腹 energy(親の裁定=このまま。§4-6) |
| 低い層の関数を直に呼ぶ(`templates`・`actions` ほか) | v1 | v1 のまま(変えていない)。ただし既定のランは v3 になったので、語彙を渡さずに低い層を読む 8 か所(パーサ・`fleet._format_ok`)は、既定のランでもランの語彙と食い違う(§4-8) |

### 4-16 再検収(直しの後・別の役)と親の直し

- 判定: 条件つき(高 0・中 1・低 3)。発注の直し(M1 の 7 本・byte-check の構成・L-2・L-4・記録)と、親の載せ直し(本体の頭へ・
  `runtime/systems/assemble.py` の import の 1 か所を手で解いた)は正しいと確かめた(読むだけ・pytest とランは回していない)。
- 〔中 M-1・親が直した〕`tests/engine/test_salt_seed_split_10f.py` の T3(回す役 `salt_runs` の最初の食い違いを、通しのランの独立の
  答えと比べる試験): M1 の直しで子のランは語彙 v1 になったが、独立の答えの側(`cli.run` を直に呼ぶ)は語彙を渡さず v3 になり、別の
  ランどうしを比べる形になっていた。独立の答えの側に語彙 v1 を明示し、子のランの manifest の語彙が v1 であることを 1 行で確かめる
  ようにした(前と同じ=両方 v1 どうしの比べ)。直した後にこの 1 本を回して通った。
- 低(残した所): L-a `tools/instruments/batch_width_gauge.py` の `setdefault` は `cmd_run` にだけあり、`run_one` を直に呼ぶと語彙 v3 で
  回る(道具の口からは通らない)/L-b 倍率に数でない値を渡すと `float()` の誤りの文で止まる(値を書く文にならない)/L-c
  `run_day(budget=X, l4_scale=NaN)` は止まらない(§4-14 の L-3 と同じ=予算を渡したランの倍率は検査しない)。
- `tests/engine/speech/_s8b.py` を使う 7 ファイルは、口の構造と、同じ設定どうしの比べだけを確かめている(空腹 v1 の 1 日でしか
  成り立たない性質・写した数・hash は無い)=空腹 energy のままでよい(§4-6)。

### 4-17 範囲の全体の試験(親・本体の頭へ載せ直した後)

- `pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`(この作業木・data のある作者の機械): **6,925 passed・
  1 failed・21 skipped・1 xfailed**(39 分 19 秒)。落ちた 1 本は前からの `tests/vocab/test_registry_from_tape.py::
  test_ab7_seed1_open_matches_the_parent_report`(linked の作業木でだけ落ちる。本体の木と CI では通る)。新しい失敗は無い。
- 土台(割る段 5a の群 1 の後)は 6,918 passed。増えた 7 本は、この版上げで足した試験(腕定義の表の語彙の明示・倍率の止め ほか)。
- 所要は、群 1 のときの同じ形の回(37 分 41 秒)より約 1 分半長い。引数を渡さずに `run_day` を呼ぶ試験が、呼数の多い別のランに
  なったぶんと見ている(**推測**。機械の揺れと分けて測ってはいない)。
- 再検収の中 M-1 の直し(§4-16)は、この回に入っている。`tests/c7` は手元では回していない(CI で回る)。

## 5. 欠陥 2 つの直し(第 348)

元の指示は返事その 9 §1 の 19・§5-2 の 6。§4-8 の 2 つ(艦隊の書式の判定・低い層の既定 v1 に頼って読む 8 か所)を直した。実 LLM の道だけが変わる。

### 5-1 棚卸し(直す前)

| 記録の名(§4-8) | 今の置き場 | 頼っていた低い層の既定 | 呼び手(既定に頼る数/全部)src・tests・tools・docs |
|---|---|---|---|
| `_parse` の 2(本文が None・空) | `act/intake/parser.py` の `_parse` | `_empty_result(errors, vocab_version="v1")` | src 2/5・ほか 0 |
| `_parse` の 1(対象) | 同上 | `foundation/vocab/actions.py` の `parse_target(..., vocab_version="v1")` | src 1/2・tests 58/64 |
| `_parse` の 1(役割語) | 同上 | `actions.is_role_action(word, vocab_version="v1")` | src 1/4・tests 1/4・tools 1/1 |
| `_fill_positional` の 2 | `act/intake/parser.py` の `_fill_positional` | `parser.find_action_word(text, vocab_version="v1")` | src 2/10・tests 3/3 |
| `commit.parse_action` | `act/intake/from_words.py` の `parse_action` | `parser.parse_two_line(text, vocab_version="v1")` | src 2/6・tests 65/104・tools 3/7・docs 2/15 |
| `fleet._format_ok` | `runtime/inference/fleet.py` の `_format_ok`(`FleetClient` の既定の判定) | 同上 | 同上 |

- `parse_action` は src に呼び手が無い(試験 9 か所だけ)。`_format_ok` は `FleetClient` の `format_check` の既定としてだけ使われる。
- mock のランが通るか: 語彙 v1・v2 の構成(byte-check の 19 構成のうち 13)は `_parse` の 4 か所を通る。ただし `_empty_result`・`parse_target`・
  `is_role_action` は v1 と v2 で同じ規則なので、ランの語彙を渡しても値は同じ。`_fill_positional` の 2 か所は、対象とひと言のラベルが両方
  ある応答では手前で返る。mock の v1・v2 の応答は `format_two_line` の形でいつも両方あるので、2 か所には届かない。`parse_action` は src に
  呼び手が無く、`_format_ok` は艦隊のランだけ。v3 の構成は `_parse_v3` を通るので 8 か所に届かない。よって mock の結果は動かない見立て
  (byte-check は親が回す)。
- src の中で語彙の既定を持つ関数は 34(`vocab_version` 33+`MockLLM` の語の並び `vocab`)。報告 347 §11 の 15 の「33 関数」と同じ数え方。

### 5-2 したこと

- 8 か所にランの語彙を渡した。`_parse` は受けた語彙を `_empty_result`・`parse_target`・`is_role_action`・`_fill_positional` へ渡す。
  `_fill_positional` は語彙を受け、`find_action_word` の 2 回へ渡す。`parse_action(text, vocab_version)` は `parse_two_line` へ渡す。
- 艦隊の書式の判定: `_format_ok(text, vocab_version)` と、版を結んだ判定を作る `format_check_for(版)` を足した。`FleetClient` は判定の
  既定を持たない(`format_check=None` のとき口は判定を持たない)。`FleetBridge` が組み立てのときに `client.bind_run_vocab(橋の語彙)` を
  呼び、ランの語彙の判定を結ぶ。組み立て(`runtime/systems/assemble.py`)は前から `FleetBridge` にランの語彙を渡しているので、配線は
  変えていない。明示して渡した判定は結び直さない。`format_retry=False` の口には結ばない。
- 低い層の既定を無くした 5 関数: `parse_two_line`・`find_action_word`・`_empty_result`・`is_role_action`・`parse_target`(`parse_target` は
  `landmarks` の後ろなので、語彙はキーワードだけで渡す形にした)。`_fill_positional`・`parse_action`・`_format_ok` は語彙を必ず受ける。
- 既定に頼っていた呼び手は、前と同じ値 `"v1"` を明示した(機械で当てた・台本は scratchpad): tests 136 か所(13 ファイル)・tools 4 か所(`c6/c6lib.py` 2・
  `fig/fig_ab7_actions.py`・`vocab/registry_from_tape.py`)。橋を通さない `FleetClient` 17 か所(`tests/llm/test_fleet.py` 14・
  `test_fleet_auth.py`・`test_fleet_contract.py`・`tools/vocab/adjudicate.py`)に `format_check=format_check_for("v1")` を明示した。
  `FleetBridge` を通す口は、橋の語彙(試験は前と同じ v1)で結ばれる。
- docs の古い台本で既定に頼る呼び出しは 2(`wallbounce-1003/r86/ab7_sample.py`・`ab7_surface_counts.py`)。どちらも今は無い
  `shibuya.llm` を読むので import で止まる=誤った結果を黙って書く形ではない。直していない。

### 5-3 前と変わる所(実 LLM の道だけ)

- 語彙 v3 のランの再生成は、減る応答と増える応答の両方がある。
  - 減る: 「なし」「食事」の応答を書式の誤りに数えない(直したい欠陥そのもの)。
  - 増える〔検収 中-1〕: 活動かまでを欠く応答と、v1 の 4 ラベルの形(「…対象: C-0001 ひと言: なし」)。前は v1 の規則で読まれ、
    ひと言の位置読みで書式どおりと判定されていた。今は v3 の規則で書式の誤り=温度 0 で再生成する。
- 語彙 v2 のラン: 「食事」の応答も、前は v1 の規則で書式の誤り=再生成していた。今は再生成しない。ラベルを省いた応答のうち行動欄に
  「食事」がある形で、位置で読むかが変わる(例 2 つを試験に固定)。発注文の「v2 は今までどおり」とは違う(同じ欠陥が v2 にもあった)。
- 語彙 v2・v3 のラン〔検収 中-1〕: 語彙の外の語を辞書で救えるか(``dictionary_candidate``=救えれば再生成しない)も、ランの語彙の表で
  引くようになった(前は v1 の表 `undefined-synonyms-v2`)。v2(表 v4)で新たに救える語は 6(見る・近づく・近寄る・食事する・食事を・
  飲食)、v3(表 v5)では 11(ぶらつく・休憩・待機・散歩・見る・近づく・近寄る・降車・食事する・食事を・飲食)。これらの語の応答は
  再生成しなくなる(休憩・待機・降車は v1 では行動語なので、判定は前と同じ)。救えなくなる語は無い(コードで 3 つの表を比べて確かめた)。
- まとめ: 再生成の数は、v3 では増えも減りもする。5070 のランでは、再生成の数の前後を、増えた分と減った分に分けて見る。
- 語彙 v3 のランに v1 の形の応答を返す偽の艦隊(`tests/c6/_fake_vllm.py` を使う `tests/c6/test_l4_l6_budget.py` の艦隊の 3 本)は、
  上の「増える」の例。前は再生成しなかった応答を再生成するようになった(確かめる中身は呼の上限と受理待ちの枠で、変わらず通る)。

### 5-4 試験

- `tests/llm/test_parser_run_vocab_348.py`: 8 か所のうち 7 か所(パーサの 6・`parse_action`)が渡した語彙で読むこと、v1・v2 で前と同じ
  こと、v2 で変わる読み 2 つ、既定を無くした 8 つの口が語彙なしで呼べないこと。
- `tests/llm/test_fleet_run_vocab_348.py`: 橋の語彙 v3 で「なし」「食事」を再生成しない(1 呼 1 要求)・v1 と v2 の橋の前の判定・v2 の
  「食事」の新しい判定・明示した判定と `format_retry=False` の扱い・橋を通さない口・`format_check_for`・`run_day` の形(v3 で再生成しない・
  v1 は前と同じ)。
- 直す前のコードで 25 本が赤、8 本(v1・v2 の固定と口の決まり)が緑。直した後は 33 本とも緑。
- 〔検収 中-2〕v3 の「再生成する」向きの 3 本を足した(橋の v3 で書式の誤りと v1 の 4 ラベルの形を再生成する 2・`run_day` の v3 で書式の誤りを
  全呼再生成する 1)。橋が語彙を結ぶ 1 行を外すと、この 3 本と v1・v2 の 4 本の計 7 本が赤になる(確かめて戻した)。今は 36 本とも緑。

### 5-5 残した既定(28)

語彙の既定を持つ関数は 34 → 28(27 が `vocab_version`・1 が `MockLLM.vocab`)。今回は 8 か所が頼っていた 5 関数と、使われていなかった
`parser._parse` の既定〔検収 低-2・呼び手は `parse_two_line` の 1 か所で、いつも渡していた〕を無くした。残り:
`act/apply.apply`・`from_words.undefined_fallback_code`・`from_words.intents_from_responses`・`ParseResult.with_dictionary_mapping`・
`undefined` の 7(`synonym_table`・`synonym_table_version`・`target_hints`・
`target_surface_hint`・`fallback_actions`・`map_synonym`・`UndefinedActionRegistry.__init__`)・`templates` の 3(`role_words_line`・
`b0_system`・`b0_sha256`)・`actions` の 8(`action_words`・`cross_action_words`・`role_action_words`・`safe_action_word`・
`engine_action_codes`・`compat_word`〔既定 v2〕・`action_code_of`・`spec_of`)・
`Renderer.__init__`・`LLMBridge.__init__`・`FleetBridge.__init__`・`run_day`(ランの入口・v3)・`weekly_reader.activity_to_action`・
`MockLLM.__init__`(`vocab`)。欄の既定は `RunResult.vocab_version`(v3)の 1 つ。

- 〔検収 低-1〕`FleetBridge.__init__` の既定 v1 は残した。語彙を渡さずに橋を作ると、v1 の書式の判定が黙って口に結ばれる。src で橋を作るのは
  組み立て(`runtime/systems/assemble.py`)の 1 か所だけで、そこはランの語彙を渡している。試験は既定の v1 で橋を作る所が約 10 か所ある。
  前は口そのものが v1 の判定を持っていたので、危うさは前より増えていない。橋の語彙をキーワードの必須にするのは次の版上げの候補。

### 5-6 まだ確かめていないこと

- 実 LLM(5070 の艦隊)のランでの確かめ(再生成の数の前後)。偽の艦隊の試験だけで確かめた。
- byte-check の 19 構成と範囲の全体の試験(親)。data の要る試験(作業木に data が無い)。

### 5-7 見つけたが直していないこと

- 〔検収 低-4〕`"v1"` を明示したことで見えるようになった、前からの食い違い(挙動を変えるので直していない。値の合否は変わらない):
  `tools/c6/c6lib.py` の `score_texts` は引数の語彙をパースと辞書に渡すのに、役割語の判定だけ v1 で見る(v3 では「並ぶ」が違う)。
  テープを読む 2 本(`tools/vocab/registry_from_tape.py`・`tests/engine/tape_analysis.py`)は、テープの語彙によらず v1 で読む。
  `tests/engine/test_intent_hold.py` は v3 の apply とランの中で `parse_target(…, vocab_version="v1")` を使う(使う語は v1 と v3 で同じ値)。
- `tools/vocab/adjudicate.py` は JSON の草案を艦隊で起草するのに、v1 の 2 行形の書式の判定を持つ=草案ごとに 1 呼の再生成が出る
  (前から。前と同じに回すため v1 を明示した)。
