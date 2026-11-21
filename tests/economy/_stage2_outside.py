"""試験の中だけの束: 経済の段階 2 の口(``attach_stage2``)を持たない台帳(第347 止めた切替口の削除・記録
``docs/bench/analysis/switch-removal-347/README.md``)。

経済の段階 2 の腕の切替口 off(2-1 までの値)を消しても、「段階 2 の外の台帳」の道は組み立ての構造として残る: engine の側の
``economy.stage2_bind.attach`` は金の台帳が ``attach_stage2`` を持たなければ何もしない(HEAD 136fdbb の台帳の写しと同じ扱い)・
再開の検査は ``check_resume(effective=False)``。本モジュールはその道を試験の中だけで選ぶ。ランの口(CLI・環境変数・``run_day`` の
引数・設定の箱の欄)には触らない。

- :func:`outside`: 台帳の型の子で、``attach_stage2`` を「無い」に見せる型(``hasattr`` が偽)。
- :func:`use_outside_bundle`: ``shibuya.cli`` の台帳の型を差し替え、``cli.build_ledger_bundle`` が作る台帳を切替口 off の
  分かれと同じ形(雇用主の口 1・輪の係数は台帳の既定=``economy.ledger.TRANSFERS_PER_AGENT_PER_DAY``)にする。組み立ての残り
  (世帯の財布・物の台帳・参入資本・センサスの口)は本物の ``cli.build_ledger_bundle`` のまま。

逐次ループ宣言: なし。
"""

from __future__ import annotations

from typing import Any

__all__ = ["outside", "use_outside_bundle"]


def outside(cls: type) -> type:
    """``cls`` の子で ``attach_stage2`` を持たない型(``cls`` が持たなければ ``cls`` のまま)。"""
    if not hasattr(cls, "attach_stage2"):
        return cls

    class Outside(cls):  # type: ignore[misc, valid-type]
        @property
        def attach_stage2(self) -> Any:  # noqa: D401 — 段階 2 の外の台帳(``hasattr`` を偽にする)
            raise AttributeError("段階 2 の外の台帳(試験の中だけの束)")

    Outside.__name__ = Outside.__qualname__ = f"Outside{cls.__name__}"
    return Outside


def _ledger_type(cls: type) -> type:
    """``cli.Ledger`` の代わり: ``Ledger(体, 店, 雇用主, rows_per_agent_day=…)`` で呼ばれても切替口 off の形で作る。"""
    base = outside(cls)

    class OutsideShapeLedger(base):  # type: ignore[misc, valid-type]
        def __init__(self, n_households: int, n_stores: int, n_employers: int = 1, *,
                     rows_per_agent_day: float | None = None) -> None:
            super().__init__(n_households, n_stores)

    return OutsideShapeLedger


def _wallet_type(cls: type) -> type:
    """``cli._HouseholdWalletLedger`` の代わり(財布つき・切替口 off の形)。"""
    base = outside(cls)

    class OutsideShapeWalletLedger(base):  # type: ignore[misc, valid-type]
        def __init__(self, n_households: int, n_stores: int, wallets: Any, n_employers: int = 1,
                     rows_per_agent_day: float | None = None) -> None:
            super().__init__(n_households, n_stores, wallets)

    return OutsideShapeWalletLedger


def use_outside_bundle(mp: Any, *, ledger_cls: type | None = None, wallet_cls: type | None = None,
                       goods_cls: type | None = None) -> None:
    """``mp``(``pytest.MonkeyPatch``)で ``shibuya.cli`` の台帳の型を差し替える(段階 2 の外の束)。

    ``ledger_cls``・``wallet_cls``・``goods_cls`` を渡すとその型(例: HEAD の台帳の写し)の上に作る。省略は今の型。

    〔割る段 5b の G3・親の裁定〕台帳の型を読むのは、作る側(``build_ledger_bundle``=割った後は ``interfaces.cli.wire_economy``)
    と表示の札を決める側(``main()`` の ``isinstance``=割った後は ``interfaces.cli.main``)の両方。``Ledger``・
    ``_HouseholdWalletLedger`` は両方を、``GoodsLedger``(作る側だけが読む)は作る側だけを差し替える。元の型は作る側の別名から
    読む。別名 ``cli``・``cli_wire`` の割り先は ``tools/pkgmove/split.py`` の ``SPLIT_ALIAS_DESTS`` の宣言(割る前は 2 つとも
    ``shibuya.cli``=同じ物)。
    """
    from shibuya.interfaces.cli import main as cli
    from shibuya.interfaces.cli import wire_economy as cli_wire

    ledger = _ledger_type(ledger_cls if ledger_cls is not None else cli_wire.Ledger)
    mp.setattr(cli, "Ledger", ledger)
    mp.setattr(cli_wire, "Ledger", ledger)
    wallet = _wallet_type(wallet_cls if wallet_cls is not None else cli_wire._HouseholdWalletLedger)
    mp.setattr(cli, "_HouseholdWalletLedger", wallet)
    mp.setattr(cli_wire, "_HouseholdWalletLedger", wallet)
    if goods_cls is not None:
        mp.setattr(cli_wire, "GoodsLedger", goods_cls)
