# -*- coding: utf-8 -*-
"""tools/night5070(回答 10-25 §6-0): 夜の実験の起動・健全性の確認・計測の分離の一覧・タスクの XML。

GPU・外のネットワーク・実 LLM は使わない。艦隊は試験の中の小さな HTTP サーバー(127.0.0.1・空いた口)。
スリープの抑止(SetThreadExecutionState)は試験では記録だけの代わりに差し替える。
"""
from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
import sys
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_DIR = _ROOT / "tools" / "night5070"
_NS = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"night5070_{name}", _DIR / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def nr():
    return _load("night_run")


@pytest.fixture(scope="module")
def rt():
    return _load("register_task")


@pytest.fixture(scope="module")
def real_cfg(nr):
    return nr.load_config(_DIR / "experiments.json")


@pytest.fixture(autouse=True)
def awake_calls(nr, monkeypatch):
    calls: list[bool] = []

    def fake(on: bool) -> bool:
        calls.append(on)
        return True

    monkeypatch.setattr(nr, "keep_awake", fake)
    return calls


# ------------------------------------------------------------------ 偽の艦隊


class _FakeFleet(BaseHTTPRequestHandler):
    reply = "朝です\n二行目"
    model_id = "fake-model"
    hits: list[str] = []

    def log_message(self, *a):  # noqa: D401 - 静かに
        pass

    def _send(self, code: int, obj) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):  # noqa: N802
        type(self).hits.append("GET " + self.path)
        if self.path == "/v1/models":
            self._send(200, {"object": "list", "data": [{"id": type(self).model_id}]})
        else:
            self._send(404, {})

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(n).decode("utf-8"))
        type(self).hits.append("POST " + self.path + " " + body.get("model", ""))
        if self.path == "/v1/chat/completions":
            self._send(200, {"choices": [{"message": {"role": "assistant", "content": type(self).reply},
                                          "finish_reason": "stop"}],
                             "usage": {"prompt_tokens": 10, "completion_tokens": 3}})
        else:
            self._send(404, {})


@pytest.fixture()
def fake_fleet():
    _FakeFleet.hits = []
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _FakeFleet)
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}"
    finally:
        srv.shutdown()
        srv.server_close()


def _py(code: str) -> list[str]:
    return [sys.executable, "-c", code]


_FAKE_STDOUT = (
    "[run] n=50 cells=10 seed=1 world=synthetic\n"
    "  壁時計 12.50s (W2 上限 600s) / 移動+密度 0.100 ms/x (P2 上限 5 ms)\n"
    "  LLM呼 1,234 = 24.68 呼/体/日 (L4 制御目標 10)\n"
    "  保存則 Σmoney 100 + Σrevenue 0 + Σ運賃 0 = 100 (初期 100) OK / 最小在庫 0\n"
    "  内訳[ms/x] presence 0.10 / fleet_wait 3.50 / llm 1.20 / 合計 8.00\n"
    "[艦隊] 呼 1,234 / 帳尻 1,230 ・繰り延べ 4(再投入 2・再送 1) ・TTFT p50/p99 0.20/0.90s"
    " ・e2e p50/p99 0.30/1.10s ・temp 0.7 max_tok 96 ・cache_salt abcd…(smoke)\n"
    "[艦隊書式] エラー率 実効 0.010 / 厳密 0.020 (受入 ≤0.10)\n"
)

#: stop が呼ばれるたびに 1 行足す(起動の前の掃除と最後の 2 回)。
_STOP_CODE = ("import pathlib,sys; p=pathlib.Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True);"
              " f=p.read_text(encoding='utf-8') if p.exists() else ''; p.write_text(f+'stop\\n', encoding='utf-8');"
              " sys.exit(int(sys.argv[2]))")


