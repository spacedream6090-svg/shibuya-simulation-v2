# -*- coding: utf-8 -*-
"""tools/night5070(回答 10-25 §6-0): 夜の実験の起動・健全性の確認・計測の分離の一覧・タスクの XML。

GPU・外のネットワーク・実 LLM は使わない。艦隊は試験の中の小さな HTTP サーバー(127.0.0.1・空いた口)。
スリープの抑止(SetThreadExecutionState)は試験では記録だけの代わりに差し替える。
WSLENV・.wslconfig・nvidia-smi は試験では差し替える(手元の機械の状態に左右されない)。
"""
from __future__ import annotations

import copy
import datetime as dt
import importlib.util
import json
import subprocess
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


@pytest.fixture(autouse=True)
def quiet_machine(nr, monkeypatch):
    """手元の機械の状態(WSLENV・.wslconfig・GPU)を試験から切り離す。"""
    monkeypatch.delenv("WSLENV", raising=False)
    monkeypatch.setattr(nr, "read_wslconfig", lambda: None)
    real = {"query_vram": nr.query_vram, "restrict_key_acl": nr.restrict_key_acl}
    monkeypatch.setattr(nr, "query_vram", lambda *a, **k: None)
    monkeypatch.setattr(nr, "restrict_key_acl", lambda p: "試験(ACL は変えない)")
    monkeypatch.setattr(nr, "_vram_sleep", lambda s: None)  # VRAM の待ちは眠らない
    return real


# ------------------------------------------------------------------ 偽の艦隊


class _FakeFleet(BaseHTTPRequestHandler):
    reply = "朝です\n二行目"
    model_id = "fake-model"
    hits: list[str] = []
    auth: list[str] = []

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
        type(self).auth.append(self.headers.get("Authorization", ""))
        if self.path == "/v1/models":
            self._send(200, {"object": "list", "data": [{"id": type(self).model_id}]})
        else:
            self._send(404, {})

    def do_POST(self):  # noqa: N802
        n = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(n).decode("utf-8"))
        type(self).hits.append("POST " + self.path + " " + body.get("model", ""))
        type(self).auth.append(self.headers.get("Authorization", ""))
        if self.path == "/v1/chat/completions":
            self._send(200, {"choices": [{"message": {"role": "assistant", "content": type(self).reply},
                                          "finish_reason": "stop"}],
                             "usage": {"prompt_tokens": 10, "completion_tokens": 3}})
        else:
            self._send(404, {})


@pytest.fixture()
def fake_fleet():
    _FakeFleet.hits = []
    _FakeFleet.auth = []
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


#: 安全の規則 1・2 に合う起動の引数(試験の起動のコマンドは python -c で、引数は読まずに捨てる)。
_SAFE_ARGS = ["--host", "127.0.0.1", "--api-key", "{{API_KEY}}", "--load-format", "safetensors"]


