"""日境界の再開と複数日の通しラン(10d・D-102 Q3・Q5・A10・A11)の状態の書き出しと読み込み。

- **書くもの**(1 つのまとまり=1 ファイル): SoA の全列のうち状態台帳の軸 2 が ``discardable`` でない列
  (``required``・``derivable``・``unknown``=full-hash と同じ範囲)、SoA の外の状態(台帳の ``full_items`` の
  道筋の値・宣言順)、進捗の印(次に回す通しの時刻 T・締めた日の数)、出したが返っていない艦隊の呼。
  見出し(``header``)に形式の版・台帳の版・設定の指紋・ラン ID・親のラン・``finished``・書いた時点の
  behavior-hash と full-hash を入れる。
- **書き方**: 先頭の 1 行(印・形式の版・ラン ID・中身の sha256)+ pickle の中身。同じディレクトリの一時ファイルに
  書いて ``fsync`` してから ``os.replace``(途中で落ちても壊れたファイルを読まない)。見出しの写しを同じ名前の
  ``.json`` に置く。読み込みは先頭の行と写しを pickle を開く前に検査する(自分が書いたものだけを読む)。
  形式の見直し(npz+json)は 10f の項。
- **直列化**: ``pickle``(プロトコル 5)。1 回の ``dump`` で全部を書くので、値どうしの同一性(会話の
  ``sessions`` と ``_of_agent`` が同じ ``Session`` を指す など)が保たれる。自分で書いたファイルだけを読む
  前提(``pickle`` は外から来たファイルを読んではいけない)。**未リサーチ(expedient)**。
- **戻し方**: ``engine.resolve.restore_soa`` と ``restore_items``(書き手は resolve=単一書き手の規律)。

設定の指紋(``fingerprint``)は ``run_day`` の引数のうち挙動に効くもの(観測だけの欄・出力先・日数・状態の
口を除く)を JSON にできる形にしたもの。再開ではこれが親と同じでなければ止める。
"""

from __future__ import annotations

import dataclasses
import json
import os
import pickle
import platform
import sys
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping

import numpy as np

from shibuya.core.hashing import blake3_hex
from shibuya.engine import state_ledger as SL
from shibuya.engine.state_hashes import _ABSENT, resolve_item

#: 状態のファイルの形式の版(中身の組み立てを変えたら上げる)。
STATE_FORMAT: Final[str] = "shibuya.engine.resume/state/v1"
#: 状態のファイルの名前(``state_out`` のディレクトリの中・通しの時刻 T で並ぶ)。
STATE_NAME: Final[str] = "state-T{T:08d}.pkl"
#: 「腕が立っていない(持ち主が ``None``)」の印(``_ABSENT`` は pickle できないので文字列で持つ)。
ABSENT_MARK: Final[str] = "<shibuya.resume.absent>"

#: 指紋に入れない ``run_day`` の引数(観測だけ・出力先・日数・状態の口・注入する物そのもの)。
FINGERPRINT_SKIP: Final[frozenset[str]] = frozenset({
    "checkpoint_every", "tape_path", "census_out", "occupancy_every", "occupancy_path", "fleet_debug_dir",
    "sim_days", "state_out", "stop_at_tick", "resume_from", "run_id", "checkpoint_detail",
    # 注入する物(下の ``_describe_objects`` で同定だけを入れる)
    "llm", "fleet", "world", "renderer", "replay", "ledger", "population",
})


def _canon(v: Any) -> Any:
    """JSON にできる正準の形(辞書は鍵を文字列にして昇順)。"""
    if v is None or isinstance(v, (bool, str)):
        return v
    if isinstance(v, Enum):
        return _canon(v.value)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Path):
        return v.as_posix()
    if isinstance(v, Mapping):
        return {str(k): _canon(x) for k, x in sorted(v.items(), key=lambda kv: str(kv[0]))}
    if isinstance(v, (list, tuple)):
        return [_canon(x) for x in v]
    if isinstance(v, np.ndarray):
        return _canon(v.tolist())
    return f"<{type(v).__module__}.{type(v).__qualname__}>"


#: 指紋で「パスの文字列」ではなく中身で同定する引数(10d 検収 L3)。
PATH_ARGS: Final[frozenset[str]] = frozenset({"world_dir", "holiday_csv"})


