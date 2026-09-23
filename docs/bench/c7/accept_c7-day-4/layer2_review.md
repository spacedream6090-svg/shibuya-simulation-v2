# 層2 独立検収 — c7-day-4(主張腕・読み口 v2.1)の受入(2026-09-14)

- 検収者: 層2(親とは別の Fable 5.1)。親の報告は信用せず、ディスク上の成果物と自分の再計算で確かめた。
- 前提の確認: HEAD `9244f38`(第175)・ブランチ build/c5-c8・`git status` clean。サーバー接続なし・data/realworld 配下は一切読んでいない・`--open-seal` は使っていない。
- 一時出力: `<scratch>/d68/layer2_tmp_day4/`(accept/・yardstick/・検証スクリプト 5 本)。リポ内ファイルの書き換えなし。

## 1 結論

**合格**(c7-day-4 の受入表・T2-a/T2-c・在圏の物差し・読み口 v2.1 の本番表での効果・事前登録 §1 との構成一致・テープ解析の合計は、すべて自分の再実行/再計算で親の値と一致。不合格行なし)。
ただし付帯 2 件(再ランは不要): (A) 開封手順 §3 の「開封記録」が `--force` の 2 本目以降で**上書き**され、主張腕の初回開封の記録がファイルから消える(開封前に手順へ手当て)。(B) 読み口 v2.1 の設計書文言「乗車に隣接しなければ消える」と実装(片側だけ隣接する移動だけのランも消す)にずれ=本番表で 566 ラン(v2 ブロックの 0.13%)・結果への影響は無視できるが文言の精密化が要る。

## 2 検収表

