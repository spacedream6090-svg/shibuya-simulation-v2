"""engine.systems — ``run_day`` を「状態の箱・系(読む欄と書く欄の宣言)・短い進行役」に分けた形(第 1 期 1-0)。

設計の正: ``docs/design/v2-run-day-decomposition-draft.md``(受入・ユーザー承認 2026-10-13)。結果不変
(byte-check 19 構成・2 日のラン・再開・系ごとの指紋で HEAD と同じ値)。

- ``allow``: 系の書く SoA の列を resolve の口の静的な閉包から作る道具(宣言の正)。

逐次ループ宣言: 各モジュールの docstring を見る(このパッケージの頂上には無い)。
"""
