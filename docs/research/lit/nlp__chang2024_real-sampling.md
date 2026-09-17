# Chang, Peng, Bansal, Ramakrishna & Chung 2024 — REAL Sampling(漸近エントロピー)

- リンク: https://arxiv.org/abs/2406.07735 | 分野: 自然言語処理 #27 | 重要度: P1
- **一次確認**: **実読(サブ・2026-09-17・arXiv HTML v1 の Appendix J と §1・§4)・親未確認**
- 主張(claim): **ベースモデル(事前学習のみ)では、モデルが大きいほど次トークンのエントロピーが単調に下がる**。この減衰曲線を外挿して得た「漸近エントロピー」との差(残差エントロピー)が幻覚の予兆になる。
- 機構(mechanism): 小さい LM は理想分布を学べず多くの語に確率を散らす(一様に近い ⇒ 高エントロピー)。形式的には「n-gram LM の平均エントロピー ≥ (n+1)-gram LM の平均エントロピー」(エントロピー関数の凹性による)。大きいモデルは文脈をより使えるので分布が鋭くなる。
- 効く箇所(seam): 既存答申 §3-4 が二次引用で置いていた「モデルが大きいほどエントロピーが低い」の**一次出所**。**8B か 32B かの判断で、どの層の多様性を議論しているかを切り分ける**ために引く。
- 「結論でなく機構として」の入れ方: **この論文の主張は「語レベル・ベースモデル」に閉じている**。v2 が使うのは instruct モデルの**意味的**多様性なので、この結果をそのまま「32B にすると多様性が下がる」と読んではいけない(そちらの根拠は [[nlp__springer2026_annotation-anchoring]])。
- 数値(節・付録まで):
  - **Appendix J「Why does the Entropy Decay as the Model Size Increases?」の逐語**: 「the average entropy across our Wikipedia validation set (**around 9M tokens**) steadily decreases as the model size increases. Furthermore, there are **90.2% contexts** given which the smallest Pythia LM (**70M**) has a larger next-token entropy compared to Pythia LLM (**6.9B**).」
  - 対象系列: **Pythia の de-duplicated 版 70M / 160M / 410M / 1B / 1.4B / 2.8B / 6.9B**(埋め込みを除いたパラメータ数の対数を横軸に)。Figure 2 がその減衰曲線
  - 訓練: Wikipedia 2021 + OpenWebText の**先頭 500 万行(全体の約 5.6%)**、Pythia 70M を 3 epoch 微調整、学習率 5e-5、分数多項式の最高次 K=10
  - 主実験: 70M の THF モデルで 7B LLM の事実性と多様性を同時に改善。対照的復号と併用で「outperforms **9 sampling methods**」
  - 一次確認の所属: Amazon AGI Foundations
- コスト/スケール含意: 補助モデルが 70M なので推論コストの増分は小さい。ただし**同一系列で 3 サイズ以上**が要る(v2 は 8B の単一系列なので THF は作れない)。
- 批判・限界: ①**次トークンのエントロピーは意味的多様性ではない**。語の選択が鋭くても意味が多様な場合がある(逆も)②ベースモデルのみ。instruct 化後は逆転しうる([[nlp__springer2026_annotation-anchoring]])③検証集合は Wikipedia の英文で、日本語の対話生成へ外挿できる保証はない④著者自身が「THF モデルは小さすぎて LLM のエントロピーを常に正確には予測できない」と書いている(Fig.6e)。
- 関連: [[nlp__springer2026_annotation-anchoring]] ・ 既存答申 v2-d68-behavioral-diversity-research §3-4(二次引用として記載されていた)
