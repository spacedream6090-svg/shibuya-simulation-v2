# -*- coding: utf-8 -*-
"""format_role_rates.py — **書式エラー率・役割語率・未定義率**(C6 受入表 §9.1 の形)。

正典
- 実装計画書 §9.1 C6 受入「指標B・ablation①・L4/L6予算・T3-T9全合格・**書式エラー率 ≤0.10
  (温度0.7・実LLM・n≥59)**・**役割語率の再測**」。
- 知覚契約書 §10.3「出力の固定2行形 … B11実測=8B INT8で書式エラー0(n=59)→卒業条件達成
  (温度0)。**Phase 2 実データ・温度0.7で再確認** / 卒業条件 ≤0.10」。
- 行動契約書 §2.2 の**役割語**(接客・補充・開閉店・価格改定・発車・停車・放送・遅延報告・
  計画改訂・指示・並ぶ・撮影)。実装計画書 §8 の C4 注記「営業時間 … フォールバック
  (conf 0.5)が 99.7%(**mock は役割語を出さない= C6 の実 LLM で再測**)」。
- **書式エラー率は実効を主・厳密を併記**(親判断 **D-28**)。実効=C6 で足したラベル別名を
  許した ``ParseResult.format_ok``、厳密=C6 以前の別名表だけで見た ``strict_format_ok``。
  未定義行動率は**段0 辞書(``llm.undefined.map_synonym``)で救えなかった分**だけを数える。

入力
    ``--tape <録画テープ>``(1呼=1行 Parquet)。テープが無ければ ``--endpoints`` を渡して
    スモークを 1 本回してから集計する。``--responses <jsonl>``(``text`` 欄)も受ける。

親がサーバーで叩く例::

    # 既にあるスモークのテープから集計
    python tools/c6/format_role_rates.py --tape runs/smoke_20260909/tape --out docs/bench/c6

    # スモークを回してから集計(温度 0.7 = 受入条件)
    python tools/c6/format_role_rates.py \
        --endpoints http://127.0.0.1:8000,http://127.0.0.1:8001 \
        --world data/world/v2 --agents 5000 --ticks 24 --temperature 0.7 --out docs/bench/c6
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c6lib  # noqa: E402

#: 受入表で名指しされている役割語(§9.1 の「補充/開閉店/発車/停車/指示」)。
WATCHED_ROLE_WORDS: tuple[str, ...] = ("補充", "開閉店", "発車", "停車", "指示")


def texts_from_tape(path: str | Path) -> list[str]:
    from shibuya.engine.tape import Tape

    # D-58: 繰り延べ行(応答空)は書式エラー率の分母に入れない
    return [str(r.response) for r in Tape(path).rows() if not r.deferred]


def texts_from_jsonl(path: str | Path) -> list[str]:
    out: list[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(str(json.loads(line).get("text", "")))
    return out


def _verdict(ok: bool, n: int) -> str:
    if n < c6lib.FORMAT_ERROR_MIN_N:
        return "標本不足"
    return "合格" if ok else "不合格"


def acceptance_rows(score: dict, diagnostics_day: dict | None) -> list[list]:
    """§9.1 C6 受入表の行(判定つき)。**純関数**。

    書式エラー率は**実効を主・厳密を併記**(親判断 D-28)。
    """
    n = int(score["n"])
    gate = f"≤ {c6lib.FORMAT_ERROR_MAX}(n≥{c6lib.FORMAT_ERROR_MIN_N})"
    rows = [
        [
            "書式エラー率(実効・主)",
            f"{score['format_error_rate']:.4f}",
            gate,
            f"n={n} CI95 [{score['format_error_ci95'][0]:.4f}, {score['format_error_ci95'][1]:.4f}]",
            _verdict(bool(score["format_error_ok"]), n),
        ],
        [
            "書式エラー率(厳密・併記)",
            f"{score.get('format_error_rate_strict', float('nan')):.4f}",
            gate,
            "C6 別名を許さない判定(B11 と地続き)",
            _verdict(bool(score.get("format_error_ok_strict", False)), n),
        ],
        ["ラベル別名率", f"{score.get('alias_used_rate', 0.0):.4f}", "—",
         " ".join(f"{k}:{v}" for k, v in sorted(score.get("alias_surfaces", {}).items())) or "なし",
         "—"],
        ["厳密2行形率", f"{score['strict_two_line_rate']:.4f}", "—", "", "—"],
        ["役割語率(全12語)", f"{score['role_action_rate']:.4f}", "—", "再測(mock は 0)", "—"],
        ["未定義行動率(段0 辞書で救えず)", f"{score['undefined_rate']:.4f}", "—",
         "未定義行動5段へ", "—"],
        ["段0 辞書で救えた率", f"{score.get('dictionary_mapped_rate', 0.0):.4f}", "—",
         f"{int(score.get('dictionary_mapped', 0))} 件", "—"],
    ]
    for w in WATCHED_ROLE_WORDS:
        k = int(score["role_action_counts"].get(w, 0))
        rows.append([f"　役割語 {w}", f"{(k / n if n else 0.0):.4f}", "—", f"{k} 件", "—"])
    if diagnostics_day:
        for col in ("deferred", "promoted", "degraded", "suppressed"):
            rows.append([f"診断行 {col}", f"{diagnostics_day.get(col, 0.0):,.0f}", "存在", "T9", "—"])
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = c6lib.common_parser("書式エラー率・役割語率・未定義率(C6 受入表)")
    ap.add_argument("--tape", default="", help="録画テープのディレクトリ")
    ap.add_argument("--responses", default="", help="応答 jsonl(text 欄)")
    ap.add_argument("--temperature", type=float, default=0.7, help="受入条件は温度 0.7")
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--mode", default="smoke")
    args = ap.parse_args(argv)

    diagnostics_day: dict | None = None
    source = ""
    if args.tape:
        texts = texts_from_tape(args.tape)
        source = f"tape={args.tape}"
    elif args.responses:
        texts = texts_from_jsonl(args.responses)
        source = f"responses={args.responses}"
    else:
        endpoints = c6lib.endpoints_of(args)
        tape_dir = Path(args.out) / "format_role_tape"
        client = (
            c6lib.build_fleet_client(
                endpoints,
                model=args.model,
                mode=args.mode,
                run_id=args.run_id,
                run_seed=args.seed,
                temperature=args.temperature,
                max_tokens=args.max_tokens,
            )
            if endpoints
            else None
        )
        try:
            res, route = c6lib.run_smoke(
                n_agents=args.agents,
                seed=args.seed,
                ticks=args.ticks,
                world_dir=c6lib.world_dir_of(args),
                tape_path=tape_dir,
                fleet=client,
            )
        finally:
            if client is not None:
                client.close()
        texts = texts_from_tape(tape_dir)
        diagnostics_day = {k: float(v) for k, v in res.diagnostics_day().items()}
        source = f"smoke({route}) tape={tape_dir}"

    score = c6lib.score_texts(texts)
    payload = {
        "test": "format_role_rates",
        "source": source,
        "temperature": args.temperature,
        "score": score,
        "watched_role_words": list(WATCHED_ROLE_WORDS),
        "diagnostics_day": diagnostics_day,
    }
    md = "\n".join(
        [
            "# C6 受入: 書式エラー率・役割語率・未定義率",
            "",
            f"- 入力: {source} / 温度 {args.temperature} / n={score['n']:,}",
            "",
            c6lib.markdown_table(
                ["指標", "値", "受入", "備考", "判定"], acceptance_rows(score, diagnostics_day)
            ),
            "",
            "## 行動語の分布",
            "",
            c6lib.markdown_table(
                ["行動語", "件数", "割合"],
                [
                    [k, v, f"{v / max(1, score['n']):.4f}"]
                    for k, v in sorted(
                        score["action_counts"].items(), key=lambda kv: (-kv[1], kv[0])
                    )
                ],
            ),
        ]
    )
    paths = c6lib.write_outputs(args.out, "format_role_rates", payload, md)
    print(json.dumps({"score": {k: score[k] for k in (
        "n", "format_error_rate", "format_error_rate_strict", "format_error_ok",
        "alias_used_rate", "role_action_rate", "undefined_rate", "dictionary_mapped_rate",
    )}, "out": paths}, ensure_ascii=False))
    return 0 if score["format_error_rate"] <= c6lib.FORMAT_ERROR_MAX else 1


if __name__ == "__main__":
    raise SystemExit(main())
