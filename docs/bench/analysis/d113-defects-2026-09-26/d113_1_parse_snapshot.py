# -*- coding: utf-8 -*-
"""D-113 ① の計測: 既存テープの応答を現行パーサで全行パースし、呼ごとの結果を保存する。
使い方: python d113_parse_snapshot.py <tag>   → scratchpad/d113_parse_<tag>.parquet + _<tag>_summary.json
修正前に tag=before、修正後に tag=after で走らせ、d113_parse_diff.py で突き合わせる。"""
import sys, io, json, glob, os, re, time
import pyarrow as pa, pyarrow.parquet as pq
sys.path.insert(0, "src")
from shibuya.llm.parser import parse_two_line, LABEL_ALIASES
tag = sys.argv[1]
SP = os.path.dirname(os.path.abspath(__file__))
tapes = sorted(glob.glob("data/tape/c8_ab8_s1/*/calls.parquet") + glob.glob("data/tape/c8_ab6c_s1/*/calls.parquet"))
COLON_TOKEN = re.compile(r"^[^\s:：]{1,10}[:：]$")
rows = {k: [] for k in ("tape","call_id","action","target_raw","format_ok","strict_format_ok","positional_used","errors","reason","comment")}
summary = {}
t0 = time.time()
for p in tapes:
    name = p.split(os.sep)[-2] if os.sep in p else p.split("/")[-2]
    t = pq.read_table(p, columns=["call_id","response","deferred"])
    resp = t.column("response").to_pylist(); cid = t.column("call_id").to_pylist(); dfr = t.column("deferred").to_pylist()
    n=0; colon_target=0; unknown_label_in_action=0
    for c, r, d in zip(cid, resp, dfr):
        if d or not r: continue
        n += 1
        pr = parse_two_line(r, "v1")
        traw = pr.target.raw if pr.target is not None else ""
        rows["tape"].append(name); rows["call_id"].append(str(c)); rows["action"].append(pr.action or "")
        rows["target_raw"].append(traw or ""); rows["format_ok"].append(bool(pr.format_ok)); rows["strict_format_ok"].append(bool(pr.strict_format_ok))
        rows["positional_used"].append(bool(pr.positional_used)); rows["errors"].append("|".join(pr.errors)); rows["reason"].append(pr.reason or ""); rows["comment"].append(pr.comment or "")
        if traw and COLON_TOKEN.match(traw.strip()): colon_target += 1
        if any(COLON_TOKEN.match(tok) and tok.rstrip(":：") not in LABEL_ALIASES for tok in pr.raw_action.split()): unknown_label_in_action += 1
    summary[name] = {"parsed": n, "target_is_colon_token": colon_target, "unknown_label_token_in_action_field": unknown_label_in_action}
    print(name, summary[name], f"{time.time()-t0:.0f}s", flush=True)
pq.write_table(pa.table(rows), os.path.join(SP, f"d113_parse_{tag}.parquet"))
json.dump(summary, io.open(os.path.join(SP, f"d113_parse_{tag}_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", tag, f"{time.time()-t0:.0f}s")
