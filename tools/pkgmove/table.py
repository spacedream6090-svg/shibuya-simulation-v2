# -*- coding: utf-8 -*-
"""全ファイルの表を読み、対応表 TOML(今の道 → 新しい道)を書く・読む。保留の一覧はここだけに置く。

- 表: ``docs/reference/package-map-final-2026-11-09-files.md`` の §3(1 ファイル 1 行・338 行)と §4(割るファイルの割り先)。
- 行の種類(``kind``):
    ``move``  置き場が変わり割らないファイル(段 4 で移す)。``empty_head`` は新しい頭を空にする行(表の「(空にする)」)。
    ``empty`` 置き場は同じで、頭を空にする行(``economy/__init__.py``・``world/__init__.py``)。
    ``split`` 割るファイル(段 3・段 4 では割らない。割る段で ``tools/pkgmove/split.py`` が当てる)。
    ``delete`` 消す頭(``agents/__init__.py``・``census/__init__.py``)。
    ``keep``  置き場を変えないもの(build と根の頭)。
- 段(``stage``): ``move``・``empty`` は包みの名(:data:`LATE_STAGES` の行はその段の名)、``delete`` は ``delete``。段 4 の
  小さな段の順は :data:`STAGES`。
- 保留(:data:`HELD`): ユーザーか親の判断待ちの問いに関わる行。道具はこの行を動かすことを断る。11-16 の答え(返事その 8 §1-6)で
  全部決着したので、今は空(仕組みは残す)。
- 〔割る段 5a・親の裁定 Q1〕割り先の 2 つ目以降の新しいファイルは、§3 に move の形の行(割るかの欄が「いいえ(`元` の割り先)」)で
  載る=``split_from``(元の割る行の今の道)。割る前は old も new も木に無いので、段 4 の段の行には数えない(``stage`` は空)。
- 〔割る段 5a・親の裁定 Q9・Q6〕割る行は §4 の節(``### 4-N `今の道```)の表から名ごとの割り先(``names``・頂上の名だけ=
  ``クラス.メソッド`` は数えない)を読む。「ほか N 個」が残る節は名が揃っていない(``names_complete`` が偽=割る道具は当てない)。
  §4 の注の行「宣言した書き換え: 割り先 `X` では別名 `V` を外す」は ``rewrites``(割り先 → 別名)。割る段 5a の順は
  :data:`SPLIT_ORDER`(``split_order`` は 1 から)。
- 〔割る段 5b の G0〕順に 5b の 5 本を足した(:data:`SPLIT_ORDER` の 18〜22 本目・群は :data:`SPLIT_GROUPS`)。入口の転送
  (:data:`SPLIT_FORWARDERS`・型は :func:`forwarder_text`=親の裁定 Q6 の (a))と入口の割り先(:data:`SPLIT_ENTRIES`)の宣言は
  ここだけに置く(``map.toml`` には写しを書く。道具はここから読む)。
"""
from __future__ import annotations

import hashlib
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Iterable

TABLE_REL: Final[str] = "docs/reference/package-map-final-2026-11-09-files.md"
MAP_REL: Final[str] = "tools/pkgmove/map.toml"
MAP_SCHEMA: Final[str] = "shibuya.tools/pkgmove/map/1"

#: 段 4 の小さな段の順(当てた順・``contracts.toml`` の ``stage_order`` と同じ)。計画 §7-4 の段 4 の行の順から、interim_bundles
#: を答えの後へ回し(親の決定 12)、答えの後の行を 2 つの段(:data:`LATE_STAGES`)に分けた。最後の ``delete`` は消す 2 本。
STAGES: Final[tuple[str, ...]] = (
    "foundation", "world", "economy", "act", "mind", "society", "runtime", "experiments", "validation",
    "society_contact", "interim_bundles", "foundation_224a", "delete",
)

#: 済んだ段の包みへ、答えの後に移す行(今の道 → 段の名)。済んだ段(society・foundation)を当て直さずに、別の段・別の commit で
#: 当てるため(返事その 8 §1-6 の 1=連絡の器 4 本は今 society・行 224a は親が置き場を確かめた)。
LATE_STAGES: Final[dict[str, str]] = {
    "engine/contact/calls.py": "society_contact",
    "engine/contact/chat_state.py": "society_contact",
    "engine/contact/deliver.py": "society_contact",
    "engine/contact/tools.py": "society_contact",
    "engine/removed_switches.py": "foundation_224a",
}

