# -*- coding: utf-8 -*-
"""bytecheck.check — 1 構成のラン(``one``)・片側の 19 構成(``side``)・2 つの side の比べ(``compare``)・基準の commit との 1 回通し(``run``)。

出典(写した): ``docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py`` の ``cmd_one``・``cmd_side``・``cmd_compare``
(25 欄・ハッシュの作り方は同じ)。足したもの:

- ``one``: 監査フックで開いたファイルを記録して仕分ける(:func:`sort_reads`=``tree_reads``・``foreign_reads``・
  ``outside_reads``・``outside_above_tree``)・``src_as_expected``(読んだ ``shibuya`` が渡した src か)・読んだ ``shibuya`` の
  モジュールの digest(``src_files``)。第346 の検収 H1 で、テープの全ファイルの sha256 と 2 表のスキーマ・manifest と
  ``run_meta.json`` の欄ごとのハッシュ・全 checkpoint を足した(:mod:`bytecheck.fields`)。
- ``side``: ``--src`` が無いときも作業木の ``src`` を ``PYTHONPATH`` に置く(venv の editable の道が本体の src を指していても
  作業木を読む)・``PYTHONHASHSEED`` を両側に同じ値で置いて記録する(検収 L1)・``SHIBUYA_BUDGET_MD`` は置かない(写しの木の
  宣言の表を読む)・``--extra-path`` を写しの一覧に足す(検収 M2)・誤りがあれば終了コード 2。
- ``compare``: 25 欄+:data:`fields.NEW_KEYS` を正準の JSON で比べる・構成が 0・比べる欄の欠け・条件の不一致は誤り(検収 M3)・
  古い記録に無い新しい欄は「比べていない」と注を付ける・終了コード(同じ 0・動いた 1・誤り 2)。
- ``run``: 基準の commit の写し → data のつなぎ → 両側の side → 確かめ → compare → つなぎを外す、を 1 回で。作業の置き場が
  git の作業木の中なら断る(検収 M4)。両側の JSON がこのランのものか(検収 L5)・基準の側が読んだ src が写しの木と同じか
  (検収 M1)を確かめる。

JSON に絶対パスを書かない(道筋は :func:`mask_paths` と :func:`mask_outside` で伏せる)。壁時計は比べない。
"""

from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Final, Iterable

from bytecheck import configs as C
from bytecheck import fields as F
from bytecheck import tree as T

TOOL_DIR = Path(__file__).resolve().parent
REPO = TOOL_DIR.parents[1]
CLI = TOOL_DIR / "cli.py"
#: つなぎの先(道具のリポの data)。試験が差し替える。
DATA_DIR = REPO / "data"

EXIT_SAME, EXIT_MOVED, EXIT_ERROR = 0, 1, 2

#: side の JSON の形の版(新しい欄=:data:`fields.NEW_KEYS`・``src_files``・``outside_reads`` を持つ)。
TOOL_ID: Final[str] = "tools/bytecheck/2"
#: 両側に置く ``PYTHONHASHSEED``(検収 L1: 呼び手の値に任せない=両側で同じ・記録に残す)。
PYTHONHASHSEED: Final[str] = "0"

#: 写しの木の下で、開いても ``tree_reads`` に数えない最上位(読むコードと data のつなぎと道具の外のもの)。
TREE_SKIP_TOPS: Final[tuple[str, ...]] = ("src", "data", ".git", ".venv", "venv")
#: 写しの側が道具のリポの下で開いても ``foreign_reads`` に数えない最上位(data は両側が同じつなぎの先を読む)。
FOREIGN_SKIP_TOPS: Final[tuple[str, ...]] = ("data", ".git", ".venv", "venv")
#: 写しの木の上の階でこの名の下を開いたら ``outside_above_tree``(根を上へ辿る読み口が写しの木の外を読んだ)。
ABOVE_TOPS: Final[tuple[str, ...]] = ("docs", "tools", "tests", "src", "data")
#: ``outside_reads`` に残す数の上限(数は ``outside_reads_n``)。
OUTSIDE_MAX: Final[int] = 200

#: 2 つの side で同じでなければならない条件(違えば誤り=検収 M3)。古い記録に無い欄は「比べていない」。
CONDITION_KEYS: Final[tuple[str, ...]] = (
    "set", "kw", "agents", "seed", "world", "env", "env_hidden", "drop_behavior_item", "multiset_items",
    "pythonhashseed",
)


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


