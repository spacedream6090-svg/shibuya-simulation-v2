# -*- coding: utf-8 -*-
"""bytecheck.check — 1 構成のラン(``one``)・片側の 19 構成(``side``)・2 つの side の比べ(``compare``)・基準の commit との 1 回通し(``run``)。

出典(写した): ``docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py`` の ``cmd_one``・``cmd_side``・``cmd_compare``
(欄・ハッシュの作り方・比べ方は同じ)。足したもの:

- ``one``: 監査フックで開いたファイルを記録する(``tree_reads``=写しの木の ``src``・``data`` の外・``foreign_reads``=写しの側が
  道具のリポのファイルを開いたもの)・``src_as_expected``(読んだ ``shibuya`` が渡した src か)。
- ``side``: ``--src`` が無いときも作業木の ``src`` を ``PYTHONPATH`` に置く(venv の editable の道が本体の src を指していても
  作業木を読む)・``SHIBUYA_BUDGET_MD`` は置かない(写しの木の宣言の表を読む)・誤りがあれば終了コード 2。
- ``compare``: 終了コード(同じ 0・動いた 1・誤り 2)・``summary`` と ``checks`` の欄。
- ``run``: 基準の commit の写し → data のつなぎ → 両側の side → compare → つなぎを外す、を 1 回で。

JSON に絶対パスを書かない(誤りの文は :func:`mask_paths` で伏せる)。壁時計は比べない。
"""

from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

from bytecheck import configs as C
from bytecheck import tree as T

TOOL_DIR = Path(__file__).resolve().parent
REPO = TOOL_DIR.parents[1]
CLI = TOOL_DIR / "cli.py"

EXIT_SAME, EXIT_MOVED, EXIT_ERROR = 0, 1, 2


def drop_package_metadata(paths: list[str]) -> list[str]:
    """包みの名札(``*.egg-info``・``*.dist-info``)を外す(第346 親)。

    venv の editable の取り込みは、道具を本体のリポから回すと本体の ``src/shibuya_sim.egg-info`` を読む
    (``importlib.metadata`` の入口の表)。名札はコードでもデータでもなく結果に効かないので、
    「写しの側が道具のリポのファイルを開いた」には数えない。コードの出どころは ``src_as_expected`` が別に確かめる。
    """
    return [x for x in paths if not any(part.endswith((".egg-info", ".dist-info")) for part in Path(x).parts)]