def _test_cfg(endpoint: str, *, commands: list[dict], needs_fleet: bool = True, stop_rc: int = 0) -> dict:
    return {
        "deadline_hours": 0.2,
        "env": {"PYTHONIOENCODING": "utf-8"},
        "vars": {"PORT_HOLE": None},
        "fleet": {
            "endpoints": [endpoint],
            "model": "",
            "start": {"argv": _py("pass"), "timeout_s": 30},
            "health": {"wait_s": 5, "poll_s": 0.1, "max_tokens": 8},
            "stop": {"argv": _py(_STOP_CODE) + ["{{DATA}}/stop_calls.txt", str(stop_rc)], "timeout_s": 30},
        },
        "experiments": {
            "T1": {"purpose": "試験", "needs_fleet": needs_fleet, "sim_days": 1, "estimated_minutes": 30,
                   "preconditions": ["試験の注"], "commands": commands,
                   "outputs": {"checkpoints": "{{DATA}}/checkpoints.json", "tape": "{{DATA}}/tape"}},
            "T2": {"purpose": "次", "estimated_minutes": None, "commands": []},
        },
    }


def _write_cfg(tmp_path: Path, cfg: dict) -> Path:
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(cfg, ensure_ascii=False), encoding="utf-8")
    return p


def _only(root: Path) -> Path:
    ds = [d for d in root.iterdir() if d.is_dir()]
    assert len(ds) == 1, ds
    return ds[0]


def _run(nr, tmp_path: Path, cfg: dict, **kw) -> tuple[int, Path, Path]:
    out, data = tmp_path / "out", tmp_path / "data"
    rc = nr.run_night("T1", config_path=_write_cfg(tmp_path, cfg), out_root=out, data_root=data, **kw)
    return rc, _only(out), data


def _assert_written(d: Path) -> str:
    for n in ("summary.md", "metrics.json", "metrics.md", "night_run.json", "NIGHT_DONE"):
        assert (d / n).exists(), n
    assert (d.parent / "_night_runs.log").exists()
    return (d / "summary.md").read_text(encoding="utf-8")


def _stop_count(data: Path) -> int:
    p = _only(data) / "stop_calls.txt"
    return len(p.read_text(encoding="utf-8").splitlines()) if p.exists() else 0


# ------------------------------------------------------------------ (a) 設定の読みと穴


def test_real_config_has_e1_to_e8_and_blank_estimates(nr, real_cfg):
    exps = real_cfg["experiments"]
    assert list(exps) == [f"E{i}" for i in range(1, 9)]
    for e in exps.values():
        assert e["estimated_minutes"] is None  # 親が R-C で埋める空欄
        assert e["purpose"] and e["commands"]
    assert any("2-7" in p for p in exps["E1"]["preconditions"]) and exps["E1"]["before_2_7"] is True
    assert exps["E3"]["needs_fleet"] is False and exps["E8"]["needs_fleet"] is False
    # 大きな出力は DATA(data/night5070)の側
    e1 = " ".join(exps["E1"]["commands"][0]["argv"])
    assert "{{DATA}}/tape" in e1 and "{{DATA}}/checkpoints.json" in e1 and "{{OUT}}" not in json.dumps(real_cfg)


def test_real_config_holes_detected(nr, real_cfg):
    holes = {h["name"] for h in nr.holes_for(real_cfg, "E1")}
    assert {"WSL_DISTRO", "MODEL", "VLLM_BIN", "VLLM_ENV", "VLLM_ARGS"} <= holes
    assert not holes & {"OUT", "DATA", "ENDPOINTS", "VLLM_PORT"}
    assert nr.holes_for(real_cfg, "E3") == []  # 艦隊を使わない実験は艦隊の穴を数えない
    allh = nr.all_holes(real_cfg)
    assert "E2_ARM_FLAGS" in allh["names"] and allh["no_estimate"] == [f"E{i}" for i in range(1, 9)]


def test_filled_vars_remove_holes_and_list_splices(nr, real_cfg):
    cfg = copy.deepcopy(real_cfg)
    cfg["vars"].update(WSL_DISTRO="Distro", MODEL="m", VLLM_BIN="~/v/bin/vllm", VLLM_ENV="", VLLM_ARGS="")
    assert nr.holes_for(cfg, "E1") == []
    argv = nr.expand_argv(["a", "{{L}}", "x{{S}}y", "{{NONE}}"], {"L": ["--p", "1"], "S": "z", "NONE": None})
    assert argv == ["a", "--p", "1", "xzy", "{{NONE}}"]


# ------------------------------------------------------------------ (b) dry-run


