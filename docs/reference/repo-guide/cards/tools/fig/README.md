# tools/fig

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 12 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tools/fig/__init__.py)

tools/fig — 論文用の図を**再現可能なスクリプト**で作る置き場。

## [_style.py](../../../../../../tools/fig/_style.py)

_style.py — 図の共通設定(書体・配色・保存・サイドカー)。

- 公開の関数とクラス
  - `T`(関数): ラベル 1 つ。日本語書体があれば ``ja``・無ければ ``en``。
  - `declutter`(関数): 直接ラベルの y 位置を ``min_gap`` 以上離す(順序は保つ)。**純関数**。
  - `note`(関数): 図の下端に注記を置く(出典・expedient・未使用データの宣言)。
  - `pick_ja_font`(関数): 候補順に**実在する**書体名を返す。1 つも無ければ ``None``。
  - `rel`(関数): パスを**リポジトリ相対の POSIX 文字列**にする。外にあるときはファイル名だけ。
  - `save`(関数): PNG と SVG を書く。戻りは**相対パス**の辞書。
  - `thousands`(関数): 3 桁区切り(軸目盛りと直接ラベルで同じ書き方をする)。
  - `use_style`(関数): rcParams を図の共通設定にする(**呼ぶたびに同じ状態**になる)。
  - `write_sidecar`(関数): 数値サイドカー JSON を書く。UTF-8・LF・``ensure_ascii=False``。戻りは相対パス。
- 呼び手: `tools/fig/fig_ab6b_signage.py`・`tools/fig/fig_ab6c_uncapped.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_ab8_budget.py`・`tools/fig/fig_calls_by_hour.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/fig/fig_presence_24h.py`・`tools/fig/fig_seed_pair.py`・`tools/fig/tbl_ablation.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- 決定の ID: 第 202

## [fig_ab6b_signage.py](../../../../../../tools/fig/fig_ab6b_signage.py)

図 6 — 看板(広告)を消す/見る頻度を下げると購入はどれだけ動くか(AB6 09-10 と AB6b 09-17)。

- 公開の関数とクラス
  - `draw`(関数): データ dict → Figure。**ファイルを読まない**。
  - `load_ab6b`(関数): runner JSON 群 → 描画に要るデータ dict。
  - `main`(関数)
  - `share_pct`(関数): 行動語のシェア[%] = action_counts[word] / n_texts × 100。**純関数**。
  - `summarize_run`(関数): runner の 1 ラン → 図に要る数だけ。**純関数**。
- import している内部モジュール: `tools/fig/_style.py`
- 呼び手: `tools/fig/fig_ab6c_uncapped.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--out`
- 決定の ID: 第 214

## [fig_ab6c_uncapped.py](../../../../../../tools/fig/fig_ab6c_uncapped.py)

図 9 — 看板(広告)の効果は呼数の上限を外しても残るか(AB6b 上限あり vs AB6c 無制限・第246)。

- 公開の関数とクラス
  - `draw`(関数): データ dict → Figure。**ファイルを読まない**。
  - `load_ab6c`(関数): runner JSON 群 → 描画に要るデータ dict。
  - `main`(関数)
- import している内部モジュール: `tools/fig/_style.py`・`tools/fig/fig_ab6b_signage.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--out`
- 決定の ID: 第 246

## [fig_ab7_actions.py](../../../../../../tools/fig/fig_ab7_actions.py)

図 3 — 行動分布 vocab vs open(AB7-OPEN-INTENT・seed 1)。

- 公開の関数とクラス
  - `analyze_arm`(関数): 1 腕のテープ → 行動分布・生表層・解決経路。
  - `draw`(関数): データ dict → Figure。**ファイルを読まない**。
  - `entropy_bits`(関数): 計数辞書のシャノンエントロピー[bits]。**純関数**。
  - `load_ab7`(関数): 両腕のテープ → 描画に要るデータ dict(比較指標つき)。
  - `main`(関数)
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.foundation.vocab.actions`・`shibuya.llm.undefined`・`shibuya.runtime.inference.tape`・`tools/c6/c6lib.py`・`tools/fig/_style.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--arm`
  - `--out`
  - `--runner`: runner 出力 JSON との突き合わせ(空文字で省略)
  - `--tape-root`

## [fig_ab7c_vocab.py](../../../../../../tools/fig/fig_ab7c_vocab.py)

図 5 — 語彙 v1 vs v2(+open_v2)の行動分布と、乗車・休憩の時刻別(AB7c-VOCAB-V2・seed 1)。

