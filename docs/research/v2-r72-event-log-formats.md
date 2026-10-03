# R-72 答申: 出来事の記録の形式(v1 の観測契約 L1 と原因台帳・他のシミュレーションの記録・汎用の形式・容量・検査)

<!-- hdr:v1 -->
- **分野**: ソフトウェア工学 #29 / 交通シミュレーション #2 | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §6 ①・⑪・§10-2・§11 第 1 群「出来事の記録の形式」)
- **一次確認**: **B**(サブ実読。◎35・○2・△6・×1。空欄 14 件は §8)・v2 と v1 のコードは本書の作成時に読んだ行を `ファイル:行` で示す・親検収 済(第316・2026-10-03: v1 の `observer/schema.py:497-503`・`causality.py` の 4 分類・提案書の 17.49 KB/体/日と 1,622 件/体/日を手元の v1 で確認・69.4 B/呼を再計算。等級 A−)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は WebFetch が保存したものを pymupdf で抽出)・コミットなし・台帳/設計書/src 未編集。v1 リポは `v1:` を付けたリポ相対の位置で示す。
> 既存答申との関係: [v2-data-contract-research](v2-data-contract-research.md)(08-30・**一次確認 D=出典 URL なし**)が「(t_ns, seq) の全順序主キー・3 本の流れ(events / llm_calls / checkpoints)」を推奨し、決定台帳 §9 の行 6 が仮決定として写している。**循環参照検査**: 本書はこの答申を根拠に使わない。同じ対象(Mesa・AgentSociety・OASIS・MCAP・Overeem 2021・OTel GenAI)は本書で原典を読み直した(§0)。

## 結論(5 行)

1. **v2 の出力には、状態の変化を原因つきで残す口がまだ無い**。テープ(版 3・1 呼 1 行・14 列)は LLM の入出力のうち共有ブロック B0〜B4 の ID と応答だけを残す。checkpoint はハッシュだけである。台帳の生ログ(24 B/行)と物の配達ログ(16 B/行)はリングバッファで、ファイルに書く口も原因の欄も無い(§1)。
2. **v1 の観測契約 L1 は 9 列の Parquet(zstd)で、原因台帳は「起こしたものの種類」6 語を 4 分類(agent / device / natural / boundary)へ畳む作り**だった。種類ごとの表(CAUSE_OF_KIND)、行為者を payload から取り戻す表(聞き手の行は話し手を行為者にする 4 種)、装置の id の 3 列を、既定 OFF で足していた。実ランの L1 は **17.49 KB/体/日・1,622 件/体/日**(1 万体)で、体数に対して超線形に増えた(10 体 135 → 1 千体 618 → 1 万体 1,622 件/体/日)(§2)。
3. **他のシミュレーションの記録で「親の出来事」を欄に持つものは見つからなかった**。MATSim の events は時刻・種類・属性だけを持つが、利用者の手引きには「events だけから再生できるはず」と書かれている。Mesa・NetLogo・Repast は集計か自由な表、OASIS は trace(user_id・created_at・action・info)、Concordia は構造化ログである。因果の鎖を欄で持つ形は OpenTelemetry の span(parent span ID と、因果を表す link)だけだった(§3・§4)。
4. **入力だけを記録して再生し、状態のずれをハッシュで見つける方式**は、ゲームのロックステップ(Age of Empires 2001・Factorio)とイベントソーシング(Fowler 2005「外部の問い合わせは記録して再生で使い回す」・スナップショットは最適化で正は出来事の列)が実務の型になっている。v2 のテープと checkpoint はこの型にすでに近い。足りないのは「記録から状態を組み立て直してスナップショットと比べる」検査である(§4・§6)。
5. **容量の錨**: v2 実ランのテープは **69.4 B/呼**(c7-day-4・39 万体・270.7 万呼・187.7 MB)[再計算]。v1 の L1 は **約 10.8 B/件**[再計算]。状態の書き出しは既定 137 B/体・全腕 5,373 B/体である(39 万体で 53 MB・2.1 GB。6 時間ごとなら 1 日 4 回)。テープ版 4 の B5・B6 本文と原因の欄のバイトは**空欄**で、5,000 体で測る手順を §7-5 に書いた。指示書の「1 日 6〜15 GB(39 万体)」は推測のまま併記する(§7-5)。

## §0 出典の表

等級: **◎** 原典本文・公式文書で数値や列名まで逐語確認 / **○** 一部推測を含む・一部だけ読めた / **△** 抄録・検索の要約・二次 / **×** 未読(空欄)

