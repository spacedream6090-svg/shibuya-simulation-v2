"""engine.systems.conductor — 系を呼ぶ進行役(第 1 期 1-0・草案 §2-4)。

``run_system(spec, ctx, box)`` が 1 つの系を包む: 試験の境目(``probe.at``=系ごとの全欄の差と指紋)・書きの許可
(``guard.system_scope``=SoA は ``writes.soa``・scratch は ``writes.scratch``)・系ごとの壁時計(``RunStats.system_seconds``。
``phase`` の鍵の集合は変えない=草案 §3-3 の 22)。

〔第 3 期 3-2・時計の段 T1〕``conduct`` は全員一斉の刻みのループ(``for T in range(t_begin, t_end)``)をやめ、「次に処理する
時刻の窓 [t, t+W)」を持って窓の中の事象を時刻順に処理する形にした(``engine.batching.WindowQueue``・決定 10-12 §4-2 TM3 (f)・
記録 ``docs/bench/analysis/wallbounce-1012/tm32/README.md``)。T1 の世界の事象は刻みの事象(世界の 1 回の系の並び=刻みの
幅ごと)だけ。幅 W(既定 60 秒=刻みの幅)は刻みの幅の約数なので、刻みの事象はいつも窓の頭に乗り、系の呼ぶ順と値は前と同じ。

逐次ループ宣言: ``run_system`` はなし(系 1 回あたり定数回)。``conduct`` は窓の数ぶん(下の宣言)。
"""

from __future__ import annotations

import functools
import os
import time
from typing import Any

from shibuya.engine.systems import guard as _G
from shibuya.engine.systems import probe as _PR
from shibuya.engine.systems.spec import SystemSpec, path_allowed

__all__ = ["run_system", "declared_check"]


def run_system(spec: SystemSpec, ctx: Any, box: Any) -> Any:
    """系 ``spec`` を 1 回呼ぶ(``ctx`` はその刻みの ``TickCtx``・ランの単位の系は ``None``)。"""
    _PR.at(spec.name, None if ctx is None else ctx.T, box)
    t0 = time.perf_counter()
    with _G.system_scope(spec.name, spec.writes.soa, spec.writes.scratch, spec.writes.buffers, spec.writes.paths):
        out = spec.fn(ctx, box)
    ss = box.runstats.system_seconds
    ss[spec.name] = ss.get(spec.name, 0.0) + (time.perf_counter() - t0)
    return out


def declared_check(specs: dict[str, SystemSpec], window_paths: frozenset[str] | None = None):
    """段 B(試験のとき): 系の前後で変わった欄 ⊆ 宣言の書く欄、を見る関数(``probe.Probe.check`` に渡す)。

    欄の鍵の族: SoA ``agents.cell`` → ``writes.soa``・外の道筋 ``O39:conv.sessions`` → ``writes.paths``(前方一致の ``*``)・
    ``stats.<名>`` → ``writes.tally``・``buffers.<名>`` → ``writes.buffers``。宣言の無い系の名(``build`` など)は通す。

    〔3-2 検収 L1〕系でない境目のうち窓の境目 ``WINDOW_MARK`` は、状態台帳の行 ``BW``(窓の待ち行列と計器)の鍵 ``BW:…``
    だけを通す(窓を閉じる・開ける・次の刻みの事象の予約のほかの変化がここに出たら宣言の外)。〔第 6 期 6-3〕腕のランでは
    会話の時計の発言の事象の処理(行 ``TCC:…``)と区域ごとの時計の窓(行 ``T4W:…``)も窓の境目に帰属する。刻みの頭 ``TICK_HEAD`` は
    前からの素通りのまま(scratch を空にする・出来事の記録の時計を進める=進行役の決まった文の差の帰属先で、系の宣言を
    持たない。1-0 の段 B の形を変えない)。

    〔第 6 期 6-4 C1〕``window_paths``=窓の境目でほかに通す道筋。``None``(既定)は連絡の道具の腕 c1 が立っているときだけ
    :data:`WINDOW_PATHS`(送信と着信の境目の処理)・ほかは空=既定のランの窓の境目は前のまま行 ``BW`` の鍵だけを通す。
    """
    if window_paths is None:
        from shibuya.engine.contact import arm as _CTA

        window_paths = WINDOW_PATHS if _CTA.is_on() else frozenset()

    def check(name: str, key: str) -> bool:
        if name == WINDOW_MARK:
            return key.startswith(WINDOW_MARK_KEYS) or (bool(window_paths) and path_allowed(key, window_paths))
        sp = specs.get(name)
        if sp is None:
            return True
        w = sp.writes
        if key.startswith("stats."):
            return key[6:] in w.tally
        if key.startswith("buffers."):
            return key[8:] in w.buffers
        if key.startswith("scratch."):
            return key[8:] in w.scratch
        if ":" in key:
            return path_allowed(key, w.paths)
        return key in w.soa

    return check


