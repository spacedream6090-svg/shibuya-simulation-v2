# 第 1 期 1-4 規則の表とつなぎの台帳の検収(独立の検収役・実装は見ていない)

- 検収役 Opus 5.5。対象は作業木の枝 `1-4/rules-bridges`(HEAD `136fdbb`+未 commit の変更)。比べた HEAD の src は本体の HEAD `fbe2c06`(`136fdbb` からの差は src・anchors・予算の表・w6 の道具のどれにも無い)。
- 読むだけ。書いたのは本書だけ。作業用の置き場(作業木の `_bc_review/`=byte-check の写しとテープ・負の対照の一時の写し)は終わりに消した。
- 正: [口の約束 1-4](../../../../design/v2-foundation-contracts-2026-10-13.md)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) §1 の 3・[R-106](../../../../research/v2-r106-rights-institutions-tax-credit.md)・[W7 の一次確認](../../../../research/v2-w7-law-primary-check-research.md)・実装役の記録 [README.md](README.md)。

## 判定: 条件つき受入

結果は動いていない(自分の byte-check 4 構成も全欄同じ)。規則の表の写しは R-106 と W7 に合う。台帳は口の約束の 16 件と不応期・起床条件のクラス・W16 の弱点を全部含み、4 つの書き方の中では 1 対 1 が試験で強制されている(自分で植えた負の対照で落ちた)。条件は中 2 件(M1: 4 つの書き方の外にあるコードの宣言、とくに既存の「conf 宣言つきフォールバック台帳」と「繋ぎ」と明記した 3 か所が台帳に無く、記録の説明も実際より狭い / M2: `cli.main` を通らない腕のランが `run_kind=reproduction` になる)について、親が範囲を決めて直すか仮採用として記録に書くこと。

## 1〜8 の確かめ

| # | 項 | 判定 | 根拠 |
|---|---|---|---|
| 1 | 結果不変 | ✓ | 実装役の [byte_check_r14.json](byte_check_r14.json): 19 構成 × 25 欄が全部 same・moved は空。**自分の 4 構成**(下の表)も 25 欄とも同じ。自分の側は 246 行の台帳(第 4 形を足した後)で回したので、実装役が回し直していない「第 4 形の後の byte-check」もこの 4 構成では同じ |
| 2 | 規則の表 | ✓ | 3 行とも出典(法令名・条・版・URL)と `asof` がある。写し検査は下の表で全部一致。2 版で引けることを自分で確かめた。読み手は manifest(`engine/run.py`)と日次の記録(`engine/systems/state_io.py`)だけ(grep) |
| 3 | つなぎの台帳 | △ | 246 行の全部に `remove_at`・`declared_in`・`conf`・`since`(全部 2026-10-14)・`status`(全部 active)がある。計画 §1 の 3 の 9 件・#88 の 6 件・西武の 1 部屋・不応期 11 種・起床条件のクラス・W16 の弱点 3 件は全部あった(漏れ 0)。外す段の分布は記録 §3-3 と同じ(自分で数えた: plan 46・inferred 200・expedient 244・mechanism 2)。`remove_at` は全部 `PLAN_STAGES` の中(読み込みで検査)。ただし `PLAN_STAGES` は手で書いた表で、計画の文書と突き合わせる試験は無い。`5-0`〜`5-6`(計画の字は「第 5 期 空間の段 0〜6」)と `7`(第 7 期には段の番号が無い)は計画に字としては無い(仮採用 4・L9)。計画の 16 件の外の漏れは M1 |
| 4 | コードの expedient との突き合わせ | △ | 下の「数の突き合わせ」。4 形の中の 1 対 1 と負の対照は ✓。4 形の外は M1 |
| 5 | manifest | ✓(M2) | 一番上の鍵は凍結の表と同じ。凍結の表の diff は末尾の `rules_version`・`run_kind` の 2 行の足しだけ。実装役の [manifest_check_r14.json](manifest_check_r14.json): 7 本とも既存の欄 1,730〜2,246 個が同じで、動いたのは `bridges_count`(null → 246)だけ。`run_kind` は `cli.run` の名前つき引数で `run_day` に渡らない(`run_day` の形は不変=頭の `_call_args = dict(locals())` に入らない)。規則(試験 > 腕 > 再現)は `engine/run_kind.py` と試験のとおり。ただし M2 |
| 6 | 守り | ✓ | `Rule`・`Source`・`Bridge` は frozen+slots。`params` は入れ子まで `MappingProxyType` と tuple。`Rules`・`BridgeLedger` は `__slots__` と `__setattr__`/`__delattr__` で止める。`by_id` は `MappingProxyType`、`PLAN_STAGES` は frozenset。自分で 14 通りの書き換えを試し、13 通りが止まった(止まらないのはモジュールの属性の付け替え=Python では止められない。1-3 と同じ扱い) |
| 7 | 試験 | ✓ | 発注の範囲(`-n 2 --dist loadfile -m "not slow"`): **328 passed(69 秒)**。実装役の 329 との差は slow の 1 本(`tests/engine/events/test_e_log_invariance.py` の 100 行目)。範囲の外で触った試験と関わる試験(`tests/engine/test_env_and_sections_10f.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/test_cli.py`): 56 passed(26 秒) |
| 8 | 抜け道 | (a) ✗ (b) ✓ (c) ✓ (d) ✓ | (a) 台帳の JSON を手で書き換えても試験は気づかない(L1)。(b) `remove_at` に `9-9` を書くと読み込みの `ValueError` で落ちる。(c) 記録・JSON・道具・新しいコードと試験に絶対パスとホスト名は無い(あるのは出典の https の URL だけ)。秘密の検査は CLEAN(変更と新規の 31 ファイル)。(d) 新しいコードに「tick」の語と時間の直書きは無い(`NON_ARM_DESTS` の `"ticks"` は既存の CLI の引数の名)。`tests/engine/time` は通った |

