# -*- coding: utf-8 -*-
"""語彙 v3 の候補抽出: 全テープ(28 本)から (A) 語彙外の行動語(未定義/辞書写像) (B) 対象欄の自由記述
(C) 書式失敗 を呼ごとに取り、表層ごとの件数・体数・腕数を集計する。出力は scratchpad の JSON。
使い方: python v3_extract.py <out.json>"""
import sys, io, json, glob, os, re, time, unicodedata, collections
import pyarrow.parquet as pq
sys.path.insert(0, "src")
from shibuya.llm.parser import parse_two_line
from shibuya.llm.undefined import map_synonym
from shibuya.llm.contract import TargetKind, NO_TARGET

out_path = sys.argv[1]
t0 = time.time()

# ---- W6 の店名(対象欄の名指し判定・B2 に見える名の判定)
poi = pq.read_table("data/world/v2/w6_poi.parquet", columns=["poi_id", "name", "cat", "place_id"]).to_pydict()
name_cells = collections.defaultdict(set)   # name -> set(place_id)
name_cat = {}
for nm, cat, pid in zip(poi["name"], poi["cat"], poi["place_id"]):
    nm = unicodedata.normalize("NFKC", str(nm)).strip()
    if len(nm) < 2:
        continue
    name_cells[nm].add(str(pid))
    name_cat.setdefault(nm, cat)
names_by_len = sorted(name_cells, key=len, reverse=True)
names3 = [n for n in names_by_len if len(n) >= 3]
PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")

def arm_of(path):
    p = path.replace("\\", "/")
    run = p.split("/")[2]; arm = p.split("/")[3]
    ver = "v2" if arm.endswith("_v2") else "v1"
    if "__open" in arm: mode = "open"
    elif "__hint" in arm: mode = "hint"
    else: mode = "vocab"
    return run, arm, mode, ver

tapes = sorted(glob.glob("data/tape/c8_*/*/calls.parquet"))
SUF = ("の店頭", "の店", "店頭", "へ", "に", "まで", "の")

def norm_target(s):
    s = unicodedata.normalize("NFKC", s).strip().strip("「」『』\"'。、.,")
    return s

def match_name(s):
    """対象欄の表層 → 店名(完全一致 or 3 字以上の店名を含む)。"""
    if s in name_cells:
        return s
    for suf in SUF:
        if s.endswith(suf) and s[: -len(suf)] in name_cells:
            return s[: -len(suf)]
    for n in names3:
        if n in s:
            return n
    return None

# 集計器: key -> {calls, agents:set, arms:set, samples:list}
def bucket():
    return {"calls": 0, "agents": set(), "arms": set(), "samples": []}
undefined = collections.defaultdict(bucket)     # 語彙外の行動語(辞書でも救えない)
dict_mapped = collections.defaultdict(bucket)   # 語彙外だが段0 辞書で写せる語: key=(surface, mapped)
target_free = collections.defaultdict(bucket)   # 対象欄の自由記述(店名でない ITEM_CATEGORY): key=(action, target)
target_named = collections.defaultdict(bucket)  # 対象欄が店名: key=(action, name, where)  where in {in_cell, in_b2_text, elsewhere}
target_kinds = collections.Counter()            # (mode, action, kind) の件数
fail = collections.defaultdict(bucket)          # 書式失敗: key=error signature
per_arm = {}
reason_undefined = collections.Counter()

def add(b, aid, arm, sample=None):
    b["calls"] += 1; b["agents"].add(aid); b["arms"].add(arm)
    if sample is not None and len(b["samples"]) < 3:
        b["samples"].append(sample)

