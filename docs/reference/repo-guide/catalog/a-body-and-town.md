# 機能のカタログ A 体と街(把握の資料 段 2)

> 発注は [返事その 6](../../../design/prompt-2026-11-05-reply6.md) §3-1 の 3 です。今のコードの現状を書きます。あるべき姿は [仕様書](../../../design/spec/) の担当なので、ここには書きません。
> 正はコードです。HEAD `15b6bbd` のコードを読みました。既定の値は CLI の引数の定義と各モジュールの腕の関数を Python で読み出して確かめました(`SHIBUYA_*` の環境変数は 1 つも立っていない状態)。この文書のためにランは回していません。`data/` は開いていません。実測の値には出どころを添えます。
> 1 日の流れは [段 1](../day-flow.md)、ファイルごとの事実は [段 3 のカード](../cards/README.md)(本体への取り込み待ち)です。

## 0. 先に一覧と読み方

### 0-1 機能の一覧

発注のリストにある機能は 1・2・3・6・7・11・14 の 7 つで、ほかは近いものとして足しました。B(人の中身)と C(基盤)の機能には踏み込みません。

| # | 機能 | 状態 | 主なファイル |
|---:|---|---|---|
| 1 | 鉄道 | 既定=時刻表の運行・乗車・運賃・200% の上限/腕=帰無腕/器だけ=渋谷の発着の表/無いと宣言=電車を見送る | [rail.py](../../../../src/shibuya/engine/processes/rail.py)・[resolve.py](../../../../src/shibuya/engine/resolve.py) |
| 2 | 在圏(域内に居る・舞台の外) | 既定=日課の実行部・読み取り規則 v2・即時の退出/腕=`--exit-mode walk_to_platform` ほか/器だけ=予約の口 3 つ/無いと宣言=催しの人の注入 | [presence.py](../../../../src/shibuya/engine/presence.py)・[weekly.py](../../../../src/shibuya/agents/weekly.py) |
| 3 | 歩行とナビメッシュ | 既定=歩ける面の移動 nav1/腕=坂・曲がる重み/器だけ=経路の候補 3 つ/`absent.py` に行なし | [nav1.py](../../../../src/shibuya/engine/space/nav1.py)・[navmesh.py](../../../../src/shibuya/world/navmesh.py)・[navmesh_route.py](../../../../src/shibuya/world/navmesh_route.py) |
| 4 | 人の動きのモデル(足した) | 既定=本人の速さ × 坂 × 混み具合・接続口/腕=密度の推定/器だけ=混雑の中の避け方 | nav1.py・[geometry.py](../../../../src/shibuya/engine/geometry.py) |
| 5 | 混雑場(足した) | 既定=密度の段と流れの 3 値/器だけ=8 方位と平均待ち | [crowd.py](../../../../src/shibuya/engine/processes/crowd.py)・[state.py](../../../../src/shibuya/world/state.py) |
| 6 | 席と列 | 既定=席・列・30 刻みと 15 刻みの離脱/腕=席の面積の感度/`absent.py` に行なし | crowd.py・resolve.py・[seat_release.py](../../../../src/shibuya/engine/seat_release.py) |
| 7 | 天気と環境 | 既定=暦の太陽と再生日の気象/腕=`--weather-perturb`/`absent.py` に行なし | [environment.py](../../../../src/shibuya/engine/processes/environment.py)・[solar.py](../../../../src/shibuya/engine/solar.py) |
| 8 | 日影(足した) | 既定=W9 の 5 分ごとの影をセル 1 点で読む | environment.py・[w9_shadow.py](../../../../src/shibuya/build/vis/w9_shadow.py) |
| 9 | 騒音(足した) | 既定=W10 の静的な昼夜の段/器だけ=動的な上書きの欄 | state.py・[w10_noise.py](../../../../src/shibuya/build/field/w10_noise.py) |
| 10 | 見通し(足した) | 既定=W8 の静的な可視の表 | [assets.py](../../../../src/shibuya/world/assets.py)・[w8_visibility.py](../../../../src/shibuya/build/vis/w8_visibility.py) |
| 11 | 世界過程 18 本 | 既定 13 本(うち記録か集計だけ 3 本・一部だけ 1 本)/無いと宣言で止めた 5 本/旧道あり | [runner.py](../../../../src/shibuya/engine/processes/runner.py)・[processes/](../../../../src/shibuya/engine/processes/) |
| 12 | 世界の台帳と検査(足した) | 既定=起動時の憲法 5 の検査と ActualLog/宣言だけの欄あり | [first_batch.py](../../../../src/shibuya/world/processes/first_batch.py)・[registry.py](../../../../src/shibuya/world/processes/registry.py) |
| 13 | 無いと宣言と入力の宣言(足した) | 宣言だけ(挙動を変えない) | [absent.py](../../../../src/shibuya/world/processes/absent.py)・[inputs.py](../../../../src/shibuya/world/processes/inputs.py) |
| 14 | 規則の表 | 既定=表と読み手/器だけ=読み手に呼び手の無い行 4 件/読むコードの無い行 8 id | [table.py](../../../../src/shibuya/engine/rules/table.py)・[rules-table.json](../../../design/rules-table.json) |
| 15 | 体の層(足した) | 既定=全員を見る版/腕=予約の版/器だけ=System 1 の 3 件/無いと宣言=倒れる | [engine/body/](../../../../src/shibuya/engine/body/) |
| 16 | 暦の口(足した) | 既定/器だけ=学校の長期休みの表 | [calendar.py](../../../../src/shibuya/engine/calendar.py) |
| 17 | 近接の判定(足した) | 既定=実距離 2.0 m/腕=距離の感度 | [proximity.py](../../../../src/shibuya/engine/proximity.py)・[spatial_index.py](../../../../src/shibuya/engine/spatial_index.py) |
| 18 | 時計と刻みの腕(足した) | 腕だけ(既定は全体で 1 つの時計・幅 60 秒) | [batching.py](../../../../src/shibuya/engine/batching.py)・[regional_clock.py](../../../../src/shibuya/engine/regional_clock.py)・[step_scope.py](../../../../src/shibuya/engine/step_scope.py) |

### 0-2 区分と ID の読み方

状態の区分は 4 つです。既定は既定のラン([段 1 §0-2](../day-flow.md) の `python -m shibuya.cli`)で動くもの、腕は切替口を立てると動くもの、器だけは口や欄があっても既定の結果を変えないもの、無いと宣言は [absent.py](../../../../src/shibuya/world/processes/absent.py) の一覧にあるものです。旧値の再現のためだけに残る切替口は「旧道」と書いて腕に入れません。

元の決定の ID は 4 つの形で書きます。

