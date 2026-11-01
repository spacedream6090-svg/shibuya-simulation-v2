#!/usr/bin/env python3
"""RW-U1 取得台帳: いつ・何を・何件・欠測いくつ・HTTP ステータス を1行ずつ追記する。

`docs/research/rw-data-acquisition.md` リスク **R9(取得漏れの静かな蓄積)** の対策。
`data/realworld/_ledger.jsonl` に **1行1レコードで追記**(JSON Lines = 途中で落ちても
既存行が壊れない)。研究文書は `_ledger.json` と書いているが、R9 本文の「1行ずつ追記」に
忠実な JSONL を採る(読む側は `read_all` を通せば同じ)。

最重要の機能は **未取得日の検出**。アメダスは保持 **10 日**(実測・リスク R1)なので、
「まだ間に合う欠け(URGENT)」と「もう二度と取れない欠け(LOST)」を分けて報告する。
"""
from __future__ import annotations

import json
from datetime import date as _date
from datetime import timedelta
from pathlib import Path

from . import common

LEDGER_NAME = "_ledger.jsonl"

# ソース別の後追い可能日数(None = 期限なし)。docs/research/rw-data-acquisition.md §4-2。
RETENTION_DAYS: dict[str, int | None] = {
    "amedas": 10,        # 実測: point/{id}/{date}_{HH}.json は 10 日で 404
    "wbgt": None,        # 実況は月初からの累積 = 月内なら後追い可
    "wbgt_forecast": 0,  # 予測は上書きされる = その日に取らないと消える
    "shibuya_jinryu": None,
    "odpt_rt": 0,        # dct:valid=5分。後追い不可
    "odpt_static": None, # 版はダイヤ改正ごと。古い版は API から消える(後追いは今の版だけ)
    "jma_xml": 3,        # 長期フィードは「数日分」を掲載
    # ↓ P4 境界較正の静的ソース。5年に1度/年1回の更新なので期限の概念が無い(日次対象外)。
    "transport_census": None,
    "odpt_passenger_survey": None,
}

# 日次実行で毎日取れているべきソース(未取得日の検出対象)。
DAILY_SOURCES = ("amedas", "wbgt", "jma_xml")


def ledger_path(root: Path) -> Path:
    return Path(root) / LEDGER_NAME


def make_entry(source: str, target: str, *, ok: bool, http_status=None, n_records: int = 0,
               n_missing: int = 0, path: str | None = None, error: str | None = None,
               date_jst: str | None = None, ts_utc: str | None = None,
               extra: dict | None = None) -> dict:
    """台帳1行。`date_jst` は「そのデータが属する日」(取得日ではない)。"""
    row = {
        "ts_utc": ts_utc or common.iso_utc(),
        "date_jst": date_jst or common.now_jst().date().isoformat(),
        "source": source,
        "target": common.scrub(target),
        "ok": bool(ok),
        "http_status": http_status,
        "n_records": int(n_records),
        "n_missing": int(n_missing),
        "path": common.scrub(path) if path else None,
        "error": common.scrub(error) if error else None,
    }
    if extra:
        row["extra"] = extra
    return row


def append(root: Path, rows) -> int:
    """台帳へ追記する。戻り値 = 書いた行数。**追記のみ・既存行は決して書き換えない。**"""
    if isinstance(rows, dict):
        rows = [rows]
    rows = list(rows)
    if not rows:
        return 0
    path = ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for row in rows:
        text = common.scrub(json.dumps(row, ensure_ascii=False, sort_keys=True))
        lines.append(text)
    _append_text(path, "\n".join(lines) + "\n")
    return len(rows)


#: 追記の開き直しの回数と間(台帳を回す `logrotate` の改名とぶつかったとき)。
APPEND_TRIES = 200
APPEND_WAIT_S = 0.01