def test_dry_run_writes_summary_without_running(nr, tmp_path, monkeypatch, awake_calls):
    def _no(*a, **k):
        raise AssertionError("dry-run はコマンドを回さない")

    monkeypatch.setattr(nr.subprocess, "run", _no)
    out, data = tmp_path / "out", tmp_path / "data"
    rc = nr.run_night("E1", config_path=_DIR / "experiments.json", out_root=out, data_root=data, dry_run=True,
                      start_at="01:00")
    assert rc == 0
    d = _only(out)
    assert d.name.endswith("_E1_dryrun") and not data.exists()  # dry-run は大きな出力の置き場を作らない
    s = _assert_written(d)
    assert "dry-run" in s and "shibuya.cli" in s and "WSL_DISTRO" in s and "空欄(R-C で埋める)" in s
    assert "参考値(2-7 の直しの前)" in s and "start_at 01:00 から" in s
    assert str(_ROOT) not in s and str(Path.home()) not in s  # 道筋は置き換える
    m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    assert m["n_measured"] == 0
    assert (d / "NIGHT_DONE").read_text(encoding="utf-8").strip() == "dry-run"
    assert awake_calls == []  # dry-run ではスリープを止めない


def test_holes_stop_before_fleet(nr, tmp_path, monkeypatch):
    def _no(*a, **k):
        raise AssertionError("穴があれば艦隊を立てない")

    monkeypatch.setattr(nr.subprocess, "run", _no)
    out = tmp_path / "out"
    rc = nr.run_night("E1", config_path=_DIR / "experiments.json", out_root=out, data_root=tmp_path / "data")
    assert rc == 3
    s = _assert_written(_only(out))
    assert "失敗" in s and "設定の穴" in s


# ------------------------------------------------------------------ (c) 健全性の確認


def test_health_check_passes_with_fake_fleet(nr, fake_fleet):
    h = nr.check_health([fake_fleet], wait_s=5, poll_s=0.1)
    assert h["ok"] is True and h["model"] == "fake-model"
    assert h["endpoints"][0]["completion_line"] == "朝です"
    assert any(x.startswith("POST /v1/chat/completions fake-model") for x in _FakeFleet.hits)
    assert nr.check_health([fake_fleet], model="fake-model", wait_s=5, poll_s=0.1)["ok"] is True


def test_health_check_rejects_other_served_model(nr, fake_fleet):
    with pytest.raises(nr.NightFailure, match="served-model-name"):
        nr.check_health([fake_fleet], model="qwen3-8b", wait_s=5, poll_s=0.1)


def test_health_check_times_out_without_fleet(nr, monkeypatch):
    t = {"now": 0.0}

    def refused(*a, **k):
        raise ConnectionRefusedError("偽の拒否")

    monkeypatch.setattr(nr, "http_json", refused)

    def clock():
        return t["now"]

    def sleep(s):
        t["now"] += s

    with pytest.raises(nr.NightFailure, match="/v1/models"):
        nr.check_health(["http://127.0.0.1:1"], wait_s=1.0, poll_s=0.5, sleep=sleep, clock=clock)


def test_health_check_fails_on_empty_completion(nr, fake_fleet, monkeypatch):
    monkeypatch.setattr(_FakeFleet, "reply", "   ")
    with pytest.raises(nr.NightFailure, match="1 行"):
        nr.check_health([fake_fleet], wait_s=5, poll_s=0.1)


# ------------------------------------------------------------------ (d) 成功と失敗の通し


