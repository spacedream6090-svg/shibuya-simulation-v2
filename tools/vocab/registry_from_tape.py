# -*- coding: utf-8 -*-
"""registry_from_tape — 録画テープ(``calls.parquet``)→ 未定義行動台帳 JSON(D-71 段2 の入力)。

位置づけ
    語彙成長の設計 v0(``docs/design/v2-vocab-growth-design.md``)§2 の**ラン後オフライン**経路。
    ``python -m shibuya.cli --undefined-out PATH`` はこれからのランのための口だが、**既に回した
    ラン**(AB7 seed 1/2 など)は台帳を JSON で残していない。本スクリプトはそのテープから
    **同じ JSON** を再構成する(``shibuya.cli.undefined_registry_payload`` を共有=形を 2 つ持たない)。

再構成の忠実さ(何を再利用し、何が違うか)
- 生表層の抽出は ``llm.parser.parse_two_line``、段0 写像は ``llm.UndefinedActionRegistry.observe``
  (=内部で ``map_synonym``)。**本番の ``engine.llm_bridge`` と同じ条件**
  (``ParseResult.action is None`` のときだけ ``observe``)で回すので、語・件数・体数は一致する。
- 分母に入れない行: ``deferred=1``(D-58 の繰り延べ行=応答が空)。
- **段2 は起こさない**(``adjudicator=None``)。裁定は ``tools/vocab/adjudicate.py`` の仕事。
- ラン中の台帳には**無い**情報として、テープの共有ブロック([B2 場所])から
  **セル ID** を復元して付ける(``cell_source: "prompt_block"``)。被覆順位
  (体数×セル数×時間帯数)の「セル数」はここでしか作れない。

expedient(本スクリプト分)
- セル ID の抽出は正規表現 ``現在地はセル(…)``。正典の文面は
  ``perception/templates.py`` の ``"B2.place"``=「[B2 場所] 現在地はセル{place_id}({band})です。」。
  **文面が変われば抽出は 0 件になる**(黙って別の値にはならない)ので、0 件のときは
  ``cell_source`` を ``"unavailable"`` にして数を報告する(推測で埋めない)。

使い方::

    python tools/vocab/registry_from_tape.py data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open \\
        --out data/vocab/ab7_open_s1.json

逐次ループ宣言(P4): テープ行数ぶんのループ 1 本(検死・ラン後の 1 回)。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:  # pragma: no cover - 実行時の経路
    sys.path.insert(0, str(REPO_ROOT / "src"))

from shibuya.cli import undefined_registry_payload  # noqa: E402
from shibuya.engine.tape import Tape  # noqa: E402
from shibuya.llm import UndefinedActionRegistry, parse_two_line  # noqa: E402

__all__ = [
    "PLACE_RE",
    "cell_by_block",
    "registry_from_tape",
    "payload_from_tape",
    "main",
]

#: [B2 場所] ブロックからセル ID を取る(**expedient**・正典は perception/templates "B2.place")。
PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")


def cell_by_block(tape: Tape) -> dict[str, str]:
    """``block_id`` → セル ID(取れたブロックだけ)。"""
    out: dict[str, str] = {}
    for block_id, text in zip(
        tape.blocks.column("block_id").to_pylist(), tape.blocks.column("text").to_pylist()
    ):
        m = PLACE_RE.search(str(text))
        if m is not None:
            out[str(block_id)] = m.group(1)
    return out


def registry_from_tape(
    tape: Tape, *, threshold_agents: int | None = None, log_limit: int = 1_000_000
) -> tuple[UndefinedActionRegistry, dict[tuple[int, int], str], dict[str, int]]:
    """テープ → (台帳, ``(agent_id, tick) → セル``, 走査の計数)。

    Args:
        tape: 読み込み済みテープ。
        threshold_agents: 段2 の閾値 N(``None``=台帳の既定 10)。段2 は起こさない
            (``adjudicator=None``)ので、印としてしか効かない。
        log_limit: 記録リングの上限。**既定を大きく取る**(ラン中の 4,096 と違い、ここでは
            全件保持が目的=設計 A (b)「台帳は全件保持」)。溢れれば ``dropped`` に出る。
    """
    kwargs: dict[str, Any] = {"log_limit": int(log_limit)}
    if threshold_agents is not None:
        kwargs["threshold_agents"] = int(threshold_agents)
    reg = UndefinedActionRegistry(adjudicator=None, **kwargs)

    block_cell = cell_by_block(tape)
    cells: dict[tuple[int, int], str] = {}
    counts = {"rows": 0, "deferred": 0, "scored": 0, "action_ok": 0, "observed": 0, "cell_hits": 0}
    for row in tape.rows():
        counts["rows"] += 1
        if int(row.deferred):
            counts["deferred"] += 1
            continue
        counts["scored"] += 1
        parse = parse_two_line(row.response)
        if parse.action is not None:
            counts["action_ok"] += 1
            continue
        counts["observed"] += 1
        reg.observe(parse.raw_action, int(row.agent_id), int(row.tick), str(row.prompt_hash))
        for block_id in row.block_ids:
            cell = block_cell.get(str(block_id))
            if cell is not None:
                cells[(int(row.agent_id), int(row.tick))] = cell
                counts["cell_hits"] += 1
                break
    return reg, cells, counts


def payload_from_tape(
    tape_dir: str | Path, *, threshold_agents: int | None = None, tag: str = ""
) -> dict[str, Any]:
    """``shibuya.cli.undefined_registry_payload`` と**同じ形**の dict を作る。"""
    tape = Tape(tape_dir)
    reg, cells, counts = registry_from_tape(tape, threshold_agents=threshold_agents)
    payload = undefined_registry_payload(reg, source="tape", cells=cells)
    payload["tape"] = {
        # 相対パスのみ(絶対パスを記録に残さない)。リポ外なら名前だけ。
        "dir": _relative(Path(tape_dir)),
        "tag": tag or Path(tape_dir).name,
        "schema_version": tape.schema_version,
        "n_rows": int(len(tape)),
        "scan": counts,
    }
    return payload


def _relative(path: Path) -> str:
    """リポジトリ相対の POSIX 表記(外なら名前だけ)。**絶対パスを書かない**。"""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tape_dir", type=str, help="calls.parquet のあるディレクトリ")
    ap.add_argument("--out", type=str, required=True, help="出力 JSON")
    ap.add_argument("--tag", type=str, default="", help="由来の印(既定=テープのディレクトリ名)")
    ap.add_argument(
        "--threshold-agents", type=int, default=None,
        help="段2 の閾値 N(既定=台帳の 10)。段2 は起こさない(印のみ)",
    )
    args = ap.parse_args(argv)

    payload = payload_from_tape(
        args.tape_dir, threshold_agents=args.threshold_agents, tag=str(args.tag)
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    scan = payload["tape"]["scan"]
    print(
        f"{out.name}: {payload['summary']['n_words']} 語 / "
        f"{payload['summary']['n_records_kept']} 行"
        f"(走査 {scan['rows']:,} 行・繰り延べ {scan['deferred']:,}・語彙一致 {scan['action_ok']:,}"
        f"・セル復元 {payload['cell_source']})"
    )
    for word, agg in list(payload["words"].items())[:10]:
        print(
            f"  {word}: {agg['n_rows']} 行 / {agg['distinct_agents']} 体 / "
            f"{agg['distinct_cells']} セル / {agg['distinct_hours']} 時間帯"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover - スクリプト入口
    raise SystemExit(main())
