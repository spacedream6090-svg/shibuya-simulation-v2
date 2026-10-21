"""第 1 期 1-8b 発話の口: 腕の行(状態台帳 ``S8``=未読の列)が腕 on のランの再開で戻る(``LedgerRow.arm``・``arm_items``)。

- 腕 on: 発話の直後(未読が残る刻み)で止めて状態を書き、再開したランの final・checkpoint の 2 本のハッシュ・日の締めの後の
  2 本が通しのランと同じ。状態のファイルの末尾に腕の行の道筋 ``speech.inbox`` があり、未読が入っている。
- 腕を取り違えた再開は止まる(on で書いた状態を off で再開=設定の指紋の ``speech_port`` が違う・道筋の集合も違う)。
- 腕 on の behavior-hash は未読の列を読む(未読を 1 件足すと behavior と full の両方が動く)。
"""

from __future__ import annotations

import pytest

from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine import state_hashes as SH
from shibuya.engine.speech import port as P
from tests.engine.speech._s8b import run_small

NS = 60 * 10**9


@pytest.fixture(scope="module")
def straight():
    return run_small("on")


def test_resume_right_after_an_utterance_gives_the_straight_result(straight, tmp_path):
    evs = [e for e in straight.event_log.events() if e.what == "行為:発話"]
    assert evs
    stop = int(evs[0].t_ns // NS) + 1  # 発話の刻みの次の頭=未読が残っている
    run_small("on", state_out=str(tmp_path), stop_at_tick=stop)
    path = next(tmp_path.glob("state-T*.npz"))
    bundle = RS.read_state(path)
    full = [p for _k, p in SL.full_items()]
    # 〔1-3 の (1) の直し〕腕の行 S8(未読の列)と S8E(口の目印 → 記録の id=diag・required)
    assert list(bundle.items)[: len(full)] == full and list(bundle.items)[len(full):] == [
        "speech.inbox", "speech._mark_event_of"]
    assert bundle.items["speech.inbox"], "止めた刻みに未読が残っていない(試験の前提)"
    assert bundle.header["fingerprint"]["speech_port"] == "on"
    resumed = run_small("on", resume_from=str(path))
    assert resumed.final_hash == straight.final_hash
    assert [(c.tick, c.behavior_hash, c.full_hash) for c in resumed.checkpoints] == \
        [(c.tick, c.behavior_hash, c.full_hash) for c in straight.checkpoints if c.tick >= stop]
    assert resumed.state_hashes_end_of_day == straight.state_hashes_end_of_day


def test_resuming_with_the_other_arm_stops(tmp_path):
    run_small("on", state_out=str(tmp_path), stop_at_tick=300)
    path = next(tmp_path.glob("state-T*.npz"))
    with pytest.raises(ValueError, match="speech_port"):
        run_small("off", resume_from=str(path))


def test_the_unread_queue_moves_both_hashes_only_when_the_arm_is_on():
    port = P.SpeechPort()
    owners = {"speech": port}
    items_b = SL.arm_items(owners, behavior=True)
    items_f = SL.arm_items(owners, behavior=False)
    b0, f0 = SH.external_digest(owners, items_b)[0], SH.external_digest(owners, items_f)[0]
    port.say(P.SpeechContext(step=1, call_id="1:0:0"), P.Utterance(speaker=0, t_ns=NS, text="やあ", addressees=(1,)))
    assert SH.external_digest(owners, items_b)[0] != b0 and SH.external_digest(owners, items_f)[0] != f0
    # 計器(S8M=診断)は 2 つのハッシュに入らない。〔1-3 の (1) の直し〕S8E(diag・required)は full だけ
    assert all(k == "S8" for k, _ in items_b) and {k for k, _ in items_f} == {"S8", "S8E"}
