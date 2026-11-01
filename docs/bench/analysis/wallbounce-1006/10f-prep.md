# 10f の材料: 環境の欄・salt の道具・AST の検査を外の状態に・K19・保存の形式(2026-10-06)

> 実行役(Opus 5.5)の記録。親の検収の前。commit していない。src は 1 文字も変えていない(読むだけ・同じプロセスの中で関数を包んで数えただけ)。
> 先に読んだもの: [D-102 の土台のアジェンダ](../../../design/v2-d102-foundation-implementation-agenda.md) §0 の 10f・§7・§9 / [指示書 10-03](../../../design/v2-wallbounce-decisions-2026-10-03.md) §6 ⑨・⑮・⑯ / [R-71](../../../research/v2-r71-stochastic-comparison-statistics.md) / [設計書 再開と決定論](../../../design/v2-resume-determinism-draft.md) §1・§5・§6 / 10b・10c・10d の記録と [review-10c.md](../wallbounce-1003/review-10c.md)。
> 印: **事実**=コードを読んだか測った値。**材料の案(expedient・未リサーチ)**=実行役の自前の構成で、先行研究を調べていないもの。R-71 から写した手順は「R-71 §n」と書く。
> 測った機械: この機械(Windows 11・x86-64・論理 CPU 20)。Python 3.12.10・numpy 2.5.3・numba 0.67.0。パスは `src/shibuya/` を省略し、絶対パスは書かない。計測の出力(JSON)は一時ディレクトリに置いた(リポには置いていない。手順は §8)。

## 0. 要点

1. **環境の欄**は状態のファイルの見出し(`platform`)にだけあり、ランの manifest(`run_manifest_fields`)・checkpoints の JSON・テープの `run_meta.json` には無い。見出しにも numba の版・git の commit・CPU の命令セット・依存の固定は無い。依存の lock ファイルは無く、`pyproject.toml` は下限だけ(`numpy>=2.1` など)。golden の値(テストの 4 つの辞書)は環境で分けていない(§1)。
2. **salt の道具**: 「腕 × salt で回して差・幅・差 ÷ 幅を出す」道具は**まだ無い**。近いのは `tools/c7/seed_exchangeability.py`(seed 以外が同じかの検査)と `seed_ensemble.py`・`prereg_v13.py`(在圏の 3 seed の家族 95%)。`seed_exchangeability` を今の manifest で回すと、既定 v3 の seed 1 と 2 で**未説明の差が 313 欄**(21 群)出て交換可能性は FAIL になる。21 群はどれも観測の値で、設定の差ではない(§2-2)。1 本は mock 5,000 体の 1 日で 28.0〜30.4 秒。3/5/3 本で 1 つの腕を基準と比べると 6/10/6 本、約 3/5/3 分。R-71 の両側 α=0.05 の下限 6 対なら 12 本・約 6 分(§2-4)。
3. **AST の検査を外の状態に広げる**: 10d で漏れた 15 項目(14+1)のうち 12 項目は、持ち主のクラスの中の `self.x` でしか読まれない(うち 2 項目は自己更新の `+=` だけ)。持ち主の外で読まれるのは `conv.n_opened`(`getattr` の文字列 1・属性 3)・`n_transfers`(属性 1・`getattr` 1)・`named_closed`(閉包の中の属性 1)の 3 項目だけ。漏れの主因は軸 2(戻す要るか)の誤りで、読み手の AST では軸 2 は捕まらない。「`__init__` の外で書き換わる属性」の規則なら 14/14 を拾うが、候補が 351 個出る(当たり 4%)。軸 2 には実行時の検査が向く(§3)。
4. **K19**: `stream()`・`philox()` の呼び手は AST で 31 か所(ほかに httpx の `stream` の誤検出 1)。静的に語数が決まらないものが 16 か所で、AST だけでは判定できない。実行時に `core.rng.philox` を包む計器(src は不変・final も不変)で 1 日を数えると、既定 v3 で**実際のブロックの重なり**が `w16.sample.stratum` 185・`body.weight` 1・`body.eer` 1、counter ×1000 で `perception.p_notice` 1,729 出た。10c の検収の実測(372 本・最大 2,602 ブロック・1,487 ブロック・2 ブロック・`body.*` の 1 体ずつ)を再現した(§4)。
5. **保存の形式**: 既定 v3 5,000 体の日の境目の保存 4,302,954 B のうち、**配列が 92.5%**(SoA 0.87 MB+外の状態の中の配列 3.11 MB)。外の状態 169 道筋のうち、そのまま npz か json になるのは 152、型が落ちるものが 4、印が要るものが 11(集合・タプルの鍵の辞書・dataclass・Generator など)、値のクラス 2。試作の npz+json は非圧縮 4.45 MB(+3%)・圧縮 1.03 MB(−76%)で、書き 17 ms・読み 11 ms(組み立て直しを除く)。同じオブジェクトを 2 か所から指すものは 2 つ(凍結した `Target` と、`_last_close.flow` と `_flow_daily[0]` の配列)(§5)。
6. **予算**: 環境の欄・AST の検査・保存の形式の変更はどれも 1 秒前後か、1 日に 1 回の数十 ms。salt の道具の時間はほぼ全部がランの本数で決まる。CRN の健全性の検査を毎 tick の checkpoint で行うと、1 本が約 29 秒 → 約 75 秒/日になる(10d の記録から)(§6)。
7. 材料の案は 14 件(§1-4 の 3・§2-5 の 4・§3-5 の 3・§4-4 の 2・§5-5 の 2)。

## 1. 環境の欄

### 1-1 今どこに何があるか(事実)

表 1: 環境と同定の欄の置き場。○=ある・×=無い。

