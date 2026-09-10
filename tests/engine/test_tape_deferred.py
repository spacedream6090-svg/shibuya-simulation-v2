"""D-58 テープ繰り延べ行: 録画→再生が**繰り延べごと**一致する(C7 受入の停止句)。

背景(PENDING D-58)
    版1 のテープは「応答の返った呼」しか行を持たず、艦隊の**繰り延べ**(queue full /
    タイムアウト → 翌 tick の起床候補へ再投入)は記録されなかった。そのため本番
    c7-day-2(390,067 体・繰り延べ 1,320,190 呼)の再生は tick 0 から分岐し
    tape_miss 98.7% になった。版2 は繰り延べも 1 行(応答空・``deferred=1``)にし、
    応答行にも ``observed_tick``(エンジンが帰結を観測した tick)を持つ。

固定する性質
- (a) 繰り延べを**強制**した艦隊ランを録画→再生すると、全 checkpoint と ``final_hash``
      が一致し ``tape_miss=0``・繰り延べ数/再投入数が一致する(queue full 版とタイムアウト版)。
- (b) 版1(3 列が無い)テープも読める=全行 ``deferred=0``/``observed_tick=-1``。
- (c) 繰り延べ 0 のランは**従来と 1 行も違わない**(行数=呼数・全行 deferred 0・
      observed_tick −1・checkpoint 一致)。

実サーバー(SSH)へは繋がない。偽 vLLM は ``tests.llm.test_fleet.FakeVLLM``。
"""

from __future__ import annotations

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.engine.run import run_day
from shibuya.engine.tape import (
    CALLS_FILENAME,
    CALLS_SCHEMA,
    CALLS_SCHEMA_V1_NAMES,
    TAPE_SCHEMA_VERSION,
    Replay,
    Tape,
    TapeDeferred,
    TapeMiss,
    TapeRow,
    TapeWriter,
)
from shibuya.llm.fleet import FleetClient, FleetConfig, Outcome
from shibuya.manifest.schema import Mode
from shibuya.world.state import World

from tests.engine.test_tape_wiring import BoomLLM
from tests.llm.test_fleet import FakeVLLM

N_AGENTS = 120
CELLS = 16


@pytest.fixture
def fleet_servers():
    servers = [FakeVLLM(), FakeVLLM()]
    try:
        yield servers
    finally:
        for s in servers:
            s.close()


def make_client(servers, **kw) -> FleetClient:
    base = dict(
        endpoints=tuple(s.endpoint for s in servers),
        model=servers[0].model,
        mode=Mode.SMOKE,
        run_id="d58-test",
        run_seed=1,
        per_replica_in_flight=16,
        queue_capacity=256,
        ttft_timeout_s=5.0,
        e2e_timeout_s=8.0,
        connect_timeout_s=5.0,
        stream=False,
        latency_samples=1000,
    )
    base.update(kw)
    return FleetClient(FleetConfig(**base))


