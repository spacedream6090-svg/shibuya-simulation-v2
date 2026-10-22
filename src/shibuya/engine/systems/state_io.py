"""engine.systems.state_io — 箱から状態台帳の持ち主・知覚 SoA・ハッシュの材料を組む口(第 1 期 1-0)。

HEAD ``ee3abc7`` の ``run_day`` の入れ子の関数(``_hash_owners``・``_pst_now``・``_act_hash_now``・``_eod_hashes``・
``_money_now``・``_bodies_now``・``_w17_weekday``・``_relay_tables``・``_start_day``・``_ledger_close``・``_day_record``・
``_close_day_midrun``・``_save_state``・``_rebuild_derived``)を、箱を受け取る関数にしたもの(中身は同じ)。
持ち主の名・順・``run_day`` の持ち主のクラス(``engine.run._RunDayLocals``)は変えない(ハッシュに道筋の文字列が入る=
草案 §3-3 の 2)。

逐次ループ宣言: なし。
"""

from __future__ import annotations

from typing import Any

import numpy as np

from shibuya.core.hashing import blake3_hex
from shibuya.core.time_consts import CLOCK_KIND
from shibuya.engine.regional_clock import CLOCK_KIND_REGIONAL as _CLOCK_KIND_REGIONAL
from shibuya.engine import proximity as _PROX
from shibuya.engine import economy_stage2 as _ES2
from shibuya.engine.bridging import ledger as _BR
from shibuya.engine.rules import table as _RT
from shibuya.engine.state_hashes import behavior_hash as behavior_state_hash
from shibuya.engine.state_hashes import component_digests
from shibuya.engine.state_hashes import full_hash as full_state_hash

__all__ = ["hash_owners", "pst_now", "act_hash_now", "full_state_hash", "behavior_state_hash", "component_digests",
           "eod_hashes", "money_now", "bodies_now", "w17_weekday", "relay_tables", "start_day", "ledger_close",
           "day_record", "close_day_midrun", "save_state", "rebuild_derived", "mark_boundary",
           "EVENTS_OFF_RECORD", "BOUNDARY_WHO"]

# 〔1-0 の注〕``full_state_hash`` は checkpoint・日の締めの後・状態の書き出し・再開の検算がどれも**この名前を通して**呼ぶ
# (試験の差し替えの的を 1 つにする=草案 §3-3 の 15。HEAD では ``engine.run.full_state_hash``)。


def pst_now(b: Any) -> Any:
    """知覚 SoA(顕著行為の過程が持つ・世界過程が無ければ ``None``)。HEAD の ``_pst_now``。"""
    runner = b.layers.runner
    return runner.salient.pstate if runner is not None else None


