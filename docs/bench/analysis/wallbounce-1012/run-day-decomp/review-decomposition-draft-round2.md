# 再検収: run_day の分解の口の案(改訂版・第330)

- 検収役 Opus 5.5(1 回目と同じ人。起草した調査役とは別)。親 Fable 5.1 が最終判断する。コードと追跡ファイルは触っていない。
- 対象: [草案の改訂版](../../../../design/v2-run-day-decomposition-draft.md)(492 行・冒頭に〔改訂(第330・検収の後)〕の表)と本フォルダの道具(`build_allow.py` を静的な閉包に作り直し・`alias_writes.json` を新規・`guard_poc.py` に ufunc.at の検査とランの終わりの守りを追加・`dyn_writers.py` の境目を系に変更・`guard_results.jsonl` は 18 行)。1 回目の記録は [review-decomposition-draft.md](review-decomposition-draft.md)。
- コードの版: `git diff --stat 0389689 -- src` は空。草案の行番号はそのまま使える。

## 判定: 受入

1 回目の条件(R1・K1〜K9・記録の誤り 10・試験の欠け 5)は、どれも本文で解けた。設計で解いたものと、限界として明記したものがある。試作の再実行では、正の 7 本の final と呼数、負の対照 10 本と「書きの起きない負」1 本が、すべて報告どおりだった。下の §5 に残る点はどれも小さく、切る前に止める理由にならない(親の判断で、段 A・段 D を作るときに拾えばよい)。

## 1. 条件ごとの判定

| 番号 | 1 回目の指摘 | 判定 | 本文の場所・確かめたこと |
|---|---|---|---|
| R1 | `focus_request` を毎 tick 空にする scratch に入れていた | 解けた | §2-3 に `Buffers` を新設した(tick の頭で空にしない・物は 1 回だけ作る)。§2-4 の擬似コードの注・§3-3 の 17 にもある |
| K1 | 段 A は ufunc.at を止めない | 解けた | §2-6 の A ②(`_require_thawed` を配列単位に・`_apply_cash` と同じ形)・D ⑦・§3-2 の段 A。試作では resolve の `np` を代理に替えて真似た。再実行で refractory_until・pois.revenue・holdings の 3 本が `guard_poc.py:107:at` で落ちた(§2) |
| K2 | 旗の直書き 3 か所 | 解けた(代わりの形) | §2-6 の D ⑤ で場所を固定し、B で台帳と在庫の道筋の変化を落とす。1 回目に挙げた「台帳と在庫の窓も系ごとに解く」案は採らず、B(試験のとき)に任せた。挙げた案は任意のものなので、この形で足りる |
| K3 | ビューと別名 | 解けた | §2-6 の D ⑥ と抜け道の表(今は実例なし=推測と明記) |
| K4 | 宣言を観測から作っていた・見えない 55 行 | 解けた(道具は下書き) | §2-5: 宣言の正は静的な閉包、動的な観測は漏れの検査。§1-5 に見えない 55 行(SoA 24・外 31)の扱いを書いた。`resolve_ops` は今も 6 構成の観測から作る下書きで、立たない腕の口は手で足す(§2-5・§6 に明記)。閉包の道具の検査は §3 |
| K5 | 指紋の境目・宣言の外の書きの帰属・stats | 解けた | §2-7: 系ごとの全欄の差(宣言の外の書きも書いた系の指紋に出る)・stats と呼数は試験のときだけ・`BOUNDS` を系に合わせた。境目の 31 行を自分で読み、§2-2 の系の切れ目と合うことを確かめた(L11 = `llm_receive_B` 3916 と `wake_filter` 3920・L12 = `relations_wake` 3955 と `wake_assemble` 3973・L20 = `memory` 4395・`familiarity` 4421・`energy_after` 4426) |
| K6 | 読む宣言を確かめない | 解けた(限界として明記) | §2-5・§0-2: 1-0 では箱の属性の静的な読みだけを AST で確かめる。層の中の読みと実行時の読みは見ない |
| K7 | 試作がループの中だけ | 解けた | §2-4 で drain・close_final・report を系として呼ぶ。試作も守る範囲を広げた。再実行で close_final の負の対照が golden 1 日・v3 2 日で落ち、v3 1 日は書きが起きないので通った(報告どおり) |
| K8 | `talk_stats` の漏れ | 解けた | §2-3 の `RunStats` に `talk_stats`・`intero_cross` を入れた。局所 449 個を箱へ割り当てる表(漏れ 0)を段 C の門にした |
| K9 | 道筋の単位 | 解けた | §0-2 の親の決め・`Access.paths`(`鍵:道筋`)・§3-3 の 11 |
| 記録の誤り 1〜10 | — | 10 件とも解けた | 1 = §1-6 は 4 列。2 = §1-3 の nonlocal は 5 つ。3 = §1-3 の注・§3-3 の 6 の lambda 3 つ。4 = §1-2 L14・§1-3・§2-2 decide・§3-3 の 6・7。5 = §0・§1-6 で例外 3 つを併記。6 = §2-6。7 = §2-7。8 = §2-8 の見出し。9 = jsonl に v3 1 日の行。10 = §4 の flecs と MATSim |
| T1〜T5 | — | 5 件とも解けた(門に入れた) | §3-1 の段 1。T1 は試作で 5 列のうち 4 列を確かめ済み(money は台帳の自前の検査で落ちる)。T2〜T5 は計画で、段 B・C・D の試作が無いことは §6 に明記 |
| §6 の言い換え | — | 合う | §4 |

