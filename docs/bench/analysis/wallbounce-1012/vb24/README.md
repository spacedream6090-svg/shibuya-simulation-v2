# 第 2 期 2-4 版上げ 2 回目(vb24)の記録

> 実行役(Opus 5.5)の記録。親(Fable 5.1)が段ごとに V1 → V7 の順に commit した(V1 `be108b7` 〜 V7 `a231ef9`)。作業木の枝 `2-4/version-bump-2`(土台 HEAD `5f38e37`=2-1・2-2・2-3・2-3b・3-3 を含む・親が rebase した後の土台。実装は `9f631b0` の上で行い、`src`・`tests`・`tools` は rebase の前後で同じ=検収の記録 review.md の冒頭)。検収(条件つき受入)の後の直しは末尾の「検収の後の直し」。
> 正: [計画](../../../../design/v2-implementation-plan-2026-10-12.md) 第 2 期 2-4 の行(2-1・2-2・2-3b を束ねる・記憶の変更は入れない・動いた量を記録)・[10e の記録](../10e/README.md)(版上げ 1 回目の形=変更ごとに commit・19 構成の byte-check・ACT=資産の活性化・RET=切替口の削除)・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0(版上げは親が決め動いた量を記録・S6=GPU の実行は止まる地点=本段は mock だけ)・各段の記録([prox22](../prox22/README.md)・[ec21](../ec21/README.md)・[tt23b](../tt23b/README.md)・[md23](../md23/README.md)・[gauge20](../gauge20/README.md))。
> **入れないもの**: 記憶の変更(M1〜M5)・energy.py の第 18-1 表の置き換え(PENDING §1-1)・京王チャレンジ枠の扱いの変更(仮-15=確認が出るまで京王の行を含めたまま活性化し、戻せる切替口を残す)・W17 の勤務の時間の出どころ(2-1 の既定化は賃金の額が現実の 1/4 のまま=宣言)。
> 測った機械: Windows 11・x86-64・論理 CPU 20。byte-check は 19 構成・mock/classical 5,000 体・seed 1・1 シミュ日・テープつき([10e/byte_check_10e.py](../10e/byte_check_10e.py))。生の side・テープ・状態のファイルは作業木の `_bc/`(git の外=載せない)。本書には比べた結果と道具だけを置く。絶対パス・ホスト名・個人名は書かない。

## 0. 結論(段ごと)

- **V1 資産の活性化**: W12 1.2.0(8 線とも実ダイヤ・6,273 行)と W9 の影 7 日の窓を 1 つの資産に組み直した(`data/world/v2_stage_2-4`・build_hash `5ff1bacf…` → `6a7d34e8…`・2 回組んで一致・置き換え 11 本・足す 3 本・同じ 93 本)。**本体の `data/world/v2` への写しは親が実行した**(2026-10-14・道具 `activate_vb24.py` の `apply`・退避 `data/world/v2_pre_2-4`・`verify` 同じ)。19/19 構成で final が動いた。原因は全部 W12 の時刻表で、呼数の合計は +1,088。W9 の 10 MB/日のゲートは案 A(宣言を 13 MB/日に)を仮に入れた(親が決める)。京王の行は切替口 `USE_ODPT_CHALLENGE`(既定 True)で戻せる。C8 の感度の台帳を作り直した(W12 の 8 行)。
- **V2 近接 distance を既定に**: 18/19 構成で final が動いた(`v3_classical` はプロンプトの列だけ)。呼数の合計は −10,046(−0.9%)。切替口 `--proximity cell` で V1 の値が 25 欄とも再現した(4 構成)。直したもの: 体の層をセルから導く(2-2 の distance の道は派生の列 `agents.band`=軸 1 no を読んでいて、既定にすると状態台帳の試験 T5 が落ちた・直した後も 19 構成で 25 欄とも同じ)。11c の読み直しの既定の列・B5 の単位の在室人数・再開=通しを記録した。
- **V3 在席の印を歩き出しで解く**: 15/19 構成で final が動いた。呼数の合計は −2,266。店のセルの外にいる在席の体 × 刻みは 4.36% → 1.91%。残りの 88% は乗車へ向かう体で、`_apply_move` の範囲の外(親が決める)。切替口 `--seat-release legacy` で V2 の値が 19/19 構成で再現した。
- **V4 経済の段階 2 を既定 on に**: 部品 5 つ全部を on にした。19/19 構成で final が動いた(呼数は 13 構成で同じ・合計 −40)。輪の係数は 16.0 行/体/日で、予算の宣言を 246,522,344 B=約 246.5 MB(M8 の約 1.0%)に改めた。`pois.revenue` は税抜きにし、`DOC-ec21-revenue-tax-inclusive` を removed にした。2 日のランは残差 0・溢れ 0。世帯の現金の 1 体の増減は −1,606・−1,173 → −734・−438 円/日。切替口 `--economy-stage2 off` で V3 の値が再現した(4 構成)。再開=通しも確かめた。再開の腕の検査は「効いている腕」で見る形に直した(台帳なしのランの再開が止まったため)。
- **V5 計器の節**: `group_norms.cost.ticks` を観測の節に移した。結果は 19/19 構成で 25 欄とも不変。`CONFIG_PATHS_SHA256` は `417f0818…`。
- **V6 錨のファイルの分離**: 値を読まずに、鍵の名で 4 本に分けた(在圏は較正側と検証側・空腹は構築側と検証側)。結果は 19/19 構成で 25 欄とも不変。manifest で動くのは `energy.anchors`・`anchors_md5` だけ。エンジンは今も空腹の検証側のファイルを読む(第 18-1 表・PENDING §1-1)。
- **V7 切替口**: 一覧だけ作った(残す 5・消す候補 10 行・消していない)。
- **合計**: 呼数は 1,129,811 → 1,118,547(−1.0%)。試験は写しの木で全体(not slow)が 4,871 passed・1 failed(既知の junction の ab7)。slow は 86 passed・1 failed(性能の試験 P6=10 並列の負荷・単独で回し直して通る=§締め-2)。`tests/c7` は回していない。**親が活性化した**(2026-10-14・`activate_vb24.py apply`・退避 `data/world/v2_pre_2-4`・`verify` 同じ=build_hash `6a7d34e8…`)。活性化の後は、活性化の golden と `tests/engine/test_activation_2_4.py` は通る(検収役と実装役が確かめた)。

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

- **親が実行する手順**(リポの根・作業木の src を `PYTHONPATH` に・〔検収の後〕親が 2026-10-14 に `apply` → `verify` 同じ=build_hash `6a7d34e8…`):

  ```
  T=docs/bench/analysis/wallbounce-1012/vb24/tools/activate_vb24.py
  python $T apply --dry-run          # 前提の確かめ(本体の v2 が plan の「前」と同じ・steps の sha256・退避先が空)と写す一覧
  python $T apply                    # 置き換える 11 本を data/world/v2_pre_2-4/ へ退避(MANIFEST.sha256・plan.json)→ 14 本を写す
                                     # → 写した全部の sha256 と build_hash 6a7d34e8… を確かめる(違えば終了コード 3=revert で戻せる)
  python $T verify --want after      # いつでも: 本体の v2 が活性化の後と同じか
  python $T revert                   # 戻す: 退避した 11 本を写し戻し・足した 3 本を消し・build_hash 5ff1bacf… を確かめる
  python $T materialize --out <置き場> # 〔検収 M1〕前の資産を置き場に組む(本体の v2 と退避は読むだけ)
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
- 新しい試験: `tests/engine/test_activation_2_4.py`(3 本・本体の v2 を見る=**親が写すまで作業木と本体では落ちる**=10e ACT と同じ・〔検収の後〕親が写した後は通る・合成の置き場の `materialize` の 3 本を足した=末尾の「検収の後の直し」): build_hash が plan の後・W12 1.2.0 で残る線 0・W9 の 8 日の影とゲート PASS・窓の 7 日は暦の日付の影を読む。`tests/build_field/test_w12_keio_switch_2_4.py`(4 本・data 不要 3+data 1)。直した試験: `tests/build_field/test_field_pipeline.py`・`tests/build_vis/test_vis_pipeline.py`(現に落ちるゲートの表から W9 を外した)・`tests/build_audit/test_audit_pipeline.py`(W9 は落ちたゲートに無い・W10 は残る)・`tests/c8/test_sensitivity_ledger.py`(数・digest・実資産の位相の対照)・`tests/engine/bridging/test_bridging_ledger.py::test_build_stage_ids_are_the_c8_d44_row_ids`(活性化の後の C8 の表 126 行=有効な W の行 118 は同じ番号の行と、W12#4〜#11 は台帳の走査器の鍵の行 `EX-build.field.w12_external_nodes-*` と文で合う・前の W12#4〜#8 は removed。**V2 の作業中に見つけて直した**=V1 のスナップショットに後から足した)。

### V1-8 つなぎの台帳で外す段が 2-4 の行(本段では直していない=親が決める・〔検収の後〕親の判断で改めた=末尾の「検収の後の直し」)

| 行 | 中身(短く) | 2-4 で何が起きたか・実装役の案 |
|---|---|---|
| `W9#5` | 影を作る日=定数 SHADOW_DATES | 活性化で窓の 7 日は本体の資産に入った。窓の外の日のつなぎは続く=外す段を「影を作る日を暦から決める段」に改める案(計画に段が無い=7) |
| `BR-SHADOW-NEAREST-DAY` | 影が無い日は近い日の影 | 同上(窓の外の日だけ・活性化で使う日は 07-20 以降) |
| `EX-build.field.w12_external_nodes-f2cc7f0a` | 等間隔ダイヤの道(切替口 False と実データの無い線) | 京王の切替口(V1)がこの道を使う=残す。外す段を仮-15 の確認の後に改める案 |
| `BR-PHONE-TABLE-BLANK` | 店の番号の表は空(W6 の POI に OSM の番号を足すのは版上げ 2 回目) | 本段の発注(V1〜V7)に入っていない=構築側の別の発注 |
| `DOC-ec21-*` 8 行 | 経済の段階 2 の宣言 | V4 で扱う(§V4) |

## V2 近接 distance を既定に(`--proximity` の既定 cell → distance・d=2.0 m)

### V2-1 変えたこと

| ファイル | 何を |
|---|---|
| `src/shibuya/engine/proximity.py` | `DEFAULT_MODE = MODE_DISTANCE`(10-03 §4 の決定=11a を版上げ 2 回目で既定に)・環境変数 `SHIBUYA_PROXIMITY` の既定を `DEFAULT_MODE` に・docstring。`cell` は**切替口**(2-2 までの判定=旧値の再現)。manifest の `proximity.schema` は上げていない(欄の意味は同じ) |
| `src/shibuya/cli.py` | ランの種類の決め方を「近接の腕が既定(distance)と違えば腕」に(前は cell と違えば腕)・`--proximity` の説明 |
| `src/shibuya/engine/systems/{build,act,boxes,judge,talk}.py`・`engine/state_ledger.py` | 既定の記述の注 |
| `src/shibuya/engine/proximity.py`・`src/shibuya/perception/renderer.py`・`engine/systems/build.py`・`engine/state_ledger.py` | **体の層をセルから導く**(§V2-5 の T5 の発見): 規則に `cell_band`(`world.assets.cell_band` の読むだけの写し・`rule_from(cell_band=…)`)を足し、`_bands` は `cell_band[agents.cell]`(舞台の外は 0)を返す・描画の B5 の近接行の自分の層も同じ。SoA の派生の列 `agents.band`(軸 1 no)を既定のランで読まない。`node_band[n] == cell_band[node_cell[n]]` は資産(3,499 ノード)と合成の世界で全部一致=**値は同じ**(19 構成で 25 欄とも同じ=[v2fix_vs_v2.json](v2fix_vs_v2.json))。状態台帳の `agents.band` の読みの許可から描画の 1 本を消した(残るのは誤検出 1 と、`cell_band` を持たない試験の合成の規則の道) |
| 試験 | §V2-5 |

- 状態のファイルの見出し: 既定のランは見出しに `proximity`(`mode=distance`・`d_m=2.0`)を書く。見出しに無い状態のファイル=2-4 より前の既定(cell)のラン=今の既定で再開すると止まる(2-2 の検収 M1 の守り=腕の違う再開を止める)。

### V2-2 動いた量(19 構成・前=V1・後=V2・どちらも作業木の src と組んだ資産)

比べ: [v2_vs_v1.json](v2_vs_v1.json)。**18/19 構成で final が動いた**。`frozen_sources`・暦・顕著行為 10・出動 5 は 19/19 同じ。

