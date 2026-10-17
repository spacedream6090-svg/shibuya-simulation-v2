#!/usr/bin/env python3
"""取得の台帳とログを日ごとに回して gzip で縮める(第337・回答 10-13b §7 の 5・§5 追記「保存するときに圧縮」)。

対象(`root` の直下・`LOGS`):
- `_ledger.jsonl`(台帳=UTF-8 の JSON Lines。`ledger.append` が書く)
- `_scheduler_odpt.log`(ODPT のタスクの PowerShell の `*>>` が書く=UTF-16)
- `_scheduler.log`(日次のタスクの同じ形のログ)

回し方(書き手を止めない・原子的な置き換え)
1. 回す側どうしは錠 `_logs/.rotate.lock`(排他の作成・古い錠は `LOCK_STALE_S` 秒で外す)で 1 つに絞る。
2. 生きているファイルを `<名>.rotating.<rotid>` へ `os.replace` で改名する。Windows では書き手が開いている間は
   改名が失敗する(共有違反)ので、そのときは何もせずに次の回へ回す(書き手は止めない・行は失わない)。
   改名の後に来た書き手は、新しい空のファイルを作って追記する(`open(..., "a")` が作る)。
3. 改名したファイルのバイト列を日ごとの塊に分け(台帳は行の `ts_utc` の JST の日・日は前へ戻らない
   =塊は元の並びのまま連続・ログは最後に書かれた日 1 つ)、塊ごとに gzip を一時の名で書いてから
   `os.replace` で `_logs/<YYYY-MM>/<名>.<日>.r<rotid>.p<k>.gz` に置く。
4. 置いた gz を全部ほどき、つないだバイト列が改名したファイルと 1 バイトも違わないことを確かめてから、
   改名したファイルを消す。確かめが通らなければ gz を消して改名したファイルを残す(次の回でやり直す)。
5. 途中で落ちたときは `<名>.rotating.<rotid>` が残る。次の回の最初にそれを片付ける(その rotid の gz を
   消してから 3〜4 をやり直す)。読み手は、`rotating` の残っている rotid の gz を使わず `rotating` を読む
   =同じ行を 2 度読まない。

読み口: :func:`read_bytes_all` / :func:`read_text_all`(gz → 残った rotating → 生きているファイルの順=元の並び)。
台帳の読み手 `ledger.read_all` はこれを通す。

いつ回すか: :func:`maybe_rotate` が取得の道具の通常の回(`cli.main` の最後)で、その日にまだ回していない
ファイルを回す(状態は `_logs/_rotate_state.json`)。開いている(=書いている最中の)ファイルは次の回へ。
ODPT のタスクは自分のログ `_scheduler_odpt.log` を開いたまま走るので、そのログは日次のタスクの回で回る。
手で回すのは `--rotate-logs`。

逐次ループ宣言(P4): 行の数ぶん(台帳を日に分けるとき 1 回)。体の数に比例するループは無い。
"""
from __future__ import annotations

import contextlib
import gzip
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from . import common

ARCHIVE_DIR = "_logs"
LOCK_NAME = ".rotate.lock"
STATE_NAME = "_rotate_state.json"
ROTATING_TAG = ".rotating."
#: 錠がこの秒より古ければ、落ちた回の残りとみなして外す(1 回の回しは数秒)。
LOCK_STALE_S = 600.0


@dataclass(frozen=True)
class LogSpec:
    name: str
    encoding: str           # 行を数えるときの符号化(回すのはバイトのまま)
    line_days: bool         # True=行の ts_utc で日に分ける(台帳)/ False=最後に書かれた日 1 つ(ログ)


LOGS: tuple[LogSpec, ...] = (
    LogSpec("_ledger.jsonl", "utf-8", True),
    LogSpec("_scheduler_odpt.log", "utf-16", False),
    LogSpec("_scheduler.log", "utf-16", False),
)
_SPEC: Mapping[str, LogSpec] = MappingProxyType({s.name: s for s in LOGS})
_ARCH_RE = re.compile(r"^(?P<name>.+)\.(?P<day>\d{4}-\d{2}-\d{2})\.r(?P<rotid>\d{8}T\d{12}Z)\.p(?P<part>\d+)\.gz$")
_ROT_RE = re.compile(r"^(?P<name>.+)\.rotating\.(?P<rotid>\d{8}T\d{12}Z)$")


