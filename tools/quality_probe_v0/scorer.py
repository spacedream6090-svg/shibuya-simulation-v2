# -*- coding: utf-8 -*-
"""scorer.py — 品質プローブv0 の採点器(標準ライブラリのみ)。

2つの使い方:
  1) ライブラリ: run_probe.py が import して1呼び出しごとに採点する。
  2) 集計CLI:  python scorer.py --ledger quality_ledger.csv --probes probes.jsonl [--report report.md]

設計方針(答申 §4-3 / §4-4):
  - 出力に厳密JSONを課さない。まずJSONを試し、失敗したら行指向の寛容パーサへフォールバックする。
  - パース失敗は「0点」ではなく `format_error` として品質スコアと分けて数える。
  - 系統⑥の一致率は Wilson 片側95%下限(既定 z=1.6449)で報告する。点推定だけの数字は出さない。
  - 日本語品質の安価な代理指標として ja_char_ratio と kana_ratio を両方出す
    (漢字は中国語と共有するため、中国語混入の判別には kana_ratio が効く)。
"""

import argparse
import csv
import io
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# 語彙と正規化
# ---------------------------------------------------------------------------

ACTION_VOCAB = ["移動", "購入", "会話", "待機", "退去", "通報", "手伝い", "断る", "休憩", "就寝"]

# 表層の言い換え → 正規語彙。長い語から順に照合する。
ACTION_SYNONYMS = [
    ("立ち去る", "退去"), ("その場を離れる", "退去"), ("離れる", "退去"), ("立ち去", "退去"),
    ("110番", "通報"), ("119番", "通報"), ("救急", "通報"), ("通報する", "通報"), ("呼ぶ", "通報"),
    ("助ける", "手伝い"), ("助け", "手伝い"), ("介抱", "手伝い"), ("声をかける", "会話"),
    ("手を貸す", "手伝い"), ("手伝う", "手伝い"),
    ("買う", "購入"), ("買い物", "購入"), ("購入する", "購入"), ("注文", "購入"),
    ("話す", "会話"), ("話しかける", "会話"), ("会話する", "会話"), ("返事", "会話"),
    ("待つ", "待機"), ("待機する", "待機"),
    ("歩く", "移動"), ("向かう", "移動"), ("行く", "移動"), ("移動する", "移動"),
    ("断わる", "断る"), ("辞退", "断る"), ("ことわる", "断る"), ("お断り", "断る"),
    ("休む", "休憩"), ("休憩する", "休憩"), ("寝る", "就寝"), ("眠る", "就寝"),
]

FIELD_KEYS = ["理由", "行動", "行き先", "相手", "ひと言", "発話", "会話", "回答", "振り返り",
              "明日", "裁定", "差分"]
FIELD_ALIASES = {
    "reason": "理由", "action": "行動", "destination": "行き先", "target": "相手",
    "utterance": "ひと言", "speech": "発話", "answer": "回答", "verdict": "裁定",
    "diff": "差分", "一言": "ひと言", "行先": "行き先", "行き先き": "行き先",
    "セリフ": "発話", "台詞": "発話", "答え": "回答", "判定": "裁定", "結論": "裁定",
}

_KEY_RE = re.compile(
    r"^\s*(?:[-*•>#]+\s*)?(?:[\[【])?\s*(" +
    "|".join(sorted(set(FIELD_KEYS + list(FIELD_ALIASES.keys())), key=len, reverse=True)) +
    r")\s*(?:[\]】])?\s*[:：]\s*(.*)$")

_THINK_RE = re.compile(r"<think>.*?</think>", re.S)
_OPEN_THINK_RE = re.compile(r"<think>.*$", re.S)


def strip_think(text):
    """Qwen3 等の思考ブロックを除去する(判定前に必ず通す)。"""
    if not text:
        return ""
    t = _THINK_RE.sub("", text)
    t = _OPEN_THINK_RE.sub("", t)
    return t.strip()


def _clean(v):
    v = v.strip()
    v = re.sub(r"^\**\s*|\s*\**$", "", v)
    v = re.sub(r"^[<＜]|[>＞]$", "", v).strip()
    return v


