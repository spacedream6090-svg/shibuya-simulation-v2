"""tests.fig — 論文用の図(``tools/fig``)の煙検査。

**実資産を読まない**: 図の描画関数は「データ dict → Figure」なので、小さな合成データを
渡して PNG が出ることだけを見る(実 journal・実テープ・holdout は開かない)。
実データでの実行は親が ``python tools/fig/fig_*.py`` を直接叩いて確かめる。
"""
