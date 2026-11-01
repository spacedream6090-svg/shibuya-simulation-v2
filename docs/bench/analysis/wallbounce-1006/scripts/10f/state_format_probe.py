"""10f の材料(保存の形式): 10d の状態のファイル(pickle)の中身を型ごとに数え、npz(配列)+ json(それ以外)に
したときの大きさと読み書きの時間を試作で測る(src は読むだけ・出力は一時ディレクトリ)。

数えるもの
- SoA: 置き場ごとの列の数・dtype・バイト。
- 外の状態(``items``): 道筋ごとの最上位の型・pickle にしたときのバイト・中に出てくる型の数。
- 「npz+json でそのまま表せるか」の分類(実行役の自前の構成=未リサーチ(expedient)):
  * ``npz``      : 数値の dtype の ndarray(object の dtype は除く)
  * ``json``     : None・bool・int・float・str と、それだけを入れた list・str の鍵の dict
  * ``json_lossy``: json にはなるが型が落ちるもの(tuple → list・int の鍵 → 文字列・numpy のスカラー → Python の数)
  * ``tag``      : 印を付ければ表せるもの(set・tuple の鍵・bytes・dataclass/NamedTuple・Generator の状態・値のクラス・
                   OrderedDict・deque・Enum)
  * ``object``   : 上のどれでもない Python のオブジェクト(印の付け方を決めないと表せない)
- 同一性の共有: 同じオブジェクト(list・dict・set・ndarray・dataclass など)に 2 つ以上の道筋から届くもの。
- 試作の変換: 配列は npz(非圧縮と圧縮)・残りは印つきの json(``__t`` tuple・``__s`` set・``__d`` 鍵が str でない dict・
  ``__b`` bytes・``__o`` オブジェクト(クラス名+欄)・``__nd`` npz の鍵)。書き出しと読み込み(json.loads と
  np.load の全配列の読み出しまで・オブジェクトの組み立て直しは含めない)の時間を pickle と並べる。

使い方::

    python docs/bench/analysis/wallbounce-1006/scripts/10f/state_format_probe.py --state <state-T00001440.pkl> \
        --scratch <一時ディレクトリ> --out <json>
"""

from __future__ import annotations

import argparse
import base64
import collections
import dataclasses
import enum
import io
import json
import pickle
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np

SCALARS = (type(None), bool, int, float, str)


def _cls(v: Any) -> str:
    t = type(v)
    return f"{t.__module__}.{t.__qualname__}"


def classify(v: Any, counts: collections.Counter, depth: int = 0) -> str:
    """値の表しやすさの最悪の分類を返す(npz < json < json_lossy < tag < object)。"""
    order = ["npz", "json", "json_lossy", "tag", "object"]

    def worst(a: str, b: str) -> str:
        return a if order.index(a) >= order.index(b) else b

    counts[_cls(v)] += 1
    if isinstance(v, np.ndarray):
        return "object" if v.dtype == object else "npz"
    if isinstance(v, np.generic):
        return "json_lossy"
    if isinstance(v, enum.Enum):
        return "tag"
    if isinstance(v, SCALARS):
        return "json"
    if isinstance(v, (bytes, bytearray, memoryview)):
        return "tag"
    if isinstance(v, np.random.Generator) or isinstance(v, np.random.BitGenerator):
        return "tag"
    if isinstance(v, (set, frozenset)):
        w = "tag"
        for x in v:
            w = worst(w, classify(x, counts, depth + 1))
        return w
    if isinstance(v, tuple) and hasattr(v, "_fields"):
        w = "tag"
        for x in v:
            w = worst(w, classify(x, counts, depth + 1))
        return w
    if isinstance(v, (list, tuple, collections.deque)):
        w = "json" if isinstance(v, list) else ("json_lossy" if isinstance(v, tuple) else "tag")
        for x in v:
            w = worst(w, classify(x, counts, depth + 1))
        return w
    if isinstance(v, dict):
        w = "tag" if isinstance(v, collections.OrderedDict) else "json"
        for k, x in v.items():
            if isinstance(k, str):
                pass
            elif isinstance(k, (int, np.integer)) and not isinstance(k, bool):
                w = worst(w, "json_lossy")
            elif isinstance(k, tuple):
                w = worst(w, "tag")
                classify(k, counts, depth + 1)
            else:
                w = worst(w, classify(k, counts, depth + 1))
                w = worst(w, "tag")
            w = worst(w, classify(x, counts, depth + 1))
        return w
    if dataclasses.is_dataclass(v):
        w = "tag"
        for f in dataclasses.fields(v):
            w = worst(w, classify(getattr(v, f.name), counts, depth + 1))
        return w
    if hasattr(v, "__dict__"):
        w = "object"
        for x in vars(v).values():
            classify(x, counts, depth + 1)
        return w
    return "object"


