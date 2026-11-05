# シミュレーションの 1 日の流れ(把握の資料 段 1)

> 発注は [返事その 6](../../design/prompt-2026-11-05-reply6.md) §3-1 の 2 です。今のコードの現状を書きます。あるべき姿は [仕様書](../../design/spec/) の担当なので、ここには書きません。
> 正はコードです。HEAD `15b6bbd` のコードを読み、既定の値は CLI の引数の定義と各モジュールの腕の関数を Python で読み出して確かめました。この文書のためにランは回していません。`data/` は開いていません。実測の数値には出どころの記録を添えます。

## 0. 先に結論と読み方

### 0-1 先に結論

1. 既定のランで「考える」を担っているのは mock(決まった乱数で答える代役)です。mock はプロンプトを読まず(腕 `--speech-port on` の発話の欄の指示だけが例外)、語彙の 12 語から一様に 1 語を引きます。LLM は腕で、判断モデルは src にまだありません。
2. 日課表 W17(初期の予定)のうちコードが実行するのは、舞台への出入り・就寝・起床の 4 種と、舞台の外に居る体の食事だけです。勤務の行を実行する処理は無く、日課の中身はプロンプトにも載りません。W17 の行の切れ目は呼び出しのきっかけとして使います。
3. 記憶・関係・発話の言葉は既定で off です。会話のセッションは成立しますが、言葉が無く、誰も覚えません。

### 0-2 既定のランとは

`python -m shibuya.cli` を引数なし・`SHIBUYA_*` の環境変数なしで起動したランを「既定のラン」と呼びます。5,000 体(`--agents`)・1 日(`--ticks 1440`)・seed(乱数の種)1・世界は `data/world/v2` です。開始日は 2026-07-13 の月曜です([calendar.py](../../../src/shibuya/engine/calendar.py) の `DEFAULT_WORLD_START`)。

入口が違うと既定も違います。[cli.py](../../../src/shibuya/cli.py) の CLI の既定は語彙 v3・空腹 energy・呼数の上限なしで、ライブラリの `run_day` の既定は語彙 v1・空腹 v1・呼数の按分です(`cli.arm_baseline`)。世界の資産が無い場所(合成の小さな世界)では、日課の実行部が立たず、移動も旧道で回ります。

読み出した主な既定の値は次のとおりです。`--llm mock`・`--policy mock`・`--vocab-version v3`・`--hunger-model energy`・`--l4-scale 0`・`--space nav1`・`--chooser nearest`・`--memory off`・`--relations off`・`--familiarity off`・`--store-memory off`・`--speech-port off`・`--decision-port legacy`・`--contact off`・`--calendar w17`・`--calendar-2 off`・`--calendar-3 off`・`--duties off`・`--clock global`・`--talk-clock table`・`--proximity distance`(2.0 m)・`--economy-stage2 on`・`SHIBUYA_RULES_42=on`・`--rate-rules off`・`--absent-processes stopped`・`--defect-fixes-1103 on`・`--seat-release walk`・`--events on`。

実測の参考値は次のとおりです。5,000 体・seed 1・mock・1 日で、呼び出し 60,939 回(12.19 回/体/日)・食事 4,164 件・満席で並んだ 166 回です([fix4-1103 §1-1](../../bench/analysis/fix4-1103/README.md))。実行は 60.5 秒と 61.8 秒・1 刻み 42〜43 ms・最大メモリ 520〜527 MB です([版上げの履歴](../../ops/version-history.md))。この記録の後の v3-0a(第344)は 1 バイト不変と記録されています。

### 0-3 4 つの区分

| 区分 | 意味 |
|---|---|
| 既定 | 既定のランで動く |
| 腕 | 既定では動かず、切替口を立てると動く(用語集の候補名は実験条件・実験スイッチ) |
| 器 | 口や欄はあるが、既定のランの結果を変えない(値が空・誰も読まない・呼ばれない) |
| 無い | 世界に無いと宣言している([absent.py](../../../src/shibuya/world/processes/absent.py) の一覧。文は同じファイルに原文があります) |

旧値の再現のためだけに残る切替口は、既定が新しい道なので腕に入れず、§10 に分けました。

### 0-4 語

用語集([v2-glossary.md](../../design/v2-glossary.md))の語で書きます。よく出る語は次のとおりです。

| 語 | 意味 |
|---|---|
| 体 | 住民 1 人 |
| 刻み | 系を 1 周する単位。既定 60 秒。1 日は 1,440 刻み |
| 系 | 刻みの中で順に呼ぶ処理のまとまり。「立つ」はそのランで呼ぶこと |
| セル | 舞台を分けた 100 m 角の区画 |
| 呼び出し(旧: 起床) | 体に判断を求めること。目を覚ます意味の「起きる」とは別 |
| 舞台の外(旧: 域外)・域内に居る(旧: 在圏) | 渋谷の範囲の外か中か |
| 日課の実行部(旧: 計画実行層) | 出入りと就寝と起床を日課表どおりに実行する層 |
| 計画の切れ目(旧: 計画境界) | 日課の行の始まり。呼び出しのきっかけの 1 つ |
| 代打 | 本来は人がする行為をエンジンが代わりにすること |
| POI | 店や施設の点 |

## 1. 1 日の順番

