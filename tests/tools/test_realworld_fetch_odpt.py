# -*- coding: utf-8 -*-
"""tools/realworld_fetch の ODPT の取得(第333): 全路線の保存・gzip・間隔・変化分だけ・欠けた時間帯・
静的データの版と --check・秘密が出ないこと。ネットワークには出ない(`common._urlopen` を差し替える)。"""
from __future__ import annotations

import gzip
import importlib.util
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[2] / "tools"
if importlib.util.find_spec("realworld_fetch") is None:      # PYTHONPATH の写しが先なら写しを使う
    sys.path.insert(0, str(_TOOLS))

from realworld_fetch import cli, common, ledger, odpt_rt, odpt_static  # noqa: E402

JST = common.JST
NOW = datetime(2026, 10, 13, 12, 0, 0, tzinfo=JST)
# 秘密の検査用の偽のキー(部品からつなぐ=このファイル自体を秘密の検査に当てない)
OPEN_KEY = "-".join(["OPENKEY", "TEST", "0123456789"])
CHAL_KEY = "-".join(["CHALKEY", "TEST", "9876543210"])


# ------------------------------------------------------------------ 偽の ODPT
class _Resp:
    def __init__(self, body: bytes, status: int = 200):
        self.status = status
        self._b = body

    def read(self):
        return self._b

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeODPT:
    """`common._urlopen` の代わり。(枠, 種類) ごとの関数が params からレコードの並びを返す。"""

    def __init__(self):
        self.calls: list[tuple[str, str, dict, str | None]] = []
        self.handlers: dict[tuple[str, str], object] = {}

    def on(self, scope: str, datatype: str, fn):
        self.handlers[(scope, datatype)] = fn
        return self

    def __call__(self, req, timeout):
        u = urllib.parse.urlsplit(req.full_url)
        dt = u.path.rsplit("/", 1)[-1]
        q = dict(urllib.parse.parse_qsl(u.query))
        key = q.pop("acl:consumerKey", None)
        scope = "challenge" if (u.hostname or "").startswith("api-challenge") else "open"
        self.calls.append((scope, dt, q, key))
        fn = self.handlers.get((scope, dt))
        data = fn(q) if fn else []
        if isinstance(data, int):                   # 状態コードだけを返す(失敗の試験)
            return _Resp(b"", status=data)
        return _Resp(json.dumps(data, ensure_ascii=False).encode("utf-8"))


@pytest.fixture
def fake(monkeypatch):
    f = FakeODPT()
    monkeypatch.setattr(common, "_urlopen", f)
    common.reset_request_count()
    yield f
    common.clear_secrets()


def _rec(rid: str, railway: str | None = None, *, now=NOW, **kw) -> dict:
    r = {"@id": f"urn:{rid}", "owl:sameAs": rid, "dc:date": now.isoformat(),
         "dct:valid": (now + timedelta(minutes=5)).isoformat()}
    if railway:
        r["odpt:railway"] = railway
    r.update(kw)
    return r


def _open_ops():
    return {"odpt:TrainInformation": ("odpt.Operator:Toei",),
            "odpt:Train": ("odpt.Operator:Toei",),
            "odpt:Bus": ("odpt.Operator:Toei",)}


def _install_rt(fake: FakeODPT, *, now=NOW, info_text="平常運転"):
    fake.on("open", "odpt:TrainInformation", lambda q: [
        _rec("ti.Toei.Asakusa", "odpt.Railway:Toei.Asakusa", now=now,
             **{"odpt:trainInformationText": {"ja": info_text}}),
        _rec("ti.Toei.Oedo", "odpt.Railway:Toei.Oedo", now=now)])
    fake.on("open", "odpt:Train", lambda q: [
        _rec(f"train.Toei.{i}", "odpt.Railway:Toei.Mita", now=now, **{"odpt:delay": i * 30})
        for i in range(5)])
    fake.on("open", "odpt:Bus", lambda q: [
        _rec(f"bus.Toei.{i}", None, now=now) for i in range(7)])
    fake.on("challenge", "odpt:TrainInformation", lambda q: [
        _rec("ti.Tokyu.Toyoko", "odpt.Railway:Tokyu.Toyoko", now=now),
        _rec("ti.Tokyu.Meguro", "odpt.Railway:Tokyu.Meguro", now=now),      # 作品の範囲の外
        _rec("ti.Tokyu.DenEnToshi", "odpt.Railway:Tokyu.DenEnToshi", now=now),
    ] if q.get("odpt:operator") == "odpt.Operator:Tokyu" else [
        _rec("ti.Keio.Inokashira", "odpt.Railway:Keio.Inokashira", now=now),
        _rec("ti.Keio.Keio", "odpt.Railway:Keio.Keio", now=now)])           # 作品の範囲の外
    fake.on("challenge", "odpt:Train", lambda q: [
        _rec(f"train.{q.get('odpt:railway')}.{i}", q.get("odpt:railway"), now=now)
        for i in range(2)])


