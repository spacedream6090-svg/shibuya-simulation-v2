# 第 1 期 1-9 お金の基本操作(CP2 の段階 1)の独立検収

- 検収役 Opus 5.5(実装は見ていない)。作業木の枝 `1-9/money-transfer`(基 `136fdbb`)の未 commit の差分を読み、回した。
- 正: 口の約束 `docs/design/v2-foundation-contracts-2026-10-13.md` の「1-9」・発注文・実装役の記録 [README.md](README.md)・決定 10-12 §4-5(CP1・CP2)・10b-prep §3-2(E1〜E9)。
- 作業用の置き場は作業木の `_bc_review/`(git の外・終わったら消した)。検収役の道具(独立の同値の列・減価償却の 3 例・負の対照の植え込み・系ごとの指紋・設定の道筋と manifest の比べ・1-4 の走査の試し)は、消す前に親のセッションの作業用の置き場 `333/review_1-9/` に写した(本書の外)。
- 途中で本体の HEAD が `fbe2c06` → `6b82be2`(1-4 の取り込み)に進んだ。比べた HEAD の src は `fbe2c06`(= `136fdbb` と src が同じことを `git diff` で確かめた)。

## 判定: 条件つき受入

結果不変(final・呼数・テープの列・帳簿の残高・金と物の台帳)は、自分の byte-check 4 構成・係数 3.0 の写し 4 構成・系ごとの指紋(違いは診断の欄だけ=§G)・独立の同値の列で確かめられた。K17 で full-hash が動くのは、親の判断の前提(動くのは O92 と容量の欄だけ・係数を戻せば 36 欄とも同じ)どおりだった。ただし次の 2 点は直すか、親が判断するまで受入にしない。

- **M1**: 科目「減価償却」を汎用の口(`Ledger.transfer`・`transfer_many`)に渡すと HEAD と値が違う。「9 口 → 同じ戻り値と状態」の主張がこの入力では成り立たない。同値の試験は seed の運で通っている。
- **M2**: 公開の `Ledger.unlocked()` と `Ledger.balance()` を組み合わせると、`transfer` の外から残高を書けて、どの検査にも掛からない。

## 1〜8 の確かめ

| # | 項 | 判定 | 根拠 |
|---|---|---|---|
| 1 | 結果不変 | ✓(full-hash は K17 の意図どおり) | 実装役の 19 構成の JSON: final は 19/19 で同じ。動いた欄は全構成で `money_core.raw_capacity`(16,384 → 32,500)だけ。HEAD で溢れていた 5 構成(w6_v3_default・v3_mem_store・v3_mem_rel・v3_classical・v3_classical_mem_rel)はさらに `full_last`・`end_of_day`・生ログの行数・その sha・落ちた行の数が動いた。係数 3.0 の JSON は 19/19 で 36 欄とも同じ。**自分の 4 構成**(下の §A)も同じ形だった |
| 2 | 口と約束 | △ | 口の形は発注どおり `transfer(ledger, src, dst, amount, what, cause, t_ns) -> TransferId`(約束の `transfer(from, to, amount, what, cause)` から ledger・t_ns・戻りを足した。`from` は Python の予約語)。約束 (1)〜(3) の試験はある。〔決定〕K17 は反映済み(6.5・manifest と計器・溢れたら記録して続ける)。約束の「A〜D は基本操作からしか書けない(AST)」は金だけが対象(発注どおり)。帳簿 9 口のうち E6〜E9(物だけの口)は載っていない(仮採用 4)。M1 も参照 |
| 3 | 発注の各項 | 下の §B | |
| 4 | 守り | △ | 書き手の AST の検査と負の対照 5 本はある。自分でも 2 本植えて落ちることを確かめた(§C)。抜け道が 2 つある: M2(`unlocked()`+`balance()`)と `setattr`(記録の限界に書いてある)。実行時に凍結されるのは `_lines` だけで、`_flow`・`_raw_*`・`_last_change_day` は窓の外でも書ける(HEAD から同じ=守りは AST だけ) |
| 5 | 宣言と凍結 | ✓ | `C:ledger.*` を world・phase_c・day_close・close_final に、`E:events.*` を phase_c に宣言。段 B の正と負の対照の試験がある。状態台帳の行 C(diag・discardable)。除外は 3 つ。凍結の表は増えた分だけ: manifest の鍵に `economy`、`E:events.*` の系に phase_c。10f の `CONFIG_PATHS_SHA256` は HEAD の値 `d16f26e6…` から `economy` の設定の 5 道筋だけが増えた値(自分で両側の `config_paths()` を出して比べた)。manifest の既存の欄の値は、200 体のランで HEAD の写しと同じ。違うのは `daily`(`economy` を足した・`events` の行数)・`manifest_sections`・環境の git の欄だけ(写しは git の外) |
| 6 | 同値 | △(M1) | §D。独立の列 5,920 回の比べで、減価償却を汎用の口に渡す場合を除いて全部同じだった。実装役の道具を別の seed 100 本で回すと 97 本が通り、3 本は M1 で落ちた |
| 7 | 試験 | ✓ | §E |
| 8 | 抜け道と記録 | △ | §F。(a)〜(g)。記録に絶対パス・ホスト名・個人名は無い。秘密の走査は CLEAN。§10 の共有ファイルの一覧は 5 本足りない(L4) |

