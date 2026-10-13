# 1-0 run_day の分解の実装の検収(検収役・Opus 5.5)

- 対象: 作業木 `1-0/run-day-decomp`(HEAD `ee3abc7` からの未コミットの差分)。比べる相手は本体の src(`f8e5ddf`・`git diff ee3abc7 HEAD -- src` は空)。
- 立場: 実装を見ていない検収役。実装役の道具(`probe_run.py`・`guard_runs.py`・`byte_check_10e.py` ほか)は使わず、自前の道具で回した。道具と生の出力は git の外の `data/runs/rev_1-0/`(道具は `tools/rev_*.py`)。
- 作業木のファイルは書き換えていない(この記録だけを足した)。途中から `PYTHONDONTWRITEBYTECODE=1` で回した。それより前の実行は、作業木の `__pycache__` に古い .pyc があれば書き直した可能性がある(ソースは変わっていないので推測では起きていない)。

## 0. 結論

- 判定: **条件つき受入**。
- 結果不変は独立に確かめた。7 構成(5,000 体 2 つを含む)と艦隊・再生・遅れ 2・再開(相手の側の状態ファイルからの再開を含む)のすべてで、final・呼数・checkpoint の behavior/full・checkpoint ごとの成分の digest(状態台帳の値)・診断の行・RunResult の全欄(壁時計を除く)・ランの最後の SoA の全列・テープの列が HEAD と同じだった。
- 「宣言の外を書いたら落ちる」に穴が 3 つある(§1 の 1〜3)。どれも今の結果は動かさないが、土台 1-1〜1-9 で新しく書く系(箱の形 `b.soa.agents…` で書く)に効く。条件は、1〜3 を負の対照つきで直すか、記録の「限界」に明記して親が残すと決めること。
- 状態台帳 187 行の鍵・道筋・型・軸は HEAD と同じ(違うのは AST の許可の 1 行だけ)。系の順と元の区間は草案 §2-2 と同じで、HEAD の L0〜E4 の実行文は 1 行も漏れていない。

## 1. 見つけた欠陥(重い順)

再現の道具は `data/runs/rev_1-0/tools/rev_loopholes.py`(系の `fn` を実行時に包んで差し込む。ファイルは変えない)と `rev_static.py`(系のモジュールに書いたと仮定した AST の検査)。合成世界 80 体・300 tick・記憶+関係+店+同席の腕で、T=200 に 1 回だけ差し込んだ。「A」は既定の実行、「B」は段 B の測り(`Probe(check=declared_check)`)を入れた実行。

| # | 抜け道 | 系 | 実行のたびに落ちるか(A・C) | 試験の形(B)で落ちるか | 静的(D)で見つかるか | final |
|---|---|---|---|---|---|---|
| L1 | `np.add.at(b.soa.agents.registry.money, …)`(resolve の外の ufunc.at・箱の形) | perceive_prepare | **落ちない** | 落ちる(`agents.money`) | **見つからない**(下の 1) | 動いた |
| L2 | `with write_permit.scope(None): R.set_refractory(…)` | checkpoint | **落ちない** | 落ちる(`agents.refractory_until`) | **見つからない** | 動いた |
| L3 | 凍結の前に作ったビュー(`registry.hunger[:]`)に書く | perceive_prepare | 落ちない | 落ちる | 形による(下の 5) | 動かず |
| L4 | scratch の中身をその場で書き換える(`plan.confirmed.action_code[...] = …`・書き手でない系) | phase_c(実行の前) | **落ちない** | **落ちない** | **見つからない** | **動いた** |
| L4b | `object.__setattr__(b.scratch, "outcome", …)` | memory | 落ちない | 落ちない | 見つからない | 動かず |
| L5 | `b.buffers.focus_request = 新しい配列`(宣言の無い系) | detect | 落ちない(Buffers に段 C が無い) | 落ちる | 読みの宣言の外なら D③ | 動かず |
| L6 | 外の状態を宣言の無い系が書く(`conv._next_id`・`arbiter._last_tick`) | phase_b | 落ちない(設計どおり) | 落ちる(2 件) | 箱の属性なら D③ | 動いた |
| L7 | drain から SoA を書く resolve の口 | drain | 落ちる(配列ごとの検査) | — | — | — |
| L8 | report から SoA を書く resolve の口 | report | 落ちる(読み取り専用) | — | — | — |
| L9 | 閉包の中の列を書く、宣言に無い口を素の import で呼ぶ | phase_c | 落ちない | 落ちない(列は許可の中) | **見つからない**(下の 6) | 動かず |
| L10 | 台帳の私物の辞書で配列の物を差し替える(`registry._arrays[...]`) | perceive_prepare | 落ちない | 落ちる | — | 動いた |
| L11 | 系の中から `write_permit.set_enabled(False)`(戻さない) | observe | 落ちない(以後のランは検査なし) | — | 見つからない | 動かず |
| L12 | 宣言の無い RunStats の欄を書く | phase_b | 落ちない | 落ちる | 書き方による(下の 7) | 動かず |

