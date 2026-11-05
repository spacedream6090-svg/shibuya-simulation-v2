# 仕様書 v0 差の一覧(gaps)

> 位置づけ: [返事その 6](../prompt-2026-11-05-reply6.md) §3-1b の 8 です。仕様書 v0 の各章の項目と今のコードを並べた差の一覧で、あるべき姿の良し悪しと直し方は書きません。
>
> 現状の正はコードです。HEAD `15b6bbd` のコードを、[段 1](../../reference/repo-guide/day-flow.md)、[段 2 のカタログ](../../reference/repo-guide/catalog/)、カード、grep で確かめました。ランと pytest は回していません。封印の層は開いていません。`data/` は置き場とファイルの名前だけを見ました。ルートの README は開いていません。

## 要約

仕様書 v0 の 393 項目を今のコードと 1 項目ずつ比べました。

差のある項目は 281 件です。内訳は、仕組みがまだ無いものが 98 件、あるが仕様と形が違うものが 124 件、既定で off の腕だけのものが 37 件、口や欄だけで既定の結果を変えない器だけのものが 22 件です。このほか、仕様の側が未決の項目が 42 件、現状を確かめられなかった項目が 7 件あります。仕様どおりと読んだ項目は 63 件です。

特に大きな差は次の 10 件です。文書役が選んだもので、影響の大きさを測ったものではありません。

1. 核はまだ事象駆動ではありません。60 秒の刻みで全員と全系を回していて、LLM の返事を世界が待つ透かしもありません(RT-02・RT-13)。
2. 判断モデルがコードにありません。既定のランで考えているのは mock です(MD-22・MD-18)。
3. 心のモジュールがありません。本人の状態、期待、感情、考えかけを持つ部品は無く、主観の関係は器だけです(MD-01・MD-02・MD-06)。
4. 差分の器と判例がありません。語彙の外の行為は「なし」に落ち、「できなかった」は本人に返りません(AC-03・AC-12)。
5. 店主や店長の判断と、制度の旗 3 欄がありません(EO-15・AC-21)。
6. 全域の物理がありません。人はぶつからず、混雑は歩く速さの係数にだけ効きます(WD-22)。
7. 建物の中と駅の中がありません。中に入った体は入口の点に居ます(WD-15・WD-14)。
8. 存在の連続性を満たしていません。体は消えて駅の出口に現れ、出入りと就寝は日課の表どおりにエンジンが実行します(PR-15・WD-29)。
9. 記憶、関係、発話、カレンダー、連絡はどれも腕です。既定のランでは会話に言葉が無く、誰も覚えません(MD-37・SO-07・SO-12・SO-20)。
10. 当たるかどうかの答え合わせがまだありません。門 1 は計画書だけで、全規模の検証のランもありません(VL-19・VL-26)。

題 8 移行の順序が未決なので、「埋める段」の欄の v3-N はすべて R-133 の案です。解釈に迷った所は 38 か所あり、その行に「読みの迷い」と書きました。

## 読み方

1 項目 1 行です。1 つの項目に複数の差があるときは、いちばん大きい差を区分にして、残りを現状の欄に書きました。

| 区分 | 意味 |
|---|---|
| 無い | 仕組みがまだ無い |
| 形が違う | あるが仕様と違う |
| 腕だけ | あるが既定で off(ランの外の道具を含む) |
| 器だけ | 口や欄や道具はあるが、既定のランの結果を変えない |
| 未決 | 仕様の項目の状態が未決 |
| 未確認 | 現状を確かめられなかった |

差なしの項目は表に入れず、章末に ID を並べました。章の項目の「現状との差」の行は、差があれば `→ gaps.md G-番号`、差なしなら `差なし`、未確認なら `未確認(gaps.md)` です。未決の項目にも G-番号を振りました。

- **埋める段**: [R-133](../../research/v2-r133-event-driven-core-design-options.md) §8-3 の段と[仕分けの表](../../reference/behavior-audit-triage-2026-11-04.md)の列から読み取れたものだけ「R-133 の案の v3-N(未決)」と書きました。題 8 移行の順序は未決なので、すべて案です。読み取れないものは「段 未定」で、括弧の中は別の系統の段や題です(空間の段・カレンダーの段など)。
- **仕分けの表の行**: V・K・D・E と行 ID です。親案の区分を機械で照らしました。「割れる」は 11-04c で未決の 9 行です。
- **ファイルの道筋**: `src/shibuya/` を省きました。`tools/`・`tests/`・`docs/`・`data/` はリポの根からです。
- **grep**: その語で検索して当たらなかったという意味で、無いことの証明は検索の範囲までです。
- **読みの迷い**: 仕様の文の解釈で迷った所です。`A-14` のような番号は [`conflicts.md`](conflicts.md)〜[`conflicts.md`](conflicts.md) の食い違いで、仕様の側の問いなので選んでいません。
- **最終形とつなぎ**: 仕様が「最終形は X、つなぎは Y」と書いていて今が Y の項目は、つなぎが宣言どおりでも差ありと読み、「形が違う」にしました。
- **研究待ち**: 仕様の状態が研究待ちの項目も、コードの今で区分を決め、現状の欄に「仕様の状態は研究待ち」と添えました。

## 数の検算(機械で確かめた)

項目の総数 393=差のある行 281+差なし 63+未決 42+未確認 7。数は各章の見出し `#### XX-nn` を機械で引いて数え、章の行の置き換えと同じ表から作りました。

| 章 | 項目 | 無い | 形が違う | 腕だけ | 器だけ | 未決 | 未確認 | 差なし |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 第 0 章 設計の原則 | 31 | 3 | 11 | 1 | 1 | 2 | 3 | 10 |
| 第 1 章 時間と実行 | 34 | 9 | 12 | 1 | 0 | 6 | 0 | 6 |
| 第 2 章 世界 | 51 | 17 | 24 | 0 | 1 | 4 | 0 | 5 |
| 第 3 章 心 | 52 | 22 | 10 | 8 | 7 | 3 | 0 | 2 |
| 第 4 章 差分の器 | 32 | 8 | 11 | 0 | 0 | 11 | 0 | 2 |
| 第 5 章 経済 | 35 | 5 | 17 | 3 | 2 | 1 | 1 | 6 |
| 第 6 章 社会 | 32 | 5 | 7 | 15 | 2 | 3 | 0 | 0 |
| 第 7 章 検証 | 42 | 8 | 11 | 1 | 4 | 4 | 0 | 14 |
| 第 8 章 実験 | 26 | 6 | 5 | 8 | 4 | 1 | 0 | 2 |
| 第 9 章 構築 | 34 | 6 | 12 | 0 | 1 | 1 | 1 | 13 |
| 第 10 章 外への口 | 24 | 9 | 4 | 0 | 0 | 6 | 2 | 3 |
| 計 | 393 | 98 | 124 | 37 | 22 | 42 | 7 | 63 |

## 第 0 章 設計の原則

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-001 | PR-01 目的と順位 | CLAUDE.md §1 は「第一目標=世界そのものがプロダクト」のまま(A-01)。コードに順位の欄は無い。読みの迷い: 文書の順位の項なので差は文書の文で書いた | 形が違う | 段 未定 | — |
| G-002 | PR-02 未来は分布で、反実仮想は差で答える | 分布と差の道は腕 `--experiment`・`--experiment-branch`・`--experiment-model`(`engine/experiment/`)。既定のランは 1 本 | 腕だけ | 段 未定 | — |
| G-003 | PR-03 背骨の文(K2) | 既定の答えは mock(`llm/mock.py`)で判断モデルは src に無い(`engine/decision/ports.py`)。本人の判断であるべき行が規則で動く | 形が違う | R-133 の案の v3-6(未決) | K: 全 43 行(仕分けの表 §1-3) |
| G-004 | PR-04 知見の置き場を 5 つに分ける | 宣言の型はある(`world/processes/records.py` の `InputDecl`・台帳の burned 列)。入力 13 件のうち 7 件は欄だけで、知識の検査 `tools/instruments/leak_check/` は実行前 | 器だけ | 段 未定 | — |
| G-005 | PR-05 錨の量を式に入れない/無いと宣言する/代打の 5 条件 | 率の 5 件は既定で外し `world/processes/absent.py` に宣言。代打の計器は開閉と補充だけで鉄道に無い(`engine/processes/rail.py`)。納品は `engine_stopped=False` | 形が違う | 段 未定 | — |
| G-006 | PR-06 係数で持たない/研究の値は駆動に入れない | 歩きスマホの係数は消した(`perception/facts.py` の注)。裁定の第 1 鍵の 213 ms(`engine/commit.py`)は既定で動く。気づきの d50(`perception/p_notice.py`)は既定で通らず、習慣 0.5(`engine/chooser.py`)は腕 | 形が違う | R-133 の案の v3-6・v3-8(未決) | V: M7・A39 / K: A38 |
| G-007 | PR-07 判断の基準に「現実との整合」の列を足す | 列を守っているかは答申ごとに数えていない。CLAUDE.md と発注の定型 `docs/research/research-order-template.md` に列の行が無いことだけ grep で確かめた | 未確認 | 段 未定 | — |
| G-008 | PR-08 主張の文言「人の行動データによる較正なし」 | 「学習なし」は `docs/design/v2_draft_proposal.md`・`v2_significance.md`・`v2-requirements.md` に無い(grep)。ルートの README は発注どおり開いていない。LoRA の本線のコードは無い | 未確認 | 段 未定 | — |
| G-009 | PR-09 共有の心・場所の環境・少数の較正(「ゼロショット」の言い直し) | 場所ごとの較正の係数の台帳と G2 の仕組みは無い(grep)。天神は材料の置き場だけ(`data/tenjin/` の名)。被験者の国の列はパターン台帳にある。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-010 | PR-12 人の手続きはコードに書かない(D1〜D6) | 語彙 12 語を固定の並びで B0 に見せ(`perception/templates.py`)、失敗の直後に「いま可能」を付ける(`perception/renderer.py`)。語彙外は「なし」へ落とす(`llm/undefined.py`) | 形が違う | R-133 の案の v3-6(未決) | D: A11・A27・A29 |
| G-011 | PR-13 世界の変化の起こり方(CP6)と組織の扱い | 世界過程 18 本の多くをエンジンの規則と代打が動かす(`engine/processes/`)。`executor=llm_agent` の 9 行は既定で人の判断でない。組織は権利台帳で表す(`engine/rights/`) | 形が違う | 段 未定 | E: S26 |
| G-012 | PR-14 組織の判断は体が渋谷に居る人が下す(A2 の線) | 店主・店長の判断の口と制度の旗 3 欄は無い。腕 `--duties arm` の開閉・補充・廃棄だけ(`engine/duties/`) | 無い | 段 未定(v3 の核の後=11-02r/§3) | — |
| G-013 | PR-15 存在の連続性 | 退出で舞台の外へ即時に移り、到着で駅の出口のセルに現れる(`engine/presence.py`)。範囲の外の位置は持たない | 形が違う | 段 未定(カレンダーの段 1b) | E: M23 / D: M13 |
| G-014 | PR-16 憲法 6 原則(決定台帳 §3a の写し) | 憲法 1 の「全員が常に考える」に対し、舞台の外と車内の体は例外なく見送る(`engine/arbiter.py`)。読みの迷い: A-03 と 9-4 の関係は仕様の側でも直っていない | 形が違う | 段 未定 | D: M13・S52 |
| G-015 | PR-17 作り方の姿勢 | 姿勢の項で、守られているかの物差しがコードに無い。土台の部品(出来事の記録・権利台帳・候補の口・規則の表・道具の台帳)はカタログ C のとおりある | 未確認 | 段 未定 | — |
| G-016 | PR-26 版上げの運用と外に出す主張の門 | 版上げの履歴は `docs/ops/version-history.md` にある。旧道の切替口 10 本が残る(段 1 §10) | 形が違う | 段 未定(11-05/§3-2) | — |
| G-017 | PR-27 包みの分け方の原則(題 10・案 B) | 今の包みは `agents`・`build`・`core`・`economy`・`engine`・`llm`・`manifest`・`perception`・`world` ほか(`src/shibuya/`)。11 の包みは無い。層の契約は import-linter 5 本 | 形が違う | 段 未定(題 10) | — |
| G-018 | PR-28 ファイルの割り当てと原則の穴 3 点 | 35 万体の状態は 1 つの SoA(`agents/state.py`)。書く口は `engine/resolve.py`。関係と約束は腕の層 | 未決 | 段 未定(題 10) | — |
| G-019 | PR-29 物の実体化(研究の題として積む) | 物を実体で持つ層は無い。仕様の状態は研究待ち | 無い | 段 未定(構築の段で後に壁打ち) | — |
| G-020 | PR-30 U2「できる限りすべて思考ブロックに」と判断の置き場の関係 | 語彙 v3 は 12 語で消費の 4 判断点は無い(`llm/contract.py`)。判断の行き先の決定は台帳の `DEC-*` の行 | 形が違う | 段 未定(11-01p 段 3 の 3-1) | — |
| G-021 | PR-31 マルチモーダルなエージェント(今は決めない) | 知覚の事実と描画は分かれた(`perception/facts.py`)。体の形の欄は無い | 未決 | 段 未定 | — |