### 自分の byte-check 4 構成

`10e/byte_check_10e.py` の `side` を 2 回(HEAD の側=本体の HEAD の `git archive` の写し+祝日の CSV・作業木の側=`--src` で作業木の src を `PYTHONPATH` に)→ `compare`。5,000 体・seed 1・1 日・テープつき。作業木の側は 4 本とも `src_is_worktree` 真、HEAD の側は偽を確かめた。

| 構成 | final(両側) | 呼数(両側) | 25 欄 |
|---|---|---|---|
| `w6_v3_default` | `5f7ae9ff24005314` | 65,597 | 全部同じ |
| `w6_v3_activity_off` | `e0054a837c6ec4c1` | 50,301 | 全部同じ |
| `w6_v1_default` | `24375ee3dab349e8` | 51,835 | 全部同じ |
| `v3_mem_rel` | `73a78288ab5e1498` | 69,111 | 全部同じ |

注: 実装役の 19 構成の compare の JSON には、側ごとの `src_is_worktree` が残っていない(side の JSON は置き場ごと消えた)。だから 19 構成が作業木の src で回ったことは JSON からは確かめられない(本体の venv の editable install は本体の src を指すので、`--src` か `PYTHONPATH` を付けないと作業木の側も本体の src で回る)。manifest の 7 本は作業木の側に `bridges_count` 246 が出ているので作業木の src で回っている。4 構成は自分の側で確かめた(L11)。

### 写し検査(規則の表 → R-106・W7)

| 行 | 表の値 | 突き合わせた先 | 結果 |
|---|---|---|---|
| 消費税 | 国 7.8%+地方 22/78=10% | R-106 の税の表「標準税率」の行(消費税法 29 条 1 号・地方税法 72 条の 83) | 一致 |
| 消費税 | 法令 ID `363AC0000000108`・`325AC0000000226`・版 2026-10-01 | R-106 §0-2 の表の同じ行 | 一致 |
| 消費税 | asof 2019-10-01 | R-106 §6-1「消費税の税率 10%(平成 24 年法律第 68 号・公布から 2019-10-01 まで 2,596 日)」 | 一致 |
| 最低賃金 | 1,280 円・効力 2026-10-01・報道発表の URL | R-106 の出典 #17 の行 | 一致 |
| 最低賃金 | 最低賃金法 `334AC0000000137`・版 2025-06-01・4 条・14 条・note の「4 条 2 項で最低賃金に置き換わる」 | R-106 §0-2・権利の表(雇用)・振り分けの例 | 一致 |
| 深夜酒類 | 風営法 `323AC0000000122`・版 2025-11-28・33 条 | R-106 §0-2 の同じ行(33・34) | 一致 |
| 深夜酒類 | 条例 15 条の逐語・例規集の URL・昭和 59 年条例第 128 号・最終改正 令和 2 年条例第 48 号・00:00〜06:00・住居集合地域 | W7 の表の「深夜酒類提供」の行と出典の行 | 一致 |

2 版で引く(自分で): リポの表の JSON に同じ id の前の版(1,226 円・asof 2025-10-03)を足して `load` → 2025-10-02 は `RuleNotInForce`・2025-10-03/2026-07-13/2026-09-30 は 1,226・2026-10-01/2027-01-01 は 1,280。行の順を逆にしても同じ版を引いた。表の sha は行の順で変わる(文書の sha。不具合ではない)。

