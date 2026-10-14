# 第 2 期 2-4 版上げ 2 回目(vb24)の記録

> 実行役(Opus 5.5)の記録。親(Fable 5.1)の検収の前。commit していない(親が段ごとに V1 → V7 の順に重ねて commit する)。作業木の枝 `2-4/version-bump-2`(土台 HEAD `9f631b0`=2-1・2-2・2-3・2-3b・3-3 を含む)。
> 正: [計画](../../../../design/v2-implementation-plan-2026-10-12.md) 第 2 期 2-4 の行(2-1・2-2・2-3b を束ねる・記憶の変更は入れない・動いた量を記録)・[10e の記録](../10e/README.md)(版上げ 1 回目の形=変更ごとに commit・19 構成の byte-check・ACT=資産の活性化・RET=切替口の削除)・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0(版上げは親が決め動いた量を記録・S6=GPU の実行は止まる地点=本段は mock だけ)・各段の記録([prox22](../prox22/README.md)・[ec21](../ec21/README.md)・[tt23b](../tt23b/README.md)・[md23](../md23/README.md)・[gauge20](../gauge20/README.md))。
> **入れないもの**: 記憶の変更(M1〜M5)・energy.py の第 18-1 表の置き換え(PENDING §1-1)・京王チャレンジ枠の扱いの変更(仮-15=確認が出るまで京王の行を含めたまま活性化し、戻せる切替口を残す)・W17 の勤務の時間の出どころ(2-1 の既定化は賃金の額が現実の 1/4 のまま=宣言)。
> 測った機械: Windows 11・x86-64・論理 CPU 20。byte-check は 19 構成・mock/classical 5,000 体・seed 1・1 シミュ日・テープつき([10e/byte_check_10e.py](../10e/byte_check_10e.py))。生の side・テープ・状態のファイルは作業木の `_bc/`(git の外=載せない)。本書には比べた結果と道具だけを置く。絶対パス・ホスト名・個人名は書かない。

## 0. 結論(段ごと)

(段ごとに追記)

## V1 資産の活性化(2-3b の W12 実ダイヤ+2-3 の W9 の影 7 日の窓)

### V1-1 変えたこと

| ファイル | 何を |
|---|---|
| `src/shibuya/build/vis/w9_shadow.py` | **〔仮採用=親の判断待ち〕W9 の容量の宣言を実測に合わせた**: `BUDGET_BYTES_PER_DAY` 10,000,000 → **13,000,000 B/再生日**(356,732 点 × 288 面のビット表=12,842,624 B/日に約 1.2% の余白)・ゲートの名 `shadow_bytes_per_day_le_10mb` → `shadow_bytes_per_day_le_budget`(値を名に持たない)。影の点は間引かない(前からの方針)。比べた案は §V1-3 |
| `src/shibuya/build/field/w12_real_timetables.py` | 京王(ODPT チャレンジ枠)の**戻せる切替口** `USE_ODPT_CHALLENGE`(既定 True=今の実ダイヤのまま活性化=PENDING 仮-15 のユーザーの確認まで)・`tables_in_use()`・`input_rel_paths(…, in_use=True)`。False でチャレンジ枠の表を読まず(入力の一覧・W19 の資産の表からも外れる)、井の頭線は実データの無い線=等間隔の推定の道(ゲート `equal_interval_lines_remaining`=1)|
| `src/shibuya/build/field/w12_external_nodes.py` | 版の表 `w12_timetable_versions.json` で、実データの無い線(切替口 False の井の頭線)の宣言を「等間隔の推定」に(既定=残る線 0 では出力は同じ) |
| `src/shibuya/build/audit/w19_freeze.py` | `BUILD_INPUT_FAMILIES`(holdout の層と同じ元かの照合)を切替口に依らない元の宣言に(`in_use=False`・既定の値は同じ) |
| `tools/c8/sensitivity.py`・`tools/c8/expedient_triage_v1.json`・`tools/c8/sensitivity_v1.json`・`docs/bench/c8/sensitivity_v1.*` | 感度の台帳を活性化の後の build_manifest(`6a7d34e8…`・126 行)で作り直した(§V1-6) |
| `docs/design/v2-world-data-build-spec.md` | D-W10 と W9 の段の行に改訂の注(宣言 13,000,000 B/日・仮採用) |
| 試験 | §V1-7 |
| 本記録の道具 | [tools/activate_vb24.py](tools/activate_vb24.py)(組み立て・差の表・写し・戻し・確かめ)・[tools/w9_shapes.py](tools/w9_shapes.py)(影の形の比べ)・[tools/triage_w12_2_4.py](tools/triage_w12_2_4.py)・[tools/c8_notes_2_4.py](tools/c8_notes_2_4.py)(感度の台帳)・[tools/table_vb24.py](tools/table_vb24.py)(動いた量の表)・[tools/goldens_vb24.py](tools/goldens_vb24.py)・[tools/regold_vb24.py](tools/regold_vb24.py)(golden の張り替え) |

