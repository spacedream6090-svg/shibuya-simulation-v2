# R-4b — v1 リサーチ資産の棚卸し(2026-09-15・第191)

<!-- hdr:v1 -->
- **分野**: 全分野にまたがる(索引そのもの) | **重要度**: P0(残務台帳 §1 のブロッキング R-4b)
- **一次確認**: **本文は読んでいない**。題名・行数・URL 数だけで仕分けた。**本書の判定は「当たりを付ける」ためのもので、採用の根拠ではない**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> ユーザー指示 09-15「今後リサーチをするってリストアップしていた分野のリサーチをして docs にまとめてほしい」。
> **この日は Web 検索・取得が使用上限で使えなかった**(WebSearch / WebFetch とも `You've reached your Fable limit.`)。
> そこで残務台帳が「**新規リサーチより安い**」と書いていた R-4b を先に実行した。v1 リポはローカルにあるので Web を必要としない。

---

## 0. 実数(親が数えた)

| | 本数 | 行 | URL 中央値 |
|---|---|---|---|
| v1 `docs/research/` **v1 固有** | **126** | 約 32,000 | **18** |
| v1 `docs/research/` の `v2-*` | 33 | — | **0** |
| v1 `docs/lit/`(1 論文 1 メモ) | **43** | 1,593(1 本 37 行) | ほぼ全件あり |
| v2 `docs/research/` | 73 | 18,691(1 本 256 行) | 09-02 以降 62 / 以前 0 |

**重要な確認**: v2 の D 等級 33 本は **v1 リポにも同名で存在し、そちらも URL 0 件**だった(親が 33 本すべて md5 比較・行差は末尾 2 行のみ)。
→ **出典はコピー時に落ちたのではなく、最初から無い**。[INDEX.md](INDEX.md) §1 の R-23 はこの確認を踏まえたもの。

---

## 1. v2 の穴に直接刺さるもの(優先順)

「v2 の穴」は [INDEX.md](INDEX.md) §2 の分野別索引で最良等級が低い/ゼロの分野。

### 1-1. 統計学・因果推論 #23 — **v2 の答申ゼロ**

**D-70(「速度でなく N を減らす設計」)が直接ここに依存する。**

| v1 資産 | 行 | URL | 何がありそうか(題名から) |
|---|---|---|---|
| `ablation-ladder` | 209 | 3 | **アブレーションの梯子 L0〜L4**。「LLM 由来の知的振る舞いが集団結果を生んでいるか」の検証装置。v2 の C8 ablation と同じ問題 |
| `analytics-methods` | 260 | **60** | 生データ処理・可視化 8 項目の標準手法 |
| `regression-signals` | 408 | 0 | 退行シグナルの定義・根拠・判定基準・較正手順 |
| `uncertainty-audit` | 213 | 0 | 不確実性の監査 + 運/実力分解。**UQ #22 の出発点**(第181 で確認済み) |
| `model-contrast-setup` | 171 | 12 | model×k 対照ランの実行構成 |
| `model-battery-design` | 373 | 4 | 人間らしさテストバッテリー |
| `pimmur-compliance` / `pimmur-results` | 162 / 290 | 6 / 0 | PIMMUR 6 原則の準拠監査と Unawareness 尋問テストの**実施結果**。残務 R-16 がこれを求めている |

### 1-2. 犯罪学 #32 — **v2 の答申ゼロ**

| v1 資産 | 行 | URL | |
|---|---|---|---|
| `crime-llm-cognition` | 259 | 37 | 犯罪は LLM の「判断」から起こせるのか。安全訓練済みモデルの逸脱バイアスと**構造派設計**。v2 の F-3 がまさにこれ |

### 1-3. 社会ネットワーク科学 #14 — **v2 は C 等級 1 本だけ**(会話 410/日 の直接の原因)

| v1 資産 | 行 | URL | |
|---|---|---|---|
| `initial-relations-improvement` | **921** | **104** | 初期関係構築の改善 — 手法比較・較正データ・実装順序案 |
| `relations-formation-map` | 562 | 0 | **関係値は誰が動かしているのか**の全経路マップ |
| `relationships-activities` | 426 | 30 | 家族・友人関係の再現と「**関係性に基づく共同行動**」。**待ち合わせの直系** |
| `community-detection` | 397 | 45 | コミュニティ検出とその時間発展 |
| `hierarchy` | 296 | 40 | 社会的ヒエラルキー(地位・信用・名声)。第3陣「評判と信頼の蓄積」の前身 |
| `social-simulacra-survey` | 403 | 82 | Social Simulacra 分野サーベイ |
| lit `network__diffusion-overview` | 22 | あり | **親が実読した**。Centola & Macy 2007 の complex contagion(行動・規範は 1 接触で伝わらない)/ Granovetter 1978 閾値 / Watts 2002 カスケード |