### 1-1 ラン全体

```text
組み立て build(1 回)
  └ 刻みのループ(既定 1,440 回)
      ├ day_head   2 日目以降の頭だけ
      ├ 刻みの中の系 30 個(立つものだけ・下の表の順)
      └ day_close  途中の日の最後だけ
ランの終わり drain → close_final → report
```

正は [table.py](../../../src/shibuya/engine/systems/table.py) の `SYSTEMS`(36 個=組み立て 1・日の頭 1・刻みの中 30・日の終わり 1・ランの終わり 3)と、[conductor.py](../../../src/shibuya/engine/systems/conductor.py) の `conduct` です。進行役は「時刻の窓」で回しますが、既定の窓の幅は 60 秒で刻みと同じです(`--batch-width-s`)。1 日のランでは `day_head` も `day_close` も立ちません([day.py](../../../src/shibuya/engine/systems/day.py))。

### 1-2 刻みの中の 30 系

ファイルは `src/shibuya/engine/systems/` の下です。腕の 5 系(experiment・contact・calendar_3・calendar_2・duties)だけ別の場所です。

| 順 | 系 | 何をする | ファイル | 既定で |
|---:|---|---|---|---|
| 1 | experiment | 申込書の改変を世界へ入れる | [experiment/layer.py](../../../src/shibuya/engine/experiment/layer.py) | 腕 `--experiment` |
| 2 | body | 空腹と疲れを進める。舞台の外の体の食事 | [body.py](../../../src/shibuya/engine/systems/body.py) | 立つ |
| 3 | world | 世界過程 18 本を順に回す(§9) | [world.py](../../../src/shibuya/engine/systems/world.py) | 立つ |
| 4 | presence | 日課の実行部が退出と到着を実行する | body.py | 立つ |
| 5 | perceive_prepare | セルの様子を知覚の欄へ前計算する | [perceive.py](../../../src/shibuya/engine/systems/perceive.py) | 立つ |
| 6 | llm_receive | LLM サーバー群(旧: 艦隊)と再生の到着を受け取る | [llm_io.py](../../../src/shibuya/engine/systems/llm_io.py) | 立つ(mock では何もしない) |
| 7 | apply_responses | 前の刻みの答えを意図に直す。会話の返事を解決する | [judge.py](../../../src/shibuya/engine/systems/judge.py) | 立つ |
| 8 | detect | 体の段とセルの様子の変化を見つける | perceive.py | 立つ |
| 9 | plan_boundary | 就寝と起床を実行し、計画の切れ目の呼び出し候補を作る | body.py | 立つ |
| 10 | home_meal | 域内の家の食事 | body.py | 腕 `--home-meal plan` |
| 11 | wake_sources | 会話の番と顕著行為の候補を作る | judge.py | 立つ |
| 12 | wake_filter | 答えが返らなかった呼び出しを候補へ戻す | judge.py | 立つ |
| 13 | relations_wake | 知人が近くに現れた候補を作る | [talk.py](../../../src/shibuya/engine/systems/talk.py) | 腕 `--relations on` |
| 14 | wake_assemble | 候補を 1 つの表にまとめる | judge.py | 立つ |
| 15 | arbiter | 呼び出しの割り当て(旧: 繰り延べアービタ) | judge.py | 立つ |
| 16 | decide | 選ばれた体の知覚を描いて答えを得る | [decide.py](../../../src/shibuya/engine/systems/decide.py) | 立つ |
| 17 | phase_a | 意図を集める(答え・歩き続ける体・着いた体) | [act.py](../../../src/shibuya/engine/systems/act.py) | 立つ |
| 18 | phase_b | 席や棚の取り合いを決着させる | act.py | 立つ |
| 19 | phase_c | 確定した意図を世界へ書く(移動・購入・食事ほか) | act.py | 立つ |
| 20 | conversation | 招待・セッションの進行・終わり | talk.py | 立つ |
| 21 | activity_intent | 活動の期限と意図を確定する | body.py | 立つ |
| 22 | contact | メッセージと電話 | [contact/layer.py](../../../src/shibuya/engine/contact/layer.py) | 腕 `--contact c1` |
| 23 | calendar_3 | 雇い主のシフトと祝日 | [calendar3/layer.py](../../../src/shibuya/engine/calendar3/layer.py) | 腕 `--calendar-3 arm` |
| 24 | calendar_2 | 会話から生まれる約束 | [calendar2/layer.py](../../../src/shibuya/engine/calendar2/layer.py) | 腕 `--calendar-2 arm` |
| 25 | duties | 店の仕事を働く人の判断へ | [duties/layer.py](../../../src/shibuya/engine/duties/layer.py) | 腕 `--duties arm` |
| 26 | memory | 記憶を書く | [remember.py](../../../src/shibuya/engine/systems/remember.py) | 立つが何もしない(`--memory off`) |
| 27 | familiarity | 親しみの表を書く | remember.py | 腕 `--familiarity on` |
| 28 | energy_after | 空腹の計器を進める | body.py | 立つ |
| 29 | observe | 診断の行と計器 | [observe.py](../../../src/shibuya/engine/systems/observe.py) | 立つ |
| 30 | checkpoint | 360 刻みごとに状態のハッシュを取る | observe.py | 立つ |