### V1-2 資産の組み立てと活性化の手順(**写すのは親**)

- 2-3b(`data/world/v2_stage_2-3b/`)と 2-3(`data/world/v2_stage_2-3/`)は、どちらも本体の v2 の写しから別々に組んだので、W18〜W20 の見出しと `build_manifest.json` が互いに食い違う(2-3b の W12 の見出しの expedients も直す前の文)。そこで **1 つに組み直した**: 本体の v2 の直下のファイル 104 本(W17 のプロンプトと応答の jsonl を除く)と `acceptance/` を `data/world/v2_stage_2-4/` へ本物のコピーで写し(sha256 一致)、作業木の src(W9 の 7 日の窓+W12 1.2.0+V1 のゲートの宣言)で W9・W12・W18・W19・W20 を組み、ほかの 16 段は `--keep-stage`。

  ```
  PYTHONPATH=src python docs/bench/analysis/wallbounce-1012/vb24/tools/activate_vb24.py stage --record <作業用>/stage.json
  ```

  **2 回組んで build_hash `6a7d34e858e07210…` が一致**(決定的・終了コード 0=走らせた段のゲートは全部 PASS・落ちたゲートは保った W10 の較正 1 件だけ)=[v1_stage_build.json](v1_stage_build.json)。エンジンが読むファイルは 2-3b・2-3 の資産とバイト一致(`w12_timetables.parquet` `7ef7ab90…`・`w12_timetable_versions.json` `4ee484eb…`・`wc_index.json` `a05f5438…`・影の 8 日)。
- 差の表と写すファイル(`plan`): 本体の v2 と組んだ資産の直下+`acceptance/` を sha256 で比べ、動いた 14 本を `data/world/v2_steps_2-4/` に写して `MANIFEST.sha256`(sha256・パス・added/moved)と `plan.json`(前後の sha256・md5・バイト数・build_hash)を書いた=[v1_activation_plan.json](v1_activation_plan.json)。**同じ 93 本・置き換え 11 本・追加 3 本・本体の v2 だけにあるもの 0**(W17 の jsonl と下位のフォルダは比べず触らない)。build_hash **`5ff1bacf7fd9c773…` → `6a7d34e858e07210…`**。

