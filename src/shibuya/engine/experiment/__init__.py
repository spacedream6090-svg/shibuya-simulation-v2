"""engine.experiment — 実験が世界に入る口(第 1 期 1-3・CP12)と反実仮想の器(第 3 期 3-3・CP5・CP14)。

- ``gate``: 実験の条件を原因とする出来事を書く唯一の口 ``admit``(原因の型 ``Experiment`` を作れるのはここだけ)。
- ``form``: 申込書 ``ExperimentForm``(知らない欄はエラー・決定的な JSON・決定の表 L0〜L4)。
- ``apply``: 申込書の改変を世界に入れる唯一の口 ``apply(form, world, t)``(決定だけを入れる=L0・L1 を実装・L2〜L4 は宣言)。
- ``layer``: 申込書をランに置く口(``staged``・組み立てが ``current`` で受け取る)・持ち主 ``ExperimentLayer``・系 ``experiment``・
  manifest の ``experiment``。申込書を渡さないランは何も変わらない。
- ``branch``: T0 までテープを再生して T0 から今の方策に切り替える分岐と R-71 の 4 つの確認(``branch_report.json``)。
- ``ensemble``: 初期状態 × モデル × 偶然・回す前に半分を封印・事前登録(CP14)・対の差の形(``salt_compare`` に渡す)・技量スコアの器。
  〔3-3b〕技量スコアの隣の生の点数の欄・封印の証拠の欄・床の分布(A/A の対の差)。
- 〔第 3 期 3-3b〕``switch``: T からの切り替えの口 ``ReplaySwitch``(T は計算のまとめの窓の頭・再生の箱は刻みごとに空・T から仮の
  モデル)と 4 つの確認の (c)(d) の分け(決定論の確認・床の分布・A/A の枝 2 本の最初の食い違いとの比べ)。
- 〔3-3b〕``checks``: 申込書の点検(CP5-1 の始まり 0 の予期しない改変=警告と記録・CP5-3 の名指しと混入の疑い=1 つの道具)。
- 〔3-3b〕``warmup``: 慣らし(CP5-6)の判定の規則と parameter(事前登録=日付ではなく規則・判定は計器
  ``tools/instruments/warmup_gauge.py``)。

逐次ループ宣言: なし。
"""
