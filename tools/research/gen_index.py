# -*- coding: utf-8 -*-
"""INDEX.md を rows.json から生成(第191)。"""
import io, json, os
from collections import defaultdict

SC = os.path.dirname(os.path.abspath(__file__))  # rows.json は本スクリプトと同じ場所
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
rows = json.load(io.open(os.path.join(SC, 'rows.json'), encoding='utf-8'))
import importlib.util
spec = importlib.util.spec_from_file_location('bi', os.path.join(SC, 'build_index.py'))
bi = importlib.util.module_from_spec(spec); spec.loader.exec_module(bi)
F, GRADE = bi.F, bi.GRADE

GLABEL = {'A': 'A 親検収済', 'B': 'B 出典あり・空欄明示', 'C': 'C 出典あり・空欄未整理',
          'D': 'D 出典 URL なし', 'E': 'E 出典不要'}
PORDER = {'P0': 0, 'P1': 1, 'P2': 2}

o = []
w = o.append
w('# 答申の索引(docs/research/ 73 本)\n')
w('> 作成 2026-09-15(第191)。ユーザー指示 09-15「リサーチをした v2 のレポートも見やすくしてほしい/全部にヘッダを入れたい」。')
w('> **v1 には `docs/references.md` と `docs/research-scope.md` があったが、v2 には索引が一つも無かった**。本書がその位置。')
w('> 各答申の**文言は一行も変えていない**。頭に 3 行のヘッダ(`<!-- hdr:v1 -->`)を足しただけ(空行が 3 連続していた 14 本で空行 1 行が詰まったのが唯一の差分)。設計書からの参照は全部生きている。')
w('> 分野番号は [分野地図](v2-discipline-map.md) の 32 分野。**分野と重要度は親(Opus 5)の判断**であって、答申自身の申告ではない。\n')

w('## 0. 一次確認の等級(このヘッダで一番大事な欄)\n')
w('| 等級 | 意味 | 本数 |')
w('|---|---|---|')
cnt = defaultdict(int)
for r in rows:
    cnt[r['g']] += 1
for g in 'ABCDE':
    w(f"| **{g}** | {GRADE[g]} | {cnt[g]} |")
w('')
w('判定は機械的に行った(出典痕跡 = URL + arXiv ID + DOI + ✔ + 「著者 年」表記の総数)。')
w('例外は 4 本だけ親が中身を見て上書きした(理由は各ファイルのヘッダに書いてある)。\n')

# --- §1 警告 ---
d_rows = sorted([r for r in rows if r['g'] == 'D'], key=lambda r: (PORDER[r['pri']], r['dt']))
w('---\n')
w('## 1. 最重要 — 33 本は出典 URL を 1 つも持っていない\n')
w('**2026-08-30〜09-01 に書かれた 33 本すべてが URL 0 件**。出典痕跡の合計も 0〜17 件(9 本は完全にゼロ)。')
w('これに対し **09-02 以降の 40 本は出典痕跡の中央値が 62 件**。桁が違う。\n')
w('この断層には理由がある。**2026-09-03 に「サブ捏造申告事件」(孫サブの沈黙 → 親サブが出典を捏造)が起きて、')
w('CLAUDE.md §5 に「リサーチサブは子サブを起動しない」「答申の出典・数値・条番号は正典化前に親が一次確認する」が追加された**。')
w('33 本はその規律が入る**前**のバッチにあたる。\n')
w('> **扱い**: 中身が間違っていると決まったわけではない。しかし **これらを根拠に新しい決定をしてはいけない**。')
w('> 使うときは、その数値だけを一次確認してから使う。題名に「全出典URL付き」とあるものも含めて、ファイル内に URL は無い。\n')
w('| 重要度 | 答申 | 行 | 痕跡 | 分野 |')
w('|---|---|---|---|---|')
for r in d_rows:
    w(f"| {r['pri']} | [{r['fn'][:-3]}]({r['fn']}) | {r['n']} | {r['tr']} | {r['fstr']} |")
