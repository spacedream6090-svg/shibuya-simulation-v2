# 10d の検収(別のサブ・Opus 5.5)

> 実装役と別の人の検収。実装の経緯は知らない。直していない(この記録だけを書いた)。
> 基準: HEAD `8486f9c` を `git archive` で短いパスの作業用ディレクトリへ展開した写し(10d の前)。比べる相手: 作業木(10d 入り・実装役は作業を終えている)。
> パスは `src/shibuya/` を省略。行番号は 10d の作業木。絶対パスは書かない。検算のスクリプトと一時ファイルは作業用ディレクトリに置いた(親が消してよい)。

## 0. まとめ

| 項目 | 結果 |
|---|---|
| byte-check(既定 v3・帰無・1 日・再開なし) | **一致**。final・呼数・checkpoint 4 点の combined・テープ(calls の全列と prompt_hash・blocks)が HEAD の写しと同じ。behavior-hash と full-hash は台帳の版が変わったので違う(宣言どおり)。manifest の差は新しい欄だけ(下の 1) |
| resume == straight(mock 5,000 体・世界資産・2 日・既定 v3・自分のスクリプト) | **一致**。止める T=753(日中・5 分帯の途中)と T=1440(日の境目)を別のプロセスで再開。全 checkpoint(毎 tick・2,880 点)の combined・behavior・full、tick ごとの呼数、テープの (tick・体・級・prompt_hash・call_id) の並び 142,043 行、日の締めの記録 2 日分、最後のお金が通しと同じ。**ただし診断の列 `conversations_opened` だけ再開の最初の tick で違う**(潜在 L1) |
| 指摘の件数 | 結果を動かす欠陥 1・潜在の欠陥 6・記録の誤り 5・テストの欠け 5・問い 4 |

いちばん重いのは **D1(2 日目からプロンプトの天候と体の天候が別の日になる)**。10d の「B3 のキャッシュの鍵に日を足した」直しで表に出た。次は **L2(名指しの店の閉店の控えが保存されない=実 LLM のランで再開がずれうる)**。どちらも mock の一致の試験では見えない。

## 1. byte-check

- 手順: 自分のスクリプト(作業用ディレクトリの `bc.py`)で、HEAD の写し(`PYTHONPATH` を写しの `src` に)と作業木を mock 5,000 体・seed 1・1 日・テープつきで回し、final・呼数・checkpoint(tick・combined・behavior・full)・calls.parquet の全列の sha・prompt_hash の並び・blocks の sha・manifest を JSON に落として比べた。構成は `wave2_bytecheck.py` の `w6_v3_default` と `w6_golden_null_arm`。
- 結果:

| 構成 | final | 呼数 | checkpoint の combined | calls の全列・prompt_hash・blocks |
|---|---|---|---|---|
| 既定 v3 | `993276d5e5bb5cbe`(両方) | 69,978(両方) | 4/4 一致 | 一致 |
| 帰無 | `72cb9cd52982da74`(両方) | 100,439(両方) | 4/4 一致 | 一致 |

- behavior-hash と full-hash は全点で違う(台帳の版 `10b-3` → `10d`・O90〜O93 の行が足された)。README §10-1 の宣言どおり。
- manifest の差: 作業木だけにある欄は `daily`・`day_heads`・`finished`・`parent_run`・`resumed_at_T`・`resume/*`(14 欄)・`state_hashes/full_external_bytes_by_row/O37・O90〜O93`。値の違う欄は `state_hashes/*`(版と 2 つのハッシュとバイト数)と `calendar/holiday_csv_md5`・`holiday_csv_range`。後の 2 つは**私の写しに祝日の CSV(gitignore 下のデータ)を入れなかった**ためで、10d の変更ではない(暦のコードは 10d で変わっていない)。新しい欄以外の値の違いは無い。

## 2. resume == straight(自分で)

- スクリプト: 作業用ディレクトリの `rs.py`(1 本のランを回して JSON に落とす)と `cmp_rs.py`(比べる)。`first_diff.py` は使っていない。`cli.run`・`sim_days=2`・`checkpoint_every=1`・全部のランがテープを書く。通しのラン 1 本と、止めたラン 2 本(T=753・T=1440)を並べて回し、その後で再開のラン 2 本を**別のプロセス**で回した。
- 比べたもの: 止めたラン+再開のランの checkpoint を合わせて 2,880 点すべて(combined・behavior・full)、診断の行の全列(tick ごと)、テープの行の並び(順序つき・call_id まで)、日の締めの記録(センサスの行・締めの後の 2 つのハッシュ・体の数・お金)、最後のお金、呼数の合計。

