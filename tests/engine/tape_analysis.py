"""録画テープの行動分布・対象・会話成立性を数える診断スクリプト(C6・09-09)。

**なぜ tools/ でなくここか**: ``tools/c6/`` はサブ P の作業域・``tools/`` 直下は運搬役
(``fleet_gen``)の場所として使っている。本スクリプトは「テープを読んで数えるだけ」の
読み取り専用の検死道具で、``engine.tape`` と ``llm.parser`` にしか触らない。

答えたい問い(C6 の 1 日ランで ``conversation_sessions: 0`` になった原因の切り分け)
    (a) **モデルが 会話 を選ばない** → ``行動`` 分布の 会話 比率。
    (b) **選んでも 対象 が解決できず不成立** → 会話 を選んだ呼の ``(tick, cell)`` を突き合わせ、
        「同 tick・同セルに**もう1人**会話候補が居たか」を数える。
        ``engine.commit.pair_partners`` は**同じ適用バッチの中の同セル最小 id**を相手にするので、
        相手が居なければ ``target=-1`` で不成立になる(LLM の ``対象`` 欄は 会話 では使われない)。
    (c) 艦隊経路の結線 → 本スクリプトでは分からない(``tests/engine/test_fleet_wiring.py`` の
        ``test_fleet_conversation_opens_a_session`` が (c) を除外する)。

使い方::

    python tests/engine/tape_analysis.py data/tape/c6-day-1
    python tests/engine/tape_analysis.py data/tape/c6-day-1 --json out.json --top 20

``call_id`` は ``"<tick>:<agent>:<class>"``(``engine.llm_bridge`` の規約)。セルはテープに
無いので、``--world <dir>`` を渡すと ``B4`` 系の描画から…**取れない**(共有ブロックは
セル代表で intern されるため個体のセルは復元できない)。そこで (b) は
``block_ids`` の**共有ブロック集合が一致する呼=同じセル・同じ 5 分帯**という同値類で近似する
(知覚レンダラは同一(セル, 5分帯, 種別)で同じ共有ブロックを引く=規約⑧)。近似であることを
出力に明記する。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from shibuya.engine.tape import Tape  # noqa: E402
from shibuya.llm.contract import ACTION_VOCAB_12, ROLE_ACTION_WORDS  # noqa: E402
from shibuya.llm.parser import parse_two_line  # noqa: E402

TALK = "会話"


def analyze(tape_dir: str | Path) -> dict[str, Any]:
    """テープ 1 本を読んで診断 dict を返す(読み取り専用)。"""
    tape = Tape(tape_dir)
    n = 0
    actions: Counter[str] = Counter()
    raw_actions: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    target_kinds: Counter[str] = Counter()
    talk_targets: Counter[str] = Counter()
    n_effective_bad = 0
    n_strict_bad = 0
    n_alias = 0
    alias_surfaces: Counter[str] = Counter()
    n_unknown_word = 0
    n_empty = 0
    finish_len = 0
    # (b) 用: 「共有ブロック集合が同じ」= 同じセル・同じ 5 分帯の同値類
    group_calls: dict[tuple[int, tuple[str, ...]], list[int]] = defaultdict(list)
    group_talkers: dict[tuple[int, tuple[str, ...]], list[int]] = defaultdict(list)

    for row in tape.rows():
        n += 1
        text = row.response or ""
        if not text.strip():
            n_empty += 1
        p = parse_two_line(text)
        if not p.format_ok:
            n_effective_bad += 1
        if not p.strict_format_ok:
            n_strict_bad += 1
        if p.alias_used:
            n_alias += 1
            alias_surfaces.update(p.alias_surfaces)
        if p.action is None:
            n_unknown_word += 1
            raw_actions[p.raw_action or "(空)"] += 1
        else:
            actions[p.action] += 1
        if p.reason:
            reasons[p.reason[:20]] += 1
        target_kinds[p.target.kind.name] += 1
        key = (int(row.tick), tuple(row.block_ids))
        group_calls[key].append(int(row.agent_id))
        if p.action == TALK:
            talk_targets[p.target.raw or "(なし)"] += 1
            group_talkers[key].append(int(row.agent_id))

    n_talk = int(actions.get(TALK, 0))
    # (b): 会話 を選んだ呼のうち、同 tick・同共有ブロック(≒同セル/同5分帯)に
    #      **会話の相手になりうる別の呼**が居たか
    talk_with_any_peer = 0
    talk_with_talk_peer = 0
    for key, talkers in group_talkers.items():
        peers = len(group_calls[key])
        for _ in talkers:
            if peers >= 2:
                talk_with_any_peer += 1
            if len(talkers) >= 2:
                talk_with_talk_peer += 1

    known = set(ACTION_VOCAB_12) | set(ROLE_ACTION_WORDS)
    return {
        "tape": str(tape_dir),
        "rows": n,
        "format": {
            "effective_error_rate": (n_effective_bad / n) if n else 0.0,
            "strict_error_rate": (n_strict_bad / n) if n else 0.0,
            "alias_rate": (n_alias / n) if n else 0.0,
            "alias_surfaces": alias_surfaces.most_common(20),
            "unknown_action_rate": (n_unknown_word / n) if n else 0.0,
            "empty_responses": n_empty,
            "finish_length": finish_len,
        },
        "actions": actions.most_common(),
        "action_share": {k: v / n for k, v in actions.most_common()} if n else {},
        "unknown_action_words": raw_actions.most_common(30),
        "unknown_words_outside_vocab": [
            w for w, _ in raw_actions.most_common(30) if w not in known
        ],
        "target_kinds": target_kinds.most_common(),
        "conversation": {
            # (a) モデルが 会話 を選ぶ割合
            "talk_calls": n_talk,
            "talk_share": (n_talk / n) if n else 0.0,
            # (b) 相手が居たか(**共有ブロック一致による近似**)
            "talk_with_any_peer_in_same_group": talk_with_any_peer,
            "talk_with_another_talker_in_same_group": talk_with_talk_peer,
            "talk_targets_written_by_model": talk_targets.most_common(20),
            "note": (
                "engine.commit.pair_partners は同じ適用バッチの同セル最小 id を相手にするので、"
                "LLM が書いた 対象 欄は 会話 では使われない。相手が居なければ target=-1 で不成立。"
                "グループは共有ブロック集合の一致=同(セル,5分帯,種別)の近似。"
            ),
        },
        "top_reasons": reasons.most_common(10),
    }


def format_report(d: dict[str, Any], top: int = 12) -> str:
    f = d["format"]
    c = d["conversation"]
    lines = [
        f"[tape] {d['tape']}  行 {d['rows']:,}",
        f"  書式 実効 {f['effective_error_rate']:.3f} / 厳密 {f['strict_error_rate']:.3f}"
        f" ・別名 {f['alias_rate']:.3f} ・語彙外 {f['unknown_action_rate']:.3f}"
        f" ・空応答 {f['empty_responses']:,}",
        "  行動分布: "
        + " ".join(f"{w}={n}({n / max(1, d['rows']):.3f})" for w, n in d["actions"][:top]),
        "  対象の型: " + " ".join(f"{k}={v}" for k, v in d["target_kinds"]),
        f"  会話: 選んだ呼 {c['talk_calls']:,}({c['talk_share']:.4f})"
        f" / 同グループに他の呼が居た {c['talk_with_any_peer_in_same_group']:,}"
        f" / 同グループに他の会話者が居た {c['talk_with_another_talker_in_same_group']:,}",
    ]
    if f["alias_surfaces"]:
        lines.append("  別名の表層: " + " ".join(f"{s}={n}" for s, n in f["alias_surfaces"][:top]))
    if d["unknown_action_words"]:
        lines.append(
            "  語彙外の行動語: "
            + " ".join(f"{w}={n}" for w, n in d["unknown_action_words"][:top])
        )
    lines.append("  " + c["note"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("tape", help="録画テープのディレクトリ(calls.parquet を含む)")
    ap.add_argument("--json", default="", help="診断 dict を JSON で書き出す先")
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args(argv)
    d = analyze(args.tape)
    print(format_report(d, args.top))
    if args.json:
        Path(args.json).write_text(
            json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"  → {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