| 欄 | `run_manifest_fields`(checkpoints の JSON の `manifest`・`cli.py:502`) | テープの `run_meta.json`(`engine/tape.py:93`) | 状態のファイルの見出し(`engine/resume.py:148` `platform_fields`) | `manifest/schema.py` の `RunManifest`(定義だけ。ランは出さない・テスト 2 本だけが使う) |
|---|---|---|---|---|
| Python の版 | × | × | ○ `python`(例 3.12.10) | × |
| numpy の版 | × | × | ○ `numpy` | × |
| numba・llvmlite の版 | × | × | × | × |
| blake3・xxhash・pyarrow の版 | × | × | × | × |
| OS | × | × | ○ `os`(`platform.system()`=Windows。版は無い) | ○ `Hardware.os` |
| machine | × | × | ○ `machine`(AMD64) | × |
| CPU の型・命令セット | × | × | × | ○ `Hardware.cpu`(文字列) |
| スレッド数 | × | × | △ `numba_threads` は環境変数 `NUMBA_NUM_THREADS` の文字列。未設定なら空(この機械で実際の numba のスレッドは 20) | × |
| git の commit・dirty | × | × | × | ○ `Code.commit`・`dirty`(較正・holdout で dirty を拒む規則 (a)) |
| 依存の固定(lock の指紋) | × | × | × | × |
| 設定の指紋 | ×(欄ごとの値はある) | × | ○ `fingerprint`(パスの文字列ではなく中身で同定・10d 検収 L3) | ○ `Settings.normalized_blake3` |
| データの同定 | ○ `registry_hash`・`catalog_sha16`・`frozen_sources`・`calendar` | × | ○(指紋の中の `world_dir` の中身) | ○ `DataAsset` |
| 乱数の方式 | ○ `rng_scheme`(10c) | ○ `rng_scheme`・`response_delay` | ○(指紋の中) | ○ `Rng.scheme`(`numpy-philox4x64`=別の意味・10c 検収 Q1) |
| tick の長さ・開始日 | ○ `tick_seconds`・`start_sim_datetime` | × | ○ `progress.ticks_per_day` | ○ `Settings` |
| 決定論のモード(⑨ の厳密/記録だけ) | × | × | × | ○ `Identity.mode`(smoke/calibration/holdout/ablation/production。⑨ の 2 つのモードとは別の軸) |

- 「版の台帳」は、設計書(再開と決定論 §1)では「既定 checkpoint の版の台帳にプラットフォーム欄を足し、値はプラットフォームごとに持つ」とある。今の golden の値はテストの辞書 4 つ(`tests/engine/test_presence_executor.py` の `W17_GOLDEN`・`tests/perception/test_near_tiebreak.py` の `CLASSICAL_1500_GOLDEN`・`tests/engine/test_relations_tenure.py` の `REL_ON_5000_GOLDEN`・`tests/engine/test_presence_derive_v2.py` の `REAL_GOLDEN`)で、どれも環境の鍵を持たない。アジェンダ §5 の 10e の「golden 13 値」はこのうちの 3 つ(`W17_GOLDEN` 8・legacy 2・`CLASSICAL_1500_GOLDEN` 3)。
- **依存の固定**: lock ファイル(`requirements*.txt`・`uv.lock`・`poetry.lock`・コンテナの定義)はリポに無い。`pyproject.toml` は下限だけ(`numpy>=2.1`・`numba>=0.61`・`blake3>=1.0` など 11 本)。この `.venv` の `pip freeze` は 47 行。

### 1-2 結果のビットに効きうる環境(事実と推測を分ける)

| 項目 | 事実 | 読み |
|---|---|---|
| numba | 使うのは `engine/change_detect.py` の nogil のループ 1 本。numba が無い環境では NumPy 版に落ち、結果はバイト一致(テストで検査)。`parallel=True`・`prange`・`fastmath` は src に無い | スレッド数は今のエンジンの結果に効かない見込み(推測)。numba の版・有無は記録しておけば足りる |
| BLAS | src(`build/` を除く)に `np.dot`・`matmul`・`einsum` は無い | OpenBLAS のスレッド数も今は効かない見込み(推測) |
| numpy の SIMD の振り分け | この機械の基線 `X86_V2`・実行時の振り分け `X86_V3`(AVX2・FMA3 など) | numpy は CPU の命令セットで超越関数などの経路を切り替える。機械が変わると浮動小数の末尾が変わりうる(**未確認**: numpy の文書で一次確認が要る)。命令セットを欄に入れる候補 |
| blake3・xxhash | ハッシュ(final・behavior・full)と艦隊の呼ごとの seed(`xxh64(call_id, run_seed)`・`llm/fleet.py:266`) | 版が変われば値が変わりうる(規格どおりなら変わらない・推測) |
| Python の `dict`・`set` の順 | 状態のハッシュは辞書を鍵の昇順で流す(順が挙動の行 O8・O39 は挿入順)。集合は要素の直列化の昇順 | 文字列のハッシュの乱択(`PYTHONHASHSEED`)は今の直列化には効かない見込み(推測) |

### 1-3 「同じ環境で 2 回回して一致・別の環境の値は別の行」の今の実績(事実)

- 今日の 4 本(既定 v3・seed 1・5,000 体・1 日。素の 1 本・状態を書く 1 本・乱数の計器で包んだ 2 本)の final はすべて `993276d5e5bb5cbe`、呼数 69,978。
- 10b〜10d の byte-check は、同じ機械で HEAD の写しと作業木を比べる形(19 構成)。別の環境の値は 1 つも記録されていない(サーバーの返却の後、別の機械が無い)。

### 1-4 検査の形の候補(**材料の案(expedient・未リサーチ)**・3 件)

1. **環境の ID**: `platform_fields()` を広げ(Python・numpy・numba・llvmlite・blake3・xxhash・OS と版・machine・numpy の実行時の振り分けの集合・numba の実際のスレッド数・git の commit と dirty・lock の指紋)、その正準の JSON の blake3 の頭 16 桁を `env_id` とする。`run_manifest_fields` と状態の見出しとテープの `run_meta.json` に同じ値を書く。
2. **golden を環境の行で持つ**: golden の辞書を `{env_id: {値…}}` にし、テストは今の `env_id` の行があれば比べる。無ければ「この環境の値が無い」と出して、同じ設定の 2 回のランの一致(A/A)だけを検査する(設計書 §1 の「CI(別機)では同一プラットフォームの値と比べるか、同 salt 2 回の一致で検査する」の形)。新しい環境の行は、A/A を通した値を人が足す。
3. **依存の固定**: `pip freeze` の写しを lock として置き、その sha256 を `env_id` に入れる。コンテナ化(⑯)はその上に載せる。lock の道具(pip-tools・uv など)の比較はリサーチしていない。

## 2. salt の道具

### 2-1 今ある道具(事実)

表 2: salt(=`seed`)をまたいで比べる道具。このリポでは salt は `seed`(`master_seed`)で、`run_salt` は seed から作る(`engine/run.py:593`)。**seed を変えると母集団の抽出も変わる**(`population_hash` が seed 1 と 2 で違う・§2-2)。

