"""1-0: 書きの検査(段 A)の正と負の対照を本実装で回す(試作 ``guard_poc.py`` の置き換え)。世界資産・1,000 体・seed 1。

- 正: 検査を入れた(既定)ランが最後まで通り、final と呼数が HEAD の値(``probe_run.py --head`` の記録)と同じ。
- 負: ``engine.systems.overrides.drop_soa(系, 列)`` で、ある系の書く列(閉包)から 1 列を外して回し、その系が書いた行で
  ``ValueError`` が出ること(ufunc.at の列は resolve の配列ごとの検査・台帳の現金は台帳の旗の検査・ほかは numpy)。
- ``--timing``: 検査を入れたランと外したラン(``SHIBUYA_WRITE_GUARD=off`` と同じ ``set_enabled(False)``)の壁時計。

使い方(リポの根で): ``python $D/guard_runs.py <構成> <体数> <日数> [<系:列>] [--off]``(1 行の JSON を出す)。
"""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from probe_run import CONFIGS  # noqa: E402


def main(argv: list[str]) -> int:
    from shibuya import cli
    from shibuya.core import write_permit as WP
    from shibuya.engine.systems import overrides as OV

    off = "--off" in argv
    argv = [a for a in argv if a != "--off"]
    cfg, n, days = argv[0], int(argv[1]), int(argv[2])
    drop = argv[3] if len(argv) > 3 else ""
    WP.set_enabled(not off)
    out = {"config": cfg, "n_agents": n, "sim_days": days, "drop": drop, "guard": not off}
    t0 = time.perf_counter()
    try:
        kw = dict(n_agents=n, seed=1, sim_days=days, ticks=1440, **CONFIGS[cfg])
        if drop:
            s_, c_ = drop.split(":", 1)
            with OV.drop_soa(s_, c_):
                r = cli.run(**kw)
        else:
            r = cli.run(**kw)
        out.update({"ok": True, "final": r.final_hash[:16], "calls": int(r.llm_calls)})
    except ValueError as e:
        tb = traceback.extract_tb(e.__traceback__)
        system, t_ = None, e.__traceback__
        while t_ is not None:  # 落ちた系=進行役の run_system の局所 spec
            if t_.tb_frame.f_code.co_name == "run_system":
                system = t_.tb_frame.f_locals["spec"].name
            t_ = t_.tb_next
        out.update({"ok": False, "error": str(e)[:100], "system": system,
                    "where": [f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in tb[-4:]]})
    out["wall_s"] = round(time.perf_counter() - t0, 1)
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
