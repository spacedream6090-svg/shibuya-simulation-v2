"""CLI ``--l4-scale FACTOR``(L4 呼数予算の倍率・PENDING D-99 (a)・腕 AB8-L4-SCALE)。

``--vocab-version`` の往復テスト(``tests/test_cli_vocab_version.py``)と同じ書き方:
``cli.run`` を差し替えて ``main`` が何を渡したかを見る + 実際に回して run manifest を見る。

見るもの
(t1) ``--l4-scale`` の parse(既定 1.0・0 可・**負は argparse error**)/
(t2) 変換規則 ``倍率>0 → call_budget_per_tick(n)×倍率`` / ``0 → float(n)`` が
     ``RunResult.budget_per_tick`` に出る/
(t3) 既定(引数なし)と ``l4_scale=1.0`` は **final_hash が一致**(=現行のバイト)。
"""

from __future__ import annotations

import pytest

from shibuya.engine.arbiter import call_budget_per_tick

SMALL = dict(
    n_agents=32, seed=1, world_dir=None, n_cells=9, ticks=2, checkpoint_every=2,
    processes=False, conversations=False,
)


# ------------------------------------------------------------------ (t1) parse
@pytest.mark.parametrize(
    "argv,expected",
    [([], 1.0), (["--l4-scale", "1.0"], 1.0), (["--l4-scale", "0.5"], 0.5),
     (["--l4-scale", "2"], 2.0), (["--l4-scale", "0"], 0.0)],
)
def test_cli_main_has_the_l4_scale_flag(monkeypatch, argv, expected):
    from shibuya import cli

    seen: dict = {}

    class _Stub:
        fleet_fields: dict = {}

        def summary(self) -> str:
            return "(stub)"

    monkeypatch.setattr(cli, "run", lambda **kw: (seen.update(kw), _Stub())[1])
    assert cli.main(["--agents", "8", "--world", "__no_such_dir__", "--cells", "9", *argv]) == 0
    assert seen["l4_scale"] == expected
    # 腕は直交(予算の倍率は看板・語彙・意図の腕を動かさない)
    assert seen["signage_p_see"] == 1.0 and seen["vocab_version"] == "v1"


def test_a_negative_factor_is_a_usage_error(capsys):
    """負の倍率は traceback ではなく usage で落とす(``--signage-p-see`` と同じ作法)。"""
    from shibuya import cli

    with pytest.raises(SystemExit):
        cli.main(["--agents", "8", "--world", "__no_such_dir__", "--l4-scale", "-1"])
    assert "--l4-scale" in capsys.readouterr().err


def test_cli_run_rejects_a_negative_factor():
    from shibuya import cli

    with pytest.raises(ValueError):
        cli.run(l4_scale=-0.5, **SMALL)


# ------------------------------------------------------- (t2) 変換規則
@pytest.mark.parametrize("scale", [1.0, 0.5, 2.0])
def test_the_factor_multiplies_the_l4_share(scale):
    from shibuya import cli

    res = cli.run(l4_scale=scale, **SMALL)
    assert res.l4_scale == scale
    assert res.budget_per_tick == pytest.approx(call_budget_per_tick(SMALL["n_agents"]) * scale)
    fields = res.run_manifest_fields()
    assert fields["l4_scale"] == scale
    assert fields["budget_per_tick"] == pytest.approx(res.budget_per_tick)


def test_zero_means_one_call_per_agent_per_tick():
    """``0`` = **無制限**。アービタは合流後に体あたり高々 1 件なので体数で足りる。"""
    from shibuya import cli

    res = cli.run(l4_scale=0.0, **SMALL)
    assert res.budget_per_tick == float(SMALL["n_agents"])
    assert res.l4_scale == 0.0


def test_an_explicit_budget_wins_over_the_factor():
    """``budget`` を直に渡した呼び出しは倍率より優先(倍率は 1.0 のまま manifest に載る)。"""
    from shibuya import cli

    res = cli.run(budget=7.0, **SMALL)
    assert res.budget_per_tick == 7.0
    assert res.l4_scale == 1.0


# ------------------------------------------------------- (t3) 既定のバイト不変
def test_the_default_run_is_byte_identical_with_the_explicit_1_0():
    from shibuya import cli

    base = cli.run(**SMALL)
    explicit = cli.run(l4_scale=1.0, **SMALL)
    assert base.final_hash == explicit.final_hash
    assert cli.checkpoints_payload(base)["checkpoints"] == (
        cli.checkpoints_payload(explicit)["checkpoints"]
    )
    assert base.run_manifest_fields() == explicit.run_manifest_fields()
    assert base.budget_per_tick == call_budget_per_tick(SMALL["n_agents"])
