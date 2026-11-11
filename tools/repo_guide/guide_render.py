# -*- coding: utf-8 -*-
"""事実の表からカードの Markdown を作る(並びは sort・時刻なし・絶対パスなし・行番号なし)。"""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field

from guide_facts import FileFacts, ModuleIndex, decision_sort_key, module_label
from guide_permits import RESOLVE_FILE, LEDGER_FILE, Permits, Row, System

CARDS_REL = "docs/reference/repo-guide/cards"
GENERATED = "自動生成(手で編集しない): `python tools/repo_guide/build.py`"

RULES = """## 読み方の規則

カードは `tools/repo_guide/build.py` が作る。対象のコードは import も実行もせず、AST と本文の文字列だけを読む。空の欄は載せない。

- **対象**: `git ls-files --cached --others --exclude-standard` の一覧(`.git` が無ければディレクトリを歩く)。カードを載せるのは `.py` だけで、ほかのファイルは名前だけを「その他のファイル」に載せる。
- **冒頭の説明**: モジュールの docstring の最初の段落。折り返しは 1 行に戻す。
- **公開の関数とクラス**: 頂上(`if`・`try`・`with` の中を含む)の `def`・`class` で `_` で始まらないもの。名前と docstring の 1 行目。メソッドは載せない。`__all__` では絞らない。
- **import**: 関数の中を含む全部の `import`・`from … import`・`import_module("文字列")` のうち、リポの中のファイルに解けるもの。`from M import a` は `M/a` が在ればそれ、無ければ `M`。tests と tools の素の名前は、同じディレクトリと、`sys.path` に足すディレクトリから探す。パッケージの中のファイルは、いちばん外のパッケージの 1 つ上のディレクトリからも探す。足す所は、そのファイルと祖先の conftest と囲むパッケージの `__init__.py` と、そこから import する内部モジュール(推移的)の `sys.path.insert`・`append`・`syspath_prepend`。足す先の式は `__file__`・`.parent`・`.parents[n]`・`os.path.dirname`・`os.path.join`・`/`・`.joinpath`・代入と `for` の変数の値の和を読む。読めない呼び出しは「`sys.path` に足す先を読めない所 N か所」と数だけ載せる。同じ名が複数の場所にあれば、この探す順で最初のものに解く(実行時の順と違うことがある)。解けなかった素の import のうち、tests と tools に同じ名のファイルが 1 つだけあるものは「解けない素の import」と載せる。再輸出はたどらない。
- **呼び手**: このファイルを import している src と tools のファイル。
- **読む試験**: このファイルを import している tests のファイル(直接だけ)。「道筋で」は、試験が `ROOT / "tools" / "x.py"` や文字列 `"tools/x.py"` でファイルを指すもの(`importlib`・AST・`subprocess` で読む形を拾う。`src/shibuya/` を省いた道筋も引く。docstring は数えない)。実際に読むかまでは確かめない。
- **状態台帳の行**: `engine/state_ledger.py` の表(`_SOA`・`_EXT`)を AST で読む。外の状態の行の持ち主は、道筋の最も長い前方が `OWNER_CLASSES` にあるクラス(1 行の道筋が複数の持ち主に分かれれば、それぞれに載せる)。`OWNER_ALT_CLASSES` は「別のクラス」として名前だけ載せる。SoA の列の持ち主は `state_ledger_ast.DECL_FILES` の宣言のファイル。持ち主を引けない行は `engine/state_ledger.py` のカードに載せる。行番号を含む根拠の欄は載せない。
- **書きの許可**: `engine/systems/table.py` の `SYSTEMS` を AST で読む。系の欄は系の関数のあるファイルのカードに載せる。`writes.soa` は `resolve_ops` の静的な閉包で、`systems/allow.py` の規則を AST の上でなぞって作る(閉包は上限=同じ名の列が余分に入る。規則の限界は allow.py の docstring)。台帳の行の「書ける系」は、外の状態なら宣言 `writes.paths` の照合(`spec.path_allowed` と同じ)、SoA の列なら `writes.soa` に入る系。`engine/resolve.py` のカードには関数ごとの直接の書きと、その口を `resolve_ops` に持つ系を載せる。実行時に許可が効くのはこの宣言(`systems/guard.py`)だが、カードは宣言を写すだけで、実際の書きを確かめない。
- **CLI の引数**: 呼び出しの名が `add_argument`・`add_parser` のもの。旗の名と help の 1 行は、文字列か頂上の文字列の定数のときだけ読む。名前を読めない呼び出しは数だけ出し、help が定数でない旗には「(help を読めない)」と書く。`sys.argv` を直接読むファイルには印を付ける。サブコマンドと旗は別々に名前の順で並べるだけで、どの旗がどのサブコマンドのものかは区別しない。
- **環境変数**: `os.environ[…]`・`os.environ.get/pop/setdefault`・`K in os.environ`・`os.getenv`(`from os import …` と `x = os.environ` の別名を含む)。名前は文字列か頂上の文字列の定数のときだけ読む。読めない所は数だけ、`os.environ` をまるごと渡す所には印を付ける。これに加えて、文字列の全体が `SHIBUYA_…` のものはこのリポの環境変数の名前として載せる(`ENV = "SHIBUYA_X"` と `os.environ.get(name)` に分かれる形を拾う。読み手とは限らず、試験の `setenv` も入る)。
- **決定の ID**: ファイルの本文の全部(docstring・コメント・文字列)を正規表現で読む。機械的な読みなので、意味は原文で確かめる。
  - 指示書と回答: `tools/decision_index.py` の `DOCS` の接頭。`接頭/ID`(`11-01/A1-2`)・`接頭 §番号`(`10-25 §2-5` → `10-25/§2-5` と書く)・接頭だけ(`10-13b`)。前に数字・`-`・`/`・`.`・`:`・英字があれば拾わない(`2026-10-12` は拾わない)。`10-12` のような数の範囲は誤って拾うことがある。
  - 答申 `R-126`・旧の決定 `D-74`。
  - devlog の番号 `第 N`。3 桁以上だけ拾う(2 桁以下はコードでは第 1 期・第 2 波・第 1 陣・第 31 表のような序数がほとんどで、本物の番号でも拾わない)。後ろが助数の語(期・部・回・章・節・条・号・表・種・位・次・項・版・週・日・月・年・図・案・世代・者・類・陣・波・弾・批・系)か `-数字` なら拾わない(`第340 段 2`・`第170 層2` は拾う)。`第 1 期 1-8` の形の計画の番号は載せない。
  - 別の文書の中の項目の番号 `#N`(1〜9999)。前の接頭につながるものだけを、接頭と一緒に載せる: `11-02r §1 #7` → `11-02r/§1 #7`・`R-116 §1-4(#46` → `R-116 §1-4 #46`・`第275 #4` → `第 275 #4`。接頭は指示書と回答(`/ID`・`§番号` つき可)・`R-N`(`§番号` つき可)・`D-N`・3 桁以上の `第 N`。間に空白と開き括弧だけを許す。続きの `・#8`・`、#8`・`〜#18` は同じ接頭につなぐ(範囲は両端だけ)。つながらない `#N`(`routing #74`・`第275 親の決め #2`・`"#333"` の色)は拾わない。
  - 接頭のない `K15`・`CA1` は拾わない(同じ ID が複数の原文にある。`docs/design/decision-id-index.md` の「衝突」)。
- **説明文のリンクの形**: docstring・help・見出し・台帳の行の名の `](` は、コードの囲みの外なら `]\\(` に逃がす(カードの中でリンクにならないように)。
- **伏せた語**: `tools/scan_secrets.py` と `tools/commit_check.py` の検出パターンに当たる語は `〔伏〕` に置き換える(docstring の写しが検査に当たらないように)。
- **CI**: `build.py --check` は src・tests・tools のカードだけを作り直して比べる(入口の索引と docs・data の索引は比べない)。未追跡のファイルもカードに載る(新しいファイルを見落とさないため)。build と `--check` は「未追跡 N 本を含む」と一覧を標準出力に出すので、CI と食い違うときはそれを見る。
- **data**: `data/` の中のファイルは 1 本も開かない。`os.scandir` の名前と stat の大きさだけを使い、深さ 2 段までのディレクトリを載せる(大きさは下の全部の合計)。
"""