### 数の突き合わせ(コードの expedient)

- 発注の grep(`grep -rn 'conf="expedient"\|expedients=\|expedient:' src/shibuya | wc -l`)は 49 行。これは `.pyc` の一致と `engine/bridging/scan.py` 自身の説明を含む。`.py` だけで `engine/bridging/` を除くと、`conf="expedient"` 0 行・`expedients=` 22 か所・`expedient:` 10 行(docstring の段落の頭 5・`#:` の注 2・行頭でない括弧 2・エラー文 1)。記録の A 0・C 5 と合う。B の 139 は 22 か所の中の要素の数(build の段 137)と `WEATHER_EXPEDIENTS` の 2 で、grep の行数とは単位が違う。
- 第 4 形(1 行まるごとの `expedient(…)`)は自分の正規表現で 74 行・71 ファイル。記録と同じ(行頭だけのゆるい数え方は 75)。
- `scan_package` の 218 個と、台帳の `declared_in` が `src/` の行 218 行は欠け 0・余り 0。
- 負の対照(一時の写しに植えた。リポには残していない。植えない写しは 31 passed):
  - `engine/run_kind.py` に `conf="expedient"` の関数を 1 本植えた → 1 対 1 の試験が「台帳に行の無い expedient の宣言: `src/shibuya/engine/run_kind.py#conf:b11e4d5d`」で落ちた。
  - 同じファイルの docstring に `expedient:` の段落を植えた → `#docstring:57227518` で落ちた。
  - `engine/processes/logistics.py` の見出しの下に項を 1 つ足した → 項の数を見る試験 3 本が落ちた。

## 欠陥

### 高

なし。

### 中

**M1 4 つの書き方の外にあるコードの expedient の宣言が台帳に無い(1 対 1 は 4 形の中だけ)。記録の説明は実際より狭い。**

- src の `.py` で expedient を含むもの 121 本(`engine/bridging/` を除く)のうち 32 本は、4 形の宣言を 1 つも持たない。そのファイルの expedient には台帳の行が無い。主なもの:
  - `world/processes/first_batch.py`: 世界過程の宣言 16 本が `mechanism=False`+`sensitivity_test_id`+`repayment_due`(CLAUDE.md §4 の mechanism|expedient のタグ)。`Registry.fallback_ledger()` が出す既存の「conf 宣言つきフォールバック台帳」は 5 行(`executor=engine_rule`・`conf` 0.3〜0.6・返済期限: `rail_operation_static`・`store_opening`・`vehicle_cross_section`・`hotel_room_inventory`・`large_event`)。CLAUDE.md §3 の「エンジン規則でつなぐ(conf 宣言つき・カバー率を台帳へ)」の台帳そのもので、新しい台帳はこれと結ばれていない(`delivery_inbound` だけが `BR-DELIVERY-INBOUND` として別にある)。実装のモジュールの見出しの行(goods_flow・civic・logistics・traffic・rail・opening)が一部を含むが、宣言の正(`repayment_due`)とは 1 対 1 でない。
  - `engine/chooser.py`(習慣の確率 p_h・走査の揺らぎ τ=感度つきの宣言)・`engine/relations.py`・`engine/store_memory.py`・`agents/weekly.py`(`#: expedient(自前の写像・登録簿 §8 D-62)`)・`build/geo/poi_class.py`(名前一致の層)。
