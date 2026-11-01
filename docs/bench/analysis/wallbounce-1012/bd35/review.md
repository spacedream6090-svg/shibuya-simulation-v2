# 第 3 期 3-5 検収の記録(本人の体の層・TM5 の予約の口)

- 検収役 Opus 5.5(実装は見ていない)。対象=作業木の枝 `3-5/body-system1`(土台 `d35a9b6`・未 commit)。本体の HEAD は `82eeab0`(読むだけ)。
- 正: 実装役への発注文(要件)・決定 10-12 §1-5 の ③ と D の論点 3・§4-2 TM5・計画 10-12 の 3-5 の行・記録 [README.md](README.md)。
- 検収の道具と生の出力は作業木の `_bc_review/`(git の外・終わったら消した)。本書には結果と方法だけを書く。

## 判定

**条件つき受入**。既定(sweep)の結果は 1 バイトも変わらず(自分の 4 構成・2 日・再開)、TM5 の予約の腕 reserve は sweep と 27 欄とも同じで、負の対照も再現した。予約の式の下界性は総当たりでも崩れなかった。直してほしい欠陥は中 1(状態台帳の行 BD の大きさの宣言と、腕 sweep でも予約の配列を確保していること)と低 8(記録と宣言の細部)。

## 欠陥(重さ順)

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `src/shibuya/engine/body/model.py:75`・`schedule.py:173`(`BodySchedule.reset`)・`src/shibuya/engine/state_ledger.py:932`(行 BD の `nbytes`) | 腕 sweep(既定)でも `reset()` が体数 × 5 本の int64(`intero_seq`・`intero_at`・`felt_seq`・`felt_at`・`felt_col`)を確保する。39 万体で 15.6 MB(体あたり 40 B・実測)。行 BD の `nbytes` は「腕 sweep: 計器だけ」と書いており食い違う。既定の道に使わない配列が載り、バイト予算の宣言(CLAUDE.md §4)とも合わない | (a) 腕 reserve のときだけ配列を作る(sweep は長さ 0 の配列のまま・`reserved_steps()` などの読み口は −1 の写しを返す)か、(b) `nbytes` を「腕 sweep でも予約の配列 40 B/体」に直して予算に載せる。結果は変わらないので、直した後は 4 構成の byte-check と範囲の試験で足りる |
| L1 | 低 | `src/shibuya/engine/resolve.py:38`(見出しの文) | 3-5 で書き直した文に「30 tick ごとの」がある(T0=新しい文に「tick」を入れない)。名の凍結の試験は識別子だけを見るので通る | 「30 刻みごとの」に |
| L2 | 低 | `src/shibuya/engine/processes/salient.py:325` | 倒れるの引き方を持ち主 `BodyModel.collapse_draw` でなく `engine.body.rules.collapse_draw` で直に呼ぶ。発注文の口は `BodyModel.collapse_draw`。同じ関数なので値は同じ。`BODY_RULES` の `port` 欄は `BodyModel.collapse_draw` と書いている | 口を通すなら salient に体の層の参照を挿す(環境の過程と同じ形)。通さないなら `port` 欄と記録 §2 を「rules.collapse_draw(持ち主は状態を持たない)」に |
| L3 | 低 | 記録 `README.md` §7-3(182 行)・§14 の 1(275 行) | 「`_bc/head_src/data` は無い場所を指すつなぎのまま・`cmd /c rmdir` で外してほしい」とあるが、今の `_bc` の下につなぎは 0 個(再解析点の検索)。`cmd /c rmdir` は道具に止められる手順でもある | 注を今の状態に直す(つなぎは無い・`_bc` は .NET の `[IO.Directory]::Delete` で消す) |
| L4 | 低 | 記録 §7-3・§14 の 1・§15 | 「10e の道具の HEAD の写しの手順に rules-table と OSM が要る」は本体の 2-3c の検収 L4(`82eeab0` の `HEAD_TREE_FILES` と docstring)で既に直っている。§15 の再現の手順は `git archive d35a9b6 …` と data の写し(つなぎでない)のまま | 取り込みの rebase の後、§15 を本体の 10e の docstring の手順(`HEAD_TREE_FILES`・data はつなぎ)に合わせ、§14 の 1 は「本体で解決済み」と書く |
| L5 | 低 | `docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py` の `SWITCH_ENV`(本段の範囲の外) | 新しい切替口の環境変数 `SHIBUYA_BODY_SCHEDULE` が side の JSON の `env` に残らない(2-4 検収 L2 の約束) | 親が取り込みのときに `SWITCH_ENV` へ足す |
| L6 | 低 | 性能(P4)・`docs/design/v2-budget-declaration.md` | 既定の sweep は HEAD 相当より体の層の 1 刻みで +19%(5,000 体)・+4%(39 万体=約 +0.43 ms/刻み)。中身は段の境目の計器(`_note`=新旧の比べと鎖のハッシュ)と持ち主の呼び出し。記録には数があるが、性能の回帰の試験は無く、予算の宣言にも載っていない(近接 2-2・申込書 3-3 も記録だけ=同じ扱い) | 親の判断: P4 の行に「体の層の段の境目の計器=既定の道で約 +0.4 ms/刻み@39 万体」を足すか、計器を腕 reserve と試験だけにするか |
| L7 | 低 | `src/shibuya/engine/body/schedule.py:150`(`BodySchedule`) | 予約の列は普通の dataclass で、実行時の守り(`__setattr__`)が無い。外から書けないことは AST の試験(負の対照つき)だけで守る。持ち主 `BodyModel` の欄は `__slots__`・`__setattr__`・`__delattr__` で守っている | 今のままでよい(内側の物)。気になるなら `BodySchedule` にも 1-3 と同じ守り |
| L8 | 低 | `src/shibuya/engine/state_hashes.py:53` | `VALUE_CLASSES` に汎用の `engine.scheduler.Scheduler` を足した。今 src で `Scheduler` を作るのは体の予約の列だけなので既存の行には効かない(系ごとの指紋の項の数は HEAD と同じ)。ただ将来ほかの行が `Scheduler` を持っても `TypeError` で止まらなくなる | 注に「体の行 BD のため・他の持ち主が `Scheduler` を持つ行を足すときは軸を決めてから」と書く |