def _test_cfg(endpoint: str, *, commands: list[dict], needs_fleet: bool = True, stop_rc: int = 0) -> dict:
    return {
        "deadline_hours": 0.2,
        "env": {"PYTHONIOENCODING": "utf-8"},
        "vars": {"PORT_HOLE": None},
        "fleet": {
            "endpoints": [endpoint],
            "model": "",
            "start": {"argv": _py("pass") + _SAFE_ARGS, "timeout_s": 30},
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
    cfg["vars"].update(WSL_DISTRO="Distro", MODEL="m", VLLM_BIN="~/v/bin/vllm", VLLM_ENV="", VLLM_ARGS="",
                       MODEL_GB=5.68, VRAM_PLAN_GB=9.0)  # VRAM の調整の 2 つの穴(5070 の段 11-01 で足した)
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
    cfg["fleet"]["start"]["argv"] = _py("import sys; sys.stderr.write('起動できない\\n'); sys.exit(5)") + _SAFE_ARGS
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
    cfg["fleet"]["start"] = {"argv": _py("import time; time.sleep(120)") + _SAFE_ARGS, "background": True}
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


def test_night_runs_log_is_masked(nr, tmp_path, monkeypatch):
    # CI(Linux)では tmp_path がホームの下に無いので、ホームを tmp_path に固定して <HOME> の置換を確かめる(第340)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    cfg = _test_cfg("http://127.0.0.1:9", commands=[{"name": "run", "argv": _py("print('ok')")}],
                    needs_fleet=False)
    rc, d, data = _run(nr, tmp_path, cfg)
    line = (d.parent / "_night_runs.log").read_text(encoding="utf-8")
    assert rc == 0 and str(Path.home()) not in line and "<HOME>" in line


# ------------------------------------------------------------------ (g) 試走 --smoke(5070 の完了の条件 4)


def test_real_config_e1_smoke_holes_and_defaults(nr, real_cfg):
    e1 = real_cfg["experiments"]["E1"]
    argv = e1["commands"][0]["argv"]
    assert argv[argv.index("--agents") + 1] == "{{AGENTS}}" and argv[argv.index("--ticks") + 1] == "{{TICKS}}"
    assert real_cfg["vars"]["AGENTS"] == 5000 and real_cfg["vars"]["TICKS"] == 1440  # 既定の意味は変えない
    assert e1["smoke"]["vars"] == {"AGENTS": 500, "TICKS": 120}
    holes = {h["name"] for h in nr.holes_for(real_cfg, "E1")}
    assert "VRAM_PLAN_GB" in holes and not holes & {"AGENTS", "TICKS", "API_KEY", "MODEL_GB"}
    assert real_cfg["vars"]["MODEL_GB"] == 5.68  # R-123 §3 の 5,816 MiB(親の指示 11-01)
    assert real_cfg["fleet"]["vram"]["max_num_seqs_steps"] == [32, 16, 8]


def test_nested_var_holes_and_expansion(nr):
    cfg = {"vars": {"VLLM_ARGS": "--a {{FOO}} --api-key {{API_KEY}}", "FOO": None},
           "fleet": {"start": {"argv": ["x", "{{VLLM_ARGS}}"]}},
           "experiments": {"T": {"commands": [{"argv": ["y"]}]}}}
    assert nr.holes_for(cfg, "T") == [{"where": "vars.VLLM_ARGS", "name": "FOO"}]
    v = dict(cfg["vars"], FOO="1", API_KEY="K")
    assert nr.expand_argv(["{{VLLM_ARGS}}"], v) == ["--a 1 --api-key K"]


def test_smoke_dry_run_lists_overrides(nr, tmp_path, monkeypatch):
    def _no(*a, **k):
        raise AssertionError("dry-run はコマンドを回さない")

    monkeypatch.setattr(nr.subprocess, "run", _no)
    out, data = tmp_path / "out", tmp_path / "data"
    rc = nr.run_night("E1", config_path=_DIR / "experiments.json", out_root=out, data_root=data, dry_run=True,
                      smoke=True)
    assert rc == 0
    d = _only(out)
    assert d.name.endswith("_E1_smoke_dryrun") and not data.exists()
    s = _assert_written(d)
    assert "--agents 500" in s and "--ticks 120" in s and "--agents 5000" not in s
    assert "試走(smoke: true)" in s and "AGENTS=500" in s and "(試走 --smoke)" in s
    assert "nvidia-smi --query-gpu=memory.total,memory.used" in s  # VRAM の段も並ぶ
    st = json.loads((d / "night_run.json").read_text(encoding="utf-8"))
    assert st["smoke"] is True and st["smoke_vars"] == {"AGENTS": 500, "TICKS": 120}
    assert "night5070-E1-smoke-" in s
    rc = nr.run_night("E1", config_path=_DIR / "experiments.json", out_root=tmp_path / "o2",
                      data_root=tmp_path / "d2", dry_run=True)
    s2 = _assert_written(_only(tmp_path / "o2"))
    assert rc == 0 and "--agents 5000" in s2 and "--ticks 1440" in s2 and "smoke: true" not in s2
    st2 = json.loads((_only(tmp_path / "o2") / "night_run.json").read_text(encoding="utf-8"))
    assert st2["smoke"] is False


def test_smoke_requires_definition(nr, tmp_path, capsys):
    cfg = _test_cfg("http://127.0.0.1:9", commands=[{"name": "run", "argv": _py("print('ok')")}])
    rc = nr.run_night("T1", config_path=_write_cfg(tmp_path, cfg), out_root=tmp_path / "out",
                      data_root=tmp_path / "data", smoke=True)
    assert rc == 2 and "smoke" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


#: 引数を JSON のファイルに書き、標準出力にも出す(鍵がログに写る形を作る)。
_REC = ("import json,sys,pathlib; p=pathlib.Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True);"
        " p.write_text(json.dumps(sys.argv[2:]), encoding='utf-8'); print(' '.join(sys.argv[2:]))")


def _key_from_start(dd: Path) -> str:
    """偽の艦隊の起動が書いた引数から鍵を取る(鍵のファイルはラン後に消える)。"""
    args = json.loads((dd / "start_argv.json").read_text(encoding="utf-8"))[-1].split()
    return args[args.index("--api-key") + 1]


#: 実験のコマンド: 渡った鍵の環境変数と、その時点の起動のログに鍵が残っていないかを書く。
_EXP_ENV = ("import json,os,sys,pathlib; k=os.environ.get('SHIBUYA_FLEET_API_KEY','');"
            " lg=pathlib.Path(sys.argv[2]); t=lg.read_text(encoding='utf-8') if lg.exists() else '';"
            " pathlib.Path(sys.argv[1]).write_text(json.dumps({'key': k, 'in_log': bool(k) and k in t}),"
            " encoding='utf-8')")


def _smoke_cfg(endpoint: str) -> dict:
    cfg = _test_cfg(endpoint, commands=[{"name": "run", "argv": _py(_REC) + [
        "{{DATA}}/run_argv.json", "--agents", "{{AGENTS}}", "--ticks", "{{TICKS}}"]}])
    cfg["vars"].update({"AGENTS": 5000, "TICKS": 1440,
                        "VLLM_ARGS": "--host 127.0.0.1 --api-key {{API_KEY}} --load-format safetensors"})
    cfg["fleet"]["start"]["argv"] = _py(_REC) + ["{{DATA}}/start_argv.json", "serve", "{{VLLM_ARGS}}"]
    cfg["experiments"]["T1"]["smoke"] = {"vars": {"AGENTS": 500, "TICKS": 120}}
    return cfg


def test_smoke_run_overrides_and_masks_api_key(nr, fake_fleet, tmp_path):
    rc, d, data = _run(nr, tmp_path, _smoke_cfg(fake_fleet), smoke=True)
    s = _assert_written(d)
    assert rc == 0, s
    dd = _only(data)
    assert d.name.endswith("_T1_smoke") and dd.name == d.name
    assert json.loads((dd / "run_argv.json").read_text(encoding="utf-8")) == ["--agents", "500", "--ticks", "120"]
    st = json.loads((d / "night_run.json").read_text(encoding="utf-8"))
    assert st["smoke"] is True and "試走(smoke: true)" in s
    assert all(c["ok"] for c in st["safety"]) and len(st["safety"]) == 9
    key = _key_from_start(dd)
    assert len(key) >= 32
    assert not (dd / "api_key").exists() and "API key のファイル: 消した(艦隊を落とした後)" in s
    # 艦隊(偽物)には鍵が届き、健全性の呼は 2 本とも Bearer を付けた
    assert len(_FakeFleet.auth) >= 2 and all(a == f"Bearer {key}" for a in _FakeFleet.auth)
    # 記録とログに鍵の値が無い(印に置き換える)
    files = list(d.iterdir()) + list((dd / "logs").iterdir()) + [d.parent / "_night_runs.log"]
    for f in files:
        assert key not in f.read_text(encoding="utf-8", errors="replace"), f.name
    assert "--api-key <API_KEY>" in (dd / "logs" / "fleet_start.stdout.log").read_text(encoding="utf-8")
    assert "<API_KEY>" in json.dumps(st, ensure_ascii=False)
    assert "API key: ランごとに作った(値は書かない)" in s


def test_full_run_keeps_default_agents_and_steps(nr, fake_fleet, tmp_path):
    rc, d, data = _run(nr, tmp_path, _smoke_cfg(fake_fleet))
    assert rc == 0 and not d.name.endswith("_smoke")
    run_argv = json.loads((_only(data) / "run_argv.json").read_text(encoding="utf-8"))
    assert run_argv == ["--agents", "5000", "--ticks", "1440"]
    assert json.loads((d / "night_run.json").read_text(encoding="utf-8"))["smoke"] is False


def test_api_keys_differ_per_run(nr, fake_fleet, tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    _run(nr, tmp_path / "a", _smoke_cfg(fake_fleet))
    _run(nr, tmp_path / "b", _smoke_cfg(fake_fleet))
    ka = _key_from_start(_only(tmp_path / "a" / "data"))
    kb = _key_from_start(_only(tmp_path / "b" / "data"))
    assert ka != kb


def test_experiment_env_gets_fleet_key_and_logs_are_scrubbed_early(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setenv("SHIBUYA_FLEET_API_KEY", "inherited-must-not-pass")
    cfg = _smoke_cfg(fake_fleet)
    cfg["experiments"]["T1"]["commands"] = [{"name": "run", "argv": _py(_EXP_ENV) + [
        "{{DATA}}/exp_env.json", "{{DATA}}/logs/fleet_start.stdout.log"]}]
    cfg["fleet"]["start"]["argv"] = _py(_REC + "; import os; print('START_ENV=' + os.environ.get("
                                        "'SHIBUYA_FLEET_API_KEY', ''))") + [
        "{{DATA}}/start_argv.json", "serve", "{{VLLM_ARGS}}"]
    rc, d, data = _run(nr, tmp_path, cfg)
    assert rc == 0, _assert_written(d)
    dd = _only(data)
    key = _key_from_start(dd)
    got = json.loads((dd / "exp_env.json").read_text(encoding="utf-8"))
    assert got == {"key": key, "in_log": False}  # 実験には鍵・その時点で起動のログは置き換え済み
    log = (dd / "logs" / "fleet_start.stdout.log").read_text(encoding="utf-8")
    assert "START_ENV=\n" in log.replace("\r\n", "\n")  # 艦隊の起動には鍵の環境変数を渡さない
    assert "inherited-must-not-pass" not in log


def test_keep_fleet_still_removes_key_file(nr, fake_fleet, tmp_path):
    rc, d, data = _run(nr, tmp_path, _smoke_cfg(fake_fleet), keep_fleet=True)
    s = _assert_written(d)
    assert rc == 0 and not (_only(data) / "api_key").exists() and "--keep-fleet で艦隊は残っている" in s


# ------------------------------------------------------------------ (h) 安全の規則の機械の検査

_GOOD_CMD = ('wsl.exe -d D -- bash -lc tmux new-session -d -s s "vllm serve m --port 8000 --host 127.0.0.1'
             ' --api-key K123 --load-format safetensors > /tmp/x 2>&1"')
_SAFETY_NAMES = {"rule1.endpoints_loopback", "rule1.vllm_host", "rule1.api_key", "rule1.wsl_nat",
                 "rule2.safetensors", "rule2.no_trust_remote_code", "rule2.no_config_file", "rule4.wslenv",
                 "rule12.no_shell_expansion"}


def _sc(nr, cmd=_GOOD_CMD, eps=("http://127.0.0.1:8000",), key: str = "K123", env=None, wsl=None,
        vllm_env=None) -> dict:
    return {c["name"]: c for c in nr.safety_checks(endpoints=list(eps), start_cmd=cmd, api_key=key,
                                                   env=env or {}, wslconfig_text=wsl, vllm_env=vllm_env)}


_ENV_CMD = _GOOD_CMD.replace("--api-key K123 ", "").replace('"vllm serve', '"VLLM_API_KEY=K123 CUDA_HOME=x vllm serve')


@pytest.mark.parametrize("cmd,vllm_env", [
    (_GOOD_CMD, None),
    (_ENV_CMD, "VLLM_API_KEY=K123 CUDA_HOME=x"),
    (_ENV_CMD.replace("vllm serve", "vllm serve --api-key K123"), "VLLM_API_KEY=K123 CUDA_HOME=x"),
])
def test_safety_api_key_by_env_or_arg(nr, cmd, vllm_env):
    c = _sc(nr, cmd=cmd, vllm_env=vllm_env)["rule1.api_key"]
    assert c["ok"] is True and "K123" not in c["detail"]


@pytest.mark.parametrize("cmd,vllm_env", [
    (_ENV_CMD, None),  # VLLM_ENV が無い=文字列のどこかにあっても数えない
    (_ENV_CMD, "CUDA_HOME=x VLLM_API_KEY=K123"),  # 先頭の語でない
    (_GOOD_CMD.replace("--api-key K123 ", "echo VLLM_API_KEY=K123; "), "CUDA_HOME=x"),
    (_ENV_CMD, "VLLM_API_KEY=OTHER"),  # VLLM_ENV の鍵が違う(起動のコマンドの語とも合わない)
    (_ENV_CMD.replace("vllm serve", "vllm serve --api-key ''"), "VLLM_API_KEY=K123 CUDA_HOME=x"),  # 空の --api-key
    (_GOOD_CMD.replace("--api-key K123", "--api-key K123 --api-key K123"), None),  # 2 回
    (_GOOD_CMD.replace("--api-key K123", "--api-key=''"), None),
    (_GOOD_CMD.replace("--api-key K123", "--api-key K123 --api-k X"), None),  # 略記
])
def test_safety_api_key_negative(nr, cmd, vllm_env):
    assert _sc(nr, cmd=cmd, vllm_env=vllm_env)["rule1.api_key"]["ok"] is False


@pytest.mark.parametrize("old,new,name", [
    ("--host 127.0.0.1", "--host 127.0.0.1 --host '0.0.0.0'", "rule1.vllm_host"),
    ("--host 127.0.0.1", "--host '0.0.0.0'", "rule1.vllm_host"),
    ("--host 127.0.0.1", "--host 127.0.0.1 --hos 0.0.0.0", "rule1.vllm_host"),
    ("--host 127.0.0.1", "--host 127.0.0.1 --ho=0.0.0.0", "rule1.vllm_host"),
    ("--load-format safetensors", "--load-format safetensors --load-format 'pt'", "rule2.safetensors"),
    ("--load-format safetensors", "--load-format safetensors --load pt", "rule2.safetensors"),
    ("--port 8000", "--port 8000 --config x.yaml", "rule2.no_config_file"),
    ("--port 8000", "--port 8000 --config=x.yaml", "rule2.no_config_file"),
    ("--port 8000", "--port 8000 --conf x.yaml", "rule2.no_config_file"),
    ("--port 8000", "--port 8000 --trust", "rule2.no_trust_remote_code"),
])
def test_safety_checks_quoted_abbrev_and_config(nr, old, new, name):
    cmd = _GOOD_CMD.replace(old, new)
    assert cmd != _GOOD_CMD
    r = _sc(nr, cmd=cmd)
    assert [k for k, c in r.items() if c["ok"] is False] == [name]


def test_safety_checks_read_argv_list_and_unsplittable(nr):
    argv = ["wsl.exe", "-d", "D", "--", "bash", "-lc",
            "vllm serve m --host 127.0.0.1 --api-key K123 --load-format safetensors"]
    assert all(c["ok"] for c in _sc(nr, cmd=argv).values())
    toks, bad = nr.split_command(["bash", "-lc", "tmux new \"vllm --host '0.0.0.0' --api-key ''\""])
    assert "0.0.0.0" in toks and "" in toks and bad == []
    broken = _GOOD_CMD.replace("--port 8000", "--port 8000 'unterminated")  # 切れない文字列は不合格
    r = _sc(nr, cmd=broken)
    assert r["rule1.vllm_host"]["ok"] is False and r["rule2.safetensors"]["ok"] is False


def test_safety_checks_pass_on_good_config(nr):
    r = _sc(nr)
    assert set(r) == _SAFETY_NAMES and all(c["ok"] for c in r.values())
    assert all("K123" not in c["detail"] for c in r.values())  # 鍵の値は書かない
    assert {c["rule"] for c in r.values()} == {"1", "2", "4", "1・2"}


@pytest.mark.parametrize("old,new,name", [
    ("--host 127.0.0.1", "--host 0.0.0.0", "rule1.vllm_host"),
    ("--host 127.0.0.1 ", "", "rule1.vllm_host"),
    ("--host 127.0.0.1", "--host 127.0.0.1 --host 0.0.0.0", "rule1.vllm_host"),
    ("--host 127.0.0.1", "--host=localhost", "rule1.vllm_host"),
    ("--api-key K123 ", "", "rule1.api_key"),
    ("--api-key K123 ", "XVLLM_API_KEY=K123 ", "rule1.api_key"),
    ("--api-key K123 ", "VLLM_API_KEY=K1234 ", "rule1.api_key"),
    ("--api-key K123", "--api-key OTHER", "rule1.api_key"),
    ("--api-key K123", "--api-key K1234", "rule1.api_key"),
    ("--load-format safetensors", "--load-format pt", "rule2.safetensors"),
    ("--load-format safetensors ", "", "rule2.safetensors"),
    ("--port 8000", "--port 8000 --trust-remote-code", "rule2.no_trust_remote_code"),
    ("--port 8000", "--port 8000 --hf-overrides trust_remote_code", "rule2.no_trust_remote_code"),
])
def test_safety_checks_fail_each(nr, old, new, name):
    cmd = _GOOD_CMD.replace(old, new)
    assert cmd != _GOOD_CMD
    r = _sc(nr, cmd=cmd)
    assert [k for k, c in r.items() if not c["ok"]] == [name]


@pytest.mark.parametrize("eps", [("http://localhost:8000",), ("http://0.0.0.0:8000",),
                                 ("http://127.0.0.1:8000", "http://192.168.1.5:8000"), ()])
def test_safety_checks_endpoints_must_be_loopback(nr, eps):
    assert _sc(nr, eps=eps)["rule1.endpoints_loopback"]["ok"] is False


@pytest.mark.parametrize("wslenv,ok", [
    ("WT_SESSION:USERPROFILE/p", True), ("", True), ("KEYBOARD_LAYOUT:MONKEY_X", True),
    ("HF_TOKEN/u", False), ("GITHUB_TOKEN", False), ("MY_SECRET/p", False), ("AWS_SECRET_ACCESS_KEY", False),
    ("KEY", False), ("DB_PASSWORD", False), ("ODPTAPIKEY", False), ("CREDENTIALS", False), ("GCP_CREDENTIAL/p", False),
    ("MYPASSWD", False),
    ("FOO/u:ODPT_API_KEY/p", False), ("ODPT_CHALLENGE_API_KEY", False), ("API_KEY/u", False),
    ("odpt_api_key", False), ("SHIBUYA_FLEET_API_KEY/u", False),
])
def test_safety_checks_wslenv_names_only(nr, wslenv, ok):
    env = {"WSLENV": wslenv, "ODPT_API_KEY": "value-must-not-appear"}
    c = _sc(nr, env=env)["rule4.wslenv"]
    assert c["ok"] is ok
    assert "value-must-not-appear" not in c["detail"]


@pytest.mark.parametrize("text,ok", [
    (None, True), ("[wsl2]\nmemory=20GB\n", True), ("[wsl2]\n# networkingMode=mirrored\n", True),
    ("[wsl2]\nnetworkingMode = NAT\n", True), ("[wsl2]\nnetworkingMode=mirrored\n", False),
    ("[wsl2]\nnetworkingmode=Mirrored ; 注\n", False),
    ("[wsl2]\nnetworkingMode=bridged\n", False), ("[wsl2]\nnetworkingMode=nat\n", True),
])
def test_safety_checks_wsl_nat(nr, text, ok):
    assert _sc(nr, wsl=text)["rule1.wsl_nat"]["ok"] is ok


def test_safety_violation_stops_before_fleet(nr, fake_fleet, tmp_path):
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("print('ok')")}])
    cfg["fleet"]["start"]["argv"] = _py("pass") + ["--host", "0.0.0.0", "--api-key", "{{API_KEY}}",
                                                   "--load-format", "safetensors"]
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 5, s
    assert "安全の規則の検査" in s and "**不合格**" in s and "rule1.vllm_host" in s and "**失敗**" in s
    assert _stop_count(data) == 0 and _FakeFleet.hits == []  # 検査は WSL を起動しない=前の艦隊を落とす段もしない
    assert not (_only(data) / "api_key").exists()
    names = [x["name"] for x in json.loads((d / "night_run.json").read_text(encoding="utf-8"))["steps"]]
    assert "艦隊を立てる" not in names and "実験: run" not in names
    assert (d / "NIGHT_DONE").read_text(encoding="utf-8").strip() == "失敗"


