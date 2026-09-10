# 受入報告 C8(ablation 第1陣・expedient 感度試験・忠実度計器盤・アンサンブル)— 進行中(2026-09-10)

> 形式は build-report-C0〜C7 と同じ: 親(Fable)が自分で実行した出力のみを証拠とする。サブの報告は証拠にしない。
> ブランチ `build/c5-c8`。実 LLM の腕はサーバー(SSH エイリアス・7×A5000・Qwen3-8B INT8)で 5,000 体×1,440 tick。

## 0. 構成

| 項目 | 内容 | 状態 |
|---|---|---|
| 基盤 | tools/c8(c8lib・ablation_runner+ablations_v1.json・sensitivity+sensitivity_v1.json・dashboard・ensemble)・tests/c8 105 本 | サブ T(第121・親検収 105 passed) |
| 切替口 | ② `--pnotice-d50-scale`・③ `--refractory-scale KEY=F`・⑥ `--no-signage`(①は C6 の `--budget-mode`) | サブ U(第122・親検収=mock 実資産 checkpoint d5d79337… 不変) |
| ランナー修正 | FleetClient をランごとに生成・`--fleet-wait-s`(既定 120) | 親(第128b・初回実行の失敗 2 件を修正) |
| 感度試験 | 構築段階で測れる 5 件を親が再実行 | 第127d(サブ T の値を完全再現) |
| 計器盤 | tools/c8/dashboard.py を C7 暫定受入 JSON でドライラン | 面3 赤 0・面2 は holdout 未照合で「—」 |

## 1. 受入項目(§9.1 C8「各 expedient の『結果を駆動していない』証明」)と結果

| 項目 | 基準 | 結果 |
|---|---|---|
| ablation 第1陣 6 本 | 知覚契約書 §8 の 6 腕(20% 予約枠) | **回せるのは 4 本**: ①固定枠/ランキング・②p_notice d50・③近接不応期・⑥広告ゼロ。④聴覚 SNR・⑤日次内省は前提機能が第2陣(blocked_feature・D-45)。②は A4 既定で距離項に槓桿なし・③は PROXIMITY_SWAP を出す過程が未実装で no-op(D-49)→ **実 LLM で回すのは ⑥→①**(下記 1b) |
| 広告ゼロ | AD1 封印行の裏=看板行を全セル空にして行動分布の JSD | ⑥ 実行中(09:20 起動) |
| expedient 感度試験 | 「結果を駆動していない」証明(片側) | 構築段階 5 件を親再実行(1a)。**残り 108 行は未宣言**(D-44) |
| 忠実度計器盤 | R14 G-1 の 3 面・ゲートは面2 のみ | ドライラン済(1c)。面2 は holdout 照合とアンサンブル分散が入るまで判定なし |
| アンサンブル運用(Phase 5) | seed 複数本で幅を出す | 設計(tools/c8/ensemble.py・k* 凍結ファイル未作成=D-40/D-46: 5,000 体で回す) |

### 1a. expedient 感度試験(親再実行・09-10 08:28・`python tools/c8/sensitivity.py --run all --include-heavy --out docs/bench/c8`)

| id | 設計出典 | expedient | JSD[bits] | 帰無 95% | 判定(片側) |
|---|---|---|---|---|---|
| S-W14-HOURUNIFORM | D-W14 | 時間帯配分=time_dist_12(2015)を 2018/2021 総量へ当てる | **0.3007** | 0.0057 | ラン対照が要る |
| S-W14-JRPHASE | D-W14 | JR3 線・東急2 線・京王=等間隔ダイヤ | **0.0000** | 0.0011 | **駆動していない** |
| S-W15-TEMP | D-W15 | 都市バイアス無補正・WBGT 推定式 | **0.0616** | 0.0042 | ラン対照が要る |
| S-W16-FLOOR | D-W16 | 町丁目→セル=住居系床面積按分 | **0.1239** | 0.0035 | ラン対照が要る(TVD 0.297=住民の 3 割が別セル) |
| S-W17-RAKE | RAKE_MAX_FRAC | raking 固定 12% → 適応 | Δ0.0203 | —(決定論) | 固定 12% で 0.40085/0.21168=登録簿の値を再現 |

判定の読み方: 構築対照の差が帰無参照(同分布 2 標本の JSD 95% 点)以内なら入力が動かない=結果を駆動しえない。超えたら「駆動するかもしれない」=ラン側の対照が要る(合格ではない)。出力 docs/bench/c8/sensitivity_v1.{json,md}(第127d)。サブ T の値(第121)と 5 件とも一致。

### 1b. ablation 第1陣(実 LLM・5,000 体×1,440 tick・seed 1・温度 0.7・max_tokens 96・fleet_wait 120)

| 腕 | 構成 | 状態 | 結果 |
|---|---|---|---|
| ⑥ AB6-AD-ZERO | signage_on(baseline)/signage_off | 実行中(09:20〜) | (追記予定) |
| ① AB1-BUDGET-MODE | fixed_slots(baseline)/single_ranking | 待ち | (追記予定) |
| ② AB2-PNOTICE-D50 | d50 ×0.5/×1.0/×2.0 | 回さない | A4 既定で到達 10,736/10,736/10,737(実資産 2,000 体×90 tick 下見・D-49)=距離項に槓桿なし。A1 併用の距離感度として再定義(判断待ち) |
| ③ AB3-REFRACTORY-PROX | PROXIMITY_SWAP ×0.5 | 回さない | 起床候補に PROXIMITY_SWAP を出す過程が §9 第2陣で未実装=no-op(D-49)。切替口は CELL_BLOCK で実証 |
| ④ AB4-HEARING-SNR | — | blocked_feature | 聴覚チャネルの SNR 機能が第2陣(D-45) |
| ⑤ AB5-INTROSPECTION | — | blocked_feature | 日次内省が第2陣(D-45) |

初回実行(09:05)は 2 腕とも 2 分で落ちた: (1) 1 つの FleetClient を baseline と腕で共有→run_day が終わりに閉じる→2 ラン目「close() 済み」(2) fleet_wait_s 未指定→非ブロッキングで 1,440 tick を駆け抜け応答がほぼ繰り延べ。第128b で修正し 09:20 に再起動。

### 1c. 忠実度計器盤(ドライラン・C7 暫定受入 JSON)

`python tools/c8/dashboard.py --accept <c7_accept.json> --out <scratch>`: 面3(運用)=W1/M8/S1/L4/DIAG/CONS/CONST-5/WC-6 が PASS・赤 0 件。面2(holdout)=照合「—」・開封記録なし・k* 凍結ファイル未作成・I_M 未計算(アンサンブル分散が要る)。面1(較正)=W0-W20 の構築ゲート表(W9 1 件・W10 2 件の不合格は C1 の記録どおり)。最終版は C7 の holdout 照合後に `docs/ops/dashboard/` へ出す。

## 2. ログ(追記予定)
