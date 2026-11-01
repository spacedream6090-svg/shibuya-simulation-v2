"""1-0: manifest(``cli.checkpoints_payload`` の JSON)が HEAD と同じか。10f の ``manifest_check_10f.py`` の ``side``(7 本=
既定 v3 の seed 1・2・帰無腕・記憶+関係の seed 1・2・古典+記憶+関係の seed 1・2・5,000 体・世界資産・1 日)をそのまま使い、
比べ方だけを 1-0 の形にする(1-0 は manifest に欄を足さない=全部の欄を比べる。壁時計の欄だけ除く)。

使い方(リポの根で・``$W`` は作業用の置き場・両側とも ``PYTHONHASHSEED=0``=成長の検査の行の並びが文字列のハッシュの
種で揺れるため=§5-3)::

    PYTHONHASHSEED=0 python docs/bench/analysis/wallbounce-1006/10f/manifest_check_10f.py side --src <HEAD の src> --label head --scratch $W
    PYTHONHASHSEED=0 python docs/bench/analysis/wallbounce-1006/10f/manifest_check_10f.py side --label work --scratch $W
    python $D/manifest_check_1_0.py --scratch $W --out $D/manifest_check.json

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RUNS = (("w6_v3_default", 1), ("w6_v3_default", 2), ("w6_golden_null_arm", 1), ("v3_mem_rel", 1), ("v3_mem_rel", 2),
        ("v3_classical_mem_rel", 1), ("v3_classical_mem_rel", 2))
#: 壁時計の欄(決定論でない=比べない)。10f の NONDET に、manifest の秒の欄を足した。
NONDET_PREFIX = ("relations.wall_seconds_nondeterministic", "relations.init.init_seconds_nondeterministic")


def _flat(d: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flat(v, f"{prefix}{k}."))
    else:
        out[prefix[:-1]] = json.dumps(d, ensure_ascii=False, sort_keys=True)
    return out


#: 環境の欄(どのコードで回したか=git の commit と汚れ・env_id)。HEAD は本体の commit・1-0 は commit 前の作業木なので必ず違う。
ENV_FIELDS = ("env_id", "environment.code.git_commit", "environment.code.git_diff_sha256", "environment.code.git_dirty",
              "environment.env_id")


def _env(k: str) -> bool:
    k = k[len("manifest."):] if k.startswith("manifest.") else k
    return k in ENV_FIELDS


def _nondet(k: str) -> bool:
    k = k[len("manifest."):] if k.startswith("manifest.") else k
    last = k.rsplit(".", 1)[-1]
    return (any(k.startswith(p) for p in NONDET_PREFIX) or "seconds" in last or last in ("wall_s", "tick_ms_max")
            or k.startswith("phase_seconds") or k.startswith("process_seconds") or k.startswith("resume.read_seconds")
            or k.startswith("resume.restore_seconds"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    scratch = Path(a.scratch)
    rows, ok = [], True
    for name, seed in RUNS:
        h = json.loads((scratch / f"man_head_{name}_s{seed}.json").read_text(encoding="utf-8"))
        w = json.loads((scratch / f"man_work_{name}_s{seed}.json").read_text(encoding="utf-8"))
        fh = {k: v for k, v in _flat(h).items() if not _nondet(k)}
        fw = {k: v for k, v in _flat(w).items() if not _nondet(k)}
        moved_all = sorted(k for k in set(fh) | set(fw) if fh.get(k) != fw.get(k))
        env_moved = [k for k in moved_all if _env(k)]
        moved = [k for k in moved_all if not _env(k)]
        skipped = sorted({k for k in _flat(h) if _nondet(k)})
        top_same = list(h.get("manifest", {})) == list(w.get("manifest", {}))
        # 壁時計の欄も鍵の集合は比べる(系ごとの計時を足しても phase の鍵の集合は変えない=草案 §3-3 の 22)
        keys_same = set(_flat(h)) == set(_flat(w))
        rows.append({"config": name, "seed": seed, "final_head": h["final_hash"][:16], "final_work": w["final_hash"][:16],
                     "fields_compared": len(fh), "fields_differ": moved, "environment_fields_differ": env_moved, "top_level_order_same": top_same,
                     "all_keys_same_including_wall_clock": keys_same, "skipped_wall_clock_fields": len(skipped)})
        ok &= h["final_hash"] == w["final_hash"] and not moved and top_same and keys_same
    doc = {"schema": "shibuya.bench/1-0/manifest-check/1", "agents": 5000, "world": "data/world/v2",
           "how": "HEAD(本体の src)と 1-0 の作業木で同じ 7 本を回し、checkpoints の JSON を平坦化した全部の欄を比べる(壁時計の欄は除く)",
           "all_ok": bool(ok), "rows": rows}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_ok": ok, "rows": [(r["config"], r["seed"], len(r["fields_differ"]), r["fields_compared"])
                                              for r in rows]}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