### 1-4. R-5 可視化(残務台帳のブロッキング)— **v1 に 3,000 行超・URL 500 件超**

| v1 資産 | 行 | URL | |
|---|---|---|---|
| `dt-snapshot-reproposal-notes` | **1,178** | **170** | **スナップショット型デジタルツイン**の再導出ノート。CLAUDE.md §3「DT 定義=現実のある時点のスナップショット」の出所と思われる |
| `dt-integration-deep` | 825 | 90 | 企業 DT / 3D シミュレーション × 社会シムの結合経路 |
| `shibuya-3d-highfidelity` | 561 | 61 | 高精細な渋谷 3D モデルの入手可能性・ライセンス・統合方法 |
| `dt-landscape` | 447 | **119** | デジタルツイン/3D 業界の大枠調査 |
| `3d-movement` | 386 | 74 | エージェント移動の 3D 地理精緻化 |
| `3d-visualization` | 179 | 34 | Blender / PLATEAU / Web3D |
| `physics-engine-selection` | 718 | 18 | 局所物理エンジンの選定(**実測比較**) |
| lit `viz__plateau-pipeline-overview` | 17 | あり | PLATEAU SDK for Unity / sim⇄viz 疎結合 I/F |
| lit `urban__lynch1960_image-of-the-city` | 15 | あり | Lynch の 5 要素。**何を描けば街に見えるか**の理論側 |

→ **ユーザーの 3D 質問(第177・第185)と可視化(水曜)の材料はほぼ全部ここにある。**Web なしで読める。

### 1-5. D-70 計算資源 — **同じ 7 GPU での試算が v1 にある**

| v1 資産 | 行 | URL | |
|---|---|---|---|
| `scale-feasibility` | 233 | 10 | **何体を何日/日で回せるか(vLLM 7GPU 試算)**。いまと同じ構成 |
| `compute-efficiency` | 207 | **70** | 「少ない計算で現実の人々を再現する」技法の棚卸し。**中心仮説そのもの** |
| `dt-reduction` | 237 | 24 | Δt 短縮(10 分→5/1 分/30 秒)の実現可能性・**呼数不変設計** |
| `multi-model-lod` | 323 | 47 | 一度のシムで複数 LLM を使い分ける |
| `agent-lod-deepdive` / `lod-fluidity` | 190 / 235 | 32 / 0 | 前景=高計算/背景=低計算 |
| `token-budgets` | 178 | 18 | LLM 社会シムのトークン予算の相場 |
| `longrun-estimate` / `scale-audit-100days` | 161 / 244 | 0 / 0 | 30 日級・100 日級の実行見積り。**第3陣の時間スケールに直結** |
| lit `mas__yang2024_oasis` | 20 | あり | **親が実読した**。OASIS の実測 **1M 体×1step = 18h / A100×27**・100k×1step = 3h / A100×5。第190 の比較表に 3 例目として入る |

### 1-6. 歩行者動力学 #18 / R-7(CFSM 着手時の義務)

| v1 資産 | 行 | URL | |
|---|---|---|---|
| `p4-calibration-search` → `p4-calibration-research` | 547 | 39 | **歩行物理層の較正**の実装前文献リサーチ |
| `crowd-attention-physics` | 329 | 27 | 群衆物理の認知二層化 |
| `social-force-crowd` | 224 | 25 | Social Force Model 導入の文献・実装調査(スクランブル交差点) |
| `pedestrian-signals` | 252 | 6 | 歩行者用信号の実装調査 |
| `crowding-dissatisfaction-empirics` | 107 | 22 | 混雑と客満足の実証 |
| `vision-los` | 119 | 0 | 擬似視覚(壁による遮蔽) |

### 1-7. 都市代謝論・MFA #19(残務台帳が「ほぼ無い・新規リサーチ」と判定していた分野)

**訂正の可能性**: 第181 では「ほぼ無い」としたが、題名で見る限り**素材はある**。ただし主題が「廃棄」ではなく「物の移動・所有」。

| v1 資産 | 行 | URL | |
|---|---|---|---|
| `economy-goods-services` | 474 | 23 | 経済活動の「物の移動」と具体的サービスの実体化 |
| `ownership-asset-models` | 275 | 38 | 所有・資産モデル |
| `retail-inventory-empirics` / `retail-margins-empirics` / `retail-pricing-empirics` | 72/61/61 | 0/16/22 | 在庫・マージン・価格改定の実証 |
| `economy-abm-research` | 411 | 27 | ABM 経済回路・LLM 経済エージェント |
| `ifE2-org-accounting-research` | 522 | 18 | org の会計主体化 + rest-of-world(域外)概念 |

### 1-8. R-4 ミクロ観察の先行例(残務台帳のブロッキング)

