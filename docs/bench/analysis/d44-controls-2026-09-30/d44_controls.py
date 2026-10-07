# -*- coding: utf-8 -*-
"""d44_controls.py — D-44 の構築段階の対照(i)と mock の対照(ii)の実行器(第311・2026-09-30)。

ユーザーの許可(指示書 v2-wallbounce-decisions-2026-09-30 §6 D-44)
    (i) 66 行を段ごとの束で回す・(iii) 17 行に「対照を定義できない」の印・(ii) 13 行は mock の
    CSB 対照・読まない 9 行は「ランに届かない」と登録。

やり方(**src は変えない**・昇格済みの世界資産は上書きしない)
    1. ``base``: 構築段 W0-W13・W8・W9・W16 を**リポの外のスクラッチ**へ再構築し、全出力の sha256 が
       ``data/world/v2/build_manifest.json`` と一致することを確かめる(=計器の 0 点)。
    2. ``one <行>``: 基準の複製(スクラッチ)に対照を当てる。当て方は 3 つ:
       (a) 構築モジュールの定数・関数を**このプロセスの中だけ**差し替えて段を再実行(monkeypatch)
       (b) 上流の出力を対照の値で書き換えて下流の段を再実行
       (c) 出力から直接、対照の分布を計算(再実行の要らない行)
       行ごとに 1 サブプロセス(差し替えが他の行へ漏れない)。
    3. 判定=既存の台帳の片側規則(``tools/c8/c8lib.compare_counts``): 宣言 vs 対照の入力側 JSD が
       帰無参照(同分布 2 標本の JSD 95% 点・多項リサンプリング)以内なら「駆動しえない」、超えたら
       「ラン対照へ」。**第200 の床**: 2 seed の感度試験は f≈1 未満を検出できない。
    4. ``mock``: (ii) のうち既存の口(``--world``)で測れる行を mock 5,000 体で回す。

**実装役の自前の構成=未リサーチ**: 対照のずらし値(±50 m・±10%・±5 歳・+6 m・500 m・5 m ピッチ・
1.25 m ラスタ・600 m・夜の配分 1.5×/0.75× など)・距離の階級幅(10 m)・指標の選び方(どの出力の
どの分布を比べるか)・大気差の式(NOAA 太陽位置計算表の式を記憶から書いた=一次未確認)。

例::

    python docs/bench/analysis/d44-controls-2026-09-30/d44_controls.py base
    python docs/bench/analysis/d44-controls-2026-09-30/d44_controls.py selfcheck
    python docs/bench/analysis/d44-controls-2026-09-30/d44_controls.py stage W7
    python docs/bench/analysis/d44-controls-2026-09-30/d44_controls.py all
    python docs/bench/analysis/d44-controls-2026-09-30/d44_controls.py mock
    python docs/bench/analysis/d44-controls-2026-09-30/d44_controls.py collect

スクラッチの場所は ``--scratch`` か環境変数 ``D44_SCRATCH``(既定 = OS の一時ディレクトリの
``shibuya_d44_scratch``)。**リポの中は拒否**する。記録には絶対パスを書かない。
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DATA = REPO / "data"
WORLD = DATA / "world" / "v2"
RESULTS = HERE / "results"
sys.path.insert(0, str(REPO / "tools" / "c8"))

import c8lib  # noqa: E402

#: 基準に再構築する段(W14/W15=LLM 文・W17=LLM 週次表・W18-W20=検査と画像は再構築しない)。
BASE_STAGES: tuple[str, ...] = (
    "W0", "W1", "W2", "W3", "W4", "W5", "W6", "W7", "W10", "W11", "W12", "W13", "W8", "W9", "W16",
)
#: 距離の階級幅[m](**未リサーチ**: 1 tick=1 分の歩行 ≈80 m より細かい幅として置いた)。
DIST_BIN_M: float = 10.0
UNRESEARCHED_COMMON = (
    "対照のずらし値・指標(どの出力のどの分布を比べるか)・階級幅は実装役の自前の構成=未リサーチ"
)


# ======================================================================== 共通
def scratch_root(arg: str | None = None) -> Path:
    p = Path(arg or os.environ.get("D44_SCRATCH") or (Path(tempfile.gettempdir()) / "shibuya_d44_scratch"))
    p = p.resolve()
    if p == REPO or REPO in p.parents:
        raise SystemExit(f"スクラッチがリポの中にある(拒否): {p.name}")
    return p


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_stages(out: Path, stages: Sequence[str], data: Path = DATA) -> float:
    """段を ``out`` で走らせる(``shibuya.build.run.run_all`` と同じ依存順)。壁時計[秒]を返す。"""
    from shibuya.build import run as BR
    from shibuya.build.geo import common as C

    ctx = C.Ctx(data=Path(data), out=Path(out))
    t0 = time.perf_counter()
    BR.run_all(ctx, list(stages), verbose=False)
    return time.perf_counter() - t0


class Env:
    """スクラッチ(基準・対照の作業場所)。"""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.base = root / "base"

    def new_ctl(self, key: str) -> Path:
        d = self.root / "ctl" / key.replace("#", "_")
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(self.base, d)
        return d

    def drop(self, d: Path) -> None:
        if d.exists() and self.root in d.resolve().parents:
            shutil.rmtree(d, ignore_errors=True)


def changed_outputs(base: Path, ctl: Path) -> list[str]:
    """基準と対照で中身が違う出力ファイル(ヘッダ・manifest を除く・名前だけ)。"""
    out: list[str] = []
    for p in sorted(ctl.iterdir()):
        if not p.is_file() or p.name.endswith(".header.json") or p.name.startswith("build_manifest"):
            continue
        q = base / p.name
        if not q.exists() or sha256_file(p) != sha256_file(q):
            out.append(p.name)
    return out


def variant(name: str, res: Mapping[str, Any], **extra: Any) -> dict[str, Any]:
    keep = ("jsd_bits", "null_p95", "detected", "tvd", "n_declared", "n_control", "n_bins")
    return {"name": name, **{k: res[k] for k in keep}, **extra}


def cmp(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    return c8lib.compare_counts(np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64))


def cmp_counter(a: Mapping[Any, float], b: Mapping[Any, float]) -> dict[str, Any]:
    keys = sorted(set(a) | set(b), key=lambda k: str(k))
    return cmp([float(a.get(k, 0.0)) for k in keys], [float(b.get(k, 0.0)) for k in keys])


def hist_pair(va: np.ndarray, vb: np.ndarray, width: float) -> tuple[np.ndarray, np.ndarray]:
    ia = np.floor(np.asarray(va, dtype=np.float64) / width).astype(np.int64)
    ib = np.floor(np.asarray(vb, dtype=np.float64) / width).astype(np.int64)
    lo = int(min(ia.min(initial=0), ib.min(initial=0)))
    hi = int(max(ia.max(initial=0), ib.max(initial=0)))
    return (np.bincount(ia - lo, minlength=hi - lo + 1).astype(np.float64),
            np.bincount(ib - lo, minlength=hi - lo + 1).astype(np.float64))


def read_cols(path: Path, cols: Sequence[str] | None = None) -> dict[str, list]:
    import pyarrow.parquet as pq

    t = pq.read_table(path, columns=list(cols) if cols else None)
    return {n: t.column(n).to_pylist() for n in t.column_names}


def cell_index(d: Path) -> dict[str, int]:
    return {p: i for i, p in enumerate(read_cols(d / "w2_cells.parquet", ["place_id"])["place_id"])}


def point_cells(x: Sequence[float], y: Sequence[float], band: Sequence[str], cidx: Mapping[str, int]) -> np.ndarray:
    """点 → w2_cells の行(無ければ len(cidx)=「セル表に無い」の階級)。"""
    ix = np.floor(np.asarray(x, dtype=np.float64) / 100.0).astype(np.int64)
    iy = np.floor(np.asarray(y, dtype=np.float64) / 100.0).astype(np.int64)
    miss = len(cidx)
    out = np.empty(ix.size, dtype=np.int64)
    for k in range(ix.size):  # 逐次: 点数ぶん(ツール側)
        out[k] = cidx.get(f"g{ix[k]}_{iy[k]}_{band[k]}", miss)
    return out


class Patch:
    """属性の差し替え(このプロセスの中だけ・戻せる)。"""

    def __init__(self) -> None:
        self._undo: list[tuple[Any, str, Any]] = []

    def set(self, obj: Any, name: str, value: Any) -> None:
        self._undo.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def undo(self) -> None:
        while self._undo:
            obj, name, value = self._undo.pop()
            setattr(obj, name, value)


def result(key: str, control: str, metric: str, variants: list[dict[str, Any]], **kw: Any) -> dict[str, Any]:
    det = any(v["detected"] for v in variants if v.get("primary", True))
    return {
        "key": key, "control": control, "metric": metric, "variants": variants,
        "detected": bool(det), "status": "measured",
        "verdict": c8lib.verdict_from_stage(det), **kw,
    }


def unmeasurable(key: str, control: str, reason: str, **kw: Any) -> dict[str, Any]:
    return {"key": key, "control": control, "status": "unmeasurable", "verdict": None,
            "reason": reason, "variants": [], **kw}


# ======================================================================== 指標
def dist_upper(d: Path) -> np.ndarray:
    m = np.load(d / "w3_cell_dist.npy")
    iu = np.triu_indices(m.shape[0], 1)
    return m[iu].astype(np.float64)


def w7_weeks(d: Path) -> tuple[list[str], list[list[list[tuple[int, int]]]], list[str], list[str]]:
    c = read_cols(d / "w7_plan_spec.parquet", ["poi_id", "content", "law_cap_key", "src"])
    weeks = [[[(int(o), int(cc)) for o, cc in day] for day in json.loads(s)] for s in c["content"]]
    return c["poi_id"], weeks, c["law_cap_key"], c["src"]


def open_hours_vector(weeks: Sequence[Sequence[Sequence[tuple[int, int]]]]) -> np.ndarray:
    """週表の列 → 168 時 × {営業中, 休業} の POI・時(営業分 ÷ 60)。日跨ぎは週で巻く。"""
    total = np.zeros(10080, dtype=np.float64)
    for week in weeks:  # 逐次: POI 数ぶん(ツール側)
        m = np.zeros(10080, dtype=bool)
        for d, day in enumerate(week):
            for o, c in day:
                a, b = d * 1440 + int(o), d * 1440 + int(c)
                if b <= 10080:
                    m[a:b] = True
                else:
                    m[a:] = True
                    m[: b - 10080] = True
        total += m
    open_h = total.reshape(168, 60).sum(axis=1) / 60.0
    return np.concatenate([open_h, float(len(weeks)) - open_h])


def day_vector(weeks: Sequence[Sequence[Sequence[tuple[int, int]]]], dow: int) -> np.ndarray:
    """ある曜日 1 日の 24 時 × {営業中, 休業}(翌日へはみ出す分は落とす=その日の中だけ)。"""
    total = np.zeros(1440, dtype=np.float64)
    for week in weeks:
        m = np.zeros(1440, dtype=bool)
        for o, c in week[dow]:
            m[int(o): min(int(c), 1440)] = True
        total += m
    open_h = total.reshape(24, 60).sum(axis=1) / 60.0
    return np.concatenate([open_h, float(len(weeks)) - open_h])


def w8_pairs(d: Path) -> tuple[np.ndarray, np.ndarray]:
    c = read_cols(d / "w8_t1_cell.parquet", ["place_idx", "target_id", "n_viewpoints"])
    key = np.asarray(c["place_idx"], dtype=np.int64) * 1_000_000 + np.asarray(c["target_id"], dtype=np.int64)
    return key, np.asarray(c["n_viewpoints"], dtype=np.float64)


def cmp_pairs(a: tuple[np.ndarray, np.ndarray], b: tuple[np.ndarray, np.ndarray]) -> dict[str, Any]:
    keys = np.union1d(a[0], b[0])
    va = np.zeros(keys.size)
    vb = np.zeros(keys.size)
    va[np.searchsorted(keys, a[0])] = a[1]
    vb[np.searchsorted(keys, b[0])] = b[1]
    res = cmp(va, vb)
    sa, sb = set(a[0].tolist()), set(b[0].tolist())
    res["jaccard_pairs"] = len(sa & sb) / max(1, len(sa | sb))
    return res


def w8_nvisible(d: Path) -> np.ndarray:
    return np.asarray(read_cols(d / "w8_t1.parquet", ["n_visible"])["n_visible"], dtype=np.int64)


def w9_joint(d: Path, cells: np.ndarray, n_cells: int) -> np.ndarray:
    """影の面 → (セル × 時 × {日陰, 日向}) の点・面の数。"""
    # 出力名は再生日つき(w9_shadow_<日付>.npy)。対照の場所には基準の複製も残るので、**その場所の W9 ヘッダ**が
    # 指す出力を読む(glob の先頭を読むと再生日を変えた対照で基準の面を読んでしまう=第311 の検算で発見)。
    h = json.loads((d / "W9.header.json").read_text(encoding="utf-8"))
    f = d / next(o["path"] for o in h["outputs"] if str(o["path"]).startswith("w9_shadow_") and str(o["path"]).endswith(".npy"))
    planes = np.load(f)
    n = cells.size
    acc = np.zeros((n_cells + 1) * 24 * 2, dtype=np.float64)
    for p in range(planes.shape[0]):  # 逐次: 288 面
        bits = np.unpackbits(planes[p])[:n].astype(np.int64)
        idx = (cells * 24 + p // 12) * 2 + bits
        acc += np.bincount(idx, minlength=acc.size)
    return acc


def w10_joint(d: Path) -> np.ndarray:
    """騒音段階 → (セル × {昼, 夜} × 段階 4) の点の数。"""
    pts = read_cols(d / "w10_street_points.parquet", ["x", "y", "band"])
    cidx = cell_index(d)
    cells = point_cells(pts["x"], pts["y"], pts["band"], cidx)
    day = np.load(d / "w10_noise_stage_day.npy").astype(np.int64)
    night = np.load(d / "w10_noise_stage_night.npy").astype(np.int64)
    size = (len(cidx) + 1) * 2 * 4
    return (np.bincount((cells * 2 + 0) * 4 + day, minlength=size)
            + np.bincount((cells * 2 + 1) * 4 + night, minlength=size)).astype(np.float64)


def heat_counts(d: Path) -> Counter:
    return Counter(read_cols(d / "w13_weather_hourly.parquet", ["heat_stage"])["heat_stage"])


# ======================================================================== W1-W3
def c_w1_2(E: Env) -> dict[str, Any]:
    import shibuya.build.geo.w1_walk_graph as W1

    d = E.new_ctl("W1#2")
    P = Patch()
    P.set(W1, "prune_pendants", lambda n, edges: (set(range(n)), set(range(len(edges)))))
    t = run_stages(d, ["W1", "W2", "W3"])
    P.undo()
    a, b = hist_pair(dist_upper(E.base), dist_upper(d), DIST_BIN_M)
    r = result("W1#2", "pendant 除去あり(宣言)vs 除去なし(pendant 列を全 False)",
               "W3 セル間距離(上三角)の 10 m 階級分布",
               [variant("除去なし", cmp(a, b))], seconds_stage=t, outputs_changed=changed_outputs(E.base, d),
               notes=["pendant 列を読むコードは src に無い(grep: w1_walk_graph.py の中だけ)"])
    E.drop(d)
    return r


def _exact_only(fg_buildings: list[dict], osm_buildings: list[dict]) -> dict[str, str | None]:
    by_name: dict[str, str] = {}
    for b in osm_buildings:
        nm = (b.get("name") or "").strip()
        if nm and nm not in by_name:
            by_name[nm] = b["id"]
    out: dict[str, str | None] = {}
    for fb in fg_buildings:
        hit = next((by_name[a] for a in fb["match"] if a in by_name), None)
        out[fb["match"][0]] = hit
    return out


def _fg_categories(d: Path) -> Counter:
    c = read_cols(d / "w1_floorguide_links.parquet", ["a_building_id", "b_building_id"])
    return Counter(f"a{'o' if a else 'x'}_b{'o' if b else 'x'}" for a, b in zip(c["a_building_id"], c["b_building_id"]))


def _w11_degree(d: Path) -> Counter:
    c = read_cols(d / "w11_station_graph_edges.parquet", ["from_node", "to_node"])
    deg = Counter(c["from_node"]) + Counter(c["to_node"])
    return Counter(deg.values())


def c_w1_3(E: Env) -> dict[str, Any]:
    import shibuya.build.geo.w1_walk_graph as W1

    d = E.new_ctl("W1#3")
    P = Patch()
    P.set(W1, "_match_floorguide", _exact_only)
    t = run_stages(d, ["W1", "W11"])
    P.undo()
    fa, fb = _fg_categories(E.base), _fg_categories(d)
    r = result("W1#3", "完全一致→部分一致(宣言)vs 完全一致だけ", "floorguide 22 本の結線の状態(両端/片端/無し)と W11 構内グラフの次数分布",
               [variant("floorguide 結線の状態", cmp_counter(fa, fb), declared=dict(fa), control=dict(fb)),
                variant("W11 構内グラフの次数", cmp_counter(_w11_degree(E.base), _w11_degree(d)))],
               seconds_stage=t, outputs_changed=changed_outputs(E.base, d))
    E.drop(d)
    return r


def _node_places(d: Path) -> list[str]:
    nd = read_cols(d / "w1_nodes.parquet", ["x", "y", "band"])
    return [f"g{math.floor(x / 100.0)}_{math.floor(y / 100.0)}_{b}" for x, y, b in zip(nd["x"], nd["y"], nd["band"])]


def c_w2_2(E: Env) -> dict[str, Any]:
    t0 = time.perf_counter()
    places = _node_places(E.base)
    ed = read_cols(E.base / "w1_edges.parquet", ["u_idx", "v_idx"])
    cells = read_cols(E.base / "w2_cells.parquet", ["place_id", "n_edges"])
    idx = {p: i for i, p in enumerate(cells["place_id"])}
    dec = np.zeros(len(idx))
    ctl = np.zeros(len(idx))
    for u, v in zip(ed["u_idx"], ed["v_idx"]):  # 逐次: 辺数ぶん
        a, b = idx[places[u]], idx[places[v]]
        dec[a] += 1
        if a == b:
            ctl[a] += 1
        else:
            dec[b] += 1
            ctl[a] += 0.5
            ctl[b] += 0.5
    ok = bool(np.array_equal(dec, np.asarray(cells["n_edges"], dtype=np.float64)))
    return result("W2#2", "端点の一方でも数える(宣言・重複計上)vs 両端点で按分(0.5 ずつ)", "セルの n_edges の分布(セル上の重み)",
                  [variant("両端点で按分", cmp(dec, ctl))], seconds_stage=time.perf_counter() - t0,
                  checks={"declared_recomputed_equals_asset": ok})


def c_w2_3(E: Env) -> dict[str, Any]:
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = E.new_ctl("W2#3")
    places = _node_places(E.base)
    nd = read_cols(E.base / "w1_nodes.parquet", ["node_id", "degree"])
    tab = pq.read_table(E.base / "w2_cells.parquet")
    pids = tab.column("place_id").to_pylist()
    best: dict[str, int] = {}
    for i, p in enumerate(places):  # 逐次: ノード数ぶん
        j = best.get(p)
        if j is None or nd["degree"][i] > nd["degree"][j]:
            best[p] = i
    rep = [best[p] for p in pids]
    tab = tab.set_column(tab.column_names.index("rep_node_idx"), "rep_node_idx", pa.array(rep, type=pa.int32()))
    tab = tab.set_column(tab.column_names.index("rep_node_id"), "rep_node_id", pa.array([nd["node_id"][i] for i in rep]))
    pq.write_table(tab, d / "w2_cells.parquet")
    t = run_stages(d, ["W3"])
    a, b = hist_pair(dist_upper(E.base), dist_upper(d), DIST_BIN_M)
    n_diff = int(sum(1 for p, r0 in zip(pids, read_cols(E.base / "w2_cells.parquet", ["rep_node_idx"])["rep_node_idx"]) if best[p] != r0))
    da, db = dist_upper(E.base), dist_upper(d)
    r = result("W2#3", "重心に最近のノード(宣言)vs セル内の最大次数ノード(同点は添字最小)", "W3 セル間距離(上三角)の 10 m 階級分布",
               [variant("最大次数ノード", cmp(a, b), mean_abs_diff_m=float(np.abs(da - db).mean()),
                        share_pairs_abs_diff_ge_10m=float((np.abs(da - db) >= 10.0).mean()))],
               seconds_stage=t, rep_changed_cells=n_diff,
               notes=["分布の JSD は対ごとの入れ替えを見ない(対ごとの差は mean_abs_diff_m・share_pairs_abs_diff_ge_10m に記録)"])
    E.drop(d)
    return r


def c_w2_4(E: Env) -> dict[str, Any]:
    t0 = time.perf_counter()
    bl = read_cols(E.base / "w2_blocks.parquet", ["place_id", "place_ids"])
    dec: Counter = Counter()
    ctl: Counter = Counter()
    for pid, pids in zip(bl["place_id"], bl["place_ids"]):
        for p in pids:
            dec[p] += 1
        ctl[pid] += 1
    return result("W2#4", "外周 GL ノードのセル集合(宣言)vs 街区重心のセル(1 街区 1 セル)", "街区×セルの所属のセル上の分布",
                  [variant("街区重心のセル", cmp_counter(dec, ctl))], seconds_stage=time.perf_counter() - t0)


def _w3_full(E: Env) -> dict[str, Any]:
    """全ノード対の最短距離(ツール側で W3 の Dijkstra を回す)。"""
    import shibuya.build.geo.w3_distances as W3

    nd = read_cols(E.base / "w1_nodes.parquet", ["node_idx"])
    ed = read_cols(E.base / "w1_edges.parquet", ["u_idx", "v_idx", "length_m"])
    cd = read_cols(E.base / "w2_cells.parquet", ["place_id", "rep_node_idx"])
    n = len(nd["node_idx"])
    indptr, indices, weights = W3.build_csr(n, np.asarray(ed["u_idx"]), np.asarray(ed["v_idx"]),
                                            np.asarray(ed["length_m"], dtype=np.float64))
    _nh, dist = W3._all_pairs(indptr, indices, weights, np.arange(n, dtype=np.int64), n)
    reps = np.asarray(cd["rep_node_idx"], dtype=np.int64)
    return {"dist": dist, "reps": reps, "place_ids": cd["place_id"]}


def c_w3(E: Env) -> list[dict[str, Any]]:
    t0 = time.perf_counter()
    F = _w3_full(E)
    dist, reps = F["dist"], F["reps"]
    sub = dist[np.ix_(reps, reps)]
    sym = np.minimum(sub, sub.T)
    declared = np.load(E.base / "w3_cell_dist.npy")
    recomputed = np.minimum(np.rint(sym), 65534).astype(np.uint16)
    ok = bool(np.array_equal(recomputed, declared))
    n = reps.size
    iu = np.triu_indices(n, 1)
    t_common = time.perf_counter() - t0
    out: list[dict[str, Any]] = []
    # W3#1: セル内ノード対の中央値
    t1 = time.perf_counter()
    places = _node_places(E.base)
    idx = {p: i for i, p in enumerate(F["place_ids"])}
    members: list[list[int]] = [[] for _ in range(n)]
    for k, p in enumerate(places):
        members[idx[p]].append(k)
    med = np.zeros((n, n))
    for i in range(n):  # 逐次: セル数ぶん(ツール側)
        block = dist[members[i]]
        for j in range(i + 1, n):
            med[i, j] = float(np.median(block[:, members[j]]))
    ctl = np.rint(med[iu])
    a, b = hist_pair(declared[iu].astype(np.float64), ctl, DIST_BIN_M)
    out.append(result("W3#1", "代表ノード間の最短路(宣言)vs セル内ノード対の最短路の中央値", "セル間距離(上三角)の 10 m 階級分布",
                      [variant("ノード対の中央値", cmp(a, b), mean_abs_diff_m=float(np.abs(declared[iu] - ctl).mean()),
                               share_pairs_abs_diff_ge_10m=float((np.abs(declared[iu] - ctl) >= 10.0).mean()))],
                      seconds_stage=t_common + time.perf_counter() - t1, checks={"declared_recomputed_equals_asset": ok},
                      notes=["分布の JSD は対ごとの入れ替えを見ない(対ごとの差は mean_abs_diff_m・share_pairs_abs_diff_ge_10m に記録)"]))
    # W3#2: 丸めない(float)
    fl = sym[iu]
    a, b = hist_pair(declared[iu].astype(np.float64), fl, DIST_BIN_M)
    a1, b1 = hist_pair(declared[iu].astype(np.float64), fl, 1.0)
    out.append(result("W3#2", "uint16 メートル丸め(宣言)vs 丸めない(float)", "セル間距離(上三角)の 10 m 階級分布",
                      [variant("丸めない・10 m 階級", cmp(a, b), max_abs_diff_m=float(np.abs(declared[iu] - fl).max())),
                       variant("丸めない・1 m 階級(参考)", cmp(a1, b1), primary=False)],
                      seconds_stage=t_common, checks={"declared_recomputed_equals_asset": ok}))
    # W3#3: 対称化しない
    raw = np.minimum(np.rint(sub), 65534)
    off = ~np.eye(n, dtype=bool)
    a, b = hist_pair(declared[off].astype(np.float64), raw[off], DIST_BIN_M)
    a1, b1 = hist_pair(declared[off].astype(np.float64), raw[off], 1.0)
    out.append(result("W3#3", "丸め前に min(D, Dᵀ) で対称化(宣言)vs 対称化しない", "セル間距離(対角以外の全順序対)の 10 m 階級分布",
                      [variant("対称化しない・10 m 階級", cmp(a, b), entries_differ=int((raw[off] != declared[off]).sum())),
                       variant("対称化しない・1 m 階級(参考)", cmp(a1, b1), primary=False)],
                      seconds_stage=t_common, checks={"declared_recomputed_equals_asset": ok}))
    return out


# ======================================================================== W5-W6
def c_w5_2(E: Env) -> dict[str, Any]:
    t0 = time.perf_counter()
    c = read_cols(E.base / "w5_entrances.parquet", ["place_id", "own_grid_place_id"])
    n_diff = sum(1 for a, b in zip(c["place_id"], c["own_grid_place_id"]) if a != b)
    return result("W5#2", "最寄りノードのセル(宣言)vs 入口座標の格子セル", "入口のセル分布",
                  [variant("入口座標の格子セル", cmp_counter(Counter(c["place_id"]), Counter(c["own_grid_place_id"])))],
                  seconds_stage=time.perf_counter() - t0, entrances_cell_differs=n_diff)


def c_w6_2(E: Env) -> dict[str, Any]:
    t0 = time.perf_counter()
    cidx = set(cell_index(E.base))
    vs = []
    for name, f in (("POI", "w6_poi.parquet"), ("組織", "w6_org.parquet")):
        c = read_cols(E.base / f, ["x", "y", "place_id"])
        ctl = []
        for x, y in zip(c["x"], c["y"]):
            p = f"g{math.floor(x / 100.0)}_{math.floor(y / 100.0)}_GL"
            ctl.append(p if p in cidx else "(セル表に無い)")
        vs.append(variant(f"{name}: 格子だけ(バンド GL)", cmp_counter(Counter(c["place_id"]), Counter(ctl)),
                          n_changed=sum(1 for a, b in zip(c["place_id"], ctl) if a != b)))
    return result("W6#2", "自身の格子×束縛ノードのバンド・欠けたらノードのセル(宣言)vs 格子だけ(バンド GL・欠けは『セル表に無い』)",
                  "POI・組織のセル分布", vs, seconds_stage=time.perf_counter() - t0)


def _subcat_counts(d: Path) -> Counter:
    c = read_cols(d / "w6_poi.parquet", ["cat", "subcat"])
    return Counter(f"{a}|{b or ''}" for a, b in zip(c["cat"], c["subcat"]))


def c_w6_3(E: Env) -> dict[str, Any]:
    import shibuya.build.geo.w6_poi_org as W6

    d = E.new_ctl("W6#3")
    P = Patch()
    P.set(W6, "USE_NAME_SUBCAT_RULES", False)
    t = run_stages(d, ["W6"])
    P.undo()
    a, b = _subcat_counts(E.base), _subcat_counts(d)
    r = result("W6#3", "名前一致層あり(宣言)vs なし(切替口 USE_NAME_SUBCAT_RULES=False)", "POI の cat|subcat 分布",
               [variant("名前一致層なし", cmp_counter(a, b), n_changed=int(sum(abs(a[k] - b[k]) for k in set(a) | set(b)) // 2))],
               seconds_stage=t, outputs_changed=changed_outputs(E.base, d))
    E.drop(d)
    return r


# ======================================================================== W7
MINOR_WINDOW = ((1380, 1680),)  # 23:00-翌4:00(青少年条例16条)


def _minor_view(weeks, mask: Sequence[bool]):
    import shibuya.build.field.w7_planspec as W7

    return [W7.apply_law_cap(w, MINOR_WINDOW)[0] if m else w for w, m in zip(weeks, mask)]


def _w7_rerun(E: Env, key: str, patches: Callable[[Patch], None], data: Path = DATA):
    d = E.new_ctl(key)
    P = Patch()
    patches(P)
    t = run_stages(d, ["W7"], data=data)
    P.undo()
    _ids, wa, _k, _s = w7_weeks(E.base)
    _ids, wb, kb, _s = w7_weeks(d)
    res = cmp(open_hours_vector(wa), open_hours_vector(wb))
    changed = sum(1 for x, y in zip(wa, wb) if x != y)
    E.drop(d)
    return res, t, changed, kb


def c_w7_2(E: Env) -> dict[str, Any]:
    t0 = time.perf_counter()
    _ids, weeks, keys, _s = w7_weeks(E.base)
    mask = [k == "minor_entry_limit" for k in keys]
    res = cmp(open_hours_vector(weeks), open_hours_vector(_minor_view(weeks, mask)))
    return result("W7#2", "18 歳未満の立入制限を窓として当てない(宣言)vs 23:00-4:00 を当てる(未成年から見た営業中)",
                  "未成年から見た営業中 POI×時(168 時×{営業中,休業})の分布",
                  [variant("立入窓を当てる", res, n_poi_affected=int(sum(mask)))], seconds_stage=time.perf_counter() - t0)


def c_w7_5(E: Env) -> dict[str, Any]:
    import shibuya.build.field.w7_planspec as W7

    table = dict(W7.LAW_KEY_BY_CATSUB)
    table[("hotel", "love_hotel")] = "tenpo_seifuzoku"
    res, t, n, _ = _w7_rerun(E, "W7#5", lambda P: P.set(W7, "LAW_KEY_BY_CATSUB", table))
    return result("W7#5", "love_hotel=上限なし(宣言)vs 店舗型性風俗の窓 0:00-6:00(旅館業なら窓なし=宣言と同じ)",
                  "営業中 POI×時(168 時×{営業中,休業})の分布", [variant("店舗型性風俗の窓", res, n_poi_changed=n)], seconds_stage=t)


def c_w7_6(E: Env) -> dict[str, Any]:
    import shibuya.build.field.w7_planspec as W7

    table = dict(W7.LAW_KEY_BY_CATSUB)
    table[("nightlife", None)] = "settai_inshoku"
    res, t, n, _ = _w7_rerun(E, "W7#6", lambda P: P.set(W7, "LAW_KEY_BY_CATSUB", table))
    return result("W7#6", "nightlife 既定=深夜酒類提供・上限なし(宣言)vs 接待飲食(1-3 号)の窓 1:00-6:00(OSM タグの明示は優先のまま)",
                  "営業中 POI×時(168 時×{営業中,休業})の分布", [variant("接待飲食の窓", res, n_poi_changed=n)], seconds_stage=t)


def _ph_day(value: str):
    """opening_hours の PH 規則だけを拾う(最後の規則が勝つ)。無ければ None。"""
    import shibuya.build.field.w7_planspec as W7

    out = None
    for chunk in value.split(";"):
        for rule in W7._split_comma_rules(chunk.strip()):
            rule = rule.strip()
            m = W7._RULE.match(rule)
            if not m or not m.group("days") or "PH" not in m.group("days"):
                continue
            body = m.group("body").strip()
            out = [] if body in ("off", "closed") else W7._parse_time_ranges(body)
    return out


def c_w7_7(E: Env) -> dict[str, Any]:
    import datetime as dt

    import shibuya.build.field.w13_weather as W13
    import shibuya.build.field.w7_planspec as W7

    t0 = time.perf_counter()
    replay = json.loads((E.base / "W9.header.json").read_text(encoding="utf-8"))["notes"]["replay_date"]
    is_holiday = replay in W13.HOLIDAYS_2026
    ids, weeks, keys, srcs = w7_weeks(E.base)
    primary = cmp(open_hours_vector(weeks), open_hours_vector(weeks))  # 再生日が祝日でない=対照=宣言
    # 参考: 再生日が祝日だったら(PH 規則をその曜日へ当てる)
    ov = json.loads((DATA / "realworld" / "osm" / "poi_opening_hours_overpass_20260907.json").read_text(encoding="utf-8"))
    raw = {f"p_{e['type'][0]}{e['id']}": (e.get("tags") or {}).get("opening_hours") for e in ov["elements"]}
    dow = dt.date.fromisoformat(replay).weekday()
    hyp = [list(map(list, w)) for w in weeks]
    n_ph = 0
    for i, (pid, src) in enumerate(zip(ids, srcs)):
        v = raw.get(pid)
        if src != "osm_opening_hours" or not v or "PH" not in v:
            continue
        ph = _ph_day(v)
        if ph is None:
            continue
        n_ph += 1
        wk = [list(day) for day in weeks[i]]
        wk[dow] = list(ph)
        wk, _ = W7.apply_law_cap(wk, W7.LAW_CAPS[keys[i]]["closed_windows_min"])
        hyp[i] = wk
    sec = cmp(day_vector(weeks, dow), day_vector(hyp, dow))
    return result("W7#7", f"PH 規則を無視(宣言)vs 当てる(再生日 {replay} は祝日表に{'ある' if is_holiday else '無い'})",
                  "再生日の営業中 POI×時の分布",
                  [variant("PH を当てる(再生日=祝日でない→対照=宣言)", primary),
                   variant(f"参考: 再生日が祝日だったら(PH 規則のある POI {n_ph} 件をその曜日へ)", sec, primary=False)],
                  seconds_stage=time.perf_counter() - t0, replay_date=replay, replay_is_holiday=is_holiday)


def c_w7_8(E: Env) -> dict[str, Any]:
    src = DATA / "realworld" / "osm" / "poi_opening_hours_overpass_20260907.json"
    root = E.root / "data_w7_8"
    dst = root / "realworld" / "osm" / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    doc = json.loads(src.read_text(encoding="utf-8"))
    for e in doc["elements"]:
        tg = e.get("tags") or {}
        tg.pop("brand", None)
        tg.pop("brand:ja", None)
    dst.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    res, t, n, _ = _w7_rerun(E, "W7#8", lambda P: None, data=root)
    shutil.rmtree(root, ignore_errors=True)
    return result("W7#8", "brand 内の最頻を伝播(宣言)vs 伝播なし(入力の brand タグを落としてカテゴリ既定へ)",
                  "営業中 POI×時(168 時×{営業中,休業})の分布", [variant("伝播なし", res, n_poi_changed=n)], seconds_stage=t)


def c_w7_9(E: Env) -> dict[str, Any]:
    import shibuya.build.field.w7_planspec as W7

    caps = copy.deepcopy(W7.LAW_CAPS)
    caps["game_center"]["closed_windows_min"] = ((1380, 2040),)
    caps["settai_inshoku"]["closed_windows_min"] = ((1380, 2040),)
    caps["shinya_shurui"]["closed_windows_min"] = ((0, 360),)
    res, t, n, _ = _w7_rerun(E, "W7#9", lambda P: P.set(W7, "LAW_CAPS", caps))
    return result("W7#9", "一律(宣言=許容地域の行)vs **上界の対照**: 全 POI を住居集合地域とみなす(1-3 号・5 号 23:00-10:00・深夜酒類 0:00-6:00)",
                  "営業中 POI×時(168 時×{営業中,休業})の分布",
                  [variant("上界(全 POI 住居集合地域)", res, n_poi_changed=n)], seconds_stage=t,
                  notes=["告示 26 町丁の全名簿と用途地域がリポに無い(答申は名簿を省略形で載せる・取得は禁止)ので、"
                         "実際の地域条件ではなく**上界**を当てた。上界が帰無内なら実際も帰無内・超えたらラン対照へ(保守側)"])


def c_w7_10(E: Env) -> dict[str, Any]:
    import shibuya.build.field.w7_planspec as W7

    caps = copy.deepcopy(W7.LAW_CAPS)
    caps["settai_inshoku"]["closed_windows_min"] = ((60, 360),)
    caps["game_center"]["closed_windows_min"] = ((60, 600),)
    res, t, n, _ = _w7_rerun(E, "W7#10", lambda P: P.set(W7, "LAW_CAPS", caps))
    return result("W7#10", "特別日なし(宣言)vs 特別日の延長(許容地域外でも 1:00 まで)", "再生日の営業中 POI×時の分布",
                  [variant("特別日の延長(1:00)", res, n_poi_changed=n)], seconds_stage=t,
                  notes=["現行は全 POI に許容地域の行(1:00)を当てているので、特別日の延長(1:00)は同じ窓=構成上 差 0。"
                         "「告示する時」(特別の事情のある地域)は告示がリポに無く測れない"])


def c_w7_11(E: Env) -> dict[str, Any]:
    t0 = time.perf_counter()
    ids, weeks, keys, _s = w7_weeks(E.base)
    poi = read_cols(E.base / "w6_poi.parquet", ["poi_id", "cat", "subcat"])
    cs = {p: (c, s) for p, c, s in zip(poi["poi_id"], poi["cat"], poi["subcat"])}
    first = {("cinema", None), ("hall", "theatre"), ("hall", "events_venue"), ("hall", "music_venue")}
    second = {("leisure", "sports_centre")}
    dec_mask = [k == "minor_entry_limit" for k in keys]
    ctl_mask = [m or cs.get(p) in first or cs.get(p) in second for m, p in zip(dec_mask, ids)]
    res = cmp(open_hours_vector(_minor_view(weeks, dec_mask)), open_hours_vector(_minor_view(weeks, ctl_mask)))
    return result("W7#11", "三・四号だけ(宣言)vs 一号(cinema・hall の theatre/events_venue/music_venue)+二号(leisure の sports_centre で代用)も",
                  "未成年の立入窓(23:00-4:00 を当てた視点)での営業中 POI×時の分布",
                  [variant("一・二号も写像", res, n_poi_added=int(sum(ctl_mask) - sum(dec_mask)))],
                  seconds_stage=time.perf_counter() - t0,
                  notes=["二号(ボウリング/スケート/水泳)は subcat に無く sports_centre で代用(未リサーチ)"])


# ======================================================================== W8
def _w8_rerun(E: Env, key: str, patches: Callable[[Patch], None], name: str, subset: str | None = None):
    d = E.new_ctl(key)
    P = Patch()
    patches(P)
    t = run_stages(d, ["W8"])
    P.undo()
    res = cmp_pairs(w8_pairs(E.base), w8_pairs(d))
    na, nb = w8_nvisible(E.base), w8_nvisible(d)
    hi = int(max(na.max(), nb.max()))
    sec = cmp(np.bincount(na, minlength=hi + 1), np.bincount(nb, minlength=hi + 1))
    vs = [variant(f"{name}: (セル,対象)→見えている視点数", res, jaccard_pairs=res["jaccard_pairs"]),
          variant(f"{name}: 視点あたり可視数の分布(参考・w8_t1 はエンジンが読まない)", sec, primary=False)]
    out = (vs, t, changed_outputs(E.base, d), d)
    return out


def c_w8(E: Env, key: str) -> dict[str, Any]:
    import shibuya.build.vis.w8_visibility as W8
    from shibuya.build.geo import common as GC

    pts = read_cols(E.base / "w10_street_points.parquet", ["band"])
    band = np.asarray(pts["band"])
    n_pts = band.size
    specs: list[tuple[str, Callable[[Patch], None]]] = []
    control = metric = ""
    notes: list[str] = []
    if key == "W8#2":
        control = "最大視程 150 m(宣言)vs 100 m / 200 m"
        for r in (100.0, 200.0):
            specs.append((f"視程 {int(r)} m", lambda P, r=r: (P.set(W8, "MAX_RANGE_M", r), P.set(W8, "T2_MAX_CELL_DIST_M", r + 200.0))))
    elif key == "W8#3":
        control = "遮蔽ラスタ 2.5 m(宣言)vs 1.25 m(視線の標本刻みは 2.5 m のまま)"
        specs.append(("ラスタ 1.25 m", lambda P: P.set(W8.build_scene, "__defaults__", (1.25,))))
    elif key == "W8#4":
        control = "建物の基準地盤高=重心の DEM(宣言)vs footprint 頂点の DEM の最小値"
        osm = GC.load_json(DATA / "realworld" / "osm" / "shibuya_osm_wide_v8.json")
        tj = GC.load_json(DATA / "plateau" / "terrain.json")
        dem = np.load(DATA / "plateau" / "terrain.npz")["heights"]
        fp = {b["id"]: np.asarray(b["footprint"], dtype=np.float64) for b in osm["buildings"]}
        bids = read_cols(E.base / "w4_buildings.parquet", ["building_id"])["building_id"]
        orig = W8._dem_sample
        mins = np.array([float(orig(dem, tj["x0"], tj["y0"], tj["cell_m"], fp[b][:, 0], fp[b][:, 1])[0].min()) for b in bids],
                        dtype=np.float32)
        state = {"used": False}

        def ds(dem_, dx0, dy0, dcell, gx, gy):
            if np.ndim(gx) == 1 and len(gx) == len(bids) and not state["used"]:
                state["used"] = True
                return mins.copy(), 0
            return orig(dem_, dx0, dy0, dcell, gx, gy)

        specs.append(("頂点の DEM の最小", lambda P: P.set(W8, "_dem_sample", ds)))
    elif key == "W8#5":
        control = "DEM 範囲外=端の値でクランプ(宣言)vs 範囲外を欠損=基準面 GROUND0 15.18 m で埋める"
        orig = W8._dem_sample

        def ds5(dem_, dx0, dy0, dcell, gx, gy):
            vals, oor = orig(dem_, dx0, dy0, dcell, gx, gy)
            ny, nx = dem_.shape
            jx = np.floor((np.asarray(gx) - dx0) / dcell + 0.5)
            jy = np.floor((np.asarray(gy) - dy0) / dcell + 0.5)
            m = (jx < 0) | (jx >= nx) | (jy < 0) | (jy >= ny)
            vals = vals.copy()
            vals[m] = np.float32(GC.GROUND0_M)
            return vals, oor

        specs.append(("範囲外=GROUND0", lambda P: P.set(W8, "_dem_sample", ds5)))
    elif key == "W8#6":
        control = "DECK 視点の眼高=GL と同じ(宣言)vs DECK 視点だけ +6 m"
        orig_sg = W8.Scene.sample_ground
        deck = np.where(band == "DECK", 6.0, 0.0)

        def sg(self, x, y):
            z = orig_sg(self, x, y)
            return z + deck if np.size(x) == n_pts else z

        specs.append(("DECK +6 m", lambda P: P.set(W8.Scene, "sample_ground", sg)))
    elif key == "W8#7":
        control = "UG は建物ラスタを当てない(宣言)vs UG にも建物ラスタ(地上と同じ 2.5D 視線)を当てる"
        src = inspect.getsource(W8._visible_targets.py_func)
        line = "ok = True  # 地下街=遮蔽モデル無し(expedient)"
        assert line in src, "W8 のカーネルの UG 行が見つからない(ソースが変わった)"
        src = src.replace(line, "ok = _los(px[i], py[i], pz[i], tx[t], ty[t], tz[t], towner[t], ground_z, top_z, owner, "
                                "x0, y0, pitch, nx, ny, step, near_skip)")
        src = src.replace("cache=True", "cache=False")
        ns = dict(vars(W8))
        exec(compile(src, "<d44 W8#7>", "exec"), ns)  # noqa: S102 (ツール側の差し替え・src は変えない)
        kern = ns["_visible_targets"]
        specs.append(("UG にも遮蔽", lambda P: P.set(W8, "_visible_targets", kern)))
        notes.append("カーネルのソースをこのプロセスの中だけ 1 行差し替えて njit した(src のファイルは変えていない)")
    elif key == "W8#8":
        control = "1 視点あたり上限 256(宣言)vs 512"
        specs.append(("上限 512", lambda P: P.set(W8, "MAX_T1_PER_POINT", 512)))
    elif key == "W8#9":
        control = "T2 のセル対の標本 ≤200(宣言)vs ≤400"
        d = E.new_ctl(key)
        P = Patch()
        P.set(W8, "T2_MAX_PAIRS", 400)
        t = run_stages(d, ["W8"])
        P.undo()
        cells = read_cols(E.base / "w2_cells.parquet", ["centroid_x", "centroid_y"])
        cx, cy = np.asarray(cells["centroid_x"]), np.asarray(cells["centroid_y"])
        d2 = (cx[:, None] - cx[None, :]) ** 2 + (cy[:, None] - cy[None, :]) ** 2
        ev = np.triu(d2 <= W8.T2_MAX_CELL_DIST_M ** 2, k=0)
        ta = np.load(E.base / "w8_t2.npy").astype(np.float64)[ev]
        tb = np.load(d / "w8_t2.npy").astype(np.float64)[ev]
        ia = np.minimum((ta / 0.05).astype(np.int64), 20)
        ib = np.minimum((tb / 0.05).astype(np.int64), 20)
        r = result(key, control, "T2 見通し率(評価したセル対)の 0.05 階級分布",
                   [variant("標本 ≤400", cmp(np.bincount(ia, minlength=21), np.bincount(ib, minlength=21)),
                            mean_abs_diff=float(np.abs(ta - tb).mean()))],
                   seconds_stage=t, outputs_changed=changed_outputs(E.base, d),
                   notes=["w8_t2 はエンジン側の読み口が無い(D-44 (c) の段単位では W8 が読まれるので『読む』に入っている)"])
        E.drop(d)
        return r
    vs: list[dict[str, Any]] = []
    secs = 0.0
    changed: list[str] = []
    for name, fn in specs:
        v, t, ch, d = _w8_rerun(E, key, fn, name)
        vs.extend(v)
        secs += t
        changed = sorted(set(changed) | set(ch))
        E.drop(d)
    metric = "w8_t1_cell の (セル, 対象) → 見えている視点数 の分布(エンジンが読む表)"
    return result(key, control, metric, vs, seconds_stage=secs, outputs_changed=changed, notes=notes)


# ======================================================================== W9
def _refraction_deg(e: float) -> float:
    """大気差[deg](NOAA 太陽位置計算表の式・**記憶から書いた=一次未確認**)。"""
    if e > 85.0:
        return 0.0
    te = math.tan(math.radians(e))
    if e > 5.0:
        r = 58.1 / te - 0.07 / te ** 3 + 0.000086 / te ** 5
    elif e > -0.575:
        r = 1735.0 + e * (-518.2 + e * (103.4 + e * (-12.79 + e * 0.711)))
    else:
        r = -20.772 / te
    return r / 3600.0


def c_w9(E: Env, key: str) -> dict[str, Any]:
    import pyarrow.parquet as pq

    import shibuya.build.vis.w8_visibility as W8
    import shibuya.build.vis.w9_shadow as W9

    pts = read_cols(E.base / "w10_street_points.parquet", ["x", "y", "band"])
    cidx = cell_index(E.base)
    cells = point_cells(pts["x"], pts["y"], pts["band"], cidx)
    band = np.asarray(pts["band"])
    n_pts = band.size
    notes: list[str] = []
    partial = None
    d = E.new_ctl(key)
    P = Patch()
    if key == "W9#1":
        control = "影の最大追跡 300 m(宣言)vs 600 m"
        P.set(W9, "SHADOW_MAX_M", 600.0)
    elif key == "W9#2":
        control = "DECK=GL と同じ扱い(宣言)vs DECK 視点だけ +6 m(UG の常時日陰は両側とも同じ)"
        orig_sg = W8.Scene.sample_ground
        deck = np.where(band == "DECK", 6.0, 0.0)
        P.set(W8.Scene, "sample_ground", lambda self, x, y: orig_sg(self, x, y) + (deck if np.size(x) == n_pts else 0.0))
    elif key == "W9#3":
        control = "遮蔽ラスタ 2.5 m(宣言)vs 1.25 m"
        P.set(W8.build_scene, "__defaults__", (1.25,))
    elif key == "W9#4":
        control = "大気差・尾根越し遮蔽なし(宣言)vs 大気差あり(太陽高度に大気差を足す)"
        orig_sv = W9.sun_vector

        def sv(date, local_min):
            e, az, _t = orig_sv(date, local_min)
            e2 = e + _refraction_deg(e)
            return e2, az, math.tan(math.radians(e2))

        P.set(W9, "sun_vector", sv)
        partial = "尾根越し遮蔽(ラスタの外の遠方地形)は遠方の DEM がリポに無く測れない"
        notes.append("大気差の式は NOAA 太陽位置計算表の式を記憶から書いた(一次未確認=未リサーチ)")
    elif key == "W9#5":
        days = pq.read_table(d / "w13_weather_days.parquet")
        order = list(range(days.num_rows))
        order = [order[-1]] + order[:-1]
        pq.write_table(days.take(order), d / "w13_weather_days.parquet")
        alt = days.column("date").to_pylist()[-1]
        control = f"再生日=W13 の先頭日 2026-07-28(宣言)vs 候補の末日 {alt}"
    else:
        raise KeyError(key)
    t = run_stages(d, ["W9"])
    P.undo()
    a = w9_joint(E.base, cells, len(cidx))
    b = w9_joint(d, cells, len(cidx))
    r = result(key, control, "影の面 → (セル × 時 × {日陰, 日向}) の点・面の数の分布",
               [variant(control.split("vs")[-1].strip(), cmp(a, b),
                        shadow_share_declared=float(a[1::2].sum() / a.sum()), shadow_share_control=float(b[1::2].sum() / b.sum()))],
               seconds_stage=t, outputs_changed=changed_outputs(E.base, d), notes=notes)
    if partial:
        r["partial"] = partial
    E.drop(d)
    return r


# ======================================================================== W10
def c_w10(E: Env, key: str) -> dict[str, Any]:
    import shibuya.build.field.w10_noise as W10

    notes: list[str] = []
    specs: list[tuple[str, Callable[[Patch], None]]] = []
    if key == "W10#2":
        control = "昼間 12 h・残り 12 h を各一様(宣言)vs 残り 12 h を昼に近い 4 時間(19-21・6 時)へ 1.5 倍・深夜 8 時間を 0.75 倍(総量は同じ)"
        orig = W10.hourly_flows

        def hf(q12, q24, heavy_pct):
            out = dict(orig(q12, q24, heavy_pct))
            for h in range(24):
                if h in W10.CENSUS_DAY12_HOURS:
                    continue
                f = 1.5 if h in (19, 20, 21, 6) else 0.75
                out[h] = (out[h][0] * f, out[h][1] * f)
            return out

        specs.append(("夜の配分を寄せる", lambda P: P.set(W10, "hourly_flows", hf)))
    elif key == "W10#3":
        control = "大型車混入率・旅行速度は昼夜同一(宣言)vs 昼間 12 h 以外の時間だけ 大型車率 ×1.1 と速度 ×1.1 / ×0.9 と ×0.9"
        for f in (1.1, 0.9):
            def ec(sec, regime, f=f):
                q12, q24, heavy = float(sec["q12"]), float(sec["q24"]), float(sec["heavy_pct"])
                fl_d = W10.hourly_flows(q12, q24, heavy)
                fl_n = W10.hourly_flows(q12, q24, min(heavy * f, 100.0))
                lanes = max(int(sec["lanes"]), 1)
                v = float(sec["v_kmh"])

                def avg(hours):
                    tot = 0.0
                    for h in hours:
                        day = h in W10.CENSUS_DAY12_HOURS
                        nl, nh = (fl_d if day else fl_n)[h]
                        vv = v if day else v * f
                        tot += W10.lane_energy_coeff("light", vv, nl / lanes, regime)
                        tot += W10.lane_energy_coeff("heavy", vv, nh / lanes, regime)
                    return tot / len(hours)

                return avg(W10.DAY_HOURS), avg(W10.NIGHT_HOURS)

            specs.append((f"夜の大型車率・速度 ×{f}", lambda P, ec=ec: P.set(W10, "energy_coeffs", ec)))
    elif key == "W10#4":
        control = "舗装=密粒(宣言)vs 排水性(騒音場の全辺)"
        orig_ec = W10.energy_coeffs
        specs.append(("排水性", lambda P: P.set(W10, "energy_coeffs",
                                                lambda sec, regime: orig_ec(sec, "nonsteady_drain" if regime == "nonsteady_dense" else regime))))
    elif key == "W10#6":
        control = "車線別線音源+交通量の車線等分(宣言)vs 車道中心の 1 線源(全交通量)"
        specs.append(("中心 1 線源", lambda P: P.set(W10, "geometry_factor",
                                                 lambda d_m, width_m, lanes: max(int(lanes), 1) / max(d_m, (width_m / max(int(lanes), 1)) / 2.0))))
    elif key == "W10#7":
        control = "バンド遮蔽 UG −20 dB(宣言)vs −10 dB / −30 dB"
        for db in (-10.0, -30.0):
            specs.append((f"UG {int(db)} dB", lambda P, db=db: P.set(W10, "BAND_SHIELDING_DB", {**W10.BAND_SHIELDING_DB, "UG": db})))
    elif key == "W10#9":
        control = "街路格子 ピッチ 2.5 m(宣言)vs 5 m(バッファ 8 m は同じ)"
        orig_sp = W10.street_points
        specs.append(("ピッチ 5 m", lambda P: P.set(W10, "street_points", lambda edges, coords, **kw: orig_sp(edges, coords, pitch_m=5.0))))
        notes.append("点の集合が変わるので、W8/W9 の視点も下流で変わる(本行の指標は W10 の騒音段階だけ)")
    else:
        raise KeyError(key)
    base = w10_joint(E.base)
    vs: list[dict[str, Any]] = []
    secs = 0.0
    changed: list[str] = []
    for name, fn in specs:
        d = E.new_ctl(key)
        P = Patch()
        fn(P)
        secs += run_stages(d, ["W10"])
        P.undo()
        extra: dict[str, Any] = {}
        if key != "W10#9":  # 点の集合が同じときだけ点ごとの段階の変化率(参考)
            sa = np.load(E.base / "w10_noise_stage_day.npy")
            sb = np.load(d / "w10_noise_stage_day.npy")
            na = np.load(E.base / "w10_noise_stage_night.npy")
            nb = np.load(d / "w10_noise_stage_night.npy")
            extra = {"share_points_stage_changed_day": float((sa != sb).mean()),
                     "share_points_stage_changed_night": float((na != nb).mean())}
        vs.append(variant(name, cmp(base, w10_joint(d)), **extra))
        changed = sorted(set(changed) | set(changed_outputs(E.base, d)))
        E.drop(d)
    return result(key, control, "騒音段階 → (セル × {昼, 夜} × 段階 4) の点の数の分布", vs,
                  seconds_stage=secs, outputs_changed=changed, notes=notes)


def c_w10_10(E: Env) -> dict[str, Any]:
    import shibuya.build.field.road_names as RN
    import shibuya.build.field.w10_noise as W10
    from shibuya.build.geo import common as GC

    t0 = time.perf_counter()
    ed = read_cols(E.base / "w1_edges.parquet", ["edge_idx", "klass", "band", "geom_start", "geom_count"])
    coords = np.load(E.base / "w1_edge_geometry.npz")["coords"]
    sections = W10.read_kasyo(DATA.joinpath(*W10.KASYO))
    ways = GC.load_json(DATA.joinpath(*RN.ROAD_NAMES))["elements"]
    gs, gc = np.asarray(ed["geom_start"]), np.asarray(ed["geom_count"])
    mids = RN.edge_midpoints(gs, gc, coords)
    starts = coords[gs, :2]
    ends = coords[gs + gc - 1, :2]
    m_mid = RN.match_edges_to_ways(mids, ways, sections, edge_klass=ed["klass"], edge_band=ed["band"])
    m_s = RN.match_edges_to_ways(starts, ways, sections, edge_klass=ed["klass"], edge_band=ed["band"])
    m_e = RN.match_edges_to_ways(ends, ways, sections, edge_klass=ed["klass"], edge_band=ed["band"])
    declared = read_cols(E.base / "w10_edge_section.parquet", ["census_route"])["census_route"]
    ok = list(m_mid.route) == list(declared)
    vote = []
    for a, b, c in zip(m_mid.route, m_s.route, m_e.route):
        cnt = Counter([a, b, c])
        top, n = cnt.most_common(1)[0]
        vote.append(top if n >= 2 else a)
    road = [k in W10.ROAD_KLASSES for k in ed["klass"]]
    da = Counter(r or "(なし)" for r, m in zip(m_mid.route, road) if m)
    db = Counter(r or "(なし)" for r, m in zip(vote, road) if m)
    return result("W10#10", "辺の中点 1 点の最近傍 way(宣言)vs 両端+中点の多数決(割れたら中点)", "道路の辺のセンサス路線ラベルの分布",
                  [variant("両端+中点の多数決", cmp_counter(da, db), n_edges_changed=sum(1 for a, b, m in zip(m_mid.route, vote, road) if m and a != b))],
                  seconds_stage=time.perf_counter() - t0, checks={"declared_recomputed_equals_asset": ok},
                  notes=["USE_ROAD_NAME_MATCH は既定 False=対応表は騒音場に当たらない(診断の出力 w10_edge_section だけ)"])


# ======================================================================== W11
def _exit_platform_lengths(nodes: Mapping[str, list], edges: Mapping[str, list],
                           shift_kind: str | None = None, dxy: tuple[float, float] = (0.0, 0.0)) -> np.ndarray:
    import shibuya.build.geo.w11_station_exits as W11

    xy = {n: (x, y) for n, x, y in zip(nodes["sg_node_id"], nodes["x"], nodes["y"])}
    kind = dict(zip(nodes["sg_node_id"], nodes["kind"]))
    if shift_kind:
        xy = {n: ((p[0] + dxy[0], p[1] + dxy[1]) if kind[n] == shift_kind else p) for n, p in xy.items()}

    def length(a: str, b: str) -> float:
        g = round(float(np.hypot(xy[b][0] - xy[a][0], xy[b][1] - xy[a][1])), 3)
        return round(g * W11.INDOOR_PATH_FACTOR, 3)

    gate_of_exit = {b: a for a, b, k in zip(edges["from_node"], edges["to_node"], edges["kind"]) if k == "gate_exit"}
    plats_of_gate = defaultdict(list)
    for a, b, k in zip(edges["from_node"], edges["to_node"], edges["kind"]):
        if k == "platform_gate":
            plats_of_gate[b].append(a)
    out = []
    for e, g in sorted(gate_of_exit.items()):
        for p in plats_of_gate[g]:
            out.append(length(g, e) + length(p, g))
    return np.asarray(out, dtype=np.float64)


def c_w11_2(E: Env) -> dict[str, Any]:
    t0 = time.perf_counter()
    nodes = read_cols(E.base / "w11_station_graph_nodes.parquet", ["sg_node_id", "kind", "x", "y"])
    edges = read_cols(E.base / "w11_station_graph_edges.parquet", ["from_node", "to_node", "kind", "length_m"])
    dec = _exit_platform_lengths(nodes, edges)
    # 検算: 資産の length_m から組んだ長さと一致するか
    ln = {(a, b): l for a, b, l in zip(edges["from_node"], edges["to_node"], edges["length_m"])}
    gate_of_exit = {b: a for a, b, k in zip(edges["from_node"], edges["to_node"], edges["kind"]) if k == "gate_exit"}
    chk = []
    for e, g in sorted(gate_of_exit.items()):
        for a, b, k in zip(edges["from_node"], edges["to_node"], edges["kind"]):
            if k == "platform_gate" and b == g:
                chk.append(ln[(g, e)] + ln[(a, g)])
    ok = bool(np.allclose(np.asarray(chk), dec))
    vs = []
    for kind in ("platform", "gate"):
        for dxy in ((50.0, 0.0), (-50.0, 0.0), (0.0, 50.0), (0.0, -50.0)):
            ctl = _exit_platform_lengths(nodes, edges, kind, dxy)
            a, b = hist_pair(dec, ctl, DIST_BIN_M)
            vs.append(variant(f"{'ホーム' if kind == 'platform' else '改札'} ({int(dxy[0]):+d}, {int(dxy[1]):+d}) m", cmp(a, b),
                              mean_abs_diff_m=float(np.abs(dec - ctl).mean())))
    return result("W11#2", "ホーム=ODPT 代表点・改札=出口重心(宣言)vs ホームだけ/改札だけを ±50 m(東西・南北の 4 方向)ずらす",
                  "出口→改札→ホームの構内経路長(出口×ホームの対)の 10 m 階級分布", vs,
                  seconds_stage=time.perf_counter() - t0, checks={"declared_recomputed_equals_asset": ok})


def c_w11_rerun(E: Env, key: str) -> dict[str, Any]:
    import shibuya.build.geo.w11_station_exits as W11

    d = E.new_ctl(key)
    P = Patch()
    if key == "W11#3":
        control = "名称一致→最近傍(宣言)vs 最近傍だけ"
        P.set(W11, "_normalize_station_name", lambda name: "")
    else:
        control = "bbox+300 m(宣言)vs bbox+500 m"
        P.set(W11, "BBOX_MARGIN_M", 500.0)
    t = run_stages(d, ["W11"])
    P.undo()
    a = Counter(read_cols(E.base / "w11_station_exits.parquet", ["station_title"])["station_title"])
    b = Counter(read_cols(d / "w11_station_exits.parquet", ["station_title"])["station_title"])
    na = len(read_cols(E.base / "w11_stations.parquet", ["station_id"])["station_id"])
    nb = len(read_cols(d / "w11_stations.parquet", ["station_id"])["station_id"])
    r = result(key, control, "出口 45 → 駅の割当の分布",
               [variant(control.split("vs")[-1].strip(), cmp_counter(a, b), stations_declared=na, stations_control=nb,
                        declared=dict(a), control=dict(b))],
               seconds_stage=t, outputs_changed=changed_outputs(E.base, d))
    E.drop(d)
    return r


# ======================================================================== W12
def _gen_hour(d: Path, n_ref: int | None = None) -> tuple[np.ndarray, int]:
    c = read_cols(d / "w12_generation_weights.parquet", ["hour", "weight"])
    h = np.zeros(24)
    np.add.at(h, np.asarray(c["hour"], dtype=np.int64), np.asarray(c["weight"], dtype=np.float64))
    n = n_ref if n_ref is not None else len(c["hour"])
    return h / h.sum() * n, len(c["hour"])


def _tt_counts(d: Path, calendar: str | None = None) -> Counter:
    c = read_cols(d / "w12_timetables.parquet", ["line", "calendar", "departure_min"])
    return Counter((l, cal, (int(m) // 60) % 24) for l, cal, m in zip(c["line"], c["calendar"], c["departure_min"])
                   if calendar is None or cal == calendar)


def c_w12_rerun(E: Env, key: str) -> dict[str, Any]:
    import shibuya.build.field.w12_external_nodes as W12

    specs: list[tuple[str, Callable[[Patch], None]]] = []
    notes: list[str] = []
    metric_kind = "tt"
    if key == "W12#2":
        control = "～6時台→5,6 時・0時台～→0,1 時の等分(宣言)vs 端へ寄せる(外側 5 時と 1 時/内側 6 時と 0 時)"
        orig = W12._pt_bin_to_hours

        def mk(first: int, last: int):
            def f(label: str):
                if label.startswith("～"):
                    return [first]
                if label.endswith("時台～") or label.startswith("0時台～"):
                    return [last]
                return orig(label)
            return f

        specs.append(("外側(5 時・1 時)", lambda P: P.set(W12, "_pt_bin_to_hours", mk(5, 1))))
        specs.append(("内側(6 時・0 時)", lambda P: P.set(W12, "_pt_bin_to_hours", mk(6, 0))))
        metric_kind = "gen"
    elif key == "W12#5":
        control = "山手線ピーク 18 本/h(宣言)vs 16 / 20 本/h"
        for n in (16, 20):
            specs.append((f"{n} 本/h", lambda P, n=n: P.set(W12, "PEAK_TRAINS_PER_HOUR", {**W12.PEAK_TRAINS_PER_HOUR, "山手線": n})))
    elif key == "W12#6":
        control = "オフピーク比=メトロ実ダイヤから(宣言)vs 比 1.0(一様)"
        orig = W12.offpeak_ratio_from
        specs.append(("比 1.0", lambda P: P.set(W12, "offpeak_ratio_from", lambda rows: (1.0,) + tuple(orig(rows)[1:]))))
    elif key == "W12#7":
        control = "夕ピーク=朝ピークと同数(宣言)vs 夕ピーク −20%"
        orig = W12.equal_interval_departures
        specs.append(("夕ピーク −20%", lambda P: P.set(
            W12, "equal_interval_departures",
            lambda peak_tph, offpeak_ratio, first_min, last_min, peak_tph_pm=None:
                orig(peak_tph, offpeak_ratio, first_min, last_min, peak_tph_pm=int(round(0.8 * peak_tph))))))
        notes.append("切替口 PM_PEAK_ASSUMED_EQUAL_TO_AM は True/False のどちらでも peak_tph_pm=朝と同数を渡す"
                     "(`None if PM_PEAK_ASSUMED_EQUAL_TO_AM else tph`)=口として効かない。ここでは関数を包んで −20% を渡した")
    else:
        raise KeyError(key)
    vs = []
    secs = 0.0
    changed: list[str] = []
    ga, n_rows = _gen_hour(E.base)
    ta = _tt_counts(E.base)
    for name, fn in specs:
        d = E.new_ctl(key)
        P = Patch()
        fn(P)
        secs += run_stages(d, ["W12"])
        P.undo()
        if metric_kind == "gen":
            gb, _ = _gen_hour(d, n_rows)
            vs.append(variant(name, cmp(ga, gb)))
        else:
            vs.append(variant(name, cmp_counter(ta, _tt_counts(d))))
        changed = sorted(set(changed) | set(changed_outputs(E.base, d)))
        E.drop(d)
    metric = ("生成用重みの時刻分布(24 時・帰無参照の N=重み行数 2,014=既存 S-W14-HOURUNIFORM と同じ expedient)"
              if metric_kind == "gen" else "便の (路線 × 曜日種別 × 時) の分布")
    return result(key, control, metric, vs, seconds_stage=secs, outputs_changed=changed, notes=notes)


def c_w12_3(E: Env) -> dict[str, Any]:
    t0 = time.perf_counter()
    c = read_cols(E.base / "w12_generation_weights.parquet", ["node_id", "purpose", "mode", "weight"])
    w = np.asarray(c["weight"], dtype=np.float64)
    n = w.size
    purposes = sorted(set(c["purpose"]))
    grp = [f"{a}|{b}" for a, b in zip(c["node_id"], c["mode"])]
    gsum = defaultdict(float)
    for g, x in zip(grp, w):
        gsum[g] += x
    dec = Counter()
    for p, x in zip(c["purpose"], w):
        dec[p] += x / w.sum() * n
    vs = []
    for p in purposes:
        for f in (1.1, 0.9):
            w2 = np.where(np.asarray(c["purpose"]) == p, w * f, w)
            g2 = defaultdict(float)
            for g, x in zip(grp, w2):
                g2[g] += x
            w3 = np.asarray([x * gsum[g] / g2[g] for g, x in zip(grp, w2)])  # (方面×手段)の総量は保つ
            ctl = Counter()
            for q, x in zip(c["purpose"], w3):
                ctl[q] += x / w3.sum() * n
            vs.append(variant(f"{p} ×{f}", cmp_counter(dec, ctl)))
    return result("W12#3", "目的×手段の構成=全ノード共通(宣言)vs 目的ごとに 1 つずつ ±10%(方面×手段の総量は保って再正規化)",
                  "生成用重みの目的分布(帰無参照の N=重み行数 2,014)", vs, seconds_stage=time.perf_counter() - t0)


def c_w12_8(E: Env) -> dict[str, Any]:
    import shibuya.build.field.w12_external_nodes as W12
    from shibuya.build.geo import common as GC

    t0 = time.perf_counter()
    rows = []
    for line, fname in W12.METRO_TIMETABLES:
        for r in W12.parse_metro_timetable(GC.load_json(DATA / "odpt" / fname)):
            rows.append({**r, "line": line})
    wk = [r for r in rows if r["calendar"] == "Weekday"]
    hol = [r for r in rows if r["calendar"] != "Weekday"]

    def first_last(rs):
        mins = sorted(W12._minute(r["departure"]) for r in rs)
        f, l = mins[0], mins[-1]
        return f, (l + 1440 if l < f else l)

    fw, lw = first_last(wk)
    fh, lh = first_last(hol)
    ratio_h = W12.offpeak_ratio_from(hol)[0]
    lines = ("井の頭線", "埼京線", "山手線", "東横線", "湘南新宿ライン", "田園都市線")
    tt = read_cols(E.base / "w12_timetables.parquet", ["line", "direction", "calendar", "departure", "source"])

    def regen(first, last):
        out = Counter()
        for line in lines:
            tph = W12.PEAK_TRAINS_PER_HOUR.get(line)
            if not tph:
                continue
            for _dir in ("上り", "下り"):
                for dep in W12.equal_interval_departures(tph, ratio_h, first, last, peak_tph_pm=None):
                    out[(line, "SaturdayHoliday", (W12._minute(dep) // 60) % 24)] += 1
        return out

    declared_exp = Counter((l, cal, (W12._minute(dep) // 60) % 24) for l, cal, dep, s in
                           zip(tt["line"], tt["calendar"], tt["departure"], tt["source"])
                           if s == "equal_interval_expedient" and cal == "SaturdayHoliday")
    ok = regen(fw, lw) == declared_exp
    real = Counter((l, cal, (W12._minute(dep) // 60) % 24) for l, cal, dep, s in
                   zip(tt["line"], tt["calendar"], tt["departure"], tt["source"]) if s == "real" and cal == "SaturdayHoliday")
    dec = real + declared_exp
    ctl = real + regen(fh, lh)
    return result("W12#8", f"初終発=メトロ平日ダイヤ {fw // 60}:{fw % 60:02d}-{(lw // 60) % 24}:{lw % 60:02d}(宣言)"
                           f"vs 土休ダイヤ {fh // 60}:{fh % 60:02d}-{(lh // 60) % 24}:{lh % 60:02d}(土休の等間隔ダイヤだけ)",
                  "土休の便の (路線 × 時) の分布", [variant("土休の初終発", cmp_counter(dec, ctl))],
                  seconds_stage=time.perf_counter() - t0, checks={"declared_regenerated_equals_asset": ok})


# ======================================================================== W13
def _read_amedas_day_hourly_point(path: Path):
    """10 分値 → 時別(気温・湿度・風は**正時の値**・降水と日照は合計のまま)。"""
    import shibuya.build.field.w13_weather as W13
    from shibuya.build.geo import common as GC

    date, out = W13._orig_read_amedas_day(path)  # type: ignore[attr-defined]
    doc = GC.load_json(path)
    at: dict[int, dict] = {}
    for rec in doc["data"]:
        t = str(rec["obs_time_jst"])
        if t[14:16] == "00":
            at[int(t[11:13])] = rec["values"]
    for h, v in out.items():
        r = at.get(h)
        if r is None:
            continue
        for k, src in (("temp_c", "temp"), ("rh", "humidity"), ("wind_ms", "wind")):
            if r.get(src) is not None:
                v[k] = r.get(src)
    return date, out


def c_w13_rerun(E: Env, key: str) -> dict[str, Any]:
    import shibuya.build.field.w13_weather as W13

    d = E.new_ctl(key)
    P = Patch()
    if key == "W13#3":
        control = "日射=日照率と太陽高度からの推定(宣言)vs 日照率だけ(SR=0.9×日照率・太陽高度を見ない)"
        P.set(W13, "solar_elevation_deg", lambda date, local_min, *a, **k: 90.0)
    else:
        control = "時別=平均(気温・湿度・風)/合計(降水・日照)(宣言)vs 気温・湿度・風だけ正時の 10 分値"
        W13._orig_read_amedas_day = W13.read_amedas_day  # type: ignore[attr-defined]
        P.set(W13, "read_amedas_day", _read_amedas_day_hourly_point)
    t = run_stages(d, ["W13"])
    P.undo()
    a, b = heat_counts(E.base), heat_counts(d)
    r = result(key, control, "時別の体感温度段階(WBGT 段階・5 語+欠測)の分布(既存 S-W15-TEMP と同じ形)",
               [variant(control.split("vs")[-1].strip(), cmp_counter(a, b), declared=dict(a), control=dict(b))],
               seconds_stage=t, outputs_changed=changed_outputs(E.base, d))
    E.drop(d)
    return r


def c_w13_7(E: Env) -> dict[str, Any]:
    import datetime as dt

    import shibuya.build.field.w13_weather as W13

    t0 = time.perf_counter()
    c = read_cols(E.base / "w13_weather_hourly.parquet")
    n = len(c["date"])
    tabs = np.asarray([(dt.date.fromisoformat(d) - dt.date(2026, 7, 28)).days * 24 + int(h) for d, h in zip(c["date"], c["hour"])])
    src = np.asarray(c["src"])
    am = src == "amedas"
    dec: Counter = Counter()
    ctl: Counter = Counter()
    n_fill = 0
    for i in range(n):  # 逐次: 時別行数(840)
        if src[i] != "etrn":
            continue
        n_fill += 1
        dec[c["heat_stage"][i]] += 1
        vals = {}
        for k in ("temp_c", "rh", "wind_ms", "sunshine_h"):
            ok = am & np.asarray([v is not None for v in c[k]])
            xs, ys = tabs[ok], np.asarray([v for v, o in zip(c[k], ok) if o], dtype=np.float64)
            vals[k] = float(np.interp(tabs[i], xs, ys))
        solar = max(math.sin(math.radians(float(c["solar_elev_deg"][i]))), 0.0) * W13.SOLAR_CONST_KW * vals["sunshine_h"]
        w = W13.wbgt_estimate(vals["temp_c"], vals["rh"], vals["wind_ms"], solar)
        ctl[W13.HEAT_VOCAB[W13.heat_stage(w)]] += 1
    return result("W13#7", "アメダス欠測時間は etrn 時別値で補完(宣言)vs 前後のアメダス時別値の線形補間(気温・湿度・風・日照)",
                  "補完した時の体感温度段階の分布", [variant("線形補間", cmp_counter(dec, ctl), n_filled_hours=n_fill,
                                                          declared=dict(dec), control=dict(ctl))],
                  seconds_stage=time.perf_counter() - t0)


# ======================================================================== W16
def _w16_cols(d: Path, cols: Sequence[str]) -> dict[str, np.ndarray]:
    c = read_cols(d / "w16_population.parquet", cols)
    return {k: np.asarray(v) for k, v in c.items()}


def _res_home(d: Path) -> Counter:
    c = _w16_cols(d, ["pool_layer", "home_cell"])
    m = (c["pool_layer"] == 1) & (c["home_cell"] >= 0)
    return Counter(c["home_cell"][m].tolist())


def _w16_rerun(E: Env, key: str, patches: Callable[[Patch, dict], None], name: str,
               measure: Callable[[Path, dict], Any]) -> tuple[Any, float, list[str]]:
    import shibuya.build.pop.w16_population as W16

    d = E.new_ctl(key)
    rec: dict[str, np.ndarray] = {}
    P = Patch()
    orig = W16._multinomial_assign

    def ma(n, probs, domain, *counters):
        out = orig(n, probs, domain, *counters)
        rec[domain] = np.asarray(out).copy()
        return out

    P.set(W16, "_multinomial_assign", ma)
    patches(P, rec)
    t = run_stages(d, ["W16"])
    P.undo()
    m = measure(d, rec)
    ch = changed_outputs(E.base, d)
    E.drop(d)
    return m, t, ch


def c_w16(E: Env, key: str) -> dict[str, Any]:
    import shibuya.build.pop.w16_population as W16
    from shibuya.build.geo import common as GC

    notes: list[str] = []
    vs: list[dict[str, Any]] = []
    secs = 0.0
    changed: list[str] = []
    if key in ("W16#1", "W16#2", "W16#4"):
        base = _res_home(E.base)
        if key == "W16#1":
            control = "目標体数の空間支持=W2 セルの被覆で按分(宣言)vs 区全域(被覆のある町丁目は人口を全部入れる=被覆率>0 を 1 に)"
            orig = W16._chome_coverage

            def cov(*a, **k):
                c, ar, cells = orig(*a, **k)
                return np.where(c > 0, 1.0, 0.0), ar, cells

            fn = lambda P, rec: P.set(W16, "_chome_coverage", cov)  # noqa: E731
            notes.append("被覆 0 の町丁目は世界にセルが無く置けない=区全域の人口のうち世界に置ける分だけで比べた")
        elif key == "W16#2":
            control = "町丁目被覆率=10 m 標本格子(宣言)vs 5 m"
            fn = lambda P, rec: P.set(W16, "COVERAGE_STEP_M", 5.0)  # noqa: E731
        else:
            control = "住居系 kind に generic を入れる(宣言)vs 入れない"
            fn = lambda P, rec: P.set(W16, "RESIDENTIAL_KINDS", tuple(k for k in W16.RESIDENTIAL_KINDS if k != "generic"))  # noqa: E731
        m, t, ch = _w16_rerun(E, key, fn, "", lambda d, rec: _res_home(d))
        vs.append(variant(control.split("vs")[-1].strip(), cmp_counter(base, m),
                          residents_declared=int(sum(base.values())), residents_control=int(sum(m.values()))))
        secs += t
        changed = ch
        metric = "住民の自宅セルの分布"
    elif key == "W16#7":
        control = "従業者の年齢目標=区の 15 歳以上の分布(宣言)vs 1 階級(5 歳)上/下へずらす"
        c0 = _w16_cols(E.base, ["kind", "age"])
        ab = lambda age: W16._age_bin(age)  # noqa: E731
        base = Counter(ab(c0["age"][c0["kind"] == 0]).tolist())
        for shift in (+1, -1):
            orig = W16._age_target

            def at(n, counts, shift=shift, orig=orig):
                c = np.asarray(counts, dtype=np.float64)
                if c[:3].sum() == 0 and c.sum() > 0:  # 従業者の目標(15 歳未満が 0)
                    s = np.zeros_like(c)
                    if shift > 0:
                        s[1:] = c[:-1]
                        s[-1] += c[-1]
                    else:
                        s[:-1] = c[1:]
                    s[:3] = 0.0
                    c = s
                return orig(n, c)

            m, t, ch = _w16_rerun(E, key, lambda P, rec, at=at: P.set(W16, "_age_target", at), "",
                                  lambda d, rec: Counter(ab(_w16_cols(d, ["kind", "age"])["age"][_w16_cols(d, ["kind"])["kind"] == 0]).tolist()))
            vs.append(variant(f"{'+' if shift > 0 else '−'}5 歳", cmp_counter(base, m)))
            secs += t
            changed = sorted(set(changed) | set(ch))
        metric = "通勤者(kind 0)の年齢階級の分布"
    elif key == "W16#9":
        control = "通学・業務・私事の体数=PT 2018 の目的別到着比(宣言)vs 1 つずつ ±10%"
        base = Counter(_w16_cols(E.base, ["kind"])["kind"].tolist())
        orig_lj = GC.load_json
        for purpose in ("自宅－通学", "自宅－業務", "自宅－私事"):
            for f in (1.1, 0.9):
                def lj(p, purpose=purpose, f=f):
                    doc = orig_lj(p)
                    if Path(p).name == "pt6_summary_core0241.json":
                        doc = copy.deepcopy(doc)
                        doc["arrive_purpose_x_mode"][purpose]["計"] = float(doc["arrive_purpose_x_mode"][purpose]["計"]) * f
                    return doc

                m, t, ch = _w16_rerun(E, key, lambda P, rec, lj=lj: P.set(W16.C, "load_json", lj), "",
                                      lambda d, rec: Counter(_w16_cols(d, ["kind"])["kind"].tolist()))
                vs.append(variant(f"{purpose} ×{f}", cmp_counter(base, m), n_declared_agents=int(sum(base.values())),
                                  n_control_agents=int(sum(m.values()))))
                secs += t
                changed = sorted(set(changed) | set(ch))
        metric = "全体の種別(kind 0-8)の体数の分布"
    elif key == "W16#11":
        control = "学校セル=学校 POI へ一様(宣言)vs 学校 POI の建物の床面積(面積×階数)比(建物の無い POI は中央値)"
        poi = read_cols(E.base / "w6_poi.parquet", ["cat", "place_id", "building_id"])
        bld = read_cols(E.base / "w4_buildings.parquet", ["building_id", "area_m2", "levels"])
        cidx = cell_index(E.base)
        fa = {b: float(a) * max(int(lv), W16.DEFAULT_LEVELS) for b, a, lv in zip(bld["building_id"], bld["area_m2"], bld["levels"])}
        w = [fa.get(b) for c, p, b in zip(poi["cat"], poi["place_id"], poi["building_id"])
             if c in W16.SCHOOL_POI_CATS and cidx.get(p, -1) >= 0]
        med = float(np.median([x for x in w if x]))
        weights = np.asarray([x if x else med for x in w], dtype=np.float64)

        def sch(d):
            c = _w16_cols(d, ["school_cell"])["school_cell"]
            return Counter(c[c >= 0].tolist())

        base = sch(E.base)

        def fn(P, rec):
            cur = W16._multinomial_assign

            def ma(n, probs, domain, *counters):
                if domain.startswith("w16.school.") and np.size(probs) == weights.size:
                    probs = weights
                return cur(n, probs, domain, *counters)

            P.set(W16, "_multinomial_assign", ma)

        m, t, ch = _w16_rerun(E, key, fn, "", lambda d, rec: sch(d))
        vs.append(variant("床面積比", cmp_counter(base, m)))
        secs, changed = t, ch
        metric = "通学者と学齢の住民の学校セルの分布"
        notes.append(f"学校 POI {weights.size} 件・建物の無い POI {sum(1 for x in w if not x)} 件は床面積の中央値で埋めた(未リサーチ)")
    elif key == "W16#12":
        control = "住民の就業区分=多項抽選(宣言)vs 最大剰余の決定論(件数を配ってから決定論の置換で割り当て)"
        dom = "w16.resident.workcat"
        m0, t0, _ = _w16_rerun(E, key, lambda P, rec: None, "", lambda d, rec: (Counter(rec[dom].tolist()), changed_outputs(E.base, d)))
        base, ch0 = m0
        notes.append(f"宣言側は W16 を記録の包みだけで再実行した(出力が基準と一致: 変化したファイル {ch0 or 'なし'})")
        F = W16.F

        def fn(P, rec):
            cur = W16._multinomial_assign

            def ma(n, probs, domain, *counters):
                if domain == dom:
                    p = np.asarray(probs, dtype=np.float64)
                    cnt = F.largest_remainder(p / p.sum() * n, n)
                    lab = np.repeat(np.arange(p.size), cnt)[W16._perm(n, dom + ".lr")]
                    rec[dom] = lab.copy()
                    return lab
                return cur(n, probs, domain, *counters)

            P.set(W16, "_multinomial_assign", ma)

        m, t, ch = _w16_rerun(E, key, fn, "", lambda d, rec: Counter(rec[dom].tolist()))
        vs.append(variant("最大剰余", cmp_counter(base, m), declared={str(k): v for k, v in base.items()},
                          control={str(k): v for k, v in m.items()}))
        secs, changed = t0 + t, ch
        metric = "住民(15-74 歳)の就業区分 4 値の分布"
    elif key == "W16#13":
        control = "域外へ通う住民の方面=到着側『自宅－勤務』の重みを流用(宣言)vs 方面一様"
        dom = "w16.direction.resident_out"

        def dirs(d):
            c = _w16_cols(d, ["pool_layer", "direction_node"])
            m = (c["pool_layer"] == 1) & (c["direction_node"] >= 0)
            return Counter(c["direction_node"][m].tolist())

        base = dirs(E.base)

        def fn(P, rec):
            cur = W16._multinomial_assign

            def ma(n, probs, domain, *counters):
                if domain == dom:
                    probs = np.ones(np.size(probs))
                return cur(n, probs, domain, *counters)

            P.set(W16, "_multinomial_assign", ma)

        m, t, ch = _w16_rerun(E, key, fn, "", lambda d, rec: dirs(d))
        vs.append(variant("方面一様", cmp_counter(base, m)))
        secs, changed = t, ch
        metric = "域外へ通う住民の方面(外界ノード)の分布"
    else:
        raise KeyError(key)
    return result(key, control, metric, vs, seconds_stage=secs, outputs_changed=changed, notes=notes)


def c_w16_5(E: Env) -> dict[str, Any]:
    import shibuya.build.pop.w16_population as W16

    t0 = time.perf_counter()
    notes = json.loads((E.base / "W16.header.json").read_text(encoding="utf-8"))["notes"]
    joint = np.asarray(notes["ward_age_sex_joint"], dtype=np.float64)
    unknown = float(notes["ward_age_unknown"])
    counts = joint.sum(axis=1)
    c = _w16_cols(E.base, ["pool_layer", "age"])
    ages = c["age"][c["pool_layer"] == 1]
    n = ages.size
    dec = np.append(np.bincount(W16._age_bin(ages), minlength=counts.size).astype(np.float64), 0.0)
    total = counts.sum() + unknown
    ctl = np.append(counts / total * n, unknown / total * n)
    return result("W16#5", "年齢不詳を既知階級の比で按分(宣言)vs 不詳を別階級(区の不詳の割合 25,380/243,883)",
                  "住民の年齢階級(16+不詳)の分布", [variant("不詳を別階級", cmp(dec, ctl))], seconds_stage=time.perf_counter() - t0,
                  notes=["対照側は期待値(区の階級比 × 住民数)。宣言側は IPF+最大剰余の整数表(抽選なし)"])


def c_w16_8(E: Env) -> dict[str, Any]:
    import shibuya.build.pop.w16_population as W16

    t0 = time.perf_counter()
    F = W16.F
    notes = json.loads((E.base / "W16.header.json").read_text(encoding="utf-8"))["notes"]
    joint = np.asarray(notes["ward_age_sex_joint"], dtype=np.float64)
    c = _w16_cols(E.base, ["kind", "age", "sex"])
    vs = []
    for name, kinds in (("来街者(kind 1・6・7)", (1, 6, 7)), ("通学者(kind 5)", (5,))):
        m = np.isin(c["kind"], kinds)
        tab = np.zeros(joint.shape)
        np.add.at(tab, (W16._age_bin(c["age"][m]), c["sex"][m].astype(np.int64)), 1.0)
        n = tab.sum()
        row = joint.sum(axis=1) / joint.sum() * n
        col = joint.sum(axis=0) / joint.sum() * n
        ctl = F.ipf(tab + 1e-9, row, col).table
        vs.append(variant(name, cmp(tab.ravel(), ctl.ravel())))
    return result("W16#8", "来街者・通学者の年齢×性別は raking しない(宣言)vs 区の年齢×性別の周辺へ raking(IPF・種=現在の表)",
                  "年齢階級×性別(16×2)の分布", vs, seconds_stage=time.perf_counter() - t0,
                  notes=["種の 0 セルは 1e-9 を足して IPF に通した(0 は動かないのと同じ)"])


# ======================================================================== W17
def _w17_ingest(out: Path, repair: bool) -> float:
    resp = WORLD / "w17v2_r2" / "w17v2_stage2_responses.jsonl"
    cmd = [sys.executable, "-m", "shibuya.build.sched.trial", "--arm", "p2p", "--ingest-production", str(resp),
           "--out", str(out), "--world", str(WORLD), "--data", str(DATA), "--days", "1"]
    if repair:
        cmd.append("--time-fact-repair")
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    (out / "ingest.log").write_text((r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or ""), encoding="utf-8")
    return time.perf_counter() - t0


def c_w17_4(E: Env) -> dict[str, Any]:
    off, on = E.root / "w17_off", E.root / "w17_on"
    for p in (off, on):
        if p.exists():
            shutil.rmtree(p)
        p.mkdir(parents=True)
    t_off = _w17_ingest(off, False)
    t_on = _w17_ingest(on, True)
    promoted = sha256_file(WORLD / "w17_schedule.parquet")
    rep_off = sha256_file(off / "w17_schedule.parquet")

    def starts(d: Path) -> np.ndarray:
        c = read_cols(d / "w17_schedule.parquet", ["start_min", "activity_code"])
        return np.bincount(np.asarray(c["activity_code"], dtype=np.int64) * 96 + np.asarray(c["start_min"], dtype=np.int64) // 15,
                           minlength=64 * 96).astype(np.float64)

    a, b = starts(off), starts(on)
    return result("W17#4", "時刻の整合修復 off(宣言)vs on(`--time-fact-repair`・応答の再取り込み)",
                  "週次表の (活動 × 開始時刻 15 分階級) の分布",
                  [variant("修復 on", cmp(a, b))], seconds_stage=t_off + t_on,
                  checks={"repair_off_reproduces_promoted_schedule": rep_off == promoted},
                  seconds_detail={"ingest_off": t_off, "ingest_on": t_on})


def c_w17_5(E: Env) -> dict[str, Any]:
    import shibuya.build.sched.trial as T
    import shibuya.build.sched.w17_schedule as W17

    t0 = time.perf_counter()
    facts = W17.build_facts(WORLD, DATA)
    anchor = T.load_anchor(T.anchor_path())
    rows = T.production_rows(facts)
    tf0 = T.draw_windows(facts, anchor, rows=rows)
    orig = T._bin_table

    def uni(table, row):
        bt = orig(table, row)
        pdf = np.diff(np.concatenate([[0.0], bt.cdf]))
        u = (pdf > 0).astype(np.float64)
        return T.BinTable(bt.start, bt.width, np.cumsum(u / u.sum()), bt.actor_rate)

    P = Patch()
    P.set(T, "_bin_table", uni)
    tf1 = T.draw_windows(facts, anchor, rows=rows)
    P.undo()
    m0, m1 = tf0.depart >= 0, tf1.depart >= 0
    a = np.bincount(tf0.depart[m0] // 15, minlength=200).astype(np.float64)
    b = np.bincount(tf1.depart[m1] // 15, minlength=200).astype(np.float64)
    ra = np.bincount(np.clip(tf0.arrive[m0], 0, None) // 15, minlength=200).astype(np.float64)
    rb = np.bincount(np.clip(tf1.arrive[m1], 0, None) // 15, minlength=200).astype(np.float64)
    n = max(a.size, b.size)
    a, b = np.pad(a, (0, n - a.size)), np.pad(b, (0, n - b.size))
    n = max(ra.size, rb.size)
    ra, rb = np.pad(ra, (0, n - ra.size)), np.pad(rb, (0, n - rb.size))
    return result("W17#5", "勤務窓=第31/36表の逆関数法(宣言)vs 表の支え(構成比>0 の 15 分ビン)の上で一様",
                  "LLM へ渡す事実行の出勤・帰宅時刻(15 分階級)の分布=入力側",
                  [variant("出勤時刻", cmp(a, b), n_windows=int(m0.sum())), variant("帰宅時刻", cmp(ra, rb))],
                  seconds_stage=time.perf_counter() - t0,
                  notes=["取り込み(修復 off=本番)では窓は一致率の計数にしか使われない=窓を変えても週次表は動かない。"
                         "窓の効きは LLM への事実行を通る(再生成が要る)。ここで測ったのはその入力の差"])


# ======================================================================== 測れない行
UNMEASURABLE: dict[str, tuple[str, str]] = {
    "W10#5": ("ΔL=0(宣言)vs 回折の近似あり",
              "回折・反射の近似は建物の配置ごとに点で変わる補正で、式が未リサーチ・構築側に実装する口も無い(src の変更が要る)"),
    "W11#5": ("座標なし駅=同名駅の重心(宣言)vs OSM の駅ノード座標",
              "OSM の駅ノード(railway=station)の座標がリポのどの入力にも無い(v8 は路線の折れ線だけ)・Web 取得は禁止。"
              "ホーム位置 ±50 m の包絡は W11#2 で測った"),
    "W13#5": ("祝日表=2026 年 7-8 月のハードコード(宣言)vs 内閣府 CSV",
              "内閣府の祝日 CSV がリポに無い(未取得)・Web 取得は禁止"),
}


# ======================================================================== 登録
def registry() -> dict[str, Callable[[Env], Any]]:
    reg: dict[str, Callable[[Env], Any]] = {
        "W1#2": c_w1_2, "W1#3": c_w1_3, "W2#2": c_w2_2, "W2#3": c_w2_3, "W2#4": c_w2_4,
        "W3": c_w3, "W5#2": c_w5_2, "W6#2": c_w6_2, "W6#3": c_w6_3,
        "W7#2": c_w7_2, "W7#5": c_w7_5, "W7#6": c_w7_6, "W7#7": c_w7_7, "W7#8": c_w7_8, "W7#9": c_w7_9,
        "W7#10": c_w7_10, "W7#11": c_w7_11,
        "W10#10": c_w10_10, "W11#2": c_w11_2, "W12#3": c_w12_3, "W12#8": c_w12_8, "W13#7": c_w13_7,
        "W16#5": c_w16_5, "W16#8": c_w16_8, "W17#4": c_w17_4, "W17#5": c_w17_5,
    }
    for k in ("W8#2", "W8#3", "W8#4", "W8#5", "W8#6", "W8#7", "W8#8", "W8#9"):
        reg[k] = lambda E, k=k: c_w8(E, k)
    for k in ("W9#1", "W9#2", "W9#3", "W9#4", "W9#5"):
        reg[k] = lambda E, k=k: c_w9(E, k)
    for k in ("W10#2", "W10#3", "W10#4", "W10#6", "W10#7", "W10#9"):
        reg[k] = lambda E, k=k: c_w10(E, k)
    for k in ("W11#3", "W11#4"):
        reg[k] = lambda E, k=k: c_w11_rerun(E, k)
    for k in ("W12#2", "W12#5", "W12#6", "W12#7"):
        reg[k] = lambda E, k=k: c_w12_rerun(E, k)
    for k in ("W13#3", "W13#6"):
        reg[k] = lambda E, k=k: c_w13_rerun(E, k)
    for k in ("W16#1", "W16#2", "W16#4", "W16#7", "W16#9", "W16#11", "W16#12", "W16#13"):
        reg[k] = lambda E, k=k: c_w16(E, k)
    for k, (control, reason) in UNMEASURABLE.items():
        reg[k] = lambda E, k=k, c=control, r=reason: unmeasurable(k, c, r)
    return reg


def stage_of(key: str) -> str:
    return key.split("#")[0]


def keys_of_stage(stage: str) -> list[str]:
    ks = [k for k in registry() if stage_of(k) == stage]
    return sorted(ks, key=lambda k: (k.split("#") + ["0"])[1].zfill(3))


def write_result(res: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    for r in (res if isinstance(res, list) else [res]):
        path = RESULTS / f"{r['key'].replace('#', '_')}.json"
        path.write_text(json.dumps(r, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")


# ======================================================================== コマンド
def cmd_base(E: Env) -> int:
    if E.base.exists():
        shutil.rmtree(E.base)
    E.base.mkdir(parents=True)
    t0 = time.perf_counter()
    run_stages(E.base, BASE_STAGES)
    wall = time.perf_counter() - t0
    man = json.loads((WORLD / "build_manifest.json").read_text(encoding="utf-8"))
    cur = {h["stage"]: {o["path"]: o["sha256"] for o in h["outputs"]} for h in man["stages"]}
    rows = []
    for st in BASE_STAGES:
        h = json.loads((E.base / f"{st}.header.json").read_text(encoding="utf-8"))
        for o in h["outputs"]:
            rows.append({"stage": st, "output": o["path"], "same_as_promoted": cur.get(st, {}).get(o["path"]) == o["sha256"]})
    doc = {"stages": list(BASE_STAGES), "wall_seconds": round(wall, 2), "outputs": rows,
           "all_same": all(r["same_as_promoted"] for r in rows), "manifest_build_hash_head": man["build_hash"][:16]}
    (HERE / "base_rebuild.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("wall_seconds", "all_same")}, ensure_ascii=False), f"outputs={len(rows)}")
    return 0 if doc["all_same"] else 1


def cmd_selfcheck(E: Env) -> int:
    """計器の検算: (1) 手計算の JSD (2) 対照をずらさない再実行=入力側の差 0。"""
    out: dict[str, Any] = {}
    # (1) 2 階級・既知のずれ(0.5/0.5 vs 0.6/0.4)
    p, q = np.array([0.5, 0.5]), np.array([0.6, 0.4])
    m = (p + q) / 2
    hand = 0.5 * float((p * np.log2(p / m)).sum()) + 0.5 * float((q * np.log2(q / m)).sum())
    r = c8lib.compare_counts([500.0, 500.0], [600.0, 400.0])
    out["jsd_two_bins"] = {"hand": hand, "compare_counts": r["jsd_bits"], "equal": abs(hand - r["jsd_bits"]) < 1e-12}
    # (1b) W7 の指標: 1 POI 月曜 0-12 時 vs 0-6 時 → 営業 POI・時 12 vs 6 を 336 階級で
    a = open_hours_vector([[[(0, 720)], [], [], [], [], [], []]])
    b = open_hours_vector([[[(0, 360)], [], [], [], [], [], []]])
    pa, pb = a / a.sum(), b / b.sum()
    mm = (pa + pb) / 2
    nz = lambda x, y: float(sum(xi * math.log2(xi / yi) for xi, yi in zip(x, y) if xi > 0))  # noqa: E731
    hand2 = 0.5 * nz(pa, mm) + 0.5 * nz(pb, mm)
    r2 = c8lib.compare_counts(a, b)
    out["jsd_w7_metric_synthetic"] = {"open_hours_declared": float(a[:168].sum()), "open_hours_control": float(b[:168].sum()),
                                      "hand": hand2, "compare_counts": r2["jsd_bits"], "equal": abs(hand2 - r2["jsd_bits"]) < 1e-12}
    # (1c) 同じ分布なら 0・検出しない
    r3 = c8lib.compare_counts([3.0, 5.0, 7.0], [3.0, 5.0, 7.0])
    out["same_distribution"] = {"jsd": r3["jsd_bits"], "detected": r3["detected"]}
    # (2) 対照をずらさない再実行(段ごと)=出力が基準と同じ・指標が 0
    null: dict[str, Any] = {}
    for st, metric in (("W7", lambda d: cmp(open_hours_vector(w7_weeks(E.base)[1]), open_hours_vector(w7_weeks(d)[1]))),
                       ("W8", lambda d: cmp_pairs(w8_pairs(E.base), w8_pairs(d))),
                       ("W10", lambda d: cmp(w10_joint(E.base), w10_joint(d))),
                       ("W3", lambda d: cmp(*hist_pair(dist_upper(E.base), dist_upper(d), DIST_BIN_M))),
                       ("W12", lambda d: cmp_counter(_tt_counts(E.base), _tt_counts(d))),
                       ("W13", lambda d: cmp_counter(heat_counts(E.base), heat_counts(d))),
                       ("W16", lambda d: cmp_counter(_res_home(E.base), _res_home(d)))):
        d = E.new_ctl(f"null_{st}")
        t = run_stages(d, [st])
        res = metric(d)
        null[st] = {"outputs_changed": changed_outputs(E.base, d), "jsd": res["jsd_bits"], "detected": res["detected"],
                    "seconds": round(t, 2)}
        E.drop(d)
    # W9 は W8 の scene と同じ部品(1 回だけ)
    cidx = cell_index(E.base)
    pts = read_cols(E.base / "w10_street_points.parquet", ["x", "y", "band"])
    cells = point_cells(pts["x"], pts["y"], pts["band"], cidx)
    d = E.new_ctl("null_W9")
    t = run_stages(d, ["W9"])
    res = cmp(w9_joint(E.base, cells, len(cidx)), w9_joint(d, cells, len(cidx)))
    null["W9"] = {"outputs_changed": changed_outputs(E.base, d), "jsd": res["jsd_bits"], "detected": res["detected"], "seconds": round(t, 2)}
    E.drop(d)
    out["null_reruns"] = null
    ok = (out["jsd_two_bins"]["equal"] and out["jsd_w7_metric_synthetic"]["equal"] and out["same_distribution"]["jsd"] == 0.0
          and not out["same_distribution"]["detected"]
          and all(not v["outputs_changed"] and v["jsd"] == 0.0 and not v["detected"] for v in null.values()))
    out["all_ok"] = bool(ok)
    (HERE / "selfcheck.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_ok": ok, **{k: v for k, v in out.items() if k != "null_reruns"}}, ensure_ascii=False, default=float))
    for k, v in null.items():
        print(k, v)
    return 0 if ok else 1


def cmd_one(E: Env, key: str) -> int:
    fn = registry()[key]
    t0 = time.perf_counter()
    res = fn(E)
    wall = time.perf_counter() - t0
    for r in (res if isinstance(res, list) else [res]):
        r["seconds_wall_row"] = round(wall, 2)
        r["measured_at"] = time.strftime("%Y-%m-%d")
    write_result(res)
    for r in (res if isinstance(res, list) else [res]):
        print(json.dumps({"key": r["key"], "status": r["status"], "verdict": r.get("verdict"),
                          "variants": [(v["name"], round(v["jsd_bits"], 6), round(v["null_p95"], 6), v["detected"])
                                       for v in r.get("variants", [])]}, ensure_ascii=False))
    return 0


def cmd_stage(E: Env, stage: str, scratch_arg: str | None) -> dict[str, Any]:
    keys = keys_of_stage(stage)
    t0 = time.perf_counter()
    per: dict[str, float] = {}
    fails: list[str] = []
    for k in keys:
        t1 = time.perf_counter()
        cmd = [sys.executable, str(Path(__file__)), "--scratch", str(E.root), "one", k]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        per[k] = round(time.perf_counter() - t1, 2)
        sys.stdout.write(r.stdout)
        if r.returncode != 0:
            fails.append(k)
            sys.stderr.write(f"[{k}] 失敗\n{r.stderr[-4000:]}\n")
    wall = round(time.perf_counter() - t0, 2)
    doc = {"stage": stage, "keys": keys, "wall_seconds": wall, "per_key_seconds": per, "failed": fails}
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"_stage_{stage}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"[{stage}] wall={wall}s keys={len(keys)} failed={fails}")
    return doc


STAGE_ORDER = ("W1", "W2", "W3", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12", "W13", "W16", "W17")


# ======================================================================== (ii) mock
MOCK_AGENTS = 5_000


def _mock_world(E: Env, name: str, mutate: Callable[[Path], None]) -> Path:
    d = E.root / name
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for p in WORLD.iterdir():
        if p.is_file() and p.suffix != ".jsonl":
            shutil.copy2(p, d / p.name)
    mutate(d)
    return d


def _mock_run(world: Path, seed: int, out_npz: Path) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "shibuya.cli", "--agents", str(MOCK_AGENTS), "--seed", str(seed), "--world", str(world),
           "--occupancy-every", "60", "--occupancy-out", str(out_npz)]
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                       cwd=str(REPO))
    wall = time.perf_counter() - t0
    import re

    final = calls = None
    for line in (r.stdout or "").splitlines():
        m = re.search(r"最終 ([0-9a-f]{16})", line)
        if m and final is None:
            final = m.group(1)
        m = re.search(r"LLM呼 ([0-9,]+)", line)
        if m and calls is None:
            calls = int(m.group(1).replace(",", ""))
    return {"returncode": r.returncode, "wall_seconds": round(wall, 1), "final_line": final, "llm_calls": calls,
            "stdout_tail": (r.stdout or "")[-1500:], "stderr_tail": (r.stderr or "")[-1500:]}


def _area_hour(npz: Path, world: Path) -> np.ndarray:
    sys.path.insert(0, str(REPO / "tools" / "c7"))
    import occupancy_series as OS  # noqa: E402

    amap, _gate = OS.build_map(world)  # セル→5 エリア(E-C7-2 の expedient・holdout は読まない)
    s = OS.load_journal(npz, amap)
    return np.asarray(s.area_hour_table(amap), dtype=np.float64)


def _same_final(out: Mapping[str, Any], name: str) -> bool | None:
    a = out["runs"].get("declared_s1", {}).get("final_line")
    b = out["runs"].get(name, {}).get("final_line")
    return None if (a is None or b is None) else a == b


def cmd_mock(E: Env) -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq

    out: dict[str, Any] = {"agents": MOCK_AGENTS, "runs": {}}
    mdir = E.root / "mock"
    mdir.mkdir(parents=True, exist_ok=True)

    def w7_mut(d: Path) -> None:
        t = pq.read_table(d / "w7_plan_spec.parquet")
        n = t.num_rows
        t = t.set_column(t.column_names.index("violability"), "violability", pa.array(["enforced"] * n))
        t = t.set_column(t.column_names.index("revising_authority"), "revising_authority", pa.array(["any_role"] * n))
        pq.write_table(t, d / "w7_plan_spec.parquet")

    def v1_mut(d: Path) -> None:
        for name in ("w17_schedule.parquet", "W17.header.json", "w17_gates.json"):
            shutil.copy2(WORLD / "w17v1_backup" / name, d / name)

    worlds = {"declared": WORLD, "w7_cols": _mock_world(E, "world_w7", w7_mut), "w17_v1": _mock_world(E, "world_w17v1", v1_mut)}
    plan = [("declared", 1), ("declared", 2), ("declared", 3), ("w7_cols", 1), ("w17_v1", 1)]
    t0 = time.perf_counter()
    tables: dict[str, np.ndarray] = {}
    for w, s in plan:
        npz = mdir / f"{w}_s{s}.npz"
        rr = _mock_run(worlds[w], s, npz)
        name = f"{w}_s{s}"
        out["runs"][name] = {k: v for k, v in rr.items() if k not in ("stdout_tail", "stderr_tail")}
        if rr["returncode"] != 0 or not npz.exists():
            out["runs"][name]["stderr_tail"] = rr["stderr_tail"]
            print(f"[mock] {name} 失敗 rc={rr['returncode']}\n{rr['stderr_tail']}")
            continue
        tables[name] = _area_hour(npz, WORLD)
        print(f"[mock] {name} {rr['wall_seconds']}s {rr['final_line']}")
    out["wall_seconds"] = round(time.perf_counter() - t0, 1)

    def jsd(a: str, b: str) -> float | None:
        if a not in tables or b not in tables:
            return None
        from c6lib import jsd as _j  # noqa: E402

        return float(_j(tables[a].ravel(), tables[b].ravel()))

    null_pairs = [("declared_s1", "declared_s2"), ("declared_s1", "declared_s3"), ("declared_s2", "declared_s3")]
    nulls = [x for x in (jsd(a, b) for a, b in null_pairs) if x is not None]
    out["seed_null"] = {"pairs": {f"{a}~{b}": jsd(a, b) for a, b in null_pairs}, "max": max(nulls) if nulls else None}
    out["controls"] = {
        "W7#3/W7#4/W7#13": {"world": "w7_plan_spec の violability=全 enforced・revising_authority=any_role",
                            "jsd_vs_declared_s1": jsd("declared_s1", "w7_cols_s1"),
                            "final_same": _same_final(out, "w7_cols_s1")},
        "W17#1": {"world": "w17_schedule=v1(w17v1_backup)", "jsd_vs_declared_s1": jsd("declared_s1", "w17_v1_s1"),
                  "final_same": _same_final(out, "w17_v1_s1")},
    }
    (HERE / "mock_controls.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out["seed_null"], ensure_ascii=False), json.dumps(out["controls"], ensure_ascii=False))
    return 0


def cmd_collect() -> int:
    rows = {}
    for p in sorted(RESULTS.glob("W*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        rows[r["key"]] = r
    stages = {}
    for p in sorted(RESULTS.glob("_stage_*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))
        stages[s["stage"]] = s
    doc = {
        "schema": "shibuya.tools.c8/d44-controls/1",
        "created": "2026-09-30",
        "note": ("D-44 (i) 構築段階の対照(第311)。宣言 vs 対照の入力側 JSD を既存の台帳の片側規則(c8lib.compare_counts の"
                 "帰無参照=同分布 2 標本の JSD 95% 点)で判定。" + UNRESEARCHED_COMMON),
        "rows": rows,
        "stages": stages,
        "base_rebuild": json.loads((HERE / "base_rebuild.json").read_text(encoding="utf-8")) if (HERE / "base_rebuild.json").exists() else None,
        "selfcheck_all_ok": json.loads((HERE / "selfcheck.json").read_text(encoding="utf-8")).get("all_ok")
        if (HERE / "selfcheck.json").exists() else None,
    }
    (HERE / "d44_results.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    tally = Counter((r["status"], r.get("verdict")) for r in rows.values())
    print(len(rows), dict(tally))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D-44 の構築段階の対照と mock の対照")
    ap.add_argument("--scratch", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("base")
    sub.add_parser("selfcheck")
    one = sub.add_parser("one")
    one.add_argument("key")
    st = sub.add_parser("stage")
    st.add_argument("stage")
    sub.add_parser("all")
    sub.add_parser("mock")
    sub.add_parser("collect")
    args = ap.parse_args(list(argv) if argv is not None else None)
    if args.cmd == "collect":
        return cmd_collect()
    E = Env(scratch_root(args.scratch))
    E.root.mkdir(parents=True, exist_ok=True)
    if args.cmd == "base":
        return cmd_base(E)
    if args.cmd == "selfcheck":
        return cmd_selfcheck(E)
    if args.cmd == "one":
        return cmd_one(E, args.key)
    if args.cmd == "stage":
        doc = cmd_stage(E, args.stage, args.scratch)
        return 0 if not doc["failed"] else 1
    if args.cmd == "all":
        fails = []
        for s in STAGE_ORDER:
            fails += cmd_stage(E, s, args.scratch)["failed"]
        return 0 if not fails else 1
    if args.cmd == "mock":
        return cmd_mock(E)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