def hash_owners(b: Any) -> dict[str, Any]:
    """10b: 状態台帳の外の状態の持ち主(``items`` の根の鍵)。HEAD の ``_hash_owners`` と同じ鍵・同じ順・同じ物。

    〔第 1 期 1-3〕末尾に ``events``(出来事の記録・状態台帳の行 ``E``=軸 1 diag・軸 2 discardable)を足した。2 つのハッシュと
    状態のファイルは軸で選んだ行の道筋だけを読むので、値は変わらない(段 B の全欄の差と書きの網羅が読む)。
    〔第 1 期 1-8 J0〕その後に ``decision``(候補の口の層・状態台帳の行 ``J0``=軸 1 diag・軸 2 discardable・腕 port のランだけ)。
    〔第 1 期 1-8b〕その後に ``speech``(発話の口・状態台帳の腕の行 ``S8``=軸 1 behavior・軸 2 required と ``S8M``=診断・
    腕 on のランだけ。腕の行は持ち主が None のランでは 2 つのハッシュにも状態のファイルにも入らない=既定は不変)。
    〔第 2 期 2-2 段 11a〕その後に ``proximity``(近接の層・状態台帳の行 ``PX``=軸 1 diag・軸 2 discardable・腕 distance のランだけ)。
    〔第 3 期 3-3〕その後に ``experiment``(申込書の持ち主・状態台帳の行 ``X``=軸 1 diag・軸 2 discardable・申込書を渡したランだけ)。
    〔第 3 期 3-2〕その後に ``batching``(計算のまとめの窓・状態台帳の行 ``BW``=軸 1 diag・軸 2 discardable・進行役が置く)。
    〔第 3 期 3-5〕その後に ``body``(本人の体の層・状態台帳の行 ``BD``=軸 1 diag・軸 2 discardable・どの腕でも置く)。
    〔第 3 期 3-1〕その後に ``calendar_shadow``(暦 1a の影・状態台帳の行 ``CAL``=軸 1 diag・軸 2 derivable・中身は hash_skip・
    腕 1a のランだけ)。
    〔第 6 期 6-2〕その後に ``calendar_self``(カレンダー 1b・状態台帳の腕の行 ``C1B``=behavior・required と ``C1BM``=diag・
    required・腕 1b のランだけ=持ち主が None のランでは 2 つのハッシュにも状態のファイルにも入らない=既定は不変)。
    〔第 6 期 6-4 C1〕その後に ``contact``(連絡の道具・状態台帳の腕の行 ``CT1*``・腕 c1 のランだけ=既定は持ち主が None)。
    〔第 6 期 6-2 カレンダー 2〕その後に ``calendar2``(会話から生まれる予定・状態台帳の腕の行 ``CA2*``・腕 arm のランだけ)。
    〔第 6 期 6-2 カレンダー 3〕その後に ``calendar3``(雇い主・祝日・状態台帳の腕の行 ``CA3*``・腕 arm のランだけ)。
    """
    from shibuya.engine.run import _RunDayLocals

    L, io = b.layers, b.llm
    return {
        "act_layer": L.act_layer, "intent_layer": L.intent_layer, "fam_layer": L.fam_layer,
        "mem_layer": L.mem_layer, "poi_resolver": L.poi_resolver, "wom": L.wom, "rel_layer": L.rel_layer,
        "classical": L.classical, "energy": L.energy, "norm_meter": L.norm_meter,
        "presence": L.presence, "conv": L.conv, "arbiter": L.arbiter, "detector": L.detector,
        "runner": L.runner, "ledger": L.ledger, "undefined": L.bridge.undefined,
        "renderer": L.renderer,
        "bridge": L.bridge, "fleet_bridge": L.fleet_bridge,
        "run_day": _RunDayLocals(io.pending, io.fleet_deferred, io.fleet_waiting, io.replay_inbox),
        "events": getattr(L, "events", None),
        "decision": getattr(L, "decision", None),
        "speech": getattr(L, "speech", None),
        "proximity": getattr(L, "proximity", None),
        "experiment": getattr(L, "experiment", None),
        "batching": getattr(L, "batching", None),
        "body": getattr(L, "body", None),
        "calendar_shadow": getattr(L, "calendar_shadow", None),
        "calendar_self": getattr(L, "calendar_self", None),
        # 〔第 6 期 6-3〕時計の段 T2〜T4 の腕の持ち主(腕の行=持ち主の居るランだけ・diag・discardable=値は変わらない)
        "talk_clock": getattr(L, "talk_clock", None),
        "step_scope": getattr(L, "step_scope", None),
        "clock": getattr(L, "clock", None),
        "contact": getattr(L, "contact", None),  # 〔第 6 期 6-4 C1〕腕の行 CT1*=持ち主の居るランだけハッシュと状態のファイルに入る
        "calendar2": getattr(L, "calendar2", None),  # 〔第 6 期 6-2 カレンダー 2〕腕の行 CA2*=持ち主の居るランだけ
        "calendar3": getattr(L, "calendar3", None),  # 〔第 6 期 6-2 カレンダー 3〕腕の行 CA3*=持ち主の居るランだけ
    }


def act_hash_now(b: Any) -> str:
    """活動層(と意図の層)の Python 側の状態のハッシュ(HEAD の ``_act_hash_now``)。"""
    act_layer, intent_layer = b.layers.act_layer, b.layers.intent_layer
    if act_layer is None:
        return ""
    if intent_layer is None:
        return act_layer.state_hash()
    return blake3_hex(f"{act_layer.state_hash()}\x1f{intent_layer.state_hash()}".encode())


def eod_hashes(b: Any) -> dict[str, Any]:
    """日の締めの**後**の behavior-hash・full-hash(10b 検収後 P2・10d の再開の判定はこちら)。読むだけ。HEAD の ``_eod_hashes``。"""
    agents, world = b.soa.agents, b.soa.world
    schedule, schedule_hash = b.fx.schedule, b.fx.schedule_hash
    _owners_e = hash_owners(b)
    _memo_e: dict[str, tuple[bytes, int]] = {}
    _full_e, _bytes_e = full_state_hash(agents, world, pst_now(b), schedule.population_hash, schedule_hash,
                                        _owners_e, memo=_memo_e)
    return {
        "behavior_hash": behavior_state_hash(agents, world, schedule.population_hash, schedule_hash,
                                             act_hash_now(b), _owners_e, memo=_memo_e),
        "full_hash": _full_e,
        "full_external_bytes": int(sum(_bytes_e.values())),
    }