| 構成 | 前 final / 呼数 | 後 final / 呼数 | 呼数の差 | 気づいた延べ | 食事 | 行動の件数 | blocks の行 | 動いた欄 |
|---|---|---|---|---|---|---|---|---|
| w6_v3_default | `4bcca9f0216362bb` / 65,400 | `7857ecb16b9665cd` / 64,635 | -765 | 302 → 534 | 4,400 → 4,365 | 296,016 → 295,235 | 8,157 → 7,826 | 15/25 |
| w6_v3_activity_off | `dee82f1ebaa73ebe` / 50,155 | `736915ca953a1aab` / 50,397 | +242 | 471 → 774 | 3,360 → 3,303 | 174,152 → 174,047 | 2,698 → 2,462 | 15/25 |
| w6_v1_default | `2c0e05968641f380` / 51,835 | `2d327566a182139d` / 51,655 | -180 | 496 → 620 | 0 → 0 | 180,450 → 183,345 | 2,744 → 2,442 | 14/25 |
| w6_v1_derive_v2_1 | `6c580488f3125d5e` / 45,572 | `317e9dd18767373c` / 44,807 | -765 | 539 → 741 | 0 → 0 | 165,704 → 162,504 | 2,427 → 2,162 | 14/25 |
| w6_v2 | `72a0ab2e7829de5d` / 52,619 | `de90869e494390c3` / 51,366 | -1,253 | 652 → 712 | 2,057 → 2,039 | 173,785 → 169,661 | 2,577 → 2,323 | 15/25 |
| w6_v1_edge | `f471394fe28facbf` / 46,242 | `1b6b9ecf75a741f9` / 46,054 | -188 | 425 → 546 | 0 → 0 | 95,273 → 94,791 | 2,483 → 2,287 | 14/25 |
| w6_v2_edge | `ef4ab573bb92b093` / 46,737 | `62178a0e488bc989` / 46,655 | -82 | 523 → 482 | 1,870 → 1,869 | 92,053 → 91,383 | 2,113 → 2,173 | 15/25 |
| w6_v1_edge_plateau | `8ff2b1e1097f805e` / 48,056 | `cc4eb08c30b1ed31` / 47,871 | -185 | 429 → 468 | 0 → 0 | 98,727 → 98,038 | 2,528 → 2,331 | 14/25 |
| w6_old_v1_default | `5cb9041dded9bdf3` / 51,835 | `71d0e6720220f45a` / 51,655 | -180 | 496 → 620 | 0 → 0 | 180,450 → 183,345 | 2,739 → 2,438 | 14/25 |
| w6_old_v1_derive_v2_1 | `78c8a8704e9a4ade` / 45,572 | `34c53e6e19f7d6f2` / 44,807 | -765 | 539 → 741 | 0 → 0 | 165,704 → 162,504 | 2,423 → 2,158 | 14/25 |
| w6_old_v2 | `1dcdf8ff51017bdf` / 52,619 | `22931e874d600ab1` / 51,366 | -1,253 | 652 → 712 | 2,057 → 2,039 | 173,785 → 169,661 | 2,574 → 2,319 | 15/25 |
| w6_old_v1_edge | `825a96be442b8749` / 46,242 | `32773d86549a11c1` / 46,054 | -188 | 425 → 546 | 0 → 0 | 95,273 → 94,791 | 2,480 → 2,281 | 14/25 |
| w6_old_v2_edge | `6c489a3b3b55defd` / 46,737 | `f24c502e520f426a` / 46,655 | -82 | 523 → 482 | 1,870 → 1,869 | 92,053 → 91,383 | 2,108 → 2,170 | 15/25 |
| w6_old_v1_edge_plateau | `5ac11d74be30416e` / 48,056 | `3a04d3f798004d4d` / 47,871 | -185 | 429 → 468 | 0 → 0 | 98,727 → 98,038 | 2,525 → 2,327 | 14/25 |
| w6_golden_null_arm | `767f0224d82ba9a9` / 98,046 | `d341ca5c9e3e89d3` / 96,797 | -1,249 | 2,572 → 1,299 | 0 → 0 | 289,960 → 287,854 | 3,937 → 3,481 | 14/25 |
| v3_mem_store | `452001a2517d7fb3` / 65,400 | `1dd3e329443349eb` / 64,635 | -765 | 302 → 534 | 4,400 → 4,365 | 296,016 → 295,235 | 8,157 → 7,826 | 15/25 |
| v3_mem_rel | `c506dec249bb4328` / 69,114 | `874ea26628f6be2e` / 68,213 | -901 | 190 → 375 | 4,691 → 4,603 | 299,407 → 299,366 | 8,453 → 8,036 | 15/25 |
| v3_classical | `f62a8d0ba0aa952f` / 93,685 | `f62a8d0ba0aa952f` / 93,685 | +0 | 903 → 903 | 9,314 → 9,314 | 434,083 → 434,083 | 8,449 → 8,449 | 1/25 |
| v3_classical_mem_rel | `18bd9bfea8f51c11` / 106,977 | `059461c683d135c7` / 105,675 | -1,302 | 905 → 914 | 9,771 → 9,851 | 467,266 → 466,399 | 8,837 → 8,864 | 15/25 |
| 呼数の合計 | 1,130,899 | 1,120,853 | -10,046 | | | | | |

- `v3_classical`(古典・記憶 off・関係 off)だけは final・呼数・行動・blocks が同じで、テープの `prompt_hash` と `tokens_in` の列だけ動いた(B5 の近接行の描画が distance の道=半径 10.3 m・B5 の単位になる。古典の方策は描画の文を選択に使わず、関係 off で知人の会話も無い)。
- 動く理由(2-2 の記録 §2-1 のとおり): 会話の開始・返事待ち・3 人会話・離脱・招待の相手・偶然の出会い・同席・B5 の近接行が「同じ層・距離 ≤ 2 m か同じ B5 の単位(在席の印 ∧ 店のセルの中)」になる・知人出現の起床が気づく確率 p(d) の抽選になる。会話の起床の呼が減り(2-2 の記録 §14-4 と同じ向き)、呼数の合計は −10,046(−0.9%)。

### V2-3 切替口 cell で V1 の値が再現する(4 構成)

`SHIBUYA_PROXIMITY=cell` で V2 の src を回した 4 構成(w6_v3_default・w6_v1_default・v3_mem_rel・v3_classical_mem_rel)は **V1 と 25 欄とも同じ**(final・呼数・テープの列・行動・blocks・full-hash ほか)=[v2cell_vs_v1.json](v2cell_vs_v1.json)。

### V2-4 11c の読み直しの既定の列・B5 の単位の在室人数・再開

- 11c の計器(2-2 の道具 [prox22/tools/reread_11c.py](../prox22/tools/reread_11c.py) をそのまま・活性化の資産 `--world data/world/v2_stage_2-4`・5,000 体・層化抽出・seed 1・語彙 v3・記憶 on・1 日・node 幾何)を、**既定の列=distance**・切替口の列=cell で回した=[v2_reread_11c.json](v2_reread_11c.json)(2-2 の記録の表は「既定 cell/腕 distance」の並び=列の役が入れ替わった)。

| 量 | distance/node mock | distance/node classical | cell/node mock | cell/node classical |
|---|---|---|---|---|
| 会話の成立時の距離が 2 m 超の割合(関係 on) | 0.0299 | 0.0088 | 0.4116 | 0.4029 |
| 同・10 m 超の割合(関係 on) | 0.0249 | 0.0059 | 0.2957 | 0.3395 |
| 同・最大[m](関係 on) | 80.83 | 31.36 | 92.96 | 119.9 |
| 会話のセッション(関係 off / on) | 155 / 201 | 0 / 341 | 211 / 328 | 0 / 489 |
| 知人出現の起床の呼(関係 on) | 9,593 | 35,232 | 10,953 | 38,867 |
| 知人出現の時点の距離の中央値[m](関係 on) | 2.154 | 0 | 28 | 28.25 |
| B5 の近接行の項/描画(関係 on) | 2.79 | 5.01 | 3.207 | 6.021 |
| B5 の近接行の 2 m 内の割合(関係 on) | 0.9417 | 0.9327 | 0.7975 | 0.7118 |
| B5 の近接行の 10 m 超の割合(関係 on) | 0.005 | 0.0024 | 0.1508 | 0.2384 |
| B5 の単位の在室人数の最大(絞った単位・関係 on) | 30 | 30 | 30 | 30 |
| 同・絞る前の在席の印の最大(関係 on) | 30 | 30 | 30 | 30 |
| 在席の体 × 刻みのうち店のセルの外(関係 on) | 11,171 | 44,556 | 12,772 | 44,269 |
| 同じ点に重なる体の最大(関係 on) | 184 | 467 | 172 | 461 |

- **再開=通し**(5,000 体・2 日・1 日目の終わりで保存 → 2 日目を再開・[tools/resume_vb24.py](tools/resume_vb24.py)・腕は今の既定=distance): v3_mem_rel `c1629175f053dbf0`(145,931 呼)・w6_v3_default `7330047ab379ec19`(139,311 呼)とも **final と日の境目の後の checkpoint 4 点(behavior/full)が通しと同じ**=[v2_resume_v3_mem_rel.json](v2_resume_v3_mem_rel.json)・[v2_resume_w6_v3_default.json](v2_resume_w6_v3_default.json)。
- **費用(P4)**: 既定のランは毎刻み近傍の索引を作り、関係 on では辺の見え方と気づく抽選を引く(2-2 の記録 §6・§14-1)。予算の宣言への追記案(親が書く=2-2 の記録 §10 の 10): 「近接の判定(既定 distance・39 万体・刻みあたり・上側): 索引 ≤ 90 ms+関係辺の集め ≤ 0.17 s+辺の見え方 ≤ 0.20 s+気づく抽選 27〜30 ms(配列)+開いている会話 1 つあたり 0.01 ms+描画 1 回あたり +0.03〜0.08 ms。切替口 cell は 0」。5,000 体・1 日の壁時計は §V2-2 の side で cell に対して(参考・同居のランあり=決定論でない)。

### V2-5 試験

- 写しの木で全体: `-m "not slow and not gpu" -n 8 --dist loadfile --ignore=tests/c7`(`tests/w17/test_diversity_yardstick.py` は写しの木に封印の錨を写さないので外した=§V1-7)= **4,854 passed・7 failed・2 skipped・1 xfailed**(13 分 44 秒)。落ちた 7 本=T5 の 3 本(下の発見)・C9b の既定の診断 2 本・T1 の合成の final 1 本・既知の junction の 1 本(ab7)。直した後に関係する 10 ファイルを写しの木で回し直した(`-m "not gpu"`=slow を含む・V3 の作業木なので在席の切替口 legacy で V2 と同じ挙動=§V2-1 の 19 構成の一致で確かめた): **393 passed・1 skipped**(4 分 43 秒・`CONFIG_PATHS_SHA256` の 1 本は V3 の設定の道筋で落ちる=V3 で直す)
- 張り替えた golden(V1 → V2)=下の表。`tests/engine/proximity/test_runs.py` の `HEAD_GOLDEN`(腕 cell を明示)と `tests/engine/test_classical_social.py`(古典・関係 off)は動かない。

| 試験のファイル | 構成(goldens_vb24 の名) | 前 | 後 |
|---|---|---|---|
| `tests/engine/test_presence_executor.py` | pe_null | `767f0224d82ba9a9` | `d341ca5c9e3e89d3` |
| `tests/engine/test_presence_executor.py` | pe_null | `98_046` | `96_797` |
| `tests/engine/test_presence_executor.py` | pe_null_leave | `e88892cd271a638d` | `62c0de517b1689ec` |
| `tests/engine/test_presence_executor.py` | pe_null_leave | `97_644` | `97_690` |
| `tests/engine/test_presence_executor.py` | pe_null_hv1 | `4ced1f4211af5e5f` | `eff11abb4169f319` |
| `tests/engine/test_presence_executor.py` | pe_null_hv1 | `94_793` | `94_030` |
| `tests/engine/test_presence_executor.py` | pe_null_l4x1 | `d9e43bf14475a17c` | `23d6397b39afb614` |
| `tests/engine/test_presence_executor.py` | pe_null_l4x1 | `40_979` | `40_976` |
| `tests/engine/test_presence_executor.py` | pe_v3 | `4bcca9f0216362bb` | `7857ecb16b9665cd` |
| `tests/engine/test_presence_executor.py` | pe_v3 | `65_400` | `64_635` |
| `tests/engine/test_presence_executor.py` | pe_v3_leave | `53a0856c5fcc1c84` | `210747ea9fa71919` |
| `tests/engine/test_presence_executor.py` | pe_v3_leave | `65_735` | `64_704` |
| `tests/engine/test_presence_executor.py` | pe_v3_hv1 | `20f96720567a5847` | `62c5ea236fe4271d` |
| `tests/engine/test_presence_executor.py` | pe_v3_hv1 | `65_019` | `64_268` |
| `tests/engine/test_presence_executor.py` | pe_v3_l4x1 | `1cc39b43dfc834ee` | `b2a1acae57abca9e` |
| `tests/engine/test_presence_executor.py` | pe_v3_l4x1 | `36_190` | `36_239` |
| `tests/engine/test_state_ledger_10b.py` | pe_v3 | `4bcca9f0216362bb` | `7857ecb16b9665cd` |
| `tests/engine/test_state_checks_10f.py` | pe_v3 | `4bcca9f0216362bb` | `7857ecb16b9665cd` |
| `tests/engine/test_intent_chooser.py` | q13_v3 | `bff3eed45a39ea62` | `6d0ad8b13125ea5a` |
| `tests/engine/test_intent_chooser.py` | q13_v3 | `36_296` | `36_246` |
| `tests/engine/test_intent_chooser.py` | q13_null | `4679b0a6f6d2fa1e` | `319e347ffe08946b` |
| `tests/engine/test_intent_chooser.py` | q13_null | `40_963` | `40_957` |
| `tests/perception/test_near_tiebreak.py` | nt_hash | `26b748695ffbf7f9…` | `e313dfaace60e425…` |
| `tests/perception/test_near_tiebreak.py` | nt_hash | `25_638` | `25_363` |
| `tests/perception/test_near_tiebreak.py` | nt_mid | `0dc35b774a45a23b…` | `348df7c410fca9ec…` |
| `tests/perception/test_near_tiebreak.py` | nt_mid | `25_653` | `25_297` |
| `tests/perception/test_near_tiebreak.py` | nt_old | `b5373e67f4122256…` | `aaf28867cc84660d…` |
| `tests/perception/test_near_tiebreak.py` | nt_old | `25_716` | `25_335` |
| `tests/engine/test_relations_tenure.py` | rel_v1 | `edc6b366feece21c` | `967a0f2eedb3576d` |
| `tests/engine/test_relations_tenure.py` | rel_v1 | `69_306` | `67_907` |
| `tests/engine/test_relations_tenure.py` | rel_v2 | `c506dec249bb4328` | `874ea26628f6be2e` |
| `tests/engine/test_relations_tenure.py` | rel_v2 | `69_114` | `68_213` |
| `tests/engine/test_env_and_sections_10f.py` | pe_v3 | `4bcca9f0216362bb` | `7857ecb16b9665cd` |
| `tests/engine/test_env_and_sections_10f.py` | pe_v3 | `65_400` | `64_635` |
| `tests/engine/test_env_and_sections_10f.py` | pe_null | `767f0224d82ba9a9` | `d341ca5c9e3e89d3` |
| `tests/engine/test_env_and_sections_10f.py` | pe_null | `98_046` | `96_797` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v1 | `edc6b366feece21c` | `967a0f2eedb3576d` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v1 | `69_306` | `67_907` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v2 | `c506dec249bb4328` | `874ea26628f6be2e` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v2 | `69_114` | `68_213` |