def test_success_run_fills_metrics(nr, fake_fleet, tmp_path, awake_calls):
    cp = {"final_hash": "f" * 64, "n_agents": 50,
          "checkpoints": [{"combined": "a1", "behavior_hash": "b1"}, {"combined": "a2", "behavior_hash": "b2"}],
          "manifest": {"action_usage": {"歩く": 3}, "calls_by_condition": {"c": 1},
                       "decision_layers": {"total": 1}, "fleet": {"n_replicas": 1},
                       "daily": [{"events": {"on": True, "rows": 7, "by_what": {"会う": 2}}}]}}
    code = ("import json,sys,pathlib; sys.stdout.write(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'));"
            " pathlib.Path(sys.argv[2]).write_text(sys.argv[3], encoding='utf-8')")
    so = tmp_path / "so.txt"
    so.write_text(_FAKE_STDOUT, encoding="utf-8")
    cmd = _py(code) + [str(so), "{{DATA}}/checkpoints.json", json.dumps(cp, ensure_ascii=False)]
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": cmd}])
    cfg["cost"] = {"yen_per_hour": 36.0}
    rc, d, data = _run(nr, tmp_path, cfg, start_at="01:00")
    s = _assert_written(d)
    assert rc == 0, s
    assert "**成功**" in s and "発射 1,234" in s and "30 分" in s and "T2(次)" in s and "艦隊が落ちていない" not in s
    assert "start_at 01:00 から" in s and "| 01:30 |" in s
    m = {f["key"]: f for f in json.loads((d / "metrics.json").read_text(encoding="utf-8"))["fields"]}
    assert m["llm.fired"]["value"] == 1234 and m["llm.deferred"]["value"] == 4
    assert m["llm.wait_ms_per_step"]["value"] == 3.5
    assert m["agents.action_usage"]["value"] == {"歩く": 3}
    assert m["agents.events"]["value"] == {"rows": 7, "by_what": {"会う": 2}}
    assert m["determinism.conservation"]["value"] == "OK"
    assert len(m["determinism.state_hashes"]["value"]) == 2
    assert m["cost.yen_per_sim_day"]["status"] == "計測"
    assert m["llm.health"]["value"]["model"] == "fake-model"
    assert "checkpoints.json" in m["agents.action_usage"]["source"]
    assert _stop_count(data) == 2  # 起動の前の掃除と最後
    assert (_only(data) / "logs").is_dir() and not (d / "logs").exists()  # ログは大きな出力の側
    assert awake_calls == [True, False]  # スリープを止めて戻した


def test_failed_command_writes_failure_and_stops_fleet(nr, fake_fleet, tmp_path):
    bad = _py("import sys; sys.stderr.write('Traceback (most recent call last):\\n  boom\\nValueError: x\\n');"
              " sys.exit(3)")
    after = _py("import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('x')") + ["{{DATA}}/never.txt"]
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": bad}, {"name": "after", "argv": after}])
    rc, d, data = _run(nr, tmp_path, cfg)
    assert rc == 1
    s = _assert_written(d)
    assert "**失敗**" in s and "実験: run" in s and "終了コード 3" in s and "ValueError: x" in s
    assert _stop_count(data) == 2
    st = json.loads((d / "night_run.json").read_text(encoding="utf-8"))
    names = [x["name"] for x in st["steps"]]
    assert "実験: after" not in names and not (_only(data) / "never.txt").exists()  # 途中で止める
    assert names[-1] == "艦隊を落とす"
    assert (d / "NIGHT_DONE").read_text(encoding="utf-8").strip() == "失敗"


def test_start_failure_stops_fleet(nr, fake_fleet, tmp_path):
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("print('ok')")}])
    cfg["fleet"]["start"]["argv"] = _py("import sys; sys.stderr.write('起動できない\\n'); sys.exit(5)")
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 1 and "艦隊を立てる" in s and "終了コード 5" in s and "起動できない" in s
    assert _stop_count(data) == 2


def test_health_failure_stops_fleet(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(_FakeFleet, "reply", "  ")
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("print('ok')")}])
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 1 and "健全性の確認" in s and "1 行" in s
    assert _stop_count(data) == 2
    m = {f["key"]: f for f in json.loads((d / "metrics.json").read_text(encoding="utf-8"))["fields"]}
    assert m["llm.health"]["value"]["ok"] is False


def test_deadline_exceeded_stops_fleet(nr, fake_fleet, tmp_path):
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("import time; time.sleep(60)")}])
    rc, d, data = _run(nr, tmp_path, cfg, deadline_hours=3.0 / 3600.0)
    s = _assert_written(d)
    assert rc == 1 and "時間切れ" in s
    assert _stop_count(data) == 2


def test_unexpected_exception_stops_fleet(nr, fake_fleet, tmp_path, monkeypatch, awake_calls):
    def boom(*a, **k):
        raise ZeroDivisionError("想定外の試験")

    monkeypatch.setattr(nr, "check_health", boom)
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("print('ok')")}])
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 1 and "想定外: ZeroDivisionError" in s
    assert _stop_count(data) == 2
    assert awake_calls == [True, False]


