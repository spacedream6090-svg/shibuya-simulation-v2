# -*- coding: utf-8 -*-
"""batch_invariance_check.py — B14: vLLM のバッチ不変性(VLLM_BATCH_INVARIANT=1)の自検証と再現性テスト(サーバー・8B INT8・契約書v1サイズ)。
T6a 不変性: 同じ32プロンプト(温度0)を「単独(逐次)」と「他200件と混在(並行)」で送り、出力が一致する割合。
T6b 再現性(温度0.7・seed固定): 同一リクエストを2回(混在環境を変えて)送り、出力一致率。
T6c 版間: 同一プロンプト・同一seedの出力ハッシュを保存(後日の別版/別GPU比較用)。
入力=品質プローブv0の①②⑥v1(59問)から32本+充填用200本(⑥のv0/full)。
"""
import argparse, asyncio, json, hashlib, time, random, os, sys
import urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_probes(path):
    items = [json.loads(l) for l in open(path, encoding="utf-8")]
    core, fill = [], []
    for p in items:
        if p["family"] in (1, 2):
            core.append((p["id"], p["system_block"], p["observation"] + "\n" + p["question"]))
        elif p["family"] == 6:
            v = p["family6_variants"]
            core.append((p["id"] + "v1", v["v1"]["system_block"], v["v1"]["observation"] + "\n" + p["question"]))
            fill.append((p["id"] + "v0", v["v0"]["system_block"], v["v0"]["observation"] + "\n" + p["question"]))
            fill.append((p["id"] + "full", v["full"]["system_block"], v["full"]["observation"] + "\n" + p["question"]))
    return core, fill

async def call(session, url, model, sysb, userb, temperature, seed, max_tokens=64):
    import aiohttp
    payload = {"model": model, "messages": [{"role": "system", "content": sysb}, {"role": "user", "content": userb}],
               "temperature": temperature, "max_tokens": max_tokens, "seed": seed, "logprobs": True, "top_logprobs": 1}
    async with session.post(url + "/v1/chat/completions", json=payload, timeout=aiohttp.ClientTimeout(total=300)) as r:
        d = await r.json()
    ch = d["choices"][0]
    text = ch["message"]["content"]
    lp = ch.get("logprobs") or {}
    toks = [(c.get("token"), round(c.get("logprob", 0.0), 6)) for c in (lp.get("content") or [])]
    return text, toks

async def run_set(url, model, reqs, temperature, seed, conc):
    import aiohttp
    sem = asyncio.Semaphore(conc)
    async with aiohttp.ClientSession() as session:
        async def one(r):
            async with sem:
                return await call(session, url, model, r[1], r[2], temperature, seed)
        return await asyncio.gather(*[one(r) for r in reqs])

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--model", default="Qwen3-8B-int8")
    ap.add_argument("--probes", default=os.path.expanduser("~/bench/quality_probe_v0/probes.jsonl"))
    ap.add_argument("--out", default="b14_result.json")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    core, fill = load_probes(a.probes)
    random.seed(1); core = core[:32]; fill = fill[:200]
    res = {"label": a.label, "model": a.model, "n_core": len(core), "n_fill": len(fill)}
    # T6a: 温度0 単独(逐次) vs 混在(並行 c=64)
    t0 = time.perf_counter()
    solo = await run_set(a.url, a.model, core, 0.0, 20260907, 1)
    t1 = time.perf_counter()
    mixed_all = await run_set(a.url, a.model, core + fill, 0.0, 20260907, 64)
    t2 = time.perf_counter()
    mixed = mixed_all[:len(core)]
    same_text = sum(1 for s, m in zip(solo, mixed) if s[0] == m[0])
    same_lp = sum(1 for s, m in zip(solo, mixed) if s[1] == m[1])
    res["T6a_temp0"] = {"same_text": same_text, "same_logprobs": same_lp, "n": len(core), "solo_s": round(t1 - t0, 1), "mixed_s": round(t2 - t1, 1)}
    # T6b: 温度0.7 seed固定 混在A vs 混在B(充填の順序を変える)
    fillB = fill[::-1]
    A = await run_set(a.url, a.model, core + fill, 0.7, 777, 64)
    B = await run_set(a.url, a.model, core + fillB, 0.7, 777, 64)
    same_text_b = sum(1 for s, m in zip(A[:len(core)], B[:len(core)]) if s[0] == m[0])
    res["T6b_temp07_seed"] = {"same_text": same_text_b, "n": len(core)}
    # T6c: hashes for cross-version comparison
    res["T6c_hashes"] = {core[i][0]: hashlib.sha256(solo[i][0].encode("utf-8")).hexdigest()[:16] for i in range(len(core))}
    # throughput probe (all 232 at c64, temp0) already measured in mixed_s
    res["throughput_calls_per_s_mixed_c64"] = round(len(core + fill) / (t2 - t1), 2)
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "T6c_hashes"}, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
