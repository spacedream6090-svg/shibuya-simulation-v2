# 評価 D の仕分け(テスト・品質・ドキュメント・開発の進め方)

> 第332・検証役(Opus 5.5)・2026-10-13。作業の途中で HEAD は `9c86846`(文書だけの commit)に進んだが、数えと試験は `82c2ed5` で行った。対象は [外部の評価](../external-review-2026-10-13.md) の「## 評価 D」。HEAD は `82c2ed5`(枝 `build/spatial-d102-prep`)。本体のコードと docs は変えていない。試験は data の無い作業木(`git worktree add <tmp> HEAD`・data のつなぎ=junction なし)で回し、終わったら作業木を消した。評価の「直す順の提案」は実行していない(第332 のユーザー指示)。
> 仕分け: **(a)** 事実が正しく計画で扱っている / **(b)** 事実が正しく計画に無い / **(c)** 事実が違う・古い / **(d)** 提案が決定と食い違う。「—」は良い点の指摘で対応が要らないもの。
> 手元の環境: Windows 11・Python 3.12.10・numpy 2.5.3・numba 0.67.0・scipy なし・pytest-xdist なし・直列。評価者は Linux・Python 3.13・2 コア。

## §0 結論

- **CI は 10-07 から 17 回の push(34 本のラン)続けて赤**(gh で確認=評価者の「推測」は事実)。最初の赤は第325(10f 第 1 段・`74d6da8`・10-07 03:50 JST)の golden の環境の assert で、10e の暦の実日(第330 ACT)で 300 件超に増えた。PENDING・STATUS・IMPLEMENTED・devlog のどこにも CI が赤だという記録は無い。
- **data の無い作業木では 313 failed / 68 errors / 3,394 passed / 195 skipped(213 秒)**。落ちた 381 件のうち **380 件は祝日の表が無いこと**が原因(開始日の検査 `engine/calendar.py:410` の文言で止まる 369 件+系の検査の試験が同じ所で止まる 10 件+CSV を直接開く 1 件)。残り 1 件は P6 の時間門(slow・2.125 ms > 2 ms)。
- **祝日 CSV 1 本(21,538 B)を置くだけで**、data の無い作業木は **1 failed / 3,776 passed / 193 skipped(1,018 秒・直列)** になった(§2-1)。残った 1 件 `tests/engine/test_calendar_10e_e3.py::test_e3_two_days_advance_on_the_calendar_and_the_weekday_rows_come_from_it` は世界資産を読むのに `@needs_world` の印が無い試験(祝日の表で先に止まっていたので隠れていた)。CI と同じ選び方(not slow)では 1 failed / 3,764 passed / 170 skipped。内閣府の CSV は公共データ利用規約 第 1.0 版(PDL1.0・CC BY 4.0 と互換・商用可・出典の記載が条件)なので、リポに入れて配れる(§2-3 (i))。
- **作業木の新しい穴**: 共有の venv は本体を editable で入れているので、作業木の試験が起こす子プロセス(6 ファイル)は **`PYTHONPATH` を付けないと本体の `src` を import する**(作業木のコードを試していないのに通る)。評価の「editable 前提」より重い。作業木で並べる前に塞ぐ(§2-4)。
- 評価の環境依存の 4 件(scipy の t 分位・ホスト名の部分一致・golden の platform・P6)は**全部コードで確かめて正しい**。golden の platform の assert(`test_env_and_sections_10f.py:295`)は K26 (1)「未登録の環境は A/A だけ・fail にしない」と食い違う試験の欠陥。
- 文書の量の数字は**バイトを「字」と書いている**(docs の Markdown 1,480 万は 14.85 MB=860 万字・src 410 万は 4.10 MB=335 万字)。比 3.6 はバイトで成り立ち、字では 2.6。README の内部語が多いという指摘は README には当たらない(D-xx・K2・つなぎ・版上げ・10e は 0 回)。src には当たる。
- 評価の「W17 の来街者の時刻形状は第 4 期で直す」は計画の読み違い: 決定では W17 は凍結(10-12 §4-1 CA1)・来街者の来訪を本人へ移すのは「判断モデルの後」(CA9)=第 6 期の側。前倒しの提案は CA1・CA9・§0-3 の 3(つなぎを溜めない)と食い違う(d)。測るだけなら食い違わない(b)。
- **決定の写し**: 開始日 2026-07-13 は 6 文書+コード、1-0 の切り方は 7 文書に書き写されている。決定台帳 `v2-redesign.md` §9 には 3 つとも無い(§9 の行は 09-08 までが中心で、10-03 以降の決定は指示書・回答の原文が「正」として働いている)。親推奨は §3 の **案 B(正=ユーザーの原文・他は全体で一意の ID で参照)**。

## §1 表(評価 D の指摘ごと)

