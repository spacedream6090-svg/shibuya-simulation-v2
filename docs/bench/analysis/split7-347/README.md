# 割る段 7(`perception/renderer.py` を割る)の記録

段 7 は 5 つの commit に分ける(G0 → G-R1 → G-R2 → G-M → G-S・親の裁定 Q16)。計画・数の取り直し・親の裁定は親の scratch に在る(計画 §3・§3-5・§8・取り直し §7・§8・§15・§16・裁定 Q1〜Q18・P1〜P5・決め事 1〜12)。

## 1. G0-試験(土台 `b578df5`・2026-11-19)

割る前の試験の直しと、副作用の順の試験。src・tools・全ファイルの表・`map.toml`・`contracts.toml`・`pyproject.toml` は変えていない(`git status --short -- src tools` は空)。道具の側の G0(形の変更の照合の台本)は別の役が別の木で作る。

### 1-1. 直した本(取り直し §15-1 の 13 本と、差し替えの形の 1 本)

| ファイル | 行(直した後) | 前の読み | 後の読み | 裁定 |
|---|---|---|---|---|
| `tests/engine/test_resume_10d.py` | 596・725(読み 615・625・732・736・741) | 関数の中の別名 `RD` 2 か所=`Renderer`/`PerceptionAssets`・`Renderer`・`_TickCache` | 名の import | Q13 |
| `tests/engine/test_weather_calendar_10e.py` | 300(読み 303・309・342) | `REN`=`Renderer`・`_TickCache` | 名の import | Q13 |
| `tests/engine/test_intent_hold.py` | 57〜67(読み 12 か所) | `PR`=7 名と、同じ頂上の `Renderer` の名の import | 名の import 1 文(8 名) | Q13 |
| `tests/engine/test_two_layer_activity.py` | 66〜77(読み 11 か所) | `PR`=8 名と `Renderer` の名の import | 名の import 1 文(9 名) | Q13 |
| `tests/perception/facts/test_percept_schema.py` | 20〜21・24〜25(読み 43・137・156・157・167) | `R`=`Renderer`・`INTERO_UP_EDGES` | `Renderer` は名の import・`INTERO_UP_EDGES` は agent_codes から名で読む | Q13 |
| `tests/perception/test_weather_a48.py` | 31〜32(読み 16 か所) | `RD`=`PerceptionAssets`・`Renderer`・`SYNTHETIC_WEATHER_NOTE`・`_TickCache` | 名の import | Q13 |
| `tests/perception/facts/test_render_from_percept_bytes.py` | 36〜37・214〜220 | `R`=`Renderer`(13 か所)と、`near_person_text` の読みと差し替え | `Renderer` は名の import・`near_person_text` は §1-2 の #7 | Q13・P2 |
| `tests/engine/test_assets_10e_b0_b1.py` | 109・114〜115 | 別名 `REN` をタプルに入れて回す | `sys.modules[PerceptionAssets.load.__module__]`(§1-2 の #13) | 取り直し §15-1 |
| `tests/perception/test_p_see_activity.py` | 33〜42・64・74〜82 | `hasattr(RD, name)` | 助け `removed_renderer_names_left`・負の対照 1 本 | 決め事 9 |
| `tests/perception/facts/test_coef_removed_or_armed.py` | 29〜30・38〜47・63〜64・76〜83・102 | `hasattr(R, name)`・`R.Renderer` | 同じ助け・負の対照 1 本・`Renderer` は名の import | 決め事 9 |
| `tests/engine/memory/test_m0_store_schema.py` | 67〜68 | 範囲の手がかり `PERCEPTION`=renderer | `shibuya.foundation.text.templates` | Q12 |
| `tests/engine/memory/test_mr65_guards.py` | 155〜156 | 同じ | 同じ | Q12 |
| `tests/llm/test_fleet_contract.py` | 66〜67 | 同じ | 同じ | Q12 |
| `tests/perception/test_nearby_vectorized.py` | 152〜155・183〜184 | 手の代入 2 か所(#10・#11) | `pytest.MonkeyPatch.context()` の `setattr` | P3 |

- **Q13 の条件**(6 本とも、別名のモジュールそのものを差し替える所が無い)は、直す前に AST で確かめて立った: 6 本の差し替えはどれも `別名.Renderer` のクラスの属性(`test_resume_10d.py`・`test_weather_calendar_10e.py`・`test_weather_a48.py`)で、別名のモジュールへの `setattr`・代入は 0。名の import にした名が、同じファイルのほかの所で別に結ばれている所も 0(`test_resume_10d.py` の別の関数の `PerceptionAssets` は、同じ物の名の import)。
- 名の import の文の上に注を 1 行。`test_intent_hold.py`・`test_two_layer_activity.py` は、同じ頂上に在った `from shibuya.perception.renderer import Renderer` を同じ文にまとめた。
- `INTERO_UP_EDGES`(`test_percept_schema.py`)は `shibuya.foundation.vocab.agent_codes` から名で読む(G-S で renderer の再輸出が外れる)。裁定 Q6 の条件「2 つの定義が同じことを見る試験」は、`tests` の下(c7 を除くディレクトリを名指し)に無かった。読むのは agent_codes の 1 つだけ(`body_fixtures`・`test_change_detect_p6`・`test_energy_balance` と、この 1 本)で、`head_renderer_136fdbb.py` は HEAD の写し=空回りになる形は無い。
- **決め事 9 の 2 本**(`hasattr(別名, 名の変数)`): 助け `removed_renderer_names_left` を足した。表 `tests/_places.py` の `split_module_names("perception/renderer.py")`(renderer の元の名を頂上で定義する今のモジュールの全部)を 1 本ずつ import して見る。割る前は `shibuya.perception.renderer` の 1 本・割った後は名の割り先のモジュールの全部。**道具が書き換えない字面**にした: 第 1 引数は対応表の鍵(元の道)で、割る道具は表の鍵を書き換えない(5b の `split_source("cli.py")` と同じ形)=割った後も同じ鍵で割り先を引く。負の対照を 1 本ずつ足した(消したはずの名を、見るモジュールの 1 つ=`Renderer` か `_signage_seen` の定義の置き場に `monkeypatch.setattr(…, raising=False)` で一時に置くと、確かめが見つける)。
- **Q12**(範囲の手がかり `PERCEPTION` 3 本を `shibuya.foundation.text.templates` に): 替える前と後で、3 本の助けが作る範囲を、メモリの中で同じ呼び方で比べた。どれも同じ(`test_m0_store_schema` の `_layers`= 頭 25・葉 232/`test_mr65_guards`= 頭 1・葉 18/`test_fleet_contract`= 頭 34・葉 298)。元の置き場が `perception/` の今のファイルは 12 本(renderer を含む)で、前後で同じ集合。

### 1-2. 差し替えの形の直し(取り直し §8 の #7・#10・#11・#13)

- **#7 `near_person_text`**(`test_render_from_percept_bytes.py`・裁定 P2): 名を呼ぶ時に引く関数(`Renderer._b5`・`Renderer._nearby_items`)のモジュールを `sys.modules` で引いて、両方へ差し替える(割る前は同じ 1 つのモジュール=今と同じ)。`Renderer._b5_ranked` の定義の置き場が `_b5` と同じことも確かめる(assert)。定義のモジュールへは届かせない。
- **#13 `file_sha256`**(`test_assets_10e_b0_b1.py`): タプルに入れていた別名 `REN` を、`sys.modules[PerceptionAssets.load.__module__]`(`file_sha256` を呼ぶ時に名を引く `PerceptionAssets.load` の定義の置き場=割ると場面の側)にした。`PerceptionAssets` は名の import。
- **#10・#11**(`test_nearby_vectorized.py` の手の代入 2 か所・裁定 P3): `pytest.MonkeyPatch.context()` の `setattr` にした(有効範囲は前の `try/finally` と同じ)。
- 直す前と後で、直した 14 本の同じノードは全部同じ結果: 前 261 passed(slow を含む・skipped 0・failed 0)→ 後 261 passed。足したノードは 14(負の対照 2・副作用の順の試験 12)=後の全体は 275 passed。〔検収の後の直し(§1-7)で、副作用の順の試験は 12 → 18 本になった=足したノードは 20・後の全体は 281 passed〕

### 1-3. 差し替えの「外すと落ちる」(割る前の木・13 か所)

確かめに使った書き換えは、1 か所ずつ行った。差し替えの呼び出しを何もしない呼び出しに替えて(文の形は残す)狙いの試験を回し、同じ台本の中でバイトを戻して sha256 で確かめた。毎回、作業木の指紋(`git diff`・`git status --porcelain` の sha256)が確かめの前と同じことを見た。確かめの間、ほかの作業でこの木を編集していない。書き換える前に、狙いのノードを書き換えずに回して全部通ることを確かめた。#7 は、2 つのモジュールへの差し替えが今は同じ 1 つなので、1 つとして確かめた(描く側と場面の側を別々に確かめるのは G-R2・G-S)。

| # | 差し替え(行) | 狙いの試験 | 外したとき |
|---:|---|---|---|
| 1 | `tests/engine/proximity/test_runs.py:128` `_nearby_people_distance` | `test_b5_near_rows_are_within_radius_or_unit` | **落ちる**(`renders` 0 > 1000) |
| 2 | `tests/engine/test_resume_10d.py:625` `_named_closed_text` | `test_named_closed_memo_survives_a_resume` | **落ちる** |
| 3 | `tests/engine/test_sim_time_T.py:365` `__init__` | `test_start_date_moves_the_prompt_clock` | **落ちる**(`IndexError`) |
| 4 | `tests/engine/test_weather_calendar_10e.py:309` `__init__` | `test_b6_b3_words_body_heat_and_sun_follow_one_rule` | **落ちる**(`IndexError`) |
| 5 | `tests/engine/tools/test_c0_signboard_mark_invariance.py:87` `render` | `test_synthetic_run_arm_on_and_off_render_the_same_bytes` | **落ちる** |
| 6 | `tests/perception/facts/test_percept_is_scratch.py:327` `render`(`drop_percepts` の形) | `test_replay_full_hash_does_not_see_percepts` | 落ちない(下) |
| 7 | `tests/perception/facts/test_render_from_percept_bytes.py:220` `near_person_text`(2 つのモジュール=今は 1 つ) | `test_negative_control_one_byte_change_is_caught` | **落ちる** |
| 8 | 同 `:313` `prepare_tick` | `test_19_configs_render_the_same_bytes_as_head[w6_v3_default]` | **落ちる**(`KeyError`) |
| 9 | 同 `:314` `render` | 同じ | **落ちる**(計数が双子と違う) |
| 10 | `tests/perception/test_nearby_vectorized.py:155` `_nearby_people` | `test_rendered_bytes_are_unchanged_in_both_modes`(2 形) | **落ちる**(呼ばれた数 0 ≠ 100) |
| 11 | 同 `:184` `_nearby_people` | `test_negative_control_a_changed_reference_is_caught` | **落ちる** |
| 12 | `tests/perception/test_weather_a48.py:89` `__init__` | `test_a_run_without_processes_builds_the_weather_only_environment_without_data` | **落ちる**(`IndexError`) |
| 13 | `tests/engine/test_assets_10e_b0_b1.py:115` `file_sha256` の renderer の側(タプルから外す) | `test_b0_hashes_stay_out_of_the_final` | 最初は落ちない(下)→ 検収の後に assert を足して **落ちる**(§1-7) |

- 直した後に落ちないのは #6 の 1 つだけ。
- **割る前からの試験の弱さ**(割る段の違いではない・#6 は直していない・#13 は §1-7 で直した):
  - #6: この試験は、差し替えで `Percept` を外した再生と外さない再生の full-hash を比べる。差し替えを外すと 2 つの再生が同じになり、比べは必ず通る(差し替えが効いたかを見る行が無い)。`Renderer.render` のクラスの属性への差し替えそのものは、#5・#9 で外すと落ちる=届く。
  - #13: `fa != fb` は、ほかの 2 つ(`world.model.assets`・`environment`)の差し替えだけで立つ。renderer の側の差し替えが変える鍵を見る行が無い。届く先は確かめた: 3 つを差し替えた回と renderer の側を外した回の `frozen_sources` を比べると、renderer の側の差し替えだけで 4 つの鍵(`perception:w10_noise_stage_day.npy`・`perception:w10_noise_stage_night.npy`・`perception:w10_street_points.parquet`・`perception:w13_weather_hourly.parquet`)が 0 埋めになる。

### 1-4. 副作用の順の試験(親の決め事 1・裁定 Q17)

- 試験 `tests/perception/facts/test_perceive_order.py`・固定の値 `tests/perception/facts/perceive_order_frozen.json`(**sha256 `6a4b27c51e4a10ad260467a1c335c02b5bd4a810d07207208ba54911fd5d3015`**・出来事 2,961・138,321 バイト=検収の後に構成 `near_table` を足して作り直した値。前の値は §1-7)・作る台本 [tools/make_perceive_order.py](tools/make_perceive_order.py)(`--check` で今の JSON と同じバイトかを見る)。
- 記録するもの(1 本の出来事の列=`[種類, 中身, 乱数の流れの数, 前の出来事から変わった計数]`):
  - 口の呼び 13 種(`clock_fn`・`day_kind_fn`・`named_closed_lookup`・`weather_date_fn`・`weather_words_key_fn`・`weather_words_fn`・`acquaintance_fn`・`session_partner_fn`・`aware`・`memory_recall`・`heard_fn`・`heard_seen_fn`・`contact_fn`)。
  - 露出の控え(`signage_exposures` への追記)・前計算の始めと終わり。
  - 区切り(`perceive` の始めと終わり・描く側の終わり・呼びの印・刻みの終わり)。
  - 計数は、描画の計数 22 と刻みの控えの数 7(場面・時刻の見方・届いた発話・報告した発話・B3 のキャッシュ・知人のキャッシュ・露出)。
  - 乱数の流れは `rng_audit.StreamRecorder` で数え、最後に流れの列(用途名・カウンタ)も比べる。
- 構成(合成の場面・24 体・4 セル・seed 21・刻み 600 と 601。体ごとに `render` と `perceive` → `render_percept` を交互・601 は `perceive` が自分で前計算する道):

| 構成 | 中身 | 出来事 | 乱数の流れ |
|---|---|---:|---:|
| `fixed` | 固定枠・`signage_p_see=0.5`・露出の控え・口を全部・`weather_date_fn`・閉店の失敗の体と金欠の体・知人・会話の参加者・想起(0 件の体を含む)・発話(届く体と届かない体)・連絡の口 | 600 | 48 |
| `ranking` | 同じ口で `budget_mode="ranking"` | 600 | 48 |
| `near` | 近接の腕(`ProximityLayer(ProximityRule())` の索引と `NearView`・気づいた印の口 `aware` を差し込む・両方の刻みで前計算に渡す) | 608 | 48 |
| `calendar` | 天気の規則(`weather_words_key_fn`・`weather_words_fn`) | 601 | 48 |
| `near_table` | 〔検収の中-1〕近接の腕で、知人の口(`acquaintance_fn`)と気づいた印の口(`aware`)を外し、知人表(`Renderer(acquaintances=…)`)を渡す。知人の口を外した形=既定のランの道(知人の控え `_acq_cache` を引いて書く。既定のランは知人表を渡さない=表は空なので、ここでは知人のある表を渡して控えの中身を動かす) | 552 | 48 |

- 構成 3(近接の腕)は合成の個体で作れた(`ProximityRule()` の既定=`poi_cell` 無し=試験の合成の体の形)。
- 比べ方:
  - (a) 出来事の列の全体を、固定の値と完全一致で比べる。
  - (b) 1 回の `perceive` の中で、口の呼びが今の順の部分列であること。順は前計算 → 露出 → 閉店の 1 句 → 天気 → 近接の口 3 つ → 想起 → 発話 → 連絡で、docstring の 6 段を含み、docstring に無い前計算・発話・連絡も足した。あわせて、露出の控えの前に看板の抽選と計数が在ることも見る。
  - (c) 乱数の流れの列を比べる。
  - 構成ごとに、出るはずの口が少なくとも 1 回出ることも確かめる(確かめが空回りしない)。
- 固定の値の作り直し〔この 1 文は、検収の後の直し(§1-7)の前の値の話。直した後の確かめは §1-7〕: 台本を 3 回(`PYTHONHASHSEED` を 1・12345・既定で)回し、3 回とも同じ sha256。JSON に絶対の道・モジュールの名・ファイルの道は入れていない(割った後も同じ値のまま比べられる)。G-S まで作り直さない(裁定 Q17)。
- 試験は not slow で、18 本の呼び出しは 1 本あたり約 0.02 秒(構成ごとの記録は 1 回だけ作って使い回す)。
- **負の対照**: `Renderer.perceive` の 2 文を入れ替えた子クラスを `fixed` で回すと、2 つとも (a) が違い (b) が落ちる(`wake_time` は 14 回の `perceive`・`recall_heard` は 48 回で順が違う)。検収の後に、同じ 2 組を `near_table` でも回し、同じく落ちることを確かめる形にした(§1-7)。
  - 入れ替えの 2 組: `_wake_view` と `_time_view` の 2 文/想起の口と発話の口の 2 つの if。
  - 子クラスは、`perceive` の字面を AST で読んで作る。メソッドの名で作るので、割った後も定義のモジュールで同じ形に作れる。
- **見つかったこと**(直さずに固定した): 近接の 2 つの道で、口を呼ぶ順が逆。
  - セルの道は、知人(`acquaintance_fn`)→ 会話の参加者(`session_partner_fn`)。
  - 近接の腕の道は、会話の参加者 → 知人 → 気づいた印(`aware`)。
  - 今の挙動なので両方を別々に固定し、試験 `test_the_two_near_paths_call_the_hooks_in_opposite_orders` で名指しした。直すかはユーザーの判断。

### 1-5. 確かめ

| 何を | 結果 |
|---|---|
| 直した 14 本の前後(`-m "not gpu"`=slow を含む・`-n 2`・合図を取って) | 前 261 passed → 後 275 passed(前の 261 ノードは全部同じ結果・足した 14 が passed)。〔検収の後の直しの後は 281 passed=§1-7〕skipped・failed 0 |
| 狙いの束(`tests/perception`・`tests/engine/memory`・`tests/llm`・直した `tests/engine` の 5 本・`tests/tools/test_repo_guide.py`・`-m "not gpu and not slow"`・`-n 2`・合図を取って) | 1,020 passed・1 skipped(`test_m2_cue.py` の Ruri の重み=前から)・0 failed |
| 外すと落ちる(13 か所・§1-3) | 落ちる 11・落ちない 2(割る前からの試験の弱さ)・作業木の指紋は毎回同じ。検収の後に #13 へ assert を足して、落ちない物は #6 の 1 つだけ(§1-7) |
| 取り直しの書かない実行の台本(メモリの中で段 7 を当てる・読むだけ)を、直した後のこの木に向けた写しで回した | 手で直す一覧は 15 → **1**(`tests/engine/test_salt_seed_split_10f.py::_HASH_SITES` だけ=裁定 P4 で G-M に E8 の宣言)・差し替えの届く先の「見られなかった」は 1 → **0**・守りは全部「同じ」(決まりは宣言どおり 5)・道具が書き換える tests の import の文は 42 → 51(名の import にした分) |
| `git status --short -- src tools` | 空 |
| 副作用の順の固定の値(`make_perceive_order.py --check`) | 同じ(sha256 は上) |
| カード | 作り直した(`data.md` は単独で戻した・`--check` 最新) |
| 秘密の走査 | CLEAN(変えたファイルと足したファイル) |

### 1-6. 確かめていないこと

- 割った後(G-R2・G-S)の「外すと落ちる」(#7 は描く側と場面の側を別々に)。今の木では #7 を 1 つとして確かめた。
- 範囲の全体の試験と byte-check(src を変えていないので回していない)。`tests/c7`(renderer の読み手は 0 本=親の確かめ)。
- 決め事 9 の助けが割った後に見るモジュールの数(表の G-M の名の表が決まった後の数)。今は 1 本。

### 1-7. 検収の後の直し(検収=条件つき受入の中 2・親の裁定)

- **中-1(知人の控え `_acq_cache` の道が、どの構成でも通っていなかった)**:
  - わけ: 前の 4 構成はどれも知人の口(`acquaintance_fn`)を差し込んでいた。口が在ると `_acquaintances_of` は控えを読みも書きもしない。この口は `--relations on` のランにしか入らない(組み立ての関係の層の結線)。
  - 既定のランの道を組み立てで読んだ: 近接の規則は組み立てで常に作られ(`rule_from(mode=distance…)`)、知覚の系は毎刻み近傍の索引を作って前計算に渡す(`near=…`)=既定のランは**近接の腕の道**。関係の層は既定で off(知人の口も気づいた印も無い)。セルの道は、前計算に索引を渡さない形(試験や、刻みが合わない `render` が自分で前計算する道)だけで、ランは通らない=今回は近接の腕の道 1 つを足した。
  - 足した構成 `near_table`: 近接の腕で、知人の口と気づいた印の口を外し、知人表(`acquaintances=`・3 体に 1 体は知人なし)を渡す。ほかの口は前の構成と同じ。
  - 確かめ(試験 `test_the_table_path_fills_and_reuses_the_acquaintance_cache`): 知人の口は呼ばれない。知人の控えの数は 1 刻み目の終わりで 0 → 24(列の中で 24 回動く=体ごとに 1 回書く)、2 刻み目は使い回して 24 のまま。口つきの 4 構成では控えの数は 0 のまま(道が違う)。
  - 負の対照: 入れ替えの 2 組を `near_table` でも回し、(a)・(b) とも落ちる。足した構成に固有の負の対照として、知人の控えを使わない子クラス(`_acquaintances_of` をメソッドの名で差し替える=割った後も同じ形)を `near_table` で回すと、(a) が違い、控えの数が 0 のまま(上の確かめが落ちる形)。
  - 固定の値を作り直した(G0 の commit の前なので裁定 Q17 には当たらない): sha256 `e5f50ffb3b23ae8a863798401a9ad4e6c1ed18b6e59d8cba39c017e7596ca27d`(出来事 2,409)→ **`6a4b27c51e4a10ad260467a1c335c02b5bd4a810d07207208ba54911fd5d3015`**(出来事 2,961)。`PYTHONHASHSEED` を 3・777 と既定で回し、3 回とも同じ sha256。**前の 4 構成の列(出来事と乱数の流れ)は、作り直しの前と全部同じ**(読んで比べた・字面の違いは 4 構成の終わりの閉じの 1 行と、その後ろに足した構成だけ)。足した構成は出来事 552・乱数の流れ 48。
  - docstring の「docstring に無い副作用」の文を、知人の控えは `near_table` で固定する形に直した。
- **中-2(#13 の差し替えが、割った後に届かなくなっても気づけない)**:
  - 試験 `test_b0_hashes_stay_out_of_the_final` に、届いたことの assert を足した。`frozen_sources` の `perception:` の頭を持つ鍵を集め、数を確かめる。ファイルの sha256 の鍵 4 つ(`w10_noise_stage_day.npy`・`w10_noise_stage_night.npy`・`w10_street_points.parquet`・`w13_weather_hourly.parquet`)が全部差し替えた値(0 埋め)で、前の値と違うことを見る。
  - **裁定の「鍵が 4 つ」と違った所**: `perception:` の頭を持つ鍵は **5 つ**。5 つ目の `perception:noise_stage_cells` は集約した騒音の段の指紋で、`array_sha256` で作る(`file_sha256` を通らない=差し替えの外)。試験は「5 つ・うちファイルの 4 つは 0 埋め・集約の指紋 1 つは変わらない」と確かめる形にした(鍵が増減したら気づく)。
  - 鍵の字面は割っても変わらない: 頭の `perception:` は組み立てが付ける字面(f 文字列の中=割る道具は書き換えない)で、後ろの名はデータのファイルの名と、集約の指紋の固定の名。
  - 外すと落ちる(やり直し): renderer の側の差し替えだけを外すと、足した assert で **落ちる**(ファイルの 4 つの鍵が 0 埋めにならない)。作業木の指紋は同じ。
- 確かめ:
  - 変えた 2 本(slow を含む・`-n` なし): 22 passed(副作用の順 18・`test_assets_10e_b0_b1` 4)。前の 16(順 12・assets 4)から +6(足した構成の (a)・(b) 2、入れ替えの負の対照の `near_table` の 2、控えの確かめ 1、控えの負の対照 1)。
  - 束(`tests/perception` と `tests/engine/test_assets_10e_b0_b1.py`・`-m "not gpu and not slow"`・`-n 2`・合図を取って): 426 passed・0 skipped・0 failed。
  - `make_perceive_order.py --check`: 同じ。`git status --short -- src tools`: 空。カードは作り直した(`data.md` は単独で戻した・`--check` 最新)。秘密の走査: CLEAN。

## 2. G0-試験の、親の確かめと検収(第347・2026-11-19)

### 2-1. 別の役の検収

- 判定: **条件つき受入**(高 0・中 2・低 5)→ 中の 2 つを直した(§1-7)→ 再検収: **受入**(高 0・中 0・低 4)。中の 2 つは直っていて、直しで新しく入った穴は無い。前の 4 構成の列は、作り直しの前と 1 字も同じ(検収役が、前の JSON と比べた)
- 直した 14 本: 名の import にしたせいで差し替えが空振りする所は 0(どの差し替えも、`Renderer` のクラスの属性か、別のモジュールが的)。名の import を元の形へ畳むと、形の直しのほかは土台と AST が同じ。裁定 Q12 の 3 本は、試験が見る範囲が前後で同じ。
- 割った後の形(字面と、表に段 7 の行を当てた姿で): 決め事 9 の助けは、割る前は renderer の 1 本・割った後は名の割り先の 4 つを見る(第 1 引数は表の鍵=道具が書き換えない字面)。`near_person_text` の差し替えは、描く側と場面の側の両方へ届く形。手の代入 2 か所は、クラスの属性を差し替えて元へ戻す。
- 副作用の順の試験: 記録する 5 種はそろっている。口の包みは元の値をそのまま返す。近接の腕の構成では、口の順が逆の道を通ったことが列から読める。負の対照は効く(検収役が作った別の入れ替え 2 組でも、列が変わる)。固定の値の JSON は、作る台本の `--check` でバイトが同じ・`PYTHONHASHSEED` を替えても同じ・モジュールの名と道と行の番号は入っていない。試験は JSON を比べるだけで、作り直す道も飛ばす道も無い。
- 前の commit(`b578df5`=落ちていた slow の試験 1 本を語彙の版で 2 形にした直し)も見て、受入。

### 2-2. 検収の中と低・親の答え

- 中-1(副作用の順の試験が、知人の控えの道=口が無い既定のランの道を、どの構成でも通っていなかった): 構成を 1 つ足して固定の値を作り直した(§1-7)。前の 4 構成の列は 1 字も変えていない。**固定の値は、ここから G-S まで変えない**(裁定 Q17)。
- 中-2(差し替え #13 `file_sha256` が、割った後に届かなくなっても気づけない): 試験に、届いたことの assert を足した(§1-7)。知覚の資産の鍵は 5 つで、ファイルの sha256 の 4 つは差し替えた値になり、集約した騒音の段の指紋 1 つは変わらない(発注は「鍵は 4 つ」と書いたが、実際は 5 つ=実装役が見つけて、形を合わせた。親が受け入れた)。
- 低(直さない): `near_person_text` の負の対照は、割った後に片方の差し替えが抜けても通る=G-R2 と G-S の後に、描く側と場面の側を別々に外して確かめる(裁定 P2)。差し替え #6 は外しても落ちない=割る前からの試験の弱さ(記録だけ・報告に載せる)。助け `removed_renderer_names_left` が 2 本のファイルに同じ形で在る=段 8 の掃除で考える。`INTERO_UP_EDGES` の読み先を語彙の側にしたので、G-R1 までの間は確かめが前より強い(値は同じ)。前の commit の id `default_v3` はそのまま。
- 再検収の低(4 つ): 言い方の誤り(「知人表を渡す=既定のランの道」は、正しくは「知人の口を外す=既定のランの道」。既定のランの知人表は空)と、古い字面(作る台本の docstring の「4 つの構成」・§1-5 の数)は、親が文だけを直した(確かめの中身と固定の値は変えていない=`--check` は同じ)。知人の控えの専用の試験は、刻みの終わりの数しか見ない(使い回しと作り直しを見分けない)が、完全一致の比べが捕まえるので、そのままにする。**中-2 の assert は、data が要る試験の中に在るので、CI では飛ぶ**(効くのは作者の機械だけ)=G-S の発注に「この試験が飛ばずに回ったことを見る」を入れる。
- 見つかったこと(直していない・報告の判断待ちに上げる): 近接の 2 つの道で、口を呼ぶ順が逆(セルの道=知人 → 会話の参加者・近接の腕の道=会話の参加者 → 知人 → 気づいた印)。両方を別々に固定した。既定のランが通るのは近接の腕の道。

### 2-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`。中の直しの前の木で。回している間、この作業木は誰にも編集させていない=始めと終わりで `git status` が同じ) | 7,083 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・22 skipped・1 xfailed・39 分 33 秒。前の回(段 6 の本体・7,069 passed)から +14=足した試験 |
| 中の直しの後: 副作用の順の試験・資産の指紋の試験・形を直した試験 4 本(slow を含む・`-n` なし) | 94 passed・failed 0 |
| 固定の値を作る台本の `--check` | 同じ(sha256 `6a4b27c51e4a10ad260467a1c335c02b5bd4a810d07207208ba54911fd5d3015`) |
| `git status --short -- src tools` | 空(src と道具は変えていない) |
| 差分を読んだ(資産の指紋の試験の assert・落ちていた slow の試験の直し) | 発注と裁定のとおり |

## 3. G-R1(土台 `3c8e126`・2026-11-19)

裁定 Q6 の (c): `src/shibuya/perception/renderer.py` が自分で持っていた `INTERO_UP_EDGES` の定義を、`foundation/vocab/agent_codes.py` からの import に替えた(同じ文の定義が 5a の割る段で agent_codes に入っていた=二重の定義。割る道具は「在る名を足す」を断るので、割る前に 1 つにする)。変えたのは renderer.py の 1 本だけ。

### 3-1. 直した所

- 80 行: `from shibuya.foundation.vocab.agent_codes import (…)` の束に `    INTERO_UP_EDGES,` を足した(束の今の並び=字の順で `INTEROCEPTION_FIELDS` の次)。
- 前の 327〜328 行: 定義の 2 行(注 1 行と `INTERO_UP_EDGES: Final[tuple[int, ...]] = (4, 7, 9)`)を消した。
- `git diff --stat` は renderer.py の 1 本・+1・−2(3,171 行 → 3,170 行)。`__all__` の `"INTERO_UP_EDGES"`(140 行)は残した(G-S で道具が再輸出として外す)。モジュールの docstring の「二重定義」の項はつなぎの台帳の宣言の見出しなので触っていない(段 8 の文の掃除)=つなぎの台帳の試験は通る(下の束)。
- 取り直しの木 `8a1e409` と土台 `3c8e126` の間で renderer.py に差が無いことを先に見た(`git diff` が空)。

### 3-2. 直す前の確かめ

| 何を | 直す前 | 直した後 |
|---|---|---|
| 定義の文の AST(renderer と agent_codes) | 同じ | renderer に定義は無い(import) |
| 値 | 同じ `(4, 7, 9)` | 同じ |
| 型 | 同じ(tuple) | 同じ |
| 同じ物か(`is`) | **別の物**(2 つのモジュールがそれぞれ作った tuple) | **同じ物** |

- 別の物であることに頼るコード(`INTERO_UP_EDGES` を書き換える所・`is` で比べる所・`id` を使う所)は、src・tests(c7 を除くディレクトリを名指し)・tools に無かった。読み手は値で使う(段の数え・先頭の閾値)だけ。renderer の名で読む読み手は今の木に無い(`tests/perception/facts/test_percept_schema.py` は G0 で agent_codes から読む形にした・`head_renderer_136fdbb.py` は自分で定義を持つ HEAD の写し)。

### 3-3. 確かめ

| 何を | 結果 |
|---|---|
| 副作用の順の固定の値(`make_perceive_order.py --check`) | 同じ(sha256 `6a4b27c51e4a10ad260467a1c335c02b5bd4a810d07207208ba54911fd5d3015`)。固定の値の JSON は変えていない |
| 狙いの束(`tests/perception`・`tests/engine/bridging`・`tests/engine/state`・`tests/engine/memory`・`tests/tools/test_repo_guide.py`・`tests/test_places_guard.py`・`-m "not gpu and not slow"`・`-n 2`・合図を取って) | 690 passed・1 skipped(`test_m2_cue.py` の Ruri の重み=前から)・0 failed。副作用の順の試験・つなぎの台帳の試験を含む |
| `lint-imports`(作業木の src を `PYTHONPATH` に) | 11 kept・0 broken |
| `cli.py contracts --stage delete --tree . --check --probe` | 同じ・例外 17 行・15 辺・効かない例外 0(import の辺は増えない=renderer は前から agent_codes を読む) |
| **byte-check 19 構成**(基準 `3c8e126`・比べる側は作業木の src・記録 [bytecheck_R1/](bytecheck_R1/)・合図を取って) | **37 欄すべて同じ 19・動いた 0・誤り 0・439 秒**(基準の側 225 秒・比べる側 213 秒)。既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939(基準と同じ) |
| メモリの中で段 7 を当てる書かない実行(G0 で使った台本の写しを、直した後の木に向けて) | 止めた理由 0(「在る名を足す」の断りは出ない)・守りは全部「同じ」(決まりは宣言どおり 5)・手で直す一覧は `tests/engine/test_salt_seed_split_10f.py::_HASH_SITES` の 1 つだけのまま・見られなかった差し替え 0。台本は G-R2 の形(案 A1 の写し)を当てて回すので、その写しの import の束が今回の直しと同じ形(80 行に `INTERO_UP_EDGES,`・定義なし)であることも見た |
| カード | 作り直した(変わったのは docs の索引の数だけ=byte-check の記録の 3 本の分・`data.md` は単独で戻した・`--check` 最新) |
| 秘密の走査 | CLEAN(renderer.py・この記録・byte-check の記録・カード) |

### 3-4. 確かめていないこと

- 範囲の全体の試験(親が回す)。G-R2 の形(案 A1)への書き換えと、その後の byte-check(次の commit)。`tests/c7`(renderer の読み手は 0 本)。

## 4. G-R1 の、親の確かめと検収(第347・2026-11-19)

### 4-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 3)。検収役はファイルを 1 本も変えていない。
- 差分: src・tests・tools の差は `renderer.py` の 1 本だけ(+1・−2)。土台の 2 つの定義は、AST の dump が完全に同じ(値 `(4, 7, 9)`・型 tuple)。直した後は、`renderer` と `agent_codes` の `INTERO_UP_EDGES` が同じ物。消した注はコメントで、つなぎの台帳の宣言は含まない(宣言の走査の結果は前後で同じ)。docstring の「二重定義」の項は残っている(裁定 Q6=段 8 の文の掃除)。
- 別の物であることに頼るコードは無い: src・tools・tests(c7 を除くディレクトリを名指し)で全部の出現を洗い、書き換え・`is`・`id`・`setattr`・`reload` は 0。renderer の側だけを差し替える試験も、語彙の側を差し替えて renderer に効くと思っている試験も無い。
- 読み込みの順: 読むモジュールの集合は前後で同じ(足したのは、同じ import の束への名 1 つ)。`__all__` は前後で同じ。`from shibuya.perception.renderer import INTERO_UP_EDGES` と読む外の読み手は 0=G-S で再輸出が外れても落ちる所は無い。
- byte-check の記録: 19 構成すべてで 37 欄が同じ。比べる側の `renderer.py` の sha は今の木と一致し、読み込んだ src 277 本のうち違うのは `renderer.py` だけ。

### 4-2. 検収の低と、親の答え

- 低-1(G-R1 から、`split_module_names("perception/renderer.py")` は `renderer` と `agent_codes` の 2 本を返す。表の割り先が `agent_codes` で、`renderer` はもう定義しないため。§1-1 と §1-6 の「割る前は 1 本」は、G-R1 の後は「2 本」): 害は無い(消した名は `agent_codes` にも無く、負の対照が期待する一覧も変わらない)。ここに書いて残す。G-M の後の葉の数にも `agent_codes` が入る。
- 低-2(段 8 の文の掃除に足す字面): `renderer.py` の docstring の「層契約により import できない」(今の import と食い違う。裁定 Q6 で残すと決めた所)・`foundation/ports/percept.py` の ``renderer.INTERO_UP_EDGES`` の言及・`chooser.py` の 3 本目の写し `_INTERO_UP_EDGES`(範囲の外)。
- 低-3(import の束の並び=定数を先に・定数の中は ASCII の順、は前からの並びと合っている。これを確かめる道具は CI に無い): そのまま。

### 4-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| byte-check 19 構成(本体の道具・基準 `3c8e126`・直した後の木) | 37 欄すべて同じ 19・動いた 0・誤り 0・436 秒・既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。記録 [bytecheck_R1_parent/](bytecheck_R1_parent/)(実装役の記録は [bytecheck_R1/](bytecheck_R1/)=439 秒)。読み込んだ src 277 本のうち、sha が変わったのは `perception/renderer.py` の 1 本 |
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`。回している間、この作業木は誰にも編集させていない=始めと終わりで `git status` が同じ) | 7,089 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・22 skipped・1 xfailed・38 分 36 秒。G0-試験の回(7,083 passed)から +6=検収の後の直しで足した試験 |
| 差分を読んだ(`renderer.py`) | import の束に 1 行・定義の 2 行(注と文)を消した・ほかは 1 字も変わっていない |
| 性能の参考(byte-check の `w6_v3_default`・5,000 体・seed 1・1 日・mock の壁時計) | 基準 60.9 秒/後 54.1 秒(6 本並列。比べない参考値)。19 構成の合計は基準 945 秒/後 898 秒 |

## 5. G0-道具: 形の変更の照合の台本(土台 `3c8e126`=段 6 の M1 の後・親の決め事 2・E1・2026-11-19)

G-R2(renderer.py の中で `Renderer` を案 A1 の 3 つのクラスに分ける)の「前」と「後」の renderer.py を字面と AST で比べ、形の変更が挙動を変えていないことを確かめる台本を、割る道具に足した。src・`table.py`・`map.toml`・`contracts.toml`・全ファイルの表は変えていない。台本は読むだけで、何も書かない。

### 足した・変えたファイル

| ファイル | 行 | 何を |
|---|---|---|
| `tools/pkgmove/shapecheck.py` | 578(新) | 照合(①〜⑧)・宣言どおりの違い 2 つ・`super()` の見張り・計画の数え(`plan_counts`)・全ファイルの表 §4 のメソッドの割り先の読み |
| `tools/pkgmove/cli.py` | 44 / 1 | 口 `shapecheck`(`--before`・`--after`・`--plan-counts`・`--src-rel`・`--json`。前と後は道か `<commit>:<道>`)と docstring |
| `tools/pkgmove/README.md` | 40 / 0 | 口の使い方・8 項目・宣言どおりの違い・比べないもの |
| `tests/tools/test_pkgmove_shapecheck.py` | 355(新) | 試験 25 本(下) |
| カード 5 枚 | — | 道具で作り直した(`tests/tools`・`tools/pkgmove`・目次・`src/shibuya`・`src/shibuya/perception`=新しい試験が renderer の道を読む) |

### 台本が確かめる項目(どれか 1 つでも違えば終了コード 1)

| # | 項目 | 何を |
|---|---|---|
| ① | 頂上の文 | クラスの外の頂上の文が、並びも AST も字面も前と同じ(後に足した基底 2 つのクラスと、それにだけ要る import のほか)。枠のクラスの位置も同じ |
| ② | メソッド | 前の `Renderer` のメソッド(`__init__` を除く 62)が後の 3 つのクラスのどれか**ちょうど 1 つ**に在り、AST(docstring・デコレータ・既定の引数・注釈を含む)も字面も同じ。前に無いメソッドが無い・メソッドでない本体の文も同じ・枠の docstring とデコレータが同じ・枠の基底は `(PerceptScene, SignageNotice)` の順・基底 2 つは基底もデコレータも持たない。メソッドの置き場の表を出す(全ファイルの表 §4-23 との突き合わせは G-M) |
| ③ | `__init__` の文 | `PerceptScene.__init__` の文と `Renderer.__init__` の文(基底を呼ぶ 1 文を除く)を合わせた多重集合が前の `__init__` と同じ(AST と字面)・それぞれの並びは前の並びの部分列。**足してよいのは 1 文だけ**(台本に名指し=`Renderer.__init__` の docstring の直後の `PerceptScene.__init__(self, <位置の引数>, <名の引数>=<同じ名>)`。世界の側の引数を全部、同じ名で・位置は同じ順・`super()` は不可)。`SignageNotice` は `__init__` を持たない |
| ④ | 枠の `__init__` の口 | `Renderer.__init__` の引数(名・順・既定の値・注釈・キーワード専用か)・戻り値の注釈・デコレータ・docstring が前と同じ |
| ⑤ | MRO で引ける名 | 3 つのクラスの本体で結ぶ名の和が前の `Renderer` の名と同じ。基底どうしに同じ名が無い・枠と基底で同じ名は `PerceptScene.__init__` だけ(MRO の順に頼る名 0) |
| ⑥ | 書く属性 | `self.x` に書く属性の名の集合が前と同じ(`__init__` と、ほかのメソッドの分を分けて比べる) |
| ⑦ | 互いの属性を読まない | `PerceptScene.__init__` の文が `Renderer.__init__` の側だけで書く属性を読まない・逆も。**裁定 Q2 の条件 ① の文(「2 つの側が互いの属性を読まない」)どおり両向きとも止める**(世界の側を先に呼ぶので、心の側が世界の側の属性を読んでも値は同じだが、文に合わせた) |
| ⑧ | 文字列の定数 | 文字列とバイト列の定数の多重集合が前と同じ(新しい docstring=基底 2 つのクラスと `PerceptScene.__init__` の docstring は除く) |

- **宣言どおりの違い**(裁定 Q2・止めない・黙って通さない): 「引数の誤りが 2 つ以上のときに先に出る例外」(`__init__` の文の並びが変わったとき、2 つの側の入れ替わりの数と、誤りを出しうる文=`raise`・`check_*`・`parse` の前の並びを出す)と「属性の辞書の並び」(`__init__` で初めて書く属性の並びの違いの数を出す)。
- 見張り(止めない・出す): 3 つのクラスのメソッドの中の、引数の無い `super()`(検収役の知らせ=負の対照の子クラスが、メソッドの名で呼ぶ形に頼っている)。
- 後に基底 2 つのクラスが無いときは「形の変更ではない(クラスが 1 つのまま)」と答え、終了コード 2(前=後を渡しても「同じ」とは言わない)。前に基底が既に在る・枠が無いも 2(使い方の誤り)。
- 比べないもの: 文と文の間の注と空行(文の字面は、最初のデコレータの行から終わりの行まで)。

### 試験(`tests/tools/test_pkgmove_shapecheck.py`・25 本)

| 何を | 本 | 結果 |
|---|---:|---|
| 見本(`Renderer` のメソッド 3・`__init__` の文 9 が 2 つの側=4 と 5 に分かれる)の正しい形の変更が全項目「同じ」・置き場の表・宣言どおりの違い 2 つ・`super()` 無し | 1 | 通る |
| 前=後は「形の変更ではない」・前に基底が在る/枠が無いは使い方の誤り | 1 | 通る |
| **植えた変異**(1 つずつ・名指しの項目が違う): メソッドの本文を 1 字変える(②)・メソッドを 2 つのクラスに重ねる(②)・メソッドを落とす(②)・`__init__` の文の順を入れ替える(③)・`__init__` の文を 1 つ落とす(③)・1 つ足す(③)・基底の 2 つに同じ名のメソッド(⑤)・属性の名を変える(⑥)・世界の側が心の側の属性を読む(⑦)・心の側が世界の側の属性を読む(⑦)・文字列の定数を 1 字変える(⑧)・`Renderer.__init__` の引数の既定の値を変える(④)・クラスの外の頂上の文を変える(①)/足した 5 つ: 基底を呼ぶ文を `super()` にする(③)・基底を呼ぶ文が引数を 1 つ渡さない(③)・気づく側に `__init__`(③)・枠の基底の順を入れ替える(②)・メソッドの中の注を変える=字面だけ(②) | 18 | 18 とも落ちる |
| 変異の関数が見本の字面に当たる(空回りしない) | 1 | 通る |
| `cli.py shapecheck` の終了コード(同じ 0・違う 1・形の変更ではない 2・後が無い 2)と `--json` | 1 | 通る |
| 本物の renderer.py(commit `3c8e126` の blob に止めた=G-R2 の後も同じ入力): 計画の数・前=後は形の変更ではない/計画の分け方で作った A1 の形(試験の中で作る)が 8 項目とも同じ・宣言どおりの違い 2 つ・メソッドの本文を 1 字変えると ② だけ落ちる/`--before <commit>:<道>` で木を写さずに読む・`--plan-counts`・読めない blob は 2 | 3 | 通る(git が無い所では飛ぶ) |

### 今の renderer.py から数えた数(`cli.py shapecheck --before src/shibuya/perception/renderer.py --plan-counts`)

| 数 | 値 | 取り直し(§4・§15-3) |
|---|---:|---|
| `Renderer` のメソッド(`__init__` を含む) | 63 | 63 |
| `__init__` の文(docstring を除く) | 68 | 68 |
| 世界の側の文(`PerceptScene.__init__` へ) | 31 | 31 |
| 心の側の文(`Renderer.__init__` に残る) | 37 | 37 |
| `__init__` で書く属性 | 67(世界の側 30・心の側 37) | 67 |
| 側ごとのメソッド(世界・気づく・枠) | 24・2・37(枠は `__init__` と `render` を含む) | 24・2・36+`__init__` |
| 基底どうしの同じ名 | 0 | 0 |
| 2 つの側が互いの属性を読む | 0・0 | 読まない |
| `PerceptScene.__init__` の引数 | 12(`world`・`agents`・`assets`・`clock_fn`・`seed` と名だけの 7) | 12(位置 5・名だけ 7) |

- 分け方: `__init__` の文は `shapecheck.A1_WORLD_ATTRS`(計画 §4-2・裁定 Q2 の世界の側の属性 30)=書く属性がこの中だけの文(何も書かない文を含む)を世界の側に数える。メソッドは全ファイルの表 §4-23 の `Renderer.<名>` の割り先(percept_scene=世界・notice=気づく・ほか=枠。裁定 Q4 の `render` は枠)。
- 計画の分け方で、今の renderer.py の中で A1 の形を作り(試験とメモリの中だけ・写しは書いていない)、台本で照合すると 8 項目とも「同じ」(メソッドの置き場 `PerceptScene` 24・`SignageNotice` 2・`Renderer` 36)。宣言どおりの違いは 2 つ: `__init__` の文は 2 つの側が 21 回入れ替わる(後は世界の側が先)・初めて書く属性の並びは 67 のうち 60 の位置が変わる。引数の無い `super()` は無い。G-R1(`INTERO_UP_EDGES` の 1 文)はクラスの外の頂上の文だけを変えるので、G-R2 の照合の前は G-R1 の後の renderer.py を使う。

### 確かめ(重いものは合図を取ってから 1 本ずつ・合図は単独の rm で返した)

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove_shapecheck.py` | 25 passed |
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 174 passed・21 skipped(前と同じ顔ぶれ) |
| `tests/tools` の残り(`-m "not slow and not gpu"`・`-n 2`) | 642 passed・落ちた試験 0 |
| `map --check`・`contracts --stage delete --tree . --check --probe`・`lint-imports`(`PYTHONPATH` を作業木の src に) | 同じ・同じ(例外 17 行・15 辺)・11 kept |
| カード(build → `cards/data.md` を単独の `git checkout --` で戻す → `--check`) | 最新(150 本・変わったカード 5 枚) |
| `git status --short -- src`・秘密の走査 | 空・CLEAN |

### 親に聞くこと・確かめていないこと

- ⑦ は裁定 Q2 の文どおり両向きとも止める形にした(発注の注の「心の側が世界の側の属性を読むのは可」の側も止める)。今の renderer.py の計画の分け方では両向きとも 0 なので、G-R2 には効かない。緩めるなら、心の側の読みを宣言どおりの違いへ回す形に替えられる。
- 確かめていないこと: 本物の G-R2 の後の renderer.py(まだ無い)。照合は、計画の分け方で作った形と見本で確かめた。

### 検収の後の直し(検収=条件つき受入〔高 0・中 3・低 8〕・親の裁定=⑦ は両向きのまま)

検収役は、挙動が変わるのに台本が「同じ」と言う形を見本で 16 個見つけた(本物の renderer.py で起こりうるのは、局所の名の組・足した import・注の 3 系統)。G-R2 の前に塞いだ。台本は 932 行・試験は 55 本になった(src・`table.py`・`map.toml`・`contracts.toml`・全ファイルの表は変えていない)。

| 直し | 中身 |
|---|---|
| 中-1 局所の名と世界の側の口 | ③ に足した: (a) `__init__` の局所の名(引数の書き換えを含む・入れ子の有効範囲で結ぶ名は除く)を書く文と、前の並びでその後に読む文は同じ側 (b) 世界の側の文が使う枠の引数は世界の側の口に在り、世界の側の口の引数は世界の側の文が使う物だけ (c) 基底を呼ぶ文の名と世界の側の口の引数は 1 対 1(前からの確かめ)・世界の側の口は既定の値を持たない |
| 中-2 足した import | 既定を「足した import は 0」にした(足す・消す・並べ替えるは ① の違い)。許す口は `--allow-import "<文>"`(`check(…, allow_imports=…)`)で 1 つずつ名指し・名指しした文が後に無ければ違い |
| 中-3 注 | 項目 ⑨ を足した(`tokenize`): 前の注が後に同じ字面で在り、付く文が同じ(行の途中の注はその行の最も内の文・行の全部の注は次に始まる文・無ければ末尾)。後にだけ在る注は基底 2 つの頭でだけ許す(見張りの欄に出す)。節の区切りの注(`# ----------`)は字面の数で比べ、重ねてよい(親の決め=宣言どおりの違いの 3 つ目に数つきで出す)・落とすのは違い |
| 低-1 | 引数の無い `super()`・`__class__`・名前のマングリングを、見張りから ⓪ の止める側へ移した |
| 低-2・低-4 と前提 | 項目 ⓪「台本の前提」を足した(下の 11 個を前と後のソースで数え、0 でなければ「前提が崩れた=この台本の照合は、この形を守れない」と名指しで止める)。台本の docstring に一覧を書いた |
| 低-3 | 世界の側の `__init__` のデコレータと `async` を ③ で止める・基底 2 つは枠の直前に `(世界の側, 気づく側)` の順で並ぶことを ① で見る(計画 §4-5=`check_near_tiebreak` の後・`class Renderer` の直前) |
| 低-6 | 本物の renderer.py の試験は、blob が読めないとき、環境変数 `CI` が在れば飛ばさずに落とす(手元の浅い木では飛ぶ・わけを出す)。土台の blob を G-R1 の後の `dc496d7` に替えた |
| 低-7 | `--plan-counts` は、表から読んだ名がソースのメソッドに無い・世界の側か気づく側のメソッドが表から 1 つも読めないときは止める(終了コード 2)。表は `<枠か基底>.<名>` のどちらの名でも読む・`--table <commit>:<道>` で表も止められる。後のソースが文法の誤りのときは使い方の誤り(2)にした(README に書いた)。`--json` は作業木の中に書かない(README に 1 行) |
| 低-8 | 宣言どおりの違いの「誤りを出しうる文」の一覧が全部でない旨を、出力の文に書いた |

- 直さないこと(親の答え): 照合は計画の分け方(どの文が世界の側か)と突き合わせない(低-5=G-R2 の記録で `method_table` と `counts` を人が見る)。

#### 台本の前提(⓪・前と後で 0・`dc496d7` の renderer.py ではどれも 0)

1. 3 つのクラスの中に、引数の無い `super()` が無い
2. `__class__` を読まない
3. 名前のマングリング(`__x`=2 つの下線で始まり 2 つの下線で終わらない名。属性・名・def)が無い
4. `__init__` の中で `self` のメソッドを呼ばない
5. `__init__` の中で `hasattr`/`getattr`/`setattr`/`delattr`(self, …)・`vars(self)`・`self.__dict__` を使わない
6. `__init__` の中で `self` をほかの呼び出しへ渡さない(基底を呼ぶ 1 文のほか)
7. `__init__` で同じ属性を 2 つの文が書かない
8. 2 つの側が同じ属性を書かない
9. クラスの本体の文はメソッドと docstring だけ
10. 同じ名の def が 1 つのクラスに 2 つ無い
11. 頂上で同じ名を 2 回結ばない(頂上の if・try などの中を含む)

#### 足した変異(試験の植えた変異は 18 → 46・どれも名指しの項目で落ちる)

| 系統 | 変異 | 落ちる項目 |
|---|---|---|
| 中-1 | 局所の名を書く文を枠へ(読む文は世界の側)・読む文を枠へ(書く文は世界の側)・世界の側の口が使う引数を受けない・使わない引数を受ける・世界の側の口の引数に既定の値 | ③ |
| 中-2 | 足した import が組み込みの名を隠す・頂上の名を隠す・注釈にだけ要る import(名指しなし) | ① |
| 中-3 | `__init__` の文の前の注を落とす・注をずらす(別の文に付く)・注の字面を変える・後にだけ在る注(基底の頭のほか)・節の区切りを落とす・枠の上の注を基底の上へずらす・行の途中の注を落とす | ⑨ |
| 低 | 世界の側の `__init__` にデコレータ・`async`(③)・基底 2 つの順を入れ替えて置く(①) | ③・① |
| 前提 | 引数の無い `super()`・`__class__`・マングリング・`__init__` の中の self のメソッド・`hasattr(self)`・self を渡す・同じ属性を 2 回書く・クラスの本体の文・同じ名の def が 2 つ・頂上で 2 回結ぶ名(前と後の両方に植える) | ⓪ |

- 止めずに出す物の試験: 節の区切りを重ねる(宣言どおりの違い 3 つ目「1 行」)・基底の頭の注 2 つ(見張りの欄)・名指しの import(見張りの欄)・名指しした import が後に無いと ① の違い。
- 表の名の食い違いの試験: 表の名がソースに無い・気づく側を読めない、で止まる・基底の名で書かれた表も読む。
- 検収役の変異の台本(見本 2 の 47 形)を、直した台本で回すと 47 とも「違う」になった。ただし見本 2 は前にクラスの属性と `super()` を持つので、多くは ⓪ で落ちる。止める項目を名指しで確かめるのは、上の試験の見本(前提を満たす形)で行った。

#### 本物の renderer.py(`dc496d7`=G-R1 の後)

- 計画の分け方で作った A1(文を前の注ごと動かす)は ⓪〜⑨ とも「同じ」。メソッドの置き場は `PerceptScene` 24・`SignageNotice` 2・`Renderer` 36。宣言どおりの違いは 2 つ(入れ替わり 21・位置の違う属性 60)で、節の区切りは重ねていない(9 行とも、続くメソッドと一緒に 1 つのクラスへ動く)。
- 数(`--plan-counts`): 前と同じ(メソッド 63・`__init__` の文 68=31+37・書く属性 67・側ごとのメソッド 24・2・37・基底どうしの同じ名 0・互いの読み 0・0・世界の側の口の引数 12)。
- 植えた変異: メソッドの本文を 1 字=② だけ・`near_salt` の既定の文だけを枠へ=③(局所の名 `near_salt`)・`_near_salt64` を書く文だけを枠へ=③(同)・世界の側の口から `near_order` を漏らす=③(受けない)。

#### 台本が今も見ない物(G-R2 の発注で、ほかの確かめで受ける)

- 実行の挙動の全体(byte-check 19 構成・範囲の全体の試験)。属性の辞書の並びの効き方も実ランで受ける。
- 計画の分け方との突き合わせ(どの文とメソッドをどちらの側に置いたか)=`method_table` と `counts` を、`--plan-counts` と全ファイルの表 §4-23 の割り先に人が突き合わせる。
- `__qualname__` の変化(心の読みの固定の表の鍵 2 つ=裁定 Q11)・`CLASS_IDS` と凍結の JSON の 2 行(Q9)・`OWNER_ALT_CLASSES`(Q10)。
- 差し替え 13 か所の「外すと落ちる」(決め事 3・`near_person_text` は 2 つの側を別々に外す=P2)・性能(決め事 4)。
- 空行と、外の物への副作用の順(`__init__` の文が呼ぶ関数の中身)。

#### 確かめ(重いものは合図を取ってから 1 本ずつ・合図は単独の rm で返した)

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove_shapecheck.py` | 55 passed(前は 25) |
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 174 passed・21 skipped(前と同じ顔ぶれ) |
| `tests/tools` の残り(`-m "not slow and not gpu"`・`-n 2`) | 642 passed・落ちた試験 0 |
| `map --check`・`contracts --stage delete --tree . --check --probe`・`lint-imports`(`PYTHONPATH` を作業木の src に) | 同じ・同じ(例外 17 行・15 辺)・11 kept |
| カード(build → `cards/data.md` を単独の `git checkout --` で戻す → `--check`) | 最新(150 本) |
| `git status --short -- src`・秘密の走査 | 空・CLEAN |

## 6. G0-道具の、親の確かめと検収(第347・2026-11-20)

### 6-1. 別の役の検収

- 1 回目の判定: **条件つき受入**(高 0・中 3・低 8)。計画の分け方で作った本物の A1 は 8 項目とも「同じ」・植えた変異 18 も落ちる。**ただし、挙動が変わるのに「同じ」と言う形が、見本で 16 個見つかった**(検収役が、変異 47 形を自分で作って当てた)。本物の renderer.py で起こりうるのは 3 つ: 中-1(`__init__` の局所の名の頼りと、世界の側の口の引数を見ていない=本物では `near_salt` の 1 組)・中-2(足した import を除く口が広い=名を隠す import が通る)・中-3(文と文の間の注を比べていない=注 281 行のうち 150 行)。
- 親の裁定: 中の 3 つは全部直す。`super()`・`__class__`・名前のマングリングは、見張りから止める側へ。台本の前提(今の renderer.py では 0 の形)は、数えて崩れたら止める。節の区切りの注は重ねてよい(落とすのは不可)。直しの中身は、上の節の小節「検収の後の直し」。
- 再検収: **受入**(高 0・中 0・低 6)。前回の中 3 つは、本物の renderer.py で起こりうる形をどれも塞いだ。新しく見つけた穴は、どれも本物で当たる所が 0。検収役が、前回の 16 形を、台本の前提を崩さない見本に植え直し、本来の項目(①・③・⑨)で落ちることを確かめた。**この台本を G-R2 の受けに使ってよい**(条件= 終了コード 0 に加えて、数・メソッドの置き場・宣言どおりの違いの中身・見張りの欄を人が突き合わせる。台本が見ない物は、ほかの確かめで受ける)

### 6-2. 親が回した確かめ(検収の後の直しの後)

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove_shapecheck.py`(`-n` なし) | 55 passed・skipped 0。環境変数 `CI` を立てた回も 55 passed(土台の blob が無いと落とす形) |
| `tests/tools/test_pkgmove.py`(not slow) | 174 passed・21 skipped(飛ぶ試験の顔ぶれは前と同じ) |
| `tests/tools` の残りと `tests/test_places_guard.py`(not slow・`-n 2`) | 660 passed・failed 0 |
| 台本を、**本物の G-R2 の後の renderer.py** に当てた(土台 `dc496d7` の blob と、別の作業木の形を変えた後のファイル) | ⓪〜⑨ の 10 項目とも「同じ」・メソッドの置き場は世界 24・気づく 2・枠 36・宣言どおりの違いは 2 つ(2 つの側の入れ替わり 21 回・位置の違う属性 60)・数は 63・68(31+37)・67・口の引数 12・基底どうしの同じ名 0 |
| 前と後に同じ物を渡した回 | 「形の変更ではない」(終了コード 2)=黙って「同じ」と言わない |
| `cli.py map --check`・`cli.py contracts --stage delete --tree . --check --probe`・`lint-imports`(作業木の src) | 同じ・同じ・11 kept |
| `git status --short -- src` | 空(src は変えていない) |

### 6-3. 台本が今も見ない物(G-R2 と G-S で、ほかの確かめで受ける)

- 実行の挙動の全体(byte-check 19 構成・範囲の全体の試験)。属性の辞書の並びがランの値に入らないことも、ここで受ける。
- 計画の `__init__` の分け方の表との突き合わせ(G-R2 の記録に、文ごとの表を書く)。
- メソッドの `__qualname__` の変化(心の読みの凍結の表の鍵で受ける)・クラスが増えたこと(クラスの名の表と凍結の JSON・`OWNER_ALT_CLASSES`)。
- 差し替えの「外すと落ちる」・性能・空行・外の物への副作用の順(副作用の順の試験で受ける)。
- **再検収が見つけた、台本が数えない書き方**(どれも、今の renderer.py では当たる所が 0=検収役が台本と別に数えた。G-R2 は、文の多重集合とメソッドの字面の確かめがあるので、前に無い形を後に持ち込めない。段 8 でこの台本を使い回す前に塞ぐ候補): 局所の名の頼りでは、内包の中の `:=`・文の中の `import … as`・閉包の遅い結び付き。注では、1 つの文に付く注の塊の中の行の入れ替え・枠の `__init__` の上の注を世界の側の `__init__` の上へ動かす形。前提の数えでは、引数つきの `super(Renderer, self)`・マングリングの名が引数の名やキーワードにだけ在る形・`__init__` で property を読む形・`self` を入れ物や f 文字列で使う形・頂上の `for`/`with` の変数による結び直し。
- 記録の文の細部(再検収の低): 上の小節の「検収役の 47 形とも違う」には、正しい形 2 つが含まれる(その見本は、台本の前提を崩す物を持つので、正しい形も ⓪ で止まる)。前提を崩さない見本では、正しい形は「同じ」になり、16 形は本来の項目で落ちる(検収役が植え直して確かめた)。