w('')
p0d = [r for r in d_rows if r['pri'] == 'P0']
w(f'**このうち P0 は {len(p0d)} 本**' + ('。' if not p0d else ': ' + ' / '.join(r['fn'][:-3] for r in p0d) + '。'))
w('→ 残務台帳 [research-backlog.md](research-backlog.md) の **R-23** として新規に登録した。\n')

# --- §2 分野別 ---
w('---\n')
w('## 2. 分野別の索引(32 分野)\n')
byf = defaultdict(list)
for r in rows:
    for i in r['fields']:
        byf[i].append(r)
w('| # | 分野 | 答申 | 最良の等級 |')
w('|---|---|---|---|')
for i in range(1, 33):
    rs = sorted(byf.get(i, []), key=lambda r: (PORDER[r['pri']], r['fn']))
    if not rs:
        w(f"| {i} | **{F[i]}** | **なし** | — |")
        continue
    best = min(r['g'] for r in rs)
    names = ' ・ '.join(f"[{r['fn'][:-3].replace('v2-','')}]({r['fn']}) {r['pri']}" for r in rs)
    w(f"| {i} | **{F[i]}** | {names} | {best} |")
w('')
none = [i for i in range(1, 33) if not byf.get(i)]
w(f'**答申が 1 本も無い分野: {len(none)} 個** — ' + ' / '.join(f'{F[i]} #{i}' for i in none))
w('\n第180 の照合では「答申が無い 4 分野」としていたが、索引を作って数え直すと上のとおり。')
w('差は、第180 が「主題として扱った答申」を数え、本索引が「その分野に紐づく答申」を数えているため。\n')

# --- §3 全件 ---
w('---\n')
w('## 3. 全 73 本(重要度 → 日付順)\n')
w(f"合計 {sum(r['n'] for r in rows):,} 行。P0 {sum(1 for r in rows if r['pri']=='P0')} / "
  f"P1 {sum(1 for r in rows if r['pri']=='P1')} / P2 {sum(1 for r in rows if r['pri']=='P2')}。\n")
for pri in ('P0', 'P1', 'P2'):
    rs = sorted([r for r in rows if r['pri'] == pri], key=lambda r: r['dt'])
    w(f'### {pri}({len(rs)} 本)\n')
    w('| 日付 | 答申 | 行 | 一次確認 | 分野 | 役割 |')
    w('|---|---|---|---|---|---|')
    for r in rs:
        w(f"| {r['dt'][5:]} | [{r['fn'][:-3].replace('v2-','')}]({r['fn']}) | {r['n']} | **{r['g']}** | {r['fstr']} | {r['role']} |")
    w('')

# --- §4 使い方 ---
w('---\n')
w('## 4. 使い方\n')
w('- **新しい決定の根拠にする前に、その答申の等級を見る**。D なら使わない(その数値だけ一次確認してから使う)。')
w('- 答申を読み直したら、その論文のメモを [lit/](lit/) へ 1 論文 1 ファイルで切り出す(v1 の `docs/lit/` 形式)。')
w('- 空欄が見つかったら [research-backlog.md](research-backlog.md) へ写す(答申の中に埋めない)。')
w('- ヘッダは `<!-- hdr:v1 -->` で機械可読。再生成は `python tools/research/build_index.py && python tools/research/gen_index.py`(二重挿入しない)。')
w('- **この索引は自動生成物**。答申を足したら再生成する。手で編集しない。\n')
w('## 5. まだやっていないこと(次のエージェントへ)\n')
w('- **「効いた決定」の欄が無い**。どの答申がどの DECIDED 行の根拠かは、決定台帳 [v2-redesign.md](../design/v2-redesign.md) 側からしか辿れない。逆引き表は未作成。')
w('- **C 等級 1 本**(ad-information)は空欄節が無いだけで、空欄が無い保証はない。読んで判定する。')
w('- **D 等級 33 本の中身の真偽は未検証**。R-23 参照。')
w('- 分野の紐づけは題名と対象決定からの親の判断。本文を読んで付け直す価値はある。')

io.open(os.path.join(REPO, 'docs', 'research', 'INDEX.md'), 'w', encoding='utf-8').write('\n'.join(o) + '\n')
print('INDEX.md', len(o), 'lines')
