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

### 1b. C5-a 仕上げ(サブ M・親検収 09-09)
- 年齢 raking を **16 階級×性別の結合表**へ(e-Stat 全 60 分類の再取得分を入力に・不詳 25,380 人は既知比で按分・性別は男女別総数表へ IPF で戻す)。新ゲート `srmse_age_sex_joint_resident` 0.0125(<0.13)。旧 expedient 2 件(70+ プール比率・結合の種)は解消。体数 390,188→**390,067**(在区就業住民 6,956→7,077)。
- 定員先取り層を**役割ベース**へ(`duty_role` 列を publish・RESERVED_ROLES=駅員/電車運転士/車掌/バス運転士/指令/警察官/消防士/救急隊員/議員)=769 体(旧 1,316)。規模の是非=PENDING D-22。
- 世帯財布を anchors(対数正規)に結線(cli 層外・経路 CARRY_IN 不変)。写し定数の等価テスト・`--no-population`(下限対照)。
- 親実行: `pytest tests/build_pop tests/economy tests/test_cli.py` 全合格(149)・build.run 再構築=W16 全ゲート PASS(build_hash は W14/W15 登録と入力差し替えで 0100706b→6f4c259f… に変化・2 回一致は M が確認 58d71960…=W14/W15 未登録時点)・cli 5,000 体: 保存則 OK・センサス残差 0・**店舗 67.49%/世帯 32.51%**・checkpoint 37c11b91… 一致(M の値と同一)。

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

## 3b. 層2 独立検収(C5-b コード=W14/W15・W17 段階コード・C5-a 仕上げ・結線)
**判定=条件付き合格(09-09 14:20・重大 0/中 6/軽 9)→ 条件 2 点を親が修正して確定**。層2 が自分で実行: pytest 1,519 passed/0 failed/1 xfail(skip 0=実データ試験が走った)・lint 5 kept・scan CLEAN(40 ファイル+全追跡)・空ディレクトリ 2 か所から build ×2=build_hash 一致(d0b57ed1…)・応答 jsonl を複写して本番 build_hash ee668724… を再現・W14〜W20 ヘッダと manifest がバイト一致・cli ×2 一致(checkpoint fbad9b81…)・規約⑧ 実資産 0/520 不一致・凍結 2,816 行が正規化の不動点。
- 条件(修正済み): ①W17 ヘッダ expedients の文言(「隙間の中だけ」→丸ごと平行移動/「7 規則」→8 規則) ②`STAGE_VERSION` 1.1.0→1.2.0(登録簿と一致)。
- 中(対応): ③`raking_lowers_jsd` は pin(同語反復)=expedients と登録簿に明記(合格線は D-23) ④凍結文の版がランの記録に無い→`RunResult.frozen_sources`(manifest 欄+要約行「凍結静的文 w14_signage=f2439da6… w15=012489fc…」)を親が結線 ⑤本番 build_hash の再現手順(応答 jsonl を --out に複写)を登録簿へ ⑥W17 表がある世界での結線の縁(`apply_to_mock_schedule` は n_agents>母集団で ValueError・0:00 勤務者の home_cell 上書き)=W17 ingest 時に確認(PENDING)。
- 軽(記録): 古い docstring 3 件・W15 ヘッダ文言(8/4 vs 2/2)・修正率の保守的定義・§1 W15 行の入力拡張(W6/W11)未記載・C5-a 報告の checkpoint 値は schedule_hash 追加で更新(fbad9b81…)・層2 チェックリストの `-q` 重複と旧ブランチ名。

## 4. C5-b(追記予定)

