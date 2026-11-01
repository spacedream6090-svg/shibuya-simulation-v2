"""1-8b の記録の道具: テープから発話の行と予算の数を数える(読むだけ)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/s8b/tools/speech_tokens.py --tape <テープの置き場> [...]
--out <JSON>``。テープは ``calls.parquet``・``blocks.parquet``(byte-check の side が scratch に書いた物など)。

出す数(テープごと・名は置き場の最後の名だけ=絶対パスは書かない):
- 呼数・出力の欄の指示(``[B6 出力]``)のある呼・届いた発話の行(``[B6 発話]``)の数・応答に ``ひと言:`` のある呼。
- 指示の行と届いた発話の行の推定トークン(文字数 ÷ 2=``perception.channels.estimate_tokens`` と同じ規約)。
- 共有の静的群(B0+B1+B3)の推定トークンの値の種類(1-8b で変わらないことの確かめ=予算 750 の残り)。
- 個体群(B5+B6)の推定トークンの最大・平均と、発話の行のある呼の最大(予算 300)。B6 の推定トークンの最大(枠 80)。
- B6 が枠 80 を超える呼の数と内訳(指示の行だけある呼・届いた発話の行だけある呼・両方ある呼・どちらも無い呼=検収 低1)。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq

FIELDS = ("[B6 出力]", "2行目末尾に ひと言:")  # 1-8b の前の形と短い形(親の判断 A6)
HEARD = "[B6 発話]"
B6_BUDGET = 80


def tok(s: str) -> int:
    return max(1, len(s) // 2)


def one(tape: Path) -> dict:
    calls = pq.read_table(tape / "calls.parquet", columns=["block_ids", "response", "b5_text", "b6_block_id"]).to_pydict()
    blocks = pq.read_table(tape / "blocks.parquet").to_pydict()
    text_of = dict(zip(blocks["block_id"], blocks["text"]))
    n = len(calls["response"])
    shared_static: dict[int, int] = {}
    ind_all: list[int] = []
    ind_speech: list[int] = []
    b6_max = 0
    n_field = n_heard_calls = n_heard_lines = n_resp = 0
    over = {"total": 0, "field_only": 0, "heard_only": 0, "both": 0, "neither": 0}
    field_tok: set[int] = set()
    heard_tok: list[int] = []
    for i in range(n):
        ids = calls["block_ids"][i]
        sst = sum(tok(text_of[ids[k]]) for k in (0, 1, 3))
        shared_static[sst] = shared_static.get(sst, 0) + 1
        b6 = text_of.get(calls["b6_block_id"][i], "")
        b5 = calls["b5_text"][i] or ""
        ind = tok(b5) + (tok(b6) if b6 else 0)
        ind_all.append(ind)
        b6_max = max(b6_max, tok(b6) if b6 else 0)
        lines = b6.split("\n")
        hl = [ln for ln in lines if ln.startswith(HEARD)]
        fl = [ln for ln in lines if ln.startswith(FIELDS)]
        if b6 and tok(b6) > B6_BUDGET:
            over["total"] += 1
            over["both" if (hl and fl) else "field_only" if fl else "heard_only" if hl else "neither"] += 1
        if fl:
            n_field += 1
            field_tok.update(tok(x) for x in fl)
        if hl:
            n_heard_calls += 1
            n_heard_lines += len(hl)
            heard_tok += [tok(x) for x in hl]
        if hl or fl:
            ind_speech.append(ind)
        if "ひと言:" in (calls["response"][i] or ""):
            n_resp += 1
    return {
        "calls": n, "calls_with_field_line": n_field, "calls_with_heard_lines": n_heard_calls,
        "heard_lines": n_heard_lines, "responses_with_comment": n_resp,
        "field_line_tokens": sorted(field_tok),
        "heard_line_tokens_max": max(heard_tok) if heard_tok else None,
        "heard_line_tokens_mean": round(sum(heard_tok) / len(heard_tok), 2) if heard_tok else None,
        "shared_static_tokens": {str(k): v for k, v in sorted(shared_static.items())},
        "individual_tokens_max": max(ind_all) if ind_all else None,
        "individual_tokens_mean": round(sum(ind_all) / len(ind_all), 2) if ind_all else None,
        "individual_tokens_max_with_speech_lines": max(ind_speech) if ind_speech else None,
        "b6_tokens_max": b6_max,
        "b6_over_80": over,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tape", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    doc = {"tool": "s8b/tools/speech_tokens.py", "token_rule": "len(text) // 2(最低 1)",
           "tapes": {Path(t).name: one(Path(t)) for t in a.tape}}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
