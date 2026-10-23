# 第 1 期 1-5 権利台帳の器 — 独立検収の記録

- 検収役 Opus 5.5(実装は見ていない)。対象は作業木の枝 `1-5/rights` の未 commit の差分(土台 `6b82be2`=1-4 まで)。読むだけ(この記録 1 本だけを書いた)。
- 正: 口の約束 `docs/design/v2-foundation-contracts-2026-10-13.md` の「## 1-5 権利台帳の器」と冒頭の共通の約束(◎=byte-check 19 構成・2 日・再開・系ごとの指紋)・実装役への発注文・実装役の記録 [README.md](README.md)・1-0/T0/1-3 の規則。
- **比べた土台について**: 雛形は「本体 HEAD の src」と比べる形だが、本体の HEAD(`ec060e7`)はこの枝の土台 `6b82be2` の後に 1-6・1-9 を取り込んでいる(1-9 の K17 で v3 の構成の full-hash が動いた)。1-5 の差だけを見るため、**土台 `6b82be2` の `git archive` の写し**(src・anchors・予算の表・w6 の道具・`rules-table.json`・`bridging-ledger.json`+祝日の CSV)と作業木の src を比べた。作業木の側は `PYTHONPATH` で作業木の src を指した(`src_is_worktree` 真を確かめた)。

## 判定: 条件つき受入

結果不変(byte-check 4 構成・2 日・系ごとの指紋・manifest)と `staff_of_poi` の同値は、独立に確かめて全部同じ。器の口と最初の中身は発注どおり。直してから取り込みたいのは M1 の 1 件(書く口の AST 検査の穴)。低の項は直すか、親の判断で記録に残す。

## 1. 結果不変 ✓

| 検査 | 方法 | 結果 |
|---|---|---|
| 実装役の byte-check 19 構成([byte_check_r15.json](byte_check_r15.json)) | JSON を読んだ | 19/19 構成で 25 欄とも `same`・`moved` 0。腕は作っていない(◎ の道)ので既定は今の道のまま |
| 検収役の byte-check 4 構成 | `10e/byte_check_10e.py side`(`w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`・5,000 体・seed 1・1 日・テープつき)を土台の写し(`src_is_worktree` 偽)と作業木の src(真)で回し `compare` | **4/4 構成で 25 欄とも同じ**。final は `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`(実装役の表と同じ)・full_last と end_of_day も同じ |
| 2 日のラン(実装役の記録に無い=共通の約束の ◎) | `10e/two_day_check_act.py one`(5,000 体・seed 1・既定 v3・テープつき)を両側で | **全欄同じ**: final `912446bd2b42b6ab`・140,913 呼・テープの calls `cb330e76b4b8a573`・blocks `7f09f3dc78d84ac4`・暦 07-13 → 07-14(1-4 の記録の値とも同じ) |
| 系ごとの指紋(実装役の記録に無い) | `r14/tools/probe_r14.py side`(1-0 の probe・全部の刻み・`PYTHONHASHSEED=0`。1-4 の欄を外す手当ては土台にも 1-4 があるので両側に同じくかかる)を両側で → `compare` | **3 構成とも全部の系・全部の刻みで同じ**(`all_ok`・最初の差なし): 合成 80 体 720 刻み 19 系・並び 6,664/世界資産 300 体の既定 v3 19 系・15,598/記憶+関係 21 系・17,710。final も同じ |
| 再開 | 範囲の試験の中の `tests/engine/processes`・`test_t0_tm9_fields.py`(再開を含む)と `test_rights_manifest.py::test_rebuild_gives_the_same_ledger` | §7 のとおり通った |
| manifest の既存の欄 | 実装役の 7 本([manifest_check_r15.json](manifest_check_r15.json))を読み、自分でも `run_day`(60 体・600 刻み)と `cli.run`(300 体・seed 2)の 2 本を両側で回して平坦化して比べた | 既存の欄で動いたのは `bridges_count`(273 → 277・日次の行も)と `bridges_version` だけ。足したのは末尾の `rights` と節の表の 1 行。final 同じ |

## 2. 口と約束