## 1. 結果不変

- ✓ 実装役の 19 構成: [head_vs_sweep.json](head_vs_sweep.json) は 19/19 で 25 欄とも同じ(`moved` は空・`n_keys` 25・a=写し・b=作業木・腕は既定)。[sweep_vs_reserve.json](sweep_vs_reserve.json) は 19/19 で 27 欄とも同じ・[head_vs_reserve.json](head_vs_reserve.json) は 19/19 で 25 欄とも同じ。どれも `env` は空。
- ✓ **自分の 4 構成**(`w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`): HEAD の写しは本体 `82eeab0` の `git archive`(src と `HEAD_TREE_FILES` の追跡ファイル 8 本と w6-regen の置き場)+写しの根に本体の data へのつなぎ(10e の docstring の手順)。道具は本体 `82eeab0` の `byte_check_10e.py`(写しの側は `tree_missing` 空)。作業木の側は `PYTHONPATH` に作業木の src(`src_is_worktree` 真)。両側とも `data/world/v2`。**4/4 構成で 25 欄とも同じ**(final `b8eadcb51e8705e7`・`c88ba9104f45f897`・`e1288e092ddaca86`・`768b2262e3b0999e`・呼数 64,528・50,006・51,655・67,794・倒れる 5・顕著行為 10・出動 5)。本体の `d35a9b6` → `82eeab0` の src の差(2-3c の器だけの `rail_events.py` など)は既定の結果に効かないことも、この比べで確かめたことになる。
- ✓ 最後の src での腕 reserve: 実装役の 19 構成の reserve の side は、結果に効かない名の付け替え(`_plan` → `_reservations` ほか)の前の src で取ったもの(記録 §7-2b)。自分の確かめ(§6 の `w6_v3_default` の 27 欄と、`w6_v3_activity_off` の 2 日の通しと再開)は今の src で回し、どれも sweep と同じ。
- ✓ 2 日と再開(§6 の独立の確かめ)・系ごとの指紋(実装役の [probe_head_vs_sweep.json](probe_head_vs_sweep.json)・[probe_sweep_vs_reserve.json](probe_sweep_vs_reserve.json)=3 構成とも動いた系 0・項の数も同じ)。

