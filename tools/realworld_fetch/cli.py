#!/usr/bin/env python3
"""RW-U1 日次オーケストレータ: 1 コマンドで全ソースを取得し、台帳を1本にまとめる。

  python scripts/rw_fetch_daily.py --offline     # ドライラン(**HTTP要求 0 本**・キー不要)
  python scripts/rw_fetch_daily.py               # 日次(アメダス+WBGT+防災XML)
  python scripts/rw_fetch_daily.py --source all  # 上記 + 渋谷区人流(初回のみ) + ODPT RT
  python scripts/rw_fetch_daily.py --report      # 取得台帳レポート(未取得日・odpt_rt の欠けた時間帯・ディスクの量。ネット不使用)
  python scripts/rw_fetch_daily.py --verify      # 保存済みファイルのスキーマ検証(.json と .json.gz・ネット不使用)
  python scripts/rw_fetch_daily.py --backfill    # アメダスの未取得日を保持10日ぶん後追い取得
  python scripts/rw_fetch_daily.py --source odpt_static           # ODPT オープン枠の静的データの版を 1 回取る(第333)
  python scripts/rw_fetch_daily.py --source odpt_static --check   # 新しい版がある operator × 種類の一覧(保存しない)

設計の要点:
  - `--offline` / `--report` / `--verify` は **ネットワークに一切出ない**(テストで固定)。
  - 部分失敗しても続行し、失敗も台帳に残す(黙って止まらない・黙って埋めない)。
  - リクエスト間に礼儀的 sleep、User-Agent 明示、リトライは指数バックオフ小回数。
  - 実行の終わりの台帳のレポート(未取得日の検出)は、日次のソース(amedas・wbgt・jma_xml)を
    頼んだときだけ出す。odpt_rt(5 分ごとのタスク)と odpt_static では出さない(台帳は 1 日に
    数千行ずつ増えるので毎回の全読みを避ける・関係の無い URGENT を出さない。第333)。
"""
from __future__ import annotations

import argparse
import os
from datetime import date as _date
from pathlib import Path

from . import amedas, common, jma_xml, ledger, logrotate, odpt_rt, odpt_static, shibuya_jinryu, wbgt

ALL_SOURCES = ("amedas", "wbgt", "shibuya_jinryu", "odpt_rt", "odpt_static", "jma_xml")
DAILY_SOURCES = ("amedas", "wbgt", "jma_xml")   # 毎日回す既定(R1 の10日期限が効くのはここ)
# `--source all` が展開する先。odpt_static(版の取得=数百要求)は名前で指定したときだけ回す。
ALL_EXPANDS = ("amedas", "wbgt", "shibuya_jinryu", "odpt_rt", "jma_xml")

