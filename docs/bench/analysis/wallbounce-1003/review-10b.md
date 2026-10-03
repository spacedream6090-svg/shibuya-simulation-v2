# 10b の検収(別のサブ・2026-10-03)

> 検収役(Opus 5.5・実装を見ていない)。何も直していない。commit していない。
> 対象: 10b(状態台帳の 2 軸・追加 C の AST 検査・behavior-hash と full-hash・揺らし試験・保留の組の発射の tick と call_id)。
> 見た版は 2 つ: (1) 実装役が親の答えを反映する前の写し(10b-1・台帳 163 行)、(2) 反映後の作業木(10b-2・台帳 187 行・`state-ledger/10b-2`)。どちらで見たかを各項に書く。
> 基準は `git archive HEAD`(HEAD=bbe7e77。src と tests は 120d147 と同じ)を OS の一時ディレクトリの短いパスに展開した写し。パスは `src/shibuya/` を省略する。

## 0. まとめ

| 種類 | 件数 |
|---|---|
| 結果を動かす欠陥 | 0 |
| 潜在の欠陥 | 6 |
| 記録の誤り | 3 |
| テストの欠け | 4 |
| 問い | 4 |

- **byte-check は一致**: 既定 v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439・relations-on `40409ebed834126b`/72,930 の 3 構成で、final(全桁)・呼数・checkpoint 4 点の全部(tick・agents・world・母集団・予定表・活動・combined)・prompt_hash・calls の全列・blocks が HEAD の写しと一致。10b-1 の写しと 10b-2 の作業木の両方で一致。
- manifest の差は新しい欄 `state_hashes` だけ(ほかの欄は値も鍵の順も同じ。relations-on の `relations.wall_seconds_nondeterministic.detect` は壁時計で毎回変わる欄)。Checkpoint に足した 2 欄は `combined` に入っていない(上の全点一致が根拠)。
- behavior-hash の新しい値は親の伝えた値と一致(v3 既定 `b315f03ad68b68c6…`・帰無 `3bd18625ff3d923e…`・relations-on `70089de493a21d41…`)。
- 壊して捕まるか: 指示の 8 種は 1 つ(揺らしの陽性対照を外す=これ単独では捕まらなくて正しい)を除き捕まる。ただし T1 の準備のテストは「揺らしが効かない」壊し方を捕まえない(テストの欠け 1)。
- 費用(10b-2・5,000 体・この機械): 1 checkpoint の 2 本の合計の最大は 既定 v3 12.9 ms・記憶+関係 25.2 ms・全腕 31.9 ms。親の上限 100 ms の中。

## 1. 結果を動かす欠陥

なし。

## 2. 潜在の欠陥

### 2-1 `to_state` が辞書の挿入順を捨てるので、順序が挙動を決める状態の違いを full-hash が見逃す(10b-2)

- 根拠: `engine/state_hashes.py:173-181`(Mapping は鍵の直列化の昇順に並べ替える)。`MemoryLayer._gist_order` は `OrderedDict` で、`engine/memory.py:585-590` の `od.popitem(last=False)` が「古い順に落とす」=並び順が次に消える要旨を決める。台帳では O8 の `mem_layer._gist_order`(behavior・required)。
- 再現: `to_state({7: OrderedDict([(1, None), (2, None)])}) == to_state({7: OrderedDict([(2, None), (1, None)])})` が True。
- 影響: 今の結果は動かない。10d で「再開の状態 == 通しの状態」を full-hash で判定するとき、要旨の並びを取り違えた復元を見逃す。ふつうの dict でも、走査の順が処理の順になる持ち主(会話の管理の `sessions` など)は同じ穴がある。順序を持つ型(OrderedDict・走査順に意味がある dict)は並びのまま流す形を検討してほしい。

### 2-2 最後の checkpoint の後に日の締めが状態を書くので、manifest の 2 本のハッシュはランの終わりの状態と違う(10b-1・10b-2)

