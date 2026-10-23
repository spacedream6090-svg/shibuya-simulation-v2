# 第 1 期 1-1 時計 T0 の検収(別の検収役・Opus 5.5)

- 立場: 実装は見ていない。作業木の枝 `1-1/t0`(HEAD `3e0ff73`・未 commit)を読むだけで確かめた。書いたのはこのファイルだけ。
- 正: 口の約束「## 1-1 時計 T0」(口・約束 4 つ・受入の試験・〔決定〕)・計画 第 1 期 1-1 の行(TM9 を含む)・指示書 10-12 の TM7・TM8・1-0 の規則(ハッシュに入る名は変えない)。
- 自分で回したもの: byte-check 4 構成(本体 HEAD の src と作業木の src)・HEAD と作業木の AST の突き合わせ(独自の道具)・build と solar の関数の実行の突き合わせ・`TickCtx.of` の同値の検算・設定の節の道筋の差・`lint-imports`・発注の試験の集合。作業用の道具はこのセッションの作業用の置き場に置いた(リポには入れない)。

## 判定

**条件つき受入**。結果不変・同値・直書き 0・乱数の鍵・TM9 の欄は確かめられた(下の 1・2・3・5・6・7 は ✓)。条件は 3 つ(§欠陥の M1・L1・L4)。どれも結果を動かさない。

## 1〜8 の確かめ

### 1. 結果不変 ✓

- 実装役の `byte_check_t0.json`: 19 構成すべてで比べた 25 欄が「同じ」(`moved` は空・`error` の行なし)。
- 自分の byte-check(`byte_check_10e.py side`・5,000 体・seed 1・1 日・テープつき・4 並列): HEAD の側は本体の src、T0 の側は作業木の src(子プロセスの `PYTHONPATH` が作業木の src を指し、`shibuya.core.time_consts` が import できることを別に確かめた。HEAD の側には無い)。`compare` の結果は 4/4 構成で 25 欄とも同じ。テープの parquet のバイト数も同じ。

| 構成 | final(全桁の頭 16) | 呼数 | blocks の行 | 動いた欄 |
|---|---|---:|---:|---|
| w6_v3_default | `5f7ae9ff24005314` | 65,597 | 7,975 | なし |
| w6_v3_activity_off | `e0054a837c6ec4c1` | 50,301 | 2,660 | なし |
| w6_v1_default | `24375ee3dab349e8` | 51,835 | 2,731 | なし |
| v3_mem_rel | `73a78288ab5e1498` | 69,111 | 8,544 | なし |

- 補足: 比べる JSON(`compare` の出力)には側ごとの src の印が残らない。どちらの src で回したかは `side` の出力の `src_is_worktree`(HEAD 側 真・T0 側 偽=本体のスクリプトから回したため向きが逆)と、上の import の確かめで見た。

### 2. 同値 ✓

- 試験 `test_t0_tickctx_equivalence.py`: 2 日の全刻みで `td`・`day`・`tod_s == td*60`・`t_ns == T*60*10**9`・`t_sim_ns(T) == t_ns`・`split_t_sim_ns` の逆。幅 1・30・60・300 秒でも関係が成り立つ。進行役(`conductor`)がランの幅を渡すことを合成の世界の 30 刻みで見ている。
- 自分の検算(作業木の src): `T` = 0〜30 日の全刻み(43,200)+`max_tick()` までの乱数の 20,000 点で、`TickCtx.of(T, 1440)`(1-0 の呼び口)と `of(T, 1440, 60)` が同じ・`tod_s == td*60`・`t_ns == T*60*10**9`・`day == T//1440`・`td == T%1440`・`t_sim_ns(T) == t_ns`・`t_ns` と `tod_s` は `int`。最初の 3 日は `time_key_from_t_ns == run_tick_key`。全部成り立った。

### 3. 直書き 0 ✓(数え方の外に残りあり=L1)

