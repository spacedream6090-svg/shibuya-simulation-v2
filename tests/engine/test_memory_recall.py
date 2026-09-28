"""記憶 第 1 段 6b: **想起**(記憶アジェンダ v1 M4・M5・M6・M11・M15・M16・修正 2・修正 4・第295)のテスト。

正典: ``docs/design/v2-memory-stage1-implementation-agenda.md`` §0 6b・§2 項 1〜8。
見るもの: (a) q と ID 一致・k(会話 3/他 2)・τ・候補が k 未満なら補う (b) 項の定型 ≤20 tok
(c) B5 の最後に「記憶」の 1 行・≤60 tok・個体枠 300・0 件なら行を出さない・off は 1 バイトも変わらない
(d) テープ版 3 の ``recalled_rows``(旧テープは空で読む・class_rank 不変) (e) K-2/K-5 の計器
(f) ラン: on の描画に記憶の行が載り、mock の挙動は off と同じ・off のテープの列は全行空。
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.agents.state import (
    MEMORY_FIELDS,
    RESULT_TEXT,
    AgentKind,
    AgentState,
    ResultCode,
    WakeCondition,
)
from shibuya.engine import memory as M
from shibuya.engine.familiarity import place_thing
from shibuya.engine.tape import (
    CALLS_FILENAME,
    CALLS_SCHEMA,
    CALLS_SCHEMA_V2_DEFAULTS,
    TAPE_SCHEMA_METADATA_KEY,
    TAPE_SCHEMA_VERSION,
    Tape,
    TapeRow,
    TapeWriter,
)
from shibuya.perception import templates as T
from shibuya.perception.channels import estimate_tokens
from shibuya.perception.renderer import Renderer, memory_item_text
from shibuya.world.state import World

SRC = Path("src/shibuya")
GEN = int(WakeCondition.PLAN_GENERAL)
TALK = int(WakeCondition.CONVERSATION_TURN)


def table(n: int = 3, rows: int = 16) -> AgentState:
    a = AgentState(n, memory_columns=True, memory_n=rows)
    with a.writable():
        a.cell[:] = 3
    return a


def put(lay, a, tick, agent, kind, *, partner=-1, obj=-1, result=0, cell=3):
    return int(lay.record(a, tick, np.array([agent]), np.array([M.EVENT_KINDS[kind]]),
                          np.array([partner]), np.array([obj]), np.array([result]),
                          np.array([cell]))[0])


# ================================================================= (a) 想起
def test_k_is_three_for_conversation_and_two_otherwise():
    a = table()
    lay = M.MemoryLayer(3, 16, minutes_per_tick=1.0)
    for j in range(5):
        put(lay, a, 100, 0, "buy", obj=10 + j, cell=9)
    assert M.RECALL_K_CONVERSATION == 3 and M.RECALL_K_OTHER == 2
    assert len(lay.recall(a, 0, 101, TALK)) == 3
    for cond in (GEN, int(WakeCondition.INTEROCEPTION), int(WakeCondition.CELL_BLOCK),
                 int(WakeCondition.ACTIVITY_EXPIRY), int(WakeCondition.OVERHEARD)):
        assert len(lay.recall(a, 0, 101, cond)) == 2
    assert lay.recall(a, 1, 101, GEN) == []  # 空の表
    assert lay.recall_stats["calls_empty_table"] == 1


def test_tau_cuts_old_rows():
    a = table()
    lay = M.MemoryLayer(3, 16, minutes_per_tick=1.0)
    put(lay, a, 0, 0, "buy", obj=10)
    assert M.RECALL_TAU == -2.0 and lay.tau == M.RECALL_TAU  # 第295 親決定(仮置き −1.0 → −2.0)
    # A = ln(1/0.5) − 0.5·ln(1001) ≈ −2.76 < −1.0
    assert lay.recall(a, 0, 1000, GEN) == []
    assert lay.recall_stats["calls_zero"] == 1 and lay.recall_stats["rows_candidate_below_tau"] == 1
    lay.tau = -3.0
    got = lay.recall(a, 0, 1000, GEN)
    assert [g.obj for g in got] == [10]


def test_id_match_comes_first_and_the_rest_is_filled_by_score():
    a = table()
    lay = M.MemoryLayer(3, 16, minutes_per_tick=1.0)
    far = put(lay, a, 100, 0, "buy", obj=50, cell=9, result=int(ResultCode.CLOSED))  # importance 4
    here = put(lay, a, 100, 0, "buy", obj=51, cell=3)                                # importance 2
    other = put(lay, a, 99, 0, "move", obj=int(place_thing(8)), cell=8)
    got = lay.recall(a, 0, 101, GEN)
    assert [g.row for g in got] == [here, far]  # 一致(セル 3)が先・残りは score 順で補う
    assert lay.recall_stats["filled_rows"] == 1 and lay.recall_stats["calls_filled"] == 1
    assert other not in [g.row for g in got]


def test_partner_object_place_and_last_result_are_query_keys():
    from shibuya.engine import commit as C

    a = table()
    lay = M.MemoryLayer(3, 16, minutes_per_tick=1.0)
    talk = put(lay, a, 100, 0, "talk", partner=7, cell=9)
    shop = put(lay, a, 100, 0, "buy", obj=42, cell=9)
    place = put(lay, a, 100, 0, "notice", obj=int(place_thing(3)), cell=9)
    fail = put(lay, a, 100, 0, "eat", obj=77, cell=9, result=int(ResultCode.OUT_OF_STOCK))
    for j in range(4):  # 一致しないが score の高い行(失敗=importance 4)
        put(lay, a, 100, 0, "queue", obj=200 + j, cell=9, result=int(ResultCode.CLOSED))
    assert [g.row for g in lay.recall(a, 0, 101, TALK, inviter=7)][0] == talk
    with a.writable():
        a.poi_ref[0] = 42
    assert shop in [g.row for g in lay.recall(a, 0, 101, GEN)]
    with a.writable():
        a.poi_ref[0] = -1
    assert place in [g.row for g in lay.recall(a, 0, 101, GEN)]  # 場所=−(cell+2)
    with a.writable():
        a.cell[0] = 11
        a.last_action[0] = C.ACT_EAT
        a.last_result[0] = int(ResultCode.OUT_OF_STOCK)
    assert [g.row for g in lay.recall(a, 0, 101, GEN)][0] == fail  # 直前の結果と同じ種類×結果


def test_recall_items_carry_the_gist():
    a = table()
    lay = M.MemoryLayer(3, 16, minutes_per_tick=1.0)
    s0 = SimpleNamespace(session_id=0, participants=[0, 1])
    lay.after_tick(a, 5, conv=SimpleNamespace(n_opened=1, sessions={0: s0}))
    lay.note_utterance(a, 0, 6, s0, "", "駅の混雑を避けたいから。")
    got = lay.recall(a, 0, 7, TALK, inviter=1)
    assert got[0].partner == 1 and got[0].gist == "駅の混雑を避けたいから。"


# ================================================================= (b) 項の定型
def item(**kw):
    base = dict(row=0, last_tick=0, kind=1, partner=-1, obj=-1, result=0, cell=3, gist="")
    base.update(kw)
    return SimpleNamespace(**base)


def fmt(it, names=("カフェ",)):
    return memory_item_text(it, hhmm="9:05", poi_names=list(names),
                            place_ids=["c0", "c1", "c2", "c3"], result_text=RESULT_TEXT)


def test_item_templates():
    ok = RESULT_TEXT[int(ResultCode.OK)]
    closed = RESULT_TEXT[int(ResultCode.CLOSED)]
    assert fmt(item(kind=1, obj=0)) == f"9:05 カフェで購入({ok})。"
    assert fmt(item(kind=4, obj=-(2 + 2), cell=1)) == f"9:05 c2で移動({ok})。"
    assert fmt(item(kind=2, obj=-1, cell=3, result=int(ResultCode.CLOSED))) == f"9:05 c3で食事({closed})。"
    assert fmt(item(kind=5, obj=-1, cell=-1)) == f"9:05 範囲外で乗車({ok})。"
    assert fmt(item(kind=9, partner=12)) == f"9:05 P-12と手伝い({ok})。"
    assert fmt(item(kind=7, partner=12, gist="空腹を感じたから。")) == "9:05 P-12と話した: 空腹を感じたから。"
    assert fmt(item(kind=7, partner=12)) == "9:05 P-12と話した。"
    assert fmt(item(kind=11, obj=0)) == "9:05 カフェで看板を見た。"
    assert fmt(item(kind=10, obj=-(3 + 2))) == "9:05 c3で出来事に気づいた。"
    assert len(T.MEMORY_EVENT_WORDS) == max(M.EVENT_KINDS.values()) + 1


def test_abbreviation_words_fall_back_to_the_cell_id_and_drop_the_gist():
    """⑥ 省略記法: POI 名に禁止語 → その行のセルの ID・要旨に禁止語 → 要旨を載せない(宣言)。"""
    from shibuya.perception import normalize as N

    ok = RESULT_TEXT[int(ResultCode.OK)]
    assert fmt(item(kind=1, obj=0, cell=2), names=("理容等の店",)) == f"9:05 c2で購入({ok})。"
    assert fmt(item(kind=7, partner=4, gist="駅など混んでいたから")) == "9:05 P-4と話した。"
    for text in (fmt(item(kind=11, obj=0, cell=1), names=("ほか弁",)),
                 fmt(item(kind=7, partner=4, gist="…"))):
        N.assert_no_abbreviation(text, "B5")


def test_one_item_is_capped_at_20_tokens():
    ok = RESULT_TEXT[int(ResultCode.OK)]
    got = fmt(item(kind=1, obj=0), names=("あ" * 80,))
    assert estimate_tokens(got) <= T.MEMORY_ITEM_MAX_TOKENS == 20
    assert got.startswith("9:05 あ") and got.endswith(f"で購入({ok})。")
    long_gist = fmt(item(kind=7, partner=3, gist="い" * 40))
    assert estimate_tokens(long_gist) <= 20 and long_gist.startswith("9:05 P-3と話した: い")


# ================================================================= (c) 描画
def build(n: int = 12, seed: int = 1) -> Renderer:
    w = World.synthetic(n_cells=9, seed=seed)
    a = AgentState(n)
    g = np.random.default_rng(seed)
    with a.writable():
        a.cell[:] = 0
        a.xy[:] = g.uniform(0.0, 50.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 4_000
        a.hunger[:] = 5
        a.last_result[:] = int(ResultCode.OK)
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=7)
    r.prepare_tick(600)
    return r


def test_off_and_zero_recall_render_exactly_as_before():
    r = build()
    base = r.render(0, tick=600, wake_reason=GEN)
    assert r.memory_recall is None and base.recalled_rows == ()
    r.memory_recall = lambda i, t, c, inv: []
    zero = r.render(0, tick=600, wake_reason=GEN)
    assert zero.text == base.text and zero.prompt_hash == base.prompt_hash
    assert zero.recalled_rows == () and r.memory_lines == 0
    assert "B5.memory_empty" not in T.TEMPLATES


def test_memory_line_is_the_last_line_of_b5():
    r = build()
    base = r.render(0, tick=600, wake_reason=GEN)
    seen = []

    def hook(i, t, c, inv):
        seen.append((i, t, c, inv))
        return [item(row=4, last_tick=540, kind=1, obj=0), item(row=9, last_tick=560, kind=9, partner=5)]

    r.memory_recall = hook
    out = r.render(0, tick=600, wake_reason=GEN, inviter=5)
    assert seen == [(0, 600, GEN, 5)]
    for b in ("B0", "B1", "B2", "B3", "B4", "B4b"):
        assert out.blocks[b] == base.blocks[b]
    b5 = out.blocks["B5"].decode("utf-8").split("\n")
    assert out.blocks["B5"].startswith(base.blocks["B5"])
    assert b5[-1].startswith("[B5 記憶] ") and "P-5と手伝い" in b5[-1]
    assert estimate_tokens(b5[-1]) <= T.MEMORY_CHANNEL_TOKENS
    assert out.recalled_rows == (4, 9)
    assert out.group_tokens["individual"] <= T.GROUP_TOKEN_BUDGET["individual"]
    assert T.TEMPLATES["B5.memory"] == "[B5 記憶] {items}"


def test_the_channel_keeps_the_whole_line_within_60_tokens():
    r = build()
    long_gist = "う" * 40
    r.memory_recall = lambda i, t, c, inv: [
        item(row=j, kind=7, partner=j + 1, last_tick=500, gist=long_gist) for j in range(3)
    ]
    out = r.render(0, tick=600, wake_reason=TALK)
    line = out.blocks["B5"].decode("utf-8").split("\n")[-1]
    assert line.startswith("[B5 記憶]") and estimate_tokens(line) <= 60
    s = r.memory_summary()
    assert s["line_tokens_max"] <= 60 and s["lines_over_group_budget"] == 0
    assert len(out.recalled_rows) == s["items"] == 2 and s["items_dropped_for_channel"] == 1


# ================================================================= (d) テープ版 3
def test_tape_v3_writes_recalled_rows_and_keeps_the_v2_columns_in_place(tmp_path):
    names = list(CALLS_SCHEMA.names)
    assert names[-1] == "recalled_rows" and names.index("wake_class") == 3
    assert TAPE_SCHEMA_VERSION == "shibuya.tape/3"
    with TapeWriter(tmp_path / "t") as w:
        b = w.intern_block("共有")
        w.append(TapeRow("c0", 0, 1, 1, "ph0", (b,), "pa", "応答", recalled_rows=(3, 7)))
        w.append(TapeRow("c1", 1, 1, 1, "ph1", (b,), "pa", "応答"))
    tape = Tape(tmp_path / "t")
    assert tape.schema_version == "shibuya.tape/3"
    assert tape.column("recalled_rows") == [[3, 7], []]
    assert [r.recalled_rows for r in tape.rows()] == [(3, 7), ()]


def test_a_v2_tape_reads_recalled_rows_as_empty(tmp_path):
    with TapeWriter(tmp_path / "t") as w:
        b = w.intern_block("共有")
        for i in range(3):
            w.append(TapeRow(f"c{i}", i, i, 1, f"ph{i}", (b,), "pa", f"応答{i}"))
    path = tmp_path / "t" / CALLS_FILENAME
    table_ = pq.read_table(path)
    v2_names = [n for n in CALLS_SCHEMA.names if n != "recalled_rows"]
    v2 = pa.schema([CALLS_SCHEMA.field(n) for n in v2_names],
                   metadata={TAPE_SCHEMA_METADATA_KEY: b"shibuya.tape/2"})
    pq.write_table(pa.Table.from_pydict({n: table_.column(n).to_pylist() for n in v2_names},
                                        schema=v2), path)
    tape = Tape(tmp_path / "t")
    assert tape.schema_version == "shibuya.tape/2" and tape.has_deferred_columns
    assert tape.column("recalled_rows") == [[], [], []]
    assert all(r.recalled_rows == () for r in tape.rows())
    assert set(CALLS_SCHEMA_V2_DEFAULTS) <= set(v2_names)


# ================================================================= (e)(f) ラン
@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    from shibuya.engine.run import run_day

    d = tmp_path_factory.mktemp("mem6b")
    kw = dict(n_agents=100, seed=2, ticks=1440, vocab_version="v3")
    off = run_day(tape_path=d / "off", **kw)
    mp = pytest.MonkeyPatch()
    mp.setattr(AgentState, "state_hash", lambda self: self.registry.state_hash(exclude=MEMORY_FIELDS))
    try:
        on = run_day(memory="on", tape_path=d / "on", **kw)
    finally:
        mp.undo()
    return off, on, d


def test_run_on_puts_memory_lines_and_mock_behavior_is_unchanged(runs):
    off, on, d = runs
    assert on.final_hash == off.final_hash and on.llm_calls == off.llm_calls
    s = on.run_manifest_fields()["memory_summary"]
    rec, ren = s["recall"], s["render"]
    assert rec["tau"] == M.RECALL_TAU and rec["k_conversation"] == 3 and rec["k_other"] == 2
    assert rec["counts"]["calls"] > 0 and ren["lines"] > 0
    assert ren["line_tokens_max"] <= 60 and ren["lines_over_group_budget"] == 0
    dropped = ren["items_dropped_for_channel"] + ren["items_dropped_for_group_budget"]
    assert ren["items"] == rec["counts"]["recalled_rows"] - dropped
    on_rows = Tape(d / "on").column("recalled_rows")
    assert sum(len(x) for x in on_rows) == ren["items"]
    assert all(x == [] for x in Tape(d / "off").column("recalled_rows"))
    assert Tape(d / "off").column("wake_class") == Tape(d / "on").column("wake_class")


def test_k2_and_k5_instruments_are_in_the_manifest(runs):
    _, on, _ = runs
    s = on.run_manifest_fields()["memory_summary"]
    k2, k5 = s["k2_motif_repeats"], s["k5_failure_avoidance"]
    assert {"repeats", "repeats_expected_uniform", "ratio"} <= set(k2["all"])
    assert {"failure_memories", "failure_revisits", "failure_revisit_rate", "success_memories",
            "success_revisits", "success_revisit_rate", "failure_by_result"} <= set(k5)
    assert set(k5["failure_by_result"]) <= {ResultCode(int(c)).name for c in M.K5_FAILURES}


def test_k5_counts_revisits_after_a_failure_and_k2_counts_repeats():
    a = table(n=3)
    lay = M.MemoryLayer(3, 16, minutes_per_tick=1.0)
    closed = int(ResultCode.CLOSED)
    put(lay, a, 10, 0, "buy", obj=5, result=closed)  # 失敗 → 後で同じ店に戻った
    put(lay, a, 20, 0, "buy", obj=5)
    put(lay, a, 10, 1, "buy", obj=6, result=closed)  # 失敗 → 戻らない
    for t_ in (30, 40, 50):
        put(lay, a, t_, 2, "eat", obj=8)                 # 成功の反復(n=3)=再訪
    k5 = lay._k5(a)
    assert (k5["failure_memories"], k5["failure_revisits"]) == (2, 1)
    assert (k5["success_memories"], k5["success_revisits"]) == (2, 1)
    assert k5["failure_by_result"] == {"CLOSED": {"memories": 2, "revisits": 1}}
    k2 = lay._k2(a)
    assert k2["eat"]["repeats"] == 2 and k2["all"]["repeats"] == 2


def test_memory_tau_is_passed_and_checked():
    from shibuya.engine.run import run_day

    with pytest.raises(ValueError):
        run_day(n_agents=10, ticks=2, memory="on", memory_tau=float("nan"))
    text = (SRC / "cli.py").read_text(encoding="utf-8")
    assert '"--memory-tau"' in text and "memory_tau=float(args.memory_tau)" in text


def test_recall_has_no_loop_over_rows():
    """P4: 想起は行の走査を配列演算で行う(for は想起した ≤k 件だけ)。"""
    tree = ast.parse((SRC / "engine/memory.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "recall")
    loops = [s for s in ast.walk(fn) if isinstance(s, (ast.For, ast.While, ast.comprehension))]
    assert not any(isinstance(s, ast.While) for s in loops)
    assert all(ast.unparse(s.iter) in ("picked", "out") for s in loops)
