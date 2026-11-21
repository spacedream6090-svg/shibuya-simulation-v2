"""第 348(返事その 9 §1 の 19・§5-2 の 6): 艦隊の書式の判定にランの語彙を渡す(記録 library-defaults-q13-347 §4-8 の 1)。

前は ``FleetClient`` の既定の判定(``fleet._format_ok``)が語彙を見ずに v1 の規則で読んだ。語彙 v3 のラン(CLI の既定)では
「なし」「食事」の応答が書式の誤りと判定され、温度 0 の再生成が 1 呼増えた。今は ``FleetBridge`` が組み立てのときに、
橋の語彙(=ランの語彙)を結んだ判定を ``FleetClient`` に渡す(``FleetClient.bind_run_vocab``)。

偽の艦隊は ``tests.llm.test_fleet.FakeVLLM``(プロセス内の ThreadingHTTPServer)。ランの形は ``tests.engine.test_fleet_wiring``。
"""

from __future__ import annotations

import pytest

from shibuya.runtime.inference.fleet import FleetBridge, FleetClient

from tests.llm.test_fleet import BAD, GOOD, FakeVLLM, make_config, mkcall

#: 語彙 v3 の「なし」(5 ラベル)。
V3_NONE = "理由: 疲れたから\n行動: なし 対象: なし 活動: 休む まで: 30分"
#: 語彙 v3 の「なし」で対象を省いた形(第275 #4 で v3 は書式どおり)。
V3_NONE_NO_TARGET = "理由: 疲れたから\n行動: なし 活動: 休む まで: 30分"
#: 語彙 v3 の「食事」。
V3_EAT = "理由: お腹がすいたから\n行動: 食事 対象: 飲食店 活動: 食事 まで: 30分"
#: 語彙 v2 の「食事」(4 ラベル)。
V2_EAT = "理由: お腹がすいたから\n行動: 食事 対象: 飲食店 ひと言: なし"

N_CALLS = 4


@pytest.fixture
def fleet2():
    servers = [FakeVLLM(), FakeVLLM()]
    try:
        yield servers
    finally:
        for s in servers:
            s.close()


def _drain(servers, text: str, vocab: str, **client_kw) -> tuple[dict, int, list]:
    for s in servers:
        s.text = text
    with FleetClient(make_config(servers, stream=False), **client_kw) as client:
        bridge = FleetBridge(client, vocab_version=vocab)
        out = bridge.submit_and_drain([mkcall(i, cell=i % 2) for i in range(N_CALLS)], timeout=20.0)
        c = bridge.counters()
    return c, sum(s.n_requests for s in servers), out


def _show(c: dict, n_req: int) -> str:
    return (f"fleet_format_retry={c.get('fleet_format_retry')} fleet_format_retry_ok={c.get('fleet_format_retry_ok')} "
            f"requests={n_req} calls={N_CALLS}\n")


# ------------------------------------------------------------------ 橋の語彙 v3
@pytest.mark.parametrize("text", [V3_NONE, V3_NONE_NO_TARGET, V3_EAT], ids=["none", "none_no_target", "eat"])
def test_v3_bridge_does_not_count_none_and_eat_as_format_errors(fleet2, text):
    """語彙 v3 の「なし」「食事」は書式どおり=再生成しない(1 呼 = 1 要求)。"""
    c, n_req, out = _drain(fleet2, text, "v3")
    assert c["fleet_format_retry"] == 0 and n_req == N_CALLS, "v3 の応答を書式の誤りに数えた\n" + _show(c, n_req)
    assert all(r.parse.format_ok for r in out)


# ------------------------------------------------------------------ 橋の語彙 v1・v2(前の値を固定)
@pytest.mark.parametrize(
    "vocab, text, retried",
    [
        ("v1", GOOD, False),
        ("v1", V3_NONE, True),  # v1 のランに v3 の形の応答=前と同じく書式の誤り
        ("v1", V2_EAT, True),  # v1 に「食事」は無い=前と同じ
        ("v2", GOOD, False),
        ("v2", V3_NONE, True),  # v2 に「なし」は無い=前と同じ
    ],
    ids=["v1_good", "v1_v3none", "v1_eat", "v2_good", "v2_v3none"],
)
def test_v1_and_v2_bridges_judge_as_before(fleet2, vocab, text, retried):
    """語彙 v1・v2 の橋では、前と同じ判定(再生成するかと要求の数)。"""
    c, n_req, _ = _drain(fleet2, text, vocab)
    want = (N_CALLS if retried else 0, 2 * N_CALLS if retried else N_CALLS)
    assert (c["fleet_format_retry"], n_req) == want, f"{vocab} の判定が前と違う(want={want})\n" + _show(c, n_req)


@pytest.mark.parametrize("text", [BAD, GOOD], ids=["broken", "v1_four_labels"])
def test_v3_bridge_regenerates_format_errors(fleet2, text):
    """〔検収 中-2〕語彙 v3 の橋は、書式の誤りを温度 0 で再生成する(橋が判定を結ばないと再生成が丸ごと切れる退行を捕まえる)。
    v1 の 4 ラベルの形(活動・まで が無い)は、前は v1 の規則で書式どおりだった。今は v3 の規則で書式の誤り(記録 §5-3 の「増える」)。"""
    c, n_req, _ = _drain(fleet2, text, "v3")
    want = (N_CALLS, 2 * N_CALLS)
    assert (c["fleet_format_retry"], n_req) == want, f"v3 で書式の誤りを再生成しない(want={want})\n" + _show(c, n_req)