def _snap(root, now=NOW, **kw):
    kw.setdefault("open_operators", _open_ops())
    return odpt_rt.fetch_snapshot(root, now=now, open_key=OPEN_KEY, challenge_key=CHAL_KEY,
                                  sleep=0, sleep_fn=lambda s: None, **kw)


def _files(root: Path, pattern="**/*.json.gz"):
    return sorted(p for p in Path(root).glob(pattern))


# ------------------------------------------------------------------ (1) 全レコード・(2) gzip
def test_open_saves_all_records_and_challenge_keeps_work_scope(fake, tmp_path):
    _install_rt(fake)
    docs, rows = _snap(tmp_path)
    names = sorted(p.name for p in _files(tmp_path))
    assert names == sorted([
        "traininformation_Toei_120000.json.gz", "train_Toei_120000.json.gz",
        "bus_Toei_120000.json.gz", "traininformation_Tokyu-challenge_120000.json.gz",
        "traininformation_Keio-challenge_120000.json.gz",
        "train_JR-East-challenge_120000.json.gz"])
    by = {p.name: common.read_json_any(p) for p in _files(tmp_path)}
    # オープン枠は絞らない(渋谷の 9 路線に無い都営の路線も全部)
    assert len(by["traininformation_Toei_120000.json.gz"]["data"]) == 2
    assert len(by["train_Toei_120000.json.gz"]["data"]) == 5
    assert len(by["bus_Toei_120000.json.gz"]["data"]) == 7
    # チャレンジ枠は作品の範囲だけ(目黒線・京王線は落ちる)
    tok = by["traininformation_Tokyu-challenge_120000.json.gz"]["data"]
    assert {r["odpt:railway"] for r in tok} == {"odpt.Railway:Tokyu.Toyoko",
                                                "odpt.Railway:Tokyu.DenEnToshi"}
    keio = by["traininformation_Keio-challenge_120000.json.gz"]["data"]
    assert [r["odpt:railway"] for r in keio] == ["odpt.Railway:Keio.Inokashira"]
    jr = by["train_JR-East-challenge_120000.json.gz"]
    assert len(jr["data"]) == 6 and jr["_meta"]["n_parts"] == 3
    # チャレンジ枠への要求は今の範囲だけ(運行情報 東急・京王 / 在線 JR 3 線)
    chal = sorted((dt, tuple(sorted(q.items()))) for s, dt, q, _ in fake.calls
                  if s == "challenge")
    assert chal == sorted([
        ("odpt:TrainInformation", (("odpt:operator", "odpt.Operator:Keio"),)),
        ("odpt:TrainInformation", (("odpt:operator", "odpt.Operator:Tokyu"),)),
        ("odpt:Train", (("odpt:railway", "odpt.Railway:JR-East.SaikyoKawagoe"),)),
        ("odpt:Train", (("odpt:railway", "odpt.Railway:JR-East.ShonanShinjuku"),)),
        ("odpt:Train", (("odpt:railway", "odpt.Railway:JR-East.Yamanote"),))])
    assert all(r["ok"] for r in rows) and len(rows) == 8        # 3 + 2 + JR 3 路線
    for doc in by.values():
        assert common.validate_document(doc) == []