ROOT_README = """# 現実世界データの静的凍結置き場(`tools/realworld_fetch/` の出力)

`tools/realworld_fetch/` が書き込む取得結果です。**シミュ本体(`src/`)はここを一切読みません。**
用途はパラメータ較正(ラン前)と事後検証(ラン後)のみで、**状態同化はしていません**。

- 設計・エンドポイント・ライセンスの一次資料: `docs/research/rw-data-acquisition.md`
- 取得台帳: `_ledger.jsonl`(1行1レコード。未取得日・odpt_rt の欠けた時間帯・ディスクの量は `--report`)
- **このディレクトリは .gitignore 済み**(コミットしない)

## 出典表示(成果物に必ず載せるもの)

| ソース | 表記 |
|---|---|
| amedas / jma_xml | 出典: 気象庁ホームページ(公共データ利用規約1.0・加工した旨も明記) |
| wbgt | 出典: 環境省熱中症予防情報サイト |
| shibuya_jinryu | 渋谷区オープンデータ(CC BY 4.0)／データ提供: KDDI・技研商事インターナショナル「KDDI Location Analyzer」 |
| odpt_rt / odpt_static | 本データは公共交通オープンデータセンターのデータを利用して作成(リアルタイム表示時は生成時刻を併記) |

## ODPT(odpt_rt/ と odpt_static/)

- `odpt_rt/`: 運行情報・列車の在線・バスの在線。**オープン枠は提供のある事業者の全路線**を、
  **チャレンジ枠は作品に使う範囲だけ**(東急 2 線と京王 井の頭線の運行情報・JR 3 線の在線)を、
  gzip した JSON(`.json.gz`)で保存する。チャレンジ枠の用途は応募作品に限られる
  (チャレンジ限定ライセンス 第 4 条 1 項)。詳しくは `odpt_rt/README.md`。
- `odpt_static/<取得日>/`: オープン枠の静的データ(時刻表・駅・路線・バス停と系統・乗降人員・運賃)の
  版。ダイヤ改正ごとに 1 回取る(古い版は API から消える)。新しい版の有無は `--source odpt_static --check`。
- どちらも第三者が再利用できる形での公開・再配布をしない(基本ライセンス・限定ライセンス 第 8 条 4 項(1))。

## 欠測の扱い

**欠測を偽の値で埋めていません。** 欠測セルは `null`、件数は各ファイルの
`_meta.n_missing`、取得できなかった対象は `_ledger.jsonl` に失敗行として残ります。
"""


def ensure_root_readme(root: Path) -> Path:
    path = Path(root) / "README.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != ROOT_README:
        path.write_text(ROOT_README, encoding="utf-8", newline="\n")
    return path


# ------------------------------------------------------------------ offline(計画表示)
def build_plan(sources, d: _date) -> list[tuple[str, str]]:
    """取得予定 (説明, URL)。**ネットワークには出ない**(キーも読まない)。"""
    plan: list[tuple[str, str]] = []
    if "amedas" in sources:
        plan += amedas.plan_day(d)
    if "wbgt" in sources:
        plan += wbgt.plan_day(d)
    if "shibuya_jinryu" in sources:
        plan += shibuya_jinryu.plan()
    if "odpt_rt" in sources:
        plan += odpt_rt.plan()
    if "odpt_static" in sources:
        plan += odpt_static.plan()
    if "jma_xml" in sources:
        plan += jma_xml.plan()
    return plan


def print_plan(sources, d: _date, root: Path) -> None:
    plan = build_plan(sources, d)
    common.log("=" * 72)
    common.log(f"RW 取得予定(--offline / 対象日 {d.isoformat()} JST)")
    common.log(f"保存先: {root}")
    common.log("=" * 72)
    for desc, url in plan:
        common.log(f"  - {desc}")
        common.log(f"      {common.scrub(url)}")
    common.log("")
    common.log(f"予定リクエスト数: {len(plan)}  (--offline のため 1 本も送っていません)")
    if "odpt_static" in sources:
        common.log("  (odpt_static は operator の一覧を取ってから operator × 種類を 1 本ずつ問い合わせ、"
                   "1,000 件の打ち切りに当たった区画は分けて取り直すので、実際の要求数は数百本)")
    for env in (odpt_rt.OPEN_KEY_ENV, odpt_rt.CHALLENGE_KEY_ENV):
        common.log(f"[offline] {env}: "
                   f"{'設定済み' if os.environ.get(env) else '未設定(またはプロセス外)'}"
                   "(値は表示しません)")
    common.log(f"[offline] HTTP要求 {common.request_count()} 本")


# ------------------------------------------------------------------ verify(ネット不使用)
def _saved_documents(root: Path):
    root = Path(root)
    paths = sorted(set(root.glob("**/*.json")) | set(root.glob("**/*.json.gz")))
    for path in paths:
        if path.name.startswith("_"):
            continue
        yield path


