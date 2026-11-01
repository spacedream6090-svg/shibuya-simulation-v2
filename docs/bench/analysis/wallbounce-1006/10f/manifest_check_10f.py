"""10f 第 1 段の記録: manifest の「環境の欄を抜いた形」が HEAD と同じか、と seed の交換可能性の前後。

mock 5,000 体・世界資産・1 シミュ日。構成は 10b の wave2 の表(``byte_check_10b.py``)から引く。

- ``one``: 1 本回して checkpoints の JSON(``cli.checkpoints_payload``)を書く(``--src`` を渡すと HEAD の写しで回す)。
- ``side``: 構成 × seed をサブプロセスで回す。
- ``compare``: (1) HEAD と作業木の manifest を、作業木から 10f の 3 欄(``env_id``・``environment``・
  ``manifest_sections``)を抜いて比べる(壁時計の欄 ``relations.wall_seconds_nondeterministic`` は除く)。
  (2) ``tools/c7/seed_exchangeability.py`` で既定 v3・記憶+関係・classical+記憶+関係の seed 1 と 2 を比べる
  (HEAD の manifest=前・作業木=後。関係の 2 構成は関係の初期化が実際に走る=検収 N1)。
- ``hashes``: byte-check の両側の JSON から最後の checkpoint の behavior/full-hash を拾い、byte-check の記録に足す。

使い方(リポのルートで・``$W`` は作業用の短いディレクトリ・HEAD の写しは 10c の手順で展開)::

    python $D/manifest_check_10f.py side --src $W/head_src/src --label head --scratch $W --jobs 4
    python $D/manifest_check_10f.py side --label work --scratch $W --jobs 4
    python $D/manifest_check_10f.py compare --scratch $W --out $D/manifest_check.json

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
B10 = REPO / "docs" / "bench" / "analysis" / "wallbounce-1003" / "10b" / "byte_check_10b.py"
NEW_KEYS = ("env_id", "environment", "manifest_sections")
#: 壁時計の欄(決定論でない=比べない)。
NONDET = ("relations.wall_seconds_nondeterministic", "relations.init.init_seconds_nondeterministic")
RUNS = (("w6_v3_default", 1), ("w6_v3_default", 2), ("w6_golden_null_arm", 1), ("v3_mem_rel", 1), ("v3_mem_rel", 2),
        ("v3_classical_mem_rel", 1), ("v3_classical_mem_rel", 2))
#: seed の交換可能性を比べる構成(関係の初期化が実際に走る 2 構成を含む=検収 N1)。
EXCH = ("w6_v3_default", "v3_mem_rel", "v3_classical_mem_rel")


def _wave2() -> Any:
    spec = importlib.util.spec_from_file_location("byte_check_10b", B10)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["byte_check_10b"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod._wave2()


def cmd_one(a: argparse.Namespace) -> int:
    from shibuya import cli

    kw = dict(_wave2().configs()[a.config])
    res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, **kw)
    doc = cli.checkpoints_payload(res, run_id=f"{a.config}_s{a.seed}")
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"config": a.config, "seed": a.seed, "final": res.final_hash[:16], "calls": int(res.llm_calls)}))
    return 0


def cmd_side(a: argparse.Namespace) -> int:
    scratch = Path(a.scratch)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if a.src:
        env["PYTHONPATH"] = str(Path(a.src).resolve())
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"

    def one(cs: tuple[str, int]) -> str:
        name, seed = cs
        out = scratch / f"man_{a.label}_{name}_s{seed}.json"
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--seed", str(seed),
               "--agents", str(a.agents), "--world", a.world, "--out", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        return r.stdout.strip().splitlines()[-1] if r.returncode == 0 else f"ERROR {name} s{seed}: {r.stderr[-800:]}"

    with cf.ThreadPoolExecutor(max_workers=int(a.jobs)) as ex:
        for line in ex.map(one, RUNS):
            print(line, flush=True)
    return 0


def _flat(d: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(_flat(v, f"{prefix}{k}."))
    else:
        out[prefix[:-1]] = json.dumps(d, ensure_ascii=False, sort_keys=True)
    return out


def cmd_compare(a: argparse.Namespace) -> int:
    sys.path.insert(0, str(REPO / "tools" / "c7"))
    import seed_exchangeability as sx

    scratch = Path(a.scratch)
    load = lambda label, name, seed: json.loads(  # noqa: E731
        (scratch / f"man_{label}_{name}_s{seed}.json").read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    ok = True
    for name, seed in RUNS:
        h, w = load("head", name, seed), load("work", name, seed)
        wm = {k: v for k, v in w["manifest"].items() if k not in NEW_KEYS}
        fh = {k: v for k, v in _flat(h["manifest"]).items() if not any(k.startswith(n) for n in NONDET)}
        fw = {k: v for k, v in _flat(wm).items() if not any(k.startswith(n) for n in NONDET)}
        moved = sorted(k for k in set(fh) | set(fw) if fh.get(k) != fw.get(k))
        new_present = [k for k in NEW_KEYS if k in w["manifest"]]
        top_order_same = list(h["manifest"]) == list(wm)
        rows.append({"config": name, "seed": seed, "final_head": h["final_hash"][:16], "final_work": w["final_hash"][:16],
                     "fields_compared": len(fh), "fields_differ": moved, "new_keys_present": new_present,
                     "top_level_order_same": top_order_same, "env_id": w["manifest"].get("env_id")})
        ok &= (h["final_hash"] == w["final_hash"]) and top_order_same and len(new_present) == 3
        # 状態のハッシュは O95 の分割で動く(予定どおり)。daily は日ごとの締めの後の 2 本だけが動くことを確かめる
        strip = lambda rows: [{k: v for k, v in r.items() if k != "state_hashes_end_of_day"} for r in rows]  # noqa: E731
        daily_other_same = strip(h["manifest"].get("daily", [])) == strip(wm.get("daily", []))
        rows[-1]["daily_same_except_state_hashes"] = daily_other_same
        ok &= daily_other_same and all(k.startswith("state_hashes") or k == "daily" for k in moved)
    ex: dict[str, Any] = {}
    for name in EXCH:
        ex[name] = {}
        for label in ("head", "work"):
            r = sx.compare([load(label, name, 1), load(label, name, 2)], ["s1", "s2"])
            e = {k: r[k] for k in ("mode", "exchangeable", "diff_observed_count", "unlisted",
                                   "environment_warning", "population_seed_independent")}
            e["unexplained_count"] = len(r["diff_unexplained"])
            e["unexplained_keys"] = [u["key"] for u in r["diff_unexplained"]][:40]
            e["unexplained_groups"] = sorted({u["key"].split(".")[1] if u["key"].startswith("manifest.")
                                              else u["key"] for u in r["diff_unexplained"]})
            e["allowed"] = [d["key"] for d in r["diff_allowed"]]
            ex[name][label] = e
        ok &= ex[name]["work"]["exchangeable"] is True
    doc = {"schema": "shibuya.bench/10f/manifest-check/1", "agents": 5000, "world": "data/world/v2",
           "how": ("HEAD(git archive の src)と作業木で同じ構成を回し、作業木の manifest から 10f の 3 欄を抜いて"
                   "平坦化した全部の欄を比べる(壁時計の欄は除く)。state_hashes の 2 本は O95 の分割で動く予定"),
           "all_ok": bool(ok), "rows": rows, "seed_exchangeability_s1_s2": ex}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False, indent=1)[:4000])
    return 0 if ok else 1


def cmd_hashes(a: argparse.Namespace) -> int:
    """byte-check の両側の JSON(``10c/byte_check_10c.py side``)から最後の checkpoint の behavior/full-hash を拾い、
    byte-check の記録に ``state_hashes_before``(HEAD)・``state_hashes_after``(作業木)として足す(検収 N8)。"""
    head = json.loads(Path(a.head).read_text(encoding="utf-8"))["runs"]
    work = json.loads(Path(a.work).read_text(encoding="utf-8"))["runs"]
    doc = json.loads(Path(a.byte_check).read_text(encoding="utf-8"))
    pick = lambda runs: {k: {"behavior_last": v.get("behavior_last"), "full_last": v.get("full_last")}  # noqa: E731
                         for k, v in sorted(runs.items())}
    doc["state_hashes_before"] = pick(head)
    doc["state_hashes_after"] = pick(work)
    doc["state_hashes_note"] = ("1 日・mock/classical 5,000 体・seed 1・テープつき・最後の checkpoint の先頭 16 桁。"
                                "10f の O95 の分割で全構成の値が変わる(final・呼数・テープは不変)。10e で比べるのは after")
    Path(a.byte_check).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    moved = [k for k in doc["state_hashes_after"] if doc["state_hashes_after"][k] != doc["state_hashes_before"].get(k)]
    print(f"configs={len(doc['state_hashes_after'])} moved={len(moved)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--config", required=True)
    o.add_argument("--seed", type=int, default=1)
    o.add_argument("--agents", type=int, default=5000)
    o.add_argument("--world", default="data/world/v2")
    o.add_argument("--out", required=True)
    s = sub.add_parser("side")
    s.add_argument("--src", default="")
    s.add_argument("--label", required=True)
    s.add_argument("--scratch", required=True)
    s.add_argument("--agents", type=int, default=5000)
    s.add_argument("--world", default="data/world/v2")
    s.add_argument("--jobs", type=int, default=4)
    c = sub.add_parser("compare")
    c.add_argument("--scratch", required=True)
    c.add_argument("--out", required=True)
    h = sub.add_parser("hashes")
    h.add_argument("--head", required=True)
    h.add_argument("--work", required=True)
    h.add_argument("--byte-check", required=True)
    a = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare, "hashes": cmd_hashes}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
