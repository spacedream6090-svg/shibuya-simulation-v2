"""第 3 期 3-5: 系ごとの指紋(1-0 の ``engine.systems.probe``)を本体の HEAD と作業木で比べる・作業木の 2 つの腕を比べる。

ec21 の道具 [probe_ec21.py](../../ec21/tools/probe_ec21.py)(構成 3 つ=合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3 と
記憶+関係)をそのまま使い、指紋から次を外す(無い側では何もしない):

- 3-5 で足した状態台帳の行 ``BD``(本人の体の層=段の境目の計器と TM5 の予約の列・軸 1 diag・軸 2 discardable=HEAD に無い・
  腕で中身が違う)と、3-2 の行 ``BW``(計算のまとめの窓・diag・discardable=進行役の窓の境目に帰属)。ec21 の道具が外す行(``E``・``EC``・``ATM``・``CR``・``EM``)はそのまま外す。
- 結果の後付けの属性 ``body_layer``(manifest の ``body`` が読む持ち主=HEAD に無い)。

``--body-schedule {sweep,reserve}`` で体の予約の腕を選ぶ(HEAD の写しでは渡さない)。

    PYTHONHASHSEED=0 PYTHONPATH=<HEAD の src の写し> python $D/tools/probe_bd35.py side --label head --out $W/probe_head.json
    PYTHONHASHSEED=0 PYTHONPATH=src python $D/tools/probe_bd35.py side --label sweep --out $W/probe_sweep.json
    PYTHONHASHSEED=0 PYTHONPATH=src python $D/tools/probe_bd35.py side --label reserve --body-schedule reserve \\
        --out $W/probe_reserve.json
    python docs/bench/analysis/wallbounce-1012/vb24/tools/probe_systems_vb24.py --a $W/probe_head.json \\
        --b $W/probe_sweep.json --out $D/probe_head_vs_sweep.json

逐次ループ宣言: 構成の数ぶん(道具)。
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
EC21 = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "ec21" / "tools" / "probe_ec21.py"


def _ec21():  # noqa: ANN202
    spec = importlib.util.spec_from_file_location("probe_ec21", EC21)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["probe_ec21"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    mod.SKIP_ROWS = frozenset(mod.SKIP_ROWS) | {"BD", "BW"}  # 〔rebase〕3-2 の計算のまとめの窓の行 BW も外す(進行役の窓)
    mod.RESULT_EXTRA = tuple(mod.RESULT_EXTRA) + ("body_layer",)
    return mod


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("side")
    sp.add_argument("--label", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--only", default="")
    sp.add_argument("--body-schedule", default="")
    a = ap.parse_args(argv)
    mod = _ec21()
    if a.body_schedule:
        from shibuya.engine import body as B

        B.set_arm(a.body_schedule)
    return mod.cmd_side(argparse.Namespace(label=a.label, out=a.out, only=a.only))


if __name__ == "__main__":
    sys.exit(main())