差なし(項目 ID): PR-10・PR-11・PR-18・PR-19・PR-20・PR-21・PR-22・PR-23・PR-24・PR-25

差なしと読んだ根拠は次のとおりです。

- PR-10 3 つの区別・自由の 3 種・世界の地図: 用語集 `docs/design/v2-glossary.md` に 3 つの区別・自由の 3 種・世界の分け方の行がある。仕様の状態は研究待ち
- PR-11 厳密な世界・曖昧な頭(憲法ではなく参考の考え): 知覚は語の段階で描く(`perception/templates.py`)・世界は数値。読みの迷い: 「迷ったときに参照する考え」で規則ではないので、数値を見せる行(A12 ほか)は差に数えなかった
- PR-18 車輪の再発明をしない: CLAUDE.md §2-4 に規則の文がある。各草案の比較表の全数は数えていない
- PR-19 計算量と資源の扱い: CLAUDE.md §4 に規則の文がある・性能予算の計器は `core/budget.py`
- PR-20 ミクロよりマクロ: 合成人口で住人は特定の人と対応しない(`build/pop/`)
- PR-21 実データを優先し、検証専用のデータを事前に決める: パターン台帳 §10・`tools/instruments/read_guard.py`・W19 の静的ゲート(`build/audit/w19_freeze.py`)
- PR-22 現実の法と制度に基づく: `docs/design/rules-table.json` は machine 16 行・human 14 行・最低賃金は human で `params.bridge` のつなぎ(`engine/rules/table.py`)
- PR-23 データは無料か申請で得られるものだけ: CLAUDE.md §7 に規則の文がある
- PR-24 段ごとに詳細まで決めてから実装する: CLAUDE.md §2-2 の文を 11-05 §1 の文と照らした
- PR-25 最優先は作り込み、当たるかの輪を早く 1 周させる: 順は決定の文(`docs/design/prompt-2026-11-05-reply6.md` §6)のとおりで、コードに現れない

## 第 1 章 時間と実行

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-022 | RT-01 世界の時刻はナノ秒で持ち、刻みは実装の都合 | 通しの時刻は刻みから計算する(`core/types.py` の `t_sim_ns`=刻み × 幅)。世界の時刻は刻みでしか進まない。届く 18 か所の鍵だけ t_ns 経由 | 形が違う | R-133 の案の v3-0(未決) | V: A68・A69 |
| G-023 | RT-02 核を事象駆動に替える(v3) | 新しい核と切替口 `--core` は無い(grep)。進行役は幅 60 秒の刻みの事象 1 種で全系を回す(`engine/systems/conductor.py`・`engine/batching.py`) | 無い | R-133 の案の v3-0〜v3-9(未決) | V: A09・B6 ほか(§1-4 の段の表) |
| G-024 | RT-03 題 1 目盛り (G2) | 窓の幅は既定 60 秒(`--batch-width-s`)で事象の粒度も 60 秒(`engine/batching.py`・台帳 `DOC-tm32-event-time-60s`) | 形が違う | R-133 の案の v3-0(未決) | — |
| G-025 | RT-04 題 2 列の構造 (Q3) | `next_t_ns`・`next_kind` の欄は試作 `tools/bench/event_cost/` だけで src に無い(grep) | 無い | R-133 の案の v3-0(未決) | — |
| G-026 | RT-05 同時刻の鍵と乱数の鍵 | 届く 18 か所の鍵は t_ns から作る(`core/rng.py`)。約 27 か所は刻みの番号のまま。同順は割り当ての lexsort(`engine/arbiter.py`) | 形が違う | R-133 の案の v3-0(未決) | V: A52・A53・A54・A55・A67・S39 |
| G-027 | RT-06 ハッシュが裁いた回数を計器にする | 同点の計器は近くの人の同点だけ(`perception/renderer.py` の `near_tie_breaks`)。事象の鍵の同点は数えない | 無い | R-133 の案の v3-0(未決) | — |
| G-028 | RT-07 事象の型 | 世界の事象は刻みの事象だけ(`engine/batching.py`)。足す 5 つの型は無い | 無い | R-133 の案の v3-0(未決) | — |
| G-029 | RT-08 世界は 1 つの時計で動く(区域ごとの列は採らない) | 既定は 1 つの時計(`--clock global`)。腕 `--clock regional`(`engine/regional_clock.py`)が残る | 形が違う | 段 未定 | — |
| G-030 | RT-09 「秒の中で順を持たない」種類の宣言の表 | v3 の設計書 §2 の表は未記入 | 未決 | 段 未定 | — |
| G-031 | RT-10 題 3 活性の境目 | 全員を毎刻み見る(`engine/change_detect.py`)。腕 `--step-scope changed` | 未決 | R-133 の案の v3-5(未決) | — |
| G-032 | RT-11 題 4 予定/反応の判断と先読み | 日課の切れ目と変化の検出で呼ぶ(`engine/systems/judge.py`) | 未決 | R-133 の案の v3-6(未決) | V: A73 |
| G-033 | RT-12 題 5 会話の時間線 | 会話は 1 刻み 1 発話。腕 `--talk-clock mora` は計器だけ(`engine/speech_clock.py`) | 未決 | R-133 の案の v3-7(未決) | V: B6 |
| G-034 | RT-13 題 6 (W1) 完全な透かし・遅れを許さない | 答えは `max(発射の刻み+考える時間, 届いた刻み)` に適用し世界は待たない(`llm/fleet.py`・`engine/systems/llm_io.py`・`--fleet-wait-s` 既定 0) | 形が違う | R-133 の案の v3-2(未決) | V: A09・A26・S21・S31 |
| G-035 | RT-14 考えた時間=最短からトークンで延ばす (P9) | 考える時間はレーンの固定値を刻みへ切り上げる(`engine/llm_bridge.py`)。返事のトークンで効く時刻を延ばす道は無い | 無い | R-133 の案の v3-2(未決) | V: A09 |
| G-036 | RT-15 レーンの表(考える時間の最短) | `LANE_SECONDS` の値は仕様と同じ。使うのは L1 だけで 60 秒の刻みへ切り上げる。L2〜L4 は `run_day(lane=)` の引数だけ。仕様の状態は研究待ち | 形が違う | R-133 の案の v3-2(未決) | V: A09 |
| G-037 | RT-16 固まりの上限は壁時計 30 分 | 壁時計の上限で止めて保存する道は無い(grep)。`--fleet-wait-s` は別の意味 | 無い | R-133 の案の v3-2(未決) | — |
| G-038 | RT-19 待つ時間を縮めるのは推論の口の側 | `llm/fleet.py` に優先度の口は無い(grep priority) | 無い | 段 未定 | — |
| G-039 | RT-20 題 9-4 L4 の予算 (b)+(d) | CLI の既定は呼数の上限なし(`--l4-scale 0`)。按分の腕は `engine/arbiter.py` に残る。ランを止める呼数か費用の上限は無い(grep) | 形が違う | 段 未定 | D: S27・S28・S29 |
| G-040 | RT-21 arbiter は消える | `engine/arbiter.py` が見送り・間隔・優先上げ・簡略応答を持つ | 形が違う | R-133 の案の v3-6(未決) | V: S30・A04(割れる) |
| G-041 | RT-22 体の変化は越える時刻を予約する(TM5) | `--body-schedule reserve`(`engine/body/schedule.py`)。既定は全員を見る sweep | 腕だけ | R-133 の案の v3-3(未決) | — |
| G-042 | RT-23 runtime と心の境 | mind と runtime の包みは無い。答えた層の記録 `layer_counts` は mock も層 2 に数え(`engine/systems/build.py`)、なぜ上げたかの欄は無い | 形が違う | 段 未定(題 9・題 10) | — |
| G-043 | RT-24 題 7 テープ | 応答の記録は版 4・21 列(`engine/tape.py`)。腕 `--tape`。出来事の記録はファイルに書かない | 未決 | 段 未定(題 7) | — |
| G-044 | RT-25 活性はランで残さず再計算する(T1) | 活性を残す道は無く、向きは同じ。組み直しの試験はある(`tests/engine/test_version_bump_10e.py`)。トークナイザの版の欄は無い(grep) | 形が違う | 段 未定(題 7) | — |
| G-045 | RT-26 W17・W12 の分の表を秒に直す段 | W17 は分、W12 は発車の分のまま(`agents/weekly.py`・`build/field/w12_external_nodes.py`) | 無い | R-133 の案の v3-1 の前の分→秒の段(未決) | V: A47・A68 |
| G-046 | RT-27 決定論は用途で分ける | エンジンは決定論(`core/rng.py`)。LLM の記録は腕で、`--mode` は smoke ほかで厳密モードの欄は無い(`engine/run.py`)。読みの迷い: C-10 は仕様の側の問い | 形が違う | 段 未定 | — |
| G-047 | RT-29 版の固定・ランの記録・計測の分離 | manifest は版とハッシュを持つ(`engine/run.py`)。種類は再現・反実仮想・腕・試験(`engine/run_kind.py`)で仕様の 4 つと違う。円/シミュ日の計器と呼数の分けは無い | 形が違う | 段 未定 | — |
| G-048 | RT-30 題 8 移行の順序 | 切替口 `--core` は無く、刻みの数の定数は `core/time_consts.py` ほかにある | 未決 | 段 未定(題 8) | — |
| G-049 | RT-32 物理の計算は CPU | 物理の層が無い(WD-22)。LLM のクライアントは同じプロセスのスレッド(`llm/fleet.py`)・`multiprocessing` は src に無い(grep)。numba のカーネルはある(`engine/space/nav1.py`) | 無い | 段 未定(空間の段 5) | — |

差なし(項目 ID): RT-17・RT-18・RT-28・RT-31・RT-33・RT-34

差なしと読んだ根拠は次のとおりです。

