# 第 6 期 6-2 カレンダー 3「雇い主・祝日」(C3 職場の連絡と束ねる・腕 `--calendar-3 arm`)の記録

- 実装役 Opus 5.5。作業木の枝 `6-2/calendar-3-employer-arm`(土台 `687f513`=本体の先端・本体の世界は W21)。commit は親。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-1(CA1「正規雇用は毎週固定、非正規とシフト勤務は
  週ごと(雇い主がエージェントになるまでのつなぎ)」「休むかどうかは本人の判断」「祝日を含むランは第 3 段まで回さない」・CA9・CA10・
  CA11)・§1-1 CP6 と §2 の 2(祝日は外からの決定=L0)・§4-4 CT1 の C3・CT2〜CT5・§1-5 の 55 件の ②(本段は**シフトを組んで知らせる**
  だけ)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) 6-2・6-6 ②・回答 2-1・
  [口の約束](../../../../design/v2-foundation-contracts-2026-10-13.md) 1-3・1-8・10-13b §0-3。先行の記録 [ca1b](../ca1b/README.md)・
  [ca2](../ca2/README.md)・[ct_c1](../ct_c1/README.md)・[pop43](../pop43/README.md) §5・[rules42](../rules42/README.md)。
- **全部 腕**(既定 off=層を作らない=今のまま)。検証の錨・封印した層は読んでいない。数は実測。生の出力は作業木の `_bc/`(git の外)。
  このフォルダには比べた結果と道具だけ(絶対パスなし)。道具 [tools/](tools/)。測った機械: Windows 11・x86-64(本体で段 0 の取得が
  並走=壁時計は参考)。

## 0. 結論

- 腕 `--calendar-3 {off,arm}`(環境変数 `SHIBUYA_CALENDAR_3`・既定 off)を足した。arm は **C1(`--contact c1`)とカレンダー 2
  (`--calendar-2 arm`)の層を再利用**する(どちらかが無いランは組み立てで `ValueError`)。
- **雇い主の口(つなぎ)**: 権利台帳の雇用の行(体 → 組織・外の雇用主の番号は除く・組織の無い体は店の担当の行の店)で単位を作り、
  単位ごとに「シフトを組む人」=担当のうち役割の語「店長」の最初の 1 人・居なければ最初の担当(ランの体の中で担当が本人だけなら本人)。
  W20 の `recurrence`=週ごと(非正規と交替制)の働く人だけを組む。**正規(毎週固定)は触らない**。
- **週 1 回**: 〔検収 M1・§12〕週の最後の平日(金曜)の頭に組む機会が始まり(試験用の印のランは土日始まりの 0 日目の頭にも)、雇い主は起きていて主の判断の無い最初の刻みに、翌週 7 日を日ごとに J0 の口で
  選ぶ(候補=休み+その人の W20 の約束の形の枠=始業〜終業。日の言葉は暦の常識の口=祝日の名つき)。労働時間の行(規則の表の human
  の行)と店の営業時間は**読むだけ**で、超えたら数える。
- **C3 職場の連絡**: シフトの知らせ・休みの申し出・返事・遅れの連絡は、どれも C1 の新しい口 `ContactLayer.workplace_send` を通る
  (手段と宛先=C1 の宛先の判断=相手にメッセージ/電話/職場のグループ・文=C1 の文の口・届くのは網)。読んだ(C1 の読む判断)か電話で
  聞いた働く人は、知らせの時刻を選んで**カレンダー 2 の器 `PromiseBook` に自分の行**を書く(種類「勤務」・置き場所=アプリ・
  確かさ=確定・元の会話=その連絡・誰と=雇い主)。休むかどうか・受ける/断る・自分の行を休みにするか・遅れると連絡するかは全部
  本人の判断(仮のモデル=一様)。
- **祝日**: 暦の口(内閣府の CSV)を読む問い合わせの口 `CommonCalendar`(全員が知る=CA11)と常識の文の 1 行。店の休業日は
  「店の決まり」の口=**枠だけ**(中身は空)。
- **既定 off で結果不変**: byte-check 19 構成 × 25 欄が土台 `687f513` の写しと全部同じ(19/19・[byte_check_ca3.json](byte_check_ca3.json))。
- **腕 arm(mock 5,000 体)**: 日曜 1 日・日曜 → 月曜 2 日・祝日を含む 2 日(日曜 → 海の日)が最後まで回る。監査の食い違いは
  カレンダー 3・C1・カレンダー 2 とも 0。記録 on/off で final と checkpoint 8 個の behavior-hash が同じ。日の境目の再開=通し
  (final と T≥1440 の checkpoint 24 個・manifest の計器 10 欄が同じ)。
