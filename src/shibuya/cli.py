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

世帯の初期財布(2026-09-09・C5-a 仕上げ)
    ``agents.schedule.synthesize`` の 2,000〜10,001 円は **mock 専用**(合成日課の一部)。
    W16 母集団を載せたランでは、種別ごとの日消費アンカーから引いた
    ``economy.anchors.initial_wallets``(対数正規・中央値=日消費×3 日)を使う。
    層契約(``agents`` は ``economy`` を import できない)を守るため、**両方を知っている
    層外の本モジュール**が母集団の ``kind`` を読んで金額を作り、``Ledger.endow_households``
    の入口で差し替える(注入は従来どおり外界 → 世帯の transfer = ex nihilo 禁止)。
    ``--no-population``(または母集団資産が無い世界)では mock の値のまま。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Final

import numpy as np

from shibuya.agents import population as POP
from shibuya.agents.state import WakeCondition
from shibuya.core.rng import stream
from shibuya.economy import GoodsLedger, Ledger
from shibuya.economy import anchors as AN
from shibuya.economy import census as CS
from shibuya.economy import entry_capital as EC
from shibuya.economy.accounts import BalanceLine, Sector
from shibuya.engine import resolve as R
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import (
    MINUTES_PER_SIM_DAY,
    RunResult,
    add_fleet_args,
    fleet_from_args,
    run_day,
)
from shibuya.world.assets import hash_free_cat_code
from shibuya.world.state import World

__all__ = [
    "STORE_ENTRY_CAPITAL_YEN",
    "WALLET_DOMAIN",
    "parse_refractory_scale",
    "store_capital_array",
    "store_capital_report",
    "household_wallets",
    "build_ledger_bundle",
    "run",
    "main",
]

#: 一律指定(``--store-capital``)を値なしで使ったときの既定[円/店]。C4 の expedient。
#: **既定の経路ではもう使わない**(D-13 で経済センサス按分に置換)。
STORE_ENTRY_CAPITAL_YEN: Final[int] = 200_000

#: 初期財布の乱数ドメイン(``core.rng`` の Philox・manifest のドメイン表に載る)。
WALLET_DOMAIN: Final[str] = "wallet.initial"


def parse_refractory_scale(items: "list[str] | tuple[str, ...] | None") -> dict[str, float]:
    """``--refractory-scale COND=FACTOR`` の並び → ``{条件名: 倍率}``(ablation ③)。

    条件名は ``agents.state.WakeCondition`` の 11 行(大小文字・``-``/``_`` は吸収)。
    同じ条件を 2 回書いたら**後が勝つ**。空の並びは空 dict(=§6 の表そのもの)。

    Example:
        >>> parse_refractory_scale(["PROXIMITY_SWAP=0.5"])
        {'PROXIMITY_SWAP': 0.5}

    Raises:
        argparse.ArgumentTypeError: ``=`` が無い・倍率が数でない・未知の条件名。
    """
    out: dict[str, float] = {}
    for raw in items or ():
        text = str(raw)
        if "=" not in text:
            raise argparse.ArgumentTypeError(
                f"--refractory-scale は COND=FACTOR の形(いま {text!r})"
            )
        key, _, val = text.partition("=")
        try:
            factor = float(val)
        except ValueError:
            raise argparse.ArgumentTypeError(f"倍率が数でない: {text!r}") from None
        try:
            idx = R.wake_condition_index(key)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(str(exc)) from None
        out[WakeCondition(idx).name] = factor
    return out


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


def household_wallets(
    world: World,
    n_agents: int,
    seed: int | str = 1,
    world_dir: str | Path | None = None,
    *, use_population: bool = True,
) -> np.ndarray | None:
    """W16 母集団の種別から初期財布[円]を引く(母集団が使えないランは ``None``)。

    ``engine.run._resolve_population`` と**同じ規約**で母集団を解決する(同じ
    ``world_dir``/``n_agents``/``seed`` なら同じ行が同じ順で返る)。世界のセル数と
    合わない母集団は engine 側が黙って見送るので、ここでも見送る。

    Returns:
        長さ ``min(n_agents, 母集団の体数)`` の int64 配列。``None``=母集団なし。
    """
    if not use_population or world_dir is None:
        return None
    try:
        pop = POP.load_population(world_dir, n=None, seed=seed)
    except (OSError, ValueError):
        return None
    if pop is None:
        return None
    for arr in (pop.home_cell, pop.work_cell, pop.school_cell):
        if arr.size and int(arr.max()) >= int(world.n_cells):
            return None  # 合成小世界に実データの母集団は載せない(engine と同じ判断)
    if pop.n > int(n_agents):
        pop = POP.sample_population(pop, int(n_agents), seed)
    kinds = np.asarray(pop.kind, dtype=np.int64)[: int(n_agents)]
    return AN.initial_wallets(kinds.size, kinds, stream(seed, WALLET_DOMAIN))