| 止めた T | checkpoint 不一致 | tick ごとの呼数 | テープ 142,043 行(順序と call_id 込み) | 日の締め 0・1 日目 | 呼数の合計 | 診断の列の違い |
|---|---|---|---|---|---|---|
| 753(12:33) | 0 / 2,880 | 一致 | 一致 | 一致 | 31,604 + 110,439 = 142,043 | `conversations_opened` が T=753 で 1 → 97 |
| 1440(日の境目) | 0 / 2,880 | 一致 | 一致 | 一致 | 69,978 + 72,065 = 142,043 | `conversations_opened` が T=1440 で 0 → 205 |

- 実装役の記録との突き合わせ: 実装役の `resume_check_v3_default_5000.json` の通しの final `47e0a85b02797e23`・呼数 142,043 は私の通しと同じ。日の境目 1440 の状態のファイルの full-hash `3d301f1d…` も私のファイルと同じ。日の境目で止めたランの final は 1 日のランの golden `993276d5e5bb5cbe`/69,978 と同じ(1 日目の頭までは 1 日のランと同じ道を通る=筋が通っている)。
- 世界資産 300 体の境界の試験(作業用ディレクトリの `edge.py`・毎 tick・全点の 3 つのハッシュ・呼数・final・日の締め): 5 体のラン(T=700)・T=1(最初の tick の後)・T=1439(日の最後の tick の手前=締めは再開側)・T=1441(2 日目の頭の直後=再開で 1 日目の表を張り直す道)・3 日のラン(T=2900=張り直しを 2 回)・counter の乱数+顕著行為の率 ×1000(T=753)・1 日のラン(T=700)・classical(T=1441・会話 0 件)。**8 件すべて一致**。

## 3. 結果を動かす欠陥

### D1 2 日目から、プロンプトの天候(B3)と体の天候(環境の過程)が別の日の値になる

- 何が起きるか: 環境の過程は日の頭で `pick_day(日)` により「再生の実日」を引き直し、暑さの段と WBGT をその実日の行(`_row`)から読む(`engine/processes/environment.py:270-274`)。一方、描画の B3 は**暦の日付**(`tc.when`)で W13 を引く(`perception/renderer.py:620-628` の `weather_by_date_hour[(日付, 時)]`)。1 日のランでは暦の開始日=0 日目の再生の実日(`engine/run.py:2665-2670`)なので両者は同じだが、2 日目からは暦の日付=開始日+1 日で、再生の実日とは別の日になる。
- 既定の世界では、`prefer_shadow_days=True` で再生の実日は影のある 1 日(2026-07-28)に絞られるので、**環境の過程は毎日 07-28 のまま**(日の頭の張り直しで値が変わらない)。ところがプロンプトは 2 日目に 07-29 の W13 の行を読む。
- 再現: 作業用ディレクトリの `relay.py`(`WorldProcessRunner.relay_day` を包んで前後の値を控える・300 体・3 日)で、1 日目・2 日目の張り直しの後も `environment.replay_date` が `2026-07-28`・層 `平日|雨` のまま。5,000 体の 2 日の通しのテープの blocks に、12 時台の B3 として「天候は曇・暑さは暑い」(07-28 の 12 時)と「天候は薄曇・暑さは厳しい暑さ」(07-29 の 12 時)の 2 種類が並ぶ(後者が 2 日目)。W13 の 12 時の行: 07-28 は「曇・暑い」、07-29 は「薄曇・厳しい暑さ」。
- 10d との関係: 10d の初版の前は B3 のキャッシュが 0 日目の行を使い回していたので、たまたま環境の過程(07-28)とそろっていた。10d の「鍵に日付を足した」直し(README §2-2 の 5・§9-4)で、プロンプトだけが暦の日付の天候に動いた。README は「2 日目のプロンプトの天候が 0 日目のままだった」を欠陥として直したと書くが、直した後は**体の暑さと言葉の暑さが食い違う**。
- 範囲: 複数日のランの 2 日目から。1 日のランは動かない(byte-check で一致)。再開は通しと同じ値になる(どちらも同じ食い違い)。
- 直し方の候補(決めるのは親): (a) 描画の天候を「その日の再生の実日」で引く(環境の過程と同じ源)/(b) 環境の過程を暦の日付の行で引く(影の面が 1 日しか無い制約と衝突)/(c) 10d の範囲では 2 日目からの天候を宣言つきで 0 日目に固定し、10g の前に決める。問い Q1。

## 4. 潜在の欠陥

### L1 再開の最初の tick の診断の行 `conversations_opened` が累計になる

