"""economy.census — 日次(軽量)センサスと月次 MER・ゲート判定(§2.4)。

正典(境界・経済設計書 §2.4)
- 「**月次**: EVE Online型経済レポート(MER)形式の**固定表** = 科目別 faucet・sink・
  貨幣供給量・残差・退蔵残高。」
- 「**日次(軽量)**: 残差・貨幣供給量のみ。」
- 「残差>閾値・純資産≠実物資産は**ゲート失敗**(較正・holdout照合に使わない)。」
- 世界過程設計書 §7.1: 物側の日次 = SKU 別収支(棚卸差異)・月次 = 廃棄 sink の t/日 band。

日次行は「軽量」の指示どおり**残差・貨幣供給量**を必須とし、ゲート判定に要る最小限
(検算②の成否・棚卸差異・廃棄質量)を足した固定列で出す。列は固定
(``DAILY_COLUMNS``)——後から列が増えると Parquet の追記が壊れるため。

**T3(冗長方程式)の毎期検算**(D-85 (a)・ユーザー決定 2026-09-17)
    設計書 §2.3 の空欄 T3 = 「冗長方程式を**検算値**として毎期assert」。全規模で毎期走って
    いたのは検算②(Σ純資産=Σ実物資産)だけで、これは集計の恒等式=部門間で誤差が相殺すると
    通ってしまう。そこで**月次センサスの時点**(``monthly_mer`` が呼ばれる時点)で検算①の
    3検査を実データに対して走らせ(``checks.t3_check``)、``t3_ok`` を月次 MER の戻りと
    run manifest に載せる。**検査が増えるだけ**で世界は 1 バイトも変わらない。

    月次 MER の**固定表 parquet は変えない**(§2.4「固定表は列も行順もバイトも変えない」)
    ——``t3_ok`` / ``t3`` は ``monthly_mer()`` の戻り(辞書)と run manifest に出る。

逐次ループ宣言(P4)
- ``daily_census``: 科目数(15)ぶんの辞書組み立て。
- ``monthly_mer``: 日数 × 科目数。個体数には比例しない。
- ``monthly_t3``: ``checks.t3_check`` = 部門×科目(90)+ 窓を畳む日数ぶん。個体数に比例しない。
- ``monthly_mer`` の**部門軸**(第204・D-76 (a)): 取引フロー行列の**非零要素**ぶん
  (上限は 部門×部門×科目 = 6×6×15 = 540)。個体数にも tick 数にも比例しない。

**締めた日を評価する**(2026-09-08・層2レビュー指摘の固定)
    ``engine.run`` は ``LedgerBundle.end_of_day`` で日を畳んでから日次センサスを回す。
    畳むと取引フロー行列も当日の廃棄も 0 に戻るので、締め後に「現在値」で行を作ると
    faucet/sink/廃棄が全部 0 の**空虚な行**になり、ゲートが素通りしていた。``day`` に
    畳んだ日を渡せば、台帳の ``close_for(day)`` から締め(``DayClose`` / 締め辞書)を
    自動で引いて**締めた日の実数**で行とゲートを作る(明示の ``close`` / ``goods_close``
    が優先)。畳んでいない日を渡したときは従来どおり当日ぶんの現在値。

expedient(本モジュール分)
- 日次行に検算②の成否と廃棄質量を足したこと(設計書の「残差・貨幣供給量のみ」より広い)。
  ゲートを日次で回すのに必要なため。狭めたい場合は ``light=True`` で 2 列に落とせる。
- Parquet の圧縮は zstd(実装計画書 §5 の「日次 Parquet(zstd)」に合わせた)。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

import numpy as np

from shibuya.economy import checks as CK
from shibuya.economy.accounts import (
    ACCOUNT_NAMES,
    SECTOR_NAMES,
    AccountCode,
    FlowKind,
    Sector,
    flow_kind,
)

__all__ = [
    "DAILY_COLUMNS",
    "LIGHT_COLUMNS",
    "SECTORS",
    "FAUCET_LABEL",
    "SINK_LABEL",
    "OTHER_SECTOR",
    "SECTOR_FLOW_COLUMNS",
    "MONTH_DAYS",
    "CensusGate",
    "daily_census",
    "write_daily_census",
    "monthly_mer",
    "write_monthly_mer",
    "flow_row_kind",
    "write_monthly_mer_sectors",
    "census_gate",
    "is_month_end",
    "monthly_t3",
    "monthly_census_t3",
]

#: 日次(軽量)の必須2列(§2.4「日次(軽量): 残差・貨幣供給量のみ」)。
LIGHT_COLUMNS: Final[tuple[str, ...]] = ("residual", "money_supply")

#: 日次センサスの固定列。
DAILY_COLUMNS: Final[tuple[str, ...]] = (
    "day",
    "residual",  # 残差科目[円]
    "money_supply",  # 貨幣供給量 M[円]
    "faucet_total",  # faucet 合計[円]
    "sink_total",  # sink 合計[円]
    "n_transfers",
    "hoard_entities",
    "hoard_amount",
    "net_worth_ok",  # 検算②
    "flow_ok",  # 検算①
    "residual_ok",
    "ex_nihilo_ok",
    "goods_residual_units",  # 棚卸差異[個]
    "goods_balanced",  # 物の検算①
    "waste_g",  # その日の廃棄搬出[g]
    "shelf_units",  # 棚在庫[個]
    "gate_ok",
)

# --------------------------------------------------------------------- 部門軸(D-76 (a))
#: 月次 MER の**部門軸**に使う部門名(第204・D-76 (a))。
#:
#: **どの属性から引いたか**: 新しい分類は作っていない——取引フロー行列
#: ``Ledger.flow`` の軸 0/1 が ``accounts.Sector``(境界・経済設計書 §2.1 の 6 部門)
#: そのもので、名前は ``accounts.SECTOR_NAMES`` をそのまま使う。台帳の主体は生成時に
#: この 6 部門のどれかに属し(``Ledger.sizes``)、``transfer`` は ``EntityRef(sector, idx)``
#: を要求するので、**払い手/受け手の部門は台帳が既に持っている属性**である。
#: 「来街者」は独立の部門ではない(``Sector.HOUSEHOLD`` = 住民+来街者の財布)ので
#: 部門としては立てない。軸の値が 6 部門の外に出た場合だけ ``OTHER_SECTOR``。
SECTORS: Final[tuple[str, ...]] = SECTOR_NAMES

#: faucet の払い手・sink の受け手に立てる**擬似部門**(実在の部門ではない=境界の印)。
#: どの行が faucet / sink かは ``accounts.flow_kind`` が付けている印をそのまま使う
#: (faucet ⟺ 払い手が外界・sink ⟺ 受け手が外界、または税/逸脱比例コストの政府受け)。
#: 擬似部門に置き換えるのは**境界を部門の外へ出す**ためで、こうすると
#: ``Σ_部門 net = faucet 合計 − sink 合計`` が成り立つ(外界を部門に残すと恒等的に 0)。
FAUCET_LABEL: Final[str] = "faucet"
SINK_LABEL: Final[str] = "sink"
#: 6 部門のどれでもない軸値(通常は発生しない)。
OTHER_SECTOR: Final[str] = "other"

#: ``monthly_mer_sectors.parquet`` の固定列(英語 snake_case・部門名/科目名は日本語)。
SECTOR_FLOW_COLUMNS: Final[tuple[str, ...]] = (
    "month",
    "kind",  # faucet / sink / internal / book / measure
    "from_sector",  # 払い手の部門名(faucet は "faucet")
    "to_sector",  # 受け手の部門名(sink は "sink")
    "account",  # 科目名(``ACCOUNT_NAMES``)
    "amount",  # 円
)


def _sector_name(index: int) -> str:
    """部門軸の値 → 部門名(6 部門の外は ``OTHER_SECTOR``・新しい分類は作らない)。"""
    i = int(index)
    return SECTORS[i] if 0 <= i < len(Sector) else OTHER_SECTOR


def flow_row_kind(from_sector: str, to_sector: str, account: str) -> str:
    """部門軸の 1 行 → ``FlowKind`` の小文字名(``faucet`` / ``sink`` / ``internal`` …)。

    区分は**二重管理しない**: 擬似部門の印(``FAUCET_LABEL`` / ``SINK_LABEL``)が付いて
    いればそれが答えで、付いていない行は実在の部門対なので ``accounts.flow_kind``
    にそのまま尋ねる。行だけから区分を復元できる = parquet を読んだ側も同じ答えになる。
    """
    if from_sector == FAUCET_LABEL:
        return FlowKind.FAUCET.name.lower()
    if to_sector == SINK_LABEL:
        return FlowKind.SINK.name.lower()
    if from_sector not in SECTORS or to_sector not in SECTORS or account not in ACCOUNT_NAMES:
        return FlowKind.INTERNAL.name.lower()  # OTHER_SECTOR 行(通常は発生しない)
    return flow_kind(
        ACCOUNT_NAMES.index(account),
        SECTORS.index(from_sector),
        SECTORS.index(to_sector),
    ).name.lower()


@dataclass(frozen=True)
class CensusGate:
    """ゲート判定(§2.4「ゲート失敗=較正・holdout照合に使わない」)。"""

    day: int
    ok: bool
    reasons: tuple[str, ...]

    def as_text(self) -> str:
        head = f"[census gate day={self.day}] {'PASS' if self.ok else 'FAIL'}"
        return head if self.ok else head + " / " + " ; ".join(self.reasons)


def _close_for(ledger, day: int | None):
    """``day`` が**既に畳まれた日**ならその締めを返す(そうでなければ ``None``)。

    層2レビュー指摘の固定: ``engine.run`` は ``end_of_day`` で日を畳んでから日次センサスを
    回す。締めると取引フロー行列も当日の廃棄も 0 に戻るので、締め後に「現在値」を読むと
    faucet/sink/廃棄が全部 0 の**空虚な行**になり、ゲートが素通りする。台帳が
    ``close_for(day)`` を持つなら、その日の締め(``DayClose`` / 締め辞書)を使う。
    """
    if ledger is None or day is None:
        return None
    fn = getattr(ledger, "close_for", None)
    return None if fn is None else fn(int(day))


def daily_census(
    ledger,
    goods=None,
    close=None,
    day: int | None = None,
    *,
    goods_close=None,
    light: bool = False,
) -> dict[str, Any]:
    """日次(軽量)センサスの1行。

    Args:
        ledger: 金の台帳。
        goods: 物の台帳(``None`` 可)。
        close: ``Ledger.on_day_end`` の戻り(``DayClose``)。``None`` かつ ``day`` が
            **その台帳が直近に畳んだ日**なら、締めを台帳から自動で引く
            (``Ledger.close_for``)。どちらでもなければ当日ぶんの現在値。
        day: 行の日付(``None`` なら台帳の現在日)。
        goods_close: ``GoodsLedger.on_day_end`` の戻り(同上・自動で引ける)。
        light: True なら §2.4 の「残差・貨幣供給量のみ」の2列に落とす。

    Returns:
        ``DAILY_COLUMNS`` を全て含む辞書(``light`` なら ``LIGHT_COLUMNS`` のみ)。
    """
    if close is None:
        close = _close_for(ledger, day)
    if goods_close is None:
        goods_close = _close_for(goods, day)
    rep = CK.check_all(ledger, goods, close)
    fs = rep.faucet_sink
    faucet = int(sum(fs.get(FlowKind.FAUCET.name, {}).values()))
    sink = int(sum(fs.get(FlowKind.SINK.name, {}).values()))
    d = int(ledger.day if day is None else day)
    if light:
        return {"residual": rep.residual_amount, "money_supply": int(ledger.money_supply())}

    if goods_close is not None:
        # 締めた日の実数(締めた瞬間に凍らせた値)。
        goods_residual = int(goods_close["residual_units"])
        goods_balanced = bool(goods_close["sku_balanced"])
        waste_g = float(goods_close["waste_g"])
        shelf_units = int(goods_close["shelf_units"])
    elif goods is not None:
        g_bal = goods.sku_balance()
        goods_residual = int(np.abs(g_bal["residual"]).sum())
        goods_balanced = bool((g_bal["diff"] == 0).all())
        waste_g = float(goods.day_waste_g)
        shelf_units = int(goods.aggregate_stock().sum())
    else:
        goods_residual, goods_balanced, waste_g, shelf_units = 0, True, 0.0, 0

    gate = census_gate(rep, goods, day=d, goods_close=goods_close)
    return {
        "day": d,
        "residual": int(rep.residual_amount),
        "money_supply": int(ledger.money_supply()),
        "faucet_total": faucet,
        "sink_total": sink,
        "n_transfers": int(ledger.n_transfers),
        "hoard_entities": int(rep.hoard.n_entities),
        "hoard_amount": int(rep.hoard.amount),
        "net_worth_ok": bool(rep.net_worth.ok),
        "flow_ok": bool(rep.flow.ok),
        "residual_ok": bool(rep.residual_ok),
        "ex_nihilo_ok": bool(rep.ex_nihilo_ok),
        "goods_residual_units": goods_residual,
        "goods_balanced": goods_balanced,
        "waste_g": waste_g,
        "shelf_units": shelf_units,
        "gate_ok": bool(gate.ok),
    }


def census_gate(
    report: "CK.CheckReport", goods=None, day: int = 0, *, goods_close=None
) -> CensusGate:
    """ゲート判定(残差超・検算②不成立・棚卸差異超で失敗)。

    Args:
        goods_close: ``GoodsLedger.on_day_end`` の戻り。渡すと**締めた日の**棚卸差異・
            検算①でゲートする(締め後の現在値は 0 に戻っているので素通りしてしまう)。
    """
    reasons = list(report.reasons())
    if goods_close is not None:
        if not bool(goods_close["stocktake_ok"]):
            ratio = float(goods_close["stocktake_ratio"])
            reasons.append(f"棚卸差異が閾値超(流量比 {ratio:.4f})")
        if not bool(goods_close["sku_balanced"]):
            reasons.append("物の検算①: 期首+流入−流出+残差 ≠ 期末")
    elif goods is not None:
        ok, ratio = goods.stocktake_gate()
        if not ok:
            reasons.append(f"棚卸差異が閾値超(流量比 {ratio:.4f})")
        if not goods.sku_balanced():
            reasons.append("物の検算①: 期首+流入−流出+残差 ≠ 期末")
    return CensusGate(day=int(day), ok=not reasons, reasons=tuple(reasons))


def write_daily_census(rows: Sequence[Mapping[str, Any]], path: str | Path) -> Path:
    """日次センサスを Parquet(zstd)で書く。列は ``DAILY_COLUMNS`` 固定。"""
    import pyarrow as pa
    import pyarrow.parquet as pq

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cols = {c: [r.get(c) for r in rows] for c in DAILY_COLUMNS}
    table = pa.table(cols)
    pq.write_table(table, p, compression="zstd")
    return p


def _sector_axis(
    total: np.ndarray,
) -> tuple[dict[str, dict[str, int]], list[list[Any]]]:
    """取引フロー行列 → 部門別収支 ``per_sector`` と長い表 ``flows``(D-76 (a))。

    逐次ループ宣言(P4): **非零要素**ぶん(上限 6×6×15 = 540)。個体数・tick 数に比例しない。
    走査順は ``np.argwhere`` = 軸の昇順(部門, 部門, 科目)なので **決定論**。
    """
    per: dict[str, dict[str, int]] = {
        name: {"received": 0, "paid": 0, "net": 0} for name in SECTORS
    }
    rows: dict[tuple[str, str, str], int] = {}
    for a, b, c in np.argwhere(np.asarray(total) != 0):
        amount = int(total[a, b, c])
        kind = flow_kind(int(c), int(a), int(b))
        src = FAUCET_LABEL if kind is FlowKind.FAUCET else _sector_name(int(a))
        dst = SINK_LABEL if kind is FlowKind.SINK else _sector_name(int(b))
        key = (src, dst, ACCOUNT_NAMES[int(c)])
        rows[key] = rows.get(key, 0) + amount
        if src in per:
            per[src]["paid"] += amount
        if dst in per:
            per[dst]["received"] += amount
    for v in per.values():
        v["net"] = v["received"] - v["paid"]
    return per, [[src, dst, name, amt] for (src, dst, name), amt in rows.items()]


# --------------------------------------------------------------- T3(D-85 (a))
#: 月次センサスの「1 か月」= 台帳が畳んだ日数(**expedient**: 設計書は「月次」としか
#: 書いていない。30 日は ``checks.HOARD_DAYS`` と同じ据え置きの区切り)。
#: 判定は ``Ledger.flow_daily`` の長さで見る——暦日ではなく**台帳が畳んだ日数**なので、
#: 何日目から始めたランでも「30 日ぶん畳んだところ」で月次センサスが立つ。
MONTH_DAYS: Final[int] = 30


def is_month_end(n_days_folded: int) -> bool:
    """畳んだ日数が 1 か月ぶんの区切りに達したか(0 日=まだ月次センサスは走らない)。"""
    n = int(n_days_folded)
    return n > 0 and n % MONTH_DAYS == 0


def monthly_t3(ledger, day: int | None = None) -> dict[str, Any]:
    """T3(冗長方程式)の検算を走らせて**記録できる形**で返す(D-85 (a))。

    中身は ``checks.t3_check``(= 検算①の3検査を期首→現在の窓で走らせたもの)。
    ``day`` は行に添える日付(``None`` なら台帳の現在日)。
    """
    rep = CK.t3_check(ledger)
    out = rep.as_dict()
    out["day"] = int(getattr(ledger, "day", 0) if day is None else day)
    return out


def monthly_census_t3(ledger, day: int) -> dict[str, Any] | None:
    """**月次センサスが立つ日だけ** T3 を走らせる(engine への注入口・D-85 (a))。

    Returns:
        月末(畳んだ日数が ``MONTH_DAYS`` の倍数)なら ``monthly_t3`` の辞書。
        そうでなければ ``None`` = **未実行**(1 日ランの manifest は ``t3_ok=None``)。
    """
    if not is_month_end(len(getattr(ledger, "flow_daily", ()) or ())):
        return None
    return monthly_t3(ledger, day)


def monthly_mer(
    ledger, goods=None, *, month: int = 0, days: int | None = None
) -> dict[str, Any]:
    """月次 MER(EVE Online 型の**固定表**)。

    固定表の行:
      1. 科目別 faucet(円)
      2. 科目別 sink(円)
      3. 貨幣供給量 M(期末)
      4. 残差
      5. 退蔵残高
      6.(物)廃棄 sink の t/日 と W1 band 判定
      7. **T3**(冗長方程式の検算・D-85 (a)): ``t3_ok`` と内訳 ``t3``(3検査の合否と
         残差の大きさ)。**固定表 parquet の列は増やさない**(§2.4)。

    ``ledger.flow_daily`` の**全期間**を合算する(日次で畳んだ集約行=D-R2-6 の運用)。

    **部門軸**(第204・D-76 (a)。固定表の既存キーは 1 つも変えない):
      - ``per_sector``: ``{部門名: {"received": 円, "paid": 円, "net": 円}}``。
        6 部門を常に全部載せる(0 の部門も落とさない=表の形が動かない)。
      - ``flows``: ``[[from_sector, to_sector, account, amount], ...]`` の長い表。
        faucet の払い手は ``"faucet"``・sink の受け手は ``"sink"``(``SECTORS`` の外)。
      検算(``tests/economy/test_census.py``):
        ① 区分ごとの ``flows`` 合計 = ``faucet`` / ``sink`` / ``internal`` の科目別合計
        ② ``Σ_部門 net = faucet_total − sink_total``
    """
    daily = list(ledger.flow_daily)
    n_days = len(daily) if days is None else int(days)
    total = (
        np.sum(np.stack(daily[-n_days:]), axis=0)
        if daily
        else np.zeros_like(np.asarray(ledger.flow))
    )
    fs = CK.faucet_sink_totals(ledger, total)
    faucet = {k: int(v) for k, v in fs.get(FlowKind.FAUCET.name, {}).items()}
    sink = {k: int(v) for k, v in fs.get(FlowKind.SINK.name, {}).items()}
    internal = {k: int(v) for k, v in fs.get(FlowKind.INTERNAL.name, {}).items()}
    hoard = CK.hoard_report(ledger)
    out: dict[str, Any] = {
        "month": int(month),
        "days": int(max(1, n_days)),
        "faucet": faucet,
        "sink": sink,
        "internal": internal,
        "faucet_total": int(sum(faucet.values())),
        "sink_total": int(sum(sink.values())),
        "money_supply": int(ledger.money_supply()),
        "residual": int(total[:, :, int(AccountCode.RESIDUAL)].sum()),
        "hoard_entities": int(hoard.n_entities),
        "hoard_amount": int(hoard.amount),
        "per_account": {
            ACCOUNT_NAMES[int(c)]: int(total[:, :, int(c)].sum()) for c in AccountCode
        },
    }
    out["per_sector"], out["flows"] = _sector_axis(total)
    # T3(D-85 (a)): 月次センサスの時点で検算①の3検査を実データに対して走らせる。
    # **固定表 parquet には出さない**(§2.4「固定表は列も行順もバイトも変えない」)。
    t3 = CK.t3_check(ledger)
    out["t3_ok"] = bool(t3.ok)
    out["t3"] = t3.as_dict()
    if goods is not None:
        band = goods.waste_band(days=max(1, n_days))
        out["waste_tonnes"] = band.tonnes
        out["waste_tonnes_per_day"] = band.tonnes_per_day
        out["waste_band_ok"] = band.ok
        out["waste_band"] = (band.low, band.high)
    return out


def write_monthly_mer(report: Mapping[str, Any], path: str | Path) -> Path:
    """月次 MER を Parquet(zstd)で書く(科目別の縦持ち + 総量列)。"""
    import pyarrow as pa
    import pyarrow.parquet as pq

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    kinds: list[str] = []
    amounts: list[int] = []
    for kind in ("faucet", "sink", "internal"):
        for name, amt in sorted(report.get(kind, {}).items()):
            names.append(name)
            kinds.append(kind)
            amounts.append(int(amt))
    table = pa.table(
        {
            "month": [int(report.get("month", 0))] * len(names),
            "kind": kinds,
            "account": names,
            "amount": amounts,
            "money_supply": [int(report.get("money_supply", 0))] * len(names),
            "residual": [int(report.get("residual", 0))] * len(names),
            "hoard_amount": [int(report.get("hoard_amount", 0))] * len(names),
        }
    )
    pq.write_table(table, p, compression="zstd")
    return p


def write_monthly_mer_sectors(report: Mapping[str, Any], path: str | Path) -> Path:
    """月次 MER の**部門軸**(``flows`` の長い表)を Parquet(zstd)で書く(D-76 (a))。

    既存の固定表 ``monthly_mer.parquet`` は**一切変えない**(列も行順もバイトも不変)。
    部門軸はこの別ファイル ``monthly_mer_sectors.parquet`` に出す。列は
    ``SECTOR_FLOW_COLUMNS`` 固定。``kind`` は行から ``flow_row_kind`` で復元した値
    (区分の二重管理を作らない)。
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = [list(r) for r in report.get("flows", ()) or ()]
    month = int(report.get("month", 0))
    schema = pa.schema(
        [
            ("month", pa.int64()),
            ("kind", pa.string()),
            ("from_sector", pa.string()),
            ("to_sector", pa.string()),
            ("account", pa.string()),
            ("amount", pa.int64()),
        ]
    )
    assert [f.name for f in schema] == list(SECTOR_FLOW_COLUMNS)
    table = pa.table(
        {
            "month": [month] * len(rows),
            "kind": [flow_row_kind(str(r[0]), str(r[1]), str(r[2])) for r in rows],
            "from_sector": [str(r[0]) for r in rows],
            "to_sector": [str(r[1]) for r in rows],
            "account": [str(r[2]) for r in rows],
            "amount": [int(r[3]) for r in rows],
        },
        schema=schema,
    )
    pq.write_table(table, p, compression="zstd")
    return p
