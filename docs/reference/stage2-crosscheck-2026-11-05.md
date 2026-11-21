# 段 2 の突き合わせの結果(2026-11-05・claude.ai の側の読み手 4 本・Opus 5.5)

> 返事その 6 §3-1 の 5 の「読み手の突き合わせ」。HEAD e863c8b(src は 15b6bbd と同じ)のコードを、実装役の資料と照らした。読み手はどれもランと試験の全体を回していない(data/ がこの機械に無い・依存の一部が無いので import の代役を置いて既定値だけを読んだ)。開かない約束の文書(IMPLEMENTED.md・build-report-C7/C8・門 1 の計画・パターン台帳・封印の層)は開いていない。**直すのは実装役。片方を選べない所は第 N で聞くこと。**

## 0. まとめ

| 資料 | 確かめた主張 | 食い違い | 大 | 書き漏れ |
|---|---:|---:|---:|---|
| catalog/a-body-and-town.md | 約 230 | 10(中 3・小 7) | 0 | 5(重いのは開始日の検査) |
| catalog/b-people.md | 201 | 10(中 3・小 4・確かめられない 3) | 0 | 7 |
| catalog/c-foundation.md | 234 | 11(違う 1・一部違う 7・確かめられない 3。中 4・小 7) | 0 | byte-check の置き場・CI の範囲・golden |
| day-flow.md・can-say.md | 約 220 | 15(一部違う 11・確かめられない 4。全部 小) | 0 | §11 の漏れ 3 |

- 合計で約 885 の主張を確かめ、食い違いは 46 件。**大(既定 on を off と書く・無いものを有ると書く)は 0**。資料の芯は信用してよい。
- **「既定で考えるのは mock・判断モデルは src に無い」は 4 本とも正しいと確かめた。** ただし言い方を直す:判断モデルの**中身**は無い。腕(c1・カレンダー 2 と 3・店の仕事)には判断モデルを**呼ぶ口**があり、仮のモデル(mock)が答える。数え口 `judge_model` はその呼数(既定のランでは 0)。catalog b §13 の「判断モデル 240,128」は判断モデルが動いた数ではない。
- **連絡・店の仕事・カレンダーの判断と文の口は `--llm fleet` でも仮のモデルに固定**(contact/layer.py:265-266 ほか)。実の LLM で回すときに、腕の判断は艦隊へ行かない。資料に書くこと。

## 1. 先に直してほしい中の食い違い(設計の判断に効くもの)