#: 保留の行(今の道 → 理由)。**保留の一覧はここだけ**(README に写す)。道具はこの行を動かさない(名指しで動かそうとすれば断る)。
#: 11-16 の答えで 7 行とも決着した(連絡の器 4 本=society・行 224a=``foundation/arms/removed.py``・``engine/resolve.py`` と
#: ``engine/run.py``=割る行の割り先が決まった。割る行は段 4 では元々動かない)。決着の文は全ファイルの表の行の「理由」に書いた。
HELD: Final[dict[str, str]] = {}

#: 割る段 5a の順(表の old・親の裁定 Q11・Q12・Q15。計画の要旨は第347 の報告 §2 と記録 docs/bench/analysis/split5a-347)。
#: 群 G1〜G5 の 17 本。下の層へ下ろすものが先(place_words・agent_codes・types → events の語の順 → 推論の口 → 選び手と店の語 →
#: System 1 と関係)。
#: 〔割る段 5b の G0・親の裁定 Q11〕5a の 17 本の後に 5b の 5 本(葉の 3 本 commit → presence → calendar_shadow・ラン・CLI)。
#: 〔割る段 6 の S6-G0・親の裁定 Q9〕5b の後に段 6 の 1 本(23 本目=``engine/resolve.py`` を 18 の割り先へ)。
#: 〔割る段 6 の M0・親の裁定 Q12・T2〕5a の 18 本目から延ばしていた ``engine/speech/port.py``(``mora_count`` と ``_SMALL_KANA`` を
#: ``foundation/text/mora.py`` へ下ろし、残りの名は元のファイルに残す)を 24 本目に載せた。延ばした理由(つなぎの台帳の道の表が
#: 1 対 1 で、2 つの今の道を同じ台帳の道に向けられない)は、E7 の前向きの表(``LEDGER_PATHS_SPLIT``)で無くなった。
SPLIT_ORDER: Final[tuple[str, ...]] = (
    "world/assets.py", "agents/state.py", "engine/calendar.py",
    "engine/tools/registry.py", "engine/tools/record.py", "engine/events/body.py",
    "llm/__init__.py", "llm/fleet.py", "llm/mock.py", "llm/undefined.py", "engine/llm_bridge.py",
    "engine/chooser.py", "engine/poi_target.py", "perception/attention.py",
    "engine/change_detect.py", "engine/arbiter.py", "engine/relations.py",
    "engine/commit.py", "engine/presence.py", "engine/calendar_shadow.py",
    "engine/run.py",
    "cli.py",
    "engine/resolve.py",
    "engine/speech/port.py",
)
#: 割る行のまま残し、割る段の順から外した行(今の道 → 理由)。順に載る行と同じく §4 の名が揃っていることを確かめる。
#: 〔割る段 6 の M0〕延ばしていた ``engine/speech/port.py`` を順の 24 本目へ移したので、今は空(仕組みは残す)。
SPLIT_DEFERRED: Final[dict[str, str]] = {}
#: 群(親の裁定 Q11・段 6 は裁定 Q9)。段(5a・5b・6)→ 名 → SPLIT_ORDER の範囲(先頭から何本目まで・1 から)。
#: 〔割る段 6 の M0〕段 6 に群 M(24 本目=延ばしていた ``engine/speech/port.py``)。
SPLIT_GROUPS: Final[dict[str, dict[str, tuple[int, int]]]] = {
    "5a": {"G1": (1, 3), "G2": (4, 6), "G3": (7, 11), "G4": (12, 14), "G5": (15, 17)},
    "5b": {"G1": (18, 20), "G2": (21, 21), "G3": (22, 22)},
    "6": {"G1": (23, 23), "M": (24, 24)},
}
#: 〔割る段 5b・E2・親の裁定 Q6・Q7〕入口の転送: 割った後も元のファイルを消さず、決まった型の転送(``split.forwarder_text``=
#: ``if __name__ == "__main__":`` の中で割り先の ``main`` を import して ``raise SystemExit(main())``・docstring つき・名を結ばない)で
#: 書き直す割る行(今の道 → ``main`` の割り先)。``python -m shibuya.cli`` を外との約束として残す(返事その 8 §1-6 の 6・案 K §2-11)。
#: 名の無い点の道(``"shibuya.cli"``)は書き換えない(転送の名=動き続ける)。
SPLIT_FORWARDERS: Final[dict[str, str]] = {
    "cli.py": "interfaces/cli/main.py",
}
#: 〔割る段 5b・E3〕入口の割り先: 割る行の ``main`` と ``if __name__ == "__main__"`` の行き先(今の道 → 割り先)。``-m <元のモジュール>``
#: の文脈の名の無い点の道はここへ向ける(返事その 8 §1-6 の 6=``python -m shibuya.engine.run`` は interfaces へ移す)。転送を残す行
#: (:data:`SPLIT_FORWARDERS`)は載せない(``-m`` の名は転送が受ける)。
SPLIT_ENTRIES: Final[dict[str, str]] = {
    "engine/run.py": "interfaces/cli/run_args.py",
}


