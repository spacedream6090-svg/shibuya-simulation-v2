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
