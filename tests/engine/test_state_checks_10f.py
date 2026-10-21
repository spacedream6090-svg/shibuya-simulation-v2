"""10f 第 3 段: AST と実行時の検査(K24 (a))・K19 の検査(K25 (a))。

既知の答え(アジェンダ §4 の T4・T5):

- T4 軸 1(AST): 外の状態の軸 1 が no/diag の属性を、持ち主の外の挙動の場所で読むと落ちる(わざと書いた断片)。
  今の src は通る(診断の出口・``result.…`` の組み立て・名前の衝突・理由つきの許可だけ)。
- T4 軸 2(実行時「捨てて同じか」): 軸 2 が discardable の属性をランの頭の値に戻しても、以後の checkpoint・呼数・
  診断の行・日の締めが通しと同じ。わざと required を discardable にすると落ちる(10d の 14 項目の ``conv.n_opened``)。
- T5 K19: 実行時の計器(合成世界・率 ×1000・2 日)で、実際のブロックの重なりと「1 語目に値・2 ブロック以上」の用途名が
  許可の表の中だけ。静的に安全な 15 か所は固定・決まらない 16 か所の一覧が増えたら落ちる。わざと 5 語目を引く呼び手を
  足すと落ちる(静的にも実行時にも)。
"""

from __future__ import annotations

import dataclasses
import textwrap
from pathlib import Path

import pytest

from shibuya import cli
from shibuya.engine import rng_audit as RA
from shibuya.engine import state_ledger as SL
from shibuya.engine import state_ledger_ast as SA
from shibuya.engine.run import run_day
from tests.engine import discard_probe as DP
from tests.engine.test_sim_time_T import ALL_ARMS

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "shibuya"
WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
TPD = 1_440
#: 10e(E4): 既定 v3・5,000 体・seed 1・1 日の final(乱数 counter・K19 の鍵の並べ方)。
#: 〔改訂(第330)〕10e 構築側(第330 B3 丸め・B4 W10 ON+Q7・B5 W13 の年間化)で世界の資産が動いた。E5 の値は 4fbf61616af1e3d2。
#: 〔改訂(第330・ACT)〕版上げ 1 回目の活性化(暦の一本化・開始日 2026-07-13・影 6 日)で動いた。B6build の値は 0483d1165e245bed。
K19_V3_FINAL_COUNTER = "bb86f89855172717"  # 〔第 4 期 4-3 段 10・版上げ 3 回目〕差し替えの世界で動いた(前 333b1820f7849b00=記録 pop43)  # 〔小さな版上げ・meal_w17〕前 b8eadcb51e8705e7(--meal-default validation で戻る)  # 〔第 4 期 4-2〕給与の天引きと預かり消費税で動いた(前 eb759bb4e5be37ec=SHIBUYA_RULES_42=off で戻る・記録 rules42)
# 〔第 4 期 4-3 版上げ 3 回目の第 2 部〕旧値の腕 --meal-default validation の final の定数 _K19_PRE_MEAL_W17(最後の値 5b080133301bf13d=差し替えの世界・前 b8eadcb51e8705e7=W16 の世界)は切替口と一緒に消した(再現は安定版のタグ stable-v2-before-meal-default-w17)


# ================================================================= K24 軸 1(AST)
@pytest.fixture(scope="module")
def ext_scan():
    return SA.scan_external(SRC)


def test_external_axis1_ast_passes_on_src(ext_scan):
    problems = SA.check_external(ext_scan)
    assert problems == [], "\n".join(problems)
    # 規則の内訳(診断の出口・結果の組み立て・名前の衝突)が実際に働いている
    reasons = [SA.ext_reason(s, ext_scan) for v in ext_scan.sites.values() for s in v]
    assert {"exit", "result", "collision"} <= set(reasons)
    assert len(SA.EXT_NAME_COLLISIONS) == len(ext_scan.collisions) >= 15


