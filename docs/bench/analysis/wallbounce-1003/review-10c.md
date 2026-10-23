# 10c の検収(別のサブ・Opus 5.5)

対象: 10c(状態を持つ乱数 2 本をカウンタ型に・切替口 `--rng-scheme {stateful,counter}`・既定 stateful)。実装役の追加(`run_meta.json` の `rng_scheme`・再生の突き合わせ)を含む最終の作業木。基準は HEAD `adc6da8` の `git archive` の写し。検算のスクリプトとテープは自分専用の短いパスの一時ディレクトリに置いた(リポには置いていない)。

## 0. 要点

- 結果を動かす欠陥: 0 件
- 潜在の欠陥: 3 件(P1〜P3。どれも 10c より前からあるもの。10c の 2 本は 1 語目を 0 にしたので当たらない)
- 記録の誤り: 4 件(R1〜R4。どれも小さい)
- テストの欠け: 3 件(T1〜T3)
- 問い: 3 件(Q1〜Q3)
- byte-check: 既定 v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439 とも、HEAD の写しと作業木で final(64 桁)・呼数・calls の全列(prompt_hash を含む)・checkpoint 4 点の全欄・顕著行為と出動の件数が一致。manifest の差は `rng_scheme` の 1 欄だけ。

## 1. byte-check(やること 1)

手順: HEAD の写し(`git archive adc6da8 src docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28`)に `PYTHONPATH` を向けたランと、作業木のランを、`w6_regen_measure` の腕 `v3_default` と `golden_null_arm` で回した(`cli.run`・5,000 体・seed 1・1 日・テープつき)。比べたもの: `final_hash` の全桁・`llm_calls`・calls.parquet の全列の sha・`prompt_hash` 列・`checkpoints` の全欄(`dataclasses.asdict` で 4 点)・`run_manifest_fields()` の全キー。

| 構成 | final | 呼数 | calls 全列・prompt_hash | checkpoint 4 点 | manifest の差 |
|---|---|---|---|---|---|
| 既定 v3 | 一致 `993276d5e5bb5cbe` | 一致 69,978 | 一致 | 一致 | `rng_scheme` だけ(HEAD は欄なし・作業木は `stateful`) |
| 帰無 | 一致 `72cb9cd52982da74` | 一致 100,439 | 一致 | 一致 | 同上 |

注意: 1 回目は manifest の `calendar` も違って見えた。原因は検算の作り(HEAD の写しに `data/calendar/syukujitsu.csv` が無く、祝日 CSV はリポの根から解決するので md5 が `None` になった)。写しに CSV を置いて既定 v3 を回し直すと、差は `rng_scheme` だけになった。コードの差ではない。

実装役の `byte_check.json`(19 構成)と `byte_check_after_replay_check.json`(2 構成)とも数字は合っている(`all_ok: true`・19 行)。

## 2. counter の性質(やること 2)

- (i) 実世界の既定 v3 を counter で 2 回回した: final `52a8b390ecd584a1`・呼数 69,796・calls の全列・checkpoint 4 点・顕著行為 10・出動 5・気づいた延べ 352 がすべて一致。帰無の counter は final `f924638f54c57f7d`・呼数 100,947・気づいた延べ 1,151(README と一致)。
- (ii) 自分のモック: 同じ T=100 でセル 3 と 7 に出動を「3,7,3,7,3」と「7,3,3,7,3」の順で呼ぶと、セルごとの到着の列はどちらも セル 3 = [104,107,106]・セル 7 = [104,105] で同じ。同じ T・同じセルの 3 件は違う遅れ。k は「同じ (T, セル) の何番目か」なので入力の順(別のセルとの混ざり方)に依らない。顕著行為の側は選んだ体を id の昇順に並べてから呼ぶ(`salient.py` の `np.sort`)。出動の呼び手は `SalientProcess._collapse_events` の 1 か所だけ(grep で `.request(` は 1 件)。
- (iii) 通し番号は使っていない。`_k_tick`・`_k_next` は `_counter_stream` の頭で `tick != _k_tick` なら空に戻すので、T が変わると捨てられるキャッシュ。tick の境目で作り直した実体(再開に相当)でも同じ値になることを、既存のテスト `test_counter_dispatch_delay_depends_only_on_T_cell_k`・`test_counter_k_restarts_for_each_tick_and_cell` と自分の確認で見た。台帳の除外に CACHE として入れたのは正しい。
- (iv) 率 ×1000 の過程だけの段を seed 6〜10 で回し直した: 倒れる stateful [303,324,308,309,310]・counter [297,298,279,301,299]。平均の差 16.0、線 17.9 で合格(余裕は小さい)。遅れの平均も合格(差 0.1・線 0.6)。tick ごとの件数を 5 seed × 1,440 tick でまとめると、stateful 平均 0.2158・分散 0.2120、counter 平均 0.2047・分散 0.2042、期待 0.2083(ポアソンなので平均と分散が同じ)。0 件の割合も期待 0.8119 に対し 0.8043 と 0.8149。どちらの方式もポアソンに合う。線の妥当性は T3 に書いた。
- (v) 2 日ランの鍵の重なりは無い(テスト `test_two_day_counter_keys_carry_T` を読み、`--day` の違いも自分で確かめた: `day_index=1` の T=100 と `day_index=0` の T=1,540 は同じ遅れ、`day_index=0` と `3` の同じ T は違う遅れ)。

