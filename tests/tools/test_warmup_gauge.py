# -*- coding: utf-8 -*-
"""tools/instruments/warmup_gauge.py(第 3 期 3-3b・CP5-6 慣らしの自動判定の器)の試験(合成の系列だけ=データ不要)。

- MSER の式(手で計算した値)・候補は d ≤ n − 5。
- 既知の慣らしの日数を植えた系列(5 本の平均)で d* が当たる(決まった種で一致・300 種で下回らない・6 割以上で一致)。
- 後半の無効: d* > n/2 は 10% 延ばして当て直す(延ばした先で有効)・3 回無効は未収束・延ばす先のデータが無ければ要延長。
- 累積の負の対照: 偏りの無い系列の累積の平均は打ち切り点が後半に寄る(=使わない規則の理由)・指標の kind=cumulative は拒む。
- 差の系列 vs 原系列の腕: 週の周期と天気(共通)を持つ系列で、差の系列は植えた日数に当たり、原系列の腕は当たらない。
- 在庫は流量に直す・月の周期は推移の指標・置き場の指標は null・束ね W=有効な指標の慣らしの日数の最大・規則はエンジンの側の 1 か所。
- 問い 2 の 3 区間・CLI(JSON の入出力)・封印と検証側の道筋は開く前に落ちる。
- 〔検収 M1〕md23 の形の累計(``probe.conv.opened``)は累計の印(``kind: counter``)で日ごとの差に直る・印の無い累計は拒む・
  守りを外した写し(印の無い累計を流量として当てる)は植えた日数に当たらない(負の対照)。
- 〔検収 L3〕在庫の指標の慣らしの日数は系列の頭の日から数える(6 日ふえる在庫=7 日目から定常 → d* 6・慣らしの日数 7・W 7)。
- 〔検収 M2〕読む守りは大文字の形とつなぎ(junction・名に語を含まない)の形も落とす(``read_guard.deny_hit``)。
- 〔検収 L8〕指標の表は読み取り専用。
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
_PATH = ROOT / "tools" / "instruments" / "warmup_gauge.py"


@pytest.fixture(scope="module")
def G():
    name = "warmup_gauge"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _PATH)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def _planted(seed: int, k: int, *, n: int = 40, bias: float = 3.0, sd: float = 0.5, runs: int = 5) -> list[float]:
    rng = np.random.default_rng(seed)
    rows = [[(bias if t < k else 0.0) + rng.normal(0.0, sd) for t in range(n)] for _ in range(runs)]
    return list(np.mean(rows, axis=0))


# ================================================================= 式
def test_mser_formula_by_hand(G):
    y = [4.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    curve = G.mser_curve(y)
    tail = y[2:]
    m = sum(tail) / len(tail)
    assert curve[2] == pytest.approx(sum((v - m) ** 2 for v in tail) / len(tail) ** 2)
    pt = G.mser_point(y)
    assert pt["candidates"] == len(y) - 5 + 1 and pt["d_star"] == 1  # 4.0 を落とすのが最小
    assert G.mser_point([1.0] * 4)["d_star"] is None  # 候補が無い(n − 5 < 0)
    assert G.mser_rule([1.0] * 4)["status"] == G.TOO_SHORT


# ================================================================= 既知の慣らし
def test_planted_warmup_is_found(G):
    r = G.mser_rule(_planted(1, 7))
    assert r["status"] == G.VALID and r["d_star"] == 7
    exact = exact1 = 0
    for s in range(300):
        d = G.mser_point(_planted(s, 7))["d_star"]
        assert d >= 7  # 植えた日数を下回らない
        exact += d == 7
        exact1 += G.mser_point(_planted(s, 7, runs=1))["d_star"] == 7
    # MSER は長めに出ることがある(Hoad ら 2008)。5 本の平均は 1 本より当たる(複数本を平均してから当てる作法)
    assert exact / 300 >= 0.6 and exact > exact1


# ================================================================= 後半の無効
def test_latter_half_is_invalid_and_extended(G):
    rng = np.random.default_rng(1)
    y = [(3.0 if t < 12 else 0.0) + rng.normal(0.0, 0.05) for t in range(40)]
    r = G.mser_rule(y, n0=20)
    # n=20 で d*=12 > 10 → 22 で d*=16 > 11(〔検収 L4〕前の注の「22 で 12」は誤り)→ 25 で 12 ≤ 12.5 有効
    assert [a["n"] for a in r["attempts"]] == [20, 22, 25] and r["status"] == G.VALID and r["d_star"] == 12
    assert [a["d_star"] for a in r["attempts"]] == [12, 16, 12]
    assert [a["valid"] for a in r["attempts"]] == [False, False, True]
    trend = [10.0 - 0.3 * t + rng.normal(0.0, 0.01) for t in range(40)]
    u = G.mser_rule(trend, n0=20)
    assert u["status"] == G.UNCONVERGED and len(u["attempts"]) == 3  # 3 回無効=未収束
    m = G.mser_rule(trend[:21], n0=20)
    assert m["status"] == G.NEEDS_MORE and m["need_n"] == 22  # 延ばす先のデータが無い=ランを延ばす


# ================================================================= 累積の負の対照
def test_cumulative_series_is_the_negative_control(G):
    late_cum = late_raw = 0
    for s in range(50):
        x = np.random.default_rng(s).normal(0.0, 1.0, 60)
        cum = list(np.cumsum(x) / np.arange(1, 61))
        late_cum += G.mser_point(cum)["d_star"] > 30
        late_raw += G.mser_point(list(x))["d_star"] > 30
    assert late_cum >= 40 and late_raw <= 10  # 累積は打ち切り点が後半に寄る(Hoad & Robinson 2011)
    runs = [{"daily": [{"day": i, "x": float(i)} for i in range(20)]}]
    with pytest.raises(ValueError, match="累積"):
        G.question1([(runs[0], runs[0], 0)], metrics=[{"id": "x", "speed": "fast", "kind": "cumulative",
                                                       "path": "daily.x"}])


# ================================================================= 差の系列 vs 原系列
def _q1_pairs(seed: int, *, n: int = 35, k: int = 7, lead: int = 28, runs: int = 5):
    rng = np.random.default_rng(seed)
    total = n + lead
    env = [8.0 * math.sin(2 * math.pi * t / 7) + (6.0 if t % 7 in (5, 6) else 0.0) + rng.normal(0.0, 2.0)
           for t in range(total)]  # 暦と天気=日付ごとに A と B に同じに入る
    pairs = []
    for _ in range(runs):
        a = {"daily": [{"day": i, "x": 100.0 + env[lead + i] + (3.0 if i < k else 0.0) + rng.normal(0.0, 0.5)}
                       for i in range(n)]}
        b = {"daily": [{"day": i, "x": 100.0 + env[i] + (3.0 if i < k else 0.0) + rng.normal(0.0, 0.5)}
                       for i in range(total)]}
        pairs.append((a, b, lead))
    return pairs


X = ({"id": "x", "speed": "fast", "kind": "flow", "path": "daily.x"},)


def test_difference_series_finds_what_the_raw_arm_misses(G):
    out = G.question1(_q1_pairs(0), metrics=X)
    r = out["metrics"][0]
    assert r["status"] == G.VALID and r["d_star"] == 7 and r["first_day"] == 0
    assert r["arm_raw"]["d_star"] != 7  # 原系列は週の周期と天気に紛れる
    hits_diff = hits_raw = 0
    for s in range(40):
        rr = G.question1(_q1_pairs(s), metrics=X)["metrics"][0]
        hits_diff += rr["d_star"] == 7
        hits_raw += rr["arm_raw"]["d_star"] == 7
    assert hits_diff >= 24 and hits_raw <= 4
    assert out["pairs"] == 5 and out["pairs_enough"] and out["lead_days"] == [28]
    assert out["bundle"]["W"] == 7 and out["bundle"]["total_min_days"] == 14


# ================================================================= 指標の表・束ね・規則
def test_metric_table_stock_transition_placeholder_and_bundle(G):
    def run(days, shift):
        return {"daily": [{"day": i, "x": 5.0 + (2.0 if i < shift else 0.0) + 0.01 * (i % 2)} for i in range(days)],
                "probe": [{"day": i, "stock": 100.0 + 3.0 * min(i, shift) + 0.01 * (i % 3),
                           "money": 1000.0 + 50.0 * (i % 25)} for i in range(days)]}

    metrics = [
        {"id": "x", "speed": "fast", "kind": "flow", "path": "daily.x"},
        {"id": "stock", "speed": "slow", "kind": "stock", "path": "probe.stock"},
        {"id": "money", "speed": "transition", "kind": "stock", "path": "probe.money"},
        {"id": "groups", "speed": "slow", "kind": "stock", "path": None, "note": "置き場"},
    ]
    a, b = run(30, 4), run(58, 4)
    out = G.question1([(a, b, 28)], metrics=metrics)
    by = {r["id"]: r for r in out["metrics"]}
    assert by["x"]["d_star"] == 4 and by["groups"]["status"] == G.PLACEHOLDER and by["groups"]["d_star"] is None
    # 在庫は流量(日ごとの差)に直す=最初の日が落ちる・増え続ける在庫でも流量は 0 に落ち着く
    assert by["stock"]["first_day"] == 1 and by["stock"]["status"] == G.VALID and by["stock"]["head_day"] == 0
    # 〔検収 L3〕慣らしの日数は系列の頭の日から数える(在庫は d* + 1)・流量は d* のまま
    assert by["stock"]["warmup_days"] == by["stock"]["d_star"] + 1 == 5 and by["x"]["warmup_days"] == 4
    assert [t["id"] for t in out["transition"]] == ["money"]  # 月の周期は推移の指標(判定しない)
    w = out["bundle"]
    assert w["W"] == max(r["warmup_days"] for r in out["metrics"] if r["status"] == G.VALID) == 5
    assert w["unit"] == "days_from_series_head"
    assert not out["pairs_enough"] and out["pairs_min"] == 5
    from shibuya.engine.experiment import warmup as WU

    assert out["rule_sha256"] == WU.rule_sha256() and out["rule"] == WU.rule_record()["rule"]
    assert {m["id"] for m in G.METRICS} >= {"acquaintances_new", "acquaintances_forgotten", "promises_new", "wages"}
    assert all(m["path"] is None for m in G.METRICS if m["id"] in ("acquaintances_new", "acquaintances_forgotten"))
    assert G.to_flow({0: 1.0, 1: 4.0, 2: 4.0, 4: 9.0}) == {1: 3.0, 2: 0.0}


def test_question2_intervals(G):
    rng = np.random.default_rng(3)

    def run(effect):
        return {"daily": [{"day": i, "x": 10.0 + (effect * (4.0 if 10 <= i < 15 else 1.0) if i >= 10 else 0.0)
                           + rng.normal(0.0, 0.05)} for i in range(40)]}

    pairs = [(run(1.0), run(0.0)) for _ in range(6)]
    out = G.question2(pairs, exec_day=10, notice_day=8, metrics=X)
    r = out["metrics"][0]
    assert r["first_day"] == 10 and r["d_star"] == 5 and r["status"] == G.VALID
    iv = out["intervals"]
    assert iv["prepare"] == [8, 10] and iv["switch"] == [10, 15] and iv["new_normal"] == [15, None]
    assert out["pairs_enough"] and out["pairs_min"] == 6


def test_cli_and_read_guard(G, tmp_path):
    pairs = _q1_pairs(0)
    spec = {"pairs": []}
    for j, (a, b, lead) in enumerate(pairs):
        (tmp_path / f"a{j}.json").write_text(json.dumps(a), encoding="utf-8")
        (tmp_path / f"b{j}.json").write_text(json.dumps(b), encoding="utf-8")
        spec["pairs"].append({"a": f"a{j}.json", "b": f"b{j}.json", "lead_days": lead})
    (tmp_path / "q1.json").write_text(json.dumps(spec), encoding="utf-8")
    (tmp_path / "metrics.json").write_text(json.dumps(list(X)), encoding="utf-8")
    out = tmp_path / "out.json"
    assert G.main(["q1", "--input", str(tmp_path / "q1.json"), "--out", str(out), "--metrics",
                   str(tmp_path / "metrics.json")]) == 0
    text = out.read_text(encoding="utf-8")
    doc = json.loads(text)
    assert doc["schema"] == G.SCHEMA and doc["question"] == "q1" and doc["bundle"]["W"] == 7
    assert str(tmp_path) not in text and ":\\" not in text
    # 既定の指標の表(md23 の記録の道筋)で合成の記録を読むと、無い列はデータ無し(落ちない)
    dflt = G.question1(pairs)
    assert {r["status"] for r in dflt["metrics"]} <= {G.NO_DATA, G.PLACEHOLDER} and dflt["bundle"]["W"] is None
    with pytest.raises(PermissionError, match="封印"):
        G.check_path("data/realworld_live/odpt_rt/x.json")
    with pytest.raises(PermissionError):
        G.check_path("docs/bench/anchors/presence_validation_anchors_v0.json")


# ================================================================= 〔検収 M1〕累計の印
CNT = ({"id": "conversations", "speed": "fast", "kind": "counter", "path": "probe.conv.opened"},)


def _md23_pairs(seed: int, *, n: int = 40, k: int = 7, lead: int = 28, runs: int = 5, bias: float = 6.0,
                per_day: float = 20.0, sd: float = 1.0):
    """md23 の道具の probe の形(``conv.opened``=ランの頭からの累計)。1 日の数=per_day+慣らしの k 日だけ bias。"""
    rng = np.random.default_rng(seed)
    pairs = []
    for _ in range(runs):
        ca = [per_day + (bias if t < k else 0.0) + rng.normal(0.0, sd) for t in range(n)]
        cb = [per_day + (bias if t < k else 0.0) + rng.normal(0.0, sd) for t in range(n + lead)]
        a = {"probe": [{"day": i, "conv": {"opened": float(np.sum(ca[: i + 1]))}} for i in range(n)]}
        b = {"probe": [{"day": i, "conv": {"opened": float(np.sum(cb[: i + 1]))}} for i in range(n + lead)]}
        pairs.append((a, b, lead))
    return pairs


def _renamed(pairs):
    """負の対照: 累計の道筋の名を変えて守りを外した写し(印の無い累計を流量として当てる)。"""
    def one(run):
        return {"probe": [{"day": r["day"], "cum": r["conv"]["opened"]} for r in run["probe"]]}

    return [(one(a), one(b), k) for a, b, k in pairs]


def test_counter_paths_are_differenced_and_unmarked_ones_are_refused(G):
    conv = next(m for m in G.METRICS if m["id"] == "conversations")
    assert conv["kind"] == "counter" and conv["path"] in G.CUMULATIVE_PATHS
    # 累計 → その日の数(最初の記録の日は落ちる=累計は再開で引き継ぐので記録の頭を 0 とみなさない)
    counts = [3.0, 5.0, 4.0, 6.0]
    run = {"probe": [{"day": i, "conv": {"opened": sum(counts[: i + 1])}} for i in range(4)]}
    assert G._prepared(G.day_series(run, "probe.conv.opened"), CNT[0]) == {1: 5.0, 2: 4.0, 3: 6.0}
    # 印の無い累計の道筋は拒む(流量・在庫と宣言しても)
    for kind in ("flow", "stock"):
        with pytest.raises(ValueError, match="累計"):
            G.question1([(run, run, 0)], metrics=[{"id": "c", "speed": "fast", "kind": kind,
                                                   "path": "probe.conv.opened"}])
    # md23 の形(5 対・先行 28 日)に植えた慣らし 7 日: 日ごとの差に直すと当たる(最初の日が落ちる=d* 6・慣らしの日数 7)
    r = G.question1(_md23_pairs(0), metrics=CNT)["metrics"][0]
    assert (r["status"], r["first_day"], r["head_day"], r["d_star"], r["warmup_days"]) == (G.VALID, 1, 0, 6, 7)
    hit = hit_bypass = 0
    for s in range(40):
        rr = G.question1(_md23_pairs(s), metrics=CNT)["metrics"][0]
        assert rr["warmup_days"] >= 7  # 植えた日数を下回らない
        hit += rr["status"] == G.VALID and rr["warmup_days"] == 7
        rb = G.question1(_renamed(_md23_pairs(s)), metrics=({"id": "c", "speed": "fast", "kind": "flow",
                                                            "path": "probe.cum"},))["metrics"][0]
        hit_bypass += rb["status"] == G.VALID and rb["warmup_days"] == 7
    # 負の対照: 印の無い累計を流量として当てると、ほとんど要延長か外れ(検収の再現=20 種中 14 が要延長)
    assert hit >= 14 and hit_bypass <= 4, (hit, hit_bypass)


# ================================================================= 〔検収 L3〕在庫の慣らしの日数
def _stock_pairs(seed: int, *, n: int = 40, lead: int = 28, runs: int = 5):
    """6 日間ふえる在庫(1〜6 日目に 1 日 5 ずつ・7 日目から定常)。流量に雑音。"""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(runs):
        fa = [0.0] + [(5.0 if t <= 6 else 0.0) + rng.normal(0.0, 0.3) for t in range(1, n)]
        fb = [0.0] + [(5.0 if t <= 6 else 0.0) + rng.normal(0.0, 0.3) for t in range(1, n + lead)]
        a = {"probe": [{"day": i, "s": 100.0 + float(np.sum(fa[: i + 1]))} for i in range(n)]}
        b = {"probe": [{"day": i, "s": 100.0 + float(np.sum(fb[: i + 1]))} for i in range(n + lead)]}
        out.append((a, b, lead))
    return out


def test_stock_warmup_days_count_from_the_series_head(G):
    st = ({"id": "s", "speed": "slow", "kind": "stock", "path": "probe.s"},)
    o = G.question1(_stock_pairs(0), metrics=st)
    r = o["metrics"][0]
    # 流量に直すと最初の日が落ちる(first_day 1)・d* は系列の中の位置 6・慣らしの日数=1 + 6 − 0 = 7
    assert (r["status"], r["first_day"], r["head_day"], r["d_star"], r["warmup_days"]) == (G.VALID, 1, 0, 6, 7)
    assert o["bundle"]["W"] == 7 and o["bundle"]["total_min_days"] == 14  # 前の束ね(d* の最大)は 6=1 日短い
    # 問い 2 の頭の日は実行の日(在庫の流量の最初の日が実行の日なら d* のまま)
    q2 = G.question2([(a, b) for a, b, _k in _stock_pairs(0)[:1]], exec_day=3, metrics=st)
    assert q2["metrics"][0]["head_day"] == 3 and q2["metrics"][0]["first_day"] == 3


# ================================================================= 〔検収 M2〕読む守り(大文字・つなぎ)
def _junction(link: Path, target: Path) -> bool:
    """名に語を含まないつなぎ(Windows=junction・ほか=symlink)。作れなければ False。"""
    target.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "nt":
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
        else:
            os.symlink(target, link, target_is_directory=True)
    except (OSError, AttributeError, ImportError):
        return False
    return True


def _remove_link(link: Path) -> None:
    """つなぎだけを外す(実体は触らない)。"""
    if os.name == "nt":
        os.rmdir(link)
    else:
        os.unlink(link)


def test_read_guard_catches_upper_case_and_junction(G, tmp_path):
    for p in ("data/KDDI_LA/x.json", "docs/bench/anchors/Presence_Validation_Anchors_v0.json",
              "data/REALWORLD_LIVE/x.json", "DOCS/BENCH/C7/HOLDOUT/x.json"):
        with pytest.raises(PermissionError):
            G.check_path(p)
    G.check_path(tmp_path / "plain.json")  # 語の無い道筋は通る(正の対照)
    link = tmp_path / "plain_dir"
    if not _junction(link, tmp_path / "kddi_la_fake"):
        pytest.skip("つなぎを作れない")
    try:
        assert "kddi" not in str(link / "x.json").lower()  # 生の形には語が無い=実体の道筋で落ちる
        with pytest.raises(PermissionError, match="kddi"):
            G.check_path(link / "x.json")
    finally:
        _remove_link(link)


# ================================================================= 〔検収 L8〕指標の表は読み取り専用
def test_metric_table_is_read_only(G):
    assert isinstance(G.METRICS, tuple)
    with pytest.raises(TypeError):
        G.METRICS[0]["kind"] = "stock"  # type: ignore[index]
    acq = next(m for m in G.METRICS if m["id"] == "acquaintances")
    assert isinstance(acq["flows"], tuple)
    assert G.metrics_sha256() == G.metrics_sha256([dict(m) for m in G.METRICS])