| ファイル | 扱い | sha256(前・先頭 16) | sha256(後・先頭 16) | md5(後・先頭 12) | バイト 前 → 後 |
|---|---|---|---|---|---|
| `W12.header.json` | 置き換え | `a6be78c810fa12a8` | `a3f7ef67f2edc693` | `48f55f7a3655` | 9,484 → 18,027 |
| `W18.header.json` | 置き換え | `35e07624930caa66` | `50a943e4cd94a8e3` | `a9dc22f934b0` | 5,989 → 5,989 |
| `W19.header.json` | 置き換え | `ac2ae4d3f18cc106` | `5c8c2565ccaf339a` | `75a93a7c2077` | 14,844 → 22,354 |
| `W20.header.json` | 置き換え | `72de2748a7cac25c` | `d540f3bfb7e452e9` | `d9481e92d1a6` | 2,602 → 2,568 |
| `W9.header.json` | 置き換え | `5b6be04d8a2547fd` | `5e1db7977cd3f075` | `71fdeea5b079` | 4,053 → 4,628 |
| `acceptance/gate_table.md` | 置き換え | `f1e3fd0346a5b6b4` | `0f755af3d91b0d09` | `1e70e46b0297` | 11,919 → 12,177 |
| `acceptance/summary.json` | 置き換え | `45fb28be64eb9836` | `c9c809e511752b38` | `3411c7fb9e1b` | 19,315 → 20,166 |
| `build_manifest.json` | 置き換え | `7d53badfb7e9a0ae` | `bc156909de308695` | `41fbb36a8482` | 141,287 → 157,962 |
| `w12_timetable_versions.json` | 追加 | `—` | `4ee484eb75037467` | `d17338957856` | 0 → 9,433 |
| `w12_timetables.parquet` | 置き換え | `c548b2bb7ecd5c21` | `7ef7ab9038348e59` | `f3aec6ccfb6a` | 30,956 → 23,645 |
| `w19_freeze.json` | 置き換え | `60dbcb6bdf3f2942` | `f1e45e9822f469c5` | `8aba396c341c` | 24,062 → 32,502 |
| `w9_shadow_2026-07-18.npy` | 追加 | `—` | `143400d4db326c45` | `e66ca6fc788d` | 0 → 12,842,624 |
| `w9_shadow_2026-07-19.npy` | 追加 | `—` | `82f5e4f36bd119d7` | `4da8909c0dab` | 0 → 12,842,624 |
| `wc_index.json` | 置き換え | `9e9c4659c5750110` | `a05f54387425090e` | `7943c09ff1c2` | 15,090 → 15,090 |

- **親が実行する手順**(リポの根・作業木の src を `PYTHONPATH` に):

  ```
  T=docs/bench/analysis/wallbounce-1012/vb24/tools/activate_vb24.py
  python $T apply --dry-run          # 前提の確かめ(本体の v2 が plan の「前」と同じ・steps の sha256・退避先が空)と写す一覧
  python $T apply                    # 置き換える 11 本を data/world/v2_pre_2-4/ へ退避(MANIFEST.sha256・plan.json)→ 14 本を写す
                                     # → 写した全部の sha256 と build_hash 6a7d34e8… を確かめる(違えば終了コード 3=revert で戻せる)
  python $T verify --want after      # いつでも: 本体の v2 が活性化の後と同じか
  python $T revert                   # 戻す: 退避した 11 本を写し戻し・足した 3 本を消し・build_hash 5ff1bacf… を確かめる
  ```

- 実装役がしたこと(**乾いたラン**): `apply --dry-run` を本体の v2 に当てて前提 OK(何も書いていない)。道具の本番の道は作業用の写し(本体の v2 の直下のファイルの写し `_bc/fake_v2`)で `verify --want before` → `apply` → `verify --want after` → 2 回目の `apply --dry-run`(前提が「前」と違うので止まる)→ `revert` → `verify --want before` を通した(全部の sha256 と build_hash が一致)。本体の `data/world/v2/` は書いていない。
- 世界資産の版の宣言: 活性化の後の v2 の build_hash = **`6a7d34e858e07210d39614f86bd5e47510dd0eb9d424b032672fd21b59702f68`**(W9 1.0.0 の 8 日の影・W12 **1.2.0** 実ダイヤ・W18〜W20 は組み直し)。

### V1-3 W9 の 10 MB/日のゲート(親が決める=実装役は案 A を仮に入れた)

| 案 | 1 日の大きさ(07-13) | 中身 | 費用・影響 |
|---|---|---|---|
| **A 宣言を実測に合わせる(仮採用)** | 12,842,624 B(今のまま) | `BUDGET_BYTES_PER_DAY` = 13,000,000・ゲートの名を値を持たない形に・設計書 D-W10 に改訂の注 | エンジンは変えない(暦の日付の 1 日ぶんを memmap で開く=RSS に効くのは使う日の面だけ)。影 8 日で 103 MB の置き場。W9 の見出し(params の予算)・W20 の落ちたゲートの表が動く(build_hash に入るのは出力の sha256 だけ=影のファイルは同じ) |
| B1 昼の面だけ残す | 7,446,864〜7,625,232 B(夜の面 117〜121 面=全ビット 1 を省く・夏) | 夜の面は太陽の高度から作り直せる | エンジンの読み口を変える(面の番号の表が要る)。memmap は保てる。冬は昼が短いのでさらに小さい |
| B2 zlib で 1 日を丸ごと圧縮 | 3,009,416〜3,044,017 B | 読むときに 1 日を展開(約 32 ms/日) | memmap を失う(1 日 12.8 MB を RAM へ)。エンジンの読み口を変える |
| B3 昼の面だけ+zlib | 3,001,775〜3,037,194 B | B1+B2 | 同上 |

