# Honka, Hortaçsu & Wildenbeest 2019 — Empirical Search and Consideration Sets(総説)

- リンク: <https://host.kelley.iu.edu/mwildenb/handbook.pdf>(著者版・表紙は「Current version: April 2019」) | 分野: 計量経済(離散選択) / 消費者行動 / 小売科学 #17 | 重要度: **P1**
- **一次確認**: **実読(サブ・2026-09-17・PDF 全 76 頁を pymupdf 抽出)・親未確認**。**掲載先の書誌(*Handbook of the Economics of Marketing* Vol.1・Elsevier と思われる)は本 PDF に記載が無い=[二次・未確認]**。
- **なぜ引くか**: 「**候補は 3〜5**」の一次に最も近い実読。原典 Hauser & Wernerfelt 1990 の PDF は **JSTOR の画像スキャン(JBIG2)でテキスト層が無く、Table 1 が抽出できない**ため、本総説の逐語を使う。

## 主張(claim)

消費者は利用可能な全銘柄から選ばない。**検討する銘柄は驚くほど少なく、通常 2〜5 件**。この経験的事実が、探索費用・検討集合を明示的に入れた計量モデルの流れを生んだ。

## 機構(mechanism)

二段構造。第 1 段で探索/認知の制約により**検討集合**が決まり、第 2 段でその中から効用最大化で選ぶ。著者は「consideration set」「search set」「evoked set」「(endogenous) choice set」を**同義で使う**と明記(脚注 1)。

## 数値(節まで・逐語)

- **§1(導入)**: 「empirical marketing research in the 1980s found that many consumers effectively choose from (or "consider") a **surprisingly small number of alternatives – usually 2 to 5** – before making a purchase decision」(引用先: Hauser and Wernerfelt 1990, Roberts and Lattin 1991, Shocker ほか 1991)。
- **§3.1**: 「Hauser and Wernerfelt (1990) also provide an overview table with mean or median consideration set sizes from previously published studies and the Assessor database for a variety of product categories. They find **most consideration sets to include 3 to 5 brands**.」
- **散らばり(フロア併記・同じ節)**:
  - Roberts & Lattin (1991): **中央値 14**。ただし注 15(逐語)「they **equate consideration with awareness** and that **aided awareness** was used to elicit the considered brands」= **定義が違う**。
  - Siddarth ほか (1995): 「the average predicted consideration set includes **4.2 brands**」。
  - Bronnenberg & Vanhonacker (1996): 忠実客 **1.5** / 非忠実客 **2.8**。
  - Mehta ほか (2003): 液体洗剤とケチャップ(各 4 銘柄)で「average predicted consideration set sizes to vary between **1.8 and 2.8**」。
- **同じ節の別の知見**: 「most papers find that marketing mix variables **rather affect consideration than purchase**」(広告は効用でなく検討集合に効く)。

→ **「3〜5」は中心であって帯ではない。定義(認知か検討か)と手法(調査か走査データか)で 1.5〜14 まで動く。**

## 効く箇所(seam)

- **R-37 §2-2・§5-1(k の決め方)**: k=4 を中央に置き、**k∈{2,4,8} を感度腕**にする根拠。
- **R-37 §1-3 との独立一致**: LLM 都市シミュレーション側でも「LLM が **3–5** の候補 Neighborhood を選ぶ」が独立に採られている(When Plausible 付録 B.5)。**分野をまたいで同じ桁**。
- **広告レーン(収益化の主要領域)**: 「広告は効用でなく検討集合に効く」は、v2 の広告チャネル(知覚契約書 §3 の看板 (b))の**効き先を「候補集合への出入り」に置く**設計の外部根拠になる。

## 「結論でなく機構として」の入れ方

- **借りる**: 二段構造(候補集合 → 選択)と、候補数が 1 桁前半という桁。
- **借りない**: 品目別の具体値(**原典の表が取得できていない**)・探索費用の推定手法(v2 に価格探索は無い)。
- **注意**: 対象は**スーパーの銘柄選択**。**店舗選択(どの店へ行くか)ではない**。同じ「3〜5」を店に転用するのは v2 側の仮説であり、先行の直接支持は無い。

## コスト/スケール含意

なし(理論・総説)。

## 批判・限界

1. **掲載書誌が本 PDF に無い**(表紙は working paper 形式)。
2. **Hauser & Wernerfelt 1990 の Table 1 そのものは未取得**。<https://web.mit.edu/bwerner/www/papers/AnEvaluationCostModelofConsiderationSets.pdf> は JSTOR の画像スキャンでテキスト層が無い。DOI <https://doi.org/10.1086/209225>(OUP)は本文が有料。
3. Manski 1977(<https://doi.org/10.1007/BF00133443>)・Swait & Ben-Akiva 1987(<https://doi.org/10.1016/0191-2615(87)90009-9>)の本文は**認証が要る**ため未取得=答申 §6 ①。
4. 全部**米国の包装消費財**。日本・飲食店・都市の目的地選択の値ではない。

## 関連

[[retail__dube2010_state-dependence]] ・ [[retail__hotpepper2018_repeat-rate]] ・ [[mobility__santos2026_unconstrained-poi]] ・ 答申 `../v2-destination-choice-llm-research.md` §2-2 ・ `../v2-preference-vector-research.md` §2