@dataclass
class DirCard:
    rel: str
    py_files: list[str] = field(default_factory=list)
    other_files: list[str] = field(default_factory=list)
    subdirs: list[str] = field(default_factory=list)


_CODE_SPAN = re.compile(r"(``.+?``|`[^`]*`)")


def escape_links(text: str) -> str:
    """説明文の ``](`` を ``]\\(`` にする(コードの囲みの中はそのまま)。"""
    parts = _CODE_SPAN.split(text)
    return "".join(p if i % 2 else p.replace("](", "]\\(") for i, p in enumerate(parts))


def card_path(dir_rel: str) -> str:
    """ディレクトリのカードの道筋(リポから)。"""
    return f"{CARDS_REL}/{dir_rel}/README.md"


def _rel_link(target: str, card_dir: str) -> str:
    return posixpath.relpath(target, start=card_dir)


def build_dir_table(all_files: list[str], py_files: set[str]) -> dict[str, DirCard]:
    dirs: dict[str, DirCard] = {}

    def ensure(d: str) -> DirCard:
        if d not in dirs:
            dirs[d] = DirCard(rel=d)
            if "/" in d:
                parent = d.rsplit("/", 1)[0]
                ensure(parent).subdirs.append(d)
        return dirs[d]

    for f in sorted(all_files):
        d, _, _name = f.rpartition("/")
        card = ensure(d)
        (card.py_files if f in py_files else card.other_files).append(f)
    for c in dirs.values():
        c.subdirs.sort()
    return dirs


