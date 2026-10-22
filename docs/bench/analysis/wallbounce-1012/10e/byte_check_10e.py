"""10e(版上げ 1 回目)の byte-check と「動いた量」の控え。

比べ方は [byte_check_10c.py](../../wallbounce-1003/10c/byte_check_10c.py) と同じ 19 構成(W6 の 15 腕+店の記憶・関係・
古典・古典+記憶+関係。mock/classical 5,000 体・seed 1・1 シミュ日・テープつき)。``one`` は 10c の欄に加えて
行動の件数(``action_usage``)・起床の内訳・最後の checkpoint の behavior-hash と full-hash(全桁)・締めの後の 2 本・
checkpoint の時間・暦の欄・テープの列の名前を出す。``--kw`` で構成の引数に足す(旧値の再現の切替口を渡す口。
HEAD の写しには HEAD に無い引数を渡さない)。

使い方(リポの根で・``$D`` = この置き場・``$W`` = 作業用の**短い**ディレクトリ):

    git archive <HEAD> src docs/bench/anchors/hunger_energy_build_anchors_v0.json \\
        docs/bench/anchors/hunger_energy_validation_anchors_v0.json docs/bench/anchors/ssb2021_activity_prior_v0.json \\
        docs/design/v2-budget-declaration.md docs/design/rules-table.json docs/design/bridging-ledger.json \\
        docs/design/v2-perception-contract.md docs/design/v2-pattern-ledger.md \\
        docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
    # 〔第 2 期 2-3c 検収 L4〕写しの木がリポの根から読む追跡ファイル(:data:`HEAD_TREE_FILES`)と data を全部そろえる。
    # 決め方: src を ``RELPATH``・``parents[3]``・``parents[4]``・``resolve_repo_path`` で grep する(2-3c の時点=
    # rules/table.py の rules-table.json・bridging/ledger.py の bridging-ledger.json・core/budget.py の予算の md・
    # world/processes/constitution.py の 2 本・energy.py と classical.py の錨 3 本・calendar.py の祝日の CSV・
    # economy_stage2.py の OSM の店の札と営業時間=``data/realworld/osm``)。rules-table.json が無いと規則の表が空になり、
    # data が無いと経済の段階 2 の店の札が空になり(本人の所持金が変わる)、どちらも final が HEAD と違って見える
    # (2-3c の記録 tt23c/README.md §9・検収)。data は本体の data へのつなぎ(junction)を写しの木に置き、回し終えたら
    # ``cmd /c rmdir`` でつなぎだけを外す(中を消さない)。side は ``--src`` の木に足りないものがあれば止まる
    # (``--allow-incomplete-tree`` で続ける=足りないものは side の JSON の ``tree_missing`` に残る)。
    # 〔第 2 期 2-4 検収 L3〕エンジンが開く錨は src を ``_anchors_v0.json`` と ``docs/bench/anchors`` で grep して決める。
    # 2-4 V6 より後の src では 3 本=空腹の 2 本(engine/energy.py: hunger_energy_build_anchors_v0.json・
    # hunger_energy_validation_anchors_v0.json)+活動の事前分布(engine/classical.py: ssb2021_activity_prior_v0.json)。
    # V6 より前の HEAD では空腹の錨は 1 本 hunger_energy_anchors_v0.json(その版の git archive にはこちらを渡す)。
    # commute_time_dist_r3.json は構築側(build/sched/trial.py)と 2-0 の計器だけが開く=エンジンは開かない(前の版の
    # 手順は写していた=写しても挙動は変わらない)。
    # 〔第334〕錨はエンジンが開く 3 本だけを写す(docs/bench/anchors を丸ごと写すと、較正側と検証側が混ざる
    # presence_anchors_v0.json・diversity_anchors_v0.json の写しが作業用の置き場に残る=2-2 の検収 L7)。
    cmd /c mklink /J <$W の Windows の道筋>\\head_src\\data <本体の data の Windows の道筋>   # 〔2-3c〕data へのつなぎ
    python $D/byte_check_10e.py side --src $W/head_src/src --label head --scratch $W --out $W/head.json
    cmd /c rmdir <$W の Windows の道筋>\\head_src\\data                                     # つなぎだけを外す
    python $D/byte_check_10e.py side --label e1 --scratch $W --out $W/e1.json
    python $D/byte_check_10e.py side --label e1_old --kw '{"hash_scheme": "full"}' --scratch $W --out $W/e1_old.json
    python $D/byte_check_10e.py compare --a $W/head.json --b $W/e1.json --out $D/<名前>.json

``compare`` は 2 つの side を構成ごとに比べ、欄ごとに「同じ/動いた」と前後の値を書く。壁時計は比べない。
絶対パスは JSON に書かない。

〔第 2 期 2-4 検収 L2〕side は切替口の環境変数(:data:`SWITCH_ENV` のうち設定されていたもの)を ``env`` に書き、
compare は ``a``・``b`` に写す(切替口は環境変数で渡すことが多く、``kw`` だけでは何を戻したかが分からないため)。
道筋やホストを持つ変数(``*_MD``・``*_PORT``)は書かない。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"


def _wave2() -> Any:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _h(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, default=str, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def cmd_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    import shibuya
    from shibuya import cli

    w2 = _wave2()
    kw = dict(w2.configs()[args.config])
    kw.update(json.loads(args.kw or "{}"))
    if args.drop_behavior_item:  # 検収 R1 の照合: HEAD の写しで behavior-hash の項から道筋を外して回す
        from shibuya.engine import state_ledger as SL

        _real = SL.behavior_items
        _drop = set(args.drop_behavior_item.split(","))
        SL.behavior_items = lambda: tuple(x for x in _real() if x[1] not in _drop)  # type: ignore[assignment]
    if args.multiset_items:  # 検収 R1 の照合: HEAD の写しで list の並びを状態から外す(多重集合でハッシュ)
        from shibuya.engine import state_hashes as SH

        _res = SH.resolve_item
        _ms = set(args.multiset_items.split(","))

        def _sorted_item(owners, path):  # noqa: ANN001
            v = _res(owners, path)
            return sorted(v, key=SH.to_state) if path in _ms and isinstance(v, (list, tuple)) else v

        SH.resolve_item = _sorted_item  # type: ignore[assignment]
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    wall = time.perf_counter() - t0
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    src_root = Path(shibuya.__file__).resolve().parents[1]
    pc = dict(getattr(res, "process_counters", {}) or {})
    man = res.run_manifest_fields()
    last = res.checkpoints[-1] if res.checkpoints else None
    cal = dict(man.get("calendar", {}) or {})
    au = {str(k): int(v) for k, v in dict(getattr(res, "action_usage", {}) or {}).items()}
    cbc = {str(k): int(v) for k, v in dict(getattr(res, "calls_by_condition", {}) or {}).items()}
    tape_bytes = {p.name: p.stat().st_size for p in sorted(Path(args.tape).glob("*.parquet"))}
    print(json.dumps({
        "config": args.config,
        "kw": json.loads(args.kw or "{}"),
        "src_is_worktree": src_root == (REPO / "src").resolve(),
        "final": res.final_hash[:16],
        "final_full": res.final_hash,
        "calls": int(res.llm_calls),
        "blocks_rows": int(blocks.num_rows),
        "blocks_sha": w2._h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_rows": int(calls.num_rows),
        "calls_column_names": list(calls.column_names),
        "calls_columns_sha": {n: w2._h(calls.column(n).to_pylist()) for n in calls.column_names},
        "blocks_column_names": list(blocks.column_names),
        "tape_bytes": tape_bytes,
        "action_usage": au,
        "action_usage_total": int(sum(au.values())),
        "action_usage_sha": _h(au),
        "calls_by_condition": cbc,
        "rng_scheme": man.get("rng_scheme", "(欄なし)"),
        "hash_scheme": man.get("hash_scheme", "(欄なし)"),
        "calendar_weekday": cal.get("calendar_weekday", ""),
        "start_sim_datetime": str(man.get("start_sim_datetime", "")),
        "replay_date": str(man.get("replay_date", getattr(res, "replay_date", ""))),
        # 第330(B0・B1・B6): manifest の資産の指紋・旧資産の切替口・天気の記録(欄が無い版は「(欄なし)」)
        "frozen_sources": dict(man.get("frozen_sources", {}) or {}),
        "world_assets_pre10e": man.get("world_assets_pre10e", "(欄なし)"),
        "weather": man.get("weather", "(欄なし)"),
        "salient_events": int(getattr(res, "salient_events", 0)),
        "collapse": int(pc.get("salient.collapse", -1)),
        "noticed": int(getattr(res, "noticed", 0)),
        "dispatches": int(getattr(res, "dispatches", 0)),
        "arrived": int(pc.get("dispatch.arrived", -1)),
        "mean_delay_min": float(pc.get("dispatch.mean_delay_min", -1.0)),
        "meals": int(getattr(res, "meals", 0)),
        "behavior_last": getattr(last, "behavior_hash", "") if last is not None else "",
        "full_last": getattr(last, "full_hash", "") if last is not None else "",
        "end_of_day": dict(getattr(res, "state_hashes_end_of_day", {}) or {}),
        "full_external_bytes": int(sum((getattr(res, "full_hash_bytes", {}) or {}).values())),
        "full_external_bytes_by_row": dict(getattr(res, "full_hash_bytes", {}) or {}),
        "n_checkpoints": len(res.checkpoints),
        "checkpoint_s": [round(float(x), 4) for x in (getattr(res, "checkpoint_seconds", []) or [])],
        "checkpoint_total_s": round(float(res.phase_seconds.get("checkpoint", 0.0)), 4),
        "run_wall_s": round(float(getattr(res, "wall_seconds", 0.0) or 0.0), 2),
        "wall_s": round(wall, 1),
    }, ensure_ascii=False))
    return 0


#: 〔2-4 検収 L2〕side の JSON に残す切替口の環境変数(値に道筋やホストを持たないものだけ)。
SWITCH_ENV: tuple[str, ...] = (
    "SHIBUYA_PROXIMITY", "SHIBUYA_PROXIMITY_D", "SHIBUYA_SEAT_RELEASE", "SHIBUYA_ECONOMY_STAGE2",
    "SHIBUYA_ECONOMY_STAGE2_PARTS", "SHIBUYA_MEMORY_STORE", "SHIBUYA_EVENTS", "SHIBUYA_TOOL_EVENTS",
    "SHIBUYA_WRITE_GUARD", "SHIBUYA_SYSTEMS_CHECK", "SHIBUYA_WARD_AREA_M2",
    # 〔第336・第 3 期〕3-2 の幅・3-1 の影・3-5 の予約の腕(検収 L3・L6)
    "SHIBUYA_BATCH_WIDTH_S", "SHIBUYA_CALENDAR_SHADOW", "SHIBUYA_BODY_SCHEDULE",
    # 〔第337〕6-5 記憶の腕・6-2 カレンダー 1b・6-3 TM T2〜T4・6-4 CT C1・第 18-1 表と賃金の切替口(検収の指摘=side の JSON に腕を残す)
    "SHIBUYA_MEMORY_MODEL", "SHIBUYA_MEMORY_CUE", "SHIBUYA_MEMORY_PEOPLE", "SHIBUYA_MEMORY_GRAIN", "SHIBUYA_MEMORY_EMBED_MODEL",
    "SHIBUYA_CALENDAR", "SHIBUYA_CALENDAR_W20", "SHIBUYA_DECISION_PORT", "SHIBUYA_SPEECH_PORT",
    "SHIBUYA_TALK_CLOCK", "SHIBUYA_STEP_SCOPE", "SHIBUYA_CLOCK",
    "SHIBUYA_CONTACT", "SHIBUYA_CONTACT_SEND", "SHIBUYA_CONTACT_UNNOTICED",
    "SHIBUYA_CALENDAR_2",  # 〔第337 6-2 カレンダー 2 の腕〕
    "SHIBUYA_RULES_42",  # 〔第337 4-2 規則の表と天引き=旧値の再現の切替口(next-bump)〕
    "SHIBUYA_CALENDAR_3", "SHIBUYA_CALENDAR_3_TRIAL",  # 〔第337 6-2 カレンダー 3 の腕と試験用の印〕
    "SHIBUYA_RULES_42B",  # 〔4-2b 規則の表の空欄 3 件=4-2 の値の再現の切替口(next-bump)〕
    "SHIBUYA_MEAL_DEFAULT", "SHIBUYA_WAGE",
    "SHIBUYA_DUTIES",  # 〔第 6 期 6-6 ② 第 1 部〕店の仕事の腕
    "SHIBUYA_SPACE", "SHIBUYA_SLOPE", "SHIBUYA_TURN_WEIGHT",  # 〔第 5 期 空間の段 1〕移動の切替口と腕
)


def switch_env() -> dict[str, str]:
    """今の環境の切替口の環境変数(設定されていたものだけ)。"""
    return {k: os.environ[k] for k in SWITCH_ENV if k in os.environ}


#: 〔2-3c 検収 L4〕``--src`` の写しの木(``src`` の親)に要る追跡ファイルと data(リポの根から読む=docstring の決め方)。
HEAD_TREE_FILES: tuple[str, ...] = (
    "docs/design/rules-table.json",
    "docs/design/bridging-ledger.json",
    "docs/design/v2-budget-declaration.md",
    "docs/design/v2-perception-contract.md",
    "docs/design/v2-pattern-ledger.md",
    "docs/bench/anchors/hunger_energy_build_anchors_v0.json",
    "docs/bench/anchors/hunger_energy_validation_anchors_v0.json",
    "docs/bench/anchors/ssb2021_activity_prior_v0.json",
    "data/calendar/syukujitsu.csv",
    "data/realworld/osm/poi_tags_overpass_20260928.json",
    "data/realworld/osm/poi_opening_hours_overpass_20260907.json",
    # 〔第 4 期 4-3 検収 L10〕賃金の腕 occupation の入力(``engine.economy_stage2.PERSONA_POOL_RELPATH``=在庫の語・
    # ``economy.wages.DERIVED_RELDIR``=賃金構造の表の写し)。無い写しでは賃金が平均に落ちて final が HEAD と違って見える
    "data/persona_pool_v2",
    "data/research_cache/pop41b/derived",
)


def head_tree_missing(src: str | Path) -> list[str]:
    """``--src`` の写しの木に足りないもの(:data:`HEAD_TREE_FILES` のうち無いもの)。"""
    root = Path(src).resolve().parent
    return [rel for rel in HEAD_TREE_FILES if not (root / rel).exists()]


def cmd_side(args: argparse.Namespace) -> int:
    w2 = _wave2()
    scratch = Path(args.scratch)
    names = list(w2.configs()) if not args.only else [s for s in args.only.split(",") if s]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    tree_missing: list[str] = []
    if args.src:
        env["PYTHONPATH"] = str(Path(args.src).resolve())
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
        # 〔2-3c 検収 L4〕写しの木に足りないものがあると HEAD の側が別の世界になる=止める(比べる欄は変えない)
        tree_missing = head_tree_missing(args.src)
        if tree_missing and not args.allow_incomplete_tree:
            print("--src の写しの木に足りないもの(docstring の手順で写す・data はつなぎ):", *tree_missing,
                  sep="\n  ", file=sys.stderr)
            return 2

    def one(name: str) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed),
               "--tape", str(scratch / f"{args.label}_{name}"), "--kw", args.kw or "",
               "--drop-behavior-item", args.drop_behavior_item or "",
               "--multiset-items", args.multiset_items or ""]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": r.stderr[-3000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    got: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, names):
            got[row["config"]] = row
            print(row["config"], row.get("final"), row.get("calls"), row.get("salient_events"),
                  row.get("dispatches"), row.get("src_is_worktree"), (row.get("error") or "")[-300:], flush=True)
    doc = {"label": args.label, "kw": json.loads(args.kw or "{}"), "src": "写し" if args.src else "作業木",
           "env": switch_env(), "tree_missing": tree_missing,
           "drop_behavior_item": args.drop_behavior_item or "", "multiset_items": args.multiset_items or "",
           "agents": args.agents, "seed": args.seed, "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


#: 比べる欄(壁時計・時間は除く)。
COMPARE_KEYS = ("final", "calls", "blocks_rows", "blocks_sha", "calls_rows", "calls_column_names", "calls_columns_sha",
                "action_usage_total", "action_usage_sha", "calls_by_condition", "salient_events", "collapse",
                "noticed", "dispatches", "arrived", "mean_delay_min", "meals", "behavior_last", "full_last",
                "end_of_day", "start_sim_datetime", "replay_date", "calendar_weekday", "rng_scheme",
                # 第330(B0): manifest の frozen_sources(B0 で動く量はこれだけ)
                "frozen_sources")


def cmd_compare(args: argparse.Namespace) -> int:
    a = json.loads(Path(args.a).read_text(encoding="utf-8"))
    b = json.loads(Path(args.b).read_text(encoding="utf-8"))
    rows: dict[str, Any] = {}
    for name in a["runs"]:
        ra, rb = a["runs"][name], b["runs"].get(name, {})
        if "error" in ra or "error" in rb:
            rows[name] = {"error_a": ra.get("error", "")[-500:], "error_b": rb.get("error", "")[-500:]}
            continue
        same, moved = [], {}
        for k in COMPARE_KEYS:
            va, vb = ra.get(k), rb.get(k)
            if va == vb:
                same.append(k)
            else:
                moved[k] = {"a": va, "b": vb}
        rows[name] = {"same": same, "moved": moved,
                      "calls_delta": (rb.get("calls", 0) or 0) - (ra.get("calls", 0) or 0),
                      "blocks_rows_delta": (rb.get("blocks_rows", 0) or 0) - (ra.get("blocks_rows", 0) or 0),
                      "action_usage_delta": ((rb.get("action_usage_total", 0) or 0)
                                             - (ra.get("action_usage_total", 0) or 0)),
                      "noticed_delta": (rb.get("noticed", 0) or 0) - (ra.get("noticed", 0) or 0)}
    doc = {"a": {"label": a.get("label"), "kw": a.get("kw"), "src": a.get("src"), "env": a.get("env")},
           "b": {"label": b.get("label"), "kw": b.get("kw"), "src": b.get("src"), "env": b.get("env")},
           "note": args.note, "keys": list(COMPARE_KEYS), "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n_same_final = sum(1 for r in rows.values() if "moved" in r and "final" not in r["moved"])
    print(f"{len(rows)} 構成・final が同じ {n_same_final}")
    for name, r in rows.items():
        print(name, sorted(r.get("moved", {}).keys()) if "moved" in r else r)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "side"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--kw", default="")
        sp.add_argument("--drop-behavior-item", default="")
        sp.add_argument("--multiset-items", default="")
        if name == "one":
            sp.add_argument("--config", required=True)
            sp.add_argument("--tape", required=True)
        else:
            sp.add_argument("--src", default="")
            sp.add_argument("--label", required=True)
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", default="")
            sp.add_argument("--jobs", type=int, default=4)
            sp.add_argument("--allow-incomplete-tree", action="store_true")
    sp = sub.add_parser("compare")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--note", default="")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