def money_now(b: Any) -> dict[str, int]:
    """HEAD の ``_money_now``。"""
    agents, ledger = b.soa.agents, b.layers.ledger
    out = {"households": int(np.asarray(agents.registry.money, dtype=np.int64).sum())}
    if ledger is not None and ledger.money is not None:
        out["money_supply"] = int(ledger.money.money_supply())
    return out


def bodies_now(b: Any) -> dict[str, int]:
    """HEAD の ``_bodies_now``。"""
    st = np.asarray(b.soa.agents.registry.transit_state, dtype=np.int64)
    return {"n": int(st.size), "in_area": int(np.count_nonzero(st == 0)),
            "riding": int(np.count_nonzero(st == 1)), "outside": int(np.count_nonzero(st == 2)),
            "other": int(np.count_nonzero((st < 0) | (st > 2)))}


def w17_weekday(b: Any, d: int) -> int:
    """その日に引く W17 の曜日の行(0 日目は暦のまま=今と同じ)。HEAD の ``_w17_weekday``。

    K9 (a)(つなぎ・宣言): W17 v2 は曜日 0(月曜)の行しか無いので、行の無い曜日は月曜の行で引く。
    """
    calendar, weekly = b.fx.calendar, b.fx.weekly
    wd = int(calendar.table_weekday(int(d)))
    if int(d) == 0 or weekly is None:
        return wd
    if weekly.agent_rows_of_day(wd).size == 0:
        return 0
    return wd


def relay_tables(b: Any, d: int) -> None:
    """10d: ``d`` 日目の日の頭の**表の張り直し**(資産・暦・日番号だけから決まる=再開でも同じ表)。HEAD の ``_relay_tables``。

    鉄道の時刻表(T の座標で末尾に足す)・天気の実日・計画実行層の在圏ブロックとイベント(出勤率の欠席を
    日番号つきで引き直す)・計画境界の表(W17 は K9 のつなぎ)。体の状態は書かない(``start_day``)。
    〔1-0〕HEAD の nonlocal 5 つ(b_*)は ``DayTables`` の欄(草案 §3-3 の 5)。
    """
    from shibuya.agents.state import WakeCondition

    runner, presence = b.layers.runner, b.layers.presence
    act_layer, classical_policy, poi_resolver = b.layers.act_layer, b.layers.classical, b.layers.poi_resolver
    calendar, weekly, schedule = b.fx.calendar, b.fx.weekly, b.fx.schedule
    tpd, ticks = b.cfg.tpd, b.cfg.ticks
    w17_substituted = b.day.w17_substituted
    d = int(d)
    if runner is not None:
        runner.relay_day(d, ticks_per_day=tpd)  # 時刻表・天気・営業時間の曜日の行・日ごとの乱数の表
    wd = w17_weekday(b, d)
    if weekly is not None and wd != int(calendar.table_weekday(d)) and d not in w17_substituted:
        w17_substituted.append(d)
    if presence is not None:
        presence.relay_day(d, t0=d * tpd, weekday=wd)
    calendar_shadow = b.layers.calendar_shadow
    if calendar_shadow is not None:  # 〔第 3 期 3-1〕暦 1a の影(計器だけ・W20 と暦と日番号から=再開でも同じ)
        calendar_shadow.relay_day(d, w17_weekday=wd)
    calendar_self = b.layers.calendar_self
    if calendar_self is not None:  # 〔第 6 期 6-2〕カレンダー 1b(W20・暦・日番号と保存した器から=再開でも同じ)
        calendar_self.relay_day(d)
    if weekly is not None:
        na, nc, nt, ncell = weekly.boundary_events_full(wd)
    else:
        na, ns, nt = schedule.events_of_day(calendar.table_weekday(d), rest_day=calendar.is_rest_day(d))
        ncell = np.full(na.size, -1, dtype=np.int32)
        nc = np.array(
            [int(WakeCondition.PLAN_GENERAL), int(WakeCondition.PLAN_TRANSIT), int(WakeCondition.PLAN_GENERAL),
             int(WakeCondition.PLAN_TRANSIT), int(WakeCondition.PLAN_SLEEPING)],
            dtype=np.int8,
        )[ns]
    dt = b.day
    same = all(np.array_equal(x, y) for x, y in ((na, dt.b_agent), (nc, dt.b_cond), (nt, dt.b_tick), (ncell, dt.b_cell)))
    if same:
        return
    if (act_layer is not None or classical_policy is not None
            or getattr(poi_resolver, "store_choice", None) is not None):
        # 活動層・方策 classical・想起優先の候補合成は起動時に計画境界の表を写して持つ。日で表が変わる
        # (休日の mock 日課・W17 の別の曜日の行)ランでの張り直しは 10d の範囲の外(止めて問いにする)
        raise NotImplementedError(
            f"{d} 日目の計画境界の表が前の日と違う(休日など)。活動層・classical・想起優先の候補合成の表の"
            "張り直しは K9 の解消まで入れていない(K9 のつなぎ=平日は月曜の行の間は通らない)"
        )
    dt.b_agent, dt.b_cond, dt.b_tick, dt.b_cell = na, nc, nt, ncell
    dt.b_start = np.searchsorted(dt.b_tick, np.arange(ticks + 1), side="left")


