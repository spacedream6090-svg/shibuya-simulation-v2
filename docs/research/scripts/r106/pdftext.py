"""R-106: URL の PDF を標準入力から読み、本文を標準出力に出す(保存しない)。
使い方: curl -sL <URL> | python pdftext.py [最大字数] [頁の範囲 例 0-3]"""
import sys, fitz
data = sys.stdin.buffer.read()
doc = fitz.open(stream=data, filetype="pdf")
mx = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
rng = sys.argv[2] if len(sys.argv) > 2 else None
pages = range(len(doc))
if rng:
    a, b = rng.split("-"); pages = range(int(a), min(int(b) + 1, len(doc)))
out = []
for i in pages:
    out.append(f"[p{i+1}] " + doc[i].get_text())
txt = "\n".join(out)
print("pages:", len(doc)); print(txt[:mx])
