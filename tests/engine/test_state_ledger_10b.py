"""10b: 状態台帳の宣言・追加 C の AST の検査・behavior-hash と full-hash・揺らし試験・保留の組の call_id。

アジェンダ ``docs/design/v2-d102-10b-agenda.md`` §4 の T1(準備)・T2・T3・T4・T5・T6 と既知の答え(2 日のラン)。
final(``Checkpoint.combined``)は今の定義のまま=既定の結果は動かない(byte-check は記録 10b/README.md)。
〔10e(E1・版上げ 1 回目)〕既定の final は behavior-hash になり、死蔵の 5 列を消した(台帳 188 行)。旧い final は
``hash_scheme="full"`` で再現する(消した 3 列は ``core.soa.retired_columns_in_hash`` の中だけで元の位置に混ざる)。
〔第330・RET〕旧い final の切替口 ``hash_scheme="full"``(``legacy_combined``・``retired_columns_in_hash``・``Registry.retire``)
と乱数の ``stateful`` を消し、K15 の 2 列(``fail_streak``・``plan_activity``)を消した(台帳 187 行)。旧値の再現の試験は
第330 ACT の commit で通ったことを 10e の記録 §RET に書いて消した。AST の試験の「読み手 0 の no の列」の例は
``fail_streak`` から ``rel_last`` に替えた。
"""

from __future__ import annotations

import dataclasses
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pytest

from tests import golden_env as GE

import shibuya.engine.resolve as RES
import shibuya.engine.run as RUN
from shibuya.engine.systems import state_io as SIO  # 1-0: full-hash の呼び出しは state_io を通す(差し替えの的)
from shibuya.agents.state import AgentState
from shibuya.core.hashing import blake3_hex
from shibuya.core.soa import Registry
from shibuya.engine import state_hashes as SH
from shibuya.engine import state_ledger as SL
from shibuya.engine import state_ledger_ast as SA
from shibuya.engine.run import Checkpoint, run_day
from shibuya.perception.state import PerceptionState
from shibuya.world.state import World

SRC = Path(__file__).resolve().parents[2] / "src" / "shibuya"
WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")

N = 100
CELLS = 16
TPD = 1_440
ALL_ARMS = dict(vocab_version="v3", memory="on", relations="on", store_memory="on", familiarity="on",
                hunger_model="energy", rel_copresent="on")
CLASSICAL_ARMS = dict(ALL_ARMS, policy="classical", chooser="classical")
#: Q9 の 3 列+A4 の 2 列(10e(E1)で消した死蔵の列)。
DEAD5 = ("agents.plan_cursor", "agents.invocation_distance", "agents.wake_pending_class",
         "perception.last_b2_hash", "perception.last_b4_hash")
#: T7(10e で門の形を確定): 目標=宣言値(5,000 体で 1 回の checkpoint ≤ 100 ms・超えたら警告)/ 門=checkpoint の
#: 壁時計の合計がシミュ全体の壁時計に占める割合 ≤ 1%(**未リサーチ(expedient)**・実測は既定 v3 で約 0.2%)。
T7_TARGET_SECONDS = 0.100
T7_SHARE_CAP = 0.01
#: T7 で確かめる既定 v3 の final(10e の版上げの段ごとに張り替える)。
T7_V3_FINAL = "b8eadcb51e8705e7"  # 〔改訂(第330・ACT)〕活性化の値(B6build は 0483d1165e245bed・E4・E5 は 4fbf61616af1e3d2・E1 は 3264c9fc190b3eb9・E2 は 4985ff2fb3c771c4)  # 〔2-4 V1〕前 5f7ae9ff24005314  # 〔2-4 V2〕前 4bcca9f0216362bb  # 〔2-4 V3〕前 7857ecb16b9665cd  # 〔2-4 V4〕前 f6488d4d5eadf5ca
#: A2 (b): 構成で読み手が変わる 6 列(どの構成でも behavior)。
A2B_SIX = ("age", "sex", "talk_partner", "weight_kg", "sm_last", "mem_last")


