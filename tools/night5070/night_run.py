#!/usr/bin/env python3
"""5070 の夜の実験を 1 コマンドで回す(回答 10-25 §6-0 の 1)。

    python tools/night5070/night_run.py --experiment E1 [--config tools/night5070/experiments.json] \
        [--out docs/bench/night5070] [--data-out data/night5070] [--dry-run] [--keep-fleet]         [--deadline-hours 9.5] [--start-at 01:00]

手順: (a) 設定を読む → (b) 艦隊(WSL2 の vLLM)を立てる → (c) 健全性の確認(``GET /v1/models`` と 1 呼)→
(d) 実験のコマンド列を順に回す(標準出力と標準エラーは大きな出力の置き場の ``logs/`` へ)→ (e) 計測の分離の一覧(§6-7)を
``metrics.json`` と ``metrics.md`` に → (f) 艦隊を落とす → (g) 朝に読む ``summary.md``。

失敗したら、その段で止めて艦隊を落とし、ログと要約を残す。``--dry-run`` は艦隊を立てずコマンドも回さず、
何をするかを並べて要約を書く。

出力は 2 か所に分ける。小さな記録(``summary.md``・``metrics.json``・``metrics.md``・``night_run.json``・
``NIGHT_DONE``)は ``<out>/<YYYY-MM-DD>_<実験>/``、大きな出力(テープ・状態・checkpoints JSON・ログ)は
``<data-out>/<同じ名>/``(既定 ``data/night5070``=gitignore の中)。同じ名があれば ``_r2``・``_r3`` … を足す
(上書きしない)。``--dry-run`` は ``_dryrun`` を足す。要約と計測の一覧と ``_night_runs.log`` では、リポの根・
ホーム・python・WSL のホームの道筋を ``<REPO>``・``<HOME>``・``<PYTHON>``・``<WSLHOME>`` に置き換える
(ログは置き換えない=ログは git に入れない)。

ラン中は Windows のスリープを止める(``SetThreadExecutionState``・終わりに戻す)。

設定の穴: コマンドの中の ``{{名}}`` は設定の ``vars`` の値で埋める。値が null の名は「穴」で、穴が残ったまま
本番を回そうとすると、艦隊を立てる前に止める。実行時に埋める名(``OUT``=小さな記録の置き場・``DATA``=大きな
出力の置き場・``PYTHON``・``REPO``・``RUN_ID``・``ENDPOINTS``・``EXPERIMENT``)は ``vars`` に書かない。

終了コード: 0=成功・dry-run / 1=失敗 / 2=実験の名が無い / 3=設定の穴 / 4=成功(後始末=艦隊を落とす段に失敗)。

src/ は読まない・変えない(ランの出力のファイルを読むだけ)。
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import io
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_CONFIG = HERE / "experiments.json"
DEFAULT_OUT = Path("docs") / "bench" / "night5070"
DEFAULT_DATA_OUT = Path("data") / "night5070"

#: コマンドの中の穴の書き方。
HOLE_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
#: 実行時に night_run が埋める名(設定の ``vars`` には書かない)。
RUNTIME_VARS: tuple[str, ...] = ("OUT", "DATA", "PYTHON", "REPO", "RUN_ID", "ENDPOINTS", "EXPERIMENT")
UNMEASURED = "未計測"
MEASURED = "計測"
#: 朝の要約に載せるエラーの行数。
ERROR_HEAD_LINES = 20
#: 既定の締め切り[時間](タスクの実行時間の上限 10 時間より短く=艦隊を落とす時間を残す)。
DEFAULT_DEADLINE_HOURS = 9.5
#: SetThreadExecutionState の旗(winbase.h)。
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
RESULT_OK = "成功"
RESULT_OK_CLEANUP_FAILED = "成功(後始末に失敗)"
RESULT_FAILED = "失敗"
RESULT_DRY = "dry-run"


def keep_awake(on: bool) -> bool:
    """ラン中のスリープを止める(on)/戻す(off)。Windows 以外では何もしない。戻り値=呼べたか。"""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        flags = ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0)
        return bool(ctypes.windll.kernel32.SetThreadExecutionState(flags))
    except Exception:  # noqa: BLE001 - 止められなくてもランは続ける
        return False


class NightFailure(RuntimeError):
    """段の失敗(要約に書いて止める)。"""


# ------------------------------------------------------------------ 設定と穴


def load_config(path: Path) -> dict[str, Any]:
    """設定の JSON を読む。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _walk_strings(obj: Any, where: str = "") -> Iterable[tuple[str, str]]:
    if isinstance(obj, str):
        yield where, obj
    elif isinstance(obj, Mapping):
        for k, v in obj.items():
            yield from _walk_strings(v, f"{where}.{k}" if where else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, f"{where}[{i}]")


def find_holes(obj: Any, vars_: Mapping[str, Any], where: str = "") -> list[dict[str, str]]:
    """``obj`` の文字列の中の ``{{名}}`` のうち、``vars_`` で埋まらない名(値が null か名が無い)。"""
    out: list[dict[str, str]] = []
    for w, s in _walk_strings(obj, where):
        for m in HOLE_RE.finditer(s):
            name = m.group(1)
            if name in RUNTIME_VARS:
                continue
            if vars_.get(name) is None:
                out.append({"where": w, "name": name})
    return out


def experiment_parts(cfg: Mapping[str, Any], exp_name: str) -> dict[str, Any]:
    """実験 1 本で使う設定の部分(艦隊の節は艦隊を使う実験だけ)。"""
    exp = cfg["experiments"][exp_name]
    parts: dict[str, Any] = {f"experiments.{exp_name}.commands": exp.get("commands", []),
                             "env": cfg.get("env", {})}
    if exp.get("needs_fleet", True):
        parts["fleet"] = cfg.get("fleet", {})
    return parts


def holes_for(cfg: Mapping[str, Any], exp_name: str) -> list[dict[str, str]]:
    """実験 1 本を回すのに埋まっていない穴の一覧(重複は 1 つに)。"""
    vars_ = cfg.get("vars", {}) or {}
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for where, part in experiment_parts(cfg, exp_name).items():
        for h in find_holes(part, vars_, where):
            key = (h["where"], h["name"])
            if key not in seen:
                seen.add(key)
                out.append(h)
    return out