## 3. 鍵の形(やること 3)

- コードは `run_tick_key = day_key0 × (86,400 // tick_seconds) + T` で、定数 1,440 ではなく 1 日の tick 数で掛けている。`tick_seconds=30` で `run_tick_key(1, 0, 30) == run_tick_key(0, 2880, 30)` を確認。正しい。記録の側に「× 1440」と書いた箇所がある(R2)。
- `real` モードは `SimCalendar.day_key(0) = 0` なので鍵は T そのもの(`calendar.py` の `day_key`)。開始日の違いは鍵に入らない(stateful も同じ・README 問い 1 に既出)。
- Philox の 1 語目: numpy で実測。`philox(1,"x",0,5)` は作った時点でカウンタ [0,5,0,0]、4 語引くと [1,5,0,0]、5 語目で [2,5,0,0]。`stream(1,"x",0,5)` の 5〜8 語目は `stream(1,"x",1,5)` の 1〜4 語目と同じ(一致)。一方 `(0,5)` から 4,000 語引いても `(0,6)` の頭とは重ならない。1 語目が進むので、そこを 0 に固定し鍵を 2 語目以降に置く実装の理由は正しい。counter の 2 本は実世界のランで 1 回 1 ブロック以内(出動 5 本・顕著行為 1,440 本とも)。

## 4. 指摘

### 結果を動かす欠陥

なし。

### 潜在の欠陥(10c より前からあるもの・直していない)

**P1. `w16.sample.stratum`(`agents/population.py:334`)で隣の層の抽出が相関する。既定のランに効く。**
- 1 語目が層の鍵 `uniq[s]`(= 種別 × 年齢階級 × 性の通し値)で、`permutation(層の人数)` は数百〜数千語を引く。実世界の既定ランでは 372 層すべてが 2 ブロック以上(最大 2,602 ブロック)を引いた。〔注(10f)〕372 は層の数ではなく流れの数。母集団の抽出が `cli.py` と `engine/run.py` で 2 回走るので、186 層の流れが 2 本ずつ作られる(同じ鍵の作り直し 186・実際の重なりは 185)。層は 186([10f の材料](../wallbounce-1006/10f-prep.md) §4-2 表 8 の数え方)。重なりの評価(隣の鍵の層どうし)には影響しない。層の鍵は男女・年齢で連続するので、隣の層の並べ替えは同じ乱数を 4 語ずらして使う。
- 実測(300 seed): 100 人の層 2 つから 30 人ずつ取ると、選んだ「名簿の中の位置」の重なりが隣の鍵では平均 17.9 人、離れた鍵(500)では 9.0 人(独立なら 9.0)。1,000 人から 300 人では 195.8 人対 90.1 人(独立なら 90.0)。
- 統計の読み: 決定論は保たれる。各層の中では一様に選ばれる(1 層だけ見れば偏りは無い)ので、期待値は歪まない。歪むのは層をまたぐ同時の分布。名簿の位置(行番号)が住所の区域などと相関していれば、たとえば同じ年齢の男女が同じ区域から選ばれやすくなり、標本の空間的な構成のばらつきが独立な抽出より大きく(あるいは偏った組で)出る。5,000 体の標本は既定のランすべての出発点なので、影響する範囲は一番広い。名簿の並びと住所の相関は測っていない(空欄)。
- 再現: `stream(s,"w16.sample.stratum",10).permutation(100)[:30]` と `…,11)…` の共通要素数を seed 0〜299 で平均。

