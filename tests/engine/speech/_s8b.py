"""第 1 期 1-8b 発話の口の試験の道具(腕の切り替え・小さなラン・テープの B6 の読み出し)。"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any, Iterator

import pyarrow.parquet as pq

from shibuya.engine.speech import layer as SPL

#: 合成の世界(data 無し)の小さなラン(会話が起きる=関係 on・会話の相手が見える 9 セル)。
SMALL: dict[str, Any] = dict(n_agents=200, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False,
                             vocab_version="v3", memory="on", relations="on", rel_copresent="on", store_memory="on",
                             checkpoint_every=60)


@contextlib.contextmanager
def speech_arm(name: str) -> Iterator[None]:
    """腕を一時的に切り替える(試験の後は元に戻す)。"""
    prev = SPL.arm()
    SPL.set_arm(name)
    try:
        yield
    finally:
        SPL.set_arm(prev)


def run_small(arm: str, tape: Path | None = None, **kw: Any) -> Any:
    from shibuya.engine.run import run_day

    args = dict(SMALL)
    args.update(kw)
    with speech_arm(arm):
        return run_day(tape_path=None if tape is None else str(tape), **args)


def tape_rows(tape: Path) -> list[dict[str, Any]]:
    """テープの呼の行(B6 の本文を ``b6`` に引いた形)。"""
    calls = pq.read_table(tape / "calls.parquet").to_pydict()
    blocks = pq.read_table(tape / "blocks.parquet").to_pydict()
    text_of = dict(zip(blocks["block_id"], blocks["text"]))
    out = []
    for i in range(len(calls["call_id"])):
        row = {k: calls[k][i] for k in calls}
        row["b6"] = text_of.get(row["b6_block_id"], "")
        row["shared"] = tuple(text_of.get(b, "") for b in row["block_ids"])
        out.append(row)
    return out