#: 刻みの頭の境目の名(系ではない=宣言を持たない。scratch を空にする差の帰属先)。
TICK_HEAD = "(tick_head)"

#: 〔第 3 期 3-2〕窓の境目の名(系ではない=宣言を持たない)。窓の中で処理の関数を呼んだ後ごとに置く=その後の待ち行列と計器
#: (状態台帳の行 ``BW``)の変化の帰属先(前の系に帰属させない)。既定のランでは何もしない(試験のときだけ snapshot)。
WINDOW_MARK = "(window)"
#: 窓の境目に帰属してよい状態台帳の行の鍵の頭(3-2 の ``BW``・〔第 6 期 6-3〕会話の時計の ``TCC``・区域ごとの時計の ``T4W``)。
WINDOW_MARK_KEYS: tuple[str, ...] = ("BW:", "TCC:", "T4W:")

#: 〔第 6 期 6-4 C1〕窓の境目で届ける種類(連絡の道具の送信=打ち終わり・着信=``engine.contact.layer.ContactLayer.bind_queue``・
#: 腕 c1 のランだけ)の処理が書く道筋(連絡の持ち主の腕の行 CT1*・出来事の記録)。窓の境目に帰属する(段 B で宣言の内)。
WINDOW_PATHS: frozenset[str] = frozenset({"CT1*:contact.*", "E:events.*"})

#: 試験(T4)のとき真: 刻みの頭で scratch を番兵で埋め、その刻みに書かれる前に読むと落とす。
STRICT_SCRATCH: bool = False

#: 立つ条件(``SystemSpec.when``)の名 → 箱を見る述語(組み立ての後は変わらない=ランの頭で 1 回だけ見る)。
WHEN = {
    "": lambda b: True,
    "presence": lambda b: b.layers.presence is not None,
    "rel_layer": lambda b: b.layers.rel_layer is not None,
    "conv": lambda b: b.layers.conv is not None,
    "act_layer": lambda b: b.layers.act_layer is not None,
    "fam_layer": lambda b: b.layers.fam_layer is not None,
    "energy": lambda b: b.layers.energy is not None,
    "home_meals": lambda b: b.layers.energy is not None and b.layers.energy.home_meals is not None,
    # 〔第 3 期 3-3〕申込書を渡したランだけ(既定のランでは系 experiment が立たない=結果不変)
    "experiment": lambda b: b.layers.experiment is not None,
    # 〔第 6 期 6-4 C1〕腕 c1 のランだけ(既定のランでは系 contact が立たない=結果不変)
    "contact": lambda b: b.layers.contact is not None,
    # 〔第 6 期 6-2 カレンダー 2〕腕 arm のランだけ(既定のランでは系 calendar_2 が立たない=結果不変)
    "calendar2": lambda b: b.layers.calendar2 is not None,
}


def tick_plan(box: Any, specs: tuple[SystemSpec, ...]) -> list[SystemSpec]:
    """刻みの中で呼ぶ系の並び(表の順・立たない系を外す・``llm_receive`` の位置を応答の遅れで選ぶ=草案 §2-2)。"""
    plan = [s for s in specs if s.timing == "tick" and WHEN[s.when](box)]
    if int(box.cfg.response_delay) == 2:  # 位置 B(旧): wake_sources の後
        rec = next(s for s in plan if s.name == "llm_receive")
        plan.remove(rec)
        plan.insert(next(k for k, s in enumerate(plan) if s.name == "wake_sources") + 1, rec)
    return plan