## 2. 口と約束

- ✓ 口の型と名: `engine.body.BodyModel`(`step(part, r, now, **kw)`=部分 `interoception`/`felt`・`initial(n=None, *, energy=None, eer=None)`・値だけの口 `felt_temperature`・`felt_cells`・`collapse_draw`)・腕 `--body-schedule {sweep,reserve}`(既定 sweep・環境変数 `SHIBUYA_BODY_SCHEDULE`)・manifest の末尾 `body`(設定 8・観測 14)・状態台帳の行 `BD`。発注文との違いは L2(倒れるは持ち主を通らない)と、引き直しを「活動の変更の口」でなく写しとの比べにした点(仮採用 1・台帳 `BR-BODY-RESERVE-DETECT`・活動を書く口が約 40 か所あるという理由は妥当)。
- ✓ 約束ごとの試験: 同じ値(`test_body_same_values.py` 24)・reserve=sweep と負の対照と引き直しと再開(`test_body_reserve.py` 19)・守り(`test_body_guard.py` 6=AST の負の対照つき)・出典(`test_body_rules_sources.py` 6)・器(`test_system1_placeholders.py` 4)・manifest と腕(`test_body_manifest.py` 5)。計 64 本(収集で確かめた・slow 0)。**試験の無い約束**: 腕 sweep で予約の配列が空であること(M1)・性能(L6)。
- ✓ 決定の反映: ③ の 3 件(D8・A2・D9)と D18 を「本人の体」の持ち主にまとめた・TM5 の受入=全員を見る版と一致。決定 §1-5 の条件「研究で意図しないと裏付けがあり選択を決めないもの」の確かめと倒れる率の出典探しは本段でしていない(記録 §13・§14 の申告どおり=親のリサーチの段)。

## 3. 発注文の「作るもの」

| 番号 | 判定 | 根拠 |
|---|---|---|
| 1 体の層 `engine/body/` | △ | 3 件と D18 を同じ値の口に移した・resolve と環境の過程は口を呼ぶ・書き手は増えない(§5)・conf と出典と台帳の行。倒れるは持ち主を通らない(L2) |
| 2 TM5 の予約の口 | ✓ | `Scheduler` を流用・腕 reserve・19 構成で sweep と同じ・負の対照・引き直しの単体の試験・再開。活動の口への接続は写しとの比べで代えた(仮採用 1・宣言あり) |
| 3 器だけの 3 件 | ✓ | 口は None を返すだけ・W10 の読みの口・`NEARBY_CHANGE_KINDS=("loud_sound",)`・`Percept` の欄と形の版と空の欄 9 は同じ・台帳 3 行(5-3・5-1・5-3・expedient・inferred) |
| 4 D18 | ✓ | `BodyModel.initial`(空腹 2・疲れ 2・暑さ 5・段・エネルギー収支の食後の消費と写し)。刻み 0 の活動は予定の表の側に残した(仮採用 5・妥当) |
| 5 manifest・状態台帳・凍結の表 | △ | manifest の末尾 `body`・行 BD・凍結の表は増えた分だけ。行 BD の大きさの宣言が実態と違う(M1) |

