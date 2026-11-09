# 心の区分が外の列を読む所の数え直し 2026-11-09

> [返事その 7](../design/prompt-2026-11-09-reply7.md) §4-2 の 2 に答える一覧です。設計役(Opus 5.5)がリポの走査の道具で数えました。作業木の HEAD は `14b151a` です。コードは 1 行も変えていません。
> 機械で読める同じ一覧は [mind-world-reads-2026-11-09.json](mind-world-reads-2026-11-09.json) です(後で試験で固定するためのもの)。どのファイルが心の区分かは[最終の全ファイルの表](package-map-final-2026-11-09-files.md)によります。
> この一覧は「言えること・言えないこと」の「全知の読み」の行から引かれます(記録 2-33)。

## 0. 要旨

1. 道具(`state_ledger_ast.scan` の strict)の数は **82 か所**です。今のファイルで 13 本、移した後のモジュールで 14 個、列は 22 種類です。持ち主の内訳は world 74・act 7・economy 1 です。
2. このうち 8 か所は、列と同じ名の別の物(記憶の行・出来事・会話のセッション)の欄でした。道具は名前で数えるので区別できません。印「別物」を付けました。
3. 道具が数えない読みが 1 か所あります。`engine/store_choice.py:94` の `world.pois.price`(店の値段)です。左辺が `self.price` なので、道具は同じ列の書き直し(自己更新)と見なして外します。照らし合わせの例に挙がった読みで、案 K の 54 か所には入っています。
4. 別物を除き、数えない 1 か所を足すと、列の本当の読みは **75 か所**です。今のファイルで 10 本、移した後のモジュールで 10 個、列は 23 種類です。
5. 照らし合わせの約 77 か所は、案 K が表に載せた 11 個のモジュールの分に当たります。この数え方でも、その 11 個は 77 か所でした。残りの 5 か所は案 K の表に無い 3 つのモジュール(描く側 3 か所・候補の源 1 か所・`events/body` 1 か所)にあり、5 か所とも「別物」です。
6. 案 K の 54 か所は案 K 自身の AST で数えた下限です。同じ 11 個のモジュールで、この数え方は 23 か所多くなりました(77 と 54)。多い分は `f("列")` の形 9 か所(`memory.py:470-484`)・名前の表を回す読み 12 か所(`change_detect.py` の空腹・疲れ・暑さ)・`field("kind")` の形 2 か所(`classical.py`)・`getattr(ev, "cell")` 1 か所(`memory.py:1115`・別物)の 24 か所です。店の値段の 1 か所(`store_choice.py:94`)は道具が数えないので、その分 1 か所少なくなります。
7. 照らし合わせが挙げた例は 3 つとも確かめました(§5)。`classical.py` の本人のセル・活動・居る店・空腹・乗車の状態・性・年齢は入っています。`relations.py` の知人の位置 `cell`・`xy` も入っています。`store_choice.py` の店の値段は道具の外です(3 の 1 か所)。

## 1. 数え方の手順

1. `PYTHONPATH` を作業木の `src` にして、`shibuya.engine.state_ledger_ast.scan(root)` を呼びました。`root` は `src/shibuya`、`files` と `names` は渡していません(既定=`build/` を除く全部・宣言の全部の列)。使ったのは戻りの `ScanResult.strict`(列名 → 読みの場所)だけです。
2. 列の持ち主は案 K の分け方です(案 K §5-1・案 K の作業の表)。`agents` の 82 列を world 35・act 12・economy 2・mind 33 に分け、`cells`・`pois`・知覚の列(`perception/state.py`)は world にしました。分け方は §6 にあります。同じ名の列は `cell` と `node`(`agents` と `pois`)の 2 つで、持ち主はどちらも world です。
3. 読みの場所のファイルを[最終の全ファイルの表](package-map-final-2026-11-09-files.md)の包みに当てました。割るファイルは、読みの行を囲む最上位の関数・クラス(`Renderer` はメソッド)から割り先を引きました(付属の表 §4)。包みが mind で、列の持ち主が mind でない所を数えました。
4. 読みの形と手前の式は、`scan` と同じ分かれ道で AST を見直して付けました。付けた形の数は `scan` の数と 1 か所ずつ一致します。
5. 道具が数えない読みは、心の区分のファイルの属性の読みのうち、`scan` が自己更新として外した所と、手前の式が SoA らしくない所(loose だけ)を別に洗いました(§4)。
6. 走査したファイルは 244 本(`build/` を除く)。`scan` の strict の読みは全部で 841 か所、そのうち心の区分のファイルは 237 か所(自分の列 155・外の列 82)でした。解決できない動的な読みは 7 か所で、全部 `UNRESOLVED_ALLOW` に載っています。

## 2. ファイルごとの数

