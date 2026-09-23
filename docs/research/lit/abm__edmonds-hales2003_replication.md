# Edmonds & Hales 2003 — Replication, Replication and Replication: Some Hard Lessons from Model Alignment

- リンク: https://www.jasss.org/6/4/11.html | 分野: 検証とV&V #22 / ABM方法論 #21 / ソフトウェア工学 #29 | 重要度: **P0**
- **一次確認**: **実読(サブ・JASSS 本文 HTML)・親未確認**(2026-09-17)。JASSS 6(4) 論文 11。受理 2003-07-13・公開 2003-10-31。段落番号は JASSS の §x.y 表記。

## 主張(claim)

*Nature* に載ったタグ協力モデルを **2 人が別々の言語で再実装**したところ、数値は一度合わず、合わせてみると**公刊論文の結論が本質的に別物だった**。「**An unreplicated simulation is an untrustworthy simulation**」。

## 機構(mechanism)

### 1. 対象と手続き

- 対象: Riolo, Cohen & Axelrod (2001) *Nature* 411:441–443。100 体・実数タグ+許容閾値。タグ差が許容内なら贈与(§2.1–2.7)。
- **2 本の独立再実装**: 実装 A = Java(Hales)・実装 B = SDML(Edmonds)(§4.1–4.2, §5.1)。**言語も人も分ける**のが設計。

### 2. 何が起きたか

- 2 本の再実装は**互いに一致したが、原典とは閾値で食い違った**。数値(§4.2, §7.1, Tables 3–5): 対戦 2 回で贈与率 **42.6%(再実装)対 4.3%(公刊値)**、コスト 0.5 で **約 46% 対 24.7%**。
- 原因は **トーナメント選択の同点処理の曖昧さ**(§8.3, §8.6)。再実装側は「同点ならランダム」と仮定していた。公刊値を再現できたのは "selected bias" 変種だけ。逐語: 「**it would appear that Riolo et al, used the "selected bias" method**」。
- **数値は合った。しかし結論は合わなかった**(§9):
  - タグ比較を `≤` から厳密な `<` に変えると贈与が**消える**(Tables 9–10, §9.2)。
  - 再生産時にタグへ微小雑音を足すと**消える**(Tables 13–14, §9.12)。
  - 個体数を 2 倍にすると**消える**(§9.13)。
  - 許容閾値を 0 に固定しても、3 つの選択法のうち 2 つで高い贈与率が**残る**(Tables 11–12, §9.7–9.11)。
- 著者の結論(§9.14–9.15・逐語 ≤125 字): 「**the tolerance mechanism was essentially irrelevant**」「**It seems that we now understand the published model better than the original authors.**」原論文の一般化は「**would appear to be false**」(§9.10)。

### 3. 処方(§10.1・整合作業の技法)

- 最初の数 tick で比べる(自己強化や混沌が出る前)。
- 多ラン長期平均に**2 標本 Kolmogorov–Smirnov 検定**。「**Often sets of figures that look the same fail this sort of test.**」
- 合わないなら**機能を 1 つずつ切ってから戻す**。
- 「**Use different kinds of languages to re-implement a simulation**」+可能なら**別人に書かせる**。

### 4. 規範(§11.2, §12.2・逐語 ≤125 字)

- 「**the description of the simulation should be sufficient for others to be able to replicate (i.e. re-implement) the simulation**」
- 結果は「**independently replicated by others and the results confirmed before the simulation or the results are taken seriously**」
- 「**An unreplicated simulation is an untrustworthy simulation - do not rely on their results, they are almost certainly wrong**」(注 16 で "wrong" = 実装が作者の意図と細部で違う、と限定)
- 「**One cannot prove that implementations are the same**」。信頼できるのは「only within the ranges that it has been tested」(§6.3)。
- §1.5: 「**almost certainly, the vast majority of published social simulations do not completely comply with their authors' intentions**」

## 数値(出所つき)

42.6% vs 4.3%(対戦 2 回)・約 46% vs 24.7%(コスト 0.5)。再実装 2 本・対象モデル 1 本・個体数 100(原典)。

## 効く箇所(seam)

- **「テープ再生で同一ハッシュ」は再現の一部でしかない**。ここで壊れたのは同一ハッシュではなく、**同点処理という 1 行の仕様の曖昧さ**。この repo の受入表に「順序・同点・終了条件の仕様を明文化したか」の欄を足す根拠。
- **数値が合っても結論が合わないことがある**(§9)。数値一致は relational equivalence の保証にならない。→ [[abm__axelrod1997_kiss-replication]] の 3 段と組で使う。
- **個体数を 2 倍にしたら現象が消えた**(§9.13)= **規模が効く/効かないは実験しないと分からない**。[[mas__yang2024_oasis]] の herd(100 では出ず 10,000 で出る)と**逆向き**の実例。両方を並べると「規模は単調に効くわけではない」と言える。
- **KS 検定で「図では同じに見えるものが落ちる」**は、この repo の受入表が図の目視に寄ることへの警告。

## 「結論でなく機構として」の入れ方

- **借りない**: タグ協力の実質(場面が違う)。
- **借りる**: (1) **整合作業の 4 技法**(初期 tick 比較・KS 検定・機能切り戻し・別言語別人)を検収手順に写す。(2) **「仕様の曖昧さ 3 点」= 更新順序・同点処理・終了条件**を公刊物の点検表にする。(3) **主要結果は 1 つの摂動(比較演算子・微小雑音・個体数 2 倍)で消えないことを示す**。

## コスト/スケール含意

再実装 2 本分の人手。**費用は計算でなく人**。

## 批判・限界

- **対象は 1 本のモデルだけ**。ここから「大多数の公刊シムが意図と違う」を導くのは著者の見立て(§1.5)であって測定ではない。
- 2003 年。コード公開・コンテナ・CI が普及する前の規範。
- 付録のコード URL(`cfpm.org/replication/riolo`)は**到達性未確認**。

## 関連

[[abm__axelrod1997_kiss-replication]] ・ [[abm__edmonds2019_modelling-purposes]] ・ [[mas__yang2024_oasis]] ・ [[nlp__atil2024_nondeterminism]] ・ `../v2-classical-vs-llm-simulation-research.md`