| v1 資産 | 行 | URL | |
|---|---|---|---|
| `metaverse-observable-data` | 192 | **113** | メタバース事業者の観測可能データと**内部状態復元の境界** |
| `emergent-events-and-narrative-ui` | 316 | 0 | 創発イベントの内生化と**物語 UI** — 前例調査+設計案 |
| `observation-commercial-data` | 63 | 0 | 観測したら面白い/商業的に活かせるデータの提案 |
| `sim-improvement-analysis` | 197 | 0 | 既存ランのデータ駆動診断 |

### 1-9. 第3陣(時間スケールの拡張・第189)

| v1 資産 | 行 | URL | 第3陣のどの行か |
|---|---|---|---|
| `population-endogenization` | 215 | 82 | **人口の転入転出**(生成・消滅を行動由来に) |
| `presence-endogenization` | 317 | 39 | 在場の内生化 |
| `rights-institutions-gap` | 246 | 26 | **制度の創発**(現実の権利・制度との差分) |
| `shibuya-government` | 121 | 8 | **税・行政サービス**(第3陣の 3 行のうち 1 行そのもの) |
| `hierarchy` | 296 | 40 | **評判と信頼の蓄積** |
| `world-change-motivation` | 235 | 0 | 「世界を変えたい」モチベーションの実証分析。**v1 の中心の問い** |
| lit `labeling__cultural-evolution-overview` | 24 | あり | **語彙と文化の変化**(ラベル創発 / semantic drift) |
| lit `collective-action__institutions-framing-overview` | 30 | あり | 集合行為・制度経済学 |

---

## 2. 読み替えが要るもの(v1 の文脈が v2 と違う)

- **v1 の問いは「世界改変者の創発」**(`world-change-motivation`・`labeling`・`hierarchy`)。v2 の第一目標は「世界そのものがプロダクト=再現」。**同じ資料でも読む向きが逆になる**ことがある。
- **v1 は 1 万〜数万体・100 日**、v2 は **40 万体・1 日**。スケールの見積りはそのまま使えない(`scale-audit-100days` など)。
- **v1 は SNS/物語 UI を持っていた**。v2 は持たない。`emergent-events-and-narrative-ui` は設計案の部分だけ。

## 3. v1 固有で持ってこないもの(親の判定・題名から)

エンジン実装の記録(`engine-baseline` / `engine-coverage-map` / `legacy-sim-review` / `framework-architecture` / `off-features-inventory` / `sv-items-research` / `sv-remaining-items-research` / `if-lane-research` / `llm-world-interface-audit`)・v1 の運用記録(`server-deployment` / `finals-backup-reliability` / `finals-llm-budget` / `org-book-11k` / `org-book-census` / `persona-pool-1m`)・v1 固有のデータ作業(`lexicon-ipf-shibuya` / `economy-census-calibration` / `poi-reality-check`)。
lit 側では `gamification__extrinsic-reward-overview`(CLAUDE.md §3「ゲームは作らない」)・`behdesign__fogg-nudge-overview`(ナッジ=設計者の指紋)・`bizeco__business-ecosystem-overview`・`infra__*` 4 本(v1 のインフラ決定)。

**ただしこれは題名だけの判定**。捨てる前に 1 度は開くこと。

---

## 4. 次の手(順序つき・すべて Web 不要)

1. **lit 層への複写 6 本**(最優先・v2 の穴に直接刺さる):
   `network__diffusion-overview`(#14)/ `method__experiment-design-statistics`(#23)/ `measurement__validation-overview`(#26)/ `mas__yang2024_oasis`(#25・第190 の比較表)/ `labeling__cultural-evolution-overview`(第3陣)/ `urban__lynch1960_image-of-the-city`(可視化)
2. **R-5 可視化の 6 本を通読**(3,000 行)→ 第177 M2 の段階案を書く。**水曜の可視化判断の材料**
3. **D-70 の 3 本を通読**(`scale-feasibility` / `compute-efficiency` / `dt-reduction`)→ 2 h/シミュ日 が届く数字かを v1 の実測で照合
4. **#23 の 7 本**→ 統計学・因果推論の答申を起草(v2 でゼロの分野を埋める)
5. **`crime-llm-cognition`**→ #32 を埋める(F-3)

## 5. この文書の限界(次のエージェントへ)

- **本文を 1 本も読んでいない**(lit 2 本を除く)。行数・URL 数・題名だけの仕分け。
- したがって「ありそうか」欄は**推測**。中身が v2 に使えるかは開くまで分からない。
- v1 資産の一次確認の状態は**未評価**。v1 も 43 本が URL ゼロ(126 本中)。v2 と同じ等級付けはしていない。
- 第181 で「物質フロー分析は v1 にほぼ無い=新規リサーチ」としたが、§1-7 のとおり**素材はある可能性**がある。主題が違うだけかもしれない。**要確認**。