def test_gzip_written_and_readable_and_verify_reads_both(fake, tmp_path):
    _install_rt(fake)
    docs, rows = _snap(tmp_path)
    p = _files(tmp_path, "**/bus_Toei_*.json.gz")[0]
    raw = p.read_bytes()
    assert raw[:2] == b"\x1f\x8b"                         # gzip の印
    doc = json.loads(gzip.decompress(raw).decode("utf-8"))
    assert doc == common.read_json_any(p)
    row = next(r for r in rows if r["target"] == "Bus/open/odpt.Operator:Toei")
    assert row["extra"]["bytes_gz"] == len(raw)
    assert row["extra"]["bytes_raw"] == len(gzip.decompress(raw))
    # 古い形の .json も同じ口で読める
    common.write_json(tmp_path / "odpt_rt" / "2026" / "10" / "2026-10-12" / "train_235500.json",
                      {"_meta": doc["_meta"], "data": doc["data"]})
    n_ok, n_all, problems = cli.verify(tmp_path)
    assert problems == [] and n_ok == n_all == 7


# ------------------------------------------------------------------ (3) 間隔
def test_cadence_skips_until_due_and_force_overrides(fake, tmp_path):
    _install_rt(fake)
    _snap(tmp_path)
    n1 = len(fake.calls)
    docs, rows = _snap(tmp_path, now=NOW + timedelta(seconds=120))
    assert len(fake.calls) == n1 and rows == [] and docs == []      # 飛ばしは台帳に書かない
    st = json.loads((tmp_path / "odpt_rt" / "_last_fetch.json").read_text(encoding="utf-8"))
    assert st["jobs"]["open|odpt:Bus|odpt.Operator:Toei"]["n_skipped_cadence"] == 1
    assert st["jobs"]["open|odpt:Bus|odpt.Operator:Toei"]["last_fetch_jst"] == NOW.isoformat()
    # 起動の揺れ: 間隔 300 秒に 5 秒足りなくても取る(余裕 60 秒)
    _install_rt(fake, now=NOW + timedelta(seconds=295))
    docs, rows = _snap(tmp_path, now=NOW + timedelta(seconds=295))
    assert len(rows) == 8
    # 種類ごとの間隔: バスだけ 600 秒
    n2 = len(fake.calls)
    t = NOW + timedelta(seconds=295 + 300)
    _install_rt(fake, now=t)
    docs, rows = _snap(tmp_path, now=t, cadence={"odpt:TrainInformation": 300,
                                                 "odpt:Train": 300, "odpt:Bus": 600})
    assert not any(dt == "odpt:Bus" for _, dt, _, _ in fake.calls[n2:])
    assert len(rows) == 7
    # --force は間隔を無視する
    n3 = len(fake.calls)
    docs, rows = _snap(tmp_path, now=t + timedelta(seconds=10), force=True)
    assert len(fake.calls) - n3 == 8


def test_due_rule():
    ent = {"last_fetch_jst": NOW.isoformat()}
    assert odpt_rt.due(None, "odpt:Bus", NOW)
    assert not odpt_rt.due(ent, "odpt:Bus", NOW + timedelta(seconds=239))
    assert odpt_rt.due(ent, "odpt:Bus", NOW + timedelta(seconds=240))
    assert odpt_rt.due(ent, "odpt:Bus", NOW - timedelta(seconds=30))     # 時計が戻った
    assert not odpt_rt.due(ent, "odpt:Bus", NOW + timedelta(seconds=500),
                           cadence={"odpt:Bus": 600})


# ------------------------------------------------------------------ (4) 変化した分だけ
def test_dedupe_unchanged_info_not_saved_and_marked_in_ledger(fake, tmp_path):
    _install_rt(fake)
    _snap(tmp_path)
    t2 = NOW + timedelta(minutes=5)
    _install_rt(fake, now=t2)                    # dc:date と dct:valid だけが変わる
    docs, rows = _snap(tmp_path, now=t2)
    ti = next(r for r in rows if r["target"] == "TrainInformation/open/odpt.Operator:Toei")
    assert ti["ok"] and ti["extra"]["unchanged"] is True
    assert ti["extra"]["same_as"] == "traininformation_Toei_120000.json.gz"
    assert not _files(tmp_path, "**/traininformation_Toei_120500.json.gz")
    # 在線は既定で変化分だけにしない(毎回保存)
    assert _files(tmp_path, "**/train_Toei_120500.json.gz")
    tr = next(r for r in rows if r["target"] == "Train/open/odpt.Operator:Toei")
    assert tr["extra"]["unchanged"] is False
    # 中身が変われば保存
    t3 = NOW + timedelta(minutes=10)
    _install_rt(fake, now=t3, info_text="遅延")
    docs, rows = _snap(tmp_path, now=t3)
    assert _files(tmp_path, "**/traininformation_Toei_121000.json.gz")
    st = json.loads((tmp_path / "odpt_rt" / "_last_fetch.json").read_text(encoding="utf-8"))
    assert st["jobs"]["open|odpt:TrainInformation|odpt.Operator:Toei"]["n_unchanged"] == 1
    # 日付が変わって最初の取得は、同じ中身でも保存する
    t4 = datetime(2026, 10, 14, 0, 2, 0, tzinfo=JST)
    _install_rt(fake, now=t4, info_text="遅延")
    _snap(tmp_path, now=t4)
    assert _files(tmp_path, "**/2026-10-14/traininformation_Toei_000200.json.gz")


