"""R-107: J-FLEC「家計の金融行動に関する世論調査 2025年」各種分類別データ(xlsx)の
シート 25・26(金額別の主な資金決済手段)と 28(平均手持ち現金残高)の、全国と世帯主の年齢別の行を出す。

j-flec.go.jp は取得の許可の一覧の外なので、ファイルは保存せず標準入力から読むだけ:
  curl -s -L https://j-flec.go.jp/wpimages/uploads/per12501.xlsx | python jflec_pay.py
"""
import io
import sys

import openpyxl

wb = openpyxl.load_workbook(io.BytesIO(sys.stdin.buffer.read()), read_only=True, data_only=True)
for sh in ["25", "26", "28"]:
    ws = wb[sh]
    print(f"### シート {sh}")
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        r = [c for c in r if c is not None]
        if not r:
            continue
        lab = " ".join(str(x) for x in r[:2])
        if i <= 8 or "歳代" in lab or "年令別" in lab:
            print(i, r[:22])
        if "就業先" in lab:
            break