| 口の約束 | 実装 | 判定 |
|---|---|---|
| `engine/rights/ledger.py` の `Right`(holder・object・kind=所有/賃借/雇用/許可・since_ns/until_ns・counterparty・source・cause=1-3 の Event.id) | `Right`(凍結・slots・kw_only)の 8 欄が同じ名と順(`RIGHT_FIELDS`)。kind の値は英字 `own/lease/employ/licence`(発注どおり)で、`KIND_WORDS` が 所有/賃借/雇用/許可 に対応。cause は `(t_ns, seq)` | ✓ |
| 読み口 `Rights.holds(holder, kind, object, t)` | `holds(holder, kind, object, t_ns)`(引数の名だけ `t_ns`)。発注の `holders_of(object, kind, t_ns)` もある。ほかに配列で引く `holds_each`・`holder_table`・`holds_any`・`tally` | ✓ |
| 権利に反する行動は止めずに `Event(cause=…, what="unauthorized_act")` | 語は `行為:許可のない行動`(発注の指定と 1-3 の `族:語` の形=仮採用 7)・原因 `Process("rights")` | ✓(語の名は発注に従った) |
| 約束 (1) 先に数える | [no_permission_r15.json](no_permission_r15.json)(19 構成・5,000 体)と生きた数えの試験(200 体) | ✓(§8 (b) の注を見よ) |
| 約束 (2) 同じ割り当て | 試験 `test_staff_of_poi_equivalence.py`+byte-check | ✓(§6 で独立に再計算) |
| 約束 (3) 行数と種類の分布を manifest に | 末尾の `rights`(観測の節) | ✓ |
| 受入の試験 4 本+byte-check | 4 本ともある。ほかに `test_rights_events.py`(発注)・`test_rights_manifest.py` | ✓ |
| 〔決定〕営業許可は許可の一覧の中で探し、無ければ空 | 記録(R-76 #17・R-106 §2-1)の上では区の一覧(39,304 件・CC BY 4.0)が**ある**が未取得=0 行で空欄を宣言 | △(ネットを使わない発注の制約による。親の判断=§「親に確かめてほしいこと」1) |
| 〔決定〕0 でなければ ▲・縮める部分を腕に | 0 なので腕なし | ✓ |

- 約束に対応する試験が無いもの: なし。ただし **判断の系(decide)の中で役割語の記録が書けること**(宣言 `E:events.*` が実行時の検査を通ること)を確かめる試験が無い(既存の試験は系の外で `LLMBridge.call` を呼ぶ)。検収で台本の LLM を使って確かめた(§8 (b))=低 L3。
- 口の約束は `test_no_permission_count.py` に「0 でなければ記録して止まる」と書くが、発注は「落とさず ▲ の印」。試験は発注どおり警告 `NoPermissionHit` を出して落とさない。どちらを正とするかは親の確認(低 L9)。

## 3. 発注文の各項

| 項 | 判定 | 根拠 |
|---|---|---|
| 1 権利台帳 `ledger.py` | ✓ | `Right` 8 欄・`Rights` は列ごとの配列(1 行 72 B)・書く口 `grant`/`revoke`・`__setattr__`/`__delattr__` の守り・`holds`/`holders_of` |
| 2(a) 雇用=W16 の `org_id` | ✓ | 5,000 体で 2,421 行・全母集団で 222,849 行(§8 (c) で parquet を数えて一致) |
| 2(b) 営業許可 | △ | 0 行で空欄を宣言(`BR-RIGHTS-LICENCE-BLANK`)。記録の上では一覧があり、取得は親へ(README §2)。申告どおり |
| 2(c) 店の賃借 | △ | 発注は holder=org だが、実装は holder=店(`store`=POI の番号)。W6 の `w6_poi` に組織の列が無く(列を確かめた)、POI と組織を結ぶ規則が無いため(仮採用 2・3)。家賃は `BR-RENT-BLANK` に結んだ |
| 2(d) 住まい | ✓ | 0 行で欄だけ(`dwelling`)・`BR-RIGHTS-DWELLING-BLANK` |
| 3 `staff_of_poi` の置き換え | ✓ | `_assign_staff` を消して台帳の `employ`(体 → 店)の行から読む。規則は `initial.staff_assignment` へ移した |
| 4 止める検査を縮める | ✓ | 19 構成とも 0 → 腕なしで縮めた。範囲は §8 (b) |
| 5 manifest | ✓ | `rights`(行数・種類・持ち主・物・出どころ・バイト・空欄の行・許可のない行動の数) |
| 記録 | ✓ | README の §0〜§11。「できなかったこと」(営業許可・住まいの値・艦隊の経路・職務の語・開閉の見出しの行・実 LLM のテープ)の申告は実態と合う |

## 4. 守り

- 書く口は `grant`/`revoke`(どちらも `_write` を通る)。属性の付け替えと消去は `AttributeError`(試験 5 名)。表(`KIND_WORDS`・`OBJECTS_OF_KIND`・`_source_codes`・`BLANK_BRIDGES`)は `MappingProxyType`。読み口は写しか値を返す(内部の配列を渡す口は無い=読んで確かめた)。列は書き込める配列(仮採用 11)。
- AST の検査(`test_rights_schema.py` の `ledger_violations`・`outside_violations`)と負の対照(台帳の中 4 形・外 5 形)はある。**検収で負の対照を植えた**(一時の写し=文字列に植えて検査の関数に渡しただけ・ファイルは書いていない):

| 植えた形 | 捕まるか |
|---|---|
| 台帳の中: `self._r_kind[0] = 1`・`object.__setattr__(self, '_n', 0)`(既存の対照) | 捕まる |
| 台帳の中: `self._r_kind.fill(0)`・`np.copyto(self._r_until, 0)`・`self._r_holder_id.put(...)`・`np.add.at(self._r_since, ...)` | **捕まらない** |
| 台帳の中: 局所の別名 `col = self._r_kind; col[0] = 3`・`c = getattr(self, '_r_kind'); c[:] = 0` | **捕まらない** |
| 台帳の外: `rights._r_kind[0] = 2`・`object.__getattribute__(rights, '_r_' 'kind')` | 捕まる |
| 台帳の外: `object.__setattr__(rights, '_n', 0)`(実行時に行の数を 0 にできた)・`getattr(rights, '_r' + '_kind')`・`_COL_NAMES` を回す `getattr` | **捕まらない** |

→ 中 M1。

## 5. 宣言と凍結 ✓

- `SYSTEMS`: decide の `writes.paths` に `E:events.*` を足した(役割語の記録)。凍結の表 `writes_paths_events.json` は decide の 1 行だけ増えた。SoA の書きは足していない。
- 状態台帳: 除外の一覧に 4 行(`runner.opening` の `rights`=CACHE(導出・再開で作り直す)・`org_of_agent`=CONST・`unauthorized`=REF・`bridge` の `role_rights`=REF)。新しい状態の行は無い(権利は 2-1 まで変わらない=仮採用 1)。
- manifest の凍結の表 `manifest_keys_frozen.json`: 111 → 112 鍵(末尾に `rights` だけ)。既存の欄の値は §1 のとおり不変。
- 語彙: §8 (e)。

## 6. 同値(独立の再計算) ✓

- 方法: 土台の写しの src と作業木の src で、同じ入力から `OpeningProcess(...).staff_of_poi` を作って npz に書き、値と型を比べた(道具は検収役の作業の置き場=リポの外)。土台の側は **HEAD の本物の `_assign_staff`**(試験の写しではない)を通る。
  - 合成の世界 640 通り: seed 11〜30 × セル 4・9・16・36 × 体 1・5・50・333 × 種別 2 通り(`synthesize` の種別と、従業者の割合を 0〜60% で乱数にした種別)。各々 `rebuild_derived` の後の表も(計 1,280 本)。
  - 実データ: `cli.run(n_agents=5_000, seed=2 と 3, ticks=3)` の組み立てた実行器の `runner.opening.staff_of_poi`(byte-check と別の seed)。
- 結果: **1,284 本とも値と型(int64)が同じ**。担当のいる表 938 本・担当の入った欄 35,094。実データは 2 本とも POI 2,337 に担当が入り、担当の体は 75 人(同じ)・短いランの final も両側で同じ。

## 7. 試験

- 範囲(`tests/engine/rights`・`systems`・`events`・`time`・`bridging`・`rules`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`processes`・`tests/test_cli.py`・作業木・`-n 2 --dist loadfile -m "not slow"`): **743 passed・0 failed・0 skipped(data の飛ばし 0)・385 秒**(byte-check・2 日・指紋のランと並べて回した時間)。全体は親が回す。
- `lint-imports`(作業木の src): 5 kept・0 broken。
- 新しい試験は 101 本(数え直した)。

## 8. 抜け道と記録

### (a) `staff_of_poi` の同値 ✓
§6。試験の写し `head_assign_staff` は HEAD の `_assign_staff` と同じ本文(差分で確かめた)。

### (b) NO_PERMISSION=0 の確かめと縮めた範囲 ✓(注あり)
- 数え方を読んだ: 開閉店の口 `resolve.request_open_close` を包んで `permitted` が偽の行を数える・`LLMBridge.call` を包んで役割語を数える・群と規範の計器の `role_words.no_permission`。`NO_PERMISSION` を `last_result` に書くのは src の中で `request_open_close` だけ(grep で確かめた)。
- 自分で 1 構成(`w6_v3_default`・5,000 体・seed 1)を両側で回した: 開閉店の口 10 回・20 行・権利の無い行 0・役割語 0・計器 0・許可のない行動の記録 0・final `5f7ae9ff24005314` で両側同じ(実装役の表と同じ)。
- **注(0 は作りから来る)**: (i) HEAD の開閉の過程は `permitted=np.ones(...)` を渡していた=権利の無い行は作りの上で出ない。(ii) mock と古典は役割語を出さない。(iii) 群と規範の計器は、判断の口が役割語を待機に置き換えた**後**の行動コードを見るので、役割語を数えられない(検収で台本の LLM に全部「開閉店」を答えさせた 409 呼でも計器の `role_actions` は 0=HEAD でも同じ・1-5 の前からの計器の盲点)。だから「19 構成とも 0」は「今の既定に止める経路が無い」ことの確認で、結果不変の強い根拠は次の 2 つ: 縮めた後も役割語の行動コードは今までどおり待機/なしに落ちる・記録は出来事の記録(行 E=軸 1 diag・軸 2 discardable)だけに入る。**検収で確かめた**: 台本の LLM(`run_day` 60 体・720 刻み・v3 と v1・語 開閉店/発車/散歩)を両側で回すと、final は 6 本とも両側で同じ。作業木の側は decide の系の中で記録が書けた(開閉店: v3 で 311 行・v1 で 261 行=雇用の行の無い体の分・manifest の `rights.unauthorized.rows` と一致・宣言の検査で落ちない)。発車は判定しない語として 409/350 を数えるだけ。
- 縮めた範囲(`request_open_close` の権利の無い行を止めずに記録する・役割語の「権限検査待ち」の意味を外して記録する)と縮めていない範囲(開閉の過程の「担当が同じセルに居るか」=物理・営業時間の旗と `open_mask`=機械の決まった動きと CP3 の「前提(営業中)」・補充の `has_permission`=実行の主体を担当か engine_rule の代打かに分けるだけで補充は起きる・開閉の `has_permission`=試験だけが呼ぶ)は、決定 10-12 §1-4 と CP3(止めるのは物理と物理的に止める仕組みだけ・前提は確定の前に確かめる)と合う。
- 縮めた所で既定の結果が動かない根拠: byte-check 19/19(実装役)+4/4(検収役)・2 日・指紋・上の台本の LLM の 6 本。

### (c) 最初の中身の出どころとつなぎの台帳の行 ✓(低の注)
- W16(`data/world/v2/w16_population.parquet`)を自分で数えた: 390,067 行・`org_id` は int32・null 0・`org_id >= 0` は **222,849**(組織 9,872)= 実装役の全母集団の雇用の行と一致。`build_initial` を全母集団で回して出どころ別 222,849/2,337/2,337(計 227,523)。5,000 体の抽出(seed 1)は 2,421。
- 担当の雇用 2,337=POI の数(実データの 5,000 体には従業者 75 人=全部の店に担当)。賃借 2,337=POI の数。営業許可 0・住まい 0。
- 足した 4 行の `remove_at`:
  - `BR-RIGHTS-LICENCE-BLANK` → 4-2(計画 4-2 に「営業許可」=plan): 妥当。ただし記録の上ではデータがある(親に確かめてほしいこと 1)。
  - `BR-RIGHTS-DWELLING-BLANK` → 4-2(inferred=発注「住まいの権利=4-2 で」): 発注どおり。計画 1-5 は住まいを 1-5 の中身に入れているので、取得するなら 1-5 の残り(親の判断)。
  - `HD-engine.rights.record` → 6-6(役割語の効果と対象の解決=6-6 ②): 妥当。
  - `HD-engine.rights.initial` → 4-2: 項の 1 つ目(担当従業者の丸振り)は `HD-engine.processes.opening` の項 1 と**同じつなぎ**で、親はそちらを 4-1(組織データ=人+関係+権利台帳)に改める予定。2 行の外す段をそろえる(低 L6)。
  - 既存の `BR-RENT-BLANK`(4-2)に家賃を結んだ: 妥当。

### (d) 台帳の守り △
§4。書く口・`__setattr__`/`__delattr__`・`MappingProxyType`・列が書き込める配列であることは試験が守る。ただし AST の検査は代入の形しか見ない(M1)。

### (e) 語彙と原因の名 ✓
土台の写しと作業木の `VOCAB` を別々に読み込んで比べた: 先頭 55 語は同じ(sha256 の先頭 16 桁 `5cafd7ba95c5544a`・コード 0〜54 も同じ)・作業木は末尾に `行為:許可のない行動`(コード 55)だけ・`PROCESS_NAMES` は 20 語で同じ。原因の名 `rights` は `CHECK_PROCESSES`(`CAUSE_PROCESS_NAMES` にだけ入る=`過程:rights` の語は無い)。出来事の記録は原因を実行時の表で持つので、名を足してもコードは動かない。`VOCAB_VERSION` を読む所は語彙の置き場の外に無い。

### (f) 範囲の外の試験 5 本 ✓
`test_e_vocab_is_closed.py`(55 → 56 語・版)・`test_bridging_ledger.py`(見出し 74 → 76・ファイル 71 → 73・項 338 → 343・`HD-` 74 → 76)・`test_manifest_rules_bridges.py`・`test_t0_tm9_fields.py`・`test_env_and_sections_10f.py`(manifest の末尾に `rights`)。どれも数の固定と末尾の並びだけで、検査の中身は弱めていない。

### (g) 既存の行 `HD-engine.processes.opening-1af925f4`(外す段 1-5) ✓
README §3 に「丸振りの規則を `initial.py` へ移しただけ(値は不変=つなぎは外れていない)・外す段を直すかは親の判断」と書かれている(§11 にも)。限界の記録はある。

### 記録の確かめ ✓
- README・JSON 3 本・道具 4 本に絶対パス・ホスト名・個人名は無い(grep)。LF(CRLF なし)。
- 共有のファイルの一覧(README §9)は `git diff --stat` の 19 本と合う。ただし §9 は `docs/design/bridging-ledger.json` を挙げていない(§1 の表にはある)。

## 欠陥

| 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|
| 中 M1 | `tests/engine/rights/test_rights_schema.py:201-235`(`ledger_violations`・`outside_violations`) | 「書く口は 2 つだけ」の AST の検査が代入の形(`self.X[...] = `)しか見ない。台帳の中のメソッドでの書き(`.fill`・`.put`・`np.copyto`・`np.add.at`)と局所の別名、台帳の外からの `object.__setattr__(rights, '_n', 0)`(実行時に行の数を 0 にできた)・名を組み立てる `getattr` を通す(§4 の表) | 1-9 の検出器(本体の `tests/economy/cp2/money_writers.py` の `MUTATING_METHODS`・`MUTATING_FUNCS`・別名の追跡)を rebase の後に流用するか同じ形を足し、台帳の外の `object.__setattr__`/`__getattribute__` を `Rights` の物に対して禁じる。負の対照を上の 4 形+外の 2 形に足す |
| 低 L1 | `src/shibuya/engine/rights/record.py:102` | 新しい関数 `RoleActCheck.__call__` の引数の名が `tick`(T0「tick を新しい識別子に入れない」。試験は名の集合で見るので既存の名 `tick` は通る) | 刻み系の名にするか、`LLMBridge` の側で `t_ns` に直して渡す |
| 低 L2 | `src/shibuya/engine/resolve.py:3101-3107` | 止めずに旗を確定した行の `last_result` が `NO_PERMISSION`(仮採用 5)。知覚では「権限なし」として代わりの行動(移動・待機・退去)が示されるので、「起きたことにする」と食い違い、柔らかい停止になりうる。今は 0 回 | 親の判断(`OK` にして記録だけにするか)。役割語に効果が付く段の前に決める |
| 低 L3 | `tests/engine/rights/test_rights_events.py` | 判断の系(decide)の中で役割語の記録が宣言の検査を通って書けることの試験が無い(試験は系の外で `bridge.call`) | 台本の LLM で `run_day` を回す試験を 1 本(検収の §8 (b) の形=記録の行数と manifest が一致・final が記録なしと同じ) |
| 低 L4 | `src/shibuya/engine/rights/record.py`(`RoleActCheck`)・`llm_bridge.py:709-713` | 役割語は効果の先が無く待機に落ちる(=行動は起きていない)のに、「許可のない行動」を出来事として書く。出来事の意味(起きたこと)と合わない | 親の判断: 効果が付く段(6-6)まで記録しないか、「試み」と分かる形にする |
| 低 L5 | 記録 README §6 | 共通の約束の ◎ のうち 2 日・系ごとの指紋・再開の結果が記録に無い | 検収で補った(§1)。README §6 に足す |
| 低 L6 | `docs/design/bridging-ledger.json`(`HD-engine.rights.initial-1af925f4`) | 丸振りの項は `HD-engine.processes.opening` の項 1 と同じつなぎで、外す段が 4-2 と(親の予定の)4-1 に分かれる | 2 行の外す段をそろえる(4-1 が近い=組織データ) |
| 低 L7 | `src/shibuya/engine/state_ledger.py:669`(行 E の注) | 「書く系は world・checkpoint・day_close・close_final」のまま(1-5 で decide が書く。1-9 の phase_c も) | 注を直す(親) |
| 低 L8 | 艦隊の経路(`llm/fleet.py`) | 役割語の確かめの口を挿していない=艦隊のランでは役割語があっても `rights.unauthorized.rows` が 0(README §11 に申告あり)。つなぎの台帳に行が無い | つなぎの台帳に行を足す(外す段=受け取りの系で同じ口を呼ぶ段) |
| 低 L9 | `tests/engine/rights/test_no_permission_count.py:59` | 19 構成の生きた数え(約 70 秒)が `not slow` の範囲にある。口の約束は「0 でなければ止まる」・発注と試験は「落とさず ▲」 | `slow` にするか構成を絞る。止まる/落とさないは親が決める |
| 低 L10 | `src/shibuya/engine/rights/record.py`(`UnauthorizedLog` の数え) | decide の系が `runner.opening` の持つ数え(`_by_act`・`_unjudged`)を書く=持ち主をまたぐ diag の書き。除外の一覧では REF(参照)としていて、数えを持つことが見えない | 除外の行の注に「数えを持つ(diag)」と書くか、数えを出来事の記録の `what_counts` から作る |

## 親に確かめてほしいこと

1. **営業許可**: 口の約束の決定は「許可の一覧の中で探し、無ければ空」。記録(R-76 #17)の上では渋谷区の一覧(SHIBUYA OPEN DATA・39,304 件・CC BY 4.0・ドメインは許可の一覧の中)があり、`data/` には無い(検収で探した)。いま取得して 1-5 の残りで入れるか、4-2 まで空欄にするか。入れるなら POI と突き合わせる規則(名と座標の距離・廃業の扱い)は設計者の指紋になる=判断が要る。住まい(国勢調査の表 18-4・e-Stat)も同じ。
2. L2・L4(止めない行の結果の欄と、起きていない役割語の記録)の扱い。
3. **取り込みの rebase**: 本体の 1-9 が同じ所に足している=manifest の末尾(`economy` と `rights` の並び)・`writes_paths_events.json`(`phase_c` と `decide`)・`test_manifest_rules_bridges.py`(末尾の鍵の assert)・`test_t0_tm9_fields.py`・`test_env_and_sections_10f.py`・`state_ledger.py`・`systems/table.py`・`systems/build.py`・`run.py`・`manifest_sections.py`・`llm_bridge.py`・`bridging-ledger.json`(末尾への追記)。rebase の後に byte-check 4 構成と manifest の末尾の並びを回し直す。M1 は 1-9 の検出器が入った後なら流用しやすい。
4. 群と規範の計器(`norm_meter` の (c))は役割語を数えられない(待機に置き換えた後を見る・1-5 の前から)。1-5 の範囲の外だが、「NO_PERMISSION の計器 0」を根拠に使う所では盲点を書き添える。
5. 予算の宣言(`docs/design/v2-budget-declaration.md`)に権利台帳の大きさ(1 行 72 B・全母集団 227,523 行=16.4 MB・作る時間 0.69 秒=README の目安)を足すか(実装役は文書を触れない)。

## 検収の作業(再現の手がかり・絶対パスなし)

- byte-check: 土台 `6b82be2` を `git archive`(src・`docs/bench/anchors`・`docs/design/v2-budget-declaration.md`・`docs/bench/analysis/w6-regen-2026-09-28`・`docs/design/rules-table.json`・`docs/design/bridging-ledger.json`)+祝日の CSV を作業用の置き場へ。`byte_check_10e.py side --src <写し>/src` と `side --src src`(作業木)→ `compare`。
- 2 日: `two_day_check_act.py one` を両側(`PYTHONPATH`)。指紋: `probe_r14.py side`(両側 `PYTHONHASHSEED=0`)→ `compare`。
- 同値・負の対照・台本の LLM・manifest の確かめの道具は検収役の作業の置き場(リポの外)に置いた。作業用の置き場は終わった後に消した。
