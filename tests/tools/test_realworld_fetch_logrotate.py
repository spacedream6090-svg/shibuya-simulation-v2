# -*- coding: utf-8 -*-
"""tools/realworld_fetch/logrotate.py(第337・取得の台帳とログを日ごとに回して gzip で縮める)の試験。

合成の台帳とログだけを使う(data/realworld_live は開かない)。見るもの: 回した後の読み口が元と 1 バイトも
違わない(gz の行数=元の行数)・日ごとの塊・書き手が開いている間は回さない・途中で落ちても行を失わず 2 度読まない・
回している最中に書き手が追記しても落ちず行を失わない・錠・1 日 1 回・`--rotate-logs`。
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import os
import sys
import threading
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[2] / "tools"
if importlib.util.find_spec("realworld_fetch") is None:
    sys.path.insert(0, str(_TOOLS))

from realworld_fetch import cli, ledger, logrotate as LR  # noqa: E402


def _row(i: int, ts: str) -> dict:
    return ledger.make_entry("odpt_rt", f"t{i}", ok=True, n_records=i, ts_utc=ts, date_jst=ts[:10],
                             extra={"seq": i})


#: JST の日の境目をまたぐ時刻(UTC 15:00 = JST 0:00)。
TS = ["2026-10-14T14:59:00Z", "2026-10-14T15:00:00Z", "2026-10-15T03:00:00Z",
      "2026-10-15T15:10:00Z", "2026-10-16T01:00:00Z"]


def _ledger_with(root: Path, n_per: int = 3) -> list[dict]:
    rows = [_row(i * 10 + k, ts) for i, ts in enumerate(TS) for k in range(n_per)]
    ledger.append(root, rows)
    return rows


def _gz_lines(root: Path, name: str) -> int:
    n = 0
    for _r, _d, _k, p in LR.archives(root, name):
        n += len(gzip.decompress(p.read_bytes()).splitlines())
    return n


def test_rotate_ledger_by_jst_day_is_byte_exact(tmp_path):
    rows = _ledger_with(tmp_path)
    before = (tmp_path / "_ledger.jsonl").read_bytes()
    res = LR.rotate_one(tmp_path, "_ledger.jsonl")
    assert res["status"] == "rotated"
    assert not (tmp_path / "_ledger.jsonl").exists()
    # JST の日: 10-14 23:59 / 10-15 0:00・12:00 / 10-16 0:10・10:00
    assert res["days"] == ["2026-10-14", "2026-10-15", "2026-10-16"]
    assert LR.read_bytes_all(tmp_path, "_ledger.jsonl") == before
    assert _gz_lines(tmp_path, "_ledger.jsonl") == len(rows) == res["lines"]
    assert ledger.read_all(tmp_path) == rows
    assert res["bytes_out"] < res["bytes_in"]


def test_new_lines_after_rotation_follow_the_archives(tmp_path):
    rows = _ledger_with(tmp_path)
    LR.rotate_one(tmp_path, "_ledger.jsonl")
    more = [_row(900 + k, "2026-10-16T02:00:00Z") for k in range(4)]
    ledger.append(tmp_path, more)
    assert ledger.read_all(tmp_path) == rows + more
    LR.rotate_one(tmp_path, "_ledger.jsonl")
    assert ledger.read_all(tmp_path) == rows + more
    assert _gz_lines(tmp_path, "_ledger.jsonl") == len(rows) + len(more)


def test_day_never_goes_back_and_chunks_concatenate(tmp_path):
    spec = LR.spec_of("_ledger.jsonl")
    lines = [json.dumps({"ts_utc": t}).encode() + b"\n" for t in
             ("2026-10-15T01:00:00Z", "2026-10-14T01:00:00Z", "2026-10-16T01:00:00Z")]
    lines.insert(1, b"not json\n")
    data = b"".join(lines) + b"{\"ts_utc\": \"2026-10-16T02:00:00Z\"}"  # 終わりの改行の無い行
    ch = LR.split_days(data, spec, "2026-10-01")
    assert [d for d, _ in ch] == ["2026-10-15", "2026-10-16"]
    assert b"".join(b for _, b in ch) == data


def test_utf16_log_rotates_as_one_chunk(tmp_path):
    p = tmp_path / "_scheduler_odpt.log"
    text = "﻿[odpt_rt] 取得開始\r\n[done] 台帳へ 3 行追記\r\n" * 5
    p.write_bytes(text.encode("utf-16-le"))
    n0 = len(LR.read_text_all(tmp_path, p.name).splitlines())
    res = LR.rotate_one(tmp_path, p.name)
    assert res["status"] == "rotated" and len(res["archives"]) == 1 and res["lines"] == n0 == 10
    assert LR.read_text_all(tmp_path, p.name) == text.replace("﻿", "")
    # 回した後に書き手が新しいファイル(BOM つき)を作っても読み口はつながる
    p.write_bytes(("﻿" + "next\r\n").encode("utf-16-le"))
    assert LR.read_text_all(tmp_path, p.name).splitlines()[-1] == "next"
    assert LR.count_lines(tmp_path, p.name) == 11


def test_busy_writer_is_left_alone(tmp_path, monkeypatch):
    rows = _ledger_with(tmp_path)

    def deny(*_a, **_k):
        raise PermissionError("共有違反(書き手が開いている)")

    monkeypatch.setattr(LR.os, "replace", deny)
    res = LR.rotate_one(tmp_path, "_ledger.jsonl", tries=2, wait_s=0)
    assert res["status"] == "busy"
    monkeypatch.undo()
    assert ledger.read_all(tmp_path) == rows
    assert LR.archives(tmp_path, "_ledger.jsonl") == []


@pytest.mark.skipif(os.name != "nt", reason="Windows の共有違反(開いている間は改名できない)")
def test_writer_handle_blocks_rename_on_windows(tmp_path):
    rows = _ledger_with(tmp_path)
    with open(tmp_path / "_ledger.jsonl", "a", encoding="utf-8"):
        res = LR.rotate_one(tmp_path, "_ledger.jsonl", tries=2, wait_s=0)
    assert res["status"] == "busy"
    assert ledger.read_all(tmp_path) == rows


def test_crash_after_rename_loses_nothing_and_reads_once(tmp_path, monkeypatch):
    rows = _ledger_with(tmp_path)
    real_gz = LR._gz
    calls = {"n": 0}

    def half(data):  # 2 つ目の塊を書く所で落ちる(1 つ目の gz は置かれている)
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("落ちた")
        return real_gz(data)

    monkeypatch.setattr(LR, "_gz", half)
    with pytest.raises(OSError):
        LR.rotate_one(tmp_path, "_ledger.jsonl")
    monkeypatch.undo()
    assert len(LR.pending(tmp_path, "_ledger.jsonl")) == 1
    assert LR.archives(tmp_path, "_ledger.jsonl") == []      # 書いた分は消した
    assert ledger.read_all(tmp_path) == rows                  # rotating を読む
    # 落ちた形をもう 1 つ: 塊の gz が残ったまま rotating も残る → 読み手はその rotid の gz を使わない
    rot_id, rot = LR.pending(tmp_path, "_ledger.jsonl")[0]
    stray = LR.archive_root(tmp_path) / "2026-10" / f"_ledger.jsonl.2026-10-14.r{rot_id}.p0.gz"
    stray.parent.mkdir(parents=True, exist_ok=True)
    stray.write_bytes(gzip.compress(rot.read_bytes()))
    assert ledger.read_all(tmp_path) == rows
    # 次の回で片付く(生きているファイルは無い=empty・片付けた結果が recovered に出る)
    res = LR.rotate_one(tmp_path, "_ledger.jsonl")
    assert res["status"] == "empty" and len(res["recovered"]) == 1
    assert LR.pending(tmp_path, "_ledger.jsonl") == []
    assert ledger.read_all(tmp_path) == rows
    assert _gz_lines(tmp_path, "_ledger.jsonl") == len(rows)


def test_verify_mismatch_keeps_the_rotating_file(tmp_path, monkeypatch):
    rows = _ledger_with(tmp_path)
    monkeypatch.setattr(LR, "_gz", lambda data: gzip.compress(data[:-1]))  # 1 バイト欠けた gz
    with pytest.raises(OSError):
        LR.rotate_one(tmp_path, "_ledger.jsonl")
    monkeypatch.undo()
    assert LR.archives(tmp_path, "_ledger.jsonl") == []
    assert ledger.read_all(tmp_path) == rows


def test_writer_keeps_appending_during_rotations(tmp_path):
    """書き手(``ledger.append``)が追記を続けている間に何度も回す: 書き手は落ちず、行は 1 つも失わず重ならない。"""
    n = 400
    errors: list[BaseException] = []

    def writer():
        try:
            for i in range(n):
                ledger.append(tmp_path, _row(i, "2026-10-15T03:00:00Z"))
        except BaseException as exc:  # pragma: no cover - 落ちたら試験が知らせる
            errors.append(exc)

    t = threading.Thread(target=writer)
    t.start()
    rotated = 0
    while t.is_alive():
        try:
            r = LR.rotate_one(tmp_path, "_ledger.jsonl", tries=3, wait_s=0.001)
        except LR.RotateBusy:
            continue
        rotated += r["status"] == "rotated"
    t.join()
    assert not errors
    got = [r["extra"]["seq"] for r in ledger.read_all(tmp_path)]
    assert got == list(range(n))
    assert rotated >= 1


def test_lock_excludes_a_second_rotator_and_stale_lock_is_cleared(tmp_path):
    _ledger_with(tmp_path)
    lk = LR.archive_root(tmp_path) / LR.LOCK_NAME
    lk.parent.mkdir(parents=True, exist_ok=True)
    lk.write_text("123 0\n")
    with pytest.raises(LR.RotateBusy):
        LR.rotate_one(tmp_path, "_ledger.jsonl")
    assert (tmp_path / "_ledger.jsonl").exists()
    old = os.path.getmtime(lk) - LR.LOCK_STALE_S - 5
    os.utime(lk, (old, old))
    assert LR.rotate_one(tmp_path, "_ledger.jsonl")["status"] == "rotated"
    assert not lk.exists()


def test_maybe_rotate_once_a_day(tmp_path):
    rows = _ledger_with(tmp_path)
    r1 = LR.maybe_rotate(tmp_path, today="2026-10-16")
    assert {r["name"]: r["status"] for r in r1}["_ledger.jsonl"] == "rotated"
    ledger.append(tmp_path, _row(77, "2026-10-16T03:00:00Z"))
    assert LR.maybe_rotate(tmp_path, today="2026-10-16") == []          # 同じ日は回さない
    r3 = LR.maybe_rotate(tmp_path, today="2026-10-17")
    assert {r["name"]: r["status"] for r in r3}["_ledger.jsonl"] == "rotated"
    assert len(ledger.read_all(tmp_path)) == len(rows) + 1


def test_cli_rotate_logs(tmp_path, capsys):
    _ledger_with(tmp_path)
    (tmp_path / "_scheduler.log").write_bytes("﻿a\r\nb\r\n".encode("utf-16-le"))
    assert cli.main(["--rotate-logs", "--out-dir", str(tmp_path)]) == 0
    out = capsys.readouterr()
    text = out.out + out.err
    assert "_ledger.jsonl" in text and "_scheduler.log" in text
    assert not (tmp_path / "_ledger.jsonl").exists() and not (tmp_path / "_scheduler.log").exists()
    assert LR.count_lines(tmp_path, "_scheduler.log") == 2


def test_report_and_verify_read_through_archives(tmp_path):
    rows = _ledger_with(tmp_path)
    LR.rotate_one(tmp_path, "_ledger.jsonl")
    assert cli.main(["--report", "--out-dir", str(tmp_path), "--date", "2026-10-16"]) == 0
    assert cli.main(["--verify", "--out-dir", str(tmp_path)]) == 0       # gz の台帳は検査の対象の外(名が _ で始まる)
    assert len(ledger.read_all(tmp_path)) == len(rows)


def test_reader_retries_when_a_rotation_runs_mid_read(tmp_path, monkeypatch):
    """〔検収 L3〕読みの途中で回しが走っても(生きているファイルが消える・gz が増える)読み落とさない。"""
    rows = _ledger_with(tmp_path)
    real_once = LR._chunks_once
    calls = {"n": 0}

    def once_then_rotate(root, name):
        calls["n"] += 1
        if calls["n"] == 1:  # 1 回目の読みの途中で回る → 生きているファイルが無い
            LR.rotate_one(root, name)
            raise FileNotFoundError(name)
        return real_once(root, name)

    monkeypatch.setattr(LR, "_chunks_once", once_then_rotate)
    assert ledger.read_all(tmp_path) == rows
    assert calls["n"] == 2


def test_reader_retries_when_the_listing_changes(tmp_path, monkeypatch):
    rows = _ledger_with(tmp_path)
    real_once = LR._chunks_once
    calls = {"n": 0}

    def stale_list(root, name):  # 1 回目: 回る前の生きているファイルだけを読み、読み終えた後に回しが走る
        calls["n"] += 1
        out = real_once(root, name)
        if calls["n"] == 1:
            LR.rotate_one(root, name)
            ledger.append(root, _row(999, "2026-10-16T05:00:00Z"))
        return out

    monkeypatch.setattr(LR, "_chunks_once", stale_list)
    got = ledger.read_all(tmp_path)
    assert calls["n"] == 2 and got == rows + [_row(999, "2026-10-16T05:00:00Z")]


def test_stale_lock_is_cleared_only_by_the_one_that_moved_it(tmp_path, monkeypatch):
    """〔検収 L4〕古い錠を移せなかった側(ほかの回しが先に片付けた)は進まない。"""
    _ledger_with(tmp_path)
    lk = LR.archive_root(tmp_path) / LR.LOCK_NAME
    lk.parent.mkdir(parents=True, exist_ok=True)
    lk.write_text("1 0\n")
    old = os.path.getmtime(lk) - LR.LOCK_STALE_S - 5
    os.utime(lk, (old, old))
    real_replace = os.replace

    def other_cleared_first(src, dst):
        if str(src) == str(lk) and ".stale." in str(dst):
            os.remove(lk)  # ほかの回しが先に移した
            raise FileNotFoundError(src)
        return real_replace(src, dst)

    monkeypatch.setattr(LR.os, "replace", other_cleared_first)
    with pytest.raises(LR.RotateBusy):
        LR.rotate_one(tmp_path, "_ledger.jsonl")
    monkeypatch.undo()
    assert (tmp_path / "_ledger.jsonl").exists()


def test_fresh_lock_moved_by_mistake_is_put_back(tmp_path, monkeypatch):
    """古いと見た後にほかの回しが新しい錠を作っていたら、移した錠を元へ戻して進まない(新しい錠を消さない)。"""
    _ledger_with(tmp_path)
    lk = LR.archive_root(tmp_path) / LR.LOCK_NAME
    lk.parent.mkdir(parents=True, exist_ok=True)
    lk.write_text("1 0\n")
    old = os.path.getmtime(lk) - LR.LOCK_STALE_S - 5
    os.utime(lk, (old, old))
    real_replace = os.replace

    def swap_in_fresh(src, dst):
        if str(src) == str(lk) and ".stale." in str(dst):
            os.remove(lk)
            lk.write_text("2 fresh\n")  # 見た後にほかの回しが新しい錠を作った
        return real_replace(src, dst)

    monkeypatch.setattr(LR.os, "replace", swap_in_fresh)
    with pytest.raises(LR.RotateBusy):
        LR.rotate_one(tmp_path, "_ledger.jsonl")
    monkeypatch.undo()
    assert lk.read_text() == "2 fresh\n"
    assert not list(lk.parent.glob(f"{LR.LOCK_NAME}.stale.*"))


def test_spec_table_is_read_only():
    with pytest.raises(TypeError):
        LR._SPEC["x"] = LR.LOGS[0]  # type: ignore[index]
