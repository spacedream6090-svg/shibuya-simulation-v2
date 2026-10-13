import base64, re, sys, pathlib

# 検出パターン本文は秘匿情報(サーバー名・IP等)を含むためbase64格納
# (リポへの平文漏出とスキャン自己HITの回避)。
# パターン更新: python -c "import base64; print(base64.b64encode(r'<新パターン>'.encode()).decode())"
_B64 = "aWNsb3VkXC5jb218c3BhY2VkcmVhbVwuNjA5MHxbXHUwNDAwLVx1MDRmZlx1MDUwMC1cdTA1MmZdfDEwXC4xMFwuMFwuMTAyfGdwdS1zdi0wMDJ8dHN1a2Ftb3RvQHwxNTJcLjE2NVwuMTE3XC4xODc="
PAT = re.compile(base64.b64decode(_B64).decode("utf-8"))

hits = 0
for p in sys.argv[1:]:
    head = pathlib.Path(p).read_bytes()[:8192]
    if 0 in head:  # NUL を含む=PNG 等のバイナリ。文字化けが偽陽性になるので検査対象外(第202)
        print(f"SKIP binary {p}")
        continue
    raw = pathlib.Path(p).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:  # 〔第333〕cp932 のファイル(内閣府の祝日 CSV の fixture)は UTF-8 で読むと文字化けが偽陽性になる
            text = raw.decode("cp932")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        m = PAT.search(line)
        if m:
            hits += 1
            print(f"HIT {p}:{i}: {m.group(0)!r}")
if hits:
    print(f"FAIL: {hits} hits")
    sys.exit(1)
print("CLEAN")
