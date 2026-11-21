"""第 1 期 1-9: 載せ替えの前(HEAD ``136fdbb``)の ``economy/ledger.py`` と ``economy/goods.py`` の写しを読む道具(試験の補助)。

写し ``head_ledger_136fdbb.py``・``head_goods_136fdbb.py`` は ``git show 136fdbb:src/shibuya/economy/<名>`` のまま(手で
書き換えない)。固定は ``PINS``=改行を LF に揃えてから ``tests/_head_copy_pin.py`` の 3 つ(字面・文の順・読み込んだ後の
意味)。コードの区分の移動 段 4 の下ごしらえ・親の決定 10 を検収 M-1 の後に改めた形。段 4 で移す道具は import の文の
モジュールの道を書き換える(1 本の文を分けることもある)。

HEAD の口は ``cause``(1-3 の原因・1-9 で足した引数)を知らないので、今のエンジンから呼べるように ``cause`` を捨てる
子クラス(``HeadLedger``・``HeadGoods``・``HeadWalletLedger``)を作る(中身は HEAD のまま)。

逐次ループ宣言: なし(試験の道具)。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np

from tests import _head_copy_pin as PIN

HERE = Path(__file__).resolve().parent
HEAD = "136fdbb"
#: 写しの固定(``tests/_head_copy_pin.py``・LF に揃えてから): 名 → 字面の sha256(import の文の束を印の行に替えた全体)・
#: 文の順(束ごとに元の文ごとの置く名)・意味(置いた名 → 指す物の元の置き場。``shibuya.`` を外した元のモジュールの名)。
#: 元の全体の値(136fdbb の時点のバイト。前は blob の名で固定していた):
#: head_ledger_136fdbb.py= blob 8a6a964dfbd201a00617c81bd095c482df00f581(``git rev-parse 136fdbb:src/shibuya/economy/ledger.py``)・
#: sha256 7cc77652d1421416dcfe2f7a52dc76b94e1da7bd809139fba3429df7ee3e538a。
#: head_goods_136fdbb.py= blob 7165e5bc78bb4a2a5a715a0b52da412524b04997(``git rev-parse 136fdbb:src/shibuya/economy/goods.py``)・
#: sha256 f1335542841533b544f1b85d03e21781bdae67df49e2ddcd14b13975c2d16168。
PINS: dict[str, dict[str, Any]] = {
    "head_ledger_136fdbb.py": {
        "text": "58f43aaedced44960e7f4154bac92390af9178fce217759e814d024166f3c3a0",
        "order": (
            (
                ("GrowthDeclaration", "Retention"),
                ("blake3_hex",),
                ("ACCOUNT_NAMES", "ENTRY_CAPITAL_PAYERS", "NON_TRANSFERABLE", "STORED_LINES",
                 "UNCONSTRAINED_SECTORS", "AccountCode", "BalanceLine", "Sector", "is_allowed"),
                ("EntityRef", "TransferStatus"),
                ("STEPS_PER_DAY",),
            ),
        ),
        "refs": {
            "ACCOUNT_NAMES": "value economy.accounts 1201313c0f2387fe",
            "AccountCode": "def economy.accounts AccountCode",
            "BalanceLine": "def economy.accounts BalanceLine",
            "ENTRY_CAPITAL_PAYERS": "value economy.accounts e47d7a2aa0f91f80",
            "EntityRef": "def engine.ledger_api EntityRef",
            "GrowthDeclaration": "def core.growth GrowthDeclaration",
            "NON_TRANSFERABLE": "value economy.accounts 89f52ffcb323db58",
            "Retention": "def core.growth Retention",
            "STEPS_PER_DAY": "value core.time_consts a4ff3ad278c7b057",
            "STORED_LINES": "value economy.accounts e5fb0d41517e95b7",
            "Sector": "def economy.accounts Sector",
            "TransferStatus": "def engine.ledger_api TransferStatus",
            "UNCONSTRAINED_SECTORS": "value economy.accounts e838d3e4cb5f7d6c",
            "blake3_hex": "def core.hashing blake3_hex",
            "is_allowed": "def economy.accounts is_allowed",
        },
    },
    "head_goods_136fdbb.py": {
        "text": "2f3f44b954e62b8e292b8def54628e91928034d48705d620d21213dbf476daa4",
        "order": (
            (
                ("GrowthDeclaration", "Retention"),
                ("pricing",),
                ("AccountCode", "FlowKind", "Sector"),
                ("WASTE_BAND_RATIO", "WASTE_TONNES_PER_DAY"),
            ),
        ),
        "refs": {
            "AccountCode": "def economy.accounts AccountCode",
            "FlowKind": "def economy.accounts FlowKind",
            "GrowthDeclaration": "def core.growth GrowthDeclaration",
            "Retention": "def core.growth Retention",
            "Sector": "def economy.accounts Sector",
            "WASTE_BAND_RATIO": "value economy.anchors 221764976efe0413",
            "WASTE_TONNES_PER_DAY": "value economy.anchors 0bd2fcdd091e0a2f",
            "pricing": "module economy.pricing",
        },
    },
}


def pin_problems(name: str, mod: ModuleType) -> list[str]:
    """写し ``name`` と読み込んだ ``mod`` が固定と違う所(字面・文の順・意味)。"""
    want = PINS[name]
    path = HERE / name
    out = [] if PIN.text_sha256(path, lf=True) == want["text"] else [f"{name}: 字面の sha256 が違う"]
    out += [f"{name}: {x}" for x in PIN.order_problems(path, want["order"], lf=True)]
    out += [f"{name}: {x}" for x in PIN.ref_problems(mod, path, want["refs"], lf=True)]
    return out


def _load(name: str, file: str) -> ModuleType:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def head_ledger_module() -> ModuleType:
    return _load("cp2_head_ledger_136fdbb", "head_ledger_136fdbb.py")


def head_goods_module() -> ModuleType:
    return _load("cp2_head_goods_136fdbb", "head_goods_136fdbb.py")


def _drop_cause(kw: dict[str, Any]) -> dict[str, Any]:
    kw.pop("cause", None)
    return kw


def shims() -> tuple[type, type, type]:
    """(HEAD の Ledger の子・HEAD の GoodsLedger の子・HEAD の財布の差し替えの子)。``cause`` を捨てるだけ。"""
    HL = head_ledger_module()
    HG = head_goods_module()

    class HeadLedger(HL.Ledger):  # type: ignore[misc, valid-type]
        def transfer(self, *a: Any, **kw: Any):  # noqa: ANN201
            return super().transfer(*a, **_drop_cause(kw))

        def transfer_many(self, *a: Any, **kw: Any):  # noqa: ANN201
            return super().transfer_many(*a, **_drop_cause(kw))

        def purchase_many(self, *a: Any, **kw: Any):  # noqa: ANN201
            return super().purchase_many(*a, **_drop_cause(kw))

        def endow_households(self, *a: Any, **kw: Any):  # noqa: ANN201
            return super().endow_households(*a, **_drop_cause(kw))

        def endow_stores(self, *a: Any, **kw: Any):  # noqa: ANN201
            return super().endow_stores(*a, **_drop_cause(kw))

        def depreciate(self, *a: Any, **kw: Any):  # noqa: ANN201
            return super().depreciate(*a, **_drop_cause(kw))

    class HeadGoods(HG.GoodsLedger):  # type: ignore[misc, valid-type]
        def restock_many(self, *a: Any, **kw: Any):  # noqa: ANN201
            return super().restock_many(*a, **_drop_cause(kw))

        def deliver(self, *a: Any, **kw: Any):  # noqa: ANN201
            return super().deliver(*a, **_drop_cause(kw))

    class HeadWalletLedger(HeadLedger):
        """``cli._HouseholdWalletLedger`` と同じ(HEAD の Ledger の上)。"""

        def __init__(self, n_households: int, n_stores: int, wallets: np.ndarray) -> None:
            super().__init__(n_households, n_stores)
            self.wallets = np.asarray(wallets, dtype=np.int64).ravel()

        def endow_households(self, amounts: np.ndarray, tick: int = 0, **kw: Any) -> np.ndarray:  # noqa: D102
            a = np.asarray(amounts, dtype=np.int64).ravel().copy()
            m = min(a.size, self.wallets.size)
            a[:m] = self.wallets[:m]
            return super().endow_households(a, tick)

    return HeadLedger, HeadGoods, HeadWalletLedger


# ---------------------------------------------------------------- 状態の突き合わせ
def money_state(led: Any) -> dict[str, Any]:
    """金の台帳の状態(残高・流れ・締め・生ログの中身と位置・計数)。HEAD と今で同じ鍵。"""
    out: dict[str, Any] = {}
    for line, arrays in led._lines.items():
        for s, arr in enumerate(arrays):
            out[f"lines.{line}.{s}"] = np.asarray(arr).copy()
    for s, arr in enumerate(led._last_change_day):
        out[f"last_change_day.{s}"] = np.asarray(arr).copy()
    out["flow"] = led._flow.copy()
    out["flow_daily"] = [f.copy() for f in led._flow_daily]
    for k in ("cash", "deposit", "loan"):
        out[f"snap.{k}"] = led._snap[k].copy()
        out[f"snap0.{k}"] = led._snap0[k].copy()
    lc = led._last_close
    out["last_close"] = None if lc is None else (lc.day, lc.flow.copy(), lc.d_cash.copy(), lc.d_deposit.copy(),
                                                 lc.d_loan.copy(), lc.raw_rows_kept)
    out["raw_rows"] = led.raw_rows()
    for c in ("_raw_tick", "_raw_ps", "_raw_pi", "_raw_qs", "_raw_qi", "_raw_amt", "_raw_code"):
        out[f"ring.{c}"] = getattr(led, c).copy()
    for c in ("_raw_pos", "_raw_head", "_day", "n_raw_dropped", "n_transfers", "raw_capacity", "retention_days"):
        out[c] = int(getattr(led, c))
    out["day_marks"] = list(led._day_marks)
    out["rejections"] = dict(led.rejections)
    out["state_hash"] = led.state_hash()
    out["money_supply"] = int(led.money_supply())
    return out


def goods_state(g: Any) -> dict[str, Any]:
    """物の台帳の状態(在庫の配列・納品ログの中身と位置・計数・締め)。"""
    out: dict[str, Any] = {f"guarded.{i}": np.asarray(a).copy() for i, a in enumerate(g._guarded())}
    out["delivery_rows"] = g.delivery_rows()
    for c in ("_dl_tick", "_dl_poi", "_dl_slot", "_dl_qty", "_dl_code"):
        out[f"ring.{c}"] = getattr(g, c).copy()
    for c in ("_dl_pos", "_dl_head", "_day", "n_delivery_dropped", "n_moves", "rejections"):
        out[c] = int(getattr(g, c))
    out["dl_marks"] = list(g._dl_marks)
    out["open_stock"] = g._open_stock.copy()
    out["day_waste_g"] = float(g._day_waste_g)
    out["waste_g_daily"] = list(g._waste_g_daily)
    out["store_waste_g_total"] = float(g.store_waste_g_total)
    lc = g._last_close
    out["last_close"] = None if lc is None else {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in lc.items()}
    return out


def diff(a: dict[str, Any], b: dict[str, Any]) -> list[str]:
    """2 つの状態の食い違う鍵(配列は形・型・中身)。"""
    bad: list[str] = []
    for k in sorted(set(a) | set(b)):
        x, y = a.get(k), b.get(k)
        if isinstance(x, np.ndarray) or isinstance(y, np.ndarray):
            if not (isinstance(x, np.ndarray) and isinstance(y, np.ndarray) and x.dtype == y.dtype
                    and x.shape == y.shape and np.array_equal(x, y)):
                bad.append(k)
        elif isinstance(x, list) and x and isinstance(x[0], np.ndarray):
            if not (isinstance(y, list) and len(x) == len(y) and all(np.array_equal(p, q) for p, q in zip(x, y))):
                bad.append(k)
        elif isinstance(x, tuple) and isinstance(y, tuple):
            if len(x) != len(y) or any(
                    (not np.array_equal(p, q)) if isinstance(p, np.ndarray) else p != q for p, q in zip(x, y)):
                bad.append(k)
        elif x != y:
            bad.append(k)
    return bad