def common(ticks: int) -> dict:
    return dict(
        n_agents=N_AGENTS, seed=1, world=World.synthetic(n_cells=CELLS, seed=1), ticks=ticks,
        renderer="stub", processes=False, population=False, world_dir=None,
        checkpoint_every=max(1, ticks // 4),
    )


def record_and_replay(client: FleetClient, path, *, ticks: int, fleet_wait_s: float, **run_kw):
    """同じ設定で 艦隊ラン(録画)→ テープ再生 を回して両方の結果を返す。

    ``fleet_wait_s`` は艦隊ランだけの引数(再生に艦隊は無い)。それ以外(``budget`` など)は
    **両方に同じ値**を渡す=違いはテープの有無だけ。
    """
    rec = run_day(
        fleet=client, tape_path=path, fleet_wait_s=fleet_wait_s, **common(ticks), **run_kw
    )
    rep = run_day(mode="replay", replay=path, llm=BoomLLM(), **common(ticks), **run_kw)
    return rec, rep


def assert_same_run(rec, rep) -> None:
    assert rec.checkpoints and rep.checkpoints
    assert [c.combined for c in rep.checkpoints] == [c.combined for c in rec.checkpoints]
    assert rep.final_hash == rec.final_hash
    assert rep.tape_miss_count == 0
    assert rep.llm_calls == rec.llm_calls
    assert rep.bridge_counters["fleet_reinjected"] == rec.bridge_counters["fleet_reinjected"]
    assert rep.bridge_counters["fleet_resent"] == rec.bridge_counters["fleet_resent"]
    assert rep.fleet_unanswered_at_end == rec.fleet_unanswered_at_end
    assert rep.fleet_drained_at_end == rec.fleet_drained_at_end


# ------------------------------------------------------------------ (a) 繰り延べつき再生


def test_queue_full_run_replays_bit_for_bit(fleet_servers, tmp_path):
    """キュー満杯を強制した艦隊ランを録画→再生: 繰り延べも含めて完全一致。"""
    for srv in fleet_servers:
        srv.total_delay_s = 0.02
    # 受理枠 8 に対して 1 tick 30 呼=**溢れる**(残りは queue full で繰り延べ)。
    # ``fleet_wait_s`` を入れて受理された呼は次 tick に届く=応答行と繰り延べ行が混ざる。
    client = make_client(fleet_servers, per_replica_in_flight=4, queue_capacity=8)
    rec, rep = record_and_replay(
        client, tmp_path / "tape_qf", ticks=20, budget=30.0, fleet_wait_s=2.0
    )
    assert rec.bridge_counters["fleet_deferred_queue_full"] > 0, "繰り延べが起きていない"
    assert rec.bridge_counters["fleet_reinjected"] > 0

    tape = Tape(tmp_path / "tape_qf")
    assert tape.schema_version == TAPE_SCHEMA_VERSION and tape.has_deferred_columns
    rows = list(tape.rows())
    deferred_rows = [r for r in rows if r.is_deferred]
    assert len(rows) == rec.llm_calls, "1 呼 = 1 行(繰り延べも 1 行)"
    assert len(deferred_rows) == int(rec.bridge_counters["tape_deferred_rows"]) > 0
    assert all(r.response == "" and r.tokens_in == 0 and r.tokens_out == 0 for r in deferred_rows)
    assert {r.deferred_reason for r in deferred_rows} <= {
        Outcome.DEFERRED_QUEUE_FULL.value, Outcome.DEFERRED_TIMEOUT.value,
        Outcome.ERROR_OTHER.value,
    }
    assert all(r.observed_tick >= 0 for r in rows), "艦隊ランは観測 tick を持つ"
    answered = [r for r in rows if not r.is_deferred]
    assert answered, "応答行と繰り延べ行が混ざる場面のはず"
    assert any(r.observed_tick > r.tick for r in answered), "応答は発射より後の tick で届く"

    assert_same_run(rec, rep)
    assert rep.bridge_counters["tape_deferred"] == float(len(deferred_rows))


def test_timeout_run_replays_bit_for_bit(fleet_servers, tmp_path):
    """タイムアウト(=発射より**後の tick** で観測)も同じ tick で再現される。"""
    for srv in fleet_servers:
        srv.total_delay_s = 1.0  # e2e 0.2 s を必ず超える=全部タイムアウト
    client = make_client(fleet_servers, e2e_timeout_s=0.2, ttft_timeout_s=0.2)
    rec, rep = record_and_replay(client, tmp_path / "tape_to", ticks=8, fleet_wait_s=1.0)
    assert rec.bridge_counters["fleet_deferred_timeout"] > 0

    rows = list(Tape(tmp_path / "tape_to").rows())
    late = [r for r in rows if r.is_deferred and r.observed_tick > r.tick]
    assert late, "タイムアウトは発射 tick より後で観測されるはず"
    assert_same_run(rec, rep)


def test_replay_of_a_deferred_tape_makes_no_intent_for_that_call(fleet_servers, tmp_path):
    """繰り延べ行はパースも未定義行動5段も通らない(=待機 intent を作らない)。

    版1 の挙動(空応答→未定義行動→待機)に落ちていないことの機械検査。
    """
    for srv in fleet_servers:
        srv.total_delay_s = 0.02
    client = make_client(fleet_servers, per_replica_in_flight=1, queue_capacity=1)
    rec, rep = record_and_replay(
        client, tmp_path / "tape_nd", ticks=16, budget=30.0, fleet_wait_s=0.0
    )
    assert rec.bridge_counters["fleet_deferred_queue_full"] > 0
    assert rep.bridge_counters["tape_deferred"] > 0
    # 繰り延べは「答えが無い」だけで未定義行動ではない
    assert rep.undefined_action_count == rec.undefined_action_count == 0
    assert rep.bridge_counters["unknown_action"] == 0.0
    # 呼数(=発射数)は再生でも本番と同じ
    assert rep.llm_calls == rec.llm_calls > 0


# ------------------------------------------------------------------ (b) 旧スキーマ


def _downgrade_to_v1(path) -> None:
    """版2 のテープから 3 列を落として版1(``shibuya.tape/1``)にする。"""
    table = pq.read_table(path / CALLS_FILENAME)
    v1 = pa.schema([CALLS_SCHEMA.field(n) for n in CALLS_SCHEMA_V1_NAMES])
    pq.write_table(
        pa.Table.from_pydict(
            {n: table.column(n).to_pylist() for n in CALLS_SCHEMA_V1_NAMES}, schema=v1
        ),
        path / CALLS_FILENAME,
        compression="zstd",
    )


def test_a_v1_tape_is_still_readable(tmp_path):
    """版1 のテープ(3 列なし)は全行 ``deferred=0``/``observed_tick=-1`` として読める。"""
    with TapeWriter(tmp_path / "t") as w:
        b = w.intern_block("共有静的ブロック")
        for i in range(5):
            w.append(TapeRow(f"c{i}", i, i, 1, f"ph{i}", (b,), "pa", f"応答{i}"))
    _downgrade_to_v1(tmp_path / "t")

    tape = Tape(tmp_path / "t")
    assert tape.schema_version == "shibuya.tape/1" and not tape.has_deferred_columns
    rows = list(tape.rows())
    assert len(rows) == 5
    assert all(r.deferred == 0 and r.deferred_reason == "" and r.observed_tick == -1
               for r in rows)
    replay = Replay(tape)
    assert replay.lookup(2, 2, 1, "ph2") == "応答2"
    assert replay.n_deferred_rows == 0 and replay.deferred_hits == 0
    assert replay.counters()["tape_deferred"] == 0


def test_a_v1_tape_replays_a_whole_run(tmp_path):
    """版1 テープでの ``run_day(mode='replay')`` が版2 と同じ結果になる(後方互換)。"""
    small = dict(n_agents=200, seed=1, ticks=90, checkpoint_every=30, n_cells=16,
                 renderer="stub", processes=False, population=False, world_dir=None)
    rec = run_day(tape_path=tmp_path / "v1", **small)
    _downgrade_to_v1(tmp_path / "v1")
    rep = run_day(mode="replay", replay=tmp_path / "v1", llm=BoomLLM(), **small)
    assert rep.final_hash == rec.final_hash
    assert [c.combined for c in rep.checkpoints] == [c.combined for c in rec.checkpoints]
    assert rep.tape_miss_count == 0
    assert rep.bridge_counters["tape_deferred"] == 0.0
    assert "fleet_reinjected" not in rep.bridge_counters


# ------------------------------------------------------------------ (c) 繰り延べ 0 は不変


def test_a_run_without_deferrals_writes_the_same_rows_as_before(tmp_path):
    """mock ラン(繰り延べ 0)は行数=呼数・全行 deferred 0・observed_tick −1。"""
    small = dict(n_agents=200, seed=1, ticks=90, checkpoint_every=30, n_cells=16,
                 renderer="stub", processes=False, population=False, world_dir=None)
    rec = run_day(tape_path=tmp_path / "plain", **small)
    tape = Tape(tmp_path / "plain")
    rows = list(tape.rows())
    assert len(rows) == rec.llm_calls > 0
    assert all(r.deferred == 0 and r.deferred_reason == "" and r.observed_tick == -1
               for r in rows)
    assert rec.bridge_counters["tape_deferred"] == 0.0
    assert "fleet_reinjected" not in rec.bridge_counters
    # 索引の版2 欄は 1 件も作られない(RAM も走査も版1 と同じ)
    replay = Replay(tape)
    assert replay._meta == {}  # noqa: SLF001 - 不変の担保はここでしか見えない

    rep = run_day(mode="replay", replay=tmp_path / "plain", llm=BoomLLM(), **small)
    assert rep.final_hash == rec.final_hash and rep.tape_miss_count == 0


# ------------------------------------------------------------------ 単体


def test_lookup_raises_on_a_deferred_row_and_lookup_row_returns_it(tmp_path):
    """``lookup``(文字列契約)は繰り延べを例外に、``lookup_row`` は値で返す。"""
    with TapeWriter(tmp_path / "t") as w:
        w.append(TapeRow("c0", 1, 2, 3, "ph", (), "pa", "A", observed_tick=5))
        w.append(TapeRow("c1", 1, 3, 3, "phd", (), "pa", "",
                         deferred=1, deferred_reason="deferred_queue_full", observed_tick=3))
    replay = Replay(tmp_path / "t")
    assert replay.lookup(1, 2, 3, "ph") == "A"
    assert replay.lookup_row(1, 2, 3, "ph").observed_tick == 5
    with pytest.raises(TapeDeferred) as e:
        replay.lookup(1, 3, 3, "phd")
    assert e.value.observed_tick == 3 and e.value.reason == "deferred_queue_full"
    assert not isinstance(e.value, TapeMiss), "繰り延べはテープ外ではない"
    hit = replay.lookup_row(1, 3, 3, "phd")
    assert hit.is_deferred and hit.response == "" and hit.deferred_reason == "deferred_queue_full"
    assert replay.n_deferred_rows == 1 and replay.deferred_hits == 2
    assert replay.misses == 0


def test_writer_counts_deferred_rows(tmp_path):
    with TapeWriter(tmp_path / "t") as w:
        w.append(TapeRow("c0", 1, 0, 0, "ph0", (), "pa", "A"))
        w.append(TapeRow("c1", 1, 1, 0, "ph1", (), "pa", "", deferred=1,
                         deferred_reason="deferred_timeout", observed_tick=4))
        assert w.n_rows == 2 and w.n_deferred_rows == 1
    assert pq.read_schema(tmp_path / "t" / CALLS_FILENAME).names == list(CALLS_SCHEMA.names)
