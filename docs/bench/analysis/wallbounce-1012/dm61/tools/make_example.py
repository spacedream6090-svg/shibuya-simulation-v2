# -*- coding: utf-8 -*-
"""dm61 の記録の例(DM4 の短い版と長い版)を、個人の行でない**合成の状況 1 件**から作る(読むだけ・data を読まない)。

使い方(リポの根で・``PYTHONPATH`` に作業木の ``src``)::

    python docs/bench/analysis/wallbounce-1012/dm61/tools/make_example.py

出力は標準出力だけ(README の §2 の例はこの出力を貼った)。並べ替えの種は ``dm61-example``。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "tools" / "instruments"))

import dm_eval  # noqa: E402,F401
from dm_eval import situations as S  # noqa: E402

B0 = "[合成の前置き] あなたは街にいる一人の人物です。観測に書かれていないことは知りません。"
LINES = (
    "[B1 種別] あなたは来街者です。",
    "[B2 場所] 現在地は駅前の広場(地上)です。",
    "[B2 可視] 見えるもの: 物販店、駅の改札。",
    "[B3 時刻] 現在時刻は18時05分です。",
    "[B3 天候] 天候は晴、日照は日中です。",
    "[B4 密度] 歩行者密度は段階Cです。",
    "[B4b 近景] 25メートル以内: なし。",
)


def main() -> None:
    sit = S.Situation(sid="example-0001", blocks={"B0": B0, **S.split_blocks("\n".join(LINES))},
                      facts={"hour": 18, "minute": 5, "station_word_or_band": True, "shop_word": True},
                      strata={"kind": "来街者"}, agent_id=1, step=1085, wake_class=1, call_id="example")
    cands = S.candidates_for(sit, ("購入",))
    pres = S.orders(cands, sit.sid, n_orders=1, seed="dm61-example")[0]
    for arm in S.LENGTH_ARMS:
        for length in ("short", "long"):
            r = S.render(sit, pres, length=length, arm=arm)
            print(f"=== {arm} / {length}: {r.chars} 字(目安 {r.budget_chars} 字・共通部分 {r.common_chars} 字・"
                  f"時刻とお金の外の数字 {r.numbers_outside_money_time})")
            print(r.text)
    print("=== 候補の源:", ", ".join(f"{c.number}.{c.kind}={c.source}" for c in pres))


if __name__ == "__main__":
    main()