- コードの docstring が自分で「繋ぎ」と書いているのに行が無い 3 か所: `agents/population.py` の `start_cell`(「W17(週次スケジュール)が入るまでの繋ぎ(expedient)」)・`engine/run.py` の 1604 行目付近の同じ繋ぎ・`llm/mock.py`(「行為の分布の錨は D-119 の古典モデルが来るまでの繋ぎ(expedient)」)。
- 記録 §4-3 と §8 の「`mechanism=False` の 44 欄は成長の宣言(`core/soa.py`)のタグ」は、`world/processes/first_batch.py` の 18 か所(世界過程と関係の宣言・返済期限つき)には当たらない。
- 4 形の外で expedient を含む行の数も記録に無い。自分の数え(`engine/bridging/` を除く): expedient を含む行 695 のうち、見出しと段落の頭の行 79 の外に、`#` で始まる注 274 行・そのほかの行 306 行(行末の注・docstring の文・文字列。`expedients=` の 22 行を含む)・ほか 36 行(未リサーチの注記 16・見出しの下の項 13・契約のタグ 5・行頭でない括弧 2)。記録の表にあるのは 17・5・44・6 の 4 つだけ。
- 直し方(範囲は親の判断): (a) 第 5 形として世界過程の宣言(`mechanism=False` か `executor=ENGINE_RULE` の行。AST で `repayment_due=` を持つ呼び出しを数えるか、`first_batch.build_registry()` から id ごとに 1 行。`declared_in` は `src/shibuya/world/processes/first_batch.py#process:<id>` の形)を足し、既存のフォールバック台帳と結ぶ。`repayment_due` の古い語(Phase 3・第2陣・第3陣)は計画の段に読み替える(多くは 6-6)。(b) 「繋ぎ」と明記した 3 か所は docstring の `expedient:` の段落にするか文書の行で台帳に入れる。(c) 記録 §4-3 に「4 形の外の行の数」と「宣言の形が 1 つも無いファイル 32 本」を書き、「1 対 1 は 4 形の中だけ」と明記する。(d) `#:` の注を数えるかは親の判断(数えると数百行増える)。

**M2 `cli.main` を通らない腕のランが `run_kind=reproduction` になる。**

- 実装役の manifest の 7 本のうち、記憶+関係(`v3_mem_rel` ×2)・古典+記憶+関係(×2)・帰無腕(`w6_golden_null_arm`=`plan_executor=False`・`report_precondition=False`)はどれも `run_kind=reproduction`。byte-check・10e・C7 などの道具はどれも `cli.run` を直に呼ぶので、腕の実験の manifest の多くが「再現」と記録される。発注の規則「切替口の腕が on なら arm」は `cli.main` の中でしか効いていない。
- 記録 §5-1 と台帳の `BR-RUN-KIND-CLI-ARMS`(外す段 3-3)で宣言はしてある。それでも manifest の欄に誤った値が入るのは、空より悪い。
- 直し方: `cli.run` で `run_kind` が渡されないときは、渡された引数を `run`・`run_day` の既定(`inspect.signature` と `CLI_DEFAULT_*`)と比べて腕を決める(`NON_ARM_DESTS` に当たる `run_day` の引数名の表を足す)。それまでの間は、決めていないランの `run_kind` を null にする案もある。

### 低

- **L1 台帳の sha の凍結が無く、manifest に台帳の版も無い**(8 (a))。一時の写しで `BR-SEIBU-ONE-ROOM` の `remove_at`(7 → 2-1)と `what`、`BR-THINK-ALPHA` の `remove_at`(6-7 → 1-5)と `remove_basis`、`HD-core.soa-1` の `remove_at` と `why` を書き換えた → 31 passed。文書の行を 1 行足しても 31 passed。manifest は件数だけなので、件数が同じ書き換えはランの記録から見分けられない。直し方: manifest に台帳の正規化した sha(例 `bridges_version`)を足す(CP10 の「版とハッシュ」)か、試験に台帳の sha の golden を置いて、変えたら理由を記録に書いて更新する(10f の `CONFIG_PATHS_SHA256` と同じ形)。
- **L2 `status=removed` が使えない**。試験は全行 active を求める(`len == count`)。`code_mismatch` はコードの行を status に関わらず数えるので、外したつなぎを removed で残すと、コードから消した宣言が「余り」で落ちる(一時の写しで 1 行を removed にすると落ちた)。直し方: removed の行は突き合わせの外にし、試験は active と removed の数を別に見る。
- **L3 `since` の固定**。試験が全行の `since == "2026-10-14"` を求めるので、後で足す行は試験を直さないと入らない(一時の写しで since 2026-11-01 の行を足すと落ちた)。直し方: 2026-10-14 以後の日付であることだけを見る。
- **L4 二重の数え**。下の「二重に数えている 7 行の判断」。
- **L5 第 4 形の id がファイルの中の何個目かで決まる**。見出しを上に 1 つ足すと、同じファイルの後ろの行の id が全部ずれる(例 `engine/resolve.py` の 4 行)。台帳の履歴の id が安定しない。直し方: id は付けた後は固定にし、試験は id と宣言の結び(`declared_in`)だけを見る。
- **L6 見出しの行の `remove_at` が項の 1 つにしか合わないことがある**。例: `HD-engine.processes.opening-1` は 1-5 で、合うのは 1 項目め(担当の丸振り)だけ。残り 3 項(日跨ぎの畳み方・REPLACEMENT の語・5 分刻み)は 1-5 では外れない。`HD-agents.state-1` は 16 項で `7`。直し方: 見出しの行は「項のうち最も遅い段」を `remove_at` にするか、記録に「見出しの行の `remove_at` は代表の項」と書く。
- **L7 規則の表の 3 行に対応する既存の直書きが、表の id と結ばれていない**。`economy/anchors.py` の `MIN_WAGE_HOURLY = 1_226`(世界の時点の値)は `HD-economy.anchors-1`(外す段 2-1・賃金の式の項)の中にあるだけ。口の約束の約束 (1)「既存の直書きの係数は 4-2 まで残す=つなぎとして台帳へ」に合わせ、規則の id(`minimum_wage.tokyo`)を書いた行を 1 つ足す(外す段 4-2)。深夜酒類は `W7#9`(4-2)で足りている。消費税はコードに無い。同じ見出しには、計画 §5-3 が「つなぎの台帳に載せる(外す段=2-1)」とした財布の初期値(D11)も入っているが、`why` に「検証専用の家計調査を構築に使っている形」(パターン台帳 §10-1)が書かれていない。
- **L8 読み手の AST の試験に穴がある**。`test_only_the_manifest_and_the_daily_record_import_the_table` は `from shibuya.engine import rules` と相対 import(`from .rules import table`)を数えない。直し方: `ImportFrom` の module と names を合わせて見て、level も見る。
- **L9 `PLAN_STAGES` と計画の文書の突き合わせが無い**(手の表)。`5-N` は計画の §5-N や CP5-5 と字が重なる。直し方: 空間の段を `S0`〜`S6` などにするか、試験で計画の文書の段の番号を引いて閉じた表と比べる(仮採用 4 の判断と一緒に)。
- **L10 台帳の JSON が壊れていると、日の締め(日次の記録)で初めて落ちる**。1 日分を回した後に止まる。直し方: ランの始め(build)で 1 回読む。
- **L11 byte-check の compare の JSON に側ごとの `src_is_worktree` が残らない**(10e の道具の形)。直し方: compare に両側の `src_is_worktree` を写す(範囲の外=親の判断)。