def test_stop_failure_marks_cleanup_failed(nr, fake_fleet, tmp_path):
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("print('ok')")}], stop_rc=1)
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 4
    assert s.splitlines()[2].startswith("> **艦隊が落ちていない。wsl --shutdown を手で。**")
    assert "成功(後始末に失敗)" in s
    assert (d / "NIGHT_DONE").read_text(encoding="utf-8").strip() == "成功(後始末に失敗)"
    st = json.loads((d / "night_run.json").read_text(encoding="utf-8"))
    assert st["fleet_stop_failed"] is True
    assert _stop_count(data) == 2  # 起動の前の掃除の失敗は無視して進む


def test_broken_tape_and_checkpoints_are_unreadable(nr, fake_fleet, tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    good = tmp_path / "good.parquet"
    pq.write_table(pa.table({"agent_id": [1, 2], "deferred": [0, 0], "tokens_in": [1, 2]}), good)
    cut = tmp_path / "cut.parquet"
    cut.write_bytes(good.read_bytes()[:-12])  # footer の無い途中のファイル(途中で落ちたラン)
    code = ("import shutil,sys,pathlib; t=pathlib.Path(sys.argv[2]); t.mkdir(parents=True, exist_ok=True);"
            " shutil.copy(sys.argv[1], t / 'calls.parquet'); pathlib.Path(sys.argv[3]).write_text('{', encoding='utf-8');"
            " sys.stdout.write(pathlib.Path(sys.argv[4]).read_text(encoding='utf-8'))")
    so = tmp_path / "so.txt"
    so.write_text(_FAKE_STDOUT, encoding="utf-8")
    cmd = _py(code) + [str(cut), "{{DATA}}/tape", "{{DATA}}/checkpoints.json", str(so)]
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": cmd}])
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 0, s
    m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    f = {x["key"]: x for x in m["fields"]}
    assert f["tokens.in_per_call"]["value"].startswith("未計測(読めない: ")
    assert f["agents.action_usage"]["value"] == "未計測(読めない: JSONDecodeError)"
    assert f["llm.fired"]["value"] == 1234  # 読めた所は埋める
    assert set(m["unreadable"]) == {"tape", "checkpoints"}
    assert _stop_count(data) == 2


def test_summary_writer_failure_still_writes_all(nr, fake_fleet, tmp_path, monkeypatch):
    def broken(*a, **k):
        raise KeyError("要約の試験")

    monkeypatch.setattr(nr, "write_summary", broken)
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("print('ok')")}])
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert "簡易" in s and "KeyError" in s
    assert _stop_count(data) == 2


def test_mock_experiment_skips_fleet(nr, tmp_path):
    cfg = _test_cfg("http://127.0.0.1:9", commands=[{"name": "run", "argv": _py("print('ok')")}],
                    needs_fleet=False)
    rc, d, data = _run(nr, tmp_path, cfg)
    assert rc == 0
    st = json.loads((d / "night_run.json").read_text(encoding="utf-8"))
    assert [x["name"] for x in st["steps"]] == ["設定を読む", "実験: run"]
    assert _stop_count(data) == 0


def test_background_start_is_stopped(nr, fake_fleet, tmp_path):
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("print('ok')")}])
    cfg["fleet"]["start"] = {"argv": _py("import time; time.sleep(120)"), "background": True}
    rc, d, data = _run(nr, tmp_path, cfg)
    assert rc == 0
    st = json.loads((d / "night_run.json").read_text(encoding="utf-8"))
    last = st["steps"][-1]
    assert last["name"] == "艦隊を落とす" and "背後の起動を止めた" in last["detail"]


def test_run_dir_never_overwrites(nr, tmp_path):
    a, ad = nr.make_run_dir(tmp_path / "o", tmp_path / "d", "2026-10-25", "E1", False)
    b, bd = nr.make_run_dir(tmp_path / "o", tmp_path / "d", "2026-10-25", "E1", False)
    assert a.name == ad.name == "2026-10-25_E1" and b.name == bd.name == "2026-10-25_E1_r2"
    (tmp_path / "d" / "2026-10-25_E1_r3").mkdir()  # 大きな出力の側にだけある名も避ける
    c, _ = nr.make_run_dir(tmp_path / "o", tmp_path / "d", "2026-10-25", "E1", False)
    assert c.name == "2026-10-25_E1_r4"