- RT-17 (W2) 依存を見て遠くを先に進める: 透かしの道が src に無く、作らない決定のまま(grep)
- RT-18 (W3) 遅れを許す形は腕にも残さない: 遅れを許す形が今の核に残り、腕の切替口は無い。読みの迷い: 「旧道として切り替えまで残る」の文を今の差なしと読んだ
- RT-28 再開: `tests/engine/test_resume_10d.py`=日中 3 点と日の境目で一致・未着の呼の出し直し・お金が湧かない。固まりの上限の再開は RT-16 に数えた
- RT-31 v3-0a 案 A: `core/rng.py` の `key_time_from_t_ns`・`DecisionPort.time_key_at`(#139)
- RT-33 推論の艦隊の安全の規則: `tools/night5070/night_run.py` の検査(127.0.0.1・safetensors・API key・trust_remote_code なし・WSLENV)と `register_task.py` の LeastPrivilege。pip の版と重みの出どころは `experiments.json` の注までしか確かめていない
- RT-34 暦: `engine/calendar.py` の `SimCalendar`・manifest の `calendar` と `start_sim_datetime`(`engine/run.py`)・`input.calendar`

## 第 2 章 世界

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-050 | WD-01 世界に置くものの線 | 体・持ち物・金・位置の欄が心の欄と同じ SoA にある(`agents/state.py`)。関係と約束は腕の層 | 形が違う | 段 未定(題 9-1・題 10) | V: S17 |
| G-051 | WD-02 世界の変化の起こり方と例外 | 鉄道・開閉・補充・ホテルはエンジンの規則か代打(`engine/processes/`)。体は日課の表で出入りする(`engine/presence.py`)。規則の conf は台帳の欄にある(`world/processes/first_batch.py`) | 形が違う | 段 未定 | — |
| G-052 | WD-03 エンジンが代わりに決めている処理の 3 群 | ① は規則のまま(K の行)。② は代打か腕 `--duties arm`。③ はコード(`engine/body/`・`engine/change_detect.py`) | 形が違う | R-133 の案の v3-6(未決) | K: 全 43 行 |
| G-053 | WD-07 音の伝わり方と騒音の場 | 声の式は無い。騒音は W10 の静的な昼夜の段(`build/field/w10_noise.py`・`world/assets.py`)。`engine/body/system1.py` のロンバード効果は値が空 | 無い | 段 未定(空間の段 3・車の段) | E: A49(割れる)・S4 |
| G-054 | WD-08 見え方の世界の側(何があるか) | 見通しは W8 のセル単位の静的な表(`build/vis/w8_visibility.py`)。向きと視線の通り道は見ない。上位を選ぶのは描画(`perception/renderer.py`) | 形が違う | 段 未定(題 9-1・空間の段 3) | V: A05・A06・A10・A33 |
| G-055 | WD-09 入力(境界の外から一方向に流れるもの) | `world/processes/inputs.py` の 13 件=値のある 5 件+欄だけ 7 件+納品の欄。読みの迷い: B-04 は仕様の側の問い | 器だけ | 段 未定 | — |
| G-056 | WD-10 位置とセルの廃止 | 位置は `r.xy` と `nav_fi` で持つが、100 m のセルと `node` が残り店の成立もセルで見る(`engine/resolve.py`・`world/state.py`)。近傍の索引は 2.5 m の格子(`engine/spatial_index.py`) | 形が違う | 段 未定(空間の段 2〜3) | — |
| G-057 | WD-11 ナビメッシュと移動 | つなぎの nav1 が既定(`engine/space/nav1.py`)。物理が xy を動かす最終形と、提供者を差し替える型の口は無い(grep) | 形が違う | 段 未定(空間の段 5) | V: S47 |
| G-058 | WD-12 経路の重みと経路の選び方 | 既定の重みは仕様の値(50 m・3.8 m)。本人が選ぶ口は器(`world/navmesh_route.py` の `candidates`)。知っている道の制限は無い | 形が違う | R-133 の案の v3-6(未決) | K: M19・S43 |
| G-059 | WD-13 3 次元と上下の接続口 | 接続口の時間と容量はある(`engine/space/nav1.py`)。向きと時間帯の欄は見つからない(grep)。建物の中の縦移動・ES の歩くか立つか・かごを動かす形は無い | 形が違う | 段 未定(空間の段 2・段 5) | V: B7・S38・S39 / E: S40・S41・S42 |
| G-060 | WD-14 駅の中 | 駅の中は入口の点(`engine/space/nav1.py` の注「駅の中は段 4」)。W11 は出口だけ(`build/geo/w11_station_exits.py`) | 無い | 段 未定(空間の段 4) | — |
| G-061 | WD-15 建物の中 | 建物の中は入口の点(同じ注「建物の中は段 2」)。読みの迷い: B-06 の入れ子と MR14 の関係は仕様の側の問い | 無い | 段 未定(空間の段 2) | — |
| G-062 | WD-16 家具と持ち物は形を持つ | 持ち物は個数の `holdings` だけ(`engine/resolve.py`)。家具は無い | 無い | 段 未定 | E: S13 |
| G-063 | WD-17 店の存在と階 | 店は OSM v8 の POI 2,337(`build/geo/w6_poi_org.py`)。出どころの強さの規則・閉店の判定・見逃しの計測は無い(grep) | 形が違う | 段 未定(空間の段 2) | — |
| G-064 | WD-18 入口 | 実入口優先と重心の射影の印はある(`build/geo/w5_entrances.py`=駅 45・建物 16 棟)。歩行空間の出入口と地下街の扉は読まない。入口を本人が選ぶ口は無い | 形が違う | 段 未定(空間の段 2) | — |
| G-065 | WD-19 容量の 3 種類と席 | 席=想定床面積 ÷ 1 席の面積(`engine/processes/crowd.py`)・受け入れ 4 人(`engine/commit.py`)。3 種類の分けと消防法の算定は無い。30 刻みと 15 刻みは規則 | 形が違う | R-133 の案の v3-6・v3-8(未決) | K: B2・M1・M2・S7・F2 / E: M6・M11 / V: B1 |
| G-066 | WD-20 行動の成立は「その場所の中にいる」 | 成立は店と同じセルか(`engine/resolve.py` の `_apply_buy`)。就寝は自宅のセルかホテルだけ。場所の使い方で寝る口は無い | 形が違う | R-133 の案の v3-6(未決) | K: M17・A35 |
| G-067 | WD-21 物理的に不可能な行動を防ぐ試験 | 速さの上限の試験は nav1 の移動だけ(`tests/engine/space/test_nav1_units.py`)。同じ刻みの退出と到着の瞬間移動は既知の穴(`engine/presence.py`) | 形が違う | 段 未定(空間の段) | E: M23 |
| G-068 | WD-22 全域の物理(D 層) | 人は衝突しない(`engine/space/nav1.py`・台帳 `BR-NAV1-E2`)。`engine/body/system1.py` の `crowd_gait` は値が空 | 無い | 段 未定(空間の段 5) | E: M21 |
| G-069 | WD-23 空間の段の順 | 段 1 は既定(#126)で段 0 は取得の残りあり。段 2〜6 は未着手(PENDING §2 の 11)。読みの迷い: 計画の順の項なので差を段の進み具合で書いた | 無い | 段 未定(題 8) | — |
| G-070 | WD-24 地名帳と場所の言い方 | 地名帳の表は無い。calendar2 の注に語があるだけ(`engine/calendar2/book.py`)。行き先は対象の語の読み(`engine/poi_target.py`) | 無い | 段 未定(空間の段 3) | K: A23 |
| G-071 | WD-25 店と会社の名前 | 公表物の架空名の段は無い(grep は `tools/instruments/leak_check/` の問いだけ)。比較の腕も無い。POI の実名をそのまま描く | 無い | 段 未定 | — |
| G-072 | WD-26 4 層(空間・制度・人口と事業所・運行) | 規則の表に管轄の欄が無い(grep 0 件)。全国の材料だけで組む口も無い | 無い | 段 未定 | — |
| G-073 | WD-27 境界とグラデーション | `transit_state` の 3 値だけで輪と遠くの段が無い(`engine/presence.py`)。`build/pop/w21_outside.py` の輪と遠くは層の表で体が無い | 形が違う | 段 未定(題 3) | D: M13・S52 |
| G-074 | WD-28 電車の通過客 | 枠の行 `transfer_only`・`through_jr` は体を作らない(`build/pop/w21_outside.py`)。読みの迷い: B-08 は仕様の側の問い | 無い | 段 未定 | — |
| G-075 | WD-29 存在の連続と出入り | `--exit-mode immediate` で消えて駅の出口に現れる(`engine/presence.py`)。W17 の出入りと就寝をエンジンが実行(台帳 `BR-W17-IO-SLEEP`)。腕 `--calendar 1b` | 形が違う | 段 未定(カレンダーの段 1b) | E: M23・S20 / K: M26・S19・F4 |
| G-076 | WD-30 鉄道の運行 | 代打で時刻表どおり(`engine/processes/rail.py`・conf 0.6)。④ の代打の計器は無い(grep)。運転士と指令の口は無い | 形が違う | 段 未定 | — |
| G-077 | WD-31 ダイヤの実データ | 実ダイヤは構築済み(`build/field/w12_real_timetables.py`)で銀座線の版も宣言あり。井の頭線の公開枠の確認は未(PENDING §2 の 13) | 形が違う | 段 未定 | — |
| G-078 | WD-32 車両は動く場所と乗車の上限 | 便ごとの人数と 200% の上限(`engine/processes/rail.py`)。車内の場所・ドア・座席は無い。定員の更新は未。読みの迷い: B-01 の上限の文は 2 つ | 形が違う | 段 未定(空間の段 4) | E: S51 / K: M4 |
| G-079 | WD-33 遅れと運行情報 | 遅れは作らない(仕様どおり)。`input.service_disruption` は欄だけ。既定の到着は「間に合う最も遅い便」を選ぶ(`engine/presence.py`)=しないことの 1 つ。腕 1b は守る(`engine/calendar_self.py`) | 形が違う | 段 未定(カレンダーの段 1b) | — |
| G-080 | WD-34 鉄道の秒の段 | 時刻表の分で発車を比べる(`engine/processes/rail.py`)。`engine/processes/rail_events.py` は器 | 未決 | R-133 の案の v3-4(未決) | — |
| G-081 | WD-35 車 | 断面の台数の集計だけ(`engine/processes/traffic.py`)。運転者の体と信号の処理は無い(grep)。`input.through_traffic` は欄だけ。読みの迷い: B-05 の文が 2 つ | 無い | 段 未定(空間の段 6) | — |
| G-082 | WD-36 バス | `engine/processes/logistics.py` は到着の記録だけで乗り降りなし。運転士の体の有無は未確認 | 未決 | 段 未定 | — |
| G-083 | WD-37 体は世界の側 | 体の層はある(`engine/body/`)。値は自前(台帳 `BR-BODY-NATURAL-VARIATION`)で研究の値でない。段の予約は腕 | 形が違う | R-133 の案の v3-3(未決)・値は題 B8 | V: A13・A14 |
| G-084 | WD-38 空腹とエネルギー | 消費の式はある(`engine/energy.py`)。満腹とふつうを描くのは腕 `--hunger-words all`。旧道 `--hunger-model v1` が残る。駆動源の置き換えは未 | 形が違う | 段 未定(腕の既定化) | V: A13 / D: S15 |
| G-085 | WD-39 食事の時刻と範囲の外の食事 | 舞台の外は自動で食べ、既定の時刻は窓の中(`engine/energy.py`)。摂取は時間帯の比。量を本人が選ぶ口は無い | 形が違う | 段 未定 | D: S1 |
| G-086 | WD-40 疲れ | 30 刻みごとに +1 ほかの自前の値(`engine/body/rules.py`)。坂と階段と距離は入らない。仕様の状態は研究待ち | 形が違う | 段 未定(題 B8) | D: A12・S14 |
| G-087 | WD-41 暑さ・熱中症・倒れる | 熱中症の体の式は無い。`absent.collapse` の宣言はある。WBGT は暑さの段まで(`engine/solar.py`)。仕様の状態は研究待ち | 無い | 段 未定(題 B8) | E: S18 |
| G-088 | WD-43 体の寸法と押す力 | 寸法の欄は無い。W21 の空欄 `body_and_senses`・`mobility_aid`・`voice_level`(`build/pop/w21_persona.py`)。仕様の状態は研究待ち | 無い | 段 未定(題 B8) | — |
| G-089 | WD-44 題 B8(体の設計) | 体の層の口は `engine/body/`。題 B8 の壁打ちは未 | 未決 | 段 未定(核の後=記録 §3) | — |
| G-090 | WD-45 考えながらの費用の宣言 | `world/processes/absent.py` に 2 行とも無い(段 1 §11 の #15) | 無い | 段 未定 | — |
| G-091 | WD-46 見た目の欄 | 見た目の欄は無い(`perception/facts.py`)。`watched_by` は空の欄 | 無い | 段 未定(題 9-1) | V: A07(割れる) |
| G-092 | WD-47 持ち物と体の属性の持ち方 | 持ち物の台帳は無い(`Percept.belongings` は空)。道具の状態は腕 c1(`engine/contact/device.py`)。W21 の持ち物の欄は空欄 | 無い | 段 未定 | — |
| G-093 | WD-48 言語の知覚 | `first_language` は W21 の表だけで、エンジンと知覚は読まない(grep) | 無い | 段 未定 | — |
| G-094 | WD-49 割れる行(世界に関わるもの) | A48 は `perception/renderer.py`、A49 は同じファイルの 6〜22 時、S46 は `engine/space/nav1.py`、S50 は `engine/processes/crowd.py` | 未決 | 段 未定 | E: A48・A49(割れる)/ D: S46・S50(割れる) |
| G-095 | WD-51 式として残す行と expedient の印 | E 29 行の表はある。直す対象の M23・M27・S12・S13 はコードに残る(`engine/resolve.py`) | 形が違う | R-133 の案の v3-1・v3-8(未決) | E: M23・M27・S12・S13・A50・M6・S20・S23・S24・S53 |

差なし(項目 ID): WD-04・WD-05・WD-06・WD-42・WD-50

差なしと読んだ根拠は次のとおりです。

- WD-04 世界過程・計画仕様・実績ログ: `world/processes/` の `records.py`・`registry.py`・`relations.py`・`actual_log.py`・`core/growth.py`。読みの迷い: 「第 1 級は自然過程だけ」に対し engine_rule と llm_agent の行が台帳に載る。つなぎの宣言と読んだ
- WD-05 憲法 5 の確定文(届き先か寄与の宣言): `world/processes/constitution.py` の `check_constitution5` が起動時に走る
- WD-06 天気と太陽: `engine/processes/environment.py` の `sample_calendar_day`(型は日数の割合で引く)・`engine/solar.py`・既定 2026-07-13(仕分け A48(E・割れる)は WD-49)
- WD-42 歩く速さと混雑の中の歩き方: `engine/space/nav1.py`・`engine/geometry.py` の U(1.00,1.60)× Kladek。避け方は未決で衝突なし。expedient の印は仕分けの表の注(仕分け E: M20・M21・S44・S45・A24・A63・A71)
- WD-50 無いと宣言する世界の過程: `world/processes/absent.py`・`engine/absent_processes.py`(5 件 stopped)・`tools/instruments/absent_declarations.py`

## 第 3 章 心

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-096 | MD-01 心は 1 つのモジュール | 変化の検出・割り当て・判断の口・描画が別の部品で、系の順に呼ぶ(`engine/change_detect.py`・`engine/arbiter.py`・`engine/decision/`・`perception/`)。1 つのモジュールは無い | 形が違う | 段 未定(題 9) | — |
| G-097 | MD-02 題 9-1 心の内と外 | 状態ベクトル・自伝・期待・感情・考えかけは無い。本人の文は器。記憶と予定は腕。体と金が心の欄と同じ SoA(`agents/state.py`) | 形が違う | 段 未定(題 9-1) | V: 題 9-1 の 27 行(§1-4) |
| G-098 | MD-03 知覚は 2 段に分ける | 事実 `Percept` と描画は分かれた(`perception/facts.py`・`renderer.py`)。何に気づくかの選びは描画の部品にある | 形が違う | 段 未定(題 9-1) | V: A05・A06・A10・A15・A33・A43・A44・A45・A46・A51・M22・S2・S3・S48・S49 / D: A36・A59・A60 |
| G-099 | MD-04 他人から見えるものは見た目の欄だけ | 見た目の欄は無い(WD-46)。種別の語は B1 の文(`perception/templates.py`) | 無い | 段 未定(題 9-1) | V: A07(割れる) |
| G-100 | MD-05 本人の知識の線 | `tools/instruments/leak_check/` は実行前(PENDING §2 の 18)。B0 の役割知識は全員同じ。読みの迷い: A-04 の「知識」の二義は仕様の側の問い | 器だけ | 段 未定 | V: A61 |
| G-101 | MD-06 主観の関係を 3 つに分ける | ① は `engine/memory_impression.py`(呼び手なし)と腕の関係 `engine/relations.py`。② と ③ は無い。読みの迷い: A-05 | 器だけ | 段 未定 | V: S17 |
| G-102 | MD-07 BIAS map は錨、偏りは消さずに測る | BIAS map の錨と不平等の軸の計器は無い(grep)。`tools/instruments/dm_eval/bias.py` は候補の位置の偏りの計器で別物 | 無い | 段 未定 | — |
| G-103 | MD-08 本人の状態ベクトル(性格と気分) | 本人のベクトルは無い。LoRA も操舵も src に無い(grep)。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-104 | MD-09 感情 | 価と覚醒度の欄は無い(grep の valence は店の評価の欄)。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-105 | MD-10 期待(本人の世界モデル) | `Percept.prediction` と判断の口の驚きの欄は空(`perception/facts.py`・`engine/decision/port.py`)。`absent.plan_fix_surprise`。仕様の状態は研究待ち | 器だけ | 段 未定 | D: A62 |
| G-106 | MD-11 目標と予定 | 既定は W17 で勤務の行を実行しない。本人の行は腕 `--calendar-2 arm`(`engine/calendar2/book.py`)と `--calendar 1b`(`engine/calendar_self.py`) | 腕だけ | R-133 の案の v3-6(未決) | K: M26・A40・A41 |
| G-107 | MD-12 本人(ペルソナ) | 人物の文は W21 段 9(`build/pop/w21_persona.py`)で事実から組む・TIPI の欄は空・生い立ちは「使わない」の版。読み口 `engine/decision/persona.py` は呼び手なし。仕様の状態は研究待ち | 器だけ | 段 未定 | V: A07(割れる) |
| G-108 | MD-13 自伝の要約と睡眠中の処理 | 自伝と寝たときの書き直しの処理は無い(grep)。`absent.reflect_day`。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-109 | MD-14 題 9-2 の方針 | `engine/decision/port.py` は候補から選ぶ口で、保存・復元・アイドルの一歩の口は無い | 無い | 段 未定(題 9-2) | — |
| G-110 | MD-15 題 9-2 の細部(読むもの・取り出すもの・出力の方式) | 今の読みは `llm/parser.py`・`llm/undefined.py` | 未決 | 段 未定(題 9-2) | D: A27・A28・A64・A65・A66・M25 |
| G-111 | MD-16 行為の鎖 | 応答の記録は呼びごとの行で、鎖の欄は無い(`engine/tape.py`・grep) | 無い | 段 未定(題 7・題 9-2) | — |
| G-112 | MD-17 A2-1 判例の穴を埋めるのは誰か | 判例の穴は無い。行き先と相手は `engine/commit.py` が規則で補う | 無い | 段 未定(v3 の核の後) | K: A02・B3・B8 |
| G-113 | MD-18 題 9-3a 案 D | mock は語彙から一様に引く。判断モデルと迷いの欄は空(`engine/decision/port.py`)。`absent.deliberate` | 無い | R-133 の案の v3-6(未決) | — |
| G-114 | MD-19 連続して動く土台は System 1 | 土台はコード(`engine/change_detect.py`・`engine/arbiter.py`)で毎刻み全員を見る。判断モデルを呼ぶ道と学習の土台は無い。読みの迷い: A-06 | 形が違う | R-133 の案の v3-5(未決) | V: A14 |
| G-115 | MD-20 熟考の間も今の行動は続く | 歩く途中で呼ばれた刻みは進まない(`engine/resolve.py`)。仮に始める道と操作ごとの性質は無い | 形が違う | R-133 の案の v3-8(未決) | V: B4・S47 |
| G-116 | MD-21 型の表=判断の置き場 112 件 | 行き先の表は `docs/reference/decision-routing-2026-11-01.md`。判断モデルの担当は 0 件(`engine/decision/ports.py`)。口の無い 13 件は `absent.py` に宣言 | 形が違う | R-133 の案の v3-6(未決) | K: 全 43 行 |
| G-117 | MD-22 判断モデル 第 1 世代 | src に無い。評価の器は `tools/instruments/dm_eval/`(340 場面)で Clef ほかは口だけ。迷いの較正の列は無い(grep) | 無い | R-133 の案の v3-6(未決) | — |
| G-118 | MD-23 判断モデル 第 2 世代 | src に無い。仕様の状態は研究待ちで今は着手しない | 無い | 段 未定 | — |
| G-119 | MD-24 System 1 の学習のデータ(第 2 世代) | 学習の道は無い。応答の記録は腕 | 無い | 段 未定 | — |
| G-120 | MD-25 候補の作り方と状況の渡し方 | 5 つの源は腕 `--decision-port port`(`engine/decision/sources.py`・`port.py`)。LLM サーバー群の道は通らない | 腕だけ | R-133 の案の v3-6(未決) | V: A34・A55・A57 / D: A29・A56 |
| G-121 | MD-26 題 9-3b 熟考へ上げる引き金 | 4 つの引き金も計器も無い(grep)。全部の呼びが L1 | 無い | 段 未定(題 9-3b) | — |
| G-122 | MD-27 動機と労力・本人の認知の容量 | 該当の部品は無い | 未決 | 段 未定(題 4) | — |
| G-123 | MD-28 「よく考える」の候補と深さ | 候補には載るが、選ばれても上の層を呼ぶ道が無い(`engine/decision/sources.py`)。`absent.deliberate`。読みの迷い: A-11 | 器だけ | 段 未定(題 9-3) | — |
| G-124 | MD-29 普段は溜めて区切りで見る | 溜める形は無く、条件ごとの再呼び出しの間隔 11 行で絞る(`agents/state.py`・`engine/arbiter.py`)。読みの迷い: A-14 | 形が違う | 段 未定(題 9-3) | V: A04(割れる)・A26・S16 / K: A16 |
| G-125 | MD-30 System 1 は物理として届いたかだけを決める | 段とセルの欄の変化でセルの全員を候補にする(`engine/change_detect.py`)。物理として届いたかの判定は無い。`perception/p_notice.py` は既定で通らない | 形が違う | R-133 の案の v3-5(未決) | V: A03・A14・A39・M12 / D: A25 |
| G-126 | MD-31 途中までの考えに知覚として足す | 途中の考えに足す道も、切る道も無い(grep) | 無い | 段 未定(題 9-3c・題 9-2) | — |
| G-127 | MD-32 会話の相手の言葉は常に届く | 言葉は腕 `--speech-port on`(`engine/speech/port.py`)で参加者に届く。既定は言葉なし | 腕だけ | 段 未定(GPU の後の版上げ) | — |
| G-128 | MD-34 題 9-3d 考えながらの費用 (D4) | 門が無いので気づきの遅れも無い。`absent.py` に 2 行とも無い(段 1 §11 の #15) | 無い | 段 未定 | — |
| G-129 | MD-35 新しい題「心と体の接続」 | 接続の口は無い。`engine/body/` は速さに影響しない。仕様の状態は研究待ち | 無い | 段 未定(題 B8) | — |
| G-130 | MD-36 題 9-5 考えかけの扱い | 考えかけは無い。返事待ちの体にもう 1 本送る穴がある(台帳 `DOC-fleet-resend-while-waiting`)。`absent.py` に再開の費用の行は無い | 無い | 段 未定(題 9-5) | — |
| G-131 | MD-37 記憶の器 | `--memory on`・`--memory-store events`(`engine/memory.py`・`engine/memory_store.py`)。既定は off で誰も覚えない | 腕だけ | 段 未定 | — |
| G-132 | MD-38 忘れ方の方向 | 腕 `--memory-model m1`(`engine/memory_m1.py`)。既定は m0 かつ `--memory off` | 腕だけ | 段 未定(版上げの時期は別に決める) | — |
| G-133 | MD-39 段 M0〜M5・人も記憶の一つ・個人差 | M0・M1・M2・人は腕(`--memory-people memory` ほか)。M3 と M5 は器(`engine/memory_impression.py`・`engine/memory_trace.py`)。店の 32 行と関係の表の上限はまだある | 腕だけ | 段 未定 | — |
| G-134 | MD-40 習慣 | LLM を呼ばず選ぶ自動化は無い。古典の `p_h` と連絡の習慣は腕(`engine/chooser.py`・`engine/contact/habit.py`)。仕様の状態は研究待ち | 無い | 段 未定 | K: A38 |
| G-135 | MD-41 実行意図 | System 1 の棚と内側の時計は無い。腕 1b・2 に知らせと頭の中の思い出し(`engine/calendar2/recall.py`)。仕様の状態は研究待ち | 無い | 段 未定(題 4) | — |
| G-136 | MD-42 起床の入口と驚き | 候補の源 6 つ・条件 12 種(`engine/change_detect.py`・`agents/state.py`)で入口 3 種の形でない。近接・見られている・傍受は条件の表に残る。仕様の状態は研究待ち | 形が違う | R-133 の案の v3-5・v3-6(未決) | V: A73・S30 / K: M26 / D: A08・A30・A31・A70 |
| G-137 | MD-43 内側の変化=関心事の棚と注意の負荷 | 関心事の棚と注意の負荷は無い(grep)。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-138 | MD-44 内省 | 振り返りの呼びは無い。`absent.reflect_day` の宣言はある | 無い | 段 未定 | D: A74 |
| G-139 | MD-45 時間の実感 | 実感の式は 1b(`engine/calendar_self.py`)。既定の B3 は 5 分切り捨て。仕様の状態は研究待ち | 腕だけ | 段 未定 | V: A47・A68 |
| G-140 | MD-46 通知と連絡の気づき | `--contact c1`(`engine/contact/device.py`・`deliver.py`・`port.py`) | 腕だけ | 段 未定 | — |
| G-141 | MD-47 漏洩の検査と知識の物差し | `tools/instruments/leak_check/` は実行前(PENDING §2 の 18) | 器だけ | 段 未定 | — |
| G-142 | MD-48 数値の見せ方と連続値 | `Choice` の連続値の欄は空(`engine/decision/port.py`)。値段を LLM が出す道は無い | 器だけ | 段 未定 | — |
| G-143 | MD-49 仕組みは全員同じ | 全員が同じ仕組みという本文は満たす(`engine/run.py`)。複数の LLM を混ぜる腕は無い(grep)。読みの迷い: 腕 1 つの有無を差に数えた | 無い | 段 未定 | — |
| G-144 | MD-50 仕分けの残り(心に関わる行) | A04 は `agents/state.py`、A07 と A32 は `perception/templates.py`、A72 は `perception/attention.py`、M10 は `engine/systems/talk.py` | 未決 | 段 未定 | V: A04・A07・A72(割れる)/ D: A32(割れる)/ K: M10(割れる) |
| G-145 | MD-52 範囲の外の人の思考 | 舞台の外と乗車中の体は見送る(`engine/arbiter.py`)。「思考は無い」の行は `absent.py` に無い(grep)。範囲の外の過ごし方は腕 calendar 2。読みの迷い: A-15 | 形が違う | 段 未定 | D: M13・S52 |

差なし(項目 ID): MD-33・MD-51

差なしと読んだ根拠は次のとおりです。

- MD-33 研究の値は錨・不応期を外す・集中 f を持たない: 間隔は台帳 `BR-REFRACTORY-*` に宣言して残す。f は無い。読みの迷い: 課題従事の旗 `task_flag`(`perception/state.py`)を f と読まなかった。p_notice の研究の値は既定で通らない
- MD-51 メニュー化と文言の誘導: `docs/reference/behavior-audit-triage-2026-11-03.md` §4 の腕の候補 13 本に 5 行とも載る。実装はしない決定のまま(仕分け D: A08・A11・A29 / V: A34・A57)

## 第 4 章 差分の器

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-146 | AC-01 世界を書く唯一の道 | 世界を書く口は `engine/resolve.py`・`economy/ops.py`・`economy/goods.py`(書きの許可=`engine/systems/allow.py`・`core/write_permit.py`)。act の包みは無い | 形が違う | 段 未定(題 10) | — |
| G-147 | AC-02 「世界を書ける」の範囲 | 世界過程も `engine/resolve.py` の口を呼ぶ。経済は `economy/` の口 | 未決 | 段 未定(題 10) | — |
| G-148 | AC-03 差分の器の定義と成り立つ条件 | 差分の型と判例の器は無い(grep) | 無い | 段 未定(v3 の核の後) | — |
| G-149 | AC-04 状態の種類 A〜E と基本操作 | 語彙 12 語の動詞と `_apply_*`(`engine/resolve.py`)。A は `ops.transfer` と `move_goods`。B の口は無い | 形が違う | 段 未定(v3 の核の後) | — |
| G-150 | AC-05 口へ移す順と操作の種類の表 | 帳簿の 9 口は `ops.transfer` を通す(`economy/ledger.py`)。行動の適用は `engine/resolve.py` のまま | 形が違う | 段 未定(v3 の核の後) | — |
| G-151 | AC-06 止めるものと記録するもの | 権利の無い開閉店は止めず記録する(`engine/rights/record.py`)。記録は開閉店だけで、事後の反応は無い。読みの迷い: B-03 | 形が違う | 段 未定 | E: S26 |
| G-152 | AC-08 やり直しがきくかは世界の性質 | 操作の種類ごとの性質の表は無い(grep) | 無い | 段 未定(v3 の核の後) | — |
| G-153 | AC-10 器の試験 | 保存則と書きの試験はある(`tests/economy/cp2/`)・hypothesis は一部。ミューテーションの精度の実測は見つからない(grep) | 形が違う | 段 未定 | — |
| G-154 | AC-11 ランは開始時の版で最後まで走る | 版とハッシュは manifest にある(`engine/run.py`)。判例の器が無いので凍結の対象も無い。読みの迷い: 器の有無を差に数えた | 無い | 段 未定(v3 の核の後) | — |
| G-155 | AC-12 層 3 の形(ランの中は凍結した判例だけ) | 語彙外は同義語辞書 → 「なし」(`llm/undefined.py`)。「できなかった」は返さない。ラン後の判定の道具は `tools/vocab/adjudicate.py` | 形が違う | 段 未定(v3 の核の後) | D: A27・A64・M25 |
| G-156 | AC-13 世界の部品を足す手順 | 世界の部品の台帳は無い(grep)。語彙の判定の道具だけ | 無い | 段 未定(v3 の核の後) | — |
| G-157 | AC-14 判例の形と昇格の手順 | 判例の形は無い | 無い | 段 未定(v3 の核の後) | — |
| G-158 | AC-15 A2-1 判例の穴を埋めるのは誰か | 判例の穴は無い(MD-17)。読みの迷い: B-15 | 無い | 段 未定(v3 の核の後) | K: A02・B3・B8 |
| G-159 | AC-16 行為の鎖 | 鎖の欄は無い(MD-16) | 無い | 段 未定(題 7・題 9-2) | — |
| G-160 | AC-17 叶わなかった望みと計器の区分 | 語彙外の語を数える台帳はある(`llm/undefined.py`・`--undefined-out`)。「正しい失敗」と「欠陥」の分けは無い | 形が違う | 段 未定(v3 の核の後) | — |
| G-161 | AC-18 A2-2〜4 の読み | 該当のコードは無い | 未決 | 段 未定 | — |
| G-162 | AC-19 意図を判例に当てる方法 | 該当のコードは無い | 未決 | 段 未定 | — |
| G-163 | AC-20 差分の表現 | 該当のコードは無い | 未決 | 段 未定 | — |
| G-164 | AC-21 制度の旗 3 欄 | 3 欄は無い(`engine/rights/ledger.py`)。設計書 `docs/design/v2-a2-rights-flags-2026-11-02.md` だけ | 無い | 段 未定(v3 の核の後) | — |
| G-165 | AC-22 旗が本社のときの扱い | 該当のコードは無い | 未決 | 段 未定 | — |
| G-166 | AC-23 旗の初期化の物差しと検査の順 | 該当のコードは無い | 未決 | 段 未定 | — |
| G-167 | AC-24 判例ごとのテストの事例の最小 | 該当のコードは無い | 未決 | 段 未定 | — |
| G-168 | AC-25 smart object の見せる量と見せ方 | 該当のコードは無い。候補の出し方は腕 `engine/decision/sources.py` | 未決 | 段 未定 | — |
| G-169 | AC-26 「できなかった」の返し方と計器の区分 | 失敗は結果コードと B6 の文で返す(`perception/renderer.py`) | 未決 | 段 未定 | D: A36 |
| G-170 | AC-27 頻度の規則は置かない | 値付けと発注の判断が無く頻度の規則も無い。腕 calendar 3 のシフトは金曜の頭に組む(`engine/calendar3/layer.py`)。顕著性で起こす口は無い | 形が違う | 段 未定(v3 の核の後) | — |
| G-171 | AC-28 語彙を定義する理由と足すもの | 語彙 v3 は 12 語+役割語 11 語で、足す語は入っていない(`llm/contract.py`) | 形が違う | 段 未定(11-01p 段 3 の 3-1) | D: A27 |
| G-172 | AC-29 意図の保持 | 意図の保持は既定(`engine/intent.py`)。黙って変わる種類は残る(`engine/resolve.py`・`engine/commit.py`) | 形が違う | R-133 の案の v3-6(未決) | K: A02・A17・B3・B5・B8・S22・S25・F1・F2・F3・F4 |
| G-173 | AC-30 同じ時刻の取り合い | 同じ刻みは行の順と `t_notice` で決める(`engine/commit.py`・`engine/resolve.py`)。受け入れ 4 人 | 形が違う | R-133 の案の v3-2・v3-8(未決) | V: A18・B1・M7・M8・M9・S8・S9・S11 |
| G-174 | AC-31 核が決まってから決める部分 | 適用は刻みの中の `phase_a`〜`phase_c`(`engine/systems/act.py`) | 未決 | R-133 の案の v3-8(未決) | — |
| G-175 | AC-32 答えの読み方 | 今の読みは `llm/parser.py` | 未決 | 段 未定(題 9-2) | D: A27・A28・A64・A65・A66・M25 |

差なし(項目 ID): AC-07・AC-09

差なしと読んだ根拠は次のとおりです。

- AC-07 規則の表と検査: `docs/design/rules-table.json`・`engine/rules/table.py`・違反の器 `rules.minimum_wage_shortfall`(`economy/stage2.py`)
- AC-09 原因の欄と実験の口: `engine/events/log.py` の原因 3 型・`engine/experiment/gate.py` の `admit`・`tests/economy/cp2/test_cp2_event_links.py`

## 第 5 章 経済

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-176 | EO-01 部門・科目・faucet と sink | 6 部門・6 行・列挙はある(`economy/accounts.py`)。銀行は預金だけ・政府は税だけ。科目は 15 で逸脱比例コストが残る(呼び手は `economy/pricing.py` だけ)。読みの迷い: 仕様は 12+残差+退蔵 | 形が違う | 段 未定 | — |
| G-177 | EO-02 保存則の実装形 | `ops.transfer` と検算 2 本と試験はある(`tests/economy/cp2/`)。T3 は `economy/checks.py` に実装がある。読みの迷い: 仕様は T3 を未実装と書く=コードが先に進んでいる | 形が違う | 段 未定 | — |
| G-178 | EO-04 入れるものと段階 | 賃金・買い物・運賃・引き出し・消費税・天引きは入る。家賃と借金は器。年金の受け取りと預け入れの行為は見つからない(grep)(`economy/stage2.py`) | 形が違う | 段 未定 | — |
| G-179 | EO-05 最初の資産 | 財布は対数正規(`economy/anchors.py`)・預金は 30 日分(`economy/stage2.py`)。W21 の資産の表 `w21_money` はエンジンが読まない(grep) | 形が違う | 段 未定 | — |
| G-180 | EO-06 支払い方法 | 財布優先のつなぎ(`economy/stage2.py`)。`Choice.payment` は空。本人が選ぶ口は無い | 形が違う | R-133 の案の v3-6(未決) | E: M28 / V: A58 |
| G-181 | EO-07 賃金と給料日 | 給料日と職業ごとの賃金は既定(`economy/stage2.py`・`economy/wages.py`)。原資は外界から同額(台帳 `DOC-ec21-employer-funding-exogenous`)で、法人企業統計からの口座の設定は無い(grep) | 形が違う | 段 未定 | — |
| G-182 | EO-09 引き出しと ATM | 規則で下ろす(`engine/resolve.py`・`economy/stage2.py`)。ATM は OSM だけで P30 は無い(`engine/economy_stage2.py`)。語彙に「下ろす」は無い | 形が違う | R-133 の案の v3-6(未決) | K: M18 |
| G-183 | EO-10 店の売上と外の売上 | 店の売上は客の買い物から。外の売上は `EXTERNAL_STORE_SALES_YEN`=0(`economy/stage2.py`・台帳 `DOC-ec21-external-store-sales-zero`) | 形が違う | 段 未定 | — |
| G-184 | EO-11 任せた技術の問い | W2・W3・W4・W6・W8 の答えをコードの行と対応づけられなかった(`economy/stage2.py` に札が無い) | 未確認 | 段 未定 | — |
| G-185 | EO-12 税と社会保険料 | 消費税と会社員の天引きは既定(`economy/taxes.py`)。自営業が本人で納める道は無い(grep・国民年金と国保の行は読むコードなし)。軽減税率は器 | 形が違う | 段 未定 | — |
| G-186 | EO-13 信用 | `economy/credit.py`(`CreditBook(capacity=0)`)。行は足されない | 器だけ | 段 未定 | — |
| G-187 | EO-14 権利台帳 | 行と口はある(`engine/rights/ledger.py`)。営業許可は 0 行・家賃は空欄(台帳 `BR-RIGHTS-LICENCE-BLANK`)。ランの中で行は増えない | 形が違う | 段 未定 | — |
| G-188 | EO-15 組織の判断の線(A2) | 店主・店長の判断の口は無い。腕 `--duties arm` の開閉・補充・廃棄だけ(`engine/duties/`) | 無い | 段 未定(v3 の核の後=11-02r/§3) | — |
| G-189 | EO-16 外=入力 | `input.economy_prices`・`input.ward_policy` は欄だけ(`world/processes/inputs.py`)。価格は構築時の値 | 器だけ | 段 未定 | — |
| G-190 | EO-17 当面「無い」と宣言するもの | `absent.hiring_firing` はある。店の出入りと新しい品目の行は `absent.py` に無い(grep)。店の一覧は固定 | 形が違う | 段 未定 | — |
| G-191 | EO-19 営業時間 | W7 の表を過程が見て担当か代打で開閉(`engine/processes/opening.py`)。本人の判断は腕 `--duties arm` | 腕だけ | 段 未定(腕の既定化) | — |
| G-192 | EO-20 雇用の割り当てとシフト | 丸振りが残る(`engine/rights/initial.py`)。全員出勤は `engine/rate_rules.py` の宣言。シフトは腕 calendar 3 | 形が違う | 段 未定(版上げ 5 回目=PENDING §2 の 8) | — |
| G-193 | EO-21 店の仕事(働く人のエージェント) | `--duties arm`(`engine/duties/`)。計器は `role_actions`・`fallback`。接客は `absent.serve_customer` | 腕だけ | 段 未定(腕の既定化) | D: A27 |
| G-194 | EO-22 納品と発注 | `absent.inbound_delivery`(`engine_stopped=False`)と `absent.ordering`。過程は乱数の時刻に枠を積むだけ(`engine/processes/goods_flow.py`)。配送員の体は無い | 形が違う | 段 未定 | — |
| G-195 | EO-23 補充と廃棄 | 補充は担当か代打(`engine/processes/goods_flow.py`)。判断は腕 `--duties arm`。既定の廃棄は `absent.discard_unsold` | 腕だけ | 段 未定(腕の既定化) | — |
| G-196 | EO-24 消費の 4 判断点 | 4 つの口は無い。`absent.item_qty`・`absent.price_balk` の宣言はある。場面の表は `tools/instruments/dm_eval/scenes/consumption_v1.jsonl`。買う前に値段を見せる知覚は無い | 無い | 段 未定(11-01p 段 3) | — |
| G-197 | EO-25 家で食べる・家で使う | `absent.eat_home`。腕 `--home-meal plan` は予定の行の実行で本人の判断でない(`engine/energy.py`)。家の食料の在庫は無い。#41 は残る(`engine/processes/goods_flow.py`) | 無い | 段 未定 | — |
| G-198 | EO-26 店の選ばれ方 | 既定は最寄り 1 件に確率 1.0(`engine/chooser.py`・`engine/poi_target.py`)。古典は腕 | 形が違う | R-133 の案の v3-6(未決) | K: A01・A19・A20・A21・A22・A23・A37 / V: A54 / D: S10 |
| G-199 | EO-27 運賃 | 一律 180 円(`engine/processes/rail.py` の `FARE_YEN`)。計画の退出は運賃 0 の腕があり、日課の移動は運賃が動かない | 形が違う | R-133 の案の v3-1(未決) | E: M27 |
| G-200 | EO-28 ホテル | 過程が 21 時に同じセルのホテルへ入れ 9 時に解く(`engine/processes/civic.py`)。「泊まる」の語・宿泊権・金の移動は無い(grep)。読みの迷い: B-13 | 形が違う | 段 未定 | — |
| G-201 | EO-31 錨と知識の検査(測るためだけ) | 設問は無い(grep は `economy/pricing.py` の出典の注だけ) | 無い | 段 未定 | — |
| G-202 | EO-32 財布の見張りと v1 の手持ちの金の問題 | 財布と預金の分布を毎日出す計器は見つからない(`engine/systems/observe.py`・`economy/census.py` の grep)。来街者の口座の部品は `economy/stage2.py` | 無い | 段 未定 | — |
| G-203 | EO-33 物の流れ | `economy/goods.py` の `move_goods`。S12 と S13 が残る(`engine/resolve.py`)。買うのは 1 回 1 個 | 形が違う | R-133 の案の v3-8(未決) | E: S12・S13 |
| G-204 | EO-35 題 A3(年の単位の力学) | 該当のコードは無い | 未決 | 段 未定(題 A3) | — |

差なし(項目 ID): EO-03・EO-08・EO-18・EO-29・EO-30・EO-34

差なしと読んだ根拠は次のとおりです。

- EO-03 経済センサス: `economy/census.py` の月次と部門軸 `write_monthly_mer_sectors`・日次
- EO-08 最低賃金と労働時間: 最低賃金は human+つなぎの床(`docs/design/rules-table.json`)・記録の器 `rules.minimum_wage_shortfall`
- EO-18 値段: `absent.change_price`・`economy/pricing.py` は結線しない
- EO-29 率の形で外すもの: `engine/rate_rules.py` の既定 off。残るのは旧道 `--rate-rules legacy`(仕分け E: S51)
- EO-30 循環の検査(経済に関わる行): `world/processes/circularity.py`・`tests/bridging/test_drives_from_vs_scoring.py`
- EO-34 帳簿の記録の容量: `economy/ledger.py` の 6.5 行/体/日・manifest の `raw_overflow`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`

## 第 6 章 社会

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-205 | SO-01 社会は器と計器だけ | society の包みは無い。会話・関係・計器は `engine/` の中(`engine/conversation.py`・`engine/relations.py`・`engine/norm_meter.py`) | 形が違う | 段 未定(題 10) | — |
| G-206 | SO-02 関係と約束の置き場 | 約束は腕 `engine/calendar2/book.py`、関係は腕 `engine/relations.py`、雇用は `engine/rights/` | 未決 | 段 未定(題 10) | — |
| G-207 | SO-03 最初の関係と顔なじみ | 腕の関係は W16・W17 の共在から上限 15 辺(`engine/relations.py`)。資産の `w21_relations_initial` はエンジンが読まない(grep)。慣らしは無い | 形が違う | 段 未定 | V: S17 |
| G-208 | SO-04 組織は開始時点の現実の一部 | 組織の特別な物は無く雇用は権利台帳(`engine/rights/`)。丸振りの店が残る(`engine/rights/initial.py`)。資産の `w21_org` はエンジンが読まない(grep) | 形が違う | 段 未定(版上げ 5 回目) | — |
| G-209 | SO-05 部署 | 部署の目安は W21 段 4(`build/pop/attr_fns.py`・`build/pop/w21_build_b.py`)。エンジンは読まない(grep)。読みの迷い: B-06 | 器だけ | 段 未定 | — |
| G-210 | SO-06 会話の作り方 | 1 呼び 1 発話ブロックはある(`engine/conversation.py`)。言葉は腕。秒の時刻は無く `--talk-clock mora` は計器だけ | 形が違う | R-133 の案の v3-7(未決) | V: B6 |
| G-211 | SO-07 会話の範囲と情報の運び方 | 言葉は腕 `--speech-port on`、同席は腕 `--rel-copresent`(`engine/relations.py`) | 腕だけ | 段 未定 | K: A42 |
| G-212 | SO-08 声が届くかで会話が成り立つ | 2 m の決め打ちはつなぎどおり(`engine/proximity.py`)。音の式と気づきの 2 段は無い。同じ店の中は距離を見ない | 形が違う | 段 未定(空間の段 3) | E: S4・M16 / V: S36 |
| G-213 | SO-09 相手・番・人数・終わり | 3 呼・5 刻み・60 刻み・間隔 60/60/30・上限 2 が規則で動く(`engine/conversation.py`)。腕 `--conv-max-participants 3` | 形が違う | R-133 の案の v3-6・v3-7(未決) | K: B8・M10(割れる)・M14・M15・M29・S32・S33・F1・F3 / V: S34・S35 / D: S37 |
| G-214 | SO-10 発話を届ける器 | `--speech-port on`(`engine/speech/port.py`)。既定は `absent.utterance`。音声と表情の欄 `modality` は空 | 腕だけ | 段 未定(GPU の後の版上げ) | D: A65 |
| G-215 | SO-11 手伝う・通報する | 手伝いは必ず失敗・通報は記録だけ(`engine/resolve.py`)。判断モデルが無い。`absent.help_refuse_effect` | 無い | 段 未定(11-01p 段 3 の 3-3) | D: M24・S6 / V: S5 |
| G-216 | SO-12 カレンダーに入るものと保管の形 | 既定は W17。本人の予定の器は腕(`engine/calendar2/book.py`)。暦の口は既定(`engine/calendar.py`) | 腕だけ | 段 未定(題 4・カレンダーの段) | — |
| G-217 | SO-13 勤務と授業の約束の作り方 | W20 の約束は腕 `--calendar 1b`・`--calendar-shadow 1a`(`engine/calendar_self.py`・`engine/calendar_shadow.py`)。シフトは腕 calendar 3。読みの迷い: B-14 | 腕だけ | 段 未定(カレンダーの段 3) | — |
| G-218 | SO-14 二人の約束 | `--calendar-2 arm`(`engine/calendar2/book.py`・`port.py`) | 腕だけ | 段 未定 | — |
| G-219 | SO-15 予定の検査と置き場所の働き | 腕 calendar 2 と 1b の検査(`engine/calendar2/layer.py`・`engine/calendar_self.py`) | 腕だけ | 段 未定 | — |
| G-220 | SO-16 範囲の外の過ごし方・暦の知識・曜日 | 腕 `engine/calendar3/knowledge.py`・`engine/calendar2/`。月曜の行のつなぎは台帳 `BR-K9-MONDAY` | 腕だけ | 段 未定 | — |
| G-221 | SO-17 カレンダーの段と計器 | 1a・1b・2・3 はどれも既定で off。W17 を変える口は保留中 | 腕だけ | 段 未定(11-02r/§4 の保留) | — |
| G-222 | SO-18 時間の見積りと電車の判断 | 見積りは腕 1b(`engine/calendar_self.py`)。既定は間に合う便を選ぶ(`engine/presence.py`) | 腕だけ | R-133 の案の v3-6(未決) | K: M3・M4・M5 |
| G-223 | SO-19 道具の台帳と共通の決まり | `engine/tools/registry.py` の 9 行。既定は結果に使わない。持ち物の台帳は無い | 器だけ | 段 未定 | — |
| G-224 | SO-20 連絡の段 | C0 は器・C1 と C2 は腕 `--contact c1`(`engine/contact/`)。C4 と C5 は無い | 腕だけ | 段 未定 | — |
| G-225 | SO-21 送る・届く | `--contact c1`(`engine/contact/deliver.py`・`port.py`・`calls.py`)。判断は仮のモデルで文は定型 | 腕だけ | 段 未定 | — |
| G-226 | SO-22 範囲の外の相手 | `SHIBUYA_CONTACT_HABIT`(`engine/contact/habit.py`)。体の無い人は入れない(`engine/contact/book.py`)。読みの迷い: A-15 | 腕だけ | 段 未定 | — |
| G-227 | SO-23 連絡先・グループ・記録の量 | `engine/contact/book.py`・`engine/tools/groups.py`。店の番号の表は空(台帳 `BR-PHONE-TABLE-BLANK`)。記録の量は宣言を超える(台帳 `DOC-ct-c1-not-default`) | 腕だけ | 段 未定 | — |
| G-228 | SO-24 使っている間の気づきにくさ | `engine/contact/attention.py`。係数 0.49 は既定の描画から消した(`perception/renderer.py` の注) | 腕だけ | 段 未定 | — |
| G-229 | SO-25 SNS とサービスの模型 | SNS と検索の模型は無い(C4)。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-230 | SO-26 情報の出どころと看板 | 看板は W14 の作り物の文で印あり(台帳 `BR-SIGNAGE-FICTION`)。報道は固定文 1 行(`engine/processes/civic.py`)で区の発信の入力でない。催しは開催の記録だけ | 形が違う | 段 未定 | V: A06 |
| G-231 | SO-27 伝播・誤情報・因果はログから事後に抽出する | 原因の欄は既定(`engine/events/log.py`)。発話の行と記憶の目印は腕。出来事のファイルへの書き出しは無い | 腕だけ | 段 未定 | — |
| G-232 | SO-28 法に反する行動への事後の反応 | 記録は開閉店だけ(`engine/rights/record.py`)。反応の口は無い | 無い | 段 未定 | E: S26 |
| G-233 | SO-29 社会と世界の計器 | 自由度の台帳と広がりの計器は無い(grep)。`engine/norm_meter.py` は別の計器。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-234 | SO-30 箱の中の社会 | 建物の中が無い(WD-15) | 未決 | 段 未定 | — |
| G-235 | SO-31 偏りを消さずに測る | 集団を当てる率などの計器は無い(grep)。`tools/instruments/dm_eval/bias.py` は位置の偏り | 無い | 段 未定 | — |
| G-236 | SO-32 社会の題と倫理 | 該当のコードは無い | 未決 | 段 未定(核の後=記録 §3) | — |

差なし(項目 ID): この章にはありません。

## 第 7 章 検証

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-237 | VL-02 パターン台帳の運用規則 | `docs/design/v2-pattern-ledger.md` に §0・判定型・burned 列はある。判定関数の参照とハッシュ固定、attrition の表の道具は見つからない(grep) | 形が違う | 段 未定 | — |
| G-238 | VL-04 較正・照合・test の 3 段 | W19 の `HOLDOUT_LAYERS` と層の元の表はある(`build/audit/w19_freeze.py`)。D1b の層は未登録(grep・PENDING §2 の 14)。K5 は未公開 | 形が違う | 段 未定 | — |
| G-239 | VL-06 一部だけ検証に回すデータの分け方 | 分け方は台帳 §10-2。役割の台帳 `data/ground_truth/registry.yaml` を読むコードと試験は無い(grep)。W21 は自前の登録で検証側を開くと止まる(`build/pop/w21_sources.py`) | 形が違う | 段 未定 | — |
| G-240 | VL-12 物理の較正と照合の相手 | 全域の物理が無いので較正も無い(WD-22) | 無い | 段 未定(空間の段 5) | — |
| G-241 | VL-13 一致の指標 I_i | `tools/c8/dashboard.py` の `I_M` は None で式の実装は見つからない(grep) | 器だけ | 段 未定 | — |
| G-242 | VL-14 二段の合否 | 台帳の「強」の列はある。二段の集計は見つからない(`tools/c8/dashboard.py`)。読みの迷い: C-05 | 器だけ | 段 未定 | — |
| G-243 | VL-16 判定はアンサンブル単位・報告は分布 | `tools/c7/seed_ensemble.py`・`salt_compare.py`(ランの外)。CRPS は `tools/instruments/skill_gauge.py` の器。分散分解は見つからない(grep) | 腕だけ | 段 未定 | — |
| G-244 | VL-17 判定関数 | 受入と封印の照合と較正側の計器はある(`tools/c7/c7_accept.py`・`holdout_compare.py`・`tools/instruments/anchor_gauge.py`)。行ごとの判定の登録とハッシュ固定は見つからない(grep) | 形が違う | 段 未定 | — |
| G-245 | VL-19 門 1(G1)の的と問い | 計画書だけ(`docs/design/v2-g1-backtest-plan-2026-11-02.md`)。D1b は封印済み。ランと判定のコードは無い(grep) | 無い | 段 未定(E2 以降=v3 の核の後) | — |
| G-246 | VL-20 門 1 の未決 6 件 | 計画書 §7 の 6 件 | 未決 | 段 未定 | — |
| G-247 | VL-21 門 2(G2)と共有の心 | 天神は材料だけ(`data/tenjin/` の名)。場所ごとの係数の計器は無い。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-248 | VL-22 比べる相手 | ハフはエンジンに無い(`engine/chooser.py` の注)。技量スコアの器は `tools/instruments/skill_gauge.py`。原単位法の実装は見つからない(grep) | 器だけ | 段 未定 | — |
| G-249 | VL-23 事前登録 v1.4 | 道具は v1.3(`tools/c7/prereg_v13.py`)。v1.4 は草案。`is_foreign` は `agents/population.py` と `tools/instruments/anchor_gauge.py` にある | 形が違う | 段 未定 | — |
| G-250 | VL-25 感度試験 | タグと `tools/c8/sensitivity_v1.json` はある。レシピは 5,000 体で全規模の測定は無い | 形が違う | 段 未定(E2 以降) | — |
| G-251 | VL-26 検証の規模 | 全規模の検証のランは無い。`dm_eval` と `leak_check` は実行前。読みの迷い: C-07 | 無い | 段 未定(E2 以降=v3 の核の後) | — |
| G-252 | VL-28 漏洩の検査と知識の物差し | `tools/instruments/leak_check/` は実行前(MD-47) | 器だけ | 段 未定 | — |
| G-253 | VL-30 較正側の常設の計器 | `tools/instruments/anchor_gauge.py` はある。記録は 10-14〜10-19 の 5 本と ca31 だけ(`docs/bench/instruments/anchor_gauge/`)で、版上げの履歴に列は無い。読みの迷い: C-06 | 形が違う | 段 未定 | — |
| G-254 | VL-31 受入の 3 分類(verification と validation) | 受入の表に主観・客観・内部整合の列は見つからない(`tools/c7/c7_accept.py`・grep) | 無い | 段 未定 | — |
| G-255 | VL-32 忠実度回帰検収 | byte-check と決定論の試験が今の検収 | 未決 | 段 未定 | — |
| G-256 | VL-34 世界の正しさの試験 | AC-10 と同じ。試験はあるが、ミューテーションの精度の実測は見つからない(grep) | 形が違う | 段 未定 | — |
| G-257 | VL-35 世界被覆指標 | 5 値は `build/audit/w18_coverage.py`。構築時は V が 0・R が null で、実測へ置き換える計器は見つからない(grep) | 形が違う | 段 未定 | — |
| G-258 | VL-36 自己修正ループ | 機械が修正を起草する道は無い(grep)。語彙の判定の道具だけ(`tools/vocab/adjudicate.py`) | 無い | 段 未定 | — |
| G-259 | VL-37 「無い」と「つなぎ」と「代打」の計器 | `tools/instruments/absent_declarations.py` と台帳の件数はある。代打の計器は開閉と補充だけ。計器盤に一覧の行は無い(`tools/c8/dashboard.py`) | 形が違う | 段 未定 | — |
| G-260 | VL-38 正しい失敗と欠陥 | 結果コードはある(`engine/resolve.py`)。「正しい失敗」と「欠陥」の分けは無い(grep) | 無い | 段 未定 | — |
| G-261 | VL-39 新しい計器(自由度・広がり・生態系) | 自由度の台帳・広がり・生態系の計器は無い(grep)。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-262 | VL-40 現実データの日次取得の位置づけ | エンジンは日次の現実データを読まない(grep は構築の 3 本だけ)。外れ値の日の印は無い(grep) | 形が違う | 段 未定 | — |
| G-263 | VL-41 検証に回すかが未決のデータ | PENDING §1-1 の行のまま | 未決 | 段 未定 | — |
| G-264 | VL-42 検証の道具の壁打ち | 該当の題は未着手 | 未決 | 段 未定(核の後=記録 §3) | — |

差なし(項目 ID): VL-01・VL-03・VL-05・VL-07・VL-08・VL-09・VL-10・VL-11・VL-15・VL-18・VL-24・VL-27・VL-29・VL-33

差なしと読んだ根拠は次のとおりです。

- VL-01 パターン台帳ゲート: CLAUDE.md §4・台帳の必須欄 `contributes`(`world/processes/records.py`)
- VL-03 強い行: 台帳 §5・§7 に行がある(値は読まず見出しと列だけ)
- VL-05 検証専用データの一覧: 台帳 §10・`tools/instruments/read_guard.py`
- VL-07 封印の層と見てよい範囲: W19 の静的ゲート・`tools/instruments/read_guard.py`・`tests/build_audit/`。包みの形は PR-27 に数えた
- VL-08 開封の手順: `tools/c7/holdout_compare.py` の `--open-seal`・W19 の `opened`
- VL-09 封印行と代わりの行: 台帳 §2 と §10。読みの迷い: §2 の後の表は「まだ封印しない」のままで、K5 は §10 の行で読んだ
- VL-10 較正に使ってよいものと burned: 台帳の burned 列・`world/processes/circularity.py`。E4 は計画書の行
- VL-11 循環の機械検査: `world/processes/circularity.py` の 2 段・`tests/bridging/`
- VL-15 合格の読み方とフロア: `tools/c8/dashboard.py` の見出しの片側性の文・`tools/c8/c8lib.py`・CLAUDE.md §5
- VL-18 ゲートの形 (c) から (d) へ: CLAUDE.md §4 の (c) の文
- VL-24 ablation: `tools/c8/ablation_runner.py`・`ablations_v1.json`・`docs/design/v2-budget-declaration.md` の L2
- VL-27 固定の評価: `tools/instruments/dm_eval/`(340 場面+消費の場面)・`.github/workflows/ci.yml` の ci-2。読みの迷い: 夜の検査は時間の門を記録だけにしている(`SHIBUYA_TIME_GATES: record`)
- VL-29 診断と合否を分ける: 計器は合否を付けない(`engine/calendar_shadow.py`・`engine/calendar_self.py`・`tools/c8/`)
- VL-33 段ごとの受入の仕組み: `.github/workflows/ci.yml` の ci-0・ci-1・ci-2。受入の役割の分けは運用で、コードに現れない

## 第 8 章 実験

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-265 | EX-01 実験が世界に入れるのは決定だけ | 改変は決定の表として世界の表へ入る(`engine/experiment/apply.py`)。告知は出来事の行までで住人に届かない(台帳 `DOC-cf33-notice-rows-only`) | 形が違う | 段 未定 | — |
| G-266 | EX-02 改変の流れと段取り | 準備・告知・実行の段取りの口は無い。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-267 | EX-03 知らせ方は手順で決まる | 申込書の `notice` の欄で誰に・いつ・どの道具でを書く(`engine/experiment/form.py`) | 形が違う | 段 未定 | — |
| G-268 | EX-04 代わりに実行しない・実行されなければ欠陥 | 担当の不在の店は代打が実行する(台帳 `DOC-cf33-fallback-executes`)。`execution_breakdown` には出るが `ok` に入らない(`engine/experiment/branch.py`) | 形が違う | 段 未定 | — |
| G-269 | EX-05 分岐の始まりと開始前の作り込み | 開始前に作り込む道は無い。L3 は器。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-270 | EX-06 改変のレベル | L0・L1 は腕 `--experiment`、L2〜L4 は `implemented=False`(`engine/experiment/form.py`)。欄は `level` の記号のまま。読みの迷い: C-08 | 腕だけ | 段 未定 | — |
| G-271 | EX-09 最初からと途中からを 1 つの書き方で | 始まり 0 は刻みの頭で当てるだけで、改変の後に経験を作る順は未実装(台帳 `DOC-cf33-start-zero-order`) | 形が違う | 段 未定 | — |
| G-272 | EX-10 任意の時刻で分岐する | `--experiment-branch`(`engine/experiment/branch.py`・`switch.py`)。LLM サーバー群の分岐は組み立てで止める | 腕だけ | 段 未定 | — |
| G-273 | EX-11 経験は改変の後に作る | 名指しの検査は道具だけ(台帳 `DOC-cf33b-persona-check-caller`・`engine/experiment/checks.py`)。経験を作り直す道は無い | 器だけ | 段 未定 | — |
| G-274 | EX-12 申込書 | `engine/experiment/form.py` に探索と確認の欄。ランの種類は `engine/run_kind.py` の 4 つで仕様と違う(RT-29) | 腕だけ | 段 未定 | — |
| G-275 | EX-13 慣らしと測る期間 | `engine/experiment/warmup.py`・`tools/instruments/warmup_gauge.py`。回した記録は見ていない | 器だけ | 段 未定 | — |
| G-276 | EX-14 探索と確認 | `--experiment-model`・`engine/experiment/ensemble.py` の封印と入口の検査 | 腕だけ | 段 未定 | — |
| G-277 | EX-15 標準の出力はアンサンブル | `engine/experiment/ensemble.py`(初期状態 × モデル × 偶然)。本数の実測は無い | 腕だけ | 段 未定 | — |
| G-278 | EX-16 初期状態の作り方(ヒストリーマッチング) | `tools/instruments/hm_gauge.py`。構築に結線していない(`build/` の grep) | 器だけ | 段 未定 | — |
| G-279 | EX-17 反実仮想の答え方 | `engine/experiment/branch.py` の A/A の枝と対の差 | 腕だけ | 段 未定 | — |
| G-280 | EX-18 統計の手順 | `tools/c7/salt_compare.py`(ランの外)。二重の並べ替え検定は見つからない(grep)。読みの迷い: C-10 | 腕だけ | 段 未定 | — |
| G-281 | EX-19 外に出す予測の封印と公開 | `engine/experiment/ensemble.py` の入口の検査と `skill_container`(値は空)。公開の記録を書く呼び手は無い | 器だけ | 段 未定 | — |
| G-282 | EX-20 予測の台帳 | 予測の台帳は無い(grep)。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-283 | EX-21 人の天気予報(観測と同化) | 観測と同化の道は無い(grep)。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-284 | EX-22 E 系列 | `tools/night5070/experiments.json` は 10-25 §6 の E1〜E8 の定義のまま。11-01 の E 系列は計画書だけ(`docs/design/v2-e-series-plan-2026-11-01.md`)。35 万体のランは無い | 形が違う | 段 未定(E2 以降=v3 の核の後) | — |
| G-285 | EX-23 比べる腕の候補 | 店舗の 4 腕・ペルソナの 3 構成・架空名の腕・複数の LLM の腕は無い(grep)。古典の腕 `--policy classical` はある | 無い | 段 未定 | K: A37 |
| G-286 | EX-24 揺らしと頑健性 | 揺らしと元に戻る時間の計器は無い(grep)。`--weather-perturb` は再生日を変えるだけ。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-287 | EX-25 伝播・誤情報・因果は事後に抽出する | 原因の欄は既定(`engine/events/log.py`)、発話の行と記憶の目印は腕。ファイルの書き出しは無い(SO-27 と同じ) | 腕だけ | 段 未定 | — |
| G-288 | EX-26 反実仮想の入口の実装 | 決定の表の L2〜L4 は `implemented=False`(`engine/experiment/form.py`) | 未決 | 段 未定 | — |

差なし(項目 ID): EX-07・EX-08

差なしと読んだ根拠は次のとおりです。

- EX-07 やらないこと: `engine/experiment/apply.py` の決定の表に心の欄は無い。ラン中の裁定は無い
- EX-08 実験の入口は 1 か所: `engine/experiment/gate.py` の `admit`・`form.py`(知らない欄は ValueError)・`tests/engine/experiment/`

## 第 9 章 構築

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-289 | BD-03 世界の時点と版 | 開始日と W12 の版は確かめた(`engine/calendar.py`・`build/field/w12_real_timetables.py`)。古いデータの店の扱いの記録は見つけられず、`data/` の中も開いていない | 未確認 | 段 未定 | — |
| G-290 | BD-04 全国で同じ形でそろう材料・4 層・都市圏 | 全国の材料だけで組む口と管轄の欄は無い(WD-26) | 無い | 段 未定 | — |
| G-291 | BD-06 データの役割の台帳 | `data/ground_truth/registry.yaml` はあるが読むコードが無い(grep)。部分の検査は W19 の層の元の表(`build/audit/w19_freeze.py`)と W21 の登録(`build/pop/w21_sources.py`) | 形が違う | 段 未定 | — |
| G-292 | BD-07 段 0 の材料 | 面の材料と塗りの順はある(`build/space/navmesh1.py`・`sources.py`)。取得の残りあり(PENDING §2 の 10)。Overture は未で配布元も未確認 | 形が違う | 段 未定(段 0) | — |
| G-293 | BD-09 店の存在の判定 | 存在の判定の規則は無い(`build/geo/w6_poi_org.py` は OSM v8 の POI) | 無い | 段 未定(空間の段 2) | — |
| G-294 | BD-10 階の割り当てとテナント | 階は OSM v8 と組織の欄の値(`build/geo/w6_poi_org.py`)。優先順の規則と「生成」の印は無い。W21 の席の偏りは確認待ち(PENDING §2 の 19) | 形が違う | 段 未定(空間の段 2) | — |
| G-295 | BD-11 商業施設の平面図 | 図から事実を写す道は無い(grep)。`data/user_floor_maps/` の置き場の名だけ | 無い | 段 未定(空間の段 2) | — |
| G-296 | BD-12 駅の構内図と時刻表 | 時刻表の読み取りは構築に入った(`build/field/w12_real_timetables.py`)。構内図と号車の位置を読む道は無い(grep) | 形が違う | 段 未定(空間の段 4) | — |
| G-297 | BD-13 京王 井の頭線 | ODPT チャレンジ枠の CSV を読む(`build/field/w12_real_timetables.py`)。公開枠の確認は未(PENDING §2 の 13) | 形が違う | 段 未定 | — |
| G-298 | BD-16 W12・W10 と旧資産の切替口 | W12 は実ダイヤへ置いた。騒音の指紋は manifest にある(`engine/systems/report.py`)。騒音は静的のままで動的な計算は無い。切替口は CLI に無い(grep) | 形が違う | 段 未定(車の段) | — |
| G-299 | BD-17 人口の作り直しの方針 | 範囲の中は体を作った(`build/pop/w21_*.py`)。輪・来る可能性のある人・遠くは層の表だけで体が無い(`build/pop/w21_outside.py`) | 形が違う | 段 未定 | — |
| G-300 | BD-19 属性 | 年齢・世帯・仕事・言語・国籍はある(`build/pop/attr_fns.py`)。持ち物・体と感覚・移動の助け・声は空欄(`build/pop/w21_persona.py` の `PS2_BLANK_FIELDS`) | 形が違う | 段 未定 | — |
| G-301 | BD-20 人物の中身 | 文は事実から組み「作り物の生い立ちは使わない」の版(`build/pop/w21_persona.py`)。TIPI は欄だけ。Anthology 型は無い(grep)。仕様の状態は研究待ち | 形が違う | 段 未定 | — |
| G-302 | BD-21 開始前の経験 | TimeGeo 型の表 `w21_prior_places` はある(`build/pop/w21_prior.py`)。エンジンは読まない(grep) | 器だけ | 段 未定 | — |
| G-303 | BD-23 開始時点の組織と雇用 | 雇用の表は `w21_rights_initial` を読む(`engine/economy_rules.py`)。表に無い店は丸振り(`engine/rights/initial.py`) | 形が違う | 段 未定(版上げ 5 回目) | — |
| G-304 | BD-25 外の人と通過客 | 外から働きに来る人は体がある(`build/pop/w21_outside.py`)。通過客と車は無い。訪日は枠の行だけ。ヒストリーマッチングは器 | 形が違う | 段 未定 | — |
| G-305 | BD-26 申請の要るデータ | 公開の集計だけで作っている(`build/pop/w21_sources.py`) | 未決 | 段 未定 | — |
| G-306 | BD-27 世界の部品を足す手順 | 手順を支える台帳は無い(AC-13)。語彙の判定の道具だけ | 無い | 段 未定(v3 の核の後) | — |
| G-307 | BD-28 物の実体化と全国の材料だけの腕 | 物の実体と全国の材料の腕は無い。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-308 | BD-33 ライセンス台帳・層の分離・商用の前の許諾 | ライセンス台帳はある(`docs/data-license-ledger.md`)。各層の OSM 混在の表は見つからない(grep) | 形が違う | 段 未定 | — |
| G-309 | BD-34 外のサービスはループの外 | ループの中で外のサービスは使わない(`build` と engine に無い)。世界の中の模型は無い。仕様の状態は研究待ち | 無い | 段 未定 | — |

差なし(項目 ID): BD-01・BD-02・BD-05・BD-08・BD-14・BD-15・BD-18・BD-22・BD-24・BD-29・BD-30・BD-31・BD-32

差なしと読んだ根拠は次のとおりです。

- BD-01 構築の原則: `build/run.py` の入力と出力のハッシュ・`pyproject.toml` の層の契約(実行時に build を読まない)
- BD-02 世界の資産の段階: `build/run.py` の `ALL_STAGES`・W21 は別の入口・`build/audit/w18_coverage.py`・`tools/c8/sensitivity_v1.json`
- BD-05 天神の段 0: `docs/data-license-ledger.md` その 21-b・`data/tenjin/` の名。残りの問いは仕様でも未決
- BD-08 点群: `data/raw/` の名・`tools/spatial/las_pointcloud_agg.py`・台帳 #135
- BD-14 ODPT と現実データの集め方: `tools/realworld_fetch/`(`rw_fetch_daily.py`・欠けを数える `ledger.py`・`logrotate.py`)
- BD-15 W13 天気: `build/field/w13_weather.py`(realworld_live は読まない注)・`engine/processes/environment.py`・manifest の sha(`engine/systems/build.py`)
- BD-18 作り直しの手順と数の書き分け: 段 0〜10 は W21 の入口(`build/pop/w21_build*.py`・`w21_apply.py`)。段 11 は GPU の後。345,858 は `docs/ops/version-history.md`
- BD-22 人数の枠: `build/pop/w21_frame.py`・`tests/build_pop/test_w21_sources.py`(人流を読まない試験)
- BD-24 人口の点検: `build/pop/w21_checks.py`・`w21_check.py`(合否なし)
- BD-29 データは無料か申請で得られるものだけ: CLAUDE.md §7・`docs/data-license-ledger.md`
- BD-30 取得を許した範囲: CLAUDE.md §7 の一覧
- BD-31 断られたら取りに行かない: CLAUDE.md §5・§7・`docs/research/research-order-template.md`。`data/research_cache/` に SGLang の名のファイルは無い(名だけ確かめた)
- BD-32 取得しないもの: `tools/realworld_fetch/`・`tools/world_data/`・`tools/spatial/`・`tools/build_geo/` に該当のドメインが無い(grep)

## 第 10 章 外への口

| G-番号 | 仕様の項目 | 現状 | 区分 | 埋める段 | 仕分けの表の行 |
|---|---|---|---|---|---|
| G-310 | IF-01 読み手と 4 つの出し方 | ビューアも映像の書き出しも無い。近いのは計器盤の 1 枚(`tools/c8/dashboard.py`) | 無い | 段 未定(止まる地点 S7) | — |
| G-311 | IF-02 最小の形 | 地図の上を点が動く画面は無い(`src/`・`tools/` の grep) | 無い | 段 未定(止まる地点 S7) | — |
| G-312 | IF-03 最初から守ること | 応答の記録と状態と在圏の記録は頼んだときだけ(`--tape`・`--state-out`・`--occupancy-every`)。出来事の記録はメモリの中 7 日でファイルに書かない。ビューアと架空名の段は無い | 形が違う | 段 未定(題 7) | — |
| G-313 | IF-04 ゼロから作り直す | ビューアのコードは無い | 無い | 段 未定(止まる地点 S7) | — |
| G-314 | IF-06 観測の不変性 | ビューアと書き出しの口が無く、試験も無い。出来事の記録の不変は別にある(`engine/events/log.py`) | 無い | 段 未定(止まる地点 S7) | — |
| G-315 | IF-07 表示の高さ | 表示の口が無い。点群の集計は `tools/spatial/las_pointcloud_agg.py` | 無い | 段 未定(止まる地点 S7) | — |
| G-316 | IF-08 ビューアの細部 | ビューアは無い(IF-01) | 未決 | 段 未定 | — |
| G-317 | IF-09 現実の誤りを報告する口 | 報告の口は無い | 無い | 段 未定 | — |
| G-318 | IF-10 計器盤 | 3 面の Markdown と JSON はある(`tools/c8/dashboard.py`)。`I_M` は None。つなぎの台帳と未計測の一覧の節は無い(grep) | 形が違う | 段 未定 | — |
| G-319 | IF-11 架空名の段 | 置き換えの段は無い(WD-25)。出力の口に通す道も無い | 無い | 段 未定(止まる地点 S7) | — |
| G-320 | IF-12 主張の線引き | 案は `docs/design/v2-methodology.md` の文 | 未決 | 段 未定 | — |
| G-321 | IF-13 言ってよいこと・言わないこと | 「34.6 万人がそれぞれ考えて動く(判断はコード・判断モデル・LLM)」の行は今の中身と合わない(既定は mock・判断モデルが無い=MD-22)。`docs/reference/repo-guide/can-say.md` §3 が同じ点を挙げる。読みの迷い: 方針の文と読むか今の中身の文と読むかは原文から分からない。ルートの README は開いていない | 形が違う | 段 未定 | — |
| G-322 | IF-14 ODbL と出典の表記 | 各層の OSM 混在の表は見つからない(BD-33) | 未決 | 段 未定 | — |
| G-323 | IF-15 PLATEAU AWARD と未来 IT | `tools/plateau2026/` は無い。`docs/plateau2026/check-3-3.md` の確認だけで図・動画・PDF は未。優先は下げた決定どおり | 形が違う | 段 未定(11/14 に一度止まる) | — |
| G-324 | IF-16 ODPT チャレンジの作品 | `docs/design/v2-odpt-work-materials-2026-10-14.md` の材料だけ | 未決 | 段 未定 | — |
| G-325 | IF-18 外に読まれる文書の書き方 | ルートの README は発注どおり開いていない。`docs/design/v2_significance.md` に訂正の注つきで判例のループの文が残る(grep) | 未確認 | 段 未定 | — |
| G-326 | IF-19 主張の言葉の決まり | 文書の全数を確かめていない。`docs/design/v2_significance.md` ほか 3 本に「学習なし」は無い(grep) | 未確認 | 段 未定 | — |
| G-327 | IF-20 倫理の運用 | 公開の層・フィクション注記・検出器・「捉えられないもの」の欄は無い(grep)。ペルソナは集計統計からの生成物(`build/pop/`) | 無い | 段 未定(核の後=記録 §3) | — |
| G-328 | IF-21 見た目の欄の倫理の線 | 見た目の欄は無い(WD-46) | 未決 | 段 未定 | — |
| G-329 | IF-22 Omniverse/OpenUSD の書き出しと 3D | 書き出しの口は無い(PENDING §2 の 15)。答申は未発注。仕様の状態は研究待ち | 無い | 段 未定 | — |
| G-330 | IF-24 データの権利 | 該当のコードは無い | 未決 | 段 未定 | — |

差なし(項目 ID): IF-05・IF-17・IF-23

差なしと読んだ根拠は次のとおりです。

- IF-05 ビューアの着手と仕様: 未着手で、止まる地点 S7 の決定どおり。読みの迷い: 着手の順の項なので未着手を差なしと読んだ
- IF-17 止まる地点(公開と外部連絡): `docs/design/v2-answers-2026-10-13b.md` §0-2 の文。CLAUDE.md §6 が同じ規則を引く
- IF-23 介入と観測の窓口(語): 用語集 `docs/design/v2-glossary.md` の行。仕様の状態は研究待ち

## 仕分けの表の行で、どの項目にも引かなかったもの

ありません。168 行(164 行+F1〜F4)をどれかの項目に引きました。

## 確かめた範囲

- 未確認の 7 件は PR-07・PR-08・PR-17・EO-11・BD-03・IF-18・IF-19 です。理由は各行の現状の欄に書きました。
- 運用の規則の項目(PR-18・PR-19・PR-23・PR-24・VL-18 ほか)を差なしと読んだ根拠は、規則の文が CLAUDE.md などにあることです。規則が守られているかまでは確かめていません。
- ランと pytest は回していないので、既定で動く・動かないの判定は、コードの読みと段 1・段 2 の資料に基づきます。実 LLM での挙動は確かめていません。
- カタログの数値(件数・体数)は記録の値のまま使いました。つなぎの台帳の ID は `docs/design/bridging-ledger.json` と照らしました。
- 段 2 のカタログが「docstring だけ読んだ」と書くファイルのうち、差の判定に要るものは該当の範囲をコードで読むか grep しました。全文を読んだわけではありません。
- パターン台帳は見出しと列の名だけで判定し、封印行と照合値は写していません。
- 仕様の章の文と決定の原文の突き合わせはしていません。比べたのは仕様の章の文と今のコードです。