既定のランで立つのは 22 系で、腕の 8 系は立ちません。立つ条件は `conductor.WHEN` です。

答えが世界に入るまでの順は次のとおりです。刻み T の `decide` で答えが出ると、T+1 の `apply_responses` で意図になり、同じ T+1 の `phase_c` で世界へ書かれます。考える時間は思考時間の段 L1 の 2.6 秒で、60 秒の刻みへ切り上げて 1 刻みです([llm_bridge.py](../../../src/shibuya/engine/llm_bridge.py))。

## 2. ランの前の準備

`cli.run` が世界と金と物の台帳を用意し、`run_day` から [build.py](../../../src/shibuya/engine/systems/build.py) が層を組み立てます。

- 母集団 345,858 体([版上げ 3 回目](../../ops/version-history.md))から `--agents` 体を二層抽出します([population.py](../../../src/shibuya/agents/population.py))。
- 日課表 W17 を読み([weekly.py](../../../src/shibuya/agents/weekly.py))、0 時の活動を立てます。LLM で作って凍結した資産で、ランのたびには作りません。
- 財布は対数正規で引き([anchors.py](../../../src/shibuya/economy/anchors.py))、来街者でない体には 30 日分の預金を入れ([stage2.py](../../../src/shibuya/economy/stage2.py))、店には経済センサスで按分した参入資本を入れます([entry_capital.py](../../../src/shibuya/economy/entry_capital.py))。
- 0 時に域内に居ない体を舞台の外へ置きます(`PlanExecutor.initialize`)。

## 3. 朝に人が圏に入る

系 `world` の中で鉄道が時刻表どおりに便を進め、次の系 `presence` で日課の実行部がその刻みの到着を実行します。舞台の外の体は駅の出口のセルへ現れます。出口の 25 セルへ通し番号で順に割り振るので、乗った線とは結び付きません。日課表の域内の行の連なりを在圏ブロックと呼び、到着の時刻はこの単位で決めます。鉄道の体は「ブロックの開始に間に合う最も遅い便」がホームへ入る刻み、徒歩や道路の体はブロックの開始の刻みです。ホームから出口までの所要時間は無く、運賃も動きません(日課由来の移動は所持金を動かさない=`resolve._board_riders` の注)。

動くファイル: [presence.py](../../../src/shibuya/engine/presence.py)・[weekly.py](../../../src/shibuya/agents/weekly.py)・[rail.py](../../../src/shibuya/engine/processes/rail.py)・[resolve.py](../../../src/shibuya/engine/resolve.py) の `rail_arrive`。

| 区分 | 中身 |
|---|---|
| 既定 | 日課の実行部(日課の読み取り規則 v2)・鉄道の発着。全員が間に合う最も遅い便に乗る。混雑は 200% の上限だけで、それまでは全員乗る |
| 腕 | `--derive-rule v2.1`(行の読み方)・`--calendar 1b`(勤務の出入りを本人の判断へ)・`--calendar-shadow 1a`(計器だけ) |
| 器 | [rail_events.py](../../../src/shibuya/engine/processes/rail_events.py)(渋谷の発着の表を読む口。呼ばれない) |
| 無い | 電車を見送る・催しの人の注入。来るかどうかの判断も無く全員出勤です([rate_rules.py](../../../src/shibuya/engine/rate_rules.py) の宣言) |

既知の穴は presence.py の冒頭に書かれています。到着の約 6/25 は表参道と明治神宮前の出口のセルに出ます。徒歩と道路の体も門でなく駅の出口に現れます。退出と到着が同じ刻みに重なる体は瞬間移動します。

## 4. 起きて考える

### 4-1 起きる

目を覚ますのは日課の時刻どおりです。系 `plan_boundary` が、就寝でない行の始まりごとに、寝ている体を起こします(`resolve.wake_from_plan`)。呼び出しが見送られても起きます。起こすきっかけとして眠気や明るさを見る処理はありません。

### 4-2 呼び出しの候補

候補の源は 6 つです。計画の切れ目・体の段やセルの様子の変化([change_detect.py](../../../src/shibuya/engine/change_detect.py))・会話の番・顕著行為(倒れるなどの目につく出来事)・答えが返らなかった呼び出し・活動の満了です。変化は、空腹と疲れと暑さの段を跨いだときと、セルの様子(密度の段・騒音の段・流れ・目につく出来事)が変わったときです。活動中の体と意図を持って歩いている体は、場所の変化では呼びません。

### 4-3 割り当て

[arbiter.py](../../../src/shibuya/engine/arbiter.py) が候補を絞ります。寝ている体は見送り(旧: 抑止)です。例外は計画の切れ目・顕著行為・会話の番です。舞台の外と乗車中の体は例外なく見送ります。再呼び出しの間隔(旧: 不応期)は表で決まっていて、値は会話の番 0 分・睡眠中の切れ目 360 分・勤務中の切れ目 150 分・一般の切れ目 60 分・移動中の切れ目 15 分・体の変化 45 分・セルの変化 30 分です(`agents/state.py` の `REFRACTORY_MINUTES`)。CLI の既定は呼数の上限なし(`--l4-scale 0`)で、1 刻みの枠は体の数です。10 呼/体/日は監査の線で、超えても絞りません(`cli.py`)。