## A. 自分の byte-check 4 構成(`w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`)

- 道具は `cp2/tools/byte_check_cp2.py`(10e の `byte_check_10e.py` の `one` をそのまま呼び、帳簿の 11 欄を足す=中身を読んだ)。比べは 10e の `compare`(25 欄)と cp2 の `compare`(36 欄)の両方で行った。
- 3 つの側: HEAD の写し(`git archive` の src)・作業木の src(`PYTHONPATH` で作業木を指定。`src_is_worktree=true` を確かめた。venv の editable の .pth は本体の src を指すので、指定しないと HEAD 同士の比べになる)・**係数だけ 3.0 に戻した作業木の写し**(`diff -r` で違いが `ledger.py` の 1 行だけと確かめた。実装役の `--rate` の差し替えは使っていない)。
- HEAD 対作業木: final・呼数・テープの列(calls と blocks の列名と sha・テープのバイト数)・behavior-hash・行動の件数・帳簿の残高・世帯の現金・流れの集約行・`state_hash`・物の台帳・生ログの末尾 16,384 行は 4/4 で同じだった。動いた欄は次のとおり。
  - 4 構成とも: `money_core` の `raw_capacity` だけ(`n_transfers`・却下の計数は同じ)。
  - w6_v3_default・v3_mem_rel: `full_last`・`end_of_day`(`full_hash` と `full_external_bytes` だけ。behavior は同じ)・`money_raw_rows`(16,384 → 20,055/20,183)・その sha・`money_n_raw_dropped`(3,671/3,799 → 0)。full-hash の材料のバイト数で違うのは行 **O92 だけ**(371 → 365 B=`_raw_head`・`n_raw_dropped` の桁)。
- HEAD 対係数 3.0 の写し: **4/4 で 36 欄が全部同じ**(full-hash を含む)。→ full-hash が動く原因は係数(輪の容量)だけで、載せ替えそのものではない。親の判断の前提は成り立つ。
- 日次の記録の出来事の行は増える(例 28,835 → 32,158=金の出来事 3,323 行)。診断なので、どのハッシュにも入らない。

## B. 発注の「作るもの」