def conduct(call_args: dict) -> Any:
    """``run_day`` の本体: 組み立て(R1)→ 窓のループ(窓の中の事象を時刻順に=刻みの事象は日の頭 D1・刻みの系・日の終わり D2)
    → ランの終わり(R2・締め・R3)。

    逐次ループ宣言1(〔第 3 期 3-2〕で書き換え): 窓の数ぶん(ランの範囲 ÷ 幅 W=既定は刻みの数と同じ)。窓の中は
    ``engine.batching.WindowQueue.run_window`` の宣言(相異なる時刻の数ぶん・種類の続きの数ぶん)。刻みの事象 1 つの中身は
    前と同じ系の並び(10a: ``T`` は通しの時刻・``td`` はその日の中の刻み)。
    """
    from shibuya.core.time_consts import NS_PER_SECOND
    from shibuya.engine import batching as _BA
    from shibuya.engine.systems import boxes as _BX
    from shibuya.engine.systems import build as _BLD
    from shibuya.engine.systems import day as _DAY
    from shibuya.engine.systems.table import SPECS, SYSTEMS

    check = os.environ.get("SHIBUYA_SYSTEMS_CHECK", "").strip()  # 試験(T5): 既存の試験の上で段 B と番兵を回す口
    if check and _PR.ACTIVE is None:
        return _conduct_checked(call_args, check)
    t0 = time.perf_counter()
    box = _BLD.build(call_args)
    box.runstats.system_seconds["build"] = time.perf_counter() - t0
    if STRICT_SCRATCH:
        box.scratch = _BX.TickScratchStrict()
    unset = _BX.UNSET if STRICT_SCRATCH else None
    cfg = box.cfg
    tpd, total = int(cfg.tpd), int(cfg.total_ticks)
    step_s = int(cfg.tick_seconds)  # 1-1 T0: 刻みの幅[秒](``TickCtx`` の ``t_ns``・``tod_s`` の換算)
    step_ns = step_s * NS_PER_SECOND
    t_begin, t_end = int(cfg.t_begin), int(cfg.t_end)
    plan = tick_plan(box, SYSTEMS)
    s_head, s_close = SPECS["day_head"], SPECS["day_close"]
    events = box.layers.events  # 第 1 期 1-3: 出来事の記録(状態台帳の行 E・軸 1 diag・軸 2 discardable)
    # ---- 〔第 3 期 3-2〕計算のまとめの窓(幅の腕は組み立てが設定の指紋に入れた値と同じ=腕のときだけ指紋にある) ----
    width_s = _BA.arm()
    fp = cfg.fp if isinstance(cfg.fp, dict) else {}
    if int(fp.get(_BA.FP_KEY, _BA.DEFAULT_WIDTH_S)) != width_s:
        raise RuntimeError(f"まとめの幅の腕がランの途中で変わった(指紋 {fp.get(_BA.FP_KEY)}・今 {width_s})")
    queue = _BA.WindowQueue(width_s=width_s, start_ns=t_begin * step_ns, step_s=step_s)
    box.layers.batching = queue  # 状態台帳の行 BW の持ち主(軸 1 diag・軸 2 discardable=再開のランはここで作り直す)
    box.runstats.result.batching_layer = queue  # manifest の batching が読む(後付けの属性=RunResult の欄は増やさない)
    # ---- 〔第 6 期 6-3〕時計の段 T4 の場所ごとの時計(腕 regional のランだけ・既定 global は None)と T2 の会話の時計の事象の口
    # (腕 mora のランだけ組み立てが置いた持ち主に、全体の窓の待ち行列か区域ごとの時計を挿す)。腕は組み立ての指紋と同じ ----
    from shibuya.engine import regional_clock as _RCK
    from shibuya.engine import speech_clock as _TCK

    if str(fp.get(_RCK.FP_KEY, _RCK.DEFAULT_ARM)) != _RCK.arm():
        raise RuntimeError(f"時計の腕がランの途中で変わった(指紋 {fp.get(_RCK.FP_KEY)}・今 {_RCK.arm()})")
    regional = _RCK.make(world=box.soa.world, agents=box.soa.agents, width_s=width_s, start_ns=t_begin * step_ns,
                         step_s=step_s)
    box.layers.clock = regional  # 状態台帳の腕の行 T4W の持ち主(軸 1 diag・軸 2 discardable)
    talk_clock = box.layers.talk_clock
    if talk_clock is not None:
        if regional is not None:
            regional.register(_TCK.KIND_TALK, "talk", talk_clock.on_dispatch)
            talk_clock.attach(regional)
        else:
            queue.register(_TCK.KIND_TALK, "talk", talk_clock.on_dispatch, rank=_TCK.RANK_TALK)
            talk_clock.attach(_TCK.QueueRouter(queue))

    def on_step(t_ns: int, _agents: Any, _seqs: Any) -> None:
        """刻みの事象(世界の 1 回の系の並び)。中身は前の刻みのループの 1 回と同じ文の並び。"""
        T = int(t_ns) // step_ns
        if T + 1 < t_end:  # 次の刻みの事象(試験の境目 ``TICK_HEAD`` の前=待ち行列の変化は窓の境目に帰属)
            queue.schedule(int(t_ns) + step_ns, _BA.WORLD, _BA.KIND_STEP)
        ctx = _BX.TickCtx.of(T, tpd, step_s)
        _PR.at(TICK_HEAD, T, box)  # 試験だけ: scratch を空にした差を前の系に帰属させない境目(既定のランでは何もしない)
        box.scratch.reset(unset)  # 刻みの中の受け渡しは刻みの頭で空にする(Buffers は空にしない=R1)
        if events is not None:
            events.begin_step(ctx.t_ns)  # 1-3: 記録の時計=この刻みの頭の時刻(id の (t_ns, seq) の seq はここから数える)
        if _DAY.day_head_due(T, ctx.td):
            run_system(s_head, ctx, box)
        for spec in plan:
            run_system(spec, ctx, box)
        if _DAY.day_close_due(T, ctx.td, tpd, total):
            run_system(s_close, ctx, box)

    queue.register(_BA.KIND_STEP, "step", on_step, rank=0)
    if box.layers.contact is not None:  # 〔第 6 期 6-4 C1〕連絡の送信と着信の種類(窓の境目)・再開では予約の表を入れ直す
        box.layers.contact.bind_queue(queue)
    if t_begin < t_end:
        queue.schedule(t_begin * step_ns, _BA.WORLD, _BA.KIND_STEP)
    end_ns = t_end * step_ns
    while queue.head_ns < end_ns:  # 逐次ループ宣言1: 窓の数ぶん
        # 試験だけ: 処理の関数(刻みの事象=系の並び)を呼んだ後ごとの境目。その後の待ち行列と計器の変化(窓を閉じる・次の
        # 窓を開ける)はこの境目に帰属する(前の系に帰属させない)。最初の窓の前は境目が無い=帰属もしない
        _w_head = queue.head_ns
        queue.run_window(after_dispatch=functools.partial(_PR.at, WINDOW_MARK, queue.head_ns // step_ns, box))
        if regional is not None:  # 〔第 6 期 6-3 T4〕全体の窓の後に区域ごとの窓(境目の移動・遅刻・区域の事象)
            regional.run_windows(_w_head, queue.head_ns, presence=box.layers.presence, tpd=tpd)
            _PR.at(WINDOW_MARK, _w_head // step_ns, box)
    run_system(SPECS["drain"], None, box)
    run_system(SPECS["close_final"], None, box)
    result = run_system(SPECS["report"], None, box)
    _PR.at("END", None, box)
    return result


def _conduct_checked(call_args: dict, every: str) -> Any:
    """``SHIBUYA_SYSTEMS_CHECK=<間引き>`` のとき(試験だけ・T5): 段 B(系の前後で変わった欄 ⊆ 宣言)と番兵の scratch(T4)を
    入れて回し、宣言の外の変化があれば ``AssertionError``。``<間引き>`` は snapshot を取る刻みの間隔(``1``=全部)。"""
    global STRICT_SCRATCH
    from shibuya.engine.systems.table import SPECS

    k = max(1, int(every)) if every.isdigit() else 1
    T_max = 10 ** 8
    pr = _PR.Probe(check=declared_check(SPECS), ticks=frozenset(range(0, T_max, k)) if k > 1 else None,
                   families=("soa", "ext", "stats", "buffers", "scratch"))  # 段 FIX: scratch の中身も
    prev_strict = STRICT_SCRATCH
    _PR.ACTIVE, STRICT_SCRATCH = pr, True
    try:
        out = conduct(call_args)
    finally:
        _PR.ACTIVE, STRICT_SCRATCH = None, prev_strict
    if pr.violations:
        raise AssertionError(f"1-0 段 B: 宣言の外の変化 {len(pr.violations)} 件(先頭 {pr.violations[:5]})")
    return out