### 4-4 考える担い手

| 担い手 | 立て方 | 状態 | 中身 |
|---|---|---|---|
| mock | `--policy mock`・`--llm mock` | 既定 | [mock.py](../../../src/shibuya/llm/mock.py)。プロンプトを読まず、語彙 12 語から一様に行為を引く。理由・活動・期限も一様。対象は「なし」(移動の 1/3 は「あたり」)。同じファイルに「書式と決定論を通す配管で、振る舞いのモデルではない」と宣言がある |
| コード(System 1) | 常に | 既定 | 出入り・就寝・起床・歩き続ける・着いた体の意図の実行・変化の検出。呼数 0 |
| 古典モデル | `--policy classical` | 腕 | [classical.py](../../../src/shibuya/engine/classical.py)。LLM 0 呼。食事の門と社会生活基本調査の事前分布 |
| LLM | `--llm fleet --endpoints …` | 腕 | [fleet.py](../../../src/shibuya/llm/fleet.py)。非同期の実 vLLM(推論サーバー)。温度 0.7・最大 96 トークン。既定は待たない(`--fleet-wait-s 0`。本番の運用値は 120) |
| 再生 | `--replay` | 腕 | 応答の記録(旧: テープ)から完全一致で引く |
| 判断モデル | なし | 未実装 | 判断の口の実装は llm・mock・classical の 3 つだけ([ports.py](../../../src/shibuya/engine/decision/ports.py))。評価の道具 `tools/instruments/dm_eval/` は src の外 |

計器の `layer_counts` は mock の呼び出しも層 2(LLM)に数えます(`build.py` の `_call_layer`)。計器の「LLM の呼数」を読むときは mock を含むと読んでください。

### 4-5 プロンプト

呼ばれた体ごとに [renderer.py](../../../src/shibuya/perception/renderer.py) が毎回プロンプトを描きます。mock は読みませんが描画は走ります。中身は、役割と規則と語彙(B0)・種別(B1)・場所と見えるものと看板(B2)・時刻と天候(B3)・密度と騒音と出来事(B4)・25 m 以内の様子(B4b)・内受容と所持金と近くの人(B5)・呼び出しの理由と直前の結果(B6)です。

載らないものは、人物像(年代・性別・職業)・日課表の中身・記憶です。[templates.py](../../../src/shibuya/perception/templates.py) と renderer.py に日課の行を描く文が無いことを grep で確かめました。

答えの形は語彙 v3 の 5 欄(理由・行動・対象・活動・まで)です。[parser.py](../../../src/shibuya/llm/parser.py) が読み、語彙の外の語は同義語辞書で語彙へ写し、写せなければ「なし」にします([undefined.py](../../../src/shibuya/llm/undefined.py))。語彙は移動・乗車・購入・食事・会話・退去・通報・手伝い・断る・就寝・並ぶ・なしの 12 語です([contract.py](../../../src/shibuya/llm/contract.py))。役割語 11 語も B0 に見せますが、既定では効果の先が無く「なし」として扱います。

| 区分 | 中身 |
|---|---|
| 既定 | 上の mock とコード・描画・変化の検出・割り当て・語彙 v3 |
| 腕 | 上の古典・LLM・再生・`--decision-port port`(判断の候補の口。LLM サーバー群の道は通らず数えるだけ) |
| 器 | [persona.py](../../../src/shibuya/engine/decision/persona.py)(人物の文。判断の入力に入れない)・判断の口の驚きと迷いと連続値の欄(どの実装も空)・起床の条件の表にある近接の入れ替わり・見られている・傍受の 3 行(検出しない) |
| 無い | よく考える(全部の呼び出しが同じ段 L1 で、CLI に切替口なし)・予定を考え直す・予想と違って直す |

## 5. 歩く

答えが「移動」なら行き先を決めます。対象が「なし」のときは職場か自宅のうち今いない方で([commit.py](../../../src/shibuya/engine/commit.py))、「あたり」のときは同じ層で格子 2 つ以内のセルです([activity.py](../../../src/shibuya/engine/activity.py))。行き先が決まれば、着くまで呼び出しなしで毎刻み進みます。店や人や寝床が別のセルにあるときは、行為を意図として持って歩き、着いたら呼ばずに実行します([intent.py](../../../src/shibuya/engine/intent.py)・上限 60 刻み)。

歩き方は歩ける面(ナビメッシュ)の上の移動です([nav1.py](../../../src/shibuya/engine/space/nav1.py))。経路は通りの選び(曲がる 1 回=50 m・上り 1 m=3.8 m の重み)と面の上の線で作ります。速さは本人の歩く速さ(毎秒 1.00〜1.60 m の一様)に坂の係数と混み具合の係数を掛けます。階段・エスカレーター・エレベーターは所要時間と容量があり、容量を超えると前で待ちます。人どうしは衝突しません(同じファイルに、つなぎと宣言があります)。

動くファイル: [act.py](../../../src/shibuya/engine/systems/act.py)・commit.py・resolve.py・nav1.py・[navmesh.py](../../../src/shibuya/world/navmesh.py)・[navmesh_route.py](../../../src/shibuya/world/navmesh_route.py)・[geometry.py](../../../src/shibuya/engine/geometry.py)・intent.py・activity.py。