def _dotted(rel: str) -> str:
    """``src/shibuya`` からの道 → モジュールの名(頭は包みの名)。"""
    parts = rel[:-3].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(["shibuya", *parts])


def forwarder_text(old: str, dest: str) -> str:
    """〔割る段 5b・E2・親の裁定 Q6 の (a)〕入口の転送の決まった型(:data:`SPLIT_FORWARDERS`)。頂上で名を結ばない(``import shibuya.cli``
    は何も持たない=古い道の口にならない)。``python -m`` で走るときだけ割り先の ``main`` を読んで呼ぶ。"""
    m_old, m_new = _dotted(old), _dotted(dest)
    return (f'"""{m_old} — ``python -m {m_old}`` の入口(外との約束)。中身は ``{m_new}``(割る段 5b)。"""\n'
            "\n"
            'if __name__ == "__main__":\n'
            f"    from {m_new} import main\n"
            "\n"
            "    raise SystemExit(main())\n")

_ROW_RE = re.compile(
    r"^\| (?P<num>\d+[a-z]?) \| `(?P<old>[^`]+)` \| (?P<pkg>[^|]+?) \| (?P<new>.+?) \| (?P<split>いいえ[^|]*?|割る[^|]*?) \| "
    r"(?P<why>.*) \| (?P<src>[^|]+?) \| (?P<rec>[^|]+?) \|$")
_CODE_SPAN_RE = re.compile(r"`([^`]+)`")
_SPLIT_FROM_RE = re.compile(r"^いいえ\(`([^`]+)` の割り先\)$")
_SEC4_RE = re.compile(r"^### (4-\d+) `([^`]+)`")
_SEC_END_RE = re.compile(r"^#{2,3} ")
_OMIT_RE = re.compile(r"ほか \d+ 個")
_REWRITE_RE = re.compile(r"宣言した書き換え: 割り先 `([^`]+)` では別名 `([A-Za-z_]\w*)` を外す")


@dataclass(frozen=True)
class Row:
    """表の 1 行(道筋は ``src/shibuya`` からの相対・``/`` 区切り)。"""

    num: str
    old: str
    package: str
    kind: str
    new: str = ""
    stage: str = ""
    empty_head: bool = False
    split_to: tuple[str, ...] = ()
    held: str = ""
    #: 〔割る段 5a〕割り先の 2 つ目以降の新しいファイルの行: 元の割る行の old。
    split_from: str = ""
    #: 〔割る段 5a〕割る行: (頂上の名, 割り先) の並び(§4 の表の順)・名が揃っているか・宣言した書き換え(割り先, 別名)・割る順。
    names: tuple[tuple[str, str], ...] = ()
    names_complete: bool = False
    rewrites: tuple[tuple[str, str], ...] = ()
    split_order: int = 0

    @property
    def is_head(self) -> bool:
        return self.old.endswith("__init__.py")

    @property
    def name_map(self) -> dict[str, str]:
        return dict(self.names)


@dataclass
class MapDoc:
    """対応表 TOML の中身。"""

    rows: list[Row]
    source: str = TABLE_REL
    source_sha256: str = ""
    stages: tuple[str, ...] = STAGES
    meta: dict = field(default_factory=dict)

    def by_old(self) -> dict[str, Row]:
        return {r.old: r for r in self.rows}

    def split_rows(self) -> list[Row]:
        """割る段 5a の割る行(:data:`SPLIT_ORDER` の順)。"""
        by = self.by_old()
        return [by[o] for o in SPLIT_ORDER if o in by]