| 番 | 判定 | 理由 |
|---|---|---|
| 1 `ops.transfer` と 9 口の載せ替え | △ | 金の口(E1〜E5 の金の脚と `depreciate`)は検査の後に `transfer` を呼ぶ。`_apply_cash`・`_record` は消えた。E6〜E9 は物だけなので載っていない(仮採用 4・親に確かめる点 3)。M1(減価償却を汎用の口に渡すと値が変わる) |
| 2 AST の検査 | △ | 試験・負の対照 5 本・凍結の表(8 関数)がある。ただし「書き手は transfer の中だけ」ではなく、resolve の 4 関数(台帳の無い経路 C2 と `pois.revenue`)を「段階 2」として凍結の表で許している(仮採用 2・5)。`alias_writes.json` は発注の置き場に無く、実行時の表 `allow.py` の `ALIAS_WRITES` から 4 行を消した(5 → 1 行)。閉包は前と同じ(`writes_soa_frozen.json` は不変)。M2 |
| 3 K17 | ✓ | 6.5・容量 5,000 体で 32,500 行・39 万体で 2,535,436 行(⌈6.5 × 390,067⌉)。バイト 60,850,464・目印 30,425,232・物の目印 9,361,608 は自分で再計算して一致した。溢れは manifest・日次・計器に出る。溢れても止めない。設計書の予算の更新は親。L2(19 構成の試験は 300 体で空振り) |
| 4 目印の列 | △ | 金の生ログと納品ログに `(t_ns, seq)` の列がある。原因を渡した行は 1 対 1。原因が渡るのは運賃(過程 rail)と補充の代金(過程 shelf)だけで、購入・食事・初期の財布・参入資本は目印が空(既定 v3 で原因つきは 3,323/20,055=16.6%)。理由は記録の仮採用 5 にある |
| 5 締めの検算 | ✓ | `flow_sum_ok` は計器だけ。transfer の外で流れの表を書けば落ちる(負の対照あり)。四重記入の既存の検算は不変 |
| 6 manifest | ✓ | `economy.raw_capacity`・`raw_overflow`・`transfers_total` ほか。既存の欄は不変(1 の 5 の行) |
| 「できなかったこと」 | ✓ | 申告(系ごとの指紋・manifest 7 本・39 万体の実測・独立検収は回していない)は実態と合う。系ごとの指紋は検収役が回した(§E) |

## C. 守りの負の対照(一時の写しに植えた・本物の src には触れていない)

`tests/economy/cp2/` と `src` を一時の写しに写し、`test_cp2_transfer_only_writer.py` を写しで回した。

| 植えたもの | 結果 |
|---|---|
| a. `engine/run.py` に新しい関数(別名の鎖 `led = res.ledger` → `lines = led.money._lines` → `row = lines[0]` → `row[1][3] = 7`) | 落ちた(`_lines`・添字への代入) |
| b. 凍結の表にある `resolve._complete_buy` に、表に無い列の書き `ledger.money._flow[0, 1, 2] += 5` | 落ちた(表の外の書き+表の行と実際の書きの食い違いの 2 本) |
| c. `with led.unlocked(): led.balance(0, 1)[2] = 9` | **落ちない**(関数をまたぐ別名)。実行時も書けた(店の現金 1,000 → 999 を確かめた)。`test_single_write_path` は `_open` の呼び手しか見ない=M2 |
| d. `setattr(led, "_raw_pos", 0)` | 落ちない(記録の限界のとおり) |

植える前の写しでは 12/12 が通った。

## D. 同値の独立の再計算

- 道具は自前(実装役の `head_copies.py`・`_Pair` は使わない)。HEAD の `ledger.py`・`goods.py` を `git show` で取り直した(blob `8a6a964…`・`7165e5b…`=実装役の写しと同じ名)。自前の乱数で口の呼び出しの列を流し、毎回の戻り値(または例外の型)と全部の状態を sha で比べた。状態は残高の全配列・世帯の現金・流れ・日次の集約・最後に動いた日・生ログの中身と輪の 7 列・位置・計数・締め・`state_hash`・貨幣供給量・物の在庫の配列・納品ログと位置。作業木の側だけ出来事の記録を挿し、原因(rail・shelf・LlmCall・なし)をでたらめに渡した。
- 結果(seed・回数・容量・保持窓): 20261014・1,500・11・1/424242・1,500・37・2/9001・1,200・4,096・1/77・2,000・23・3。比べ 5,920 回が全部同じ(溢れ 0〜1,700 行・締め 20〜45 日・出来事 728〜1,352 行。目印のある行は記録の金の出来事と 1 対 1)。**ただし、減価償却を汎用の口に渡す呼び出しは除いた**。除く前は 3 seed とも食い違った=M1。
- 決定的な 3 例(店 3 軒に参入資本 1,000 円ずつ・刻み 5):

| 呼び出し | HEAD | 1-9 |
|---|---|---|
| `transfer_many(店0 → 店1, 100, 減価償却)` | OK・店の現金 900/1,100・取引 +1・流れ +100 | **ValueError**「減価償却は自己ループ」 |
| `transfer_many(店2 → 店2, 100, 減価償却)` | OK・現金は差し引き 0・取引 +1・流れ +100 | OK・**固定資産 −100**・取引 +0・流れ +100 |
| `transfer(店0 → 店0, 100, 減価償却)` | 同上(現金は差し引き 0) | 同上(固定資産 −100) |
| `depreciate(店1, 100)` | 固定資産 −100 | 同じ |

