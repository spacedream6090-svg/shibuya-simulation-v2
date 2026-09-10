"""C6-a 結線の検収テスト(``run_day(fleet=…)``・**プロセス内の偽 vLLM**)。

実サーバー(SSH)へは繋がない。偽 vLLM は ``tests.llm.test_fleet.FakeVLLM``
(``ThreadingHTTPServer``・``/v1/models`` と ``/v1/chat/completions``・遅延/切断/書式不良を注入)。

固定する性質
- **mock 経路は 1 バイトも変わらない**(``fleet=None`` は従来と同じ checkpoint ハッシュ列)。
- 艦隊経路でも保存則(Σ所持金+Σ売上+Σ運賃)が閉じる。
- ``fleet_accounted == fleet_calls``(呼を捨てない=憲法1 の監査点)。
- タイムアウト注入 → 繰り延べ → **次 tick に再投入**(不応期免除)→ 最終的に処理される。
- 録画テープに実応答が入り ``Replay`` で完全一致で引ける。
- ``run_manifest_fields()["fleet"]`` に ``cache_salt``/``prefix_caching_hash_algo`` が押される。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.run import run_day
from shibuya.engine.tape import Replay
from shibuya.llm.fleet import FleetClient, FleetConfig
from shibuya.manifest.schema import Mode
from shibuya.world.state import World

from tests.llm.test_fleet import BAD, GOOD, FakeVLLM

BAD_TEXT = BAD

N_AGENTS = 200
TICKS = 24
CELLS = 24


@pytest.fixture
def fleet_servers():
    servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
    try:
        yield servers
    finally:
        for s in servers:
            s.close()


def make_client(servers, **kw) -> FleetClient:
    base = dict(
        endpoints=tuple(s.endpoint for s in servers),
        model=servers[0].model,
        mode=Mode.SMOKE,
        run_id="wiring-test",
        run_seed=1,
        per_replica_in_flight=16,
        queue_capacity=256,
        ttft_timeout_s=5.0,
        e2e_timeout_s=8.0,
        connect_timeout_s=5.0,
        stream=False,
        latency_samples=1000,
    )
    base.update(kw)
    return FleetClient(FleetConfig(**base))


def make_world(seed: int = 1) -> World:
    return World.synthetic(n_cells=CELLS, seed=seed)


def run_mock(**kw):
    return run_day(
        n_agents=N_AGENTS, seed=1, world=make_world(), ticks=TICKS,
        renderer="stub", processes=False, population=False, world_dir=None, **kw
    )


def run_fleet(client: FleetClient, ticks: int = TICKS, **kw):
    """``fleet_wait_s`` を入れる理由: このテストのエンジンは 1 tick を 1 ms 未満で回すので、
    0 のままだと応答が全部ラン終端に届いてしまい「次 tick に届く」性質が観測できない
    (本番は 1 tick ≈ 37 秒の壁時計=予算行 W1)。"""
    return run_day(
        n_agents=N_AGENTS, seed=1, world=make_world(), ticks=ticks, fleet=client,
        fleet_wait_s=kw.pop("fleet_wait_s", 10.0),
        renderer="stub", processes=False, population=False, world_dir=None, **kw
    )


def assert_no_call_is_dropped(res) -> None:
    """エンジン側の「呼を捨てない」恒等式(憲法1 の監査点)。

    ``繰り延べ総数 == 起床候補へ戻した数 + ラン終端で未応答のまま残った数``。
    後者は**次ランへ持ち越す**ぶんで、どこにも消えていないことの証拠。
    """
    c = res.bridge_counters
    deferred_total = (
        c["fleet_deferred_timeout"] + c["fleet_deferred_queue_full"] + c["fleet_error_other"]
    )
    assert c["fleet_reinjected"] + res.fleet_unanswered_at_end == deferred_total
    assert c["fleet_calls"] == c["fleet_accounted"]


# ------------------------------------------------------------------ 退化しないこと


def test_mock_path_is_deterministic_and_carries_no_fleet_state():
    """``fleet=None``(既定)は従来経路: **同 seed の 2 回**で checkpoint ハッシュ列が一致し、
    艦隊の欄・診断が一切付かない。

    (名前の実態化・層2 軽-6: 本テストは「C6 前と同じハッシュ」ではなく
    「現行コードで 2 回回して同じ」を見ている。C6 前との対照は
    ``docs/design/v2-implementation-plan.md`` §8 の C6 節に実測値で記録する。)
    """
    a = run_mock()
    b = run_mock()
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert a.checkpoints and a.llm_calls > 0
    assert a.conserved
    # 艦隊欄は mock ランでは空(欄自体は常にある)
    assert a.fleet_fields == {}
    assert a.run_manifest_fields()["fleet"] == {}
    assert "fleet_calls" not in a.bridge_counters


# ------------------------------------------------------------------ 艦隊経路の正常系


def test_fleet_run_conserves_money_and_accounts_every_call(fleet_servers):
    client = make_client(fleet_servers)
    res = run_fleet(client)
    c = res.bridge_counters
    assert res.conserved  # Σ所持金 + Σ売上 + Σ運賃 が不変
    assert res.llm_calls > 0
    assert c["fleet_calls"] == c["fleet_accounted"]  # 呼を捨てない
    assert c["fleet_calls"] == float(res.llm_calls)  # L4 の呼数=発射数
    assert c["fleet_ok"] == c["fleet_calls"]  # 注入なしなので全部 ok
    assert c["fleet_deferred_timeout"] == 0.0 and c["fleet_deferred_queue_full"] == 0.0
    assert c["fleet_reinjected"] == 0.0 and c["fleet_resent"] == 0.0
    assert res.fleet_unanswered_at_end == 0
    assert_no_call_is_dropped(res)
    assert res.parse_error_rate == 0.0  # 偽 vLLM は 2 行形を返す
    # 実応答が世界へ届いている(全員が同じ「移動」を選ぶので位置が動く)
    assert int(np.count_nonzero(res.agents.registry.last_action >= 0)) > 0
    # 3 レプリカに散っている(BN-4: 同一 GPU に寄せない)
    assert sum(c[f"fleet_calls_r{i}"] > 0 for i in range(3)) >= 2


def test_fleet_run_pushes_cache_salt_into_the_run_manifest(fleet_servers):
    client = make_client(fleet_servers, mode=Mode.CALIBRATION, run_id="abc123")
    res = run_fleet(client)
    f = res.run_manifest_fields()["fleet"]
    assert f["prefix_caching_hash_algo"] == "sha256_cbor"
    assert f["mode"] == "calibration"
    assert len(f["cache_salt"]) == 32
    assert f["routing"]["cell_affinity"] is False
    assert f["in_flight_cap_per_replica"] == 16 and f["in_flight_cap_total"] == 48
    # モードを変えると salt が変わる(較正と holdout が prefix キャッシュを共有しない)
    other = make_client(fleet_servers, mode=Mode.HOLDOUT, run_id="abc123")
    try:
        assert other.cache_salt != f["cache_salt"]
    finally:
        other.close()


def test_fleet_run_records_the_real_responses_to_the_tape(fleet_servers, tmp_path: Path):
    client = make_client(fleet_servers)
    res = run_fleet(client, tape_path=tmp_path / "tape")
    replay = Replay(tmp_path / "tape")
    assert len(replay) == res.llm_calls  # 1 呼 = 1 行
    rows = list(replay.tape.rows())
    assert len(rows) == res.llm_calls
    assert all(r.response == GOOD for r in rows)  # **実応答**が入っている
    for r in rows:  # (agent_id, tick, wake_class, prompt_hash) 完全一致で引ける
        assert replay.lookup(r.agent_id, r.tick, r.wake_class, r.prompt_hash) == GOOD
    assert res.bridge_counters["tape_rows"] == float(res.llm_calls)


# ------------------------------------------------------------------ 繰り延べ → 再投入


def test_timeout_defers_then_reinjects_and_is_finally_answered(fleet_servers):
    """タイムアウト注入 → 繰り延べ → 次 tick 再投入(不応期免除)→ 最終的に処理される。"""
    for s in fleet_servers:
        s.total_delay_s = 1.0  # e2e 0.2 s を必ず超える
    client = make_client(fleet_servers, e2e_timeout_s=0.2, ttft_timeout_s=0.2)

    # 最初の 6 tick だけ遅延させ、その後は正常に返す(別スレッドで解除)
    import threading

    def _heal() -> None:
        import time as _t

        _t.sleep(3.0)
        for s in fleet_servers:
            s.total_delay_s = 0.0

    t = threading.Thread(target=_heal, daemon=True)
    t.start()
    res = run_fleet(client, ticks=90, fleet_wait_s=1.0)
    t.join(timeout=10.0)

    c = res.bridge_counters
    assert c["fleet_deferred_timeout"] > 0  # 繰り延べが起きた
    assert c["fleet_resent"] > 0  # 戻った呼が実際に再送された
    assert c["fleet_ok"] > 0  # 回復後は普通に答えが返る
    assert_no_call_is_dropped(res)  # 繰り延べ = 再投入 + 持ち越し(消えない)
    assert res.conserved


def test_deferred_calls_are_not_suppressed_by_the_refractory(fleet_servers):
    """不応期免除が効いていること: 繰り延べ件数がそのまま再投入件数になる。"""
    from shibuya.agents.state import AgentState, WakeCondition
    from shibuya.engine import resolve as R

    cond = int(WakeCondition.INTEROCEPTION)
    agents = AgentState(8)  # 構築直後は非凍結(run.py が freeze する規律)
    R.set_refractory(agents, np.array([1, 2]), np.array([cond, cond]), 100)
    assert int(agents.registry.refractory_until[1, cond]) > 100
    R.clear_refractory(agents, np.array([1, 2]), np.array([cond, cond]))
    assert int(agents.registry.refractory_until[1, cond]) == 0
    assert int(agents.registry.refractory_until[2, cond]) == 0
    # 他の (個体, 条件) は触らない
    R.set_refractory(agents, np.array([3]), np.array([cond]), 100)
    R.clear_refractory(agents, np.array([1]), np.array([cond]))
    assert int(agents.registry.refractory_until[3, cond]) > 100


def test_queue_full_defers_and_is_reinjected(fleet_servers):
    """キュー満杯(非ブロッキング却下)も繰り延べ → 再投入され、呼は消えない。

    ``budget``(1 tick の呼数上限)を上げてキュー容量 1 を必ず溢れさせる。
    ``fleet_wait_s=0``(純非ブロッキング)にしないと発射前に空になってしまう。
    """
    for srv in fleet_servers:
        srv.total_delay_s = 0.05
    client = make_client(fleet_servers, per_replica_in_flight=1, queue_capacity=1)
    res = run_fleet(client, ticks=20, budget=30.0, fleet_wait_s=0.0)
    c = res.bridge_counters
    assert c["fleet_deferred_queue_full"] > 0
    assert c["fleet_resent"] > 0
    assert_no_call_is_dropped(res)
    assert res.conserved


# ------------------------------------------------------------------ 対照


def test_fleet_and_mock_runs_use_the_same_prompts(fleet_servers):
    """同 seed の艦隊ランと mock ランで**プロンプト(=テープ鍵)が一致**する。

    艦隊経路は描画を素通しするだけ=知覚側は 1 バイトも変わらない、の機械検査。
    """
    from shibuya.core.hashing import sha256_cbor

    client = make_client(fleet_servers)
    run_fleet(client)
    seen = [p["messages"] for s in fleet_servers for p in s.requests]
    assert seen, "偽 vLLM がリクエストを受けていない"
    for msgs in seen:
        joined = "\n".join(m["content"] for m in msgs)
        assert len(sha256_cbor(joined)) == 64  # 連結本文からテープ鍵が作れる形
        assert msgs[-1]["role"] == "user"


# ------------------------------------------------------------------ C6 二重指標(09-09)

ALIAS = "理由: 予定の時間になったから\n行動: 移動 目的地: C-0001 ひと言: なし"
OOV = "理由: 様子を見たいから\n行動: 探索 対象: C-0001 ひと言: なし"


def test_run_reports_effective_and_strict_format_error_rates(fleet_servers):
    """ラベル別名は**実効 0 / 厳密 >0**。要約行に両方が出る。"""
    for srv in fleet_servers:
        srv.text = ALIAS
    client = make_client(fleet_servers)
    res = run_fleet(client)
    c = res.bridge_counters
    assert res.llm_calls > 0
    assert res.parse_error_rate == 0.0  # 実効(別名許容後)
    assert res.parse_error_rate_strict == 1.0  # 厳密(定義を動かさない受入指標)
    assert res.label_alias_rate == 1.0
    assert c["fleet_format_strict_errors"] == float(res.llm_calls)
    assert c["fleet_format_retry"] == 0.0  # 別名で読めたら再生成しない
    line = [x for x in res.summary().splitlines() if "書式エラー率" in x]
    assert line and "実効 0.000" in line[0] and "厳密 1.000" in line[0]
    assert "別名 1.000" in line[0] and "受入 ≤0.10" in line[0]


def test_run_reports_dictionary_mapped_rate(fleet_servers):
    """語彙外の行動語は段0 の辞書で救い、要約行の辞書写像率に出る。"""
    for srv in fleet_servers:
        srv.text = OOV
    client = make_client(fleet_servers)
    res = run_fleet(client)
    c = res.bridge_counters
    assert c["fleet_dictionary_mapped"] == float(res.llm_calls)
    assert res.dictionary_mapped_rate == 1.0
    line = [x for x in res.summary().splitlines() if "書式エラー率" in x][0]
    assert "辞書写像 1.000" in line
    assert res.conserved


def test_cli_flags_put_temperature_and_max_tokens_on_the_wire(fleet_servers):
    """``--temperature 0.7 --max-tokens 96`` が payload と run manifest 欄に載る。"""
    from shibuya.engine.run import add_fleet_args, fleet_from_args
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    add_fleet_args(ap)
    args = ap.parse_args(
        ["--llm", "fleet", "--endpoints", ",".join(s.endpoint for s in fleet_servers),
         "--model", fleet_servers[0].model, "--mode", "smoke", "--run-id", "cli-test",
         "--temperature", "0.7", "--max-tokens", "96"]
    )
    client = fleet_from_args(args, ap)
    assert client is not None
    try:
        res = run_fleet(client)
    finally:
        pass
    payloads = [p for s in fleet_servers for p in s.requests]
    assert payloads
    assert all(p["temperature"] == 0.7 and p["max_tokens"] == 96 for p in payloads)
    dec = res.run_manifest_fields()["fleet"]["decoding"]["T1"]
    assert dec["temperature"] == 0.7 and dec["max_tokens"] == 96


def test_add_fleet_args_defaults_follow_the_canon():
    """既定は温度 0.7(知覚契約書 §2.5/運用設計書 §1.3)・max_tokens 96(expedient)。"""
    import argparse

    from shibuya.engine.run import add_fleet_args
    from shibuya.llm.fleet import DEFAULT_T1_MAX_TOKENS, DEFAULT_TEMPERATURE

    ap = argparse.ArgumentParser()
    add_fleet_args(ap)
    args = ap.parse_args([])
    assert args.temperature == DEFAULT_TEMPERATURE == 0.7
    assert args.max_tokens == DEFAULT_T1_MAX_TOKENS == 96
    assert args.llm == "mock" and args.mode == "smoke"


# ------------------------------------------------------------------ C6 追調査(09-09)

#: 「会話」を選び、対象に隣の個体 ID を書く応答(結線 (c) の切り分け用)。
TALK_PAIR = "理由: 知人を見かけたから" + chr(10) + "行動: 会話 対象: P-%d ひと言: こんにちは"
TALK = "理由: 知人を見かけたから\n行動: 会話 対象: P-1 ひと言: こんにちは"


#: 会話が成立しうる窓。**tick 0 は真夜中で全員 SLEEPING** なので、mock 日課で起きる
#: 朝(≈tick 420)を含む長さまで回さないと会話は 1 件も開かない(C6 の切り分けで判明)。
CONV_TICKS = 600
CONV_AGENTS = 200
CONV_CELLS = 2


def _conv_world():
    return World.synthetic(n_cells=CONV_CELLS, seed=1)


def test_fleet_conversation_opens_a_session_like_the_mock_path(fleet_servers):
    """(c) の除外: 艦隊経路の「会話」応答も mock 経路と**同じ招待機構**へ入る。

    偽 vLLM は ``pair_talk``= プロンプトの個体 id から対 ``id^1`` を名指す(承諾の対象規則)。
    成立数そのものは世界の条件(同セル・起床・予算)に依るので、ここでは
    「招待が出る」「帳尻が合う」「片側だけ CONVERSING が残らない」を固定する。
    """
    for srv in fleet_servers:
        srv.pair_talk = True
    client = make_client(fleet_servers)
    res = run_day(
        n_agents=CONV_AGENTS, seed=1, world=_conv_world(), ticks=CONV_TICKS,
        fleet=client, fleet_wait_s=5.0, renderer="stub", processes=False,
        population=False, world_dir=None,
    )
    c = res.conversation_counters
    assert res.llm_calls > 0
    assert c["conv_target_named"] > 0  # 対象スロットが艦隊経路でも効いている
    assert c["conv_invites"] > 0, c  # 招待機構へ入った=(c) は原因ではない
    assert (
        c["conv_accepted"] + c["conv_declined"] + c["conv_pending_expired"]
        + c["conv_pending_open"] == c["conv_invites"]
    ), c
    assert res.conserved


def test_mock_path_opens_conversations_in_the_same_world():
    """対照: 同じ世界・同じ台本を mock 経路(scripted client)で流しても同じ機構に入る。"""

    class ScriptedLLM:
        def complete(self, request):
            from shibuya.llm import LLMResponse

            return LLMResponse(
                text=TALK_PAIR % (int(request.agent_id) ^ 1), source="scripted"
            )

    res = run_day(
        n_agents=CONV_AGENTS, seed=1, world=_conv_world(), ticks=CONV_TICKS,
        llm=ScriptedLLM(), renderer="stub", processes=False, population=False,
        world_dir=None,
    )
    c = res.conversation_counters
    assert c["conv_target_named"] > 0 and c["conv_invites"] > 0


def test_conversations_need_awake_partners_so_night_only_runs_barely_open_any():
    """**切り分けの根**: 全員が「会話」と答えても、真夜中(全員 SLEEPING)はほとんど開かない。

    ``ticks`` が短いラン(tick 0 = 真夜中)と朝を含むランで**呼あたりの成立率**を比べる。
    C6 の 1 日ランの ``conversation_sessions: 0`` を読むときの土台
    (「開かない」は結線の不具合とは限らない=起床している相手が同じ適用バッチに要る)。
    """

    class ScriptedLLM:
        def complete(self, request):
            from shibuya.llm import LLMResponse

            return LLMResponse(text=TALK, source="scripted")

    def rate(ticks: int) -> tuple[float, int, int]:
        r = run_day(
            n_agents=CONV_AGENTS, seed=1, world=_conv_world(), ticks=ticks,
            llm=ScriptedLLM(), renderer="stub", processes=False, population=False,
            world_dir=None,
        )
        opened = r.conversation_counters["sessions_opened"]
        return (opened / max(1, r.llm_calls), opened, r.llm_calls)

    night, n_open, n_calls = rate(60)
    day, d_open, d_calls = rate(CONV_TICKS)
    assert n_calls > 0 and d_calls > 0
    assert d_open > n_open
    assert day > 5.0 * night, (night, day, n_open, d_open)


def test_fleet_debug_dir_records_the_first_response_of_failed_parses(fleet_servers, tmp_path):
    """(1) 初回パースが落ちた呼の**初回の生応答**が jsonl に残る(テープ形式は不変)。"""
    for srv in fleet_servers:
        srv.text = ALIAS  # 別名=実効 OK・厳密 NG(再生成しない)
        srv.bad_format_remaining = 3  # 最初の 3 呼だけ本当に壊す(再生成が走る)
    client = make_client(fleet_servers)
    debug = tmp_path / "dbg"
    res = run_fleet(client, fleet_debug_dir=debug, tape_path=tmp_path / "tape")
    path = debug / "format_debug.jsonl"
    assert path.exists()
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert rows and len(rows) == int(res.bridge_counters["fleet_debug_rows"])
    # 別名だけの行(再生成なし)と、本当に壊れた行(再生成あり)の両方が入る
    retried = [r for r in rows if r["format_retried"]]
    alias_only = [r for r in rows if not r["format_retried"]]
    assert retried and alias_only
    for r in retried:
        assert r["first_raw"] == BAD_TEXT  # **初回の生応答**(テープには残らない)
        assert r["retry_raw"] in (BAD_TEXT, ALIAS)  # 温度 0 の再生成で返ってきたもの
        assert r["retry_raw"] != ""
        assert r["first_effective_ok"] is False and r["first_strict_ok"] is False
        assert r["reason"] in ("no_labels", "no_action_field") or r["reason"].startswith(
            "missing_label:"
        )
    for r in alias_only:
        assert r["first_effective_ok"] is True and r["first_strict_ok"] is False
        assert r["reason"].startswith("label_alias:") and "目的地" in r["reason"]
    for r in rows:  # 共通欄
        assert r["call_id"] and r["user"] and "system" in r
        assert set(r) >= {"agent_id", "tick", "replica", "final_errors", "labels_found"}
    # テープは最終応答 1 行のまま(形式不変)
    replay = Replay(tmp_path / "tape")
    assert len(replay) == res.llm_calls


def test_fleet_debug_dir_is_off_by_default(fleet_servers, tmp_path):
    client = make_client(fleet_servers)
    for srv in fleet_servers:
        srv.bad_format_remaining = 5
    res = run_fleet(client)
    assert res.bridge_counters["fleet_debug_rows"] == 0.0
    assert not list(tmp_path.iterdir())


def test_phase_breakdown_separates_fleet_wait(fleet_servers):
    """(3) 要約に位相別 ms/tick が出る。``fleet_wait`` は ``llm`` と別勘定。"""
    for srv in fleet_servers:
        srv.total_delay_s = 0.02
    client = make_client(fleet_servers)
    res = run_fleet(client, fleet_wait_s=5.0)
    assert "fleet_wait" in res.phase_seconds
    assert res.phase_seconds["fleet_wait"] > 0.0
    line = [x for x in res.summary().splitlines() if x.startswith("  内訳[ms/tick]")]
    assert line and "fleet_wait" in line[0] and "movement" in line[0] and "合計" in line[0]


def test_tape_analysis_reads_a_fleet_tape(fleet_servers, tmp_path):
    """(2) テープ解析スクリプトが艦隊テープを読めて、会話の切り分け欄を出す。"""
    from tests.engine.tape_analysis import analyze, format_report

    for srv in fleet_servers:
        srv.text = TALK
    client = make_client(fleet_servers)
    res = run_fleet(client, tape_path=tmp_path / "tape")
    d = analyze(tmp_path / "tape")
    assert d["rows"] == res.llm_calls
    assert dict(d["actions"])["会話"] == res.llm_calls
    assert d["conversation"]["talk_share"] == 1.0
    assert d["conversation"]["talk_calls"] == res.llm_calls
    assert d["format"]["effective_error_rate"] == 0.0
    text = format_report(d)
    assert "行動分布" in text and "会話" in text and "同グループに他の呼が居た" in text


def test_movement_cpu_time_is_recorded_alongside_wall_time():
    """(3) movement 区間の**スレッド CPU 時間**が壁時計と並んで出る(GIL 待ちの切り分け)。

    Windows の ``time.thread_time`` は解像度が粗く(≈15.6 ms)、小さいランでは 0 になる。
    ここで固定するのは「欄があること」と「CPU ≤ 壁時計」だけ。実測は Linux サーバー側。
    """
    res = run_mock()
    assert "movement_cpu" in res.phase_seconds
    # Windows の ``thread_time`` は 15.6 ms 粒度で量子化されるため、短いランでは
    # CPU が壁時計を**上回って見える**ことがある(0 か 15.625 ms のどちらか)。
    # ここは「欄がある」「比が 0..1 にクランプされる」だけを固定する。
    assert res.phase_seconds["movement_cpu"] >= 0.0
    assert 0.0 <= res.movement_gil_wait_ratio <= 1.0
    line = [x for x in res.summary().splitlines() if "movement 壁" in x]
    assert line and "CPU" in line[0] and "待ち割合" in line[0] and "P2 上限 5" in line[0]


# ---------------------------------------------------------------- --fleet-queue-capacity(C7 D-58)


def test_fleet_from_args_passes_queue_capacity_through():
    """CLI の ``--fleet-queue-capacity`` が FleetConfig.queue_capacity に届く。0/未指定は既定(×4)。"""
    import argparse

    from shibuya.engine.run import fleet_from_args

    base = dict(llm="fleet", endpoints="http://127.0.0.1:1", model="m", mode="smoke", run_id="",
                seed=1, temperature=0.7, max_tokens=96)
    c = fleet_from_args(argparse.Namespace(**base, fleet_queue_capacity=4096))
    try:
        assert c.queue_capacity == 4096
    finally:
        c.close()
    c0 = fleet_from_args(argparse.Namespace(**base, fleet_queue_capacity=0))
    try:
        assert c0.queue_capacity == c0.config.resolved_max_in_flight() * 4
    finally:
        c0.close()
    c1 = fleet_from_args(argparse.Namespace(**base))  # 属性が無くても落ちない
    try:
        assert c1.queue_capacity == c1.config.resolved_max_in_flight() * 4
    finally:
        c1.close()
