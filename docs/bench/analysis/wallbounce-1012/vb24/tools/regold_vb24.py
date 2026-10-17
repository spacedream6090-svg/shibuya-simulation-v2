"""第 2 期 2-4: 既定を変えた段で落ちる golden の定数を ``goldens_vb24.py all`` の値に張り替える(段ごとに 1 回)。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/regold_vb24.py --goldens <作業用>/goldens_V1.json --stage V1 \
        [--dry-run]

張り替える定数(試験のファイル → 定数 → ``goldens_vb24.CONFIGS`` の名)は下の ``TARGETS``。前の値は各行の末尾の注
``# 〔2-4 <段>〕前 <値>`` に残す(同じ行に前の段の注があれば足していく)。値が同じなら触らない。張り替えた一覧を出す
(記録の「張り替えた golden」の表)。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
REPO = HERE.parents[6]

#: (ファイル, 行を見つける正規表現(1 つ目の群=値の文字列), goldens の名, 欄 "final16"|"final"|"calls")
TARGETS: list[tuple[str, str, str, str]] = [
    ("tests/engine/test_presence_executor.py", r'"null_arm_final": "([0-9a-f]+)"', "pe_null", "final16"),
    ("tests/engine/test_presence_executor.py", r'"null_arm_final": "[0-9a-f]+", "null_arm_llm_calls": ([0-9_]+)', "pe_null", "calls"),
    ("tests/engine/test_presence_executor.py", r'"null_arm_final_leave_off": "([0-9a-f]+)"', "pe_null_leave", "final16"),
    ("tests/engine/test_presence_executor.py", r'"null_arm_llm_calls_leave_off": ([0-9_]+)', "pe_null_leave", "calls"),
    ("tests/engine/test_presence_executor.py", r'"null_arm_final_hunger_v1": "([0-9a-f]+)"', "pe_null_hv1", "final16"),
    ("tests/engine/test_presence_executor.py", r'"null_arm_llm_calls_hunger_v1": ([0-9_]+)', "pe_null_hv1", "calls"),
    ("tests/engine/test_presence_executor.py", r'"null_arm_final_l4x1": "([0-9a-f]+)"', "pe_null_l4x1", "final16"),
    ("tests/engine/test_presence_executor.py", r'"null_arm_llm_calls_l4x1": ([0-9_]+)', "pe_null_l4x1", "calls"),
    ("tests/engine/test_presence_executor.py", r'"v3_default_final": "([0-9a-f]+)"', "pe_v3", "final16"),
    ("tests/engine/test_presence_executor.py", r'"v3_default_llm_calls": ([0-9_]+)', "pe_v3", "calls"),
    ("tests/engine/test_presence_executor.py", r'"v3_default_final_leave_off": "([0-9a-f]+)"', "pe_v3_leave", "final16"),
    ("tests/engine/test_presence_executor.py", r'"v3_default_llm_calls_leave_off": ([0-9_]+)', "pe_v3_leave", "calls"),
    ("tests/engine/test_presence_executor.py", r'"v3_default_final_hunger_v1": "([0-9a-f]+)"', "pe_v3_hv1", "final16"),
    ("tests/engine/test_presence_executor.py", r'"v3_default_llm_calls_hunger_v1": ([0-9_]+)', "pe_v3_hv1", "calls"),
    ("tests/engine/test_presence_executor.py", r'"v3_default_final_l4x1": "([0-9a-f]+)"', "pe_v3_l4x1", "final16"),
    ("tests/engine/test_presence_executor.py", r'"v3_default_llm_calls_l4x1": ([0-9_]+)', "pe_v3_l4x1", "calls"),
    ("tests/engine/test_state_ledger_10b.py", r'^T7_V3_FINAL = "([0-9a-f]+)"', "pe_v3", "final16"),
    ("tests/engine/test_state_checks_10f.py", r'^K19_V3_FINAL_COUNTER = "([0-9a-f]+)"', "pe_v3", "final16"),
    ("tests/engine/test_intent_chooser.py", r'assert v3\.final_hash\.startswith\("([0-9a-f]+)"\) and int\(v3\.llm_calls\) == [0-9_]+',
     "q13_v3", "final16"),
    ("tests/engine/test_intent_chooser.py", r'assert v3\.final_hash\.startswith\("[0-9a-f]+"\) and int\(v3\.llm_calls\) == ([0-9_]+)',
     "q13_v3", "calls"),
    ("tests/engine/test_intent_chooser.py", r'assert null\.final_hash\.startswith\("([0-9a-f]+)"\) and int\(null\.llm_calls\) == [0-9_]+',
     "q13_null", "final16"),
    ("tests/engine/test_intent_chooser.py", r'assert null\.final_hash\.startswith\("[0-9a-f]+"\) and int\(null\.llm_calls\) == ([0-9_]+)',
     "q13_null", "calls"),
    ("tests/engine/proximity/test_runs.py", r'^HEAD_GOLDEN = \("([0-9a-f]+)", [0-9_]+\)', "prox_cell300", "final"),
    ("tests/engine/proximity/test_runs.py", r'^HEAD_GOLDEN = \("[0-9a-f]+", ([0-9_]+)\)', "prox_cell300", "calls"),
    ("tests/perception/test_near_tiebreak.py", r'"hash": \("([0-9a-f]+)", [0-9_]+\)', "nt_hash", "final"),
    ("tests/perception/test_near_tiebreak.py", r'"hash": \("[0-9a-f]+", ([0-9_]+)\)', "nt_hash", "calls"),
    ("tests/perception/test_near_tiebreak.py", r'"hash_order_id": \("([0-9a-f]+)", [0-9_]+\)', "nt_mid", "final"),
    ("tests/perception/test_near_tiebreak.py", r'"hash_order_id": \("[0-9a-f]+", ([0-9_]+)\)', "nt_mid", "calls"),
    ("tests/perception/test_near_tiebreak.py", r'"classical_tie_id": \("([0-9a-f]+)", [0-9_]+\)', "nt_old", "final"),
    ("tests/perception/test_near_tiebreak.py", r'"classical_tie_id": \("[0-9a-f]+", ([0-9_]+)\)', "nt_old", "calls"),
    ("tests/engine/test_classical_social.py", r'GE\.PLATFORM_10F: \("([0-9a-f]+)", [0-9_]+\),', "cs_acq", "final"),
    ("tests/engine/test_classical_social.py", r'GE\.PLATFORM_10F: \("[0-9a-f]+", ([0-9_]+)\),', "cs_acq", "calls"),
    ("tests/engine/test_relations_tenure.py", r'\("v1", "behavior"\): \("([0-9a-f]+)", [0-9_]+\)', "rel_v1", "final16"),
    ("tests/engine/test_relations_tenure.py", r'\("v1", "behavior"\): \("[0-9a-f]+", ([0-9_]+)\)', "rel_v1", "calls"),
    ("tests/engine/test_relations_tenure.py", r'\("v2", "behavior"\): \("([0-9a-f]+)", [0-9_]+\)', "rel_v2", "final16"),
    ("tests/engine/test_relations_tenure.py", r'\("v2", "behavior"\): \("[0-9a-f]+", ([0-9_]+)\)', "rel_v2", "calls"),
    # 10f の golden の表の見張り(上の値の写し)
    ("tests/engine/test_env_and_sections_10f.py",
     r'\(g\["v3_default_final"\], g\["v3_default_llm_calls"\]\) == \("([0-9a-f]+)", [0-9_]+\)', "pe_v3", "final16"),
    ("tests/engine/test_env_and_sections_10f.py", r'\(g\["v3_default_final"\], g\["v3_default_llm_calls"\]\) == \("[0-9a-f]+", ([0-9_]+)\)',
     "pe_v3", "calls"),
    ("tests/engine/test_env_and_sections_10f.py", r'\(g\["null_arm_final"\], g\["null_arm_llm_calls"\]\) == \("([0-9a-f]+)", [0-9_]+\)',
     "pe_null", "final16"),
    ("tests/engine/test_env_and_sections_10f.py", r'\(g\["null_arm_final"\], g\["null_arm_llm_calls"\]\) == \("[0-9a-f]+", ([0-9_]+)\)',
     "pe_null", "calls"),
    ("tests/engine/test_env_and_sections_10f.py", r'\[\("v1", "behavior"\)\] == \("([0-9a-f]+)", [0-9_]+\)', "rel_v1", "final16"),
    ("tests/engine/test_env_and_sections_10f.py", r'\[\("v1", "behavior"\)\] == \("[0-9a-f]+", ([0-9_]+)\)', "rel_v1", "calls"),
    ("tests/engine/test_env_and_sections_10f.py", r'\[\("v2", "behavior"\)\] == \("([0-9a-f]+)", [0-9_]+\)', "rel_v2", "final16"),
    ("tests/engine/test_env_and_sections_10f.py", r'\[\("v2", "behavior"\)\] == \("[0-9a-f]+", ([0-9_]+)\)', "rel_v2", "calls"),
]


def _fmt_calls(n: int) -> str:
    return f"{n:_}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--goldens", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    g = json.loads(Path(a.goldens).read_text(encoding="utf-8"))["runs"]
    texts: dict[str, str] = {}
    changed: list[tuple[str, str, str, str]] = []
    for rel, pat, name, field in TARGETS:
        p = REPO / rel
        t = texts.setdefault(rel, p.read_text(encoding="utf-8"))
        m = re.search(pat, t, re.M)
        if m is None:
            raise SystemExit(f"見つからない: {rel} {pat}")
        old = m.group(1)
        row = g[name]
        if "error" in row:
            raise SystemExit(f"{name}: {row['error'][-300:]}")
        new = _fmt_calls(int(row["calls"])) if field == "calls" else str(row[field])
        if field != "calls" and len(old) != len(new):  # 先頭 16 桁か全桁かは前の値の長さに合わせる
            new = str(row["final"])[: len(old)]
        if old.replace("_", "") == new.replace("_", ""):
            continue
        t = t[: m.start(1)] + new + t[m.end(1):]
        # 行末の注(同じ段の注が既にあれば前の値を足す)
        e = t.index("\n", m.start(1))
        tag = f"  # 〔2-4 {a.stage}〕前 "
        line_start = t.rindex("\n", 0, m.start(1)) + 1
        line = t[line_start:e]
        if tag.strip() in line:
            t = t[:e] + " / " + old + t[e:]
        else:
            t = t[:e] + tag + old + t[e:]
        texts[rel] = t
        changed.append((rel, name, old, new))
    for rel, name, old, new in changed:
        print(f"{rel} | {name} | {old} → {new}")
    if not a.dry_run:
        for rel, t in texts.items():
            (REPO / rel).write_text(t, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
