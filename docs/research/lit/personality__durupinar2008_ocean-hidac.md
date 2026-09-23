# Durupınar, Pelechano, Allbeck, Güdükbay & Badler 2008 / 2011 — OCEAN 性格モデルで群衆の個体差を作る(HiDAC)

- リンク(2008 短報 PDF): https://www.cs.upc.edu/~npelechano/AAMAS08_Durupinar.pdf / リンク(2011 誌): https://doi.org/10.1109/mcg.2009.105 | 分野: ゲームエンジン工学・CG #30 / 人格心理学 #13 | 重要度: **P2**(**「数値で持ってエンジンに写す」の直接の先行**)
- **一次確認**: **実読**(2026-09-17・サブが AAMAS 2008 短報 PDF を WebFetch 取得 → pymupdf で本文抽出 → §2.2「Integrating the OCEAN Model into HiDAC」と §2.3「Personality to Behavior Mapping」を逐語照合)。**2011 年の IEEE CG&A 版は未読(抄録・二次情報のみ)**。**親未確認**。

## 主張(claim)

群衆シミュレータ HiDAC の低水準パラメータは数が多く(12〜13 本)、意味が分かりにくい。**OCEAN(Big Five)の 5 次元を上位の操作子に置き、そこから低水準パラメータへ写す**ことで、ユーザーは心理学的な概念だけを触ればよくなる。2011 年版のユーザー調査(70 名)では、参加者は特性を有意に知覚した(p<0.005)。

## 数値・形式(§2.2–2.3・逐語 ≤125 字を含む)

- 個体の性格 **π = ⟨Ψ_O, Ψ_C, Ψ_E, Ψ_A, Ψ_N⟩**。
- 群(subgroup)ごとにガウス分布: **Ψ_i = N(μ_i, σ_i²), i ∈ {O,C,E,A,N}**、**μ ∈ [0,1]、σ ∈ [−0.1, 0.1]**。
- 行動 **β = (β_1, …, β_n)、β_j = f(π)**。
- **双極**: 「A positive factor takes values in the range [0.5 1], whereas a negative factor takes values in the range [0 0.5)」。符号なしの表記は両極が当てはまる。
- **重み**: 「The sum of the weights for a specific type of behavior is 1.」ある行動を定義する形容詞が多い因子ほど、その行動への影響が強い。例: ω_EL は外向性のリーダーシップへの重み・[0,1]。
- 具体例(リーダーシップ): **β_i^Leadership = ω_EL f(Ψ_E) + ω_AL g(Ψ_A) + ω_CL Ψ_C + ω_NL (1 − Ψ_N)**(f・g は条件分岐つき)。
- 効果: 「decreased the number of parameters that need to be set from 12 to 5」(2008 短報)/ 2011 年版では 13 → 5。
- 2011 年版(**二次**): 参加者 70 名。「Emergent behaviors in crowds depend significantly on the personality distributions of subgroups」。

## 機構(mechanism)

**性格を「数値のベクトル」として個体に持たせ、重み付き線形結合でエンジンのパラメータに写す**。テキスト生成も LLM も一切介さない。個体差はパラメータ空間の位置として実現される。

## 効く箇所(seam)

- 本 repo の「**数値で L0 に持ち、B5(プロンプト)には言葉にしない**」案の、**最も近い先行**。
- 分布の形(群ごとのガウス・[0,1] クリップ)も、本 repo の抽選案とほぼ同型。
- **「パラメータ 13 本 → 5 本」という圧縮の主張**は、本 repo の expedient 削減(手で置く係数を減らす)と同じ動機。

## 「結論でなく機構として」の入れ方

**重み ω を輸入しない**。輸入するのは「特性ベクトル → 重み付き結合 → エンジンパラメータ」という**形**だけ。**重みは実測された効果量(r)を目標に較正する**——ここが本 repo が先行と分かれる点。

## コスト/スケール含意

5 float × 体数 + 重み行列。無視できる。40 万体でも 8 MB。

## 批判・限界(これが本メモの主眼)

1. **★写像が手書き**。著者自身が「a plausible mapping」と書く。**実測の効果量に基づいていない**。そのまま真似ると、**マッピング全体が設計者の指紋**になる(CLAUDE.md §3「設計者の指紋の最小化」に正面から反する)。
2. **検証の目標が「知覚された性格」**。ユーザー調査で「外向的に見えたか」を測っており、**現実の人の行動量に合っているかは測っていない**。本 repo が欲しいのは後者。
3. 群(subgroup)単位の μ・σ を**ユーザーが指定する**設計。本 repo は母集団の規準分布から引くので、ここは置き換わる。
4. σ ∈ [−0.1, 0.1] という表記(標準偏差が負を取り得る)は原文ママ。**分散の指定として不自然**=原著の記法上の曖昧さ。
5. **2011 年 IEEE CG&A 版の写像表(どのパラメータにどの因子が効くか)は未読**=空欄。
6. 関連: Guy, Kim, Lin & Manocha 2011(SCA・DOI 10.1145/2019406.2019413)は **OCEAN ではなく Eysenck PEN**で、RVO2 の 5 パラメータ(近傍距離・最大近傍数・計画地平・半径・希望速度)への**線形写像を被験者実験から推定**した。手書きでない点は 1 段良いが、**推定の目標はやはり「知覚された性格」**。**本メモの Guy 2011 に関する記述はすべて二次(検索要約)**。

## 関連

- [[crowd__bosina-weidmann2018_fd-generic-model]] / [[crowd__kretz2015_kladek-formula]](同じ層のパラメータを扱う)
- [[personality__harari2020_sensing-sociability]](写像の目標にすべき実測)
- 答申 [v2-personality-traits-research](../v2-personality-traits-research.md) §3-4(a)