def parse_kw(kw: str) -> dict[str, Any]:
    """``--kw`` の JSON を読む(JSON の辞書でなければ ``ValueError``=ランの前に止める・検収 L3)。"""
    try:
        v = json.loads(kw or "{}")
    except json.JSONDecodeError as e:
        raise ValueError(f"--kw が JSON でない: {e}") from None
    if not isinstance(v, dict):
        raise ValueError("--kw は JSON の辞書で渡す")
    return v


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


def tree_label(root: str | Path) -> str:
    """読む src の親の伏せ字(道具のリポなら ``<repo>``・写しの木なら ``<tree>``=検収 L8: 比べる側の誤りの文が ``<tree>`` に見えない)。"""
    same = os.path.normcase(os.path.abspath(str(root))) == os.path.normcase(os.path.abspath(str(REPO)))
    return "<repo>" if same else "<tree>"


_DRIVE_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z]:")


def mask_outside(paths: Iterable[str], masks: Iterable[tuple[str | Path, str]]) -> list[str]:
    """リポと写しの木の外の道筋を伏せる(知っている置き場は名に・それ以外は ``<abs>/…``=ドライブと頭の ``/`` を外す)。"""
    roots = list(masks)
    out: set[str] = set()
    for a in paths:
        m = mask_paths(a, roots).replace("\\", "/")
        if _DRIVE_RE.match(m) or m.startswith("/"):
            m = "<abs>/" + os.path.splitdrive(m)[1].lstrip("/")
        out.add(m)
    return sorted(out)


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


def sort_reads(seen: Iterable[str], *, tree_root: str | Path, repo: str | Path,
               skip_dirs: Iterable[str | Path]) -> dict[str, list[str]]:
    """監査フックの記録(開いたファイル)を仕分ける。

    - ``tree_reads``: 読む src の親(写しの木か道具のリポ)の下で、:data:`TREE_SKIP_TOPS` の外のもの(リポの根からの道筋)。
    - ``foreign``: 写しの側(読む src の親が道具のリポでない)が道具のリポの下で開いたもの(:data:`FOREIGN_SKIP_TOPS` と
      ``skip_dirs`` と包みの名札を除く)。
    - ``outside``: 読む src の親・道具のリポ・``skip_dirs`` のどれの下でもないもの(絶対の道筋=JSON に出す前に伏せる・検収 M4)。
    - ``above``: ``outside`` のうち、読む src の親の上の階の :data:`ABOVE_TOPS` の下のもの(根を上へ辿る読み口が写しの木の外の
      ``docs`` などを読んだ=誤り)。
    """
    seen = list(seen)
    skip_list = [d for d in skip_dirs if str(d)]
    tree_abs = os.path.abspath(str(tree_root))
    repo_abs = os.path.abspath(str(repo))
    tree_reads = opened_outside(seen, Path(tree_abs), skip_tops=TREE_SKIP_TOPS, skip_dirs=skip_list)
    foreign: list[str] = []
    if os.path.normcase(tree_abs) != os.path.normcase(repo_abs):
        foreign = drop_package_metadata(opened_outside(seen, Path(repo_abs), skip_tops=FOREIGN_SKIP_TOPS,
                                                       skip_dirs=[*skip_list, tree_abs]))
    skips = [os.path.normcase(os.path.abspath(str(d))) for d in [*skip_list, tree_abs, repo_abs]]
    ancestors = [os.path.normcase(str(p)) for p in Path(tree_abs).parents]
    tops = {os.path.normcase(t) for t in ABOVE_TOPS}
    outside: set[str] = set()
    above: set[str] = set()
    for raw in seen:
        a = os.path.abspath(raw)
        nc = os.path.normcase(a)
        if any(_under(nc, s) for s in skips):
            continue
        outside.add(a)
        for anc in ancestors:
            if nc != anc and _under(nc, anc):
                first = nc[len(anc):].lstrip("\\/").replace("\\", "/").split("/")[0]
                if first in tops:
                    above.add(a)
                    break
    return {"tree_reads": tree_reads, "foreign": foreign, "outside": sorted(outside), "above": sorted(above)}


