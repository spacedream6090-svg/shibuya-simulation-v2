# 工程 C2(エンジン核)受入報告(進行中・2026-09-08〜・ブランチ build/c0-c4)

> 根拠: 実装計画書 §9.1 C2 行(core SoA レジストリ・dtype/バイト予算・Philox・ハッシュ+world/agents SoA+engine(1分tick時計・スケジューラ・4クラス繰り延べアービタ・resolve 単一書き込み口・二相コミット・録画テープ)+mock LLM+状態成長宣言(5欄)。検収=5,000体×1日 mock ≤10分(W2)・P2/P3/P6・M7≤2.0x・同seed同状態ハッシュ(T1/T2)・hypothesis 性質テスト)。証拠=親自身の実行出力のみ。

## 1. 第1弾(サブC: core types/hashing/soa/growth/serialize・engine clock/scheduler/tape・llm mock)= 親検収済み

```
$ .venv/Scripts/python.exe -m pytest tests/core tests/engine -q -p no:cacheprovider -o addopts=""
83 passed in 1.81s
$ .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -o addopts=""      (全体)
177 passed in 4.89s
$ .venv/Scripts/lint-imports.exe → Contracts: 5 kept, 0 broken.   (Analyzed 37 files, 36 dependencies)
$ python tools/scan_secrets.py <untracked new files> → CLEAN
$ pytest tests/engine/test_scheduler_p3.py -s
[P3] 予約 7,401,492/s ・ 取り出し 2,364,408/s ・ 通し 1,791,965 events/s (閾値 100,000/s ・ 1,000,000件/1440 tick)
```

| 受入項目 | 実測 | 予算 |
|---|---|---|
| P3 イベント処理 | 1.79M events/s(通し・100万件/1,440 tick) | ≥100k/s |
| M7 直列化膨張率 | 1.000x(RAM/非圧縮直列化・5,000体乱数充填)・参考 RAM/zstd ファイル 1.002x | ≤2.0x |
| M9 バイト予算宣言 | Registry.declare は予算なしを拒否・個体上限=M1(30,000 B/体) | 恒常 |

