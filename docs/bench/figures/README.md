# 論文用の図(docs/bench/figures)

図は**手で描かない**。全て `tools/fig/` のスクリプトが既存の成果物から作り直せる。
1 枚につき **PNG + SVG + 数値サイドカー JSON** の 3 点が出る。JSON には図に出した数値が
そのまま入っているので、図を読まずに検算できる。

## 全部作り直す

```
python tools/fig/fig_presence_24h.py  --out docs/bench/figures
python tools/fig/fig_calls_by_hour.py --out docs/bench/figures
python tools/fig/fig_ab7_actions.py   --out docs/bench/figures
```

依存は `matplotlib`(`pyproject.toml` の `[project.optional-dependencies] dev`)。
煙検査は `pytest tests/fig`(合成データのみ・実資産も holdout も開かない)。

---

## 図 1 — `fig1_presence_24h.{png,svg,json}`

**何を示すか**
渋谷駅周辺 139 ha 相当(5 エリア合計)の在圏人数を 24 時間ぶん並べ、現実側のアンカーと
同じ軸に置く。ラン 3 本 `c7-day-2 → c7-day-3 → c7-day-4` の並びが D-66(域外常住者が
深夜も域内に残る)の修正の効き。`mock40-v21` は実 LLM を使わない対照(細い破線)。
副パネルは現実側の起床率 a(h) 曲線(anchor)。

**データの出所**

| 何 | 相対パス |
|---|---|
| 在圏 journal(24 標本×520 セル) | `data/server_retrieval/2026-09-16/v2_data/runs/{c7-day-2,c7-day-3,c7-day-4,mock40-v21}/occupancy.npz` |
| セル→5 エリア写像 | `data/world/v2/w2_cells.parquet` + `tools/c7/area_axes_v0.json`(`tools/c7/occupancy_series.build_map`) |
| 現実アンカー | `docs/bench/anchors/presence_anchors_v0.json` |
| 突き合わせ先(集計済み) | `docs/bench/c7/yardstick/after_c7-day-4_vs_c7-day-3/presence_yardstick.json` |

**再現コマンド**

```
python tools/fig/fig_presence_24h.py \
  --runs-dir data/server_retrieval/2026-09-16/v2_data/runs \
  --world data/world/v2 --axes tools/c7/area_axes_v0.json \
  --anchors docs/bench/anchors/presence_anchors_v0.json \
  --yardstick docs/bench/c7/yardstick/after_c7-day-4_vs_c7-day-3/presence_yardstick.json \
  --out docs/bench/figures
```

所要 1 秒未満。標準出力に `yardstick_ok` が出る。

**注記**

- 数え方は二重実装していない。写像は `tools/c7/occupancy_series.build_map`、時×エリア集計は
  `c7lib.OccupancySeries.area_hour_table`。本スクリプトは合計して描くだけ。
- **自己検査**: npz から出した 24 値が上の yardstick JSON の `area_hour_counts` と一致するか
  を毎回測り、`fig1_presence_24h.json` の `yardstick_check` に書く(c7-day-4 と c7-day-3 の
  両方・24 時間全部・最大絶対差 0.0)。
- **縮尺なし**。縦軸は生の体数(n=390,067)。線形換算の `five_area_scaled` は使っていない。
- **expedient**: セル→5 エリア写像 `area_axes_v0` は公的ポリゴンが無いための近似
  (登録簿 E-C7-2)。境界を ±50 m 動かすと −50 m で 5.6% / +50 m で 8.3% のセルが移動する
  (`docs/design/v2-implementation-plan.md` §9.1 の実測)。
- アンカーの tag: `pt_area_daytime_peak` 145,000 = **anchor**(内閣府 PT・139 ha)/
  `night_presence_estimate` 15,000–30,000 = **estimate**(推定帯)/
  `core9_daytime_population` 130,167 = **anchor** だが**面積が違う**(中核 9 町丁目 1.39 km²)
  ので線は点線・凡例に「面積差あり」と明記した参考値。
- **KDDI holdout は開いていない**(`data/world/v2/w19_freeze.json` の封印に触れていない)。
  現実側の数値は全てアンカー台帳(source / verified_by / tag つき)から読む。

---

## 図 2 — `fig2_calls_by_hour.{png,svg,json}`

**何を示すか**
c7-day-4(390,067 体×1 シミュ日)で、**どの時刻に・どんな理由で** LLM を呼んだか。
上段は応答が返った呼(非繰り延べ)を起床クラスで積み上げ、中段は応答が返らなかった呼
(`deferred`)の件数、下段はその率。

**データの出所**

| 何 | 相対パス |
|---|---|
| 呼のテープ(270 万行) | `data/server_retrieval/2026-09-16/v2_data/tape/c7-day-4/calls.parquet` |
| 体数 390,067 の出どころ | `docs/bench/anchors/presence_anchors_v0.json` の `anchors.full_population` |
| `wake_class` の意味 | `src/shibuya/core/types.py` の `EventClass` |