- 実測は [v1_w9_shapes.json](v1_w9_shapes.json)(`tools/w9_shapes.py`・2-3 の資産=2-4 と同じバイト)。B 案はどれも影のファイルの sha256 が変わる(manifest の `frozen_sources` が動く・値は同じなので final は動かない見込み=未測)。
- 実装役の推奨: **A**(宣言の前提 239,028 点が W10 の 356,732 点に変わったのが食い違いの原因で、エンジンは使う日の面しか開かない=RAM の予算に効かない。B はエンジンの読み口を変える版上げになる)。B を選ぶなら W9 とエンジンの読み口を 1 段で直し、影の資産を組み直す。

### V1-4 動いた量(19 構成・5,000 体・seed 1・1 日・既定の引数)

- 前=本体 HEAD `9f631b0` の src の写し(錨はエンジンが開く 3 本だけ)+本体の v2(`5ff1bacf…`)。後=作業木の src+組んだ資産 `data/world/v2_stage_2-4`(`6a7d34e8…`・`--world` で渡した)。比べ: [v1_vs_base.json](v1_vs_base.json)。
- **19/19 構成で final が動いた**。`frozen_sources` で動いたのは `process:w12_timetables.parquet` の 1 行だけ(`c548b2bb…` → `7ef7ab90…`)=1 日のランで動いた量はすべて W12 の時刻表から来る。W9 の窓の影(07-18・07-19)は 1 日・2 日・5 日(月〜金)のランでは読まない(07-13〜17 の影は前から本体の v2 にある)=**W9 の活性化は 6 日目(07-18)以降を回すランだけを動かす**。顕著行為 10・出動 5・暦の欄は 19/19 同じ。

