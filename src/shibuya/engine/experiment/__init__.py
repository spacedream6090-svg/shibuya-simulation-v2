"""engine.experiment — 実験が世界に入る口(第 1 期 1-3・CP12)と反実仮想の器(第 3 期 3-3・CP5・CP14)。

- ``gate``: 実験の条件を原因とする出来事を書く唯一の口 ``admit``(原因の型 ``Experiment`` を作れるのはここだけ)。
- ``form``: 申込書 ``ExperimentForm``(知らない欄はエラー・決定的な JSON・決定の表 L0〜L4)。
- ``apply``: 申込書の改変を世界に入れる唯一の口 ``apply(form, world, t)``(決定だけを入れる=L0・L1 を実装・L2〜L4 は宣言)。
- ``layer``: 申込書をランに置く口(``staged``・組み立てが ``current`` で受け取る)・持ち主 ``ExperimentLayer``・系 ``experiment``・
  manifest の ``experiment``。申込書を渡さないランは何も変わらない。
- ``branch``: T0 までテープを再生して T0 から今の方策に切り替える分岐と R-71 の 4 つの確認(``branch_report.json``)。
- ``ensemble``: 初期状態 × モデル × 偶然・回す前に半分を封印・事前登録(CP14)・対の差の形(``salt_compare`` に渡す)・技量スコアの器。

逐次ループ宣言: なし。
"""