| 道具 | 何本 | 出すもの | 差 ÷ 幅 |
|---|---|---|---|
| `tools/c7/seed_exchangeability.py` | 2 本以上 | checkpoints の JSON の manifest を平坦化して、seed 以外の差を「許容 `ALLOWED_DIFF`」「宣言した同値 `--equivalent`」「未説明」に分ける。必須欄(`n_agents`・`ticks`・`schema`)と checkpoint の tick 列の一致。4 つのハッシュの seed 間の同一性を報告。任意で 0 時の在圏 | なし |
| `tools/c7/seed_ensemble.py` | N 本(既定 3 本・サーバーのラン) | 在圏(5 エリア × 時)の CV・対ごとの JSD の平均(帰無の参照)・家族 95% の半幅 t(0.995, n−1)·CV/√n・fair CRPS の係数・N=(CV/r)² | なし(腕の比較ではない) |
| `tools/c7/prereg_v13.py` | 3 本 | H1〜H5 を家族 95%(Bonferroni α=0.01/指標)の区間で pass/fail/undecided。undecided を解く本数の探索 | なし(線との比較) |
| `tools/c8/ablation_runner.py` | 1 腕 1 本 | 腕の定義表と実行・M1〜M3 | なし |
| 各記録の計測スクリプト(`w6_regen_measure.py` など) | 1 本(seed 1) | 腕ごとの要約 | なし |

- **`ALLOWED_DIFF` の中身**(`seed_exchangeability.py:29`): `seed`・`run_id`・`final_hash`・`manifest.fleet.cache_salt`・`manifest.fleet.run_id` の 5 つ。使い手は同じファイルの `compare` だけ(テストは `tests/c7/test_seed_exchangeability.py`)。
- 「差・幅・差 ÷ 幅」の 3 列は設計書 §5 の報告の形で、道具はまだ無い。幅の定義は設計書では「salt 間の幅(家族 95%)」。`prereg_v13` の半幅 t(0.995, n−1)·SD/√n がそれに近い(差 ÷ 幅の幅に同じ式を使うかは未決)。

### 2-2 `seed_exchangeability` を今の manifest で回した結果(事実)

既定 v3・5,000 体・1 日・seed 1 と 2(`probe_runs.py` で回した checkpoints の JSON)。

- 結果: `exchangeable=False`・許容の差 3(`seed`・`run_id`・`final_hash`)・**未説明 343**(うち 30 は計測スクリプトが足した `probe.*` の欄なので、manifest の未説明は **313**)。
- 313 欄の群: `energy` 114・`group_norms` 73・`intent` 20・`action_usage` 13・`decision_layers` 13・`p_see_activity` 11・`state_hashes` 11・`intero_crossings` 10・`target_resolution` 10・`presence_exit` 8・`calls_by_condition` 7・`activity_kind_counts` 5・`leave_effects` 4・`move_resolution` 4・`near_tiebreak` 3・`state_hashes_end_of_day` 3・`waste_sink` 3・`daily` 1・`l4_conversation_share` 1・`llm_calls_per_agent_day` 1・`llm_calls_total` 1(計 21 群)。**どれも観測の値**(件数・分布・ハッシュ)で、設定の欄の差は 0。
- 4 つのハッシュ(`population_hash`・`schedule_hash`・`world_hash`・`agents_hash`)は seed 間ですべて違う(`population_seed_independent=False`)。
- 読み: 道具を作った時(第217)より manifest に観測の欄が増え、許容の一覧では追えなくなっている。10d の問い 7 (c)(`daily`・`resume` は seed で変わる欄)もこの形の 1 つ。

### 2-3 CRN にするには乱数の流れのどこを揃えるか(事実の分類)

CRN の対=同じ salt で基準と腕を回すこと。用途の鍵 × カウンタの形(`core/rng.py`)なので、多くの流れは「同じ (tick, 体) の同じ決定なら同じ乱数」になる(R-71 §1-4 の「決定ごとの流れ」)。

表 3: 流れの鍵の形と、腕で同期が崩れるか。

| 鍵の形 | 用途(例) | 腕の間の同期 |
|---|---|---|
| seed だけ・日の鍵だけ | `w16.sample.stratum`(母集団)・`wallet.initial`・`body.weight`・`body.eer`・`world.delivery_inbound`・`world.road_works`・`world.large_event`・`engine.processes.rail`・`agent.schedule` | 腕に依らず同じ(腕が母集団・世界・日課を変えない限り完全に揃う) |
| (tick, 体)・(tick, 体, 起床級) | `engine.chooser`・`policy.classical`・`conversation.invite`・`llm.mock`(移動・店の対象を含む)・`perception.attention.p_see`・艦隊の seed `xxh64(call_id, run_seed)`(call_id=`T:体:起床級`) | 揃う。腕で起きない体の乱数は使われないだけで、ほかの体の列はずれない |
| 状態を持つ流れ(stateful) | `world.salient`・`world.public_service_dispatch`(既定 `--rng-scheme stateful`) | **崩れる**。腕で引く回数が変わると、それ以後の列が全部ずれる。counter にすれば (T)・(T, セル, k) の鍵になる(10c) |
| 「同じ tick の何番目か」の通し | `perception.p_notice`(1 語目=その tick の事象の番号)・出動の k(同じ (T, セル) の何番目か)・顕著行為で選ぶ体(在圏の体の集合から選ぶ) | **腕で事象の数や順が変われば番号がずれる**(部分的な CRN) |
| LLM の応答 | 実 LLM | バッチの組み方で出力が変わる(R-71 §1-5)。mock は (tick, 体) の鍵なので揃う |

- **改変の時刻 T0 の扱い**: 腕が最初から違う比較(T0=0)では、最初の checkpoint から状態のハッシュが違う(R-71 §8-1 の確認 2 は T0>0 の反実仮想だけに意味がある)。T0>0 の分岐を作るには、基準を T0 まで回して状態を書き、腕の設定で再開する形が自然だが、**今の再開は設定の指紋が親と違えば止める**(`engine/resume.py` の `fingerprint`・10d §4-2)。分岐のために「宣言した欄だけ違ってよい」口が要る。

### 2-4 時間の見込み(事実の実測と、それからの掛け算)

表 4: mock 5,000 体・世界資産・1 シミュ日の壁時計(この機械・1 本ずつ直列)。

| ラン | 壁時計 |
|---|---|
| 既定 v3・seed 1(素) | 28.0 s |
| 既定 v3・seed 2(素) | 29.9 s |
| 既定 v3・seed 1(テープ+状態の書き出し・2 日のランを T=1440 で止める) | 30.4 s |
| 既定 v3・seed 1(乱数の計器で包む・2 回) | 29.4 s・27.5 s |
| counter・率 ×1000・seed 1(乱数の計器で包む) | 36.1 s |
| import | 0.63〜0.66 s |
| 参考: 既定 v3・2 日・毎 tick の checkpoint・テープ(10d の記録) | 149.4 s(1 日 約 75 s) |

表 5: 1 つの腕を基準と比べるときの本数と時間(1 本 29 s・直列で計算)。基準のランは同じ salt の組なら複数の腕で共有できる(k 本の腕なら n(k+1) 本)。

