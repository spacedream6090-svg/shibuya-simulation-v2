"""economy.credit — 信用の器(第 2 期 2-1・決定 10-12 §4-11 の信用 C1〜C3・**器だけ=動かない**)。

決定 10-12 §4-11:
- C1 種類: カード・住宅ローン・消費者ローン・店の借入(BNPL は後)。
- C2 借りるのは本人の判断・審査は貸す側の機械の点数づけ・総量規制などの法の上限は機械の検査・貸す側は体のない外の組織。
- C3 返済は口座から自動・不足したら延滞を記録し、契約と法に沿って機械が処理する。督促は本人に届き、どうするかは本人が
  決める。倒産と破産は経済の最後の段。

2-1 で作るのは貸付の行の器(``CreditBook``=種類・借り手・限度・残高・返済日・1 回の返済額・延滞の回数と額)と、「返済は口座
から自動・不足は延滞の記録」の関数(``repay_due``)だけ。**呼び手は無い**(ランの中で行は 1 つも足されない=試験だけが
呼ぶ)。審査と総量規制は 4-2 の規則の表(R-106 の E4 の後)を待つ(宣言)。借りる判断・督促・倒産と破産は後の段。

台帳の口: 返済は ``Ledger.transfer_many``(世帯の預金 → 銀行・科目「利子」=口座の方法)で払う=基本操作 ``ops.transfer``
だけが残高を書く(新しい書き手は作らない)。元本の返済の科目(借入の返済)は 12 科目に無い=2-1 では利子の科目に載せる
(器だけ・呼び手なし・**未リサーチ(expedient)**)。返済の流れ(世帯 → 銀行の利子)は保存則の検算の登録(``accounts.FLOW_REGISTRY``)
に入れていない=呼び手を作る段で登録する(今呼ぶと検算が「登録の無い流れ」で落ちる=試験が確かめる)。状態台帳の行 CR(軸 1 diag=読み手は manifest
だけ・軸 2 derivable=いつも空・中身は hash_skip)。

〔第 4 期 4-2〕総量規制の検査(:func:`total_volume_check`=貸金業法 13 条の 2 第 2 項・13 条 3 項=規則の表の
``credit.total_volume_cap``)と利息の上限(:func:`interest_cap_rate`=利息制限法 1 条=``credit.interest_cap``)を器に足した
(貸す側の機械の検査=決定 10-12 §4-11 C2)。**呼び手は無い**(借りる判断の段の後=結果不変)。除外と例外(規則 10 条の 21・
10 条の 23)の号ごとの要件は貸す側の判断が入る=入れていない。カードの枠(割賦販売法 30 条の 2 の 2=包括支払可能見込額 ×
大臣の定める割合)は割合の値が未確認=欄だけ(:data:`CARD_LIMIT_RATIO` は ``None``=空欄・台帳 ``DOC-rules42-card-limit-blank``)。

逐次ループ宣言: ``CreditBook.add`` は 1 行=定数時間(列の倍化は償却)。``repay_due`` は配列演算(返済日の行の数ぶんの
Python ループ無し)。``total_volume_check``・``interest_cap_rate`` は配列演算(上限の帯の数=3 ぶんのループ)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

import numpy as np

from shibuya.economy.accounts import AccountCode, Sector

__all__ = ["KINDS", "KIND_WORDS", "CARD", "MORTGAGE", "CONSUMER", "STORE_LOAN", "LENDER_SECTOR", "CreditBook",
           "repay_due", "CARD_LIMIT_RATIO", "TOTAL_VOLUME_KINDS", "total_volume_check", "interest_cap_rate"]

CARD: Final[int] = 0
MORTGAGE: Final[int] = 1
CONSUMER: Final[int] = 2
STORE_LOAN: Final[int] = 3
#: 貸付の種類(C1・並びが列のコード)。
KINDS: Final[tuple[int, ...]] = (CARD, MORTGAGE, CONSUMER, STORE_LOAN)
KIND_WORDS: Final[tuple[str, ...]] = ("カード", "住宅ローン", "消費者ローン", "店の借入")
#: 貸す側(C2「体のない外の組織」=銀行の部門の口 0)。
LENDER_SECTOR: Final[int] = int(Sector.BANK)
#: 〔第 4 期 4-2〕カードの枠の割合(割賦販売法 30 条の 2 の 2 の大臣の定める割合=R-118 §8 の 14=未確認=空欄)。
CARD_LIMIT_RATIO: Final[None] = None
#: 〔第 4 期 4-2〕総量規制の対象の貸付の種類(消費者ローン=貸金業者の個人向け。住宅ローンは除外=規則 10 条の 21・カードの
#: ショッピングは割賦販売法の側・店の借入は個人向けでない=金融庁 Q2-11〜Q2-13)。貸す側が貸金業者か銀行かは区別しない
#: (銀行のカードローンは対象外=未リサーチ(expedient)の区別なし・台帳 ``DOC-rules42-credit-lender-kind``)。
TOTAL_VOLUME_KINDS: Final[tuple[int, ...]] = (2,)

_COLS: Final[tuple[tuple[str, type], ...]] = (
    ("kind", np.int8), ("borrower_sector", np.int8), ("borrower", np.int32), ("limit", np.int64),
    ("balance", np.int64), ("due_day", np.int32), ("installment", np.int64), ("delinquent_count", np.int32),
    ("delinquent_amount", np.int64),
)


@dataclass
class CreditBook:
    """貸付の行の器(列ごとの配列)。2-1 では行を足す呼び手が無い(``capacity=0`` の空の器)。"""

    capacity: int = 0
    n: int = 0
    cols: dict[str, np.ndarray] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if int(self.capacity) < 0:
            raise ValueError("capacity は 0 以上")
        if not self.cols:
            self.cols = {name: np.zeros(int(self.capacity), dtype=t) for name, t in _COLS}
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, name: str, value: object) -> None:
        """〔検収 L1〕組み立ての後は行の数 ``n`` の外は書けない(``add`` だけが ``n`` を進める)。"""
        if getattr(self, "_sealed", False) and name != "n":
            raise AttributeError(f"CreditBook は組み立ての後は書けない({name})")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"CreditBook の属性は消せない({name})")

    def __len__(self) -> int:
        return int(self.n)

    def add(self, *, kind: int, borrower_sector: int, borrower: int, limit: int, balance: int, due_day: int,
            installment: int) -> int:
        """行を 1 つ足して番号を返す(審査と総量規制は 4-2 の規則の表の後=ここでは形だけ見る)。"""
        if int(kind) not in KINDS:
            raise ValueError(f"貸付の種類は {KINDS} のどれか(いま {kind!r})")
        if min(int(limit), int(balance), int(installment)) < 0 or int(balance) > int(limit):
            raise ValueError("限度・残高・返済額は 0 以上・残高は限度以下")
        i = int(self.n)
        if i >= self.cols["kind"].size:
            grow = max(1, 2 * self.cols["kind"].size)
            for name, t in _COLS:
                old = self.cols[name]
                new = np.zeros(grow, dtype=t)
                new[: old.size] = old
                self.cols[name] = new
        vals = {"kind": kind, "borrower_sector": borrower_sector, "borrower": borrower, "limit": limit,
                "balance": balance, "due_day": due_day, "installment": installment, "delinquent_count": 0,
                "delinquent_amount": 0}
        for name, v in vals.items():
            self.cols[name][i] = v
        self.n = i + 1
        return i

    def view(self, name: str) -> np.ndarray:
        """列の写し(行の数ぶん)。"""
        return self.cols[name][: self.n].copy()

    def record(self) -> dict[str, int]:
        """manifest の段階 2 の ``credit`` の欄(行の数と残高・延滞の合計=計器)。"""
        n = int(self.n)
        return {"rows": n, "balance": int(self.cols["balance"][:n].sum()) if n else 0,
                "delinquent_count": int(self.cols["delinquent_count"][:n].sum()) if n else 0,
                "delinquent_amount": int(self.cols["delinquent_amount"][:n].sum()) if n else 0}


def repay_due(book: CreditBook, ledger, day: int, step: int) -> dict[str, int]:  # noqa: ANN001
    """C3: 返済日の行の返済を口座から自動で払い、足りない行は延滞を記録する(**呼び手なし**=試験だけ)。

    返済の額=``min(1 回の返済額, 残高)``。借り手(世帯)の預金が足りる行だけを ``Ledger.transfer_many``(世帯 → 銀行・
    利子の科目・口座の方法)で払い、残高を減らす。足りない行は延滞の回数と額を足す(督促は本人に届く=後の段)。

    Returns:
        ``{"due", "paid", "paid_amount", "delinquent", "delinquent_amount"}``。
    """
    from shibuya.economy import ops as _OPS

    n = int(book.n)
    due = np.flatnonzero(book.cols["due_day"][:n] == int(day))
    hh = due[book.cols["borrower_sector"][due] == _OPS.ACCOUNT_SECTOR]
    amt = np.minimum(book.cols["installment"][hh], book.cols["balance"][hh]).astype(np.int64)
    hh, amt = hh[amt > 0], amt[amt > 0]
    out = {"due": int(due.size), "paid": 0, "paid_amount": 0, "delinquent": 0, "delinquent_amount": 0}
    if hh.size == 0:
        return out
    who = book.cols["borrower"][hh].astype(np.int64)
    status = np.asarray(ledger.transfer_many(
        _OPS.ACCOUNT_SECTOR, who, LENDER_SECTOR, np.zeros(who.size, dtype=np.int64), amt,
        int(AccountCode.INTEREST), int(step), method=_OPS.METHOD_ACCOUNT))
    ok = status == 0
    book.cols["balance"][hh[ok]] -= amt[ok]
    book.cols["delinquent_count"][hh[~ok]] += 1
    book.cols["delinquent_amount"][hh[~ok]] += amt[~ok]
    out.update(paid=int(ok.sum()), paid_amount=int(amt[ok].sum()), delinquent=int((~ok).sum()),
               delinquent_amount=int(amt[~ok].sum()))
    return out


def total_volume_check(annual_income: np.ndarray, balance_all: np.ndarray, balance_this_lender: np.ndarray,
                       amount: np.ndarray, asof: str) -> dict[str, np.ndarray | str | None]:
    """〔第 4 期 4-2〕総量規制の検査(貸す側の機械の検査・**呼び手なし**=器)。

    ``annual_income``=年収など・``balance_all``=総量規制の対象の借入れの残高の合計(他社を含む)・``balance_this_lender``=この
    貸し手の残高・``amount``=新しく貸す額(どれも行ごとの円)。規則の表 ``credit.total_volume_cap`` の ``asof`` の日の版で:

    - ``ok``: 借入れの合計(残高+新しい額)が年収などの 3 分の 1 以下(超えれば貸せない=借り手は処罰されない=Q2-2・Q2-3)。
    - ``document``: 収入の書類が要るか(この貸し手で 50 万円超、または他社と合わせて 100 万円超=13 条 3 項)=**欄だけ**
      (書類の有無は本人の持ち物の段の後)。

    行が無い日は ``ok`` 全部真・``document`` 全部偽・``source`` ``"none"``。
    """
    from shibuya.economy import taxes as _TX

    inc = np.asarray(annual_income, dtype=np.int64)
    tot = np.asarray(balance_all, dtype=np.int64) + np.asarray(amount, dtype=np.int64)
    one = np.asarray(balance_this_lender, dtype=np.int64) + np.asarray(amount, dtype=np.int64)
    cap = _TX.total_volume_cap(asof)
    if cap is None:
        return {"ok": np.ones(inc.shape, dtype=bool), "document": np.zeros(inc.shape, dtype=bool), "source": "none"}
    r = cap["ratio"]
    ok = tot * int(r.denominator) <= inc * int(r.numerator)
    doc = (one > int(cap["document_over_single"])) | (tot > int(cap["document_over_all"]))
    return {"ok": ok, "document": doc, "source": cap["source"]}


def interest_cap_rate(principal: np.ndarray, asof: str) -> tuple[np.ndarray, str]:
    """〔第 4 期 4-2〕利息制限法 1 条の年率の上限(元本の帯ごと・分母 10,000 の整数=万分率)と出どころ(**呼び手なし**=器)。

    契約の利率が上限を超える部分は無効=機械が上限に置き換える側(R-118 §3 の 2)。行が無い日は −1(上限なし)と ``"none"``。
    """
    from shibuya.economy import taxes as _TX

    p = np.asarray(principal, dtype=np.int64)
    cap = _TX.interest_cap(asof)
    out = np.full(p.shape, -1, dtype=np.int64)
    if cap is None:
        return out, "none"
    for lo, hi, rate in cap["bands"]:  # 逐次ループ宣言: 上限の帯の数(3)
        m = (p >= lo) & ((p < hi) if hi is not None else True)
        out[m] = int(rate * 10_000)
    return out, str(cap["source"])
