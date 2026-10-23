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

from ..field import w7_planspec, w10_noise, w12_external_nodes, w12_real_timetables, w13_weather
from ..geo import common as C
from ..geo import w0_crs, w1_walk_graph, w4_heights, w5_entrances, w6_poi_org, w11_station_exits
from ..pop import w16_population
from ..sched import w20_calendar_1a

STAGE = "W19"
STAGE_VERSION = "1.0.0"  # 〔第333〕層の元の表(layer_independence)を notes に足した。資産の作り直しは版上げ 2 回目で

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

#: 〔第333・回答 10-13b §1 1-2〕**層の元**(データセットの系)。holdout 層と構築の入力が同じ元を持つかを機械で照らす
#: 表。名前の静的ゲート(``scan_build_sources``)は層の**名前**しか探さないので、同じ元を別のファイル名で読む形
#: (``boundary_counts`` と W12 の大都市交通センサス)は捕まえない(仕分け C X1・X2)。元は「提供元/データセット」の語で
#: 書き、ファイル名ではなく系で合わせる。
SOURCE_FAMILIES: dict[str, str] = {
    # 渋谷区オープンデータの KDDI Location Analyzer(滞在人口・通過人口)。kddi_la は事前登録 v1.3 で開封済み。
    "kddi_la": "kddi_location_analyzer/shibuya_city_opendata",
    # 同じ区のオープンデータの 6 層(5 表)=kddi_la と列名・行数が一致(月次・日の欄なし)。
    "shibuya_jinryu": "kddi_location_analyzer/shibuya_city_opendata",
    # 大都市交通センサス(station_flow/time_dist/transfer)+ODPT 乗降人員=W12 の構築の入力と同じ系。
    "boundary_counts": "transport_census_12+odpt_passenger_survey",
    # 〔第 2 期 2-3b〕構築の入力の層(holdout ではない)=W12 の実ダイヤ。元の語は層の名と同じにする
    # (``w12_real_timetables.INPUT_FAMILIES``)。ユーザーが各社の公式サイトから手で入手した時刻表の読み取り(JR・東急)。
    "user_timetables": w12_real_timetables.FAMILY_USER,
    # ODPT チャレンジ枠(京王 井の頭線・利用は応募と照合の範囲・生の行は再配布しない)。
    "odpt_challenge": w12_real_timetables.FAMILY_CHALLENGE,
    # ODPT オープン枠の静的データ版 1(銀座線の列車時刻表)。日次の実時間の取得(odpt_rt)とは別の系。
    "odpt_static": w12_real_timetables.FAMILY_STATIC,
}
#: 構築の入力の元(系 → その系から読む入力。W12 の定数から組む=手書きの重複を避ける)。
#: 〔第 2 期 2-3b〕W12 の実ダイヤの入力の層を 3 つ足した(``w12_real_timetables.input_rel_paths`` から組む)。
#: holdout の層がこれらと同じ元を持つ形になれば ``layer_independence`` が「構築の入力と同じ元」と印を付ける。
BUILD_INPUT_FAMILIES: dict[str, tuple[str, ...]] = {
    "transport_census_12+odpt_passenger_survey": tuple(
        "/".join(getattr(w12_external_nodes, c))
        for c in ("STATION_FLOW", "TIME_DIST", "TRANSFER", "PASSENGER_SURVEY")
        if getattr(w12_external_nodes, c, None)
    ),
    # 〔2-4〕元の宣言は W12 の京王の切替口(USE_ODPT_CHALLENGE)に依らない=in_use=False(既定の値は前と同じ)
    **{fam: w12_real_timetables.input_rel_paths(fam, in_use=False) for fam in w12_real_timetables.INPUT_FAMILIES},
    # 〔第 3 期 3-1〕構築の段 W20cal(暦 1a・脇の段=ALL_STAGES の外)の構築側の表の元(社会生活基本調査の東京都の 2 表・
    # 就業構造基本調査の地域の表・経済センサスの市区町村の表)。検証側の表(第 14・15・68-3 表)はここに載らない
    **{fam: tuple(paths) for fam, paths in w20_calendar_1a.INPUT_FAMILIES.items()},
}
#: 開封済みの層(事前登録で 1 回開けた。値は読まないが「独立」ではない)。
OPENED_LAYERS: dict[str, str] = {
    "kddi_la": "事前登録 v1.3(c7-day-4・3 seed・0/4)で開封済み=docs/bench/c7",
}