| # | 評価の指摘(要約) | 確かめた事実(根拠) | 仕分け | 計画・決定の対応 |
|---|---|---|---|---|
| 1-1 | 収集 3,945・`def test_` 3,190・README の 2,298 は古い | `def test_` 3,190 本(208 ファイル)。収集は手元 3,970(評価者と環境が違う)。README.md:32 に「2,298 本」 | (b) | README の更新は計画に無い |
| 1-2 | import-linter 5 契約 KEPT | 作業木で `lint-imports` 5 kept / 0 broken | — | — |
| 1-3 | そのまま回すと 317 failed / 68 errors。362 件が `calendar.py:410` で止まる | 手元 313 failed / 68 errors / 3,394 passed / 195 skipped。381 件中 380 件が祝日の表(§2-1 の表) | (b) | 計画 §1-11 の段 3(夜の全体試験)は data のある手元が前提。clean checkout は扱っていない |
| 1-4 | CI は赤の見込み(推測) | **事実**。`gh run list`: 10-06 14:55Z の `8c8a77c` が最後の緑、`74d6da8`(第325)から 34 ラン連続で赤。最初の原因は golden の platform の assert(1 件)と旧 pickle の試験が祝日 CSV を開く 1 件、第330 ACT 後は 304 failed / 68 errors(`82c2ed5` の CI) | (b)・一部 (c) | 評価は原因を 10e からとするが、赤は 10f 第 1 段から。記録に CI の状態は無い |
| 1-5a | `tests/c7/test_prereg_v13.py:186` は scipy があれば必ず落ちる | 正しい。`tools/c7/seed_ensemble.py:50` は scipy の ppf を優先し、:186 は表の 9.925 と rel=1e-9 で比べる。CI と手元は scipy なしなので通る | (b) | pip は 10-12 §6 で「試験に要るパッケージ・版を固定」で許可済み |
| 1-5b | `test_env_and_sections_10f.py:92` のホスト名の部分一致 | 正しい。`assert node not in json.dumps(...)`=ホスト名「vm」は llvmlite に当たる | (b) | — |
| 1-5c | `:295` は golden の platform が登録済みであることを要求 | 正しい(:295 の assert)。`tests/golden_env.py` の約束(未登録は A/A だけ・fail にしない=K26 (1))と食い違う試験の欠陥 | (b) | K26 (1)(10f アジェンダ §6-1)に合わせて直す |
| 1-5d | P6 の時間門(4.08 ms > 2 ms) | 正しい。`test_change_detect_p6.py:205`(slow)。手元では回 2 で 2.125 ms で落ち、回 3 では通った(負荷で揺れる)。CI は slow を外すので CI の赤の原因ではない | (b) | 10-03 ⑥ 6-5「性能のテストを毎晩の自動検査に」は決定済みで未実装 |
| 1-6 | subprocess が `shibuya` を import できない 3 件(editable 前提) | 正しい(CI は `pip install -e` なので通る)。**手元の作業木ではもっと悪い**: 子は本体の `src` を import する(§2-4) | (b) | 計画 §1-10(作業木)に import の先の約束が無い |
| 1-7 | 自作 CSV の md5 の違い 1 件・原因不明 2 件 | 再現していない(本物の CSV で回した)。§5 空欄 | 空欄 | — |
| 1-8 | 遅い試験は CI の timeout 30 分に近い(推測) | slow は CI で外している。ただ **slow を外した段だけで 17 分(10-06・緑)・24 分(10-11)** かかっていた | (b) | 計画 §1-11 の段 3 は「xdist などの効き目を測って採用」=手元の話 |
| 1-9 | data に触る試験 113 ファイル・skipif 66・未登録の環境は A/A だけ=CI は golden を守らない | data が無いと落ちるか飛ぶ試験ファイル 108(実測)・`skipif` 67 か所(49 ファイル)・`pytest.skip(` 30 か所。A/A は `tests/golden_env.py:9-13` のとおり | 数は概ね正しい。golden は (a) の設計どおり+(b) | K26 (1) が「未登録は A/A」を決めている。CI の行を足すのは K26 (1) の「行を人が見て足す」の範囲で、計画には無い |
| 2-1 | 結果不変の網が厚い・AST の試験 18 ファイル 282 本・systems 54 本 | 18 ファイル・282 本・`tests/engine/systems/` 5 ファイル 54 本 | — | — |
| 2-2 | 振る舞いの単体試験は錨を固定するだけで街全体の合否ではない | 正しい | (a) | 判定関数は 10-03 ⑥ 6-2「作れるものから今すぐ」・計器は 3-1 の CA8(診断だけ)・合否は第 7 期 |
| 2-3 | holdout の外れを改善の方向に縛る試験は無い | 正しい | (d) | holdout を試験で縛るのは「較正が holdout に触れない」(CLAUDE.md §4)と事前登録(第 7 期)に反する |
| 2-4 | golden の 16 進を直書きしたファイル 30 本・版上げごとに張り替え(第330 で 6 定数) | 30 ファイル・95 個。IMPLEMENTED #88 に「golden 6 定数」 | (a) | 計画 §1-2「動く段の門」=golden の張り替え+動いた量の記録+計器の値 |
| 3-1 | docs 1,328 ファイル・Markdown 1,480 万字・research 722 万・design 322 万・bench 849(345 万)・src 410 万=文書は src の 3.6 倍 | ファイル数は正しい。**数はバイト**(§4)。字で数えると docs の Markdown 860 万字・src 335 万字で比は 2.6。bench の 345 万は Markdown 172 本だけのバイト(bench 全体は JSON 518 本を含め 28.8 MB) | (c) 単位 | — |
| 3-2 | IMPLEMENTED 215 KB(1 行最大 2,498 字)・PENDING 20 KB・旧 PENDING 207 KB・CLAUDE.md 21 KB・決定台帳 146 KB(§9 約 105 行)・壁打ちの文書 93 万字 | KB は正しい。1 行最大 2,498 は**バイト**(1,519 字)。§9 の表は 105 行。壁打ち・回答・決定の 20 本で 89 万バイト | 概ね正しい・(c) 単位 | — |
| 3-3 | 答申 176 本のうち未参照 26 本・D 等級 33 本 | 答申 174 本+索引 2 本=176。design・src・tools・トップから未参照は 26 本(正しい)。ただし 24 本は bench か他の答申から参照され、どこからも参照されないのは 2 本。D 等級 33 本は INDEX §5 のとおり(INDEX:314「D なら使わない(その数値だけ一次確認してから使う)」) | 正しい | — |
| 3-4 | 09-22 以降 147 commit・docs/bench 48.3 万行・src 3.2 万・research 3.1 万・tests 2.2 万・件名の 6 割は答申ほか | 148 commit(JST 09-22 0 時から)・行数は一致。src と tests に触れない commit は 79/148=53% | 概ね正しい(6 割はやや多い) | — |
| 3-5 | 決定 1 件が 6〜8 か所に写されている。STATUS の 10-14 と README の数字はその遅れ | §3 の数え: 開始日=6 文書+コード・1-0 の切り方=7 文書・W17 の凍結=5 文書。STATUS.md:3・:13 の「2026-10-14」は `82c2ed5`(10-13 13:08 JST)で書かれた=commit より先の日付(devlog の見出しも「10-13〜14」)。README の「完了 40 項」(:16)は IMPLEMENTED #89 まで | (b) | 計画に写しを減らす段は無い。CLAUDE.md §5 の写し検査は写しを前提にした検査 |
| 3-6 | PENDING §1 は 6 件・§1-4 の手作業が約 15 件。§2-2 と §7 の逐条が問いを増やす | §1-1 の表 6 行・§1-4 は 7 項(中に約 15 件) | 事実は正しい・(d) | §2-2(09-01 ユーザー指示)と §7 の許可の一覧はユーザーの決定。回答 10-12b §6-6「戻せる判断は止めない」で一部は手当て済み |
| 4-1 | README は良い入口 | — | — | — |
| 4-2 | README の背骨の 1 行が古い | README.md:11 は旧文。CLAUDE.md §3 は K2(10-12 §2 の 1)で改訂済み | (b) | 10-12 §2 の改訂先に README が入っていない |
| 4-3 | 「次にやること」が計画と合わない | README.md:121〜126(判断層・記憶・複数日と再開・事前登録 v2)。再開(`resume == straight`)は 10d で済み。第 1〜7 期の順は無い | (b) | — |
| 4-4 | 開発の手順が PowerShell 前提・Linux では祝日 CSV が無いと動かない | README.md:145 が ```powershell。CSV が無いと止まるのは OS に関係なく同じ | (b) | — |
| 4-5 | 本文に内部語が多い・`run.py` の docstring も同じ・用語集 2.8 万字 | README の本文は D-xx 0・K2 0・つなぎ 0・版上げ 0・10e 0・第 N 3・腕 1。`engine/run.py` は D-xx 134・腕 63・第 N 63(docstring の冒頭は少ない)。用語集は 27,748 バイト=14,186 字 | README は (c)・src は (b) | — |
| 4-6 | 顧客に何を出せるかの頁が無い | 確かめていない(D の範囲の外) | 空欄 | — |
| 5-1 | MockLLM は語彙から決定論で抽選するだけ | `llm/mock.py` の docstring のとおり(「振る舞いのモデルではなく配管」) | — | — |
| 5-2 | 10e の実日の暦・天気・時刻表は本物の前進 | — | (a) | 第 0 期・2-3b |
| 5-3 | presence-shape README:90 の主因の推定=W17 の来街者の時刻形状。直すのは第 4 期 | :90 の文は正しい(「推定のまま・判定はしない」)。**直す段は第 4 期ではない**: W17 は凍結(10-12 §4-1 CA1)・来街者の来訪は「判断モデルの後」(CA9)・3-1 カレンダー 1a は勤務と授業だけ・第 4 期は人数と属性 | (c) | CA1・CA9・計画 6-2 |
| 5-4 | mock でも測れるのに 09-29 以降扱っていない・10-12 以降は合否の数字が動いていない | 正しい。計画に「ピーク時刻・来街者の比を毎回測る」段は無い(3-1 の CA8 の計器は勤務と通学) | (b) | 10-03 ⑥ 6-2 の判定関数の決定と近い |
| 6 | 同分野との比較 | 確かめていない(意見) | — | — |
| 7-1 | **CI を緑に・第三者が再現できる形に**(祝日 CSV・golden の CI の行・環境依存 4 件・実データの縮小版) | 上の 1-3〜1-9 | (b)。縮小版のうち KDDI・PT・ODPT チャレンジ枠は (d) | KDDI は holdout(封印)・PT は申請・ODPT チャレンジ枠は再配布しない(CLAUDE.md §7・回答 10-13 の 3)。§2-3 |
| 7-2 | **「現実との差」を測る mock の回帰試験を 1 本常設**(在圏のピーク時刻・来街者比・エリア JSD を毎回記録・較正側のアンカーで)。W17 の時刻形状の修正を前倒しする材料に | 測ること自体は (b)。前倒しは (d) | (b)/(d) | 毎晩の自動検査(10-03 ⑥ 6-5)・判定関数(6-2)は決定済みで、計画の段と CI に無い。W17 の修正の前倒しは CA1(凍結)・CA9(来街者は判断モデルの後)・§0-3 の 3 と食い違う |
| 7-3 | **記録を一元化**(決定は決定台帳 1 か所・他は ID リンク・IMPLEMENTED は 1 項 2〜3 行・README を版上げごとに更新・判断待ちと手作業を週 1 回まとめる) | §3 | 決定台帳 1 か所は (d)・IMPLEMENTED と README は (b)・週 1 回は一部 (a) | 指示書と回答は原文のまま保存して「正」(10-03 §0 の 2・計画の冒頭「回答が正」)。§6 の記録プロトコルは PENDING だけ 5 節の形を決めている。戻せる判断は止めず後でまとめて確認(回答 10-12b §6-6) |

## §2 3-2 の 4(取り出したばかりの状態での試験)

### §2-1 data の無い作業木の結果

手順: `git worktree add <tmp> HEAD`(data のつなぎを作らない)→ `PYTHONPATH=<tmp>/src` で本体の venv の pytest を直列で(`-p no:cacheprovider -o addopts=""`・`--junitxml` で分類)。

| 回 | 置いたもの | 結果 | 時間 |
|---|---|---|---|
| 1(`-x`) | なし | 最初の失敗 `tests/c6/test_l4_l6_budget.py::test_l4_cap_holds_for_a_5000_agent_day_on_the_synthetic_world`(合成の世界のランでも開始日の検査で止まる)。それまで 801 passed / 71 skipped | 13 秒 |
| 2(全体) | なし | **313 failed / 68 errors / 3,394 passed / 195 skipped** | 213 秒 |
| 3(全体) | 祝日 CSV 1 本だけ(`data/calendar/syukujitsu.csv`・本物と同じ md5・junction ではない普通のファイル) | **1 failed / 3,776 passed / 193 skipped**。slow を外した分は 1 failed / 3,764 passed / 170 skipped(試験の時間の和 887 秒)・slow は 12 passed / 23 skipped(126 秒)。P6 は通った(回 2 で落ちたのは負荷による揺れ) | 1,018 秒 |

回 3 で残った 1 件: `test_calendar_10e_e3.py::test_e3_two_days_advance_on_the_calendar_and_the_weekday_rows_come_from_it`(:192 `assert seen["presence"] == [(1, 0)]` が `[]`)。`world_dir=data/world/v2` でランを回すのに、同じファイルにある `needs_world`(:30)が付いていない。世界資産が無いと計画実行層が作られず、W17 の行が呼ばれない。**data の印の付け忘れ**で、祝日の表が無い間は開始日の検査で先に止まっていたので見えなかった。

回 2 の落ち方の分類(381 件):

| 分類 | 件数 | 中身 |
|---|---|---|
| A 開始日の検査で止まる | 369(failed 301・errors 68) | `ValueError: 開始日の検査で止めた: 祝日の表が読めていない`(`calendar.py:410` で積み `:431` で投げる)。72 ファイルにまたがる。多いのは `test_state_ledger_10b` 27・`test_fleet_wiring` 19・`test_resume_10d` 17・`test_intent_mode_open` 15・`test_ledger_wiring` 12 |
| A′ 同じ原因で検査の試験が別の形で落ちる | 10 | `tests/engine/systems/test_guard_runs.py::test_dropping_a_column_fails_where_it_is_written`(列を外して「書いた所で落ちる」を見る試験が、`build → check_start` で先に落ちる) |
| B CSV を直接開く | 1 | `test_state_format_10f.py::test_u1_resume_from_a_pkl_written_by_the_pickle_commit`(`FileNotFoundError`) |
| C 環境(時間門) | 1 | `test_change_detect_p6.py::test_p6_change_detection_under_2ms_at_400k_agents`(slow・2.125 ms) |

飛ばした 195 件の理由は 23 通りの文言(「data/ absent (CI)」55・「実世界資産が無い」53・「実世界資産 data/world/v2 が無い」32 ほか)。中身は世界資産(`data/world/v2`)・PLATEAU・e-Stat の境界・テープ・艦隊の診断の環境変数。

評価者の環境依存の 4 件は手元では P6 だけが出た(scipy なし・ホスト名が当たらない・golden に登録済みの機械・`PYTHONPATH` を付けた)。コードは §1 の 1-5a〜d のとおり。

### §2-2 CI の状態(gh で確認)

- `.github/workflows/ci.yml`: ubuntu・Python 3.12・`pip install -e ".[dev]"`・秘密スキャン・`lint-imports`・`pytest -q -m "not gpu and not slow"`・timeout 30 分。data は無い。nightly のジョブ(cron)は無い(ci.yml:31 の「slow は nightly」は印だけ)。
- 最後の緑: `8c8a77c`(10-06 23:55 JST)。以後 34 ラン連続で赤。
  - `74d6da8`(第325)〜`6267f71`: 1〜2 件(golden の platform の assert・旧 pickle の試験の CSV)。
  - `0e366cc`(第329): 17 件(訂正 commit の前の版。ファイルが入っていなかった)。
  - `ee3abc7`(第330 ACT の後): 287 failed / 66 errors。`82c2ed5`: 304 failed / 68 errors。
- pytest の段の所要: 17 分(10-06・緑)・24 分(10-11・ほぼ全部走った最後)。slow を外しても 30 分の上限に近い。
- golden: CI の Linux は未登録の環境なので、golden の値とは比べず A/A だけ(K26 (1) の設計どおり)。CI の値は golden を守っていない(評価のとおり)。CI の依存は下限だけの指定(pyproject)で毎回最新を入れるので、`platform_id` は上流の版が出るたびに変わる。

### §2-3 案

#### (i) 試験に要る小さな公開データをリポに入れる

**入れられるもの(規約を読んだ)**: 内閣府「国民の祝日」CSV。

- 頁 `https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html` には CSV への案内(「昭和30年(1955年)から令和9年(2027年)国民の祝日(csv形式:22KB)」)と更新の時期(「令和10年(2028年)の国民の祝日は、前年(令和9年(2027年))の2月に掲載します」)があり、頁の中に別の利用条件は無い。
- 内閣府の利用規約 `https://www.cao.go.jp/notice/rule.html`: 「権利表記の記載がない限り公共データ利用規約(第1.0版)(デジタル庁)が適用されます」。
- 公共データ利用規約 第 1.0 版(`https://www.digital.go.jp/resources/open_data/public_data_license_v1.0`): 複製・公衆送信・翻案が自由・商用利用も可能・出典の記載が条件・加工したら加工したことと主体を書く・CC BY 4.0 と互換。数値データや簡単な表はそもそも著作権の対象ではない。
- ライセンス台帳 135 行(2026-10-03 の取得・md5 `733fabb6…`・21,538 B・PDL1.0)と一致する。

