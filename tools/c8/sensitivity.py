# -*- coding: utf-8 -*-
"""sensitivity.py — expedient 登録簿の**感度試験の台帳**と、構築段階の対照の実行器。

正典
- 方法論「②cap が世界の法則化(**artefact**: 付随的仮定が結果を駆動)→ 全 cap に
  ``mechanism|expedient`` タグ。**expedient は感度試験 id 必須(振って結果非依存を示す)。
  示せなければ限界として明記**」・「Phase 4 …expedient タグ全 cap の artefact 試験」。
- CLAUDE.md §4「全 cap/近似に ``mechanism|expedient`` タグ。expedient は感度試験で
  『結果を駆動していない』証明必須」。
- 実装計画書 **§9.1 C8** 検収列「各 expedient の『結果を駆動していない』証明」。
- 世界データ構築仕様書 **§0-7**「expedient 登録: 段階ごとに expedient を列挙し感度試験
  (対照ラン)を紐付ける。**感度試験なしの expedient は出荷不可**」。台帳の分母は同書 §2 の
  ``### D-W\\d+`` 見出しに書かれた「感度: …」14 行(``c8lib.scan_build_spec_sensitivities``)。
- 世界過程の 21 過程は台帳行ごとに感度試験 id(``AB-*``)を持ち、``--ablate <AB-*>`` で切れる
  (実装計画書 §8・``c8lib.scan_engine_ablation_ids``)。

**構築段階の対照で言えること(片側の論法・自前=登録簿へ)**
    構築対照(入力側)の差が帰無参照(同分布 2 標本の JSD 95% 点)以内なら、入力が動かない
    のだから **その expedient はランの結果を駆動しえない**(``not_driving``)。超えたときは
    「駆動する**かもしれない**」までしか言えず、**ラン側の対照が要る**(``needs_run``)。
    構築段階だけで「駆動している」と結論はしない。

親が叩く例::

    python tools/c8/sensitivity.py --list
    python tools/c8/sensitivity.py --run all --out docs/bench/c8
    python tools/c8/sensitivity.py --run S-W17-RAKE --include-heavy --out docs/bench/c8
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c8lib  # noqa: E402

WORLD_DIR = c8lib.REPO_ROOT / "data" / "world" / "v2"
DATA_DIR = c8lib.REPO_ROOT / "data"


# ------------------------------------------------------------------ 構築段階の対照(実行器)
def w16_area_apportionment(world_dir: Path = WORLD_DIR, data_dir: Path = DATA_DIR) -> dict[str, Any]:
    """**D-W16**: 町丁目→セルの按分を「建物床面積」(宣言)vs「面積」(対照)。

    宣言側は ``w16_population.parquet`` の ``home_cell``(実際に凍結された配置)、
    対照側は ``w16_population._chome_coverage`` の 10 m 標本格子で測った**セル被覆面積**で
    同じ町丁目の同じ人数を配り直す(``fitting.largest_remainder``=W16 本体と同じ配り方)。

    Returns:
        ``compare_counts`` の辞書 + 町丁目数・住民数・空セル数。
    """
    import pyarrow.parquet as pq

    from shibuya.build.geo import common as C
    from shibuya.build.pop import fitting as F
    from shibuya.build.pop import shapefile as SH
    from shibuya.build.pop import w16_population as W16

    cells = C.read_parquet_columns(Path(world_dir) / "w2_cells.parquet", ["place_id"])
    place_to_cell = {p: i for i, p in enumerate(cells["place_id"])}
    n_cells = len(place_to_cell)

    shp = Path(data_dir) / "realworld" / "estat" / "r2ka13113" / "r2ka13113.shp"
    dbf = shp.with_suffix(".dbf")
    polys = [
        p.transformed(
            lambda lon, lat: (
                (lon - C.ORIGIN_LATLON[1]) * C.M_PER_DEG_LON,
                (lat - C.ORIGIN_LATLON[0]) * C.M_PER_DEG_LAT,
            )
        )
        for p in SH.read_shp(shp)
    ]
    keys = [str(r["KEY_CODE"]) for r in SH.read_dbf(dbf)]
    _cov, _area, per_cell = W16._chome_coverage(polys, place_to_cell, W16.COVERAGE_STEP_M)

    t = pq.read_table(Path(world_dir) / "w16_population.parquet", columns=["chome_key", "home_cell"])
    chome_key = np.asarray(t["chome_key"].to_pylist())
    home_cell = np.asarray(t["home_cell"])
    keep = (home_cell >= 0) & (chome_key != "")
    chome_key, home_cell = chome_key[keep], home_cell[keep]

    declared = np.bincount(home_cell, minlength=n_cells).astype(np.float64)
    control = np.zeros(n_cells, dtype=np.float64)
    index_of = {k: i for i, k in enumerate(keys)}
    unplaced = 0
    for key in np.unique(chome_key):  # 逐次(P4): 町丁目数(80)ぶん・構築時 1 回
        n = int((chome_key == key).sum())
        j = index_of.get(str(key), -1)
        if j < 0 or per_cell[j][0].size == 0:
            unplaced += n
            continue
        cell_ids, counts = per_cell[j]
        control[cell_ids] += F.largest_remainder(counts.astype(np.float64), n)

    out = c8lib.compare_counts(declared, control)
    out.update(
        {
            "n_chome": len(keys),
            "n_residents": int(declared.sum()),
            "unplaced": int(unplaced),
            "cells_declared_nonzero": int((declared > 0).sum()),
            "cells_control_nonzero": int((control > 0).sum()),
        }
    )
    return out


def w13_temp_plus(
    world_dir: Path = WORLD_DIR, data_dir: Path = DATA_DIR, delta_c: float = 1.5
) -> dict[str, Any]:
    """**D-W15**: 気温 +1.5 ℃ の対照(体感段階 ``heat_stage`` の分布が動くか)。

    ``w13_weather_hourly.parquet`` の実測行から ``w13_weather.wbgt_estimate`` を**同じ式で**
    引き直す(宣言=そのまま/対照=``temp_c + delta_c``)。
    """
    import pyarrow.parquet as pq

    from shibuya.build.field import w13_weather as W13

    t = pq.read_table(Path(world_dir) / "w13_weather_hourly.parquet")
    cols = {n: t[n].to_pylist() for n in ("temp_c", "rh", "wind_ms", "solar_kw_est", "wbgt_est")}
    vocab = list(W13.HEAT_VOCAB)
    base = np.zeros(len(vocab), dtype=np.float64)
    ctrl = np.zeros(len(vocab), dtype=np.float64)
    changed = 0
    n = 0
    dw = 0.0
    for i in range(len(cols["temp_c"])):  # 逐次(P4): 時別行数(840)ぶん
        if cols["wbgt_est"][i] is None or cols["temp_c"][i] is None:
            continue
        w0 = W13.wbgt_estimate(cols["temp_c"][i], cols["rh"][i], cols["wind_ms"][i], cols["solar_kw_est"][i])
        w1 = W13.wbgt_estimate(cols["temp_c"][i] + delta_c, cols["rh"][i], cols["wind_ms"][i], cols["solar_kw_est"][i])
        s0, s1 = W13.heat_stage(w0), W13.heat_stage(w1)
        base[s0] += 1.0
        ctrl[s1] += 1.0
        changed += int(s0 != s1)
        dw += w1 - w0
        n += 1
    out = c8lib.compare_counts(base, ctrl, labels=vocab)
    out.update(
        {
            "delta_c": float(delta_c),
            "n_hours": n,
            "stage_changed": changed,
            "stage_changed_rate": changed / max(1, n),
            "mean_d_wbgt": dw / max(1, n),
            "declared_hist": {v: float(base[i]) for i, v in enumerate(vocab)},
            "control_hist": {v: float(ctrl[i]) for i, v in enumerate(vocab)},
        }
    )
    return out


def w12_hour_uniform(world_dir: Path = WORLD_DIR, data_dir: Path = DATA_DIR) -> dict[str, Any]:
    """**D-W14 前半**: 外界ノードの時間帯配分を「一様」にした対照。

    宣言=``w12_generation_weights.parquet`` の時刻重み(time_dist_12・2015 を 2018/2021 総量へ
    当てた時点混合=expedient)/対照=24 時間一様。
    """
    import pyarrow.parquet as pq

    t = pq.read_table(Path(world_dir) / "w12_generation_weights.parquet")
    hour = np.asarray(t["hour"])
    weight = np.asarray(t["weight"], dtype=np.float64)
    declared = np.zeros(24, dtype=np.float64)
    np.add.at(declared, hour.astype(np.int64), weight)
    # 帰無参照は「重み行数ぶんの標本」を仮の N に置く(**expedient**: 重みは確率で件数ではない)
    n_rows = int(hour.size)
    scaled = declared / max(declared.sum(), 1e-12) * n_rows
    control = np.full(24, n_rows / 24.0)
    out = c8lib.compare_counts(scaled, control, labels=[f"{h}時" for h in range(24)])
    out.update(
        {
            "n_weight_rows": n_rows,
            "declared_share": (declared / max(declared.sum(), 1e-12)).round(6).tolist(),
            "null_n_note": "帰無参照の N=重み行数 2,014(重みは確率で件数ではない=expedient)",
        }
    )
    return out


def w12_jr_phase(world_dir: Path = WORLD_DIR, data_dir: Path = DATA_DIR) -> dict[str, Any]:
    """**D-W14 後半**: 等間隔ダイヤ(JR/東急/京王=expedient)の**位相を半運転間隔ずらす**対照。

    ``source == 'equal_interval_expedient'`` の便だけを (路線, 方向, 曜日種別) ごとに
    中央運転間隔の 1/2 だけずらし、到着の時刻分布(時別・10 分別)がどれだけ動くかを測る。
    実ダイヤ(メトロ)の便は動かさない。
    """
    import pyarrow.parquet as pq

    t = pq.read_table(Path(world_dir) / "w12_timetables.parquet")
    line = np.asarray(t["line"].to_pylist())
    direction = np.asarray(t["direction"].to_pylist())
    calendar = np.asarray(t["calendar"].to_pylist())
    source = np.asarray(t["source"].to_pylist())
    dep = np.asarray(t["departure_min"], dtype=np.float64)

    sel = source == "equal_interval_expedient"
    control = dep.copy()
    groups = sorted({(str(a), str(b), str(c)) for a, b, c in zip(line[sel], direction[sel], calendar[sel])})
    headways: list[float] = []
    for key in groups:  # 逐次(P4): 群数(20)ぶん
        m = sel & (line == key[0]) & (direction == key[1]) & (calendar == key[2])
        v = np.sort(dep[m])
        if v.size < 2:
            continue
        hw = float(np.median(np.diff(v)))
        headways.append(hw)
        control[m] = (dep[m] + hw / 2.0) % 1440.0

    def _hist(x: np.ndarray, bins: int) -> np.ndarray:
        h = np.zeros(bins, dtype=np.float64)
        np.add.at(h, (x % 1440.0 // (1440.0 / bins)).astype(np.int64), 1.0)
        return h

    hour_cmp = c8lib.compare_counts(_hist(dep, 24), _hist(control, 24), labels=[f"{h}時" for h in range(24)])
    bin10 = c8lib.compare_counts(_hist(dep, 144), _hist(control, 144))
    return {
        **hour_cmp,
        # **判定は保守側**(時別で動かなくても 10 分刻みで動けば「ラン対照が要る」)。
        # 1 tick=1 分のエンジンでは乗車判断が分刻みで起きるため。
        "detected": bool(hour_cmp["detected"] or bin10["detected"]),
        "detected_hour": bool(hour_cmp["detected"]),
        "jsd_bits_10min": bin10["jsd_bits"],
        "null_p95_10min": bin10["null_p95"],
        "detected_10min": bin10["detected"],
        "n_departures": int(dep.size),
        "n_shifted": int(sel.sum()),
        "n_groups": len(groups),
        "median_headway_min": float(np.median(headways)) if headways else float("nan"),
        "max_abs_delta_trains_per_hour": float(np.abs(_hist(dep, 24) - _hist(control, 24)).max()),
    }


def w17_rake_fixed12(world_dir: Path = WORLD_DIR, data_dir: Path = DATA_DIR) -> dict[str, Any]:
    """**§8 RAKE_MAX_FRAC**: raking 予算の「適応」(宣言)vs「固定 12%」(対照)。

    宣言側は ``w17_gates.json`` に凍結済みの本番値、対照側は同じ応答 jsonl を
    ``w17_schedule.ingest(rake_budget_rows=0.12×活動数)`` で**回し直す**(約 90 秒・
    応答 jsonl 約 400 MB をストリーミング)。**重い**ので既定では走らせない。
    """
    from shibuya.build.sched import w17_schedule as W17

    gates = c8lib.load_json(Path(world_dir) / "w17_gates.json")
    n_act = int(gates["n_activities"])
    budget = int(W17.RAKE_MAX_FRAC * n_act)
    t0 = time.perf_counter()
    rep, _cols = W17.ingest(Path(world_dir), Path(data_dir), rake_budget_rows=budget)
    declared = gates["raking"]
    return {
        "declared": {
            "mode": "適応(ADAPTIVE_MODIFIED_TARGET − 修復ぶん)",
            "budget_rows": int(declared["budget_rows"]),
            "jsd_max_after": float(declared["jsd_max_after"]),
            "modified_rate": float(gates["modified_rate"]),
            "n_moved": int(declared["n_moved"]),
        },
        "control": {
            "mode": f"固定 {W17.RAKE_MAX_FRAC:.0%}",
            "budget_rows": budget,
            "jsd_max_after": float(rep.rake.max_after),
            "modified_rate": rep.n_modified / max(1, rep.n_considered),
            "n_moved": int(rep.rake.n_moved),
            "jsd_after": {k: float(v) for k, v in rep.rake.jsd_after.items()},
        },
        "d_jsd_max_after": float(rep.rake.max_after) - float(declared["jsd_max_after"]),
        "d_modified_rate": rep.n_modified / max(1, rep.n_considered) - float(gates["modified_rate"]),
        "jsd_bits": abs(float(rep.rake.max_after) - float(declared["jsd_max_after"])),
        "null_p95": None,
        "detected": True,
        "seconds": time.perf_counter() - t0,
        "note": "両側とも決定論の構築設定なので帰無参照(標本ゆらぎ)は無い=差の値そのものが答え。",
    }


#: 台帳の ``runner`` 欄 → 実装(**ここに無い名前は実行できない**)。
RUNNERS: dict[str, Callable[..., dict[str, Any]]] = {
    "w16_area_apportionment": w16_area_apportionment,
    "w13_temp_plus": w13_temp_plus,
    "w12_hour_uniform": w12_hour_uniform,
    "w12_jr_phase": w12_jr_phase,
    "w17_rake_fixed12": w17_rake_fixed12,
}


# ------------------------------------------------------------------ 台帳
def validate_ledger(ledger: Mapping[str, Any]) -> list[str]:
    """台帳の自己検査+**設計書との突合(漏れ検出)**。問題の一覧を返す。"""
    problems: list[str] = []
    rows = list(c8lib.iter_rows(ledger))
    ids: set[str] = set()
    for r in rows:
        rid = str(r.get("id", ""))
        if not rid or rid in ids:
            problems.append(f"id が空か重複: {rid!r}")
        ids.add(rid)
        for field in ("design_anchor", "source", "expedient", "declared", "control", "exec_form", "metric", "criterion", "status"):
            if field not in r:
                problems.append(f"{rid}: 欄 {field} が無い")
        if r.get("exec_form") not in ("build_rerun", "run", "build_rerun+run", "analysis"):
            problems.append(f"{rid}: exec_form が不正({r.get('exec_form')})")
        if r.get("status") not in ("done", "todo"):
            problems.append(f"{rid}: status は done/todo({r.get('status')})")
        runner = r.get("runner")
        if runner is not None and runner not in RUNNERS:
            problems.append(f"{rid}: runner {runner!r} は RUNNERS に無い")
        if r.get("status") == "done" and not r.get("result"):
            problems.append(f"{rid}: status=done なのに result が空")
    gaps = c8lib.ledger_gaps(c8lib.scan_build_spec_sensitivities(), ledger)
    for miss in gaps["missing"]:
        problems.append(f"**漏れ**: 構築仕様書 §2 {miss} の感度行が台帳に無い")
    want_ab = set(c8lib.scan_engine_ablation_ids())
    have_ab = set(ledger.get("process_ablations", {}).get("ids", ()))
    if want_ab - have_ab:
        problems.append(f"**漏れ**: 過程の感度試験 id が台帳に無い {sorted(want_ab - have_ab)}")
    if have_ab - want_ab:
        problems.append(f"台帳にしかない過程 id {sorted(have_ab - want_ab)}")
    return problems


def run_row(row: Mapping[str, Any], *, world_dir: Path, data_dir: Path) -> dict[str, Any]:
    """1 行の対照を実行して ``result`` を作る。"""
    runner = RUNNERS[str(row["runner"])]
    t0 = time.perf_counter()
    res = runner(world_dir, data_dir)  # 全 runner が (world_dir, data_dir) を受ける規約
    res.setdefault("seconds", time.perf_counter() - t0)
    res["verdict"] = c8lib.verdict_from_stage(bool(res.get("detected", True)))
    res["measured_at"] = time.strftime("%Y-%m-%d")
    return res


def ledger_markdown(ledger: Mapping[str, Any]) -> str:
    """台帳 → Markdown(**純関数**・計器盤が同じ表を埋め込む)。"""
    rows = []
    for r in c8lib.iter_rows(ledger):
        res = r.get("result") or {}
        rows.append(
            [
                r.get("id"),
                r.get("design_anchor"),
                str(r.get("expedient", ""))[:40],
                r.get("exec_form"),
                "実行済" if r.get("status") == "done" else "未実行",
                c8lib.fmt(res.get("jsd_bits"), 4),
                c8lib.fmt(res.get("null_p95"), 4),
                {"not_driving": "駆動していない", "needs_run": "ラン対照が要る"}.get(str(res.get("verdict")), "—"),
            ]
        )
    md = [
        "# expedient 感度試験の台帳(実装計画書 §9.1 C8「各 expedient の『結果を駆動していない』証明」)",
        "",
        c8lib.markdown_table(
            ["id", "設計出典", "expedient", "実行形", "状態", "JSD[bits]", "帰無95%", "判定"], rows
        ),
        "",
        "- **判定の読み方(片側)**: 構築対照の差が帰無参照以内 → 入力が動かない=**結果を駆動しえない**。"
        "超えた → 駆動する**かもしれない**=ラン側の対照が要る(構築段階だけで「駆動している」とは結論しない)。",
    ]
    pa = ledger.get("process_ablations", {})
    if pa:
        md += [
            "",
            f"- 世界過程の感度試験 id **{len(pa.get('ids', ()))} 本**は `--ablate <AB-*>` でそのまま切れる"
            f"(実行形={pa.get('exec_form')}・状態={pa.get('status')})。",
        ]
    for q in ledger.get("open_questions", ()):
        md.append(f"- **親判断待ち**: {q}")
    return "\n".join(md)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="expedient 感度試験の台帳と構築段階の対照の実行器")
    ap.add_argument("--ledger", default="", help="台帳 JSON(既定 tools/c8/sensitivity_v1.json)")
    ap.add_argument("--run", default="", help="実行する行 id、または all")
    ap.add_argument("--include-heavy", action="store_true", help="heavy=true の行も回す(W17 再 ingest 約 90 s)")
    ap.add_argument("--world", default=str(WORLD_DIR))
    ap.add_argument("--data", default=str(DATA_DIR))
    ap.add_argument("--out", default="docs/bench/c8")
    ap.add_argument("--no-write-ledger", action="store_true", help="結果を台帳へ書き戻さない")
    ap.add_argument(
        "--list", action="store_true",
        help="台帳を印字して終わる(既定でも印字するので、--run を付けないときの明示用)",
    )
    args = ap.parse_args(list(argv) if argv is not None else None)

    path = Path(args.ledger) if args.ledger else c8lib.SENSITIVITY_PATH
    ledger = c8lib.load_sensitivity(path)
    ran: list[str] = []
    if args.run:
        want = {r["id"] for r in c8lib.iter_rows(ledger)} if args.run == "all" else {args.run}
        for row in ledger["rows"]:
            if row["id"] not in want or not row.get("runner"):
                continue
            if row.get("heavy") and not args.include_heavy and args.run == "all":
                continue
            row["result"] = run_row(row, world_dir=Path(args.world), data_dir=Path(args.data))
            row["status"] = "done"
            ran.append(row["id"])
        if ran and not args.no_write_ledger:
            path.write_text(json.dumps(ledger, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    problems = validate_ledger(ledger)
    md = ledger_markdown(ledger)
    print(md)
    if problems:
        print("\n**自己検査で見つかった問題**")
        for p in problems:
            print(f"- {p}")
    paths = c8lib.write_outputs(args.out, "sensitivity_v1", ledger, md)
    print(json.dumps({"ran": ran, "out": paths, "problems": problems}, ensure_ascii=False))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