### 1. 箱の形の ufunc.at は A でも D でも捕まらない(L1・中)

- 段 A の ② は resolve の中の `_require_thawed` だけで、resolve の外の `ufunc.at` は旗を見ないので実行時に通る。草案 §2-6 は D ⑦ でこれを塞ぐ想定だった。
- 実装の D ⑦(`test_every_state_ufunc_at_in_resolve_checks_the_written_array`)は resolve の中だけを見る。resolve の外を見る既存の `tests/engine/test_add_at_guard.py` は根を `("world", "agents", "self.world", "self.agents")` で判定するので、`b.soa.agents.registry.money`・`r = b.soa.agents.registry; np.add.at(r.money, …)` を見つけない(`rev_static.py` で `_ufunc_at_targets` が 0 件を返した)。
- 今の系は前置きで `agents = b.soa.agents` と局所に結ぶので、今のコードには穴は無い。土台で箱の形で書く新しい系から効く。
- 直し方の案: `STATE_ROOTS` と別名の判定に `b.soa.agents`・`b.soa.world`・`box.soa.*` を足し、植えた行で落ちる負の対照を 1 本足す。

### 2. scratch の中身の書き換えはどの段も捕まえない(L4・中)

- 段 C は `TickScratch.__setattr__` だけを見る。段 B は `families=("soa", "ext", "stats", "buffers")` が既定で、`view_of` も scratch を渡さない。`declared_check` には `scratch.` の分岐があるが、通る道が無い(使われていない分岐)。
- 書き手でない phase_c が実行の前に `scratch.plan.confirmed.action_code` をその場で書き換えると、final が `d407095944819970 → b54f7d523e67510f` に動き、A・B・C・D のどれも落ちなかった。
- 直し方の案: 試験のときは `view_of` に scratch を渡し、`families` に `"scratch"` を足す。系の境目で中身の digest を取れば、宣言の外の書き換えは書いた系に帰属する。

### 3. 書きの許可を外す口が系と層から呼べる(L2・L11・中〜低)

- `write_permit.scope(None)` と `set_enabled(False)` は誰でも呼べる。静的な禁止は D ④ の `writable`・`thaw`・`_set_writeable`・`setflags` だけ。L2 では宣言の外の書きが実行時に通り、final が動いた。
- 直し方の案: D ④ を広げ、`core.write_permit` を import してよいのは状態のモジュール・`engine/systems/guard.py`・`conductor.py`・試験だけにする。

### 4. Buffers に段 C が無い(L5・低)

草案 §2-6 の C は「TickScratch・Buffers」。実装は `Buffers` を素の dataclass にした。宣言の外の差し替えや書きは B(試験)でしか落ちない。実装の記録 §2-4 は C を TickScratch だけと書いているので、草案との違いとして記録に足す。

### 5. D ⑥ は別名の多くの形を見ない(L3・低)

`test_no_layer_holds_a_soa_array_or_view_as_an_attribute` の判定 `_soa_array_expr` に 9 つの形を当てた。見つけたのは `agents.registry.cell[:]`・`b.soa.agents.registry.hunger` の 2 つ。見つけなかったのは `registry.arrays["hunger"]`・`getattr(registry, "hunger")`・`registry.field(変数)`・`r = agents.registry; self.x = r.hunger`・`np.asarray(r.hunger)`・タプルの代入・辞書に入れる、の 7 つ。草案も「AST の限界・B で落とす」と書いているので、限界として記録に書けば足りる。