def _h_sorted(obj: Any) -> str:
    """``byte_check_10e._h``(鍵を並べる)。``action_usage_sha`` に使う。"""
    raw = json.dumps(obj, ensure_ascii=False, default=str, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _h_plain(obj: Any) -> str:
    """``wave2_bytecheck._h``(鍵を並べない)。``blocks_sha``・``calls_columns_sha`` に使う。"""
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


# ------------------------------------------------------------------ 伏せる
def mask_paths(text: str, roots: Iterable[tuple[str | Path, str]]) -> str:
    """``text`` の中の道筋を伏せる(``(道筋, 置き換え)`` の並び・長いものから・``\\`` と ``/`` の両方の書き方)。"""
    pairs: list[tuple[str, str]] = []
    for p, label in roots:
        if not str(p):
            continue
        s = os.path.abspath(str(p))
        for v in {s, s.replace("\\", "/"), s.replace("/", "\\")}:
            pairs.append((v, label))
    for v, label in sorted(pairs, key=lambda x: -len(x[0])):
        text = text.replace(v, label)
        if os.name == "nt":  # 大文字小文字の違う書き方(ドライブの文字など)
            low = text.lower()
            i = low.find(v.lower())
            while i >= 0:
                text = text[:i] + label + text[i + len(v):]
                low = text.lower()
                i = low.find(v.lower(), i + len(label))
    return text


def _mask_roots(*extra: tuple[str | Path, str]) -> list[tuple[str | Path, str]]:
    return [*extra, (REPO, "<repo>"), (sys.prefix, "<python>"), (sys.base_prefix, "<python>"), (Path.home(), "<home>")]


# ------------------------------------------------------------------ one
_OPENED: set[str] = set()


def _audit(event: str, args: tuple[Any, ...]) -> None:
    if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        try:
            _OPENED.add(os.fsdecode(args[0]))
        except (TypeError, ValueError):
            pass


def _under(path_nc: str, root_nc: str) -> bool:
    return path_nc == root_nc or path_nc.startswith(root_nc.rstrip("\\/") + os.sep)


def opened_outside(opened: Iterable[str], root: Path, *, skip_tops: Iterable[str], skip_dirs: Iterable[str | Path]) -> list[str]:
    """``root`` の下で開いたファイル(``skip_tops`` の最上位と ``skip_dirs`` の下を除く)の、``root`` からの posix の道筋。"""
    root_abs = os.path.abspath(str(root))
    root_nc = os.path.normcase(root_abs)
    skips = [os.path.normcase(os.path.abspath(str(d))) for d in skip_dirs if str(d)]
    tops = {os.path.normcase(t) for t in skip_tops}
    out: set[str] = set()
    for raw in opened:
        a = os.path.abspath(raw)
        nc = os.path.normcase(a)
        if not _under(nc, root_nc) or nc == root_nc or any(_under(nc, s) for s in skips):
            continue
        rel = a[len(root_abs):].lstrip("\\/")
        if os.path.normcase(rel.replace("\\", "/").split("/")[0]) in tops:
            continue
        out.add(rel.replace("\\", "/"))
    return sorted(out)


def cmd_one(*, config: str, tape: str, world: str, agents: int, seed: int, kw: str = "",
            drop_behavior_item: str = "", multiset_items: str = "", expect_src: str = "", scratch: str = "") -> int:
    """1 構成を回し、比べる欄を 1 行の JSON で標準出力に出す(``byte_check_10e.cmd_one`` と同じ欄+開いたファイル)。"""
    sys.addaudithook(_audit)
    import pyarrow.parquet as pq

    import shibuya
    from shibuya import cli

    kwd = dict(C.configs()[config])
    kwd.update(json.loads(kw or "{}"))
    if drop_behavior_item:  # 検収 R1 の照合: behavior-hash の項から道筋を外して回す(10e と同じ口)
        from shibuya.engine import state_ledger as SL

        _real = SL.behavior_items
        _drop = set(drop_behavior_item.split(","))
        SL.behavior_items = lambda: tuple(x for x in _real() if x[1] not in _drop)  # type: ignore[assignment]
    if multiset_items:  # 検収 R1 の照合: list の並びを状態から外す(多重集合でハッシュ・10e と同じ口)
        from shibuya.engine import state_hashes as SH

        _res = SH.resolve_item
        _ms = set(multiset_items.split(","))

        def _sorted_item(owners, path):  # noqa: ANN001
            v = _res(owners, path)
            return sorted(v, key=SH.to_state) if path in _ms and isinstance(v, (list, tuple)) else v

        SH.resolve_item = _sorted_item  # type: ignore[assignment]
    t0 = time.perf_counter()
    res = cli.run(n_agents=agents, seed=seed, world_dir=world, tape_path=tape, **kwd)
    wall = time.perf_counter() - t0
    calls = pq.read_table(Path(tape) / "calls.parquet")
    blocks = pq.read_table(Path(tape) / "blocks.parquet")
    src_root = Path(shibuya.__file__).resolve().parents[1]
    tree_root = src_root.parent
    pc = dict(getattr(res, "process_counters", {}) or {})
    man = res.run_manifest_fields()
    last = res.checkpoints[-1] if res.checkpoints else None
    cal = dict(man.get("calendar", {}) or {})
    au = {str(k): int(v) for k, v in dict(getattr(res, "action_usage", {}) or {}).items()}
    cbc = {str(k): int(v) for k, v in dict(getattr(res, "calls_by_condition", {}) or {}).items()}
    tape_bytes = {p.name: p.stat().st_size for p in sorted(Path(tape).glob("*.parquet"))}
    opened = sorted(_OPENED)
    skip_dirs = [TOOL_DIR, *T.python_prefixes(), scratch, tape]
    tree_reads = opened_outside(opened, tree_root, skip_tops=("src", "data", ".git", ".venv", "venv"), skip_dirs=skip_dirs)
    foreign: list[str] = []
    if os.path.normcase(str(tree_root)) != os.path.normcase(str(REPO.resolve())):
        foreign = drop_package_metadata(opened_outside(opened, REPO, skip_tops=("data", ".git", ".venv", "venv"),
                                                       skip_dirs=[*skip_dirs, tree_root]))
    print(json.dumps({
        "config": config,
        "kw": json.loads(kw or "{}"),
        "src_is_worktree": src_root == (REPO / "src").resolve(),
        "src_as_expected": (src_root == Path(expect_src).resolve()) if expect_src else None,
        "final": res.final_hash[:16],
        "final_full": res.final_hash,
        "calls": int(res.llm_calls),
        "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h_plain({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_rows": int(calls.num_rows),
        "calls_column_names": list(calls.column_names),
        "calls_columns_sha": {n: _h_plain(calls.column(n).to_pylist()) for n in calls.column_names},
        "blocks_column_names": list(blocks.column_names),
        "tape_bytes": tape_bytes,
        "action_usage": au,
        "action_usage_total": int(sum(au.values())),
        "action_usage_sha": _h_sorted(au),
        "calls_by_condition": cbc,
        "rng_scheme": man.get("rng_scheme", "(欄なし)"),
        "hash_scheme": man.get("hash_scheme", "(欄なし)"),
        "calendar_weekday": cal.get("calendar_weekday", ""),
        "start_sim_datetime": str(man.get("start_sim_datetime", "")),
        "replay_date": str(man.get("replay_date", getattr(res, "replay_date", ""))),
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
        "tree_reads": tree_reads,
        "foreign_reads": foreign,
    }, ensure_ascii=False))
    return 0


# ------------------------------------------------------------------ side
def resolve_names(set_name: str, only: str) -> list[str]:
    """回す構成の並び(``only`` があればそれ・無ければ組の並び)。知らない名は ``KeyError``。"""
    known = C.configs()
    names = [s for s in only.split(",") if s] if only else list(C.set_configs(set_name))
    bad = [n for n in names if n not in known]
    if bad:
        raise KeyError(f"知らない構成: {bad}")
    return names


def side(*, label: str, scratch: str | Path, out: str | Path, src: str | Path = "", set_name: str = "all19",
         only: str = "", jobs: int = 4, kw: str = "", world: str = "data/world/v2", agents: int = 5_000, seed: int = 1,
         drop_behavior_item: str = "", multiset_items: str = "", allow_incomplete_tree: bool = False,
         commit: str = "") -> int:
    """片側の構成を回して side の JSON を書く。戻り値=0(誤りなし)/ 2(ランの誤り・写しの木の不足・開いたファイルの問題)。"""
    src_dir = Path(src).resolve() if str(src) else (REPO / "src").resolve()
    root = src_dir.parent
    is_worktree = src_dir == (REPO / "src").resolve()
    scratch_p = Path(scratch)
    names = resolve_names(set_name, only)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(src_dir)
    env.update(C.set_env(set_name))
    missing = T.tree_missing(root)
    if missing and not allow_incomplete_tree:
        print("src の木に足りないもの(写しは run か git archive で・data はつなぎ):", *missing, sep="\n  ", file=sys.stderr)
        return EXIT_ERROR
    masks = _mask_roots((root, "<tree>"), (scratch_p, "<scratch>"))

    def one(name: str) -> dict[str, Any]:
        cmd = [sys.executable, str(CLI), "one", "--config", name, "--world", world, "--agents", str(agents),
               "--seed", str(seed), "--tape", str(scratch_p / f"{label}_{name}"), "--kw", kw,
               "--drop-behavior-item", drop_behavior_item, "--multiset-items", multiset_items,
               "--expect-src", str(src_dir), "--scratch", str(scratch_p)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": mask_paths(r.stderr[-3000:], masks)}
        try:
            return json.loads(r.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError):
            return {"config": name, "error": mask_paths("出力の最後の行が JSON でない: " + r.stdout[-500:], masks)}

    got: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=max(1, int(jobs))) as ex:
        for row in ex.map(one, names):
            got[row["config"]] = row
            print(label, row["config"], row.get("final"), row.get("calls"), row.get("wall_s"),
                  "src_ok" if row.get("src_as_expected") else "SRC?", (row.get("error") or "")[-300:], flush=True)
    reads = sorted({x for r in got.values() for x in r.get("tree_reads", [])})
    foreign = sorted({x for r in got.values() for x in r.get("foreign_reads", [])})
    cls = T.classify_reads(reads, root)
    doc = {"label": label, "set": set_name, "configs": names, "kw": json.loads(kw or "{}"),
           "src": "作業木" if is_worktree else "写し", "commit": commit,
           "env": C.switch_env(env), "env_hidden": C.hidden_env_names(env), "tree_missing": missing,
           "tree_reads": reads, "tree_reads_unlisted": cls["unlisted"], "tree_reads_absent": cls["absent"],
           "foreign_reads": foreign, "drop_behavior_item": drop_behavior_item, "multiset_items": multiset_items,
           "agents": agents, "seed": seed, "runs": got}
    Path(out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    bad_rows = [n for n, r in got.items() if "error" in r or r.get("src_as_expected") is False]
    if bad_rows or cls["unlisted"] or cls["absent"] or foreign:
        print("side の誤り:", {"rows": bad_rows, "unlisted": cls["unlisted"], "absent": cls["absent"], "foreign": foreign},
              file=sys.stderr)
        return EXIT_ERROR
    return 0


# ------------------------------------------------------------------ compare
def side_checks(doc: dict[str, Any]) -> list[str]:
    """side の JSON の誤り(ランの誤り・読んだ src の違い・開いたファイルの問題)。古い記録で欄が無いものは見ない。"""
    out: list[str] = []
    for name, r in doc.get("runs", {}).items():
        if "error" in r:
            out.append(f"{name}: ランの誤り")
        if r.get("src_as_expected") is False:
            out.append(f"{name}: 渡した src と違う shibuya を読んだ")
    for k, msg in (("tree_reads_unlisted", "写しの一覧に無い追跡ファイルを開いた"),
                   ("tree_reads_absent", "写しの木に無いファイルを開こうとした"),
                   ("foreign_reads", "写しの側が道具のリポのファイルを開いた")):
        if doc.get(k):
            out.append(f"{msg}: {doc[k]}")
    return out


def compare_docs(a: dict[str, Any], b: dict[str, Any], note: str = "") -> tuple[dict[str, Any], int]:
    """2 つの side を構成ごとに比べる(欄ごとに同じ/動いた・前後の値)。戻り値=(compare の JSON, 終了コード)。"""
    rows: dict[str, Any] = {}
    names = list(a.get("runs", {})) + [n for n in b.get("runs", {}) if n not in a.get("runs", {})]
    for name in names:
        ra, rb = a.get("runs", {}).get(name), b.get("runs", {}).get(name)
        if ra is None or rb is None:
            rows[name] = {"missing_in": "a" if ra is None else "b"}
            continue
        if "error" in ra or "error" in rb:
            rows[name] = {"error_a": ra.get("error", "")[-500:], "error_b": rb.get("error", "")[-500:]}
            continue
        same, moved = [], {}
        for k in C.COMPARE_KEYS:
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
    checks = {"a": side_checks(a), "b": side_checks(b)}
    n_err = sum(1 for r in rows.values() if "moved" not in r)
    n_moved = sum(1 for r in rows.values() if r.get("moved"))
    n_same = sum(1 for r in rows.values() if "moved" in r and not r["moved"])
    code = EXIT_ERROR if (n_err or checks["a"] or checks["b"]) else EXIT_MOVED if n_moved else EXIT_SAME
    head = ("label", "set", "kw", "src", "commit", "env", "env_hidden")
    doc = {"a": {k: a.get(k) for k in head}, "b": {k: b.get(k) for k in head}, "note": note,
           "keys": list(C.COMPARE_KEYS),
           "summary": {"configs": len(rows), "all_same": n_same, "moved": n_moved, "errors": n_err,
                       "final_same": sum(1 for r in rows.values() if "moved" in r and "final" not in r["moved"]),
                       "result": {EXIT_SAME: "同じ", EXIT_MOVED: "動いた", EXIT_ERROR: "誤り"}[code],
                       "exit_code": code},
           "checks": checks, "rows": rows}
    return doc, code


def compare(*, a: str | Path, b: str | Path, out: str | Path, note: str = "") -> int:
    """side の JSON 2 本を比べて compare の JSON を書く。戻り値=0 同じ / 1 動いた欄がある / 2 誤り。"""
    da = json.loads(Path(a).read_text(encoding="utf-8"))
    db = json.loads(Path(b).read_text(encoding="utf-8"))
    doc, code = compare_docs(da, db, note)
    Path(out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    s = doc["summary"]
    print(f"{s['configs']} 構成・25 欄すべて同じ {s['all_same']}・動いた {s['moved']}・誤り {s['errors']}"
          f"・final が同じ {s['final_same']} → {s['result']}(終了コード {code})")
    for name, r in doc["rows"].items():
        if r.get("moved") or "moved" not in r:
            print(" ", name, sorted(r.get("moved", {}).keys()) if "moved" in r else r)
    for k in ("a", "b"):
        for c in doc["checks"][k]:
            print(f"  [{k}] {c}")
    return code


# ------------------------------------------------------------------ run
#: 呼び手の環境にあっても run を止めない変数(mock のランの結果に効かない=艦隊の鍵)。
STRAY_ENV_OK: tuple[str, ...] = ("SHIBUYA_FLEET_API_KEY",)


def stray_env(env: dict[str, str]) -> list[str]:
    """呼び手の環境に置かれた ``SHIBUYA_`` の変数の名(run は既定で止める=構成が黙って変わらないように)。"""
    return sorted(k for k in env if k.startswith("SHIBUYA_") and k not in STRAY_ENV_OK)


def worktree_commit(src: str | Path = "") -> str:
    """比べる側が作業木の src なら、その HEAD の commit(src に未 commit の変更があれば ``+dirty``)。それ以外は ``""``。"""
    src_dir = Path(src).resolve() if str(src) else (REPO / "src").resolve()
    if src_dir != (REPO / "src").resolve():
        return ""
    try:
        head = T.resolve_commit(REPO, "HEAD")
    except ValueError:
        return ""
    st = T.git(REPO, "status", "--porcelain", "--", "src")
    return head + ("+dirty" if st.returncode == 0 and st.stdout.strip() else "")


def run(*, work: str | Path, out_dir: str | Path, base: str = "HEAD", src: str | Path = "", set_name: str = "all19",
        only: str = "", jobs: int = 4, label: str = "work", kw: str = "", extra_paths: Iterable[str] = (),
        inherit_env: bool = False, note: str = "", world: str = "data/world/v2", agents: int = 5_000,
        seed: int = 1) -> int:
    """基準の commit と比べる側の src を 1 回で比べる。戻り値=0 同じ / 1 動いた欄がある / 2 誤り。

    ① 基準の commit の ``src`` と :data:`tree.TRACKED_READS`(+``extra_paths``)を ``work/tree`` へ git archive で写す
    ② ``work/tree/data`` を道具のリポの data へのつなぎにする ③ 基準の側と比べる側の side を回す ④ compare を書く
    ⑤ つなぎだけを外す(中は消さない・写しの木とテープは ``work`` に残る)。
    """
    t_start = time.perf_counter()
    try:
        commit = T.resolve_commit(REPO, base)
        names = resolve_names(set_name, only)
    except (ValueError, KeyError) as e:
        print(e, file=sys.stderr)
        return EXIT_ERROR
    stray = stray_env(dict(os.environ))
    if stray and not inherit_env:
        print("呼び手の環境に SHIBUYA_ の変数がある(構成が変わる=止めた。続けるなら --inherit-env):", stray, file=sys.stderr)
        return EXIT_ERROR
    work_p = Path(work)
    if work_p.exists() and any(work_p.iterdir()):
        print("作業の置き場が空でない(前のランの残り=消すなら単独のコマンドで・つなぎが残っていないか先に確かめる)",
              file=sys.stderr)
        return EXIT_ERROR
    data_target = REPO / "data"
    if not data_target.is_dir():
        print("道具のリポに data が無い(つなぎの先)", file=sys.stderr)
        return EXIT_ERROR
    out_p = Path(out_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    tree_root = work_p / "tree"
    tapes = work_p / "tapes"
    paths = T.archive_paths(extra_paths)
    have, lack = T.paths_in_commit(REPO, commit, paths)
    if "src" in lack:
        print("基準の commit に src が無い", file=sys.stderr)
        return EXIT_ERROR
    tapes.mkdir(parents=True, exist_ok=True)
    T.git_archive(REPO, commit, have, tree_root)
    print(f"写した: commit {commit[:12]}・{len(have)} 個の道筋(無かったもの {lack})", flush=True)
    link = T.place_data_link(tree_root, data_target)
    short = commit[:7]
    prefix = f"{set_name}_only" if only else set_name  # --only で組の一部だけ回したことが名で分かるように
    base_json = out_p / f"{prefix}_base_{short}.json"
    work_json = out_p / f"{prefix}_{label}.json"
    cmp_json = out_p / f"{prefix}_compare_base_{short}_vs_{label}.json"
    common = dict(set_name=set_name, only=",".join(names), jobs=jobs, kw=kw, world=world, agents=agents, seed=seed)
    link_ok = False
    codes: list[int] = []
    try:
        t0 = time.perf_counter()
        codes.append(side(label=f"base_{short}", scratch=tapes, out=base_json, src=tree_root / "src", commit=commit,
                          **common))
        t1 = time.perf_counter()
        codes.append(side(label=label, scratch=tapes, out=work_json, src=src, commit=worktree_commit(src), **common))
        t2 = time.perf_counter()
        print(f"壁時計: 基準の側 {t1 - t0:.0f} 秒・比べる側 {t2 - t1:.0f} 秒", flush=True)
    finally:
        try:
            T.remove_link(link)
            link_ok = True
            print("つなぎを外した(中は消していない)", flush=True)
        except Exception as e:  # noqa: BLE001 - 外せなかったことを必ず知らせる
            print(f"!! つなぎを外せなかった: {e}\n   cmd /c rmdir で、つなぎの道筋だけを外すこと(中を消すコマンドを使わない)",
                  file=sys.stderr)
    if not (base_json.is_file() and work_json.is_file()):
        return EXIT_ERROR
    code = compare(a=base_json, b=work_json, out=cmp_json,
                   note=note or f"tools/bytecheck run: 基準 {short} の写し vs {label}・組 {set_name}")
    print(f"全体の壁時計 {time.perf_counter() - t_start:.0f} 秒", flush=True)
    if not link_ok or EXIT_ERROR in codes:
        return EXIT_ERROR
    return code
