"""economy.stage2 — 経済の段階 2(第 2 期 2-1・CP2 の段階 2・腕 ``--economy-stage2``・既定 off)。

正: 決定 10-12 §4-11(EC1〜EC6・税・信用・v1 の手持ちのお金の問題と直し方・見張り)・計画 10-12 第 2 期 2-1・回答 10-13b §0-3
(新しい問いは既定 off の腕で仮採用)・口の約束 1-9(基本操作 ``ops.transfer`` だけが残高を書く=本モジュールは帳簿の汎用の口
``Ledger.transfer_many`` を呼ぶだけ・新しい書き手は作らない)。

腕は 1 つ(``engine.economy_stage2``・``--economy-stage2 {off,on}``・環境変数 ``SHIBUYA_ECONOMY_STAGE2``)。部品は 5 つ
(``--economy-stage2-parts``・既定=全部)。部品ごとに 1 つずつ止められる(止めると当該の流れが 0):

| 部品 | 流れ | 口 |
|---|---|---|
| ``wages`` | 給料日(毎月 25 日・土休なら前の営業日=暦の口)の日の締めで、雇用主 → 世帯の銀行預金(``金:賃金``・
  ``Process("payroll")``)。雇用主(組織・店の担当従業者の店)の原資=外界 → 雇用主の消費支出(域外の取引先の支払い=払う
  賃金と同じ額=第 1 陣の「外生」・faucet)。給与の天引きは器だけ(規則の表に行が無い=0) | ``before_close`` |
| ``withdraw`` | ATM・銀行の支店で本人が下ろす(銀行 → 世帯の現金・``金:引き出し``・``Process("atm")``) | ``withdraw`` |
| ``payment`` | 購入・食事・運賃の支払いの方法(現金か口座=カード・電子マネー・IC)を本人が選ぶ。口座=世帯の預金 → 店(本体の
  行は ``金:消費支出`` のまま+銀行の決済の行 ``金:カード``) | ``purchase``・``can_pay``・``pay_fares`` |
| ``tax`` | レジの消費税(規則の表の率=国 7.8%+地方 22/78=10%)の分を店 → 政府(``金:税``・``Process("register")``)=店の
  売上は税抜きに | ``purchase`` |
| ``visitors`` | 来街者(種別 1・6・7)にも口座(持ち込み=初期の財布の ``VISITOR_ACCOUNT_SHARE`` を預金へ分ける=合計は不変)=カード払いが効く | ``endow`` |

腕が on なら部品によらず、来街者でない体には初期の預金を入れる(``endow``)。保存則: 新しい流れは全部
``accounts.FLOW_REGISTRY`` に登録し、日の締めで ``checks.conservation_check`` が見る(腕の有無によらず)。

本人の判断(mock と古典の方策の規則=**未リサーチ(expedient)**・判断モデルと LLM の段で本人の答えに替える):

- 引き出し: 財布 < 1 日の消費 × ``WITHDRAW_TRIGGER_DAYS``(1)のとき、ATM の営業中のセルで下ろす。額=min(預金, 1 日の消費 ×
  ``WITHDRAW_DAYS``(3))を千円単位に切り下げ(ATM の紙幣の単位)。引き出しは主の行為(行為の語彙 12 語)に添える副の判断
  (判断の 1 呼の中で決める=行為の語彙を変えない)。
- 支払いの方法: 財布が足りれば現金・足りなければ口座(本人の属性があれば優先=今は無い)。運賃は IC(口座)が既定・口座が
  足りなければ現金。
- 初期の預金: 来街者でない体=1 日の消費 × ``DEPOSIT_DAYS``(30)日・来街者(visitors の部品)=持ち込み(初期の財布)×
  ``VISITOR_ACCOUNT_SHARE``(0.5)を預金へ分ける(財布はその分減る)。財布(現金)は今の ``anchors.initial_wallets`` のまま(EC2 の統計からの資産は親が
  e-Stat の表を取ってから)。
- 給料日=毎月 25 日(多くの企業の慣行=出典なし)・労働時間=W17 の「勤務」の週の分 × 52/12 週(W17 の無いランは月
  ``DEFAULT_MONTHLY_HOURS``=160 時間)・時給=最低賃金(規則の表から asof で読む=W16/W17 に賃金の属性が無い)。
  〔賃金の小さな版上げ・2026-10-17・回答 10-13b §7 の 3〕既定の賃金の腕 ``occupation`` では、月の賃金=職業 × 性 × 年齢 ×
  雇用形態の実データ(賃金構造基本統計調査 令和 7 年の所定内給与=``economy.wages.occupation_wages``)で、W17 の勤務時間も
  最低賃金も額に使わない(つなぎの台帳 ``DOC-wage_occ-*``・記録 ``wage_occ/README.md``)。上の「労働時間 × 最低賃金」は
  切替口 ``--wage w17``(旧値の再現だけ=次の版上げで消す)と、賃金の表の写しが無い写し(data の無い CI=月 160 時間 ×
  最低賃金に戻して注記)の道。
- 店の外界の売上(範囲の外の取引先)の額は 0(資料なし)。縮小ランの比(体数 / 母集団)を manifest に宣言する。

つなぎの台帳の行(``docs/design/bridging-ledger.json``・宣言の場所=記録 ``ec21/README.md``): ``DOC-ec21-*``。

逐次ループ宣言(P4): 新しい逐次ループは無い(どの口も配列演算・Python のループは部門・部品・登録の行の数ぶんだけ)。
"""

from __future__ import annotations

import datetime as _dt
import warnings
from fractions import Fraction
from typing import Any, Final, Mapping

import numpy as np

from shibuya.economy import anchors as AN
from shibuya.economy import ops as _OPS
from shibuya.economy import wages as _WG
from shibuya.economy.accounts import (
    ACCOUNT_NAMES,
    SECTOR_NAMES,
    AccountCode,
    BalanceLine,
    Sector,
    flow_registry_table,
    registered_cells,
)
from shibuya.engine.ledger_api import TransferStatus