| 比べ方 | 本数(基準+腕) | 直列の壁時計 | 両側の p の下限(R-71 §2-3) |
|---|---|---|---|
| 3 salt(主要な腕・設計書 §5) | 6 | 約 2.9 分 | 0.25(検定にならない) |
| 5 salt(希少な量) | 10 | 約 4.8 分 | 0.0625(両側 α=0.05 に届かない・片側なら 0.031) |
| 6 対(両側 α=0.05 の最小) | 12 | 約 5.8 分 | 0.031 |
| 8 対(Holm で指標 5 本) | 16 | 約 7.7 分 | 0.0078 |
| 6 対+毎 tick の checkpoint(CRN の最初の食い違いの tick を出す) | 12 | 約 15 分(1 本 75 s) | 0.031 |
| 39 万体 3 salt | 6 | **未計測**(この機械で 39 万体の 1 日を回していない) | 0.25 |

- 並べ替え検定の計算(全部の符号の組を数える)は無視できる: 2^8=256 通りで 0.03 ms、2^12 で 0.36 ms、2^20 で 254 ms(この機械)。
- 並列に回したときの伸びは測っていない(10b は並列 3 本の負荷で checkpoint の時間が伸びたと記録)。

### 2-5 R-71 の手順を道具の仕様に落とすときの要点

R-71 §8-1 の入出力の案(親の案)を前提に、仕様にするとき決める必要があるもの。

1. **本数と出力の線**(R-71 §2-3): 両側 α=0.05 は 6 対から、片側は向きを事前に登録して 5 対から。3/5/3 本(設計書 §5・指示書 ⑦ 7-4 は「今のまま」)では検定は成り立たず、道具は「記述のみ(本数不足)」と出す。p の下限は全部の符号の組を数えた 2/2^n。
2. **ρ の実測**(R-71 §1-1): 対ごとに差の分散 Var(D) と各腕の salt 間の分散を出し、比 Var(D)/(Var(X_基準)+Var(X_腕)) と ρ を出す。比が 1 を超えたら警告。3 対では分散の推定の幅が広い(SD の 95% 区間が推定値の 0.52〜6.28 倍・R-71 §5-1)ので、ρ の値は 5 対以上で読む。
3. **D-46 の式の訂正**(R-71 §5-1): N=(CV/r)² は**相対の標準誤差**を r にする本数。95% の区間の半幅を r にするなら t を入れて解く(CV 0.0325 で r=2% は 13 本、1% は 44 本)。道具は 2 つを別の名前で出す。差を比べるときは各腕の CV ではなく対の差の SD で本数を決める(R-71 §5-4)。
4. **区間**(R-71 §4-2): n ≤ 10 では対の差の t 区間と、並べ替えを反転した区間(到達した水準を明記・n=5 では 95% は作れない)を並べる。百分位のブートストラップは使わない。
5. **効果の大きさ**(R-71 §4-1): 差の生の値・基準に対する比・差の SD を主に出す。d_z は「CRN の対の d_z」と明記して CRN の無い比較と並べない。d_av も出す。
6. **多重比較**(R-71 §6): 主要な指標を 1 つ事前登録。副次は Holm、探索は BH。Holm で指標が増えると本数の下限が上がる(5 本で 8 対)。
7. **CRN の健全性**(指示書 ⑮・R-71 §1-6): (a) 入力の一致(manifest の差が腕の欄だけ)(b) T0 より前の checkpoint の behavior-hash の一致(c) T0 以後の最初の食い違いの tick と部品(10d の `first_diff.py` が近い)(d) A/A。(a) は §2-2 のとおり今の `seed_exchangeability` では使えない。
8. **「二重の並べ替え検定」が何を指すか**は R-71 §3-3 で未確定(Farine & Carter 2022 の double permutation か、走の中のノードの並べ替え × 走の間の符号反転の 2 段か)。ユーザーへの確認が残っている。

**材料の案(expedient・未リサーチ)・4 件**

1. **manifest を「設定」と「観測」の 2 つに分ける**(`run_manifest_fields` の中で節を分けるか、観測の欄の接頭辞の一覧を道具が持つ)。交換可能性の検査は設定の節だけを比べる。今の 313 欄を許容の一覧に足す形は、欄が増えるたびに壊れる。
2. **salt の意味を分ける**: 今は seed を変えると母集団の抽出も変わる。「同じ母集団で動きの乱数だけを変える salt」を別の引数にするか(母集団の seed と動きの seed)。設計書 §5 の 3 本の根拠(salt 間 JSD)は母集団の抽出の違いを含んだ値。
3. **分岐の口**: T0>0 の反実仮想は「基準を T0 まで回して状態を書く → 腕の設定で再開」で作る。再開の指紋の検査に「宣言した欄だけ違ってよい」を足す(10d の再開の口の再利用)。
4. **CRN の最初の食い違い**: 毎 tick の checkpoint は 1 本 約 75 s に伸びるので、既定は 60 tick ごとに比べ、食い違った区間だけを毎 tick で回し直して tick を絞る(2 分探索)。

## 3. AST の検査を外の状態に広げる

### 3-1 10b の検査の範囲(事実・`engine/state_ledger_ast.py`)

| 見ているもの | 見ていないもの |
|---|---|
| SoA の列(agents 79・cells 5・pois 9・知覚 5)の読み手。属性 `X.列名`・`field("c")`・`getattr(r, "c")`・`arrays["c"]`・`arrays.get("c")`・`attrgetter("c")`・名前の表を回すループ・直書きの組。規則: behavior の列は strict の読み手 ≥ 1、no/diag の列は loose の読み手 0(許可を除く) | **外の状態の属性の読み手**(10d §10-1 の「AST の検査の穴」)。外の状態は「網羅」だけを見る: 持ち主のクラス 46(+入れ替わる 2)の `self.x = …` の属性が台帳の行か除外の一覧に載っているか(`coverage`)と、実行時の `vars()` の網羅(`runtime_uncovered`)。軸 1・軸 2 の判定の正しさは見ていない |

### 3-2 10d で漏れた 15 項目の読み手の形(事実・`ext_readers_ast.py`)

表 6: 15 項目(10d §10-1 の 14+§11 L2 の `named_closed`)。「直した軸」は 10d の記録から。

