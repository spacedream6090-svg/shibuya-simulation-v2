"""〔11-01 段 2 の 3・4〕率の形の規則を外す切替口 ``engine.rate_rules`` の試験(規則ごとの正と負の対照)。

各規則について、既定(腕 off)では旧道の件数が 0・切替口(腕 legacy)では旧の件数が出ることを、過程を直に組んで確かめる。
ランの全体(manifest の節・状態の見出し・CLI の口)は小さな合成世界の run_day で確かめる。記録
``docs/bench/analysis/s2-rates-1101/README.md``。〔第347 止めた切替口の削除〕ランの切替口(``--rate-rules``・環境変数
``SHIBUYA_RATE_RULES``・``run_day(salient_rate_per_10k=…)``)は消した=旧道は過程の部品の口(引数 ``rate_rules``)だけ・ランの
旧道は試験の中だけの助け(``tests/engine/_legacy_world.py``)。記録 ``docs/bench/analysis/switch-removal-347/README.md``。
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from shibuya.world.laws import switch_rate as RR
from shibuya.engine import resolve as R
from shibuya.world.laws.civic import EVENT_WINDOW, LargeEventProcess
from shibuya.world.laws.goods_flow import (
    LITTER_G_PER_PERSON_TICK,
    WASTE_TO_BIN_MINUTE,
    StreetCleaningProcess,
    WasteCollectionProcess,
)
from shibuya.world.laws.logistics import LastMileProcess
from shibuya.world.laws.rail import RailProcess
from shibuya.world.laws.salient import COLLAPSE_PER_10K_PER_DAY, SalientProcess
from shibuya.engine.presence import PlanExecutor
from shibuya.engine.run import run_day

from .conftest import fake_timetable_assets, make_agents, make_world
from .test_goods_flow import _setup as goods_setup

ROOT = Path(__file__).resolve().parents[3]


# ================================================================= 切替口(〔第347〕消した)と部品の口
def test_the_run_arm_is_off_and_the_switch_is_removed():
    """〔第347 止めた切替口の削除〕前(``test_the_default_arm_is_off_and_names_are_checked``)は「既定 off・``resolve(None)`` は
    今の腕・腕の名の誤り(``set_arm("on")``)で止まる」。切替口を消した: 腕を選ぶ名(``arm``・``set_arm``・``_ARM``)が無い・
    ``resolve(None)`` は既定 off・消した環境変数と旗の名とタグは止める一覧にある(止まることは
    ``tests/engine/test_removed_switches_346.py``)。部品の口の名の検査・印・規則の表は残す。"""
    from shibuya.foundation.arms import removed as RSW

    for name in ("arm", "set_arm", "_ARM"):
        assert not hasattr(RR, name), name
        assert name not in RR.__all__, name
    assert RR.DEFAULT_MODE == RR.MODE_OFF and RR.MODES == ("off", "legacy")
    assert RR.resolve(None) == RR.DEFAULT_MODE and RR.is_legacy() is False and RR.is_legacy("legacy") is True
    assert RR.ENV_REMOVED == "SHIBUYA_RATE_RULES" and RR.ENV_REMOVED in RSW.REMOVED_ENV
    assert RSW.REMOVED_CLI_FLAGS["--rate-rules"] == RR.ENV_REMOVED
    assert RSW.tag_of(RR.ENV_REMOVED) == RSW.REMOVED_SWITCH_TAG_347 == "stable-v2-before-switch-removal-347"
    for bad in ("on", "bogus"):  # 部品の口の名の検査(前は set_arm("on") で見た名の誤り)
        with pytest.raises(ValueError):
            RR.resolve(bad)
    off = RR.removed_flags("off")
    leg = RR.removed_flags("legacy")
    assert set(off) == {f"rate_rule_{r}_removed" for r in RR.RULES} and len(RR.RULES) == 9
    assert all(v == 1 for v in off.values())
    # 旧道でも戻らないのは出勤率のくじ(消した)と Calvo(結線していない)だけ
    assert {k for k, v in leg.items() if v == 1} == {"rate_rule_attendance_removed", "rate_rule_calvo_removed"}
    assert set(RR.REMOVED_RULES) == set(RR.RULES)


def test_state_header_and_resume_check():
    """〔第347 止めた切替口の削除〕前は切替口の腕を off と legacy に置いて再開の検査を見た(legacy の腕なら見出しに無いファイル
    からも再開できた)。切替口を消した: 今の腕はいつも既定 off=見出し off は通る・見出しに無い(legacy=版上げの前のラン)と
    legacy は止まる・文に消した切替口と安定版のタグ。"""
    assert RR.header_fields("off") == {"mode": "off"} and RR.header_fields("legacy") is None
    RR.check_resume({"mode": "off"})
    with pytest.raises(ValueError, match="率の規則の腕が親と違う.*--rate-rules legacy.*消した.*"
                                         "stable-v2-before-switch-removal-347"):
        RR.check_resume(None)  # 見出しに無い=版上げの前(legacy)のラン
    with pytest.raises(ValueError, match="率の規則の腕が親と違う"):
        RR.check_resume({"mode": "legacy"})


# ================================================================= #3 E8 到着の分散
def _crowded_layer(rate_rules):
    from tests.engine.test_presence_executor import (
        ACT_SLEEP, ACT_WORK, PK_OUT, PK_WORK, fake_assets, make_weekly, make_world_agents,
    )

    n = 60
    rows = [(i, 0, 400, ACT_SLEEP, PK_OUT, -1) for i in range(n)]
    rows += [(i, 500, 900, ACT_WORK, PK_WORK, 3) for i in range(n)]
    wk = make_weekly(rows, n)
    pa = fake_assets(departures=(300, 340, 380, 420, 460, 500))
    w, a = make_world_agents(n)
    rail = RailProcess(w, a, pa, master_seed=1, day_index=0, plan_executor=True)
    rail.capacity100 = np.full(rail.dep_tick.size, 4.0)
    rail.cap_pct = np.full(rail.dep_tick.size, 100.0)
    return PlanExecutor(
        w, a, wk, day_index=0, home_cell=np.full(n, -1, dtype=np.int64), direction_node=np.zeros(n, dtype=np.int64),
        rail=rail, assets=pa, ticks=1_440,
        rate_rules=rate_rules,
    )


def test_off_everyone_takes_the_latest_train_that_is_in_time():
    layer = _crowded_layer("off")
    tr, e1 = layer.arrival_train, layer.arrival_train_e1
    assert np.array_equal(tr, e1) and layer.n_spread_moved == 0 and layer.n_spread_overflow == 0
    assert layer.counters()["spread_moved"] == 0.0
    # 席より多くても全員が E1 便(=最後の便)に乗る(散らさない)
    assert int(np.bincount(tr[tr >= 0]).max()) == 60


def test_legacy_spreads_the_arrivals():
    layer = _crowded_layer("legacy")
    assert layer.n_spread_moved > 0 and not np.array_equal(layer.arrival_train, layer.arrival_train_e1)


# ================================================================= #22 乗車の受け入れ確率
def _rail(rate_rules):
    world = make_world(9)
    agents, schedule = make_agents(world, 20)
    pa = fake_timetable_assets(platform_cell=0, departures=(100, 200, 300), lines=("山手線", "井の頭線"))
    rail = RailProcess(world, agents, pa, master_seed=1, day_index=0, schedule=schedule, rate_rules=rate_rules)
    rail.capacity100[0] = 100.0
    return rail


def test_off_keeps_only_the_two_hundred_percent_cap():
    rail = _rail("off")
    rail.occupancy[0] = 180  # 180%=旧道なら受け入れ 0.82
    assert rail.accept_quota(0, 10) == 10  # 上限までは全員乗る
    rail.occupancy[0] = 195
    assert rail.accept_quota(0, 10) == 5  # 200% の上限(物理)だけ
    assert rail.n_left_behind == 5 and rail.n_left_behind_by_rate == 0
    c = rail.counters()
    assert c["rate_rule_board_accept_removed"] == 1.0 and c["left_behind_by_rate"] == 0.0


def test_legacy_refuses_by_the_acceptance_rate():
    rail = _rail("legacy")
    rail.occupancy[0] = 180
    q = rail.accept_quota(0, 10)
    assert q == int(np.floor(rail.accept_rate(1.8) * 10)) < 10
    assert rail.n_left_behind_by_rate == 10 - q
    assert rail.counters()["rate_rule_board_accept_removed"] == 0.0


# ================================================================= #10 催しの 200 人注入
@pytest.mark.parametrize("mode", ["off", "legacy"])
def test_event_injection(mode):
    world = make_world(16)
    agents, _ = make_agents(world, 40)
    from shibuya.world.ledger.actual_log import ActualLog

    alog = ActualLog("actual_log", retention_days=7, ticks_per_day=1_440)
    ev = LargeEventProcess(world, agents, master_seed=2, visitor_delta=5, actual_log=alog, rate_rules=mode)
    R.place_at_external(agents, np.arange(8, dtype=np.int64), np.zeros(8, dtype=np.int64))
    lo, hi = EVENT_WINDOW
    ev.step(lo)
    ev.step(hi)
    assert ev.venue_cells.size == 3  # 会場の開催は残す
    assert len(alog) == 2 * ev.venue_cells.size  # 開催の記録(18:00 と 21:00)は両方の腕にある
    if mode == "off":
        assert ev.n_in == 0 and ev.n_out == 0 and int((agents.registry.transit_state == 2).sum()) == 8
        assert ev.counters()["rate_rule_event_injection_removed"] == 1.0
    else:
        assert ev.n_in == 5 and ev.n_out == 5
        assert ev.counters()["rate_rule_event_injection_removed"] == 0.0


# ================================================================= #99 売れ残りの廃棄率・#42 ポイ捨て
@pytest.mark.parametrize("mode", ["off", "legacy"])
def test_leftover_waste(mode):
    world, agents, bundle = goods_setup(n_agents=30, n_cells=16)
    waste = WasteCollectionProcess(world, agents, ledger=bundle, rate_rules=mode)
    waste.step(WASTE_TO_BIN_MINUTE)
    if mode == "off":
        assert int(bundle.goods.bins.sum()) == 0 and waste.n_bin_rows == 0
        assert waste.counters()["rate_rule_leftover_waste_removed"] == 1.0
    else:
        assert int(bundle.goods.bins.sum()) > 0 and waste.n_bin_rows > 0
    assert bundle.goods.sku_balanced()


@pytest.mark.parametrize("mode", ["off", "legacy"])
def test_litter(mode):
    world, agents, _ = goods_setup(n_agents=40, n_cells=9)
    clean = StreetCleaningProcess(world, agents, rate_rules=mode)
    for t in range(0, 60):
        clean.step(t)
    dens = float(np.asarray(world.cells.density, dtype=np.float64).sum())
    if mode == "off":
        assert clean.litter_g.sum() == 0.0 and clean.litter_generated_g == 0.0
        assert clean.counters()["rate_rule_litter_removed"] == 1.0
    else:
        assert clean.litter_generated_g == pytest.approx(60 * dens * LITTER_G_PER_PERSON_TICK) and dens > 0


# ================================================================= #105 宅配
@pytest.mark.parametrize("mode", ["off", "legacy"])
def test_parcels(mode):
    world = make_world(16)
    lm = LastMileProcess(world, household_per_cell=np.full(16, 5, dtype=np.int64), rate_rules=mode)
    for t in range(1_440):
        lm.step(t)
    if mode == "off":
        assert lm.parcels_today == 0 and not lm.active and int(lm.delivered.sum()) == 0
        assert lm.counters()["rate_rule_parcels_removed"] == 1.0
    else:
        assert lm.parcels_today > 0 and int(lm.delivered.sum()) > 0


# ================================================================= #83 倒れる率
def test_collapse_rate_is_zero_off_and_three_legacy():
    world = make_world(9)
    agents, _ = make_agents(world, 50)
    off = SalientProcess(world, agents, rate_rules="off")
    leg = SalientProcess(world, agents, rate_rules="legacy")
    knob_off = SalientProcess(world, agents, rate_rules="off", rate_per_10k_per_day=50.0)  # 〔検収 L3〕試験の口は off で無視
    knob_leg = SalientProcess(world, agents, rate_rules="legacy", rate_per_10k_per_day=50.0)  # 旧道でだけ効く
    assert off.rate == 0.0 and leg.rate == COLLAPSE_PER_10K_PER_DAY == 3.0
    assert knob_off.rate == 0.0 and knob_off.counters()["rate_rule_collapse_removed"] == 1.0 and knob_leg.rate == 50.0
    assert off._collapse_events(10) == [] and off.counters()["rate_rule_collapse_removed"] == 1.0
    assert leg.counters()["rate_rule_collapse_removed"] == 0.0


def test_collapse_off_over_a_day_has_no_events_but_legacy_does():
    world = make_world(9)
    agents, _ = make_agents(world, 50)
    off = SalientProcess(world, agents, rate_rules="off")
    hot = SalientProcess(world, agents, rate_rules="legacy", rate_per_10k_per_day=20_000.0)  # 旧道の式(率を大きく)
    for t in range(200):
        off._collapse_events(t)
        hot._collapse_events(t)
    assert off.n_collapse == 0 and hot.n_collapse > 0


# ================================================================= #101 価格の改定確率(Calvo)
_CALVO_NAMES = {"calvo_draw", "calvo_daily_probability", "apply_r", "deviation_cost", "book_deviation_cost",
                "propose_price", "PriceProposal", "clearing", "floor_price", "CALVO_MONTHLY", "DEVIATION_BETA"}


def _pricing_uses(root: Path) -> tuple[dict[str, set[str]], list[str], list[str]]:
    """``root``(``src/shibuya`` の形)の中で ``economy.pricing`` を import するモジュール → そこで別名から引く属性の名・
    ``from …pricing import`` の行・Calvo の名の属性の参照(完全修飾を含む)。"""
    importers: dict[str, set[str]] = {}
    attr_hits, from_hits = [], []
    for p in root.rglob("*.py"):
        rel = p.relative_to(root).as_posix()
        if rel == "economy/pricing.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        aliases: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.endswith("economy.pricing"):
                        aliases.add(a.asname or a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.endswith("pricing"):
                    from_hits += [f"{rel}:{node.lineno}:{a.name}" for a in node.names]
                    aliases.add("<from>")
                for a in node.names:
                    if a.name == "pricing" and (mod.endswith("economy") or (node.level and rel.startswith("economy/"))):
                        aliases.add(a.asname or "pricing")
            elif isinstance(node, ast.Attribute) and node.attr in _CALVO_NAMES:
                attr_hits.append(f"{rel}:{node.lineno}:{node.attr}")
        if aliases:
            importers[rel] = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                              and isinstance(n.value, ast.Name) and n.value.id in aliases}
    return importers, from_hits, attr_hits


def test_calvo_is_not_wired_into_the_engine():
    """``economy.pricing`` の Calvo の口は src のどこからも呼ばれていない(結線しない=価格は固定)。

    〔検収 L1〕別名の import と完全修飾の呼び出しも見る: ``pricing`` を import するモジュールは ``economy/goods.py`` だけ・
    そこで使う名は内生フロアの係数 ``K_*`` だけ・Calvo の名の属性の参照は 0 件。
    """
    importers, from_hits, attr_hits = _pricing_uses(ROOT / "src" / "shibuya")
    assert set(importers) == {"economy/goods.py"}, importers
    assert importers["economy/goods.py"] <= {"K_VOLUME", "K_AVERAGE", "K_PREMIUM", "K_BY_KIND"}
    assert from_hits == [] and attr_hits == []


def test_negative_calvo_wiring_is_caught_through_aliases(tmp_path):
    """負の対照: 別名の import・相対の import・完全修飾の呼び出し・from import を植えると捕まる。"""
    (tmp_path / "economy").mkdir()
    (tmp_path / "engine").mkdir()
    (tmp_path / "engine" / "a.py").write_text("import shibuya.economy.pricing as P\nP.calvo_draw(1)\n", encoding="utf-8")
    (tmp_path / "economy" / "b.py").write_text("from . import pricing as Q\nQ.K_AVERAGE\n", encoding="utf-8")
    (tmp_path / "engine" / "c.py").write_text("import shibuya\nshibuya.economy.pricing.propose_price()\n", encoding="utf-8")
    (tmp_path / "engine" / "d.py").write_text("from shibuya.economy.pricing import apply_r\n", encoding="utf-8")
    importers, from_hits, attr_hits = _pricing_uses(tmp_path)
    assert importers["engine/a.py"] == {"calvo_draw"} and importers["economy/b.py"] == {"K_AVERAGE"}
    assert from_hits == ["engine/d.py:1:apply_r"]
    assert {h.rsplit(":", 1)[1] for h in attr_hits} == {"calvo_draw", "propose_price"}


# ================================================================= ランの全体
@pytest.fixture(scope="module")
def day_runs():
    """〔検収 L2〕世界資産(台帳つき)の 200 体で 1 日(1,440 刻み)=05:00 の売れ残り・05〜08 時の納品・08〜21 時の宅配・
    18:00 と 21:00 の催しの窓を含む。腕 off と legacy を 1 本ずつ(合成の世界は鉄道が休み=域外の体が居ないので催しの注入が
    起きない=世界資産で回す)。

    〔第347 止めた切替口の削除〕legacy は切替口(``--rate-rules`` の腕)の代わりに、試験の中だけで実行器と計画実行層に部品の口
    (率の規則の旧道)を挿して回す(``tests/engine/_legacy_world.py``=同じランになることを手順 0 で確かめた)。"""
    from shibuya import cli
    from tests.engine._legacy_world import legacy_world_rules

    kw = dict(n_agents=200, seed=3, world_dir="data/world/v2", ticks=1_440, checkpoint_every=360)
    out = {"off": cli.run(**kw)}
    with pytest.MonkeyPatch.context() as mp:
        legacy_world_rules(mp, absent=False)
        out["legacy"] = cli.run(**kw)
    return out


@pytest.mark.requires_data("world_v2:w2_cells.parquet")
def test_run_manifest_counts_rise_in_legacy_and_are_zero_off(day_runs):
    """〔検収 L2〕同じ 1 日のランで、旧道は催し・売れ残り・ポイ捨て・宅配の件数が立ち、off は全部 0(倒れる率は off で 0)。"""
    m = day_runs["off"].run_manifest_fields()
    rr = m["rate_rules"]
    assert list(m)[-3:] == ["rate_rules", "absent_processes", "defect_fixes_1103"] and "attendance_rate" not in m  # 〔11-02r §1 #7〕末尾に absent_processes
    assert rr["schema"] == RR.SCHEMA and rr["mode"] == "off"
    assert all(v == 1 for v in rr["removed"].values())
    assert {k: v for k, v in rr["counts"].items() if v not in (0, None)} == {}
    leg = day_runs["legacy"].run_manifest_fields()["rate_rules"]
    # 〔第347〕旧道は実行器と計画実行層の部品の口で動く(過程の印が 0=旧道)。manifest の mode と removed の印は組み立ての腕
    # (既定 off)を書く=試験の中だけの助けの注。件数(counts)は実行器と計画実行層の計数から数える=旧道の件数
    leg_rn = day_runs["legacy"].runner
    assert leg_rn.rate_rules == "legacy" and leg_rn.last_mile.counters()["rate_rule_parcels_removed"] == 0.0
    assert leg["mode"] == "off"
    c = leg["counts"]
    assert c["event_injection_arrived"] > 0 and c["leftover_waste_bin_rows"] > 0
    assert c["parcels_delivered"] > 0 and c["litter_generated_g"] > 0 and c["collapse_rate_per_10k"] == 3
    # off でも会場は立ち、開催の記録の行はある(人は動かない)
    off_rn = day_runs["off"].runner
    assert off_rn.large_event.venue_cells.size == 3 and off_rn.large_event.n_in == 0
    assert "large_event" in off_rn.log.process_ids


def test_attendance_rate_is_gone_from_run_day_and_the_cli(capsys):
    with pytest.raises(TypeError):
        run_day(n_agents=10, seed=1, n_cells=9, ticks=2, attendance_rate=0.5)
    from shibuya import cli

    with pytest.raises(SystemExit):
        cli.main(["--attendance-rate", "0.5"])
    capsys.readouterr()
    # 〔第347 止めた切替口の削除〕前は ``--rate-rules on`` が名の誤りで止まるのを見た。旗は消した=値に依らず、表に出さない旗で
    # 受けて消した切替口の文で止まる
    for value in ("on", "legacy", "off"):
        with pytest.raises(SystemExit) as exc:
            cli.main(["--rate-rules", value])
        assert exc.value.code == 2
        assert "--rate-rules は消した切替口" in capsys.readouterr().err


def test_the_run_day_collapse_rate_port_is_removed():
    """〔第347 止めた切替口の削除・案 k1〕倒れる率の試験の口 ``run_day(salient_rate_per_10k=…)`` は率の規則の旧道でだけ効いた=
    一緒に消した。引数は設定の指紋と 1-0 の引数の数を変えないため残し、None 以外は刻みの前に止める(文に消した口・タグ・部品の
    口の名)。None(既定)のランは今のまま。"""
    import inspect

    assert inspect.signature(run_day).parameters["salient_rate_per_10k"].default is None
    with pytest.raises(ValueError, match="salient_rate_per_10k は消した試験の口.*stable-v2-before-switch-removal-347"
                                         ".*WorldProcessRunner.*SalientProcess"):
        run_day(n_agents=10, seed=1, n_cells=9, ticks=2, salient_rate_per_10k=3_000.0)
    res = run_day(n_agents=10, seed=1, n_cells=9, ticks=2, salient_rate_per_10k=None)
    assert res.runner.salient.rate_rules == RR.DEFAULT_MODE
