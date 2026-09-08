"""engine.llm_bridge の結線テスト(録画テープ・δ_think レーン・record/replay の同一性)。

正典
- 運用設計書 §2.5: 「録画リプレイ=(agent_id, tick, wake_class, prompt_hash) **完全一致**。
  テープ外は失敗(**黙って実LLMへ落とさない**)・テープ外率を診断行へ。」
- 認知設計書 §1: δ_think レーン表(L0=0 / L1=2.6秒 / L2=82秒 / L3=300秒/ブロック)。
- 知覚契約書 §2.4 ⑨: 時刻表記は5分丸め(``StubRenderer`` の ``tick//5``)。
- 予算宣言表 §7-5 / C3 受け入れ: 診断行(繰り延べ/昇格/縮退/抑止 + 書式エラー率ほか)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.engine.llm_bridge import (
    DEFAULT_LANE,
    LANE_SECONDS,
    LLMBridge,
    StubRenderer,
    delta_think_ticks,
)
from shibuya.engine.run import DIAG_DAY_ROWS, DIAG_RUN_COLUMNS, run_day
from shibuya.engine.tape import BLOCKS_FILENAME, CALLS_FILENAME, Replay, Tape, TapeWriter
from shibuya.llm import MockLLM
from shibuya.llm.mock import MOCK_RNG_DOMAIN

SMALL = dict(n_agents=400, seed=1, ticks=180, checkpoint_every=60, n_cells=25)


class BoomLLM:
    """呼ばれたら落ちるクライアント(**リプレイで実LLMへ落ちない**ことの証拠)。"""

    def __init__(self) -> None:
        self.n_calls = 0

    def complete(self, request):  # pragma: no cover - 呼ばれてはいけない
        self.n_calls += 1
        raise AssertionError("リプレイ中に実クライアントが呼ばれた")


# ---------------------------------------------------------------- δ_think レーン
def test_delta_think_lanes_match_the_cognition_design():
    assert LANE_SECONDS["L1"] == pytest.approx(2.6)
    assert LANE_SECONDS["L2"] == pytest.approx(82.0)
    assert LANE_SECONDS["L3"] == pytest.approx(300.0)
    assert delta_think_ticks("L0") == 0
    assert delta_think_ticks("L1") == 1  # ceil(2.6/60)
    assert delta_think_ticks("L2") == 2  # ceil(82/60)= 2 tick
    assert delta_think_ticks("L3") == 5  # ceil(300/60)
    with pytest.raises(KeyError):
        delta_think_ticks("L9")


def test_t_apply_uses_the_lane():
    llm = MockLLM(master_seed=1)
    b1 = LLMBridge(llm, lane="L1")
    b2 = LLMBridge(llm, lane="L2")
    assert b1.call(3, 100, 1).t_apply == 101
    assert b2.call(3, 100, 1).t_apply == 102
    assert b1.call(3, 100, 1, lane="L3").t_apply == 105


# ---------------------------------------------------------------- StubRenderer
def test_stub_renderer_hash_is_stable_within_a_five_minute_bucket():
    r = StubRenderer()
    a = r.render(agent_id=7, tick=10, cell=3, wake_class=1)
    b = r.render(agent_id=7, tick=14, cell=3, wake_class=1)  # 同じ 5 分バケツ
    c = r.render(agent_id=7, tick=15, cell=3, wake_class=1)  # 次のバケツ
    d = r.render(agent_id=8, tick=10, cell=3, wake_class=1)
    assert a.text == b.text != c.text
    assert a.text != d.text
    assert a.block_ids and a.block_ids == c.block_ids


# ---------------------------------------------------------------- テープ書き出し
def test_bridge_writes_every_call_to_the_tape(tmp_path):
    writer = TapeWriter(tmp_path / "tape")
    bridge = LLMBridge(MockLLM(master_seed=1), tape=writer)
    for tick in range(12):
        bridge.call(agent_id=tick % 3, tick=tick, wake_class=1, cell=5)
    bridge.close()
    tape = Tape(tmp_path / "tape")
    assert len(tape) == 12 == bridge.n_calls == bridge.n_tape_rows
    assert tape.n_blocks == 1  # 共有静的ブロックは intern される
    row = next(iter(tape.rows()))
    assert row.response.startswith("理由: ") and row.params_hash
    assert (tmp_path / "tape" / CALLS_FILENAME).exists()
    assert (tmp_path / "tape" / BLOCKS_FILENAME).exists()


def test_replay_hits_the_tape_and_never_calls_a_live_model(tmp_path):
    writer = TapeWriter(tmp_path / "tape")
    rec = LLMBridge(MockLLM(master_seed=1), tape=writer)
    made = [rec.call(agent_id=i, tick=i, wake_class=1, cell=i) for i in range(5)]
    rec.close()

    rep = LLMBridge(BoomLLM(), mode="replay", replay=tmp_path / "tape")
    for i, original in enumerate(made):
        got = rep.call(agent_id=i, tick=i, wake_class=1, cell=i)
        assert got.text == original.text and got.source == "tape"
    assert rep.n_tape_misses == 0 and rep.tape_miss_rate == 0.0


def test_tape_miss_is_counted_and_does_not_fall_back(tmp_path):
    writer = TapeWriter(tmp_path / "tape")
    rec = LLMBridge(MockLLM(master_seed=1), tape=writer)
    rec.call(agent_id=0, tick=0, wake_class=1, cell=0)
    rec.close()

    boom = BoomLLM()
    rep = LLMBridge(boom, mode="replay", replay=Replay(tmp_path / "tape"))
    miss = rep.call(agent_id=999, tick=7, wake_class=1, cell=3)
    assert miss.tape_miss and miss.text == "" and miss.source == "tape_miss"
    assert rep.n_tape_misses == 1 and boom.n_calls == 0
    assert miss.action_code == -2  # 未定義行動=安全弁(待機)へ落ちる


def test_replay_mode_requires_a_tape():
    with pytest.raises(ValueError):
        LLMBridge(MockLLM(master_seed=1), mode="replay")
    with pytest.raises(ValueError):
        LLMBridge(None, mode="record")
    with pytest.raises(ValueError):
        LLMBridge(MockLLM(master_seed=1), mode="ときどき実LLM")


# ---------------------------------------------------------------- run_day の record/replay
@pytest.fixture(scope="module")
def recorded(tmp_path_factory):
    path = tmp_path_factory.mktemp("record") / "tape"
    res = run_day(tape_path=path, **SMALL)
    return res, path


def test_record_mode_produces_a_tape_with_one_row_per_call(recorded):
    res, path = recorded
    tape = Tape(path)
    assert len(tape) == res.llm_calls > 0
    assert res.tape_path == str(path) and res.mode == "record"
    assert res.bridge_counters["llm_calls"] == res.llm_calls


def test_replay_reproduces_the_run_bit_for_bit_with_zero_misses(recorded, tmp_path):
    res, path = recorded
    boom = BoomLLM()
    replayed = run_day(mode="replay", replay=path, llm=boom, **SMALL)
    assert replayed.final_hash == res.final_hash
    assert [c.combined for c in replayed.checkpoints] == [c.combined for c in res.checkpoints]
    assert np.array_equal(replayed.diagnostics, res.diagnostics)
    assert replayed.tape_miss_count == 0
    assert boom.n_calls == 0, "リプレイは実LLMを呼ばない(運用設計書 §2.5)"


def test_replay_with_a_different_seed_misses_the_tape(recorded):
    _, path = recorded
    boom = BoomLLM()
    other = dict(SMALL)
    other["seed"] = 2
    replayed = run_day(mode="replay", replay=path, llm=boom, **other)
    assert replayed.tape_miss_count > 0
    assert boom.n_calls == 0
    assert replayed.bridge_counters["tape_miss_rate"] > 0.0


# ---------------------------------------------------------------- 診断行
def test_the_five_diagnostic_rows_exist(recorded):
    res, _ = recorded
    day = res.diagnostics_day()
    for name in DIAG_DAY_ROWS:
        assert name in day, name
    for column in ("parse_errors", "tape_misses", "conversations_opened", "undefined_actions"):
        assert column in DIAG_RUN_COLUMNS


def test_parse_error_rate_is_zero_with_the_mock(recorded):
    """B11 実測「2行形の書式順守=1.000」の再現(MockLLM は必ず2行形)。"""
    res, _ = recorded
    assert res.parse_error_rate == 0.0
    assert res.undefined_action_count == 0
    assert res.bridge_counters["parse_error_rate"] == 0.0
    assert MOCK_RNG_DOMAIN == "llm.mock"


# ---------------------------------------------------------------- W2 規模(nightly)
@pytest.mark.slow
def test_record_and_replay_at_five_thousand_agents(tmp_path):
    """C3 受け入れ: 5,000 体の 1 シミュ日を録画→リプレイで**同一ハッシュ・テープ外0**。"""
    path = tmp_path / "tape5000"
    rec = run_day(n_agents=5_000, seed=1, ticks=1_440, checkpoint_every=360,
                  n_cells=139, tape_path=path)
    rep = run_day(n_agents=5_000, seed=1, ticks=1_440, checkpoint_every=360,
                  n_cells=139, mode="replay", replay=path, llm=BoomLLM())
    print(f"\n[record] {rec.final_hash}\n[replay] {rep.final_hash}\n"
          f"  呼 {rec.llm_calls:,} / テープ {len(Tape(path)):,} 行 / "
          f"テープ外 {rep.tape_miss_count} / 書式エラー率 {rec.parse_error_rate:.4f}")
    assert rep.final_hash == rec.final_hash
    assert rep.tape_miss_count == 0
    assert rec.parse_error_rate == 0.0


# ------------------------------------------- 本物のレンダラ(C3 結線)での record/replay
def test_the_default_renderer_is_the_real_one(recorded):
    """``run_day`` の既定は本物の ``perception.renderer.Renderer``(C3 結線)。"""
    res, _ = recorded
    assert res.renderer_name == "perception.Renderer"
    assert res.renderer_counters["render_calls"] == res.llm_calls > 0
    # 共有ブロック(B0-B4b)がテープの共有表へ intern されている
    assert res.bridge_counters["llm_calls"] == res.llm_calls


def test_real_renderer_record_replay_is_bit_for_bit_on_a_synthetic_world(tmp_path):
    """合成世界+**本物のレンダラ**でも録画→再生が完全一致・テープ外 0。"""
    path = tmp_path / "tape_real"
    rec = run_day(tape_path=path, **SMALL)
    assert rec.renderer_name == "perception.Renderer"
    tape = Tape(path)
    assert len(tape) == rec.llm_calls > 0
    # B0/B4b は 1 本、B1 は種別ぶん、B2 はセルぶん…= 共有表は 1 本より多く、呼数よりずっと少ない
    assert 1 < tape.n_blocks < len(tape)

    boom = BoomLLM()
    rep = run_day(mode="replay", replay=path, llm=boom, **SMALL)
    assert rep.final_hash == rec.final_hash
    assert [c.combined for c in rep.checkpoints] == [c.combined for c in rec.checkpoints]
    assert np.array_equal(rep.diagnostics, rec.diagnostics)
    assert rep.tape_miss_count == 0 and boom.n_calls == 0


def test_stub_renderer_path_still_records_and_replays(tmp_path):
    """``renderer="stub"`` の安い経路も同じ性質を保つ(テストの逃げ道が生きている)。"""
    path = tmp_path / "tape_stub"
    rec = run_day(tape_path=path, renderer="stub", **SMALL)
    assert rec.renderer_name == "StubRenderer" and rec.renderer_counters == {}
    boom = BoomLLM()
    rep = run_day(mode="replay", replay=path, llm=boom, renderer="stub", **SMALL)
    assert rep.final_hash == rec.final_hash
    assert rep.tape_miss_count == 0 and boom.n_calls == 0
    assert Tape(path).n_blocks == 1  # スタブの共有ブロックは 1 本だけ


def test_the_two_prompt_hashes_are_both_deterministic_and_different():
    """``BridgeResult.prompt_hash``(レンダラ blake3)と ``tape_prompt_hash``(テープ鍵)。"""
    from shibuya.agents.state import AgentState
    from shibuya.engine.llm_bridge import PerceptionRendererAdapter
    from shibuya.perception.renderer import Renderer as PerceptionRenderer
    from shibuya.world.state import World

    w = World.synthetic(n_cells=9, seed=1)
    a = AgentState(4)
    a.cell[:] = 0
    adapter = PerceptionRendererAdapter(PerceptionRenderer(w, a, seed=1))
    bridge = LLMBridge(MockLLM(master_seed=1), renderer=adapter)
    bridge.prepare_tick(700)
    r1 = bridge.call(0, 700, 1, 3)
    bridge.prepare_tick(700)
    r2 = bridge.call(0, 700, 1, 3)
    assert r1.prompt_hash == r2.prompt_hash and len(r1.prompt_hash) == 64
    assert r1.tape_prompt_hash == r2.tape_prompt_hash
    assert r1.prompt_hash != r1.tape_prompt_hash, "2 本のハッシュは別物(docstring 参照)"
