"""CLI ``--l4-scale FACTOR``(L4 呼数予算の倍率・PENDING D-99 (a)・腕 AB8-L4-SCALE)。

``--vocab-version`` の往復テスト(``tests/test_cli_vocab_version.py``)と同じ書き方:
``cli.run`` を差し替えて ``main`` が何を渡したかを見る + 実際に回して run manifest を見る。

見るもの
(t1) ``--l4-scale`` の parse(**既定 0=無制限**=3 段目・D-99 (a′)・D-110・0 可・**負は argparse error**)/
(t2) 変換規則 ``倍率>0 → call_budget_per_tick(n)×倍率`` / ``0 → float(n)`` が
     ``RunResult.budget_per_tick`` に出る/
(t3) 既定(引数なし)と ``l4_scale=0.0`` は **final_hash が一致**・``l4_scale=1.0`` は旧挙動(L4 按分)/
(t4) manifest の L4 監査欄(総呼数・呼/体/日・監査線 10・超過)と艦隊×無制限の注記。
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
    [([], 0.0), (["--l4-scale", "1.0"], 1.0), (["--l4-scale", "0.5"], 0.5),
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
    # 腕は直交(予算の倍率は看板・語彙・意図の腕を動かさない)。CLI の既定の版は第277 で v3
    assert seen["signage_p_see"] == 1.0 and seen["vocab_version"] == cli.CLI_DEFAULT_VOCAB_VERSION


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


# ------------------------------------------------------- (t3) 既定=無制限・1.0=旧挙動
def test_the_default_is_unlimited_and_identical_with_the_explicit_0():
    """3 段目(D-99 (a′)・D-110): CLI と ``cli.run`` の既定は **0=無制限**(``CLI_DEFAULT_L4_SCALE``)。"""
    from shibuya import cli

    assert cli.CLI_DEFAULT_L4_SCALE == 0.0
    base = cli.run(**SMALL)
    explicit = cli.run(l4_scale=0.0, **SMALL)
    assert base.final_hash == explicit.final_hash
    assert cli.checkpoints_payload(base)["checkpoints"] == (
        cli.checkpoints_payload(explicit)["checkpoints"]
    )
    assert base.run_manifest_fields() == explicit.run_manifest_fields()
    assert base.budget_per_tick == float(SMALL["n_agents"]) and base.l4_scale == 0.0


def test_the_explicit_1_0_is_the_old_l4_share():
    """``--l4-scale 1`` で旧挙動(L4 按分・持ち越し 2 tick)。ライブラリ ``run_day`` の既定と同じ。"""
    from shibuya import cli
    from shibuya.engine.run import run_day

    old = cli.run(l4_scale=1.0, **SMALL)
    assert old.budget_per_tick == call_budget_per_tick(SMALL["n_agents"])
    assert old.l4_scale == 1.0
    lib = run_day(n_agents=8, seed=1, ticks=2, renderer="stub", checkpoint_every=2)
    assert lib.budget_per_tick == call_budget_per_tick(8) and lib.l4_scale == 1.0


# ------------------------------------------------------- (t4) L4 監査欄・艦隊の注記
def test_the_manifest_always_carries_the_l4_audit_fields():
    from shibuya import cli
    from shibuya.engine.arbiter import L4_LINE_PER_AGENT_DAY

    assert L4_LINE_PER_AGENT_DAY == 10.0
    for scale in (0.0, 1.0):
        res = cli.run(l4_scale=scale, **SMALL)
        m = res.run_manifest_fields()
        days = SMALL["ticks"] * 60 / 86_400
        assert m["llm_calls_total"] == res.llm_calls
        assert m["llm_calls_per_agent_day"] == pytest.approx(
            res.llm_calls / SMALL["n_agents"] / days, rel=1e-5
        )
        assert m["l4_line"] == 10.0
        assert m["l4_exceeded"] == (m["llm_calls_per_agent_day"] > 10.0)
        assert m["l4_notes"] == []


def test_fleet_x_unlimited_without_a_queue_capacity_is_noted_when_it_cannot_be_fixed():
    """艦隊 × 無制限で ``--fleet-queue-capacity`` が未指定かつ枠が体数未満なら注記の文(D-55)。

    第289 Q28 以降、``cli.run`` は枠を直せる艦隊では ``apply_fleet_queue_default`` で既定を体数にする
    ので、注記(と警告)が残るのは枠を差し替えられない艦隊だけ。
    """
    from types import SimpleNamespace

    from shibuya import cli

    fleet = SimpleNamespace(config=SimpleNamespace(queue_capacity=None), queue_capacity=448)
    note = cli.fleet_queue_note(fleet, 0.0, 5_000)
    assert "--fleet-queue-capacity" in note and "448" in note and "5,000" in note
    assert cli.fleet_queue_note(fleet, 1.0, 5_000) == ""          # 上限あり=注記なし
    assert cli.fleet_queue_note(None, 0.0, 5_000) == ""           # mock=注記なし
    given = SimpleNamespace(config=SimpleNamespace(queue_capacity=8_192), queue_capacity=8_192)
    assert cli.fleet_queue_note(given, 0.0, 5_000) == ""          # 明示した=注記なし
    wide = SimpleNamespace(config=SimpleNamespace(queue_capacity=None), queue_capacity=512)
    assert cli.fleet_queue_note(wide, 0.0, 300) == ""             # 既定の枠が体数以上=繰り延べは起きない


def test_fleet_x_unlimited_queue_capacity_defaults_to_the_agent_count():
    """第289 Q28(D-55): 艦隊 × 無制限 × 枠 未指定 → 枠の既定=体数(``FleetConfig`` を差し替え・manifest に載る)。"""
    from types import SimpleNamespace

    from shibuya import cli
    from shibuya.llm.fleet import FleetConfig

    def client(cap_total: int, queue_capacity: int | None = None) -> SimpleNamespace:
        cfg = FleetConfig(endpoints=("http://127.0.0.1:1",), max_in_flight=cap_total, queue_capacity=queue_capacity)
        return SimpleNamespace(config=cfg, queue_capacity=cfg.resolved_queue_capacity())

    small = client(8)                                             # 既定の枠 8×4=32 < 5,000
    assert cli.apply_fleet_queue_default(small, 0.0, 5_000) == 5_000
    assert small.queue_capacity == 5_000 and small.config.queue_capacity == 5_000
    assert small.config.manifest_fields()["queue_capacity"] == 5_000
    assert small.config.max_in_flight == 8                        # ほかの欄は変えない
    assert cli.fleet_queue_note(small, 0.0, 5_000) == ""          # 直した後は注記なし
    capped = client(8)
    assert cli.apply_fleet_queue_default(capped, 1.0, 5_000) is None and capped.queue_capacity == 32  # 上限あり
    given = client(8, queue_capacity=64)
    assert cli.apply_fleet_queue_default(given, 0.0, 5_000) is None and given.queue_capacity == 64    # 明示
    wide = client(2_000)                                          # 既定の枠 8,000 ≥ 5,000=狭めない
    assert cli.apply_fleet_queue_default(wide, 0.0, 5_000) is None and wide.queue_capacity == 8_000
    assert cli.apply_fleet_queue_default(None, 0.0, 5_000) is None
    frozen = SimpleNamespace(config=SimpleNamespace(queue_capacity=None), queue_capacity=32)
    assert cli.apply_fleet_queue_default(frozen, 0.0, 5_000) is None  # 差し替えられない=従来の注記へ