- **W14/W15 第1回生成(09-09 09:37-10:10・Qwen3-32B-AWQ TP2・温度0・seed 20260909・repeat 2・VLLM_BATCH_INVARIANT=1)**: 呼 4,674+1,040・失敗 0・約 3 呼/s(80 ctok/s)。応答 SHA fa6e5b4e(W14)/cbf1a9b7(W15)。親 ingest: **rep 間バイト一致率 1.0/1.0**(決定論=T3 の傍証)。不合格率 **W14 0.131(閾値 0.10)=FAIL・W15 0.283(閾値 0.05)=FAIL**・凍結 2,030/2,337・373/520。
  - 理由(親分析): W14=N7 漢字列 113(**偽陽性**: 開校 26・開館 21・参拝 10・診療・利用=一般語/月金 17=略記は⑥で扱うべき)・N4 数字 78(**真陽性**: 入力「毎日終日」をコンビニで「10時から22時」と捏造 74 件→入力の表記を「24時間営業」に直す)・too_long 72(複数曜日の営業時間を全部書いて 50 字超)・N1 英字 47(**偽陽性**: 入力にある英字店名に後続の数字が連結「Skechers 11」)・N2 カタカナ 11(一般語 スイーツ/パチンコ/クリニック が主)。W15=A1 略記 106(「など」)・N4 数字 50(見えるものの個数を数字で書く「2軒」=入力に無い数字)・I1 個体語 5(「私」)・N3 2・too_long 7。
  - 対応: 検査器の偽陽性修正(N1 の英字トークン分割・N7 の一般語除外/N2 の一般カタカナ語表)+プロンプト改訂(終日→24時間営業・50 字制約・曜日別営業時間の圧縮・「など」「等」禁止・個数を数字で書かない・一人称禁止)→**第2回生成**(サブ L 修正後・親が再生成)。第1回の応答は data/ に保持(比較用)。
  - **第2回(09-09 11:05-11:35・同構成・新プロンプト W14 5923438d/W15 75c75ce2)**: 呼 4,674+1,040・失敗 0・rep 一致率 1.0/1.0。親 ingest: **W14 合格**(不合格率 **0.040**≤0.10・凍結 2,243/2,337・残理由 A1 曜日連結 56[「土曜日曜日」=略記でない偽陽性→検査器修正へ]・too_long 30・I1 7)。**W15 不合格**(0.362>0.05・too_long 181=「など」禁止で名前を全列挙→90 字超・I1 8・N4 3)→ 第3回=見えるもの上位 2 件に前処理+45 字制約+regex `[^
]{10,88}`(構造化出力)で W15 のみ再生成(サブ L 修正中)。
  - **W14 最終(第2回応答×検査器修正後の再 ingest・09-09 11:55)**: 不合格率 **0.018**・凍結 **2,295/2,337**・rep 一致 1.0・tokens max 25(上限 25)・残 42 件は全て真陽性(too_long 30・一人称 7・評価語 2 ほか)。プロンプト SHA 5923438d(不変)。
  - **第3回(W15 のみ・09-09 12:05-)**: プロンプト全面改稿(三人称・45 字 1 文・可視物上位 2 件のみ・数字を渡さない)+`regex "[^
]{10,88}"`(構造化出力=文字単位を親プローブで確認: 32 文字/92 バイトが通過)。SHA dfd70b35。プローブで「見えるもの:」見出しの本文混入 2/3 → ingest の正規化(先頭見出し語の除去・冪等)で吸収。**結果(12:20・1,040 呼・失敗 0・応答 SHA aae5c911)**: fail_rate **0.0154**(≤0.05 PASS)・凍結 **512/520**・tokens max 35(≤45)・見出し混入 426/520 は正規化で全除去(凍結文に残存 0)。残 8 件=一人称 3・rep 不一致 2(TP2+構造化出力で温度 0 でも 2 セルが揺れた=非決定性の記録)・略記 1・命令形 1・カタカナ 1・既知固有名詞 1。`rep_byte_match_rate 0.996`/`individual_word_violations 3` の 2 ゲートは母集団を凍結行に揃える定義修正(サブ L)で PASS 見込み。
- **W17 段階コード(サブ N・09-09)**: build/sched(語彙 12+12・行書式 `d0 0700-0830 移動 職場`・パーサ・修復 7 規則・raking・骸格)・agents/weekly(CSR ローダ 266 B/体・boundary_events)・90 テスト。親が結線: build/run.py に SCHED 登録(RUN_ORDER W16→W17→W18)・engine/run.py の計画境界を weekly 分岐へ(mock 日課は下限対照として残置)・Checkpoint.schedule_hash。プロンプト生成 390,067 呼・SHA 6927a1d7…・入力 tok 平均 339.9・11.9 s。
- **W17 パイロット(親・先頭 300 体=住民・GPU 1 枚・conc 32・133 s=2.25 呼/s/GPU・1,323 ctok/s)**: completion 平均 587 tok・**239/300 が max_tokens 640 で切れ**・行数 30.6・**就寝しか書かない応答 23/300**(facts が「勤務・通学: なし」の住民=区内席なしの就業者を域外勤務と書いていない)・語彙外 朝食/学習。→ N に修正指示(facts の域外勤務・15 歳未満/無職の明示・日跨ぎ就寝 1 行化・各日 4 行以上の必須化・max_tokens 560・パーサの strip・種別別 40 体の再パイロット)。**再構築一致 FAIL**(W17 ヘッダに壁時計)→ N に修正指示。
- **W17 v2/v3 パイロット(親・344 体=9 種別×40・5 GPU)**: v2(自由生成・max_tokens 560)=318/344 が length 切れ・1 行≈19 tok・1 日 12 行を書く→**v3=日見出し形+vLLM structured_outputs(regex・種別と事実に応じた場所語集合 35 本)**: finish stop 281/length 63(18%)・completion 平均 427 tok(p50 578・max 600)・活動行 25.0/体・parse 失敗率 **0.007**(切れた末尾行)・修復=duty_clamped 312/duty_off_day 350/visitor_entry 150/exit 125/day_underfilled 24。length 切れ 18% は最終日の欠けを骸格で補う運用で受容(max_tokens 640 への再改版は見送り=時間優先・登録簿に記録)。
- **W17 本番生成(09-09 12:07 開始)**: プロンプト v3 SHA c5e8c1a2(390,067 呼・入力 tok 平均 467.5・7 シャード 212 MB×7)。シャード 0-4=GPU2-6(Qwen3-8B INT8・VLLM_BATCH_INVARIANT=1・conc 48・約 1,340 ctok/s=2.3 呼/s/GPU→1 シャード≈6.7 h)。シャード 5-6 は W15 第 3 回完了後に GPU0-1 で。結果:
  - **W17 本番生成(09-09 12:07-18:05・7 シャード・8B INT8 DP7・conc 48/GPU)**: 呼 **390,067/390,067・失敗 0**・completion 合計 1.84 億 tok(1 シャード ≈2,626 万 tok・約 1,410 ctok/s/GPU・壁時計 18,378-19,138 s ≈5.2 h/シャード)。応答 7 ファイル 398 MB(SHA は W17.header.json)。
  - **ingest 第1回(親)**: response_rate 1.0・parse_fail 0.0042(unknown_place 29,898=max_tokens 600 で切れた末尾行・format 17,690・bad_time 5,715)・活動 12.57M(32.2/体)・completion 平均 471(p50 588・p90 600)・**modified_rate 0.2117 > 0.20=FAIL**(修復 9.6%+raking 固定 12%)・JSD 0.556→0.401 → raking 予算を**適応**(0.19−修復率)へ(サブ N・登録簿 §4)。
  - **ingest 第2回=最終**: **modified_rate 0.1871 < 0.20 PASS**・jsd_max_after 0.421(自宅－勤務・合格線は D-23)・raking 1,188,863 行(9.41%)+修復 1,210,227(9.58%)・n_dropped 283,588・骸格 0 体・`w17_schedule.parquet` 14,600,818 B=**37.4 B/体**・ingest 105 s。感度: 固定 12% 予算との JSD 差 +0.020。
  - **全段ビルド(親・09-09 18:20)**: W14〜W20 すべて PASS(残る FAIL 3 は C1 既知=D-1/D-2)。**W18 被覆 C 0.295→0.425(定量 0.237)・実装クラス 19/57・孤児 0**。build_hash **4acb4eb349a5a810…**。
  - **エンジン結線(親)**: 5,000 体 mock 1 日が W17 週次表で動作(計画境界=週次表・checkpoint d5d79337…・呼 49,847・保存則 OK・センサス PASS・sessions 48)。
