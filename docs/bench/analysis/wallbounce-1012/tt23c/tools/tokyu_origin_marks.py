"""第 2 期 2-3c: 東急 渋谷の下りの 2 表(TY01_2 東横線・DT01_2 田園都市線)の「当駅始発」の印の読み取り。

印は分の上の青い塗りの丸。頁の右の凡例(「時刻表の見方」)は「● 当駅始発・⑤…5 番線発車」(東横線)・
「● 当駅始発・②…2 番線発車」(田園都市線)=番線の数字の入った青い丸も当駅始発の印。第330 の読み取り
(extraction-tokyu-metro.md §7 の 3「取っていない情報: 当駅始発・番線」)で取っていなかった印を、同じ作法で取る。

部分コマンド(リポの根で・**システムの python**=PyMuPDF が要る・ネットワークなし):

- ``read1`` : 読み 1(機械)。第330 の道具 ``data/user_timetables/_extracted/tools/tokyu_read1.py`` の ``extract_file`` と
  ``locate``(図形の取り出しと時の帯・マスの位置)を**読むだけで**呼び(道具は書き換えない・``glyphs.json`` も書かない)、
  第330 で名前を付けた指紋の表 ``tokyu_fp_labels.json`` の ``#dot``(青い丸)・``#w5``(白い 5)・``#w2``(白い 2)で
  印を決める(``#dot`` だけ=●・``#dot``+``#w5``=⑤・``#dot``+``#w2``=②)。分はマスの数字の指紋の名前から。
  出力 ``_extracted/東急_印.read1.csv``(列=表,平日土休,時,分,印,md5,読み)。
- ``read2`` : 読み 2(目)。``_extracted/read2_raw/tokyu_origin_marks.txt``(150 dpi の時の帯の画像を見て起こした分と印・
  読み 1 の分の値を見る前に書いた)→ ``_extracted/東急_印.read2.csv``。
- ``check`` : 2 つの読みを (表, 平日土休, 時, 分) で 1 行ずつ突き合わせ(印の種類も比べる)、時ごとの本数(読み 1・読み 2)を
  並べ、印の付いた分が final の発車の表(``東急_<線>_渋谷_<方面>_<暦>_final.csv``)にあることを確かめ、ODPT チャレンジ枠の
  東急 渋谷の駅の時刻表の ``odpt:isOrigin``(照合だけ・構築の入力ではない)と分まで照らす。食い違いが 0 なら
  ``_extracted/東急_印.final.csv``(読み=1=2)を書く。要約(本数・時ごとの数・一致の数=時刻は書かない)を
  ``--record`` の JSON へ。
- ``selftest`` : 比べる道具が違いを見落とさないこと(読み 2 の写しに 3 か所の違い=1 行の削除・印の種類 1・分 1 を入れて
  3 件とも出ること・写しはメモリの中だけ)。

逐次ループ宣言: 表の図形(1 頁に数千)と印(約 200)を 1 回ずつ。道具だけ(ランでは呼ばない)。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
UT = REPO / "data" / "user_timetables"
EXT = UT / "_extracted"
TOOLS = EXT / "tools"
CHALLENGE = REPO / "data" / "odpt" / "challenge"

#: 読む 2 表(PDF の名 → final の表の stem・ODPT チャレンジ枠の駅の時刻表=照合だけ・md5 の先頭=第330 README §2-1)。
TABLES: dict[str, dict[str, str]] = {
    "202603_ty01_shibuya_2.pdf": {"stem": "東急_東横線_渋谷_横浜方面", "dir": "toyoko", "md5_8": "d9423192",
                                  "challenge": "station_timetable_tokyu_toyoko_shibuya.json"},
    "202603_dt01_shibuya_2.pdf": {"stem": "東急_田園都市線_渋谷_中央林間方面", "dir": "denentoshi", "md5_8": "e6c9280a",
                                  "challenge": "station_timetable_tokyu_denentoshi_shibuya.json"},
}
HALF_CAL = {"wd": "平日", "ho": "土休"}
CAL_ODPT = {"平日": "Weekday", "土休": "SaturdayHoliday"}
MARK_OF = {"": "●", "#w5": "⑤", "#w2": "②"}
COLS = ["表", "平日土休", "時", "分", "印", "md5", "読み"]
OUT1 = EXT / "東急_印.read1.csv"
OUT2 = EXT / "東急_印.read2.csv"
OUTF = EXT / "東急_印.final.csv"
RAW2 = EXT / "read2_raw" / "tokyu_origin_marks.txt"
#: 食い違いの決着(300 dpi の画像で確かめて読み 1 か読み 2 を採る・理由つき)。jr_resolutions.json と同じ扱い。
RES = EXT / "read2_raw" / "tokyu_origin_marks_resolutions.json"


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def _tokyu_read1():
    # 〔検収 L5〕第330 の道具の置き場に __pycache__ の pyc を残さない(読むだけで呼ぶ)
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("tokyu_read1_330", TOOLS / "tokyu_read1.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        sys.dont_write_bytecode = prev
    return mod


def _write(path: Path, rows: list[list]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows)


def _read(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _order(r: dict) -> tuple:
    return (r["表"], r["平日土休"], (int(r["時"]) - 4) % 24, int(r["分"]))


def cmd_read1(_a: argparse.Namespace) -> int:
    t = _tokyu_read1()
    labels = json.loads((TOOLS / "tokyu_fp_labels.json").read_text(encoding="utf-8"))
    rows: list[list] = []
    problems: list[str] = []
    for pdf, meta in TABLES.items():
        path = UT / "tokyu" / meta["dir"] / "timetable" / pdf
        md5 = _md5(path)
        if not md5.startswith(meta["md5_8"]):
            raise RuntimeError(f"{pdf} の md5 が第330 の一覧と違う")
        _pg, bands, halves, glyphs, decos = t.extract_file(str(path))
        cells: dict[tuple, list] = defaultdict(list)
        for g in glyphs + decos:
            loc = t.locate(g, bands, halves)
            if loc is None:
                continue
            half, row, cell = loc
            g["above"] = (g["y0"] + g["y1"]) / 2 < bands[half][row].y0 + 1
            cells[(half, t.HOURS[row], cell)].append(g)
        for (half, hour, _cell), rs in sorted(cells.items(), key=lambda kv: (kv[0][0], (kv[0][1] - 4) % 24, kv[0][2])):
            toks = [labels.get(r["fp"], {}).get("label", "?") for r in rs if r["kind"] == "small"]
            if "#dot" not in toks:
                continue
            digits = sorted([r for r in rs if r["kind"] == "digit" and not r["above"]], key=lambda r: r["x0"])
            s = "".join(labels.get(d["fp"], {}).get("label", "?") for d in digits)
            if not s.isdigit() or not 0 <= int(s) <= 59:
                problems.append(f"{pdf} {half} {hour}: 印のあるマスの分が読めない")
                continue
            nums = [x for x in ("#w5", "#w2") if x in toks]
            if toks.count("#dot") != 1 or len(nums) > 1:
                problems.append(f"{pdf} {half} {hour}: 1 つのマスに印が 2 つ")
                continue
            rows.append([meta["stem"], HALF_CAL[half], hour, int(s), MARK_OF[nums[0] if nums else ""], md5[:8], 1])
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    _write(OUT1, rows)
    print(f"読み 1: {len(rows)} 行 → {OUT1.name}", dict(Counter((r[0], r[1]) for r in rows)))
    return 0


def parse_raw2(text: str) -> list[list]:
    md5_of = {meta["stem"]: _md5(UT / "tokyu" / meta["dir"] / "timetable" / pdf)[:8] for pdf, meta in TABLES.items()}
    stem_of = {pdf[:-4]: meta["stem"] for pdf, meta in TABLES.items()}
    rows: list[list] = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        head, _, body = line.partition(":")
        pdf_stem, half, hour = head.split()
        stem = stem_of[pdf_stem]
        for tok in body.split():
            mark = tok[-1]
            if mark not in ("●", "⑤", "②"):
                raise ValueError(f"印の字が違う: {line}")
            rows.append([stem, HALF_CAL[half], int(hour), int(tok[:-1]), mark, md5_of[stem], 2])
    return rows


def cmd_read2(_a: argparse.Namespace) -> int:
    rows = parse_raw2(RAW2.read_text(encoding="utf-8"))
    _write(OUT2, rows)
    print(f"読み 2: {len(rows)} 行 → {OUT2.name}", dict(Counter((r[0], r[1]) for r in rows)))
    return 0


def compare(r1: list[dict], r2: list[dict]) -> list[dict]:
    """(表, 平日土休, 時, 分) で突き合わせた違い(片方だけ・印の種類が違う)。時刻は呼び手が記録に写さない。"""
    k = lambda r: (r["表"], r["平日土休"], int(r["時"]), int(r["分"]))  # noqa: E731
    c1, c2 = Counter(map(k, r1)), Counter(map(k, r2))
    m1, m2 = {k(r): r["印"] for r in r1}, {k(r): r["印"] for r in r2}
    out = []
    for key in sorted(set(c1) | set(c2)):
        if c1[key] != c2[key]:
            out.append({"key": key, "what": "count", "r1": c1[key], "r2": c2[key]})
        elif m1[key] != m2[key]:
            out.append({"key": key, "what": "印", "r1": m1[key], "r2": m2[key]})
    return out


def cmd_check(a: argparse.Namespace) -> int:
    r1, r2 = _read(OUT1), _read(OUT2)
    diffs = compare(r1, r2)
    hours: dict[str, dict[str, dict[int, list[int]]]] = {}
    for tag, rr in (("r1", r1), ("r2", r2)):
        for r in rr:
            d = hours.setdefault(f"{r['表']}|{r['平日土休']}", {})
            d.setdefault(int(r["時"]), [0, 0])[0 if tag == "r1" else 1] += 1
    # 印の付いた分が final の発車の表にあるか
    missing = 0
    for r in r1:
        f = EXT / f"{r['表']}_{r['平日土休']}_final.csv"
        have = {(int(x["時"]), int(x["分"])) for x in _read(f)}
        missing += (int(r["時"]), int(r["分"])) not in have
    # ODPT チャレンジ枠の isOrigin と照らす(照合だけ)
    coll = {}
    for pdf, meta in TABLES.items():
        doc = json.loads((CHALLENGE / meta["challenge"]).read_text(encoding="utf-8"))
        orig: Counter = Counter()
        for tt in doc["data"]:
            cal = str(tt["odpt:calendar"]).split(":")[-1]
            for o in tt["odpt:stationTimetableObject"]:
                if o.get("odpt:isOrigin"):
                    h, m = map(int, str(o["odpt:departureTime"]).split(":"))
                    orig[(cal, h, m)] += 1
        mine = Counter((CAL_ODPT[r["平日土休"]], int(r["時"]), int(r["分"])) for r in r1 if r["表"] == meta["stem"])
        coll[meta["stem"]] = {"read1": sum(mine.values()), "challenge_isOrigin": sum(orig.values()),
                              "agree": sum((mine & orig).values()), "read1_only": sum((mine - orig).values()),
                              "challenge_only": sum((orig - mine).values())}
    summary = {
        "schema": "tt23c.origin_marks/1",
        "n_read1": len(r1), "n_read2": len(r2),
        "by_table_calendar": {f"{s}|{c}": {"read1": sum(1 for r in r1 if (r["表"], r["平日土休"]) == (s, c)),
                                           "read2": sum(1 for r in r2 if (r["表"], r["平日土休"]) == (s, c))}
                              for s in sorted({m["stem"] for m in TABLES.values()}) for c in ("平日", "土休")},
        "by_mark": {"read1": dict(sorted(Counter(r["印"] for r in r1).items())),
                    "read2": dict(sorted(Counter(r["印"] for r in r2).items()))},
        "diffs": [{"table": d["key"][0], "calendar": d["key"][1], "hour": d["key"][2], "what": d["what"]} for d in diffs],
        "hour_cells": {k: {str(h): v for h, v in sorted(d.items(), key=lambda kv: (kv[0] - 4) % 24)}
                       for k, d in sorted(hours.items())},
        "hour_cells_mismatch": sum(1 for d in hours.values() for v in d.values() if v[0] != v[1]),
        "marks_not_in_final_departures": missing,
        "collation_odpt_challenge_isOrigin": coll,
    }
    res = json.loads(RES.read_text(encoding="utf-8")) if RES.exists() else []
    resolved = {(x["表"], x["平日土休"], int(x["時"]), int(x["分"])): x for x in res}
    open_diffs = [d for d in diffs if d["key"] not in resolved]
    stale = [k for k in resolved if k not in {d["key"] for d in diffs}]
    summary["resolved"] = [{"table": k[0], "calendar": k[1], "hour": k[2], "adopt": v["採る"], "why": v["理由"]}
                           for k, v in sorted(resolved.items())]
    if a.record:
        Path(a.record).write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                  newline="\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "hour_cells"}, ensure_ascii=False))
    if open_diffs or missing or stale or any(v["採る"] != "read1" for v in resolved.values()):
        print(f"決着していない食い違い {len(open_diffs)}・final に無い分 {missing}・古い決着 {len(stale)}: final は書かない",
              file=sys.stderr)
        return 1
    rows = [[r["表"], r["平日土休"], r["時"], r["分"], r["印"], r["md5"], "1=2"] for r in sorted(r1, key=_order)]
    _write(OUTF, rows)
    print(f"final: {len(rows)} 行 → {OUTF.name}")
    return 0


def cmd_selftest(_a: argparse.Namespace) -> int:
    r2 = _read(OUT2)
    planted = [dict(r) for r in r2]
    del planted[3]
    planted[10]["印"] = "⑤" if planted[10]["印"] != "⑤" else "●"
    planted[20]["分"] = str((int(planted[20]["分"]) + 1) % 60)
    got = compare(r2, planted)
    whats = Counter(d["what"] for d in got)
    ok = whats["印"] == 1 and whats["count"] >= 2
    print("自己検査:", "OK" if ok else "NG", dict(whats))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("read1", "read2", "selftest"):
        sub.add_parser(name)
    sp = sub.add_parser("check")
    sp.add_argument("--record", default="")
    a = ap.parse_args(argv)
    return {"read1": cmd_read1, "read2": cmd_read2, "check": cmd_check, "selftest": cmd_selftest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