def test_wslenv_key_name_stops_without_reading_value(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setenv("ODPT_API_KEY", "value-must-not-appear")
    monkeypatch.setenv("WSLENV", "ODPT_API_KEY/u")
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _py("print('ok')")}])
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 5 and "rule4.wslenv" in s and "ODPT_API_KEY" in s
    assert _stop_count(data) == 0  # 検査で止まれば前の艦隊を落とす段もしない
    for f in d.iterdir():
        assert "value-must-not-appear" not in f.read_text(encoding="utf-8")


def test_trust_remote_code_in_vllm_args_stops(nr, fake_fleet, tmp_path):
    cfg = _smoke_cfg(fake_fleet)
    cfg["vars"]["VLLM_ARGS"] += " --trust-remote-code"
    rc, d, data = _run(nr, tmp_path, cfg)
    assert rc == 5 and "rule2.no_trust_remote_code" in _assert_written(d)
    assert not (_only(data) / "start_argv.json").exists()


def test_dry_run_shows_safety_failures_without_stopping(nr, tmp_path, monkeypatch):
    def _no(*a, **k):
        raise AssertionError("dry-run はコマンドを回さない")

    monkeypatch.setattr(nr.subprocess, "run", _no)
    cfg = _smoke_cfg("http://localhost:9")
    rc = nr.run_night("T1", config_path=_write_cfg(tmp_path, cfg), out_root=tmp_path / "out",
                      data_root=tmp_path / "data", dry_run=True)
    s = _assert_written(_only(tmp_path / "out"))
    assert rc == 0 and "rule1.endpoints_loopback" in s and "**不合格**" in s and "dry-run なので続ける" in s
    assert "--api-key <API_KEY>" in s  # dry-run の鍵は印のまま


