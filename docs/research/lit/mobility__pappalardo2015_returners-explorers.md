# Pappalardo ほか 2015 — Returners and explorers dichotomy in human mobility

- リンク: https://doi.org/10.1038/ncomms9166(Nat. Commun. 6:8166・OA)/ 全文 PDF https://barabasi.com/media/pub_imports/files/667.pdf | 分野: 人間移動科学 #3 | 重要度: **P0**
- **一次確認**: **実読(サブ・2026-09-17・上記 PDF を pymupdf で全文抽出)・親未確認**。**補足資料(Supplementary Figs 1-18)は未取得**=「k ごとの人口比の表」は本メモに無い(§数値の注を見よ)。

## 主張(claim)

人は **2 つの類型に割れる**。**k-returner** = 移動の広がりが「上位 k 地点」でほぼ説明できる人。**k-explorer** = 説明できない人。この二分は EPR モデル([[mobility__song2010_epr]])では再現できない。

## 機構(mechanism)

- 総回転半径 `r_g`(式1)と **k-回転半径 `r_g^(k)`**(式2・上位 k 頻度地点だけで計算)を比べる。
- 判定(**二等分法**・逐語): 「the bisector method classifies an individual as a k-returner if **r_g^(k) > r_g/2**」。SVM と EM クラスタリングでも同じ結果 → 以後は二等分法を使う。
- 比 `s_k = r_g^(k)/r_g` の分布 `P(s_k)` は **0 と 1 に二峰**。0 の山 = explorer・1 の山 = returner。
- **k を上げると explorer は returner になるが、逆はほぼ起きない**(逐語: 「while explorers gradually become returners as k increases, the opposite process is extremely rare」)。

## 数値(節・図番号まで)

- **標本**: GSM = 欧州キャリアの CDR **3 か月**・**67,000 人**(約 300 万人から「3 か所以上訪問」「平均通話頻度 f ≥ 0.5 h⁻¹」で抽出)。GPS = 中部イタリア 250×250 km を走った **約 46,000 台**・**1 か月(2011 年 5 月)**。地点は ISTAT 国勢調査セル。
- **均衡する k**(逐語・Fig. 4): 「The population reaches a balance of k-returners and k-explorers **for k = 4** for GSM.」GPS は「regardless of k, we always have more k-returners than k-explorers」。
- **k=2 の人口比**: **本文に直接の記述が無い**。Fig. 7 の**無作為化基準線**から読むと **2-returner ≈ 0.21 / 2-explorer ≈ 0.78**(逐語: 「obtaining RR_rand ≈ 0.21」「EE ≈ 0.81, EE_rand ≈ 0.78」)。無作為に親友を割り当てた場合の同類率 = 人口比なので、**GSM・k=2 で returner ≈ 21%・explorer ≈ 79%** と読める。**この読みは本メモの推論であって著者の記述ではない**=親の一次確認が要る(補足 Fig. 3 に k=2..10 の人口数の図がある)。
- **社会的同類性**(Fig. 7・逐語): 「the fraction of two-returners whose 'best friend' … is also a two-returner is **RR ≈ 0.27**」(無作為 0.21・p < 10⁻⁵)。explorer 側は **EE ≈ 0.81**(無作為 0.78)。**n 番目の友人まで n ≤ 15 で有意**。
- **切断べき則の当てはめ(Table 1)**: GSM `r_g^(2)` は r₀=0.82・a=1.89・r_cut=691.03、`r_g` は 5.5・1.60・250.11。**k が小さいほど指数 a が大きく、カットオフも大きい**。
- **EPR では再現できない**(Fig. 6・逐語): 「For k ≈ **60**, we have the perfect balance … as for the GSM data set for k = 4」「the EPR model **overestimates by more than an order of magnitude** the number of locations needed」。重力則を入れた **d-EPR で k ≈ 9** まで縮まる(実測 4 にはまだ届かない)。
- **d-EPR の実装(Box 1)**: 待ち時間 β=0.8・τ=17 h。行動選択 `P_new = ρ S^{-γ}`・**ρ = 0.6・γ = 0.21**(Song 2010 の値をそのまま使用)。探索先は重力則 `p_ij ∝ n_i n_j / r_ij²`(n = その地点から発信された総通話数=**集団レベルの人気**)。回帰先は訪問回数に比例。

## 効く箇所(seam)

- **P3 の「常連/探索の比」の判定関数**。`r_g^(k) > r_g/2` は v2 のテープから計算できる(体ごとの訪問セルと頻度がある)。**閾値が単純で恣意性が小さい**。
- **「探索は集団の人気に引かれる」= d-EPR の修正**。v2 の「棚が減る=店員の補充」と同じ向き(世界側の状態が選択を変える)。ただし **d-EPR は重力則を外から押し込む**ので、v2 では「人気」を**エンジンが観測している在圏・売上から**作るほうが筋が通る。
- **同類性 RR 0.27 vs 0.21** は **C10(関係)の観察点**。設計に入れず「出るか見る」側に置ける創発指標。

## 「結論でなく機構として」の入れ方

- **借りない**: 重力則(v2 は bbox 内の徒歩圏なので距離減衰の形が違う)。
- **借りる**: (1) **二等分法による 2 分類**を計器にする。(2) **均衡 k を報告する**(v2 の k が 60 側に寄ったら「EPR そのまま」の症状)。(3) **explorer→returner は起きるが逆はまれ**という非対称性を、長期ランの検査項に。

## 批判・限界

1. **k=2 の人口比が本文に無い**(上述)。補足未取得。
2. GSM は通話時しか位置が取れず、GPS は自家用車のみ → **どちらも「観測されない訪問」で分類が歪む**(著者自身が GPS で returner が多く出る理由として述べている)。
3. **観測期間依存**: 別研究(広州・Sustainable Cities and Society 2021)は「21 日で均衡」と報告(**本メモ未読=二次**)。v2 の 1 日ランでは**この指標は測れない**。
4. 地点 = 基地局/国勢調査セルで、POI ではない。
5. 距離が長い人ほど分離が明瞭 → **渋谷 bbox(139 ha)の内側だけでは r_g の幅が足りず、二分が出ない可能性がある**(v2 にとって最大の懸念)。

## 関連

[[mobility__song2010_epr]] ・ [[mobility__schlapfer2021_visitation-law]] ・ [[mobility__lu2013_predictability-civ]] ・ `../v2-preference-vector-research.md` §1
