"""日境界の再開と複数日の通しラン(10d・D-102 Q3・Q5・A10・A11)の状態の書き出しと読み込み。

- **書くもの**(1 つのまとまり=1 ファイル): SoA の全列のうち状態台帳の軸 2 が ``discardable`` でない列
  (``required``・``derivable``・``unknown``=full-hash と同じ範囲)、SoA の外の状態(台帳の ``full_items`` の
  道筋の値・宣言順)、進捗の印(次に回す通しの時刻 T・締めた日の数)、出したが返っていない艦隊の呼。
  見出し(``header``)に形式の版・台帳の版・設定の指紋・ラン ID・親のラン・``finished``・書いた時点の
  behavior-hash と full-hash を入れる。
- **書き方**(10f・K23 (a)): npz+json(``engine.state_codec``・圧縮)の 1 ファイル ``state-T<T>.npz``。同じディレクトリの
  一時ファイルに書いて ``fsync`` してから ``os.replace``(途中で落ちても壊れたファイルを読まない)。見出しの写しを
  同じ名前の ``.json`` に置き、写しの ``file`` にファイルの sha256 とバイト数を書く(壊れたファイル・取り違えを止める)。
- **読み**: npz+json は ``np.load(allow_pickle=False)`` と許可したクラスの表(``state_codec.ALLOWED_CLASSES``)だけで
  組み立てる=外から来たファイルでも、読むだけでコードは動かない。読んだ値の形・dtype・鍵を台帳の宣言と突き合わせる
  (``check_bundle``)。再開では戻す前に今の値の型とも突き合わせる(``check_item_kinds``)。同じオブジェクトを 2 か所
  から指す値(凍結した ``Target``・金の台帳の配列)は 1 つのまま戻る(印 ``__r``・``__nd``)。
- **旧の形式**(10d の pickle・``state-T<T>.pkl``): 10e まで読める口を残す。ただし **明示の切替口**
  (``read_state(..., allow_legacy_pickle=True)``・``run_day(resume_legacy_pickle=True)``・CLI の
  ``--resume-legacy-pickle``)と**拡張子 ``.pkl``** がそろったときだけ pickle を開く(``LegacyStateFormatWarning`` を
  出す)。それ以外で中身が pickle なら、開かずに ``StateFormatError`` で止める(10f 第 3 段の検収 U1: 中身の先頭の
  バイトで自動で選ぶと、外から来たファイルでコードが動いた)。pickle は開いた時点で任意のコードが動きうるので、
  切替口を付けるのは**自分が書いたファイルに限る**(先頭の行の sha256 と写しの検査は壊れたファイルと取り違えを
  止めるだけで、出どころの証明にはならない)。
  〔訂正(10f)〕10d の版の「``sessions`` と ``_of_agent`` が同じ ``Session`` を指す」は今のコードでは当たらない。
  ``_of_agent`` は体 → 会話の番号の**整数**の辞書(``engine/conversation.py`` の ``ConversationManager``)で、
  ``Session`` を指さない。同じオブジェクトを 2 か所から指すのは、日の境目の保存では ``run_day.pending`` の中の
  凍結した ``Target``(12 か所から 1 つ)と、金の台帳の ``_last_close.flow`` と ``_flow_daily[0]`` の配列の 2 つ
  (10f の材料 §5-2 の計測)。
- **環境の欄**(10f): 見出しの ``platform`` に ``environment_fields()`` の全体、``env_id`` に同じ ID を書く
  (manifest とテープの ``run_meta.json`` と同じ値)。
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
from shibuya.engine import state_codec as SC
from shibuya.engine.state_codec import StateFormatError  # noqa: F401 - 読み口の拒否の型(再輸出)
from shibuya.engine.state_hashes import _ABSENT, resolve_item

#: 状態のファイルの形式の版(中身の組み立てを変えたら上げる)。10f: v2 = npz+json(``engine.state_codec``)。
STATE_FORMAT: Final[str] = "shibuya.engine.resume/state/v2"
#: 10d の pickle の形式の版(10e まで読むだけ・``LegacyStateFormatWarning``)。
STATE_FORMAT_PICKLE: Final[str] = "shibuya.engine.resume/state/v1"
#: 状態のファイルの名前(``state_out`` のディレクトリの中・通しの時刻 T で並ぶ)。
STATE_NAME: Final[str] = "state-T{T:08d}.npz"
#: 10d の pickle のファイルの名前(読むだけ)。
STATE_NAME_PICKLE: Final[str] = "state-T{T:08d}.pkl"
#: 「腕が立っていない(持ち主が ``None``)」の印(``_ABSENT`` は pickle できないので文字列で持つ)。
ABSENT_MARK: Final[str] = "<shibuya.resume.absent>"

#: 指紋に入れない ``run_day`` の引数(観測だけ・出力先・日数・状態の口・注入する物そのもの)。
FINGERPRINT_SKIP: Final[frozenset[str]] = frozenset({
    "checkpoint_every", "tape_path", "census_out", "occupancy_every", "occupancy_path", "fleet_debug_dir",
    "sim_days", "state_out", "stop_at_tick", "resume_from", "resume_legacy_pickle", "run_id", "checkpoint_detail",
    # 注入する物(下の ``_describe_objects`` で同定だけを入れる)
    "llm", "fleet", "world", "renderer", "replay", "ledger", "population",
})


def _canon(v: Any) -> Any:
    """JSON にできる正準の形(辞書は鍵を文字列にして昇順)。"""
    if isinstance(v, Enum):  # 10f: str の子の Enum(BudgetMode)も値にする(見出しを素の JSON に保つ)
        return _canon(v.value)
    if v is None or isinstance(v, (bool, str)):
        return v
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


#: 環境の欄の形式の版(欄の組み立てを変えたら上げる・10f)。
ENV_SCHEMA: Final[str] = "shibuya.engine.resume/environment/v1"
#: 版を記録する依存(``importlib.metadata`` の配布名)。無ければ空の値。
ENV_PACKAGES: Final[tuple[str, ...]] = ("numpy", "numba", "llvmlite", "blake3")


def _dist_version(name: str) -> str:
    from importlib import metadata

    try:
        return str(metadata.version(name))
    except Exception:  # noqa: BLE001 - 入っていない配布は空の値(欄は残す)
        return ""


def _numpy_simd() -> dict[str, list[str]]:
    """numpy の命令セット(基線と実行時の振り分けで見つかったもの)。取れなければ空の list。"""
    try:
        simd = np.show_config(mode="dicts").get("SIMD Extensions", {})  # type: ignore[union-attr]
        return {"baseline": [str(x) for x in simd.get("baseline", [])],
                "found": [str(x) for x in simd.get("found", [])],
                "not_found": [str(x) for x in simd.get("not found", [])]}
    except Exception:  # noqa: BLE001
        return {"baseline": [], "found": [], "not_found": []}


def _deps_list() -> list[str]:
    """入っている配布の「名前==版」(名前は小文字・``_`` を ``-`` に揃える・昇順・重複なし)。``pip freeze`` 相当
    (``pip`` のサブプロセスは呼ばない)。"""
    from importlib import metadata

    lines: set[str] = set()
    for d in metadata.distributions():
        name = str(d.metadata.get("Name") or "").strip().lower().replace("_", "-")
        if name:
            lines.add(f"{name}=={d.version}")
    return sorted(lines)


def _deps_digest(lines: list[str] | None = None) -> tuple[str, int]:
    """依存の一覧(``_deps_list``)の sha256(行を改行でつなぎ末尾にも改行)と行数。"""
    import hashlib

    lines = _deps_list() if lines is None else lines
    body = "\n".join(lines) + "\n"
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(), len(lines)


def _numba_threads() -> int | None:
    """numba の実際のスレッド数(``numba.config.NUMBA_NUM_THREADS``)。numba が無ければ ``None``。"""
    try:
        import numba  # noqa: PLC0415 - 版を見るだけ(スレッドの層は起動しない)

        return int(numba.config.NUMBA_NUM_THREADS)
    except Exception:  # noqa: BLE001
        return None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _git(root: Path, *args: str, timeout: float = 30) -> Any:
    import subprocess

    return subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args], capture_output=True, timeout=timeout)


def _git_state() -> dict[str, Any]:
    """git の commit・dirty・差分の sha256(10f 検収 N6・N7)。

    - ``git rev-parse --show-toplevel`` がこのパッケージの根と同じときだけ値を入れる(``git archive`` の写しが
      別のリポの中にあっても、外のリポの commit を拾わない)。
    - ``git_dirty``: **追跡しているファイル**に未コミットの変更があるか(``--untracked-files=no``。未追跡の文書では
      true にならない)。
    - ``git_diff_sha256``: dirty のとき ``git diff HEAD --binary`` の出力の sha256(同じ commit の上の別の変更を
      区別する)。clean なら ``""``。未追跡のファイルは入らない。
    - 必須でないロックを取らない(``--no-optional-locks``=並べて動く ``git add``・``commit`` とぶつからない)。

    git が無い・リポの外・根が違うときは空の値(``""``・``None``)。
    """
    import hashlib

    root = _repo_root()
    out: dict[str, Any] = {"git_commit": "", "git_dirty": None, "git_diff_sha256": ""}
    try:
        top = _git(root, "rev-parse", "--show-toplevel", timeout=10)
        if top.returncode != 0:
            return out
        if Path(top.stdout.decode("utf-8", "replace").strip()).resolve() != root.resolve():
            return out
        r = _git(root, "rev-parse", "HEAD", timeout=10)
        if r.returncode != 0:
            return out
        out["git_commit"] = r.stdout.decode("ascii", "replace").strip()
        st = _git(root, "status", "--porcelain", "--untracked-files=no")
        if st.returncode == 0:
            out["git_dirty"] = bool(st.stdout.strip())
            if out["git_dirty"]:
                d = _git(root, "diff", "HEAD", "--binary")
                if d.returncode == 0:
                    out["git_diff_sha256"] = "sha256:" + hashlib.sha256(d.stdout).hexdigest()
    except Exception:  # noqa: BLE001 - git が無い
        pass
    return out


def _git_stamp() -> tuple[int, ...] | None:
    """git の index・HEAD・今の枝の ref の更新時刻(コミットや ``git add`` で変わる)。``.git`` が無ければ ``None``。"""
    g = _repo_root() / ".git"
    if not g.is_dir():
        return None
    files = [g / "index", g / "HEAD"]
    try:
        head = (g / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            files.append(g / head[5:])
        return tuple(f.stat().st_mtime_ns if f.exists() else -1 for f in files)
    except OSError:
        return None


_CODE_CACHE: dict[str, Any] = {}


def _code_fields() -> dict[str, Any]:
    """``code`` の欄。git の index・HEAD・ref の更新時刻が前と同じなら前の値を使う(10f 検収 N9: 長く動くプロセスで
    コミットした後のランが古い commit を書かない)。索引に載せていない作業木の編集だけでは取り直さない(宣言)。"""
    stamp = _git_stamp()
    if stamp is not None and _CODE_CACHE.get("stamp") == stamp:
        return dict(_CODE_CACHE["code"])
    code = _git_state()
    _CODE_CACHE.clear()
    _CODE_CACHE.update({"stamp": stamp, "code": dict(code)})
    return code


def canonical_json(v: Any) -> str:
    """正準の JSON(鍵を昇順・区切りを ``,`` ``:`` に固定・ASCII 以外もそのまま)。"""
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _id_of(v: Any) -> str:
    return blake3_hex(canonical_json(v).encode("utf-8"))[:16]


_ENV_CACHE: dict[str, Any] = {}
#: ``platform_id`` に入れる欄(結果のビットに効きうるもの・10f 検収 N2)。依存の一覧(``deps``・``deps_sha256``・
#: ``deps_count``)は記録には残すが鍵に入れない(pytest などビットに効かない配布の版で golden の行が外れないように)。
PLATFORM_ID_KEYS: Final[tuple[str, ...]] = (
    "python", "python_implementation", "numpy", "numba", "llvmlite", "blake3", "os", "os_release", "os_version",
    "machine", "cpu", "numpy_simd",
)


def environment_fields(*, refresh: bool = False) -> dict[str, Any]:
    """環境の欄(10f・K26 (a))。``platform``・``runtime`` はプロセスごとに 1 回だけ集める(``refresh=True`` で
    集め直す)。``code`` は git の更新時刻が変わったら取り直す。

    - ``platform``: Python・numpy・numba・llvmlite・blake3 の版・OS と版・machine・CPU の型と numpy の命令セット・
      依存の一覧(``deps``=「名前==版」の昇順の list・``deps_sha256``・``deps_count``)。
    - ``runtime``: numba の既定のスレッド数(``numba.config.NUMBA_NUM_THREADS``。途中の ``set_num_threads`` は
      映らない)と環境変数 ``NUMBA_NUM_THREADS``(今のエンジンは並列の経路を持たない)。
    - ``code``: git の commit・dirty(追跡しているファイルだけ)・差分の sha256。
    - ``env_id``: 上の 3 つ(と ``schema``)の正準の JSON の blake3 の頭 16 桁(manifest・状態の見出し・
      ``run_meta.json`` に同じ値)。
    - ``platform_id``: ``platform`` のうち ``PLATFORM_ID_KEYS`` だけの同じ形の ID(golden の行の鍵。commit・dirty・
      スレッド数・依存の一覧を含めない)。

    取れない欄は空の値(``""``・``None``・空の list)にし、欄は残す。返すのは毎回新しい写し。
    """
    if refresh or not _ENV_CACHE:
        deps = _deps_list()
        deps_sha, deps_n = _deps_digest(deps)
        plat = {
            "python": sys.version.split()[0],
            "python_implementation": platform.python_implementation(),
            **{p: (np.__version__ if p == "numpy" else _dist_version(p)) for p in ENV_PACKAGES},
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "machine": platform.machine(),
            "cpu": platform.processor(),
            "numpy_simd": _numpy_simd(),
            "deps": deps,
            "deps_sha256": deps_sha,
            "deps_count": deps_n,
        }
        runtime = {"numba_threads": _numba_threads(),
                   "numba_threads_env": os.environ.get("NUMBA_NUM_THREADS", "")}
        _ENV_CACHE.clear()
        _ENV_CACHE.update({"platform": plat, "runtime": runtime})
        if refresh:
            _CODE_CACHE.clear()
    plat = json.loads(json.dumps(_ENV_CACHE["platform"]))
    runtime = dict(_ENV_CACHE["runtime"])
    body = {"schema": ENV_SCHEMA, "platform": plat, "runtime": runtime, "code": _code_fields()}
    env = json.loads(json.dumps(body))
    env["platform_id"] = _id_of({k: plat.get(k) for k in PLATFORM_ID_KEYS})
    env["env_id"] = _id_of(body)
    return env


class EnvironmentMismatchWarning(UserWarning):
    """再開・再生の元(状態のファイル・テープ)を書いた環境の ``platform_id`` が今の環境と違う(10f・§8 の 6)。

    決定論の約束は同じ環境の中だけなので知らせる。挙動は変えない(止めない)。"""


def warn_if_other_environment(recorded: Any, source: str) -> bool:
    """記録の環境の欄(``platform_id`` を持つ辞書)が今の環境と違えば警告を 1 行出す。返り値=警告したか。

    記録に ``platform_id`` が無い(10f より前の状態のファイル・テープ)ときは何もしない。
    """
    if not isinstance(recorded, Mapping):
        return False
    rec = str(recorded.get("platform_id", "") or "")
    if not rec:
        return False
    now = str(environment_fields()["platform_id"])
    if rec == now:
        return False
    import warnings

    warnings.warn(EnvironmentMismatchWarning(
        f"{source} を書いた環境は platform_id={rec}・今は {now}(決定論の約束は同じ環境の中だけ。続けて回す)"),
        stacklevel=3)
    return True


def platform_fields() -> dict[str, Any]:
    """同じ環境かを見るための欄(決定論の方針: 同じ環境・同じ設定で同じ結果)。10f で ``environment_fields`` に広げた。"""
    return environment_fields()


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



class LegacyStateFormatWarning(UserWarning):
    """10d の pickle の状態のファイルを読んだ(10e まで残す読み口・10f の K23 (a))。"""


#: pickle(プロトコル 2 以上)の最初のバイト(この中身は開かない=U1)。
PICKLE_PROTO: Final[bytes] = bytes([0x80])
#: 10d の pickle のファイルの先頭の 1 行の印(``MAGIC 形式の版 ラン ID 中身の sha256 中身のバイト数``)。
MAGIC: Final[bytes] = b"SHIBUYA-STATE"


def _bundle_doc(bundle: StateBundle) -> dict[str, Any]:
    return {"header": bundle.header, "soa": bundle.soa, "items": bundle.items, "inflight": bundle.inflight}


def write_state(path: str | Path, bundle: StateBundle) -> int:
    """状態のまとまりを 1 ファイル(npz+json・圧縮)に書く(一時ファイル → ``os.replace``)。返り値=ファイルのバイト数。

    見出しの写しを同じ名前の ``.json`` に書き、写しの ``file`` にファイルの形式の版・sha256・バイト数を入れる。
    """
    import hashlib


    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    run_id = str(bundle.header.get("run_id", ""))
    if not run_id or any(c.isspace() for c in run_id):
        raise ValueError(f"ラン ID が空か空白を含む: {run_id!r}")
    # 見出しは素の JSON に限る(写しの .json と同じ値・読むときに許可の表が要らない)
    header = json.loads(json.dumps(bundle.header, ensure_ascii=False, allow_nan=False))
    header["format"] = STATE_FORMAT  # 旧の形式から読んだまとまりを書き直すときも今の形式の版
    doc = _bundle_doc(bundle)
    doc["header"] = header
    data = SC.dumps(doc)
    side_doc = dict(header)
    side_doc["file"] = {"format": STATE_FORMAT, "codec": SC.CODEC,
                        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    side = json.dumps(side_doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    _atomic_write(p.with_suffix(".json"), side.encode("utf-8"))
    _atomic_write(p, data)
    return len(data)


def write_state_pickle(path: str | Path, bundle: StateBundle) -> int:
    """10d の pickle の形式で書く(**試験だけ**=旧の形式の読み口の試験の材料。10e で読み口と一緒に消す)。"""
    import hashlib

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    header = dict(bundle.header)
    header["format"] = STATE_FORMAT_PICKLE
    payload = pickle.dumps({"header": header, "soa": bundle.soa, "items": bundle.items,
                            "inflight": bundle.inflight}, protocol=5)
    run_id = str(header.get("run_id", ""))
    head = b" ".join([MAGIC, STATE_FORMAT_PICKLE.encode("ascii"), run_id.encode("utf-8"),
                      hashlib.sha256(payload).hexdigest().encode("ascii"), str(len(payload)).encode("ascii")]) + b"\n"
    side = json.dumps(header, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    _atomic_write(p.with_suffix(".json"), side.encode("utf-8"))
    _atomic_write(p, head + payload)
    return len(head) + len(payload)


def _read_side(p: Path, run_id: str | None = None) -> dict[str, Any]:
    side_path = p.with_suffix(".json")
    if not side_path.exists():
        raise SC.StateFormatError(f"見出しの写し({side_path.name})が無い状態のファイルは読まない")
    side = json.loads(side_path.read_text(encoding="utf-8"))
    if not isinstance(side, dict):
        raise SC.StateFormatError(f"見出しの写し({side_path.name})の形が違う")
    if run_id is not None and str(side.get("run_id", "")) != run_id:
        raise SC.StateFormatError(f"見出しの写しのラン ID が状態のファイルと違う({side.get('run_id')!r} != {run_id!r})")
    return side


def read_state(path: str | Path, *, allow_legacy_pickle: bool = False) -> StateBundle:
    """状態のまとまりを読む。既定は npz+json だけ(外から来たファイルでもコードを動かさない)。

    10d の pickle は ``allow_legacy_pickle=True`` と拡張子 ``.pkl`` がそろったときだけ開く(自分が書いたファイルに限る)。
    それ以外で中身が pickle(``SHIBUYA-STATE`` の先頭の行か pickle の印)なら開かずに ``StateFormatError``。
    拒否は全部 ``StateFormatError``(``ValueError`` の子)。

    npz+json: 1. 見出しの写し(``.json``)があり、写しの ``file`` の sha256・バイト数がファイルと同じ(壊れた・取り違えた
    ファイルを止める)。2. ``np.load(allow_pickle=False)`` と許可の表で組み立てる(``engine.state_codec``)。
    3. 見出しの形式の版・ラン ID・full-hash が写しと同じ。4. 状態台帳の版が今と同じ。5. 中身を台帳の宣言と突き合わせる
    (``check_bundle``)。
    """
    import hashlib


    p = Path(path)
    data = p.read_bytes()
    if data.startswith(MAGIC + b" ") or data[:1] == PICKLE_PROTO:
        if not (allow_legacy_pickle and p.suffix == ".pkl"):
            raise SC.StateFormatError(
                f"{p.name} は 10d の pickle の形式(開かない)。自分が書いた .pkl だけを、切替口"
                "(read_state の allow_legacy_pickle=True・run_day の resume_legacy_pickle=True・CLI の --resume-legacy-pickle)"
                "を付けて読む。拡張子が .pkl でないものは切替口があっても開かない")
        return _read_state_pickle(p, data)
    if not data.startswith(SC.ZIP_MAGIC):
        raise SC.StateFormatError(f"状態のファイルの形が違う(npz の印が無い): {p.name}")
    side = _read_side(p)
    f = side.get("file") if isinstance(side.get("file"), dict) else {}
    if f.get("format") != STATE_FORMAT:
        raise SC.StateFormatError(f"状態のファイルの形式の版が違う: 写しは {f.get('format')!r}(今は {STATE_FORMAT!r})")
    if f.get("bytes") != len(data) or f.get("sha256") != hashlib.sha256(data).hexdigest():
        raise SC.StateFormatError(f"状態のファイルの中身が写しの sha256 と合わない(壊れたか差し替えられた): {p.name}")
    try:
        doc = SC.loads(data)
    except SC.StateFormatError as e:
        raise SC.StateFormatError(f"状態のファイルを組み立てられない({p.name}): {e}") from None
    bundle = _bundle_from_doc(doc, p.name)
    h = bundle.header
    if h.get("format") != STATE_FORMAT:
        raise SC.StateFormatError(f"状態のファイルの形式の版が違う: {h.get('format')!r}(今は {STATE_FORMAT!r})")
    if str(h.get("run_id", "")) != str(side.get("run_id", "")) or h.get("hashes") != side.get("hashes"):
        raise SC.StateFormatError("状態のファイルの見出しが写し(.json)と違う(ラン ID か full-hash)")
    _check_ledger_version(h)
    check_bundle(bundle)
    return bundle


def _bundle_from_doc(doc: Any, name: str) -> StateBundle:
    if not isinstance(doc, dict) or set(doc) != {"header", "soa", "items", "inflight"}:
        raise SC.StateFormatError(f"状態のファイルの形が違う(header・soa・items・inflight の 4 つでない): {name}")
    if not isinstance(doc["header"], dict) or not isinstance(doc["soa"], dict) or not isinstance(doc["items"], dict) \
            or not isinstance(doc["inflight"], list):
        raise SC.StateFormatError(f"状態のファイルの形が違う(まとまりの型): {name}")
    return StateBundle(header=doc["header"], soa=doc["soa"], items=doc["items"], inflight=list(doc["inflight"]))


def _check_ledger_version(h: Mapping[str, Any]) -> None:
    if h.get("ledger_version") != SL.LEDGER_VERSION:
        raise SC.StateFormatError(
            f"状態台帳の版が違う: ファイルは {h.get('ledger_version')!r}・今は {SL.LEDGER_VERSION!r}"
            "(状態の範囲が変わったので読めない)"
        )


def _read_state_pickle(p: Path, data: bytes) -> StateBundle:
    """10d の pickle の形式(10e まで)。**自分が書いたものだけ**を読む検査を pickle を開く前に通す。

    1. 先頭の行の印と形式の版が 10d の版。2. 中身のバイト数と sha256 が先頭の行と同じ。3. 見出しの写し(``.json``)が
    あり、ラン ID が先頭の行と同じ。開いた後: 4. 見出しのラン ID・full-hash が写しと同じ。5. 状態台帳の版が今と同じ。
    6. 中身を台帳の宣言と突き合わせる。
    """
    import hashlib
    import warnings

    nl = data.find(b"\n")
    parts = data[:nl].split(b" ") if nl > 0 else []
    if len(parts) != 5 or parts[0] != MAGIC:
        raise SC.StateFormatError(f"状態のファイルの形が違う(先頭の行に印が無い): {p.name}")
    if parts[1].decode("ascii", "replace") != STATE_FORMAT_PICKLE:
        raise SC.StateFormatError(f"状態のファイルの形式の版が違う: {parts[1]!r}(10d の pickle は {STATE_FORMAT_PICKLE!r})")
    run_id = parts[2].decode("utf-8", "replace")
    payload = data[nl + 1:]
    if str(len(payload)).encode("ascii") != parts[4] or hashlib.sha256(payload).hexdigest().encode("ascii") != parts[3]:
        raise SC.StateFormatError(f"状態のファイルの中身が先頭の行の sha256 と合わない(壊れたか差し替えられた): {p.name}")
    side = _read_side(p, run_id)
    warnings.warn(LegacyStateFormatWarning(
        f"{p.name} は 10d の pickle の形式(10e まで読める・自分が書いたファイルだけを開く)。npz+json に書き直すには"
        " このファイルから再開して状態を書く"), stacklevel=3)
    doc = pickle.loads(payload)  # 自分で書いたファイルだけ(上の検査を通ったもの)を開く
    bundle = _bundle_from_doc(doc, p.name)
    h = bundle.header
    if h.get("format") != STATE_FORMAT_PICKLE:
        raise SC.StateFormatError(f"状態のファイルの形式の版が違う: {h.get('format')!r}(10d の pickle は {STATE_FORMAT_PICKLE!r})")
    if str(h.get("run_id", "")) != run_id or h.get("hashes") != side.get("hashes"):
        raise SC.StateFormatError("状態のファイルの見出しが写し(.json)と違う(ラン ID か full-hash)")
    _check_ledger_version(h)
    check_bundle(bundle)
    return bundle


# ---------------------------------------------------------------- 台帳の宣言との突き合わせ(10f・K23 (a))
def declared_dtype(code: str) -> tuple[np.dtype, int | None]:
    """台帳の SoA の行の型の略記(``i4``・``f4x2``・``u1x128``)→ (dtype, 2 次元目の長さ。1 次元なら ``None``)。"""
    base, _, k = str(code).partition("x")
    return np.dtype(base), (int(k) if k else None)


def check_bundle(bundle: StateBundle) -> None:
    """読んだ中身を状態台帳の宣言と突き合わせる(壊れた値・取り違えた値で動き出さない)。

    - 見出し: 必須の欄(形式の版・台帳の版・ラン ID・進捗・指紋・ハッシュ)と型。
    - SoA: 置き場は台帳の 4 つ・列は台帳の行(軸 2 が ``discardable`` でない列)・dtype と形は行の型の宣言
      (``i4x11`` なら ``(体数, 11)``)・同じ置き場の列は 1 次元目が同じ。
    - 外の状態: 道筋の集合と順が台帳の ``full_items`` と同じ・辞書の鍵はハッシュできる型。
    - 艦隊の未着の呼: list。
    """
    h = bundle.header
    for k, t in (("run_id", str), ("progress", dict), ("fingerprint", dict), ("hashes", dict),
                 ("ledger_version", str)):
        if not isinstance(h.get(k), t):
            raise SC.StateFormatError(f"状態のファイルの見出しの欄 {k} が無いか型が違う")
    nt = h["progress"].get("next_T")
    if not isinstance(nt, int) or isinstance(nt, bool) or nt < 0:
        raise SC.StateFormatError(f"状態のファイルの見出しの next_T が違う: {nt!r}")
    rows = {(r.place, r.name): r for r in SL.LEDGER if r.is_soa}
    for place, cols in bundle.soa.items():
        if place not in SL.SOA_PLACES or not isinstance(cols, dict):
            raise SC.StateFormatError(f"保存した SoA の置き場が台帳に無い: {place!r}")
        n0: int | None = None
        for name, arr in cols.items():
            r = rows.get((place, name))
            if r is None:
                raise SC.StateFormatError(f"保存した SoA の列が台帳に無い: {place}.{name}")
            if not r.in_full:
                raise SC.StateFormatError(f"保存した SoA の列は台帳では捨ててよい列: {place}.{name}")
            if not isinstance(arr, np.ndarray):
                raise SC.StateFormatError(f"保存した SoA の列が配列でない: {place}.{name}")
            dt, k = declared_dtype(r.dtype)
            want_ndim = 1 if k is None else 2
            if arr.dtype != dt or arr.ndim != want_ndim or (k is not None and arr.shape[1] != k):
                raise SC.StateFormatError(f"保存した SoA の列の型か形が台帳の宣言 {r.dtype} と違う: {place}.{name} "
                                 f"{arr.dtype}{arr.shape}")
            if n0 is None:
                n0 = int(arr.shape[0])
            elif int(arr.shape[0]) != n0:
                raise SC.StateFormatError(f"保存した SoA の列の長さが置き場の中で違う: {place}.{name}")
    want = [p_ for _k, p_ in SL.full_items()]
    if list(bundle.items) != want:
        got = set(bundle.items)
        raise SC.StateFormatError(f"保存した外の状態の道筋が今の台帳と違う(足りない {sorted(set(want) - got)[:5]}・"
                         f"余分 {sorted(got - set(want))[:5]}・順)")


#: 型を比べるときに同じ仲間とみなす数(Python の int・float と numpy の数のスカラー。bool は別)。
def _kind(v: Any) -> Any:
    from collections import OrderedDict, deque

    if v is None:
        return None
    if isinstance(v, (bool, np.bool_)):
        return "bool"
    if isinstance(v, Enum):
        return type(v)
    if isinstance(v, (int, float, np.integer, np.floating)):
        return "number"
    if isinstance(v, np.ndarray):
        return ("ndarray", v.dtype.str, v.ndim)
    if isinstance(v, np.random.Generator):
        return ("generator", type(v.bit_generator).__name__)
    if isinstance(v, (dict, OrderedDict, list, set, frozenset, deque, tuple, str)):
        return type(v)
    return type(v)


def _key_kinds(d: Mapping[Any, Any]) -> set[Any]:
    out = set()
    for k in d:
        out.add(tuple(_kind(e) for e in k) if type(k) is tuple else _kind(k))
    return out


def check_item_kinds(owners: Mapping[str, Any], items: Mapping[str, Any]) -> None:
    """再開で戻す前に、保存の値と今の値の型を突き合わせる(10f・K23 (a))。違えば ``ValueError``。

    どちらかが ``None`` なら比べない(初期値が ``None`` の属性)。数は Python と numpy の整数・浮動小数を同じ仲間に
    する(初期値の 0 と貯めた浮動小数)。配列は dtype と次元の数・辞書は型と、両方に鍵があるときは鍵の型の組・
    そのほかは型が同じ。
    """
    for path, saved in items.items():
        if isinstance(saved, str) and saved == ABSENT_MARK:
            continue
        cur = resolve_item(owners, path)
        if cur is _ABSENT or cur is None or saved is None:
            continue
        a, b = _kind(cur), _kind(saved)
        if a != b:
            raise SC.StateFormatError(f"保存した外の状態の型が今の値と違う: {path}(今 {a}・保存 {b})")
        if isinstance(cur, Mapping) and cur and saved:
            extra = _key_kinds(saved) - _key_kinds(cur)
            if extra:
                raise SC.StateFormatError(f"保存した外の状態の辞書の鍵の型が今の値と違う: {path}({sorted(map(str, extra))[:3]})")
