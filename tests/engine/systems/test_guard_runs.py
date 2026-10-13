"""1-0: 書きの検査をランの単位で確かめる(草案 §3-1 の T1〜T4・合成世界の小さなラン)。

- 正: 検査を入れたランと外したランの final が同じ(書きの検査は書く値を変えない)。
- 負(T1・段 A): ある系の書く列(閉包)から 1 列を外すと、その系がその列を書いた行で ``ValueError``(ufunc.at の列は
  配列ごとの検査・ほかは numpy の読み取り専用)。合成世界で書きが起きる列だけ(世界資産が要る列=``holdings``・
  ``close_final`` の ``transit_state``・計画実行層の列は記録の道具 ``guard_runs.py`` で回す)。
- 負(T2・段 C): ある系の書く scratch の欄を外すと ``AttributeError``。
- 負(T2・段 B): ある系の書く道筋の宣言を外すと、系ごとの差の測りが宣言の外の変化を出す。
- T4: tick の頭で scratch を番兵で埋めても読む前に書かれている(古い束縛を読む所が無い)。
"""

from __future__ import annotations

import pytest

from shibuya.core import write_permit as WP
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import overrides as OV
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS

KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="on", rel_copresent="on", store_memory="on", checkpoint_every=60)


@pytest.fixture(scope="module")
def base_final():
    prev = WP.enabled()
    WP.set_enabled(True)
    try:
        return run_day(**KW).final_hash
    finally:
        WP.set_enabled(prev)


@pytest.fixture(autouse=True)
def _guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def test_guard_on_and_off_give_the_same_final(base_final):
    WP.set_enabled(False)
    assert run_day(**KW).final_hash == base_final


@pytest.mark.parametrize("system,col,where", [
    ("decide", "agents.refractory_until", "set_refractory"),      # ufunc.at(np.maximum.at)
    ("phase_c", "pois.revenue", "_complete_"),                    # ufunc.at(np.add.at)
    ("phase_c", "pois.stock", "_complete_buy"),                   # ufunc.at(np.add.at)
    ("phase_c", "agents.money", "_complete_"),                    # 添字の代入(台帳の無いラン)
    ("world", "agents.thermal", "set_thermal"),
    ("decide", "agents.mem_last", "write_memory"),                # 会話ターンの発話 → 記憶
    ("relations_wake", "agents.rel_last", "write_relations"),     # 同席の書き手
    ("detect", "agents.hunger_stage", "apply_detection"),         # field(変数) の書き(別名の表)
    ("activity_intent", "agents.activity_kind", "set_activity"),
    ("plan_boundary", "agents.activity", "wake_from_plan"),
])
def test_dropping_a_column_fails_where_it_is_written(system, col, where):
    with OV.drop_soa(system, col):
        with pytest.raises(ValueError) as ei:
            run_day(**KW)
    import traceback

    frames = [f.name for f in traceback.extract_tb(ei.value.__traceback__)]
    assert any(where in f for f in frames), frames


def test_dropping_a_scratch_field_fails():
    with OV.drop_scratch("phase_b", "plan"):
        with pytest.raises(AttributeError, match="scratch.plan"):
            run_day(**KW)


def test_dropping_a_path_shows_up_in_the_per_system_diff():
    pr = PR.Probe(check=CD.declared_check(SPECS), ticks=frozenset(range(300, 330)))
    PR.ACTIVE = pr
    try:
        with OV.drop_path("arbiter", "O42:arbiter.*"):
            pr.check = CD.declared_check(SPECS)
            run_day(**KW)
    finally:
        PR.ACTIVE = None
    assert any(s == "arbiter" and k.startswith("O42:") for _t, s, k in pr.violations), pr.violations[:5]


def test_declared_writes_cover_the_observed_changes():
    """段 B(正): 系の前後で変わった欄 ⊆ 宣言(SoA・外の道筋・積算・buffers)。"""
    pr = PR.Probe(check=CD.declared_check(SPECS), ticks=frozenset(range(0, 720, 7)))
    PR.ACTIVE = pr
    try:
        run_day(**KW)
    finally:
        PR.ACTIVE = None
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]


def test_strict_scratch_no_stale_reads(base_final):
    """T4: tick の頭で scratch を番兵で埋めても読む前に書かれている(final も同じ)。"""
    CD.STRICT_SCRATCH = True
    try:
        assert run_day(**KW).final_hash == base_final
    finally:
        CD.STRICT_SCRATCH = False