def _code_join(names: list[str]) -> str:
    return "・".join(f"`{n}`" for n in names)


def _row_line(r: Row, items: tuple[str, ...], writers: set[str]) -> str:
    marks = [f"挙動 {r.behavior}", f"復元 {r.restore}"]
    if r.arm:
        marks.append(f"腕 {r.arm}")
    if r.dead:
        marks.append("死蔵")
    line = f"`{r.key}` {escape_links(r.name)}({'・'.join(marks)})"
    if items:
        line += f" 道筋 {_code_join(sorted(items))}"
    line += " 書ける系: " + ("・".join(sorted(writers)) if writers else "(宣言なし)")
    return line


def ledger_lines_by_file(p: Permits) -> dict[str, list[str]]:
    """ファイル → カードに載せる台帳の行(持ち主ごとに鍵の順)。"""
    per_file: dict[str, dict[str, list[tuple[str, str]]]] = {}

    def add(path: str, group: str, key: str, line: str) -> None:
        per_file.setdefault(path, {}).setdefault(group, []).append((key, line))

    for r in p.rows:
        if r.place in p.soa_files:
            add(p.soa_files[r.place], f"SoA の列 `{r.place}`", r.key, _row_line(r, (), p.writers_of_soa(r.key)))
            continue
        by_owner: dict[str, list[str]] = {}
        for it in r.items:
            o = p.owner_of(it)
            if o is not None:
                by_owner.setdefault(o, []).append(it)
        for o, items in by_owner.items():
            writers: set[str] = set()
            for it in items:
                writers |= p.writers_of_item(r.key, it)
            path, cls = p.owners[o]
            add(path, f"持ち主 `{o}`(`{cls}`)", r.key, _row_line(r, tuple(items), writers))
    out: dict[str, list[str]] = {}
    for path, groups in per_file.items():
        lines: list[str] = []
        for g in sorted(groups):
            lines.append(f"  - {g}")
            lines.extend(f"    - {line}" for _, line in sorted(groups[g], key=lambda x: decision_natural(x[0])))
        out[path] = lines
    for owner, alts in sorted(p.alts.items()):
        for path, cls in alts:
            main_path = p.owners.get(owner, ("", ""))[0]
            out.setdefault(path, []).append(
                f"  - 持ち主 `{owner}` の別のクラス `{cls}`(行は `{module_label(main_path)}` のカードを見る)")
    unowned = p.unowned_rows()
    if unowned:
        lines = out.setdefault(LEDGER_FILE, [])
        lines.append("  - 持ち主を引けない行(道筋が `OWNER_CLASSES` に無い・道筋なし)")
        for r, miss in sorted(unowned, key=lambda x: decision_natural(x[0].key)):
            writers = set()
            for it in miss:
                writers |= p.writers_of_item(r.key, it)
            lines.append(f"    - {_row_line(r, miss, writers)}")
    return out


def decision_natural(key: str):
    return decision_sort_key(key)[1]


def _system_lines(s: System) -> list[str]:
    head = f"  - 系 `{s.name}`(群 {s.group}・時 `{s.timing}`"
    if s.when:
        head += f"・立つ条件 `{s.when}`"
    if s.calls_llm:
        head += f"・LLM `{s.calls_llm}`"
    head += f"・関数 `{s.fn_name}`)"
    lines = [head]
    if s.resolve_ops:
        lines.append(f"    - 呼んでよい resolve の口: {_code_join(list(s.resolve_ops))}")
    if s.soa:
        lines.append(f"    - 書いてよい SoA の列(閉包): {_code_join(list(s.soa))}")
    if s.paths:
        lines.append(f"    - 書いてよい外の道筋: {_code_join(list(s.paths))}")
    if s.scratch:
        lines.append(f"    - 書く scratch: {_code_join(list(s.scratch))}")
    if s.buffers:
        lines.append(f"    - 書く buffers: {_code_join(list(s.buffers))}")
    if s.tally:
        lines.append(f"    - 書く計数: {_code_join(list(s.tally))}")
    return lines