- `engine/run.py:3090` の `prev_sessions = 0` は再開でも 0 から始まり、`conv.n_opened` は保存から戻る(O91)。最初の tick の行が `conv.n_opened - 0`=止めた時点までの累計になる(T=753 で 97・T=1440 で 205。通しは 1 と 0)。
- 影響: 結果(ハッシュ・呼数)は動かない。診断の行を親と子のランで足すと会話の開いた数を二重に数える。`prev_tape_misses`(`bridge.n_tape_misses` は保存しない計数=どちらも 0 から)は食い違わない。
- 直し: 再開では戻した後の `conv.n_opened` で `prev_sessions` を置く。

### L2 名指しの店の即時閉店の控え `poi_resolver.named_closed` が保存されない(O26 の軸の誤り)

- `engine/poi_target.py:472` が体ごとに `(店, 失敗の tick)` を控え、描画の B6 が `named_closed_lookup`(`engine/run.py:495-520`)経由で読んで、**プロンプトに「(店名は閉店中・07:30 に開く)」の 1 句を足す**(`perception/renderer.py:2493-2511`。体の `last_result_tick` が控えの tick と同じときだけ)。既存のテスト `tests/engine/test_stage3_small_fixes.py:134-145` が prompt_hash が変わることを確かめている。
- ところが台帳では O26(`state_ledger.py:348`)の中で軸 1 diag・軸 2 discardable=保存しない。再開では控えが空になるので、止めた時刻をはさんで「失敗の直後の起床」がある体のプロンプトが通しと違う。
- mock ではこの道を通らない(5,000 体の既定 v3 の manifest で `b6_named_closed_notes` 0・`intent:named` 0)。**実 LLM で店名を書く応答が出るランでだけ再開がずれる**。既定 v3 では意図の層が立つ(活動層+候補の解決)ので、この口は既定で開いている。
- README §10-1 の「AST の検査は外の状態の属性の読み手を見ない」の具体例(`conv.n_opened` と同じ形)。
- 直し: `named_closed` を O26 から外して軸 1 behavior・軸 2 required の行にする。テストは T4。

### L3 設定の指紋が「パスの文字列」を含む(置き場所や OS が変わると再開を拒む・ラン ID が置き場所で変わる)

- `engine/resume.py:79-91` の指紋に `world_dir` の文字列と `objects.world.source`(`str(world.assets.source)`)が入る。同じ世界を絶対パスで渡すか相対パスで渡すかで指紋が変わり、再開を拒む。`source` は `Path` の文字列なので区切りが OS で違う(Windows では `data\\world\\v2`)=Windows で書いた状態を Linux で再開できない。
- 再現: `cli.run(world_dir="data/world/v2", sim_days=2, stop_at_tick=30, state_out=…)` の見出しの写しは `"source": "data\\world\\v2"`・`"world_dir": "data/world/v2"`。絶対パスで渡すと両方とも絶対パス(ユーザー名を含む)になり、ラン ID もそれで決まる(実装役の 5,000 体の記録のラン ID `run-95156277471abc48` は私が絶対パスで回したランと同じ=実装役も絶対パスで回した)。
- 影響: 同じ機械・同じ書き方なら困らない。サーバーと手元のように置き場所が違うと再開できない。状態の見出しの写し(`.json`)に絶対パスとユーザー名が入る(状態のファイルは今は記録に置いていないので漏れてはいない。記録の JSON 5 本に絶対パスが無いことは確かめた)。
- 直し: 世界は中身の同定(資産の版・`registry_hash` など)で指紋に入れ、パスの文字列は入れない。

### L4 開閉の過程の担当従業者 `staff_of_poi` の作り直しを外しても捕まるテストが無い

- `_rebuild_derived`(`engine/run.py:3388`)は classical の `employed` と `runner.opening.staff_of_poi` を作り直す。壊す試験(下の 7)で `_rebuild_derived()` の呼び出しを外すと、落ちるのは classical の 2 件だけだった。`staff_of_poi` は補充の過程の「担当の店員が居るか」(`goods_flow.py:210,234`)で読まれ、mock では役割の行為と規則の補充の内訳(診断)にしか効かないが、実 LLM が補充を選ぶと権限の判定(`mine`)が変わる=挙動に効く。
- 直し: 再開の後の `staff_of_poi` が通しと同じことを直接比べるテスト(T3)。

### L5 O37 `presence._pulled_in_today` の軸 1 が behavior のまま(読み手は診断の計数だけ)

- 読み手は `presence.py:1366-1368` の到着の飛ばしの内訳の計数(O70・diag)だけ。軸 1 behavior なので、診断だけが違う 2 本でも behavior-hash が違う。実装役も README §9-1 (d) と台帳の注記で「軸 1 の方が誤りかもしれない」と書いている。10d で軸 2 を required にしたのは正しい(計数を通しと同じにするため)が、軸 1 は diag が正しい。問い Q2。

