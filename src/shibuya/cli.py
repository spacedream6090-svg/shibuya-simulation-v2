"""shibuya.cli — 実行入口(層外の組立コード・C4 出口で追加)。

engine は economy を import できない(層契約: economy > engine)。世界・台帳(金/物)・センサスを
束ねて ``engine.run.run_day`` を呼ぶ組立は、層のどこにも置けないので本モジュール(パッケージ直下・
層契約の対象外)に置く。``python -m shibuya.engine.run`` は台帳なし(C2 の mock)のまま残す。

使い方::

    python -m shibuya.cli --agents 5000 --seed 1 --world data/world/v2

参入資本(D-13・2026-09-09 で置換)
    既定は ``economy.entry_capital.store_entry_capital``= 経済センサス2021 の産業大分類別
    「1 事業所当たり売上」→日商→運転資金 k 日分ぶんの**按分**。C4 の一律 200,000 円/店は
    ``--store-capital <円>`` を明示したときだけ使う(``STORE_ENTRY_CAPITAL_YEN`` はその既定値)。
    注入は従来どおり ``Ledger.endow_stores``(外界 → 店舗・参入資本科目)=ex nihilo 禁止。
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

import numpy as np

from shibuya.economy import GoodsLedger, Ledger
from shibuya.economy import census as CS
from shibuya.economy import entry_capital as EC
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import MINUTES_PER_SIM_DAY, RunResult, run_day
from shibuya.world.assets import hash_free_cat_code
from shibuya.world.state import World

__all__ = [
    "STORE_ENTRY_CAPITAL_YEN",
    "store_capital_array",
    "store_capital_report",
    "build_ledger_bundle",
    "run",
    "main",
]

#: 一律指定(``--store-capital``)を値なしで使ったときの既定[円/店]。C4 の expedient。
#: **既定の経路ではもう使わない**(D-13 で経済センサス按分に置換)。
STORE_ENTRY_CAPITAL_YEN: Final[int] = 200_000


def store_capital_array(
    world: World, n_agents: int, store_capital_yen: int | None = None
) -> np.ndarray:
    """店舗ごとの参入資本[円]の配列(``(n_poi,)`` int64)。

    ``store_capital_yen`` が ``None``(既定)なら経済センサス按分、整数ならその値で一律。
    """
    if store_capital_yen is None:
        return EC.store_entry_capital(world.assets.poi_cat, n_agents=n_agents)
    return np.full(world.n_poi, int(store_capital_yen), dtype=np.int64)


def store_capital_report(
    world: World,
    n_agents: int,
    store_capital_yen: int | None = None,
    *,
    household_cash_yen: int | None = None,
) -> EC.EntryCapitalReport:
    """参入資本の検算行(合計・大分類別・貨幣供給比)。ランを回さずに作れる。"""
    cap = store_capital_array(world, n_agents, store_capital_yen)
    return EC.entry_capital_report(
        cap,
        world.assets.poi_cat,
        scale=1.0 if store_capital_yen is not None else EC.population_scale(n_agents),
        cost_basis=store_capital_yen is None,
        household_cash_yen=household_cash_yen,
    )


def build_ledger_bundle(
    world: World, n_agents: int, store_capital_yen: int | None = None
) -> LedgerBundle:
    """世界から金/物の台帳とセンサス呼び出しを組み立てる(engine/ledger_api の Protocol を満たす)。"""
    led = Ledger(n_agents, world.n_poi)
    cats = np.array([hash_free_cat_code(c) for c in world.assets.poi_cat], dtype=np.int64)
    goods = GoodsLedger.from_pois(cats, np.asarray(world.pois.stock), np.asarray(world.pois.price))
    capital = store_capital_array(world, n_agents, store_capital_yen)
    if capital.size and int(capital.sum()) > 0:
        led.endow_stores(capital, tick=0)
    return LedgerBundle(money=led, goods=goods, census=lambda d: CS.daily_census(led, goods, day=d))


def run(
    n_agents: int = 5_000,
    seed: int = 1,
    world_dir: str | Path | None = "data/world/v2",
    n_cells: int = 139,
    ticks: int = MINUTES_PER_SIM_DAY,
    checkpoint_every: int = 360,
    store_capital_yen: int | None = None,
    **kwargs,
) -> RunResult:
    """台帳つきの 1 シミュ日ラン(C4 の標準入口)。"""
    wd = Path(world_dir) if world_dir is not None else None
    world = World.load_or_synthetic(wd, n_cells=n_cells, seed=seed) if wd is not None else World.synthetic(
        n_cells=n_cells, seed=seed
    )
    bundle = build_ledger_bundle(world, n_agents, store_capital_yen)
    return run_day(
        n_agents=n_agents,
        seed=seed,
        world=world,
        ticks=ticks,
        checkpoint_every=checkpoint_every,
        world_dir=wd if (wd is not None and wd.exists()) else None,
        ledger=bundle,
        **kwargs,
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="台帳(金/物)+世界過程つきの 1 シミュ日ラン(C4)")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--world", type=str, default="data/world/v2")
    ap.add_argument("--cells", type=int, default=139, help="合成世界のセル数")
    ap.add_argument("--ticks", type=int, default=MINUTES_PER_SIM_DAY)
    ap.add_argument("--checkpoint-every", type=int, default=360)
    ap.add_argument(
        "--store-capital",
        type=int,
        nargs="?",
        const=STORE_ENTRY_CAPITAL_YEN,
        default=None,
        help="店舗の参入資本を一律[円/店]で上書き(既定=経済センサス按分・D-13)",
    )
    ap.add_argument("--ablate", action="append", default=[], help="無効化する過程 id / AB-* id")
    args = ap.parse_args(argv)
    res = run(
        n_agents=args.agents,
        seed=args.seed,
        world_dir=args.world,
        n_cells=args.cells,
        ticks=args.ticks,
        checkpoint_every=args.checkpoint_every,
        store_capital_yen=args.store_capital,
        processes_disabled=args.ablate or None,
    )
    print(res.summary())
    led = getattr(res, "ledger", None)
    money = getattr(led, "money", None) if led is not None else None
    if money is not None:
        store, m, share = EC.ledger_entry_capital_share(money)
        print(
            f"[参入資本] 店舗の現金+預金 {store:,} 円 / 貨幣供給 {m:,} 円 = {share * 100:.2f}%"
            f" ({'一律 ' + format(args.store_capital, ',') + ' 円/店' if args.store_capital is not None else '経済センサス按分'})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