置き場の案:

| 案 | 中身 | 長所 | 短所 |
|---|---|---|---|
| (i-1) `tests/fixtures/calendar/syukujitsu.csv`+`tests/conftest.py` で「`data/calendar/syukujitsu.csv` が無ければ fixture を写す」 | CSV は手を加えず(md5 同じ)、出典の 1 行を `tests/fixtures/README.md` に(「出典: 内閣府『国民の祝日について』(URL)・PDL1.0(URL)・2026-10-03 取得」) | gitignore を解かない(CLAUDE.md §7)。既定の道筋の文字列 `data/calendar/syukujitsu.csv` が変わらない=manifest の `holiday_csv` の欄と final が同じ | 試験が作業コピーの `data/` に 1 本書く(gitignore 下・作業木は junction があれば書かない) |
| (i-2) `data/calendar/` を gitignore の例外にして CSV を入れる | `.gitignore` に `!data/calendar/syukujitsu.csv`・ci.yml の「data/ must stay out of git」の段に例外 | コードも conftest も変えない | **CLAUDE.md §7「gitignore を解除しない」と食い違う(d)**=ユーザーの判断が要る |
| (i-3) 道筋を環境変数で変えられるようにする(`src` を変える) | `SHIBUYA_HOLIDAY_CSV` | 置き場が自由 | manifest の `holiday_csv` の欄が環境で変わる。既定の挙動に触る |