## 「二重に数えている 7 行」の判断(親の依頼)

- **判断: 1-4 ではこのままでよい(仮採用のまま)**。ただし「`bridges_count` は台帳の active の行の数=宣言の数で、一意のつなぎの数ではない」と、記録 §3-3 と台帳の `note` に 1 行書くこと。理由: 7 行(`w7_planspec`・`w8_visibility`・`w10_noise`・`w13_weather`・`w14_signage`・`w15_cell_static`・`sched/trial`)は同じファイルの第 2 形の要旨で、外すときは同じ段で両方を消す。だから件数の増減(計器の向き)は正しく動く。消すと見出しの 1 対 1 の規則に例外が要る。
- **ただし二重は 7 行だけではない**。文書の行とコードの行の重なりも同じ型で、`why` に書かれていない: `BR-K9-MONDAY` ↔ `W17#2`(「1 日モード(月曜 d0 のみ)」)・`BR-E4-EXIT-VANISH` と `BR-ATTENDANCE-LOTTERY` ↔ `HD-engine.presence-1` の E4・E6 の項・`BR-W12-HOLIDAY-GT-WEEKDAY` ↔ `W12#4`〜`#8`(等間隔のダイヤ)・`BR-W17-IO-SLEEP` ↔ `HD-engine.presence-1` と W17 の行。記録 §3-3 の「二重に数えない」は #88 の 4〜6 だけの話で、台帳全体では成り立たない。
- 2-0(計器の器)で件数を計器に出す前に、行に重なる行の id(例 `overlaps`)を持たせ、一意の数も出すのがよい(親の判断)。

## 親に確かめてほしいこと

1. M1 の範囲: 世界過程の宣言(`first_batch` の 16 本と既存のフォールバック台帳 5 行)と「繋ぎ」と明記した 3 か所を 1-4 で台帳に入れるか、仮採用として記録に件数を書くだけにするか。
2. M2: `cli.run` に腕の判定を足すか、決めていないランを null にするか。
3. 発注の範囲の外の直し `tests/engine/time/test_t0_tm9_fields.py`(3 か所)は、発注の「null を件数に」から必ず要る直しで、T0 の約束(TM9 の 4 つは続きの並び・その後ろに足すだけ)も保っている。検収役は認めてよいと読む。
4. 仮採用 4(段 `7`・`5-N`)と 5(inferred の 200 行)の当て方。第 4 形の 74 行の当て方はまだ親が見ていない(記録 §8 の 5)。L6 のとおり、見出しの行の `remove_at` は代表の項にしか合わないものがある。
