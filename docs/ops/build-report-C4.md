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

## 3. 世界過程の挙動 前半(サブH-2a: runner・昼夜/天候/体感温度・鉄道運行・営業時間 PlanSpec・混雑場/屋内占有・断面交通)= 親検収済み

```
$ .venv/Scripts/python.exe -m shibuya.engine.run --agents 5000 --seed 1 --world data/world/v2
壁計 13.19 s(≤600 s)/ P2 0.096 ms / LLM呼 56,488 = 11.30 呼/体/日(**L4 制御目標 10 を超過→後半で上限厳守へ**)
保存則 Σmoney+Σrevenue+Σ運賃 = 35,064,083 OK / 世界過程 台帳 1a5fcb8c… 憲法5 OK / 再生日 2026-07-28 / 乗車 169 降車 0 / ActualLog 10,635 行 遵守率 0.386
過程別[s]: crowd 0.141 / environment 0.024 / opening 0.009 / rail 0.064 / traffic 0.002
$ pytest(全体)→ 1,055 passed, 1 xfailed, 1 failed(core.types.max_tick の境界=親が修正)   $ lint-imports → 5 kept   $ scan → CLEAN
```
列車 4,089 本/日(井の頭 760/田園都市 760/東横 680/山手 508/埼京 508/銀座 325/半蔵門 289/副都心 259=W12 平日行と一致)・乗客保存(4,831+0+169=5,000)・開店イベント 6,546(役割行動 17/フォールバック 6,529)・待ち行列は席数 84,761 vs 購入 1,600/日で未発火(単体テストで被覆)・車両 km 566,670/日。
矛盾(親裁定): §2.6 実効容量 2 種→二層(PENDING)/line_capacity_12 は src 不可→§2.6 引用値/build 不可→転記/流れ 3 値/B4b 未結線→後半/降車 in situ 0→PENDING/売却の単一スロット不具合→後半で経済側修正。

## 4. 世界過程の挙動 後半(サブH-2b: 補充・納品・廃棄物収集/前倒し9過程/顕著行為+p_notice 結線/センサスゲート/L4 上限厳守)= 親検収済み

```
$ .venv/Scripts/python.exe -m shibuya.cli --agents 5000 --seed 1 --world data/world/v2   (台帳つき・親が新設した層外入口)
壁時計 12.80 s / LLM呼 **50,000 = 10.00 呼/体/日**(修正前 56,488=11.30・上限=憲法1 監査点) / 保存則 Σmoney+Σrevenue+Σ運賃 = 35,064,083 OK
世界過程 21 過程(第1陣 12+前倒し 9)・憲法5 OK・ActualLog 31,088 行・遵守率 0.549
C4後半: 補充 20 / 納品 2,337 / 宅配 5,716 / バス到着 12,954 / ホテル泊 2 / 顕著行為 0(seed 1・Poisson 平均 1.5/日=P(0)22%・seed 2-5 で 1-3 件) / 廃棄 1.301 t/日 (band 83.7-155.5) NG=規模 1% の帰結
日次センサス(§2.4): 残差 0 / 貨幣供給 502,411,562 / 棚卸差異 0 / ゲート PASS
$ pytest(全体)→ 1,119 passed, 1 xfailed(+cli 2)   $ lint-imports → 5 kept   $ scan → CLEAN
```

| 受入項目(§9.1 C4) | 実測 | 判定 |
|---|---|---|
| 保存則テスト全合格(金: 全部門 Σ=0・運賃込み/物: SKU 別 期首+流入−流出=期末) | 合格 | 済 |
| センサス残差閾値内(日次センサス+ゲート) | 残差 0・棚卸差異 0・PASS | 済 |
| 憲法5 機械検査(reaches/contributes・削除候補) | OK・削除候補 0・registry_hash 1a5fcb8c… | 済 |
| 第1陣 16 行(1-3 移動/占有/時計=C2・4 売買保存則・5 価格エンジン側・7 会話・15 記憶減衰は C5・16 未定義)+D-R2-5 の 6 過程+U-Goods 骨格(補充/納品/廃棄/屋内占有/断面交通)+前倒し 9 | 実装+テスト(1,121) | 済(行 6/8-14 は第2陣) |
| L4 上限(4M 呼/日 相当) | 50,000/50,000 | 済(修正) |
| W2/T2 | 12.8 s・同 seed 同ハッシュ | 済 |