def start_day(b: Any, d: int) -> None:
    """10d: ``d`` 日目の日の頭の体の側の書き換え(通しのランだけ・再開では保存した値を読む)。HEAD の ``_start_day``。

    日の頭の初期化(``initialize``・初期の活動・域外の配置・空腹の初期値・初期の財布・参入資本・帳簿の作り
    直し)は**走らせない**(A11)。計画実行層の「今日の計画」の写しと日ごとの印だけを今日の表から置く。
    """
    presence, tpd = b.layers.presence, b.cfg.tpd
    if presence is not None:
        presence.start_day()
    b.runstats.day_heads.append({"day": int(d), "T": int(d) * tpd, "money": money_now(b), "bodies": bodies_now(b)})


def ledger_close(b: Any, day: int) -> tuple[dict[str, Any], dict[str, int]]:
    """金と物の台帳の日の締め・日次センサス・月次 T3・センサスの書き出し(1 日のランは今のまま)。HEAD の ``_ledger_close``。"""
    from pathlib import Path

    calendar, ledger, result = b.fx.calendar, b.layers.ledger, b.runstats.result
    census_out, sim_days = b.cfg.census_out, b.cfg.sim_days
    # 日次の畳み込み(D-R2-6: 生ログは保持窓・取引行列は日次集約行へ)。
    # **締めを捨てない**——締めると取引行列も当日の廃棄も 0 に戻るので、締めたあとに
    # 現在値でセンサスを回すと faucet/sink/廃棄が全部 0 の空虚な行になり、ゲートが
    # 素通りする(層2レビュー指摘)。``daily_census`` は ``day_index`` の締めを読む。
    # 10a #21: 締めの日番号は暦の口の ``day_key``(day_index モードでは今の ``day_index``)。
    _close_day = calendar.day_key(int(day))
    closes = ledger.end_of_day(_close_day)
    result.day_closed = int(closes.day)
    growth = ledger.growth_parts()
    # 日次(軽量)センサス+ゲート(境界・経済設計書 §2.4)。
    # engine は economy を import できない(層契約)ので、行の作り手は
    # ``LedgerBundle.census``(economy 側が注入する呼び出し可能)。**失敗しても raise しない**
    # =診断の赤(§2.4「ゲート失敗=較正・holdout 照合に使わない」)。
    row = ledger.daily_census(_close_day)
    if row is not None:
        result.census_row = dict(row)
        result.census_pass = bool(row.get("gate_ok", False))
    # 月次センサスの T3(冗長方程式の検算・D-85 (a)・ユーザー決定 2026-09-17)。
    # 月次が立たない日は None(=未実行)。**``census_out`` とは無関係に**毎日呼ぶ
    # ——書き出しの有無で manifest が動くと「観測が世界を変えない」が崩れるため。
    t3 = ledger.monthly_t3(_close_day)
    if t3 is not None:
        result.t3_report = dict(t3)
        result.t3_ok = bool(t3.get("ok", False))
    # 日次センサス/月次 MER の出力口(§2.4)。**``census_out`` を渡したときだけ**書く。
    # 書き手は economy 側の注入(engine は economy を import できない=層契約)。
    # 10d: 複数日のランでは日ごとの置き場(``day-NNNN``)に書く(1 日のランは今のまま)。
    if census_out is not None:
        _out = str(census_out) if sim_days == 1 else str(Path(census_out) / f"day-{int(day):04d}")
        result.census_paths = ledger.write_census(_close_day, _out)
    return growth


