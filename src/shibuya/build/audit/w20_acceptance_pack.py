"""W20 検収パック(§1 W20)。

目視検収セット(画像)+全段階のゲート結果表(markdown)+要約 JSON を
``<out>/acceptance/`` に書く。画像は自前の PNG 書き出し(``build.vis.png``)で作る
(部品表に PIL/matplotlib は無い)。

画像
  cells.png       セル(100m×層)を POI 密度で塗る + 街区の代表点
  exits.png       駅出入口45 を歩行グラフの上に重ねる
  noise_day.png   W10 昼の騒音場をグレースケールで 5m 格子へ焼く
  visibility.png  W8 のセル平均可視対象数
  shadow_noon.png W9 の正午面(日陰=暗)

表・要約
  gate_table.md   全段階のゲート(PASS/FAIL)+落ちたゲートの一覧(先頭に build_hash)
  summary.json    段階・出力・バイト数・被覆指標ベクトル・holdout封印の要約(+ build_hash)

**build_hash の射程**: パックが自分で名乗る識別子は **W0..W19** の出力ハッシュ連結
(``build_manifest.json`` の build_hash は W20 自身の出力も含むので別値になる。W20 の出力を
含めると自分のハッシュを自分の中に書くことになり決定論が壊れる)。

**W20 は判定しない**: 落ちたゲートを隠さずそのまま出す(親検収の材料)。
自分のゲートは「検収パックが揃っているか」だけ。
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..geo import common as C
from ..vis.png import Canvas, ramp_rgb, write_png

STAGE = "W20"
STAGE_VERSION = "1.0.0"

#: 画像の分解能 [m/画素]。
M_PER_PX = 5.0
#: 出力ディレクトリ名。
PACK_DIR = "acceptance"


def _bounds(xs: np.ndarray, ys: np.ndarray, pad: float = 60.0) -> tuple[float, float, float, float]:
    return (
        float(np.floor(xs.min() - pad)),
        float(np.floor(ys.min() - pad)),
        float(np.ceil(xs.max() + pad)),
        float(np.ceil(ys.max() + pad)),
    )


def _norm(v: np.ndarray) -> np.ndarray:
    lo = float(v.min())
    hi = float(v.max())
    if hi <= lo:
        return np.zeros_like(v, dtype=np.float64)
    return (v.astype(np.float64) - lo) / (hi - lo)


def _gate_rows(headers: list[dict[str, Any]]) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for h in headers:
        for name, g in h["gates"].items():
            rows.append(
                (
                    h["stage"],
                    name,
                    str(g["value"]),
                    "-" if g["expected"] is None else str(g["expected"]),
                    "PASS" if g["pass"] else "FAIL",
                )
            )
    return rows


def upstream_build_hash(headers: list[dict[str, Any]]) -> str:
    """W20 より前の段階の出力 sha256 を W 番号順に連結した文字列の sha256。

    ``build.run`` の ``build_hash`` と**同じ作り方**だが、W20 自身の出力は入れない
    (検収パックの中身が自分のハッシュに入ると自己参照になる)。パックが「どの構築の
    ものか」を自分で名乗るための識別子。
    """
    digests = [o["sha256"] for h in headers for o in h["outputs"]]
    return C.sha256_bytes("".join(digests).encode("utf-8"))


#: ``build_hash`` の射程の説明(summary.json / gate_table.md に同じ文言で出す)。
BUILD_HASH_SCOPE = (
    "W0..W19 の出力 sha256 を W 番号順に連結した sha256(W20 自身の出力は自己参照に"
    "なるので含めない)。build_manifest.json の build_hash(全段階)とは別値。"
)


def gate_table_markdown(headers: list[dict[str, Any]], build_hash: str | None = None) -> str:
    """全段階のゲート表(markdown)。``build_hash`` を渡すと先頭に出す。"""
    rows = _gate_rows(headers)
    failed = [r for r in rows if r[4] == "FAIL"]
    lines = [
        "# W20 検収パック — ゲート結果表",
        "",
        f"- build_hash: `{upstream_build_hash(headers) if build_hash is None else build_hash}`",
        f"- build_hash の射程: {BUILD_HASH_SCOPE}",
        f"- 段階数: {len(headers)}",
        f"- ゲート数: {len(rows)}(PASS {len(rows) - len(failed)} / FAIL {len(failed)})",
        "",
        "## 落ちたゲート(理由は各段階ヘッダの notes を見る)",
        "",
    ]
    if failed:
        lines += ["| 段階 | ゲート | 値 | 期待 |", "|---|---|---|---|"]
        lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |" for r in failed]
    else:
        lines.append("なし。")
    lines += ["", "## 全ゲート", "", "| 段階 | ゲート | 値 | 期待 | 判定 |", "|---|---|---|---|---|"]
    lines += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |" for r in rows]
    lines.append("")
    return "\n".join(lines)


def run(ctx: C.Ctx) -> C.StageResult:
    pack = ctx.out / PACK_DIR
    pack.mkdir(parents=True, exist_ok=True)

    headers: list[dict[str, Any]] = []
    header_paths = []
    for path in sorted(ctx.out.glob("W*.header.json"), key=lambda p: int(p.stem.split(".")[0][1:])):
        h = C.load_json(path)
        if int(h["stage"][1:]) >= int(STAGE[1:]):
            continue
        headers.append(h)
        header_paths.append(path)

    pts = C.read_parquet_columns(ctx.out / "w10_street_points.parquet", ["x", "y", "band"])
    px = np.asarray(pts["x"], dtype=np.float64)
    py = np.asarray(pts["y"], dtype=np.float64)
    pband = np.asarray(pts["band"])
    bounds = _bounds(px, py)

    cells = C.read_parquet_columns(
        ctx.out / "w2_cells.parquet", ["place_id", "ix", "iy", "band", "centroid_x", "centroid_y"]
    )
    poi = C.read_parquet_columns(ctx.out / "w6_poi.parquet", ["place_id", "x", "y"])
    exits = C.read_parquet_columns(ctx.out / "w11_station_exits.parquet", ["exit_id", "x", "y"])
    edges = C.read_parquet_columns(
        ctx.out / "w1_edges.parquet", ["edge_idx", "geom_start", "geom_count", "band"]
    )
    coords = np.load(ctx.out / "w1_edge_geometry.npz")["coords"]

    written: list[str] = []

    # --- cells.png: セル(100m格子×層)を POI 密度で塗る -------------------------------
    poi_count: dict[str, int] = {}
    for pid in poi["place_id"]:
        poi_count[pid] = poi_count.get(pid, 0) + 1
    band_tint = {"GL": (1.0, 1.0, 1.0), "DECK": (1.0, 0.75, 0.55), "UG": (0.6, 0.75, 1.0)}
    cv = Canvas(*bounds, M_PER_PX)
    counts = np.array([poi_count.get(pid, 0) for pid in cells["place_id"]], dtype=np.float64)
    scaled = np.log1p(counts) / max(np.log1p(counts).max(), 1e-9)
    base = ramp_rgb(scaled).astype(np.float64)
    for i, pid in enumerate(cells["place_id"]):
        tint = band_tint.get(cells["band"][i], (1.0, 1.0, 1.0))
        rgb = tuple(int(min(255, base[i][k] * tint[k])) for k in range(3))
        x0 = cells["ix"][i] * C.CELL_M
        y0 = cells["iy"][i] * C.CELL_M
        half = int(C.CELL_M / M_PER_PX / 2) - 1
        cv.square(x0 + C.CELL_M / 2, y0 + C.CELL_M / 2, half, rgb)
    cv.points(np.asarray(cells["centroid_x"]), np.asarray(cells["centroid_y"]), (255, 60, 60))
    written.append("cells.png")
    cv.write(pack / "cells.png")

    # --- exits.png: 歩行グラフ + 駅出入口45 -------------------------------------------
    cv = Canvas(*bounds, M_PER_PX)
    for s, n in zip(edges["geom_start"], edges["geom_count"]):
        for k in range(int(s), int(s) + int(n) - 1):
            cv.line(
                float(coords[k, 0]), float(coords[k, 1]),
                float(coords[k + 1, 0]), float(coords[k + 1, 1]),
                (105, 110, 120),
            )
    for x, y in zip(exits["x"], exits["y"]):
        cv.square(float(x), float(y), 2, (255, 70, 70))
    written.append("exits.png")
    cv.write(pack / "exits.png")

    # --- noise_day.png: W10 昼の騒音場(グレースケール)--------------------------------
    noise = np.load(ctx.out / "w10_noise_day.npy")
    width = int(round((bounds[2] - bounds[0]) / M_PER_PX))
    height = int(round((bounds[3] - bounds[1]) / M_PER_PX))
    col = np.clip(((px - bounds[0]) / M_PER_PX).astype(np.int64), 0, width - 1)
    row = np.clip(height - 1 - ((py - bounds[1]) / M_PER_PX).astype(np.int64), 0, height - 1)
    gray = np.zeros((height, width), dtype=np.uint8)
    flat = row * width + col
    acc = np.zeros(height * width, dtype=np.float64)
    cnt = np.zeros(height * width, dtype=np.int64)
    np.add.at(acc, flat, noise.astype(np.float64))
    np.add.at(cnt, flat, 1)
    filled = cnt > 0
    vals = np.zeros(height * width, dtype=np.float64)
    vals[filled] = acc[filled] / cnt[filled]
    lo, hi = 40.0, 85.0
    gray_flat = np.zeros(height * width, dtype=np.uint8)
    gray_flat[filled] = np.clip(
        np.rint((vals[filled] - lo) / (hi - lo) * 255.0), 0, 255
    ).astype(np.uint8)
    gray = gray_flat.reshape(height, width)
    written.append("noise_day.png")
    write_png(pack / "noise_day.png", gray)

    # --- visibility.png: セル平均可視対象数 ---------------------------------------------
    t1 = C.read_parquet_columns(ctx.out / "w8_t1.parquet", ["place_idx", "n_visible"])
    place_idx = np.asarray(t1["place_idx"], dtype=np.int64)
    n_vis = np.asarray(t1["n_visible"], dtype=np.float64)
    n_cells = len(cells["place_id"])
    sums = np.zeros(n_cells)
    nums = np.zeros(n_cells)
    ok = place_idx >= 0
    np.add.at(sums, place_idx[ok], n_vis[ok])
    np.add.at(nums, place_idx[ok], 1.0)
    mean_vis = np.divide(sums, nums, out=np.zeros(n_cells), where=nums > 0)
    cv = Canvas(*bounds, M_PER_PX)
    colors = ramp_rgb(_norm(mean_vis))
    for i in range(n_cells):
        half = int(C.CELL_M / M_PER_PX / 2) - 1
        cv.square(
            cells["ix"][i] * C.CELL_M + C.CELL_M / 2,
            cells["iy"][i] * C.CELL_M + C.CELL_M / 2,
            half,
            tuple(int(v) for v in colors[i]),
        )
    written.append("visibility.png")
    cv.write(pack / "visibility.png")

    # --- shadow_noon.png: W9 正午面 -----------------------------------------------------
    shadow_files = sorted(ctx.out.glob("w9_shadow_*.npy"))
    shadow_noon_share: float | None = None
    if shadow_files:
        planes = np.load(shadow_files[0])
        noon = np.unpackbits(planes[(12 * 60) // 5])[: px.shape[0]]
        shadow_noon_share = float(noon.mean())
        gray_flat = np.full(height * width, 25, dtype=np.uint8)
        acc = np.zeros(height * width, dtype=np.float64)
        cnt = np.zeros(height * width, dtype=np.int64)
        np.add.at(acc, flat, noon.astype(np.float64))
        np.add.at(cnt, flat, 1)
        filled = cnt > 0
        share = np.zeros(height * width)
        share[filled] = acc[filled] / cnt[filled]
        gray_flat[filled] = np.clip(np.rint((1.0 - share[filled]) * 235.0) + 20, 0, 255).astype(
            np.uint8
        )
        written.append("shadow_noon.png")
        write_png(pack / "shadow_noon.png", gray_flat.reshape(height, width))

    # --- gate_table.md / summary.json ---------------------------------------------------
    build_hash = upstream_build_hash(headers)
    md = gate_table_markdown(headers, build_hash=build_hash)
    (pack / "gate_table.md").write_bytes(md.encode("utf-8"))
    written.append("gate_table.md")

    wc = C.load_json(ctx.out / "wc_index.json") if (ctx.out / "wc_index.json").exists() else None
    frz = C.load_json(ctx.out / "w19_freeze.json") if (ctx.out / "w19_freeze.json").exists() else None
    rows = _gate_rows(headers)
    summary = {
        "schema": "shibuya.build.audit/acceptance_summary/1",
        "build_hash": build_hash,
        "build_hash_scope": BUILD_HASH_SCOPE,
        "stages": [
            {
                "stage": h["stage"],
                "stage_version": h["stage_version"],
                "outputs": [
                    {"path": o["path"], "bytes": o["bytes"], "rows": o["rows"]} for o in h["outputs"]
                ],
                "output_bytes": sum(o["bytes"] for o in h["outputs"]),
                "gates_pass": sum(1 for g in h["gates"].values() if g["pass"]),
                "gates_fail": sum(1 for g in h["gates"].values() if not g["pass"]),
                "expedients": h["expedients"],
            }
            for h in headers
        ],
        "gates_total": len(rows),
        "gates_failed": [{"stage": r[0], "gate": r[1], "value": r[2], "expected": r[3]}
                         for r in rows if r[4] == "FAIL"],
        "world_coverage": None if wc is None else {
            "catalog_sha16": wc["catalog_sha16"],
            "vector": wc["vector"],
            "X": wc["X"],
            "dead_stock_candidates": wc["dead_stock_candidates"],
            "orphans": wc["orphans"],
        },
        "holdout_seal": None if frz is None else {
            "seal_scheme": frz["holdout_seal"]["seal_scheme"],
            "layers": [
                {"name": lyr["name"], "member_hash": lyr["member_hash"], "opened": lyr["opened"]}
                for lyr in frz["holdout_seal"]["layers"]
            ],
        },
        "images": sorted(w for w in written if w.endswith(".png")),
        "noise_day_scale_db": [lo, hi],
        "shadow_noon_share": shadow_noon_share,
        "viewpoints": int(px.shape[0]),
        "viewpoints_by_band": {b: int((pband == b).sum()) for b in sorted(set(pband.tolist()))},
    }

    params: dict[str, Any] = {
        "m_per_px": M_PER_PX,
        "pack_dir": PACK_DIR,
        "noise_scale_db": [lo, hi],
        "band_tint": {k: list(v) for k, v in sorted(band_tint.items())},
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(header_paths),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=[],
        expedients=[
            "画像の配色・分解能(5m/画素)は目視用で判断には使わない",
            "騒音場の階調範囲 40-85 dB に固定(自動スケールにしない)",
        ],
        notes={
            "pack_dir": PACK_DIR,
            "build_hash": build_hash,
            "build_hash_scope": BUILD_HASH_SCOPE,
            "files": sorted(written),
            "gates_total": len(rows),
            "gates_failed_count": sum(1 for r in rows if r[4] == "FAIL"),
            "gates_failed": [f"{r[0]}.{r[1]}" for r in rows if r[4] == "FAIL"],
            "image_size_px": [width, height],
            "shadow_noon_share": shadow_noon_share,
        },
    )
    for name in sorted(written):
        path = pack / name
        res.outputs.append(
            {
                "path": path.relative_to(ctx.out).as_posix(),
                "sha256": C.sha256_file(path),
                "bytes": path.stat().st_size,
                "rows": None,
            }
        )
    res.outputs.append(
        C.write_json(ctx.out, f"{PACK_DIR}/summary.json", summary, rows=len(headers))
    )
    expected_images = {"cells.png", "exits.png", "noise_day.png", "visibility.png", "shadow_noon.png"}
    res.gates = [
        C.Gate("acceptance_images", len(summary["images"]), 5),
        C.Gate("acceptance_images_complete", sorted(expected_images) == summary["images"], True),
        C.Gate("gate_table_written", (pack / "gate_table.md").exists(), True),
        C.Gate("summary_written", (ctx.out / PACK_DIR / "summary.json").exists(), True),
        C.Gate("build_hash_in_pack", build_hash[:16], None, passed=len(build_hash) == 64),
        C.Gate("stages_covered", len(headers), None),
        C.Gate("gates_failed_upstream", sum(1 for r in rows if r[4] == "FAIL"), None),
    ]
    return res