| 構成 | 前 final / 呼数 | 後 final / 呼数 | 呼数の差 | 気づいた延べ | 食事 | 行動の件数 | blocks の行 | 動いた欄 |
|---|---|---|---|---|---|---|---|---|
| w6_v3_default | `5f7ae9ff24005314` / 65,597 | `4bcca9f0216362bb` / 65,400 | -197 | 237 → 302 | 4,559 → 4,400 | 291,935 → 296,016 | 7,975 → 8,157 | 16/25 |
| w6_v3_activity_off | `e0054a837c6ec4c1` / 50,301 | `dee82f1ebaa73ebe` / 50,155 | -146 | 719 → 471 | 3,342 → 3,360 | 173,688 → 174,152 | 2,660 → 2,698 | 16/25 |
| w6_v1_default | `24375ee3dab349e8` / 51,835 | `2c0e05968641f380` / 51,835 | +0 | 692 → 496 | 0 → 0 | 180,082 → 180,450 | 2,731 → 2,744 | 13/25 |
| w6_v1_derive_v2_1 | `59329a9a3611c16c` / 46,032 | `6c580488f3125d5e` / 45,572 | -460 | 570 → 539 | 0 → 0 | 166,461 → 165,704 | 2,461 → 2,427 | 15/25 |
| w6_v2 | `7e3a16b4190c10b5` / 52,268 | `72a0ab2e7829de5d` / 52,619 | +351 | 575 → 652 | 2,100 → 2,057 | 170,829 → 173,785 | 2,607 → 2,577 | 16/25 |
| w6_v1_edge | `0e0430daa24c109e` / 46,325 | `f471394fe28facbf` / 46,242 | -83 | 438 → 425 | 0 → 0 | 95,066 → 95,273 | 2,514 → 2,483 | 15/25 |
| w6_v2_edge | `8151c3ee812ef412` / 46,601 | `ef4ab573bb92b093` / 46,737 | +136 | 376 → 523 | 1,886 → 1,870 | 91,998 → 92,053 | 2,139 → 2,113 | 16/25 |
| w6_v1_edge_plateau | `a9d0c78a8e3bb079` / 47,912 | `8ff2b1e1097f805e` / 48,056 | +144 | 407 → 429 | 0 → 0 | 98,226 → 98,727 | 2,527 → 2,528 | 15/25 |
| w6_old_v1_default | `5f3665e29e8c55e1` / 51,835 | `5cb9041dded9bdf3` / 51,835 | +0 | 692 → 496 | 0 → 0 | 180,082 → 180,450 | 2,726 → 2,739 | 13/25 |
| w6_old_v1_derive_v2_1 | `f1ac9740ef2d04ca` / 46,032 | `78c8a8704e9a4ade` / 45,572 | -460 | 570 → 539 | 0 → 0 | 166,461 → 165,704 | 2,458 → 2,423 | 15/25 |
| w6_old_v2 | `24efbaa77c1ce701` / 52,268 | `1dcdf8ff51017bdf` / 52,619 | +351 | 575 → 652 | 2,100 → 2,057 | 170,829 → 173,785 | 2,603 → 2,574 | 16/25 |
| w6_old_v1_edge | `607b93b4cef8f716` / 46,325 | `825a96be442b8749` / 46,242 | -83 | 438 → 425 | 0 → 0 | 95,066 → 95,273 | 2,510 → 2,480 | 15/25 |
| w6_old_v2_edge | `c1056e6fda20f2c5` / 46,601 | `6c489a3b3b55defd` / 46,737 | +136 | 376 → 523 | 1,886 → 1,870 | 91,998 → 92,053 | 2,136 → 2,108 | 16/25 |
| w6_old_v1_edge_plateau | `8a15b93709c7ebdf` / 47,912 | `5ac11d74be30416e` / 48,056 | +144 | 407 → 429 | 0 → 0 | 98,226 → 98,727 | 2,524 → 2,525 | 15/25 |
| w6_golden_null_arm | `354f49ca9a61b986` / 97,234 | `767f0224d82ba9a9` / 98,046 | +812 | 563 → 2,572 | 0 → 0 | 290,189 → 289,960 | 3,939 → 3,937 | 15/25 |
| v3_mem_store | `f7ff0a6953fb9a38` / 65,597 | `452001a2517d7fb3` / 65,400 | -197 | 237 → 302 | 4,559 → 4,400 | 291,935 → 296,016 | 7,975 → 8,157 | 16/25 |
| v3_mem_rel | `73a78288ab5e1498` / 69,111 | `c506dec249bb4328` / 69,114 | +3 | 396 → 190 | 4,658 → 4,691 | 298,472 → 299,407 | 8,544 → 8,453 | 16/25 |
| v3_classical | `202a05a22c5bd8e1` / 93,460 | `f62a8d0ba0aa952f` / 93,685 | +225 | 901 → 903 | 9,298 → 9,314 | 433,042 → 434,083 | 8,566 → 8,449 | 16/25 |
| v3_classical_mem_rel | `4c512a1fdc2a70c0` / 106,565 | `18bd9bfea8f51c11` / 106,977 | +412 | 906 → 905 | 9,802 → 9,771 | 461,935 → 467,266 | 8,969 → 8,837 | 16/25 |
| 呼数の合計 | 1,129,811 | 1,130,899 | +1,088 | | | | | |

- 2-3b の記録 §9 の 4 構成(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel)の値と final・呼数が全部同じ(2-3b の資産と組み直した資産でエンジンの読むファイルが同じ)。
- **W12 の本数**(2-3b の golden=[tt23b](../tt23b/README.md) の末尾): 行 9,014 → **6,273**(平日 3,359・土休 2,914)・8 線とも実ダイヤ(等間隔の推定で残る線 0)・出どころ JR 1,883・東急 2,164・京王(チャレンジ枠)566・銀座線(オープン枠 9 月改正)665・メトロ 2 線(7 月の取得)995。
- **到着の波(2-0 の計器)**: `tools/instruments/anchor_gauge.py run --world data/world/v2_stage_2-4 --label 2026-10-14_vb24-V1 --compare …/2026-10-14_2bc7a4b` → [2026-10-14_vb24-V1/](../../../instruments/anchor_gauge/2026-10-14_vb24-V1/anchor_gauge.md)(比べ [compare_vs_2026-10-14_2bc7a4b.md](../../../instruments/anchor_gauge/2026-10-14_vb24-V1/compare_vs_2026-10-14_2bc7a4b.md))。mock `4bcca9f0216362bb`/65,400・classical `f62a8d0ba0aa952f`/93,685。要約の値 156 件のうち変わった 52 件(3-1 のピーク 1・3-2 の比 25・3-3 の割合 14 とピーク 7・3-4 の始業 5)=2-3b の記録 §9 の到着の波と同じ値(田園都市線・山手線のピーク 9 → 8 時台・東横線 8 → 9 時台・井の頭線 mock 7 → 8 時台)。合否は書かない(〔写〕の錨は構築の入力の写し)。
- manifest で動く欄: `frozen_sources`(W12 の 1 行・7 月 18・19 日を回すランでは W9 の影の行)。`bridges_version`・`rules_version` は V1 では動かない(つなぎの台帳と規則の表を変えていない)。

