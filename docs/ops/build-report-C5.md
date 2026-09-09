# 受入報告 C5(母集団・生成)— 進行中(2026-09-09)

> 形式は build-report-C0〜C4 と同じ: 親(Fable)が自分で実行した出力のみを証拠とする。サブの完了報告は証拠にしない。
> ブランチ `build/c5-c8`(main d413d61 から)。/goal C5〜C8 通し(docs/ops/goal_c5_c8.md)。

## 0. 構成

| 部分 | 内容 | 実装 | 状態 |
|---|---|---|---|
| C5-a | W16 母集団合成(build/pop・agents/population・エンジン結線)+D-13 店舗参入資本の経済センサス按分(economy/entry_capital) | サブ J・サブ K(Opus) | 親検収=済(§1・§2)・層2=実施中 |
| C5-b(コード) | W14 看板(a)文面・W15 B2 セル静的文の段階コード(build/lang・renderer 結線) | サブ L(Opus) | 実装完了・親検収=未(RUN_ORDER 統合後) |
| C5-b(生成) | W14 2,337 店×2 回・W15 520 セル×2 回を Qwen3-32B-AWQ(TP2・温度0・seed 20260909)で生成→ingest・凍結 | 親(tools/gen/fleet_gen.py・サーバー) | 生成中(09-09 09:37 開始) |
| C5-b(W17) | 週 7 日活動表(390,188 呼・8B INT8 DP7・温度 0.7・seed=hash(agent)) | サブ N(段階コード)+親(生成) | 段階コード実装中 |

## 1. C5-a W16 母集団合成(親検収・2026-09-09)

**再構築(親実行)** `PYTHONUTF8=1 .venv/Scripts/python.exe -m shibuya.build.run --out data/world/v2 --data data`

```
[W16]  11.26s  outputs=6  gates_pass=True
W16 | pool_inventory_matches_meta    | True       | True   | PASS
W16 | chome_jinko_match              | 80         | 80     | PASS   (dbf JINKO と e-Stat 総数が 80 町丁目で一致)
W16 | srmse_sex_resident             | 3e-06      | <0.01  | PASS
W16 | srmse_age_resident             | 0.000143   | <0.13  | PASS
W16 | srmse_sex_worker               | 4e-06      | <0.01  | PASS
W16 | jsd_direction_max              | 0.00084843 | <0.01  | PASS
W16 | empty_residential_cells        | 0          | 0      | PASS
W16 | residents_without_home_cell    | 0          | 0      | PASS
W16 | worker_seats_filled            | 222849     | 222849 | PASS
W16 | households_cover_all_residents | 43588      | 43588  | PASS
W16 | n_agents                       | 390188     | -      | PASS
build_hash = 0100706bcaf010788d00c1019981812e44d4a501a20c1f18e6574d84b264ae9b(サブ J 報告値と一致=再構築一致)
残る FAIL 3 本は C1 由来の既知(W9 影容量・W10 区間突合・W10 較正残差=PENDING D-1/D-2)
```

**体数(40 万は目標でなく結果=390,188)**: 住民 43,588(区の公的値×セル被覆率・D-20)/通勤 215,893/通学 33,385/定期来街 20,000/業務来街 17,862/来街 58,144(訪日 17,404)/乗務・職務 1,258+議員 34/指令 24(expedient)。

**予算**: w16_population.parquet 4,610,711 B=11.8 B/体(zstd)・AgentState 121 B/体(M1 30,000 B の内数)・合成の壁時計 ≈11 s・RSS 720 MB。

**エンジン結線(親実行)** `python -m shibuya.cli --agents 5000 --seed 1 --world data/world/v2` ×2:

```
壁時計 16.84s / 16.70s (W2 上限 600s) / 移動+密度 0.121 ms/tick (P2 上限 5 ms)
保存則 Σmoney 33,948,683 + Σrevenue 1,082,100 + Σ運賃 33,300 = 35,064,083 (初期 35,064,083) OK / 最小在庫 0
2 回のサマリ(ハッシュ行)一致 = T2
```

**テスト(親実行)**: `pytest -q -m "not gpu and not slow" --ignore=tests/build_lang` 全合格(tests/build_pop 28 本を含む)・`lint-imports` 5 kept / 0 broken・`scan_secrets` 41 ファイル CLEAN・`git ls-files data`=0。

## 2. C5-a D-13 店舗参入資本(親検収)

- 式: 参入資本=経済センサス2021 産業大分類別「1 事業所当たり年商」÷365×k(30 日・expedient)×原価率(goods.CATEGORY_K の逆数)×ρ(n/400,000)→1,000 円切り捨て・clip[10,000, 50,000,000]。注入は従来どおり外界→店舗 transfer(ENTRY_CAPITAL)=ex nihilo 禁止不変。
- 親実行(5,000 体・実データ): `[参入資本] 店舗の現金+預金 287,368,938 円 / 貨幣供給 321,317,621 円 = 89.43%`(C4 の一律 200,000 円=93.02% から低下・世帯財布が mock のままなので残りは C5 後半で)。
- `pytest -q tests/economy tests/test_cli.py` 108 passed。
- 発見(D-16): 境界経済設計書 §2.5・anchors.SALES_PER_ESTABLISHMENT の年商が生値の 1/10(転記誤り)。実装は生値。設計書側の訂正はユーザー判断。

## 3. 層2 独立検収(別インスタンス Fable)

**判定=合格(09-09・重大 0/中 4/軽 9)**。層2 が自分で実行: pytest 1,165 passed・0 skipped(実データ試験 11 本が実際に走った)・lint 5 kept・scan CLEAN・build.run ×2 で build_hash と w16_population.parquet の SHA(4a2ff2d9…)が一致・cli ×2 で final_hash f2cf8d8f… 一致・`git diff main -- docs/design/`=71 insertions/0 deletions(追記のみ)。
- 中(次工程): ①定員先取り層が L5 全件 1,316 体=5,000 体ランの 26%(答申 §6-b の「最小定員≈300-400」より大) ②e-Stat 年齢表は抽出側で 14 階級に切れていた(親が 09-09 に全 60 分類を再取得済み→W16 の raking を 16 階級へ) ③層境界を跨いで写した定数(KIND_*/AGE_EDGES/RESERVED_*)の等価テストがない ④W16 の再構築一致は CI(data なし)では走らない(W0-W13 と同じ制約)。
- 軽: 登録簿の日末比率 89.46%→実測 89.43%・Checkpoint.combined の連結形変更(旧 golden 無効)・RUN_ORDER 断定の緩め・`--no-population` は engine.run のみ・coverage_fraction 死蔵候補 ほか。
- 親の対応: ①③=サブ M(次コミット)・②=データ再取得済み→サブ M・④=D-W20 との差を登録簿に記録。

## 4. C5-b(追記予定)

- W14/W15: 生成ログ・ingest ゲート(rep 一致率・固有名詞検査・不合格率)・凍結 SHA。
- W17: プロンプト SHA・呼数・出力 tok 分布・JSD・修正率・壁時計。
- W18 再算出。

## 5. ユーザー判断へ回した事項

PENDING D-16〜D-21(anchors 1/10・office 写像・W15 45 tok・実店名 vs 架空・空間支持・KIND_WORDS テンプレ改版)。