def test_external_axis1_tables_have_reasons():
    for e in SA.EXT_AST_ALLOW:
        assert e.allow.reason and e.allow.contains and e.allow.path and e.count >= 1, e.attr
    for d in SA.DIAG_EXITS:
        assert d.reason, d
    # 許可の属性はどれも軸 1 が no/diag の行の属性
    rows = SA.ext_attr_rows()
    for e in SA.EXT_AST_ALLOW:
        assert all(b != SL.BEHAVIOR for _o, _k, b in rows[e.attr]), e.attr


def _fake_tree(tmp_path: Path, files: dict[str, str]) -> tuple[Path, list[Path]]:
    root = tmp_path / "src" / "shibuya"
    out = []
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text), encoding="utf-8")
        out.append(p)
    return root, out


def test_t4_axis1_reading_a_no_attribute_in_a_behavior_place_fails(tmp_path, ext_scan):
    """T4 軸 1: 実物の src に「挙動の場所で no/diag の属性を読む」断片を 1 つ足すと落ちる。"""
    import shutil

    root = tmp_path / "src" / "shibuya"
    shutil.copytree(SRC, root, ignore=shutil.ignore_patterns("build", "__pycache__"))
    # O66 の act_layer.n_wander_bad(diag・計数)を、挙動の分岐(歩き先を選ぶ関数)で読む
    p = root / "engine" / "processes" / "fake_behavior.py"
    p.write_text(textwrap.dedent('''
        def choose_next(act_layer, agents):
            if act_layer.n_wander_bad > 3:
                return 0
            return getattr(act_layer, "n_set", 0)
    '''), encoding="utf-8")
    sc = SA.scan_external(root)
    problems = SA.check_external(sc)
    assert len(problems) == 2, problems
    assert all("fake_behavior.py" in x for x in problems)
    assert any("n_wander_bad" in x and "O66" in x for x in problems)
    # 同じ読みを run.py の結果の組み立て(result.… への代入)に置けば落ちない=出口
    p.write_text(textwrap.dedent('''
        def report(act_layer, result):
            result.wander_bad = int(act_layer.n_wander_bad)
    '''), encoding="utf-8")
    sc2 = SA.scan_external(root)
    assert any("fake_behavior.py" in str(s) for s in sc2.sites["n_wander_bad"])
    assert len(SA.check_external(sc2)) == 1  # 結果の組み立ての置き場(RESULT_FILES)の外の result.… は出口ではない
    assert "engine/processes/fake_behavior.py" not in SA.RESULT_FILES


def test_t4_axis1_collision_needs_the_owner_receiver(tmp_path):
    """名前の衝突は受け手が持ち主を指さないときだけ許す(持ち主の名前で読めば落ちる)。"""
    import shutil

    root = tmp_path / "src" / "shibuya"
    shutil.copytree(SRC, root, ignore=shutil.ignore_patterns("build", "__pycache__"))
    p = root / "engine" / "fake_collision.py"
    # n_calls は ArbiterDecision・MockLLM も持つ=受け手が decision なら衝突として許す・arbiter なら落とす
    p.write_text("def f(decision, arbiter):\n    a = decision.n_calls\n    return arbiter.n_calls_total + a\n",
                 encoding="utf-8")
    problems = SA.check_external(SA.scan_external(root))
    assert len(problems) == 1 and "n_calls_total" in problems[0], problems
    # 限界(検収 U6・README に明記): 衝突の属性を、持ち主と違う名前の受け手で読むと見えない。持ち主の名前なら落ちる
    p.write_text("def f(conv_mgr, conv):\n    a = conv_mgr.n_blocks > 3\n    return a, conv.n_blocks\n",
                 encoding="utf-8")
    problems = SA.check_external(SA.scan_external(root))
    assert len(problems) == 1 and "fake_collision.py:3" in problems[0], problems  # 2 行目(conv_mgr)は見えない


