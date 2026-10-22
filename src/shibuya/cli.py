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
import dataclasses
import json
import warnings
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
from shibuya.economy import ledger as LED
from shibuya.economy import stage2 as S2
from shibuya.economy.accounts import BalanceLine, Sector
from shibuya.engine import economy_stage2 as _ES2
from shibuya.engine import resolve as R
from shibuya.engine import run_kind as _RK
from shibuya.engine.arbiter import call_budget_per_tick
from shibuya.engine.geometry import DEFAULT_GEOMETRY, GEOMETRY_MODES
from shibuya.engine.space import nav1 as _NAV1
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.run import (
    MINUTES_PER_SIM_DAY,
    RunResult,
    add_calendar_args,
    add_fleet_args,
    calendar_kwargs_from_args,
    fleet_from_args,
    resolve_population_seed,
    run_day,
)
from shibuya.perception.renderer import SIGNAGE_P_SEE_DEFAULT
from shibuya.perception.templates import (
    DEFAULT_INTENT_MODE,
    DEFAULT_VOCAB_VERSION,
    INTENT_MODES,
    VOCAB_VERSIONS,
)
from shibuya.world.assets import AREA_SOURCES, DEFAULT_AREA_SOURCE, hash_free_cat_code
from shibuya.engine.chooser import CHOOSER_NAMES, DEFAULT_CHOOSER
from shibuya.engine.poi_target import MOVE_SEARCH_RADIUS_CELLS
from shibuya.engine.intent import INTENT_MAX_TICKS
from shibuya.engine.familiarity import FAMILIARITY_K, FAMILIARITY_MODES
from shibuya.engine.memory import MEMORY_MODES, MEMORY_N, RECALL_TAU
from shibuya.engine.store_memory import (
    DEFAULT_STORE_DECAY,
    STORE_DECAY_MODES,
    STORE_MEMORY_MODES,
    STORE_MEMORY_N,
)
from shibuya.engine.chooser import HABIT_P, RANK_TAU
from shibuya.engine.classical import (
    ACTIVITY_REGIONS,
    DEFAULT_ACTIVITY_REGION,
    DEFAULT_POLICY,
    POLICIES,
)
from shibuya.engine.energy import (
    DEFAULT_ENERGY_RATE,
    DEFAULT_HUNGER_MODEL,
    ENERGY_RATES,
    HUNGER_MODELS,
)
from shibuya.world.state import DEFAULT_EATERY_MODE, EATERY_MODES, World
from shibuya.core.time_consts import STEPS_PER_HOUR

#: **CLI の既定の語彙版**(二層の段 3・第277=``--vocab-version`` を渡さないランは v3)。
#: ライブラリの既定(``templates.DEFAULT_VOCAB_VERSION``/``run_day``/``cli.run``)は **v1 のまま**
#: =ライブラリ経由の退化検査・golden は v1 の値で通る(切替口)。v1 の既定 checkpoint を
#: CLI で再現するときは ``--vocab-version v1`` を明示する。
CLI_DEFAULT_VOCAB_VERSION: Final[str] = "v3"
#: **3 段目(D-99 (a′)・D-110・ユーザー決定 09-25)**: CLI と ``cli.run`` の呼数の既定=**無制限**
#: (``0``=1 tick の上限を体数に置く=AB8/AB6c の ``l4_unlimited`` と同じ経路)。L4(10 呼/体/日)は
#: 制御目標ではなく**監査線**(manifest ``llm_calls_per_agent_day``/``l4_exceeded``)。上限の
#: スイッチ(``--l4-scale 1``=旧挙動・0.5/2=倍率)と従来の配り方(``arbiter.call_budget_per_tick``・
#: ``POOL_CAP_TICKS``)は残す。
CLI_DEFAULT_L4_SCALE: Final[float] = 0.0
#: **5 段目 5a(D-118 K5 (a)・第291)**: CLI と ``cli.run`` の空腹のモデルの既定=**energy**
#: (体のエネルギー収支)。``run_day`` のライブラリ既定は ``v1`` のまま(語彙・L4 と同じ分け方)。
#: 旧 checkpoint は ``--hunger-model v1``(``cli.run(hunger_model="v1")``)で再現する(テストで固定)。
CLI_DEFAULT_HUNGER_MODEL: Final[str] = DEFAULT_HUNGER_MODEL