def layer_independence() -> list[dict[str, Any]]:
    """holdout 層ごとに「元」「構築の入力と同じ元か」「独立か」「印」を返す(値は読まない・表だけ)。

    独立でない層は一覧から消さず「照合用」の印を付ける(回答 10-13b §1 1-2=一覧の変更はユーザー承認)。
    """
    out: list[dict[str, Any]] = []
    families_of_opened = {SOURCE_FAMILIES[n] for n in OPENED_LAYERS if n in SOURCE_FAMILIES}
    for name, _members in HOLDOUT_LAYERS:
        fam = SOURCE_FAMILIES.get(name)
        shares_build = fam in BUILD_INPUT_FAMILIES
        same_as_opened = (name not in OPENED_LAYERS) and (fam in families_of_opened)
        opened = name in OPENED_LAYERS
        independent = (fam is not None) and not shares_build and not same_as_opened and not opened
        reasons: list[str] = []
        if fam is None:
            reasons.append("元が未登録(SOURCE_FAMILIES に足す)")
        if shares_build:
            reasons.append("構築の入力と同じ元: " + ", ".join(BUILD_INPUT_FAMILIES[fam]))
        if same_as_opened:
            reasons.append("開封済みの層と同じ元: " + ", ".join(sorted(n for n in OPENED_LAYERS if SOURCE_FAMILIES.get(n) == fam)))
        if opened:
            reasons.append(OPENED_LAYERS[name])
        out.append({
            "name": name,
            "source_family": fam,
            "shares_build_input": shares_build,
            "same_family_as_opened": same_as_opened,
            "opened": opened,
            "independent": independent,
            "mark": "独立" if independent else "照合用(独立でない)",
            "reasons": reasons,
        })
    return out
#: 本モジュールのファイル名(自己 HIT を避ける)。
SELF_NAME = "w19_freeze.py"


def _joined(parts: tuple[str, ...]) -> str:
    return "/".join(parts)


def data_asset_paths(data_root: Path) -> list[str]:
    """全段階の入力ファイル(data 根からの相対パス・整列済み・重複なし)。"""
    rel: set[str] = set()
    for mod in (
        w0_crs, w1_walk_graph, w4_heights, w5_entrances, w6_poi_org, w7_planspec, w16_population
    ):
        for parts in getattr(mod, "INPUT_FILES", ()):
            rel.add(_joined(parts))
    for name in w11_station_exits.ODPT_STATION_FILES:
        rel.add(f"odpt/{name}")
    rel.add(_joined(w10_noise.KASYO))
    rel.add(_joined(w10_noise.R5_POINTS))
    rel.add(_joined(w10_noise.ROAD_NAMES))  # 段 1c(道路名の突合)
    # PT_CORE(docs/bench/pt_shibuya/…)は data 根の外なので資産表に載せない(下の notes に記す)。
    for const in ("STATION_FLOW", "TIME_DIST", "TRANSFER", "PASSENGER_SURVEY"):
        parts = getattr(w12_external_nodes, const, None)
        if parts:
            rel.add(_joined(tuple(parts)))
    # 〔第 2 期 2-3b〕W12 が実際に読むファイルだけ。実ダイヤ(既定)では ODPT の駅の時刻表は半蔵門線・副都心線だけで、
    # 実ダイヤの入力 3 層(ユーザー提供の時刻表の読み取り・ODPT チャレンジ枠・ODPT オープン枠の静的データ版 1)を足す。
    for _line, fname in w12_external_nodes.metro_timetables_in_use():
        rel.add(f"odpt/{fname}")
    rel.update(w12_real_timetables.all_input_rel_paths())
    # 〔改訂(第330 B5)〕W13 が実際に読むファイルだけ(窓の CSV 2 本と祝日 CSV)。旧は
    # data/realworld/amedas を rglob して、構築が読まない日次取得の日まで載せうる形だった。
    for parts in w13_weather.INPUT_FILES:
        rel.add(_joined(parts))
    # 〔第 3 期 3-1〕構築の段 W20cal(暦 1a)の入力(構築側の 4 本の xlsx と産業の写像)。第 31/36 表の錨は data 根の外
    for parts in w20_calendar_1a.INPUT_FILES:
        rel.add(_joined(parts))
    pool_root = data_root.joinpath(*w16_population.POOL_DIR)
    if pool_root.exists():
        for q in sorted(pool_root.rglob("part-*.jsonl")):
            rel.add(q.relative_to(data_root).as_posix())
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


