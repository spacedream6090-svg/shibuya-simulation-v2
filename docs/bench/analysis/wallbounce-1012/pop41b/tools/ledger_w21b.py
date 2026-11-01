"""第 4 期 4-1 段 4〜7(W21b): つなぎの台帳に段 4〜7 の近似の行を足し、W16 ほかの行の why に注を足す(冪等)。

    python docs/bench/analysis/wallbounce-1012/pop41b/tools/ledger_w21b.py [--dry-run]

- 足す行: ``src/shibuya/build/pop/w21_build_b.py`` の ``W21B_EXPEDIENTS``(``engine.bridging.scan`` の第 2 形)の宣言ごとに
  1 行(id ``EX-build.pop.w21_build_b-<sha8>``・``what`` は宣言の文そのまま)。舞台で働く人の数(1 番目)は ``remove_at=4-3``
  (2025 の従業地・通学地集計の公表の後=「4-3 以降」)・ほかは ``7``(置き換える段が計画に無い)。``remove_basis=inferred``。
- 段 4〜7 で置き換えの資産ができた行(W16・W6・権利台帳の空欄)は ``status`` を変えず、why の末尾に注を足す(前に足した
  本段の注は外して足し直す=冪等)。
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

from shibuya.engine.bridging import scan as S  # noqa: E402

LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
SRC = "src/shibuya/build/pop/w21_build_b.py"
SINCE = "2026-10-15"
REC = "docs/bench/analysis/wallbounce-1012/pop41b/README.md"
REMOVE_AT = {0: "4-3"}
WHY_43 = ("外す段: 4-3 以降=2025 の従業地・通学地集計(町丁目の昼の人口と従業地の結合=統計局の公表の予定 2027-05)の後に"
          "見直す(台帳の段の表に「4-3 以降」が無いので 4-3 と書く)")
WHY_7 = "外す段: 第 7 期(置き換える段が計画に無い=主張の前に感度試験で結果を駆動していないことを示す)"
#: 〔検収 L4〕宣言の番号(0 から)→ why の末尾に足す文。
EXTRA = {
    0: ("外から来て働く人 173,150 は R-116 §4 の枠「外から来て働く人と学ぶ人 18.5〜25 万」の下の端より少ない=働く人だけ"
        "(学ぶ人の舞台の分は空欄)・舞台の割合は町丁目の中を一様と見た近似"),
}
#: 〔検収 M1・L9〕段 10 の口の宿題の行(DOC・外す段=段 10=4-3)。
DOC_ROWS = (
    {"id": "DOC-pop41b-w20-port",
     "what": ("W21b の担当の語(duty_role)と人の表は W20 の入力と形が違う: W20 の DUTY_ROLE_SPEC の鍵に無い語(店長・補充・"
              "配送作業員・警備員)を W20 は黙って「担当なし」と読み、W20 は種別 0・2(席のある体)の担当を見ない。"
              "calendar_inputs_b の 5 列は段 10 の材料で、W20 の入力(Attributes 19 欄と Employment)ではない"),
     "why": ("親の判断(検収 M1): 段 10 で W21 から Attributes を作る関数を書く(職業は occupation_major を直接・雇用の語は "
             "W16_EMPLOYMENT_OF で写す)・鍵に無い 4 語は DUTY_ROLE_SPEC に足す(勤務場所・交替制)。記録 " + REC),
     "remove_at": "4-3", "declared_in": REC, "conf": "expedient", "since": SINCE, "status": "active",
     "remove_basis": "plan", "code_at": ["src/shibuya/build/pop/attr_fns.py"]},
    {"id": "DOC-pop41b-rights-port",
     "what": ("W21b の権利台帳の開始時点の行は engine の口と 3 点違う: 店の担当(engine の staff_of_poi が読む「体 → 店」の"
              "雇用の行)が無い(店長は duty_role だけ)・店の持ち主の行(組織 → 店の所有)は閉じた表の外(in_closed_table=偽)・"
              "体の番号は w21_people.person_id(ランの SoA の番号との対応は段 10)"),
     "why": ("検収 L9: 閉じた表の行は Rights.grant が全部受け付けることを試験で確かめた。店の担当の行・店の持ち主の表し方・"
             "番号の対応は段 10(W16 の差し替え)で決める。記録 " + REC),
     "remove_at": "4-3", "declared_in": REC, "conf": "expedient", "since": SINCE, "status": "active",
     "remove_basis": "plan", "code_at": ["src/shibuya/build/pop/w21_build_b.py"]},
)
TAG = "〔第 4 期 4-1 段 4〜7・W21b〕"
HEAD = f"{TAG}置き換えの資産ができた(data/world/v2_stage_4-1b の w21_*・記録 {REC})。差し替えは段 10(=4-3)。"
NOTES = {
    "W6#1": "W21b は W6 の組織の従業者を経済センサスの席として使い、人数を国勢調査に合わせた(空席・席の外は計器)。組織の場所は W6 のまま。",
    "W16#7": "W21b は外から来て働く人の男女・年齢を従業地 第11-1表で引いた体を作った(段 4・複製 0)。",
    "W16#8": "W21b は来街者・通学者を層の表にした(段 7=人は作らない・通学の舞台の分は空欄)。",
    "W16#9": "W21b の層の表=通学(区全体)・訪日・乗り換えだけ・通過は枠と分布だけ・都市圏の私事と業務の来街は空欄(仮-23)。",
    "W16#10": "W21b は②群の担当(duty_role)を役割から割り当てた(運輸で席の無い人=運転士・車掌と駅員など)。指令は作っていない。",
    "W16#13": "W21b は舞台の外で働く住民の駅の口を大都市交通センサスの路線別の流入の比で引く(PT の到着側の重みを使わない)。",
    "BR-W16-REPLICATED-108142": "W21b の外から来て働く人の体も複製 0。",
    "BR-W16-VISITOR-COUNT-BASIS": "W21b の外の人は層の表(人は作らない)・都市圏の私事と業務の来街は空欄(仮-23)。",
    "BR-W16-NO-TRANSFER-ONLY": "W21b の層の表に乗り換えだけの人と JR の通過の行(枠と分布だけ・人は作らない)。",
    "BR-RIGHTS-DWELLING-BLANK": "W21b の権利台帳の開始時点の行に住まい(段 2 の tenure=国勢調査 第7-1表・世帯主 → 住まい)を作った。",
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
    want = {f"EX-build.pop.w21_build_b-{d.declared_in.rsplit(':', 1)[-1]}" for d in decls}
    # 本段の行のうち、宣言の文が変わって id の合わなくなった古い行は外す(本段が足した行だけ=接頭辞で絞る)
    stale = [r for r in rows if r["id"].startswith("EX-build.pop.w21_build_b-") and r["id"] not in want]
    for r in stale:
        rows.remove(r)
    have = {r["id"] for r in rows}
    added = 0
    for i, d in enumerate(decls):
        rid = f"EX-build.pop.w21_build_b-{d.declared_in.rsplit(':', 1)[-1]}"
        if rid in have:
            continue
        ra = REMOVE_AT.get(i, "7")
        why = (f"構築の段 W21b が宣言した近似(第 4 期 4-1 段 4〜7・モジュールの表 W21B_EXPEDIENTS の {i + 1} 番目・記録 {REC})。"
               + (WHY_43 if ra == "4-3" else WHY_7) + ("。" + EXTRA[i] if i in EXTRA else ""))
        rows.append({"id": rid, "what": d.text, "why": why, "remove_at": ra, "declared_in": d.declared_in,
                     "conf": "expedient", "since": SINCE, "status": "active", "remove_basis": "inferred"})
        added += 1
    for i, r in enumerate(rows):  # 前に足した行の why を今の文に(EXTRA を足した後の冪等)
        if r["id"] in want:
            k = [f"EX-build.pop.w21_build_b-{d.declared_in.rsplit(':', 1)[-1]}" for d in decls].index(r["id"])
            ra = REMOVE_AT.get(k, "7")
            r["why"] = (f"構築の段 W21b が宣言した近似(第 4 期 4-1 段 4〜7・モジュールの表 W21B_EXPEDIENTS の {k + 1} 番目・"
                        f"記録 {REC})。" + (WHY_43 if ra == "4-3" else WHY_7) + ("。" + EXTRA[k] if k in EXTRA else ""))
    have = {r["id"] for r in rows}
    for d in DOC_ROWS:  # 段 10 の口の宿題の行
        if d["id"] in have:
            r = next(x for x in rows if x["id"] == d["id"])
            r.update(d)
        else:
            rows.append(dict(d))
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
    print(f"宣言 {len(decls)}・足した行 {added}・外した古い行 {len(stale)}・注を足した行 {noted}")
    if not a.dry_run and out != raw:
        LEDGER.write_bytes(out.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