**再現コマンド**

```
python tools/fig/fig_calls_by_hour.py \
  --tape data/server_retrieval/2026-09-16/v2_data/tape/c7-day-4/calls.parquet \
  --anchors docs/bench/anchors/presence_anchors_v0.json \
  --out docs/bench/figures
```

所要 約 1 秒(`tick` / `wake_class` / `deferred` の 3 列しか読まない。`response` 列は読まない)。

**注記**

- `wake_class` は `EventClass`(`INSTITUTION=-1 / CONVERSATION=0 / PLAN_BOUNDARY=1 /
  INDIVIDUAL=2 / CELL=3`)。**昇順が優先**。値と並びは enum から取り、和名だけ同 docstring
  §2.5 の文面を写した(enum が増えたらスクリプトは例外で止まる)。このテープには 0..3 が出る。
- **右軸を作らない**。件数と率は 2 つの縦軸を重ねると相関を捏造するので、同じ x 軸を共有する
  別パネルに分けた(`dataviz` スキルの anti-pattern 第 1 位)。
- 総呼数は**発射数**(再送も 1 呼・親決定 2026-09-09)。`呼/体/日` は**応答が返った呼**を
  390,067 で割った値。
- 24×クラスの表・時刻別の繰り延べ件数と率・`deferred_reason` の内訳は
  `fig2_calls_by_hour.json`。

---

## 図 3 — `fig3_ab7_actions.{png,svg,json}`

**何を示すか**
AB7-OPEN-INTENT(seed 1)の 2 腕——LLM に横断 12 語のホワイトリスト(契約語彙は全 24 語・第203 訂正)を見せる `vocab` と、
自由文で意図を書かせる `open`——で、エンジンが受け取る行動語の分布がどう変わるか。
(a) 解決後の分布の比較、(b) `open` 腕の**生の表層**上位 10 とその落ちた先。

**データの出所**

| 何 | 相対パス |
|---|---|
| 腕のテープ(各 ≈37k 行) | `data/tape/c8_ab7_s1/AB7-OPEN-INTENT__vocab/`・`…__open/` |
| 解決の関数 | `src/shibuya/llm/parser.py` `parse_two_line` / `src/shibuya/llm/undefined.py` `map_synonym` / `src/shibuya/llm/contract.py` `ALL_ACTION_WORDS` |
| 分布・JSD | `tools/c6/c6lib.py` の `score_texts` / `jsd_counts` |
| runner 出力(照合先) | `docs/bench/c8/ablation/ablation_AB7-OPEN-INTENT_s1.json` |
| ランの諸元 | `docs/bench/c8/ablation/ab7_s1_parent_report.md` |

**再現コマンド**

```
python tools/fig/fig_ab7_actions.py \
  --tape-root data/tape/c8_ab7_s1 --arm AB7-OPEN-INTENT \
  --runner docs/bench/c8/ablation/ablation_AB7-OPEN-INTENT_s1.json \
  --out docs/bench/figures
```

所要 約 4.5 秒(2 腕ぶんのテープを全行なめて解決し直す)。

**注記**

- 採点の定義を 2 つ持たない。段0 辞書で救えた語は**写像先の契約語**として数え、どちらでも
  解けない語はエンジンの段1 と同じく `待機` に畳む(`UndefinedActionRegistry.observe` と同じ扱い)。
- **JSD は定義で値が変わる**ので 2 通りをサイドカー JSON に書く。
  `action_counts`(`(未定義)` を独立の箱として数える)= **0.0518 bits** = runner の `action_jsd`。
  `resolved`(`(未定義)` を `待機` に畳んだあと)= **0.0364 bits**。図の注記は前者。
  帰無参照(同モデル seed 違い T7)= 0.0035 bits なので **14.8 倍**。
- エントロピー(解決後)は **1.5638 → 1.1374 bits**。
- (a) は両腕とも 0 件の 15 語(全 24 語のうち)を省いた。片方だけ 0 の語は `0` と明示。
  縦軸は対数にしない(比較が歪むため)ので、`乗車 907 → 1` のような小さい値は数値ラベルで読む。
- ラン: 5,000 体×1,440 tick(1 シミュ日)・実 LLM(7×Qwen3-8B INT8・温度 0.7・max-tokens 96)・
  seed 1。テープは `data/tape/`(gitignore)にあり、リポジトリには入らない。

---

## 図に共通の作法(`tools/fig/_style.py`)

- **書体**: 日本語が出る書体を候補順に探す(Yu Gothic → Meiryo → MS Gothic →
  Noto Sans CJK JP → IPAexGothic)。1 つも無ければ警告を出して**英語ラベルに落ちる**ので、
  書体の無い環境でも図は壊れない。
