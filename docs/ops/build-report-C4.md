# 工程 C4(世界過程第1陣+経済+物)受入報告(進行中・2026-09-08・ブランチ build/c0-c4)

> 根拠: 実装計画書 §9.1 C4 行(16行の第1陣+U-Goods 骨格+前倒し分+U11 SFC(transfer 単一API・検算2本・pytest 8本・faucet/sink 列挙・月次センサス)+憲法5 機械検査。検収=保存則テスト全合格・センサス残差閾値内・憲法5 機械検査)。証拠=親自身の実行出力のみ。

## 1. 経済側(サブG: economy accounts/ledger/goods/checks/census/pricing/anchors + engine/ledger_api + resolve/run 結線)= 親検収済み

```
$ .venv/Scripts/python.exe -m pytest tests/economy tests/engine/test_ledger_wiring.py -q → 90 passed in 13.88s
$ pytest -q (全体) → 836 passed, 1 xfailed in 106.65s
$ lint-imports → 5 kept, 0 broken(economy は engine.ledger_api の Protocol のみ・engine→economy なし)   $ scan → CLEAN
```

| 受入項目 | 実測 | 判定 |
|---|---|---|
| transfer 単一API(残高直接代入の静的禁止・科目 enum 外は実行不能・部門対の許可表=faucet/sink 1:1) | AST 検査+テスト | 済 |
| 検算①(行和 0・列和=Δ現金・Δ預金−Δ借入=0)/検算②(Σ純資産=実物資産・毎期 O(N)) | 5,000体×1日で毎 checkpoint 成立 | 済 |
| ex nihilo 禁止・残差閾値・退蔵測度・faucet/sink 科目別集計・日次軽量センサス+月次 MER 骨格 | テスト合格(pytest 8本相当を含む 77本) | 済 |
| 物の保存則(move_goods 単一API・SKU 別 期首+流入−流出=期末・棚卸差異・退蔵・廃棄 band=区ごみ 119.6 t/日) | テスト合格・resolve に restock/consume/collect_waste 入口 | 済(担い手行動は subH) |
| 価格形成(H-1〜H-5 のエンジン側: 内生フロア k 2.9/3.3/5.0・Calvo 業種別・r クリップ[0.7,1.5]・逸脱比例コスト sink) | 純関数+テスト | 済(LLM の r は C6) |
| 結線の中立性・性能 | 同 seed 同ハッシュ(台帳あり/なし)・W2 4.2 s(変化なし)・P2 0.075 ms | 済 |

設計との食い違い(サブG 報告→親裁定): 減価償却の相手方なし=自己ループ受理/退蔵項=測度/逸脱比例コスト=15 番目の科目/初期財布の科目なし(CARRY_IN で代用=誤ラベル)/列和=Δ現金/日次センサスの拡張/物の内部移動科目 3 追加=**いずれも PENDING(科目表の delta・ユーザー承認)**。numpy `np.add.at` が読み取り専用フラグを無視する穴=台帳側は防御済み・engine 側は C3 結線で静的検査を追加。

## 2. 世界側台帳(サブH-1: WorldProcess/PlanSpec/ActualLog 型・関係4・憲法5 機械検査・第1陣の宣言)= 親検収済み

```
$ pytest tests/world/processes -q → 113 passed   (全体 975 passed, 1 xfailed)   $ lint-imports → 5 kept   $ scan → CLEAN
第1陣の宣言: 過程 21(llm_agent 9/none 7/engine_rule 5)・フォールバック台帳 5 行・カタログ被覆(宣言)23/57・registry_hash 1a5fcb8c…・憲法5 検査 OK(実文書の id: 知覚チャネル 15/パターン台帳 48/観測出力 5)・削除候補 0
```
矛盾4件(B3 チャネル行なし/封印 S3 の参照/§1 vs §7.2 の線引き/台帳行数の記述)=PENDING。expedient は §8 C4 世界側台帳節。

## 3. 世界過程の挙動(サブH-2: 昼夜/天候/鉄道運行/混雑場/営業時間/騒音場+補充/納品/廃棄物収集/屋内占有/断面交通+前倒し分)= 未着手
