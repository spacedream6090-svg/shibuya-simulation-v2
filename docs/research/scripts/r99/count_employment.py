"""R-99 A3: count values of employment-related fields in the persona pool (read only).

Usage: python docs/research/scripts/r99/count_employment.py
Reads data/persona_pool_v2/L*/part-*.jsonl and prints counts. Writes nothing.
"""
import collections
import glob
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
FIELDS = ["employment", "rank", "workplace_scope", "presence", "shift_pattern", "work_days"]

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "persona_pool_v2", "L*", "part-*.jsonl")))
    total = 0
    by_layer = collections.Counter()
    counts = {f: collections.Counter() for f in FIELDS}
    emp_by_layer = collections.defaultdict(collections.Counter)
    emp_by_ind = collections.defaultdict(collections.Counter)
    emp_by_occ = collections.defaultdict(collections.Counter)
    l2_by_ind = collections.defaultdict(collections.Counter)
    keys = collections.Counter()
    for fp in files:
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                total += 1
                lay = r.get("layer")
                by_layer[lay] += 1
                for k in r.keys():
                    keys[k] += 1
                for f in FIELDS:
                    v = r.get(f, "<absent>")
                    if isinstance(v, (list, dict)):
                        v = json.dumps(v, ensure_ascii=False)[:60]
                    counts[f][v] += 1
                e = r.get("employment", "<absent>")
                emp_by_layer[lay][e] += 1
                emp_by_ind[r.get("industry_major", "<absent>")][e] += 1
                emp_by_occ[r.get("occupation_major", "<absent>")][e] += 1
                if lay == "L2":
                    l2_by_ind[r.get("industry_major", "<absent>")][e] += 1
    print("TOTAL", total)
    print("LAYERS", dict(by_layer))
    print("KEYS", dict(keys))
    for f in FIELDS:
        print("==", f, "distinct", len(counts[f]))
        for v, c in counts[f].most_common(15):
            print("   ", repr(v), c)
    print("== employment by layer")
    for lay in sorted(emp_by_layer, key=str):
        print("   ", lay, dict(emp_by_layer[lay]))
    print("== employment by industry_major")
    for ind, c in sorted(emp_by_ind.items(), key=lambda x: -sum(x[1].values())):
        print("   ", ind, sum(c.values()), dict(c))
    print("== L2 (workday_shift) employment share by industry_major")
    for ind, c in sorted(l2_by_ind.items(), key=lambda x: -sum(x[1].values())):
        n = sum(c.values())
        print("   ", ind, n, {k: round(v / n * 100, 1) for k, v in c.items()})
    print("== employment by occupation_major")
    for ind, c in sorted(emp_by_occ.items(), key=lambda x: -sum(x[1].values())):
        print("   ", ind, sum(c.values()), dict(c))

if __name__ == "__main__":
    main()