- 根拠: `engine/run.py:3946`(`runner.end_of_day`)と `:3975`(`ledger.end_of_day`)が tick のループの後=最後の checkpoint の後に走る。
- 再現: 実資産 200 体・v3 既定(`cli.run`)の最後の checkpoint の `owners` で、ランの後に行ごとの digest を取り直すと、O57 `ledger.money._day`・O59 `ledger.goods._sold_today`・`ledger.goods._day` が変わる(10b-1)。10b-2 では O77・O80(バイト数も変わる)も変わり、behavior-hash と full-hash の両方が checkpoint の値と一致しない。合成世界(台帳なし)では一致する。
- 影響: 10d で日境界に保存するのは締めの後の状態のはずで、そのときの full-hash は manifest に出る値と別物になる。問い 5-1 と組。

### 2-3 会話の管理の期限つきの辞書が期限切れの項を消さず、日数に比例して増える(10b-1 で測る・10b-2 も同じ形)

- 根拠: `engine/conversation.py:282-290`(`_refusal_until`・`_pair_invite_until`・`_speaker_invite_until`)。書くのは `:481-484`・`:599`、消す所が無い。
- 再現: 合成世界 2,000 体・v3・3 日(`run_day(sim_days=3)`)で O39 の直列化が 2,291 B(1 日目の朝)→ 96,917 B(1 日目の終わり)→ 253,229 B(3 日目の終わり)。`_refusal_until` は 8 → 2,252 項。
- 影響: (a) full-hash と再開の状態の大きさが日数に比例して増える。(b) 期限切れの項は挙動では「無い」と同じだが full-hash では違う値になるので、10d の復元が期限切れを落とすと resume と straight が食い違う(挙動は同じなのに)。

### 2-4 速い道 `_feed_int_table` は Python の int だけを通すので、同じ値でも numpy の整数が混ざるとバイト列が変わる(10b-2)

- 根拠: `engine/state_hashes.py:99-108`(`type(x) is not int` で普通の道へ)。普通の道は int と `np.int64` を同じ `I` で流すので、型の違いを区別しない約束が速い道でだけ崩れる。
- 再現: `to_state({(1, 2): 5, (0, 3): 7}) != to_state({(1, 2): np.int64(5), (0, 3): 7})`、`to_state({1: 5}) != to_state({np.int64(1): 5})`。挿入順には依らない(`to_state` 2 つの順で一致を確認)。
- 今のランでは問題ない: 全腕の合成世界で O39 の 3 辞書は鍵も値も全部 Python の int(速い道)。10d の復元で numpy の整数に戻すと、値が同じでも full-hash が食い違う。速い道に入る条件を「整数(np.integer を含む)」にするか、復元の型を宣言するか。

### 2-5 追加 C の AST 検査の死角(10b-1・10b-2 とも同じ)

自分の一時ディレクトリに 1 ファイルずつ置いて `scan`+`check`(`fail_streak` を no のまま)を回した。

| 書き方 | 結果 |
|---|---|
| `getattr(reg, n)`(`n` が名前の表を回す変数) | 捕まらない(読みにも「解決できない」にも数えない) |
| `getattr(reg, n)`(`n` が引数) | 捕まらない |
| `reg.arrays.get('fail_streak')` | 捕まらない |
| `operator.attrgetter('fail_streak')(reg)` | 捕まらない |
| `reg.money[a], reg.fail_streak[a] = reg.money[a] - reg.fail_streak[a], 0` | 捕まらない(左辺に同じ列があると右辺の読みを全部「自己更新」として外す) |
| クラスの欄の名前の表・dict 内包・f 文字列 | 捕まる(読み、または解決できない読み) |

- 根拠: `engine/state_ledger_ast.py:252,264`(`getattr` を変数の読みから外す)・`:285`(自己更新の判定が文単位)。
- 今の src では見逃しは無い: 変数の名前で `getattr` する 15 か所に SoA の持ち主は無く、軸 1 が no/diag の列を左辺に持つ文で右辺が同じ列を読むのは 5 か所(`resolve.py:1074,1465,1538,3054` の `fail_streak` の +1・`:2821` の `band`)で、どれも本当の自己更新。docstring の「限界」に `getattr(obj, 変数)` は書いてあるが、左辺つきの文の件は書いていない。

