# -*- coding: utf-8 -*-
"""``tools/fig`` の煙検査。

**合成データだけ**を使う(実 journal・実テープ・KDDI holdout は開かない)。見るのは
「描画関数が Figure を返し、PNG と SVG が出て、サイドカー JSON に絶対パスが混じらない」
の 3 点だけ。数値の正しさは各スクリプトの ``load_*`` が既存の集計物と突き合わせる。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_FIG = REPO_ROOT / "tools" / "fig"
if str(TOOLS_FIG) not in sys.path:  # tools/c7 と同じ作法(単体実行でも通るように)
    sys.path.insert(0, str(TOOLS_FIG))

pytest.importorskip("matplotlib", reason="matplotlib が無い環境では図は作らない")

HOURS = list(range(24))


@pytest.fixture(scope="module")
def style():
    import _style as _m

    return _m


def _png_ok(path: Path) -> None:
    assert path.exists(), f"PNG が無い: {path.name}"
    head = path.read_bytes()[:8]
    assert head == b"\x89PNG\r\n\x1a\n", f"PNG の署名が違う: {head!r}"
    assert path.stat().st_size > 5_000


# ---------------------------------------------------------------- _style


def test_rel_never_returns_absolute(style):
    """``rel`` はリポジトリ相対 / 外のものはファイル名だけ(絶対パスを出さない)。"""
    assert style.rel(REPO_ROOT / "docs" / "bench" / "figures" / "x.png") == \
        "docs/bench/figures/x.png"
    out = style.rel(Path.home() / "secret" / "tape.parquet")
    assert out == "tape.parquet"
    assert ":" not in out and not out.startswith("/")


def test_declutter_keeps_order_and_gap(style):
    ys = style.declutter([10.0, 11.0, 12.0, 50.0], min_gap=5.0)
    assert ys == sorted(ys)
    assert all(b - a >= 5.0 - 1e-9 for a, b in zip(ys, ys[1:]))
    assert ys[0] == 10.0 and ys[-1] == 50.0


def test_write_sidecar_is_utf8_lf(style, tmp_path):
    p = style.write_sidecar(tmp_path, "toy", {"語": "値", "n": 1})
    assert p == "toy.json"  # リポジトリ外 → ファイル名だけ
    raw = (tmp_path / "toy.json").read_bytes()
    assert b"\r\n" not in raw
    assert json.loads(raw.decode("utf-8"))["語"] == "値"


# ---------------------------------------------------------------- 図 1


def _toy_presence() -> dict:
    ramp = [26_000 + 8_000 * min(h, 24 - h) for h in HOURS]
    return {
        "hours": HOURS,
        "series": {
            "toy-a": {"label": "toy-a", "kind": "run", "color": "#2a78d6", "lw": 2.0,
                      "ls": "-", "five_area": [float(v) for v in ramp]},
            "toy-b": {"label": "toy-b", "kind": "mock", "color": "#898781", "lw": 1.3,
                      "ls": (0, (5, 3)), "five_area": [float(v) * 0.8 for v in ramp]},
        },
        "anchors": {
            "pt_area_daytime_peak": {"value": 145_000.0, "tag": "anchor",
                                     "scope": "toy", "source": "toy"},
            "night_presence_estimate": {"low": 15_000.0, "high": 30_000.0,
                                        "tag": "estimate", "scope": "toy", "source": "toy"},
            "core9_daytime_population": {"value": 130_167.0, "tag": "anchor",
                                         "scope": "toy", "source": "toy"},
        },
        "wake_rate_anchor": {"values": [50.0 + h for h in HOURS], "unit": "%",
                             "tag": "anchor", "scope": "toy", "caveat": None,
                             "source": "toy"},
    }


def test_fig1_draws(style, tmp_path):
    import fig_presence_24h as f1

    fig = f1.draw(_toy_presence())
    paths = style.save(fig, tmp_path, f1.STEM)
    _png_ok(tmp_path / f"{f1.STEM}.png")
    assert (tmp_path / f"{f1.STEM}.svg").exists()
    assert paths["png"].endswith(".png")


def test_fig1_output_bytes_are_reproducible(style, tmp_path):
    """同じ入力を 2 回描いたら PNG も SVG も**同じバイト列**(作り直しの差分をゼロにする)。"""
    import fig_presence_24h as f1

    data = _toy_presence()
    out = []
    for name in ("a", "b"):
        d = tmp_path / name
        style.save(f1.draw(data), d, f1.STEM)
        out.append(((d / f"{f1.STEM}.png").read_bytes(),
                    (d / f"{f1.STEM}.svg").read_bytes()))
    assert out[0][0] == out[1][0], "PNG のバイト列が再実行で変わった"
    assert out[0][1] == out[1][1], "SVG のバイト列が再実行で変わった(svg.hashsalt を疑う)"


def test_fig1_draws_without_wake_panel(style, tmp_path):
    """a(h) が台帳に無いときは副パネルを落として描ける。"""
    import fig_presence_24h as f1

    data = _toy_presence()
    data["wake_rate_anchor"] = None
    fig = f1.draw(data)
    style.save(fig, tmp_path, "fig1_nowake")
    _png_ok(tmp_path / "fig1_nowake.png")


def test_fig1_yardstick_check_flags_mismatch():
    """突き合わせは**差が出たら ok=False** になる(黙って通さない)。"""
    import fig_presence_24h as f1

    series = {"toy": {"five_area": [float(h) for h in HOURS]}}
    doc = {"after": {"label": "toy",
                     "presence_by_hour": [{"hour": h, "five_area": float(h)}
                                          for h in f1.YARDSTICK_HOURS],
                     "area_hour_counts": [[float(h)] for h in HOURS]}}
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "ys.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        assert f1.check_against_yardstick(series, p)["ok"] is True
        doc["after"]["area_hour_counts"][5] = [999.0]
        p.write_text(json.dumps(doc), encoding="utf-8")
        bad = f1.check_against_yardstick(series, p)
        assert bad["ok"] is False and bad["runs"][0]["max_abs_diff_24h"] > 0


# ---------------------------------------------------------------- 図 2


def _toy_calls() -> dict:
    classes = [
        {"value": 0, "name": "CONVERSATION", "ja": "会話ターン", "en": "conversation",
         "color": "#2a78d6"},
        {"value": 1, "name": "PLAN_BOUNDARY", "ja": "計画境界", "en": "plan boundary",
         "color": "#eb6834"},
    ]
    live = [[100 + 10 * h, 200 + 5 * h] for h in HOURS]
    deferred = [h * 3 for h in HOURS]
    total = [sum(row) + d for row, d in zip(live, deferred)]
    return {
        "hours": HOURS,
        "classes": classes,
        "live_by_hour_class": live,
        "deferred_by_hour": deferred,
        "total_by_hour": total,
        "deferred_rate_by_hour": [d / t for d, t in zip(deferred, total)],
        "deferred_reasons": {"deferred_queue_full": sum(deferred)},
        "totals": {"rows": sum(total), "live": sum(sum(r) for r in live),
                   "deferred": sum(deferred), "deferred_rate": 0.01,
                   "n_agents": 1_000, "calls_per_agent_day": 7.0,
                   "n_agents_source": "toy"},
        "input": "toy/calls.parquet",
    }


def test_fig2_draws(style, tmp_path):
    import fig_calls_by_hour as f2

    fig = f2.draw(_toy_calls())
    style.save(fig, tmp_path, f2.STEM)
    _png_ok(tmp_path / f"{f2.STEM}.png")


def test_fig2_event_classes_match_src():
    """和名表が ``EventClass`` を**全部**覆っている(src が増えたら落ちる)。"""
    import fig_calls_by_hour as f2

    from shibuya.core.types import EventClass

    got = f2.event_classes()
    assert [c["value"] for c in got] == sorted(int(m) for m in EventClass)
    assert all(c["ja"] and c["en"] for c in got)


# ---------------------------------------------------------------- 図 3


def _toy_ab7() -> dict:
    vocab = {"移動": 120, "購入": 80, "待機": 10, "乗車": 7}
    open_ = {"移動": 160, "購入": 40, "待機": 17, "乗車": 1}
    return {
        "arms": [{"tag": "vocab", "ja": "vocab", "en": "vocab", "color": "#2a78d6"},
                 {"tag": "open", "ja": "open", "en": "open", "color": "#eb6834"}],
        "per_arm": {
            "vocab": {"resolved": vocab, "action_counts": vocab, "n_live": 217,
                      "entropy_resolved_bits": 1.2, "entropy_excl_undefined_bits": 1.2,
                      "surfaces": {"移動": 120}, "routes": {"移動": {"route": "direct",
                                                                 "to": "移動"}},
                      "ja": "vocab", "en": "vocab", "color": "#2a78d6"},
            "open": {"resolved": open_, "action_counts": open_, "n_live": 218,
                     "entropy_resolved_bits": 1.0, "entropy_excl_undefined_bits": 1.0,
                     "surfaces": {"行く": 150, "食べる": 40, "食事": 7, "待機": 10,
                                  "乗車": 1},
                     "routes": {"行く": {"route": "stage0", "to": "移動"},
                                "食べる": {"route": "stage0", "to": "購入"},
                                "食事": {"route": "undefined", "to": "待機"},
                                "待機": {"route": "direct", "to": "待機"},
                                "乗車": {"route": "direct", "to": "乗車"}},
                     "ja": "open", "en": "open", "color": "#eb6834"},
        },
        "vocab_size": 24,
        "words_shown": ["移動", "購入", "待機", "乗車"],
        "words_all_zero": ["会話"] * 20,
        "jsd_bits": {"action_counts": 0.05, "resolved": 0.04},
        "runner": {"path": "toy.json", "null_reference_bits": 0.0035,
                   "action_jsd": 0.05, "exceeds_null": True, "llm_calls": {},
                   "scale": None},
    }


def test_fig3_draws(style, tmp_path):
    import fig_ab7_actions as f3

    fig = f3.draw(_toy_ab7())
    style.save(fig, tmp_path, f3.STEM)
    _png_ok(tmp_path / f"{f3.STEM}.png")


def test_fig3_entropy_bits_is_pure():
    import fig_ab7_actions as f3

    assert f3.entropy_bits({}) == 0.0
    assert f3.entropy_bits({"a": 5}) == 0.0
    assert abs(f3.entropy_bits({"a": 1, "b": 1}) - 1.0) < 1e-12
    assert abs(f3.entropy_bits({"a": 1, "b": 1, "c": 1, "d": 1}) - 2.0) < 1e-12

# ---------------------------------------------------------------- 図 4(seed 1 vs seed 2)


def _toy_pair():
    import numpy as np
    rng = np.random.default_rng(4)
    base = np.abs(rng.normal(1000, 200, size=(24, 5))) + 50
    t1 = base.round()
    t2 = (base * (1 + rng.normal(0, 0.02, size=base.shape))).round()
    return t1, t2


def test_fig4_summarize_is_symmetric_and_bounded(style):
    import fig_seed_pair as f4
    t1, t2 = _toy_pair()
    d = f4.summarize("a", t1, "b", t2, {"a": "x", "b": "y"})
    assert len(d["cv_hour"]) == 24 and all(0 <= c < 1 for c in d["cv_hour"])
    assert d["per_area_share_jsd_mean"] >= 0
    e = f4.summarize("b", t2, "a", t1, {"b": "y", "a": "x"})
    assert e["cv_hour"] == pytest.approx(d["cv_hour"])
    same = f4.summarize("a", t1, "a2", t1.copy(), {"a": "x", "a2": "x"})
    assert max(same["cv_hour"]) == 0 and same["per_area_share_jsd_mean"] == 0


def test_fig4_draws(style, tmp_path):
    import fig_seed_pair as f4
    t1, t2 = _toy_pair()
    d = f4.summarize("seed 1", t1, "seed 2", t2, {"seed 1": "x", "seed 2": "y"})
    fig = f4.draw(d)
    paths = style.save(fig, tmp_path, f4.STEM)
    assert (tmp_path / f"{f4.STEM}.png").stat().st_size > 1000
    assert not Path(paths["png"]).is_absolute()


# ---------------------------------------------------------------- 図 5〜7・表(第235・合成データ)


def _toy_ab7c() -> dict:
    import fig_ab7c_vocab as f5
    per = {}
    for k, (tag, spec) in enumerate(((a["tag"], a) for a in f5.ARMS)):
        counts = {"移動": 1000 + 10 * k, "購入": 900 if spec["vocab"] == "v1" else 50,
                  "食事": 0 if spec["vocab"] == "v1" else 850, "休憩": 100 + 60 * k, "乗車": 60 - 15 * k}
        per[tag] = {"n_rows": 2200, "n_live": 2200, "deferred": 0, "action_counts": counts,
                    "hourly": {w: [(h * (k + 1)) % 7 for h in HOURS] for w in f5.HOURLY_WORDS},
                    "entropy_bits": 1.5 - 0.1 * k, "path": "toy", "ja": spec["ja"], "en": spec["en"],
                    "color": spec["color"], "vocab": spec["vocab"]}
    return {"arms": [dict(a) for a in f5.ARMS], "per_arm": per,
            "words_shown": ["移動", "購入", "食事", "休憩", "乗車"], "words_omitted": [],
            "jsd_bits": {"raw": 0.3, "meal_folded_into_buy": 0.01},
            "runner": {"per_arm": {"vocab_v2": {"meals": 700}}}, "runner_check": None,
            "inputs": {"tape_root": "toy", "arm": "toy"}}


def test_fig5_fold_meal_and_entropy_are_pure():
    import fig_ab7c_vocab as f5
    assert f5.fold_meal({"購入": 10, "食事": 5, "移動": 1}) == {"購入": 15, "移動": 1}
    assert f5.fold_meal({"移動": 1}) == {"移動": 1}
    assert f5.entropy_bits({"a": 1, "b": 1}) == pytest.approx(1.0)
    assert f5.entropy_bits({}) == 0.0


def test_fig5_draws(style, tmp_path):
    import fig_ab7c_vocab as f5
    fig = f5.draw(_toy_ab7c())
    paths = style.save(fig, tmp_path, f5.STEM)
    _png_ok(tmp_path / f"{f5.STEM}.png")
    assert not Path(paths["png"]).is_absolute()


def _toy_ab6b() -> dict:
    def run(group, seed, tag, ja, delta, talk, rest, gate):
        return {"group": group, "seed": seed, "code": "toy", "tag": tag, "ja": ja, "en": ja,
                "delta_buy_pp": delta, "jsd": 0.001, "path": "toy", "n_texts": 1000, "llm_calls": 1000,
                "buy_pct": 44.0 + delta, "rest_pct": rest, "move_pct": 40.0, "wait_pct": 3.0, "ride": 10,
                "talk": talk, "prompt_tokens_mean": 900.0, "signage_p_see": 1.0, "shown_rate": gate,
                "gate_draws": 1000 if gate is not None else 0, "conserved": True}
    runs = [run("legacy", 1, "signage_on", "看板あり", 0.0, 20, 4.0, None),
            run("legacy", 1, "signage_off", "看板なし", -1.3, 22, 5.0, None),
            run("current", 1, "p_see_1_00", "現行(p_see 1.0)", 0.0, 25, 4.4, None),
            run("current", 1, "ad_zero", "看板なし", 0.5, 108, 5.7, None),
            run("current", 1, "p_see_0_30", "p_see 0.30", 0.48, 69, 5.4, 0.30),
            run("current", 1, "p_see_0_14", "p_see 0.14", 0.61, 47, 5.5, 0.14)]
    rows = [r for r in runs if r["delta_buy_pp"] != 0.0]
    return {"rows": rows, "runs": runs, "ad1_line_pp": 1.0, "null_seed_pp": {"legacy": 0.17, "current": None},
            "current_seeds_found": [1]}


def test_fig6_share_pct_is_pure():
    import fig_ab6b_signage as f6
    assert f6.share_pct({"n_texts": 200, "action_counts": {"購入": 50}}, "購入") == pytest.approx(25.0)
    assert f6.share_pct({"n_texts": 0, "action_counts": {"購入": 50}}, "購入") == 0.0
    s = f6.summarize_run({"n_texts": 100, "llm_calls": 100, "action_counts": {"購入": 40, "会話": 3},
                          "signage_gate": {"draws": 10, "shown": 3, "shown_rate": 0.3}})
    assert s["buy_pct"] == pytest.approx(40.0) and s["talk"] == 3 and s["shown_rate"] == 0.3


def test_fig6_draws(style, tmp_path):
    import fig_ab6b_signage as f6
    fig = f6.draw(_toy_ab6b())
    paths = style.save(fig, tmp_path, f6.STEM)
    _png_ok(tmp_path / f"{f6.STEM}.png")
    assert not Path(paths["png"]).is_absolute()


def _toy_d91_rows() -> dict:
    rows = {}
    for k, tag in enumerate(("vocab_v1", "vocab_v2")):
        lst = []
        for agent in range(40):
            for j in range(6):
                hour = 6 + (agent + j) % 5
                action = "乗車" if (agent + j + k) % (5 + 3 * k) == 0 else ("食事" if k else "購入")
                if j == 5:
                    action = "休憩" if (agent % 4 == 0 and k) else "移動"
                lst.append({"agent": agent, "tick": hour * 60 + j, "hour": hour,
                            "kind": "通勤者" if agent % 2 == 0 else "居住者", "station": agent % 3 == 0,
                            "wc": j % 4, "action": action})
        lst.sort(key=lambda x: (x["agent"], x["tick"]))
        prev = {}
        for x in lst:
            x["prev"] = prev.get(x["agent"], "(初回)")
            prev[x["agent"]] = x["action"]
        rows[tag] = lst
    return rows


def test_fig7_summarize_is_consistent():
    import fig_d91_ride_chain as f7
    rows = _toy_d91_rows()
    d = f7.summarize(rows)
    allc = next(c for c in d["conditions"] if c["key"] == "all")
    for tag in rows:
        mor = [r for r in rows[tag] if 6 <= r["hour"] <= 10]
        assert allc[tag]["n"] == len(mor)
        assert allc[tag]["ride"] == sum(1 for r in mor if r["action"] == "乗車")
    for ch in d["chains"]:
        assert sum(ch["counts"].values()) == ch["n"]
        if ch["n"]:
            assert sum(ch["share_pct"].values()) == pytest.approx(100.0, abs=0.05)
    assert d["overlap"]["common"] <= min(d["overlap"]["vocab_v1"], d["overlap"]["vocab_v2"])


def test_fig7_draws(style, tmp_path):
    import fig_d91_ride_chain as f7
    d = f7.summarize(_toy_d91_rows())
    d["arms"] = [dict(a) for a in f7.ARMS]
    d["n_live"] = {"vocab_v1": 240, "vocab_v2": 240}
    d["inputs"] = {"tape_root": "toy", "arm": "toy", "morning_hours": [6, 10]}
    fig = f7.draw(d)
    paths = style.save(fig, tmp_path, f7.STEM)
    _png_ok(tmp_path / f"{f7.STEM}.png")
    assert not Path(paths["png"]).is_absolute()


def test_tables_build_markdown_and_render(style, tmp_path):
    import fig_d91_ride_chain as f7
    import tbl_ablation as tb
    fig5 = _toy_ab7c()
    fig5 = {"arms": {t: {"label": p["ja"], "action_counts": p["action_counts"], "n_live": p["n_live"],
                         "entropy_bits": p["entropy_bits"]} for t, p in fig5["per_arm"].items()},
            "runner": fig5["runner"], "jsd_bits": fig5["jsd_bits"]}
    fig6 = _toy_ab6b()
    d7 = f7.summarize(_toy_d91_rows())
    d7["arms"] = [dict(a) for a in f7.ARMS]
    d7["inputs"] = {"morning_hours": [6, 10]}
    specs = tb.build_tables(fig5, fig6, d7)
    assert [s["stem"] for s in specs] == ["tbl1_ab7c_vocab", "tbl2_ab6b_signage", "tbl3a_d91_ride_rate",
                                          "tbl3b_d91_next_action"]
    for s in specs:
        md = tb.to_markdown(s)
        assert md.count("|") >= 3 * (len(s["rows"]) + 2)
        assert all(len(r) == len(s["columns"]) for r in s["rows"])
        fig = tb.render_table(s)
        paths = style.save(fig, tmp_path, s["stem"])
        _png_ok(tmp_path / f"{s['stem']}.png")
        assert not Path(paths["png"]).is_absolute()


# ---------------------------------------------------------------- 図 8 / 図 9(第248)


def _toy_ab8() -> dict:
    rows = []
    for tag, ja, scale, calls, buy, rev, board, sess, share in (
        ("l4_x0.5", "×0.5", 0.5, 20000, 3900, 3_150_000, 465, 0, 50.3),
        ("l4_x1", "×1(現行)", 1.0, 37000, 6600, 5_490_000, 648, 3, 43.8),
        ("l4_x2", "×2", 2.0, 61000, 9200, 7_770_000, 530, 18, 37.9),
        ("l4_unlimited", "無制限", 0.0, 77000, 9600, 8_160_000, 407, 31, 36.4),
    ):
        rows.append({"seed": 1, "tag": tag, "ja": ja, "en": ja, "scale": scale, "path": "toy", "n_agents": 5000,
                     "llm_calls": calls, "calls_per_agent_day": calls / 5000, "budget_per_tick": 1.0,
                     "l4_scale": scale, "purchases": buy, "purchases_per_agent_day": buy / 5000,
                     "purchases_per_1k_calls": 1000 * buy / calls, "revenue_yen": rev,
                     "revenue_yen_per_agent": rev / 5000, "boarded": board, "boarded_per_agent_day": board / 5000,
                     "conversation_sessions": sess, "buy_share_pct": share, "deferred": 0, "conserved": True,
                     "final_hash": "toy"})
    return {"rows": rows, "seed": 1, "seeds_found": [1], "all_rows": rows}


def test_fig8_summarize_is_pure_division():
    import fig_ab8_budget as f8
    s = f8.summarize_run({"llm_calls": 1000, "n_texts": 900, "action_counts": {"購入": 450},
                          "realized": {"purchases": 200, "revenue_end": 50000, "n_boarded": 25},
                          "conversation_sessions": 4, "diagnostics_day": {"deferred": 7}}, n_agents=100)
    assert s["calls_per_agent_day"] == pytest.approx(10.0)
    assert s["purchases_per_agent_day"] == pytest.approx(2.0)
    assert s["purchases_per_1k_calls"] == pytest.approx(200.0)
    assert s["revenue_yen_per_agent"] == pytest.approx(500.0)
    assert s["boarded_per_agent_day"] == pytest.approx(0.25)
    assert s["buy_share_pct"] == pytest.approx(50.0) and s["deferred"] == 7
    z = f8.summarize_run({"llm_calls": 0, "n_texts": 0}, n_agents=10)
    assert z["purchases_per_1k_calls"] is None and z["buy_share_pct"] is None


def test_fig8_draws(style, tmp_path):
    import fig_ab8_budget as f8
    fig = f8.draw(_toy_ab8())
    paths = style.save(fig, tmp_path, f8.STEM)
    _png_ok(tmp_path / f"{f8.STEM}.png")
    assert not Path(paths["png"]).is_absolute()


def _toy_ab6c() -> dict:
    def run(group, seed, tag, ja, delta, talk, rest):
        return {"group": group, "seed": seed, "tag": tag, "ja": ja, "en": ja, "delta_buy_pp": delta,
                "delta_rest_pp": rest - 4.4, "jsd": 0.001, "path": "toy", "boarded": 400, "purchases": 9000,
                "revenue_yen": 8_000_000, "sessions": 10, "n_texts": 1000, "llm_calls": 1000,
                "buy_pct": 44.0 + delta, "rest_pct": rest, "move_pct": 40.0, "wait_pct": 3.0, "ride": 10,
                "talk": talk, "prompt_tokens_mean": 900.0, "signage_p_see": 1.0, "shown_rate": None,
                "gate_draws": 0, "conserved": True}
    runs = []
    for group, base_talk in (("capped", 25), ("uncapped", 190)):
        runs += [run(group, 1, "p_see_1_00", "現行(p_see 1.0)", 0.0, base_talk, 4.4),
                 run(group, 1, "ad_zero", "看板なし", 0.5 if group == "capped" else -0.1, base_talk * 3, 6.0),
                 run(group, 1, "p_see_0_30", "p_see 0.30", 0.48, base_talk * 2, 5.5),
                 run(group, 1, "p_see_0_14", "p_see 0.14", 0.61, base_talk * 2, 5.6)]
    rows = [r for r in runs if r["tag"] != "p_see_1_00"]
    return {"rows": rows, "runs": runs, "ad1_line_pp": 1.0, "null_seed_pp": {"capped": 0.15, "uncapped": None},
            "capped_seeds_found": [1], "uncapped_seeds_found": [1]}


def test_fig9_draws(style, tmp_path):
    import fig_ab6c_uncapped as f9
    fig = f9.draw(_toy_ab6c())
    paths = style.save(fig, tmp_path, f9.STEM)
    _png_ok(tmp_path / f"{f9.STEM}.png")
    assert not Path(paths["png"]).is_absolute()


def test_fig9_reuses_fig6_arm_definitions():
    import fig_ab6b_signage as f6
    import fig_ab6c_uncapped as f9
    assert f9.CURRENT_ARMS is f6.CURRENT_ARMS and f9.AD1_LINE_PP == f6.AD1_LINE_PP