| 区分 | 中身 |
|---|---|
| 既定 | 歩ける面の上の移動(`--space` の既定 nav1。本番の世界で資産が無いと止まり、合成の世界では旧道)・活動層・意図の保持・坂は Wood 2023・曲がる重みは 50 m 固定・密度は近傍 1 段の推定 |
| 腕 | `--slope tobler`・`--turn-weight person`・`SHIBUYA_NAV1_DENSITY`(cell か unscaled) |
| 器 | [system1.py](../../../src/shibuya/engine/body/system1.py) の混雑の中の歩き方と避け方(値は空) |
| 無い | absent.py に行はありません。経路の選びは本人の判断でなく既定の重みで、衝突と回避は nav1.py につなぎと宣言があります |

## 6. 店で買う・食べる

答えが「購入」「食事」「並ぶ」なら、今のセルの営業中で意図に合う店を候補にし、最寄りを選びます([poi_target.py](../../../src/shibuya/engine/poi_target.py)・[chooser.py](../../../src/shibuya/engine/chooser.py))。mock は対象が「なし」なので、今のセルに候補が無ければ失敗します。

購入は、営業中・在庫あり・支払えるを確かめ、席があれば成立します。1 回 1 個で、棚が減り、所持が増えます。満席なら列に並び、席が空くと並んだ順に入り、15 刻みで離れます。在席は最大 30 刻みです([crowd.py](../../../src/shibuya/engine/processes/crowd.py))。食事は飲食店だけで成立し、棚も所持も動きません。金は購入と同じ道で動き、空腹が戻ります。

支払いは財布が足りれば現金、足りなければ口座です。レジの消費税は 10% で店の預かり金に積みます。財布が 1 日の消費を下回った体が営業中の ATM のセルで判断すると、千円単位で下ろします。どれも規則で、[stage2.py](../../../src/shibuya/economy/stage2.py) に未リサーチ(expedient)と宣言があります。給料日は毎月 25 日(土休は前の営業日)の日の締めで、職業ごとの実データの賃金と天引きが動きます。既定の 1 日のラン(7 月 13 日)には来ません。

空腹はエネルギー収支です([energy.py](../../../src/shibuya/engine/energy.py))。語は満腹・ふつう・空腹・とても空腹の 4 段です。舞台の外に居る体は日課の食事の行(無ければ分布から引いた時刻)で自動に食べ、金と物は動きません。

店の側はコードが動かします。開閉は営業時間の表 W7 を 5 分ごとに見て、担当が店に居ればその人の役割行動として記録し、居なければ代打です([opening.py](../../../src/shibuya/engine/processes/opening.py))。補充は棚が容量の 95% を割ったら 5 分ごとに、担当が居る店で行い、10 時に残りの店を代打します。納品は 5〜8 時に外から入ります([goods_flow.py](../../../src/shibuya/engine/processes/goods_flow.py))。

動くファイル: 上のほか、resolve.py の `_apply_buy`・`_apply_eat`・`_apply_queue`・`_serve_poi_queue`、[ledger.py](../../../src/shibuya/economy/ledger.py)・[goods.py](../../../src/shibuya/economy/goods.py)・[taxes.py](../../../src/shibuya/economy/taxes.py)・[economy_stage2.py](../../../src/shibuya/engine/economy_stage2.py)・[economy_rules.py](../../../src/shibuya/engine/economy_rules.py)・[rules/table.py](../../../src/shibuya/engine/rules/table.py)・[rights/ledger.py](../../../src/shibuya/engine/rights/ledger.py)。

| 区分 | 中身 |
|---|---|
| 既定 | 店選びは最寄り(`--chooser nearest`・憲法⑥の宣言つき暫定)・購入と食事と列・金と物の台帳・経済の段階 2 の 5 部品(賃金・引き出し・支払いの方法・レジの税・来街者の口座)・規則の表の天引きと預かり消費税・開閉と補充の代打・納品 |
| 腕 | `--duties arm`(開閉と補充と廃棄を担当の判断へ)・`--chooser classical`・`--home-meal plan`・`--meal-sleep-defer on`・`--eatery place_food`・`--store-memory on` |
| 器 | [credit.py](../../../src/shibuya/economy/credit.py)(信用。呼び手なし)・[pricing.py](../../../src/shibuya/economy/pricing.py)(価格形成。結線しない) |
| 無い | 品と数を選ぶ・値段を見て見送る・家で食べる・値段を変える・接客・売れ残りの廃棄・ポイ捨て・ごみ収集・宅配・採用と解雇。納品は無いでなく入力、発注は無いでなく初期の予定(固定の注文)と宣言しています |

## 7. 話す

答えが「会話」なら相手を決めます。名指しがあればその人、無ければ同じ刻みに呼ばれて届く体です。届くとは、同じ層で 2.0 m 以内か、同じ店の中です([proximity.py](../../../src/shibuya/engine/proximity.py))。話しかけた体は返事を待ち、相手は次の刻みに招待を受けて呼ばれます。相手の答えが「会話」(名指しなしか招待者宛て)なら成立し、ほかの答えは断りです(`run._settle_pending_invites`)。返事の期限は 3 刻みです。

