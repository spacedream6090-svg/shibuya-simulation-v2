import base64, re, sys, pathlib

# 検出パターン本文は秘匿情報(サーバー名・IP等)を含むためbase64格納
# (リポへの平文漏出とスキャン自己HITの回避)。
# パターン更新: python -c "import base64; print(base64.b64encode(r'<新パターン>'.encode()).decode())"
_B64 = "aWNsb3VkXC5jb218c3BhY2VkcmVhbVwuNjA5MHxbXHUwNDAwLVx1MDRmZlx1MDUwMC1cdTA1MmZdfDEwXC4xMFwuMFwuMTAyfGdwdS1zdi0wMDJ8dHN1a2Ftb3RvQHwxNTJcLjE2NVwuMTE3XC4xODc="
PAT = re.compile(base64.b64decode(_B64).decode("utf-8"))

hits = 0
for p in sys.argv[1:]:
    text = pathlib.Path(p).read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(text.splitlines(), 1):
        m = PAT.search(line)
        if m:
            hits += 1
            print(f"HIT {p}:{i}: {m.group(0)!r}")
if hits:
    print(f"FAIL: {hits} hits")
    sys.exit(1)
print("CLEAN")