**P2. `perception.p_notice`(`p_notice.py:478`)で同じ tick の事象 k と k+1 の引きが重なる。**
- 1 語目が tick の中の事象の番号 `ev_id`(`salient.py` の `enumerate(raw)`)で、`random((2, 候補数))` を引く。率 ×1000 の合成世界では 1,206 回すべてが 2 ブロック以上(最大 15)。実世界の counter ランでは 10 回すべてが 2 ブロック以上(最大 86)。
- 実測: 候補 10 人で、事象 1 の 20 語は事象 0 の 5 語目以降を 4 語ずらしたものと同じ(20 語中 16 語が共通)。
- 統計の読み: 1 人・1 事象ごとの気づく確率は正しい(一様乱数の周辺分布は変わらない)。同じ tick に事象が 2 件以上あると、事象 k+1 の候補 i の乱数は事象 k の候補 i+4 の乱数と同じになる。同じセルの事象(候補の並びが同じ)では「事象 k で i+4 番目の人が気づいたなら、事象 k+1 で i 番目の人も気づきやすい」という人をまたぐ正の相関が出て、tick の気づいた延べ人数の分散が大きくなる(平均は変わらない)。既定の率では、実世界 seed 1 の counter ランで 2 件が同じ tick に出たことは無く(事象番号はすべて 0)、stateful の既定ランは事象 0 件なので、今の golden には効いていない。率を上げた感度試験(×1000 など)では毎 tick のように起きる。
- 再現: `stream(1,"perception.p_notice",0,500).random((2,10)).ravel()[4:]` と `…,1,500).random((2,10)).ravel()[:-4]` が一致。

**P3. `world.delivery_inbound`(`goods_flow.py:336`)は `--day` が 1 違うランで配送の予定がそのまま 8 店ずれる。**
- 1 語目が日の鍵で、POI 数 × 3 種の引き(実世界で 1,487 ブロック)。実測: 500 POI で、日の鍵 1 の予定分 `integers` は日の鍵 0 の列を 8 個ずらしたものと完全に一致(一致率 1.0。31 bit 未満の整数は 1 語から 2 個取るので 4 語 = 8 個)。
- 統計の読み: 1 日のランの中では問題ない。`--day d` と `--day d+1` を別々に回して「日ごとのばらつき」を作ると、配送の時刻の集まり(分布)はほぼ同じになり、日の間のばらつきを過小に見積もる。今の複数日の口(`sim_days`)は日の頭で作り直さない(1 日目の予定を使い続ける)ので、この重なりは出ない代わりに毎日同じ予定になる(これは 10d・10g の話)。
- 同じ形の重なりは stateful の `world.salient`・`world.public_service_dispatch` にもある(日の鍵 0 の 5 語目以降 = 日の鍵 1 の頭・一致を確認)。counter に切り替えればこの 2 本は解消する。

そのほかの呼び手(実測): `engine.chooser`・`llm.mock`(v3 の 6 個を含む)・`policy.classical`(コードを読んで 2 語)・`conversation.invite`(1 語)・`perception.attention.p_see`(呼び手はどれも n=1)は 1 ブロック以内。`body.weight`・`body.eer` は R3 のとおりごくまれに超えるが、効きは無視できる(5,000 体で 1 体ずつ・正規乱数の棄却の分の 1 語だけ)。`world.road_works` は実世界で 2 ブロック(日の鍵が 1 違うランの間で P3 と同じ形)。`wallet.initial` はカウンタ無し(1 語目が定数 0)なので隣が無い。

### 記録の誤り(README)

**R1. テストの件数が古い。** §3 と §5 は「14 件」。再生の突き合わせの 2 件が足されて今は 16 件(`grep -c "^def test_"` で 16・全件通過)。§0-5「止めた問いは 3 件」も §6 に親の答えが入った今は「答えが出た」と書くのが合う。

**R2. 鍵の式を「× 1440」と書いた箇所がある。** §2 の 3 つめの点と §6 の親の答え 1・問い 1 の文面。コードは「× 1 日の tick 数」(`86,400 // tick_seconds`)で、1,440 は `tick_seconds=60` のときだけ。§2 の初めの式の書き方(「× 1 日の tick 数」)にそろえるのがよい。