| 対象 | 親の主張 | 自分の再計算値 | 一致 | 所見 |
|---|---|---|---|---|
| 受入表(c7_accept.py 再実行・同入力・`--out-bytes 187902222`) | 判定済み 11/16・合格 11・不合格 0 | 出力 md/json が `docs/bench/c7/accept_c7-day-4/` と**バイト一致**(diff なし) | 一致 | S1 合計 187,714,260+74,921+4,055+108,986=187,902,222 B=0.1750 GB・W1 33,000.77 s=9.167 h・M8 1,604,428 KB=1.530 GB・L4 2,706,593/390,067=6.939(表の備考 6.940 は要約文の「6.94」を書式化した値=軽微) |
| checkpoints.json(本ラン)vs replay_checkpoints.json | 4 点×5 ハッシュ全一致・final 8f8ee7e8 | tick 359/719/1079/1439 × agents/world/population/schedule/combined **20/20 一致**・final `8f8ee7e8e864344b…`・accept 配下の写しも本ランの写しと sha 一致(f61cf179… / 88a1c2fb…) | 一致 | 受入表の T2-c 行そのものは「再生 doc の自己整合+final が要約の最終ハッシュに前方一致」しか見ない(c7_accept.selfconsistency)。4 点×5 の突合は表の外の主張であり、本検収で独立に確認した |
| t2a_1 vs t2a_2(mock 5,000・v2.1) | 一致 | JSON 全体が等しい(sha 2eb67950… 同一)・final `4fb0f2ec…`=事前登録 §1 の同期確認ハッシュと一致 | 一致 | — |
| holdout 開封の痕跡 | 未照合(HOLD/SEAL —) | `holdout_open_record.json` なし・`docs/bench/c7/holdout/` なし・`c7_holdout_compare.*` なし・`git log -3 --name-only` に realworld/holdout のパスなし・`w19_freeze.json.holdout_seal` は layers/seal_scheme のみ | 一致 | 開封していない |
| 在圏の物差し(presence_yardstick.py 再実行) | 09 時 172,265→147,606・18 時 162,142→143,158・03 時 29,322→27,716・近づいた 14/19 | 同値。md/json は anchors_path の表記(親は `<repo>/` に置換・第174)と改行コード(親 LF・当方 CRLF)以外**同一**(正規化 diff で全 122 行一致・json も anchors_path 除き等しい) | 一致 | npz から独自に 24 時系列も出した(§3 参照): 03 27,716 / 09 147,606 / 12 217,435 / 18 143,158 / 21 81,858・昼夜比 5.326 / 7.845 |
| 03 時 ★ 種別(通勤+来街+定期来街+乗務) | 3,012→1,541・訪日は参考行 12,843→13,019 | npz の kind_cell_counts から 3,012→1,541・訪日 12,843→13,019 | 一致 | 訪日を ★ から外した妥当性: W17 day0 で**訪日 17,404 体の 100% が「就寝@宿泊施設」行を持ち自宅就寝 0**(他種別は宿泊就寝 ≤0.1%)=舞台内で寝るのは表の構成上の必然で D-66(域外常住のはずの体の残留)の指標にならない → 外すのは妥当。ただし 03 時在圏の 47% が訪日(13,019)という**水準の当否**は宿泊容量など別アンカーで見る必要があり、参考行として残す扱いは適切 |
| pytest(presence_derive_v2 / presence_executor / c7 yardstick) | — | **59 passed**(28 s) | — | golden 両表(REAL_GOLDEN)を含む |
| 読み口 v2.1 合成行(設計書 §2 追補 2026-09-13 との照合) | 規則どおり | 11 例中 10 例が設計書の記述どおり((a) 先頭 支度→移動 乗車なし → 落とす/(b) 乗車→移動→滞在→移動→乗車なし → 末尾だけ落とす/(c) 移動だけの錨ラン 乗車なし → 消える/(d) ラン内の移動 → 触らない/(e) 域内居住者 → v1 と同一/(f) 両端乗車隣接 → 不変/(g) 「移動・域外」を乗車行扱い/(h) 移動+支度のみ錨なし → v2 で既に落ちる/(i) 設計書例と同型/(j) 2 ラン・昼に域外行)。**1 例(c′)**: 移動だけの錨ランで**直前だけ**乗車 → 実装は消す・設計書文言では残るとも読める | ほぼ一致 | 問題 (B) 参照 |
| 本番 v2 表・域外居住者(346,445 体)のブロック数分布 | v2 [1,269/254,605/85,421/5,076]・v2.1 [1,292/255,230/84,895/4,961]・全消失 23 体 | v1 [92/160,033/133,575/47,861]・v2 **[1,269/254,605/85,421/5,076]**・v2.1 **[1,292/255,230/84,895/4,961]**・本数 440,971→440,171(−800)・全消失 **23**・減った体 795・増えた体 0・域内居住者 3 読み口で本数同一 | 一致 | 1 本の体 254,582 のうち先頭が遅くなった 57.4%(中央値 +41・p90 +71)/末尾が早くなった 27.4%(中央値 −43・p90 −98)・計画上の在圏 08 時 134,844→79,167・09 時 208,522→175,728・18 時 206,658→182,410・12 時 299,917→298,481・03 時 18,421→18,209 も README と一致 |
| 事前登録 §1 の構成 | 読み口 v2.1・出勤率 1.0・queue 4096・fleet-wait 120・温度 0.7・max-tokens 96 | `c7-day-4.log` の実行コマンド: `--llm fleet`(7 endpoints)`--model Qwen3-8B-int8 --mode production --fleet-wait-s 120 --fleet-queue-capacity 4096 --temperature 0.7 --max-tokens 96 --derive-rule v2.1 --attendance-rate 1.0 --seed 1 --ticks 1440 --agents 390067`・HEAD=1e20cd3(第173)。c7-day-3 のコマンドとの差は run-id/tape/出力パスと `--derive-rule v2.1 --attendance-rate 1.0` のみ(day-3 manifest も attendance_rate 1.0=既定なので実質 derive だけ)。manifest: template_sha256 161fe181…・catalog 34f9fa9d…・queue 4096・T1 temp 0.7/max_tokens 96 は両腕同一 | 一致 | — |
| 事前登録 §4 の予想 vs 物差し | 朝の坂が遅く・夕方が早く・昼と深夜は不変 | 独自 24 時系列(day4/day3 比): 07 時 0.71・08 時 **0.66**・09 時 0.86・10 時 0.96・11 時 0.995(ピーク時刻は両腕とも 11 時で不変)/ 17 時 0.93・18 時 0.88・19 時 0.88・20 時 0.91・21 時 0.88 / 12 時 0.97(−6,208=−2.8%)・03 時 0.945(−1,606=−5.5%・うち通勤 −1,475) | 矛盾なし | 「昼と深夜は不変」は坂の −34%/−12% に比べれば桁として妥当だが、03 時は −5.5% 減っている(帰りの行程を在圏に読まなくなったぶんの通勤者)。H1/H2/H5 の予想は holdout 未開封のため検証不能 |
| テープ解析 tape_stats.json | 合計 2,706,593 行=LLM 呼数 | rows 2,706,593 = 要約の LLM 呼 2,706,593 = Σ呼/時 = Σwake_class = Σ行動・未定義 "" 14,798 = 繰り延べ行 14,798(再投入 14,798・再送 14,778) | 一致 | 行動分布(shares): 移動 52.79→52.51%・購入 38.74→38.75%・休憩 4.10→4.03%・乗車 1.63→1.77%・待機 1.40→1.62%・未定義 1.10→1.07%=最大差 0.27 pt で「ほぼ同じ」は正しい。呼/時は 08〜19 時が両腕とも 162,528 で頭打ち(艦隊の処理上限=昼間は呼数が供給側で決まる)・差は 00〜07 時 −90k・20 時 −12k・23 時 −15k・21/22 時 +8.5k/+8.7k(計 −99,077=−3.5%)。wake_class(選ばれた実効クラス)の混合は大きく動いている(0: 610,821→300,098・2: 425,721→561,458・3: 465,329→643,894)=行動の分布ではなく予算配分の変化。テープ本体はローカルに無く再集計は不能(下記 §5) |