### V1-5 京王チャレンジ枠の切替口(仮-15 の確認まで京王の行を含めたまま)

- 既定 `USE_ODPT_CHALLENGE = True`=活性化した資産は京王の行(渋谷発 566 本)を含む。False で組み直すと井の頭線は等間隔の推定の行だけになり、ほかの 7 線の行(出どころと本数)と方面ノード・生成の重みは同じ(試験 `tests/build_field/test_w12_keio_switch_2_4.py`=data が要る 1 本で W12 を 2 回組んで確かめる)。ゲート `equal_interval_lines_remaining` は 1(FAIL=宣言どおり)・expedients に等間隔の道の 1 行(`EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS`=台帳 `EX-build.field.w12_external_nodes-f2cc7f0a`)。
- 切替口 False の資産は組んでいない(組むときは `activate_vb24.py stage` の前に定数を False にする=W12・W18〜W20 が動く)。

### V1-6 感度の台帳(C8)の作り直し

- 活性化で build_manifest の expedient が **123 → 126 行**(W12 8 → 11 行=等間隔の推定の 5 行=前の W12#4〜#8 が消え、実ダイヤの宣言 8 行=W12#4〜#11 が入る・W9 は 5 行のまま)。`tools/c8/sensitivity.py --manifest data/world/v2_stage_2-4/build_manifest.json` で `--judge-manifest → --read-graph → --triage → --d44` の順に作り直した(10e ACT-5 と同じ)。**同じ文言の 117 行は鍵を含め全欄が前と同じ**(突き合わせた)。
- 新しい 8 行の 3 分類と対照は実装役の案(**未リサーチ**・`tools/c8/expedient_triage_v1.json` の note に前の 4 行の値): W12#4 (ii)・#5 (i)・#6 (ii)・#7 (i)・#8 (iii)・#9 (i)・#10 (iii)・#11 (ii)。D-44 の列は未判定の印 `pending`(`D44_PENDING` に 8 行・(iii) の 2 行は今までどおり `no_control`)。
- `COVERED_EXPEDIENTS` から `("W12", "JR・東急・京王=等間隔ダイヤ", "S-W14-JRPHASE")` を外した(build_manifest に等間隔の行が無い)。S-W14-JRPHASE の台帳行は設計書の感度の行として残る(「対応行の無い台帳行」の一覧に出る・結果は 1.1.0 の時刻表で測った値のまま)。実資産でのこの対照の道具は「ずらす便 0」になる(試験を直した)。
- 集計: 判定不能 107 → **111**・読む 98 → **102**・3 分類 i 66 → 65 / ii 14 → 17 / iii 18 → 20・D-44 駆動しえない 38 → 35・ラン対照へ 25 → 24・測れない 12・対照を定義できない 18 → 20・対象外 9・未判定 5 → **11**。

### V1-7 試験

- 写しの木(`_bc/tree`=作業木のコードの写し+本体の data へのつなぎ・`data/world/v2` だけ組んだ資産へのハードリンク=10e ACT と同じ形。封印の錨 2 本は写さない)で全体(`-m "not slow and not gpu" -n 8 --dist loadfile --ignore=tests/c7`・18 分 35 秒): **4,845 passed・18 failed・23 errors・2 skipped・1 xfailed**。errors 23 は `tests/w17/test_diversity_yardstick.py`(写しの木に封印の錨 `diversity_anchors_v0.json` を写さなかったため=写しの木の都合・本体では回る)。failed 18 の行き先:
  - golden の張り替え(既定の資産が動いた所の固定)13 本+見張り 1 本=下の表(`tools/goldens_vb24.py all` で試験と同じ引数で値を集め、`tools/regold_vb24.py` で張り替え・行末に `# 〔2-4 V1〕前 <値>`)。
  - 感度の台帳 6 本(§V1-6 の前に写しの木を作ったため)→ 直して **193 passed**(`tests/c8`+活性化の試験+京王の切替口)。
  - `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(既知=`data` が本体への junction のためテープの道筋が相対にならない)。
- 張り替えた golden(前=本体の v2・後=活性化の資産):

| 試験のファイル | 構成(goldens_vb24 の名) | 前 | 後 |
|---|---|---|---|
| `tests/engine/test_state_ledger_10b.py` | pe_v3 | `5f7ae9ff24005314` | `4bcca9f0216362bb` |
| `tests/engine/test_state_checks_10f.py` | pe_v3 | `5f7ae9ff24005314` | `4bcca9f0216362bb` |
| `tests/engine/test_intent_chooser.py` | q13_v3 | `9bc6929fbb0da5e8` | `bff3eed45a39ea62` |
| `tests/engine/test_intent_chooser.py` | q13_v3 | `36_275` | `36_296` |
| `tests/engine/test_intent_chooser.py` | q13_null | `ce33abec7629c811` | `4679b0a6f6d2fa1e` |
| `tests/engine/proximity/test_runs.py` | prox_cell300 | `f0503a35ccb501aa…` | `f1ec0336ef617de0…` |
| `tests/engine/proximity/test_runs.py` | prox_cell300 | `3062` | `3_077` |
| `tests/perception/test_near_tiebreak.py` | nt_hash | `87492778f4582d8f…` | `26b748695ffbf7f9…` |
| `tests/perception/test_near_tiebreak.py` | nt_hash | `25_890` | `25_638` |
| `tests/perception/test_near_tiebreak.py` | nt_mid | `b7697fcafb4ba63b…` | `0dc35b774a45a23b…` |
| `tests/perception/test_near_tiebreak.py` | nt_mid | `25_828` | `25_653` |
| `tests/perception/test_near_tiebreak.py` | nt_old | `49c3fae02c2de5ec…` | `b5373e67f4122256…` |
| `tests/perception/test_near_tiebreak.py` | nt_old | `25_877` | `25_716` |
| `tests/engine/test_classical_social.py` | cs_acq | `78399f8cedec1c62…` | `faeacf8cff1f1fae…` |
| `tests/engine/test_classical_social.py` | cs_acq | `25_082` | `24_813` |
| `tests/engine/test_relations_tenure.py` | rel_v1 | `380e8651a96b1829` | `edc6b366feece21c` |
| `tests/engine/test_relations_tenure.py` | rel_v1 | `69_406` | `69_306` |
| `tests/engine/test_relations_tenure.py` | rel_v2 | `73a78288ab5e1498` | `c506dec249bb4328` |
| `tests/engine/test_relations_tenure.py` | rel_v2 | `69_111` | `69_114` |
| `tests/engine/test_env_and_sections_10f.py` | pe_v3 | `5f7ae9ff24005314` | `4bcca9f0216362bb` |
| `tests/engine/test_env_and_sections_10f.py` | pe_v3 | `65_597` | `65_400` |
| `tests/engine/test_env_and_sections_10f.py` | pe_null | `354f49ca9a61b986` | `767f0224d82ba9a9` |
| `tests/engine/test_env_and_sections_10f.py` | pe_null | `97_234` | `98_046` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v1 | `380e8651a96b1829` | `edc6b366feece21c` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v1 | `69_406` | `69_306` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v2 | `73a78288ab5e1498` | `c506dec249bb4328` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v2 | `69_111` | `69_114` |
| `tests/engine/test_presence_executor.py` | pe_null | `354f49ca9a61b986` | `767f0224d82ba9a9` |
| `tests/engine/test_presence_executor.py` | pe_null | `97_234` | `98_046` |
| `tests/engine/test_presence_executor.py` | pe_null_leave | `a33c00469ca28832` | `e88892cd271a638d` |
| `tests/engine/test_presence_executor.py` | pe_null_leave | `98_017` | `97_644` |
| `tests/engine/test_presence_executor.py` | pe_null_hv1 | `f655d1eb601d7bb4` | `4ced1f4211af5e5f` |
| `tests/engine/test_presence_executor.py` | pe_null_hv1 | `94_435` | `94_793` |
| `tests/engine/test_presence_executor.py` | pe_null_l4x1 | `f02d7fd4fbb4dc4f` | `d9e43bf14475a17c` |
| `tests/engine/test_presence_executor.py` | pe_v3 | `5f7ae9ff24005314` | `4bcca9f0216362bb` |
| `tests/engine/test_presence_executor.py` | pe_v3 | `65_597` | `65_400` |
| `tests/engine/test_presence_executor.py` | pe_v3_leave | `1761eef0e3c48dd5` | `53a0856c5fcc1c84` |
| `tests/engine/test_presence_executor.py` | pe_v3_leave | `65_634` | `65_735` |
| `tests/engine/test_presence_executor.py` | pe_v3_hv1 | `1767737a4183a436` | `20f96720567a5847` |
| `tests/engine/test_presence_executor.py` | pe_v3_hv1 | `64_977` | `65_019` |
| `tests/engine/test_presence_executor.py` | pe_v3_l4x1 | `a18594506e4a0ea5` | `1cc39b43dfc834ee` |
| `tests/engine/test_presence_executor.py` | pe_v3_l4x1 | `36_172` | `36_190` |

- 張り替えの後の確かめ(写しの木・`-m "not gpu"`=slow を含む・張り替えた 9 ファイル+`tests/c8`+新しい試験 2 ファイル): **403 passed**(6 分 20 秒)。K19 の slow(`test_state_checks_10f.py`)の final も V1 の値。
- 新しい試験: `tests/engine/test_activation_2_4.py`(3 本・本体の v2 を見る=**親が写すまで作業木と本体では落ちる**=10e ACT と同じ): build_hash が plan の後・W12 1.2.0 で残る線 0・W9 の 8 日の影とゲート PASS・窓の 7 日は暦の日付の影を読む。`tests/build_field/test_w12_keio_switch_2_4.py`(4 本・data 不要 3+data 1)。直した試験: `tests/build_field/test_field_pipeline.py`・`tests/build_vis/test_vis_pipeline.py`(現に落ちるゲートの表から W9 を外した)・`tests/build_audit/test_audit_pipeline.py`(W9 は落ちたゲートに無い・W10 は残る)・`tests/c8/test_sensitivity_ledger.py`(数・digest・実資産の位相の対照)・`tests/engine/bridging/test_bridging_ledger.py::test_build_stage_ids_are_the_c8_d44_row_ids`(活性化の後の C8 の表 126 行=有効な W の行 118 は同じ番号の行と、W12#4〜#11 は台帳の走査器の鍵の行 `EX-build.field.w12_external_nodes-*` と文で合う・前の W12#4〜#8 は removed。**V2 の作業中に見つけて直した**=V1 のスナップショットに後から足した)。

### V1-8 つなぎの台帳で外す段が 2-4 の行(本段では直していない=親が決める)

| 行 | 中身(短く) | 2-4 で何が起きたか・実装役の案 |
|---|---|---|
| `W9#5` | 影を作る日=定数 SHADOW_DATES | 活性化で窓の 7 日は本体の資産に入った。窓の外の日のつなぎは続く=外す段を「影を作る日を暦から決める段」に改める案(計画に段が無い=7) |
| `BR-SHADOW-NEAREST-DAY` | 影が無い日は近い日の影 | 同上(窓の外の日だけ・活性化で使う日は 07-20 以降) |
| `EX-build.field.w12_external_nodes-f2cc7f0a` | 等間隔ダイヤの道(切替口 False と実データの無い線) | 京王の切替口(V1)がこの道を使う=残す。外す段を仮-15 の確認の後に改める案 |
| `BR-PHONE-TABLE-BLANK` | 店の番号の表は空(W6 の POI に OSM の番号を足すのは版上げ 2 回目) | 本段の発注(V1〜V7)に入っていない=構築側の別の発注 |
| `DOC-ec21-*` 8 行 | 経済の段階 2 の宣言 | V4 で扱う(§V4) |