def _same_file(fh, path: Path) -> bool:
    """POSIX: 追記の錠(flock)を取り、手の内のファイルが今の名のファイルと同じか(回しに改名されていないか)。

    Windows では開いている間は改名できない(共有違反)ので常に同じ。"""
    import os

    if os.name == "nt":
        return True
    import fcntl

    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
    try:
        return os.fstat(fh.fileno()).st_ino == os.stat(path).st_ino
    except FileNotFoundError:
        return False


def _append_text(path: Path, text: str) -> None:
    """1 回の追記。台帳を回す側(`logrotate`)と並んでも行を失わない(第337)。

    - Windows: 回す側が改名している瞬間は開けない(PermissionError)ので、少し待って開き直す。
    - POSIX: 開いた後に回す側が改名していたら(手の内が今の名と違う)、閉じて開き直す。
    """
    import time

    for _ in range(APPEND_TRIES):
        try:
            fh = path.open("a", encoding="utf-8", newline="\n")
        except PermissionError:
            time.sleep(APPEND_WAIT_S)
            continue
        with fh:
            if _same_file(fh, path):
                fh.write(text)
                return
    raise PermissionError(f"台帳へ追記できない(回しとぶつかり続けた): {path.name}")


def read_all(root: Path) -> list[dict]:
    """台帳を読む。壊れた行は捨てずに `{"_broken": 生テキスト}` として返す(黙って消さない)。

    〔第337〕回した台帳(`_logs/` の gz と、途中で落ちた回しの残り)も元の並びで読む(`logrotate.read_text_all`)。
    """
    from . import logrotate

    path = ledger_path(root)
    if not path.exists() and not logrotate.archives(root, LEDGER_NAME) and not logrotate.pending(root, LEDGER_NAME):
        return []
    out: list[dict] = []
    for line in logrotate.read_text_all(root, LEDGER_NAME, "utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            out.append({"_broken": line})
            continue
        out.append(obj if isinstance(obj, dict) else {"_broken": line})
    return out


# ------------------------------------------------------------------ 集計
def ok_days(rows, source: str) -> set[str]:
    """そのソースで **成功した** 日(date_jst)の集合。"""
    return {r.get("date_jst") for r in rows
            if r.get("source") == source and r.get("ok") and r.get("date_jst")}


def day_status(rows, source: str, day: str) -> str:
    """`ok` / `partial` / `failed` / `missing`。

    `partial` = 成功行はあるが `extra.complete` が False(アメダスの 8 ブロックが揃っていない等)。
    """
    same = [r for r in rows if r.get("source") == source and r.get("date_jst") == day]
    if not same:
        return "missing"
    oks = [r for r in same if r.get("ok")]
    if not oks:
        return "failed"
    completes = [r.get("extra", {}).get("complete") for r in oks]
    if any(c is True for c in completes):
        return "ok"
    if any(c is False for c in completes):
        return "partial"
    return "ok"


def missing_days(rows, source: str, start: _date, end: _date) -> list[str]:
    """start..end のうち `ok` でない日(= partial / failed / missing)を返す。"""
    return [d.isoformat() for d in common.date_range(start, end)
            if day_status(rows, source, d.isoformat()) != "ok"]


def gap_report(rows, source: str, today: _date, *, lookback_days: int = 30) -> dict:
    """未取得日を「まだ間に合う(URGENT)」と「もう取れない(LOST)」に分けて返す。

    保持期間 `RETENTION_DAYS[source]` を超えた欠けは後追いできない = LOST。
    当日(today)は取得途中でありうるので `pending` として別に数える。
    """
    retention = RETENTION_DAYS.get(source)
    start = today - timedelta(days=lookback_days)
    urgent, lost, pending, partial = [], [], [], []
    for d in common.date_range(start, today):
        day = d.isoformat()
        st = day_status(rows, source, day)
        if st == "ok":
            continue
        if d == today:
            pending.append(day)
            continue
        if st == "partial":
            partial.append(day)
        age = (today - d).days
        if retention is None:
            urgent.append(day)
        elif age <= retention:
            urgent.append(day)
        else:
            lost.append(day)
    return {
        "source": source,
        "today": today.isoformat(),
        "retention_days": retention,
        "lookback_days": lookback_days,
        "urgent": urgent,       # まだ後追い取得できる欠け → 今すぐ取る
        "lost": lost,           # 保持期間を過ぎた欠け → 二度と取れない(正直に記録するだけ)
        "partial": partial,     # 成功はしたが不完全な日
        "pending": pending,     # 当日(まだ途中でありうる)
        "n_ok": len(ok_days(rows, source)),
    }


def summary(rows) -> dict:
    """ソース別の件数・最終成功時刻・失敗件数。"""
    out: dict[str, dict] = {}
    for r in rows:
        src = r.get("source")
        if not src:
            continue
        s = out.setdefault(src, {"n_rows": 0, "n_ok": 0, "n_fail": 0, "n_records": 0,
                                 "n_missing": 0, "last_ok_utc": None, "errors": {}})
        s["n_rows"] += 1
        s["n_records"] += int(r.get("n_records") or 0)
        s["n_missing"] += int(r.get("n_missing") or 0)
        if r.get("ok"):
            s["n_ok"] += 1
            ts = r.get("ts_utc")
            if ts and (s["last_ok_utc"] is None or ts > s["last_ok_utc"]):
                s["last_ok_utc"] = ts
        else:
            s["n_fail"] += 1
            key = str(r.get("error") or r.get("http_status") or "unknown")
            s["errors"][key] = s["errors"].get(key, 0) + 1
    return out


def format_report(rows, today: _date, *, sources=None, lookback_days: int = 30) -> str:
    """人が読む取得台帳レポート(`--report`)。ネットワーク不使用。"""
    sources = list(sources or DAILY_SOURCES)
    summ = summary(rows)
    lines = ["=" * 72,
             f"RW 取得台帳レポート (今日 = {today.isoformat()} JST / 全 {len(rows)} 行)",
             "=" * 72]
    if not rows:
        lines.append("台帳が空。まだ一度も取得していない。")
        return "\n".join(lines)
    lines.append("")
    lines.append(f"{'source':<16}{'rows':>6}{'ok':>6}{'fail':>6}{'records':>10}"
                 f"{'missing':>9}  last_ok_utc")
    for src in sorted(summ):
        s = summ[src]
        lines.append(f"{src:<16}{s['n_rows']:>6}{s['n_ok']:>6}{s['n_fail']:>6}"
                     f"{s['n_records']:>10}{s['n_missing']:>9}  {s['last_ok_utc'] or '-'}")
        if s["errors"]:
            errs = ", ".join(f"{k}×{v}" for k, v in sorted(s["errors"].items()))
            lines.append(f"{'':<16}  失敗内訳: {errs}")
    lines.append("")
    lines.append("-" * 72)
    lines.append("未取得日の検出(★アメダスは保持10日 = 過ぎたら永久に取れない)")
    lines.append("-" * 72)
    n_urgent = n_lost = 0
    for src in sources:
        rep = gap_report(rows, src, today, lookback_days=lookback_days)
        n_urgent += len(rep["urgent"])
        n_lost += len(rep["lost"])
        ret = "無期限" if rep["retention_days"] is None else f"{rep['retention_days']}日"
        lines.append(f"[{src}] 保持={ret}")
        if rep["urgent"]:
            lines.append(f"  ⚠ URGENT 今すぐ後追い取得できる欠け {len(rep['urgent'])} 日: "
                         + ", ".join(rep["urgent"]))
        if rep["lost"]:
            lines.append(f"  ✖ LOST 保持期間切れで回復不能 {len(rep['lost'])} 日: "
                         + ", ".join(rep["lost"]))
        if rep["partial"]:
            lines.append(f"  △ PARTIAL 不完全な日 {len(rep['partial'])} 日: "
                         + ", ".join(rep["partial"]))
        if not (rep["urgent"] or rep["lost"] or rep["partial"]):
            lines.append("  OK 欠けなし")
    lines.append("")
    lines.append(f"合計: URGENT {n_urgent} 日 / LOST {n_lost} 日")
    if n_urgent:
        lines.append("→ `python scripts/rw_fetch_daily.py --backfill` で後追い取得できる。")
    return "\n".join(lines)


# ================================================================ odpt_rt の欠けた時間帯(第333)
# 取得はユーザーの PC が動いている間しか回らない。止まっていた時間帯を台帳から数える(ネット不使用)。
RT_SOURCE = "odpt_rt"
RT_TYPES = ("odpt:TrainInformation", "odpt:Train", "odpt:Bus")
RT_TYPE_LABEL = {"odpt:TrainInformation": "運行情報", "odpt:Train": "在線", "odpt:Bus": "バス"}
_RT_TARGET_TYPE = {"TrainInformation": "odpt:TrainInformation", "Train": "odpt:Train",
                   "Bus": "odpt:Bus"}
# 同じ種類の行が何秒以内なら 1 回のスナップショットとみなすか(`snapshot_jst` の無い古い行用)。
SNAPSHOT_CLUSTER_S = 60


def _parse_iso(text):
    if not isinstance(text, str) or not text:
        return None
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=common.JST)
    return dt.astimezone(common.JST)


