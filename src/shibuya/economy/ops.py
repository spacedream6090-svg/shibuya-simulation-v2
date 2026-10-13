"""economy.ops — お金の基本操作「移す」(第 1 期 1-9・CP2 の段階 1・A 湧かないもの)。

口の約束: ``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-9 お金の基本操作」。決定 10-12 §4-5 CP1・CP2・
CP3(湧かないものは移すだけ・保存則は基本操作の中で守る)。回答 10-13b §3(K17)。

- 基本操作は **``transfer(ledger, src, dst, amount, what, cause, t_ns) -> TransferId`` の 1 つ**。
  ``src``/``dst`` は口の id=``(部門, 索引)``(索引は整数か整数の配列)。外界・銀行・政府(faucet/sink)も部門の口として
  持つ=湧かせない(許された組だけ=``accounts.is_allowed``・参入資本の出所=``ENTRY_CAPITAL_PAYERS``)。``amount`` は
  正の整数の円(配列なら行ごと)。``what`` は 1-3 の語彙の族「金」の語(``"金:消費支出"`` など=科目)。``cause`` は 1-3 の
  原因(``LlmCall``・``Process``・実験の条件)か ``None``。``t_ns`` は通しの時刻(ナノ秒)。
- 帳簿の口(``economy.ledger.Ledger`` の ``transfer``・``transfer_many``・``purchase_many``・``endow_households``・
  ``endow_stores``・``depreciate`` と、それを呼ぶ ``GoodsLedger.restock_many`` の代金・``RailProcess.pay_fares``)は
  検査(業務の失敗=残高不足などを行ごとの状態で返す)をしてから、通った行をここへ渡す。**残高・流れの表・生ログを
  書くのはこの関数だけ**(AST の試験 ``tests/economy/cp2/test_cp2_transfer_only_writer.py``)。

約束(先例: TigerBeetle の「口の残高は transfer でしか変わらない・transfer は変更も削除もできない記録」=形だけ借りた・
Apache-2.0・R-113 §10):

1. 1 行は 2 脚(借方と貸方が同じ額)。``預金純増`` は現金↔預金の振替の 2 脚目(銀行側は借入=預金負債)も書く(四重記入)。
   ``減価償却`` は自己ループ(固定資産だけが減る・現金は動かない・相手は同じ口)。
2. 前提が崩れていたら例外(口が先に検査する=ここに来るのはプログラムの誤り): 語彙の外の ``what``・移せない科目
   (退蔵項)・許されない組・参入資本の出所・範囲の外の索引・0 以下の額・世帯の現金(``agents.money``)が書けない
   (resolve の書き込み窓の外)。
3. 生ログ(輪)へ 1 行ずつ追記。輪が溢れたら**古い行を上書きして続け**、上書きで失った行の数を計器に数える
   (K17=回答 10-13b §3「溢れたら記録して続ける」。先例 Linux ftrace の overrun・OTel の「捨てた数を必ず出す」)。
4. 出来事(1-3): ``cause`` を渡すと 1 行ごとに 1 件 ``EventLog.append(Event(what, cause, how_much=額, who=払い手,
   whom=受け手, where=店なら POI))`` を書き、その id ``(t_ns, seq)`` を生ログの目印の列に入れる。``cause`` が ``None``
   の行・記録が無い/off のときは書かず、目印は空(``-1``)。原因の無い行の数は計器に出る。
   **economy は ``engine.events`` を import しない**(層の契約 forbidden「economy → llm」: 語彙表が ``llm.contract`` を読む)。
   出来事を書くのは engine の側の口 ``engine.events.links.MoneyEventLink``(``LedgerBundle.attach_events`` が作って台帳に
   挿す=1-3 の ``ActualLogLink`` と同じ依存逆転)。金の語は族の名「金」と科目の名から作る(1-3 の語彙表と同じことは試験が
   突き合わせる)。
5. 計器 ``TransferMeter``(状態台帳の行 ``A``=軸 1 diag・軸 2 discardable): 行数・額・原因の無い行・出来事の行・溢れ。
   1 日の締め(``Ledger.on_day_end``)で「その日の transfer の額の和=流れの表の和」を検算する(新しい検算 1 本)。
6. 順(検収 L5): 検査 → 出来事を書く → 金を書く(記録の口が例外を出したとき、金だけが動いた状態を残さない)。
   台帳の配列を書く窓(``Ledger._unlocked``)を開けるのはこの関数だけ(検収 M2・AST の試験 ``test_cp2_write_window.py``)。
   減価償却(自己ループ)の入口は ``Ledger.depreciate`` だけ(汎用の口は行の状態 FORBIDDEN_PAIR で返す=検収 M1)。

逐次ループ宣言: 出来事を 1 行ずつ書くループ(原因を渡した行の数ぶん・``EventLog.append`` が 1 行の口だから=1-3 の
``ActualLogLink`` と同じ)。ほかは numpy のベクトル演算(行数・個体数ぶんの Python ループ無し)。

**未リサーチ(expedient)**: 口の名の書き方(世帯=体の id・ほかは ``"部門:索引"``)・``where`` は店の側の POI だけ・
計器の欄。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final, Mapping, NamedTuple

import numpy as np

from shibuya.economy.accounts import (
    ACCOUNT_NAMES,
    ENTRY_CAPITAL_PAYERS,
    NON_TRANSFERABLE,
    SECTOR_NAMES,
    AccountCode,
    BalanceLine,
    Sector,
    is_allowed,
)

if TYPE_CHECKING:  # 循環を避ける(ledger.py がこのモジュールを読む)
    from shibuya.economy.ledger import Ledger

__all__ = [
    "TransferId",
    "TransferMeter",
    "MONEY_FAMILY",
    "CAUSE_KINDS",
    "MONEY_WHAT",
    "MONEY_PATHS",
    "MONEY_ATTRS",
    "NO_EVENT",
    "what_of",
    "account_name",
    "transfer",
]

#: 目印の列の空の値(出来事を書かなかった行)。
NO_EVENT: Final[int] = -1


class TransferId(NamedTuple):
    """``transfer`` の戻り=生ログの通し番号の範囲 ``[first, first + n)``(1 行=1 つの transfer の記録)。"""

    first: int
    n: int


#: 1-3 の語彙の族「金」の名(``engine.events.vocab.FAMILY_MONEY`` と同じ=試験が突き合わせる)。
MONEY_FAMILY: Final[str] = "金"
#: 1-3 の原因の種類の名(``engine.events.log.CAUSE_KINDS`` と同じ=試験が突き合わせる)。型は記録の口が確かめる。
CAUSE_KINDS: Final[tuple[str, ...]] = ("llm_call", "process", "experiment")
#: 金の語(1-3 の語彙の族「金」・``"金:<科目>"``)→ 科目。語彙表と科目の表は並びまで同じ(1-3 の試験が突き合わせる)。
MONEY_WHAT: Final[Mapping[str, AccountCode]] = MappingProxyType(
    {f"{MONEY_FAMILY}:{ACCOUNT_NAMES[int(c)]}": c for c in AccountCode}
)

#: お金の列(状態台帳の金の道筋=CP1 の A〜D のうち C 金)。**書き手は ``transfer`` だけ**(AST の試験が見る範囲)。
#: 値は中身。属性の名は ``MONEY_ATTRS``(道筋の末尾)。
MONEY_PATHS: Final[Mapping[str, str]] = MappingProxyType({
    "agents.money": "世帯の現金(帳簿の世帯の現金の行と同じ配列=Ledger.attach_household_cash)",
    "pois.revenue": "店の売上の写し(診断・保存則の検査とラン要約だけが読む)",
    "ledger.money._lines": "帳簿の残高(現金・預金・在庫・固定資産・借入 × 6 部門)",
    "ledger.money._flow": "その日の取引の流れの表(部門 × 部門 × 科目)",
    "ledger.money._last_change_day": "部門ごとの最後に現金/預金が動いた日(退蔵項の素材)",
    "ledger.money._raw_*": "生ログの輪(7 列+目印の 2 列)と位置(_raw_pos・_raw_head)",
})
#: AST の試験が見る属性の名(``_raw_`` で始まる名も全部)。
MONEY_ATTRS: Final[frozenset[str]] = frozenset({"money", "revenue", "_lines", "_flow", "_last_change_day"})
#: 生ログの属性の頭(``_raw_tick``・``_raw_pos`` など)。
MONEY_ATTR_PREFIX: Final[str] = "_raw_"


def what_of(code: int) -> str:
    """科目 → 金の語(``"金:消費支出"``)。"""
    return f"{MONEY_FAMILY}:{ACCOUNT_NAMES[int(code)]}"


def account_name(sector: int, index: int) -> int | str:
    """出来事の ``who``/``whom`` に書く口の名(世帯=体の id・ほかは ``"部門:索引"``・未リサーチ(expedient))。"""
    if int(sector) == int(Sector.HOUSEHOLD):
        return int(index)
    return f"{SECTOR_NAMES[int(sector)]}:{int(index)}"


@dataclass
class TransferMeter:
    """``transfer`` の計器(状態台帳の行 ``A``=軸 1 diag・軸 2 discardable=再開のランは 0 から数える)。

    ``rows``・``amount``・``uncaused``・``events``・``overflow`` はこのランの積算。``day_*`` はその日の分(日の締めで
    ``last_day`` に移して 0 に戻す)。``flow_base`` はその日の流れの表の和の起点(最初の transfer のときに決める=
    日の途中から再開したランでも検算が成り立つ)。
    """

    rows: int = 0
    amount: int = 0
    uncaused: int = 0
    events: int = 0
    overflow: int = 0
    day_rows: int = 0
    day_amount: int = 0
    day_uncaused: int = 0
    day_events: int = 0
    day_overflow: int = 0
    flow_base: int | None = None
    last_day: dict[str, Any] = field(default_factory=dict)

    def close_day(self, day: int, flow_sum: int) -> dict[str, Any]:
        """日の締め: その日の transfer の額の和=流れの表の和(起点からの増え)を検算し、日の欄を 0 に戻す。"""
        base = int(flow_sum) if self.flow_base is None else int(self.flow_base)
        expect = base + int(self.day_amount)
        out = {
            "day": int(day),
            "rows": int(self.day_rows),
            "amount": int(self.day_amount),
            "flow_sum": int(flow_sum),
            "flow_sum_ok": bool(int(flow_sum) == expect),
            "overflow": int(self.day_overflow),
            "uncaused": int(self.day_uncaused),
            "event_rows": int(self.day_events),
        }
        self.day_rows = self.day_amount = self.day_uncaused = self.day_events = self.day_overflow = 0
        self.flow_base = 0  # 締めで流れの表は 0 に戻る
        self.last_day = out
        return out


def _account(ledger: "Ledger", ref: Any, name: str) -> tuple[int, np.ndarray]:
    """口の id ``(部門, 索引)`` → (部門, 索引の 1 次元の int64 配列)。"""
    try:
        s, idx = ref
    except (TypeError, ValueError):
        raise ValueError(f"transfer の {name} は (部門, 索引) の組(いま {ref!r})") from None
    s = int(s)
    if not 0 <= s < len(ledger.sizes):
        raise ValueError(f"transfer の {name} の部門が範囲の外: {s}")
    i = np.asarray(idx, dtype=np.int64).ravel()
    return s, i


def transfer(
    ledger: "Ledger",
    src: Any,
    dst: Any,
    amount: Any,
    what: str,
    cause: Any,
    t_ns: int,
) -> TransferId:
    """**基本操作「移す」**(お金・A 湧かないもの)。``src`` から ``dst`` へ ``amount`` 円を移し、生ログに記録する。

    Args:
        ledger: 帳簿(``economy.ledger.Ledger``)。
        src: 払い手の口 ``(部門, 索引)``(索引は整数か配列)。
        dst: 受け手の口 ``(部門, 索引)``(``src`` と同じ行数)。
        amount: 正の整数の円(行ごと)。
        what: 金の語(``MONEY_WHAT`` の鍵)。
        cause: 1-3 の原因か ``None``(``None`` の行は出来事を書かない)。
        t_ns: 通しの時刻(ナノ秒・刻みの頭)。

    Returns:
        生ログの通し番号の範囲 ``TransferId(first, n)``。

    Raises:
        ValueError: 前提が崩れている(口が先に検査する=プログラムの誤り)・世帯の現金が書き込み窓の外。
        TypeError: ``cause`` が 1-3 の 3 型でも ``None`` でもない。
    """
    code = MONEY_WHAT.get(what) if isinstance(what, str) else None
    if code is None:
        raise ValueError(f"transfer の what は金の語(語彙 1-3 の族「金」): {what!r}")
    if code in NON_TRANSFERABLE:
        raise ValueError(f"移せない科目: {what}")
    ps, p = _account(ledger, src, "src")
    qs, q = _account(ledger, dst, "dst")
    a = np.asarray(amount, dtype=np.int64).ravel()
    k = int(a.size)
    if not (p.size == q.size == k):
        raise ValueError(f"transfer の行数が揃っていない: {p.size} / {q.size} / {k}")
    if cause is not None and getattr(cause, "kind", None) not in CAUSE_KINDS:
        raise TypeError(f"transfer の cause は 1-3 の原因の 3 型か None(いま {type(cause)!r})")
    first = int(ledger._raw_pos)
    if k == 0:
        return TransferId(first, 0)
    if bool((a <= 0).any()):
        raise ValueError("transfer の amount は正の整数の円")
    if code == AccountCode.ENTRY_CAPITAL and Sector(ps) not in ENTRY_CAPITAL_PAYERS:
        raise ValueError(f"参入資本の出所が許されない(ex nihilo): {Sector(ps).name}")
    if not is_allowed(int(code), ps, qs):
        raise ValueError(f"許されない組: {what} {Sector(ps).name} → {Sector(qs).name}")
    n_p, n_q = ledger.sizes[ps], ledger.sizes[qs]
    if int(p.min()) < 0 or int(p.max()) >= n_p or int(q.min()) < 0 or int(q.max()) >= n_q:
        raise ValueError("transfer の索引が範囲の外")
    self_loop = code == AccountCode.DEPRECIATION
    if self_loop and (ps != qs or not np.array_equal(p, q)):
        raise ValueError("減価償却は自己ループ(src と dst が同じ口)")
    t = int(t_ns)
    step_ns = int(ledger._step_ns)
    step = t // step_ns
    if step * step_ns != t:
        raise ValueError(f"transfer の t_ns が刻みの頭でない: {t}(刻み {step_ns} ns)")

    with ledger._unlocked():  # 台帳の窓を開けるのはこの関数だけ(検収 M2・AST の試験 test_cp2_write_window.py)
        lines = ledger._lines
        # ---- 1. 検査の残り: 世帯の現金(agents.money=resolve の書き込み窓)が書けるか。窓を開けた後に見る(台帳の配列は
        #         窓の中で書ける・採用した世帯の現金の旗は resolve が持つ)。np.add.at は writeable=False を無視して書けて
        #         しまう(numpy 2.5 実測)ので自前で見る ----
        if not self_loop:
            for sector in (ps, qs):
                if not lines[int(BalanceLine.CASH)][sector].flags.writeable:
                    raise ValueError(
                        f"部門 {Sector(sector).name} の現金配列が読み取り専用: "
                        "resolve の writable ブロックの外から transfer を呼んでいる"
                    )

        # ---- 2. 出来事(1-3)。金を書く前に書く(検収 L5: 記録の口が例外を出したとき金だけが動かない) ----
        sink = ledger._events
        if cause is None or sink is None or not sink.enabled:
            ev_t = ev_s = None
            n_ev = 0
        else:
            store_p, store_q = ps == int(Sector.STORE), qs == int(Sector.STORE)
            pl, ql = p.tolist(), q.tolist()
            who = [account_name(ps, x) for x in pl]  # 逐次ループ宣言: 原因を渡した行の数ぶん
            whom = [account_name(qs, x) for x in ql]
            where = [("poi", y) if store_q else (("poi", x) if store_p else None) for x, y in zip(pl, ql)]
            ev_t, ev_s = sink(what, cause, t, who, whom, where, a)
            n_ev = int(np.count_nonzero(np.asarray(ev_s) >= 0))

        # ---- 3. 金(残高・流れの表・最後に動いた日・取引の件数) ----
        if self_loop:
            # 自己ループ: 固定資産だけが減る(現金・最後に動いた日・取引の件数は動かさない=HEAD の depreciate と同じ)
            np.add.at(lines[int(BalanceLine.FIXED_ASSET)][ps], p, -a)
        else:
            cash_p = lines[int(BalanceLine.CASH)][ps]
            cash_q = lines[int(BalanceLine.CASH)][qs]
            np.add.at(cash_p, p, (-a).astype(cash_p.dtype))
            np.add.at(cash_q, q, a.astype(cash_q.dtype))
            if code == AccountCode.DEPOSIT_NET:
                # 四重記入の 2 脚目: 現金↔預金の振替(銀行側は預金負債=借入の行)
                dep = lines[int(BalanceLine.DEPOSIT)]
                loan = lines[int(BalanceLine.LOAN)]
                if Sector(qs) == Sector.BANK:  # 預入
                    np.add.at(dep[ps], p, a)
                    np.add.at(loan[qs], q, a)
                else:  # 引出(銀行 → 預金者)
                    np.add.at(dep[qs], q, -a)
                    np.add.at(loan[ps], p, -a)
            last = ledger._last_change_day
            last[ps][p] = np.int32(ledger._day)
            last[qs][q] = np.int32(ledger._day)
            ledger.n_transfers += k
        meter = ledger.meter
        if meter.flow_base is None:
            meter.flow_base = int(ledger._flow.sum())
        total = int(a.sum())
        ledger._flow[ps, qs, int(code)] += total

        # ---- 4. 生ログ(輪)と目印の列。D-R2-6: 保持窓を超えた分は日次の集約行に畳む・K17: 溢れたら上書きして数える ----
        cap = ledger._raw_tick.size
        pos = first + np.arange(k, dtype=np.int64)
        slot = pos % cap
        ledger._raw_tick[slot] = np.int32(step)
        ledger._raw_ps[slot] = np.int8(ps)
        ledger._raw_pi[slot] = p.astype(np.int32)
        ledger._raw_qs[slot] = np.int8(qs)
        ledger._raw_qi[slot] = q.astype(np.int32)
        ledger._raw_amt[slot] = a
        ledger._raw_code[slot] = np.int8(int(code))
        if ev_s is None:  # 出来事の無い行は空(輪の使い回しで前の周の id を残さない)
            ledger._raw_event_t_ns[slot] = NO_EVENT
            ledger._raw_event_seq[slot] = NO_EVENT
        else:
            ledger._raw_event_t_ns[slot] = ev_t
            ledger._raw_event_seq[slot] = ev_s
        ledger._raw_pos += k
        overflow = 0
        if ledger._raw_pos - ledger._raw_head > cap:
            overflow = (ledger._raw_pos - ledger._raw_head) - cap
            ledger._raw_head += overflow
            ledger.n_raw_dropped += int(overflow)

    meter.rows += k
    meter.amount += total
    meter.overflow += int(overflow)
    meter.events += n_ev
    meter.day_rows += k
    meter.day_amount += total
    meter.day_overflow += int(overflow)
    meter.day_events += n_ev
    if cause is None:
        meter.uncaused += k
        meter.day_uncaused += k
    return TransferId(first, k)