# ================================================================= 1. 状態台帳の宣言(A3)
def test_ledger_has_187_rows_in_two_axes():
    """材料の 163 行(SoA 98+外の状態 65)+10b-2 の棚卸しで足した外の状態 24 行(O66〜O89)+10d の 5 行(O90〜O94)
    +10f の 1 行(O95=O75 から読み手 0 の 2 属性を diag に分けた)−10e(E1)の死蔵の 5 列(Q9 の 3 列+A4 の 2 列)
    +10e(E1・検収 R1)の 1 行(O96=O44 から再生の到着待ちを軸 1 no に分けた)−〔第330・RET〕K15 の 2 列
    (前: agents 76・SoA 93・全体 189・版 ``state-ledger/10e``)。
    〔第 1 期 1-3〕出来事の記録の行 ``E``(軸 1 diag・軸 2 discardable)を足して外の状態 97 行・全体 188 行(試験の名は
    187 のまま=履歴)。どちらのハッシュにも状態のファイルにも入らない行なので版は上げない(仮採用・記録 e13/README.md)。
    〔第 1 期 1-6〕記憶の器の行 ``M0``(軸 1 no・軸 2 derivable・中身は全部 hash_skip)と ``M0R``(diag・discardable)を
    足して外の状態 99 行・全体 190 行。どちらもハッシュと状態のファイルに入らない=版は上げない(記録 m0/README.md)。
    〔第 1 期 1-9〕金と物の台帳の行の目印の列と transfer の計器の行 ``A``(軸 1 diag・軸 2 discardable)を足して外の状態
    100 行・全体 191 行(1-6 の 2 行と合わせて・同じ理由で版は上げない=記録 cp2/README.md)。
    〔第 1 期 1-2〕知覚の事実の行 ``P``(``TickScratch.percepts``・軸 1 no・軸 2 discardable・道筋なし)を足して外の状態
    101 行・全体 192 行(1-6・1-9 の行の後・版は上げない=同じ理由・記録 p12/README.md)。
    〔第 1 期 1-8 J0〕候補の口の行 ``J0``(``DecisionLayer`` の計器と営業中の店の控え・軸 1 diag・軸 2 discardable)を足して
    外の状態 102 行・全体 193 行(1-2 の行の後・版は上げない=同じ理由・記録 j0/README.md)。
    〔第 1 期 1-7〕連絡先の印の行 ``CT5``(``rel_layer._contact_flags``・軸 1 diag・軸 2 derivable・中身は全部 hash_skip=M0 と同じ形)
    を足して外の状態 103 行・全体 194 行(1-8 の J0 の後・版は上げない=同じ理由・記録 c0/README.md)。
    〔第 1 期 1-8b〕発話の口の腕の行 ``S8``(未読の列・軸 1 behavior・軸 2 required・腕の行=腕 on のランだけハッシュと状態の
    ファイルに入る)と ``S8M``(計器・diag・discardable)を足して外の状態 105 行・全体 196 行(1-7 の CT5 の後・版は上げない=
    既定 off のランの状態のファイルは前と同じ中身・記録 s8b/README.md)。
    〔第 2 期 2-2 段 11a〕近接の層の行 ``PX``(``ProximityLayer`` の計器・軸 1 diag・軸 2 discardable)と近傍の索引の行 ``PX0``
    (``TickScratch.near_index``・軸 1 no・軸 2 discardable・道筋なし)を足して外の状態 107 行・全体 198 行(1-8b の S8M の後・
    版は上げない=同じ理由・記録 prox22/README.md)。
    〔第 2 期 2-1〕経済の段階 2 の行 ``EC``(中身・behavior・derivable・hash_skip)・``ATM``(ATM の表・同)・``CR``(信用の器・
    diag・derivable・hash_skip)・``EM``(生ログの支払いの方法の列・diag・discardable)を足して外の状態 111 行・全体 202 行
    (2-2 の PX0 の後・どれもハッシュにも状態のファイルにも入らない=版は上げない・記録 ec21/README.md)。
    〔第 2 期 2-3〕記憶の器の記録の目印の seq の腕の行 ``M0L``(軸 1 no・軸 2 required・腕 memory-store)を足して外の状態 113 行・
    全体 204 行(3-3 の X の後・腕の行=既定のランのハッシュと状態のファイルは不変=版は上げない・記録 md23/README.md)。
    〔第 3 期 3-1〕暦 1a の影の行 ``CAL``(軸 1 diag・軸 2 derivable・中身は全部 hash_skip=CT5 と同じ形・腕 1a のランだけ持ち主)を
    足して外の状態 114 行・全体 205 行(2-3 の M0L の後・版は上げない=同じ理由・記録 ca31/README.md)。"""
    c = SL.counts()
    # 〔第 3 期 3-3〕申込書の控えの行 X(diag・discardable・どちらのハッシュにも状態のファイルにも入らない)を足して 112・203
    # 〔第 2 期 2-3〕その後に腕の行 M0L を足して 113・204
    # 〔第 3 期 3-2〕その後に計算のまとめの窓の行 BW(diag・discardable・どちらのハッシュにも状態のファイルにも入らない)を足して 114・205
    # 〔第 3 期 3-5〕その後に本人の体の層の行 BD(diag・discardable・どちらのハッシュにも状態のファイルにも入らない)を足して 115・206
    # 〔第 3 期 3-1〕その後に暦 1a の影の行 CAL(diag・derivable・中身は hash_skip)を足して 116・207
    # 〔第 6 期 6-5〕その後に記憶の腕の行 M0M(腕 memory-model)・M0C(腕 memory-cue)と計数の行 M0X(diag)と
    # 〔検収 M4〕店の行の表の腕の行 M0S(腕 memory-people)を足して 120・211
    # 〔第 6 期 6-2〕カレンダー 1b の腕の行 C1B(behavior・required)と C1BM(diag・required)を足して 122・213(腕 calendar の
    # ランだけ持ち主=既定の 2 つのハッシュと状態のファイルは不変・版は上げない=同じ理由・記録 ca1b/README.md)
    # 〔第 6 期 6-3〕その後に時計の段 T2〜T4 の腕の行 TCR・TCC(腕 talk-clock)・T3M(腕 step-scope)・T4W(腕 clock-regional)
    # (どれも diag・discardable=どちらのハッシュにも状態のファイルにも入らない)を 6-2 の C1B・C1BM の後に足して 126・217
    # 〔第 6 期 6-4 C1〕その後に連絡の道具の腕の行 CT1D・CT1A・CT1AS・CT1I・CT1IS・CT1C・CT1K・CT1S・CT1M・CT1G・CT1Q(腕 contact-c1)を足して 137・228
    assert c == {"agents": 74, "cells": 5, "pois": 9, "perception": 3, "external": 137, "soa": 91, "total": 228}
    assert SL.LEDGER_VERSION == "state-ledger/10e-ret"
    keys = [r.key for r in SL.LEDGER]
    assert len(set(keys)) == len(keys)
    assert [r.key for r in SL.external_rows()] == [f"O{i}" for i in range(1, 97)] + ["E", "M0", "M0R", "A", "P", "J0",
                                                                                     "CT5", "S8", "S8M",
                                                                                     "PX", "PX0", "EC", "ATM", "CR", "EM", "X",
                                                                                     "M0L", "BW", "BD", "CAL", "M0M",
                                                                                     "M0C", "M0X", "M0S", "C1B", "C1BM",
                                                                                     "TCR", "TCC", "T3M", "T4W", "CT1D", "CT1A",
                                                                                     "CT1AS", "CT1I", "CT1IS", "CT1C",
                                                                                     "CT1K", "CT1S", "CT1M", "CT1G", "CT1Q"]
    assert (SL.row("X").behavior, SL.row("X").restore, SL.row("X").arm) == (SL.DIAG, SL.DISCARDABLE, "")
    assert (SL.row("BW").behavior, SL.row("BW").restore, SL.row("BW").arm) == (SL.DIAG, SL.DISCARDABLE, "")
    assert (SL.row("E").behavior, SL.row("E").restore) == (SL.DIAG, SL.DISCARDABLE)
    assert (SL.row("M0").behavior, SL.row("M0").restore) == (SL.NO, SL.DERIVABLE)
    assert set(SL.row("M0").hash_skip) == set(SL.row("M0").items)
    assert (SL.row("M0R").behavior, SL.row("M0R").restore) == (SL.DIAG, SL.DISCARDABLE)
    assert (SL.row("A").behavior, SL.row("A").restore) == (SL.DIAG, SL.DISCARDABLE)
    assert (SL.row("P").behavior, SL.row("P").restore, SL.row("P").items) == (SL.NO, SL.DISCARDABLE, ())
    assert (SL.row("J0").behavior, SL.row("J0").restore) == (SL.DIAG, SL.DISCARDABLE)
    assert (SL.row("CT5").behavior, SL.row("CT5").restore) == (SL.DIAG, SL.DERIVABLE)
    assert set(SL.row("CT5").hash_skip) == set(SL.row("CT5").items) == {"rel_layer._contact_flags"}
    assert (SL.row("S8").behavior, SL.row("S8").restore, SL.row("S8").arm) == (SL.BEHAVIOR, SL.REQUIRED, "speech-port")
    assert (SL.row("S8M").behavior, SL.row("S8M").restore) == (SL.DIAG, SL.DISCARDABLE)
    # 腕の行(1-8b の 2 行+2-3 の M0L+〔第 6 期 6-5〕M0M・M0C・〔検収 M4〕M0S+〔第 6 期 6-2〕C1B・C1BM)
    # 〔第 6 期 6-3〕その後に TCR・TCC・T3M・T4W
    assert [r.key for r in SL.LEDGER if r.arm] == ["S8", "S8M", "M0L", "M0M", "M0C", "M0S", "C1B", "C1BM",
                                                   "TCR", "TCC", "T3M", "T4W", "CT1D", "CT1A", "CT1AS", "CT1I", "CT1IS", "CT1C", "CT1K", "CT1S", "CT1M", "CT1G", "CT1Q"]  # 〔6-4 C1〕
    for k, arm in (("TCR", "talk-clock"), ("TCC", "talk-clock"), ("T3M", "step-scope"), ("T4W", "clock-regional")):
        assert (SL.row(k).behavior, SL.row(k).restore, SL.row(k).arm) == (SL.DIAG, SL.DISCARDABLE, arm), k
    assert (SL.row("PX").behavior, SL.row("PX").restore, SL.row("PX").items) == (SL.DIAG, SL.DISCARDABLE,
                                                                                ("proximity._meter",))
    assert (SL.row("PX0").behavior, SL.row("PX0").restore, SL.row("PX0").items) == (SL.NO, SL.DISCARDABLE, ())
    for r in SL.LEDGER:
        assert r.behavior in SL.AXIS1_VALUES, r.key
        assert r.restore in SL.AXIS2_VALUES, r.key
        assert r.basis, r.key
        assert set(r.hash_skip) <= set(r.items), r.key
        if r.ast_allow:
            assert r.is_soa and r.behavior != SL.BEHAVIOR, r.key
            assert all(a.reason for a in r.ast_allow)
        if r.dead:
            assert (r.behavior, r.restore) == (SL.NO, SL.DISCARDABLE), r.key
        if r.is_soa:
            assert not r.items, r.key
    # 外の状態の行で full に入る行は、属性の道筋を 1 つ以上持つ(O65 は捨ててよい=道筋なし)
    for r in SL.external_rows():
        if r.in_full:
            assert r.items, r.key


def test_ledger_declarations_from_the_decisions():
    row = SL.row
    for name in A2B_SIX:  # A2 (b)
        assert row(f"agents.{name}").behavior == SL.BEHAVIOR
    for key in ("pois.revenue", "agents.energy_balance"):  # 挙動=入れない・復元=要る
        assert (row(key).behavior, row(key).restore) == (SL.DIAG, SL.REQUIRED)
    for key in ("perception.heading", "perception.task_flag"):  # 派生=入れない(親の宣言)
        assert row(key).behavior == SL.NO
    # 〔改訂(第330・RET)〕K15 の 2 列は列ごと消した(前: no・復元 unknown・full に入る)
    keys = {r.key for r in SL.LEDGER}
    assert not ({"agents.fail_streak", "agents.plan_activity"} & keys)
    a = AgentState(3, plan_columns=True)
    assert "fail_streak" not in a.registry.arrays and "plan_activity" not in a.registry.arrays
    assert "plan_flags" in a.registry.arrays
    assert row("O31").restore == SL.REQUIRED and row("O31").items == ("energy.out_of_area.d_armed",)
    for key in ("O58", "O60", "O61"):  # リング 3 行(K16 の既定案)
        assert row(key).restore == SL.DISCARDABLE
    # 10e(E1): 死蔵の 5 列は台帳から消えた(残る死蔵は知覚の単体ベンチの逃げ道 1 行だけ)
    assert {r.key for r in SL.LEDGER if r.dead} == {"perception.invocation_distance"}
    keys = {r.key for r in SL.LEDGER}
    assert not (set(DEAD5) & keys)


def _all_columns_state(n: int = 3) -> tuple[AgentState, World, PerceptionState]:
    a = AgentState(n, plan_columns=True, edge_columns=True, attention_columns=True, activity_columns=True,
                   familiarity_columns=True, energy_columns=True, memory_columns=True,
                   store_memory_columns=True, relation_columns=True)
    return a, World.synthetic(n_cells=9, seed=1), PerceptionState(n, include_invocation_distance=True)


def _dtype_tag(d: Any) -> str:
    dt = np.dtype(d.dtype)
    tag = f"{dt.kind if dt.kind != 'b' else 'u'}{dt.itemsize}"
    if d.shape_per_entity:
        tag += "x" + "x".join(str(s) for s in d.shape_per_entity)
    return tag


def test_ledger_matches_the_actual_soa_columns_and_types():
    """表と実際の SoA の列名と型が一致する(列が増えたら表に無い→失敗)。"""
    a, w, p = _all_columns_state()
    regs = {"agents": a.registry, "cells": w.cells, "pois": w.pois, "perception": p.registry}
    for place, reg in regs.items():
        got = {d.name: d for d in reg.decls}
        want = {r.name: r for r in SL.soa_rows(place)}
        assert set(got) == set(want), place
        for name, d in got.items():
            assert _dtype_tag(d) == want[name].dtype, (place, name)
            assert d.actual_bytes_per_entity == int(want[name].nbytes), (place, name)


# ================================================================= 2. 追加 C の AST の検査(T3)
@pytest.fixture(scope="module")
def scanned() -> SA.ScanResult:
    return SA.scan(SRC)


def test_ast_check_passes_on_the_current_source(scanned):
    assert SA.check(scanned) == []
    # 走査は src/shibuya 全体(engine だけでは world/・perception/ の読み手を見落とす)
    assert scanned.files > 90
    for name in ("noise_stage", "open_from", "open_to"):
        assert any(not s.path.startswith("engine/") for s in scanned.strict[name]), name


def _flip(key: str, behavior: str) -> tuple[SL.LedgerRow, ...]:
    return tuple(dataclasses.replace(r, behavior=behavior, ast_allow=()) if r.key == key else r
                 for r in SL.LEDGER)