| 今のファイル | 移した後のモジュール | か所 | うち別物 | 列(か所) | 案 K の 54 の数 |
|---|---|---:|---:|---|---:|
| `engine/classical.py` | `mind/judge/classical.py` | 24 | 0 | `cell` 6・`activity` 4・`poi_ref` 3・`hunger` 3・`kind` 2・`transit_state` 2・`age` 2・`sex` 2 | 22 |
| `engine/memory.py` | `mind/memory/memory.py` | 21 | 1 | `poi_ref` 6・`cell` 5・`queue_poi` 2・`last_action` 2・`last_result` 2・`talk_partner` 1・`intent_kind` 1・`intent_target` 1・`last_result_tick` 1 | 11 |
| `engine/change_detect.py` | `mind/system1/change_detect.py` | 14 | 0 | `fatigue` 4・`hunger` 4・`thermal` 4・`density_stage` 1・`cell` 1 | 2 |
| `engine/relations.py` | `mind/relations/layer.py` | 7 | 0 | `cell` 5・`xy` 2 | 7 |
| `engine/store_choice.py` | `mind/judge/store_choice.py` | 3 | 0 | `cell` 1・`money` 1・`hunger` 1 | 4 |
| `perception/renderer.py` | `mind/percept/draw.py` | 3 | 3 | `kind` 2・`cell` 1 | — |
| `engine/memory_store.py` | `mind/memory/memory_store.py` | 2 | 2 | `kind` 1・`cell` 1 | 2 |
| `perception/renderer.py` | `mind/percept/notice.py` | 2 | 0 | `open_from` 1・`open_to` 1 | 2 |
| `engine/decision/layer.py` | `mind/judge/decision/layer.py` | 1 | 0 | `cell` 1 | 1 |
| `engine/decision/sources.py` | `mind/judge/decision/sources.py` | 1 | 1 | `kind` 1 | — |
| `engine/events/body.py` | `mind/memory/body_events.py` | 1 | 1 | `cell` 1 | — |
| `engine/familiarity.py` | `mind/memory/familiarity.py` | 1 | 0 | `cell` 1 | 1 |
| `engine/relations_people.py` | `mind/relations/people.py` | 1 | 0 | `cell` 1 | 1 |
| `engine/wom.py` | `mind/memory/wom.py` | 1 | 0 | `cell` 1 | 1 |
| 計 | | 82 | 8 | | 54 |

`renderer.py` は 2 つの割り先に分かれます(描く側 `mind/percept/draw.py` 3 か所・看板の気づき `mind/percept/notice.py` 2 か所)。

## 3. 列ごとの数

| 列 | 置き場 | 持ち主 | か所 | うち別物 | 読むモジュール |
|---|---|---|---:|---:|---|
| `cell` | agents・pois | world | 25 | 4 | judge/classical 6・memory/memory 5・relations/layer 5・system1/change_detect 1・judge/decision/layer 1・memory/body_events 1・memory/familiarity 1・memory/memory_store 1・relations/people 1・judge/store_choice 1・memory/wom 1・percept/draw 1 |
| `poi_ref` | agents | world | 9 | 0 | memory/memory 6・judge/classical 3 |
| `hunger` | agents | world | 8 | 0 | system1/change_detect 4・judge/classical 3・judge/store_choice 1 |
| `kind` | agents | world | 6 | 4 | judge/classical 2・percept/draw 2・judge/decision/sources 1・memory/memory_store 1 |
| `fatigue` | agents | world | 4 | 0 | system1/change_detect 4 |
| `thermal` | agents | world | 4 | 0 | system1/change_detect 4 |
| `activity` | agents | world | 4 | 0 | judge/classical 4 |
| `transit_state` | agents | world | 2 | 0 | judge/classical 2 |
| `age` | agents | world | 2 | 0 | judge/classical 2 |
| `sex` | agents | world | 2 | 0 | judge/classical 2 |
| `queue_poi` | agents | world | 2 | 0 | memory/memory 2 |
| `last_action` | agents | act | 2 | 0 | memory/memory 2 |
| `last_result` | agents | act | 2 | 0 | memory/memory 2 |
| `xy` | agents | world | 2 | 0 | relations/layer 2 |
| `density_stage` | cells | world | 1 | 0 | system1/change_detect 1 |
| `talk_partner` | agents | world | 1 | 0 | memory/memory 1 |
| `intent_kind` | agents | act | 1 | 0 | memory/memory 1 |
| `intent_target` | agents | act | 1 | 0 | memory/memory 1 |
| `last_result_tick` | agents | act | 1 | 0 | memory/memory 1 |
| `money` | agents | economy | 1 | 0 | judge/store_choice 1 |
| `open_from` | pois | world | 1 | 0 | percept/notice 1 |
| `open_to` | pois | world | 1 | 0 | percept/notice 1 |
| `price`(道具の外) | pois | world | (1) | 0 | judge/store_choice 1 |

