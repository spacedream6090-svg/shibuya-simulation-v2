"""第 2 期 2-2 段 11a: ランの単位の検査(アジェンダ §2-1 の不変条件のうちランが要るもの)。

- 成立した会話の相手は必ず届く(同じ層・距離 ≤ d、または同じ B5 の単位)=1 日のランの全会話(成立の 2 か所
  ``resolve.set_conversing`` と 3 人会話 ``resolve.join_conversation`` を包んで数える)。腕 1.0/2.5 m でも同じ。
- B5 の近接行に載った人は、同じ層で半径の中か・同じ B5 の単位か・気づいた知人(全描画)。距離の値は今と同じ作り。
- 同じ入力で同じ結果(腕 distance を 2 回)。
- ``--proximity cell`` は今と同じ(本体 HEAD ``2bc7a4b`` の src で同じ構成を回した final と呼数=golden。19 構成の
  byte-check は記録 prox22/byte_check_prox22.json)。
- 再開 == 通し(腕 distance・合成の世界・2 日・日中と日の境目と、世界資産 1,000 体=検収 L2): 気づいた印は同一相手の
  不応期の配列(状態台帳 O17)にあるので再開で戻る(負の対照: 再開の最初に印を消すと final が動く)。
- 腕の違う再開は止まる(検収 M1: cell で保存 → distance で再開・逆・d の違い)。
- 描画の B5 の近接行の知人で半径の外に載る人は、関係の層の気づいた印が切れていない(検収 L1)。
- 気づく抽選の流れは K19 の検査を通る(重なり・作り直し 0・合成のラン)。
- 書きの検査(腕 distance): 検査の on/off で final が同じ・scratch の番兵・段 B(系の前後の変化 ⊆ 宣言)。
- CLI ``--proximity`` は環境変数より強い・``--proximity-d`` の腕・manifest の ``proximity``。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.core import write_permit as WP
from shibuya.engine import proximity as P
from shibuya.engine import resolve as R
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS
from shibuya.perception import renderer as RD

WORLD = "data/world/v2"
world_assets = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
#: 本体 HEAD ``2bc7a4b`` の src(``git archive`` の写し)で回した既定の腕の final と呼数(世界資産・300 体・1 日・語彙 v3・
#: 記憶+関係+同席)。作業木の腕 cell で同じ値=今と同じ(記録 prox22/README.md §6)。
HEAD_GOLDEN = ("b516af5b688c61e780d4d10d21907a4003bf8f2626b365ece35c027ccd05e9fa", 2_615)  # 〔第 4 期 4-3 段 10・版上げ 3 回目〕差し替えの世界(W16 を W21 に)で動いた(前 652cd5d900054591718093e3edeb096aaa81c9123a6586fc6cb895fa9ccdac47 / 3_049=記録 pop43)  # 〔小さな版上げ・meal_w17〕既定の食事時刻 w17 で動いた(前 ab5c9d9c0b40a26301286d4b1e8d6ca3ddabcc02b2dd7fc4261823408193e9fe / 3_077=--meal-default validation で戻る)
_HEAD_GOLDEN_PRE_MEAL_W17 = ("ab5c9d9c0b40a26301286d4b1e8d6ca3ddabcc02b2dd7fc4261823408193e9fe", 3_077)  # 〔2-4 V1〕前 f0503a35ccb501aae79dd64da80a81a65e560df143c8d18da5395a7de17d69ce / 3062  # 〔2-4 V4〕前 f1ec0336ef617de06d985fcb02bbb632476703ca917998c777d6db769f139101
GOLDEN_KW = dict(n_agents=300, seed=1, world_dir=WORLD, ticks=1440, vocab_version="v3", memory="on", relations="on",
                 rel_copresent="on")


@contextmanager
def arm(mode: str, d: float = 2.0):
    prev = (P.arm(), P.d())
    P.set_arm(mode)
    P.set_d(d)
    try:
        yield
    finally:
        P.set_arm(prev[0])
        P.set_d(prev[1])


# ================================================================= 世界資産: 全会話が届く・B5 の近接行
def _recorded_run(d: float, n_agents: int, **kw):
    built: dict = {}                                            # 組み立てが作った規則(店のセルの表つき)
    st = {"open": 0, "open_bad": [], "open_dist": [], "open_far_not_unit": 0, "open_by_unit": 0, "join": 0, "join_bad": [], "renders": 0, "seen": 0,
          "seen_bad": [], "seen_unit": 0, "seen_acq_far": 0, "seen_unit_out_of_cell": 0}
    with pytest.MonkeyPatch.context() as mp:
        orig_rule_from = P.rule_from

        def rule_from(**k):
            built["rule"] = orig_rule_from(**k)
            return built["rule"]

        mp.setattr(P, "rule_from", rule_from)
        orig_sc, orig_join = R.set_conversing, R.join_conversation
        orig_near = RD.Renderer._nearby_people_distance

        def sc(agents, inviters, invitees):
            rule = built["rule"]
            a = np.asarray(inviters, dtype=np.int64)
            b = np.asarray(invitees, dtype=np.int64)
            ok = rule.reach(agents, a, b)
            xy = np.asarray(agents.registry.xy, dtype=np.float64)
            st["open"] += int(a.size)
            dist = np.sqrt(((xy[a] - xy[b]) ** 2).sum(axis=1))
            unit = rule.by_unit(agents, a, b)
            st["open_dist"] += dist.tolist()
            st["open_by_unit"] += int(np.count_nonzero(unit))
            st["open_far_not_unit"] += int(np.count_nonzero((dist > d) & ~unit))
            st["open_bad"] += [(int(x), int(y)) for x, y in zip(a[~ok].tolist(), b[~ok].tolist())]
            return orig_sc(agents, inviters, invitees)

        def join(agents, joiners, hosts, tick):
            rule = built["rule"]
            a = np.asarray(joiners, dtype=np.int64)
            b = np.asarray(hosts, dtype=np.int64)
            ok = rule.reach(agents, a, b)
            st["join"] += int(a.size)
            st["join_bad"] += [(int(x), int(y)) for x, y in zip(a[~ok].tolist(), b[~ok].tolist())]
            return orig_join(agents, joiners, hosts, tick)

        def near(self, i, cell, tc):
            out = orig_near(self, i, cell, tc)
            nv = tc.near
            rl, idx = nv.rule, nv.index
            st["renders"] += 1
            xi, yi, bi = float(self.agents.xy[i, 0]), float(self.agents.xy[i, 1]), int(self.agents.band[i])
            pi = int(idx.pos[i])
            unit_i = int(idx.unit[pi]) if pi >= 0 else -1
            cell_now = np.asarray(self.agents.cell)
            for sp in out:
                st["seen"] += 1
                p = int(idx.pos[sp.id])
                dd = float(np.sqrt((idx.x[p] - xi) ** 2 + (idx.y[p] - yi) ** 2))
                same_unit = unit_i >= 0 and int(idx.unit[p]) == unit_i
                in_radius = int(idx.bands[p]) == bi and dd <= rl.b5_radius_m
                st["seen_unit"] += int(same_unit and not in_radius)
                st["seen_acq_far"] += int(sp.acquainted and not in_radius and not same_unit)
                if same_unit:  # 単位の仲間は店のセルの中(親の判断 10-14 の 2)
                    st["seen_unit_out_of_cell"] += int(int(cell_now[sp.id]) != int(rl.poi_cell[unit_i]))
                good = in_radius or same_unit                       # 半径の外の知人は載せない(親の判断 10-14 の 3)
                if not good or abs(sp.distance_m - max(dd, 0.1)) > 1e-6 or sp.id == i:
                    st["seen_bad"].append((int(i), int(sp.id), dd))
            return out

        mp.setattr(R, "set_conversing", sc)
        mp.setattr(R, "join_conversation", join)
        mp.setattr(RD.Renderer, "_nearby_people_distance", near)
        with arm("distance", d):
            res = cli.run(n_agents=n_agents, seed=1, world_dir=WORLD, vocab_version="v3", memory="on", relations="on",
                          rel_copresent="on", **kw)
    return res, st


@pytest.fixture(scope="module")
def distance_day():
    return _recorded_run(2.0, 1_500)


@world_assets
def test_every_opened_conversation_is_within_reach(distance_day):
    res, st = distance_day
    assert st["open"] > 10 and st["open_bad"] == [] and st["join_bad"] == []
    m = res.run_manifest_fields()["proximity"]
    assert m["mode"] == "distance" and m["d_m"] == 2.0 and m["index_builds"] == 1440
    # 同じ単位でない会話の距離は d 以内(同じ単位の会話だけ距離を見ない=B5)
    assert st["open_far_not_unit"] == 0
    assert max(d for d in st["open_dist"]) <= 2.0 or st["open_by_unit"] > 0


@world_assets
def test_b5_near_rows_are_within_radius_or_unit(distance_day):
    _res, st = distance_day
    assert st["renders"] > 1000 and st["seen"] > 0 and st["seen_bad"] == []
    assert st["seen_acq_far"] == 0 and st["seen_unit_out_of_cell"] == 0


@world_assets
def test_cell_arm_equals_the_head_golden():
    with arm("cell"):
        res = cli.run(**GOLDEN_KW)
    assert (res.final_hash, int(res.llm_calls)) == HEAD_GOLDEN
    m = res.run_manifest_fields()["proximity"]
    assert m["mode"] == "cell" and m["index_builds"] is None and getattr(res, "proximity_layer") is None


@world_assets
@pytest.mark.slow
@pytest.mark.parametrize("d", [1.0, 2.5])
def test_sensitivity_arms_keep_every_conversation_within_their_d(d):
    res, st = _recorded_run(d, 5_000)
    assert st["open"] > 0 and st["open_bad"] == [] and st["join_bad"] == [] and st["seen_bad"] == []
    assert res.run_manifest_fields()["proximity"]["d_m"] == d


# ================================================================= 合成の世界: 決定論・再開・書きの検査
SYN = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
           memory="on", relations="on", rel_copresent="on", store_memory="on", checkpoint_every=60)


def test_same_input_same_result_and_the_arm_moves_the_run():
    with arm("distance"):
        a = run_day(**SYN)
        b = run_day(**SYN)
    with arm("cell"):
        c = run_day(**SYN)
    assert (a.final_hash, a.llm_calls) == (b.final_hash, b.llm_calls)
    assert a.run_manifest_fields()["proximity"] == b.run_manifest_fields()["proximity"]
    assert c.run_manifest_fields()["proximity"]["mode"] == "cell"
    assert a.run_manifest_fields()["proximity"]["index_builds"] == 720


TPD = 1440
RES_KW = dict(n_agents=100, seed=1, n_cells=16, ticks=TPD, sim_days=2, budget=100.0, vocab_version="v3",
              memory="on", relations="on", store_memory="on", familiarity="on", hunger_model="energy",
              rel_copresent="on", checkpoint_every=60)


def _hashes(res, from_T):
    return [(c.tick, c.combined, c.behavior_hash, c.full_hash) for c in res.checkpoints if c.tick >= from_T]


@pytest.mark.parametrize("stop", [750, 1440])
def test_resume_equals_straight_on_the_distance_arm(tmp_path, stop):
    with arm("distance"):
        straight = run_day(**RES_KW)
        a = run_day(state_out=tmp_path / "state", stop_at_tick=stop, **RES_KW)
        files = a.resume["state_files"]
        b = run_day(resume_from=tmp_path / "state" / files[-1]["file"], **RES_KW)
    assert _hashes(b, stop) == _hashes(straight, stop) and _hashes(straight, stop)
    assert a.llm_calls + b.llm_calls == straight.llm_calls
    assert b.final_hash == straight.final_hash


@pytest.fixture
def _guard_on():
    prev = WP.enabled()
    WP.set_enabled(True)
    yield
    WP.set_enabled(prev)


def test_guards_hold_on_the_distance_arm(_guard_on):
    with arm("distance"):
        base = run_day(**SYN).final_hash
        WP.set_enabled(False)
        off = run_day(**SYN).final_hash
        WP.set_enabled(True)
        CD.STRICT_SCRATCH = True
        try:
            strict = run_day(**SYN).final_hash
        finally:
            CD.STRICT_SCRATCH = False
        pr = PR.Probe(check=CD.declared_check(SPECS), ticks=frozenset(range(0, 720, 7)),
                      families=("soa", "ext", "stats", "buffers", "scratch"))
        PR.ACTIVE = pr
        try:
            run_day(**SYN)
        finally:
            PR.ACTIVE = None
    assert base == off == strict
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]


# ================================================================= CLI
ARGS = ["--agents", "40", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "180"]


def _cli(tmp_path, name: str, env: dict, extra: list[str]) -> dict:
    out = tmp_path / f"{name}.json"
    e = dict(os.environ, PYTHONIOENCODING="utf-8", **env)
    code = "import sys; from shibuya import cli; sys.exit(cli.main(sys.argv[1:]))"
    r = subprocess.run([sys.executable, "-c", code, *ARGS, "--checkpoints-out", str(out), *extra],
                       capture_output=True, text=True, encoding="utf-8", env=e, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(Path(out).read_text(encoding="utf-8"))["manifest"]["proximity"]


@pytest.mark.parametrize("env_arm,cli_arm,want", [
    ("cell", "distance", "distance"), ("distance", "cell", "cell"), ("distance", None, "distance")])
def test_cli_proximity_beats_the_environment(tmp_path, env_arm, cli_arm, want):
    extra = [] if cli_arm is None else ["--proximity", cli_arm]
    m = _cli(tmp_path, f"{env_arm}_{cli_arm}", {"SHIBUYA_PROXIMITY": env_arm}, extra)
    assert m["mode"] == want and ((m["index_builds"] is None) == (want == "cell"))


def test_cli_proximity_d_arm(tmp_path):
    m = _cli(tmp_path, "d25", {"SHIBUYA_PROXIMITY": "cell", "SHIBUYA_PROXIMITY_D": "1.0"},
             ["--proximity", "distance", "--proximity-d", "2.5"])
    assert m["mode"] == "distance" and m["d_m"] == 2.5 and m["leave_m"] == 3.5


# ================================================================= 検収 M1: 腕の違う再開は止まる
@pytest.mark.parametrize("first,second", [
    (("cell", 2.0), ("distance", 2.0)), (("distance", 2.0), ("cell", 2.0)), (("distance", 2.0), ("distance", 2.5))])
def test_resume_with_another_proximity_arm_is_refused(tmp_path, first, second):
    kw = dict(n_agents=40, seed=1, n_cells=9, ticks=240, budget=40.0, vocab_version="v3", memory="on",
              relations="on")
    with arm(*first):
        a = run_day(state_out=tmp_path / "st", stop_at_tick=120, **kw)
    from shibuya.engine import resume as RS

    f = tmp_path / "st" / a.resume["state_files"][-1]["file"]
    head = RS.read_state(f).header
    assert ("proximity" in head) == (first[0] == "distance")
    if first[0] == "distance":
        assert head["proximity"] == {"mode": "distance", "d_m": first[1]}
    with arm(*second):
        with pytest.raises(ValueError, match="近接の腕"):
            run_day(resume_from=f, **kw)
    with arm(*first):
        run_day(resume_from=f, **kw)                            # 同じ腕は通る


# ================================================================= 検収 L2: 世界資産の再開(気づく抽選が十分に起きる構成)
WRES = dict(n_agents=1_000, seed=1, world_dir=WORLD, vocab_version="v3", memory="on", relations="on",
            rel_copresent="on", checkpoint_every=60)


@world_assets
def test_world_resume_equals_straight_and_the_marks_matter(tmp_path):
    from shibuya.engine import relations as RL

    with arm("distance"):
        straight = cli.run(**WRES)
        a = cli.run(state_out=tmp_path / "st", stop_at_tick=750, **WRES)
        f = tmp_path / "st" / a.resume["state_files"][-1]["file"]
        b = cli.run(resume_from=f, **WRES)
        assert _hashes(b, 750) == _hashes(straight, 750) and b.final_hash == straight.final_hash
        assert a.llm_calls + b.llm_calls == straight.llm_calls
        draws = straight.run_manifest_fields()["relations"]["counts"]["acq_notice_draws"]
        assert draws > 50                                       # 1,000 体 1 日で百数十本(既定の抽出)
        # 負の対照: 再開の最初の知人出現の呼び出しで気づいた印を消すと final が動く(印は結果に効き、再開で戻っている)
        orig = RL.RelationLayer.acquaintance_candidates
        done = {"n": 0}

        def wiped(self, agents, tick, *rest, **kw):
            if not done["n"] and self._acq_until is not None:
                done["n"] = int(np.count_nonzero(self._acq_until > int(tick)))
                self._acq_until[:] = -1
            return orig(self, agents, tick, *rest, **kw)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(RL.RelationLayer, "acquaintance_candidates", wiped)
            c = cli.run(resume_from=f, **WRES)
    assert done["n"] > 0 and c.final_hash != straight.final_hash


# ================================================================= 気づく抽選の流れの K19(ランの中)
def test_notice_streams_in_a_run_pass_k19():
    from shibuya.engine import rng_audit as RA

    with arm("distance"):
        with RA.StreamRecorder() as rec:
            r = run_day(**SYN)
    st = rec.analyze()
    n = r.run_manifest_fields()["relations"]["counts"].get("acq_notice_draws", 0)
    assert n > 0 and st[P.NOTICE_DOMAIN].streams == n and st[P.NOTICE_DOMAIN].max_blocks == 1
    assert st[P.NOTICE_DOMAIN].same_key_recreated == 0 and st[P.NOTICE_DOMAIN].actual_overlaps == 0
    assert RA.check_overlaps(st, recreated=RA.recreated_for()) == []
