"""R-110: 渋谷区の外国人人口を国籍・地域別に並べる(東京都 住民基本台帳による外国人人口 第3表)。

入力: data/research_cache/r110/tokyo_gaikoku_2026_ga26ev0300.csv(令和8年1月1日現在)
出力: 標準出力(上位の国籍・地域・人数・割合・男女)
使い方: リポの根から python docs/research/scripts/r110/shibuya_foreign_by_nationality.py
"""
import csv
import io
import sys

PATH = "data/research_cache/r110/tokyo_gaikoku_2026_ga26ev0300.csv"
REGION_COLS = {"アジア", "ヨーロッパ", "アフリカ", "北米", "南米", "オセアニア", "無国籍", "その他"}


def main(top: int = 20) -> None:
    text = open(PATH, "rb").read().decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    head = rows[0]
    row = next(r for r in rows if r[1] == "13113")
    total = int(row[3])
    print(f"渋谷区 総数 {total} 男 {row[4]} 女 {row[5]}")
    pairs = []
    for name, v in zip(head[6:], row[6:]):
        if not v.strip().lstrip("-").isdigit():
            continue
        if name in REGION_COLS or name.endswith("州"):
            print(f"  (大陸の小計) {name} {v}")
            continue
        pairs.append((int(v), name))
    pairs.sort(reverse=True)
    acc = 0
    for n, name in pairs[:top]:
        acc += n
        print(f"{name}\t{n}\t{n / total:.3f}\t累積 {acc / total:.3f}")
    print(f"国籍・地域の数(1 人以上) {sum(1 for n, _ in pairs if n > 0)}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
