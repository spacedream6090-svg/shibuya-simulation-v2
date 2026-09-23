# Grimm & Railsback 2012 — Pattern-oriented modelling: a "multi-scope" for predictive systems ecology

- リンク: https://pmc.ncbi.nlm.nih.gov/articles/PMC3223804/ | 分野: ABM 方法論 #21 / 科学哲学(モデルの認識論)#26 | 重要度: **P1**
- **一次確認**: **サブ実読**(2026-09-17・PMC 本文を取得して §1〜§5 から逐語採取)。**親未確認**。
  - 書誌: *Phil Trans R Soc B* **367**(1586):298–310、**doi:10.1098/rstb.2011.0180**、PMID 22144392、PMCID PMC3223804。
  - **本メモは Grimm et al. 2005 *Science* 310(5750):987–991(doi:10.1126/science.1116681)の代替**。原典は有料で本文未取得(残務)。POM の「複数パターン・弱いパターン」の逐語は**本 2012 版から採ったもの**であって 2005 の文言ではない。

## 主張(claim)

**1 つのパターンに合わせることは簡単で、しかも間違った理由で合いうる**(equifinality)。したがって **POM は複数のパターンを同時にフィルタとして使い、合わないモデル・パラメタを却下する**多基準の設計・選択・較正である。**弱い(weak)パターンを捨ててはいけない**。

## 機構(mechanism)

| 段 | 逐語 |
|---|---|
| パターンの定義 | "**A pattern thus can be defined as anything beyond random variation**"(§2) |
| 単一パターンの危険 | "**Models can easily be calibrated to reproduce a single pattern of interest, but potentially for the wrong reasons.**"(§2・von Bertalanffy の equifinality を引く) |
| 単一では足りない | "**a single pattern is rarely enough to fully decode the internal organization and achieve structural realism**"(§2) |
| 複数同時 | "the central idea of POM is to use **multiple patterns, observed at different levels of a system's organization and scales**"(§2)/ "In POM, we seek models that **simultaneously** reproduce a diverse set of patterns."(§2) |
| フィルタ | "**Each pattern used in POM can be considered a filter that helps reject unacceptable models or parametrizations.**"(§2) |
| 弱いパターン | "**Weak patterns are often qualitative and can be described with a few words or numbers**"(§2)/ "**A weak pattern is less striking and therefore often easier to reproduce—in isolation—by multiple models**"(§2)/ §3(a) step 2 "**Do not ignore weak patterns.**" |
| 3 つの用途 | §3(a) 構造の設計 / §3(b) 部分モデルの選択("formulate alternative submodels representing the process and **treat them as hypotheses that we then try to falsify**"・step 3 "**reject submodels that cannot reproduce one or more patterns**")/ §3(c) 較正("each pattern is used as a filter, or criterion, for acceptance, but now it is **parameter values** being filtered") |
| 一文定義 | §4 "**POM is the multi-criteria design, selection and calibration of models of complex systems**" |
| 実例 | §5(b) カンジキウサギの周期: "**the single pattern that cycles exist is not sufficient to determine which models contain the mechanisms**" |
| 障害の指摘 | §1 第 3 の障害 = "traditional ecological theory and modelling have addressed **single patterns, observed at a single level of organization**" |

## 効く箇所(seam)

- **v2 のパターン台帳ゲート**(「どの現実パターン照合で使うか」を 1 行で書けなければ作らない)は POM の思想そのもの。**本メモはその原典側の逐語**。
- **ミクロ観察(M1)から出てくるものはほぼ全部「弱いパターン」**(「昼にバーで食べる体がいる」「待ち合わせが起きない」)。**弱いパターンは単独で主張にせず、束ねて台帳へ入れる**のが正しい置き場——本論文がまさにそう言っている。
- **逸話規律の最も一般的な形**: 「1 つ合った」は結論にならない。計器盤 面2 の k*(I_M ≤ 3)を**アンカー集合**で見る既決とも整合。
- **却下の道具としてのパターン**: v2 の「合わなかったアンカーを書く」(ODD の HARKing 禁止)と対になる。

## 「結論でなく機構として」の入れ方

- **借りない**: 生態学の例(カンジキウサギ・ブナ林)。
- **借りる**: (1) **パターン = 却下のフィルタ**という位置づけ。(2) **弱いパターンを捨てない・単独で使わない・束ねる**。(3) **部分モデルを「反証すべき仮説」として並べる**(v2 の腕・ablation と同型)。(4) **equifinality の警戒**——「合った」を「機構が正しい」と読まない。

## 数値(出所つき)

**本論文に v2 がそのまま使える数値は無い**(方法論の論文)。使うのは語彙と手順。

## コスト/スケール含意

パターンを増やすほど却下は強くなるが、**較正にかかるラン数は増える**(§3(c))。v2 では D-70(反復回数)・D-44(感度解析)と衝突する軸。**本論文はその費用の議論をしていない**。

## 批判・限界

- **2005 *Science* の原典は未読**。本メモの逐語は 2012 版のもので、2005 の文言として引いてはいけない。
- 生態学の文脈で書かれており、**LLM 判断層・40 万体・holdout 封印といった v2 の事情は一切扱っていない**。
- 「弱いパターンをいくつ束ねれば十分か」の定量的な線は書かれていない(**空欄**)。
- §5 の事例は全て生態学で、都市・社会系の例は無い。

## 関連

[[abm__grimm2020_odd-observation]](同著者・ODD 側)・[[validation__sargent2016_interval-test]](「帯の中」の検定)・[[stats__ogara2025_history-matching-abm]](非含意度による却下=POM のフィルタの統計版)・`../v2-micro-observation-research.md` §1-4