成立すると話者が交替で呼ばれます。1 呼び出しが 1 発話ブロックで、1 体 3 回まで、2 人までです。終わりを決めるのはエンジンです。話題が尽きる・沈黙 5 刻み・退去・3 m より離れる・寿命 60 刻みで閉じます([conversation.py](../../../src/shibuya/engine/conversation.py))。

既定のランに言葉はありません。語彙 v3 に「ひと言」の欄が無く、発話の口も off なので、残るのはセッションと回数だけです。記憶も関係も off なので、終わった後に誰も覚えていません。

実績は、招待 2,218 回のうち成立 155・断り 2,029・期限切れ 1・届かず不成立 32・帳尻の既知の穴 1 です([fix4-1103 §1-1](../../bench/analysis/fix4-1103/README.md))。mock は 12 語から一様に引くので、承諾は計算で約 1/12 になります。

動くファイル: [talk.py](../../../src/shibuya/engine/systems/talk.py)・judge.py・[run.py](../../../src/shibuya/engine/run.py)・conversation.py・proximity.py・[spatial_index.py](../../../src/shibuya/engine/spatial_index.py)・llm_io.py の `utter`。

| 区分 | 中身 |
|---|---|
| 既定 | 招待とセッション・実距離の判定(`--proximity` の既定 distance) |
| 腕 | `--speech-port on`(ひと言)・`--memory on`・`--memory-store events`・`--memory-model m1`・`--memory-cue embed`・`--memory-people memory`・`--memory-grain day`・`--relations on`・`--rel-copresent on`・`--conv-max-participants 3`・`--familiarity on`・`--talk-clock mora`(計器だけ)・`--contact c1`・`--calendar-2 arm`・`--calendar-3 arm` |
| 器 | system1.py のロンバード効果(値は空)・[道具の台帳](../../../src/shibuya/engine/tools/registry.py)(既定は誰も読まない)・[記憶の印象](../../../src/shibuya/engine/memory_impression.py)と[浅い痕跡](../../../src/shibuya/engine/memory_trace.py)(結線しない)・応答率 0.8 の抽選と重要度上位の +2 呼(死んだ道=11-05/§3-2 で消す) |
| 無い | ひと言・3 人目として加わる・手伝いと断るの効果(手伝いはいつも失敗し、断るは記録だけ) |

## 8. 帰って寝る

域内に居る体は、在圏ブロックが終わる刻みに、今いるセルから舞台の外へ出ます。駅へは歩かず、運賃も動きません。会話中なら最大 30 刻み待ち、買い物と列は中断します(`PlanExecutor._do_depart`)。

寝るのは日課の就寝の行の時刻で、コードが実行します(`resolve.begin_planned_sleep`)。このとき呼び出しはありません。就寝地のセルに居ればすぐ寝て、居なければ歩いて着いたら寝ます。乗車中・舞台の外・会話中の体には何もしません。寝ている間は疲れが戻り、空腹は進みます。

判断の答えからも動きます。「就寝」は自宅のセルなら寝て、別のセルなら意図を持って歩きます。「乗車」はホームまで歩いて便を待ち、運賃 180 円(`rail.FARE_YEN`・運賃表は未取得)を払います。乗車で出た体は次のブロックの到着で戻ります。次のブロックが無ければ、60 分以後の便が進行中のブロックの終わりより前にあるときだけ出口のセルへ戻ります(`_rearm_after_leaving`・E12)。「退去」は店や会話から抜けるだけで、舞台の外へは出ません。

舞台の外の体は呼ばれません(`--no-outside-suppression` を立てない限り)。行為はなく、空腹と疲れが進み、食事は §6 のとおり自動です。

動くファイル: presence.py・body.py・resolve.py・rail.py・[body/model.py](../../../src/shibuya/engine/body/model.py)・[body/rules.py](../../../src/shibuya/engine/body/rules.py)。

| 区分 | 中身 |
|---|---|
| 既定 | 就寝は日課の実行・即時の退出(`--exit-mode immediate`)・寝ている間の見送り |
| 腕 | `--exit-mode walk_to_platform`(路線のホームへ歩いて乗る)・`--calendar 1b` |
| 器 | system1.py の大きな音に注意が向く(値は空) |
| 無い | 1 日の振り返り(就寝で数えるだけで呼ばない)・倒れる |

既知の穴は presence.py の冒頭に書かれています。日の境目で計画と在圏がずれる体がいます(day0 の表から数えた静的な数で、ランでは未計測)。

## 9. 世界過程 18 本の既定

系 `world` の中で次の順に回ります([runner.py](../../../src/shibuya/engine/processes/runner.py) の `PROCESS_ORDER`)。名前は 18 本ありますが、5 本は既定で中身が止まっています。

