#!/usr/bin/env python3
"""夜の実験をタスクスケジューラに登録する(回答 10-25 §6-0 の 2)。

    python tools/night5070/register_task.py --at 01:00 --experiment E1 [--name shibuya-v2-night5070] [--wake]
    python tools/night5070/register_task.py --at 01:00 --experiment E1 --print-only   # XML とコマンドを出すだけ
    python tools/night5070/register_task.py --delete [--name shibuya-v2-night5070]

登録の方式は ODPT の取得タスク(``\\shibuya-v2-rw-fetch-odpt``・docs/bench/analysis/wallbounce-1003/
realworld-fetch-check.md §5-2)と同じ: タスクの XML(UTF-16)を作り ``schtasks /create /tn … /xml … /f``。
実行するユーザーは登録したユーザー・対話のログオンのときだけ(Interactive only=WSL2 はユーザーのセッションで動く)。

条件(ODPT のタスクとの違い): 電池で動いているときも始める・電池に切り替わっても止めない
(``DisallowStartIfOnBatteries=false``・``StopIfGoingOnBatteries=false``)。``StartWhenAvailable=true``
(時刻に止まっていたら後で始める)・多重起動は無視・実行時間の上限は ``--max-hours``(既定 10 時間)・
``WakeToRun`` は ``--wake`` のときだけ true。

既定は 1 回だけ(次の ``--at`` の時刻)。``--daily`` で毎日。起動は ODPT のタスクと同じ形:

    powershell.exe -NoProfile -WindowStyle Hidden -Command "Set-Location '<リポの根>'; & '<python>'
        tools/night5070/night_run.py --experiment <E> --deadline-hours <上限 − 0.5> --start-at <HH:MM>
        *>> docs/bench/night5070/_scheduler.log"

リポの根はこのスクリプトの位置から、python は ``sys.executable`` から求めて XML に書く(登録先は手元の OS
なので、ユーザー名を含む絶対パスが XML に入るのはよい)。``--print-only`` の表示ではホームを ``<HOME>`` に
置き換える。このスクリプトのファイル自身には絶対パスを書かない。
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_NAME = "shibuya-v2-night5070"
DEFAULT_MAX_HOURS = 10
#: night_run の締め切りをタスクの上限より短くする幅[時間](艦隊を落とす時間を残す)。
DEADLINE_MARGIN_HOURS = 0.5
DEFAULT_LOG_ROOT = "docs/bench/night5070"
TASK_NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"


def next_start(at: str, now: dt.datetime | None = None) -> dt.datetime:
    """``HH:MM`` → 次にその時刻になる日時(今より後)。"""
    m = re.fullmatch(r"([01]?[0-9]|2[0-3]):([0-5][0-9])", at.strip())
    if not m:
        raise ValueError(f"--at は HH:MM(例 01:00): {at!r}")
    now = now or dt.datetime.now()
    t = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
    if t <= now:
        t += dt.timedelta(days=1)
    return t


def _ps_quote(s: str) -> str:
    """PowerShell の単一引用符の文字列(中の ' は '' にする)。"""
    return "'" + str(s).replace("'", "''") + "'"


def night_args(experiment: str, *, deadline_hours: float, start_at: str | None = None, config: str | None = None,
               out: str | None = None) -> list[str]:
    """night_run.py に渡す引数(リポの根からの相対の道筋だけ)。"""
    args = ["tools/night5070/night_run.py", "--experiment", experiment, "--deadline-hours", f"{deadline_hours:g}"]
    if start_at:
        args += ["--start-at", start_at]
    if config:
        args += ["--config", config]
    if out:
        args += ["--out", out]
    return args


def ps_arguments(*, python: str, workdir: str, night: list[str], log_root: str = DEFAULT_LOG_ROOT) -> str:
    """powershell.exe の Arguments(ODPT のタスクと同じ形・ログは log_root/_scheduler.log に足す)。"""
    inner = (f"Set-Location {_ps_quote(workdir)}; "
             f"New-Item -ItemType Directory -Force -Path {_ps_quote(log_root)} | Out-Null; "
             f"& {_ps_quote(python)} " + " ".join(_ps_quote(a) if (" " in a or "'" in a) else a for a in night)
             + f" *>> {_ps_quote(log_root + '/_scheduler.log')}")
    return f'-NoProfile -WindowStyle Hidden -Command "{inner}"'


def mask_home(text: str, *, xml: bool = False) -> str:
    """表示用にホームの道筋を ``<HOME>`` に置き換える(XML の中では ``&lt;HOME&gt;``=読むと ``<HOME>``)。"""
    rep = "&lt;HOME&gt;" if xml else "<HOME>"
    for h in sorted({str(Path.home()), Path.home().as_posix()}, key=len, reverse=True):
        text = text.replace(h, rep)
    return text


def build_xml(*, experiment: str, start: dt.datetime, wake: bool = False, daily: bool = False,
              max_hours: int = DEFAULT_MAX_HOURS, deadline_hours: float | None = None, python: str | None = None,
              workdir: str | None = None, config: str | None = None, out: str | None = None,
              start_at: str | None = None) -> str:
    """タスクの XML(文字列)。書き出すときは UTF-16。締め切りが上限以上なら ValueError。"""
    python = python or sys.executable
    workdir = workdir or str(REPO)
    dl = float(max_hours) - DEADLINE_MARGIN_HOURS if deadline_hours is None else float(deadline_hours)
    if dl <= 0 or dl >= float(max_hours):
        raise ValueError(f"night_run の締め切り {dl:g} 時間はタスクの上限 {max_hours} 時間より短く、0 より長くする")
    night = night_args(experiment, deadline_hours=dl, start_at=start_at or start.strftime("%H:%M"),
                       config=config, out=out)
    arguments = ps_arguments(python=python, workdir=workdir, night=night, log_root=out or DEFAULT_LOG_ROOT)
    boundary = start.strftime("%Y-%m-%dT%H:%M:%S")
    if daily:
        trigger = (f"    <CalendarTrigger>\n      <StartBoundary>{boundary}</StartBoundary>\n"
                   f"      <Enabled>true</Enabled>\n      <ScheduleByDay>\n        <DaysInterval>1</DaysInterval>\n"
                   f"      </ScheduleByDay>\n    </CalendarTrigger>\n")
    else:
        trigger = (f"    <TimeTrigger>\n      <StartBoundary>{boundary}</StartBoundary>\n"
                   f"      <Enabled>true</Enabled>\n    </TimeTrigger>\n")
    desc = (f"shibuya-simulation-v2: 5070 の夜の実験 {experiment}(回答 10-25 §6-0)。"
            f"tools/night5070/night_run.py が艦隊を立て、実験を回し、要約を docs/bench/night5070 に書く。")
    return (
        '<?xml version="1.0" encoding="UTF-16"?>\n'
        f'<Task version="1.2" xmlns="{TASK_NS}">\n'
        "  <RegistrationInfo>\n"
        f"    <Description>{escape(desc)}</Description>\n"
        "  </RegistrationInfo>\n"
        "  <Triggers>\n"
        f"{trigger}"
        "  </Triggers>\n"
        "  <Principals>\n"
        '    <Principal id="Author">\n'
        "      <LogonType>InteractiveToken</LogonType>\n"
        "      <RunLevel>LeastPrivilege</RunLevel>\n"
        "    </Principal>\n"
        "  </Principals>\n"
        "  <Settings>\n"
        "    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>\n"
        "    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>\n"
        "    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>\n"
        "    <AllowHardTerminate>true</AllowHardTerminate>\n"
        "    <StartWhenAvailable>true</StartWhenAvailable>\n"
        "    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>\n"
        "    <IdleSettings>\n"
        "      <StopOnIdleEnd>false</StopOnIdleEnd>\n"
        "      <RestartOnIdle>false</RestartOnIdle>\n"
        "    </IdleSettings>\n"
        "    <AllowStartOnDemand>true</AllowStartOnDemand>\n"
        "    <Enabled>true</Enabled>\n"
        "    <Hidden>false</Hidden>\n"
        "    <RunOnlyIfIdle>false</RunOnlyIfIdle>\n"
        f"    <WakeToRun>{'true' if wake else 'false'}</WakeToRun>\n"
        f"    <ExecutionTimeLimit>PT{int(max_hours)}H</ExecutionTimeLimit>\n"
        "    <Priority>7</Priority>\n"
        "  </Settings>\n"
        '  <Actions Context="Author">\n'
        "    <Exec>\n"
        "      <Command>powershell.exe</Command>\n"
        f"      <Arguments>{escape(arguments)}</Arguments>\n"
        f"      <WorkingDirectory>{escape(workdir)}</WorkingDirectory>\n"
        "    </Exec>\n"
        "  </Actions>\n"
        "</Task>\n"
    )


def create_command(name: str, xml_path: str) -> list[str]:
    return ["schtasks", "/create", "/tn", f"\\{name}", "/xml", xml_path, "/f"]


def delete_command(name: str) -> list[str]:
    return ["schtasks", "/delete", "/tn", f"\\{name}", "/f"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="夜の実験をタスクスケジューラに登録する(回答 10-25 §6-0)")
    ap.add_argument("--at", default="01:00", help="始める時刻 HH:MM(既定の案 01:00=ユーザーが決める)")
    ap.add_argument("--experiment", default="", help="実験の名(例 E1)")
    ap.add_argument("--name", default=DEFAULT_NAME, help=f"タスクの名(既定 {DEFAULT_NAME})")
    ap.add_argument("--wake", action="store_true", help="スリープから起こして始める(WakeToRun=true)")
    ap.add_argument("--daily", action="store_true", help="毎日回す(既定は次の 1 回だけ)")
    ap.add_argument("--max-hours", type=int, default=DEFAULT_MAX_HOURS, help="実行時間の上限[時間](既定 10)")
    ap.add_argument("--deadline-hours", type=float, default=None,
                    help="night_run の締め切り[時間](既定=上限 − 0.5。上限以上なら登録しない)")
    ap.add_argument("--config", default=None, help="night_run に渡す --config(リポの根からの相対)")
    ap.add_argument("--out", default=None, help="night_run に渡す --out(リポの根からの相対)")
    ap.add_argument("--print-only", action="store_true", help="XML とコマンドを出すだけで登録しない")
    ap.add_argument("--delete", action="store_true", help="タスクを消す")
    args = ap.parse_args(argv)

    if args.delete:
        cmd = delete_command(args.name)
        if args.print_only:
            print(" ".join(cmd))
            return 0
        return subprocess.run(cmd, check=False).returncode
    if not args.experiment:
        ap.error("--experiment が要る(例 E1)")
    try:
        start = next_start(args.at)
    except ValueError as exc:
        ap.error(str(exc))
    try:
        xml = build_xml(experiment=args.experiment, start=start, wake=args.wake, daily=args.daily,
                        max_hours=args.max_hours, deadline_hours=args.deadline_hours, config=args.config,
                        out=args.out, start_at=args.at)
    except ValueError as exc:
        print(f"register_task: 登録しない: {exc}", file=sys.stderr)
        return 2
    if args.print_only:
        print(mask_home(xml, xml=True))
        print(" ".join(create_command(args.name, "<XML の一時ファイル>")))
        return 0
    with tempfile.TemporaryDirectory(prefix="night5070_") as td:
        xp = Path(td) / f"{args.name}.xml"
        xp.write_text(xml, encoding="utf-16")
        cp = subprocess.run(create_command(args.name, str(xp)), check=False)
    if cp.returncode == 0:
        print(f"登録した: \\{args.name}(始め {start:%Y-%m-%d %H:%M}・{'毎日' if args.daily else '1 回'}"
              f"・WakeToRun={'true' if args.wake else 'false'})。確かめる: schtasks /query /tn \\{args.name} /v /fo LIST")
    return cp.returncode


if __name__ == "__main__":
    raise SystemExit(main())