- **配色**: Claude Code スキル `dataviz` の `references/palette.md`(light モード)をそのまま写した。
  独自の色は作らない・8 スロットを循環させない。使った組み合わせは同スキルの
  `scripts/validate_palette.py` で検査済み(下表)。
- **出力**: PNG(dpi 150)+ SVG + サイドカー JSON。PNG/SVG のメタデータから生成時刻と
  ソフト名を外し、SVG の内部 id を決める `svg.hashsalt` を固定してあるので、**同じ入力なら
  同じバイト列**が出る(作り直しても無意味な差分が出ない。`tests/fig` が 2 回描いて照合する)。
- **パスは相対のみ**。JSON に書く経路は `_style.rel()` を通す(絶対パス=ホームディレクトリを
  出力物に残さない)。

### 配色の検査(`validate_palette.py` · light · surface `#fcfcfb`)

| 図 | 色 | 検査 | 結果 |
|---|---|---|---|
| 1(ラン 3 本) | `#86b6ef,#2a78d6,#0d366b` | `--ordinal` | ALL PASS(単色・L 単調・明端 2.06:1) |
| 1(アンカー橙 vs ランプ両端) | `#0d366b,#eb6834` / `#86b6ef,#eb6834` | `--pairs all` | PASS(ΔE 30.3 / 23.1)。`#86b6ef` は対地 2.06:1 = **直接ラベル必須**(実装済み) |
| 2(起床クラス 4 色) | `#2a78d6,#eb6834,#1baf7a,#eda100` | 既定(隣接) | ALL PASS(最悪隣接 CVD ΔE 9.1・通常視 22.9)。aqua 2.74:1 / yellow 2.11:1 = **直接ラベル + 表(JSON)で補う**(実装済み) |
| 3(a) | `#2a78d6,#eb6834` | `--pairs all` | ALL PASS(CVD ΔE 24.7・対地 ≥3:1) |
| 3(b) | `#eb6834,#4a3aa7` | `--pairs all` | ALL PASS(CVD ΔE 29.5・対地 ≥3:1) |

系列の色は**実体に付く**(`c7-day-4` は常に濃い青・`open` は常に橙)。並べ替えや絞り込みで
色を付け替えない。

---

## 図 4 — `fig4_seed_pair.{png,svg,json}`(第204)

**何を示すか** 同一構成(c7-day-4=390,067 体・v2.1・attendance 1.0・7×Qwen3-8B INT8・温度 0.7)で **seed だけ違う 2 ラン**の 5 エリア合計在圏(上)・相対差(中)・時刻別 CV(n=2)(下)。D-46(アンサンブルの規模)・D-70・G-8(初回 8 seed=expedient)を数字で決めるための図。

**データの出所** `data/server_retrieval/2026-09-16/v2_data/runs/c7-day-4/occupancy.npz`(seed 1)・`data/server_retrieval/2026-09-17/runs/c7-day-4-s2/occupancy.npz`(seed 2)・写像は図 1 と同じ(`occupancy_series.build_map` / `c7lib.area_hour_table`)。

**再現コマンド** `python tools/fig/fig_seed_pair.py --out docs/bench/figures`

**注記** seed 間 CV 中央値 0.38%・最大 3.25%(05 時)。エリア別 24h シェアの JSD 平均 0.000162 bits=事前登録 H1 線の 1/75。N=(CV/r)² は L-B 答申 §5(深夜を 2% で言うなら 3 本)。KDDI holdout は未開封・未使用。数値は `fig4_seed_pair.json`。

---

## 図 5 — `fig5_ab7c_vocab.{png,svg,json}`(第235)

**何を示すか** AB7c-VOCAB-V2(seed 1)の 3 腕——語彙 v1(24 語・現行)/ 語彙 v2(+「食事」)/ 自由文+v2 辞書——でエンジンが受け取る行動語の分布 (a) と、乗車 (b)・休憩 (c) の時刻別(v1 vs v2)。第227 親報告と D-91 診断(第235)の数字。

**データの出所** テープ `data/tape/c8_ab7c_s1/AB7c-VOCAB-V2__{vocab_v1,vocab_v2,open_v2}/`(gitignore)・runner 出力 `docs/bench/c8/ablation/ablation_AB7c-VOCAB-V2_s1.json`(照合先・実現した食事 7,024 と書式エラー率)・解決の関数は図 3 と同じ(`parse_two_line(vocab_version=腕の版)` + `map_synonym(vocab_version=腕の版)`)・JSD は `c6lib.jsd_counts`。

**再現コマンド** `python tools/fig/fig_ab7c_vocab.py --out docs/bench/figures`(約 10 秒・3 腕のテープを全行なめる)。