### 6. D ① は `R.`・`RES.`・`resolve.` の別名しか見ない(L9・低)

`from shibuya.engine.resolve import revert_conversation` や `import shibuya.engine.resolve as RV` で呼ぶと `resolve_calls` が空になる。書く列が許可の中なら、実行時にも落ちない。

### 7. observe の積算の宣言と静的な検査が欠ける(低・診断だけ)

- observe は `occ_counts`・`occ_kind`・`occ_transit` を `append` で書くが、`writes.tally` は `occ_ticks` しか持たない。
- `static_check` はタプルの代入 `occ_ticks, occ_counts, … = rs.occ_ticks, …` の別名をたどらない。observe について見えた書きは `prev_sessions`・`prev_tape_misses` だけで、`diag_rows`・`sleep_counts`・`occ_*` は見えない。このため D ③ の「書き ⊆ 宣言」は検査の数が少ないまま通っている。
- probe の `STATS_NAMES` は `occ_counts`・`occ_kind`・`occ_transit`・`ledger_growth`・`state_files`・`frozen_sources_map` を持たないので、B でも見えない。

### 8. 段 B が見えない外の道筋が 7 本ある(低)

probe の `snapshot` で `item_digest` が例外になり、値が `ERR:…` の定数になる道筋が 7 本あった(記憶+関係+店の腕・T=300)。O25 `poi_resolver.chooser.last_habit`・`.stats`、O61 `runner.log`、O63 `renderer._tickc`、O64 `renderer.acquaintance_fn`・`.memory_recall`・`.named_closed_lookup`。どれもハッシュに入らない行(diag/no・discardable/derivable)だが、O64 の 3 本は組み立てで差し込む関数(草案 §3-3 の 6)の置き場なので、系が差し替えても B では見えない。記録に限界として書く。

### 9. 外の道筋の宣言が粗い(低・設計の注)

`writes.paths` の 179 個のうち 174 個が行や持ち主の `*`。宣言上の (系, 道筋) は 2,196 対で、観測(実装役の 6 構成)の 379 対の約 5.8 倍になる。草案 K9 の「宣言と検査は道筋の単位」に比べると、B が外の状態について捕まえる力は弱い。1-0 は行を割らない約束なので、話題ごとにまとめ直すときの課題として記録に足すのがよい。

### 10. 記録の数と記述の食い違い(記録)

- 「run.py の未使用 import 104 個を削除」: HEAD と作業木の `engine.run` の名前空間を比べると、消えた名前は 99 個(頂上の import が 187 → 88)。関数の中の import を含めると 103 個(205 → 103)。どちらも 104 にならない。
- `local-assignment.json` は `ledger_growth` を「end:close_final,report(系の局所)」に分けているが、実装では `RunStats.ledger_growth` の欄=箱にある。
- `SystemSpec.soa_declared`(「手で書いた writes.soa・閉包と食い違えば試験で落とす」)はどこからも設定されず、使われていない。D ② の試験は `make` が作った値を同じ関数と比べるので、常に真になる。宣言を手で書かない形にした以上、この欄は消すか、注で役目が無いことを書く。

## 2. 確かめたこと

### 2-1. 結果不変(独立の道具 `rev_run.py`・`rev_cmp.py`)

`cli.run` に同じ引数(`checkpoint_every=60`・`checkpoint_detail=True`・テープつき・両側 `PYTHONHASHSEED=0`)を渡して比べた。欄は final(全桁)・呼数・checkpoint 24〜48 点の (tick, behavior, full)・checkpoint ごとの成分の digest(状態台帳の SoA の列と外の状態の行)・`state_hashes_end_of_day`・RunResult の 158 欄(壁時計と大きな物の参照を除く)・ランの最後の SoA の全列・manifest(環境の欄を除く)・テープの全列。

