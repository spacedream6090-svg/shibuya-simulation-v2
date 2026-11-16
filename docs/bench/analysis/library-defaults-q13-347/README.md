# Q13(第347)ライブラリの既定を CLI にそろえる(library-defaults-q13-347)

> 版上げ。発注: [返事その 8](../../../design/prompt-2026-11-16-reply8.md) §1-2 の Q13(決定の正は原文)、親の裁定(計画 `plan_bumps`
> §2-3 の Q13-1〜Q13-8・段 0 の後の裁定=語彙は (s1)・呼数の倍率は (a′))。作業の枝 `work/q13-defaults-347`。実装役 Opus 5.5。
> byte-check・範囲の全体の試験・commit・タグ・版上げの履歴への写しは親。**この下書きは commit ① の節だけ**(commit ② の節は後で足す)。

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