def test_u5_allow_entries_have_a_fixed_hit_count(tmp_path, ext_scan):
    """U5: 場所ごとの許可は当たる数を固定する。数を変えた宣言と、許可した行を挙動の場所に写した src で落ちる。"""
    import dataclasses as dc
    import shutil

    wrong = tuple(dc.replace(e, count=e.count + 1) if e.attr == "seconds" else e for e in SA.EXT_AST_ALLOW)
    assert any("当たる数が 1(宣言は 2)" in x for x in SA.check_external(ext_scan, allow=wrong))
    root = tmp_path / "src" / "shibuya"
    shutil.copytree(SRC, root, ignore=shutil.ignore_patterns("build", "__pycache__"))
    run_py = root / "engine" / "systems" / "body.py"  # 1-0: 層別の起床の数えは系 presence(engine/systems/body.py)
    text = run_py.read_text(encoding="utf-8")
    # 許可した行(層別の起床の数えの基準)と同じ文字列の行を、同じファイルの別の関数に足す
    run_py.write_text(text + "\n\ndef _copied(presence):\n    _pres0 = int(presence.n_arrivals) + 1\n    return _pres0\n",
                      encoding="utf-8")
    problems = SA.check_external(SA.scan_external(root))
    assert any("当たる数が 2(宣言は 1)" in x and "n_arrivals" in x for x in problems), problems


def test_v3_allow_entries_pin_the_function_of_the_line(tmp_path, ext_scan):
    """10e(E2・10f 第 3 段の検収 V3): 許可した行を別の関数へ**移す**(数は同じ)と、関数の名前で落ちる。"""
    import dataclasses as dc
    import shutil

    assert all(len(e.funcs) == e.count for e in SA.EXT_AST_ALLOW)
    wrong = tuple(dc.replace(e, funcs=("other",)) if e.attr == "seconds" else e for e in SA.EXT_AST_ALLOW)
    assert any("当たる行の関数" in x and "seconds" in x for x in SA.check_external(ext_scan, allow=wrong))
    root = tmp_path / "src" / "shibuya"
    shutil.copytree(SRC, root, ignore=shutil.ignore_patterns("build", "__pycache__"))
    clock = root / "engine" / "clock.py"
    text = clock.read_text(encoding="utf-8")
    assert text.count("delta.seconds") == 1
    # 許可した行(timedelta.seconds)の式を元の関数から消し、同じ式を別の関数(挙動の場所のつもり)へ移す
    moved = text.replace("delta.seconds", "0") + "\n\ndef _moved(delta):\n    return delta.seconds\n"
    clock.write_text(moved, encoding="utf-8")
    problems = SA.check_external(SA.scan_external(root))
    assert any("当たる行の関数" in x and "_moved" in x for x in problems), problems


def test_axis1_stale_allow_and_collision_entries_fail(ext_scan):
    stale = SA.EXT_AST_ALLOW + (SA.ExtAllow("n_set", 1, SL.AstAllow("engine/run.py", "no such text", "古い")),)
    assert any("古い許可" in x for x in SA.check_external(ext_scan, allow=stale))
    coll = dict(SA.EXT_NAME_COLLISIONS, n_set="衝突は無い")
    assert any("衝突が無い" in x for x in SA.check_external(ext_scan, collisions_allow=coll))
    coll2 = {k: v for k, v in SA.EXT_NAME_COLLISIONS.items() if k != "tick"}
    assert any("tick" in x and "理由" in x for x in SA.check_external(ext_scan, collisions_allow=coll2))


# ================================================================= K24 軸 2(実行時「捨てて同じか」)
SYN_KW = dict(n_agents=100, seed=1, n_cells=16, ticks=TPD, sim_days=2, budget=100.0, checkpoint_every=1, **ALL_ARMS)


@pytest.fixture(scope="module")
def syn_straight():
    return run_day(**SYN_KW)


def _probe(monkeypatch, kw, T, paths=None, runner=run_day):
    rep = DP.install(monkeypatch, T, paths)
    try:
        res = runner(**kw)
    finally:
        monkeypatch.undo()
    return rep, res