### L6 ラン ID が実行ごとに一意でない

- ラン ID は指紋・始めの T・親のラン ID だけから作る(`engine/resume.py` の `run_id_of`)。止めたラン(T=753 で止める)と最後まで回したランが**同じラン ID** になる(作業用ディレクトリの `readcheck.py`: 両方 `run-41b09cb731c1cd15`)。`stop_at_tick` は指紋から外れている。
- 影響: `parent_run.run_id` だけでは「どのランが書いたファイルか」を区別できない(`resume_T` と `state_full_hash` を合わせれば区別できる)。テープの鎖を `run_id` で引く読み手を作るときに混ざる。
- 直し(案): ラン ID に止める時刻か書いた時刻の印を入れるか、鎖は (run_id・resume_T・full-hash) の組で引くと決めて書く。

## 5. 記録の誤り(README)

1. **§2-2 の 4・§3 の W5・§10-5 の表「天気の実日=張り直す」**: 既定の世界では張り直しても値が変わらない(影のある 1 日に絞るため 07-28 のまま・D1 の再現)。また §2-2 の 5「B3 の鍵に日付を足した=2 日目の天候を直した」は、直した後のプロンプトの天候が環境の過程と別の日になる(D1)ことを書いていない。
2. **§3 の M1 の行**: 「再開でも入れない(台帳を通さない初期化の値は上書き)」は初版の形(初期化を一度置いて上書き)の文言。§10-2 の後は初期化を呼ばない。また「131,529,808 → 125,763,428 円=1 体 −1,153 円/日」は初版の値で、反映後の値は 131,529,808 → 125,672,948 円(実装役の JSON と私のランが一致)=1 体あたり約 −1,171 円/日。§0 は「§3 の表は反映後の値に直した」と書いている。
3. **§5 の表の「4,302,784 B」**: 反映後の JSON は 4,302,839 B(先頭の 1 行の分)。861 B/体・336 MB の外挿は変わらない(860.6 B/体)。記憶+関係 21.9 MB(21,867,013 B=4,373 B/体・1.7 GB の外挿)と呼数 142,043・148,347・197,659 は JSON と合う。
4. **§1 の表の `state_ledger.py` の行**: 「行と軸の判定は変えていない(LEDGER_VERSION もそのまま)」は初版の文言で、§10-1 で版を `10d` に上げ行を足した。§1〜§9 は初版と断ってあるが、§1 の表は「入れたもの」の一覧として読まれるので、反映後に合わせるか印を付けたい。
5. **§10-1 の「AST の検査の穴」**: 穴の大きさの具体例として `named_closed`(L2)が抜けている。私の抜き取り(下の 6-4)で、外の状態の行で「挙動に効くのに軸 1 が no/diag」は `named_closed` の 1 件を見つけた。

## 6. 項目ごとの確認

### 6-1 再開で日の頭の初期化が走らないこと(やること 3)

- コード: 再開(`_resuming`)では `R.initialize`(`run.py:2563`)・`R.initialize_energy`(:2596)・世界過程の域外の配置(`runner.py` の `initial_placement=False`)・計画実行層の `initialize`(:2655 で `initialize_caches` に)・`R.set_initial_activity`(:2809)・関係の初期の辺(:2950)を呼ばない。参入資本は `cli.build_ledger_bundle(endow=False)`。財布の入れ直しは `R.initialize` の中(台帳の `endow_households`)なので呼ばれない。台帳に取引が 1 件でもあれば止める(:2553)。
- モック(作業用ディレクトリの `initguard.py`): `R.initialize`・`R.initialize_energy`・`R.set_initial_activity`・`R.place_at_external`(構築と initialize から呼ばれたときだけ)・`PlanExecutor.initialize`・`RelationLayer.seed_initial`・台帳の `endow_stores`・`endow_households` を、再開のランで呼ばれたら例外にした。既定 v3(T=753)・classical+記憶+関係(T=1440)・帰無腕(T=1100)の 3 本とも**再開で 1 回も呼ばれず**、final と最後の checkpoint の behavior・full が通しと一致。通しでは各 1 回(0 日目)だけ。
- お金: 通しの 2 日目の頭の世帯のお金=1 日目の終わり(300 体で 5,846,960 円・5,000 体で 131,529,808 円)。再開の始めのお金=止めたランの終わり、再開の終わり=通しの終わり。
- `rebuild_derived` が作り直すのは classical の `employed` と開閉の `staff_of_poi` だけで、どちらも台帳の行ではなく除外の一覧のキャッシュ(理由つき)。台帳の derivable の行(計画境界の表・イベントの表など)は作り直さずに保存から戻している。必須の行には触らない。