- **日曜始まりの限界(親に確かめてほしい=§9)**: W17 は月曜の行しか無く(K9)、0 日目の日曜は体が全員範囲の外で待つ(主の判断の
  呼び 0)。日曜 → 月曜の 2 日は計画境界の表が変わるので、活動層のあるランは日の頭で止まる(K9 の張り直しの外)=2 日のランは
  **活動層を外して**回した。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/calendar3/__init__.py`(新) | 包みの説明 |
| `src/shibuya/engine/calendar3/arm.py`(新) | 腕の切替口・試験用の印の下の腕 `SHIBUYA_CALENDAR_3_TRIAL`・設定の指紋の組・状態台帳の腕の名 `calendar-3`・manifest の鍵 `calendar_3` |
| `src/shibuya/engine/calendar3/port.py`(新) | 判断の口 `Calendar3Port`(`DecisionPort` の子・用途名 `calendar3.mock`/`calendar3.present`)・判断の種類 7・候補の語・呼びの id(通し番号は 2^21 から=C1・カレンダー 2 とぶつからない) |
| `src/shibuya/engine/calendar3/roster.py`(新) | 雇い主の口の表 `Roster`(単位・シフトを組む人・週ごとの働く人・枠・店の担当の店・数)・`build_roster`・`roster_for_run`(母集団の無いランは空) |
| `src/shibuya/engine/calendar3/knowledge.py`(新) | 暦の常識の口 `CommonCalendar`(`ask`・`words`)・常識の文 `common_line`・店の決まりの口 `StoreRules.closed_days`(枠だけ) |
| `src/shibuya/engine/calendar3/layer.py`(新) | 持ち主 `Calendar3Layer`・系 `sys_calendar_3`・労働時間の行の読み `labor_params`・manifest の `calendar_3`・監査 `audit_causes` |
| 共有のファイル | §11 |
| `tests/engine/calendar3/`(新) | §10 |
| 記録 | 本書・[byte_check_ca3.json](byte_check_ca3.json)・[ca3_5000.json](ca3_5000.json)・道具 [tools/run_ca3.py](tools/run_ca3.py)・[tools/add_bridges_ca3.py](tools/add_bridges_ca3.py) |

## 2. 口の表(誰が)

| 口 | 置き場 | 中身 | 誰が |
|---|---|---|---|
| 雇い主の口の表 | `roster.build_roster`(組み立てで 1 回=導出) | 単位(組織か店)・シフトを組む人(店長 → 最初の担当 → 本人)・週ごとの働く人・枠(W20 の約束の形) | 構築(読むだけ・つなぎ) |
| 組む機会 | `_begin_compose`(〔検収 L2〕名を替えた) | 〔検収 M1〕金曜の頭(暦の曜日と刻みの番号だけ)に始まる・試験用の印のランは土日始まりの 0 日目の頭にも | エンジン(機会だけ) |
| その日の枠 | `_compose`(`P_FRAME`) | 翌週 7 日 × 週ごとの働く人=休みか枠のどれか | 雇い主(判断の口) |
| 雇い主の記録 | `_plan`・`_composed`(行 CA3S) | 組んだシフト・組んだ週・受けた休みを直す | 雇い主 |
| 労働時間の行・営業時間 | `_labor`・`_closed_check` | 週 40 時間・1 日 8 時間・毎週 1 回の休日(規則の表の human の行)・店の W7 の営業の表(祝日は PH の行) | 計器(止めない) |
| 店の決まり | `StoreRules.closed_days` | 休業日の知らせ(本段は空) | 組織の口(枠だけ) |
| 暦の常識 | `CommonCalendar.ask/words`・`common_line` | 日付・曜日・祝日の名(全員が知る) | 世界の常識(読むだけ) |
| C3 の連絡を送る | `ContactLayer.workplace_send`(C1) | 手段と宛先(相手にメッセージ/電話/職場のグループ)・文 | 送る本人(C1 の判断の口) |
| 届く | C1 の網(`_send_now`・着信) | 送った時刻に届く・電話は窓の境目で鳴る | エンジン(C1) |
| 送った/読んだの控え | `note_sent`(C1 の `sent_sink`=窓の境目)・`note_read`(C1 の `read_sink`=読む判断) | call_id → メッセージの番号・読んだ C3 の連絡 | エンジン(控えるだけ) |
| 電話で伝わる | `_poll_calls` | つながった通話で伝わる・つながらなければ 3 回まで送り直す | エンジン(C1 の通話の状態を読むだけ) |
| 書く | `_write_rows`(`P_NOTIFY`)→ `PromiseBook.write`(カレンダー 2 の器) | 勤務の日ごとに自分の行(アプリ・確定・元の会話・誰と=雇い主)・知らせの時刻 | 働く人 |
| 休みの申し出 | `_ask_rest`(`P_REST`・`P_REST_DAY`) | 申し出るか・どの日か → C3 の連絡 | 働く人 |
| 返事 | `_answer`(`P_ANSWER`) | 受ける/断る → 自分の記録を直す → 返事(電話の申し出は同じ通話で) | 雇い主 |
| 休みにする | `_apply`(`P_APPLY`)→ `PromiseBook.edit` | 自分の行の状態=取り消し(自分の行だけ) | 働く人 |
| 知らせ | `_agenda_step` → `勤務:知らせ`(原因=過程 calendar3) | 本人が選んだ時刻にアプリが鳴る | 道具 |
| 遅れの連絡 | `_late`(`P_LATE`) | 知らせの後に考えた刻みで勤め先のセルに居ないとき → C3 の連絡 | 働く人 |
| 計器 | manifest の `calendar_3` | §5 | — |
| 監査 | `audit_causes`・`issued_keys`(行 CA3Q) | 本人の語の原因=この層の発行した判断の呼び・道具の語=過程 calendar3 | — |

## 3. 流れ(日曜 → 月曜)

1. 〔検収 M1〕金曜の頭(日曜始まりの試験用のランは 0 日目の頭): シフトを組む人ごとに組む機会が始まる(`composed:begun`)。起きていて主の判断の無い最初の刻みに、受け持つ単位の働く人ごとに
   7 日の枠を選ぶ(出来事 `勤務:枠を決めた`=1 日 1 行・how_much=枠の長さ[分]・休みは 0)→ 労働時間と営業時間を数える → 働く人ごとに
   C3 の連絡(`workplace_send`=C1 の `連絡:送った`/`連絡:電話をかけた`)。本人しか居ない単位は連絡なしで本人が書く。
2. 届いたメッセージを C1 の読む判断で読んだ刻み(電話はつながった刻み): 働く人が知らせの時刻を選び勤務の行を書く(`勤務:書いた`)→
   休みを申し出るか → 申し出たら C3 の連絡 → 雇い主が読んだ刻みに受ける/断る → 返事 → 働く人が読んだ刻みに自分の行を休みにするか。
3. 月曜: 勤務の行の知らせ(本人が選んだ時刻)→ 次に考えた刻みに勤め先のセルに居なければ遅れると連絡するか。行は終わりの刻みに締めて
   器から落とす(有界)。
4. 送れなかった連絡(寝ている・電源が無い・通話中)は控え、次に考えた刻みに送り直す。控えた中身は 7 日で落とす。

仲裁: 雇い主の組む・送り直す・遅れの判断は、主の判断の呼びのあった刻みにはしない(次の刻み=C1・カレンダー 2 と同じ)。読んだ・
聞いたときの判断は読んだ刻みの中身(C1 の読む判断は主の判断の無い刻み)。

## 4. 既定 off の結果不変

- byte-check 19 構成(mock/classical 5,000 体・seed 1・1 シミュ日・テープつき)× 25 欄: 土台 `687f513` の写し(`git archive`+
  `HEAD_TREE_FILES`+data へのつなぎ=回した後に .NET で外した=`tree_missing` 空)と作業木の src で**全部同じ(19/19)**・呼数の合計
  1,106,861・両側の `env` 空・作業木の側は `src_is_worktree` 真=[byte_check_ca3.json](byte_check_ca3.json)(既定 v3 の final
  `bb86f89855172717`)。5,000 体のランは 1 本ずつ(`--jobs 1`)。
- 既定のランで動く欄(どれも 25 欄の外): `manifest_sections`(節の表=`calendar_3` と子)・`bridges_count`(つなぎの台帳 602 → 615)・
  `bridges_version`・日次の記録の `bridges_count`・出来事の記録の語彙の版(`events-vocab/6-2-ca3`)。既定のランの `calls_by_model` は今のまま。
- 腕 off のランでは層・系・C1 の控えの口(`sent_sink`・`read_sink`=None)・試験用の印のどれも動かない。開始日の検査は今のまま
  (試験用の印の無い日曜始まりは止まる=試験)。

## 5. 計器(腕 arm・mock 5,000 体・世界 v2(W21)・seed 1・試験用の印=分析に使わない・合否なし)

[ca3_5000.json](ca3_5000.json)(道具 [tools/run_ca3.py](tools/run_ca3.py))。どのランも `--contact c1`・`--calendar-2 arm` と束ねる。

| 計器 | 日曜 1 日(7/26) | 日曜 → 月曜 2 日(7/26〜27・活動層 off) | 祝日を含む 2 日(7/19〜20 海の日・活動層 off) |
|---|---|---|---|
| final(頭 16)・壁時計 | `c1acc2841723b33f`・19.2 秒 | `ba7d3b96f5cd527c`・133.6 秒 | `39528e65d7143fd2`・139.5 秒 |
| 主の判断の呼び | 0(0 日目の日曜は全員が範囲の外=§9) | 43,310 | 52,310 |
| 雇い主の口の表 | 単位 428(組織 420・店 8)・組む人の選び方 店長 4/最初の担当 153/本人 271 | 同じ | 同じ |
| 週ごとの働く人(組む/外の雇用主/勤め先なし)・毎週固定 | 1,124(544/381/199)・1,976 | 同じ | 同じ |
| 組んだ単位・働く人 | 428・544(週 1 回=始まった 428・0 日目の頭=試験用の印) | 同じ | 同じ |
| 1 人 1 週の勤務日数(2/3/4/5/6/7 日) | 3/27/65/170/176/103 | 同じ | 同じ |
| 1 単位 1 日の枠の人数(0/1/2/3 人以上) | 590/2,113/188/105 | 同じ | 同じ |
| 勤務の行(書いた・知らせ・締めた) | 2,136・0・0 | 2,715・281・376(休み 1) | 2,743・279・378 |
| 休みの申し出(申し出た/申し出ない/本人が組んだ) | 21/21/353 | 74/71/353 | 78/71/353 |
| 受けた/断った(受け入れの割合)・休みにした/そのまま | 4/1(0.80)・1/2 | 33/24(0.58)・11/16 | 33/26(0.56)・10/16 |
| C3 の連絡 送った(メッセージ/電話/グループ) | 52/54/56 | 133/147/142 | 134/141/143 |
| 内訳 シフトの知らせ/休みの申し出/返事/遅れ(送った・送り直しを含む) | 147/12/3/0 | 227/93/60/42 | 223/94/63/38 |
| 本人が組んだ知らせ(連絡なし) | 353 | 353 | 353 |
| 届いた(シフト/申し出/返事/遅れ)・グループでほかの人が読んだ | 395/5/4/0・49 | 498/57/49/21・299 | 502/59/48/20・310 |
| 電話 つながった/つながらなかった・あきらめた | 21/33・0 | 47/100・4 | 47/94・3 |
| 送れずに控えた(送り直し) | 53(0) | 64(2) | 66(3) |
| 遅れ 伝えた/このまま/勤め先に居た・セルなし/本人が組んだ | — | 32/44/7/181 | 29/45/14/178 |
| 労働時間の行を超えた(1 日 8 時間の日/週 40 時間の人/休日が足りない人) | 1,493/314/103 | 同じ | 同じ |
| 営業時間の外の枠/調べた枠(店の担当だけ) | 409/604 | 409/604 | 413/604(祝日は PH の行) |
| 祝日の日の枠(休み/勤務)・祝日の日の休みの申し出 | — | — | 119/425・12 |
| 暦の常識の口を引いた数・常識の文 | 3,110・「今日は 7 月 26 日(日)。」 | 3,410・「今日は 7 月 27 日(月)。」 | 3,434・「今日は 7 月 20 日(月・海の日)。」 |
| 判断の呼び(カレンダー 3)・C3 の送る判断と文(C1 の内訳に入る) | 4,274・162/108 | 4,685・422/275 | 4,696・418/277 |
| `calls_by_model` の判断モデル(C1/カレンダー 2/カレンダー 3) | 40,971(11,883/24,814/4,274) | 321,760(125,630/191,445/4,685) | 347,479(138,272/204,511/4,696) |
| 勤務の族の出来事・監査の食い違い(カレンダー 3/C1/カレンダー 2) | 5,971・0/0/0 | 6,978・0/0/0 | 7,006・0/0/0 |
| 出来事の記録の全体(行・行のバイト・原因の表のバイト) | 56,497・4.07 MB・1.74 MB | 260,936・18.8 MB・12.9 MB | 275,481・19.8 MB・13.9 MB |

- **数の読み方の注**: 仮のモデルは候補から一様に選ぶ(休み 1+枠 k 個から 1 つ=週の勤務日数は 7 × k/(k+1) の寄り)=数は振る舞いの
  モデルではない。1 日 8 時間を超える日が多いのは W20 の勤務の長さが 4〜12 時間(第 31/36 表の逆算=入力の写し)だから(記録だけ)。
  「本人が組んだ」単位が多い(428 のうち 271)のは 5,000 体の抽出で単位の担当がランに居ないから(抽出の形=§9)。
- 祝日のランの違い(来街者の行動は判断モデルの後=宣言): 祝日の日も雇い主は同じ候補から選ぶ(仮のモデルは祝日を読まない)=
  違いは営業時間の外の枠(409 → 413=祝日の PH の行)と祝日の日の枠の数え(休み 119/勤務 425)だけ。来街者の来訪・店の休業は本段に無い。
- 記録の量(カレンダー 3 の分): 勤務の族の出来事 6,978 行/2 日(行 1 つ約 72 B=約 0.5 MB)。C1 とカレンダー 2 と束ねた記録の全体
  (18.8+12.9 MB/2 日)の大半は C1 とカレンダー 2 の分。

## 6. 負の対照

| 確かめ | 対照 | 試験 |
|---|---|---|
| 本人の語の原因は判断の呼びだけ(AST) | `_log` の本人の語の原因=同じ関数の `self._decide` の答えだけ・道具の語=過程 calendar3。植えた 4 件(道具が書いた・偽の LlmCall の枠・判断が原因の知らせ・条件式の語に過程)を全部見つける | `test_ast_person_events_come_only_from_decisions`・`test_ast_negative_control_catches_planted_causes` |
| エンジンは時刻と中身を決めない(AST) | 帳面に事象を置くのは `_schedule_row` だけ・知らせの刻みは `notify_ns`/`written_ns` だけから・行の時刻の欄を作る辞書は `_write_rows` だけ(届いた中身=雇い主の選んだ枠から)・`_think` の値は刻み T だけ・組む機会を書くのは `_open_compose` と `_act` だけ・枠の番号は判断の答えの id からだけ。植えた 6 件を全部見つける | `test_ast_engine_does_not_decide_times_or_contents`・`test_ast_negative_control_catches_engine_rules` |
| 器は口だけで書く(AST) | 層の中にカレンダー 2 の器の行への直の代入が無い | `test_ast_book_is_written_only_through_its_ports` |
| 監査 | 種類の違う語・体の違う呼び・道具が原因の本人の語・判断が原因の道具の語・控えに無い呼び=5 件とも数える | `test_audit_catches_forged_and_engine_causes` |
| 段 B | 連絡の系の宣言から `CA3G:calendar3._reads` を外すと `AssertionError`(宣言の外) | `test_stage_b_negative_control_without_the_read_declaration_fails` |
| 既定は何も作らない | 腕 off=層なし・manifest の節なし・状態のファイルの `calendar3.*` なし・指紋の鍵なし・勤務の族の出来事 0・`calls_by_model` の内訳なし | `test_default_off_builds_nothing` |
| 腕の前提 | C1 かカレンダー 2 の無い arm は止まる・試験用の印の無い日曜始まりは今のまま止まる | `test_arm_needs_contact_and_calendar2`・`test_sunday_start_without_the_trial_mark_still_stops` |
| 腕の取り違えの再開は止まる | arm で書いた状態を off で再開=設定の指紋の `calendar_3` で止まる | `test_resuming_with_the_arm_off_stops` |

## 7. 2 日と再開(腕 arm・5,000 体・日曜 → 月曜・活動層 off)

| ラン | 通し final | 再開 final | 同じか |
|---|---|---|---|
| 2 日・日の境目 T=1440 で止めて再開 | `ba7d3b96…` | `ba7d3b96…` | final・T≥1440 の checkpoint 24 個の behavior/full・manifest の計器 10 欄(組んだ・勤務日数・休み・連絡・行・遅れ・労働時間・祝日・生きている控え・呼び数)が同じ |
| 記録 on/off(2 日) | `ba7d3b96…`(on) | `ba7d3b96…`(off) | final と checkpoint 8 個の behavior-hash が同じ(off の記録 0 行) |

- 合成(80 体・組織と雇用の行つき・2 日)の日の境目の再開=通し(`test_two_days_sunday_to_monday_and_resume_is_the_straight_run`)・
  記録 on/off(`test_event_log_on_off_does_not_change_the_arm_run`)。

## 8. manifest の節・設定の指紋・状態台帳の行・つなぎの台帳

- manifest の一番上の鍵 `calendar_3`(腕 arm のランだけ)。設定の子 9(`schema`・`arm`・`trial`・`port`・`compose`・`labor`・
  `arbitration`・`store_rules`・`provisional`)・観測の子 14(`meter`・`decisions`・`roster`・`composed`・`work_days_per_week`・`rest`・
  `contacts`・`rows`・`late`・`labor_over`・`holiday`・`common_knowledge`・`live`・`calls`)。設定の道筋 `CONFIG_PATHS_SHA256`
  `ceb58699…bcba7901` → `94fe399f…99682dea`(この 9 本を外すと前の値)。`calls_by_model` に内訳 `calendar_3`(manifest と日次の記録)。
- 設定の指紋に `calendar_3`(腕 arm のときだけ=`{"arm": "arm", "trial": "on|off"}`)。
- 状態台帳の腕の行(腕の名 `calendar-3`・持ち主の居るランだけ 2 つのハッシュと状態のファイルに入る=既定は不変・版は上げない):

| 行 | 道筋 | 軸 1 / 軸 2 |
|---|---|---|
| CA3S | `calendar3._composed`・`_plan`・`_compose_due` | behavior / required |
| CA3P | `calendar3._out`・`_msg`・`_calls`・`_wait`・`_agenda`・`_work_rows`・`_noticed`・`_next`・`_days` | behavior / required |
| CA3G | `calendar3._reads`(系の間)・`_think` | behavior / required |
| CA3M | `calendar3._c3_meter`・`_c3_hist`・`_c3_event_of`(休みの申し出の出来事の id=返事の判断の入力の目印=記録の有無で behavior が変わらない) | diag / required |
| CA3Q | `calendar3._c3_issued`・`_c3_issued_n` | diag / required |

- 外の状態 144 → 149 行・全体 235 → 240 行。働く人の行はカレンダー 2 の行 CA2B に入る(系 calendar_3 の宣言 `CA2B:calendar2.book.*`)。
  C1 の控えの口 `sent_sink`・`read_sink` は参照として除外。窓の境目の送信(`_send_now` → `note_sent`)が書く `CA3P:calendar3._out`・
  `_msg` は窓の境目の宣言 `WINDOW_PATHS_CA3`(腕のランだけ)。
- 出来事の記録の語彙: 族 `勤務` と 8 語(表の末尾=カレンダー 2 までの 93 語のコードは不変・93〜100)・道具の名 `calendar3`(末尾)・
  版 `events-vocab/6-2-ca3`。カレンダー 2 の行の種類 `KINDS` の末尾に「勤務」(前の番号は不変)。
- つなぎの台帳 13 行(`DOC-ca3-scheduler-pick`・`-frame-form`・`-port-candidates`・`-compose-opportunity`・`-labor-record-only`・
  `-store-closed-days-frame`・`-trial-mark`・`-weekend-k9`・`-resend`・`-request-opportunity`・`-row-form`・`-rows-not-executed`・
  `-not-default`=602 → 615 行)。道具 [tools/add_bridges_ca3.py](tools/add_bridges_ca3.py) は同じ id の行を置き換える(2 回回して同じ)。
- 乱数: 用途名 `calendar3.mock`・`calendar3.present`(動きの側=`MOTION_RNG_DOMAINS` の末尾)・`SAFE_SITES` 23 → 24・決まらない呼び手
  15 → 16。系の表: 刻みの系 28 → 29(`contact` → `calendar_3` → `calendar_2`)。

## 9. 限界と仮採用(親に確かめてほしいこと=問い)

1. **日曜始まりと K9**(問い): W17 は月曜の行しか無く、`w17_weekday` は 0 日目を暦の曜日のまま引く=日曜始まりの 0 日目は体が全員
   範囲の外で待つ(主の判断の呼び 0・C1 とカレンダー 2 の判断は範囲の外のまま動く)。そのため「週の境目の前の決まった刻み」は
   **日曜の頭**にし、組むのは起きていて主の判断の無い最初の刻みにした(主の判断の刻みに限ると日曜に誰も組めない)。日曜 → 月曜の
   2 日は計画境界の表が変わるので、活動層・方策 classical・想起優先の候補合成のあるランは日の頭の張り直しで止まる(K9 の外)=2 日の
   ランは活動層を外した(`DOC-ca3-weekend-k9`)。代わりの案: 月曜始まりで日曜を通る 8 日(K9 で日曜も月曜の行=活動層ありで回る・
   重い)。どちらにするか。
2. **試験用の印の口**(問い): 発注の日曜 → 月曜と祝日のランは開始日の検査(A1-1・A1-3)が止める。腕 arm の下の腕
   `SHIBUYA_CALENDAR_3_TRIAL=on` のランだけ規則の違反を止めずに manifest の `calendar_3.trial` に記録する口を `systems/build.py` に
   足した(止める違反は今のまま)。CA10 の「試験用(分析に使わない印)」の形としてこれでよいか(ほかの腕にも広げるか)。
3. **C3 の呼び数の内訳**(問い): C3 の連絡の送る判断(宛先と手段)と文は C1 の口=`calls_by_model.contact` に入る。`calendar_3` は本段の
   判断(雇い主の枠・働く人の書く/申し出る/休みにする/遅れ)だけ。C3 の分は manifest の `calendar_3.contacts.c1_judge_calls`・
   `c1_llm_calls` に別に出した(二重に数えない)。この分け方でよいか。
4. **シフトを組む人**: 店長の語の体が単位に居ることは少ない(5,000 体で 4 単位)・本人しか居ない単位が多い(271)。本人が組む単位は
   連絡・休みの申し出・遅れの連絡をしない(相手が無い)。抽出の形のつなぎ。
5. **勤務の行は実行に結ばない**(`DOC-ca3-rows-not-executed`): 出入りは今のまま(W17・腕 1b は W20)。勤務の行はカレンダー 2 の見える
   予定・出発の判断・重なりの警告の外(種類「勤務」で分けた)。1b の既定化と 6-6 ② で結ぶ。
6. **置き場所と確かさは固定**(発注どおり=アプリ・確定)。知らせの時刻だけ本人の判断(カレンダー 2 と同じ候補)。
7. 労働時間は休憩を除かずに数える・36 協定と変形労働時間制は入れていない・人数の上限は規則が無い=空欄(分布だけ記録)。
8. 店の休業日は枠だけ(中身は空)・祝日の日も仮のモデルは祝日を読まない(候補の文に祝日の名は出る)。
9. 電話の C3 の連絡は「つながった刻みに伝わる」(通話の番の中身は読まない)・電話の休みの申し出は同じ通話で返事。
10. 艦隊の経路(実 LLM)は通していない(mock だけ)=段 B は mock の道だけ。

## 10. 試験

新しい試験 `tests/engine/calendar3/`(共通 `_ca3.py`=腕の切替・合成の雇い主の口の表(組織=体の番号 // 10・奇数の体=週ごと・
25 番=店長)・グループの一覧・判断の差し替え):

- `test_ca3_units.py`(11): 雇い主の口の表(単位・店長 → 最初の担当・正規は触らない・枠の形・外の雇用主と勤め先なしは組まない・
  店の単位と本人が組む・表の無いランは空)・暦の常識(祝日の名・日の言葉・常識の文)・店の決まり(空)・労働時間の行(human・止めない)・
  呼びの id がぶつからない・仮のモデルの一様と決定論・カレンダー 2 の種類の末尾・監査の負の対照・腕の切替口。
- `test_ca3_runs.py`(25): 既定 off は何も作らない・腕の前提・試験用の印の無い日曜は止まる・雇い主が週 1 回だけ組む(正規は触らない・
  店長が組む)・勤務の行がカレンダー 2 の形・C3 の連絡が C1 の口を通る(監査 0)・労働時間は記録だけ・manifest の節と `calls_by_model`・
  休みの申し出 → 受ける → 休みにする(本人の判断)・断ったら行はそのまま・祝日の日付のラン(祝日の名が候補の文に出る)・2 日(日 → 月)と
  再開=通し・取り違えの再開は止まる・段 B と負の対照・記録 on/off・腕の行・系の宣言・CLI とランの種類・AST の 3 つと負の対照 2 つ。
- `test_ca3_world.py`(1・slow・data): 5,000 体の日曜 1 日(雇い主の口の表・組んだ数・監査 0)。

結果(作業木の src・本体の .venv・`-p no:cacheprovider -o addopts=""`):

- 範囲(`tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`):
  **4,179 passed・2 failed・0 errors**(57 分 27 秒)。落ちた 2 本はどちらも本段の未了で、直して単独で通した: つなぎの台帳の宣言の
  場所(本書がまだ無かった=本書を足した)・規則の表の読み手の一覧(`engine/calendar3/layer.py` を足した=`tests/engine/rules/` 31 passed)。
  → 直した後の範囲の結果は §10-1。
- `tests/engine/calendar3`(slow を除く): 36 passed。slow の 5,000 体: §10-1。
- lint-imports: 5 kept・0 broken。

### 10-1. 直した後

- 落ちた 2 本を直した後、`tests/engine/bridging tests/engine/rules tests/engine/calendar3 tests/engine/calendar2 tests/engine/contact`(`-n 2 --dist loadfile -m "not slow"`): **237 passed・0 failed・0 errors**(12 分 55 秒)。
- slow の 5,000 体 `tests/engine/calendar3/test_ca3_world.py`(1 本だけで): **1 passed**。
- 範囲の全体は直す前の 1 回(4,179 passed・2 failed)だけ=直したのは記録の追加と試験の一覧 1 行(src は同じ)。親の検収で全体を回し直す。
- 〔注〕直した後の再確認の 1 回目を slow を含めて走らせてしまい、途中で止めた(止めるまでに calendar2/contact の slow の 5,000 体が2 本並んだ可能性がある=発注の「1 本ずつ」に反した=数は使っていない)。

## 11. 触った共有ファイル(どれも末尾に足す形・腕のランだけ通る)

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/contact/layer.py` | 属性 `sent_sink`・`read_sink`(既定 None)・`_send_now` と `_read` に控えの呼び(腕のランだけ)・`_dial` の後半を `_place_call` に分けた(挙動は同じ)・新しい口 `workplace_send`(C3 の連絡) |
| `src/shibuya/engine/calendar2/book.py` | `KINDS` の末尾に「勤務」・`K_WORK` |
| `src/shibuya/engine/systems/table.py` | import 1 行・`contact` と `calendar_2` の間に系 `calendar_3`・contact の `paths` の末尾に `CA3G:calendar3._reads`・close_final の reads の末尾・docstring の段落 |
| `src/shibuya/engine/systems/conductor.py` | `WHEN` の末尾に `calendar3`・窓の境目の宣言 `WINDOW_PATHS_CA3`(腕のランだけ足す) |
| `src/shibuya/engine/systems/boxes.py` | `OWNER_NAMES` の末尾・`Layers` の末尾の欄 `calendar3` |
| `src/shibuya/engine/systems/state_io.py` | `hash_owners` の末尾と docstring・日次の記録の `calls_by_model` の内訳 `calendar_3` |
| `src/shibuya/engine/systems/run_end.py` | `calendar2_layer` の直後に `calendar3_layer` |
| `src/shibuya/engine/systems/build.py` | 設定の指紋(カレンダー 2 の直後・C1 とカレンダー 2 が無ければ止める)・開始日の検査(試験用の印のランだけ規則の違反を記録)・組み立て(カレンダー 2 の層の後=C1 に控えの口を挿す)・`Layers(calendar3=…)` |
| `src/shibuya/engine/run.py` | `_calls_by_model` に `calendar3`・`before3`・manifest の末尾(`calendar_2` の後)・補助 `_calendar3_field`・乱数の用途名の表の末尾 2 つ |
| `src/shibuya/engine/rng_audit.py` | `SAFE_SITES` の末尾 1 行・`UNDETERMINED_SITES` の末尾 1 行 |
| `src/shibuya/engine/manifest_sections.py` | `PATHS` の末尾(`calendar_2` の後) |
| `src/shibuya/engine/state_ledger.py` | `_EXT` の末尾(TXD の後)に 5 行・`OWNER_CLASSES` の末尾 1 項・`EXCLUDED` の末尾 6 項 |
| `src/shibuya/engine/events/vocab.py` | 族 `勤務`(`FAMILIES` の末尾)・8 語(表の末尾)・道具の名 `calendar3`(原因の名の末尾)・版・docstring |
| `src/shibuya/cli.py` | `run` のランの種類の腕の数え方の末尾・引数 `--calendar-3`(`--calendar-2` の後)・切替口 |
| `docs/design/bridging-ledger.json` | 末尾に 13 行 |
| 凍結の表の試験 | `tests/engine/systems/test_systems_table.py`(並び・刻みの系 29)・`writes_soa_frozen.json`(`calendar_3`)・`tests/engine/events/writes_paths_events.json`(contact の後に calendar_3)・`test_e_vocab_is_closed.py`(101 語)・`tests/engine/test_state_ledger_10b.py`(149・240・外の行と腕の行の並び)・`test_state_checks_10f.py`(`SAFE_SITES` 24・決まらない呼び手 16)・`test_env_and_sections_10f.py`(`CONFIG_PATHS_SHA256`)・語彙の末尾と版を固定していた 6 本(`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/tools/test_c0_tool_registry.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/engine/multiday/test_md23_body_events.py`)・`tests/engine/rules/test_rules_table_schema.py`(規則の表の読み手に `engine/calendar3/layer.py`) |