## 2. 試作の再実行

親の venv・`PYTHONPATH=src`・1,000 体・seed 1。同時に回すのは 4 本まで(`xargs -P 4`)。出力は scratch。18 本とも報告(`guard_results.jsonl` と草案 §2-6 の表)と一致した。

| # | 構成・日数 | 外した列 | 結果 | final・呼数・落ちた所 |
|---|---|---|---|---|
| 1 | v3 既定・1 | — | 通った | `a2edde01b409d6a1`・12,614 |
| 2 | v3 既定・2 | — | 通った | `08013362b035909d`・25,814 |
| 3 | v3 記憶+関係+店+同席・1 | — | 通った | `28a316167605d410`・12,698 |
| 4 | v3 古典+記憶+関係・1 | — | 通った | `a7c16d0fd2d59a0a`・15,836 |
| 5 | v1 edge・1 | — | 通った | `9a7c5f0b66359886`・10,142 |
| 6 | v2 edge・1 | — | 通った | `5c881f69e0894b50`・9,942 |
| 7 | golden の帰無腕・1 | — | 通った | `bee59e96a1849734`・19,144 |
| 8 | v3 既定・1 | world:agents.thermal | 落ちた | environment.py:299 → resolve.py:2742 set_thermal |
| 9 | v3 既定・1 | phase_c:agents.money | 落ちた | ledger.py:502 transfer_many → ledger.py:640 `_apply_cash`(台帳の自前の検査) |
| 10 | v3 記憶+関係+店・1 | decide:agents.mem_last | 落ちた | memory.py:544 `_write` → resolve.py:954 write_memory |
| 11 | v3 記憶+関係+店・1 | relations_wake:agents.rel_last | 落ちた | relations.py:976 → resolve.py:1004 write_relations |
| 12 | v3 既定・1 | decide:agents.refractory_until(ufunc.at) | 落ちた | resolve.py:820 set_refractory → 配列単位の検査 |
| 13 | v3 既定・1 | phase_c:pois.revenue(ufunc.at) | 落ちた | resolve.py:2264 `_complete_buy` → 配列単位の検査 |
| 14 | v3 既定・1 | world:agents.holdings(ufunc.at) | 落ちた | resolve.py:2717 consume → 配列単位の検査 |
| 15 | v3 既定・1 | phase_c:pois.stock | 落ちた | resolve.py:2257 `_complete_buy`(添字の代入) |
| 16 | golden の帰無腕・1 | close_final:agents.transit_state | 落ちた | rail.py:785 → resolve.py:2836 rail_depart |
| 17 | v3 既定・2 | close_final:agents.transit_state | 落ちた | run.py:4590 → runner.py:432 → rail.py:785 → resolve.py:2836 |
| 18 | v3 既定・1 | close_final:agents.transit_state | 通った(書きが起きない) | `a2edde01b409d6a1`・12,614 |

改訂した動的な測り(`dyn_*.json` 6 本)も集計し直した。6 本の final と呼数は上の 1〜7 と同じ。書き手の見えた行 134(SoA 69・外 65)・2 系以上の列 28・行 27。`activity` の 7 系(world・presence・apply_responses・plan_boundary・phase_c・conversation・close_final)・O19 と O70 の 5 系・decide の stats 5 欄(calls_by_cond・layer_counts・n_outside_calls・peak_pending・result)は、どれも草案と一致した。

## 3. 静的な閉包の道具(build_allow.py)

