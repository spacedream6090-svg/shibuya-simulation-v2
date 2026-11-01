"""第 4 期 4-1 段 1〜3(W21): つなぎの台帳に W21 の近似の行を足し、W16 の行の why に注を足す(1 回だけ・冪等)。

    python docs/bench/analysis/wallbounce-1012/pop41/tools/ledger_w21.py [--dry-run]

- 足す行: ``src/shibuya/build/pop/w21_build.py`` の ``W21_EXPEDIENTS``(``engine.bridging.scan`` の第 2 形)の宣言ごとに 1 行
  (id ``EX-build.pop.w21_build-<sha8>``・``what`` は宣言の文そのまま)。時点の混ぜ方と不詳の 4 行は ``remove_at=4-3``
  (2025 の小地域の表の公表の後=「4-3 以降」)・ほかは ``7``(置き換える段が計画に無い)。``remove_basis=inferred``。
- W16 の行(remove_at=4-1)のうち本段で置き換えの資産ができた行は ``status`` を変えず、why の末尾に注を足す。
- 書き方は台帳の今の形(indent 1・``ensure_ascii=False``・``,``/``: ``・末尾の改行)。既に足してあれば何もしない。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "src"))

from shibuya.engine.bridging import scan as S  # noqa: E402

LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
SRC = "src/shibuya/build/pop/w21_build.py"
SINCE = "2026-10-15"
REC = "docs/bench/analysis/wallbounce-1012/pop41/README.md"
#: W21_EXPEDIENTS の番号(0 から)→ 外す段。0〜3 は 2025 の小地域の表の後(4-3 以降)。
REMOVE_AT = {0: "4-3", 1: "4-3", 2: "4-3", 3: "4-3"}
WHY_43 = ("外す段: 4-3 以降=2025 の小地域の表(と小地域の不詳補完値)の公表の後に差し替える(統計局の資料 2 は小地域の公表を"
          "「別途」と書く=R-116 §空欄 1)。台帳の段の表に「4-3 以降」が無いので 4-3 と書く(PENDING 仮-23)")
WHY_7 = "外す段: 第 7 期(置き換える段が計画に無い=主張の前に感度試験で結果を駆動していないことを示す)"
EXTRA = {
    15: "住民基本台帳(R-116 §2 の U7=取得はユーザーの判断待ち)が入れば国籍と人数の時点を見直す",
    4: "W16#1・#2 と同じ按分(差し替えの後も残る)",
}
TAG = "〔第 4 期 4-1 段 1〜3・W21〕"
NOTE_HEAD = (f"{TAG}置き換えの資産ができた(data/world/v2_stage_4-1 の w21_*・記録 {REC})。差し替えは段 10(=4-3)。")
#: 〔検収 情報〕枠の行だけができた行(人は段 7 で作る)の頭。
FRAME_HEAD = (f"{TAG}段 1〜3 で枠の行ができた(data/world/v2_stage_4-1 の w21_frame.json・記録 {REC})。人は段 7 で作る。")
FRAME_ROWS = {"W16#9", "BR-W16-VISITOR-COUNT-BASIS", "BR-W16-NO-TRANSFER-ONLY"}
W16_NOTES = {
    "W16#3": "W21 は住宅の建て方(第8-1表)の階の区分ごとに町丁目の住居系の建物の床面積で配る。",
    "W16#5": "W21 は町丁目の年齢不詳を区の 2020 の遡及の不詳補完値と原数値の差の比で割り振る。",
    "W16#9": "枠は PT の目的別の到着比を使わない(構築側の値だけ・都市圏の私事と業務の来街は空欄=仮-23)。",
    "W16#11": "W21 は在学の種類(第14表)と通学地(第16-3表)を持つ。学校のセル(定員)はまだ無い。",
    "W16#12": "W21 は労働力状態(第9・10表)と従業地(第16-2表・第8表)を町丁目 × 男女の周辺へ寄せて引く。",
    "W16#14": "W21 は家族類型 × 世帯人員(第5-2・6-1表・2025 第10表)で世帯を組み、続き柄と年齢を条件付きで引く。",
    "BR-W16-REPLICATED-108142": "W21 の住民は複製 0 体(synthetic 0)。通勤・通学の人は段 7。",
    "BR-W16-VISITOR-COUNT-BASIS": "枠の行: 都市圏の私事・業務の来街は空欄(仮-23)・訪日 4.3〜8.5 万(引)。",
    "BR-W16-NO-TRANSFER-ONLY": "枠の行: 乗り換えだけの人 70〜80 万・JR の通過 約 46 万(引)。",
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    raw = LEDGER.read_text(encoding="utf-8")
    doc = json.loads(raw)
    rows = doc["bridges"]
    have = {r["id"] for r in rows}
    decls = [d for d in S.scan_package() if d.path == SRC and d.form == S.FORM_EXPEDIENTS]
    added = 0
    for i, d in enumerate(decls):
        rid = f"EX-build.pop.w21_build-{d.declared_in.rsplit(':', 1)[-1]}"
        if rid in have:
            continue
        ra = REMOVE_AT.get(i, "7")
        why = (f"構築の段 W21 が宣言した近似(第 4 期 4-1 段 1〜3・モジュールの表 W21_EXPEDIENTS の {i + 1} 番目・記録 {REC})。"
               + (WHY_43 if ra == "4-3" else WHY_7) + ("。" + EXTRA[i] if i in EXTRA else ""))
        rows.append({"id": rid, "what": d.text, "why": why, "remove_at": ra, "declared_in": d.declared_in,
                     "conf": "expedient", "since": SINCE, "status": "active", "remove_basis": "inferred"})
        added += 1
    noted = 0
    for r in rows:
        note = W16_NOTES.get(r["id"])
        if not note:
            continue
        base = r["why"].split(TAG, 1)[0]  # 前に足した注は外して足し直す(冪等)
        new = base + (FRAME_HEAD if r["id"] in FRAME_ROWS else NOTE_HEAD) + note
        if new != r["why"]:
            r["why"] = new
            noted += 1
    out = json.dumps(doc, ensure_ascii=False, indent=1, separators=(",", ": ")) + "\n"
    print(f"宣言 {len(decls)}・足した行 {added}・注を足した W16 の行 {noted}")
    if not a.dry_run and out != raw:
        LEDGER.write_bytes(out.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