def all_holes(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """設定全体の穴(名ごとに使われる所)と、見積りが空欄の実験。"""
    vars_ = cfg.get("vars", {}) or {}
    names: dict[str, list[str]] = {}
    for h in find_holes({k: v for k, v in cfg.items() if k != "vars"}, vars_):
        names.setdefault(h["name"], []).append(h["where"])
    no_estimate = [k for k, e in (cfg.get("experiments") or {}).items() if e.get("estimated_minutes") is None]
    return {"names": names, "no_estimate": no_estimate}


def expand_str(s: str, vars_: Mapping[str, Any]) -> str:
    """文字列の中の ``{{名}}`` を埋める(埋まらない名はそのまま残す)。"""

    def _sub(m: re.Match[str]) -> str:
        v = vars_.get(m.group(1))
        if v is None:
            return m.group(0)
        if isinstance(v, (list, tuple)):
            return " ".join(str(x) for x in v)
        return str(v)

    return HOLE_RE.sub(_sub, s)


def expand_argv(argv: Iterable[Any], vars_: Mapping[str, Any]) -> list[str]:
    """コマンドの並びを埋める。要素がちょうど ``{{名}}`` で値が並びなら、その並びを差し込む。"""
    out: list[str] = []
    for a in argv:
        s = str(a)
        m = HOLE_RE.fullmatch(s)
        if m and isinstance(vars_.get(m.group(1)), (list, tuple)):
            out.extend(str(x) for x in vars_[m.group(1)])
        else:
            out.append(expand_str(s, vars_))
    return out


# ------------------------------------------------------------------ 道筋の置き換え


def mask_paths(text: str) -> str:
    """要約と計測の一覧に絶対パスを残さない(リポの根・python・ホーム)。"""
    pairs = [(str(Path(sys.executable)), "<PYTHON>"), (str(REPO), "<REPO>"), (REPO.as_posix(), "<REPO>"),
             (str(Path.home()), "<HOME>"), (Path.home().as_posix(), "<HOME>")]
    for raw, rep in sorted(pairs, key=lambda p: -len(p[0])):
        if raw:
            text = text.replace(raw, rep)
            text = text.replace(raw.replace("\\", "\\\\"), rep)  # JSON の中の二重のバックスラッシュ
    return _WSLHOME_RE.sub("<WSLHOME>", text)


_WSLHOME_RE = re.compile(r"/home/[^/\s'\"<>|]+")


def rel_or_abs(p: Path) -> str:
    """リポの中ならリポの根からの相対(posix)・外なら posix の絶対。"""
    try:
        return p.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return p.resolve().as_posix()


# ------------------------------------------------------------------ 段の記録


@dataclass
class Step:
    name: str
    status: str = "planned"  # planned / ok / failed / skipped
    started: str = ""
    ended: str = ""
    seconds: float = 0.0
    detail: str = ""
    argv: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    returncode: int | None = None


def _now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def _stamp(t: dt.datetime) -> str:
    return t.strftime("%Y-%m-%d %H:%M:%S %z")


class StepTimer:
    def __init__(self, step: Step) -> None:
        self.step = step
        self._t0 = 0.0

    def __enter__(self) -> Step:
        self.step.started = _stamp(_now())
        self._t0 = time.monotonic()
        return self.step

    def __exit__(self, et: Any, ev: Any, tb: Any) -> None:
        self.step.ended = _stamp(_now())
        self.step.seconds = round(time.monotonic() - self._t0, 3)
        if et is not None and self.step.status in ("planned", "ok"):
            self.step.status = "failed"
            if not self.step.detail:
                self.step.detail = f"{et.__name__}: {ev}"


# ------------------------------------------------------------------ コマンド


def run_logged(name: str, argv: list[str], *, cwd: Path, env: Mapping[str, str], timeout_s: float | None,
               log_dir: Path) -> tuple[int | None, Path, Path, str]:
    """コマンドを回し、標準出力と標準エラーを ``log_dir`` に書く。戻り値=(終了コード, 出力, エラー, 失敗の理由)。

    終了コードが None は「時間切れ」か「起動できない」(理由は 4 つ目)。
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    out_p = log_dir / f"{name}.stdout.log"
    err_p = log_dir / f"{name}.stderr.log"
    with io.FileIO(out_p, "w") as fo, io.FileIO(err_p, "w") as fe:
        try:
            cp = subprocess.run(argv, cwd=str(cwd), env=dict(env), stdout=fo, stderr=fe,
                                timeout=timeout_s, check=False)
            return cp.returncode, out_p, err_p, ""
        except subprocess.TimeoutExpired:
            fe.write(f"\n[night_run] 時間切れ({timeout_s:.0f} 秒)\n".encode("utf-8"))
            return None, out_p, err_p, f"時間切れ({timeout_s:.0f} 秒)"
        except OSError as exc:
            fe.write(f"\n[night_run] 起動できない: {exc}\n".encode("utf-8"))
            return None, out_p, err_p, f"起動できない: {exc}"


def error_head(err_path: Path | None, n: int = ERROR_HEAD_LINES) -> list[str]:
    """エラーの先頭 n 行(Traceback があれば最初の Traceback から・無ければ標準エラーの頭から)。"""
    if err_path is None or not Path(err_path).exists():
        return []
    lines = Path(err_path).read_text(encoding="utf-8", errors="replace").splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("Traceback"):
            return lines[i:i + n]
    return [ln for ln in lines if ln.strip()][:n]


# ------------------------------------------------------------------ 艦隊


def http_json(method: str, url: str, body: Any = None, timeout: float = 10.0) -> tuple[int, Any]:
    """HTTP で JSON を送って JSON を受ける(標準ライブラリだけ)。"""
    parts = urlsplit(url)
    conn_cls = http.client.HTTPSConnection if parts.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(parts.hostname or "127.0.0.1", parts.port, timeout=timeout)
    try:
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data is not None else {}
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        conn.request(method, path, body=data, headers=headers)
        r = conn.getresponse()
        raw = r.read()
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else None
        except ValueError:
            payload = raw.decode("utf-8", errors="replace")[:500]
        return int(r.status), payload
    finally:
        conn.close()


def check_health(endpoints: list[str], *, model: str = "", wait_s: float = 900.0, poll_s: float = 10.0,
                 prompt: str = "", max_tokens: int = 16,
                 sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic) -> dict[str, Any]:
    """各口で ``/v1/models`` が返るまで待ち(上限 ``wait_s``)、completion を 1 本投げて 1 行返るかを見る。

    ``model`` が空でなければ ``/v1/models`` の名と照合する(期待する served-model-name)。
    呼の形は ``shibuya.llm.fleet`` と同じ ``/v1/chat/completions``(考える段を切る)。失敗は ``NightFailure``。
    """
    out: dict[str, Any] = {"endpoints": [], "ok": False, "model": model}
    for base in endpoints:
        rec: dict[str, Any] = {"endpoint": base, "models": [], "seconds_to_ready": None, "completion_line": ""}
        t0 = clock()
        last = ""
        while True:
            try:
                st, js = http_json("GET", base.rstrip("/") + "/v1/models", timeout=min(10.0, max(1.0, poll_s)))
                if st == 200 and isinstance(js, Mapping) and js.get("data"):
                    rec["models"] = [str(d.get("id", "")) for d in js["data"]]
                    rec["seconds_to_ready"] = round(clock() - t0, 3)
                    break
                last = f"HTTP {st}"
            except (OSError, http.client.HTTPException) as exc:
                last = f"{type(exc).__name__}: {exc}"
            if clock() - t0 >= wait_s:
                out["endpoints"].append(rec)
                raise NightFailure(f"{base} の /v1/models が {wait_s:.0f} 秒以内に返らない(最後: {last})")
            sleep(poll_s)
        if model and model not in rec["models"]:
            out["endpoints"].append(rec)
            raise NightFailure(f"{base} の served-model-name が設定と違う(期待 {model}・/v1/models {rec['models']})")
        m = model or rec["models"][0]
        out["model"] = m
        body = {
            "model": m,
            "messages": [{"role": "user", "content": prompt or "1 行で答えてください。いまは朝ですか夜ですか。"}],
            "max_tokens": int(max_tokens),
            "temperature": 0.0,
            "chat_template_kwargs": {"enable_thinking": False},
        }
        try:
            st, js = http_json("POST", base.rstrip("/") + "/v1/chat/completions", body, timeout=120.0)
        except (OSError, http.client.HTTPException) as exc:
            out["endpoints"].append(rec)
            raise NightFailure(f"{base} の completion が失敗: {type(exc).__name__}: {exc}") from exc
        text = ""
        if st == 200 and isinstance(js, Mapping):
            try:
                text = str(js["choices"][0]["message"].get("content") or "")
            except (KeyError, IndexError, TypeError, AttributeError):
                text = ""
        first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
        rec["completion_line"] = first
        out["endpoints"].append(rec)
        if not first:
            raise NightFailure(f"{base} の completion が 1 行を返さない(HTTP {st}・{str(js)[:200]})")
    out["ok"] = True
    return out


# ------------------------------------------------------------------ 計測の分離の一覧(§6-7)

_RE_WALL = re.compile(r"壁時計 ([0-9.]+)s")
_RE_CALLS = re.compile(r"LLM呼 ([0-9,]+) = ([0-9.]+) 呼/体/日")
_RE_CONS = re.compile(r"保存則 .*? (OK|NG) / 最小在庫 (-?[0-9]+)")
_RE_PHASE = re.compile(r"内訳\[[^\]]*\] (.*)$", re.M)
_RE_FLEET = re.compile(
    r"\[艦隊\] 呼 ([0-9,]+) / 帳尻 ([0-9,]+) ・繰り延べ ([0-9,]+)\(再投入 ([0-9,]+)・再送 ([0-9,]+)\)"
    r" ・TTFT p50/p99 ([0-9.]+)/([0-9.]+)s ・e2e p50/p99 ([0-9.]+)/([0-9.]+)s"
)
_RE_FORMAT = re.compile(r"\[艦隊書式\] エラー率 実効 ([0-9.]+) / 厳密 ([0-9.]+)")


def _num(s: str) -> float:
    return float(s.replace(",", ""))


def parse_stdout(text: str) -> dict[str, Any]:
    """``shibuya.cli`` の標準出力(``RunResult.summary`` と艦隊の行)から取れる数。取れない鍵は入れない。"""
    out: dict[str, Any] = {}
    if m := _RE_WALL.search(text):
        out["engine_wall_seconds"] = float(m.group(1))
    if m := _RE_CALLS.search(text):
        out["llm_calls"] = int(_num(m.group(1)))
        out["calls_per_agent_day"] = float(m.group(2))
    if m := _RE_CONS.search(text):
        out["conservation"] = m.group(1)
        out["min_stock"] = int(m.group(2))
    if m := _RE_PHASE.search(text):
        phases: dict[str, float] = {}
        for part in m.group(1).split(" / "):
            bits = part.strip().rsplit(" ", 1)
            if len(bits) == 2:
                try:
                    phases[bits[0]] = float(bits[1])
                except ValueError:
                    pass
        out["phase_ms_per_step"] = phases
    if m := _RE_FLEET.search(text):
        g = [_num(x) for x in m.groups()]
        out["fleet"] = {"fired": int(g[0]), "accounted": int(g[1]), "deferred": int(g[2]), "reinjected": int(g[3]),
                        "resent": int(g[4]), "ttft_p50_s": g[5], "ttft_p99_s": g[6], "e2e_p50_s": g[7],
                        "e2e_p99_s": g[8]}
    if m := _RE_FORMAT.search(text):
        out["format_error"] = {"effective": float(m.group(1)), "strict": float(m.group(2))}
    return out


#: テープから読む列(在るものだけを読む=schema を先に読んで交わりを取る)。
TAPE_COLUMNS: tuple[str, ...] = ("agent_id", "wake_class", "tokens_in", "tokens_out", "deferred", "deferred_reason")


def read_tape(tape_dir: Path | None) -> dict[str, Any] | None:
    """テープの ``calls.parquet`` の集計(pyarrow が無い・ファイルが無いなら None)。

    読めないテープ(途中で落ちたランの footer の無いファイルなど)は例外を上げる。呼ぶ側が欄を
    「未計測(読めない: 例外の名)」にして続ける。トークンの平均は繰り延べでない行(deferred=0)だけで出す。
    """
    if tape_dir is None:
        return None
    p = Path(tape_dir) / "calls.parquet"
    if not p.exists():
        return None
    try:
        import pyarrow.parquet as pq
    except ImportError:
        return None
    present = set(pq.read_schema(p).names)
    cols = [c for c in TAPE_COLUMNS if c in present]
    t = pq.read_table(p, columns=cols)
    names = set(cols)
    rows = int(t.num_rows)
    out: dict[str, Any] = {"rows": rows}
    deferred = [int(x) for x in t.column("deferred").to_pylist()] if "deferred" in names else None
    answered_mask = [not x for x in deferred] if deferred is not None else [True] * rows
    if deferred is not None:
        out["deferred"] = int(sum(1 for x in deferred if x))
        out["answered"] = rows - out["deferred"]
    if "deferred_reason" in names:
        reasons: dict[str, int] = {}
        for r in t.column("deferred_reason").to_pylist():
            if r:
                reasons[str(r)] = reasons.get(str(r), 0) + 1
        out["deferred_reason"] = reasons
    for col in ("tokens_in", "tokens_out"):
        if col in names and rows:
            vals = [int(x) for x, ok in zip(t.column(col).to_pylist(), answered_mask) if ok]
            n = len(vals)
            out[col] = {"sum": int(sum(vals)), "mean": (round(sum(vals) / n, 3) if n else None), "rows": n}
    if "wake_class" in names:
        by: dict[str, dict[str, int]] = {}
        wc = t.column("wake_class").to_pylist()
        for i, w in enumerate(wc):
            d = by.setdefault(str(w), {"rows": 0, "deferred": 0})
            d["rows"] += 1
            if deferred is not None and deferred[i]:
                d["deferred"] += 1
        out["by_wake_class"] = dict(sorted(by.items()))
    if "agent_id" in names:
        out["distinct_agents"] = len(set(t.column("agent_id").to_pylist()))
    return out


def _field(key: str, group: str, label: str, value: Any, source: str, note: str = "", *,
           unreadable: str = "") -> dict[str, Any]:
    """1 欄。取れない欄は「未計測」(元のファイルが読めなかったときは「未計測(読めない: 例外の名)」)。

    ``source`` は取れたときの出所、``source_planned`` は取る予定の出所(未計測でも残す)。
    """
    measured = value is not None
    if measured:
        shown: Any = value
    elif unreadable:
        shown = f"{UNMEASURED}(読めない: {unreadable})"
    else:
        shown = UNMEASURED
    return {"key": key, "group": group, "label": label, "status": MEASURED if measured else UNMEASURED,
            "value": shown, "source": source if measured else "", "source_planned": source, "note": note}


def build_metrics(*, stdout_text: str = "", stdout_name: str = "", checkpoints: Mapping[str, Any] | None = None,
                  checkpoints_name: str = "", tape: Mapping[str, Any] | None = None, tape_name: str = "",
                  night_wall_seconds: float | None = None, sim_days: int = 1,
                  yen_per_hour: float | None = None, health: Mapping[str, Any] | None = None,
                  unreadable: Mapping[str, str] | None = None) -> dict[str, Any]:
    """計測の分離の一覧(回答 10-25 §6-7)。ランの出力から取れる欄だけ埋め、取れない欄は「未計測」。

    各欄に、どのファイルのどの鍵(行)から来たかを ``source`` に書く。``unreadable`` は読めなかった元
    (``stdout``・``checkpoints``・``tape`` → 例外の名)。
    """
    u = dict(unreadable or {})
    us, uc, ut = u.get("stdout", ""), u.get("checkpoints", ""), u.get("tape", "")
    so = parse_stdout(stdout_text or "")
    fl = so.get("fleet") or {}
    ph = so.get("phase_ms_per_step") or {}
    man = dict((checkpoints or {}).get("manifest") or {})
    cps = list((checkpoints or {}).get("checkpoints") or [])
    tp = dict(tape or {})
    src_so = f"{stdout_name}" if stdout_name else "実験の標準出力"
    src_cp = f"{checkpoints_name}" if checkpoints_name else "checkpoints JSON"
    src_tp = f"{tape_name}/calls.parquet" if tape_name else "テープ calls.parquet"

    def g(d: Mapping[str, Any], k: str) -> Any:
        return d.get(k) if k in d else None

    daily = list(man.get("daily") or [])
    ev_rows = None
    ev_by_what: dict[str, int] = {}
    if daily and all(isinstance(r, Mapping) and isinstance(r.get("events"), Mapping) for r in daily):
        if any(bool(r["events"].get("on")) for r in daily):
            ev_rows = int(sum(int(r["events"].get("rows", 0) or 0) for r in daily))
            for r in daily:
                for k, v in dict(r["events"].get("by_what") or {}).items():
                    ev_by_what[str(k)] = ev_by_what.get(str(k), 0) + int(v)
    yen = None
    if yen_per_hour is not None and night_wall_seconds is not None and sim_days > 0:
        yen = round(float(yen_per_hour) * night_wall_seconds / 3600.0 / sim_days, 1)
    hashes = None
    if cps:
        hashes = [{k: v for k, v in dict(c).items()} for c in cps]
    n_rep = (man.get("fleet") or {}).get("n_replicas") if isinstance(man.get("fleet"), Mapping) else None
    tin, tout = tp.get("tokens_in"), tp.get("tokens_out")

    fields_ = [
        # 1 エンジンの時間
        _field("engine.wall_seconds", "エンジンの時間", "ランの壁時計[s]", g(so, "engine_wall_seconds"),
               f"{src_so} の「壁時計 …s」", unreadable=us),
        _field("engine.phase_ms_per_step", "エンジンの時間", "段ごとの時間[ms/刻み]", ph or None,
               f"{src_so} の「内訳[…]」の行", unreadable=us),
        _field("night.wall_seconds", "エンジンの時間", "夜の全体の壁時計[s](艦隊の起動と健全性の確認を含む)",
               night_wall_seconds, "night_run の時計"),
        # 2 LLM
        _field("llm.fired", "LLM", "発射数", fl.get("fired"), f"{src_so} の「[艦隊] 呼」", unreadable=us),
        _field("llm.answered", "LLM", "応答数(テープの繰り延べでない行)", tp.get("answered"),
               f"{src_tp} の deferred=0 の行数", unreadable=ut),
        _field("llm.accounted", "LLM", "帳尻(fleet_accounted)", fl.get("accounted"), f"{src_so} の「帳尻」",
               unreadable=us),
        _field("llm.deferred", "LLM", "繰り延べ", fl.get("deferred"), f"{src_so} の「繰り延べ」", unreadable=us),
        _field("llm.deferred_reason", "LLM", "繰り延べの理由別(テープ)", tp.get("deferred_reason"),
               f"{src_tp} の deferred_reason", unreadable=ut),
        _field("llm.reinjected", "LLM", "再投入", fl.get("reinjected"), f"{src_so} の「再投入」", unreadable=us),
        _field("llm.resent", "LLM", "再送", fl.get("resent"), f"{src_so} の「再送」", unreadable=us),
        _field("llm.failed", "LLM", "失敗", None, "", "ランの出力に失敗の数の欄が無い"),
        _field("llm.wait_ms_per_step", "LLM", "艦隊の待ち時間[ms/刻み]", ph.get("fleet_wait"),
               f"{src_so} の「内訳」の fleet_wait", unreadable=us),
        _field("llm.ttft_s", "LLM", "TTFT p50/p99[s]",
               ({"p50": fl["ttft_p50_s"], "p99": fl["ttft_p99_s"]} if fl else None), f"{src_so} の「TTFT p50/p99」",
               "ストリーミングでない呼では TTFT は e2e と同じ値(fleet.py の expedient)", unreadable=us),
        _field("llm.e2e_s", "LLM", "e2e p50/p99[s]", ({"p50": fl["e2e_p50_s"], "p99": fl["e2e_p99_s"]} if fl else None),
               f"{src_so} の「e2e p50/p99」", unreadable=us),
        _field("llm.per_gpu", "LLM", "GPU ごとの処理量", None, "",
               f"ランの出力にレプリカごとの数が無い(manifest の fleet.n_replicas={n_rep})"),
        _field("llm.format_error", "LLM", "書式エラー率 実効/厳密", so.get("format_error"), f"{src_so} の「[艦隊書式]」",
               unreadable=us),
        _field("llm.health", "LLM", "健全性の確認(口ごとの準備までの秒・1 行)", dict(health) if health else None,
               "night_run の健全性の確認"),
        # 3 トークン(繰り延べでない行だけ)
        _field("tokens.in_per_call", "トークン", "呼あたりの入力トークン(deferred=0 の行)", tin,
               f"{src_tp} の tokens_in", unreadable=ut),
        _field("tokens.out_per_call", "トークン", "呼あたりの出力トークン(deferred=0 の行)", tout,
               f"{src_tp} の tokens_out", unreadable=ut),
        # 4 起床の理由
        _field("wake.calls_by_class", "起床の理由", "起床の種類ごとの呼と繰り延べ(テープ)", tp.get("by_wake_class"),
               f"{src_tp} の wake_class・deferred", unreadable=ut),
        _field("wake.decision_layers", "起床の理由", "時 × 層 × 起床入口の判断数", man.get("decision_layers") or None,
               f"{src_cp} の manifest.decision_layers", unreadable=uc),
        _field("wake.candidates", "起床の理由", "起床の理由別の候補", None, "", "ランの出力に候補の数が無い"),
        _field("wake.adopted", "起床の理由", "起床の理由別の採択", None, "", "ランの出力に採択の数が無い(呼の数は上の欄)"),
        # 5 体と行動
        _field("agents.calls_per_agent_day", "体と行動", "体あたりの呼数[呼/体/日]", g(so, "calls_per_agent_day"),
               f"{src_so} の「LLM呼 … 呼/体/日」", unreadable=us),
        _field("agents.calls_by_condition", "体と行動", "条件ごとの呼数", man.get("calls_by_condition") or None,
               f"{src_cp} の manifest.calls_by_condition", unreadable=uc),
        _field("agents.action_usage", "体と行動", "行動の分布", man.get("action_usage") or None,
               f"{src_cp} の manifest.action_usage", unreadable=uc),
        _field("agents.conversations", "体と行動", "会話の回数", None, "",
               "ランの出力に会話の回数の欄が無い(出来事の種類の内訳を見る)"),
        _field("agents.events", "体と行動", "出来事の数(日ごとの記録の合計)",
               ({"rows": ev_rows, "by_what": ev_by_what} if ev_rows is not None else None),
               f"{src_cp} の manifest.daily[].events.rows・by_what", unreadable=uc),
        # 6 決定論
        _field("determinism.state_hashes", "決定論", "刻みごとの状態ハッシュ(checkpoint の列)", hashes,
               f"{src_cp} の checkpoints", unreadable=uc),
        _field("determinism.final_hash", "決定論", "最後のハッシュ", (checkpoints or {}).get("final_hash") or None,
               f"{src_cp} の final_hash", unreadable=uc),
        _field("determinism.tape_replay", "決定論", "テープ再生の一致", None, "", "再生のランを回していない"),
        _field("determinism.conservation", "決定論", "保存則", g(so, "conservation"), f"{src_so} の「保存則 … OK/NG」",
               unreadable=us),
        # 7 錨
        _field("anchors.presence", "錨", "在圏との一致", None, "", "錨の計器をこの道具では回さない"),
        _field("anchors.peak_time", "錨", "ピーク時刻との一致", None, "", "同上"),
        _field("anchors.visitor_ratio", "錨", "来街者比との一致", None, "", "同上"),
        # 8 費用
        _field("cost.yen_per_sim_day", "費用", "円/シミュ日", yen, "設定 cost.yen_per_hour × 夜の壁時計 ÷ シミュ日",
               "" if yen is not None else "設定 cost.yen_per_hour が空欄(S4 の計器は未実装)"),
    ]
    return {"schema": "night5070/metrics/2", "fields": fields_,
            "n_measured": sum(1 for f in fields_ if f["status"] == MEASURED),
            "n_unmeasured": sum(1 for f in fields_ if f["status"] == UNMEASURED),
            "unreadable": u}


def metrics_markdown(metrics: Mapping[str, Any]) -> str:
    lines = ["# 計測の分離の一覧(回答 10-25 §6-7)", "",
             f"計測 {metrics['n_measured']} 欄 / 未計測 {metrics['n_unmeasured']} 欄。値の長いものは metrics.json を見る。", "",
             "| 群 | 欄 | 値 | 出所 | 注 |", "|---|---|---|---|---|"]
    for f in metrics["fields"]:
        v = f["value"]
        s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str)
        if len(s) > 120:
            s = s[:117] + "…"
        s = s.replace("|", "\\|")
        lines.append(f"| {f['group']} | {f['label']} | {s} | {f['source']} | {f['note']} |")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ 出力先


def make_run_dir(out_root: Path, data_root: Path, day: str, exp_name: str, dry_run: bool) -> tuple[Path, Path]:
    """小さな記録の置き場(作る)と大きな出力の置き場(dry-run では作らない)。どちらにも無い名を選ぶ。"""
    base = f"{day}_{exp_name}" + ("_dryrun" if dry_run else "")
    name = base
    k = 2
    while (out_root / name).exists() or (data_root / name).exists():
        name = f"{base}_r{k}"
        k += 1
    d = out_root / name
    d.mkdir(parents=True)
    dd = data_root / name
    if not dry_run:
        dd.mkdir(parents=True)
    return d, dd


# ------------------------------------------------------------------ 要約


def _fmt_minutes(m: Any) -> str:
    return "空欄(R-C で埋める)" if m is None else f"{m} 分"


def _end_at(start: dt.datetime | None, minutes: Any) -> str:
    if minutes is None:
        return "見積りが空欄"
    if start is None:
        return "—"
    return (start + dt.timedelta(minutes=float(minutes))).strftime("%H:%M")


def _at_on(day: dt.datetime, hhmm: str | None) -> dt.datetime | None:
    """``HH:MM`` → ``day`` の日のその時刻(読めなければ None)。"""
    m = re.fullmatch(r"([01]?[0-9]|2[0-3]):([0-5][0-9])", str(hhmm or "").strip())
    if not m:
        return None
    return day.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)


def write_summary(run_dir: Path, state: Mapping[str, Any], cfg: Mapping[str, Any]) -> Path:
    """朝に読む 1 枚(成功/失敗・時刻・壁時計・呼数・エラーの先頭・結果のパス・見積り)。"""
    exp_name = state["experiment"]
    exp = cfg["experiments"][exp_name]
    order = list(cfg["experiments"].keys())
    nxt = order[order.index(exp_name) + 1] if order.index(exp_name) + 1 < len(order) else None
    start = dt.datetime.fromisoformat(state["started_iso"])
    lines = [f"# 夜の実験 {exp_name} の要約", ""]
    if state.get("fleet_stop_failed"):
        lines += ["> **艦隊が落ちていない。wsl --shutdown を手で。**", ""]
    calls = state.get("calls_text", UNMEASURED)
    if exp.get("before_2_7"):
        calls = f"参考値(2-7 の直しの前): {calls}"
    lines += [f"- 結果: **{state['result']}**" + ("(何も回していない)" if state["dry_run"] else ""),
              f"- 目的: {exp.get('purpose', '')}",
              f"- 開始: {state['started']} / 終了: {state.get('ended', '')} / 壁時計: {state.get('wall_seconds', 0):.0f} 秒"
              f"({state.get('wall_seconds', 0) / 60:.1f} 分)",
              f"- 呼数: {calls}",
              f"- 見積り: {_fmt_minutes(exp.get('estimated_minutes'))}"
              f"(実際の開始 {start:%H:%M} から終わりの見込み {_end_at(start, exp.get('estimated_minutes'))})",
              f"- 小さな記録: `{state['run_dir']}`(summary.md・metrics.json・metrics.md・night_run.json・NIGHT_DONE)",
              f"- 大きな出力とログ: `{state.get('data_dir', '')}`(テープ・状態・checkpoints JSON・logs/)",
              f"- スリープの抑止: {'効いた' if state.get('keep_awake') else '効かない(Windows 以外か dry-run)'}"]
    if state.get("failed_step"):
        lines.append(f"- 失敗した段: {state['failed_step']} — {state.get('failure', '')}")
    if state.get("fleet_left_running"):
        lines.append("- **艦隊を落としていない**(--keep-fleet)。朝に stop のコマンドを手で回す。")
    if state.get("finish_errors"):
        lines.append("- 記録の書き出しの失敗: " + " / ".join(state["finish_errors"]))
    pre = exp.get("preconditions") or []
    if pre:
        lines += ["", "## 前提と注"] + [f"- {p}" for p in pre]
    if state.get("holes"):
        lines += ["", "## 設定の穴(埋まっていない名)"]
        lines += [f"- `{{{{{h['name']}}}}}` — {h['where']}" for h in state["holes"]]
    lines += ["", "## 段", "", "| 段 | 状態 | 秒 | 詳細 |", "|---|---|---|---|"]
    for s in state.get("steps", []):
        lines.append(f"| {s['name']} | {s['status']} | {s['seconds']:.1f} | {str(s['detail']).replace('|', '/')} |")
    if state.get("error_head"):
        lines += ["", f"## エラーの先頭 {ERROR_HEAD_LINES} 行", "", "```"] + list(state["error_head"]) + ["```"]
    if state["dry_run"]:
        lines += ["", "## 回すはずのコマンド(dry-run)", ""]
        for s in state.get("steps", []):
            if s["argv"]:
                lines.append(f"- {s['name']}: `{' '.join(s['argv'])}`")
    lines += ["", "## 計測の分離の一覧", "",
              f"metrics.md を見る(計測 {state.get('n_measured', 0)} 欄 / 未計測 {state.get('n_unmeasured', 0)} 欄)。"]
    sa = _at_on(start, state.get("start_at"))
    head = f"| 実験 | 見積り | 実際の開始 {start:%H:%M} から |"
    rule = "|---|---|---|"
    if sa is not None:
        head += f" start_at {sa:%H:%M} から |"
        rule += "---|"
    lines += ["", "## 各実験の所要時間の見積り(設定の estimated_minutes)と終わりの時刻", "",
              head + " 前提 |", rule + "---|"]
    for k in order:
        e = cfg["experiments"][k]
        mark = "(次)" if k == nxt else ("(今回)" if k == exp_name else "")
        pre1 = "・".join(e.get("preconditions") or [])[:60]
        row = f"| {k}{mark} | {_fmt_minutes(e.get('estimated_minutes'))} | {_end_at(start, e.get('estimated_minutes'))} |"
        if sa is not None:
            row += f" {_end_at(sa, e.get('estimated_minutes'))} |"
        lines.append(row + f" {pre1} |")
    p = run_dir / "summary.md"
    p.write_text(mask_paths("\n".join(lines) + "\n"), encoding="utf-8", newline="\n")
    return p


def _fallback_summary(run_dir: Path, state: Mapping[str, Any], exc: BaseException) -> None:
    """要約を書く処理が落ちたときの最小の 1 枚。"""
    text = (f"# 夜の実験 {state.get('experiment', '')} の要約(簡易)\n\n"
            f"- 結果: **{state.get('result', RESULT_FAILED)}**\n"
            f"- 失敗: {state.get('failure', '')}\n"
            f"- 要約を書く処理が落ちた: {type(exc).__name__}: {exc}\n"
            f"- night_run.json と大きな出力の置き場の logs/ を見る\n")
    if state.get("fleet_stop_failed"):
        text = "> **艦隊が落ちていない。wsl --shutdown を手で。**\n\n" + text
    (run_dir / "summary.md").write_text(mask_paths(text), encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ 本体


def _build_env(cfg: Mapping[str, Any], vars_: Mapping[str, Any]) -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    for k, v in (cfg.get("env") or {}).items():
        if v is not None:
            env[str(k)] = expand_str(str(v), vars_)
    return env


def _cmd_timeout(cmd: Mapping[str, Any], deadline: float) -> float:
    remain = max(1.0, deadline - time.monotonic())
    own = cmd.get("timeout_minutes")
    return min(remain, float(own) * 60.0) if own else remain


def _abs_root(p: Path | None, default: Path) -> Path:
    q = Path(p) if p is not None else default
    return q if q.is_absolute() else REPO / q


def run_night(exp_name: str, *, config_path: Path = DEFAULT_CONFIG, out_root: Path | None = None,
              data_root: Path | None = None, dry_run: bool = False, keep_fleet: bool = False,
              deadline_hours: float | None = None, start_at: str | None = None) -> int:
    """夜の 1 本。戻り値=0(成功・dry-run)/ 1(失敗)/ 2(実験の名が無い)/ 3(設定の穴)/ 4(成功・後始末に失敗)。"""
    cfg = load_config(config_path)
    if exp_name not in (cfg.get("experiments") or {}):
        print(f"night_run: 実験 {exp_name} が設定に無い(ある: {', '.join(cfg.get('experiments') or {})})",
              file=sys.stderr)
        return 2
    exp = cfg["experiments"][exp_name]
    t_start = _now()
    m0 = time.monotonic()
    out_root = _abs_root(out_root, DEFAULT_OUT)
    data_root = _abs_root(data_root, DEFAULT_DATA_OUT)
    run_dir, data_dir = make_run_dir(out_root, data_root, t_start.strftime("%Y-%m-%d"), exp_name, dry_run)
    log_dir = data_dir / "logs"
    needs_fleet = bool(exp.get("needs_fleet", True))
    hours = float(deadline_hours if deadline_hours is not None else cfg.get("deadline_hours", DEFAULT_DEADLINE_HOURS))
    deadline = m0 + hours * 3600.0
    start_at = start_at or cfg.get("start_at") or None

    vars_: dict[str, Any] = dict(cfg.get("vars") or {})
    vars_.update({"OUT": rel_or_abs(run_dir), "DATA": rel_or_abs(data_dir), "PYTHON": sys.executable,
                  "REPO": str(REPO), "RUN_ID": f"night5070-{exp_name}-{t_start.strftime('%Y%m%d-%H%M')}",
                  "EXPERIMENT": exp_name})
    fleet_cfg = dict(cfg.get("fleet") or {})
    endpoints = [expand_str(str(e), vars_) for e in fleet_cfg.get("endpoints", [])]
    vars_["ENDPOINTS"] = ",".join(endpoints)
    env = _build_env(cfg, vars_)
    holes = holes_for(cfg, exp_name)

    steps: list[Step] = []
    state: dict[str, Any] = {"experiment": exp_name, "dry_run": dry_run, "started": _stamp(t_start),
                             "started_iso": t_start.isoformat(), "run_dir": rel_or_abs(run_dir),
                             "data_dir": rel_or_abs(data_dir), "holes": holes, "needs_fleet": needs_fleet,
                             "deadline_hours": hours, "start_at": start_at,
                             "before_2_7": bool(exp.get("before_2_7"))}
    state["keep_awake"] = keep_awake(True) if not dry_run else False
    fleet_started = False
    bg_proc: Any = None
    health: dict[str, Any] | None = None
    main_stdout: Path | None = None
    main_stdout_name = ""
    last_err: Path | None = None

    def _fleet_argv(key: str) -> list[str]:
        node = fleet_cfg.get(key) or {}
        return expand_argv(node.get("argv") or [], vars_)

    def _check_deadline(what: str) -> None:
        if time.monotonic() >= deadline:
            raise NightFailure(f"締め切り({hours:g} 時間)を超えた({what} の前)")

    try:
        # (a) 設定
        st = Step("設定を読む")
        steps.append(st)
        with StepTimer(st):
            if holes:
                st.status = "failed" if not dry_run else "ok"
                st.detail = f"穴 {len(holes)} 個(" + "・".join(sorted({h['name'] for h in holes})) + ")"
                if not dry_run:
                    raise NightFailure("設定の穴が埋まっていない(艦隊は立てていない)")
            else:
                st.status = "ok"
                st.detail = "穴なし"
        # (b)(c) 艦隊
        if needs_fleet:
            st = Step("前の艦隊を落とす(起動の前・失敗は無視)", argv=_fleet_argv("stop"))
            steps.append(st)
            with StepTimer(st):
                if dry_run:
                    st.status = "skipped"
                    st.detail = "dry-run"
                else:
                    rc, o, e, why = run_logged("fleet_prestop", st.argv, cwd=REPO, env=env,
                                               timeout_s=float((fleet_cfg.get("stop") or {}).get("timeout_s", 120)),
                                               log_dir=log_dir)
                    st.returncode = rc
                    st.logs = [rel_or_abs(o), rel_or_abs(e)]
                    st.status = "ok"
                    st.detail = "落とした" if rc == 0 else f"無視(終了コード {rc}{'・' + why if why else ''})"
            st = Step("艦隊を立てる", argv=_fleet_argv("start"))
            steps.append(st)
            with StepTimer(st):
                if dry_run:
                    st.status = "skipped"
                    st.detail = "dry-run"
                else:
                    _check_deadline("艦隊を立てる")
                    node = fleet_cfg.get("start") or {}
                    if node.get("background"):
                        log_dir.mkdir(parents=True, exist_ok=True)
                        fo = io.FileIO(log_dir / "fleet_start.stdout.log", "w")
                        fe = io.FileIO(log_dir / "fleet_start.stderr.log", "w")
                        try:
                            fleet_started = True
                            bg_proc = subprocess.Popen(st.argv, cwd=str(REPO), env=env, stdout=fo, stderr=fe)
                        finally:
                            fo.close()
                            fe.close()
                        st.status = "ok"
                        st.detail = "背後で起動(健全性の確認で待つ)"
                    else:
                        fleet_started = True  # 途中まで立った可能性があるので stop は回す
                        rc, _o, e, why = run_logged("fleet_start", st.argv, cwd=REPO, env=env,
                                                    timeout_s=float(node.get("timeout_s", 120)), log_dir=log_dir)
                        st.returncode = rc
                        st.logs = [rel_or_abs(_o), rel_or_abs(e)]
                        if rc != 0:
                            last_err = e
                            raise NightFailure(why or f"終了コード {rc}")
                        st.status = "ok"
            st = Step("健全性の確認")
            steps.append(st)
            with StepTimer(st):
                if dry_run:
                    st.status = "skipped"
                    st.detail = "dry-run(" + ", ".join(endpoints) + ")"
                else:
                    _check_deadline("健全性の確認")
                    hc = fleet_cfg.get("health") or {}
                    wait_s = min(float(hc.get("wait_s", 900)), max(1.0, deadline - time.monotonic()))
                    health = {"pending": True}
                    try:
                        health = check_health(endpoints, model=str(fleet_cfg.get("model") or ""),
                                              wait_s=wait_s, poll_s=float(hc.get("poll_s", 10)),
                                              prompt=str(hc.get("prompt") or ""),
                                              max_tokens=int(hc.get("max_tokens", 16)))
                    except NightFailure as exc:
                        health = {"ok": False, "error": str(exc)}
                        raise
                    st.status = "ok"
                    st.detail = "・".join(f"{r['endpoint']} {r['seconds_to_ready']}s「{r['completion_line'][:30]}」"
                                          for r in health["endpoints"])
        # (d) 実験
        cmds = list(exp.get("commands") or [])
        if not cmds:
            st = Step("実験のコマンド")
            steps.append(st)
            with StepTimer(st):
                st.status = "skipped" if dry_run else "failed"
                st.detail = "コマンドが無い"
                if not dry_run:
                    raise NightFailure("実験のコマンドが無い")
        for i, cmd in enumerate(cmds):
            nm = str(cmd.get("name") or f"cmd{i + 1}")
            st = Step(f"実験: {nm}", argv=expand_argv(cmd.get("argv") or [], vars_))
            steps.append(st)
            with StepTimer(st):
                if dry_run:
                    st.status = "skipped"
                    st.detail = "dry-run"
                    continue
                _check_deadline(f"実験: {nm}")
                rc, o, e, why = run_logged(f"exp_{i + 1:02d}_{nm}", st.argv, cwd=REPO, env=env,
                                           timeout_s=_cmd_timeout(cmd, deadline), log_dir=log_dir)
                st.returncode = rc
                st.logs = [rel_or_abs(o), rel_or_abs(e)]
                if cmd.get("metrics_source", i == 0):
                    main_stdout, main_stdout_name = o, rel_or_abs(o)
                if rc != 0:
                    last_err = e
                    raise NightFailure(why or f"終了コード {rc}")
                st.status = "ok"
        state["result"] = RESULT_DRY if dry_run else RESULT_OK
    except NightFailure as exc:
        state["result"] = RESULT_FAILED
        bad = next((s for s in steps if s.status == "failed"), steps[-1] if steps else None)
        state["failed_step"] = bad.name if bad else ""
        state["failure"] = str(exc)
        if bad and not bad.detail:
            bad.detail = str(exc)
        state["error_head"] = error_head(last_err) or [str(exc)]
    except KeyboardInterrupt:
        state["result"] = RESULT_FAILED
        state["failed_step"] = steps[-1].name if steps else ""
        state["failure"] = "中断(KeyboardInterrupt)"
        state["error_head"] = error_head(last_err) or ["中断"]
    except Exception as exc:  # noqa: BLE001 - 想定外の失敗も朝に読める形で残す
        import traceback

        state["result"] = RESULT_FAILED
        state["failed_step"] = steps[-1].name if steps else ""
        state["failure"] = f"想定外: {type(exc).__name__}: {exc}"
        state["error_head"] = traceback.format_exc().splitlines()[:ERROR_HEAD_LINES]
        if steps and steps[-1].status in ("planned", "ok"):
            steps[-1].status = "failed"
    finally:
        try:
            _cleanup_fleet(steps=steps, state=state, fleet_cfg=fleet_cfg, needs_fleet=needs_fleet,
                           fleet_started=fleet_started, dry_run=dry_run, keep_fleet=keep_fleet, bg_proc=bg_proc,
                           argv_of=_fleet_argv, env=env, log_dir=log_dir)
        finally:
            if state.get("keep_awake"):
                keep_awake(False)
            _finish(run_dir=run_dir, out_root=out_root, state=state, cfg=cfg, exp=exp, steps=steps, vars_=vars_,
                    m0=m0, dry_run=dry_run, main_stdout=main_stdout, main_stdout_name=main_stdout_name,
                    health=health)
    res = state.get("result")
    if res in (RESULT_OK, RESULT_DRY):
        return 0
    if res == RESULT_OK_CLEANUP_FAILED:
        return 4
    return 3 if holes and not dry_run else 1


def _cleanup_fleet(*, steps: list[Step], state: dict[str, Any], fleet_cfg: Mapping[str, Any], needs_fleet: bool,
                   fleet_started: bool, dry_run: bool, keep_fleet: bool, bg_proc: Any,
                   argv_of: Callable[[str], list[str]], env: Mapping[str, str], log_dir: Path) -> None:
    """(f) 艦隊のログを集めて落とす。落とす段の失敗は ``fleet_stop_failed`` に記録する(例外は外へ出さない)。"""
    if not needs_fleet:
        return
    if dry_run:
        steps.append(Step("艦隊を落とす", status="skipped", detail="dry-run", argv=argv_of("stop")))
        return
    if not fleet_started:
        return
    try:
        if (fleet_cfg.get("collect_log") or {}).get("argv"):
            st = Step("艦隊のログを集める", argv=argv_of("collect_log"))
            steps.append(st)
            with StepTimer(st):
                rc, o, e, why = run_logged("fleet_log", st.argv, cwd=REPO, env=env,
                                           timeout_s=float(fleet_cfg["collect_log"].get("timeout_s", 60)),
                                           log_dir=log_dir)
                st.returncode = rc
                st.logs = [rel_or_abs(o), rel_or_abs(e)]
                st.status = "ok" if rc == 0 else "failed"
                st.detail = why
    except Exception as exc:  # noqa: BLE001 - ログが集まらなくても落とす
        steps.append(Step("艦隊のログを集める", status="failed", detail=f"{type(exc).__name__}: {exc}"))
    if keep_fleet:
        state["fleet_left_running"] = True
        steps.append(Step("艦隊を落とす", status="skipped", detail="--keep-fleet"))
        return
    st = Step("艦隊を落とす", argv=argv_of("stop"))
    steps.append(st)
    try:
        with StepTimer(st):
            rc, o, e, why = run_logged("fleet_stop", st.argv, cwd=REPO, env=env,
                                       timeout_s=float((fleet_cfg.get("stop") or {}).get("timeout_s", 120)),
                                       log_dir=log_dir)
            st.returncode = rc
            st.logs = [rel_or_abs(o), rel_or_abs(e)]
            st.status = "ok" if rc == 0 else "failed"
            st.detail = why or ("" if rc == 0 else f"終了コード {rc}")
            if bg_proc is not None and bg_proc.poll() is None:
                bg_proc.terminate()
                try:
                    bg_proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    bg_proc.kill()
                st.detail = (st.detail + "・背後の起動を止めた").strip("・")
    except Exception as exc:  # noqa: BLE001
        st.status = "failed"
        st.detail = f"{type(exc).__name__}: {exc}"
    if st.status == "failed":
        state["fleet_stop_failed"] = True
        if state.get("result") == RESULT_OK:
            state["result"] = RESULT_OK_CLEANUP_FAILED


def _finish(*, run_dir: Path, out_root: Path, state: dict[str, Any], cfg: Mapping[str, Any], exp: Mapping[str, Any],
            steps: list[Step], vars_: Mapping[str, Any], m0: float, dry_run: bool, main_stdout: Path | None,
            main_stdout_name: str, health: Mapping[str, Any] | None) -> None:
    """(e)(g) 計測の一覧・要約・印・1 行の記録を書く。どの失敗の道でも 5 本と 1 行を必ず書く。"""
    errors: list[str] = []
    state.setdefault("result", RESULT_FAILED)
    wall = time.monotonic() - m0
    unreadable: dict[str, str] = {}
    outs = exp.get("outputs") or {}

    def _resolve(key: str, default: str) -> Path:
        q = Path(expand_str(str(outs.get(key, default)), vars_))
        return q if q.is_absolute() else REPO / q

    cp_js = None
    cp_path = _resolve("checkpoints", "{{DATA}}/checkpoints.json")
    tape_path = _resolve("tape", "{{DATA}}/tape")
    try:
        if cp_path.exists():
            cp_js = json.loads(cp_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        unreadable["checkpoints"] = type(exc).__name__
        cp_js = None
    tape = None
    try:
        tape = read_tape(tape_path)
    except Exception as exc:  # noqa: BLE001 - footer の無い途中のファイルなど
        unreadable["tape"] = type(exc).__name__
    so_text = ""
    try:
        if main_stdout is not None and main_stdout.exists():
            so_text = main_stdout.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        unreadable["stdout"] = type(exc).__name__
    try:
        metrics = build_metrics(stdout_text=so_text, stdout_name=main_stdout_name, checkpoints=cp_js,
                                checkpoints_name=rel_or_abs(cp_path), tape=tape, tape_name=rel_or_abs(tape_path),
                                night_wall_seconds=None if dry_run else round(wall, 1),
                                sim_days=int(exp.get("sim_days", 1) or 1),
                                yen_per_hour=(cfg.get("cost") or {}).get("yen_per_hour"),
                                health=health if health and "pending" not in health else None,
                                unreadable=unreadable)
    except Exception as exc:  # noqa: BLE001
        metrics = {"schema": "night5070/metrics/2", "fields": [], "n_measured": 0, "n_unmeasured": 0,
                   "error": f"{type(exc).__name__}: {exc}", "unreadable": unreadable}
        errors.append(f"計測の一覧: {type(exc).__name__}")
    try:
        so = parse_stdout(so_text)
        if "fleet" in so:
            state["calls_text"] = f"発射 {so['fleet']['fired']:,}・繰り延べ {so['fleet']['deferred']:,}" + (
                f"・{so['calls_per_agent_day']} 呼/体/日" if "calls_per_agent_day" in so else "")
        elif "llm_calls" in so:
            state["calls_text"] = f"{so['llm_calls']:,} 呼({so['calls_per_agent_day']} 呼/体/日)"
    except Exception as exc:  # noqa: BLE001
        errors.append(f"呼数: {type(exc).__name__}")
    state.update({"ended": _stamp(_now()), "wall_seconds": round(wall, 1),
                  "n_measured": metrics.get("n_measured", 0), "n_unmeasured": metrics.get("n_unmeasured", 0),
                  "steps": [asdict(s) for s in steps], "unreadable": unreadable})

    def _w(name: str, make: Callable[[], str]) -> None:
        try:
            (run_dir / name).write_text(mask_paths(make()), encoding="utf-8", newline="\n")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {type(exc).__name__}")

    _w("metrics.json", lambda: json.dumps(metrics, ensure_ascii=False, indent=1, default=str) + "\n")
    _w("metrics.md", lambda: metrics_markdown(metrics) if metrics.get("fields") else
       f"# 計測の分離の一覧\n\n作れなかった: {metrics.get('error', '')}\n")
    state["finish_errors"] = list(errors)
    try:
        write_summary(run_dir, state, cfg)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"summary.md: {type(exc).__name__}")
        state["finish_errors"] = list(errors)
        try:
            _fallback_summary(run_dir, state, exc)
        except Exception:  # noqa: BLE001
            pass
    _w("night_run.json", lambda: json.dumps(state, ensure_ascii=False, indent=1, default=str) + "\n")
    _w("NIGHT_DONE", lambda: f"{state['result']}\n")
    try:
        line = mask_paths(f"{state['started']}\t{state['experiment']}\t{state['result']}\t{state['run_dir']}\n")
        with io.FileIO(out_root / "_night_runs.log", "a") as fa:
            fa.write(line.encode("utf-8"))
    except Exception:  # noqa: BLE001
        pass
    try:
        print(mask_paths(f"night_run: {state['experiment']} {state['result']} → {state['run_dir']}/summary.md"))
    except Exception:  # noqa: BLE001
        pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="5070 の夜の実験を 1 コマンドで回す(回答 10-25 §6-0)")
    ap.add_argument("--experiment", required=True, help="実験の名(設定の experiments の鍵・例 E1)")
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="設定の JSON(既定 tools/night5070/experiments.json)")
    ap.add_argument("--out", type=Path, default=None,
                    help="小さな記録の根(既定 docs/bench/night5070・相対はリポの根から)")
    ap.add_argument("--data-out", type=Path, default=None,
                    help="大きな出力とログの根(既定 data/night5070=gitignore の中・相対はリポの根から)")
    ap.add_argument("--dry-run", action="store_true", help="艦隊を立てずコマンドも回さず、何をするかを並べて要約を書く")
    ap.add_argument("--keep-fleet", action="store_true", help="終わっても艦隊を落とさない(朝に手で落とす)")
    ap.add_argument("--deadline-hours", type=float, default=None,
                    help="全体の締め切り[時間](既定=設定の deadline_hours=9.5。タスクからは上限 − 0.5 が渡る)")
    ap.add_argument("--start-at", default=None, help="予定の開始の時刻 HH:MM(要約の終わりの時刻の表に使う)")
    args = ap.parse_args(argv)
    cfg_path = args.config if args.config.is_absolute() else (Path.cwd() / args.config)
    if not cfg_path.exists():
        cfg_path = REPO / args.config
    return run_night(args.experiment, config_path=cfg_path, out_root=args.out, data_root=args.data_out,
                     dry_run=args.dry_run, keep_fleet=args.keep_fleet, deadline_hours=args.deadline_hours,
                     start_at=args.start_at)


if __name__ == "__main__":
    raise SystemExit(main())