触っていない: カレンダー 2 の層(`calendar2/layer.py`)・C1 の判断の口と届き方(`contact/port.py`・`deliver.py`)・権利台帳・規則の表・
W20 の表・`manifest_keys_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`・10e の byte-check の道具(`SWITCH_ENV` に
`SHIBUYA_CALENDAR_3`・`SHIBUYA_CALENDAR_3_TRIAL` を足すのは親が本体で=カレンダー 2 と同じ)・用語集(足す語の候補: 雇い主の口・
シフトを組む人・勤務の枠・試験用の印・暦の常識の口=〔検収 L6〕「枠」は呼数枠ほかとぶつかる)。

## 12. 独立検収の直し(条件つき受入=高 1・中 1・低 9 → L8 のほかは全部直した・rebase はまだ)

検収の報告は [review.md](review.md)。直しの後の数はこの節が正(§0〜§11 は直す前の記録=数と形はこの節で上書きする)。scratch は
作業木の `_bc2/fix/`(git の外)。

### 12-1. 直しの表

| 欠陥 | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| H1 雇い主の口の表が再開で変わる | `calendar3/layer.py`(`ensure_roster`・`run_step`・`manifest`)・`calendar3/roster.py`(`w20_table_for_run`・`roster_for_run`)・`systems/build.py`・`state_ledger.py`(除外の `roster`・`sched_units`=CACHE) | 表と `sched_units` は組み立てでは作らず、最初の刻みの頭に作る(再開では状態を戻して権利台帳を作り直した `rebuild_derived` の後=通しと同じ台帳・同じ並びの単位)。W20 の週の表(世界の資産)だけ組み立てで読む(無ければ止める)。除外の理由を「導出=最初の刻みの頭に作り直す」に。道具 `run_ca3.py` の再開の比べに `roster` を足した | `test_roster_is_built_after_restore_and_resume_matches_without_monkeypatch`(表を差し替えない=合成の世界の開閉の過程の権利台帳から本物の道で作る・2 日・T=1440 の再開で表・`sched_units`・manifest の roster/composed/rest・final が通しと同じ)・`test_roster_is_not_built_at_assembly`・5,000 体の再開(§12-3) |
| M1 組む機会が日曜の頭だけ=印の外では組まない | `calendar3/layer.py`(`COMPOSE_WEEKDAY`=金曜・`_begin_compose`・manifest の `compose`・計器 `composed.hour_of_day`・`composed:weekday:*`) | 組む機会=**週の最後の平日(金曜)の頭**に始まり、起きていて主の判断の無い最初の刻みに翌週(次の月曜から)7 日を組む。試験用の印のランだけ、土日に始まるランの 0 日目の頭にも 1 回(金曜が来ない=宣言)。範囲の外の体は寝ていなければ起きている(宣言)。組んだ時刻[時]と曜日を計器に出す。台帳 `DOC-ca3-compose-opportunity`・`-weekend-k9` の文を直した | `test_compose_on_friday_without_the_trial_mark`(印なしの月曜始まり 5 日=金曜=4 日目に組み、翌週=7 日目)・`test_seven_days_with_the_trial_mark_compose_once_on_friday`(月曜始まり 7 日=金曜の 1 回だけ)・`test_employer_composes_once_a_week_for_weekly_workers_only`(日曜始まり=0 日目の 1 回) |
| L1 印のランの `calendar.start_check` が空 | `systems/build.py` | 違反を印つき(「試験用(分析に使わない): …」)で `start_check` に入れる(止めない) | `test_trial_run_fills_the_start_check_field` |
| L2 識別子の「open」 | `calendar3/layer.py`・AST の試験 | `_open_compose` → `_begin_compose`・manifest の `compose.opens_at` → `begins_at`・計器 `composed:opened` → `composed:begun`(設定の道筋の数は変わらない=`CONFIG_PATHS_SHA256` は同じ) | `test_ast_engine_does_not_decide_times_or_contents`(`_COMPOSE_OK`) |
| L3 新しいファイルの改行 | `calendar3/*.py`・`tests/engine/calendar3/*.py`・記録と道具 | 作業木のバイトで CR を数えた=どれも 0(LF)。検収の CRLF は Git Bash の grep の見え方と推測(index の LF は取り込みで親が確かめる) | — |
| L4 カレンダー 2 の `live_rows` が勤務の行を数える | `calendar2/layer.py`(manifest) | `live_rows.rows`=勤務の行の外・`live_rows.work_rows`=勤務の行(腕 --calendar-3 arm のランだけ 0 でない)。カレンダー 2 の仲裁が勤務の行だけの体も「考えた」に入れる点は宣言(`_look` は勤務を見ない=判断は出ない) | 既存の試験 |
| L5 rules42 の表の読み手 | `rules42/README.md` §2 | `labor.statutory_hours` の読み手に `engine.calendar3.layer.labor_params`(計器=読むだけ・腕のランだけ) | — |
| L6 用語集の「枠」 | 本書 §11 | 足す語の候補を「勤務の枠」に(用語集そのものは親が足す) | — |
| L7 C1 だけで控えの口が None | 試験 | C1 あり・カレンダー 3 なしで `sent_sink`・`read_sink` が None・窓の境目の宣言に `CA3P:calendar3._out` が入らない(arm では入る) | `test_contact_without_calendar3_has_no_sinks_and_no_window_paths` |
| L8 `SWITCH_ENV` | 10e の道具 | 親の仕事(触っていない) | — |
| L9 試験の件数 | §10 | §12-4 に直した後の数 | — |