### 2-6 持ち主のクラスの網羅は「道筋ごとに 1 つのクラスの AST」だけを見る(10b-2)

- 根拠: `engine/state_ledger.py:650-697`(`OWNER_CLASSES`)と `engine/state_ledger_ast.py` の `class_attrs`(そのクラスの本体だけを読み、継承元と別のクラスは見ない)。
- 再現: checkpoint の `owners` を 4 構成(合成の既定・全腕・古典、実資産の記憶+関係)でたどると、`poi_resolver.chooser` は `NearestChooser`(宣言は `ClassicalChooser`)、`ledger.money` は `cli._HouseholdWalletLedger`(宣言は `Ledger` の子)。実際の `vars()` を台帳と除外の一覧に突き合わせると、載っていない属性は `ledger.money.wallets`(`cli.py:251`・初期の財布=定数)の 1 つだけ。
- 影響: 今は定数 1 つで害はない。構成で別のクラスや子クラスが入ると、新しい状態が網羅のテストをすり抜ける。実行時の `vars()` で突き合わせる検査を足すか、子クラスも `OWNER_CLASSES` に載せるか。

## 3. 記録の誤り

### 3-1 除外の分類「キャッシュ」の説明が実際と違う(10b-2)

- `engine/state_ledger.py:699` は `CACHE` を「毎 tick 作り直す・他から計算できる」と書くが、抜き取ると「毎 tick 作り直す」ものと「中身で引く覚え書き(ラン中ずっと残る)」が混ざる。後者は中身が同じなら空から始めても出力は同じなので、除外の判断そのものは正しい。説明の文言だけ直したい。
- 確かめたもの(10b-2・合成の全腕 2 日と古典 2 日、実資産 400 体 1 日で checkpoint ごとに digest を取り、変わったものをコードで読んだ):
  - `detector._wake_buf`・`_cell_mask`・`_hit`・`_any`・`_up`・`_dn`・`_b2`: 使う前に `out=` で全部書くか `[:] = False` で戻す(`engine/change_detect.py:310-327,372-376`)=毎回作り直し。
  - `rel_layer._hits`・`_hits_tick`: tick で引く(`engine/relations.py:920-930`)=別の tick では作り直し。
  - `runner.crowd.admitted_this_tick`: step の頭で 0 に戻す(`engine/processes/crowd.py:225`)。
  - `runner.salient._order`・`_start`: 事象のある tick の頭で作り直し、読むのはその後だけ(`engine/processes/salient.py:208,228,270`)。
  - `runner.environment._shade_cache_frame`: 印だけ。`_shade` は O56 で full に入り、印を −1 に戻すと同じ枠の値を作り直す(`engine/processes/environment.py:236-251`)。
  - `runner.traffic.hour`: 同じ形(`engine/processes/traffic.py:146-149`)。
  - 覚え書きの側(ラン中残る): `act_layer._digest_cache`(`engine/activity.py:493-499`)・`renderer._b1_cache`・`_b4_cache`(`perception/renderer.py:1394-1401,1761-1785`・鍵がセルと B4 の欄のハッシュ)・`poi_resolver._cat_mask_cache`(`engine/poi_target.py:315-322`)。
- 「定数・設定」257 属性は、上の 3 構成で checkpoint のたびに digest を取って 1 つも変わらなかった(途中で変わるものは紛れていない)。

### 3-2 README の基準の版の書き方(10b-1・10b-2)

- README §5 と §10-4 は「HEAD `120d147` の写し」と書くが、今の HEAD は bbe7e77。src と tests は同じなので比較は有効。「HEAD(bbe7e77・src は 120d147 と同じ)」と書くと読み手が迷わない。

### 3-3 README §0〜§9 に 10b-1 の数値が残る(10b-2)