def test_ast_check_fails_when_hunger_is_declared_no(scanned):
    out = SA.check(scanned, _flip("agents.hunger", SL.NO))
    assert any(v.startswith("agents.hunger:") for v in out), out


def test_ast_check_fails_through_a_name_table(scanned):
    """``fatigue`` の読みは名前の表 INTERO_VARS / INTEROCEPTION_FIELDS 経由だけ(属性の読みは 0)。"""
    import re

    assert scanned.strict["fatigue"]
    assert not any(re.search(r"\.fatigue", s.text) for s in scanned.strict["fatigue"])
    out = SA.check(scanned, _flip("agents.fatigue", SL.NO))
    assert any(v.startswith("agents.fatigue:") for v in out), out


def test_ast_check_fails_when_a_behavior_column_has_no_reader(scanned):
    # 10e(E1): 死蔵の plan_cursor を消したので、読み手 0 の no の列で見る(〔改訂(第330・RET)〕fail_streak を K15 で
    # 消したので rel_last に替えた)
    out = SA.check(scanned, _flip("agents.rel_last", SL.BEHAVIOR))
    assert any("agents.rel_last: 軸 1 が behavior なのに読み手 0" in v for v in out), out


@pytest.mark.parametrize("code", [
    "def f(reg, a):\n    return reg.rel_last[a] > 3\n",  # 直接の読み
    "def f(reg, a):\n    tmp = reg.rel_last\n    if tmp[a] > 3:\n        return 1\n",  # 一時変数経由
    "NAMES = ('rel_last',)\n\ndef f(r):\n    return [r.field(n) for n in NAMES]\n",  # 名前の表経由
    "def f(r):\n    for n in ('rel_last', 'x'):\n        r.field(n)\n",  # 直書きの組を回す
    "def f(r):\n    return r.field('rel_last')\n",  # 文字列
], ids=["direct", "temp_var", "name_table", "literal_loop", "string"])
def test_ast_check_catches_a_new_reader_of_a_no_column(tmp_path, code):
    fp = tmp_path / "engine" / "fake.py"
    fp.parent.mkdir()
    fp.write_text(code, encoding="utf-8")
    res = SA.scan(tmp_path, files=[fp], names={"rel_last"})
    rows = [SL.row("agents.rel_last")]
    out = SA.check(res, rows, unresolved_allow=(), check_declared=False)
    assert any(v.startswith("agents.rel_last:") for v in out), (code, out)
    # 書くだけ・自己更新は読みに数えない
    fp.write_text("def f(reg, a):\n    reg.rel_last[a] = reg.rel_last[a] + 1\n    reg.rel_last[a] = 0\n",
                  encoding="utf-8")
    assert SA.check(SA.scan(tmp_path, files=[fp], names={"rel_last"}), rows, unresolved_allow=(),
                    check_declared=False) == []


def test_ast_check_fails_on_an_unresolved_dynamic_read(tmp_path):
    fp = tmp_path / "engine" / "fake.py"
    fp.parent.mkdir()
    fp.write_text("def f(r, name):\n    return r.field(name)\n", encoding="utf-8")
    out = SA.check(SA.scan(tmp_path, files=[fp], names={"hunger"}), [], unresolved_allow=(), check_declared=False)
    assert any("解決できない動的な読み" in v for v in out), out


def test_ast_check_fails_on_a_stale_allow(scanned):
    stale = SL.AstAllow("engine/run.py", "この文字列はどこにも無い", "試験")
    ledger = tuple(dataclasses.replace(r, ast_allow=r.ast_allow + (stale,)) if r.key == "agents.rel_last" else r
                   for r in SL.LEDGER)
    out = SA.check(scanned, ledger)
    assert any("古い許可" in v for v in out), out


def test_ast_false_positives_band_and_b4_hash_are_explicit(scanned):
    """材料 §2-4 の誤検出 2 列は、読みの場所と根拠つきで許す(黙って外さない)。

    〔第 2 期 2-2 段 11a〕``agents.band`` には腕 ``--proximity distance`` だけの読み手 2 か所(``engine/proximity.py`` の
    1 か所に集めた読み・``perception/renderer.py`` の B5 の近接行の自分の層)の許可を足した(3 個=誤検出 1 と合わせて)。
    〔第 2 期 2-4 V2〕近接の既定が distance になり、組み立ての規則と描画は体の層を ``agents.cell`` から導く形に替えた=
    描画の許可は消した(2 個=誤検出 1+試験の合成の規則の道)。"""
    n_allow = {"agents.band": 2, "cells.b4_hash": 1}
    for key, path in (("agents.band", "world/assets.py"), ("cells.b4_hash", "world/state.py")):
        r = SL.row(key)
        assert r.behavior == SL.NO and len(r.ast_allow) == n_allow[key] and r.ast_allow[0].path == path
        hits = [s for s in scanned.loose[r.name] if SA._allowed(s, r.ast_allow)]
        assert hits, key
    assert [a.path for a in SL.row("agents.band").ast_allow[1:]] == ["engine/proximity.py"]
    # b4_hash のプロパティ World.b4_hash の呼び手は 0(属性 .b4_hash の読みはプロパティの中の 1 か所だけ)
    assert [str(s) for s in scanned.loose["b4_hash"]] == [str(s) for s in scanned.loose["b4_hash"]
                                                         if s.path == "world/state.py"]


def test_ast_check_detects_a_new_declared_column(tmp_path, scanned):
    res = SA.ScanResult(strict=scanned.strict, loose=scanned.loose, unresolved=scanned.unresolved,
                        declared={**scanned.declared, "agents": scanned.declared["agents"] + ["new_col"]},
                        files=scanned.files)
    out = SA.check(res)
    assert any("宣言と台帳の列が違う" in v and "new_col" in v for v in out), out


# ================================================================= 3. ハッシュの関数(T2・T4・T6)
def _registry_without(reg: Registry, drop: frozenset[str]) -> Registry:
    """``drop`` の列を宣言から消した写し(10e の列の削除を模す)。"""
    out = Registry(reg.n_entities, kind=reg.kind, per_entity_byte_cap=None)
    for d in reg.decls:
        if d.name in drop:
            continue
        out.declare(d.name, d.dtype, d.shape_per_entity, byte_budget_per_agent=d.byte_budget_per_entity,
                    mechanism=d.mechanism, doc=d.doc)
        out.field(d.name)[...] = reg.field(d.name)
    return out


def _fill_random(reg: Registry, seed: int) -> None:
    rng = np.random.default_rng(seed)
    for d in reg.decls:
        arr = reg.field(d.name)
        arr.flags.writeable = True
        raw = arr.reshape(-1).view(np.uint8)
        raw[:] = rng.integers(0, 256, raw.size, dtype=np.uint8)
        if arr.dtype.kind == "f":  # NaN を避ける(比較は生バイトでよいが値として扱える形に)
            arr[...] = rng.normal(size=arr.shape).astype(arr.dtype)


def test_t2_exclude_equals_deleting_the_columns():
    """``state_hash(exclude=S)`` == 「S を宣言から消した ``state_hash()``」(10e の手順の前提・材料 §2-3)。"""
    a, w, _ = _all_columns_state(50)
    _fill_random(a.registry, 1)
    # 10e(E1): 死蔵の 3 列は消えたので、no の 2 列で「除いて計算」と「消して計算」を比べる
    # (〔改訂(第330・RET)〕K15 の fail_streak・plan_activity を消したので fam_last・rel_last に替えた)
    for drop in (frozenset({"fam_last", "rel_last"}),
                 SL.behavior_excluded("agents"), frozenset()):
        assert a.registry.state_hash(exclude=drop) == _registry_without(a.registry, drop).state_hash()
        if drop:
            assert a.registry.state_hash() != _registry_without(a.registry, drop).state_hash()
    # 陽性対照: hunger を 1 要素変えると behavior の側も動く
    before = a.registry.state_hash(exclude=SL.behavior_excluded("agents"))
    a.registry.field("hunger")[0] ^= 1
    assert a.registry.state_hash(exclude=SL.behavior_excluded("agents")) != before


def test_t2_behavior_hash_equals_the_final_after_deleting_the_non_behavior_columns():
    """10e で behavior でない列を消して final を ``state_hash()`` で計算すると、10b の behavior-hash と一致する。"""
    a, w, _ = _all_columns_state(40)
    for reg, seed in ((a.registry, 1), (w.cells, 2), (w.pois, 3)):
        _fill_random(reg, seed)
    owners = {k: None for k in {it.split(".")[0] for _, it in SL.full_items() + SL.behavior_items()}}
    beh = SH.behavior_hash(a, w, "pop", "sched", "act", owners)
    a2 = _registry_without(a.registry, SL.behavior_excluded("agents")).state_hash()
    w2 = blake3_hex((_registry_without(w.cells, SL.behavior_excluded("cells")).state_hash() + "\x1f"
                     + _registry_without(w.pois, SL.behavior_excluded("pois")).state_hash()).encode("utf-8"))
    ext = SH.external_digest(owners, SL.behavior_items())[0]
    # 10e の final = 今の combined の組み立て(列を消した SoA)の末尾に外の状態の behavior の行の digest
    assert beh == blake3_hex("\x1f".join([a2, w2, "pop", "sched", "act", ext]).encode("utf-8"))
    # 〔改訂(第330・RET)〕「何も除かない列の組なら 10e より前の final の組み立て(legacy_combined)」は切替口と一緒に消した
    # 10e(E1): 既定の final は behavior-hash そのもの
    assert Checkpoint(0, a.state_hash(), w.state_hash(), "pop", "sched", "act", behavior_hash=beh).combined == beh