def day_record(b: Any, d: int) -> None:
    """HEAD の ``_day_record``。"""
    ledger, result, tpd = b.layers.ledger, b.runstats.result, b.cfg.tpd
    rec: dict[str, Any] = {"day": int(d), "end_T": (int(d) + 1) * tpd, "money": money_now(b),
                           "bodies": bodies_now(b)}
    if ledger is not None:
        rec["day_closed"] = int(result.day_closed)
        rec["census_pass"] = bool(result.census_pass)
        rec["census_row"] = {k: v for k, v in dict(result.census_row).items()
                             if isinstance(v, (bool, int, float, str))}
    if result.state_hashes_end_of_day:
        rec["state_hashes_end_of_day"] = dict(result.state_hashes_end_of_day)
    # 第 1 期 1-1 T0(TM9・GPU 無しの欄): この日の呼び出し数を判断モデルと LLM に分ける(判断モデルはまだ無い=0。
    # LLM は発射数の積算 ``RunResult.llm_calls`` のこの記録までの増え=このランの中で数えた分。再開したランの最初の日は
    # 再開した時刻からの分)・時計の種類と幅・つなぎの台帳の数。記録の欄が増えるだけ(状態に入らない)。
    llm_before = sum(int(r["calls_by_model"]["llm"]) for r in b.runstats.daily_records if "calls_by_model" in r)
    # 〔第 6 期 6-4 C1 検収 M5 (ii)〕腕 c1 のランは連絡の判断と文の口を足す(既定のランは今のまま)
    ct = getattr(b.layers, "contact", None)
    c2 = getattr(b.layers, "calendar2", None)  # 〔第 6 期 6-2 カレンダー 2〕腕 arm のランは同じ形で内訳 calendar_2
    if ct is None and c2 is None:
        rec["calls_by_model"] = {"judge_model": 0, "llm": int(result.llm_calls) - llm_before}
    else:
        from shibuya.engine.run import _calls_by_model

        prev = [r["calls_by_model"].get("contact", {}) for r in b.runstats.daily_records if "calls_by_model" in r]
        prev2 = [r["calls_by_model"].get("calendar_2", {}) for r in b.runstats.daily_records if "calls_by_model" in r]
        # 〔第 6 期 6-2 カレンダー 3〕腕 arm のランは同じ形で内訳 calendar_3(腕の無いランは今のまま)
        c3 = getattr(b.layers, "calendar3", None)
        prev3 = [r["calls_by_model"].get("calendar_3", {}) for r in b.runstats.daily_records if "calls_by_model" in r]
        llm_before -= (sum(int(x.get("llm", 0)) for x in prev) + sum(int(x.get("llm", 0)) for x in prev2)
                       + sum(int(x.get("llm", 0)) for x in prev3))
        rec["calls_by_model"] = _calls_by_model(int(result.llm_calls) - llm_before, ct, (
            sum(int(x.get("judge_model", 0)) for x in prev), sum(int(x.get("llm", 0)) for x in prev)), calendar2=c2,
            before2=(sum(int(x.get("judge_model", 0)) for x in prev2), sum(int(x.get("llm", 0)) for x in prev2)),
            calendar3=c3,
            before3=(sum(int(x.get("judge_model", 0)) for x in prev3), sum(int(x.get("llm", 0)) for x in prev3)))
    # 〔第 6 期 6-3 T4〕時計の種類は区域ごとの時計のランだけ regional(既定は今の steps)
    rec["clock_kind"] = CLOCK_KIND if getattr(b.layers, "clock", None) is None else _CLOCK_KIND_REGIONAL
    rec["step_seconds"] = int(b.cfg.tick_seconds)
    # 第 1 期 1-4: つなぎの台帳の件数(T0 の null を件数に)と規則の表の版(表の sha)。TM9 の行に並べる(``events`` の前)。
    # どちらもリポの docs の表を 1 回だけ読む(状態に入らない=記録だけ)。
    rec["bridges_count"] = _BR.bridges_count()
    rec["rules_version"] = _RT.rules_version()
    # 第 1 期 1-3: E(診断)の区切りの行(日の締め)を書き、その日の出来事の記録の行数・バイト・種類の分布を記録の欄に出す
    # (計器・口の約束 1-3 の約束 (3))。保持窓の外の行はここで落とす。記録の欄が増えるだけ(状態に入らない)。
    events = b.layers.events
    mark_boundary(events, "day_close")
    # 第 1 期 1-9: その日の transfer の計器(行・額・溢れ=K17・原因の無い行・出来事の行)と流れの表の検算(締めの後の値)。
    # 記録の欄が増えるだけ(状態に入らない)。台帳が無いランは空。
    rec["economy"] = ledger.economy_day_record() if ledger is not None else {}
    rec["events"] = events.close_day(int(d)) if events is not None else dict(EVENTS_OFF_RECORD)
    b.runstats.daily_records.append(rec)


