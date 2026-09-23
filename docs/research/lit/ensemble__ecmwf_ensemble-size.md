# Buizza & Richardson 2017 / Leutbecher 2017 — ECMWF のアンサンブル・メンバー数(51)の根拠と「小アンサンブル+fair score」

- リンク: Buizza & Richardson "25 years of ensemble forecasting at ECMWF", ECMWF Newsletter 153 (2017-10, doi 10.21957/bv418o) https://www.ecmwf.int/en/newsletter/153/meteorology/25-years-ensemble-forecasting-ecmwf / Leutbecher "Ensemble size: How suboptimal is less than infinity?", ECMWF Annual Seminar 2017-09-13 https://www.ecmwf.int/en/elibrary/80289-ensemble-size-how-suboptimal-less-infinity(査読版 QJRMS 145 Suppl.1, DOI 10.1002/qj.3387=未読)| 分野: 不確実性定量化 #22 / 気象アンサンブル | 重要度: **P0**
- **一次確認**: **実読**(2026-09-16・第200・Newsletter は親が再取得し逐語一致・著者名も親が確認。Leutbecher はスライド PDF を親が pymupdf で抽出し逐語一致)。**QJRMS 査読版は未読**。

## 主張(claim)

- Buizza & Richardson: 「**one needs at least about 10 members for a good ensemble-mean forecast**」「**increasing the ensemble size from say 10 to about 50 was found to have a clear and detectable impact** … **Further increases beyond 50 have a smaller effect, on average, but can still have a detectable impact** [稀事象]」「**Resolution, forecast length and the number of ensemble members are key cost drivers**」。年表: Dec 1992 **33** members → Dec 1996 **33→51**(解像度増強と同時)。
- Leutbecher: 「50 member since Dec 1996 / **Why 50?**」。交換可能(iid)なアンサンブルでは **CRPS_M = (1+1/M)·CRPS_∞**。実測「**50 and 200 members are 2% and 0.5% worse than ∞**」。結論=「Operational ensemble forecasts: **50 members are too few**」「Research & Development: Small ensembles are highly efficient. **Two to four members may be enough for standard evaluations** (provided exchangeability in the ensemble generation and use of fair scores)」。

## 機構(mechanism)

メンバー数の罰は **1/M** で効く。fair score(有限 M のバイアス項 1/(2M²(M−1))·ΣΣ|x_j−x_k| を解析的に引く)で、**ラン数を増やさずに**無限アンサンブル相当の比較ができる。条件=**交換可能性**(ECMWF 自身も「完全には満たしていない」)。

## 効く箇所(seam)

- **M=8 → +12.5%**(16→6.25%・32→3.13%・50→2.0%)。8 seed は「運用」には 1 桁足りないが「**R&D(2〜4)**」は上回る=**G-8 を文献準拠で正当化できる唯一の枠**。
- 要る作業は (i) seed の交換可能性の検査(温度・初期配置・母集団抽出が同一分布か)(ii) JSD 等のスコアの fair 化(有限標本の正のバイアスを引く)(iii) 検出可能効果量の床の宣言。
- 「51」の明示的根拠文書は**見つからず**(10→50 の改善+逓減+資源との妥協、摂動 50=特異ベクトルの ± 対で偶数、+コントロール 1)。

## 「結論でなく機構として」の入れ方

「気象は 51 だから我々も 51」ではなく、**(1+1/M) の罰と fair 化の処方**を持ち込む。D-70 は「M を増やす」か「fair 化で M を小さく保つ」かの選択として書ける。

- 関連: [[stats__siepe2024_simulation-study-template]] [[validation__operational-validity-overview]] [[compute__agentsociety2025_parallel_framework]]