- 公開の関数とクラス
  - `analyze_arm`(関数): 1 腕のテープ → 行動分布・時刻別分布。
  - `draw`(関数): データ dict → Figure。**ファイルを読まない**。
  - `entropy_bits`(関数): 計数辞書のシャノンエントロピー[bits]。**純関数**。
  - `fold_meal`(関数): 「食事」を「購入」に畳んだ計数(v1 の語彙で読むときの対応表)。**純関数**。
  - `load_ab7c`(関数): 3 腕のテープ → 描画に要るデータ dict(runner との突き合わせつき)。
  - `main`(関数)
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.llm.undefined`・`shibuya.runtime.inference.tape`・`tools/c6/c6lib.py`・`tools/fig/_style.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--arm`
  - `--out`
  - `--runner`: runner 出力 JSON との突き合わせ(空文字で省略)
  - `--tape-root`
- 決定の ID: 第 227・第 235

## [fig_ab8_budget.py](../../../../../../tools/fig/fig_ab8_budget.py)

図 8 — LLM 呼数の予算(L4)を動かすと世界で起きることはどう変わるか(AB8-L4-SCALE・第247)。

- 公開の関数とクラス
  - `draw`(関数): データ dict → Figure。**ファイルを読まない**。
  - `load_ab8`(関数): runner JSON 群 → 描画に要るデータ dict(在る seed を全部読み、図は最小 seed)。
  - `main`(関数)
  - `summarize_run`(関数): runner の 1 ラン → 図に要る数だけ。**純関数**(割り算だけ)。
- import している内部モジュール: `tools/fig/_style.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--out`
- 決定の ID: 第 247

## [fig_calls_by_hour.py](../../../../../../tools/fig/fig_calls_by_hour.py)

図 2 — 時刻別の LLM 呼数と起床クラス(c7-day-4)。

- 公開の関数とクラス
  - `draw`(関数): データ dict → Figure。**ファイルを読まない**。
  - `event_classes`(関数): ``EventClass`` を**優先順(昇順)**に並べた記述。値と並びは src から取る。
  - `load_calls`(関数): ``calls.parquet`` の必要 3 列だけを読む(``response`` 列は読まない=メモリ節約)。
  - `main`(関数)
- import している内部モジュール: `shibuya.foundation.types`・`tools/fig/_style.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--anchors`: 体数(full_population)の出どころ
  - `--n-agents`: 体数の上書き
  - `--out`
  - `--tape`: calls.parquet

## [fig_d91_ride_chain.py](../../../../../../tools/fig/fig_d91_ride_chain.py)

図 7 — 語彙 v2 で乗車が半減し休憩が倍増した理由(D-91 (a) 診断・AB7c seed 1 のテープ)。

- 公開の関数とクラス
  - `draw`(関数): データ dict → Figure。**ファイルを読まない**。
  - `load_d91`(関数)
  - `main`(関数)
  - `read_arm`(関数): 1 腕のテープ → 行の list(agent 昇順・tick 昇順・直前行動つき)。
  - `summarize`(関数): 行(agent/tick/hour/kind/station/wc/action/prev)→ (a)(b) の数。**純関数**。
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.llm.undefined`・`shibuya.runtime.inference.tape`・`tools/fig/_style.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--arm`
  - `--out`
  - `--tape-root`
- 決定の ID: D-91

## [fig_presence_24h.py](../../../../../../tools/fig/fig_presence_24h.py)

図 1 — 在圏の 24 時間曲線 vs 現実アンカー。

- 公開の関数とクラス
  - `check_against_yardstick`(関数): 自分で npz から出した値が既存の集計 JSON と一致するかを測る。**純関数**。
  - `draw`(関数): データ dict → Figure。**ファイルを読まない**(テストは合成データで呼べる)。
  - `load_presence`(関数): journal(``occupancy.npz``)とアンカー台帳 → 描画に要るデータ dict。
  - `main`(関数)
- import している内部モジュール: `tools/c7/occupancy_series.py`・`tools/fig/_style.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--anchors`
  - `--axes`
  - `--out`
  - `--runs-dir`
  - `--world`
  - `--yardstick`: 集計済み JSON との突き合わせ(空文字で省略)
- 決定の ID: D-66

## [fig_seed_pair.py](../../../../../../tools/fig/fig_seed_pair.py)

図 4: 同一構成 × seed 違い(c7-day-4 seed 1 vs seed 2・390,067 体)の在圏 24 時間と seed 間の変動係数。

- 公開の関数とクラス
  - `draw`(関数): データ dict → Figure(上: 在圏 2 本・中: 相対差・下: CV)。
  - `load_pair`(関数): 2 ランの 時×エリア表を読み、合計・相対差・CV(n=2)・エリア別 24h シェアの JSD を出す。
  - `main`(関数)
  - `summarize`(関数): 数値だけの要約(描画から分離=テスト用)。
- import している内部モジュール: `tools/c7/occupancy_series.py`・`tools/fig/_style.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--axes`
  - `--out`
  - `--run1`
  - `--run2`
  - `--world`
- 決定の ID: D-46・D-70

## [tbl_ablation.py](../../../../../../tools/fig/tbl_ablation.py)

表 1〜3 — 検証ラン(ablation)の結果表(PNG + SVG + Markdown + JSON)。

- 公開の関数とクラス
  - `build_tables`(関数): 3 つのサイドカー → 表 4 枚の仕様。**純関数**。
  - `main`(関数)
  - `render_table`(関数): 表の仕様 → Figure(matplotlib の table)。**ファイルを読まない**。
  - `table1`(関数)
  - `table2`(関数)
  - `table3a`(関数)
  - `table3b`(関数)
  - `to_markdown`(関数): 表の仕様 → Markdown(GFM)。**純関数**。
- import している内部モジュール: `tools/fig/_style.py`
- 読む試験: `tests/fig/test_fig_smoke.py`
- CLI の引数
  - `--fig-dir`: fig5/6/7 のサイドカー JSON の置き場
  - `--out`
