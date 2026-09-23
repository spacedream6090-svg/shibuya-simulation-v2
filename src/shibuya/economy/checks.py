"""economy.checks — **検算2本**(Caiani 2016)・残差ゲート・退蔵計上・ex nihilo 検査。

正典(境界・経済設計書 §2.3-2.4)
- 「**検算2本**: ①四重記入=取引フロー行列の**行和・列和が0**(開発時テスト)
  ②**全主体の純資産合計=実物資産(在庫+固定資産)の価額**が毎期成立
  (**主検算・O(N)総和・全規模**)」。
- 「残差>閾値・純資産≠実物資産は**ゲート失敗**(較正・holdout照合に使わない)」(§2.4)。
- 「pytest 8本: transfer保存・列挙外科目拒否・行和列和0・純資産=実物資産・
  参入資本のtransfer由来・残差閾値・退蔵項計上・faucet/sink科目別集計」(§2.3)。

**検算②の恒等式(設計書の式を実装形へ書き下したもの)**
    純資産(主体) = 現金 + 預金 + 在庫 + 固定資産 − 借入
    Σ純資産 = Σ(在庫+固定資産)  ⟺  **Σ(現金 + 預金 − 借入) = 0**(全部門・外界を含む)
    つまり②は「金融資産と金融負債が全部門で相殺するか」の検査であり、在庫の評価額には
    依存しない(左辺と右辺の両方に同額で入るため)。**外界(RoW)を勘定に入れることが本質**:
    faucet で bbox 内へ入った現金は外界の負の現金として残るので、合計は 0 のまま動かない。
    残高への直接代入(単一API迂回)は Σ≠0 として必ずここに出る。

**検算①の実装形**
    行(科目)方向: 科目ごとに Σ部門の符号つき流入 = 0 —— transfer が2主体に同額を
    立てることの検査(構造上ほぼ自明だが、片脚だけ書く実装事故を捕まえる)。
    列(部門)方向: 部門ごとに Σ科目の符号つき流入 = **その日の現金増減** —— これが
    「残高の直接代入」を捕まえる本体。預金脚(預金純増)は別に
    Δ預金 − Δ借入 = 0 で照合する(四重記入の3脚目・4脚目)。

**T3(SFC の冗長方程式・D-85 (a)・ユーザー決定 2026-09-17)**
    設計書 §2.3 の空欄「T3(冗長方程式を実装せず**検算値**として毎期assert)は答申にあるが
    未実装」への対応。検算②(Σ純資産=Σ実物資産)は**集計の恒等式**なので、部門間で誤差が
    相殺すると通ってしまう。T3 は検算①の3検査を**実データに対して**月次センサスの時点で
    走らせる(``t3_check``)。**検算①のロジックは再実装せず** ``flow_matrix_balanced`` を
    そのまま呼ぶ——違うのは**窓**だけ:
      日次の検算① = その日の締め(``DayClose``)/ T3 = **期首(台帳の生成時)から現在まで**
      (``Ledger.cumulative_close``)。窓を期首からにするのは、(i) 途中の月に入った破れが
      その後も残る(1 度でも破れたら以後ずっと FAIL)ためと、(ii) 任意の部分窓で走らせるには
      日ごとの残高増減を保持する必要があり、D-R2-6 の成長宣言(``flow_matrix_daily``)を
      動かしてしまうため。期首窓なら台帳が持つ**定数サイズ**の期首スナップで済む。

逐次ループ宣言(P4): 部門数×科目数(90)ぶんのみ。個体数に比例するのは NumPy 総和。

expedient(本モジュール分)
- 残差の閾値 = 貨幣供給量の 1e-6(設計書は「閾値」としか書いていない)。
- 退蔵の判定日数 = 30 日(家計調査の預貯金純増 177,061円/月 が基準とされるが、
  「何日動かなければ退蔵か」は書かれていない)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final, Mapping

import numpy as np

from shibuya.economy.accounts import (
    ACCOUNT_NAMES,
    ENTRY_CAPITAL_PAYERS,
    SECTOR_NAMES,
    AccountCode,
    BalanceLine,
    FlowKind,
    Sector,
    flow_kind,
)

__all__ = [
    "RESIDUAL_THRESHOLD_RATIO",
    "HOARD_DAYS",
    "FlowCheck",
    "T3Check",
    "NetWorthCheck",
    "HoardReport",
    "CheckReport",
    "flow_matrix_balanced",
    "t3_check",
    "net_worth_equals_real_assets",
    "residual_gate",
    "hoard_report",
    "ex_nihilo_ok",
    "faucet_sink_totals",
    "check_all",
]

#: 残差科目の閾値(貨幣供給量に対する比・expedient)。
RESIDUAL_THRESHOLD_RATIO: Final[float] = 1e-6
#: 退蔵と見なす無変動日数(expedient)。
HOARD_DAYS: Final[int] = 30


@dataclass(frozen=True)
class FlowCheck:
    """検算①(四重記入)の結果。"""

    rows_zero: bool  # 科目ごとに Σ部門 = 0
    cols_match_cash: bool  # 部門ごとに Σ科目 = Δ現金
    deposit_legs_match: bool  # Δ預金 − Δ借入 = 0(預金脚)
    row_residual: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    col_residual: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    #: 預金脚の残差 ``Δ預金 − Δ借入``(部門ごと)。合計が 0 かを見る(T3 の内訳に出す)。
    dep_residual: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))

    @property
    def ok(self) -> bool:
        return self.rows_zero and self.cols_match_cash and self.deposit_legs_match

    def as_text(self) -> str:
        return (
            f"[検算①] 行和(科目)={'0' if self.rows_zero else 'NG'} / "
            f"列和(部門)=Δ現金 {'一致' if self.cols_match_cash else 'NG'} / "
            f"預金脚 {'一致' if self.deposit_legs_match else 'NG'}"
        )


@dataclass(frozen=True)
class T3Check:
    """T3(SFC の冗長方程式)= 検算①の3検査を**実データ**に対して走らせた結果。

    3検査は ``FlowCheck`` と同じもの(``flow_matrix_balanced`` をそのまま呼ぶ)。違うのは
    窓だけで、既定は**期首(台帳の生成時)から現在まで**(``scope="cumulative"``)。
    ``days`` は窓に入っている畳んだ日数(``Ledger.flow_daily`` の長さ)。

    残差は**大きさ**だけ持つ(部門×科目の配列を manifest へ持ち出さないため):
    行残差・列残差は絶対値の最大、預金脚は符号つきの合計。
    """

    ok: bool
    rows_zero: bool
    cols_match_cash: bool
    deposit_legs_match: bool
    row_residual_max: int
    col_residual_max: int
    deposit_residual: int
    days: int
    scope: str = "cumulative"

    def reasons(self) -> tuple[str, ...]:
        out: list[str] = []
        if not self.rows_zero:
            out.append(f"T3: 科目ごとの行和が 0 でない(最大 {self.row_residual_max:,}円)")
        if not self.cols_match_cash:
            out.append(
                "T3: 部門ごとの列和が現金増減と一致しない"
                f"(最大 {self.col_residual_max:,}円・残高の直接代入の疑い)"
            )
        if not self.deposit_legs_match:
            out.append(f"T3: 預金脚(Δ預金−Δ借入)が 0 でない({self.deposit_residual:,}円)")
        return tuple(out)

    def as_dict(self) -> dict[str, Any]:
        """月次 MER / run manifest に載せる形(JSON にできる素の型だけ)。"""
        return {
            "ok": bool(self.ok),
            "rows_zero": bool(self.rows_zero),
            "cols_match_cash": bool(self.cols_match_cash),
            "deposit_legs_match": bool(self.deposit_legs_match),
            "row_residual_max": int(self.row_residual_max),
            "col_residual_max": int(self.col_residual_max),
            "deposit_residual": int(self.deposit_residual),
            "days": int(self.days),
            "scope": str(self.scope),
        }

    def as_text(self) -> str:
        head = f"[T3 {self.scope} {self.days}日] {'PASS' if self.ok else 'FAIL'}"
        return head if self.ok else head + " / " + " ; ".join(self.reasons())


@dataclass(frozen=True)
class NetWorthCheck:
    """検算②(純資産合計 = 実物資産)の結果。"""

    net_worth_total: int
    real_assets_total: int
    financial_net_total: int

    @property
    def ok(self) -> bool:
        return self.net_worth_total == self.real_assets_total and self.financial_net_total == 0

    def as_text(self) -> str:
        return (
            f"[検算②] Σ純資産 {self.net_worth_total:,} = Σ実物資産 {self.real_assets_total:,} "
            f"(Σ金融純資産 {self.financial_net_total:,}) {'OK' if self.ok else 'NG'}"
        )


@dataclass(frozen=True)
class HoardReport:
    """退蔵項(§2.2「使われず溜まる現金/預金=UO教訓の監視点」)。"""

    days: int
    n_entities: int
    amount: int
    by_sector: dict[str, int]

    def as_text(self) -> str:
        return f"[退蔵] {self.days}日以上不動 {self.n_entities:,}主体 / {self.amount:,}円"


@dataclass(frozen=True)
class CheckReport:
    """日次ゲートに使うまとめ。"""

    flow: FlowCheck
    net_worth: NetWorthCheck
    residual_ok: bool
    residual_amount: int
    hoard: HoardReport
    ex_nihilo_ok: bool
    faucet_sink: dict[str, dict[str, int]]

    @property
    def ok(self) -> bool:
        return (
            self.flow.ok and self.net_worth.ok and self.residual_ok and self.ex_nihilo_ok
        )

    def reasons(self) -> tuple[str, ...]:
        out: list[str] = []
        if not self.flow.rows_zero:
            out.append("検算①: 科目ごとの行和が 0 でない")
        if not self.flow.cols_match_cash:
            out.append("検算①: 部門ごとの列和が現金増減と一致しない(残高の直接代入の疑い)")
        if not self.flow.deposit_legs_match:
            out.append("検算①: 預金脚(Δ預金−Δ借入)が 0 でない")
        if not self.net_worth.ok:
            out.append("検算②: Σ純資産 ≠ Σ実物資産(Σ金融純資産 ≠ 0)")
        if not self.residual_ok:
            out.append(f"残差科目 {self.residual_amount:,}円 が閾値超")
        if not self.ex_nihilo_ok:
            out.append("参入資本が許された出所(創業者預金・銀行貸出・外界)以外から来ている")
        return tuple(out)


def flow_matrix_balanced(ledger, close=None) -> FlowCheck:
    """検算①: 四重記入(逐次ループ宣言: 部門×科目=90)。

    Args:
        ledger: ``economy.ledger.Ledger``。
        close: ``DayClose``(``on_day_end`` の戻り)。``None`` なら**当日ぶん**を見る。
    """
    if close is None:
        flow = np.asarray(ledger.flow)
        delta = ledger.financial_delta()
        d_cash, d_dep, d_loan = delta["cash"], delta["deposit"], delta["loan"]
    else:
        flow = np.asarray(close.flow)
        d_cash, d_dep, d_loan = close.d_cash, close.d_deposit, close.d_loan

    signed = ledger.signed_flow(flow)  # (部門, 科目) 受取 − 支払
    row_resid = signed.sum(axis=0)  # 科目ごとの Σ部門
    col_resid = signed.sum(axis=1) - d_cash  # 部門ごとの Σ科目 − Δ現金
    dep_resid = d_dep - d_loan
    return FlowCheck(
        rows_zero=bool((row_resid == 0).all()),
        cols_match_cash=bool((col_resid == 0).all()),
        deposit_legs_match=bool((dep_resid.sum() == 0)),
        row_residual=row_resid,
        col_residual=col_resid,
        dep_residual=np.asarray(dep_resid),
    )


def t3_check(ledger, close=None) -> T3Check:
    """T3: 検算①の3検査を**実データ**で走らせる(D-85 (a)・月次センサスの時点)。

    **検算①を再実装しない**——``flow_matrix_balanced`` をそのまま呼び、窓だけを差し替える。

    Args:
        ledger: ``economy.ledger.Ledger``。
        close: 見る窓(``DayClose`` 形)。``None`` なら台帳の ``cumulative_close()``
            (期首→現在)を使い、それが無い台帳では当日ぶん(従来の検算①と同じ窓)。

    逐次ループ宣言(P4): ``flow_matrix_balanced`` と同じ 部門×科目(90)。窓を畳む総和は
    日数ぶん(``Ledger.cumulative_close``)で、**個体数には比例しない**。
    """
    scope = "cumulative"
    if close is None:
        fn = getattr(ledger, "cumulative_close", None)
        if fn is None:
            scope = "open_day"
        else:
            close = fn()
    else:
        scope = "window"
    fc = flow_matrix_balanced(ledger, close)
    row = np.asarray(fc.row_residual)
    col = np.asarray(fc.col_residual)
    dep = np.asarray(fc.dep_residual)
    return T3Check(
        ok=bool(fc.ok),
        rows_zero=bool(fc.rows_zero),
        cols_match_cash=bool(fc.cols_match_cash),
        deposit_legs_match=bool(fc.deposit_legs_match),
        row_residual_max=int(np.abs(row).max()) if row.size else 0,
        col_residual_max=int(np.abs(col).max()) if col.size else 0,
        deposit_residual=int(dep.sum()) if dep.size else 0,
        days=int(len(getattr(ledger, "flow_daily", ()) or ())),
        scope=scope,
    )


def net_worth_equals_real_assets(ledger, goods=None) -> NetWorthCheck:
    """検算②(主検算・O(N)総和)。``goods`` を渡すと在庫評価額を U-Goods 側から取る。"""
    nw = 0
    real = 0
    fin = 0
    inv_from_goods = None
    if goods is not None:
        inv_from_goods = int(goods.inventory_value().sum())
    for s in Sector:
        cash = int(ledger.balance(BalanceLine.CASH, s).astype(np.int64).sum())
        dep = int(ledger.balance(BalanceLine.DEPOSIT, s).sum())
        inv = int(ledger.balance(BalanceLine.INVENTORY, s).sum())
        fix = int(ledger.balance(BalanceLine.FIXED_ASSET, s).sum())
        loan = int(ledger.balance(BalanceLine.LOAN, s).sum())
        if inv_from_goods is not None and s == Sector.STORE:
            inv = inv_from_goods
        nw += cash + dep + inv + fix - loan
        real += inv + fix
        fin += cash + dep - loan
    return NetWorthCheck(net_worth_total=nw, real_assets_total=real, financial_net_total=fin)


def residual_gate(
    ledger, flow: np.ndarray | None = None, ratio: float = RESIDUAL_THRESHOLD_RATIO
) -> tuple[bool, int]:
    """残差科目のゲート(§2.4「残差>閾値はゲート失敗」)。

    Returns:
        ``(閾値内か, 残差額[円])``。
    """
    f = np.asarray(ledger.flow if flow is None else flow)
    resid = int(f[:, :, int(AccountCode.RESIDUAL)].sum())
    m = max(1, abs(int(ledger.money_supply())))
    return (abs(resid) <= ratio * m, resid)


def hoard_report(ledger, day: int | None = None, days: int = HOARD_DAYS) -> HoardReport:
    """退蔵項の計上: ``days`` 日以上 現金/預金が動いていない主体の残高。"""
    d = ledger.day if day is None else int(day)
    n_ent = 0
    amount = 0
    by_sector: dict[str, int] = {}
    for s in Sector:
        last = ledger.last_change_day(s)
        bal = ledger.balance(BalanceLine.CASH, s).astype(np.int64) + ledger.balance(
            BalanceLine.DEPOSIT, s
        )
        idle = (d - last.astype(np.int64) >= int(days)) & (bal > 0)
        n = int(idle.sum())
        amt = int(bal[idle].sum())
        n_ent += n
        amount += amt
        by_sector[SECTOR_NAMES[int(s)]] = amt
    return HoardReport(days=int(days), n_entities=n_ent, amount=amount, by_sector=by_sector)


def ex_nihilo_ok(ledger) -> bool:
    """参入資本が許された出所のみから来ているか(§2.3 ex nihilo 禁止)。

    生ログの保持窓内 + 日次集約行の両方を見る(集約行は部門対を保っているので判定できる)。
    """
    code = int(AccountCode.ENTRY_CAPITAL)
    allowed = np.zeros(len(Sector), dtype=bool)
    for s in ENTRY_CAPITAL_PAYERS:
        allowed[int(s)] = True
    flows = [np.asarray(ledger.flow)] + [np.asarray(f) for f in ledger.flow_daily]
    for f in flows:
        by_payer = f[:, :, code].sum(axis=1)
        if int(by_payer[~allowed].sum()) != 0:
            return False
    return True


def faucet_sink_totals(ledger, flow: np.ndarray | None = None) -> dict[str, dict[str, int]]:
    """faucet/sink の**科目別**集計(§2.3 pytest 8本目・§2.4 月次 MER の素材)。

    Returns:
        ``{"FAUCET": {科目名: 円}, "SINK": {...}, "INTERNAL": {...}, ...}``。
    """
    f = np.asarray(ledger.flow if flow is None else flow)
    out: dict[str, dict[str, int]] = {k.name: {} for k in FlowKind}
    # 逐次ループ宣言: 部門×部門×科目(6×6×15=540)
    for c in AccountCode:
        for a in Sector:
            for b in Sector:
                amt = int(f[int(a), int(b), int(c)])
                if amt == 0:
                    continue
                kind = flow_kind(int(c), int(a), int(b)).name
                name = ACCOUNT_NAMES[int(c)]
                out[kind][name] = out[kind].get(name, 0) + amt
    return out


def check_all(ledger, goods=None, close=None) -> CheckReport:
    """日次ゲートに使う全検査(§2.4)。"""
    flow = None if close is None else close.flow
    res_ok, res_amt = residual_gate(ledger, flow)
    return CheckReport(
        flow=flow_matrix_balanced(ledger, close),
        net_worth=net_worth_equals_real_assets(ledger, goods),
        residual_ok=res_ok,
        residual_amount=res_amt,
        hoard=hoard_report(ledger),
        ex_nihilo_ok=ex_nihilo_ok(ledger),
        faucet_sink=faucet_sink_totals(ledger, flow),
    )