@pytest.mark.parametrize("T", (420, 1320, 1439, 1441, 1860))
def test_axis2_discardable_reset_keeps_the_run_synthetic(syn_straight, monkeypatch, T):
    rep, res = _probe(monkeypatch, SYN_KW, T)
    assert rep.fired and len(rep.reset) >= 150 and rep.no_snapshot == []
    assert DP.differences(syn_straight, res, T) == {}, (T, DP.differences(syn_straight, res, T))


def test_t4_axis2_required_made_discardable_fails(syn_straight, monkeypatch):
    """T4 軸 2: O91 の ``conv.n_opened``(10d で再開の試験が見つけた 14 項目の 1 つ・記憶の層が読む)を、わざと
    discardable にした台帳で通しと「捨てて」を回すと、checkpoint・診断の行・日の締めが食い違う。

    〔第337〕既定の食事時刻を体ごとに引く形(meal_w17)で合成の世界の一斉の起床が消え、750 までに開く会話が 0 になった
    (O91 は 0 のまま=差が出ない)ので、両方の腕で会話の開いた刻み 2,007 より後の 2,100 で捨てる(前は 750)。"""
    T = 2_100
    row = SL.row("O91")
    flipped = tuple(dataclasses.replace(r, restore=SL.DISCARDABLE) if r.key == "O91" else r for r in SL.LEDGER)
    monkeypatch.setattr(SL, "LEDGER", flipped)
    assert "conv.n_opened" in DP.discardable_paths() and row.restore == SL.REQUIRED
    straight = run_day(**SYN_KW)  # 同じ(わざと誤った)台帳で通し
    rep = DP.install(monkeypatch, T)
    probed = run_day(**SYN_KW)
    monkeypatch.undo()
    assert "conv.n_opened" in rep.reset
    diff = DP.differences(straight, probed, T)
    assert diff and "first_checkpoint" in diff and "daily" in diff, diff
    # 属性そのもののハッシュだけでなく挙動(final=combined)も後で食い違う
    a, b = DP.hashes(straight, T), DP.hashes(probed, T)
    assert any(x[1] != y[1] for x, y in zip(a, b))


@real_data
@pytest.mark.parametrize("arms,T", [
    (dict(), 750),
    (dict(memory="on", relations="on", policy="classical", chooser="classical"), 1320),
], ids=["v3_default", "classical_mem_rel"])
def test_axis2_discardable_reset_keeps_the_run_world(monkeypatch, arms, T):
    kw = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", activity=True,
              checkpoint_every=1, **arms)
    straight = cli.run(**kw)
    rep, res = _probe(monkeypatch, kw, T, runner=cli.run)
    assert rep.fired and rep.no_snapshot == []
    assert DP.differences(straight, res, T) == {}


@real_data
def test_t4_axis2_ledger_snap_made_discardable_fails_world(monkeypatch):
    """T4 軸 2 の 2 例目(世界資産・金の台帳): O92 の ``ledger.money._snap``(日の締めの基準)を 2 日目の途中で捨てると、
    2 日目の締めのセンサスが食い違う。0 日目の途中では基準がランの頭の値のまま=捨てても同じ(戻す値と同じ)なので
    2 日目で見る。"""
    kw = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", activity=True,
              checkpoint_every=1)
    straight = cli.run(**kw)
    rep, res = _probe(monkeypatch, kw, 1860, DP.discardable_paths() + ("ledger.money._snap",), runner=cli.run)
    assert "ledger.money._snap" in rep.reset
    assert "daily" in DP.differences(straight, res, 1860)


def _flip(monkeypatch, key: str) -> None:
    """台帳の行 ``key`` の軸 2 を、わざと discardable にする(通しと「捨てて」の両方に同じ台帳を使う)。"""
    flipped = tuple(dataclasses.replace(r, restore=SL.DISCARDABLE) if r.key == key else r for r in SL.LEDGER)
    monkeypatch.setattr(SL, "LEDGER", flipped)