def path_identity(path: Any) -> str | None:
    """パス → 中身の同定(置き場所・書き方・OS に依らない)。ファイルは sha256、ディレクトリは
    ``build_manifest.json`` の sha256(無ければ直下のファイルの名前と大きさの一覧の sha256)。無ければ ``missing``。"""
    import hashlib

    if path is None or str(path) == "":
        return None
    p = Path(path)
    if not p.is_absolute() and not p.exists():
        from shibuya.engine.calendar import resolve_repo_path

        p = Path(resolve_repo_path(str(path)))
    if p.is_file():
        return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    if p.is_dir():
        man = p / "build_manifest.json"
        if man.is_file():
            return "manifest-sha256:" + hashlib.sha256(man.read_bytes()).hexdigest()
        names = sorted(f"{q.name}:{q.stat().st_size}" for q in p.iterdir() if q.is_file())
        return "listing-sha256:" + hashlib.sha256("\n".join(names).encode("utf-8")).hexdigest()
    return "missing"


def _describe_objects(args: Mapping[str, Any]) -> dict[str, Any]:
    """注入する物の同定(中身ではなく「何が入ったか」・パスの文字列は入れない)。"""
    world = args.get("world")
    renderer = args.get("renderer")
    population = args.get("population")
    return {
        "world": (None if world is None else {"n_cells": int(world.n_cells), "n_poi": int(world.n_poi)}),
        "renderer": renderer if (renderer is None or isinstance(renderer, str)) else _canon(renderer),
        "llm": None if args.get("llm") is None else _canon(args.get("llm")),
        "fleet": args.get("fleet") is not None,
        "replay": args.get("replay") is not None,
        "ledger": args.get("ledger") is not None,
        "population": (population if (population is None or isinstance(population, bool)) else "<Population>"),
    }


def fingerprint(args: Mapping[str, Any]) -> dict[str, Any]:
    """``run_day`` の引数から設定の指紋を作る(再開で親と同じでなければ止める)。"""
    out = {k: (path_identity(v) if k in PATH_ARGS else _canon(v))
           for k, v in sorted(args.items()) if k not in FINGERPRINT_SKIP}
    out["objects"] = _describe_objects(args)
    return out


def fingerprint_diff(a: Mapping[str, Any], b: Mapping[str, Any]) -> list[str]:
    """2 つの指紋で値の違う鍵(昇順)。"""
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def run_id_of(fp: Mapping[str, Any], *, start_T: int, parent: str = "") -> str:
    """ラン ID(実行ごとに一意・10d 検収 L6)。指紋・始めの T・親のラン ID に、実行の時刻とプロセス番号の印を混ぜる。

    再開の鎖は ``parent_run`` の (親のラン ID・再開の T・保存の full-hash) の組で引く(ラン ID だけに頼らない)。
    """
    import time

    nonce = f"{time.time_ns()}:{os.getpid()}"
    body = json.dumps({"fp": fp, "start_T": int(start_T), "parent": parent, "nonce": nonce},
                      ensure_ascii=False, sort_keys=True)
    return "run-" + blake3_hex(body.encode("utf-8"))[:16]


def platform_fields() -> dict[str, Any]:
    """同じ環境かを見るための欄(決定論の方針: 同じ環境・同じ設定で同じ結果)。"""
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "os": platform.system(),
        "machine": platform.machine(),
        "numba_threads": os.environ.get("NUMBA_NUM_THREADS", ""),
    }


# ---------------------------------------------------------------- 集め方
def collect_soa(agents: Any, world: Any, pstate: Any) -> dict[str, dict[str, np.ndarray]]:
    """SoA の列のうち軸 2 が ``discardable`` でない列の写し(置き場 → 列名 → 配列)。宣言順。"""
    out: dict[str, dict[str, np.ndarray]] = {}
    for place, reg in (("agents", agents.registry), ("cells", world.cells), ("pois", world.pois),
                       ("perception", None if pstate is None else pstate.registry)):
        if reg is None:
            continue
        skip = SL.full_excluded(place)
        out[place] = {name: np.array(arr, copy=True) for name, arr in reg.arrays.items() if name not in skip}
    return out


def collect_items(owners: Mapping[str, Any]) -> dict[str, Any]:
    """外の状態の値(台帳の ``full_items`` の道筋 → 値・宣言順)。持ち主が無い道筋は ``ABSENT_MARK``。"""
    out: dict[str, Any] = {}
    for path in [p for _k, p in SL.full_items()]:
        v = resolve_item(owners, path)
        out[path] = ABSENT_MARK if v is _ABSENT else v
    return out


@dataclasses.dataclass
class StateBundle:
    """状態のまとまり 1 つ(見出し・SoA・外の状態・艦隊の未着の呼)。"""

    header: dict[str, Any]
    soa: dict[str, dict[str, np.ndarray]]
    items: dict[str, Any]
    inflight: list[Any]


def state_path(state_out: str | Path, T: int) -> Path:
    return Path(state_out) / STATE_NAME.format(T=int(T))