#: 1-3: 記録の物が無いときの日次の記録の欄(``EventLog.close_day`` の記録しないときと同じ形)。
EVENTS_OFF_RECORD: dict[str, Any] = {"on": False, "rows": 0, "bytes": 0, "by_what": {}, "by_cause": {},
                                     "live_rows": 0, "live_bytes": 0, "evicted": 0}
#: 1-3: 区切りの行の ``who``(持ち主の名=エンジンの区切り)。未リサーチ(expedient)。
BOUNDARY_WHO: str = "engine"


def mark_boundary(events: Any, name: str) -> None:
    """1-3: E(診断)の区切りの行(``day_close``・``checkpoint``)を記録の時計の時刻で 1 行書く(記録しないときは何もしない)。

    原因は ``Process(name)``・``what`` は ``過程:<name>``(語彙表の区切りの名)。
    """
    if events is None or not events.enabled:
        return
    from shibuya.engine.events import log as _EV
    from shibuya.engine.events import vocab as _V

    events.append(_EV.Event(t_ns=events.now_ns, who=BOUNDARY_WHO, what=_V.word(_V.FAMILY_PROCESS, name),
                            cause=_EV.Process(name)))


def close_day_midrun(b: Any, d: int) -> None:
    """10d: 複数日のランの途中の日の締め(1 日 1 回・最後の刻みの後・次の日の刻み 0 の前)。HEAD の ``_close_day_midrun``。

    鉄道の最後の便は流さない(次の日の頭の刻みが流す=同じ発車を 2 度処理しない)。台帳の締め・センサス・
    締めの後の 2 つのハッシュは最後の日と同じ。
    """
    runner, ledger, result = b.layers.runner, b.layers.ledger, b.runstats.result
    tpd, checkpoint_every = b.cfg.tpd, b.cfg.checkpoint_every
    if runner is not None:
        runner.end_of_day((int(d) + 1) * tpd - 1, flush_rail=False)
    if ledger is not None:
        ledger_close(b, int(d))
    if checkpoint_every:
        result.state_hashes_end_of_day = eod_hashes(b)
    day_record(b, int(d))


def _stage2_plan(b: Any) -> Any:
    """〔2-1〕経済の段階 2 の組み立ての物(腕の無いランは None)。"""
    led = b.layers.ledger
    money = getattr(led, "money", None) if led is not None else None
    s2 = getattr(money, "stage2", None)
    return None if s2 is None else s2.plan


