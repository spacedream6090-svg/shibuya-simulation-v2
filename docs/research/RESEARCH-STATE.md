# リサーチの進行状況(次のエージェントが最初に読む 1 枚)

<!-- hdr:v1 -->
- **分野**: 全分野(進行状況の索引) | **重要度**: P0
- **一次確認**: 本書自体は状態の記録であって主張をしない。**各行の状態が正**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **v1 資産**: [v1-asset-triage.md](v1-asset-triage.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 最終更新 **2026-09-17(第207)**: **L-R8・L-C9 完了**(答申 2 本・lit 13 本・親確認 7 件 → C9 アジェンダ §4 改訂)。R-7 の空欄 2 件解消(単位・γ)。Weidmann 1993 原典と鉄道総研 2016 の数値は取得不能=空欄確定。
> 最終更新 **2026-09-17(第204)**: **L-D71 完了**(答申 [v2-d71-vocab-growth-research.md](v2-d71-vocab-growth-research.md)・lit 8 本・親確認 5 件 → 設計アジェンダ [v2-vocab-growth-design.md](../design/v2-vocab-growth-design.md))。空欄 13 件は答申 §3(ATUS 465 の再計数・ASI・Voyager 付録・MAST 14 型 ほか)。
> 最終更新 **2026-09-16(第202)**: **R-23 第1批 完了**(設計書が引く 8 本・28 主張・答申 [v2-r23-primary-check-batch1.md](v2-r23-primary-check-batch1.md)・親確認 3 件 → PENDING D-74)。**R-2 完了**(lit 12 本+答申 [v2-r2-llm-social-sim-fulltext-check.md](v2-r2-llm-social-sim-fulltext-check.md)・親確認 4 件=OASIS/GAMA/Ye/Larooij・新発見 3: OASIS は超線形 N^1.5・事前登録の外部根拠は Larooij の 1 行のみ・TRAILS-R 5 次元が v2 に空白=v1 S-16 の置換忘れ → PENDING D-75・D-70 追記)。
> 最終更新 **2026-09-16(第200)**: §0 の Web 停止は **09-16 08 時に復旧**(第197)。R-24(法学)と A-3(反復回数=L-B)は第199〜200 で完了。
> 最終更新 **2026-09-15(第191)**。ユーザー指示 09-15「調べきれなかったところ・不明なところをきちんと明示して、進行状況を次のエージェントが理解できるようにしておいてほしい」。

---

## 0. いまブロックされていること(最重要)

**Web 検索と Web 取得が使用上限で止まっている。**

```
WebSearch → You've reached your Fable limit. Switch to another model, or manage usage credits...
WebFetch  → 同一のエラー
```

- **発生**: 2026-09-15 の第190(ECMWF の運用スケジュールを調べようとしたところ)から継続。
- **試行**: 第190 で 3 回、第191 で 2 回(WebSearch / WebFetch の両方)。**モデルを Opus 5 に切り替えても解消しない**。この環境では Web ツール自体が Fable 側の枠に紐づいている。
- **ユーザーの見込み(09-15)**: 「明日までトークンの回復が見込めない」。
- **したがって §2 の B-2 実行票は 1 行も実行できていない。** 記憶で埋めていない(CLAUDE.md §5)。

**Web が戻ったら最初にやる 3 手**(この順):

1. **R-23 の P1 24 本のうち、いま決定に効いているものから**([INDEX.md](INDEX.md) §1 の表)。~~特に R-24 = 法学 #11 の 2 本~~ → **R-24 は第199〜200 で完了**(W7 はその 2 本に依存していなかった・法学 #11 は答申 `v2-w7-law-primary-check-research.md` で A 等級・副産物 D-72)。
2. **第190 の未確認 4 件**(§2-A)。1 件あたり 1 回の取得で済む。
3. **R-2 の 11 件**(§2-B)。arXiv ID は判明済みなので機械的に消化できる。→ **第202 完了**(12 件・答申 [v2-r2-llm-social-sim-fulltext-check.md](v2-r2-llm-social-sim-fulltext-check.md)・lit 12 本・親確認 4 件)。

---

## 1. 2026-09-15(第191)にやったこと

Web を使わずに進められる分だけを実行した。

| | 何を | 結果 |
|---|---|---|
| A-1 | **[INDEX.md](INDEX.md) を新設** | v2 には答申 73 本の索引が 1 つも無かった(v1 には `references.md` と `research-scope.md` があった)。分野別・重要度別・一次確認の等級つき |
| A-2 | **73 本全部に 3 行ヘッダを付与** | 分野 / 重要度 / 一次確認の等級。**文言は一行も変えていない**(空行 1 行が詰まった 14 本が唯一の差分)。再生成は `python tools/research/build_index.py && python tools/research/gen_index.py` |
| — | **一次確認の等級を機械判定** | **A 2 / B 35 / C 1 / D 33 / E 2**。判定式=出典痕跡(URL + arXiv ID + DOI + ✔ + 「著者 年」)の総数。例外 4 本は親が中身を見て上書き |
| — | **D 等級 33 本の発見** | 2026-08-30〜09-01 の答申は **全部 URL 0 件**。09-02 以降は中央値 62 件。断層の理由は 09-03 のサブ捏造申告事件で親一次確認の規律が入る**前**のバッチだから。**救い: この 33 本に P0 は 1 本も無い** |
| — | **v1 原本との照合** | 33 本は v1 リポにも同名で存在し、**そちらも URL 0 件**(33 本すべて md5 比較)。→ コピー時に落ちたのではなく最初から無い |
| R-4b | **[v1-asset-triage.md](v1-asset-triage.md) を新設** | v1 固有の答申 126 本(約 32,000 行・URL 中央値 18)+ lit 43 本を v2 の穴に対応づけた。**R-5 可視化だけで v1 に 3,000 行超・URL 500 件超**がある |
| — | 残務台帳に **R-23〜R-26** を追加 | [research-backlog.md](research-backlog.md) §3b |

**やっていないこと**: v1 資産の**本文は 1 本も読んでいない**(lit 2 本を除く)。仕分けは題名・行数・URL 数だけ。

---

## 2. B-2 実行票(Web が要る。**全行 未着手**)

各行は「1 回の取得で 1 つの数値を確かめる」粒度にしてある。確認できたら該当の答申に確認日と手段を書き、[research-backlog.md](research-backlog.md) の行を消す。

### A. 第190 で取り切れなかった 4 件(最も安い)

| # | 確かめること | 行き先 | どこで使っているか | 状態 |
|---|---|---|---|---|
| A-1 | Park et al. 2023 の **「25 体 × 2 日で数千ドル・数日」**の原文 | arxiv.org/abs/2304.03442 の**本文 PDF** の Limitations/Future Work 節(抄録ページには無いことを確認済み) | 第190 の比較表・未踏の位置づけ | 未着手 |
| A-2 | Balmer et al. 2008 の **23 h(181,693 体)/ 36 h(2.3M 体)** | MATSim の公開 SVN にある `matsim-architecture` PDF(第190 の検索で URL を確認済み・未取得) | [lit/compute__matsim2020_hermes](lit/compute__matsim2020_hermes.md) の批判節 | 未着手 |
| A-3 | **✔ 第200 完了**(答申 [v2-replication-count-research.md](v2-replication-count-research.md)・等級 A・lit 7 本。Lorscheid 原典は有料で未読=二次で確認)← **ABM の反復回数の相場**(Lorscheid et al. 2012 の変動係数法 / Law & Kelton の信頼区間法) | JASSS(jasss.org)の該当論文。第190 では検索の統合のみで原典未読 | **D-70「N を減らす設計」の根拠**。G-8 の「初回 seed 群 8 本」が expedient のままなのを解消する | **完了(第200)** |
| A-4 | **部分(第200)**: メンバー数 51 の根拠と「小アンサンブル+fair score」は取得済み([lit/ensemble__ecmwf_ensemble-size](lit/ensemble__ecmwf_ensemble-size.md))。**配信時刻の規則値は未取得** ← **ECMWF の運用スケジュール**(10 日予報を何時間以内に出す決まりか) | ecmwf.int。**第190 はここで使用上限に当たった** | 「実用」の外部基準をもう 1 つ持つため。計器盤 G-8 のスコアカード様式も ECMWF 由来だが**原文未読**(R-14) | **部分(第200)**・配信時刻は未着手 |

### B. R-2 — LLM 社会シミュ文献の本文実読 11 件(arXiv ID は判明済み)

出所: [v2-llm-social-sim-timeline-seed.md](v2-llm-social-sim-timeline-seed.md) §4。いまは**抄録レベルのみ**。

| # | 論文 | ID | 本文で確かめること | 状態 |
|---|---|---|---|---|
| B-1 | Examining Identity Drift(Choi et al.) | arXiv 2412.00804 | 「大きいモデルほど漂う」の効果量。D-68 の同一性設計へ | **完了(第202)** |
| B-2 | Systematic Biases in LLM Simulations of Debates(Taubenfeld・EMNLP 2024) | arXiv 2402.04049 | 党派ペルソナの基底回帰の大きさ。広告の過剰反応(D-56 系)と同根かの判定 | **完了(第202)** |
| B-3 | StateAct(Rozanov & Rei) | arXiv 2410.02810 | 状態を「LLM の出力の中に書く」方式の効果。知覚テンプレの状態欄へ | **完了(第202)** |
| B-4 | The Effect of State Representation(Goodyear et al.) | arXiv 2506.15624 | どの書き方が均衡に近づくか。知覚テンプレ 3 層の設計変数 | **完了(第202)** |
| B-5 | GAMA + Agno(都市モビリティ) | arXiv 2607.02716 | **表 3 の計算費**(有志の「3〜5 倍」は抄録に無い)。D-70 の比較表に 4 例目として入る可能性 | **完了(第202)** |
| B-6 | Larooij & Törnberg「検証が中心課題」 | AI Review 2025-11-18・**PMC で全文公開** | face-validity 依存とデータ漏洩の警告の具体。holdout の作法の外部根拠 | **完了(第202)** |
| B-7 | AI Agents Alone Are Not (Yet) Sufficient | arXiv 2603.00113 | **処方側の記述**があるか(親は脆さ側で読んだ・有志は処方側で読んだ) | **完了(第202)** |
| B-8 | 頑健性監査(Ye et al.) | arXiv 2605.18890 | **事前登録の推奨が本文にあるか**(#14 の実体探索を兼ねる)。TRAILS 3 層を C8 ablation へ写すか | **完了(第202)** |
| B-9 | Causal Agent Replay(Shah) | arXiv 2606.08275 | 介入再生の手続き。この repo はテープ再生で同一確認済みだが**介入再生は未実装** | **完了(第202)** |
| B-10 | Steering Geometry | arXiv 2609.06289 | 指示微調整後の劣化の程度。採らない道の確認 | **完了(第202)** |
| B-11 | Procedural Graphs(Lu et al.) | arXiv 2609.09153 | 手続き知識グラフ。第2陣の記憶/習慣の表現候補 | **完了(第202)** |

**+ B-12(完了・第202・親確認)**: OASIS(arXiv 2411.11581)の **1M 体×1step = 18h / A100×27・100k×1step = 3h / A100×5** を一次確認 → [lit/](lit/) へ。**v1 の `docs/lit/mas__yang2024_oasis.md` に既に記録がある**ので、原典と突き合わせるだけで済む。第190 の比較表の 3 例目。

### C. R-3 — 個体の同質性の残 10 件(D-68 経路3 の設計に効く)

出所: [v2-d68-behavioral-diversity-research.md](v2-d68-behavioral-diversity-research.md) §8。

日本の始業時刻分布表 / 片道通勤時間の分布(**令和3年の表 ID が未特定**) / Schneider 2013 Fig.3 の p(ID) 数値 / Schlich & Axhausen 2003 原典 / inverse scaling と REAL Sampling の本文 / arXiv 2604.01520 の扱い / Song 2010 の追試値 / 交替制の出勤時刻 / 日本 PT へのモチーフ適用研究 / TrajLLM の定量評価。**全件未着手。**

### D. R-10〜R-16 — 既に使っている数値の裏取り(債務)

| # | 何 | 主な空欄 | 状態 |
|---|---|---|---|
| R-10 | 知覚 §10.2 | 日本語成人の最大読書速度 cpm / 中小媒体の p_see(0.14-0.40 は**英仏からの流用**)/ ISO 9921 数表 / Milgram 1969 原典 / Hyman 2010 の群別 n | 未着手 |
| R-11 | p_notice 系 10 件 | Simons & Chabris の内訳 / Haun 2021 E2(**孫引きの疑い**→原典 JOV)/ 周辺視の運動検出閾値 / Bouma 定数 / 視覚探索スロープ / Johnson 原典 / ANSI S3.5-1997 / IEC-EN 62676-4 の DORI / 夜間の認識距離 / 群衆遮蔽度 4 段 | 未着手(**規格本文が大半**) |
| R-12 | 会話契約の二次引用 | Mastroianni 2021 PNAS(**持続時間の分布が空欄**)/ Sellen 1995 / Robbins & Karan 2020(press release 経由)/ Zhou 2005 / Mollenhorst 2014(**内層の年間入替率が空欄**)/ ALFWorld | 未着手 |
| R-13 | 聴覚 | hearing_verification の汚染除去版の正典化 / Forssberg(**原典不明**)/ 消防法条文の e-Gov 直接確認(**API 404**) | 未着手 |
| R-14 | 計器盤 | Augusiak 2014 要旨 / **Siepe 2024 の反復回数式**(= A-3 と同じ問題)/ **ECMWF 原文**(= A-4)/ History Matching for ABM(2501.00616)/ LLM エージェント評価サーベイ(2507.21504) | 未着手 |
| R-15 | 倫理・公開 | OASIS 付録 I 全文 / Generative Agents §8.3 の残り / 日本心理学会倫理規程 / Five Safes 原文 / EU AI Act 50 条(2) 原文 / HF データセットカード | 未着手 |
| R-16 | F-8 サーベイ 4 件 | PIMMUR 6 原則の準拠表 / Unawareness 監査の実 LLM 自己言及率 / 数日連続稼働のドリフト / 2604.01520 考察節 | 未着手。**v1 に `pimmur-compliance` と `pimmur-results` がある**([v1-asset-triage](v1-asset-triage.md) §1-1)=先に読むと安い |

### E. R-17〜R-22 — 公的データの取得(調べる先は分かっている)

| # | 何 | 障害 |
|---|---|---|
| R-17 | PT 2018 c-2 / b-4 | tokyo-pt.jp の**同意ページ越し=ブラウザ操作が要る(ユーザーの手)** |
| R-18 | OSM 道路名の再取得(Overpass) | 公的ドメイン外。読み取りのみ・数 KB |
| R-19 | 5 エリア境界の座標化 | OSM 線形化 / SCJ 施設 214 件の属性一致 ≥90% / 区への照会 |
| R-20 | 都環境局 自動車交通騒音の最新年度表 | いま H23 で代替中 |
| R-21 | チェーン公式の営業時間表(上位 300 件)・駅構内図 | 手入力。API 規約=法務レーン |
| R-22 | PLATEAU 渋谷区 2023 年度版+追加メッシュ / 再生候補日の選定 | 未決 |

### F. R-23〜R-26(第191 で新規)

[research-backlog.md](research-backlog.md) §3b を参照。~~R-24(法学 #11 が両方 D 等級)が最優先~~ → **R-24 完了(第200・等級 A・D-72 8 件へ)**。**L-B も第200 で完了**(答申 [v2-replication-count-research.md](v2-replication-count-research.md)・A)。次の優先は R-23(出典ゼロ 33 本)と R-2(11 件)。→ **第202: R-23 第1批 完了**([研究残務 R-23 行](research-backlog.md) に要約・値を直す 4 件は PENDING D-74)。第2批は背骨の 4 答申(economy-sfc / conversation / llm-mobility / institutions)から。

---

## 3. Web なしで進められる残り(いま着手できる)

[v1-asset-triage.md](v1-asset-triage.md) §4 が順序つきの手順書。要約:

1. **lit 層へ v1 から 6 本を読み替え複写** — `network__diffusion`(#14)/ `method__experiment-design-statistics`(#23)/ `measurement__validation`(#26)/ `mas__yang2024_oasis`(#25)/ `labeling__cultural-evolution`(第3陣)/ `urban__lynch1960`(可視化)
2. **R-5 可視化の v1 資産 6 本を通読**(約 3,000 行)→ 第177 M2 の段階案。**水曜の可視化判断の材料**
3. **D-70 の v1 資産 3 本**(`scale-feasibility` は**同じ vLLM 7GPU の試算**)→ 2 h/シミュ日 が届くかを照合
4. **#23 統計学・因果推論の答申を起草**(v2 でゼロの分野・v1 に 7 本ある)
5. **`crime-llm-cognition`** → #32 を埋める(F-3)
6. **C 等級 1 本**(ad-information)を読んで空欄の有無を判定(R-26)

---

## 4. 取得不能と確認済み(**再探索しない**)

[research-backlog.md](research-backlog.md) §6 が正。時間を使わないこと:
渋谷駅の時間帯別乗降人員 / 来街者の来訪頻度の公的分布 / 日本人来街者の平日滞在時間 / 「試みたが環境が支えない行動」の採掘研究 / 5 エリアの町丁目リストによる定義 / 平日休日比(KDDI)。

## 5. 作法(CLAUDE.md からの抜粋・リサーチに効くもの)

- **記憶で埋めない**。読んでいない項目は空欄のまま残す(§5)。
- **リサーチサブは子サブを起動しない**。子の未完了・タイムアウトは「空欄」として報告する(§5)。
- **答申の出典・数値・条番号は正典化前に親が一次確認**(§5)。検収 = ファイル実在 + 出典 URL の実読 + 主要数値の再計算。
- **Web からのファイルダウンロード実行はしない(読むだけ)**。例外は政府・公的機関ドメインのデータファイルを gitignore 下の `data/` へ(§7)。取得ごとにライセンス台帳へ行を追加。
- **論文リンクは正規ドメイン**(arxiv.org / doi.org / 公的機関)を安全確認してから記載。未検証ならリンクを張らず「未検証」と書く。
- 新しい答申を書いたら、末尾の「空欄(未確認)」を[残務台帳](research-backlog.md)へ**写す**(答申の中に埋めない)。
