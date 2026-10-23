"""R-99 A3: Economic Census 2021 table 6-2, 渋谷区: employees by industry (major) x status of employment (read only).

Reads data/research_cache/r99/ecensus2021_t6-2_industry_status_muni.xlsx and prints shares for 渋谷区 (13113).
Usage: python docs/research/scripts/r99/ecensus_status.py
"""
import os, sys
import openpyxl
sys.stdout.reconfigure(encoding="utf-8")
F = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "research_cache", "r99",
                 "ecensus2021_t6-2_industry_status_muni.xlsx")
def num(x):
    try: return float(x)
    except Exception: return 0.0
ws = openpyxl.load_workbook(F, read_only=True).worksheets[0]
cols = {"総数": 5, "個人業主": 8, "無給家族": 11, "有給役員": 14, "常用": 17, "無期": 20, "有期": 23, "臨時": 26}
print("columns:", list(cols))
for r in ws.iter_rows(min_row=10, values_only=True):
    area = str(r[1])
    if not (area.startswith("13113") or area.startswith("13000") or area.startswith("00000")): continue
    if str(r[2]) not in ("1", "2"): continue
    tot = num(r[5])
    if tot <= 0: continue
    parts = {k: num(r[c]) for k, c in cols.items()}
    print(f"{area[:12]:<12} lv{r[2]} {str(r[4])[:28]:<28} N={tot:>10.0f} " +
          " ".join(f"{k}={parts[k]/tot*100:5.1f}%" for k in ("個人業主", "無給家族", "有給役員", "無期", "有期", "臨時")))
