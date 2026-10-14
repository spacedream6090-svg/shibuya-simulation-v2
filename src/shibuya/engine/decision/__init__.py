"""engine.decision — 候補の口 J0(第 1 期 1-8・DM-0・DM4・DM5・DM13・C-2)。

- ``port``: 口の型(``Candidate``・``Choice``・``DecisionContext``・``DecisionPort.choose``)と提示(順のシャッフルと番号)。
- ``sources``: 候補を 5 つの源から作る(J0 は語彙の残りをつなぎの印で載せる)。
- ``ports``: 3 つの実装(``MockPort``・``ClassicalPort``・``LlmPort``=同じ入口)。
- ``layer``: 腕 ``--decision-port {legacy,port}``(既定 legacy=今の道)と層(1 呼を口に通す・計器・判断の出来事)。

口の約束: ``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-8 候補の口 J0」。

逐次ループ宣言: なし(各モジュールの宣言を見る)。
"""