- 冒頭に「§10 が正」と注記があるので誤読は防げるが、§0-2(163 行)・§0-4(85.8 ms)・§1(27 関数 45 件)・§9 問 1(641 個)は §10 と食い違う。commit 前に §0 だけでも 10b-2 の数に直すか、10b-1 の節を「経緯」に移すと一画面で読める。
- 突き合わせた数(どれも一致): 台帳 187 行(agents 79・cells 5・pois 9・知覚 5・外 89)・除外 111 項 490 属性(キャッシュ 127・定数 257・参照 106)・持ち主のクラス 46・未カバー 0(`ledger_uncovered_attrs.json`)・behavior の外の属性 88 本・`byte_check_after_answers.json` の `all_ok` true・テスト 52 件合格(作業木で 129.96 s)。10b-1 の時点の表の数(SoA と外の状態の軸ごとの件数・外の状態のバイト 3,323,095 B など)も `byte_check.json` と一致した。

## 4. テストの欠け

### 4-1 T1 の準備のテストは「揺らしが効いていない」を捕まえない(10b-1・10b-2)

- 再現: `tests/engine/test_state_ledger_10b.py:488`(10b-2 の行)の `arr[...] = _edge_value(...)` を `arr.copy()[...] = _edge_value(...)`(書き込みが列に届かない)に変えると、`test_t1_prep_ignoring_the_dead_columns_changes_nothing` の 5 構成が全部合格する。`done["n"]` は書いた回数を数えるだけで、効いたかは見ない。
- 同じ壊し方で、`test_t5_perturbing_no_columns_changes_nothing` は「今の final が動く」の確認で、実資産の `test_t5_and_t1_on_real_assets` は陽性対照で捕まる。T1 の準備にも「死蔵の列が今の final に入っているので final は動く」を足せば捕まる(agents の死蔵 3 列は今の final に入る)。

### 4-2 call_id は mock の道だけを固定している(10b-1)

- `_call_ref` を足した 5 か所のうち、10b のテスト(`test_pending_tuple_carries_fire_tick_and_call_id`)が通るのは mock の道だけ。艦隊の到着・艦隊の終端の drain・再生の到着・再生の終端は見ていない。
- 今は正しい: `_split_due` に「13 要素・`call_id == f"{発射}:{体}:{級}"`・発射 ≤ 適用」の assert を入れた写しで、`test_fleet_wiring`・`test_tape_deferred`・`test_response_delay`(38 件)が全部合格。ただし道ごとに通ったかは数えていない。
- `_call_ref` は艦隊の結果が持つ `call_id`(`llm/fleet.py:404`)を使わず式で作り直している。式は同じなので今は一致する。

### 4-3 T7 は壁時計の 1 本・既定 v3 だけ・平均(10b-2)

- `tests/engine/test_state_ledger_10b.py:710-718` は既定 v3 の `phase_seconds["checkpoint"]` を checkpoint 数で割った平均を 100 ms と比べる。重い構成(全腕で最大 31.9 ms)と、日が進むと増える O39(2-3)を見ていない。負荷の高い機械では偽赤になりうる(今は 1/10 程度なので余裕はある)。

### 4-4 `_split_due` を壊したときに 10b のテストだけでは捕まらない形がある(10b-1・参考)

- `<=` を `<` に変える(適用が 1 tick 遅れる・合成 4 構成で final が変わる)と 10b のテストは全部合格。既存の `test_response_delay` の 3 件が捕まえるので、回帰の組では捕まる。
- 適用分の並びを逆にする・体で並べ替える・残りの並びを逆にするは、合成 4 構成で final も呼数も変わらなかった(適用の順は `np.lexsort` で決まる=`engine/run.py:3093-3094`)。捕まらなくて正しい。

### 壊して捕まるか(指示の 8 種+追加・10b-1 の写しで実施。揺らしの 2 種は 10b-2 でも再確認)