親推奨(案): (i-1)。サイズ 21,538 B。更新の仕方: 内閣府が翌年の分を 2 月に載せたら、手で取得 → ライセンス台帳に行 → fixture を差し替えて md5 を記録 → 祝日の表の範囲(今は 2027-11-23 まで)が変わったことを devlog に、の 1 commit。差し替えで final が動くかは、開始日 2026-07-13 の周りの行が同じなら動かない見込み(推測・未確認)。

**ほかの候補**: data の無い環境で**落ちる**のは祝日 CSV だけだった(§2-1)。ほかの試験は飛ぶ。世界資産(`data/world/v2`・13 GB)は OSM(ODbL)・PLATEAU・e-Stat・W16 の人口(国勢調査から作った物)・LLM で作った persona_pool などを混ぜた構築物で、資産ごとの規約と大きさの確かめは済んでいない(§5 空欄)。小さな世界の fixture を作るなら、合成の世界(既にある `test_l4_cap_holds_for_a_5000_agent_day_on_the_synthetic_world` の形)を先に広げる方が規約の確認が要らない。

#### (ii) 入れられないものは理由を書いて飛ばす

入れられないもの: KDDI の滞在人口(holdout・封印・有償の許諾)・PT の個票(申請)・ODPT チャレンジ枠(応募のためだけ・再配布しない=回答 10-13 の 3)・ユーザーが手で入手した時刻表と構内図(git に入れない=回答 10-12b §2-1)・世界資産 13 GB(大きさと混ざった規約)・テープ・回収物。