「できなかったこと」の申告(③ の裏付けと倒れる率の出典のリサーチ・10e の道具の直し・予約の腕が遅い)は実態と合う。10e の直しは本体で既に済んでいる(L4)。

## 4. 守り

- ✓ 書く口: SoA の体の欄を書くのは resolve の 11 関数のまま(HEAD の写しと作業木を自分の AST で数えた=10 関数を代入の形で拾い、`apply_detection` の `field(crossing.stage_field)` は grep で確かめて 11)。口の呼び手(`R.advance_body`・`R.set_thermal` × 2・`R.initialize`・`R.initialize_energy`)は両側とも 5 か所。体の層の 5 ファイルの代入を AST で全部見て、SoA への書きは 0(書くのは自分の予約の列と局所の配列だけ)。
- ✓ 実行時の守り: `BodyModel` は `__slots__` と `__setattr__`・`__delattr__`(試験あり)・`meter_view` は `MappingProxyType`・`STAGE_FIELDS` と `BodyInitial.stages` も `MappingProxyType`・`BODY_RULES` は凍結の dataclass の tuple。`BodySchedule` には実行時の守りが無い(L7)。
- ✓ 負の対照: `test_body_guard.py` が外から書く・予約の列の口を呼ぶ・`step` を呼ぶ行を植えて見つかることを確かめている。写しは SoA のビューを持たない(`np.shares_memory` の試験)。

## 5. 宣言と凍結

- ✓ 系の表: HEAD の写しと作業木で `SYSTEMS` を正規化して比べた。32 系・同じ順・`resolve_ops` と `writes.soa` は同じ。違いは `body` の `reads` に `layers.body`・`writes.paths` に `BD:body.*`、`world` の `writes.paths` に `BD:body.*`、`close_final` の `reads` に `layers.body` の 4 か所だけ。`writes_soa_frozen.json` は変わっていない。
- ✓ boxes の `OWNER_NAMES` の末尾 `body`・`Layers.body`(既定 None)・`hash_owners` の末尾 `body`・`OWNER_CLASSES["body"]`。
- △ 状態台帳の行 BD: 軸 1 diag・軸 2 discardable・外 114・全体 205・版は上げない(1-3〜3-3 と同じ仮採用)。再開で復元が要らない理由(下界の予約なので状態から引き直せば結果は同じ)は確かめた(§6)。大きさの宣言は M1。`VALUE_CLASSES` の影響は L8。
- ✓ 凍結の表: `manifest_keys_frozen.json` は末尾に `body` だけ。`tick_word_allow.json` から消した `per_tick` は src に残っていない(grep 0)。
- ✓ manifest の既存の欄: HEAD の写しと作業木で 300 体・1 日を回し、`run_manifest_fields()` を葉まで比べた。final 同じ。一番上の鍵は作業木=HEAD+末尾 `body`。値が違う葉は git の情報(写しには無い)・`manifest_sections.paths` の `body.*`(足した分)・`bridges_count` と `bridges_version` と `daily[0].bridges_count`(つなぎの台帳の行の数。作業木 349・写し 344=本体の 2-3c の行と本段の 12 行の差)だけ。

## 6. 同値と独立の再計算

