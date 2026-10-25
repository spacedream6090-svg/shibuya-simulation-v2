"""最小の xlsx 読み取り(openpyxl を入れずに標準ライブラリだけで先頭シートを行の配列にする)。R-86 用。"""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_rows(path: str, sheet: int = 1) -> list[list[object]]:
    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        root = ET.fromstring(z.read(f"xl/worksheets/sheet{sheet}.xml"))
        out: list[list[object]] = []
        for row in root.iter("{%s}row" % NS["m"]):
            cells: dict[int, object] = {}
            for c in row.findall("m:c", NS):
                v = c.find("m:v", NS)
                t = c.get("t")
                if t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter("{%s}t" % NS["m"]))
                elif v is None:
                    continue
                elif t == "s":
                    val = shared[int(v.text)]
                else:
                    val = v.text
                cells[_col_index(c.get("r"))] = val
            if cells:
                w = max(cells) + 1
                out.append([cells.get(i) for i in range(w)])
            else:
                out.append([])
        return out