| # | 出典 | URL・位置 | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | v1 観測の型 `Event` と種類の登録 | `v1:src/society/observer/schema.py`(486 行目〜の dataclass・登録表) | ◎ | 全 507 行(登録表は種類名と説明) |
| 2 | v1 原因台帳(因果台帳 IF-F) | `v1:src/society/observer/causality.py`(1〜130 行・621〜700 行) | ◎ | 語彙・射影・分類の原則・行為者の取り戻し |
| 3 | v1 ロガー(L1/L1b/L2/L3) | `v1:src/society/observer/logger.py`(1〜300 行) | ◎ | 列の型・スコープ注入・part 分割 |
| 4 | v1 伝播系譜 | `v1:src/society/observer/provenance.py` | ◎ | 全 85 行 |
| 5 | v1 25 万体の観測の提案書(容量の実測) | `v1:docs/plans/proposal-dp-u3-observe-250k.md` §2-1・§2-3 | ◎ | 表と「正直な限界」 |
| 6 | v1 移行計画(帰属率・近接因+後方ポインタ 1 本) | `v1:docs/plans/actor-model-migration-plan.md` 15・49・62 行 | ◎ | 該当行 |
| 7 | 創立時の要件(直接記録の 3 点セット) | [v2-requirements.md](../design/v2-requirements.md) 50〜55 行 | ◎ | 該当節 |
| 8 | MATSim `MatsimEventsReader.java` | https://github.com/matsim-org/matsim-libs/blob/master/matsim/src/main/java/org/matsim/core/events/MatsimEventsReader.java | ◎ | 拡張子ごとの読み手 |
| 9 | MATSim User Guide(開発版 2014-09-12) | https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2014/14-20/user-guide-0.6.0-2014-09-12.pdf/ | ◎ | events の節(PDF 抽出) |
| 10 | MATSim code-examples issue #111(2019) | https://github.com/matsim-org/matsim-code-examples/issues/111 | ◎ | 本文(体数の記載なし) |
| 11 | MATSim の event 型(GitHub・API 文書) | https://github.com/matsim-org/matsim-libs/blob/master/matsim/src/main/java/org/matsim/api/core/v01/events/PersonDepartureEvent.java ほか | △ | 検索の要約(型名・属性名) |
| 12 | SUMO Output(一覧) | https://sumo.dlr.de/docs/Simulation/Output/index.html | ◎ | 形式(.csv/.parquet)と分類 |
| 13 | SUMO FCD Output | https://sumo.dlr.de/docs/Simulation/Output/FCDOutput.html | ◎ | 属性・周期・抽出 |
| 14 | SUMO TripInfo | https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html | ◎ | 属性・書く時点 |
| 15 | SUMO RawDump(netstate) | https://sumo.dlr.de/docs/Simulation/Output/RawDump.html | △ | 検索の要約 |
| 16 | Park ほか 2023 Generative Agents(UIST) | https://arxiv.org/abs/2304.03442(本文は https://ar5iv.labs.arxiv.org/html/2304.03442) | ◎ | 記憶の流れ・§5 の JSON |
| 17 | generative_agents リポの README | https://github.com/joonspk-research/generative_agents | ◎ | 保存・再生・圧縮 |
| 18 | Concordia CHEATSHEET | https://github.com/google-deepmind/concordia/blob/main/CHEATSHEET.md | ◎ | ログの解析の節 |
| 19 | Concordia CHANGELOG | https://github.com/google-deepmind/concordia/blob/main/CHANGELOG.md | △ | 検索の要約 |
| 20 | AgentSociety(Piao ほか 2025) | https://arxiv.org/html/2502.08691v1 | ◎ | §5.2・§5.5 |
| 21 | AgentSociety `storage.avro` API 文書 | https://agentsociety.readthedocs.io/en/latest/apidocs/agentsociety/agentsociety.storage.avro.html | △ | 404。検索の要約のみ |
| 22 | OASIS(Yang ほか 2024) | https://arxiv.org/html/2411.11581v4 | ○ | §2.2 の 1 文。付録 D.2 は途中で切れた |
| 23 | OASIS `trace.sql` | https://raw.githubusercontent.com/camel-ai/oasis/main/oasis/social_platform/schema/trace.sql | ◎ | CREATE TABLE |
| 24 | NetLogo BehaviorSpace(7.0.4) | https://docs.netlogo.org/behaviorspace.html | ◎ | 出力形式・測る時点 |
| 25 | Mesa DataCollector | https://mesa.readthedocs.io/latest/apis/datacollection.html | ◎ | 4 種のデータ・tables |
| 26 | Repast4Py logging | https://repast.github.io/repast4py.site/apidoc/source/repast4py.logging.html | ◎ | TabularLogger |
| 27 | AnyLogic Model execution logs | https://anylogic.help/anylogic/running/logs.html | △ | 403(遮断)。検索の要約のみ |
| 28 | OpenTelemetry Traces | https://opentelemetry.io/docs/concepts/signals/traces/ | ◎ | span の欄・root・link |
| 29 | OpenTelemetry GenAI(移設の告知) | https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/ | ◎ | 移設先だけ(属性の要件は未読) |
| 30 | CloudEvents spec | https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md | ◎ | 必須・任意の属性・一意性 |
| 31 | CloudEvents Distributed Tracing 拡張 | https://github.com/cloudevents/spec/blob/main/cloudevents/extensions/distributed-tracing.md | ◎ | traceparent・tracestate |
| 32 | Fowler 2005「Event Sourcing」 | https://martinfowler.com/eaaDev/EventSourcing.html | ◎ | 定義・再構成・スナップショット・Gateway |
| 33 | Microsoft Azure Architecture Center「Event Sourcing pattern」 | https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing | ◎ | 全文 |
| 34 | Overeem ほか 2021(JSS 178) | https://arxiv.org/abs/2104.01146 | △ | 抄録 |
| 35 | Lamport 1978 CACM 21(7):558-565 | https://lamport.azurewebsites.net/pubs/pubs.html(論文 https://doi.org/10.1145/359545.359563) | ○ | 著者の解説だけ(論文本文は未読) |
| 36 | Bettner・Terrano 2001「1500 Archers on a 28.8」 | https://www.gamedeveloper.com/programming/1500-archers-on-a-28-8-network-programming-in-age-of-empires-and-beyond | ◎ | ロックステップ・同期外れ・録画 |
| 37 | Factorio Wiki「Desynchronization」 | https://wiki.factorio.com/Desynchronization | ◎ | 全文 |
| 38 | MCAP 仕様 | https://mcap.dev/spec | ◎ | Message レコード・Timestamp |
| 39 | zstd README | https://github.com/facebook/zstd | ◎ | ベンチマーク表 |
| 40 | Adaltas 2021「Storage size and generation time in popular file formats」 | https://www.adaltas.com/en/2021/03/22/performance-comparison-of-file-formats/ | ◎ | 容量の表 |
| 41 | Taylor ほか 2021「Towards an Open Format for Scalable System Telemetry」 | https://arxiv.org/abs/2101.10474 | ◎ | 表 VI(PDF 抽出) |
| 42 | H3 解像度の表 | https://h3geo.org/docs/core-library/restable/ | ◎ | 解像度 9〜15 |
| 43 | Elasticsearch geohash_grid | https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-geohashgrid-aggregation.html | ◎ | 精度 6〜12 の大きさ |
| 44 | ベクトル時計(Fidge 1988・Mattern 1989) | なし | × | 未読(空欄) |

v2 のコードは本書の作成時に読んだ(commit 1e212c2 の作業木)。行番号はその時点の値。

## §1 v2 の今の出力(何があり、何が無いか)