1. **既定の店選びで距離が効かない**(b §2・poi_target.py:462・512):候補は今のセルの店だけで距離が全部同じ。既定の「最寄り」は実際には可視の降順 → 番号。
2. **空腹の比 0.03 は飲料だけ**(b §3・energy.py:279-285・608-611):軽食は性と年齢ごとの `snack_share_of`。飲料の店は本番の世界に 0 件。
3. **開始日の検査が書かれていない**(a の書き漏れ・calendar.py:424・446・build.py:893):0 日目は祝日でない月曜だけ、2 日以上は連続する平日だけ。`--start-date`・`--sim-days` の使える範囲はこれで決まる。**今の作りでは土日と祝日を回せない**ことを、言えないことの表(can-say)にも足す。
4. **祝日 CSV が無いとき**(a §16):読み込みは警告だけだが、開始日の検査がランを止める。docstring の「既定のランを壊さない」も直す。
5. **`system1.noise_stage_at` の読み手**(a §9):連絡の腕 c1(contact/layer.py:955)が呼ぶ。「読み手なし」「差なし」を直す。
6. **`--geometry edge` と nav1**(a §0-3・§3):build.py:701 で nav1 でも語彙 v2 と組むと注意の層が立つ。「効かない」を直す(結果が変わるかは未確認)。
7. **既知の穴 S12**(c C1):`GoodsLedger.sell_many` は全スロットをまたいで払い出す(economy/goods.py:614-659)。resolve.py:2500-2504 の古い注を写したと見られる。ランで確かめてから消す。
8. **dm_eval の当て口**(c C3):HF と vLLM の logprob の当て口も実装済み(backends/hf.py:58・vllm.py:91・base.py:264)。
9. **録画と再生**(c C6):ValueError で止めるのは再生だけ(systems/build.py:309-310)。
10. **pricing.py は器ではない**(day-flow §6・§10-2・can-say #30):係数 K は原価=価格÷k と参入資本の原価率に効く(goods.py:180-184・433-435・entry_capital.py:173)。

## 2. CI と決定論について(書き漏れ・中)

- byte-check は tools/ にも CI にも無く、docs/bench/analysis の各記録の下に置かれている。
- data が要る試験・golden・性能の門・byte-check は CI の外で、作者の機械で回している。golden は登録した 1 つの環境とだけ比べる(tests/golden_env.py)。
- **資料に「CI が緑でも決定論は確かめていない」と書くこと。** byte-check を道具として tools/ に置き、版上げの手順から呼ぶ形にするかは返事その 7 で答える。

## 3. 系統的な傾向(直すときの見方)

- 古い docstring を写した所が、docstring ごと古い。docstring の直しも同じ commit で。
- モジュールの外で決まる条件(他の腕との組み合わせ・組み立ての後段の検査)が抜けやすい。
- 「器だけ」「効かない」「読み手なし」と書いた所に食い違いが集まった。こう書く前に呼び手を grep で確かめる手順を、カードの道具(呼び手の一覧)で機械的に出せないか検討すること。

## 4. 各読み手の全文

以下に 4 本の報告をそのまま付ける。行番号は HEAD e863c8b。


---

### 4-a-body-and-town-check

#### 突き合わせ: 機能カタログ A 体と街(a-body-and-town.md)× コード

- 対象: `docs/reference/repo-guide/catalog/a-body-and-town.md`(1,145 行)。リポ HEAD `e863c8b`(src は `15b6bbd` と同じ)。
- やり方: src・tests・tools をじかに読み、grep した。既定の値は Python で取り出した。CLI の引数の定義は `shibuya.cli.main` の `parse_args` を差し替えて全 131 個を読み出し、環境変数の既定は各モジュールの `arm()` などの関数を呼んで確かめた(`SHIBUYA_*` は 1 つも立っていない)。足りない外部の包み(blake3・numba など 9 個)は、import を通すためだけに偽の空の包みを差し込んだ(数の計算には使っていない)。台帳の行は `build_registry()` を、無いの一覧と入力の一覧は `absent.py`・`inputs.py` の定数を、規則の表は JSON を数えた。
- 開いていないもの: `data/`(このチェックアウトには `data/` 自体が無い)・IMPLEMENTED.md・README・build-report・門 1 の計画・パターン台帳。つなぎの台帳 `docs/design/bridging-ledger.json` は行の id と文だけを引いた。仕分けの表 11-04 は grep と、約 20 行の見本の確かめだけ。
- ランと試験の全体は回していない。リポは変えていない(import で `__pycache__` ができたので消した。`git status` は空)。

## 1. 確かめた主張の数

| 節 | 確かめた数 | 食い違い |
|---|---:|---:|
| 0-3 切替口の表(27 行の既定・環境変数・区分) | 27 | 2(行 `--geometry`・効く機能の列) |
| 1 鉄道 | 21 | 0 |
| 2 在圏 | 22 | 1 |
| 3 歩行とナビメッシュ | 14 | 1(0-3 と同じ件) |
| 4 人の動きのモデル | 11 | 0 |
| 5 混雑場 | 8 | 0 |
| 6 席と列 | 12 | 0 |
| 7 天気と環境 | 15 | 0 |
| 8 日影 | 6 | 0 |
| 9 騒音 | 6 | 1 |
| 10 見通し | 5 | 0 |
| 11 世界過程 18 本(18 行の中身・台帳の id と executor と conf・切替口・差の表 6 行) | 30 | 0 |
| 12 世界の台帳と検査 | 8 | 0 |
| 13 無いと宣言と入力の宣言 | 7 | 0 |
| 14 規則の表 | 10 | 0 |
| 15 体の層 | 8 | 1 |
| 16 暦の口 | 7 | 3 |
| 17 近接の判定 | 6 | 0 |
| 18 時計と刻みの腕 | 7 | 1 |
| 計 | 約 230 | 10(大 0・中 3・小 7) |

確かめて合っていた主な主張(抜き書き):
- 0-3: 27 行の既定は全部合う。`--space`→nav1、`--slope`→wood、`--turn-weight`→fixed、`SHIBUYA_NAV1_DENSITY`→neighborhood、`--seat-release`→walk、`--defect-fixes-1103`→on、`--rate-rules`→off、`--absent-processes`→stopped、`--body-schedule`→sweep、`SHIBUYA_RULES_42`・`42B`→on(CLI の旗なし)、`--proximity`→distance、d=2.0、幅 60 秒(約数 12 通り)、`--clock`→global、`--step-scope`→all、`--exit-mode`→immediate、`--derive-rule`→v2、`--queue-service`→on、`--intent-max-ticks`=60、`--move-search-radius`=5、`--geometry`→node、`--area-source`→legacy。`--attendance-rate`・`--weather-scheme`・`--calendar-weekday`・`--rng-scheme` は CLI に無い(これも合う)。
- 1: 発車は 1 刻み遅れて処理(rail.py:807)。`plan_executor=True` で 12% の抽選と帰りの便が止まる(rail.py:502・:610)。上限 `floor(2.0×定員−乗車人数)`(rail.py:703・:710)。FIFO(resolve.py:2227)。運賃 180 円・科目 8=持ち出し。30 刻みで `NO_TRAIN`(resolve.py:250・:2250)。運賃の前の確かめは `r.money` だけ(resolve.py:2228)。`rail_events` は `READ_RAIL_EVENTS=False` で呼び手なし。`cap_pct` を読むのは presence の `_spread_arrivals`(旧道)だけ(presence.py:1015)。
- 2: 日課の実行部は W17 と母集団の両方がそろうランだけ立つ(build.py:694)。E1=間に合う最も遅い便(presence.py:959-979)。到着のセルは出口のセルを通し番号で割る(presence.py:1145-1148)。退出の規則(presence.py:1219-1227)。繰り延べ 30 刻み(presence.py:125)。`board_intent` と `native` は `NotImplementedError`。W12 の門のセルはエンジンが読まない(grep)。舞台の外の呼び出しの見送りは judge.py:52-58。
- 4: 速さ U(1.00, 1.60)・Kladek の 1.913 と 5.4・Fruin の 5 つの境・接続口の式・割り当て 4 回(nav1.py:1003)・係数は歩く区間だけに掛かる(advance_kernel の `L < 0` の枝)。
- 6: 席数の式と最低 1 席(crowd.py:132-134)・30 刻みと 15 刻み・`pois.capacity`=4・`EAT_DWELL_MINUTES` は定義と試験だけ。
- 7・8: NOAA の近似・WBGT の境 21/25/28/31・写像 2/4/6/8/10・日陰 0.86・舞台の外は日陰なし(rules.py:289)・`SHADOW_DATES` 8 日・雨や天候型が行為を変える処理なし(grep)。
- 11・12: `PROCESS_ORDER` 18 本の順、台帳 21 行(llm_agent 9・engine_rule 5・none 7)・PlanSpec 4 行・57 分類のうち 23・止めた過程も `step` は呼ばれ中で何もしない。各過程の時刻と量(報道 7・12・18 時、ホテル 21 時と 9 時に 120 室、補充点 0.95 と 10 時の代打、納品 5〜8 時・15%・×2、バス 6〜23 時・10 分間隔)も合う。
- 13: 無いの一覧 26 件の群の内訳 8・2・13・2・1、`engine_stopped=False` は `inbound_delivery` だけ、入力の一覧 13 件=値あり 5+欄だけ 7+納品 1。
- 14: 30 行・28 id・machine 16・human 14。読むコードの無い 8 id は src と tools に文字列が無い。器だけ 4 件は taxes.py の表と credit.py の器だけの関数。

## 2. 食い違いの一覧

| # | カタログの位置 | カタログの主張(要約) | コードの事実(ファイル:行) | 判定 | 重さ |
|---:|---|---|---|---|---|
| 1 | §9「状態」の表の 2 行目(器だけ)と「文書とコードの差」 | `system1.noise_stage_at` は読み手なし。差は「なし」 | 連絡の腕 `--contact c1`(既定 off=contact/arm.py:35・:67)が import して呼ぶ(contact/layer.py:91・:955-956)。電話とメッセージに気づく刺激の強さを騒音の段から作る(device.py:136 の `noise_db_of_stage`)。system1.py:76 の docstring の「本段では読み手が居ない」も古い=書き漏れた文書とコードの差 | 一部違う | 中 |
| 2 | §0-3 の表の `--geometry` の行と §3「状態」の器だけ | `--geometry edge` は nav1 のランでは効かない | nav1 でも `attention_on = (geometry == "edge") and (vocab_version == "v2")`(build.py:701)で注意の層が立ち、SoA の edge の欄も確保される(build.py:720-721)。焦点の処理は `r.xy` を使うので nav1 でも動く(resolve.py:1920-1940)。台帳 `DOC-nav1-arms-inert-edge-plateau` が測ったのは語彙 v1 の構成だけ。語彙 v2 と組むと結果が変わる道があるが、回していないので変わるかは確かめられない | 一部違う(条件つき) | 中 |
| 3 | §16「何をしているか」の 1 段落目 | 祝日は内閣府の CSV から読み、無ければ空で警告する | 読み込みは警告して空を返す(calendar.py:167-175)。しかし組み立てが必ず呼ぶ開始日の検査が「祝日の表が読めていない」を止める違反にしている(calendar.py:424-425・:446-447、build.py:893。試験用の印のランも止まる=build.py:887-888)。CSV が無いとランは止まる。calendar.py:16-17 の docstring「既定のランを壊さない」と :172 の警告文「祝日を空として回す」も、この挙動と合わない(書き漏れた文書とコードの差) | 一部違う | 中 |
| 4 | §16「状態」の器だけ | `--school-holidays` は渡す形だけで中身は空 | 既定が空なのは合う。渡すと開始日の検査が、その区間に入る日を含むランを止める(calendar.py:434-436・build.py:300)=渡せば効く口 | 一部違う | 小 |
| 5 | §16「既知の穴」の 3 つ目 | 日曜始まりのランの 0 日目は全員が舞台の外で待つ | 0 日目が月曜でないランは開始日の検査で止まる(calendar.py:427-428・:449)。走るのはカレンダー 3 の試験用の印のランだけ(build.py:882-890) | 一部違う(条件の書き落とし) | 小 |
| 6 | §2「何をしているか」の 5 段落目(E12) | 次のブロックが無ければ、60 分後以降の最も早い便が進行中のブロックの終わりより前にあるときだけ戻す | 条件はほかに 3 つある: ブロックの残りが 60 分以上・便が日の終わりより前・LLM の乗車で出た体だけ(`allow_return_to_current`、civic の押し出しは使わない)(presence.py:1859-1866) | 一部違う(条件の書き落とし) | 小 |
| 7 | §15「何をしているか」の箇条の 1 つ目 | 疲れは 30 刻みごとに +1、就寝中は −2 | 体の刻みで先に +1、そのあと就寝中は −2(rules.py:197-201)。寝ている体は 30 刻みで差し引き −1 | 一部違う(言い回し) | 小 |
| 8 | §18「文書とコードの差」 | なし(確かめた範囲) | regional_clock.py:21 と :408 は「メッセージと電話は今の世界に無い(C1 の後)」と書く。しかし連絡の腕 `--contact c1`(engine/contact/ の calls.py・deliver.py・layer.py)がメッセージと電話を実装している。区域の時計の側は欄だけのまま(grep で contact との結線なし) | 違う(差の書き漏れ) | 小 |
| 9 | §0-3 の表の「効く機能」の列(`--rate-rules`・`--intent-max-ticks` の行) | `--rate-rules` は 1・2・11、`--intent-max-ticks` は 3 | `--rate-rules` は倒れる率(§15)にも効く(rules.py:73-77・salient.py:331)。`--intent-max-ticks` は歩いて乗る退出の上限として §2 にも効く(build.py:863 の `walk_max_ticks`。§2 の本文には書いてある) | 一部違う(列の書き落とし) | 小 |
| 10 | §0-1 の表の 2 行目と §2「状態」の器だけ | 器だけ=予約の口 3 つ | §2 の器だけの欄は 4 項目(`board_intent`・`native`・`WORK_START`/`AT_HOME`・W12 の門のセル)。「3 つ」がどれを指すか読み取れない | 一部違う(数の食い違い) | 小 |

確かめられなかった主張(コードの外の値か、開かない約束のもの):
- 資産の中身: 出口 25 セルと表参道と明治神宮前の 6/25・W13 の窓・影のファイルの実在・ナビメッシュの 7 階、ラン 221,784、接続口 245・資産 `nav1_corridor` の実の幅(`data/` が無い・#124 は IMPLEMENTED)。
- 測った値: 18〜20 件・最大 1,355 m・32,065 体と 4,281 体・1 日の新しい経路の約 1 割・店のセルの外の在席 1.91%(記録と docstring の値)。
- `--area-source plateau` が nav1 で効かないこと(台帳の計測の値。コードの道は追い切れていない)。
- 「結果は既定と同じ」(`--body-schedule reserve`・`--batch-width-s`・`--clock regional`・`--step-scope changed`)は docstring の記述で、回していない。
- 「元の決定」の各行の ID と、「11-05/§3-2 で消す予定」などの決定文書の中身(索引と IMPLEMENTED の本文は読んでいない)。§3 の差の表の 3 行目(IMPLEMENTED #124 の見出し)。
- 仕分けの表の区分は約 20 行(M3・M5・S51・M27・A48・S18・S26・A39・S46・B7・S38・M13・S52・A49・A05・S4・S36・A12・S14・F4・M2)を見て、全部カタログと合っていた。残りは見ていない。

## 3. 書き漏れ(体と街の範囲でコードにあるがカタログに無いもの)

| # | 機能 | コードの場所 | 何が漏れているか | 重さ |
|---:|---|---|---|---|
| O1 | 開始日の検査(既定で毎ランに効く) | calendar.py:405-450・build.py:880-893 | 0 日目は祝日でない月曜だけ、2 日以上のランは連続する平日だけ、祝日の表が無いか範囲の外なら止まる。カタログの §7・§16 で「腕」と書く `--start-date`・`--sim-days` の使える範囲がこれで決まる(たとえば土日を含む 7 日のランは止まる)。§16 は `check_start` の名を挙げるだけで規則が無い | 中 |
| O2 | 連絡の腕の騒音の読み | contact/layer.py:941-960・device.py:136 | W10 の騒音の段の使い道として、電話とメッセージに気づく刺激(腕 `--contact c1`・既定 off)がある。§9 の使い道に無い(食い違い 1 と同じ根) | 小 |
| O3 | セルごとの営業中の店の数 `cells.open_count` | resolve.py:581・:1563、state_ledger.py:315 | 毎刻み書かれるが、読み手は 0(状態台帳の注「読み 0」)。町の側の器だけの欄なのに、カタログの器だけの欄に無い | 小 |
| O4 | 暦 1a の影 `--calendar-shadow 1a` | engine/calendar_shadow.py・build.py:876 | 在圏の出入りの「勤務と授業の影」を W20 から数える計器だけの腕(既定 w17=作らない)。§2 の腕の欄に無い | 小 |
| O5 | 日課の実行部を切る口 `--ablate AB-PLAN-EXECUTOR`・`plan_execution` | build.py:690-693・presence.py:660-662 | §2 の腕の欄には帰無腕 3 本はあるが、この切る口が無い(§1 の `AB-RAIL-EXECUTOR` は書いてある) | 小 |

## 4. 全体の所見

- 約 230 の主張のうち、食い違いは 10 件(大 0・中 3・小 7)だった。既定 on/off の取り違えや、無いものを有ると書く誤りは見つからなかった。既定の値・環境変数・ファイル名・関数名・定数の数は高い精度で合っており、設計の判断の土台に使ってよい。
- 系統的な誤り 1: docstring をそのまま写した所で、docstring 自体が古いとそのまま引きずる(system1 の「読み手なし」・暦の「既定のランを壊さない」・区域の時計の「メッセージは無い」)。「文書とコードの差: なし」と書いた節にも、こうした差が残っている。
- 系統的な誤り 2: モジュールの外で決まる条件の書き落とし。ほかの腕との組み合わせ(`--geometry edge` × 語彙 v2)や、組み立ての後段の検査(開始日の検査)が抜けやすい。
- 「器だけ」「効かない」「読み手なし」と書かれた所は、使う前に呼び手を grep で確かめるのがよい(1 と 2 の誤りはどちらもここに出た)。

---

### 4-b-people-check

#### 突き合わせ: カタログ B 人の中身(docs/reference/repo-guide/catalog/b-people.md)とコード

- 対象のコード: 〔読み手の機械のリポの置き場:commit の検査のためリポの写しでは伏せた〕(HEAD e863c8b・src は 15b6bbd と同一とされる)。リポのファイルは変えていない。
- 確かめ方: src・tests・tools をコードで読んだ。既定の値は、`shibuya.cli.main([])` の `parse_args` を差し替えて引数なしの結果だけを取り出し、各モジュールの `arm()`・`arms()` と既定の定数を `SHIBUYA_*` の環境変数なしで読み出した(ランは回していない)。この環境には依存のパッケージ(numba・pyarrow・blake3 ほか)が入っていないので、足りないモジュールを中身のない代役で埋めて import した。引数の定義と定数の読み出しには影響しない。
- 開いていないもの: data/(このチェックアウトには data/ が無い)・README・IMPLEMENTED.md・build-report-C7*/C8*・門 1 の計画・パターン台帳。#番号の記録から写した数値は確かめていない。

## 0. 実装役の報告のいちばん大きな主張の確かめ

主張:「今の既定のランで『考える』を担っているのは mock(決まった乱数で答える代役)で、判断モデルは src に無い」

判定: **正しい**。ただし補足が 2 点ある(下の 4・5)。

1. 既定のランで LLM の口につながるもの: `--llm` の既定は `mock`(src/shibuya/engine/run.py:2496)。`fleet_from_args` は `--llm fleet` でなければ `None` を返す(run.py:2577-2578)。`--policy` の既定も `mock`(cli.py:1035-1041)。組み立ては `llm` が注入されていなければ `_default_mock` を置く(engine/systems/build.py:648-650)。語彙 v3 では `MockLLM(form="v3")` で、行為の語は 11 語+「なし」の 12 語から、乱数の流れ(刻み・体・起床の級)で一様に引く(run.py:385-411・llm/mock.py:204-221)。プロンプトの本文は読まない。例外は発話の欄の指示 `SPEECH_FIELD_LINE` があるかだけ(mock.py:220)。`--decision-port` の既定は `legacy` で、判断の口の層は作らない(engine/decision/layer.py:68・build.py:1408-1409)。
2. 実の LLM へつなぐ道: `--llm fleet --endpoints http://…` を渡したときだけ `FleetClient`(llm/fleet.py「実 vLLM 艦隊クライアント(httpx 非同期 × N レプリカ)」)が作られる(run.py:2572-2599)。`--endpoints` が無いと止まる。夜間の実験の表 tools/night5070/experiments.json はこの形(`--llm fleet --endpoints {{ENDPOINTS}}`)で回す。`--policy classical` は艦隊と一緒に使えない(build.py:610-616)。
3. 判断モデルに当たるコード: src に無い。`判断モデル` の語は src の 26 ファイルに 59 か所出てくるが、どれも「判断モデルの代わり」「判断モデルまでのつなぎ」の注か、呼びの数え口の名(`judge_model`)。各腕の口は仮のモデルで、候補を並べて乱数の余りで一様に選ぶ(contact/port.py:217-218・duties/port.py:140-141・calendar2/port.py:178-179・calendar3/port.py:147-148・calendar_self.py:328-365)。Ruri(memory_embed.py)は記憶の「意味の手がかり」の腕の埋め込みで、判断モデルではない。重みも取得していない(作ると `EmbedUnavailable`・memory_embed.py:117-137)。「LLM を呼ぶか」を決めるのはコードの System 1(起床の検出)。「よく考えるかを決める段」は無いと宣言されている(world/processes/absent.py:271-273 `absent.deliberate`「既定は起床のたびに全部 L2」)。
4. 補足(カタログに書かれていない): 腕の層(連絡 c1・店の仕事 duties・カレンダー 1b/2/3)の判断の口と文の口は、コードで仮のモデルに固定されている(contact/layer.py:265-266 `ContactPort`・`MockTextPort`、duties/layer.py:178、calendar2/layer.py:201、calendar3/layer.py:202、calendar_self.py:1743)。`--llm fleet` を選んでも、これらの判断は艦隊へ行かない。艦隊へ行くのは主の判断の呼び(会話の番を含む)だけ。
5. 補足: manifest と日次の記録の `calls_by_model.judge_model` は、上の仮のモデルを呼んだ回数(contact/layer.py:450・476-478、duties/layer.py:317-318)。カタログ 13 節の「判断モデル 240,128」はこの数え口の値で、判断モデルが動いた数ではない(下の表の 6 行目)。

## 1. 確かめた主張の数

| 節 | 確かめた主張の数 | 主な中身 |
|---|---:|---|
| 0 一覧 | 6 | 区分と腕の本数(3 節の 6 本・8 節の 5 本ほか) |
| 1 購入 | 12 | `_apply_buy` の確かめの順と失敗の 4 種・満席で列・`_complete_buy` の 7 つの効果・持ち物 +1(255 で頭打ち)・19 時に 1 個・受け入れ数 min(4, 在庫)・合成と本番の両方で 4・`--queue-service` 既定 on・段階 2 既定 on・空腹 −4 は v1 だけ・無いの宣言 2 件・docstring の「売上+同額」 |
| 2 店選び | 11 | mock の対象は「なし」(描画は候補を渡さない)・`classify` の読み順・総称語 4 語・カテゴリ語 59 語・`BUYABLE_CATS` 7 種・候補が無い理由 5 種・`NearestChooser` の並び・既定 nearest・古典 0.5/1.0・想起優先の 3 条件・近傍 5 セル |
| 3 食事と空腹 | 15 | `_apply_eat` の順と失敗の 3 種・棚と持ち物を動かさない・消費の式・語の区切り 0.25/0.75/1.5・写し 1/5/8/10・食事で消費を 0・軽食と飲料・B5 の語の既定 hungry・舞台の外の食事・CLI は energy でライブラリは v1・腕 6 本の既定・食事の資源も `space.poi`・`absent.eat_home`・docstring の差 2 件 |
| 4 会話 | 16 | 定数(3 呼・話題 3・沈黙 5・寿命 60・間隔 60/30・断り 60・返事 3)・終わり 6 種・`_talk_partners_reach`・`_apply_talk` の失敗 3 種・`end_conversation`・`conversations` 既定 True で CLI なし・`--defect-fixes-1103` 既定 on・上限 2・`answered=True`・`important` を渡さない・相槌/締め/割り込み/拒否の記憶の呼び手なし・`walk_over_ticks` 0・`D_TALK_METERS` を読まない・相互指名・F1 の docstring・`same_cell` の名 |
| 5 近接の判定 | 9 | 既定 distance・d 2.0 と 3 値・離脱 d+1 m・`reach` の式・B5 10.3 m・打ち切り 100 m・格子 2.5 m・`marks_for("nav1")`・docstring の「node の座標」 |
| 6 発話の口 | 8 | 既定 off と環境変数・20 字・欄の指示・「こんにちは」・`modality` は空・`absent.utterance`・既定化は GPU の後・mock が欄の指示を見る |
| 7 会話の時計 | 5 | 既定 table と環境変数・table は `None`・`ChatTiming` は空・計器だけ |
| 8 記憶 | 18 | 既定 off・系 `memory` は条件なしで立つ・128 行・重要度の表・d 0.5 と w_i 0.5・τ −2.0・想起 3/2 件・要旨 16 件 40 字と源・器の既定 mem と環境変数・m0/id/table/each と埋め込みの既定・M1 の τ −3.738・ばらつき 0.15・直近 3 回・cos 0.5・`check_arms`・店の記憶と関係は記憶 on が前提・印象/浅い痕跡/注意の口の呼び手なし・Ruri の重みは未取得 |
| 9 店の評価と口コミ | 10 | 32 行・σ の表・減衰 actr・下の腕の既定 4 つ・上限なしは人も記憶の腕で 256 まで・ネットはビット 8 と σ だけで書き手なし・抽出は `llm_io.utter`・docstring の差 2 件 |
| 10 親しみ | 7 | 64 行・既定 off・`fam_visits` は classical だけが読む・`fam_exposures` の判断の読み手なし・人と道は書かない・A の式・docstring の「誰も読まない」 |
| 11 関係 | 14 | 種別 5 つ・15 辺・τ −2.322・d 0.5・密度 1.0・在職 13 週・下の腕の既定(invite on・acq-wake on・copresent off)・重み 40/20/40・同じ相手 60 分・符号は結果コードから・記憶 on が前提・copresent は関係 on が前提・人も記憶の腕は `rel_*` を読まない・同席と知人出現を作らない |
| 12 カレンダー | 14 | 開始日 2026-07-13・給料日 25 日を `replace` で別に作る・`--calendar` 既定 w17 と環境変数・`--derive-rule` v2・影 1a 既定 w17・1b の止まる条件・2 と 3 の既定 off・3 は c1 と 2 が前提・試験用の印・`KINDS` 6 つ・`STAGE_DIR`・口は一様の仮のモデル・`--calendar-weekday` の注・`StoreRules` は枠だけ |
| 13 連絡 | 16 | 既定 off と環境変数・下の腕の既定 i/b/off・台帳 9 行・c1 で 6 行・`build_fixture` は既定でも作る・`PhoneTable` は空・`TOOL_ACTION_WORDS` は空・看板の出来事 既定 off・周辺視 2.0 m・電池 20%/10%・習慣 5 回/0.1・`ContactPort` は一様・文は `MockTextPort`・仲裁・`body/system1.py` は空・家族だけの連絡先 |
| 14 店の仕事 | 15 | 開閉 5 分ごと・担当が居れば SCHEDULED/居なければ REPLACEMENT・寝ているかを見ない・補充 95%・10 時の代打・納品 5〜8 時と 15%・duties 既定 off と環境変数・`staffed_now` は起きているかまで見る・`role_sink` は腕だけ・05 時の廃棄は旧道だけ・無いの宣言・docstring の 80%・役割語 11 語・`has_permission`・`executor=llm_agent` |
| 15 意図と活動層 | 5 | 活動層は v3 で既定 on・意図の層の作る条件・60 刻み・docstring の「engine.run」 |
| 16 手伝い・断る・通報 | 7 | 手伝いは必ず BAD_TARGET・断るは OK・通報の窓 5 刻み・前提の検査 既定 on・既定のランで顕著行為の過程が立つ・`absent.help_refuse_effect`・`absent.public_service_dispatch` |
| 17 人物の文 | 5 | `load_persona`・`persona_blocks` の呼び手は src に無い(試験だけ)・切替口なし・構築側の文のファイルあり |
| 報告の大きな主張(上の 0) | 8 | 上の 1〜5 の分け方 |
| 計 | 201 | |

## 2. 食い違いの一覧

| # | カタログの位置 | カタログの主張(要約) | コードの事実(ファイル:行) | 判定 | 重さ |
|---:|---|---|---|---|---|
| 1 | 2 節「何をしているか」第 4 段落・「状態」の最寄りの選び手 | 既定の `NearestChooser` は、距離の昇順 → 可視の降順 → POI 番号の先頭 1 件 | 選び手の規則そのものはそのとおり(engine/chooser.py:115-143)。ただし既定の道の候補は今のセルの POI だけで(engine/poi_target.py:462 `cand_all = base`)、距離は `cell_dist[cell, poi_cell[cands]]`=全候補で同じ値(poi_target.py:512)。だから既定のランの店選びは、実際には「可視の降順 → 番号」で決まる。距離が効くのは、ほかのセルの店を見る `_pick` の道(poi_target.py:600-616・631-645)だけ。CLI の help も「可視の降順 → POI 索引」と書く(cli.py:1029-1032) | 一部違う | 中 |
| 2 | 3 節「何をしているか」箇条の 3 つ目 | 飲食系の店の購入は、軽食か飲料(比 0.03)として食後の消費を減らす | 0.03 は飲料だけ(`DRINK_SHARE`・engine/energy.py:279-280)。軽食は性と年齢の階級ごとの「間」の比 `snack_share_of`(energy.py:608-611・engine/resolve.py:1246-1249)。飲料の subcat は「実資産の W6 には 0 件」(energy.py:284)なので、本番の世界では 0.03 の道は通らない | 一部違う | 中 |
| 3 | 2 節「何をしているか」第 3 段落 | 候補は…営業中で、購入は棚の在庫があるもの | 購入と並ぶでは、飲食店の POI は棚の在庫を見ずに候補に残る(poi_target.py:490-491 `stock_ok[is_open] \| eatery[is_open]`)。在庫が 0 の飲食店が「購入」の候補に残り、後で `_apply_buy` の OUT_OF_STOCK か取り合いの決着で落ちる | 一部違う | 小 |
| 4 | 5 節「既知の穴」1 つ目 | 今の既定の nav1 では、建物の中の体は入口の点に居る | `--space` の既定は nav1(engine/space/nav1.py:97)。ただし nav1 が立つのは、本番の世界の置き場に `nav1_*` の資産があるときだけ。合成の世界と資産の無い置き場は legacy で回る(build.py:477-492)。`--geometry` の既定は node(cli.py:1276-1278)。この条件がカタログに無い | 一部違う | 小 |
| 5 | 13 節「文書とコードの差」2 つ目 | `tools/__init__.py`・`contacts.py`・`groups.py`・`registry.py` の「C0 では誰も読まない」は C0 当時の文 | 3 つのファイルにはその文がある(tools/contacts.py:10・groups.py:10・registry.py:33)。`tools/__init__.py` の文は「C0 は器だけ(既定の final・behavior-hash・テープ・描画は動かない)」(tools/__init__.py:9)で、「誰も読まない」ではない | 一部違う | 小 |
| 6 | 13 節「既知の穴」2 つ目 | 判断の呼びは 5,000 体 1 日で、判断モデル 240,128・LLM 32,482 | 数え口 `judge_model` は仮のモデル `ContactPort` の呼びの数、`llm` は定型の文の口 `MockTextPort` の呼びの数(engine/contact/layer.py:265-266・450・466-478)。判断モデルも LLM も動いていない。値そのものは #116 の写しで確かめていない | 一部違う(言い回しが誤解を招く)・値は確かめられない | 中 |
| 7 | 12 節「状態」カレンダー 1b の行・「未確認」5 つ目 | W20 の表が無いと止まる(世界の置き場を見る) | 置き場のほかに環境変数 `SHIBUYA_CALENDAR_W20` でも表の場所を渡せる(engine/calendar_shadow.py:100・calendar_self.py:1739-1740 の止まる文も「world_dir か SHIBUYA_CALENDAR_W20」と書く) | 一部違う(書き落とし) | 小 |
| 8 | 1・3・4・8・12〜14 節の #番号つきの実測の値(例 166 回/117 回・509 体/103 本・招待 2,218・約束の行 37,774・遅刻 697・155,148 行/27.9 MB ほか) | 記録からの写し | 値は記録の側にあり、コードでは確かめられない。IMPLEMENTED は開いていない。カタログ自身も「写し」と断っている | 確かめられない | 小 |
| 9 | 3 節「既知の穴」・12 節「既知の穴」2 つ目 | W17 の食事の行の数・W17 v2 は月曜の行しか無い | data/ の中身にかかる。このチェックアウトには data/ が無い | 確かめられない | 小 |
| 10 | 2・3・4・6・8・11・14 節の「文書とコードの差」のうち、決定の原文との差(例 `09-30/Q31`・`Q34`・`Q35`・`Q48`・`Q57` の 40 字・`09-30/Q111` の容量 50) | 決定はこう決め、コードの既定はこう | コードの側(既定 hungry・20 字・`--rel-k` 15 ほか)は確かめた。決定の原文の側は今回の範囲(コード)の外で、開いていない | 確かめられない(コードの側は合っている) | 小 |

食い違いとしなかったもの(念のため): 「既定=系 memory は立つが層が無いので何もしない」は正しい(systems/table.py:426-435 に `when=` が無く、remember.py:35 で `mem_layer is not None` を見る)。16 節の「通報はほとんど BAD_TARGET のはず」は推測と断ってあり、既定のランで顕著行為の過程が立つこと(engine/processes/runner.py:430-440 の既定は全部の過程・systems/act.py:117)はコードと合う。抽選の件数は数えていない。

## 3. 書き漏れ(人の範囲で、コードにあってカタログに無いもの)

| # | 中身 | コード(ファイル:行) | 重さ | 置き場の案 |
|---:|---|---|---|---|
| 1 | 腕の層(連絡・店の仕事・カレンダー 1b/2/3)の判断の口と文の口は、コードで仮のモデルに固定。`--llm fleet` を選んでも艦隊へ行かない。艦隊へ行くのは主の判断の呼び(会話の番を含む)だけ | contact/layer.py:265-266・duties/layer.py:178・calendar2/layer.py:201・calendar3/layer.py:202・calendar_self.py:1743 | 中 | 12〜14 節の「既知の穴」。報告の大きな主張の注 |
| 2 | 「よく考えるかを決める段」は無いと宣言されている(既定は起床のたびに全部 L2)。判断モデルが無いことの宣言の側 | world/processes/absent.py:271-273(`absent.deliberate`・routing 95) | 中(C 群との境) | 17 節か「読み方」の判断の担い手の注 |
| 3 | 判断の口の腕 `--decision-port {legacy,port}`(既定 legacy・環境変数 `SHIBUYA_DECISION_PORT`)。port のとき mock の代わりに `MockPort`(同じ乱数の鍵で同じ番号)・`ClassicalPort`・`LlmPort` を口に通す | engine/decision/layer.py:67-82・decision/ports.py:1-80・build.py:1408-1430 | 小(本体は C 群) | 「考える」の担い手を書く所の注 |
| 4 | 古典の方策の交際の相手の切替口 `--classical-social {acquaintance,near_first}`(既定 acquaintance)。会話の相手の選び方を変える | cli.py:1049-1056・build.py:1222-1251(`classical_policy.acq_fn`・`partner_fn`) | 小 | 4 節か 11 節の状態の表(腕の中) |
| 5 | CLI の `--chooser` の help が並びを「可視の降順 → POI 索引」と書き、docstring とコードの「距離 → 可視 → 索引」と違う | cli.py:1029-1032・chooser.py:118・141 | 小 | 2 節「文書とコードの差」 |
| 6 | `ProximityLayer` の docstring「既定の腕 cell では作らない」は古い(既定は distance) | engine/proximity.py:448 | 小 | 5 節「文書とコードの差」 |
| 7 | 既定の道の店選びで距離が効かないこと(上の表の 1 行目)。既定のランの「最寄り」は、今のセルの中で最も見える店 | poi_target.py:462・512 | 中 | 2 節「既知の穴」 |

## 4. 全体の所見

1. 区分(既定・腕・器・無い)と既定の値は、確かめた 201 の主張のうち、ほぼ全部がコードと合っていた。各腕の既定と環境変数の名は、CLI の引数・`arm()`・定数のどれから辿っても一致した。
2. 報告の大きな主張(既定で「考える」のは mock、判断モデルは src に無い)は正しい。補うべきなのは、腕の層の判断が `--llm fleet` でも仮のモデルのままである点と、数え口 `judge_model` が仮のモデルの呼びを数えている点。
3. 設計の判断に効くずれは 2 つ。既定の店選びは距離ではなく可視の順で決まる。軽食の摂取は 0.03 ではなく性と年齢の比。
4. 記憶・関係・発話・カレンダー・連絡を「腕」とする区分は正しい。既定ではどれも層を作らない(系 `memory` だけは立つが、中身は動かない)。
5. #番号の実測の値と data/ に依る主張は、コードでは確かめられない。外に出す前には記録の側での突き合わせが別に要る。

---

### 4-c-foundation-check

#### c-foundation.md の突き合わせ(読み手の側)

- 対象: `docs/reference/repo-guide/catalog/c-foundation.md`(23 機能・1,210 行)
- 照らしたコード: HEAD `e863c8b` の作業木(src は `15b6bbd` と同一とされる版)。src・tests・tools・pyproject.toml・.github/workflows/ci.yml・.githooks/pre-commit を読んだ。
- 確かめ方: grep と、短い python で定数と既定を読み出した。CLI の既定は `shibuya.cli.main` の argparse を中で組ませて全部の引数の既定を出した。腕の既定は各モジュールの `arm()` を `SHIBUYA_*` なしで呼んで出した。
- 制約: この機械には blake3・numba・pyarrow・xxhash・cbor2・zstandard・duckdb・httpx が入っていない。import を通すため、scratchpad の中だけで代用のモジュールを差して、定数と既定を読むためだけに使った(ハッシュの値などは使っていない)。ランと試験は回していない。data/ は開いていない。リポのファイルは変えていない。

## 1. 確かめた主張の数

| 機能 | 確かめた主張 | 合う | 食い違い(下の表の番号) |
|---|---:|---:|---|
| §0-1 入口ごとの既定 | 3 | 3 | — |
| C1 経済と台帳 | 18 | 17 | 1 |
| C2 権利 | 11 | 10 | 2 |
| C3 計器 | 13 | 11 | 3・8 |
| C4 manifest とランの種類 | 8 | 8 | — |
| C5 実験と分岐 | 12 | 12 | — |
| C6 応答の記録(テープ) | 11 | 9 | 4・5 |
| C7 出来事の記録 | 8 | 8 | — |
| C8 保存と再開 | 12 | 12 | — |
| C9 状態の台帳 | 7 | 7 | — |
| C10 LLM サーバー群 | 13 | 13 | — |
| C11 判断の口 | 13 | 12 | 6 |
| C12 語彙と読み取り | 9 | 9 | — |
| C13 知覚 | 13 | 13 | — |
| C14 呼び出し | 12 | 12 | — |
| C15 行為の解決 | 6 | 6 | — |
| C16 進行役・系の表 | 10 | 9 | 7 |
| C17 時計と窓 | 9 | 9 | — |
| C18 乱数と決定論 | 11 | 9 | 9・10 |
| C19 構築 | 10 | 10 | — |
| C20 母集団 | 6 | 5 | 11 |
| C21 ビューア | 5 | 5 | — |
| C22 道具の台帳 | 6 | 6 | — |
| C23 つなぎの台帳と「無い」 | 8 | 8 | — |
| 計 | 234 | 223 | 11 件(違う 1・一部違う 7・確かめられない 3) |

コードと合った主な数: 系 36(組み立て 1・日の頭 1・刻みの中 30・日の終わり 1・ランの終わり 3)/状態の台帳 254 行(SoA 99=agents 82・cells 5・pois 9・知覚 3/外 155/腕 41/版 `state-ledger/10e-ret`)/テープ 21 列(`shibuya.tape/4`)/出来事の語彙 118 語/科目 15・部門 6・流れの登録 20/つなぎの台帳 active 763・removed 31/absent.py 26 行(8・2・13・2・1)/間隔の表 11 行(0/360/150/60/15/45/10/15/5/5/30)/呼び出し条件 12/知覚の上限 12 行・空の欄 10/役割語 v3 11 語/道具 9 行/import-linter の契約 5/CI 3 段。CLI と腕の既定(`--economy-stage2`→on・`--decision-port`→legacy・`--batch-width-s`→60・`--talk-clock`→table・`--step-scope`→all・`--body-schedule`→sweep・`--clock`→global・`--events` on・`--l4-scale` 0・`--vocab-version` v3・`--hunger-model` energy ほか)は全部合った。

## 2. 食い違いの一覧

| # | カタログの位置 | 主張(短く) | コードの事実(ファイル:行) | 判定 | 重さ |
|---:|---|---|---|---|---|
| 1 | C1「既知の穴」2 つ目 | 払い出しは最大 8 スロットで、9 スロット以上の店は偽の品切れになる(S12) | `GoodsLedger.sell_many` は 1 回の呼びで、店ごとの前置数を棚の累積和に当て、全スロットをまたいで払い出す(src/shibuya/economy/goods.py:614-659。docstring 622-628 は「正しい払い出しはここで完結」「8 回の再試行は保険」)。`_apply_buy` の 8 回の再試行(src/shibuya/engine/resolve.py:238・2505-2514)は、進まなければ抜けるだけ。resolve.py:2500-2504 の注は 09-08 の直しより前の記述のまま。棚卸しの表の S12 の行はこの古い注を読んだと見られる | 違う(コードの読み。ランでは確かめていない) | 中 |
| 2 | C2「状態」の表 6 行目 | 信用・道路の区間・看板の権利は「種類の表にある」 | 権利の種類(`KINDS`)に足したのは `credit` だけ。`road_segment`・`signboard` は物の種類(`OBJECT_KINDS`)で、許可(`licence`)の対象(src/shibuya/engine/rights/ledger.py:23-27) | 一部違う | 小 |
| 3 | C3「状態」の表「判断モデルの評価」の行 | 実装のある当て口は mock・古典・テープだけ。Clef ほかは口だけ | 〔11-01 段 1 の 3〕で logprob の当て口が実装済み: `HFCausalChoiceScorer`(tools/instruments/dm_eval/backends/hf.py:58)・`VLLMLogprobScorer`(backends/vllm.py:91)・`LogprobChoiceScorer`(backends/base.py:264)。tools/instruments/dm_eval/__init__.py:20-21 にも書いてある(15 行の「口だけ」は judge の当て口の話)。重みと GPU が無いので回していないだけ | 一部違う(書き漏れ) | 中 |
| 4 | C6「状態」の表 最後の行 | 複数日のランと状態の口との組み合わせは無い。組み立てで `ValueError` | 止めるのは再生だけ(src/shibuya/engine/systems/build.py:309-310 の条件は `(sim_days > 1 or _state_mode) and (mode == "replay" or replay is not None)`)。録画は複数日・状態の書き出し・再開と一緒に使え、試験がそう回している(tests/engine/duties/test_du_runs.py:311-316・tests/engine/test_version_bump_10e.py:60・77) | 一部違う | 中 |
| 5 | C6「何をしているか」1 文目 | LLM の 1 呼び出しを 1 行に残す | テープの行を書くのは `LLMBridge` だけ(src/shibuya/engine/llm_bridge.py:964-990)。答え手が mock でも古典の方策でも 1 行になる(古典は build.py:652 で `llm = classical_policy`)。腕の判断の口(連絡・カレンダー 2/3・店の仕事)の呼びはテープに書かない(engine/contact・calendar2・calendar3・duties・decision に tape の参照が無い) | 一部違う(範囲の書き漏れ) | 小 |
| 6 | C11「状態」の表「判断モデル」の行 | 判断モデルは無い(宣言なし)。`PORT_NAMES` は llm・mock・classical だけ | 本物のモデルは無い。ただし腕 `--contact c1`・`--calendar-2 arm`・`--calendar-3 arm`・`--duties arm` には「判断モデル」の呼びの道があり、仮のモデル(mock)が答える(src/shibuya/engine/contact/port.py:3-10)。manifest の `calls_by_model.judge_model` がその呼数を数える(src/shibuya/engine/run.py:517-539・engine/contact/layer.py:476-478。既定のランは 0) | 一部違う(書き漏れ) | 中 |
| 7 | C16「何をしているか」 | 既定のランで立つのは刻みの中の 22 系 | 22 は「無条件の 18 系+presence・conversation・activity_intent・energy_after」(src/shibuya/engine/systems/table.py:107 の `SYSTEMS`・conductor.py:104-129)。presence は W17 と W16 の資産があるときだけ立つ(build.py:682・694)ので、資産の無い世界(CI など)では 21 系。energy_after は空腹 energy(CLI の既定)のときだけで、`run_day` の既定(v1)では立たない | 一部違う(条件の書き漏れ) | 小 |
| 8 | C3「既知の穴」3 つ目 | 計器の「LLM の呼数」は mock を含む | そのとおりだが範囲が狭い。`result.llm_calls += len(sel)` は答え手によらず足す(src/shibuya/engine/systems/decide.py:212)ので、古典の方策のランでも数える(古典は classical.py:308 で「LLM 0 呼」と書く)。層の記録では mock を層 2 に数える(build.py:1102) | 一部違う(足りない) | 小 |
| 9 | C18「何をしているか」 | v3-0a で、届く 18 か所の鍵を世界の時刻 t_ns から作る形にした | src で `key_time_from_t_ns`・`time_key_at` を呼ぶ箇所は 17(decide.py:162・decision/layer.py:310・decision/port.py:322・contact/layer.py:447・507・518・contact/port.py:225・235・calendar2/layer.py:271・calendar2/port.py:185・195・calendar3/layer.py:281・calendar3/port.py:154・164・duties/layer.py:290・duties/port.py:147・157)と定義 1(decision/port.py:315)。18 の数え方が分からず照らせない | 確かめられない | 小 |
| 10 | C18「既知の穴」1 つ目 | 刻みの番号から作る鍵が約 27 か所残る | 短い検索では数を出せなかった(`MockPort.pick` が `ctx.step` を使う=src/shibuya/engine/decision/ports.py:92 は 1 例) | 確かめられない | 小 |
| 11 | C20「何をしているか」・§4 | 母集団は 345,858 体 | data/ を開いていないので確かめていない(カタログも §4 で未確認と宣言している) | 確かめられない | 小 |

## 3. 依頼の重点の主張

| 主張 | 出どころ | コードの事実 | 判定 |
|---|---|---|---|
| 刻みの中の系は 30 本で、既定で立つのは 22 本 | 段 1 §1-2・カタログ C16 | `SYSTEMS` は 36。timing が tick のものは 30 で、条件なし 18・条件つき 12(conductor.py:104-123 の `WHEN`)。CLI の既定で立つ条件は presence・conv・act_layer・energy の 4 つで 22。立たない腕の 8 系は experiment・home_meal・relations_wake・contact・calendar_3・calendar_2・duties・familiarity | 合う(条件は #7) |
| 世界過程は 18 本で、5 本は既定で止まる | 段 1 §9(カタログ C は書いていない。A の担当) | `PROCESS_ORDER` は 18(src/shibuya/engine/processes/runner.py:88-109)。丸ごと止まるのは street_cleaning・road_works・dispatch・infra(腕 `absent_processes`=stopped。civic.py:162・442 ほか)と last_mile(腕 `rate_rules`=off。logistics.py:85-86)の 5 本。`absent_processes.PROCESSES`(absent_processes.py:57)の 5 件目 waste_collection は waste 過程の中のごみ収集だけ(goods_flow.py:535)。止め方が 2 系統あり、「止めた 5 本」と `absent_processes` の「5 件」は同じ集合ではない | 数は合う。中身に注意 |
| 既定は 5,000 体で 1 日 60,939 呼(12.19 呼/体/日) | 段 1 §0。記録は docs/bench/analysis/fix4-1103/README.md:43・53 | 記録の値。60,939 ÷ 5,000 = 12.19 は計算で合う。ランは data/world/v2 を読むので回していない。tools/instruments/dm_eval/judge.py:85-88 は古い 64,528 呼/日を母数に持つ。src/shibuya/engine/arbiter.py:53 の docstring には 56,488 呼が残る | 確かめられない(記録どおり) |
| 計器の LLM の呼数は mock を含む | カタログ C3 | decide.py:212 で合う。古典の方策も含む(#8) | 合う |
| テープに判断モデルの呼び・候補・確率が載らない | カタログに明文は無い | テープの列は 21 で、候補・並び・確率の列は無い(src/shibuya/engine/tape.py:144-172)。行を書くのは `LLMBridge` だけ。判断の口(port)の候補の源と提示の番号の分布は計器と出来事の記録へ行き(decision/layer.py:12-17)、腕の判断の口の呼びも含めてテープへは行かない | 合う |
| logprobs は src に 0 件 | カタログに明文は無い | src の .py に 1 件ある: src/shibuya/engine/chooser.py:6 の docstring「GPU 後の ``logprob`` はここに増える」(実装は無い)。tools には実装がある(dm_eval/backends の hf.py・vllm.py・base.py と leak_check) | 違う(0 件ではなく docstring の 1 件。実装は src に無い) |
| 決定論(byte-check) | カタログに明文は無い | 下の「書き漏れ」の 1 | 書き漏れ |

## 4. 書き漏れの重要な機能

| 機能 | コードの所在 | 何が抜けているか | 重さ |
|---|---|---|---|
| byte-check(決定論と「1 バイト不変」の受入) | 道具は docs/bench/analysis/ の下に記録ごとに置かれている(wallbounce-1012/10e/byte_check_10e.py・wallbounce-1012/bd35/tools/byte_check_bd35.py・wave2-2026-09-30/wave2_bytecheck.py・fix4-1103/bytecheck ほか)。src の docstring が「byte-check 19 構成」を受入の基準に引く(engine/systems/__init__.py:4・engine/speech_clock.py:16・engine/step_scope.py:29・engine/tape.py:195) | C18 に無い。tools/ にも CI にも無く、作者の機械で版上げのたびに回す(.github/workflows/ci.yml:6)。決定論の判断の根拠がどこにあるか読めない | 中 |
| CI と pre-commit の中身 | .github/workflows/ci.yml:19-92・.githooks/pre-commit・tools/scan_secrets.py・tools/commit_check.py・tests/_data_ids.py・tests/_time_gates.py | C16 は「3 段」の 1 行だけ。ci-0 は祝日の CSV の md5・秘密スキャン・import-linter・data の未追跡・カードの新しさ。ci-1 は not gpu and not slow で、data の要る試験は `requires_data` の印で飛ぶ。ci-2 は毎晩と手動だけで、時間の門は記録だけ(`SHIBUYA_TIME_GATES=record`)。data の要る試験・golden・性能の門・byte-check は CI の外。「CI が緑=決定論を確かめた」と読み違えるおそれ | 中 |
| golden の環境の行 | tests/golden_env.py:1-29 | golden は登録した 1 環境(Windows 11・Python 3.12.10・numpy 2.5.3 ほか)とだけ比べる。ほかの環境(CI の Ubuntu を含む)は同じ設定 2 回の一致(A/A)と警告だけで、落とさない | 中 |
| 判断モデルの呼数の欄 | src/shibuya/engine/run.py:517-539(`calls_by_model.judge_model`) | #6 と同じ。C3 の計器にも C11 にも出てこない | (#6) |
| 計器の古い母数 | tools/instruments/dm_eval/judge.py:85-88 | dm_eval の「1 シム日あたりの GPU 時間」の母数が 64,528 呼/日(bd35 の記録)のままで、今の記録の 60,939 と違う | 小 |
| カードと決定の索引の自動生成 | tools/repo_guide/・tools/decision_index.py | 文書を作る道具で、CI の ci-0 と pre-commit が `--check` を回す。カタログに無い | 小 |

## 5. 全体の所見

1. 234 の主張を確かめ、食い違いは 11 件(違う 1・一部違う 7・確かめられない 3)。大はない。既定値・切替口・登録の数はほぼ全部コードと合う。
2. ずれは既定のランの外の道の書き方に集まっている。テープの録画と複数日(#4)、腕の判断モデルの道と呼数の欄(#6)、dm_eval の logprob の当て口(#3)。
3. 既知の穴の S12(#1)は今のコードでは起きない。棚卸しの表の読みをそのまま写していて、resolve.py の古い注が元になっている。
4. 決定論の受入(byte-check・golden)と CI の範囲が書かれていない。CI が緑でも決定論は確かめていない、という点が読めない。
5. 「logprobs は src に 0 件」は、正確には「docstring の 1 件だけで実装は 0」。tools には実装がある。

---

### 4-dayflow-cansay-check

#### day-flow.md と can-say.md の突き合わせ(読み手)

- 対象: `docs/reference/repo-guide/day-flow.md`(328 行)・`docs/reference/repo-guide/can-say.md`(112 行)
- リポ: `〔読み手の機械のリポの置き場:commit の検査のためリポの写しでは伏せた〕`。HEAD `e863c8b`。`git diff 15b6bbd HEAD -- src` は空で、src は 15b6bbd と同じです。
- 確かめ方: コードを静的に読みました。既定の値は Python で読み出しました。CLI の引数は `parse_args` の時点で捕まえ、各モジュールの腕の関数は `SHIBUYA_*` を消して呼びました。この環境には numba・blake3・httpx など依存の一部が無いので、import を通すだけの代役を scratchpad に置きました(ランには使っていません)。
- `data/` はこの環境に無いので、ランは回せていません(回していません)。資産の中身に頼る主張は、記録と照らしただけです。
- 開いていないもの: IMPLEMENTED.md・docs/ops/build-report-C7*・C8*・門 1 の計画・パターン台帳・封印の層・holdout の記録・data/ の全部。

## 1. 食い違いの一覧

判定は「違う」「一部違う」「確かめられない」の 3 つです。重さは「大=設計の判断や外への説明を誤らせる」「中」「小」です。

| # | 文書と位置 | 主張(短く) | コードや記録の事実 | 判定 | 重さ |
|---:|---|---|---|---|---|
| 1 | day-flow §6 区分表「器」(207 行)・§10-2 器 14(291 行) | pricing.py は「価格形成。結線しない」器 | 改定の関数(Calvo・propose_price)は結線されていません。ただし係数 `K_VOLUME/K_AVERAGE/K_PREMIUM`(pricing.py:60-62)は `goods.CATEGORY_K`(goods.py:180-184)として原価=価格 ÷ k に使われます(goods.py:433-435)。参入資本の原価率にも使われます(entry_capital.py:25・173)。つまり既定のランの補充の代金と参入資本の値に効きます | 一部違う | 小 |
| 2 | day-flow §6 区分表「器」(207 行) | credit.py は「信用。呼び手なし」 | 既定(段階 2 on)では `Ledger.attach_stage2` が `CreditBook(capacity=0)` を作り(economy/ledger.py:403-410)、記録にも載せます(ledger.py:395)。中身は空で結果は変えないので、「器」という区分は合います。「呼び手なし」は違います | 一部違う | 小 |
| 3 | day-flow §11 #15(316 行) | 11-05/9-3d・9-5 で「考え中も歩く速さは落ちない」「再開の費用は無い」を無いの一覧へ足す決定 | 原文で無いの一覧へ足すと決めたのは 3 件です。9-3d が「考え中も歩く速さは落ちない」と「考え中も回避に失敗しない」(prompt-2026-11-05-reply6.md:40)、9-5 が「再開の費用は無い」(同:49)。文書は「回避に失敗しない」を落としています。absent.py に 3 件とも行が無い点は正しいです | 一部違う | 小 |
| 4 | day-flow §11 #16(317 行) | 発注文の手がかりが `engine/conductor.py` | リポの中で `engine/conductor.py` と書いた文は day-flow.md のほかに見つかりません(grep)。発注文はリポの外にあるとみられます。コードの側の事実(`src/shibuya/engine/conductor.py` は無く、実体は `engine/systems/conductor.py`)は正しいです | 確かめられない | 小 |
| 5 | day-flow §10-2 末尾(294 行) | 旧道の切替口は 10 本 | CLI の help には、ほかにも旧値の再現と書いた切替口があります。`--vocab-version v1/v2`(「v1 の checkpoint を再現するとき」cli.py:936-940)・`--l4-scale 1.0`(「旧挙動」cli.py:916-921)・`--report-precondition off`(「checkpoint ba01bd0b を再現する帰無腕」cli.py:1000-1004)・`--wom-source reason-target`(「旧の再現用」cli.py:1172-1177)・`--derive-rule v1`(cli.py:1263)。後ろの 3 本は文書の数え方(帰無の腕・腕の中の下の腕は数えない)で外れると読めます。`--vocab-version v1/v2` と `--l4-scale 1.0` は、腕にも旧道にも数えられていません。§12 に「網羅は未確認」とは書いてあります | 一部違う | 小 |
| 6 | day-flow §0-1 の 1(10 行) | mock はプロンプトを読まない(発話の欄の指示だけが例外) | CLI の既定と CLI の腕の範囲では正しいです。ただし `run_day` の引数 `mock_move_target_p`・`mock_out_of_cell_target_p`(既定 0・CLI に引数なし)を上げると、mock は B2 の「見えるもの」を読みます(mock.py:224-263・run.py:386-410) | 一部違う | 小 |
| 7 | day-flow §6 第 2 段落(193 行) | 「席が空くと並んだ順に入り、15 刻みで離れます」 | 15 は列の待ちの離脱の閾値です(`WAIT_MAX_TICKS=15`・crowd.py:96-97)。席に座っていられるのは最大 30 刻みです(`DWELL_MAX_TICKS`)。文の並びだと「席に入ってから 15 刻みで離れる」とも読めます | 一部違う(書き方) | 小 |
| 8 | day-flow §11(一覧の漏れ) | 文書とコードの違いは 17 件 | 次の 3 件が一覧にありません。① stage2.py の冒頭の表は「給与の天引きは器だけ(規則の表に行が無い=0)」(economy/stage2.py:12-14)ですが、既定の `SHIBUYA_RULES_42=on` で天引きが動きます(engine/economy_rules.py:5-7)。day-flow §6 の「天引きが動きます」はコードと合っています。② 報道の過程の docstring と要約は「全セルへ届く」「到達=全セル」(civic.py:240・279)ですが、実際は在席者のいるセルだけです(salient.py:369-371)。day-flow §9 の記述はコードと合っています。③ change_detect.py:37 に「流れ・顕著行為ダイジェストは C3 では常に 0」という古い注が残っています | 一部違う(漏れ) | 小 |
| 9 | can-say 冒頭 2(4 行)・§2 の表の見出し(60 行) | c7-day-4 は commit `1e20cd3` で、seed 3 本 | seed 1 は HEAD=1e20cd3 です(docs/bench/c7/accept_c7-day-4/run_cli_summary.txt:1)。seed 2・3 の記録は「HEAD 1e20cd3+AB7=ラン経路は同一」です(docs/bench/c7/ensemble/c7-day-4_seed1_vs_seed2.md:3・c7-day-4_seeds1-3.md:3) | 一部違う | 小 |
| 10 | can-say #21(35 行) | 記憶と店の評価は既定 off で、mock では行動が変わらない | 既定の店選び(nearest)なら正しいです。`--store-memory on` に `--chooser classical` を組むと、想起を先にする店選びが働き、mock でも行き先の店が変わります(poi_target.py:280・422-437・build.py:1198-1212) | 一部違う | 小 |
| 11 | can-say #30(44 行) | 信用・価格形成・家賃は器だけで動いていない | 価格の改定は動かないので、外向けの文としては正しいです。ただし pricing.py の係数は既定で原価と参入資本に効きます(上の #1)。家賃は空欄です(rights/initial.py:12・63)。信用は容量 0 の帳面です(上の #2) | 一部違う(印) | 小 |
| 12 | can-say #32(46 行)・#38(52 行) | 照合と試験の道具・世界の構築を「腕だけ(ランの外)」とする | 段 1 §0-3 の腕の定義は「既定では動かず、切替口を立てると動く」です(day-flow.md:29)。構築の道具と照合の道具はランの切替口ではありません。定義の外の使い方で、行の数の「腕だけ 13」にこの 2 行が入っています | 一部違う(区分の当てはめ) | 小 |
| 13 | can-say 冒頭 4(6 行)・§5 末行(108 行) | 今の版の照合の記録は確認できない | 開封の記録と封印の層は開かない約束なので、記録が無いことは確かめられません。9 月の 0/4 NOT PASS は devlog.md:11 の記録と合います | 確かめられない | 小 |
| 14 | can-say §5 #32(104 行) | C8 の報告は 9 月 10 日の時点で進行中のまま | docs/ops/build-report-C8 を開かない約束なので、確かめられません。9 月の ablation(5,000 体・8B を 7 枚)は docs/ops/discord_report_ablations_2026-09-18.md で確かめました | 確かめられない | 小 |
| 15 | can-say §6 出どころ(112 行) | C7 の受入報告から書いた | build-report-C7 は開かない約束なので、確かめられません。代わりに docs/bench/c7 の記録で、390,067 体・seed 3 本・Qwen3-8B-int8・7 endpoints・温度 0.7・最大 96 トークン・derive v2.1 を確かめました(layer2_review.md:25・ensemble の 2 本) | 確かめられない(代わりの記録で一致) | 小 |

「大」と「中」に当たる食い違いは見つかりませんでした。

## 2. 確かめて合っていた主な点

### 依頼の 2「既定のランで考えるのは mock で、判断モデルは src に無い」= 合っています

コードの経路は次のとおりです。

1. `cli.main` の既定は `--llm mock`・`--policy mock` です。
2. `fleet_from_args` は `None` を返します(run.py:2577-2578)。CLI は `llm` を渡しません。
3. `build` の中で `llm = _default_mock(seed, "v3", 0, 0)` となり(build.py:653-655・run.py:402-410)、`MockLLM(form="v3")` が作られます。語彙 v3 は 12 語で、「なし」を含みます(contract で読み出し)。
4. 判断の口の層は既定で作られません。`--decision-port` の既定が legacy で、`decision_layer=None` のままです(build.py:1409-1410)。
5. decide 系は `bridge.call` で描画したうえで mock に渡します(decide.py:110-117)。対象の候補は空で(llm_bridge.py:217・792)、対象は「なし」になります。移動のときだけ 1/3 が「あたり」です(mock.py:209-211)。
6. 判断の口の実装は LlmPort・MockPort・ClassicalPort の 3 つだけです(decision/ports.py)。src の中の「判断モデル」という語は、注と「判断モデルの代わり」の仮のモデルの文だけです。dm_eval は tools/instruments/dm_eval にあり、src の外です。
7. 計器の layer_counts は mock の呼び出しも層 2 に数えます(build.py:1102)。

### day-flow で合っていた主な点

- CLI の既定の値(§0-2 の 27 個)は、読み出した値と全部一致しました。例: proximity distance・2.0 m、economy_stage2 on、SHIBUYA_RULES_42 on、absent stopped、defect_fixes on、seat_release walk、space nav1、events on。`run_day` の既定(語彙 v1・空腹 v1・l4_scale 1.0)も合っています。
- 系の表 `SYSTEMS` は 36 個で、刻みの中は 30 個です。順は文書と同じです。
- 立つ条件(conductor.WHEN)と build の層の有無から数えると、既定で立つ系は 22 です。立たない 8 系は experiment・home_meal・relations_wake・contact・calendar_3・calendar_2・duties・familiarity です。1 日のランでは day_head も day_close も立ちません(day.py:19-26)。
- 刻み T の decide で出た答えは、T+1 の apply_responses で意図になります。L1 は 2.6 秒で、切り上げて 1 刻みです(llm_bridge.py:161-198)。
- 起床について: presence があるランでは、WAKE の出来事(就寝でない行ごと・presence.py:1252)が `R.wake_from_plan` を呼びます。日課の時刻どおりに起きます。
- 候補の源は 6 つで、就寝中に通す例外は計画の切れ目・会話の番・顕著行為です(judge.py:374-399)。再呼び出しの間隔の値は文書どおりです(state.py:306-318)。
- 変化の検出が出す条件は内受容とセルの 2 つだけです(change_detect.py)。近接の入れ替わり・見られている・傍受の 3 条件は検出しません。
- 世界過程 18 本の順(runner.py:88-110)と、既定で止まる 5 本も文書どおりです。各過程の中身も合っています: 報道 7・12・18 時、宿 21 時・9 時・120 室、催しは記録だけ、バス 6〜23 時・10 分間隔、ごみは 19 時の世帯の消費だけ、補充点 0.95、納品 5〜8 時、顕著行為の抽選は起きない(salient.py:216-228・330-332)。
- absent.py は 26 件です(主体が居ない 8・言い換え 2・口が無い 13・率を外した 2・効果の先が無い 1)。§10-2 の「無い 24」と内訳は一致します。区分の数(既定 38・腕 38・器 14)の内訳の足し算も合っています。
- §11 の 17 件のうち、1〜14 と 17 は書かれた場所にそのとおりの文があり、コードの事実も合っています。17 は `git show 33193c3` の行数(1,688・2,662・1,860)と今の行数(1,701・2,691・1,876)で確かめました。15 は一部違い(#3)、16 は確かめられません(#4)。
- 実測の値は記録と一致しました。60,939 回・4,164 件・166 回・招待 2,218 の帳尻は fix4-1103/README.md:43-54、60.5/61.8 秒・42〜43 ms・520〜527 MB は version-history.md:17 です。この記録のランが CLI の既定と同じ引数であることは、試験が固定しています(test_manifest_rules_bridges.py:173 の w6_v3_default)。v3-0a が 1 バイト不変であることは devlog.md:11・22 にあります。

### can-say で合っていた主な点

- 表の 40 行の印の数は、表と一致します(既定 19・腕 13・器 3・無いと宣言 3・宣言なし 2)。
- 既定とした行(#1・#6〜#13・#15〜#19・#25・#29・#31・#37・#39)は、既定のコードで動きます。
- 腕の行(#2・#3・#20〜#24・#26・#33・#35・#36)は既定 off の切替口です。器の行(#28・#34)は効く口が無く、無いと宣言の行(#5・#14・#27)は absent.py に行があります。
- §2 の表: 1e20cd3 に nav1.py・energy.py・poi_target.py・absent_processes.py が無いことを git で確かめました。9 月のテープは版 1〜2 で、今の版では再生できません(run.py:272-291)。1e20cd3 から 15b6bbd までは 446 commit です。時刻表の違いと「理由を読むコードが無い」は check-3-3.md:65・144 と合います。
- §3 の 5 行は返事その 5 §3-2(prompt-2026-11-04-reply5.md:36-43)と合います。IF-12・VL-20・EX-20・C-01・C-03 も仕様書にあり、状態の記述が合っています。
- 「実 LLM は 9/22 から回していない」は PENDING.md §0 と、devlog-compressed.md:388(最後の実 LLM ランは 09-20・サーバーの利用終了は 09-22)と矛盾しません。
- 外に出す数の出どころ: 345,858 体は version-history.md:11、7 階層は check-3-3.md:187 の記録の値です。data/ は開いていないので、資産の中身そのものは確かめていません。気象が 1 地点であることは w13_weather.py:54(アメダス 1 地点)にあります。

## 3. 確かめた主張の数と所見

確かめた主張は約 220 です(day-flow 約 155・can-say 約 65)。食い違いは 15 件で、内訳は一部違う 11・確かめられない 4 です。「違う」はありません。重さは全部「小」です。

所見:

1. 2 つの文書の芯はコードと合っています。既定で考えるのは mock で、判断モデルは src に無く、LLM は腕です。外に出す文の印にも、外への説明を誤らせる食い違いは見つかりませんでした。
2. ずれは「器」と「腕」の当てはめの細部に集まっています。pricing と credit が完全な空ではない点と、ランの外の道具を「腕」と呼ぶ点です。
3. §11 の一覧には、小さな漏れが 3 件あります(stage2 の天引きの注・報道の到達・change_detect の古い注)。
4. ラン記録が要る主張のうち、C7 と C8 の報告に頼る部分は、開かない約束のため確かめられません。数そのものは docs/bench/c7 と devlog で裏づけられました。

## 4. 作業の注

- リポのファイルは変えていません。commit も push もしていません。最後の `git status --short` は空でした。
- 最初の import のとき、`PYTHONDONTWRITEBYTECODE` を付ける前だったので、`src/**/__pycache__/*.pyc` ができた可能性があります。stubs.py より新しいものが 57 個あり、残りの 155 個はそれ以前からありました。どちらも `.gitignore` の対象で、git の状態は変わりません。消してはいません。
- scratchpad の私の出力ファイル `cli_defaults.txt` は、作業中に別の処理(`dump_cli.py`)に上書きされました。中身は上書きの前に読み終えていました。以後の作業は `/tmp/claude-0/-home-claude/f5fea789-0c80-5ecd-90ec-d611f8ebd2e7/scratchpad/dfcheck/` で行いました。