- 実装役の試験(腕 on/off・置き換えの前後・HEAD の式の写し)は読んだ(§2)。
- **独立の再計算 1(負の対照)**: 10e の 1 本のランを同じプロセスで包む道具を自分で書き、`w6_v3_default` で 4 本(sweep・reserve・予約の刻みと窓を +1・−1(−1 は今の次の刻みで止める))。reserve と −1 は sweep と 27 欄とも同じ。+1 は 25 欄のうち 15 欄と境目の列 2 欄が動いた(呼数 64,528 → 54,532・境目 空腹 26,054 → 25,631・疲れ 147,392 → 14,563・暑さ 43,987 → 41,003)。実装役の記録 §3-4 の値と一致。規則に通した体は reserve で 417,115/7,200,000(5.8%)・体感温度 75,282/1,440,000(5.2%)。19 構成の side の JSON では sweep の延べがどれも 7,200,000(全構成でエネルギー収支が on=毎刻み全員)なので、2.7〜6.9% の分母は正しい。
- **独立の再計算 2(予約の式の下界性・総当たり)**: エネルギー収支の空腹は、`EnergyModel.stage_of` と同じ式(float32 の比・`searchsorted` side=right)を写し、float32 の足し算を実際に毎刻み回して段が変わる最初の刻みを数えた。EER 900〜4,200・1 刻みの消費 0.001〜9 kcal・半分の体は境目の 0.02 手前、の 2 万体 × 3 種で、境目を越えた 57,528 体のうち予約が越えた刻みより遅いのは **0**。予約が次の刻みに止められた体を除くと、余白はいつも 2 刻み以上残った(float64 の見込みと実際の差は −754〜+1,013 刻み=1 刻みの消費が小さい体で float32 の丸めが効く・ulp の項が吸収)。疲れ・空腹 v1・休みは、入力を止めたまま sweep の規則を回して最初に値が変わる刻みと予約を比べた(活動の列なし/あり × 4,000 体 × 120 の始点=変わった 953,038 体)で、遅い予約・予約なしで変わる体とも **0**。式を読んだ確かめ: 疲れは起きていて 10 未満/就寝中で 0 より上 → 次の体の刻み・休んでいる体(期限が次の休みの刻みより後)で 0 より上 → 次の休みの刻み(休みの刻みは体の刻みより前か同じ・休みの判定は入力が同じなら時刻とともに真から偽にしかならない)。エネルギーの余白=2+⌈j × ulp(1.5 × EER/3) ÷ 1 刻みの消費⌉ は、足し算 1 回の誤差 ulp/2 × j 回の 2 倍と、比の割り算の丸め(約 ulp/2)を覆う。
- **独立の再計算 3(2 日と再開)**: `w6_v3_activity_off`(実装役の 2 構成と別)・5,000 体・2 日。HEAD の写しの通し・作業木 sweep の通し・reserve の通しが final `66381dbe2fd3a970`・115,066 呼・checkpoint 8 点とも同じ。sweep で刻み 750 と 1,440 に止めて reserve で再開=通しと final・呼数の和(23,336+91,730・50,006+65,060)・止めた後の checkpoint(6 点・4 点)が同じ。

## 7. 試験

- ✓ 範囲の試験(発注の一覧=`tests/engine/body tests/engine/systems tests/engine/events tests/engine/time tests/engine/bridging tests/engine/rights tests/engine/tools tests/perception tests/engine/experiment` と 10b・10d・10f・energy_balance・sim_time_T の 6 本・`-m "not slow"`・`-n 2 --dist loadfile`・子にも作業木の src): **1,230 passed・failed 0・skipped 0**(19 分 15 秒・requires_data の飛ばし 0=data のつなぎで実データの試験も回った・別の作業木のランが並行していた)。新しい試験は 64 本(収集で確かめた・slow 0)。
- ✓ `lint-imports`(作業木の src): 5 契約とも KEPT・0 broken。
- `tests/c7` は回していない(第334 の規律)。封印の層は読んでいない。`engine/energy.py` は作業木で変わっていない(`git diff` 0)。読んだのは `stage_of`・`hunger_copy`・`expenditure` の式と `HUNGER_RATIO_EDGES` の行だけで、錨の読み口は読んでいない。byte-check の写しの木には 10e の手順どおり錨 3 本が写る(中身は開いていない・写しは検収の後に消した)。全体の試験は親が回す。

## 8. 抜け道と記録

