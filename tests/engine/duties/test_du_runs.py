"""第 6 期 6-6 ② 第 1 部 店の仕事を働く人の体へ: ランの試験(合成 80 体・1 セル・店 2=店 0 は担当あり・店 1 は担当なし・店の
決まり=9:00〜21:00・物の台帳つき)。

既定 off で層が無い・担当が店に居る店は本人の判断で開く(判断なし=開かない=負の対照)・担当が居ない店はエンジンのつなぎ
(REPLACEMENT)・候補を出す条件は店の決まりの行から(行を変えると動く)・補充は本人の判断(担当の居る店にエンジンの補充なし)・
廃棄は閉店の作業(捨てた店は 05:00 のつなぎが捨てない)・労働時間の行は記録だけ・2 日と再開=通し・段 B と負の対照・記録 on/off・
監査 0・役割語の道・CLI。"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from shibuya.engine import manifest_sections as MS
from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine.duties import arm as AD
from shibuya.engine.duties import layer as LY
from shibuya.engine.duties import port as PD
from shibuya.engine.events import vocab as V
from shibuya.engine.run import run_day
from shibuya.engine.systems import table as TB
from shibuya.world.processes.records import DEVIATION_CODES, DeviationVocab

from tests.engine.duties._du import KW, RULE_FROM, ST, UN, RULE_TO, STEP_NS, TPD, by_pref, choose, du, duty_events, fresh

SCHED = DEVIATION_CODES[DeviationVocab.SCHEDULED]
SHORT_FROM, SHORT_TO = RULE_FROM, RULE_FROM + 60
REPL = DEVIATION_CODES[DeviationVocab.REPLACEMENT]


def _minute(e) -> int:
    return (int(e.t_ns) // STEP_NS) % TPD


def _audit(r) -> dict:
    lay = r.duties_layer
    return LY.audit_causes(r.event_log.events(), step_ns=STEP_NS, issued=lay.issued_keys(), role_ids=lay.role_call_ids())


# ================================================================= 既定 off
def test_default_off_builds_nothing(monkeypatch, tmp_path):
    with du(on=False):
        r = run_day(state_out=tmp_path / "state", stop_at_tick=120, **dict(KW, ticks=240), **fresh(monkeypatch))
    assert getattr(r, "duties_layer", "missing") is None
    m = r.run_manifest_fields()
    assert "duties" not in m and "duties" not in m["calls_by_model"]
    assert duty_events(r) == []
    assert r.runner.opening.duties is None and r.runner.shelf.duties is None and r.runner.waste.duties is None
    bundle = RS.read_state(tmp_path / "state" / r.resume["state_files"][-1]["file"])
    assert [p for p in bundle.items if p.startswith("duties.")] == []
    assert AD.FP_KEY not in bundle.header["fingerprint"]
    assert TB.SPECS["duties"].when == "duties"


# ================================================================= 腕 arm(仮のモデルのまま 1 日)
@pytest.fixture(scope="module")
def day_run():
    mp = pytest.MonkeyPatch()
    try:
        extra = fresh(mp)
        with du():
            r = run_day(**KW, **extra)
    finally:
        mp.undo()
    return r


def test_staffed_store_is_unlocked_by_the_person_and_the_other_by_the_bridge(day_run):
    r = day_run
    staff = r.runner.opening.staff_of_poi
    assert staff[ST] >= 0 and staff[UN] < 0
    rows = r.runner.log.rows_for("store_opening")
    # 担当の居る店(0): 最初の設定(刻み 0)のほかは本人の行(SCHEDULED)だけ・担当の居ない店(1): エンジンのつなぎ(REPLACEMENT)
    s0 = rows[(rows["subject_id"] == ST) & (rows["tick"] > 0)]
    s1 = rows[(rows["subject_id"] == UN) & (rows["tick"] > 0)]
    assert s0.size >= 2 and set(s0["deviation"].tolist()) == {SCHED}
    assert s1.size >= 2 and set(s1["deviation"].tolist()) == {REPL}
    evs = duty_events(r)
    unlocked = [e for e in evs if e.what == LY.W_UNLOCK]
    closed = [e for e in evs if e.what == LY.W_LOCK]
    assert unlocked and closed and all(int(e.who) == int(staff[ST]) and e.where == ("poi", ST) for e in unlocked + closed)
    assert len(unlocked) + len(closed) == s0.size
    # 開けたのは店の決まりの区切りの前 15 分から(遅れは区切りとの差=負は早め)
    assert all(_minute(e) >= RULE_FROM - LY.SHOP_LEAD_MINUTES for e in unlocked)
    assert all(int(e.how_much) >= -LY.SHOP_LEAD_MINUTES for e in unlocked)
    m = r.run_manifest_fields()["duties"]
    tot = m["coverage"]["total"]
    assert tot["unlock"]["person"] + tot["lock"]["person"] == len(unlocked) + len(closed)
    assert tot["unlock"]["bridge"] + tot["lock"]["bridge"] == s1.size
    by_o = m["coverage"]["by_employment_origin"]
    assert by_o["unlock"]["round_robin"]["bridge"] == 0 and by_o["unlock"]["none"]["person"] == 0  # 雇用の行の無い店=つなぎだけ
    assert m["shop"]["stores_with_employment"] == 1 and m["shop"]["stores_by_staff_origin"]["round_robin"] == 1
    assert all(e.origin == "store_rules:unknown" for e in unlocked)  # 出どころの印(合成の資産は列 src が無い)
    assert not [k for k in m["labor_over"] if "open" in k]  # 〔検収 L2〕鍵の名に open を入れない
    assert _audit(r)["violations"] == 0


def test_manifest_section_and_calls_by_model(day_run):
    r = day_run
    m = r.run_manifest_fields()
    d = m["duties"]
    assert set(d) == set(LY.CONFIG_KEYS) | set(LY.OBSERVED_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("duties.") and s == MS.CONFIG} \
        == set(LY.CONFIG_KEYS)
    assert {p.split(".", 1)[1] for p, s in MS.PATHS.items() if p.startswith("duties.") and s == MS.OBSERVED} \
        == set(LY.OBSERVED_KEYS)
    assert MS.unlisted_in_mixed(m) == []
    j, t = r.duties_layer.model_calls()
    assert m["calls_by_model"]["duties"] == {"judge_model": j, "llm": t} and j > 0
    assert m["calls_by_model"]["judge_model"] == j
    assert d["common_knowledge"]["line"] == "店の決まり: 営業 9:00〜21:00。(出どころ不明)"
    assert d["labor_over"]["enforced"] is False


# ================================================================= 負の対照: 判断なし=開かない
def test_without_the_decision_the_staffed_store_stays_closed(monkeypatch):
    def keep_closed(ctx, presented):
        return "wait"

    with choose(monkeypatch, keep_closed), du():
        r = run_day(**dict(KW, ticks=12 * 60), **fresh(monkeypatch))
    now = np.asarray(r.runner.world.pois.open_now)
    assert now[ST] == 0 and now[UN] == 1  # 正午: 担当の居る店は閉じたまま・担当の居ない店はつなぎが開けた
    assert [e for e in duty_events(r) if e.what in (LY.W_UNLOCK, LY.W_LOCK)] == []
    rows = r.runner.log.rows_for("store_opening")
    assert rows[(rows["subject_id"] == ST) & (rows["tick"] > 0)].size == 0
    assert r.run_manifest_fields()["duties"]["meter"].get("shop:not_yet", 0) > 0


def test_a_sleeping_staff_is_bridged_like_an_absent_one(monkeypatch):
    """担当が店で寝ている店は担当が居ない店と同じ(開閉の過程の REPLACEMENT)=寝ている体の代わりに店が止まらない。"""
    real = LY.DutiesLayer._here
    monkeypatch.setattr(LY.DutiesLayer, "_here", lambda self: (real(self)[0], np.zeros(self._emp_agent.size, dtype=bool)))
    with choose(monkeypatch, lambda ctx, presented: "wait"), du():
        r = run_day(**dict(KW, ticks=12 * 60), **fresh(monkeypatch))
    rows = r.runner.log.rows_for("store_opening")
    st = rows[(rows["subject_id"] == ST) & (rows["tick"] > 0)]
    assert st.size >= 1 and set(st["deviation"].tolist()) == {REPL}
    assert int(np.asarray(r.runner.world.pois.open_now)[ST]) == 1


# ================================================================= 〔検収 M1〕雇用の行を持つ体なら誰でも・出どころ別のカバー率
def test_a_second_employee_acts_and_coverage_is_split_by_origin(monkeypatch):
    """店 ST に W21c の雇用の行が 2 行(体 30 → 体 9 の順)・店 UN は丸振り。体 30 を起きていない扱いにすると 2 人目(体 9)が
    開け閉めする(1 店 1 刻み 1 人=雇用の行の順で最初の居る体)。カバー率は W21c と丸振りに分かれる。"""
    first, second = 30, 9
    real = LY.DutiesLayer._here

    def here(self):
        h, aw = real(self)
        return h, aw & (self._emp_agent != first)

    monkeypatch.setattr(LY.DutiesLayer, "_here", here)
    with choose(monkeypatch, by_pref("unlock", "lock", "restock", "discard")), du():
        r = run_day(**KW, **fresh(monkeypatch, unstaffed=-1, w21c=[(first, ST), (second, ST)]))
    evs = duty_events(r)
    st_ev = [e for e in evs if e.where == ("poi", ST)]
    assert st_ev and {int(e.who) for e in st_ev} == {second}
    m = r.run_manifest_fields()["duties"]
    assert m["shop"]["stores_with_2plus_employment"] == 1 and m["shop"]["stores_by_staff_origin"]["w21c"] == 1
    assert m["meter"].get("present:second_or_later", 0) > 0
    by_o = m["coverage"]["by_employment_origin"]
    for origin in ("w21c", "round_robin"):  # 本人の行動が両方の出どころにある(項目のどれか)
        assert any(by_o[it].get(origin, {}).get("person", 0) > 0 for it in by_o), origin
    rows = r.runner.log.rows_for("store_opening")
    assert REPL not in set(rows[(rows["subject_id"] == ST) & (rows["tick"] > 0)]["deviation"].tolist())
    assert _audit(r)["violations"] == 0


# ================================================================= 〔検収 M2〕バックヤードが空なら補充の候補を出さない
def test_no_restock_offer_when_the_backroom_is_empty(monkeypatch):
    from shibuya.engine.processes import goods_flow as GF

    monkeypatch.setattr(GF.DeliveryInboundProcess, "step", lambda self, t: None)  # 納品が来ない=バックヤードはいつも 0
    with choose(monkeypatch, by_pref("restock", "unlock", "lock")), du():
        r = run_day(**KW, **fresh(monkeypatch))
    m = r.run_manifest_fields()["duties"]
    assert m["decisions"].get("shelf", 0) == 0 and m["shelf"].get("person_failed", 0) == 0
    assert m["shelf"]["no_notice_empty_backroom"] > 0


# ================================================================= 〔検収 M4〕補充の「居る」は開閉と同じ(種別を見ない)
def test_restock_presence_ignores_the_agent_kind(monkeypatch):
    """担当が種別 従業者でない(通勤者=W21c の担当)店を模して has_permission をいつも偽に=腕 arm のつなぎは店に居て起きている
    担当の店を補充しない(本人が補充する)。"""
    from shibuya.engine.processes import goods_flow as GF

    monkeypatch.setattr(GF.ShelfRestockProcess, "has_permission",
                        lambda self, a, p: np.zeros(np.asarray(a).size, dtype=bool))
    with choose(monkeypatch, by_pref("restock", "unlock", "lock")), du():
        r = run_day(**KW, **fresh(monkeypatch))
    rows = r.runner.log.rows_for("shelf_stock_restock")
    st = rows[rows["subject_id"] == ST]
    assert st.size and REPL not in set(st["deviation"].tolist())
    assert [e for e in duty_events(r) if e.what == LY.W_RESTOCK]


# ================================================================= 〔検収 M3〕店の決まりの出どころの印
def test_store_rules_carry_the_source_mark(monkeypatch):
    with choose(monkeypatch, by_pref("unlock", "lock")), du():
        r = run_day(**dict(KW, ticks=12 * 60), **fresh(monkeypatch, src={ST: "category_default", UN: "osm_opening_hours"}))
    m = r.run_manifest_fields()["duties"]
    assert m["common_knowledge"]["line"] == "店の決まり: 営業 9:00〜21:00。(出どころ category_default=作り物の印)"
    ev = [e for e in duty_events(r) if e.what == LY.W_UNLOCK]
    assert ev and all(e.origin == "store_rules:category_default" for e in ev)
    by_s = m["coverage"]["by_rule_source"]["unlock"]
    assert by_s["category_default"]["person"] == len(ev) and by_s["osm_opening_hours"]["bridge"] >= 1
    assert any(k.endswith(":category_default") for k in m["delay_minutes"])
    assert m["rules"]["rule_sources"] == ["category_default", "osm_opening_hours"]


# ================================================================= 候補を出す条件は店の決まりの行から
def test_the_offer_moves_with_the_store_rules(monkeypatch):
    def first_unlock(per_poi):
        with choose(monkeypatch, by_pref("unlock", "lock", "wait")), du():
            r = run_day(**dict(KW, ticks=16 * 60), **fresh(monkeypatch, per_poi=per_poi))
        ev = [e for e in duty_events(r) if e.what == LY.W_UNLOCK]
        return min(_minute(e) for e in ev), r

    a, ra = first_unlock(None)
    late = 13 * 60
    b, rb = first_unlock({ST: (late, RULE_TO)})
    assert RULE_FROM - LY.SHOP_LEAD_MINUTES <= a < late - LY.SHOP_LEAD_MINUTES
    assert b >= late - LY.SHOP_LEAD_MINUTES  # 行を変えると候補を出す刻みが動く
    assert ra.run_manifest_fields()["duties"]["common_knowledge"]["line"] == "店の決まり: 営業 9:00〜21:00。(出どころ不明)"
    assert rb.run_manifest_fields()["duties"]["common_knowledge"]["line"] == "店の決まり: 営業 13:00〜21:00。(出どころ不明)"


# ================================================================= 補充は本人の判断
def test_restock_is_the_persons_decision_and_the_engine_does_not_restock_a_staffed_store(monkeypatch):
    with choose(monkeypatch, by_pref("restock", "unlock", "lock", "wait")), du():
        r = run_day(**KW, **fresh(monkeypatch))
    evs = [e for e in duty_events(r) if e.what == LY.W_RESTOCK]
    assert evs and all(e.where == ("poi", ST) for e in evs) and all(int(e.how_much) > 0 for e in evs)
    rows = r.runner.log.rows_for("shelf_stock_restock")
    s0 = rows[rows["subject_id"] == ST]
    assert s0.size and REPL not in set(s0["deviation"].tolist())  # 担当の居る店にエンジンの補充(10:00 のつなぎ)なし
    assert int(np.count_nonzero(s0["deviation"] == SCHED)) == len(evs)
    m = r.run_manifest_fields()["duties"]
    assert m["coverage"]["total"]["restock"]["person"] == len(evs)
    assert m["coverage"]["total"]["restock"]["bridge"] == int(np.count_nonzero(rows[rows["subject_id"] == UN]["deviation"]
                                                                              == REPL))
    assert _audit(r)["violations"] == 0


def test_without_the_decision_the_shelf_is_not_restocked_by_the_engine_at_a_staffed_store(monkeypatch):
    with choose(monkeypatch, by_pref("serve", "unlock", "lock", "wait")), du():
        r = run_day(**KW, **fresh(monkeypatch))
    rows = r.runner.log.rows_for("shelf_stock_restock")
    assert rows[rows["subject_id"] == ST].size == 0
    assert [e for e in duty_events(r) if e.what == LY.W_RESTOCK] == []
    assert r.run_manifest_fields()["duties"]["meter"].get("shelf:serve", 0) > 0


# ================================================================= 廃棄は閉店の作業
def test_discard_is_a_closing_task_and_the_morning_bridge_skips_it(monkeypatch):
    from shibuya.engine import resolve as R
    from shibuya.engine.processes import goods_flow as GF

    calls = []
    real = R.discard_to_bin

    def spy(world, ledger, stores, qty, step, slot=None):
        calls.append((int(step), sorted(set(np.asarray(stores, dtype=np.int64).tolist()))))
        return real(world, ledger, stores, qty, step, slot=slot)

    monkeypatch.setattr(R, "discard_to_bin", spy)
    with choose(monkeypatch, by_pref("discard", "unlock", "lock", "restock", "wait")), du():
        # 担当の居る店(廃棄率のある棚)の決まりは 9:00〜10:00(売り切れる前に閉める=売れ残りがある)
        r = run_day(**dict(KW, sim_days=2), **fresh(monkeypatch, per_poi={ST: (SHORT_FROM, SHORT_TO)}))
    evs = duty_events(r)
    binned = [e for e in evs if e.what == LY.W_DISCARD]
    locks = [e for e in evs if e.what == LY.W_LOCK]
    assert binned and locks and min(int(e.t_ns) for e in locks) <= min(int(e.t_ns) for e in binned)
    assert all(e.where == ("poi", ST) for e in binned) and all(int(e.how_much) > 0 for e in binned)
    assert all(_minute(e) >= SHORT_TO - LY.SHOP_LEAD_MINUTES for e in binned if int(e.t_ns) < TPD * STEP_NS)
    morning = TPD + GF.WASTE_TO_BIN_MINUTE  # 1 日目の 05:00(つなぎ)
    engine = [s for st, s in calls if st == morning]
    assert all(ST not in s for s in engine)  # 担当が捨てた店はつなぎが捨てない
    assert any(st == GF.WASTE_TO_BIN_MINUTE and ST in s for st, s in calls)  # 0 日目の 05:00 は捨てた店が無い=つなぎが捨てた
    m = r.run_manifest_fields()["duties"]
    assert m["waste"]["person_bin"] == len(binned) and m["coverage"]["total"]["discard_rows"]["person"] > 0


# ================================================================= 労働時間の行は記録だけ
def test_labor_rows_are_recorded_and_do_not_stop(monkeypatch):
    monkeypatch.setattr(LY, "labor_params", lambda asof: {"max_hours_per_day": 1, "max_hours_per_week": 40,
                                                          "min_rest_days_per_week": 1, "enforced": False})
    with choose(monkeypatch, by_pref("unlock", "lock", "restock", "discard")), du():
        r = run_day(**KW, **fresh(monkeypatch))
    m = r.run_manifest_fields()["duties"]
    assert m["labor_over"]["over_day_hours"] >= 1 and m["labor_over"]["enforced"] is False
    # 上限(1 時間)を超えた後も本人の行動は続く(止めない)
    late = [e for e in duty_events(r) if _minute(e) > RULE_FROM + 2 * 60]
    assert late


# ================================================================= 2 日と再開・記録 on/off・段 B
def _cp(r):
    return [(int(c.tick), c.behavior_hash, c.full_hash) for c in r.checkpoints if int(c.tick) >= TPD]


def test_two_days_and_resume_is_the_straight_run(monkeypatch, tmp_path):
    kw = dict(KW, sim_days=2)
    with du():
        straight = run_day(tape_path=tmp_path / "s", **kw, **fresh(monkeypatch))
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, tape_path=tmp_path / "a", **kw, **fresh(monkeypatch))
        path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
        b = run_day(resume_from=path, tape_path=tmp_path / "b", **kw, **fresh(monkeypatch, endow=False))
    assert b.final_hash == straight.final_hash and _cp(b) == _cp(straight) and _cp(b)
    bundle = RS.read_state(path)
    arm_paths = [p for _k, p in SL.arm_items({"duties": a.duties_layer}, behavior=False)]
    assert arm_paths and set(arm_paths) <= set(bundle.items)
    assert bundle.header["fingerprint"][AD.FP_KEY] == {"arm": "arm"}
    ms, mb = straight.run_manifest_fields()["duties"], b.run_manifest_fields()["duties"]
    for k in ("meter", "shop", "shelf", "waste", "coverage", "delay_minutes", "labor_over", "calls"):
        assert ms[k] == mb[k], k
    assert ms["coverage"]["total"]["unlock"]["person"] > 0


def test_resuming_with_the_arm_off_stops(monkeypatch, tmp_path):
    kw = dict(KW, sim_days=2)
    with du():
        a = run_day(state_out=tmp_path / "state", stop_at_tick=TPD, **kw, **fresh(monkeypatch))
    path = tmp_path / "state" / a.resume["state_files"][-1]["file"]
    with du(on=False), pytest.raises(ValueError, match="duties"):
        run_day(resume_from=path, **kw, **fresh(monkeypatch, endow=False))


def test_event_log_on_off_does_not_change_the_arm_run(monkeypatch):
    from shibuya.engine.events import log as EV

    prev = EV.enabled()
    try:
        with du():
            EV.set_enabled(True)
            on = run_day(**dict(KW, ticks=TPD), **fresh(monkeypatch))
            EV.set_enabled(False)
            off = run_day(**dict(KW, ticks=TPD), **fresh(monkeypatch))
    finally:
        EV.set_enabled(prev)
    assert on.final_hash == off.final_hash
    assert [(c.tick, c.behavior_hash) for c in on.checkpoints] == [(c.tick, c.behavior_hash) for c in off.checkpoints]
    assert duty_events(on) and duty_events(off) == []


def test_stage_b_has_no_undeclared_writes(monkeypatch):
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with choose(monkeypatch, by_pref("unlock", "lock", "restock", "discard")), du():
        r = run_day(**dict(KW, ticks=TPD), **fresh(monkeypatch))
    m = r.run_manifest_fields()["duties"]
    assert m["coverage"]["total"]["unlock"]["person"] > 0 and m["coverage"]["total"]["restock"]["person"] > 0


def test_stage_b_negative_control_without_the_declaration_fails(monkeypatch):
    spec = TB.SPECS["duties"]
    paths = frozenset(p for p in spec.writes.paths if not p.startswith("DU*:"))
    monkeypatch.setitem(TB.SPECS, "duties", dataclasses.replace(spec, writes=dataclasses.replace(spec.writes, paths=paths)))
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with choose(monkeypatch, by_pref("unlock", "lock")), du(), pytest.raises(AssertionError, match="宣言の外"):
        run_day(**dict(KW, ticks=TPD), **fresh(monkeypatch))


# ================================================================= 役割語の道(主の判断が「補充」「開閉店」と答えた)
def test_role_words_from_the_main_decision_take_effect_at_the_store(monkeypatch):
    real = LY.DutiesLayer.run_step
    staff_box = {}

    def run_step(self, T, t_ns, td, day, **kw):
        a = int(self.shops.staff_of_poi[ST])
        staff_box["a"] = a
        if int(T) == 11 * 60:  # 11:00 に主の判断が「補充」・12:00 に「開閉店」・別の体の「補充」(店に居ない担当でない)
            self.note_role_word(a, int(T), PD.K_RESTOCK, f"{int(T)}:{a}:3")
            self.note_role_word(a + 1, int(T), PD.K_RESTOCK, f"{int(T)}:{a + 1}:3")
            self.note_role_word(a, int(T), "接客", f"{int(T)}:{a}:4")
        if int(T) == 12 * 60:
            self.note_role_word(a, int(T), PD.K_SHOP, f"{int(T)}:{a}:3")
        return real(self, T, t_ns, td, day, **kw)

    monkeypatch.setattr(LY.DutiesLayer, "run_step", run_step)
    with choose(monkeypatch, by_pref("wait")), du():
        r = run_day(**dict(KW, ticks=13 * 60), **fresh(monkeypatch))
    evs = duty_events(r)
    a = staff_box["a"]
    role = [e for e in evs if getattr(e.cause, "call_id", "").endswith(":3")]
    assert {e.what for e in role} <= {LY.W_RESTOCK, LY.W_UNLOCK}
    assert any(e.what == LY.W_UNLOCK and _minute(e) == 12 * 60 for e in role)  # 判断の候補で「まだ」を選び続けた店を開けた
    assert all(int(e.who) == a for e in role)
    m = r.run_manifest_fields()["duties"]["role_words"]
    assert m.get("shop", 0) == 1 and m.get("other:接客", 0) == 1 and m.get("not_at_store:補充", 0) == 1
    assert m.get("restock_not_needed", 0) == 1  # 〔検収 L7〕11:00 は店が閉まっている=気づきと同じ条件で補充しない
    assert _audit(r)["violations"] == 0
    assert set(r.duties_layer.role_call_ids()) >= {f"{12 * 60}:{a}:3"}


def test_llm_bridge_hands_the_role_word_to_the_sink():
    from shibuya.engine.llm_bridge import LLMBridge
    from shibuya.llm.contract import ACTION_CODES
    from tests.engine.rights.test_rights_events import WordLLM

    got = []
    bridge = LLMBridge(WordLLM("補充"))
    res0 = bridge.call(agent_id=2, tick=1, wake_class=1, cell=0)  # 口が無い=今の道
    bridge.role_sink = lambda a, st, w, cid: got.append((a, st, w, cid))
    res = bridge.call(agent_id=2, tick=5, wake_class=1, cell=0)
    assert res.action_code == res0.action_code == ACTION_CODES["待機"]  # 体の行為は今のまま(店の中の作業)
    assert got == [(2, 5, "補充", "5:2:1")]


# ================================================================= 監査・語彙・腕の行・系・CLI
def test_audit_catches_forged_causes(day_run):
    from shibuya.engine.events.log import Event, LlmCall, Process

    r = day_run
    lay = r.duties_layer
    good = duty_events(r)
    assert good and _audit(r)["violations"] == 0
    e0 = good[0]
    forged = [
        Event(t_ns=e0.t_ns, who=e0.who, what=LY.W_RESTOCK, where=("poi", 0), cause=Process("opening")),
        Event(t_ns=e0.t_ns, who=e0.who, what=LY.W_UNLOCK, where=("poi", 0), cause=LlmCall("1:2:3")),
        Event(t_ns=e0.t_ns, who=int(e0.who) + 1, what=e0.what, where=("poi", 0), cause=e0.cause),
        Event(t_ns=e0.t_ns, who=e0.who, what=LY.W_DISCARD, where=("poi", 0), cause=e0.cause),
        Event(t_ns=e0.t_ns + STEP_NS, who=e0.who, what=e0.what, where=("poi", 0), cause=e0.cause),
    ]
    got = LY.audit_causes(forged, step_ns=STEP_NS, issued=lay.issued_keys(), role_ids=lay.role_call_ids())
    assert got["events"] == 5 and got["violations"] == 5


def test_vocabulary_is_closed_and_appended():
    assert V.VOCAB_VERSION == "events-vocab/6-4-c2"  # 〔取り込み〕6-4 C2 が後に着地=版の文字列は最後の段・仕事の 4 語のコードは不変
    assert V.FAMILIES[-1] == V.FAMILY_DUTY == "仕事"
    assert V.VOCAB[-17:-13] == tuple(f"仕事:{w}" for w in V.DUTY_WORDS)  # 後ろに連絡の 13 語(C2・105〜117)
    assert V.code_of("仕事:開けた") == 101 and V.code_of("仕事:捨てた") == 104
    assert V.code_of("勤務:知らせ") == 100  # 前の語のコードは動かない
    with pytest.raises(ValueError):
        V.code_of("仕事:片付けた")
    assert set(PD.KINDS) == {"開閉店", "補充", "接客", "なし", "廃棄"} and PD.ROLE_KINDS == {"開閉店", "補充"}


def test_arm_rows_and_system_declarations():
    keys = {r.key for r in SL.arm_rows() if r.arm == "duties"}
    assert keys == {"DUS", "DUG", "DUM", "DUQ"}
    beh = {r.key for r in SL.arm_rows() if r.arm == "duties" and r.behavior == SL.BEHAVIOR}
    assert beh == {"DUS", "DUG"}
    for r in SL.arm_rows():
        if r.arm == "duties":
            assert r.items and all(it.startswith("duties.") for it in r.items), r.key
    assert all(r.arm != "duties" for r in SL.arm_rows() if SL.arm_items({"duties": None}, behavior=False))
    sp = TB.SPECS["duties"]
    order = list(TB.TICK_ORDER)
    assert order.index("calendar_2") < order.index("duties") < order.index("memory")
    assert {"request_open_close", "restock", "discard_to_bin"} == set(sp.resolve_ops)
    for name in ("decide", "llm_receive"):
        assert "DUG:duties._role_asks" in TB.SPECS[name].writes.paths


def test_cli_flag_and_run_kind(monkeypatch):
    from shibuya import cli
    from shibuya.engine import run_kind as RK

    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    kw = dict(n_agents=30, seed=1, world_dir=None, n_cells=9, ticks=30, checkpoint_every=30, vocab_version="v3",
              activity="off")
    with du():
        r1 = cli.run(**kw)
    assert r1.run_kind == "arm" and "duties" in r1.run_manifest_fields()
    seen = {}

    def fake_run(**k):
        seen["arm"] = AD.arm()
        raise SystemExit(0)

    monkeypatch.setattr(cli, "run", fake_run)
    with du(on=False):
        with pytest.raises(SystemExit):
            cli.main(["--duties", "arm", "--agents", "5", "--ticks", "1"])
        assert seen["arm"] == "arm"


def test_arm_needs_the_world_processes():
    with du(), pytest.raises(ValueError, match="世界過程"):
        run_day(**dict(KW, ticks=10, processes=False))