class _HouseholdWalletLedger(Ledger):
    """``endow_households`` の金額だけ差し替える ``Ledger``(層外の組立コード)。

    ``engine.resolve.initialize`` は ``schedule.initial_money``(mock の一様乱数)を
    ``endow_households`` に渡す。engine は economy を import できず、agents は
    アンカーを知らないので、**注入の入口で**アンカー由来の金額へ置き換える。
    経路(外界 → 世帯・科目 CARRY_IN)は変えない = ex nihilo 禁止・保存則は不変。
    """

    def __init__(self, n_households: int, n_stores: int, wallets: np.ndarray) -> None:
        super().__init__(n_households, n_stores)
        self.wallets = np.asarray(wallets, dtype=np.int64).ravel()

    def endow_households(self, amounts: np.ndarray, tick: int = 0) -> np.ndarray:
        a = np.asarray(amounts, dtype=np.int64).ravel().copy()
        m = min(a.size, self.wallets.size)
        a[:m] = self.wallets[:m]  # 母集団を超える行(縮小ラン)は mock のまま
        return super().endow_households(a, tick)


def build_ledger_bundle(
    world: World,
    n_agents: int,
    store_capital_yen: int | None = None,
    *,
    seed: int | str = 1,
    world_dir: str | Path | None = None,
    use_population: bool = True,
) -> LedgerBundle:
    """世界から金/物の台帳とセンサス呼び出しを組み立てる(engine/ledger_api の Protocol を満たす)。

    ``world_dir`` に W16 母集団があれば、世帯の初期財布を ``economy.anchors`` の
    アンカー由来に差し替える(``use_population=False`` で mock のまま)。

    両台帳の O(t) ログ(取引・納品)のリングバッファ容量は **N 比例**(D-53)。金の台帳は
    世帯数から自分で決められるが、物の台帳は POI 側の器なので ``n_agents`` を渡して決める。
    """
    wallets = household_wallets(
        world, n_agents, seed, world_dir, use_population=use_population
    )
    led = (
        Ledger(n_agents, world.n_poi)
        if wallets is None
        else _HouseholdWalletLedger(n_agents, world.n_poi, wallets)
    )
    cats = np.array([hash_free_cat_code(c) for c in world.assets.poi_cat], dtype=np.int64)
    goods = GoodsLedger.from_pois(
        cats, np.asarray(world.pois.stock), np.asarray(world.pois.price), n_agents=n_agents
    )
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
    use_population: bool = True,
    **kwargs,
) -> RunResult:
    """台帳つきの 1 シミュ日ラン(C4 の標準入口)。

    ``use_population=False`` は下限対照(``engine.run --no-population`` と同じ意味):
    W16 母集団を読まず合成個体で回し、世帯の初期財布も mock のままにする。
    """
    wd = Path(world_dir) if world_dir is not None else None
    world = World.load_or_synthetic(wd, n_cells=n_cells, seed=seed) if wd is not None else World.synthetic(
        n_cells=n_cells, seed=seed
    )
    run_world_dir = wd if (wd is not None and wd.exists()) else None
    bundle = build_ledger_bundle(
        world, n_agents, store_capital_yen,
        seed=seed, world_dir=run_world_dir, use_population=use_population,
    )
    return run_day(
        n_agents=n_agents,
        seed=seed,
        world=world,
        ticks=ticks,
        checkpoint_every=checkpoint_every,
        world_dir=run_world_dir,
        ledger=bundle,
        population=None if use_population else False,
        **kwargs,
    )


