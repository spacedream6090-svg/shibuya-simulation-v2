# -*- coding: utf-8 -*-
"""anchor_gauge — 第 2 期 2-0 **較正側の錨の計器**(記録を読むだけ・エンジン不変)。

正典
    計画 ``docs/design/v2-implementation-plan-2026-10-12.md`` の 2-0(較正側の錨だけで測る常設の計器・5,000 体
    mock と古典の 2 腕で版上げごとに記録・holdout と PT の検証側には触れない・「現実に近づいた」の主張は holdout の
    開封(S1)の後だけ)。設計は答申 R-115(``docs/research/v2-r115-calibration-anchors-inventory-for-2-0.md``)の
    §2 錨 × 材料の表・§3 量ごとの式と記録の口・§4 事前登録 v1.4 の定義の草案。

4 つの量(R-115 §3)
    3-1 在圏のピーク時刻 / 3-2 来街者/居住者の比 / 3-3 駅ごとの到着の波 / 3-4 勤務の始業の分布。
    錨の印: 〔写〕構築の入力の写し(形だけ見る・合否にしない)/〔部〕一部だけ入力/〔非〕入力でない。
    〔検〕(検証側)と〔灰〕(区分が未決)は **1 バイトも読まない**(``read_guard`` の許可の一覧で縛る)。
    PT c-2(錨 3)・線ごとに違う材料(3-3 の錨 4〔灰〕)は材料待ち=器だけ(空の列)。**合否は書かない**。

段は 2 つ(どちらも src を変えない)
    ``record``: ``shibuya.cli.run`` を 1 本回し、``tools/c7/attr_arms.AgentCellRecorder``(``engine.resolve.apply``
    を包んで毎刻みの cell と transit_state を控える)で体の journal を取る。計画実行層(``PlanExecutor``)と
    母集団(``engine.run._resolve_population``)は**関数を包んで参照を控えるだけ**(戻り値は変えない)。
    計画上のセル(刻み × 体)・計画の到着(ARRIVE の予定)・W17 の勤務の行の始まりを記録に足す。
    ランの間は封印の層を開いたら落ちる守り(``ReadGuard.sealed_only``)を載せる。
    ``gauge``: 記録(2 腕)と構築側のファイルだけを許可の一覧で読んで 4 つの量を出す。

使い方(リポの根で・作業木の src)::

    python tools/instruments/anchor_gauge.py run --scratch <作業用> --out-root docs/bench/instruments/anchor_gauge
    python tools/instruments/anchor_gauge.py record --arm mock --out <作業用>/anchor_journal_mock.npz
    python tools/instruments/anchor_gauge.py gauge --journal mock=<…>.npz --journal classical=<…>.npz \\
        --out-dir docs/bench/instruments/anchor_gauge/<日付>_<commit> [--compare <前のフォルダ>]
    python tools/instruments/anchor_gauge.py compare --prev <前のフォルダ> --cur <今のフォルダ>

宣言(未リサーチ=expedient・記録 README に一覧)
    - 拡大係数 ω_k = N_k / n_k(W16 の種別 k の体数 ÷ 標本の体数)。二層抽出の種別の偏りを戻す(R-115 §3-0)。
    - 1 日ランの 24〜28 時は同じ日の 0〜4 時で代える(R-115 §4-6)。
    - 時間帯別の数え方は θ ∈ {1 刻み(既定), 30 分}(仕分け C §2-1 の 5)。1 日単位の 30 分は**合計**(既定)・連続は腕。
    - 計画上のセル: 行の target_cell。負の行は 職場 → W16 work_cell・学校 → school_cell・自宅 → home_cell で補う
      (R-115 §5 空欄 7)。補えない行は「舞台の中・セル不明」(エリアに数えない・舞台には数える)。
    - 3-3 の到着の帰属は W16 の direction_node(域内居住者の帰りは線を選ばない=ずれうる)。母集団は全員(W12 の
      流量に年齢の軸が無い)。
    - 3-4 の対象: kind 0・2・v1.4 の母集団・work_cell ≥ 0 かつ work_cell ≠ home_cell(自宅で従業は除く)。
      始まり=その日に work_cell に 30 分以上続けて居た最初の区間の始まり(0 時から続く区間は前日の続き=除く)。
    - 3-4 錨 3 の「立ち上がり」= 仕事の行動者率が 1 日の最大の 50% を超える最初の 15 分(閾値 50% は expedient)。
    - 中核 9 町丁目の腕: セル → 町丁目は W16 の居住者の chome_key の多数決・居住者の居ないセルは最も近いセルの
      町丁目。昼間=10:00〜16:00 に 30 分以上(ランの腕)。
逐次ループ宣言: 計画のセル(行の数=5,000 体で約 4.5 万)・最長の連続と始業の検出(刻みの数 1,440 × ベクトル)・
    町丁目の最近傍(セルの数 520)。体の数に比例する Python のループは記録の段の行の塗りだけ。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

HERE = Path(os.path.abspath(__file__)).parent
REPO = HERE.parent.parent
for _p in (str(REPO / "src"), str(REPO / "tools" / "c7"), str(HERE)):
    if _p not in sys.path:  # pragma: no cover - 実行時の経路
        sys.path.insert(0, _p)

import c7lib  # noqa: E402
from read_guard import (  # noqa: E402
    GAUGE_EXTRA_DENY_TOKENS, JOURNAL_PREFIX, JOURNAL_SUFFIX, NotAllowedError, ReadGuard, deny_hit, files_listing,
    roles_table,
)
from shibuya.core.time_consts import (  # noqa: E402
    HOURS_PER_DAY, MINUTES_PER_DAY, MINUTES_PER_HOUR, SECONDS_PER_HOUR, SECONDS_PER_MINUTE, STEP_SECONDS,
)
# 〔第 3 期 3-1・検収 低 7〕W20cal の組んだ資産の置き場と名はエンジンの読み口の定数を 1 か所で読む
from shibuya.engine.calendar_shadow import FILE_NAME as _CSH_FILE_NAME  # noqa: E402
from shibuya.engine.calendar_shadow import STAGE_DIR as _CSH_STAGE_DIR  # noqa: E402

SCHEMA = "shibuya.tools.instruments/anchor_gauge/1"
JOURNAL_SCHEMA = "shibuya.tools.instruments/anchor_journal/1"

#: 2 腕(byte-check の表と同じ呼び方=wave2_bytecheck の v3 既定・v3_classical)。計画実行層は既定 on。
ARMS: dict[str, dict[str, Any]] = {
    "mock": {"vocab_version": "v3"},
    "classical": {"vocab_version": "v3", "policy": "classical", "chooser": "classical"},
}

AREA_IDS: tuple[str, ...] = c7lib.AREA_IDS
#: 列: 5 エリア+5 エリア計(どれかのエリア)+舞台(bbox 内のどこか)。
COLS: tuple[str, ...] = AREA_IDS + ("total5", "stage")
COL_JA: dict[str, str] = {**c7lib.AREA_JA, "total5": "5 エリア計", "stage": "舞台全体"}
#: KDDI の時間帯 5〜28 時(24 区分)。24〜28 時は同じ日の 0〜4 時で代える(宣言)。
KDDI_HOURS: tuple[int, ...] = c7lib.KDDI_HOUR_BINS
HOUR_IDX = np.asarray([h % HOURS_PER_DAY for h in KDDI_HOURS], dtype=np.int64)
DWELL_MIN = 30
#: 時間帯別の θ[分](1 分=今の 1 刻み・30 分)。比べるときは秒に直す(検収 L4)。
THETAS: tuple[int, ...] = (1, 30)
THETA_MAIN = 1
ADULT_AGE = 20
FOREIGN_KIND = 7
VISITOR_KINDS: tuple[int, ...] = (1, 6, 7)
WORK_KINDS: tuple[int, ...] = (0, 2)
SLOT_MIN = 15
N_SLOTS = MINUTES_PER_DAY // SLOT_MIN
RISE_FRACTION = 0.5
CORE9_DAY_WINDOW = (10 * MINUTES_PER_HOUR, 16 * MINUTES_PER_HOUR)  # 10:00〜16:00(宣言)
#: 現実同士のずれ(フロア): PT 2018 の日中ピークの 所属なし/勤務通学 0.16(業務を足して 0.27)vs KDDI 1.66。
#: 合否にしない・表に書くだけ(attr_arms.FLOOR_PT_VISITOR_PER_WORKER と同じ値=sub_e §2-3)。
FLOOR_VISITOR_PER_WORKER = {"pt_2018": [0.16, 0.27], "kddi": 1.66}
NONE_NODE = "none"
#: ピークの順の区切り(早い順=左が早い・検収 L5)。
ORDER_SEP = "→"

#: 既定の道筋(リポの根からの相対)。
DEFAULTS: dict[str, str] = {
    "world": "data/world/v2",
    "area_axes": "tools/c7/area_axes_v0.json",
    "time_dist_12": "data/realworld/transport_census/time_dist_12.json",
    "commute_r3": "docs/bench/anchors/commute_time_dist_r3.json",
    "ssb_8_1": "docs/bench/anchors/ssb2021_activity_prior_v0.json",
    "calib_anchors": "docs/bench/instruments/anchor_gauge/calib_anchors_v0.json",
    "pool": "data/persona_pool_v2",
    "records": "docs/bench/instruments/anchor_gauge",
    # 〔第 3 期 3-1〕3-4 の源「W20」=構築の段 W20cal(暦 1a)の週の表(組んだ資産の置き場・無ければ空の列)
    "w20": f"{_CSH_STAGE_DIR}/{_CSH_FILE_NAME}",
}
#: 世界資産の中の役割 → ファイル名。
WORLD_FILES: dict[str, str] = {
    "W16": "w16_population.parquet",
    "W16_chome": "w16_chome.parquet",
    "W2_cells": "w2_cells.parquet",
    "W12_nodes": "w12_external_nodes.parquet",
    "W12_weights": "w12_generation_weights.parquet",
}
#: 役割 → 名(別名のファイルを差し込めないように名で縛る)。
ROLE_NAMES: dict[str, str] = {
    **WORLD_FILES,
    "area_axes": "area_axes_v0.json",
    "time_dist_12": "time_dist_12.json",
    "commute_r3": "commute_time_dist_r3.json",
    "ssb_8_1": "ssb2021_activity_prior_v0.json",
    "calib_anchors": "calib_anchors_v0.json",
    "w20": "w20_calendar_1a.parquet",
}
#: 錨の印(R-115 §2)。
MARKS: dict[str, dict[str, str]] = {
    "3-1": {"a1": "〔写〕計画上の在圏", "a2": "〔部〕W12 から組む在圏の形", "a3": "〔非〕PT c-2(材料待ち)"},
    "3-2": {"a1": "〔写〕W16 の体数", "a2": "〔写〕計画上の在圏の比", "a3": "〔非〕中核 9 町丁目の昼夜間人口比"},
    "3-3": {"a1": "〔写〕W12 の線の割合", "a2": "〔部〕W12 の時刻の形", "a3": "〔非〕PT c-2(材料待ち)",
            "a4": "〔灰〕線ごとに違う材料(親の判断待ち・読まない)"},
    "3-4": {"a1": "〔写〕第 31 表+arrival_lead(W17 v2 の作り方)", "a2": "〔写〕W17 v2 の勤務の行の始まり",
            "a3": "〔部〕第 8-1 表 関東大都市圏の仕事の立ち上がり", "a4": "〔非〕PT c-2(材料待ち)",
            "a5": "〔写〕W20 暦 1a の始業(第 31/36 表の逆算+通勤=構築側の錨の写し・3-1)"},
}
PENDING_MATERIAL = {"value": None, "status": "材料待ち(PT c-2 は tokyo-pt.jp の同意ページ越し=手元に無い・器だけ)"}
PENDING_GREY = {"value": None, "status": "親の判断待ち(〔灰〕=boundary_counts と同じ元・読まない・R-115 §5 空欄 1)"}


# ====================================================================== 小道具
def hm(minute: float | int | None) -> str | None:
    if minute is None or (isinstance(minute, float) and math.isnan(minute)):
        return None
    m = int(round(float(minute)))
    return f"{m // MINUTES_PER_HOUR}:{m % MINUTES_PER_HOUR:02d}"


def _f(x: Any, nd: int = 4) -> Any:
    if x is None:
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        return None if math.isnan(v) or math.isinf(v) else round(v, nd)
    return x


def jsd(p: Sequence[float], q: Sequence[float]) -> float | None:
    """Jensen-Shannon divergence(底 2・形だけ)。どちらかが空なら None。"""
    a = np.asarray(p, dtype=np.float64)
    b = np.asarray(q, dtype=np.float64)
    sa, sb = a.sum(), b.sum()
    if sa <= 0 or sb <= 0:
        return None
    a, b = a / sa, b / sb
    m = 0.5 * (a + b)

    def _kl(x: np.ndarray, y: np.ndarray) -> float:
        nz = x > 0
        return float(np.sum(x[nz] * np.log2(x[nz] / y[nz])))

    return 0.5 * _kl(a, m) + 0.5 * _kl(b, m)


def ratio(a: float, b: float) -> float | None:
    return None if b <= 0 else float(a) / float(b)


def peak_hour(series: Sequence[float]) -> int | None:
    """KDDI の軸(5〜28 時)の系列 → ピーク時刻(同点は早い方)。全部 0 なら None。"""
    s = np.asarray(series, dtype=np.float64)
    if s.size == 0 or not np.any(s > 0):
        return None
    return int(KDDI_HOURS[int(np.argmax(s))])


def share(series: Sequence[float]) -> list[float]:
    s = np.asarray(series, dtype=np.float64)
    t = s.sum()
    return [0.0] * s.size if t <= 0 else [float(v) for v in (s / t)]


def wquantiles(x: np.ndarray, w: np.ndarray, qs: Sequence[float]) -> list[float | None]:
    if x.size == 0 or float(w.sum()) <= 0:
        return [None] * len(qs)
    o = np.argsort(x, kind="stable")
    xs, ws = x[o].astype(np.float64), w[o].astype(np.float64)
    c = np.cumsum(ws)
    tot = c[-1]
    out = []
    for q in qs:
        j = int(np.searchsorted(c, q * tot, side="left"))
        out.append(float(xs[min(j, xs.size - 1)]))
    return out


def dist_stats(minutes: np.ndarray, weights: np.ndarray) -> dict[str, Any]:
    """始まりの分布(15 分)。平均・分位・:00/:30 の率・最頻のビン・15 分の構成(重みつき)。"""
    x = np.asarray(minutes, dtype=np.int64)
    w = np.asarray(weights, dtype=np.float64)
    if x.size == 0 or float(w.sum()) <= 0:
        return {"n": int(x.size), "mean": None, "hist15": [0.0] * N_SLOTS}
    xc = np.clip(x, 0, MINUTES_PER_DAY - 1)
    hist = np.bincount(xc // SLOT_MIN, weights=w, minlength=N_SLOTS)[:N_SLOTS]
    hist = hist / hist.sum()
    q = wquantiles(x, w, (0.10, 0.25, 0.50, 0.75, 0.90))
    mode = int(np.argmax(hist))
    return {
        "n": int(x.size),
        "weight": _f(w.sum(), 2),
        "mean": _f(float(np.sum(w * x) / w.sum()), 2),
        "mean_hm": hm(float(np.sum(w * x) / w.sum())),
        "p10": hm(q[0]), "p25": hm(q[1]), "p50": hm(q[2]), "p75": hm(q[3]), "p90": hm(q[4]),
        "p50_min": _f(q[2], 1),
        "on_00_30": _f(float(w[(x % 30) == 0].sum() / w.sum())),
        "mode_bin": hm(mode * SLOT_MIN),
        "mode_share": _f(float(hist[mode])),
        "hist15": [_f(v, 6) for v in hist],
    }


def rise_slot(curve: Sequence[float], frac: float = RISE_FRACTION) -> int | None:
    """15 分の率の曲線 → 1 日の最大の ``frac`` を初めて超える 15 分の索引(全部 0 なら None)。"""
    c = np.asarray(curve, dtype=np.float64)
    if c.size == 0 or not np.any(c > 0):
        return None
    thr = frac * float(c.max())
    return int(np.flatnonzero(c >= thr)[0])


def git_head(repo: Path = REPO) -> dict[str, Any]:
    def _run(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True,
                                  encoding="utf-8", check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):  # pragma: no cover
            return ""
    src_diff = [s for s in _run("diff", "--name-only", "HEAD", "--", "src").splitlines() if s]
    return {"commit": _run("rev-parse", "--short", "HEAD"), "src_diff_files_vs_head": len(src_diff)}


# ====================================================================== 記録の段(エンジン不変)
def _plan_from_executor(pe: Any, pop: Any, n_ticks: int) -> dict[str, np.ndarray]:
    """``PlanExecutor`` の参照 → 計画上のセル(刻み × 体)・計画の到着・W17 の勤務の行の始まり。読むだけ。"""
    from shibuya.agents.weekly import ACTIVITY_WORDS, PLACE_WORDS
    from shibuya.engine.presence import EventType, _day_rows

    work_pk, school_pk, home_pk = (PLACE_WORDS.index(w) for w in ("職場", "学校", "自宅"))
    act_work = ACTIVITY_WORDS.index("勤務")
    n = int(pe.n)
    weekly = pe.weekly
    rows, idx, _ = _day_rows(weekly, int(pe.day_index))
    s = np.asarray(weekly.start_min, dtype=np.int64)[idx]
    e = np.asarray(weekly.end_min, dtype=np.int64)[idx]
    act = np.asarray(weekly.activity, dtype=np.int64)[idx]
    pk = np.asarray(weekly.place_kind, dtype=np.int64)[idx]
    cell = np.asarray(weekly.target_cell, dtype=np.int64)[idx].copy()
    wc = np.asarray(pop.work_cell, dtype=np.int64)
    sc = np.asarray(pop.school_cell, dtype=np.int64)
    hc = np.asarray(pop.home_cell, dtype=np.int64)
    neg = cell < 0
    cell = np.where(neg & (pk == work_pk), wc[np.minimum(rows, wc.size - 1)], cell)
    cell = np.where(neg & (pk == school_pk), sc[np.minimum(rows, sc.size - 1)], cell)
    cell = np.where(neg & (pk == home_pk), hc[np.minimum(rows, hc.size - 1)], cell)
    row_cell = np.full((n_ticks, n), -2, dtype=np.int16)
    order = np.lexsort((s, rows))
    for j in order.tolist():  # 逐次ループ宣言: その日の行の数(5,000 体で約 4.5 万)
        lo, hi = max(0, int(s[j])), min(n_ticks, int(e[j]))
        if hi > lo and int(rows[j]) < n:
            row_cell[lo:hi, int(rows[j])] = int(cell[j]) if cell[j] >= 0 else -2
    blocks = pe.blocks
    in_block = np.zeros((n_ticks, n), dtype=bool)
    b_agent = np.asarray(blocks.agent_of_block, dtype=np.int64)
    bs = np.asarray(blocks.start, dtype=np.int64)
    be = np.asarray(blocks.end, dtype=np.int64)
    for b in range(int(blocks.n_blocks)):  # 逐次ループ宣言: ブロックの数(5,000 体で約 1 万)
        lo, hi = max(0, int(bs[b])), min(n_ticks, int(be[b]))
        if hi > lo and int(b_agent[b]) < n:
            in_block[lo:hi, int(b_agent[b])] = True
    plan_cells = np.where(in_block, row_cell, np.int16(-1)).astype(np.int16)
    # W17 の勤務の行の始まり(その日に初めて 勤務 の行が始まる分・0 時から続く行は除く)
    big = 10 ** 6
    first = np.full(n, big, dtype=np.int64)
    m = (act == act_work) & (s > 0) & (rows < n)
    if m.any():
        np.minimum.at(first, rows[m], s[m])
    absent = np.asarray(getattr(pe, "absent", np.zeros(n, dtype=bool)), dtype=bool)
    work_start = np.where((first < big) & ~absent[:n], first, -1).astype(np.int32)
    sel = np.asarray(pe.ev_type) == EventType.ARRIVE
    return {
        "plan_cells": plan_cells,
        "plan_work_start": work_start,
        "plan_arrive_tick": np.asarray(pe.ev_tick, dtype=np.int32)[sel],
        "plan_arrive_agent": np.asarray(pe.ev_agent, dtype=np.int32)[sel],
    }


POP_COLS: tuple[str, ...] = ("source_agent_id", "kind", "age", "is_foreign", "home_cell", "work_cell", "school_cell",
                             "direction_node", "pool_layer", "pool_index")
MANIFEST_KEYS: tuple[str, ...] = ("bridges_count", "rules_version", "bridges_version", "run_kind", "hash_scheme",
                                  "population_seed", "environment_seed", "clock_kind", "step_seconds")


def opened_listing(paths: Sequence[str]) -> list[dict[str, Any]]:
    """ランの段で開いた道筋の一覧。計器の段で落とす語(〔検〕・〔灰〕)に当たる行に印を付ける(値は読まない)。"""
    rows = []
    for p in sorted(set(paths)):
        hit = deny_hit(p, GAUGE_EXTRA_DENY_TOKENS)
        rows.append({"path": p, "gauge_deny_token": hit})
    return rows


def record(arm: str, *, out_path: Path, n_agents: int = 5_000, seed: int = 1, world_dir: str = DEFAULTS["world"],
           use_recorder: bool = True) -> dict[str, Any]:
    """1 腕のラン → 体の journal(``anchor_journal_*.npz``)。``use_recorder=False`` は包まずに回す(不変の確かめ)。"""
    import attr_arms as A
    from shibuya import cli
    from shibuya.engine import presence as P
    from shibuya.engine import run as RUN

    import shibuya

    kw = dict(ARMS[arm])
    cap: dict[str, Any] = {}
    rec = A.AgentCellRecorder(every=1)
    orig_init = P.PlanExecutor.__init__
    orig_pop = RUN._resolve_population

    def _init(self: Any, *a: Any, **k: Any) -> None:
        orig_init(self, *a, **k)
        cap.setdefault("pe", self)

    def _pop(*a: Any, **k: Any) -> Any:
        out = orig_pop(*a, **k)
        cap.setdefault("pop", out)
        return out

    t0 = time.perf_counter()
    # 検収 M1: ランの間に Python の open が開いたファイル(data・docs・tools・世界資産の下)を控える。封印の層は落とす
    run_guard = ReadGuard.sealed_only(track_roots=[REPO / "data", REPO / "docs", REPO / "tools", Path(world_dir)],
                                      repo_root=REPO)
    if use_recorder:
        P.PlanExecutor.__init__ = _init  # type: ignore[method-assign]
        RUN._resolve_population = _pop
        rec.attach()
    try:
        with run_guard.active():
            res = cli.run(n_agents=n_agents, seed=seed, world_dir=world_dir, **kw)
    finally:
        if use_recorder:
            rec.detach()
            P.PlanExecutor.__init__ = orig_init  # type: ignore[method-assign]
            RUN._resolve_population = orig_pop
    wall = time.perf_counter() - t0
    mf = res.run_manifest_fields()
    head = git_head()
    meta: dict[str, Any] = {
        "schema": JOURNAL_SCHEMA, "arm": arm, "kwargs": kw, "n_agents": int(n_agents), "seed": int(seed),
        "world_dir": str(world_dir).replace("\\", "/"), "final_hash": str(res.final_hash)[:16],
        "llm_calls": int(res.llm_calls), "manifest": {k: mf.get(k) for k in MANIFEST_KEYS},
        "commit": head["commit"], "src_diff_files_vs_head": head["src_diff_files_vs_head"],
        "src_is_worktree": Path(shibuya.__file__).resolve().parents[1] == (REPO / "src").resolve(),
        "tick_seconds": STEP_SECONDS, "start_hour": 0, "recorder": bool(use_recorder),
        "wall_s_nondeterministic": round(wall, 1),
        "record_opened_files": opened_listing(run_guard.opened),
    }
    if not use_recorder:
        return meta
    pe, pop = cap.get("pe"), cap.get("pop")
    if pe is None or pop is None:
        raise RuntimeError("計画実行層か母集団の参照が取れなかった(計画実行層 off のラン・母集団の無い世界は対象外)")
    ticks = np.asarray(rec.ticks, dtype=np.int64)
    cells = np.stack(rec.cells).astype(np.int16)
    transit = np.stack(rec.transit).astype(np.int8)
    kind = np.asarray(rec.kind, dtype=np.int8)
    if not np.array_equal(kind[: pop.n].astype(np.int64), np.asarray(pop.kind, dtype=np.int64)[: kind.size]):
        raise ValueError("journal の種別が母集団の行と食い違う(行 i = 体 i の規約が崩れている)")
    plan = _plan_from_executor(pe, pop, int(ticks.size))
    meta["plan"] = {"day_index": int(pe.day_index), "derive_rule": str(pe.derive_rule), "exit_mode": str(pe.exit_mode),
                    "n_blocks": int(pe.blocks.n_blocks), "absent": int(np.asarray(pe.absent).sum()),
                    "n_plan_arrivals": int(plan["plan_arrive_tick"].size)}
    arrays = {f"pop_{c}": np.asarray(getattr(pop, c)) for c in POP_COLS}
    arrays.update(ticks=ticks, cells=cells, transit=transit, kind=kind, **plan)
    meta["journal_arrays_sha16"] = arrays_sha16(arrays)
    out_path = Path(out_path)
    if not (out_path.name.startswith(JOURNAL_PREFIX) and out_path.name.endswith(JOURNAL_SUFFIX)):
        raise ValueError(f"記録の名は {JOURNAL_PREFIX}*{JOURNAL_SUFFIX}(許可の一覧の形)")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, **arrays, meta=np.asarray(json.dumps(meta, ensure_ascii=False)))
    meta["journal"] = out_path.name
    meta["journal_md5"] = hashlib.md5(out_path.read_bytes()).hexdigest()
    return meta


# ====================================================================== 読み込み(許可の一覧)
def resolve_paths(args: Mapping[str, Any] | None = None) -> dict[str, Path]:
    a = dict(args or {})
    out = {k: Path(a.get(k) or v) for k, v in DEFAULTS.items()}
    return {k: (p if p.is_absolute() else REPO / p) for k, p in out.items()}


def make_guard(paths: Mapping[str, Path], *, out_dir: Path | None = None,
               prev_dirs: Sequence[Path] = ()) -> ReadGuard:
    """許可の一覧を組む(役割ごとに名で縛る・封印の語は組んだ時点で落ちる)。"""
    files: dict[str, Path] = {r: Path(paths["world"]) / n for r, n in WORLD_FILES.items()}
    for r in ("area_axes", "time_dist_12", "commute_r3", "ssb_8_1", "calib_anchors"):
        files[r] = Path(paths[r])
    if paths.get("w20") is not None and Path(paths["w20"]).is_file():  # 〔3-1〕源 W20(組んだ資産があるときだけ)
        files["w20"] = Path(paths["w20"])
    for r, p in files.items():
        if Path(p).name != ROLE_NAMES[r]:
            raise NotAllowedError(f"役割 {r} のファイルの名は {ROLE_NAMES[r]}(いま {Path(p).name})")
    dirs: dict[str, Path] = {"pool": Path(paths["pool"])}
    if out_dir is not None:
        dirs["out"] = Path(out_dir)
    for i, d in enumerate(prev_dirs):
        dirs[f"prev{i}"] = Path(d)
    protect = [REPO / "data", REPO / "docs", Path(paths["world"]), Path(paths["pool"])]
    return ReadGuard(files=files, dirs=dirs, protect=protect, repo_root=REPO)


@dataclass
class Static:
    """構築側の入力(2 腕で共通)。"""

    area_of_cell: np.ndarray
    cell_ix: np.ndarray
    cell_iy: np.ndarray
    place_ids: list[str]
    area_meta: dict[str, Any]
    w16: dict[str, np.ndarray]
    chome: dict[str, np.ndarray]
    nodes: dict[str, np.ndarray]
    weights: dict[str, np.ndarray]
    time_dist: dict[str, Any]
    commute: dict[str, Any]
    ssb: dict[str, Any]
    calib: dict[str, Any]
    pool_root: Path
    dilated: dict[str, np.ndarray] = field(default_factory=dict)
    cache: dict[str, Any] = field(default_factory=dict, repr=False)
    #: 〔第 3 期 3-1〕3-4 の源「W20」(W20cal の週の表・許可の一覧の役割 w20・無ければ None)。
    w20_path: Path | None = None


def _cached(S: Static, key: str, fn: Any) -> Any:
    """2 腕で共通の錨の計算は 1 回だけ(``Static.cache``)。"""
    if key not in S.cache:
        S.cache[key] = fn()
    return S.cache[key]


def load_static(guard: ReadGuard, paths: Mapping[str, Path], *, dilate: Sequence[float] = (-50.0, 50.0)) -> Static:
    cells = guard.read_parquet(guard.files["W2_cells"], ["place_id", "ix", "iy"])
    axes = guard.read_json(guard.files["area_axes"])
    pids = [str(v) for v in cells["place_id"].tolist()]
    amap = c7lib.build_area_map(pids, cells["ix"], cells["iy"], axes)
    gate = c7lib.area_ha_gate(amap, axes)
    dil = {f"{d:+.0f}m": np.asarray(c7lib.build_area_map(pids, cells["ix"], cells["iy"], axes, dilate_m=d).area_of_cell,
                                    dtype=np.int64) for d in dilate}
    w16 = guard.read_parquet(guard.files["W16"], ["agent_id", "kind", "age", "is_foreign", "home_cell", "work_cell",
                                                  "school_cell", "direction_node", "chome_key"])
    return Static(
        area_of_cell=np.asarray(amap.area_of_cell, dtype=np.int64),
        cell_ix=np.asarray(cells["ix"], dtype=np.int64), cell_iy=np.asarray(cells["iy"], dtype=np.int64),
        place_ids=pids,
        area_meta={"counts": amap.counts(), "area_ha": amap.area_ha(), "area_ha_gate_ok": bool(gate["ok"]),
                   "axes_version": axes.get("version"), "axes_status": axes.get("status")},
        w16=w16,
        chome=guard.read_parquet(guard.files["W16_chome"], ["key_code", "s_name"]),
        nodes=guard.read_parquet(guard.files["W12_nodes"], ["node_id", "kind", "daily_inflow", "daily_outflow"]),
        weights=guard.read_parquet(guard.files["W12_weights"], ["node_id", "hour", "weight"]),
        time_dist=guard.read_json(guard.files["time_dist_12"]),
        commute=guard.read_json(guard.files["commute_r3"]),
        ssb=guard.read_json(guard.files["ssb_8_1"]),
        calib=guard.read_json(guard.files["calib_anchors"]),
        pool_root=Path(paths["pool"]),
        dilated=dil,
        w20_path=guard.files.get("w20"),
    )


def arrays_sha16(arrays: Mapping[str, Any]) -> str:
    """journal の配列だけの sha256(先頭 16 桁)。meta(壁時計を含む)は入れない=同じランなら同じ値(検収 L10)。"""
    h = hashlib.sha256()
    for k in sorted(a for a in arrays if a != "meta"):
        v = np.ascontiguousarray(np.asarray(arrays[k]))
        h.update(k.encode("utf-8"))
        h.update(str(v.dtype).encode("ascii"))
        h.update(str(v.shape).encode("ascii"))
        h.update(v.tobytes())
    return h.hexdigest()[:16]


def load_journal(guard: ReadGuard, path: Path) -> dict[str, Any]:
    z = guard.np_load(path)
    meta = json.loads(str(z.pop("meta")))
    if meta.get("schema") != JOURNAL_SCHEMA:
        raise ValueError(f"記録の形が違う: {meta.get('schema')!r}")
    sha = arrays_sha16(z)
    if meta.get("journal_arrays_sha16") not in (None, sha):
        raise ValueError("journal の配列が meta の hash と違う(壊れた記録)")
    guard.annotate(path, arrays_sha16=sha)
    z["meta"] = meta
    return z


# ====================================================================== 純関数(4 つの量の部品)
def cells_to_area(cells: np.ndarray, area_of_cell: np.ndarray) -> np.ndarray:
    c = np.asarray(cells, dtype=np.int64)
    ok = (c >= 0) & (c < area_of_cell.size)
    return np.where(ok, area_of_cell[np.where(ok, c, 0)], -1)


def expansion_factors(full_kind: np.ndarray, sample_kind: np.ndarray, n_kinds: int = 9) -> np.ndarray:
    """拡大係数 ω_k = N_k / n_k(標本に居ない種別は 0)→ 体ごとの ω。"""
    full = np.bincount(np.asarray(full_kind, dtype=np.int64), minlength=n_kinds)[:n_kinds].astype(np.float64)
    samp = np.bincount(np.asarray(sample_kind, dtype=np.int64), minlength=n_kinds)[:n_kinds].astype(np.float64)
    omega = np.where(samp > 0, full / np.maximum(samp, 1.0), 0.0)
    return omega[np.clip(np.asarray(sample_kind, dtype=np.int64), 0, n_kinds - 1)]


def population_masks(kind: np.ndarray, age: np.ndarray, is_foreign: np.ndarray) -> dict[str, np.ndarray]:
    """v1.4 の母集団 P′(本則)・P(kind≠7・継続)・全員。"""
    k = np.asarray(kind, dtype=np.int64)
    adult = np.asarray(age, dtype=np.int64) >= ADULT_AGE
    fo = np.asarray(is_foreign, dtype=bool)
    return {"P_prime": adult & ~fo, "P": adult & (k != FOREIGN_KIND), "all": np.ones(k.size, dtype=bool)}


def area_and_stage(cells: np.ndarray, transit: np.ndarray | None, area_of_cell: np.ndarray, *,
                   plan: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """刻み × 体 → (エリアの索引 or −1, 舞台に居るか)。

    ランの記録: 舞台=transit_state 0 かつ cell ≥ 0。計画: 舞台=計画のセル ≠ −1(−2=舞台の中・セル不明)。
    """
    c = np.asarray(cells, dtype=np.int64)
    if plan:
        stage = c != -1
    else:
        stage = (np.asarray(transit, dtype=np.int64) == 0) & (c >= 0)
    area = np.where(stage, cells_to_area(c, area_of_cell), -1)
    return area.astype(np.int8), stage


def col_masks(area_row: np.ndarray, stage_row: np.ndarray) -> np.ndarray:
    """1 刻みぶん → (7, n) の列の印(5 エリア・5 エリア計・舞台)。"""
    a = np.asarray(area_row)
    out = np.empty((len(COLS), a.size), dtype=bool)
    for i in range(len(AREA_IDS)):
        out[i] = a == i
    out[len(AREA_IDS)] = a >= 0
    out[len(AREA_IDS) + 1] = np.asarray(stage_row, dtype=bool)
    return out


def hour_minutes(area_t: np.ndarray, stage_t: np.ndarray, ticks: np.ndarray, tick_seconds: int = STEP_SECONDS
                 ) -> tuple[np.ndarray, np.ndarray]:
    """(時 24, 列 7, 体)の居た分と、列ごとの 1 日の最長の連続[刻み]。"""
    t = np.asarray(ticks, dtype=np.int64)
    hour = ((t * int(tick_seconds)) // SECONDS_PER_HOUR) % HOURS_PER_DAY
    n = area_t.shape[1]
    hmn = np.zeros((HOURS_PER_DAY, len(COLS), n), dtype=np.int32)
    cur = np.zeros((len(COLS), n), dtype=np.int32)
    best = np.zeros((len(COLS), n), dtype=np.int32)
    for j in range(t.size):  # 逐次ループ宣言: 刻みの数(1 日 1,440)× ベクトル
        m = col_masks(area_t[j], stage_t[j])
        hmn[hour[j]] += m
        cur = np.where(m, cur + 1, 0)
        np.maximum(best, cur, out=best)
    return hmn, best


def daily_qualified(hmn: np.ndarray, best: np.ndarray, dwell: str, tick_seconds: int = STEP_SECONDS) -> np.ndarray:
    """1 日単位の 30 分(``sum``=合計=本則 / ``cont``=連続=腕)→ (7, n) bool。"""
    need = int(math.ceil(DWELL_MIN * SECONDS_PER_MINUTE / float(tick_seconds)))
    if dwell == "sum":
        return hmn.sum(axis=0) >= need
    if dwell == "cont":
        return best >= need
    raise ValueError(f"dwell は sum / cont(いま {dwell!r})")


def presence_hourly(hmn: np.ndarray, qualified: np.ndarray, weight: np.ndarray, keep: np.ndarray, theta: int,
                    tick_seconds: int = STEP_SECONDS) -> np.ndarray:
    """N^θ_{c,h} = Σ_i ω_i · 1[i∈母集団] · 1[1 日 30 分] · 1[その時間帯に θ 分以上]。KDDI の軸 (7, 24)。

    θ は分で受け、居た刻みの数 × 刻みの秒と秒で比べる(検収 L4=刻みが 60 秒でなくても θ の分がずれない)。
    """
    w = np.asarray(weight, dtype=np.float64) * np.asarray(keep, dtype=bool)
    base = qualified * w[None, :]                                # (7, n)
    present_s = hmn.astype(np.int64) * int(tick_seconds)
    out = np.einsum("hcn,cn->ch", (present_s >= int(theta) * SECONDS_PER_MINUTE).astype(np.float64), base)
    return out[:, HOUR_IDX]


def presence_on_hour(area_t: np.ndarray, stage_t: np.ndarray, ticks: np.ndarray, weight: np.ndarray,
                     keep: np.ndarray, tick_seconds: int = STEP_SECONDS) -> np.ndarray:
    """正時の標本(v1.3 の数え方・1 日の条件なし)。KDDI の軸 (7, 24)。"""
    t = np.asarray(ticks, dtype=np.int64)
    sec = t * int(tick_seconds)
    w = np.asarray(weight, dtype=np.float64) * np.asarray(keep, dtype=bool)
    out = np.zeros((len(COLS), HOURS_PER_DAY))
    nh = np.zeros(HOURS_PER_DAY)
    for j in np.flatnonzero(sec % SECONDS_PER_HOUR == 0).tolist():  # 逐次ループ宣言: 正時の標本(≤ 24)
        h = int((sec[j] // SECONDS_PER_HOUR) % HOURS_PER_DAY)
        out[:, h] += col_masks(area_t[j], stage_t[j]) @ w
        nh[h] += 1.0
    out = out / np.maximum(nh, 1.0)[None, :]
    return out[:, HOUR_IDX]


def peaks_block(N: np.ndarray) -> dict[str, Any]:
    pk = {c: peak_hour(N[i]) for i, c in enumerate(COLS)}
    order = sorted((a for a in AREA_IDS if pk[a] is not None), key=lambda a: (pk[a], AREA_IDS.index(a)))
    return {"peak": pk, "order": order, "hour_share": {c: [_f(v, 6) for v in share(N[i])] for i, c in enumerate(COLS)},
            "level": {c: _f(float(N[i].sum()), 1) for i, c in enumerate(COLS)}}


def attr_by_area(home_area: np.ndarray, work_area: np.ndarray, school_area: np.ndarray) -> np.ndarray:
    """(n, 5) の属性(0=勤務者・1=居住者・2=来街者)。居住地が先(R-56 §2 の判定順)。"""
    x = np.arange(len(AREA_IDS))[None, :]
    home = home_area[:, None] == x
    work = (work_area[:, None] == x) | (school_area[:, None] == x)
    out = np.full((home_area.size, len(AREA_IDS)), 2, dtype=np.int64)
    out[work] = 0
    out[home] = 1
    return out


def attr_by_kind(kind: np.ndarray) -> np.ndarray:
    idx = {a: i for i, a in enumerate(c7lib.ATTR_IDS)}
    lut = np.asarray([idx[c7lib.KIND_TO_ATTR.get(k, "visitor")] for k in range(9)], dtype=np.int64)
    a = lut[np.clip(np.asarray(kind, dtype=np.int64), 0, 8)]
    return np.repeat(a[:, None], len(AREA_IDS), axis=1)


def ratio_block(qualified: np.ndarray, attr: np.ndarray, weight: np.ndarray, keep: np.ndarray,
                foreign: np.ndarray | None = None) -> dict[str, Any]:
    """1 日単位の在圏(5 エリア)を属性で分けた数と V/Res・W/Res。計=エリアの数の和。"""
    w = np.asarray(weight, dtype=np.float64)
    k = np.asarray(keep, dtype=bool)
    rows: dict[str, Any] = {}
    tot = np.zeros(3)
    tot_n = np.zeros(3, dtype=np.int64)
    tot_fo = 0.0
    for a, name in enumerate(AREA_IDS):
        q = qualified[a] & k
        c = np.asarray([float(w[q & (attr[:, a] == j)].sum()) for j in range(3)])
        nn = np.asarray([int((q & (attr[:, a] == j)).sum()) for j in range(3)])
        fo = float(w[qualified[a] & foreign].sum()) if foreign is not None else None
        rows[name] = {"W": _f(c[0], 1), "Res": _f(c[1], 1), "V": _f(c[2], 1), "n": nn.tolist(),
                      "V_per_Res": _f(ratio(c[2], c[1])), "W_per_Res": _f(ratio(c[0], c[1])),
                      "V_per_W": _f(ratio(c[2], c[0])), "foreign": _f(fo, 1)}
        tot += c
        tot_n += nn
        tot_fo += fo or 0.0
    rows["total"] = {"W": _f(tot[0], 1), "Res": _f(tot[1], 1), "V": _f(tot[2], 1), "n": tot_n.tolist(),
                     "V_per_Res": _f(ratio(tot[2], tot[1])), "W_per_Res": _f(ratio(tot[0], tot[1])),
                     "V_per_W": _f(ratio(tot[2], tot[0])), "foreign": _f(tot_fo, 1) if foreign is not None else None}
    return rows


def plan_unknown_shares(plan_cells: np.ndarray, stage_p: np.ndarray, kind: np.ndarray) -> dict[str, Any]:
    """計画で舞台の中に居るがセルが分からない(−2)体分の割合(全体・来街の種別・それ以外)。"""
    unk = (np.asarray(plan_cells) == -2) & stage_p
    vis = np.isin(np.asarray(kind, dtype=np.int64), VISITOR_KINDS)

    def _r(sel: np.ndarray) -> float | None:
        st = float(stage_p[:, sel].sum())
        return None if st <= 0 else _f(float(unk[:, sel].sum()) / st)

    return {"all": _r(np.ones(vis.size, dtype=bool)), "visitor_kinds": _r(vis), "other_kinds": _r(~vis)}


def blank_visitor(block: Mapping[str, Any]) -> dict[str, Any]:
    """計画の比の表から来街者の列を空にする(セルが分からない=0 ではない)。"""
    out = {}
    for k, r in block.items():
        out[k] = {**r, "V": None, "V_per_Res": None, "V_per_W": None,
                  "note": "計画の来街の行は target_cell を持たない=エリアに置けない(空)"}
    return out


def w16_static_ratios(S: Static) -> dict[str, Any]:
    """3-2 錨 1〔写〕: W16 の体数(kind の写像は舞台全体・area の写像はエリアごとの W/Res)。"""
    w = S.w16
    kind = np.asarray(w["kind"], dtype=np.int64)
    pm = population_masks(kind, w["age"], w["is_foreign"])
    attr = attr_by_kind(kind)[:, 0]
    kind_rows = {}
    for pname in ("P_prime", "P", "all"):
        k = pm[pname]
        c = [int((k & (attr == j)).sum()) for j in range(3)]
        kind_rows[pname] = {"W": c[0], "Res": c[1], "V": c[2], "V_per_Res": _f(ratio(c[2], c[1])),
                            "W_per_Res": _f(ratio(c[0], c[1]))}
    ha = cells_to_area(w["home_cell"], S.area_of_cell)
    wa = cells_to_area(w["work_cell"], S.area_of_cell)
    sa = cells_to_area(w["school_cell"], S.area_of_cell)
    k = pm["P_prime"]
    area_rows: dict[str, Any] = {}
    tr = tw = 0
    for a, name in enumerate(AREA_IDS):
        res = int((k & (ha == a)).sum())
        wk = int((k & (ha != a) & ((wa == a) | (sa == a))).sum())
        area_rows[name] = {"Res": res, "W": wk, "W_per_Res": _f(ratio(wk, res)), "V": None}
        tr += res
        tw += wk
    area_rows["total"] = {"Res": tr, "W": tw, "W_per_Res": _f(ratio(tw, tr)), "V": None}
    return {"kind_map_stage": kind_rows, "area_map": area_rows,
            "note": "area の写像では「来る人」(来街者)を W16 の体数から数えられない=V は空(錨 2 で見る)"}


# ---------------------------------------------------------------------- 中核 9 町丁目(3-2 錨 3〔非〕)
def chome_of_cells(S: Static) -> np.ndarray:
    """セル → 町丁目の符号(W16 の居住者の chome_key の多数決・居住者の居ないセルは最も近いセル)。"""
    w = S.w16
    kind = np.asarray(w["kind"], dtype=np.int64)
    hc = np.asarray(w["home_cell"], dtype=np.int64)
    keys = np.asarray(w["chome_key"], dtype=object)
    sel = np.isin(kind, (2, 3)) & (hc >= 0) & (hc < S.area_of_cell.size) & (keys != "")
    votes: dict[tuple[int, int], dict[str, int]] = {}
    for c, kk in zip(hc[sel].tolist(), keys[sel].tolist()):  # 逐次ループ宣言: 居住者の数(W16 で約 4.4 万)
        d = votes.setdefault((int(S.cell_ix[c]), int(S.cell_iy[c])), {})
        d[str(kk)] = d.get(str(kk), 0) + 1
    # 多数決(同数は符号の小さい方)。格子 (ix, iy) で寄せる=同じ地面の UG/DECK も同じ町丁目
    mapped = {g: sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for g, d in votes.items()}
    out = np.full(S.area_of_cell.size, "", dtype=object)
    if not mapped:
        return out
    grid = list(mapped)
    gx = np.asarray([g[0] for g in grid], dtype=np.int64)
    gy = np.asarray([g[1] for g in grid], dtype=np.int64)
    gk = [mapped[g] for g in grid]
    rank = np.asarray([sorted(set(gk)).index(k) for k in gk], dtype=np.int64)
    for i in range(out.size):  # 逐次ループ宣言: セルの数(520)
        g = (int(S.cell_ix[i]), int(S.cell_iy[i]))
        if g in mapped:
            out[i] = mapped[g]
            continue
        d2 = (gx - g[0]) ** 2 + (gy - g[1]) ** 2  # 居住者の居ないセル=最も近い格子の町丁目(同距離は符号の小さい方)
        out[i] = gk[int(np.lexsort((rank, d2))[0])]
    return out


def core9_keys(S: Static) -> list[str]:
    names = list(S.calib["core9"]["chome_names"])
    tbl = {str(n): str(k) for k, n in zip(S.chome["key_code"].tolist(), S.chome["s_name"].tolist())}
    missing = [n for n in names if n not in tbl]
    if missing:
        raise ValueError(f"中核 9 町丁目の名が W16 の町丁目表に無い: {missing}")
    return [tbl[n] for n in names]


def core9_w16_static(S: Static, core_cell: np.ndarray) -> dict[str, Any]:
    """W16 の静的な昼夜間人口比(夜=居住者・昼=夜−流出+流入・全年齢)。"""
    w = S.w16
    kind = np.asarray(w["kind"], dtype=np.int64)
    keys = set(core9_keys(S))
    res = np.isin(kind, (2, 3)) & np.asarray([str(k) in keys for k in w["chome_key"].tolist()])
    wc, sc = np.asarray(w["work_cell"], dtype=np.int64), np.asarray(w["school_cell"], dtype=np.int64)
    dn = np.asarray(w["direction_node"], dtype=np.int64)

    def _in(c: np.ndarray) -> np.ndarray:
        ok = (c >= 0) & (c < core_cell.size)
        return ok & core_cell[np.where(ok, c, 0)]

    out_flow = res & (((wc >= 0) & ~_in(wc)) | ((sc >= 0) & ~_in(sc)) | ((wc < 0) & (sc < 0) & (dn >= 0)))
    in_flow = ~res & ~np.isin(kind, VISITOR_KINDS) & (_in(wc) | _in(sc))
    night = int(res.sum())
    day = night - int(out_flow.sum()) + int(in_flow.sum())
    return {"night": night, "outflow": int(out_flow.sum()), "inflow": int(in_flow.sum()), "day": day,
            "ratio": _f(ratio(day, night), 3)}


def core9_run(cells_t: np.ndarray, stage_t: np.ndarray, ticks: np.ndarray, J: Mapping[str, Any], weight: np.ndarray,
              core_cell: np.ndarray, sample_core_res: np.ndarray, tick_seconds: int = STEP_SECONDS) -> dict[str, Any]:
    """ランの昼夜間の比: 夜=中核 9 の居住者(ω)・昼=居住者か勤務・通学先が中核 9 の体で 10〜16 時に 30 分以上居た(ω)。"""
    t = np.asarray(ticks, dtype=np.int64) * int(tick_seconds) // SECONDS_PER_MINUTE
    win = (t >= CORE9_DAY_WINDOW[0]) & (t < CORE9_DAY_WINDOW[1])
    c = np.asarray(cells_t, dtype=np.int64)[win]
    ok = np.asarray(stage_t, dtype=bool)[win] & (c >= 0) & (c < core_cell.size)
    inside = ok & core_cell[np.where(ok, c, 0)]
    minutes = inside.sum(axis=0)
    kind = np.asarray(J["pop_kind"], dtype=np.int64)
    wc, sc = np.asarray(J["pop_work_cell"], dtype=np.int64), np.asarray(J["pop_school_cell"], dtype=np.int64)

    def _in(x: np.ndarray) -> np.ndarray:
        k = (x >= 0) & (x < core_cell.size)
        return k & core_cell[np.where(k, x, 0)]

    member = sample_core_res | (~np.isin(kind, VISITOR_KINDS) & (_in(wc) | _in(sc)))
    day_ok = member & (minutes >= DWELL_MIN)
    w = np.asarray(weight, dtype=np.float64)
    night = float(w[sample_core_res].sum())
    day = float(w[day_ok].sum())
    return {"night_w": _f(night, 1), "day_w": _f(day, 1), "ratio": _f(ratio(day, night), 3),
            "n_res": int(sample_core_res.sum()), "n_day": int(day_ok.sum())}


# ---------------------------------------------------------------------- 3-1 錨 2(W12 から組む在圏の形)
def _kddi_axis_from_hours(hours: Sequence[int], values: Sequence[float]) -> np.ndarray:
    """0〜23 時の値 → KDDI の軸(0〜4 時は 24〜28 時へ)。"""
    out = np.zeros(len(KDDI_HOURS))
    for h, v in zip(hours, values):
        hh = int(h) % HOURS_PER_DAY
        idx = int(np.flatnonzero(HOUR_IDX == hh)[0])
        out[idx] += float(v)
    return out


def time_dist_shape(td: Mapping[str, Any], purpose: str, flow: str) -> np.ndarray:
    """time_dist_12 の 1 行(目的 × 乗降)→ KDDI の軸の形。開端は W12 と同じ等分(～6時台→5,6・0時台～→24,25)。"""
    out = np.zeros(len(KDDI_HOURS))
    pos = {h: i for i, h in enumerate(KDDI_HOURS)}
    for r in td["data"]:
        if r.get("purpose") != purpose or r.get("flow") != flow:
            continue
        b, v = str(r["bin"]), float(r["share"])
        if b.startswith("～"):
            out[pos[5]] += v / 2
            out[pos[6]] += v / 2
        elif b.endswith("～"):
            out[pos[24]] += v / 2
            out[pos[25]] += v / 2
        else:
            out[pos[int(b.replace("時台", ""))]] += v
    s = out.sum()
    return out / s if s > 0 else out


#: 3-1 錨 2 の β(流出の時刻の形)に使う time_dist_12 の目的。本則=帰宅(R-115 §3-1「帰宅中心」)・腕=合計。
BETA_PURPOSE_MAIN = "帰宅"
BETA_PURPOSE_ARM = "合計"


def w12_stock_shape(S: Static, beta_purpose: str = BETA_PURPOSE_MAIN, *, with_arm: bool = True) -> dict[str, Any]:
    """N̂(h) = R + I·Σ_{t≤h}α(t) − O·Σ_{t≤h}β(t)(時間帯の終わりの在庫・5 時の在庫=居住者)。

    α = W12 の重みの時刻の周辺(全ノード=time_dist_12 の降車を d-1 の目的の構成で重み付けた形)・β = time_dist_12 の
    乗車の形(本則は帰宅・腕は合計)・R = W16 の居住者(kind 2・3・P′)・I/O = W12 の 1 日の流入/流出の和。
    舞台全体の流量なので 5 エリアには分けない(5 エリア計と舞台全体の列に並べる)。
    """
    wt = S.weights
    alpha = _kddi_axis_from_hours(wt["hour"].tolist(), wt["weight"].tolist())
    alpha = alpha / alpha.sum() if alpha.sum() > 0 else alpha
    beta = time_dist_shape(S.time_dist, beta_purpose, "乗車")
    inflow = float(np.sum(S.nodes["daily_inflow"]))
    outflow = float(np.sum(S.nodes["daily_outflow"]))
    w = S.w16
    pm = population_masks(w["kind"], w["age"], w["is_foreign"])["P_prime"]
    resid = float((np.isin(np.asarray(w["kind"], dtype=np.int64), (2, 3)) & (np.asarray(w["home_cell"]) >= 0) & pm).sum())
    stock = np.maximum(resid + inflow * np.cumsum(alpha) - outflow * np.cumsum(beta), 0.0)
    out = {"series": [_f(v, 1) for v in stock], "peak": peak_hour(stock), "R": resid, "I": inflow, "O": outflow,
           "beta_purpose": beta_purpose, "hour_share": [_f(v, 6) for v in share(stock)],
           "note": f"α=W12 の重みの時刻の周辺(全ノード)・β=time_dist_12 の乗車 {beta_purpose}・舞台全体の流量"
                   "(5 エリアに分けない)・時間帯の終わりの在庫"}
    if with_arm:
        arm = w12_stock_shape(S, BETA_PURPOSE_ARM, with_arm=False)
        out["arm_beta_total"] = {"peak": arm["peak"], "hour_share": arm["hour_share"], "beta_purpose": BETA_PURPOSE_ARM}
    return out


# ---------------------------------------------------------------------- 3-3
def node_ids(S: Static) -> list[str]:
    return [str(v) for v in S.nodes["node_id"].tolist()]


def arrivals_table(transit: np.ndarray, ticks: np.ndarray, direction: np.ndarray, weight: np.ndarray, n_nodes: int,
                   tick_seconds: int = STEP_SECONDS) -> tuple[np.ndarray, int]:
    """transit_state が域外(1・2)→ 舞台(0)に変わった刻み × direction_node。(n_nodes+1, 24)・最後の行=なし。"""
    tr = np.asarray(transit, dtype=np.int64)
    arr = (tr[:-1] != 0) & (tr[1:] == 0)                      # (T-1, n)・刻み t+1 に着いた
    t = np.asarray(ticks, dtype=np.int64)[1:]
    hour = ((t * int(tick_seconds)) // SECONDS_PER_HOUR) % HOURS_PER_DAY
    dn = np.asarray(direction, dtype=np.int64)
    node = np.where((dn >= 0) & (dn < n_nodes), dn, n_nodes)
    w = np.asarray(weight, dtype=np.float64)
    out = np.zeros((n_nodes + 1, HOURS_PER_DAY))
    tt, ii = np.nonzero(arr)
    np.add.at(out, (node[ii], hour[tt]), w[ii])
    return out[:, HOUR_IDX], int(tt.size)


def plan_arrivals_table(tick: np.ndarray, agent: np.ndarray, direction: np.ndarray, weight: np.ndarray,
                        n_nodes: int, tick_seconds: int = STEP_SECONDS) -> np.ndarray:
    dn = np.asarray(direction, dtype=np.int64)
    a = np.asarray(agent, dtype=np.int64)
    node = np.where((dn[a] >= 0) & (dn[a] < n_nodes), dn[a], n_nodes)
    hour = ((np.asarray(tick, dtype=np.int64) * int(tick_seconds)) // SECONDS_PER_HOUR) % HOURS_PER_DAY
    out = np.zeros((n_nodes + 1, HOURS_PER_DAY))
    np.add.at(out, (node, hour), np.asarray(weight, dtype=np.float64)[a])
    return out[:, HOUR_IDX]


def w12_node_anchors(S: Static) -> dict[str, Any]:
    ids = node_ids(S)
    inflow = np.asarray(S.nodes["daily_inflow"], dtype=np.float64)
    s1 = inflow / inflow.sum()
    shape = np.zeros((len(ids), len(KDDI_HOURS)))
    for nid, h, w in zip(S.weights["node_id"].tolist(), S.weights["hour"].tolist(), S.weights["weight"].tolist()):
        if str(nid) in ids:
            shape[ids.index(str(nid))] += _kddi_axis_from_hours([h], [w])
    wsum = shape.sum(axis=1)
    return {"ids": ids, "share": s1, "share_from_weights": wsum / max(wsum.sum(), 1e-12), "shape": shape}


# ---------------------------------------------------------------------- 3-4
def work_targets(J: Mapping[str, Any], keep: np.ndarray) -> np.ndarray:
    kind = np.asarray(J["pop_kind"], dtype=np.int64)
    wc = np.asarray(J["pop_work_cell"], dtype=np.int64)
    hc = np.asarray(J["pop_home_cell"], dtype=np.int64)
    return np.isin(kind, WORK_KINDS) & np.asarray(keep, dtype=bool) & (wc >= 0) & (wc != hc)


def first_work_run(cells_t: np.ndarray, stage_t: np.ndarray, work_cell: np.ndarray, ticks: np.ndarray,
                   tick_seconds: int = STEP_SECONDS) -> tuple[np.ndarray, np.ndarray]:
    """その日に初めて work_cell に 30 分以上続けて居た区間の始まり[分](無ければ −1)と 15 分の在席の率 (96, n)。"""
    t = np.asarray(ticks, dtype=np.int64)
    minute = t * int(tick_seconds) // SECONDS_PER_MINUTE
    need = int(math.ceil(DWELL_MIN * SECONDS_PER_MINUTE / float(tick_seconds)))
    wc = np.asarray(work_cell, dtype=np.int64)
    n = wc.size
    cur = np.zeros(n, dtype=np.int64)
    start = np.zeros(n, dtype=np.int64)
    found = np.full(n, -1, dtype=np.int64)
    slot_sum = np.zeros((N_SLOTS, n))
    slot_cnt = np.zeros(N_SLOTS)
    for j in range(t.size):  # 逐次ループ宣言: 刻みの数 × ベクトル(対象の体)
        m = np.asarray(stage_t[j], dtype=bool) & (np.asarray(cells_t[j], dtype=np.int64) == wc)
        start = np.where(m & (cur == 0), minute[j], start)
        cur = np.where(m, cur + 1, 0)
        hit = (cur >= need) & (found < 0) & (start > 0)
        found = np.where(hit, start, found)
        s = int(minute[j] // SLOT_MIN) % N_SLOTS
        slot_sum[s] += m
        slot_cnt[s] += 1.0
    return found, slot_sum / np.maximum(slot_cnt, 1.0)[:, None]


def weighted_curve(rate: np.ndarray, weight: np.ndarray) -> np.ndarray:
    w = np.asarray(weight, dtype=np.float64)
    return (rate @ w) / w.sum() if w.sum() > 0 else np.zeros(rate.shape[0])


def ssb_work_rise(ssb: Mapping[str, Any], region: str = "03") -> dict[str, Any]:
    """第 8-1 表(平日・関東大都市圏・有業者・年齢総数)の仕事(05)の行動者率を男女の推定人口で混ぜた曲線の立ち上がり。"""
    ai = list(ssb["activity_codes"]).index("05")
    tbl = ssb["tables"]["weekday"][region]
    curve = np.zeros(N_SLOTS)
    pops = 0.0
    for se in ("1-1", "2-1"):
        r = tbl[se][ssb.get("age_total_code", "00")]
        p = float(r["pop_k"])
        curve += p * np.asarray(r["rates"][ai], dtype=np.float64) / 10_000.0
        pops += p
    curve = curve / max(pops, 1e-12)
    rs = rise_slot(curve)
    return {"rise": hm(None if rs is None else rs * SLOT_MIN), "rise_slot": rs, "max_rate": _f(float(curve.max())),
            "curve15": [_f(v, 4) for v in curve], "region": region,
            "note": "15 分の枠の 0 番=0:00(engine/classical.py の minute // 15 と同じ読み)・閾値 50% は expedient"}


def duty_open_anchor(J: Mapping[str, Any], targets: np.ndarray, S: Static, guard: ReadGuard) -> dict[str, Any]:
    """3-4 錨 1〔写〕: W17 v2 の勤務窓の作り方(trial.draw_windows=第 31 表の逆関数法+arrival_lead)を対象の体に。

    プールの素材(雇用形態・arrival_lead_min・職業・学校段階・曜日)は ``pool_facts.read_facts`` で必要な行だけ読む
    (許可の一覧の ``pool`` の下だけ=監査フックが見る)。duty_activity は ``w17_schedule.build_facts`` の
    勤務/通学/無職の分岐(kind 0・2 に効く部分)をそのまま当てる。欠勤は本番と同じく曜日ごとに引く(absent=True)。
    """
    from shibuya.build.sched import pool_facts as PF
    from shibuya.build.sched import trial as TR
    from shibuya.build.sched import vocab as V
    from shibuya.build.sched import w17_schedule as W17

    pool_root = S.pool_root
    guard.check(pool_root / "L1" / "part-0000.jsonl")  # 読む前に許可の一覧(役割 pool)で確かめる
    layer_dirs = [pool_root / L for L in PF.LAYERS]
    if not any(d.is_dir() for d in layer_dirs):
        return {"duty_open": None, "status": "プールが無い(data/persona_pool_v2)=錨 1 は空"}
    n = int(np.asarray(J["pop_kind"]).size)
    tg = np.flatnonzero(targets)
    layer = np.where(targets, np.asarray(J["pop_pool_layer"], dtype=np.int64), 0)
    index = np.where(targets, np.asarray(J["pop_pool_index"], dtype=np.int64), -1)
    facts = PF.read_facts(pool_root, layer, index)  # 必要な行だけ json.loads(open は監査フックが見る)
    read_parts = [p for d in layer_dirs if d.is_dir() for p in PF.layer_files(pool_root, d.name)]
    guard.note_dir_files("pool", read_parts)
    age = np.asarray(J["pop_age"], dtype=np.int64)
    wc = np.asarray(J["pop_work_cell"], dtype=np.int64)
    sc = np.asarray(J["pop_school_cell"], dtype=np.int64)
    occ = facts.col("occupation")
    stage_col = facts.col("school_stage")
    duty = np.full(n, -1, dtype=np.int8)
    for i in tg.tolist():  # 逐次ループ宣言: 対象の体(5,000 体で約 2,000)
        stage = stage_col[i] or W17.SCHOOL_OCCUPATIONS.get(occ[i], "")
        if not stage and int(age[i]) < W17.SCHOOL_AGE_MAX:
            stage = "school"
        if sc[i] >= 0 or stage:
            continue  # 通学(窓を引かない)
        if occ[i] in W17.NON_WORKING_OCCUPATIONS and (wc[i] < 0 or int(age[i]) >= W17.RETIREMENT_AGE):
            continue  # 無職
        duty[i] = V.ACT_WORK
    work_days = np.where(facts.work_days > 0, facts.work_days, PF.WEEKDAY_MASK).astype(np.uint8)
    f = SimpleNamespace(n=n, agent_id=np.asarray(J["pop_source_agent_id"], dtype=np.int64),
                        kind=np.asarray(J["pop_kind"], dtype=np.int64), duty_activity=duty, work_days=work_days,
                        pool=facts)
    tf = TR.draw_windows(f, S.commute, rows=tg, absent=True)
    day = int(J["meta"].get("plan", {}).get("day_index", 0))
    on_day = ((np.asarray(tf.work_days, dtype=np.int64) >> day) & 1) == 1
    ok = targets & (np.asarray(tf.duty_open) >= 0) & on_day
    return {"duty_open": np.asarray(tf.duty_open, dtype=np.int64), "ok": ok,
            "counters": {k: int(v) for k, v in tf.counters.items()},
            "n_targets": int(targets.sum()), "n_window": int((np.asarray(tf.duty_open) >= 0).sum()),
            "n_on_day": int(ok.sum())}


def w20_start_anchor(J: Mapping[str, Any], targets: np.ndarray, S: Static, guard: ReadGuard) -> dict[str, Any]:
    """3-4 錨 5〔写〕(第 3 期 3-1): W20cal(暦 1a)の週の表の、その日の曜日の勤務の約束の始まり(週 0・対象の体)。

    表は許可の一覧の役割 ``w20`` だけで読む(組んだ資産が無ければ空の列)。曜日は journal の計画の曜日(``plan.day_index``)。
    """
    p = S.w20_path
    if p is None:
        return {"start": None, "status": f"W20 の週の表が無い({_CSH_STAGE_DIR} を組んでいない)=錨 5 は空"}
    tab = _cached(S, "w20_tab", lambda: guard.read_parquet(p, ["agent_id", "week", "weekday", "commit", "start_min",
                                                                "depart_min", "lead_min"]))
    day = int(J["meta"].get("plan", {}).get("day_index", 0))
    sel = (np.asarray(tab["week"]) == 0) & (np.asarray(tab["weekday"]) == day)
    aid = np.asarray(tab["agent_id"], dtype=np.int64)[sel]
    order = np.argsort(aid)
    aid = aid[order]
    commit = np.asarray(tab["commit"], dtype=np.int64)[sel][order]
    start = np.asarray(tab["start_min"], dtype=np.int64)[sel][order]
    want = np.asarray(J["pop_source_agent_id"], dtype=np.int64)
    pos = np.clip(np.searchsorted(aid, want), 0, max(aid.size - 1, 0))
    found = (aid.size > 0) & (aid[pos] == want)
    work = found & (commit[pos] == 1)
    st = np.where(work, start[pos], -1)
    ok = np.asarray(targets, dtype=bool) & work
    return {"start": st, "ok": ok, "n_targets": int(np.count_nonzero(targets)), "n_work": int(ok.sum()),
            "n_not_in_table": int(np.count_nonzero(np.asarray(targets, dtype=bool) & ~found)), "weekday": day}


# ====================================================================== 1 腕の計器
def gauge_arm(J: Mapping[str, Any], S: Static, guard: ReadGuard, *, duty_cache: dict[str, Any] | None = None
              ) -> dict[str, Any]:
    meta = dict(J["meta"])
    tick_s = int(meta.get("tick_seconds", STEP_SECONDS))
    ticks = np.asarray(J["ticks"], dtype=np.int64)
    cells = np.asarray(J["cells"], dtype=np.int64)
    transit = np.asarray(J["transit"], dtype=np.int64)
    plan_cells = np.asarray(J["plan_cells"], dtype=np.int64)
    kind = np.asarray(J["pop_kind"], dtype=np.int64)
    if not np.array_equal(kind, np.asarray(J["kind"], dtype=np.int64)[: kind.size]):
        raise ValueError("記録の種別と母集団の行が食い違う")
    omega = expansion_factors(S.w16["kind"], kind)
    pm = population_masks(kind, J["pop_age"], J["pop_is_foreign"])
    keep = pm["P_prime"]
    aoc = S.area_of_cell
    out: dict[str, Any] = {"meta": {k: meta.get(k) for k in ("arm", "kwargs", "n_agents", "seed", "final_hash",
                                                              "llm_calls", "manifest", "commit",
                                                              "src_diff_files_vs_head", "src_is_worktree", "plan",
                                                              "journal_arrays_sha16", "record_opened_files")}}
    out["weights"] = {"omega_by_kind": {str(k): _f(float(omega[kind == k][0]), 3) for k in np.unique(kind)},
                      "n_by_kind": {str(k): int((kind == k).sum()) for k in np.unique(kind)}}

    # ---------- 3-1・3-2 の部品(ランと計画)
    area_s, stage_s = area_and_stage(cells, transit, aoc)
    area_p, stage_p = area_and_stage(plan_cells, None, aoc, plan=True)
    hm_s, best_s = hour_minutes(area_s, stage_s, ticks, tick_s)
    hm_p, best_p = hour_minutes(area_p, stage_p, ticks, tick_s)
    q = {("sim", d): daily_qualified(hm_s, best_s, d, tick_s) for d in ("sum", "cont")}
    q.update({("plan", d): daily_qualified(hm_p, best_p, d, tick_s) for d in ("sum", "cont")})
    unknown = plan_unknown_shares(plan_cells, stage_p, kind)

    # ---------- 3-1 在圏のピーク時刻
    arms31: dict[str, Any] = {}
    for src, hmn in (("sim", hm_s), ("plan", hm_p)):
        for d in ("sum", "cont"):
            for th in THETAS:
                arms31[f"{src}/{d}/theta{th}"] = peaks_block(presence_hourly(hmn, q[(src, d)], omega, keep, th,
                                                                             tick_s))
    arms31["sim/on_hour_v13"] = peaks_block(presence_on_hour(area_s, stage_s, ticks, omega, keep, tick_s))
    main = arms31[f"sim/sum/theta{THETA_MAIN}"]
    a1 = arms31[f"plan/sum/theta{THETA_MAIN}"]
    a2 = _cached(S, "w12_stock", lambda: w12_stock_shape(S))
    cmp31: dict[str, Any] = {}
    for c in COLS:
        sp, pp = main["peak"][c], a1["peak"][c]
        row = {"sim": sp, "a1_plan": pp, "a1_diff_h": None if sp is None or pp is None else sp - pp,
               "a1_jsd": _f(jsd(main["hour_share"][c], a1["hour_share"][c]), 5)}
        if c in ("total5", "stage"):
            row.update({"a2_w12": a2["peak"], "a2_diff_h": None if sp is None or a2["peak"] is None else sp - a2["peak"],
                        "a2_jsd": _f(jsd(main["hour_share"][c], a2["hour_share"]), 5)})
        cmp31[c] = row
    pops31 = {}
    for pname in ("P", "all"):
        N = presence_hourly(hm_s, q[("sim", "sum")], omega, pm[pname], THETA_MAIN, tick_s)
        pops31[pname] = {c: peak_hour(N[i]) for i, c in enumerate(COLS)}
    out["3-1"] = {"marks": MARKS["3-1"], "main": f"sim/sum/theta{THETA_MAIN}", "arms": arms31, "compare": cmp31,
                  "a2_w12": a2, "a3_pt_c2": dict(PENDING_MATERIAL), "population_arms": pops31,
                  "plan_unknown_cell_share": unknown}

    # ---------- 3-2 来街者/居住者の比
    ha = cells_to_area(J["pop_home_cell"], aoc)
    wa = cells_to_area(J["pop_work_cell"], aoc)
    sa = cells_to_area(J["pop_school_cell"], aoc)
    att_area = attr_by_area(ha, wa, sa)
    att_kind = attr_by_kind(kind)
    foreign = np.asarray(J["pop_age"], dtype=np.int64) >= ADULT_AGE
    foreign &= np.asarray(J["pop_is_foreign"], dtype=bool)
    rat: dict[str, Any] = {}
    for src in ("sim", "plan"):
        for d in ("sum", "cont"):
            rat[f"{src}/{d}/area"] = ratio_block(q[(src, d)], att_area, omega, keep, foreign)
        rat[f"{src}/sum/kind"] = ratio_block(q[(src, "sum")], att_kind, omega, keep, foreign)
    for pname in ("P", "all"):
        rat[f"sim/sum/area/{pname}"] = ratio_block(q[("sim", "sum")], att_area, omega, pm[pname], None)
    # 計画の来街の行は target_cell を持たない(−1)=エリアに置けない。舞台の中でセル不明の分の割合を出し、
    # 来街の種別でほぼ全部が不明なら計画の V は空(0 と書かない)
    if unknown["visitor_kinds"] is not None and unknown["visitor_kinds"] >= 0.99:
        for key in [k for k in rat if k.startswith("plan/")]:
            rat[key] = blank_visitor(rat[key])
    core = _cached(S, "core9", lambda: _core9_static(S))
    keys9 = set(core["keys"])
    res9 = np.isin(kind, (2, 3)) & np.asarray([_chome_of_agent(S, a) in keys9 for a in
                                               np.asarray(J["pop_source_agent_id"], dtype=np.int64).tolist()])
    core_cell = core["core_cell"]
    out["3-2"] = {
        "marks": MARKS["3-2"], "main": "sim/sum/area", "arms": rat, "plan_unknown_cell_share": unknown,
        "a1_w16": _cached(S, "w16_static", lambda: w16_static_ratios(S)),
        "a3_core9": {"anchor": S.calib["core9"]["day_night_ratio"], "w16_static": core["w16_static"],
                     "run": core9_run(cells, stage_s, ticks, J, omega, core_cell, res9, tick_s),
                     "plan": core9_run(plan_cells, stage_p, ticks, J, omega, core_cell, res9, tick_s),
                     "mapping": core["mapping"]},
        "floor_visitor_per_worker": FLOOR_VISITOR_PER_WORKER,
    }

    # ---------- 3-3 駅ごとの到着の波
    ids = node_ids(S)
    nn = len(ids)
    A_sim, n_arr = arrivals_table(transit, ticks, J["pop_direction_node"], omega, nn, tick_s)
    A_plan = plan_arrivals_table(J["plan_arrive_tick"], J["plan_arrive_agent"], J["pop_direction_node"], omega, nn,
                                 tick_s)
    anc = _cached(S, "w12_nodes", lambda: w12_node_anchors(S))
    sim_tot = A_sim[:nn].sum()
    plan_tot = A_plan[:nn].sum()
    rows33: dict[str, Any] = {}
    for i, nid in enumerate(ids + [NONE_NODE]):
        r: dict[str, Any] = {"sim_share": _f(A_sim[i].sum() / sim_tot) if i < nn and sim_tot > 0 else None,
                             "sim_peak": peak_hour(A_sim[i]), "sim_level": _f(A_sim[i].sum(), 1),
                             "plan_share": _f(A_plan[i].sum() / plan_tot) if i < nn and plan_tot > 0 else None,
                             "plan_peak": peak_hour(A_plan[i]),
                             "sim_shape": [_f(v, 6) for v in share(A_sim[i])]}
        if i < nn:
            r.update({"a1_share": _f(anc["share"][i]), "a1_diff": _f((r["sim_share"] or 0.0) - anc["share"][i])
                      if r["sim_share"] is not None else None,
                      "a2_peak": peak_hour(anc["shape"][i]),
                      "a2_jsd": _f(jsd(A_sim[i], anc["shape"][i]), 5),
                      "plan_a2_jsd": _f(jsd(A_plan[i], anc["shape"][i]), 5)})
            r["a2_diff_h"] = None if r["sim_peak"] is None or r["a2_peak"] is None else r["sim_peak"] - r["a2_peak"]
        rows33[nid] = r
    out["3-3"] = {"marks": MARKS["3-3"], "nodes": rows33, "n_arrivals": n_arr,
                  "n_plan_arrivals": int(np.asarray(J["plan_arrive_tick"]).size),
                  "a1_share_vs_weights_max_abs": _f(float(np.max(np.abs(anc["share"] - anc["share_from_weights"]))), 8),
                  "a3_pt_c2": dict(PENDING_MATERIAL), "a4_grey": dict(PENDING_GREY),
                  "population": "全員(W12 の流量に年齢の軸が無い=宣言)"}

    # ---------- 3-4 勤務の始業の分布
    tg = work_targets(J, keep)
    idx = np.flatnonzero(tg)
    wc_t = np.asarray(J["pop_work_cell"], dtype=np.int64)[idx]
    found, rate = first_work_run(cells[:, idx], stage_s[:, idx], wc_t, ticks, tick_s)
    found_p, rate_p = first_work_run(plan_cells[:, idx], stage_p[:, idx], wc_t, ticks, tick_s)
    w_t = omega[idx]
    sim_ok = found >= 0
    sim_stats = dist_stats(found[sim_ok], w_t[sim_ok])
    curve_s = weighted_curve(rate, w_t)
    curve_p = weighted_curve(rate_p, w_t)
    pws = np.asarray(J["plan_work_start"], dtype=np.int64)[idx]
    a2_ok = pws >= 0
    a2_stats = dist_stats(pws[a2_ok], w_t[a2_ok])
    if duty_cache is not None and "duty" in duty_cache and np.array_equal(duty_cache["targets"], tg):
        duty = duty_cache["duty"]
    else:
        duty = duty_open_anchor(J, tg, S, guard)
        if duty_cache is not None:
            duty_cache.update({"duty": duty, "targets": tg})
    if duty.get("duty_open") is not None:
        ok1 = np.asarray(duty["ok"], dtype=bool)
        a1_stats = dist_stats(np.asarray(duty["duty_open"])[ok1], omega[ok1])
        a1_info = {k: duty[k] for k in ("counters", "n_targets", "n_window", "n_on_day")}
    else:
        a1_stats, a1_info = {"n": 0, "mean": None, "hist15": [0.0] * N_SLOTS}, {"status": duty.get("status")}
    a3 = _cached(S, "ssb_rise", lambda: ssb_work_rise(S.ssb))
    rs_s, rs_p = rise_slot(curve_s), rise_slot(curve_p)
    w20 = w20_start_anchor(J, tg, S, guard)  # 〔3-1〕源 W20(暦 1a の約束の始まり)
    if w20.get("start") is not None:
        ok5 = np.asarray(w20["ok"], dtype=bool)
        a5_stats = dist_stats(np.asarray(w20["start"])[ok5], omega[ok5])
        a5_info = {k: w20[k] for k in ("n_targets", "n_work", "n_not_in_table", "weekday")}
    else:
        a5_stats, a5_info = {"n": 0, "mean": None, "hist15": [0.0] * N_SLOTS}, {"status": w20.get("status")}

    def _d(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        return {"mean_min": _f((a["mean"] - b["mean"]) if a.get("mean") is not None and b.get("mean") is not None
                               else None, 1),
                "p50_min": _f((a["p50_min"] - b["p50_min"]) if a.get("p50_min") is not None and
                              b.get("p50_min") is not None else None, 1),
                "jsd15": _f(jsd(a["hist15"], b["hist15"]), 5)}

    out["3-4"] = {
        "marks": MARKS["3-4"], "n_targets": int(tg.sum()), "n_found": int(sim_ok.sum()),
        "sim": sim_stats, "sim_rise": hm(None if rs_s is None else rs_s * SLOT_MIN),
        "plan_rise": hm(None if rs_p is None else rs_p * SLOT_MIN),
        "sim_curve15": [_f(v, 4) for v in curve_s], "plan_curve15": [_f(v, 4) for v in curve_p],
        "a1_r31_lead": {**a1_stats, **a1_info}, "a2_w17_work_row": a2_stats,
        "a3_ssb_8_1": a3, "a4_pt_c2": dict(PENDING_MATERIAL),
        "diff_vs_a1": _d(sim_stats, a1_stats), "diff_vs_a2": _d(sim_stats, a2_stats),
        # 〔第 3 期 3-1〕源 W20(暦 1a)と、ランとの差・W17 との差(参考)・錨 1 との差(どちらも第 31 表の写し)
        "a5_w20": {**a5_stats, **a5_info}, "diff_vs_a5": _d(sim_stats, a5_stats),
        "a2_minus_a5": _d(a2_stats, a5_stats), "a1_minus_a5": _d(a1_stats, a5_stats),
        "rise_diff_vs_a3_min": None if rs_s is None or a3["rise_slot"] is None else (rs_s - a3["rise_slot"]) * SLOT_MIN,
    }

    # ---------- 感度: エリアの写像 ±50 m(3-1 のピークと 3-2 の計)
    sens: dict[str, Any] = {}
    for lab, aoc_d in S.dilated.items():
        ar, st = area_and_stage(cells, transit, aoc_d)
        hmd, bd = hour_minutes(ar, st, ticks, tick_s)
        qd = daily_qualified(hmd, bd, "sum", tick_s)
        Nd = presence_hourly(hmd, qd, omega, keep, THETA_MAIN, tick_s)
        att = attr_by_area(cells_to_area(J["pop_home_cell"], aoc_d), cells_to_area(J["pop_work_cell"], aoc_d),
                           cells_to_area(J["pop_school_cell"], aoc_d))
        rb = ratio_block(qd, att, omega, keep)
        sens[lab] = {"peak": {c: peak_hour(Nd[i]) for i, c in enumerate(COLS)},
                     "V_per_Res": rb["total"]["V_per_Res"], "W_per_Res": rb["total"]["W_per_Res"]}
    out["sensitivity_area_dilate"] = sens
    out["summary"] = summarize(out)
    return out


def _core9_static(S: Static) -> dict[str, Any]:
    keys = core9_keys(S)
    chome_cells = chome_of_cells(S)
    core_cell = np.asarray([str(k) in set(keys) for k in chome_cells.tolist()], dtype=bool)
    gl = np.asarray([p.endswith("_GL") for p in S.place_ids], dtype=bool)
    return {"keys": keys, "core_cell": core_cell, "w16_static": core9_w16_static(S, core_cell),
            "mapping": {"n_cells": int(core_cell.sum()), "n_gl_cells": int((core_cell & gl).sum()),
                        "gl_ha": float((core_cell & gl).sum()),
                        "rule": "居住者の chome_key の多数決・居住者の居ないセルは最も近いセル(expedient)"}}


def _chome_of_agent(S: Static, agent_id: int) -> str:
    lut = _cached(S, "chome_lut", lambda: {int(a): str(k) for a, k in zip(S.w16["agent_id"].tolist(),
                                                                           S.w16["chome_key"].tolist())})
    return lut.get(int(agent_id), "")


def summarize(arm: Mapping[str, Any]) -> dict[str, Any]:
    """版の間で比べる値(平らな辞書)。"""
    s: dict[str, Any] = {}
    m31 = arm["3-1"]["arms"][arm["3-1"]["main"]]
    for c in COLS:
        s[f"3-1/sim/peak/{c}"] = m31["peak"][c]
        s[f"3-1/plan/peak/{c}"] = arm["3-1"]["arms"][f"plan/sum/theta{THETA_MAIN}"]["peak"][c]
    s["3-1/sim/order"] = ORDER_SEP.join(m31["order"])
    s["3-1/a2_w12/peak"] = arm["3-1"]["a2_w12"]["peak"]
    for src in ("sim", "plan"):
        b = arm["3-2"]["arms"][f"{src}/sum/area"]
        for a in AREA_IDS + ("total",):
            s[f"3-2/{src}/V_per_Res/{a}"] = b[a]["V_per_Res"]
            s[f"3-2/{src}/W_per_Res/{a}"] = b[a]["W_per_Res"]
    s["3-2/core9/run_ratio"] = arm["3-2"]["a3_core9"]["run"]["ratio"]
    s["3-2/core9/w16_ratio"] = arm["3-2"]["a3_core9"]["w16_static"]["ratio"]
    for nid, r in arm["3-3"]["nodes"].items():
        s[f"3-3/sim/share/{nid}"] = r["sim_share"]
        s[f"3-3/sim/peak/{nid}"] = r["sim_peak"]
    for k in ("mean", "p50_min", "on_00_30", "mode_bin"):
        s[f"3-4/sim/{k}"] = arm["3-4"]["sim"].get(k)
        s[f"3-4/a1/{k}"] = arm["3-4"]["a1_r31_lead"].get(k)
        s[f"3-4/a2/{k}"] = arm["3-4"]["a2_w17_work_row"].get(k)
        if "a5_w20" in arm["3-4"]:  # 〔3-1〕源 W20(前の版の記録には無い)
            s[f"3-4/a5/{k}"] = arm["3-4"]["a5_w20"].get(k)
    s["3-4/sim/rise"] = arm["3-4"]["sim_rise"]
    s["3-4/a3/rise"] = arm["3-4"]["a3_ssb_8_1"]["rise"]
    return s


# ====================================================================== 全体・書き出し
def gauge(journals: Mapping[str, Path], *, paths: Mapping[str, Path], out_dir: Path | None = None,
          compare_dir: Path | None = None) -> dict[str, Any]:
    prev = [compare_dir] if compare_dir is not None else []
    guard = make_guard(paths, out_dir=out_dir, prev_dirs=prev)
    with guard.active():
        S = load_static(guard, paths)
        doc: dict[str, Any] = {
            "schema": SCHEMA, "created": _dt.date.today().isoformat(),
            "declared": declared_text(), "area_map": S.area_meta, "arms": {},
        }
        duty_cache: dict[str, Any] = {}
        for arm, jp in journals.items():
            J = load_journal(guard, Path(jp))
            doc["arms"][arm] = gauge_arm(J, S, guard, duty_cache=duty_cache)
        doc["allow_list"] = dict(roles_table(guard))
        doc["inputs_read"] = files_listing(guard)
        if compare_dir is not None:
            prev_doc = guard.read_json(Path(compare_dir) / "anchor_gauge.json")
            doc["compare"] = compare_docs(prev_doc, doc, prev_label=Path(compare_dir).name)
        if out_dir is not None:
            write_outputs(doc, Path(out_dir))
    return doc


def declared_text() -> dict[str, str]:
    return {
        "population": "v1.4 の母集団 P′ = age ≥ 20 かつ is_foreign でない(本則)。P = kind ≠ 7 かつ age ≥ 20 は継続の腕",
        "weights": "拡大係数 ω_k = N_k(W16)/ n_k(標本)。二層抽出の種別の偏りを戻す(expedient)",
        "dwell": "1 日単位の 30 分=合計(本則)・連続(腕)。時間帯別は θ = 1 刻み(既定)・30 分(腕)",
        "hours": "KDDI の 5〜28 時の 24 区分。1 日ランの 24〜28 時は同じ日の 0〜4 時で代える",
        "attr": "area の写像(自宅エリアが先・次に職場/学校エリア・どちらでもなければ来街)。kind の写像は継続の記録",
        "plan_cells": "計画上のセル=行の target_cell・負の行は職場/学校/自宅のセルで補う・補えない行は舞台の中のセル不明",
        "arrivals": "transit_state が 1・2 → 0 に変わった刻み × W16 direction_node(全員)",
        "work_start": "kind 0・2・P′・work_cell ≥ 0 かつ ≠ home_cell。work_cell に 30 分以上続けて居た最初の区間の始まり"
                      "(0 時から続く区間は除く)",
        "rise": "仕事の行動者率(または在席の率)が 1 日の最大の 50% を初めて超える 15 分(閾値 expedient)",
        "core9": "セル → 町丁目は居住者の chome_key の多数決+最近傍。昼=10〜16 時に 30 分以上(ランの腕)",
        "no_pass_fail": "合否は書かない。〔写〕の錨との差は形だけ。「現実に近づいた」の主張は holdout の開封(S1)の後だけ",
    }


def compare_docs(prev: Mapping[str, Any], cur: Mapping[str, Any], *, prev_label: str = "prev") -> dict[str, Any]:
    """前の版との差の表(要約の値ごと・腕ごと)。数は差・文字は同じか。"""
    rows: list[dict[str, Any]] = []
    for arm in sorted(set(prev.get("arms", {})) | set(cur.get("arms", {}))):
        a = prev.get("arms", {}).get(arm, {}).get("summary", {})
        b = cur.get("arms", {}).get(arm, {}).get("summary", {})
        for k in sorted(set(a) | set(b)):
            va, vb = a.get(k), b.get(k)
            if isinstance(va, (int, float)) and isinstance(vb, (int, float)) and not isinstance(va, bool):
                d: Any = _f(float(vb) - float(va), 4)
                same = d == 0
            elif k.endswith("/order"):  # 並びは区切りの記号によらず列で比べる(検収 L5 で > を → にした)
                d, same = None, _order_list(va) == _order_list(vb)
            else:
                d, same = None, va == vb
            rows.append({"arm": arm, "key": k, "prev": va, "cur": vb, "diff": d, "same": bool(same)})
    pm = {a: (prev.get("arms", {}).get(a, {}).get("meta", {}) or {}) for a in prev.get("arms", {})}
    cm = {a: (cur.get("arms", {}).get(a, {}).get("meta", {}) or {}) for a in cur.get("arms", {})}
    return {"prev_label": prev_label, "n_rows": len(rows), "n_changed": sum(1 for r in rows if not r["same"]),
            "prev_meta": {a: {k: m.get(k) for k in ("commit", "final_hash", "llm_calls")} for a, m in pm.items()},
            "cur_meta": {a: {k: m.get(k) for k in ("commit", "final_hash", "llm_calls")} for a, m in cm.items()},
            "rows": rows}


def _order_list(v: Any) -> list[str] | None:
    return None if v is None else [x for x in re.split(r"[>→<,\s]+", str(v)) if x]


def _jdump(doc: Any) -> str:
    def _default(o: Any) -> Any:
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, Path):
            return o.name
        raise TypeError(type(o))

    return json.dumps(doc, ensure_ascii=False, indent=1, default=_default) + "\n"


def _strip_arrays(doc: Mapping[str, Any]) -> dict[str, Any]:
    """JSON に要らない大きな配列(3-4 錨 1 の体ごとの値)を落とす。"""
    out = json.loads(_jdump(_drop(doc)))
    return out


def _drop(x: Any) -> Any:
    if isinstance(x, Mapping):
        return {k: _drop(v) for k, v in x.items() if k not in ("duty_open", "ok")}
    if isinstance(x, list):
        return [_drop(v) for v in x]
    return x


def write_outputs(doc: Mapping[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    clean = _strip_arrays(doc)
    (out_dir / "anchor_gauge.json").write_text(_jdump(clean), encoding="utf-8", newline="\n")
    (out_dir / "anchor_gauge.md").write_text(render_markdown(clean), encoding="utf-8", newline="\n")
    if "compare" in clean:
        (out_dir / f"compare_vs_{clean['compare']['prev_label']}.md").write_text(
            render_compare(clean["compare"]), encoding="utf-8", newline="\n")


# ====================================================================== Markdown
def _c(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "真" if v else "偽"
    if isinstance(v, float):
        return f"{v:.4g}" if abs(v) < 1000 else f"{v:,.0f}"
    if isinstance(v, int):
        return f"{v:,}" if abs(v) >= 10000 else str(v)
    return str(v)


def _table(head: Sequence[str], rows: Iterable[Sequence[Any]]) -> str:
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    lines += ["| " + " | ".join(_c(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def render_markdown(doc: Mapping[str, Any]) -> str:
    out: list[str] = ["# 較正側の錨の計器(2-0)", ""]
    out.append("合否は書かない。〔写〕の錨は構築の入力の写しで、差は形だけを見る。「現実に近づいた」と書けるのは"
               " holdout の開封(S1)の後だけ。検証側(〔検〕)と〔灰〕は、**gauge の段では**許可の一覧で縛って読んでいない。"
               "record の段(エンジンのラン)では、エンジンが前から読む入力を開く(末尾の表。計器はその値を使わない)。")
    out.append("")
    out.append("## ラン")
    out.append("")
    rows = []
    for arm, a in doc["arms"].items():
        m = a["meta"]
        mf = m.get("manifest") or {}
        rows.append([arm, m.get("commit"), m.get("final_hash"), m.get("llm_calls"), mf.get("bridges_count"),
                     mf.get("rules_version"), m.get("src_diff_files_vs_head"), m.get("n_agents"), m.get("seed")])
    out.append(_table(["腕", "commit", "final", "呼数", "bridges_count", "rules_version", "src の差(ファイル数)",
                       "体数", "seed"], rows))
    out.append("")
    am = doc.get("area_map", {})
    out.append(f"エリアの写像: `area_axes_v0.json`(版 {am.get('axes_version')}・{am.get('axes_status')})・"
               f"面積の帯の自己検査 {_c(am.get('area_ha_gate_ok'))}・面積[ha] {am.get('area_ha')}")
    out.append("")
    for arm, a in doc["arms"].items():
        out += _md_arm(arm, a)
    out.append("## 宣言")
    out.append("")
    out += [f"- {k}: {v}" for k, v in doc.get("declared", {}).items()]
    out.append("")
    out.append("## 読んだファイル(gauge の段・許可の一覧の中だけ)")
    out.append("")
    out.append(_table(["役割", "道筋", "バイト", "md5", "配列の hash(journal)"],
                      [[r["role"], r["path"], r["bytes"], r["md5"], r.get("arrays_sha16")]
                       for r in doc.get("inputs_read", [])]))
    out.append("")
    out.append("journal の md5 は meta の壁時計で変わる。同じランかは配列の hash で見る。")
    out.append("")
    out.append("## record の段でエンジンが開いたファイル(Python の open・道筋だけ・計器はその値を使わない)")
    out.append("")
    paths: dict[str, dict[str, Any]] = {}
    for arm, a in doc["arms"].items():
        for r in (a["meta"].get("record_opened_files") or []):
            row = paths.setdefault(r["path"], {"arms": [], "tok": r.get("gauge_deny_token")})
            row["arms"].append(arm)
    out.append(_table(["道筋", "腕", "計器の段で落とす語"],
                      [[p, "・".join(v["arms"]), (f"{v['tok']}(〔検〕か〔灰〕の行が混ざる)" if v["tok"] else "—")]
                       for p, v in sorted(paths.items())]))
    out.append("")
    out.append("pyarrow の読みは監査に出ない。表の parquet は Python の open でも開かれたもので、pyarrow だけで読んだ"
               " parquet はこの表に載らない。")
    out.append("")
    return "\n".join(out)


def _md_arm(arm: str, a: Mapping[str, Any]) -> list[str]:
    out = [f"## 腕 {arm}", ""]
    w = a.get("weights", {})
    out.append(f"拡大係数 ω(種別 → W16 の体数 ÷ 標本の体数): {w.get('omega_by_kind')}")
    out.append("")
    # 3-1
    s31 = a["3-1"]
    out.append("### 3-1 在圏のピーク時刻(5〜28 時)")
    out.append("")
    ar = s31["arms"]
    rows = []
    for c in COLS:
        cm = s31["compare"][c]
        rows.append([COL_JA[c], ar[f"sim/sum/theta{THETA_MAIN}"]["peak"][c], ar["sim/sum/theta30"]["peak"][c],
                     ar[f"sim/cont/theta{THETA_MAIN}"]["peak"][c], ar["sim/on_hour_v13"]["peak"][c],
                     cm["a1_plan"], cm["a1_diff_h"], cm["a1_jsd"], cm.get("a2_w12"), cm.get("a2_diff_h"),
                     cm.get("a2_jsd"), "材料待ち"])
    out.append(_table(["列", "ラン(合計・θ1)", "θ30", "連続・θ1", "正時(v1.3)", "錨1〔写〕計画", "差[時]",
                       "JSD", "錨2〔部〕W12", "差[時]", "JSD", "錨3〔非〕PT c-2"], rows))
    out.append("")
    out.append(f"5 エリアのピークの順(早い順・ラン): {f' {ORDER_SEP} '.join(ar[f'sim/sum/theta{THETA_MAIN}']['order'])}"
               f" / 計画: {f' {ORDER_SEP} '.join(ar[f'plan/sum/theta{THETA_MAIN}']['order'])}。"
               f"母集団の腕(5 エリア計のピーク): P {s31['population_arms']['P']['total5']}・"
               f"全員 {s31['population_arms']['all']['total5']}。錨 2 の R・I・O = "
               f"{_c(s31['a2_w12']['R'])}・{_c(s31['a2_w12']['I'])}・{_c(s31['a2_w12']['O'])}"
               f"(β=time_dist_12 の乗車 {s31['a2_w12']['beta_purpose']}・腕 β=合計のピーク "
               f"{_c(s31['a2_w12'].get('arm_beta_total', {}).get('peak'))})。"
               f"計画で舞台の中に居るがセルが分からない割合(エリアに数えない・舞台には数える): 全体 "
               f"{_c(s31['plan_unknown_cell_share']['all'])}・来街の種別 "
               f"{_c(s31['plan_unknown_cell_share']['visitor_kinds'])}・それ以外 "
               f"{_c(s31['plan_unknown_cell_share']['other_kinds'])}。")
    out.append("")
    # 3-2
    s32 = a["3-2"]
    out.append("### 3-2 来街者/居住者の比(1 日単位・30 分・area の写像・ω で戻す)")
    out.append("")
    sim, plan = s32["arms"]["sim/sum/area"], s32["arms"]["plan/sum/area"]
    cont, kind = s32["arms"]["sim/cont/area"], s32["arms"]["sim/sum/kind"]
    w16a = s32["a1_w16"]["area_map"]
    rows = []
    for k in AREA_IDS + ("total",):
        rows.append([COL_JA.get(k, "5 エリアの和"), sim[k]["V_per_Res"], sim[k]["W_per_Res"], sim[k]["n"],
                     sim[k]["foreign"], cont[k]["V_per_Res"], kind[k]["V_per_Res"], plan[k]["V_per_Res"],
                     plan[k]["W_per_Res"], w16a[k]["W_per_Res"]])
    out.append(_table(["エリア", "ラン V/Res", "ラン W/Res", "ラン n(W,Res,V)", "訪日(別の列・ω)", "連続 V/Res",
                       "kind 写像 V/Res", "錨2〔写〕計画 V/Res", "錨2 W/Res", "錨1〔写〕W16 W/Res(area)"], rows))
    out.append("")
    km = s32["a1_w16"]["kind_map_stage"]
    out.append(f"錨 1〔写〕W16 の体数(kind の写像・舞台全体): P′ V/Res {_c(km['P_prime']['V_per_Res'])}・W/Res "
               f"{_c(km['P_prime']['W_per_Res'])} / P(kind≠7) V/Res {_c(km['P']['V_per_Res'])}・W/Res "
               f"{_c(km['P']['W_per_Res'])} / 全員 V/Res {_c(km['all']['V_per_Res'])}。")
    c9 = s32["a3_core9"]
    out.append(f"錨 3〔非〕中核 9 町丁目の昼夜間人口比 {c9['anchor']['value']}(都 第 11 表): W16 の静的な比 "
               f"{_c(c9['w16_static']['ratio'])}(夜 {_c(c9['w16_static']['night'])}・昼 {_c(c9['w16_static']['day'])})・"
               f"ランの比 {_c(c9['run']['ratio'])}(居住者 n={c9['run']['n_res']})・計画の比 {_c(c9['plan']['ratio'])}。"
               f"写像のセル {c9['mapping']['n_gl_cells']} 枚(GL)。")
    fl = s32["floor_visitor_per_worker"]
    out.append(f"フロア(合否にしない): 来街/勤務 PT 2018 {fl['pt_2018']} 対 KDDI {fl['kddi']}。ランの来街/勤務(5 エリアの和) "
               f"{_c(sim['total']['V_per_W'])}。")
    out.append("")
    # 3-3
    s33 = a["3-3"]
    out.append("### 3-3 駅ごとの到着の波(ω で戻す・全員)")
    out.append("")
    rows = []
    for nid, r in s33["nodes"].items():
        rows.append([nid, r["sim_share"], r.get("a1_share"), r.get("a1_diff"), r["sim_peak"], r.get("a2_peak"),
                     r.get("a2_diff_h"), r.get("a2_jsd"), r["plan_share"], r["plan_peak"], r.get("plan_a2_jsd"),
                     "材料待ち", "読まない"])
    out.append(_table(["ノード", "ラン 割合", "錨1〔写〕割合", "差", "ラン ピーク", "錨2〔部〕ピーク", "差[時]",
                       "JSD(形)", "計画 割合", "計画 ピーク", "計画 JSD", "錨3〔非〕", "錨4〔灰〕"], rows))
    out.append("")
    out.append(f"到着の数(ラン・体の延べ): {_c(s33['n_arrivals'])}・計画の到着(ARRIVE の予定): "
               f"{_c(s33['n_plan_arrivals'])}。錨 1 の割合(daily_inflow)と W12 の重みの和の差の最大 "
               f"{_c(s33['a1_share_vs_weights_max_abs'])}。")
    out.append("")
    # 3-4
    s34 = a["3-4"]
    out.append("### 3-4 勤務の始業の分布(kind 0・2・ω で戻す)")
    out.append("")
    rows = []
    for lab, st, rise in (("ラン", s34["sim"], s34["sim_rise"]), ("錨1〔写〕第 31 表+lead", s34["a1_r31_lead"], None),
                          ("錨2〔写〕W17 v2 勤務の行", s34["a2_w17_work_row"], s34["plan_rise"]),
                          ("錨5〔写〕W20 暦 1a の約束", s34.get("a5_w20", {}), None)):
        rows.append([lab, st.get("n"), st.get("mean_hm"), st.get("p10"), st.get("p25"), st.get("p50"), st.get("p75"),
                     st.get("p90"), st.get("on_00_30"), st.get("mode_bin"), rise])
    rows.append(["錨3〔部〕第 8-1 表 仕事", None, None, None, None, None, None, None, None, None,
                 s34["a3_ssb_8_1"]["rise"]])
    rows.append(["錨4〔非〕PT c-2", "材料待ち", None, None, None, None, None, None, None, None, None])
    out.append(_table(["列", "n", "平均", "p10", "p25", "p50", "p75", "p90", ":00/:30 の率", "最頻の 15 分",
                       "立ち上がり(50%)"], rows))
    out.append("")
    d1, d2 = s34["diff_vs_a1"], s34["diff_vs_a2"]
    out.append(f"差(ラン − 錨): 錨 1 平均 {_c(d1['mean_min'])} 分・p50 {_c(d1['p50_min'])} 分・JSD {_c(d1['jsd15'])} / "
               f"錨 2 平均 {_c(d2['mean_min'])} 分・p50 {_c(d2['p50_min'])} 分・JSD {_c(d2['jsd15'])} / "
               f"立ち上がり(在席の率 対 第 8-1 表) {_c(s34['rise_diff_vs_a3_min'])} 分。対象 {s34['n_targets']} 体・"
               f"始まりが取れた {s34['n_found']} 体(立ち上がりの行の計画=計画上のセルの在席の率)。")
    if "diff_vs_a5" in s34:  # 〔第 3 期 3-1〕源 W20(暦 1a)
        d5, d25 = s34["diff_vs_a5"], s34["a2_minus_a5"]
        a5 = s34.get("a5_w20", {})
        out.append(f"〔3-1〕差(ラン − 錨 5=W20): 平均 {_c(d5['mean_min'])} 分・p50 {_c(d5['p50_min'])} 分・JSD "
                   f"{_c(d5['jsd15'])} / W17 − W20(参考): 平均 {_c(d25['mean_min'])} 分・p50 {_c(d25['p50_min'])} 分・"
                   f"JSD {_c(d25['jsd15'])}。錨 5 の体 {_c(a5.get('n_work'))}・表に無い体 {_c(a5.get('n_not_in_table'))}"
                   f"{('・' + str(a5['status'])) if a5.get('status') else ''}(合否にしない)。")
    out.append("")
    sens = a.get("sensitivity_area_dilate", {})
    if sens:
        out.append("### 感度: エリアの写像 ±50 m")
        out.append("")
        rows = [[lab, *(v["peak"][c] for c in AREA_IDS + ("total5",)), v["V_per_Res"], v["W_per_Res"]]
                for lab, v in sens.items()]
        out.append(_table(["膨張", *(COL_JA[c] for c in AREA_IDS + ("total5",)), "計 V/Res", "計 W/Res"], rows))
        out.append("")
    return out


def render_compare(cmp: Mapping[str, Any]) -> str:
    out = [f"# 前の版との差({cmp['prev_label']} → 今)", "",
           f"要約の値 {cmp['n_rows']} 件のうち変わった {cmp['n_changed']} 件。合否は書かない。", ""]
    out.append(_table(["腕", "前 commit・final", "今 commit・final"],
                      [[a, f"{cmp['prev_meta'].get(a, {}).get('commit')}・{cmp['prev_meta'].get(a, {}).get('final_hash')}",
                        f"{cmp['cur_meta'].get(a, {}).get('commit')}・{cmp['cur_meta'].get(a, {}).get('final_hash')}"]
                       for a in sorted(set(cmp["prev_meta"]) | set(cmp["cur_meta"]))]))
    out.append("")
    changed = [[r["arm"], r["key"], r["prev"], r["cur"], r["diff"]] for r in cmp["rows"] if not r["same"]]
    if changed:
        out.append(_table(["腕", "値", "前", "今", "差"], changed))
    else:
        out.append(f"変わった値は無い(要約の値 {cmp['n_rows']} 件がすべて同じ)。")
    out.append("")
    return "\n".join(out)


# ====================================================================== CLI
def _journal_args(items: Sequence[str]) -> dict[str, Path]:
    out = {}
    for it in items:
        arm, _, p = it.partition("=")
        if not p:
            raise SystemExit(f"--journal は 腕=道筋(いま {it!r})")
        out[arm] = Path(p)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="較正側の錨の計器(2-0・記録を読むだけ)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record", help="1 腕のランから体の journal を取る")
    r.add_argument("--arm", choices=tuple(ARMS), required=True)
    r.add_argument("--out", default="", help=f"{JOURNAL_PREFIX}<腕>{JOURNAL_SUFFIX}")
    r.add_argument("--agents", type=int, default=5_000)
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--world", default=DEFAULTS["world"])
    r.add_argument("--no-recorder", action="store_true", help="包まずに回す(final と呼数だけ・不変の確かめ)")
    g = sub.add_parser("gauge", help="記録(腕=道筋)から 4 つの量を出す")
    g.add_argument("--journal", action="append", default=[], required=True)
    g.add_argument("--out-dir", required=True)
    g.add_argument("--compare", default="")
    for k in DEFAULTS:
        if k != "records":
            g.add_argument(f"--{k.replace('_', '-')}", dest=k, default=None)
    rr = sub.add_parser("run", help="2 腕を記録して計器を回す(版上げごとの記録)")
    rr.add_argument("--scratch", required=True)
    rr.add_argument("--out-root", default=DEFAULTS["records"])
    rr.add_argument("--label", default="", help="既定 <日付>_<commit>")
    rr.add_argument("--compare", default="")
    rr.add_argument("--agents", type=int, default=5_000)
    rr.add_argument("--seed", type=int, default=1)
    rr.add_argument("--world", default=DEFAULTS["world"])
    c = sub.add_parser("compare", help="前の版のフォルダと今のフォルダの差の表")
    c.add_argument("--prev", required=True)
    c.add_argument("--cur", required=True)
    args = ap.parse_args(argv)

    if args.cmd == "record":
        out = Path(args.out or f"{JOURNAL_PREFIX}{args.arm}{JOURNAL_SUFFIX}")
        meta = record(args.arm, out_path=out, n_agents=args.agents, seed=args.seed, world_dir=args.world,
                      use_recorder=not args.no_recorder)
        print(json.dumps(meta, ensure_ascii=False))
        return 0
    if args.cmd == "gauge":
        paths = resolve_paths({k: getattr(args, k, None) for k in DEFAULTS})
        doc = gauge(_journal_args(args.journal), paths=paths, out_dir=Path(args.out_dir),
                    compare_dir=Path(args.compare) if args.compare else None)
        print(json.dumps({a: v["summary"] for a, v in _strip_arrays(doc)["arms"].items()}, ensure_ascii=False))
        return 0
    if args.cmd == "run":
        scratch = Path(args.scratch)
        scratch.mkdir(parents=True, exist_ok=True)
        journals: dict[str, Path] = {}
        metas = {}
        for arm in ARMS:  # 腕ごとに子プロセス(エンジンのモジュールの状態を持ち越さない)
            jp = scratch / f"{JOURNAL_PREFIX}{arm}{JOURNAL_SUFFIX}"
            cmd = [sys.executable, str(Path(__file__)), "record", "--arm", arm, "--out", str(jp),
                   "--agents", str(args.agents), "--seed", str(args.seed), "--world", args.world]
            got = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(REPO))
            if got.returncode != 0:
                print(got.stderr[-4000:], file=sys.stderr)
                return got.returncode
            metas[arm] = json.loads(got.stdout.strip().splitlines()[-1])
            journals[arm] = jp
            print(arm, metas[arm]["final_hash"], metas[arm]["llm_calls"], metas[arm]["wall_s_nondeterministic"],
                  flush=True)
        head = metas[next(iter(metas))]["commit"] or "nocommit"
        label = args.label or f"{_dt.date.today().isoformat()}_{head}"
        paths = resolve_paths({"world": args.world})
        gauge(journals, paths=paths, out_dir=Path(args.out_root) / label,
              compare_dir=Path(args.compare) if args.compare else None)
        print(label)
        return 0
    if args.cmd == "compare":
        guard = ReadGuard(files={}, dirs={"prev": Path(args.prev), "cur": Path(args.cur)},
                          protect=[REPO / "data", REPO / "docs"], repo_root=REPO, allow_journals=False)
        with guard.active():
            a = guard.read_json(Path(args.prev) / "anchor_gauge.json")
            b = guard.read_json(Path(args.cur) / "anchor_gauge.json")
            cmp = compare_docs(a, b, prev_label=Path(args.prev).name)
            (Path(args.cur) / f"compare_vs_{Path(args.prev).name}.md").write_text(render_compare(cmp), encoding="utf-8",
                                                                                   newline="\n")
        print(json.dumps({"n_rows": cmp["n_rows"], "n_changed": cmp["n_changed"]}, ensure_ascii=False))
        return 0
    return 2  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