- 実装役の `_Pair` を別の seed 5000〜5099 で回すと 97 本が通り、5012・5030・5098 の 3 本が上と同じ理由で落ちた。`test_cp2_nine_ops_equivalence.py` の seed 0〜23 は運よく当たっていない。

## E. 試験

- 指定の範囲 `tests/economy tests/engine/test_ledger_wiring.py tests/engine/systems tests/engine/events tests/engine/time tests/engine/test_two_phase.py tests/engine/test_state_ledger_10b.py tests/engine/test_env_and_sections_10f.py`(`-m "not slow" -n 2 --dist loadfile`): **585 passed**(213 秒)。指定にあった `tests/engine/test_single_write_path.py` は存在しない(実物は `tests/economy/` にあり、上の範囲に入っている)。
- cp2 の `slow` 4 本: **4 passed**(115 秒)。
- `tests/engine/test_resume_10d.py`(`-m "not slow" -n 2`): **38 passed**(674 秒)。
- `lint-imports`(作業木の src を `PYTHONPATH` で指定・`--no-cache`・190 ファイル): **5 契約とも KEPT**。負の対照として、一時の写しの `economy/ops.py` に `from shibuya.engine.events import vocab` を足すと「economy は … world/agents 直接書き込み禁止」が **BROKEN**(`economy.ops → engine.events.vocab → llm.contract`)。層の契約は `MoneyEventLink` の依存逆転で守られている。
- 系ごとの指紋(1-3 の `probe_e13.py` の形を写した自前の道具・全部の刻み・`PYTHONHASHSEED=0`・両側から行 E と C・日次の `events`・`economy` を外す。構成は probe_e13 と同じ 3 つ): final は 3/3 で同じ。合成の世界 80 体は全部の系・全部の刻みで同じ。世界資産 300 体の 2 構成は **world・close_final・report の指紋が違った**。欄ごとに追うと、違いは次の 2 つだけだった(§G)。
  1. T=600 から world の `O61:runner.log`(ActualLog)。1-3 の目印の列 `_event_seq` の値がずれる。補充の代金の出来事が同じ刻みの出来事の通し番号 seq を先に使うので、同じ刻みの ActualLog の行の出来事の id が後ろへずれる。
  2. ランの終わりの `stats.ledger_growth` と `stats.result`。成長の宣言の行が 2 本増え(目印の列)、`transfer_log` の係数が 72 → 156 B/体/日になった。
- ActualLog の目印の 3 欄も外して回し直すと、違うのは (2) の 2 つの欄(close_final と report の終わりの 2 行)だけになった。並びの長さは 14,159・16,271 で同じ。どちらも診断(O61 は軸 1 no・成長の報告は manifest の外)で、ハッシュには入らない(L9)。

## F. 抜け道と記録((a)〜(g))