# ------------------------------------------------------------------ (i) 空き VRAM と起動の値の調整


def test_parse_vram(nr):
    assert nr.parse_vram("12227, 2081\n") == {"total_mib": 12227, "used_mib": 2081, "free_mib": 10146}
    assert nr.parse_vram("12227, 2081\n12227, 9000\n")["used_mib"] == 2081  # 1 枚目
    assert nr.parse_vram("") is None and nr.parse_vram("[N/A], [N/A]") is None


def test_query_vram_reads_nvidia_smi_or_unmeasured(nr, quiet_machine, monkeypatch):
    real = quiet_machine["query_vram"]
    seen: dict = {}

    def fake_run(argv, **k):
        seen["argv"] = list(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="12227, 2081\n", stderr="")

    monkeypatch.setattr(nr.subprocess, "run", fake_run)
    assert real() == {"total_mib": 12227, "used_mib": 2081, "free_mib": 10146}
    assert seen["argv"] == ["nvidia-smi", "--query-gpu=memory.total,memory.used", "--format=csv,noheader,nounits"]

    def missing(argv, **k):
        raise FileNotFoundError("nvidia-smi が無い")

    monkeypatch.setattr(nr.subprocess, "run", missing)
    assert real() is None
    monkeypatch.setattr(nr.subprocess, "run", lambda argv, **k: subprocess.CompletedProcess(argv, 9, "", "x"))
    assert real() is None


def _vram(free_gb: float, total_mib: int = 12227) -> dict:
    free = int(round(free_gb * 1024))
    return {"total_mib": total_mib, "used_mib": total_mib - free, "free_mib": free}


_PLAN = {"util_setting": 0.78, "seqs_setting": 32, "seqs_steps": [32, 16, 8], "model_gb": 5.68, "plan_gb": 9.0}


@pytest.mark.parametrize("free_gb,seqs,util", [(10.0, 32, 0.78), (8.5, 16, 0.66), (8.1, 8, 0.63)])
def test_plan_vram_three_steps(nr, free_gb, seqs, util):
    p = nr.plan_vram(_vram(free_gb), **_PLAN)
    assert p["enough"] is True and p["measured"] is True
    assert p["seqs_used"] == seqs and p["util_used"] == util
    total_gb = 12227 / 1024
    assert p["util_used"] <= min(0.78, (p["free_mib"] / 1024 - 0.5) / total_gb)  # 空きから 0.5 GB 残す


def test_plan_vram_shortage_and_unmeasured(nr):
    p = nr.plan_vram(_vram(7.5), **_PLAN)  # 7.5 < 5.68 + 2
    assert p["enough"] is False and "足りない" in p["reason"] and p["util_used"] is None
    q = nr.plan_vram(None, **_PLAN)
    assert q["measured"] is False and q["enough"] is None and q["util_used"] == 0.78 and q["seqs_used"] == 32


