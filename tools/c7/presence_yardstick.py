# -*- coding: utf-8 -*-
"""presence_yardstick.py — **在圏の物差し**。ランの「どこに何体居るか」を現実アンカーと並べる。

なぜ要るか
    D-66(域外常住者が深夜も域内に居る)の修正は「前より良くなったか」で受け入れる。
    ところが良し悪しを測る器が無く、毎回その場で数え方を決めていた=**比較にならない**。
    本ツールは**同じ入力・同じ数え方・同じアンカー**で表を出す。C7 の再ラン前修正
    (D-66 計画実行層)の前後比較がそのまま並ぶ。

パターン台帳ゲート(CLAUDE.md §4)
    「深夜の 139 ha に何人居るか」「昼夜比はいくつか」という**現実パターン**との照合に使う。

数え方は既存物を再利用する(二重実装しない)
    セル→5 エリアの写像は ``tools/c7/c7lib.build_area_map``(``area_axes_v0.json``)、
    時×エリアの集計は ``c7lib.OccupancySeries.area_hour_table``、journal の読みは
    ``tools/c7/occupancy_series.load_journal``。本ツールが足すのは**種別軸**と
    **アンカーとの距離**だけ。

現実側の数値はここに書かない
    全て ``docs/bench/anchors/presence_anchors_v0.json``(source/tag/verified_by 付き)から読む。
    **合格線は書かない**——距離を出すだけで、良否は親が決める(CLAUDE.md §2)。

入口
    ``--journal RUN.npz``  エンジンの ``--occupancy-every 60 --occupancy-out`` が出す生 journal
                           (``ticks``/``cell_counts``/``kind_cell_counts``/``meta``)。**種別行が出る**。
    ``--series RUN.json``  ``occupancy_series.py`` の集計済み JSON(``area_hour_counts`` (24,5))。
                           bbox 全体と種別行は**入っていない**ので空欄になる。
    ``--summary RUN.txt``  cli の標準出力(``起床率/時`` ``起床率(在圏)/時`` ``D-62 計画就寝``
                           ``呼/時`` ``[run] n=``)。**``起床率(在圏)/時`` があれば a(h) との
                           比較にそちらを使う**(D-66 計画実行層のランは域外の体が多く、
                           D-62 定義の ``起床率/時`` は分母が揃わない)。

例::

    python tools/c7/presence_yardstick.py --journal runs/after.npz --summary runs/after.txt \\
        --before runs/before.npz --before-summary runs/before.txt --out out/
    python tools/c7/presence_yardstick.py --series docs/bench/c7/occupancy_series_c7-day-2.json \\
        --n-agents 390067 --label c7-day-2 --out out/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c7lib  # noqa: E402
import occupancy_series as occ  # noqa: E402

AREA_IDS = c7lib.AREA_IDS
REPO_ROOT = c7lib.REPO_ROOT

#: 既定のアンカー台帳(現実側の数値は**全てここ**にある)。
DEFAULT_ANCHORS_PATH = REPO_ROOT / "docs" / "bench" / "anchors" / "presence_anchors_v0.json"

#: ``AgentKind``(src/shibuya/agents/state.py)の順と名前。journal の kind 軸に対応。
KIND_JA: tuple[str, ...] = (
    "通勤", "来街", "従業", "住民", "指令", "通学", "定期来街", "訪日", "乗務",
)
N_KINDS = len(KIND_JA)

#: D-66 の直接指標になる種別 = **域外常住のはずの種別**(通勤・来街・定期来街・乗務)。
#: 深夜に域内に居れば居るほど「域外常住者が帰っていない」。
#: **訪日(7)は含めない**(第170 層2 指摘→第173 ユーザー決定 A3): W16 の訪日 17,404 体は全員に
#: 宿泊施設の就寝行があり、舞台の中で寝るのが正当。参考行(``LODGING_KINDS``)として別掲し判定に使わない。
D66_KINDS: tuple[int, ...] = (0, 1, 6, 8)
#: 宿泊施設で就寝する種別(参考行・判定外)。
LODGING_KINDS: tuple[int, ...] = (7,)

#: 表に出す時刻(3 時間刻み)。
REPORT_HOURS: tuple[int, ...] = (0, 3, 6, 9, 12, 15, 18, 21)

#: 昼夜比の分母(深夜)と分子(昼)。
NIGHT_HOUR = 3
DAY_HOUR = 9
NOON_HOUR = 12


# ---------------------------------------------------------------- アンカー台帳

#: アンカー 1 件に必ず要る欄(CLAUDE.md §5「出典・数値は親が一次確認」の受け皿)。
ANCHOR_REQUIRED: tuple[str, ...] = ("source", "verified_by", "tag")
ANCHOR_TAGS: frozenset[str] = frozenset({"anchor", "estimate", "expedient"})


def check_anchors(doc: Mapping[str, Any]) -> None:
    """必須欄(source/verified_by/tag)と値の存在を検査する。**純関数**(例外で知らせる)。"""
    anchors = doc.get("anchors")
    if not isinstance(anchors, dict) or not anchors:
        raise ValueError("anchors が空")
    for key, a in anchors.items():
        for need in ANCHOR_REQUIRED:
            if not a.get(need):
                raise ValueError(f"アンカー {key} に {need} が無い")
        if a["tag"] not in ANCHOR_TAGS:
            raise ValueError(f"アンカー {key} の tag が不正: {a['tag']}")
        if not any(k in a for k in ("value", "values", "shares", "low")):
            raise ValueError(f"アンカー {key} に値(value/values/shares/low)が無い")


def load_anchors(path: str | Path | None = None) -> dict[str, Any]:
    """アンカー台帳を読む。**必須欄が欠けていたら落とす**(推測で埋めない)。"""
    p = Path(path) if path else DEFAULT_ANCHORS_PATH
    doc = json.loads(p.read_text(encoding="utf-8"))
    check_anchors(doc)
    doc["_path"] = str(p)
    return doc


# ---------------------------------------------------------------- 要約テキストの読み

_WAKE_RE = re.compile(r"起床率/時\s+((?:\d{2}:[-0-9.]+\s*)+)")
#: D-66 の補助欄(**在圏の体だけ**の非就寝率)。あれば a(h) との比較に**こちらを優先**する。
_WAKE_IN_AREA_RE = re.compile(r"起床率\(在圏\)/時\s+((?:\d{2}:[-0-9.]+\s*)+)")
_CALLS_RE = re.compile(r"呼/時\s+((?:\d{2}:\d+\s*)+)")
_PAIR_RE = re.compile(r"(\d{2}):([-0-9.]+)")
_N_AGENTS_RE = re.compile(r"\[run\]\s+n=(\d+)")
#: ``D-62 計画就寝`` 行の欄名(``engine/run.py`` の書式に対応)。
_SLEEP_FIELDS: dict[str, str] = {
    "slept": "その場", "arrived": "着いて", "walking": "歩行中", "woke": "計画起床",
    "riding": "乗車中", "outside": "域外", "conversing": "会話中",
    "asleep": "就寝済", "unreachable": "行けない",
}


def _pairs_to_24(blob: str, cast: Any) -> list[Any]:
    """``00:0.185 01:0.237 …`` → 索引 0..23 の配列(欠けた時は 0 で埋める)。"""
    out: list[Any] = [cast(0)] * 24
    for h, v in _PAIR_RE.findall(blob):
        i = int(h)
        if 0 <= i < 24:
            out[i] = cast(v)
    return out


def parse_wake_rate(text: str) -> list[float] | None:
    """``起床率/時 00:0.185 …`` の 24 値(**割合**)。行が無ければ None。**純関数**。

    D-62 の定義=**域外滞在・乗車中も「起きている」に数える**。D-66 計画実行層が入った
    ランではこの欄が自動的に上がるので、a(h) と並べるなら ``parse_wake_rate_in_area``
    を優先する(``read_summary`` がそうしている)。
    """
    m = _WAKE_RE.search(text)
    return _pairs_to_24(m.group(1), float) if m else None


def parse_wake_rate_in_area(text: str) -> list[float] | None:
    """``起床率(在圏)/時 00:0.485 …`` の 24 値。行が無ければ None。**純関数**。

    定義 = **在圏(``transit_state == 0``)の体のうち ``activity != SLEEPING`` の割合**
    (D-66 計画実行層の補助欄・``engine.run.RunResult.wake_rate_in_area_by_hour``)。
    """
    m = _WAKE_IN_AREA_RE.search(text)
    return _pairs_to_24(m.group(1), float) if m else None


def parse_calls_by_hour(text: str) -> list[int] | None:
    """``呼/時 00:1550 …`` の 24 値。行が無ければ None。**純関数**。"""
    m = _CALLS_RE.search(text)
    return _pairs_to_24(m.group(1), int) if m else None


def parse_planned_sleep(text: str) -> dict[str, int] | None:
    """``D-62 計画就寝 …`` 行 → 内訳。行が無ければ None。**純関数**。"""
    line = next((ln for ln in text.splitlines() if "D-62 計画就寝" in ln), None)
    if line is None:
        return None
    out: dict[str, int] = {}
    for key, word in _SLEEP_FIELDS.items():
        m = re.search(rf"{word}\s+([\d,]+)", line)
        if m:
            out[key] = int(m.group(1).replace(",", ""))
    return out


def parse_n_agents(text: str) -> int | None:
    """``[run] n=5000 …`` の個体数。無ければ None。**純関数**。"""
    m = _N_AGENTS_RE.search(text)
    return int(m.group(1)) if m else None


def read_summary(path: str | Path | None) -> dict[str, Any]:
    """要約テキスト → 使う欄だけの辞書(読めない欄は None のまま=推測しない)。"""
    if not path:
        return {"path": None, "wake_rate": None, "wake_rate_plain": None,
                "wake_rate_in_area": None, "wake_rate_basis": None,
                "planned_sleep": None, "calls_by_hour": None, "n_agents": None}
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    plain = parse_wake_rate(text)
    in_area = parse_wake_rate_in_area(text)
    return {
        "path": str(path),
        # a(h) との比較に**実際に使う**系列。在圏版があればそちらが正(分母が揃う)。
        "wake_rate": in_area if in_area is not None else plain,
        "wake_rate_plain": plain,
        "wake_rate_in_area": in_area,
        "wake_rate_basis": ("in_area" if in_area is not None else
                            ("all_agents" if plain is not None else None)),
        "planned_sleep": parse_planned_sleep(text),
        "calls_by_hour": parse_calls_by_hour(text),
        "n_agents": parse_n_agents(text),
    }


# ---------------------------------------------------------------- 在圏(1 ラン)


def hour_mean(values: np.ndarray, hours: Sequence[int]) -> np.ndarray:
    """``(n_samples, …)`` → ``(24, …)``。同じ時の標本は平均。

    ``c7lib.OccupancySeries.area_hour_table`` と**同じ規則**(そちらは (24,5) 専用)。
    """
    v = np.asarray(values, dtype=np.float64)
    out = np.zeros((24,) + v.shape[1:], dtype=np.float64)
    n = np.zeros(24, dtype=np.float64)
    np.add.at(out, np.asarray(hours, dtype=np.int64), v)
    np.add.at(n, np.asarray(hours, dtype=np.int64), 1.0)
    return out / np.maximum(n, 1.0).reshape((24,) + (1,) * (v.ndim - 1))


def kind_tables(kind_cell: np.ndarray, hours: Sequence[int],
                amap: c7lib.AreaMap) -> tuple[np.ndarray, np.ndarray]:
    """``(T,9,C)`` 種別×セル → ``(24,9)`` の 5 エリア内 と bbox 全体。**純関数**。"""
    arr = np.asarray(kind_cell, dtype=np.int64)
    if arr.ndim != 3:
        raise ValueError(f"kind_cell_counts は (T,K,C) のはず: {arr.shape}")
    if arr.shape[2] != amap.n_cells:
        raise ValueError(f"セル数が違う: journal {arr.shape[2]} vs map {amap.n_cells}")
    inside = amap.area_of_cell >= 0
    return (hour_mean(arr[:, :, inside].sum(axis=2), hours),
            hour_mean(arr.sum(axis=2), hours))


@dataclass
class Presence:
    """1 ランの在圏。journal(生)からも series JSON(集計済み)からも作れる。"""

    label: str
    #: ``(24,5)`` 時×エリアの在圏数。
    area_hour: np.ndarray
    #: ``(24,)`` bbox 全体(5 エリア外を含む)。series JSON からは取れない=None。
    bbox_hour: np.ndarray | None = None
    #: ``(24,9)`` 時×種別(5 エリア内)。journal のみ。
    kind_area_hour: np.ndarray | None = None
    #: ``(24,9)`` 時×種別(bbox 全体)。journal のみ。
    kind_bbox_hour: np.ndarray | None = None
    n_agents: int | None = None
    n_agents_source: str = "不明"
    summary: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def five(self) -> np.ndarray:
        """``(24,)`` 5 エリア合計。"""
        return np.asarray(self.area_hour, dtype=np.float64).sum(axis=1)


def _resolve_n_agents(cli: int | None, summary: Mapping[str, Any],
                      meta: Mapping[str, Any], bbox_hour: np.ndarray | None,
                      ) -> tuple[int | None, str]:
    """個体数の出所を**明示して**決める(cli > 要約 > journal meta > bbox 最大)。"""
    if cli:
        return int(cli), "cli"
    if summary.get("n_agents"):
        return int(summary["n_agents"]), "summary([run] n=)"
    for key in ("agents", "n_agents"):
        if meta.get(key):
            return int(meta[key]), f"meta.{key}"
    if bbox_hour is not None and np.asarray(bbox_hour).size:
        return int(round(float(np.max(bbox_hour)))), "bbox 最大(下界・域外滞在ぶんを含まない)"
    return None, "不明"


def presence_from_journal(path: str | Path, amap: c7lib.AreaMap, *, label: str = "run",
                          summary: Mapping[str, Any] | None = None,
                          n_agents: int | None = None) -> Presence:
    """journal(``.npz``)→ ``Presence``。読みと 5 エリア集計は既存物に任せる。"""
    series = occ.load_journal(path)              # amap=None: 属性表(5×3)は要らない
    hours = series.hour_of_sample()
    area_hour = series.area_hour_table(amap)     # (24,5)・c7lib の集計をそのまま使う
    bbox_hour = hour_mean(np.asarray(series.cell_counts, dtype=np.int64).sum(axis=1), hours)
    kind_area = kind_bbox = None
    with np.load(Path(path), allow_pickle=False) as z:
        if "kind_cell_counts" in z.files:
            kind_area, kind_bbox = kind_tables(z["kind_cell_counts"], hours, amap)
    sm = dict(summary or {})
    n, src = _resolve_n_agents(n_agents, sm, series.meta, bbox_hour)
    return Presence(label=label, area_hour=area_hour, bbox_hour=bbox_hour,
                    kind_area_hour=kind_area, kind_bbox_hour=kind_bbox,
                    n_agents=n, n_agents_source=src, summary=sm,
                    meta={"input": "journal", "path": str(path), "n_samples": series.n_samples,
                          "n_cells": int(series.cell_counts.shape[1]),
                          "journal_meta": {k: v for k, v in series.meta.items()
                                           if k != "source"}})


def presence_from_series(path: str | Path, *, label: str = "run",
                         summary: Mapping[str, Any] | None = None,
                         n_agents: int | None = None) -> Presence:
    """``occupancy_series.py`` の集計済み JSON → ``Presence``(bbox と種別は空欄)。"""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if "area_hour_counts" not in doc:
        raise ValueError(f"{path} に area_hour_counts が無い(生 journal なら --journal)")
    area_hour = np.asarray(doc["area_hour_counts"], dtype=np.float64)
    if area_hour.shape != (24, len(AREA_IDS)):
        raise ValueError(f"area_hour_counts の形が (24,5) でない: {area_hour.shape}")
    if list(doc.get("area_ids", AREA_IDS)) != list(AREA_IDS):
        raise ValueError("area_ids の並びが c7lib.AREA_IDS と違う")
    sm = dict(summary or {})
    n, src = _resolve_n_agents(n_agents, sm, doc.get("meta", {}), None)
    return Presence(label=label, area_hour=area_hour, n_agents=n, n_agents_source=src,
                    summary=sm,
                    meta={"input": "series", "path": str(path),
                          "series_meta": dict(doc.get("meta", {})),
                          "area_attr_counts": doc.get("area_attr_counts")})


# ---------------------------------------------------------------- 指標


def scale_factor(p: Presence, target: int) -> float | None:
    """``target`` 体換算の縮尺(**線形・expedient**)。個体数が分からなければ None。"""
    if not p.n_agents:
        return None
    return float(target) / float(p.n_agents)


def _kind_rows(p: Presence, f: float | None) -> dict[str, Any] | None:
    """03 時の種別内訳(5 エリア内)。journal 以外では None。"""
    if p.kind_area_hour is None:
        return None
    k5 = np.asarray(p.kind_area_hour, dtype=np.float64)[NIGHT_HOUR]
    kb = (np.asarray(p.kind_bbox_hour, dtype=np.float64)[NIGHT_HOUR]
          if p.kind_bbox_hour is not None else None)
    tot5 = float(k5.sum())
    rows = []
    for i in range(min(N_KINDS, int(k5.size))):
        rows.append({
            "kind": i,
            "name": KIND_JA[i],
            "d66": i in D66_KINDS,
            "lodging": i in LODGING_KINDS,
            "count_five_area": round(float(k5[i]), 1),
            "share_of_five_area": round(float(k5[i]) / tot5, 4) if tot5 > 0 else None,
            "count_bbox": None if kb is None else round(float(kb[i]), 1),
            "count_five_area_scaled": None if f is None else round(float(k5[i]) * f, 1),
        })
    d66 = float(sum(k5[i] for i in D66_KINDS if i < k5.size))
    return {
        "hour": NIGHT_HOUR,
        "rows": rows,
        "five_area_total": round(tot5, 1),
        "d66_total": {
            "kinds": [KIND_JA[i] for i in D66_KINDS],
            "count_five_area": round(d66, 1),
            "share_of_five_area": round(d66 / tot5, 4) if tot5 > 0 else None,
            "count_five_area_scaled": None if f is None else round(d66 * f, 1),
            "note": "域外常住のはずの種別が深夜に域内に居る体数=D-66 の直接指標"
                    "(訪日は宿泊施設で就寝=参考行・判定外・第173)。",
        },
    }


def _wake_rows(p: Presence, a: Mapping[str, Any]) -> dict[str, Any] | None:
    """起床率/時 と a(h) の差(要約が無ければ None)。"""
    wr = p.summary.get("wake_rate")
    if not wr:
        return None
    anchor = [v / 100.0 for v in a["wake_rate_tokyo_weekday"]["values"]]
    diff = [round(float(wr[h]) - anchor[h], 4) for h in range(24)]
    idx = int(np.argmax(np.abs(np.asarray(diff, dtype=np.float64))))
    return {
        "run": [round(float(v), 4) for v in wr],
        "anchor": [round(v, 4) for v in anchor],
        "diff": diff,
        "max_abs_diff": abs(diff[idx]),
        "max_abs_hour": idx,
        "diff_03": diff[NIGHT_HOUR],
        "diff_12": diff[NOON_HOUR],
        "anchor_source": a["wake_rate_tokyo_weekday"]["source"],
        "anchor_caveat": a["wake_rate_tokyo_weekday"].get("caveat"),
        # どちらの系列で測ったか(**分母が違う**ので前後比較のときに要る)
        "basis": p.summary.get("wake_rate_basis"),
        "basis_note": (
            "定義=在圏の体の非就寝率(transit_state==0 の体のうち activity != SLEEPING)"
            if p.summary.get("wake_rate_basis") == "in_area"
            else "定義=全体の非就寝率(D-62・域外滞在と乗車中も『起きている』に数える)"
        ),
    }


def _distance(p: Presence, a: Mapping[str, Any], f: float | None) -> dict[str, Any]:
    """現実比(ラン ÷ 現実)。1.0 が一致・>1 が過大。縮尺が無いときは生値で割る。"""
    five = p.five
    v09 = float(five[DAY_HOUR]) * (f if f is not None else 1.0)
    v03 = float(five[NIGHT_HOUR]) * (f if f is not None else 1.0)
    lo = float(a["night_presence_estimate"]["low"])
    hi = float(a["night_presence_estimate"]["high"])
    gap = 0.0 if lo <= v03 <= hi else min(abs(v03 - lo), abs(v03 - hi))
    return {
        "scaled": f is not None,
        "day_09_vs_core9_daytime": round(v09 / float(a["core9_daytime_population"]["value"]), 4),
        "day_09_vs_pt_peak": round(v09 / float(a["pt_area_daytime_peak"]["value"]), 4),
        "night_03_vs_core9_night": round(v03 / float(a["core9_night_population"]["value"]), 4),
        "night_03_vs_estimate_high": round(v03 / hi, 4),
        "night_03_in_estimate_band": bool(lo <= v03 <= hi),
        "night_03_band_gap": round(gap, 1),
        "values": {"day_09": round(v09, 1), "night_03": round(v03, 1)},
    }


def measures(p: Presence, anchors: Mapping[str, Any], *, target: int) -> dict[str, Any]:
    """1 ランの在圏 → 表の素(JSON にそのまま入る)。**純関数**。"""
    a = anchors["anchors"]
    f = scale_factor(p, target)
    five = p.five
    bbox = p.bbox_hour
    rows = []
    for h in REPORT_HOURS:
        rows.append({
            "hour": int(h),
            "five_area": round(float(five[h]), 1),
            "bbox": None if bbox is None else round(float(bbox[h]), 1),
            "five_area_scaled": None if f is None else round(float(five[h]) * f, 1),
            "bbox_scaled": None if (bbox is None or f is None) else round(float(bbox[h]) * f, 1),
        })
    night = float(five[NIGHT_HOUR])
    ratios = {
        "r_day_night_09_03": round(float(five[DAY_HOUR]) / night, 4) if night > 0 else None,
        "r_noon_night_12_03": round(float(five[NOON_HOUR]) / night, 4) if night > 0 else None,
    }
    return {
        "label": p.label,
        "input": p.meta.get("input"),
        "path": p.meta.get("path"),
        "summary_path": p.summary.get("path"),
        "n_agents": p.n_agents,
        "n_agents_source": p.n_agents_source,
        "scale": {
            "target_population": int(target),
            "factor": None if f is None else round(f, 6),
            "tag": "expedient",
            "note": "縮尺は線形(体数に比例)。混雑・待ち行列・容量は非線形なので"
                    "絶対値の一致は主張しない=向きと桁を見るための列。",
        },
        "presence_by_hour": rows,
        "area_ids": list(AREA_IDS),
        "area_hour_counts": [[round(float(v), 1) for v in row]
                             for row in np.asarray(p.area_hour, dtype=np.float64)],
        "ratios": ratios,
        "kind_at_03": _kind_rows(p, f),
        "wake_rate": _wake_rows(p, a),
        "planned_sleep": p.summary.get("planned_sleep"),
        "distance": _distance(p, a, f),
        "meta": p.meta,
    }


# ---------------------------------------------------------------- 前後比較


def metric_entries(m: Mapping[str, Any], anchors: Mapping[str, Any]) -> list[dict[str, Any]]:
    """比較に使う**スカラー指標**の一覧(値・目標・向き)。**純関数**。

    ``target`` があれば「目標への距離が縮んだか」、``band`` があれば「帯への隙間が縮んだか」、
    ``direction='lower'`` は「小さくなったか」。**合格線は持たない**(距離だけ)。
    """
    a = anchors["anchors"]
    by_hour = {r["hour"]: r for r in m["presence_by_hour"]}

    def val(h: int) -> float | None:
        r = by_hour.get(h)
        if r is None:
            return None
        return r["five_area_scaled"] if r["five_area_scaled"] is not None else r["five_area"]

    ent: list[dict[str, Any]] = [
        {"metric": "在圏 09時 5エリア(換算) 対 昼間人口", "value": val(DAY_HOUR),
         "target": float(a["core9_daytime_population"]["value"]),
         "note": "対 昼間人口 130,167(中核9町丁目 1.39 km²・anchor)"},
        {"metric": "在圏 09時 5エリア(換算) 対 PT ピーク", "value": val(DAY_HOUR),
         "target": float(a["pt_area_daytime_peak"]["value"]),
         "note": "対 日中滞在者ピーク 145,000(渋谷駅周辺 約139 ha・anchor)"},
        {"metric": "在圏 03時 5エリア(換算) 対 常住", "value": val(NIGHT_HOUR),
         "target": float(a["core9_night_population"]["value"]),
         "note": "対 常住 8,810(anchor・下限側の目安)"},
        {"metric": "在圏 03時 5エリア(換算) 対 深夜在圏帯", "value": val(NIGHT_HOUR),
         "band": [float(a["night_presence_estimate"]["low"]),
                  float(a["night_presence_estimate"]["high"])],
         "note": "対 深夜在圏推定 1.5〜3 万人(estimate)"},
        {"metric": "昼夜比 09/03", "value": m["ratios"]["r_day_night_09_03"],
         "target": float(a["core9_day_night_ratio"]["value"]),
         "note": "対 昼夜間人口比率 14.8(anchor)"},
        {"metric": "昼夜比 12/03", "value": m["ratios"]["r_noon_night_12_03"],
         "target": float(a["core9_day_night_ratio"]["value"]), "note": "同上(12時版)"},
    ]
    k = m.get("kind_at_03")
    if k:
        d = k["d66_total"]
        ent.append({
            "metric": "03時 D-66 種別 在圏(換算)",
            "value": (d["count_five_area_scaled"] if d["count_five_area_scaled"] is not None
                      else d["count_five_area"]),
            "direction": "lower",
            "note": "通勤+来街+定期来街+乗務。域外常住のはずの種別=減るほど D-66 の意図に近い"
                    "(訪日は宿泊施設で就寝=参考行・第173)"})
        ent.append({"metric": "03時 D-66 種別 全体比", "value": d["share_of_five_area"],
                    "direction": "lower", "note": "同 5エリア在圏に占める割合"})
        for row in k["rows"]:
            if row["d66"]:
                ent.append({"metric": f"03時 {row['name']} 在圏(生)",
                            "value": row["count_five_area"], "direction": "lower",
                            "note": "5エリア内・縮尺前"})
            elif row.get("lodging"):
                ent.append({"metric": f"03時 {row['name']} 在圏(生・参考)",
                            "value": row["count_five_area"],
                            "note": "宿泊施設で就寝する種別(訪日は全員に宿泊施設の就寝行)"
                                    "=舞台の中で寝るのが正当・判定に使わない(第173)"})
    w = m.get("wake_rate")
    if w:
        ent += [
            {"metric": "起床率 最大絶対差 vs a(h)", "value": w["max_abs_diff"], "target": 0.0,
             "note": f"最大は {w['max_abs_hour']:02d} 時"},
            {"metric": "起床率 03時 差", "value": w["diff_03"], "target": 0.0,
             "note": "run − a(3)=0.035"},
            {"metric": "起床率 12時 差", "value": w["diff_12"], "target": 0.0,
             "note": "run − a(12)=0.978"},
        ]
    s = m.get("planned_sleep")
    if s:
        ent += [
            {"metric": "計画就寝 その場", "value": s.get("slept"),
             "note": "アンカー無し(参考)。職場等でその場就寝した体"},
            {"metric": "計画就寝 着いて", "value": s.get("arrived"), "note": "アンカー無し(参考)"},
            {"metric": "寝かせなかった 域外", "value": s.get("outside"),
             "note": "アンカー無し(参考)。域外に居たので寝かせなかった体"},
        ]
    ent += [
        {"metric": "距離 09時/現実(core9)", "value": m["distance"]["day_09_vs_core9_daytime"],
         "target": 1.0, "note": "1.0 が一致・>1 が過大"},
        {"metric": "距離 09時/現実(PT)", "value": m["distance"]["day_09_vs_pt_peak"],
         "target": 1.0, "note": "同上"},
        {"metric": "距離 03時/常住 8,810", "value": m["distance"]["night_03_vs_core9_night"],
         "target": 1.0, "note": "1.0 が常住と同数"},
        {"metric": "距離 03時/推定上限 30,000",
         "value": m["distance"]["night_03_vs_estimate_high"], "target": 1.0,
         "note": "1.0 が推定帯の上端"},
    ]
    return ent


def _gap(entry: Mapping[str, Any], value: float | None) -> float | None:
    """目標(または帯)からの距離。目標も帯も無ければ None。"""
    if value is None:
        return None
    if entry.get("target") is not None:
        return abs(float(value) - float(entry["target"]))
    band = entry.get("band")
    if band:
        lo, hi = float(band[0]), float(band[1])
        v = float(value)
        return 0.0 if lo <= v <= hi else min(abs(v - lo), abs(v - hi))
    return None


def compare(after: Mapping[str, Any], before: Mapping[str, Any],
            anchors: Mapping[str, Any]) -> list[dict[str, Any]]:
    """before/after の同名指標を並べ、**現実側へ近づいたか**の bool を付ける。**純関数**。

    合格線は持たない(近づいたか否かだけ)。目標も向きも無い行は ``closer=None``。
    **行は after 側で決まる**(after に出せない指標=例えば series JSON には種別軸が無い、は
    before に有っても表に出ない)。前後比較は**同じ入口**(journal 同士)で取ること。
    """
    b = {e["metric"]: e for e in metric_entries(before, anchors)}
    out: list[dict[str, Any]] = []
    for e in metric_entries(after, anchors):
        pre = b.get(e["metric"], {})
        bv, av = pre.get("value"), e.get("value")
        gb, ga = _gap(e, bv), _gap(e, av)
        closer: bool | None = None
        if gb is not None and ga is not None:
            closer = bool(ga < gb)
        elif e.get("direction") == "lower" and bv is not None and av is not None:
            closer = bool(float(av) < float(bv))
        delta = (float(av) - float(bv)) if (bv is not None and av is not None) else None
        out.append({
            "metric": e["metric"], "before": bv, "after": av,
            "delta": None if delta is None else round(delta, 4),
            "target": e.get("target"), "band": e.get("band"),
            "direction": e.get("direction"),
            "gap_before": None if gb is None else round(gb, 4),
            "gap_after": None if ga is None else round(ga, 4),
            "closer": closer, "note": e.get("note"),
        })
    return out


# ---------------------------------------------------------------- 報告(Markdown)


def _num(v: Any, nd: int = 1) -> str:
    """None は「—」・bool は yes/no・整数は桁区切り。"""
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int):
        return f"{v:,}"
    return f"{float(v):,.{nd}f}"


def _delta(b: Any, a: Any, nd: int = 1) -> str:
    if b is None or a is None:
        return "—"
    d = float(a) - float(b)
    return f"{d:+,.{nd}f}"


def _hour_table(after: Mapping[str, Any], before: Mapping[str, Any] | None,
                key: str, scaled_key: str) -> str:
    ra = {r["hour"]: r for r in after["presence_by_hour"]}
    rb = {r["hour"]: r for r in (before or {}).get("presence_by_hour", [])}
    if before is None:
        head = ["時", "在圏", f"{after['scale']['target_population']:,}体換算"]
        rows = [[f"{h:02d}", _num(ra[h][key]), _num(ra[h][scaled_key])] for h in REPORT_HOURS]
    else:
        head = ["時", "before", "after", "差", "before(換算)", "after(換算)", "差(換算)"]
        rows = [[f"{h:02d}", _num(rb.get(h, {}).get(key)), _num(ra[h][key]),
                 _delta(rb.get(h, {}).get(key), ra[h][key]),
                 _num(rb.get(h, {}).get(scaled_key)), _num(ra[h][scaled_key]),
                 _delta(rb.get(h, {}).get(scaled_key), ra[h][scaled_key])]
                for h in REPORT_HOURS]
    return c7lib.markdown_table(head, rows)


def _scalar_table(pairs: Sequence[tuple[str, Any, Any]], compare_mode: bool, nd: int = 3) -> str:
    """``(名前, before, after)`` の並び → 表。"""
    if compare_mode:
        return c7lib.markdown_table(
            ["指標", "before", "after", "差"],
            [[n, _num(b, nd), _num(a, nd), _delta(b, a, nd)] for n, b, a in pairs])
    return c7lib.markdown_table(["指標", "値"], [[n, _num(a, nd)] for n, _b, a in pairs])


def markdown(payload: Mapping[str, Any]) -> str:
    """JSON と同じ内容の表。**合格線は書かない**(距離と bool だけ)。"""
    after = payload["after"]
    before = payload.get("before")
    cm = before is not None
    a = payload["anchors_echo"]
    tgt = after["scale"]["target_population"]
    out: list[str] = [
        "# 在圏の物差し(presence yardstick)"
        + f" — {after['label']}" + (f" vs {before['label']}" if cm else ""),
        "",
        f"- アンカー台帳: `{payload['anchors_path']}`({payload['anchors_version']})",
        f"- after: `{after['path']}`(入力 {after['input']}・n_agents {_num(after['n_agents'])}"
        f"[{after['n_agents_source']}]・縮尺 ×{_num(after['scale']['factor'], 4)} → {tgt:,} 体換算"
        "・**expedient**=線形)",
    ]
    if cm:
        out.append(
            f"- before: `{before['path']}`(入力 {before['input']}・n_agents "
            f"{_num(before['n_agents'])}[{before['n_agents_source']}]・縮尺 "
            f"×{_num(before['scale']['factor'], 4)})")
    out += [
        f"- 現実側: 昼間人口 {a['core9_daytime_population']:,} / 常住 "
        f"{a['core9_night_population']:,} / 昼夜比 {a['core9_day_night_ratio']}"
        f"(中核9町丁目 1.39 km²)・PT 日中ピーク {a['pt_area_daytime_peak']:,}(約139 ha)"
        f"・深夜在圏推定 {a['night_presence_low']:,}〜{a['night_presence_high']:,}(estimate)",
        "- **合格線は書かない**。距離と「前より現実側へ近づいたか」の bool だけを出す(判定は親)。",
        "",
        "## 1 在圏(5 エリア合計)",
        "",
        _hour_table(after, before, "five_area", "five_area_scaled"),
    ]
    if after["presence_by_hour"][0]["bbox"] is not None:
        out += ["", "### 1b 在圏(bbox 全体・5 エリア外を含む)", "",
                _hour_table(after, before, "bbox", "bbox_scaled")]
    out += [
        "", "## 2 昼夜比(5 エリア)", "",
        _scalar_table([
            ("昼夜比 09/03", (before or {}).get("ratios", {}).get("r_day_night_09_03"),
             after["ratios"]["r_day_night_09_03"]),
            ("昼夜比 12/03", (before or {}).get("ratios", {}).get("r_noon_night_12_03"),
             after["ratios"]["r_noon_night_12_03"]),
            ("現実 昼夜間人口比率", None if not cm else a["core9_day_night_ratio"],
             a["core9_day_night_ratio"]),
        ], cm, nd=3),
    ]
    out += ["", "## 3 03 時の種別内訳(5 エリア内)", ""]
    ka, kb = after.get("kind_at_03"), (before or {}).get("kind_at_03")
    if ka is None:
        out.append("(種別軸は journal(`kind_cell_counts`)にしか無い。この入力では出せない)")
    else:
        bmap = {r["name"]: r for r in (kb or {}).get("rows", [])}
        if cm and kb:
            head = ["種別", "D-66", "before", "after", "差", "before 全体比", "after 全体比"]
            rows = [[r["name"], "★" if r["d66"] else ("宿" if r.get("lodging") else ""),
                     _num(bmap.get(r["name"], {}).get(
                "count_five_area")), _num(r["count_five_area"]),
                _delta(bmap.get(r["name"], {}).get("count_five_area"), r["count_five_area"]),
                _num(bmap.get(r["name"], {}).get("share_of_five_area"), 4),
                _num(r["share_of_five_area"], 4)] for r in ka["rows"]]
        else:
            head = ["種別", "D-66", "03時 5エリア", "全体比", f"{tgt:,}体換算", "bbox 全体"]
            rows = [[r["name"], "★" if r["d66"] else ("宿" if r.get("lodging") else ""),
                     _num(r["count_five_area"]),
                     _num(r["share_of_five_area"], 4), _num(r["count_five_area_scaled"]),
                     _num(r["count_bbox"])] for r in ka["rows"]]
        out += [c7lib.markdown_table(head, rows), "",
                f"★ = D-66 の直接指標(域外常住のはずの種別)・宿 = 宿泊施設で就寝する種別"
                f"(参考・判定外・第173)。★ 合計 "
                f"{_num(ka['d66_total']['count_five_area'])} 体 = 全体比 "
                f"{_num(ka['d66_total']['share_of_five_area'], 4)}"
                + (f"(before {_num(kb['d66_total']['count_five_area'])} 体・"
                   f"{_num(kb['d66_total']['share_of_five_area'], 4)})" if (cm and kb) else "")]
    out += ["", "## 4 起床率/時 と a(h) の差", ""]
    wa, wb = after.get("wake_rate"), (before or {}).get("wake_rate")
    if wa is None:
        out.append("(`--summary` が無い=`起床率/時` 行を読めていない)")
    else:
        out.append(_scalar_table([
            ("最大絶対差 abs(run − a(h))", (wb or {}).get("max_abs_diff"), wa["max_abs_diff"]),
            ("その時刻", (wb or {}).get("max_abs_hour"), wa["max_abs_hour"]),
            ("03 時 差(run − a(3))", (wb or {}).get("diff_03"), wa["diff_03"]),
            ("12 時 差(run − a(12))", (wb or {}).get("diff_12"), wa["diff_12"]),
        ], cm, nd=3))
        out += ["", f"- after の {wa['basis_note']}"]
        if wb is not None and wb.get("basis") != wa.get("basis"):
            out.append(f"- **before は定義が違う**: {wb['basis_note']}(差は定義差を含む)")
        out += [f"- a(h) 出典: {wa['anchor_source']}",
                f"- 注意: {wa['anchor_caveat']}"]
    out += ["", "## 5 計画就寝(D-62 の計数)", ""]
    sa, sb = after.get("planned_sleep"), (before or {}).get("planned_sleep")
    if not sa:
        out.append("(`--summary` が無い=`D-62 計画就寝` 行を読めていない)")
    else:
        out.append(_scalar_table([
            ("その場(職場等でその場就寝)", (sb or {}).get("slept"), sa.get("slept")),
            ("着いて(就寝地へ着いて就寝)", (sb or {}).get("arrived"), sa.get("arrived")),
            ("寝かせなかった 域外", (sb or {}).get("outside"), sa.get("outside")),
            ("寝かせなかった 就寝済", (sb or {}).get("asleep"), sa.get("asleep")),
        ], cm, nd=0))
        out.append("")
        out.append("※ 「その場」に域外居住者ぶんが何体含まれるかは要約からは分からない"
                   "(engine の計数が種別を分けていない)= そのまま載せる。")
    out += ["", "## 6 距離の要約(ラン ÷ 現実・1.0 が一致)", ""]
    da, db = after["distance"], (before or {}).get("distance", {})
    out.append(_scalar_table([
        ("09時 5エリア / 昼間人口 130,167", db.get("day_09_vs_core9_daytime"),
         da["day_09_vs_core9_daytime"]),
        ("09時 5エリア / PT ピーク 145,000", db.get("day_09_vs_pt_peak"), da["day_09_vs_pt_peak"]),
        ("03時 5エリア / 常住 8,810", db.get("night_03_vs_core9_night"),
         da["night_03_vs_core9_night"]),
        ("03時 5エリア / 推定上限 30,000", db.get("night_03_vs_estimate_high"),
         da["night_03_vs_estimate_high"]),
        ("03時 推定帯 1.5〜3 万からの隙間[人]", db.get("night_03_band_gap"),
         da["night_03_band_gap"]),
    ], cm, nd=4))
    if not da["scaled"]:
        out.append("")
        out.append("※ 個体数が分からず**縮尺していない**(生値をそのまま割った)。")
    if cm:
        out += ["", "## 7 前より良いか(現実側へ近づいたか)", "",
                c7lib.markdown_table(
                    ["指標", "before", "after", "差", "目標/帯", "距離 before", "距離 after",
                     "近づいた", "注"],
                    [[r["metric"], _num(r["before"], 3), _num(r["after"], 3),
                      _num(r["delta"], 3),
                      (_num(r["target"], 3) if r["target"] is not None
                       else (f"{r['band'][0]:,.0f}〜{r['band'][1]:,.0f}" if r["band"]
                             else ("小さいほど良い" if r["direction"] == "lower" else "—"))),
                      _num(r["gap_before"], 3), _num(r["gap_after"], 3),
                      ("—" if r["closer"] is None else ("yes" if r["closer"] else "no")),
                      r["note"] or ""]
                     for r in payload["comparison"]]),
                "",
                f"- 近づいた: {payload['comparison_counts']['closer']} / "
                f"判定できた {payload['comparison_counts']['judged']} 指標"
                f"(判定不能 {payload['comparison_counts']['unjudged']})",
                "- **これは合格判定ではない**。どの指標を重く見るか・どこで合格とするかは親が決める。"]
    return "\n".join(out)


# ---------------------------------------------------------------- 組み立て


def anchors_echo(anchors: Mapping[str, Any]) -> dict[str, Any]:
    """報告に載せる現実側の数値(出典つきで JSON に残す)。"""
    a = anchors["anchors"]
    return {
        "core9_daytime_population": a["core9_daytime_population"]["value"],
        "core9_night_population": a["core9_night_population"]["value"],
        "core9_day_night_ratio": a["core9_day_night_ratio"]["value"],
        "pt_area_daytime_peak": a["pt_area_daytime_peak"]["value"],
        "night_presence_low": a["night_presence_estimate"]["low"],
        "night_presence_high": a["night_presence_estimate"]["high"],
        "attendance_rate": a["attendance_rate"]["value"],
        "sources": {k: a[k]["source"] for k in a},
        "tags": {k: a[k]["tag"] for k in a},
    }


def build_payload(after: Presence, anchors: Mapping[str, Any], *, target: int,
                  before: Presence | None = None) -> dict[str, Any]:
    """1 ラン(または前後 2 ラン)→ 出力 JSON まるごと。**純関数**。"""
    ma = measures(after, anchors, target=target)
    payload: dict[str, Any] = {
        "schema": "shibuya.tools.c7/presence_yardstick/1",
        "anchors_path": anchors.get("_path", str(DEFAULT_ANCHORS_PATH)),
        "anchors_version": anchors.get("version", "?"),
        "anchors_echo": anchors_echo(anchors),
        "no_pass_line": "合格線は持たない=距離と『近づいたか』の bool のみ(判定は親)。",
        "after": ma,
    }
    if before is not None:
        mb = measures(before, anchors, target=target)
        rows = compare(ma, mb, anchors)
        judged = [r for r in rows if r["closer"] is not None]
        payload["before"] = mb
        payload["comparison"] = rows
        payload["comparison_counts"] = {
            "judged": len(judged),
            "closer": sum(1 for r in judged if r["closer"]),
            "unjudged": len(rows) - len(judged),
        }
    return payload


def _area_map(args: argparse.Namespace) -> c7lib.AreaMap:
    """写像表(``--area-map`` があれば読む・無ければ ``--world`` から作る)。"""
    if args.area_map:
        return c7lib.AreaMap.from_json(
            json.loads(Path(args.area_map).read_text(encoding="utf-8")))
    amap, _gate = occ.build_map(args.world, args.axes)
    return amap


def _presence(journal: str | None, series: str | None, summary_path: str | None,
              label: str | None, n_agents: int | None, args: argparse.Namespace,
              amap_cache: dict[str, c7lib.AreaMap]) -> Presence:
    sm = read_summary(summary_path)
    if journal:
        if "amap" not in amap_cache:
            amap_cache["amap"] = _area_map(args)
        return presence_from_journal(journal, amap_cache["amap"],
                                     label=label or Path(journal).stem, summary=sm,
                                     n_agents=n_agents)
    if series:
        return presence_from_series(series, label=label or Path(series).stem, summary=sm,
                                    n_agents=n_agents)
    raise SystemExit("--journal か --series のどちらかが要る")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="C7: ランの在圏を現実アンカーと同じ物差しで測る(前後比較つき)")
    ap.add_argument("--journal", default=None, help="在圏 journal(.npz)")
    ap.add_argument("--series", default=None, help="集計済み在圏 JSON(area_hour_counts)")
    ap.add_argument("--summary", default=None, help="ラン要約テキスト(cli の標準出力)")
    ap.add_argument("--label", default=None, help="after 側の名前(既定=ファイル名)")
    ap.add_argument("--n-agents", type=int, default=None, help="after の個体数(縮尺の分母)")
    ap.add_argument("--before", default=None, help="比較元の journal(.npz)")
    ap.add_argument("--before-series", default=None, help="比較元の集計済み JSON")
    ap.add_argument("--before-summary", default=None, help="比較元の要約テキスト")
    ap.add_argument("--before-label", default=None, help="before 側の名前")
    ap.add_argument("--before-n-agents", type=int, default=None, help="before の個体数")
    ap.add_argument("--anchors", default=None,
                    help=f"アンカー台帳(既定 {DEFAULT_ANCHORS_PATH})")
    ap.add_argument("--target-population", type=int, default=None,
                    help="縮尺の分子(既定=台帳の full_population)")
    ap.add_argument("--world", default="data/world/v2", help="世界資産(写像表を作るとき)")
    ap.add_argument("--axes", default=None, help="境界定義 JSON(既定 tools/c7/area_axes_v0.json)")
    ap.add_argument("--area-map", default=None, help="既存の写像表 JSON")
    ap.add_argument("--out", default=None, help="出力ディレクトリ(既定=標準出力のみ)")
    args = ap.parse_args(argv)

    anchors = load_anchors(args.anchors)
    target = int(args.target_population or anchors["anchors"]["full_population"]["value"])
    cache: dict[str, c7lib.AreaMap] = {}
    after = _presence(args.journal, args.series, args.summary, args.label, args.n_agents,
                      args, cache)
    before = None
    if args.before or args.before_series:
        before = _presence(args.before, args.before_series, args.before_summary,
                           args.before_label or "before", args.before_n_agents, args, cache)
    payload = build_payload(after, anchors, target=target, before=before)
    md = markdown(payload)
    if args.out:
        paths = c7lib.write_outputs(args.out, "presence_yardstick", payload, md)
        print(json.dumps(paths, ensure_ascii=False))
    print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
