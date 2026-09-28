"""活動選択の事前分布(D-119 L2・5 段目 5b)の錨を **追跡ファイル**へ書き出す(決定論)。

入力: ``data/calib/hunger/ssb2021_jikantai_t8-{1,2,3}_*.xlsx``(gitignore 下・令和3年社会生活基本調査
時間帯編 第8-1/8-2/8-3表=曜日,男女,ふだんの就業状態,行動の種類,年齢,時刻区分別行動者率(15歳以上))。
出力: ``docs/bench/anchors/ssb2021_activity_prior_v0.json``(追跡)。**エンジンとテストはこの追跡
ファイルだけを読む**(data/ が無い機械でも動く)。

**openpyxl はエンジンの .venv に無い**ので、この builder だけはシステムの python(openpyxl あり)で回す::

    python tools/hunger/build_activity_prior.py            # 生成して上書き(3 表で約 1 分)
    python tools/hunger/build_activity_prior.py --check    # 生成物と追跡ファイルが一致するか(exit 1=不一致)

中身は **数値と符号だけ**(行動の種類・地域・年齢は原表の符号 ``01``〜``20``・``00``/``03``・``01``〜``15``。
表の文言=行動名の和文は入れない)。行動者率は % × 100 の整数(原表は小数 2 桁)。原表の記号「-」
(行動者皆無/サンプル皆無)は 0。層(性 × 就業状態 × 年齢)ごとに原表の「00_総数」行の推定人口[千人]と
サンプルサイズを添える(0 の層=サンプル皆無→エンジンは年齢総数の行へ落とす)。

採る範囲(宣言): 行動 01〜20 から **03 食事を除く 19 種**(K6 (i)=食事は事前分布に含めない)・
性 1 男 / 2 女・就業 1 有業者 / 2 無業者(総数の列は採らない)・年齢 01_15〜19 歳 … 15_85 歳以上+00_総数
(再掲は採らない)・時刻 96 区分。地域 × 曜日 = 平日: 00_全国・03_関東大都市圏 / 土曜・日曜: 03_関東大都市圏
のみ(ファイルの大きさの宣言=全国の土日は要るときに足す)。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SRC_DIR = REPO / "data" / "calib" / "hunger"
OUT = REPO / "docs" / "bench" / "anchors" / "ssb2021_activity_prior_v0.json"
SCHEMA = "shibuya.anchors/ssb2021-activity-prior/v0"
ATTRIBUTION = "「令和3年社会生活基本調査結果」(総務省統計局)を加工して作成"

#: (曜日の鍵, ファイル, シート, statInfId, 採る地域の符号)
TABLES = (
    ("weekday", "ssb2021_jikantai_t8-1_weekday.xlsx", "a008_1", "000032224341", ("00", "03")),
    ("saturday", "ssb2021_jikantai_t8-2_saturday.xlsx", "a008_2", "000032224342", ("03",)),
    ("sunday", "ssb2021_jikantai_t8-3_sunday.xlsx", "a008_3", "000032224343", ("03",)),
)
URL = "https://www.e-stat.go.jp/stat-search/file-download?statInfId={sid}&fileKind=0"
ACTIVITY_CODES = tuple(f"{i:02d}" for i in range(1, 21) if i != 3)
EXCLUDED = ("03",)
AGE_CODES = tuple(f"{i:02d}" for i in range(1, 16))
AGE_LO = (15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85)
SEX_CODES = ("1", "2")
EMP_CODES = ("1", "2")
N_SLOTS = 96
FIRST_RATE_COL = 7  # 0 起点: A 曜日・B 地域・C 男女・D 就業・E 行動・F 年齢・G 推定人口・H.. 行動者率
SAMPLE_COL = 103


def _code(cell: Any) -> str:
    return str(cell).split("_", 1)[0] if cell is not None else ""


def _rate(v: Any) -> int:
    if v is None or isinstance(v, str):
        return 0  # 「-」
    return int(round(float(v) * 100))


def read_table(path: Path, sheet: str, regions: tuple[str, ...]) -> dict[str, Any]:
    import openpyxl  # システムの python にだけある

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    out: dict[str, Any] = {r: {} for r in regions}
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        if i < 10:
            continue
        reg, sex, emp, act, age = (_code(row[1]), _code(row[2]), _code(row[3]), _code(row[4]),
                                   _code(row[5]))
        if reg not in out or sex not in SEX_CODES or emp not in EMP_CODES:
            continue
        if age != "00" and age not in AGE_CODES:
            continue  # 再掲(R1〜R6)は採らない
        key = f"{sex}-{emp}"
        stratum = out[reg].setdefault(key, {}).setdefault(
            age, {"xlsx_row": None, "pop_k": 0, "sample": 0, "rates": {}}
        )
        if act == "00":  # 行動の総数の行=推定人口とサンプルサイズ
            stratum["xlsx_row"] = i
            stratum["pop_k"] = 0 if isinstance(row[6], str) or row[6] is None else int(row[6])
            s = row[SAMPLE_COL] if len(row) > SAMPLE_COL else None
            stratum["sample"] = 0 if isinstance(s, str) or s is None else int(s)
            continue
        if act not in ACTIVITY_CODES:
            continue  # 03 食事・再掲(R1〜R3)は採らない
        vals = row[FIRST_RATE_COL:FIRST_RATE_COL + N_SLOTS]
        if len(vals) != N_SLOTS:
            raise SystemExit(f"{path.name} 行 {i}: 96 区分でない")
        stratum["rates"][act] = [_rate(v) for v in vals]
    wb.close()
    # 並びを固定(行動は ACTIVITY_CODES の順の配列にする)
    fixed: dict[str, Any] = {}
    for reg in regions:
        fixed[reg] = {}
        for key in (f"{s}-{e}" for s in SEX_CODES for e in EMP_CODES):
            fixed[reg][key] = {}
            for age in ("00",) + AGE_CODES:
                st = out[reg][key][age]
                missing = [a for a in ACTIVITY_CODES if a not in st["rates"]]
                if missing:
                    raise SystemExit(f"{path.name} {reg} {key} {age}: 行動の行が無い {missing}")
                fixed[reg][key][age] = {
                    "xlsx_row": st["xlsx_row"], "pop_k": st["pop_k"], "sample": st["sample"],
                    "rates": [st["rates"][a] for a in ACTIVITY_CODES],
                }
    return fixed


def build() -> dict[str, Any]:
    sources: dict[str, Any] = {}
    tables: dict[str, Any] = {}
    for day, fname, sheet, sid, regions in TABLES:
        path = SRC_DIR / fname
        sources[day] = {"file": fname, "sheet": sheet, "statInfId": sid, "url": URL.format(sid=sid),
                        "md5": hashlib.md5(path.read_bytes()).hexdigest(), "regions": list(regions)}
        tables[day] = read_table(path, sheet, regions)
    return {
        "schema": SCHEMA,
        "generated_by": "tools/hunger/build_activity_prior.py",
        "attribution": [ATTRIBUTION],
        "usage": "D-119 L2 activity prior P(activity | 15-min slot, day, sex, age, employment) "
                 "(meal code 03 excluded by K6 (i)); rates are percent x 100 of people doing "
                 "the activity in the slot; symbol '-' is stored as 0",
        "sources": sources,
        "slot_minutes": 15,
        "n_slots": N_SLOTS,
        "activity_codes": list(ACTIVITY_CODES),
        "excluded_activity_codes": list(EXCLUDED),
        "age_codes": list(AGE_CODES),
        "age_lo": list(AGE_LO),
        "age_total_code": "00",
        "strata_keys": "sex-employment (sex 1 male / 2 female; employment 1 employed / 2 not employed)",
        "region_codes": {"00": "national", "03": "kanto_major_metro"},
        "tables": tables,
    }


def dumps(obj: dict[str, Any]) -> str:
    # 96 値の配列は 1 行に(読める形で・大きさを抑える)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D-119 5b の活動の事前分布を追跡ファイルへ書く")
    ap.add_argument("--check", action="store_true", help="追跡ファイルと一致するかだけ見る")
    args = ap.parse_args(argv)
    text = dumps(build())
    if args.check:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != text:
            print("不一致: 追跡ファイルは再生成が要る")
            return 1
        print("一致")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(text.encode("utf-8"))
    print(f"書いた: {OUT.relative_to(REPO).as_posix()} ({len(text.encode('utf-8')):,} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
