"""R-100 A7: ペルソナプール(data/persona_pool_v2)の全欄の棚卸し。読むだけ。

全 1,000,000 行を読む(標本ではなく全数)。入れ子の dict(traits・shift_pattern・
duty_pattern)は「親.子」の名前に平らにして数える。

出力: 標準出力に要約、data/research_cache/r100/a7_pool_fields.json に全表。
名前(name)と persona の値は出さない(name は異なり数だけ・persona は長さと型だけ。
例は名前と年齢を伏せ字にして 3 件まで)。

実行: .venv/Scripts/python.exe docs/research/scripts/r100/a7_pool_fields.py
"""

from __future__ import annotations

import json
import re
import sys
from array import array
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
POOL = ROOT / "data" / "persona_pool_v2"
OUT = ROOT / "data" / "research_cache" / "r100" / "a7_pool_fields.json"
LAYERS = ("L1", "L2", "L3", "L4", "L5")
NO_COUNTER = {"id", "name", "persona", "household_id"}  # 値の頻度を取らない欄
TOP = 12


def flatten(d: dict, prefix: str = "") -> dict:
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out[key] = "<dict>"
            out.update(flatten(v, key + "."))
        else:
            out[key] = v
    return out


def tname(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    if isinstance(v, list):
        return "list"
    return type(v).__name__


def quantiles(a: array) -> dict:
    if not a:
        return {}
    s = sorted(a)
    n = len(s)

    def q(p):
        return s[min(n - 1, int(p * (n - 1) + 0.5))]

    return {"n": n, "min": s[0], "p05": q(0.05), "p25": q(0.25), "p50": q(0.5),
            "p75": q(0.75), "p95": q(0.95), "max": s[-1], "mean": sum(s) / n}


def mask_persona(text: str, name: str, age) -> str:
    t = text.replace(name, "〈名前〉") if name else text
    t = re.sub(r"\d+歳", "〈年齢〉歳", t)
    return t


def main() -> None:
    per_layer: dict[str, dict] = {}
    overall_rows = 0
    for L in LAYERS:
        files = sorted((POOL / L).glob("part-*.jsonl"))
        n = 0
        present = Counter()
        types: dict[str, Counter] = defaultdict(Counter)
        cats: dict[str, Counter] = defaultdict(Counter)
        nums: dict[str, array] = defaultdict(lambda: array("d"))
        empty_str = Counter()
        names = set()
        persona_len = array("d")
        persona_sent = Counter()
        persona_examples = []
        persona_templates = Counter()
        for f in files:
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    n += 1
                    flat = flatten(d)
                    for k, v in flat.items():
                        present[k] += 1
                        tn = tname(v) if v != "<dict>" else "dict"
                        types[k][tn] += 1
                        if v == "":
                            empty_str[k] += 1
                        if tn in ("int", "float"):
                            nums[k].append(float(v))
                        if k in NO_COUNTER:
                            continue
                        if tn in ("str", "bool", "null"):
                            cats[k][str(v)] += 1
                        elif tn == "int" and k in ("party_size",):
                            cats[k][str(v)] += 1
                        elif tn == "list":
                            cats[k][json.dumps(v, ensure_ascii=False)] += 1
                    names.add(d.get("name"))
                    p = d.get("persona") or ""
                    persona_len.append(len(p))
                    persona_sent[p.count("。")] += 1
                    m = mask_persona(p, d.get("name") or "", d.get("age"))
                    # 型: 職業名・住まい・趣味などを残したまま、名前と年齢だけ伏せた文の頻度
                    persona_templates[m] += 1
                    if len(persona_examples) < 3 and n in (1, 1001, 20001):
                        persona_examples.append(m)
        overall_rows += n
        fields = {}
        for k in sorted(present, key=lambda x: (x.count("."), x)):
            fd = {
                "present": present[k],
                "missing_rate": round(1 - present[k] / n, 6),
                "types": dict(types[k]),
                "null_rate": round(types[k].get("null", 0) / n, 6),
                "empty_str_rate": round(empty_str[k] / n, 6),
            }
            if k in nums and len(nums[k]):
                fd["quantiles"] = quantiles(nums[k])
            if k in cats:
                c = cats[k]
                fd["distinct"] = len(c)
                fd["top"] = [[v, cnt, round(cnt / n, 4)] for v, cnt in c.most_common(TOP)]
            fields[k] = fd
        per_layer[L] = {
            "rows": n,
            "files": [p.name for p in files],
            "fields": fields,
            "name_distinct": len(names),
            "persona_len": quantiles(persona_len),
            "persona_sentences": dict(sorted(persona_sent.items())),
            "persona_distinct_after_masking_name_age": len(persona_templates),
            "persona_top_masked": [[t, c] for t, c in persona_templates.most_common(3)],
            "persona_examples_masked": persona_examples,
        }
        print(f"{L}: rows={n} fields={len(fields)} name_distinct={len(names)}", flush=True)
    all_fields = sorted({k for L in per_layer for k in per_layer[L]["fields"]},
                        key=lambda x: (x.count("."), x))
    matrix = {k: {L: per_layer[L]["fields"].get(k, {}).get("present", 0) for L in LAYERS}
              for k in all_fields}
    out = {"rows_total": overall_rows, "fields_union": all_fields,
           "presence_matrix": matrix, "layers": per_layer}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total rows", overall_rows, "fields(union, flattened)", len(all_fields))
    top_level = [k for k in all_fields if "." not in k]
    print("top-level fields", len(top_level))
    for k in all_fields:
        print(k, matrix[k])
    bs = [k for k in all_fields if re.search(r"story|back|bio|history|memory|生い立ち|経歴", k)]
    print("backstory-like keys:", bs)


if __name__ == "__main__":
    sys.exit(main())