**R3. §6-1 の表の `body.weight`・`body.eer` の「1〜3 語・超えない」。** seed 1・5,000 体で、`body.weight` は体 1017、`body.eer` は体 4316 が 5 語以上を引き、次の体の流れの頭と重なる(`philox(1,"body.weight",1017).random_raw(8)[4:]` = `philox(1,"body.weight",1018).random_raw(4)`)。200 回の試しでは見えない頻度。「まれに超える(5,000 体で 1 体)・効きは無視できる」と書くのが正しい。

**R4. §6-1 の表の `world.road_works`「139 から 3 個で 3」。** 実世界の既定ランでは 2 ブロック(5 語以上)を引いた。「工事の数が多いと超えうる」は合っているが、実世界では既に超えている。

README のほかの数値(§4 の表の 19 構成の件数・呼数の差・blocks の差・平均の遅れ・気づいた延べ 290〜1,151・呼数の差 −185〜+1,444・§3 の表)は `byte_check.json`・`count_dist_x1000.json` と全部合っていた。

### テストの欠け

壊して捕まるかの全体は §5 の表。

**T1. 1 日の tick 数を定数 1,440 にしても捕まらない(§5 の M7)。** `run_tick_key` を `day_key0 × 1440 + T` に書き換えても全件通る。単体テストの `run_tick_key(0, 10, 30) == 10` は `day_key0 = 0` なので掛け算を通らない。`run_tick_key(1, 0, 30) == 2880`(= `run_tick_key(0, 2880, 30)`)の 1 行で守れる。

**T2. 鍵から `day_key(0)` を落としても捕まらない(§5 の M8)。** テストはどれも `day_index=0` で回すので、`run_tick_key(0, T)` と区別がつかない。問い 1 の親の答え(`--day` が違うランは違う乱数)を守るテストが要る(`day_index=0` と `3` の同じ T で引きが違う、`day_index=1` の T と `day_index=0` の T+1440 が同じ)。

**T3. 合否の線(平均の差 ≤ 2 × seed 間 SD・分散の比 ≤ 10)は、5 seed では弱くて誤報がある。** 同じポアソン(平均 300)を 2 組 5 seed ずつ 200,000 回試すと、分散の比 > 10 で落ちる率が 4.7%(F(4,4) の両側の裾)、平均の線で落ちる率が 0.7%、合わせて 5.3%。逆に、率を 10% 下げた counter を見逃す率は 71%(検出 29%)、15% 下げても 30% を見逃す。自分の seed 6〜10 でも平均の差 16.0 対 線 17.9 と際どかった。今のテストは seed 固定なので決定的に通るが、合成世界の作り(`make_world`)が変わると 20 回に 1 回は理由なく落ちる。より強くて誤報の少ない形: 5 seed × 1,440 tick の tick ごとの件数をまとめ、期待値(既知の答え: 率 × 体数 / 1,440)とのずれを z で見る(合計は 5 seed で約 1,500 件なので標準誤差は約 39 件)、と平均と分散がそろうこと(ポアソン)。「同じ桁」というアジェンダの言葉には今の線でも足りるので、問いとして親に返す。

### 問い

**Q1. 名前 `rng_scheme` が既存の設計の欄と重なる。** `manifest/schema.py:189` の `Rng.scheme: Literal["numpy-philox4x64"]`、設計 `v2-run-manifest-concurrency.md:19`、答申 `v2-implementation-stack-research.md:177`(「manifest 欄 `rng_scheme: "numpy-philox4x64"`」)では、`rng_scheme` は乱数の算法の名前の意味。10c の `rng_scheme` は「状態を持つか」の切替で意味が違う。今の run_day の manifest は `rng.scheme` を出していないので衝突はしないが、後で schema の manifest を出すときに同じ綴りで違う意味になる。`rng_stream_mode` などに分けるか、今の名前のまま注記するか。

