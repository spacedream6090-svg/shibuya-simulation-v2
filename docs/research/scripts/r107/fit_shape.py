"""R-107: 第4-22-1表の貯蓄現在高階級別の世帯分布に、ゼロの塊+対数正規を当てはめて形を見る。

ゼロの割合 = 100 − 貯蓄保有率(表の cat04=5)。正の部分は階級の度数から区間の尤度で
対数正規(mu, sigma)を最尤推定する(scipy が無ければ格子探索)。度数の比べを表で出す。
使い方: python fit_shape.py <CSV のパス>
"""
import csv
import io
import math
import sys

raw = open(sys.argv[1], encoding="utf-8-sig").read()
body = raw[raw.find('"VALUE"'):].split("\n", 1)[1]
rows = list(csv.DictReader(io.StringIO(body)))
v = {(r["tab_code"], r["cat01_code"], r["cat04_code"], r["cat05_code"]): r["value"] for r in rows}
edges = [0, 25, 50, 100, 150, 200, 300, 450, 600, 750, 900, 1200, 1500, 2000, 3000, 4000, 5000, 7500, 10000, math.inf]  # 万円
codes = [f"{i:02d}" for i in range(1, 20)]
Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))

def cdf(x, mu, s):
    if x <= 0:
        return 0.0
    if math.isinf(x):
        return 1.0
    return Phi((math.log(x) - mu) / s)

for c1, name in [("0", "総世帯"), ("1", "二人以上"), ("2", "単身")]:
    n = [float(v[("07-2024", c1, "0", c)]) for c in codes]
    tot = sum(n)
    p = [x / tot for x in n]
    zero = (100 - float(v[("05-2024", c1, "5", "00")])) / 100
    # 正の部分の度数: 最下位の階級からゼロの分を引く
    q = p[:]
    q[0] = max(p[0] - zero, 1e-9)
    qs = sum(q)
    q = [x / qs for x in q]
    best = None
    for mu100 in range(400, 900, 2):
        mu = mu100 / 100
        for s100 in range(50, 300, 2):
            s = s100 / 100
            ll = 0
            for i in range(19):
                pr = cdf(edges[i + 1], mu, s) - cdf(edges[i], mu, s)
                ll += q[i] * math.log(max(pr, 1e-12))
            if best is None or ll > best[0]:
                best = (ll, mu, s)
    ll, mu, s = best
    # 累積で中央値(線形補間・ゼロ込み)
    acc = 0
    med = None
    for i in range(19):
        if acc + p[i] >= 0.5:
            med = edges[i] + (0.5 - acc) / p[i] * (edges[i + 1] - edges[i])
            break
        acc += p[i]
    print(f"## {name}: 世帯 {tot:,.0f}・ゼロ(貯蓄保有率の補数) {zero*100:.1f}%・25 万円未満 {p[0]*100:.1f}%・中央値(ゼロ込み・補間) {med:.0f} 万円")
    print(f"   正の部分の対数正規: 中央値 exp(mu) = {math.exp(mu):.0f} 万円・sigma = {s:.2f}・平均の理論値 {math.exp(mu+s*s/2):.0f} 万円(表の平均 {float(v[('04-2024', c1, '21', '00')])/10:.0f} 万円)")
    print("   階級 | 実の割合(正の部分) | 当てはめ")
    for i in range(19):
        pr = cdf(edges[i + 1], mu, s) - cdf(edges[i], mu, s)
        print(f"   {edges[i]}-{edges[i+1]} | {q[i]*100:.1f} | {pr*100:.1f}")
