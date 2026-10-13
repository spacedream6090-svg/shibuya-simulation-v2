"""第 1 期 1-9(CP2 の段階 1): 帳簿の 9 口を基本操作 ``transfer`` に載せ替えても、同じ残高・同じ台帳の行(結果不変 ◎)。

口の約束 1-9 の受入の試験 ``test_cp2_nine_ops_equivalence.py``。比べる相手は載せ替えの前(HEAD ``136fdbb``)の
``economy/ledger.py``・``economy/goods.py`` の写し(``head_copies.py``・blob の名で同じことを確かめる)。

帳簿の 9 口(10b-prep §3-2 の E1〜E9): 金の口 E1 ``purchase_many``・E2 ``transfer_many``(と 1 件の ``transfer``)・
E3 ``endow_households``・E4 ``endow_stores``(+ ``depreciate``)は ``ops.transfer`` を呼ぶ。物の口 E5 ``restock_many`` の
代金は E2 を通る。E6 ``sell_many``・E7 ``to_bin_many``・E8 ``collect_waste``・E9 ``consume_many`` は金を動かさない
(物の行に目印の列を足しただけ)。

1. 乱数で作った口の呼び出しの列(不正な行・足りない残高・溢れる小さな輪・日の締め・預金の 2 脚目・減価償却・評価替え
   ・物の口と代金)を HEAD と今の台帳に同じ順に流し、毎回の戻り値と全部の状態(残高・流れ・締め・生ログの中身と位置・
   計数・state_hash・物の在庫と納品ログ)が同じ。
2. 出来事の記録を挿して原因を渡しても、金と物の状態は同じ(記録は状態を変えない)。
3. (slow・data)5,000 体 mock の 1 日(既定 v3)を HEAD の台帳と今の台帳で回し、final・呼数・残高・生ログ・物の台帳が同じ。
   輪の係数を両方 6.5(溢れない)と両方 3.0(HEAD の既定=溢れる)の 2 通り。

〔独立検収 M1・宣言つきの直し〕汎用の口(``transfer``・``transfer_many``)に科目「減価償却」を渡すと、HEAD は現金の脚で
動かしていた(別の口なら現金が移る・同じ口なら差し引き 0 で取引の件数だけ増える=減価償却は「現金を動かさない」に反する
潜在の欠陥)。1-9 は行の状態 FORBIDDEN_PAIR で返す(例外にしない・状態は却下の計数だけ動く)。自己ループの入口は
``depreciate`` だけ。engine からの呼び手は無い=到達しない入力。この入力だけは HEAD と値が違うので、乱数の列では汎用の口に
減価償却を渡さず、決定的な試験 3 本(検収役の seed 5012・5030・5098 で落ちた 3 つの形)で HEAD との違いと 1-9 の値を固定する。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.economy.accounts import AccountCode, BalanceLine, Sector
from shibuya.economy.goods import GoodsLedger
from shibuya.economy.ledger import Ledger
from shibuya.engine.events.links import MoneyEventLink
from shibuya.engine.events.log import EventLog, Process
from shibuya.engine.ledger_api import EntityRef
from tests.economy.cp2 import head_copies as CP

H, S, E, B, G, W = (int(Sector.HOUSEHOLD), int(Sector.STORE), int(Sector.EMPLOYER), int(Sector.BANK),
                    int(Sector.GOVERNMENT), int(Sector.ROW))


def test_the_copies_are_the_head_blobs():
    for name, sha in CP.BLOBS.items():
        assert CP.blob_sha(CP.HERE / name) == sha, name


# ---------------------------------------------------------------- 1. 乱数の呼び出しの列
def _norm(x):  # noqa: ANN001, ANN202
    """戻り値を比べられる形に(配列 → list・締めの dataclass と辞書 → 中身)。"""
    import dataclasses

    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, np.ndarray) or isinstance(x, np.generic):
        return np.asarray(x).tolist()
    if dataclasses.is_dataclass(x):
        return {f.name: _norm(getattr(x, f.name)) for f in dataclasses.fields(x)}
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_norm(v) for v in x]
    return repr(x)


class _Pair:
    """HEAD と今の台帳(金・物)を同じ形で作り、同じ呼び出しを流して比べる。"""

    def __init__(self, seed: int, *, cap: int, retention: int, events: bool = False) -> None:
        self.rng = np.random.default_rng(seed)
        HL, HG, _ = CP.shims()
        self.sizes = (int(self.rng.integers(3, 9)), int(self.rng.integers(2, 6)), int(self.rng.integers(1, 4)))
        nh, ns, ne = self.sizes
        self.old = HL(nh, ns, ne, raw_capacity=cap, retention_days=retention)
        self.new = Ledger(nh, ns, ne, raw_capacity=cap, retention_days=retention)
        self.m_old = np.zeros(nh, dtype=np.int32)
        self.m_new = np.zeros(nh, dtype=np.int32)
        self.old.attach_household_cash(self.m_old)
        self.new.attach_household_cash(self.m_new)
        cats = self.rng.integers(0, 3, ns)
        stock = self.rng.integers(0, 12, ns)
        price = self.rng.integers(100, 900, ns)
        self.g_old = HG.from_pois(cats, stock, price, n_agents=nh, delivery_capacity=cap)
        self.g_new = GoodsLedger.from_pois(cats, stock, price, n_agents=nh, delivery_capacity=cap)
        self.log = None
        if events:
            self.log = EventLog()
            self.new.attach_events(MoneyEventLink(self.log), step_seconds=60)
        self.step = 0
        self.day = 0
        self.n_calls = 0

    # 同じ呼び出しを両方へ(戻り値か例外の型を比べる)
    def call(self, name: str, *args, cause=None, goods: bool = False, **kw):  # noqa: ANN001, ANN201
        res = []
        for led, g in ((self.old, self.g_old), (self.new, self.g_new)):
            obj = g if goods else led
            kk = dict(kw)
            if "money" in kk:
                kk["money"] = led
            if cause is not None:  # HEAD の写しの子クラスは捨てる(HEAD の口は原因を知らない)
                kk["cause"] = cause
            try:
                res.append(("ok", _norm(getattr(obj, name)(*args, **kk))))
            except Exception as e:  # noqa: BLE001
                res.append(("err", type(e).__name__))
        assert res[0] == res[1], (name, res)
        self.n_calls += 1
        return res[1]

    def check(self) -> None:
        bad = CP.diff(CP.money_state(self.old), CP.money_state(self.new))
        assert bad == [], bad
        assert np.array_equal(self.m_old, self.m_new)
        bad = CP.diff(CP.goods_state(self.g_old), CP.goods_state(self.g_new))
        assert bad == [], bad

    def _idx(self, s: int, n: int) -> np.ndarray:
        size = (self.sizes + (1, 1, 1))[s]
        return self.rng.integers(-1, size + 1, n)  # 範囲の外を混ぜる

    def run(self, n_ops: int) -> None:
        rng = self.rng
        # 汎用の口に減価償却は渡さない(検収 M1=宣言つきの直しで HEAD と値が違う入力・決定的な試験 3 本が受け持つ)
        codes = [int(c) for c in AccountCode if c != AccountCode.DEPRECIATION] + [99]
        nh, ns, _ne = self.sizes
        self.call("endow_households", rng.integers(1_000, 50_000, nh), 0, cause=Process("rail"))
        self.call("endow_stores", rng.integers(10_000, 90_000, ns), 0)
        self.check()
        for _ in range(n_ops):
            self.step += int(rng.integers(0, 3))
            op = int(rng.integers(0, 14))
            cause = Process("shelf") if rng.random() < 0.5 else None
            if op == 0:
                k = int(rng.integers(0, 5))
                self.call("purchase_many", self._idx(H, k), self._idx(S, k), rng.integers(-5, 3_000, k), self.step,
                          cause=cause)
            elif op == 1:
                ps, qs = int(rng.integers(0, 6)), int(rng.integers(0, 6))
                k = int(rng.integers(0, 6))
                self.call("transfer_many", ps, self._idx(ps, k), qs, self._idx(qs, k), rng.integers(-3, 4_000, k),
                          int(rng.choice(codes)), self.step, cause=cause)
            elif op == 2:
                ps, qs = int(rng.integers(0, 6)), int(rng.integers(0, 6))
                amt = int(rng.integers(-2, 5_000))
                self.call("transfer", EntityRef(ps, int(self._idx(ps, 1)[0])), EntityRef(qs, int(self._idx(qs, 1)[0])),
                          amt, int(rng.choice(codes)), self.step, cause=cause)
            elif op == 3:  # 預金の 2 脚目(預入・引出)
                k = int(rng.integers(1, 4))
                if rng.random() < 0.5:
                    self.call("transfer_many", H, self._idx(H, k), B, np.zeros(k, np.int64), rng.integers(1, 2_000, k),
                              int(AccountCode.DEPOSIT_NET), self.step, cause=cause)
                else:
                    self.call("transfer_many", B, np.zeros(k, np.int64), H, self._idx(H, k), rng.integers(1, 2_000, k),
                              int(AccountCode.DEPOSIT_NET), self.step, cause=cause)
            elif op == 4:
                s = int(rng.choice([H, S, E, B, W]))
                k = int(rng.integers(0, 4))
                self.call("depreciate", s, self._idx(s, k), rng.integers(-5, 900, k), self.step, cause=cause)
            elif op == 5:
                s = int(rng.choice([S, H]))
                n = (self.sizes + (1, 1, 1))[s]
                self.call("revalue_inventory", s, rng.integers(0, 9_000, n))
            elif op == 6:
                self.call("endow_stores", rng.integers(-5, 9_000, ns), self.step,
                          payer=Sector(int(rng.choice([W, H, B, S]))), cause=cause)
            elif op == 7:
                k = int(rng.integers(0, 4))
                self.call("restock_many", self._idx(S, k), rng.integers(-1, 6, k), self.step, goods=True,
                          money=True, slot=rng.integers(-1, 4, k), cause=cause)
            elif op == 8:
                self.call("sell_many", self._idx(S, int(rng.integers(0, 5))), self.step, goods=True)
            elif op == 9:
                k = int(rng.integers(0, 3))
                self.call("to_bin_many", self._idx(S, k), rng.integers(0, 3, k), self.step, goods=True,
                          slot=rng.integers(0, 3, k))
            elif op == 10:
                self.call("collect_waste", None if rng.random() < 0.5 else self._idx(S, 2), self.step, goods=True)
            elif op == 11:
                k = int(rng.integers(0, 3))
                self.call("consume_many", rng.integers(-1, 6, k), rng.integers(0, 3, k), self.step, goods=True)
            elif op == 12 and rng.random() < 0.3:  # 日の締め(金と物)
                self.call("on_day_end", self.day)
                self.call("on_day_end", self.day, goods=True)
                self.day += 1
            elif op == 13:  # 世帯の現金が書けない(resolve の書き込み窓の外)=両方 ValueError・何も書かない
                self.m_old.flags.writeable = False
                self.m_new.flags.writeable = False
                self.call("endow_households", rng.integers(1, 100, nh), self.step)
                self.m_old.flags.writeable = True
                self.m_new.flags.writeable = True
            self.check()


@pytest.mark.parametrize("seed", list(range(24)) + [5012, 5030, 5098])
def test_random_port_sequences_match_head(seed):
    p = _Pair(seed, cap=int((seed % 4) * 16 + 12), retention=1 + seed % 2)
    p.run(160)
    assert p.n_calls > 100


@pytest.mark.parametrize("seed", range(6))
def test_events_on_do_not_change_the_ledgers(seed):
    """出来事の記録を挿して原因を渡しても、金と物の状態は HEAD と同じ(記録は状態を変えない)。"""
    p = _Pair(100 + seed, cap=40, retention=1, events=True)
    p.run(120)
    assert p.log is not None and p.log.n_appended > 0


def test_overflowing_ring_is_identical_and_counted():
    """小さな輪で溢れさせても HEAD と同じ行が残り、溢れた行の数は計器にも出る(K17: 記録して続ける)。"""
    p = _Pair(7, cap=12, retention=3)
    p.run(200)
    assert p.new.n_raw_dropped > 0
    assert p.new.meter.overflow > 0
    assert p.new.meter.overflow <= p.new.n_raw_dropped  # 落ちた行=溢れ+保持窓


# ---------------------------------------------------------------- 3. 5,000 体 mock の 1 日(slow・data)
def _mock_day(monkeypatch, *, head: bool, rate: float):
    from shibuya import cli
    from shibuya.economy import ledger as LED

    HL, HG, HW = CP.shims()
    monkeypatch.setattr(LED, "TRANSFERS_PER_AGENT_PER_DAY", rate)
    monkeypatch.setattr(CP.head_ledger_module(), "TRANSFERS_PER_AGENT_PER_DAY", rate)
    if head:
        monkeypatch.setattr(cli, "Ledger", HL)
        monkeypatch.setattr(cli, "_HouseholdWalletLedger", HW)
        monkeypatch.setattr(cli, "GoodsLedger", HG)
    res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", vocab_version="v3")
    monkeypatch.undo()
    led = res.ledger
    return res, led


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
@pytest.mark.parametrize("rate", [6.5, 3.0])
def test_5k_mock_day_matches_head(monkeypatch, rate):
    res_h, led_h = _mock_day(monkeypatch, head=True, rate=rate)
    res_n, led_n = _mock_day(monkeypatch, head=False, rate=rate)
    assert type(led_h.money).__module__ != type(led_n.money).__module__  # 本当に HEAD の台帳で回した
    assert res_h.final_hash == res_n.final_hash
    assert res_h.llm_calls == res_n.llm_calls
    assert CP.diff(CP.money_state(led_h.money), CP.money_state(led_n.money)) == []
    assert CP.diff(CP.goods_state(led_h.goods), CP.goods_state(led_n.goods)) == []
    assert np.array_equal(res_h.agents.registry.money, res_n.agents.registry.money)
    m = led_n.money
    if rate == 6.5:
        assert m.n_raw_dropped == 0 and m.meter.overflow == 0  # K17: 溢れ 0 件
    else:
        assert m.meter.overflow == m.n_raw_dropped > 0  # 旧い係数では溢れる(数えて続ける・値は HEAD と同じ)


# ---------------------------------------------------------------- 4. 検収 M1: 汎用の口の減価償却(宣言つきの直し)
def _three_stores():
    """店 3 軒に参入資本 1,000 円ずつ(検収の決定的な 3 例と同じ形)。HEAD の写しと今の台帳。"""
    HL, _HG, _HW = CP.shims()
    old, new = HL(2, 3), Ledger(2, 3)
    for led in (old, new):
        led.endow_stores(np.full(3, 1_000), 0)
    return old, new


DEP = int(AccountCode.DEPRECIATION)
FORBIDDEN = 3  # TransferStatus.FORBIDDEN_PAIR


def _unchanged_except_rejections(before, led):
    after = CP.money_state(led)
    bad = CP.diff(before, after)
    assert bad == ["rejections"], bad
    assert after["rejections"][FORBIDDEN] == before["rejections"][FORBIDDEN] + 1


def test_m1_depreciation_between_two_stores_is_a_forbidden_row():
    """形 1(店 0 → 店 1): HEAD は現金を 100 円移した(900/1,100・取引 +1)。1-9 は FORBIDDEN_PAIR で何も動かさない。"""
    old, new = _three_stores()
    st_old = old.transfer_many(S, np.array([0]), S, np.array([1]), np.array([100]), DEP, 5)
    assert st_old.tolist() == [0]
    assert old.balance(BalanceLine.CASH, S).tolist() == [900, 1_100, 1_000] and old.n_transfers == 4
    before = CP.money_state(new)
    st_new = new.transfer_many(S, np.array([0]), S, np.array([1]), np.array([100]), DEP, 5)
    assert st_new.tolist() == [FORBIDDEN]
    _unchanged_except_rejections(before, new)
    assert new.balance(BalanceLine.CASH, S).tolist() == [1_000, 1_000, 1_000] and new.n_transfers == 3


def test_m1_depreciation_on_one_store_via_the_vector_port():
    """形 2(店 2 → 店 2・transfer_many): HEAD は現金が差し引き 0 で取引 +1・流れ +100。1-9 は FORBIDDEN_PAIR(固定資産も動かない)。"""
    old, new = _three_stores()
    st_old = old.transfer_many(S, np.array([2]), S, np.array([2]), np.array([100]), DEP, 5)
    assert st_old.tolist() == [0] and old.n_transfers == 4
    assert int(old.flow[S, S, DEP]) == 100 and old.balance(BalanceLine.FIXED_ASSET, S).tolist() == [0, 0, 0]
    before = CP.money_state(new)
    assert new.transfer_many(S, np.array([2]), S, np.array([2]), np.array([100]), DEP, 5).tolist() == [FORBIDDEN]
    _unchanged_except_rejections(before, new)
    assert int(new.flow[S, S, DEP]) == 0 and new.balance(BalanceLine.FIXED_ASSET, S).tolist() == [0, 0, 0]


def test_m1_depreciation_via_the_scalar_port_and_the_one_entrance():
    """形 3(店 0 → 店 0・1 件の transfer): HEAD は OK(現金 ±0・取引 +1)。1-9 は FORBIDDEN_PAIR。
    自己ループの入口 ``depreciate`` は HEAD と同じ(固定資産 −100・現金と取引の件数は動かない)。"""
    old, new = _three_stores()
    assert int(old.transfer(EntityRef(S, 0), EntityRef(S, 0), 100, DEP, 5)) == 0 and old.n_transfers == 4
    before = CP.money_state(new)
    assert int(new.transfer(EntityRef(S, 0), EntityRef(S, 0), 100, DEP, 5)) == FORBIDDEN
    _unchanged_except_rejections(before, new)
    old2, new2 = _three_stores()
    old2.depreciate(S, np.array([1]), np.array([100]), 5)
    new2.depreciate(S, np.array([1]), np.array([100]), 5)
    assert CP.diff(CP.money_state(old2), CP.money_state(new2)) == []
    assert new2.balance(BalanceLine.FIXED_ASSET, S).tolist() == [0, -100, 0] and new2.n_transfers == 3