def test_content_hash_ignores_time_fields_and_order():
    a = [_rec("x", "r1"), _rec("y", "r2")]
    b = [_rec("y", "r2", now=NOW + timedelta(minutes=3)), _rec("x", "r1", now=NOW + timedelta(minutes=3))]
    assert odpt_rt.content_hash(a) == odpt_rt.content_hash(b)
    c = [_rec("x", "r1"), _rec("y", "r3")]
    assert odpt_rt.content_hash(a) != odpt_rt.content_hash(c)


def test_bus_capped_is_split_by_route_with_static_routes(fake, tmp_path, monkeypatch):
    monkeypatch.setattr(odpt_rt, "API_CAP", 4)
    _install_rt(fake)
    buses = {f"odpt.Busroute:Toei.R{k}": [_rec(f"bus.R{k}.{i}", None, **{
        "odpt:busroute": f"odpt.Busroute:Toei.R{k}"}) for i in range(2)] for k in (1, 2, 3)}

    def bus(q):
        if "odpt:busroute" in q:
            vals = q["odpt:busroute"].split(",")
            assert len(vals) <= odpt_rt.OR_MAX_VALUES
            return [b for v in vals for b in buses.get(v, [])]          # 6 件(打ち切りでない)
        return buses["odpt.Busroute:Toei.R1"] + buses["odpt.Busroute:Toei.R2"]   # 4 件=打ち切り
    fake.on("open", "odpt:Bus", bus)
    # 静的データの最新版の系統(R3 は打ち切られた応答に出てこない)
    common.write_json_gz(tmp_path / "odpt_static" / "2026-10-12" / "busroutepattern_Toei.json.gz",
                         {"_meta": {}, "data": [{"odpt:busroute": "odpt.Busroute:Toei.R3"}]})
    docs, rows = _snap(tmp_path, open_operators={"odpt:Bus": ("odpt.Operator:Toei",)})
    doc = common.read_json_any(_files(tmp_path, "**/bus_Toei_*.json.gz")[0])
    assert sorted(r["owl:sameAs"] for r in doc["data"]) == sorted(
        b["owl:sameAs"] for v in buses.values() for b in v)
    assert doc["_meta"]["split"]["route_source"] == "static+response"
    assert doc["_meta"]["capped"] is False
    row = next(r for r in rows if r["target"] == "Bus/open/odpt.Operator:Toei")
    assert row["extra"]["n_split_requests"] == 1 and row["extra"]["n_api_first"] == 4


def test_empty_response_writes_no_file(fake, tmp_path):
    _install_rt(fake)
    fake.on("open", "odpt:Train", lambda q: [])
    docs, rows = _snap(tmp_path)
    assert not _files(tmp_path, "**/train_Toei_*.json.gz")
    row = next(r for r in rows if r["target"] == "Train/open/odpt.Operator:Toei")
    assert row["ok"] and row["n_records"] == 0 and row["extra"]["empty"] is True


