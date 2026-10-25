# 第 6 期 6-2 カレンダー 3(雇い主・祝日・腕 `--calendar-3 arm`)の独立検収

- 検収役 Opus 5.5(実装は見ていない)。対象=作業木の枝 `6-2/calendar-3-employer-arm` の未 commit の差分(土台 `687f513`)。
  実装役の自己申告は使わず、ディスクの実在・自分の試験・自分の再計算で確かめた。作業木で書いたのは本書だけ(試しは git の外の
  `_bc2/review/`)。本体は読むだけ。5,000 体のランは 1 本ずつ。封印した層は読んでいない。
- 比べた本体 HEAD=`71c53bd`(土台 `687f513` との差は文書 3 本だけ=src と `HEAD_TREE_FILES` は同じ)。

## 判定

**条件つき受入**(高 1・中 1・低 9)。既定 off は 1 バイト不変(自分の 4 構成で 25 欄同じ)。腕 arm の監査・記録 on/off・2 日の
再開の final は自分の再計算でも合う。ただし**再開で雇い主の口の表が変わる**(高 H1)。2 日のランでは final が偶然同じだが、
次の週に組むランや店の単位の休みの返事で通しとずれる。H1 を直して再開の比べに `roster` を入れれば受入でよい。

## 1〜11 の確かめ