# ------------------------------------------------------------------ (e) タスクの XML


def _xml_root(xml: str) -> ET.Element:
    return ET.fromstring(xml.split("\n", 1)[1])  # 宣言の encoding=UTF-16 を外して str で読む


@pytest.mark.parametrize("wake", [False, True])
def test_print_only_xml_battery_and_wake(rt, capsys, wake):
    argv = ["--at", "01:00", "--experiment", "E1", "--print-only"] + (["--wake"] if wake else [])
    assert rt.main(argv) == 0
    outp = capsys.readouterr().out
    xml = outp[: outp.index("</Task>") + len("</Task>")]
    s = {el.tag.split("}")[1]: (el.text or "") for el in _xml_root(xml).find("t:Settings", _NS)}
    assert s["DisallowStartIfOnBatteries"] == "false"
    assert s["StopIfGoingOnBatteries"] == "false"
    assert s["StartWhenAvailable"] == "true"
    assert s["MultipleInstancesPolicy"] == "IgnoreNew"
    assert s["ExecutionTimeLimit"] == "PT10H"
    assert s["WakeToRun"] == ("true" if wake else "false")
    args = _xml_root(xml).find("t:Actions/t:Exec/t:Arguments", _NS).text
    assert "night_run.py --experiment E1 --deadline-hours 9.5 --start-at 01:00" in args
    assert "*>> 'docs/bench/night5070/_scheduler.log'" in args
    assert str(Path.home()) not in outp  # 表示では <HOME> に置き換える(XML の中は &lt;HOME&gt;)
    assert "schtasks /create /tn \\shibuya-v2-night5070 /xml" in outp


def test_xml_powershell_trigger_and_workdir(rt):
    start = rt.next_start("01:00", now=dt.datetime(2026, 10, 25, 23, 0))
    assert start == dt.datetime(2026, 10, 26, 1, 0)
    xml = rt.build_xml(experiment="E3", start=start, daily=True, max_hours=8, python="PY", workdir="W'D")
    root = _xml_root(xml)
    assert root.find("t:Triggers/t:CalendarTrigger/t:StartBoundary", _NS).text == "2026-10-26T01:00:00"
    ex = root.find("t:Actions/t:Exec", _NS)
    assert ex.find("t:Command", _NS).text == "powershell.exe"
    a = ex.find("t:Arguments", _NS).text
    assert a.startswith("-NoProfile -WindowStyle Hidden -Command \"Set-Location 'W''D'; ")
    assert "& 'PY' tools/night5070/night_run.py --experiment E3 --deadline-hours 7.5" in a
    assert ex.find("t:WorkingDirectory", _NS).text == "W'D"
    assert root.find("t:Settings/t:ExecutionTimeLimit", _NS).text == "PT8H"
    assert root.find("t:Principals/t:Principal/t:LogonType", _NS).text == "InteractiveToken"
    once = rt.build_xml(experiment="E1", start=start, python="PY")
    assert "<TimeTrigger>" in once and "<CalendarTrigger>" not in once
    assert str(rt.REPO) in once  # 作業ディレクトリはスクリプトの位置から実行時に求める


def test_deadline_not_shorter_than_limit_is_refused(rt, capsys):
    start = dt.datetime(2026, 10, 26, 1, 0)
    with pytest.raises(ValueError):
        rt.build_xml(experiment="E1", start=start, max_hours=9, deadline_hours=9)
    assert rt.main(["--experiment", "E1", "--max-hours", "6", "--deadline-hours", "7", "--print-only"]) == 2
    assert "登録しない" in capsys.readouterr().err


def test_delete_print_only(rt, capsys):
    assert rt.main(["--delete", "--print-only"]) == 0
    assert capsys.readouterr().out.strip() == "schtasks /delete /tn \\shibuya-v2-night5070 /f"


# ------------------------------------------------------------------ (f) 未計測の埋め方