| 構成 | 体 | final | 呼数 | 違い |
|---|---|---|---|---|
| v3 既定・1 日 | 1,000 | `ba70447d1ab89be6` | 11,873 | なし |
| v3 既定・2 日 | 1,000 | `fc2fde3ae17a96e8` | 25,698 | なし |
| v3 記憶+関係+店 | 1,000 | `4b8fc9783b71c63f` | 11,928 | manifest の壁時計の 2 欄だけ(`relations.wall_seconds_nondeterministic.detect`・`init_seconds_nondeterministic`=HEAD を 2 回回しても違う) |
| v2 edge(注視の腕) | 1,000 | `1b83226c002b1eb2` | 8,695 | なし |
| v3 既定・`response_delay=2` | 1,000 | `ba70447d1ab89be6` | 11,873 | なし(mock は遅れの値に依らない=試験のとおり) |
| v3 既定・1 日 | 5,000 | `5f7ae9ff24005314` | 65,597 | なし |
| golden の帰無腕 | 5,000 | `354f49ca9a61b986` | 97,234 | なし |

- 艦隊(偽の vLLM・合成 200 体・40 tick・`rev_extra.py`): 待ち 10 秒の艦隊を遅れ 1・2 で回すと、final・checkpoint・診断の行が HEAD と同じ。テープの行は多重集合として同じだが、並びは違う。並びは HEAD 同士の 2 回でも違う(到着順)ので、1-0 の差ではない。
- 繰り延べのある艦隊(キュー 8・繰り延べ 758 件・再投入 736 件)を遅れ 1・2 で録画し、HEAD のテープと作業木のテープを HEAD と作業木の両方で再生した。8 本とも final と呼数が録画と同じ(遅れ 1 `0a1d72ce16614016`・遅れ 2 `ca4af367714097b2`・1,038 呼)。
- 再開(1,000 体・v3 既定・2 日・T=1000 で止める): 状態のファイル(npz の 190 配列)は `meta` 以外が HEAD と同じで、JSON の見出しは環境の欄と `run_id` だけが違う。自分の側のファイルからの再開、相手の側のファイルからの再開(HEAD → 作業木・作業木 → HEAD)の 4 本とも final `fc2fde3ae17a96e8`・呼数 6,735+18,963=25,698・checkpoint・診断・日の締めが通しのランと同じ。
- 重さ(参考・HEAD と作業木を並べて 1 回ずつ・`checkpoint_detail` あり): 作業木が 6 構成ともに +2〜6% 遅い(5,000 体で 35.4 → 36.1 秒・38.4 → 39.1 秒)。実装役の「+5〜9%(推測)」と同じ向きで、少し小さい。

### 2-2. 書きの検査の正の確かめ

- 系の間で SoA の配列がどれも読み取り専用であること(`rev_frozen.py`・全部の系の前後): v3 既定・v2 edge・記憶+関係+店(各 300 体・400 tick)と、再開のラン(1,000 体)で、書ける配列は 0 だった。系の外に窓が開いたまま残る道は見つからなかった。
- 宣言を外した列への書きは実行時に落ちる(L7・L8)。

### 2-3. 口の約束

- `SYSTEMS` の順は草案 §2-2 の表と同じ(`close_final` を足しただけ)。`origin` の行の範囲で HEAD の 3605〜4600 行を覆うと、範囲の外に残る実行文はループの頭の 2 行(`for tick …`・`td = …`=進行役が持つ)だけ。
- `writes.soa` は全部の系で `resolve_ops` の静的な閉包そのもので、手で書いた列は混ざっていない。`resolve_ops` の名前は全部 resolve.py にある。
- 外の状態の宣言は `multi-writer-columns.json` の観測と矛盾しない。観測の書き手 ⊆ 宣言の書き手が、SoA 78 列・外の道筋 489 本のすべてで成り立つ。
- 局所の割り当て 450 個のうち「tick の中の一時」は 86 個。そのうち 2 つ以上の系にまたがるものは 0 個。名前は同じでも系ごとに別の一時が 16 個(13 個は複数の系にまたがる)。複数の系にまたがるものは箱の欄か `ctx` に入っていて、一時に逃げた受け渡しは無い。
- 系のモジュールの関数が読む大域の名前(`LOAD_GLOBAL`)は全部モジュールの中か組み込みにあった(まれな枝で NameError になる所は無い)。HEAD の run_day の局所と同じ名前を大域から読む所も無い。

### 2-4. ハッシュに入る名