class RotateBusy(RuntimeError):
    """書き手がファイルを開いている(改名できない)か、ほかの回しが錠を持っている。"""


def spec_of(name: str) -> LogSpec:
    return _SPEC.get(name) or LogSpec(name, "utf-8", False)


def _rotid(now: datetime | None = None) -> str:
    dt = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%S") + f"{dt.microsecond:06d}Z"


def _jst_day_of_ts(ts: str | None) -> str | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(common.JST).date().isoformat()


# ------------------------------------------------------------------ 置き場の一覧
def archive_root(root: Path) -> Path:
    return Path(root) / ARCHIVE_DIR


def archives(root: Path, name: str) -> list[tuple[str, str, int, Path]]:
    """`name` の gz の一覧 (rotid, 日, 塊の番, 道筋)。並び=元の並び(rotid → 塊の番)。"""
    out = []
    base = archive_root(root)
    if not base.is_dir():
        return out
    for sub in base.iterdir():
        if not sub.is_dir():
            continue
        for p in sub.iterdir():
            m = _ARCH_RE.match(p.name)
            if m and m["name"] == name:
                out.append((m["rotid"], m["day"], int(m["part"]), p))
    return sorted(out, key=lambda t: (t[0], t[2]))


def pending(root: Path, name: str) -> list[tuple[str, Path]]:
    """途中で落ちた回しの残り (rotid, 道筋)。"""
    out = []
    for p in Path(root).glob(f"{name}{ROTATING_TAG}*"):
        m = _ROT_RE.match(p.name)
        if m and m["name"] == name:
            out.append((m["rotid"], p))
    return sorted(out)


# ------------------------------------------------------------------ 読み口
#: 読みの途中で回しが走ったときに一覧を取り直す回数(〔検収 L3〕)。
READ_RETRIES = 3


def _listing(root: Path, name: str) -> tuple:
    return (tuple(p.name for *_x, p in archives(root, name)), tuple(p.name for _r, p in pending(root, name)))


def _chunks_once(root: Path, name: str) -> list[bytes]:
    pend = dict(pending(root, name))
    items: list[tuple[str, int, Path, bool]] = []
    for rotid, _day, part, p in archives(root, name):
        if rotid not in pend:
            items.append((rotid, part, p, True))
    for rotid, p in pend.items():
        items.append((rotid, 0, p, False))
    out = [gzip.decompress(p.read_bytes()) if gz else p.read_bytes()
           for _rotid, _part, p, gz in sorted(items, key=lambda t: (t[0], t[1]))]
    live = Path(root) / name
    if live.exists():
        out.append(live.read_bytes())
    return out


def iter_chunks(root: Path, name: str) -> list[bytes]:
    """元の並びでバイト列を返す: gz(残った rotating の rotid は除く)→ 残った rotating → 生きているファイル。

    〔検収 L3〕読み手は錠を取らない。読みの途中で回しが走る(生きているファイルが改名される=``FileNotFoundError``・
    一覧の後に gz が増える)と読み落としうるので、読む前と後で一覧が違うか ``FileNotFoundError`` なら一覧を取り直して
    やり直す(``READ_RETRIES`` 回まで)。
    """
    for i in range(READ_RETRIES + 1):
        before = _listing(root, name)
        try:
            out = _chunks_once(root, name)
        except FileNotFoundError:
            if i >= READ_RETRIES:
                raise
            continue
        if _listing(root, name) == before or i >= READ_RETRIES:
            return out
    raise FileNotFoundError(name)  # pragma: no cover - 上で返すか投げる


def read_bytes_all(root: Path, name: str) -> bytes:
    return b"".join(iter_chunks(root, name))


def _decode(b: bytes, encoding: str) -> str:
    if encoding == "utf-16":
        # PowerShell の `*>>` は UTF-16 LE(先頭に BOM)。回した後の新しいファイルも BOM から始まる
        return b.decode("utf-16-le", "replace").replace("﻿", "")
    return b.decode(encoding)