| 出力 | 位置 | 中身 | 原因の欄 | ファイルに書くか |
|---|---|---|---|---|
| LLM テープ `calls.parquet` | `src/shibuya/engine/tape.py`(版 3=`shibuya.tape/3`・91 行) | 1 呼 1 行・14 列: call_id(string)・agent_id(int32)・tick(int64)・wake_class(int8)・prompt_hash・block_ids(list)・params_hash・response・tokens_in・tokens_out・deferred・deferred_reason・observed_tick・recalled_rows(list<int32>)。zstd | call_id がその呼の id。**状態の変化とは結ばれていない** | `--tape DIR`(`engine/run.py:4078`) |
| LLM テープ `blocks.parquet` | 同上 | 共有ブロック B0〜B4 の本文(block_id=blake3 の先頭 16 バイト)。**B5・B6 は入らない**(`llm_bridge.py:147` の `SHARED_BLOCK_IDS`) | なし | 同上 |
| checkpoint 列 | `engine/run.py:465` `Checkpoint`・`cli.py:465` `checkpoints_payload` | tick ごとの agents/world/population/schedule(+activity)のハッシュと combined。既定は 360 tick ごと | なし | `--checkpoints-out`(JSON) |
| 日次センサス・月次 MER | `cli.py:302-327`・`economy/census.py:195` | 1 日 1 行(残差・貨幣供給量・faucet/sink の合計・取引件数・退蔵・物の残差・廃棄 g・棚の数・ゲート) | 科目(AccountCode)の集計だけ | `--census-out`(Parquet) |
| 金の台帳の生ログ | `economy/ledger.py:414`(transfer)・`:447`(transfer_many)・`:692`(raw_rows) | 1 行 = tick・支払部門・索引・受取部門・索引・金額・科目。1 行 24 B・リングバッファ・保持窓(容量 3.0 行/体/日 × N × 保持日数の宣言) | **科目だけ。call_id も過程の名前も無い** | 無い(メモリ内) |
| 物の配達ログ | `economy/goods.py:936-`(`_log_many`)・`delivery_log` | tick・POI・スロット・数量・GoodsCode。16 B/行 | GoodsCode だけ | 無い(メモリ内) |
| ActualLog | `world/processes/actual_log.py`(23 B 固定幅+索引 8 B) | 対象 id・tick・過程・逸脱語彙(GTFS-RT 式)・遅延。保持窓 7 日・日次集約 | 過程の id を持つ(エンジン由来の行) | 書く口は見つからない(grep の範囲) |
| 在圏 journal | `cli.py:623` | セルの在圏 | なし | `--occupancy-out`(.npz) |
| 未定義行動の表 | `cli.py` `--undefined-out` | 語彙外の行動語の集計 | なし | JSON |
| 診断行 | `engine/run.py:254` `DIAG_RUN_COLUMNS` | tick ごとの件数 | なし | RunResult の中 |

**無いもの**(指示書 §6 ① の (a) に対して): 行動・会話・取引・エンジンが強制した出入り・世界の過程・体の閾値越えの**出来事の行**/発話の届け先の行/位置の記録(C5)/状態の中身のスナップショット(今はハッシュだけ)/B5・B6 の本文/決定モデルの出力。改訂記録 [v2-requirements-revision-log](../design/v2-requirements-revision-log.md) 43 行も同じ判断(「無い」の根拠は grep の範囲)をしている。

記憶の出どころの手がかりは 1 つだけある。店の記憶の `sm_source`(u8・ビットの和: self=1・wom=2・signage=4・net=8)(`engine/store_memory.py:93`)で、「どこから知ったか」の集合は持つが、**話し手の id と call_id は持たない**。

## §2 v1 の観測契約 L1 と原因台帳

### 2-1 L1(出来事の行)のスキーマ

`v1:src/society/observer/logger.py` 234〜255 行(`_l1_table`)と `schema.py` 486 行(`Event`)。Parquet・zstd・追記専用。

| 列 | 型 | 意味 |
|---|---|---|
| step | int32 | ステップ番号 |
| sim_min | int32 | 世界内の分 |
| agent_id | int32 | **その行を誰の視点で記録したか**(行為者とは限らない。世界の出来事は -1) |
| kind | string | 種類(登録表 `EVENT_KINDS` にあるものだけ。未登録は例外) |
| x / y | float32 | 位置 |
| payload | string | 種類ごとの詳細(JSON 文字列。sort_keys) |
| rng_stream | string | 乱数の流れの名前 |
| llm_call_id | string | その行為を出した LLM 呼の id(IF-1・既定 OFF。**行為者自身の行にだけ**刻む) |
| cause_type | string | 原因の 6 語(IF-F・既定 OFF のときは列ごと無い) |
| actor_id | int32 | 行為者の id(復元できなければ null) |
| device_id | string | 装置の id(`"faregate:<駅ノード>"`・`"signal:<交差点id>"` など) |

- 固定列は変えず、詳細は payload に入れる(D12 の拡張契約)。新しい種類は `register_event_kind` の 1 行で足す。登録表には 194 種(causality.py の docstring の数)。
- L1b = LLM 呼の行(`log_llm_call`: llm_call_id・agent_id・purpose・step・cached など)。L2 = step ごとの集計 1 行。L3 = スナップショット(`{"step", "state": JSON 文字列}`)。
- part 分割(checkpoint ごとに `l1_events.part-NNNN.parquet`)と、row group 単位で流し込む finalize(25 万体 × 10 日の L1 を 1 プロセスに載せられないため)。

### 2-2 原因台帳(IF-F・第 100 バッチ)

`v1:src/society/observer/causality.py`。

- **解いた問題**: L1 の `agent_id` は「行の主語」ではなく「誰の視点の記録か」で、`speak`(話した本人)・`hear`(聞いた側)・`wage`(受け取った本人)・`weather`(-1)が同じ列に同居していた。そのため「エージェントが起こした変化」と「装置が起こした変化」を事後に分けられなかった。
- **語彙**: 6 語を設計文書の 4 分類へ射影する(`PROJECTION_4WAY`)。