## 4. 道具が数えない読み

### 4-1 自己更新と見なされて外れた読み(数え直しに足す 1 か所)

| ファイル:行 | 列 | 手前の式 | 行の文 | 印 |
|---|---|---|---|---|
| `engine/store_choice.py:94` | `price` | `world.pois` | `self.price = np.asarray(world.pois.price, dtype=np.int64)` | 数えない読み(店の値段を全員が読む形) |

- 道具の規則は「左辺と同じ名の属性が右辺にあれば自己更新」です(`state_ledger_ast._is_self_update`)。`self.price = np.asarray(world.pois.price, ...)` は左辺の `self` が SoA ではないのに、この規則に当たります。
- 同じ規則で外れた読みは心の区分にほかに 5 か所あります(`memory.py:580`・`581`・`663` の `it_.kind`)。どれも記憶の行の欄で、SoA の列ではありません。
- 道具を直すかは本文の聞きたいことに書きました(直せば 1 か所が strict に入ります)。

### 4-2 strict に入らない読み(loose だけ・65 か所)

手前の式が SoA らしくない読みです。数え直しには入れていません。中身は次のとおりです。

| ファイル | 手前の式 | か所 | 読んでいる物 |
|---|---|---:|---|
| `engine/calendar2/port.py` | `c` | 2 | 候補・選択の行(`Candidate`・`Choice`)。`memory_store.py` だけは想起の手がかり `Cue` |
| `engine/calendar3/port.py` | `c` | 2 | 候補・選択の行(`Candidate`・`Choice`)。`memory_store.py` だけは想起の手がかり `Cue` |
| `engine/chooser.py` | `context` | 4 | 選び手の文脈 `ChoiceContext`(呼び手が SoA から詰めた空腹・値段・所持金) |
| `engine/contact/port.py` | `c` | 2 | 候補・選択の行(`Candidate`・`Choice`)。`memory_store.py` だけは想起の手がかり `Cue` |
| `engine/decision/layer.py` | `c` | 2 | 候補・選択の行(`Candidate`・`Choice`)。`memory_store.py` だけは想起の手がかり `Cue` |
| `engine/decision/layer.py` | `choice` | 7 | 選んだ候補 |
| `engine/decision/layer.py` | `ctx` | 4 | 判断の文脈(`ctx.cell`) |
| `engine/decision/ports.py` | `c` | 3 | 候補・選択の行(`Candidate`・`Choice`)。`memory_store.py` だけは想起の手がかり `Cue` |
| `engine/decision/sources.py` | `c` | 1 | 候補・選択の行(`Candidate`・`Choice`)。`memory_store.py` だけは想起の手がかり `Cue` |
| `engine/duties/port.py` | `c` | 3 | 候補・選択の行(`Candidate`・`Choice`)。`memory_store.py` だけは想起の手がかり `Cue` |
| `engine/memory.py` | `it` | 1 | 記憶の行 |
| `engine/memory_impression.py` | `e` | 1 | 印象の行 |
| `engine/memory_store.py` | `c` | 5 | 候補・選択の行(`Candidate`・`Choice`)。`memory_store.py` だけは想起の手がかり `Cue` |
| `engine/memory_store.py` | `ev` | 7 | 記憶の器に入る出来事 |
| `engine/relations.py` | `init` | 3 | 最初の辺(`InitialEdges`) |
| `engine/relations_people.py` | `init` | 2 | 最初の辺(`InitialEdges`) |
| `engine/store_choice.py` | `self` | 1 | `self.price`(4-1 で足した値段の写し) |
| `perception/renderer.py` | `me` | 4 | 本人の見え方(`Percept` の欄) |
| `perception/renderer.py` | `p` | 6 | 知覚 `Percept` |
| `perception/renderer.py` | `scene` | 4 | 場面の物 |
| `perception/renderer.py` | `w` | 1 | 起床の見え方 |

- 知覚 `Percept` の欄(`p.self_view.money` など)は、心に渡す口の値なので全知の読みではありません。
- `engine/chooser.py:198-202` の `context.hunger`・`context.price`・`context.money` は、呼び手が SoA から詰めて渡した値です。配列を渡した先の読みは道具の限界(`state_ledger_ast` の docstring)で、読みは呼び手の側で数えています。

## 5. 照らし合わせの例の確かめ

| 例 | 入っているか | 場所 |
|---|---|---|
| `classical.py` が本人のセル・活動・居る店・空腹・乗車の状態・性・年齢を読む | 入っている | `cell` 5・`activity` 4・`poi_ref` 3・`hunger` 3・`transit_state` 2・`sex` 2・`age` 2(ほかに `kind` 2 と店のセル `pois.cell` 1) |
| `store_choice.py` が店の値段を読む | 道具の外 | `store_choice.py:94` `world.pois.price`(§4-1)。道具が数えるのは店のセル・所持金・空腹の 3 か所 |
| `relations.py` が知人の位置を読む | 入っている | `cell` 5・`xy` 2(`partners_in_cell`・`choose_talk_partners`・`_same_cell_hits`・`_edge_view`・`copresent_step`・`acquaintance_candidates`) |