- **再実行**: `rcalls_*.json` と `dyn_agg.json` を scratch に写し、`build_allow.py <scratch> src/shibuya` を回した。出た `allow.json`・`alias_writes.json` は記録のものと同じだった。局所の別名の書きは `('set_refractory', 820, 'cur')`・`('consume', 2717, 'holdings')`、漏れ 0、許可のある系 14。
- **表を通す呼び出し**: たどれる。頂上の代入(`AnnAssign` を含む)の値に出る関数名を表として集め、`{**_APPLY, ...}` の入れ子も開く。関数の中の名前の参照(呼び出しに限らない)を辺にする。resolve.py の `_APPLY`(3107)・`_APPLY_V2`(3127)・`_APPLY_BY_VOCAB`(3151)がこの形であることを読んで確かめた。
- **局所の別名**: たどれる(`x = <...>.<列>` と、その後の `x[...] =` と `np.<ufunc>.at(x, ...)`)。より広い形(`x += `・`x.fill`・`out=x`・`np.copyto(x, ...)`・組の展開・`np.asarray(<列>)`・切り出しの別名)を探す AST を自分で書いて resolve.py に当てた。HEAD では上の 2 か所の外に当たりは無い。今の規則で漏れは無い。
- **手書きの別名の表(alias_writes.json)**: 中身は正しいが、網羅していない。
  - `_complete_buy`・`_complete_eat` → `agents.money`: 正しい。resolve.py:2224・2351 の `led.money.purchase_many` → ledger.py:511 → transfer_many → `_apply_cash` の `np.add.at`。
  - `apply_detection` → 段の 3 列: 正しい。resolve.py:787 `agents.registry.field(crossing.stage_field)[...] =`。
  - 表に無い台帳越しの `agents.money` の書きが 2 つある。`_board_riders`(resolve.py:2092 `out.rail.pay_fares` → rail.py:720 transfer_many → `_apply_cash`)と、`initialize`(:523 `endow_households` → transfer_many)。どちらの関数も `money` を属性で直接書くので、閉包には `agents.money` が入っていて、今の許可は変わらない。表の網羅だけの問題(下の §5 の 1)。
  - `field(変数)` の書きは、apply_detection の外に `initialize` の 539 行(段の列の初期値)と `_restore_array_into` の 3205 行がある。どちらも組み立て(守らない範囲)なので、今は影響しない。
- **道具の限界**(どれも草案の §2-5・§6 に書いてあるか、閉包の性質から来る):
  - 閉包は resolve.py の外へ出る呼び出し(台帳・在庫・`rail.pay_fares`)をたどらない。そこは手の表に頼る。
  - 置き場は式の文字列で決める。同じ名の列(`pois.cell`・`pois.node`)が余分に入る。
  - 閉包は上限なので、許可は観測より広い。例: world は 23 列を許すが、観測では 12 列。閉包の中の「本来書かないはずの列」への書きは段 A では落ちない。「宣言の外」の意味は「閉包の外」になる。

## 4. §0-1 と §0-2 は 1 回目の §6 の言い換えに合うか

- §0-1 のユーザーへの問いは 1 件で、文は 1 回目の言い換え案とほぼ同じ。末尾に「CLAUDE.md §2-6=例示からの手段の変更」の根拠と、「宣言の外の検査の強さは 2 段」の伝えることを添えている。合う。
- §0-2 の親の決め 7 つは 1 回目の判定と合う。合わせ方は次のとおり。
  - 1 回目の 2 番(段 A を本番で既定にする)→ 親の決め。
  - 4 番(粒度)→ 親の決め(道筋の単位)。
  - 5 番(持ち主をまたぐ書き)→ 1-0 では宣言で認め、直す段でユーザーに聞く。
  - 3 番(Phase C)→ §0-1 の説明に含め、§0-2 にも残した。
  - 1 回目の §7 で親に聞いた点(K1 の直しの時期・閉包の表を誰が書くか・指紋に stats を入れるか)にも答えが入った。

## 5. 残る小さな点(切る前に止める理由ではない)

1. `alias_writes.json` に `_board_riders` と `initialize` の台帳越しの `agents.money` が無い(§3)。今は直接の書きで閉包に入っているので、許可は変わらない。表を「AST で見えない書きの全部」にするなら足す。
2. 記録の小さな食い違い: §0 は「8 本の正のランが final 不変で通り」と書くが、§2-6 の表と §5 は「正 7・書きの起きない負 1」。8 本は「通ったラン」の数で、正の対照は 7 本。
3. 閉包は上限なので、許可は観測より広い(world 23 列・観測 12 列)。「宣言の外を書いたら落ちる」の「宣言」が閉包の上限であることを、ユーザーに伝える文(§0-1 の伝えること)に 1 句足してもよい。
4. 段 B・C・D の試作はまだ無い(§6 に明記)。§3-2 の段 A で T1・T2 の負の対照を作るときに、初めて形が確かめられる。
5. `resolve_ops` は 6 構成の観測から作る下書きで、`wake_filter`(fleet の再投入の `clear_refractory`)・`llm_receive`(`_utter` の発話)・`home_meal`・`familiarity` の許可は今は空(§3 の再実行の出力)。手で足すことは §2-5 と §6 に書いてある。T5(19 構成と艦隊・再開の上で段 A を回す)で漏れが見えるはず。

## 6. 再現(リポの根で)

```
D=docs/bench/analysis/wallbounce-1012/run-day-decomp
# 正 7・負 10・書きの起きない負 1 を 4 本ずつ
PYTHONPATH=src .venv/Scripts/python.exe $D/guard_poc.py v3_default 1000 1 decide:agents.refractory_until
PYTHONPATH=src .venv/Scripts/python.exe $D/guard_poc.py v3_default 1000 2 close_final:agents.transit_state
# 閉包の道具(出力は scratch へ。rcalls_*.json と dyn_agg.json を写してから)
PYTHONPATH=src .venv/Scripts/python.exe $D/build_allow.py <scratch> src/shibuya
```
