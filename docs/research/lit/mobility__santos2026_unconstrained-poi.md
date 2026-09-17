# Santos, Viana & Silva 2026 — When Plausible Is Not Realistic: Evaluating Human Mobility in LLM-Based Urban Simulation

- リンク: <https://arxiv.org/abs/2606.13835> / PDF <https://arxiv.org/pdf/2606.13835> | 分野: 人間移動科学 #3 / 検証とV&V #22 / 計算社会科学 #25 | 重要度: **P0**
- **一次確認**: **実読(サブ・2026-09-17・PDF 全 14 頁を pymupdf 抽出)**。**親は §5.1 Table 1/2/3 と §6.1 を第210 で確認済**(`../v2-r23-primary-check-batch2.md` §16・§17)。**本メモが新しく足すのは §3.1「Unconstrained POI selection」の逐語・付録 B.5(候補 3〜5)・§5.1 の「単純な重力が勝つ」の 2 逐語と 4 数値**。
- 書誌: SIGSPATIAL'26(Riverside, CA・2026-11-03〜06)採録。Inria。

## 主張(claim)

LLM 都市シミュレータ(AgentSociety・CitySim)は「もっともらしい物語」を作るが、実データの移動則には合わない。**そして合わない主因は POI 選択にある**。

## 機構(mechanism)— 本メモの中心

### (1) 名指しされた欠陥: 無制約 POI 選択(§3.1)

逐語: 「needs-driven mobility actions could **select destinations from the full set of POIs available in the simulated map**, rather than from POIs **semantically consistent** with the active need and **spatially plausible** given the agent's current context.」

結果(逐語): 「agents with low hunger satisfaction could be routed to **semantically unrelated or distant POIs**, producing unrealistic trip distances, dwell patterns, and activity transitions.」

→ **「候補集合を作る」ことは、先行が名指しした欠陥の是正であって、需要モデルの注入ではない。**

### (2) AgentSociety の型(§2.3)

LLM が **POI カテゴリ・サブタイプ・探索半径**を出し、エンジンが「**Density-aware Gravity model based on Distance-decayed Attraction**」で候補 POI を抽出。重み `w_i = ρ_k / d_i²`(ρ_k = 空間リング k の POI 密度・d_i = 候補 POI i までの距離)を正規化して選択確率にする。

### (3) CitySim 再実装の型(付録 B.5)

- 巨視(逐語): 「the LLM selects **3–5 candidate Neighborhoods** using the persona, **7-day visit history**, and matching-POI density. If this fails, the block **falls back to AOI-level selection ranked by distance and popularity**.」
- 微視: 選ばれた Neighborhood/AOI の中で **belief-weighted gravity model**。4 つの空間記憶信念を平均した `b_j` を使い、距離減衰は `distance^{1+γ(b_j−0.5)}`・**γ = 2.0**。
- → **LLM が候補を作り、エンジンが選ぶ**(= 親案 H と順序が逆)。

## 数値(節・表番号まで)

- **§5.1(H の方向への否定的証拠・逐語)**: 「the **simpler gravity-based destination selection** used in AgentSociety **outperforms CitySim's LLM-driven POI-selection strategy** in reproducing the most frequently visited urban areas.」「**Increasing POI-selection complexity does not necessarily improve** the reproduction of highly visited urban areas.」
  - GreaterParis・H3 解像度 8 の **STVD W₁ = AgentSociety 607.69 ± 5.88 / CitySim 748.71 ± 23.00**。Shanghai も AgentSociety が低い(数値は未取得=空欄)。
- **§5.1(逆向きの証拠)**: 個体レベルでは CitySim が良い。GreaterParis の **Δr 誤差 14.83 km → 7.53 km**、**回転半径誤差 7.29 km → 3.47 km**。Shanghai は Δr **3.97 km**・r_g **4.86 km**。
- **OD(フロア併記)**: 「OD-matrix agreement remains weak, particularly in the GreaterParis dataset (**CPC H8 = 0.138 ± 0.018**)」。**実データ同士の参照標本は H7 0.297 / H8 0.092 / H9 0.045**(親が第210 で確認)なので **0.138 は H8 のフロア 0.092 を上回る**。
- **§6.1**(親確認済): OSM POI の **57.45%** がベンチ・駐輪・ごみ箱等。Overture 追加で施設相関 **0.55 ± 0.23 → 0.80 ± 0.20**。
- **Table 6(検証指標の一覧)**: 距離 Δr(切断べき則 `P(Δr)=(Δr+Δr₀)^{-β}e^{-Δr/κ}`)・回転半径・日次訪問地点数・予測可能性 Π_max・**距離−頻度 `ρ_i(r,f)=μ_i/(rf)^η`(= Schläpfer 2021)**・OD 行列・移動時間・滞在時間・訪問頻度・モチーフ・**移動プロファイル = GMM(Intermittency, Degree of Return) → Scouters / Regulars / Routiners**・規則性・定常性・多様性・エントロピー・VPD・ATM・DARD・STVD。類似度は JSD・CPC・W₁。
- **§3.1 が挙げた AgentSociety の他の欠陥**: 訪問 POI とカテゴリを記録しない(逐語「prevents verification of whether destination choices are **genuinely needs-driven or effectively random**」)・ブロック実行順とプロンプト/応答対を記録しない。

## 効く箇所(seam)

- **R-37 §1-3 / §5-4**: H を採るかどうかの唯一の直接比較。
- **v2 の計器**: 「訪問 POI とカテゴリを記録しないと、行き先が本当に動機由来か無作為かを検証できない」= v2 のテープに**行き先 POI の列が無い**(P3 答申 §6-2)ことの外部根拠。
- **パターン台帳**: Table 6 が「この分野の標準の物差し一覧」。P-1(η≈2)・P-3(returners/explorers)が実際に使われていることの裏づけ。

## 「結論でなく機構として」の入れ方

- **借りる**: (1) 候補集合を「意味整合 ∧ 空間的にもっともらしい」で絞るという**制約の形**(値ではない) (2) **個体レベルと集計レベルを必ず両方測る**という検証の形(符号が逆になりうる)。
- **借りない**: 重力則 `S_j/D_ij^β`・`ρ_k/d_i²` を v2 に注入すること(`../v2-llm-mobility-research.md` §4 の「不可」)。
- **警戒**: 「LLM 主導の POI 選択のほうが良い」を前提にしないこと。**この論文は逆を報告している。**

## コスト/スケール含意

付録 E に token 使用量と API 費用の表(Table 8)があるが未取得(空欄)。

## 批判・限界

1. 対象は Greater Paris と Shanghai。**東京・渋谷ではない**。
2. CitySim は**著者による再実装**(En-AgentSociety 上)であり、原著者の実装ではない。§5.1 の比較はこの再実装に対するもの。
3. STVD W₁ は「10 分の時間差 = 100 m の空間差」という重みづけの近似 Wasserstein 距離。**重みが結論に効く**。
4. 2026-06 公刊=LLM の学習データに入りうる。

## 関連

[[leisure__bougie2025_citysim-shibuya-poi]] ・ [[mobility__feng2024_llm-move-candidate-order]] ・ [[mobility__schlapfer2021_visitation-law]] ・ [[mobility__pappalardo2015_returners-explorers]] ・ [[mas__amano2026_aggregate-stats-distill]] ・ 答申 `../v2-destination-choice-llm-research.md` §1-3・§4-1 ・ `../v2-r23-primary-check-batch2.md` §16・§17