| 壊し方 | 捕まった | テスト |
|---|---|---|
| 台帳の `hunger` を no | 捕まった | `test_ast_check_passes_on_the_current_source`・`test_t2_exclude_equals_deleting_the_columns`・`test_t4_soa_rows_move_the_hashes_by_their_axes[agents.hunger]`・`test_t5_perturbing_no_columns_changes_nothing` 2 件 |
| 台帳の `fatigue`(名前の表経由)を no | 捕まった | `test_ast_check_passes_on_the_current_source`・`test_t5_perturbing_no_columns_changes_nothing` 2 件 |
| AST の走査を `engine/` だけ | 捕まった | `test_ast_check_passes_on_the_current_source`・`test_ast_false_positives_band_and_b4_hash_are_explicit` |
| behavior-hash の exclude を空 | 捕まった | 15 件(`test_t2_behavior_hash_equals…`・`test_t4_soa_rows…` 5 件・`test_t5…` 2 件・`test_t1_prep…` 5 件・`test_two_day_run…` 2 件) |
| full-hash から外の状態を落とす | 捕まった | `test_t4_full_hash_detects_one_element_of_required_external_state`(1 件だけ) |
| `_call_ref` の call_id を "0" | 捕まった | `test_pending_tuple_carries_fire_tick_and_call_id` |
| `_split_due` の順序を変える(逆順・体で並べ替え・残りを逆順) | 捕まらない(結果が変わらない=同値の壊し方) | なし(4-4) |
| `_split_due` の境界を `<` に | 10b では捕まらない | 既存の `test_response_delay` 3 件(4-4) |
| 揺らしを効かなくする | T5 は捕まった・T1 の準備は捕まらない | `test_t5_perturbing_no_columns_changes_nothing` 2 件・`test_t5_weight_kg_is_read_only_at_initialization`(4-1) |
| 揺らしを効かなくする+陽性対照を外す | 上と同じ | 同上(合成世界の T5 は「final が動く」で捕まる。実資産の T5 は陽性対照だけが頼り) |
| 陽性対照だけを外す | 捕まらない(揺らしは効いているので正しい) | なし |

## 5. 問い

### 5-1 10d の full-hash は「日の締めの後」で取るか(2-2 と組)

最後の checkpoint は締めの前。日境界の再開で比べるのは締めの後の状態のはずなので、締めの後にもう 1 本取るか、締めを最後の checkpoint の前に動かすか(後者は final が動く)。

### 5-2 軸 1 が behavior で軸 2 が捨ててよいの行(O37 `presence._pulled_in_today`)を behavior-hash に入れたままでよいか

`engine/state_ledger.py` の O37 は behavior・discardable で、10b-2 から behavior-hash に入る。再開で作り直す前提の値なので、日境界の behavior-hash を resume と straight で比べる使い方をするなら食い違いの元になる。10d の判定に使うのが full-hash だけなら問題ない。

### 5-3 期限切れの項を消してよいか(2-3 と組)

会話の管理の 3 辞書の期限切れを消すと、挙動は変わらないが今の final 以外の 2 本(と 10e 以後の final)が変わる。消すなら 10e の版上げに束ねるのが筋か。

### 5-4 アジェンダ §5 の「金の生ログの溢れが日次センサスの金の項に効くかは 10b の実装で確かめる」が README に無い

`docs/design/v2-d102-10b-agenda.md` §5 の 2 項目め。K17 の判断の材料なので、確かめたかどうかを README に書いてほしい。

## 6. 確かめて問題がなかったこと