| 道筋 | 直した軸 | 読み手の形(自己更新の右辺を除く) | 持ち主の外の読み |
|---|---|---|---|
| `presence._pulled_in_today` | 軸 2(のち軸 1 も diag に) | 持ち主の中 1 | なし |
| `classical._ipf_cache` | 軸 1・軸 2 | 持ち主の中 1(`.get`) | なし |
| `conv.n_opened` | 軸 1・軸 2 | 持ち主の中 1・`getattr` の文字列 1・属性 3 | `engine/memory.py:713`(`getattr(conv, "n_opened", 0)`)・`engine/run.py:3433,4259,4265` |
| `ledger.money._snap` | 軸 2 | 持ち主の中 5 | なし |
| `ledger.money._flow_daily` | 軸 2 | 持ち主の中 5 | なし |
| `ledger.money._raw_pos`・`_raw_head` | 軸 2 | 持ち主の中 8・9 | なし |
| `ledger.money._day_marks` | 軸 2 | 持ち主の中 2 | なし |
| `ledger.money.n_raw_dropped` | 軸 2 | 読みは自己更新(`+=`)だけ | なし |
| `ledger.money.n_transfers` | 軸 2 | 持ち主の中 1・属性 1・`getattr` の文字列 1 | `economy/census.py:253`・`engine/run.py:2557` |
| `ledger.goods._dl_pos`・`_dl_head` | 軸 2 | 持ち主の中 7・8 | なし |
| `ledger.goods._dl_marks` | 軸 2 | 持ち主の中 2 | なし |
| `ledger.goods.n_delivery_dropped` | 軸 2 | 読みは自己更新だけ | なし |
| `poi_resolver.named_closed` | 軸 1・軸 2 | **閉包の中の属性 1**(`engine/run.py:514`=`_named_closed_lookup` の中の `look` が `resolver.named_closed.get(...)`。受け手の名前は `resolver` で、台帳の道筋 `poi_resolver` と違う) | 同左 |

- 15 項目の属性の名前は、どれも src の中で 1 つのクラスだけが持つ(名前の衝突なし)。だから受け手を問わず属性の名前で拾えば、持ち主の外の読み(5 項目ぶん)は全部拾える。
- 軸 1 の誤り(4 項目)のうち、持ち主の外の読みで見つかるのは `n_opened`(記憶の層が読む)と `named_closed`(描画へ渡す閉包)の 2 つ。`_ipf_cache` は持ち主の中のメソッドが挙動のために読むので、「持ち主の中か外か」では区別できない。`_pulled_in_today` は逆向き(behavior → diag)の誤り。
- 15 項目はどれも軸 2 を discardable(か unknown)から required に直した。軸 2 の誤りは「読み手がどこか」と関係しない。保存が要るかは「tick をまたいで値が残り、後で読まれるか」で決まる。

### 3-3 全体に当てたときの数(事実)

- 外の状態の行が指す属性 437(持ち主のクラスの属性)+`run_day` の局所変数の行 4(`run_day.pending`・`fleet_deferred`・`fleet_waiting`・`replay_inbox`=属性ではなく名前の読みなので、この形の AST では拾えない)。
- 読みの場所 1,332: 持ち主の中の `self.x` 1,013・持ち主の外の属性 185・`getattr` の文字列 27・別のクラスの中の同じ名前の `self.x` 105(名前の衝突)・直列化と戻しの書き手 2。閉包の中の読み 5。`getattr(obj, 変数)` は 16 か所(静的にはどの属性か決まらない)。
- 同じ属性の名前を 2 つ以上のクラスが持つものが 52(例 `tick`・`blocks`・`log`・`home_cell`・`_start`・`_rows`)。受け手を問わずに名前で拾うと、これらは誤検出の元になる。
- **SoA の規則 2(no/diag は持ち主の外の読み 0)をそのまま当てると**、軸 1 が no/diag の属性 354 のうち 56 属性で持ち主の外の読みが計 235 か所出る(うち名前の衝突 95)。大半は `engine/run.py` の結果の組み立て(`RunResult` の要約・診断の行・manifest)と `cli.py`・`economy/census.py` で、診断の出口として正しい読み。許可の一覧か「診断の出口の関数」の一覧が要る。
- **軸 1 が behavior なのに読みが 0**: `runner.crowd.flow_dir8`・`coherence`(O75)。`engine/processes/crowd.py` で書くだけで、src に読み手が無い(docstring に「診断・将来用」)。軸 1 の判定の見直しの候補(SoA の死蔵の列と同じ形)。
- 時間: 100 ファイルの構文解析 0.43 s+走査 0.33 s(10b の SoA の検査は 0.9 s)。

### 3-4 軸 2 の静的な候補(事実・`ext_state_writes_ast.py`)

- 規則「持ち主のクラスの `__init__` の外のメソッドで書き換える(代入・`+=`・`self.x[...] =`・`append` などの変更のメソッド)属性」は 524 属性。その内訳: 行の軸 2 が required 105・derivable 40・unknown 8・**discardable 282**、除外の cache 60・const 9・ref 9、そのほか 11(子の持ち主の参照と、持ち主そのものが 1 行の属性)。
- 10d の 14 項目は **14/14** がこの規則に当たる。ただし「discardable か除外の cache・const なのに `__init__` の外で書き換わる」候補は **351**(当たり 14=4%)。計数(diag)・リングの中身・日の頭で張り直す表・tick の中の作業の値が大半。
- 除外の `const` なのに `__init__` の外で書き換わる 9 属性(例 `classical._tpd`・`classical.minutes_per_tick` は `bind` で入る・`rel_layer._co_minutes` は `enable_copresent` で入る)は、「起動の後に 1 回だけ置く設定」で、分類としては正しい(人が見て確かめた範囲)。
- 時間 0.21 s。

### 3-5 AST で捕まえられる形・捕まえられない形と、検査の案

表 7: 読み手の形と捕まえ方。

| 形 | AST | 誤検出の見込み | 実行時の検査 |
|---|---|---|---|
| 持ち主の外の属性 `obj.x`(受け手の名前は何でも) | 捕まる(名前で) | 名前の衝突 52 属性 | 不要 |
| `getattr(obj, "x")` | 捕まる | 同上 | 不要 |
| 閉包の中の `obj.x`(`named_closed`) | 捕まる(名前で)。ただし閉包が**どこで呼ばれるか**(描画=挙動か)は AST では分からない | 同上 | 揺らし試験で挙動に効くかを見る |
| 持ち主の中の `self.x`(挙動のためか診断のためか) | 場所は捕まるが、目的は分からない | 判定できない | 揺らし試験(10b の T5 の外の状態版) |
| `getattr(obj, 変数)`・`vars()`・持ち主ごと関数へ渡す | 捕まらない | なし | 揺らし試験 |
| `run_day` の局所変数(O43・O44 など) | 属性ではないので捕まらない | なし | 再開の試験 |
| 軸 2(戻す要るか) | 「`__init__` の外で書き換わる」なら捕まるが候補 351 | 当たり 4% | **再開の試験**(10d の日中 3 点が 14 項目を見つけた)・下の案 2 |

**材料の案(expedient・未リサーチ)・3 件**

