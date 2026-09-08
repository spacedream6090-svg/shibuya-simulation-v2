"""W18 カタログ写像・世界被覆指標(§1 W18・D-W19)。

方法論「世界被覆指標」の定義をそのまま実装する。

  重み  w_i = 1 + log10(1 + N_real,i)(上限 6)。N_real 不明は w=1(expedient)。
  深度  d_i ∈ {0..4}。**構築時は「宣言値」**=凍結カタログの「初回後d」列を実装済みクラスに当てる
        (実測ではない=expedient。ランタイムの計器盤が実測へ置き換える)。
  門    gate_i = カタログ「gate」列が ✔ で始まる行。計上対象 G={i: gate_i}。
  C     = Σ_{G, d≥1} w / Σ_{WC} w         (分母=凍結カタログ全体 57 クラス)
  C_q   = 同上を「数量が突合できるクラス」に限ったもの
  Q     = Σ w·min(1, N_sim/N_real) / Σ_{WC} w   (上振れは加点しない)
  D     = Σ_G w·d / (4 Σ_{WC} w)
  V     = Σ_{G, VERIFIED} w / Σ_{WC} w    (構築時は VERIFIED=false 固定 → V=0)
  R     = 到達率。**ランタイムの実測**なので構築時は null。
  X     = Σ w·max(0, N_sim/N_real − 1) / Σ w(+ 死蔵候補クラス数=別欄)
  孤児  = reaches 宣言あり ∧ 実読0。構築時は実読が無いので空。

**単位の突合(mechanism ではなく手書き)**: カタログの「現実数量」欄は自由文で、
先頭の数がクラスの員数とは限らない(例: 駅・出口=「6事業者/出口=未取得」の 6、
騒音場=「ASJ RTN+5点」の 5)。単位が一致しない行は ``quantity_comparable=false`` にして
Q と X から外し、理由を per_class に残す。**数を合わせにいく調整はしない**。

出力
  ``wc_index.json``          5値ベクトル+X+死蔵候補+孤児+per_class
  ``wc_reverse_index.json``  逆引き表 stub(クラス → それを埋める段階)
"""

from __future__ import annotations

import math
import re
from typing import Any

from shibuya.manifest.world_catalog import (
    FROZEN_N_CLASSES,
    FROZEN_SHA16,
    load_world_catalog,
    verify_frozen,
)

from ..geo import common as C

STAGE = "W18"
STAGE_VERSION = "1.0.0"

#: 重みの上限(方法論)。
W_CAP = 6.0
#: 深度の最大値。
D_MAX = 4

#: 段階ヘッダの ``catalog_classes`` の表記ゆれ → 凍結カタログのクラス名(手書き・expedient)。
#: ここに無い宣言は ``unmapped_declarations`` として報告する(黙って捨てない)。
CLASS_ALIASES: dict[str, str] = {
    "街路面(可視・可聴の台)": "街路(歩行グラフ)",
    "道路交通騒音場": "騒音場",
    "環境音(静的)": "騒音場",
    "計画仕様(PlanSpec)": "ダイヤ・営業時間・価格表(PlanSpec)",
    "営業時間": "ダイヤ・営業時間・価格表(PlanSpec)",
    "価格帯": "ダイヤ・営業時間・価格表(PlanSpec)",
    "鉄道運行(計画データ)": "鉄道運行(静的→運行連動)",
    "気象(日次・時別)": "天候・気温(+生成器)",
    "日照・昼夜": "昼夜・日照・影",
}