def test_set_and_get_flag(nr):
    assert nr.set_flag("--a 1", "--max-num-seqs", 16) == "--a 1 --max-num-seqs 16"
    assert nr.set_flag("--max-num-seqs=32 --x", "--max-num-seqs", 8) == "--max-num-seqs=8 --x"
    assert nr.set_flag("", "--gpu-memory-utilization", "0.7") == "--gpu-memory-utilization 0.7"
    assert nr.get_flag("--gpu-memory-utilization 0.78 --y", "--gpu-memory-utilization") == "0.78"
    assert nr.get_flag("--y", "--max-num-seqs") is None


def _vram_cfg(endpoint: str, vllm_args: str) -> dict:
    cfg = _test_cfg(endpoint, commands=[{"name": "run", "argv": _py("print('ok')")}])
    cfg["vars"].update({"VLLM_ARGS": vllm_args, "MODEL_GB": 5.68, "VRAM_PLAN_GB": 9.0})
    cfg["fleet"]["start"]["argv"] = _py(_REC) + ["{{DATA}}/start_argv.json", "{{VLLM_ARGS}}"]
    cfg["fleet"]["vram"] = {"model_gb": "{{MODEL_GB}}", "plan_gb": "{{VRAM_PLAN_GB}}", "gpu_memory_utilization": 0.78,
                            "max_num_seqs": 32, "max_num_seqs_steps": [32, 16, 8], "margin_gb": 0.5,
                            "headroom_gb": 2.0}
    return cfg


_SAFE_VLLM_ARGS = "--host 127.0.0.1 --api-key {{API_KEY}} --load-format safetensors"


def test_vram_adjusts_start_args_and_metrics(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "query_vram", lambda *a, **k: _vram(8.5))
    cfg = _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS + " --gpu-memory-utilization 0.78 --max-num-seqs 32")
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 0, s
    a = json.loads((_only(data) / "start_argv.json").read_text(encoding="utf-8"))[-1]
    assert "--gpu-memory-utilization 0.66" in a and "--max-num-seqs 16" in a and "0.78" not in a
    m = {f["key"]: f for f in json.loads((d / "metrics.json").read_text(encoding="utf-8"))["fields"]}
    assert m["vram.free_before"]["value"]["free_gb"] == 8.5 and m["vram.free_before"]["label"] == "空き VRAM(起動前)"
    assert m["vram.gpu_memory_utilization"]["value"] == 0.66
    assert m["vram.gpu_memory_utilization"]["label"] == "gpu-memory-utilization(使った値)"
    assert m["vram.max_num_seqs"]["value"] == 16 and m["vram.max_num_seqs"]["label"] == "max-num-seqs(使った値)"
    assert "max-num-seqs 16(設定 32)" in s and "gpu-memory-utilization 0.66(設定 0.78)" in s
    assert "| VRAM | 空き VRAM(起動前) |" in (d / "metrics.md").read_text(encoding="utf-8")


def test_vram_flags_added_when_absent(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "query_vram", lambda *a, **k: _vram(10.0))
    rc, d, data = _run(nr, tmp_path, _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS))
    a = json.loads((_only(data) / "start_argv.json").read_text(encoding="utf-8"))[-1]
    assert rc == 0 and a.endswith("--gpu-memory-utilization 0.78 --max-num-seqs 32")


def test_vram_shortage_stops_before_fleet(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "query_vram", lambda *a, **k: _vram(7.0))
    rc, d, data = _run(nr, tmp_path, _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS))
    s = _assert_written(d)
    assert rc == 6 and "**足りない**" in s and "艦隊を立てていない" in s
    assert _stop_count(data) == 1 and _FakeFleet.hits == []  # 前の艦隊を落とす段だけ
    assert not (_only(data) / "start_argv.json").exists()
    m = {f["key"]: f for f in json.loads((d / "metrics.json").read_text(encoding="utf-8"))["fields"]}
    assert m["vram.free_before"]["value"]["free_gb"] == 7.0 and m["vram.max_num_seqs"]["status"] == "未計測"


def test_vram_unmeasured_keeps_settings(nr, fake_fleet, tmp_path):
    rc, d, data = _run(nr, tmp_path, _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS + " --max-num-seqs 24"))
    s = _assert_written(d)
    a = json.loads((_only(data) / "start_argv.json").read_text(encoding="utf-8"))[-1]
    assert rc == 0 and "--max-num-seqs 24" in a and "--gpu-memory-utilization 0.78" in a
    m = {f["key"]: f for f in json.loads((d / "metrics.json").read_text(encoding="utf-8"))["fields"]}
    assert m["vram.free_before"]["value"] == "未計測" and m["vram.max_num_seqs"]["value"] == 24
    assert "空き 未計測" in s


def test_vram_bad_number_is_config_error(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "query_vram", lambda *a, **k: _vram(10.0))
    cfg = _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS)
    cfg["vars"]["MODEL_GB"] = "六"
    rc, d, data = _run(nr, tmp_path, cfg)
    assert rc == 3 and _stop_count(data) == 1


# ------------------------------------------------------------------ (j) タスクの主体(安全の規則 5)


def test_xml_principal_is_user_not_system(rt):
    xml = rt.build_xml(experiment="E1", start=dt.datetime(2026, 11, 2, 1, 0), python="PY", user_id="PC\\someone")
    pr = _xml_root(xml).find("t:Principals/t:Principal", _NS)
    assert pr.find("t:UserId", _NS).text == "PC\\someone"
    assert pr.find("t:LogonType", _NS).text == "InteractiveToken"
    assert pr.find("t:RunLevel", _NS).text == "LeastPrivilege"
    assert pr.find("t:GroupId", _NS) is None
    assert rt.check_principal_xml(xml) == {"UserId": "PC\\someone", "LogonType": "InteractiveToken",
                                           "RunLevel": "LeastPrivilege"}


@pytest.mark.parametrize("uid", ["SYSTEM", "NT AUTHORITY\\SYSTEM", "nt authority\\system", "S-1-5-18",
                                 "LocalSystem", "NT AUTHORITY\\LOCAL SERVICE", "NT AUTHORITY\\NETWORK SERVICE",
                                 "S-1-5-19", "S-1-5-20", "WORKGROUP\\PC$", ""])
def test_xml_refuses_non_user_principal(rt, uid):
    with pytest.raises(ValueError):
        rt.build_xml(experiment="E1", start=dt.datetime(2026, 11, 2, 1, 0), python="PY", user_id=uid)


@pytest.mark.parametrize("old,new", [
    ("<LogonType>InteractiveToken</LogonType>", "<LogonType>ServiceAccount</LogonType>"),
    ("<LogonType>InteractiveToken</LogonType>", "<LogonType>S4U</LogonType>"),
    ("<RunLevel>LeastPrivilege</RunLevel>", "<RunLevel>HighestAvailable</RunLevel>"),
    ("<UserId>PC\\someone</UserId>", "<UserId>S-1-5-18</UserId>"),
    ("<UserId>PC\\someone</UserId>", "<GroupId>S-1-5-32-545</GroupId>"),
    ("<UserId>PC\\someone</UserId>", ""),
])
def test_check_principal_xml_rejects_tampered(rt, old, new):
    xml = rt.build_xml(experiment="E1", start=dt.datetime(2026, 11, 2, 1, 0), python="PY", user_id="PC\\someone")
    bad = xml.replace(old, new)
    assert bad != xml
    with pytest.raises(ValueError):
        rt.check_principal_xml(bad)


