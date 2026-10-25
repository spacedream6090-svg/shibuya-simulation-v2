# -*- coding: utf-8 -*-
"""hm_gauge — 第 3 期 3-3b **ヒストリーマッチング(HM)の直接判定の器**(器だけ・読むだけ・記録に JSON)。

正典
    決定 10-12 §4-5「複数ランの作り方」(初期状態はデータと矛盾しない世界を何通りか作る・ヒストリーマッチング(Vernon ら)で現実と
    明らかに合わない世界を先に除く・使う現実データは**較正用だけ**で検証用には触れない)・§1-6(係数で持たない)・PENDING 仮-24
    (HM の入力は**離散の seed の組だけ**=係数は持たない)・答申 R-117 §3(Vernon ら 2014 の非含意度の式 6・閾値 3=Pukelsheim の
    3σ・mogp-emulator(MIT)の ``HistoryMatching`` の既定=閾値 3・2 番目に大きい値・代理モデル無しの直接の判定=McCulloch ら
    2022・安い層で回す)。**候補の初期状態は第 4 期 4-1 の後**(本段は器と合成の試験だけ)。

式(代理モデル無しの直接の判定=候補ごとに複数本を回した出力の平均と分散をそのまま使う)
    I_k(x) = |z_k − Ē_k(x)| / √(Var_ens,k(x) + Var_obs,k + Var_disc,k)
    - z_k: 較正側の観測・Var_obs: 観測の誤差の分散・Var_disc: 宣言したモデルの食い違いの分散(v2 の「歪む場所の宣言」を数にした物
      =0 と置けない・R-117 §3-4)。
    - Ē_k(x)・Var_ens,k(x): 候補 x(離散の seed の組)で回した複数本の出力の平均と標本分散(n − 1)。1 本なら分散 0(宣言)。
    - 束ね: 指標が 2 つ以上なら **2 番目に大きい値** I_2M(x)(mogp-emulator の既定)・1 つなら最大 I_M(x)。I ≤ 3 の候補を残す。
      残りが空なら「シミュレータかデータの問題の強い警告」(Vernon ら)。
    コードは写していない(mogp-emulator は MIT=写せるが、式が単純なので原典の式から書いた)。

守り
    - 候補の欄は離散の seed の組(``CANDIDATE_KEYS``)だけ。ほかの欄(係数・連続の母数)は ``ValueError``(§1-6)。
    - 観測の行は ``side: "calibration"`` だけ(検証側は ``PermissionError``)。入力の道筋に封印と検証側の語
      (``read_guard.GAUGE_DENY_TOKENS``)があれば開く前に落とす(〔検収 M2〕照らすのは ``read_guard.deny_hit``=小文字に
      そろえた生の道筋と、当たらなければ実体の道筋=つなぎ・symlink を解いた形)。

入力::

    {"candidates": [{"population_seed": 11, "environment_seed": 11}, …],
     "runs": [[{"<指標>": 値, …}, …], …],            # 候補ごとの複数本(候補と同じ並び)
     "observations": {"<指標>": {"z": 値, "var_obs": 値, "var_disc": 値, "side": "calibration"}, …}}

使い方: ``python tools/instruments/hm_gauge.py judge --input <…>.json --out <…>.json``。

逐次ループ宣言: 候補 × 指標 × 本数(候補は数十)。体の数に比例するループは無い。絶対パスは出力に書かない。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(os.path.abspath(__file__)).parent

SCHEMA = "shibuya.tools.instruments/hm_gauge/1"
#: 候補の欄(離散の seed の組だけ=係数は持たない)。
CANDIDATE_KEYS: tuple[str, ...] = ("population_seed", "environment_seed")
#: 非含意度の閾値(Pukelsheim の 3σ=R-117 §3-1)・束ね(2 番目に大きい値=mogp-emulator の既定)。
THRESHOLD = 3.0
COMBINE = "second_max"
SIDE_CALIBRATION = "calibration"


def _read_guard() -> Any:
    name = "read_guard_hm"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / "read_guard.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def check_path(path: str | Path) -> None:
    """入力の道筋に封印と検証側の語があれば開く前に落とす(``read_guard.deny_hit``=小文字にそろえて照らし、当たらなければ
    実体の道筋(つなぎ・symlink を解いた形)でも照らす=〔検収 M2〕)。"""
    hit = _read_guard().deny_hit(path)
    if hit:
        raise PermissionError(f"HM の計器は封印と検証側を読まない(道筋に {hit!r})")


def check_candidate(c: Mapping[str, Any]) -> dict[str, int]:
    """候補=離散の seed の組だけ(ほかの欄・整数でない値は ``ValueError``)。"""
    extra = sorted(set(c) - set(CANDIDATE_KEYS))
    if extra:
        raise ValueError(f"HM の候補は離散の seed の組だけ(係数は持たない=10-12 §1-6)。知らない欄 {extra}")
    out = {}
    for k in CANDIDATE_KEYS:
        v = c.get(k)
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"HM の候補の {k} は整数の seed(いま {v!r})")
        out[k] = int(v)
    return out


def check_observations(obs: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    """観測は較正側だけ・分散は 0 以上の有限の数。"""
    out = {}
    for k, o in obs.items():
        if o.get("side") != SIDE_CALIBRATION:
            raise PermissionError(f"HM の観測 {k} は較正側だけ(side={o.get('side')!r}=検証側には触れない)")
        row = {}
        for f in ("z", "var_obs", "var_disc"):
            v = o.get(f)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
                raise ValueError(f"HM の観測 {k}.{f} は有限の数")
            if f != "z" and float(v) < 0:
                raise ValueError(f"HM の観測 {k}.{f} は 0 以上")
            row[f] = float(v)
        out[str(k)] = row
    return out


def implausibility(z: float, mean: float, var_ens: float, var_obs: float, var_disc: float) -> float:
    """I = |z − 平均| / √(Var_ens + Var_obs + Var_disc)(分母 0 は ``ValueError``)。"""
    den = float(var_ens) + float(var_obs) + float(var_disc)
    if not den > 0.0:
        raise ValueError("非含意度の分母(アンサンブル+観測+モデルの食い違いの分散)が 0")
    return abs(float(z) - float(mean)) / math.sqrt(den)


def combine(values: Sequence[float]) -> tuple[float, str]:
    """束ね: 2 つ以上なら 2 番目に大きい値・1 つなら最大。"""
    v = sorted((float(x) for x in values), reverse=True)
    if not v:
        raise ValueError("指標が無い")
    return (v[1], "second_max") if len(v) >= 2 else (v[0], "max")


def judge(candidates: Sequence[Mapping[str, Any]], runs: Sequence[Sequence[Mapping[str, float]]],
          observations: Mapping[str, Mapping[str, Any]], *, threshold: float = THRESHOLD) -> dict[str, Any]:
    """候補ごとの非含意度と残す/除く(器だけ=候補の初期状態は 4-1 の後)。"""
    if len(candidates) != len(runs):
        raise ValueError("candidates と runs の長さが違う")
    obs = check_observations(observations)
    rows = []
    for c, rs in zip(candidates, runs):  # 逐次ループ宣言: 候補の数ぶん
        cand = check_candidate(c)
        if not rs:
            raise ValueError(f"候補 {cand} の本数が 0")
        per = {}
        for k, o in obs.items():
            xs = [float(r[k]) for r in rs]
            n = len(xs)
            mean = sum(xs) / n
            var = sum((x - mean) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
            per[k] = {"mean": mean, "var_ens": var, "runs": n,
                      "I": implausibility(o["z"], mean, var, o["var_obs"], o["var_disc"])}
        vals = [per[k]["I"] for k in per]
        comb, how = combine(vals)
        rows.append({"candidate": cand, "metrics": per, "I_M": max(vals), "I_combined": comb, "combine": how,
                     "plausible": comb <= float(threshold)})
    kept = [r["candidate"] for r in rows if r["plausible"]]
    return {"schema": SCHEMA, "threshold": float(threshold), "combine": COMBINE, "candidate_keys": list(CANDIDATE_KEYS),
            "observations": obs, "rows": rows, "kept": kept, "n_candidates": len(rows), "n_kept": len(kept),
            "warning": None if kept else "残りが空=シミュレータかデータの問題の強い警告(Vernon ら)",
            "note": ("器だけ(候補の初期状態は第 4 期 4-1 の後)。代理モデル無しの直接の判定・1 本の候補は Var_ens=0(宣言)。"
                     "安い層(mock・古典・判断モデル)で回し、層の差はモデルの食い違いの分散に入れる(R-117 §3-5)")}


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("judge")
    sp.add_argument("--input", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--threshold", type=float, default=THRESHOLD)
    args = ap.parse_args(argv)
    check_path(args.input)
    doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
    out = judge(doc["candidates"], doc["runs"], doc["observations"], threshold=args.threshold)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"[hm] 候補 {out['n_candidates']}・残り {out['n_kept']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