1. **外の状態の軸 1 の AST**: 属性の名前で持ち主の外の読みを拾い、軸 1 が no/diag の属性に「診断の出口」以外の読みがあれば落とす。出口は関数の一覧(`RunResult` を組む関数・manifest の書き手・センサス)で持つ。名前の衝突の 52 属性は「受け手の型が分からない」として許可の一覧に理由を付ける。見積り: 走査 1 秒未満。初回は 56 属性 235 か所の仕分けが要る(人手)。
2. **軸 2 の実行時の検査(「捨てて同じか」)**: ランの途中の tick T で、軸 2 が discardable の属性と除外の cache を、新しく作ったインスタンスの値に戻し(保存しなかったときと同じ状態)、T 以後の behavior-hash・呼数・診断の行が通しと同じかを比べる。違えば「discardable の判定が誤り」。再開の試験より軽い(保存と読み込みが要らない)。日中 3 点で回すと 1 構成 1 日ぶんのランが 4 本。
3. **外の状態の揺らし試験**(10b の T5 の拡張): 軸 1 が no/diag の外の状態の属性を、型に合わせて揺らし(数は乱数・辞書は中身を入れ替えるなど)、behavior-hash・呼数・prompt_hash が動かないことを見る。揺らし方を型ごとに決める手間がある(配列以外の型が 30 種ほど・§5-2)。

## 4. K19 の検査(`stream()` の呼び手が 1 回に 4 語を超えて引くもの)

### 4-1 AST の一覧(事実・`stream_sites_ast.py`・0.65 s)

`stream`・`philox` の呼び出しは 32 か所。うち `llm/fleet.py:1268` は httpx の `stream`(乱数ではない=誤検出)なので、乱数は **31 か所**。

| 判定 | 数 | 呼び手 |
|---|---|---|
| 1 語目が定数(0)かカウンタ無し=隣の流れが無い | 7 | `w16.sample.reserved`・`wallet.initial`・`world.public_service_dispatch.counter`・`world.salient.counter`・`engine.processes.rail` ×2・`world.synthetic` |
| 静的に 4 語以内 | 8 | `engine.chooser`・`policy.classical`(2 語)・`conversation.invite`・`engine.processes.environment` ×2・`llm.mock` ×3 |
| 静的には決まらない | 16 | `w16.sample.stratum`(`permutation`)・`agent.schedule` ×2(`random_raw(式)`)・`body.weight`・`body.eer`(正規乱数の棄却)・`world.large_event`(`choice`)・`world.public_service_dispatch` ×2・`world.salient` ×2(Generator を持つ)・`world.delivery_inbound`・`world.delivery_last_mile`・`world.road_works`・`llm.mock`(Generator を渡す)・`perception.attention.p_see`(`random(式)`)・`perception.p_notice`(`random((2, 候補の数))`) |

- AST の静的な判定では 31 のうち 16(52%)が決まらない。大きさが式・棄却のある分布・Generator を持つか渡す形のため。

### 4-2 実行時の実測(事実・`stream_overlap_runtime.py`)

`core.rng.philox`(と直に import した `agents/schedule.py`・`engine/processes/rail.py` の名前)を包み、作った流れごとに「作った時と終わりの 0 語目の差=使ったブロック数」と、同じ (用途名, 1〜3 語目) の別の流れとのブロックの重なりを数えた。final は包まないランと同じ(`993276d5e5bb5cbe`)。

表 8: 既定 v3・5,000 体・seed 1・1 日(流れ 92,041 本)と、counter・率 ×1000(130,666 本)。

| 用途名 | 流れの数 | 最大ブロック | 2 ブロック以上 | 実際の重なり | 読み |
|---|---|---|---|---|---|
| `w16.sample.stratum` | 372(同じ鍵の作り直し 186) | 2,602 | 372 | **185** | 10c 検収 P1 の再現。層は 186 で、抽出が `cli.py:235` と `engine/run.py:1578` で 2 回走るので流れは 372(検収の「372 層」は流れの数と読める=実行役の読み) |
| `body.weight`・`body.eer` | 5,000 ずつ | 2 | 1 ずつ | **1 ずつ** | 10c 検収 R3 の再現(次の体の流れの頭と重なる) |
| `perception.p_notice`(×1000 だけ) | 3,105 | 244 | 2,765 | **1,729** | 10c 検収 P2。既定の率では事象が 0 件で現れない |
| `world.delivery_inbound` | 1 | 1,487 | 1 | 0 | 検収 P3 の 1,487 ブロックを再現。重なるのは日の鍵が 1 違う流れ(別の日・別のラン)で、1 日のランの中には相手が無い |
| `world.road_works` | 1 | 2 | 1 | 0 | 検収 R4 の再現。同上 |
| `world.salient`(stateful) | 1 | 360 | 1 | 0 | 同上(`--day` が 1 違うラン同士で重なる) |
| `world.salient.counter`(×1000) | 1,440 | 4 | 437 | 0 | 1 語目が 0 なので隣が無い(10c の設計どおり) |
| `agent.schedule` | 1 | 10,000 | 1 | 0 | 1 語目=体 × `BLOCKS_PER_AGENT` の**刻みつきの設計**(体ごとに 2 ブロック)。1 本で全員を引いても体ごとの流れと同じ列(T4) |
| `wallet.initial` | 1 | 1,279 | 1 | 0 | カウンタ無し=隣が無い |
| `engine.chooser`・`llm.mock`・`world.public_service_dispatch.counter` ほか | 11,681・69,978・1,562 | 1 | 0 | 0 | 1 ブロック以内 |

- 費用: 包む処理 1.9〜2.6 s(1 本 27.5〜36.1 s の中・約 7%)・後の数え 0.2〜0.4 s。包んだ流れ(9〜13 万本)は全部を手元に持つ(メモリは測っていない)。
- 1 日のランの中で相手が無い重なり(日の鍵の流れ)は、実際の重なりの数え方では 0 になる。「1 語目が値ごとに変わり、2 ブロック以上引いた」という潜在の数えと組にしないと捕まらない。

### 4-3 AST と実行時の分担(事実からの整理)

| 形 | AST | 実行時 |
|---|---|---|
| 1 語目が定数・カウンタ無し | 判定できる(安全) | 不要 |
| 1 語目が値で、引く語数が定数で 4 以内 | 判定できる(安全) | 不要 |
| 1 語目が値で、大きさが式・棄却・Generator を持つ/渡す | 判定できない | 要る(ブロック数を数える) |
| 刻みつきの設計(`agent.schedule`) | 判定できない(刻みが足りるか) | 実際の重なり 0 で確かめられる |
| 日の鍵・別のランとの重なり(P3 の形) | 判定できない | 潜在の数え(2 ブロック以上)で拾う |

### 4-4 検査の案(**材料の案(expedient・未リサーチ)**・2 件)

