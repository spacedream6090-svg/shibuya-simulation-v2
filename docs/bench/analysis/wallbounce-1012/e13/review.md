# 第 1 期 1-3 出来事の記録の検収(別の検収役・実装は見ていない)

- 検収役 Opus 5.5。対象は作業木の枝 `1-3/events`(HEAD `4998174` の上の未 commit の差分)。読むだけで、書いたのはこの記録 1 本。
- 正: [口の約束 1-3](../../../../design/v2-foundation-contracts-2026-10-13.md)・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-5 CP12・§4-4 CT9・発注文(実装役あて)・実装役の記録 [README.md](README.md)。
- 自分で回したもの: byte-check 4 構成(HEAD の src と作業木の src・記録 on と off)・合成の世界の 2 日の manifest の比べ・静的と実行時の負の対照(一時のスクリプトと src の一時の写し=リポには残していない)・試験の部分集合。生の出力は作業木の `_bc_review/` に置き、検収の後に消した。

## 判定

**条件つき受入**。結果不変(◎)は 4 構成の自前の byte-check と合成の世界の manifest でも確かめた。CP12 の門は「型を作る所」では実行時の検査が効く(書きの検査を切っても外れない)。ただし「書く所」で見ていないので、既にある実験の原因の使い回しと `__init__` を飛ばした偽物が書ける(中 M1)。条件は M1 の直しと、M2(39 万体の見積り)を記録に足すこと。テープと金・物の生ログに目印の列を足していない点は発注との差なので、親が判断する。

## 1〜9 の確かめ

