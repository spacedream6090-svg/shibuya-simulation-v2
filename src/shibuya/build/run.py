"""build.run — 世界データ構築の通し実行(地理 W0-W6/W11 + 場・境界 W7/W10/W12/W13 +
可視性・影 W8/W9 + 被覆指標・凍結・検収 W18/W19/W20)。

    python -m shibuya.build.run --out data/world/v2 [--data data] [--stage W7 ...]

- **実行順と build_hash の順は別**: 実行は ``RUN_ORDER``(W8/W9 は W10/W11 の出力が要るので
  W13 の後・W18-W20 は最後)、``build_hash`` は W 番号順(下記)。
- ``build_manifest.json`` = {stages:[ヘッダ], build_hash}。**全段階**のヘッダを W 番号順
  (W0..W13, W18, W19, W20)に並べ、その順の出力 sha256 を連結した文字列の sha256 が
  ``build_hash``(D-W20 の再構築テスト T1 の対象)。
- ヘッダ・出力に時刻など非決定な値を入れないので、同じ入力からの再構築でバイト一致する。
- ``--stage`` で**一部だけ**走らせたときは ``build_manifest.json`` を書き換えず、
  ``build_manifest.partial.json``(``partial: true`` + 走らせた段階 + 前回のランから
  残っていた段階)を書く(古いヘッダを混ぜた build_hash を正典に置かないため)。
- ゲートが1つでも落ちたら終了コード 1。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .audit import STAGES as AUDIT_STAGES, run as audit_run
from .field import STAGES as FIELD_STAGES, run as field_run
from .geo import STAGES as GEO_STAGES, common as C
from .geo import run as geo_run
from .lang import STAGES as LANG_STAGES, run as lang_run
from .pop import STAGES as POP_STAGES, run as pop_run
from .sched import STAGES as SCHED_STAGES, run as sched_run
from .vis import STAGES as VIS_STAGES, run as vis_run

__all__ = ["ALL_STAGES", "RUN_ORDER", "stage_order", "run_all", "write_build_manifest", "main"]


def stage_order(stages: list[str]) -> list[str]:
    """W 番号の数値順に並べる(W7 → W10 → W11 の順・文字列順ではない)。"""
    return sorted(stages, key=lambda s: int(s[1:]))


#: 全段階(W 番号順)。build_hash はこの順の出力 sha256 連結。
ALL_STAGES: tuple[str, ...] = tuple(
    stage_order([*GEO_STAGES, *FIELD_STAGES, *VIS_STAGES, *LANG_STAGES, *POP_STAGES, *SCHED_STAGES, *AUDIT_STAGES])
)

#: **実行順**(build_hash の順=``ALL_STAGES`` とは別)。
#: W8(可視性)・W9(影)は D-W9 の街路格子=W10 の ``w10_street_points`` と W11 の駅出口を
#: 入力にするので、W 番号は 8/9 でも**実行は W13 の後**。W18-W20 はさらにその後
#: (W18 は全段階のヘッダを、W19/W20 は W18 の出力を読む)。W16(母集団合成)は
#: W2/W4/W6/W11/W12 の出力を読むので、番号順でも実行順でも可視性・影の後に置く。
RUN_ORDER: tuple[str, ...] = (
    *[
        s
        for s in ALL_STAGES
        if s not in VIS_STAGES and s not in AUDIT_STAGES and s not in POP_STAGES and s not in LANG_STAGES and s not in SCHED_STAGES
    ],
    *VIS_STAGES,
    *LANG_STAGES,  # W15 は W8 出力(w8_t1_cell)を読むので VIS の後・W16 の前
    *POP_STAGES,
    *SCHED_STAGES,  # W17 は W16(母集団)・W7(PlanSpec)・W12(時間帯カーブ)を読む
    *AUDIT_STAGES,
)

MANIFEST_NAME = "build_manifest.json"
#: 一部の段階だけを走らせたときの manifest。``build_manifest.json`` は**書かない**
#: (走らせていない段階のヘッダは前回のランの残り=混ぜると build_hash が嘘になる)。
PARTIAL_MANIFEST_NAME = "build_manifest.partial.json"
MANIFEST_SCHEMA = "shibuya.build/build_manifest/1"


def run_all(ctx: C.Ctx, stages: list[str], verbose: bool = True) -> list[C.StageResult]:
    """指定段階を ``RUN_ORDER``(依存順)で実行する。``build_hash`` の順は W 番号順で別。"""
    want = set(stages)
    results: list[C.StageResult] = []
    for st in [s for s in RUN_ORDER if s in want]:
        if st in GEO_STAGES:
            results.extend(geo_run.run_stages(ctx, [st], verbose=verbose))
        elif st in FIELD_STAGES:
            results.extend(field_run.run_stages(ctx, [st], verbose=verbose))
        elif st in VIS_STAGES:
            results.extend(vis_run.run_stages(ctx, [st], verbose=verbose))
        elif st in LANG_STAGES:
            results.extend(lang_run.run_stages(ctx, [st], verbose=verbose))
        elif st in POP_STAGES:
            results.extend(pop_run.run_stages(ctx, [st], verbose=verbose))
        elif st in SCHED_STAGES:
            results.extend(sched_run.run_stages(ctx, [st], verbose=verbose))
        else:
            results.extend(audit_run.run_stages(ctx, [st], verbose=verbose))
    return results


def write_build_manifest(
    ctx: C.Ctx, stages_run: list[str] | None = None
) -> dict[str, Any]:
    """out に存在する**全段階**のヘッダから manifest を組む(W 番号順)。

    ``stages_run`` に**このラン**で実際に走らせた段階を渡すと、それが全段階に満たないときは
    ``build_manifest.json`` を上書きせず ``build_manifest.partial.json`` を書く
    (``partial: true`` + ``stages_run`` + 前回のランから残っていたヘッダの一覧)。
    ``None``(既定)は「全段階を走らせた」の意。
    """
    headers: list[dict[str, Any]] = []
    digests: list[str] = []
    for st in ALL_STAGES:
        path = ctx.out / f"{st}.header.json"
        if not path.exists():
            continue
        header = C.load_json(path)
        headers.append(header)
        digests.extend(o["sha256"] for o in header["outputs"])
    ran = None if stages_run is None else stage_order(list(dict.fromkeys(stages_run)))
    partial = ran is not None and set(ran) != set(ALL_STAGES)
    manifest: dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "stage_order": [h["stage"] for h in headers],
        "stages": headers,
        "build_hash": C.sha256_bytes("".join(digests).encode("utf-8")),
    }
    if partial:
        assert ran is not None
        manifest["partial"] = True
        manifest["stages_run"] = ran
        manifest["stages_from_previous_runs"] = [
            h["stage"] for h in headers if h["stage"] not in set(ran)
        ]
        manifest["partial_note"] = (
            "一部の段階だけを走らせたラン。build_hash は out に残っているヘッダ"
            "(前回のランの分を含む)から組んだ値であり、通しの再構築で得られる値と"
            "一致する保証はない。正典の build_manifest.json は全段階を走らせたときだけ書く。"
        )
    path = ctx.out / (PARTIAL_MANIFEST_NAME if partial else MANIFEST_NAME)
    path.write_bytes(C.canonical_json_bytes(manifest) + b"\n")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.run")
    ap.add_argument("--out", required=True, type=Path, help="出力ディレクトリ(例 data/world/v2)")
    ap.add_argument("--data", type=Path, default=Path("data"), help="入力データ根(既定 data)")
    ap.add_argument(
        "--stage",
        action="append",
        choices=list(ALL_STAGES),
        help="実行する段階(繰り返し可・既定=全段階)",
    )
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    stages = [s for s in ALL_STAGES if args.stage is None or s in args.stage]
    ctx = C.Ctx(data=args.data.resolve(), out=args.out.resolve())
    if not ctx.data.exists():
        print(f"入力データ根が無い: {ctx.data}", file=sys.stderr)
        return 2

    ctx.out.mkdir(parents=True, exist_ok=True)
    results = run_all(ctx, stages, verbose=not args.quiet)
    manifest = write_build_manifest(ctx, stages_run=stages)
    ok = geo_run.print_gate_table(results)
    name = PARTIAL_MANIFEST_NAME if manifest.get("partial") else MANIFEST_NAME
    print(f"build_hash = {manifest['build_hash']}")
    print(f"stages     = {','.join(manifest['stage_order'])}")
    print(f"manifest   = {name}")
    if manifest.get("partial"):
        print(f"stages_run = {','.join(manifest['stages_run'])}(部分ラン=build_manifest.json は更新しない)")
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