- W18 再算出=済(上記)。**C5 出口=09-09 18:25**(コミット 第118)。層2: C5-b コードは第117 で合格・W17 本番 ingest と raking 適応化の再検証は C6 の層2 に含める。

## 4b. サーバー側の実行環境(C6/C7 の準備・09-09 親)
- サーバーには Python 3.10 しか無い(pyproject は >=3.12)。ユーザー空間に 3.12 を入れる手段(uv・pyenv)は §7 の実行ファイル/アーカイブ取得禁止に当たるため親は行わず、**3.10 の venv(~/venvs/v2)に 3.10 対応の依存版(numpy 2.2.6・numba 0.67・pyarrow 25.0.1 ほか)を入れ、本体は `--no-deps --ignore-requires-python` で導入**した(コードに 3.11+ 専用構文なし=grep 確認)。コードは ~/v2(src/tests/pyproject/tools/docs/design)へ tar 複製、世界データは data/world/v2(jsonl 除く)を複製。
- サーバーでのテスト: core/engine/agents/economy/llm/perception=緑(1 件のみ FAIL=OSM バス停の実データ依存テストで data/realworld 未複製のため・3.10 起因ではない)。
- **5,000 体×1 日(実データ・mock LLM)をサーバーで実行: 壁時計 38.2 s・保存則 OK・checkpoint 最終 `fbad9b8119fcc287…`=PC(Windows・3.12)と同一ハッシュ→機種・OS・Python 版を跨いだ T2 一致**。移動+密度 0.271 ms/tick(PC 0.126)。40 万体の見積り: エンジン側 ≈50 分/日(LLM 待ちを除く)。
- 記録: 3.10 運用は実装計画書 §1(Python ≥3.12)からの逸脱=expedient(親判断待ち=U-8 として PENDING: ユーザーがサーバーへ 3.12 を導入するか、3.10 運用を C7 まで容認するか)。

## 5. ユーザー判断へ回した事項

PENDING D-16〜D-21(anchors 1/10・office 写像・W15 45 tok・実店名 vs 架空・空間支持・KIND_WORDS テンプレ改版)。