### 6-2 台帳の直し(やること 4)

- O90 `classical._ipf_cache`(behavior・required): 帯ごとに最初に引いた時の体の状態から作る=作り直せない。妥当。
- O91 `conv.n_opened`(behavior・required): 記憶の層が `engine/memory.py:713` で `range(self._next_session, upto)` の上限として読み、この tick に開いた会話を記憶に書く=挙動に効く。妥当。ほかの読み手は `run.py:4245-4251` の診断の差(L1)と `conversation.py:844` の計数の出力。
- O92・O93(diag・required): `_snap` は次の日の締めの `d_cash` の基準、位置は締めの `raw_rows_kept`・`delivery_rows_kept`。どれも挙動ではなくセンサス(診断)に効く=軸 1 diag は妥当。軸 2 required は「再開した日のセンサスが通しと同じ」ために要る。壊す試験(O92 を discardable に戻す)で世界資産の再開の試験 15 件が落ちた=効いている。
- O37: 軸 2 required は妥当、軸 1 は diag が正しい(L5)。
- O85・O88(no・required): テープの共有ブロックの印。full-hash に入るので「通しと再開の両方がテープを書く」前提が要る(README §10-3 に記録あり)。妥当。
- 外の状態の行で「腕が読むのに軸 1 が no/diag」の抜き取り(10 件を grep で読み手まで追った):

| 行・属性 | 読み手 | 判定 |
|---|---|---|
| O26 `poi_resolver.named_closed` | B6 のプロンプトの 1 句 | **挙動に効く**(L2) |
| O62 `undefined.counts`・O82 `undefined._agents` | 裁定の閾値と裁定のプロンプト | 今は `run_day` の裁定器が None(`state_ledger.py:925`)なので効かない。裁定器をつなぐときに軸 1 を見直す |
| O62 `undefined.precedents` | 未定義語の写像 | 親の `adopt` でだけ増える(ラン中に自動では増えない)=今は効かない |
| O13 `store_choice.choice_poi` | 訪問の決め手の計数 | 診断だけ |
| O25 `chooser.last_habit` | 決め手の理由の印 | 診断だけ |
| O28 `energy.meal_bits` | 報告の欠食率 | 診断だけ |
| O19 `rel_layer._invite_salt` | 招待の抽選の鍵 | 毎回 `enable_invite(salt)` で同じ値が入る(定数)=保存しなくてよい |
| O54 `road_works.blocked_cells` | 計数だけ(ほかの読み手なし) | 診断だけ |
| O55 `delivery_inbound.delay_minute` | 納品の時刻 | 日の鍵から作る表(軸 2 derivable で保存される)。台帳の「表は軸 1 no」の約束どおり |
| O64 `renderer.signage_exposures` | tick ごとに取り出して空にする | tick の中だけ |

### 6-3 保存の形(やること 5)

作業用ディレクトリの `readcheck.py`(300 体・2 日):

| 試験 | 結果 |
|---|---|
| 別のランの見出しの写し(`.json`)を置いて読ませる | 止まる(「見出しが写しと違う(ラン ID か full-hash)」)。注: 同じ設定のランどうしはラン ID が同じ(L6)なので、止めたのは full-hash の違い |
| 中身を 1 バイト変える | 止まる(sha256) |
| `finished: true` のランへ再開 | 止まる |
| seed の違うランで読む | 止まる(指紋の `seed`) |
| 見出しの写しが無い | 止まる |
| 正しいファイル | 読める。`parent_run` に親のラン ID・再開の T・ファイル名・full-hash |
| 通しのランが日の締めで書いたファイル(T=1440)から再開 | 読める |
| `--state-out` を渡さない | 何も書かない(今の作業ディレクトリにも何も出ない・manifest の `state_files` は空) |

- sha256 は同じファイルの先頭の行にあるので、壊れたファイルを開かない検査であって、作り直されたファイルを見抜く検査ではない(pickle の「自分が書いたものだけを読む」は運用の約束)。README §4-1 の注意どおり。問い Q4。
- 艦隊の未着の呼: 実装役のテスト `test_fleet_inflight_calls_are_reissued_with_the_same_call_id` が全体の組の中で合格(下の 7 の基準の回)。コードでは、止めたランは吸い切らずに未着を状態へ書き(`run.py:3384`)、再開は同じ `LLMCall` を `now_tick=t_begin-1` で出し直す(:3420-3433)。日の境目で艦隊の未着がある形の試験は無い(T5)。

### 6-4 日ごとの張り直し(やること 6)

