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
from typing import Any, Final, Mapping

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
from shibuya.engine.geometry import DEFAULT_GEOMETRY, GEOMETRY_MODES
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import (
    MINUTES_PER_SIM_DAY,
    RunResult,
    add_fleet_args,
    fleet_from_args,
    run_day,
)
from shibuya.perception.templates import (
    DEFAULT_INTENT_MODE,
    DEFAULT_VOCAB_VERSION,
    INTENT_MODES,
    VOCAB_VERSIONS,
)
from shibuya.world.assets import AREA_SOURCES, DEFAULT_AREA_SOURCE, hash_free_cat_code
from shibuya.world.state import World

__all__ = [
    "STORE_ENTRY_CAPITAL_YEN",
    "WALLET_DOMAIN",
    "parse_refractory_scale",
    "store_capital_array",
    "store_capital_report",
    "household_wallets",
    "build_ledger_bundle",
    "write_census_files",
    "DAILY_CENSUS_FILENAME",
    "MONTHLY_MER_FILENAME",
    "MONTHLY_MER_SECTORS_FILENAME",
    "UNDEFINED_PAYLOAD_SCHEMA",
    "undefined_registry_payload",
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
    return LedgerBundle(
        money=led,
        goods=goods,
        census=lambda d: CS.daily_census(led, goods, day=d),
        census_write=lambda d, out: write_census_files(led, goods, d, out),
        monthly_check=lambda d: CS.monthly_census_t3(led, d),
    )


#: ``--census-out`` が書く 3 ファイルの名(``economy.census`` の書き手は **Parquet** を出す)。
#: 3 つ目は月次 MER の**部門軸**(第204・D-76 (a))。固定表 ``monthly_mer.parquet`` は
#: 列も行順もバイトも変えない=部門軸は**別ファイル**に出す。
DAILY_CENSUS_FILENAME: Final[str] = "daily_census.parquet"
MONTHLY_MER_FILENAME: Final[str] = "monthly_mer.parquet"
MONTHLY_MER_SECTORS_FILENAME: Final[str] = "monthly_mer_sectors.parquet"


def write_census_files(ledger, goods, day: int, out_dir: str | Path) -> tuple[str, ...]:
    """日次センサス(§2.4 軽量)と月次 MER(EVE 型の固定表 + 部門軸)を ``out_dir`` へ書く。

    ``engine.run`` は ``census_out`` を渡されたときだけ ``LedgerBundle.write_census``
    経由でこれを呼ぶ(engine は economy を import できない=層契約の依存逆転)。

    ``day`` は**畳んだ日**を渡す。``daily_census`` が台帳の ``close_for(day)`` から
    締めを引くので、行は締めた日の実数になる(空虚な行にならない)。1 シミュ日のランでは
    月次 MER の集計窓も 1 日(``days=1``)=**当日ぶん**。

    Returns:
        書いたファイルのパス(日次・月次固定表・月次部門軸の順)。
    """
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    row = CS.daily_census(ledger, goods, day=int(day))
    p_daily = CS.write_daily_census([row], d / DAILY_CENSUS_FILENAME)
    mer = CS.monthly_mer(ledger, goods, month=0, days=1)
    p_mer = CS.write_monthly_mer(mer, d / MONTHLY_MER_FILENAME)
    p_sectors = CS.write_monthly_mer_sectors(mer, d / MONTHLY_MER_SECTORS_FILENAME)
    return (p_daily.as_posix(), p_mer.as_posix(), p_sectors.as_posix())


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


#: ``--undefined-out`` が書く JSON の形の名前(``tools/vocab/*`` が読む鍵)。
UNDEFINED_PAYLOAD_SCHEMA: Final[str] = "shibuya.vocab/undefined-registry/1"


def undefined_registry_payload(
    registry: Any,
    *,
    source: str = "",
    cells: "Mapping[tuple[int, int], str] | None" = None,
    n_samples: int = 3,
) -> dict[str, Any]:
    """未定義行動台帳(``llm.UndefinedActionRegistry``)→ 段2 起草バッチの入力 JSON(**純関数**)。

    D-71 の段2〜3 は**ラン後のオフライン**(語彙成長の設計 v0 §2)なので、ランは台帳を
    残すだけでよい。本関数はその「残し方」を 1 か所に決める(``tools/vocab/adjudicate.py``
    が読み、``tools/vocab/registry_from_tape.py`` がテープから同じ形を作る)。

    Args:
        registry: ``RunResult.undefined_registry``。``None``(台帳の無いラン)は空の記録で返す。
        source: 由来の印(``"run_day"`` / ``"tape"``)。
        cells: ``(agent_id, tick) → セルID``。台帳は**セルを持たない**(``observe`` が受け取る
            のは ``prompt_hash`` だけ)ので、セルを知っている経路だけが渡す。渡さなければ
            ``records[].cell`` は ``None``・``words[].distinct_cells`` は 0 になり、
            ``cell_source`` が ``"unavailable"`` になる(**推測で埋めない**)。
        n_samples: 語ごとに載せる標本の件数(既定 3)。

    Returns:
        版・記録リング・語ごとの集計・カウンタを持つ dict(``json.dumps`` 可能・相対パスのみ)。

    Note:
        ``records[].word`` と ``records[].raw`` は**同じ値**になる。段1 は
        ``UndefinedActionRecord(word=raw_word.strip())`` しか残さない(生の前後空白より前の
        形は台帳に無い)ため、欄は 2 つ持つが値は strip 済みの逐語ひとつ。
        ``records[].stage`` は常に 1(段1 のレコードだけが記録リングに入る)。

    逐次ループ宣言(P4): 記録リング長(``log_limit`` 既定 4,096)ぶんのループ 1 本。ラン後に
    1 回だけ呼ぶ(ランの毎 tick 経路には入らない)。
    """
    from shibuya.llm.undefined import synonym_table_version

    # 語彙版は**ランごと**の値(モジュール定数ではない)= 台帳が持つ版を正とする(第205・親修正)。
    _vv = str(getattr(registry, "vocab_version", DEFAULT_VOCAB_VERSION))
    versions: dict[str, Any] = {"vocabulary": _vv, "synonym_table": synonym_table_version(_vv)}

    cell_of = dict(cells or {})
    records: list[dict[str, Any]] = []
    counters: dict[str, int] = {}
    threshold = 10
    if registry is not None and hasattr(registry, "counters"):
        counters = {str(k): int(v) for k, v in registry.counters().items()}
        threshold = int(getattr(registry, "threshold_agents", 10))
        for rec in getattr(registry, "log", ()):  # 記録リング(deque・古い順)
            word = str(rec.raw_word)
            records.append(
                {
                    "word": word,
                    "raw": word,  # 段1 は strip 済みの逐語しか持たない(Note)
                    "agent_id": int(rec.agent_id),
                    "tick": int(rec.tick),
                    "cell": cell_of.get((int(rec.agent_id), int(rec.tick))),
                    "stage": 1,
                    "context_hash": str(rec.context_hash),
                }
            )

    words: dict[str, dict[str, Any]] = {}
    for row in records:
        w = words.setdefault(
            row["word"],
            {
                "n_rows": 0,
                "distinct_agents": 0,
                "distinct_cells": 0,
                "distinct_hours": 0,
                "first_tick": int(row["tick"]),
                "samples": [],
                "_agents": set(),
                "_cells": set(),
                "_hours": set(),
            },
        )
        w["n_rows"] += 1
        w["_agents"].add(int(row["agent_id"]))
        if row["cell"] is not None:
            w["_cells"].add(str(row["cell"]))
        w["_hours"].add(int(row["tick"]) // 60)
        w["first_tick"] = min(int(w["first_tick"]), int(row["tick"]))
        if len(w["samples"]) < int(n_samples):
            w["samples"].append(
                {"agent_id": row["agent_id"], "tick": row["tick"], "cell": row["cell"]}
            )
    for word, w in words.items():
        w["distinct_agents"] = len(w.pop("_agents"))
        w["distinct_cells"] = len(w.pop("_cells"))
        w["distinct_hours"] = len(w.pop("_hours"))
        if registry is not None and hasattr(registry, "counts"):
            # 記録リングが溢れた語は ``counts``(有界化の影響を受けない)が正
            w["n_rows"] = int(registry.counts.get(word, w["n_rows"]))
            w["distinct_agents"] = int(registry.distinct_agents(word))

    dropped = int(counters.get("undefined_dropped", 0))
    return {
        "schema": UNDEFINED_PAYLOAD_SCHEMA,
        "source": str(source),
        "versions": versions,
        "threshold_agents": threshold,
        "cell_source": "prompt_block" if cell_of else "unavailable",
        "counters": counters,
        "dropped": dropped,
        "summary": {
            "n_records_kept": len(records),
            "n_words": len(words),
            "ring_truncated": bool(dropped),
        },
        "records": records,
        "words": dict(sorted(words.items(), key=lambda kv: (-kv[1]["n_rows"], kv[0]))),
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
    ap.add_argument(
        "--census-out",
        type=str,
        default="",
        help="日次センサス/月次 MER の出力先ディレクトリ(境界・経済設計書 §2.4)。"
             f"空=書かない(既定・出力は 1 バイトも増えない)。渡すと {DAILY_CENSUS_FILENAME} と "
             f"{MONTHLY_MER_FILENAME} と {MONTHLY_MER_SECTORS_FILENAME}(部門軸・D-76 (a))"
             "(いずれも Parquet・zstd)を締めた日のぶんだけ書く",
    )
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
        "--intent-mode",
        choices=INTENT_MODES,
        default=DEFAULT_INTENT_MODE,
        help="行動の出させ方(AB7 自由意図の腕・docs/design/v2-open-intent-arm-spec.md §2)。"
             "vocab=24 語のホワイトリストを B0 で見せる(既定・現行のバイト)/"
             "open=語彙を見せず『いま自分がしたいこと』を 10 字以内の動詞句で書かせ、"
             "接地はエンジン側(行動契約書 §7 段0〜1)に任せる/"
             "hint=語彙を例として見せたうえで、当てはまる語が無いときだけ 10 字以内の"
             "自由文を許す(AB7b・vocab と open の中間)",
    )
    ap.add_argument(
        "--vocab-version",
        choices=VOCAB_VERSIONS,
        default=DEFAULT_VOCAB_VERSION,
        help="行動語彙の版(語彙成長 v0・docs/design/v2-vocab-growth-design.md §3 F)。"
             "v1=現行 24 語(既定・バイト不変)/"
             "v2=24 語 + 横断語「食事」(飲食店オブジェクトの affordance)。"
             "v2 では B0 の提示が 13 語になり、段0 辞書が v3(食べる/飲む→食事)になり、"
             "resolve に「食事」の分岐が増える",
    )
    ap.add_argument(
        "--no-sleep-suppression",
        action="store_true",
        help="D-56 就寝抑止を切る(就寝中の個体も内受容/セル変化で呼ぶ=D-56 前の挙動・帰無腕)",
    )
    ap.add_argument(
        "--no-plan-sleep",
        action="store_true",
        help="D-62「就寝は計画の実行」を切る(就寝境界も LLM に判断させ・tick 0 は全員"
             " SLEEPING=D-62 前の挙動・帰無腕)",
    )
    ap.add_argument(
        "--no-plan-executor",
        action="store_true",
        help="D-66 計画実行層(engine.presence)を切る(=rail の乱数 12%% + D-61 帰りの便 +"
             " D-62 の run.py 発火=現行挙動・帰無腕)",
    )
    ap.add_argument(
        "--exit-mode",
        choices=("immediate", "board_intent", "walk_to_platform"),
        default="immediate",
        help="退出の実行形(設計書 §10-3)。immediate のみ実装・他は予約(NotImplementedError)",
    )
    ap.add_argument(
        "--attendance-rate",
        type=float,
        default=1.0,
        metavar="RATE",
        help="出勤率(D-67 (b)・expedient E6。既定 1.0=全員来る)。通勤・通学の体のうち"
             " 1-RATE をその日「終日域外」にする(_mix64(agent_id) の決定論)",
    )
    ap.add_argument(
        "--derive-rule",
        choices=("v1", "v2", "v2.1"),
        default="v2",
        help="在圏ブロックの読み口(設計書 §2 追補 2026-09-12)。v2=域外居住者の自宅側の行"
             "(乗車前の「移動 駅」・帰りの乗車後の店)を在圏に読まない。v2.1=v2+乗車に隣接"
             "しない先頭/末尾の移動・支度をブロックから落とす(移動行=行程全体)。v1=原則のまま",
    )
    ap.add_argument(
        "--no-outside-suppression",
        action="store_true",
        help="D-66 域外抑止を切る(域外滞在・乗車中の体にも LLM を呼ぶ=D-66 前の挙動・帰無腕)",
    )
    ap.add_argument(
        "--geometry",
        choices=GEOMETRY_MODES,
        default=DEFAULT_GEOMETRY,
        help="位置幾何(C9 G1/G2・docs/design/v2-c9-geometry-agenda.md §4)。"
             "node=現行の 1 tick=1 ノード(既定・checkpoint はバイト不変)/"
             "edge=辺上の連続位置(edge_id・辺上距離・向き)+希望速度 Uniform(1.00,1.60) m/s"
             "+Kladek 式の密度減速。edge では密度段が人/m² の Fruin LOS 段になる",
    )
    ap.add_argument(
        "--area-source",
        choices=AREA_SOURCES,
        default=DEFAULT_AREA_SOURCE,
        help="歩行可能面積の出所(C9c-1・G8 (b)・docs/research/v2-c9-geometry-capacity-"
             "research.md §2-1)。legacy=W10 街路点数 × 6.25 m²・床 1,500 m²(既定・"
             "**checkpoint はバイト不変**・6.25 は 2.5 m 格子の目の面積=expedient)/"
             " plateau=c9c_walkable_area.parquet(PLATEAU tran 歩道部の面 + OSM 線 × 道路"
             "構造令の既定幅員で実測・tools/build_geo/walkable_area.py が作る)",
    )
    ap.add_argument(
        "--seat-area-eatery",
        type=float,
        default=None,
        metavar="M2",
        help="飲食(food/nightlife)の 1 人あたり床面積[m²]の感度腕(既定=現行 2.0 のまま)。"
             "法定: 消防法施行規則 1 条の 3(三)項ロ **3.0** / 建告1441 飲食室 0.7 人/m² **1.43**",
    )
    ap.add_argument(
        "--seat-area-retail",
        type=float,
        default=None,
        metavar="M2",
        help="物販その他の 1 人あたり床面積[m²]の感度腕(既定=現行 4.0 のまま)。"
             "法定: 消防法施行規則 1 条の 3(四)項ロ **4.0** / 建告1441 売場 0.5 人/m² **2.0**",
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
        "--undefined-out",
        type=str,
        default="",
        help="未定義行動台帳(行動契約書 §7 段1)を JSON で書く(D-71 段2 起草バッチ "
             "tools/vocab/adjudicate.py の入力)。空=書かない(既定・出力は 1 バイトも増えない)。"
             "**ランの中では裁定しない**(語彙成長の設計 v0 §2: ラン後オフライン)",
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
        if not (0.0 <= float(args.attendance_rate) <= 1.0):
            raise argparse.ArgumentTypeError("--attendance-rate は 0.0〜1.0")
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
        sleep_suppression=not args.no_sleep_suppression,
        plan_sleep=not args.no_plan_sleep,
        plan_executor=not args.no_plan_executor,
        exit_mode=str(args.exit_mode),
        attendance_rate=float(args.attendance_rate),
        derive_rule=str(args.derive_rule),
        outside_suppression=not args.no_outside_suppression,
        geometry=str(args.geometry),
        area_source=str(args.area_source),
        seat_area_eatery_m2=args.seat_area_eatery,
        seat_area_retail_m2=args.seat_area_retail,
        intent_mode=str(args.intent_mode),
        vocab_version=str(args.vocab_version),
        fleet=fleet_from_args(args, ap),
        fleet_wait_s=float(getattr(args, "fleet_wait_s", 0.0)),
        fleet_debug_dir=getattr(args, "fleet_debug_dir", "") or None,
        occupancy_every=int(getattr(args, "occupancy_every", 0) or 0),
        occupancy_path=getattr(args, "occupancy_out", "") or None,
        census_out=getattr(args, "census_out", "") or None,
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
    if args.undefined_out:
        out = Path(args.undefined_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = undefined_registry_payload(
            getattr(res, "undefined_registry", None), source="run_day"
        )
        out.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        # ファイル名だけを出す(記録に絶対パスを残さない=第175 の教訓)。
        print(
            f"  未定義台帳 JSON {out.name}"
            f"({payload['summary']['n_words']} 語 / {payload['summary']['n_records_kept']} 行)"
        )
    census_paths = tuple(getattr(res, "census_paths", ()) or ())
    if census_paths:
        # ファイル名だけを出す(記録に絶対パスを残さない=第175 の教訓)。
        names = " / ".join(sorted(Path(p).name for p in census_paths))
        print(f"  census {len(census_paths)} ファイル: {names}(day={res.day_closed})")
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
