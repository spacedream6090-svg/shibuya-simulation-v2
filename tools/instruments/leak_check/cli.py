# -*- coding: utf-8 -*-
"""leak_check.cli — 漏洩の検査を 1 回通して ``result.json``(集計だけ)と ``table.md`` を書く。

使い方(``PYTHONPATH`` に ``src`` と ``tools/instruments``)::

    python -m leak_check.cli run --type 1 --backend mock --out-dir <出力の置き場>
    python -m leak_check.cli run --type 2 --backend vllm --model <served-model-name> --port 8000 --out-dir …
    python -m leak_check.cli run --type 4 --backend vllm --model … --recall-refs <参照の JSONL> --out-dir …
    python -m leak_check.cli summary <result.json> <result.json> …   # 運用規則 9 の欄の 1 行をまとめる(同じモデル)

vLLM の口は 127.0.0.1 に固定(``--port`` だけ)。API key は環境変数(既定 ``VLLM_API_KEY``)。記録には絶対の道筋を
書かない(入力のファイルは名だけ)。型に関係の無い引数(型 ② に ``--expect-md5`` など)は rc 2 で止める。
書く前に、記録の文に絶対の道筋の形が無いことを確かめる(あれば止まる)。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from leak_check import run as R
from leak_check import score as SC
from leak_check.backends import DEFAULT_KEY_ENV, DEFAULT_PORT, make_backend

RESULT_NAME: Final[str] = "result.json"
TABLE_NAME: Final[str] = "table.md"
#: 絶対の道筋の形(Windows のドライブ・UNC・POSIX のホーム)。
ABS_PATH: Final[re.Pattern[str]] = re.compile(r"(?i)(?<![A-Za-z])[A-Z]:[\\/]|\\\\[^\\\s]+\\|/(?:Users|home)/")


#: 型 ① (b) の混ぜる順の既定の種。
DEFAULT_SEED: Final[str] = "leak"
#: 型に関係する引数(ほかの型に渡すと rc 2=検収 L2)。既定は None(渡したかを見分ける)。
TYPE_ONLY_ARGS: Final[Mapping[str, frozenset[int]]] = {
    "real_events": frozenset({1}), "model_cutoff": frozenset({1}), "seed": frozenset({1}),
    "min_mass": frozenset({2}),
    "recall_refs": frozenset({4}), "prefix_chars": frozenset({4}), "cont_chars": frozenset({4}),
    "expect_md5": frozenset({1, 4}),
}


class AbsolutePathInRecord(ValueError):
    """記録の文に絶対の道筋の形がある。"""


def check_no_abs_path(text: str) -> None:
    if ABS_PATH.search(text):
        raise AbsolutePathInRecord("記録に絶対の道筋の形がある(書かない)")


def run_once(a: argparse.Namespace) -> dict[str, Any]:
    backend = make_backend(a.backend, model=a.model, port=a.port, key_env=a.key_env, seed=a.mock_seed,
                           model_version=a.model_version)
    if a.type == 1:
        return R.run_type1(backend, real_events=a.real_events, expected_md5=a.expect_md5,
                           seed=DEFAULT_SEED if a.seed is None else a.seed, limit=a.limit, model_cutoff=a.model_cutoff)
    if a.type == 2:
        return R.run_type2(backend, limit=a.limit, min_mass=SC.MIN_MASS if a.min_mass is None else a.min_mass)
    return R.run_type4(backend, recall_refs=a.recall_refs, expected_md5=a.expect_md5,
                       prefix_chars=R.DEFAULT_PREFIX_CHARS if a.prefix_chars is None else a.prefix_chars,
                       cont_chars=R.DEFAULT_CONT_CHARS if a.cont_chars is None else a.cont_chars, limit=a.limit)


def write_outputs(res: Mapping[str, Any], out_dir: Path) -> tuple[Path, Path]:
    js = json.dumps(res, ensure_ascii=False, indent=1, sort_keys=False) + "\n"
    md = R.to_markdown(res)
    check_no_abs_path(js)
    check_no_abs_path(md)
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    (d / RESULT_NAME).write_bytes(js.encode("utf-8"))
    (d / TABLE_NAME).write_bytes(md.encode("utf-8"))
    return d / RESULT_NAME, d / TABLE_NAME


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="leak_check", description="データ漏洩の検査(型 ①②④)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="1 つの型を 1 回通す")
    r.add_argument("--type", type=int, choices=(1, 2, 4), required=True)
    r.add_argument("--backend", choices=("mock", "vllm"), default="mock")
    r.add_argument("--out-dir", type=Path, required=True)
    r.add_argument("--model", default="", help="vLLM の served-model-name(vllm では必須)")
    r.add_argument("--model-version", default="", help="モデルの版(重みの revision・sha など)=台帳の 1 行の頭に付ける")
    r.add_argument("--model-cutoff", default=None, help="型 ①: モデルの学習の締め切り(YYYY-MM か YYYY-MM-DD・任意)")
    r.add_argument("--port", type=int, default=DEFAULT_PORT, help="vLLM の口(127.0.0.1 に固定・1〜65535)")
    r.add_argument("--key-env", default=DEFAULT_KEY_ENV, help="API key を読む環境変数の名")
    r.add_argument("--mock-seed", default="leak-mock")
    r.add_argument("--seed", default=None, help=f"型 ①: (b) の混ぜる順の種(既定 {DEFAULT_SEED})")
    r.add_argument("--limit", type=int, default=None, help="試走: 各集合の先頭 N 件だけ(1 以上)")
    r.add_argument("--real-events", type=Path, default=None, help="型 ①: 実在の出来事の JSONL(既定 data/leak_check/)")
    r.add_argument("--recall-refs", type=Path, default=None, help="型 ④: 参照の JSONL(既定 data/leak_check/)")
    r.add_argument("--expect-md5", default=None, help="型 ①・④: 入力の JSONL の md5(違うか、ファイルが無ければ止まる)")
    r.add_argument("--prefix-chars", type=int, default=None, help=f"型 ④: 冒頭の字数(正・既定 {R.DEFAULT_PREFIX_CHARS})")
    r.add_argument("--cont-chars", type=int, default=None, help=f"型 ④: 続きの字数(正・既定 {R.DEFAULT_CONT_CHARS})")
    r.add_argument("--min-mass", type=float, default=None,
                   help="型 ②: 番号に乗った確率の和の下限(これより小さければ本文の番号)")
    s = sub.add_parser("summary", help="result.json をまとめて運用規則 9 の 1 行を出す(同じモデルだけ)")
    s.add_argument("results", nargs="+", type=Path)
    return ap


def check_args(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    """引数の検査(合わなければ分かる文で rc 2)。"""
    for dest, types in TYPE_ONLY_ARGS.items():
        if getattr(a, dest) is not None and a.type not in types:
            flag = "--" + dest.replace("_", "-")
            ap.error(f"{flag} は型 {'・'.join(str(t) for t in sorted(types))} だけの引数(いま型 {a.type})")
    if a.limit is not None and a.limit < 1:
        ap.error("--limit は 1 以上")
    if (a.prefix_chars is not None and a.prefix_chars < 1) or (a.cont_chars is not None and a.cont_chars < 1):
        ap.error("--prefix-chars と --cont-chars は正の整数")
    if not 1 <= a.port <= 65535:
        ap.error("--port は 1〜65535")
    if a.min_mass is not None and not a.min_mass > 0:
        ap.error("--min-mass は正")
    if a.backend == "vllm" and not a.model:
        ap.error("--backend vllm には --model(served-model-name)が要る")
    if a.model_cutoff:
        try:
            R.check_when(a.model_cutoff)
        except R.InputMismatch as exc:
            ap.error(f"--model-cutoff: {exc}")


def main(argv: Sequence[str] | None = None) -> int:
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.cmd == "summary":
        rs = [json.loads(Path(p).read_bytes().decode("utf-8")) for p in a.results]
        try:
            out = R.merge_ledger(rs)
        except ValueError as exc:
            print(f"leak_check: {exc}", file=sys.stderr)
            return 1
        print(out["line"])
        return 0
    check_args(ap, a)
    try:
        res = run_once(a)
    except R.InputMismatch as exc:
        print(f"leak_check: 入力が合わない: {exc}", file=sys.stderr)
        return 1
    write_outputs(res, a.out_dir)
    print(res["ledger_rule9"]["line"])
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
