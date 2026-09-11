# -*- coding: utf-8 -*-
"""diversity_yardstick.py — **個体の行動多様性の物差し**(D-68 下見 P0/P0b/P1a/P1b/P2)。

なぜ要るか
    「個体が同質すぎる」(D-68)の修正は「前より現実側へ寄ったか」で受け入れる。ところが
    腕を回すたびに数え方を決め直すと**比較にならない**。本ツールは W17 の凍結資産(parquet)
    と下見の応答 jsonl を**同じ入口・同じ数え方・同じアンカー**で測る。設計 =
    ``docs/design/v2-d68-pilot-design.md`` §5(M1〜M8)。流儀は ``tools/c7/presence_yardstick.py``
    と同じ(純関数+CLI・アンカー JSON・before/after・**合格線は書かない**=判定は親)。

パターン台帳ゲート(CLAUDE.md §4)
    「1 日の軌跡は何種類の形になるか(Schneider 17 モチーフ)」「出勤時刻は人口をまたいで
    どれだけ散るか(社会生活基本調査 第30/31表)」「同じ人の 2 日はどれだけ似るか
    (Alessandretti/Schlich)」という**現実パターン**との照合に使う。

数え方は既存物を再利用する(二重実装しない)
    parquet の読みは ``shibuya.agents.weekly.load_weekly``、語彙は同モジュールの
    ``ACTIVITY_WORDS``/``PLACE_WORDS``、応答 jsonl の行パースは
    ``shibuya.build.sched.vocab``(W17 の段2 が使うのと同じ ``parse_line``/``canonical_text``)。
    **``repair_day``/``repair``/``rake`` は呼ばない**——修復前の LLM 出力を測るため。
    表と JSON の書き出しは ``tools/c6/c6lib``。

現実側の数値はここに書かない
    全て ``docs/bench/anchors/diversity_anchors_v0.json``(source/tag/verified_by 付き)。
    同ファイルの ``p0_prior`` は**現実アンカーではない**=設計書 §5 の前値で、
    物差し自身の再現性検査にだけ使う。

入口
    ``--parquet PATH``     W17 週次表(既定 ``<world>/w17_schedule.parquet``)。P0 の前値。
    ``--responses PATH…``  下見の応答 jsonl(``w17_trial_<arm>_responses.jsonl``)。
                           現行形式(``d0`` 見出し+``0700-0830 移動 職場``)と
                           **ブロック形式**(``0700-0830 2 勤務 職場``・計画実行層設計書 §9)の両対応。
    ``--world PATH``       W16 母集団(種別 kind と層化重み w_k の出所)。

例::

    python tools/w17/diversity_yardstick.py --parquet data/world/v2/w17_schedule.parquet \\
        --world data/world/v2 --label P0 --out out/div_p0
    python tools/w17/diversity_yardstick.py --responses out/w17_trial_p1a_responses.jsonl \\
        --world data/world/v2 --label P1a --before-parquet data/world/v2/w17_schedule.parquet \\
        --before-label P0 --floor out/w17_trial_p0b_a.jsonl out/w17_trial_p0b_b.jsonl --out out/div_p1a

逐次ループ宣言(P4)
    体比例のループは **(a) 応答 jsonl の行読み**(下見 2,000 体規模)と
    **(b) M2 の体ごとの署名ダイジェスト**(``hashlib`` 呼が体数ぶん)の 2 本だけ。
    M1/M4/M6/M8 は ``np.unique``/``bincount``/``maximum.accumulate`` のベクトル演算で、
    390,067 体でも Python ループを持たない。
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

_HERE = Path(os.path.abspath(__file__)).parent
REPO_ROOT = _HERE.parent.parent
for _p in (str(REPO_ROOT / "src"), str(REPO_ROOT / "tools" / "c6")):
    if _p not in sys.path:  # pragma: no cover - 実行時の経路
        sys.path.insert(0, _p)

import c6lib  # noqa: E402

from shibuya.agents.population import load_population  # noqa: E402
from shibuya.agents.weekly import (  # noqa: E402
    ACTIVITY_WORDS,
    CELL_UNRESOLVED,
    MINUTES_PER_DAY,
    N_DAYS,
    PLACE_WORDS,
    WEEKLY_FILE,
    load_weekly,
    load_weekly_file,
)
from shibuya.build.sched import vocab as V  # noqa: E402

markdown_table = c6lib.markdown_table
write_outputs = c6lib.write_outputs

#: 既定のアンカー台帳(現実側の数値は**全てここ**にある)。
DEFAULT_ANCHORS_PATH = REPO_ROOT / "docs" / "bench" / "anchors" / "diversity_anchors_v0.json"

#: ``AgentKind``(src/shibuya/agents/state.py)の順と名前。
KIND_JA: tuple[str, ...] = (
    "通勤", "来街", "従業", "住民", "指令", "通学", "定期来街", "訪日", "乗務",
)
N_KINDS = len(KIND_JA)

# 活動語のコード(**二重定義しない**= ``agents.weekly.ACTIVITY_WORDS`` から引く)。
ACT_SLEEP = ACTIVITY_WORDS.index("就寝")
ACT_PREP = ACTIVITY_WORDS.index("支度")
ACT_MOVE = ACTIVITY_WORDS.index("移動")
ACT_RIDE = ACTIVITY_WORDS.index("乗車")
ACT_WORK = ACTIVITY_WORDS.index("勤務")
PLACE_HOME = PLACE_WORDS.index("自宅")
PLACE_LODGING = PLACE_WORDS.index("宿泊施設")
PLACE_OUTSIDE = PLACE_WORDS.index("域外")

#: ``block_kind``(計画実行層設計書 §9)= 0 域外 / 1 自宅 / 2 在圏 / 3 就寝 / 4 移動。
#: 応答 jsonl と、下見が書く ``w17_trial_<arm>_schedule.parquet`` の追加列に出る。
BLOCK_WORDS: tuple[str, ...] = ("域外", "自宅", "在圏", "就寝", "移動")

#: 開始時刻のビン幅[分](15 分=第30表の刻みに合わせる。96 ビン/日)。
TIME_BIN_MIN = 15
N_TIME_BINS = MINUTES_PER_DAY // TIME_BIN_MIN

#: 深夜違反の窓(D-63 (iii)「0〜4 時に 支度/乗車 を置かない」)。
NIGHT_START, NIGHT_END = 0, 4 * 60

#: 平日(day<5)と全 7 日。**設計書 §5 の前値は全 7 日で測られている**ので両方出す。
SCOPES: dict[str, tuple[int, ...]] = {
    "weekday": (0, 1, 2, 3, 4),
    "all_days": tuple(range(N_DAYS)),
}

#: M1 の正準化(グラフ同型の判定)を総当たりで行う節点数の上限。これを超える日は
#: 「出現順ラベル」のまま数え、``capped_share`` に計上する(近似であることを明示)。
MOTIF_PERM_CAP = 7


# ================================================================= アンカー台帳

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
        if not any(k in a for k in ("value", "values", "low")):
            raise ValueError(f"アンカー {key} に値(value/values/low)が無い")


def load_anchors(path: str | Path | None = None) -> dict[str, Any]:
    """アンカー台帳を読む。**必須欄が欠けていたら落とす**(推測で埋めない)。"""
    p = Path(path) if path else DEFAULT_ANCHORS_PATH
    doc = json.loads(p.read_text(encoding="utf-8"))
    check_anchors(doc)
    doc["_path"] = str(p)
    return doc


def unverified_anchors(doc: Mapping[str, Any]) -> list[str]:
    """``verified_by`` が「未確認」で始まるアンカーの名前(報告に印を出すため)。"""
    return sorted(k for k, a in doc["anchors"].items()
                  if str(a.get("verified_by", "")).startswith("未確認"))


# ================================================================= 入力の器

@dataclass(frozen=True)
class Sample:
    """1 標本(1 腕の 1 ラン)。行は ``(体行, 曜日, 並び)`` 昇順。

    Attributes:
        agent_id: 体の ``agent_id``(昇順・重複なし)。索引=**体行**。
        kind: 体ごとの種別(``-1``=母集団に無い)。
        row_agent/row_day: 行ごとの体行・曜日。
        block_kind: ブロック形式の列(``None``=現行形式)。
        ingest: 応答 jsonl の生の計数(``None``=parquet 入力)。
    """

    label: str
    source: str
    input_kind: str
    agent_id: np.ndarray
    kind: np.ndarray
    row_agent: np.ndarray
    row_day: np.ndarray
    start: np.ndarray
    end: np.ndarray
    activity: np.ndarray
    place_kind: np.ndarray
    target_cell: np.ndarray
    block_kind: np.ndarray | None = None
    arm: str | None = None
    ingest: dict[str, Any] | None = None

    @property
    def n_agents(self) -> int:
        return int(self.agent_id.size)

    @property
    def n_rows(self) -> int:
        return int(self.start.size)


_POP_CACHE: dict[str, Any] = {}


def _population(world_dir: str | Path | None):
    """W16 母集団(同じ世界を 2 度読まない)。資産が無ければ ``None``。"""
    if world_dir is None:
        return None
    key = str(Path(world_dir))
    if key not in _POP_CACHE:
        _POP_CACHE[key] = load_population(world_dir)
    return _POP_CACHE[key]


def _kind_of(agent_id: np.ndarray, world_dir: str | Path | None) -> np.ndarray:
    """``agent_id`` → 種別(W16 母集団から引く)。資産が無ければ全て ``-1``。"""
    out = np.full(agent_id.size, -1, dtype=np.int8)
    pop = _population(world_dir)
    if pop is None:
        return out
    src = np.asarray(pop.source_agent_id)
    pos = np.searchsorted(src, agent_id)
    ok = pos < src.size
    idx = np.where(ok, pos, 0)
    ok &= src[idx] == agent_id
    out[ok] = np.asarray(pop.kind)[idx[ok]]
    return out


def population_kind_counts(world_dir: str | Path | None) -> np.ndarray | None:
    """W16 母集団の種別ごとの体数(層化重み ``w_k`` の分子)。資産が無ければ ``None``。"""
    pop = _population(world_dir)
    if pop is None:
        return None
    return np.bincount(np.asarray(pop.kind).astype(np.int64), minlength=N_KINDS)[:N_KINDS]


def read_weekly_any(target: str | Path):
    """``--parquet`` の引数 → ``(WeeklySchedule, 読んだファイル)``。**純関数**。

    **ファイルパスでもディレクトリでも読む**。下見の出力は本番 glob
    (``w17_responses*.jsonl``/``w17_schedule.parquet``)に当たらない名前
    ``data/world/v2/trials/<arm>/w17_trial_<arm>_schedule.parquet`` に置くので、
    ``load_weekly``(ディレクトリ+固定ファイル名)だけでは読めない。
    """
    p = Path(target)
    if p.is_dir():
        ws = load_weekly(p)
        if ws is None:
            raise SystemExit(f"{p / WEEKLY_FILE} が無い")
        return ws, p / WEEKLY_FILE
    if p.suffix != ".parquet":
        raise SystemExit(f"--parquet は .parquet ファイルか世界資産ディレクトリ: {p}")
    if not p.exists():
        raise SystemExit(f"{p} が無い")
    return load_weekly_file(p), p


def read_extra_columns(path: str | Path) -> tuple[np.ndarray | None, str | None]:
    """``block_kind``/``arm`` 列があれば読む(無ければ ``None``)。行順は ``_COLUMNS`` と同じ。

    **M1〜M8 の場所判定には使わない**(場所は今までどおり ``place_kind``/``target_cell``)。
    ``block_kind`` は弊害側の「block_kind と場所語の矛盾」の計数にだけ使う。
    """
    import pyarrow.parquet as pq

    names = set(pq.read_schema(path).names)
    block = None
    if "block_kind" in names:
        col = pq.read_table(path, columns=["block_kind"]).column("block_kind")
        block = np.asarray(col.to_numpy(zero_copy_only=False)).astype(np.int64)
    arm = None
    if "arm" in names:
        vals = pq.read_table(path, columns=["arm"]).column("arm").to_pylist()
        arm = str(vals[0]) if vals else None
    return block, arm


def sample_from_weekly(world_dir: str | Path | None, *, parquet: str | Path | None = None,
                       label: str | None = None, limit_agents: int | None = None) -> Sample:
    """W17 週次表 parquet → ``Sample``。``load_weekly`` の CSR を行ごとの形に展開する。

    ``parquet`` は**ファイルでもディレクトリでもよい**(省略時は ``world_dir``)。
    ``world_dir`` は種別 kind と層化重み w_k の出所で、資産の在り処とは独立。
    """
    ws, src_path = read_weekly_any(parquet if parquet else world_dir)
    block, arm = read_extra_columns(src_path)
    n = ws.n_agents
    counts = np.diff(ws.day_offset)
    cellidx = np.repeat(np.arange(n * N_DAYS, dtype=np.int64), counts)
    row_agent = cellidx // N_DAYS
    row_day = (cellidx % N_DAYS).astype(np.int64)
    s = Sample(
        label=label or "weekly",
        source=str(src_path),
        input_kind="parquet",
        block_kind=block,
        arm=arm,
        agent_id=np.asarray(ws.agent_id, dtype=np.int64),
        kind=_kind_of(np.asarray(ws.agent_id, dtype=np.int64), world_dir),
        row_agent=row_agent,
        row_day=row_day,
        start=ws.start_min.astype(np.int64),
        end=ws.end_min.astype(np.int64),
        activity=ws.activity.astype(np.int64),
        place_kind=ws.place_kind.astype(np.int64),
        target_cell=ws.target_cell.astype(np.int64),
    )
    return restrict_agents(s, limit_agents) if limit_agents else s


def restrict_agents(s: Sample, limit: int) -> Sample:
    """先頭 ``limit`` 体だけに絞る(小さく回すため・**決定論**=agent_id 昇順の先頭)。"""
    if limit >= s.n_agents:
        return s
    keep = s.row_agent < limit
    return Sample(
        label=s.label, source=s.source, input_kind=s.input_kind,
        agent_id=s.agent_id[:limit], kind=s.kind[:limit],
        row_agent=s.row_agent[keep], row_day=s.row_day[keep],
        start=s.start[keep], end=s.end[keep], activity=s.activity[keep],
        place_kind=s.place_kind[keep], target_cell=s.target_cell[keep],
        block_kind=None if s.block_kind is None else s.block_kind[keep],
        arm=s.arm, ingest=s.ingest,
    )


# ---------------------------------------------------------------- 応答 jsonl の読み

_ID_RE = re.compile(r'"id"\s*:\s*"([^"]{1,32})"')
_DAY_HEADER_RE = re.compile(r"^d([0-6])$")
#: ブロック形式の行(``0700-0830 2 勤務 職場``)の中央の 1 桁= ``block_kind``
#: (0 域外/1 自宅/2 在圏/3 就寝/4 移動・計画実行層設計書 §9)。
BLOCK_KINDS: tuple[str, ...] = ("域外", "自宅", "在圏", "就寝", "移動")


def parse_response_text(raw: str) -> tuple[list[V.Act], list[int], dict[str, int], int]:
    """応答本文 → ``(活動列, block_kind 列, 理由の計数, 検査した行数)``。**純関数**。

    ``vocab.canonical_text``/``vocab.parse_line`` を**そのまま**使う(同義語表・日またぎの
    分割・失敗理由の語彙を二重定義しない)。ブロック形式は「時刻欄の次の 1 桁」を外してから
    同じ ``parse_line`` に渡す=**現行形式と 1 本のパーサで読む**。

    ``repair_day`` は呼ばない=**修復前の生の並び**を測る(設計書 §5 の規約)。

    Returns:
        ``block_kind`` は活動 1 件ごとに ``-1``(現行形式)か 0-4(ブロック形式)。
    """
    acts: list[V.Act] = []
    blocks: list[int] = []
    bad: dict[str, int] = {}
    considered = 0
    day: int | None = None
    for ln in V.canonical_text(raw).split("\n"):
        if not ln:
            continue
        head = _DAY_HEADER_RE.match(ln)
        if head is not None:
            day = int(head.group(1))
            continue
        considered += 1
        bk = -1
        parts = ln.split(" ")
        if len(parts) >= 4 and len(parts[1]) == 1 and parts[1].isdigit() \
                and 0 <= int(parts[1]) < len(BLOCK_KINDS):
            bk = int(parts[1])
            ln = parts[0] + " " + " ".join(parts[2:])
        got, why, notes = V.parse_line(ln, day)
        if why:
            bad[why] = bad.get(why, 0) + 1
            continue
        for note in notes:
            bad[note] = bad.get(note, 0) + 1
        acts.extend(got)
        blocks.extend([bk] * len(got))
        if len(acts) >= V.MAX_ACTS_PER_RESPONSE:
            bad["truncated"] = bad.get("truncated", 0) + 1
            break
    return acts, blocks, bad, considered


def read_responses(paths: Sequence[str | Path]) -> dict[str, str]:
    """応答 jsonl → ``{id: text}``。**同じ id が二度書かれたら最後の行を採る**
    (fleet_gen は追記型・W14/W15/W17 と同じ規約)。"""
    out: dict[str, str] = {}
    for p in paths:
        with open(p, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                m = _ID_RE.search(line[:200])
                if m is None:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                out[m.group(1)] = str(d.get("text", "") or "")
    return out


def sample_from_responses(paths: Sequence[str | Path], world_dir: str | Path | None, *,
                          label: str | None = None) -> Sample:
    """下見の応答 jsonl → ``Sample``(**修復なし**)。"""
    texts = read_responses(paths)
    ids = sorted(int(k) for k in texts if k.lstrip("-").isdigit())
    agent_id = np.asarray(ids, dtype=np.int64)
    row_a: list[int] = []
    row_d: list[int] = []
    st: list[int] = []
    en: list[int] = []
    ac: list[int] = []
    pl: list[int] = []
    bk: list[int] = []
    bad_total: dict[str, int] = {}
    considered_total = 0
    n_empty = 0
    n_block_rows = 0
    for row, aid in enumerate(ids):  # P4: 体比例ループ(下見 2,000 体規模)
        acts, blocks, bad, considered = parse_response_text(texts[str(aid)])
        considered_total += considered
        for k, v in bad.items():
            bad_total[k] = bad_total.get(k, 0) + v
        if not acts:
            n_empty += 1
        for a, b in zip(acts, blocks):
            row_a.append(row)
            row_d.append(int(a.day))
            st.append(int(a.start))
            en.append(int(a.end))
            ac.append(int(a.activity))
            pl.append(int(a.place))
            bk.append(int(b))
            if b >= 0:
                n_block_rows += 1
    arr = lambda x: np.asarray(x, dtype=np.int64)  # noqa: E731
    row_agent, row_day = arr(row_a), arr(row_d)
    order = np.lexsort((np.arange(row_agent.size), row_day, row_agent))
    ingest = {
        "n_response_rows": len(texts),
        "n_agents_with_text": len(ids),
        "n_agents_no_acts": n_empty,
        "n_lines_considered": considered_total,
        "n_parsed_acts": int(row_agent.size),
        "n_block_rows": n_block_rows,
        "format": ("block" if n_block_rows > row_agent.size / 2 else "flat"),
        "bad": bad_total,
        "parse_fail_lines": int(sum(v for k, v in bad_total.items() if k in V.FAILURE_REASONS)),
        "parse_fail_rate": (float(sum(v for k, v in bad_total.items() if k in V.FAILURE_REASONS))
                            / considered_total) if considered_total else None,
        "files": [str(p) for p in paths],
    }
    return Sample(
        label=label or Path(paths[0]).stem,
        source=";".join(str(p) for p in paths),
        input_kind="responses",
        agent_id=agent_id,
        kind=_kind_of(agent_id, world_dir),
        row_agent=row_agent[order], row_day=row_day[order],
        start=arr(st)[order], end=arr(en)[order], activity=arr(ac)[order],
        place_kind=arr(pl)[order],
        target_cell=np.full(row_agent.size, CELL_UNRESOLVED, dtype=np.int64),
        block_kind=arr(bk)[order],
        ingest=ingest,
    )


# ================================================================= 純関数(数え方)

def _dense(codes: np.ndarray) -> tuple[np.ndarray, int]:
    """任意の整数コード列 → 0 起点の密な索引と種類数。"""
    u, inv = np.unique(codes, return_inverse=True)
    return np.asarray(inv, dtype=np.int64).ravel(), int(u.size)


def _popcount(x: np.ndarray) -> np.ndarray:
    """立っているビット数(numpy 2.0 の ``bitwise_count`` が無い環境では表引き)。"""
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(x)
    lut = np.array([bin(i).count("1") for i in range(256)], dtype=np.int64)
    v = np.asarray(x, dtype=np.int64)
    out = np.zeros(v.shape, dtype=np.int64)
    for _ in range(8):
        out += lut[(v & 0xFF).astype(np.int64)]
        v = v >> 8
    return out


def _or_by_group(group: np.ndarray, bit_source: np.ndarray, n_groups: int,
                 n_bits: int) -> np.ndarray:
    """群ごとの**ビット和集合**。``(群, ビット位置)`` を一意化してから足す=OR と同値。

    ``np.bitwise_or.at`` は 1,000 万行で数秒かかるので使わない(P4 の逐次ループも作らない)。
    """
    out = np.zeros(n_groups, dtype=np.int64)
    if group.size == 0:
        return out
    u = np.unique(group * n_bits + bit_source)
    return np.bincount((u // n_bits).astype(np.int64),
                       weights=(1 << (u % n_bits)).astype(np.float64),
                       minlength=n_groups).astype(np.int64)


def time_stats(starts: np.ndarray) -> dict[str, Any]:
    """開始分の並び → ``:00+:30`` 率・15 分ビンの最頻と占有率・エントロピー。**純関数**。

    エントロピーは **1 日 96 ビン**(15 分刻み)で取る。第30表は 58 区分(4:45-19:00)なので
    上限が違う(96 ビン=6.585 bit / 58 区分=5.858 bit)。**同じ物差しで前後を比べるための値**で
    あって、アンカーとの差はこの上限差ぶんだけ甘い——報告にその旨を書く。
    """
    s = np.asarray(starts, dtype=np.int64).ravel()
    if s.size == 0:
        return {"n": 0, "on_00_30": None, "entropy_bits": None,
                "top_bin": None, "top_bin_share": None, "top_hour": None, "top_hour_share": None}
    mins = s % 60
    b = np.bincount(np.clip(s // TIME_BIN_MIN, 0, N_TIME_BINS - 1), minlength=N_TIME_BINS)
    p = b[b > 0] / b.sum()
    hb = np.bincount(np.clip(s // 60, 0, 23), minlength=24)
    top = int(b.argmax())
    toph = int(hb.argmax())
    return {
        "n": int(s.size),
        "on_00_30": float(np.mean((mins == 0) | (mins == 30))),
        "entropy_bits": float(-(p * np.log2(p)).sum()),
        "entropy_max_bits": float(np.log2(N_TIME_BINS)),
        "top_bin": f"{top * TIME_BIN_MIN // 60:02d}:{top * TIME_BIN_MIN % 60:02d}",
        "top_bin_share": float(b.max() / b.sum()),
        "top_hour": f"{toph:02d}時台",
        "top_hour_share": float(hb.max() / hb.sum()),
    }


def mean_sd(values: np.ndarray) -> dict[str, Any]:
    """平均・標準偏差(母標準偏差 ddof=0)・件数。**純関数**。"""
    v = np.asarray(values, dtype=np.float64).ravel()
    if v.size == 0:
        return {"n": 0, "mean": None, "sd": None}
    return {"n": int(v.size), "mean": float(v.mean()), "sd": float(v.std(ddof=0))}


def canonical_motif(edges: Sequence[tuple[int, int]], n_nodes: int) -> tuple[str, bool]:
    """有向グラフ(節点ラベルなし)の**正準形**と「総当たりできたか」。**純関数**。

    Schneider 2013 のモチーフ= 重みなし・向きだけの有向ネットワークの**同型類**。節点は
    「どの地点か」を区別しないので、出現順ラベルのままでは同じ形が別物に見える。節点数が
    ``MOTIF_PERM_CAP`` 以下なら全順列を試して辞書順最小の辺集合を正準形にする。
    """
    es = sorted(set((int(a), int(b)) for a, b in edges))
    if n_nodes > MOTIF_PERM_CAP:
        return f"N{n_nodes}*:" + ",".join(f"{a}>{b}" for a, b in es), False
    best: tuple[tuple[int, int], ...] | None = None
    for perm in itertools.permutations(range(n_nodes)):
        t = tuple(sorted((perm[a], perm[b]) for a, b in es))
        if best is None or t < best:
            best = t
    assert best is not None
    return f"N{n_nodes}:" + ",".join(f"{a}>{b}" for a, b in best), True


def motif_table(labels: Sequence[str], motif_of_day: np.ndarray, *, threshold: float,
                closed: np.ndarray | None = None, capped: np.ndarray | None = None,
                top: int = 12) -> dict[str, Any]:
    """モチーフ索引の並び → 出現率 ``threshold`` 以上の形の個数と累積被覆。**純関数**。"""
    m = np.asarray(motif_of_day, dtype=np.int64).ravel()
    if m.size == 0:
        return {"n_day_graphs": 0, "n_distinct": 0, "n_motifs_ge_threshold": 0,
                "threshold": threshold, "coverage_ge_threshold": None, "top": []}
    c = np.bincount(m, minlength=len(labels)).astype(np.float64)
    share = c / c.sum()
    hit = share >= threshold
    order = np.argsort(-c)
    return {
        "n_day_graphs": int(m.size),
        "n_distinct": int((c > 0).sum()),
        "n_motifs_ge_threshold": int(hit.sum()),
        "threshold": float(threshold),
        "coverage_ge_threshold": float(share[hit].sum()),
        "closed_share": None if closed is None else float(np.mean(closed)),
        "capped_share": None if capped is None else float(np.mean(capped)),
        "top": [{"motif": labels[int(i)], "n": int(c[int(i)]), "share": float(share[int(i)])}
                for i in order[:top] if c[int(i)] > 0],
    }


def signature_stats(digests: np.ndarray) -> dict[str, Any]:
    """体ごとの署名ダイジェスト → 種類数・種類率・上位 1 型の占有率。**純関数**。"""
    d = np.asarray(digests).ravel()
    if d.size == 0:
        return {"n_agents": 0, "n_types": 0, "type_rate": None, "top1_share": None}
    u, c = np.unique(d, return_counts=True)
    return {"n_agents": int(d.size), "n_types": int(u.size),
            "type_rate": float(u.size / d.size), "top1_share": float(c.max() / d.size)}


def group_digests(values: np.ndarray, offsets: np.ndarray) -> np.ndarray:
    """CSR 区切りごとの 8 バイトダイジェスト(空区間も一意に区別する)。**純関数**。

    P4 逐次ループ宣言: 区間数ぶん(=体数)の ``hashlib`` 呼。
    """
    v = np.ascontiguousarray(values)
    buf = v.tobytes()
    isz = v.dtype.itemsize
    out = np.empty(offsets.size - 1, dtype=np.uint64)
    for i in range(out.size):
        lo, hi = int(offsets[i]) * isz, int(offsets[i + 1]) * isz
        out[i] = int.from_bytes(hashlib.blake2b(buf[lo:hi], digest_size=8).digest(), "little")
    return out


def block_consistency(block: np.ndarray | None, place: np.ndarray) -> dict[str, Any]:
    """``block_kind`` と場所語の矛盾を数える(計画実行層設計書 §9 の検査項目)。**純関数**。

    **expedient(自前の規則)**: 設計書は「``block_kind`` と場所語の矛盾」を検査に挙げるだけで
    対応表を持たない。ここでは**必ず言える 4 つだけ**を矛盾として数え、それ以外は判定しない:

    ===== ============================================================
    0 域外 場所語が「域外」でない
    1 自宅 場所語が「自宅」でない
    2 在圏 場所語が「域外」である(在圏なのに域外)
    3 就寝 場所語が「自宅/宿泊施設/域外」のいずれでもない
    4 移動 **判定しない**。W17 の「移動」行は**行き先**の場所語を持つので、
           駅・路上に限れない(限ると全行が矛盾になる)
    ===== ============================================================

    ``block_kind`` が無い(現行形式)なら ``present=False`` だけを返す。
    """
    if block is None or block.size == 0:
        return {"present": False, "n": 0,
                "note": "block_kind 列が無い(現行形式)=この検査は出せない"}
    b = np.asarray(block, dtype=np.int64).ravel()
    pl = np.asarray(place, dtype=np.int64).ravel()
    known = (b >= 0) & (b < len(BLOCK_WORDS))
    bad_outside = known & (b == 0) & (pl != PLACE_OUTSIDE)
    bad_home = known & (b == 1) & (pl != PLACE_HOME)
    bad_in_area = known & (b == 2) & (pl == PLACE_OUTSIDE)
    bad_sleep = known & (b == 3) & ~np.isin(pl, (PLACE_HOME, PLACE_LODGING, PLACE_OUTSIDE))
    judged = known & (b != 4)
    bad = bad_outside | bad_home | bad_in_area | bad_sleep
    return {
        "present": True,
        "n": int(judged.sum()),
        "rule": "expedient(自前・移動 4 は判定しない)",
        "n_rows": int(b.size),
        "n_unknown_code": int((~known).sum()),
        "n_move_unjudged": int((known & (b == 4)).sum()),
        "mismatch_rows": int(bad.sum()),
        "mismatch_share": (float(bad.sum() / judged.sum()) if judged.any() else None),
        "by_rule": {
            "0 域外なのに場所語が域外でない": int(bad_outside.sum()),
            "1 自宅なのに場所語が自宅でない": int(bad_home.sum()),
            "2 在圏なのに場所語が域外": int(bad_in_area.sum()),
            "3 就寝なのに場所語が自宅/宿泊施設/域外でない": int(bad_sleep.sum()),
        },
        "counts_by_block": {BLOCK_WORDS[i]: int((b == i).sum()) for i in range(len(BLOCK_WORDS))},
    }


def covered_minutes(gid: np.ndarray, start: np.ndarray, end: np.ndarray,
                    n_groups: int) -> np.ndarray:
    """(体・日)ごとに**重なりを除いた**被覆分。**純関数**・ループなし。

    区間は ``(体行, 曜日, 並び)`` 昇順=開始分の昇順なので、「その日の直前までの最大終了分」
    を群内累積最大で出し、``max(0, end − max(start, 直前までの最大終了))`` を足せばよい。
    群内累積最大は「群番号 × 2048 を足してから全体で累積最大を取る」で作る
    (終了分は 0-1440 < 2048 なので群の境界が必ず勝つ)。
    """
    out = np.zeros(n_groups, dtype=np.float64)
    if start.size == 0:
        return out
    off = gid * 2048
    cm = np.maximum.accumulate(end + off) - off
    prev = np.empty_like(cm)
    prev[0] = -1
    prev[1:] = cm[:-1]
    first = np.empty(gid.size, dtype=bool)
    first[0] = True
    first[1:] = gid[1:] != gid[:-1]
    prev[first] = -1
    add = np.maximum(0, end - np.maximum(start, prev))
    return np.bincount(gid, weights=add.astype(np.float64), minlength=n_groups)


# ================================================================= 曜日スコープの下ごしらえ

@dataclass
class ScopeCache:
    """1 つの曜日スコープ(平日 / 全 7 日)について、**種別に依らない**中間結果を 1 度だけ作る。

    種別ごとの表は、ここに入っている (体・日) 単位・体単位・日対単位の配列を
    ``bincount``/マスクで畳むだけで出る(同じ計算を 10 回しない)。
    """

    days: tuple[int, ...]
    n_agents: int
    day_agent: np.ndarray          # (G,) 体行
    day_index: np.ndarray          # (G,) 曜日
    day_count: np.ndarray          # (G,) 行数
    day_distinct_place: np.ndarray  # (G,) 相異なる (場所種別, cell)
    day_distinct_kind: np.ndarray  # (G,) 相異なる 場所種別
    day_coverage: np.ndarray       # (G,) 被覆率(0-1)
    day_has_sleep: np.ndarray      # (G,) 就寝行あり
    day_night_bad: np.ndarray      # (G,) 深夜(0-4 時)の 支度/乗車 の件数
    motif_labels: list[str]
    motif_of_day: np.ndarray       # (G,) モチーフ索引
    motif_closed: np.ndarray       # (G,) 始点=終点
    motif_capped: np.ndarray       # (G,) 正準化を諦めた
    work_start: np.ndarray         # (G,) 最初の勤務の開始分(-1=勤務なし)
    work_rows_start: np.ndarray    # 勤務行の開始分(全行)
    work_rows_agent: np.ndarray    # 同 体行
    commute_proxy: np.ndarray      # (G,) 出勤代理(-1=取れない)
    row_agent: np.ndarray          # スコープ内の行の体行
    row_start: np.ndarray
    row_place: np.ndarray          # スコープ内の行の場所種別
    row_block: np.ndarray | None   # 同 block_kind(None=現行形式)
    pairs: list[tuple[int, int]]
    pair_inter: np.ndarray         # (P, n_agents)
    pair_union: np.ndarray         # (P, n_agents)
    pair_both: np.ndarray          # (P, n_agents) 両日とも活動がある(=J が定義できる)
    agent_place_mask: np.ndarray   # (n_agents,) 場所種別の 12 bit 集合
    agent_capacity_cell: np.ndarray  # (n_agents,) 相異なる (場所種別, cell)
    sig: dict[str, np.ndarray]     # 署名ダイジェスト(体ごと)


def _appearance_nodes(day_gid: np.ndarray, code: np.ndarray,
                      n_codes: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(体・日)ごとに「その地点が何番目に初めて出たか」= 節点 id。

    Returns:
        ``(行ごとの節点 id, 一意化した (日,地点) キー, そのキーの日)``。
    """
    pairkey = day_gid * n_codes + code
    u2, first_idx = np.unique(pairkey, return_index=True)
    day_of_u2 = u2 // n_codes
    order = np.lexsort((first_idx, day_of_u2))
    days_sorted = day_of_u2[order]
    gstart = np.zeros(days_sorted.size, dtype=np.int64)
    if days_sorted.size:
        newg = np.empty(days_sorted.size, dtype=bool)
        newg[0] = True
        newg[1:] = days_sorted[1:] != days_sorted[:-1]
        gstart = np.maximum.accumulate(np.where(newg, np.arange(days_sorted.size), 0))
    rank = np.empty(order.size, dtype=np.int64)
    rank[order] = np.arange(order.size, dtype=np.int64) - gstart
    node = rank[np.searchsorted(u2, pairkey)]
    return node, u2, day_of_u2


