"""run_day の静的な地図(HEAD 0389689 の engine/run.py)。読むだけ。

出力: 区間ごとの run_day 局所名の 読み/束縛/変更(属性・添字の代入・変更するメソッドの呼び出し)、
入れ子の関数の自由変数、区間をまたいで共有される名前、tick ループで前の tick から持ち越される名前。
"""
from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(sys.argv[1])  # src/shibuya/engine/run.py
OUT = Path(sys.argv[2])

# 区間(HEAD 0389689 の行番号・両端を含む)。名前は草案の表と同じ。
SEGMENTS = [
    ("S0 引数の指紋・暦・再開の見出し", 2411, 2498),
    ("S1 腕の検査・選び手・方策・mock", 2499, 2677),
    ("S2 塩・テープ・会話・母集団・SoA 確保・初期化・エネルギー", 2678, 2777),
    ("S3 世界過程・計画実行層・開始日", 2779, 2853),
    ("S4 知覚・橋・艦隊・検出・幾何・アービタ", 2855, 2978),
    ("S5 計画境界・方策の結線・層(活動/意図/親しみ/記憶/店/関係/口コミ)", 2980, 3196),
    ("S6 _utter・RunResult・計器・tick をまたぐ入れ物", 3198, 3297),
    ("S7 入れ子の関数(到着・ハッシュ・日の頭/締め・保存)", 3298, 3592),
    ("S8 再開の復元", 3593, 3630),
    ("L0 日の頭(_relay_tables・_start_day)", 3632, 3635),
    ("L1 体の更新・範囲外の食事", 3636, 3651),
    ("L2 世界過程 runner.step", 3652, 3657),
    ("L3 計画実行層 presence.step", 3658, 3670),
    ("L4 知覚の前計算 prepare_tick", 3671, 3691),
    ("L5 到着の受け取り(delay=1)", 3692, 3695),
    ("L6 ① 応答の反映(招待の解決・intents_from_responses・焦点)", 3696, 3812),
    ("L7 ② 変化検出と活動/意図の抑止・満了入口", 3813, 3840),
    ("L8 計画境界の起床と就寝", 3841, 3886),
    ("L9 自宅の食事", 3887, 3894),
    ("L10 会話ターン・顕著行為の起床候補", 3895, 3911),
    ("L11 到着(delay=2)・艦隊の再投入", 3912, 3938),
    ("L12 抑止の例外・歩く退出・知人出現・候補の組み立て", 3939, 4005),
    ("L13 ③ アービタ・起床率", 4006, 4026),
    ("L14 ④ 呼(mock/再生/艦隊)", 4027, 4154),
    ("L15 ⑤ Phase A", 4155, 4183),
    ("L16 ⑥ Phase B", 4184, 4190),
    ("L17 ⑦ Phase C と結果の積算", 4191, 4249),
    ("L18 会話セッション", 4250, 4383),
    ("L19 活動層・意図の後処理", 4384, 4394),
    ("L20 記憶・親しみ・エネルギーの tick の後", 4395, 4428),
    ("L21 診断の行", 4429, 4460),
    ("L22 在圏の標本・計器・在圏 journal", 4461, 4477),
    ("L23 checkpoint", 4478, 4526),
    ("L24 途中の日の締めと保存", 4527, 4532),
    ("E0 止めたラン・艦隊/再生の吸い切り", 4533, 4581),
    ("E1 締め・締めの後のハッシュ・保存", 4582, 4623),
    ("E2 結果の組み立て", 4624, 4903),
    ("E3 状態成長の検査", 4904, 4947),
    ("E4 再開の欄・在圏の書き出し", 4948, 4979),
]
MUTATORS = {"append", "extend", "clear", "pop", "add", "discard", "update", "setdefault", "remove",
            "insert", "popitem", "fill"}

tree = ast.parse(SRC.read_text(encoding="utf-8"))
rd = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_day")
params = {a.arg for a in rd.args.args + rd.args.kwonlyargs}