案:

1. 印を 1 つにする: `tests/conftest.py` に `requires_data(<id>, *paths)` を置き、理由の文言を `data-absent:<id>` に揃える(id は `calendar`・`world-v2`・`plateau-raw`・`estat-boundary`・`tape-ab7`・`fleet-counters` ほか)。`pyproject.toml` の `markers` に登録する。今の 67 か所の `skipif` と 30 か所の `pytest.skip(` のうち data の有無を見るものを置き換える(試験の中身は変えない)。
2. 「飛ばした数」を出す: `pytest_terminal_summary` で id ごとの件数を 1 行ずつ出し、CI ではジョブの要約(`$GITHUB_STEP_SUMMARY`)にも書く。数が前回より増えたら目で見て分かる形(合否にはしない)。
3. 落ちるのではなく飛ぶ形にする範囲: data が無いときに**落ちる**試験は、(i) の後は回 3 で 1 件(`test_calendar_10e_e3.py` の `needs_world` の付け忘れ)。これに印を付ければ 0 件。今後 data を読む試験を足すときは `requires_data` を付けることを試験の書き方の約束にし、印の付け忘れは W0 の CI で毎回見つかる形にする。

#### (iii) 速い段の試験を GitHub 上で自動で回す

| 段 | いつ・どこで | 中身 | 目安 |
|---|---|---|---|
| CI-0 静的 | push と PR・GitHub | 秘密スキャン・`lint-imports`・AST の試験(18 ファイル)・`tests/engine/systems/` の静的な宣言の検査 | 数分 |
| CI-1 data 不要の単体と結合 | push と PR・GitHub | `-m "not gpu and not slow"`(祝日の fixture つき・data の要る試験は (ii) の印で飛ぶ)。`pytest-xdist` で 2〜4 並べる(GitHub の標準ランナーは 4 コア)。golden は未登録=A/A | 今は直列で 17〜24 分。並べて 10 分前後(推測・未計測) |
| CI-2 夜の data 不要の slow | 毎晩・GitHub の cron | 合成の世界の 5,000 体×1 日など slow のうち data の要らないもの。時間の門は GitHub では揺れるので**記録だけ**(合否にしない) | slow 35 本のうち data 不要の分 |
| 本体の夜間 | 毎晩・作者の機械(タスク スケジューラ。日次の現実データの取得と同じ置き場) | data のある全体の試験・byte-check 19 構成・golden(登録済みの環境)・性能の門(P6 ほか)・10-03 ⑥ 6-5 の性能の記録・「現実との差」の計器(7-2 を採るなら) | 計画 §1-11 の段 3 と同じもの |