def rt_row_time(row: dict):
    """行の時刻(JST)。`extra.snapshot_jst` があればそれ、無ければ `ts_utc`。"""
    ex = row.get("extra") if isinstance(row.get("extra"), dict) else {}
    return _parse_iso(ex.get("snapshot_jst")) or _parse_iso(row.get("ts_utc"))


def rt_row_type(row: dict) -> str | None:
    ex = row.get("extra") if isinstance(row.get("extra"), dict) else {}
    if ex.get("datatype") in RT_TYPES:
        return ex["datatype"]
    head = str(row.get("target") or "").split("/", 1)[0]
    return _RT_TARGET_TYPE.get(head)


def _count_snapshots(times) -> int:
    """時刻の並びを `SNAPSHOT_CLUSTER_S` 秒の隙間で区切った塊の数。"""
    ts = sorted(times)
    n = 0
    prev = None
    for t in ts:
        if prev is None or (t - prev).total_seconds() > SNAPSHOT_CLUSTER_S:
            n += 1
        prev = t
    return n


def _hour_runs(hours: list[int]) -> list[tuple[int, int]]:
    """欠けた時(0..23)の並びを、連続した区間 (始め, 終わり) にまとめる。"""
    runs: list[tuple[int, int]] = []
    for h in sorted(hours):
        if runs and h == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], h)
        else:
            runs.append((h, h))
    return runs