- (a) ✓ 既定の不変(§1)。(b) ✓ ③ の移し方: D8 `rules.interoception` は HEAD の `advance_body` と同じ式と順(`int16` に上げて ±・上限 10・就寝 −2・休み −1・消費は `+` の後に `[:]=`=前の `+=` と同じ float32 の丸め)・A2 はセルごとに `rint`・`clip` してから体のセルで引く(要素ごとの丸めなので添字と入れ替えてよい・舞台の外は丸めた生値=HEAD の `base` と同じ)・D9 は同じ流れから同じ順(ポアソン → 在圏の体から重複なし → 昇順)・D18 は同じ値と段。倒れる率は expedient・出典なし・`BR-BODY-COLLAPSE-RATE`(文の数 935,373 件/年と約 1.8 件は HEAD の salient の見出しの項を移したもの=新しい数ではない)。(c) ✓ 予約の式・引き直しの条件・負の対照・延べの数え方(§6)。(d) ✓ 器だけの 3 件(§3)。描画のバイト不変はテープの blocks と呼の列の sha が 19+4 構成で同じことで確かめた。(e) ✓/△(§5)。(f) 性能は L6。予約の腕が sweep より遅いのは全員のエネルギーの積み上げと写しとの比べ(体数ぶんの配列の比べ 7 本)と予約の積みのため=台帳 `BR-BODY-RESERVE-*`(外す段 T3)で宣言済み=T3 の版上げまで既定 off のままでよい。
- (g) 記録: `README.md` と道具と JSON に絶対パス・ホスト名・個人名は無い(`tools/__pycache__` の pyc だけ絶対パスを含むが gitignore の対象)。改行は全部 LF。仮採用 6 点: 1(写しとの比べ)は活動の口が無い今は妥当・T3 で口の知らせに。2(全員の積み上げ)は float32 の足し算の順を守るため必要。3(体感温度も予約)は発注文が「暑さの段」を挙げており妥当。4(行 BD は軸 1 diag)は受入の条件(結果が sweep と同じ)と負の対照の試験で守る限り妥当。5(刻み 0 の活動は予定の表)は妥当。6(`step` は部分 2 つ)は呼ぶ時刻が違うので妥当。共有ファイルの一覧(記録 §12)は `git diff --stat` の 28 本(src 16・試験 11(凍結の表 2 本を含む)・台帳 1)と合う。
- (h) 取り込みの衝突の見込み(本体 `82eeab0` → 3-2 → 3-1 → 3-5 の順):
  - 本体 `82eeab0`(2-3c)と: `docs/design/bridging-ledger.json`(両方が末尾に行を足す=文の衝突)・`tests/engine/bridging/test_bridging_ledger.py` の expedients の数(本体 143 → 144・本段 143 → 155=同じ行の衝突・取り込んだ後は 156)・manifest の `bridges_count`(作業木 349・本体 344 → 取り込んだ後 356 の見込み)。
  - 3-2・3-1 と: boxes の `OWNER_NAMES` と `Layers` の末尾・`state_io.hash_owners` の末尾・状態台帳の行(BW・CAL・BD の並び)と `OWNER_CLASSES`・`EXCLUDED` の末尾・`test_state_ledger_10b.py` の行の数(外 114・全体 205)と並びの末尾・manifest の一番上の鍵の末尾(`batching`・`calendar_shadow`・`body` の順)と `manifest_keys_frozen.json`・末尾を数える試験 6 本(`test_t0_tm9_fields.py`・`test_percept_schema.py`・`test_rights_manifest.py`・`test_c0_phone_table_empty_and_declared.py`・`test_manifest_rules_bridges.py`・`test_env_and_sections_10f.py`)・`CONFIG_PATHS_SHA256`(取り込むたびに計算し直す)・`cli.py` の引数の並び・`test_system1_placeholders.py` が `conductor.run_system` を包む(3-2 で名が変われば 1-2 の試験と一緒に直す)・系ごとの指紋の道具 `probe_bd35.py` が外す行(BW・CAL も外す必要が出る)。