def test_failed_part_keeps_other_parts_and_job_errors_are_isolated(fake, tmp_path, monkeypatch):
    _install_rt(fake)
    ok_train = fake.handlers[("challenge", "odpt:Train")]
    fake.on("challenge", "odpt:Train", lambda q: 503 if q.get("odpt:railway", "").endswith(
        "SaikyoKawagoe") else ok_train(q))
    docs, rows = _snap(tmp_path)
    jr = common.read_json_any(_files(tmp_path, "**/train_JR-East-challenge_*.json.gz")[0])
    assert len(jr["data"]) == 4 and jr["_meta"]["n_failed_parts"] == 1
    bad = [r for r in rows if r["target"] == "Train/challenge/jr_saikyo"]
    assert len(bad) == 1 and bad[0]["ok"] is False and bad[0]["http_status"] == 503
    # 1 つの job の例外は、その job の失敗行になるだけ(他の job と状態ファイルは残る)
    def boom(records):
        raise RuntimeError("delay_summary failed")
    monkeypatch.setattr(odpt_rt, "delay_summary", boom)
    t = NOW + timedelta(minutes=5)
    _install_rt(fake, now=t)
    docs, rows = _snap(tmp_path, now=t)
    errs = [r for r in rows if not r["ok"]]
    assert {r["target"] for r in errs} == {"Train/open/odpt.Operator:Toei",
                                           "Bus/open/odpt.Operator:Toei",
                                           "Train/challenge/odpt.Operator:JR-East"}
    assert all("RuntimeError" in r["error"] for r in errs)
    st = json.loads((tmp_path / "odpt_rt" / "_last_fetch.json").read_text(encoding="utf-8"))
    assert st["updated_jst"] == t.isoformat()


# ------------------------------------------------------------------ (5) 欠けた時間帯
def _row(t: datetime, target="Train/open/odpt.Operator:Toei", ok=True, with_snap=True):
    extra = {"snapshot_jst": t.isoformat()} if with_snap else None
    return ledger.make_entry("odpt_rt", target, ok=ok, date_jst=t.date().isoformat(),
                             ts_utc=common.iso_utc(t), extra=extra)


def test_rt_gap_report_counts_missing_hours_and_runs():
    d1 = datetime(2026, 10, 11, 0, 0, tzinfo=JST)
    rows = []
    for k in range(288):                                  # 10-11 は 5 分ごと(3〜5 時は止まっていた)
        t = d1 + timedelta(minutes=5 * k)
        if 3 <= t.hour <= 5:
            continue
        rows.append(_row(t))
        rows.append(_row(t + timedelta(seconds=2), target="Bus/open/odpt.Operator:Toei"))
    d2 = datetime(2026, 10, 12, 0, 0, tzinfo=JST)        # 10-12 は 22 時台だけ失敗、23 時台は空
    for k in range(276):
        t = d2 + timedelta(minutes=5 * k)
        rows.append(_row(t, ok=(t.hour != 22)))
    now = datetime(2026, 10, 13, 2, 30, tzinfo=JST)       # 今日は 0・1 時の枠だけ数える
    rows.append(_row(datetime(2026, 10, 13, 0, 5, tzinfo=JST)))
    rep = ledger.rt_gap_report(rows, now.date(), now=now, lookback_days=30)
    days = {d["day"]: d for d in rep["days"]}
    assert rep["window_start"] == "2026-10-11"            # 集め始める前の日は数えない
    assert days["2026-10-11"]["hours_missing"] == 3
    assert days["2026-10-11"]["gaps"] == [("03:00", "05:59")]
    assert days["2026-10-11"]["snapshots"]["odpt:Train"] == 252
    assert days["2026-10-11"]["snapshots"]["odpt:Bus"] == 252
    assert days["2026-10-11"]["expected"]["odpt:Train"] == 288
    assert days["2026-10-12"]["hours_missing"] == 2
    assert days["2026-10-12"]["gaps"] == [("22:00", "23:59")]
    assert days["2026-10-12"]["fail_only_hours"] == 1
    assert days["2026-10-13"]["hours_counted"] == 2 and days["2026-10-13"]["hours_missing"] == 1
    assert rep["total_missing_hours"] == 6 and rep["n_days"] == 3
    text = ledger.format_rt_report(rows, now.date(), now=now)
    assert "合計: 欠け 6 時間 / 3 日" in text


def test_rt_gap_report_first_day_starts_at_first_row_and_old_rows_cluster():
    t0 = datetime(2026, 10, 3, 17, 40, tzinfo=JST)
    rows = []
    for k in range(12 * 6):                               # 17:40〜23:35 の 5 分ごと
        t = t0 + timedelta(minutes=5 * k)
        # 古い形の行(snapshot_jst なし): 1 回の実行の 3 行が数秒ずつずれる
        for j, tg in enumerate(("Train/challenge/jr_yamanote", "Train/challenge/jr_saikyo",
                                "Train/challenge/jr_shonanshinjuku")):
            rows.append(_row(t + timedelta(seconds=3 * j), target=tg, with_snap=False))
    now = datetime(2026, 10, 4, 0, 30, tzinfo=JST)
    rep = ledger.rt_gap_report(rows, datetime(2026, 10, 3).date(), now=now)
    day = rep["days"][0]
    assert day["hours_counted"] == 7 and day["hours_missing"] == 0     # 17 時から数える
    assert day["snapshots"]["odpt:Train"] == 72


