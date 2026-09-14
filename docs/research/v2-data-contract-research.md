# v2データ契約リサーチ答申(2026-08-30・Opusサブエージェント・全出典URL付き)

<!-- hdr:v1 -->
- **分野**: ソフトウェア工学 #29 | **重要度**: P2(親判断・2026-09-15 第191)
- **一次確認**: **D** = **出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る — 出典痕跡 6 件・URL 0 件。09-02 以降の中央値 62 に対して桁が違う
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> D6(観測データ契約)の意思決定材料。要件: 連続時間イベント駆動・全LLM入出力の恒久記録・
> 6時間毎checkpoint・N本並列ラン横断分析・v1資産(Chronicle/較正)の扱い。

## 結論(推奨)

**案(b)「新スキーマ(連続時刻)+Chronicle/較正向けエクスポータ」を推奨。**
v2要件(連続時間・異種ペイロード・LLM恒久記録・N本横断)はv1のstep固定ワイド設計と構造的に非互換。
一方Chronicle/較正は「入力表の形」にしか依存しないため、エクスポータ1層で資産を救える。
MCAP全面採用(案c)は時刻・多チャネル設計として理想的だが列指向でなく、4,400万行級の集計分析層の
全面書き直しが必要でコスト超過(この採否判断は推測)。

## 先行例(事実)

- **XES / IEEE 1849**(プロセスマイニング標準・2023改訂): log>trace>eventの3階層+全てkey-value属性・
  意味付けはextension機構に外出し。**コア最小+拡張で語彙を足す**進化方式はv2の長期語彙拡張と相性良。
- **ABMフレームワーク**(Mesa DataCollector/Agents.jl/FLAME GPU 2)は総じてtick同期・集計指向でv2要件を満たさない。
  Agents.jlの`ensemblerun!`はアンサンブル一級市民の前例。
- **AgentSociety**(1万体・500万インタラクション)が最近接先行: ローカル=Avro追記+DB=SQLite/PostgreSQL選択の二層。
  LLM生入出力の恒久記録を標準化した例は見つからず。
- **イベントソーシングのスキーマ進化5戦術**(arXiv 2104.01146): versioned events / weak schema / upcasting /
  in-place transformation / copy-and-transform。実務はV1/V2型分割+読み側upcasterが定番。

## フォーマット比較(要点)

| | 追記書込 | 時刻範囲クエリ | N本横断 |
|---|---|---|---|
| Parquet継続 | △(小ファイル列+コンパクションで回避) | ○ | ◎ hive_partitioning |
| Arrow IPC stream | ◎ | △ 自前索引 | △ |
| MCAP | ◎(fastwrite) | ◎ ChunkIndex | × 自前 |
| DuckDB直書き | ×(複数プロセス書込非対応・予定なし) | ◎ | ×(読み側としては最適) |
| JSONL+圧縮 | ◎ | × | △ |

- 横断読みの実務: DuckDB `read_parquet('runs/*/*.parquet', hive_partitioning=true)`(プルーニング実測30倍)・
  Polars `scan_parquet`+`include_file_paths`(ファイルパスを列化=run_id埋め込みが自然)。

## LLM入出力の記録標準(事実)

- **OpenTelemetry GenAI semconv**(大半Development状態): Required=`gen_ai.operation.name`/`gen_ai.provider.name`・
  Recommended=`gen_ai.usage.input_tokens/output_tokens`・`gen_ai.conversation.id`・
  Opt-in=`gen_ai.input.messages`/`gen_ai.output.messages`(本文記録)。`invoke_agent`/`execute_tool`/
  `create_memory`/`search_memory`の語彙あり。
- LangSmith: `trace_id`+`dotted_order`(={time}{run-uuid}連結で全順序化)・外部時刻体系の注入余地あり。
- **シム内時刻とLLM呼び出しの対応付けの標準前例は発見できず**→独自namespace属性(`sim.t_ns`/`sim.run_id`/
  `sim.agent_id`)をGenAI spanに載せるのが定石(推測)。

## 時刻設計(事実+推測)

1. **float秒でなく整数ナノ秒**(MCAPがuint64 ns+ユーザー定義epoch・浮動小数点は環境間決定性なし)
2. **同時刻の全順序化**: 主キーは`(t_ns, seq)`複合(グローバルカウンタ・arXiv 2105.00069の無バイアス全順序)
3. **checkpoint**: 対応イベントストリーム位置(`last_event_seq`)+スキーマ版を必ず持たせ・派生値は入れない
4. 任意時刻tの状態=直前checkpoint+seq範囲イベント差分で読み取り専用再構成(再実行不要)

## 3案比較

| 判断軸 | (a) v1 L1互換 | **(b) 新スキーマ+エクスポータ** | (c) MCAP等既製標準 |
|---|---|---|---|
| 書込性能 | △ step列が歪む | ○ hiveパーティション+コンパクション | ◎ |
| 分析容易性 | ○ 既存流用 | ◎ DuckDB/Polarsそのまま | △ 全走査 |
| v1資産再利用 | ◎ | ○ エクスポータ1層 | × 全面書き直し |
| スキーマ進化 | × 破壊的 | ◎ versioned events+upcaster | ◎ |
| N本横断 | △ run_id設計なし | ◎ | × 自前 |
| LLM恒久記録 | × | ○ 別ストリーム(GenAI semconv準拠) | ○ |

## 推奨(b)の具体形(設計提案・推測含む)

- **コア列(不変契約)**: `run_id, t_ns(uint64), seq(uint64), kind, schema_ver, agent_id, x, y, payload`。
  `(t_ns, seq)`=全順序主キー。`step`は`t_ns`から導出する仮想列(v1較正互換)。
- **ストリーム3分離**: `events`(高頻度・列指向)/`llm_calls`(GenAI semconv準拠+sim.t_ns等)/
  `checkpoints`(last_event_seq+schema_ver)。
- **物理配置**: `runs/run_id=<id>/sim_day=<d>/hour=<h>/part-*.parquet`・小ファイル追記+日次コンパクション。
- **進化戦術**: kindに版(versioned events)+読み側upcaster。既存ファイルは書き換えない。
- **MCAPは設計の借用のみ**(ns整数時刻・ユーザー定義epoch・chunk index)。

## 主要出典

MCAP spec/mcap.dev/ROS2既定化・IEEE 1849-2023(XES)・Mesa datacollection・Agents.jl API・
FLAME GPU 2 docs・arXiv 2104.01146(イベントソーシング進化)・Kurrent snapshots・Arrow IPC docs・
ARROW-18171・DuckDB concurrency/hive/pruning 30x・polars scan_parquet/hive・OTel GenAI semconv repo/
gen-ai-spans・LangSmith Run schema・arXiv 2105.00069(全順序)・OASIS(arXiv 2411.11581)・
AgentSociety(arXiv 2502.08691)+storage.avro docs。(URLはリサーチ実行ログに完全版)