def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fp:
        fp.write(data)
        fp.flush()
        os.fsync(fp.fileno())
    os.replace(tmp, path)


#: ファイルの先頭の 1 行の印(``MAGIC 形式の版 ラン ID 中身の sha256 中身のバイト数``)。
MAGIC: Final[bytes] = b"SHIBUYA-STATE"


def write_state(path: str | Path, bundle: StateBundle) -> int:
    """状態のまとまりを 1 ファイルに書く(一時ファイル → ``os.replace``)。返り値=ファイルのバイト数。

    形: 先頭の 1 行(印・形式の版・ラン ID・中身の sha256・中身のバイト数)+ pickle の中身。見出しの写しを同じ名前の
    ``.json`` に書く(読み込みはこの 2 つが食い違えば止める=自分が書いたものだけを読む)。
    """
    import hashlib

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = pickle.dumps(
        {"header": bundle.header, "soa": bundle.soa, "items": bundle.items, "inflight": bundle.inflight},
        protocol=5,
    )
    run_id = str(bundle.header.get("run_id", ""))
    if not run_id or any(c.isspace() for c in run_id):
        raise ValueError(f"ラン ID が空か空白を含む: {run_id!r}")
    head = b" ".join([MAGIC, STATE_FORMAT.encode("ascii"), run_id.encode("utf-8"),
                      hashlib.sha256(payload).hexdigest().encode("ascii"), str(len(payload)).encode("ascii")]) + b"\n"
    side = json.dumps(bundle.header, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    _atomic_write(p.with_suffix(".json"), side.encode("utf-8"))
    _atomic_write(p, head + payload)
    return len(head) + len(payload)


def read_state(path: str | Path) -> StateBundle:
    """状態のまとまりを読む。**自分が書いたものだけ**を読む検査を pickle を開く前に通す。

    1. 先頭の行の印と形式の版が今と同じ。2. 中身のバイト数と sha256 が先頭の行と同じ(壊れた・差し替えられた中身を開かない)。
    3. 見出しの写し(``.json``)があり、ラン ID が先頭の行と同じ。開いた後: 4. 見出しのラン ID・full-hash が写しと同じ。
    5. 状態台帳の版が今と同じ。
    """
    import hashlib

    p = Path(path)
    data = p.read_bytes()
    nl = data.find(b"\n")
    parts = data[:nl].split(b" ") if nl > 0 else []
    if len(parts) != 5 or parts[0] != MAGIC:
        raise ValueError(f"状態のファイルの形が違う(先頭の行に印が無い): {p.name}")
    if parts[1].decode("ascii", "replace") != STATE_FORMAT:
        raise ValueError(f"状態のファイルの形式の版が違う: {parts[1]!r}(今は {STATE_FORMAT!r})")
    run_id = parts[2].decode("utf-8", "replace")
    payload = data[nl + 1:]
    if str(len(payload)).encode("ascii") != parts[4] or hashlib.sha256(payload).hexdigest().encode("ascii") != parts[3]:
        raise ValueError(f"状態のファイルの中身が先頭の行の sha256 と合わない(壊れたか差し替えられた): {p.name}")
    side_path = p.with_suffix(".json")
    if not side_path.exists():
        raise ValueError(f"見出しの写し({side_path.name})が無い状態のファイルは読まない")
    side = json.loads(side_path.read_text(encoding="utf-8"))
    if str(side.get("run_id", "")) != run_id:
        raise ValueError(f"見出しの写しのラン ID が状態のファイルと違う({side.get('run_id')!r} != {run_id!r})")
    doc = pickle.loads(payload)  # 自分で書いたファイルだけ(上の検査を通ったもの)を開く
    if not isinstance(doc, dict) or "header" not in doc:
        raise ValueError(f"状態のファイルの形が違う: {p.name}")
    h = doc["header"]
    if h.get("format") != STATE_FORMAT:
        raise ValueError(f"状態のファイルの形式の版が違う: {h.get('format')!r}(今は {STATE_FORMAT!r})")
    if str(h.get("run_id", "")) != run_id or h.get("hashes") != side.get("hashes"):
        raise ValueError("状態のファイルの見出しが写し(.json)と違う(ラン ID か full-hash)")
    if h.get("ledger_version") != SL.LEDGER_VERSION:
        raise ValueError(
            f"状態台帳の版が違う: ファイルは {h.get('ledger_version')!r}・今は {SL.LEDGER_VERSION!r}"
            "(状態の範囲が変わったので読めない)"
        )
    return StateBundle(header=h, soa=doc["soa"], items=doc["items"], inflight=list(doc.get("inflight", [])))
