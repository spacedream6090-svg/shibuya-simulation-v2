#!/usr/bin/env python3
"""気象庁「過去の気象データ検索」(etrn)の東京(prec_no=44・block_no=47662)を日ごとに取り、表にする。

第330 B5(W13 の年間化・答え 10-12b 1-3)。**取得は ``www.data.jma.go.jp`` だけ**(CLAUDE.md §7 の公的ドメインの例外)。
転送(3xx)は追わない=転送先が別ドメインでも同じドメインでも、その頁は取らずに止めて報告する。

    python tools/realworld_fetch/jma_etrn.py fetch --kind 10min --start 2025-09-01 --end 2026-08-31
    python tools/realworld_fetch/jma_etrn.py fetch --kind hourly --start 2025-09-01 --end 2026-08-31
    python tools/realworld_fetch/jma_etrn.py table --kind 10min --start 2025-09-01 --end 2026-08-31
    python tools/realworld_fetch/jma_etrn.py table --kind hourly --start 2025-09-01 --end 2026-08-31

- 頁の置き場: 時別値 ``data/realworld/jma_etrn/raw/tokyo47662_<日付>.html``(前回 35 日と同じ名前)・
  10 分値 ``data/realworld/jma_etrn/raw10min/tokyo47662_10min_<日付>.html``。手元にある頁は取り直さない。
- 間隔: 2 秒に 1 回(``--interval``)。
- 頁ごとの md5・取得時刻(UTC)・URL・バイト数を ``data/realworld/jma_etrn/MANIFEST_<kind>.tsv`` に追記する。
- ``table`` は頁の表(``id='tablefix1'``)のセルからタグを除いた文字列をそのまま CSV にする(値の記号
  ``--``・``×``・``)``・``]``・空欄は**加工しない**=読み手の ``w13_weather._etrn_num`` が解く)。
  時別値の CSV の列は前回(2026-09-08・親の手取り)の CSV と同じ。
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "data" / "realworld" / "jma_etrn"
HOST = "www.data.jma.go.jp"
URL = {
    "hourly": "https://www.data.jma.go.jp/stats/etrn/view/hourly_s1.php?prec_no=44&block_no=47662&year={y}&month={m}&day={d}&view=p1",
    "10min": "https://www.data.jma.go.jp/stats/etrn/view/10min_s1.php?prec_no=44&block_no=47662&year={y}&month={m}&day={d}&view=p1",
}
RAW_DIR = {"hourly": ROOT / "raw", "10min": ROOT / "raw10min"}
RAW_NAME = {"hourly": "tokyo47662_{date}.html", "10min": "tokyo47662_10min_{date}.html"}
USER_AGENT = "shibuya-simulation/rw-fetch/1.0 (research use; non-commercial; attribution kept)"

#: 時別値の CSV の列(前回の CSV と同じ順)。頁の列: 時・気圧(現地・海面)・降水量・気温・露点温度・蒸気圧・
#: 湿度・風速・風向・日照時間・全天日射量・雪(降雪・積雪)・天気・雲量・視程。
HOURLY_COLS = (
    "date", "hour", "pressure_local_hpa", "pressure_sea_hpa", "precip_mm", "temp_c", "dewpoint_c",
    "vapor_hpa", "rh_pct", "wind_ms", "wind_dir", "sunshine_h", "solar_mj_m2", "snowfall_cm",
    "snowdepth_cm", "weather", "cloud", "visibility_km",
)
#: 10 分値の CSV の列。頁の列: 時分・気圧(現地・海面)・降水量・気温・相対湿度・平均風速・風向・
#: 最大瞬間風速・風向・日照時間(分)。
TENMIN_COLS = (
    "date", "time", "pressure_local_hpa", "pressure_sea_hpa", "precip_mm", "temp_c", "rh_pct",
    "wind_ms", "wind_dir", "gust_ms", "gust_dir", "sunshine_min",
)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        raise urllib.error.HTTPError(req.full_url, code, f"redirect to {newurl}", headers, fp)


_OPENER = urllib.request.build_opener(_NoRedirect)


def _days(start: str, end: str) -> list[dt.date]:
    a, b = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    return [a + dt.timedelta(days=i) for i in range((b - a).days + 1)]


def page_url(kind: str, d: dt.date) -> str:
    url = URL[kind].format(y=d.year, m=d.month, d=d.day)
    assert urllib.parse.urlsplit(url).hostname == HOST
    return url


def raw_path(kind: str, d: dt.date) -> Path:
    return RAW_DIR[kind] / RAW_NAME[kind].format(date=d.isoformat())


def table_cells(html: str) -> list[list[str]]:
    """``id='tablefix1'`` の表 → 行ごとのセル(タグを除いた文字列)。"""
    i = html.find("tablefix1")
    if i < 0:
        raise ValueError("表 tablefix1 が無い")
    t = html[i : html.find("</table>", i)]
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S)
    out = []
    for r in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)
        out.append([re.sub(r"<[^>]+>", "", c).strip() for c in cells])
    return out


def data_rows(kind: str, html: str) -> list[list[str]]:
    """見出し行を除いたデータ行(時別値は 24 行・10 分値は 144 行)。"""
    rows = table_cells(html)
    n = len(HOURLY_COLS) - 1 if kind == "hourly" else len(TENMIN_COLS) - 1
    body = [r for r in rows if len(r) == n and re.fullmatch(r"\d{1,2}(:\d{2})?", r[0] or "")]
    want = 24 if kind == "hourly" else 144
    if len(body) != want:
        raise ValueError(f"{kind} のデータ行が {len(body)} 行(期待 {want})")
    return body


def cmd_fetch(args: argparse.Namespace) -> int:
    RAW_DIR[args.kind].mkdir(parents=True, exist_ok=True)
    manifest = ROOT / f"MANIFEST_{args.kind}.tsv"
    new = 0
    last = 0.0
    for d in _days(args.start, args.end):
        p = raw_path(args.kind, d)
        if p.exists():
            continue
        url = page_url(args.kind, d)
        wait = args.interval - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with _OPENER.open(req, timeout=60) as resp:
                status = resp.status
                final = resp.geturl()
                body = resp.read()
        except urllib.error.HTTPError as e:
            print(f"STOP {d} HTTP {e.code} {e.msg}(転送は追わない・取得せず報告)", file=sys.stderr)
            return 2
        if status != 200 or urllib.parse.urlsplit(final).hostname != HOST:
            print(f"STOP {d} status={status} host={urllib.parse.urlsplit(final).hostname}", file=sys.stderr)
            return 2
        html = body.decode("utf-8")
        data_rows(args.kind, html)  # 表が壊れていれば保存せずに止める
        p.write_bytes(body)
        md5 = hashlib.md5(body).hexdigest()
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with manifest.open("a", encoding="utf-8", newline="\n") as f:
            f.write(f"{d.isoformat()}\t{md5}\t{len(body)}\t{stamp}\t{url}\n")
        new += 1
        if new % 30 == 0:
            print(f"{args.kind} {d} new={new}", flush=True)
    print(f"done {args.kind} new={new}", flush=True)
    return 0


def cmd_table(args: argparse.Namespace) -> int:
    cols = HOURLY_COLS if args.kind == "hourly" else TENMIN_COLS
    out = ROOT / f"tokyo47662_{args.kind}_{args.start}_{args.end}.csv"
    n = 0
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for d in _days(args.start, args.end):
            html = raw_path(args.kind, d).read_text(encoding="utf-8")
            for r in data_rows(args.kind, html):
                w.writerow([d.isoformat(), *r])
                n += 1
    print(f"{out.name} rows={n}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("fetch", "table"):
        sp = sub.add_parser(name)
        sp.add_argument("--kind", choices=("hourly", "10min"), required=True)
        sp.add_argument("--start", required=True)
        sp.add_argument("--end", required=True)
        if name == "fetch":
            sp.add_argument("--interval", type=float, default=2.0)
    args = ap.parse_args(argv)
    return cmd_fetch(args) if args.cmd == "fetch" else cmd_table(args)


if __name__ == "__main__":
    raise SystemExit(main())