サブH-2b の矛盾 9 件(親裁定): B5 気づき行=テンプレ改版判断(PENDING)/納品支払い=棚入れ時(登録)/在庫置場節点なし(PENDING)/補充フォールバック行=台帳追加(PENDING)/バス停座標なし(PENDING・再取得)/B3 行なし(既出)/B4b と §6(i)(PENDING)/台帳の有無で世界が変わる(テスト範囲を限定)/補充・開閉店はフォールバック支配(C5 で従業者が店に付くまで)。

## 5. 層2 独立検収(別インスタンスの Fable)

**判定: 不合格(修正1点で合格)→ 修正を反映(C4-fix)**。レビュー役の実行: 1,121 passed/lint 5 kept/scan CLEAN/`shibuya.cli` 実データ 2 回=最終ハッシュ一致・呼 50,000=自算の上限ちょうど/独立検算: Σ現金(外界込み)=0・行和 0・列和=Δ現金・検算② 40,965,919=40,965,919・残差 0・ex nihilo OK・SKU 別 diff 0・棚と写しの一致・禁じ手(未知科目/禁止対/直接代入/窓外 transfer)は全て拒否/憲法5 を実文書の id で再実行=OK(過程 21・削除候補 0)/id の双方向照合/鉄道 8 線の便数=W12 一致/顕著行為 seed 2 で発火(事象 6・気づき 63・出動 3)/`git diff main -- docs/design/`=追記のみ(+115/−0)。

| 指摘 | 処置 |
|---|---|
| **日次センサスが台帳を畳んだ後の空行列を評価**(faucet/sink/waste=0 で PASS=空振り。閉じた日で再計算すると残差 0・閾値内) | C4-fix: DayClose を保持してセンサスに渡す・空振りしていたテスト 2 本を修正・faucet/waste の実値を固定 |
| D-R2-6 ラン終端ゲートが O(t) ログ(ActualLog 31,088 行・transfer_log・納品ログ 4,418 行)を実測しない | C4-fix: 各モジュールの成長宣言で実測を追加 |
| §2.6(iii)乗り残し率の診断行なし・(ii)未実装 | C4-fix: (iii)追加・(ii)は注記(5,000 体では発火せず) |
| 陳腐化した注記(goods.py の払い出し規則・crowd.py の B4b 未結線)・has_permission の死にコード・便数照合が片方向 | C4-fix |
| expedient 未登録 12 件 | §8 へ追記済み |
| 廃棄 band=規模非依存の絶対比較(5,000 体で NG=正直に報告・NG を期待するテストあり) | C7 前に方式を決める(PENDING) |
| 店舗参入資本(467.4M 円=貨幣供給の 93%)・役割語の LLM 結線・政府給付の科目 | PENDING(C5/C6/第2陣) |

## 6. 修正後の親検収(C4-fix 反映・09-08)

```
$ .venv/Scripts/python.exe -m shibuya.cli --agents 5000 --seed 1 --world data/world/v2
保存則 Σmoney 33,867,103 + Σrevenue 1,166,200 + Σ運賃 30,780 = 35,064,083 OK / 憲法5 OK / 乗り残し 0(0.0000)
日次センサス(§2.4・締めた day=0): 残差 0 / 貨幣供給 502,411,562 / faucet 502,464,083(来街者持込 35,064,083+参入資本 467,400,000) / sink 52,521 / 棚卸差異 0 / 廃棄 1,097,700 g / ゲート PASS
廃棄 1.301 t/日 (band 83.7-155.5) NG(規模 1%=C7 前に方式決定・PENDING)
状態成長 30 日外挿: OK・宣言超過 ['actual_log_raw'](実測 963,728 B/日 vs 宣言 620,000=1.55×・宣言側の delta 要=PENDING)
$ pytest(全体)→ 1,125 passed, 1 xfailed   $ lint-imports → 5 kept   $ scan → CLEAN   $ git ls-files data → 0
```
修正で見つかった潜在バグ: `attach_household_cash` が全部門の期首を取り直し、参入資本(事前の流量)が期首に飲み込まれて検算①の列和が崩れていた→世帯行のみ再取得へ(状態ハッシュは不変)。

**C4 の判定=完了**(受入列: 保存則テスト全合格・センサス残差閾値内(閉じた日の実値で 0)・憲法5 機械検査 OK)。
