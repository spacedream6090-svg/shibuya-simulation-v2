# expedient 感度試験の台帳(実装計画書 §9.1 C8「各 expedient の『結果を駆動していない』証明」)

| id | 設計出典 | expedient | 実行形 | 状態 | JSD[bits] | 帰無95% | 判定 |
|---|---|---|---|---|---|---|---|
| S-W2-GRID | D-W2 | 格子原点(0,0)・100m・層3値(既決 R3-5) | build_rerun+run | 未実行 | — | — | — |
| S-W3-LAYER | D-W3 | OSM layer は描画順タグ(物理階層ではない)→ 層バンドへの写像 | build_rerun+run | 未実行 | — | — | — |
| S-W5-HEIGHT | D-W5 | levels×3.0 m の高さ推定・kind→既定階数表(事前宣言・PLATE | build_rerun+run | 未実行 | — | — | — |
| S-W6-ENTRANCE | D-W6 | 残り 7,194 棟の入口=建物重心から最寄り道路ノードへの決定論射影 | build_rerun+run | 未実行 | — | — | — |
| S-W7-ORGALLOC | D-W7 | 組織の建物配分則(v1 手続き生成・census 版 9,872 を正典) | build_rerun+run | 未実行 | — | — | — |
| S-W8-HOURS | D-W8 | カテゴリ既定営業時間・価格帯(cat×subcat 24 行)。OSM open | run | 未実行 | — | — | — |
| S-W9-BUFFER | D-W9 | 眼高 1.5 m・道路 8 m バッファ・2.5D 近似 | build_rerun+run | 未実行 | — | — | — |
| S-W10-SHADOW | D-W10 | 影グリッドの時刻刻み(宣言 5 分=正規化規約⑨と同刻み) | build_rerun+run | 未実行 | — | — | — |
| S-W11-AADT | D-W11 | tertiary 以下の klass→AADT 既定表(公的既定表なし=D-W1 | build_rerun+run | 未実行 | — | — | — |
| S-W13-CONCOURSE | D-W13 | 駅構内経路長=幾何距離×1.3(昇格条件=公式構内図からの実測) | build_rerun+run | 未実行 | — | — | — |
| S-W14-HOURUNIFORM | D-W14 | 時間帯配分=time_dist_12(2015)を 2018/2021 総量へ当 | build_rerun | 実行済 | 0.3007 | 0.0057 | ラン対照が要る |
| S-W14-JRPHASE | D-W14 | JR3 線・東急2 線・京王=等間隔ダイヤ(F10・実ダイヤはメトロ3 線のみ) | build_rerun | 実行済 | 0.0000 | 0.0011 | 駆動していない |
| S-W15-TEMP | D-W15 | 都市バイアス無補正(北の丸公園 ≠ 渋谷)・WBGT=推定式(環境省 API 実 | build_rerun | 実行済 | 0.0616 | 0.0042 | ラン対照が要る |
| S-W16-FLOOR | D-W16 | 町丁目→セル=住居系建物の床面積(area_m2×levels)按分 | build_rerun | 実行済 | 0.1239 | 0.0035 | ラン対照が要る |
| S-W17-T2 | D-W17 | 週次スケジュール生成のモデル=T1(Qwen3-8B INT8・温度 0.7) | build_rerun+run | 未実行 | — | — | — |
| S-W17-RAKE | RAKE_MAX_FRAC | raking の行数予算(固定 12% → 適応=ADAPTIVE_MODIFI | build_rerun | 実行済 | 0.0203 | — | ラン対照が要る |
| S-AB1-BUDGET | BUDGET_MODE | チャネル別トークン上限表の固定枠(§3.2・根拠なし行 約130 tok=470 | run | 未実行 | — | — | — |
| S-C7-BOUNDARY | E-C7-2 | セル→5 エリア写像(tools/c7/area_axes_v0.json=指針 | analysis | 実行済 | — | — | ラン対照が要る |
| S-C7-KINDATTR | KIND_TO_ATTR | 種別→KDDI 3 分類(勤務者/居住者/来街者)の写像 | analysis | 未実行 | — | — | — |

- **判定の読み方(片側)**: 構築対照の差が帰無参照以内 → 入力が動かない=**結果を駆動しえない**。超えた → 駆動する**かもしれない**=ラン側の対照が要る(構築段階だけで「駆動している」とは結論しない)。

- 世界過程の感度試験 id **22 本**は `--ablate <AB-*>` でそのまま切れる(実行形=run・状態=todo)。
- **親判断待ち**: 『結果を駆動していない』の合格線が設計書に無い(方法論は『振って結果非依存を示す』とだけ)。本台帳は帰無参照(同分布 2 標本の JSD 95% 点)を仮の物差しに置いた=expedient。
- **親判断待ち**: build_manifest の expedient 122 行のうち、設計書が感度試験を宣言しているのは 14 行だけ。残り 108 行の扱い(宣言を足す/限界として明記する)=親判断。
- **親判断待ち**: D-W8 だけが『感度(必須)』。他は必須でない=優先順位の根拠は §8 の ablation 優先規則(expedient の量 × 駆動可能性 ÷ コスト)を構築側にも当てるのが自然だが、設計書は当てていない。