- **behavior-hash の意味**(10b-1・合成の全腕+edge と v2+edge・実資産 200 体で、10b-2・合成の全腕と実資産で再確認): 確保された SoA の全列(合成 93・62 列、実資産 66 列、10b-2 の全腕 91 列)を 1 列ずつ、テストと別の要素(配列の最後の要素)を別の量(整数 +3・浮動小数 ×2+1.5)で揺らし、behavior-hash は「軸 1 が behavior の agents・cells・pois の列」でだけ動き、full-hash は「軸 2 が discardable でない列」でだけ動いた(食い違い 0)。知覚 SoA は behavior-hash に入らない。discardable の外の行と `hash_skip` の属性は `full_items()` に無い。
- **2 日の合成世界ラン**: 実装役のテストに加え、古典+全腕の 2 日・1 体・予算 0(会話も呼も 0 件)・1 tick だけ・v1 の素のランで、2 本が毎 checkpoint 出て例外なし。外の状態が全部「無い」の場合は既存のテスト(`test_full_hash_marks_absent_owners`)で確認。
- **memo の共有**: digest は道筋だけで決まり(`engine/state_hashes.py:256-266`)、memo は checkpoint ごとに新しく作る(`engine/run.py:3877`)。full と behavior の間に状態を書く処理は無い。memo あり・なしで値が同じことはテストで固定されている。
- **`_feed_int_table` の正準性**: 鍵の昇順(`np.lexsort`)で流すので挿入順に依らない(順を変えた 2 つの辞書で一致)。型の件は 2-4。
- **`_split_due`**: 乱数で作った 2,000 組の保留の列と tick で、旧の 2 行の内包と結果が同じ。保留の組の読み手は `p[0]`〜`p[10]` の添字だけで、13 要素に増えても壊れない(`engine/run.py:3089-3120`)。
- **台帳の SoA の行**: 材料 §1-1〜§1-4 の表と軸 1・軸 2・死蔵を機械で突き合わせ、違うのは知覚の `heading`・`task_flag`(材料は「入れる」、台帳は no=親の宣言)だけ。外の状態の行の違い(O23・O26・O31・O55・O58・O60・O61・O65)は親の宣言か README §9 問 4 に理由がある。
- **費用**: 10b-1 の写しで 1 checkpoint の合計 最大 32.8 ms(うち O39 25.1 ms)、10b-2 で 既定 v3 最大 12.9 ms・記憶+関係 25.2 ms・全腕 31.9 ms(どれも 5,000 体・実資産)。

## 7. 手順(再現用)

- 一時ディレクトリ(短いパス)に `git archive HEAD src tests docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28` を展開し、HEAD 側は `PYTHONPATH=<写し>/src`・`SHIBUYA_BUDGET_MD=docs/design/v2-budget-declaration.md` で、リポのルートを作業ディレクトリにして `cli.run(n_agents=5000, seed=1, world_dir="data/world/v2", tape_path=…, **構成)` を回す。比べたのは final・呼数・`checkpoints` の全欄・テープの calls の全列と blocks の sha256・manifest(`state_hashes` を除く)。
- 壊して捕まるかは、作業木の写しの上で 1 か所ずつ文字列を置き換え、`tests/engine/test_state_ledger_10b.py` を `-o addopts= -p no:cacheprovider` で回した(写しには実資産が無いので実資産のテストは飛ぶ。揺らしの件の実資産のテストは作業木のルートで別に回した)。
- 検算のスクリプトは自分の一時ディレクトリに置いた(リポには足していない)。

## 8. 再検収(10b-3・2026-10-04・差分だけ)

> 実装役の直し(台帳 `state-ledger/10b-3`・README §0・§11・§12)を、反映後の作業木の写しで見た。何も直していない。

### 8-0 まとめ

| 種類 | 残った件数 |
|---|---|
| 結果を動かす欠陥 | 0 |
| 潜在の欠陥 | 1(8-3-1) |
| 記録の誤り | 0 |
| テストの欠け | 0 |
| 問い | 1(8-3-2) |

- 前回の指摘(潜在 6・記録 3・テスト 4・問い 4)は、潜在 2-3(会話の管理の期限つきの辞書)を除いて直っている。2-3 は README §11-3 で「10e へ送る」と宣言された(持ち越しとして数えない)。
- **byte-check は一致**: 既定 v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439 で、final の全桁・呼数・checkpoint 4 点の全欄・prompt_hash・calls の全列・blocks が HEAD(bbe7e77)の写しと一致。manifest の差は `state_hashes` と新しい欄 `state_hashes_end_of_day` だけ。最後の checkpoint の behavior-hash は `535b040a…`・`aee7c77d…`、締めの後の full-hash は `1e2426f4…`・`10c869e4…`(親の伝えた値と一致)。
- 結論: **直しは正しい**。壊し方 10 種(下の表)はどれもテストが捕まえる。