#: クラス → (段階, 出力ファイル, その行数を N_sim とみなすか) の対応(手書き・expedient)。
#: ``comparable`` が False の行は Q/X から外す(カタログの「現実数量」と単位が違う)。
QUANTITY_MAP: dict[str, dict[str, Any]] = {
    "建物": {"stage": "W4", "output": "w4_buildings.parquet", "comparable": True,
             "unit": "棟(OSM building)"},
    "街路(歩行グラフ)": {"stage": "W1", "output": "w1_edges.parquet", "comparable": True,
                          "unit": "エッジ"},
    "街区": {"stage": "W2", "output": "w2_blocks.parquet", "comparable": True, "unit": "街区面"},
    "セル(場所100m+層)": {"stage": "W2", "output": "w2_cells.parquet", "comparable": True,
                              "unit": "セル(GL+DECK+UG)",
                              "note": "カタログの 453 は GL のみ。本実装の GL も 453 で、"
                                      "上振れ分 67 は DECK 39 + UG 28(層の追加)。"},
    "POI/店舗": {"stage": "W6", "output": "w6_poi.parquet", "comparable": True, "unit": "POI"},
    "事業所(組織)": {"stage": "W6", "output": "w6_org.parquet", "comparable": True,
                       "unit": "事業所",
                       "note": "カタログの 27,624 は渋谷区全域・本実装は 13町丁目(=世界範囲)の 9,872。"
                               "bbox 定義差(方法論の expedient)で Q<1 になるのは想定内。"},
    "駅・出口": {"stage": "W11", "output": "w11_station_exits.parquet", "comparable": False,
                 "unit": "出口",
                 "note": "カタログの先頭数 6 は**事業者数**で出口数は「未取得」。単位不一致で Q/X から外す。"},
    "ダイヤ・営業時間・価格表(PlanSpec)": {"stage": "W7", "output": "w7_plan_spec.parquet",
                                            "comparable": True, "unit": "PlanSpec 行"},
    "騒音場": {"stage": "W10", "output": "w10_street_points.parquet", "comparable": False,
               "unit": "街路格子点",
               "note": "カタログの先頭数 5 は**較正点数**。場の員数ではないので Q/X から外す。"},
    "鉄道運行(静的→運行連動)": {"stage": "W12", "output": "w12_timetables.parquet",
                                  "comparable": False, "unit": "発車行",
                                  "note": "カタログ現実数量が「ODPT」= 数値なし。"},
    "天候・気温(+生成器)": {"stage": "W13", "output": "w13_weather_days.parquet",
                              "comparable": True, "unit": "再生候補日"},
    "地形(起伏)": {"stage": "W8", "output": "w8_t1.parquet", "comparable": False,
                    "unit": "可視性テーブルの視点数",
                    "note": "カタログの先頭数 2 は DEM の解像度 2m。単位不一致で Q/X から外す。"},
    "昼夜・日照・影": {"stage": "W9", "output": "w9_shadow_planes.parquet", "comparable": False,
                       "unit": "影の面数/日", "note": "カタログ現実数量が「天文計算」= 数値なし。"},
}

_NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)")
_INT = re.compile(r"(\d+)")


def parse_n_real(text: str) -> float | None:
    """カタログ「現実数量」欄 → 先頭の数(桁区切りのカンマを外す)。数が無ければ None。"""
    m = _NUM.search(text or "")
    if m is None:
        return None
    return float(m.group(1).replace(",", ""))


def parse_depth(text: str) -> int:
    """カタログ「初回後d」欄 → 深度。``**0**`` や ``2(…)`` のような装飾を剥がす。"""
    m = _INT.search((text or "").replace("*", ""))
    return int(m.group(1)) if m else 0


def parse_gate(text: str) -> bool:
    """カタログ「gate」欄 → 憲法5の門を通ったか(``✔`` で始まる行)。"""
    return (text or "").strip().startswith("✔")


def weight(n_real: float | None) -> float:
    """w = 1 + log10(1 + N_real)(上限 6)。N_real 不明は 1(expedient)。"""
    if n_real is None or n_real <= 0:
        return 1.0
    return min(W_CAP, 1.0 + math.log10(1.0 + n_real))


