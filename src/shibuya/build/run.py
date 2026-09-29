"""build.run — 世界データ構築の通し実行(地理 W0-W6/W11 + 場・境界 W7/W10/W12/W13 +
可視性・影 W8/W9 + 被覆指標・凍結・検収 W18/W19/W20)。

    python -m shibuya.build.run --out data/world/v2 [--data data] [--stage W7 ...] [--keep-stage W17 ...]

- **実行順と build_hash の順は別**: 実行は ``RUN_ORDER``(W8/W9 は W10/W11 の出力が要るので
  W13 の後・W18-W20 は最後)、``build_hash`` は W 番号順(下記)。
- ``build_manifest.json`` = {stages:[ヘッダ], build_hash}。**全段階**のヘッダを W 番号順
  (W0..W13, W18, W19, W20)に並べ、その順の出力 sha256 を連結した文字列の sha256 が
  ``build_hash``(D-W20 の再構築テスト T1 の対象)。
- ヘッダ・出力に時刻など非決定な値を入れないので、同じ入力からの再構築でバイト一致する。
- ``--stage`` で**一部だけ**走らせたときは ``build_manifest.json`` を書き換えず、
  ``build_manifest.partial.json``(``partial: true`` + 走らせた段階 + 前回のランから
  残っていた段階)を書く(古いヘッダを混ぜた build_hash を正典に置かないため)。
- **凍結段を保つ口** ``--keep-stage <段>``(複数可・第281 親決定 Q2 (b)): その段は再構築せず、
  ディスク上の出力と既存ヘッダをそのまま採る(ヘッダが主張する出力が在り sha256 が一致することを
  先に確かめ、合わなければ何も走らせずに終了コード 2)。走らせた段+保った段で全段階がそろえば
  ``build_manifest.json`` を**正典として**書き(partial にしない)、``kept: [...]`` を記録する。
  用途= W17 v2(``build/sched/trial.py --promote`` で昇格した資産)。W17 段(``w17_schedule.run``)は
  ``w17_responses*.jsonl``(v1 の応答)を取り込み直すので、``build.run`` では v2 を再現できない。
- **安全弁**(:data:`PROTECTED_OUTPUTS`): 走らせる段の出力の md5 が昇格版と一致するときは、
  ``--stage <その段>`` を**明示しない限り**上書きを拒否し、何も走らせずに終了コード 2。
  W17 を再構築するのは ``--stage W17`` を明示したときだけ。
- ゲートが1つでも落ちたら終了コード 1。
"""

from __future__ import annotations

import argparse
import hashlib
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

__all__ = [
    "ALL_STAGES",
    "RUN_ORDER",
    "PROTECTED_OUTPUTS",
    "stage_order",
    "run_all",
    "write_build_manifest",
    "verify_kept_stage",
    "protected_output_hits",
    "main",
]


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

#: 安全弁: 段 → {出力ファイル名: 昇格版の md5 の先頭(16 進)}。走らせる段のディスク上の出力が
#: これに一致したら、``--stage <段>`` の明示が無い限り上書きを拒否する。
#: W17 v2 = 本番 第 2 回・第168 昇格(``tests/engine/test_presence_executor.py`` の ``W17_GOLDEN`` の鍵)。
PROTECTED_OUTPUTS: dict[str, dict[str, tuple[str, ...]]] = {
    "W17": {"w17_schedule.parquet": ("3113e9ba7abb",)},
}


class KeptStageError(RuntimeError):
    """``--keep-stage`` で保つ段のヘッダ・出力がディスク上で揃っていない。"""


def _md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_kept_stage(out: Path, stage: str) -> dict[str, Any]:
    """保つ段のヘッダを読み、ヘッダが主張する出力が在って sha256 が一致することを確かめる。

    出力の ``path`` は ``out`` からの相対(通常)か絶対(W17 v2 の段 2 プロンプトのように隔離先に
    残っている出力)。**書き換えない**。合わなければ :class:`KeptStageError`。
    """
    path = Path(out) / f"{stage}.header.json"
    if not path.exists():
        raise KeptStageError(f"{stage}: ヘッダが無い({path.name})")
    header = C.load_json(path)
    if header.get("stage") != stage:
        raise KeptStageError(f"{stage}: ヘッダの stage が {header.get('stage')!r}")
    for o in header.get("outputs", []):
        op = Path(str(o["path"]))
        p = op if op.is_absolute() else Path(out) / op
        if not p.exists():
            raise KeptStageError(f"{stage}: ヘッダの出力が無い({op.name})")
        if C.sha256_file(p) != o["sha256"]:
            raise KeptStageError(f"{stage}: 出力の sha256 がヘッダと違う({op.name})")
    return header