def _cell_names(cell: str) -> tuple[list[str], bool]:
    """§4 の表の 1 欄 → 頂上の名(``クラス.メソッド`` と注の中の名は除く)と、「ほか N 個」が残っていないか。"""
    cell = re.sub(r"〔[^〕]*〕", "", cell)
    out: list[str] = []
    for m in _CODE_SPAN_RE.finditer(cell):
        name = re.sub(r"\(.*?\)", "", m.group(1)).strip()
        if name and "." not in name and re.fullmatch(r"[A-Za-z_]\w*", name):
            out.append(name)
    return out, not _OMIT_RE.search(cell)


def parse_split_tables(text: str) -> dict[str, tuple[list[tuple[str, str]], bool, list[tuple[str, str]]]]:
    """§4 の節 → 今の道 → (名と割り先の並び, 名が揃っているか, 宣言した書き換え)。名が 2 つの割り先に載れば ``ValueError``。"""
    out: dict[str, tuple[list[tuple[str, str]], bool, list[tuple[str, str]]]] = {}
    cur: str | None = None
    for line in text.splitlines():
        m = _SEC4_RE.match(line)
        if m:
            cur = m.group(2)
            out[cur] = ([], True, [])
            continue
        if cur is None:
            continue
        if _SEC_END_RE.match(line):
            cur = None
            continue
        names, complete, rewrites = out[cur]
        rw = _REWRITE_RE.search(line)
        if rw:
            rewrites.append((rw.group(1), rw.group(2)))
            continue
        if not line.startswith("| `"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 5:
            continue
        dest = cols[0].strip("`")
        for c in cols[2:5]:
            ns, ok = _cell_names(c)
            complete = complete and ok
            for n in ns:
                if any(n == x for x, _d in names):
                    complete = False  # 2 つの割り先に載る=名の単位では言えない
                    continue
                names.append((n, dest))
        out[cur] = (names, complete, rewrites)
    return out


def parse_table(text: str) -> list[Row]:
    """表の §3 の行を読む(行の数と道筋の重なりを確かめる)。割る行には §4 の名の表を付ける。"""
    rows: list[Row] = []
    seen: set[str] = set()
    sec4 = parse_split_tables(text)
    for line in text.splitlines():
        m = _ROW_RE.match(line)
        if not m:
            continue
        old = m["old"]
        if old in seen:
            raise ValueError(f"表に同じ道筋が 2 行ある: {old}")
        seen.add(old)
        pkg = m["pkg"].strip()
        new_col = m["new"]
        spans = _CODE_SPAN_RE.findall(new_col)
        held = HELD.get(old, "")
        if m["split"].startswith("割る"):
            names, complete, rewrites = sec4.get(old, ([], False, []))
            order = SPLIT_ORDER.index(old) + 1 if old in SPLIT_ORDER else 0
            rows.append(Row(m["num"], old, pkg, "split", new=spans[0] if spans else "", split_to=tuple(spans),
                            held=held, names=tuple(names), names_complete=bool(names) and complete,
                            rewrites=tuple(rewrites), split_order=order))
            continue
        sf = _SPLIT_FROM_RE.match(m["split"].strip())
        if m["split"].strip() != "いいえ" and sf is None:
            raise ValueError(f"割るかの欄が読めない: {old} {m['split']!r}")
        if pkg == "消す":
            rows.append(Row(m["num"], old, pkg, "delete", stage="delete", held=held))
            continue
        if not spans:
            raise ValueError(f"新しい置き場が読めない: {old} {new_col!r}")
        new = spans[0]
        empty = "(空にする)" in new_col
        if sf is not None:
            rows.append(Row(m["num"], old, pkg, "move", new=new, stage="", held=held, split_from=sf.group(1)))
            continue
        if pkg == "build" or new == old:
            kind = "empty" if (empty and new == old) else "keep"
            rows.append(Row(m["num"], old, pkg, kind, new=new, stage=pkg if kind == "empty" else "",
                            empty_head=empty, held=held))
            continue
        rows.append(Row(m["num"], old, pkg, "move", new=new, stage=LATE_STAGES.get(old, pkg), empty_head=empty,
                        held=held))
    missing = sorted(set(HELD) - seen)
    if missing:
        raise ValueError(f"保留の一覧の行が表に無い: {missing}")
    late = {r.old for r in rows if r.kind == "move" and r.old in LATE_STAGES}
    if late != set(LATE_STAGES):
        raise ValueError(f"答えの後の段の行が表の move の行に無い: {sorted(set(LATE_STAGES) - late)}")
    by = {r.old: r for r in rows}
    bad = [o for o in SPLIT_ORDER if o not in by or by[o].kind != "split"]
    if bad:
        raise ValueError(f"割る段の順の行が表の割る行に無い: {bad}")
    # 〔割る段 5a〕順に載る割る行(と延ばした行)は、§4 の名が揃っていて(「ほか N 個」が無く・名が 1 つの割り先にだけ載る)、割り先が
    # §3 の一覧に在る
    both = set(SPLIT_ORDER) & set(SPLIT_DEFERRED)
    if both:
        raise ValueError(f"割る段の順と延ばした行の両方に載る: {sorted(both)}")
    bad = [o for o in SPLIT_DEFERRED if o not in by or by[o].kind != "split"]
    if bad:
        raise ValueError(f"延ばした行が表の割る行に無い: {bad}")
    for o in (*SPLIT_ORDER, *SPLIT_DEFERRED):
        r = by[o]
        if not r.names_complete:
            raise ValueError(f"割る行 {o}: §4 の名が揃っていない(「ほか N 個」が残るか、名が 2 つの割り先に載る)")
        stray = sorted({d for _n, d in r.names} - set(r.split_to))
        if stray:
            raise ValueError(f"割る行 {o}: §4 の割り先が §3 の割り先の一覧に無い: {stray}")
    for r in rows:
        if r.split_from and (r.split_from not in by or by[r.split_from].kind != "split"
                             or r.new not in by[r.split_from].split_to):
            raise ValueError(f"行 {r.num}: 割り先の元 {r.split_from} が割る行でないか、割り先の一覧に {r.new} が無い")
    # 〔割る段 5b・E2・E3〕入口の転送と入口の割り先は、順に載る割る行の、`main` の割り先(転送は主な割り先でもある)
    both = set(SPLIT_FORWARDERS) & set(SPLIT_ENTRIES)
    if both:
        raise ValueError(f"入口の転送と入口の割り先の両方に載る: {sorted(both)}")
    for o, d in (*SPLIT_FORWARDERS.items(), *SPLIT_ENTRIES.items()):
        r = by.get(o)
        if r is None or r.kind != "split" or o not in SPLIT_ORDER or r.name_map.get("main") != d:
            raise ValueError(f"入口の宣言 {o} → {d}: 順に載る割る行でないか、`main` の割り先が {d} でない")
        if o in SPLIT_FORWARDERS and r.new != d:
            raise ValueError(f"入口の転送 {o} → {d}: 主な割り先 {r.new} と違う")
    return rows


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ TOML の書き手(標準ライブラリの tomllib は読むだけ)
def _q(s: str) -> str:
    """TOML の基本の文字列(``"`` と ``\\`` と制御文字だけを逃がす)。"""
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ord(ch) < 0x20 or ch == "\x7f":
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _arr(xs: Iterable[str]) -> str:
    return "[" + ", ".join(_q(x) for x in xs) + "]"


def _inline(d: dict[str, str]) -> str:
    return "{" + ", ".join(f"{_q(k)} = {_q(v)}" for k, v in d.items()) + "}"


def render_map(rows: list[Row], source_sha256: str) -> str:
    """対応表 TOML の文(行の順は表の順)。割る行の名の表は ``[row.names]``(名 → 割り先)・宣言した書き換えは
    ``[row.rewrites]``(割り先 → 別名)。"""
    head = [
        "# 移す段 3 の対応表(道具 tools/pkgmove/cli.py map が全ファイルの表から作る。手で書かない)。",
        "# 道筋は src/shibuya からの相対。kind: move=移す(empty_head=新しい頭を空に・split_from=割る段の 2 つ目以降の割り先)・",
        "# empty=同じ置き場で頭を空に・split=割る(割る段で split.py が当てる。split_to は割り先・names は名ごとの割り先)・",
        "# delete=消す頭・keep=置き場を変えない。",
        "# held がある行は保留(道具は動かさない)。stage は段 4 の小さな段(答えの後に移す行は、その包みと別の段の名)。",
        f"schema = {_q(MAP_SCHEMA)}",
        f"source = {_q(TABLE_REL)}",
        f"source_sha256 = {_q(source_sha256)}",
        f"stages = {_arr(STAGES)}",
        f"split_order = {_arr(SPLIT_ORDER)}",
        "# split_deferred: 割る行のまま割る段の順から外した行(table.SPLIT_DEFERRED・理由はそこ)。",
        f"split_deferred = {_arr(tuple(SPLIT_DEFERRED))}",
        "# split_forwarders: 割った後も決まった型の転送で残す元のファイル → main の割り先(table.SPLIT_FORWARDERS)。",
        "# split_entries: 割る行の main と if __name__ == \"__main__\" の割り先(table.SPLIT_ENTRIES)。道具はどちらも table.py から読む。",
        f"split_forwarders = {_inline(SPLIT_FORWARDERS)}",
        f"split_entries = {_inline(SPLIT_ENTRIES)}",
        "",
    ]
    body: list[str] = []
    for r in rows:
        body.append("[[row]]")
        body.append(f"num = {_q(r.num)}")
        body.append(f"old = {_q(r.old)}")
        body.append(f"package = {_q(r.package)}")
        body.append(f"kind = {_q(r.kind)}")
        if r.new:
            body.append(f"new = {_q(r.new)}")
        if r.stage:
            body.append(f"stage = {_q(r.stage)}")
        if r.empty_head:
            body.append("empty_head = true")
        if r.split_to:
            body.append(f"split_to = {_arr(r.split_to)}")
        if r.held:
            body.append(f"held = {_q(r.held)}")
        if r.split_from:
            body.append(f"split_from = {_q(r.split_from)}")
        if r.kind == "split":
            if r.split_order:
                body.append(f"split_order = {r.split_order}")
            body.append(f"names_complete = {'true' if r.names_complete else 'false'}")
            if r.names:
                body.append("")
                body.append("[row.names]")
                body += [f"{_q(n)} = {_q(d)}" for n, d in r.names]
            if r.rewrites:
                body.append("")
                body.append("[row.rewrites]")
                body += [f"{_q(d)} = {_q(a)}" for d, a in r.rewrites]
        body.append("")
    return "\n".join(head + body)


def build_map_text(repo: Path) -> str:
    text = (repo / TABLE_REL).read_text(encoding="utf-8")
    return render_map(parse_table(text), sha256_text(text))


def split_order_of(doc: MapDoc) -> tuple[str, ...]:
    """〔割る段 6・E9〕対応表の割る行の ``split_order``(1 から)で並べた割る段の順(``cli.py split --map`` が使う=表と木を渡す口)。
    番号が 1 から続かない(同じ番号が 2 つ・抜け)か、表の頭の ``split_order`` と食い違えば ``ValueError``。"""
    rows = sorted((r.split_order, r.old) for r in doc.rows if r.kind == "split" and r.split_order > 0)
    nums = [n for n, _o in rows]
    if nums != list(range(1, len(nums) + 1)):
        raise ValueError(f"対応表の割る行の split_order が 1 から続かない: {nums}")
    order = tuple(o for _n, o in rows)
    head = doc.meta.get("split_order")
    if head is not None and tuple(head) != order:
        raise ValueError(f"対応表の頭の split_order と割る行の split_order が食い違う(頭 {list(head)}・行 {list(order)})")
    return order


def load_map(path: Path) -> MapDoc:
    """対応表 TOML を読む(保留の一覧が道具の一覧と同じかも確かめる)。"""
    doc = tomllib.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != MAP_SCHEMA:
        raise ValueError(f"対応表の schema が違う: {doc.get('schema')!r}")
    rows = [Row(num=r["num"], old=r["old"], package=r["package"], kind=r["kind"], new=r.get("new", ""),
                stage=r.get("stage", ""), empty_head=bool(r.get("empty_head", False)),
                split_to=tuple(r.get("split_to", ())), held=r.get("held", ""), split_from=r.get("split_from", ""),
                names=tuple((str(k), str(v)) for k, v in r.get("names", {}).items()),
                names_complete=bool(r.get("names_complete", False)),
                rewrites=tuple((str(k), str(v)) for k, v in r.get("rewrites", {}).items()),
                split_order=int(r.get("split_order", 0))) for r in doc.get("row", [])]
    held = {r.old: r.held for r in rows if r.held}
    if held != HELD:
        raise ValueError("対応表の保留の行が道具の保留の一覧(table.HELD)と違う(cli.py map で作り直す)")
    return MapDoc(rows=rows, source=doc.get("source", ""), source_sha256=doc.get("source_sha256", ""),
                  stages=tuple(doc.get("stages", STAGES)), meta={k: v for k, v in doc.items() if k != "row"})