def test_checkpoint_combined_is_the_behavior_hash():
    """10e(E1): final は behavior-hash。〔改訂(第330・RET)〕旧い組み立て(``hash_scheme="full"``・``legacy_combined``)を
    消した=``Checkpoint`` に ``hash_scheme`` の欄は無く、``run_day`` に ``hash_scheme`` を渡すと止まる。"""
    beh = Checkpoint(0, "a", "w", "p", "s", "x", behavior_hash="b", full_hash="f")
    assert beh.combined == "b"
    assert dataclasses.replace(beh, agents_hash="a2").combined == "b"  # 全列のハッシュは final に効かない
    assert not hasattr(beh, "legacy_combined") and "hash_scheme" not in {f.name for f in dataclasses.fields(beh)}
    with pytest.raises(ValueError):
        Checkpoint(0, "a", "w", "p", "s").combined  # final に behavior-hash が無い
    with pytest.raises(TypeError):
        run_day(n_agents=4, ticks=2, hash_scheme="full")


def test_e1_retire_and_the_retired_hash_are_gone():
    """〔改訂(第330・RET)〕10e(E1)の「消した死蔵の 3 列を旧い final の再現のためにハッシュの中で元の位置に並べ直す」口
    (``Registry.retire``・``core.soa.retired_columns_in_hash``)を消した(前の試験は消す前の宣言を組み直した写しと同じ
    ハッシュになることを見ていた=第330 ACT の commit で通った)。消した列はどこにも現れない。"""
    import shibuya.core.soa as SOA

    assert not hasattr(Registry, "retire") and not hasattr(SOA, "retired_columns_in_hash")
    for a in (AgentState(7), _all_columns_state(9)[0]):
        assert not ({"plan_cursor", "invocation_distance", "wake_pending_class", "fail_streak", "plan_activity"}
                    & set(a.registry.arrays))


def test_e1_r1_replay_inbox_is_out_of_the_behavior_hash():
    """10e(E1・検収 R1): 再生の到着待ち(``run_day.replay_inbox``)は軸 1 no・軸 2 required(O96)。behavior-hash の項に
    無く、full-hash の項にはある。艦隊の繰り延べと待ち(O44)は behavior のまま。"""
    beh = {p for _k, p in SL.behavior_items()}
    full = {p for _k, p in SL.full_items()}
    assert "run_day.replay_inbox" not in beh and "run_day.replay_inbox" in full
    assert {"run_day.fleet_deferred", "run_day.fleet_waiting"} <= beh
    o96 = SL.row("O96")
    assert (o96.behavior, o96.restore, o96.items) == (SL.NO, SL.REQUIRED, ("run_day.replay_inbox",))


def test_e1_r1_fleet_deferred_is_hashed_as_a_multiset():
    """10e(E1・検収 R1 の続き): 艦隊の繰り延べの list は並びに依らず、中身(多重集合)が変われば動く。"""
    from types import SimpleNamespace

    assert SL.row("O44").multiset == ("run_day.fleet_deferred",)
    assert SL.row("O43").multiset == ("run_day.pending",)
    items = [(3, 10, 3, 0), (1, 10, 3, 0), (3, 10, 3, 0)]

    def dig(lst):
        rd = SimpleNamespace(fleet_deferred=lst)
        return SH.item_digest({"run_day": rd}, "O44", "run_day.fleet_deferred")[0]

    assert dig(items) == dig(list(reversed(items))) == dig([items[1], items[0], items[2]])
    assert dig(items) != dig(items[:2]) and dig(items) != dig(items + [(1, 10, 3, 0)])


def test_e1_dead_columns_are_gone_from_the_soa():
    """10e(E1・Q9・A4): 死蔵の 5 列は SoA から消え、宣言のバイトが減った(agents −5 B/体・知覚 −16 B/体)。"""
    a, _w, p = _all_columns_state(3)
    for key in DEAD5:
        place, name = key.split(".")
        reg = a.registry if place == "agents" else p.registry
        assert name not in reg.arrays, key
    assert set(PerceptionState(3).registry.arrays) == {"heading", "task_flag"}
    assert PerceptionState(3).declared_bytes_per_agent == 2


def test_to_state_is_canonical_and_strict():
    assert SH.to_state({"b": 1, "a": [1, 2.5, None]}) == SH.to_state({"a": [1, 2.5, None], "b": 1})
    assert SH.to_state({3, 1, 2}) == SH.to_state({2, 3, 1})
    assert SH.to_state((1, 2)) != SH.to_state([1, 2])
    assert SH.to_state(np.arange(3, dtype=np.int32)) != SH.to_state(np.arange(3, dtype=np.int64))
    assert SH.to_state(True) != SH.to_state(1)
    g1, g2 = np.random.default_rng(5), np.random.default_rng(5)
    assert SH.to_state(g1) == SH.to_state(g2)
    g2.random()
    assert SH.to_state(g1) != SH.to_state(g2)

    class Unknown:
        pass

    with pytest.raises(TypeError, match="直列化の書き手が無い型"):
        SH.to_state([Unknown()])


@contextmanager
def _spy_hash_inputs(monkeypatch) -> Iterator[list[dict[str, Any]]]:
    """checkpoint ごとに full-hash の入力(agents・world・知覚 SoA・owners)を控える。"""
    seen: list[dict[str, Any]] = []
    real = SIO.full_state_hash

    def spy(agents, world, pstate, pop, sched, owners, **kw):
        seen.append(dict(agents=agents, world=world, pstate=pstate, pop=pop, sched=sched, owners=owners))
        return real(agents, world, pstate, pop, sched, owners, **kw)

    monkeypatch.setattr(SIO, "full_state_hash", spy)
    yield seen


def _full(c: dict[str, Any]) -> str:
    return SH.full_hash(c["agents"], c["world"], c["pstate"], c["pop"], c["sched"], c["owners"])[0]


def _beh(c: dict[str, Any]) -> str:
    return SH.behavior_hash(c["agents"], c["world"], c["pop"], c["sched"], "", c["owners"])


@contextmanager
def _writable(arr: np.ndarray) -> Iterator[np.ndarray]:
    was = arr.flags.writeable
    arr.flags.writeable = True
    try:
        yield arr
    finally:
        arr.flags.writeable = was


@pytest.fixture(scope="module")
def all_arms_capture():
    mp = pytest.MonkeyPatch()
    try:
        with _spy_hash_inputs(mp) as seen:
            res = run_day(n_agents=N, seed=1, n_cells=CELLS, ticks=TPD, checkpoint_every=360, budget=float(N),
                          **ALL_ARMS)
        yield res, seen[-1]
    finally:
        mp.undo()


def test_t4_full_hash_detects_one_element_of_required_external_state(all_arms_capture):
    res, c = all_arms_capture
    o = c["owners"]
    base_full, base_beh = _full(c), _beh(c)
    assert len(base_full) == 64

    def moved(mutate, undo) -> tuple[bool, bool]:
        mutate()
        try:
            return _full(c) != base_full, _beh(c) != base_beh
        finally:
            undo()
            assert _full(c) == base_full

    rel = o["rel_layer"]
    conv = o["conv"]
    arb = o["arbiter"]
    pend = o["run_day"].pending
    act = o["act_layer"]
    # 軸 1 が behavior・要る(外の状態): full も behavior も動く(10b-2・親の答え 3)
    assert moved(lambda: rel._acq_until.__setitem__((0, 0), rel._acq_until[0, 0] + 1),
                 lambda: rel._acq_until.__setitem__((0, 0), rel._acq_until[0, 0] - 1)) == (True, True)
    assert moved(lambda: conv._refusal_until.__setitem__((10**6, 10**6 + 1), 5),
                 lambda: conv._refusal_until.pop((10**6, 10**6 + 1))) == (True, True)
    pool0 = arb._pool
    assert moved(lambda: setattr(arb, "_pool", pool0 + 1.0), lambda: setattr(arb, "_pool", pool0)) == (True, True)
    assert moved(lambda: pend.append((10**6, 0, 0, 0, "", 0, -1, 0, -1, None, None, 0, "0:0:0")),
                 lambda: pend.pop()) == (True, True)
    t0 = act.text[0]
    assert moved(lambda: act.text.__setitem__(0, t0 + "x"), lambda: act.text.__setitem__(0, t0)) == (True, True)
    # 軸 1 が no/diag・要る(外の状態): full だけが動く
    waste = o["runner"].waste
    g0 = waste.waste_g_collected
    assert moved(lambda: setattr(waste, "waste_g_collected", g0 + 1.0),
                 lambda: setattr(waste, "waste_g_collected", g0)) == (True, False)
    flow = o["ledger"].money._flow if o["ledger"] is not None else None
    if flow is not None:
        assert moved(lambda: flow.__setitem__((0, 0, 0), flow[0, 0, 0] + 1),
                     lambda: flow.__setitem__((0, 0, 0), flow[0, 0, 0] - 1)) == (True, False)
    # 軸 2 が不明(安全側で full に入る): 店の混雑の場
    occ = o["runner"].crowd.occupancy
    if occ.size:
        assert moved(lambda: occ.__setitem__(0, occ[0] + 1), lambda: occ.__setitem__(0, occ[0] - 1)) == (True, True)
    # 捨ててよい・キャッシュ: どちらも動かない
    mem = o["mem_layer"]
    assert moved(lambda: mem.stats.__setitem__("__t4__", 1), lambda: mem.stats.pop("__t4__")) == (False, False)
    assert moved(lambda: act._digest_cache.__setitem__("__t4__", b"x"),
                 lambda: act._digest_cache.pop("__t4__")) == (False, False)
    n_set = act.n_set
    assert moved(lambda: setattr(act, "n_set", n_set + 1), lambda: setattr(act, "n_set", n_set)) == (False, False)


