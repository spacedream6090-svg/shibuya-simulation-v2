"""R-110: 令和2年国勢調査 小地域集計 第2表(東京都 h02_13.csv)から渋谷区の町丁目別の外国人人口を出す。

入力: data/research_cache/r110/census2020_sa_h02_13_foreign.csv(cp932)
出力: 標準出力(区の総数・町丁目の外国人の割合の分布・上位 15 町丁目)
注意: 「人口(総数)」は日本人・外国人の別「不詳」を含む(表の注 1)。外国人の割合は不詳を含む総数で割った値。
使い方: リポの根から python docs/research/scripts/r110/shibuya_foreign_by_chome_2020.py
"""
import csv
import io
import statistics

PATH = "data/research_cache/r110/census2020_sa_h02_13_foreign.csv"


def num(x: str):
    x = x.strip().replace(",", "")
    return int(x) if x.lstrip("-").isdigit() else None


def main() -> None:
    text = open(PATH, "rb").read().decode("cp932")
    rows = [r for r in csv.reader(io.StringIO(text)) if len(r) > 14 and r[1] == "13113"]
    city = next(r for r in rows if r[3] == "1")
    tot, fr = num(city[11]), num(city[14])
    print(f"渋谷区 人口 {tot} 外国人 {fr} 割合 {fr / tot:.4f} 世帯 {city[15]}")
    # 地域階層: 1=区 / 2=丁目の無い町 / 3=丁目のある町の小計 / 4=丁目。最小の単位は 2 と 4。
    lvl = [r for r in rows if r[3] in ("2", "4")]
    shares, hidden = [], 0
    out = []
    for r in lvl:
        p, f = num(r[11]), num(r[14])
        if p is None or f is None or p == 0:
            hidden += 1
            continue
        shares.append(f / p)
        out.append((f, p, r[9] + r[10], r[4]))
    print(f"町丁目の数 {len(lvl)}(秘匿・合算・ゼロで除いた {hidden})")
    q = statistics.quantiles(shares, n=10)
    print(f"外国人の割合 中央値 {statistics.median(shares):.4f} 10%点 {q[0]:.4f} 90%点 {q[-1]:.4f} 最大 {max(shares):.4f}")
    out.sort(reverse=True)
    for f, p, name, flag in out[:15]:
        print(f"{name}\t外国人 {f}\t人口 {p}\t{f / p:.3f}\t秘匿 {flag}")
    print(f"町丁目の外国人の合計 {sum(o[0] for o in out)}")


if __name__ == "__main__":
    main()