def permit_lines_by_file(p: Permits) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in sorted(p.systems, key=lambda x: x.name):
        out.setdefault(s.fn_file or "src/shibuya/runtime/systems/table.py", []).extend(_system_lines(s))
    resolve_lines: list[str] = []
    for fname in sorted(set(p.direct) | set(p.op_systems)):
        writes = sorted(p.direct.get(fname, frozenset()))
        systems = p.op_systems.get(fname, [])
        line = f"  - `{fname}`: 直接の書き {_code_join(writes) if writes else '(なし)'}"
        if systems:
            line += " 口として持つ系: " + "・".join(systems)
        resolve_lines.append(line)
    if resolve_lines:
        out.setdefault(RESOLVE_FILE, []).extend(resolve_lines)
    return out


@dataclass
class Edges:
    imports: dict[str, set[str]] = field(default_factory=dict)
    importers: dict[str, set[str]] = field(default_factory=dict)
    mentions_by_target: dict[str, set[str]] = field(default_factory=dict)


def build_edges(index: ModuleIndex, facts: dict[str, FileFacts]) -> Edges:
    e = Edges()
    for rel, f in facts.items():
        targets: set[str] = set()
        for ref in f.imports:
            targets |= index.resolve(rel, ref)
        targets.discard(rel)
        e.imports[rel] = targets
        for t in targets:
            e.importers.setdefault(t, set()).add(rel)
        if rel.startswith("tests/"):
            for t in index.mention_targets(rel):
                e.mentions_by_target.setdefault(t, set()).add(rel)
    return e


def _labels(rels: set[str]) -> str:
    return "・".join(f"`{module_label(r)}`" for r in sorted(rels))


def _file_block(rel: str, card_dir: str, f: FileFacts, index: ModuleIndex, edges: Edges,
                ledger: dict[str, list[str]], permits: dict[str, list[str]]) -> list[str]:
    name = rel.rsplit("/", 1)[-1]
    lines = [f"## [{name}]({_rel_link(rel, card_dir)})", ""]
    if f.error:
        lines += [f"**読めなかった**: {f.error}", ""]
    lines += [escape_links(f.summary) if f.summary else "(冒頭の説明なし)", ""]
    bullets: list[str] = []
    if f.public:
        bullets.append("- 公開の関数とクラス")
        for kind, n, doc in f.public:
            bullets.append(f"  - `{n}`({kind})" + (f": {escape_links(doc)}" if doc else ""))
    imp = edges.imports.get(rel, set())
    if imp:
        bullets.append(f"- import している内部モジュール: {_labels(imp)}")
    unresolved = index.unresolved_bare(rel)
    if unresolved:
        bullets.append("- 解けない素の import: " + "・".join(
            f"`{name}`(同じ名のファイル `{unresolved[name]}` が 1 つある)" for name in sorted(unresolved)))
    if f.syspath_unread:
        bullets.append(f"- `sys.path` に足す先を読めない所 {f.syspath_unread} か所")
    importers = edges.importers.get(rel, set())
    callers = {x for x in importers if not x.startswith("tests/")}
    tests = {x for x in importers if x.startswith("tests/")}
    mentions = edges.mentions_by_target.get(rel, set()) - tests
    if callers:
        bullets.append(f"- 呼び手: {_labels(callers)}")
    if tests:
        bullets.append(f"- 読む試験: {_labels(tests)}")
    if mentions:
        bullets.append(f"- 読む試験(道筋で): {_labels(mentions)}")
    if rel in ledger:
        bullets.append("- 状態台帳の行")
        bullets.extend(ledger[rel])
    if rel in permits:
        bullets.append("- 書きの許可")
        bullets.extend(permits[rel])
    if f.cli_args or f.cli_subcommands or f.cli_unread or f.cli_argv:
        bullets.append("- CLI の引数")
        for sub in sorted(f.cli_subcommands):
            bullets.append(f"  - サブコマンド `{sub}`")
        for flag in sorted(f.cli_args):
            h = f.cli_args[flag]
            if h is None:
                bullets.append(f"  - `{flag}`: (help を読めない)")
            else:
                bullets.append(f"  - `{flag}`" + (f": {escape_links(h)}" if h else ""))
        if f.cli_unread:
            bullets.append(f"  - 名前を読めない呼び出し {f.cli_unread} か所")
        if f.cli_argv:
            bullets.append("  - `sys.argv` を直接読む")
    if f.env_names or f.env_unread or f.env_whole:
        parts = [_code_join(sorted(f.env_names))] if f.env_names else []
        if f.env_unread:
            parts.append(f"名前を読めない所 {f.env_unread} か所")
        if f.env_whole:
            parts.append("`os.environ` をまるごと使う")
        bullets.append("- 環境変数: " + "・".join(parts))
    if f.decision_ids:
        ids = sorted(f.decision_ids, key=decision_sort_key)
        bullets.append("- 決定の ID: " + "・".join(ids))
    return lines + bullets + ([""] if bullets else [])


