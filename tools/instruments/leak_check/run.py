# -*- coding: utf-8 -*-
"""leak_check.run — 型ごとに 1 回通して集計(``result.json`` の中身)と表(``table.md``)を作る。

型 ①(``run_type1``): (a) 日付 20 件を問い、時点の前後で「分からない」の率・具体名の率とその差(後 − 前)。
    (b) 架空の出来事 10 件と、親が置いた実在の出来事(``data/leak_check/real_events.jsonl``)を種の鍵で混ぜて
    「知っているか」を問い、架空への同意の率(迎合)・実在への同意の率・その差(実在 − 架空=見分ける力)・具体名の
    率を前後に分けて出す。率は分母に other を含める版と含めない版の両方。実在のファイルが無ければ実在の側と差は
    「未投入」(架空の側は測る)。``model_cutoff``(モデルの学習の締め切り・任意)を渡すと、前後の各側をさらに
    「締め切りの前/後」に分けて出す(渡さなければ分けない)。
型 ②(``run_type2``): 実名版と架空名版の対ごとに分布(1 トークン目の確率・番号に乗った確率が下限 ``min_mass`` より
    小さいか対数確率が無ければ本文の番号)を取り、JSD・1 位の一致・名の向き(名を含む候補の確率の差)を、出所ごと
    (logprobs/本文/混ざり=片方ずつ違う)に分けて、全体と対象の群ごとに出す。出所は混ぜない。Glasserman & Lin 型の
    成績の差は人の分布が無い=値なし(器だけ)。
型 ④(``run_type4``): 親が置いた参照(``data/leak_check/recall_refs.jsonl``)ごとに guided と general の 2 つの
    指示で続きを書かせ、完全一致・正規化した部分一致・最長共通部分列の率。参照が無ければ「未投入」。

入力のファイルの形(親が置く・gitignore の下)
    - ``real_events.jsonl``: 1 行 1 件 ``{"id": "r01", "when": "YYYY-MM" か "YYYY-MM-DD", "text": "出来事の文"}``。
      id は ``f`` で始めない(架空と混ぜるため)。前後は ``when`` の粒度で決める(日付まであれば日で・年月だけなら、
      時点の月を「後」に数える)。月は 01〜12・日は暦に合うこと(合わなければ ``InputMismatch``)。
    - ``recall_refs.jsonl``: 1 行 1 件 ``{"id", "name", "text"}``(冒頭=先頭 ``prefix_chars`` 字・続き=その後
      ``cont_chars`` 字)か ``{"id", "name", "prefix", "continuation"}``。
    md5 は読んだバイトの md5 を記録し、``expected_md5`` を渡したときは照らす(違えば止まる・ファイルが無くても
    止まる。「未投入」は md5 を渡していないときだけ)。封印・検証側の語とパターン台帳の道筋は開く前に落とす
    (``read_guard.deny_hit``+``LEAK_EXTRA_DENY_TOKENS``)。

記録に写さないもの: 応答の本文・問いの文・参照の文・実在の出来事の文・絶対の道筋(ファイルは名だけ)。
``digest`` は記録の決定的な部分(``wall_s`` と ``digest`` を除いた全部)の sha256。

台帳の 1 行(``ledger_rule9.line``): モデルごとの 1 行(モデル名と版を頭に付ける)。運用規則 9 の欄はパターンの行
    ごとの欄なので、同じ 1 行をパターンの行ごとに写す前提(README)。
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from leak_check import DATA_DIR, SCHEMA, WORLD_DATE, sets as S
from leak_check import score as SC
from leak_check.backends import Backend
from read_guard import GAUGE_DENY_TOKENS, SealedPathError, deny_hit

REAL_EVENTS_NAME: Final[str] = "real_events.jsonl"
RECALL_REFS_NAME: Final[str] = "recall_refs.jsonl"
NOT_LOADED: Final[str] = "未投入"
LOADED: Final[str] = "投入済み"
UNMEASURED: Final[str] = "未測"
NO_VERSION: Final[str] = "版未記入"

DEFAULT_PREFIX_CHARS: Final[int] = 64
DEFAULT_CONT_CHARS: Final[int] = 128
MAX_TOKENS: Final[Mapping[str, int]] = {"dates": 256, "events": 128, "choice": 4, "recall": 256}
TYPE_NAMES: Final[Mapping[int, str]] = {1: "時点を切る", 2: "名前を伏せる", 4: "記憶の誘い出し"}
SOURCES: Final[tuple[str, ...]] = ("logprobs", "text", "mixed")
CUTOFF_SIDES: Final[tuple[str, ...]] = ("before_cutoff", "after_cutoff")

#: 計器の段の語(read_guard)に足して落とす語=検証側の錨のファイルの名の形(``*_validation_anchors_*``)と
#: パターン台帳(照合値を型 ④ の参照に使わない=親の判断・検収 L8)。
LEAK_EXTRA_DENY_TOKENS: Final[tuple[str, ...]] = ("validation_anchors", "_validation_", "pattern-ledger",
                                                  "pattern_ledger")
DENY_TOKENS: Final[tuple[str, ...]] = GAUGE_DENY_TOKENS + LEAK_EXTRA_DENY_TOKENS

NOT_IN_SCOPE: Final[str] = "③ 反事実の課題はこの器に入れない(外に出す主張の前=C-3 のバックテストの形を決める時に別途)"

_WHEN: Final[re.Pattern[str]] = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


class InputMismatch(ValueError):
    """親が置いた入力の md5 が渡した値と違う・md5 を渡したのにファイルが無い・形が違う。"""


# ---------------------------------------------------------------------------------------------- 入力
def _guard(path: Path) -> Path:
    hit = deny_hit(Path(path), DENY_TOKENS)
    if hit:
        raise SealedPathError(f"leak_check は {hit!r} を含む道筋を読まない")
    return Path(path)


def load_input(path: Path | None, default_name: str, expected_md5: str | None = None
               ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """親が置く入力を読む。無ければ ``([], 未投入)``(md5 を渡したのに無ければ ``InputMismatch``)。md5 は生のバイト。"""
    p = _guard(Path(path) if path is not None else DATA_DIR / default_name)
    info: dict[str, Any] = {"file": p.name, "status": NOT_LOADED, "md5": None, "expected_md5": expected_md5,
                            "md5_match": None, "n": 0}
    if not p.is_file():
        if expected_md5:
            raise InputMismatch(f"md5 を渡したのに {p.name} が無い")
        return [], info
    raw = p.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    info["md5"] = md5
    if expected_md5:
        info["md5_match"] = md5 == expected_md5
        if md5 != expected_md5:
            raise InputMismatch(f"{p.name} の md5 が渡した値と違う")
    text = raw.replace(b"\r\n", b"\n").decode("utf-8")
    try:
        rows = [json.loads(line) for line in text.split("\n") if line.strip()]
    except ValueError as exc:
        raise InputMismatch(f"{p.name} が JSONL として読めない") from exc
    if not rows:
        return [], info
    info["status"] = LOADED
    info["n"] = len(rows)
    return rows, info


def check_when(when: str) -> str:
    """``YYYY-MM`` か ``YYYY-MM-DD``(月は 01〜12・日は暦に合う)。合わなければ ``InputMismatch``。"""
    w = str(when)
    if not _WHEN.match(w):
        raise InputMismatch(f"when の形が YYYY-MM か YYYY-MM-DD でない: {w!r}")
    y, m = int(w[:4]), int(w[5:7])
    if not 1 <= m <= 12:
        raise InputMismatch(f"when の月が 01〜12 でない: {w!r}")
    if len(w) == 10:
        try:
            dt.date(y, m, int(w[8:10]))
        except ValueError as exc:
            raise InputMismatch(f"when の日が暦に合わない: {w!r}") from exc
    return w


def _check_real_events(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out = []
    for r in rows:
        rid, text = str(r.get("id", "")), str(r.get("text", ""))
        if not rid or rid in seen or rid.startswith("f"):
            raise InputMismatch(f"実在の出来事の id が空・重複・f で始まる: {rid!r}")
        if not text:
            raise InputMismatch(f"実在の出来事 {rid} の text が空")
        when = check_when(str(r.get("when", "")))
        seen.add(rid)
        try:
            side = S.side_of(when)  # 日付まであれば日で決める(検収 M5)
        except ValueError as exc:
            raise InputMismatch(f"実在の出来事 {rid} は世界の時点の当日(前後に分けない)") from exc
        out.append({"qid": f"t1b-{rid}", "kind": "real", "when": when, "side": side,
                    "prompt": S.event_prompt(when[:7], text)})
    return out


def cutoff_side(when: str, cutoff: str) -> str:
    """モデルの学習の締め切り ``cutoff``(``YYYY-MM`` か ``YYYY-MM-DD``)に対する前後。

    締め切りが年月なら、その月までを「前」(月を含む)。締め切りが日付なら、日付の項目はその日までを「前」、年月だけの
    項目は締め切りの月より前の月だけを「前」(締め切りを含む月は「後」=知りえない側に寄せる)。
    """
    c = check_when(cutoff)
    w = str(when)
    if len(c) == 7:
        return "before_cutoff" if w[:7] <= c else "after_cutoff"
    if len(w) == 10:
        return "before_cutoff" if w <= c else "after_cutoff"
    return "before_cutoff" if w[:7] < c[:7] else "after_cutoff"


def _mix_key(seed: str, qid: str) -> str:
    return hashlib.sha256(f"{seed}|mix|{qid}".encode("utf-8")).hexdigest()


def _limit(rows: list[Any], limit: int | None) -> list[Any]:
    if limit is None:
        return rows
    if int(limit) < 1:
        raise ValueError("limit は 1 以上")
    return rows[:int(limit)]


def _fmt(x: Any, nd: int = 3) -> str:
    if x is None:
        return "—"
    if isinstance(x, bool):
        return "はい" if x else "いいえ"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _signed(x: Any, nd: int = 3) -> str:
    if x is None:
        return "—"
    if isinstance(x, str):
        return x
    return f"{x:+.{nd}f}"


def model_label(backend_desc: Mapping[str, Any]) -> str:
    return f"{backend_desc.get('model', '') or '?'}@{backend_desc.get('model_version') or NO_VERSION}"


def _base(type_no: int, backend: Backend, sets_info: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema": SCHEMA, "type": type_no, "type_name": TYPE_NAMES[type_no], "world_date": WORLD_DATE,
            "backend": backend.describe(), "question_sets": dict(sets_info), "not_in_scope": NOT_IN_SCOPE}


def digest_of(res: Mapping[str, Any]) -> str:
    """記録の決定的な部分(``wall_s`` と ``digest`` を除く)の sha256(鍵の順をそろえた JSON)。"""
    body = {k: v for k, v in res.items() if k not in ("wall_s", "digest")}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _finish(res: dict[str, Any], t0: float) -> dict[str, Any]:
    res["digest"] = digest_of(res)
    res["wall_s"] = round(time.perf_counter() - t0, 3)
    return res


# ---------------------------------------------------------------------------------------------- 型 ①
def _by_cutoff(items: Sequence[Mapping[str, Any]], classes: Sequence[str], cutoff: str | None
               ) -> dict[str, Any] | None:
    if not cutoff:
        return None
    return {side: {cs: SC.summarize_type1([i for i in items if i["side"] == side and i["cutoff_side"] == cs], classes)
                   for cs in CUTOFF_SIDES} for side in (S.SIDE_PRE, S.SIDE_POST)}


def run_type1(backend: Backend, *, real_events: Path | None = None, expected_md5: str | None = None,
              seed: str = "leak", limit: int | None = None, sets_dir: Path | None = None,
              model_cutoff: str | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    if model_cutoff:
        model_cutoff = check_when(model_cutoff)
    dates, md5_a = S.load_set(S.TYPE1_DATES_NAME, sets_dir)
    fict, md5_b = S.load_set(S.TYPE1_EVENTS_NAME, sets_dir)
    rows, info = load_input(real_events, REAL_EVENTS_NAME, expected_md5)
    real = _check_real_events(rows)

    a_items = []
    for q in _limit(dates, limit):
        rep = backend.complete(q["prompt"], kind="dates", max_tokens=MAX_TOKENS["dates"])
        cls = SC.classify_dates(rep.text, q["prompt"])
        spec = any(SC.has_specific_name(ln, q["prompt"]) for ln in SC.event_lines(rep.text, cls))
        it = {"qid": q["qid"], "side": q["side"], "cls": cls, "specific": spec}
        if model_cutoff:
            it["cutoff_side"] = cutoff_side(q["date"], model_cutoff)
        a_items.append(it)

    mixed = sorted([{"qid": q["qid"], "kind": q["kind"], "when": q["when"], "side": q["side"],
                     "prompt": q["prompt"]} for q in fict] + real, key=lambda q: _mix_key(seed, q["qid"]))
    b_items = []
    for q in _limit(mixed, limit):
        rep = backend.complete(q["prompt"], kind="events", max_tokens=MAX_TOKENS["events"])
        cls = SC.classify_events(rep.text)
        spec = any(SC.has_specific_name(ln, q["prompt"]) for ln in SC.event_lines(rep.text, cls))
        it = {"qid": q["qid"], "kind": q["kind"], "side": q["side"], "cls": cls, "specific": spec}
        if model_cutoff:
            it["cutoff_side"] = cutoff_side(q["when"], model_cutoff)
        b_items.append(it)

    a_cls = ("unknown", "has", "other")
    b_cls = ("agree", "deny", "unknown", "other")
    a: dict[str, Any] = {side: SC.summarize_type1([i for i in a_items if i["side"] == side], a_cls)
                         for side in (S.SIDE_PRE, S.SIDE_POST)}
    a["post_minus_pre"] = {
        k: SC.diff_or_none(a[S.SIDE_POST][k], a[S.SIDE_PRE][k])
        for k in ("unknown_rate", "unknown_rate_excl_other", "specific_rate")}
    a["by_cutoff"] = _by_cutoff(a_items, a_cls, model_cutoff)
    b: dict[str, Any] = {}
    for kind in ("fictional", "real"):
        sub = [i for i in b_items if i["kind"] == kind]
        b[kind] = {"all": SC.summarize_type1(sub, b_cls),
                   **{side: SC.summarize_type1([i for i in sub if i["side"] == side], b_cls)
                      for side in (S.SIDE_PRE, S.SIDE_POST)},
                   "by_cutoff": _by_cutoff(sub, b_cls, model_cutoff)}
    b["real"]["status"] = info["status"] if real else NOT_LOADED
    fa, fx = b["fictional"]["all"]["agree_rate"], b["fictional"]["all"]["agree_rate_excl_other"]
    if real:
        ra, rx = b["real"]["all"]["agree_rate"], b["real"]["all"]["agree_rate_excl_other"]
        disc: Any = {"agree_rate": SC.diff_or_none(ra, fa), "agree_rate_excl_other": SC.diff_or_none(rx, fx)}
    else:
        ra = rx = None
        disc = NOT_LOADED
    metrics = {"a_dates": a, "b_events": b,
               "sycophancy_fictional_agree_rate": fa, "sycophancy_fictional_agree_rate_excl_other": fx,
               "real_agree_rate": ra if real else NOT_LOADED,
               "real_agree_rate_excl_other": rx if real else NOT_LOADED,
               "real_minus_fictional_agree": disc, "model_cutoff": model_cutoff}
    res = _base(1, backend, {S.TYPE1_DATES_NAME: {"md5_lf": md5_a, "n": len(dates)},
                             S.TYPE1_EVENTS_NAME: {"md5_lf": md5_b, "n": len(fict)}})
    res.update({
        "inputs": {"real_events": info}, "metrics": metrics, "items": {"a_dates": a_items, "b_events": b_items},
        "ledger_rule9": ledger_block({1: ledger_part(1, metrics)}, model_label(res["backend"])),
        "blanks": ([] if real else [f"実在の出来事={NOT_LOADED}(親が data/leak_check/{REAL_EVENTS_NAME} に置く)"])
        + ([] if model_cutoff else ["モデルの学習の締め切り(--model-cutoff)=未記入(前後をさらに分けない)"])
        + ["LLM の学習の締め切りとの関係の記入(運用規則 9 の欄)=モデルのカードから親が書く"],
        "expedients": ["判定語の表と具体名の印の規則(score の冒頭)", "日付と架空の出来事の選び方(sets)",
                       "混ぜる順=種と qid の sha256 の順"],
        "n_calls": len(a_items) + len(b_items),
    })
    return _finish(res, t0)


# ---------------------------------------------------------------------------------------------- 型 ②
def _pair_source(r: Mapping[str, Any] | None, f: Mapping[str, Any] | None) -> str | None:
    if r is None or f is None:
        return None
    return r["source"] if r["source"] == f["source"] else "mixed"


def run_type2(backend: Backend, *, limit: int | None = None, sets_dir: Path | None = None,
              human: Mapping[str, Sequence[float]] | None = None, min_mass: float = SC.MIN_MASS) -> dict[str, Any]:
    t0 = time.perf_counter()
    if not float(min_mass) > 0:
        raise ValueError("min_mass は正")
    rows, md5 = S.load_set(S.TYPE2_NAME, sets_dir)
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for r in rows:
        by_pair.setdefault(r["pair_id"], {})[r["variant"]] = r
    pair_ids = _limit(sorted(by_pair), limit)
    pairs = []
    dists_r: dict[str, list[float]] = {}
    dists_f: dict[str, list[float]] = {}
    n_unparsed = 0
    n_below_floor = 0
    for pid in pair_ids:
        rr, rf = by_pair[pid]["real"], by_pair[pid]["fictional"]
        if [c["id"] for c in rr["candidates"]] != [c["id"] for c in rf["candidates"]]:
            raise ValueError(f"{pid}: 実名版と架空名版の候補が違う")
        k = len(rr["candidates"])
        mentions = [bool(c["mentions_name"]) for c in rr["candidates"]]
        got = {}
        for v, row in (("real", rr), ("fictional", rf)):
            rep = backend.complete(row["prompt"], kind="choice", max_tokens=MAX_TOKENS["choice"], want_logprobs=True)
            got[v] = SC.choice_distribution(rep.text, rep.top_logprobs, k, min_mass)
            if got[v] is not None and got[v]["fallback"] == "below_floor":
                n_below_floor += 1
        src = _pair_source(got["real"], got["fictional"])
        rec: dict[str, Any] = {"pair_id": pid, "target": rr["target"], "target_group": rr["target_group"],
                               "k": k, "source": src, "jsd": None, "top1_real": None, "top1_fictional": None,
                               "top1_same": None, "name_mass_real": None, "name_mass_fictional": None,
                               "name_shift": None, "coverage_real": None, "coverage_fictional": None,
                               "fallback_real": None, "fallback_fictional": None}
        if src is None:
            n_unparsed += 1
        else:
            pr, pf = got["real"]["p"], got["fictional"]["p"]
            if src == "logprobs":
                dists_r[pid], dists_f[pid] = pr, pf
            mr, mf = SC.name_mass(pr, mentions), SC.name_mass(pf, mentions)
            rec.update({"jsd": SC.jsd(pr, pf), "top1_real": SC.top1(pr), "top1_fictional": SC.top1(pf),
                        "top1_same": SC.top1(pr) == SC.top1(pf), "name_mass_real": mr, "name_mass_fictional": mf,
                        "name_shift": SC.diff_or_none(mr, mf), "coverage_real": got["real"]["coverage"],
                        "coverage_fictional": got["fictional"]["coverage"],
                        "fallback_real": got["real"]["fallback"], "fallback_fictional": got["fictional"]["fallback"]})
        pairs.append(rec)
    groups = sorted({p["target_group"] for p in pairs})
    by_source = {s: SC.summarize_pairs([p for p in pairs if p["source"] == s]) for s in SOURCES}
    primary = "logprobs" if by_source["logprobs"]["n_pairs"] else ("text" if by_source["text"]["n_pairs"] else None)
    metrics = {"by_source": by_source, "primary_source": primary,
               "by_group": {g: {s: SC.summarize_pairs([p for p in pairs if p["target_group"] == g and p["source"] == s])
                                for s in SOURCES} for g in groups},
               "n_pairs": len(pairs), "n_unparsed_pairs": n_unparsed, "n_below_floor_variants": n_below_floor,
               "min_mass": float(min_mass),
               "performance_gap": SC.performance_gap(dists_r, dists_f, human)}
    res = _base(2, backend, {S.TYPE2_NAME: {"md5_lf": md5, "n": len(rows), "n_pairs": len(by_pair)}})
    res.update({
        "metrics": metrics, "items": pairs,
        "ledger_rule9": ledger_block({2: ledger_part(2, metrics)}, model_label(res["backend"])),
        "blanks": ["Glasserman & Lin 型の成績の差=人の分布(回答 11-01 §7 の (d))の後(logprobs の対だけで測る)",
                   "架空名が実在しないことの確認=親(検収 Q5)"],
        "expedients": ["場面と候補の文・架空名(sets)",
                       f"1 トークン目の上位 20 の確率を番号に集める・番号の確率の和が {float(min_mass):g} より小さければ本文の番号",
                       "候補の並びは実名版と架空名版で同じに固定"],
        "n_calls": 2 * len(pair_ids),
    })
    return _finish(res, t0)


# ---------------------------------------------------------------------------------------------- 型 ④
def _refs(rows: Sequence[Mapping[str, Any]], prefix_chars: int, cont_chars: int) -> tuple[list[dict[str, Any]], int]:
    out, skipped = [], 0
    seen: set[str] = set()
    for r in rows:
        rid, name = str(r.get("id", "")), str(r.get("name", ""))
        if not rid or rid in seen or not name:
            raise InputMismatch(f"参照の id か name が空・重複: {rid!r}")
        seen.add(rid)
        if "prefix" in r and "continuation" in r:
            prefix, cont = str(r["prefix"]), str(r["continuation"])
        else:
            text = str(r.get("text", ""))
            prefix, cont = text[:int(prefix_chars)], text[int(prefix_chars):int(prefix_chars) + int(cont_chars)]
        if not prefix or not cont:
            skipped += 1
            continue
        out.append({"id": rid, "name": name, "prefix": prefix, "continuation": cont})
    return out, skipped


def run_type4(backend: Backend, *, recall_refs: Path | None = None, expected_md5: str | None = None,
              prefix_chars: int = DEFAULT_PREFIX_CHARS, cont_chars: int = DEFAULT_CONT_CHARS,
              limit: int | None = None, sets_dir: Path | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    if int(prefix_chars) < 1 or int(cont_chars) < 1:
        raise ValueError("prefix_chars と cont_chars は 1 以上")
    templates, md5 = S.load_set(S.TYPE4_NAME, sets_dir)
    rows, info = load_input(recall_refs, RECALL_REFS_NAME, expected_md5)
    refs, skipped = _refs(rows, prefix_chars, cont_chars)
    refs = _limit(refs, limit)
    items = []
    for ref in refs:
        for t in templates:
            prompt = str(t["template"]).format(name=ref["name"], prefix=ref["prefix"])
            rep = backend.complete(prompt, kind="recall", max_tokens=MAX_TOKENS["recall"])
            sc = SC.recall_scores(rep.text, ref["continuation"])
            items.append({"id": ref["id"], "template_id": t["template_id"], **sc})
    tids = [t["template_id"] for t in templates]
    if not refs:
        metrics: dict[str, Any] = {"status": NOT_LOADED if info["status"] == NOT_LOADED else "参照が空",
                                   "by_template": {tid: None for tid in tids}, "guided_minus_general": None}
    else:
        by_t = {tid: SC.summarize_recall([i for i in items if i["template_id"] == tid]) for tid in tids}
        g = {i["id"]: i["lcs_recall"] for i in items if i["template_id"] == "guided"}
        n = {i["id"]: i["lcs_recall"] for i in items if i["template_id"] == "general"}
        diffs = [g[k] - n[k] for k in sorted(set(g) & set(n)) if g[k] is not None and n[k] is not None]
        pos, neg = sum(1 for d in diffs if d > 0), sum(1 for d in diffs if d < 0)
        metrics = {"status": "測った", "by_template": by_t,
                   "guided_minus_general": {"lcs_recall_mean": SC.mean_or_none(diffs), "n": len(diffs), "pos": pos,
                                            "neg": neg, "sign_p": SC.sign_test_p(pos, neg)}}
    metrics.update({"prefix_chars": int(prefix_chars), "cont_chars": int(cont_chars), "skipped_refs": skipped,
                    "partial_min_chars": SC.PARTIAL_MIN_CHARS})
    res = _base(4, backend, {S.TYPE4_NAME: {"md5_lf": md5, "n": len(templates)}})
    res.update({
        "inputs": {"recall_refs": info}, "metrics": metrics, "items": items,
        "ledger_rule9": ledger_block({4: ledger_part(4, metrics)}, model_label(res["backend"])),
        "blanks": ([] if refs else [f"参照={NOT_LOADED}(親が data/leak_check/{RECALL_REFS_NAME} に置く)"]),
        "expedients": [f"冒頭 {int(prefix_chars)} 字・続き {int(cont_chars)} 字",
                       f"部分一致=正規化した後の連続する共通の部分が {SC.PARTIAL_MIN_CHARS} 字以上"],
        "n_calls": len(items),
    })
    return _finish(res, t0)


# ---------------------------------------------------------------------------------------------- 台帳の 1 行
def ledger_part(type_no: int, metrics: Mapping[str, Any]) -> str:
    """運用規則 9 の欄に写す型ごとの短い文。"""
    if type_no == 1:
        a = metrics["a_dates"]
        pre, post = a[S.SIDE_PRE], a[S.SIDE_POST]
        real = metrics.get("real_agree_rate")
        disc = metrics.get("real_minus_fictional_agree")
        disc_s = disc if isinstance(disc, str) else _signed(disc["agree_rate"], 2)
        cut = metrics.get("model_cutoff")
        return (f"型① 時点後 分からない {_fmt(post['unknown_rate'], 2)}・具体名 {_fmt(post['specific_rate'], 2)}"
                f"(時点前 {_fmt(pre['unknown_rate'], 2)}・{_fmt(pre['specific_rate'], 2)})"
                f"・架空への同意 {_fmt(metrics['sycophancy_fictional_agree_rate'], 2)}"
                f"・実在への同意 {_fmt(real, 2)}・実在 − 架空 {disc_s}"
                f"・締め切り {cut or '未記入'}")
    if type_no == 2:
        src = metrics.get("primary_source")
        if src is None:
            return "型② 読めた対なし"
        m = metrics["by_source"][src]
        cnt = "・".join(f"{s} {metrics['by_source'][s]['n_pairs']}" for s in SOURCES)
        return (f"型② [{src}] JSD 平均 {_fmt(m['jsd_mean'])}・1 位の一致 {_fmt(m['top1_agree'], 2)}"
                f"・名の向き {_signed(m['name_shift_mean'])}(符号 p={_fmt(m['name_shift_sign_p'], 2)})"
                f"(対 {cnt}・下限で本文へ {metrics['n_below_floor_variants']})")
    if type_no == 4:
        if metrics.get("status") != "測った":
            return f"型④ {metrics.get('status', NOT_LOADED)}"
        g = metrics["by_template"]["guided"]
        n = metrics["by_template"]["general"]
        d = metrics["guided_minus_general"]
        return (f"型④ 最長共通部分列の率 guided {_fmt(g['lcs_recall_mean'], 2)}・general {_fmt(n['lcs_recall_mean'], 2)}"
                f"(差 {_signed(d['lcs_recall_mean'], 2)}・符号 p={_fmt(d['sign_p'], 2)})・完全一致 {_fmt(g['exact_rate'], 2)}")
    raise ValueError(f"型は 1・2・4(いま {type_no})")


def ledger_block(parts: Mapping[int, str], model: str) -> dict[str, Any]:
    """型 ①②④ の文をまとめた 1 行(頭にモデル名と版・測っていない型は「未測」)。"""
    full = {t: parts.get(t, f"型{'①②④'[(1, 2, 4).index(t)]} {UNMEASURED}") for t in (1, 2, 4)}
    return {"line": f"疑い(モデル {model}): " + " / ".join(full[t] for t in (1, 2, 4)), "model": model,
            "parts": {f"type{t}": parts.get(t) for t in (1, 2, 4)}}


def merge_ledger(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """いくつかの ``result.json`` の型ごとの文を 1 行にまとめる(同じ型が 2 つあれば後の方)。

    モデルの違う result を混ぜると ``ValueError``(台帳の 1 行はモデルごと)。
    """
    parts: dict[int, str] = {}
    models = sorted({str(r.get("ledger_rule9", {}).get("model", "")) for r in results})
    if len(models) != 1:
        raise ValueError(f"モデルの違う記録は 1 行にまとめない: {models}")
    for r in results:
        for t in (1, 2, 4):
            p = r.get("ledger_rule9", {}).get("parts", {}).get(f"type{t}")
            if p:
                parts[t] = p
    return ledger_block(parts, models[0])


# ---------------------------------------------------------------------------------------------- 表
def _t1_row(label: str, x: Mapping[str, Any], cls: Sequence[str]) -> str:
    cells = [f"{_fmt(x[f'{c}_rate'])}" for c in cls] + [
        f"{_fmt(x.get(f'{c}_rate_excl_other'))}" for c in cls if c != "other"]
    return f"| {label} | {x['n']} | " + " | ".join(cells) + f" | {_fmt(x['specific_rate'])} |"


def _t1_head(cls: Sequence[str]) -> list[str]:
    cols = list(cls) + [f"{c}(other 除く)" for c in cls if c != "other"]
    return ["| 側 | 件 | " + " | ".join(cols) + " | 具体名 |", "|---|---:|" + "---:|" * (len(cols) + 1)]


def to_markdown(res: Mapping[str, Any]) -> str:
    b = res["backend"]
    lines = [f"# 漏洩の検査 型{res['type']}「{res['type_name']}」", "",
             f"- 世界の時点: {res['world_date']}・当て口: {b.get('kind')}・モデル: {model_label(b)}",
             "- 問いの集合: " + "・".join(f"{k}(md5 {v['md5_lf']}・{v['n']} 行)" for k, v in res["question_sets"].items()),
             f"- 呼の数: {res.get('n_calls')}・digest: {res.get('digest')}", ""]
    m = res["metrics"]
    if res["type"] == 1:
        a = m["a_dates"]
        a_cls, b_cls = ("unknown", "has", "other"), ("agree", "deny", "unknown", "other")
        lines += ["## (a) 日付を指定して出来事を問う", ""] + _t1_head(a_cls)
        for side in (S.SIDE_PRE, S.SIDE_POST):
            lines.append(_t1_row(side, a[side], a_cls))
            if a["by_cutoff"]:
                for cs in CUTOFF_SIDES:
                    lines.append(_t1_row(f"{side}/{cs}", a["by_cutoff"][side][cs], a_cls))
        d = a["post_minus_pre"]
        lines += ["", f"後 − 前: 分からない {_signed(d['unknown_rate'])}(other 除く {_signed(d['unknown_rate_excl_other'])})"
                  f"・具体名 {_signed(d['specific_rate'])}", "",
                  "## (b) 出来事を知っているか(架空と実在を混ぜる)", ""] + _t1_head(b_cls)
        for kind in ("fictional", "real"):
            for side in ("all", S.SIDE_PRE, S.SIDE_POST):
                lines.append(_t1_row(f"{kind}/{side}", m["b_events"][kind][side], b_cls))
            bc = m["b_events"][kind]["by_cutoff"]
            if bc:
                for side in (S.SIDE_PRE, S.SIDE_POST):
                    for cs in CUTOFF_SIDES:
                        lines.append(_t1_row(f"{kind}/{side}/{cs}", bc[side][cs], b_cls))
        disc = m["real_minus_fictional_agree"]
        disc_s = disc if isinstance(disc, str) else (f"{_signed(disc['agree_rate'])}"
                                                     f"(other 除く {_signed(disc['agree_rate_excl_other'])})")
        lines += ["", f"実在の出来事: {m['b_events']['real']['status']}・実在 − 架空 の同意: {disc_s}"
                  f"・モデルの締め切り: {m['model_cutoff'] or '未記入'}"]
    elif res["type"] == 2:
        lines += ["| 群 | 出所 | 対 | 採点 | JSD 平均 | JSD 中央 | 1 位の一致 | 名の向き | 向き + / − | 符号 p | 被覆 |",
                  "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        rows = [("全体", m["by_source"])] + sorted(m["by_group"].items())
        for g, per in rows:
            for s in SOURCES:
                x = per[s]
                if not x["n_pairs"]:
                    continue
                lines.append(f"| {g} | {s} | {x['n_pairs']} | {x['n_scored']} | {_fmt(x['jsd_mean'])} | "
                             f"{_fmt(x['jsd_median'])} | {_fmt(x['top1_agree'])} | {_signed(x['name_shift_mean'])} | "
                             f"{x['name_shift_pos']} / {x['name_shift_neg']} | {_fmt(x['name_shift_sign_p'])} | "
                             f"{_fmt(x['coverage_mean'])} |")
        pg = m["performance_gap"]
        lines += ["", f"出所は混ぜない(logprobs・本文・混ざり=片方ずつ違う)。読めない対 {m['n_unparsed_pairs']}"
                  f"・番号の確率の和が下限 {m['min_mass']:g} より小さく本文へ落とした行 {m['n_below_floor_variants']}",
                  f"成績の差(Glasserman & Lin 型): {pg['status']}・差 {_signed(pg['gap'])}"]
    else:
        lines += [f"状態: {m['status']}・冒頭 {m['prefix_chars']} 字・続き {m['cont_chars']} 字・飛ばした参照 {m['skipped_refs']}", "",
                  "| 指示 | 件 | 完全一致 | 部分一致 | 最長共通部分列の率 | F |", "|---|---:|---:|---:|---:|---:|"]
        for tid, x in m["by_template"].items():
            if x is None:
                lines.append(f"| {tid} | 0 | — | — | — | — |")
            else:
                lines.append(f"| {tid} | {x['n']} | {_fmt(x['exact_rate'])} | {_fmt(x['partial_rate'])} | "
                             f"{_fmt(x['lcs_recall_mean'])} | {_fmt(x['lcs_f1_mean'])} |")
    lines += ["", "## パターン台帳 運用規則 9 の欄に写す 1 行(パターンの行ごとに同じ行を写す)", "",
              res["ledger_rule9"]["line"], ""]
    if res.get("blanks"):
        lines += ["## 空欄", ""] + [f"- {x}" for x in res["blanks"]] + [""]
    lines += ["## expedient", ""] + [f"- {x}" for x in res.get("expedients", [])] + ["", f"- {res['not_in_scope']}", ""]
    return "\n".join(lines)