def shared_refs(roots: dict[str, Any]) -> list[dict[str, Any]]:
    """2 つ以上の道筋から届く可変のオブジェクト(id で数える)。"""
    seen: dict[int, list[str]] = collections.defaultdict(list)
    keep: dict[int, Any] = {}

    def walk(v: Any, path: str) -> None:
        if isinstance(v, SCALARS) or isinstance(v, (np.generic, enum.Enum, bytes)):
            return
        i = id(v)
        first = i not in seen
        seen[i].append(path)
        keep[i] = v
        if not first:
            return
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, f"{path}[{k!r}]"[:200])
        elif isinstance(v, (list, tuple, set, frozenset, collections.deque)):
            for j, x in enumerate(v):
                walk(x, f"{path}[{j}]"[:200])
        elif isinstance(v, np.ndarray):
            if v.base is not None and isinstance(v.base, np.ndarray):
                walk(v.base, path + ".base")
        elif dataclasses.is_dataclass(v):
            for f in dataclasses.fields(v):
                walk(getattr(v, f.name), f"{path}.{f.name}")
        elif hasattr(v, "__dict__"):
            for k, x in vars(v).items():
                walk(x, f"{path}.{k}")

    for k, v in roots.items():
        walk(v, k)
    out = []
    for i, paths in seen.items():
        if len(paths) >= 2:
            out.append({"type": _cls(keep[i]), "n_paths": len(paths), "paths": paths[:4]})
    out.sort(key=lambda r: -r["n_paths"])
    return out


class Enc:
    """印つきの json + npz の試作の書き手。"""

    def __init__(self) -> None:
        self.arrays: dict[str, np.ndarray] = {}

    def arr(self, a: np.ndarray) -> dict:
        k = f"a{len(self.arrays)}"
        self.arrays[k] = a
        return {"__nd": k}

    def enc(self, v: Any) -> Any:
        if isinstance(v, np.ndarray):
            if v.dtype == object:
                return {"__ndo": [self.enc(x) for x in v.tolist()]}
            return self.arr(v)
        if isinstance(v, np.generic):
            return v.item()
        if isinstance(v, enum.Enum):
            return {"__e": _cls(v), "v": self.enc(v.value)}
        if isinstance(v, SCALARS):
            return v
        if isinstance(v, (bytes, bytearray)):
            return {"__b": base64.b64encode(bytes(v)).decode("ascii")}
        if isinstance(v, np.random.Generator):
            return {"__g": self.enc(v.bit_generator.state)}
        if isinstance(v, (set, frozenset)):
            return {"__s": [self.enc(x) for x in v]}
        if isinstance(v, tuple) and hasattr(v, "_fields"):
            return {"__o": _cls(v), "f": [self.enc(x) for x in v]}
        if isinstance(v, tuple):
            return {"__t": [self.enc(x) for x in v]}
        if isinstance(v, collections.deque):
            return {"__q": [self.enc(x) for x in v]}
        if isinstance(v, list):
            return [self.enc(x) for x in v]
        if isinstance(v, dict):
            if all(isinstance(k, str) for k in v) and not isinstance(v, collections.OrderedDict):
                return {k: self.enc(x) for k, x in v.items()}
            return {"__d": [[self.enc(k), self.enc(x)] for k, x in v.items()]}
        if dataclasses.is_dataclass(v):
            return {"__o": _cls(v), "f": {f.name: self.enc(getattr(v, f.name)) for f in dataclasses.fields(v)}}
        if hasattr(v, "__dict__"):
            return {"__o": _cls(v), "f": {k: self.enc(x) for k, x in vars(v).items()}}
        return {"__unk": _cls(v)}


