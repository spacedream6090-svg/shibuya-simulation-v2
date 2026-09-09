# 受入報告 C7(40 万体×1 シミュ日・本番相当)— 本番ラン完走・受入進行中(2026-09-10)

> 形式は build-report-C0〜C6 と同じ: 親(Fable)が自分で実行した出力のみを証拠とする。
> ブランチ `build/c5-c8`。サーバー(SSH エイリアス・7×A5000・Python 3.10 venv)で実行。

## 0. 構成

| 項目 | 内容 | 状態 |
|---|---|---|
| ドレスリハーサル | 390,067 体×1,440 tick・mock LLM | **親の tmux 操作ミス(`kill-window -t c5:c7` が前方一致で c7dress を殺した)で 1.6 h 時点で消失**。代替=本番ラン自体の実測+12 tick mock(下記) |
| 本番ラン c7-day-1 | 390,067 体×1,440 tick・実 LLM(7×Qwen3-8B INT8・温度 0.7・max_tokens 96・mode production・`--fleet-wait-s 120`・tape 記録) | **09-09 19:39 開始**(`~/c5/run_c7.sh`) |
| 受入計器 | tools/c7(occupancy_series・holdout_compare・c7_accept・c7lib・area_axes_v0.json=セル→5 エリア写像 expedient)・tests/c7 58 本 | サブ S 完了(09-09 20:10)・engine の在圏 journal フック=親が結線 |

## 1. 受入項目(§9.1 C7)と結果(追記予定)

