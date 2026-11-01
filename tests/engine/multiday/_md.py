"""第 2 期 2-3 の試験の共通(合成の世界の小さなランの設定・腕の切替・ランの記録と器を控える・道具の読み込み)。"""

from __future__ import annotations

import importlib.util
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from shibuya.engine import economy_stage2 as ES2
from shibuya.engine import memory_store as MS
from shibuya.engine import proximity as PX
from shibuya.engine.memory_store import MemoryStore

ROOT = Path(__file__).resolve().parents[3]
WORLD = ROOT / "data" / "world" / "v2"
STAGE = ROOT / "data" / "world" / "v2_stage_2-3"
TOOL = ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "md23" / "tools" / "multiday_md23.py"
#: 合成の世界の小さなラン(記憶+関係+同席+店の記憶=1-3・1-6 の試験と同じ腕)。
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="on", rel_copresent="on", store_memory="on", checkpoint_every=60)


@contextmanager
def arms(memory_store: str = "mem", proximity: str = "cell", economy_stage2: str = "off") -> Iterator[None]:
    """腕を一時的に選ぶ(組み立てが読む)。"""
    prev = (MS.arm(), PX.arm(), ES2.arm())
    MS.set_arm(memory_store)
    PX.set_arm(proximity)
    ES2.set_arm(economy_stage2)
    try:
        yield
    finally:
        MS.set_arm(prev[0])
        PX.set_arm(prev[1])
        ES2.set_arm(prev[2])


class Capture:
    """器に口を置く所を包み、ランの器と記録を控える(戻り値は変えない)。"""

    def __init__(self, monkeypatch: Any) -> None:
        self.store: MemoryStore | None = None
        self.log: Any = None
        orig = MemoryStore.attach_events
        cap = self

        def _attach(ms: MemoryStore, link: Any) -> None:
            orig(ms, link)
            cap.store, cap.log = ms, link.log

        monkeypatch.setattr(MemoryStore, "attach_events", _attach)


def tool() -> Any:
    """記録の道具(``md23/tools/multiday_md23.py``)を読み込む。"""
    spec = importlib.util.spec_from_file_location("multiday_md23", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod
