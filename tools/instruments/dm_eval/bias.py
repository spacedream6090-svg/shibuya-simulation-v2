# -*- coding: utf-8 -*-
"""dm_eval.bias — 位置の偏りの対照試験(R-108 §1-1・§1-4・§3-1・C-2 の対策 1・第 6 期 6-1 の器)。

手順
    同じ状況で候補の並びを N 通り(``situations.orders``=``present`` の並びの巡回)に変えて採点し、次を出す。
    - **1 位が変わる率**(``top1_change_rate``)= N 通りで 1 位の候補(中身)が全部同じでない状況の割合。
      対ごとの率(``top1_change_pairwise``)= 状況ごとに「1 位が違う並びの対の数 ÷ C(N, 2)」の平均。
    - **自己整合**(``self_consistency_2``)= 0 番目と 1 番目の並びで同じ 1 位の状況の割合(採点の指標 (b))。
    - **番号 1 を選ぶ率**(``number1_rate``)と一様のときの値(``number1_expected``=1/n の平均)。
    - **PBS**(Wang 2026 §3.3・R-108 §1-4)= 位置ごとの選択の分布(並びの全部で平均)と一様分布の L2 の距離。
      「その他」(番号 n+1・並べ替えない)は位置に数えず ``other_top1_rate`` に分ける。候補の数 n ごとに出す。
    - **有意性の欄**: 状況ごとの d_i = (番号 1 を選んだ並びの割合) − 1/n_i の符号反転の並べ替え検定
      (``tools/c7/salt_compare.sign_flip_p``=10f の salt と同じ式・両側・n > 20 は 2^20 回の無作為の組)。
    期待: mock=0・古典=0(中身だけで決まる=負の対照)・テープ=並べ替えに対しては構成上 0(テープの LLM はここの
    並びを見ていない)・番号 1 の対照(``FirstNumberControl``)=正の対照(検出力)。

PBS の帰無の床(``pbs_null_floor``・フロア併記): 位置の偏りの無い当て口の PBS の分布を模擬で出す(340 件 × 巡回 4 通りで
    平均 約 0.021)。床の中の PBS は偏りの証拠にならない。

テープの固定の並び(``tape_fixed_order``): テープの LLM が見た B0 の語彙の並び(1=移動 … 12=就寝)での選んだ位置の
    分布。位置と中身が分けられない(並びが 1 通り)ので**記録だけ**(R-108 §3-1 (i)「ID の事前分布を記録するだけ」)。

expedient: d_i の分布は H0 でも左右対称とは限らない(巡回 4 通りでは割合が 0・1/4・… の離散)。340 件では中心極限で
    近似として読む(記録の限界に書く)。
"""

from __future__ import annotations

import importlib.util
import itertools
import math
import sys
import time
from typing import Any, Final, Mapping, Sequence

import numpy as np

import dm_eval  # noqa: F401
from dm_eval.judge import Scorer, top1
from dm_eval.situations import VOCAB, Situation, render, word_of_output
from shibuya.engine.decision.port import OTHER_ID, Candidate

SALT_COMPARE_PATH: Final = dm_eval.REPO / "tools" / "c7" / "salt_compare.py"
_SALT_NAME: Final[str] = "dm_eval_salt_compare"


def salt_compare() -> Any:
    """10f の salt の比較(``tools/c7/salt_compare.py``)を道筋から読む(1 回だけ)。"""
    if _SALT_NAME in sys.modules:
        return sys.modules[_SALT_NAME]
    spec = importlib.util.spec_from_file_location(_SALT_NAME, SALT_COMPARE_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError("salt_compare を読めない")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_SALT_NAME] = mod
    spec.loader.exec_module(mod)
    return mod


Record = tuple[tuple[Candidate, ...], dict[str, float]]


def score_orders(scorer: Scorer, situations: Sequence[Situation],
                 orders_by_sid: Mapping[str, Sequence[tuple[Candidate, ...]]], *, arm: str,
                 length: str = "short") -> tuple[dict[str, list[Record]], float]:
    """状況 × 並びの全部を採点する → (状況 → [(提示, 分布)]・1 件あたりの壁時計の秒)。"""
    out: dict[str, list[Record]] = {}
    n = 0
    t0 = time.perf_counter()
    for s in situations:  # 逐次ループ宣言: 状況 × 並び
        recs: list[Record] = []
        for pres in orders_by_sid[s.sid]:
            text = render(s, pres, length=length, arm=arm).text if scorer.reads_text else None
            recs.append((pres, scorer.score(s, pres, text=text)))
            n += 1
        out[s.sid] = recs
    wall = (time.perf_counter() - t0) / n if n else None
    return out, wall


def _number_of(pres: Sequence[Candidate], cid: str) -> int:
    if cid == OTHER_ID:
        return len(pres) + 1
    for c in pres:
        if c.id == cid:
            return int(c.number or 0)
    raise ValueError(f"提示に無い 1 位 {cid!r}")


def position_bias(records: Mapping[str, Sequence[Record]], *, test: bool = True) -> dict[str, Any]:
    """並べ替え試験の集計(上の説明の量)。``records`` は ``score_orders`` の 1 つ目。"""
    sids = sorted(records)
    if not sids:
        return {"n_situations": 0}
    n_orders = {len(records[s]) for s in sids}
    changed = 0
    pairwise: list[float] = []
    same2: list[float] = []
    d: list[float] = []
    picks = 0
    number1 = 0
    other = 0
    expected: list[float] = []
    pos_counts: dict[int, np.ndarray] = {}
    for s in sids:  # 逐次ループ宣言: 状況 × 並び
        recs = records[s]
        tops = [top1(dist) for _pres, dist in recs]
        nums = [_number_of(pres, t) for (pres, _dist), t in zip(recs, tops)]
        n = len(recs[0][0])
        if len(set(tops)) > 1:
            changed += 1
        pairs = list(itertools.combinations(range(len(tops)), 2))
        if pairs:
            pairwise.append(sum(tops[i] != tops[j] for i, j in pairs) / len(pairs))
        if len(tops) >= 2:
            same2.append(1.0 if tops[0] == tops[1] else 0.0)
        share1 = sum(1 for k in nums if k == 1) / len(nums)
        d.append(share1 - 1.0 / n)
        expected.append(1.0 / n)
        pc = pos_counts.setdefault(n, np.zeros(n, dtype=np.int64))
        for k in nums:
            picks += 1
            if k == n + 1:
                other += 1
            else:
                pc[k - 1] += 1
                number1 += int(k == 1)
    pbs = {}
    for n, cnt in sorted(pos_counts.items()):
        tot = int(cnt.sum())
        if tot == 0:
            pbs[str(n)] = {"picks": 0, "pbs": None, "position_dist": None}
            continue
        p = cnt / tot
        pbs[str(n)] = {"picks": tot, "pbs": float(math.sqrt(float(((p - 1.0 / n) ** 2).sum()))),
                       "position_dist": [float(x) for x in p]}
    out: dict[str, Any] = {
        "n_situations": len(sids), "n_orders": sorted(n_orders),
        "top1_change_rate": changed / len(sids),
        "top1_change_pairwise": float(np.mean(pairwise)) if pairwise else None,
        "self_consistency_2": float(np.mean(same2)) if same2 else None,
        "number1_rate": number1 / picks if picks else None,
        "number1_expected": float(np.mean(expected)),
        "other_top1_rate": other / picks if picks else None,
        "pbs_by_n": pbs,
    }
    if test:
        sf = salt_compare().sign_flip_p(np.asarray(d, dtype=np.float64), "two-sided")
        out["number1_test"] = {"statistic": "d_i = 番号 1 を選んだ並びの割合 − 1/n_i の平均", "mean_d": float(np.mean(d)),
                               "p": float(sf["p"]), "n": int(sf["n"]), "method": sf["method"],
                               "alternative": "two-sided", "formula": "tools/c7/salt_compare.sign_flip_p"}
    return out


#: PBS の帰無の床の模擬の回数と種。
FLOOR_REPS: Final[int] = 10_000
FLOOR_SEED: Final[str] = "dm61-pbs-floor"


def pbs_null_floor(n_situations: int, n: int, offsets: Sequence[int], *, reps: int = FLOOR_REPS,
                   seed: str | int = FLOOR_SEED) -> dict[str, Any]:
    """PBS の帰無の床(フロア併記): 中身だけで選ぶ当て口の PBS の分布を模擬で出す。

    帰無=位置の偏りが無い当て口。選んだ中身の 0 番目の並び(``present``=一様な置換)での位置は 0〜n−1 の一様。巡回の
    位置 r の並びでは (位置 − r) mod n に来る。状況 ``n_situations`` 件 × 並び ``len(offsets)`` 通りの位置の分布と一様の
    L2 の距離を ``reps`` 回(「その他」は選ばない)。
    """
    from shibuya.core.rng import stream

    if n_situations < 1 or n < 1:
        return {"reps": 0, "mean": None, "p05": None, "p50": None, "p95": None}
    g = stream(seed, "dm_eval.pbs_floor")
    base = g.integers(0, n, size=(int(reps), int(n_situations)))
    counts = np.zeros((int(reps), n), dtype=np.int64)
    rows = np.arange(int(reps), dtype=np.int64)[:, None] * n
    for r in offsets:  # 逐次ループ宣言: 並びの数
        pos = (base - int(r)) % n
        counts += np.bincount((rows + pos).ravel(), minlength=int(reps) * n).reshape(int(reps), n)
    p = counts / counts.sum(axis=1, keepdims=True)
    pbs = np.sqrt(((p - 1.0 / n) ** 2).sum(axis=1))
    q05, q50, q95 = (float(x) for x in np.quantile(pbs, [0.05, 0.5, 0.95]))
    return {"reps": int(reps), "n_situations": int(n_situations), "n": int(n), "offsets": [int(r) for r in offsets],
            "mean": float(pbs.mean()), "p05": q05, "p50": q50, "p95": q95, "seed": str(seed),
            "method": "模擬(選んだ中身の 0 番目の並びの位置が一様)"}


def tape_fixed_order(situations: Sequence[Situation]) -> dict[str, Any]:
    """テープの LLM が見た B0 の固定の並び(語彙 v1 の順)での選んだ位置の分布(記録だけ=位置と中身が分けられない)。"""
    counts = np.zeros(len(VOCAB), dtype=np.int64)
    other = 0
    for s in situations:
        w = word_of_output(s.tape_output)
        if w is None:
            other += 1
        else:
            counts[VOCAB.index(w)] += 1
    tot = int(counts.sum())
    return {"order": list(VOCAB), "counts": [int(x) for x in counts], "other": other,
            "position1_rate": float(counts[0] / tot) if tot else None, "position1_expected": 1.0 / len(VOCAB),
            "note": "並びが 1 通り=位置と中身が分けられない(記録だけ・R-108 §3-1 (i))"}
