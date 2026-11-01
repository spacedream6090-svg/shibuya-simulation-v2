"""第 6 期 6-5 記憶 MR の試験の共通(腕の切替・合成の世界の小さなラン)。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from shibuya.engine import memory_m1 as M1
from shibuya.engine import memory_store as MS

#: 合成の世界の小さなラン(記憶+関係+店の記憶・同席なし=人も記憶の腕も同じ設定で回せる)。
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="on", rel_copresent="off", store_memory="on", checkpoint_every=60)


@contextmanager
def arms(store: str = "events", *, rows0: int | None = None, caps: dict[str, int] | None = None,
         **kw: str) -> Iterator[None]:
    """器の腕と 6-5 の腕を一時的に選ぶ(組み立てが読む)。``kw`` は ``model``・``cue``・``people``・``embed_model``・``grain``。

    ``caps`` は上限なしの腕の種類ごとの行の上限(``episode``・``person``・``shop``=検収 M2・M4)。〔検収 M1〕人ごとの忘れる速さの
    seed は組み立てがランの母集団の seed を渡す(ここでは置かない)。
    """
    prev_store = MS.arm()
    prev = M1.arms()
    prev_rows0 = MS.rows0()
    prev_caps = MS.row_caps()
    MS.set_arm(store)
    for k, v in kw.items():
        M1.set_arm(k, v)
    MS.set_rows0(rows0)
    if caps:
        MS.set_row_caps(**caps)
    try:
        yield
    finally:
        MS.set_arm(prev_store)
        for k in ("model", "cue", "people", "embed_model", "grain"):
            M1.set_arm(k, getattr(prev, k))
        MS.set_rows0(prev_rows0)
        MS.set_row_caps(**prev_caps)


def mr65(res: Any) -> dict[str, Any]:
    """ランの manifest の ``memory_summary.memory_store.mr65``(腕の計器)。"""
    return res.run_manifest_fields()["memory_summary"]["memory_store"].get("mr65", {})