def test_v2_bridge_no_longer_retries_eat(fleet2):
    """〔第 348 で変わる判定〕語彙 v2 の橋の「食事」の応答。前は判定が v1 の規則で読み、書式の誤り=再生成していた
    (``fleet_format_retry`` = 呼数・要求 = 2 × 呼数)。今は v2 の規則で読み、書式どおり=再生成しない。"""
    c, n_req, out = _drain(fleet2, V2_EAT, "v2")
    assert c["fleet_format_retry"] == 0 and n_req == N_CALLS, "v2 の「食事」を書式の誤りに数えた\n" + _show(c, n_req)
    assert all(r.parse.action == "食事" for r in out)


# ------------------------------------------------------------------ 結ぶ口の決まり
def test_explicit_format_check_is_kept_by_the_bridge(fleet2):
    """``format_check`` を明示して渡した口は、橋が結び直さない(渡した判定が勝つ)。"""
    c, n_req, _ = _drain(fleet2, V3_NONE, "v3", format_check=lambda text: False)
    assert c["fleet_format_retry"] == N_CALLS and n_req == 2 * N_CALLS, _show(c, n_req)


def test_format_retry_off_stays_off(fleet2):
    """``format_retry=False`` の口には、橋が判定を結ばない(再生成しない)。"""
    for s in fleet2:
        s.text = BAD
    with FleetClient(make_config(fleet2, stream=False, format_retry=False)) as client:
        bridge = FleetBridge(client, vocab_version="v3")
        bridge.submit_and_drain([mkcall(0)], timeout=20.0)
        c = bridge.counters()
    n_req = sum(s.n_requests for s in fleet2)
    assert c["fleet_format_retry"] == 0 and n_req == 1, _show(c, n_req)


def test_client_without_a_bridge_or_a_check_does_not_regenerate(fleet2):
    """橋を通さず判定も渡さない口は、書式の判定を持たない(語彙の既定を持たない=再生成しない)。"""
    for s in fleet2:
        s.text = BAD
    with FleetClient(make_config(fleet2, stream=False)) as client:
        client.submit([mkcall(0)])
        client.drain(timeout=20.0)
        c = client.counters()
    n_req = sum(s.n_requests for s in fleet2)
    assert c["fleet_format_retry"] == 0 and n_req == 1, _show(c, n_req)


def test_format_check_for_binds_the_vocab():
    """``format_check_for(版)`` はその版の規則で読む判定(不正な版は止める)。"""
    from shibuya.runtime.inference.fleet import format_check_for

    assert format_check_for("v3")(V3_NONE) is True
    assert format_check_for("v1")(V3_NONE) is False
    assert format_check_for("v2")(V2_EAT) is True and format_check_for("v1")(V2_EAT) is False
    assert format_check_for("v1")(GOOD) is True
    with pytest.raises(ValueError):
        format_check_for("v9")


# ------------------------------------------------------------------ ランの形(test_fleet_wiring と同じ組み立て)
@pytest.mark.parametrize("text", [V3_NONE, V3_EAT], ids=["none", "eat"])
def test_v3_run_does_not_regenerate_none_and_eat(text):
    """``run_day(vocab_version="v3", fleet=…)``: 組み立てが作る橋がランの語彙を口に結ぶ=「なし」「食事」で再生成しない。"""
    from tests.engine.test_fleet_wiring import make_client, run_fleet

    servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
    try:
        for s in servers:
            s.text = text
        res = run_fleet(make_client(servers), ticks=2, vocab_version="v3")
        c = res.bridge_counters
        n_req = sum(s.n_requests for s in servers)
    finally:
        for s in servers:
            s.close()
    msg = (f"fleet_calls={c.get('fleet_calls')} fleet_format_retry={c.get('fleet_format_retry')} requests={n_req}\n")
    assert c["fleet_calls"] > 0, "呼が立っていない\n" + msg
    assert c["fleet_format_retry"] == 0 and n_req == c["fleet_calls"], "v3 のランで再生成した\n" + msg


def test_v3_run_regenerates_every_broken_answer():
    """〔検収 中-2〕``run_day(vocab_version="v3", fleet=…)`` で、書式の誤りの応答は全呼を温度 0 で再生成する。"""
    from tests.engine.test_fleet_wiring import make_client, run_fleet

    servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
    try:
        for s in servers:
            s.text = BAD
        res = run_fleet(make_client(servers), ticks=2, vocab_version="v3")
        c = res.bridge_counters
        n_req = sum(s.n_requests for s in servers)
    finally:
        for s in servers:
            s.close()
    msg = (f"fleet_calls={c.get('fleet_calls')} fleet_format_retry={c.get('fleet_format_retry')} requests={n_req}\n")
    assert c["fleet_calls"] > 0, "呼が立っていない\n" + msg
    assert c["fleet_format_retry"] == c["fleet_calls"] and n_req == 2 * c["fleet_calls"], "v3 のランで再生成しない\n" + msg


def test_v1_run_judges_v3_none_as_before():
    """``run_day(vocab_version="v1", fleet=…)`` では、v3 の形の「なし」は前と同じく書式の誤り(全呼を再生成)。"""
    from tests.engine.test_fleet_wiring import make_client, run_fleet

    servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
    try:
        for s in servers:
            s.text = V3_NONE
        res = run_fleet(make_client(servers), ticks=2, vocab_version="v1")
        c = res.bridge_counters
        n_req = sum(s.n_requests for s in servers)
    finally:
        for s in servers:
            s.close()
    msg = (f"fleet_calls={c.get('fleet_calls')} fleet_format_retry={c.get('fleet_format_retry')} requests={n_req}\n")
    assert c["fleet_calls"] > 0, "呼が立っていない\n" + msg
    assert c["fleet_format_retry"] == c["fleet_calls"] and n_req == 2 * c["fleet_calls"], "v1 の判定が前と違う\n" + msg