def compute_index(
    rows: list[dict[str, str]],
    implemented: dict[str, list[str]],
    n_sim: dict[str, float | None],
    comparable: dict[str, bool],
) -> dict[str, Any]:
    """凍結カタログ行 + 実装状況 → 被覆指標(純関数・テストの入口)。"""
    per_class: list[dict[str, Any]] = []
    w_all = 0.0
    num_c = 0.0
    num_cq = 0.0
    num_q = 0.0
    num_d = 0.0
    num_v = 0.0
    num_x = 0.0
    dead_stock: list[str] = []
    for row in rows:
        name = row["クラス"]
        n_real = parse_n_real(row.get("現実数量(bbox/区)", ""))
        w = weight(n_real)
        gate = parse_gate(row.get("gate", ""))
        stages = implemented.get(name, [])
        impl = bool(stages)
        depth = parse_depth(row.get("初回後d", "")) if impl else 0
        sim = n_sim.get(name)
        cmpb = bool(comparable.get(name, False)) and sim is not None and n_real not in (None, 0)
        verified = False  # 構築時はアンカー照合をしない
        w_all += w
        if gate:
            num_d += w * depth
            if depth >= 1:
                num_c += w
                if cmpb:
                    num_cq += w
            if verified:
                num_v += w
        if cmpb:
            ratio = sim / n_real
            num_q += w * min(1.0, ratio)
            num_x += w * max(0.0, ratio - 1.0)
        if impl and n_real is None and not verified:
            dead_stock.append(name)
        per_class.append(
            {
                "n": int(row["#"]),
                "type": row["型"],
                "class": name,
                "n_real": n_real,
                "n_real_raw": row.get("現実数量(bbox/区)", ""),
                "n_sim": sim,
                "quantity_comparable": cmpb,
                "weight": round(w, 6),
                "depth": depth,
                "gate": gate,
                "implemented": impl,
                "stages": stages,
                "verified": verified,
                "reach": None,
            }
        )
    vector = {
        "C": round(num_c / w_all, 6),
        "C_quantified": round(num_cq / w_all, 6),
        "Q": round(num_q / w_all, 6),
        "D": round(num_d / (D_MAX * w_all), 6),
        "V": round(num_v / w_all, 6),
        "R": None,
    }
    return {
        "vector": vector,
        "X": round(num_x / w_all, 6),
        "dead_stock_candidates": sorted(dead_stock),
        "orphans": [],
        "weight_total": round(w_all, 6),
        "per_class": per_class,
    }