def test_metrics_unmeasured_when_outputs_missing(nr):
    m = nr.build_metrics()
    assert m["n_measured"] == 0
    assert all(f["value"] == "未計測" and f["status"] == "未計測" and f["source"] == "" for f in m["fields"])
    by = {f["key"]: f for f in m["fields"]}
    for k in ("engine.phase_ms_per_step", "llm.fired", "llm.ttft_s", "llm.per_gpu", "tokens.in_per_call",
              "wake.candidates", "agents.conversations", "determinism.tape_replay", "anchors.presence",
              "cost.yen_per_sim_day"):
        assert k in by
    assert "calls.parquet" in by["tokens.in_per_call"]["source_planned"]  # 取る予定の出所は残す


def test_metrics_partial_stdout_without_fleet_line(nr):
    text = "\n".join(ln for ln in _FAKE_STDOUT.splitlines() if not ln.startswith("[艦隊"))
    m = {f["key"]: f for f in nr.build_metrics(stdout_text=text, stdout_name="logs/x.log")["fields"]}
    assert m["engine.wall_seconds"]["value"] == 12.5 and m["engine.wall_seconds"]["source"].startswith("logs/x.log")
    assert m["agents.calls_per_agent_day"]["value"] == 24.68
    assert m["llm.fired"]["status"] == "未計測" and m["llm.ttft_s"]["value"] == "未計測"
    assert m["llm.failed"]["status"] == "未計測" and m["llm.failed"]["note"]
    assert m["cost.yen_per_sim_day"]["status"] == "未計測"  # 円の設定が空欄


def test_read_tape_counts_and_answered_only_tokens(nr, tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    t = pa.table({"agent_id": [1, 1, 2], "wake_class": [0, 1, 1], "tokens_in": [10, 20, 30],
                  "tokens_out": [3, 3, 6], "deferred": [0, 1, 0], "deferred_reason": ["", "queue_full", ""],
                  "response": ["a", "b", "c"]})
    pq.write_table(t, tmp_path / "calls.parquet")
    r = nr.read_tape(tmp_path)
    assert r["rows"] == 3 and r["answered"] == 2 and r["deferred"] == 1
    assert r["deferred_reason"] == {"queue_full": 1}
    assert r["tokens_in"] == {"sum": 40, "mean": 20.0, "rows": 2}  # deferred=0 の行だけ
    assert r["tokens_out"] == {"sum": 9, "mean": 4.5, "rows": 2}
    assert r["by_wake_class"] == {"0": {"rows": 1, "deferred": 0}, "1": {"rows": 2, "deferred": 1}}
    assert r["distinct_agents"] == 2
    assert nr.read_tape(tmp_path / "none") is None


def test_read_tape_reads_only_needed_columns(nr, tmp_path, monkeypatch):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    pq.write_table(pa.table({"agent_id": [1], "response": ["長い応答"], "deferred": [0]}), tmp_path / "calls.parquet")
    seen: dict = {}
    real = pq.read_table

    def spy(p, columns=None, **k):
        seen["columns"] = columns
        return real(p, columns=columns, **k)

    monkeypatch.setattr(pq, "read_table", spy)
    nr.read_tape(tmp_path)
    assert seen["columns"] == ["agent_id", "deferred"]


def test_mask_paths(nr):
    wsl_path = "/home" + "/someone/.venv/bin/vllm"  # 連結=道筋の検査(commit_check)に当てないため
    t = f"{nr.REPO}/a {sys.executable} " + json.dumps(str(nr.REPO)) + " " + wsl_path
    m = nr.mask_paths(t)
    assert str(nr.REPO) not in m and sys.executable not in m and "<REPO>" in m and "<PYTHON>" in m
    assert "<WSLHOME>/.venv/bin/vllm" in m and "someone" not in m


def test_night_runs_log_is_masked(nr, tmp_path):
    cfg = _test_cfg("http://127.0.0.1:9", commands=[{"name": "run", "argv": _py("print('ok')")}],
                    needs_fleet=False)
    rc, d, data = _run(nr, tmp_path, cfg)
    line = (d.parent / "_night_runs.log").read_text(encoding="utf-8")
    assert rc == 0 and str(Path.home()) not in line and "<HOME>" in line
