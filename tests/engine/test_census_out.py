"""``--census-out`` — 日次センサス/月次 MER の出力口(境界・経済設計書 §2.4)。

見るもの
(i) **既定(``census_out=None``)は何も書かない**——ディレクトリも作らない。
    ``RunResult.census_paths`` は空・run manifest にも欄は増えない/
(ii) 渡すと 3 ファイル(日次センサス・月次 MER の固定表・月次 MER の**部門軸**)が出て、
     日次は ``residual`` / ``money_supply`` / ``gate_ok`` を持ち、MER は科目別 faucet/sink の
     縦持ち、部門軸は ``from_sector``/``to_sector`` の長い表になる(第204・D-76 (a))/
(iii) **既定 checkpoint が動かない**——``census_out`` を渡したランと渡さないランで
      ``final_hash`` と checkpoint 列が一致する(観測は世界を変えない)。

書き手は ``economy.census``(Parquet・zstd)。engine は economy を import できない
(層契約 ``economy > engine``)ので、``LedgerBundle.census_write`` へ ``cli`` が注入する。
"""

from __future__ import annotations

import pyarrow.parquet as pq

from shibuya import cli
from shibuya.economy.census import DAILY_COLUMNS, SECTOR_FLOW_COLUMNS, SECTORS

#: 合成世界の極小ラン(``tests/test_cli_intent_mode.py`` と同じ書き方)。
SMALL = dict(
    n_agents=64, seed=3, world_dir=None, n_cells=9, ticks=8, checkpoint_every=4,
    processes=False, conversations=False,
)


# ------------------------------------------------------------------ (i) 既定は何も書かない
def test_default_writes_nothing(tmp_path):
    target = tmp_path / "census"
    res = cli.run(**SMALL)
    assert res.census_paths == ()
    assert not target.exists(), "既定でディレクトリを作ってはいけない"
    assert list(tmp_path.iterdir()) == []
    assert "census_out" not in res.run_manifest_fields()
    assert "census_paths" not in res.run_manifest_fields()


def test_explicit_none_is_the_same_as_the_default(tmp_path):
    res = cli.run(census_out=None, **SMALL)
    assert res.census_paths == ()
    assert list(tmp_path.iterdir()) == []


# ------------------------------------------------------------------ (ii) 渡すと 3 ファイル
def test_census_out_writes_the_three_files(tmp_path):
    target = tmp_path / "census"
    res = cli.run(census_out=str(target), **SMALL)
    daily = target / cli.DAILY_CENSUS_FILENAME
    mer = target / cli.MONTHLY_MER_FILENAME
    sectors = target / cli.MONTHLY_MER_SECTORS_FILENAME
    assert sorted(p.name for p in target.iterdir()) == sorted(
        [daily.name, mer.name, sectors.name]
    )
    assert set(res.census_paths) == {
        daily.as_posix(), mer.as_posix(), sectors.as_posix()
    }

    t = pq.read_table(daily)
    assert list(t.column_names) == list(DAILY_COLUMNS)
    assert t.num_rows == 1
    for col in ("residual", "money_supply", "gate_ok"):
        assert col in t.column_names
    row = {k: v[0] for k, v in t.to_pydict().items()}
    assert row["day"] == res.day_closed >= 0
    # 締めた日の実数=エンジンが持っている行と同じ(空虚な行になっていない)
    assert row["residual"] == res.census_row["residual"]
    assert row["money_supply"] == res.census_row["money_supply"]
    assert row["gate_ok"] == res.census_row["gate_ok"] == res.census_pass
    assert row["money_supply"] > 0

    m = pq.read_table(mer)
    assert {"kind", "account", "amount", "money_supply", "residual"} <= set(m.column_names)
    kinds = set(m.column("kind").to_pylist())
    assert kinds and kinds <= {"faucet", "sink", "internal"}
    assert set(m.column("money_supply").to_pylist()) == {row["money_supply"]}
    # 固定表の列は増えていない(部門軸は別ファイル=D-76 (a))。
    assert list(m.column_names) == [
        "month", "kind", "account", "amount", "money_supply", "residual", "hoard_amount",
    ]

    sec = pq.read_table(sectors)
    assert list(sec.column_names) == list(SECTOR_FLOW_COLUMNS)
    assert sec.num_rows > 0
    assert set(sec.column("kind").to_pylist()) <= {
        "faucet", "sink", "internal", "book", "measure"
    }
    # 検算: 区分×科目で畳むと固定表(科目別 faucet/sink/internal)と一致する。
    got: dict[tuple[str, str], int] = {}
    for k, a, amt in zip(
        sec.column("kind").to_pylist(),
        sec.column("account").to_pylist(),
        sec.column("amount").to_pylist(),
    ):
        if k in ("faucet", "sink", "internal"):
            got[(k, a)] = got.get((k, a), 0) + int(amt)
    want = {
        (k, a): int(amt)
        for k, a, amt in zip(
            m.column("kind").to_pylist(),
            m.column("account").to_pylist(),
            m.column("amount").to_pylist(),
        )
    }
    assert got == want
    # 境界は擬似部門へ出ている(faucet の払い手は "faucet")。この極小ランに sink は無い。
    assert "faucet" in sec.column("from_sector").to_pylist()
    allowed = set(SECTORS) | {"faucet", "sink"}
    assert set(sec.column("from_sector").to_pylist()) <= allowed
    assert set(sec.column("to_sector").to_pylist()) <= allowed


def test_census_out_creates_missing_parents(tmp_path):
    target = tmp_path / "a" / "b" / "census"
    res = cli.run(census_out=str(target), **SMALL)
    assert target.is_dir() and len(res.census_paths) == 3


# ------------------------------------------------------------------ (iii) 既定 checkpoint 不変
def test_the_checkpoint_does_not_move(tmp_path):
    """観測(センサスの書き出し)は世界を変えない=checkpoint 列が 1 ビットも動かない。"""
    base = cli.run(**SMALL)
    withc = cli.run(census_out=str(tmp_path / "census"), **SMALL)
    assert base.final_hash == withc.final_hash != ""
    assert cli.checkpoints_payload(base)["checkpoints"] == (
        cli.checkpoints_payload(withc)["checkpoints"]
    )
    assert base.run_manifest_fields() == withc.run_manifest_fields()
    assert base.llm_calls == withc.llm_calls
    assert base.census_row == withc.census_row


# ------------------------------------------------------------------ 台帳が無いラン
def test_run_day_without_a_ledger_writes_nothing(tmp_path):
    from shibuya.engine.run import run_day

    res = run_day(n_agents=32, seed=1, ticks=4, checkpoint_every=4, n_cells=9,
                  processes=False, conversations=False, census_out=str(tmp_path / "c"))
    assert res.census_paths == ()
    assert not (tmp_path / "c").exists()