- **見つけたこと(T5)**: 状態台帳の試験 T5(軸 1 が no の列を刻みの頭で揺らしても挙動は動かない・`tests/engine/test_state_ledger_10b.py`)が、既定を distance にすると落ちた(合成の世界の all_arms・classical と実資産 300 体の 3 本)。近接の判定と描画が `agents.band`(セルの層から導く派生の列=軸 1 no・2-2 では「既定の腕 cell では読まない」という読みの許可つき)を読むため。直し方は列を behavior にする(behavior-hash が動く)のではなく、読み手を behavior の列 `agents.cell` から導く形に替えた(上の表・値は同じ)。直した後は T5 の 4 本とも通る。
- 直した試験(既定の約束を書いた試験): `tests/engine/test_c9b_targets_attention.py::test_default_arms_have_no_attention_columns_and_no_new_counters`(`n_talk_by_distance` は近接の腕の実距離の成立も数える=C9b の診断が立たないことは切替口 cell で見る)・`tests/engine/test_state_ledger_10b.py`(T1 の今の既定の final `CUR_SYN["all_arms"]` `ab8201f624b4dfa7` → `9071edfd618d42d8`・読みの許可の数 3 → 2)・`tests/perception/facts/test_render_from_percept_bytes.py` の (B)(19 構成の描画を HEAD `136fdbb` の描画の写しと比べる=写しは distance の道を持たない=切替口 cell で比べる・前と同じ比べ)。`tests/engine/bridging/test_bridging_ledger.py::test_build_stage_ids_are_the_c8_d44_row_ids`(**V1 の直し**=活性化の後の C8 の表 126 行・W12#4〜#11 は台帳の EX の行と文で合う・前の W12#4〜#8 は removed)。

## V3 在席の印を歩き出しで解く(`resolve._apply_move`・切替口 `--seat-release legacy`)

### V3-1 変えたこと

| ファイル | 何を |
|---|---|
| `src/shibuya/engine/seat_release.py`(新) | 腕 `--seat-release {walk,legacy}`(環境変数 `SHIBUYA_SEAT_RELEASE`・既定 **walk**=`DEFAULT_MODE`)・`header_fields`・`check_resume`(近接・経済の段階 2 の腕と同じ形=設定の指紋に入れず、状態のファイルの見出しで再開の腕を突き合わせる) |
| `src/shibuya/engine/resolve.py` | `apply(…, seat_release_walk=False)`・`ResolveOutcome.seat_release_walk`・`n_seat_released_walk`。`_apply_move` で**歩き出した体**(行き先のノードへ向かう=`MOVING`)の `poi_ref`/`poi_since` を −1 に(到着済み=行き先のノードに居る体・行けない体・移動しない体は解かない)。`apply` の既定は False(直に呼ぶ試験・切替口 legacy=2-4 より前の挙動) |
| `src/shibuya/engine/systems/{boxes,build,act,report,state_io}.py` | `RunConfig.seat_release`(組み立てで 1 回読む)・`act` が `apply` へ渡す・解いた数を `leave_counts` に積む・manifest の `leave_effects` に `seat_release`(設定)と `released_on_walk`(観測)・状態のファイルの見出しに `seat_release`(walk のランだけ)・再開の検査 |
| `src/shibuya/engine/manifest_sections.py` | `leave_effects` の設定に `seat_release`・観測に `released_on_walk`(=`CONFIG_PATHS_SHA256` が動く) |
| `src/shibuya/cli.py` | `--seat-release`・ランの種類は既定(walk)と違えば腕 |
| `tests/engine/test_seat_release_2_4.py`(新) | 7 本(§V3-5) |

- 席の数え方: `crowd` の在室の数は刻みごとに `poi_ref` の `bincount` で数え直す=歩き出しで解いた席は次の刻みから空く(退去の `release_indoor` と同じ)。
- 範囲は発注どおり `_apply_move` だけ。就寝の帰り道(`_apply_sleep` の歩き出し)・乗車の意図でホームへ歩く体(`_apply_board` と計画の出口の乗車=乗った時に解く)は今のまま(§V3-3 に残りの数)。

### V3-2 動いた量(19 構成・前=V2・後=V3)

比べ: [v3_vs_v2.json](v3_vs_v2.json)。**15/19 構成で final が動いた**(語彙 v1 の 2 構成=w6_v1_default・w6_old_v1_default は 25 欄とも同じ・w6_v1_derive_v2_1・w6_old_v1_derive_v2_1 はテープの列の sha の 1 欄だけ)。`frozen_sources`・暦・顕著行為・出動は 19/19 同じ。

| 構成 | 前 final / 呼数 | 後 final / 呼数 | 呼数の差 | 気づいた延べ | 食事 | 行動の件数 | blocks の行 | 動いた欄 |
|---|---|---|---|---|---|---|---|---|
| w6_v3_default | `7857ecb16b9665cd` / 64,635 | `f6488d4d5eadf5ca` / 64,526 | -109 | 534 → 332 | 4,365 → 4,447 | 295,235 → 295,063 | 7,826 → 7,657 | 15/25 |
| w6_v3_activity_off | `736915ca953a1aab` / 50,397 | `35cc3ce57f604a0c` / 50,033 | -364 | 774 → 802 | 3,303 → 3,294 | 174,047 → 172,664 | 2,462 → 2,441 | 15/25 |
| w6_v1_default | `2d327566a182139d` / 51,655 | `2d327566a182139d` / 51,655 | +0 | 620 → 620 | 0 → 0 | 183,345 → 183,345 | 2,442 → 2,442 | 0/25 |
| w6_v1_derive_v2_1 | `317e9dd18767373c` / 44,807 | `317e9dd18767373c` / 44,807 | +0 | 741 → 741 | 0 → 0 | 162,504 → 162,504 | 2,162 → 2,162 | 1/25 |
| w6_v2 | `de90869e494390c3` / 51,366 | `1698f1b7cddc92dd` / 51,266 | -100 | 712 → 406 | 2,039 → 2,052 | 169,661 → 170,110 | 2,323 → 2,309 | 15/25 |
| w6_v1_edge | `1b6b9ecf75a741f9` / 46,054 | `5ed1bb6f37bf1b68` / 46,054 | +0 | 546 → 546 | 0 → 0 | 94,791 → 94,791 | 2,287 → 2,287 | 4/25 |
| w6_v2_edge | `62178a0e488bc989` / 46,655 | `9f89b1a7be01ac12` / 46,655 | +0 | 482 → 482 | 1,869 → 1,870 | 91,383 → 91,383 | 2,173 → 2,173 | 8/25 |
| w6_v1_edge_plateau | `cc4eb08c30b1ed31` / 47,871 | `c13ff90acb300aae` / 47,871 | +0 | 468 → 468 | 0 → 0 | 98,038 → 98,038 | 2,331 → 2,331 | 4/25 |
| w6_old_v1_default | `71d0e6720220f45a` / 51,655 | `71d0e6720220f45a` / 51,655 | +0 | 620 → 620 | 0 → 0 | 183,345 → 183,345 | 2,438 → 2,438 | 0/25 |
| w6_old_v1_derive_v2_1 | `34c53e6e19f7d6f2` / 44,807 | `34c53e6e19f7d6f2` / 44,807 | +0 | 741 → 741 | 0 → 0 | 162,504 → 162,504 | 2,158 → 2,158 | 1/25 |
| w6_old_v2 | `22931e874d600ab1` / 51,366 | `c0788c5c8a3f4f3f` / 51,266 | -100 | 712 → 406 | 2,039 → 2,052 | 169,661 → 170,110 | 2,319 → 2,306 | 15/25 |
| w6_old_v1_edge | `32773d86549a11c1` / 46,054 | `1d15972ddcc39130` / 46,054 | +0 | 546 → 546 | 0 → 0 | 94,791 → 94,791 | 2,281 → 2,281 | 4/25 |
| w6_old_v2_edge | `f24c502e520f426a` / 46,655 | `47f422bfb758e934` / 46,655 | +0 | 482 → 482 | 1,869 → 1,870 | 91,383 → 91,383 | 2,170 → 2,170 | 8/25 |
| w6_old_v1_edge_plateau | `3a04d3f798004d4d` / 47,871 | `780236fe3706f4f1` / 47,871 | +0 | 468 → 468 | 0 → 0 | 98,038 → 98,038 | 2,327 → 2,327 | 4/25 |
| w6_golden_null_arm | `d341ca5c9e3e89d3` / 96,797 | `5c8db46f50eb0945` / 96,695 | -102 | 1,299 → 1,293 | 0 → 0 | 287,854 → 289,561 | 3,481 → 3,428 | 14/25 |
| v3_mem_store | `1dd3e329443349eb` / 64,635 | `017e0f95bf0c5685` / 64,526 | -109 | 534 → 332 | 4,365 → 4,447 | 295,235 → 295,063 | 7,826 → 7,657 | 15/25 |
| v3_mem_rel | `874ea26628f6be2e` / 68,213 | `4a0db59663ef0d7b` / 67,780 | -433 | 375 → 470 | 4,603 → 4,447 | 299,366 → 300,105 | 8,036 → 7,992 | 14/25 |
| v3_classical | `f62a8d0ba0aa952f` / 93,685 | `dc5ba0f6645aa13e` / 93,017 | -668 | 903 → 922 | 9,314 → 9,282 | 434,083 → 432,738 | 8,449 → 8,444 | 15/25 |
| v3_classical_mem_rel | `059461c683d135c7` / 105,675 | `ee4769e87e070519` / 105,394 | -281 | 914 → 939 | 9,851 → 9,760 | 466,399 → 466,658 | 8,864 → 8,739 | 15/25 |
| 呼数の合計 | 1,120,853 | 1,118,587 | -2,266 | | | | | |

- 動いたのは移動の意図を出して店を出る体の多い構成(語彙 v2/v3・古典)。語彙 v1 の既定は在席のまま歩き出す体が無い(在席の印を持つ体が移動を選ぶのは語彙 v2 以降の「食事」と移動の組み合わせ・推測)。edge 幾何の 4 構成は final だけが動き呼数は同じ(席が空いて店の在室の段が変わり、刻みの終わりの体の状態が変わる・呼び出しの条件は同じ)。

### V3-3 席の数え方の前後(在席の体 × 刻み・5,000 体・1 日・語彙 v3・記憶 on・近接 distance)

[v3_seat_probe.json](v3_seat_probe.json)([tools/seat_probe_vb24.py](tools/seat_probe_vb24.py)=2-2 の `probe_poi_ref.py` の数え方+内訳)。

| 量 | 前(legacy=V2) | 後(walk=V3) |
|---|---|---|
| 在席の体 × 刻み | 237,399 | 231,285 |
| うち店のセルの外 | 10,350(**4.36%**) | 4,418(**1.91%**) |
| うち歩いている(MOVING) | 11,299(4.76%) | 5,164(2.23%) |
| 店のセルの外の内訳: 乗車へ向かう(`board_line` ≥ 0) | 3,843 | 3,888 |
| 同・就寝の帰り道 | 29 | 10 |
| 同・そのほかの移動 | 4,962 | **159** |
| 同・動いていない | 1,516 | 361 |
| 同じ単位の組 × 刻み(そのうち店のセルの外の体を含む組) | 837,538(69,637=8.3%) | 798,201(25,781=3.2%) |
| 店のセルの外の在席の最大(1 刻み) | 31 | 16 |
| 歩き出しで解いた印(1 日) | 0 | 371 |
| final / 呼数(この構成) | `89e1a96885862eea` / 64,635 | `fe7f4ec709ef1b30` / 64,526 |

- **残り 1.91% の 88%(3,888)は乗車へ向かう体**(`_apply_board` と計画の出口の乗車が `MOVING` にする道=乗った時に解く)。`_apply_move` の範囲の外=親が決める(案: 乗車へ歩き出した時にも解く=同じ口を `_apply_board` の歩き出しと計画の出口の乗車に足す。既定の結果がまた動く)。〔検収の後・親の判断〕つなぎの台帳の行 `DOC-vb24-seat-not-released-on-board`(conf expedient・外す段 4-3=版上げ 3 回目の候補)。
- 〔検収 L5〕本表の final は byte-check の w6_v3_default の V2・V3 の final(`7857ecb1…`・`f6488d4d…`)と違う。席の探りの道具はテープなしで回す([seat_probe_vb24.py](tools/seat_probe_vb24.py))=テープの有無で final がずれる(10d からの既知)。呼数は同じ(64,635・64,526)。
- 2-2 の記録の数(4.3%・4.7%・7.9%)は活性化の前の資産の腕 cell の値。活性化の後の資産でも cell で 4.29%・4.67%(V2 の下書きの探り)。

### V3-4 切替口 legacy で V2 の値が再現する・系ごとの指紋

- `SHIBUYA_SEAT_RELEASE=legacy` の 4 構成は **V2 と 25 欄とも同じ**=[v3legacy_vs_v2.json](v3legacy_vs_v2.json)。さらに V2 の直し(体の層をセルから導く)の確かめで、V3 の src を legacy で回した 19 構成が V2 と 25 欄とも同じ([v2fix_vs_v2.json](v2fix_vs_v2.json))=**legacy は 19/19 で V2 を再現する**。
- 系ごとの指紋(1-0 の `engine.systems.probe`・ec21 の道具 [probe_ec21.py](../ec21/tools/probe_ec21.py) を写しの木で・合成の世界 80 体と世界資産 300 体の 2 構成): 切替口 legacy(V2 と同じ)と既定 walk の 2 つの side を比べた=[v3_probe_systems.json](v3_probe_systems.json)([tools/probe_systems_vb24.py](tools/probe_systems_vb24.py)=全部の刻みの (T, 系) ごとの指紋を並べて、食い違った系と最初の刻みを数える)。世界資産 300 体の 2 構成は刻み 424 の行為の解決(phase_c=歩き出しで在席の印を解いた)から動き、final は同じ(1 日の終わりには在席の印が解かれて状態が同じに戻る)。合成の世界は report(manifest の `leave_effects` の欄)だけ。V2 の同じ表は §V2-4 の後に足した(下の 2 つ目の表=前=V1 と同じ挙動の切替口 cell・後=V2)。

V3(legacy → walk):

| 構成 | final 前 → 後 | 呼数 前 → 後 | 動いた系(最初に動いた刻み) |
|---|---|---|---|
| syn_mem_rel_store | `d5c5fde554f17dea` → `d5c5fde554f17dea` | 1,028 → 1,028 | 1 系: report(-1) |
| real300_v3_default | `b3a584a0b0082c9c` → `b3a584a0b0082c9c` | 3,077 → 3,077 | 9 系: phase_c(424)・perceive_prepare(425)・world(425)・presence(859)・checkpoint(1079)・decide(1080) ほか 3 系 |
| real300_v3_mem_rel | `1441c65a3728926a` → `1441c65a3728926a` | 3,084 → 3,084 | 9 系: phase_c(424)・perceive_prepare(425)・world(425)・decide(451)・presence(859)・checkpoint(1079) ほか 3 系 |

V2(cell → distance):

| 構成 | final 前 → 後 | 呼数 前 → 後 | 動いた系(最初に動いた刻み) |
|---|---|---|---|
| syn_mem_rel_store | `22a71f59126a396d` → `d5c5fde554f17dea` | 1,011 → 1,028 | 18 系: decide(0)・perceive_prepare(0)・relations_wake(0)・apply_responses(1)・memory(1)・phase_c(1) ほか 12 系 |
| real300_v3_default | `70dfa441c88b64d0` → `b3a584a0b0082c9c` | 3,077 → 3,077 | 18 系: perceive_prepare(0)・decide(10)・world(22)・phase_c(433)・apply_responses(491)・conversation(491) ほか 12 系 |
| real300_v3_mem_rel | `cd67be5fbef8b420` → `1441c65a3728926a` | 3,077 → 3,084 | 20 系: perceive_prepare(0)・relations_wake(0)・decide(10)・world(22)・apply_responses(86)・phase_c(433) ほか 14 系 |

### V3-5 試験

- `tests/engine/test_seat_release_2_4.py`(7 本・data 不要): 歩き出した体だけ解く(walk)/解かない(legacy)・到着済みと移動しない体は解かない・在席でない体は数えない・腕の既定と見出しと再開の検査・合成の世界のランの manifest(walk は数が出る・legacy は 0)・腕の違う再開は止まる(2 通り)・同じ腕は通る。
- 張り替えた golden(V2 → V3)=下の表。

| 試験のファイル | 構成(goldens_vb24 の名) | 前 | 後 |
|---|---|---|---|
| `tests/engine/test_presence_executor.py` | pe_null | `d341ca5c9e3e89d3` | `5c8db46f50eb0945` |
| `tests/engine/test_presence_executor.py` | pe_null | `96_797` | `96_695` |
| `tests/engine/test_presence_executor.py` | pe_null_leave | `62c0de517b1689ec` | `de42b93d55c91cb8` |
| `tests/engine/test_presence_executor.py` | pe_null_leave | `97_690` | `96_651` |
| `tests/engine/test_presence_executor.py` | pe_null_hv1 | `eff11abb4169f319` | `3cb80dcb0d5df613` |
| `tests/engine/test_presence_executor.py` | pe_null_hv1 | `94_030` | `95_644` |
| `tests/engine/test_presence_executor.py` | pe_v3 | `7857ecb16b9665cd` | `f6488d4d5eadf5ca` |
| `tests/engine/test_presence_executor.py` | pe_v3 | `64_635` | `64_526` |
| `tests/engine/test_presence_executor.py` | pe_v3_leave | `210747ea9fa71919` | `da5e1a8ea8544881` |
| `tests/engine/test_presence_executor.py` | pe_v3_leave | `64_704` | `64_293` |
| `tests/engine/test_presence_executor.py` | pe_v3_hv1 | `62c5ea236fe4271d` | `ed20b33a7e53864d` |
| `tests/engine/test_presence_executor.py` | pe_v3_hv1 | `64_268` | `64_338` |
| `tests/engine/test_presence_executor.py` | pe_v3_l4x1 | `b2a1acae57abca9e` | `efd48de9c988cf6c` |
| `tests/engine/test_presence_executor.py` | pe_v3_l4x1 | `36_239` | `36_244` |
| `tests/engine/test_state_ledger_10b.py` | pe_v3 | `7857ecb16b9665cd` | `f6488d4d5eadf5ca` |
| `tests/engine/test_state_checks_10f.py` | pe_v3 | `7857ecb16b9665cd` | `f6488d4d5eadf5ca` |
| `tests/perception/test_near_tiebreak.py` | nt_hash | `e313dfaace60e425…` | `e4185ac9f6901403…` |
| `tests/perception/test_near_tiebreak.py` | nt_hash | `25_363` | `25_335` |
| `tests/perception/test_near_tiebreak.py` | nt_mid | `348df7c410fca9ec…` | `9a9dc58f833bdfd7…` |
| `tests/perception/test_near_tiebreak.py` | nt_mid | `25_297` | `25_284` |
| `tests/perception/test_near_tiebreak.py` | nt_old | `aaf28867cc84660d…` | `ee6d9b7b47b82618…` |
| `tests/perception/test_near_tiebreak.py` | nt_old | `25_335` | `25_307` |
| `tests/engine/test_classical_social.py` | cs_acq | `faeacf8cff1f1fae…` | `92179becdd6a2ec9…` |
| `tests/engine/test_classical_social.py` | cs_acq | `24_813` | `24_793` |
| `tests/engine/test_relations_tenure.py` | rel_v1 | `967a0f2eedb3576d` | `d696dfa98390e830` |
| `tests/engine/test_relations_tenure.py` | rel_v1 | `67_907` | `67_830` |
| `tests/engine/test_relations_tenure.py` | rel_v2 | `874ea26628f6be2e` | `4a0db59663ef0d7b` |
| `tests/engine/test_relations_tenure.py` | rel_v2 | `68_213` | `67_780` |
| `tests/engine/test_env_and_sections_10f.py` | pe_v3 | `7857ecb16b9665cd` | `f6488d4d5eadf5ca` |
| `tests/engine/test_env_and_sections_10f.py` | pe_v3 | `64_635` | `64_526` |
| `tests/engine/test_env_and_sections_10f.py` | pe_null | `d341ca5c9e3e89d3` | `5c8db46f50eb0945` |
| `tests/engine/test_env_and_sections_10f.py` | pe_null | `96_797` | `96_695` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v1 | `967a0f2eedb3576d` | `d696dfa98390e830` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v1 | `67_907` | `67_830` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v2 | `874ea26628f6be2e` | `4a0db59663ef0d7b` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v2 | `68_213` | `67_780` |

- 写しの木で関係する試験: `-m "not gpu"`(slow を含む)・`-n 10`・張り替えた golden の 7 ファイル+近接・知覚・処理・CLI・複数日・再開・系の表ほか 17 の場所 = **1,060 passed・5 failed・1 skipped**(12 分 23 秒)。落ちた 5 本は系の表の宣言(`tests/engine/systems/test_systems_table.py::test_d1_d3_code_matches_the_declaration` の phase_c・day_close・drain・close_final・report=新しい `cfg.seat_release` の読みが宣言に無い)→ `src/shibuya/engine/systems/table.py` の 5 つの系の `reads` に `cfg.seat_release` を足した(**V3 のスナップショットに後から足した**)→ `tests/engine/systems` **129 passed**

## V4 経済の段階 2 を既定に(`--economy-stage2` の既定 off → on・部品 5 つ全部)

### V4-1 変えたこと

| ファイル | 何を |
|---|---|
| `src/shibuya/engine/economy_stage2.py` | `DEFAULT_ARM = ARM_ON`・環境変数 `SHIBUYA_ECONOMY_STAGE2` の既定を `DEFAULT_ARM` に・docstring。`off` は**切替口**(2-1 までの既定=旧値の再現)。再開の腕の検査を「効いている腕」で見る(`check_resume(…, effective=)`=金の台帳の無いラン=台帳なしの `run_day` は腕 on でも段階 2 を挿さない=見出しに書かない=off と同じ・§V4-5 の発見) |
| `src/shibuya/engine/systems/build.py` | 再開の検査に `effective`(金の台帳があるか)を渡す |
| `src/shibuya/cli.py` | ランの種類は経済の段階 2 の腕も既定(on)と違えば腕(2-1 では数えていなかった)・`--economy-stage2` の説明・輪の係数の注 |
| **`pois.revenue` を税抜きに**: `src/shibuya/economy/stage2.py`・`economy/ledger.py`・`engine/resolve.py`・`engine/systems/report.py` | `MoneyStage2.purchase` が行ごとに店 → 政府へ移せたレジの税を控え(`last_purchase_tax`・中身だけ変わる箱=組み立ての後の封じは今のまま)、`Ledger.last_purchase_tax(n)` が委ねる(段階 2 が購入を委ねられないランは 0)。`resolve._apply_buy`・`_complete_eat` は店の売上の写しに `支払い − 税` を足す(`revenue_delta` も税抜き・`meal_yen` は税込のまま)。`RunResult.conserved` の左辺は `money_stage2_in = cash_terms() − register_tax()`(店から政府へ出たレジの税を引く)。つなぎの台帳 `DOC-ec21-revenue-tax-inclusive` を removed |
| 輪の係数(予算の宣言) | 既定のランは段階 2 の値 **16.0 行/体/日**(`cli.build_ledger_bundle` が腕 on のランに渡す=2-1 のまま)。`docs/design/v2-budget-declaration.md` §3 に改訂の行(5,000 体 80,000 行・39 万体 6,241,072 行=224.7 MB・金と物の輪の合計 246,522,344 B=約 246.5 MB=M8 の約 1.0%)・`economy/ledger.py` の係数の注。切替口 off は 6.5 のまま。つなぎの台帳 `DOC-ec21-ring-coefficient` を removed |
| `docs/design/bridging-ledger.json` | 上の 2 行を removed・`DOC-ec21-uncaused-rows-arm-off` を狭めた(既定のランの購入と食事の行は原因つき・残るのは組み立ての行と呼の控えの無い体の行と切替口 off のラン)・外す段 2-4 → **4-1**(実装役の案=仮)。active 338 → 336 |
| 試験 | §V4-6 |

- 給与の天引きは器のまま(`payroll_deductions`=規則の表に行が無い=0・4-2)。
- **宣言(W17 の勤務の時間)**: 賃金は W17 の「勤務」の時間 × 最低賃金で、雇用の行の体の月 38 時間(中央値 39.7 時間)=現実の 1/4 程度の見込み(ec21 §11 の 3・月の時間の出どころは判断待ち)=既定にした賃金の額は現実の 1/4 のまま。

### V4-2 動いた量(19 構成・前=V3・後=V4・1 日=2026-07-13 は給料日でない)

比べ: [v4_vs_v3.json](v4_vs_v3.json)。**19/19 構成で final が動いた**(呼数は 13 構成で同じ)。`frozen_sources`・暦・顕著行為・出動は同じ。

| 構成 | 前 final / 呼数 | 後 final / 呼数 | 呼数の差 | 気づいた延べ | 食事 | 行動の件数 | blocks の行 | 動いた欄 |
|---|---|---|---|---|---|---|---|---|
| w6_v3_default | `f6488d4d5eadf5ca` / 64,526 | `b8eadcb51e8705e7` / 64,528 | +2 | 332 → 181 | 4,447 → 4,434 | 295,063 → 295,410 | 7,657 → 7,646 | 15/25 |
| w6_v3_activity_off | `35cc3ce57f604a0c` / 50,033 | `c88ba9104f45f897` / 50,006 | -27 | 802 → 804 | 3,294 → 3,299 | 172,664 → 172,498 | 2,441 → 2,428 | 14/25 |
| w6_v1_default | `2d327566a182139d` / 51,655 | `e1288e092ddaca86` / 51,655 | +0 | 620 → 620 | 0 → 0 | 183,345 → 183,345 | 2,442 → 2,440 | 7/25 |
| w6_v1_derive_v2_1 | `317e9dd18767373c` / 44,807 | `cfbba0d504a27aa7` / 44,807 | +0 | 741 → 741 | 0 → 0 | 162,504 → 162,504 | 2,162 → 2,162 | 5/25 |
| w6_v2 | `1698f1b7cddc92dd` / 51,266 | `c186b380ae65cb86` / 51,266 | +0 | 406 → 406 | 2,052 → 2,052 | 170,110 → 170,110 | 2,309 → 2,309 | 5/25 |
| w6_v1_edge | `5ed1bb6f37bf1b68` / 46,054 | `d1c56f85847c21db` / 46,054 | +0 | 546 → 546 | 0 → 0 | 94,791 → 94,791 | 2,287 → 2,287 | 5/25 |
| w6_v2_edge | `9f89b1a7be01ac12` / 46,655 | `948b975a2ab74231` / 46,655 | +0 | 482 → 482 | 1,870 → 1,870 | 91,383 → 91,383 | 2,173 → 2,173 | 5/25 |
| w6_v1_edge_plateau | `c13ff90acb300aae` / 47,871 | `ff8fc6b562622640` / 47,871 | +0 | 468 → 468 | 0 → 0 | 98,038 → 98,038 | 2,331 → 2,331 | 5/25 |
| w6_old_v1_default | `71d0e6720220f45a` / 51,655 | `78b6fec6036b2438` / 51,655 | +0 | 620 → 620 | 0 → 0 | 183,345 → 183,345 | 2,438 → 2,436 | 7/25 |
| w6_old_v1_derive_v2_1 | `34c53e6e19f7d6f2` / 44,807 | `f647f0483ef3d7ca` / 44,807 | +0 | 741 → 741 | 0 → 0 | 162,504 → 162,504 | 2,158 → 2,158 | 5/25 |
| w6_old_v2 | `c0788c5c8a3f4f3f` / 51,266 | `9d8a34ee545f484a` / 51,266 | +0 | 406 → 406 | 2,052 → 2,052 | 170,110 → 170,110 | 2,306 → 2,306 | 5/25 |
| w6_old_v1_edge | `1d15972ddcc39130` / 46,054 | `245b2fdb8aa229ef` / 46,054 | +0 | 546 → 546 | 0 → 0 | 94,791 → 94,791 | 2,281 → 2,281 | 5/25 |
| w6_old_v2_edge | `47f422bfb758e934` / 46,655 | `2fb54c9ad562faca` / 46,655 | +0 | 482 → 482 | 1,870 → 1,870 | 91,383 → 91,383 | 2,170 → 2,170 | 5/25 |
| w6_old_v1_edge_plateau | `780236fe3706f4f1` / 47,871 | `dd66261d71c4d6ae` / 47,871 | +0 | 468 → 468 | 0 → 0 | 98,038 → 98,038 | 2,327 → 2,327 | 5/25 |
| w6_golden_null_arm | `5c8db46f50eb0945` / 96,695 | `19ee17b1b1caf44c` / 96,695 | +0 | 1,293 → 1,293 | 0 → 0 | 289,561 → 289,561 | 3,428 → 3,427 | 7/25 |
| v3_mem_store | `017e0f95bf0c5685` / 64,526 | `a9f6f9f0adb3f9a4` / 64,528 | +2 | 332 → 181 | 4,447 → 4,434 | 295,063 → 295,410 | 7,657 → 7,646 | 15/25 |
| v3_mem_rel | `4a0db59663ef0d7b` / 67,780 | `768b2262e3b0999e` / 67,794 | +14 | 470 → 486 | 4,447 → 4,479 | 300,105 → 300,390 | 7,992 → 7,969 | 15/25 |
| v3_classical | `dc5ba0f6645aa13e` / 93,017 | `ca25874a5e4acb79` / 93,017 | +0 | 922 → 922 | 9,282 → 9,282 | 432,738 → 432,738 | 8,444 → 8,444 | 5/25 |
| v3_classical_mem_rel | `ee4769e87e070519` / 105,394 | `9dd9d5684891b57c` / 105,363 | -31 | 939 → 939 | 9,760 → 9,764 | 466,658 → 466,666 | 8,739 → 8,727 | 13/25 |
| 呼数の合計 | 1,118,587 | 1,118,547 | -40 | | | | | |

- 1 日のランで効くのは引き出し(ATM)・支払いの方法(現金/口座)・IC の運賃・レジの税・来街者の口座と、税抜きの売上の写し(`pois.revenue` は behavior-hash の列)。呼数の差は財布の残りで変わる行為の成否(口座の購入・引き出し)から(推測)。

### V4-3 切替口 off で V3 の値が再現する(4 構成)

`SHIBUYA_ECONOMY_STAGE2=off` の 4 構成は **V3 と 25 欄とも同じ**=[v4off_vs_v3.json](v4off_vs_v3.json)。

### V4-4 2 日のラン(財布の推移・残差 0・溢れ)

ec21 の道具 [stage2_two_day.py](../ec21/tools/stage2_two_day.py) をそのまま(活性化の資産・5,000 体・seed 1・語彙 v3・2026-08-24(月)→ 25 日=給料日・近接 distance・在席 walk=V2・V3 の既定)=[v4_two_day.json](v4_two_day.json)。

| 腕・部品 | final | 呼数 | 行/体/日(0・1 日目) | 溢れ | 保存則 残差 | 賃金(人・円) | 引き出し(回・円) | 口座の購入・食事(行・円) | IC(行) | 税(円) | 来街者の口座(体) | 世帯の現金の 1 体の増減(0・1 日目) | conserved |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 7310d5ece7fac6fb | 143,273 | 4.098・2.076 | 0 | 0・0 | 0・0 | 0・0 | 0・0 | 0 | 0 | 0 | -1605.664・-1173.4 | True |
| on(全部) | 21e62930e8e51822 | 143,744 | 8.591・5.418 | 0 | 0・0 | 2,392・112,838,004 | 455・6,855,000 | 19・17,900 | 7,193 | 1,147,351 | 1,042 | -733.976・-437.552 | True |
| on − wages | 21e62930e8e51822 | 143,744 | 8.591・4.186 | 0 | 0・0 | 0・0 | 455・6,855,000 | 19・17,900 | 7,193 | 1,147,351 | 1,042 | -733.976・-437.552 | True |
| on − withdraw | a3325f68dcd88c20 | 143,716 | 8.545・5.403 | 0 | 0・0 | 2,392・112,838,004 | 0・0 | 113・106,600 | 7,228 | 1,150,477 | 1,042 | -1487.94・-1042.56 | True |
| on − payment | d21e1d73fe37fe4e | 143,687 | 7.888・4.668 | 0 | 0・0 | 2,392・112,838,004 | 474・7,202,000 | 0・0 | 0 | 1,146,232 | 1,042 | -822.108・-540.028 | True |
| on − tax | e6ac94ee3c02a3d1 | 143,744 | 6.659・4.1 | 0 | 0・0 | 2,392・112,838,004 | 455・6,855,000 | 19・17,900 | 7,193 | 0 | 1,042 | -733.976・-437.552 | True |
| on − visitors | 42b7ae4091e426be | 143,744 | 8.26・5.301 | 0 | 0・0 | 2,392・112,838,004 | 264・4,735,000 | 18・17,100 | 6,185 | 1,147,351 | 0 | -1042.656・-589.32 | True |

- **財布**: 世帯の現金の 1 体あたりの増減は off(V3)−1,606・−1,173 円/日 → on(V4 の既定)−734・−438 円/日(ec21 の腕 on −736・−406 と同じ向き)。2 日で尽きる型は止まっていない(月の見込みは ec21 §0 のとおり=W17 の勤務の時間が短い)。
- **残差**: 保存則の検算の残差は 7 本とも毎日 0・`RunResult.conserved` 真(店の売上の写しは税抜き・左辺からレジの税を引く)。
- **溢れ**: 輪の係数 16.0(on)・6.5(off)とも 0。生ログの行は on で 0 日目 8.59・1 日目 5.42 行/体(2 日の和 14.0 < 16.0)。
- 部品を 1 つ止めるとその流れが 0(on − wages は賃金 0・final は on と同じ=賃金は 2 日目の締めで払う=最後の checkpoint の後)。

### V4-5 再開=通し・系ごとの指紋

- **再開=通し**(5,000 体・2 日・日の境目・腕は今の既定=distance・walk・on): v3_mem_rel `31c9b19409e18b2f`(145,675 呼)・w6_v3_default `b346bb6e3ecc60af`(138,946 呼)とも **final と日の境目の後の checkpoint 4 点(behavior/full)が通しと同じ**=[v4_resume_v3_mem_rel.json](v4_resume_v3_mem_rel.json)・[v4_resume_w6_v3_default.json](v4_resume_w6_v3_default.json)(状態のファイルの見出しに `proximity`・`economy_stage2`・`seat_release` の 3 つの腕が載り、再開で今の腕と突き合わせる)
- **見つけたこと(再開の腕の検査)**: 既定を on にすると、金の台帳なしで `run_day` を直に呼ぶ試験(合成の世界)の再開が「親 arm=off・今 arm=on」で止まった(`tests/engine/events/test_e_log_schema.py::test_resume_at_a_step_boundary_gives_the_same_ids`)。台帳が無いランは段階 2 を挿さない=見出しに書かない=効いている腕は off なのに、検査が腕の値だけを見ていたため。検査を「効いている腕」(台帳があるか)で見る形に直した(§V4-1)。試験 `tests/economy/stage2/test_stage2_default_2_4.py`。
- 系ごとの指紋(切替口 off と既定 on・ec21 の道具を写しの木で): [v4_probe_systems.json](v4_probe_systems.json)。世界資産 300 体の 2 構成は最初の checkpoint(刻み 359=金の台帳の行と生ログ)と判断の系(刻み 360)から動く(初期の預金・口座の支払い・税の行)。合成の世界(台帳なしの `run_day`)は段階 2 を挿さない=0 系(V4-5 の「効いている腕」)。

| 構成 | final 前 → 後 | 呼数 前 → 後 | 動いた系(最初に動いた刻み) |
|---|---|---|---|
| syn_mem_rel_store | `d5c5fde554f17dea` → `d5c5fde554f17dea` | 1,028 → 1,028 | 0 系: — |
| real300_v3_default | `b3a584a0b0082c9c` → `3dfb30508605d14a` | 3,077 → 3,077 | 11 系: checkpoint(359)・decide(360)・phase_c(364)・world(600)・observe(1056)・apply_responses(1057) ほか 5 系 |
| real300_v3_mem_rel | `1441c65a3728926a` → `5cb03e3afb3d00f7` | 3,084 → 3,084 | 12 系: checkpoint(359)・decide(360)・phase_c(364)・world(600)・memory(1056)・observe(1056) ほか 6 系 |

### V4-6 試験

- 写しの木で全体(`-m "not slow and not gpu" -n 10 --dist loadfile --ignore=tests/c7`・封印の錨の試験 1 ファイルを外した=§V1-7): **4,864 passed・8 failed・2 skipped・1 xfailed**(12 分 12 秒)。落ちた 8 本の行き先: (1) 試験の偽の金の台帳(`_FakeMoney`・`_PickyMoney`)に `last_purchase_tax` が無い 3 本 → `resolve._purchase_tax` が口の無い台帳では税 0(売上の写しは支払いのまま)にした (2) 台帳の配線の試験 3 本(`tests/engine/test_ledger_wiring.py`=段階 2 の外の C4 の帳簿)→ ファイルの頭で切替口 off (3) 退出の歩きの試験の保存則の手書きの式に段階 2 の項 `money_stage2_in` を足した (4) 既知の junction の 1 本(ab7)。ほかに合成の世界で 3 本(§V4-5 の再開の検査・段階 2 の保存則の左辺・1-9 の金の行と出来事の 1 対 1=切替口 off で見る)を作業木で見つけて直した。
- 直した後の確かめ(写しの木): 落ちた試験のファイル+`tests/economy`+`tests/engine/events`+張り替えた golden のファイル(`-m "not gpu"`=slow を含む): **661 passed・22 failed**(14 分 3 秒)→ 22 本は slow の `tests/economy/cp2` の 2 ファイル(K17 の 19 構成=既定の係数は段階 2 の 16.0・5,000 体の 1 日の 6.5 と 1-9 の HEAD の写しとの同値=切替口 off で見る)→ 直して `tests/economy` の slow **26 passed**(2 分 29 秒)。
- 新しい試験 `tests/economy/stage2/test_stage2_default_2_4.py`(4 本・data 不要): 既定の腕は on・切替口 off で部品が空・効いている腕で見る再開の検査(台帳なし/あり)・税の切り捨て・合成の世界のランの売上の写し=世帯 → 店の消費支出 − レジの税(保存則が通る)。

- 張り替えた golden(V3 → V4)=下の表。

| 試験のファイル | 構成(goldens_vb24 の名) | 前 | 後 |
|---|---|---|---|
| `tests/engine/test_presence_executor.py` | pe_null | `5c8db46f50eb0945` | `19ee17b1b1caf44c` |
| `tests/engine/test_presence_executor.py` | pe_null_leave | `de42b93d55c91cb8` | `aac7b60677cb985d` |
| `tests/engine/test_presence_executor.py` | pe_null_hv1 | `3cb80dcb0d5df613` | `c977ca9de2975f1a` |
| `tests/engine/test_presence_executor.py` | pe_null_hv1 | `95_644` | `95_647` |
| `tests/engine/test_presence_executor.py` | pe_null_l4x1 | `23d6397b39afb614` | `e539b7c8d5e60a0f` |
| `tests/engine/test_presence_executor.py` | pe_v3 | `f6488d4d5eadf5ca` | `b8eadcb51e8705e7` |
| `tests/engine/test_presence_executor.py` | pe_v3 | `64_526` | `64_528` |
| `tests/engine/test_presence_executor.py` | pe_v3_leave | `da5e1a8ea8544881` | `2838430451abbac1` |
| `tests/engine/test_presence_executor.py` | pe_v3_leave | `64_293` | `64_327` |
| `tests/engine/test_presence_executor.py` | pe_v3_hv1 | `ed20b33a7e53864d` | `0776169f2d8f366a` |
| `tests/engine/test_presence_executor.py` | pe_v3_hv1 | `64_338` | `64_223` |
| `tests/engine/test_presence_executor.py` | pe_v3_l4x1 | `efd48de9c988cf6c` | `5d227b075985bd68` |
| `tests/engine/test_presence_executor.py` | pe_v3_l4x1 | `36_244` | `36_225` |
| `tests/engine/test_state_ledger_10b.py` | pe_v3 | `f6488d4d5eadf5ca` | `b8eadcb51e8705e7` |
| `tests/engine/test_state_checks_10f.py` | pe_v3 | `f6488d4d5eadf5ca` | `b8eadcb51e8705e7` |
| `tests/engine/test_intent_chooser.py` | q13_v3 | `6d0ad8b13125ea5a` | `66f0d41736514fa4` |
| `tests/engine/test_intent_chooser.py` | q13_v3 | `36_246` | `36_146` |
| `tests/engine/test_intent_chooser.py` | q13_null | `319e347ffe08946b` | `cee40ff700954d37` |
| `tests/engine/proximity/test_runs.py` | prox_cell300 | `f1ec0336ef617de0…` | `ab5c9d9c0b40a263…` |
| `tests/perception/test_near_tiebreak.py` | nt_hash | `e4185ac9f6901403…` | `4b3db260a5320a17…` |
| `tests/perception/test_near_tiebreak.py` | nt_mid | `9a9dc58f833bdfd7…` | `c2a7d4823ef8acc1…` |
| `tests/perception/test_near_tiebreak.py` | nt_old | `ee6d9b7b47b82618…` | `0a1ce7b6e5c750d6…` |
| `tests/engine/test_classical_social.py` | cs_acq | `92179becdd6a2ec9…` | `87f051103976be28…` |
| `tests/engine/test_relations_tenure.py` | rel_v1 | `d696dfa98390e830` | `a2beb00f254b219c` |
| `tests/engine/test_relations_tenure.py` | rel_v1 | `67_830` | `67_780` |
| `tests/engine/test_relations_tenure.py` | rel_v2 | `4a0db59663ef0d7b` | `768b2262e3b0999e` |
| `tests/engine/test_relations_tenure.py` | rel_v2 | `67_780` | `67_794` |
| `tests/engine/test_env_and_sections_10f.py` | pe_v3 | `f6488d4d5eadf5ca` | `b8eadcb51e8705e7` |
| `tests/engine/test_env_and_sections_10f.py` | pe_v3 | `64_526` | `64_528` |
| `tests/engine/test_env_and_sections_10f.py` | pe_null | `5c8db46f50eb0945` | `19ee17b1b1caf44c` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v1 | `d696dfa98390e830` | `a2beb00f254b219c` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v1 | `67_830` | `67_780` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v2 | `4a0db59663ef0d7b` | `768b2262e3b0999e` |
| `tests/engine/test_env_and_sections_10f.py` | rel_v2 | `67_780` | `67_794` |

## V5 計器の節の整理(`group_norms.cost.ticks` を manifest の設定の節から観測の節へ)

| ファイル | 何を |
|---|---|
| `src/shibuya/engine/manifest_sections.py` | `group_norms` の設定の子から `cost` を外し、`_mixed("group_norms.cost", config=("note",), observed=("ticks",))` を足した(`cost.ticks`=計器が回った刻みの数=再開のランは再開の時刻からの数=**観測**・`cost.note`=定数の文=設定)。`CONFIG_PATHS_SHA256` が動く(`group_norms.cost` → `group_norms.cost.note`・この 1 本を戻すと V3 の値 `ac930362…` に戻る) |
| `src/shibuya/engine/experiment/branch.py` | `RESUME_DERIVED`(反実仮想の分岐の入力の一致で、再開で動く設定の欄を宣言して許す口)の注: 2-4 より後の manifest どうしの比べでは設定の差に出ない=2-4 より前の節の表で録った基準との比べのために残す(比べは基準の manifest の節の表で見る) |
| `tests/engine/test_env_and_sections_10f.py` | `CONFIG_PATHS_SHA256` `ac930362…` → `417f0818…` |
| `tests/engine/experiment/test_x33_branch.py` | 世界資産の分岐の 4 つの確かめ: `resume_derived` は空・`group_norms.cost.ticks` は設定の差に無い。負の対照: 2-4 より前の節の表を載せた基準では宣言の値のときだけ許す(前と同じ)+今の節の表では宣言なしで差に出ない |

- **結果は不変**: 19 構成で 25 欄とも V4 と同じ=[v5_vs_v4.json](v5_vs_v4.json)。
- 試験(作業木・`-m "not slow and not gpu"`): `tests/engine/test_env_and_sections_10f.py`・`tests/engine/experiment`・`tests/engine/time`・`tests/engine/bridging` = 203 passed・1 failed(負の対照の 1 本=上の直しの前)→ 直して通る。

## V6 錨のファイルの分離(較正側/構築側と検証側・値は変えない)

2-0 の検収(混在)・PENDING 仮-13(〔灰〕は決まるまで検証側と同じ扱い)。**値を読まずに鍵の名で機械的に分けた**([tools/split_anchors_vb24.py](tools/split_anchors_vb24.py)=JSON を読んで鍵の名で振り分けて書くだけ・画面には錨の名の数と較正側/構築側の鍵の名だけ。確かめの `check` は git の版の元のファイルと「2 本を合わせたもの」が鍵と値の全部で同じかを真偽だけで出す=元の写しを作業用の置き場に作らない)。

| 元(消した) | 較正側/構築側 | 検証側 |
|---|---|---|
| `docs/bench/anchors/presence_anchors_v0.json` | `presence_calib_anchors_v0.json`=錨 3 本(`core9_daytime_population`・`core9_night_population`・`core9_day_night_ratio`=中核 9 町丁目の昼夜間人口〔非〕)+見出し(`schema`・`version`・`created`)+本道具が書いた `purpose`・`split_from` | `presence_validation_anchors_v0.json`=ほかの錨 6 本(PT 由来〔灰〕・第 4-1 表〔検〕ほか=〔灰〕と区分の決まっていない錨は仮-13 のとおり検証側)+元の `purpose`・`rules`・見出し・`split_from` |
| `docs/bench/anchors/hunger_energy_anchors_v0.json` | `hunger_energy_build_anchors_v0.json`=`dri2025`・`nhns_t14_weight`・`nhns_t13_meal_kcal`・`mets_2012` と、その `sources`(4 本) | `hunger_energy_validation_anchors_v0.json`=`nhns_t10_breakfast_skip`・`ssb2021_t18_1_weekday`・`ssb2021_meal_rate_15min`・`derived`(昼の既定の時刻=15 分の食事率の導出)と、その `sources`(2 本) |

- 空腹の錨の見出し(`schema`・`generated_by`・`attribution`・`usage`)は両方に写した(`usage` は元の文が自ら「constants … and validation-only anchors (NHNS table 10, SSB table 18-1, 15-min meal rates)」と書く=分け方はこの文に合わせた)。在圏の錨の `rules` と元の `purpose` は検証側(中身を読まずに検証側へ寄せた=保守側)。
- 確かめ: `split_anchors_vb24.py check` → 2 本とも「合わせると元と同じ: True」。
- **結果は不変**: 19 構成で 25 欄とも V5 と同じ=[v6_vs_v5.json](v6_vs_v5.json)。manifest で動くのは `energy.anchors`(2 本の道筋を `+` でつないだ文)と `energy.anchors_md5`(2 本のバイト列をつないだ md5)だけ(設定の節の値・道筋の表は同じ)。

読む側の道筋(直したもの):

| ファイル | 前 | 後 |
|---|---|---|
| `src/shibuya/engine/energy.py` | `ANCHORS_PATH`(1 本) | `ANCHORS_BUILD_PATH`・`ANCHORS_VALIDATION_PATH`・`ANCHORS_PATHS`・`ANCHORS_REL`。`load_anchors()` は 2 本を 1 つの辞書に戻す(分ける前の 1 本と同じ辞書=鍵の順だけ違う)。**読み口は検証側のファイルを読む形のまま**(既定の食事の時刻=第 18-1 表・`derived.lunch_default`=置き換えはユーザーの判断の後=PENDING §1-1) |
| `tools/hunger/build_hunger_anchors.py` | 1 本を書く | `split_doc` で 2 本を書く・`--check` も 2 本(分け方の正=本記録の道具も同じ関数を呼ぶ)。**生成器そのものは回していない**(`data/calib/hunger` の原表=計器の段で落とす語に当たる=読まない) |
| `tools/instruments/read_guard.py`(2-0 の計器) | 落とす語 `presence_anchors`・`hunger_energy_anchors` | 足した: `presence_validation_anchors`・`hunger_energy_validation_anchors`(前の 2 語は残す=古い写しを落とす)。較正側 `presence_calib_anchors`・構築側 `hunger_energy_build_anchors` は落ちない |
| `tools/c7/presence_yardstick.py` | `DEFAULT_ANCHORS_PATH`(1 本) | `DEFAULT_ANCHORS_PATHS`(2 本)・`load_anchors()` は 2 本を 1 つに戻す(物差しは両方の錨を使う)・`DEFAULT_ANCHORS_PATH` は検証側(記録の表記) |
| `tools/fig/fig_presence_24h.py`・`fig_calls_by_hour.py` | 1 本 | 在圏の図は 2 本を `+` でつないで錨を合わせる・呼の図(`full_population`)は検証側 |
| `tests/c7/test_presence_yardstick.py` | fixture が 1 本(混在)を読む | **fixture は較正側だけを読む**(`ANCHORS_PATH`=`presence_calib_anchors_v0.json`)。〔検収 H1〕較正側だけでは検証側の鍵を引く試験が KeyError で落ちた(HEAD `a231ef9` の版で 11 本)=fixture を「較正側のファイル+検証側の作り物」に直した(末尾の「検収の後の直し」) |
| `tests/tools/test_anchor_gauge.py`・`tests/engine/test_energy_balance.py` | 1 本の名 | 2 本の名(落とす語・開いたファイルの印・CR の検査) |

- 試験(作業木・`-m "not slow and not gpu"`): エネルギーと食事の 4 ファイル・`tests/tools`・`tests/engine/bridging`・`test_env_and_sections_10f.py` = **218 passed**。
- 写しの木(`_bc/tree`)には較正側と構築側と空腹の検証側を写し、在圏の検証側 `presence_validation_anchors_v0.json` は写さない(前の `presence_anchors_v0.json`・`diversity_anchors_v0.json` と同じ扱い)。
- byte-check の head の写しの手順(10e の道具の docstring)の「錨はエンジンが開く 3 本」は、V6 より後の src では 3 本=空腹の 2 本(`engine/energy.py`)+活動の事前分布(`engine/classical.py`)。〔検収 L3〕前の版の本書は「4 本(+通勤時間)」と書いたが、`commute_time_dist_r3.json` は構築側(`build/sched/trial.py`)と 2-0 の計器だけが開く=エンジンは開かない(src を grep して確かめた)。10e の docstring を直した。

## V7 切替口の整理(RET=本段では一覧だけ・消すかは親が決める)

### V7-1 残す(本段で既定を変えた・2-4 の記録の旧値の再現に使う)

| 切替口 | 置き場 | 旧値の再現の確かめ |
|---|---|---|
| `--proximity cell`(環境変数 `SHIBUYA_PROXIMITY`) | `engine/proximity.py`(`DEFAULT_MODE`=distance) | §V2-3(4 構成 25 欄) |
| `--seat-release legacy`(`SHIBUYA_SEAT_RELEASE`) | `engine/seat_release.py`(`DEFAULT_MODE`=walk) | §V3-4(19 構成 25 欄) |
| `--economy-stage2 off`(`SHIBUYA_ECONOMY_STAGE2`)・`--economy-stage2-parts` | `engine/economy_stage2.py`(`DEFAULT_ARM`=on) | §V4-3(4 構成 25 欄)・§V4-4(部品を 1 つずつ止めた 2 日) |
| `w12_real_timetables.USE_ODPT_CHALLENGE`(構築側・新) | `build/field/w12_real_timetables.py`(既定 True) | §V1-5(試験で W12 を 2 回組む)=PENDING 仮-15 の確認まで |
| `--proximity-d {1.0,2.0,2.5}` | `engine/proximity.py` | 感度の腕(2-2 の B3)=旧値ではない |

### V7-2 消す候補(10e・第 1 期・それより前に残した旧値の再現の口=実装役の見立て・親が記録を見て決める)

| 切替口 | 再現するもの | 使う試験(golden) | 実装役の見立て |
|---|---|---|---|
| 構築 `w12_external_nodes.USE_REAL_TIMETABLES=False` | W12 1.1.0(等間隔の推定 5 線+メトロ 3 線) | `tests/build_field/test_w12_real_timetables.py`・`test_w12_pm_peak_switch.py` | 候補(つなぎの台帳 `EX-build.field.w12_external_nodes-f2cc7f0a` の外す段が 2-4)。**ただし等間隔の推定の関数そのものは京王の切替口(False)と実データの無い線の道が使う=関数は残す** |
| `--leave-effect off`(`leave_effect=False`) | 9a(第301)より前の退去 | `test_presence_executor.py` の `*_leave_off`・`test_l4_scale_1_…`・`test_hunger_model_v1_…`・`test_intent_chooser.py` の Q13 | 候補(旧値の再現の試験の束=下の 3 つと一緒に消すかを決める) |
| `--hunger-model v1` | 5 段目(第291)より前の空腹 | 同上 `*_hunger_v1` | 候補(ただし `run_day` のライブラリの既定が v1=CLI の既定だけ energy=合成の世界の試験が多数 v1 で回る=消すと既定の付け替えが要る) |
| `--l4-scale 1.0` | 3 段目(第289)より前の呼数の上限 | 同上 `*_l4x1` | 残す見込み(予算の腕 D-99 として意味がある) |
| `--poi-target legacy` | 段 2a(第288)より前の対象の選び方 | `test_intent_chooser.py` の Q13 | 候補 |
| `--near-tiebreak id`・`--near-order id` | 第304 Q107・Q130 より前の近接の並び | `tests/perception/test_near_tiebreak.py` | 候補 |
| `--rel-tenure-hash v1` | 関係の初期化の寿命のハッシュ v1 | `tests/engine/test_relations_tenure.py` の `("v1","behavior")` | 候補 |
| `report_precondition=False`・`queue_service=False`・`plan_executor=False` | D-113 ②③・D-62 より前 | `test_presence_executor.py` の帰無腕(null arm=計画実行層 off の退化検査) | 残す見込み(帰無腕は退化検査の要=§7) |
| `--response-delay 2` | 10a より前のテープの再生(+2 刻み) | 10a の試験 | 候補(手元の 53 本の旧テープは RET で再生できなくなった=10e §RET-1) |
| `SHIBUYA_WRITE_GUARD=off`・`SHIBUYA_EVENTS=off` | 書きの守り・出来事の記録の運用の口 | 1-0・1-3 の試験 | 残す(運用の口=旧値ではない) |

- どれも本段では消していない(発注=一覧だけ)。消すときは 10e の RET と同じ形(旧値の再現の試験を「切替口が無い」ことを見る試験に置き換え・`full-hash` だけ動く列の削除は無い見込み)。

## 締め(版上げ 2 回目)

### 締め-1 段ごとの動いた量(19 構成・5,000 体・seed 1・1 日・既定の引数・資産は V1 から組んだ資産)

| 段 | 中身 | v3 既定 final / 呼数 | v3_mem_rel final / 呼数 | 帰無腕 final / 呼数 | 古典+記憶+関係 final / 呼数 | 呼数の合計(19 構成) |
|---|---|---|---|---|---|---|
| **base** | 本体 HEAD 9f631b0+本体の v2(5ff1bacf) | `5f7ae9ff24005314` / 65,597 | `73a78288ab5e1498` / 69,111 | `354f49ca9a61b986` / 97,234 | `4c512a1fdc2a70c0` / 106,565 | 1,129,811 |
| **V1** | 資産の活性化(W12 1.2.0・W9 の窓・6a7d34e8) | `4bcca9f0216362bb` / 65,400 | `c506dec249bb4328` / 69,114 | `767f0224d82ba9a9` / 98,046 | `18bd9bfea8f51c11` / 106,977 | 1,130,899 |
| **V2** | 近接 distance を既定に | `7857ecb16b9665cd` / 64,635 | `874ea26628f6be2e` / 68,213 | `d341ca5c9e3e89d3` / 96,797 | `059461c683d135c7` / 105,675 | 1,120,853 |
| **V3** | 在席の印を歩き出しで解く | `f6488d4d5eadf5ca` / 64,526 | `4a0db59663ef0d7b` / 67,780 | `5c8db46f50eb0945` / 96,695 | `ee4769e87e070519` / 105,394 | 1,118,587 |
| **V4** | 経済の段階 2 を既定 on・売上の写しは税抜き | `b8eadcb51e8705e7` / 64,528 | `768b2262e3b0999e` / 67,794 | `19ee17b1b1caf44c` / 96,695 | `9dd9d5684891b57c` / 105,363 | 1,118,547 |
| **V5** | 計器の節の整理(結果不変) | `b8eadcb51e8705e7` / 64,528 | `768b2262e3b0999e` / 67,794 | `19ee17b1b1caf44c` / 96,695 | `9dd9d5684891b57c` / 105,363 | 1,118,547 |
| **V6** | 錨のファイルの分離(結果不変) | `b8eadcb51e8705e7` / 64,528 | `768b2262e3b0999e` / 67,794 | `19ee17b1b1caf44c` / 96,695 | `9dd9d5684891b57c` / 105,363 | 1,118,547 |

- V1〜V4 で既定の final が動き、V5・V6 は 19 構成で 25 欄とも同じ。呼数の合計は 1,129,811 → 1,118,547(−1.0%)。
- 切替口で前の段の値が再現する: V2 `--proximity cell`(4 構成)・V3 `--seat-release legacy`(19 構成=§V3-4)・V4 `--economy-stage2 off`(4 構成)とも 25 欄が同じ。
- 2-0 の計器: V1 の後([2026-10-14_vb24-V1](../../../instruments/anchor_gauge/2026-10-14_vb24-V1/anchor_gauge.md)・最初の記録 `2026-10-14_2bc7a4b` との差 52 件)と版上げの後(V6=[2026-10-14_vb24-V6](../../../instruments/anchor_gauge/2026-10-14_vb24-V6/anchor_gauge.md)・V1 との差 [compare_vs_2026-10-14_vb24-V1.md](../../../instruments/anchor_gauge/2026-10-14_vb24-V6/compare_vs_2026-10-14_vb24-V1.md)=156 件のうち 40 件=在圏のピークの順 1・来街者/居住者の比 25・到着の割合 10・始業 4 ほか・合否は書かない)。mock `b8eadcb51e8705e7`/64,528・classical `ca25874a5e4acb79`/93,017(V6 の byte-check の w6_v3_default・v3_classical と同じ値)。
- manifest で動いた欄(設定): `frozen_sources`(V1=W12 の時刻表の 1 行)・`proximity`(V2)・`leave_effects.seat_release`(V3)・`economy.stage2`・`economy.raw_capacity`・`raw_rows_per_agent_day`(V4=16.0)・`bridges_version`・`bridges_count`(V4=つなぎの台帳の 3 行)・`energy.anchors`・`anchors_md5`(V6)。`rules_version` は動かない(規則の表を変えていない)。設定の道筋の表 `CONFIG_PATHS_SHA256` は V3(`leave_effects.seat_release`)と V5(`group_norms.cost.note`)で動いた。

### 締め-2 試験

| 段 | 何を | 結果 |
|---|---|---|
| V1 | 写しの木で全体(not slow)→ 張り替えの後の 12 ファイル(slow を含む)+ `tests/c8` | 4,845 passed・18 failed・23 errors(§V1-7)→ 403 passed・193 passed |
| V2 | 写しの木で全体(not slow)→ 直した 10 ファイル(slow を含む・在席 legacy) | 4,854 passed・7 failed → 393 passed |
| V3 | 写しの木で 17 の場所(slow を含む)→ `tests/engine/systems` | 1,060 passed・5 failed → 129 passed |
| V4 | 写しの木で全体(not slow)→ 落ちた所と経済(slow を含む) | 4,864 passed・8 failed → 661 passed・22 failed → `tests/economy` slow 26 passed |
| V5 | 作業木で 4 の場所(not slow) | 203 passed・1 failed → 直して通る |
| V6 | 作業木で 8 の場所(not slow) | 218 passed |
| **最後(V6 の後)** | 写しの木で全体 `-m "not slow and not gpu" -n 10 --dist loadfile --ignore=tests/c7`(封印の錨の試験 1 ファイルを外した) | **4,871 passed・1 failed・2 skipped・1 xfailed**(17 分 30 秒)。落ちた 1 本は既知の junction の ab7 |
| **最後の slow** | 写しの木で `-m "slow and not gpu" -n 10 --ignore=tests/c7` | 86 passed・1 failed・1 skipped(13 分 0 秒)。落ちた 1 本は性能の試験 `tests/engine/test_change_detect_p6.py`(40 万体の変化の検出・最悪 4.522 ms/刻み > 2 ms=10 並列で 5,000 体の試験と同時に回った)→ **単独で回し直して通る**(最悪 1.798 ms/刻み・余裕は小さい)。本段は変化の検出のコード(`engine/change_detect.py`)を変えていない |

- `tests/c7` は回していない(発注)。`tests/w17/test_diversity_yardstick.py` は写しの木に封印の錨 `diversity_anchors_v0.json` を写さないので写しの木では外した(本体では回る・中身は変えていない)。
- 秘密の走査(`tools/scan_secrets.py`・変えたファイルと新しいファイル全部): CLEAN(変えたファイルと新しいファイル 113 本)。同じ 113 本で CR 0 本・絶対パスと名前の検索 0 件。走査と CR の検査は在圏の検証側の錨のファイルもバイト列で機械的に見た(値は画面に出していない)

### 締め-3 スナップショット(親が段ごとに commit する)

- 作業用の置き場 `_bc/snaps/V1`〜`V6`(git の外)に段ごとの**累積**の写し(`files/<リポからの道筋>`)・`MANIFEST.txt`(sha256・道筋・M/A/D)・`delta.txt`(前の段からの差=その段で commit するファイル)。`added_later.txt` はその段の試験で後から見つけて足した直し(V1: つなぎの台帳の試験・影の形の道具の改行/V3: 系の表の宣言)。V6 の `presence_validation_anchors_v0.json` は写していない(封印の層の写しを置き場に残さない=作業木のファイルをそのまま)。
- V7 は本記録(README の §0・§V7・締め)と 2-0 の計器の V6 の記録(`docs/bench/instruments/anchor_gauge/2026-10-14_vb24-V6/`=V6 のスナップショットの後に回した)。作業木の今の状態=V7 の累積。
- 段ごとの commit の順: V1 → V2 → V3 → V4 → V5 → V6 → V7。各段の `delta.txt` のファイルを `files/` から作業木へ写して(または作業木の今のファイルが同じ sha256 ならそのまま)ステージする。V2 のスナップショットは V3 の差し込みを文字で外して作った(`_bc/make_snap_v2.py`)=HEAD に V2 の `src` を重ねた写しで byte-check 6 構成が V2 と 25 欄とも同じ(`_bc/v2snap_vs_v2.json`)。

### 締め-4 限界・仮採用・親に確かめてほしいこと

**仮採用(10-13b §0-3=戻せる形)**

1. **W9 の容量の宣言**(§V1-3): 案 A(宣言を 13,000,000 B/日に)を入れた。B(昼の面だけ/zlib)を選ぶならエンジンの読み口を直して影を組み直す。
2. **京王の切替口 `USE_ODPT_CHALLENGE`**(§V1-5): 既定 True(京王の行を含めたまま活性化)。仮-15 の確認で扱いが変わるなら False で W12 を組み直す(井の頭線は等間隔の推定=ゲート 1 件 FAIL の宣言)。
3. **新しい W12 の 8 行の 3 分類と対照**(§V1-6): 実装役の案(未リサーチ)・D-44 は未判定。
4. **在席の印は `_apply_move` だけ**(§V3-3): 残り 1.9% の 88% は乗車へ歩く体。乗車の歩き出しにも同じ口を足すか(既定の結果がまた動く)。
5. **`DOC-ec21-uncaused-rows-arm-off` の外す段 4-1**(§V4-1・実装役の案)。
6. **在圏の錨の分け方**(§V6): 較正側は core9 の 3 本だけ・ほかの 6 本(区分の決まっていない〔灰〕を含む)は検証側=仮-13 のとおり。`rules` と元の `purpose` も検証側。
7. **`tests/c7` の fixture を較正側だけに**(§V6): 〔検収 H1〕落ちた(11 本)=較正側のファイル+検証側の作り物に直した(末尾の「検収の後の直し」)。

**親に確かめてほしいこと**

1. **V1 の写し**(§V1-2): `activate_vb24.py apply --dry-run` → `apply` → `verify`(本体の `data/world/v2` を書く=親が実行)。〔検収の後〕親が活性化した(2026-10-14・`verify` 同じ)。前の資産は `materialize` で組む(検収 M1)。写した後、写しの木は不要(`_bc/tree` は data へのつなぎ=消すときは junction を先に外す)。
2. **つなぎの台帳で外す段が 2-4 の行の残り**(§V1-8): `W9#5`・`BR-SHADOW-NEAREST-DAY`(窓の外の日=続く)・`EX-build.field.w12_external_nodes-f2cc7f0a`(京王の切替口が使う)・`BR-PHONE-TABLE-BLANK`・`DOC-ec21-atm-fixture`・`DOC-ec21-atm-hours-and-cells`・`DOC-ec21-account-two-rows`・`DOC-ec21-consumption-pair-for-outside-sales`・`DOC-ec21-bank-branch-default-hours` は本段の発注の外=外す段を親が改める(V4 で外したのは `DOC-ec21-revenue-tax-inclusive`・`DOC-ec21-ring-coefficient`・狭めたのは `DOC-ec21-uncaused-rows-arm-off`)。〔検収の後・親の判断〕外す段を改めた(末尾の「検収の後の直し」)。
3. **近接の費用の予算の宣言**(§V2-4): 追記案を書いた(予算の宣言の設計書は親)。
4. **ランの種類**(§V4-1): 経済の段階 2 の腕も既定と違えば「腕」にした(2-1 では数えていなかった)。
5. **錨の名の変更の波及**: 設計書・PENDING・STATUS・各段の記録が `presence_anchors_v0.json`・`hunger_energy_anchors_v0.json` を名指す所(本段の発注の外=親の文書)。byte-check の head の写しの錨は V6 より後の src では 3 本(空腹の 2 本+活動の事前分布)。〔検収 L3〕消した錨のファイルを開く古い道具 3 本と 10e の docstring は直した(末尾の「検収の後の直し」)。
6. 切替口の消す候補(§V7-2)。

**限界**

- 動いた量は 1 日(07-13=給料日でない)と 2 日(08-24〜25)と 2-0 の計器だけ。W9 の窓の影(07-18・07-19)が効くのは 6 日目以降を回すラン=本段では測っていない(5 日の正の表=md23 は窓の中の影が本体の v2 にあった)。
- 近接に左右される値は暫定(5-2)・在席の印の数え方は node 座標。
- 賃金の額は現実の 1/4 のまま(W17 の勤務の時間・判断待ち)。給与の天引きは器のまま(4-2)。
- byte-check の 25 欄は manifest の設定の値(`proximity`・`leave_effects`・`economy` ほか)を比べない=その動きは各段の表と試験で見た。

### 締め-5 触った共有ファイル(親が取り込み順に rebase するときの一覧)

| 段 | ファイル |
|---|---|
| V1 | `src/shibuya/build/{vis/w9_shadow.py,field/w12_real_timetables.py,field/w12_external_nodes.py,audit/w19_freeze.py}`・`tools/c8/{sensitivity.py,sensitivity_v1.json,expedient_triage_v1.json}`・`docs/bench/c8/sensitivity_v1.*`・`docs/design/v2-world-data-build-spec.md`・試験(build の 3 つ・c8・golden の 9 ファイル・つなぎの台帳)・`docs/bench/instruments/anchor_gauge/2026-10-14_vb24-V1/` |
| V2 | `src/shibuya/{cli.py,engine/proximity.py,perception/renderer.py,engine/state_ledger.py,engine/systems/{build,act,boxes,judge,talk}.py}`・試験(golden・描画の (B)・C9b・状態台帳) |
| V3 | `src/shibuya/{cli.py,engine/seat_release.py(新),engine/resolve.py,engine/manifest_sections.py,engine/systems/{boxes,build,act,report,state_io,table}.py}`・試験(golden・`CONFIG_PATHS_SHA256`・新しい 1 ファイル) |
| V4 | `src/shibuya/{cli.py,economy/{stage2,ledger}.py,engine/{economy_stage2,resolve}.py,engine/systems/{build,report}.py}`・`docs/design/{bridging-ledger.json,v2-budget-declaration.md}`・試験(golden・経済・台帳の配線・退出の歩き・新しい 1 ファイル) |
| V5 | `src/shibuya/engine/{manifest_sections.py,experiment/branch.py}`・試験 2 ファイル |
| V6 | `docs/bench/anchors/*`(2 本を消し 4 本を足す)・`src/shibuya/engine/energy.py`・`tools/{hunger/build_hunger_anchors.py,instruments/read_guard.py,c7/presence_yardstick.py,fig/fig_presence_24h.py,fig/fig_calls_by_hour.py}`・試験 3 ファイル(`tests/c7` を含む) |

- 凍結の表(`manifest_keys_frozen.json`・`writes_soa_frozen.json`・`writes_paths_events.json`)・語彙・状態台帳の行の数は変えていない(V3 の manifest は `leave_effects` の子を足しただけ・状態台帳は V2 の読みの許可の 1 本を消しただけ)。

### 締め-6 再現(リポの根・作業木の src を `PYTHONPATH` に)

```
D=docs/bench/analysis/wallbounce-1012/vb24
B=docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py
# V1 の資産
python $D/tools/activate_vb24.py stage --record <作業用>/stage.json        # data/world/v2_stage_2-4(2 回組んで build_hash 一致)
python $D/tools/activate_vb24.py plan --record $D/v1_activation_plan.json  # data/world/v2_steps_2-4
python $D/tools/w9_shapes.py data/world/v2_stage_2-4 > $D/v1_w9_shapes.json
# byte-check(前=本体 HEAD の src の写し+本体の v2・段ごと=作業木の src+組んだ資産)
python $B side --src <HEAD の写し>/src --label base --scratch <作業用> --out <作業用>/side_base.json
python $B side --world data/world/v2_stage_2-4 --label vN --scratch <作業用> --out <作業用>/side_vN.json
SHIBUYA_PROXIMITY=cell python $B side --world data/world/v2_stage_2-4 --label v2cell --only w6_v3_default,w6_v1_default,v3_mem_rel,v3_classical_mem_rel …
SHIBUYA_SEAT_RELEASE=legacy python $B side … ; SHIBUYA_ECONOMY_STAGE2=off python $B side …
python $B compare --a <前> --b <後> --out $D/vN_vs_vM.json
python $D/tools/table_vb24.py --a <前> --b <後>
# golden(試験と同じ引数で集めて張り替え)
python $D/tools/goldens_vb24.py all --world data/world/v2_stage_2-4 --out <作業用>/goldens_VN.json
python $D/tools/regold_vb24.py --goldens <作業用>/goldens_VN.json --stage VN
# 2-0 の計器
python tools/instruments/anchor_gauge.py run --scratch <作業用> --world data/world/v2_stage_2-4 --label 2026-10-14_vb24-V1 \
    --compare docs/bench/instruments/anchor_gauge/2026-10-14_2bc7a4b
# V2 の 11c・V3 の席・再開・2 日・系ごとの指紋
python docs/bench/analysis/wallbounce-1012/prox22/tools/reread_11c.py runs --label wt --modes distance,cell --geometries node \
    --world data/world/v2_stage_2-4 --out <作業用>/r11c.json && python …/reread_11c.py table --runs <作業用>/r11c.json --out $D/v2_reread_11c.json
python $D/tools/seat_probe_vb24.py --world data/world/v2_stage_2-4 --seat-release {walk,legacy}
python $D/tools/resume_vb24.py --world data/world/v2_stage_2-4 --scratch <作業用> --label VN --base {v3_mem_rel,w6_v3_default} --out …
python docs/bench/analysis/wallbounce-1012/ec21/tools/stage2_two_day.py side --world data/world/v2_stage_2-4 --out $D/v4_two_day.json
PYTHONHASHSEED=0 python docs/bench/analysis/wallbounce-1012/ec21/tools/probe_ec21.py side --label … --out …   # 写しの木で
python $D/tools/probe_systems_vb24.py --a <前の side> --b <後の side> --out $D/vN_probe_systems.json
# V6
python $D/tools/split_anchors_vb24.py split && python $D/tools/split_anchors_vb24.py check
```

## 検収の後の直し(2-4 の検収=条件つき受入・[review.md](review.md))

親の指示(高 H1・中 M1・低 L1〜L6・台帳の判断)で直した。L7 は台帳の判断(下の「つなぎの台帳」)・L8 はそのまま(締め-3 に書いてある)。

| 番 | 直したこと | 確かめ |
|---|---|---|
| **H1** | `tests/c7/test_presence_yardstick.py` の fixture `anchors` を「較正側のファイル(`presence_calib_anchors_v0.json`=中核 9 町丁目の 3 本)+検証側の**作り物**」に。作り物は鍵の名だけ検証側と同じ 6 本(`tools/c7/presence_yardstick.py` が `a[...]` で引く鍵=`pt_area_daytime_peak`・`night_presence_estimate`・`wake_rate_tokyo_weekday`・`attendance_rate`・`full_population` と、試験が名指す `homebound_boarding_time_dist_2015`)・`source: "synthetic(test)"`・値は試験の中で作る(起床率 a(h) の 0・3・12・23 時は試験のファイルに前から書いてある数に合わせ、ほかは作り物。assert は緩めていない)。CLI の試験は `--anchors` で fixture を渡す(前は既定の道筋=検証側のファイルを開いていた)。番人: 既定の道筋で錨を読もうとしたら検証側を無いファイルに差し替えて落とす(モジュールの autouse の fixture) | 検証側のファイルを開いたら止める監査フック(`sys.addaudithook`・ファイルの名だけを見る)をかけて回した: `-m "not gpu and not slow and not requires_data"` で本ファイル **16 passed**・開いた回数 0。`tests/c7` 全体 **166 passed・2 deselected**(世界の資産を読む写像表の 2 本)・0 回。CI-1 と同じ印 `-m "not gpu and not slow"` で `tests/c7` **168 passed**・0 回。負の対照: HEAD(`a231ef9`)の版の本ファイルは同じ印で **11 failed**(KeyError 10 本+CLI の試験が検証側のファイルを開こうとして監査フックで止まった 1 本)。`tests/c7` のほかのファイル(合成の holdout)と `tests/fig`(作り物の辞書)は錨のファイルを開かない(grep) |
| **M1** | `vb24/tools/activate_vb24.py` に `materialize --out <置き場>`(退避 `v2_pre_2-4` の置き換えた 11 本は退避から・変わっていない 93 本は本体の v2 から写し・活性化で足した 3 本は除く=W17 の jsonl は `stage` と同じく写さない → plan の「前」と同じかを確かめる・`--hardlink` は読むだけのランに限る)。**`v2_pre_2-4` は退避の差分だけ=前の資産そのものではない(エンジンの `--world` に渡せない)。前の資産でランを回すには `materialize` か `revert`**。`tests/engine/test_activation_2_4.py` に合成の置き場の試験 3 本(組んだ後の `verify --want before` が通る・退避のファイルが欠けたら止まる・置き場が空でない/本体が前とも後とも違うと止まる)。本物の資産を見る 3 本だけに `requires_data` の印(前はモジュール全体) | 本物で: `materialize --out <作業用>` → 退避から 11・本体から 93・除いた 3・build_hash **`5ff1bacf7fd9c773`**・`verify --live <置き場> --want before` 同じ・本体の v2 は `verify --want after` 同じ(書いていない)。その置き場+切替口 3 つを旧値(`SHIBUYA_PROXIMITY=cell`・`SHIBUYA_SEAT_RELEASE=legacy`・`SHIBUYA_ECONOMY_STAGE2=off`)で w6_v3_default を回すと **base と 25 欄とも同じ**(`5f7ae9ff24005314`/65,597=検収の記録 §4 のラン F と同じ) |
| L1 | 39 万体の金と物の輪の合計「約 246.6 MB」→ **246,522,344 B=約 246.5 MB**(224,678,592+12,482,144+9,361,608・M8 の約 1.0% は同じ)。本書の §0・§V4-1 と `docs/design/v2-budget-declaration.md` の 2-4 の行 | 和を検算した |
| L2 | 10e の byte-check の side に切替口の環境変数を書く欄 `env`(`SWITCH_ENV`=値に道筋やホストを持たない 11 個のうち設定されていたもの)・compare は `a`・`b` に写す。本段の切替口の比べの JSON 4 本([v2cell_vs_v1.json](v2cell_vs_v1.json)・[v3legacy_vs_v2.json](v3legacy_vs_v2.json)・[v2fix_vs_v2.json](v2fix_vs_v2.json)・[v4off_vs_v3.json](v4off_vs_v3.json))に `env` と `env_note`(後から書き足した)を足した | 4 本の値は回したときのコマンドの環境変数(`v2fix` は `SHIBUYA_SEAT_RELEASE=legacy`)。ほかの欄はバイトで同じ(足したのは 2 欄と注だけ) |
| L3 | 消した錨のファイル `hunger_energy_anchors_v0.json` を開く古い道具 3 本(`wave2-2026-09-30/meal_bundle_measure.py`・`energy-classical-2026-09-28/energy_measure.py`・`classical_measure.py`)を `energy.load_anchors()`(2 本を 1 つの辞書に戻す口)で読む形に。10e の docstring の head の写しの錨をエンジンが開く 3 本(空腹の 2 本+活動の事前分布)に | 3 本とも構文の読み込みが通り、引く鍵が合わせた辞書にある・`_anchors()` は `energy.load_anchors()` と同じ辞書(真偽だけ・値は出していない)。回してはいない(古い記録の道具) |
| L4 | 本書の頭の土台を `5f38e37` に・§0 の「活性化の前」の文を活性化の後の文に・§V1-2 に `materialize` の 1 行 | — |
| L5 | §V3-3 の表の下に 1 行(席の探りはテープなしのラン=final は byte-check と違う・呼数は同じ) | — |
| L6 | 締め-5 の「golden の 10 ファイル」→ 9 | — |

**つなぎの台帳**(`docs/design/bridging-ledger.json`・親の判断)

1. 外す段が 2-4 で active の 9 行の外す段を改めた(各行の `why` の末尾に「〔第334・2-4〕外す段を改めた(親)」=台帳に note の欄は無い・改訂の注は `why` の末尾に書く慣行): `W9#5`・`BR-SHADOW-NEAREST-DAY`・`EX-build.field.w12_external_nodes-f2cc7f0a` → **7**(窓の外の日・等間隔の推定の道は残る)/ `BR-PHONE-TABLE-BLANK`・`DOC-ec21-atm-fixture`・`DOC-ec21-atm-hours-and-cells`・`DOC-ec21-account-two-rows`・`DOC-ec21-consumption-pair-for-outside-sales`・`DOC-ec21-bank-branch-default-hours` → **4-2**。外す段が 2-4 で active の行は 0。`remove_basis` は `inferred` のまま(親の判断を決定の文に写したら `plan` に改める)。外す段を名指す試験 2 本(`tests/engine/multiday/test_md23_w9_window.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`)を合わせた。
2. 新しい行 `DOC-vb24-seat-not-released-on-board`(conf expedient・外す段 4-3・宣言は本書 §V3-3・関わるコード `engine/resolve.py`・`engine/seat_release.py`=乗車の歩き出しでは在席を解かない=版上げ 3 回目の候補)。台帳は 347 → 348 行(active 336 → 337)。`bridges_count`・`bridges_version` が動く(manifest の欄=byte-check の 25 欄の外)。台帳の行の数を固定した試験は無い(数は台帳から読む)。
3. 外す段が 2-1 で active の 10 行(変えていない=親が決める・2-4 の前から残る):

| 行 | 何の行か(台帳の what の頭) | 宣言の場所 |
|---|---|---|
| `BR-DOC-RESIDENT-CASH-ACCOUNT` | expedient: 居住者の初期現金も「来街者持込」科目で入れる。設計書 §2.2 の 12 科目に 「初期ストックの注入」に当たる科目が… | `src/shibuya/economy/ledger.py` |
| `HD-economy.anchors-1af925f4` | src/shibuya/economy/anchors.py の docstring の見出し「expedient(本モジュール分)」の下の… | `src/shibuya/economy/anchors.py` |
| `HD-economy.census-1af925f4` | src/shibuya/economy/census.py の docstring の見出し「expedient(本モジュール分)」の下の項… | `src/shibuya/economy/census.py` |
| `HD-economy.checks-1af925f4` | src/shibuya/economy/checks.py の docstring の見出し「expedient(本モジュール分)」の下の項… | `src/shibuya/economy/checks.py` |
| `HD-economy.entry_capital-cf8155f5` | src/shibuya/economy/entry_capital.py の docstring の見出し「expedient(本モジュール… | `src/shibuya/economy/entry_capital.py` |
| `HD-economy.goods-1af925f4` | src/shibuya/economy/goods.py の docstring の見出し「expedient(本モジュール分)」の下の項 … | `src/shibuya/economy/goods.py` |
| `HD-economy.ledger-1af925f4` | src/shibuya/economy/ledger.py の docstring の見出し「expedient(本モジュール分)」の下の項… | `src/shibuya/economy/ledger.py` |
| `HD-economy.pricing-1af925f4` | src/shibuya/economy/pricing.py の docstring の見出し「expedient(本モジュール分)」の下の… | `src/shibuya/economy/pricing.py` |
| `PR-shelf_stock_restock` | 世界過程 shelf_stock_restock(mechanism=False・executor=llm_agent・感度 AB-SHEL… | `src/shibuya/world/processes/first_batch.py` |
| `DOC-money-fare-cause-rail` | 運賃の移動(世帯 → 外界・持ち出し)の原因=過程 rail(Process("rail"))。乗車を決めた呼(LlmCall)ではない | `docs/bench/analysis/wallbounce-1012/cp2/README.md` |

**試験**(作業木・活性化の後の本体の資産・`PYTHONPATH` に作業木の `src`・`PYTHONDONTWRITEBYTECODE=1`)

| 何を | 印 | 結果 |
|---|---|---|
| `tests/engine/test_activation_2_4.py`(6)・`tests/engine/bridging`(49)・`tests/tools`(51)・`tests/economy`(281)・`tests/engine/multiday/test_md23_w9_window.py`(3)・`tests/engine/tools`(70) | `-m "not gpu and not slow" -n 4 --dist loadfile` | **460 passed**・failed 0 |
| `tests/c7`(監査フックつき=上の H1) | `-m "not gpu and not slow"`(CI-1 と同じ印) | **168 passed**・検証側のファイルを開いた回数 0 |
| 層の契約 `lint-imports --no-cache` | — | **5 kept・0 broken** |

## §親の検収(第334〜335・Fable 5.1・rebase の後)

- 本体 5f38e37 へ rebase(衝突 1=予算の宣言の同じ行への追記を親が両方残した。range-diff は V4 だけ「!」で他は「=」=review.md)。資産は親が活性化(`activate_vb24.py apply`・退避 `v2_pre_2-4`・`verify` 同じ)。範囲の試験(economy・proximity・systems・events・time・bridging・experiment・multiday・build_field/vis/audit・c8・活性化・在席・再開・状態台帳・10f・perception・llm・cli)**2,093 passed・1 xfailed**(12 分 49 秒)。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・資産は両側とも活性化の後の v2)=**final は 4 構成とも違う**(既定が動く段 V2 distance・V3 在席・V4 stage2 の分=情報として記録 `parent_head_vs_vb24_4cfg.json`・25 欄のうち同じなのは列の名と日付の類だけ)。旧値の再現は検収役の独立の再現(切替口 3 つ+前の資産=base と 25 欄同じ・`5f7ae9ff…`/65,597)と V8 の materialize の再現を根拠にする。動いた量は検収役が 5 本のランで段ごとに再現(呼数の差 −197/−765/−109/+2=記録と同じ)。
- 独立検収([review.md](review.md))=条件つき受入(高 1=tests/c7 の fixture が検証側の鍵を欠き CI-1 が赤になる見込み・中 1=退避は前の資産そのものではない・低 8)→ **V8(309d168)で全部直した**+親の判断(remove_at=2-4 の 9 行を 7 と 4-2 に・乗車の歩き出しの在席は 4-3 の行・切替口は版上げ 3 回目まで残す・remove_at=2-1 の 10 行は 4-2 の着手時に棚卸し・作り物の錨の `verified_by` は `synthetic(test)`=親が確かめた値ではない印)。親の試験: 作業木で 275 passed(tests/c7 の合成・活性化・台帳・道具)。**data 無しの写し(detached の作業木)で CI-1 と同じ印 `-m "not gpu and not slow"` の tests/c7・tests/tools・活性化・台帳=268 passed・6 skipped(data が要る印)・failed 0**=CI-1 の赤の見込みは消えた。
- 判定: **受入**(第 2 期 2-4 の完了=第 2 期 7 段が全部完了)。仮採用は PENDING §1-1b 仮-22(W9 のゲート 13 MB/日=案 A・energy.py が検証側を読む形は判断待ち・京王の行は活性化した資産に含む)。