def save_state(b: Any, T_next: int, *, finished: bool, closed: bool) -> None:
    """10d: 状態のまとまりを 1 ファイルに書く(SoA の列・外の状態・進捗の印・艦隊の未着の呼)。HEAD の ``_save_state``。"""
    import copy
    import time

    from shibuya.engine import resume as RS
    from shibuya.engine import state_ledger as SL

    agents, world = b.soa.agents, b.soa.world
    schedule, schedule_hash, _env_fields = b.fx.schedule, b.fx.schedule_hash, b.fx.env_fields
    cfg = b.cfg
    run_id, parent_run, sim_days, tpd, _fp, state_out = (cfg.run_id, cfg.parent_run, cfg.sim_days, cfg.tpd, cfg.fp,
                                                         cfg.state_out)
    fleet_inflight = b.llm.fleet_inflight
    t0_ = time.perf_counter()
    owners_ = hash_owners(b)
    memo_: dict[str, tuple[bytes, int]] = {}
    full_, _ = full_state_hash(agents, world, pst_now(b), schedule.population_hash, schedule_hash, owners_,
                               memo=memo_)
    beh_ = behavior_state_hash(agents, world, schedule.population_hash, schedule_hash, act_hash_now(b),
                               owners_, memo=memo_)
    soa_ = RS.collect_soa(agents, world, pst_now(b))
    items_ = RS.collect_items(owners_)
    header = {
        "format": RS.STATE_FORMAT,
        "ledger_version": SL.LEDGER_VERSION,
        "run_id": run_id,
        "parent_run": parent_run,
        "finished": bool(finished),
        "progress": {
            "next_T": int(T_next), "day": int(T_next) // tpd, "tick_of_day": int(T_next) % tpd,
            "days_closed": int(T_next) // tpd, "closed_at_day_end": bool(closed),
            "sim_days": int(sim_days), "ticks_per_day": int(tpd),
        },
        "fingerprint": _fp,
        "platform": copy.deepcopy(_env_fields),
        "env_id": str(_env_fields["env_id"]),  # 10f: manifest・run_meta.json と同じ値
        "hashes": {"behavior_hash": beh_, "full_hash": full_},
        "counts": {
            "soa_columns": {k: len(v) for k, v in soa_.items()},
            "external_items": len(items_),
            "inflight_calls": len(fleet_inflight),
            "pending_responses": len(b.llm.pending),
        },
    }
    # 第 2 期 2-2(検収 M1): 腕 distance のランだけ近接の腕を書く(再開で今の腕と突き合わせる・腕 cell は今の見出しのまま)
    _px = _PROX.header_fields(b.layers.proximity)
    if _px is not None:
        header["proximity"] = _px
    # 第 2 期 2-1(検収 A5): 経済の段階 2 の腕のランだけ腕と部品を書く(再開で今の腕と突き合わせる・腕 off は今の見出しのまま)
    _es2 = _ES2.header_fields(_stage2_plan(b))
    if _es2 is not None:
        header["economy_stage2"] = _es2
    # 〔第 2 期 2-4 V3〕在席の印を歩き出しで解く腕(既定の walk のランだけ書く=legacy は 2-4 より前の見出しのまま)
    from shibuya.engine import seat_release as _SR

    _sr = _SR.header_fields(b.cfg.seat_release)
    if _sr is not None:
        header["seat_release"] = _sr
    from shibuya.engine.experiment import layer as _EXPL

    _exp_h = _EXPL.state_header(getattr(b.layers, "experiment", None))
    if _exp_h is not None:  # 〔第 3 期 3-3〕申込書つきのランだけ(既定のランの見出しは今のまま)=再開で違えば止める
        header["experiment"] = _exp_h
    path = RS.state_path(state_out, int(T_next))
    nbytes = RS.write_state(path, RS.StateBundle(header, soa_, items_, list(fleet_inflight.values())))
    b.runstats.state_files.append({"file": path.name, "T": int(T_next), "bytes": int(nbytes), "finished": bool(finished),
                                   "full_hash": full_, "seconds": round(time.perf_counter() - t0_, 3)})


def rebuild_derived(b: Any) -> None:
    """10d(親の答え 2): 起動時に**SoA の値から**作る表を、戻した SoA から決定的に作り直す(再開だけ)。HEAD の ``_rebuild_derived``。

    通しのランではこれらの表は ``initialize`` の後の SoA(体の種別)から作られる。再開では初期化を呼ばないので、
    保存から戻した SoA で作り直す(種別はラン中に変わらない=通しと同じ表)。表は状態台帳の除外の一覧の
    キャッシュ(導出)に載る: 方策 classical の ``employed``・開閉の過程の担当従業者 ``staff_of_poi``
    (補充の過程が同じ配列を持つ)。〔第 1 期 1-7〕関係の記憶の連絡先の印(``rel_layer._contact_flags``=状態台帳の行 CT5)も
    戻した辺の種別から作り直す。
    """
    classical_policy, runner = b.layers.classical, b.layers.runner
    if classical_policy is not None:
        classical_policy.rebuild_derived()
    if runner is not None:
        runner.opening.rebuild_derived()
    # 第 1 期 1-7 CT5: 連絡先の印(関係の記憶の contact_flags)を戻した辺の種別から作り直す(状態台帳の行 CT5=導出)
    if b.layers.rel_layer is not None:
        b.layers.rel_layer.rebuild_contacts(b.soa.agents)