# ------------------------------------------------------------------ (6) 静的データ
def _install_static(fake: FakeODPT, *, issued="2026-03-14", cap=False):
    rails = [{"owl:sameAs": "odpt.Railway:Toei.Asakusa", "dc:date": "2024-06-27T08:00:00+09:00"},
             {"owl:sameAs": "odpt.Railway:Toei.Oedo", "dc:date": "2024-06-27T08:00:00+09:00"}]
    fake.on("open", "odpt:Operator", lambda q: [{"owl:sameAs": "odpt.Operator:Toei"},
                                                {"owl:sameAs": "odpt.Operator:JAL"}])
    fake.on("open", "odpt:Railway", lambda q: rails if q.get("odpt:operator") == "odpt.Operator:Toei" else [])

    def tt(q):
        if q.get("odpt:operator") != "odpt.Operator:Toei":
            return []
        rw = q.get("odpt:railway")
        all_ = [{"owl:sameAs": f"tt.{r}.{i}", "odpt:railway": r, "dct:issued": issued,
                 "dc:date": "2026-03-16T10:00:00+09:00"}
                for r, n in (("odpt.Railway:Toei.Asakusa", 6), ("odpt.Railway:Toei.Oedo", 5))
                for i in range(n)]
        if rw:
            return [x for x in all_ if x["odpt:railway"] == rw]
        return all_[:4] if cap else all_
    fake.on("open", "odpt:TrainTimetable", tt)


def test_static_version_splits_capped_and_check_lists_newer(fake, tmp_path, monkeypatch):
    monkeypatch.setattr(odpt_rt, "API_CAP", 4)            # 上限 4 件の偽の API
    _install_static(fake, cap=True)
    t = datetime(2026, 10, 13, 23, 0, tzinfo=JST)
    index, rows = odpt_static.fetch_version(
        tmp_path, types=("odpt:Railway", "odpt:TrainTimetable"), now=t, key=OPEN_KEY,
        sleep=0, sleep_fn=lambda s: None)
    ent = index["entries"]["odpt.Operator:Toei|odpt:TrainTimetable"]
    assert ent["n"] == 11 and ent["capped_parts"] == []          # 路線で分けて全部
    assert ent["split_keys_used"] == ["odpt:railway"]
    assert ent["issued_max"] == "2026-03-14"
    assert "odpt.Operator:JAL|odpt:Railway" not in index["entries"]   # 航空会社は対象外
    vfile = tmp_path / "odpt_static" / "2026-10-13" / "traintimetable_Toei.json.gz"
    doc = common.read_json_any(vfile)
    assert doc["_meta"]["issued_max"] == "2026-03-14" and len(doc["data"]) == 11
    assert common.validate_document(doc) == []
    # --check: API の dct:issued が新しくなった組だけが出る
    _install_static(fake, issued="2026-11-01", cap=False)
    fake.on("open", "odpt:Operator", lambda q: [{"owl:sameAs": "odpt.Operator:Toei"},
                                                {"owl:sameAs": "odpt.Operator:NewRail"}])
    n_before = len([p for p in tmp_path.rglob("*") if p.is_file()])
    rep, rows = odpt_static.check(tmp_path, now=t + timedelta(days=30), key=OPEN_KEY,
                                  sleep=0, sleep_fn=lambda s: None)
    assert rep["version"] == "2026-10-13"
    assert [(i["operator"], i["datatype"]) for i in rep["newer"]] == [
        ("odpt.Operator:Toei", "odpt:TrainTimetable")]
    assert rep["same"] == 1                                   # Railway は変わらない
    assert rep["new_operators"] == ["odpt.Operator:NewRail"]
    assert len([p for p in tmp_path.rglob("*") if p.is_file()]) == n_before   # 保存しない
    assert "新しい版: odpt:TrainTimetable / odpt.Operator:Toei" in odpt_static.format_check(rep)