## 6. 列の持ち主の分け方(案 K)

| 持ち主 | 列の数 | 列 |
|---|---:|---|
| world | 35 | `cell`・`node`・`band`・`xy`・`path_next_node`・`target_node`・`edge_id`・`edge_s`・`kind`・`age`・`sex`・`hunger`・`fatigue`・`thermal`・`weight_kg`・`eer_kcal`・`since_meal_kcal`・`energy_balance`・`activity`・`talk_partner`・`transit_state`・`transit_ref`・`poi_ref`・`poi_since`・`queue_poi`・`queue_since`・`plan_flags`・`nav_ox`・`nav_oy`・`nav_of`・`nav_tgt`・`nav_t`・`nav_fi`・`nav_wait`・`nav_node` |
| act | 12 | `board_line`・`board_since`・`sleep_pending`・`intent_action`・`intent_target`・`intent_kind`・`intent_since`・`activity_until`・`activity_kind`・`last_action`・`last_result`・`last_result_tick` |
| economy | 2 | `money`・`holdings` |
| mind | 33 | `focus_target`・`focus_ttl`・`hunger_stage`・`fatigue_stage`・`thermal_stage`・`refractory_until`・`fam_thing`・`fam_first`・`fam_last`・`fam_visits`・`fam_exposures`・`mem_kind`・`mem_tick`・`mem_last`・`mem_cell`・`mem_partner`・`mem_object`・`mem_result`・`mem_importance`・`mem_n`・`sm_poi`・`sm_valence`・`sm_precision`・`sm_first`・`sm_last`・`sm_n`・`sm_source`・`rel_partner`・`rel_kind`・`rel_sign`・`rel_first`・`rel_last`・`rel_n` |
| world | 17 | `cells` 5 列・`pois` 9 列・知覚の列 3 列(`heading`・`task_flag`・`invocation_distance`) |

案 K の作業の表から写しました。案 K の本文 §5-1 の数(world 35・act 12・economy 2・mind 33)と合います。

## 7. 1 か所ずつ

印: 別物=列と同じ名の別の物の欄(SoA の列ではない)。pois の列=店の列 `pois.cell`。同名あり=`agents` と `pois` に同じ名の列があり、手前の式から agents の列と読んだもの。