def read_text_all(root: Path, name: str, encoding: str | None = None) -> str:
    enc = encoding or spec_of(name).encoding
    return "".join(_decode(c, enc) for c in iter_chunks(root, name))


def count_lines(root: Path, name: str) -> int:
    return len(read_text_all(root, name).splitlines())


# ------------------------------------------------------------------ 錠
def _clear_stale(lk: Path) -> None:
    """〔検収 L4〕古い錠の掃除。``os.replace`` で別名へ移せた側だけが進む(移せなかった=ほかの回しが先に動いた
    → ``RotateBusy``)。移したものが古くなかった(見た後にほかの回しが新しい錠を作っていた)ときは元の名へ戻して
    ``RotateBusy``(新しい錠を消さない)。"""
    grave = lk.with_name(f"{lk.name}.stale.{os.getpid()}.{time.time_ns()}")
    try:
        os.replace(lk, grave)
    except FileNotFoundError:
        raise RotateBusy("古い錠はほかの回しが片付けた") from None
    try:
        age = time.time() - grave.stat().st_mtime
    except OSError:
        age = LOCK_STALE_S + 1
    if age <= LOCK_STALE_S:
        with contextlib.suppress(OSError):
            os.replace(grave, lk)
        raise RotateBusy("ほかの回しが新しい錠を作っていた")
    with contextlib.suppress(OSError):
        os.remove(grave)


@contextlib.contextmanager
def _lock(root: Path):
    d = archive_root(root)
    d.mkdir(parents=True, exist_ok=True)
    lk = d / LOCK_NAME
    for _ in range(2):
        try:
            fd = os.open(lk, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                age = time.time() - lk.stat().st_mtime
            except OSError:
                continue
            if age > LOCK_STALE_S:
                _clear_stale(lk)  # 移せた側だけが進む(移せなければ RotateBusy)
                continue
            raise RotateBusy("ほかの回しが錠を持っている")
        else:
            break
    else:
        raise RotateBusy("錠が取れない")
    try:
        os.write(fd, f"{os.getpid()} {time.time():.0f}\n".encode("ascii"))
        os.close(fd)
        yield
    finally:
        with contextlib.suppress(OSError):
            os.remove(lk)


# ------------------------------------------------------------------ 分けて書く
def split_days(data: bytes, spec: LogSpec, fallback_day: str) -> list[tuple[str, bytes]]:
    """バイト列を日ごとの連続した塊に分ける(つなぐと元と同じ)。日は前へ戻らない(戻る行は前の日の塊に残す)。"""
    if not spec.line_days:
        return [(fallback_day, data)] if data else []
    out: list[tuple[str, bytearray]] = []
    mark: str | None = None
    for ln in data.splitlines(keepends=True):  # 逐次: 行の数ぶん
        day = None
        with contextlib.suppress(ValueError, AttributeError, TypeError):
            day = _jst_day_of_ts(json.loads(ln.decode("utf-8")).get("ts_utc"))
        if day is None or (mark is not None and day < mark):
            day = mark or fallback_day
        if mark is None or day != mark:
            out.append((day, bytearray()))
            mark = day
        out[-1][1].extend(ln)
    return [(d, bytes(b)) for d, b in out]


def _gz(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9, mtime=0)


def wait_writers(fh) -> None:
    """POSIX: 改名の前に開いていた書き手の追記が終わるまで待つ(``ledger.append`` は追記の間 flock を持ち、
    取った後に自分の手の内のファイルが今の名のファイルと同じかを確かめて、違えば開き直す)。Windows では
    開いている間は改名そのものが失敗するので待つ必要がない。"""
    if os.name == "nt":
        return
    import fcntl

    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)