golden の CI の環境への登録: **今は登録しない**を親推奨(案)にする。理由: 登録すると版上げのたびに 2 つの環境で張り替えが要り、CI の依存が下限だけの指定なので上流の版が出るたびに `platform_id` が変わる。golden の値は「本体の夜間」(登録済みの機械)で守る。そのかわり `test_env_and_sections_10f.py:295` の assert は K26 (1) に合わせて「未登録なら警告して飛ばす」に直す。第三者の再現を主張に使うとき(論文・未踏の報告)に、依存の版を固定する一覧(constraints)を作ってから CI の行を足す。

#### 作業木で回る最小の試験の集合(案)

作業木の並行作業の前提として 2 つに分ける。

- **W0(data のつなぎの無い作業木・clean checkout と CI と同じ)**: `pytest -m "not gpu and not slow"`+`lint-imports`。祝日の fixture(i-1)と (ii) の印があれば「失敗 0・飛ばした数を id ごとに表示」が合格の形。回 3 の結果: 1 failed(印の付け忘れ 1 件)/ 3,764 passed / 170 skipped・直列で約 15 分(手元)。子プロセスの import の穴(§2-4)を塞ぐのが前提。研究の枝(文書だけ)と、data に触らない系の単体の試験(計画 §1-11 の段 0)はこれで足りる。
- **W1(data のつなぎのある作業木)**: 計画 §1-11 の段 0〜1(系の単体の試験+関係する試験+小さな人数の byte-check 3〜4 構成+系ごとの指紋)。段 2(byte-check 19 構成)と段 3(全体)は取り込みの前と夜に本体で。

### §2-4 作業木の import の穴(評価に無い・(b))

- 本体の venv は `shibuya-sim` を editable で入れていて(`__editable__.shibuya_sim-0.0.1.pth`)、行き先は本体の作業コピー。
- pytest の本体のプロセスは `pyproject.toml` の `pythonpath = ["src"]` で作業木の `src` を読むが、**子プロセスは `.pth` で本体の `src` を読む**。作業木で `PYTHONPATH` を付けずに `python -c "import shibuya; print(shibuya.__file__)"` を回すと本体の道筋が出た。
- 子プロセスを起こす試験は 6 ファイル(`test_resume_10d`・`test_env_and_sections_10f`・`test_salt_seed_split_10f`(`tools/c7/salt_runs.py`)・`c6/test_t3_parallel_invariance`(`tools/c6/run_hash.py`)・`test_world_catalog_sha`・`test_state_format_10f`(これだけは `PYTHONPATH` を自分で付ける))。作業木の変更が子に届かず、**本体のコードで試験が通る**(再開と並列の不変を見る試験が多い)。
- これまでの作業木の記録は `PYTHONPATH=src` を付けて回している(例: run-day-decomp の検収の記録)が、リポの仕組みにはなっていない。
- 案: `tests/conftest.py` でセッションの頭に `os.environ["PYTHONPATH"]` の先頭へ `<rootdir>/src` を足す(子が同じ `src` を読む)。または作業木ごとに venv を作る。親推奨(案)は conftest(1 か所で済む・CI では無害)。

