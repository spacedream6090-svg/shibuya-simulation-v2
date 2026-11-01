"""試作: 系ごとに「書いてよい SoA の列」だけを解いて回す(HEAD 0389689・コードは変えない・走らせるときに差し替える)。

許す列 = allow.json の ``allow``(build_allow.py: 系が呼ぶ resolve の口の静的な書き集合の閉包=宣言の正)。
差し替えは 2 つ(草案 §2-6 の段 A の形を試作の中だけで作る):

1. 既存の解除口(AgentState.thaw・World.thaw・PerceptionState._set_writeable)を、いまの系の許可の列だけを解くものに。
   宣言の外の列への添字の代入・``fill``・``out=`` は numpy が ValueError を投げる。
2. 〔改訂(第330・検収 K1)〕numpy の ``ufunc.at``(``np.add.at``・``np.maximum.at``)は書き込みの旗を見ない(numpy 2.5.3)。
   resolve の中の ``np`` を代理に替え、``<ufunc>.at(arr, ...)`` の前に ``arr.flags.writeable`` を確かめる
   (=設計の「``_require_thawed`` を配列単位で見る」と同じ働き)。

守る範囲は〔改訂(第330・検収 K7)〕ループの中の系に加えて drain・close_final・report(ランの終わり)。組み立て(build)は守らない。
使い方: python guard_poc.py <構成名> <体数> <日数> [<外す 系:列>]
  外す列を渡すと、その系の許可から 1 列を外す(負の対照=落ちることを確かめる)。
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

import numpy as np

import shibuya.engine.run as RUN
from shibuya import cli
from shibuya.engine import resolve as R

HERE = Path(__file__).resolve().parent
src = (HERE / "dyn_writers.py").read_text(encoding="utf-8")
CONFIGS = eval(src.split("CONFIGS = ", 1)[1].split("\nBOUNDS", 1)[0])
BOUNDS = eval(src.split("BOUNDS = ", 1)[1].split("\nRUN_END", 1)[0])
LINE2SEG = {ln: s for s, ln in BOUNDS}
ALLOW = {s: set(v["allow"]) for s, v in json.loads((HERE / "allow.json").read_text(encoding="utf-8")).items()}
cfg, n, days = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
drop = sys.argv[4] if len(sys.argv) > 4 else ""
if drop:
    s_, c_ = drop.split(":", 1)
    if c_ not in ALLOW.get(s_, set()):
        raise SystemExit(f"負の対照の列 {c_} は {s_} の許可に無い(外しても意味が無い)")
    ALLOW[s_].discard(c_)

code = RUN.run_day.__code__
TOOL = sys.monitoring.PROFILER_ID
st = {"cur": None, "n_toggle": 0, "n_at_checked": 0}


def on_line(c, line):
    if c is not code:
        return sys.monitoring.DISABLE
    seg = LINE2SEG.get(line)
    if seg is None:
        return sys.monitoring.DISABLE
    st["cur"] = None if seg == "END" else seg  # 組み立て(ループの前)と END の後は守らない
    return None


# ---- 1. 解除口を「系の許可の列だけ解く」に ----
from shibuya.agents.state import AgentState  # noqa: E402
from shibuya.perception.state import PerceptionState  # noqa: E402
from shibuya.world.state import World  # noqa: E402


def _ok(key):
    return st["cur"] is None or key in ALLOW.get(st["cur"], set())


def _agents_thaw(self):
    for name, arr in self.registry.arrays.items():
        arr.flags.writeable = _ok(f"agents.{name}")
        st["n_toggle"] += 1
    self._frozen = False


def _world_thaw(self):
    for place, reg in (("cells", self.cells), ("pois", self.pois)):
        for name, arr in reg.arrays.items():
            arr.flags.writeable = _ok(f"{place}.{name}")
            st["n_toggle"] += 1
    self._frozen = False


_orig_pset = PerceptionState._set_writeable


def _pst_set(self, flag):
    if not flag:
        return _orig_pset(self, flag)
    for name, arr in self.registry.arrays.items():
        arr.flags.writeable = _ok(f"perception.{name}")
        st["n_toggle"] += 1


AgentState.thaw = _agents_thaw
World.thaw = _world_thaw
PerceptionState._set_writeable = _pst_set


# ---- 2. resolve の中の ufunc.at を配列の旗で止める ----
class _UfuncAtGuard:
    def __init__(self, uf):
        self._uf = uf

    def at(self, a, *args, **kw):
        st["n_at_checked"] += 1
        if isinstance(a, np.ndarray) and not a.flags.writeable:
            raise ValueError("ufunc.at で読み取り専用の配列へ書こうとした(配列単位の _require_thawed)")
        return self._uf.at(a, *args, **kw)

    def __call__(self, *a, **kw):
        return self._uf(*a, **kw)

    def __getattr__(self, name):
        return getattr(self._uf, name)


class _NpProxy:
    def __getattr__(self, name):
        v = getattr(np, name)
        return _UfuncAtGuard(v) if isinstance(v, np.ufunc) else v


R.np = _NpProxy()

sys.monitoring.use_tool_id(TOOL, "guard-poc")
sys.monitoring.register_callback(TOOL, sys.monitoring.events.LINE, on_line)
sys.monitoring.set_local_events(TOOL, code, sys.monitoring.events.LINE)
out = {"config": cfg, "n_agents": n, "sim_days": days, "drop": drop}
try:
    r = cli.run(n_agents=n, seed=1, sim_days=days, ticks=1440, **CONFIGS[cfg])
    out.update({"ok": True, "final": r.final_hash[:16], "calls": int(r.llm_calls)})
except ValueError as e:
    tb = traceback.extract_tb(e.__traceback__)
    out.update({"ok": False, "error": str(e)[:120], "system": st["cur"],
                "where": [f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in tb[-4:]]})
out["toggles"] = st["n_toggle"]
out["ufunc_at_checked"] = st["n_at_checked"]
print(json.dumps(out, ensure_ascii=False))