- AST の試験 `test_t0_literal_count.py` は、リテラル `1440`・`86400`・`3600`(書き方と int/float を問わない)と、`//`・`*`・`/`・`%`(累算代入を含む)の項の `60`・`24` を数える。発注の 6 つの形(`1440`・`86400`・`// 60`・`* 60`・`/ 60`・`% 1440`)を含む。allow の表 `time_literal_allow.json` は空(`{}`)。理由つきで残した時間の直書きは無い。表の古い行と負の対照(仮のファイルの 11 行を形ごとに検出・文字列・演算でない 60・足し算は数えない)もある。
- 件数の再計算: 同じ数え方を HEAD の `src/shibuya` にかけると **281 か所・55 ファイル**(記録と一致)、作業木では 0。
- build の段の値が変わっていないことの確かめ方は記録 §2-5 にある(AST の同値・16 個の純粋な関数の出力の sha)。自分でも独立に確かめた。
  - **AST の突き合わせ(独自)**: 変えた src 69 本について、作業木の `time_consts` の名をその値に戻し、docstring と `time_consts` の import を落とし、モジュールの重複定義を外して HEAD と節点ごとに比べた。60 本は完全に同じ。energy.py の 1 本は関数の中で `weekly` から同じ名を import し直していて見かけの差が出るだけ(値は両方 1,440)。残る 8 本(`types.py`・`rng.py`・`manifest_sections.py`・`run.py`・`state_io.py`・`table.py`・`boxes.py`・`conductor.py`)は意図して足したもの。`types.py` と `rng.py` は足した名(`SimTime`・`time_key_from_t_ns`)を外すと HEAD と同じ。演算子は 1 つも変わっていない(`//` が `/` になった所は無い)。docstring 以外の文字列(エラーの文・道筋・列の名)も同じ。
  - 浮動小数のリテラルを int の名にした所は 38 か所。全部、真の割り算 `/` の項か、もう片方が浮動小数のリテラルの掛け算(`5.0 * 60.0`・`19.0 * 60.0`)だった。値も型も変わらない(numpy 2.5.3・NEP 50 でも同じ)。
  - **実行の突き合わせ**: `build/field/common.hhmm_to_min`・`min_to_hhmm`(00:00〜47:59 と −5〜2,884 分)・`build/field/w13_weather.sun_times`・`solar_elevation_deg`・`engine/solar` の 3 関数(2025 年の 366 日 × 7 時刻)を、HEAD と作業木の src で別々のプロセスで呼んだ。11,992 個の出力の sha は両側とも `87d1bead2867e552`。

### 4. 「tick」の語 ✓(試験の形)/ 約束 (3) の範囲は ✗ 寄り(=M1)

- 凍結の表 `tick_word_allow.json` は 158 名。HEAD の識別子の集合(同じ数え方)と作業木の集合はどちらも 158 で、差は 0。試験は、表の外の名(増えた)と、使われなくなった表の名(古い)の両方で落ちる。負の対照(識別子 6 種・注釈と docstring の引用の内外)もある。
- 理由の分類を確かめた: 「状態台帳の鍵・道筋」に分けた 44 名は全部 `engine/state_ledger.py` に語として出る。ほかの 114 名は 1 つも出ない。分け方と食い違わない。
- ハッシュに入る名・CLI の引数・manifest の既存の欄・テープの列は変わっていない。根拠: AST の突き合わせで、文字列の定数の差は `__all__`・manifest の 4 欄の追加・`table.py` の読みの宣言 2 行(`cfg.tick_seconds` を足した)だけ。`engine/state_ledger.py` と `tests/engine/systems/writes_soa_frozen.json` は差分なし(SoA の列は増えていない)。
- 注釈と docstring は `core/` と `engine/systems/` で引用の外の「tick」が 0(試験が見る)。

### 5. TM9 の欄 ✓

- 置き場: manifest の末尾に `calls_by_model`(観測)・`clock_kind`・`step_seconds`・`bridges_count`(設定)。日次の記録(`daily` の各行)に同じ 4 つ。manifest の一番上の鍵(108 個・順も)は `manifest_keys_frozen.json` に凍結し、TM9 の 4 つが末尾にあることも試験で見ている。
- 既存の欄の値が変わらないこと: 実装役の `manifest_check_t0.json` で 7 本とも final が同じ・既存の欄 1,695〜2,211 個が同じ・足したのは 14 葉・予想外の追加と消えた欄は 0。
- 10f の凍結の更新(発注の範囲の外=要確認だった点): `CONFIG_PATHS_SHA256` の前後を自分で計算した。HEAD の設定の道筋は `58bb3124…`、作業木は `d16f26e6…`。差は `bridges_count`・`clock_kind`・`step_seconds` の 3 本が増えただけで、既存の道筋の順と節は 1 つも変わっていない(`PATHS` の追加は 4 行=上の 3 本+`calls_by_model` 観測)。「増えた欄だけ」の更新として妥当。
- final と behavior-hash が manifest を含まないこと: `final_hash` は最後の checkpoint の `combined`(状態台帳の道筋から作る)。`engine/state_ledger.py` に `daily_records`・manifest の行は無い。試験 `test_tm9_fields_do_not_feed_the_final_hash` は `clock_kind` を書き換えても final と呼数が同じことを見る。byte-check の final・behavior・full が同じ。
- 日次の LLM の数: 日ごとの和=総数=診断の行の `calls` の日ごとの和を試験で突き合わせている。再開したランの最初の日は再開した時刻からの分(止めたランの残り+再開したランの分=通しの 2 日目)も試験にある。

### 6. 乱数の鍵 ✓

- `rng.time_key_from_t_ns` は src に呼び手が無い(試験 `test_no_caller_yet` が AST の呼び出しを数える。自分の grep でも 0)。`run_tick_key` の `86_400` → `SECONDS_PER_DAY` は同じ値。鍵の値は変わらない(byte-check の `rng_scheme` と final が同じ)。

### 7. 試験 ✓

- 作業木で発注の集合(`tests/engine/time`・`tests/engine/systems`・`test_sim_time_T.py`・`test_calendar.py`・`test_resume_10d.py`・`test_10a_review_fixes.py`)を 1 本で回した(`PYTHONIOENCODING=utf-8`・data あり): **262 passed・0 failed・飛ばし 0(9 分 21 秒)**。実装役の記録にあった並列の子プロセスの落ち(`test_world_resume_equals_straight_at_every_tick[750]`)は 1 本の実行では起きなかった。
- `lint-imports`(作業木の src): 5 契約とも守られている(183 ファイル)。

### 8. 抜け道

- (a) 定数の 2 重の定義 ✓: `core/types.py` は `NS_PER_SECOND`・`SECONDS_PER_MINUTE` を `time_consts` から再輸出し、`DEFAULT_TICK_SECONDS = STEP_SECONDS`・`MINUTES_PER_SIM_DAY = MINUTES_PER_DAY` と名で別名にしている(`is` で同じ物)。値を書いているのは `time_consts` だけ。モジュールごとの重複定義 7 つ(`MINUTES_PER_DAY: Final[int] = 1_440`)も消えて import になった。
- (b) `TickCtx` の新しい欄の読み手 ✓: src に `.t_ns`・`.tod_s` を読む所は無い(`boxes.py` の定義と docstring だけ)。進行役は幅を渡すだけ。
- (c) 整数の切り捨て ✓: AST の突き合わせで演算子は全部同じ。`time_consts` の定数は全部 int(試験が型を見る)。
- (d) 記録の絶対パス・ホスト名 ✓: 記録・JSON・新しい試験・`time_consts.py` に絶対パス・ホスト名・個人名は無い。`tools/scan_secrets.py` は CLEAN。