def _archive(root: Path, name: str, rot: Path, rotid: str) -> dict:
    """改名したファイル `rot` を gz に書き、ほどいて元と同じかを確かめてから `rot` を消す。"""
    spec = spec_of(name)
    with open(rot, "rb") as fh:
        wait_writers(fh)
        data = fh.read()
    fallback = datetime.fromtimestamp(rot.stat().st_mtime, common.JST).date().isoformat()
    chunks = split_days(data, spec, fallback)
    written: list[Path] = []
    try:
        for k, (day, b) in enumerate(chunks):
            sub = archive_root(root) / day[:7]
            sub.mkdir(parents=True, exist_ok=True)
            final = sub / f"{name}.{day}.r{rotid}.p{k}.gz"
            tmp = sub / f".{final.name}.tmp"
            with open(tmp, "wb") as fh:
                fh.write(_gz(b))
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, final)
            written.append(final)
        back = b"".join(gzip.decompress(p.read_bytes()) for p in written)
        if back != data:
            raise OSError("ほどいた gz が元と違う")
    except BaseException:
        for p in written:
            with contextlib.suppress(OSError):
                os.remove(p)
        raise
    os.remove(rot)
    return {"name": name, "rotid": rotid, "bytes_in": len(data),
            "bytes_out": sum(p.stat().st_size for p in written),
            "lines": len(_decode(data, spec.encoding).splitlines()),
            "days": [d for d, _ in chunks], "archives": [p.name for p in written]}


def _recover(root: Path, name: str) -> list[dict]:
    out = []
    for rotid, rot in pending(root, name):
        for r, _d, _k, p in archives(root, name):
            if r == rotid:
                os.remove(p)
        out.append(_archive(root, name, rot, rotid))
    return out


def rotate_one(root: Path, name: str, *, now: datetime | None = None, tries: int = 5,
               wait_s: float = 0.2) -> dict:
    """1 本を回す。戻り値 = 結果(``status`` = rotated / empty / busy)。"""
    root = Path(root)
    with _lock(root):
        recovered = _recover(root, name)
        live = root / name
        if not live.exists() or live.stat().st_size == 0:
            return {"name": name, "status": "empty", "recovered": recovered}
        rotid = _rotid(now)
        rot = root / f"{name}{ROTATING_TAG}{rotid}"
        for i in range(max(1, tries)):
            try:
                os.replace(live, rot)
                break
            except PermissionError:  # 書き手が開いている(Windows の共有違反)
                if i + 1 >= tries:
                    return {"name": name, "status": "busy", "recovered": recovered}
                time.sleep(wait_s)
        res = _archive(root, name, rot, rotid)
        res.update(status="rotated", recovered=recovered)
        return res


def _read_state(root: Path) -> dict:
    p = archive_root(root) / STATE_NAME
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_state(root: Path, state: dict) -> None:
    d = archive_root(root)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / f".{STATE_NAME}.tmp"
    tmp.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, d / STATE_NAME)


def maybe_rotate(root: Path, *, today: str | None = None, names=None, force: bool = False,
                 tries: int = 3) -> list[dict]:
    """その日にまだ回していないものを回す(``force`` なら日に依らず回す)。失敗しても取得の回を止めない。"""
    root = Path(root)
    day = today or common.now_jst().date().isoformat()
    names = list(names or [s.name for s in LOGS])
    state = _read_state(root)
    out: list[dict] = []
    for name in names:
        if not force and state.get(name, "") >= day:
            continue
        try:
            res = rotate_one(root, name, tries=tries)
        except RotateBusy as exc:
            out.append({"name": name, "status": "busy", "why": str(exc)})
            continue
        except OSError as exc:
            out.append({"name": name, "status": "error", "why": type(exc).__name__})
            continue
        out.append(res)
        if res["status"] in ("rotated", "empty"):
            state[name] = day
    with contextlib.suppress(OSError):
        _write_state(root, state)
    return out


def format_results(results: list[dict]) -> str:
    lines = []
    for r in results:
        if r.get("status") == "rotated":
            lines.append(f"[rotate] {r['name']}: {r['lines']} 行・{r['bytes_in']:,} B → gz {r['bytes_out']:,} B"
                         f"({len(r['archives'])} 塊・日 {r['days'][0]}〜{r['days'][-1]})")
        else:
            lines.append(f"[rotate] {r['name']}: {r.get('status')}" + (f"({r['why']})" if r.get("why") else ""))
    return "\n".join(lines)