### 12-2. 組む機会の新旧と計器の新旧

| ラン | 前(日曜の頭) | 後(金曜の頭・印の土日始まりは 0 日目) |
|---|---|---|
| 5,000 体 日曜 → 月曜 2 日(印) | 0 日目の頭に 428 単位・544 人(全部 0 時) | 同じ=`begun_on_trial_day0` 1 回・428 単位・544 人・`hour_of_day` {0: 428}・final `ba7d3b96…`(前と同じ) |
| 5,000 体 祝日を含む 2 日(印) | 428・544 | 同じ・final `39528e65…`(前と同じ) |
| 5,000 体 日曜 1 日(印) | 428・544 | 同じ・final `c1acc284…`(前と同じ) |
| 合成 80 体 月曜始まり 5 日(印なし) | 組まない(日曜が来ない) | 金曜(4 日目)に 8 単位・40 人・翌週=7 日目・組んだ時刻 0/2/6/7 時(3/1/3/1 単位) |
| 合成 80 体 月曜始まり 7 日(印) | 日曜に組む | 金曜の 1 回だけ(8 単位・40 人)・0 日目の組む機会なし |

- 日曜始まりの 5,000 体のランは 0 日目の頭に組む(全員が範囲の外で寝ていない=0 時に寄る)ので、計器の数は前と同じ(§5 の表のまま)。
- **新しく見つけたこと(問い)**: 合成の月曜始まり 7 日・5 日では、金曜に組んだシフトの知らせが**全部送れなかった**(控え 39・送り直し
  299・C1 の計器 `c3:cannot_send:device_off` 338・金曜には 80 体全員の電池が 0)。C1 は充電が無い(C1 の記録の限界)ので、4 日を
  超えるランでは C3 の連絡が C1 の口を通れない。本段では直していない(C1 の範囲=充電は本人の行動か道具の性質)。

