"""interfaces.cli.wire_economy — 割る段で ``cli.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``interfaces/cli/main.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from pathlib import Path
from typing import Final
import numpy as np
from shibuya.world.facts import population_reader as POP
from shibuya.foundation.rng import stream
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.economy import anchors as AN
from shibuya.economy import census as CS
from shibuya.economy import entry_capital as EC
from shibuya.economy import ledger as LED
from shibuya.economy import stage2 as S2
from shibuya.foundation.ports.ledger import LedgerBundle
from shibuya.world.model.assets import hash_free_cat_code
from shibuya.world.model.state import World

__all__ = [
    "WALLET_DOMAIN", "store_capital_array", "store_capital_report", "household_wallets", "build_ledger_bundle",
    "write_census_files", "DAILY_CENSUS_FILENAME", "MONTHLY_MER_FILENAME", "MONTHLY_MER_SECTORS_FILENAME",
]


#: 初期財布の乱数ドメイン(``core.rng`` の Philox・manifest のドメイン表に載る)。
WALLET_DOMAIN: Final[str] = "wallet.initial"


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
    # 第 2 期 2-1: 経済の段階 2 のランは、雇用主の口を W6 の組織の数にする(賃金=権利台帳の雇用の行の組織 → 世帯)。
    # 生ログの輪の係数も段階 2 の値(K17 と同じ規則=実測の 1.5 倍以上・economy.stage2)。
    # 〔第 2 期 2-4 V4〕既定は on=雇用主の口が W6 の組織の数・輪の係数 16.0 行/体/日(予算の宣言 §3)。
    # 〔第347 止めた切替口の削除〕切替口 off(2-1 までのまま=1 口・6.5 行/体/日)は消した=旧値の再現は安定版のタグ。
    # 段階 2 の外の台帳(1-9 の試験が差し込む HEAD の台帳の写し・試験の中だけの束)は、この 2 つの型を差し替えて作る。
    n_emp = LED.load_employers(world_dir).n if world_dir is not None else 1
    rate = S2.STAGE2_TRANSFERS_PER_AGENT_PER_DAY
    led = (
        Ledger(n_agents, world.n_poi, n_emp, rows_per_agent_day=rate)
        if wallets is None
        else _HouseholdWalletLedger(n_agents, world.n_poi, wallets, n_emp, rows_per_agent_day=rate)
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
    from shibuya.world.laws import switch_rate as _RRC  # 〔11-01 段 2 の 4・検収 M1〕腕 off は店の廃棄の帯を非該当に

    # 〔第347 止めた切替口の削除〕ランの腕はいつも既定 off(切替口 --rate-rules は消した)=ここは常に偽(帯は非該当)。旧道は部品の
    # 口(試験の中だけ)で回すランだけで、その月次 MER は試験がそのランの実行器の腕から作る(記録 switch-removal-347 §11 の L4)
    mer = CS.monthly_mer(ledger, goods, month=0, days=1, waste_band_applies=_RRC.is_legacy())
    p_mer = CS.write_monthly_mer(mer, d / MONTHLY_MER_FILENAME)
    p_sectors = CS.write_monthly_mer_sectors(mer, d / MONTHLY_MER_SECTORS_FILENAME)
    return (p_daily.as_posix(), p_mer.as_posix(), p_sectors.as_posix())