1. **試験の計器**: 本書の包み方をテストに入れ、小さなラン(合成世界・率 ×1000・2 日)で「実際の重なり 0」と「1 語目が値で 2 ブロック以上の用途名が許可の一覧の中だけ」を検査する。許可の一覧は今の P1〜P3・`body.*`・`agent.schedule`(刻みつき)・stateful の 2 本を K19 の番号つきで載せ、直すたびに外す(10c 検収 Q3 の「一覧を固定する」の形)。src は変えない。
2. **AST の補助**: 静的に安全と決まる 15 か所はテストで固定し、決まらない 16 か所の一覧が増えたら落とす(新しい呼び手を実行時の検査に回す合図)。

## 5. 保存の形式(pickle → npz+json)

### 5-1 中身(事実・`state_format_probe.py`)

既定 v3・5,000 体・seed 1・テープつき・2 日のランを T=1440(日の境目)で止めた状態のファイル(10d §5 と同じ形・4,302,954 B=10d の検収後の値と同じ)。

表 9: まとまりの内訳。

| 部分 | 中身 | バイト |
|---|---|---|
| SoA | agents 45 列(int32 17・int8 17・float32 5・uint8 6)775,000 B・cells 5 列 9,360 B・pois 9 列 77,121 B・知覚 2 列 10,000 B(計 61 列) | 871,481 |
| 外の状態の中の配列 | 75 道筋が配列そのもの+辞書・dataclass の中の配列(`_lines` の 30 本・`PlanBlocks` の 7 本など)。npz にした配列は計 202 本 | 3,109,831 |
| 外の状態の配列以外 | json にした部分 | 418,310(json の大きさ) |
| 見出し・艦隊の未着の呼 | 未着の呼は 0 件(日の境目) | 小さい |
| pickle の中身の合計 | | 4,302,912 |

**配列は 3,981,312 B=中身の 92.5%**。大きい道筋: 活動層の `_bt_agent`・`_bt_tick`(各 0.35 MB)・金の台帳 `_lines`(0.27 MB・整数の鍵の辞書 × 配列)・計画実行層の `ev_tick`・`ev_agent`・`ev_arg`(各 0.22 MB)・テープの印 `bridge._interned`(0.19 MB・文字列 5,394 個の集合)・`presence.blocks`(0.14 MB)。

### 5-2 npz+json で表せるか(事実の分類)

外の状態 169 道筋(うち 26 は腕が立っていない「無い」の印の文字列)。分類は道筋の中で最も表しにくい型で決めた。

| 分類 | 道筋の数 | pickle のバイト | 例 |
|---|---|---|---|
| npz(数の dtype の配列) | 75 | 2,671,410 | `act_layer._bt_*`・`presence.ev_*`・`energy.out_of_area.*` |
| json(数・文字列・None・list・文字列の鍵の dict) | 77 | 85,656 | `conv.n_opened`・`conv.sessions`(この時点は空)・「無い」の印 |
| json だが型が落ちる | 4 | 286,679 | `ledger.money._lines`(整数の鍵 → 文字列)・`conv._speaker_invite_until`(同)・`_day_marks`・`_dl_marks`(タプル → list) |
| 印が要る | 11 | 391,363 | 集合: `bridge._interned`・`run_day.fleet_waiting` / タプルの鍵の辞書: `conv._pair_invite_until`・`_refusal_until` / 凍結した dataclass: `presence.blocks`(`PlanBlocks`)・`_last_close`(`DayClose`)・`arbiter._pending`(`WakeCandidates`) / 13 要素の組の list: `run_day.pending`(`ActivityPayload`=NamedTuple・`Target`=凍結した dataclass・`TargetKind`=Enum を含む)・`intent_layer._payload` / Generator: `runner.salient.rng`・`runner.dispatch.rng`(stateful だけ) |
| 値のクラス(dataclass でない) | 2 | 772 | `arbiter.queue`(`DeferralQueue`・中に `EventClass` の Enum)・`runner.salient.budget`(`EventBudget`・中に dataclass `Counters`) |

- 中に出てくる型(外の状態の全体): int 18,038・str 10,491・tuple 5,276・ndarray 135・None 74・bool 40・list 32・`ActivityPayload` 24・dict 21・`Target` 12・`TargetKind` 12・float 9・`EventClass` 4・set 2・Generator 2・`PlanBlocks`・`WakeCandidates`・`DeferralQueue`・`EventBudget`・`Counters`・`DayClose` 1 ずつ。bytes と object の dtype の配列は 0。
- この時点(日の境目)では会話の `sessions`・`pending_invites` が空。日の途中の状態では `Session`(dataclass・`ConvState` の Enum・辞書を持つ)と `PendingInvite` が入る(印が要る側)。記憶+関係の構成(21.7 MB・10d §5)は測っていない。
- **同じオブジェクトを 2 か所以上から指すもの**: 2 つ。(1) `run_day.pending` の中の `Target` 1 つを 12 か所から(凍結した dataclass なので、写しに分かれても挙動は同じ見込み)。(2) `ledger.money._last_close.flow` と `_flow_daily[0]` が同じ配列(npz にすると別の配列になる。その配列を後で書き換える箇所が無いかは未確認)。10d の README と `engine/resume.py` の docstring にある「会話の `sessions` と `_of_agent` が同じ `Session` を指す」は、今のコードでは当たらない(`_of_agent` は体 → 会話の番号の整数・`engine/conversation.py:281`)。

### 5-3 大きさと時間(事実・試作で測った・中央値)

| 形 | 大きさ | 書き | 読み |
|---|---|---|---|
| pickle(今) | 4,302,954 B(861 B/体) | 3.9 ms(`dumps` だけ) | 3.2 ms(`loads` だけ)・今の読み口(sha256 と写しの検査込み)32.8 ms |
| npz(非圧縮)+json | 4,029,594+418,310=4,447,904 B(890 B/体・+3%) | 木の変換 7.4 ms+json 3.5 ms+npz 5.7 ms ≈ 17 ms | json 2.6 ms+npz の全配列 8.2 ms ≈ 11 ms(オブジェクトの組み立て直しを含まない) |
| npz(圧縮)+json | 608,072+418,310=1,026,382 B(205 B/体・−76%) | npz 76.5 ms+上と同じ | npz 14.3 ms+json 2.6 ms |

- 39 万体への線形の外挿(推測): pickle 336 MB(10d)・非圧縮 npz+json 約 347 MB・圧縮 約 80 MB。
- json の 418 KB の 45% は `bridge._interned`(文字列の集合)。

### 5-4 「自分が書いたものだけを読む」約束を外せるか(事実と読み)