### 8-1 壊して捕まるか(反映後の写しで 1 か所ずつ壊し、実資産のテストも含めて 70 件を回した)

| 壊し方 | 捕まった | テスト |
|---|---|---|
| O39 の `ordered` の印を外す | 捕まった | `test_p1_ordered_rows_keep_the_insertion_order`・`test_p1_full_hash_sees_the_order_of_ordered_rows` |
| O8 の `ordered` の印を外す | 捕まった | `test_p1_ordered_rows_keep_the_insertion_order`(`_gist_order` は OrderedDict なので印が無くても順は残る=値は守られる) |
| 直列化で順の印を無視する(速い道も普通の道も昇順に戻す) | 捕まった | `test_p1_…` 2 件 |
| 速い道の整数の判定を `type(x) is int` に戻す | 捕まった | `test_p4_numpy_integers_take_the_same_bytes_as_python_ints` |
| 締めの後の 2 本を消す | 捕まった | `test_p2_end_of_day_hashes_are_reported_separately`・`test_p2_end_of_day_differs_after_the_ledger_close` |
| 実行時に持ち主へ属性を 1 つ足す(クラスの外から `conv._sneaky_state = 1`) | 捕まった | `test_p6_runtime_owner_instances_are_fully_declared`・`test_p6_runtime_check_catches_an_undeclared_attribute` |
| クラスの `__init__` に属性を 1 つ足す(`ConversationManager._new_state`) | 捕まった | `test_every_attribute_of_the_owner_classes_is_declared`・`test_coverage_fails_when_a_new_state_is_not_declared`・`test_p6_…` 2 件 |
| 揺らしを効かなくする(前回 T1 の準備が捕まえなかった形) | 捕まった | T5 の 3 件・**T1 の準備の 5 構成**・実資産の 1 件(計 9 件) |
| AST の `getattr(持ち主, 変数)` の検出を外す | 捕まった | `test_ast_check_passes_on_the_current_source`・`test_p5_ast_blind_spots_are_caught` 2 件 |
| `OWNER_ALT_CLASSES` から `ledger.money` を外す | 捕まった | `test_every_attribute_of_the_owner_classes_is_declared`・`test_coverage_fails_when_a_new_state_is_not_declared` |

AST の死角(前回の表の 5 つ)は、自分の一時ファイルで 5 つとも捕まった(`getattr` の名前の表・引数、`.arrays.get`、`attrgetter`、組の代入)。

### 8-2 確かめたこと

