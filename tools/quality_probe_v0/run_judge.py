# -*- coding: utf-8 -*-
"""run_judge.py — 系統②のペア比較判定(judge_protocol.md jp-v0.1 の実装)。

- 判定プロンプトと参照回答は judge_protocol.md から**その場で抽出**する(転記事故を避ける)。
- 各ペアを、そのペアに含まれない第3の候補モデルが判定する(§2の暫定運用)。
- AB両順で2回判定し、両順一致だけを「決着」とする(§6)。
- 出力: judge_ledger.csv
"""
import argparse, csv, hashlib, json, os, re, sys, time
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20260905

COLUMNS = ["pair", "probe_id", "judge_model", "order", "winner", "reason",
           "out_tokens", "len_a", "len_b", "model_a", "model_b",
           "prompt_template_hash", "ts"]


def extract_prompt_template(md_text):
    """§3 の最初のコードブロック本文を返す。"""
    sec = md_text.split("## 3. ")[1]
    m = re.search(r"```\n(.*?)\n```", sec, re.S)
    if not m:
        raise SystemExit("判定プロンプトのコードブロックを抽出できない")
    return m.group(1)


def extract_references(md_text):
    """§4 の表から probe_id -> 参照回答 を返す。"""
    sec = md_text.split("## 4. ")[1].split("## 5.")[0]
    refs = {}
    for line in sec.splitlines():
        m = re.match(r"\|\s*\*\*(F2-\d\d)\*\*[^|]*\|\s*(.+?)\s*\|\s*$", line)
        if m:
            refs[m.group(1)] = m.group(2)
    if len(refs) != 6:
        raise SystemExit("参照回答の抽出数が6でない: %d" % len(refs))
    return refs


def http_json(url, payload, timeout=300):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def call(endpoint, model, prompt, max_tokens=96):
    payload = {"model": model,
               "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.0, "top_p": 1.0, "max_tokens": max_tokens,
               "seed": SEED, "n": 1, "stream": False,
               "chat_template_kwargs": {"enable_thinking": False}}
    for attempt in range(3):
        try:
            d = http_json(endpoint + "/v1/chat/completions", payload)
            txt = d["choices"][0]["message"].get("content") or ""
            return txt, (d.get("usage") or {}).get("completion_tokens")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:200]
            if e.code == 400 and "chat_template_kwargs" in body:
                payload.pop("chat_template_kwargs", None)
                continue
            last = "HTTP %s %s" % (e.code, body)
        except Exception as e:
            last = "%s: %s" % (type(e).__name__, e)
        time.sleep(2)
    return "__ERROR__ " + str(last), None


VERDICT_RE = re.compile(r"判定\s*[:：]\s*(.+)")
REASON_RE = re.compile(r"理由\s*[:：]\s*(.+)")


def parse_verdict(txt):
    """A / B / tie を返す。読めなければ tie。"""
    m = VERDICT_RE.search(txt)
    seg = m.group(1).strip() if m else txt.strip()
    seg = seg.replace("回答", "").strip()
    if seg.startswith("A") or seg[:1] == "Ａ":
        return "A"
    if seg.startswith("B") or seg[:1] == "Ｂ":
        return "B"
    if "引き分け" in seg or "同" in seg:
        return "tie"
    # フォールバック: 本文全体から探す
    if "引き分け" in txt:
        return "tie"
    return "tie"


def parse_reason(txt):
    m = REASON_RE.search(txt)
    return (m.group(1).strip() if m else "")[:120].replace("\n", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=os.path.join(HERE, "quality_ledger.csv"))
    ap.add_argument("--probes", default=os.path.join(HERE, "probes.jsonl"))
    ap.add_argument("--protocol", default=os.path.join(HERE, "judge_protocol.md"))
    ap.add_argument("--out", default=os.path.join(HERE, "judge_ledger.csv"))
    ap.add_argument("--endpoints", required=True,
                    help="model=url を3つカンマ区切り。例 Qwen3-8B-int8=http://127.0.0.1:8000,...")
    args = ap.parse_args()

    md = open(args.protocol, encoding="utf-8").read()
    tmpl = extract_prompt_template(md)
    refs = extract_references(md)
    tmpl_hash = hashlib.sha256(tmpl.encode("utf-8")).hexdigest()
    print("prompt_template_hash =", tmpl_hash)

    eps = {}
    for spec in args.endpoints.split(","):
        k, v = spec.split("=", 1)
        eps[k.strip()] = v.strip().rstrip("/")
    models = list(eps.keys())
    if len(models) != 3:
        raise SystemExit("3モデル必要")

    probes = {}
    for line in open(args.probes, encoding="utf-8"):
        d = json.loads(line)
        if d["family"] == 2:
            probes[d["id"]] = d

    # 台帳から family2 の生出力を回収
    answers = {}   # (model, probe_id) -> text
    with open(args.ledger, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("family") == "2" and row.get("variant") == "main":
                p = row.get("raw_output_path") or ""
                if not os.path.isabs(p):
                    p = os.path.join(HERE, p)
                if os.path.exists(p):
                    answers[(row["model"], row["probe_id"])] = \
                        open(p, encoding="utf-8").read().strip()
    print("回収した②の出力:", len(answers))

    pairs = [(models[0], models[1], models[2]),
             (models[0], models[2], models[1]),
             (models[1], models[2], models[0])]

    rows = []
    for ma, mb, judge in pairs:
        pair_name = "%s_vs_%s" % (ma, mb)
        for pid in sorted(probes):
            a_txt = answers.get((ma, pid))
            b_txt = answers.get((mb, pid))
            if a_txt is None or b_txt is None:
                print("skip (出力欠落):", pair_name, pid)
                continue
            for order in ("AB", "BA"):
                if order == "AB":
                    ans_a, ans_b, who_a, who_b = a_txt, b_txt, ma, mb
                else:
                    ans_a, ans_b, who_a, who_b = b_txt, a_txt, mb, ma
                prompt = (tmpl
                          .replace("{observation}", probes[pid]["observation"])
                          .replace("{question}", probes[pid]["question"])
                          .replace("{reference}", refs[pid])
                          .replace("{answer_a}", ans_a)
                          .replace("{answer_b}", ans_b))
                out, ntok = call(eps[judge], judge, prompt)
                rows.append({
                    "pair": pair_name, "probe_id": pid, "judge_model": judge,
                    "order": order, "winner": parse_verdict(out),
                    "reason": parse_reason(out), "out_tokens": ntok,
                    "len_a": len(ans_a), "len_b": len(ans_b),
                    "model_a": who_a, "model_b": who_b,
                    "prompt_template_hash": tmpl_hash,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                })
                print("%s %s %s judge=%s -> %s" %
                      (pair_name, pid, order, judge, rows[-1]["winner"]))

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print("wrote", args.out, len(rows), "rows")


if __name__ == "__main__":
    main()