| # | 項目 | 判定 | 根拠 |
|---|---|---|---|
| 1 | 結果不変 | ✓ | 実装役の [byte_check_e13.json](byte_check_e13.json): 19/19 構成で 25 欄とも同じ・呼数の差 0。[byte_check_e13_on_off.json](byte_check_e13_on_off.json) も 19/19 で同じ。**自前の 4 構成**(HEAD 側は本体の src=`src_is_worktree` 偽、e13 側は作業木の src=真、記録は既定の on): 4/4 で 25 欄とも同じ。final は `w6_v3_default` `5f7ae9ff24005314`(65,597 呼)・`w6_v3_activity_off` `e0054a837c6ec4c1`(50,301)・`w6_v1_default` `24375ee3dab349e8`(51,835)・`v3_mem_rel` `73a78288ab5e1498`(69,111)。テープの calls の列は 21 個で名も sha も同じ。e13 の on と `SHIBUYA_EVENTS=off` も 4/4 で同じ。**合成の世界の 2 日**(80 体・記憶+関係+同席+店の記憶): final・呼数・checkpoint の 2 本のハッシュ・日の締めの後の 2 本・manifest の一番上の鍵が同じで、平坦にした葉 2,444 個に違いも消えた葉も無い。足された葉は 24 個で、どれも `daily[*].events` の下 |
| 2a | CP12 静的(別名 10 形) | △ | 発注の 10 形のうち 8 形を捕まえる(直接・`from … import`・`import … as`・`getattr`・属性の鎖・`__dict__`・`vars()`・サブクラス。`globals()` は `*` の import の形なら捕まえる)。**抜けるのは 2 形**: `globals().update(dict(inspect.getmembers(L)))` の後の `globals()[…]` と、文字列の `eval`。発注の外の形では `sys.modules[...]`・`importlib.import_module` に組み立てた名・`L.__getattribute__(名)`・`operator.attrgetter`・`exec` も抜ける。どれも実行時の検査は捕まえる(2b)。**負の対照 3 本**(`*` の import+`globals()`・属性の鎖・サブクラス)を src の一時の写しに植えると試験 `test_no_module_outside_the_gate_names_the_experiment_type` は落ちた(植える前の写しでは通る)。`eval` と `sys.modules` を植えると試験は通った(=抜けた) |
| 2b | CP12 実行時・切替口 | ✓ | 直接・別名・`getattr`・`eval` の文字列・`dataclasses.replace` はどれも `PermissionError`。プロセスを `SHIBUYA_WRITE_GUARD=off` で起こしても同じく落ちた(`write_permit.enabled()` は偽)。外さない理由は `log._only_from_gate` の docstring と記録 §2 にある |
| 2c | 第 4 の型 | △ | `Experiment` の子・`_Cause` の子(`type`・`make_dataclass`・`types.new_class` で名と置き場を真似る)はどれも `TypeError`。型の外の物を `Event` に渡すと `TypeError`、`Event` の子を `append` に渡すと `TypeError`。**ただし `__init__` を通らない `Experiment` は作れて、`append` が受け取る**: `object.__new__`+`object.__setattr__`/`__dict__`・手で組んだ pickle の流れ(NEWOBJ+BUILD)・`Process` の `__class__` の差し替え・`type(既存).__new__`(型の名を書かない=静的にも見えない)。記録から読んだ実験の原因をそのまま別の出来事に付けることもできる(M1) |
| 3 | 書き口が 1 つ | △ | 行を足す公開の口は `append` だけで、宣言の無い系から呼ぶと `PermissionError`(`gate.admit` 経由でも同じ)。`ids()` は写しを返し、`__slots__` で新しい属性は付かない。**段 C と同じ守りは無い**: `TickScratch`・`Buffers` は `__setattr__` で差し替えを落とすが、`EventLog` は `_ev_n` の差し替え・列への直接の書き・`_ev_causes.append`/`extend`・`enabled` の切り替えを実行時に止めない。`close_day`・`begin_step` も宣言の無い系から呼べる。試験のときは段 B が `E:` の道筋の変化を捕まえる(L2) |
| 4 | 宣言 | ✓ | `writes.paths` に `E:events.*` を持つ系は world・checkpoint・day_close・close_final で、凍結の表 `writes_paths_events.json` と同じ。宣言の外の系は `E:` の道筋に当たる型を持たない。状態台帳の行 `E` は軸 1 diag・軸 2 discardable(差分で確認)。段 B の宣言の外 0 は `test_declared_writes_cover_the_event_changes` と `tests/engine/systems/` で見た(#8)。台帳の版は上げていない(L5) |
| 5 | 目印 | △(発注との差) | ActualLog: 固定幅のレコード(凍結の dtype)は変えずに、並びの列 2 本(`_event_t_ns`・`_event_seq`)を足しただけ。保持窓で畳んでも同じ行を残す。`test_e_log_links_actual.py` は配線した系の分(world・close_final)で 1 対 1 を見ていて、通った(#8)。テープ: 列を足していない。calls の列は 21 個で、名と sha は HEAD と同じ(版 4 のまま)。結びは `LlmCall.call_id`=テープの `call_id` 列の値に任せている。金と物の生ログ: 列を足していない。発注の 4 と口の約束の約束 (2) の「目印で結ぶ」に対して、ActualLog の分だけ作った。記録 §5・§10 の 10 で仮採用として申告済み=**親の判断** |
| 6 | 語彙 | ✓ | `what` は 55 語の閉じた表で、表の外は `ValueError`。行為 12 語は `llm.contract.ACTION_VOCAB_V3` を import してそのまま使う(写しではない)。過程・金・物の写しは元の表と突き合わせる試験がある。`via` は CT9 (b) の 5 つ+無し。`VOCAB_CODES` は普通の dict なので、実行時に語を足せてしまう(L7) |
| 7 | manifest | ✓ | 日次の記録の末尾に `events`(`on`・`rows`・`bytes`・`by_what`・`by_cause`・`live_rows`・`live_bytes`・`evicted`)。一番上の鍵は足していないので、T0 の `manifest_keys_frozen.json` は変えていない(作業木でも差分なし)。足した鍵は別の凍結の表 `manifest_events_keys_frozen.json` に置いた。既存の欄の値は、実装役の 7 本([manifest_check_e13.json](manifest_check_e13.json)=違うのは環境の 3 欄だけ)と、自前の合成の世界の 2 日(#1)で同じ |
| 8 | 試験 | (下の §試験) | |
| 9a | 記録 off | ✓ | off では ActualLog の目印は seq=-1 のまま、`close_day` は同じ形の off の記録を返し、`result.event_log` は空。自前の 4 構成の off も on と同じ final・テープ。CLI の `--events on` は環境変数の off を上書きしない(L3) |
| 9b | 行数とバイト・39 万体 | ✗ | 5,000 体の実測(28,835 行/日・2,076,120 B/日・目印 345,960 B/日)は記録 §7 にある。**39 万体への見積りと M8(RSS ≤ 24 GB/ラン)との比べが記録に無い**(M2)。下の §見積りに検収役の見積りを置いた |
| 9c | id の決定性 | ✓ | id=`(t_ns, seq)` は刻みの頭の時刻と刻みの中の通し番号。同じランの 2 回で同じ列、刻みの境目からの再開でも通しのランと同じ id(`test_e_log_schema.py` の 2 本・#8)。続きの番号は作りの上で保たれる。ただし `n_appended` と日次の `rows`・`live_rows` は再開のランでは 0 から数える(L6) |
| 9d | 絶対パス・ホスト名 | ✓ | 記録のフォルダ(README・JSON・`tools/`)に絶対パス・ホスト名・個人名は無い。新しいファイルはどれも LF |

## 試験

作業木で `tests/engine/events tests/engine/systems tests/engine/time tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py` を `-n 2 --dist loadfile` で回した(`-o addopts=""` なので `slow` も入る): **371 passed・失敗 0・飛ばし 0(7 分 52 秒)**。新しい試験 `tests/engine/events/` の 87 本(`slow` の 19 構成の on/off=300 体を含む)が全部通った。`lint-imports`(作業木の src を読ませて `--no-cache`)は 5 契約とも守られている(189 ファイル)。

## 見積り(検収役・未リサーチ(expedient)の外挿)

- 1-3 で配線した分(世界過程の ActualLog の行+区切り)は世界の大きさでほぼ決まる。200 体で 26,153 行/日・5,000 体で 28,835 行/日の 2 点から直線で外挿すると、39 万体で約 24.4 万行/日=約 17.6 MB/日。保持窓 7 日で約 123 MB、ActualLog の目印(12 B/行)が約 20 MB。合わせて約 143 MB で、M8 の約 0.6%。1-3 の分は予算に収まる。
- **配線していない系を載せた後が問題**。お金の行(4.07 行/体/日=10b-prep #20)は 39 万体で約 159 万行/日・7 日で約 800 MB(M8 の約 3.3%)。LLM の呼び出しの行を mock の既定 v3 の 13.1 呼/体/日(65,597 呼 ÷ 5,000 体)で見積もると、約 512 万行/日で、列だけで 7 日に約 2.6 GB(約 11%)。さらに原因の表は呼び出しごとに Python の物を 1 つ持つ。検収役の実測では、原因の表の 1 件あたり 221 B(入力の id 0 個)〜525 B(3 個)。7 日分の約 3,600 万件で約 7.9〜18.8 GB になり、M8 の 33〜78% に当たる。`LlmCall` を配線する段(1-8 の候補)の前に、原因の表を列の形(`call_id` を整数の組に・入力の id は CSR の配列に)へ直し、成長の宣言を `check_growth` に載せる必要がある。

## 欠陥(重さ順)

### 中

- **M1 CP12 の検査が「作る所」だけで、「書く所」に無い**(`src/shibuya/engine/events/log.py` の `Event.__post_init__` の 232 行と `EventLog.append` の 332 行は型の一致しか見ない)。抜け道は 2 種類ある。(1) 記録から読んだ実験の原因(`log.event(i).cause`・`log._ev_causes`)を、口の外で別の出来事にそのまま付けられる。新しい物を作らないので、静的にも実行時にも見えない。後の段が「この出来事は実験のせい」と帰属を写す近道として起こりうる形で、CP12 の「直接の原因だけを書き込むその場で記録する」に反する。(2) `object.__new__`・`type(既存).__new__`・手で組んだ pickle の流れ・`__class__` の差し替えで、`__init__` を通らない偽物を作れて、`append` がそのまま受け取る。記録 §10 は `type(x).__new__` の形を限界として申告しているが、使い回しの形は申告に無い。**直し方**: `EventLog.append` で `type(ev.cause) is Experiment` のとき、呼び手のフレームのコードが `gate.ADMIT_CODE` であることを見る(`_only_from_gate(sys._getframe(1))` と同じ形。書きの検査の切替口でも外さない)。こうすると (1) も (2) も書く所で落ちる。わざと `ADMIT_CODE` を借りた関数を作る形だけが残る。負の対照に「使い回し」「`type(既存).__new__`」「`object.__new__`」の 3 本を足す。
- **M2 39 万体の見積りと M8 との比べが記録に無い**(発注 9b)。1-3 の分は収まる(上の §見積り)。ただし原因の表の作り(呼び出しごとに Python の物)は、`LlmCall` を配線した段で M8 の 3 割を超えうる。**直し方**: README §7 に上の見積り(または実装役の見積り)を足し、PENDING に「`LlmCall` の配線の前に原因の表を列の形へ・成長の宣言を `check_growth` に」を残す。

### 低

- **L1 静的な検査の抜け**(`tests/engine/events/test_e_cause_three_kinds.py` の `offenders`): 発注の 10 形のうち `globals()`(`inspect.getmembers` 経由)と文字列の `eval` を捕まえない。発注の外でも `sys.modules[...]`・組み立てた名の `importlib`・`__getattribute__`・`attrgetter`・`exec` が抜ける。どれも実行時は落ちる。src には今 `eval`・`exec`・`sys.modules[...]` の使い所が無いので、src 全体で禁止する検査は安く足せる。少なくとも試験の docstring と記録 §2 の「別名 12 形」に、発注の 10 形との対応と抜ける形を書く。
- **L2 `EventLog` に段 C と同じ差し替えの守りが無い**(`log.py` 277〜311 行): `__setattr__` が無く、`close_day`・`begin_step` も宣言を見ない。試験のときの段 B が捕まえるので、既定の誤りは試験で見つかる。直すなら `_ev_*` の差し替えを `events_write_allowed()` で見る `__setattr__` を足し、`close_day` にも同じ検査を入れる。直さないなら限界として記録に書く。
- **L3 CLI の `--events on` は環境変数 `SHIBUYA_EVENTS=off` を上書きしない**(`src/shibuya/cli.py` 1191 行は off のときだけ `set_enabled(False)`)。既定を `None` にして、指定されたときだけ `set_enabled(args.events == "on")` にするか、記録に「環境変数が勝つ」と書く。
- **L4 発注の「編集してよい」の外の編集**(`tests/engine/test_state_ledger_10b.py`): 行を足すと必ず要る直しで、中身は妥当。試験の名は `test_ledger_has_187_rows_in_two_axes` のままで 188 を確かめている(名が古い)。親の承認が要る。
- **L5 台帳の版を上げていない**(`src/shibuya/engine/state_ledger.py` の `LEDGER_VERSION`): 自身の注「列や行の判定を変えたら上げる」に反する。理由(manifest の値が動き、前の版の状態のファイルから再開できなくなる)は記録 §10 の 4 にあり、仮採用。親の判断。
- **L6 日次の `events` の数は再開をまたがない**: 再開のランは空の記録から数えるので、途中から再開した日の `rows`・`live_rows` は通しのランより小さい。diag で、既存の再開の試験は比べていない。記録に一行書く。
- **L7 語彙表を実行時に開ける**(`src/shibuya/engine/events/vocab.py` の `VOCAB_CODES`・`VIA_CODES` は dict): `types.MappingProxyType` にすれば閉じる。
- **L8 目印の列のバイトがどの成長の宣言にも入っていない**(ActualLog の `nbytes` は外し、`EventLog.growth_declaration()` は `check_growth` に載っていない)。記録 §6・§10 に申告済み。全部の系を載せる段で宣言し直す。
- **L9 保持窓の鍵が 2 つの記録で違う**: ActualLog は行の `tick`(予定の刻みのことがある)で、出来事の記録は書いた刻みの `t_ns` で落とす。7 日の境目で、目印が落ちた出来事を指すことがありうる(diag だけ・7 日を超えるランで)。

## 親に確かめてほしいこと

1. M1 の直し(書く所での検査)を 1-3 で入れるか。入れるなら負の対照 3 本も一緒に。
2. テープと金・物の生ログに目印の列を足さないこと(記録 §5・§10 の 10)を認めるか。発注の 4 と口の約束の約束 (2) の文面とは違う。
3. 仮採用 11 件(記録 §10)、特に台帳の版(L5)・持ち主 `events` を末尾に足したこと・切替口を `run_day` の引数にしなかったこと。
4. 範囲の外の編集 `tests/engine/test_state_ledger_10b.py`(L4)。
5. `LlmCall` を配線する段の前に、原因の表を列の形へ直す件(M2)を PENDING に残すか。
