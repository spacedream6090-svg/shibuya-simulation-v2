"""C3 結線(レンダラ → bridge → run)の受入テスト。

正典
- 知覚契約書 §2.4 ⑧「同セル・同時間帯の2体で **B0-B4 のバイト差分がゼロ**」
  (§2.2「B1=種別」により**種別も揃えて読む**=C3-subE の登録済み解釈)。
- 同 §5「ハッシュ三役」/ §6 起床条件 (i)「所属セルの **B4 ハッシュ変化**」
  → 変化検出器はレンダラが作った B4 描画欄**そのもの**を読む(取りこぼし 0)。
- 行動契約書 §6「直前の結果」= 直前に**試みた**行動 + 失敗理由 + 観測値 + いま可能3語
  → ``agents.last_action``(resolve が唯一の書き手)。
- 予算宣言表 **W2**(壁時計/シミュ日)・§2.2 グループ予算(共有静的 750/セル 250/個体 300)。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import LAST_ACTION_NONE, Activity, AgentState
from shibuya.engine import change_detect as CD
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.llm_bridge import ACTION_WORD_BY_CODE, PerceptionRendererAdapter
from shibuya.engine.run import run_day
from shibuya.perception import templates as PT
from shibuya.perception.renderer import PerceptionAssets, Renderer as PerceptionRenderer
from shibuya.world.state import World

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.skipif(
    not PerceptionAssets.available(WORLD_DIR), reason="実世界資産 data/world/v2 が無い"
)

#: ``recording`` フィクスチャが作ったアダプタの置き場。
_BUILT: list["RecordingAdapter"] = []


class RecordingAdapter(PerceptionRendererAdapter):
    """描画のたびに ``(tick, agent, cell, kind, B0-B4b のバイト列)`` を残すアダプタ。

    ``run_day`` は ``AgentState`` を自前で作るのでレンダラも ``run_day`` の中で生まれる。
    本番コードにテスト専用の注入口を足さずに済ませるため、``engine.run`` が参照している
    ``PerceptionRendererAdapter`` の名前を monkeypatch で本クラスに差し替える。
    """

    def __init__(self, renderer) -> None:
        super().__init__(renderer)
        self.log: list[tuple[int, int, int, int, str]] = []
        self.b6: dict[tuple[int, int], str] = {}
        _BUILT.append(self)

    def render(self, **kw):  # type: ignore[override]
        out = super().render(**kw)
        i = int(kw["agent_id"])
        a = self.renderer.agents
        shared = chr(10).join(text for _, text in out.blocks)
        self.log.append((int(kw["tick"]), i, int(a.cell[i]), int(a.kind[i]), shared))
        self.b6[(int(kw["tick"]), i)] = out.text.split(chr(10))[-2]  # [B6 結果] の行
        return out


@pytest.fixture
def recording(monkeypatch):
    """``run_day`` が作るアダプタを記録つきに差し替える。"""
    _BUILT.clear()
    monkeypatch.setattr("shibuya.engine.run.PerceptionRendererAdapter", RecordingAdapter)
    yield _BUILT
    _BUILT.clear()


def _run(recording, **kw):
    """記録つきレンダラで 1 ラン回し ``(RunResult, RecordingAdapter)`` を返す。"""
    res = run_day(**kw)
    assert len(recording) == 1, "アダプタは 1 個だけ作られるはず"
    return res, recording[0]


def _intents(agent_id, action_code, target_id):
    n = len(agent_id)
    return C.IntentBatch(
        agent_id=np.asarray(agent_id, dtype=np.int64),
        action_code=np.asarray(action_code, dtype=np.int8),
        target_id=np.asarray(target_id, dtype=np.int32),
        resource_id=np.full(n, -1, dtype=np.int32),
        t_notice_ns=np.zeros(n, dtype=np.int64),
    )


def _rule8_groups(log):
    """``(tick, cell, kind)`` ごとに 2 体以上そろった組を返す(場外 cell<0 は除く)。"""
    groups: dict[tuple[int, int, int], list[tuple[int, str]]] = {}
    for tick, agent, cell, kind, shared in log:
        if cell < 0:
            continue
        groups.setdefault((tick, cell, kind), []).append((agent, shared))
    return {k: v for k, v in groups.items() if len(v) >= 2}


def _assert_rule8(log, want: int = 50):
    groups = _rule8_groups(log)
    keys = sorted(groups)
    assert keys, "同 tick・同セル・同種別で 2 体以上起きた場面が 1 つも無い(標本不足)"
    rng = np.random.default_rng(0)
    take = min(want, len(keys))
    picked = [keys[int(i)] for i in rng.choice(len(keys), size=take, replace=False)]
    for key in picked:
        members = groups[key]
        a0, s0 = members[0]
        for a1, s1 in members[1:]:
            assert s0 == s1, f"§2.4 ⑧ 違反 {key}: 個体 {a0} と {a1} の B0-B4b が違う"
    return len(keys), take


# ================================================================= 規約⑧(合成世界・常に走る)
def test_rule8_holds_in_situ_on_a_synthetic_world(recording, capsys):
    """走行中のランから拾った実際の起床対で B0-B4b がバイト一致する。"""
    res, rec = _run(  # ticks: D-56 以降は最初の計画境界(tick 300-480)を跨ぐ窓が要る
        recording, n_agents=400, seed=1, ticks=540, checkpoint_every=120, n_cells=25
    )
    n_groups, n_checked = _assert_rule8(rec.log)
    with capsys.disabled():
        print(
            f"\n[規約⑧ in situ・合成] 描画 {len(rec.log):,} / "
            f"(tick,セル,種別) の同席組 {n_groups:,} 中 {n_checked} 組を検査 → 全一致"
        )
    assert res.renderer_counters["render_calls"] == len(rec.log)


@real_data
def test_rule8_holds_in_situ_on_the_real_world(recording, capsys):
    """実資産(520 セル・2,337 POI)でも同じ。"""
    world = World.load(WORLD_DIR)
    res, rec = _run(
        recording, n_agents=5_000, seed=1, ticks=360, checkpoint_every=360,
        world=world, world_dir=WORLD_DIR,
    )
    n_groups, n_checked = _assert_rule8(rec.log)
    with capsys.disabled():
        print(
            f"\n[規約⑧ in situ・実データ] 描画 {len(rec.log):,} / 同席組 {n_groups:,} 中 "
            f"{n_checked} 組を検査 → 全一致 / 命中率 "
            f"{res.renderer_counters['render_cache_hit_rate']:.3f}"
        )


# ================================================================= グループ予算
def test_group_token_budgets_hold_across_a_whole_run(recording):
    """§2.2 グループ予算(750/250/300)は全描画で満たされる(超過は描画側が例外にする)。"""
    res, _ = _run(
        recording, n_agents=400, seed=3, ticks=240, checkpoint_every=240, n_cells=25
    )
    c = res.renderer_counters
    for group, cap in PT.GROUP_TOKEN_BUDGET.items():
        assert c[f"tokens_{group}_mean"] <= cap, (group, c[f"tokens_{group}_mean"], cap)
    assert 0.0 <= c["render_cache_hit_rate"] <= 1.0


# ================================================================= 変化検出 ↔ 描画
def test_the_detector_hashes_exactly_the_rows_the_renderer_renders():
    """起床条件 (i) の欄=レンダラの ``b4_field_rows``(engine 側からの同一性検査)。"""
    world = World.synthetic(n_cells=32, seed=2)
    agents = AgentState(64)
    agents.cell[:] = np.arange(64) % 32
    with world.writable():
        world.cells.density[:] = world.compute_density(agents.cell)
    assets = PerceptionAssets.synthetic(world)
    r = PerceptionRenderer(world, agents, assets, seed=1)
    det = CD.ChangeDetector(agents.n, world.n_cells, walkable_area_m2=assets.walkable_area_m2)

    g = np.random.default_rng(0)
    missed = over = changes = 0
    prev: list[bytes] | None = None
    for tick in range(0, 400, 10):
        with world.writable():
            world.cells.density[:] = g.integers(0, 3_000, size=world.n_cells)
        r.prepare_tick(tick, noise_stage=world.noise_stage_for_tick(tick))
        rows = r.b4_field_rows
        # 検出器が独立に world から作った欄と一致する(=同じ 1 本を見ている)
        assert np.array_equal(
            rows, CD.b4_block_raw(world, tick, walkable_area_m2=assets.walkable_area_m2)
        )
        res = det.detect(world, agents, tick, field_rows=rows)
        body = [r._b4(c, r._tickc, []) for c in range(world.n_cells)]
        if prev is not None:
            byte_changed = np.array([body[c] != prev[c] for c in range(world.n_cells)])
            hash_changed = np.zeros(world.n_cells, dtype=bool)
            hash_changed[res.changed_cells] = True
            changes += int(byte_changed.sum())
            missed += int((byte_changed & ~hash_changed).sum())
            over += int((~byte_changed & hash_changed).sum())
        prev = body
    assert changes > 0
    assert missed == 0, "起床条件(i) が鳴らないのに B4 の文面が変わった"
    assert over == 0, "文面が変わらないのに (i) が鳴った(無駄な起床)"


def test_open_count_no_longer_wakes_anybody():
    """営業中POI数は描画に出ない → B4 欄から外した(過検出の除去)。"""
    world = World.synthetic(n_cells=8, seed=1)
    agents = AgentState(8)
    agents.cell[:] = np.arange(8)
    with world.writable():
        world.cells.density[:] = world.compute_density(agents.cell)
    det = CD.ChangeDetector(agents.n, world.n_cells)
    det.detect(world, agents, 599)  # 開店直前
    res = det.detect(world, agents, 600)  # 全 POI 開店(密度は不変)
    assert res.changed_cells.size == 0
    assert "open_count" not in CD.B4_FIELD_COLUMNS


# ================================================================= last_action
def test_resolve_records_the_attempted_action_not_the_resulting_state():
    """失敗した行動も ``last_action`` に残る(``activity`` では復元できない)。"""
    world = World.synthetic(n_cells=4, seed=1)
    agents = AgentState(3)
    agents.cell[:] = 0
    agents.node[:] = 0
    agents.money[:] = 0  # 所持金 0 → 購入は必ず MONEY_SHORT
    assert int(agents.last_action[0]) == LAST_ACTION_NONE
    agents.freeze()
    world.freeze()
    R.apply(
        _intents([0, 1], [C.ACT_BUY, C.ACT_REST], [0, -1]),
        C.IntentBatch.empty(), agents, world, 700,
    )
    assert int(agents.last_action[0]) == C.ACT_BUY  # 失敗しても「試みた行動」が残る
    assert int(agents.last_action[1]) == C.ACT_REST
    assert int(agents.last_action[2]) == LAST_ACTION_NONE  # 動いていない個体は触らない
    assert int(agents.activity[0]) != int(Activity.SHOPPING)  # 状態には残らない


def test_losers_also_get_their_attempted_action():
    """Phase B の落選者(``LOST_ARBITRATION``)も「試みた行動」を残す。"""
    world = World.synthetic(n_cells=4, seed=1)
    agents = AgentState(2)
    agents.cell[:] = 0
    agents.node[:] = 0
    agents.freeze()
    world.freeze()
    R.apply(
        C.IntentBatch.empty(), _intents([1], [C.ACT_BUY], [0]), agents, world, 700
    )
    assert int(agents.last_action[1]) == C.ACT_BUY
    assert int(agents.last_action[0]) == LAST_ACTION_NONE


def test_engine_continuation_does_not_overwrite_the_attempted_action():
    """エンジン継続(``ENGINE_STEP``)は「新しく試みた行動」ではないので上書きしない。"""
    world = World.synthetic(n_cells=9, seed=1)
    agents = AgentState(2)
    agents.cell[:] = 0
    agents.node[:] = 0
    agents.freeze()
    world.freeze()
    R.apply(_intents([0], [C.ACT_MOVE], [8]), C.IntentBatch.empty(), agents, world, 10)
    assert int(agents.last_action[0]) == C.ACT_MOVE
    R.apply(_intents([0], [C.ENGINE_STEP], [8]), C.IntentBatch.empty(), agents, world, 11)
    assert int(agents.last_action[0]) == C.ACT_MOVE


def test_b6_names_the_attempted_action_in_a_real_run(recording, capsys):
    """B6「直前の結果」の主語が ``last_action`` の語になっている(結線の突き合わせ)。"""
    res, rec = _run(  # ticks: D-56 以降は最初の計画境界(tick 300-480)を跨ぐ窓が要る
        recording, n_agents=400, seed=7, ticks=540, checkpoint_every=540, n_cells=25
    )
    agents = res.agents  # type: ignore[attr-defined]
    words = set(ACTION_WORD_BY_CODE.values())
    named = 0
    none_line = PT.TEMPLATES["B6.result_none"]
    for line in rec.b6.values():
        if line == none_line or not line.startswith("[B6 結果] 直前の"):
            continue
        subject = line[len("[B6 結果] 直前の") :]
        assert any(subject.startswith(w) for w in words), line
        named += 1
    assert named > 0
    assert int(agents.last_action.max()) >= 0
    with capsys.disabled():
        print(f"\n[B6] 「直前の…」が出た描画 {named:,} / 全 {len(rec.b6):,}")


# ================================================================= W10 騒音段
@real_data
def test_world_and_perception_agree_on_the_w10_noise_stage():
    """world 側(``assets.noise_stage_*``)と知覚側(``PerceptionAssets``)の集約が一致する。"""
    world = World.load(WORLD_DIR)
    pa = PerceptionAssets.load(WORLD_DIR, world)
    assert world.assets.has_noise_field
    assert np.array_equal(world.assets.noise_stage_day, pa.noise_stage_day)
    assert np.array_equal(world.assets.noise_stage_night, pa.noise_stage_night)
    assert int(world.assets.noise_stage_day.max()) > 0  # 実データは 0 一色ではない


@real_data
def test_noise_stage_switches_between_day_and_night():
    """環境基準の昼 6-22 時 / 夜 22-6 時で読む配列が入れ替わる。"""
    world = World.load(WORLD_DIR)
    day = world.noise_stage_for_tick(12 * 60)
    night = world.noise_stage_for_tick(2 * 60)
    assert np.array_equal(day, world.assets.noise_stage_day)
    assert np.array_equal(night, world.assets.noise_stage_night)
    assert not np.array_equal(day, night)


def test_dynamic_noise_overrides_the_static_field():
    """``cells.noise_stage`` に値が入っていれば静的場より優先(C4 の世界過程用の口)。"""
    world = World.synthetic(n_cells=8, seed=1)
    assert not np.any(world.noise_stage_for_tick(0))
    with world.writable():
        world.cells.noise_stage[:] = 2
    assert np.all(world.noise_stage_for_tick(0) == 2)


def test_synthetic_world_has_no_static_noise_field():
    world = World.synthetic(n_cells=8, seed=1)
    assert world.assets.has_noise_field is False
    assert np.array_equal(world.assets.noise_stage_for_hour(12), np.zeros(8, dtype=np.uint8))