## 欠陥(重さ順)

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | 口の約束 1-1 の約束 (3)・`tests/engine/time/tick_word_allow.json`・記録 §3・§7 | 約束 (3) は「tick」の語を**識別子と docstring から消す**(名は別名で段階的に・ハッシュに入る名だけ残す=〔決定〕〔1〕)。実装は識別子を 1 つも替えず、ハッシュにもテープ・manifest・CLI にも入らない 110 名(公開 85・局所 17・箱 8=理由「段階的」)も凍結の表に入れた。docstring と注釈は `core/` と `engine/systems/` だけ直し、ほかに 707 行が残る。記録には書いてある(隠してはいない)が、〔決定〕〔1〕が残してよいとしたのはハッシュの鍵の名だけ | 親が決める: (i) 段階的として受けるなら、10-13b §0-3 の仮採用として PENDING §1-1 に載せ、外す段(例: T1)を決める。凍結の表の理由に「外す段」を書き、残りの数(110 名・707 行)を記録の §0 に出す。(ii) T0 で直すなら、110 名を別名で置き換える(結果は動かない)。 |
| L1 | 低 | `build/lang/w14_signage.py:147`・`build/field/w12_external_nodes.py:335`・`build/sched/pool_facts.py:235,238`・`build/field/w7_planspec.py:481`・関数の既定の引数 `tick_seconds: int = 60`(自分の数えで 29 か所)・`range(24)`・`np.zeros(24)`・`minlength=24` | 数え方(二項演算と 3 つのリテラル)の外に、時間の意味の直書きが残る。`divmod(m, 60)` は `// 60` と `% 60` そのもの。`Fraction(60) / Fraction(tph)` は 1 時間の分。`min(1439, …)` は 1 日の分 − 1。`SPAN_MIN = 2880` は 2 日の分。記録 §7 は既定の引数・`range(24)`・`minlength=24`・分のリテラルは書いているが、`divmod`・`Fraction(60)`・`1439`・`2880` は書いていない | `divmod(x, 60/24/1440)` を数え方に足して 1 か所を置き換え、`Fraction(60)` を `Fraction(MINUTES_PER_HOUR)` にする。`1439`・`2880` と既定の引数の 60(刻みの幅=T1 で触る所)は記録 §7 の一覧に足す(置き換えるなら既定の引数は `DEFAULT_TICK_SECONDS` に) |
| L2 | 低 | 記録 §2-2・`core/time_consts.py` の docstring | 「幅を変える段では `grep STEPS_PER_` で拾える」とあるが、HEAD からある「刻みの数を分の名で割る」所は拾えない(例 `engine/presence.py:1796`・`:1830` の `tick % MINUTES_PER_DAY`・`:623` の `ticks: int = MINUTES_PER_DAY`)。既定の引数 `tick_seconds: int = 60` も同じ | 記録の言い方を「T0 で置き換えた所は `STEPS_PER_` で拾える。HEAD からある名の使い方と既定の引数は別に洗う」に弱める |
| L3 | 低 | 口の約束 1-1 の口・`core/types.py:106`・`engine/systems/boxes.py` | 口は `TICK_SECONDS=60` と書くが、実装は `STEP_SECONDS`(「tick」の語を避けた=妥当)。記録に口との違いとして書いていない。`SimTime` は足したが注釈で 1 か所も使っていない(`t_sim_ns(...) -> int`・`TickCtx.t_ns: int \| None`)。「正にし」は名札だけ | 記録 §7 に 1 行(口の名の違いと理由)。注釈を `-> SimTime`・`t_ns: SimTime \| None` にする(値は変わらない) |
| L4 | 低 | 記録 §2-5・§7 | 同値の確かめの道具(`ast_equiv.py`・`build_probe.py`・`manifest_check_t0.py` ほか)がセッションの作業用の置き場にあり、リポに無い。10e・10f は確かめの道具を記録のフォルダに置いている。セッションが終わると §2-5 の確かめを再現できない | 少なくとも `ast_equiv.py`・`build_probe.py`・`manifest_check_t0.py` を記録のフォルダへ(絶対パスを消してから) |
| L5 | 低 | `tests/engine/time/test_t0_no_tick_word.py` | 凍結は名の単位で、場所の単位でない。`tick`・`ticks`・`tick_seconds` などが表にあるので、新しいコードがこれらの名を新しいファイルで使っても落ちない(「新しい名を足すと落ちる」は正しいが、語は既存の名で広がる) | 名ごとの出る場所(ファイルの集合)か数を凍結する。T0 の門としては必須でない |
| L6 | 低 | `core/time_consts.py`・`core/rng.py:139` | `seconds_to_steps` の `seconds` は `bool` を受ける(`operator.index(True)` = 1)。記録 §1 の「float と bool は落とす」は幅だけに当たる。`time_key_from_t_ns` は幅を `int()` で丸めるので 60.5 を黙って 60 にする(`time_consts` の `operator.index` の規則と違う)。呼び手は無い | 記録の言い方を直すか、型の検査をそろえる |

- 欠陥ではない確かめ: 作業木の直下の `_bc/`(実装役の生の出力)は検収の終わりの時点で無くなっていた。自分の `_bc_review/` は検収の後に消した。`git status` の未追跡に `parent_head_vs_t0_4cfg.json` と記録の §8(親の検収)が検収の途中で増えた(親の作業)。

## 条件(受入の前に)

1. M1: 約束 (3) の範囲を親が決め、記録と PENDING に残す。
2. L1: `divmod` と `Fraction(60)` を数え方に入れるか、記録 §7 の「数え方の外」の一覧に足す(`1439`・`2880` も)。
3. L4: 同値の確かめの道具を記録のフォルダに置く。

L2・L3・L5・L6 は任意(記録の言い方の直しで足りる)。