@pytest.mark.parametrize("key,full_moves,beh_moves", [
    ("agents.hunger", True, True),            # behavior・要る
    ("agents.rel_last", True, False),         # no・要る(〔改訂(第330・RET)〕前は K15 の fail_streak=no・不明)
    ("agents.energy_balance", True, False),   # diag・要る
    ("pois.revenue", True, False),            # diag・要る
    ("cells.open_count", True, False),        # no・導出できる
    ("pois.stock", True, True),
    ("perception.heading", True, False),      # 派生(no)・導出できる
])
def test_t4_soa_rows_move_the_hashes_by_their_axes(all_arms_capture, key, full_moves, beh_moves):
    _, c = all_arms_capture
    place, name = key.split(".")
    reg = {"agents": c["agents"].registry, "cells": c["world"].cells, "pois": c["world"].pois,
           "perception": c["pstate"].registry}[place]
    base_full, base_beh = _full(c), _beh(c)
    with _writable(reg.field(name)) as arr:
        flat = arr.reshape(-1)
        old = flat[0].copy()
        flat[0] = old + 1 if arr.dtype.kind != "f" else old + 1.0
        try:
            assert (_full(c) != base_full, _beh(c) != base_beh) == (full_moves, beh_moves)
        finally:
            flat[0] = old
    assert _full(c) == base_full


def test_full_hash_marks_absent_owners():
    """腕が立っていない持ち主は「無い」の印だけ(エラーにしない)。根の鍵が無いのは配線の誤り。"""
    a, w, p = _all_columns_state(4)
    owners = {k: None for k in {it.split(".")[0] for _, it in SL.full_items()}}
    h1, sizes = SH.full_hash(a, w, p, "", "", owners)
    h2, _ = SH.full_hash(a, w, None, "", "", owners)
    assert h1 != h2 and set(sizes) == {k for k, _ in SL.full_items()}
    owners.pop("conv")
    with pytest.raises(KeyError):
        SH.full_hash(a, w, p, "", "", owners)


def test_t6_behavior_columns_do_not_depend_on_the_configuration(monkeypatch):
    """構成を変えても behavior の列の集合は表から決まる(A2 (b))。age・sex は v1 の構成でも behavior。"""
    seen_sets = []
    for kw in ({"vocab_version": "v1"}, ALL_ARMS, CLASSICAL_ARMS):
        with _spy_hash_inputs(monkeypatch) as seen:
            run_day(n_agents=20, seed=1, n_cells=CELLS, ticks=60, checkpoint_every=60, budget=20.0, **kw)
        names = {d.name for d in seen[-1]["agents"].registry.decls}
        beh = names - SL.behavior_excluded("agents")
        assert beh == names & SL.behavior_columns("agents")
        assert {"age", "sex", "talk_partner"} <= beh
        seen_sets.append(SL.behavior_excluded("agents"))
        monkeypatch.undo()
    assert seen_sets[0] == seen_sets[1] == seen_sets[2]
    assert not (set(A2B_SIX) & SL.behavior_excluded("agents"))


# ================================================================= 4. 揺らし試験(T5)と T1 の準備
def _edge_value(dtype: np.dtype, mode: int, rng: np.random.Generator, shape) -> np.ndarray:
    if dtype.kind == "f":
        v = {0: rng.normal(scale=1e6, size=shape), 1: np.full(shape, -1e30), 2: np.full(shape, 1e30)}[mode]
        return v.astype(dtype)
    info = np.iinfo(dtype)
    if mode == 1:
        return np.full(shape, info.min, dtype=dtype)
    if mode == 2:
        return np.full(shape, info.max, dtype=dtype)
    return rng.integers(info.min, info.max, size=shape, dtype=dtype, endpoint=True)


