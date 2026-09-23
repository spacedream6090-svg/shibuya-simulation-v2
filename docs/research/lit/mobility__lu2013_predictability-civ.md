# Lu, Wetter, Bharti, Tatem & Bengtsson 2013 — Approaching the Limit of Predictability in Human Mobility

- リンク: https://www.nature.com/articles/srep02923 (Scientific Reports 3:2923, doi:10.1038/srep02923) | 分野: 人間移動科学 #3 | 重要度: P0
- **一次確認**: **実読(サブ・2026-09-17・全文 HTML)・親未確認**
- 主張(claim): Song 2010 の「93%」は**上限でも普遍値でもない**。粒度と設定が変われば **0.85(ハイチ)/ 0.88(コートジボワール)** になる。そして**理論上界は実際のアルゴリズムで到達できる**(MC(1) が 0.91)。
- 機構(mechanism): Π_max は Fano 不等式の極限解で、S_real(順序と滞在を含む真のエントロピー)から決まる。S_real はデータの**時空間粒度**に強く依存する — 1 日 1 点・サブプレフェクチャ単位なら情報量が減り、Π は Song の設定と違う値に落ち着く。
- 効く箇所(seam): D-68 の **M5(体ごとの行動エントロピー / Π_max)の合格線**。第2陣の記憶・習慣が「個人内規則性」を作れたかの**下限側の門番**(MC(1) で当たるか)。
- 「結論でなく機構として」の入れ方: 「Π_max を 0.93 に合わせる」ではなく「**同じ粒度で測った現実標本と突き合わせる**」。v2 のセル × 15 分は Song より細かいので、上界は下がる方向に出るのが正しい。
- 数値(節・図番号まで):
  - 標本: Orange の CDR 無作為 **500,000 人**(2011-12-01〜2012-04-28)。位置 = 基地局の属する sous-préfecture(19 州 / 255 サブプレフェクチャ / 237 に基地局)。予測可能性解析は「2 つ以上を訪問し 120 日超観測」= **208,288 人**。**1 日 1 点**
  - 逐語(抄録): 「the theoretical maximum predictability is as high as **88%**」「MC models can produce a prediction accuracy of **87% for stationary** trajectories and **95% for non-stationary**」
  - 本文(Regularity and potential predictability): S_rand の中央値 **2.0**。Fig.4B → L_i のみなら「cannot exceed **0.35**」、<Π_unc> ≈ **0.84**、<Π_max> ≈ **0.88**
  - Fig.4C: 「<Π_max> stays around **0.85** for a wide range of r_g ∈ [20, 300]」= 距離非依存の再現。ただし Fig.4E で**訪問地点数が増えると Π_unc・Π_max はほぼ線形に減少**
  - Fig.5A: MC(1)〜MC(7) の <γ> ≈ **0.91**、頻度のみの MC(0) は **0.85**。後半期に MC(0) は 0.88→0.77 に落ちるが MC 系は 0.92→0.87
  - Fig.7: S_real と <γ_i> の相関 **−0.849**(p<0.000)、Π_max と <γ_i> は **0.802**(p<0.000)
  - ハイチの 85%(逐語・**本論文による引用**): 「Lu et al analyzed a complete mobile phone dataset of **2.9 million** anonymous subscribers after the earthquake in Haiti in 2010 and found that … the predictability of people's movements remained as high as **85%**」(原典 Lu, Bengtsson & Holme 2012 PNAS は**未読**)
- コスト/スケール含意: なし(解析論文)。ただし「MC(1) で 0.91」は、**v2 が習慣を作れたかを一次マルコフで検定できる**ことを意味する=安い計器。
- 批判・限界: ①**1 日 1 点**の粗い時間粒度なので v2 の 15 分粒度とは直接比較できない②サブプレフェクチャは平均で数十〜数百 km²=セル単位の Π はこれより低く出るはず③非定常軌跡で実精度が理論上界を超える(0.95 > 0.88)= **Π_max は「安定していれば上界」という条件つき**④到達可能性制約を入れると上界はさらに 11–24 ポイント下がる(Smith et al. 2014・本文未読)。
- 関連: [[mobility__song2010_predictability]](未作成)・[[mobility__pflow2022_japan-motifs]]・既存答申 v2-d68-behavioral-diversity-research §1-1