**注記**
- **自己検査**: 腕ごとの計数を runner の `action_counts` と語ごとに突き合わせ、最大絶対差をサイドカー `runner_check` に書く(3 腕とも **0**=段0 辞書を当てると runner と同じ数になる)。
- JSD v1 vs v2 = **0.3611 bits**、食事を購入に畳むと **0.0132 bits**(差の大半は購入→食事の付け替え)。エントロピー 1.564 / 1.842 / 1.280 bits。
- 色は実体に付く: vocab 系=青・v2=aqua(slot 3)・open=橙(図 3 の open と同じ)。青/橙/aqua の隣接 2 組は図 2 の検査で PASS 済み(青-aqua は未検査=直接ラベルで補う)。
- (b)(c) の乗車半減・休憩倍増の原因は図 7。

---

## 図 6 — `fig6_ab6b_signage.{png,svg,json}`(第235)

**何を示すか** 看板あり腕に対する**購入シェアの差 Δ[pp]**を、09-10 の広告ゼロ腕(AB6-AD-ZERO・C7 期のコード・seed 1/2)と 09-17 の注視ゲート腕(AB6b-AD-NOTICE・HEAD 667ceb5・在る seed ぶん)で並べる (a)。AD1 の線(±1 pp)と、同構成 seed 差の幅(看板あり腕 seed 1 vs 2 の購入差 0.17 pp)を同じ軸に置く。(b) 会話の呼数、(c) 休憩シェア(09-17 seed 1 の 4 腕・実測注視率つき)。

**データの出所** runner 出力だけ: `docs/bench/c8/ablation/ablation_AB6-AD-ZERO{,_seed2}.json`・`ablation_AB6b-AD-NOTICE_s{N}.json`(seed 1〜3 の在るぶんを自動で読む)。購入シェア = `action_counts["購入"] / n_texts`。AD1 の線 = パターン台帳 第3封印行 S3/AD1。

**再現コマンド** `python tools/fig/fig_ab6b_signage.py --out docs/bench/figures`(1 秒未満)。

**注記**
- 正 = 看板を消す/減らすと購入が**増える**。09-10 は −1.34 / −1.02 pp(線超え)・09-17 は +0.51 / +0.48 / +0.61 pp(線の内側・符号が逆)。
- 09-10 と 09-17 は呼数が違う(50,000 vs ≈36,900/腕)= C7 期と現行で予算配分が違うためで、シェアで比べる。
- 色は実体に付く: 現行コード=青・C7 期=灰(`MUTED`)・AD1 の線=赤(slot 8)。seed 2 以降の JSON を置けば行が増える(コードは変えない)。

---

## 図 7 — `fig7_d91_ride_chain.{png,svg,json}`(第235)

**何を示すか** D-91 (a) 診断([診断書](../c8/ablation/ab7c_s1_d91_diagnosis.md))。(a) 朝 06〜10 時の呼のうち「乗車」を選んだ率を条件(通勤者×駅の可視・起床クラス 4・全体)で切って v1 と v2 で並べる=どの条件でも同じ比(0.42〜0.45)で薄まる。(b) 直前の行動が 購入(v1)/ 食事(v2)/ 購入(v2)だった呼の次手分布=食事のあとは休憩が 22%(購入のあとは 7%)。

**データの出所** 図 5 と同じテープ(v1・v2 の 2 腕)。種別 = B1 ブロック(`tape.block_text`)・駅の可視 = B2 ブロックに「駅」を含む・起床クラス = `wake_class`(`EventClass`)・行動語は図 5 と同じ手順。

**再現コマンド** `python tools/fig/fig_d91_ride_chain.py --out docs/bench/figures`(約 8 秒)。

**注記**
- 朝に乗車を選んだ体は v1 380 / v2 162 / 共通 25。B5(空腹)と B6(直前の結果)はテープに無いので条件にできない(限界)。
- (b) の色は 7 色(移動=青・休憩=橙・待機=黄・購入=aqua・食事=magenta・乗車=violet・その他=灰)。隣接の検査は未実施=区切り線と直接ラベルで補う。

---

## 表 1〜3 — `tbl{1,2,3a,3b}_*.{png,svg}` + `tbl_ablation.{md,json}`(第235)

**何を示すか** 図 5〜7 の**サイドカー JSON だけ**から組んだ結果表(数値の出所を 1 つにする)。表 1 = 3 腕の行動分布・エントロピー・書式エラー率・実現した食事・入力トークン。表 2 = 看板の腕(09-10 seed 1/2・09-17 seed 在るぶん)の購入・Δ購入・会話・休憩・注視率・入力トークン。表 3a = 朝の乗車率の条件別。表 3b = 直前の行動別の次手。Discord は表を描けないので PNG を添付し、Markdown(`tbl_ablation.md`)は文書用。

**再現コマンド** `python tools/fig/tbl_ablation.py --out docs/bench/figures`(図 5〜7 を先に作る)。
