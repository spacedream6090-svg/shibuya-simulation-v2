# -*- coding: utf-8 -*-
"""手順 0(第347 止めた切替口の削除): 経済の段階 2 の「off」(切替口)・「on・部品 none」・「段階 2 の外の束」(試験の中だけの束=
``tests/economy/_stage2_outside.py``)を同じ設定で回し、書き直す試験が見る値を JSON に書く(1 回 1 構成 1 腕)。

使い方(リポの根で・``PYTHONPATH`` に ``src`` とリポの根): python step0_parts_none.py <構成> <腕 off|none|noattach> <出力 JSON>
構成: e4_wired・e4_t2・e1_world200・e11_small2d・e13_world300_2d。切替口 off が在る木(②a の前)でだけ回る。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np


def _sha(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(np.asarray(a)).tobytes()).hexdigest()[:16]


NOATTACH = False


def _arm(variant: str) -> None:
    global NOATTACH
    from shibuya.economy import stage2_bind as ES2

    if variant == "off":
        ES2.set_arm("off")
    elif variant == "noattach":  # 腕は既定 on のまま・台帳を「段階 2 の口を持たない」形にする(試験の中だけの束の確かめ)
        ES2.set_arm("on")
        NOATTACH = True
        import pytest

        from tests.economy import _stage2_outside as SO

        SO.use_outside_bundle(pytest.MonkeyPatch())
    else:
        ES2.set_arm("on")
        ES2.set_parts("none")


def _wired_bundle(world, n):
    from shibuya.economy import census as CS
    from shibuya.economy.goods import GoodsLedger
    from shibuya.economy.ledger import Ledger
    from shibuya.foundation.ports.ledger import LedgerBundle

    if NOATTACH:
        from tests.economy import _stage2_outside as SO

        led = SO.outside(Ledger)(n, world.n_poi)
    else:
        led = Ledger(n, world.n_poi)
    goods = GoodsLedger.from_pois(np.arange(world.n_poi) % 3, np.asarray(world.pois.stock), np.asarray(world.pois.price))
    return LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))


def run(cfg: str):
    from shibuya.engine.run import run_day
    from shibuya.world.model.state import World

    if cfg == "e4_wired":
        world = World.synthetic(n_cells=64, seed=2)
        b = _wired_bundle(world, 500)
        return run_day(n_agents=500, seed=2, world=world, ticks=1_440, checkpoint_every=360, ledger=b), b
    if cfg == "e4_t2":
        goods_ids = ("shelf_stock_restock", "delivery_inbound", "waste_collection", "street_cleaning")
        world = World.synthetic(n_cells=64, seed=2)
        b = _wired_bundle(world, 500)
        return run_day(n_agents=500, seed=2, world=world, ledger=b, ticks=1_440, checkpoint_every=360,
                       processes_disabled=goods_ids), b
    if cfg == "e1_world200":
        from shibuya import cli
        from shibuya.world.laws import switch_rate as RR

        RR.set_arm(RR.MODE_LEGACY)
        res = cli.run(n_agents=200, seed=1, world_dir="data/world/v2", vocab_version="v3")
        return res, res.ledger
    if cfg == "e11_small2d":
        from shibuya.economy import stage2_bind as ES2
        from tests.economy.stage2 import test_stage2_runs as TR

        ES2.set_atm_table(TR._atm_everywhere(World.synthetic(n_cells=64, seed=2).n_cells))
        if NOATTACH:
            from tests.economy import _stage2_outside as SO

            TR._SmallWallets = SO.outside(TR._SmallWallets)
        res, led = TR._run(sim_days=2)
        return res, res.ledger
    if cfg == "e13_world300_2d":
        from shibuya import cli

        res = cli.run(n_agents=300, seed=1, world_dir="data/world/v2", sim_days=2, vocab_version="v3",
                      start_sim_datetime="2026-08-24")
        return res, res.ledger
    raise SystemExit(f"構成の名 {cfg}")


def dump(res, bundle) -> dict:
    from shibuya.economy import checks as CK
    from shibuya.economy.accounts import BalanceLine, Sector
    from tests import golden_env as GE

    led = bundle.money
    goods = bundle.goods
    out = {
        "final": res.final_hash, "calls": int(res.llm_calls),
        "cp": [(int(c.tick), c.combined, c.behavior_hash) for c in res.checkpoints],
        "cp_soa": [GE.soa_combined(c) for c in res.checkpoints],
        "cp_full": [c.full_hash for c in res.checkpoints],
        "money_end": int(res.money_end), "revenue_end": int(res.revenue_end), "conserved": bool(res.conserved),
        "money_stage2_in": int(getattr(res, "money_stage2_in", 0) or 0),
        "purchases": int(res.column("purchases").sum()),
        "census_pass": bool(res.census_pass),
        "census_row": {k: (v if isinstance(v, (int, float, bool, str)) or v is None else str(v))
                       for k, v in dict(res.census_row or {}).items()},
        "stage2_attached": getattr(led, "stage2", None) is not None,
        "sizes": [int(x) for x in led.sizes],
        "n_transfers": int(led.n_transfers),
        "meter_rows": int(led.meter.rows), "meter_events": int(led.meter.events),
        "meter_uncaused": int(led.meter.uncaused), "overflow": int(led.meter.overflow),
        "n_raw_dropped": int(led.n_raw_dropped),
        "raw_rows_sha": _sha(led.raw_rows()), "raw_event_ids_sha": [_sha(x) for x in led.raw_event_ids()],
        "raw_methods_nonzero": int((np.asarray(led.raw_methods()) != 0).sum()),
        "flow_daily_sha": [_sha(f) for f in led.flow_daily], "flow_now_sha": _sha(led.flow),
        "cash_by_sector": [int(x) for x in np.asarray(led.sector_totals(BalanceLine.CASH))],
        "deposit_h_sum": int(np.asarray(led.balance(BalanceLine.DEPOSIT, Sector.HOUSEHOLD)).sum()),
        "hh_cash_is_agents_money": led.balance(BalanceLine.CASH, Sector.HOUSEHOLD) is res.agents.registry.money,
        "check2_ok": bool(CK.net_worth_equals_real_assets(led, goods).ok),
        "goods_stock_sha": _sha(goods.aggregate_stock()), "goods_delivery_sha": _sha(goods.delivery_rows()),
        "goods_delivery_event_ids_sha": [_sha(x) for x in goods.delivery_event_ids()],
        "sku_balanced": bool(goods.sku_balanced()),
        "conserved_daily": [], "faucet_sink_day0": None,
    }
    m = res.run_manifest_fields()
    out["daily_economy"] = [{k: d["economy"].get(k) for k in ("rows", "amount", "overflow", "event_rows", "flow_sum_ok")}
                            for d in m["daily"]]
    out["conserved_daily"] = [(d["economy"].get("conservation") or {}).get("ok") for d in m["daily"]]
    out["by_what"] = [d.get("events", {}).get("by_what") for d in m["daily"]]
    out["manifest_economy_keys"] = sorted(m["economy"])
    close = led.close_for(0)
    if close is not None:
        fs = CK.faucet_sink_totals(led, close.flow)
        out["faucet_sink_day0"] = {k: {str(a): int(b) for a, b in v.items()} for k, v in fs.items()}
    return out


if __name__ == "__main__":
    cfg, variant, path = sys.argv[1], sys.argv[2], sys.argv[3]
    _arm(variant)
    res, bundle = run(cfg)
    Path(path).write_text(json.dumps(dump(res, bundle), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("書いた", path)