def test_u7_ipf_cache_with_a_multiplier_is_caught(monkeypatch):
    """U7: O90 ``classical._ipf_cache`` は乗数が全部 1 の classical では使われない(10d の記録・検収で捕まらなかった)。
    乗数を 1.5 にした classical の腕で、わざと discardable にした台帳で帯の途中(T=757)に捨てると、behavior-hash と
    日の締めが食い違って落ちる。final と呼数は同じ(合成世界 100 体では、帯の途中で作り直した c_t が同じ値になる=
    軸 1 が behavior の行なので、属性そのもののハッシュで捕まる)。"""
    import numpy as np

    from shibuya.engine import classical as CL

    orig_bind = CL.ClassicalPolicy.bind

    def bind(self, *a, **k):
        orig_bind(self, *a, **k)
        self.m_next = np.full_like(self.m_next, 1.5)
        self._identity = False

    monkeypatch.setattr(CL.ClassicalPolicy, "bind", bind)
    _flip(monkeypatch, "O90")
    kw = dict(SYN_KW, policy="classical", chooser="classical")
    straight = run_day(**kw)
    rep = DP.install(monkeypatch, 757)
    probed = run_day(**kw)
    monkeypatch.undo()
    assert "classical._ipf_cache" in rep.reset
    diff = DP.differences(straight, probed, 757)
    assert diff.get("first_checkpoint", {}).get("behavior") and "daily" in diff, diff


@real_data
def test_u7_pulled_in_today_is_outside_this_check(monkeypatch):
    """U7: O37 ``presence._pulled_in_today``(軸 1 diag)は、わざと discardable にして日の境目の直後(T=1441)に捨てても
    食い違わない=この検査の外。読み手は到着の飛ばしの内訳の計数(O70・discardable)だけで、挙動・呼数・診断の行・
    日の締めのどれにも出ない。discardable にすると full-hash からも外れる。日の途中の再開で要ることは、再開の試験
    (10d・full-hash に入る)が見る。"""
    _flip(monkeypatch, "O37")
    kw = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", activity=True,
              checkpoint_every=1)
    straight = cli.run(**kw)
    rep = DP.install(monkeypatch, 1441)
    probed = cli.run(**kw)
    monkeypatch.undo()
    assert "presence._pulled_in_today" in rep.reset
    assert DP.differences(straight, probed, 1441) == {}


# ================================================================= K25: K19 の検査(静的)
def test_k19_static_sites_are_frozen():
    sites = RA.scan_sites(SRC)
    assert RA.check_sites(sites) == []
    # 〔第330・10e B6〕SAFE_SITES に天気の規則 calendar の再生日の抽選(sample_calendar_day)を足して 15 → 16
    # 〔改訂(第330・RET)〕legacy の天気の 2 か所(_pick_day・select_day)を消して 16 → 14・stateful の Generator の
    # 4 か所(salient と dispatch の __init__・relay_day)を消して決まらない呼び手 16 → 12
    # 〔第 1 期 1-8 J0〕候補の口の提示の並べ替え(present_rng=permutation(候補の数))を決まらない呼び手に足して 12 → 13
    #(古典の方策の抽選の場所は render から answer へ移っただけ=SAFE_SITES の数は同じ)
    # 〔第 2 期 2-2 段 11a〕知人に気づく抽選(ProximityRule.notice_u=k19 の並べ方・1 語)を SAFE_SITES に足して 14 → 15
    # 〔第 6 期 6-5〕忘れる速さの人ごとのばらつき(forgetting_scale=k19 の並べ方・2 語)を足して 15 → 16
    # 〔第 6 期 6-3 T2〕会話の時計の人ごとの話す速さ(person_mora_len_s)と発言ごとの揺れ(utterance_jitter)=k19 の並べ方・
    # どちらも一様 1 語を足して 16 → 18
    # 〔賃金の小さな版上げ〕賃金の分位(core/wage_formula.py の wage_uniform=k19 の並べ方・1 語)を足して 18 → 19
    # 〔第 6 期 6-4 C1〕最初の道具の状態(Devices.__init__)と連絡の判断の仮のモデルの選び(ContactPort._draw)を足して 19 → 21・
    # 連絡の判断の候補の提示の並べ替え(ContactPort.choose=permutation)を決まらない呼び手に 13 → 14
    # 〔小さな版上げ・meal_w17〕既定の食事時刻の引き(MealStartDistribution.draw=k19 の並べ方・3 語)を足して 21 → 22
    # 〔第 6 期 6-2 カレンダー 2〕予定の判断の仮のモデルの選び(Calendar2Port._draw)を足して 22 → 23・候補の提示の並べ替え
    # (Calendar2Port.choose=permutation)を決まらない呼び手に 14 → 15
    assert len(RA.SAFE_SITES) == 23 and len(RA.UNDETERMINED_SITES) == 15
    # httpx の client.stream(llm/fleet.py)は乱数ではない=一覧に入らない
    assert all(s.path != "llm/fleet.py" for s in sites)