__all__ = [
    "PARTS",
    "VISITOR_KINDS",
    "DEPOSIT_DAYS",
    "VISITOR_ACCOUNT_SHARE",
    "WITHDRAW_TRIGGER_DAYS",
    "WITHDRAW_DAYS",
    "ATM_UNIT_YEN",
    "DEFAULT_MONTHLY_HOURS",
    "PAYDAY_DAY_OF_MONTH",
    "EXTERNAL_STORE_SALES_YEN",
    "QUANTILES",
    "BYTES_PER_AGENT",
    "WAGE_BYTES_PER_AGENT",
    "STAGE2_TRANSFERS_PER_AGENT_PER_DAY",
    "STAGE2_MEASURED_TRANSFERS_PER_AGENT_DAY",
    "STAGE2_MEASURED_LIVE_ROWS_PER_AGENT",
    "ATM_ROW_BYTES",
    "EMPLOYER_ROW_BYTES",
    "MoneyStage2",
    "payroll_deductions",
    "tax_of",
]

#: 部品(``engine.economy_stage2.PARTS`` と同じ並び=試験が突き合わせる)。
PARTS: Final[tuple[str, ...]] = ("wages", "withdraw", "payment", "tax", "visitors")
#: 来街者の種別(``anchors.WalletKind`` の来街者・定期来街者・訪日来街者)。
VISITOR_KINDS: Final[tuple[int, ...]] = (
    int(AN.WalletKind.VISITOR), int(AN.WalletKind.REGULAR_VISITOR), int(AN.WalletKind.FOREIGN_VISITOR))
#: 初期の預金=1 日の消費 × この日数(来街者でない体・未リサーチ(expedient))。
DEPOSIT_DAYS: Final[float] = 30.0
#: 来街者の持ち込み(初期の財布)のうち口座(預金)へ分ける割合(未リサーチ(expedient)・〔検収 L2〕上乗せでなく分ける)。
VISITOR_ACCOUNT_SHARE: Final[float] = 0.5
#: 引き出しの規則: 財布 < 1 日の消費 × この日数のとき下ろす(mock と古典の方策の規則・未リサーチ(expedient))。
WITHDRAW_TRIGGER_DAYS: Final[float] = 1.0
#: 引き出しの額の上限=1 日の消費 × この日数(未リサーチ(expedient))。
WITHDRAW_DAYS: Final[float] = 3.0
#: ATM の払い出しの単位[円](紙幣=千円・未リサーチ(expedient))。
ATM_UNIT_YEN: Final[int] = 1_000
#: W17 の無いランの月の労働時間[時](週 40 時間 × 4 週・未リサーチ(expedient))。
DEFAULT_MONTHLY_HOURS: Final[float] = 160.0
#: 給料日(毎月この日・土休なら前の営業日=暦の口 ``SimCalendar.is_payday``・未リサーチ(expedient))。
PAYDAY_DAY_OF_MONTH: Final[int] = 25
#: 店の外界の売上(範囲の外の取引先)の 1 店 1 日の額[円](資料なし=0・未リサーチ(expedient))。
EXTERNAL_STORE_SALES_YEN: Final[int] = 0
#: 財布と預金の分位(見張り・決定 10-12 §4-11)。
QUANTILES: Final[tuple[int, ...]] = (10, 50, 90)
#: バイト予算(腕のランだけ・伸びない): 体あたり=中身の 4 列(種別 8・1 日の消費 8・来街者 1・労働時間 8)+組み立ての物の
#: 2 列(種別 8・労働時間 8)=41 B+〔検収 A1〕呼の控えの 2 列(呼の id への参照 8+その文字列 57(39 万体の id の
#: ``sys.getsizeof`` の実測)・支払いの答え 1)=66 B → 107 B。ATM の表=1 点 66 B(セル 8・種類 1・営業の区間 7×2×2×2 B=56・
#: 出どころ 1)・55 点で 3,630 B。雇用主の口(W6 の組織の数 9,872)=1 口 44 B(帳簿の 5 行 × 8 B+最後に動いた日 4 B)=
#: 434,368 B。生ログの支払いの方法の列は輪の 1 行 24 B の切り上げの空きに入る(``ledger.RAW_ROW_BYTES`` は不変)。信用の器は
#: 0 行(空)。
BYTES_PER_AGENT: Final[int] = 107
#: 〔賃金の小さな版上げ〕賃金の腕 ``occupation`` のランの体あたりの足し分: 中身の 2 列(月の賃金 8・出どころ 1)+組み立ての
#: 物の入力 5 列(職業の語の番号 2・雇用の語の番号 2・性 1・年齢 2・乱数の鍵 8)=24 B+〔検収 M1〕月の時間の目安 8 B=32 B
#: (``w17`` のランは 0=今のまま)。
WAGE_BYTES_PER_AGENT: Final[int] = 32
#: 金の生ログの輪の係数(腕のランだけ・行/体/日)。腕 on の 5,000 体 2 日の実測: 0 日目 8.824・1 日目 5.402 行/体
#: (0 日目=初期の預金の 2 行・IC の運賃の 2 行・税の行を含む)。保持窓 1 日の輪は前の日の行と今日の行を持つ=2 日の和の
#: 最大 14.226 行/体で 13.5(1 日の最大の 1.5 倍)の輪は 3,630 行溢れた → 2 日の和の最大の 1.1 倍以上かつ 1 日の最大の 1.5 倍
#: 以上=16.0(未リサーチ(expedient)・実測 1 本)。腕の無いランは ``ledger.TRANSFERS_PER_AGENT_PER_DAY``(6.5)のまま。
STAGE2_TRANSFERS_PER_AGENT_PER_DAY: Final[float] = 16.0
STAGE2_MEASURED_TRANSFERS_PER_AGENT_DAY: Final[float] = 8.824
STAGE2_MEASURED_LIVE_ROWS_PER_AGENT: Final[float] = 14.226
ATM_ROW_BYTES: Final[int] = 66
EMPLOYER_ROW_BYTES: Final[int] = 44

_H: Final[int] = _OPS.ACCOUNT_SECTOR
_S: Final[int] = int(Sector.STORE)
_E: Final[int] = int(Sector.EMPLOYER)
_B: Final[int] = int(Sector.BANK)
_G: Final[int] = int(Sector.GOVERNMENT)
_W: Final[int] = int(Sector.ROW)
_WITHDRAW_WHAT: Final[str] = f"{_OPS.MONEY_FAMILY}:引き出し"


def tax_of(amounts: np.ndarray, rate: Fraction) -> np.ndarray:
    """税込の額の中の消費税[円](``額 × 率 / (1 + 率)`` の切り捨て=レジの端数=未リサーチ(expedient)・4-2 で表に)。"""
    a = np.asarray(amounts, dtype=np.int64)
    if rate == 0:
        return np.zeros(a.shape, dtype=np.int64)
    num, den = int(rate.numerator), int(rate.denominator)
    return (a * num) // (den + num)


