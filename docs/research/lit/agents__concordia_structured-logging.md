# Concordia(Google DeepMind)— 構造化ログとエンティティの検査(GM ログの粒度・再生の可否)

- リンク: https://github.com/google-deepmind/concordia | 分野: ソフトウェア工学 #29 / ABM 方法論 #21 | 重要度: **P1**
- **一次確認**: **サブ実読**(2026-09-17・`README.md` / `CHEATSHEET.md` / `CHANGELOG.md` の 3 本を raw で取得して読解)。**親未確認**。**コード本体(`concordia/utils/structured_logging.py`・`utils/log_viewer.html`)は未読**。**2.4.0 のリリース日も未確認**。論文(Vezhnevets et al.)は本メモの対象外。
- 命名に年が無いのは資料が継続更新のドキュメントだから(`gameeng__unreal_ai-perception` と同じ扱い)。

## 主張(claim)

シミュレーションの記録は **1 個の構造化 JSON**(`SimulationLog`)であり、読み口は **API(`AIAgentLogInterface`)+ CLI(`concordia-log`)+ HTML 1 枚(`log_viewer.html`)**の 3 段で後付けされた。**「replay(再生)」という語は README・CHEATSHEET・CHANGELOG のどこにも無い**。巻き戻しに相当するのは **checkpoint からの復元**(`get_state` / `set_state`)。

## 機構(mechanism)— ログの粒度は 4 次元

CLI の引数がそのまま次元になっている:

```
concordia-log components sim.json --entity Alice --component __act__ --key Key --step 3
```

→ **entity × step × component × key**。他のサブコマンド: `overview` `actions` `context` `step` `search` `memories` `entities` `timeline` `dump`。
`dump sim.json | jq '.[] | .data.__act__.Value'` のように jq へ流せる。**画像は既定でストリップ**("Base64 image data is stripped unless `--include-images` is passed")。

API 側(CHEATSHEET「Analyzing Simulation Logs」):

```python
log = simulation.play(return_structured_log=True)
interface = AIAgentLogInterface(log)
```

デバッグ手順として並ぶメソッド: `get_overview()` → `get_entity_actions(name)` → `get_entity_action_context(name, step)` → **`get_entity_timeline(name)`** → `get_step_summary(step, include_content=True)` → `search_summaries('keyword')` → `search_entries('keyword')` → `get_entry_content(entry_index=N)`。他に `filter_entries(...)` `get_entity_memories(name)` `get_game_master_memories()`。

保存・復元:

```python
with open('/tmp/simulation_log.json', 'w') as f:
    f.write(log.to_json())
log = SimulationLog.from_json(open('/tmp/simulation_log.json').read())
```

**`get_entity_timeline(name)` が個体カルテ、`get_step_summary(step)` が時刻断面**。つまり **「体で切る」「時刻で切る」の 2 軸が最初から API にある**。

## 状態の保存(checkpoint)

CHEATSHEET「State Management (Required for Checkpointing)」で、各 component が `get_state()` / `set_state()` を実装する。記憶の移送も同じ口:

```python
temp_memory = copy.deepcopy(source_entity.get_component("__memory__").get_state())
target_entity.get_component("__memory__").set_state(temp_memory)
```

## CHANGELOG からの事実(バージョンつき)

| 版 | 逐語 | 読み方 |
|---|---|---|
| 2.4.0 | "**Add generic log_viewer.html and simplify the Simulation.play API.**" / "**Add log analysis CLI**" / "Add support for logs produced by the asynchronous engine to the generic log viewer." | **読み口は後付け**(先に記録・あとで読み口) |
| 2.4.0 | "**Add dynamic state editing in the visual interface** and additional visualization improvements" | **UI から状態を編集できる**=v2 の「観測は世界を 1 バイトも変えない」と逆。**採らない道** |
| 2.4.0 | "**Add missing variables in get_state/set_state methods for all components.**" / "**Fixing scene serialisation error that was crashing jobs after restoration from a checkpoint.**" / "generic simulation now saves more info in checkpoints" | **全 component の状態保存に漏れがあり、復元後に落ちる事故が実際に起きた**。v2 の T2-c(checkpoint 自己整合)の価値の外部裏づけ |
| 2.4.0 | "**Fix broken HTML log rendering due to broken regex in structured_logging_html.py.**"(本文はエスケープのバグでシミュレーション HTML ログが空になっていた旨を続ける)/ "Fix deduplication for large images in structured_logging." | **計器そのものが黙って空になる事故**。v1 の「内省空バグ」と同型 |
| 2.3.0 | "**add structured logging**" / "Add option on generic simulation.play to produce new style structured logs. **No change to default behavior.**" / "Replace print() statements with absl.logging" | **新形式は既定を変えずに入れた**=v2 の「切替口・既定バイト不変」と同じ作法 |
| 2.1.0 | "**Adding a callback to get the state of the simulation after every step**"(独自 checkpoint 用)/ "Add option to **return raw log** from simulation.play" / "Add option to remove duplicates, when extracting data from the logs" | 毎ステップの状態取得はコールバックで外出し=**基盤側に checkpoint 方針を焼き込まない** |
| 1.8.0 | "**Make it optional to include full episode summaries in HTML logs and turn it off for the contest environments.**"(既定は変えない) | **重い場面ではカルテの粒度を落とす切替口**の先行 |
| 1.7.0 | "**Add a log that combines the main GM log and all the scene logs into one, sorted by date.**" / "Implement `get_last_log` in `EntityAgent`." / "Add default error logging to all measurement channels of component logging." | **GM ログと場面ログを時刻順に 1 本へ併合**=v2 の「4 系統を 1 本の時刻順に併合」(答申 §2 O1)と同型 |
| 1.8.6 | "Add ability to save and load rational and basic agents to/from json." | 体単位の直列化 |

## 効く箇所(seam)

- **M1 の読み口の形**: **CLI が先・HTML 1 枚が後**。GUI は作らなくてよい。
- **粒度の切替口**(1.8.0・画像ストリップ)は答申 §2 O10 の直接の先行。
- **計器が空になる検査**(答申 §2 O16)の根拠は 2.4.0 の修正記録。
- **「再生」の語が無い**ことは重要: **v2 のテープ再生(同一入力 → バイト一致)は Concordia より強い保証**で、M1 はその上に読み口だけ足す形になる。

## 「結論でなく機構として」の入れ方

- **借りない**: UI からの状態編集・prefab 構成・GM の語彙。
- **借りる**: (1) **記録は 1 個の構造化 JSON、読み口は後付け**。(2) **entity × step × component × key の 4 次元**。(3) **既定を変えない切替口で粒度を落とす**。(4) **GM ログと場面ログを時刻順に 1 本へ**。

## 数値

**なし**(本メモの資料にバイト数・件数の記載は無い)。ログ 1 件あたりのバイト数は**空欄**。

## 批判・限界

- ドキュメントと CHANGELOG のみで、**コード本体は未読**。`AIAgentLogInterface` の実装が実際に何を保持するかは確認していない。
- **規模が違う**: Concordia の例は `{'total_entries': 15, 'total_steps': 5, 'entities': ['Alice', 'Bob', 'default rules']}`。**40 万体の話ではない**ので、抽出の議論は Concordia から借りられない(そこは OpenTelemetry 側)。
- 版ごとの日付が CHANGELOG に無く、本メモは版番号でしか位置づけられない。

## 関連

[[agents__park2023_generative-agents-replay]](同じ問いの LLM 社会シミュ側)・[[transport__matsim-via_agent-facility-queries]](個体と場所の 2 クエリ)・`../v2-micro-observation-research.md` §1-2