def _perturbing_run(monkeypatch, run_fn, targets: tuple[str, ...], *, every: int = 37, start: int = 360,
                    tape: Path | None = None):
    """``targets`` の列(``place.name``)をランの途中で乱数と端の値で揺らす。

    知覚 SoA と world の参照は最初の checkpoint で控える(それより後の tick から揺らす)。
    揺らすのは各 tick の頭(``resolve.advance_body`` の直後)。"""
    real_adv = RES.advance_body
    holder: dict[str, Any] = {}
    real_full = SIO.full_state_hash
    rng = np.random.default_rng(12345)
    n_done: dict[str, Any] = {"n": 0, "keys": set()}

    def spy(agents, world, pstate, pop, sched, owners, **kw):
        holder.setdefault("world", world)
        holder.setdefault("pstate", pstate)
        return real_full(agents, world, pstate, pop, sched, owners, **kw)

    def adv(agents, tick, *a, **k):
        out = real_adv(agents, tick, *a, **k)  # 体を進めた**後**に揺らす(energy の空腹は体から作り直されるため)
        if targets and tick >= start and tick % every == 0 and "world" in holder:
            regs = {"agents": agents.registry, "cells": holder["world"].cells, "pois": holder["world"].pois,
                    "perception": holder["pstate"].registry if holder["pstate"] is not None else None}
            for key in targets:
                place, name = key.split(".")
                reg = regs[place]
                if reg is None or name not in reg:
                    continue
                arr = reg.field(name)
                with _writable(arr):
                    arr[...] = _edge_value(arr.dtype, (tick // every) % 3, rng, arr.shape)
                n_done["n"] += 1
                n_done["keys"].add(key)
        return out

    monkeypatch.setattr(SIO, "full_state_hash", spy)
    monkeypatch.setattr(RES, "advance_body", adv)
    try:
        res = run_fn(tape)
    finally:
        monkeypatch.undo()
    assert "world" in holder, "full_state_hash の差し替えが使われていない(1-0: state_io を通す)"
    return res, n_done


def _observed(res, tape: Path | None) -> dict[str, Any]:
    out = {
        "calls": int(res.llm_calls),
        "action_usage": dict(res.action_usage),
        "calls_by_condition": dict(res.calls_by_condition),
        "behavior": [c.behavior_hash for c in res.checkpoints],
    }
    if tape is not None:
        import pyarrow.parquet as pq

        out["prompt_hash"] = pq.read_table(tape / "calls.parquet").column("prompt_hash").to_pylist()
    return out


NO_COLUMNS = tuple(r.key for r in SL.LEDGER if r.is_soa and r.behavior != SL.BEHAVIOR)


def _syn(kw):
    def f(tape):
        return run_day(n_agents=N, seed=1, n_cells=CELLS, ticks=TPD, checkpoint_every=360, budget=float(N),
                       tape_path=tape, **kw)
    return f


@pytest.mark.parametrize("kw", [ALL_ARMS, CLASSICAL_ARMS], ids=["all_arms", "classical"])
def test_t5_perturbing_no_columns_changes_nothing(monkeypatch, tmp_path, kw):
    base, _ = _perturbing_run(monkeypatch, _syn(kw), (), tape=tmp_path / "base")
    shaken, done = _perturbing_run(monkeypatch, _syn(kw), NO_COLUMNS, tape=tmp_path / "shaken")
    assert done["n"] > 100
    assert _observed(shaken, tmp_path / "shaken") == _observed(base, tmp_path / "base")
    # 10e(E1): 既定の final は behavior-hash=no の列を揺らしても動かない
    assert shaken.final_hash == base.final_hash
    # 揺らしは効いていた: 全列のハッシュには no の列が入るので動く(〔改訂(第330・RET)〕前は旧い final の組み立て
    # legacy_combined で見た=切替口と一緒に消したので、SoA の全列のハッシュ agents_hash で見る)
    assert shaken.checkpoints[-1].agents_hash != base.checkpoints[-1].agents_hash
    # 陽性対照: hunger を揺らすと変わる
    pos, _ = _perturbing_run(monkeypatch, _syn(kw), ("agents.hunger",), tape=tmp_path / "pos")
    assert _observed(pos, tmp_path / "pos") != _observed(base, tmp_path / "base")


def test_t5_weight_kg_is_read_only_at_initialization(monkeypatch, tmp_path):
    """``weight_kg`` は behavior(A2 b)だが読むのは初期化だけ=途中で揺らすと behavior-hash だけが動き、
    呼数・行動の件数・prompt_hash は動かない(陽性対照には使えない列=記録 §5)。"""
    base, _ = _perturbing_run(monkeypatch, _syn(ALL_ARMS), (), tape=tmp_path / "b")
    w, _ = _perturbing_run(monkeypatch, _syn(ALL_ARMS), ("agents.weight_kg",), tape=tmp_path / "w")
    ob, ow = _observed(base, tmp_path / "b"), _observed(w, tmp_path / "w")
    assert ow["behavior"] != ob["behavior"]
    assert {k: v for k, v in ow.items() if k != "behavior"} == {k: v for k, v in ob.items() if k != "behavior"}


#: 〔第330・RET〕10e の前の値の表 ``PRE10E_SYN``(HEAD ``66472a0`` の写しで回した final・behavior-hash・呼数)は、旧値を再現する
#: 切替口と一緒に消した(値は 10e の記録 §E1 と §RET に残した)。
#: 今の既定の final(=behavior-hash)の頭 16 桁(段ごとに張り替える)。
CUR_SYN = {
    "v1": "a36995c487c3f214", "v3": "92290af2f272b811", "v2_edge_attention": "863d35e1bfdb55f9",
    "all_arms": "9071edfd618d42d8", "classical": "2297d5c5947551f0",  # 〔2-4 V2〕前 all_arms ab8201f624b4dfa7(近接の既定 distance)
}


@pytest.mark.parametrize("kw", [
    {}, {"vocab_version": "v3"}, {"vocab_version": "v2", "geometry": "edge"}, ALL_ARMS, CLASSICAL_ARMS,
], ids=["v1", "v3", "v2_edge_attention", "all_arms", "classical"])
def test_t1_deleting_the_dead_columns_changes_nothing(request, tmp_path, kw):
    """T1(10e・E1): 死蔵 5 列を消した後の既定の final は behavior-hash そのもの。

    〔改訂(第330・RET)〕前は ``hash_scheme="full"``・``rng_scheme="stateful"`` で 10e の前の final と behavior-hash
    (``PRE10E_SYN``)を再現する形だった(切替口を消した=第330 ACT の commit で 5 構成とも通ったことを記録 §RET に書いた)。
    いまは今の既定の final(``CUR_SYN``)と、K15 の 2 列を消しても final が動かないこと(同じ値)を見る。
    """
    cid = request.node.callspec.id
    new = _syn(kw)(tmp_path / "new")
    assert new.final_hash == new.checkpoints[-1].behavior_hash and new.final_hash[:16] == CUR_SYN[cid]


@real_data
def test_t5_and_t1_on_real_assets(monkeypatch, tmp_path):
    """実資産(W16+W17・計画実行層・エネルギー)300 体 1 日。〔改訂(第330・RET)〕前は plan_activity(K15)も揺らした
    (K15 で消した)。"""
    from shibuya import cli

    def f(tape):
        return cli.run(n_agents=300, seed=1, world_dir=str(WORLD_DIR), tape_path=tape, vocab_version="v3")

    base, _ = _perturbing_run(monkeypatch, f, (), tape=tmp_path / "base")
    shaken, done = _perturbing_run(monkeypatch, f, NO_COLUMNS, tape=tmp_path / "shaken")
    assert done["n"] > 100
    # 実資産のランでは energy_balance・知覚の列も揺らした
    assert {"agents.energy_balance", "perception.heading"} <= done["keys"]
    assert _observed(shaken, tmp_path / "shaken") == _observed(base, tmp_path / "base")
    pos, _ = _perturbing_run(monkeypatch, f, ("agents.hunger",), tape=tmp_path / "pos")
    assert _observed(pos, tmp_path / "pos") != _observed(base, tmp_path / "base")


# ================================================================= 5. 既知の答え: 2 日のラン
@pytest.mark.parametrize("kw", [{}, ALL_ARMS], ids=["default", "all_arms"])
def test_two_day_run_reports_both_hashes_every_day(kw):
    one = run_day(n_agents=N, seed=1, n_cells=CELLS, ticks=TPD, checkpoint_every=360, budget=float(N), **kw)
    two = run_day(n_agents=N, seed=1, n_cells=CELLS, ticks=TPD, sim_days=2, checkpoint_every=360,
                  budget=float(N), **kw)
    assert len(two.checkpoints) == 8
    for c in two.checkpoints:
        assert len(c.behavior_hash) == 64 and len(c.full_hash) == 64
        assert c.behavior_hash == c.combined  # 10e(E1): final は behavior-hash(〔第330・RET〕legacy_combined は消した)
    d1 = [c for c in two.checkpoints if c.tick < TPD]
    d2 = [c for c in two.checkpoints if c.tick >= TPD]
    assert d1[-1].behavior_hash != d2[-1].behavior_hash
    assert d1[-1].full_hash != d2[-1].full_hash
    # 0 日目は 1 日のランと同じ(behavior・full とも)
    assert [c.behavior_hash for c in d1] == [c.behavior_hash for c in one.checkpoints]
    assert [c.full_hash for c in d1] == [c.full_hash for c in one.checkpoints]
    # manifest に最後の checkpoint の値が出る
    m = two.run_manifest_fields()["state_hashes"]
    assert m["behavior_hash"] == d2[-1].behavior_hash and m["full_hash"] == d2[-1].full_hash
    assert m["ledger_version"] == SL.LEDGER_VERSION and m["full_external_bytes"] > 0


def test_hashes_are_deterministic_across_runs():
    a = run_day(n_agents=N, seed=2, n_cells=CELLS, ticks=720, checkpoint_every=360, budget=float(N), **ALL_ARMS)
    b = run_day(n_agents=N, seed=2, n_cells=CELLS, ticks=720, checkpoint_every=360, budget=float(N), **ALL_ARMS)
    assert [(c.combined, c.behavior_hash, c.full_hash) for c in a.checkpoints] == [
        (c.combined, c.behavior_hash, c.full_hash) for c in b.checkpoints]


# ================================================================= 6. 保留の組の発射の tick と call_id(① の前提)
def test_pending_tuple_carries_fire_tick_and_call_id(monkeypatch, tmp_path):
    import pyarrow.parquet as pq

    due_seen: list[tuple] = []
    real_split = RUN._split_due

    def spy(pending, tick):
        due, rest = real_split(pending, tick)
        due_seen.extend((tick, p) for p in due)
        return due, rest

    monkeypatch.setattr(RUN, "_split_due", spy)
    res = run_day(n_agents=N, seed=1, n_cells=CELLS, ticks=TPD, checkpoint_every=360, budget=float(N),
                  tape_path=tmp_path / "tape", vocab_version="v3")
    tape_ids = pq.read_table(tmp_path / "tape" / "calls.parquet").column("call_id").to_pylist()
    assert due_seen and len(due_seen) <= res.llm_calls
    for tick, p in due_seen:
        assert len(p) == 13
        t_apply, cls, agent, fire, cid = p[0], p[1], p[2], p[11], p[12]
        assert fire <= t_apply <= tick  # 適用の時点で発射の tick が引ける
        assert cid == f"{fire}:{agent}:{cls}"
    assert {p[12] for _, p in due_seen} <= set(tape_ids)
    assert len({p[12] for _, p in due_seen}) == len(due_seen)  # 呼ごとに一意


# ================================================================= 7. 親の答え(10b-2)
def test_every_attribute_of_the_owner_classes_is_declared():
    """親の答え 1: 外の状態の持ち主のクラスの属性は、台帳の行か明示の除外の一覧のどちらかに必ず載る。"""
    uncovered, problems = SA.coverage(SRC)
    assert uncovered == {} and problems == []
    kinds = {e.kind for e in SL.EXCLUDED}
    assert kinds <= set(SL.EXCLUDE_KINDS) and all(e.reason for e in SL.EXCLUDED)


def test_coverage_fails_when_a_new_state_is_not_declared(monkeypatch, tmp_path):
    # (a) 除外の一覧から 1 項を外すと「未カバー」が出る
    e0 = next(e for e in SL.EXCLUDED if e.owner == "conv")
    monkeypatch.setattr(SL, "EXCLUDED", tuple(e for e in SL.EXCLUDED if e is not e0))
    uncovered, _ = SA.coverage(SRC)
    assert set(uncovered.get("conv", [])) == set(e0.attrs)
    monkeypatch.undo()
    # (b) クラスに属性を 1 本足すと「未カバー」が出る(写しの src で)
    import shutil

    root = tmp_path / "shibuya"
    shutil.copytree(SRC, root, ignore=shutil.ignore_patterns("__pycache__"))
    fp = root / "engine" / "conversation.py"
    src = fp.read_text(encoding="utf-8")
    anchor = "        self.n_opened = 0\n"
    assert anchor in src
    fp.write_text(src.replace(anchor, anchor + "        self.new_state_10b = 0\n"), encoding="utf-8")
    uncovered, problems = SA.coverage(root)
    # 〔第 6 期 6-4 C1〕電話の会話(持ち主 contact.calls)も同じクラス ConversationManager=どちらの持ち主にも未カバーが出る
    assert uncovered == {"conv": ["new_state_10b"], "contact.calls": ["new_state_10b"],
                         "contact.chats": ["new_state_10b"]} and problems == []  # 〔検収 L1〕チャットも会話の器の子
    # (c) 除外に載せた属性がクラスから消えると「古い除外」
    fp.write_text(src.replace("        self.silence_ticks = int(silence_ticks)\n", ""), encoding="utf-8")
    _, problems = SA.coverage(root)
    assert any("conv.silence_ticks" in v and "古い除外" in v for v in problems), problems


def test_hunger_restore_depends_on_the_configuration():
    """親の答え 6: hunger は構成で軸 2 が変わる(既定=要る・energy のとき=導出できる)。full には入れる。"""
    r = SL.row("agents.hunger")
    assert r.restore == SL.REQUIRED and r.restore_by_config == (("hunger_model=energy", SL.DERIVABLE),)
    assert r.in_full and "hunger" not in SL.full_excluded("agents")
    assert [x.key for x in SL.LEDGER if x.restore_by_config] == ["agents.hunger"]


def test_behavior_hash_includes_the_behavior_rows_of_the_external_state():
    """親の答え 3: behavior-hash に外の状態の軸 1 が behavior の行が入る(no/diag の行は入らない)。"""
    items = SL.behavior_items()
    keys = {k for k, _ in items}
    assert {"O1", "O4", "O7", "O17", "O39", "O42", "O43", "O46", "O74", "O79"} <= keys
    assert not keys & {r.key for r in SL.external_rows() if r.behavior != SL.BEHAVIOR}
    assert all(p not in SL.row(k).hash_skip for k, p in items)


def test_int_table_fast_path_is_canonical():
    """会話の管理の辞書(鍵が整数の組・値が整数)の速い道: 挿入順に依らず、型が混ざれば普通の道に回る。"""
    d1 = {(3, 1): 5, (1, 2): 7, (1, 1): 9}
    d2 = {(1, 1): 9, (3, 1): 5, (1, 2): 7}
    assert SH.to_state(d1) == SH.to_state(d2) and SH.to_state(d1).startswith(b"Q")
    assert SH.to_state({1: 2, 0: 3}) == SH.to_state({0: 3, 1: 2})
    assert SH.to_state({(1, 1): 9}) != SH.to_state({(1, 1): 8})
    assert SH.to_state({(1, 1): True}) != SH.to_state({(1, 1): 1})  # bool は普通の道
    assert not SH.to_state({(1, 1): 1.0}).startswith(b"Q")
    assert not SH.to_state({(1, 1): 2**70}).startswith(b"Q")


def test_memo_does_not_change_the_hashes(all_arms_capture):
    _, c = all_arms_capture
    memo: dict = {}
    f1 = SH.full_hash(c["agents"], c["world"], c["pstate"], c["pop"], c["sched"], c["owners"], memo=memo)
    b1 = SH.behavior_hash(c["agents"], c["world"], c["pop"], c["sched"], "", c["owners"], memo=memo)
    assert memo
    assert f1 == SH.full_hash(c["agents"], c["world"], c["pstate"], c["pop"], c["sched"], c["owners"])
    assert b1 == _beh(c)


@real_data
@pytest.mark.parametrize("kw", [{"vocab_version": "v3"}, dict(ALL_ARMS, home_meal="plan", meal_sleep_defer="on")],
                         ids=["v3_default", "all_arms"])
def test_t7_hash_cost_within_the_declared_cap(kw):
    """T7(10e で門の形を確定・ユーザー決定 10-12=10f のアジェンダ §6-2): **門は checkpoint のハッシュの壁時計が
    シミュ全体の壁時計に占める割合**(``T7_SHARE_CAP``)。宣言値(5,000 体で 1 回の checkpoint の 2 本の合計 ≤ 100 ms)
    は守れたらよい**目標**として併記し、超えたら警告だけ出す(「シミュにかかる時間に影響しないなら上回ってもよい」)。
    checkpoint の時間は今の final の SoA 部分を含めた checkpoint ごとの値(上側に寄せた測り方・検収 4-3)。

    経緯(第321): 全体テストの大きな束の中で all_arms が 1 回だけ宣言の 100 ms を超え、単独では通った(壁時計が
    揺れる)ので、門を宣言の 3 倍(300 ms)にしていた。指示書 10-06 §6 の「つなぎ」で期限を付けることになり、
    10e で門を割合の形に替えた(3 倍の門は消した)。割合は分母も同じ束の中で揺れるので、揺れに強い。
    """
    from shibuya import cli

    res = cli.run(n_agents=5_000, seed=1, world_dir=str(WORLD_DIR), **kw)
    if kw == {"vocab_version": "v3"}:
        if GE.platform_id() in GE.REGISTERED:  # 10f: golden は登録した環境だけ(未登録は警告=黙って通さない)
            assert res.final_hash[:16] == T7_V3_FINAL  # 10e: behavior-hash(10e の前の値 993276d5…)
        else:
            GE.warn_unregistered("T7 の既定 v3 の final")
    assert len(res.checkpoint_seconds) == len(res.checkpoints) == 4
    hashed = float(sum(res.checkpoint_seconds))
    share = hashed / float(res.wall_seconds)
    print(f"\n[T7] checkpoint の合計 {hashed * 1e3:.1f} ms/日・シム日の壁時計 {res.wall_seconds:.1f} s・"
          f"割合 {share:.4%}(門 {T7_SHARE_CAP:.0%})・最大 {max(res.checkpoint_seconds) * 1e3:.1f} ms(目標 "
          f"{T7_TARGET_SECONDS * 1e3:.0f} ms)")
    assert share <= T7_SHARE_CAP, (
        f"checkpoint のハッシュがシミュ全体の壁時計の {share:.3%} を占めた(門 {T7_SHARE_CAP:.0%})",
        res.checkpoint_seconds, res.wall_seconds,
    )
    if max(res.checkpoint_seconds) > T7_TARGET_SECONDS:  # 目標(宣言値)は警告だけ=全体の時間に効かなければ合格
        import warnings

        warnings.warn(f"T7: checkpoint の最大 {max(res.checkpoint_seconds):.4f} s が目標 {T7_TARGET_SECONDS} s を超えた"
                      f"(割合 {share:.3%} は門の中)")


def test_t7_gate_is_the_share_of_the_whole_wall_clock():
    """T7 の門の形の単体: 割合の門は宣言値を超える checkpoint でも、全体に占める割合が小さければ通す。"""
    assert T7_TARGET_SECONDS == 0.100 and 0 < T7_SHARE_CAP <= 0.05
    # 1 回 150 ms(目標超え)× 4 回 / シム日 60 s = 1.0%(門の内側)・1 回 1 s × 4 / 60 s = 6.7%(門の外)
    assert 4 * 0.150 / 60.0 <= T7_SHARE_CAP < 4 * 1.0 / 60.0


# ================================================================= 8. 検収後の直し(10b-3)
def test_p1_ordered_rows_keep_the_insertion_order():
    """検収 2-1: 順序が挙動を決める行(O8 要旨の並び・O39 会話の管理)は辞書の挿入順を保つ。"""
    from collections import OrderedDict

    # 〔第 6 期 6-4 C1〕チャットの会話の状態 CT1C と電話の会話 CT1K(O39 と同じ形)も順を保つ
    assert {r.key for r in SL.external_rows() if r.ordered} == {"O8", "O39", "CT1C", "CT1K"}
    a = {7: OrderedDict([(1, None), (2, None)])}
    b = {7: OrderedDict([(2, None), (1, None)])}
    assert SH.to_state(a) != SH.to_state(b)  # OrderedDict は印が無くても順を保つ
    assert SH.to_state({1: "x", 2: "y"}) == SH.to_state({2: "y", 1: "x"})  # 印の無い dict は順に依らない
    assert SH.to_state({1: "x", 2: "y"}, ordered=True) != SH.to_state({2: "y", 1: "x"}, ordered=True)
    assert SH.to_state({1: 5, 2: 6}, ordered=True) != SH.to_state({2: 6, 1: 5}, ordered=True)  # 速い道も


def test_p1_full_hash_sees_the_order_of_ordered_rows(all_arms_capture):
    _, c = all_arms_capture
    o = c["owners"]
    base = _full(c)
    # O39: 印つきの行の普通の dict(会話の管理の辞書)の並びを逆にすると full が動く
    conv = o["conv"]
    # 10e(E2): 期限の切れた項は tick ごとに落とすので、checkpoint の時点で生きた項が 2 件あるとは限らない。
    # 期限の遠い控えを 2 件足してから並びを逆にする(足した状態を基準に取り直す)
    big = 10**9
    conv._refusal_until[(big, big + 1)] = big
    conv._refusal_until[(big + 2, big + 3)] = big
    base_probe = _full(c)
    saved = dict(conv._refusal_until)
    assert len(saved) >= 2
    conv._refusal_until.clear()
    conv._refusal_until.update(reversed(list(saved.items())))
    try:
        assert _full(c) != base_probe
    finally:
        conv._refusal_until.clear()
        conv._refusal_until.update(saved)
        del conv._refusal_until[(big, big + 1)], conv._refusal_until[(big + 2, big + 3)]
    assert _full(c) == base
    # O8: 要旨の並び(OrderedDict・popitem(last=False) で古い順に落とす)
    # (100 体 1 日では要旨が 2 行以上の体がいないので、2 行の並びを 1 つ足して入れ替える)
    from collections import OrderedDict

    mem = o["mem_layer"]
    probe = 10**6
    mem._gist_order[probe] = OrderedDict([(1, None), (2, None)])
    try:
        with_12 = _full(c)
        mem._gist_order[probe].move_to_end(1)
        assert _full(c) != with_12
    finally:
        del mem._gist_order[probe]
    assert _full(c) == base


def test_p4_numpy_integers_take_the_same_bytes_as_python_ints():
    """検収 2-4: 速い道は Python の int と numpy の整数を同じに扱う。"""
    assert SH.to_state({1: 2}) == SH.to_state({np.int64(1): np.int64(2)})
    assert SH.to_state({(1, 2): 5, (0, 3): 7}) == SH.to_state({(1, 2): np.int64(5), (np.int32(0), 3): 7})
    assert SH.to_state({1: 2}).startswith(b"Q") and SH.to_state({np.int64(1): np.int64(2)}).startswith(b"Q")
    assert not SH.to_state({1: np.bool_(True)}).startswith(b"Q")
    assert not SH.to_state({1: np.uint64(2**63)}).startswith(b"Q")  # int64 に収まらない=普通の道


def _scan_one(tmp_path, code: str, names=("rel_last",)):
    fp = tmp_path / "engine" / "fake.py"
    fp.parent.mkdir(exist_ok=True)
    fp.write_text(code, encoding="utf-8")
    res = SA.scan(tmp_path, files=[fp], names=set(names))
    return res, SA.check(res, [SL.row("agents.rel_last")], unresolved_allow=(), check_declared=False)


@pytest.mark.parametrize("code,expect", [
    ("NAMES = ('rel_last',)\n\ndef f(reg):\n    for n in NAMES:\n        getattr(reg, n)\n", "read"),
    ("def f(reg, n):\n    return getattr(reg, n)\n", "unresolved"),
    ("def f(reg):\n    return reg.arrays.get('rel_last')\n", "read"),
    ("import operator\n\ndef f(reg):\n    return operator.attrgetter('rel_last')(reg)\n", "read"),
    ("def f(reg, a):\n    reg.money[a], reg.rel_last[a] = reg.money[a] - reg.rel_last[a], 0\n", "read"),
], ids=["getattr_name_table", "getattr_arg", "arrays_get", "attrgetter", "tuple_assign"])
def test_p5_ast_blind_spots_are_caught(tmp_path, code, expect):
    """検収 2-5 の表の 5 つの書き方をそのまま: どれも捕まる(読みとして数える/解決できない読み)。"""
    res, out = _scan_one(tmp_path, code)
    if expect == "read":
        assert res.loose["rel_last"], code
        assert any(v.startswith("agents.rel_last:") for v in out), out
    else:
        assert res.unresolved and any("解決できない動的な読み" in v for v in out), out


@pytest.mark.parametrize("code", [
    "def f(reg, a):\n    reg.rel_last[a] = reg.rel_last[a] + 1\n",
    "def f(reg, a):\n    reg.rel_last[a] += 1\n",
    "def f(reg, a):\n    reg.rel_last[a], reg.money[a] = reg.rel_last[a] + 1, 0\n",
    "def f(reg, a):\n    reg.rel_last[reg.rel_last > 3] = 0\n",
], ids=["assign", "augassign", "tuple_pair_same_column", "slice_of_same_target"])
def test_p5_true_self_updates_are_still_not_reads(tmp_path, code):
    res, out = _scan_one(tmp_path, code)
    assert not res.loose["rel_last"] and out == [], (code, out)


@pytest.fixture(scope="module")
def runtime_owners():
    """小さなラン(合成の全腕・古典、実資産 200 体の v3 既定と全腕+古典)の最後の checkpoint の owners。"""
    from shibuya import cli

    runs = {
        "syn_all": lambda: run_day(n_agents=60, seed=1, n_cells=CELLS, ticks=400, budget=60.0, **ALL_ARMS),
        "syn_classical": lambda: run_day(n_agents=60, seed=1, n_cells=CELLS, ticks=400, budget=60.0,
                                         **CLASSICAL_ARMS),
    }
    if (WORLD_DIR / "w17_schedule.parquet").exists():
        runs["real_v3"] = lambda: cli.run(n_agents=200, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3")
        runs["real_all"] = lambda: cli.run(n_agents=200, seed=1, world_dir=str(WORLD_DIR), **CLASSICAL_ARMS,
                                           home_meal="plan", meal_sleep_defer="on")
    out = {}
    mp = pytest.MonkeyPatch()
    try:
        for name, f in runs.items():
            with _spy_hash_inputs(mp) as seen:
                f()
            out[name] = seen[-1]["owners"]
            mp.undo()
    finally:
        mp.undo()
    return out


def test_p6_runtime_owner_instances_are_fully_declared(runtime_owners):
    """検収 2-6: 実行時のインスタンスの ``vars()`` を台帳+除外の一覧に突き合わせる(子クラス・入れ替わるクラスも)。"""
    assert len(runtime_owners) >= 2
    for name, owners in runtime_owners.items():
        assert SA.runtime_uncovered(owners) == {}, name
    if "real_v3" in runtime_owners:
        # 子クラス(cli._HouseholdWalletLedger)と別のクラス(NearestChooser)が実際に入っていることも確かめる
        o = runtime_owners["real_v3"]
        assert type(o["ledger"].money).__name__ == "_HouseholdWalletLedger"
        assert type(o["poi_resolver"].chooser).__name__ == "NearestChooser"


def test_p6_runtime_check_catches_an_undeclared_attribute(runtime_owners):
    owners = runtime_owners["syn_all"]
    conv = owners["conv"]
    conv.new_state_10b = 1
    try:
        assert SA.runtime_uncovered(owners) == {"conv": ["new_state_10b"]}
    finally:
        del conv.new_state_10b


def test_p2_end_of_day_hashes_are_reported_separately():
    """検収 2-2: 日の締めの後の 2 本を manifest の ``state_hashes_end_of_day`` に別に出す(台帳の無いランは
    最後の checkpoint と同じ値・final と checkpoint の位置は変えない)。"""
    r = run_day(n_agents=N, seed=1, n_cells=CELLS, ticks=TPD, checkpoint_every=360, budget=float(N), **ALL_ARMS)
    e = r.state_hashes_end_of_day
    assert (e["behavior_hash"], e["full_hash"]) == (r.checkpoints[-1].behavior_hash, r.checkpoints[-1].full_hash)
    assert r.run_manifest_fields()["state_hashes_end_of_day"] == e
    assert [c.tick for c in r.checkpoints] == [359, 719, 1079, 1439]


@real_data
def test_p2_end_of_day_differs_after_the_ledger_close():
    from shibuya import cli

    r = cli.run(n_agents=200, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3")
    r2 = cli.run(n_agents=200, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3")
    e = r.state_hashes_end_of_day
    assert e == r2.state_hashes_end_of_day  # 決定論
    # 台帳の日番号・当日の売れ行き・センサスの項が締めで書き換わる=最後の checkpoint と違う
    assert e["full_hash"] != r.checkpoints[-1].full_hash
    assert e["behavior_hash"] != r.checkpoints[-1].behavior_hash
    assert r.final_hash == r2.final_hash


def _call_ref_sites() -> dict[tuple[str, int], str]:
    """``*_call_ref(`` の行(ファイル・行)→ 道の名。1-0: HEAD の run_day の 5 か所は 3 つの系の関数へ移った
    (到着の受け取り ``llm_io.receive_arrivals``・呼 ``decide.sys_decide``・ランの終わり ``run_end.sys_drain``)。"""
    import inspect

    from shibuya.engine.systems import decide as DEC
    from shibuya.engine.systems import llm_io as LIO
    from shibuya.engine.systems import run_end as RE

    lines: list[tuple[str, int]] = []
    for fn in (LIO.receive_arrivals, DEC.sys_decide, RE.sys_drain):
        src, start = inspect.getsourcelines(fn)
        path = inspect.getsourcefile(fn)
        lines += [(path, start + i) for i, ln in enumerate(src) if "*_call_ref(" in ln]
    assert len(lines) == 5, lines
    # 出現順: 再生の到着(④′-r)・艦隊の到着(④′)・mock(④)・艦隊の終端の drain・再生の終端
    return dict(zip(lines, ("replay_arrival", "fleet_arrival", "mock", "fleet_drain", "replay_end")))


def test_t2_call_id_on_the_fleet_and_replay_paths(tmp_path, monkeypatch):
    """検収 4-2: 艦隊の到着・艦隊の終端の drain・再生の到着・再生の終端の 4 つの道でも、保留の組は 13 要素・
    call_id は ``発射:体:級``・発射 ≤ 適用。艦隊の結果が持つ ``call_id`` と式の値も一致する。"""
    import sys

    from tests.engine.test_tape_deferred import BoomLLM, common, make_client
    from tests.llm.test_fleet import FakeVLLM

    sites = _call_ref_sites()
    seen_paths: set[str] = set()
    n_fleet_ids = {"n": 0}
    real_ref = RUN._call_ref
    real_split = RUN._split_due

    def ref_spy(res):
        fr = sys._getframe(1)
        line, path = fr.f_lineno, fr.f_code.co_filename
        cand = [k for k in sites if k[0] == path and k[1] <= line]  # 呼び手の行のいちばん近い手前の印の行=その道
        seen_paths.add(sites[max(cand, key=lambda k: k[1])] if cand else "?")
        out = real_ref(res)
        cid = getattr(res, "call_id", "")
        if cid:
            n_fleet_ids["n"] += 1
            assert cid == out[1], (cid, out)
        return out

    def split_spy(pending, tick):
        due, rest = real_split(pending, tick)
        for p in due:
            assert len(p) == 13 and p[11] <= p[0] <= tick and p[12] == f"{p[11]}:{p[2]}:{p[1]}", p
        return due, rest

    monkeypatch.setattr(RUN, "_call_ref", ref_spy)
    monkeypatch.setattr(RUN, "_split_due", split_spy)
    servers = [FakeVLLM(), FakeVLLM()]
    try:
        for srv in servers:
            srv.total_delay_s = 0.05
        # (a) 艦隊: 待ち 2 s で次 tick に届く(到着の道)
        run_day(fleet=make_client(servers, per_replica_in_flight=4, queue_capacity=8), tape_path=tmp_path / "a",
                fleet_wait_s=2.0, budget=30.0, **common(20))
        # (b) 艦隊: 待ち 0 で遅らせる=ラン終端の drain に残る
        for srv in servers:
            srv.total_delay_s = 0.5
        rec = run_day(fleet=make_client(servers), tape_path=tmp_path / "b", fleet_wait_s=0.0, budget=30.0,
                      **common(6))
        assert rec.fleet_drained_at_end > 0
    finally:
        for s in servers:
            s.close()
    # (c) 再生: 到着(テープの観測 tick)と終端(ループ中に届かなかった分)
    run_day(mode="replay", replay=tmp_path / "a", llm=BoomLLM(), budget=30.0, **common(20))
    rep = run_day(mode="replay", replay=tmp_path / "b", llm=BoomLLM(), budget=30.0, **common(6))
    assert rep.fleet_drained_at_end > 0
    assert {"fleet_arrival", "fleet_drain", "replay_arrival", "replay_end"} <= seen_paths, seen_paths
    assert n_fleet_ids["n"] > 0  # 艦隊の結果の call_id と式の値を突き合わせた
