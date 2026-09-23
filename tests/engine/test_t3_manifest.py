"""T3(冗長方程式の毎期検算)が run manifest に載る(D-85 (a)・ユーザー決定 2026-09-17)。

正典: 境界・経済設計書 §2.3 の空欄 T3(「答申にあるが未実装」)・§2.4 センサス。
検査が増えるだけで**世界は 1 バイトも変わらない**——既定 checkpoint も既存の manifest 欄も
動かないことをここで押さえる。

見るもの
(i) **1 日ラン**(月次センサスが立たない)では ``t3_ok`` は ``None``=未実行。``--census-out``
    の有無で manifest は 1 欄も変わらない(観測は世界を変えない)/
(ii) 月次センサスが立つラン(台帳が 30 日ぶん畳んだ日)では ``t3_ok`` が manifest と
     月次 MER の両方に出て、3 検査の内訳が付く/
(iii) 台帳の無いランは ``t3_ok=None``(注入が無い=未実行)。
"""

from __future__ import annotations

import pyarrow.parquet as pq

from shibuya import cli
from shibuya.economy import census as CS
from shibuya.engine.run import run_day
from shibuya.world.state import World

#: 合成世界の極小ラン(``tests/engine/test_census_out.py`` と同じ書き方)。
SMALL = dict(
    n_agents=64, seed=3, world_dir=None, n_cells=9, ticks=8, checkpoint_every=4,
    processes=False, conversations=False,
)


# ------------------------------------------------------------------ (i) 1 日ラン
def test_a_one_day_run_reports_t3_as_not_run():
    res = cli.run(**SMALL)
    assert res.t3_ok is None and res.t3_report == {}
    fields = res.run_manifest_fields()
    assert "t3_ok" in fields and fields["t3_ok"] is None


def test_the_census_out_does_not_move_the_manifest_or_the_checkpoint(tmp_path):
    """``--census-out`` を渡しても manifest は 1 欄も動かない(t3_ok も None のまま)。"""
    base = cli.run(**SMALL)
    withc = cli.run(census_out=str(tmp_path / "census"), **SMALL)
    assert base.run_manifest_fields() == withc.run_manifest_fields()
    assert base.run_manifest_fields()["t3_ok"] is None
    assert base.final_hash == withc.final_hash != ""


# ------------------------------------------------------------------ (iii) 台帳なし
def test_a_run_without_a_ledger_has_no_t3():
    res = run_day(n_agents=32, seed=1, ticks=4, checkpoint_every=4, n_cells=9,
                  processes=False, conversations=False)
    assert res.t3_ok is None
    assert res.run_manifest_fields()["t3_ok"] is None


# ------------------------------------------------------------------ (ii) 月次が立つラン
def _month_break_run(tmp_path):
    """台帳に**空の 29 日**を畳んでから 1 日回す = その締めが月次センサスの日になる。"""
    world = World.synthetic(n_cells=9, seed=3)
    bundle = cli.build_ledger_bundle(world, 64, seed=3, world_dir=None, use_population=False)
    for d in range(CS.MONTH_DAYS - 1):
        bundle.money.on_day_end(d)
        bundle.goods.on_day_end(d)
    res = run_day(
        n_agents=64, seed=3, world=world, ticks=8, checkpoint_every=4,
        processes=False, conversations=False, ledger=bundle,
        census_out=str(tmp_path / "census"),
    )
    return res, bundle


def test_the_month_break_run_puts_t3_in_the_manifest(tmp_path):
    res, bundle = _month_break_run(tmp_path)
    assert len(bundle.money.flow_daily) == CS.MONTH_DAYS
    assert res.t3_ok is True
    assert res.run_manifest_fields()["t3_ok"] is True
    rep = res.t3_report
    assert rep["ok"] is True
    # 3 検査それぞれの合否と残差の大きさが内訳として残る。
    assert (rep["rows_zero"], rep["cols_match_cash"], rep["deposit_legs_match"]) == (
        True, True, True
    )
    assert (rep["row_residual_max"], rep["col_residual_max"], rep["deposit_residual"]) == (
        0, 0, 0
    )
    assert rep["days"] == CS.MONTH_DAYS and rep["scope"] == "cumulative"
    assert rep["day"] == res.day_closed == 0


def test_the_month_break_run_puts_t3_in_the_monthly_mer(tmp_path):
    """月次 MER の戻りにも同じ答えが出る。**固定表 parquet の列は増えない**(§2.4)。"""
    res, bundle = _month_break_run(tmp_path)
    mer = CS.monthly_mer(bundle.money, bundle.goods, month=0, days=1)
    assert mer["t3_ok"] is res.t3_ok is True
    assert mer["t3"]["ok"] is True and mer["t3"]["days"] == CS.MONTH_DAYS

    target = tmp_path / "census"
    assert len(res.census_paths) == 3
    t = pq.read_table(target / cli.MONTHLY_MER_FILENAME)
    assert list(t.column_names) == [
        "month", "kind", "account", "amount", "money_supply", "residual", "hoard_amount",
    ]
    d = pq.read_table(target / cli.DAILY_CENSUS_FILENAME)
    assert list(d.column_names) == list(CS.DAILY_COLUMNS)
    s = pq.read_table(target / cli.MONTHLY_MER_SECTORS_FILENAME)
    assert list(s.column_names) == list(CS.SECTOR_FLOW_COLUMNS)