| 6 語 | 4 分類 | 意味(docstring の要約) |
|---|---|---|
| agent | agent | ある個体が選んで行ったことの帰結 |
| device | device | 制度・自動処理・ルールが世界の状態に反応して発火 |
| schedule | device | 暦・時計だけで決まる制度(DEVS の内部遷移) |
| physics | device | 身体・空間・内部状態の連続力学 |
| natural | natural | 外生(天気・災害) |
| boundary | boundary | 観測の枠の外の統計・実験者の介入・名簿の配布 |

- **分類の原則**: 1) その step に個体の選んだ行為が無ければ存在しない行は agent。2) 個体が作った状態にルールが反応したら device。3) 両方から出る種類は device に寄せる(帰属率の過大評価を避ける)。4) unknown は作らない。
- **分類の単位は種類(kind)**。種類→原因の表 `CAUSE_OF_KIND`(160 行〜)に無い種類は KeyError。
- **行為者の取り戻し** `PATIENT_ACTOR_OVERRIDES`: hear→speaker・opinion_shift→source・transmission→from・deliver→courier の 4 種(agent_id が受け手の種類)。
- **装置の id を刻んでよい語** `DEVICE_STAMPABLE` = device・schedule・boundary だけ(装置の処理中に出た行でも agent・physics・natural には刻まない)。
- **帰属率の分母から外す語** `TICK_CAUSES` = physics・schedule(毎 step・毎日必ず出る行で分母が埋まるのを避ける)。
- **注入の仕方**: 単一の書き口(`logger.log`)で、行為の適用中だけ開くスコープ(`set_cause` / `set_prov` / `set_cause_device`)から刻む。移行計画は「近接因+後方ポインタ 1 本(因果の鎖を行に直列化しない)」「帰属率は種類別の行列で報告」とした(`v1:docs/plans/actor-model-migration-plan.md` 49 行)。
- **既定 OFF**で、OFF のとき列は生えず L1 はバイト一致。

### 2-3 真偽台帳・伝播系譜(参考)

- 伝播系譜(`provenance.py`): 広まるもの(ラベル・語彙・噂・制度案)ごとに item_id を振り、`transmission` 行(agent_id=受け手・payload の from・channel)を書く。「L1 の transmission 行が正典(event sourcing)なので明細は事後に組み立て直せる」と docstring にある。
- 真偽台帳(第 73 バッチ): 事実の台帳(id・発生 step・場所・真値・目撃可能の条件)をエージェントから見えない側に置き、信念(値・確信度・情報源・取得 step・検証済み・親ノード)を L1 に出した。指示書 §10-2 はこの 2 つを**移植せず**ログから事後に抽出すると決めている。

### 2-4 容量(v1 の実測)

`v1:docs/plans/proposal-dp-u3-observe-250k.md` §2-1 の表。

| 量 | 値 | 種別(原文) | 出どころ(原文) |
|---|---|---|---|
| L1 出力 | **17.49 KB/体/日**(174.9 MB / 1 万体 / 1 日) | 実測 | `runs/rehearsal_pool10k` |
| イベント数 | **1,622 件/体/日**(16,220,177 件) | 実測 | 同上 |
| 1 件あたり | **約 10.8 B/件** | [再計算] 174.9e6 ÷ 16,220,177 | |
| 体数による変化 | 135(N=10)→ 618(N=1,000)→ 1,622(N=1 万)件/体/日 | 実測 | `bench_scaling`。原文は「同席由来の hear/transmission が二乗的」 |
| 25 万体 × 10 日 | 42.7 GB・40.6 億件(線形の下界) | 外挿 | 同 §2-3 |

v1 の 1 日あたりの GB を 39 万体で記録した実ランは見つからなかった(空欄)。創立時の要件は「標準プランで ~17GB/シミュ日」(`v2-requirements.md` 54 行)、予算表 S1 は「恒久記録 ≤5GB/シミュ日」である。

## §3 他のシミュレーションの出来事の記録の形式

| 枠組み | 記録の単位と形 | 主な欄 | 形式・圧縮 | 原因の持ち方 | 出典 |
|---|---|---|---|---|---|
| MATSim events | 1 行 1 出来事(人・車・施設)。手引き: 「各エージェントは 1 回のシミュレーションで典型的に数百の events を出す」「大きなシミュレーションでは 10 億を超える」 | 時刻・type・種類ごとの属性(person・link・facility・vehicle・actType・x/y など)。型の例: actstart / actend / departure / arrival / entered link / left link / PersonEntersVehicle | XML(.xml・.gz・.zst・.lz4)と NDJSON(.ndjson・.gz・.zst)。テキスト形式は廃止。**Parquet は読み手に無い** | **欄は無い**。手引き: 「理論上は events の情報だけで再生できるはず。plans はその日の計画、events は実際にどうだったか」 | #8・#9・#11 |
| MATSim 容量 | 利用者の報告: output_event.xml 約 22 GB・output_plans.xml 約 14 GB(体数は書かれていない) | | | | #10 |
| SUMO fcd | 毎 step・全車両と人。timestep・id・x・y・z・angle・type・speed・pos・lane・edge・slope・signals・acceleration など | 周期 `--device.fcd.period`・抽出率 `--device.fcd.probability` | 既定 XML。**拡張子を .csv / .parquet にすると表形式**。.xml.gz / .csv.gz で gzip | なし | #12・#13 |
| SUMO tripinfo | 車両が到着した時に 1 行(未到着は `--tripinfo-output.write-unfinished`) | id・depart・departDelay・arrival・duration・routeLength・waitingTime・timeLoss・rerouteNo・vaporized など。人は personinfo の段ごと | 同上 | なし | #14 |
| SUMO netstate | 毎 step・全辺・全車線・全車両(fcd に置き換えられ非推奨) | 名前・速度・位置 | XML | なし | #15 |
| Generative Agents | 記憶の流れ: 各記憶は「自然言語の記述・作成時刻・最後に引いた時刻」。想起の新しさの減衰は 0.995 | サーバーが各エージェントの JSON(位置・行動の記述・対象の物)を持ち、毎 step 変化を読んで更新 | 保存: `environment/frontend_server/storage`・圧縮版 `compressed_storage`・再生 URL `/replay/<名>/<開始 step>`(デバッグ向け) | なし | #16・#17 |
| Concordia | 構造化ログ(JSON)。`simulation.play(return_structured_log=True)` | 項目は entity・component・type・step を持ち、行動・観察・プロンプトを引ける | JSON・HTML の閲覧器 | **親や原因の欄の記載は無い** | #18・#19 |
| AgentSociety | 「プロフィール・シミュレーション中の状態・思考と対話・調査の結果」を記録。実験の id・名前・時間・設定・エラー | | ローカル=AVRO・オンライン=PostgreSQL(COPY FROM の一括書き込み)。規模の記載は「1 万体超・500 万のやりとり」 | 記載なし | #20・#21 |
| OASIS | trace 表: user_id(INTEGER)・created_at(DATETIME)・action(TEXT)・info(TEXT)。「各利用者の行動の履歴全体を trace 表に記録」 | 4 列が複合主キー | SQLite | 欄は無い(info の中身は自由) | #22・#23 |
| NetLogo BehaviorSpace | 測る時点ごとに reporter の値を 1 行(Table)・runs を列に並べる(Spreadsheet)・Lists・Statistics | `[run number]`・`[step]`・reporter の列 | CSV | 出来事の記録ではない。自前の記録は export-world などで | #24 |
| Mesa DataCollector | model・agent・agent-type の reporter と tables(自由な列の表) | | pandas の DataFrame | 欄は無い(tables に自分で作る) | #25 |
| Repast4Py | ReducingDataSet(列ごとに MPI で畳む)と TabularLogger(行を記録・全プロセスの行を連結) | 列は利用者が決める | 区切り文字の表 | 欄は無い | #26 |
| AnyLogic | 実行ログ(移動・出来事・メッセージ・状態遷移・資源など)を内蔵 DB の表に書く。表の例: agent_movement_log・agent_messages_log・statechart_transitions_log | | 内蔵 DB(読み取り専用) | 不明(公式ページが読めなかった) | #27(△) |