- (a) ✓ K17 の受け入れの前提は成り立つ(§A)。動いたのは full-hash 系と容量の欄だけで、final・呼数・テープの列・残高は同じ。係数 3.0 の写しでは 4 構成 × 36 欄が HEAD と全部同じ。full-hash の差は O92 のバイトに出ている(O77 の `raw_rows_kept` は同じ桁なので長さには出ない)。
- (b) ✓/M2 AST の負の対照は §C。新しい書き手と、表にある関数の表に無い列は落ちる。`unlocked()`+`balance()` と `setattr` は通る。
- (c) △/M1 §D。
- (d) ✓ 原因の無い金の行の扱いは記録の §0・§6・§11 の仮採用 5・親に確かめる点 2 にある(`transfers_uncaused`)。1-8 で `purchase_many` に `LlmCall` を渡す段は、問いの形で書かれている(段の約束としては書かれていない)。1-4 のつなぎの台帳には載っていない(L8)。
- (e) △ CP1 の表では A(湧かないもの)=お金と物(品目つき)で、変え方はどちらも「移す」。CP2 の段階は「帳簿 9 口 → 行動の適用 → 残り」で、「お金から始めます」。E6〜E9 を金の `transfer` に載せない読みは「お金から」と合う。ただし E6〜E9 は CP2 の**段階 1(帳簿 9 口)の残り**で、段階 2(行動の適用)ではない。記録 §3 は「物の基本操作の段」と書いていて正しい。凍結の表の「段階 2」は resolve の直の書き(行動の適用)を指していて、これも CP2 と合う。E9 の消費は CP1 の B「使う」に当たりうる。段階 1 の完了の条件(物の「移す」と消費)を PENDING に残すことを勧める。
- (f) ✓ 範囲の外の既存の試験 7 本の編集は、どれも決定から必ず動く所だけ。
  - `test_ledger.py`: 係数 6.5 で奇数の N は切り上げ。等値は「差が 1 行のバイト未満」に緩めたが、意味は保っている。
  - `test_ledger_wiring.py`: cap の数を新しい値にした(自分で再計算して一致)。
  - `test_single_write_path.py`: 触れてよい置き場に ops.py を足した(書きの移動の帰結)。
  - `test_stage_a_guard.py`: 別名の表の行の有無を、規則で引けることの確かめに変えた。閉包 `writes_for_ops` の確かめは残した。
  - `test_two_phase.py`: hot path を足した(強める側)。
  - `test_state_ledger_10b.py`: 行の数。
  - `test_env_and_sections_10f.py`: golden。増えた 5 道筋だけを確かめた。
- (g) ✓ §E。
- 記録: 絶対パス・ホスト名・個人名なし。`tools/scan_secrets.py`(変えたファイルと新しいファイル)は CLEAN。

## 欠陥

