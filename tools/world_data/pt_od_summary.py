"""第6回東京都市圏PT 表d-1(目的種類別代表交通手段別OD表)の渋谷ゾーン集計(W12/D-W22用)。

入力: data/realworld/pt_tokyo/pt6_d-1_purpose_mode_od.csv(cp932・e-Stat配布そのまま)
      + 渋谷ゾーンコード(計画基本ゾーン4桁・H30_zonecode.xlsx から親が転記)
出力: (1) 渋谷着トリップの 目的種類×代表交通手段 行列(拡大トリップ数・構成比)
      (2) 発地の大ゾーン(頭2桁)別シェア=外界ノード(方面)重みの入力
      (3) 渋谷発 帰宅トリップの手段別(退場側)
決定論: 入力ファイルSHA256と引数を出力JSONに記録。ネットワーク不使用。
使い方: python tools/world_data/pt_od_summary.py --zones 1230 1231 --out docs/bench/pt_shibuya_summary.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import defaultdict
from pathlib import Path

SRC = Path("data/realworld/pt_tokyo/pt6_d-1_purpose_mode_od.csv")
MODES = ["鉄道", "バス", "自動車", "２輪車", "自転車", "徒歩", "その他", "不明", "計"]
PURPOSES = ["自宅－勤務", "自宅－通学", "自宅－業務", "自宅－私事", "帰宅", "勤務・業務", "私事", "不明", "計"]


def _num(s: str) -> int:
    s = s.replace(",", "").strip()
    return int(s) if s.isdigit() else 0


def _code(s: str) -> str:
    s = s.strip()
    return s[1:5] if s.startswith(":") and len(s) >= 5 and s[1:5].isdigit() else s


def load_rows(src: Path):
    raw = src.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    rows = list(csv.reader(io.StringIO(raw.decode("cp932"))))
    hdr_modes = rows[3][3:]
    assert hdr_modes == MODES, hdr_modes
    data = []
    for r in rows[5:]:
        if len(r) < 12:
            continue
        data.append((_code(r[0]), _code(r[1]), r[2].strip(), [_num(x) for x in r[3:12]]))
    return sha, data


def summarize(data, zones: set[str]):
    # (1) 着=渋谷: purpose x mode
    arr = defaultdict(lambda: [0] * 9)
    # (2) 発地の大ゾーン(頭2桁)別 (計行のみ)
    origin_big = defaultdict(int)
    origin_big_by_mode = defaultdict(lambda: [0] * 9)
    # (3) 発=渋谷 帰宅 by mode
    depart_home = [0] * 9
    internal = [0] * 9  # 渋谷内々
    def real(c: str) -> bool:  # 7000以降(東京区部/圏域計/全計/不明)と '0---' 型の集計コードを除外
        return c.isdigit() and int(c) < 7000

    for o, d, p, v in data:
        o_in, d_in = o in zones, d in zones
        if d_in and real(o):
            row = arr[p]
            for i in range(9):
                row[i] += v[i]
            if p == "計":
                origin_big[o[:2]] += v[8]
                ob = origin_big_by_mode[o[:2]]
                for i in range(9):
                    ob[i] += v[i]
            if o_in and p == "計":
                for i in range(9):
                    internal[i] += v[i]
        if o_in and p == "帰宅" and real(d):
            for i in range(9):
                depart_home[i] += v[i]
    total = arr["計"][8] if "計" in arr else 0
    purpose_share = {p: (arr[p][8] / total if total else 0.0) for p in PURPOSES if p != "計"}
    mode_share = {m: (arr["計"][i] / total if total else 0.0) for i, m in enumerate(MODES) if m != "計"}
    return {
        "arrive_purpose_x_mode": {p: dict(zip(MODES, arr[p])) for p in PURPOSES if p in arr},
        "arrive_total": total,
        "arrive_purpose_share": purpose_share,
        "arrive_mode_share": mode_share,
        "arrive_internal(発着とも渋谷)": dict(zip(MODES, internal)),
        "origin_bigzone_share": {k: v / total for k, v in sorted(origin_big.items(), key=lambda x: -x[1])} if total else {},
        "origin_bigzone_by_mode": {k: dict(zip(MODES, v)) for k, v in origin_big_by_mode.items()},
        "depart_home_by_mode": dict(zip(MODES, depart_home)),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zones", nargs="+", required=True, help="渋谷の計画基本ゾーン4桁コード")
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    sha, data = load_rows(Path(a.src))
    res = summarize(data, set(a.zones))
    out = {"source": a.src, "source_sha256": sha, "zones": sorted(a.zones), "survey": "第6回東京都市圏PT(2018・平日1日・拡大トリップ)", **res}
    js = json.dumps(out, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(js, encoding="utf-8")
    print(js)


if __name__ == "__main__":
    main()