def verify(root: Path) -> tuple[int, int, list[str]]:
    """保存済み JSON(`.json` と `.json.gz`)の `_meta` スキーマを検証する。

    戻り値 = (合格数, 検査数, 問題)。
    """
    problems: list[str] = []
    n_ok = n_all = 0
    for path in _saved_documents(root):
        n_all += 1
        try:
            doc = common.read_json_any(path)
        except (ValueError, OSError, EOFError) as exc:
            problems.append(f"{path}: JSON として読めない ({type(exc).__name__})")
            continue
        probs = common.validate_document(doc)
        if probs:
            problems += [f"{path}: {p}" for p in probs]
        else:
            n_ok += 1
    return n_ok, n_all, problems


# ------------------------------------------------------------------ 実取得
def _split_list(value) -> list[str] | None:
    if not value:
        return None
    out = [p.strip() for p in str(value).split(",") if p.strip()]
    return out or None


def run_sources(root: Path, sources, d: _date, args) -> tuple[list[dict], int]:
    """要求されたソースを順に取得する。戻り値 = (台帳行, 失敗ソース数)。"""
    rows: list[dict] = []
    n_failed_sources = 0
    for src in ALL_SOURCES:
        if src not in sources:
            continue
        common.log(f"[{src}] 取得開始")
        before = len(rows)
        try:
            if src == "amedas":
                _, r = amedas.fetch_day(root, d, timeout=args.timeout, retries=args.retries,
                                        sleep=args.sleep)
                rows += r
                if args.backfill:
                    for miss in amedas.missing_days(root, d):
                        common.log(f"  [amedas] backfill {miss.isoformat()}")
                        _, r2 = amedas.fetch_day(root, miss, timeout=args.timeout,
                                                 retries=args.retries, sleep=args.sleep,
                                                 today=d)
                        rows += r2
            elif src == "wbgt":
                _, r = wbgt.fetch_day(root, d, timeout=args.timeout, retries=args.retries,
                                      sleep=args.sleep, save_raw=not args.no_raw)
                rows += r
            elif src == "shibuya_jinryu":
                _, r = shibuya_jinryu.fetch_all(root, d, timeout=args.timeout,
                                                retries=args.retries, sleep=args.sleep,
                                                force=args.force, save_raw=not args.no_raw)
                rows += r
            elif src == "odpt_rt":
                for i in range(max(1, args.repeat)):
                    _, r = odpt_rt.fetch_snapshot(root, timeout=args.timeout,
                                                  retries=args.retries, sleep=args.sleep,
                                                  force=args.force)
                    rows += r
                    if i < args.repeat - 1:
                        common.polite_sleep(args.interval)
            elif src == "odpt_static":
                ops = _split_list(args.operators)
                types = _split_list(args.static_types)
                if args.survey:
                    _, r = odpt_static.survey(root, operators=ops,
                                              types=types or odpt_static.SURVEY_TYPES,
                                              timeout=args.timeout, retries=args.retries,
                                              sleep=args.sleep)
                    common.log(f"  [odpt_static] 洗い出しの表: {odpt_static.SOURCE}/_survey_*.json")
                elif args.check:
                    rep, r = odpt_static.check(root, operators=ops, types=types,
                                               timeout=args.timeout, retries=args.retries,
                                               sleep=args.sleep)
                    common.log(odpt_static.format_check(rep))
                else:
                    _, r = odpt_static.fetch_version(root, operators=ops, types=types,
                                                     timeout=args.timeout,
                                                     retries=args.retries, sleep=args.sleep)
                rows += r
            elif src == "jma_xml":
                _, r = jma_xml.fetch_all(root, timeout=args.timeout, retries=args.retries,
                                         sleep=args.sleep, save_raw=args.save_xml)
                rows += r
        except Exception as exc:            # 1ソースの事故で全体を止めない
            rows.append(ledger.make_entry(src, "run", ok=False, date_jst=d.isoformat(),
                                          error=f"{type(exc).__name__}: {exc}"))
            common.log(f"  [{src}] 例外: {type(exc).__name__}: {exc}", err=True)
        new = rows[before:]
        n_ok = sum(1 for x in new if x.get("ok"))
        if new and n_ok == 0:
            n_failed_sources += 1
        n_unch = sum(1 for x in new if (x.get("extra") or {}).get("unchanged"))
        common.log(f"[{src}] 完了 ok={n_ok}/{len(new)} "
                   f"records={sum(int(x.get('n_records') or 0) for x in new)} "
                   f"missing={sum(int(x.get('n_missing') or 0) for x in new)}"
                   + (f" unchanged={n_unch}" if n_unch else ""))
    return rows, n_failed_sources


