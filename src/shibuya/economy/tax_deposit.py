"""economy.tax_deposit — 店の預かり消費税(第 4 期 4-2・Q1=PENDING 仮-40・R-118 §5 ①)。

現実の手順: 店は売上の中に消費税を預かり、課税期間の後に申告して期限までに国へ納める(消費税法 45 条・租特法 86 条の 4=
R-106 §3-1)。4-2 の前は売った時点で店 → 政府へ移していた(``Process("register")``)。本モジュールは、レジの税を店ごとの
預かり金の口に積み(お金は店の現金のまま=店はその間も使える)、申告の期限の日の締めに店 → 政府(科目「税」・原因
``Process("register")``)へ移す。店の現金が足りない分は移せない=預かり金に残り、次の日の締めにまた移す(滞納の数を計器に・
延滞税は答申に無い=入れていない)。

状態(状態台帳の腕の行 ``TXD``=軸 1 behavior=期限の納付の額を決める・軸 2 required=作り直せない): ``held``=課税期間の年 →
店ごとの預かり額(int64)・``totals``=積んだ額・移した額・移せなかった回数の累計。腕 ``SHIBUYA_RULES_42=off`` のランは持ち主が
無い(``MoneyStage2.tax_deposit`` が ``None``)=2 つのハッシュと状態のファイルは腕を足す前と同じバイト。

保存則(``economy.checks.tax_deposit_check``): 積んだ額の累計 − 移した額の累計 = 預かり額の合計(残差 0)。預かり金は店の
現金の中にある=部門の残高の検算(faucet − sink = ΔM)はそのまま(移すときは登録の sink「消費税の納付」)。

逐次ループ宣言: :meth:`TaxDeposit.collect` は配列演算。:meth:`TaxDeposit.remit_due` は預かりのある課税期間の数(1〜2)ぶん。
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Final

import numpy as np

from shibuya.economy import taxes as _TX
from shibuya.economy.accounts import AccountCode, Sector
from shibuya.engine.ledger_api import TransferStatus

__all__ = ["TaxDeposit", "LEDGER_ARM"]

#: 状態台帳の腕の行 ``TXD`` の腕の名(``engine.state_ledger`` の行の ``arm`` と同じ)。
LEDGER_ARM: Final[str] = "rules-42"


class TaxDeposit:
    """店ごとの預かり消費税(課税期間の年ごと)。書くのは :meth:`collect` と :meth:`remit_due` だけ。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

    def __init__(self, n_stores: int) -> None:
        #: 店の数(帳簿の店舗の口の数)。
        self.n = int(n_stores)
        #: 課税期間の年 → 店ごとの預かり額[円](int64・長さ n)。
        self.held: dict[int, np.ndarray] = {}
        #: 累計(積んだ額・移した額・移した行・移せなかった行と額)。
        self.totals: dict[str, int] = {"collected": 0, "remitted": 0, "remit_rows": 0, "unpaid_rows": 0,
                                       "unpaid_amount": 0}

    def collect(self, stores: np.ndarray, tax: np.ndarray, period_year: int) -> int:
        """レジの税を店の預かり金に積む(戻り=積んだ額の合計)。"""
        s = np.asarray(stores, dtype=np.int64).ravel()
        t = np.asarray(tax, dtype=np.int64).ravel()
        if s.size == 0:
            return 0
        if s.min() < 0 or s.max() >= self.n:
            raise IndexError(f"店の番号が預かり金の口の外(店の数 {self.n})")
        y = int(period_year)
        arr = self.held.get(y)
        if arr is None:
            arr = np.zeros(self.n, dtype=np.int64)
            self.held[y] = arr
        np.add.at(arr, s, t)
        amt = int(t.sum())
        self.totals["collected"] = int(self.totals["collected"]) + amt
        return amt

    def held_total(self) -> int:
        """預かり額の合計[円](課税期間をまたいだ合計)。"""
        return int(sum(int(v.sum()) for v in self.held.values()))

    def remit_due(self, ledger: Any, today: _dt.date, step: int, *, cause: Any = None) -> dict[str, int]:
        """期限(:func:`economy.taxes.filing_deadline`)が今日以前の課税期間の預かり額を店 → 政府へ移す。"""
        out = {"remit_rows": 0, "remitted": 0, "unpaid_rows": 0, "unpaid_amount": 0}
        for year in sorted(self.held):  # 逐次ループ宣言: 預かりのある課税期間の数(1〜2)
            due, _src = _TX.filing_deadline(year)
            if due is None or today < due:
                continue
            arr = self.held[year]
            who = np.flatnonzero(arr > 0)
            if who.size == 0:
                del self.held[year]
                continue
            amt = arr[who]
            st = np.asarray(ledger.transfer_many(int(Sector.STORE), who, int(Sector.GOVERNMENT),
                                                 np.zeros(who.size, dtype=np.int64), amt, int(AccountCode.TAX),
                                                 int(step), cause=cause))
            ok = st == int(TransferStatus.OK)
            arr[who[ok]] = 0
            out["remit_rows"] += int(ok.sum())
            out["remitted"] += int(amt[ok].sum())
            out["unpaid_rows"] += int((~ok).sum())
            out["unpaid_amount"] += int(amt[~ok].sum())
            if not arr.any():
                del self.held[year]
        for k, v in out.items():
            self.totals[k] = int(self.totals[k]) + int(v)
        return out

    def record(self) -> dict[str, Any]:
        """manifest と日次の記録の預かり消費税(累計・残高・課税期間ごとの残高と期限)。"""
        by = {}
        for year in sorted(self.held):  # 逐次: 課税期間の数
            due, src = _TX.filing_deadline(year)
            by[str(year)] = {"held": int(self.held[year].sum()), "stores": int((self.held[year] > 0).sum()),
                             "due": None if due is None else due.isoformat(), "rule": src}
        return {**{k: int(v) for k, v in self.totals.items()}, "held": self.held_total(), "periods": by}