__all__ = [
    "CLI_DEFAULT_VOCAB_VERSION",
    "CLI_DEFAULT_L4_SCALE",
    "CLI_DEFAULT_HUNGER_MODEL",
    "fleet_queue_note",
    "apply_fleet_queue_default",
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
        pop = POP.sample_population(pop, int(n_agents), seed)  # 10e(E4): engine と同じ鍵
    kinds = np.asarray(pop.kind, dtype=np.int64)[: int(n_agents)]
    return AN.initial_wallets(kinds.size, kinds, stream(seed, WALLET_DOMAIN))


class _HouseholdWalletLedger(Ledger):
    """``endow_households`` の金額だけ差し替える ``Ledger``(層外の組立コード)。

    ``engine.resolve.initialize`` は ``schedule.initial_money``(mock の一様乱数)を
    ``endow_households`` に渡す。engine は economy を import できず、agents は
    アンカーを知らないので、**注入の入口で**アンカー由来の金額へ置き換える。
    経路(外界 → 世帯・科目 CARRY_IN)は変えない = ex nihilo 禁止・保存則は不変。
    """

    def __init__(self, n_households: int, n_stores: int, wallets: np.ndarray, n_employers: int = 1,
                 rows_per_agent_day: float | None = None) -> None:
        super().__init__(n_households, n_stores, n_employers, rows_per_agent_day=rows_per_agent_day)
        self.wallets = np.asarray(wallets, dtype=np.int64).ravel()

    def endow_households(self, amounts: np.ndarray, tick: int = 0, *, cause=None) -> np.ndarray:  # noqa: ANN001
        a = np.asarray(amounts, dtype=np.int64).ravel().copy()
        m = min(a.size, self.wallets.size)
        a[:m] = self.wallets[:m]  # 母集団を超える行(縮小ラン)は mock のまま
        return super().endow_households(a, tick, cause=cause)


def build_ledger_bundle(
    world: World,
    n_agents: int,
    store_capital_yen: int | None = None,
    *,
    seed: int | str = 1,
    world_dir: str | Path | None = None,
    use_population: bool = True,
    endow: bool = True,
) -> LedgerBundle:
    """世界から金/物の台帳とセンサス呼び出しを組み立てる(engine/ledger_api の Protocol を満たす)。

    ``endow=False``(10d の再開用)は店舗の参入資本を入れない(残高は再開で保存した状態から戻す=A11 の
    お金の自動補充をしない)。世帯の財布は ``engine.resolve.initialize`` が入れるので、再開ではそちらも走らない。

    ``world_dir`` に W16 母集団があれば、世帯の初期財布を ``economy.anchors`` の
    アンカー由来に差し替える(``use_population=False`` で mock のまま)。

    両台帳の O(t) ログ(取引・納品)のリングバッファ容量は **N 比例**(D-53)。金の台帳は
    世帯数から自分で決められるが、物の台帳は POI 側の器なので ``n_agents`` を渡して決める。
    """
    wallets = household_wallets(
        world, n_agents, seed, world_dir, use_population=use_population
    )
    # 第 2 期 2-1: 経済の段階 2 の腕(--economy-stage2 on)のランだけ、雇用主の口を W6 の組織の数にする(賃金=権利台帳の
    # 雇用の行の組織 → 世帯)。腕の無いランは今のまま 1 口(値は不変)。
    # 生ログの輪の係数も腕のランだけ段階 2 の値(K17 と同じ規則=実測の 1.5 倍以上・economy.stage2)。
    # 〔第 2 期 2-4 V4〕既定は on=既定のランは雇用主の口が W6 の組織の数・輪の係数 16.0 行/体/日(予算の宣言 §3)。
    # 切替口 off は 2-1 までのまま(1 口・6.5 行/体/日)。
    if _ES2.arm() == _ES2.ARM_ON:
        n_emp = LED.load_employers(world_dir).n if world_dir is not None else 1
        rate = S2.STAGE2_TRANSFERS_PER_AGENT_PER_DAY
        led = (
            Ledger(n_agents, world.n_poi, n_emp, rows_per_agent_day=rate)
            if wallets is None
            else _HouseholdWalletLedger(n_agents, world.n_poi, wallets, n_emp, rows_per_agent_day=rate)
        )
    else:  # 腕の無いラン=今の呼び方のまま(1-9 の試験が HEAD の台帳の写しを差し込む口も同じ)
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
    if endow and capital.size and int(capital.sum()) > 0:
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


def fleet_queue_note(fleet: Any, l4_scale: float, n_agents: int) -> str:
    """艦隊 × 無制限で受理待ち枠が未指定かつ体数より小さいなら注記の文(それ以外は ``""``・D-55)。

    無制限(``l4_scale=0``)では 1 tick の呼数の上限が体数になる。艦隊の受理待ち+実行中の枠
    (``FleetConfig.queue_capacity``・既定 ``max_in_flight×4``)がそれより小さいと、あふれた呼は
    繰り延べになる(C7 D-55/D-58)。**第289 Q28 以降、``cli.run`` はこの場合 ``apply_fleet_queue_default``
    で枠の既定を体数にする**ので、注記が要るのは枠を直せなかった(``config`` を持たない)艦隊だけ。
    """
    if fleet is None or float(l4_scale) != 0.0:
        return ""
    cfg = getattr(fleet, "config", None)
    if cfg is None or getattr(cfg, "queue_capacity", None) is not None:
        return ""
    cap = getattr(fleet, "queue_capacity", None)
    if cap is not None and int(cap) >= int(n_agents):
        return ""  # 既定の枠が体数以上=繰り延べは起きない
    return (
        "艦隊 × 呼数無制限(--l4-scale 0)で --fleet-queue-capacity が未指定: 受理待ち枠は既定 "
        f"{cap}(max_in_flight×4)。1 tick の呼数の上限は体数 {int(n_agents):,} なので、枠を超えた"
        "呼は繰り延べになる(D-55)。繰り延べ 0 には計画呼数以上の --fleet-queue-capacity を渡す"
    )


def apply_fleet_queue_default(fleet: Any, l4_scale: float, n_agents: int) -> int | None:
    """第289 Q28(D-55): 艦隊 × 呼数無制限 × 受理待ち枠 未指定 → 枠の既定を**体数**にする。

    無制限では 1 tick の呼数の上限が体数なので、枠 = 体数なら受理待ちあふれの繰り延べは 0 になる
    (C7 D-58 は計画呼数以上の ``--fleet-queue-capacity`` を手で渡していた)。既定の枠
    (``max_in_flight×4``)が既に体数以上なら**狭めない**(何もしない)。明示した枠・上限ありのラン・
    mock(艦隊なし)は変えない。枠を変えたら ``FleetConfig`` を差し替え(manifest の ``llm_fleet.queue_capacity``
    に載る)、クライアントの ``queue_capacity`` も揃える。返り値=設定した枠(変えなければ ``None``)。
    同期の経路(mock・``llm_bridge``)は触らない。
    """
    if fleet is None or float(l4_scale) != 0.0:
        return None
    cfg = getattr(fleet, "config", None)
    if cfg is None or getattr(cfg, "queue_capacity", None) is not None:
        return None
    cur = getattr(fleet, "queue_capacity", None)
    if cur is not None and int(cur) >= int(n_agents):
        return None
    cap = int(n_agents)
    try:
        fleet.config = dataclasses.replace(cfg, queue_capacity=cap)
        fleet.queue_capacity = cap
    except (AttributeError, TypeError):  # 設定を差し替えられない艦隊=従来どおり注記と警告
        return None
    return cap


def run(
    n_agents: int = 5_000,
    seed: int = 1,
    world_dir: str | Path | None = "data/world/v2",
    n_cells: int = 139,
    ticks: int = MINUTES_PER_SIM_DAY,
    checkpoint_every: int = 360,
    store_capital_yen: int | None = None,
    use_population: bool = True,
    l4_scale: float | None = None,
    population_seed: int | None = None,
    environment_seed: int | None = None,
    run_kind: str | None = None,
    experiment: Any = None,
    experiment_aa: bool = False,
    experiment_branch: Any = None,
    experiment_model: str | None = None,
    **kwargs,
) -> RunResult:
    """台帳つきの 1 シミュ日ラン(C4 の標準入口)。

    ``population_seed``(10f・K21 (a))は母集団の seed(省略=``seed`` と同じ=今と同じ)。合成世界・世帯の財布・
    ``run_day`` の母集団の側の乱数(``engine.run.POPULATION_RNG_DOMAINS``)に使う。``seed`` は動きの seed(salt)。
    ``environment_seed``(10f 第 2 段の直し・S1)は環境の seed(気象・大きな催し・道路工事。省略=``seed`` と同じ)。

    ``use_population=False`` は下限対照(``engine.run --no-population`` と同じ意味):
    W16 母集団を読まず合成個体で回し、世帯の初期財布も mock のままにする。

    ``l4_scale`` は**予算行 L4(呼数)の倍率**(PENDING D-99 (a)・腕 AB8-L4-SCALE)::

        倍率 > 0 → budget = call_budget_per_tick(n_agents) × 倍率
        倍率 = 0 → budget = float(n_agents)  # **無制限**

    ``0`` を「無制限」と書けるのは、アービタが ③(同一体の合流)で**体あたり高々 1 件**に
    畳んでから ⑤ の予算で切るため(``engine.arbiter.arbitrate``: 合流後の ``agent.size`` は
    体数を超えず、``n_sel = min(…, floor(budget), agent.size)``)。``budget`` に ``inf`` を
    入れると ``Arbiter._pool_cap`` と ``int(np.floor(...))`` が壊れるので**有限値で置く**。

    既定 ``1.0`` では ``budget=None`` のまま ``run_day`` に渡す=**現行の経路・現行のバイト**。
    ``budget`` を直に渡した呼び出しは倍率より優先される(倍率は manifest に 1.0 と載る)。

    **3 段目(D-99 (a′)・D-110)**: ``l4_scale`` の既定(``None``)は ``CLI_DEFAULT_L4_SCALE``
    (**0=無制限**)。``l4_scale=1.0`` で旧挙動(L4 按分・持ち越し 2 tick)を再現する(テストで固定)。
    艦隊(``fleet``)× 無制限で受理待ち枠(``--fleet-queue-capacity``)が未指定なら、**枠の既定を体数にする**
    (第289 Q28・D-55=繰り延べ 0・``apply_fleet_queue_default``)。manifest の ``l4_notes`` にその旨を載せる。
    枠を直せない艦隊だけ従来どおり警告と注記。

    **5 段目 5a(D-118)**: ``hunger_model`` の既定(渡さないとき)は ``CLI_DEFAULT_HUNGER_MODEL``
    (**energy**)。``hunger_model="v1"`` で旧規則(旧 checkpoint)を再現する(テストで固定)。

    **第 1 期 1-4(CP5-5・検収 M2)**: ``run_kind`` はランの種類(``engine.run_kind.RUN_KINDS``)。省略すると
    ここで決める=試験の中は ``test``・CLI の既定(``arm_baseline``)と違う腕の引数が 1 つでもあれば ``arm``・ほかは
    ``reproduction``(``run_arms``・``NON_ARM_RUN_KWARGS`` は数えない)。結果の ``run_kind`` に置くだけで、``run_day``
    には渡さない(設定の指紋 ``_call_args`` は変わらない)。``main`` もこの決め方を使う。

    **第 3 期 3-3(反実仮想の器)**: ``experiment`` は申込書(``engine.experiment.form.ExperimentForm``・その JSON のパス・辞書)。
    渡すと組み立てに置き(``engine.experiment.layer.staged``=``run_day`` の引数は増やさない)、ランの種類は ``counterfactual``
    (試験の中は ``test``)。``experiment_aa`` は改変を空にした A/A の枝(``ExperimentForm.aa``)。``experiment_branch`` は分岐の
    指定(``engine.experiment.branch.BranchSpec``=T0 までテープを再生・``run_branch`` が渡す)。``experiment_model`` は申込書の
    アンサンブルのモデルの札(札が 1 つなら省略可・組み立てが seed の 3 つと合わせて封印の入口で照合する)。どれも設定の指紋に入れない。
    渡さないランは何も変わらない。
    """
    exp_form = _experiment_form(experiment, aa=experiment_aa, branch=experiment_branch)
    budget = kwargs.pop("budget", None)
    run_kind = None if run_kind is None else _RK.check(run_kind)  # 第 1 期 1-4: 名の誤りはランの前に止める
    # 5 段目 5a: 空腹のモデルの既定は energy(``CLI_DEFAULT_HUNGER_MODEL``)
    kwargs.setdefault("hunger_model", CLI_DEFAULT_HUNGER_MODEL)
    if l4_scale is None:
        # 予算を直に渡した呼び出しは従来どおり倍率 1.0 と載せる(倍率より予算が優先)
        scale = 1.0 if budget is not None else float(CLI_DEFAULT_L4_SCALE)
    else:
        scale = float(l4_scale)
    if scale < 0.0:
        raise ValueError("l4_scale は 0 以上(0=無制限)")
    if run_kind is None:  # 第 1 期 1-4(検収 M2): 腕は CLI の既定と比べて決める(記録だけ)
        arms = run_arms({**kwargs, "budget": budget, "l4_scale": scale, "use_population": use_population,
                         "store_capital_yen": store_capital_yen})
        from shibuya.engine import proximity as _proximity  # 第 2 期 2-2: 環境変数の腕も腕と数える(結果が変わる腕)
        from shibuya.engine import seat_release as _seat_release  # 〔第 2 期 2-4 V3〕同じ(既定 walk と違えば腕)
        from shibuya.engine import batching as _BATCH  # 〔第 3 期 3-2〕まとめの幅の腕(環境変数か --batch-width-s)
        from shibuya.engine import body as _body  # 〔第 3 期 3-5〕TM5 の予約の腕(既定 sweep と違えば腕=結果は同じはず)
        from shibuya.engine import calendar_shadow as _calendar_shadow  # 〔第 3 期 3-1〕暦 1a の影(既定 w17 と違えば腕)
        from shibuya.engine import calendar_self as _calendar_self  # 〔第 6 期 6-2〕カレンダー 1b(既定 w17 と違えば腕)
        from shibuya.engine import memory_m1 as _memory_m1  # 〔第 6 期 6-5〕記憶の腕(結果を変える腕=既定と違えば腕)
        from shibuya.engine import regional_clock as _regional_clock  # 〔第 6 期 6-3〕時計の段 T2〜T4 の腕(既定と違えば腕)
        from shibuya.engine import speech_clock as _speech_clock
        from shibuya.engine import step_scope as _step_scope
        from shibuya.engine.contact import arm as _contact_arm  # 〔第 6 期 6-4 C1〕連絡の道具の腕(c1 は結果を変える=腕)
        from shibuya.engine.calendar2 import arm as _calendar2_arm  # 〔第 6 期 6-2 カレンダー 2〕(arm は結果を変える=腕)
        from shibuya.engine.calendar3 import arm as _calendar3_arm  # 〔第 6 期 6-2 カレンダー 3〕(arm は結果を変える=腕)
        from shibuya.engine.duties import arm as _duties_arm  # 〔第 6 期 6-6 ② 第 1 部〕店の仕事(arm は結果を変える=腕)
        from shibuya.engine.speech import layer as _speech_layer

        # 第 1 期 1-8b: 発話の口の腕(環境変数か --speech-port・run の引数ではない)は結果を変える=on は腕に数える
        # 〔第 3 期 3-3〕申込書を渡したランは反実仮想(試験 > 反実仮想 > 腕 > 再現)
        run_kind = _RK.decide(arms_on=bool(arms) or _speech_layer.arm() != _speech_layer.ARM_OFF
                              or _proximity.arm() != _proximity.DEFAULT_MODE  # 〔2-4 V2〕既定は distance
                              or _seat_release.arm() != _seat_release.DEFAULT_MODE  # 〔2-4 V3〕既定は walk
                              or _ES2.arm() != _ES2.DEFAULT_ARM  # 〔2-4 V4〕経済の段階 2 も(既定 on と違えば腕)
                              or not _BATCH.is_default()  # 〔第 3 期 3-2〕まとめの幅(既定 60 秒と違えば腕)
                              or _body.arm() != _body.DEFAULT_ARM  # 〔3-5〕体の予約の腕(既定は sweep)
                              or _calendar_shadow.arm() != _calendar_shadow.DEFAULT_MODE  # 〔3-1〕既定は w17
                              or _calendar_self.arm() != _calendar_self.DEFAULT_MODE  # 〔6-2〕既定は w17
                              or _memory_m1.arms_on()  # 〔6-5〕記憶の腕(--memory-model/-cue/-people/-grain)
                              # 〔6-3〕会話の時計・何かあった体だけ・場所ごとの時計(既定 table/all/global と違えば腕)
                              or not (_speech_clock.is_default() and _step_scope.is_default()
                                      and _regional_clock.is_default())
                              or _contact_arm.is_on()  # 〔6-4 C1〕連絡の道具の腕(--contact c1)
                              or _calendar2_arm.is_on()  # 〔6-2 カレンダー 2〕会話から生まれる予定の腕(--calendar-2 arm)
                              or _calendar3_arm.is_on()  # 〔6-2 カレンダー 3〕雇い主・祝日の腕(--calendar-3 arm)
                              or _duties_arm.is_on()  # 〔6-6 ② 第 1 部〕店の仕事の腕(--duties arm)
                              # 〔第 5 期 空間の段 1〕移動の腕(引数か環境変数 SHIBUYA_SPACE で nav1=坂と曲がる重みの腕は nav1 の中だけ)
                              or _NAV1.space_env_override(kwargs.get("space")) != _NAV1.DEFAULT_SPACE,
                              counterfactual=exp_form is not None)
    if budget is None and scale != 1.0:
        budget = float(n_agents) if scale == 0.0 else call_budget_per_tick(n_agents) * scale
    applied = apply_fleet_queue_default(kwargs.get("fleet"), scale, n_agents)
    note = "" if applied is not None else fleet_queue_note(kwargs.get("fleet"), scale, n_agents)
    if note:
        warnings.warn(note, RuntimeWarning, stacklevel=2)
    elif applied is not None:
        note = (f"艦隊 × 呼数無制限(--l4-scale 0)で --fleet-queue-capacity が未指定: 受理待ち枠の既定を体数 "
                f"{applied:,} にした(第289 Q28・D-55=受理待ちあふれの繰り延べ 0)")
    # 10f(K21 (a)): 合成世界・世帯の財布(W16 の抽出を含む)は母集団の seed から(省略=seed と同じ=今と同じ)
    pop_seed = resolve_population_seed(seed, population_seed)
    wd = Path(world_dir) if world_dir is not None else None
    world = World.load_or_synthetic(wd, n_cells=n_cells, seed=pop_seed) if wd is not None else World.synthetic(
        n_cells=n_cells, seed=pop_seed
    )
    run_world_dir = wd if (wd is not None and wd.exists()) else None
    # 〔第330・RET〕再生するテープが 10e より前の録画なら、台帳を組む前に止める(run_day と同じ検査)
    from shibuya.engine.run import check_replay_tape

    check_replay_tape(str(kwargs.get("mode", "record")), kwargs.get("replay"))
    bundle = build_ledger_bundle(
        world, n_agents, store_capital_yen,
        seed=pop_seed, world_dir=run_world_dir, use_population=use_population,
        endow=kwargs.get("resume_from") is None,  # 10d(A11): 再開では参入資本を入れ直さない
    )
    import contextlib

    from shibuya.engine.experiment import layer as _EXPL

    _stage = (contextlib.nullcontext() if exp_form is None
              else _EXPL.staged(exp_form, branch=experiment_branch, model=experiment_model))
    with _stage:  # 3-3: 申込書は組み立てが受け取る(run_day の引数・設定の指紋は今のまま)
        res = run_day(
            n_agents=n_agents,
            seed=seed,
            population_seed=population_seed,
            environment_seed=environment_seed,
            world=world,
            ticks=ticks,
            checkpoint_every=checkpoint_every,
            world_dir=run_world_dir,
            ledger=bundle,
            population=None if use_population else False,
            budget=budget,
            l4_scale=scale,
            **kwargs,
        )
    if note:
        res.l4_notes.append(note)
    # 第 1 期 1-4(CP5-5): ランの種類(記録だけ。run_day の引数=設定の指紋には入れない)
    res.run_kind = run_kind
    return res


def _batch_widths() -> tuple[int, ...]:
    """〔第 3 期 3-2〕``--batch-width-s`` で選べる幅(``engine.batching.WIDTHS_S``=刻みの幅の約数)。"""
    from shibuya.engine import batching as _batching

    return tuple(_batching.WIDTHS_S)


def _experiment_form(experiment: Any, *, aa: bool = False, branch: Any = None) -> Any:
    """〔第 3 期 3-3〕``cli.run`` の ``experiment`` → 申込書(``None``=渡さない)。``aa`` は改変を空にした A/A の枝。"""
    from shibuya.engine.experiment.form import ExperimentForm

    if experiment is None or (isinstance(experiment, str) and not experiment):
        if aa or branch is not None:
            raise ValueError("experiment_aa・experiment_branch には申込書(experiment)が要る")
        return None
    if isinstance(experiment, ExperimentForm):
        form = experiment
    elif isinstance(experiment, Mapping):
        form = ExperimentForm.from_dict(experiment)
    else:
        form = ExperimentForm.load(experiment)
    return form.aa() if aa else form


def checkpoints_payload(res: RunResult, *, run_id: str = "") -> dict[str, Any]:
    """T2(決定論)行の入力 = checkpoint 列を JSON にできる形で返す(**純関数**)。

    受入計器 ``tools/c7/c7_accept.py`` の ``normalize_checkpoints`` / ``selfconsistency``
    が読む形(``checkpoints[].{tick, combined, population_hash, schedule_hash}``)。
    ``final_hash`` は summary の「checkpoint N 点 最終 …」と同じ値(16 桁でなく全桁)。
    〔10e〕版 2: ``combined`` は既定で behavior-hash(``--hash-scheme full`` のランでは 10e より前の組み立て)。
    """
    return {
        # 10e(検収 L3): 版 2=``combined``(final)の意味が behavior-hash に変わった(manifest の hash_scheme)
        "schema": "shibuya.cli/checkpoints/2",
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
                # 二層の段 2: 活動層のあるランだけ(既定の payload は 1 キーも増えない)
                **({"activity_hash": c.activity_hash} if c.activity_hash else {}),
                # 10b(A2・A3): 状態台帳の 2 つのハッシュ。10e(E1): 既定の final=combined は behavior-hash と同じ値
                **({"behavior_hash": c.behavior_hash} if c.behavior_hash else {}),
                **({"full_hash": c.full_hash} if c.full_hash else {}),
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
        w["_hours"].add(int(row["tick"]) // STEPS_PER_HOUR)
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


#: **第 1 期 1-4(CP5-5・検収 M2)**: ランの種類の規則で「腕」に数えない ``cli.run``/``run_day`` の引数。規模と seed・
#: データと出力の置き場・再開と状態の書き出し・テープの記録と再生・暦の日付とデータの置き場・LLM の接続。これ以外の
#: 引数が CLI の既定(``arm_baseline``)と違えば腕(``engine.run_kind`` の expedient の段落・台帳 ``BR-RUN-KIND-CLI-ARMS``)。
#: CLI の引数では ``--events``(出来事の記録=指紋に入らない・``run`` の引数でない)・``--checkpoints-out``・
#: ``--undefined-out`` も腕でない。LLM の復号(``--temperature``・``--max-tokens``)は ``fleet`` の中=腕でない。
NON_ARM_RUN_KWARGS: Final[frozenset[str]] = frozenset({
    "n_agents", "seed", "population_seed", "environment_seed", "n_cells", "ticks", "sim_days", "day_index",
    "world", "world_dir", "ledger", "checkpoint_every", "checkpoint_detail", "occupancy_every", "occupancy_path",
    "census_out", "state_out", "stop_at_tick", "resume_from", "run_id", "tape_path", "mode", "replay",
    "start_sim_datetime", "holiday_csv", "school_holidays", "llm", "fleet", "fleet_wait_s", "fleet_debug_dir",
})


def _engine_run_day() -> Any:
    """``engine.run.run_day`` そのもの(このモジュールの名 ``run_day`` を差し替えた試験でも既定を正しく読む)。"""
    from shibuya.engine import run as _ENGINE_RUN

    return _ENGINE_RUN.run_day


def arm_baseline() -> dict[str, Any]:
    """腕の比べの元=CLI の既定の ``run_day`` の引数(``run_day`` の既定に、CLI と ``cli.run`` が違う既定を重ねた)。

    CLI の既定と ``run_day`` の既定が違う所は 3 つ(語彙の版 ``CLI_DEFAULT_VOCAB_VERSION``・空腹のモデル
    ``CLI_DEFAULT_HUNGER_MODEL``・呼数の倍率 ``CLI_DEFAULT_L4_SCALE``)と ``cli.run`` の 2 つ(``use_population=True``・
    ``store_capital_yen=None``)。``on``/``off`` と真偽・空の並びの書き方の違いは ``_arm_norm`` でそろえる(試験
    ``test_manifest_rules_bridges.py`` が ``main`` の既定の引数とこの表が同じことを確かめる)。
    """
    import inspect

    base = {k: p.default for k, p in inspect.signature(_engine_run_day()).parameters.items()
            if p.default is not inspect.Parameter.empty}
    base.update(vocab_version=CLI_DEFAULT_VOCAB_VERSION, hunger_model=CLI_DEFAULT_HUNGER_MODEL,
                l4_scale=float(CLI_DEFAULT_L4_SCALE), use_population=True, store_capital_yen=None)
    return base


def _arm_norm(key: str, v: Any) -> Any:
    """比べるための値の形(``on``→真・``off``→偽・空→None・列挙→値・``budget_mode`` は列挙の値に)。"""
    import enum

    from shibuya.perception.channels import BudgetMode

    if key == "budget_mode" and v is not None:
        return BudgetMode.parse(v).value
    if key == "space" and (v is None or v == _NAV1.DEFAULT_SPACE):
        return None  # 〔第 5 期 空間の段 1〕既定(legacy)を明示で渡しても腕ではない(環境変数の nav1 は下の decide で数える)
    if isinstance(v, enum.Enum):
        v = v.value
    if v is True or v == "on":
        return True
    if v is False or v == "off":
        return False
    if v is None or (isinstance(v, (str, tuple, list, dict, set, frozenset)) and len(v) == 0):
        return None
    if isinstance(v, (list, tuple)):
        return tuple(_arm_norm(key, x) for x in v)
    if isinstance(v, Mapping):
        return tuple(sorted((str(k), _arm_norm(key, x)) for k, x in v.items()))
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def run_arms(passed: Mapping[str, Any]) -> tuple[str, ...]:
    """``cli.run`` に渡された引数のうち、CLI の既定と違う腕の名(昇順)。渡さなかった引数は ``run_day`` の既定で比べる
    (``vocab_version`` を渡さない ``cli.run`` はライブラリの既定 v1=CLI の既定 v3 と違う=腕)。"""
    import inspect

    base = arm_baseline()
    rd = {k: p.default for k, p in inspect.signature(_engine_run_day()).parameters.items()
          if p.default is not inspect.Parameter.empty}
    eff = {**rd, **dict(passed)}
    out = [k for k in sorted(set(base) | set(eff))
           if k not in NON_ARM_RUN_KWARGS and _arm_norm(k, eff.get(k)) != _arm_norm(k, base.get(k))]
    return tuple(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="台帳(金/物)+世界過程つきの 1 シミュ日ラン(C4)")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--population-seed", type=int, default=None,
                    help="10f(K21 (a))母集団の seed(W16 の抽出・mock 日課・体の定数・財布・域外居住・合成世界。気象は"
                         "--environment-seed。"
                         "省略=--seed と同じ=今と同じ)。--seed は動きの seed(salt)。salt の比較では母集団の seed を固定して"
                         " --seed だけを変える")
    ap.add_argument("--environment-seed", type=int, default=None,
                    help="10f 環境の seed(気象の再生実日・大きな催し・道路工事。省略=--seed と同じ=今と同じ)。"
                         "天気は同じで動きだけ変える比較では固定する")
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
        "--signage-p-see",
        type=float,
        default=SIGNAGE_P_SEE_DEFAULT,
        metavar="P",
        help="看板の注視ゲート(知覚契約書 §4 段1 の視認確率 p_see・D-59 (b)・腕 "
             "AB6b-AD-NOTICE)。在圏セルの看板行を観測へ入れるかを 体×看板×tick の"
             "決定論的ベルヌーイで決める。既定 1.0=常に載せる(現行のバイト)・"
             "0.30/0.14=実測帯 0.14-0.79 の下側・0.0=⑥ 広告ゼロと同じ描画",
    )
    ap.add_argument(
        "--l4-scale",
        type=float,
        default=CLI_DEFAULT_L4_SCALE,
        metavar="FACTOR",
        help="呼数の上限の倍率。**既定 0=無制限**(3 段目・D-99 (a′)・D-110=L4 は監査線・"
             "manifest に llm_calls_per_agent_day と l4_exceeded)。1.0=旧挙動(L4 400 万呼/日を"
             "体数按分・持ち越し 2 tick)・0.5/2.0=半分/倍。PENDING D-99 AB8 の腕",
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
        default=CLI_DEFAULT_VOCAB_VERSION,
        help="行動語彙の版(語彙成長 v0・docs/design/v2-vocab-growth-design.md §3 F)。"
             "v1=24 語(D-113 以前からの既定・v1 の checkpoint を再現するときは明示)/"
             "v2=24 語 + 横断語「食事」(飲食店オブジェクトの affordance)/"
             "v3=行為と活動の二層(D-116・**CLI の既定**=第277): 横断 11 語+なし・5 ラベル形"
             "(理由・行動・対象・活動・まで)・活動層(--activity)・段0 辞書 v5。"
             "v3 は --intent-mode vocab だけ",
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
        help="退出の実行形(設計書 §10-3)。immediate(既定=即時)/ walk_to_platform(9a=その体の路線の"
             "ホームへ歩いて受容関数を通して乗る)・board_intent は予約(NotImplementedError)",
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
        "--report-precondition",
        choices=("on", "off"),
        default="on",
        help="D-113 ②: 通報の前提「当該事象を知覚済み」の検査(既定 on)。off=従来どおり必ず成功"
             "(第266 以前の checkpoint ba01bd0b を再現する帰無腕)",
    )
    ap.add_argument(
        "--group-norms",
        choices=("on", "off"),
        default="on",
        help="第309(Q150): 群・規範の計器(D-107 (a)・読むだけ=final は変わらない)を回すか(既定 on)",
    )
    ap.add_argument(
        "--queue-service",
        choices=("on", "off"),
        default="on",
        help="D-113 ③: 満席で並んだ体を席が空いた分だけ並んだ順に席へ入れる(既定 on)。"
             "off=第267 以前の挙動(誰も捌かず 15 tick で INTERRUPTED)",
    )
    ap.add_argument(
        "--activity",
        choices=("on", "off"),
        default="on",
        help="行為と活動の二層の活動層(段 2・D-116・既定 on)。立つのは --vocab-version v3 の"
             "ときだけ(v1/v2 では活動欄が来ない=実質無効・checkpoint 不変)。on=満了入口・活動中は"
             "場所の変化で起こさない・あたり歩行・B4b の活動の 1 行。off=抑止も満了も無効=現行",
    )
    ap.add_argument(
        "--chooser",
        choices=CHOOSER_NAMES,
        default=DEFAULT_CHOOSER,
        help="段 2a(D-114 (a)): 購入/食事/並ぶの対象の選び手。候補=現在セルの営業中・意図に合う POI。"
             "nearest=可視(W8 の視点数)の降順 → POI 索引(既定・憲法⑥の宣言つき暫定)/"
             "classical=5 段目 5b の古典的選択モデル(習慣 p_h+空腹の語で動く願望水準+可視順の揺らぎ τ)",
    )
    ap.add_argument(
        "--policy",
        choices=POLICIES,
        default=DEFAULT_POLICY,
        help="5 段目 5b(D-119 L5): 起床ごとの応答を作る方策。mock=凍結の MockLLM(既定)/"
             "classical=LLM 0 呼の古典的選択モデル(食事の門+社会生活基本調査の活動の事前分布+"
             "対応表 v0・語彙 v3 だけ)",
    )
    ap.add_argument(
        "--activity-region",
        choices=tuple(ACTIVITY_REGIONS),
        default=DEFAULT_ACTIVITY_REGION,
        help="--policy classical の事前分布の地域(kanto=関東大都市圏・既定/national=全国)",
    )
    ap.add_argument(
        "--classical-social",
        choices=("acquaintance", "near_first"),
        default="acquaintance",
        help="第2波 §2A 項 3-1(Q42): --policy classical の交際・付き合いの相手。acquaintance=B5 近接行の知人"
             "(関係辺の相手)のうち活性 A が最大の人・居なければ待つ(既定・関係 off では会話を始めない)/"
             "near_first=旧(近接行の最初の人=見知らぬ人)",
    )
    ap.add_argument(
        "--meal-gate",
        choices=("per_wake", "per_hour"),
        default="per_wake",
        help="第2波 §2A 項 4(Q48): --policy classical の食事の門の確率の読み方。per_wake=起床ごと(既定=旧)/"
             "per_hour=1 時間あたりと読み前回の門からの経過分で換算(既定の切り替えは食事の束の版上げで確認)",
    )
    ap.add_argument(
        "--classical-habit-p",
        type=float,
        default=HABIT_P,
        metavar="P",
        help="--chooser classical の習慣の確率 p_h(宣言 0.5・感度 0.25/0.75・--familiarity on のときだけ効く)",
    )
    ap.add_argument(
        "--classical-tau",
        type=float,
        default=RANK_TAU,
        metavar="TAU",
        help="--chooser classical の満足化の走査順の揺らぎ τ(宣言 1.0・感度 0.5/2.0)",
    )
    ap.add_argument(
        "--move-search-radius",
        type=int,
        default=MOVE_SEARCH_RADIUS_CELLS,
        metavar="R",
        help="段 2b(D-112 ②): 移動の対象がカテゴリ語のとき、現在セル・見えている POI に候補が無ければ "
             "cell_dist の近い順に見るセルの数(既定 5・宣言・0=近傍探索しない)",
    )
    ap.add_argument(
        "--intent-max-ticks",
        type=int,
        default=INTENT_MAX_TICKS,
        metavar="N",
        help="段 2c(意図の保持・D-112 ①): セル外の対象へ歩く意図の上限[tick]。超えたら TOO_FAR"
             "(既定 60・宣言・expedient・感度腕 30/120)",
    )
    ap.add_argument(
        "--familiarity",
        choices=FAMILIARITY_MODES,
        default="off",
        help="4 段目(記憶の先行部品=M13 訪問+M17 露出): 体×K 行の親しみの表を確保して、訪問・看板の"
             "露出・セルに入った回を数える(本段では誰も読まない)。既定 off=表を確保しない=既定の "
             "checkpoint 不変",
    )
    ap.add_argument(
        "--familiarity-k",
        type=int,
        default=FAMILIARITY_K,
        metavar="K",
        help="親しみの表の体あたりの行数(既定 64・宣言・感度 32/128)",
    )
    ap.add_argument(
        "--memory",
        choices=MEMORY_MODES,
        default="off",
        help="6 段目 6a/6b(記憶 第 1 段): 体×N 行の記憶の表を確保して、行動の成否・会話・気づき・"
             "強い看板(初見)を書き(6a)、各呼で k 件を想起して B5 の最後に「記憶」の 1 行を載せる(6b)。"
             "既定 off=表を確保しない=既定の checkpoint も描画バイトも不変",
    )
    ap.add_argument(
        "--memory-n",
        type=int,
        default=MEMORY_N,
        metavar="N",
        help="記憶の表の体あたりの行数(既定 128・宣言・感度 64/256)",
    )
    ap.add_argument(
        "--memory-tau",
        type=float,
        default=RECALL_TAU,
        metavar="TAU",
        help="6b(想起): A ≥ τ の行だけ想起する閾値(既定 −2.0・第295 の決め・--memory on のときだけ効く)",
    )
    ap.add_argument(
        "--store-memory",
        choices=STORE_MEMORY_MODES,
        default="off",
        help="D-120 7a(店の評価の記憶): 体×32 行の店の評価の表を確保し、記憶のエピソード(購入/食事/並ぶの"
             "成否・看板の初見)から書く(本段では誰も読まない)。--memory on のときだけ。既定 off=表を確保しない"
             "=既定の checkpoint 不変",
    )
    ap.add_argument(
        "--store-memory-n",
        type=int,
        default=STORE_MEMORY_N,
        metavar="M",
        help="店の評価の表の体あたりの行数(既定 32・宣言・感度 16/64)",
    )
    ap.add_argument(
        "--store-sigma",
        default=None,
        metavar="JSON",
        help='出どころ別の雑音 σ(例 \'{"self": 1, "wom": 1, "signage": 1, "net": 1}\'・既定 自分 1/伝聞 2/'
             "看板 4/ネット 2=宣言・感度腕)",
    )
    ap.add_argument(
        "--store-wom",
        choices=("on", "off"),
        default="on",
        help="D-120 7c(N8 の腕): 口コミ(7b の聞き手への転写)を使うか(既定 on・--store-memory on のときだけ)",
    )
    ap.add_argument(
        "--store-signage",
        choices=("on", "off"),
        default="on",
        help="D-120 7c(N8 の腕): 看板の初見から店の行を書くか(N2 (iii)・既定 on)",
    )
    ap.add_argument(
        "--store-recall-scope",
        choices=("all", "conversation"),
        default="all",
        help="D-120 7c: B5 の想起で店の行を候補にする入口(既定 all=全入口・conversation=会話だけ=感度腕)",
    )
    ap.add_argument(
        "--wom-source",
        choices=("utterance", "reason-target"),
        default="utterance",
        help="第2波 §2A 項 1(Q57): 口コミの抽出の源。utterance=発話の欄(ひと言)だけ(既定・いまの語彙 v3 には"
             "ひと言欄が無い=抽出 0)/ reason-target=旧(v3 で理由欄+対象欄=本人の内心が聞き手に漏れる欠陥・"
             "旧の再現用)。--store-memory on のときだけ効く",
    )
    ap.add_argument(
        "--relations",
        choices=("off", "on"),
        default="off",
        help="C10 8a(関係辺): 体×15 辺の関係の表を確保し、W16+W17 の共在で初期化・会話/手伝いのエピソードから"
             "書き、B5 近接行の「知人」の印に結線する(--memory on のときだけ)。既定 off=既定の checkpoint 不変",
    )
    ap.add_argument("--rel-k", type=int, default=15, metavar="K",
                    help="関係辺の数(既定 15・感度 5/50)")
    ap.add_argument("--rel-tau", type=float, default=None, metavar="TAU",
                    help="辺として残る A の閾値 τ_rel(既定=在職期間のハッシュ v2 での全母集団の逆算 −2.322・感度 ±0.5)")
    ap.add_argument("--rel-d", type=float, default=0.5, metavar="D",
                    help="関係辺の A の減衰 d(既定 0.5=記憶と同じ・感度 0.25/0.75)")
    ap.add_argument("--rel-init-density", type=float, choices=(0.5, 1.0, 2.0), default=1.0,
                    help="初期網の密度の腕(0.5=共在が中央値以上・1.0=共在 > 0・2.0=共在 0 の組も入れる)")
    ap.add_argument("--rel-tenure-weeks", type=float, default=13.0, metavar="W",
                    help="C10 8b(Q89/Q90): 初期辺の在職期間 T_uv の上限[週](既定 13・感度 26)")
    ap.add_argument("--rel-invite", choices=("off", "on"), default="on",
                    help="C10 8b: 名指しの無い会話の相手を関係辺の重み(5 人 40%%・10 人 20%%・残り 40%%)で引く"
                         "(--relations on のときだけ効く・既定 on)")
    ap.add_argument("--rel-acq-wake", choices=("off", "on"), default="on",
                    help="C10 8b(R7 (a)): 知人出現の起床(同一相手 60 分・--relations on のときだけ効く・既定 on)")
    ap.add_argument("--rel-copresent", choices=("off", "on"), default="off",
                    help="C10 8b(Q91): 同席の書き手(同セル・2 m 内・連続 5 分で 1 本・相手ごと 1 日 1 本・既定 off)")
    ap.add_argument("--conv-max-participants", type=int, choices=(2, 3), default=2,
                    help="C10 8a(D-93 (d)): 会話の参加上限(既定 2・3=会話中の相手に話しかけた体が加わる)")
    ap.add_argument(
        "--store-decay",
        choices=STORE_DECAY_MODES,
        default=DEFAULT_STORE_DECAY,
        help="店の評価の減衰の形(既定 actr=ACT-R d=0.5・ga=0.995/時・citysim=中立回帰 0.03/日=感度腕)",
    )
    ap.add_argument(
        "--hunger-model",
        choices=HUNGER_MODELS,
        default=CLI_DEFAULT_HUNGER_MODEL,
        help="5 段目 5a(D-118): 空腹のモデル。energy=体のエネルギー収支(既定・体重と EER・活動の "
             "METs で消費・食事/軽食/飲料で摂取・B5 は語)/v1=旧規則(+1/30 分・購入/食事で −4)"
             "=旧 checkpoint の再現",
    )
    ap.add_argument(
        "--energy-rate",
        choices=ENERGY_RATES,
        default=DEFAULT_ENERGY_RATE,
        help="消費の式(--hunger-model energy のときだけ効く)。eer=EER/1440×METs/基準日の平均 METs"
             "(既定・K1 (c))/bmr=基礎代謝量×METs(感度腕・K1 (a))",
    )
    ap.add_argument(
        "--meal-sleep-defer",
        choices=("off", "on"),
        default="off",
        help="第2波 §2B 項 1(Q34 (b)): 範囲外の既定の食事時刻に W17 で就寝中の体。off=旧(そのまま食べる・既定)/"
             "on=起床の時刻へ遅らせ、時間帯の窓の中なら食べる(過ぎていれば無し)。--hunger-model energy のときだけ効く",
    )
    ap.add_argument(
        "--home-meal",
        choices=("off", "plan"),
        default="off",
        help="第2波 §2B 項 2(Q35 (a)): 範囲内の自宅の食事行。off=旧(食事は飲食店でしか成立しない・既定)/"
             "plan=行の開始に自宅に居て起きていれば予定の実行として食べる(金と物は動かさない・照合から外す)",
    )
    ap.add_argument(
        "--hunger-words",
        choices=("hungry", "all"),
        default="hungry",
        help="第2波 §2B 項 3(Q31 (b)): B5 の空腹の語。hungry=空腹以上だけ描く(既定=旧)/all=満腹・ふつうも描く",
    )
    ap.add_argument(
        "--eatery",
        choices=EATERY_MODES,
        default=DEFAULT_EATERY_MODE,
        help="段 1b(D-96 nightlife (b)): 行動語「食事」が成立する飲食店の集合。food=現行"
             "(cat の価格帯「飲食」・既定・checkpoint はバイト不変)/place_food=W17 の場所語"
             "「飲食店」と同じ集合(food+nightlife のうち club/karaoke/sauna/net_cafe でないもの)。"
             "価格は動かさない",
    )
    ap.add_argument(
        "--role-words",
        choices=("on", "off"),
        default="on",
        help="D-113 ④: B0 の末尾に役割語 12 語の 1 行を足す(既定 on・行動契約書 §2.2)。"
             "off=第268 以前の B0(それ以前に録ったテープの再生・帰無腕)",
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
    _NAV1.add_space_args(ap)
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
    ap.add_argument(
        "--events",
        choices=("on", "off"),
        default="on",
        help="第 1 期 1-3: 出来事の記録(既定 on)。off で記録しない(環境変数 SHIBUYA_EVENTS=off と同じ)。"
             "記録は結果を変えないので設定の指紋には入らない(manifest の日次の記録 events.on に出る)",
    )
    ap.add_argument(
        "--memory-store",
        choices=("mem", "events"),
        default=None,
        help="第 1 期 1-6 記憶の器 M0 の腕(既定 mem=今の記憶の表だけ・環境変数 SHIBUYA_MEMORY_STORE と同じ。指定すれば"
             "環境変数より強い)。events で --memory on のランに記憶の器(出来事の記録への目印)を作り、想起を器から引き、"
             "テープに列 recalled_event_ids を足す。器は結果を変えないので設定の指紋には入らない"
             "(manifest の memory_summary.memory_store に出る)",
    )
    ap.add_argument(
        "--memory-model",
        choices=("m0", "m1"),
        default=None,
        help="第 6 期 6-5 記憶の強さの式の腕(既定 m0=今の式・環境変数 SHIBUYA_MEMORY_MODEL と同じ。指定すれば環境変数より強い)。"
             "m1=ACT-R の折衷形(時刻は秒・+1 なし・最短の符号化時間・忘れる速さの人ごとのばらつき 15%・境目 τ は仮の値)。"
             "--memory-store events のランだけ効く(記憶 off のランで立てると止める・結果を変える腕=ランの種類は腕・manifest の"
             "設定の節 memory_summary.mr65_arms と設定の指紋に入る・計器は memory_summary.memory_store.mr65)",
    )
    ap.add_argument(
        "--memory-cue",
        choices=("id", "embed"),
        default=None,
        help="第 6 期 6-5 想起の手がかりの腕(既定 id=その場の手がかり=ID の一致・環境変数 SHIBUYA_MEMORY_CUE)。embed=意味の手がかり"
             "(埋め込み=--memory-embed-model・会話中は相手の直前の発言・ほかは本人の直前の理由)",
    )
    ap.add_argument(
        "--memory-embed-model",
        choices=("ruri-v3-30m", "ruri-v3-130m", "ngram-test"),
        default=None,
        help="第 6 期 6-5 埋め込みのモデル(既定 ruri-v3-30m・環境変数 SHIBUYA_MEMORY_EMBED_MODEL)。Ruri の重みは "
             "data/models/ruri/ に版を固定して置く(本段では未取得)。ngram-test は重みの要らない試験用の代わり(意味ではない)",
    )
    ap.add_argument(
        "--memory-people",
        choices=("table", "memory"),
        default=None,
        help="第 6 期 6-5 人も記憶の一つの腕(既定 table=今の関係の層・環境変数 SHIBUYA_MEMORY_PEOPLE)。memory=人を同じ器・同じ式"
             "(出来事 128・店 32 の固定の上限を外し、種類ごとの上限 256 まで幅を倍に・上限で思い浮かぶ強さの一番低い行を消す・"
             "忘れる=消す・関係の表を読まない)。--memory-model m1 が前提・再開には対応しない",
    )
    ap.add_argument(
        "--memory-grain",
        choices=("each", "day"),
        default=None,
        help="第 6 期 6-5 体の出来事を記録へ書く粒度の腕(既定 each=1 回 1 行・環境変数 SHIBUYA_MEMORY_GRAIN)。day=同じ記憶の行は"
             "日に 1 行(2-3 の 14.6 行/体/日を減らす案)。再開には対応しない",
    )
    ap.add_argument(
        "--decision-port",
        choices=("legacy", "port"),
        default=None,
        help="第 1 期 1-8 候補の口 J0 の腕(既定 legacy=今の道・環境変数 SHIBUYA_DECISION_PORT と同じ。指定すれば環境変数より"
             "強い)。port で判断の 1 呼を候補の口に通す(候補は 5 つの源・順のシャッフル・番号で返す・mock と古典は今と同じ"
             "番号=結果は同じ)。口は結果を変えないので設定の指紋には入らない(manifest の decision_port に出る)",
    )
    ap.add_argument(
        "--speech-port",
        choices=("off", "on"),
        default=None,
        help="第 1 期 1-8b 発話の口の腕(既定 off=今の道・環境変数 SHIBUYA_SPEECH_PORT と同じ。指定すれば環境変数より強い)。"
             "on で会話の番の呼び出しだけ B6 の末尾に ひと言 の欄を求め(語彙 v3)、答えの ひと言 を発話の口に通す(出来事の"
             "記録に 1 行・相手の次の入力の B6 に素性タグと命令文の除去つきで載る・口コミの抽出に渡す)。on は結果を変えるので"
             "設定の指紋に入り、ランの種類は腕(manifest の speech_port に出る)",
    )
    ap.add_argument(
        "--proximity",
        choices=("cell", "distance"),
        default=None,
        help="第 2 期 2-2 段 11a 近接の判定の腕(〔2-4 V2〕既定 distance・環境変数 SHIBUYA_PROXIMITY と同じ。指定すれば"
             "環境変数より強い)。distance で会話・返事待ち・3 人会話・離脱・招待の相手・偶然・知人出現(気づく確率)・同席・"
             "B5 の近接行を「同じ層・距離 ≤ d(同じ店の区画の中は距離を見ない)」で判定する。cell=2-2 までの判定(同じセル)"
             "=切替口(旧値の再現)。腕は設定の指紋に入れない(manifest の proximity に出る・既定と違えばランの種類は arm)",
    )
    ap.add_argument(
        "--proximity-d",
        choices=("1.0", "2.0", "2.5"),
        default=None,
        help="第 2 期 2-2 段 11a 会話の距離 d[m] の感度の腕(既定 2.0=B3 の決め打ち・環境変数 SHIBUYA_PROXIMITY_D と同じ。"
             "--proximity distance のときだけ効く)",
    )
    ap.add_argument(
        "--economy-stage2",
        choices=("off", "on"),
        default=None,
        help="第 2 期 2-1 経済の段階 2 の腕(〔2-4 V4〕既定 on・環境変数 SHIBUYA_ECONOMY_STAGE2 と同じ。指定すれば環境変数より"
             "強い)。on で賃金(給料日)・引き出し(ATM)・支払いの方法(現金/口座)・レジの消費税・来街者の口座を動かす"
             "(manifest の economy.stage2 に出る・設定の指紋には入らない)。off=2-1 までの既定=切替口(旧値の再現)",
    )
    ap.add_argument(
        "--economy-stage2-parts",
        type=str,
        default=None,
        help="第 2 期 2-1 経済の段階 2 の部品(カンマ区切り・既定=全部 wages,withdraw,payment,tax,visitors・環境変数 "
             "SHIBUYA_ECONOMY_STAGE2_PARTS と同じ)。1 つずつ測るため",
    )
    ap.add_argument(
        "--seat-release",
        choices=("walk", "legacy"),
        default=None,
        help="第 2 期 2-4 V3 在席の印を歩き出しで解く腕(既定 walk・環境変数 SHIBUYA_SEAT_RELEASE と同じ。指定すれば環境変数より"
             "強い)。walk=移動の意図で歩き出した体の在席の印(店の席)を解く。legacy=2-4 より前の挙動(退去・乗車・滞在の上限で"
             "しか解かない)=切替口(旧値の再現)。腕は設定の指紋に入れない(manifest の leave_effects.seat_release に出る・"
             "既定と違えばランの種類は arm)",
    )
    ap.add_argument(
        "--batch-width-s",
        type=int,
        choices=_batch_widths(),
        default=None,
        help="第 3 期 3-2 計算のまとめの幅[秒](既定 60=刻みの幅=今と同じ・環境変数 SHIBUYA_BATCH_WIDTH_S と同じ。指定すれば"
             "環境変数より強い)。刻みの幅の約数だけ選べる。進行役は窓 [t, t+W) の中の事象を時刻順に処理する(T1 の世界の事象"
             "は刻みの事象だけ=どの幅でも同じ結果)。既定と違えば設定の指紋に入り、ランの種類は arm(manifest の batching に出る)",
    )
    ap.add_argument(
        "--body-schedule",
        choices=("sweep", "reserve"),
        default=None,
        help="第 3 期 3-5 TM5 の体の予約の腕(既定 sweep・環境変数 SHIBUYA_BODY_SCHEDULE と同じ。指定すれば環境変数より強い)。"
             "sweep=毎刻み全員の体を規則に通す(今の形)。reserve=体ごとに次に段の境目(空腹・疲れ・暑さ)を越える刻みを予約し、"
             "予約の来た体と入力の変わった体だけを規則に通す(結果は sweep と同じでなければならない=T3 で有効)。腕は設定の指紋に"
             "入れない(manifest の body に出る・既定と違えばランの種類は arm)",
    )
    ap.add_argument(
        "--talk-clock",
        choices=("table", "mora"),
        default=None,
        help="第 6 期 6-3 時計の段 T2 会話の時計の腕(既定 table・環境変数 SHIBUYA_TALK_CLOCK と同じ。指定すれば環境変数より"
             "強い)。table=今の 1 ターンの長さの表(1 呼=1 発話ブロック=刻み 1 つ)。mora=発言の長さをモーラ数 × その人の話す速さ"
             "(人ごとの値+発言ごとの揺れ・R-111 §3)で数え、会話ごとの時計(間=日本語の平均 7 ms)を窓の待ち行列の事象として"
             "時刻順に処理する(計器だけ=会話の番は今も刻みに 1 回)。既定と違えば設定の指紋に入り、ランの種類は arm(manifest の"
             "talk_clock に出る)",
    )
    ap.add_argument(
        "--step-scope",
        choices=("all", "changed"),
        default=None,
        help="第 6 期 6-3 時計の段 T3 何かあった体だけの腕(既定 all・環境変数 SHIBUYA_STEP_SCOPE と同じ。指定すれば環境変数より"
             "強い)。changed=体の反映を TM5 の予約(3-5 の reserve)にし、内受容の段の跨ぎの判定を変化の印の体だけに通す(結果は"
             "all と同じでなければならない=一致の確認)。既定と違えば設定の指紋に入り、ランの種類は arm(manifest の step_scope)",
    )
    ap.add_argument(
        "--clock",
        choices=("global", "regional", "mixed"),
        default=None,
        help="第 6 期 6-3 時計の段 T4 場所ごとの時計の腕(既定 global・環境変数 SHIBUYA_CLOCK と同じ。指定すれば環境変数より"
             "強い)。regional=区域(セルの重心の 500 m の塊)ごとに窓を進め、区域をまたぐ事象は境目で届ける(結果は global と同じ"
             "でなければならない)。mixed=口だけ(値は空欄=選ぶと止める)。既定と違えば設定の指紋に入り、ランの種類は arm"
             "(manifest の clock・clock_kind)",
    )
    ap.add_argument(
        "--calendar-shadow",
        choices=("w17", "1a"),
        default=None,
        help="第 3 期 3-1 暦 1a の影の腕(既定 w17・環境変数 SHIBUYA_CALENDAR_SHADOW と同じ。指定すれば環境変数より強い)。"
             "1a=計画実行層の勤務と授業の影を W20 の週の表(<world>/w20_calendar_1a.parquet・SHIBUYA_CALENDAR_W20)から作り、"
             "manifest の calendar_shadow に出す(計器だけ=出入りは今の W17 のまま・1a のランだけ設定の指紋に入る・ランの種類は arm)",
    )
    ap.add_argument(
        "--calendar",
        choices=("w17", "1b"),
        default=None,
        help="第 6 期 6-2 カレンダー 1b の腕(既定 w17・環境変数 SHIBUYA_CALENDAR と同じ。指定すれば環境変数より強い)。"
             "1b=W20 の時刻つきの勤務の約束を持つ体の出入り(出発するか・いつか・帰るか)を本人の判断(仮のモデル=mock/古典)へ"
             "渡す(その体の W17 の到着・退出は実行しない・就寝と起床は W17 のまま)。W20 の週の表は <world>/w20_calendar_1a.parquet"
             "か SHIBUYA_CALENDAR_W20。manifest の末尾に calendar_1b・1b のランだけ設定の指紋に入る・ランの種類は arm",
    )
    ap.add_argument(
        "--contact",
        choices=("off", "c1"),
        default=None,
        help="第 6 期 6-4 連絡の道具 C1 の腕(既定 off=今の道・環境変数 SHIBUYA_CONTACT と同じ。指定すれば環境変数より強い)。"
             "c1=1 対 1 とグループのメッセージ・電話・チャットの会話の状態・目と心の向き(届くのはエンジン・気づく/読む/返す/"
             "出る/切るは本人の判断の口=仮のモデル)。下の腕は環境変数だけ(SHIBUYA_CONTACT_UNNOTICED=i/ii/iii・"
             "SHIBUYA_CONTACT_SEND=b/c)。c1 は結果を変えるので設定の指紋に入り、ランの種類は腕(manifest の contact_c1 に出る)",
    )
    ap.add_argument(
        "--calendar-2",
        dest="calendar_2",
        choices=("off", "arm"),
        default=None,
        help="第 6 期 6-2 カレンダー 2 の腕(既定 off=今の道・環境変数 SHIBUYA_CALENDAR_2 と同じ。指定すれば環境変数より強い)。"
             "arm=会話(対面・通話・メッセージ・チャット)から生まれる約束を各自が自分の行として持つ・置き場所と確かさと元の会話・"
             "壊れた予定だけ拒む・頭の中の予定は記憶で思い出せたときだけ見える・本人が約束の場所へ歩く(判断は仮のモデル)。"
             "arm は結果を変えるので設定の指紋に入り、ランの種類は腕(manifest の calendar_2 に出る)",
    )
    ap.add_argument(
        "--calendar-3",
        dest="calendar_3",
        choices=("off", "arm"),
        default=None,
        help="第 6 期 6-2 カレンダー 3 の腕(既定 off=今の道・環境変数 SHIBUYA_CALENDAR_3 と同じ。指定すれば環境変数より強い)。"
             "arm=雇い主(組織の担当のうち店長か最初の担当=つなぎ)が週の最後の日に非正規とシフト勤務の働く人の翌週の枠を選び、"
             "C3 の職場の連絡(C1 の口)で知らせる・働く人はカレンダー 2 の形で自分の行に書く・休みの申し出と返事・遅れの連絡・"
             "祝日は暦の常識(判断は仮のモデル)。--contact c1 と --calendar-2 arm が要る。試験用の印は環境変数 "
             "SHIBUYA_CALENDAR_3_TRIAL=on(日曜始まり・祝日を含むランを分析に使わない印で回す)。arm は結果を変えるので設定の"
             "指紋に入り、ランの種類は腕(manifest の calendar_3 に出る)",
    )
    ap.add_argument(
        "--duties",
        dest="duties",
        choices=("off", "arm"),
        default=None,
        help="第 6 期 6-6 ② 第 1 部 店の仕事の腕(既定 off=今の道・環境変数 SHIBUYA_DUTIES と同じ。指定すれば環境変数より強い)。"
             "arm=開閉店・補充(品出し)・売れ残りの廃棄を、担当(雇用の行)が店に居る店では本人の判断にする(店の決まり=営業時間は"
             "担当が知る・棚が減ったら気づく・閉めた店の売れ残りを捨てる・判断は仮のモデル)。担当が居ない店は今の conf 宣言つきの"
             "つなぎ。arm は結果を変えるので設定の指紋に入り、ランの種類は腕(manifest の duties に出る)",
    )
    ap.add_argument(
        "--experiment", type=str, default="",
        help="第 3 期 3-3 反実仮想の申込書(JSON のパス・engine.experiment.form)。既定なし=今と同じ。渡すとランの種類は "
             "counterfactual・申込書の指紋は manifest の experiment に出る(設定の指紋には入らない)",
    )
    ap.add_argument(
        "--experiment-branch", type=str, default="",
        help="第 3 期 3-3 分岐の基準のランの記録(tape/・state/・checkpoints.json のあるディレクトリ)。--experiment と一緒に"
             "使う。T0 までテープを再生して T0 から今の方策で続け、A/A の枝 2 本と改変の枝 1 本を回して R-71 の 4 つの確認を"
             "書く(<記録>/branches/<申込書の指紋の先頭 16 字>/branch_report.json)。〔3-3b〕申込書の T0 は計算のまとめの窓の頭"
             "(基準のランの batching.width_s ずつ)でなければ止める(3-3 では刻みの頭でない T0 を切り上げて受けていた=3-3b で"
             "止める形に変えた・申込書の T0 を黙って丸めない)",
    )
    ap.add_argument(
        "--experiment-model", type=str, default="",
        help="第 3 期 3-3 申込書のアンサンブルのモデルの札(札が 2 つ以上のときに渡す・封印の入口で seed の 3 つと合わせて照合)",
    )
    ap.add_argument(
        "--experiment-aa", action="store_true",
        help="第 3 期 3-3 改変を空にした A/A の枝として回す(--experiment-branch と一緒なら 3 本とも A/A)",
    )
    # --llm / --endpoints / --model / --mode / --run-id / --tape / --temperature /
    # --max-tokens / --fleet-wait-s(C6-a)
    add_fleet_args(ap)
    add_calendar_args(ap)  # 10a: --calendar-weekday / --start-date / --holiday-csv / --school-holidays・10c: --rng-scheme
    args = ap.parse_args(argv)
    try:
        refractory_scale = parse_refractory_scale(args.refractory_scale)
        if float(args.pnotice_d50_scale) <= 0.0:
            raise argparse.ArgumentTypeError("--pnotice-d50-scale は正の値")
        if not (0.0 <= float(args.attendance_rate) <= 1.0):
            raise argparse.ArgumentTypeError("--attendance-rate は 0.0〜1.0")
        if not (0.0 <= float(args.signage_p_see) <= 1.0):
            raise argparse.ArgumentTypeError("--signage-p-see は 0.0〜1.0 の確率")
        if float(args.l4_scale) < 0.0:
            raise argparse.ArgumentTypeError("--l4-scale は 0 以上(0=無制限)")
        if str(args.vocab_version) == "v3" and str(args.intent_mode) != "vocab":
            # 二層の段 3: CLI の既定が v3 になったので、open/hint の腕は版を明示させる
            # (v3 の B0 は vocab 腕だけ=段 1 の決め)。
            raise argparse.ArgumentTypeError(
                "--intent-mode open/hint は --vocab-version v1 か v2 と一緒に使う"
                "(語彙 v3 の B0 は vocab 腕だけ)"
            )
    except argparse.ArgumentTypeError as exc:  # 使い方の誤りは traceback ではなく usage で返す
        ap.error(str(exc))
    if str(args.events) in ("off", "on"):  # 第 1 期 1-3: 出来事の記録の切替口(組み立てが読む。CLI は環境変数より強い=検収 L3)
        from shibuya.engine.events import log as _events_log

        _events_log.set_enabled(str(args.events) == "on")
    if args.memory_store is not None:  # 第 1 期 1-6: 記憶の器の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine import memory_store as _memory_store

        _memory_store.set_arm(str(args.memory_store))
    # 〔第 6 期 6-5〕記憶の腕(組み立てが読む。指定は環境変数より強い)
    for _mk, _mv in (("model", args.memory_model), ("cue", args.memory_cue), ("embed_model", args.memory_embed_model),
                     ("people", args.memory_people), ("grain", args.memory_grain)):
        if _mv is not None:
            from shibuya.engine import memory_m1 as _memory_m1

            _memory_m1.set_arm(_mk, str(_mv))
    if args.decision_port is not None:  # 第 1 期 1-8 J0: 候補の口の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine.decision import layer as _decision_layer

        _decision_layer.set_arm(str(args.decision_port))
    if args.speech_port is not None:  # 第 1 期 1-8b: 発話の口の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine.speech import layer as _speech_layer

        _speech_layer.set_arm(str(args.speech_port))
    if args.proximity is not None:  # 第 2 期 2-2 段 11a: 近接の判定の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine import proximity as _proximity

        _proximity.set_arm(str(args.proximity))
    if args.proximity_d is not None:
        from shibuya.engine import proximity as _proximity

        _proximity.set_d(str(args.proximity_d))
    if args.batch_width_s is not None:  # 〔第 3 期 3-2〕まとめの幅の腕(組み立てと進行役が読む。指定は環境変数より強い)
        from shibuya.engine import batching as _batching

        _batching.set_arm(int(args.batch_width_s))
    if args.seat_release is not None:  # 〔第 2 期 2-4 V3〕在席の印の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine import seat_release as _seat_release

        _seat_release.set_arm(str(args.seat_release))
    if args.body_schedule is not None:  # 〔第 3 期 3-5〕TM5 の体の予約の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine import body as _body

        _body.set_arm(str(args.body_schedule))
    if args.talk_clock is not None:  # 〔第 6 期 6-3 T2〕会話の時計の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine import speech_clock as _speech_clock

        _speech_clock.set_arm(str(args.talk_clock))
    if args.step_scope is not None:  # 〔第 6 期 6-3 T3〕何かあった体だけの腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine import step_scope as _step_scope

        _step_scope.set_arm(str(args.step_scope))
    if args.clock is not None:  # 〔第 6 期 6-3 T4〕場所ごとの時計の腕(組み立てと進行役が読む。指定は環境変数より強い)
        from shibuya.engine import regional_clock as _regional_clock

        _regional_clock.set_arm(str(args.clock))
    if args.calendar_shadow is not None:  # 〔第 3 期 3-1〕暦 1a の影の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine import calendar_shadow as _calendar_shadow

        _calendar_shadow.set_arm(str(args.calendar_shadow))
    if args.calendar is not None:  # 〔第 6 期 6-2〕カレンダー 1b の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine import calendar_self as _calendar_self

        _calendar_self.set_arm(str(args.calendar))
    if args.contact is not None:  # 〔第 6 期 6-4 C1〕連絡の道具の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine.contact import arm as _contact_arm

        _contact_arm.set_arm(str(args.contact))
    if args.calendar_2 is not None:  # 〔第 6 期 6-2 カレンダー 2〕会話から生まれる予定の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine.calendar2 import arm as _calendar2_arm

        _calendar2_arm.set_arm(str(args.calendar_2))
    if args.calendar_3 is not None:  # 〔第 6 期 6-2 カレンダー 3〕雇い主・祝日の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine.calendar3 import arm as _calendar3_arm

        _calendar3_arm.set_arm(str(args.calendar_3))
    if args.duties is not None:  # 〔第 6 期 6-6 ② 第 1 部〕店の仕事の腕(組み立てが読む。指定は環境変数より強い)
        from shibuya.engine.duties import arm as _duties_arm

        _duties_arm.set_arm(str(args.duties))
    if args.economy_stage2 is not None:  # 第 2 期 2-1: 経済の段階 2 の腕(組み立てと台帳の組み立てが読む)
        _ES2.set_arm(str(args.economy_stage2))
    if args.economy_stage2_parts is not None:
        try:
            _ES2.set_parts(str(args.economy_stage2_parts))
        except ValueError as exc:
            ap.error(str(exc))
    run_kwargs = dict(  # 第 1 期 1-4(検収 M2): ランの種類は run が決める(試験 > 反実仮想 > CLI の既定と違う腕 > 再現)
        n_agents=args.agents,
        seed=args.seed,
        population_seed=args.population_seed,
        environment_seed=args.environment_seed,
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
        signage_p_see=float(args.signage_p_see),
        l4_scale=float(args.l4_scale),
        sleep_suppression=not args.no_sleep_suppression,
        plan_sleep=not args.no_plan_sleep,
        plan_executor=not args.no_plan_executor,
        exit_mode=str(args.exit_mode),
        group_norms=str(args.group_norms),
        report_precondition=(str(args.report_precondition) == "on"),
        queue_service=(str(args.queue_service) == "on"),
        activity=(str(args.activity) == "on"),
        eatery=str(args.eatery),
        chooser=str(args.chooser),
        policy=str(args.policy),
        activity_region=str(args.activity_region),
        classical_social=str(args.classical_social),
        meal_gate=str(args.meal_gate),
        classical_habit_p=float(args.classical_habit_p),
        classical_tau=float(args.classical_tau),
        move_search_radius=int(args.move_search_radius),
        intent_max_ticks=int(args.intent_max_ticks),
        familiarity=str(args.familiarity),
        familiarity_k=int(args.familiarity_k),
        memory=str(args.memory),
        memory_n=int(args.memory_n),
        memory_tau=float(args.memory_tau),
        store_wom=str(args.store_wom),
        store_signage=str(args.store_signage),
        store_recall_scope=str(args.store_recall_scope),
        wom_source=str(args.wom_source),
        relations=str(args.relations),
        rel_k=int(args.rel_k),
        rel_tau=(float(args.rel_tau) if args.rel_tau is not None else None),
        rel_d=float(args.rel_d),
        rel_init_density=float(args.rel_init_density),
        conv_max_participants=int(args.conv_max_participants),
        rel_tenure_weeks=float(args.rel_tenure_weeks),
        rel_invite=str(args.rel_invite),
        rel_acq_wake=str(args.rel_acq_wake),
        rel_copresent=str(args.rel_copresent),
        store_memory=str(args.store_memory),
        store_memory_n=int(args.store_memory_n),
        store_sigma=args.store_sigma,
        store_decay=str(args.store_decay),
        hunger_model=str(args.hunger_model),
        energy_rate=str(args.energy_rate),
        meal_sleep_defer=str(args.meal_sleep_defer),
        home_meal=str(args.home_meal),
        hunger_words=str(args.hunger_words),
        role_words=(str(args.role_words) == "on"),
        attendance_rate=float(args.attendance_rate),
        derive_rule=str(args.derive_rule),
        outside_suppression=not args.no_outside_suppression,
        geometry=str(args.geometry),
        area_source=str(args.area_source),
        space=_NAV1.space_from_args(args),
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
        **calendar_kwargs_from_args(args),  # 10a: 暦の口(〔第 2 部〕応答の遅れの切替口は消した)
        **({"mode": "replay", "replay": args.replay} if args.replay else {}),
    )
    if args.experiment_aa and not args.experiment:
        ap.error("--experiment-aa には --experiment(申込書)が要る")
    if args.experiment_branch:  # 第 3 期 3-3: 分岐(T0 までテープを再生・A/A の枝 2 本+改変の枝 1 本・4 つの確認)
        if not args.experiment:
            ap.error("--experiment-branch には --experiment(申込書)が要る")
        from shibuya.engine.experiment import branch as _BRANCH

        outcome = _BRANCH.run_branch(_experiment_form(args.experiment), args.experiment_branch, runner=run,
                                     run_kwargs=run_kwargs, aa_only=bool(args.experiment_aa))
        res = outcome.branch
        sm = outcome.report["summary"]
        print(f"[分岐] T0={outcome.report['T0_step']} 確認 a={sm['a']} b={sm['b']} d={sm['d']} "
              f"最初の食い違い 刻み={sm['c_step']} 系={sm['c_system']} → "
              f"{outcome.report_path.name if outcome.report_path else '-'}")
    else:
        # 3-3: 申込書を渡したときだけ欄を足す(既定の引数は今のまま=腕の数え方も変わらない)
        res = run(**run_kwargs, **({"experiment": args.experiment, "experiment_aa": bool(args.experiment_aa),
                                    "experiment_model": (args.experiment_model or None)} if args.experiment else {}))
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
