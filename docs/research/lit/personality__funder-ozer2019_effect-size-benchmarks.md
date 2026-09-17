# Funder & Ozer 2019 — Evaluating Effect Size in Psychological Research: Sense and Nonsense

- リンク: https://doi.org/10.1177/2515245919847202 | 分野: 統計学・因果推論 #23 / 人格心理学 #13 | 重要度: **P1**(効果量の物差しは本 repo の全分野に効く)
- **一次確認**: **実読**(2026-09-17・サブが公開 PDF を WebFetch 取得 → pymupdf で本文抽出 → 要旨を逐語照合)。**親未確認**。*Advances in Methods and Practices in Psychological Science* 2(2), 156–168。

## 主張(claim)

効果量は「無情報な基準(恣意的な大中小)」か「誤導する変換(r を二乗する)」で誤読されている。**理解しやすいベンチマークと具体的な帰結**で評価すべき。その上で r の読みを 5 段で提案する。

## 数値(要旨の逐語・≤125 字ずつ)

- "an effect-size r of .05 indicates an effect that is very small for the explanation of single events"
- "an effect-size r of .10 indicates an effect that is still small at the level of single events but"
- "an effect-size r of .20 indicates a medium effect that is of some explanatory and practical use even in the short run"
- "an effect-size r of .30 indicates a large effect that is potentially powerful in both the short and the long run"
- "A very large effect size (r = .40 or greater) in the context of psychological research is likely to be a gross overestimate"

| r | 読み |
|---|---|
| .05 | 単一事象の説明としては**とても小さい**が、それほど長くない目で見れば結果を持ち得る |
| .10 | 単一事象ではまだ小さい。しかし最終的にはより結果を持ち得る |
| .20 | **中程度**。短期でも説明・実用に足りる |
| .30 | **大きい**。短期・長期とも強力 |
| ≥.40 | 心理学の文脈では**過大推定の可能性が高い**。大標本や追試では滅多に出ない |

**ベンチマークの例(Funder & Ozer 1983 の再解析)**: Festinger & Carlsmith 1959・Darley & Latané 1968・Milgram の古典 3 本を r に直すと **.36〜.42 に収まった**。「心理学の最も有名な実験でもこの範囲」。

## 機構(mechanism)

効果量の意味は**累積**で決まる。小さな r でも、①多数の人に、②繰り返し、③長期に作用すれば、帰結は大きい。**逆に、単一の意思決定を予測する力は小さいままである**。この 2 つは矛盾しない。

## 効く箇所(seam)

- **性格 → 行動の係数を置くとき**。目標 r が .17 なら「中程度の下端」であって「無視できる」ではない。
- **感度試験の判定線**。「effect size が .40 を超えたら過大推定の警報」という自動検査に使える。
- **r² にしない**という禁止。指標 B(行動分布 JSD)や相関系の報告で分散説明率を書かない根拠。

## 「結論でなく機構として」の入れ方

Cohen の旧慣例(.10/.30/.50)を捨てて、この 5 段を報告書の凡例に固定する。**数値を解釈なしで置かない**。

## コスト/スケール含意

なし(読み方の規約)。

## 批判・限界

1. ベンチマークは**信頼できる推定であることが前提**("when reliably estimated (a critical consideration)")。小標本の r にこの読みを当ててはいけない。
2. 「.40 以上は過大推定」は**心理学の文脈**の話。物理計測や決定論的な工学量には当たらない。本 repo でいえば、**人の行動に関する相関**にだけ当てる。

## 関連

- [[personality__soto2019_loopr]](追試で 23% 縮む=「信頼できる推定」の実測)
- [[personality__roberts2007_power-of-personality]](比較ベンチマークの実例)
- [[stats__lakens2017_tost-equivalence]](「差が無い」を主張する側の手続き)
- 答申 [v2-personality-traits-research](../v2-personality-traits-research.md) §2-0