def payroll_deductions(gross: np.ndarray, asof: "str | _dt.date") -> tuple[np.ndarray, str | None]:
    """給与の天引き(所得税・住民税・社会保険料)の器。規則の表に行が無い=0(``None``=表なし)。外す段 4-2。"""
    del asof
    return np.zeros(np.asarray(gross).shape, dtype=np.int64), None


def _rows_of(cause: Any, rows: np.ndarray) -> Any:
    """〔検収 A1〕行ごとの原因(``list``)なら ``rows`` の行の分だけ・1 つの原因か None はそのまま。"""
    if isinstance(cause, list):
        return [cause[i] for i in np.asarray(rows, dtype=np.int64).tolist()]
    return cause


def _q(x: np.ndarray) -> dict[str, int]:
    v = np.asarray(x, dtype=np.int64)
    if v.size == 0:
        return {f"p{q}": 0 for q in QUANTILES}
    return {f"p{q}": int(round(float(np.percentile(v, q)))) for q in QUANTILES}


def _empty_meter() -> dict[str, dict[str, int]]:
    return {
        "endow": {"deposit_rows": 0, "deposit_amount": 0, "visitor_rows": 0, "visitor_amount": 0},
        "wages": {"paydays": 0, "paid": 0, "amount": 0, "unpaid": 0, "unpaid_amount": 0, "funding": 0,
                  "deductions": 0, "no_hours": 0, "outside_employer": 0, "employer_rows": 0, "store_rows": 0},
        "withdraw": {"asked": 0, "count": 0, "amount": 0, "wallet_ok": 0, "no_deposit": 0},
        "payment": {"cash_rows": 0, "cash_amount": 0, "account_rows": 0, "account_amount": 0, "short": 0,
                    "fare_ic_rows": 0, "fare_ic_amount": 0, "fare_cash_rows": 0, "fare_cash_amount": 0},
        "tax": {"rows": 0, "amount": 0},
        "external_sales": {"rows": 0, "amount": 0},
        # 〔検収 A1〕呼の id の配線: 控えた行(金に触れる行為の呼)・口の支払いの答え・原因 LlmCall の購入と食事の行・
        # 原因の無い購入と食事の行・答えを使った支払いの行・原因 LlmCall の引き出し・口が選んだ引き出し
        "calls": {"noted": 0, "pay_answers": 0, "purchase_caused": 0, "purchase_uncaused": 0,
                  "pay_answer_rows": 0, "withdraw_caused": 0, "withdraw_chosen": 0},
    }