サブCが検出し親が裁定した矛盾:
1. 状態成長宣言の5欄: 親の指示(name/unit/bytes_per_unit/growth_per_simday/cap)が誤り。**正典=D-R2-6(per_agent_bytes/per_cell_bytes/per_day_growth/retention/worst_case_ops_per_tick)**→第2弾で必須欄に修正(TASK 0)。
2. TapeLLM が engine.tape を import すると層契約違反→llm 側に `TapeLookup` Protocol を置く依存性逆転で解決(engine.tape.Replay が満たす)。採用。
3. M7 の分母未定義→RAM/**非圧縮**直列化長を主指標、RAM/ファイルも併記(expedient・登録)。
4. セル単位のバイト予算行が予算表に無い(M10は総額)→セルレジストリの上限は None(登録)。
5. §2.5 の blake3 引数列・バイト配置が未定義→`run_salt ‖ 3バイト用途タグ ‖ int64-LE 欄` で固定・既知解固定(登録)。
6. class_rank=−1 が RNG カウンタ(非負)と衝突→規約「カウンタ=class_rank+1」を第2弾に指示。

## 2. 第2弾(サブD: agents/world SoA・二相コミット・アービタ・resolve・変化検出 P6・mock 1日)= 親検収済み

```
$ .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -o addopts=""      (全体)
368 passed in 30.15s
$ .venv/Scripts/lint-imports.exe → Contracts: 5 kept, 0 broken.   (Analyzed 59 files, 104 dependencies)
$ python tools/scan_secrets.py <new+modified files> → CLEAN
$ .venv/Scripts/python.exe -m shibuya.engine.run --agents 5000 --seed 1 --world data/world/v2
[run] n=5000 cells=520 seed=1 ticks=1440
  壁時計 3.17s (W2 上限 600s) / 移動+密度 0.081 ms/tick (P2 上限 5 ms)
  LLM呼 47,942 = 9.59 呼/体/日 (L4 制御目標 10)
  保存則 Σmoney 33,986,283 + Σrevenue 1,077,800 = 35,064,083 (初期 35,064,083) OK / 最小在庫 48
  checkpoint 4 点 / 診断 deferred 50,032・promoted 85,767・degraded 12,404・suppressed 9,912
  状態成長宣言(D-R2-6)30日外挿: pending_apply/intent_buffer/arbiter_backlog/diagnostics_rows/tape_rows すべて cap 内
$ pytest tests/engine/test_change_detect_p6.py ... -s
[P6] 400,000体×453セル×100 tick: 定常 0.753 / セル10%変化 1.070 / +個体1%跨ぎ 1.259 ms/tick (上限 2 ms)
```

| 受入項目(§9.1 C2) | 実測 | 予算 |
|---|---|---|
| W2 5,000体×1日 mock | 3.17 s(実資産 520セル)/3.05 s(合成) | ≤10分 |
| P2 移動+密度 | 0.081 ms/tick | ≤5 ms |
| P3 イベント処理 | 1.79M events/s(第1弾) | ≥100k/s |
| P6 変化検出@40万体 | 1.26 ms/tick(最悪ケース) | ≤2 ms |
| M7 膨張率 | agents 0.949x / cells 0.304x / pois 0.526x(state_hash 往復一致) | ≤2.0x |
| 同seed同状態ハッシュ(T1/T2) | 一致(別seedは相違)・T4 規模不変(5,000 vs 5,001) | 必須 |
| 保存則 | Σmoney+Σrevenue 不変・在庫非負 | 必須 |
| 単一書き込み口 | `writable()` 呼び出しは engine/resolve.py のみ(AST 検査) | 必須 |
| hypothesis 性質 | 意図の順序置換で結果不変(T3型)・アービタ純関数 | 必須 |

親の裁定: 降車の失敗語は行動契約書 §2.1(「その駅には止まらない」=NO_STOP)に合わせて修正(親の指示が誤っていた)。セル数の表記揺れ(139/453/520)は PENDING(台帳整合・ユーザー確認)。相手別不応期・会話継続・記憶転写・関係辺・録画テープ実書き出しは C3/C4 の範囲として明示。40万体フルランは C7 で実測(4万体 18.2 s・arbiter 支配)。

## 3. 層2 独立検収(別インスタンスの Fable)

**判定: 合格(条件付き・逸脱3件は親が反映)**。レビュー役の実行: C2範囲 273 passed(+build 95=368 と突合)/lint-imports 5 kept/秘密スキャン CLEAN/seed1 を2回・seed2 を1回走らせ最終 checkpoint ハッシュが seed1 同士で一致・seed2 と相違(T2)/P6 最悪 1.24 ms/M7 非圧縮比 0.95-1.0x/書き込みガードをスクラッチで実証(凍結後の代入は `ValueError: assignment destination is read-only`・`writable()` 内は可)/`git diff --stat main -- docs/design/`=§8/§4 への追記のみ(削除0)/敵対プローブ: cap=4・10 intent → confirmed 4・losers 6・第2ラウンド空回り。

| 指摘 | 処置 |
|---|---|
| 書き込みガードが opt-in(構築直後は非凍結・`thaw()` が公開で AST 検査外) | AST 検査に `.thaw(` の呼び出し元制限を追加(agents/state.py・world/state.py 内のみ)。run.py の freeze 規律を登録簿に明記 |
| `n_conflicts` が再試行で二重計上(6→12) | 初回裁定の落選のみ計数するよう修正 |
| 縮退の適用範囲(予算超過 tick で下位2クラス全件)が未登録 | 登録簿へ追記(範囲規則) |
| expedient 未登録 11 件 | 登録簿へ追記 |
| 落選→再起床の経路/M7 分母/テープ鍵と昇格 | C3 前に決める設計解釈として PENDING に記録(親の推奨つき) |