def test_static_or_batches_halve_when_capped(fake, tmp_path, monkeypatch):
    monkeypatch.setattr(odpt_rt, "API_CAP", 4)
    pats = [f"odpt.BusroutePattern:Toei.P{i:02d}" for i in range(20)]
    fake.on("open", "odpt:BusstopPole", lambda q: [
        {"owl:sameAs": f"pole.{i}", "odpt:busroutePattern": pats[i * 2:(i + 1) * 2]}
        for i in range(10)])

    def bp(q):
        if "owl:sameAs" in q:
            vals = q["owl:sameAs"].split(",")
            assert len(vals) <= odpt_static.OR_MAX_VALUES
            return [{"owl:sameAs": v} for v in vals][:4]
        return [{"owl:sameAs": v} for v in pats[:4]]          # 打ち切り
    fake.on("open", "odpt:BusroutePattern", bp)
    ctx = odpt_static._Ctx("odpt.Operator:Toei", OPEN_KEY, timeout=1, retries=0, sleep=0,
                           sleep_fn=lambda s: None)
    recs, how = odpt_static.fetch_complete(ctx, "odpt:BusroutePattern")
    assert sorted(r["owl:sameAs"] for r in recs) == pats
    assert how["capped_parts"] == [] and how["split_keys_used"] == ["owl:sameAs"]
    sames = [q["owl:sameAs"] for s, dt, q, _ in fake.calls
             if dt == "odpt:BusroutePattern" and "owl:sameAs" in q]
    assert sames[0].count(",") == 7          # まだ取れていない 16 件の半分(8 件)から始める
    assert sames[1].count(",") == 3          # 打ち切り → 4 件の束
    assert all(x.count(",") <= 1 for x in sames[2:])         # さらに打ち切り → 2 件の束


def test_batches_respects_size_and_budget():
    vals = ["a" * 10] * 7
    assert [len(b) for b in odpt_static._batches(vals, 3)] == [3, 3, 1]
    assert [len(b) for b in odpt_static._batches(vals, 100, budget=32)] == [3, 3, 1]
    assert [len(b) for b in odpt_static._batches(["x"] * 25, 100)] == [10, 10, 5]   # OR は 10 個まで


# ------------------------------------------------------------------ (7) 秘密
def test_no_secret_in_any_saved_file_url_or_output(fake, tmp_path, capsys, monkeypatch):
    _install_rt(fake)
    _install_static(fake)
    _snap(tmp_path)
    _, rows_rt = _snap(tmp_path, now=NOW + timedelta(minutes=5))
    monkeypatch.setattr(odpt_static, "AIRLINE_OPERATORS", frozenset({"odpt.Operator:JAL"}))
    _, rows_v = odpt_static.fetch_version(tmp_path, types=("odpt:Railway",), now=NOW,
                                          key=OPEN_KEY, sleep=0, sleep_fn=lambda s: None)
    _, rows_s = odpt_static.survey(tmp_path, types=("odpt:Railway", "odpt:Bus"), now=NOW,
                                   key=OPEN_KEY, sleep=0, sleep_fn=lambda s: None)
    ledger.append(tmp_path, rows_rt + rows_v + rows_s)
    # キーは要求には載っている(実際に使っている)
    assert {k for s, _, _, k in fake.calls if s == "open"} == {OPEN_KEY}
    assert {k for s, _, _, k in fake.calls if s == "challenge"} == {CHAL_KEY}
    n_files = 0
    for p in tmp_path.rglob("*"):
        if not p.is_file():
            continue
        n_files += 1
        b = p.read_bytes()
        text = gzip.decompress(b).decode("utf-8") if p.name.endswith(".gz") else b.decode("utf-8")
        assert not common.contains_secret(text), p.name
        assert OPEN_KEY not in text and CHAL_KEY not in text
    assert n_files >= 10
    for r in rows_rt + rows_v + rows_s:
        assert not common.contains_secret(json.dumps(r, ensure_ascii=False))
    url = odpt_rt.display_url("open", "odpt:Bus", {"odpt:operator": "odpt.Operator:Toei"})
    assert url.endswith("acl:consumerKey=***")
    common.log(odpt_rt.api_url("open", "odpt:Bus", {}, OPEN_KEY))    # ログの口も潰す
    out = capsys.readouterr()
    assert OPEN_KEY not in out.out + out.err and "***" in out.out