for p in tapes:
    run, arm, mode, ver = arm_of(p)
    key = f"{run}/{arm}"
    blocks = pq.read_table(p.replace("calls.parquet", "blocks.parquet"), columns=["block_id", "text"]).to_pydict()
    btext = dict(zip(blocks["block_id"], blocks["text"]))
    b2cache = {}
    def b2_info(bids):
        for bid in bids:
            if bid in b2cache:
                return b2cache[bid]
            tx = btext.get(bid, "")
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                cell = m.group(1) if m else ""
                seen = tuple(n for n in names3 if n in tx)
                b2cache[bid] = (cell, seen)
                return b2cache[bid]
        return ("", ())
    t = pq.read_table(p, columns=["call_id", "agent_id", "response", "deferred", "block_ids"])
    resp = t.column("response").to_pylist(); aid = t.column("agent_id").to_pylist()
    dfr = t.column("deferred").to_pylist(); bids = t.column("block_ids").to_pylist()
    n = 0; n_fail = 0; n_undef = 0; n_dict = 0; n_free = 0; n_named = 0
    for r, a, d, bl in zip(resp, aid, dfr, bids):
        if d or not r:
            continue
        n += 1
        pr = parse_two_line(r, ver)
        # ---- (C) 書式失敗
        if not pr.format_ok:
            n_fail += 1
            sig = "|".join(e.split(":")[0] for e in pr.errors if not e.startswith("positional") and not e.startswith("unknown_label"))
            add(fail[sig], a, key, r[:160])
        # ---- (A) 語彙外の行動語
        if pr.action is None:
            raw = unicodedata.normalize("NFKC", pr.raw_action).strip()
            word = raw.split()[0] if raw else "(空)"
            cand = map_synonym(raw, None, ver)[0] if raw else None
            if cand:
                n_dict += 1
                add(dict_mapped[(word, cand)], a, key, r[:120])
            else:
                n_undef += 1
                add(undefined[word], a, key, r[:120])
                reason_undefined[(word, pr.raw_reason[:30])] += 1
        act = pr.action or "(未定義)"
        # ---- (B) 対象欄
        tg = pr.target
        target_kinds[(mode, act, tg.kind.name)] += 1
        if tg.kind == TargetKind.ITEM_CATEGORY or tg.kind == TargetKind.STATION_OR_VEHICLE:
            s = norm_target(tg.raw)
            nm = match_name(s)
            if nm:
                n_named += 1
                cell, seen = b2_info(bl)
                if cell and cell in name_cells[nm]:
                    where = "in_cell"
                elif nm in seen:
                    where = "in_b2_text"
                else:
                    where = "elsewhere"
                add(target_named[(act, nm, where)], a, key, r[:120])
            else:
                n_free += 1
                add(target_free[(act, s)], a, key, r[:120])
    per_arm[key] = {"mode": mode, "vocab": ver, "parsed": n, "format_fail": n_fail, "undefined": n_undef,
                    "dict_mapped": n_dict, "target_free": n_free, "target_named": n_named}
    print(key, per_arm[key], f"{time.time()-t0:.0f}s", flush=True)

def dump(d, keyfmt):
    rows = []
    for k, b in d.items():
        rows.append({"key": keyfmt(k), "calls": b["calls"], "agents": len(b["agents"]), "arms": len(b["arms"]),
                     "arm_list": sorted(b["arms"]), "samples": b["samples"]})
    rows.sort(key=lambda x: (-x["agents"], -x["calls"]))
    return rows

res = {
    "per_arm": per_arm,
    "undefined": dump(undefined, lambda k: k),
    "dict_mapped": dump(dict_mapped, lambda k: f"{k[0]} -> {k[1]}"),
    "target_free": dump(target_free, lambda k: f"{k[0]} | {k[1]}"),
    "target_named": dump(target_named, lambda k: f"{k[0]} | {k[1]} | {k[2]}"),
    "target_kinds": [{"mode": k[0], "action": k[1], "kind": k[2], "calls": v} for k, v in sorted(target_kinds.items(), key=lambda kv: -kv[1])],
    "fail": dump(fail, lambda k: k),
    "reason_undefined": [{"word": k[0], "reason": k[1], "calls": v} for k, v in reason_undefined.most_common(400)],
}
json.dump(res, io.open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", f"{time.time()-t0:.0f}s", "undefined", len(undefined), "dict", len(dict_mapped), "free", len(target_free), "named", len(target_named))