def test_print_only_masks_user_id_and_refuses_system(rt, capsys, monkeypatch):
    monkeypatch.setattr(rt, "current_user_id", lambda: "PC\\someone")
    assert rt.main(["--at", "01:00", "--experiment", "E1", "--wake", "--print-only"]) == 0
    outp = capsys.readouterr().out
    xml = outp[: outp.index("</Task>") + len("</Task>")]
    assert "someone" not in outp
    assert _xml_root(xml).find("t:Principals/t:Principal/t:UserId", _NS).text == "<USER>"
    monkeypatch.setattr(rt, "current_user_id", lambda: "NT AUTHORITY\\SYSTEM")
    assert rt.main(["--at", "01:00", "--experiment", "E1", "--print-only"]) == 2
    assert "安全の規則 5" in capsys.readouterr().err


def test_current_user_id_is_user(rt, monkeypatch):
    monkeypatch.setenv("USERNAME", "someone")
    monkeypatch.setenv("USERDOMAIN", "PC")
    assert rt.current_user_id() == "PC\\someone"
    monkeypatch.delenv("USERDOMAIN")
    assert rt.current_user_id() == "someone"


# ------------------------------------------------------------------ (k) ファイアウォール・Defender・ネットワークに触らない


_FORBIDDEN_WORDS = ("netsh", "new-netfirewallrule", "set-netfirewall", "set-mppreference", "add-mppreference",
                    "networkingmode=mirrored", "networkingmode mirrored")


@pytest.mark.parametrize("name", ["night_run.py", "register_task.py"])
def test_no_firewall_defender_or_network_setting_calls(name):
    text = (_DIR / name).read_text(encoding="utf-8").lower()
    for word in _FORBIDDEN_WORDS:
        assert word not in text, (name, word)


def test_no_firewall_calls_in_experiment_commands(real_cfg):
    argvs = [real_cfg["fleet"][k]["argv"] for k in ("start", "stop", "collect_log")]
    argvs += [c["argv"] for e in real_cfg["experiments"].values() for c in e["commands"]]
    text = json.dumps(argvs, ensure_ascii=False).lower()
    assert "wsl.exe" in text  # 実際に回るコマンドを見ている
    for word in _FORBIDDEN_WORDS + ("powershell", "icacls", "schtasks"):
        assert word not in text, word


def test_readme_lists_safety_rules_and_checks(nr):
    text = (_DIR / "README.md").read_text(encoding="utf-8")
    assert "## 安全の規則" in text and "## E1 の開始の合図" in text
    for n in _SAFETY_NAMES | {"rule5.task_principal", "rule5.task_workdir", "rule5.no_firewall_calls"}:
        assert n in text, n
    assert "register_task.py --at HH:MM --experiment E1 --wake" in text


# ------------------------------------------------------------------ (l) 検収 11-01 の直し(H1・M1・M3・L1・L2・L4・L6・L7・L8)

#: 前の夜の艦隊の印を消す stop(落とすたびに 1 行足し、印のファイルを消す)。
_STOP_PREV = ("import pathlib,sys; p=pathlib.Path(sys.argv[1]); p.parent.mkdir(parents=True, exist_ok=True);"
              " f=p.read_text(encoding='utf-8') if p.exists() else ''; p.write_text(f+'stop\\n', encoding='utf-8');"
              " m=pathlib.Path(sys.argv[3]); m.unlink() if m.exists() else None; sys.exit(int(sys.argv[2]))")


def _names(d: Path) -> list[str]:
    return [x["name"] for x in json.loads((d / "night_run.json").read_text(encoding="utf-8"))["steps"]]


def test_prestop_runs_before_safety_and_vram_and_frees_last_night(nr, fake_fleet, tmp_path, monkeypatch):
    marker = tmp_path / "last_night_fleet.txt"
    marker.write_text("前の夜の艦隊が VRAM を持っている", encoding="utf-8")
    seen: list[bool] = []

    def vram(*a, **k):
        seen.append(marker.exists())
        return _vram(4.0) if marker.exists() else _vram(10.0)  # 前の夜の艦隊が居れば足りない

    monkeypatch.setattr(nr, "query_vram", vram)
    cfg = _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS)
    cfg["fleet"]["stop"]["argv"] = _py(_STOP_PREV) + ["{{DATA}}/stop_calls.txt", "0", str(marker)]
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 0, s
    names = _names(d)
    i_pre, i_safe, i_vram = (names.index("前の艦隊を落とす(起動の前・失敗は無視)"), names.index("安全の規則の検査"),
                             names.index("空き VRAM の確認と起動の値の調整"))
    i_re = names.index("安全の規則の再検査(VRAM の調整の後)")
    assert i_safe < i_pre < i_vram < i_re < names.index("艦隊を立てる")
    assert seen and not any(seen)  # VRAM は落とした後に測った(落ち着くまで 2 回以上読む)
    assert "前の艦隊を落とす(VRAM を測る前): 落とした" in s


def test_prestop_failure_still_measures_vram(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "query_vram", lambda *a, **k: _vram(10.0))
    cfg = _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS)
    cfg["fleet"]["stop"]["argv"] = _py(_STOP_CODE) + ["{{DATA}}/stop_calls.txt", "1"]
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 4  # 最後の落とす段も失敗する(偽の stop はいつも 1)
    st = json.loads((d / "night_run.json").read_text(encoding="utf-8"))
    vr = next(x for x in st["steps"] if x["name"] == "空き VRAM の確認と起動の値の調整")
    assert vr["status"] == "ok" and "前の艦隊を落とす(VRAM を測る前): 無視(終了コード 1)" in s


def _tape_cmd(rows: dict | None) -> list[str]:
    """テープ(calls.parquet)を書く実験のコマンド。rows=None ならテープを書かない。"""
    if rows is None:
        return _py("print('no tape')")
    code = ("import json,sys,pathlib; import pyarrow as pa, pyarrow.parquet as pq; t=pathlib.Path(sys.argv[1]);"
            " t.mkdir(parents=True, exist_ok=True); r=json.loads(sys.argv[2]);"
            " pq.write_table(pa.table(r), t / 'calls.parquet')")
    return _py(code) + ["{{DATA}}/tape", json.dumps(rows)]


@pytest.mark.parametrize("rows,rc_want,word", [
    ({"agent_id": [1, 2], "deferred": [1, 0], "tokens_out": [0, 0], "deferred_reason": ["error_other", ""]},
     1, "応答 0(401 の疑い)"),
    ({"agent_id": [1, 2], "deferred": [1, 0], "tokens_out": [0, 7], "deferred_reason": ["error_other", ""]},
     0, "応答あり(0 でない)"),
    (None, 1, "応答数 未計測"),
])
def test_require_answers_gate(nr, fake_fleet, tmp_path, rows, rc_want, word):
    pytest.importorskip("pyarrow")
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _tape_cmd(rows)}])
    cfg["experiments"]["T1"]["require_answers"] = True
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == rc_want, s
    assert word in s and "応答の確認(テープの応答数 > 0)" in _names(d)
    if rc_want:
        assert "**失敗**" in s and (d / "NIGHT_DONE").read_text(encoding="utf-8").strip() == "失敗"
    assert "7" not in s.split("応答の確認")[1].split("\n")[0]  # 数は出さない(0 かどうかだけ)