| # | 項 | 判 | 根拠 |
|---|---|---|---|
| 1 | 既定 off で不変 | ✓ | 実装役の 19 構成の生の JSON(`_bc/bc/head.json`・`ca3.json`): 作業木の側は `src_is_worktree` 真 19/19・写しの側は偽・`tree_missing` 空・`env` 空。自分の 4 構成(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`): 本体 HEAD の写し(`git archive`+`HEAD_TREE_FILES`+data のつなぎ=回した後に .NET で外した)と作業木の src で **25 欄とも同じ**(final `bb86f898…`・`3cdf9dbf…`・`8fca095b…`・`94becde2…`・呼数 63,572・49,462・50,447・66,374=実装役の値と同じ)。既定 off で層が作られない形は `test_default_off_builds_nothing`(層 None・manifest の節 0・状態のファイルの `calendar3.*` 0・指紋の鍵 0・勤務の出来事 0)。腕 c1 だけのランは下の 4 |
| 2 | 誰が決めるか | ✓(注あり) | コードを読んだ: 本人の語 7 つの原因はどれも同じ関数の `_decide` の答え(枠=雇い主 `P_FRAME`・書いた=`P_NOTIFY`・申し出=`P_REST_DAY`・受けた/断った=`P_ANSWER`・休みにした=`P_APPLY`・遅れ=`P_LATE`)・道具の語「知らせ」は過程 calendar3。**自分の監査**(`audit_causes` を使わず別に書いた・5,000 体 2 日): 勤務の族 6,978 行(枠 3,808=544 人 × 7 日・書いた 2,715・申し出 74・受けた 33・断った 24・休みにした 11・遅れ 32・知らせ 281)・控え 4,685 件・食い違い 0(LlmCall でない/体が違う/控えに無い/種類が語に合わない/時刻が判断の刻みと違う/知らせの原因=どれも 0)・枠の相手 544 人は全員が週ごとの働く人。エンジンが決めているのは組む機会(週の最後の日の頭)・枠の数(W20 の約束の形)・届く(C1 の網)・送り直しの機会と回数・申し出と遅れの機会(つなぎの台帳に宣言あり)。注: 届いたシフトを「書く」こと自体は判断でない(知らせの時刻だけが判断)=発注どおり。労働時間の行は `rules.get` で読むだけ(`economy/taxes.py` の machine の口 `_row`・`_bridge_row` は触っていない=差分なし)・超えた数を数えるだけ。規則の表の読み手の一覧の試験に `engine/calendar3/layer.py` を足した(腕のランだけ) |
| 3 | 雇い主の口(つなぎ) | ✓(H1) | `roster.build_roster`: 雇用の行(体 → 組織)から外の雇用主の番号を除く・組織の無い体は店の担当の行の店・店長 → 最初の担当 → 本人(担当が 1 人だけ)。正規は W20 の `recurrence`=毎週固定で除く(W20 は体ごとに一様=`w20_calendar_1a.py:1176-1177`)。候補=休み+W20 の重ならない枠。つなぎの台帳 `DOC-ca3-scheduler-pick`・`-frame-form`(外す段 6-6)・`-port-candidates`(6-1)。5,000 体の数は実装役と同じ(単位 428=組織 420・店 8・店長 4/最初の担当 153/本人 271・組んだ 544)。**ただし再開で表が変わる**=H1 |
| 4 | C3 と行 | ✓ | C3 の連絡はどれも `ContactLayer.workplace_send`(C1 の宛先の判断 `P_WHOM`・文の口・`_queue_send`/`_place_call`)。5,000 体 2 日で C1 の計器 `c3:msg` 133・`c3:call` 147・`c3:group` 142 がカレンダー 3 の `sent:*` の内訳の和と一致。働く人の行はカレンダー 2 の器 `PromiseBook.write`(種類「勤務」・アプリ・確定・元の会話・誰と=雇い主)。`KINDS` は末尾に足しただけ(前の番号は不変)。`_dial` → `_place_call` は行の切り出しだけ(中身は同じ)。**腕 c1 だけの 5,000 体 1 日**: 作業木 `2b9c9346…` = 本体 HEAD の写し `2b9c9346…`(checkpoint 4 個も同じ)。注: ct_c1 §16 の `b4bdb154…` は 4-2(規則の表と天引き=既定 on)より前の土台 `6f07eff` の値で、今の HEAD 自身が `2b9c9346…`=本段の差ではない |
| 5 | 祝日 | ✓(L1) | `CommonCalendar` は暦の口(内閣府の CSV)を読むだけ・常識の文 1 行。試験用の印の口は `build.py:832-840`: 腕 arm かつ下の腕 on のときだけ規則の違反を止めない。**負の対照(5,000 体の世界・自分で)**: 腕 arm で印なしの日曜始まり=止まる・腕 off で `SHIBUYA_CALENDAR_3_TRIAL=on`(C1+カレンダー 2)=止まる(どちらも「開始日の検査で止めた(real)」)。祝日の枠の数え(実装役の JSON): 休み 119+勤務 425=544=組んだ人数(1 人 1 日)・営業時間の外の枠 409 → 413(祝日の日の表は PH の行=`opening_row`)。L1=印のランの manifest の `calendar.start_check` は空のまま |
| 6 | 日曜始まりと K9 | △(M1) | 0 日目の日曜は W17 の行が無く体が全員範囲の外=寝ていない・主の判断 0 → **組むのは全部 T=0(0:00)**(自分のランで枠の判断 3,808 回の刻みは最小=最大=0)。「起きていて主の判断の無い最初の刻み」の「起きていて」が効いていない。日曜 → 月曜で `state_io.py:194-200` が計画境界の表の違いで `NotImplementedError`(活動層・classical・想起優先は起動時の表を写して持つ=K9 の張り直しの外)。活動層を外した 2 日は構造の確かめ(数は振る舞いでない)。既定のランは state_io を触っていない=影響なし(上の 1)。比較: (A) 今の日曜始まりの 2 日=軽い・活動層なし・組む刻みが 0:00 に寄る/(B) 月曜始まりの 8 日=K9 で日曜も月曜の行=活動層あり・起きている刻みで組む・重い(2 日の約 4 倍)。加えて、試験用の印の無いランは月曜始まり・連続する平日だけなので**日曜が来ない=腕は印の外では組まない**(M1) |
| 7 | 宣言と凍結 | ✓ | 系 `calendar_3`: `paths`=`CA3*:calendar3.* E:events.* CA2B:calendar2.book.* CT1*:contact.* BW:batching.* CA2G:calendar2._turns`・contact の `paths` の末尾に `CA3G:calendar3._reads`・窓の境目 `WINDOW_PATHS_CA3`(腕のランだけ)。状態台帳 外 144 → 149・全体 235 → 240(CA3S/P/G=behavior・CA3M/Q=diag・どれも required・腕 `calendar-3`)。`CONFIG_PATHS_SHA256` を自分で計算: 作業木 `94fe399f…99682dea`(319 本)・`calendar_3.*` の 9 本を外すと `ceb58699…bcba7901`=本体 HEAD の値と同じ。語彙 族「勤務」8 語=コード 93〜100・道具の名 `calendar3`・版 `events-vocab/6-2-ca3`。凍結の表の張り替え 13 本(試験 11+凍結の JSON 2)は本段の分だけ(語彙の末尾・版・数・並びに本段の行を足した形)。乱数の用途名 `calendar3.mock`/`.present` は src に他の使い手なし・通し番号 2^21+k×16+種類(k < 2^14)は C1(< 2^18)・カレンダー 2(2^20〜2^20+2^18)とぶつからない。控えの詰め方(通し番号−2^21 を 21 ビット)も範囲の内 |
| 8 | 2 日と再開・段 B・記録 on/off | ✓(H1) | 自分の 5,000 体 2 日(日 → 月・活動層 off・印 on): 記録 on の final `ba7d3b96…`=実装役と同じ・記録 off も `ba7d3b96…`・checkpoint 48 個の behavior-hash が全部同じ。T=1440 で止めて再開: final `ba7d3b96…`=通し・T≥1440 の checkpoint 24 個の behavior/full が全部同じ。**manifest の `calendar_3.roster` は通しと違う**(単位 428 → 420・店の単位 8 → 0・組んだ人 544 → 536=H1)。段 B: 合成の `test_stage_b_has_no_undeclared_writes` と負の対照(contact の宣言から `CA3G` を外すと「宣言の外」で落ちる)を単独で回して通った・5,000 体 1 日の段 B は未完(§試験) |
| 9 | 試験 | §試験 | 範囲・slow の world 1 本・lint-imports |
| 10 | 台帳と記録 | ✓(L5・L6) | つなぎの台帳 602 → 615(13 行の id・外す段・根拠を 1 行ずつ読んだ=6-6 が 4・6-1 が 5・6-2 が 3・7 が 1)。`add_bridges_ca3.py` を git の外の写し(本体 HEAD の台帳)で 3 回回した=1 回目で作業木の台帳と md5 同じ・2・3 回目は 0 行で同じ md5(冪等)。記録(README・JSON 2・道具 2)に絶対パス・個人名なし・CR なし。計器の表の照合: 日曜 1 日の単位 428/店長 4・最初の担当 153・本人 271・勤務日数 3/27/65/170/176/103・労働時間 1,493/314/103・C3 の送った 52/54/56(メッセージ=49+2+1・電話=49+4+1・グループ=49+6+1)・祝日 119/425・2 日の final=JSON と一致 |
| 11 | 問い 1〜5 | — | §問いへの意見 |

## 欠陥

| 重さ | 欠陥 | 場所 | 直し方 |
|---|---|---|---|
| 高 H1 | **再開で雇い主の口の表が作り直されて変わる**。表は組み立ての途中(`build.py:1438` の `roster_for_run`)で `runner.rights` から作るが、権利台帳は状態を戻した後の `rebuild_derived`(`build.py:1533`→`state_io.py:427-440`)で作り直される。再開の組み立ての時点の台帳は店の担当の行が 166(通しは 2,435)=単位 428 → 420・店の単位 8 → 0・組む人 544 → 536・外の雇用主 381 → 383・勤め先なし 199 → 205(自分の道具で両方の組み立ての台帳を数えた)。単位の番号で持つ状態(CA3S の `_composed`・`_plan`・CA3P の `_work_rows` の単位)と導出 `sched_units`(CONST の宣言)が再開の後にずれる=店の単位の休みの返事が雇い主の記録を直さない・次の週の組む機会が通しと違う。2 日のランは T≥1440 に組む機会が無く final が偶然同じ。実装役の再開の比べ(`tools/run_ca3.py:112` の `same`)は `roster` を外していて、合成の試験は表を monkeypatch で差すので見えなかった | `src/shibuya/engine/systems/build.py:1430-1441`・`src/shibuya/engine/calendar3/roster.py`(`roster_for_run`)・`src/shibuya/engine/state_ledger.py`(EXCLUDED の `roster`・`sched_units`) | 表を状態を戻した後に作る(`state_io.rebuild_derived` で `calendar3.rebuild_roster()` を呼ぶか、最初の刻みで作る)・`sched_units` も同じ。状態台帳の除外の理由を「再開では rebuild_derived で作り直す」に。試験: 権利台帳の本物の道(`OpeningProcess` の台帳)で作る合成の再開の試験(monkeypatch なし)で通しと表が同じ・`run_ca3.py` の比べに `roster` を入れる・できれば 8 日以上か店の単位の返事を含む再開 |
| 中 M1 | **組む刻みが全員 0:00**(5,000 体 2 日の枠の判断 3,808 回が全部 T=0)。0 日目の日曜は全員が範囲の外で寝ていない=「起きていて」が効かない。また試験用の印の無いランは月曜始まり・連続する平日だけなので日曜が来ず、腕は印の外では一度も組まない(雇い主の口の表と計器だけ) | `src/shibuya/engine/calendar3/layer.py:584-617`(`_open_compose`・`_opportunities`)・記録 §9 の 1 | 問い 1 の判断に添える: 組む日を週の最後の平日(金曜)にする案(印の無い月〜金のランで組める)か、月曜始まりの 8 日。少なくとも manifest に組んだ刻みの時の分布を出し、範囲の外の体を「寝ていない」と数える点を宣言 |
| 低 L1 | 試験用の印のランの manifest の `calendar.start_check` が空(違反は `calendar_3.trial` だけ)=開始日の検査の欄で選ぶ分析の道具は印のランを通ってしまう | `src/shibuya/engine/systems/build.py:832-840` | `start_check` に違反と印を入れるか、manifest の一番上に印の欄 |
| 低 L2 | 新しい識別子 `_open_compose` に「open」(発注の規律)・manifest の子 `compose.opens_at` | `layer.py:584`・`:748` | 名を替える(AST の試験の `_COMPOSE_OK` も)。manifest の鍵は設定の道筋に入るので替えるなら `CONFIG_PATHS_SHA256` を計算し直す |
| 低 L3 | 新しい src と試験のファイルが作業木で CRLF(既存のファイルは LF・README と JSON は LF)。`core.autocrlf=true` なので add で LF になるはず | `src/shibuya/engine/calendar3/*.py`・`tests/engine/calendar3/*.py` | 取り込みで index が LF か確かめる |
| 低 L4 | カレンダー 2 の計器 `live_rows.rows`(`len(book)`)が勤務の行を数える・カレンダー 2 の仲裁は勤務の行だけの体も「考えた」に入れる(`_look` は勤務を見ないので判断は出ない) | `src/shibuya/engine/calendar2/layer.py:801`・`:1021` | 計器を種類で分けるか宣言 |
| 低 L5 | `rules42/README.md` §2 の表で `labor.statutory_hours` の読み手が「なし」のまま(腕の読み手ができた) | `docs/bench/analysis/wallbounce-1012/rules42/README.md:62` | 注を 1 行 |
| 低 L6 | 用語集: 「枠」は呼数枠・思考トークン枠・判断モデルの「差し替え可能な枠」とぶつかる。雇い主の口・シフトを組む人・試験用の印・暦の常識の口は用語集に無く、ぶつかる語も無い | `docs/design/v2-glossary.md` | §2-8 の候補に足す・「枠」は「勤務の枠」 |
| 低 L7 | 試験の穴: C1 あり・カレンダー 3 なしで `sent_sink`・`read_sink` が None・`WINDOW_PATHS_CA3` が足されないことを見る試験が無い(5,000 体の腕 c1 が本体と同じなので挙動は確か) | `tests/engine/calendar3/test_ca3_runs.py` | 1 本足す |
| 低 L8 | 10e の `SWITCH_ENV` に `SHIBUYA_CALENDAR_3`・`SHIBUYA_CALENDAR_3_TRIAL` が無い(実装役の記録どおり=親の仕事) | `docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py:168-182` | 親が足す |
| 低 L9 | 記録 §10 の「範囲は直す前の 1 回だけ」→ 本書の §試験で回し直した | README §10 | §試験の数を写す |

## 試験(作業木の src・本体の .venv・`-q -p no:cacheprovider -o addopts="" -rf`)

- 範囲 `tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`(`-n 2 --dist loadfile -m "not slow"`): **4,181 passed・1 skipped・0 failed・0 errors**(56 分 15 秒・直した後の作業木で回し直した=実装役の 2 failed は解消)。
- `tests/engine/calendar3` の段 B・記録 on/off・再開・AST・既定 off の 10 本(単独): 10 passed。
- slow の world `tests/engine/calendar3/test_ca3_world.py`(1 本だけで): 1 passed。
- 5,000 体 1 日の段 B(`SHIBUYA_SYSTEMS_CHECK=1`・腕 arm・印 on): **未完**(60 分を超えても終わらず、自分で起こした背景の仕事を止めた=結果なし・空欄)。段 B は合成の 2 本(宣言の外 0・`CA3G` を外すと落ちる)だけで確かめた。
- `lint-imports`: 5 kept・0 broken。
- `tests/c7` は回していない。

## 問いへの意見

1. 日曜始まりと K9: **今の形でつなぎとして受入**(親案どおり)。ただし M1 を宣言に足し、腕の既定化か分析の前に「金曜に組む」か「月曜始まりの 8 日」を決める(印の外で組めない点を親に)。
2. 試験用の印の口: **腕の中だけで受入・広げない**(親案どおり)。L1 の欄だけ直す。
3. C3 の呼び数の分け方: **受入**。5,000 体で C1 の `c3:*` とカレンダー 3 の `sent:*` が一致・`calls_by_model.calendar_3` はカレンダー 3 の判断だけ=二重に数えていない。
4. シフトを組む人(本人が組む単位が多い): **宣言で受入**。ただし表は H1 を直してから。
5. 勤務の行は実行に結ばない: **受入**(`DOC-ca3-rows-not-executed`・外す段 6-2)。

## 親に確かめてほしいこと

- H1 の直しの後に、合成の再開(monkeypatch なし)と 5,000 体 2 日の再開で `calendar_3.roster` が通しと同じか。
- M1(組む刻みが 0:00・印の外では日曜が来ない)を問い 1 の判断に入れるか。
- ct_c1 §16 の腕 c1 の値 `b4bdb154…` は 4-2 の前の値。今の本体 HEAD は `2b9c9346…`(本段の作業木も同じ)。比べの基準を記録で更新するか。
- 取り込みで新しいファイルの index が LF か(L3)・`SWITCH_ENV` に 2 つ(L8)。