def render_dir_card(card: DirCard, facts: dict[str, FileFacts], index: ModuleIndex, edges: Edges, ledger, permits) -> str:
    card_file = card_path(card.rel)
    card_dir = posixpath.dirname(card_file)
    lines = [f"# {card.rel}", "", GENERATED, "",
             f"Python {len(card.py_files)} 本・その他 {len(card.other_files)} 本(このディレクトリの直下)", ""]
    if card.subdirs:
        lines.append("下のディレクトリ: " + "・".join(
            f"[{s.rsplit('/', 1)[-1]}]({posixpath.relpath(card_path(s), start=card_dir)})" for s in card.subdirs))
        lines.append("")
    if card.other_files:
        lines.append("その他のファイル: " + "・".join(f"`{x.rsplit('/', 1)[-1]}`" for x in card.other_files))
        lines.append("")
    for rel in card.py_files:
        lines += _file_block(rel, card_dir, facts[rel], index, edges, ledger, permits)
    return "\n".join(lines).rstrip("\n") + "\n"


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


def render_docs_index(rows: dict[str, tuple[int, list[tuple[str, str]]]]) -> str:
    """rows: ディレクトリ → (ファイルの数, [(.md の名前, 最初の見出し)])。"""
    total = sum(v[0] for v in rows.values())
    lines = ["# docs の索引", "", GENERATED, "",
             f"{len(rows)} ディレクトリ・{total} 本(`{CARDS_REL}` 自身を除く)。各行は Markdown の文書と最初の見出し。", ""]
    for d in sorted(rows):
        n, mds = rows[d]
        lines += [f"## {d}({n} 本)", ""]
        for name, head in mds:
            lines.append(f"- [{name}]({posixpath.relpath(f'{d}/{name}', start=CARDS_REL)}): {escape_links(head)}")
        if mds:
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def render_data_index(rows: list[tuple[str, int | None]], problems: list[str]) -> str:
    """rows: (ディレクトリ, 大きさ)。大きさが ``None`` はリンクか読めなかったもの。"""
    lines = ["# data の一覧", "", GENERATED, "",
             "ディレクトリの名前と大きさだけ(深さ 2 段まで・大きさは下の全部の合計)。ファイルは 1 本も開いていない。git に入らないので手元の状態の写し。", "",
             "| ディレクトリ | 大きさ |", "|---|---|"]
    for d, size in rows:
        lines.append(f"| `{d}` | {human_size(size) if size is not None else '—'} |")
    lines.append("")
    if problems:
        lines += ["この下のどこかを読めなかった所(大きさは読めた分だけ):", ""] + [f"- `{p}`" for p in problems] + [""]
    return "\n".join(lines).rstrip("\n") + "\n"


def render_readme(dirs: dict[str, DirCard], docs_rows, problems: list[str]) -> str:
    lines = ["# 段 3 ファイルのカード(入口)", "", GENERATED, "",
             "11-05/§3-1 の 1。`src/`・`tests/`・`tools/` のファイルごとの事実をディレクトリごとの Markdown に、`docs/` は索引、`data/` は大きさの一覧にした。", "",
             "## ディレクトリごとのカード", "",
             "| ディレクトリ | Python(直下) | その他(直下) |", "|---|---|---|"]
    for d in sorted(dirs):
        c = dirs[d]
        lines.append(f"| [{d}]({d}/README.md) | {len(c.py_files)} | {len(c.other_files)} |")
    n_docs = sum(v[0] for v in docs_rows.values())
    lines += ["", "## docs と data", "",
              f"- [docs の索引](docs.md): {len(docs_rows)} ディレクトリ・{n_docs} 本",
              "- [data の一覧](data.md): ディレクトリの名前と大きさだけ(data のある機械で作ったときの写し)",
              ""]
    lines.append(RULES.rstrip("\n"))
    lines.append("")
    lines += ["## 読めなかったもの", ""]
    lines += [f"- {p}" for p in problems] if problems else ["なし"]
    return "\n".join(lines).rstrip("\n") + "\n"
