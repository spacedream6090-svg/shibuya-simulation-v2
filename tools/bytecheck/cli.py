# -*- coding: utf-8 -*-
"""bytecheck.cli — byte-check の入口(``python tools/bytecheck/cli.py {run,side,compare,one} …``・リポの根で)。

版上げのときの 1 行(README.md):

    python tools/bytecheck/cli.py run --work C:\\bc<N> --out-dir <記録の置き場> --jobs 6

終了コード: 0=全部同じ・1=動いた欄がある・2=誤り(引数・ランの誤り・写しの木の不足・読んだ src の違い・条件の違い・
つなぎを外せなかった)。比べるものと比べない欄は README.md の「何を確かめるか」。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if __package__ in (None, ""):  # pragma: no cover - スクリプトとして実行したとき
    # スクリプトの置き場(tools/bytecheck)を sys.path から外し(configs・tree などの名がほかのモジュールを隠さないように)、
    # tools/ を末尾に足す(先頭に置くと tools の下の名が入れた包みを隠しうる)。
    _here = os.path.normcase(str(Path(__file__).resolve().parent))
    sys.path[:] = [p for p in sys.path if os.path.normcase(os.path.abspath(p or os.curdir)) != _here]
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from bytecheck import check as K  # noqa: E402
from bytecheck import configs as C  # noqa: E402


def _common(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--world", default="data/world/v2", help="世界資産の置き場(道具のリポの根からの相対)")
    sp.add_argument("--agents", type=int, default=5_000)
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--kw", default="", help="構成の引数に足す JSON(旧値の再現の切替口を渡す口・10e と同じ)")


def _set_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--set", dest="set_name", default="all19", choices=sorted(C.SETS),
                    help="構成の組(all19=19 構成・parent4=親の 4 構成・arms=腕 on の 2 構成と 7 変数)")
    sp.add_argument("--only", default="", help="構成の名をカンマで(組の並びの代わり)")
    sp.add_argument("--jobs", type=int, default=4, help="同時に回すランの数")


def build_parser() -> argparse.ArgumentParser:
    """引数の解析器。"""
    ap = argparse.ArgumentParser(prog="tools/bytecheck/cli.py", description="byte-check(決定論の確かめ)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("run", help="基準の commit の写しと比べる側の src を 1 回で比べる")
    _common(sp)
    _set_args(sp)
    sp.add_argument("--base", default="HEAD", help="基準の commit(既定 HEAD)")
    sp.add_argument("--src", default="", help="比べる側の src(既定は道具のリポ=作業木の src)")
    sp.add_argument("--work", required=True, help="作業の置き場(短い道筋・空か無いこと。写しの木とテープが残る)")
    sp.add_argument("--out-dir", required=True, help="side 2 本と compare を書く置き場")
    sp.add_argument("--label", default="work", help="比べる側の名")
    sp.add_argument("--extra-path", action="append", default=[], help="写しの木へ足して写す追跡ファイル(古い基準の錨など)")
    sp.add_argument("--inherit-env", action="store_true", help="呼び手の SHIBUYA_ の変数をそのまま両側に渡す")
    sp.add_argument("--note", default="")

    sp = sub.add_parser("side", help="片側の構成を回して side の JSON を書く")
    _common(sp)
    _set_args(sp)
    sp.add_argument("--src", default="", help="読む src(既定は道具のリポ=作業木の src)")
    sp.add_argument("--label", required=True)
    sp.add_argument("--scratch", required=True, help="テープの置き場")
    sp.add_argument("--out", required=True)
    sp.add_argument("--drop-behavior-item", default="")
    sp.add_argument("--multiset-items", default="")
    sp.add_argument("--allow-incomplete-tree", action="store_true")
    sp.add_argument("--commit", default="", help="side の JSON に書く commit(記録だけ)")
    sp.add_argument("--extra-path", action="append", default=[],
                    help="写しの一覧に足す追跡ファイル(run の --extra-path と同じ=開いても一覧に無いとは数えない)")

    sp = sub.add_parser("compare", help="side の JSON 2 本を比べる")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--note", default="")
    sp.add_argument("--out", required=True)
    sp.add_argument("--strict", action="store_true",
                    help="新しい欄や条件の欄が記録に無いことも誤り(2)にする(run は常に strict)")

    sp = sub.add_parser("one", help="1 構成を回す(side が呼ぶ)")
    _common(sp)
    sp.add_argument("--config", required=True, choices=list(C.configs()))
    sp.add_argument("--tape", required=True)
    sp.add_argument("--drop-behavior-item", default="")
    sp.add_argument("--multiset-items", default="")
    sp.add_argument("--expect-src", default="")
    sp.add_argument("--scratch", default="")
    return ap


def main(argv: list[str] | None = None) -> int:
    """入口。終了コード 0 同じ / 1 動いた / 2 誤り。"""
    for stream in (sys.stdout, sys.stderr):  # 端末の文字コードで書けない字で落ちない
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    a = build_parser().parse_args(argv)
    try:
        if a.cmd == "run":
            return K.run(work=a.work, out_dir=a.out_dir, base=a.base, src=a.src, set_name=a.set_name, only=a.only,
                         jobs=a.jobs, label=a.label, kw=a.kw, extra_paths=a.extra_path, inherit_env=a.inherit_env,
                         note=a.note, world=a.world, agents=a.agents, seed=a.seed)
        if a.cmd == "side":
            return K.side(label=a.label, scratch=a.scratch, out=a.out, src=a.src, set_name=a.set_name, only=a.only,
                          jobs=a.jobs, kw=a.kw, world=a.world, agents=a.agents, seed=a.seed,
                          drop_behavior_item=a.drop_behavior_item, multiset_items=a.multiset_items,
                          allow_incomplete_tree=a.allow_incomplete_tree, commit=a.commit, extra_paths=a.extra_path)
        if a.cmd == "compare":
            return K.compare(a=a.a, b=a.b, out=a.out, note=a.note, strict=a.strict)
        return K.cmd_one(config=a.config, tape=a.tape, world=a.world, agents=a.agents, seed=a.seed, kw=a.kw,
                         drop_behavior_item=a.drop_behavior_item, multiset_items=a.multiset_items,
                         expect_src=a.expect_src, scratch=a.scratch)
    except Exception as e:  # noqa: BLE001 - 誤りは終了コード 2
        if a.cmd == "one":
            raise
        print(f"誤り: {type(e).__name__}: {e}", file=sys.stderr)
        return K.EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