**まとめ**: 交通の 2 つ(MATSim・SUMO)は「出来事の行(MATSim)」と「毎 step の位置(SUMO fcd)」と「旅の要約(tripinfo)」を別の出力に分けている。LLM 社会シミュレーションの 3 つ(Generative Agents・Concordia・AgentSociety/OASIS)は行動・対話・状態を記録するが、状態の変化を原因に結ぶ欄は見当たらなかった。v1 の原因台帳(種類単位の原因・行為者の取り戻し・装置の id)は、調べた範囲では他に例が無い。v1 移行計画も「先行例が見つからない粒度」と書いている(#6)。

## §4 汎用の形式

| 形式 | 要点(原典) | v2 で使える点 | 出典 |
|---|---|---|---|
| OpenTelemetry trace | span の欄: 名前・**親 span の ID**(root は空)・開始/終了時刻・span context・属性・span の出来事・span link・状態。「link は 1 つの span を 1 つ以上の span に結び、因果の関係を表す」 | 「親 1 本+任意の link」で因果の鎖を表す。LLM 呼(親)→ 意図 → 解決 → 帳簿の書き込み(子)の形 | #28 |
| OTel GenAI | 仕様は opentelemetry.io から専用リポ(open-telemetry/semantic-conventions-genai)へ移った | 属性の要件は本書では読んでいない(空欄) | #29 |
| CloudEvents | 必須: id・source・specversion・type。任意: datacontenttype・dataschema・subject・time。「source+id は出来事ごとに一意」。**因果・親の標準属性は無い**。分散トレースの拡張が traceparent(必須)・tracestate を足す | 行の id を「(run・source・連番)で一意」にする | #30・#31 |
| イベントソーシング(Fowler 2005) | 「アプリケーションの状態の変化をすべて出来事の列として残す」。完全な再構成・時点の問い合わせ・出来事の再生。スナップショットから始めて後の出来事を再生。**外部の系は Gateway で包み、外部への問い合わせの応答は記録して再生で使う** | LLM=外部の系、テープ=Gateway の記録、という対応がそのまま成り立つ | #32 |
| 同(Azure の型) | 出来事は不変・追記のみ。状態は出来事の列の再生で作る(rehydration)。**スナップショットは最適化で、正は出来事の列**。N 件ごとにスナップショット。版: 寛容な読み・版の id・upcaster・書き換え(最後の手段)。順序: 出来事ごとに時刻と増える連番。**意図を書く出来事が、結果の状態だけを書く出来事より価値がある**(「2 席予約」と「残り 42 席」の例) | 原因の欄=意図の側の情報。状態の差分だけの行にしない | #33 |
| スキーマ進化(Overeem 2021) | 5 つの手: versioned events・weak schema・upcasting・in-place transformation・copy-and-transform | テープ版 4 と出来事の版の上げ方 | #34(抄録) |
| Lamport 1978 | 「e1 が e2 に因果的に影響しうるときに限り e1 が e2 に先行する、という半順序しか無い」(著者の解説)。論理時計で全順序を作る | 同じ tick の中の順序は (tick, 書き口の順, 連番) の全順序で十分(単一プロセス・単一の書き手のため)。ベクトル時計は分散で要るもの(未読) | #35・#44 |
| ゲームの決定論的な再生(AoE) | 「各機械で同じシミュレーションを走らせ、同じ命令の組だけを渡す」。乱数の種も同期。世界・物体・経路探索・照準をチェックサムし、違えば「out of sync」で止める。**録画は命令の列で、毎回同じに再生される**ためバグの再現に使った | テープ=命令の列、checkpoint のハッシュ=チェックサム | #36 |
| 同(Factorio) | 決定論のロックステップ。入力だけを送る。同期外れの報告に、クライアントの状態とサーバーの状態の両方のセーブを入れ、**テキスト比較で差を探す**(差は原因の証拠ではなく調べる場所の手がかり) | 「記録から組み立てた状態」と「スナップショット」を欄ごとに比べて、ずれた欄の名前を出す検査 | #37 |
| MCAP(ロボットの記録) | Message: channel_id(u16)・sequence(u32)・log_time(u64 ns)・publish_time・data。時刻は「利用者が決めた紀元からの u64 ナノ秒」 | 連続時間(§7-5 の時間のモデル)に移ったときの時刻の型の参考 | #38 |

## §5 列指向の保存と容量

| 項目 | 数値(原典) | 注 | 出典 |
|---|---|---|---|
| zstd の圧縮率 | Silesia コーパスで zstd -1 = 2.896・--fast=1 = 2.439・lz4 = 2.101 | 一般のファイルの値。v2 の表の値ではない | #39 |
| JSON と Parquet(Adaltas) | NYC trip: 生の JSON 222.0 GB・JSON-Gzip 11.5 GB・Parquet 58.1 GB(26%)・ORC-Zlib 6.7 GB。Wikimedia: 43.8 GB・3.6 GB・10.3 GB(24%) | **原文が「Parquet の圧縮が効いていない」と書いている**(HDP の jar 不足の可能性)。圧縮なしの Parquet と gzip の JSON の比較になっている | #40 |
| JSON(gzip)と Parquet(SysFlow) | 1 分の試料: httpd_prefork 3,300 KB 対 1,334 KB・httpd_worker 4,900 対 2,041・httpd_event 5,800 対 2,567・mysql 118 対 85・postgres 87 対 68・redis 93 対 59・minio 3,100 対 3,239・hadoop 18,483 対 9,682。原文: 「JSON は属性名を全レコードに書くので、属性名の長さが容量に大きく効く」 | gzip の JSON は Parquet の 0.96〜2.47 倍 [再計算] | #41 |
| 位置の量子化(H3) | 解像度 12: 平均面積 307.092 m²・辺 10.8 m。13: 43.870 m²・4.1 m。14: 6.267 m²・1.5 m。15: 0.895 m²・0.58 m(9〜15 の辺は外挿値と原文の注) | 渋谷の歩行の解像度なら 13〜15 の帯 | #42 |
| 位置の量子化(geohash) | 長さ 8: 38.2 m × 19 m・9: 4.8 m × 4.8 m・10: 1.2 m × 59.5 cm(赤道での最悪値) | | #43 |
| v2 の固定小数の前例 | 状態の SoA は位置を `node`(int32)・`edge_id`・`edge_s` で持つ(`resolve.py:1432-1434`) | 位置の行はグラフの (辺, 辺上の距離の量子化) で書ける(親の案) | コード |

追記専用+スナップショットの組み合わせは §4 のイベントソーシングと同じ型である。v1 の L1 も part 分割+finalize の連結で同じことをしていた(§2-1)。

## §6 検査の形(記録と状態の食い違いを見つける)

| 検査 | 原典での形 | v2 での形(親の案・未リサーチ) |
|---|---|---|
| 再構成(rehydration)と比較 | Azure: 状態は出来事の再生で作る。スナップショットはそこから作り直せる(#33)。Factorio: 2 つの状態をテキスト比較して差の場所を出す(#37) | 前のスナップショット S(t0)+ (t0, t1] の出来事の行 → S'(t1) を組み立て、S(t1) と**欄ごと**に比べる。ずれた欄の名前と体の id を出す。受入の試験に入れる(指示書 §6 ①) |
| 全体のチェックサム | AoE: 世界・物体・経路探索などをチェックサムし、違えば止める(#36) | 既存の checkpoint のハッシュ(agents/world/...)を S'(t1) にも掛けて一致を見る。10b の behavior-hash/full-hash と同じ道具 |
| 計画と実際の整合 | MATSim: plans は計画、events は実際。events だけで再生できるはず(#9) | 予定(カレンダー)と出来事の行の突き合わせ(遵守率)。ActualLog の遵守率と同じ考え |
| 保存則の試算 | (会計の試算表の原典は未読=空欄) | 既存の日次センサスの検算(残差・flow_ok・ex_nihilo_ok)を「出来事の行の和」で独立に再計算し、台帳の締めと一致するかを見る |
| 原因の欄の閉包 | v1: 未分類の種類は KeyError(unknown を作らない)(#2) | 出来事の種類ごとに原因の分類を 1 か所の表で宣言し、未宣言は試験で落とす |

**陽性対照**(親の案): 出来事の行を 1 行わざと落とす・金額を 1 円変える、と検査が必ず落ちることを試験に入れる。

## §7 v2 への当てはめ(すべて**親の案(未リサーチ)**。数値は出典か [再計算] か「推測」を付けた)

### 7-1 出来事 1 行の欄の案

| 欄 | 型の案 | 意味 |
|---|---|---|
| day・tick | int16・int32 | 時刻(A1 で日を入れる)。連続時間に移ったら MCAP 型の整数時刻(#38)に置き換える |
| seq | int64 | 書き込みの通し番号(同じ tick の中の全順序。単一の書き手なので Lamport 時計は要らない) |
| kind | uint16 | 種類(登録表の番号。名前は別表) |
| subject | int32 | 主体(行為者)。v1 の「視点の id」と混ぜない |
| object | int32 | 対象(相手・POI・SKU・辺など。種類ごとに意味を宣言) |
| place | int32+int16 | 位置の量子化(辺 id+辺上の距離の量子化、または階つきの格子)。C5 の形(起きたときだけ・範囲内) |
| cause_kind | uint8 | 原因の分類(v1 の 6 語を引き継ぐ案: agent/device/schedule/physics/natural/boundary) |
| cause_ref | int64 | agent なら call_id の数値化、エンジン由来なら過程の id(過程名の表を別に持つ) |
| parent_seq | int64 | 近接因の行(v1 移行計画の「後方ポインタ 1 本」・OTel の parent)。無ければ -1 |
| delta | 種類ごとの固定欄 2〜3 本(int64) | 差分(金額・数量・前後の値) |

**call_id の注意**(コードの事実): 今の call_id は `"<tick>:<agent>:<class>"`(`llm_bridge.py` docstring の expedient)で、日を含まない。複数日のランでは衝突するので、出来事の行から引く前に A1(鍵に日を入れる)で日を入れる必要がある。数値化するなら (day, tick, agent, class) を詰めた int64 が使える。

### 7-2 発話の届け先の行(§10-2 の 1)

話し手・聞き手・day/tick・call_id・届き方(宛先/非宛先/傍受)・会話セッションの id。書き口の候補は `ConversationManager.utterance`(`engine/conversation.py:651`)と `wom.py` の聞き手への転写(今は宛先だけ)。v1 の `hear` 行は agent_id=聞き手・payload の speaker=行為者だった。v2 は**行を話し手主体で 1 行、聞き手ごとに 1 行**にすると、v1 の「行為者の取り戻し」の表が要らなくなる。

### 7-3 記憶の出どころ(§10-2 の 2)

記憶の行(`write_memory`・`resolve.py:935`)と店の記憶の行(`write_store_memory`・`:962`)に、出どころの話し手 id(int32)と call_id(int64)を足す。店の記憶は今 `sm_source` のビットだけを持つ(§1)。テープ版 4 で欄を予約する(指示書 §3-4 の 3)。

### 7-4 原因の欄を入れる場所の候補(書き口の一覧)

`src/shibuya/engine/resolve.py` は「世界状態への唯一の書き込み口」(docstring)で、`with state.writable()` を書けるのは本ファイルだけと試験で強制されている。金と物は economy の単一 API を通る。

| 種類 | 書き口(関数・行) | 呼び手(代表) | 原因の候補 |
|---|---|---|---|
| 金 | `Ledger.transfer`(`economy/ledger.py:414`)・`transfer_many`(`:447`)→ `_record` | `resolve.py:2223`(購入)・`:2350`(食事)・`engine/processes/rail.py:590`(運賃)・`economy/pricing.py:196`・`economy/anchors.py:249` | 購入・食事=その呼の call_id / 運賃=過程(rail) |
| 初期の注入 | `endow_households`(`ledger.py:516`)・`endow_stores`(`:530`) | `resolve.py:522`・`cli.py:289` | boundary |
| 物 | `GoodsLedger.move_goods`(`goods.py:515`)・`sell_many`(`:602`)・`restock_many`(`:650`)・`deliver`(`:698`)・`to_bin_many`(`:706`)・`collect_waste`(`:730`)・`consume_many`(`:767`)→ `_log_many` | `resolve.py:2245`・`:2654`・`:2683`・`:2713`・`:2726`・`engine/processes/goods_flow.py:506` | 補充=店員の行為(call_id か古典の決定)/廃棄回収=過程 |
| 位置 | `r.node` の書き込み(`resolve.py:1434`・`:1501`・`:1555`)・`place_at_external`(`:2788`)・`rail_arrive`(`:2809`)・`rail_depart`(`:2827`)・`release_indoor`(`:2857`)・`begin_exit_walk`(`:2968`) | `_apply_move`(`:1641`)ほか | 移動=call_id / 乗降=過程(rail) |
| 関係辺 | `write_relations`(`:986`) | `engine/relations.py` | 会話の call_id |
| 記憶 | `write_memory`(`:935`)・`write_store_memory`(`:962`)・`write_familiarity`(`:910`) | `engine/memory.py`・`store_memory.py`・`wom.py`・`familiarity.py` | 直接経験=その行為の call_id / 伝聞=話し手の call_id |
| 会話 | `join_conversation`(`:1007`)・`set_conversing`(`:2441`)・`revert_conversation`(`:2425`) | `engine/conversation.py` | 招いた呼の call_id |
| 意図 | `set_intent`(`:1027`)・`fail_intent`(`:1059`)・`clear_intent`(`:1049`) | `engine/commit.py` | call_id |
| 体の閾値越え | `advance_body`(`:1101`)・`_energy_meal`(`:1189`)・`energy_home_meal`(`:1265`)・`energy_out_of_area_meal`(`:1246`) | `engine/run.py` | physics(閾値の段が変わった時だけ行にする) |
| 睡眠・起床 | `begin_planned_sleep`(`:628`)・`wake_from_plan`(`:753`)・`_apply_sleep`(`:2601`) | | 予定=schedule / 判断=call_id |
| 世界(店の開閉・温熱) | `set_open_flags`(`:2770`)・`request_open_close`(`:3057`)・`set_thermal`(`:2732`) | `engine/processes/opening.py`・`environment.py` | 開閉=店員の行為か schedule / 温熱=natural |
| 世界の過程の記録 | `ActualLog.append`(`world/processes/actual_log.py`) | `engine/processes/runner.py:185` | 過程の id(既に持つ) |

**バイトの見積り**(推測): 原因の欄を cause_kind(1 B)+cause_ref(8 B)とすると 1 行 +9 B。台帳の生ログ 24 B/行は 33 B/行になる(+38%)[再計算]。parent_seq(8 B)も足すと +17 B。列指向で zstd を掛けたときの実際の増分は空欄(§7-5 で測る)。

### 7-5 容量の見積り

**既知の錨**

| 量 | 値 | 出どころ |
|---|---|---|
| テープ(c7-day-4) | 187,714,260 B ÷ 2,706,593 呼 = **69.4 B/呼**・6.94 呼/体/日 [再計算] | [build-report-C7](../ops/build-report-C7.md) 135 行(c7-day-4 のテープ・390,067 体・B5/B6 の本文は入らない) |
| v1 L1 | 17.49 KB/体/日・1,622 件/体/日・約 10.8 B/件 [再計算] | §2-4 |
| 状態の書き出し | 既定 137 B/体(39 万体で 53 MB)・全腕 5,373 B/体(39 万体で 2.1 GB)。6 時間ごと(1 日 4 回)なら 212 MB/日・8.4 GB/日 [再計算] | [v2-d102-foundation-implementation-agenda](../design/v2-d102-foundation-implementation-agenda.md) 113 行・[state-inventory-refresh](../bench/analysis/wallbounce-0930/state-inventory-refresh.md) §0 |
| 台帳の生ログ | 24 B/行 × 3.0 行/体/日(宣言) | `economy/ledger.py` 40 行 |
| 物の配達ログ | 32 B/体/日(2.0 移動 × 16 B・宣言) | `economy/goods.py` 277 行 |
| ActualLog | 31 B/行(23 B+索引 8 B)・1 対象 4 件/日(見積り=expedient) | `world/processes/actual_log.py` |
| 予算 S1 | 恒久記録 ≤5 GB/シミュ日 | [v2-budget-declaration](../design/v2-budget-declaration.md) 70 行 |
| 指示書の推測 | 39 万体で 1 日約 6〜15 GB・スナップショット 1 回約 2.1 GB(全腕) | 指示書 §6 ①(**推測のまま**) |

**空欄**: テープ版 4 の B5・B6 本文の B/呼・決定モデルの出力の B/呼と呼数・出来事の行の件数/体/日と B/件(v2 の行動の粒度で)・原因の欄の圧縮後の増分。

**5,000 体で測る手順**(親の案)

1. mock の実資産 5,000 体 × 1 日(既定の checkpoint を再現する構成)と、全腕 ON の構成の 2 本を、記録の口を 1 本ずつ ON にして回す(口ごとの増分を分けるため)。
2. 口ごとに、ファイルのバイト数・行数・種類ごとの件数/体/日を取る。テープは B5・B6 の本文を入れた版と入れない版で比べる。
3. 圧縮の設定(zstd の段・row group の大きさ・辞書の有無)を 2〜3 通り変えて B/行を取る。
4. 39 万体への外挿は 2 通り書く。線形(件数/体/日 × 体数)と、**同席に由来する行(発話の届け先・近接)を体数の 2 乗に近い項として分けた式**。v1 の L1 は 1 千体→1 万体で件数/体/日が 2.6 倍になった(§2-4)。5,000 体の 1 点だけでは傾きが取れないので、1,000 体・5,000 体・(可能なら)2 万体の 3 点で測る。
5. mock は LLM の応答の長さと会話の量が実 LLM と違うので、テープと発話の行は c7-day-4 の実テープの B/呼(69.4 B)と呼数で補正し、補正したことを明記する。

### 7-6 (a) と (c) の比較

| 観点 | (a) 全部を原因つきで記録・スナップショット 6 時間ごと | (c) 人の行動とやりとりが中心・スナップショット 1 日 1 回・日中の内部の値は再生で補う |
|---|---|---|
| 出来事を出す口 | §7-4 の全行(金・物・位置・関係・記憶・会話・意図・体・睡眠・世界・過程) | 行動の確定・発話の届け先・取引・記憶の出どころ・位置(C5)。体の閾値越えと世界の過程は出さない |
| 実装の手間 | 書き口 30 前後に原因を渡す引数を足す(推測)。economy の API も変わる | resolve の行動の確定(`_ok`/`_fail`・`:1522`)と会話・記憶・帳簿の数か所 |
| 事後の抽出 | 伝播・誤情報・因果を再生なしで抽出できる | 体や過程が絡む因果(空腹→食事など)は再生が要る。**再生は同じコードの版でしか効かない**(指示書 §10-2) |
| 検査 | 「前のスナップショット+出来事 → 次のスナップショット」が欄ごとにそのまま成り立つ(§6) | 日中の値は記録に無いので、検査は 1 日単位。ずれた時刻を絞るには再生が要る |
| スナップショットの用途 4 つ(再開・時点の調査・分岐・検査) | 6 時間ごとに再開と分岐ができる | 日の境目からだけ(運用の再開は日の境目からと決まっている=指示書 §3-6) |
| 容量(39 万体・1 日) | スナップショット 全腕 8.4 GB [再計算]+出来事(空欄)+テープ。指示書の推測 6〜15 GB | スナップショット 全腕 2.1 GB+出来事(空欄・(a) より少ない)+テープ |
| 予算 S1(≤5 GB/日)との関係 | 全腕 ON ではスナップショットだけで超える [再計算]。既定の構成なら 212 MB/日 | 全腕 ON でもスナップショット分は 2.1 GB |
| 先行例との近さ | イベントソーシングの「正は出来事の列」(#32・#33)に近い | ゲームの「命令の列+チェックサム」(#36・#37)に近い |

## §8 空欄の一覧

1. v1 の 39 万体級の実ランの 1 日あたりの L1 の GB(見つからない)。
2. MATSim の events の容量の公式な目安(体数つき)。issue #111 の 22 GB は体数が無い。
3. MATSim の events を Parquet で書く公式の口(読み手に無い)。
4. Concordia の構造化ログの JSON スキーマの全体(CHEATSHEET に無い)。
5. AgentSociety の AVRO スキーマの列(API 文書が 404)。
6. AnyLogic の events_log の列(公式ページが遮断)。
7. OTel GenAI の属性の要件(移設先は未読)。
8. ベクトル時計の原典(未読)。
9. 会計の試算表の原典(未読)。
10. StarCraft のリプレイ形式(未読)。
11. テープ版 4 の B5・B6 本文の B/呼。
12. 決定モデルの出力の B/呼と呼数。
13. v2 の出来事の行の件数/体/日と B/件。
14. 原因の欄の圧縮後の増分。

## §9 写し検査・訂正の伝播・循環参照・フロア併記

- **写し検査**: 本書の数値のうち v1 と v2 の内部の値(17.49 KB・1,622 件・137 B・5,373 B・69.4 B の元の 187,714,260 B と 2,706,593 呼)は、元のファイルの行を読んで写した(§0 の #5・§7-5 の表の出どころ)。
- **循環参照検査**: 決定台帳 §9 の行 6 の「(t_ns, seq) 全順序主キー・3 本の流れ」は D 等級の答申([v2-data-contract-research](v2-data-contract-research.md))が根拠で、一次は無い。本書は MCAP(#38)と Azure の「出来事ごとに時刻と増える連番」(#33)で、整数時刻と連番という考え方の原典を足した。主キーの具体形は親の判断。
- **フロア併記**: JSON と Parquet の比は、データによって逆転する(SysFlow の minio は 0.96 倍で JSON(gzip) が小さい・Adaltas は Parquet の圧縮が効いていない)。「Parquet は何倍小さい」と一つの値で書かない。