`state_ledger.LEDGER` の 187 行を欄ごとに repr にして比べた。違いは SoA の行 1 本(`pois.revenue`)の `ast_allow` だけで、`report.py` への付け替えと `_require_thawed(world, world.pois.revenue)` の許可。鍵・名・置き場・dtype・軸・道筋・`ordered`・`multiset`・`behavior_items()` は同じ。値のクラスの置き場は、checkpoint ごとの成分の digest が 7 構成で全部同じことで確かめた(`external_digest` は値のクラスの `module.qualname` を流す)。

### 2-5. 物の同一性

- `Buffers.focus_request`(v2 edge・遅れ 1 と 2): 組み立てで作った物の id と、apply_responses と phase_c が全 tick で見た id が 1 つだった。
- `llm_receive` の位置: 遅れ 1 は perceive_prepare の直後(tick の系の 5 番目)、遅れ 2 は wake_sources の直後(9 番目)。
- 差し込んだ関数(build.py の無名関数 3 つ・入れ子の def): HEAD の run_day で、ループに入った後に `agents`・`rel_layer`・`mem_layer`・`conv`・`_env` を束縛し直す文は無い。組み立ての局所を捕まえても、HEAD の遅い束縛と同じ物になる。`pending` は組み立ての最後に `del` され、閉包からは捕まえられない。

### 2-6. run.py の import の削除

消えた 99 個の名前について、リポの .py(src・tests・tools・docs)の `from shibuya.engine.run import`・`engine.run` の別名の属性・`"shibuya.engine.run.<名>"` の文字列を調べた。当たったのは実装役が挙げた 3 本の道具の 8 か所だけ(`intent_hold_measure.py` の `RUN.IntentLayer` ×3・`response_delay_measure.py` の `RUN.FleetBridge` ×3・`hash_cost.py` の `RUN.full_state_hash` ×2)。試験の差し替えで、今も `engine.run` を的にするのは `_split_due`・`_call_ref`・`sample_population` で、系は呼ぶ時に `engine.run` から引くので差し替えは効く。

### 2-7. 既知の落ち 1 件

`tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` は、本体(HEAD の src)で通り、作業木の src を本体の場所から回しても通る。作業木で落ちる理由は最後の assert `doc["tape"]["dir"].startswith("data/tape/")` だけで、junction の先のパスでは `'AB7-OPEN-INTENT__open'` になる。1-0 の差ではない。

### 2-8. 記録の数の再計算

- run.py 5,188 → 2,484 行・systems のモジュール 25(`__init__` を含む)・系 31(tick 25+日の境目 2+close_final+ランの単位 3)・TickScratch 34 欄・Fixtures 12 欄・局所 450(引数 113)・箱 199(cfg 85・soa 2・layers 19・llm 5・day 6・buffers 1・scratch 34・stats 35・fx 12): 記録と同じ。
- 試験の数: HEAD 3,841 件・作業木 3,949 件を集めた(差 108 = `tests/engine/systems` の 108 件)。3,946 passed+1 failed+1 skipped+1 xfailed = 3,949 と合う。passed の数そのものは、親の全体テストで確かめる。
- 複数の系が書く列の数(SoA 宣言 56・観測 33・外の行の観測 30): JSON の `counts` と同じ。
- 書きの検査の正と負: `guard_results_1-0.jsonl` は 20 行(正 7・負の 12 本が落ちた・書きの起きない負 1 本が通った)。記録と同じ。
- 食い違い: §1 の 10 の 3 点。

### 2-9. 草案 §3-3 の危ない所 22

実装の記録 §2-6 の表は 22 か所すべてに行がある(8・9 は 1 行)。検収で足すことは次のとおり。

- 1(`pending`): 再開(相手の側のファイルを含む)と繰り延べの艦隊の再生で O43 を含む final が同じ。
- 6(差し込んだ関数): §2-5 のとおり物は同じ。ただし置き場の O64 は段 B に見えない(§1 の 8)。
- 10・20(scratch の受け渡しと古い束縛): 番兵の試験はあるが、中身の書き換えはどの段も見ない(§1 の 2)。
- 15(差し替えの的): §2-6 のとおり。
- 17(`focus_request`): §2-5 のとおり。書きの宣言は B だけが見る(§1 の 4)。
- 18・19(ufunc.at・旗の直書き・ビュー): resolve の中の配列ごとの検査は落ちる(L7)。resolve の外の箱の形の ufunc.at(§1 の 1)と D ⑥ の別名(§1 の 5)は穴。
- 22(計時の鍵): manifest の鍵の集合は同じ(記憶+関係+店の差は値だけ)。
- 記録に無いもの: 書きの許可を外す口(§1 の 3)。これは草案の 22 か所にも無い。

