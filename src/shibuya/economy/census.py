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

逐次ループ宣言(P4)
- ``daily_census``: 科目数(15)ぶんの辞書組み立て。
- ``monthly_mer``: 日数 × 科目数。個体数には比例しない。

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
from shibuya.economy.accounts import ACCOUNT_NAMES, AccountCode, FlowKind

__all__ = [
    "DAILY_COLUMNS",
    "LIGHT_COLUMNS",
    "CensusGate",
    "daily_census",
    "write_daily_census",
    "monthly_mer",
    "write_monthly_mer",
    "census_gate",
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


@dataclass(frozen=True)
class CensusGate:
    """ゲート判定(§2.4「ゲート失敗=較正・holdout照合に使わない」)。"""

    day: int
    ok: bool
    reasons: tuple[str, ...]

    def as_text(self) -> str:
        head = f"[census gate day={self.day}] {'PASS' if self.ok else 'FAIL'}"
        return head if self.ok else head + " / " + " ; ".join(self.reasons)


def daily_census(
    ledger,
    goods=None,
    close=None,
    day: int | None = None,
    *,
    light: bool = False,
) -> dict[str, Any]:
    """日次(軽量)センサスの1行。

    Args:
        ledger: 金の台帳。
        goods: 物の台帳(``None`` 可)。
        close: ``Ledger.on_day_end`` の戻り(``None`` なら当日ぶんの現在値)。
        day: 行の日付(``None`` なら台帳の現在日)。
        light: True なら §2.4 の「残差・貨幣供給量のみ」の2列に落とす。

    Returns:
        ``DAILY_COLUMNS`` を全て含む辞書(``light`` なら ``LIGHT_COLUMNS`` のみ)。
    """
    rep = CK.check_all(ledger, goods, close)
    fs = rep.faucet_sink
    faucet = int(sum(fs.get(FlowKind.FAUCET.name, {}).values()))
    sink = int(sum(fs.get(FlowKind.SINK.name, {}).values()))
    d = int(ledger.day if day is None else day)
    if light:
        return {"residual": rep.residual_amount, "money_supply": int(ledger.money_supply())}

    if goods is not None:
        g_bal = goods.sku_balance()
        goods_residual = int(np.abs(g_bal["residual"]).sum())
        goods_balanced = bool((g_bal["diff"] == 0).all())
        waste_g = float(goods.day_waste_g)
        shelf_units = int(goods.aggregate_stock().sum())
    else:
        goods_residual, goods_balanced, waste_g, shelf_units = 0, True, 0.0, 0

    gate = census_gate(rep, goods, day=d)
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


def census_gate(report: "CK.CheckReport", goods=None, day: int = 0) -> CensusGate:
    """ゲート判定(残差超・検算②不成立・棚卸差異超で失敗)。"""
    reasons = list(report.reasons())
    if goods is not None:
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

    ``ledger.flow_daily`` の**全期間**を合算する(日次で畳んだ集約行=D-R2-6 の運用)。
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