def test_real_config_e1_requires_answers(real_cfg):
    assert real_cfg["experiments"]["E1"]["require_answers"] is True
    assert not any(e.get("require_answers") for k, e in real_cfg["experiments"].items() if k != "E1")


def test_fleet_commands_get_no_wslenv(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setenv("WSLENV", "FOO/u:USERPROFILE/p")  # 鍵らしい名は無い=合格・ただし艦隊には渡さない
    cfg = _smoke_cfg(fake_fleet)
    cfg["fleet"]["start"]["argv"] = _py(_REC + "; import os; print('WSLENV=' + os.environ.get('WSLENV', ''))") + [
        "{{DATA}}/start_argv.json", "serve", "{{VLLM_ARGS}}"]
    rc, d, data = _run(nr, tmp_path, cfg)
    assert rc == 0, _assert_written(d)
    log = (_only(data) / "logs" / "fleet_start.stdout.log").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert "WSLENV=\n" in log


@pytest.mark.parametrize("name", ["HF_TOKEN", "GITHUB_TOKEN", "MY_SECRET"])
def test_wslenv_secret_like_name_stops(nr, fake_fleet, tmp_path, monkeypatch, name):
    monkeypatch.setenv("WSLENV", f"FOO/u:{name}/u")
    rc, d, data = _run(nr, tmp_path, _smoke_cfg(fake_fleet))
    s = _assert_written(d)
    assert rc == 5 and name in s and not (_only(data) / "start_argv.json").exists()


def test_vllm_args_list_stays_list(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "query_vram", lambda *a, **k: _vram(8.5))
    cfg = _vram_cfg(fake_fleet, "")
    cfg["vars"]["VLLM_ARGS"] = ["--host", "127.0.0.1", "--api-key", "{{API_KEY}}", "--load-format", "safetensors",
                                "--max-num-seqs", "32"]
    cfg["fleet"]["start"]["argv"] = _py(_REC) + ["{{DATA}}/start_argv.json", "serve", "{{VLLM_ARGS}}"]
    rc, d, data = _run(nr, tmp_path, cfg)
    assert rc == 0, _assert_written(d)
    a = json.loads((_only(data) / "start_argv.json").read_text(encoding="utf-8"))
    assert a[0] == "serve" and a[1:3] == ["--host", "127.0.0.1"] and a[4] != "{{API_KEY}}"
    assert a[a.index("--max-num-seqs") + 1] == "16" and a[-2:] == ["--gpu-memory-utilization", "0.66"]


def test_dry_run_with_holes_lists_undecided_rules(nr, tmp_path, monkeypatch):
    def _no(*a, **k):
        raise AssertionError("dry-run はコマンドを回さない")

    monkeypatch.setattr(nr.subprocess, "run", _no)
    monkeypatch.setenv("WSLENV", "HF_TOKEN/u")
    rc = nr.run_night("E1", config_path=_DIR / "experiments.json", out_root=tmp_path / "out",
                      data_root=tmp_path / "data", dry_run=True)
    s = _assert_written(_only(tmp_path / "out"))
    assert rc == 0
    st = json.loads((_only(tmp_path / "out") / "night_run.json").read_text(encoding="utf-8"))
    by = {c["name"]: c for c in st["safety"]}
    assert by["rule1.endpoints_loopback"]["ok"] is True and by["rule1.wsl_nat"]["ok"] is True
    assert by["rule4.wslenv"]["ok"] is False  # 穴に依らない検査は dry-run でも判定する
    assert set(st["safety_undecided"]) == set(nr.START_CHECKS)
    assert "未判定の規則" in s and "| 未判定 |" in s and "rule1.vllm_host" in s


def test_exit_codes_are_distinct(nr):
    assert (nr.RC_CONFIG_ERROR, nr.RC_CONFIG_UNREADABLE, nr.RC_SAFETY, nr.RC_VRAM) == (2, 3, 5, 6)


def test_unknown_experiment_is_config_error(nr, tmp_path):
    cfg = _test_cfg("http://127.0.0.1:9", commands=[{"name": "run", "argv": _py("print('ok')")}])
    assert nr.run_night("NOPE", config_path=_write_cfg(tmp_path, cfg), out_root=tmp_path / "o",
                        data_root=tmp_path / "d") == 2


def test_key_file_removal_error_still_writes_records(nr, fake_fleet, tmp_path, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("消す処理の想定外")

    monkeypatch.setattr(nr, "_remove_api_key_file", boom)
    rc, d, data = _run(nr, tmp_path, _smoke_cfg(fake_fleet))
    s = _assert_written(d)
    assert rc == 0 and "消せなかった(RuntimeError)" in s


def test_icacls_restricts_key_file(nr, quiet_machine, monkeypatch, tmp_path):
    real = quiet_machine["restrict_key_acl"]
    seen: dict = {}

    def fake_run(argv, **k):
        seen["argv"] = list(argv)
        return subprocess.CompletedProcess(argv, seen.get("rc", 0), b"", b"")

    monkeypatch.setattr(nr.subprocess, "run", fake_run)
    monkeypatch.setattr(nr.sys, "platform", "win32")
    monkeypatch.setenv("USERNAME", "someone")
    f = tmp_path / "api_key"
    assert real(f) == "icacls で本人だけ(継承を外した)"
    assert seen["argv"] == ["icacls", str(f), "/inheritance:r", "/grant:r", "someone:F"]
    seen["rc"] = 5
    assert real(f) == "icacls に失敗(終了コード 5)・置き場の継承の権限のまま"

    def missing(argv, **k):
        raise FileNotFoundError("icacls")

    monkeypatch.setattr(nr.subprocess, "run", missing)
    assert "icacls に失敗(FileNotFoundError)" in real(f)
    monkeypatch.delenv("USERNAME")
    assert "USERNAME が無い" in real(f)


def test_acl_note_in_summary_without_user_name(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "restrict_key_acl", lambda p: "icacls に失敗(終了コード 5)・置き場の継承の権限のまま")
    rc, d, data = _run(nr, tmp_path, _smoke_cfg(fake_fleet))
    s = _assert_written(d)
    assert rc == 0 and "- 鍵のファイルの ACL: icacls に失敗(終了コード 5)" in s


def test_register_refuses_worktree(rt, capsys, monkeypatch, tmp_path):
    def _no(*a, **k):
        raise AssertionError("作業木からは登録しない")

    monkeypatch.setattr(rt.subprocess, "run", _no)
    monkeypatch.setattr(rt, "current_user_id", lambda: "PC\\someone")
    monkeypatch.setattr(rt, "REPO", tmp_path / ("wt_" + "x") / "repo")
    assert rt.main(["--at", "01:00", "--experiment", "E1"]) == 2
    assert "作業木から登録しようとした" in capsys.readouterr().err
    assert rt.main(["--at", "01:00", "--experiment", "E1", "--print-only"]) == 0  # 見るだけはよい
    assert "この道筋からは登録しない" in capsys.readouterr().err
    gitwt = tmp_path / "plain"
    gitwt.mkdir()
    (gitwt / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")
    assert rt.worktree_reason(gitwt) and rt.worktree_reason(tmp_path) == ""


# ------------------------------------------------------------------ (m) 再検収 11-01 の直し(N1〜N3・L-a〜L-e)


def _seq_vram(used_list: list[int], total: int = 12227):
    """読むたびに次の使用量を返す偽の nvidia-smi(最後の値はそのまま続く)。"""
    seq = list(used_list)
    calls: list[int] = []

    def q(*a, **k):
        u = seq.pop(0) if len(seq) > 1 else seq[0]
        calls.append(u)
        return {"total_mib": total, "used_mib": u, "free_mib": total - u}

    return q, calls


def test_wait_vram_settle_until_two_equal_reads(nr):
    q, calls = _seq_vram([9000, 6000, 3000, 2400, 2400, 2000])
    t = {"now": 0.0}

    def sleep(sec):
        t["now"] += sec

    v, info = nr.wait_vram_settle(q, poll_s=2.0, limit_s=60.0, sleep=sleep, clock=lambda: t["now"])
    assert calls == [9000, 6000, 3000, 2400, 2400]  # 連続 2 回同じになったら止める
    assert v["used_mib"] == 2400 and info["settled"] is True and info["reads"] == 5
    assert info["used_before_mib"] == 9000 and info["used_after_mib"] == 2400 and info["waited_s"] == 8.0


def test_wait_vram_settle_gives_up_after_limit(nr):
    n = {"i": 0}

    def q(*a, **k):
        n["i"] += 1
        return {"total_mib": 12227, "used_mib": 9000 - n["i"], "free_mib": 3227 + n["i"]}

    t = {"now": 0.0}
    v, info = nr.wait_vram_settle(q, poll_s=2.0, limit_s=60.0, sleep=lambda s: t.__setitem__("now", t["now"] + s),
                                  clock=lambda: t["now"])
    assert info["settled"] is False and info["waited_s"] == 60.0 and "60 秒で打ち切った" in info["note"]
    v, info = nr.wait_vram_settle(lambda: None)
    assert v is None and info["reads"] == 0 and "読めない" in info["note"]


def test_vram_waits_for_release_after_prestop(nr, fake_fleet, tmp_path, monkeypatch):
    # 前の夜の艦隊が返していく途中=使用量が減っていく。落ち着いてから測るので rc 6 にならない
    q, calls = _seq_vram([11000, 8000, 4000, 2383, 2383])
    monkeypatch.setattr(nr, "query_vram", q)
    rc, d, data = _run(nr, tmp_path, _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS))
    s = _assert_written(d)
    assert rc == 0, s
    assert calls[:5] == [11000, 8000, 4000, 2383, 2383]
    assert "VRAM の待ち(前の艦隊を落とした後):" in s and "使用 11000 → 2383 MiB・5 回読んだ・落ち着いた" in s
    st = json.loads((d / "night_run.json").read_text(encoding="utf-8"))
    assert st["vram"]["used_mib"] == 2383 and st["vram_wait"]["settled"] is True


def test_vram_remeasures_once_before_shortage(nr, fake_fleet, tmp_path, monkeypatch):
    # 落ち着いた値が足りなくても、1 回測り直して足りれば進む
    q, calls = _seq_vram([11000, 11000, 2383])
    monkeypatch.setattr(nr, "query_vram", q)
    rc, d, data = _run(nr, tmp_path, _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS))
    s = _assert_written(d)
    assert rc == 0, s
    assert len(calls) == 3 and "VRAM の測り直し: 1 回目: 足りない" in s
    # 測り直しても足りなければ rc 6
    q2, calls2 = _seq_vram([11000])
    monkeypatch.setattr(nr, "query_vram", q2)
    (tmp_path / "b").mkdir()
    rc, d, data = _run(nr, tmp_path / "b", _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS))
    assert rc == 6 and len(calls2) == 3 and "VRAM の測り直し" in _assert_written(d)


