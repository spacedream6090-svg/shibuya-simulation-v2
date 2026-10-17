"""engine.systems — ``run_day`` を「状態の箱・系(読む欄と書く欄の宣言)・短い進行役」に分けた形(第 1 期 1-0)。

設計の正: ``docs/design/v2-run-day-decomposition-draft.md``(受入・ユーザー承認 2026-10-13)。結果不変
(byte-check 19 構成・2 日のラン・再開・系ごとの指紋で HEAD ``ee3abc7`` と同じ値)。記録は
``docs/bench/analysis/wallbounce-1012/run-day-decomp/impl-1-0.md``。

- 状態の箱: ``boxes``(``Box`` と 9 つの箱・``TickCtx``)。
- 系の宣言の表: ``table.SYSTEMS``(呼ぶ順の 1 つの表)・口 ``spec``(``Access``・``SystemSpec``・``make``)。
- 進行役: ``conductor``(``conduct``・``run_system``)。組み立て: ``build``。
- 系の本体: ``body``・``world``・``perceive``・``judge``・``decide``・``act``・``talk``・``remember``・``observe``・``day``・
  ``run_end``・``report``(群の名札とは別の置き場)。LLM の往復の口 ``llm_io``・状態と日の口 ``state_io``。
- 宣言の外を書いたら落ちる: ``guard``(系を呼ぶ間の許可)+``core.write_permit``(SoA の解除口)・``allow``(閉包)・
  ``static_check``(AST)・``probe``(試験のときの系ごとの全欄の差と指紋)・``overrides``(試験の負の対照)。

逐次ループ宣言: 各モジュールの docstring を見る(このパッケージの頂上には無い)。
"""