### 12-3. 再開の一致(roster を含む・5,000 体・日曜 → 月曜 2 日・活動層 off・印 on)

[ca3_5000_fix.json](ca3_5000_fix.json)。T=1440 で止めて再開: final `ba7d3b96…` が通しと同じ・T≥1440 の checkpoint 24 個の behavior/full が
同じ・manifest の `calendar_3` の 11 欄(**roster**・composed・勤務日数・休み・連絡・行・遅れ・労働時間・祝日・生きている控え・呼び数)が
同じ(検収の再開では roster が 428 → 420 単位にずれていた=直った)。

### 12-4. 既定 off の 4 構成と試験(直した後)

- 既定 off の 4 構成(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`): 本体 `71c53bd` の写し(`git archive`+
  `HEAD_TREE_FILES`+data へのつなぎ=回した後に .NET で外した)と作業木の src で **4/4 構成 × 25 欄 同じ**(final `bb86f898…`・`3cdf9dbf…`・
  `8fca095b…`・`94becde2…`・`tree_missing` 空・`env` 空・作業木の側は `src_is_worktree` 真)=[byte_check_ca3_fix_4cfg.json](byte_check_ca3_fix_4cfg.json)。
- 範囲(`tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`):
  **4,187 passed・1 skipped・0 failed・0 errors**(47 分 0 秒・直した後の作業木=新しい試験 6 本を含む)。
- slow の world `tests/engine/calendar3/test_ca3_world.py`(1 本だけで): 1 passed。lint-imports: 5 kept・0 broken。
- 段 B は合成の 2 本(宣言の外 0・`CA3G` を外すと落ちる)=範囲の試験の中。

## 13. 親の判断(問い 1〜5)

1. 日曜始まりと K9: 今の形(起きていて主の判断の無い最初の刻みに組む)+ M1 の直し(金曜の頭)を**つなぎとして受入**(台帳
   `DOC-ca3-compose-opportunity`・`-weekend-k9`)。
2. 試験用の印の口: **腕の中だけ**(ほかの腕に広げない)・L1 の直しつき・印なしの日曜始まりは止まる(負の対照
   `test_sunday_start_without_the_trial_mark_still_stops`)。
3. C3 の呼び数の分け方: **受入**。
4. 本人が組む単位が多い: **宣言**(H1 の直しの後の数=単位 428・本人 271・最初の担当 153・店長 4=前と同じ・再開でも同じ)。
5. 勤務の行は実行に結ばない: **受入**。
- ct_c1 §16 の参照値(`b4bdb154…`)は 4-2 の前の値=本段では触らない(親が別に注を入れる)。

## 14. C1 の家での充電のつなぎ(親の発注=§12-2 で見つけた「4 日を超えると電池 0 で知らせが送れない」)

決定 10-12 §2 の 2「まだ人の行動で作れない変化はエンジン規則でつなぐ(conf 宣言つき)」の形。充電が本人の行動になるまで(判断
モデルの段 6-6)のつなぎ `BR-CT1-CHARGE-AT-HOME`(expedient・外す段 6-6・つなぎの台帳 615 → 616 行)。

| 箇所 | 中身 |
|---|---|
| `contact/device.py` | `CHARGE_PER_HOUR`=0.5/時(満充電まで 2 時間相当=仮の値)・`Devices.charge(at_home, 刻みの秒)`=家に居る体だけ電池が増える(満充電で止まる)・電池が 0 でなくなった体は電源が入る(充電中に電源が入る=宣言)・計器 `summary().battery_zero` |
| `contact/deliver.py` | `Mailbox.release_held`=電源が入った体に網が預かっていたメッセージを届ける(届いた時刻=その刻み) |
| `contact/layer.py` | 引数 `home_cell`(既定 None=充電なし)・系 contact の物理の段(電池の減りの直後)に `_charge_at_home`=家に居る=住まいのセルに居る(範囲の中)か、住まいが範囲の外の体が範囲の外で寝ている刻み(住まいの場所が無い=宣言)・職場では増えない・預かりを届けたら出来事 `連絡:届いた`(原因 過程 contact)と未読の目印・計器 `charge:agent_steps`・`charge:power_on`・`held_released`・manifest の `device.charge_per_hour` |
| `systems/build.py` | C1 の層に `home_cell=schedule.home_cell`(腕 c1 のランだけ=既定 off は層を作らない) |
| `state_ledger.py` | 除外に `contact.home_cell`(設定=組み立てが 1 回だけ置く)。電池は今の行 CT1D のまま |

- 既存のつなぎの行 `DOC-ct-c1-no-charging`(C1 の記録=「充電が無い」)は触っていない=新しい行と食い違う(親の判断=§15 の問い)。
- **合成 80 体・月曜始まり 7 日(試験用の印)**: 充電の前=金曜に 80 体全員が電池 0・シフトの知らせの控え 39・送り直し 299・
  `c3:cannot_send:device_off` 338・書いた行 7 → 充電の後=電池 0 の体 0・電源の切れた体 0・`device_off` 0・控えに残る 0・知らせ
  届いた 38・書いた行 207・休みの申し出 21(受けた 6/断った 15)。
- **腕 c1 だけの 5,000 体 1 日**: final `2b9c9346…`(検収の値=本体 71c53bd と同じ)→ `59930cf3…`(充電で電池が変わる=腕の中だけ)・
  電池 0 の体 24(電源の切れた体 24)・充電した体の延べ 444,411 体 × 刻み・預かり 1,089。
- **カレンダー 3 の 5,000 体**(試験用の印): 日曜 1 日の final は同じ `c1acc284…`(0 日目の日曜は全員が範囲の外で寝ていない=誰も
  充電しない)・日曜 → 月曜 2 日 `ba7d3b96…` → `581f6169…`・祝日の 2 日 `39528e65…` → `ee14897a…`。カレンダー 3 の計器(組んだ 428/544・
  申し出 74/78・受けた/断った・送った 422/418・控え 64/66・行 2,715/2,743・遅れ 32/29)は前と同じ・監査の食い違い 0(3 つとも)・
  T=1440 の再開は final・checkpoint 24 個・manifest の 11 欄(roster を含む)が通しと同じ=[ca3_5000_fix.json](ca3_5000_fix.json)。
- 試験: `tests/engine/contact/test_c1_charge.py`(新 2=家でだけ増える・満充電で止まる・電源が入る・預かりが届く)・
  `test_seven_days_with_the_trial_mark_compose_once_on_friday` に「電池 0 の体 0・`device_off` 0・控えに残る 0・知らせが届いて行を書く」。

## 15. 親に確かめてほしいこと(充電のつなぎの後)

1. つなぎの台帳の `DOC-ct-c1-no-charging`(C1 の記録の行・外す段 6-4)を `BR-CT1-CHARGE-AT-HOME` に置き換わった印にするか(本段は触って
   いない)。ct_c1 の記録への注も親の側。
2. 住まいが範囲の外の体は「範囲の外で寝ている刻み」を家とした(住まいの場所が無い)。この当てはめでよいか。

## 16. 試験(充電のつなぎの後=§12-4 の数を上書き)

- 範囲(`tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`=`tests/engine/contact` を含む・`-n 2 --dist loadfile
  -m "not slow"`): **4,189 passed・1 skipped・0 failed・0 errors**(53 分 29 秒)。
- slow の world `tests/engine/calendar3/test_ca3_world.py`(1 本だけで): 1 passed。lint-imports: 5 kept・0 broken。
- 既定 off の 4 構成(本体 `71c53bd` の写し vs 充電の後の作業木の src): **4/4 構成 × 25 欄 同じ**(final `bb86f898…`・`3cdf9dbf…`・`8fca095b…`・
  `94becde2…`・`tree_missing` 空・`env` 空・`src_is_worktree` 真)=[byte_check_ca3_fix_4cfg.json](byte_check_ca3_fix_4cfg.json)(充電の後に上書き)。

## §親の検収(第337・2026-10-22・Fable 5.1)

- **実在と差分**: 作業木の 53 本(src 17・tests 15+新規 2 組・docs 3・台帳)を親がディスクで確かめ、明示の一覧で stage(`commit_check` 一覧 53=ステージ 53・秘密スキャン CLEAN・絶対パスと個人名 0・CR 0・新しい識別子に `open`/`tick` 0)。親 commit 25f4b16 → 本体 f27377a へ rebase(衝突なし)=`c378eff`。
- **親の判断(§15)**: 問い 1=`DOC-ct-c1-no-charging` を **removed** にした(台帳 616 行・active 593 → 592・`why` に置き換えの注・ct_c1 README §12 の仮採用 1 に注)。問い 2=住まいが範囲の外の体の「家」=範囲の外で寝ている刻み、は台帳の行の宣言のまま受入(住まいの場所が無い体の扱いは第 5 期 段 7 の外の人の層で見直す)。
- **既定 off の byte-check(親・4 構成)**: 本体 f27377a の src の写しと作業木 c378eff の src で `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` の 25 欄が全部同じ(差の欄 0/4 構成・[byte_check_ca3_parent_4cfg.json](byte_check_ca3_parent_4cfg.json))。
- **範囲の試験(親・-n 4・not slow)**: `tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`=**4,189 passed・1 skipped・0 failed・0 errors**(25 分 11 秒)。台帳の試験(`tests/engine/bridging`+c8 の感度)は removed の後で 91 passed。
- **data 無しの写しの全体試験(CI-1 と同じ印・c378eff)**: **5,721 passed・290 skipped(data 無し)・0 failed・0 errors**(27 分 22 秒・faulthandler 900 秒の門に当たらず)。
- **読んだ所**: `calendar3/roster.py`(表は組み立てで作らず最初の刻みの頭=復元の後)・`calendar3/layer.py`(`_begin_compose`=金曜の頭・起きていて主の判断が無い最初の刻み)・`contact/device.py`(`Devices.charge`=家に居る刻みに 0.5/時・職場では増えない)・`contact/deliver.py`(`release_held`)・`systems/build.py`(試験用の印の口は腕 arm のときだけ)。
- **残り(親)**: `SWITCH_ENV` に `SHIBUYA_CALENDAR_3`/`_TRIAL`(本体の docs の commit で)・用語集に 5 語・ct_c1 §16 の参照値の注(4-2 の後 `2b9c9346…`・充電のつなぎの後 `59930cf3…`=腕 c1 だけの 5,000 体 1 日)。5,000 体の段 B は本段では回していない(合成の段 B は範囲の試験の中)。