`relay.py`(300 体・3 日・顕著行為の率 ×1000)で `WorldProcessRunner.relay_day` と `PlanExecutor.relay_day` の前後を控えた:

| 表 | 1 日目の張り直しの後 | README §10-5 | 合うか |
|---|---|---|---|
| 営業時間(W7) | `opening.day_index` 0 → 1・開閉の行列が変わる・2 日目は 2 | 張り直す | 合う |
| 納品の時刻と遅れ | `delivery_inbound.day_index` 0 → 1・遅れの表が変わる | 張り直す | 合う |
| 道路工事の辺 | 変わる | 張り直す | 合う |
| 大きな催しの会場 | 変わる | 張り直す | 合う |
| 顕著行為・出動の乱数(stateful) | 状態が変わる(日の鍵の流れ) | 張り直す | 合う |
| 宅配の配達済み | 9,163 → 0 | 張り直す | 合う |
| 鉄道の時刻表 | 便 4,089 → 8,178 → 12,267(末尾に足す) | 張り直す | 合う |
| 計画実行層 | `t0`=1440・2880、その日の便の範囲 (4089, 8178)・(8178, 12267)・曜日の行 0(K9 のつなぎ) | 張り直す | 合う |
| 天気の実日 | **07-28 のまま**(層も同じ) | 張り直す | 値は変わらない(D1・記録の誤り 1) |
| 計画境界(W17) | 曜日 0 で置き換え・manifest の `w17_weekday_substituted_days` = [1, 2] | K9 のつなぎ(宣言) | 合う |

- 日の鍵は day_index モードで 1・2(=day_index+日)、`table_weekday` も 1・2。
- 張り直さないもの: 範囲外と自宅の食事の予定(`OutOfAreaMeals`・`HomeMeals` は起動時の `table_weekday(0)` の行=0 日目の曜日の行を毎日)・古典の事前分布の曜日・関係の初期の辺・エネルギーの計数は README §10-5 に宣言がある。manifest には「張り直さなかった表」の欄は無い(K9 の置き換えの日だけ出る)。0 日目が月曜でない暦では「月曜の行を毎日」ではなく「0 日目の曜日の行を毎日」になる(README の文言は既定の暦の場合だけ正しい)。

## 7. 壊して捕まるか(やること 7)

作業木の `src` を作業用ディレクトリへ写して 1 か所ずつ壊し、`tests/engine/test_resume_10d.py`(32 件)を `-o pythonpath=<壊した写しの src>` で回した(pytest は `pyproject.toml` の `pythonpath = ["src"]` で作業木を先に読むので、`PYTHONPATH` だけでは壊した写しが読まれない点に注意)。壊していない写し(基準)は 32 件すべて合格。

| 壊し方 | 落ちたテスト(件数) | 捕まるか |
|---|---|---|
| 保存から外の状態を 1 行(`ledger.money._snap`)落とす | 再開を通る 25 件(戻す側の道筋の集合の検査で止まる) | 捕まる |
| 台帳の O92 を discardable に戻す(保存も戻しもしない) | 世界資産の再開 11 件+日の境目のセンサス+記憶の日中+行の移し替え+別プロセス=15 件 | 捕まる |
| `_rebuild_derived()` を呼ばない | `test_world_arms_resume_equals_straight[classical_mem_rel]`・`[classical_day2]` の 2 件だけ | classical は捕まる。開閉の `staff_of_poi` は捕まらない(L4・T3) |
| 2 日目の頭で財布を入れ直す(`_start_day` で `endow_households`) | `test_no_money_is_added_at_the_head_of_day_two_or_on_resume`・`test_two_day_world_run_closes_money_goods_and_bodies_each_day`・世界資産の腕 6 件・日の境目のセンサス・記憶の日中・日ごとの表の張り直し(計 11 件) | 捕まる(一致の試験の多くは通しと再開の両方で同じだけ入れるので一致のまま=捕まえるのはお金とセンサスの試験) |
| `_ipf_cache` の鍵から日を落とす | `test_ipf_cache_key_has_the_day` の 1 件 | 捕まる(鍵の形だけを見る。乗数が 1 でない classical の複数日の値を見る試験は無い) |
| B3 のキャッシュの鍵から日を落とす | 世界資産の再開の試験 14 件 | 捕まる(通しはキャッシュの 0 日目の行・再開は 2 日目の行で prompt_hash が違う) |
| 保存の sha256 の検査を外す | `test_read_state_opens_only_files_it_wrote` の 1 件 | 捕まる |

## 8. テストの欠け

