# Boero & Squazzoni 2005 — Does Empirical Embeddedness Matter? Methodological Issues on Agent-Based Models for Analytical Social Science

- リンク: https://www.jasss.org/8/4/6.html | 分野: ABM方法論 #21 / 検証とV&V #22 / 科学哲学 #26 | 重要度: **P1**
- **一次確認**: **実読(サブ・JASSS 本文 HTML)・親未確認**(2026-09-17)。JASSS 8(4) 論文 6。公開 2005-10-31。段落番号は JASSS の §x.y 表記。

## 主張(claim)

ABM は「人工世界の思考実験」として扱われすぎている。**モデルの型によって、経験データに何を求めるべきかが変わる**。型は 3 つあり、連続体をなす。

## 機構(mechanism)

### 1. 3 つの型(§3.2・逐語 ≤125 字)

| 型 | 定義 | 例 |
|---|---|---|
| **Case-based models** | 「**models of empirically circumscribed phenomena, with specificity and "individuality" in terms of time-space dimensions**」 | Artificial Anasazi・Moss & Edmonds の水需要 |
| **Typifications** | 「**refer to specific classes of empirical phenomena, and are intended to investigate some theoretical properties**」(Weber の理念型) | Fearlus・著者らの産業集積モデル |
| **Theoretical abstractions** | 「**"pure" theoretical models with reference neither to specific circumscribed empirical phenomena**」nor to a class of them。「a metaphor of a general social reality」 | ゲーム理論 ABM・Schelling 分居 |

**3 つは離散的な範疇ではなく連続体**(§3.3, §3.21–3.22)。図 1 の魚市場の例(マルセイユ → コート・ダジュール → 地中海 → 世界 → ダッチオークション)で階段を示す。

### 2. 型ごとの経験データの要求

- **Case-based**(§4.2): 集計データは手に入りやすい。「**More difficult is to figure out a good strategy for micro-level data gathering.**」
- **Typifications**(§4.30–4.32): 対象が事例でなく**類**なのでミクロ較正が難しい。「**typifications mostly lay upon theoretical analyses and second-order (un-direct) empirical data**」
- **Theoretical abstractions**(§4.60): 「**the level of abstraction implies the need of a strong and extensive empirical validation**」— 多数の異なる母集団か無作為化実験室実験のデータが要る。**抽象だから検証が軽くなるのではなく、逆に重くなる**。

### 3. 識別問題への答え(§2.12–2.13)

無限に多くのミクロ仕様が同じマクロを再現しうる以上、「**what else, if not empirical data and knowledge about the micro level, is indispensable**」で真の機構を特定するのか、と問う。→ **ミクロ側のデータが等結果性への唯一の処方**という立場。

データ取得は **direct(実験・当事者参加・質的・量的)/ indirect(二次データ)**、および **hard(量)/ soft(行動の質的規則)**の 2 軸(§2.17–2.21)。

### 4. 連続体の皮肉(§4.63・Carley を引く)

抽象モデルは透明でデータ不要に見えるが、産出する知識は一般的すぎて「a plethora of interpretations」を許し**反証しにくい**。事例モデルと理念型は一般化しにくく見えて「**paradoxically more easily falsifiable**」。

### 5. 検証と再現の位置づけ(§1.5, §2.1–2.2, §5.2)

docking / alignment / replication は **internal verification** の側であり、経験的較正・検証とは**別の脚**。さらに「**a unique method for empirically calibrating and validating ABMs does not exist, yet**」(§1.10, §4.1)。

## 数値(出所つき)

なし(方法論論考)。

## 効く箇所(seam)

- **この repo は明確に case-based**(特定の街・特定の日)。したがって要求は「**ミクロ水準のデータ取得戦略**」であって、抽象モデル用の広範な外部妥当性ではない。**アンカー台帳はまさにその戦略**。型を宣言すれば、要求される検証の量が決まる。
- **「抽象ほど検証が重い」**は直感に反するが、LLM 社会シムの多くが抽象(囚人のジレンマ・名付けゲーム)であることを考えると、**それらは本来もっと重い検証を要求される側**という含意になる。
- **verification と validation の 2 脚**の線引きは [[validation__larooij2025_generative-abm-validation]] の「内部整合性は verification であって validation ではない」と同じ。**2005 年に既にある規律**。
- **一般化の道筋**(§4.49–4.51): 事例を理念型に埋め込むか、代表的事例で理念型を試す。到達点は Merton の中範囲理論。→ 渋谷 1 事例から何が言えるかの設計に効く。

## 「結論でなく機構として」の入れ方

- **借りない**: 産業集積の実質。
- **借りる**: (1) **答申・設計書の頭に「この模型は case-based / typification / abstraction のどれか」を書く**。(2) **型に応じてミクロデータ取得戦略(direct/indirect × hard/soft)を宣言する**。(3) **verification(再生の同一性)と validation(現実との一致)を別欄に分ける**。

## コスト/スケール含意

なし。ただし「抽象ほど検証が重い」は**検証予算の配分の指針**になる。

## 批判・限界

- 2005 年。ベイズ較正・POM の定式化以前(POM は Grimm 2005 と同年)。
- 3 型は**連続体**と断っているので、境界判定の手続きは無い=**分類は書き手の宣言**。
- 事例は欧州の社会経済 ABM に偏る。
- 「唯一の方法は無い」で終わっており、**代替の合格線を与えない**。

## 関連

[[abm__windrum2007_empirical-validation]] ・ [[abm__grimm-railsback2012_pom-multiscope]] ・ [[validation__larooij2025_generative-abm-validation]] ・ [[abm__edmonds2019_modelling-purposes]] ・ `../v2-classical-vs-llm-simulation-research.md`