@pytest.mark.parametrize("extra", ["$EXTRA", "$(cat x)", "`cat x`", "${HOST}", "$'--host' 0.0.0.0", "{a,b}"])
def test_safety_rejects_shell_expansion(nr, extra):
    cmd = _GOOD_CMD.replace("--port 8000", "--port 8000 " + extra)
    r = _sc(nr, cmd=cmd)
    assert r["rule12.no_shell_expansion"]["ok"] is False


def test_safety_shell_expansion_ok_on_plain_command(nr):
    assert _sc(nr)["rule12.no_shell_expansion"]["ok"] is True
    assert _sc(nr, cmd=_ENV_CMD, vllm_env="VLLM_API_KEY=K123 CUDA_HOME=x")["rule12.no_shell_expansion"]["ok"] is True


@pytest.mark.parametrize("vllm_env", ["VLLM_API_KEY=K123 VLLM_API_KEY=", "VLLM_API_KEY=K123 CUDA_HOME=x VLLM_API_KEY=K123"])
def test_safety_env_key_twice_fails(nr, vllm_env):
    cmd = _ENV_CMD.replace("CUDA_HOME=x", vllm_env.split(" ", 1)[1])
    c = _sc(nr, cmd=cmd, vllm_env=vllm_env)["rule1.api_key"]
    assert c["ok"] is False and "2 回" in c["detail"]
    # 引数の形の鍵があっても、VLLM_ENV の 2 回は不合格
    c = _sc(nr, cmd=_GOOD_CMD, vllm_env=vllm_env)["rule1.api_key"]
    assert c["ok"] is False


def test_safety_failure_skips_prestop(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "read_wslconfig", lambda: "[wsl2]\nnetworkingMode=bridged\n")
    rc, d, data = _run(nr, tmp_path, _smoke_cfg(fake_fleet))
    s = _assert_written(d)
    assert rc == 5 and "rule1.wsl_nat" in s and _stop_count(data) == 0
    assert "前の艦隊を落とす(起動の前・失敗は無視)" not in _names(d)


def test_safety_rechecked_after_vram_adjustment(nr, fake_fleet, tmp_path, monkeypatch):
    monkeypatch.setattr(nr, "query_vram", lambda *a, **k: _vram(10.0))
    real_set = nr.set_flag

    def broken(args, flag, value):  # 調整が引数を壊したとする
        out = real_set(args, flag, value)
        return out + " --host 0.0.0.0" if isinstance(out, str) else out

    monkeypatch.setattr(nr, "set_flag", broken)
    rc, d, data = _run(nr, tmp_path, _vram_cfg(fake_fleet, _SAFE_VLLM_ARGS))
    s = _assert_written(d)
    assert rc == 5 and "安全の規則の再検査(VRAM の調整の後): **不合格** rule1.vllm_host" in s
    assert not (_only(data) / "start_argv.json").exists() and _FakeFleet.hits == []


def test_cleanup_failure_wins_over_zero_answers(nr, fake_fleet, tmp_path):
    pytest.importorskip("pyarrow")
    rows = {"agent_id": [1], "deferred": [0], "tokens_out": [0], "deferred_reason": [""]}
    cfg = _test_cfg(fake_fleet, commands=[{"name": "run", "argv": _tape_cmd(rows)}], stop_rc=1)
    cfg["experiments"]["T1"]["require_answers"] = True
    rc, d, data = _run(nr, tmp_path, cfg)
    s = _assert_written(d)
    assert rc == 4, s
    assert "艦隊が落ちていない" in s and "応答 0(401 の疑い)" in s and "終了コード 4 を優先" in s
    assert (d / "NIGHT_DONE").read_text(encoding="utf-8").strip() == "失敗(後始末にも失敗)"