def rt_gap_report(rows, today: _date, *, now=None, lookback_days: int = 30,
                  cadence: dict | None = None) -> dict:
    """odpt_rt の日ごとの「取得の無かった 1 時間の枠」と、種類ごとのスナップショット数。

    - 期間の始まりは `today - lookback_days` と、odpt_rt の最初の行の日の遅い方
      (集め始める前の日を欠けと数えない)。最初の日は最初の行の時から数える。
    - 今日は、いまの時より前の(終わった)枠だけを数える。
    - 期待するスナップショット数 = 数えた時間 × 3600 / 間隔(今の `cadence`)。
    """
    now = now or common.now_jst()
    cadence = dict(cadence or {t: 300 for t in RT_TYPES})
    rt = [r for r in rows if isinstance(r, dict) and r.get("source") == RT_SOURCE]
    out = {"days": [], "total_missing_hours": 0, "n_days": 0, "first_day": None,
           "window_start": None, "window_end": today.isoformat()}
    timed = [(rt_row_time(r), r) for r in rt]
    timed = [(t, r) for t, r in timed if t is not None]
    if not timed:
        return out
    first_t = min(t for t, _ in timed)
    first_day = first_t.date()
    start = max(today - timedelta(days=lookback_days), first_day)
    out["first_day"] = first_day.isoformat()
    out["window_start"] = start.isoformat()

    ok_hours: dict[str, set[int]] = {}
    any_hours: dict[str, set[int]] = {}
    snap_times: dict[tuple[str, str], list] = {}
    capped: dict[tuple[str, str], int] = {}
    for t, r in timed:
        day = t.date().isoformat()
        any_hours.setdefault(day, set()).add(t.hour)
        if not r.get("ok"):
            continue
        ok_hours.setdefault(day, set()).add(t.hour)
        dt = rt_row_type(r)
        if dt:
            snap_times.setdefault((day, dt), []).append(t)
            ex = r.get("extra") if isinstance(r.get("extra"), dict) else {}
            if ex.get("capped"):
                capped[(day, dt)] = capped.get((day, dt), 0) + 1

    for d in common.date_range(start, today):
        day = d.isoformat()
        h0 = first_t.hour if d == first_day else 0
        h1 = 24
        if d == now.date():
            h1 = now.hour
        elif d > now.date():
            h1 = h0
        expected_hours = list(range(h0, max(h0, h1)))
        covered = ok_hours.get(day, set())
        missing = [h for h in expected_hours if h not in covered]
        fail_only = [h for h in missing if h in any_hours.get(day, set())]
        snaps = {dt: _count_snapshots(snap_times.get((day, dt), [])) for dt in RT_TYPES}
        expected = {dt: int(round(len(expected_hours) * 3600 / max(1, int(cadence.get(dt, 300)))))
                    for dt in RT_TYPES}
        out["days"].append({
            "day": day, "hours_counted": len(expected_hours), "hours_missing": len(missing),
            "gaps": [(f"{a:02d}:00", f"{b:02d}:59") for a, b in _hour_runs(missing)],
            "fail_only_hours": len(fail_only), "snapshots": snaps, "expected": expected,
            "capped_rows": {dt: capped.get((day, dt), 0) for dt in RT_TYPES},
        })
        out["total_missing_hours"] += len(missing)
    out["n_days"] = len(out["days"])
    return out