## 3 見つけた問題(重大→軽微)

### (A) 開封手順 §3 の穴: 開封記録が 2 本目以降の `--force` で上書きされ、主張腕の初回開封の証跡がファイルから消える(中・開封前に手当て)

- 事象: `tools/c7/holdout_compare.py` は `guard_open`(line 449)で既存記録があれば `--force` を要求するが、`write_open_record`(line 501)は**無条件に同じパスへ上書き**する。§3 step 4 の順序(c7-day-4 を `--open-seal` → c7-day-3・c7-day-2(・c7-day-5)を `--force`)を踏むと、最終的な `docs/bench/c7/holdout_open_record.json` は最後の腕(run_id=c7-day-2 等・forced=true)の記録になり、「主張腕から先に・強制なしで開けた」証跡が record ファイルから失われる(`--manifest --write-manifest` を主張腕で使えば manifest 側には残るが、§3 はどのファイルを manifest とするか指定していない)。
- 再現(holdout を読まない関数単位・一時ディレクトリ): `write_open_record(rec, {run_id:"c7-day-4", forced:False})` → `guard_open(rec, open_seal=True, force=False)` は SealError(期待どおり)→ `guard_open(rec, open_seal=True, force=True)` → `write_open_record(rec, {run_id:"c7-day-3", forced:True})` → rec の中身は c7-day-3 の記録のみ(当方 `layer2_tmp_day4/fake_open_record.json` で確認)。
- 手当て案(親判断): §3 step 4 に「主張腕の開封直後に record を `holdout/open_record_c7-day-4.json` へ複写してから `--force` を呼ぶ」を明記する、または record を履歴 list にする(コード変更=開封前に prereg の版を上げて理由を書く §5)。加えて、SEAL 行のために `--manifest` に渡すファイル(checkpoints.json の manifest か別ファイルか)を §3 に固定する。
- 補足: ラン c7-day-4 の成果物そのものには欠陥なし。開封は未実施なので現時点で証跡は失われていない。

### (B) 読み口 v2.1 の設計書文言と実装のずれ: 移動だけの錨ランが**片側だけ**乗車に隣接する場合(軽微・結果への影響は無視できる・文言の精密化)

- 事象: 設計書 §2 追補 2026-09-13 は「ランが移動だけ(錨 cell≥0)で乗車に隣接しなければ消える」「直前が乗車行なら先頭側は残す・直後が乗車行なら末尾側は残す」。1 行だけのランは先頭側=末尾側なので両規則が競合し、実装(`_trim_nonstay_edges`: `drop = (leading & ~run_prev_ride) | (trailing & ~run_next_ride)`)は**片側でも乗車が無ければ落とす**(=両側とも乗車に隣接しない限り消える)。コードの docstring(「ランが全部 移動/支度 なら両側が全行」)とは整合するが、設計書と README(「全ブロック消失 23 体(移動だけの錨ランで乗車に隣接しない)」)の文言は片側隣接を含んでいない。
- 本番 v2 表での規模: 域外居住者の v2 ラン 440,971 のうち移動/支度だけのラン 1,040 = 両側乗車 240(残る)・前だけ 504・後だけ 62・どちらも無し 234 → v2.1 で空になるラン **800**(=前だけ 504+後だけ 62+なし 234・README の −800 本と一致)。片側隣接の 566 ラン(v2 ブロックの 0.13%)がこの解釈に依存する。
- 再現: `layer2_tmp_day4/synth_v21.py` の例 (c′)(就寝 0-500 自宅・乗車 460-500 域外・移動 500-560 駅 cell 7・休憩 560-1440 域外・域外居住者)→ v2 `[(500,560)]`・v2.1 `[]`。本番表の分類は `layer2_tmp_day4/real_moveonly_runs.py`。
- 判断材料: 「乗車→移動(錨)→域外(乗車なし)」は駅から歩いたとも帰りの行程とも読め、落とす実装も擁護できる。どちらに寄せるにせよ設計書の文言を「両側とも乗車に隣接しない限り消える」等へ精密化するのが最小の手当て(挙動を変えるなら開封前に prereg 版上げ=§5)。