## 3. 空欄

- 19 構成の byte-check を自分の道具で回し直すことはしていない(7 構成と艦隊・再生・再開で代えた)。
- 全体の pytest は回していない(親が作業木で回している)。
- 既存の実 LLM テープの再生(手元に再生できる物が無い=10e の RET)。
- 世界資産の上での歩いて乗る退出・親しみ・古典 per_hour の腕(T5 で見つかった 2 件)は回し直していない。
- 重さの静かな機械での測り直し。

## 再検収(段 FIX)

- 対象: 作業木の段 FIX の後の状態(実装の記録 §7)。前回と同じく、作業木と本体は変えず、自前の道具で確かめた(`data/runs/rev_1-0/tools/rev_loopholes_fix.py`・`rev_static.py`・`rev_static2.py`・生の出力は `loopholes_fix.jsonl`)。段 B は試験の形と同じ族(`soa, ext, stats, buffers, scratch`)で回した。
- 判定: **条件つき受入**(条件は軽い)。前回の中の 3 件は、どれも負の対照つきの検査で捕まるようになった。直しの後で開いた穴は 1 つで、許可を外す口に再輸出の名(`guard._WP`・`agents.state._WP`)から届く(R1)。R1 を直すか、§7-3 の限界の表に足すことを条件にする。結果不変は保たれていた。

### R-1. 前回の抜け道の今の捕まり方

合成 80 体・300 tick・記憶+関係+店+同席の腕で、T=200 に 1 回だけ差し込んだ。「A・C」は既定のラン、「B」は試験の形、「D」は静的な検査(植えた行で確かめた)。

| 前回 | 抜け道 | A・C(実行のたび) | B(試験) | D(静的) | 前回との違い |
|---|---|---|---|---|---|
| 1 / L1 | 箱の形の ufunc.at(`b.soa.agents.registry.money`・`r = b.soa.agents.registry`) | 落ちない(限界のとおり) | 落ちる | **見つかる**(`test_add_at_guard` の根に `b.soa`・`box.soa`) | D が捕まえる |
| 2 / L4 | scratch の中身のその場の書き換え(phase_c の前・conversation の後) | 落ちない(限界のとおり) | **落ちる**(`scratch.plan` を書いた系に出る) | 見つからない(限界のとおり) | B が捕まえる |
| 2 / L4b | `object.__setattr__(b.scratch, …)` | 落ちない | 値が変わったときだけ落ちる | **見つかる** | D が捕まえる |
| 3 / L2 | `write_permit.scope(None)`(素の import) | 落ちない | 落ちる | **見つかる** | D が捕まえる |
| 3 / L11 | `set_enabled(False)` | 落ちない | (後の書きがあれば落ちる) | **見つかる** | D が捕まえる |
| 4 / L5 | `b.buffers.focus_request = …`(宣言の無い系) | **落ちる**(段 C・`AttributeError`) | — | — | C が捕まえる |
| 5 / L3 | 凍結の前に作ったビュー | 落ちない | 落ちる | 前回の 9 形が全部見つかる(`self.xs.append(…)`・`setattr(self, 変数, …)` は §7-3 の限界のとおり見つからない) | D が広がった |
| 6 / L9 | 素の import で呼ぶ resolve の口 | 落ちない(列が許可の中) | 落ちない | **見つかる**(`resolve_calls` に `revert_conversation`・`set_activity`) | D が捕まえる |
| — | L6 外の状態・L10 台帳の配列の差し替え・L12 宣言の無い積算 | 落ちない | 落ちる | — | 同じ |
| — | L7 drain・L8 report の SoA の書き | 落ちる | — | — | 同じ |