def test_t5_static_fifth_word_caller_fails(tmp_path):
    root, files = _fake_tree(tmp_path, {
        "engine/fake.py": '''
            from shibuya.core.rng import stream
            from shibuya.core import rng as R

            def five(seed, agent, tick):
                return stream(seed, "test.fifth_word", agent, tick).random(5)

            def dynamic(seed, agent, n):
                g = R.stream(seed, "test.dynamic", agent)
                return g.random(n)

            def four(seed, agent):
                return stream(seed, "test.four", agent).random((2, 2))
        ''',
    })
    sites = RA.scan_sites(root, files)
    by = {s.domain: s.verdict for s in sites}
    assert by == {"test.fifth_word": RA.OVER_STATIC, "test.dynamic": RA.UNDETERMINED, "test.four": RA.SAFE_STATIC}
    problems = RA.check_sites(sites, safe=frozenset({("engine/fake.py", "four", "test.four")}), undetermined={})
    assert len(problems) == 2
    assert any("4 語を超えて" in x and "test.fifth_word" in x for x in problems)
    assert any("決まらない呼び手が増えた" in x and "test.dynamic" in x for x in problems)


# ================================================================= K25: K19 の検査(実行時)
def _record(kw, runner=run_day, extra=None):
    with RA.StreamRecorder() as rec:
        res = runner(**kw)
        if extra is not None:
            extra()
    return rec.analyze(), res


SYN1000 = dict(n_agents=200, seed=1, n_cells=25, ticks=TPD, sim_days=2, budget=100.0, checkpoint_every=360,
               salient_rate_per_10k=3000.0, **ALL_ARMS)


@pytest.fixture(scope="module")
def k19_runs():
    """合成世界・率 ×1000・2 日(counter)。〔改訂(第330・RET)〕前は stateful(旧値の再現の切替口)とも比べた(消した)。"""
    return {"counter": _record(dict(SYN1000))}


def test_k19_runtime_overlaps_only_in_the_allow_list(k19_runs):
    """10e(E4): counter では実際の重なりが 0(許可の表に ``overlap`` は無い)。〔改訂(第330・RET)〕扱い ``stateful`` の
    用途名(stateful のランでだけ重なりを許した 8 本)は切替口と一緒に消した=許可の表は空。"""
    st, res = k19_runs["counter"]
    assert RA.check_overlaps(st) == []
    ov = {d for d, s in st.items() if s.actual_overlaps}
    assert ov == set()  # 鍵の 0 語目を空けた=隣が無い
    assert st["world.salient.counter"].keyed is False and st["perception.p_notice"].keyed is False
    assert st["world.delivery_inbound"].keyed is False
    assert not ({"world.salient", "world.public_service_dispatch"} & set(st))  # 日の頭の Generator は作らない
    assert RA.K19_ALLOW == {} and not hasattr(RA, "STATEFUL_ONLY") and not hasattr(RA, "OVERLAP")
    # 計器は結果を変えない(包まないランと同じ final)
    assert run_day(**dict(SYN1000)).final_hash == res.final_hash