def own_nodes(fn: ast.AST):
    """fn の本体のノード(入れ子の def の中は含めない・def の名前は含める)。"""
    stack = list(ast.iter_child_nodes(fn))
    while stack:
        n = stack.pop()
        yield n
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        stack.extend(ast.iter_child_nodes(n))


locals_ = set(params)
nested = []
for n in own_nodes(rd):
    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
        locals_.add(n.id)
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        locals_.add(n.name)
        nested.append(n)
    if isinstance(n, ast.arg):
        pass
# 入れ子の入れ子(_session_partners・_revert・_classical_acq・_classical_partner)も拾う
all_nested = []
for n in ast.walk(rd):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not rd:
        all_nested.append(n)


def root(expr):
    while isinstance(expr, (ast.Attribute, ast.Subscript, ast.Starred)):
        expr = expr.value
    return expr.id if isinstance(expr, ast.Name) else None


def classify(nodes):
    reads, binds, muts = set(), set(), set()
    for n in nodes:
        if isinstance(n, ast.Name) and n.id in locals_:
            if isinstance(n.ctx, ast.Load):
                reads.add(n.id)
            else:
                binds.add(n.id)
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            tgs = n.targets if isinstance(n, ast.Assign) else [n.target]
            flat = []
            for t in tgs:
                flat.extend(t.elts if isinstance(t, (ast.Tuple, ast.List)) else [t])
            for t in flat:
                if isinstance(t, (ast.Attribute, ast.Subscript)):
                    r = root(t)
                    if r in locals_:
                        muts.add(r)
                if isinstance(n, ast.AugAssign) and isinstance(t, ast.Name) and t.id in locals_:
                    reads.add(t.id)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in MUTATORS:
            r = root(n.func.value)
            if r in locals_:
                muts.add(r)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "at":
            if n.args:
                r = root(n.args[0])
                if r in locals_:
                    muts.add(r)
    return reads, binds, muts


def nodes_in_range(lo, hi):
    out = []
    for n in own_nodes(rd):
        ln = getattr(n, "lineno", None)
        if ln is not None and lo <= ln <= hi:
            out.append(n)
    # lambda と入れ子の def の中の読みも区間の読みに数える(def 自体は S7 などの区間に属する)
    return out


seg_info = {}
for name, lo, hi in SEGMENTS:
    ns = nodes_in_range(lo, hi)
    # 区間の中で呼ばれる入れ子の関数
    calls = sorted({n.func.id for n in ns if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id in {f.name for f in all_nested}})
    r, b, m = classify(ns)
    seg_info[name] = {"lines": [lo, hi], "n_lines": hi - lo + 1, "reads": sorted(r), "binds": sorted(b),
                      "mutates": sorted(m), "calls_nested": calls}

nested_info = {}
for f in all_nested:
    body_nodes = list(ast.walk(f))
    inner_locals = {a.arg for a in f.args.args + f.args.kwonlyargs}
    for n in body_nodes:
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            inner_locals.add(n.id)
    nonlocal_ = sorted({nm for n in body_nodes if isinstance(n, ast.Nonlocal) for nm in n.names})
    r, b, m = classify(body_nodes)
    free_r = sorted((r - inner_locals) | set(nonlocal_))
    nested_info[f.name] = {
        "lines": [f.lineno, f.end_lineno], "n_lines": f.end_lineno - f.lineno + 1,
        "free_reads": free_r, "nonlocal": nonlocal_, "mutates_free": sorted(m - inner_locals),
    }

# 共有: 2 区間以上で触る名前
touch = defaultdict(set)
writers = defaultdict(set)
for name, d in seg_info.items():
    for x in set(d["reads"]) | set(d["binds"]) | set(d["mutates"]):
        touch[x].add(name.split()[0])
    for x in set(d["binds"]) | set(d["mutates"]):
        writers[x].add(name.split()[0])
shared = {x: {"segments": sorted(s), "writers": sorted(writers.get(x, ()))}
          for x, s in touch.items() if len(s) >= 2}