def parse_output(text, required):
    """寛容パーサ。①JSONを試す ②行正規表現で抽出 ③どちらも駄目なら format_error。

    required: 必須キーのリスト(例 ["理由","行動"])。
    返り値: (fields:dict, parse_ok:bool, parse_mode:str)
    """
    t = strip_think(text or "")
    fields = {}

    # --- ① JSON を試す(課してはいないが、書いてきたら読む)---
    m = re.search(r"\{.*\}", t, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                for k, v in obj.items():
                    key = FIELD_ALIASES.get(str(k).strip(), str(k).strip())
                    if key in FIELD_KEYS:
                        fields[key] = _clean(str(v))
        except Exception:
            pass
    if fields and all(k in fields and fields[k] for k in required):
        return fields, True, "json"

    # --- ② 行指向の抽出 ---
    line_fields = {}
    cur = None
    for raw_line in t.split("\n"):
        mm = _KEY_RE.match(raw_line)
        if mm:
            key = FIELD_ALIASES.get(mm.group(1), mm.group(1))
            line_fields[key] = _clean(mm.group(2))
            cur = key
        elif cur and raw_line.strip():
            # 継続行(差分の複数行など)は直前のキーに足す
            if cur in ("差分", "振り返り"):
                line_fields[cur] = (line_fields.get(cur, "") + "\n" + raw_line.strip()).strip()
    for k, v in line_fields.items():
        if v or k not in fields:
            fields[k] = v

    if all(k in fields and fields[k] for k in required):
        return fields, True, "lines"

    # --- ③ 失敗。本文全体を残して format_error にする ---
    fields.setdefault("_raw", t)
    return fields, False, "format_error"


def extract_action(fields, whole_text):
    """行動をスカラー語彙へ写像する。行動欄→本文の順に探す。"""
    for src, mode in ((fields.get("行動", ""), "field"), (whole_text, "fallback")):
        if not src:
            continue
        for a in ACTION_VOCAB:
            if a in src:
                return a, mode
        for pat, a in ACTION_SYNONYMS:
            if pat in src:
                return a, mode
    return "", "none"


_CELL_RE = re.compile(r"[CcＣ][-‐-―－]?\s*0*(\d{1,4})")


def extract_destination(fields, whole_text):
    src = fields.get("行き先", "")
    if not src:
        src = ""
    for s in (src, whole_text):
        if not s:
            continue
        m = _CELL_RE.search(s)
        if m:
            return "C-%04d" % int(m.group(1))
        if re.search(r"^\s*(なし|無し|None|none|-|—)\s*$", s.strip()):
            return "なし"
    if src.strip():
        return src.strip()[:24]
    return ""


# ---------------------------------------------------------------------------
# 日本語らしさ(安価な代理指標)
# ---------------------------------------------------------------------------

def _cls(ch):
    o = ord(ch)
    if 0x3040 <= o <= 0x309F:
        return "hira"
    if 0x30A0 <= o <= 0x30FF or o == 0x30FC:
        return "kata"
    if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
        return "kanji"
    if 0x3000 <= o <= 0x303F or 0xFF01 <= o <= 0xFF60:
        return "jpunct"
    if 0x0041 <= o <= 0x007A:
        return "latin"
    if 0x0410 <= o <= 0x044F or 0xAC00 <= o <= 0xD7AF:
        return "other_script"
    return "other"


def script_ratios(text):
    t = re.sub(r"\s+", "", strip_think(text or ""))
    if not t:
        return dict(ja_char_ratio=0.0, kana_ratio=0.0, latin_ratio=0.0,
                    other_script_ratio=0.0, n_chars=0)
    c = Counter(_cls(ch) for ch in t)
    # v0.1(2026-09-08): 分母から "other"(数字・ASCII記号・セルID/時刻/金額の桁)を除く。
    # v0では時刻・金額・デシベル値・セルIDが分母に入り、定型出力で閾値0.85が転用不能だった(summary.md §5)。
    n_all = len(t)
    n = n_all - c["other"]
    if n <= 0:
        return dict(ja_char_ratio=0.0, kana_ratio=0.0, latin_ratio=0.0,
                    other_script_ratio=0.0, n_chars=n_all)
    ja = c["hira"] + c["kata"] + c["kanji"] + c["jpunct"]
    return dict(ja_char_ratio=round(ja / n, 4),
                kana_ratio=round((c["hira"] + c["kata"]) / n, 4),
                latin_ratio=round(c["latin"] / n, 4),
                other_script_ratio=round(c["other_script"] / n, 4),
                n_chars=n_all)


# ---------------------------------------------------------------------------
# 制約充足・gold・終了合図
# ---------------------------------------------------------------------------

def _scope_text(fields, scope):
    return "\n".join(fields.get(k, "") for k in scope)


def check_constraints(probe, fields, action, whole_text):
    """違反した制約の一覧を返す。"""
    hits = []
    for c in probe["expected"].get("constraints") or []:
        va = c.get("violating_actions")
        if va and action in va:
            hits.append(c["kind"])
            continue
        vr = c.get("violating_regex")
        if vr:
            scope = c.get("scope") or ["行動", "行き先", "ひと言", "発話"]
            txt = _scope_text(fields, scope) or whole_text
            ex = c.get("exempt_regex")
            if re.search(vr, txt) and not (ex and re.search(ex, txt)):
                hits.append(c["kind"])
    return hits


_VERDICT = [("条件付", "条件付き"), ("不許可", "不許可"), ("却下", "不許可"), ("認めない", "不許可"),
            ("不成立", "不許可"), ("拒否", "不許可"), ("許可", "許可"), ("承認", "許可"),
            ("認める", "許可"), ("成立", "許可")]


def extract_verdict(fields, whole_text):
    src = fields.get("裁定", "") or whole_text
    for pat, v in _VERDICT:
        if pat in src:
            return v
    return ""


def check_gold(probe, fields, action, whole_text):
    g = probe["expected"].get("gold_answer")
    if not g:
        return None
    kind = g["kind"]
    if kind == "action_any_of":
        return action in g["value"]
    if kind == "regex":
        field = g.get("field")
        src = fields.get(field, "") if field else ""
        return bool(re.search(g["value"], src) or re.search(g["value"], whole_text))
    if kind == "verdict":
        return extract_verdict(fields, whole_text) == g["value"]
    return None


def check_termination(probe, fields, action, whole_text):
    ts = probe["expected"].get("termination_signal")
    if not ts:
        return None, None
    detected = False
    conv = fields.get("会話", "")
    if "終了" in conv or "終わ" in conv:
        detected = True
    if action in ("退去", "移動", "断る"):
        detected = True
    src = fields.get("発話", "") or fields.get("ひと言", "") or whole_text
    for kw in ts.get("keywords") or []:
        if kw in src:
            detected = True
            break
    return detected, bool(ts.get("expected"))


# ---------------------------------------------------------------------------
# 系統④ 内省の事実照合
# ---------------------------------------------------------------------------

_FACT_PATTERNS = [
    ("person", re.compile(r"P[-‐-―－]?\s*\d{3}")),
    ("cell", re.compile(r"[CcＣ][-‐-―－]?\s*\d{3,4}")),
    ("money", re.compile(r"\d[\d,]*\s*円")),
]


def _norm_fact(s):
    return re.sub(r"[\s,‐-―－-]", "", s)


def score_reflection(probe, fields, whole_text):
    log = probe["observation"]
    body = fields.get("振り返り", "") or whole_text
    log_norm = _norm_fact(log)
    claims, halluc = 0, []
    for _, pat in _FACT_PATTERNS:
        for m in pat.findall(body):
            claims += 1
            if _norm_fact(m) not in log_norm:
                halluc.append(m)
    hr = (len(halluc) / claims) if claims else 0.0
    sal = probe["expected"].get("salient_events") or []
    hit = [s["key"] for s in sal if re.search(s["regex"], body)]
    rr = (len(hit) / len(sal)) if sal else 0.0
    return dict(hallucination_rate=round(hr, 4), n_fact_claims=claims,
                hallucinated=halluc, recall_rate=round(rr, 4), recalled=hit)


# ---------------------------------------------------------------------------
# 系統⑤ 差分のスキーマ検証
# ---------------------------------------------------------------------------

_DIFF_LINE = re.compile(r"^\s*(?P<obj>[^|｜]+)[|｜](?P<field>[^|｜]+)[|｜](?P<from>.+?)\s*(?:->|→|=>)\s*(?P<to>.+?)\s*$")


def check_diff(probe, fields):
    de = probe["expected"].get("diff_expected") or {}
    raw = fields.get("差分", "").strip()
    none_like = bool(re.match(r"^(なし|無し|None|none|-|変更なし|変化なし)\s*$", raw))
    lines = [l for l in raw.split("\n") if l.strip() and not none_like]
    parsed = [_DIFF_LINE.match(l) for l in lines]
    valid = all(p is not None for p in parsed) if lines else True
    if de.get("should_change"):
        ok = (not none_like) and bool(lines) and valid
        for kw in de.get("must_mention") or []:
            ok = ok and (kw in raw)
        if de.get("expect_to"):
            ok = ok and (_norm_fact(de["expect_to"]) in _norm_fact(raw))
        return dict(diff_valid=valid, diff_semantic_ok=bool(ok), n_diff_lines=len(lines))
    else:
        ok = none_like or not lines
        return dict(diff_valid=valid, diff_semantic_ok=bool(ok), n_diff_lines=len(lines))


# ---------------------------------------------------------------------------
# 1呼び出しの採点
# ---------------------------------------------------------------------------

REQUIRED = {1: ["理由", "行動"], 2: ["発話"], 3: ["回答"], 4: ["振り返り"],
            5: ["裁定"], 6: ["理由", "行動"]}


def score_call(probe, raw_text):
    fam = probe["family"]
    fields, parse_ok, mode = parse_output(raw_text, REQUIRED[fam])
    whole = strip_think(raw_text or "")
    action, action_src = extract_action(fields, whole)
    dest = extract_destination(fields, whole)
    sr = script_ratios(whole)
    out = dict(parse_ok=parse_ok, parse_mode=mode, action=action, action_src=action_src,
               destination=dest, fields=fields, **sr)

    violations = check_constraints(probe, fields, action, whole)
    gold = check_gold(probe, fields, action, whole)
    term_detected, term_expected = check_termination(probe, fields, action, whole)
    out.update(violations=violations, n_violations=len(violations),
               gold_ok=gold, term_detected=term_detected, term_expected=term_expected)

    orr = probe["expected"].get("over_refusal_regex")
    if orr:
        out["over_refusal"] = bool(re.search(orr, whole))

    if fam == 1:
        s = 1 if not violations else 0
        if gold is not None:
            s = 1 if (s == 1 and gold) else 0
        out["score"] = s if parse_ok else 0
    elif fam == 2:
        s = 1 if not violations else 0
        if gold is not None and not gold:
            s = 0
        if term_expected and not term_detected:
            s = 0
        if term_expected is False and out.get("over_refusal"):
            pass  # 過剰拒否は別勘定(スコアは落とさない)
        out["score"] = s if parse_ok else 0
    elif fam == 3:
        out["score"] = (1 if gold else 0) if parse_ok else 0
    elif fam == 4:
        r = score_reflection(probe, fields, whole)
        out.update(r)
        s = 1 if (r["hallucination_rate"] == 0.0 and r["recall_rate"] >= 2.0 / 3.0) else 0
        out["score"] = s if parse_ok else 0
    elif fam == 5:
        d = check_diff(probe, fields)
        out.update(d)
        out["verdict"] = extract_verdict(fields, whole)
        s = 1 if (gold and d["diff_semantic_ok"]) else 0
        out["score"] = s if parse_ok else 0
    elif fam == 6:
        # ⑥は水準間の一致が指標。1呼び出し単体では書式のみを点にする。
        out["score"] = 1 if parse_ok else 0
    return out


# ---------------------------------------------------------------------------
# 区間推定
# ---------------------------------------------------------------------------

def wilson_lb(k, n, z=1.6449):
    """Wilson スコア区間の下限。既定 z=1.6449 = 片側95%(ゲート用)。両側95%は z=1.96。"""
    if n <= 0:
        return 0.0
    p = float(k) / n
    den = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    margin = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return max(0.0, (centre - margin) / den)


def wilson_ci(k, n, z=1.96):
    if n <= 0:
        return (0.0, 1.0)
    p = float(k) / n
    den = 1.0 + z * z / n
    centre = p + z * z / (2.0 * n)
    margin = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return (max(0.0, (centre - margin) / den), min(1.0, (centre + margin) / den))


# ---------------------------------------------------------------------------
# 行き先の隣接許容(expedient・ユーザー判断項目)
# ---------------------------------------------------------------------------
# 100mセルで隣に行くのを同判断と見なすかは世界観の問題。既定の群は暫定で、
# README「未確認事項」に挙げてある。変更したらこの表ごと版を上げること。
ADJACENCY_GROUPS = [
    {"C-0002", "C-0004", "C-0006", "C-0012"},           # 駅前広場・デッキ・構内・地下街
    {"C-0088", "C-0091", "C-0030", "C-0075"},           # センター街・公園通り・井ノ頭通り
    {"C-0117", "C-0135", "C-0166"},                     # 道玄坂・神泉・桜丘町
    {"C-0043", "C-0055", "C-0060"},                     # 宮益坂・明治通り・美竹通り
    {"C-0210"}, {"C-0190"},                             # 表参道 / 並木橋
]


def dest_equal(a, b, adjacent_ok=False):
    a = (a or "").strip()
    b = (b or "").strip()
    if a == b:
        return True
    if not adjacent_ok or not a or not b:
        return False
    for g in ADJACENCY_GROUPS:
        if a in g and b in g:
            return True
    return False


# ---------------------------------------------------------------------------
# 集計
# ---------------------------------------------------------------------------

# 運用時の場面分布の仮定(層別一致率の再重み付けに使う・宣言つきの仮定)。
TIER_PRIOR = {"plain": 0.80, "mid": 0.15, "tail": 0.05}

GATES = dict(
    f6_primary_lb=0.80, f6_conditional_lb=0.75,
    f1_violation_max=0.25, f3_accuracy_min=0.60, f5_pair_min=0.80,
    format_error_max=0.10, ja_char_ratio_min=0.85, kana_ratio_min=0.20,
)


def load_probes(path):
    P = {}
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                p = json.loads(line)
                P[p["id"]] = p
    return P


def load_ledger(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(row, key, default=0.0):
    try:
        return float(row.get(key, "") or default)
    except ValueError:
        return default


def aggregate(rows, probes, adjacent=False):
    """モデルごとの集計を返す。"""
    by_model = defaultdict(list)
    for r in rows:
        by_model[(r.get("model", ""), r.get("quant", ""))].append(r)

    report = {}
    for key, rs in sorted(by_model.items()):
        model, quant = key
        res = dict(model=model, quant=quant, n_calls=len(rs))

        # --- 書式・日本語(全系統共通・品質と分離)---
        n_fe = sum(1 for r in rs if str(r.get("parse_ok", "")).lower() in ("false", "0", ""))
        res["format_error_rate"] = round(n_fe / len(rs), 4) if rs else 0.0
        jas = [_f(r, "ja_char_ratio") for r in rs if r.get("ja_char_ratio")]
        kanas = [_f(r, "kana_ratio") for r in rs if r.get("kana_ratio")]
        res["ja_char_ratio_mean"] = round(sum(jas) / len(jas), 4) if jas else 0.0
        res["kana_ratio_mean"] = round(sum(kanas) / len(kanas), 4) if kanas else 0.0
        res["ja_char_ratio_p05"] = round(sorted(jas)[max(0, int(0.05 * len(jas)))], 4) if jas else 0.0
        outtok = [_f(r, "out_tokens") for r in rs if r.get("out_tokens")]
        res["out_tokens_mean"] = round(sum(outtok) / len(outtok), 1) if outtok else 0.0
        lat = [_f(r, "latency_ms") for r in rs if r.get("latency_ms")]
        res["latency_ms_p50"] = round(sorted(lat)[len(lat) // 2], 1) if lat else 0.0

        # --- 系統①〜⑤ ---
        for fam in (1, 2, 3, 4, 5):
            fr = [r for r in rs if r.get("family") == str(fam) and r.get("variant") in ("", "-", None, "main")]
            if not fr:
                fr = [r for r in rs if r.get("family") == str(fam)]
            if not fr:
                continue
            k = sum(1 for r in fr if _f(r, "score") >= 1.0)
            n = len(fr)
            lo, hi = wilson_ci(k, n)
            res["f%d_score" % fam] = round(k / n, 4)
            res["f%d_n" % fam] = n
            res["f%d_ci" % fam] = (round(lo, 4), round(hi, 4))
            res["f%d_lb95" % fam] = round(wilson_lb(k, n), 4)
        f1 = [r for r in rs if r.get("family") == "1"]
        if f1:
            nv = sum(1 for r in f1 if int(_f(r, "n_violations")) > 0)
            res["violation_rate"] = round(nv / len(f1), 4)
        f5 = [r for r in rs if r.get("family") == "5"]
        if f5:
            pairs = defaultdict(dict)
            for r in f5:
                p = probes.get(r["probe_id"])
                if not p:
                    continue
                pid = p["expected"].get("consistency_pair_id")
                if pid:
                    pairs[pid][r["probe_id"]] = r.get("verdict", "")
            agreed = sum(1 for d in pairs.values() if len(d) == 2 and len(set(d.values())) == 1)
            res["pair_consistency"] = round(agreed / len(pairs), 4) if pairs else None
            res["pair_n"] = len(pairs)

        # --- 系統⑥ 観測削減の一致率 ---
        f6 = [r for r in rs if r.get("family") == "6"]
        if f6:
            by_probe = defaultdict(dict)
            for r in f6:
                by_probe[r["probe_id"]][r.get("variant", "")] = r
            agr = defaultdict(lambda: [0, 0])         # key -> [一致数, 比較数]
            tier_agr = defaultdict(lambda: defaultdict(lambda: [0, 0]))
            disagree_rows = []
            for pid, d in sorted(by_probe.items()):
                if not all(v in d for v in ("full", "v0", "v1")):
                    continue
                p = probes.get(pid, {})
                tier = (p.get("expected", {}) or {}).get("salience_tier", "?")
                pred = (p.get("expected", {}) or {}).get("predicted_disagreement")
                for a, b, name in (("full", "v1", "agree_full_v1"),
                                   ("full", "v0", "agree_full_v0"),
                                   ("v0", "v1", "agree_v0_v1")):
                    same_act = d[a].get("action", "") == d[b].get("action", "") and d[a].get("action", "") != ""
                    same_dst = dest_equal(d[a].get("destination", ""), d[b].get("destination", ""))
                    same_dst_adj = dest_equal(d[a].get("destination", ""), d[b].get("destination", ""), True)
                    for metric, val in ((name, same_act),
                                        (name + "_dest_exact", same_dst),
                                        (name + "_dest_adjacent", same_dst_adj)):
                        agr[metric][1] += 1
                        agr[metric][0] += 1 if val else 0
                        if metric == name:
                            tier_agr[name][tier][1] += 1
                            tier_agr[name][tier][0] += 1 if val else 0
                    if not same_act and name == "agree_v0_v1":
                        disagree_rows.append(dict(
                            probe_id=pid, tier=tier, predicted=pred,
                            driver=(p.get("expected", {}) or {}).get("driver_channel", ""),
                            v0_action=d["v0"].get("action", ""), v1_action=d["v1"].get("action", ""),
                            full_action=d["full"].get("action", ""),
                            v0_dest=d["v0"].get("destination", ""), v1_dest=d["v1"].get("destination", ""),
                            v0_raw=d["v0"].get("raw_output_path", ""), v1_raw=d["v1"].get("raw_output_path", "")))
            for metric, (k, n) in sorted(agr.items()):
                res[metric] = round(k / n, 4) if n else None
                res[metric + "_n"] = n
                res[metric + "_lb95"] = round(wilson_lb(k, n), 4) if n else None
            for name, td in tier_agr.items():
                for tier, (k, n) in td.items():
                    res["%s__%s" % (name, tier)] = "%d/%d" % (k, n)
            # 層別を運用分布で再重み付け(宣言つきの仮定)
            for name in ("agree_full_v1", "agree_v0_v1"):
                num = den = 0.0
                for tier, w in TIER_PRIOR.items():
                    k, n = tier_agr[name].get(tier, [0, 0])
                    if n:
                        num += w * (k / n)
                        den += w
                res[name + "_tierweighted"] = round(num / den, 4) if den else None
            res["_disagreements"] = disagree_rows

        # --- 安定性(pass^k)---
        stab = defaultdict(list)
        for r in rs:
            if (r.get("variant") or "").startswith("stab"):
                stab[r["probe_id"]].append(_f(r, "score"))
        if stab:
            ks = [len(v) for v in stab.values()]
            kmin = min(ks)
            allpass = sum(1 for v in stab.values() if all(x >= 1.0 for x in v))
            res["pass_pow_k"] = round(allpass / len(stab), 4)
            res["pass_pow_k_k"] = kmin
            res["pass_pow_k_n"] = len(stab)
            self_agr = sum(1 for v in stab.values() if len(set(v)) == 1) / len(stab)
            res["self_agreement"] = round(self_agr, 4)

        report[key] = res
    return report


def verdict_lines(res):
    """ゲート判定の文面を返す。"""
    out = []
    lb = res.get("agree_v0_v1_lb95")
    if lb is not None:
        if lb >= GATES["f6_primary_lb"]:
            out.append("⑥ v0→v1 削減: 合格 (LB95=%.3f >= 0.80)" % lb)
        elif lb >= GATES["f6_conditional_lb"]:
            out.append("⑥ v0→v1 削減: 条件付き合格 (LB95=%.3f)。不一致が層tailに集中し、"
                       "全件が『削られた情報を要する』と説明できるかを目視で確認すること" % lb)
        else:
            out.append("⑥ v0→v1 削減: 不合格 (LB95=%.3f < 0.75)。個体部予算(B5+B6 300tok)の見直しが要る" % lb)
    if res.get("violation_rate") is not None:
        out.append("① 制約違反率 %.3f (足切り閾値 <= %.2f)" % (res["violation_rate"], GATES["f1_violation_max"]))
    if res.get("f3_score") is not None:
        out.append("③ 役割知識QA %.3f (足切り閾値 >= %.2f)" % (res["f3_score"], GATES["f3_accuracy_min"]))
    if res.get("pair_consistency") is not None:
        out.append("⑤ 同型ペア一致 %.3f (足切り閾値 >= %.2f)" % (res["pair_consistency"], GATES["f5_pair_min"]))
    out.append("書式エラー率 %.3f (<= %.2f) / ja_char_ratio %.3f (>= %.2f) / kana_ratio %.3f (>= %.2f)"
               % (res.get("format_error_rate", 0), GATES["format_error_max"],
                  res.get("ja_char_ratio_mean", 0), GATES["ja_char_ratio_min"],
                  res.get("kana_ratio_mean", 0), GATES["kana_ratio_min"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--probes", required=True)
    ap.add_argument("--report", default=None)
    ap.add_argument("--adjacent", action="store_true", help="行き先一致に隣接セル許容を既定で使う")
    a = ap.parse_args()

    probes = load_probes(a.probes)
    rows = load_ledger(a.ledger)
    rep = aggregate(rows, probes, adjacent=a.adjacent)

    lines = ["# 品質プローブv0 集計", ""]
    lines.append("読み方: 本プローブは足切り+観測削減の安全確認器である。"
                 "n<100 で検出可能な最小差は12〜25ポイント。モデル選定の最終根拠にはならない。")
    lines.append("")
    for key, res in sorted(rep.items()):
        lines.append("## %s (%s) — %d呼" % (res["model"], res["quant"], res["n_calls"]))
        for v in verdict_lines(res):
            lines.append("- " + v)
        lines.append("")
        lines.append("| 指標 | 値 |")
        lines.append("|---|---|")
        for k in sorted(res):
            if k.startswith("_") or k in ("model", "quant"):
                continue
            lines.append("| %s | %s |" % (k, res[k]))
        lines.append("")
        dis = res.get("_disagreements") or []
        if dis:
            lines.append("### ⑥ v0対v1 の不一致(全件・手で3分類すること: "
                         "(i)削減が判断を駆動=真の代償 / (ii)どちらも妥当=無害 / (iii)出力の揺れ=測定ノイズ)")
            lines.append("")
            lines.append("| probe | 層 | 事前予測 | 駆動チャネル | v0行動 | v1行動 | full行動 | 分類 |")
            lines.append("|---|---|---|---|---|---|---|---|")
            for d in dis:
                lines.append("| %s | %s | %s | %s | %s | %s | %s |  |"
                             % (d["probe_id"], d["tier"], d["predicted"], d["driver"],
                                d["v0_action"], d["v1_action"], d["full_action"]))
            lines.append("")
    text = "\n".join(lines) + "\n"
    if a.report:
        with io.open(a.report, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote", a.report)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