def loaded_src_files(src_root: str | Path) -> tuple[dict[str, str], list[str]]:
    """読み込んだ ``shibuya`` のモジュールのファイルの digest(``src_root`` からの posix の道筋 → バイトの sha256 の頭 16 桁)と、
    ``src_root`` の外から読んだモジュールの名(検収 M1: run が基準の側の digest を写しの木と照らす)。"""
    root_abs = os.path.abspath(str(src_root))
    root_nc = os.path.normcase(root_abs)
    files: dict[str, str] = {}
    stray: list[str] = []
    for name, mod in sorted(dict(sys.modules).items()):
        if name != "shibuya" and not name.startswith("shibuya."):
            continue
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        a = os.path.abspath(f)
        if not _under(os.path.normcase(a), root_nc):
            stray.append(name)
            continue
        rel = a[len(root_abs):].lstrip("\\/").replace("\\", "/")
        files[rel] = hashlib.sha256(Path(a).read_bytes()).hexdigest()[:16]
    return dict(sorted(files.items())), stray


def _read_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else {}


def cmd_one(*, config: str, tape: str, world: str, agents: int, seed: int, kw: str = "",
            drop_behavior_item: str = "", multiset_items: str = "", expect_src: str = "", scratch: str = "") -> int:
    """1 構成を回し、比べる欄を 1 行の JSON で標準出力に出す(``byte_check_10e.cmd_one`` の欄+開いたファイル+H1 の欄)。"""
    sys.addaudithook(_audit)
    import pyarrow.parquet as pq

    import shibuya
    from shibuya import cli

    kwd = dict(C.configs()[config])
    kwd.update(parse_kw(kw))
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
    tape_p = Path(tape)
    calls = pq.read_table(tape_p / "calls.parquet")
    blocks = pq.read_table(tape_p / "blocks.parquet")
    src_root = Path(shibuya.__file__).resolve().parents[1]
    tree_root = src_root.parent
    pc = dict(getattr(res, "process_counters", {}) or {})
    man = res.run_manifest_fields()  # 規則の表や台帳を読むことがある=開いたファイルの記録はこの後に取る
    seen = sorted(_OPENED)  # この後に道具が読むのはテープと src の下だけ(どちらも仕分けで外す)
    last = res.checkpoints[-1] if res.checkpoints else None
    cal = dict(man.get("calendar", {}) or {})
    au = {str(k): int(v) for k, v in dict(getattr(res, "action_usage", {}) or {}).items()}
    cbc = {str(k): int(v) for k, v in dict(getattr(res, "calls_by_condition", {}) or {}).items()}
    tape_bytes = {p.name: p.stat().st_size for p in sorted(tape_p.glob("*.parquet"))}
    rd = sort_reads(seen, tree_root=tree_root, repo=REPO, skip_dirs=[TOOL_DIR, *T.python_prefixes(), scratch, tape])
    masks = _mask_roots((tree_root, tree_label(tree_root)), (tape_p, "<tape>"), (scratch, "<scratch>"))
    mdig = F.field_digest(man, F.MANIFEST_SKIP)
    rdig = F.field_digest(_read_json(tape_p / "run_meta.json"), F.RUN_META_SKIP)
    src_files, src_stray = loaded_src_files(src_root)
    outside = mask_outside(rd["outside"], masks)
    print(json.dumps({
        "config": config,
        "kw": parse_kw(kw),
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
        # ---- 第346 検収 H1: 25 欄の外に足した比べるもの(fields.NEW_KEYS) ----
        "tape_files": F.tape_files(tape_p),
        "tape_sha256": F.tape_sha256(tape_p),
        "calls_schema": F.arrow_schema(calls.schema),
        "blocks_schema": F.arrow_schema(blocks.schema),
        "manifest_sha": mdig["sha"],
        "manifest_fields_sha": mdig["fields"],
        "manifest_scalars": mdig["scalars"],
        "manifest_skipped": mdig["skipped"],
        "run_meta_sha": rdig["sha"],
        "run_meta_fields_sha": rdig["fields"],
        "run_meta_scalars": rdig["scalars"],
        "run_meta_skipped": rdig["skipped"],
        "checkpoints": F.checkpoint_rows(res.checkpoints),
        # ---- 読んだもの(M1・M4) ----
        "src_files": src_files,
        "src_loaded_outside": src_stray,
        "tree_reads": rd["tree_reads"],
        "foreign_reads": rd["foreign"],
        "outside_reads": outside[:OUTSIDE_MAX],
        "outside_reads_n": len(outside),
        "outside_above_tree": mask_outside(rd["above"], masks),
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
         commit: str = "", extra_paths: Iterable[str] = (), nonce: str = "") -> int:
    """片側の構成を回して side の JSON を書く。戻り値=0(誤りなし)/ 2(ランの誤り・写しの木の不足・開いたファイルの問題)。

    ``extra_paths``: run の ``--extra-path``(写しの木へ足して写した追跡ファイル=開いても一覧に無いとは数えない・検収 M2)。
    ``nonce``: run がこのランの印として渡す値(JSON に書く=run が前のランの JSON と取り違えないように・検収 L5)。
    """
    try:
        kw_doc = parse_kw(kw)
        names = resolve_names(set_name, only)
    except (ValueError, KeyError) as e:
        print(f"誤り: {e}", file=sys.stderr)
        return EXIT_ERROR
    src_dir = Path(src).resolve() if str(src) else (REPO / "src").resolve()
    root = src_dir.parent
    is_worktree = src_dir == (REPO / "src").resolve()
    scratch_p = Path(scratch)
    extras = [e for e in extra_paths if e]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(src_dir)
    env["PYTHONHASHSEED"] = PYTHONHASHSEED
    env.update(C.set_env(set_name))
    missing = T.tree_missing(root)
    if missing and not allow_incomplete_tree:
        print("src の木に足りないもの(写しは run か git archive で・data はつなぎ):", *missing, sep="\n  ", file=sys.stderr)
        return EXIT_ERROR
    masks = _mask_roots((root, tree_label(root)), (scratch_p, "<scratch>"))

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
    # 読んだ src の digest は構成ごとに同じ道筋なら同じ値=side に 1 つにまとめ、行には数と全体のハッシュだけ残す
    src_files: dict[str, str] = {}
    conflict: set[str] = set()
    for r in got.values():
        if "src_files" not in r:
            continue
        files = r.pop("src_files") or {}
        for rel, h in files.items():
            if src_files.setdefault(rel, h) != h:
                conflict.add(rel)
        r["src_files_n"] = len(files)
        r["src_files_sha"] = F.sha16(files)
    reads = sorted({x for r in got.values() for x in r.get("tree_reads", [])})
    cls = T.classify_reads(reads, root, listed=[*T.TRACKED_READS, *extras])
    doc = {"tool": TOOL_ID, "label": label, "set": set_name, "configs": names, "kw": kw_doc,
           "src": "作業木" if is_worktree else "写し", "commit": commit, "nonce": nonce,
           "world": world, "agents": agents, "seed": seed, "pythonhashseed": PYTHONHASHSEED,
           "env": C.switch_env(env), "env_hidden": C.hidden_env_names(env), "extra_paths": extras,
           "tree_missing": missing, "tree_reads": reads, "tree_reads_unlisted": cls["unlisted"],
           "tree_reads_absent": cls["absent"],
           "foreign_reads": sorted({x for r in got.values() for x in r.get("foreign_reads", [])}),
           "outside_reads": sorted({x for r in got.values() for x in r.get("outside_reads", [])})[:OUTSIDE_MAX],
           "outside_above_tree": sorted({x for r in got.values() for x in r.get("outside_above_tree", [])}),
           "src_files": dict(sorted(src_files.items())), "src_files_conflict": sorted(conflict),
           "src_loaded_outside": sorted({x for r in got.values() for x in r.get("src_loaded_outside", [])}),
           "drop_behavior_item": drop_behavior_item, "multiset_items": multiset_items, "runs": got}
    Path(out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    errs = side_checks(doc)
    if errs:
        print("side の誤り:", *errs, sep="\n  ", file=sys.stderr)
        return EXIT_ERROR
    return 0


# ------------------------------------------------------------------ compare
#: side の JSON の欄 → 中身があれば誤りにする文(古い記録で欄が無いものは見ない)。
SIDE_ERROR_FIELDS: Final[tuple[tuple[str, str], ...]] = (
    ("tree_reads_unlisted", "写しの一覧に無い追跡ファイルを開いた"),
    ("tree_reads_absent", "写しの木に無いファイルを開こうとした"),
    ("foreign_reads", "写しの側が道具のリポのファイルを開いた"),
    ("outside_above_tree", "読む src の親の上の階の docs などを開いた(根を上へ辿る読み口が写しの木の外を読んだ)"),
    ("src_loaded_outside", "渡した src の外から shibuya のモジュールを読んだ"),
    ("src_files_conflict", "構成の間で同じ src のファイルの digest が違う"),
)


def side_checks(doc: dict[str, Any]) -> list[str]:
    """side の JSON の誤り(ランの誤り・読んだ src の違い・開いたファイルの問題)。古い記録で欄が無いものは見ない。"""
    out: list[str] = []
    for name, r in (doc.get("runs") or {}).items():
        if "error" in r:
            out.append(f"{name}: ランの誤り")
        if r.get("src_as_expected") is False:
            out.append(f"{name}: 渡した src と違う shibuya を読んだ")
    for k, msg in SIDE_ERROR_FIELDS:
        if doc.get(k):
            out.append(f"{msg}: {doc[k]}")
    return out


def condition_checks(a: dict[str, Any], b: dict[str, Any]) -> tuple[list[str], list[str]]:
    """2 つの side の条件(:data:`CONDITION_KEYS`)の違い(誤り)と、片側か両側の記録に無くて比べていない条件の名。"""
    bad: list[str] = []
    skipped: list[str] = []
    for k in CONDITION_KEYS:
        if k not in a or k not in b:
            skipped.append(k)
            continue
        va, vb = a[k], b[k]
        if k == "env_hidden":  # mock のランに効かない鍵は比べない(run も止めない側)
            va = [x for x in (va or []) if x not in STRAY_ENV_OK]
            vb = [x for x in (vb or []) if x not in STRAY_ENV_OK]
        if not F.same_value(va, vb):
            bad.append(f"条件が違う {k}: a={va!r}・b={vb!r}")
    return bad, skipped


def _num(r: dict[str, Any], k: str) -> float:
    v = r.get(k, 0)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else 0


def compare_row(ra: dict[str, Any], rb: dict[str, Any]) -> dict[str, Any]:
    """1 構成の比べ(25 欄と新しい欄=正準の JSON で同じか・新しい欄が片側か両側に無ければ ``not_compared``)。"""
    same: list[str] = []
    moved: dict[str, Any] = {}
    not_compared: list[str] = []
    for k in C.COMPARE_KEYS:
        if F.same_value(ra[k], rb[k]):
            same.append(k)
        else:
            moved[k] = {"a": ra[k], "b": rb[k]}
    for k in F.NEW_KEYS:
        if k not in ra or k not in rb:
            not_compared.append(k)
        elif F.same_value(ra[k], rb[k]):
            same.append(k)
        else:
            moved[k] = F.diff(ra[k], rb[k])
    row: dict[str, Any] = {"same": same, "moved": moved, "not_compared": not_compared,
                           "calls_delta": _num(rb, "calls") - _num(ra, "calls"),
                           "blocks_rows_delta": _num(rb, "blocks_rows") - _num(ra, "blocks_rows"),
                           "action_usage_delta": _num(rb, "action_usage_total") - _num(ra, "action_usage_total"),
                           "noticed_delta": _num(rb, "noticed") - _num(ra, "noticed")}
    for prefix in ("manifest", "run_meta"):
        if f"{prefix}_fields_sha" in moved or f"{prefix}_sha" in moved:
            row[f"{prefix}_moved"] = F.named_moves(ra, rb, prefix)
    return row


def compare_docs(a: dict[str, Any], b: dict[str, Any], note: str = "", *, strict: bool = False,
                 run_checks: Iterable[str] = ()) -> tuple[dict[str, Any], int]:
    """2 つの side を構成ごとに比べる(欄ごとに同じ/動いた・前後の値)。戻り値=(compare の JSON, 終了コード)。

    誤り(2): 構成が 0・どちらかの側にしか無い構成・ランの誤り・25 欄の欠け(片側でも両側でも)・条件の違い・side の誤り・
    ``run_checks``。``strict`` なら新しい欄や条件の欄が記録に無いことも誤り(run は strict)。
    """
    runs_a, runs_b = a.get("runs") or {}, b.get("runs") or {}
    rows: dict[str, Any] = {}
    for name in list(runs_a) + [n for n in runs_b if n not in runs_a]:
        ra, rb = runs_a.get(name), runs_b.get(name)
        if ra is None or rb is None:
            rows[name] = {"missing_in": "a" if ra is None else "b"}
            continue
        if "error" in ra or "error" in rb:
            rows[name] = {"error_a": str(ra.get("error", ""))[-500:], "error_b": str(rb.get("error", ""))[-500:]}
            continue
        lack = {s: [k for k in C.COMPARE_KEYS if k not in r] for s, r in (("a", ra), ("b", rb))}
        if lack["a"] or lack["b"]:
            rows[name] = {"lacking_keys": lack}
            continue
        rows[name] = compare_row(ra, rb)
    cond_bad, cond_skipped = condition_checks(a, b)
    not_compared: dict[str, int] = {}
    for r in rows.values():
        for k in r.get("not_compared", []):
            not_compared[k] = not_compared.get(k, 0) + 1
    checks: dict[str, list[str]] = {"a": side_checks(a), "b": side_checks(b), "conditions": cond_bad,
                                    "compare": [], "run": list(run_checks)}
    if not rows:
        checks["compare"].append("構成が 0(比べるものが無い)")
    if strict and not_compared:
        checks["compare"].append(f"新しい欄が記録に無い(比べていない): {sorted(not_compared)}")
    if strict and cond_skipped:
        checks["compare"].append(f"条件の欄が記録に無い(比べていない): {cond_skipped}")
    n_err = sum(1 for r in rows.values() if "moved" not in r)
    n_moved = sum(1 for r in rows.values() if r.get("moved"))
    n_same = sum(1 for r in rows.values() if "moved" in r and not r["moved"] and not r["not_compared"])
    n_partial = sum(1 for r in rows.values() if "moved" in r and not r["moved"] and r["not_compared"])
    code = EXIT_ERROR if (n_err or any(checks.values())) else EXIT_MOVED if n_moved else EXIT_SAME
    result = {EXIT_SAME: "同じ" if not n_partial else "比べた欄は同じ(古い記録で比べていない欄がある=1 バイトまでは確かめていない)",
              EXIT_MOVED: "動いた", EXIT_ERROR: "誤り"}[code]
    head = ("tool", "label", "set", "kw", "src", "commit", "world", "agents", "seed", "pythonhashseed", "env",
            "env_hidden", "extra_paths", "drop_behavior_item", "multiset_items")
    doc = {"a": {k: a.get(k) for k in head}, "b": {k: b.get(k) for k in head}, "note": note,
           "keys": [*C.COMPARE_KEYS, *F.NEW_KEYS], "keys_new": list(F.NEW_KEYS),
           "not_compared_fields": {"manifest": dict(F.MANIFEST_SKIP), "run_meta": dict(F.RUN_META_SKIP),
                                   "suffixes": list(F.SKIP_SUFFIXES), "suffix_exempt": dict(F.SUFFIX_EXEMPT),
                                   "tape_fieldwise": list(F.TAPE_FIELDWISE)},
           "summary": {"configs": len(rows), "all_same": n_same, "same_partial": n_partial, "moved": n_moved,
                       "errors": n_err,
                       "final_same": sum(1 for r in rows.values() if "moved" in r and "final" not in r["moved"]),
                       "not_compared": not_compared, "conditions_not_compared": cond_skipped,
                       "result": result, "exit_code": code},
           "checks": checks, "rows": rows}
    return doc, code


def _short(v: Any, n: int = 80) -> str:
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + "…"


def compare(*, a: str | Path, b: str | Path, out: str | Path, note: str = "", strict: bool = False,
            run_checks: Iterable[str] = ()) -> int:
    """side の JSON 2 本を比べて compare の JSON を書く。戻り値=0 同じ / 1 動いた欄がある / 2 誤り。"""
    da = json.loads(Path(a).read_text(encoding="utf-8"))
    db = json.loads(Path(b).read_text(encoding="utf-8"))
    doc, code = compare_docs(da, db, note, strict=strict, run_checks=run_checks)
    Path(out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    s = doc["summary"]
    print(f"{s['configs']} 構成・{len(doc['keys'])} 欄すべて同じ {s['all_same']}・一部の欄を比べていない {s['same_partial']}"
          f"・動いた {s['moved']}・誤り {s['errors']}・final が同じ {s['final_same']} → {s['result']}(終了コード {code})")
    if s["not_compared"]:
        print(f"  比べていない欄(片側か両側の記録に無い=構成の数): {s['not_compared']}")
    if s["conditions_not_compared"]:
        print(f"  比べていない条件(記録に無い): {s['conditions_not_compared']}")
    for name, r in doc["rows"].items():
        if "moved" not in r:
            print(" ", name, _short(r, 300))
            continue
        if not r["moved"]:
            continue
        print(" ", name, sorted(r["moved"]))
        for prefix in ("manifest", "run_meta"):
            if r.get(f"{prefix}_moved"):
                print(f"    {prefix} の動いた欄:",
                      "・".join(f"{k}: {_short(v['a'])} → {_short(v['b'])}" for k, v in r[f"{prefix}_moved"].items()))
        if "tape_sha256" in r["moved"]:
            print("    テープの動いたファイル:", sorted(r["moved"]["tape_sha256"].get("keys", {})))
        for k in ("calls_schema", "blocks_schema", "tape_files"):
            if k in r["moved"]:
                print(f"    {k}:", _short(r["moved"][k], 300))
        if "checkpoints" in r["moved"]:
            print("    動いた checkpoint(何番目):", sorted(r["moved"]["checkpoints"].get("items", {}), key=int))
    for k, items in doc["checks"].items():
        for c in items:
            print(f"  [{k}] {c}")
    return code


# ------------------------------------------------------------------ run
#: 呼び手の環境にあっても run を止めない変数(mock のランの結果に効かない=艦隊の鍵)。
STRAY_ENV_OK: tuple[str, ...] = ("SHIBUYA_FLEET_API_KEY",)


def stray_env(env: dict[str, str]) -> list[str]:
    """呼び手の環境に置かれた ``SHIBUYA_`` の変数の名(run は既定で止める=構成が黙って変わらないように)。"""
    return sorted(k for k in env if k.startswith("SHIBUYA_") and k not in STRAY_ENV_OK)


def worktree_commit(src: str | Path = "", extra_paths: Iterable[str] = ()) -> str:
    """比べる側が作業木の src なら、その HEAD の commit(src と、エンジンが読む追跡ファイル=``TRACKED_READS`` と
    ``extra_paths`` に未 commit の変更があれば ``+dirty``=検収 L9)。それ以外は ``""``。"""
    src_dir = Path(src).resolve() if str(src) else (REPO / "src").resolve()
    if src_dir != (REPO / "src").resolve():
        return ""
    try:
        head = T.resolve_commit(REPO, "HEAD")
    except ValueError:
        return ""
    st = T.git(REPO, "status", "--porcelain", "--", "src", *T.TRACKED_READS, *[e for e in extra_paths if e])
    return head + ("+dirty" if st.returncode == 0 and st.stdout.strip() else "")


def verify_sides(base_doc: dict[str, Any], work_doc: dict[str, Any], *, base_src: str | Path,
                 work_src: str | Path) -> list[str]:
    """run の確かめ(検収 M1): 基準の側が写しの src を読んだ・比べる側が渡した src を読んだ・両側の読んだ ``shibuya`` の
    ファイルの digest が、それぞれの src の今のファイルと同じ(基準の側=写しの木)。"""
    out: list[str] = []
    if base_doc.get("src") != "写し":
        out.append(f"基準の側が写しの src を読んでいない(src={base_doc.get('src')!r})")
    work_kind = "作業木" if Path(work_src).resolve() == (REPO / "src").resolve() else "写し"
    if work_doc.get("src") != work_kind:
        out.append(f"比べる側が渡した src を読んでいない(src={work_doc.get('src')!r}・渡したのは {work_kind})")
    for side_name, doc, sdir, where in (("a", base_doc, base_src, "写しの木"), ("b", work_doc, work_src, "比べる側の src")):
        files = doc.get("src_files") or {}
        if not files:
            out.append(f"[{side_name}] 読んだ src の digest が無い")
            continue
        disk = T.src_files_digest(sdir, files)
        bad = sorted(rel for rel, h in files.items() if disk.get(rel) != h)
        if bad:
            out.append(f"[{side_name}] 読んだ src のファイルが{where}と違う({len(bad)} 本): {bad[:10]}")
    return out


def run(*, work: str | Path, out_dir: str | Path, base: str = "HEAD", src: str | Path = "", set_name: str = "all19",
        only: str = "", jobs: int = 4, label: str = "work", kw: str = "", extra_paths: Iterable[str] = (),
        inherit_env: bool = False, note: str = "", world: str = "data/world/v2", agents: int = 5_000,
        seed: int = 1) -> int:
    """基準の commit と比べる側の src を 1 回で比べる。戻り値=0 同じ / 1 動いた欄がある / 2 誤り。

    ① 基準の commit の ``src`` と :data:`tree.TRACKED_READS`(+``extra_paths``)を ``work/tree`` へ git archive で写す
    ② ``work/tree/data`` を道具のリポの data へのつなぎにする ③ 基準の側と比べる側の side を回す ④ 両側の JSON が
    このランのものか・読んだ src が渡したものかを確かめる ⑤ compare(strict)を書く ⑥ つなぎだけを外す(中は消さない・
    写しの木とテープは ``work`` に残る)。
    """
    t_start = time.perf_counter()
    try:
        commit = T.resolve_commit(REPO, base)
        names = resolve_names(set_name, only)
        parse_kw(kw)
    except (ValueError, KeyError) as e:
        print(e, file=sys.stderr)
        return EXIT_ERROR
    stray = stray_env(dict(os.environ))
    if stray and not inherit_env:
        print("呼び手の環境に SHIBUYA_ の変数がある(構成が変わる=止めた。続けるなら --inherit-env):", stray, file=sys.stderr)
        return EXIT_ERROR
    work_p = Path(work)
    work_nc = os.path.normcase(os.path.abspath(str(work_p)))
    if _under(work_nc, os.path.normcase(os.path.abspath(str(REPO)))) or T.in_git_worktree(work_p):
        print("作業の置き場が git の作業木の中にある(写しの木の根を上へ辿る読み口が作業木の docs を読みうる=止めた。"
              "リポの外の短い道筋にすること)", file=sys.stderr)
        return EXIT_ERROR
    if work_p.exists() and any(work_p.iterdir()):
        print("作業の置き場が空でない(前のランの残り=消すなら単独のコマンドで・つなぎが残っていないか先に確かめる)",
              file=sys.stderr)
        return EXIT_ERROR
    data_target = DATA_DIR
    if not data_target.is_dir():
        print("道具のリポに data が無い(つなぎの先)", file=sys.stderr)
        return EXIT_ERROR
    out_p = Path(out_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    tree_root = work_p / "tree"
    tapes = work_p / "tapes"
    extras = [e for e in extra_paths if e]
    paths = T.archive_paths(extras)
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
    nonce = uuid.uuid4().hex
    common = dict(set_name=set_name, only=",".join(names), jobs=jobs, kw=kw, world=world, agents=agents, seed=seed,
                  extra_paths=extras, nonce=nonce)
    base_src = tree_root / "src"
    work_src = Path(src).resolve() if str(src) else (REPO / "src").resolve()
    link_ok = False
    codes: list[int] = []
    try:
        t0 = time.perf_counter()
        codes.append(side(label=f"base_{short}", scratch=tapes, out=base_json, src=base_src, commit=commit, **common))
        t1 = time.perf_counter()
        codes.append(side(label=label, scratch=tapes, out=work_json, src=src, commit=worktree_commit(src, extras),
                          **common))
        t2 = time.perf_counter()
        print(f"壁時計: 基準の側 {t1 - t0:.0f} 秒・比べる側 {t2 - t1:.0f} 秒", flush=True)
    finally:
        try:
            T.remove_link(link)
            link_ok = True
            print("つなぎを外した(中は消していない)", flush=True)
        except Exception as e:  # noqa: BLE001 - 外せなかったことを必ず知らせる
            print(f"!! つなぎを外せなかった: {e}\n   os.rmdir(Windows)か cmd /c rmdir で、つなぎの道筋だけを外すこと"
                  "(中を消すコマンドを使わない)", file=sys.stderr)
    if not (base_json.is_file() and work_json.is_file()):
        print("side の JSON が書かれていない", file=sys.stderr)
        return EXIT_ERROR
    base_doc = json.loads(base_json.read_text(encoding="utf-8"))
    work_doc = json.loads(work_json.read_text(encoding="utf-8"))
    stale = [p.name for p, d in ((base_json, base_doc), (work_json, work_doc)) if d.get("nonce") != nonce]
    if stale:  # 検収 L5: side が JSON を書く前に戻った=置き場にあるのは前のランの JSON
        print(f"side の JSON がこのランのものでない(前のランの残り): {stale}。compare は書かない", file=sys.stderr)
        return EXIT_ERROR
    run_checks = verify_sides(base_doc, work_doc, base_src=base_src, work_src=work_src)
    if EXIT_ERROR in codes:
        run_checks.append(f"side が誤りで終わった(終了コード: 基準の側 {codes[0]}・比べる側 {codes[-1]})")
    code = compare(a=base_json, b=work_json, out=cmp_json, strict=True, run_checks=run_checks,
                   note=note or f"tools/bytecheck run: 基準 {short} の写し vs {label}・組 {set_name}")
    print(f"全体の壁時計 {time.perf_counter() - t_start:.0f} 秒", flush=True)
    if not link_ok or EXIT_ERROR in codes:
        return EXIT_ERROR
    return code