#: 〔第 4 期 4-3 段 10〕差し替えの世界の W21 の材料の台帳(置き場に manifest があるときだけ読む=本体の v2 は今のまま)。
W21_MANIFESTS: tuple[str, ...] = ("w21_manifest.json", "w21b_manifest.json", "w21c_manifest.json")


def w21_material_paths(out_dir: Path) -> dict[str, str]:
    """置き場の W21 の manifest の材料(``sources`` の元のファイルと写し)→ {data 根からの相対: manifest の md5}。"""
    got: dict[str, str] = {}
    for name in W21_MANIFESTS:  # 逐次: manifest の数(3)
        p = Path(out_dir) / name
        if not p.exists():
            continue
        for src in C.load_json(p).get("sources", []):  # 逐次: 材料の数(≤ 60)
            for key, md5 in (("path", "md5"), ("derived", "derived_md5")):
                rel = src.get(key)
                if rel:
                    got.setdefault(str(rel), str(src.get(md5) or ""))
    return dict(sorted(got.items()))


def run(ctx: C.Ctx) -> C.StageResult:
    rel_paths = data_asset_paths(ctx.data)
    # 〔段 10〕W21 の材料(差し替えの世界=W16 の体の元が W21 になった)を資産の表へ(md5 を manifest と照らす)
    w21_mat = w21_material_paths(ctx.out)
    rel_paths = sorted(set(rel_paths) | set(w21_mat))
    w21_md5_bad: list[str] = []
    assets: list[dict[str, Any]] = []
    missing: list[str] = []
    for rel in rel_paths:
        p = ctx.data / rel
        if not p.exists():
            missing.append(rel)
            continue
        row = {
            "id": rel.replace("/", "."),
            "path": rel,
            "sha256": C.sha256_file(p),
            "bytes": p.stat().st_size,
        }
        if rel in w21_mat:
            import hashlib

            md5 = hashlib.md5(p.read_bytes()).hexdigest()
            row["w21_md5"] = w21_mat[rel]
            if w21_mat[rel] and md5 != w21_mat[rel]:
                w21_md5_bad.append(rel)
        assets.append(row)

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
    independence = layer_independence()
    for lyr in layers:
        row = next(r for r in independence if r["name"] == lyr["name"])
        lyr["source_family"] = row["source_family"]
        lyr["independent"] = row["independent"]
        lyr["mark"] = row["mark"]

    # --- W0..W18 の出力ダイジェスト(最終 build_hash は build.run が全段階で組む)---
    stage_digests: list[dict[str, Any]] = []
    digests: list[str] = []
    for path in C.stage_header_paths(ctx.out):
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
        "layer_independence": independence,
        "stage_digests": stage_digests,
        "partial_build_hash_w0_w18": partial,
    }

    params: dict[str, Any] = {
        "seal_scheme": SEAL_SCHEME,
        "sealed_utc": SEALED_UTC,
        "holdout_layers": {name: list(members) for name, members in HOLDOUT_LAYERS},
        "source_families": dict(SOURCE_FAMILIES),
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
                        "source_family": lyr["source_family"],
                        "independent": lyr["independent"],
                        "mark": lyr["mark"],
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
    if w21_mat:  # 〔段 10〕差し替えの世界だけ(本体の v2 の門の表は今のまま)
        res.gates.append(C.Gate("w21_materials", len(w21_mat), None))
        res.gates.append(C.Gate("w21_material_md5_mismatch", len(w21_md5_bad), 0))
        res.notes["w21_materials"] = {"count": len(w21_mat), "md5_mismatch": w21_md5_bad,
                                      "manifests": [m for m in W21_MANIFESTS if (ctx.out / m).exists()]}
    return res