### (C) 表記の軽微事項

- 受入表 L4 の備考「平均 6.940 呼/体/日」は要約文の「6.94」を書式化した値(再計算では 6.939)。判定に影響なし。
- 物差し md の anchors_path は親がコミット前に `<repo>/` へ置換している(第174 の方針)。ツールの出力そのものは絶対パスを書くので、再実行すると差が出る(数値は同一)。

## 4 実行したコマンドと所要時間(全て `.venv/Scripts/python.exe`・`PYTHONUTF8=1`・リポ直下)

| # | コマンド | 所要 |
|---|---|---|
| 1 | `git log -1` / `git status --short` / `git log -3 --name-only` / `ls docs/bench/c7/holdout*` | <1 s |
| 2 | `python tools/c7/c7_accept.py --summary docs/bench/c7/accept_c7-day-4/run_cli_summary.txt --time-v …/run_time_v.txt --determinism …/t2a_1.json …/t2a_2.json --full …/replay_checkpoints.json --wc data/world/v2/wc_index.json --out-bytes 187902222 --out <tmp>/accept` → `diff` で md/json バイト一致 | 1 s |
| 3 | checkpoints.json vs replay_checkpoints.json(4 点×5 鍵)・t2a_1 vs t2a_2 の突合(自作スクリプト・stdin) | 1 s |
| 4 | `python tools/c7/presence_yardstick.py --journal data/runs/c7-day-4/occupancy.npz --summary data/runs/c7-day-4/c7-day-4.log --label c7-day-4 --before data/runs/c7-day-3/occupancy.npz --before-summary docs/bench/c7/yardstick/after_c7-day-3_vs_c7-day-2/run_summary_c7-day-3.txt --before-label c7-day-3 --target-population 390067 --out <tmp>/yardstick` → 正規化 diff | 1 s |
| 5 | `python -m pytest tests/engine/test_presence_derive_v2.py tests/engine/test_presence_executor.py tests/c7/test_presence_yardstick.py -q -o addopts=""` → 59 passed | 30 s |
| 6 | `<tmp>/synth_v21.py`(合成 11 例・`PlanBlocks.from_weekly(..., derive_rule="v2.1")`) | 3 s |
| 7 | `<tmp>/real_w17_dist.py`(本番 W17 v2 表 md5 3113e9ba・3 読み口の分布/消失/シフト/計画在圏) | 4 s |
| 8 | `<tmp>/real_moveonly_runs.py`(移動だけのランの隣接別分類・落とした行の内訳) | 5 s |
| 9 | `<tmp>/hourly_series.py`(occupancy.npz → 5 エリア 24 時系列・種別内訳・深夜残存率) | 3 s |
| 10 | `<tmp>/foreign_lodging.py`(種別×就寝場所の集計) | 3 s |
| 11 | tape_stats.json の内部整合・予算値の再計算・c7-day-3/4 のコマンド行 diff・manifest 比較(stdin スクリプト) | 各 <1 s |
| 12 | holdout_compare の `guard_open`/`write_open_record` を一時パスで関数単位に実行(問題 A の再現) | <1 s |

検収の総所要 約 25 分。

## 5 確かめられなかったこと(理由つき)

- **HOLD/SEAL(KDDI 形状 5 指標)**: holdout 未開封・開封は禁止事項。事前登録 §4 の H1/H2/H5 に関する予想の当否も同様に検証不能。
- **tape_stats.json の再集計**: テープ本体(`data/tape/c7-day-4/calls.parquet` 187 MB)はローカルに無い(`data/tape/` には c7-day-3 のみ)。合計行数と各内訳の和・繰り延べ行との整合(内部整合)だけを確認した。生成スクリプトもリポ内に無い(scratch 由来)。
- **サーバー側の実測バイト数**(`--out-bytes 187902222` の内訳 4 ファイル)と `/usr/bin/time -v` の値の一次確認: サーバー接続禁止のため、ローカルの写し(run_time_v.txt・c7-day-4.log 末尾の time -v 出力・checkpoints.json 4,055 B・occupancy.npz 108,986 B は一致)で確認できた範囲まで。calls.parquet/blocks.parquet のバイト数は写しが無い。
- **T2-b(先頭 K tick 部分再ラン)**: 親も未実施(表 —)。
- **wake_class の混合が動いた理由**: `selected_eff_class`(予算の実効クラス)の配分変化であることまでは特定したが、在圏の減少との因果は本検収の範囲外(呼数の頭打ち 162,528/時が両腕で同じため、昼間は予算配分側の差として現れている可能性がある=推測のため結論にしない)。