def _motifs(day_gid: np.ndarray, code: np.ndarray, n_groups: int,
            n_codes: int) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    """(体・日)の地点列 → モチーフ索引。**ループなし**(正準化だけ種類数ぶん)。

    Schneider の定義に合わせて **連続する同じ地点は畳む**(滞在時間・活動語・時刻は捨てる)。
    """
    labels: list[str] = ["N0:"]
    motif = np.zeros(n_groups, dtype=np.int32)
    closed = np.zeros(n_groups, dtype=bool)
    capped = np.zeros(n_groups, dtype=bool)
    if day_gid.size == 0:
        return labels, motif, closed, capped
    newday = np.empty(day_gid.size, dtype=bool)
    newday[0] = True
    newday[1:] = day_gid[1:] != day_gid[:-1]
    keep = newday.copy()
    keep[1:] |= code[1:] != code[:-1]
    dk = day_gid[keep]
    cd = code[keep]
    node, _u2, day_of_u2 = _appearance_nodes(dk, cd, n_codes)
    n_nodes = np.bincount(day_of_u2, minlength=n_groups)
    # 始点=終点(その日の最初と最後の地点が同じ)
    firstk = np.empty(dk.size, dtype=bool)
    firstk[0] = True
    firstk[1:] = dk[1:] != dk[:-1]
    lastk = np.empty(dk.size, dtype=bool)
    lastk[-1] = True
    lastk[:-1] = dk[1:] != dk[:-1]
    closed[dk[firstk]] = cd[firstk] == cd[lastk]
    # 辺(連続する異なる地点)
    same = dk[1:] == dk[:-1]
    K = int(n_nodes.max()) + 1 if n_nodes.size else 1
    e_day = dk[1:][same]
    e_code = node[:-1][same] * K + node[1:][same]
    ekey = np.unique(e_day * (K * K) + e_code)
    e_day = ekey // (K * K)
    e_code = (ekey % (K * K)).astype(np.int64)
    per_day = np.bincount(e_day, minlength=n_groups)
    emax = int(per_day.max()) if per_day.size else 0
    mat = np.full((n_groups, 1 + emax), -1, dtype=np.int32)
    mat[:, 0] = n_nodes
    if emax:
        starts = np.cumsum(per_day) - per_day
        slot = np.arange(e_day.size, dtype=np.int64) - starts[e_day]
        mat[e_day, 1 + slot] = e_code
    uniq, inv = np.unique(mat, axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel()
    labels: list[str] = []
    ok_flags = np.ones(uniq.shape[0], dtype=bool)
    for r in range(uniq.shape[0]):  # 種類数ぶん(体比例ではない)
        nn = int(uniq[r, 0])
        es = [(int(v) // K, int(v) % K) for v in uniq[r, 1:] if v >= 0]
        lab, ok = canonical_motif(es, nn)
        labels.append(lab)
        ok_flags[r] = ok
    # 正準形が同じ行はひとつにまとめ直す
    lab_u, lab_inv = np.unique(np.asarray(labels), return_inverse=True)
    motif = np.asarray(lab_inv, dtype=np.int32).ravel()[inv].astype(np.int32)
    capped = ~ok_flags[inv]
    return [str(x) for x in lab_u], motif, closed, capped


def build_scope(s: Sample, days: Sequence[int], *, m8_mask_cap: int = 1024) -> ScopeCache:
    """1 スコープぶんの中間結果を作る(種別に依らない部分は**ここで 1 度だけ**)。"""
    sel = np.isin(s.row_day, np.asarray(days, dtype=np.int64))
    ra, rd = s.row_agent[sel], s.row_day[sel]
    st, en = s.start[sel], s.end[sel]
    act, plc, tc = s.activity[sel], s.place_kind[sel], s.target_cell[sel]
    n = s.n_agents
    daykey = ra * N_DAYS + rd
    gid, _ = _dense(daykey) if daykey.size else (np.zeros(0, np.int64), 0)
    uday = np.unique(daykey)
    G = int(uday.size)
    day_agent = (uday // N_DAYS).astype(np.int64)
    day_index = (uday % N_DAYS).astype(np.int64)
    day_count = np.bincount(gid, minlength=G)
    # 地点コード(場所種別+cell)と 場所種別だけ
    place_raw = plc * (int(tc.max()) + 2 if tc.size else 2) + (tc + 1)
    code, n_codes = _dense(place_raw) if place_raw.size else (np.zeros(0, np.int64), 1)
    day_distinct_place = np.bincount(np.unique(gid * max(n_codes, 1) + code) // max(n_codes, 1),
                                     minlength=G) if code.size else np.zeros(G, np.int64)
    day_distinct_kind = np.bincount(np.unique(gid * 16 + plc) // 16, minlength=G) \
        if plc.size else np.zeros(G, np.int64)
    day_coverage = covered_minutes(gid, st, en, G) / MINUTES_PER_DAY
    day_has_sleep = np.zeros(G, dtype=bool)
    if act.size:
        day_has_sleep[gid[act == ACT_SLEEP]] = True
    night = ((act == ACT_PREP) | (act == ACT_RIDE)) & (st < NIGHT_END) & (en > NIGHT_START)
    day_night_bad = np.bincount(gid[night], minlength=G) if act.size else np.zeros(G, np.int64)
    labels, motif, closed, capped = _motifs(gid, code, G, max(n_codes, 1))
    # 勤務開始(その日の最初)と 出勤代理(勤務のある日だけ)
    work_start = np.full(G, 1 << 30, dtype=np.int64)
    isw = act == ACT_WORK
    if isw.any():
        np.minimum.at(work_start, gid[isw], st[isw])
    has_work = work_start < (1 << 30)
    ismv = (act == ACT_MOVE) | (act == ACT_RIDE)
    proxy = np.full(G, -1, dtype=np.int64)
    if ismv.any():
        g2, s2 = gid[ismv], st[ismv]
        before = has_work[g2] & (s2 < work_start[g2])
        if before.any():
            np.maximum.at(proxy, g2[before], s2[before])
    work_start = np.where(has_work, work_start, -1)
    # M6: 日対の交わり・和集合((活動, 場所)集合)
    pairs = list(itertools.combinations(range(len(days)), 2))
    pos_of_day = np.full(N_DAYS, 0, dtype=np.int64)
    pos_of_day[np.asarray(days, dtype=np.int64)] = np.arange(len(days), dtype=np.int64)
    combo_raw = act * 16 + plc
    ccode, n_ccodes = _dense(combo_raw) if combo_raw.size else (np.zeros(0, np.int64), 1)
    pair_inter = np.zeros((len(pairs), n), dtype=np.int64)
    pair_union = np.zeros((len(pairs), n), dtype=np.int64)
    pair_both = np.zeros((len(pairs), n), dtype=bool)
    if ccode.size:
        akey = ra * max(n_ccodes, 1) + ccode
        ukey = np.unique(akey)
        bits = _or_by_group(np.searchsorted(ukey, akey), pos_of_day[rd], ukey.size, N_DAYS)
        uag = (ukey // max(n_ccodes, 1)).astype(np.int64)
        size = np.zeros((len(days), n), dtype=np.int64)
        for i in range(len(days)):
            size[i] = np.bincount(uag[(bits >> i) & 1 == 1], minlength=n)
        for pi, (i, j) in enumerate(pairs):
            both = (((bits >> i) & 1) == 1) & (((bits >> j) & 1) == 1)
            pair_inter[pi] = np.bincount(uag[both], minlength=n)
            pair_union[pi] = size[i] + size[j] - pair_inter[pi]
            # **両日とも活動がある体だけ**を数える。片方が空の対を J=0 で入れると
            # 「その曜日に活動が無い」ことが「似ていない」に化ける(D-68 の測り違い)。
            pair_both[pi] = (size[i] > 0) & (size[j] > 0)
    # M8 部分測定: 場所種別の 12 bit 集合と (場所種別, cell) の容量
    agent_place_mask = _or_by_group(ra, plc, n, 16) if plc.size else np.zeros(n, dtype=np.int64)
    agent_capacity_cell = np.bincount(
        np.unique(ra * max(n_codes, 1) + code) // max(n_codes, 1), minlength=n
    ) if code.size else np.zeros(n, dtype=np.int64)
    # M2 署名(体ごと・スコープ内 / day0)
    sig: dict[str, np.ndarray] = {}
    off_scope = np.searchsorted(ra, np.arange(n + 1))
    sig["scope_untimed"] = group_digests((act * 16 + plc).astype(np.int64), off_scope)
    sig["scope_timed"] = group_digests(((st * 16 + act) * 16 + plc).astype(np.int64), off_scope)
    d0 = rd == 0
    ra0 = ra[d0]
    off0 = np.searchsorted(ra0, np.arange(n + 1))
    sig["day0_untimed"] = group_digests((act[d0] * 16 + plc[d0]).astype(np.int64), off0)
    sig["day0_timed"] = group_digests(((st[d0] * 16 + act[d0]) * 16 + plc[d0]).astype(np.int64),
                                      off0)
    return ScopeCache(
        days=tuple(int(d) for d in days), n_agents=n,
        day_agent=day_agent, day_index=day_index, day_count=day_count,
        day_distinct_place=day_distinct_place, day_distinct_kind=day_distinct_kind,
        day_coverage=day_coverage, day_has_sleep=day_has_sleep, day_night_bad=day_night_bad,
        motif_labels=labels, motif_of_day=motif, motif_closed=closed, motif_capped=capped,
        work_start=work_start, work_rows_start=st[isw], work_rows_agent=ra[isw],
        commute_proxy=proxy, row_agent=ra, row_start=st, row_place=plc,
        row_block=(s.block_kind[sel] if s.block_kind is not None else None),
        pairs=pairs, pair_inter=pair_inter, pair_union=pair_union, pair_both=pair_both,
        agent_place_mask=agent_place_mask, agent_capacity_cell=agent_capacity_cell,
        sig=sig,
    )


def _mutual_jaccard(masks: np.ndarray, cap: int = 1024) -> dict[str, Any]:
    """場所種別集合(12 bit)の**相互 Jaccard**。種類が少ないので全対の厳密平均が出せる。"""
    m = masks[masks > 0]
    if m.size < 2:
        return {"n_agents": int(m.size), "mean": None, "exact": None}
    u, c = np.unique(m, return_counts=True)
    if u.size > cap:  # 種類が多すぎるときだけ標本に落とす(起きない見込み)
        rng = np.random.default_rng(0)
        idx = rng.choice(u.size, cap, replace=False)
        u, c = u[idx], c[idx]
        exact = False
    else:
        exact = True
    inter = _popcount(u[:, None] & u[None, :]).astype(np.float64)
    union = _popcount(u[:, None] | u[None, :]).astype(np.float64)
    J = np.divide(inter, union, out=np.ones_like(inter), where=union > 0)
    W = c[:, None].astype(np.float64) * c[None, :].astype(np.float64)
    np.fill_diagonal(W, c.astype(np.float64) * (c - 1))
    tot = W.sum()
    return {"n_agents": int(m.size), "mean": float((J * W).sum() / tot) if tot else None,
            "exact": exact}


# ================================================================= 種別ごとの表

def measure_group(s: Sample, sc: ScopeCache, agent_mask: np.ndarray,
                  anchors: Mapping[str, Any]) -> dict[str, Any]:
    """1 つの (曜日スコープ × 種別) の指標一式。**純関数**(配列を畳むだけ)。"""
    thr = float(anchors["anchors"]["motif_threshold"]["value"])
    dsel = agent_mask[sc.day_agent]
    rsel = agent_mask[sc.row_agent]
    asel = agent_mask
    out: dict[str, Any] = {
        "n_agents": int(asel.sum()),
        "n_agent_days": int(dsel.sum()),
        "n_rows": int(rsel.sum()),
    }
    out["m1"] = motif_table(sc.motif_labels, sc.motif_of_day[dsel], threshold=thr,
                            closed=sc.motif_closed[dsel], capped=sc.motif_capped[dsel])
    out["m1"]["place_basis"] = "(place_kind, target_cell)"
    out["m2"] = {k: signature_stats(v[asel]) for k, v in sc.sig.items()}
    out["m3a"] = time_stats(sc.row_start[rsel])
    proxy = sc.commute_proxy[dsel]
    out["m3b"] = time_stats(proxy[proxy >= 0])
    out["m3b"]["n_agent_days_with_work"] = int((sc.work_start[dsel] >= 0).sum())
    out["m3b"]["n_missing_proxy"] = int(((sc.work_start[dsel] >= 0) & (proxy < 0)).sum())
    ws = sc.work_start[dsel]
    out["m3c"] = time_stats(ws[ws >= 0])
    out["m3c_all_work_rows"] = time_stats(sc.work_rows_start[agent_mask[sc.work_rows_agent]])
    out["m4a"] = mean_sd(sc.day_count[dsel])
    dk = sc.day_distinct_kind[dsel]
    dp = sc.day_distinct_place[dsel]
    out["m4b"] = {
        "place_kind": {**mean_sd(dk),
                       "lt7_share": float(np.mean(dk < 7)) if dk.size else None},
        "place_cell": {**mean_sd(dp),
                       "lt7_share": float(np.mean(dp < 7)) if dp.size else None},
    }
    out["m6"] = _jaccard_block(sc, asel, range(len(sc.pairs)))
    # 設計書 §5 の書き方 J(d0,d)= **最初の曜日を基準にした対だけ**(全対ではない)。
    d0_pairs = [k for k, (i, _j) in enumerate(sc.pairs) if i == 0]
    out["m6_from_d0"] = _jaccard_block(sc, asel, d0_pairs)
    cap_kind = _popcount(sc.agent_place_mask[asel]).astype(np.float64)
    cap_cell = sc.agent_capacity_cell[asel].astype(np.float64)
    cap_kind = cap_kind[cap_kind > 0]
    cap_cell = cap_cell[cap_cell > 0]
    mk, mc = mean_sd(cap_kind), mean_sd(cap_cell)
    out["m8_partial"] = {
        "measurable": "partial",
        "note": "場所種別までの部分測定。店・駅・公園の target_cell が未解決(-1)なので"
                "「馴染みの場所」の中身は比べられない(設計書 §7 自宅セル解決率 ≥0.95 が前提)。",
        "capacity_place_kind": {**mk,
                                "cv": (mk["sd"] / mk["mean"]) if mk["mean"] else None},
        "capacity_place_cell": {**mc,
                                "cv": (mc["sd"] / mc["mean"]) if mc["mean"] else None},
        "mutual_jaccard_place_kind": _mutual_jaccard(sc.agent_place_mask[asel]),
    }
    out["harm_block"] = block_consistency(
        None if sc.row_block is None else sc.row_block[rsel], sc.row_place[rsel])
    cov = sc.day_coverage[dsel]
    out["harm_structural"] = {
        "n": int(dsel.sum()),
        "coverage_mean": float(cov.mean()) if cov.size else None,
        "coverage_ge_0999_share": float(np.mean(cov >= 0.999)) if cov.size else None,
        "sleep_line_share": float(np.mean(sc.day_has_sleep[dsel])) if dsel.any() else None,
        "night_violation_rows": int(sc.day_night_bad[dsel].sum()),
        "night_violation_day_share": (float(np.mean(sc.day_night_bad[dsel] > 0))
                                      if dsel.any() else None),
        "lines_per_day": mean_sd(sc.day_count[dsel]),
        "lines_per_day_min": int(sc.day_count[dsel].min()) if dsel.any() else None,
        "lines_per_day_max": int(sc.day_count[dsel].max()) if dsel.any() else None,
    }
    return out


def _jaccard_block(sc: "ScopeCache", asel: np.ndarray, pair_idx) -> dict[str, Any]:
    """選んだ日対だけの Jaccard(平均±sd・完全一致率)。**純関数**。

    ``pair_both`` で**両日に活動がある体だけ**を数える(片方が空の対を J=0 に落とすと
    「その曜日は出歩かない」が「似ていない」に化ける)。
    """
    ii = list(pair_idx)
    if not ii:
        return {"n": 0, "mean": None, "sd": None, "exact_share": None, "n_day_pairs": 0}
    inter = sc.pair_inter[ii][:, asel]
    union = sc.pair_union[ii][:, asel]
    ok = sc.pair_both[ii][:, asel] & (union > 0)
    if not ok.any():
        return {"n": 0, "mean": None, "sd": None, "exact_share": None, "n_day_pairs": len(ii)}
    J = inter[ok] / union[ok]
    return {**mean_sd(J), "exact_share": float(np.mean(inter[ok] == union[ok])),
            "n_day_pairs": len(ii),
            "pairs": [f"d{sc.days[i]}-d{sc.days[j]}" for i, j in (sc.pairs[k] for k in ii)][:8]}


#: 全体値を層化重みで畳むときに「件数」に使う欄(この欄を持つ辞書の数値だけ加重する)。
_WEIGHT_N_KEY = "n"


def _weighted(nodes: Sequence[tuple[float, Any]]) -> Any:
    """``(重み, 値)`` の並び → 加重した同じ形。辞書は再帰・``n`` 欄を持つ辞書だけ加重する。

    ``n`` が無い辞書(件数の定義が無い= M1 の個数や M2 の種類数)は**加重できない**ので
    数値を ``None`` にする(第一種別の値を全体として出してしまわないため)。
    """
    first = nodes[0][1]
    if not isinstance(first, dict):
        return None
    out: dict[str, Any] = {}
    wn = [(w, d) for w, d in nodes if isinstance(d, dict)]
    has_n = isinstance(first.get(_WEIGHT_N_KEY), int) and not isinstance(
        first.get(_WEIGHT_N_KEY), bool)
    for key, proto in first.items():
        if isinstance(proto, dict):
            out[key] = _weighted([(w, d.get(key)) for w, d in wn])
        elif key == _WEIGHT_N_KEY:
            out[key] = int(sum(d.get(key) or 0 for _w, d in wn))
        elif has_n and isinstance(proto, (int, float)) and not isinstance(proto, bool):
            num = den = 0.0
            for (w, d) in wn:
                v, nn = d.get(key), d.get(_WEIGHT_N_KEY) or 0
                if v is None or isinstance(v, bool) or not isinstance(v, (int, float)):
                    continue
                num += w * nn * float(v)
                den += w * nn
            out[key] = (num / den) if den else None
        elif isinstance(proto, str):
            out[key] = proto if key in ("place_basis", "note", "measurable") else None
        else:
            out[key] = None
    return out


def measure(s: Sample, anchors: Mapping[str, Any], *,
            pop_counts: np.ndarray | None = None) -> dict[str, Any]:
    """1 標本 → 全スコープ・全種別の表。**純関数**。"""
    kinds_present = sorted({int(k) for k in s.kind if k >= 0})
    n_by_kind = {k: int((s.kind == k).sum()) for k in kinds_present}
    weights: dict[str, float] = {}
    for k in kinds_present:
        if pop_counts is not None and n_by_kind[k]:
            weights[str(k)] = float(pop_counts[k]) / n_by_kind[k]
        else:
            weights[str(k)] = 1.0
    scopes: dict[str, Any] = {}
    for name, days in SCOPES.items():
        sc = build_scope(s, days)
        by_kind = {str(k): measure_group(s, sc, s.kind == k, anchors) for k in kinds_present}
        overall = measure_group(s, sc, np.ones(s.n_agents, dtype=bool), anchors)
        weighted = _weighted([(weights[str(k)], by_kind[str(k)]) for k in kinds_present]) \
            if kinds_present else None
        scopes[name] = {"days": list(days), "overall": overall,
                        "overall_weighted": weighted, "by_kind": by_kind}
    return {
        "label": s.label,
        "source": s.source,
        "input": s.input_kind,
        "arm": s.arm,
        "n_agents": s.n_agents,
        "n_rows": s.n_rows,
        "kind_counts": {str(k): n_by_kind[k] for k in kinds_present},
        "kind_unknown": int((s.kind < 0).sum()),
        "weights": weights,
        "weights_note": "w_k = W16 母集団の種別体数 ÷ 標本の種別体数(設計書 §4)。"
                        "全件を測ったランでは 1.0 になる。",
        "scopes": scopes,
        "ingest": s.ingest,
    }


# ================================================================= 比較の仕様

#: 比較する指標。``path`` は ``scopes[SCOPE]["overall"]`` からの経路。
#: ``anchor``= 台帳の項目名(``None``=現実側の目標が無い=方向だけ見る)。
#: ``direction``= 現実へ寄る向き(``lower``/``higher``/``None``=アンカーとの距離で見る)。
CMP_SPECS: tuple[dict[str, Any], ...] = (
    {"id": "m1_n_motifs", "label": "M1 モチーフ個数(≥0.5%)",
     "path": ("m1", "n_motifs_ge_threshold"), "anchor": "motif_count", "direction": None},
    {"id": "m1_coverage", "label": "M1 累積被覆",
     "path": ("m1", "coverage_ge_threshold"), "anchor": "motif_coverage", "direction": None},
    {"id": "m2_top1_timed", "label": "M2 上位1型占有率(時刻込み・d0)",
     "path": ("m2", "day0_timed", "top1_share"),
     "anchor": "tokyo_weekday_depart_top_bin_share", "direction": None,
     "note": "代理(現実の最頻 15 分ビン)。単独で不合格にしない"},
    {"id": "m2_types_untimed", "label": "M2 種類率(時刻なし・d0)",
     "path": ("m2", "day0_untimed", "type_rate"), "anchor": None, "direction": "higher"},
    {"id": "m3a_on", "label": "M3a 全活動 :00+:30",
     "path": ("m3a", "on_00_30"), "anchor": "tokyo_weekday_depart_on_00_30",
     "direction": None, "note": "アンカーは出勤時刻=全活動の直接の相手ではない"},
    {"id": "m3a_H", "label": "M3a 全活動 H[bit]",
     "path": ("m3a", "entropy_bits"), "anchor": None, "direction": "higher"},
    {"id": "m3b_on", "label": "M3b 出勤代理 :00+:30",
     "path": ("m3b", "on_00_30"), "anchor": "tokyo_weekday_depart_on_00_30", "direction": None},
    {"id": "m3b_top", "label": "M3b 出勤代理 最頻ビン占有",
     "path": ("m3b", "top_bin_share"), "anchor": "tokyo_weekday_depart_top_bin_share",
     "direction": None},
    {"id": "m3b_H", "label": "M3b 出勤代理 H[bit]",
     "path": ("m3b", "entropy_bits"), "anchor": "tokyo_weekday_depart_entropy_bits",
     "direction": None, "note": "こちらは 96 ビン・アンカーは 58 区分=上限が違う"},
    {"id": "m3c_on", "label": "M3c 勤務開始 :00+:30",
     "path": ("m3c", "on_00_30"), "anchor": "depart_on_00_30_band_by_employment",
     "direction": None},
    {"id": "m3c_H", "label": "M3c 勤務開始 H[bit]",
     "path": ("m3c", "entropy_bits"), "anchor": None, "direction": "higher"},
    {"id": "m4a_sd", "label": "M4a 活動数/日 sd",
     "path": ("m4a", "sd"), "anchor": None, "direction": "higher"},
    {"id": "m4b_lt7", "label": "M4b 場所数 7 未満の割合",
     "path": ("m4b", "place_cell", "lt7_share"), "anchor": "daily_locations_lt7_share",
     "direction": None},
    {"id": "m4b_sd", "label": "M4b 場所数 sd",
     "path": ("m4b", "place_cell", "sd"), "anchor": None, "direction": "higher"},
    {"id": "m6_mean", "label": "M6 日間 Jaccard 平均",
     "path": ("m6", "mean"), "anchor": None, "direction": None,
     "note": "J≈1 も J≈0 も現実ではない=方向を決めない(台帳 activity_set_jaccard_decay_lambda)"},
    {"id": "m6_exact", "label": "M6 完全一致率",
     "path": ("m6", "exact_share"), "anchor": None, "direction": "lower"},
    {"id": "m8_cap_cv", "label": "M8 容量(場所種別)の変動係数",
     "path": ("m8_partial", "capacity_place_kind", "cv"), "anchor": None, "direction": None},
    {"id": "m8_mutual_J", "label": "M8 相互 Jaccard(場所種別)",
     "path": ("m8_partial", "mutual_jaccard_place_kind", "mean"), "anchor": None,
     "direction": "lower"},
    {"id": "harm_coverage", "label": "弊害 被覆率 平均",
     "path": ("harm_structural", "coverage_mean"), "anchor": None, "direction": "higher"},
    {"id": "harm_sleep", "label": "弊害 就寝行あり率",
     "path": ("harm_structural", "sleep_line_share"), "anchor": None, "direction": "higher"},
    {"id": "harm_night", "label": "弊害 深夜違反のある日の割合",
     "path": ("harm_structural", "night_violation_day_share"), "anchor": None,
     "direction": "lower"},
)


def dig(d: Mapping[str, Any] | None, path: Sequence[str]) -> Any:
    """入れ子辞書から経路で取り出す(欠けていたら ``None``)。**純関数**。"""
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _anchor_target(anchors: Mapping[str, Any], key: str | None) -> tuple[Any, Any, str]:
    """アンカー名 → ``(点の値, 帯, 種別)``。帯は ``(low, high)``。**純関数**。

    ``value`` が**数でない**(区分別の内訳辞書など・第154 で親が
    ``depart_on_00_30_band_by_employment`` に加えた形)ときは点の目標として使わず、
    ``low``/``high`` の帯へ落とす。台帳が細かくなっても距離の出し方は変えない。
    """
    if not key:
        return None, None, "none"
    a = anchors["anchors"].get(key)
    if a is None:
        return None, None, "none"
    v = a.get("value")
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v), None, "value"
    if "low" in a and "high" in a:
        return None, (float(a["low"]), float(a["high"])), "band"
    return None, None, "none"


def _gap(value: Any, target: Any, band: Any) -> float | None:
    """現実側との距離(帯なら帯からのはみ出し)。"""
    if value is None:
        return None
    if target is not None:
        return abs(float(value) - float(target))
    if band is not None:
        lo, hi = band
        if value < lo:
            return float(lo - value)
        if value > hi:
            return float(value - hi)
        return 0.0
    return None


def compare(after: Mapping[str, Any], before: Mapping[str, Any] | None,
            anchors: Mapping[str, Any], scope: str = "weekday") -> list[dict[str, Any]]:
    """指標ごとに「現実アンカーとの距離」と「前より近づいたか」を並べる。**純関数**。"""
    rows: list[dict[str, Any]] = []
    ma = dig(after, ("scopes", scope, "overall"))
    mb = dig(before, ("scopes", scope, "overall")) if before else None
    for spec in CMP_SPECS:
        va = dig(ma, spec["path"])
        vb = dig(mb, spec["path"]) if mb else None
        tgt, band, _kind = _anchor_target(anchors, spec.get("anchor"))
        ga, gb = _gap(va, tgt, band), _gap(vb, tgt, band)
        closer: bool | None = None
        if ga is not None and gb is not None:
            closer = ga < gb
        elif spec.get("direction") and va is not None and vb is not None:
            closer = (va < vb) if spec["direction"] == "lower" else (va > vb)
        rows.append({
            "id": spec["id"], "metric": spec["label"],
            "before": vb, "after": va,
            "delta": (None if va is None or vb is None else float(va) - float(vb)),
            "target": tgt, "band": list(band) if band else None,
            "anchor": spec.get("anchor"), "direction": spec.get("direction"),
            "gap_before": gb, "gap_after": ga,
            "improvement_rate": (None if not gb else (gb - ga) / gb) if ga is not None else None,
            "closer": closer, "note": spec.get("note", ""),
        })
    return rows


def floor_rows(a: Mapping[str, Any], b: Mapping[str, Any],
               scope: str = "weekday") -> list[dict[str, Any]]:
    """同腕 2 標本の差 ``|A−B|`` = 揺らぎのフロア。**純関数**。"""
    ma = dig(a, ("scopes", scope, "overall"))
    mb = dig(b, ("scopes", scope, "overall"))
    out: list[dict[str, Any]] = []
    for spec in CMP_SPECS:
        va, vb = dig(ma, spec["path"]), dig(mb, spec["path"])
        out.append({"id": spec["id"], "metric": spec["label"], "a": va, "b": vb,
                    "abs_diff": (None if va is None or vb is None
                                 else abs(float(va) - float(vb)))})
    return out


#: 設計書 §5 の前値との突合(``p0_prior`` の名前 → 指標の経路とスコープ)。
PRIOR_MAP: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("m3a_on_00_30", ("m3a", "on_00_30"), "all_days", "M3a :00+:30"),
    ("m3a_entropy_bits", ("m3a", "entropy_bits"), "all_days", "M3a H[bit]"),
    ("m3b_on_00_30", ("m3b", "on_00_30"), "all_days", "M3b :00+:30"),
    ("m3b_top_bin", ("m3b", "top_bin"), "all_days", "M3b 最頻ビン"),
    ("m3b_top_bin_share", ("m3b", "top_bin_share"), "all_days", "M3b 最頻占有"),
    ("m3b_entropy_bits", ("m3b", "entropy_bits"), "all_days", "M3b H[bit]"),
    ("m3c_on_00_30", ("m3c_all_work_rows", "on_00_30"), "weekday", "M3c :00+:30(勤務行 全件)"),
    ("m3c_top_bin", ("m3c_all_work_rows", "top_bin"), "weekday", "M3c 最頻ビン"),
    ("m3c_top_bin_share", ("m3c_all_work_rows", "top_bin_share"), "weekday", "M3c 最頻占有"),
    ("m3c_entropy_bits", ("m3c_all_work_rows", "entropy_bits"), "weekday", "M3c H[bit]"),
    ("m4a_mean", ("m4a", "mean"), "all_days", "M4a 活動数 平均"),
    ("m4a_sd", ("m4a", "sd"), "all_days", "M4a 活動数 sd"),
    ("m4b_place_kind_mean", ("m4b", "place_kind", "mean"), "all_days", "M4b 場所種別数 平均"),
    ("m4b_place_kind_sd", ("m4b", "place_kind", "sd"), "all_days", "M4b 場所種別数 sd"),
    ("m4b_lt7_share", ("m4b", "place_kind", "lt7_share"), "all_days", "M4b 7 未満の割合"),
    ("m6_mean", ("m6_from_d0", "mean"), "all_days", "M6 J(d0,d) 平均"),
    ("m6_sd", ("m6_from_d0", "sd"), "all_days", "M6 J(d0,d) sd"),
    ("m6_exact_share", ("m6_from_d0", "exact_share"), "all_days", "M6 J(d0,d) 完全一致率"),
)
#: 通勤(kind 0)でだけ意味のある前値。
PRIOR_MAP_KIND0: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("m2_commuter_top1_share", ("m2", "day0_timed", "top1_share"), "weekday",
     "M2 上位1型(時刻込み・d0・通勤)"),
    ("m2_commuter_types", ("m2", "day0_untimed", "n_types"), "weekday",
     "M2 種類数(時刻なし・d0・通勤)"),
    ("m2_commuter_type_rate", ("m2", "day0_untimed", "type_rate"), "weekday",
     "M2 種類率(時刻なし・d0・通勤)"),
)


def prior_rows(m: Mapping[str, Any], anchors: Mapping[str, Any]) -> list[dict[str, Any]]:
    """設計書 §5 の前値と実測を並べる(**物差し自身の再現性検査**)。**純関数**。"""
    prior = anchors.get("p0_prior", {}).get("values", {})
    rows: list[dict[str, Any]] = []
    for key, path, scope, label in PRIOR_MAP:
        got = dig(dig(m, ("scopes", scope, "overall")), path)
        rows.append(_prior_row(key, label, scope, "全体", prior.get(key), got))
    for key, path, scope, label in PRIOR_MAP_KIND0:
        got = dig(dig(m, ("scopes", scope, "by_kind", "0")), path)
        rows.append(_prior_row(key, label, scope, "通勤", prior.get(key), got))
    return rows


def _prior_row(key: str, label: str, scope: str, group: str, want: Any, got: Any) -> dict[str, Any]:
    if isinstance(want, str) or isinstance(got, str):
        match = (want == got) if (want is not None and got is not None) else None
        return {"key": key, "metric": label, "scope": scope, "group": group,
                "prior": want, "measured": got, "diff": None, "match": match}
    if want is None or got is None:
        return {"key": key, "metric": label, "scope": scope, "group": group,
                "prior": want, "measured": got, "diff": None, "match": None}
    diff = float(got) - float(want)
    # 一致の判定 = **前値の記載桁の 1 単位以内**(0.919 なら ±0.001・5.78 なら ±0.01)。
    # 前値自体が丸めて書かれているので、丸め直して等号を取ると 0.8783 vs 0.879 のような
    # 「書き取りの端数」まで不一致に見えてしまう。
    dec = len(str(want).split(".")[1]) if "." in str(want) else 0
    match = abs(diff) <= 10.0 ** (-dec)
    return {"key": key, "metric": label, "scope": scope, "group": group,
            "prior": want, "measured": got, "diff": diff, "match": match}


# ================================================================= 報告

def _num(v: Any, nd: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return ", ".join(f"{k}={_num(x, nd)}" for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return "〜".join(_num(x, nd) for x in v)
    if isinstance(v, int):
        return f"{v:,}"
    return f"{float(v):,.{nd}f}"


def markdown(payload: Mapping[str, Any]) -> str:
    """JSON と同じ内容の表。**合格線は書かない**(距離と bool だけ)。"""
    after = payload["after"]
    before = payload.get("before")
    out: list[str] = [
        f"# 行動多様性の物差し(diversity yardstick) — {after['label']}"
        + (f" vs {before['label']}" if before else ""),
        "",
        f"- アンカー台帳: `{payload['anchors_path']}`({payload['anchors_version']})"
        f"・親一次確認**未**の項目 {len(payload['anchors_unverified'])} 件"
        + (f": {', '.join(payload['anchors_unverified'])}" if payload["anchors_unverified"] else ""),
        f"- after: `{after['source']}`(入力 {after['input']}・体 {after['n_agents']:,}"
        f"・行 {after['n_rows']:,}・種別不明 {after['kind_unknown']:,})",
    ]
    if before:
        out.append(f"- before: `{before['source']}`(入力 {before['input']}"
                   f"・体 {before['n_agents']:,}・行 {before['n_rows']:,})")
    out += [
        "- **合格線は書かない**。距離と「前より現実側へ近づいたか」の bool だけ(判定は親)。",
        "- 主スコープ=**平日(day<5)**。設計書 §5 の前値は**全 7 日**で測られているので、"
        "突合表だけ `all_days` を併記する。",
        "",
        "## 0 測れないもの(設計書 §5 の宣言をそのまま出す)",
        "",
        markdown_table(["ID", "状態", "理由"], [
            ["M5", "測れない", "S^real / Π^max は 7 日では出ない(Song は 3 か月・168 時間区分)。"
                               "下見では**報告のみ**"],
            ["M7", "測らない", "同一文脈での選択分散は C7 のテープ(呼と応答の対)でしか測れない"
                               "=下見の入力に無い"],
            ["M8", "部分測定", "馴染みの場所集合は target_cell 未解決(店・駅・公園が −1)なので"
                               "**場所種別まで**。容量の分散と相互 Jaccard を出す"],
            ["M1", "近似", "同上の理由で「場所=(place_kind, target_cell)」。店は全部同じ節点に"
                           "潰れる=**節点数は下振れ・モチーフ個数も下振れ**"],
        ]),
        "",
        "## 1 設計書 §5 の前値との突合(物差しの再現性検査)",
        "",
        markdown_table(
            ["指標", "スコープ", "群", "§5 前値", "実測", "差", "一致(±記載桁1単位)"],
            [[r["metric"], r["scope"], r["group"], _num(r["prior"], 4), _num(r["measured"], 4),
              _num(r["diff"], 4), ("—" if r["match"] is None else ("○" if r["match"] else "×"))]
             for r in payload["prior_check"]]),
        "",
        f"- 一致 {sum(1 for r in payload['prior_check'] if r['match'])} / "
        f"判定できた {sum(1 for r in payload['prior_check'] if r['match'] is not None)} 行。"
        "**×は物差しの誤りとは限らない**——前値側の数え方が書き残されていない可能性がある"
        "(親の判断待ち)。",
    ]
    for scope in ("weekday", "all_days"):
        out += _scope_section(after, scope)
    if after.get("ingest"):
        g = after["ingest"]
        out += ["", "## 4 弊害側(応答 jsonl の取り込み)", "",
                markdown_table(["欄", "値"], [
                    ["応答行", _num(g["n_response_rows"])],
                    ["体(テキストあり)", _num(g["n_agents_with_text"])],
                    ["活動 0 件の体", _num(g["n_agents_no_acts"])],
                    ["検査した行", _num(g["n_lines_considered"])],
                    ["採れた活動", _num(g["n_parsed_acts"])],
                    ["parse 失敗行", _num(g["parse_fail_lines"])],
                    ["**parse 失敗率**", _num(g["parse_fail_rate"], 4)],
                    ["形式", g["format"]],
                    ["ブロック行", _num(g["n_block_rows"])],
                    ["理由の内訳", ", ".join(f"{k}={v}" for k, v in sorted(g["bad"].items())) or "—"],
                ])]
    if before:
        rows = payload["comparison"]
        out += ["", "## 5 前より現実側へ近づいたか(平日)", "",
                markdown_table(
                    ["指標", "before", "after", "差", "目標/帯", "距離 before", "距離 after",
                     "改善率", "近づいた", "注"],
                    [[r["metric"], _num(r["before"], 4), _num(r["after"], 4), _num(r["delta"], 4),
                      (_num(r["target"], 4) if r["target"] is not None
                       else (f"{r['band'][0]:.3f}〜{r['band'][1]:.3f}" if r["band"]
                             else ("小さいほど良い" if r["direction"] == "lower"
                                   else ("大きいほど良い" if r["direction"] == "higher" else "—")))),
                      _num(r["gap_before"], 4), _num(r["gap_after"], 4),
                      _num(r["improvement_rate"], 3),
                      ("—" if r["closer"] is None else ("yes" if r["closer"] else "no")),
                      r["note"]] for r in rows]),
                "",
                f"- 近づいた: {payload['comparison_counts']['closer']} / "
                f"判定できた {payload['comparison_counts']['judged']}"
                f"(判定不能 {payload['comparison_counts']['unjudged']})",
                "- **これは合格判定ではない**。重みづけと合格線は親が決める。"]
    if payload.get("floor"):
        f = payload["floor"]
        out += ["", f"## 6 フロア(同腕 2 標本 {f['a_label']} / {f['b_label']} の |A−B|)", "",
                markdown_table(["指標", "A", "B", "差の絶対値"],
                               [[r["metric"], _num(r["a"], 4), _num(r["b"], 4),
                                 _num(r["abs_diff"], 4)] for r in f["rows"]]),
                "",
                "- 腕の差がこの値を超えないなら、それは**効果ではなく揺らぎ**の範囲。"]
    out += ["", "## 7 現実アンカー(台帳の echo)", "",
            markdown_table(["項目", "値", "tag", "親一次確認", "出典"],
                           [[k, _num(a.get("value", a.get("values", a.get("low"))), 4),
                             a["tag"], a["verified_by"], a["source"][:90]]
                            for k, a in payload["anchors_echo"].items()])]
    return "\n".join(out)


def _scope_section(m: Mapping[str, Any], scope: str) -> list[str]:
    sc = m["scopes"][scope]
    ov = sc["overall"]
    wt = sc.get("overall_weighted")
    title = "2 平日(day<5)" if scope == "weekday" else "3 全 7 日"
    out = ["", f"## {title}", "",
           f"- 体 {ov['n_agents']:,}・(体・日) {ov['n_agent_days']:,}・行 {ov['n_rows']:,}",
           "- **層化重み 全体** = 種別ごとの値を w_k で加重平均したもの。**混合分布を数え直した値では"
           "ない**ので、H や sd のような非加法量は重みなし全体と一致しない(全件ランで w_k=1.0 でも"
           "ずれる)。率(:00+:30・完全一致率など)は一致する。",
           "- 件数の定義が無い欄(M1 の個数・M2 の種類数)は加重できないので「—」。", ""]
    head = ["指標", "重みなし 全体", "層化重み 全体"]
    rows = [
        ["M1 モチーフ個数(≥0.5%)", _num(ov["m1"]["n_motifs_ge_threshold"]), "—"],
        ["M1 相異なる形", _num(ov["m1"]["n_distinct"]), "—"],
        ["M1 累積被覆", _num(ov["m1"]["coverage_ge_threshold"], 4),
         _num(dig(wt, ("m1", "coverage_ge_threshold")), 4)],
        ["M1 始点=終点の割合", _num(ov["m1"]["closed_share"], 4), "—"],
        ["M2 種類率(時刻なし・d0)", _num(ov["m2"]["day0_untimed"]["type_rate"], 5), "—"],
        ["M2 上位1型(時刻なし・d0)", _num(ov["m2"]["day0_untimed"]["top1_share"], 4), "—"],
        ["M2 種類率(時刻込み・d0)", _num(ov["m2"]["day0_timed"]["type_rate"], 5), "—"],
        ["M2 上位1型(時刻込み・d0)", _num(ov["m2"]["day0_timed"]["top1_share"], 4), "—"],
        ["M3a :00+:30", _num(ov["m3a"]["on_00_30"], 4),
         _num(dig(wt, ("m3a", "on_00_30")), 4)],
        ["M3a H[bit]", _num(ov["m3a"]["entropy_bits"], 4),
         _num(dig(wt, ("m3a", "entropy_bits")), 4)],
        ["M3b :00+:30", _num(ov["m3b"]["on_00_30"], 4),
         _num(dig(wt, ("m3b", "on_00_30")), 4)],
        ["M3b 最頻ビン/占有", f"{ov['m3b']['top_bin']} / {_num(ov['m3b']['top_bin_share'], 4)}",
         "—"],
        ["M3b H[bit]", _num(ov["m3b"]["entropy_bits"], 4),
         _num(dig(wt, ("m3b", "entropy_bits")), 4)],
        ["M3c :00+:30(最初の勤務)", _num(ov["m3c"]["on_00_30"], 4),
         _num(dig(wt, ("m3c", "on_00_30")), 4)],
        ["M3c 最頻ビン/占有", f"{ov['m3c']['top_bin']} / {_num(ov['m3c']['top_bin_share'], 4)}",
         "—"],
        ["M3c H[bit]", _num(ov["m3c"]["entropy_bits"], 4),
         _num(dig(wt, ("m3c", "entropy_bits")), 4)],
        ["M4a 活動数/日 平均±sd",
         f"{_num(ov['m4a']['mean'], 3)}±{_num(ov['m4a']['sd'], 3)}",
         f"{_num(dig(wt, ('m4a', 'mean')), 3)}±{_num(dig(wt, ('m4a', 'sd')), 3)}"],
        ["M4b 場所数(種別+cell) 平均±sd",
         f"{_num(ov['m4b']['place_cell']['mean'], 3)}±{_num(ov['m4b']['place_cell']['sd'], 3)}",
         f"{_num(dig(wt, ('m4b', 'place_cell', 'mean')), 3)}"],
        ["M4b 7 未満の割合", _num(ov["m4b"]["place_cell"]["lt7_share"], 4),
         _num(dig(wt, ("m4b", "place_cell", "lt7_share")), 4)],
        ["M6 Jaccard 平均±sd",
         f"{_num(ov['m6']['mean'], 3)}±{_num(ov['m6']['sd'], 3)}",
         f"{_num(dig(wt, ('m6', 'mean')), 3)}"],
        ["M6 完全一致率", _num(ov["m6"]["exact_share"], 4),
         _num(dig(wt, ("m6", "exact_share")), 4)],
        ["M6 J(d0,d) 平均±sd(§5 の書き方)",
         f"{_num(dig(ov, ('m6_from_d0', 'mean')), 3)}±{_num(dig(ov, ('m6_from_d0', 'sd')), 3)}",
         _num(dig(wt, ("m6_from_d0", "mean")), 3)],
        ["M6 J(d0,d) 完全一致率", _num(dig(ov, ("m6_from_d0", "exact_share")), 4),
         _num(dig(wt, ("m6_from_d0", "exact_share")), 4)],
        ["M8 容量(種別) 平均/変動係数",
         f"{_num(ov['m8_partial']['capacity_place_kind']['mean'], 3)} / "
         f"{_num(ov['m8_partial']['capacity_place_kind']['cv'], 3)}", "—"],
        ["M8 相互 Jaccard(種別)",
         _num(ov["m8_partial"]["mutual_jaccard_place_kind"]["mean"], 4), "—"],
        ["弊害 被覆率 平均", _num(ov["harm_structural"]["coverage_mean"], 4),
         _num(dig(wt, ("harm_structural", "coverage_mean")), 4)],
        ["弊害 就寝行あり率", _num(ov["harm_structural"]["sleep_line_share"], 4), "—"],
        ["弊害 深夜違反のある日の割合",
         _num(ov["harm_structural"]["night_violation_day_share"], 5), "—"],
    ]
    hb = ov.get("harm_block", {})
    if hb.get("present"):
        rows += [
            ["弊害 block_kind と場所語の矛盾(行)", _num(hb["mismatch_rows"]), "—"],
            ["弊害 同 矛盾率(移動 4 を除く)", _num(hb["mismatch_share"], 5),
             _num(dig(wt, ("harm_block", "mismatch_share")), 5)],
        ]
    out.append(markdown_table(head, rows))
    if hb.get("present"):
        out += ["", f"- block_kind 内訳: "
                + " / ".join(f"{k} {v:,}" for k, v in hb["counts_by_block"].items())
                + f"(判定外 移動 {hb['n_move_unjudged']:,}・未知コード {hb['n_unknown_code']:,})",
                "- 矛盾の内訳: "
                + " / ".join(f"{k} {v:,}" for k, v in hb["by_rule"].items())
                + f"。規則は **{hb['rule']}**(設計書 §9 は対応表を持たない)。",
                "- **場所の判定には block_kind を使っていない**(M1〜M8 は place_kind / "
                "target_cell のまま)=この列が増えても既存の値は動かない。"]
    out += ["", f"### {title} — 種別ごと", "",
            markdown_table(
                ["種別", "体", "w_k", "M3a :00+:30", "M3b :00+:30", "M3b H", "M4a 平均±sd",
                 "M6 平均", "M6 完全一致", "M1 個数", "M2 上位1型(d0時刻込)"],
                [[f"{k} {KIND_JA[int(k)] if int(k) < len(KIND_JA) else '?'}",
                  _num(v["n_agents"]), _num(m["weights"].get(k), 1),
                  _num(dig(v, ("m3a", "on_00_30")), 4),
                  _num(dig(v, ("m3b", "on_00_30")), 4),
                  _num(dig(v, ("m3b", "entropy_bits")), 3),
                  f"{_num(dig(v, ('m4a', 'mean')), 2)}±{_num(dig(v, ('m4a', 'sd')), 2)}",
                  _num(dig(v, ("m6", "mean")), 3),
                  _num(dig(v, ("m6", "exact_share")), 3),
                  _num(dig(v, ("m1", "n_motifs_ge_threshold"))),
                  _num(dig(v, ("m2", "day0_timed", "top1_share")), 4)]
                 for k, v in sorted(sc["by_kind"].items(), key=lambda kv: int(kv[0]))])]
    top = ov["m1"]["top"][:8]
    if top:
        out += ["", f"### {title} — M1 上位モチーフ(近似)", "",
                markdown_table(["形(正準形)", "件数", "割合"],
                               [[t["motif"], _num(t["n"]), _num(t["share"], 4)] for t in top])]
    return out


# ================================================================= 組み立て・CLI

def jsonable(obj: Any) -> Any:
    """numpy のスカラを Python の型へ落とす(``json.dumps`` が通るように)。**純関数**。"""
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return [jsonable(v) for v in obj.tolist()]
    return obj


def anchors_echo(anchors: Mapping[str, Any]) -> dict[str, Any]:
    """報告に載せる現実側の数値(出典つきで JSON に残す)。"""
    return {k: {"value": a.get("value", a.get("values", a.get("low"))),
                "tag": a["tag"], "verified_by": a["verified_by"], "source": a["source"],
                "scope": a.get("scope", "")}
            for k, a in anchors["anchors"].items()}


def build_payload(after: Mapping[str, Any], anchors: Mapping[str, Any], *,
                  before: Mapping[str, Any] | None = None,
                  floor: tuple[Mapping[str, Any], Mapping[str, Any]] | None = None,
                  ) -> dict[str, Any]:
    """1 標本(または前後 2 標本・フロア 2 標本)→ 出力 JSON まるごと。**純関数**。"""
    payload: dict[str, Any] = {
        "schema": "shibuya.tools.w17/diversity_yardstick/1",
        "anchors_path": anchors.get("_path", str(DEFAULT_ANCHORS_PATH)),
        "anchors_version": anchors.get("version", "?"),
        "anchors_echo": anchors_echo(anchors),
        "anchors_unverified": unverified_anchors(anchors),
        "no_pass_line": "合格線は持たない=距離と『近づいたか』の bool のみ(判定は親)。",
        "approximations": {
            "m1_place": "場所=(place_kind, target_cell)。店・駅・公園は target_cell=-1 なので"
                        "同種別が 1 節点に潰れる=モチーフ個数・節点数は**下振れ**する近似。",
            "m1_canonical": f"節点数 {MOTIF_PERM_CAP} 以下は全順列で正準化(同型判定)。"
                            "超える日は出現順ラベルのまま(capped_share に計上)。",
            "m3_entropy_bins": "H は 1 日 96 ビン(15 分)。第30表は 58 区分=上限が違う"
                               "(6.585 bit vs 5.858 bit)。",
            "m5": "測れない(7 日では S^real / Π^max が出ない)。",
            "m7": "測らない(同一文脈の選択分散は C7 テープが要る)。",
            "m8": "部分測定(場所種別まで・cell 未解決)。",
        },
        "after": after,
        "prior_check": prior_rows(after, anchors),
    }
    if before is not None:
        rows = compare(after, before, anchors)
        judged = [r for r in rows if r["closer"] is not None]
        payload["before"] = before
        payload["comparison"] = rows
        payload["comparison_counts"] = {
            "judged": len(judged),
            "closer": sum(1 for r in judged if r["closer"]),
            "unjudged": len(rows) - len(judged),
        }
    if floor is not None:
        a, b = floor
        payload["floor"] = {"a_label": a["label"], "b_label": b["label"],
                            "rows": floor_rows(a, b)}
    return jsonable(payload)


def _load_sample(parquet: str | None, responses: Sequence[str] | None, world: str | None,
                 label: str | None, limit: int | None) -> Sample:
    if responses:
        return sample_from_responses(responses, world, label=label)
    if parquet or world:
        return sample_from_weekly(world, parquet=parquet, label=label, limit_agents=limit)
    raise SystemExit("--parquet か --responses か --world のどれかが要る")


def _load_any(path: str, world: str | None, label: str | None) -> Sample:
    """``--floor`` の 1 本(parquet でも jsonl でもよい)。名前は既定でファイル名。"""
    name = label or Path(path).stem
    if str(path).endswith(".jsonl"):
        return sample_from_responses([path], world, label=name)
    return sample_from_weekly(world, parquet=path, label=name)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="D-68: W17 の個体多様性を現実アンカーと同じ物差しで測る(前後比較・フロアつき)")
    ap.add_argument("--parquet", default=None,
                    help="W17 週次表(.parquet ファイル でも 世界資産ディレクトリ でもよい)")
    ap.add_argument("--responses", nargs="+", default=None, help="下見の応答 jsonl(複数可)")
    ap.add_argument("--world", default="data/world/v2", help="世界資産(種別と層化重みの出所)")
    ap.add_argument("--label", default=None, help="after 側の名前")
    ap.add_argument("--limit-agents", type=int, default=None, help="先頭 N 体だけ測る(小さく回す)")
    ap.add_argument("--before-parquet", default=None,
                    help="比較元(.parquet ファイル でも ディレクトリ でもよい)")
    ap.add_argument("--before-responses", nargs="+", default=None, help="比較元の応答 jsonl")
    ap.add_argument("--before-label", default="before", help="before 側の名前")
    ap.add_argument("--floor", nargs=2, default=None, metavar=("A", "B"),
                    help="同腕 2 標本(parquet か jsonl)= 揺らぎのフロア")
    ap.add_argument("--anchors", default=None, help=f"アンカー台帳(既定 {DEFAULT_ANCHORS_PATH})")
    ap.add_argument("--out", default=None, help="出力ディレクトリ(既定=標準出力のみ)")
    args = ap.parse_args(argv)

    anchors = load_anchors(args.anchors)
    pop_counts = population_kind_counts(args.world)
    after_s = _load_sample(args.parquet, args.responses, args.world,
                           args.label, args.limit_agents)
    after = measure(after_s, anchors, pop_counts=pop_counts)
    before = None
    if args.before_parquet or args.before_responses:
        before_s = _load_sample(args.before_parquet, args.before_responses, args.world,
                                args.before_label, args.limit_agents)
        before = measure(before_s, anchors, pop_counts=pop_counts)
    floor = None
    if args.floor:
        fa = measure(_load_any(args.floor[0], args.world, None), anchors, pop_counts=pop_counts)
        fb = measure(_load_any(args.floor[1], args.world, None), anchors, pop_counts=pop_counts)
        floor = (fa, fb)
    payload = build_payload(after, anchors, before=before, floor=floor)
    md = markdown(payload)
    if args.out:
        paths = write_outputs(args.out, "diversity_yardstick", payload, md)
        print(json.dumps(paths, ensure_ascii=False))
    print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