def checkpoints_payload(res: RunResult, *, run_id: str = "") -> dict[str, Any]:
    """T2(決定論)行の入力 = checkpoint 列を JSON にできる形で返す(**純関数**)。

    受入計器 ``tools/c7/c7_accept.py`` の ``normalize_checkpoints`` / ``selfconsistency``
    が読む形(``checkpoints[].{tick, combined, population_hash, schedule_hash}``)。
    ``final_hash`` は summary の「checkpoint N 点 最終 …」と同じ値(16 桁でなく全桁)。
    """
    return {
        "schema": "shibuya.cli/checkpoints/1",
        "run_id": run_id,
        "n_agents": int(res.n_agents),
        "seed": res.seed,
        "ticks": int(res.ticks),
        "final_hash": res.final_hash,
        "checkpoints": [
            {
                "tick": int(c.tick),
                "agents_hash": c.agents_hash,
                "world_hash": c.world_hash,
                "population_hash": c.population_hash,
                "schedule_hash": c.schedule_hash,
                "combined": c.combined,
            }
            for c in res.checkpoints
        ],
        "manifest": res.run_manifest_fields(),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="台帳(金/物)+世界過程つきの 1 シミュ日ラン(C4)")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--world", type=str, default="data/world/v2")
    ap.add_argument("--cells", type=int, default=139, help="合成世界のセル数")
    ap.add_argument("--ticks", type=int, default=MINUTES_PER_SIM_DAY)
    ap.add_argument("--occupancy-every", type=int, default=0, help="在圏 journal の記録間隔[tick](0=書かない・C7 受入計器の入力・毎正時なら 60)")
    ap.add_argument("--occupancy-out", type=str, default="", help="在圏 journal の出力 .npz")
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
    ap.add_argument(
        "--budget-mode",
        choices=("fixed", "ranking"),
        default="fixed",
        help="知覚のトークン配分(知覚契約書 §3.2 ablation ①)。fixed=チャネル固定枠(既定)/"
             "ranking=同一総トークンの単一ランキング",
    )
    ap.add_argument(
        "--pnotice-d50-scale",
        "--p-notice-d50-scale",
        dest="pnotice_d50_scale",
        type=float,
        default=1.0,
        metavar="FACTOR",
        help="p_notice の d50 を倍率で振る(知覚契約書 §8 第1陣 ② の腕。既定 1.0=40 m・"
             "0.5=20 m・2.0=80 m。2.0 は打ち切り 80 m と同値になる)",
    )
    ap.add_argument(
        "--refractory-scale",
        action="append",
        default=[],
        metavar="COND=FACTOR",
        help="§6 不応期表を条件ごとに倍率で振る(§8 第1陣 ③ の腕。繰り返し可。"
             "例 --refractory-scale PROXIMITY_SWAP=0.5。条件名は WakeCondition の 11 行)",
    )
    ap.add_argument(
        "--no-signage",
        action="store_true",
        help="看板・広告面(B2.signage)を全セルで空にする(§8 第1陣 ⑥「広告ゼロ」の腕)",
    )
    ap.add_argument(
        "--no-population",
        action="store_true",
        help="W16 母集団を使わず合成個体で回す(下限対照・世帯財布も mock のまま)",
    )
    ap.add_argument(
        "--checkpoints-out",
        type=str,
        default="",
        help="checkpoint 列(tick・agents/world/population/schedule ハッシュ・combined)と"
             " final_hash を JSON で書く(C7 受入 T2-a/b/c の入力。既定=書かない)",
    )
    ap.add_argument(
        "--replay",
        type=str,
        default="",
        help="録画テープのディレクトリを与えると mode=replay(テープ完全一致・LLM 呼なし)で回す"
             "(C7 T2-c: 本番テープの再生で checkpoint 列を復元する)",
    )
    # --llm / --endpoints / --model / --mode / --run-id / --tape / --temperature /
    # --max-tokens / --fleet-wait-s(C6-a)
    add_fleet_args(ap)
    args = ap.parse_args(argv)
    try:
        refractory_scale = parse_refractory_scale(args.refractory_scale)
        if float(args.pnotice_d50_scale) <= 0.0:
            raise argparse.ArgumentTypeError("--pnotice-d50-scale は正の値")
    except argparse.ArgumentTypeError as exc:  # 使い方の誤りは traceback ではなく usage で返す
        ap.error(str(exc))
    res = run(
        n_agents=args.agents,
        seed=args.seed,
        world_dir=args.world,
        n_cells=args.cells,
        ticks=args.ticks,
        checkpoint_every=args.checkpoint_every,
        store_capital_yen=args.store_capital,
        use_population=not args.no_population,
        processes_disabled=args.ablate or None,
        budget_mode=args.budget_mode,
        p_notice_d50_scale=float(args.pnotice_d50_scale),
        refractory_scale=refractory_scale or None,
        signage=not args.no_signage,
        fleet=fleet_from_args(args, ap),
        fleet_wait_s=float(getattr(args, "fleet_wait_s", 0.0)),
        fleet_debug_dir=getattr(args, "fleet_debug_dir", "") or None,
        occupancy_every=int(getattr(args, "occupancy_every", 0) or 0),
        occupancy_path=getattr(args, "occupancy_out", "") or None,
        tape_path=args.tape or None,
        **({"mode": "replay", "replay": args.replay} if args.replay else {}),
    )
    print(res.summary())
    if args.checkpoints_out:
        out = Path(args.checkpoints_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = checkpoints_payload(res, run_id=str(getattr(args, "run_id", "") or ""))
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
        print(f"  checkpoints JSON {out} ({len(payload['checkpoints'])} 点)")
    if res.fleet_fields:
        c = res.bridge_counters
        dec = res.fleet_fields.get("decoding", {}).get("T1", {})
        print(
            f"[艦隊] 呼 {int(c.get('fleet_calls', 0)):,} / 帳尻 {int(c.get('fleet_accounted', 0)):,}"
            f" ・繰り延べ {int(c.get('fleet_deferred_timeout', 0) + c.get('fleet_deferred_queue_full', 0)):,}"
            f"(再投入 {int(c.get('fleet_reinjected', 0)):,}・再送 {int(c.get('fleet_resent', 0)):,})"
            f" ・TTFT p50/p99 {c.get('fleet_ttft_p50', 0.0):.2f}/{c.get('fleet_ttft_p99', 0.0):.2f}s"
            f" ・e2e p50/p99 {c.get('fleet_e2e_p50', 0.0):.2f}/{c.get('fleet_e2e_p99', 0.0):.2f}s"
            f" ・temp {dec.get('temperature', 0.0)} max_tok {dec.get('max_tokens', 0)}"
            f" ・cache_salt {res.fleet_fields.get('cache_salt', '')[:16]}…"
            f"({res.fleet_fields.get('mode', '')})"
        )
        print(
            f"[艦隊書式] エラー率 実効 {res.parse_error_rate:.3f} / 厳密 "
            f"{res.parse_error_rate_strict:.3f} (受入 ≤0.10) ・別名 "
            f"{res.label_alias_rate:.3f}({int(c.get('fleet_label_alias_used', 0)):,} 呼)"
            f" ・位置読み {res.positional_rate:.3f}"
            f"({int(c.get('fleet_positional_used', 0)):,} 呼)"
            f" ・辞書写像 {res.dictionary_mapped_rate:.3f}"
            f"({int(c.get('fleet_dictionary_mapped', 0)):,} 呼)"
            f" ・温度0再生成 {int(c.get('fleet_format_retry', 0)):,}"
            f"(成功 {int(c.get('fleet_format_retry_ok', 0)):,})"
            f" ・未定義 {int(c.get('unknown_action', 0)):,}"
        )
        if c.get("fleet_debug_rows", 0):
            print(
                f"[艦隊書式デバッグ] {int(c['fleet_debug_rows']):,} 行"
                f"(上限超過で未記録 {int(c.get('fleet_debug_skipped', 0)):,}) → "
                f"{args.fleet_debug_dir}/format_debug.jsonl"
            )
    led = getattr(res, "ledger", None)
    money = getattr(led, "money", None) if led is not None else None
    if money is not None:
        store, m, share = EC.ledger_entry_capital_share(money)
        cash = money.sector_totals(BalanceLine.CASH)
        dep = money.sector_totals(BalanceLine.DEPOSIT)
        hh = int(cash[int(Sector.HOUSEHOLD)] + dep[int(Sector.HOUSEHOLD)])
        print(
            f"[参入資本] 店舗の現金+預金 {store:,} 円 / 世帯の現金+預金 {hh:,} 円 /"
            f" 貨幣供給 {m:,} 円 = 店舗 {share * 100:.2f}%"
            f" ({'一律 ' + format(args.store_capital, ',') + ' 円/店' if args.store_capital is not None else '経済センサス按分'})"
        )
        src = "mock 一様" if isinstance(money, Ledger) and not isinstance(
            money, _HouseholdWalletLedger
        ) else "anchors 対数正規"
        print(
            f"[世帯財布] 世帯の現金+預金 {hh:,} 円 / 貨幣供給 {m:,} 円 = "
            f"{(hh / m * 100) if m else 0.0:.2f}% ({src}・"
            f"{'母集団あり' if not args.no_population else '--no-population'})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