# ------------------------------------------------------------------ CLI
def _sources_from_args(values) -> list[str]:
    if not values:
        return list(DAILY_SOURCES)
    out: list[str] = []
    for v in values:
        for part in str(v).split(","):
            part = part.strip()
            if not part:
                continue
            if part == "all":
                out += list(ALL_EXPANDS)
            elif part == "daily":
                out += list(DAILY_SOURCES)
            elif part in ALL_SOURCES:
                out.append(part)
            else:
                raise SystemExit(f"未知のソース: {part} (選択肢: {', '.join(ALL_SOURCES)}, all, daily)")
    return [s for s in ALL_SOURCES if s in set(out)]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rw_fetch_daily.py",
        description="現実世界データの日次取得(RW-U1)。"
                    "APIキーは環境変数からのみ読み、値は一切出力しない。")
    p.add_argument("--source", action="append", default=None,
                   help=f"取得ソース(複数可・カンマ可)。{', '.join(ALL_SOURCES)} / all / daily"
                        f"(既定: {', '.join(DAILY_SOURCES)}。all は odpt_static を含まない)")
    p.add_argument("--date", default=None, help="対象日 YYYY-MM-DD(既定: 今日 JST)")
    p.add_argument("--out-dir", default=str(common.DEFAULT_ROOT), help="保存先ルート")
    p.add_argument("--offline", action="store_true",
                   help="ドライラン。取得予定を表示するだけで HTTP 要求を 1 本も出さない")
    p.add_argument("--report", action="store_true",
                   help="取得台帳のレポート(未取得日・odpt_rt の欠けた時間帯・ディスクの量)。"
                        "ネットワーク不使用")
    p.add_argument("--verify", action="store_true",
                   help="保存済みファイル(.json と .json.gz)のスキーマ検証。ネットワーク不使用")
    p.add_argument("--check", action="store_true",
                   help="odpt_static: 保存済みの最新版と API の dct:issued を比べ、新しい版がある "
                        "operator × 種類を一覧にする(保存しない)")
    p.add_argument("--survey", action="store_true",
                   help="odpt_static: オープン枠の operator × 種類の件数・バイト・日付の範囲の表を作る"
                        "(データの値は保存しない。--static-types で種類を絞れる)")
    p.add_argument("--operators", default=None,
                   help="odpt_static: operator を絞る(カンマ区切り。例 odpt.Operator:Toei)")
    p.add_argument("--static-types", default=None,
                   help="odpt_static: 種類を絞る(カンマ区切り。例 odpt:Railway,odpt:Station)")
    p.add_argument("--backfill", action="store_true",
                   help="アメダスの未取得日(保持10日以内)を後追い取得する")
    p.add_argument("--force", action="store_true",
                   help="既取得でも取り直す(渋谷区人流など低頻度ソース向け)。"
                        "odpt_rt では種類ごとの間隔を無視して全部取る")
    p.add_argument("--repeat", type=int, default=1, help="ODPT リアルタイムのスナップショット回数")
    p.add_argument("--interval", type=float, default=90.0,
                   help="ODPT リアルタイムの間隔秒(既定 90 = dct:valid 5分を尊重)")
    p.add_argument("--sleep", type=float, default=1.0, help="リクエスト間の礼儀的待機秒")
    p.add_argument("--timeout", type=float, default=30.0, help="1リクエストのタイムアウト秒")
    p.add_argument("--retries", type=int, default=2, help="リトライ回数(指数バックオフ)")
    p.add_argument("--no-raw", action="store_true", help="CSV 等の生ファイルを保存しない")
    p.add_argument("--save-xml", action="store_true", help="防災情報XML の生 XML も保存する")
    p.add_argument("--lookback", type=int, default=30, help="--report の遡り日数")
    p.add_argument("--rotate-logs", action="store_true",
                   help="台帳 _ledger.jsonl とタスクのログ(_scheduler_odpt.log・_scheduler.log)を今すぐ回して "
                        "gzip する(_logs/ の下へ・書き手が開いていれば次の回へ)。ネットワーク不使用。"
                        "通常の取得の回でも、その日にまだ回していないものを回す(第337)")
    return p