前回「捕まらない」だった 3 つ(箱の形の ufunc.at・scratch の中身・許可を外す口)は、どれも少なくとも 1 つの負の対照つきの段で捕まる。ufunc.at は D、scratch の中身は B、許可を外す口は D が捕まえる。

### R-2. 新しい抜け道(直しの副作用を狙ったもの)

| # | 抜け道 | A・C | B | D | final |
|---|---|---|---|---|---|
| R1 | 再輸出の名から許可を外す: `from shibuya.engine.systems import guard as G; with G._WP.scope(None): R.set_refractory(…)`(checkpoint から) | **落ちない** | 落ちる(`agents.refractory_until`) | **見つからない** | **動いた** |
| R1' | 同じ形の静的な変種: `from shibuya.agents.state import _WP as X; X.set_enabled(False)`・`import shibuya.agents.state as ST; ST._WP.scope(None)`・`setattr(G, 変数, None)` | — | — | **見つからない**(`permit_offenders` が空) | — |
| R2 | scratch の段 C を `object.__setattr__` 以外で素通りする: `super(type(b.scratch), b.scratch).__setattr__("plan", …)`・スロットの記述子 `type(b.scratch).plan.__set__(…)`・`o = object; o.__setattr__`・`__mro__[-1].__setattr__` | 落ちない | 落ちる(`scratch.plan` を memory に帰属) | 見つからない(`bypass_setattr_sites` は `object.__setattr__` の形だけ) | 動かず |
| R3 | Buffers の中身の配列にその場で書く(`focus_request[:] = 0`・detect・v2 edge 300 体) | 落ちない(段 C は欄の差し替えだけ=限界のとおり) | 落ちる(`buffers.focus_request`) | — | 動かず |
| R4 | scratch の入れ子の入れ子(`scratch.outcome.crowd.coherence` をその場で書く・memory) | 落ちない | 落ちる。scratch の digest は同一性だけだが、外の道筋の族が `O95:runner.crowd.coherence` を memory に出す | — | 動かず |
| R5 | D⑥ の許可 `("engine/processes/civic.py", "self.bed_cell[got]")` の悪用 | — | — | 別の的(`self.bed_cell[0] = agents.registry.cell`)は見つかる。同じ的の 2 行目は許可で通る(許可は (ファイル, 的の文字列) だけで、行数も右辺も見ない) | — |
| R6 | ufunc.at を補助関数の引数や `getattr` で渡す | 落ちない | 落ちる(試していないが L1 と同じ配列) | 見つからない(`field("money")` は見つかる) | — |