- 今の読み口(`engine/resume.py:233`)は先頭の行の sha256・バイト数・見出しの写しのラン ID を pickle を開く前に確かめる。これは壊れたファイルと取り違えを止めるが、**ファイルを書ける者は先頭の行と写しも書ける**ので、外から来たファイルの安全は守らない。pickle は開いた時点で任意のコードが動きうる。
- npz を `np.load(allow_pickle=False)` で読み、json の印を「許可したクラスだけを組み立てる」表(今の `state_hashes.VALUE_CLASSES` と dataclass・NamedTuple・Enum の一覧)で読めば、読むだけでコードが動く経路は無くなる(推測・numpy の文書で `allow_pickle=False` の範囲を一次確認する)。残る仕事は、読んだ値の形・dtype・鍵の型を台帳の宣言と突き合わせる検査(壊れた値で動き出さないため)。

### 5-5 案(**材料の案(expedient・未リサーチ)**・2 件)

1. **形**: 1 ファイルの zip(または npz)の中に `arrays/<道筋>.npy` と `meta.json`(見出し・配列以外の値・印つき)。印は `__t`(タプル)・`__s`(集合・要素は直列化の昇順)・`__d`(鍵が文字列でない辞書=[鍵, 値] の組の list・挿入順を保つ=O8・O39 の順が要る行)・`__o`(許可したクラス名+欄)・`__nd`(配列の参照)・`__g`(Generator の `bit_generator.state`)。同じ配列を 2 か所から指すものは `__nd` の同じ鍵で表せば同一性を保てる(`flow` の 1 件)。
2. **圧縮**: 日に 1 回なので圧縮の 77 ms は無視できる。39 万体で 336 MB → 約 80 MB(推測)は §7 の予算の再宣言(10d §10-7 で 10e に送った)に効く。

## 6. 予算(アジェンダ §7 との関係)

| 道具 | 足す時間・大きさ | §7 の宣言との関係 |
|---|---|---|
| 環境の欄 | 1 ランに 1 回。版の取得は ms 程度、git の commit を外部コマンドで引くなら数十 ms(推測・未計測) | §7 に項が無い。逐次ループは足さない |
| salt の道具 | 1 本 28〜30 s × 本数(表 5)。検定の計算は n ≤ 12 で 1 ms 未満 | §7 に項が無い(ランの外の道具) |
| CRN の健全性(毎 tick の checkpoint) | 1 本 約 29 s → 約 75 s/日(10d の記録) | §7「behavior-hash の計算は checkpoint ごと(既定は 60 tick ごと)」の範囲。毎 tick は検査のときだけ |
| 外の状態の AST(軸 1) | 構文解析 0.43 s+走査 0.33 s(10b の検査と構文解析を共有できる) | テストの時間に足すだけ |
| 軸 2 の静的な候補 | 0.21 s | 同上 |
| K19 の AST | 0.65 s | 同上 |
| K19 の実行時の計器 | 1 本に +約 7%(1.9〜2.6 s)+0.2〜0.4 s。テストの小さなランなら数秒(推測) | 本番のランには入れない |
| 軸 2 の「捨てて同じか」の試験(案) | 1 構成で 1 日のランが 4 本(5,000 体で約 2 分) | テストの時間 |
| 保存の形式(npz+json) | 書き 17 ms・読み 11 ms(+組み立て直し・未計測)/日。大きさは非圧縮 +3%・圧縮 −76% | §7「状態の書き出しは既定 137 B/体」はすでに 10d で 861 B/体を超えている(10e で再宣言の予定)。圧縮なら 205 B/体 |

## 7. 迷った点・気づいたこと

1. **3/5/3 本と R-71 の 6 対**: 設計書 §5 と指示書 ⑦ 7-4 は開発中の 3/5/3 本を残すとし、R-71 は「主張には 6 対以上」とする。道具は「3 本は記述のみ」と出せば両立するが、「腕が効く」と言う比較の本数の規則は決定が要る(R-71 §8-2 は親の案)。
2. **salt に母集団の抽出が含まれる**: seed を変えると 5,000 体の標本も変わる。CRN の対では問題にならないが、「salt 間の幅」には母集団の抽出のばらつきが入る。動きだけの幅が要るかは決定が要る(§2-5 案 2)。
3. **`seed_exchangeability` の扱い**: 今の manifest では必ず FAIL になる。直すか、manifest を分けるか(§2-5 案 1)。
4. **O75 の `flow_dir8`・`coherence`**: 軸 1 が behavior だが読み手が 0。10e の死蔵の削除と同じ扱いにするかの判断が要る。
5. **`resume.py` の docstring の誤り**: 「`sessions` と `_of_agent` が同じ `Session` を指す」は今のコードでは当たらない(§5-2)。pickle を選んだ理由の 1 つだったので、形式の見直しの判断材料として記録した(src は直していない)。
6. **`w16.sample.stratum` の流れの数**: 10c の検収の「372 層」は、抽出が 2 回走るための流れの数で、層は 186。重なりの評価(隣の鍵の層どうし)には影響しない。
7. **環境の欄の `numba_threads`**: 環境変数の文字列なので、未設定の機械では空になり、実際のスレッド数(この機械で 20)を表さない。今のエンジンはスレッド数に依らない見込み(§1-2)だが、欄の意味は直す余地がある。

## 8. 再現の手順(scripts)

スクリプトは `scripts/10f/` に置いた(src は読むだけ)。`$W` は短い一時ディレクトリ。

```
S=docs/bench/analysis/wallbounce-1006/scripts/10f
python $S/probe_runs.py one --arm v3_default --seed 1 --scratch $W --state --tape   # 状態のファイル+壁時計
python $S/probe_runs.py one --arm v3_default --seed 2 --scratch $W                  # seed 2
python $S/probe_runs.py one --arm v3_default --seed 1 --scratch $W/plain            # seed 1(素の 1 日)
python tools/c7/seed_exchangeability.py --checkpoints s1=$W/plain/ckpt_v3_default_s1.json \
    --checkpoints s2=$W/ckpt_v3_default_s2.json --out $W/exch_s1_s2.json            # §2-2
python $S/state_format_probe.py --state $W/state_v3_default_s1/state-T00001440.pkl --scratch $W/fmt --out $W/state_format.json
python $S/stream_sites_ast.py --out $W/stream_sites.json                            # §4-1
python $S/stream_overlap_runtime.py --out $W/stream_overlap_v3_s1.json              # §4-2 既定 v3
python $S/stream_overlap_runtime.py --arm-json '{"vocab_version":"v3","activity":true,"rng_scheme":"counter","salient_rate_per_10k":3000.0}' \
    --out $W/stream_overlap_v3_counter_x1000_s1.json                                # §4-2 ×1000
python $S/ext_readers_ast.py --out $W/ext_readers.json                              # §3-2・§3-3
python $S/ext_state_writes_ast.py --out $W/ext_writes.json                          # §3-4
```

計測の JSON は一時ディレクトリに置き、リポには入れていない(要れば親が写す)。