| 形 | 意味 |
|---|---|
| `10-12/§1-3`・`09-25/D-112` | [決定の索引](../../../design/decision-id-index.md) にある ID |
| `#124` | [IMPLEMENTED.md](../../../../IMPLEMENTED.md) の番号(`11-02r/§1` の #6・#7 と段 1 §11 の #11 などは、それぞれの表の番号) |
| routing 行 22 | [行き先の表](../../decision-routing-2026-11-01.md) §1 の行。本文は読まず、[つなぎの台帳](../../../design/bridging-ledger.json) の `DEC-22-*` の行で読みました |
| D-51・D-R2-5・D-W15 | 索引に無い旧の番号(コードの docstring の表記のまま)。grep で確かめた置き場は [凍結した PENDING](../../../log/pending-archive-2026-09-28.md)・[計画実行層の設計書](../../../design/v2-plan-executor-design.md)・[決定台帳](../../../design/v2-redesign.md) です |

指紋は [仕分けの表 11-04](../../behavior-audit-triage-2026-11-04.md) の行 ID と区分です。V は v3 で消える・変わる、K は本人の判断であるべき、D は外して無いと宣言する、E は式として残す(物理・保存則・制度の手順・物理的に止める仕組みの 4 種)です。表の行番号は古い HEAD `90258ef` の値なので、ここでは ID だけを書きます。

### 0-3 確かめた切替口

CLI の既定は `shibuya.cli.main` の引数の定義を読み出した値、環境変数の既定は各モジュールの腕の関数を呼んだ値です。

| 旗 | 環境変数 | 既定 | 区分 | 効く機能 |
|---|---|---:|---|---|
| `--space` | `SHIBUYA_SPACE` | 未指定 → `nav1` | `legacy` は旧道 | 3 |
| `--slope` | `SHIBUYA_SLOPE` | 未指定 → `wood` | 腕 `tobler` | 3・4 |
| `--turn-weight` | `SHIBUYA_TURN_WEIGHT` | 未指定 → `fixed` | 腕 `person` | 3 |
| なし | `SHIBUYA_NAV1_DENSITY` | `neighborhood` | 腕 `cell`・`unscaled` | 4・5 |
| `--geometry` | なし | `node` | 腕 `edge`(nav1 のランでは効かない) | 3 |
| `--area-source` | なし | `legacy` | 腕 `plateau`(nav1 のランでは効かない) | 5 |
| `--intent-max-ticks` | なし | 60 | 感度の腕 30・120 | 3 |
| `--move-search-radius` | なし | 5 | 感度の値 | 3 |
| `--exit-mode` | なし | `immediate` | 腕 `walk_to_platform`・`board_intent` は選ぶと止まる | 1・2 |
| `--derive-rule` | なし | `v2` | 腕 `v1`・`v2.1` | 2 |
| `--no-plan-executor`・`--no-outside-suppression`・`--no-plan-sleep` | なし | 立てない | 帰無腕 | 1・2 |
| `--queue-service` | なし | `on` | 帰無腕 `off` | 6 |
| `--seat-area-eatery`・`--seat-area-retail` | なし | `None` | 感度の腕 | 6 |
| `--seat-release` | `SHIBUYA_SEAT_RELEASE` | 未指定 → `walk` | `legacy` は旧道 | 6 |
| `--defect-fixes-1103` | `SHIBUYA_DEFECT_FIXES_1103` | 未指定 → `on` | `legacy` は旧道 | 6 |
| `--rate-rules` | `SHIBUYA_RATE_RULES` | 未指定 → `off` | `legacy` は旧道 | 1・2・11 |
| `--absent-processes` | `SHIBUYA_ABSENT_PROCESSES` | 未指定 → `stopped` | `legacy` は旧道 | 11 |
| `--ablate` | なし | 空 | 過程の id か `AB-*` で切る口 | 11 |
| `--weather-perturb` | なし | 立てない | 腕 | 7 |
| `--start-date` | なし | 空 → 2026-07-13 | 腕 | 7・16 |
| `--body-schedule` | `SHIBUYA_BODY_SCHEDULE` | 未指定 → `sweep` | 腕 `reserve` | 15 |
| なし | `SHIBUYA_RULES_42`・`SHIBUYA_RULES_42B` | どちらも `on` | `off` は旧道 | 14 |
| `--proximity` | `SHIBUYA_PROXIMITY` | 未指定 → `distance` | `cell` は旧道 | 17 |
| `--proximity-d` | `SHIBUYA_PROXIMITY_D` | 未指定 → 2.0 | 腕 1.0・2.5 | 17 |
| `--batch-width-s` | `SHIBUYA_BATCH_WIDTH_S` | 未指定 | 腕 | 18 |
| `--clock` | `SHIBUYA_CLOCK` | 未指定 → `global` | 腕 `regional`・`mixed` は口だけ | 18 |
| `--step-scope` | `SHIBUYA_STEP_SCOPE` | 未指定 → `all` | 腕 `changed` | 18 |

## 1. 鉄道

### 何をしているか

世界過程 `rail` が、時刻表どおりに渋谷のホームの便を進めます。1 日分の便を起動時に広げ、刻みごとに発車の刻みと比べるだけで、線路の上を走る列車は持ちません。読むのは W12 の発車の表で、暦の平日か土休かで行を選びます。遅れは作りません。

体が乗るのは答えが「乗車」のときです。ホームのセルに居れば乗車待ちに入り、居なければ直線で最も近く経路のあるホームの代表の節へ歩き、着くと乗車待ちに入ります。`_serve_board_queue` が停車中の便へ、待ち始めの刻み → 体の番号の順に乗せます。運賃 180 円の動きは世帯から外界へ、科目は「持ち出し」です。払えなければ `FARE_SHORT`、満員なら `TRAIN_FULL` で待ち続け、30 刻み待つと `NO_TRAIN` です。

発車は 1 刻み遅れて処理します。発車した便の乗客を舞台の外へ移し(`transit_state=2`)、便の人数を 0 に戻し、日課の実行部へ通知します(§2 の張り直し)。混雑率は渋谷で乗った客だけで測ります。

既定のランでは到着の処理に乗る体が居ません。`plan_executor=True` なので域外居住の抽選と帰りの便が止まり、`_arr_order` と `_return_queue` は空のままです。到着は日課の実行部が便のホームへ入る刻みで実行します(§2)。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 時刻表の運行・乗車の意図の保持・先着順・運賃・上限 `floor(2.0 × 定員 − 乗車人数)` だけの乗り残し。合成の世界は便が無く休み、乗車は `NO_TRAIN` |
| 腕 | `--exit-mode walk_to_platform`(§2)・帰無腕 `--no-plan-executor`(12% の域外居住の抽選と D-61 の帰りの便)・`--ablate AB-RAIL-EXECUTOR` |
| 器だけ | [rail_events.py](../../../../src/shibuya/engine/processes/rail_events.py)(`READ_RAIL_EVENTS=False`・呼び手なし)。線別の混雑率の上限 `cap_pct` は旧道の `_spread_arrivals` だけが読みます |
| 無いと宣言 | `absent.skip_train`(電車を見送る)。運行の乱れは `input.service_disruption` の欄だけ |
| 旧道 | `--rate-rules legacy` の受け入れ確率(150〜200% で 1.0→0.7) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/processes/rail.py](../../../../src/shibuya/engine/processes/rail.py) | 便の表・発車・定員と停車の表・運賃の口・計器 |
| [engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `_apply_board`・`_enter_board_queue`・`_serve_board_queue`・`_board_riders`・`rail_arrive`・`rail_depart`・`sync_transit_activity` |
| [engine/rate_rules.py](../../../../src/shibuya/engine/rate_rules.py) | 受け入れ確率を外す切替口 |
| [world/assets.py](../../../../src/shibuya/world/assets.py) | `ProcessAssets` の `tt_*`・`line_platform_cell`・`ext_node_line_idx` |
| [world/processes/first_batch.py](../../../../src/shibuya/world/processes/first_batch.py) | 台帳の行 `rail_operation_static`(engine_rule・conf 0.6)・`plan.rail_timetable` |
| [build/field/w12_external_nodes.py](../../../../src/shibuya/build/field/w12_external_nodes.py)・[w12_real_timetables.py](../../../../src/shibuya/build/field/w12_real_timetables.py)・[w12_rail_events.py](../../../../src/shibuya/build/field/w12_rail_events.py) | 構築側の W12 |
| [build/geo/w11_station_exits.py](../../../../src/shibuya/build/geo/w11_station_exits.py) | 構築側の W11(駅と出口) |

### 元の決定

D-R2-5・D-W14(静的ダイヤ)・D-51(乗車の意図の保持)・D-61(帰りの便=帰無腕だけ)・`09-25/D-112`・`10-13/W12`・`10-13b/§2`・`10-12b/§2`(実ダイヤ)・#94・#102・`10-06/§2` の SR16・`11-01/§2` と #132(受け入れ確率を外す)・routing 行 19〜23 と 107。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| M3 | K | ホームの外で選ぶと直線で最寄りの経路のあるホームの線へ |
| M4 | K | 同じホームの複数の便でも先頭の便で 1 回だけ試し、乗れる便には必ず乗せる |
| M5 | K | ホームで 30 刻み待つと意図を消して `NO_TRAIN` |
| B5 | K | ホームへ歩く途中の「なし」で立ち止まり、乗車の意図は掃除で消える |
| S22 | K | 着いた所がホームでなければ乗車の意図を黙って落とす |
| S25 | K | 保つ表に無い行為を選ぶと乗車の意図を落とす |
| S51 | E 物理 | 乗車の上限=定員の 200% |
| M27 | E 保存則 | 計画の退出で歩いて乗る体は運賃 0(腕だけ・直す対象) |
| F4 | K | ホームに居た体の乗車では列の印が消えない |

### 既知の穴

- 運賃の前の確かめは所持金 `r.money` だけです。支払いの本体は経済の段階 2 の支払いの部品で口座が先です(`pay_fares_many`)。M28 で列から席へ入る確かめは `_payable` に揃えましたが、乗車の確かめは揃っていません(コードの読み・件数は未計測)。
- 運賃 180 円は運賃表が未取得の expedient です(`FARE_YEN`・台帳 `DOC-tt23c-rail-fare`)。IC と切符の区別はありません。
- 定員のうち東横線・半蔵門線・銀座線の 3 線は推定です。`10-06/§2` の SR16 にある定員の更新(田園都市線 1,494 → 1,518 ほか)は rail.py に入っていません。
- 線別の混雑率の上限のうち山手・埼京・銀座の 3 線は令和 6 年度の値のままです(2025 値は親未確認とコードの注にあります)。
- 混雑率は舞台の中で乗った客だけなので、5,000 体では上限に届かないとコードの注にあります(`DOC-tt23c-rail-congestion`)。混雑率で不快と停車時間が増える §2.6 (ii) は未実装です。
- 停車は通過 1 刻み・終端 2 刻みです。終端の折返し時分は未取得です。
- 渋谷の発車の表だけを読み、着く体も発車の便から降ります(台帳 `EX-build.field.w12_external_nodes-ea8dc0c1`)。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 受容は `accept_quota`(混雑率 → 受容率) | 既定は 200% の上限だけ。受容率は旧道 | `resolve._serve_board_queue` の docstring・`resolve.begin_exit_walk` の docstring |
| いまの決め手=混雑率 150〜200% で受け入れ 1.0→0.7 | 11-01 の時点の文。今の既定は外した | つなぎの台帳 `DEC-22-crowdedBoard` の `why` |
| 待機・なしで意図を保つ | ホームへ歩く途中の待機となしは歩みを止め、意図は掃除で消える(同じ注に書いてある) | `resolve._BOARD_KEEP_ACTIONS` の注 |

## 2. 在圏(域内に居る・舞台の外)

### 何をしているか

日課の実行部 `PlanExecutor` が、誰がいつ舞台に居るかを持ちます。W17 の週次表を在圏ブロック(その日舞台に居る連続区間)に畳み、日の頭に到着・退出・就寝・起床の表を作り、刻みごとに resolve の口を呼びます。体の居場所は `transit_state` の 3 値で、0 が域内、1 が乗車中、2 が舞台の外です。

到着の時刻は、鉄道の体は「ブロックの開始に間に合う最も遅い便」がホームへ入る刻み、徒歩と道路の体はブロックの開始の刻みです。到着のセルは W11 の出口を重複を除いた 25 セル(docstring の値)へ通し番号で順に割り振ります。線・方面・ホームとは結び付けません。

退出は、域外居住者は毎ブロックの終わり、域内居住者は直後の行が「域外」のときだけです。今いるセルからその場で舞台の外へ出ます。会話中は最大 30 刻み繰り延べ、買い物と列は解きます。

就寝は W17 の就寝の行で `begin_planned_sleep` が実行します。就寝地のセルに居れば寝て、居なければ歩いて着いたら寝ます。乗車中・舞台の外・会話中の体には何もしません。起床の実行は就寝でない行の始まりごとの `wake_from_plan` です。

乗車で舞台の外へ出た体は、次のブロックの到着を張り直します。次のブロックが無ければ、60 分以後の最も早い便が進行中のブロックの終わりより前にあるときだけ、出口のセルへ戻します(E12)。舞台の外と乗車中の体には呼び出しを出しません([judge.py](../../../../src/shibuya/engine/systems/judge.py) が `arbiter.step` に `outside` を渡します)。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 日課の実行部・読み取り規則 v2・即時の退出・E1 の便・全員出勤・舞台の外の見送り・計画の就寝。W17 か W16 が無いランでは立ちません |
| 腕 | `--exit-mode walk_to_platform`(路線のホームへ歩いて乗る・運賃なし・上限は `--intent-max-ticks`)・`--derive-rule v2.1`・`v1`・`--calendar 1b`(`io_hook` で出入りを本人へ。中身は B)・帰無腕 3 本 |
| 器だけ | `--exit-mode board_intent` と `mode="native"` は `NotImplementedError`。`EventType.WORK_START`・`AT_HOME` は値だけで積みません。W12 の門のセルはエンジンが読みません |
| 無いと宣言 | `absent.event_injection`(催しの人の注入)。来るかどうかは `rate_rules` の `attendance`=全員出勤の宣言 |
| 旧道 | `--rate-rules legacy` の到着の分散 E8(E1 の便の ±8 便) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/presence.py](../../../../src/shibuya/engine/presence.py) | `PlanBlocks`(在圏ブロック)・`PlanExecutor`(表と実行と計器) |
| [agents/weekly.py](../../../../src/shibuya/agents/weekly.py) | W17 の読み口(語彙は二重定義) |
| [engine/systems/body.py](../../../../src/shibuya/engine/systems/body.py) | 系 `presence`・`plan_boundary` |
| [engine/systems/build.py](../../../../src/shibuya/engine/systems/build.py) | 組み立て(`home_cell`・`direction_node` を母集団から渡す) |
| [engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `begin_planned_sleep`・`wake_from_plan`・`place_at_external`・`rail_arrive`・`rail_depart`・`release_indoor`・`balk_queue`・`set_plan_state`・`begin_exit_walk` |
| [engine/arbiter.py](../../../../src/shibuya/engine/arbiter.py)・[engine/systems/judge.py](../../../../src/shibuya/engine/systems/judge.py) | 舞台の外の見送り |

### 元の決定

D-66(計画実行層)・D-62(就寝は計画の実行)・`09-25/D-112`・`09-25/D-115`・`09-29d/§1-6`・#68・#69・#134・`11-01/§2` と #132(出勤率と到着の分散を外す)・`10-12/§1-3`(存在の連続性)・`10-12/CA9`・`10-12/K9`・routing 行 1〜10・69・71。

### 棚卸しの指紋

presence.py は表の path の列に 1 度も出てきません(grep)。この層の定数(60 分の戻り・30 刻みの繰り延べほか)には行が無く、出入りの判断は routing 行 1〜10 で読みます。

| 行 | 区分 | 一言 |
|---|---|---|
| M13 | D | 域外・車内の体の起床候補を例外なく落とす |
| S52 | D | 域外の見送りは日課の実行部のランだけ |
| M23 | E 物理 | 移動の外で node を書き換えた体を節の点へ置き直す(今は瞬間移動=直す対象) |
| M26 | K | 非就寝の切れ目で寝ている体を起こす |
| S19 | K | 計画の就寝で、会話中・乗車中・域外の体は寝かせない |
| S20 | E 物理 | 寝床のセルと違っても節が同じならその場で寝かせる |
| S53 | E 物理 | 計画の退出で、代表の節に居るがセルの判定が外れた体をその場で待たせる |
| M27 | E 保存則 | 計画の退出で歩いて乗る体は運賃 0(腕だけ) |
| F4 | K | 計画の就寝の歩き出しでは列の印が消えない |

### 既知の穴

presence.py の冒頭に〔既知の穴・11-02〕として書かれ、[PENDING](../../../../PENDING.md) §2 の 17 に同じ題があります。

- 徒歩と道路の体が門でなく駅の出口のセルに現れます。
- 到着の約 6/25 が表参道と明治神宮前の出口のセルに出ます(最寄りの渋谷の出口のセルから 0.72〜0.91 km)。
- 同じ刻みの退出と到着は瞬間移動です。5,000 体 1 日で 18〜20 件・最大 1,355 m は旧既定の腕の値で、今の既定では未計測です(台帳 `DOC-nav1-presence-same-step-depart-arrive`)。
- 日の境目で計画と在圏がずれます(32,065 体と 4,281 体は day0 の表から数えた静的な数・ランでは未計測)。
- 戻りと 0 時の降ろしは先頭の出口のセルに偏ります。

ほかの穴は次のとおりです。

- ホームから出口までの所要時間はありません。退出は駅へ歩きません。
- W17 の出入りと就寝をエンジンが実行するのはつなぎです(`BR-W17-IO-SLEEP`・外す段 6-2)。
- W17 v2 は月曜の行しか無く、火〜金も月曜の予定を使います(`BR-K9-MONDAY`)。
- 2 日以上のランの日の境で体が一斉に張り直され、大きいセルでも 2〜3 刻み止まることがあります(`DOC-nav1-density-day-boundary-surge`)。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| LLM の「乗車/退去」で域外へ出た体 | `_apply_leave` は域外へ出ない(同じ docstring に「帰る」の意味は持たないとある)。張り直しの呼び手は `rail.step` の発車だけ | `presence.notify_departed_by_llm`・E12 の注 |
| 9a は受容関数を通して乗せる | 既定は 200% の上限だけ | presence.py の E4 |
| いまの決め手=`--attendance-rate 1.0` のくじ | CLI にその引数は無い(読み出した一覧に無い) | つなぎの台帳 `DEC-2-skipWork` の `why` |
| 設計書 §2・§3・§6 の 10 件 | PENDING §2 の 17 が「直す」と書く。表は未読 | [v2-plan-executor-design.md](../../../design/v2-plan-executor-design.md) |

## 3. 歩行とナビメッシュ

### 何をしているか

答えが「移動」なら行き先を決めます。対象が「なし」や説明語なら職場か自宅のうち今いない方(`commit.intents_from_responses`)、対象の語があれば `poi_target.resolve_move`、「あたり」は活動層の近傍です。店・人・寝床が別のセルにあるときは行為を意図として持ち、着いたら呼ばずに実行します([intent.py](../../../../src/shibuya/engine/intent.py)・上限 60 刻み)。

`_apply_move` は行き先をセルの代表の節にし、W3 の次の節の表で経路があるかを確かめます。nav1 でもこの確かめは W3 のままです。

経路の形は [NavPlanner](../../../../src/shibuya/world/navmesh_route.py) が 2 段で引きます。通りの選びは W1 の向きつきの辺の Dijkstra(曲がる 1 回=50 m・上り 1 m=3.8 m)、面の上の線は通り道の近くの帯の A* と funnel です。通り道の中で引けなければ全面に広げます。

歩ける面の資産は階ごとの 0.5 m の格子を塗ったもので、構築は [navmesh1.py](../../../../src/shibuya/build/space/navmesh1.py) です。行ごとの連なり(ラン)・その境(門)・縦の鎖(帯)に分け、階の間は接続口(階段・エスカレーター・エレベーター・スロープ)でつなぎます。位置は `r.xy` と `nav_fi`(階)で持ち、セルは面から導きます。経路の形と時間は状態でなく派生の値です(再開では引き直す)。

新しい行為を選んだ体は、その場に止まり経路を捨て、`node` を面の上の点に最も近い節にします。

資産の大きさは [#124](../../../../IMPLEMENTED.md) の記録で 7 階・ラン 221,784(第339 の注の値)・地上 797,320 m²・接続口 245 です。data を開いて確かめてはいません。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | nav1 の移動・活動層と意図の保持・Wood 2023 の坂・曲がる重み 50 m |
| 条件 | 合成の世界と `build_hash` の無い世界は legacy で回し、manifest の `space.effective` に書きます。本番の世界に `nav1_*` が無ければ `FileNotFoundError` で止まります |
| 腕 | `--slope tobler`・`--turn-weight person`(32〜62 m の一様)・`--intent-max-ticks 30/120`・`--move-search-radius` |
| 器だけ | `NavPlanner.candidates`(3 つの候補を本人が選ぶ口・呼び手なし)。`--geometry edge` は nav1 のランでは効きません(台帳 `DOC-nav1-arms-inert-edge-plateau`) |
| 無いと宣言 | `absent.py` に行はありません。衝突なしと経路の選びは nav1.py の `NAV1_EXPEDIENTS` とつなぎの台帳の宣言です |
| 旧道 | `--space legacy`(1 刻み 1 節・人/セルの密度の段) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/space/nav1.py](../../../../src/shibuya/engine/space/nav1.py) | `NavSpace`・`RoutePool`・`advance_kernel`・腕と manifest |
| [world/navmesh.py](../../../../src/shibuya/world/navmesh.py) | 資産と問い合わせ(`locate_run`・`astar_strips`・`funnel_points`・`w1_turn_dijkstra`・`cell_of`) |
| [world/navmesh_route.py](../../../../src/shibuya/world/navmesh_route.py) | 経路の形を引く `NavPlanner` |
| [world/graph.py](../../../../src/shibuya/world/graph.py) | W1 と W3 の次の節の表 |
| [engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `_apply_move`・`_apply_engine_step`・`_nav_step`・`_nav_stop`・`_nav_positions`・`nav_place` |
| [engine/commit.py](../../../../src/shibuya/engine/commit.py)・[engine/poi_target.py](../../../../src/shibuya/engine/poi_target.py) | 行き先の決定 |
| [engine/intent.py](../../../../src/shibuya/engine/intent.py)・[engine/activity.py](../../../../src/shibuya/engine/activity.py) | 意図の保持・活動層とあたり |
| [engine/geometry.py](../../../../src/shibuya/engine/geometry.py) | `desired_speeds`・Kladek の式・`EdgeGeometry`(腕) |
| [build/space/navmesh1.py](../../../../src/shibuya/build/space/navmesh1.py)・[mesh.py](../../../../src/shibuya/build/space/mesh.py)・[raster.py](../../../../src/shibuya/build/space/raster.py)・[sources.py](../../../../src/shibuya/build/space/sources.py) | 構築側 |
| [build/geo/w1_walk_graph.py](../../../../src/shibuya/build/geo/w1_walk_graph.py)・[w2_cells.py](../../../../src/shibuya/build/geo/w2_cells.py)・[w3_distances.py](../../../../src/shibuya/build/geo/w3_distances.py) | W1・W2・W3 の構築 |

### 元の決定

`10-03/§8`(空間 3-1〜3-10)・`10-06/§2`(SR10〜SR13・SR17)・`10-13b/§0-6`・#124・#126(版上げ 4 回目で既定へ)・`09-25/D-112`・`09-25/D-114`・#53・#54・C9 の G1(`docs/design/v2-c9-geometry-agenda.md`・索引の ID 不明)・`10-25/§2-5`(`--space legacy` の削除)・routing 行 11・14〜16。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| A02・B3 | K | 行き先の解けない移動を職場と自宅のうち今いない方へ |
| B4 | V | 移動を選んだ刻み・歩く途中で起こされた刻みは進まない(経路も捨てる) |
| B5 | K | 寝床へ歩く途中の「なし」で就寝の意図が消え立ち止まる |
| M19・S43 | K | 既定の重みで経路を引く・接続口の時間を重みに直す基準 1.34 m/s |
| S23 | E 物理 | 経路の行き止まりで `UNREACHABLE` |
| S46 | D(割れる) | 経路の形のキャッシュ 5 万件・出発の点を float32 に丸めて引く |
| S47 | V | 新しい行為を選んだ体を止め、node を最も近い節にする |
| A16 | K | 意図を持って歩いている体のセルの変化と到着満了の起床を落とす |
| A17 | K | 意図を立てて 60 刻み歩いても着かなければ `TOO_FAR` |
| A18 | V | 着いた意図を呼ばず実行し、順位の鍵は刻みの頭 |
| A40 | K | 着いて実行した後に戻す活動が無ければ活動なし・60 分 |
| S2・S3 | V | 注意の焦点の寿命・近づくの距離(`attention_on` のランだけ) |

### 既知の穴

- 人と人は衝突せず、避けません(`BR-NAV1-E2`・外す段 5-5)。
- 経路の選びは本人の判断でなく既定の重みです(`BR-NAV1-E1`)。
- 新しい行動で止まった体の `node` は最も近い節で、建物の中は入口の点です(`BR-NAV1-E4`・外す段 5-2)。
- 階段・エスカレーター・エレベーターの中の位置は入口の端か出口の端で、半分で跳びます(`BR-NAV1-E3`)。
- 通り道の中で着けない経路は全面の A* に落ちて曲がる重みが効きません(1 日の新しい経路の約 1 割=`BR-NAV1-E7` の文)。
- 面の材料の仮の値があります(幹線の両端 2.0 m=`BR-NAV1-B1`・横断の帯 4.0 m=`BR-NAV1-B2`・デッキの高さ=`BR-NAV1-B5`)。
- W1 の階をまたぐ辺のうち勾配の小さい 2 本が残っています(`DOC-nav1-w1-interband-flat-edges`)。
- 歩行者信号の処理は engine と world にありません(grep「信号」「traffic_signal」)。`absent.py` とつなぎの台帳にも行がありません。
- [PENDING](../../../../PENDING.md) §1-1 に `--space legacy` を消すと段の世界を回す口が無くなる問いがあります。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 資産 `nav1_corridor`=辺から 20 m | 構築の既定は `corridor_radius_m=40.0`(`NAV1_EXPEDIENTS` と `BR-NAV1-B12` も 40 m) | navmesh_route.py の docstring |
| `node` が既定=1 tick=1 ノード | CLI の `--geometry` の既定は `node` のままだが、既定のランは nav1 が位置幾何を置き換える | geometry.py の docstring・`world/graph.py` の expedient |
| 腕 `--space`・既定 legacy | #126 で既定 nav1 へ | IMPLEMENTED #124 の見出し(#126 が後の決定) |

## 4. 人の動きのモデル(足した)

### 何をしているか

歩く区間の所要時間は、区間の長さ ÷(本人の速さ × 坂の係数)です。本人の速さは母集団の seed と体の番号だけで決まる一様分布 1.00〜1.60 m/s です。坂の係数は Wood 2023 の舗装路の式で、経路に沿った前後 10 m の標高の差でならします。

混み具合は Kladek の式 `v/v0 = 1 − exp(−1.913 × (1/ρ − 1/5.4))` で、ρ が 5.4 人/m² 以上なら進みません。ρ は刻みの頭に面の上に居て建物の中でない体を数え、そのセルと、同じ層で面が接する 8 近傍の数を足し、面積の和 × 抽出の割合で割った値です(`NavSpace.per_m2`)。この係数は歩く区間にだけ掛かり、接続口の中には掛かりません(`advance_kernel`)。

接続口の時間は種類ごとの式です。階段は高さ ÷ 上下の速さ(24.6° の階段の値 × 本人の速さ ÷ 1.40)、エスカレーターは 0.5 m/s・30°、エレベーターは 0.75 m/s(仮)と待ち、スロープは坂の式で勾配を ±1/8 で切ります。容量は 1 分あたりの人数を刻みの長さで割り当て(最低 1 人・値の無い接続口は上限なし)、超えた体は前で待ちます。順は待ち始めの刻み → 体の番号で、1 刻みの割り当ては 4 回までです。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 上の全部(`SHIBUYA_NAV1_DENSITY=neighborhood`) |
| 腕 | `--slope tobler`・`SHIBUYA_NAV1_DENSITY=cell`・`unscaled` |
| 器だけ | `engine/body/system1.py` の `crowd_gait`(値は空・`BR-SYSTEM1-CROWD-GAIT`) |
| 無いと宣言 | `absent.py` に行はありません |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/space/nav1.py](../../../../src/shibuya/engine/space/nav1.py) | `slope_speed_factor`・`link_times`・`per_m2`・`surface_counts`・`kladek_factor`・`advance` |
| [engine/geometry.py](../../../../src/shibuya/engine/geometry.py) | `desired_speeds`・`kladek_speed_factor` |
| [world/state.py](../../../../src/shibuya/world/state.py) | `DENSITY_STAGE_EDGES_PER_M2`(Fruin の境) |

### 元の決定

C9 の G2(索引の ID 不明)・`10-06/§2` の SR11・SR12・R-61・R-63・R-64・#124・#126・`10-12/§1-6`・`10-12/§1-9`・routing 行 17・18。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| M20 | E 物理 | 歩く速さを体ごとに U(1.00,1.60) m/s で引く |
| M21 | E 物理 | 刻みの頭の密度から Kladek の減速を掛け、係数 0 以下はその刻み進めない |
| B7 | V | 接続口の容量=1 分あたりの人数 × 刻みの秒 ÷ 60 を切り下げ、最低 1 人 |
| S38・S39 | V | 接続口の割り当ては 4 回まで・先着順 |
| S40・S41・S42 | E 物理 | 接続口の時間の下限 1 秒・エスカレーターとエレベーターの値・スロープの勾配の切り |
| S44・S45 | E 物理 | 歩ける面積の下限 1 m²・在店や列の体を分子から外す |

### 既知の穴

- 密度の推定は近傍を足すので局所の混みを薄める向きです(`BR-NAV1-DENSITY-SAMPLE-SCALE` の文)。
- 孤立した断片 20 セルはセルだけのまま量子化が残ります(`DOC-nav1-density-isolated-fragments`)。
- 速さに年齢・疲れ・考え中の影響はありません。11-05 の 9-3d で「考え中も歩く速さは落ちない」を無いの一覧へ足す決定がありますが、`absent.py` にまだ行がありません([段 1 §11](../day-flow.md) の #15)。

### 文書とコードの差

なし(確かめた範囲)。

## 5. 混雑場(足した)

### 何をしているか

位置の確定で `world.cells.density` にセルの全員の数を書き、`density_stage` に段を書きます。nav1 の段は §4 の ρ を Fruin の境(0.30754・0.43056・0.71760・1.07640・2.15279 人/m²)で切った値です。変化の検出と B4 の描画はこの段を読みます(`los_from_stage`・`los_stage`)。

世界過程 `crowd` は流れの 3 値を作ります。移動者の割合が 0.20 未満なら滞留気味、0.20 以上で向きのそろいが 0.50 以上なら一方向で、ほかは「一定」です。移動者が 1 人も居ない刻みは、人の居るセルを全部滞留気味にします。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 密度・段・流れの 3 値 |
| 腕 | `--area-source plateau` は nav1 のランでは効きません(`DOC-nav1-arms-inert-edge-plateau`) |
| 器だけ | `flow_dir8`・`coherence`(読み手は状態台帳と試験だけ)・`mean_wait_ticks`(呼び手は試験だけ) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/processes/crowd.py](../../../../src/shibuya/engine/processes/crowd.py) | `_update_flow`・`queue_rows` |
| [engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `apply` の末尾の位置の確定 |
| [world/state.py](../../../../src/shibuya/world/state.py) | `compute_density`・`density_stage` |
| [engine/change_detect.py](../../../../src/shibuya/engine/change_detect.py) | セルの変化の検出(中身は C の起床) |

### 元の決定

D-R2-5・C9 §4 の改訂(索引の ID 不明)・#126・`10-12/§1-6`。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| M22 | V | 移動者の割合 0.20 未満を滞留気味、一貫性 0.50 以上を一方向とし B4 に出す |
| S48 | V | 移動者が 1 人も居ないとき、人の居るセルを全部「滞留気味」にする |
| A03 | V | セルの B4 の欄が 1 つでも変われば在席者全員を候補にする |
| A25 | D | 最初の検出は全セルを変化とする |
| A24 | E 物理 | 歩ける面積の下限=セル面積 × 0.15(`--space legacy` の密度の分母) |
| A50 | E 物理 | LOS の境界=Fruin |
| S50 | D(割れる) | M/M/c の平均待ちの近似(観測の欄だけ) |

### 既知の穴

- 建物の中の体は B4 の混み具合に入りません(`BR-NAV1-B4-LOS-FROM-STAGE`・外す段 5-2)。
- しきい値 0.20 と 0.50 は expedient です。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| M/M/c の平均待ち時間の近似・サービス率 μ=1/滞在上限 | 式は `queue_len ÷ (queue_len ÷ 15)` で、列があれば常に 15。μ も席数も使わない | crowd.py の `mean_wait_ticks` |

## 6. 席と列

### 何をしているか

店の席数はカテゴリの想定床面積(60〜500 m²・既定 80)÷ 1 席の面積(飲食と夜の店 2 m²・ほか 4 m²)を切り下げた値で、最低 1 です。

購入と食事が成立するとき、席があれば席の印 `poi_ref` を付けます。満席なら失敗でなく列に入ります(`queue_poi`・`queue_since`・`queue_action`)。答えが「並ぶ」のときは、対象が飲食店なら食事、それ以外は購入へ回します。

世界過程 `crowd` は刻みの頭に、席に着いて 30 刻みの体を解き、並んで 15 刻みの体を `INTERRUPTED` で列から外します。席が空いた分だけ並んだ順に入れて購入か食事を完了させるのは `_serve_poi_queue` です。店のセルに居ない体は列から外し、閉店した店の列は `CLOSED` で解散し、払えない体は `MONEY_SHORT`、棚が空なら `OUT_OF_STOCK` で離れます。

移動で歩き出した体は席の印を解き、移動か乗車で歩き出した体は列を離れます。行列の材料は `queue_rows(3)` で B4b へ渡します。

席とは別に、1 刻みに店が受け入れる数 `pois.capacity`(4 人)が取り合いの決着で効きます([commit.py](../../../../src/shibuya/engine/commit.py) の `capacity`)。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 上の全部(`--queue-service on`・`--seat-release walk`・`--defect-fixes-1103 on`) |
| 腕 | `--seat-area-eatery`・`--seat-area-retail`(感度)・帰無腕 `--queue-service off` |
| 器だけ | `mean_wait_ticks`・定数 `EAT_DWELL_MINUTES`(定義だけ) |
| 無いと宣言 | `absent.py` に行はありません。並ぶか・離れるか・席を立つかの判断は routing 行 28〜31 の行き先(段 3)です |
| 旧道 | `--seat-release legacy`・`--defect-fixes-1103 legacy` |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/processes/crowd.py](../../../../src/shibuya/engine/processes/crowd.py) | `seats_for_categories`・`can_admit`・`on_admit`・`step`・`queue_rows` |
| [engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `_apply_buy`・`_apply_eat`・`_apply_queue`・`_complete_buy`・`_complete_eat`・`_serve_poi_queue`・`release_indoor`・`balk_queue` |
| [engine/seat_release.py](../../../../src/shibuya/engine/seat_release.py) | 歩き出しで席を解く切替口 |
| [engine/defect_fixes_1103.py](../../../../src/shibuya/engine/defect_fixes_1103.py) | 欠陥 4 件の切替口と計器 |
| [engine/commit.py](../../../../src/shibuya/engine/commit.py) | 店の受け入れ数の取り合い |

購入と食事の中身は B(購入・食事)の担当です。

### 元の決定

`09-25/D-113`(③ 席へ捌く)・#43・#54(保存則の直し)・#101(2-4 V3)・`11-03/§3` と #138(M11・M28)・`10-25/§2-5`(vb24 の腕の削除)・世界過程設計書の 16 行表の行 2(索引の ID 不明)・R-8・routing 行 28〜31。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| B1 | V | 店ごとの受け入れ=min(1 刻みの受け入れ数, 在庫)。超えた分は落選 |
| B2 | K | 席に着いて 30 刻みたった体を一律に席から外す |
| M1 | K | 並んで 15 刻みたった体を列から外す |
| M2 | K | 満席なら自動で列に入れて OK を返す |
| M6 | E 物理 | 席数=想定床面積 ÷ 1 席の面積 |
| M8 | V | 同じ刻みの席と最後の 1 個を行の順で決める |
| M11 | E 物理 | 列の印の場所の整合(直した後の残りは F2・F4) |
| M28 | E 制度の手順 | 列から席へ入れる前の支払いの確かめ(`_payable` に揃えた) |
| S7 | K | 「並ぶ」の対象が飲食店なら食事、それ以外は購入 |
| S9・S11 | V | 再試行の回は容量 0・棚を超える買い手は行の順で落ちる |
| S24 | E 物理 | 席の印は移動で歩き出したときだけ解く |
| A15・S49 | V | B4b の行列は世界全体の上位 3 件・セルに最長 1 件 |
| F2 | K | 同じ刻みで列を捌く処理が新しい行為より先に回る |
| F4 | K | 計画の就寝・本人の予定の歩き出しと、ホームに居た体の乗車では列の印が消えない |

### 既知の穴

- 席数も 1 席の面積も実測ではありません。飲食の 2.0 は出所が無いとコードの注にあります。
- 乗車の歩き出しでは席を解きません(`DOC-vb24-seat-not-released-on-board`・店のセルの外の在席の残り 1.91% の 88% がこの道という記録の値)。
- F4 の歩き出しは列の印が残ります。安全網は給仕の前の居場所の確かめです。
- 席 30 分は錨 D8 との循環の警告が残っています([PENDING](../../../../PENDING.md) §1-1 の第340 の行)。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 容量 c の M/M/c 近似 | 席数と比べるだけで待ち行列の式は使わない | `resolve._apply_buy` の注・crowd.py の docstring |

## 7. 天気と環境

### 何をしているか

世界過程 `environment` は過程の順の先頭で、日の頭に太陽と天気を決めます。日の出・日の入り・太陽高度は暦の日付から計算します(NOAA の低次近似)。雨・気温・湿度・風・日照の出どころは再生日の W13 の行です。再生日は暦の日付が W13 の窓の中ならその日で、`--weather-perturb` のときと窓の外のときは季節 × 平日か土休 × 天候型の層から引きます。層が空なら隣の季節へ広げて警告します。

WBGT は再生日の気象と暦の太陽高度から時ごとに計算し(推定式は expedient)、21・25・28・31 の境で暑さ段 0〜4 にします。

更新は 5 分ごとです。日照の 3 値・暑さ段を更新し、体の層の口で体感温度を作り、`resolve.set_thermal` で全員に書きます。写像は暑さ段 → 2・4・6・8・10 で、日陰のセルは 0.86 倍です(§8)。舞台の外の体は日陰なしの値です。

描画の B3 は、組み立てが差し込む `_b3_words` が天候の語を再生日の W13 の表から、日照を暦の日付から、暑さを同じ暑さ段から作ります。夜かどうかは顕著行為の気づきの係数にも効きます(`is_night`)。

engine の中で雨や天候型が行為や歩く速さを変える処理はありません(`weather_type`・`stratum`・「雨」の grep)。天気が体に届くのは体感温度と B3 の語だけです。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 上の全部(規則の名 `calendar`・切替口なし) |
| 腕 | `--weather-perturb`・`--start-date`・`--environment-seed`・申込書の L0(`set_replay_date`) |
| 器だけ | なし |
| 無いと宣言 | 暑さで倒れる人は `absent.collapse`(§15) |

合成の世界は気象が無く、体感温度は 5 の固定です。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/processes/environment.py](../../../../src/shibuya/engine/processes/environment.py) | 再生日の決定・5 分ごとの更新・manifest の `weather` |
| [engine/solar.py](../../../../src/shibuya/engine/solar.py) | 太陽の位置と WBGT(構築側の式の写し) |
| [engine/body/rules.py](../../../../src/shibuya/engine/body/rules.py)・[engine/body/model.py](../../../../src/shibuya/engine/body/model.py) | 体感温度の写像 |
| [engine/systems/build.py](../../../../src/shibuya/engine/systems/build.py)・[perception/renderer.py](../../../../src/shibuya/perception/renderer.py) | B3 の語 |
| [world/assets.py](../../../../src/shibuya/world/assets.py) | W13 の読み口(`hourly_*`) |
| [build/field/w13_weather.py](../../../../src/shibuya/build/field/w13_weather.py) | 構築側の W13 |
| [tools/realworld_fetch/jma_etrn.py](../../../../tools/realworld_fetch/jma_etrn.py) | 気象庁のデータの取得 |

### 元の決定

D-R2-5・D-W15・`10-12b/§1-3`(天気と太陽の分け方)・`10-12b/§1-4`(開始日)・#88(10e B6)・#105(体の層)・`10-12/§1-5`・`input.weather`(`11-01/§8`)。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| A48 | E 物理(割れる) | 天候が W13 に無い日はその時の最頻値。同数は文字列の大きい方 |
| S18 | E 物理 | 体感温度を 0〜10 にクリップ |

`environment.py` は表の path の列に出てきません。

### 既知の穴

- 気象は東京 47662(北の丸公園)の 1 点で、都市の差を補正しません(台帳 `W13#1`)。
- WBGT と日射は推定です(`W13#2`・`W13#3`)。
- 天気の層の広げ方は未リサーチです(`BR-WEATHER-STRATUM-WIDEN`)。
- 雨や暑さが判断へ届くのは文だけです。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 天気の規則 `--weather-scheme calendar` | CLI にその引数は無い(calendar.py の docstring も消したと書く) | solar.py の docstring |
| `--calendar-weekday`・`--rng-scheme` を足す | CLI に無い | cli.py の `add_calendar_args` の注 |
| `weather` は tick 単位に線形補間・気温 × 影グリッド | 5 分ごとに時の値を保つ・暑さ段 × 日陰(`inputs.py` の注も認めている・文の直しは registry_hash に効くので次の版上げ) | first_batch.py の `weather` の `update_rule` |
| `daynight_solar` は 1 分 tick ごとに評価 | 5 分ごと | first_batch.py の `daynight_solar` の `update_rule` |

## 8. 日影(足した)

### 何をしているか

構築の W9 が街路の格子点の上に 5 分ごと 288 面の影のビットを作ります。夜は全部日陰、地下は常に日陰、建物に当たれば日陰です。作る日は定数 `SHADOW_DATES` の 8 日(2026-07-28 と 07-13〜07-19)です。

エンジンは暦の日付の影を読みます。無ければいちばん近い日の影を読み、警告と manifest の `shadow_fallback` を残します。影が 1 枚も無い世界は全セル日向になり、`shadow_missing=1` を立てます。セルの日陰は代表点に最も近い街路点 1 点のビットです。

使い道は体感温度の 0.86 倍だけです。B3 の暑さの語は日陰を見ません。

### 状態

既定です。腕はありません。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [build/vis/w9_shadow.py](../../../../src/shibuya/build/vis/w9_shadow.py) | 構築 |
| [engine/processes/environment.py](../../../../src/shibuya/engine/processes/environment.py) | `_shade_mask`・`_shade_at`・`nearest_shadow_date` |
| [world/assets.py](../../../../src/shibuya/world/assets.py) | `shadow_planes`・`cell_street_point` |

### 元の決定

D-W10(5 分刻み)・`10-12b/§1-3`・#88・#100(影 7 日)・知覚契約書 §3(係数 0.86・R3-2)。

### 棚卸しの指紋

表に日影の行はありません。

### 既知の穴

- セルの中の分布を持ちません(100 m 角で 1 点)。
- 影を作る日は 8 日だけで、ほかの日は近い日の影です(`W9#5`)。
- 大気差と遠い地形の遮蔽を見ません(`W9#4`)。デッキは地上と同じ扱いです(`W9#2`)。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 影は 2026-07-28 の 1 日ぶんだけ実在・無い日は全セル日向 | `SHADOW_DATES` は 8 日。無い日は近い日の影を読む(同じ docstring の後半にも書いてある) | environment.py の docstring の expedient の項 |

## 9. 騒音(足した)

### 何をしているか

構築の W10 が道路交通の式(ASJ RTN-Model 2018)から街路の点の騒音を作り、セルごとの昼と夜の段にします。エンジンと知覚は時刻で昼(6〜22 時)か夜の配列を読むだけです。動く車の台数(`traffic`)は騒音に入りません。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 静的な昼夜の段(B4 に載る・変化の検出に効く) |
| 器だけ | `cells.noise_stage`(動的な上書きの欄・書く系の宣言なし=カードの状態台帳の行)・`system1.noise_stage_at`(読み手なし) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [build/field/w10_noise.py](../../../../src/shibuya/build/field/w10_noise.py)・[road_names.py](../../../../src/shibuya/build/field/road_names.py)・[w10_ruler.py](../../../../src/shibuya/build/field/w10_ruler.py) | 構築 |
| [world/assets.py](../../../../src/shibuya/world/assets.py) | `noise_stage_for_hour`・`NOISE_DAY_HOURS` |
| [world/state.py](../../../../src/shibuya/world/state.py) | `noise_stage_for_tick` |
| [perception/renderer.py](../../../../src/shibuya/perception/renderer.py) | `PerceptionAssets.noise_stage_for_tick`(同じ 6〜22 時の切り) |

### 元の決定

D-W11・`10-03/§9-4`・#51・#77・`static_noise_field`(台帳の行・実行器の過程は無い)。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| A49 | E 制度の手順(割れる) | 騒音の段の昼夜の切替=6〜22 時 |

### 既知の穴

- 静的な場は区間別で、動く車は道の種類の既定のままなので食い違います(`W10#11`)。
- 回折・反射を見ません(`W10#5`)。
- 騒音→ D12′ の循環の警告が残っています([PENDING](../../../../PENDING.md) §1-1 の第340 の行)。

### 文書とコードの差

なし(確かめた範囲)。

## 10. 見通し(足した)

### 何をしているか

構築の W8 が街路の格子点(2.5 m)から POI・駅の出入口・建物が見えるかを建物の高さの場で判定し、セルごとの表にします。エンジンは次の 3 か所で読みます。

- `World.visible_pois`: セルから見える POI と視点の数(カテゴリ語の店の探索・古典の候補)
- `World.poi_visibility`: 自分のセルから見える数(店選びの可視順)
- `PerceptionAssets.visible_poi`: B2 の「見えるもの」

表は静的です。人や時刻で見通しは変わりません。

### 状態

既定です。腕はありません。`--signage-p-see` などの看板の腕は C の知覚の担当です。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [build/vis/w8_visibility.py](../../../../src/shibuya/build/vis/w8_visibility.py) | 構築 |
| [world/assets.py](../../../../src/shibuya/world/assets.py) | `load_visible_pois_by_cell`・`load_poi_own_cell_visibility` |
| [world/state.py](../../../../src/shibuya/world/state.py) | `visible_pois`・`poi_visibility` |
| [engine/poi_target.py](../../../../src/shibuya/engine/poi_target.py)・[engine/classical.py](../../../../src/shibuya/engine/classical.py) | 読み手 |

### 元の決定

D-W9・#52(段 2a)・#53(段 2b)・`09-25/D-114`。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| A05 | V | 見える店を視点数の降順で 8 件・目印 4 件まで持ち、B2 には店 3 件・目印 2 件だけ書く |
| A06 | V | 看板は可視順の先頭 1 店だけ |

### 既知の穴

- 体の居る点でなくセルの単位の表です。

### 文書とコードの差

なし(確かめた範囲)。

## 11. 世界過程 18 本

### 何をしているか

系 `world` が刻みの頭で `WorldProcessRunner.step` を呼び、`PROCESS_ORDER` の順に 18 本を回します。過程は状態を直接書かず、書くのは `engine.resolve` の口です。止めた過程も `step` は呼ばれ、中で何もしません。

### 状態

| 順 | 実行器の名 | 台帳の id(executor) | 既定の中身 | 状態 |
|---:|---|---|---|---|
| 1 | environment | `daynight_solar`・`weather`(none) | §7 | 既定 |
| 2 | rail | `rail_operation_static`(engine_rule・0.6) | §1 | 既定 |
| 3 | opening | `store_opening`(engine_rule・0.5) | 5 分ごとに W7 の行列と比べ、変わる店を開閉する。担当が店のセルに居れば `request_open_close`(記録 SCHEDULED)、居なければ代打(REPLACEMENT)。腕 `--duties arm` | 既定(担当か代打) |
| 4 | crowd | `crowd_field`・`indoor_occupancy`(none) | §5・§6 | 既定 |
| 5 | traffic | `vehicle_cross_section`(engine_rule・0.4) | 道の種類の既定交通量から時間帯の場を作り、時が変わると `cell_vehicles` を差し替える。読み手は計器と試験だけ | 既定(集計だけ) |
| 6 | delivery_inbound | `delivery_inbound`(llm_agent) | 5〜8 時の乱数の時刻(15% は最大 30 分遅れ)に未陳列の枠を積む。量は `max(1, 容量 × 0.05) × 2`。物は動かない | 既定(入力の宣言) |
| 7 | shelf | `shelf_stock_restock`(llm_agent) | 5 分ごとに棚が容量の 95% を割った営業中の店を見る。担当が居れば補充、10 時に今日まだの店を代打。腕 `--duties arm` | 既定(担当か代打) |
| 8 | waste | `waste_collection`(llm_agent) | 19 時に持ち物のある体が 1 個消費する。収集と売れ残りの廃棄は旧道だけ | 既定(一部)・収集は無いと宣言 |
| 9 | street_cleaning | `street_cleaning`(llm_agent) | 何もしない | 無いと宣言 |
| 10 | last_mile | `delivery_last_mile`(llm_agent) | 予定 0 個で休む | 無いと宣言 |
| 11 | bus_taxi | `bus_taxi_operation`(llm_agent) | 6〜23 時・10 分間隔で停留所の到着を ActualLog に書く。乗り降りなし。タクシーの処理は無い | 既定(記録だけ) |
| 12 | road_works | `road_works_occupancy`(llm_agent) | その日の辺を引くだけで占用しない | 無いと宣言 |
| 13 | hotel | `hotel_room_inventory`(engine_rule・0.4) | 21 時に域内に居る種別 VISITOR の域外居住の体を同じセルのホテルへ(1 POI 120 室)、9 時に全員解く。`_apply_sleep` の `has_bed` が読む | 既定 |
| 14 | infra | `infra_daily_load`(none) | 集計しない | 無いと宣言 |
| 15 | press | `press_official_release`(llm_agent) | 7・12・18 時に ActualLog に 1 行。文「鉄道各線は平常どおり運行しています」を salient が B4 へ | 既定 |
| 16 | large_event | `large_event`(engine_rule・0.3) | 環境の seed で会場 3 セルを引き、18 時と 21 時に開催の行を ActualLog へ。人は増えない | 既定(記録だけ)・注入は無いと宣言 |
| 17 | dispatch | `public_service_dispatch`(llm_agent) | `request` は −1 を返す | 無いと宣言 |
| 18 | salient | 行なし(結線器) | 倒れる率 0・出動なし。報道の行を在席者のいるセルの B4 へ渡す | 既定 |

台帳だけの行が 2 つあります。`goods_conservation`(none)と `static_noise_field`(none)で、実行器の過程はありません。

切替口は `--rate-rules`(旧道=受け入れ確率・到着の分散・催しの注入・ポイ捨て・売れ残りの廃棄・宅配・倒れる)と `--absent-processes`(旧道=ごみ収集・街路の清掃・道路工事・出動・電気と水)、過程ごとに切る `--ablate`(過程の id か `AB-*`)です。`--absent-processes legacy` と `--rate-rules legacy` は 11-05/§3-2 で消す予定です。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/processes/runner.py](../../../../src/shibuya/engine/processes/runner.py) | 実行器・順・切り替え・日の頭の張り直し・廃棄の報告 |
| [engine/systems/world.py](../../../../src/shibuya/engine/systems/world.py) | 系 `world` |
| [engine/processes/environment.py](../../../../src/shibuya/engine/processes/environment.py)・[rail.py](../../../../src/shibuya/engine/processes/rail.py)・[crowd.py](../../../../src/shibuya/engine/processes/crowd.py) | §7・§1・§5・§6 |
| [engine/processes/opening.py](../../../../src/shibuya/engine/processes/opening.py) | 開閉と権利台帳の持ち主 |
| [engine/processes/traffic.py](../../../../src/shibuya/engine/processes/traffic.py) | 断面の車 |
| [engine/processes/goods_flow.py](../../../../src/shibuya/engine/processes/goods_flow.py) | 納品・補充・廃棄・街路の清掃 |
| [engine/processes/logistics.py](../../../../src/shibuya/engine/processes/logistics.py) | 宅配・バス・道路工事 |
| [engine/processes/civic.py](../../../../src/shibuya/engine/processes/civic.py) | 出動・報道・ホテル・電気と水・催し |
| [engine/processes/salient.py](../../../../src/shibuya/engine/processes/salient.py) | 顕著行為と気づきの結線 |
| [engine/rate_rules.py](../../../../src/shibuya/engine/rate_rules.py)・[engine/absent_processes.py](../../../../src/shibuya/engine/absent_processes.py) | 切替口と manifest の印 |
| [build/field/w7_planspec.py](../../../../src/shibuya/build/field/w7_planspec.py) | W7 の営業時間(法規の上限を構築で畳む) |