## §3 3-2 の 7(決定の写し)

### §3-1 数え(grep・v1 の参考の文書は除く)

| 決定 | 正(ユーザーの原文) | 写し(中身を書き直している所) | 参照だけ・使う所 | 決定台帳 §9 |
|---|---|---|---|---|
| 既定の開始日 2026-07-13 | 回答 10-12b §1 の 4 | 計画(第 0 期の 2 か所)・PENDING(§3・§4)・IMPLEMENTED #88・devlog-compressed 第330・10e の記録 README(12 回)・10e-build-side-prep=**6 文書**。コード `engine/calendar.py:76`(`DEFAULT_WORLD_START`)と docstring 3 か所 | ライセンス台帳・時刻表の記録 5 本・回答 10-13(「世界の時点」として使う) | 無い |
| W17 の凍結(CA1) | 指示書 10-12 §4-1 | カレンダーの草案の〔答え〕(21 回)・計画 3-1・ペルソナの作り直しの設計書・壁打ちのメモ 10-07〜12・コードと決定の食い違いの洗い出し=**5 文書** | 答申 3 本(R-99・R-101・R-102)・10-06 の調べの指示書 | 無い |
| 1-0 の切り方(今の実行順の区間・25 系) | 回答 10-13 §1 の 1 | 分解の草案の〔承認〕・計画 1-0・PENDING(§0・§2・§3・§4 の 4 行)・STATUS(2 行)・devlog 第331・IMPLEMENTED #89・記録 `run-day-decomp/impl-1-0.md`=**7 文書** | — | 無い |

所見:

1. 「正」は実際には**ユーザーの原文(指示書・回答)**で、計画の冒頭も「回答が正・本書の写しは回答に従う」と書いている。決定台帳 `v2-redesign.md` §9(105 行)は 09-08 までの行が中心で、10-03 以降の決定は行になっていない(10-12 の日付の行 8 つは改訂の印)。
2. ID は文書ごとの局所の番号で、ぶつかる: 「C1」は工程 C1・連絡の道具 C1(CT)・10-03 ⑥ 6-2 のカスケード C1、「6-1」は 10-03 ⑥ と回答 10-12b §6 の両方にある。
3. 写しが遅れた例は評価の指摘のとおり(STATUS の日付・README の数字)。今回の 3 件には中身の食い違いは見つけていない(数値の突き合わせまではしていない)。
4. コードに入る値(開始日の定数など)と、設計書で実装に要る数値は写しが避けられない。これは CLAUDE.md §5 の写し検査(2 段の突き合わせ)と訂正の伝播検査が守る範囲で、変えなくてよい。

### §3-2 案(2〜3 通り)

| 案 | 中身 | CLAUDE.md を変えるか | 費用 | 写しの減り方 |
|---|---|---|---|---|
| **A 索引だけ足す** | 道具(`tools/` に 1 本)で指示書・回答から ID を拾い、「全体の ID → 正の節 → 写し先(grep)」の表を自動で作る(research の INDEX と同じ自動生成)。ID の形は `<文書の日付>/<局所 ID>`(例 `10-12/CA1`・`10-13/1-1`) | 変えない | 小 | 減らない。写し検査と訂正の伝播検査が ID の grep 1 回で済む |
| **B 正は原文・他は ID で参照**(A を土台に) | A に加えて、計画・PENDING・STATUS・devlog・IMPLEMENTED・草案の〔答え〕では決定の中身を書き直さず、`[10-12/CA1]` のリンクと 1 行の見出し(10〜20 字)だけにする。STATUS は「現在地」を書かず PENDING §0 へのリンクに。値がコードと設計書に要るものは今までどおり写して写し検査 | §6 に 1 項足す(「決定の中身は写さず全体の ID で参照する。写すのは実装に要る値だけで、§5 の写し検査の対象にする」)。§5 は変えない | 中(書き方の約束と、次の交換からの適用。過去の文書は書き換えない) | 1 件あたり 6〜8 か所 → 正 1+ID の参照、値の写しは計画と設計書とコードだけ |
| **C 決定台帳を 1 か所の登録簿に戻す**(評価の提案) | `v2-redesign.md` §9 に 10-03 以降の決定を全部 1 行ずつ足し(D-ID・1 行・原文へのリンク)、他は D-ID だけで参照 | §1 の正典の書き方と §6 を変える | 大(10-03〜10-13 の決定は数百項目。§9 は既に 146 KB) | B と同じだが、原文と台帳の 2 か所になり、台帳の行が新しい写しになる |