def test_cross_host_redirect_refused_and_not_retried(monkeypatch):
    h = common._GuardedRedirectHandler()
    req = urllib.request.Request("https://api.odpt.org/api/v4/odpt:Calendar.json?x=1")
    req.same_host_only = True

    class _FP:
        def close(self):
            pass
    with pytest.raises(common.CrossHostRedirect) as ei:
        h.redirect_request(req, _FP(), 302, "Found", {}, "https://elsewhere.example.net/blob")
    assert ei.value.host == "elsewhere.example.net"
    same = h.redirect_request(req, _FP(), 302, "Found", {}, "https://api.odpt.org/api/v4/b")
    assert same is not None and same.same_host_only is True
    req2 = urllib.request.Request("https://www.example.org/a")          # 印の無い要求は標準どおり
    assert h.redirect_request(req2, _FP(), 302, "Found", {}, "https://other.example.org/b")

    n = {"calls": 0}

    def boom(req, timeout):
        n["calls"] += 1
        assert getattr(req, "same_host_only", False) is True
        raise common.CrossHostRedirect("elsewhere.example.net")
    monkeypatch.setattr(common, "_urlopen", boom)
    res = common.http_get("https://api.odpt.org/api/v4/odpt:Calendar.json", retries=3,
                          sleep_fn=lambda s: None, same_host_only=True)
    assert res.error == "cross-host-redirect-refused:elsewhere.example.net"
    assert n["calls"] == 1 and not res.ok


# ------------------------------------------------------------------ CLI(ネットに出ない口)
def test_offline_makes_zero_requests(monkeypatch, tmp_path, capsys):
    def boom(req, timeout):
        raise AssertionError("ネットワークに出た")
    monkeypatch.setattr(common, "_urlopen", boom)
    common.reset_request_count()
    rc = cli.main(["--offline", "--source", "odpt_rt,odpt_static", "--out-dir", str(tmp_path)])
    assert rc == 0 and common.request_count() == 0
    out = capsys.readouterr().out
    assert "odpt:Bus" in out and "odpt:TrainTimetable" in out


def test_report_includes_rt_gaps_and_disk_usage(monkeypatch, tmp_path, capsys):
    def boom(req, timeout):
        raise AssertionError("ネットワークに出た")
    monkeypatch.setattr(common, "_urlopen", boom)
    day = tmp_path / "odpt_rt" / "2026" / "10" / "2026-10-12"
    day.mkdir(parents=True)
    (day / "bus_Toei_120000.json.gz").write_bytes(b"x" * 7000)
    (day / "train_Toei_120000.json.gz").write_bytes(b"x" * 3000)
    (day / "traininformation_Toei_120000.json.gz").write_bytes(b"x" * 1000)
    (day / "train_120000.json").write_bytes(b"x" * 500)                     # 古い形も在線に数える
    ledger.append(tmp_path, [_row(datetime(2026, 10, 12, 12, 0, tzinfo=JST))])
    rep = ledger.disk_usage(tmp_path, datetime(2026, 10, 13).date())
    cats = rep["categories"]
    assert cats["odpt_rt/バス"]["bytes"] == 7000 and cats["odpt_rt/在線"]["bytes"] == 3500
    assert cats["odpt_rt/運行情報"]["window_bytes"] == 1000
    assert abs(cats["odpt_rt/バス"]["per_day_bytes"] - 1000) < 1e-9          # 7 日で割る
    rc = cli.main(["--report", "--date", "2026-10-13", "--out-dir", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "欠けた時間帯" in out and "ディスクの量" in out and "odpt_rt/バス" in out


def test_frequent_run_skips_full_ledger_report(fake, tmp_path, capsys, monkeypatch):
    _install_rt(fake)
    monkeypatch.setattr(odpt_rt, "OPEN_RT_OPERATORS", _open_ops())
    monkeypatch.setenv(odpt_rt.OPEN_KEY_ENV, OPEN_KEY)
    monkeypatch.setenv(odpt_rt.CHALLENGE_KEY_ENV, CHAL_KEY)
    monkeypatch.setattr(common, "now_jst", lambda: NOW)
    rc = cli.main(["--source", "odpt_rt", "--out-dir", str(tmp_path), "--sleep", "0"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "未取得日の検出" not in out and "[done] 台帳へ 8 行追記" in out
    assert OPEN_KEY not in out and CHAL_KEY not in out