### 元の決定

D-R2-1・D-R2-5・`10-12/§1-1`(CP6)・`11-01/§2`・`11-01/§3`・`11-01/§10-1`・`11-01/§10-2`・`11-01/§10-3`・`11-02r/§1`(#7)・#132・#133・#136・routing 行 10・41〜43・73・83・99・101〜111。

### 棚卸しの指紋

表の path の列に `processes/` が出るのは crowd.py と rail.py だけです(§1・§5・§6)。civic・goods_flow・logistics・opening・traffic・environment・salient は棚卸しの行に出てきません。それらの判断の置き場は routing 行で読みます。関わる行は次のとおりです。

| 行 | 区分 | 一言 |
|---|---|---|
| S26 | E 物理的に止める仕組み | 権利の無い開閉店も止めない |
| A39 | V | 気づきの係数・顕著な出来事は 1 刻み 200 件まで先着 |
| A53 | V | 気づきの抽選の鍵 |

### 既知の穴

- `executor=llm_agent` の 9 行は、既定では人の判断で動いていません(`--duties arm` の shelf を除く)。担い手の割合は `opening`・`shelf` の計器 `role_actions` と `fallback` で読みます(値は未確認)。
- 納品はまだエンジンの乱数で動きます(`absent.inbound_delivery` の `engine_stopped=False`)。E5 と気象の文と一緒に次の版上げです([PENDING](../../../../PENDING.md) §2 の 3)。
- 廃棄の sink は 19 時の消費だけで、外すかは判断待ちです(PENDING §1-1 の第340 の行)。
- 計画の就寝 `begin_planned_sleep` はホテルの部屋を見ません(コードの読み)。部屋を読むのは答えが「就寝」の `_apply_sleep` だけです。
- 乗客がいないバスの扱いは routing 行 108 が要判断と書いています。運転士の体の有無は未確認です。
- 報道の文は固定で、区の決定と結びません(`input.ward_policy` は欄だけ)。
- 循環の警告が残る組は PENDING §1-1 の第340 の行にあります。
- 世界カタログ 57 分類のうち台帳が覆うのは 23 です(`build_registry().coverage_report()` の値)。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 補充点=棚容量の 80% | `REORDER_FILL_RATIO = 0.95` | goods_flow.py の docstring([段 1 §11](../day-flow.md) の #11) |
| 過程数(5)ぶんのループ | 18 本 | runner.py の `step` の注(段 1 §11 の #12) |
| 報道の到達=全セル | 在席者のいるセルだけ(`_broadcast_events`) | civic.py の docstring と `summary`・[段 1 §9](../day-flow.md) の行 15 |
| 催しは 18 時に記録 | 18 時と 21 時の 2 回(`_arrive`・`_leave` が `_log_held`) | [段 1 §9](../day-flow.md) の行 16 |
| 駆動の主体は `executor=llm_agent` が示す | 既定はエンジンの規則か代打 | first_batch.py の冒頭・各行の `executor` |
| 環境変数 `SHIBUYA_WARD_AREA_M2` | 定数の名で環境変数ではない | カードの logistics.py の行 |

## 12. 世界の台帳と検査(足した)

### 何をしているか

世界過程と計画の仕様を 1 つの名前空間の台帳に宣言します。実行器は起動時に憲法 5 の検査を走らせ、通らなければ止まります(`check_constitution5`)。台帳のハッシュは manifest に載ります。過程の実績は追記専用の ActualLog に書き(保持 7 日)、遵守率を計器で読みます。

`build_registry()` の結果は過程 21 行・PlanSpec 4 行(`plan.bus_timetable`・`plan.opening_hours`・`plan.rail_timetable`・`plan.road_works`)です。executor の内訳は llm_agent 9・engine_rule 5・none 7 です。

循環の検査(`drives_from` と採点する系の重なり)は CI の試験が読みます。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 起動時の検査・`registry_hash`・ActualLog |
| 器だけ | `drives_from`・`absence`・`input_decl` の欄(`as_dict` に入らない=宣言だけと first_batch.py の注) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [world/processes/records.py](../../../../src/shibuya/world/processes/records.py) | レコードの型 |
| [world/processes/relations.py](../../../../src/shibuya/world/processes/relations.py) | 関係 4 本 |
| [world/processes/registry.py](../../../../src/shibuya/world/processes/registry.py) | 台帳 |
| [world/processes/first_batch.py](../../../../src/shibuya/world/processes/first_batch.py) | 宣言(データだけ) |
| [world/processes/constitution.py](../../../../src/shibuya/world/processes/constitution.py) | 憲法 5 の検査 |
| [world/processes/actual_log.py](../../../../src/shibuya/world/processes/actual_log.py) | ActualLog |
| [world/processes/circularity.py](../../../../src/shibuya/world/processes/circularity.py) | 循環の機械検査 |
| [world/processes/deletion_candidates.py](../../../../src/shibuya/world/processes/deletion_candidates.py) | 削除候補の追記 |

### 元の決定

D-R2-2・D-R2-4・D-R2-6・`11-01/§3`・`11-02r/§1`(#6)・#133・#136。

### 棚卸しの指紋

表に行はありません。

### 既知の穴

循環の重なりの多くは警告のままです(PENDING §1-1 の第340・第342 の行)。

### 文書とコードの差

§7 と §11 の差の行を見てください。

## 13. 無いと宣言と入力の宣言(足した)

### 何をしているか

[absent.py](../../../../src/shibuya/world/processes/absent.py) が世界に無い過程と判断の一覧を、[inputs.py](../../../../src/shibuya/world/processes/inputs.py) が境界の外から一方向に入るものの一覧を持ちます。どちらも宣言だけで挙動を変えません。計器 [absent_declarations.py](../../../../tools/instruments/absent_declarations.py) が Markdown に出します。

### 状態

無いの一覧は 26 件です。

| 群 | 件数 | id(`absent.` を略す) |
|---|---:|---|
| 主体が居ない | 8 | `waste_collection`・`street_cleaning`・`parcel_delivery`・`road_works`・`public_service_dispatch`・`event_injection`・`hiring_firing`・`power_water` |
| 無いでない言い換え | 2 | `inbound_delivery`(入力)・`ordering`(初期の予定) |
| 口が無い | 13 | `skip_train`・`item_qty`・`price_balk`・`third_joiner`・`replan`・`eat_home`・`deliberate`・`utterance`・`reflect_day`・`plan_fix_surprise`・`serve_customer`・`change_price`・`collapse` |
| 率を外した | 2 | `litter`・`discard_unsold` |
| 効果の先が無い | 1 | `help_refuse_effect` |

`engine_stopped=False` は `inbound_delivery` だけです。

入力の一覧は 13 件で、値のある 5 件(`input.weather`・`timetable`・`calendar`・`external_nodes`・`row_sales`)と、欄だけの 7 件(`visitor_population`・`economy_prices`・`ward_policy`・`service_disruption`・`event_info`・`through_traffic`・`signage_text`)、納品の欄 `inbound_goods` から成ります。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [world/processes/absent.py](../../../../src/shibuya/world/processes/absent.py) | 無いの宣言 |
| [world/processes/inputs.py](../../../../src/shibuya/world/processes/inputs.py) | 入力の宣言 |
| [world/processes/records.py](../../../../src/shibuya/world/processes/records.py) | `Absence`・`InputDecl` |
| [engine/absent_processes.py](../../../../src/shibuya/engine/absent_processes.py)・[engine/rate_rules.py](../../../../src/shibuya/engine/rate_rules.py) | エンジンの側の切替 |

### 元の決定

`11-01/§1`・`11-01/§2`・`11-01/§8`・`11-01/§10-1`・`11-01/§10-3`・`11-02r/§1`(#7)・#133・文案は [routing](../../decision-routing-2026-11-01.md) §3。

### 棚卸しの指紋

表に宣言そのものの行はありません。M24 D(手伝い)と S6 D(断る・通報)が同じ題です。

### 既知の穴

- 11-05 の 9-3d・9-5 で足す 2 件がまだ入っていません([段 1 §11](../day-flow.md) の #15)。
- 外す段が空欄の行があります(文案のまま)。
- 人の衝突は無いの一覧に行が無く、つなぎの台帳の `BR-NAV1-E2` にだけ書かれています。歩行者信号はどちらにも行がありません(§3)。

### 文書とコードの差

`absent.deliberate` の「既定は起床のたびに全部 L2」は語の衝突です([段 1 §11](../day-flow.md) の #14)。

## 14. 規則の表

### 何をしているか

法と制度を出典と版つきの表で持ちます。表は [rules-table.json](../../../design/rules-table.json)(形式 `shibuya.rules-table/2`)の 30 行・28 id で、machine 16 行・human 14 行・norm 0 行です。`Rules.get(id, asof)` が `asof` の日に効いている版を返します。表の sha を manifest と日次の記録の `rules_version` に書きます。

machine は機械が守らせる行、human は人が知っていて人が取り締まる行で、機械は止めません。最低賃金は human で、`params.bridge` の machine のつなぎだけが床を当てます。

### 状態

| 区分 | id | 読み手 |
|---|---|---|
| 既定 | `consumption_tax.standard_rate`・`minimum_wage.tokyo` | [economy/anchors.py](../../../../src/shibuya/economy/anchors.py)(`wages.py`・`stage2.py` が使う) |
| 既定(給料日) | `income_tax.withholding_monthly`・`resident_tax.special_collection_tokyo_ward`・`resident_tax.basic_deduction`・`resident_tax.adjustment_credit_tokyo_ward`・`resident_tax.non_taxable_tokyo_ward`・`health_insurance.kyoukai_tokyo`・`child_support_levy.rate`・`pension.employees_rate`・`child_care_contribution.rate`・`employment_insurance.rate_general` | [economy/taxes.py](../../../../src/shibuya/economy/taxes.py)。既定の 1 日のラン(7 月 13 日)に給料日は来ません |
| 既定(レジ・日の締め) | `consumption_tax.invoice_rounding`・`consumption_tax.filing_deadline` | economy/taxes.py |
| 器だけ | `consumption_tax.reduced_rate`・`credit.total_volume_cap`・`credit.interest_cap`・`labor.overtime_premium` | taxes.py の読み手に呼び手なし(taxes.py の表による) |
| 腕 | `labor.statutory_hours`・`labor.weekly_rest_day` | [calendar3/layer.py](../../../../src/shibuya/engine/calendar3/layer.py)(`--calendar-3 arm`)。`weekly_rest_day` は構築の [w20_calendar_1a.py](../../../../src/shibuya/build/sched/w20_calendar_1a.py) も読む |
| 読むコードなし | `late_night_alcohol.residential_ban`・`food_business.licence`・`building_lease.termination_notice`・`road_use.police_permit`・`road_occupancy.shibuya_ward_road`・`outdoor_ad.tokyo_permit`・`national_pension.premium`・`national_health_insurance.shibuya` | src と tools の `.py` に id の文字列が無い(grep)。`check_rule_bridges` が全行の `params.bridge` だけを見ます |

旧道は `SHIBUYA_RULES_42=off`(天引き 0・レジの税は売った時点で政府へ)と `SHIBUYA_RULES_42B=off`(空欄 3 件を埋める前の値)で、どちらも CLI の旗はありません。

深夜の酒類の規則は表の `applies_to` が `plan.law_cap_key == 'shinya_shurui'` を指します。実際の営業時間の上限は構築の [w7_planspec.py](../../../../src/shibuya/build/field/w7_planspec.py) の `LAW_CAPS` に直書きして W7 に畳んであり、表を読みません。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/rules/table.py](../../../../src/shibuya/engine/rules/table.py) | `Rule`・`Source`・`Rules`・`load`・`rules_version` |
| [docs/design/rules-table.json](../../../design/rules-table.json) | 表の中身 |
| [economy/taxes.py](../../../../src/shibuya/economy/taxes.py)・[economy/anchors.py](../../../../src/shibuya/economy/anchors.py) | machine の行の読み手・最低賃金と消費税 |
| [engine/economy_rules.py](../../../../src/shibuya/engine/economy_rules.py) | 旧道の切替口・給与の天引きの材料 |
| [engine/run.py](../../../../src/shibuya/engine/run.py)・[engine/systems/state_io.py](../../../../src/shibuya/engine/systems/state_io.py) | 版の記録 |
| [tests/engine/rules/test_rules_table_schema.py](../../../../tests/engine/rules/test_rules_table_schema.py) | 行数(30・28)と写しの検査 |

### 元の決定

`10-12/§1-12`・`10-12/CP10`・`11-01/§5`・#91(1-4)・#120(4-2)・#122(4-2b)・#131・`10-25/§2-5`・`11-05/§3-2`(`SHIBUYA_RULES_42`・`42B` を消す)・R-106・R-113・R-118。

### 棚卸しの指紋

表の path の列に `engine/rules` も `economy/` も出てきません(grep で 0 行)。

### 既知の穴

- human の行に検知と反応の口がありません。違反は記録の器だけです(`economy.stage2` の `rules.minimum_wage_shortfall`)。
- machine の行の判定を `labor.overtime_premium`・`credit.interest_cap` にも掛けるかは判断待ちです([PENDING](../../../../PENDING.md) §1-1 の第340 の行)。
- `params.bridge` を行の欄へ移す形式の版 3 は未着手です(PENDING §2 の 3)。
- 管轄の欄は仮決定の答申待ちです(PENDING §3 の末尾)。
- 天引きの仮の形が多数あります(台帳 `DOC-rules42-*`)。
- 75 歳以上の後期高齢者医療の行はありません(`DOC-rules42b-late-elderly-medical-blank`)。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 26 行・24 の id | 30 行・28 id | table.py の docstring(試験は 30・28) |
| 実在の規則 4 行・1-4 では読み手を作らない・表を import するのは 2 か所 | 30 行で、読み手は economy と calendar3 にある | test_rules_table_schema.py の docstring |

## 15. 体の層(足した)

### 何をしているか

本人の体の規則を 1 つの持ち主にまとめた層です。値は 3 つの内受容で、空腹・疲れ・体感温度です。

- 疲れは 30 刻みごとに +1、就寝中は −2、在店かその場で持続中は 10 刻みごとに −1 です。
- 空腹の既定はエネルギー収支です。中身は B の食事の担当です。
- 体感温度は §7 のとおりです。
- 刻み 0 の値は空腹 2・疲れ 2・暑さ 5 で、自前です。

値を書くのは `resolve` の `advance_body`・`set_thermal`・`initialize`・`initialize_energy` の口に限ります。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | `--body-schedule sweep`(全員を見る) |
| 腕 | `--body-schedule reserve`(次に段を越える時刻を予約する・結果は全員を見る版と同じと docstring にある)・`SHIBUYA_BODY_BOUNDARY_GAUGE=1`(計器) |
| 器だけ | [system1.py](../../../../src/shibuya/engine/body/system1.py) の 3 件=ロンバード効果・混雑の中の歩き方と避け方・大きな音に注意が向く(値は `None`) |
| 無いと宣言 | `absent.collapse`(倒れる)。率 3.0 件は旧道 `--rate-rules legacy` だけ |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/body/rules.py](../../../../src/shibuya/engine/body/rules.py) | 値と純関数・`BODY_RULES`・`BODY_EXPEDIENTS` |
| [engine/body/model.py](../../../../src/shibuya/engine/body/model.py) | `BodyModel`(持ち主)・manifest |
| [engine/body/schedule.py](../../../../src/shibuya/engine/body/schedule.py) | TM5 の予約 |
| [engine/body/system1.py](../../../../src/shibuya/engine/body/system1.py) | 器 3 件 |
| [engine/systems/body.py](../../../../src/shibuya/engine/systems/body.py) | 系 `body` |

### 元の決定

`10-12/§1-5`(③ 群)・`10-12/TM5`・`10-12/§4-2`・#105・D-118・routing 行 83。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| S18 | E 物理 | 体感温度を 0〜10 にクリップ |
| A12 | D | 疲れの値に「体力」の名 |
| A13・A14 | V | 空腹の語は段 2 以上だけ・内受容の段 4/7/9 |
| S14 | D | 「休憩」で疲れ −3(v1・v2 だけ) |
| S15 | D | 空腹 v1 のとき購入と食事で −4 |

### 既知の穴

- 自然変動の値は自前です(`BR-BODY-NATURAL-VARIATION`)。写像と掛け先は expedient です(`BR-BODY-FELT-MAP`・`BR-BODY-SHADE-TARGET`)。
- 眠気で起きる・寝る処理はありません。就寝と起床は日課の時刻です(§2)。
- 考えながらの費用と体から心への影響は新しい題です(11-05 の 9-3d)。

### 文書とコードの差

なし(確かめた範囲)。

## 16. 暦の口(足した)

### 何をしているか

日付・曜日・祝日・季節・土休・営業時間の表の行を `SimCalendar` 1 つで引きます。開始日の既定は 2026-07-13(月)です。祝日は内閣府の CSV から読み、無ければ空で警告します。祝日は土休に数え、曜日 7 日の表では日曜の行、W7 では祝日の行(無い店は日曜の行)です。鉄道の平日か土休か、天気の層、営業時間の行、日ごとの乱数の鍵がここを読みます。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | 上の全部 |
| 腕 | `--start-date`・`--holiday-csv`・`--sim-days` |
| 器だけ | `--school-holidays`(学校の長期休みの表は渡す形だけで中身は空) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/calendar.py](../../../../src/shibuya/engine/calendar.py) | `SimCalendar`・`load_holidays`・`check_start` |
| [world/processes/inputs.py](../../../../src/shibuya/world/processes/inputs.py) | `input.calendar` |
| [engine/systems/state_io.py](../../../../src/shibuya/engine/systems/state_io.py) | K9 の月曜の行で引くつなぎ |

### 元の決定

`10-03/A1`・`10-03/A1-1`・`10-03/A1-2`・`10-03/A1-3`・`10-12b/§1-4`・`10-12/K9`・#80・#88。

### 棚卸しの指紋

表に行はありません。

### 既知の穴

- 年末年始などの慣行の休みはありません(未リサーチ・宣言)。
- 祝日を日曜の行で読むのは未リサーチの expedient です。
- 日曜始まりのランの 0 日目は W17 に行が無く全員が舞台の外で待ちます(`DOC-ca3-weekend-k9`)。

### 文書とコードの差

| 文書の記述 | コード | 場所 |
|---|---|---|
| 給料日は今は誰も読まない | 経済の段階 2 が 25 日の暦を作って読む(`economy_stage2.py` の `payday_calendar`・`stage2.py` の `plan.is_payday`) | calendar.py の docstring |

## 17. 近接の判定(足した)

### 何をしているか

会話が届くかを実距離で判定します。舞台の中・同じ層・距離 2.0 m 以内か、同じ店の中です。層ごとの格子の索引 `SpatialIndex` を刻みごとに作って捨てます。知人に気づく確率もここにあります(関係の腕で使う)。会話そのものは B の担当です。

### 状態

| 区分 | 中身 |
|---|---|
| 既定 | `--proximity distance`・d=2.0 m |
| 腕 | `--proximity-d 1.0`・`2.5` |
| 旧道 | `--proximity cell` |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/proximity.py](../../../../src/shibuya/engine/proximity.py) | 切替口・`ProximityRule` |
| [engine/spatial_index.py](../../../../src/shibuya/engine/spatial_index.py) | 近傍の索引 |
| [engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `talk_within_reach` |

### 元の決定

`10-03/§4`・`10-03/§4-2`・#97・#101・R-62・R-79。

### 棚卸しの指紋

| 行 | 区分 | 一言 |
|---|---|---|
| S4 | E 物理 | 会話の成立 2 m・離脱 3 m |
| M16 | E 物理 | 返事の時点で届かなければ不成立 |
| S36 | V | セル離脱の判定を開始のセルと比べる |

### 既知の穴

- 同じ店の中は距離を見ません(B5 の単位=空間の段 2 までのつなぎ)。
- 声の届く距離は固定で、音の伝わり方は空間の段 3 の題です(`10-03/§4-1`)。

### 文書とコードの差

なし(確かめた範囲)。

## 18. 時計と刻みの腕(足した)

### 何をしているか

進行役は時刻の窓で回し、既定の幅は 60 秒で刻みと同じです。腕で次の 3 つを選べます。どれも docstring に「結果は既定と同じ」か「一致が条件」とあり、動かして確かめてはいません。

- `--batch-width-s`: 窓の幅(刻みの幅の約数)
- `--clock regional`: 区域ごとの時計(セルの重心を 500 m で束ねる)。`mixed` は口だけで選ぶと止まります
- `--step-scope changed`: 何かあった体だけ走査する

### 状態

腕です。既定は `global`・`all`・幅 60 秒です。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [engine/batching.py](../../../../src/shibuya/engine/batching.py) | 窓の待ち行列 |
| [engine/regional_clock.py](../../../../src/shibuya/engine/regional_clock.py) | 区域ごとの時計 |
| [engine/step_scope.py](../../../../src/shibuya/engine/step_scope.py) | 走査の絞り込み |
| [engine/systems/conductor.py](../../../../src/shibuya/engine/systems/conductor.py) | 進行役 |
| [engine/clock.py](../../../../src/shibuya/engine/clock.py) | シミュレーションの時計 |

### 元の決定

`10-12/§4-2`(TM1・TM6)・#103・#114。

### 棚卸しの指紋

表に行はありません。

### 既知の穴

- メッセージと電話は区域の時計では欄だけです(regional_clock.py の docstring)。
- 印は写しとの比べで付けます(`DOC-tm234-t3-mark-by-copy`)。

### 文書とコードの差

なし(確かめた範囲)。

## 19. 読んでいないファイル

全文を読んだのは rail.py・presence.py・nav1.py・crowd.py・environment.py・traffic.py・civic.py・goods_flow.py・logistics.py・opening.py・solar.py・rate_rules.py・absent_processes.py・seat_release.py・defect_fixes_1103.py・rail_events.py・economy_rules.py・absent.py・inputs.py・rules/table.py・world/graph.py・world/state.py・systems/body.py・systems/world.py・system1.py です。

| ファイル | 読み方 |
|---|---|
| resolve.py | 660〜809・1500〜1884・2040〜2340・2368〜2376・2417〜2466・2556〜2701・2830〜2864・2905〜2934・3101〜3435 の範囲と grep |
| commit.py | 750〜794 と grep |
| poi_target.py・chooser.py・classical.py | 読んでいません(grep と棚卸しの記述) |
| intent.py・activity.py | 冒頭の docstring |
| geometry.py | 冒頭 160 行(`EdgeGeometry` の本体は未読) |
| navmesh.py・navmesh_route.py・navmesh1.py | 冒頭(110〜150 行)。mesh.py・raster.py・sources.py はカードの一覧だけ |
| salient.py | 1〜420 行 |
| world/assets.py | 828〜907 行と grep |
| agents/weekly.py・agents/state.py | weekly.py は 1〜90 行、state.py は grep |
| engine/arbiter.py・systems/judge.py・systems/perceive.py | judge.py と perceive.py は一部の行、arbiter.py は読んでいません(段 1 と棚卸しの記述) |
| records.py・registry.py・relations.py・actual_log.py・constitution.py・circularity.py・deletion_candidates.py | カードと `build_registry` の実行結果 |
| first_batch.py | 冒頭 120 行と `build_registry` の実行結果 |
| body/model.py・body/schedule.py | カード。body/rules.py は 1〜150 行と `felt_cells` |
| calendar.py | 1〜180 行と grep |
| proximity.py・spatial_index.py・regional_clock.py・step_scope.py・batching.py・clock.py | 冒頭の docstring |
| 構築側(w7・w8・w9・w10・w11・w12・w13) | 冒頭の docstring。w7 は `LAW_CAPS` の頭も |
| economy/taxes.py・anchors.py | taxes.py は冒頭、anchors.py は 245〜404 行 |
| 試験 | test_rules_table_schema.py の 1〜120 行だけ |
| 設計書と答申 | 計画実行層の設計書・空間の設計の下書き・行き先の表は本文を読んでいません。原文は索引の見出しで引き、読んだ本文は 10-25 §2-5 と 10-06 の SR16 だけです |
| 記録 | `docs/bench/analysis/` の README は開いていません(値は docstring と IMPLEMENTED と段 1 の引用) |
| data | 開いていません |

## 20. 未確認

- 資産の中身を確かめていません。W13 の窓に 2026-07-13 があるか(構築の定数の窓 2025-09-01〜2026-08-31 の中です)・影のファイルの実在・便の数・出口 25 セル・ナビメッシュの大きさは、docstring と IMPLEMENTED の値です。
- ランを回していないので、既定のランの乗車・列・席・補充の担い手の件数は未確認です。
- 同じ刻みの退出と到着と、日の境目の体の数の今の既定の値は未計測です(presence.py の docstring の注)。
- 運賃の前の確かめ(§1 の既知の穴)の影響の件数は未計測です。
- `--geometry edge` と `--area-source plateau` が nav1 で効かないのは台帳の記録の値で、動かしていません。
- 窓の幅・区域の時計・走査の絞り込みの「結果が同じ」は docstring の記述です。
- S46 の float32 の丸めで経路の形が変わらないかは、仕分けの表も未確認と書いています。
- 運転士の体が母集団に居るかは未確認です(routing 行 108 の文)。
- つなぎの台帳の行は id と文の先頭を読みました。全 794 行の網羅ではありません。