| 重さ | 置き場 | 中身 | 直し方(案) |
|---|---|---|---|
| **中 M1** | `src/shibuya/economy/ops.py` 234〜236 行(`self_loop = code == DEPRECIATION`)・`economy/ledger.py` の `transfer`・`transfer_many`(減価償却の科目を通す) | 汎用の口に科目「減価償却」を渡すと HEAD と値が違う(§D の表)。別の口なら例外になる(業務の失敗を行の状態で返す口の約束に反する)。同じ口なら現金ではなく固定資産が減り、取引の件数も数えない。engine の呼び手は無いので 19 構成の結果は不変。ただし「9 口 → 同じ戻り値と状態」は成り立たず、同値の試験は seed の運で通っている(別の seed 100 本中 3 本で落ちる) | 親が決める。(i) 汎用の口では減価償却を `FORBIDDEN_PAIR`(または `UNKNOWN_CODE`)の行の状態で返し、`depreciate` だけを自己ループの入口にする。HEAD との違いは、到達しない入力の宣言つきの直しとして記録する(HEAD の挙動は減価償却の科目で現金を動かす潜在の欠陥=accounts の「現金を動かさない」に反する)。(ii) 決定的な試験を 3 本足す(§D の表)。同値の乱数の列は、汎用の口で減価償却を除く理由を書くか、(i) の後の値で比べる |
| **中 M2** | `economy/ledger.py` の `unlocked()`(公開)・`balance()` | `with led.unlocked(): led.balance(line, s)[i] = x` で残高を書ける。AST の検査(関数をまたぐ別名)にも、`test_single_write_path`(`_open` の呼び手だけ)にも、実行時の守り(窓が開く)にも掛からない(§C の c)。いまの呼び手は ops.py だけ | `unlocked` の呼び手を `economy/ops.py` だけに縛る静的な検査と負の対照を足す(`_modules_calling("unlocked")`)。または `unlocked` を内部の名にする |
| 低 L1 | `economy/goods.py` の docstring「expedient(本モジュール分)」の下 | 1-9 の説明(目印の列)を expedient の項として足した。本体はいま 1-4 が入った `6b82be2` で、つなぎの台帳の行 `HD-economy.goods-1af925f4` は「項 7 個」。1-4 の走査を作業木にかけると 8 個になる=rebase の後に 1-4 の試験が落ちる(走査で確かめた。ほかの宣言は台帳と合う) | 説明を見出しの外へ移す(ledger.py と同じく冒頭の段落にする) |
| 低 L2 | `tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py::test_nineteen_configs_do_not_overflow` | 300 体では行が約 1,200 で、容量の下限 16,384 に遠く届かない=溢れ 0 は必ず成り立つ(空振り) | 構成ごとに `transfers_total / n_agents < TRANSFERS_PER_AGENT_PER_DAY` を確かめる形にする(5,000 体の 19 構成の溢れ 0 は byte-check の JSON にある) |
| 低 L3 | `engine/state_ledger.py` の行 C の注・`table.py` の `C:ledger.*` | 鍵 C の根拠を「CP1 の C=お金」としているが、10-12 §4-5 の CP1 の表では C=権利(お金は A 湧かないもの)。もとは口の約束の「A〜D(体・世界・お金・物)」と発注の「C 金」の書き方で、CP1 の表と食い違う。1-5(権利台帳)と取り違えるおそれ | 親が鍵の名(例 `M`)と注、口の約束の括弧を決める。commit の前なら変えても安い |
| 低 L4 | 記録 §10 | 共有ファイルの一覧に、`git diff --stat` の 5 本(`engine/events/links.py`・`engine/ledger_api.py`・`engine/processes/rail.py`・`engine/processes/goods_flow.py`・`engine/resolve.py`)が無い(§1 にはある)。本体の `6b82be2`(1-4)は run.py・manifest_sections.py・build.py・state_io.py・cli.py と manifest の鍵の凍結の末尾を変えた=rebase で重なる | 一覧に足す |
| 低 L5 | `economy/ops.py` 280〜313 行 | 残高・流れ・輪を書いてから出来事を書く。記録の口が例外を出す(phase_c の宣言漏れの PermissionError・CP12)と、金は動いたまま、計器は数えず、輪の目印の列には前の周の id が残る(ランは止まるので低) | 出来事を書く前に、その行の目印を -1 にしておく |
| 低 L6 | `engine/systems/allow.py` の `TRANSFER_PORTS_HOUSEHOLD` | 書き換えられる dict(1-3 の教訓は MappingProxyType)。規則は名前のある 3 つの口だけを見る(resolve が汎用の `transfer_many` で世帯を動かすと漏れる。いまは無い) | MappingProxyType にする。限界を記録に書く |
| 低 L7 | 計画 1-9・口の約束 | 「A〜D は基本操作からしか書けない」のうち、検査は金だけ(発注どおり)。物の「移す」(E6〜E9 と E5 の物の脚)は CP2 の段階 1 の残り | PENDING に段階 1 の残りとして残す |
| 低 L8 | 1-4 のつなぎの台帳 | 1-9 の新しいつなぎ(運賃の原因=過程 rail・原因の無い金の行・K17 の係数の expedient)が台帳に無い(1-4 が並列で入ったため)。共通の約束「新しいつなぎは台帳に外す段つきで」 | rebase の後に親が行を足す(外す段 1-8 ほか) |
| 低 L9(記録だけ) | 1-3 の出来事の id `(t_ns, seq)` | 金の出来事が同じ刻みの seq を使うので、既存の ActualLog の行の目印(出来事の id)の値が HEAD とずれる(系ごとの指紋の world に出る)。中身・行数・final は同じ。1-3 の id は「刻みの中の書いた順」なので、出来事の書き手を足すたびに既存の id が動く | 記録に「系ごとの指紋は ActualLog の目印の列を外して比べる」と書く。id を書き手をまたいで安定させたいなら、1-3 の id の作り方を親が決める |

## G. 系ごとの指紋の食い違いの追い方

- 1 回目(行 E・C・日次の `events`・`economy` を外す): real300_v3_default は 14,159 の並びのうち 827 が違い、最初は T=600 の world。T=600 の snapshot だけを取り直して欄ごとの digest を比べると、違うのは `O61:runner.log` と `O73:runner.phase_seconds`(壁時計=指紋から外れる欄)だけだった。
- ActualLog の目印の 3 欄(`event_sink`・`_event_t_ns`・`_event_seq`)を外すと、T=600 の欄は全部同じになった。
- 2 回目(目印の 3 欄も外す・全部の刻み): 違うのは終わりの 2 行(close_final・report)だけ。その欄は `stats.ledger_growth` と `stats.result` だった(ランの終わりの snapshot を取り直して確かめた)。
- 結論: 系ごとの指紋の違いは、1-9 が意図した診断の追加(金の出来事の seq・成長の宣言)だけで、行動・状態・final には出ていない。