**親推奨(案)は B**。理由: 正はすでに原文で決まっていて、時間を食っているのは計画・PENDING・STATUS・devlog・IMPLEMENTED での書き直し。C は原文と台帳の 2 か所目を作るうえ、原文のまま保存する約束(10-03 §0 の 2)と台帳のどちらが正かをまた決める必要がある。B は §6 に 1 項を足すだけで §5 は変えずに済み、変える前に A だけ先に入れても効く(写し検査が軽くなる)。CLAUDE.md を変えるのでユーザーの承認が要る。

ついでに直せるもの(事後報告の範囲かは親の判断): STATUS.md:3・:13 と devlog 第331 の見出しの日付(10-14 → 10-13)・README の数字と背骨の行と「次にやること」(README を版上げのたびに直すかは B の「STATUS は PENDING へのリンク」と同じ考えで、README は外向けの要約だけにして数字は IMPLEMENTED へのリンクにする案もある)。

## §4 数え直し

| 評価の数 | 数え直し | 数え方 |
|---|---|---|
| 収集 3,945 | 3,970(手元)。CI の選び方(not gpu and not slow)は 3,935 | `pytest --co`。環境で parametrize と収集が違う |
| `def test_` 3,190 | 3,190 | `grep -E '^\s*(async )?def test_'` |
| README の 2,298 | README.md:32 にある | — |
| import-linter 5 契約 | 5 kept / 0 broken | 作業木で `lint-imports` |
| AST の試験 18 ファイル・282 本 | 18・282 | `import ast` のある試験ファイルと、その中の `def test_` |
| systems 54 本 | 54(5 ファイル) | `tests/engine/systems/` の `def test_` |
| golden の 16 進の直書き 30 本 | 30 ファイル・95 個 | 16〜64 桁の 16 進の文字列 |
| data に触る試験 113 | 108(data が無いと落ちるか飛ぶファイル・実測)/ 文字列での数え 74〜88 | junit の結果/`data/` などの文字列 |
| skipif 66 | 67 か所(49 ファイル)+`pytest.skip(` 30 か所・`importorskip` 4 か所 | grep |
| 遅い試験 5,000 体×1 日 | slow の印 35 本 | `-m slow --co` |
| docs 1,328 ファイル | 1,328 | `git ls-files docs` |
| Markdown 1,480 万字 | 14,846,360 **バイト**・8,599,656 字(597 本) | UTF-8 のバイト/文字 |
| research 349(722 万) | 349 ファイル(Markdown 296)・Markdown 7,218,803 バイト・4,300,708 字 | 同上 |
| design 94(322 万) | 94 ファイル・Markdown 3,215,011 バイト・1,632,502 字 | 同上 |
| bench 849(345 万) | 849 ファイル(JSON 518・Markdown 172・py 111)・Markdown 3,449,642 バイト・2,132,253 字・全体 28.8 MB | 同上 |
| src 410 万 | 4,099,425 バイト・3,352,419 字・84,256 行(182 ファイル) | 同上 |
| tests 5.7 万行 | 57,360 行 | 同上 |
| IMPLEMENTED 215 KB・1 行最大 2,498 | 215,262 B・1 行最大 2,498 バイト(1,519 字) | — |
| PENDING 20 KB・旧 PENDING 207 KB・CLAUDE.md 21 KB | 20,230・207,408・21,443 B | — |
| 決定台帳 146 KB・§9 約 105 行 | 146,204 B・§9 の表 105 行 | — |
| 壁打ち・回答・決定 93 万字 | 名前に wallbounce・answers・decision などを含む 20 本で 892,571 バイト | 数え方で変わる |
| 答申 176・未参照 26・D 等級 33 | 答申 174+索引 2・未参照(design・src・tools・トップから)26・うち docs のどこからも未参照 2・D 等級 33(INDEX §5) | grep |
| 09-22 以降 147 commit | 148(JST 09-22 0 時から HEAD まで) | `git log --since` |
| docs/bench 48.3 万・src 3.2 万・research 3.1 万・tests 2.2 万行 | 483,200・31,685・31,069・21,698 行(追加) | `git log --numstat` |
| 件名の約 6 割が答申ほか | src と tests に触れない commit 79/148=53% | 変更したファイルで分けた |
| 用語集 2.8 万字 | 27,748 バイト・14,186 字 | — |

## §5 空欄

- 評価者の環境の「自作 CSV の md5 の違い 1 件」と「原因を詰め切れていない 2 件」: 再現していない(本物の CSV と Windows で回したため)。Linux・Python 3.13・scipy ありの環境では試していない。
- 世界資産(`data/world/v2`)の資産ごとの規約と大きさ: 小さな世界の fixture に使えるかは確かめていない。
- (iii) の CI-1 を xdist で並べたときの時間: 未計測(推測)。リポは公開(`gh repo view` で PUBLIC)なので標準の Linux ランナーは 4 コアのはず(記憶・GitHub の文書で未確認)。
- 祝日 CSV を内閣府の新しい版に差し替えたときに final が動くか: 未確認(推測)。
- 評価 D §4 の「顧客に何を出せるかの頁」と §6 の同分野の比較: D の事実確認の範囲の外として見ていない。
- 「判断待ちと手作業を週 1 回まとめて出す」: 回答 10-12b §6-6 で一部は手当て済みと読んだが、週ごとにまとめる運用の決定は見つけていない。
