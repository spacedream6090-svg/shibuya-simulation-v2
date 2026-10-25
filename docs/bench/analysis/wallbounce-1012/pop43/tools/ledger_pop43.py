"""第 4 期 4-3 段 10 差し替え: つなぎの台帳の行を足す・閉じる・外す段を改める(冪等)。

    python docs/bench/analysis/wallbounce-1012/pop43/tools/ledger_pop43.py [--dry-run]

- 足す行(コードの宣言=``engine.bridging.scan`` の第 2 形・id ``EX-<モジュール>-<sha8>``): ``build/pop/w21_apply.py`` の
  ``W21APPLY_EXPEDIENTS``(7 行)・``w21_build_b.py`` の 1.2.0 の 1 行(地位の分け)・``w21_build_c.py`` の改めた 2 行と足した
  1 行(言語の印・W20 の口・通う駅の口)。外す段は :data:`REMOVE_AT`(``remove_basis=inferred``=親が確かめる)。
- 閉じる行(``status=removed``・why の末尾に理由): 段 10 で決めて宣言を消した W21c の行(置き場・W16 の在庫の案・地位の分け=
  W21b へ移した)と、文を改めた W21c の行(言語・W20 の口=新しい行へ)・段 10 の宿題の 2 行(``DOC-pop41b-w20-port``・
  ``DOC-pop41b-rights-port``)・W16 の弱点の複製の行(``BR-W16-REPLICATED-108142``)。
- 外す段を改める行(status は active のまま・why の末尾に理由): W21c の店の担当(4-2)と 4 語(6-2)・W16 の弱点の来街者と
  乗り換えの 2 行(6-1=判断モデルの後)・段 1〜3 と段 4 の近似で 4-3 に結んでいた 5 行(7=差し替えた後も近似が残る)・賃金の
  写像の 2 行(6-1=W16 の残す行の来街者が W21 に替わるまで)。
- 足す文書の行: 店の持ち主の行の先送り(4-2)・人物の欄は今のランの判断の入力に入れない(6-1)。
- 書き方は台帳の今の形(indent 1・``ensure_ascii=False``・``,``/``: ``・末尾の改行)。前に足した本段の注は外して足し直す(冪等)。
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
REC = "docs/bench/analysis/wallbounce-1012/pop43/README.md"
SINCE = "2026-10-18"
TAG = "〔第 4 期 4-3 段 10・pop43〕"
#: 足すコードの宣言の行のモジュールと、宣言の番号(0 から)→ 外す段。
SOURCES = {
    "src/shibuya/build/pop/w21_apply.py": ("EX-build.pop.w21_apply-", "W21APPLY_EXPEDIENTS",
                                           {0: "6-2", 1: "7", 2: "6-1", 3: "6-1", 4: "4-2", 5: "7", 6: "7", 7: "6-6",
                                            8: "4-2"}),
    "src/shibuya/build/pop/w21_build_b.py": ("EX-build.pop.w21_build_b-", "W21B_EXPEDIENTS", {}),
    "src/shibuya/build/pop/w21_build_c.py": ("EX-build.pop.w21_build_c-", "W21C_EXPEDIENTS", {}),
}
#: 段 4〜7・段 8〜10 で新しく足す宣言の外す段(文の頭で見分ける)。ここに無い新しい宣言は 7。
NEW_REMOVE_AT = {
    "〔1.2.0〕外から来て働く人の地位の分け": "7",
    "人物の文の言語=": "7",
    "W20 への口=": "6-2",
    "通う駅の口=": "7",
}
WHY_NEW = {
    "6-6": "外す段: 第 6 期 6-6 ②(人の仕事を働く人のエージェントへ=乗務員・駅員の要員規模と交代を本人と雇い主の約束に)",
    "6-2": "外す段: 第 6 期 6-2(カレンダー 1b〜3=出入り・約束を本人と雇い主へ・W17 の日課のつなぎを外す段)",
    "6-1": "外す段: 第 6 期 6-1(判断モデルの段=来街者と人物の入力をそこで作り直す)",
    "4-2": "外す段: 第 4 期 4-2(権利台帳と規則の表の中身=閉じた表の店・店の持ち主の行)",
    "7": "外す段: 第 7 期(置き換える段が計画に無い=主張の前に感度試験で結果を駆動していないことを示す)",
}
#: 〔検収 L5〕閉じた行 → 後継の行(書き換えた行は解けたのではない=後継の id を why に)。
SUCCESSOR = {
    "EX-build.pop.w21_build_c-47fdae16": "EX-build.pop.w21_build_c-02821dbf(言語の印に書き換え)",
    "EX-build.pop.w21_build_c-55a9ed43": "EX-build.pop.w21_build_c-8969675f(8 区分の直接の行・電車の人は 30 分に書き換え)",
    "EX-build.pop.w21_build_c-9ac4e179": "EX-build.pop.w21_build_b-8595e5ed(地位の分けを段 4 の席の前へ移した)",
    "EX-build.pop.w21_build_c-ac5e3131": "DOC-pop43-persona-not-in-live-prompt(engine.decision.persona の正式な欄=解けた)",
    "EX-build.pop.w21_build_c-2379ec13": "EX-build.pop.w21_apply-96469fbc(残す群と外す群を決めた=解けた)",
}
#: 閉じる行 → 理由。
CLOSE = {
    "DOC-pop41b-w20-port": "段 10 で W21 → Attributes の口(build/sched/w20_w21_port)で W20cal の週の表を新しい母集団で組んだ"
                           "(担当の 4 語は DUTY_ROLE_SPEC_W21・地位は 8 区分から直接・param_hash 不変)=宿題は済んだ。"
                           "残る近似は W21c の行(W20 の口・4 語)",
    "DOC-pop41b-rights-port": "段 10 で体の番号の対応表(w21_agent_map=agent_id=390,067+person_id)と初期の行の表"
                              "(w21_rights_run=W21c の店の担当+W21b の住まい)を engine の rights.initial が読む形にした=宿題は"
                              "済んだ。店の持ち主の行(閉じた表の外)は入れない=DOC-pop43-store-owner-deferred",
}
#: 外す段を改める行 → (前の外す段, 新しい外す段, 理由)。
REPOINT = {
    "BR-W16-VISITOR-COUNT-BASIS": ("4-1", "6-1", "段 10 で来街者・定期来街者・訪日来街者(96,006 行)は W16 のまま残した(親の判断 仮-33 (10)="
                                          "来街者は判断モデルの後)"),
    "BR-W16-REPLICATED-108142": ("4-1", "6-1", "段 10 で住民・外から来て働く人の複製は消えた(W21=複製 0)。残る複製は W16 のまま残した"
                                              "通学者の 16,695 と指令の 24=16,719 体(検収 M1=通学者は W21 に体が入る段で外す)"),
    "BR-W16-NO-TRANSFER-ONLY": ("4-1", "6-1", "段 10 で乗り換えるだけの人は作っていない(W21 の段 7 は層の表だけ=体は「来るか」の段)"),
    "EX-build.pop.w21_build-60537a44": ("4-3", "7", "段 10 で差し替えたが近似は残る(2025 の小地域の表が無い)"),
    "EX-build.pop.w21_build-5af05e9d": ("4-3", "7", "段 10 で差し替えたが近似は残る(不詳の割り振り)"),
    "EX-build.pop.w21_build-ee7d62b5": ("4-3", "7", "段 10 で差し替えたが近似は残る(不詳の割り振り)"),
    "EX-build.pop.w21_build-564cf9e6": ("4-3", "7", "段 10 で差し替えたが近似は残る(2025 の区の表が無い町丁目の表)"),
    "EX-build.pop.w21_build_b-f872ad4e": ("4-3", "7", "段 10 で差し替えたが近似は残る(舞台で働く人の数の割り方)"),
    "EX-build.pop.w21_build_c-5d13fbc8": ("4-3", "4-2", "段 10 でこの規則のまま初期の行に入れた(店の持ち主の組織の所属を振る)"),
    "EX-build.pop.w21_build_c-239fd94f": ("4-3", "6-2", "段 10 でこの当てはめのまま W20cal の週の表を組んだ"),
    "DOC-wage_occ-persona-map": ("4-3", "6-1", "段 10 で W21 の人は月の賃金をそのまま使う(given)=写像は W16 の残す行(来街者・運輸ほか)だけ"),
    "DOC-wage_occ-unmapped-average": ("4-3", "6-1", "段 10 で W21 の人は月の賃金をそのまま使う(given)=平均は W16 の残す行と賃金の無い W21 の人"),
}
#: 注だけ足す行(status と外す段は変えない=活性化の後に親が閉じる)。
NOTES = {
    "BR-RIGHTS-DWELLING-BLANK": "差し替えの世界(data/world/v2_stage_4-3)では W21b の住まいの行(世帯主 → 住まい=所有と賃借・"
                                "国勢調査 第7-1表の住宅の所有の関係・27,491 行)を初期の行に入れる(engine.rights.initial の "
                                "w21_rights_run)=本体の v2 への活性化の後は空欄でない(閉じるのは活性化の後=親)",
}
#: 足す文書の行。
DOC_ROWS = [
    {"id": "DOC-pop43-store-owner-deferred",
     "what": "店の持ち主の行(組織 → 店の所有=W21b の 286 行・閉じた表の所有の対象に店が無い)は段 10 の初期の行に入れない",
     "why": "親の判断 仮-33 (3)(PENDING §1-1「閉じた表に店」の判断の後)。記録 " + REC,
     "remove_at": "4-2", "declared_in": REC, "conf": "expedient", "since": SINCE, "status": "active",
     "remove_basis": "plan", "code_at": ["src/shibuya/build/pop/w21_apply.py", "src/shibuya/engine/rights/initial.py"]},
    {"id": "DOC-pop43-store-round-robin-kept",
     "what": "差し替えの世界で W21c の店の担当のいない店(POI 2,337 のうち 2,053 店)は今の丸振り(種別 従業者の体を店へ決定論で"
             "振る)のまま=出どころの語は丸振り(engine.rights.initial.SOURCE_STAFF)・表の担当は w21c の語",
     "why": "親の判断(検収の問い 6): 担当のいない店の開け閉めがつなぎに落ちないように丸振りを残す。記録 " + REC,
     "remove_at": "4-2", "declared_in": REC, "conf": "expedient", "since": SINCE, "status": "active",
     "remove_basis": "plan", "code_at": ["src/shibuya/engine/rights/initial.py"]},
    {"id": "DOC-pop43-persona-not-in-live-prompt",
     "what": "人物の欄(engine.decision.persona=段 9 の短い版と長い版)は compose(6-1 の器と判断モデルの段)だけが読み、今のランの"
             "判断の入力(J0 の知覚の描画・mock の呼び)には入れない",
     "why": "親の判断 仮-33 (6)(判断の入力に短い版・LLM の入力に長い版の正式な欄=読むだけ)。今のランに入れると mock の応答と既定の"
            "結果が動く=判断モデルと実 LLM の段で入れる。記録 " + REC,
     "remove_at": "6-1", "declared_in": REC, "conf": "expedient", "since": SINCE, "status": "active",
     "remove_basis": "inferred", "code_at": ["src/shibuya/engine/decision/persona.py", "src/shibuya/engine/decision/port.py"]},
]


def _strip(why: str) -> str:
    return why.split(TAG, 1)[0]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = doc["bridges"]
    have = {r["id"]: r for r in rows}
    decls = [d for d in S.scan_package() if d.form == S.FORM_EXPEDIENTS]
    added, closed, repointed = [], [], []
    for path, (prefix, table, idx_map) in SOURCES.items():
        mine = [d for d in decls if d.path == path]
        ids = [f"{prefix}{d.declared_in.rsplit(':', 1)[-1]}" for d in mine]
        for k, (d, rid) in enumerate(zip(mine, ids)):
            if rid in have:
                continue
            ra = idx_map.get(k) or next((v for h, v in NEW_REMOVE_AT.items() if d.text.startswith(h)), "7")
            row = {"id": rid, "what": d.text,
                   "why": (f"{TAG}段 10 の差し替えで宣言した近似(モジュールの表 {table} の {k + 1} 番目・記録 {REC})。"
                           + WHY_NEW[ra]),
                   "remove_at": ra, "declared_in": d.declared_in, "conf": "expedient", "since": SINCE,
                   "status": "active", "remove_basis": "inferred"}
            rows.append(row)
            have[rid] = row
            added.append(rid)
        # 宣言の消えた本モジュールの行(段 10 で決めた・文を改めた)=閉じる
        for r in rows:
            if r["id"].startswith(prefix) and r["id"] not in set(ids) and r["status"] == "active":
                succ = SUCCESSOR.get(r["id"], "")
                r["why"] = _strip(r["why"]) + (f"{TAG}閉じた: 段 10 で決めて宣言を消したか、文を改めて新しい行にした"
                                                + (f"=後継 {succ}" if succ else "")
                                                + f"(記録 {REC}・取り込みの commit は親)")
                r["status"] = "removed"
                closed.append(r["id"])
    for rid, reason in CLOSE.items():
        r = have[rid]
        r["why"] = _strip(r["why"]) + f"{TAG}閉じた: {reason}(記録 {REC}・取り込みの commit は親)"
        if r["status"] != "removed":
            r["status"] = "removed"
            closed.append(rid)
    for rid, (ra_from, ra, reason) in REPOINT.items():
        r = have[rid]
        if r["remove_at"] not in (ra_from, ra):
            raise SystemExit(f"{rid}: 外す段が想定({ra_from})と違う: {r['remove_at']}")
        r["why"] = _strip(r["why"]) + f"{TAG}外す段を {ra_from} → {ra}: {reason}(記録 {REC})"
        if r["remove_at"] != ra:
            r["remove_at"] = ra
            r["remove_basis"] = "inferred"
            repointed.append(rid)
    for rid, note in NOTES.items():
        r = have[rid]
        r["why"] = _strip(r["why"]) + f"{TAG}{note}(記録 {REC})"
    for d in DOC_ROWS:
        if d["id"] not in have:
            rows.append(dict(d))
            have[d["id"]] = rows[-1]
            added.append(d["id"])
    print(f"足した {len(added)}・閉じた {len(closed)}・外す段を改めた {len(repointed)}・行 {len(rows)}")
    for x in added:
        print("  +", x)
    for x in closed:
        print("  -", x)
    for x in repointed:
        print("  ~", x)
    if not a.dry_run:
        LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