def run(ctx: C.Ctx) -> C.StageResult:
    cat = load_world_catalog()
    verify_frozen(cat)

    # --- 各段階ヘッダの catalog_classes を集める(自分より前の段階のみ)---
    headers: dict[str, dict[str, Any]] = {}
    header_paths: list[Any] = []
    for path in sorted(ctx.out.glob("W*.header.json"), key=lambda p: int(p.stem.split(".")[0][1:])):
        h = C.load_json(path)
        if int(h["stage"][1:]) < int(STAGE[1:]):
            headers[h["stage"]] = h
            header_paths.append(path)
    known = {row["クラス"] for row in cat.rows}
    implemented: dict[str, list[str]] = {}
    unmapped: dict[str, list[str]] = {}
    for stage in sorted(headers, key=lambda s: int(s[1:])):
        for declared in headers[stage]["catalog_classes"]:
            name = CLASS_ALIASES.get(declared, declared)
            if name in known:
                got = implemented.setdefault(name, [])
                if stage not in got:
                    got.append(stage)
            else:
                unmapped.setdefault(declared, []).append(stage)

    # --- N_sim(段階出力の行数)---
    n_sim: dict[str, float | None] = {}
    comparable: dict[str, bool] = {}
    quantity_missing: list[str] = []
    for name, spec in QUANTITY_MAP.items():
        rows_n: float | None = None
        h = headers.get(spec["stage"])
        if h is not None:
            for o in h["outputs"]:
                if o["path"] == spec["output"] and o["rows"] is not None:
                    rows_n = float(o["rows"])
        if rows_n is None:
            quantity_missing.append(name)
        n_sim[name] = rows_n
        comparable[name] = bool(spec["comparable"])

    index = compute_index(list(cat.rows), implemented, n_sim, comparable)
    index_doc = {
        "schema": "shibuya.build.audit/wc_index/1",
        "catalog_version": cat.version,
        "catalog_sha16": cat.sha16,
        "n_classes": cat.n_classes,
        "reach_note": "R(到達率)と孤児はランタイムの実読が要る。構築時は null / 空。",
        "depth_note": "深度は凍結カタログ「初回後d」の宣言値(実測ではない=expedient)。",
        **index,
    }
    reverse = {
        "schema": "shibuya.build.audit/wc_reverse_index/1",
        "catalog_sha16": cat.sha16,
        "note": (
            "クラス → それを埋める構築段階。パターン台帳側の逆引き"
            "(パターン行 → 支える世界クラス)はランタイム/手動の未決欄。"
        ),
        "class_to_stages": {row["クラス"]: implemented.get(row["クラス"], []) for row in cat.rows},
        "unmapped_declarations": {k: sorted(set(v)) for k, v in sorted(unmapped.items())},
    }

    n_impl = sum(1 for c in index["per_class"] if c["implemented"])
    n_gate = sum(1 for c in index["per_class"] if c["gate"])
    params: dict[str, Any] = {
        "w_cap": W_CAP,
        "d_max": D_MAX,
        "class_aliases": dict(sorted(CLASS_ALIASES.items())),
        "quantity_map": {k: dict(sorted(v.items())) for k, v in sorted(QUANTITY_MAP.items())},
        "verified_at_build": False,
        "reach_at_build": None,
    }
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(header_paths),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=[],
        expedients=[
            "深度=カタログ宣言値(実測ではない)",
            "重み関数 w=1+log10(1+N_real) 上限6・N_real 不明は w=1",
            "クラス名の別名表(段階ヘッダの表記ゆれ吸収)は手書き",
            "N_sim の単位突合(quantity_comparable)は手書き",
            "VERIFIED は構築時に評価しない(全 false)",
        ],
        notes={
            "stages_scanned": sorted(headers, key=lambda s: int(s[1:])),
            "classes_total": cat.n_classes,
            "classes_implemented": n_impl,
            "classes_gated": n_gate,
            "classes_with_quantity": sum(
                1 for c in index["per_class"] if c["quantity_comparable"]
            ),
            "quantity_map_without_rows": sorted(quantity_missing),
            "unmapped_declarations": {k: sorted(set(v)) for k, v in sorted(unmapped.items())},
            "vector": index["vector"],
            "X": index["X"],
            "dead_stock_candidates": index["dead_stock_candidates"],
        },
    )
    res.outputs.append(C.write_json(ctx.out, "wc_index.json", index_doc, rows=cat.n_classes))
    res.outputs.append(C.write_json(ctx.out, "wc_reverse_index.json", reverse, rows=cat.n_classes))
    res.gates = [
        C.Gate("catalog_sha16_frozen", cat.sha16, FROZEN_SHA16),
        C.Gate("catalog_n_classes", cat.n_classes, FROZEN_N_CLASSES),
        C.Gate("classes_implemented", n_impl, None),
        C.Gate("wc1_world_coverage_C", index["vector"]["C"], None),
        C.Gate("wc1_world_coverage_C_quantified", index["vector"]["C_quantified"], None),
        C.Gate("wc2_world_quantity_fit_Q", index["vector"]["Q"], None),
        C.Gate("wc3_world_depth_D", index["vector"]["D"], None),
        C.Gate("wc4_world_verified_ratio_V", index["vector"]["V"], None),
        C.Gate("wc5_world_commission_X", index["X"], None),
        C.Gate("wc6_world_orphans", len(index["orphans"]), 0),
        C.Gate("unmapped_class_declarations", len(unmapped), None),
    ]
    return res