| 順 | 過程 | 既定の中身 | 状態 |
|---:|---|---|---|
| 1 | environment | 5 分ごとに日照・天候・体感温度(実日の気象の再生) | 既定 |
| 2 | rail | 便の発着・乗車の客を運ぶ | 既定 |
| 3 | opening | 5 分ごとの開閉 | 既定(担当か代打) |
| 4 | crowd | 混雑の段・流れ・席・列 | 既定 |
| 5 | traffic | 断面の車の台数の集計。知覚の騒音は別の静的な昼夜の場(W10)で、台数は書き込まない | 既定(集計だけ) |
| 6 | delivery_inbound | 5〜8 時の納品の枠 | 既定(入力の宣言) |
| 7 | shelf | 棚の補充と代金 | 既定(担当か代打) |
| 8 | waste | 19 時に持ち物のある体が 1 個消費するだけ | 既定(一部) |
| 9 | street_cleaning | 止めた | 無い |
| 10 | last_mile | 止めた(宅配) | 無い |
| 11 | bus_taxi | 6〜23 時・10 分間隔の運行の記録。乗り降りは無い | 既定(記録だけ) |
| 12 | road_works | 止めた | 無い |
| 13 | hotel | 21 時チェックイン・9 時アウト・1 POI 120 室 | 既定 |
| 14 | infra | 止めた(電気と水) | 無い |
| 15 | press | 7・12・18 時に、在席者のいるセルへ 1 行「鉄道各線は平常どおり運行しています」(`_broadcast_events`) | 既定 |
| 16 | large_event | 18 時と 21 時に開催を記録するだけ。人は増えない | 既定(記録だけ) |
| 17 | dispatch | 止めた(救急と警察) | 無い |
| 18 | salient | 報道の行を知覚へ渡す。倒れる人と出動が無いので顕著行為の抽選は起きない | 既定 |

## 10. 日の終わりと一覧

### 10-1 日の終わり

1 日のランでは `drain`(LLM の残りを受け取る)→ `close_final`(鉄道の最後の便・金と物の台帳の締め・センサス)→ `report`(結果と manifest=ランの同定情報)と進みます([run_end.py](../../../src/shibuya/engine/systems/run_end.py)・[report.py](../../../src/shibuya/engine/systems/report.py))。`--sim-days 2` 以上では日の間に `day_close` と `day_head` が入り、表だけ張り直して体の状態は持ち越します([state_io.py](../../../src/shibuya/engine/systems/state_io.py))。

既定のランがファイルに書くものはありません。出来事の記録は既定 on ですがメモリの中に 7 日分を持つだけで([log.py](../../../src/shibuya/engine/events/log.py))、応答の記録(`--tape`)・状態(`--state-out`)・センサス(`--census-out`)・在圏の記録(`--occupancy-every`)は頼んだときだけです。

### 10-2 区分の数

この文書の数え方です。腕は 1 日の流れに関わる機能の腕を数え、感度の値だけを振る引数(`--refractory-scale`・`--signage-p-see` ほか)と帰無の腕(`--no-plan-executor` ほか)と腕の中の下の腕は数えません。リポ全部の棚卸しは機能のカタログ(段 2)と[技術マップ](../tech-map-2026-11-03.md)の担当です。

| 区分 | 数 | 中身 |
|---|---:|---|
| 既定 | 38 | 進行と記録 5(進行役と窓・組み立て・出来事の記録・群と規範の計器・診断と checkpoint と manifest とセンサス)/世界過程 13(§9 の既定)/体 3(日課の実行部・空腹と疲れと体感温度・舞台の外の食事)/知覚と判断 7(描画・変化の検出・割り当て・mock・語彙と読み取りと同義語辞書・活動層・意図の保持)/行為 6(取り合いの決着と書き込み・歩行・店選び・購入と食事と列・近接の判定・会話のセッション)/経済と制度 4(台帳・経済の段階 2・規則の表と天引き・権利台帳) |
| 腕 | 38 | 考える 4(`--policy classical`・`--llm fleet`・`--replay`・`--decision-port port`)/話すと覚える 12(§7 の `--speech-port` から `--familiarity` までの 11 本と §6 の `--store-memory on`)/予定と連絡と仕事 6(`--calendar 1b`・`--calendar-shadow 1a`・`--calendar-2 arm`・`--calendar-3 arm`・`--contact c1`・`--duties arm`)/店と食事 4(`--chooser classical`・`--home-meal plan`・`--meal-sleep-defer on`・`--eatery place_food`)/歩くと出入り 5(`--exit-mode walk_to_platform`・`--derive-rule v2.1`・`--slope tobler`・`--turn-weight person`・`SHIBUYA_NAV1_DENSITY`)/時計 5(`--talk-clock mora`・`--step-scope changed`・`--clock regional`・`--body-schedule reserve`・`--batch-width-s`)/実験 2(`--experiment`・`--weather-perturb`) |
| 器 | 14 | system1.py の 3 件・道具の台帳・persona.py・credit.py・pricing.py・memory_impression.py・memory_trace.py・rail_events.py・応答率 0.8 の抽選・重要度上位の +2 呼・判断の口の驚きと迷いの欄・起床の条件の 3 行 |
| 無い | 24 | 主体が居ない 8(ごみ収集・街路の清掃・宅配・道路工事・救急と警察の出動・催しの人の注入・採用と解雇・電気と水の負荷)/口が無い 13(電車を見送る・品と数を選ぶ・値段を見て見送る・3 人目として加わる・予定を考え直す・家で食べる・よく考える・ひと言・1 日の振り返り・予想と違って直す・接客・値段を変える・倒れる)/率を外した 2(ポイ捨て・売れ残りの廃棄)/効果の先が無い 1(手伝いと断るの効果)。このほか absent.py には納品(入力)と発注(初期の予定)の 2 件の言い換えがあります |