def protected_output_hits(out: Path, stages: list[str], explicit: set[str]) -> list[str]:
    """走らせる段のうち、昇格版の出力を上書きしてしまうもの(``--stage`` の明示が無いもの)。"""
    hits: list[str] = []
    for st in stages:
        if st in explicit or st not in PROTECTED_OUTPUTS:
            continue
        for name, prefixes in PROTECTED_OUTPUTS[st].items():
            p = Path(out) / name
            if not p.exists():
                continue
            md5 = _md5_file(p)
            if any(md5.startswith(x) for x in prefixes):
                hits.append(f"{st}: {name}(md5 {md5[:12]}=昇格版)")
    return hits


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
    ctx: C.Ctx, stages_run: list[str] | None = None, kept: list[str] | None = None
) -> dict[str, Any]:
    """out に存在する**全段階**のヘッダから manifest を組む(W 番号順)。

    ``stages_run`` に**このラン**で実際に走らせた段階を渡すと、それが全段階に満たないときは
    ``build_manifest.json`` を上書きせず ``build_manifest.partial.json`` を書く
    (``partial: true`` + ``stages_run`` + 前回のランから残っていたヘッダの一覧)。
    ``None``(既定)は「全段階を走らせた」の意。

    ``kept`` = ``--keep-stage`` で**意図して保った**段(:func:`verify_kept_stage` 済み)。
    走らせた段+保った段で全段階がそろえば正典(``build_manifest.json``)を書き、
    ``kept`` を manifest に記録する。
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
    kept_l = stage_order(list(dict.fromkeys(kept or [])))
    partial = ran is not None and (set(ran) | set(kept_l)) != set(ALL_STAGES)
    manifest: dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "stage_order": [h["stage"] for h in headers],
        "stages": headers,
        "build_hash": C.sha256_bytes("".join(digests).encode("utf-8")),
    }
    if kept_l:
        manifest["kept"] = kept_l
        manifest["kept_note"] = (
            "再構築せず、ディスク上の出力と既存ヘッダをそのまま採った段(--keep-stage)。"
            "出力の存在と sha256 はヘッダと突き合わせ済み。"
        )
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
    ap.add_argument(
        "--keep-stage",
        action="append",
        choices=list(ALL_STAGES),
        help="再構築せずディスク上の出力と既存ヘッダを採る段階(繰り返し可・例 W17)",
    )
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    explicit = set(args.stage or [])
    keep = stage_order(list(dict.fromkeys(args.keep_stage or [])))
    both = sorted(explicit & set(keep))
    if both:
        print(f"--stage と --keep-stage の両方に指定された段階: {','.join(both)}", file=sys.stderr)
        return 2
    stages = [
        s for s in ALL_STAGES if (args.stage is None or s in args.stage) and s not in keep
    ]
    ctx = C.Ctx(data=args.data.resolve(), out=args.out.resolve())
    if not ctx.data.exists():
        print(f"入力データ根が無い: {ctx.data}", file=sys.stderr)
        return 2
    for st in keep:  # 何も走らせる前に確かめる
        try:
            verify_kept_stage(ctx.out, st)
        except KeptStageError as e:
            print(f"--keep-stage を満たせない: {e}", file=sys.stderr)
            return 2
    hits = protected_output_hits(ctx.out, stages, explicit)
    if hits:
        print(
            "昇格版の出力を上書きするので止めた(何も走らせていない): " + " / ".join(hits)
            + "。保つなら --keep-stage、作り直すなら --stage でその段階を明示する。",
            file=sys.stderr,
        )
        return 2

    ctx.out.mkdir(parents=True, exist_ok=True)
    results = run_all(ctx, stages, verbose=not args.quiet)
    manifest = write_build_manifest(ctx, stages_run=stages, kept=keep)
    ok = geo_run.print_gate_table(results)
    name = PARTIAL_MANIFEST_NAME if manifest.get("partial") else MANIFEST_NAME
    print(f"build_hash = {manifest['build_hash']}")
    print(f"stages     = {','.join(manifest['stage_order'])}")
    print(f"manifest   = {name}")
    if keep:
        print(f"kept       = {','.join(keep)}(再構築せず既存の出力とヘッダを採った)")
    if manifest.get("partial"):
        print(f"stages_run = {','.join(manifest['stages_run'])}(部分ラン=build_manifest.json は更新しない)")
    return 0 if ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