- **T1**: 一致の試験と `first_diff.py` は診断の行のうち `calls` の列しか比べない。L1 を見落とした。診断の行の全列(または全列から「累計の差分」の列を宣言して除いたもの)を比べたい。
- **T2**: D1 を捕まえる試験が無い。2 日のランで、2 日目のある時刻の B3 の天候の語と、環境の過程のその時刻の天候・暑さの段が同じ日の行から来ていることを確かめる試験。
- **T3**: 再開の後の `runner.opening.staff_of_poi`(と補充の過程の同じ配列)が通しと同じことを直接比べる試験(L4)。
- **T4**: 名指しの即時閉店の控え(L2)を通る再開の試験。mock では店名が出ないので、`TargetResolver.named_closed` に控えを入れてから止めて戻し、戻した後に控えが同じこと・B6 の prompt_hash が通しと同じことを見る小さい試験で足りる。
- **T5**: 日の境目(T=1440)で艦隊の未着の呼がある形の再開の試験。今の艦隊の試験は合成 24 tick の日中だけ。A10 の指示は「日の境目でも夜の街の分があるので、この仕組みは境目の再開にも要る」。

## 9. 問い

- **Q1**(D1): 2 日目からの天候の源をどちらにそろえるか。(a) 描画を環境の過程の再生の実日に合わせる/(b) 環境の過程を暦の日付に合わせる/(c) 10d では 0 日目に固定して宣言し 10g の前に決める。あわせて「影の面が 1 日しか無いので再生の実日が毎日同じ」を宣言の一覧に入れるか。
- **Q2**(L5): O37 の軸 1 を diag に直すか(behavior-hash の値が全構成で変わる)。
- **Q3**(L3・L6): 指紋とラン ID からパスの文字列を外して中身の同定にするか。ラン ID を実行ごとに一意にするか、鎖は (run_id・resume_T・full-hash) で引くと決めるか。
- **Q4**: 状態のファイルの sha256 は壊れの検査だけで、作り直しは見抜かない。pickle を読むのは「自分が書いたものだけ」の運用の約束のままでよいか(10f の npz+json への見直しで解消する前提でよいか)。

## 10. 使ったスクリプト(作業用ディレクトリ・親が消してよい)

`bc.py`(byte-check の 1 本)・`cmp.py`(byte-check の比べ)・`rs.py`(再開の 1 本)・`cmp_rs.py`(再開の比べ)・`initguard.py`(初期化が呼ばれないことのモック)・`readcheck.py`(読み口の検査)・`relay.py`(日ごとの張り直しの控え)・`edge.py`(境界の 8 件)・`mut.py`(壊した写しを作る)。

## §再確認(実装役の直しの後・10d README §11)

> 直しの前に検収した作業木の写しと今の作業木を `diff` で比べ、変わった 4 ファイル(`perception/renderer.py`・`engine/run.py`・`engine/resume.py`・`engine/state_ledger.py`)とテスト・README を読んだ。直していない(この節だけを足した)。検算は前と同じ作業用ディレクトリ。

### 結果