def format_rt_report(rows, today: _date, *, now=None, lookback_days: int = 30,
                     cadence: dict | None = None) -> str:
    rep = rt_gap_report(rows, today, now=now, lookback_days=lookback_days, cadence=cadence)
    lines = ["", "-" * 72,
             "ODPT リアルタイム(odpt_rt)の欠けた時間帯(1 時間の枠・JST・取得の成功が無い枠)",
             "-" * 72]
    if not rep["days"]:
        lines.append("odpt_rt の行が台帳に無い。")
        return "\n".join(lines)
    for day in rep["days"]:
        snaps = "  ".join(f"{RT_TYPE_LABEL[dt]} {day['snapshots'][dt]}/{day['expected'][dt]}"
                          for dt in RT_TYPES)
        gaps = ", ".join(f"{a}-{b}" for a, b in day["gaps"]) or "なし"
        fail = f"(うち失敗だけの枠 {day['fail_only_hours']})" if day["fail_only_hours"] else ""
        lines.append(f"  {day['day']}  欠けた枠 {day['hours_missing']}/{day['hours_counted']}"
                     f"{fail}  欠け {gaps}")
        lines.append(f"              スナップショット(実際/期待) {snaps}")
        cap = {dt: n for dt, n in day["capped_rows"].items() if n}
        if cap:
            lines.append("              ⚠ 1,000 件の打ち切りが残った行 "
                         + "  ".join(f"{RT_TYPE_LABEL[dt]} {n}" for dt, n in cap.items()))
    lines.append("")
    lines.append(f"合計: 欠け {rep['total_missing_hours']} 時間 / {rep['n_days']} 日"
                 f"({rep['window_start']}〜{rep['window_end']}。最初の日は最初の取得の時から、"
                 "今日は終わった枠だけ)")
    return "\n".join(lines)


# ================================================================ ディスクの量(第333)
RT_FILE_PREFIX = (("traininformation_", "運行情報"), ("train_", "在線"), ("bus_", "バス"))