- **締めの後の 2 本**(`engine/run.py` の `state_hashes_end_of_day` を作る節・`ledger.end_of_day` とセンサスの後に置かれている): 合成世界の全腕 100 体では最後の checkpoint の値と同じ、実資産 300 体の v3 既定では違う。どちらも、ランが返った後に同じ持ち主でハッシュを取り直した値と一致する=締めの後の状態を見ていて、その後に状態を書く処理は無い。実装役の読みは正しい。
- **費用**: README §11-7 の値(既定 v3 最大 13.4 ms・全腕 39.3 ms)は親の上限 100 ms の中。checkpoint ごとの時間 `checkpoint_seconds` は manifest に出ない(壁時計)。
- **順の印の漏れ**: full と behavior に入る属性のうち、実行時に辞書か集合だったもの(合成の全腕と実資産の記憶+関係で 23 本)を挙げ、印の無いものを走査する箇所を grep した。`intent_layer._payload`(全部消すか `sorted`・`engine/intent.py:306,475`)・`ledger.money._lines`(足し合わせと書き込みの許可=順に依らない・`economy/ledger.py:283,292`)・`runner.rail._return_queue` と `presence._extra`(鍵で `pop` するだけ)・`run_day.replay_inbox`(`pop` と `sorted`)・集合の `_gist_done`・`fleet_waiting`・`bridge._interned`(含むかを引くだけ)。順で挙動が変わる印の漏れは見つからなかった。README §11-1 の表と同じ結論。
- **`OWNER_ALT_CLASSES` の網羅**: 道筋に入りうるクラスを grep した。`poi_resolver.chooser` は `NearestChooser`・`ClassicalChooser` の 2 つ(`engine/chooser.py:115,146`)、`Ledger` の子クラスは `cli._HouseholdWalletLedger` だけ、`bridge` は `LLMBridge` だけ(`engine/run.py` の `bridge = LLMBridge(`)。漏れは無い。
- **numpy の整数の速い道**: `{1: 2}` と `{np.int64(1): np.int64(2)}` が同じバイト列になり、`bool` は通らない(`engine/state_hashes.py` の `_is_int`)。挿入順に依らないこと(印の無い辞書)と、印のある辞書では順が変わると値が変わることもテストで固定されている。
- **金の生ログの溢れ**: `Ledger.raw_rows()`(`economy/ledger.py:692`)の呼び手は src に無い(grep で 0 件)。README §11-4 の読みと同じ。
- **記録**: README §0(187 行・除外 112 項 491 属性・70 件)は台帳とテストの数と一致。基準の書き方は bbe7e77 に直った。

### 8-3 残った指摘

#### 8-3-1 潜在の欠陥: AST の検査に死角が少し残る

自分の一時ファイルで、`fail_streak`(no)を読む次の書き方はまだ捕まらない。

| 書き方 | 結果 |
|---|---|
| `reg.money[a], reg.fail_streak[a] = g(reg.money[a] - reg.fail_streak[a])`(左辺は組・右辺は組でない式) | 捕まらない(`_is_self_update` は右辺が組でないと「左辺のどこかに同じ列がある」で自己更新にする) |
| `x = reg.fail_streak[a] = reg.fail_streak[a] + 1` の後で `x` を使う(連鎖の代入) | 捕まらない |
| `getattr(ag8, n)`(持ち主の名前が `SOA_BASE_TAILS` に無い) | 捕まらない(`_soa_like` で SoA らしい名前のときだけ見る) |
| `reg.fail_streak[a] = 0 if (x := reg.fail_streak[a]) > 3 else 1` の後で `x` を使う(代入式) | 捕まらない |

- 今の src では見逃しは無い: 軸 1 が no/diag の列を左辺に持つ文は 5 か所で、どれも本当の自己更新(前回 2-5)。変数の名前で `getattr` する箇所に SoA の持ち主は無い。
- 影響は小さい。揺らし試験(T5)が動的に補う。直すなら、右辺が組でない組の代入は自己更新にしない(安全側に倒す)だけで 1 つ目と 2 つ目は塞がる。

#### 8-3-2 問い: 日をまたぐランの日境界の締めと full-hash

- 締めの後の 2 本はランの最後に 1 回だけ取る。`runner.end_of_day` もランの最後に 1 回(`engine/run.py` の `runner.end_of_day(max(0, total_ticks - 1))`)で、金と物の台帳は 1 日のランだけ。`run_day(sim_days=2 以上)` の途中の日境界には締めも締めの後のハッシュも無い。
- 10d で「2 日の通しのラン」と「1 日目の終わりで保存して再開したラン」を比べるとき、通しの側の 1 日目の終わりに比べる値が無い。10d の設計(日をまたぐランでも日ごとに締めるのか、比べる値をどこで取るのか)で決める必要がある。10b の範囲では問題ない。

#### 補足(数えない)

- O39 の印で、鍵で引くだけの辞書(`_refusal_until` など)も挿入順が full-hash に入る(README §11-1 で「安全側」と宣言)。10d の復元は辞書を挿入順のまま戻す必要がある(昇順で戻すと、挙動は同じでも full-hash が食い違う)。10d の直列化の約束に書いておくとよい。