| # | ファイル:行 | 移した後のモジュール | 関数 | 列 | 持ち主 | 読みの形 | 手前の式 | 印 | 行の文 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | `engine/change_detect.py:303` | `mind.system1.change_detect` | `ChangeDetector._cell_changes` | `density_stage` | world | 属性 X.列 | `world.cells` |  | `los_stage=world.cells.density_stage if self.los_from_stage else None)` |
| 2 | `engine/change_detect.py:317` | `mind.system1.change_detect` | `ChangeDetector._interoception` | `fatigue` | world | 名前の表を回す field(変数) | `agents.registry` |  | `stages = [agents.registry.field(sf).view(np.uint8) for _, sf in INTERO_VARS]` |
| 3 | `engine/change_detect.py:317` | `mind.system1.change_detect` | `ChangeDetector._interoception` | `hunger` | world | 名前の表を回す field(変数) | `agents.registry` |  | `stages = [agents.registry.field(sf).view(np.uint8) for _, sf in INTERO_VARS]` |
| 4 | `engine/change_detect.py:317` | `mind.system1.change_detect` | `ChangeDetector._interoception` | `thermal` | world | 名前の表を回す field(変数) | `agents.registry` |  | `stages = [agents.registry.field(sf).view(np.uint8) for _, sf in INTERO_VARS]` |
| 5 | `engine/change_detect.py:320` | `mind.system1.change_detect` | `ChangeDetector._interoception` | `fatigue` | world | 名前の表を回す field(変数) | `agents.registry` |  | `v = agents.registry.field(value_field)` |
| 6 | `engine/change_detect.py:320` | `mind.system1.change_detect` | `ChangeDetector._interoception` | `hunger` | world | 名前の表を回す field(変数) | `agents.registry` |  | `v = agents.registry.field(value_field)` |
| 7 | `engine/change_detect.py:320` | `mind.system1.change_detect` | `ChangeDetector._interoception` | `thermal` | world | 名前の表を回す field(変数) | `agents.registry` |  | `v = agents.registry.field(value_field)` |
| 8 | `engine/change_detect.py:372` | `mind.system1.change_detect` | `ChangeDetector._interoception_scoped` | `fatigue` | world | 名前の表を回す field(変数) | `agents.registry` |  | `v = agents.registry.field(value_field)[idx]` |
| 9 | `engine/change_detect.py:372` | `mind.system1.change_detect` | `ChangeDetector._interoception_scoped` | `hunger` | world | 名前の表を回す field(変数) | `agents.registry` |  | `v = agents.registry.field(value_field)[idx]` |
| 10 | `engine/change_detect.py:372` | `mind.system1.change_detect` | `ChangeDetector._interoception_scoped` | `thermal` | world | 名前の表を回す field(変数) | `agents.registry` |  | `v = agents.registry.field(value_field)[idx]` |
| 11 | `engine/change_detect.py:373` | `mind.system1.change_detect` | `ChangeDetector._interoception_scoped` | `fatigue` | world | 名前の表を回す field(変数) | `agents.registry` |  | `p = agents.registry.field(stage_field).view(np.uint8)[idx]` |
| 12 | `engine/change_detect.py:373` | `mind.system1.change_detect` | `ChangeDetector._interoception_scoped` | `hunger` | world | 名前の表を回す field(変数) | `agents.registry` |  | `p = agents.registry.field(stage_field).view(np.uint8)[idx]` |
| 13 | `engine/change_detect.py:373` | `mind.system1.change_detect` | `ChangeDetector._interoception_scoped` | `thermal` | world | 名前の表を回す field(変数) | `agents.registry` |  | `p = agents.registry.field(stage_field).view(np.uint8)[idx]` |
| 14 | `engine/change_detect.py:432` | `mind.system1.change_detect` | `ChangeDetector.detect` | `cell` | world | 属性 X.列 | `agents.registry` | 同名あり | `k = _CELL_WAKE(agents.registry.cell, self._cell_mask, self._wake_buf)` |
| 15 | `engine/classical.py:354` | `mind.judge.classical` | — | `kind` | world | 文字列 field("列") | `agents.registry` |  | `kind = np.asarray(agents.registry.field("kind"), dtype=np.int64)` |
| 16 | `engine/classical.py:371` | `mind.judge.classical` | — | `cell` | world | 属性 X.列 | `world.pois` | pois の列 | `poi_cell = np.asarray(world.pois.cell, dtype=np.int64)` |
| 17 | `engine/classical.py:405` | `mind.judge.classical` | — | `kind` | world | 文字列 field("列") | `self.agents.registry` |  | `kind = np.asarray(self.agents.registry.field("kind"), dtype=np.int64)` |
| 18 | `engine/classical.py:430` | `mind.judge.classical` | — | `poi_ref` | world | 属性 X.列 | `r` |  | `ref = np.asarray(r.poi_ref, dtype=np.int64)` |
| 19 | `engine/classical.py:431` | `mind.judge.classical` | — | `activity` | world | 属性 X.列 | `r` |  | `ok = (ref >= 0) & (np.asarray(r.activity) == int(Activity.SHOPPING))` |
| 20 | `engine/classical.py:433` | `mind.judge.classical` | — | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell = np.asarray(r.cell, dtype=np.int64)` |
| 21 | `engine/classical.py:441` | `mind.judge.classical` | — | `poi_ref` | world | 属性 X.列 | `r` |  | `if int(r.poi_ref[aid]) >= 0:` |
| 22 | `engine/classical.py:465` | `mind.judge.classical` | — | `hunger` | world | 属性 X.列 | `self.agents.registry` |  | `stage = hunger_stage_of(int(self.agents.registry.hunger[aid]))` |
| 23 | `engine/classical.py:485` | `mind.judge.classical` | — | `activity` | world | 属性 X.列 | `r` |  | `ok = (np.asarray(r.activity) != int(Activity.SLEEPING)) & (np.asarray(r.transit_state) == 0)` |
| 24 | `engine/classical.py:485` | `mind.judge.classical` | — | `transit_state` | world | 属性 X.列 | `r` |  | `ok = (np.asarray(r.activity) != int(Activity.SLEEPING)) & (np.asarray(r.transit_state) == 0)` |
| 25 | `engine/classical.py:489` | `mind.judge.classical` | — | `hunger` | world | 属性 X.列 | `r` |  | `np.asarray(r.hunger, dtype=np.int64)[ok], side="right")` |
| 26 | `engine/classical.py:498` | `mind.judge.classical` | — | `hunger` | world | 属性 X.列 | `r` |  | `stage = hunger_stage_of(int(r.hunger[aid]))` |
| 27 | `engine/classical.py:504` | `mind.judge.classical` | — | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell = int(r.cell[aid])` |
| 28 | `engine/classical.py:522` | `mind.judge.classical` | — | `age` | world | 属性 X.列 | `r` |  | `p0 = self.prior.row(int(r.sex[aid]), bool(self.employed[aid]), int(r.age[aid]), slot)` |
| 29 | `engine/classical.py:522` | `mind.judge.classical` | — | `sex` | world | 属性 X.列 | `r` |  | `p0 = self.prior.row(int(r.sex[aid]), bool(self.employed[aid]), int(r.age[aid]), slot)` |
| 30 | `engine/classical.py:525` | `mind.judge.classical` | — | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell = int(r.cell[aid])` |
| 31 | `engine/classical.py:541` | `mind.judge.classical` | — | `transit_state` | world | 属性 X.列 | `r` |  | `ids = np.flatnonzero((np.asarray(r.transit_state) == 0)` |
| 32 | `engine/classical.py:542` | `mind.judge.classical` | — | `activity` | world | 属性 X.列 | `r` |  | `& (np.asarray(r.activity) != int(Activity.SLEEPING)))` |
| 33 | `engine/classical.py:546` | `mind.judge.classical` | — | `age` | world | 属性 X.列 | `r` |  | `p0 = np.stack([self.prior.row(int(r.sex[i]), bool(self.employed[i]), int(r.age[i]), slot)` |
| 34 | `engine/classical.py:546` | `mind.judge.classical` | — | `sex` | world | 属性 X.列 | `r` |  | `p0 = np.stack([self.prior.row(int(r.sex[i]), bool(self.employed[i]), int(r.age[i]), slot)` |
| 35 | `engine/classical.py:549` | `mind.judge.classical` | — | `cell` | world | 属性 X.列 | `r` | 同名あり | `self.m_place[self._place_kind(int(i), int(r.cell[i]))]` |
| 36 | `engine/classical.py:629` | `mind.judge.classical` | — | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell = int(r.cell[aid])` |
| 37 | `engine/classical.py:732` | `mind.judge.classical` | — | `poi_ref` | world | 属性 X.列 | `r` |  | `ref = int(r.poi_ref[aid])` |
| 38 | `engine/classical.py:733` | `mind.judge.classical` | — | `activity` | world | 属性 X.列 | `r` |  | `return bool(ref >= 0 and int(r.activity[aid]) == int(Activity.SHOPPING) and eatery[ref])` |
| 39 | `engine/decision/layer.py:172` | `mind.judge.decision.layer` | — | `cell` | world | 属性 X.列 | `world.pois` | pois の列 | `self._poi_cell = (np.asarray(world.pois.cell, dtype=np.int64) if world is not None` |
| 40 | `engine/decision/sources.py:119` | `mind.judge.decision.sources` | — | `kind` | world | 文字列 getattr(X, "列") | `it` | 別物(想起した記憶の行 `it` の種類) | `w = kind_words.get(int(getattr(it, "kind", -1)))` |
| 41 | `engine/events/body.py:201` | `mind.memory.body_events` | `BodyEventLink.conversation_end` | `cell` | world | 文字列 getattr(X, "列") | `s` | 別物(閉じた会話のセッション `s` のセル) | `sc = int(getattr(s, "cell", -1))` |
| 42 | `engine/familiarity.py:248` | `mind.memory.familiarity` | — | `cell` | world | 属性 X.列 | `agents.registry` | 同名あり | `cell = np.asarray(agents.registry.cell, dtype=np.int64)` |
| 43 | `engine/memory.py:470` | `mind.memory.memory` | — | `cell` | world | 文字列 f("列") | `f` | 同名あり | `q_cell = int(f("cell")[i])` |
| 44 | `engine/memory.py:471` | `mind.memory.memory` | — | `talk_partner` | world | 文字列 f("列") | `f` |  | `q_partner = int(inviter) if int(inviter) >= 0 else int(f("talk_partner")[i])` |
| 45 | `engine/memory.py:473` | `mind.memory.memory` | — | `intent_kind` | act | 文字列 f("列") | `f` |  | `ik = int(f("intent_kind")[i]) if has_intent else 0` |
| 46 | `engine/memory.py:474` | `mind.memory.memory` | — | `intent_target` | act | 文字列 f("列") | `f` |  | `it = int(f("intent_target")[i]) if has_intent else -1` |
| 47 | `engine/memory.py:479` | `mind.memory.memory` | — | `poi_ref` | world | 文字列 f("列") | `f` |  | `elif int(f("poi_ref")[i]) >= 0:` |
| 48 | `engine/memory.py:480` | `mind.memory.memory` | — | `poi_ref` | world | 文字列 f("列") | `f` |  | `q_obj = int(f("poi_ref")[i])` |
| 49 | `engine/memory.py:482` | `mind.memory.memory` | — | `queue_poi` | world | 文字列 f("列") | `f` |  | `q_obj = int(f("queue_poi")[i])` |
| 50 | `engine/memory.py:483` | `mind.memory.memory` | — | `last_action` | act | 文字列 f("列") | `f` |  | `q_kind = ACTION_KIND.get(int(f("last_action")[i]), 0)` |
| 51 | `engine/memory.py:484` | `mind.memory.memory` | — | `last_result` | act | 文字列 f("列") | `f` |  | `q_result = int(f("last_result")[i])` |
| 52 | `engine/memory.py:869` | `mind.memory.memory` | — | `cell` | world | 属性 X.列 | `agents.registry` | 同名あり | `cell = np.asarray(agents.registry.cell, dtype=np.int64)[aa]` |
| 53 | `engine/memory.py:969` | `mind.memory.memory` | — | `cell` | world | 属性 X.列 | `agents.registry` | 同名あり | `np.asarray([int(agents.registry.cell[int(agent_id)])]),` |
| 54 | `engine/memory.py:1018` | `mind.memory.memory` | — | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell_now = np.asarray(r.cell, dtype=np.int64)` |
| 55 | `engine/memory.py:1027` | `mind.memory.memory` | — | `last_result_tick` | act | 属性 X.列 | `r` |  | `ids = np.flatnonzero(np.asarray(r.last_result_tick) == t)` |
| 56 | `engine/memory.py:1029` | `mind.memory.memory` | — | `last_action` | act | 属性 X.列 | `r` |  | `act = np.asarray(r.last_action, dtype=np.int64)[ids]` |
| 57 | `engine/memory.py:1030` | `mind.memory.memory` | — | `last_result` | act | 属性 X.列 | `r` |  | `res = np.asarray(r.last_result, dtype=np.int64)[ids]` |
| 58 | `engine/memory.py:1040` | `mind.memory.memory` | — | `poi_ref` | world | 属性 X.列 | `r` |  | `poi_ref = np.asarray(r.poi_ref, dtype=np.int64)[ids]` |
| 59 | `engine/memory.py:1041` | `mind.memory.memory` | — | `queue_poi` | world | 属性 X.列 | `r` |  | `queue_poi = np.asarray(r.queue_poi, dtype=np.int64)[ids]` |
| 60 | `engine/memory.py:1084` | `mind.memory.memory` | — | `poi_ref` | world | 属性 X.列 | `r` |  | `ref = int(r.poi_ref[p])` |
| 61 | `engine/memory.py:1101` | `mind.memory.memory` | — | `poi_ref` | world | 属性 X.列 | `r` |  | `ref = int(r.poi_ref[int(p)])` |
| 62 | `engine/memory.py:1105` | `mind.memory.memory` | — | `poi_ref` | world | 属性 X.列 | `r` |  | `ref = int(r.poi_ref[x])` |
| 63 | `engine/memory.py:1115` | `mind.memory.memory` | — | `cell` | world | 文字列 getattr(X, "列") | `ev` | 別物(顕著な出来事 `ev`(salient の出来事の物)のセル) | `c = int(getattr(ev, "cell", -1))` |
| 64 | `engine/memory_store.py:392` | `mind.memory.memory_store` | — | `kind` | world | 属性 X.列 | `v` | 別物(記憶の器の行 `MemoryView` の種類) | `row=int(v.row), last_tick=int(v.when_ns) // int(ns_per_step), kind=int(v.kind), partner=int(v.partne…` |
| 65 | `engine/memory_store.py:393` | `mind.memory.memory_store` | — | `cell` | world | 属性 X.列 | `v` | 別物(記憶の器の行 `MemoryView` のセル) | `obj=int(v.obj), result=int(v.result), cell=int(v.cell), gist=str(v.annotation), valence=int(v.valenc…` |
| 66 | `engine/relations.py:869` | `mind.relations.layer` | `RelationLayer.partners_in_cell` | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell = np.asarray(r.cell, dtype=np.int64)` |
| 67 | `engine/relations.py:931` | `mind.relations.layer` | `RelationLayer.choose_talk_partners` | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell = np.asarray(r.cell, dtype=np.int64)` |
| 68 | `engine/relations.py:934` | `mind.relations.layer` | `RelationLayer.choose_talk_partners` | `xy` | world | 属性 X.列 | `r` |  | `xy = np.asarray(r.xy, dtype=np.float64)` |
| 69 | `engine/relations.py:999` | `mind.relations.layer` | `RelationLayer._same_cell_hits` | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell = np.asarray(r.cell)` |
| 70 | `engine/relations.py:1026` | `mind.relations.layer` | `RelationLayer._edge_view` | `cell` | world | 属性 X.列 | `agents.registry` | 同名あり | `cell = np.asarray(agents.registry.cell)` |
| 71 | `engine/relations.py:1076` | `mind.relations.layer` | `RelationLayer.copresent_step` | `xy` | world | 属性 X.列 | `r` |  | `xy = np.asarray(r.xy, dtype=np.float64)` |
| 72 | `engine/relations.py:1127` | `mind.relations.layer` | `RelationLayer.acquaintance_candidates` | `cell` | world | 属性 X.列 | `r` | 同名あり | `self._prev_cell = np.array(r.cell, copy=True)` |
| 73 | `engine/relations_people.py:130` | `mind.relations.people` | — | `cell` | world | 属性 X.列 | `r` | 同名あり | `cell = np.asarray(r.cell, dtype=np.int64)` |
| 74 | `engine/store_choice.py:93` | `mind.judge.store_choice` | — | `cell` | world | 属性 X.列 | `world.pois` | pois の列 | `self.poi_cell = np.asarray(world.pois.cell, dtype=np.int64)` |
| 75 | `engine/store_choice.py:174` | `mind.judge.store_choice` | — | `money` | economy | 属性 X.列 | `r` |  | `money = int(r.money[i])` |
| 76 | `engine/store_choice.py:175` | `mind.judge.store_choice` | — | `hunger` | world | 属性 X.列 | `r` |  | `if not (eat and hunger_stage_of(int(r.hunger[i])) >= 3):` |
| 77 | `engine/wom.py:252` | `mind.memory.wom` | — | `cell` | world | 属性 X.列 | `world.pois` | pois の列 | `np.asarray(world.pois.cell, dtype=np.int64), getattr(a, "cell_dist", None), source=source)` |
| 78 | `perception/renderer.py:202` | `mind.percept.draw` | `memory_item_text` | `kind` | world | 文字列 getattr(X, "列") | `item` | 別物(想起した記憶の行 `item` の種類) | `kind = int(getattr(item, "kind"))` |
| 79 | `perception/renderer.py:204` | `mind.percept.draw` | `memory_item_text` | `cell` | world | 文字列 getattr(X, "列") | `item` | 別物(想起した記憶の行 `item` のセル) | `cell = int(getattr(item, "cell"))` |
| 80 | `perception/renderer.py:1887` | `mind.percept.notice` | `Renderer._signage_body` | `open_from` | world | 属性 X.列 | `w.pois` |  | `frm = int(w.pois.open_from[j]) // MINUTES_PER_HOUR` |
| 81 | `perception/renderer.py:1888` | `mind.percept.notice` | `Renderer._signage_body` | `open_to` | world | 属性 X.列 | `w.pois` |  | `to = int(w.pois.open_to[j]) // MINUTES_PER_HOUR` |
| 82 | `perception/renderer.py:2253` | `mind.percept.draw` | `Renderer._with_memory_line` | `kind` | world | 文字列 getattr(X, "列") | `it` | 別物(想起した記憶の行 `it` の種類) | `(int(getattr(it, "first_tick", -1)), int(getattr(it, "kind")), int(getattr(it, "obj"))) for it in it…` |

関数の欄は割るファイルだけに書きました(割り先を決めた記号)。

## 8. 参考: 一時の区分(束ね)が心の外の列を読む所

一時の区分 `interim_bundles` は心の区分ではないので、上の数に入れていません。束ねは本人の判断を持つので、v3 で割るときの材料として数だけ載せます。同じ道具で 69 か所(world 64・act 5)です。

| 今のファイル | か所 |
|---|---:|
| `engine/calendar_self.py` | 25 |
| `engine/calendar2/layer.py` | 14 |
| `engine/contact/layer.py` | 14 |
| `engine/duties/layer.py` | 11 |
| `engine/calendar3/layer.py` | 5 |

## 9. 試験で固定するときの形(案)

- 固定するのは道具の出す一覧そのもの(§7 の 82 か所。別物も含む)です。同じ道具で数えるので、試験の結果がぶれません。
- 行の番号は直すたびに動くので、鍵は「移した後の道筋・関数・列」の組の数にします(json の `key_counts`)。試験は、道具の数が組ごとに一覧の数以下であることを確かめます。数が減ったら一覧も減らします(減らす向きにだけ動かす)。
- 新しい組や増えた組が出たら落とします。直す人は、読みを口に替えるか、理由を書いて一覧に足すかを選びます(足すのは決定の後だけ)。
- 道具の外の 1 か所(§4-1)は json の `not_counted_by_tool` に分けて載せました。道具を直すまでは、文字列の検査(その行の文が残っているか)で見張る形が使えます。

## 10. 確かめていないこと・限界

- 道具は列の名と手前の式で数えます。他人の行を読んだか(添字が本人か)は分かりません。かき乱しの試験(9-2 と一緒に入れる・記録 2-33)でしか分かりません。
- 配列を関数に渡した先の読みと局所の別名の先は数えていません(§4-2)。
- 案 K の持ち主の分け方は案 K の作業の表から写しました。分け方そのもの(例えば `activity` を world に置くか act に置くか)はこの文書では決めていません。
- 照らし合わせの数えのスクリプトはこの機械に無いので、約 77 か所・12 本の 12 本目がどれかは確かめていません。
