# -*- coding: utf-8 -*-
"""leak_check — データ漏洩(学習データの混入)の検査の器(回答 11-01 §6・指示 11-01 段 1 の 4)。

正典
    回答 ``docs/design/v2-answers-2026-11-01.md`` §6(4 型のうち ①時点を切る ②名前を伏せる ④記憶の誘い出し は
    E 系列から毎回・③反事実の課題 は外に出す主張の前=C-3・架空名の腕を店名から施設と出来事へ広げる)。
    先例と当てはめ ``docs/reference/a1-research-2026-10-31.md`` §4-2・§4-3。店名の架空名の比較の腕
    ``docs/design/v2-wallbounce-decisions-2026-10-03.md`` §9-1。パターン台帳 ``docs/design/v2-pattern-ledger.md``
    §0 運用規則 9(訓練データ混入の疑いの欄)。

モジュール
    - ``sets``: 問いの集合(型 ① の日付と架空の出来事・型 ② の実名と架空名の対の場面・型 ④ の指示の型)を作り、
      ``question_sets/*.jsonl`` に書く(作り直すと同じバイトになる=試験で確かめる)。
    - ``backends``: 当て口(``mock``=決定的・``vllm``=127.0.0.1 の OpenAI 互換 ``/v1/chat/completions``)。
    - ``score``: 採点(型 ① の応答の分類・型 ② の JSD と 1 位の一致と名の向き・型 ④ の一致と最長共通部分列)。
    - ``run``: 型ごとに 1 回通して集計(``result.json`` の中身)と表(``table.md``)を作る。
    - ``cli``: ``run --type 1|2|4 --backend mock|vllm --out-dir …`` と ``summary``(台帳の 1 行をまとめる)。

守ること: 検証側の値(``*_validation_anchors_*``・封印の層・パターン台帳の照合値)は問いの集合に入れない。
実在の出来事(型 ① (b))と記憶の誘い出しの参照(型 ④)は親が後で ``data/leak_check/`` (gitignore の下)に置く。
記録には応答の本文を写さない(集計と分類の印だけ)・絶対の道筋を書かない。GPU と外のネットワークは使わない
(vLLM の口は 127.0.0.1 だけ)。③ 反事実の課題はこの器に入れない(主張の前に別途)。
"""

from __future__ import annotations

import sys
from pathlib import Path

#: 記録の形の版(欄を足したり意味を変えたりしたら上げる)。
SCHEMA = "shibuya.tools.leak_check/1"

HERE = Path(__file__).resolve().parent
INSTRUMENTS = HERE.parent
REPO = HERE.parents[2]
SETS_DIR = HERE / "question_sets"
#: 親が後で置く入力の置き場(gitignore の下)。
DATA_DIR = REPO / "data" / "leak_check"

#: 世界の時点(DT のスナップショット=回答 11-01 段 1 の 4)。
WORLD_DATE = "2026-07-13"

if str(INSTRUMENTS) not in sys.path:  # pragma: no cover - 実行時の経路(read_guard を読む)
    sys.path.insert(0, str(INSTRUMENTS))
