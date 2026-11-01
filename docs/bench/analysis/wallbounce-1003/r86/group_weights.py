# -*- coding: utf-8 -*-
"""R-86: 「無い」と「近い」の小分類を、答申 §3 の足りない行動の群(G 番号)にまとめて重みを足す。
群の切り方は実行役の判断(推測・expedient)。使い方: python group_weights.py <coverage_ssb.json> <out_json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GROUPS = {
    "G01 身の回りの用事(トイレ・身支度)": ["423"],
    "G02 受診・療養": ["421", "413", "425"],
    "G03 子ども・家族の世話と同伴(付き添い・送迎・遊ぶ)": ["221", "222", "223", "224", "225", "226", "227", "2110", "2111", "2112", "2113"],
    "G04 遠隔の連絡(電話・メッセージ・メール・手紙)": ["524", "525", "526"],
    "G05 スポーツ・運動(球技・ジム・ウォーキング)": ["541", "542", "543", "544", "545"],
    "G06 公的サービス・手続き(役所・銀行)": ["232", "2109"],
    "G07 社会参加・ボランティア・地域の会合": ["251", "511", "521"],
    "G08 礼拝": ["512"],
    "G09 求職": ["142"],
    "G10 自宅の家事(炊事・掃除・洗濯・修繕)": ["2101", "2102", "2103", "2104", "2105", "2106", "2107", "2108", "2114"],
    "G11 趣味の制作・園芸・ペット": ["5303", "5304", "5305", "5306", "5308"],
    "G12 ドライブ(車)": ["5312"],
    "K01 仕事の中身(接客・補充・事務)": ["111", "121"],
    "K02 学校・学習": ["311", "312", "313", "321"],
    "K03 メディア・画面(テレビ・PC・ゲーム・読書)": ["551", "552", "553", "554", "555", "556", "5310", "5311", "5309", "5302", "5313"],
    "K04 対人サービス・観覧(美容室・塾・映画・劇場・浴場)": ["233", "424", "5301", "422"],
    "K05 散歩・犬の散歩": ["5307"],
    "K06 うたたね・家族との会話": ["412", "523"],
}


def main(src: str, dst: str) -> None:
    d = json.loads(Path(src).read_text(encoding="utf-8"))
    by = {r["code"]: r for r in d["rows"]}
    used = set()
    out = []
    for g, codes in GROUPS.items():
        rs = [by[c] for c in codes]
        used |= set(codes)
        out.append({"group": g, "codes": codes, "minutes": sum(r["minutes"] for r in rs),
                    "w": round(sum(r["w"] for r in rs), 2), "cov": sorted({r["cov"] for r in rs})})
    rest = [c for c, r in by.items() if r["cov"] in ("無い", "近い") and c not in used]
    out.sort(key=lambda x: -x["w"])
    Path(dst).write_text(json.dumps({"groups": out, "ungrouped_absent_or_near": rest}, ensure_ascii=False, indent=1),
                         encoding="utf-8", newline="\n")
    for g in out:
        print(g["group"], g["minutes"], g["w"], g["cov"])
    print("ungrouped", rest)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
