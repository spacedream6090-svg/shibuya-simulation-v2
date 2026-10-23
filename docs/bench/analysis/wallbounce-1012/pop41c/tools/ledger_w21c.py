"""第 4 期 4-1 段 8〜10 の材料(W21c): つなぎの台帳に段 8〜10 の近似の行を足し、段 10 の宿題の行の why に注を足す(冪等)。

    python docs/bench/analysis/wallbounce-1012/pop41c/tools/ledger_w21c.py [--dry-run]

- 足す行: ``src/shibuya/build/pop/w21_build_c.py`` の ``W21C_EXPEDIENTS``(``engine.bridging.scan`` の第 2 形)の宣言ごとに
  1 行(id ``EX-build.pop.w21_build_c-<sha8>``・``what`` は宣言の文そのまま)。段 10 に結ぶ宣言(``STAGE10_ROWS_OF_DECLARATIONS``=
  判断の入力への置き場・体 → 店の行・W16 の在庫の扱い・W20 への口・DUTY_ROLE_SPEC の 4 語)は ``remove_at=4-3``・ほかは
  ``7``。``remove_basis=inferred``。
- 段 4〜7 の段 10 の宿題の行(``DOC-pop41b-w20-port``・``DOC-pop41b-rights-port``)は ``status`` を変えず、why の末尾に
  「段 10 の材料ができた」の注を足す(前に足した本段の注は外して足し直す=冪等)。
- 書き方は台帳の今の形(indent 1・``ensure_ascii=False``・``,``/``: ``・末尾の改行)。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "src"))

from shibuya.build.pop import w21_build_c as BC  # noqa: E402
from shibuya.engine.bridging import scan as S  # noqa: E402

LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
SRC = "src/shibuya/build/pop/w21_build_c.py"
PREFIX = "EX-build.pop.w21_build_c-"
SINCE = "2026-10-15"
REC = "docs/bench/analysis/wallbounce-1012/pop41c/README.md"
WHY_43 = "外す段: 段 10(=4-3・W16 の差し替え=版上げ 3 回目)で口と行を決め直す"
WHY_7 = "外す段: 第 7 期(置き換える段が計画に無い=主張の前に感度試験で結果を駆動していないことを示す)"
TAG = "〔第 4 期 4-1 段 8〜10・W21c〕"
HEAD = f"{TAG}段 10 の材料ができた(data/world/v2_stage_4-1c・記録 {REC})。差し替えは段 10(=4-3)。"
NOTES = {
    "DOC-pop41b-w20-port": ("build/sched/w20_w21_port.attributes_from_w21(W21 → Attributes 19 欄・職業は occupation_major・"
                            "知らない担当の語は止める)と DUTY_ROLE_SPEC の 4 語(店長・補充・配送作業員・警備員)を足した。"
                            "本体の calendar_from_attributes に通る(試験)。"),
    "DOC-pop41b-rights-port": ("w21c_rights_store_staff.parquet=体 → 店の雇用の行(店の持ち主の組織の所属・engine の "
                               "staff_of_poi が読む形・Rights.grant に通る=試験)。店の持ち主の行の閉じた表の外と体の番号の"
                               "対応は段 10 のまま。"),
}


def _why(k: int) -> str:
    ra = "4-3" if k in BC.STAGE10_ROWS_OF_DECLARATIONS else "7"
    return (f"構築の段 W21c が宣言した近似(第 4 期 4-1 段 8〜10・モジュールの表 W21C_EXPEDIENTS の {k + 1} 番目・記録 {REC})。"
            + (WHY_43 if ra == "4-3" else WHY_7))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    raw = LEDGER.read_text(encoding="utf-8")
    doc = json.loads(raw)
    rows = doc["bridges"]
    decls = [d for d in S.scan_package() if d.path == SRC and d.form == S.FORM_EXPEDIENTS]
    ids = [f"{PREFIX}{d.declared_in.rsplit(':', 1)[-1]}" for d in decls]
    stale = [r for r in rows if r["id"].startswith(PREFIX) and r["id"] not in set(ids)]
    for r in stale:
        rows.remove(r)
    have = {r["id"]: r for r in rows}
    added = 0
    for k, (d, rid) in enumerate(zip(decls, ids)):
        ra = "4-3" if k in BC.STAGE10_ROWS_OF_DECLARATIONS else "7"
        if rid in have:
            have[rid]["why"] = _why(k)
            have[rid]["remove_at"] = ra
            continue
        rows.append({"id": rid, "what": d.text, "why": _why(k), "remove_at": ra, "declared_in": d.declared_in,
                     "conf": "expedient", "since": SINCE, "status": "active", "remove_basis": "inferred"})
        added += 1
    noted = 0
    for r in rows:
        note = NOTES.get(r["id"])
        if not note:
            continue
        base = r["why"].split(TAG, 1)[0]
        new = base + HEAD + note
        if new != r["why"]:
            r["why"] = new
            noted += 1
    out = json.dumps(doc, ensure_ascii=False, indent=1, separators=(",", ": ")) + "\n"
    print(f"宣言 {len(decls)}・足した行 {added}・外した古い行 {len(stale)}・注を足した行 {noted}・台帳 {len(rows)} 行")
    if not a.dry_run and out != raw:
        LEDGER.write_bytes(out.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