| 項目 | 基準 | 結果 |
|---|---|---|
| 壁時計 | ≤24 h/シミュ日(W1) | **9 h 10 m 15 s(33,014 s)=PASS**(/usr/bin/time -v Elapsed・CPU 70%) |
| M8 RSS | ≤24 GB | **1.533 GB(1,607,692 kB)=PASS** |
| S1 出力 | ≤5 GB | **0.165 GB=PASS**(calls.parquet 177,063,789 B+blocks.parquet 84,757 B+occupancy.npz 128,892 B) |
| 決定論 T2 | 同 seed 再ラン一致(40 万体は 1 回=checkpoint 自己整合+5,000 体の再ラン一致で代替=D-39) | 進行中(09-10 07:54 起動): **T2-c**=本番テープの再生(`cli --replay`・LLM 呼なし)→checkpoint 4 点の自己整合+最終 `530399c174a62448…` との一致/**T2-a**=5,000 体×1 日 同 seed・同 run-id 2 本(実 LLM)/**T2-b は回さない**(本番の繰り延べ 1,320,190 件が時刻依存=実 LLM 再ランは一致しえない・D-54) |
| 診断行 | 繰り延べ/昇格/縮退/抑止+保存則 2 検算 | **PASS**: deferred 3,290,800 / promoted 14,698,917 / degraded 22,096 / suppressed 1,080,963・保存則 Σmoney+Σrevenue+Σ運賃 = 11,522,113,271 円(初期と一致)・日次センサス 残差 0・ゲート PASS・憲法5 OK |
| 被覆指標 WC-6 | 孤児 0 | **0=PASS**(WC-5 過剰 0.004・報告のみ) |
| holdout 照合 | 事後 1 回のみ(KDDI 形状 5 指標) | T2 合格後に 1 回開封(D-43)。在圏系列は作成済み(5 エリア 138.0 ha=帯 110-170 OK・属性構成 勤務者 0.55-0.85/居住者 0.05-0.09/来街者 0.10-0.36) |

## 1b. 性能の発見(09-09 20:00・本番ラン開始直後)
- 12 tick mock @390,067 体: **内訳 llm 46,079 ms/tick**(呼 2,709/tick)・arbiter 616・movement 13.7・合計 47 s/tick → 1 日 18.8 h(エンジンだけ)。本番ランの vLLM ログでも tick 周期 ≈60 s(=24 h 超の見込み)。
- cProfile(3 tick・8,126 呼): `perception/renderer.py:1091 <dictcomp>` 101 s/7,173 呼=**14 ms/呼**・`_nearby_items` の生成式が 1 呼あたり 13,663 反復=**B5 近接個体の候補をセル内全個体の Python 反復で作っている**(5,000 体では 0.27 ms/呼で見えなかった)。→ サブ R にベクトル化+(tick, セル)キャッシュを依頼(出力バイト不変が条件)。修正後に本番ランを再起動する(現行ランは fallback として継続)。
- 在圏 journal(holdout 照合の入力)のフックは本番ラン開始時に未実装だった→親が engine/run.py に `occupancy_every/occupancy_path`(毎正時のセル別在圏+種別別)を追加し、再起動ランから記録する。

### 1c. 性能修正(サブ R・09-09 20:30)と再起動
- `perception/renderer._nearby_items` をベクトル化(セル順の連続座標配列・逆置換で自分を除去・sqrt は採った件だけ・知人は範囲比較)。**出力バイト不変**(旧実装を逐語で持つ照合テスト 7 本・5,000 体 checkpoint d5d79337… 不変・golden 不変)。PC 実測 390,067 体×3 tick: llm 16,908→**690 ms/tick**(24.5×)・1 呼 6.24→0.255 ms。
- **サーバー実測(親・3 tick mock @390,067)**: llm 46,079→**1,624 ms/tick**・arbiter 691・detect 68・合計 **3.49 s/tick**(→エンジン単独 ≈1.4 h/日)。
- 本番ランを **c7-day-2** として再起動(vectorized renderer+在圏 journal `--occupancy-every 60`)。c7-day-1(60 s/tick 見込み・在圏 journal なし)は停止。

### 1d. 本番ラン c7-day-2 の要約(親・09-10 05:39 完走・ログ回収 07:50)

| 項目 | 実測 | 所見 |
|---|---|---|
| 規模 | 390,067 体×1,440 tick・実 LLM 7×Qwen3-8B INT8・温度 0.7・max_tokens 96・mode production・fleet_wait_s 120 | 09-09 20:29→09-10 05:39 |
| LLM 呼 | **3,900,670 = 10.00 呼/体/日**(L4 制御目標 10・上限 400 万)| 帳尻 3,900,670(呼を 1 つも捨てていない) |
| 壁時計の内訳 | 22.9 s/tick = fleet_wait **19.37 s(84%)**・llm 2.22 s・arbiter 0.50 s・phase_c 0.22 s・movement 0.11 s・detect 0.08 s | 艦隊が律速(D-55)。エンジン単独なら 1.4 h/日 |
| 艦隊 | 処理量 118 呼/s(16.9 呼/s/GPU)・TTFT p50/p99 2.01/3.95 s・e2e 4.24/6.25 s・**繰り延べ 1,320,190(33.8%)**・再投入 1,319,273・再送 1,319,259 | 繰り延べは時刻依存→T2-b 不可(D-54) |
| 書式 | 実効 **0.007**(受入 ≤0.10)・厳密 0.424・別名 0.087(224,868 呼)・位置読み 0.337(868,459 呼)・辞書写像 0.010(24,827 呼)・温度0再生成 8,612(成功 7,960)・未定義 25,312(最終 undefined_action_count 485) | 5,000 体(0.007/0.385)と同じ帯 |
| checkpoint | 4 点・最終 `530399c174a62448…` | T2-c の照合対象 |
| 会話 | conversation_sessions **65**(呼の 0.0017%) | 5,000 体の 3/日と同率=D-33 の歪みが規模でも不変 |
| 鉄道 | **乗車 75・降車 0・待ち行列 7,969・乗り残し 0** | 5,000 体では乗車 1-2。行動語「乗車」の選択は多いのに実乗車に至らない=**D-51** |
| C4 後半 | 補充 141・納品 2,337・宅配 5,919・ホテル泊 503・顕著行為 228(気づき 2,349,711・出動 114)・**廃棄 17.906 t/日(帯 83.7-155.5)NG** | 全母集団でも帯の 1/5〜1/9=**D-52** |
| 状態成長宣言 | **NG**: transfer_log 6,291,456 B = cap ちょうど(頭打ち)・delivery_log 378,752 B・「宣言だけで cap 超過(失敗)」 | C6 では警告→390k で失敗=**D-53** |
| ActualLog | 15,530 行・遵守率 **0.273** | 5,000 体でも 0.268-0.270=規模不変 |
| 参入資本 | 店舗 22,432,899,146 円(66.10%)/世帯 11,502,707,171 円(33.90%)/貨幣供給 33,935,606,317 円 | 経済センサス按分・anchors 対数正規 |
| レンダラ | 描画 3,900,670・命中率 1.000・平均 tok 共有静的 643.1/750・セル 143.4/250・個体 125.8/300(合計 912.3) | 予算内 |
| RSS/CPU | 最大 RSS 1.53 GB・User 22,439 s・System 923 s・CPU 70% | M8 の 1/16 |

受入計器(tools/c7/c7_accept.py・T2/HOLD 未入力)の出力: **判定済み 9/16 行・合格 9・不合格 0**(W1・M8・S1・L4・DIAG・CONS-1・CONS-2・CONST-5・WC-6)。P2 は 5 千体の行なので 40 万体では参考(114.5 ms 壁/23.5 ms CPU・待ち割合 0.79=D-35)。

### 1e. 本番テープの解析(親・サーバー側で calls.parquet 2,580,480 行を全件パース・133 s)

| 項目 | 実測 | 所見 |
|---|---|---|
| 行数 | **2,580,480**(= 3,900,670 − 繰り延べ 1,320,190。L4 の「呼」は発射数=再送も 1 呼・親決定 09-09) | 実際に消費された応答は **6.6 呼/体/日**。呼んだ個体 389,591/390,067(99.9%) |
| 時間配分 | **毎時 107,520 = 1,792/tick で 24 時間平坦**(深夜 0-5 時も同数) | 1,792 = 艦隊 `queue_capacity` = `max_in_flight`(64/GPU×7=448)×4。計画 2,709/tick のうち 917/tick(33.8%)が **queue full で繰り延べ**=D-55 追記。深夜も上限まで呼ぶ=需要非依存の配分(D-56) |
| tick 周期 | 22.9 s ≈ 1,792 呼を 78 呼/s で捌く時間 | 艦隊の実処理量 78 応答/s(11.2/s/GPU)。W1 は捌き切る時間で決まっている |
| トークン | 入力 3.66 G(平均 1,419/呼)・出力 95.9 M(平均 37.2/呼) | 111 k 入力 tok/s(prefix キャッシュ込み) |
| 行動分布 | **移動 46.7%・購入 41.8%**・休憩 4.6%・待機 2.7%・乗車 2.5%・未定義 1.0%・退去 0.4%・通報 0.2%・会話 0.04%(1,130)・手伝い 307・就寝 229・降車 77・並ぶ 66・断る 10 | 購入偏重(5,000 体の 49%→41.8%)は規模でも残る=D-33。**就寝が 229 回/日**=夜間の呼が就寝以外に使われている |
| 対象欄 | ITEM_CATEGORY **83.6%**・NONE 16.3%・STATION_OR_VEHICLE 1,634・PERSON 1,229・CELL 30 | 移動(46.7%)の多くも対象が品目=対象欄の語彙が買い物に寄っている |
| 乗車→実乗車 | 選択 **64,784** → 乗車 75(**0.12%**)・降車 77 | D-51 の実測 |
| 通報 | **6,426** vs 顕著行為 228・出動 114 | 事象の 28 倍の通報=過剰通報(D-57) |
| 未定義行動の上位 | **探索 14,624・通勤 7,457**・観察 1,476・探す 654・進入 401・近づく 209・食事 127・調査 57 | D-50 穴台帳の実例: 「通勤」「探索」は語彙に無い意図 |
| 書式 | format_ok 0.990・strict 0.576・別名 0.087・位置読み 0.337 | summary と一致 |
| 起床区分 | class 0: 2,290,550(88.8%)・class 1: 267,849(10.4%)・class 2: 22,081(0.9%) | 区分ごとの行動分布は同形(移動>購入>休憩/待機) |

解析スクリプト: 親が書いた tape_stats.py(scratchpad・parser.parse_two_line を全行に適用)。数値は tape_stats.json(scratchpad)。
## 2. ログ

### 2a. c7-day-2 summary(親回収・エンドポイント行のみ除外)

```text
[run] n=390067 cells=520 seed=1 ticks=1440 world=data/world/v2
  壁時計 33014.44s (W2 上限 600s) / 移動+密度 114.523 ms/tick (P2 上限 5 ms)
  LLM呼 3,900,670 = 10.00 呼/体/日 (L4 制御目標 10)
  書式エラー率 実効 0.007 / 厳密 0.424 (受入 ≤0.10) ・別名 0.087 ・位置読み 0.337 ・辞書写像 0.010
  保存則 Σmoney 11,502,707,171 + Σrevenue 19,392,600 + Σ運賃 13,500 = 11,522,113,271 (初期 11,522,113,271) OK / 最小在庫 0
  checkpoint 4 点 最終 530399c174a62448…
  内訳[ms/tick] phase_a 95.05 / detect 84.62 / fleet_wait 19366.98 / llm 2216.23 / arbiter 504.16 / phase_b 32.94 / phase_c 217.38 / movement 114.52 / checkpoint 0.12 / 合計 22926.70
  movement 壁 114.523 / CPU 23.485 ms/tick (P2 上限 5) ・待ち割合 0.79
  凍結静的文 w14_signage.parquet=f2439da625729895 w15_cell_static.parquet=012489fc47264359
  世界過程 台帳 1a5fcb8ce4a7e24f… 憲法5 OK / 再生日 2026-07-28 / 乗車 75 降車 0 待ち行列 7,969 乗り残し 0(0.0000) / ActualLog 15,530 行 遵守率 0.273
  C4後半: 補充 141 / 納品 2,337 / 宅配 5,919 / バス到着 0 / ホテル泊 503 / 顕著行為 228(気づき 2,349,711・出動 114) / 廃棄 17.906 t/日 (band 83.7-155.5) NG
  日次センサス(§2.4・締めた day=0): 残差 0 / 貨幣供給 33,935,606,317 / faucet 33,935,934,271 / sink 327,954 / 棚卸差異 0 / 廃棄 1,897,200g / ゲート PASS
  過程別[s]: bus_taxi=0.009, crowd=219.365, delivery_inbound=1.237, dispatch=0.005, environment=13.901, hotel=0.040, infra=4.221, large_event=0.015, last_mile=0.061, opening=1.406, press=0.020, rail=21.233, road_works=0.021, salient=93.291, shelf=0.566, street_cleaning=1.965, traffic=0.024, waste=0.279
  レンダラ perception.Renderer: 描画 3,900,670 命中率 1.000 / 平均tok 共有静的 643.1/750 セル 143.4/250 個体 125.8/300 (合計 912.3) 切り詰め 83
  診断 deferred: 3,290,800
  診断 promoted: 14,698,917
  診断 degraded: 22,096
  診断 suppressed: 1,080,963
  診断 parse_error_rate: 0.0065 / undefined_action_count: 485 / tape_miss_count: 0 / conversation_sessions: 65
  状態成長宣言(D-R2-6)の検査: steps=1440×1分 = 1.0000 シミュ日 → 30 日外挿 (N=390067) (NG)
    pending_apply        実測      229,376B →        229,376B/日 → 1日          229,376B / cap       16,000,000B OK
    intent_buffer        実測      988,064B →        988,064B/日 → 1日          988,064B / cap       16,000,000B OK
    arbiter_backlog      実測   12,394,976B →     12,394,976B/日 → 1日       12,394,976B / cap       32,000,000B OK
    diagnostics_rows     実測      184,320B →        184,320B/日 → 30日        5,529,600B / cap       64,000,000B OK
    tape_rows            実測 1,560,268,000B →  1,560,268,000B/日 → 1日    1,560,268,000B / cap    5,000,000,000B OK
    actual_log_raw       実測      481,430B →        481,430B/日 → 7日        3,370,010B / cap      536,870,912B OK
    actual_log_daily     実測            0B →              0B/日 → 30日                0B / cap       16,777,216B OK
    flow_matrix_daily    実測        4,320B →          4,320B/日 → 30日          129,600B / cap       16,000,000B OK
    transfer_log         実測    6,291,456B →      6,291,456B/日 → 1日        6,291,456B / cap        6,291,456B OK
    delivery_log         実測      378,752B →        378,752B/日 → 1日          378,752B / cap        2,097,152B OK
    宣言だけで cap 超過(失敗): ['transfer_log', 'delivery_log']
[艦隊] 呼 3,900,670 / 帳尻 3,900,670 ・繰り延べ 1,320,190(再投入 1,319,273・再送 1,319,259) ・TTFT p50/p99 2.01/3.95s ・e2e p50/p99 4.24/6.25s ・temp 0.7 max_tok 96 ・cache_salt 53306b457ea68148…(production)
[艦隊書式] エラー率 実効 0.007 / 厳密 0.424 (受入 ≤0.10) ・別名 0.087(224,868 呼) ・位置読み 0.337(868,459 呼) ・辞書写像 0.010(24,827 呼) ・温度0再生成 8,612(成功 7,960) ・未定義 25,312
[参入資本] 店舗の現金+預金 22,432,899,146 円 / 世帯の現金+預金 11,502,707,171 円 / 貨幣供給 33,935,606,317 円 = 店舗 66.10% (経済センサス按分)
[世帯財布] 世帯の現金+預金 11,502,707,171 円 / 貨幣供給 33,935,606,317 円 = 33.90% (anchors 対数正規・母集団あり)
	User time (seconds): 22439.02
	System time (seconds): 922.74
	Percent of CPU this job got: 70%
	Elapsed (wall clock) time (h:mm:ss or m:ss): 9:10:15
	Average shared text size (kbytes): 0
	Average unshared data size (kbytes): 0
	Average stack size (kbytes): 0
	Average total size (kbytes): 0
	Maximum resident set size (kbytes): 1607692
	Average resident set size (kbytes): 0
	Major (requiring I/O) page faults: 0
	Minor (reclaiming a frame) page faults: 216562099
	Voluntary context switches: 19627450
	Involuntary context switches: 302043
	Swaps: 0
	File system inputs: 0
	File system outputs: 351304
	Socket messages sent: 0
	Socket messages received: 0
	Signals delivered: 0
	Page size (bytes): 4096
	Exit status: 0
C7_DONE
```