def _category(rel_parts: tuple[str, ...]) -> str:
    if len(rel_parts) == 1:
        return "(直下のファイル: 台帳・ログ)"
    top = rel_parts[0]
    if top == RT_SOURCE:
        name = rel_parts[-1]
        for pre, label in RT_FILE_PREFIX:
            if name.startswith(pre):
                return f"{RT_SOURCE}/{label}"
        return f"{RT_SOURCE}/その他"
    return top


def _day_of(rel_parts: tuple[str, ...], mtime: float) -> str:
    for p in reversed(rel_parts[:-1]):
        if len(p) == 10 and p[4] == "-" and p[7] == "-" and p.replace("-", "").isdigit():
            return p
    from datetime import datetime
    return datetime.fromtimestamp(mtime, common.JST).date().isoformat()


def disk_usage(root: Path, today: _date, *, days: int = 7) -> dict:
    """`root` の下のファイルの大きさを種類ごとに足す(中身は読まない)。

    日は道筋の `YYYY-MM-DD` の段(無ければ更新時刻の日)。直近 `days` 日(今日を除く)の
    1 日あたりの増え方と、その 365 倍の年の見込みを出す。
    """
    import os

    root = Path(root)
    cats: dict[str, dict] = {}
    window = {(today - timedelta(days=i)).isoformat() for i in range(1, days + 1)}
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            it = os.scandir(cur)
        except OSError:
            continue
        with it:
            for e in it:
                try:
                    if e.is_dir(follow_symlinks=False):
                        stack.append(Path(e.path))
                        continue
                    stt = e.stat(follow_symlinks=False)
                except OSError:
                    continue
                rel = Path(e.path).relative_to(root).parts
                cat = _category(rel)
                c = cats.setdefault(cat, {"files": 0, "bytes": 0, "window_bytes": 0,
                                          "today_bytes": 0})
                c["files"] += 1
                c["bytes"] += stt.st_size
                day = _day_of(rel, stt.st_mtime)
                if day in window:
                    c["window_bytes"] += stt.st_size
                elif day == today.isoformat():
                    c["today_bytes"] += stt.st_size
    for c in cats.values():
        c["per_day_bytes"] = c["window_bytes"] / days
        c["per_year_gb"] = c["per_day_bytes"] * 365 / 1e9
    return {"root_name": root.name, "days": days, "categories": cats}


def _pad(text: str, width: int) -> str:
    """全角を 2 桁と数えて左寄せで埋める(表の桁をそろえる)。"""
    import unicodedata

    w = sum(2 if unicodedata.east_asian_width(c) in ("F", "W") else 1 for c in text)
    return text + " " * max(0, width - w)


def format_disk_report(root: Path, today: _date, *, days: int = 7) -> str:
    rep = disk_usage(root, today, days=days)
    lines = ["", "-" * 72,
             f"ディスクの量(ファイルの大きさだけ・中身は読まない。増え方は今日を除く直近 {days} 日の平均)",
             "-" * 72,
             _pad("種類", 30) + f"{'files':>9}{'total_MB':>11}{'MB/day':>9}{'GB/yr':>8}{'today_MB':>9}"]
    tot = {"files": 0, "bytes": 0, "per_day_bytes": 0.0, "today_bytes": 0}
    for cat in sorted(rep["categories"]):
        c = rep["categories"][cat]
        lines.append(_pad(cat, 30) + f"{c['files']:>9}{c['bytes'] / 1e6:>11.1f}"
                     f"{c['per_day_bytes'] / 1e6:>9.2f}{c['per_year_gb']:>8.2f}"
                     f"{c['today_bytes'] / 1e6:>9.2f}")
        for k in tot:
            tot[k] += c[k]
    lines.append(_pad("合計", 30) + f"{tot['files']:>9}{tot['bytes'] / 1e6:>11.1f}"
                 f"{tot['per_day_bytes'] / 1e6:>9.2f}{tot['per_day_bytes'] * 365 / 1e9:>8.2f}"
                 f"{tot['today_bytes'] / 1e6:>9.2f}")
    return "\n".join(lines)