# tick ループで持ち越す名前: L 区間で書かれ、それより前の L 区間(次の tick)で読まれる
order = [n.split()[0] for n, _, _ in SEGMENTS if n.startswith("L")]
carried = {}
for x in shared:
    w_l = [s for s in writers.get(x, ()) if s.startswith("L")]
    r_l = [s for s in touch[x] if s.startswith("L") and x in seg_info[[k for k in seg_info if k.split()[0] == s][0]]["reads"]]
    if w_l and r_l:
        last_w = max(order.index(s) for s in w_l)
        first_r = min(order.index(s) for s in r_l)
        if first_r <= last_w:
            carried[x] = {"written_in": sorted(w_l, key=order.index), "read_in": sorted(r_l, key=order.index)}

out = {
    "source": "engine/run.py @ HEAD 0389689",
    "run_day_lines": [rd.lineno, rd.end_lineno],
    "run_day_n_lines": rd.end_lineno - rd.lineno + 1,
    "n_params": len(params),
    "n_locals": len(locals_),
    "n_nested_direct": len(nested),
    "nested_direct": [f.name for f in nested],
    "n_nested_all": len(all_nested),
    "segments": seg_info,
    "nested": nested_info,
    "n_shared": len(shared),
    "shared": shared,
    "loop_carried": carried,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({k: out[k] for k in ("run_day_lines", "run_day_n_lines", "n_params", "n_locals",
                                      "n_nested_direct", "nested_direct", "n_nested_all", "n_shared")},
                 ensure_ascii=False))
print("loop_carried:", json.dumps(carried, ensure_ascii=False))

# ---- 精密版: tick ループの本体(3632〜4531)で、行の順に「最初の読み」と「最初の束縛」を比べる ----
LOOP_LO, LOOP_HI = 3632, 4531
nested_by_name = {f.name: nested_info[f.name] for f in all_nested}
events = defaultdict(list)  # name -> [(line, kind)]
for n in own_nodes(rd):
    ln = getattr(n, "lineno", None)
    if ln is None or not (LOOP_LO <= ln <= LOOP_HI):
        continue
    if isinstance(n, ast.Name) and n.id in locals_:
        events[n.id].append((ln, "r" if isinstance(n.ctx, ast.Load) else "b"))
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in nested_by_name:
        for x in nested_by_name[n.func.id]["free_reads"]:
            events[x].append((ln, "r"))
        for x in nested_by_name[n.func.id]["mutates_free"]:
            events[x].append((ln, "m"))
for n in own_nodes(rd):
    ln = getattr(n, "lineno", None)
    if ln is None or not (LOOP_LO <= ln <= LOOP_HI):
        continue
    _r, _b, _m = classify([n])
    for x in _m:
        events[x].append((ln, "m"))
loop_vars = {}
for x, ev in events.items():
    ev.sort()
    first_r = next((l for l, k in ev if k == "r"), None)
    first_b = next((l for l, k in ev if k == "b"), None)
    muts = sorted({l for l, k in ev if k == "m"})
    if first_b is not None and first_r is not None and first_r < first_b:
        cat = "carried_rebind"   # 前の tick の束縛を読む
    elif first_b is not None:
        cat = "tick_local"
    elif muts:
        cat = "persistent_mutated"  # ループの外で作り、ループの中で中身を変える
    else:
        cat = "read_only"
    loop_vars[x] = {"cat": cat, "first_read": first_r, "first_bind": first_b, "mut_lines": muts[:12],
                    "n_mut": len(muts)}
by_cat = defaultdict(list)
for x, d in loop_vars.items():
    by_cat[d["cat"]].append(x)
out["loop_vars"] = loop_vars
out["loop_vars_by_cat"] = {k: sorted(v) for k, v in by_cat.items()}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print({k: len(v) for k, v in by_cat.items()})
for k in ("carried_rebind", "persistent_mutated"):
    print(k, sorted(by_cat[k]))