def full_report(root: Path, rows, d: _date, sources, lookback: int, now=None) -> str:
    """`--report` の全文(未取得日・odpt_rt の欠けた時間帯・ディスクの量)。ネット不使用。"""
    parts = [ledger.format_report(rows, d, sources=sources, lookback_days=lookback)]
    if any(isinstance(r, dict) and r.get("source") == odpt_rt.SOURCE for r in rows):
        parts.append(ledger.format_rt_report(rows, d, now=now, lookback_days=lookback,
                                             cadence=odpt_rt.CADENCE))
    parts.append(ledger.format_disk_report(root, d))
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    common.reconfigure_stdio()
    args = build_parser().parse_args(argv)
    root = Path(args.out_dir)
    sources = _sources_from_args(args.source)
    d = common.parse_date(args.date) if args.date else common.now_jst().date()

    if args.report:
        rows = ledger.read_all(root)
        common.log(full_report(root, rows, d, sources, args.lookback))
        return 0

    if args.rotate_logs:
        res = logrotate.maybe_rotate(root, force=True)
        common.log(logrotate.format_results(res))
        return 1 if any(r.get("status") == "error" for r in res) else 0

    if args.verify:
        n_ok, n_all, problems = verify(root)
        for p in problems:
            common.log(f"[NG] {p}", err=True)
        common.log(f"[verify] スキーマ合格 {n_ok}/{n_all} 件")
        return 1 if problems else 0

    if args.offline:
        print_plan(sources, d, root)
        return 0

    ensure_root_readme(root)
    rows, n_failed = run_sources(root, sources, d, args)
    ledger.append(root, rows)

    if any(s in ledger.DAILY_SOURCES for s in sources):
        all_rows = ledger.read_all(root)
        common.log("")
        common.log(ledger.format_report(all_rows, d, sources=[s for s in sources
                                                              if s in ledger.DAILY_SOURCES],
                                        lookback_days=args.lookback))
    n_ok = sum(1 for r in rows if r.get("ok"))
    common.log("")
    common.log(f"[done] 台帳へ {len(rows)} 行追記(成功 {n_ok})。HTTP要求 {common.request_count()} 本。")
    _rotate_quietly(root)
    return 1 if n_failed else 0


def _rotate_quietly(root: Path) -> None:
    """〔第337〕その日にまだ回していない台帳とログを回す(取得の回を止めない=何が起きても飲み込んで 1 行だけ出す)。"""
    try:
        res = logrotate.maybe_rotate(root, tries=1)
    except Exception as exc:  # noqa: BLE001 - 回しの失敗で取得を落とさない
        common.log(f"[rotate] 回せなかった({type(exc).__name__})", err=True)
        return
    # 書き手が開いている(busy)ものは次の回で回す=ログに毎回書かない(ODPT の回は自分のログを開いたまま走る)
    shown = [r for r in res if r.get("status") != "busy"]
    if shown:
        common.log(logrotate.format_results(shown))


if __name__ == "__main__":   # pragma: no cover - 通常は scripts/rw_fetch_daily.py から起動
    raise SystemExit(main())