**Q2. 再生のときの既定の扱いが `response_delay` と違う。** `response_delay` は未指定(`None`)ならテープの値に合わせる。`rng_scheme` は既定が `stateful` で、counter のテープを既定のまま再生すると止まる(`--rng-scheme counter` が要る)。止めるのは安全側で、README §7 にも書いてあるので欠陥ではないが、10e で既定を counter にしたとき、既存の実 LLM テープ 17 本(meta に値なし=stateful とみなす)が既定のまま再生できず、毎回 `--rng-scheme stateful` が要る。`response_delay` と同じく「未指定ならテープに合わせる」にするかを 10e で決めるのがよい。

**Q3. P1(`w16.sample.stratum`)をいつ直すか。** 直すと 5,000 体の標本が変わり、すべての golden が動く。A6 の版上げの 1 回目に束ねるか、10f の検査(1 語目に値を置く流れから 4 語より多く引いたら落とす)を先に入れて一覧を固定するか。P2・P3 も同じ検査で捕まる。

## 5. 壊して捕まるか(やること 5)

作業木の `src` と `tests` を一時ディレクトリに写し、1 か所ずつ書き換えて `tests/engine/processes/test_rng_scheme_10c.py`・`test_calendar_sites.py`・`test_10a_review_fixes.py`・`processes/test_civic.py`・`test_state_ledger_10b.py` を回した(書き換える前は全件通過)。

| 壊し方 | 捕まえたテスト |
|---|---|
| M1 k を常に 0 | `test_counter_dispatches_in_one_cell_and_tick_draw_different_delays` |
| M2a 顕著行為の鍵から T を落とす | `test_counter_run_twice_is_identical`・`test_counts_have_the_same_order_under_a_x1000_rate`・`test_two_day_counter_keys_carry_T`・`test_counter_calls_the_dispatch_in_ascending_agent_id`・`test_the_tape_carries_the_scheme_and_a_mismatch_stops` |
| M2b 出動の鍵から T を落とす | `test_two_day_counter_keys_carry_T` だけ |
| M3 用途名を stateful と同じにする | `test_two_day_counter_keys_carry_T` だけ(stateful の 2 日ランが counter の用途名を作らない、という末尾の確認に偶然かかる。意図して守っているテストではない) |
| M4 体の並べ替えを外す | `test_counter_calls_the_dispatch_in_ascending_agent_id` |
| M5 既定を counter にする | 13 件(`test_scheme_values_and_default_is_stateful`・`test_cli_switches_and_defaults`・10a の meta のテスト 3 件など) |
| M6 k の数えを T が変わっても空に戻さない | `test_counter_dispatch_delay_depends_only_on_T_cell_k` |
| M7 1 日の tick 数を定数 1,440 にする | **捕まらない**(T1) |
| M8 鍵から `day_key(0)` を落とす(0 を渡す) | **捕まらない**(T2) |
| M9 顕著行為の 1 語目を 0 にせず鍵を置く | `test_two_day_counter_keys_carry_T`(`c[0] == 0` の確認) |
| M10 再生の突き合わせを止める | `test_the_tape_carries_the_scheme_and_a_mismatch_stops`・`test_a_tape_without_the_value_is_replayed_as_stateful` |
| M11 meta に `rng_scheme` を書かない | 上の 2 件+10a の `test_tape_meta_does_not_touch_the_parquet`・`test_the_tape_carries_the_response_delay_and_mismatches_stop` |

M2b・M3・M9 は 2 日ランの 1 本のテストだけが頼り。そのテストが重い作り(1 日 1,440 tick × 2)に変わったり分けられたりすると守りが消えるので、M3(用途名が違う)と M9(1 語目が 0)は単体の 1 行でも守っておくとよい(必須ではない)。

## 6. 再生の突き合わせ(やること 7)

自分のランで確かめた(60 体・16 セル・200 tick・率を上げた合成世界):
- counter で録ると `run_meta.json` は `{"response_delay": 1, "rng_scheme": "counter"}`。既定(stateful)で再生すると `ValueError`「乱数の方式がテープと違う: テープは rng_scheme=counter・今の設定は stateful(--rng-scheme を録画と同じ値にする)」で止まる。`replay` を文字列のパスで渡しても止まる。`rng_scheme="counter"` で再生すると final が一致し、取りこぼし 0。
- stateful で録ったテープの meta から `rng_scheme` を消すと、既定で再生して stateful で回り final が一致(manifest は `stateful`)。meta のファイルごと消しても既定で回って一致。
- 既定の結果: byte-check(§1)の作業木は meta を書く版で、final・呼数・calls は HEAD と一致。