旧道の切替口は 10 本あります。`--rate-rules legacy`・`--absent-processes legacy`・`--defect-fixes-1103 legacy`・`--seat-release legacy`・`--proximity cell`・`--economy-stage2 off`・`SHIBUYA_RULES_42=off`・`SHIBUYA_RULES_42B=off`・`--space legacy`・`--hunger-model v1` です。11-05/§3-2 で消す予定で、既定のランでは通りません(通らないことの確認は §3-2 の作業で行います)。

## 11. 文書とコードが違う所

正はコードです。古い文書を直すかは整理の段(11-05/§3-2)の判断で、ここでは書き直していません。

| # | 文書の記述 | コード | 場所 |
|---:|---|---|---|
| 1 | 刻みの順は「1 応答の適用 → 2 世界過程と日課の実行部 → 3 前計算と変化検出」 | 体 → 世界過程 → 出入り → 知覚の前計算 → 到着の受け取り → 応答の適用 → 変化検出。応答の適用は先頭でない | [概要の詳細版](../../design/v2-architecture-overview-detailed.md) §4 の図・[run.py](../../../src/shibuya/engine/run.py) の docstring の骨格 |
| 2 | 個体の状態「既定 345,858 体」 | `--agents` の既定は 5,000。345,858 は母集団の総数 | 概要の詳細版 §1 の図 |
| 3 | 「各体は W17 の予定表どおりに動き」 | 実行するのは出入り・就寝・起床(`WORK_START` と `AT_HOME` は積まない)と舞台の外の食事 | 概要の詳細版 §7 |
| 4 | 個体の欄に `plan_activity` | 第330 の K15 で欄を消した(`agents/state.py` の注) | 概要の詳細版 §7 |
| 5 | 呼数 7.38〜7.44 回/体/日(5,000 体) | 今の既定の記録は 60,939 回=12.19 回/体/日 | 概要の詳細版 §9・fix4-1103 |
| 6 | 世界過程 18 本が動く形の説明 | 5 本は既定で止めた。催しは記録だけ。概要は 10-25 が最終更新でその後の決定が入っていない | 概要の詳細版 §4 |
| 7 | 「平均 10 呼/体/日がアービタの制御目標」 | CLI の既定は上限なしで監査の線 | arbiter.py の docstring |
| 8 | 刻みの中 25 系 | 今は 30 系 | table.py の docstring とコメント |
| 9 | 応答の遅れ 2 は旧いテープの再生のために残す | `RESPONSE_DELAYS=(1,)`。切替口は消した | run.py の docstring |
| 10 | 経済の段階 2 は既定 off・`--wage w17` が切替口 | 既定 on(`economy_stage2.DEFAULT_ARM`)。切替口は消した。既定 off の不一致は技術マップにも記載あり | stage2.py の docstring |
| 11 | 補充点=棚容量の 80% | `REORDER_FILL_RATIO = 0.95` | goods_flow.py の docstring |
| 12 | 過程数(5)ぶんのループ | 18 本 | runner.py の `step` のコメント |
| 13 | `--exit-mode` は「immediate のみ実装」 | `walk_to_platform` も実装済み(`shibuya.cli` の help は正しい) | run.py の `main` の help |
| 14 | 「既定は起床のたびに全部 L2」 | 語の衝突。ここの L2 は判断の行き先の LLM の層で、コードの思考時間の段の既定は L1 | absent.py の `absent.deliberate`・llm_bridge.py の `DEFAULT_LANE` |
| 15 | 11-05/9-3d・9-5 で「考え中も歩く速さは落ちない」「再開の費用は無い」を無いの一覧へ足す決定 | absent.py にまだ行が無い(決定が新しく未着手) | absent.py |
| 16 | 発注の手がかりの `engine/conductor.py` | 実体は `engine/systems/conductor.py` | 発注文 |
| 17 | 技術マップの行数(build.py 1,688・run.py 2,662・cli.py 1,860) | HEAD `33193c3` の値。今は 1,701・2,691・1,876 | [技術マップ](../tech-map-2026-11-03.md) §1 |

## 12. 未確認のまま残した所

- 今の既定の構成を実 LLM で 1 日回した記録を確認できませんでした。[PENDING](../../../PENDING.md) §0 は実 LLM を 5070 で再開の準備中と書いています。39 万体 × 1 日の受入(タグ `v2-c7-day-4-accepted`)は古いコードの記録です。
- `data/` を開いていないので、母集団 345,858 体は版上げの履歴の値、出口 25 セルと日の境目の体の数は presence.py の docstring の値のままです。
- presence.py の既知の穴の、今の既定での件数は未計測です(docstring に旧既定の値だけがあります)。
- 今の既定の呼び出しの理由ごとの内訳は確かめていません。
- 腕・器・旧道の切替口の一覧は 1 日の流れに関わるものを読んで作りました。リポ全部の網羅は未確認で、機能のカタログ(段 2)と突き合わせます。10-25 §2-5 の切替口の一覧とは突き合わせていません。

カードは [cards/README.md](cards/README.md) です(段 3・本体への取り込み待ち)。ファイルごとの公開の関数・呼び手・書きの許可はカードで引けます。