class MoneyStage2:
    """経済の段階 2 の中身(``Ledger.attach_stage2`` が作る=状態台帳の行 EC・計器 ``s2_meter`` は行 EM)。

    Args:
        plan: engine の側の組み立ての物(``engine.economy_stage2.Stage2Plan``)。
        n_households: 世帯の数(=体の数)。
        n_employers: 雇用主の口の数(W6 の組織の数・``cli.build_ledger_bundle`` が決める)。
    """

    def __init__(self, plan: Any, *, n_households: int, n_employers: int) -> None:
        self.plan = plan
        self.parts = frozenset(str(p) for p in plan.parts)
        unknown = self.parts - set(PARTS)
        if unknown:
            raise ValueError(f"経済の段階 2 の部品は {PARTS} の中(いま {sorted(unknown)})")
        n = int(n_households)
        self.n = n
        self.n_employers = int(n_employers)
        k = np.zeros(n, dtype=np.int64)
        src = np.asarray(plan.kinds, dtype=np.int64).ravel()[:n]
        k[: src.size] = src
        self.kinds = k
        #: 1 日の消費[円](``anchors.daily_spending``=種別の写像)。引き出しの規則と初期の預金の物差し。
        self.daily = AN.daily_spending(k)
        self.visitor = np.isin(k, np.asarray(VISITOR_KINDS, dtype=np.int64))
        h = np.full(n, float(DEFAULT_MONTHLY_HOURS), dtype=np.float64)
        mh = getattr(plan, "monthly_hours", None)
        if mh is not None:
            mh = np.asarray(mh, dtype=np.float64).ravel()[:n]
            h[: mh.size] = mh
        self.monthly_hours = h
        self.hours_source = str(getattr(plan, "hours_source", "default"))
        #: 〔賃金の小さな版上げ〕賃金の腕(組み立ての物に無ければ w17=今までの道)と、体ごとの月の賃金[円](``occupation`` の
        #: ランだけ・−1=値なし)・出どころ(``economy.wages.BASIS_NAMES`` の番号)・点検の記録(manifest の plan.wage)。
        self.wage_model = str(getattr(plan, "wage_model", "w17"))
        mw, basis, summary, wsrc, hours = self._occupation_wages(plan, n)
        self.monthly_wage = mw
        self.wage_basis = basis
        #: 〔検収 M1〕体ごとの月の所定内の時間の目安[時](最低賃金の床=時給 × この時間・``economy.wages.month_hours``)。
        self.wage_hours = hours
        self.wage_summary = summary
        self.wage_source = wsrc
        #: ATM の表(``Fixtures.atms`` と同じ物=状態台帳の行 ATM)。
        self.atms = getattr(plan, "atms", None)
        #: 支払い(payment)か税(tax)が動くランは購入を委ねる。
        self.handles_purchase = bool({"payment", "tax"} & self.parts)
        #: 計器(状態台帳の行 EM=diag・discardable)。ランの積算と日の欄(日の締めで 0)。
        self.s2_meter: dict[str, Any] = {"run": _empty_meter(), "day": _empty_meter(), "rules": {}}
        if self.wage_model != "w17":
            # 〔賃金の小さな版上げ〕組み立ての賃金の点検は観測(母集団の抽出=seed で動く)=rules.wage_build・plan には道だけ
            winp = getattr(plan, "wage_inputs", None)
            self.s2_meter["rules"]["wage_build"] = {
                "path": wsrc, **(summary or {}),
                "inputs": winp.record() if winp is not None and hasattr(winp, "record") else None,
                "floor_at_start": self._floor_record(plan, mw, hours)}
        self._rates: dict[str, tuple[Fraction, str]] = {}
        #: 〔検収 A1〕体ごとの最後の「金に触れる行為」(購入・食事・並ぶ)の呼の id(None=まだ無い)と、その呼の支払いの方法の
        #: 答え(-1=答えなし・0=現金・1=口座)。着いて実行する意図・列から席へ入った体の支払いも同じ呼を原因にする。
        self.last_call = np.full(n, None, dtype=object)
        self.pay_answer = np.full(n, -1, dtype=np.int8)
        #: 〔第 2 期 2-4 V4〕直前の ``purchase`` の行ごとのレジの税[円](店 → 政府へ移せた額・ほかは 0)。``resolve`` が店の売上の
        #: 写し ``pois.revenue`` を税抜きにするのに読む(``Ledger.last_purchase_tax``)。中身だけ変わる箱(組み立ての後は封じる)。
        self._last_tax: dict[str, np.ndarray] = {"rows": np.zeros(0, dtype=np.int64)}
        for a in (self.kinds, self.daily, self.visitor, self.monthly_hours, self.monthly_wage, self.wage_basis,
                  self.wage_hours):
            if a is not None:
                a.setflags(write=False)
        object.__setattr__(self, "_sealed", True)

    @staticmethod
    def _floor_record(plan: Any, mw: np.ndarray | None, hours: np.ndarray | None) -> dict[str, Any] | None:
        """〔検収 M1〕組み立ての点検: ランの最初の日に効いている最低賃金の床に、何体が当たるか(値のある体の中=観測)。"""
        if mw is None or hours is None:
            return None
        try:
            asof = plan.date_of(0).isoformat()
        except (AttributeError, TypeError):
            return None
        floor, src = _WG.min_wage_floor(asof)
        _f, raised = _WG.apply_floor(mw, hours, floor)
        have = int((mw >= 0).sum())
        return {"asof": asof, "yen_per_hour": floor, "source": src, "raised": int(raised.sum()), "bodies": have,
                "raised_share": round(float(raised.sum()) / have, 4) if have else 0.0}

    @staticmethod
    def _occupation_wages(plan: Any, n: int) -> tuple[Any, Any, Any, str, Any]:
        """〔賃金の小さな版上げ〕賃金の腕 ``occupation`` の体ごとの月の賃金(``economy.wages``・W17 の勤務時間を読まない)。

        Returns:
            (月の賃金 int64 か None, 出どころ int8 か None, 点検の記録か None, 道の名, 月の時間の目安 float64 か None)。道の名:
            ``w17``(腕 w17・今までの道)・``occupation``・``tables_absent``(賃金の表の写しが無い写し=月の時間 × 最低賃金に
            戻す=注記)。最低賃金の床は給料日に当てる(その日の規則の表の版=:meth:`payroll`)。
        """
        if str(getattr(plan, "wage_model", "w17")) == "w17":
            return None, None, None, "w17", None
        winp = getattr(plan, "wage_inputs", None)
        tables = _WG.load_wage_tables()
        if tables is None or winp is None:
            warnings.warn(f"賃金の表の写し {_WG.DERIVED_RELDIR} が無い写し: 賃金は 2-1 の道(月の時間 × 最低賃金)に戻す",
                          _WG.WageTablesAbsentWarning, stacklevel=3)
            return None, None, {"source": "tables_absent"}, "tables_absent", None
        got, b = _WG.occupation_wages(
            tables, occ_code=winp.occ_code, occ_vocab=winp.occ_vocab, emp_code=winp.emp_code,
            emp_vocab=winp.emp_vocab, sex=winp.sex, age=winp.age, seed=winp.seed, counters=winp.counters,
            given=winp.given)
        hrs_got = _WG.month_hours(tables, occ_code=winp.occ_code, occ_vocab=winp.occ_vocab, emp_code=winp.emp_code,
                                  emp_vocab=winp.emp_vocab, sex=winp.sex)
        mw = np.full(n, -1, dtype=np.int64)
        basis = np.full(n, _WG.BASIS_AVERAGE, dtype=np.int8)
        hours = np.full(n, np.nan, dtype=np.float64)
        k = min(n, got.size)
        mw[:k], basis[:k], hours[:k] = got[:k], b[:k], hrs_got[:k]
        summary = {
            "source": "賃金構造基本統計調査 令和7年(R-107・一般 第9・6・18表・短時間 第2表・全国・企業規模計)",
            "md5": dict(tables.md5),
            "bodies": int(n),
            "basis": {name: int((basis == i).sum()) for i, name in enumerate(_WG.BASIS_NAMES)},
            "no_value": int((mw < 0).sum()),
            "monthly": _q(mw[mw >= 0]),
            "median_check": _WG.median_check(tables, mw, basis, winp.occ_code, winp.occ_vocab, winp.emp_code,
                                             winp.emp_vocab, winp.sex, min_n=30),
        }
        return mw, basis, summary, "occupation", hours

    def __setattr__(self, name: str, value: Any) -> None:
        """〔検収 L1〕組み立ての後は属性を書き換えられない(計器と率の控えは辞書の中身だけが変わる)。"""
        if getattr(self, "_sealed", False):
            raise AttributeError(f"MoneyStage2 は組み立ての後は書けない({name})")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"MoneyStage2 の属性は消せない({name})")

    # ------------------------------------------------------------------ 共通
    def part(self, name: str) -> bool:
        return str(name) in self.parts

    def _add(self, group: str, **kw: int) -> None:
        for scope in ("run", "day"):
            g = self.s2_meter[scope][group]
            for k_, v in kw.items():
                g[k_] = int(g[k_]) + int(v)

    def _cause(self, name: str) -> Any:
        fn = getattr(self.plan, "cause", None)
        return None if fn is None else fn(name)

    def _date_of_step(self, step: int) -> _dt.date:
        return self.plan.date_of_step(int(step))

    def _tax_rate(self, step: int) -> Fraction:
        d = self._date_of_step(step).isoformat()
        got = self._rates.get(d)
        if got is None:
            got = AN.consumption_tax_rate(d)
            self._rates[d] = got
            self.s2_meter["rules"]["consumption_tax"] = {"asof": d, "rate": str(got[0]), "source": got[1]}
        return got[0]

    # ------------------------------------------------------------------ 初期の預金(組み立て)
    def endow(self, ledger: Any, step: int) -> None:
        """初期の預金。``Ledger.endow_households``(初期の財布=現金)の後に呼ばれる。

        - 来街者でない体: 外界 → 世帯の口座(来街者持込の科目・口座の方法)=1 日の消費 × ``DEPOSIT_DAYS``。
        - 来街者(visitors の部品・〔検収 L2〕): 持ち込み(=初期の財布)を**分ける**=財布 × ``VISITOR_ACCOUNT_SHARE`` を
          預け入れ(世帯 → 銀行の預金純増=世帯の現金が減り預金が増える)。合計(現金+預金)は変わらない。
        """
        amt = np.rint(self.daily.astype(np.float64) * float(DEPOSIT_DAYS)).astype(np.int64)
        amt[self.visitor] = 0
        who = np.flatnonzero(amt > 0)
        if who.size:
            st = np.asarray(ledger.transfer_many(_W, np.zeros(who.size, dtype=np.int64), _H, who, amt[who],
                                                 int(AccountCode.CARRY_IN), int(step), method=_OPS.METHOD_ACCOUNT))
            ok = st == int(TransferStatus.OK)
            self._add("endow", deposit_rows=int(ok.sum()), deposit_amount=int(amt[who][ok].sum()))
        if not self.part("visitors"):
            return
        cash, _dep = self._balances(ledger)
        vis = np.zeros(self.n, dtype=np.int64)
        vis[self.visitor] = np.floor(cash[self.visitor].astype(np.float64) * float(VISITOR_ACCOUNT_SHARE)).astype(np.int64)
        vw = np.flatnonzero(vis > 0)
        if vw.size == 0:
            return
        st = np.asarray(ledger.transfer_many(_H, vw, _B, np.zeros(vw.size, dtype=np.int64), vis[vw],
                                             int(AccountCode.DEPOSIT_NET), int(step)))
        ok = st == int(TransferStatus.OK)
        self._add("endow", visitor_rows=int(ok.sum()), visitor_amount=int(vis[vw][ok].sum()))

    # ------------------------------------------------------------------ 呼の id(検収 A1)
    def note_calls(self, agents: np.ndarray, call_ids: np.ndarray, pay: np.ndarray) -> None:
        """この刻みに適用した LLM の答えのうち金に触れる行為(購入・食事・並ぶ)の行の呼の id と支払いの方法の答えを控える。

        engine の行為の解決(``resolve.apply``)が意図の行(``IntentBatch.call_id``・``s2_flags``)から渡す。
        """
        a = np.asarray(agents, dtype=np.int64).ravel()
        if a.size == 0:
            return
        cid = np.asarray(call_ids, dtype=object).ravel()
        pa = np.asarray(pay, dtype=np.int64).ravel()
        self.last_call[a] = cid
        self.pay_answer[a] = pa.astype(np.int8)
        self._add("calls", noted=int(a.size), pay_answers=int((pa >= 0).sum()))

    def _llm_causes(self, holders: np.ndarray) -> list[Any] | None:
        """体ごとの控えの呼 → 行ごとの原因 ``LlmCall(call_id)`` の並び(控えの無い行は None・全部無ければ None)。"""
        make = getattr(self.plan, "llm_cause", None)
        if make is None:
            return None
        cid = self.last_call[np.asarray(holders, dtype=np.int64).ravel()]
        if not any(c is not None for c in cid):
            return None
        return [None if c is None else make(c) for c in cid]  # 逐次ループ宣言: 購入・食事の行の数ぶん

    def purchase_causes(self, buyers: np.ndarray) -> list[Any] | None:
        """購入・食事の行の原因(``Ledger.purchase_many`` が呼ぶ)。数を計器に足す。"""
        b = np.asarray(buyers, dtype=np.int64).ravel()
        if b.size == 0:
            return None
        out = self._llm_causes(b)
        n_c = 0 if out is None else sum(1 for c in out if c is not None)
        self._add("calls", purchase_caused=n_c, purchase_uncaused=int(b.size) - n_c)
        return out

    # ------------------------------------------------------------------ 支払い(payment・tax)
    def _balances(self, ledger: Any) -> tuple[np.ndarray, np.ndarray]:
        cash = np.asarray(ledger.balance(BalanceLine.CASH, _H), dtype=np.int64)
        dep = np.asarray(ledger.balance(BalanceLine.DEPOSIT, _H), dtype=np.int64)
        return cash, dep

    def can_pay(self, ledger: Any, buyers: np.ndarray, amounts: np.ndarray) -> np.ndarray:
        """払えるか(payment の部品=現金か口座のどちらかで足りる・ほか=現金で足りる)。読むだけ。"""
        b = np.asarray(buyers, dtype=np.int64).ravel()
        a = np.asarray(amounts, dtype=np.int64).ravel()
        cash, dep = self._balances(ledger)
        ok = cash[b] >= a
        if self.part("payment"):
            ok = ok | (dep[b] >= a)
        return ok

    def _methods(self, ledger: Any, payers: np.ndarray, amounts: np.ndarray) -> np.ndarray:
        """行ごとの支払いの方法(財布が足りれば現金・足りなければ口座・どちらも足りなければ現金=却下に任せる)。

        〔検収 A1〕その体の呼に支払いの方法の答えがあれば先に従う(カード=預金で足りれば口座・現金=財布で足りれば現金)。
        足りなければ上の規則に戻る。
        """
        cash, dep = self._balances(ledger)
        need = ledger._running_need(payers, amounts)
        cash_ok = need <= cash[payers]
        acct = np.zeros(payers.size, dtype=bool)
        ans = self.pay_answer[payers]
        if bool((ans >= 0).any()):
            self._add("calls", pay_answer_rows=int((ans >= 0).sum()))
        cand = np.flatnonzero(~cash_ok | (ans == 1))
        if cand.size:
            dneed = ledger._running_need(payers[cand], amounts[cand])
            acct[cand[dneed <= dep[payers[cand]]]] = True
        return acct

    def purchase(self, ledger: Any, buyers: np.ndarray, stores: np.ndarray, amounts: np.ndarray, step: int,
                 *, cause: Any = None) -> np.ndarray:
        """購入・食事の金の脚(世帯 → 店舗・消費支出)。payment=本人の選ぶ方法・tax=レジの消費税。行ごとの状態。"""
        b = np.asarray(buyers, dtype=np.int64).ravel()
        s = np.asarray(stores, dtype=np.int64).ravel()
        a = np.asarray(amounts, dtype=np.int64).ravel()
        out = np.full(b.size, int(TransferStatus.OK), dtype=np.int8)
        last_tax = np.zeros(b.size, dtype=np.int64)
        self._last_tax["rows"] = last_tax
        if b.size == 0:
            return out
        acct = self._methods(ledger, b, a) if self.part("payment") else np.zeros(b.size, dtype=bool)
        cash_rows = np.flatnonzero(~acct)
        acct_rows = np.flatnonzero(acct)
        code = int(AccountCode.CONSUMPTION)
        if cash_rows.size:
            out[cash_rows] = ledger.transfer_many(_H, b[cash_rows], _S, s[cash_rows], a[cash_rows], code, int(step),
                                                  cause=_rows_of(cause, cash_rows))
        if acct_rows.size:
            out[acct_rows] = ledger.transfer_many(_H, b[acct_rows], _S, s[acct_rows], a[acct_rows], code, int(step),
                                                  cause=_rows_of(cause, acct_rows), method=_OPS.METHOD_ACCOUNT)
        ok = out == int(TransferStatus.OK)
        self._add("payment", cash_rows=int((ok & ~acct).sum()), cash_amount=int(a[ok & ~acct].sum()),
                  account_rows=int((ok & acct).sum()), account_amount=int(a[ok & acct].sum()),
                  short=int((~ok).sum()))
        if self.part("tax") and ok.any():
            tax = tax_of(a[ok], self._tax_rate(step))
            keep = tax > 0
            if keep.any():
                st = np.asarray(ledger.transfer_many(_S, s[ok][keep], _G, np.zeros(int(keep.sum()), dtype=np.int64),
                                                     tax[keep], int(AccountCode.TAX), int(step),
                                                     cause=self._cause("register")))
                paid = st == int(TransferStatus.OK)
                self._add("tax", rows=int(paid.sum()), amount=int(tax[keep][paid].sum()))
                last_tax[np.flatnonzero(ok)[keep][paid]] = tax[keep][paid]  # 〔2-4 V4〕行ごとの移せた税
        return out

    def last_purchase_tax(self, n: int) -> np.ndarray:
        """〔第 2 期 2-4 V4〕直前の :meth:`purchase` の行ごとのレジの税[円](行の数 ``n`` と合わなければ止める)。"""
        rows = self._last_tax["rows"]
        if rows.size != int(n):
            raise RuntimeError(f"直前の購入の行の数が違う({rows.size} ≠ {int(n)})")
        return rows

    def register_tax(self) -> int:
        """〔第 2 期 2-4 V4〕ランの積算のレジの税[円](店 → 政府)。店の売上の写しは税抜き=``RunResult.conserved`` の左辺から引く。"""
        return int(self.s2_meter["run"]["tax"]["amount"])

    def pay_fares(self, ledger: Any, riders: np.ndarray, fare: int, step: int, *, cause: Any = None) -> np.ndarray:
        """運賃(世帯 → 外界・持ち出し)。IC(口座)が既定・口座が足りなければ現金。行ごとの状態。"""
        r = np.asarray(riders, dtype=np.int64).ravel()
        out = np.full(r.size, int(TransferStatus.OK), dtype=np.int8)
        if r.size == 0:
            return out
        a = np.full(r.size, int(fare), dtype=np.int64)
        _cash, dep = self._balances(ledger)
        need = ledger._running_need(r, a)
        ic = need <= dep[r]
        code = int(AccountCode.CARRY_OUT)
        zeros = np.zeros(r.size, dtype=np.int64)
        if ic.any():
            out[ic] = ledger.transfer_many(_H, r[ic], _W, zeros[ic], a[ic], code, int(step), cause=cause,
                                           method=_OPS.METHOD_ACCOUNT)
        if (~ic).any():
            out[~ic] = ledger.transfer_many(_H, r[~ic], _W, zeros[~ic], a[~ic], code, int(step), cause=cause)
        ok = out == int(TransferStatus.OK)
        self._add("payment", fare_ic_rows=int((ok & ic).sum()), fare_ic_amount=int(a[ok & ic].sum()),
                  fare_cash_rows=int((ok & ~ic).sum()), fare_cash_amount=int(a[ok & ~ic].sum()))
        return out

    # ------------------------------------------------------------------ 引き出し(withdraw)
    def withdraw(self, ledger: Any, holders: np.ndarray, step: int, *, cause: Any = None,
                 wanted: np.ndarray | None = None, call_ids: np.ndarray | None = None) -> np.ndarray:
        """ATM・銀行の支店で下ろす(engine が「営業中の ATM のセルで、この刻みに判断した体」を渡す)。

        下ろすかは本人の判断(mock と古典の規則=財布 < 1 日の消費 × ``WITHDRAW_TRIGGER_DAYS``・``wanted`` の行=判断の口が
        「お金を下ろす」を選んだ体は規則を通さない)。額=min(預金, 1 日の消費 × ``WITHDRAW_DAYS``) を千円単位に切り下げ。
        戻り=行ごとの下ろした額(0=下ろさない)。

        〔検収 A1〕``call_ids``=行ごとのこの刻みの判断の呼の id(None=呼でない行)。呼のある行の原因は
        ``LlmCall(call_id)``(下ろすのはその判断の副の行為)・無い行は ``cause``(既定 ``Process("atm")``)。
        """
        h = np.asarray(holders, dtype=np.int64).ravel()
        got = np.zeros(h.size, dtype=np.int64)
        if h.size == 0 or not self.part("withdraw"):
            return got
        cash, dep = self._balances(ledger)
        uniq, first = np.unique(h, return_index=True)
        want = cash[uniq].astype(np.float64) < self.daily[uniq].astype(np.float64) * float(WITHDRAW_TRIGGER_DAYS)
        if wanted is not None:
            want = want | np.asarray(wanted, dtype=bool).ravel()[first]
        cap = np.rint(self.daily[uniq].astype(np.float64) * float(WITHDRAW_DAYS)).astype(np.int64)
        amt = (np.minimum(cap, dep[uniq]) // ATM_UNIT_YEN) * ATM_UNIT_YEN
        go = want & (amt > 0)
        self._add("withdraw", asked=int(uniq.size), wallet_ok=int((~want).sum()), no_deposit=int((want & (amt <= 0)).sum()))
        if not go.any():
            return got
        who, amt = uniq[go], amt[go]
        c = cause if cause is not None else self._cause("atm")
        make = getattr(self.plan, "llm_cause", None)
        if call_ids is not None and make is not None:
            cid = np.asarray(call_ids, dtype=object).ravel()[first[go]]
            if any(x is not None for x in cid):
                c = [c if x is None else make(x) for x in cid]  # 逐次ループ宣言: 下ろす行の数ぶん
                self._add("calls", withdraw_caused=sum(1 for x in cid if x is not None))
        if wanted is not None:
            self._add("calls", withdraw_chosen=int(np.asarray(wanted, dtype=bool).ravel()[first[go]].sum()))
        st = np.asarray(ledger.transfer_many(_B, np.zeros(who.size, dtype=np.int64), _H, who, amt,
                                             int(AccountCode.DEPOSIT_NET), int(step), cause=c, what=_WITHDRAW_WHAT))
        ok = st == int(TransferStatus.OK)
        self._add("withdraw", count=int(ok.sum()), amount=int(amt[ok].sum()))
        got[first[go][ok]] = amt[ok]
        return got

    # ------------------------------------------------------------------ 賃金(wages)・日の締め
    def before_close(self, ledger: Any, day: int) -> None:
        """日の締めの前: 給料日なら賃金を払う(wages の部品)。"""
        if not self.part("wages"):
            return
        if not bool(self.plan.is_payday(int(day))):
            return
        self.payroll(ledger, int(day))

    def payroll(self, ledger: Any, day: int) -> dict[str, int]:
        """雇用の行(権利台帳の employ)ごとに月の賃金を払う(雇用主 → 世帯の口座・原因 ``Process("payroll")``)。"""
        step = int(self.plan.close_step(int(day)))
        asof = self.plan.date_of(int(day))
        hourly, src = AN.min_wage_hourly(asof.isoformat())
        self.s2_meter["rules"]["minimum_wage"] = {"asof": asof.isoformat(), "yen_per_hour": int(hourly), "source": src}
        agents, sectors, idx = self.plan.employment(int(day))
        agents = np.asarray(agents, dtype=np.int64)
        sectors = np.asarray(sectors, dtype=np.int64)
        idx = np.asarray(idx, dtype=np.int64)
        inside = (agents >= 0) & (agents < self.n)
        agents, sectors, idx = agents[inside], sectors[inside], idx[inside]
        hourly_arr = getattr(self.plan, "hourly", None)
        rate = float(hourly) if hourly_arr is None else np.asarray(hourly_arr, dtype=np.float64)[agents]
        occupation = self.monthly_wage is not None
        if occupation:  # 〔賃金の小さな版上げ〕月の賃金=職業 × 性 × 年齢 × 雇用形態(W17 の勤務時間を使わない)
            # 〔検収 M1〕最低賃金法の床(4 条 2 項)=給料日に効いている規則の表の版(machine の行)。版が無ければ床なし
            floor, floor_src = _WG.min_wage_floor(asof.isoformat())
            floored, raised = _WG.apply_floor(self.monthly_wage[agents], self.wage_hours[agents], floor)
            raised_amount = int((floored - self.monthly_wage[agents])[raised].sum())
            gross = np.maximum(floored, 0)
        else:
            gross = AN.monthly_wage_amounts(self.monthly_hours[agents], hourly=rate)
        ded, _table = payroll_deductions(gross, asof)
        net = gross - ded
        cause = self._cause("payroll")
        self._add("wages", paydays=1, no_hours=int((net <= 0).sum()))
        out = {"paid": 0, "amount": 0}
        for sector in (_E, _S):  # 逐次ループ宣言: 払い手の部門 2 つ
            m = (sectors == sector) & (net > 0)
            if sector == _E:
                bad = m & (idx >= self.n_employers)
                self._add("wages", outside_employer=int(bad.sum()))
                m = m & ~bad
            if not m.any():
                continue
            a, who, emp = net[m], agents[m], idx[m]
            # 原資=外界の売上(払う賃金と同じ額・外生=第 1 陣のまま・雇用主ごとに 1 行)
            uniq, inv = np.unique(emp, return_inverse=True)
            fund = np.bincount(inv, weights=a.astype(np.float64)).astype(np.int64)
            fst = np.asarray(ledger.transfer_many(_W, np.zeros(uniq.size, dtype=np.int64), sector, uniq, fund,
                                                  int(AccountCode.CONSUMPTION), step, cause=cause))
            self._add("wages", funding=int(fund[fst == int(TransferStatus.OK)].sum()))
            if occupation:
                st = np.asarray(AN.monthly_wages(ledger, emp, who, np.zeros(who.size), step, amounts=a,
                                                 payer_sector=sector, method=_OPS.METHOD_ACCOUNT, cause=cause))
            else:
                hrs = self.monthly_hours[who]
                rate_m = rate if np.ndim(rate) == 0 else np.asarray(rate)[m]
                st = np.asarray(AN.monthly_wages(ledger, emp, who, hrs, step, hourly=rate_m, payer_sector=sector,
                                                 method=_OPS.METHOD_ACCOUNT, cause=cause))
            ok = st == int(TransferStatus.OK)
            self._add("wages", paid=int(ok.sum()), amount=int(a[ok].sum()), unpaid=int((~ok).sum()),
                      unpaid_amount=int(a[~ok].sum()),
                      **({"employer_rows": int(ok.sum())} if sector == _E else {"store_rows": int(ok.sum())}))
            out["paid"] += int(ok.sum())
            out["amount"] += int(a[ok].sum())
        if int(ded.sum()) > 0:  # 器: 規則の表に行が無い=いつも 0(4-2 で表に)
            raise NotImplementedError("給与の天引きの表は 4-2")
        if occupation:  # 〔賃金の小さな版上げ〕給料日の計器(払った体の出どころと額の分位)=観測
            paid = net > 0
            b = self.wage_basis[agents]
            self.s2_meter["rules"]["wage_model"] = {
                "model": self.wage_model, "asof": asof.isoformat(), "employed": int(agents.size),
                "paid_by_basis": {name: int((paid & (b == i)).sum()) for i, name in enumerate(_WG.BASIS_NAMES)},
                "no_value": int((~paid).sum()), "paid_amount": _q(net[paid]),
                "paid_mean": round(float(net[paid].mean()), 3) if paid.any() else 0.0,
                "floor": {"yen_per_hour": floor, "source": floor_src, "raised": int(raised.sum()),
                          "raised_share": round(float(raised.sum()) / agents.size, 4) if agents.size else 0.0,
                          "raised_amount": raised_amount}}
        return out

    def external_sales(self, ledger: Any, step: int) -> int:
        """店の外界の売上(範囲の外の取引先・EC5)。1 店 1 日の額 ``EXTERNAL_STORE_SALES_YEN``(0=資料なし)。"""
        if EXTERNAL_STORE_SALES_YEN <= 0:
            return 0
        n_s = int(ledger.sizes[_S])
        a = np.full(n_s, int(EXTERNAL_STORE_SALES_YEN), dtype=np.int64)
        st = np.asarray(ledger.transfer_many(_W, np.zeros(n_s, dtype=np.int64), _S, np.arange(n_s, dtype=np.int64),
                                             a, int(AccountCode.CONSUMPTION), int(step)))
        ok = st == int(TransferStatus.OK)
        self._add("external_sales", rows=int(ok.sum()), amount=int(a[ok].sum()))
        return int(a[ok].sum())

    def growth_declaration(self, *, employers: int) -> Any:
        """腕のランの成長の宣言(体あたりの定常バイト・ATM の表と雇用主の口は定数・伸びない=D-R2-6 の 5 欄)。"""
        from shibuya.core.growth import GrowthDeclaration, Retention

        n_atm = int(getattr(self.atms, "n", 0) or 0)
        fixed = n_atm * ATM_ROW_BYTES + int(employers) * EMPLOYER_ROW_BYTES
        per = int(BYTES_PER_AGENT) + (int(WAGE_BYTES_PER_AGENT) if self.wage_model != "w17" else 0)
        wage_note = (f"・賃金の腕 {self.wage_model} の足し分 {WAGE_BYTES_PER_AGENT} B(月の賃金と出どころと月の時間+入力 5 列)"
                     if self.wage_model != "w17" else "")
        return GrowthDeclaration(
            name="economy_stage2", per_agent_bytes=per, per_cell_bytes=0, per_day_growth="O(1)",
            per_day_growth_coef=0.0, retention=Retention(days=None), worst_case_ops_per_tick=0,
            cap=per * 400_000 + fixed + 1_000_000, cap_budget_row="M8(親が割当・要 delta)",
            mechanism=False,
            note=(f"第 2 期 2-1 経済の段階 2 の腕のランだけ。体あたり {per} B(中身 4 列+呼の控え 2 列+組み立ての物 2 列"
                  f"{wage_note})・ATM の表 {n_atm} 点 × {ATM_ROW_BYTES} B・雇用主の口 {int(employers)} × "
                  f"{EMPLOYER_ROW_BYTES} B は定数。日をまたいで伸びない(実測の増分 0)"),
            unit="entity", bytes_per_unit=per,
        )

    def cash_terms(self) -> int:
        """世帯の現金の外から入った額と現金を通らずに払った額の和(引き出し+口座の購入・食事+IC の運賃)=
        ``RunResult.conserved`` の式の左辺に足す額(ランの積算)。"""
        r = self.s2_meter["run"]
        return int(r["withdraw"]["amount"]) + int(r["payment"]["account_amount"]) + int(r["payment"]["fare_ic_amount"])

    # ------------------------------------------------------------------ 見張り(日次の記録・manifest)
    def _money_view(self, ledger: Any) -> dict[str, Any]:
        cash, dep = self._balances(ledger)
        return {
            "wallet": _q(cash), "deposit": _q(dep),
            "wallet_mean": round(float(cash.mean()), 3) if cash.size else 0.0,
            "deposit_mean": round(float(dep.mean()), 3) if dep.size else 0.0,
            "wallet_zero": int((cash <= 0).sum()),
        }

    def day_record(self, ledger: Any, day: int) -> dict[str, Any]:
        """日次の記録の ``economy.stage2``(その日の計器と財布・預金の分位)。日の欄を 0 に戻す。"""
        out = {"day": int(day), "payday": bool(self.plan.is_payday(int(day))),
               **{k: dict(v) for k, v in self.s2_meter["day"].items()}, **self._money_view(ledger)}
        self.s2_meter["day"] = _empty_meter()
        return out

    def manifest_record(self, ledger: Any, *, credit: Any = None) -> dict[str, Any]:
        """manifest の ``economy.stage2``(設定=腕・部品・規則と宣言/観測=計器・faucet/sink の表・分位)。

        ``credit`` は信用の器の記録(``CreditBook.record``=持ち主の ``Ledger.economy_record`` が読んで渡す)。
        """
        flows: dict[tuple[int, int, int], int] = {}
        for f in tuple(ledger.flow_daily) + (np.asarray(ledger.flow),):  # 逐次ループ宣言: 畳んだ日数ぶん
            for a, b, c in np.argwhere(np.asarray(f) != 0).tolist():
                flows[(c, a, b)] = flows.get((c, a, b), 0) + int(np.asarray(f)[a, b, c])
        cells = registered_cells()
        table = [{"name": n, "account": acc, "payer": pa, "payee": pe, "kind": kd, "stage": st}
                 for n, acc, pa, pe, kd, st in flow_registry_table()]
        by_cell = [{"account": ACCOUNT_NAMES[c], "payer": SECTOR_NAMES[a], "payee": SECTOR_NAMES[b],
                    "kind": (cells[(c, a, b)].name if (c, a, b) in cells else "UNREGISTERED"), "amount": int(v)}
                   for (c, a, b), v in sorted(flows.items())]
        atm = self.atms.record() if self.atms is not None and hasattr(self.atms, "record") else None
        plan_rec = self.plan.record() if hasattr(self.plan, "record") else {}
        if self.wage_model != "w17":  # 〔賃金の小さな版上げ〕賃金の道(設定の節=plan の中・点検の値は観測の rules.wage_build)
            plan_rec = {**plan_rec, "wage_path": self.wage_source}
        return {
            "arm": "on",
            "parts": [p for p in PARTS if p in self.parts],
            "payday_day_of_month": int(PAYDAY_DAY_OF_MONTH),
            "expedients": {
                "deposit_days": float(DEPOSIT_DAYS), "visitor_account_share": float(VISITOR_ACCOUNT_SHARE),
                "withdraw_trigger_days": float(WITHDRAW_TRIGGER_DAYS), "withdraw_days": float(WITHDRAW_DAYS),
                "atm_unit_yen": int(ATM_UNIT_YEN), "default_monthly_hours": float(DEFAULT_MONTHLY_HOURS),
                "fare_default": "IC(口座)", "payment_rule": "財布が足りれば現金・足りなければ口座",
                "external_store_sales_yen": int(EXTERNAL_STORE_SALES_YEN),
            },
            "hours_source": self.hours_source,
            "plan": plan_rec,
            "rules": {k: dict(v) for k, v in self.s2_meter["rules"].items()},
            **{k: dict(v) for k, v in self.s2_meter["run"].items()},
            "faucet_sink_registry": table,
            "faucet_sink_by_cell": by_cell,
            "atms": atm,
            "credit": credit,
            **self._money_view(ledger),
        }