| # | 指摘 | 判定 | 確かめたこと |
|---|---|---|---|
| D1 | 2 日目の B3 の天候と体の天候が別の日 | **直った** | 描画の `_b3` は `weather_date_fn`(`engine/run.py` が `runner.environment.replay_date` を差し込む・合成世界は口が立たず旧経路)で W13 を引く。300 体・2 日・テープつきの自分の確認(`d1.py`)で、B3 の天候と暑さの語が再生の実日(07-28)の同じ時の W13 の行と、1 日目 3,318 呼・2 日目 3,487 呼の全部で一致(毎時 58・59 分は 5 分帯の丸めで時がずれるので除いた)。環境の過程も同じ実日(`replay_date` 07-28)。`start_sim_datetime` を 2026-08-10 にしたランでも B3 の天候は実日 07-28 の行(README §11 の「今までは暦の日付の行・直した後は実日の行」の記述どおり。日付の語は暦のまま=K7 のつなぎの宣言どおり) |
| D1 | 1 日のランの既定のバイト | **不変** | 自分の byte-check(既定 v3・5,000 体・1 日)で final `993276d5e5bb5cbe`・69,978 呼・checkpoint 4 点の combined・calls の全列・blocks が HEAD の写しと同じ。最後の behavior-hash `b3ccfa6797f2c418`・full-hash `fa168793db2b6433` は README §11-1 の新しい値と同じ |
| L1 | 再開の最初の tick の診断の行 | **直った** | 5,000 体・2 日・T=753 で止めて別のプロセスで再開(自分の `rs.py`・`cmp_rs.py`)。診断の行の**全列**が全 tick で通しと一致(前は `conversations_opened` が 1 → 97)。checkpoint 2,880 点・テープ 142,043 行(順序と call_id)・日の締め・最後のお金も一致。通しの final `47e0a85b02797e23`・142,043 呼は直しの前と同じ |
| L2 | `named_closed` を保存しない | **直った** | O26 から外して O94(behavior・required)。戻しは `restore_items` が辞書の中身を入れ替える=`_named_closed_lookup` の閉包は `resolver.named_closed` をその都度読むので B6 に効く。台帳の網羅と AST の検査(`test_state_ledger_10b.py` の該当 35 件)は合格。O94 を discardable に戻すと `test_named_closed_memo_survives_a_resume` ほか 3 件が落ちる |
| L3 | 指紋にパスの文字列 | **直った** | `PATH_ARGS`(`world_dir`・`holiday_csv`)は中身の同定(`manifest-sha256:`・`sha256:`)・`_describe_objects` から `source` を外した。`run_day` のパスの引数はほかに `tape_path`・`census_out`・`occupancy_path`・`fleet_debug_dir`・`state_out`・`resume_from` で、どれも指紋から除く一覧に入っている。100 体の状態を相対パスで書き(`l3.py`)、見出しの写しを読んだ: `/` か `\` を含む値は形式の版と台帳の版の 2 つだけ・ホームと作業ディレクトリとユーザー名は無い。相対で書いた状態を絶対パスの `world_dir` で再開できた |
| L4 | `staff_of_poi` の作り直しを捕まえるテスト | **直った** | `runner.opening.rebuild_derived()` を外した写しで `test_resume_rebuilds_the_staff_table_shared_with_restocking` が落ちる |
| L5 | O37 の軸 1 | **直った** | O37 は diag・required |
| L6 | ラン ID が一意でない | **直った** | 同じ設定の 2 回でラン ID が違う(`run-862e…`・`run-cefc…`)。状態の口を使わないランはラン ID が空で、同じ設定の 2 回の manifest は全部の欄で同じ(壁時計の欄を除く)=決定論は壊れていない |
| T5 | 日の境目の艦隊の未着の呼 | **直った** | 未着の呼の保存を外した写し(保存に `[]` を書く)で `test_fleet_inflight_calls_at_the_day_boundary` と `test_fleet_inflight_calls_are_reissued_with_the_same_call_id` が落ちる |
| L1 の試験 | `prev_sessions` の基準を旧に戻す | **捕まる** | 再開の一致の試験 14 件が落ちる(診断の行の全列の比べが効いている) |
| 記録 1〜5 | README §2-2・§3 M1・§5・§1 の表・§10-1 | **直った** | §2-2 の 4 と 5 に注・§3 の M1 と W5・§5 の 4,302,839 B・§1 の表の台帳の行(192 行・O90〜O94)・§10-1 に `named_closed` |

### 新しい指摘

- **テストの欠け N1(`_b3` の鍵の日)**: `_b3` の鍵から日を外した写し(`key = (0, 5 分帯)`)で、`test_resume_10d.py` の 37 件が**全部合格した**。既定の世界では再生の実日が毎日 07-28(影のある 1 日に絞る)なので日を外しても同じ値になり、合成世界は天候が日付に依らない(時ごとの表)ので、この壊し方はどの試験でも見えない。今は結果を動かさないが、影の面の日が増えるか `prefer_shadow_days` を外すと、2 日目に 0 日目の天候を使い回す欠陥(10d の初版の欠陥と同じ形)が試験をすり抜ける。再生の実日が日ごとに変わるラン(例: `prefer_shadow_days=False` の世界過程)で、2 日目の B3 の天候が 2 日目の実日の行であることを見る試験がほしい。
- **テストの欠け N2(`test_named_closed_memo_survives_a_resume` の届く範囲)**: 控えを入れる体 3 の `last_result_tick` は 599 ではないので、B6 の 1 句は通しでも再開でも出ない。この試験が確かめているのは「控えが保存され戻ること」(behavior-hash で捕まる)までで、docstring の「B6 の prompt_hash も通しと同じ」は 1 句が出る形では確かめていない。戻しの経路(閉包がその都度読む)はコードで確かめたので結果を動かす欠陥ではない。
- **記録の誤り N3**: README §2-2 の末尾の「張り直さないもの(0 日目の表を毎日繰り返す=宣言): 営業時間の表(W7 の曜日の行)・世界過程の日ごとの乱数の表…」は初版の文言のまま。§10-5 の後は営業時間と日ごとの乱数の表は張り直す(§2-2 の 4・5 には注を足したが、この段落には印が無い)。

### 件数

直った: D1・L1〜L6・T5・記録の誤り 5 件(計 13)。直っていない: 0。新しい指摘: 3(テストの欠け 2・記録の誤り 1)。結果を動かす欠陥の新しいものは無い。