def _timeit(fn, n: int = 5) -> float:
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    ts.sort()
    return ts[len(ts) // 2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from shibuya.engine import resume as RS
    from shibuya.engine import state_ledger as SL

    sp = Path(a.state)
    t0 = time.perf_counter()
    b = RS.read_state(sp)
    t_read_full = time.perf_counter() - t0
    file_bytes = sp.stat().st_size
    doc = {"header": b.header, "soa": b.soa, "items": b.items, "inflight": b.inflight}

    # ---- SoA
    soa_rows = []
    soa_bytes = 0
    for place, cols in b.soa.items():
        dts = collections.Counter(str(v.dtype) for v in cols.values())
        nb = sum(int(v.nbytes) for v in cols.values())
        soa_bytes += nb
        soa_rows.append({"place": place, "columns": len(cols), "bytes": nb, "dtypes": dict(dts)})

    # ---- items
    path_to_key = {p: k for k, p in SL.full_items()}
    rows = []
    cls_total: collections.Counter = collections.Counter()
    by_class: collections.Counter = collections.Counter()
    bytes_by_class: collections.Counter = collections.Counter()
    nd_bytes_items = 0
    for path, v in b.items.items():
        c: collections.Counter = collections.Counter()
        k = classify(v, c)
        pb = len(pickle.dumps(v, protocol=5))
        enc = Enc()
        try:
            js = json.dumps(enc.enc(v), ensure_ascii=False, separators=(",", ":"))
            jb = len(js.encode("utf-8"))
        except (TypeError, ValueError) as e:  # noqa: PERF203
            jb = -1
        nb = sum(int(x.nbytes) for x in enc.arrays.values())
        nd_bytes_items += nb
        cls_total.update(c)
        by_class[k] += 1
        bytes_by_class[k] += pb
        rows.append({"path": path, "row": path_to_key.get(path, ""), "top_type": _cls(v), "class": k,
                     "pickle_bytes": pb, "json_bytes": jb, "npz_raw_bytes": nb,
                     "types_inside": dict(c.most_common(6))})
    rows.sort(key=lambda r: -r["pickle_bytes"])

    # ---- 同一性の共有
    shared = shared_refs({"soa": b.soa, "items": b.items, "inflight": b.inflight})
    shared_items_only = [s for s in shared if not all(p.startswith("soa") for p in s["paths"])]

    # ---- 試作の変換(全体)
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    enc = Enc()
    t = time.perf_counter()
    body = {"header": enc.enc(b.header), "soa": {p: {c: enc.arr(x) for c, x in cols.items()} for p, cols in b.soa.items()},
            "items": enc.enc(b.items), "inflight": enc.enc(b.inflight)}
    t_encode = time.perf_counter() - t
    js_text = json.dumps(body, ensure_ascii=False, separators=(",", ":"))
    jpath = scratch / "probe_state.json"
    npath = scratch / "probe_state.npz"
    zpath = scratch / "probe_state_z.npz"

    def w_json() -> None:
        jpath.write_text(json.dumps(body, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    def w_npz() -> None:
        np.savez(npath, **enc.arrays)

    def w_npz_z() -> None:
        np.savez_compressed(zpath, **enc.arrays)

    def r_json() -> None:
        json.loads(jpath.read_text(encoding="utf-8"))

    def r_npz() -> None:
        with np.load(npath, allow_pickle=False) as z:
            for k in z.files:
                z[k]

    def r_npz_z() -> None:
        with np.load(zpath, allow_pickle=False) as z:
            for k in z.files:
                z[k]

    payload = pickle.dumps(doc, protocol=5)

    def w_pkl() -> None:
        pickle.dumps(doc, protocol=5)

    def r_pkl() -> None:
        pickle.loads(payload)

    times = {
        "pickle_dumps_s": _timeit(w_pkl), "pickle_loads_s": _timeit(r_pkl),
        "encode_tree_s": round(t_encode, 4),
        "json_write_s": _timeit(w_json), "json_read_s": _timeit(r_json),
        "npz_write_s": _timeit(w_npz), "npz_read_all_s": _timeit(r_npz),
        "npz_compressed_write_s": _timeit(w_npz_z, 3), "npz_compressed_read_all_s": _timeit(r_npz_z, 3),
        "read_state_total_s(今の読み口・検査込み・1 回)": round(t_read_full, 4),
    }
    times = {k: round(v, 4) for k, v in times.items()}
    with zipfile.ZipFile(npath) as zf:
        npz_members = len(zf.namelist())
    nd_total = sum(int(x.nbytes) for x in enc.arrays.values())
    sizes = {
        "pickle_file_bytes(先頭の行を含む)": file_bytes,
        "pickle_payload_bytes": len(payload),
        "soa_array_bytes": soa_bytes,
        "items_array_bytes(items の中の ndarray)": nd_bytes_items,
        "all_array_bytes": nd_total,
        "npz_bytes": npath.stat().st_size,
        "npz_compressed_bytes": zpath.stat().st_size,
        "npz_members": npz_members,
        "json_bytes": len(js_text.encode("utf-8")),
        "npz+json_bytes": npath.stat().st_size + len(js_text.encode("utf-8")),
        "npz_compressed+json_bytes": zpath.stat().st_size + len(js_text.encode("utf-8")),
    }
    out = {
        "schema": "10f/state_format_probe/1",
        "state_file": sp.name,
        "header_platform": b.header.get("platform"),
        "ledger_version": b.header.get("ledger_version"),
        "n_items": len(b.items),
        "n_inflight": len(b.inflight),
        "soa": soa_rows,
        "items_by_class": dict(by_class),
        "items_pickle_bytes_by_class": dict(bytes_by_class),
        "types_inside_items_top": dict(cls_total.most_common(40)),
        "sizes": sizes,
        "times_median_s": times,
        "shared_objects_n": len(shared),
        "shared_objects_touching_items": shared_items_only[:40],
        "items_top": rows[:40],
        "items_all": rows,
    }
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"sizes": sizes, "times": times, "by_class": dict(by_class),
                      "shared": len(shared), "shared_items": len(shared_items_only)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