def test_k19_empty_allow_list_reports_every_overlap(k19_runs):
    """〔改訂(第330・RET)〕前は stateful のランの重なりを空の許可の表で見て全部落ちることを見た(stateful を消した)。
    いまは許可の表そのものが空で、counter のランはそれで通る(重なりを足すと落ちる=``test_t5_runtime_fifth_word_caller_fails``)。"""
    st, _ = k19_runs["counter"]
    assert RA.check_overlaps(st, allow={}) == RA.check_overlaps(st) == []


def test_t5_runtime_fifth_word_caller_fails(monkeypatch):
    """T5: 体ごとの流れ(1 語目=体)から 5 語引く呼び手を足すと、隣の体の流れと重なって落ちる。"""
    from shibuya.core.rng import stream
    from shibuya.engine import resolve as R

    orig = R.advance_body

    def advance_body(agents, tick, *a, **k):
        if int(tick) % 60 == 0:
            for aid in range(8):
                stream(1, "test.k19.fifth_word", aid, int(tick)).random(5)
        return orig(agents, tick, *a, **k)

    monkeypatch.setattr(R, "advance_body", advance_body)
    st, _ = _record(dict(n_agents=60, seed=1, n_cells=9, ticks=240, checkpoint_every=60))
    d = st["test.k19.fifth_word"]
    assert d.max_blocks == 2 and d.actual_overlaps > 0
    problems = RA.check_overlaps(st)
    assert len(problems) == 1 and "test.k19.fifth_word" in problems[0]


@real_data
def test_k19_runtime_world_two_days(monkeypatch):
    """世界資産 300 体・2 日(既定 v3)。10e(E4・U2): counter では日の鍵の流れ(配送・工事)も重ならない。
    〔改訂(第330・RET)〕前は stateful(旧値の再現)の 2 日のランでは重なることも見た(消した)。"""
    kw = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", activity=True)
    st, _ = _record(kw, runner=cli.run)
    assert RA.check_overlaps(st) == []
    assert {d for d, s in st.items() if s.actual_overlaps} == set()
    assert st["world.delivery_inbound"].streams >= 2 and st["world.road_works"].streams >= 2  # 2 日ぶん作っている
    # 〔第 1 期 1-8 J0・検収 M2〕既定の腕(--decision-port legacy)では mock の同じ鍵の作り直しは 0(MockPort の作り直しの
    # 許可は腕 port の検査だけ=rng_audit.recreated_for)
    assert st["llm.mock"].streams > 0 and st["llm.mock"].same_key_recreated == 0


@real_data
@pytest.mark.slow
def test_k19_runtime_default_v3_5000_known_counts():
    """既定 v3・5,000 体・seed 1・1 日。10e(E4): counter では実際の重なり 0。final は包まないランと同じ。
    〔改訂(第330・RET)〕前は stateful(旧値の再現)の既知の答え(w16 185・body 1 ずつ・final 4985ff2f…/69,978)も
    見た(ACT の commit で退避先の資産と暦を渡して通った。stateful を消した)。"""
    kw = dict(n_agents=5000, seed=1, world_dir=str(WORLD_DIR), vocab_version="v3", activity=True)
    cur, res_c = _record(kw, runner=cli.run)
    assert RA.check_overlaps(cur) == [] and {d for d, s in cur.items() if s.actual_overlaps} == set()
    assert res_c.final_hash.startswith(K19_V3_FINAL_COUNTER)
    # U8: 同じ鍵の作り直しは許可の表の用途名だけ(w16 の抽出が cli と run_day で 2 回走る=186 層+定員先取り層)
    assert {d for d, s in cur.items() if s.same_key_recreated} <= set(RA.K19_RECREATED)
    # 〔第 4 期 4-3 段 10〕差し替えの世界の層の数(種別 8 の W21 の担当の体ほか)=188(前=W16 の世界 186)
    assert cur["w16.sample.stratum"].same_key_recreated == 188
    assert cur["llm.mock"].streams > 0 and cur["llm.mock"].same_key_recreated == 0  # 〔1-8 J0・検収 M2〕既定の腕
