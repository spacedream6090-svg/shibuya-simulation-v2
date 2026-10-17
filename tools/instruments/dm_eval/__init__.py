# -*- coding: utf-8 -*-
"""dm_eval — 第 6 期 6-1 判断モデル(DM)の**評価の器**(GPU の前に作る分・読むだけ・エンジン不変)。

正典
    決定 ``docs/design/v2-wallbounce-decisions-2026-10-12.md`` §4-7(DM-0 候補は 5 つの源・DM1 候補と基準・表
    「人らしさ × 速さ × 1 シム日あたりの GPU 時間」はユーザーが選ぶ・DM4 状況の渡し方・DM5 驚きと迷い・DM9 厳密モード)・
    §4-8(住人の第一言語)・§1-9(速さ・性能・計算量を合わせて判断する=順位は付けない)。計画 6-1 と回答 2-1
    (``docs/design/v2-plan-answers-2026-10-12.md`` §2-1=評価セットと比べる道具・位置の偏りの試験を GPU の前に)。
    1-10 の評価セット(``docs/bench/analysis/wallbounce-1012/evalset-1-10/README.md``・状況 340 件)と 1-8 の候補の口
    (``src/shibuya/engine/decision/``・``j0/README.md``)。R-108(選択肢の形式の偏り・巡回の並べ替え・PBS)。

モジュール
    - ``situations``: 状況の読み口(1-10 の 340 件 → DM4 の短い版/長い版を ``engine.decision.port.compose`` で作る・
      長さの腕 t300/t1000)と候補の口(DM-0 の 5 つの源を記録から付ける・``present`` で並べ替え)。
    - ``judge``: 候補の当て口 ``Scorer``(mock・古典・テープを実装・Clef/Kev/即断/(G) は口だけ)・採点の器(分布の一致・
      自己整合・迷い・驚きの読み口・人のデータの欄=空)・速さと GPU 時間の式(値は空欄)・厳密モードの検査(DM9)。
    - ``bias``: 位置の偏りの対照試験(R-108・巡回の並べ替え・1 位が変わる率・番号 1 を選ぶ率・PBS・符号反転の検定)。
    - ``table``: 表「人らしさ × 速さ × 1 シム日あたりの GPU 時間」(候補ごと 1 行・言語ごと・長さの腕ごと・順位なし)。
    - ``cli``: 1 回通して記録の JSON と表を書く。

守ること: モデルの重みは取らない・GPU とネットワークは使わない(S6 の後)・正解の表は作らない(人のデータと考慮集合の
研究の値は検証側=パターン台帳 §10-1)・テープの本文(LLM の応答の文)は記録に写さない(集計だけ)。
"""

from __future__ import annotations

import sys
from pathlib import Path

#: 記録の形の版(欄を足したり意味を変えたりしたら上げる)。
SCHEMA = "shibuya.tools.dm_eval/1"

HERE = Path(__file__).resolve().parent
INSTRUMENTS = HERE.parent
REPO = HERE.parents[2]
for _p in (str(REPO / "src"), str(INSTRUMENTS)):
    if _p not in sys.path:  # pragma: no cover - 実行時の経路
        sys.path.insert(0, _p)
