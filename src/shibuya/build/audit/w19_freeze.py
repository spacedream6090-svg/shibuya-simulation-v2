"""W19 manifest 凍結(§1 W19・D-W20・運用設計書 §1.2「データ資産」「holdout封印」)。

やること
1. **データ資産表**: どの段階かが読む入力ファイルを列挙し ``{id, path, sha256, bytes}`` を出す。
   一覧は各段階モジュールが宣言している入力定数から組む(手書きの重複を避ける)。
2. **holdout 封印**: seal_scheme=``S``(層別・運用設計書 §1.2)。層ごとに
   ``member_hash = sha256(整列した各メンバーの sha256 を改行で連ねた文字列)``・``opened=false``。
3. **holdout 規律の静的ゲート**(§0-5): ``src/shibuya/build`` 配下の**本モジュール以外**に
   holdout のファイル名パターンが1つも現れないこと。現れたら構築コードが holdout を
   開いた可能性がある=ゲート不合格。
4. 段階ごとの出力 sha256 を連ねた ``partial_build_hash``(W0..W18)。最終 ``build_hash`` は
   ``build.run.write_build_manifest`` が全段階(W20 まで)で計算する。

**封印時刻**: ``sealed_utc`` は**パラメータ**(既定=本仕様の承認日)。実行時刻を使うとヘッダが
非決定になり D-W20 の再構築テスト T1(build_hash 一致)が壊れるため(§0-1)。

出力 ``w19_freeze.json``。同じ内容をヘッダ ``notes`` にも入れるので、
``build_manifest.json``(= 全ヘッダの埋め込み)がそのまま資産表と封印を持つ。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..field import w7_planspec, w10_noise, w12_external_nodes, w13_weather
from ..geo import common as C
from ..geo import w0_crs, w1_walk_graph, w4_heights, w5_entrances, w6_poi_org, w11_station_exits

STAGE = "W19"
STAGE_VERSION = "1.0.0"

#: 封印方式(運用設計書 §1.2: D=ダイジェスト/S=層別/P=第三者)。
SEAL_SCHEME = "S"
#: 封印時刻(決定論のため固定パラメータ。仕様書 v1 の承認日)。
SEALED_UTC = "2026-09-08T00:00:00Z"

#: holdout 層(§0-5)。構築で**一切**読まないファイル群。
HOLDOUT_LAYERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("kddi_la", ("realworld/kddi_la",)),
    ("shibuya_jinryu", ("realworld/shibuya_jinryu",)),
    ("boundary_counts", ("realworld/boundary_counts.json",)),
)
#: 静的ゲートで探す語(= holdout 層名。本モジュールは検査対象から外す)。
HOLDOUT_TOKENS: tuple[str, ...] = tuple(name for name, _ in HOLDOUT_LAYERS)
#: 本モジュールのファイル名(自己 HIT を避ける)。
SELF_NAME = "w19_freeze.py"


def _joined(parts: tuple[str, ...]) -> str:
    return "/".join(parts)


def data_asset_paths(data_root: Path) -> list[str]:
    """全段階の入力ファイル(data 根からの相対パス・整列済み・重複なし)。"""
    rel: set[str] = set()
    for mod in (w0_crs, w1_walk_graph, w4_heights, w5_entrances, w6_poi_org, w7_planspec):
        for parts in getattr(mod, "INPUT_FILES", ()):
            rel.add(_joined(parts))
    for name in w11_station_exits.ODPT_STATION_FILES:
        rel.add(f"odpt/{name}")
    rel.add(_joined(w10_noise.KASYO))
    rel.add(_joined(w10_noise.R5_POINTS))
    # PT_CORE(docs/bench/pt_shibuya/…)は data 根の外なので資産表に載せない(下の notes に記す)。
    for const in ("STATION_FLOW", "TIME_DIST", "TRANSFER", "PASSENGER_SURVEY"):
        parts = getattr(w12_external_nodes, const, None)
        if parts:
            rel.add(_joined(tuple(parts)))
    for _line, fname in w12_external_nodes.METRO_TIMETABLES:
        rel.add(f"odpt/{fname}")
    rel.add(_joined(w13_weather.ETRN_CSV))
    amedas = data_root.joinpath(*w13_weather.AMEDAS_DIR)
    if amedas.exists():
        for p in sorted(amedas.rglob("amedas_*.json")):
            rel.add(p.relative_to(data_root).as_posix())
    # W8/W9(可視性・影)の外部入力
    rel.add("realworld/osm/shibuya_osm_wide_v8.json")
    rel.add("plateau/terrain.npz")
    rel.add("plateau/terrain.json")
    return sorted(rel)


def seal_layer(data_root: Path, members: tuple[str, ...]) -> tuple[str, list[dict[str, Any]]]:
    """holdout 層 → (member_hash, メンバー表)。ファイルの中身は**開かず** sha256 だけ取る。"""
    files: list[Path] = []
    for m in members:
        p = data_root / m
        if p.is_dir():
            files.extend(sorted(q for q in p.rglob("*") if q.is_file()))
        elif p.is_file():
            files.append(p)
    entries = [
        {
            "path": f.relative_to(data_root).as_posix(),
            "sha256": C.sha256_file(f),
            "bytes": f.stat().st_size,
        }
        for f in sorted(files)
    ]
    digest = C.sha256_bytes("\n".join(sorted(e["sha256"] for e in entries)).encode("utf-8"))
    return digest, entries


def scan_build_sources(build_root: Path) -> dict[str, list[str]]:
    """``src/shibuya/build`` 配下で holdout 語を含むモジュールを探す(本モジュールは除く)。"""
    hits: dict[str, list[str]] = {}
    for path in sorted(build_root.rglob("*.py")):
        if path.name == SELF_NAME or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        found = [tok for tok in HOLDOUT_TOKENS if tok in text]
        if found:
            hits[path.relative_to(build_root).as_posix()] = found
    return hits


def run(ctx: C.Ctx) -> C.StageResult:
    rel_paths = data_asset_paths(ctx.data)
    assets: list[dict[str, Any]] = []
    missing: list[str] = []
    for rel in rel_paths:
        p = ctx.data / rel
        if not p.exists():
            missing.append(rel)
            continue
        assets.append(
            {
                "id": rel.replace("/", "."),
                "path": rel,
                "sha256": C.sha256_file(p),
                "bytes": p.stat().st_size,
            }
        )

    layers: list[dict[str, Any]] = []
    for name, members in HOLDOUT_LAYERS:
        member_hash, entries = seal_layer(ctx.data, members)
        layers.append(
            {
                "name": name,
                "members": [e["path"] for e in entries],
                "member_files": entries,
                "member_hash": member_hash,
                "sealed_utc": SEALED_UTC,
                "opened": False,
            }
        )

    build_root = Path(__file__).resolve().parents[1]
    hits = scan_build_sources(build_root)

    # --- W0..W18 の出力ダイジェスト(最終 build_hash は build.run が全段階で組む)---
    stage_digests: list[dict[str, Any]] = []
    digests: list[str] = []
    for path in sorted(ctx.out.glob("W*.header.json"), key=lambda p: int(p.stem.split(".")[0][1:])):
        h = C.load_json(path)
        if int(h["stage"][1:]) >= int(STAGE[1:]):
            continue
        outs = [o["sha256"] for o in h["outputs"]]
        digests.extend(outs)
        stage_digests.append(
            {
                "stage": h["stage"],
                "stage_version": h["stage_version"],
                "input_hash": h["input_hash"],
                "param_hash": h["param_hash"],
                "output_sha256": outs,
            }
        )
    partial = C.sha256_bytes("".join(digests).encode("utf-8"))

    freeze = {
        "schema": "shibuya.build.audit/w19_freeze/1",
        "data_assets": assets,
        "data_assets_missing": missing,
        "holdout_seal": {"seal_scheme": SEAL_SCHEME, "layers": layers},
        "stage_digests": stage_digests,
        "partial_build_hash_w0_w18": partial,
    }

    params: dict[str, Any] = {
        "seal_scheme": SEAL_SCHEME,
        "sealed_utc": SEALED_UTC,
        "holdout_layers": {name: list(members) for name, members in HOLDOUT_LAYERS},
        "sealed_utc_note": "実行時刻を使わない(§0-1 決定論・T1 再構築一致のため固定パラメータ)",
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([ctx.data / r for r in rel_paths if (ctx.data / r).exists()]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=[],
        expedients=[
            "sealed_utc は固定パラメータ(実行時刻ではない)",
            "データ資産表は各段階モジュールの入力定数から組む(段階が定数を持たない入力は落ちる)",
        ],
        notes={
            "data_assets": assets,
            "data_assets_count": len(assets),
            "data_assets_missing": missing,
            "data_assets_bytes_total": sum(a["bytes"] for a in assets),
            "holdout_seal": {
                "seal_scheme": SEAL_SCHEME,
                "layers": [
                    {
                        "name": lyr["name"],
                        "member_hash": lyr["member_hash"],
                        "n_members": len(lyr["members"]),
                        "sealed_utc": lyr["sealed_utc"],
                        "opened": lyr["opened"],
                    }
                    for lyr in layers
                ],
            },
            "holdout_static_scan_hits": hits,
            "partial_build_hash_w0_w18": partial,
            "assets_outside_data_root": [
                "docs/bench/pt_shibuya/pt6_summary_core0241.json (W12 の PT 集計・data 根の外)"
            ],
        },
    )
    res.outputs.append(C.write_json(ctx.out, "w19_freeze.json", freeze, rows=len(assets)))
    res.gates = [
        C.Gate("data_assets", len(assets), None),
        C.Gate("data_assets_missing", len(missing), 0),
        C.Gate("holdout_layers", len(layers), 3),
        C.Gate("holdout_layers_all_sealed", all(not lyr["opened"] for lyr in layers), True),
        C.Gate("holdout_members_hashed", sum(len(lyr["members"]) for lyr in layers), None),
        C.Gate("holdout_not_referenced_in_build_code", len(hits), 0),
        C.Gate("seal_scheme", SEAL_SCHEME, "S"),
        C.Gate("partial_build_hash_w0_w18", partial[:16], None),
    ]
    return res
