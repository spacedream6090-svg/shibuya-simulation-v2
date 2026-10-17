# -*- coding: utf-8 -*-
"""measure_refractory — 第 2 期 2-0b **不応期を外した腕の計測**(記録だけ・エンジン不変)。

正典
    回答 ``docs/design/v2-answers-2026-10-13b.md`` §4-2 の 3(GPU の前に「不応期を外した腕を mock で回し、判断の
    呼び出しの数がどれだけ増えるかを測っておく(GPU 後の必要量の見積り)」)・計画
    ``docs/design/v2-implementation-plan-2026-10-12.md`` の 2-0b の行(記録だけ・既定は変えない)。
    不応期の表は ``shibuya.agents.state``(``WakeCondition`` の 11 行・``REFRACTORY_MINUTES``)。つなぎの台帳の
    ``BR-REFRACTORY-*``(11 行・remove_at T3)。

腕(新しい腕は作らない=既存の ``--refractory-scale COND=FACTOR``・ablation ③ を使う)
    A   既定(§6 の不応期表どおり・``refractory_scale`` を渡さない)。
    B   11 種とも 0(``--refractory-scale`` を 11 個並べる・FACTOR=0)。
    Ck  k 番目の条件だけ 0(k=1..11・``WakeCondition`` の値 k-1)。どの条件が呼数を増やすかの分解。
    FACTOR=0 は ``engine.resolve.refractory_ticks`` が「床なし」として受け付ける(``floor(0×分+0.5)=0`` 分)。
    不応期 0 刻みのタイマーは ``until = 刻み+0`` で、アービタの抑止 ``refractory_until > 刻み`` が偽=抑止しない。

構成(``byte_check_10e`` の表=``wave2_bytecheck.configs()`` の kw をそのまま)
    ``w6_v3_default``・``v3_mem_rel``・``w6_v1_default``。方策は mock(``policy="mock"`` を明示して渡す=CLI の既定と同じ値)。
    seed 1 を本則・``w6_v3_default`` だけ seed 2・3 も(ばらつき)。5,000 体・1 シミュ日。

段(どれも src を変えない)
    ``arms``   腕の一覧と ``--refractory-scale`` の並びを出す(手で CLI を回すときの写し)。
    ``one``    1 本(構成 × 腕 × seed)を ``shibuya.cli.run`` で回し、行(JSON)を 1 つ書く。
    ``run``    ``one`` を子プロセスで並べて回し(``--src`` を ``PYTHONPATH`` に・``cwd`` はリポの根)、行を
               ``<scratch>/rows`` に貯める(在る行は回さない=再開できる)。終われば ``table`` と同じ集計を書く。
    ``table``  行から ``refractory_calls.json`` と ``refractory_calls.md`` を作る(呼数・倍率・C1〜C11 の増分の順位・
               39 万体への外挿)。
    ``same``   2 回のランの行を (構成, 腕, seed, 体数) ごとに比べる(決定論の確かめ・壁時計は除く)。

追記(親の指示・2026-10-14)
    - 活動層を層ごと off にした量: 構成 ``w6_v3_activity_off``(語彙 v3・活動層 off)の A・B(seed 1)を足し、活動層
      on/off で倍率 B/A と場所の変化(CELL_BLOCK)の増分を並べる(``activity_gate``)。層ごと off は門(活動中の場所の
      変化の候補の落とし)だけでなく、活動の満了の起床・活動の設定・あたり歩行なども一緒に外す(腕 A も変わる)。
      門だけを外す口は src に無いので、門だけの重みは測っていない。
    - 体数の確かめ: ``w6_v3_default`` seed 1 を 20,000 体でも A・B を回し、体あたりの倍率を 5,000 体と比べる
      (``scale_check``)。5,000 体以外の行の名には ``__n<体数>`` を付ける。
    - 不応期の表の外の門の一覧(主なもの・網羅ではない。名と出典=ファイル+記号だけ・行番号なし)を ``gates_outside_table`` に載せる。

使い方(リポの根で・作業木の src)::

    python docs/bench/analysis/wallbounce-1012/refr20b/tools/measure_refractory.py run \\
        --src src --scratch <作業用> --out-dir docs/bench/analysis/wallbounce-1012/refr20b --jobs 3
    python docs/bench/analysis/wallbounce-1012/refr20b/tools/measure_refractory.py table \\
        --rows-dir <作業用>/rows --out-dir docs/bench/analysis/wallbounce-1012/refr20b

集めるもの(1 行)
    呼数(``llm_calls``)・``calls_by_model``(manifest の欄)・起床条件ごとの発射数(``calls_by_condition``=アービタが
    合流した後の代表の条件)・時ごとの発射数・候補と合流の延べ(診断の列)・アービタの 4 列 × 4 クラス
    (``suppressed``=不応期の抑止を含む)・就寝抑止(``sleep_suppressed``)・域外抑止・会話(開いたセッション・
    診断の ``conversations``・会話の管理の計数)・L4 の監査欄・final(動くのは当然=記録だけ)・壁時計。

外挿(``extrapolate``)
    39 万体(W16 の 390,067 人=10e の ``budget_10e.json`` の ``n_full``)の既定の呼数は、10e の記録
    (``10e/sides/ret.json`` の 5,000 体の呼数=§締め-1 の ACT の行)を体数に比例させた値(**推測**=10e の
    外挿と同じ線形)。腕 B の倍率を掛けて 1 日・7 日(1 日の値 × 7=曜日の違いは測っていない)。

宣言(未リサーチ=expedient)
    - 判断モデルと LLM の分け方: 今の版の ``calls_by_model`` は判断モデル 0・LLM=全呼(判断モデルはまだ無い)。
      見積りの行では CLAUDE.md §3 の線(日常の判断=判断モデル・会話=LLM)に合わせ、会話ターン
      (``CONVERSATION_TURN``)の呼を LLM・それ以外を判断モデルに分けた**仮の割り**も併記する(よく考える判断を
      LLM に上げる分は mock では測れない=LLM は下限・判断モデルは上限)。
    - C の順位: 増分(Ck − A)の降順・同点は条件の番号の昇順(決定的)。
逐次ループ宣言: 行の数(構成 × 腕 × seed ≤ 65)と条件の数(11)だけ。体の数に比例するループは無い。
絶対パスは JSON と Markdown に書かない(名だけ)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REFR = HERE.parent
#: tools(HERE) → refr20b → wallbounce-1012 → analysis → bench → docs → リポの根。
REPO = HERE.parents[5]
TOOL_REL = "docs/bench/analysis/wallbounce-1012/refr20b/tools/measure_refractory.py"
BYTE_CHECK_10E = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "10e" / "byte_check_10e.py"
TEN_E_RET = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "10e" / "sides" / "ret.json"
TEN_E_BUDGET = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "10e" / "budget_10e.json"
TEN_E_RET_REL = "docs/bench/analysis/wallbounce-1012/10e/sides/ret.json"
TEN_E_BUDGET_REL = "docs/bench/analysis/wallbounce-1012/10e/budget_10e.json"

SCHEMA_ROW = "shibuya.bench/refr20b-row/1"
SCHEMA_TABLE = "shibuya.bench/refr20b-table/1"

#: 測る構成(``byte_check_10e`` の表の名)。
CONFIGS: tuple[str, ...] = ("w6_v3_default", "v3_mem_rel", "w6_v1_default")
#: 追記で足した構成(腕 A・B・seed 1 だけ回す)。``byte_check_10e`` の表の名。
EXTRA_CONFIGS: tuple[str, ...] = ("w6_v3_activity_off",)
ALL_CONFIGS: tuple[str, ...] = (*CONFIGS, *EXTRA_CONFIGS)
#: 活動層を層ごと off にした量を見る対(活動層 on, off)。
ACTIVITY_GATE_PAIR: tuple[str, str] = ("w6_v3_default", "w6_v3_activity_off")
#: 本則の seed。
SEED_MAIN: int = 1
#: ばらつきを見る構成と追加の seed。
EXTRA_SEEDS: dict[str, tuple[int, ...]] = {"w6_v3_default": (2, 3)}
#: 腕 B・Ck で掛ける倍率(``--refractory-scale COND=0``)。
FACTOR_TEXT: str = "0"
#: 体数(本則)。
N_AGENTS: int = 5_000
#: 外挿の日数。
DAYS_WEEK: int = 7
#: 不応期の表(11 行)の外で「いつ考えるか」をエンジンが決めている門(名と出典だけ)。
#: 出典は「<ファイル> <記号>(注)」。記号が 2 つあれば「・」でつなぐ。行番号は書かない(並行の段の変更で
#: ずれるため)。試験は当該のファイルにその記号の定義(``def 記号`` か ``記号:``/``記号 =``)があることを照らす。
GATES_OUTSIDE_TABLE: tuple[dict[str, str], ...] = (
    {"name": "活動層の候補の落とし(活動中の体の場所の変化 CELL_BLOCK・語彙 v3 の活動層 on のとき)",
     "source": "src/shibuya/engine/activity.py suppress_cell_block(ActivityLayer の関数)"},
    {"name": "就寝抑止(D-56)",
     "source": "src/shibuya/engine/arbiter.py sleep_suppressed_total(Arbiter の累計。門は arbitrate の ⓪-b)"},
    {"name": "域外抑止(D-66)",
     "source": "src/shibuya/engine/arbiter.py outside_suppressed_total(Arbiter の累計。門は arbitrate の ⓪-a)"},
    {"name": "アービタの合流(同じ体の起床は 1 刻み 1 呼)",
     "source": "src/shibuya/engine/arbiter.py merged_total(Arbiter の累計。門は arbitrate の ③。知覚契約書 §6 運用規定②)"},
    {"name": "会話の招待の間隔(同じ対 60 分・同じ招待側 30 分)",
     "source": "src/shibuya/engine/conversation.py PAIR_INVITE_REFRACTORY_TICKS・SPEAKER_INVITE_REFRACTORY_TICKS"},
    {"name": "知人出現の同一相手の間隔(60 分・関係 on のとき)",
     "source": "src/shibuya/engine/relations.py REL_ACQ_PAIR_REFRACTORY_MIN"},
    {"name": "意図の保持(意図を持つ体の場所の変化 CELL_BLOCK と活動の満了の候補を落とす・既定 v3 で働く)",
     "source": "src/shibuya/engine/intent.py suppress_wakes(IntentLayer の関数)"},
    {"name": "就寝境界をエンジンが実行する(D-62 (a)・判断を呼ばない・plan_sleep は既定 on)",
     "source": "src/shibuya/engine/systems/body.py sys_plan_boundary・to_bed(D-62 の分岐)"},
)


def gate_refs(entry: Mapping[str, str]) -> list[tuple[str, str]]:
    """``GATES_OUTSIDE_TABLE`` の 1 行の出典 → ``[(ファイル, 記号)]``(括弧の注は捨てる)。"""
    import re

    path, _, rest = str(entry["source"]).partition(" ")
    rest = re.sub(r"[(\uff08][^)\uff09]*[)\uff09]", "", rest)  # notes in ASCII or full-width parentheses are dropped
    return [(path, part.strip()) for part in rest.split("・") if part.strip()]


def symbol_defined(text: str, symbol: str) -> bool:
    """``text``(Python のソース)に ``symbol`` の定義(``def 記号`` か行頭の ``記号:``/``記号 =``)があるか。"""
    import re

    pat = rf"^\s*(?:def\s+{re.escape(symbol)}\b|{re.escape(symbol)}\s*[:=])"
    return re.search(pat, text, flags=re.MULTILINE) is not None


# ---------------------------------------------------------------- 腕
def conditions() -> tuple[str, ...]:
    """不応期表の 11 行の条件名(``WakeCondition`` の値 0..10 の順・``ACTIVITY_EXPIRY`` は表の外=含まない)。"""
    from shibuya.agents.state import N_WAKE_CONDITIONS, WakeCondition

    return tuple(WakeCondition(i).name for i in range(int(N_WAKE_CONDITIONS)))


def arm_names() -> tuple[str, ...]:
    """腕の名の並び(A・B・C1..C11)。"""
    return ("A", "B", *(f"C{k}" for k in range(1, len(conditions()) + 1)))


def arm_condition(arm: str) -> str | None:
    """腕 Ck の条件名(A・B は None)。"""
    if arm.startswith("C"):
        k = int(arm[1:])
        conds = conditions()
        if not 1 <= k <= len(conds):
            raise ValueError(f"未知の腕: {arm!r}")
        return conds[k - 1]
    if arm in ("A", "B"):
        return None
    raise ValueError(f"未知の腕: {arm!r}")


def scale_items(arm: str) -> list[str]:
    """腕の ``COND=FACTOR`` の並び(A は空・B は 11 個・Ck は 1 個)。"""
    if arm == "A":
        return []
    if arm == "B":
        return [f"{c}={FACTOR_TEXT}" for c in conditions()]
    return [f"{arm_condition(arm)}={FACTOR_TEXT}"]


def cli_flags(arm: str) -> list[str]:
    """CLI に渡す旗の並び(``--refractory-scale X=0`` を条件の数だけ)。"""
    out: list[str] = []
    for item in scale_items(arm):
        out += ["--refractory-scale", item]
    return out


def scale_dict(arm: str) -> dict[str, float]:
    """``cli.parse_refractory_scale`` を通した倍率の辞書(CLI と同じ読み口)。"""
    from shibuya import cli

    return cli.parse_refractory_scale(scale_items(arm))


def effective_minutes(arm: str) -> list[int]:
    """腕の実効不応期表[分](``engine.resolve.refractory_ticks``・刻み 60 秒=分)。"""
    from shibuya.engine import resolve as R

    sc = scale_dict(arm)
    return [int(x) for x in R.refractory_ticks(sc or None)]


def plan(configs: Sequence[str] = CONFIGS, seed_main: int = SEED_MAIN,
         extra_seeds: Mapping[str, Sequence[int]] | None = None,
         arms: Sequence[str] | None = None) -> list[tuple[str, str, int]]:
    """回す (構成, 腕, seed) の並び(構成 → seed → 腕の順)。"""
    extra = dict(EXTRA_SEEDS if extra_seeds is None else extra_seeds)
    use_arms = tuple(arm_names() if arms is None else arms)
    out: list[tuple[str, str, int]] = []
    for c in configs:
        for s in (int(seed_main), *(int(x) for x in extra.get(c, ()))):
            for a in use_arms:
                out.append((c, a, s))
    return out


def row_name(config: str, arm: str, seed: int, n_agents: int = N_AGENTS) -> str:
    """行のファイル名(5,000 体は従来の名・ほかは ``__n<体数>`` を付ける)。"""
    tail = "" if int(n_agents) == N_AGENTS else f"__n{int(n_agents)}"
    return f"{config}__{arm}__s{int(seed)}{tail}.json"


# ---------------------------------------------------------------- 構成の表
def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def config_kw(config: str) -> dict[str, Any]:
    """``byte_check_10e`` の表(``wave2_bytecheck.configs()``)の kw をそのまま返す。"""
    bc = _load(BYTE_CHECK_10E, "byte_check_10e_refr20b")
    table = bc._wave2().configs()  # noqa: SLF001 - 10e の道具と同じ読み方
    if config not in table:
        raise KeyError(f"byte_check_10e の表に無い構成: {config!r}")
    return dict(table[config])


# ---------------------------------------------------------------- 1 本
def _sum_col(res: Any, name: str) -> int:
    try:
        return int(res.column(name).sum()) if res.diagnostics.size else 0
    except Exception:  # pragma: no cover - 列が無い版
        return -1


def observation_from_result(res: Any) -> dict[str, Any]:
    """RunResult から manifest に無い観測(診断の列・アービタ・会話)を取る。"""
    arb = {str(k): {str(c): int(n) for c, n in dict(v).items()} for k, v in dict(res.arbiter_counters).items()}
    conv = {str(k): int(v) for k, v in dict(res.conversation_counters or {}).items()}
    l4 = dict(res.l4_audit_fields())
    return {
        "candidates": _sum_col(res, "candidates"),
        "merged": _sum_col(res, "merged"),
        "arbiter": arb,
        "sleep_suppressed": int(res.sleep_suppressed_count),
        "outside_suppressed": int(res.outside_suppressed_count),
        "conversation_sessions": int(res.conversation_sessions),
        "conversations_diag": _sum_col(res, "conversations"),
        "conversation_counters": conv,
        "calls_by_hour": [int(x) for x in res.calls_by_hour],
        "l4": {k: l4[k] for k in ("llm_calls_per_agent_day", "l4_line", "l4_exceeded", "l4_conversation_share")
               if k in l4},
        "action_usage_total": int(sum(int(v) for v in dict(res.action_usage).values())),
        # 活動層(語彙 v3)の「活動中の場所の変化(CELL_BLOCK)の候補を落とす」門の延べ(不応期の表の外の門)
        "activity_counters": {str(k): int(v) for k, v in dict(res.activity_counters or {}).items()},
        "final": str(res.final_hash)[:16],
        "llm_calls": int(res.llm_calls),
        "n_agents": int(res.n_agents),
        "run_wall_s": round(float(getattr(res, "wall_seconds", 0.0) or 0.0), 2),
    }


def row_from_manifest(man: Mapping[str, Any], obs: Mapping[str, Any], *, config: str, arm: str, seed: int,
                      kw: Mapping[str, Any] | None = None, wall_s: float | None = None) -> dict[str, Any]:
    """manifest(``run_manifest_fields``)と観測から 1 行を作る(試験は合成の manifest で呼ぶ)。"""
    cbm = {str(k): int(v) for k, v in dict(man.get("calls_by_model", {}) or {}).items()}
    cbc = {str(k): int(v) for k, v in dict(man.get("calls_by_condition", {}) or {}).items()}
    calls = int(obs.get("llm_calls", sum(cbm.values())))
    arb = dict(obs.get("arbiter", {}) or {})
    sup = arb.get("suppressed", {}) or {}
    daily = [dict(d.get("calls_by_model", {}) or {}) for d in (man.get("daily") or []) if isinstance(d, Mapping)]
    return {
        "schema": SCHEMA_ROW,
        "config": str(config),
        "arm": str(arm),
        "seed": int(seed),
        "n_agents": int(obs.get("n_agents", N_AGENTS)),
        "kw": dict(kw or {}),
        "refractory_flags": cli_flags(arm),
        "refractory_scale": {str(k): float(v) for k, v in dict(man.get("refractory_scale", {}) or {}).items()},
        "policy": str(man.get("policy", "")),
        "run_kind": man.get("run_kind"),
        "final": str(obs.get("final", "")),
        "calls": calls,
        "calls_by_model": cbm,
        "calls_by_model_daily": daily,
        "calls_by_condition": cbc,
        "calls_by_hour": list(obs.get("calls_by_hour", []) or []),
        "candidates": int(obs.get("candidates", -1)),
        "merged": int(obs.get("merged", -1)),
        "arbiter": arb,
        "suppressed": int(sum(int(v) for v in dict(sup).values())),
        "sleep_suppressed": int(obs.get("sleep_suppressed", -1)),
        "outside_suppressed": int(obs.get("outside_suppressed", -1)),
        "conversation_sessions": int(obs.get("conversation_sessions", -1)),
        "conversations_diag": int(obs.get("conversations_diag", -1)),
        "conversation_counters": dict(obs.get("conversation_counters", {}) or {}),
        "l4": dict(obs.get("l4", {}) or {}),
        "action_usage_total": int(obs.get("action_usage_total", -1)),
        "activity_counters": dict(obs.get("activity_counters", {}) or {}),
        "activity_cell_block_suppressed": int(dict(obs.get("activity_counters", {}) or {}).get("cell_block_suppressed", 0)),
        "run_wall_s": obs.get("run_wall_s"),
        "wall_s": None if wall_s is None else round(float(wall_s), 1),
    }


def cmd_one(args: argparse.Namespace) -> int:
    import shibuya
    from shibuya import cli

    kw = config_kw(args.config)
    kw.setdefault("policy", "mock")  # 方策 mock を明示(CLI の既定と同じ値)
    sc = scale_dict(args.arm)
    t0 = time.perf_counter()
    res = cli.run(n_agents=int(args.agents), seed=int(args.seed), world_dir=args.world,
                  refractory_scale=(sc or None), **kw)
    wall = time.perf_counter() - t0
    man = res.run_manifest_fields()
    obs = observation_from_result(res)
    row = row_from_manifest(man, obs, config=args.config, arm=args.arm, seed=int(args.seed),
                            kw=config_kw(args.config), wall_s=wall)
    row["effective_minutes"] = effective_minutes(args.arm)
    src_root = Path(shibuya.__file__).resolve().parents[1]
    row["shibuya_from_given_src"] = (not args.src) or (src_root == Path(args.src).resolve())
    if row["policy"] != "mock":
        raise SystemExit(f"方策が mock でない: {row['policy']!r}")
    if not row["shibuya_from_given_src"]:
        raise SystemExit("shibuya が --src の木から読まれていない(PYTHONPATH を確かめる)")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(row, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: row[k] for k in ("config", "arm", "seed", "final", "calls", "wall_s")}, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- 集計
def _ratio(num: float, den: float) -> float | None:
    return None if not den else round(float(num) / float(den), 4)


def load_rows(rows_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for p in sorted(Path(rows_dir).glob("*.json")):
        rows.append(json.loads(p.read_text(encoding="utf-8")))
    return rows


def _k2_split(row: Mapping[str, Any]) -> dict[str, int]:
    """仮の割り(会話ターン=LLM・それ以外=判断モデル)。"""
    cbc = dict(row.get("calls_by_condition", {}) or {})
    conv = int(cbc.get("CONVERSATION_TURN", 0))
    return {"judge_model": int(row["calls"]) - conv, "llm": conv}


def build_table(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """行の集まり → 表(構成 × seed ごとの A・B・倍率・C1..C11 の増分と順位)。入力の並びに依らない。"""
    conds = conditions()
    groups: dict[tuple[str, int, int], dict[str, Mapping[str, Any]]] = {}
    for r in rows:
        key = (str(r["config"]), int(r["seed"]), int(r.get("n_agents", N_AGENTS)))
        groups.setdefault(key, {})[str(r["arm"])] = r
    out_groups: list[dict[str, Any]] = []
    for (config, seed, n) in sorted(groups, key=lambda t: (ALL_CONFIGS.index(t[0]) if t[0] in ALL_CONFIGS else 99,
                                                         t[0], t[2], t[1])):
        g = groups[(config, seed, n)]
        a = g.get("A")
        b = g.get("B")
        ent: dict[str, Any] = {"config": config, "seed": seed, "n_agents": n}
        if a is not None:
            ent["A"] = _arm_brief(a)
        if b is not None:
            ent["B"] = _arm_brief(b)
        if a is not None and b is not None:
            ent["ratio_B"] = _ratio(b["calls"], a["calls"])  # 表示用(4 桁)
            ent["ratio_B_exact"] = (float(b["calls"]) / float(a["calls"])) if a["calls"] else None  # 外挿用
            ent["delta_B"] = int(b["calls"]) - int(a["calls"])
            ent["by_condition_delta_B"] = {
                k: int(b["calls_by_condition"].get(k, 0)) - int(a["calls_by_condition"].get(k, 0))
                for k in (*conds, "ACTIVITY_EXPIRY")
            }
        cs: list[dict[str, Any]] = []
        if a is not None:
            for k, cname in enumerate(conds, start=1):
                rc = g.get(f"C{k}")
                if rc is None:
                    continue
                cs.append({
                    "arm": f"C{k}", "condition": cname, "index": k - 1,
                    "calls": int(rc["calls"]), "delta": int(rc["calls"]) - int(a["calls"]),
                    "ratio": _ratio(rc["calls"], a["calls"]),
                    "same_final_as_A": str(rc.get("final", "")) == str(a.get("final", "")),
                    "calls_of_condition_A": int(a["calls_by_condition"].get(cname, 0)),
                    "calls_of_condition_C": int(rc["calls_by_condition"].get(cname, 0)),
                    "suppressed": int(rc.get("suppressed", -1)),
                })
            order = sorted(cs, key=lambda e: (-e["delta"], e["index"]))
            for rank, e in enumerate(order, start=1):
                e["rank"] = rank
            ent["C"] = order
            if cs:
                ent["sum_C_delta"] = int(sum(e["delta"] for e in cs))
                if "delta_B" in ent and len(cs) == len(conds):
                    ent["interaction"] = int(ent["delta_B"]) - int(ent["sum_C_delta"])
        out_groups.append(ent)
    main_groups = [g for g in out_groups if int(g["n_agents"]) == N_AGENTS]
    return {"schema": SCHEMA_TABLE, "conditions": list(conds), "groups": out_groups, "seed_spread": _spread(main_groups),
            "activity_gate": _activity_gate(main_groups), "scale_check": _scale_check(out_groups)}


def _find(groups: Sequence[Mapping[str, Any]], config: str, seed: int, n: int) -> Mapping[str, Any] | None:
    for g in groups:
        if str(g["config"]) == config and int(g["seed"]) == int(seed) and int(g["n_agents"]) == int(n):
            return g
    return None


def _activity_gate(groups: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """活動層を層ごと off にした量(活動層 on/off・seed 1・5,000 体): 倍率 B/A と場所の変化の増分を並べる。

    層ごと off は門・満了の起床・活動の設定・あたり歩行などを一緒に外す(門だけの重みではない)。
    """
    on_name, off_name = ACTIVITY_GATE_PAIR
    on = _find(groups, on_name, SEED_MAIN, N_AGENTS)
    off = _find(groups, off_name, SEED_MAIN, N_AGENTS)
    if on is None or off is None or on.get("ratio_B") is None or off.get("ratio_B") is None:
        return None

    def side(g: Mapping[str, Any]) -> dict[str, Any]:
        a, b = g["A"], g["B"]
        return {
            "config": str(g["config"]),
            "calls_A": int(a["calls"]), "calls_B": int(b["calls"]),
            "ratio_B": g["ratio_B"],
            "cell_block_A": int(a["calls_by_condition"].get("CELL_BLOCK", 0)),
            "cell_block_B": int(b["calls_by_condition"].get("CELL_BLOCK", 0)),
            "cell_block_delta_B": int(b["calls_by_condition"].get("CELL_BLOCK", 0))
            - int(a["calls_by_condition"].get("CELL_BLOCK", 0)),
            "cell_block_share_of_delta_B": (round((int(b["calls_by_condition"].get("CELL_BLOCK", 0))
                                                   - int(a["calls_by_condition"].get("CELL_BLOCK", 0)))
                                                  / float(g["delta_B"]), 4) if g.get("delta_B") else None),
            "activity_gate_suppressed_A": int(a.get("activity_cell_block_suppressed", 0)),
            "activity_gate_suppressed_B": int(b.get("activity_cell_block_suppressed", 0)),
        }

    s_on, s_off = side(on), side(off)
    return {
        "seed": SEED_MAIN, "n_agents": N_AGENTS, "on": s_on, "off": s_off,
        "ratio_B_diff_off_minus_on": round(float(off["ratio_B_exact"]) - float(on["ratio_B_exact"]), 4),
        "ratio_B_ratio_off_over_on": round(float(off["ratio_B_exact"]) / float(on["ratio_B_exact"]), 4),
        "cell_block_delta_B_diff_off_minus_on": int(s_off["cell_block_delta_B"]) - int(s_on["cell_block_delta_B"]),
        "calls_A_diff_on_minus_off_by_condition": {
            k: int(on["A"]["calls_by_condition"].get(k, 0)) - int(off["A"]["calls_by_condition"].get(k, 0))
            for k in sorted(set(on["A"]["calls_by_condition"]) | set(off["A"]["calls_by_condition"]))
            if int(on["A"]["calls_by_condition"].get(k, 0)) != int(off["A"]["calls_by_condition"].get(k, 0))
        },
        "note": ("層ごと off(門・活動の満了の起床・活動の設定・あたり歩行などを一緒に外す)。腕 A も変わる。"
                 "門だけを外す口は src に無い=門だけの重みは測っていない"),
    }


def _scale_check(groups: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """体数を変えた A・B: 体あたりの倍率 B/A と呼/体/日を 5,000 体と並べる。"""
    out: list[dict[str, Any]] = []
    for g in groups:
        n = int(g["n_agents"])
        if n == N_AGENTS or g.get("ratio_B") is None:
            continue
        base = _find(groups, str(g["config"]), int(g["seed"]), N_AGENTS)
        if base is None or base.get("ratio_B") is None:
            continue
        rb, rn = float(base["ratio_B_exact"]), float(g["ratio_B_exact"])
        out.append({
            "config": str(g["config"]), "seed": int(g["seed"]), "n_base": N_AGENTS, "n": n,
            "ratio_B_base": base["ratio_B"], "ratio_B": g["ratio_B"],
            "ratio_B_diff": round(rn - rb, 4), "ratio_B_rel_diff": round(rn / rb - 1.0, 4),
            "per_agent_day_A_base": base["A"]["per_agent_day"], "per_agent_day_A": g["A"]["per_agent_day"],
            "per_agent_day_B_base": base["B"]["per_agent_day"], "per_agent_day_B": g["B"]["per_agent_day"],
            "per_agent_delta_B_by_condition_base": {k: round(v / float(N_AGENTS), 4)
                                                    for k, v in base["by_condition_delta_B"].items() if v},
            "per_agent_delta_B_by_condition": {k: round(v / float(n), 4)
                                               for k, v in g["by_condition_delta_B"].items() if v},
            "wall_s_A": g["A"].get("wall_s"), "wall_s_B": g["B"].get("wall_s"),
        })
    return out


def _arm_brief(r: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "calls": int(r["calls"]),
        "per_agent_day": round(int(r["calls"]) / max(1, int(r.get("n_agents", N_AGENTS))), 4),
        "calls_by_model": dict(r.get("calls_by_model", {}) or {}),
        "split_k2": _k2_split(r),
        "calls_by_condition": dict(r.get("calls_by_condition", {}) or {}),
        "suppressed": int(r.get("suppressed", -1)),
        "sleep_suppressed": int(r.get("sleep_suppressed", -1)),
        "outside_suppressed": int(r.get("outside_suppressed", -1)),
        "activity_cell_block_suppressed": int(r.get("activity_cell_block_suppressed", 0)),
        "candidates": int(r.get("candidates", -1)),
        "merged": int(r.get("merged", -1)),
        "conversation_sessions": int(r.get("conversation_sessions", -1)),
        "conversations_diag": int(r.get("conversations_diag", -1)),
        "final": str(r.get("final", "")),
        "wall_s": r.get("wall_s"),
    }


def _spread(groups: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """seed が 2 本以上ある構成の倍率の幅と上位 3 の並び。"""
    by_cfg: dict[str, list[Mapping[str, Any]]] = {}
    for g in groups:
        by_cfg.setdefault(str(g["config"]), []).append(g)
    out: dict[str, Any] = {}
    for cfg, gs in by_cfg.items():
        if len(gs) < 2:
            continue
        ratios = [g["ratio_B"] for g in gs if g.get("ratio_B") is not None]
        exact = [g["ratio_B_exact"] for g in gs if g.get("ratio_B_exact") is not None]
        out[cfg] = {
            "seeds": [int(g["seed"]) for g in gs],
            "ratio_B": ratios,
            "ratio_B_min": min(ratios) if ratios else None,
            "ratio_B_max": max(ratios) if ratios else None,
            "ratio_B_mean": round(sum(ratios) / len(ratios), 4) if ratios else None,
            "ratio_B_exact_min": min(exact) if exact else None,
            "ratio_B_exact_max": max(exact) if exact else None,
            "top3_by_seed": {str(g["seed"]): [e["condition"] for e in (g.get("C") or [])[:3]] for g in gs},
        }
    return out


# ---------------------------------------------------------------- 外挿
def ten_e_reference() -> dict[str, Any]:
    """10e の記録(5,000 体の既定の呼数=ret.json・39 万体の体数=budget_10e.json)。"""
    ret = json.loads(TEN_E_RET.read_text(encoding="utf-8"))
    bud = json.loads(TEN_E_BUDGET.read_text(encoding="utf-8"))
    return {
        "source_calls": TEN_E_RET_REL,
        "source_n_full": TEN_E_BUDGET_REL,
        "n_sample": int(ret.get("agents", N_AGENTS)),
        "seed": int(ret.get("seed", 1)),
        "n_full": int(bud["n_full"]),
        "calls_5000": {c: int(ret["runs"][c]["calls"]) for c in ALL_CONFIGS if c in ret.get("runs", {})},
        "final_5000": {c: str(ret["runs"][c]["final"]) for c in ALL_CONFIGS if c in ret.get("runs", {})},
    }


def extrapolate(ratio_B: float, base_calls_sample: int, *, n_full: int, n_sample: int = N_AGENTS,
                days: int = DAYS_WEEK, conv_share_B: float | None = None) -> dict[str, Any]:
    """39 万体への比例の外挿(体数に線形=**推測**)。"""
    base_full = float(base_calls_sample) * float(n_full) / float(n_sample)
    b_day = base_full * float(ratio_B)
    out: dict[str, Any] = {
        "base_calls_sample": int(base_calls_sample),
        "n_sample": int(n_sample),
        "n_full": int(n_full),
        "base_full_per_day": int(round(base_full)),
        "ratio_B": round(float(ratio_B), 6),
        "B_full_per_day": int(round(b_day)),
        "B_full_per_week": int(round(b_day * days)),
        "days": int(days),
        "per_agent_day_A": round(float(base_calls_sample) / float(n_sample), 4),
        "per_agent_day_B": round(float(base_calls_sample) * float(ratio_B) / float(n_sample), 4),
    }
    if conv_share_B is not None:
        llm = b_day * float(conv_share_B)
        out["split_k2_per_day"] = {"judge_model": int(round(b_day - llm)), "llm": int(round(llm))}
        out["conv_share_B"] = round(float(conv_share_B), 6)
    return out


def build_extrapolation(table: Mapping[str, Any], ref: Mapping[str, Any]) -> dict[str, Any]:
    from shibuya.engine.arbiter import L4_CALLS_PER_DAY, L4_REFERENCE_AGENTS

    out: dict[str, Any] = {"reference": dict(ref), "l4_calls_per_day": int(L4_CALLS_PER_DAY),
                           "l4_reference_agents": int(L4_REFERENCE_AGENTS), "by_config": {}}
    for g in table["groups"]:
        if int(g["seed"]) != SEED_MAIN or int(g["n_agents"]) != N_AGENTS or g.get("ratio_B") is None:
            continue
        cfg = str(g["config"])
        base = ref["calls_5000"].get(cfg)
        if base is None:
            continue
        b = g["B"]
        conv = int(b["calls_by_condition"].get("CONVERSATION_TURN", 0))
        e = extrapolate(float(g["ratio_B_exact"]), int(base), n_full=int(ref["n_full"]), n_sample=int(ref["n_sample"]),
                        conv_share_B=(conv / b["calls"] if b["calls"] else 0.0))
        e["A_matches_10e"] = int(g["A"]["calls"]) == int(base)
        e["A_final_matches_10e"] = str(g["A"]["final"]) == str(ref["final_5000"].get(cfg, ""))
        e["B_full_per_day_over_l4"] = round(e["B_full_per_day"] / float(L4_CALLS_PER_DAY), 3)
        spread = table.get("seed_spread", {}).get(cfg)
        if spread and spread.get("ratio_B_exact_min") is not None:
            e["B_full_per_day_seed_range"] = [
                int(round(float(base) * float(ref["n_full"]) / float(ref["n_sample"]) * spread["ratio_B_exact_min"])),
                int(round(float(base) * float(ref["n_full"]) / float(ref["n_sample"]) * spread["ratio_B_exact_max"])),
            ]
        out["by_config"][cfg] = e
    return out


# ---------------------------------------------------------------- Markdown
def _fmt(n: Any) -> str:
    if n is None:
        return "—"
    if isinstance(n, float):
        return f"{n:,.4f}".rstrip("0").rstrip(".") if abs(n) < 1000 else f"{n:,.0f}"
    if isinstance(n, int):
        return f"{n:,}"
    return str(n)


def render_md(doc: Mapping[str, Any]) -> str:
    t = doc["table"]
    lines: list[str] = []
    lines.append("# 2-0b 不応期を外した腕の呼数(道具の出力・手で書かない)")
    lines.append("")
    lines.append(f"- 道具: `{TOOL_REL}`・5,000 体・1 シミュ日・方策 mock・腕 B は `--refractory-scale COND={FACTOR_TEXT}` × 11")
    lines.append(f"- src: commit `{doc['provenance'].get('src_commit', '')}`・src の差 {doc['provenance'].get('src_dirty_files', '?')} 本")
    lines.append("")
    lines.append("## 腕 A(既定)と腕 B(11 種とも 0)")
    lines.append("")
    lines.append("| 構成 | 体数 | seed | A 呼数 | B 呼数 | 倍率 B/A | A 呼/体/日 | B 呼/体/日 | 抑止(不応期)A → B | 就寝抑止 A → B | 活動層の場所起床の抑止 A → B | 会話セッション A → B | final A / B | 壁時計 A / B [秒] |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for g in t["groups"]:
        a, b = g.get("A"), g.get("B")
        if a is None or b is None:
            continue
        lines.append(
            f"| {g['config']} | {_fmt(g['n_agents'])} | {g['seed']} | {_fmt(a['calls'])} | {_fmt(b['calls'])} | **{_fmt(g['ratio_B'])}** | "
            f"{_fmt(a['per_agent_day'])} | {_fmt(b['per_agent_day'])} | {_fmt(a['suppressed'])} → {_fmt(b['suppressed'])} | "
            f"{_fmt(a['sleep_suppressed'])} → {_fmt(b['sleep_suppressed'])} | "
            f"{_fmt(a['activity_cell_block_suppressed'])} → {_fmt(b['activity_cell_block_suppressed'])} | "
            f"{_fmt(a['conversation_sessions'])} → {_fmt(b['conversation_sessions'])} | "
            f"`{a['final']}` / `{b['final']}` | {_fmt(a['wall_s'])} / {_fmt(b['wall_s'])} |"
        )
    lines.append("")
    lines.append("`calls_by_model`(manifest の欄)は今の版では判断モデル 0・LLM=全呼。仮の割り(会話ターン=LLM・それ以外=判断モデル):")
    lines.append("")
    lines.append("| 構成 | 体数 | seed | A 判断モデル / LLM(仮の割り) | B 判断モデル / LLM(仮の割り) | A の manifest | B の manifest |")
    lines.append("|---|---|---|---|---|---|---|")
    for g in t["groups"]:
        a, b = g.get("A"), g.get("B")
        if a is None or b is None:
            continue
        lines.append(
            f"| {g['config']} | {_fmt(g['n_agents'])} | {g['seed']} | {_fmt(a['split_k2']['judge_model'])} / {_fmt(a['split_k2']['llm'])} | "
            f"{_fmt(b['split_k2']['judge_model'])} / {_fmt(b['split_k2']['llm'])} | "
            f"{_fmt(a['calls_by_model'].get('judge_model'))} / {_fmt(a['calls_by_model'].get('llm'))} | "
            f"{_fmt(b['calls_by_model'].get('judge_model'))} / {_fmt(b['calls_by_model'].get('llm'))} |"
        )
    lines.append("")
    lines.append("## 起床条件ごとの発射数(A → B・アービタが合流した後の代表の条件)")
    lines.append("")
    conds = [*t["conditions"], "ACTIVITY_EXPIRY"]
    lines.append("| 構成 | 体数 | seed | " + " | ".join(conds) + " |")
    lines.append("|---|---|---|" + "---|" * len(conds))
    for g in t["groups"]:
        a, b = g.get("A"), g.get("B")
        if a is None or b is None:
            continue
        cells = [f"{_fmt(a['calls_by_condition'].get(c, 0))} → {_fmt(b['calls_by_condition'].get(c, 0))}" for c in conds]
        lines.append(f"| {g['config']} | {_fmt(g['n_agents'])} | {g['seed']} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## C1〜C11(1 種ずつ 0)の増分の順位(増分=Ck − A・同点は条件の番号順)")
    lines.append("")
    for g in t["groups"]:
        if not g.get("C"):
            continue
        lines.append(f"### {g['config']}・seed {g['seed']}(A {_fmt(g['A']['calls'])} 呼)")
        lines.append("")
        lines.append("| 順位 | 腕 | 条件 | 呼数 | 増分 | 倍率 | その条件の発射 A → C | final が A と同じ |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for e in g["C"]:
            lines.append(
                f"| {e['rank']} | {e['arm']} | {e['condition']} | {_fmt(e['calls'])} | {_fmt(e['delta'])} | {_fmt(e['ratio'])} | "
                f"{_fmt(e['calls_of_condition_A'])} → {_fmt(e['calls_of_condition_C'])} | {'はい' if e['same_final_as_A'] else 'いいえ'} |"
            )
        if "interaction" in g:
            lines.append("")
            lines.append(f"増分の和 Σ(Ck − A) = {_fmt(g['sum_C_delta'])}・B − A = {_fmt(g['delta_B'])}・差(足し算で表せない分)= {_fmt(g['interaction'])}")
        lines.append("")
    sp = t.get("seed_spread", {})
    if sp:
        lines.append("## seed のばらつき")
        lines.append("")
        for cfg, s in sp.items():
            lines.append(f"- {cfg}: seed {s['seeds']} の倍率 {s['ratio_B']}(最小 {_fmt(s['ratio_B_min'])}・最大 {_fmt(s['ratio_B_max'])}・平均 {_fmt(s['ratio_B_mean'])})。上位 3: "
                         + "・".join(f"seed {k}={'/'.join(v)}" for k, v in s["top3_by_seed"].items()))
        lines.append("")
    ag = t.get("activity_gate")
    if ag:
        lines.append(f"## 活動層を層ごと off にした量(活動層 on / off・seed {ag['seed']}・{ag['n_agents']:,} 体)")
        lines.append("")
        lines.append(f"- 層ごと off は、門(活動中の場所の変化の候補の落とし)だけでなく、活動の満了の起床・活動の設定・あたり歩行"
                     f"なども一緒に外す。腕 A も {_fmt(ag['on']['calls_A'])} → {_fmt(ag['off']['calls_A'])} に変わる。"
                     "門だけを外す口は src に無いので、門だけの重みは測っていない。")
        lines.append("")
        lines.append("| 構成 | A 呼数 | B 呼数 | 倍率 B/A | 場所の変化の発射 A → B | 場所の変化の増分 | B − A に占める割合 | 活動層の場所起床の抑止 A → B |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for side in (ag["on"], ag["off"]):
            lines.append(
                f"| {side['config']} | {_fmt(side['calls_A'])} | {_fmt(side['calls_B'])} | **{_fmt(side['ratio_B'])}** | "
                f"{_fmt(side['cell_block_A'])} → {_fmt(side['cell_block_B'])} | {_fmt(side['cell_block_delta_B'])} | "
                f"{_fmt(side['cell_block_share_of_delta_B'])} | {_fmt(side['activity_gate_suppressed_A'])} → "
                f"{_fmt(side['activity_gate_suppressed_B'])} |"
            )
        lines.append("")
        lines.append(f"倍率の差(off − on)= +{_fmt(ag['ratio_B_diff_off_minus_on'])}(比なら {_fmt(ag['ratio_B_ratio_off_over_on'])} 倍)・"
                     f"場所の変化の増分の差(off − on)= {_fmt(ag['cell_block_delta_B_diff_off_minus_on'])}")
        lines.append("")
        lines.append("腕 A の差(on − off・起床条件ごと): " + "・".join(
            f"{k} {'+' if v > 0 else ''}{_fmt(v)}" for k, v in ag["calls_A_diff_on_minus_off_by_condition"].items()))
        lines.append("")
    sc = t.get("scale_check") or []
    if sc:
        lines.append("## 体数の確かめ(体あたりの倍率)")
        lines.append("")
        lines.append("| 構成 | seed | 体数 | 倍率 B/A | 5,000 体の倍率 | 差 | 相対の差 | 呼/体/日 A(5,000 体 → この体数) | 呼/体/日 B(5,000 体 → この体数) | 壁時計 A / B [秒] |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for e in sc:
            lines.append(
                f"| {e['config']} | {e['seed']} | {_fmt(e['n'])} | **{_fmt(e['ratio_B'])}** | {_fmt(e['ratio_B_base'])} | "
                f"{_fmt(e['ratio_B_diff'])} | {_fmt(e['ratio_B_rel_diff'])} | {_fmt(e['per_agent_day_A_base'])} → "
                f"{_fmt(e['per_agent_day_A'])} | {_fmt(e['per_agent_day_B_base'])} → {_fmt(e['per_agent_day_B'])} | "
                f"{_fmt(e['wall_s_A'])} / {_fmt(e['wall_s_B'])} |"
            )
        lines.append("")
        lines.append("B − A の体あたりの増え(条件ごと・5,000 体 → この体数):")
        lines.append("")
        for e in sc:
            keys = sorted(set(e["per_agent_delta_B_by_condition_base"]) | set(e["per_agent_delta_B_by_condition"]))
            lines.append(f"- {e['config']}・{e['n']:,} 体: " + "・".join(
                f"{k} {_fmt(e['per_agent_delta_B_by_condition_base'].get(k, 0.0))} → "
                f"{_fmt(e['per_agent_delta_B_by_condition'].get(k, 0.0))}" for k in keys))
        lines.append("")
    ex = doc.get("extrapolation", {})
    if ex.get("by_config"):
        ref = ex["reference"]
        lines.append("## 39 万体への外挿(体数に比例=推測・T3 の驚き駆動では「何かあった人だけ」になるので上限の見積り)")
        lines.append("")
        lines.append(f"- 出典: 5,000 体の既定の呼数=`{ref['source_calls']}`(seed {ref['seed']})・39 万体の体数 {ref['n_full']:,}=`{ref['source_n_full']}` の `n_full`")
        lines.append(f"- 式: 39 万体の既定の呼数/日 = 10e の 5,000 体の呼数 × {ref['n_full']:,} / {ref['n_sample']:,}・腕 B = それ × 倍率 B/A(seed {SEED_MAIN})・7 日 = 1 日 × 7")
        lines.append(f"- 予算宣言表 L4 の線: {ex['l4_calls_per_day']:,} 呼/日({ex['l4_reference_agents']:,} 体基準)")
        lines.append("- 不応期の表の外の門(下の一覧)は腕 B でも残る。T3 の設計でそれらも外すと決めれば、上限はここより上がる。")
        lines.append("")
        lines.append("| 構成 | 10e の 5,000 体 | 39 万体 既定/日 | 倍率 | 39 万体 腕 B/日 | 腕 B/7 日 | 腕 B の判断モデル/日(仮の割り) | 腕 B の LLM/日(仮の割り) | L4 の何倍 | seed 1〜3 の幅/日 | A が 10e と同じ |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for cfg, e in ex["by_config"].items():
            sk = e.get("split_k2_per_day", {})
            rng = e.get("B_full_per_day_seed_range")
            lines.append(
                f"| {cfg} | {_fmt(e['base_calls_sample'])} | {_fmt(e['base_full_per_day'])} | {_fmt(e['ratio_B'])} | "
                f"**{_fmt(e['B_full_per_day'])}** | {_fmt(e['B_full_per_week'])} | {_fmt(sk.get('judge_model'))} | {_fmt(sk.get('llm'))} | "
                f"{_fmt(e['B_full_per_day_over_l4'])} | {('〜'.join(_fmt(x) for x in rng)) if rng else '—'} | "
                f"{'はい' if e['A_matches_10e'] and e['A_final_matches_10e'] else 'いいえ'} |"
            )
        lines.append("")
    gates = doc.get("gates_outside_table") or []
    if gates:
        lines.append("## 不応期の表の外の門(腕 B でも残る・名と出典=ファイル+記号)")
        lines.append("")
        lines.append("主なものの一覧で、網羅ではない(例: 9a の歩行退出・L4 の繰り延べは既定では効かないので載せていない)。")
        lines.append("")
        for gt in gates:
            lines.append(f"- {gt['name']}: `{gt['source']}`")
        lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- 由来
def provenance(src: Path | None) -> dict[str, Any]:
    out: dict[str, Any] = {"tool": TOOL_REL, "python": platform.python_version()}
    try:
        import numpy as np

        out["numpy"] = np.__version__
    except Exception:  # pragma: no cover
        pass
    root = REPO
    try:
        out["src_commit"] = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                                           capture_output=True, text=True, check=True).stdout.strip()
        st = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "src"],
                            capture_output=True, text=True, check=True).stdout
        out["src_dirty_files"] = len([ln for ln in st.splitlines() if ln.strip()])
    except Exception:  # pragma: no cover - git の無い写し
        out["src_commit"] = ""
        out["src_dirty_files"] = None
    out["src_is_repo_src"] = (src is None) or (Path(src).resolve() == (REPO / "src").resolve())
    return out


def write_outputs(rows: Sequence[Mapping[str, Any]], out_dir: Path, *, src: Path | None = None,
                  extra: Mapping[str, Any] | None = None) -> dict[str, Any]:
    table = build_table(rows)
    ref = ten_e_reference()
    doc = {
        "schema": SCHEMA_TABLE,
        "provenance": provenance(src),
        "settings": {"configs": list(CONFIGS), "extra_configs_AB_seed1": list(EXTRA_CONFIGS), "seed_main": SEED_MAIN,
                     "extra_seeds": {k: list(v) for k, v in EXTRA_SEEDS.items()},
                     "arms": list(arm_names()), "factor": FACTOR_TEXT, "n_agents": N_AGENTS, "policy": "mock",
                     "flags_B": cli_flags("B")},
        "table": table,
        "extrapolation": build_extrapolation(table, ref),
        "gates_outside_table": [dict(g) for g in GATES_OUTSIDE_TABLE],
        "rows": sorted((dict(r) for r in rows), key=lambda r: (str(r["config"]), int(r.get("n_agents", N_AGENTS)),
                                                              int(r["seed"]), _arm_key(str(r["arm"])))),
    }
    if extra:
        doc["run"] = dict(extra)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "refractory_calls.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                                                   encoding="utf-8", newline="\n")
    (out_dir / "refractory_calls.md").write_text(render_md(doc), encoding="utf-8", newline="\n")
    return doc


def _arm_key(arm: str) -> tuple[int, int]:
    if arm == "A":
        return (0, 0)
    if arm == "B":
        return (1, 0)
    return (2, int(arm[1:]))


def cmd_table(args: argparse.Namespace) -> int:
    rows = load_rows(Path(args.rows_dir))
    prev = Path(args.out_dir) / "refractory_calls.json"
    log = Path(args.rows_dir).parent / RUN_LOG
    extra = None
    if log.exists():  # ``run`` の回し方の控え(呼び出しごと)
        extra = {"invocations": json.loads(log.read_text(encoding="utf-8"))}
    elif prev.exists():  # ``run`` が書いた回し方の欄(並列の数・総壁時計)は集計し直しても残す
        try:
            extra = json.loads(prev.read_text(encoding="utf-8")).get("run")
        except (ValueError, OSError):
            extra = None
    doc = write_outputs(rows, Path(args.out_dir), src=(Path(args.src) if args.src else None), extra=extra)
    for g in doc["table"]["groups"]:
        top = [e["condition"] for e in (g.get("C") or [])[:3]]
        print(g["config"], g["n_agents"], g["seed"], g.get("A", {}).get("calls"), g.get("B", {}).get("calls"),
              g.get("ratio_B"), top)
    return 0


#: ``run`` の呼び出しごとの控え(作業場所に置く・``table`` が ``run`` の欄に写す)。
RUN_LOG = "run_log.json"


def cmd_run(args: argparse.Namespace) -> int:
    scratch = Path(args.scratch)
    rows_dir = scratch / "rows"
    logs_dir = scratch / "logs"
    rows_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    configs = [s for s in args.configs.split(",") if s] if args.configs else list(CONFIGS)
    arms = [s for s in args.arms.split(",") if s] if args.arms else None
    todo = plan(configs=configs, arms=arms, extra_seeds=(EXTRA_SEEDS if not args.no_extra_seeds else {}))
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONHASHSEED"] = "0"
    src = Path(args.src).resolve() if args.src else (REPO / "src").resolve()
    env["PYTHONPATH"] = os.pathsep.join([str(src), *[p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p]])

    def one(item: tuple[str, str, int]) -> tuple[tuple[str, str, int], str]:
        cfg, arm, seed = item
        out = rows_dir / row_name(cfg, arm, seed, int(args.agents))
        if out.exists():
            return item, "在る"
        cmd = [sys.executable, str(Path(__file__).resolve()), "one", "--config", cfg, "--arm", arm, "--seed", str(seed),
               "--agents", str(args.agents), "--world", args.world, "--src", str(src), "--out", str(out)]
        t0 = time.perf_counter()
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        (logs_dir / (row_name(cfg, arm, seed, int(args.agents))[:-5] + ".log")).write_text(
            (r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or ""), encoding="utf-8", newline="\n")
        if r.returncode != 0:
            return item, f"失敗 rc={r.returncode} {(r.stderr or '')[-400:]}"
        return item, f"済 {time.perf_counter() - t0:.0f}s {(r.stdout or '').strip().splitlines()[-1] if r.stdout else ''}"

    t_all = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for item, msg in ex.map(one, todo):
            print(*item, msg, flush=True)
    rows = load_rows(rows_dir)
    inv = {"configs": configs, "arms": arms or "全部", "extra_seeds": not args.no_extra_seeds, "agents": int(args.agents),
           "jobs": int(args.jobs), "scratch_name": scratch.name, "total_wall_s": round(time.perf_counter() - t_all, 1),
           "n_planned": len(todo)}
    log_path = scratch / RUN_LOG
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []
    log.append(inv)
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    extra = {"invocations": log, "n_rows": len(rows), "total_wall_s": inv["total_wall_s"]}
    if args.out_dir:
        write_outputs(rows, Path(args.out_dir), src=src, extra={"invocations": log})
    print(f"{len(rows)} 行・{extra['total_wall_s']} 秒")
    return 0


#: 2 回のランで同じであるべき欄(壁時計は除く)。
SAME_KEYS: tuple[str, ...] = ("final", "calls", "calls_by_condition", "calls_by_hour", "suppressed", "sleep_suppressed",
                              "outside_suppressed", "candidates", "merged", "conversation_sessions", "arbiter",
                              # 検収 L5: 活動層・会話の計数・calls_by_model・L4 の監査欄も比べる
                              "activity_counters", "conversation_counters", "calls_by_model", "l4")


def compare_rows(rows_a: Sequence[Mapping[str, Any]], rows_b: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """同じ (構成, 腕, seed) の 2 回のランを欄ごとに比べる(決定論の確かめ)。"""
    def key(r: Mapping[str, Any]) -> tuple[str, str, int, int]:
        return (str(r["config"]), str(r["arm"]), int(r["seed"]), int(r.get("n_agents", N_AGENTS)))

    ka = {key(r): r for r in rows_a}
    kb = {key(r): r for r in rows_b}
    common = sorted(set(ka) & set(kb))
    diff = {f"{c}/{a}/s{s}" + ("" if n == N_AGENTS else f"/n{n}"): [k for k in SAME_KEYS if ka[(c, a, s, n)].get(k) != kb[(c, a, s, n)].get(k)]
            for (c, a, s, n) in common}
    diff = {k: v for k, v in diff.items() if v}
    return {"n_common": len(common), "n_same": len(common) - len(diff), "keys": list(SAME_KEYS), "differ": diff,
            "only_a": len(set(ka) - set(kb)), "only_b": len(set(kb) - set(ka))}


def cmd_same(args: argparse.Namespace) -> int:
    doc = compare_rows(load_rows(Path(args.a)), load_rows(Path(args.b)))
    doc["a"], doc["b"] = Path(args.a).name, Path(args.b).name
    if args.out:
        Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{doc['n_same']} / {doc['n_common']} 行が同じ", doc["differ"] or "")
    return 0


def cmd_arms(args: argparse.Namespace) -> int:
    doc = {a: {"condition": arm_condition(a), "flags": cli_flags(a), "scale": scale_dict(a),
               "effective_minutes": effective_minutes(a)} for a in arm_names()}
    print(json.dumps(doc, ensure_ascii=False, indent=1))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("arms")
    sp = sub.add_parser("one")
    sp.add_argument("--config", required=True, choices=ALL_CONFIGS)
    sp.add_argument("--arm", required=True)
    sp.add_argument("--seed", type=int, default=SEED_MAIN)
    sp.add_argument("--agents", type=int, default=N_AGENTS)
    sp.add_argument("--world", default="data/world/v2")
    sp.add_argument("--src", default="")
    sp.add_argument("--out", required=True)
    sp = sub.add_parser("run")
    sp.add_argument("--src", default="")
    sp.add_argument("--scratch", required=True)
    sp.add_argument("--out-dir", default="")
    sp.add_argument("--configs", default="")
    sp.add_argument("--arms", default="")
    sp.add_argument("--no-extra-seeds", action="store_true")
    sp.add_argument("--agents", type=int, default=N_AGENTS)
    sp.add_argument("--world", default="data/world/v2")
    sp.add_argument("--jobs", type=int, default=3)
    sp = sub.add_parser("table")
    sp.add_argument("--rows-dir", required=True)
    sp.add_argument("--out-dir", required=True)
    sp.add_argument("--src", default="")
    sp = sub.add_parser("same")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--out", default="")
    args = ap.parse_args(argv)
    if args.cmd == "one" and args.arm not in arm_names():
        ap.error(f"未知の腕: {args.arm!r}(A・B・C1..C11)")
    return {"arms": cmd_arms, "one": cmd_one, "run": cmd_run, "table": cmd_table, "same": cmd_same}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
