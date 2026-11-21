"""CLAUDE.md を軽くした前後の確かめ(11-22 §3-1 の 2)。

    python docs/bench/analysis/claude-md-slim-349/check_slim.py <旧 CLAUDE.md> <新 CLAUDE.md> [--table <出力.md>]

確かめること(どれか 1 つでも外れたら exit 1):

1. 対応表: 旧の、空でない行の全部に行き先がある(新の行か、「経緯へ」)。行き先の目印(新の行の頭の文字列)は、
   新の中にちょうど 1 行ある。
2. 固い語: 旧に出てくる「ドメインの名」「バッククォートで囲んだ語(コマンド・道・識別子)」は、新にも出てくる。
   出てこない語は、下の MOVED(経緯へ移した語と、その理由)に 1 つずつ書いてあるものだけ。
3. 写しの率(参考・合否にしない): 旧の行の 12 文字の並びのうち、新にもある割合。低い行は、経緯へ移した行か、
   書き直した行。対応表に並べて、人が見られるようにする。

出力の対応表(Markdown)は、history の文書と報告に貼る。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

H = "経緯へ"  # 行き先が history だけの印

# 旧の行番号 → 行き先(新の行の頭の文字列。括弧の半角と全角の違いに頼らないよう、括弧を含めない)。注は表に出す。
MAP: dict[int, tuple[list[str], str]] = {
    1: (["# CLAUDE.md"], ""),
    3: (["> 本書には決まりの文だけを置く"], "v1 の経緯の文は経緯へ。メモリの引き継ぎの道は残した"),
    5: (["## 1. プロジェクト概要"], ""),
    7: (["現実の渋谷を仮想空間上に再現する"], ""),
    9: ([H], "第一目標の改訂の出どころ(日付・承認・旧文の場所)"),
    11: (["> **第一目標:**"], ""),
    12: (["> **予見の形:**"], ""),
    13: (["> **確かめる順:**"], ""),
    14: (["> **住民の判断が要ることも確かめる:**"], ""),
    15: (["> **信用してよい範囲を一緒に出す:**"], ""),
    16: (["> 再現と、人間らしさ"], ""),
    18: (["## 2. 進め方の規律"], ""),
    20: (["1. **Q&A対話式**"], ""),
    21: (["2. **コード着手前の決定アジェンダ**"], "日付と出どころは経緯へ"),
    22: (["3. **拡張は先に聞く**"], ""),
    23: (["4. **毎回事前リサーチ**"], "日付と出どころは経緯へ"),
    24: (["5. **都度report**"], ""),
    25: (["6. **手段の検討と「拡張」の境界**"], "日付は経緯へ"),
    27: (["## 3. 世界観・設計ドクトリン"], ""),
    29: (["- **世界の状態と集約と破れない法則はエンジン"], "改訂の出どころと旧文の場所は経緯へ"),
    30: (["- 世界の変化は人の行動の結果として実装する"], "出どころは経緯へ"),
    31: (["- 実験の改変で世界に入れるのは「決定」だけ"], ""),
    32: (["- **自然界を模した仕組み志向**"], ""),
    33: (["- **ゲームは作らない**"], ""),
    34: (["- **DT定義**"], "改訂の出どころと旧文の場所は経緯へ"),
    35: (["- 憲法6原則・三層世界・認知3層は"], ""),
    37: (["## 4. 開発方法論"], ""),
    39: (["- v2-methodology.md の「全て強制」"], "改訂の出どころ・計器盤の古い写しの注は経緯へ(今の決まり=今の報告で足りる、を残した)"),
    41: (["- **パターン台帳ゲート**"], ""),
    42: (["- 全cap/近似に"], "改訂の印は経緯へ"),
    43: (["- 保存則系"], "日付は経緯へ"),
    44: (["- **性能予算"], ""),
    45: (["- 計算量は案を外す理由にしない"], "出どころは経緯へ"),
    46: (["- **版上げの運用**", "- **byte-check**"], "2 行に分けた。20 構成に足した経緯は経緯へ"),
    47: (["- 較正データとholdoutは最初に分割"], "創立時の文は経緯へ"),
    48: (["- 検証ランは短く"], ""),
    50: (["## 5. 体制"], ""),
    52: (["- **Fable 5.2"], "日付は経緯へ"),
    53: (["- サブエージェントは**コミット禁止**"], ""),
    54: (["- **Fable 5.2"], "「モデルの存在・ID は記憶で断言せず…」を上の行にまとめた(同じ文が 2 か所にあった)"),
    55: (["- リサーチサブは**子サブを起動しない**"], "根拠の事件の名は経緯へ"),
    56: (["- 一次確認には **写し検査**"], "根拠と訂正の出典は経緯へ"),
    57: (["- 研究役への発注文には"], "根拠の件は経緯へ"),
    58: (["- ファイルを消す・戻すコマンドは単独で"], "根拠の件は経緯へ"),
    60: (["## 6. 記録プロトコル"], ""),
    62: (["- **devlog**"], ""),
    63: (["- **台帳3ファイル**"], "09-28 の 5 節の並びは、10-25 の 3 区分に替わった旧規則=経緯へ。「決定した項は §1 から §2 へ移す」は、今の区分の名(判断待ち → 決定済みで実装待ち)で残した"),
    64: (["- **決定の写し**"], "出どころは経緯へ"),
    65: (["- **自律運転**"], "出どころは経緯へ"),
    66: (["- コミットメッセージは「第N 〜」形式", "- **Fable 5.2"], "「親のモデルが替わったら 2 か所を直す」は §5 の行へ。改訂の日付は経緯へ"),
    68: (["## 7. セキュリティ"], ""),
    70: (["- **秘密スキャン**"], ""),
    71: (["- APIキー"], ""),
    72: (["- **断られたら取りに行かない**"], "出どころは経緯へ"),
    73: (["- **「経路を変える」の範囲**", "1. 公開されている要旨の索引", "2. 発行元が断っていても", "3. web.archive.org・ミラー・キャッシュで",
          "4. curl などで頁を読むのは", "5. Web の道具が利用の上限に当たったら", "- **封印の層**"], "①〜⑤ を番号の行に分けた。出どころは経緯へ"),
    74: (["- `git add -A` 禁止"], ""),
    75: (["- 論文リンクは正規ドメイン", "- **政府・公的機関**", "- **取得の前に許可の一覧"], "緩和の日付は経緯へ"),
    76: (["- **`metro.tokyo.lg.jp` の下位のホスト**"], "出どころは経緯へ"),
    77: (["- **ODPT**", "- **G空間情報センターの公開バケット**", "- **Overpass API**", "- `api.openpoiapi.com`", "- **政府・公的機関**",
          "- **取得の前に許可の一覧"], "出どころは経緯へ"),
    78: (["- **駅の公式サイト**", "- **ユーザーが手で入手した時刻表・駅構内図**", "- geospatial.jp の点群の zip", "- 法人番号公表サイト",
          "- e-Stat の小地域の境界の zip", "- これ以外の zip・実行ファイル"], "各社の規約の確かめ(R-90・R-91)の中身と出どころは経緯へ(今の決まり=どのサイトからも取得しない、を残した)"),
    79: (["- データは無料か申請で得られるものだけ", "- **`huggingface.co` から取ってよい重み**", "- **pip", "- `3dcel.com`", "- **渋谷区のオープンデータ**",
          "- 都の土地利用現況調査の GIS の zip", "- 取得しないもの: cocoti", "- **商業施設の平面図**", "- **ユーザーが手で保存した平面図**"], "出どころは経緯へ"),
    80: (["- **渋谷区のオープンデータ**", "- 3dcel の点群の zip", "- **国土地理院**", "- `ecomo-rakuraku.jp`", "- **pip", "- Overture Maps Places",
          "- 自動で取得しないもの", "- **商業施設の平面図**"], "出どころは経緯へ"),
    81: (["- **WSL と艦隊**", "- **`huggingface.co` から取ってよい重み**", "- 重みの決まり", "- **ユーザーが手で保存した平面図**"], "出どころは経緯へ"),
    82: (["- **`huggingface.co` から取ってよい重み**", "- 重みの決まり"], "出どころは経緯へ"),
    83: (["- 都の区部点群", "- D1b の東京都の zip", "- **渋谷区のオープンデータ**", "- **天神の取得先**", "- 法人番号公表サイト",
          "- e-Stat の小地域の境界の zip", "- 自動で取得しないもの"], "出どころは経緯へ。「規約と robots を読んでから」「一覧と規約の要点を添えて」は天神の行に付けたまま"),
    84: (["- 文章の推敲スキル yomiyasu"], "写したときの確かめ(スクリプト 2 本を親が実読)と出どころは経緯へ"),
}

# 新にだけある行(11-22 に足した決まり)。行の頭の文字列 → 出どころ
ADDED: dict[str, str] = {
    "- **試験と CI の回し方**": "11-22 §3-2 の 1〜7",
    "- **トークンを減らす決まり**": "11-22 §3-1 の 1",
    "- **仕様書への写し**": "11-22 §3-1 の 4",
    "- **壁打ちの記録の読み方**": "11-22 §3-1 の 3",
    "- **`osf.io`**": "11-22 §2(段 1 の計画 D9)",
    "## 8. 手元の機械の負荷と、5070 の時間帯": "11-22 §3-3",
}

# 旧にあって新に無い固い語 → 理由。ここに無い語が新から消えていたら落ちる
MOVED: dict[str, str] = {}

_TICK = re.compile(r"`([^`\n]+)`")
_DOMAIN = re.compile(r"(?<![A-Za-z0-9_./-])((?:[A-Za-z0-9-]+\.)+(?:jp|org|com|io|biz|net|co|ai))(?![A-Za-z0-9-])")
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def norm(s: str) -> str:
    """比べるための正規化(括弧の半角と全角・空白の違いを無くす)。"""
    return s.replace("（", "(").replace("）", ")").replace("　", " ")


def hard_tokens(text: str) -> tuple[set[str], set[str]]:
    """(固い語, リンクの行き先)。リンクの行き先は出どころの文書なので、固い語から除く。"""
    links = set(_LINK.findall(text))
    no_links = _LINK.sub("]()", text)
    ticks = {norm(t.strip()) for t in _TICK.findall(no_links)}
    domains = set(_DOMAIN.findall(_TICK.sub(" ", no_links))) | {d for t in ticks for d in _DOMAIN.findall(t)}
    return ticks | domains, links


def shingle_rate(old_line: str, new_text: str, n: int = 12) -> float | None:
    s = re.sub(r"\s+", "", norm(old_line))
    if len(s) < n:
        return None
    grams = [s[i:i + n] for i in range(len(s) - n + 1)]
    hay = re.sub(r"\s+", "", norm(new_text))
    return sum(1 for g in grams if g in hay) / len(grams)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument("old", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--table", type=Path, default=None, help="対応表(Markdown)の出力先")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    old_text = args.old.read_bytes().decode("utf-8").replace("\r\n", "\n")
    new_text = args.new.read_bytes().decode("utf-8").replace("\r\n", "\n")
    old_lines = old_text.rstrip("\n").split("\n")
    new_lines = new_text.rstrip("\n").split("\n")
    problems: list[str] = []

    # 1. 対応表
    def find(anchor: str) -> int | None:
        hits = [i for i, line in enumerate(new_lines, start=1) if norm(line.strip()).startswith(norm(anchor))]
        if len(hits) != 1:
            problems.append(f"目印が新に {len(hits)} 行: {anchor!r}")
            return None
        return hits[0]

    rows: list[str] = ["| 旧の行 | 旧の行の頭 | 新の行 | 写しの率 | 注 |", "|---|---|---|---|---|"]
    used_new: set[int] = set()
    for i, line in enumerate(old_lines, start=1):
        if not line.strip():
            continue
        if i not in MAP:
            problems.append(f"旧の {i} 行目に行き先が無い")
            continue
        anchors, note = MAP[i]
        dest: list[str] = []
        for a in anchors:
            if a == H:
                dest.append(H)
                continue
            n = find(a)
            if n is not None:
                dest.append(str(n))
                used_new.add(n)
        rate = shingle_rate(line, new_text)
        head = norm(line.strip())[:24].replace("|", "/")
        rows.append(f"| {i} | {head} | {'・'.join(dest)} | {'' if rate is None else f'{rate:.0%}'} | {note} |")
    for k in MAP:
        if k > len(old_lines) or not old_lines[k - 1].strip():
            problems.append(f"対応表の {k} 行目は、旧では空か範囲の外")
    added_rows = ["| 新の行 | 足した決まり | 出どころ |", "|---|---|---|"]
    for a, src in ADDED.items():
        n = find(a)
        if n is not None:
            added_rows.append(f"| {n} | {norm(a).lstrip('-# ').strip('*')} | {src} |")

    # 2. 固い語
    old_tok, old_links = hard_tokens(old_text)
    new_tok, _ = hard_tokens(new_text)
    new_norm = norm(new_text)
    missing = sorted(t for t in old_tok if t not in new_tok and t not in new_norm)
    unexplained = [t for t in missing if t not in MOVED]
    stale = [t for t in MOVED if t not in missing]
    for t in unexplained:
        problems.append(f"固い語が新に無く、理由も無い: {t!r}")
    for t in stale:
        problems.append(f"MOVED にあるが、旧に無いか新にある: {t!r}")

    print(f"旧 {len(old_text.encode('utf-8'))} バイト・{len(old_lines)} 行 → 新 {len(new_text.encode('utf-8'))} バイト・{len(new_lines)} 行")
    print(f"旧の固い語 {len(old_tok)}(うち新にもある {len(old_tok) - len(missing)}・経緯へ移した {len(missing) - len(unexplained)}・理由なし {len(unexplained)})")
    print(f"旧のリンクの行き先 {len(old_links)} 本(出どころの文書。固い語に数えない)")
    if args.table:
        moved_rows = (["| 経緯へ移した固い語 | 理由 |", "|---|---|"] + [f"| `{t}` | {MOVED[t]} |" for t in missing if t in MOVED]
                      if missing else ["無し。台本が調べたのは、ドメインの名とバッククォートで囲んだ語だけ(旧の " + str(len(old_tok)) + " 個が今の CLAUDE.md に全部ある)。"
                                       "文として経緯へ移したもの(日付・承認の出どころ・理由・旧文の場所・各社の規約の確かめの中身など)は、上の表の「注」に書いた。"])
        out = "\n".join(["### 旧の行 → 今の行", "", *rows, "", "### 11-22 に足した決まり(旧に無い行)", "", *added_rows, "",
                         "### 今の CLAUDE.md に無い固い語(経緯へ移したもの)", "", *moved_rows]) + "\n"
        args.table.write_bytes(out.encode("utf-8"))
        print(f"対応表を書いた: {args.table.name}")
    for p in problems:
        print("NG:", p)
    print("結果:", "NG" if problems else "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