- R1 は直しの 3(許可を外す口)を素通りする。`guard.py` は `_WP` を、状態のモジュール 3 つは `_WP` をモジュールの属性として持つ。`permit_offenders` は `write_permit` を直接 import した名と、`X.scope` のように 1 段の属性しか見ない。§7-3 の限界の表は `importlib`・`getattr(WP, 変数)`・`sys.modules` を挙げているが、この形は無い。直し方の案: 許可の関数(`scope`・`set_enabled`・`enabled`・`allows`・`current`)を、属性の鎖の最後の名で見る。あるいは、置き場の外で属性 `_WP` を読むことを禁じる(負の対照に R1 と R1' の 4 行)。
- R2・R3・R6 は、§7-3 の限界の表に書いた「B だけが見る」に当たる。ただし R2 の表の D の欄は「`object.__setattr__` の素通りだけ」なので、ほかの素通りの形(super・記述子・別名・`vars(b.buffers)[…]`)は D の外で、B だけが見る、と 1 行足すとよい。
- R5 は低い。今の civic の `bed_cell` は ndarray で、要素の代入は写しになる。許可を (ファイル, 的, 右辺の文字列) か件数で固定すると、前の `ExtAllow` と同じ強さになる。

### R-3. 足した宣言 4 つは妥当か

| 系 | 宣言 | 確かめたこと | 判定 |
|---|---|---|---|
| world | `O63:renderer._tickc`(`*` でない 1 本) | `_tickc` は描画の前計算で、perceive_prepare の `prepare_tick` が毎 tick 作り直す(`renderer.py` の `self._tickc = _TickCache(…)`)。`render` は `_tickc.tick != tick` なら作り直す。world が書くのは前の tick の `_tickc.flow`(`runner.flow` と同じ配列)で、作り直す前に読む所は無い。HEAD にも同じ別名がある | 妥当。結果に効く書きを認めたものではなく、HEAD からある別名を宣言に写しただけ(行 O63 は軸 1 no・derivable) |
| checkpoint | `tally` に `phase` | `phase["checkpoint"] +=` の壁時計 | 妥当(診断・`STATS_NAMES` の外) |
| report | `tally` に `frozen_sources_map` | `.update(…)` の後、`result.frozen_sources` へ。HEAD の E2〜E4 と同じ所 | 妥当(ランの最後・manifest の欄) |
| observe | `tally` に `occ_counts`・`occ_kind`・`occ_transit` | `append` の在圏 journal | 妥当(前回の §1 の 7 の宣言漏れ) |

### R-4. D② は本物になったか

- `tests/engine/systems/writes_soa_frozen.json` の 31 系は、いまの閉包(`writes_for_ops(resolve_ops)`)とも、系が持つ `writes.soa` とも全部一致した。
- 実装役の対照(perceive_prepare を広げる・phase_c を狭める)とは別に、自分で 4 本当てた。どれも当たった系の名だけが出た。
  - decide の口に `write_relations` を足す → `['decide']`
  - world から `consume` を外す → `['world']`
  - `resolve_ops` は変えず、observe の `writes.soa` に手で `agents.money` を足す → `['observe']`
  - resolve の中身が変わった場合(`set_refractory` の直接の書きに `agents.cell` を足す)→ `['decide']`
- 恒真だった試験と使われない欄 `soa_declared` は消えている。限界: 凍結の表は作り直せば通る(更新の手順は試験の説明文にある)。

### R-5. 記録 §7 の数の再計算

- 試験の数: 作業木で 3,964 件を集めた。3,961 passed+1 failed(既知)+1 skipped+1 xfailed = 3,964 で合う。`tests/engine/systems`+`test_add_at_guard.py` は 130 件で、記録の 130 passed と同じ。passed の数そのものは親の全体テストで確かめる。
- byte-check: `byte_check_FIX_vs_head.json` は 19 構成とも `moved` が空(19/19・25 欄)。
- 外の道筋の粗さ(`ext_coarse.json`): 台帳の道筋は 489 本。宣言は 180 個で、そのうち `*` は 174 個。宣言の対 2,197・観測の対 383(`multi-writer-columns.json` の観測の和と同じ)・比は 5.74 倍。どれも再計算と一致した。
- `local-assignment.json`: `box:stats` 36・`end` 25。合計は 450 のまま。`ledger_growth` は `box:stats.ledger_growth`。
- `multi-writer-columns.json`: SoA の観測 33・外の道筋の観測 66・行 32。記録と同じ。
- import の数(§7-1 の 10): 頂上の 99 と、関数の中を含めた 103 は前回の実測と同じ。
- 限界の表 §7-3: R1(再輸出の名)と R2 の素通りの形を除き、試した形はどれも表のとおりの段で捕まった。

### R-6. 結果不変の軽い再確認

段 FIX の作業木で、1,000 体の 2 構成を前回の HEAD の出力と比べた。

| 構成 | final | 呼数 | 違い |
|---|---|---|---|
| v3 既定・2 日 | `fc2fde3ae17a96e8` | 25,698 | なし(checkpoint 48 点・成分の digest・RunResult の全欄・SoA・テープ) |
| v3 記憶+関係+店 | `4b8fc9783b71c63f` | 11,928 | manifest の壁時計の欄だけ(前回と同じ) |

### R-7. 空欄

- 親の全体テスト(作業木・段 FIX): 3,960 passed・1 failed・1 skipped・1 deselected・1 xfailed(rc=1)。落ちたのは `tests/engine/test_change_detect_p6.py::test_p6_change_detection_under_2ms_at_400k_agents`(400k 体で 2 ms 以内という時間の試験)。検収のランを同じ機械で並べて回していたので、負荷による落ちと推測する(確かめていない)。単独で回し直すかは親の判断。§7 の 3,961 passed との差 1 はこの 1 件。
- R6 の実行時の確かめ(試していない)。
