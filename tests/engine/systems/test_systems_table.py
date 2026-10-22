"""1-0: 系の宣言の表 ``SYSTEMS`` の約束(草案 §2-2・§2-5・§2-6 の D ①②③⑧)。

- 呼ぶ順の 1 つの表(tick の中 25・日の頭 D1・日の終わり D2・ランの単位 R1〜R3 と最後の締め)。
- D ②: ``writes.soa`` は ``resolve_ops`` の静的な閉包そのもの。〔段 FIX〕閉包を凍結した表
  ``writes_soa_frozen.json`` との突き合わせと負の対照は ``test_fix_guards.py``(旧の手書きの対照は恒真だったので消した)。
- D ①: 系のコードが直接呼ぶ resolve の口 ⊆ ``resolve_ops``。
- D ③: 系のコードの箱の属性の参照 ⊆ ``reads.box``・scratch への書き ⊆ ``writes.scratch``・RunStats の欄への書き ⊆
  ``writes.tally``(負の対照つき)。
- D ⑧: 書く鍵(SoA の列・外の道筋)が状態台帳にある。
- scratch の受け渡しの順: 系が読む scratch の欄は、tick の中でそれより前の系が書く。
"""

from __future__ import annotations

import fnmatch

import pytest

from shibuya.engine import state_ledger as SL
from shibuya.engine.systems import allow as AL
from shibuya.engine.systems import boxes as BX
from shibuya.engine.systems import static_check as SC
from shibuya.engine.systems.spec import TIMINGS
from shibuya.engine.systems.table import SPECS, SYSTEMS

ORDER = (
    "build", "day_head",
    "experiment",  # 〔第 3 期 3-3〕申込書の改変を効かせる系(申込書を渡したランだけ立つ)
    "body", "world", "presence", "perceive_prepare", "llm_receive", "apply_responses", "detect", "plan_boundary",
    "home_meal", "wake_sources", "wake_filter", "relations_wake", "wake_assemble", "arbiter", "decide", "phase_a",
    "phase_b", "phase_c", "conversation", "activity_intent",
    "contact",  # 〔第 6 期 6-4 C1〕連絡の道具の系(腕 c1 のランだけ立つ)
    "calendar_3",  # 〔第 6 期 6-2 カレンダー 3〕雇い主・祝日の系(腕 arm のランだけ立つ・連絡の系の後・カレンダー 2 の前)
    "calendar_2",  # 〔第 6 期 6-2 カレンダー 2〕会話から生まれる予定の系(腕 arm のランだけ立つ)
    "memory", "familiarity", "energy_after", "observe",
    "checkpoint",
    "day_close", "drain", "close_final", "report",
)


def test_order_and_counts():
    assert tuple(s.name for s in SYSTEMS) == ORDER
    assert sum(1 for s in SYSTEMS if s.timing == "tick") == 29  # 〔3-3〕25+申込書の系 experiment・〔6-4 C1〕+連絡の系 contact・〔6-2 カレンダー 2〕+calendar_2・〔6-2 カレンダー 3〕+calendar_3
    ranks = [TIMINGS.index(s.timing) for s in SYSTEMS]
    assert ranks == sorted(ranks)  # ランの頭 → 日の頭 → tick → 日の終わり → ランの終わり
    assert all(s.fn is not None and s.group and s.origin for s in SYSTEMS)


@pytest.mark.parametrize("spec", SYSTEMS, ids=lambda s: s.name)
def test_d2_writes_soa_is_the_static_closure(spec):
    assert spec.writes.soa == AL.writes_for_ops(spec.resolve_ops)


@pytest.mark.parametrize("spec", [s for s in SYSTEMS if s.name != "build"], ids=lambda s: s.name)
def test_d1_d3_code_matches_the_declaration(spec):
    c = SC.analyze_spec(spec)
    assert c.resolve_calls <= spec.resolve_ops, c.resolve_calls - spec.resolve_ops
    assert c.box_refs <= spec.reads.box, sorted(c.box_refs - spec.reads.box)
    assert c.scratch_stores <= spec.writes.scratch, c.scratch_stores - spec.writes.scratch
    assert c.tally_stores <= spec.writes.tally, c.tally_stores - spec.writes.tally
    sc_refs = {r.split(".", 1)[1] for r in c.box_refs if r.startswith("scratch.")}
    assert sc_refs <= spec.reads.scratch | spec.writes.scratch, sc_refs - (spec.reads.scratch | spec.writes.scratch)


def test_d3_detects_undeclared_reads_and_writes():
    """負の対照(T2・D ③): 宣言に無い箱の属性の参照・scratch の書き・resolve の口の呼び出しが見つかる。"""

    def sys_fake(ctx, b):  # noqa: ANN001, ANN202
        from shibuya.engine import resolve as R

        x = b.layers.conv
        b.scratch.plan = x
        R.set_refractory(b.soa.agents, [], [], 0)

    c = SC.analyze(sys_fake)
    assert {"layers.conv", "scratch.plan", "soa.agents"} <= c.box_refs
    assert c.scratch_stores == {"plan"} and c.resolve_calls == {"set_refractory"}
    spec = SPECS["phase_b"]
    assert not (c.resolve_calls <= spec.resolve_ops)


def test_d8_written_keys_exist_in_the_ledger():
    soa = {f"{r.place}.{r.name}" for r in SL.LEDGER if r.is_soa}
    items = [f"{r.key}:{it}" for r in SL.external_rows() for it in r.items]
    for s in SYSTEMS:
        assert s.writes.soa <= soa, (s.name, sorted(s.writes.soa - soa))
        for pat in s.writes.paths:
            assert any(fnmatch.fnmatchcase(k, pat) for k in items), (s.name, pat)
        rs = {f for f in BX.RunStats.__dataclass_fields__} | {"sleep_counts"}
        assert s.writes.tally <= rs, (s.name, s.writes.tally - rs)
        assert s.writes.scratch <= set(BX.SCRATCH_FIELDS), (s.name, s.writes.scratch - set(BX.SCRATCH_FIELDS))


def test_scratch_is_written_before_it_is_read_in_tick_order():
    written: set[str] = set()
    for s in (x for x in SYSTEMS if x.timing == "tick"):
        need = s.reads.scratch - s.writes.scratch | (s.reads.scratch & s.writes.scratch)
        missing = {f for f in need if f not in written}
        assert not missing, (s.name, missing)
        written |= s.writes.scratch
    # llm_receive の位置 B(wake_sources の後)でも decide より前
    names = [x.name for x in SYSTEMS if x.timing == "tick"]
    assert names.index("wake_sources") < names.index("decide")


def test_every_scratch_field_has_a_writer_and_a_reader():
    w = set().union(*(s.writes.scratch for s in SYSTEMS))
    r = set().union(*(s.reads.scratch for s in SYSTEMS))
    assert w == set(BX.SCRATCH_FIELDS)
    assert r <= w
