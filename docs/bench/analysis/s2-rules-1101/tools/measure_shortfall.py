"""段 2 の 5(11-01 §5)の計器: 既定の 2 日のラン(世界資産・開始日 2026-08-24=1 日目の締めが給料日)の最低賃金の違反の記録の器と、
金の流れと状態の印(1 バイト不変の確かめ)を JSON で標準出力へ。

使い方(読むだけ・何も書かない。出力は呼び手がファイルへ):
``PYTHONPATH=<src> python docs/bench/analysis/s2-rules-1101/tools/measure_shortfall.py [体数] [日数] [--no-bridge]``
(日数の既定 2。3 日なら給料日の締め(2 日目の終わり=1 日目の締め)の後の日が入り、``final_hash`` も賃金を見分ける。
``--no-bridge``=最低賃金の 3 版の ``params.bridge`` を消した表をメモリの中で使う=対照(ファイルは書き換えない))
``<src>`` を変えの前(土台の写し)と後で回し、``money`` と ``state`` の欄が同じことを比べる(``rules_version`` と
``shortfall`` は変わってよい=規則の表の中身と新しい器)。
"""

from __future__ import annotations

import hashlib
import json
import sys

import numpy as np


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n = int(args[0]) if args else 5_000
    days = int(args[1]) if len(args) > 1 else 2
    from shibuya import cli
    from shibuya.engine import economy_stage2 as ES2
    from shibuya.engine.rules import table as RT

    if "--no-bridge" in sys.argv[1:]:
        rows = []
        for r in RT.default_rules():
            d = r.as_dict()
            if r.id == "minimum_wage.tokyo":
                d["params"].pop("bridge", None)
            rows.append(RT.Rule.from_dict(d))
        stripped = RT.Rules(rows, sha="no-bridge")
        RT.default_rules = lambda: stripped  # メモリの中だけ(ファイルは書き換えない)

    assert ES2.arm() == ES2.ARM_ON, "経済の段階 2 の腕が既定(on)でない"
    res = cli.run(seed=1, world_dir="data/world/v2", sim_days=days, vocab_version="v3", start_sim_datetime="2026-08-24",
                  n_agents=n)
    man = res.run_manifest_fields()
    money = res.ledger.money
    st2 = money.stage2
    s2 = man["economy"]["stage2"]
    flows = [np.asarray(f).tolist() for f in money.flow_daily]
    out = {
        "n_agents": n,
        "sim_days": days,
        "rules_version": man.get("rules_version"),
        "state": {"final_hash": res.final_hash, "state_hashes": man.get("state_hashes"),
                  "state_hashes_end_of_day": man.get("state_hashes_end_of_day"),
                  "daily_end_of_day": [d.get("state_hashes_end_of_day") for d in man["daily"]]},
        "money": {
            "flow_daily_sha": _sha(flows),
            "conservation": [d["economy"]["conservation"] for d in man["daily"]],
            "wages_run_sha": _sha(st2.s2_meter["run"]["wages"]),
            "wages_run": {k: st2.s2_meter["run"]["wages"][k] for k in ("paydays", "paid", "amount", "funding")},
            "wage_model_floor": s2["rules"].get("wage_model", {}).get("floor"),
            "floor_at_start": s2["rules"].get("wage_build", {}).get("floor_at_start"),
        },
        "shortfall": s2["rules"].get("minimum_wage_shortfall"),
    }
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
