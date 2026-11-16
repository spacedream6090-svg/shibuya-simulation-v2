"""心の読みの一覧の固定(返事その 7 §4-2 の 2・計画 docs/reference/mind-world-reads-2026-11-09.md §9・11-16 の裁定)。

心の区分のコードが、持ち主が心でない SoA の列(世界・行為・経済の列)を直接読む所(「全知の読み」=記録 2-33)を、走査の道具
``ledger_ast.scan`` の strict の読みで数え、固定の表 ``mind_world_reads_frozen.json`` と**組ごとに完全一致**で比べる。
増えても減っても落ちる(落ちたときの文に表の直し方を出す)。data は要らない(道具を読むだけで回す)。

- 鍵 = (移した後の道筋, 読みを囲む最上位の関数か ``クラス.メソッド``, 列)。行の番号は鍵に入れない。
- 範囲 = 表の ``scope.dirs``(心の包みのディレクトリ)の下のファイルと、割るファイル(``scope.split``)のうち心の割り先へ行く
  関数。割るファイルの割り先は全ファイルの表 §4 から写した(表の ``scope.md_source``)。記号の完全一致を先に引き、無ければ
  クラスの名、最上位の文は最初の割り先。
- 列の持ち主 = 表の ``owners``(案 K の分け・``agents`` の列だけ。``cells``・``pois``・知覚の列は世界)。数えるのは心の列でない
  列の読み。状態台帳に持ち主の欄は足していない(11-16 の裁定 4)。
- 同じ名の別物(記憶の行・出来事・会話のセッションの欄)も道具は名前で数えるので一覧に残し、表の ``other_object`` に注を付けた。
- 道の文字列は表(json)にだけ置く(試験のコードに src の道を字面で持たない=移す道具の書き換えの外)。
- 割る段で割るファイルが無くなったら、範囲の試験が落ちる。そのとき割り先の表を作り直す(記録
  ``docs/bench/analysis/self-update-347/README.md``)。

今の表の作り方(数え直し): ``python -m tests.engine.state.test_mind_world_reads``(``PYTHONPATH=src``・リポの根で)が今の
``key_counts`` を JSON で出す。表を直すのは下の ``HOW_TO_FIX`` の決まりのとおり。

逐次ループ宣言: なし(試験)。
"""

from __future__ import annotations

import ast
import json
import sys
from collections import Counter
from functools import cache
from pathlib import Path

import pytest

from shibuya.runtime.state import ledger_ast as SA
from tests import _places as PL

FROZEN_PATH = Path(__file__).with_name("mind_world_reads_frozen.json")
SCHEMA = "shibuya.tests/mind-world-reads/1"

HOW_TO_FIX = (
    "心の読みの一覧(tests/engine/state/mind_world_reads_frozen.json の key_counts)と今の走査が違う。直し方: "
    "(1) 増えた・新しい組=心のコードが世界の欄を新しく直接読む。知覚の口に替えるか、決定の後に理由を記録して表の count を"
    "上げる(行を足す)。決定なしに足さない。"
    "(2) 減った・消えた組=表の count を下げるか行を消す(減らす向きは決定なしで直してよい)。"
    "(3) 関数の名を変えた・関数をまたいで移しただけ(合計が同じ)=表の鍵(path・symbol)を直す。"
    "今の数は python -m tests.engine.state.test_mind_world_reads で出る。")

Key = tuple[str, str, str]


def load_frozen(path: Path = FROZEN_PATH) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA:
        raise AssertionError(f"固定の表の形の名が違う: {doc.get('schema')!r}(想定 {SCHEMA!r})")
    return doc


def frozen_counts(doc: dict) -> Counter:
    return Counter({(e["path"], e["symbol"], e["column"]): int(e["count"]) for e in doc["key_counts"]})


def symbols_by_line(tree: ast.Module) -> dict[int, str]:
    """行 → 囲む最上位の関数・クラス・``クラス.メソッド`` の名(最上位の文は空)。"""
    out: dict[int, str] = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.update(dict.fromkeys(range(n.lineno, n.end_lineno + 1), n.name))
        elif isinstance(n, ast.ClassDef):
            out.update(dict.fromkeys(range(n.lineno, n.end_lineno + 1), n.name))
            for s in n.body:
                if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.update(dict.fromkeys(range(s.lineno, s.end_lineno + 1), f"{n.name}.{s.name}"))
    return out


def defined_symbols(tree: ast.Module) -> set[str]:
    """最上位の関数・クラス・``クラス.メソッド`` の名。"""
    return set(symbols_by_line(tree).values())


def split_dest(rows: list[dict], symbol: str) -> str | None:
    """割るファイルの記号 → 割り先(記号の完全一致 → クラスの名 → 最上位の文は最初の割り先)。引けなければ None。"""
    if not symbol:
        return rows[0]["dest"]
    for r in rows:
        if symbol in r["symbols"]:
            return r["dest"]
    head = symbol.split(".")[0]
    for r in rows:
        if head in r["symbols"]:
            return r["dest"]
    return None


def mind_reads(res: SA.ScanResult, root: Path, doc: dict) -> tuple[Counter, list[str]]:
    """走査の結果 → (鍵 → 数, 割り先を引けない読みの場所)。"""
    mind_cols = set(doc["owners"]["mind"])
    dirs = tuple(doc["scope"]["dirs"])
    split = {e["path"]: e["rows"] for e in doc["scope"]["split"]}
    lines: dict[str, dict[int, str]] = {}
    counts: Counter = Counter()
    unknown: list[str] = []
    for col, sites in res.strict.items():
        if col in mind_cols:
            continue
        for s in sites:
            in_dir = s.path.startswith(dirs)
            if not in_dir and s.path not in split:
                continue
            if s.path not in lines:
                lines[s.path] = symbols_by_line(ast.parse((root / s.path).read_text(encoding="utf-8")))
            sym = lines[s.path].get(s.line, "")
            if in_dir:
                counts[(s.path, sym, col)] += 1
                continue
            dest = split_dest(split[s.path], sym)
            if dest is None:
                unknown.append(f"{s.path}:{s.line} [{sym}] {col}")
            elif dest.startswith(dirs):
                counts[(dest, sym, col)] += 1
    return counts, unknown


def compare(now: Counter, frozen: Counter) -> list[str]:
    """組ごとの違い(空なら同じ)。"""
    out: list[str] = []
    for k in sorted(set(now) | set(frozen)):
        a, b = now[k], frozen[k]
        if a != b:
            out.append(f"{'増えた' if a > b else '減った'} {k[0]} [{k[1]}] {k[2]}: 表 {b} → 今 {a}")
    return out


@cache
def _scan() -> SA.ScanResult:
    return SA.scan(PL.PKG)


@pytest.fixture(scope="module")
def frozen() -> dict:
    return load_frozen()


def test_mind_reads_match_the_frozen_table(frozen):
    """今の心の読みが、固定の表と組ごとに同じ(増えても減っても落ちる・落ちたら文の直し方に従う)。"""
    now, unknown = mind_reads(_scan(), PL.PKG, frozen)
    assert not unknown, ("割るファイルの読みで、割り先の表(scope.split)に記号が無い。全ファイルの表 §4 で割り先を決めて"
                         f"表に足す: {unknown}")
    diff = compare(now, frozen_counts(frozen))
    assert not diff, HOW_TO_FIX + "\n" + "\n".join(diff)
    assert frozen["totals"] == {"sites": sum(now.values()), "keys": len(now)}, "表の totals を key_counts に合わせる"


def test_scope_is_current(frozen):
    """範囲の表が今の木を指している。割る段で割るファイルが無くなったら、ここで落ちる(割り先の表を作り直す)。

    心のディレクトリがある・割るファイルがある・割り先の記号がファイルにある・記号は 1 つの割り先にだけ載る。"""
    for d in frozen["scope"]["dirs"]:
        assert (PL.PKG / d).is_dir(), d
    for e in frozen["scope"]["split"]:
        fp = PL.PKG / e["path"]
        assert fp.is_file(), (f"割るファイル {e['path']} が無い(割る段で割った)。割り先の表 scope.split を作り直す"
                              "(記録 docs/bench/analysis/self-update-347/README.md の ② の節)")
        have = defined_symbols(ast.parse(fp.read_text(encoding="utf-8")))
        seen: Counter = Counter(sym for r in e["rows"] for sym in r["symbols"])
        assert not [s for s, n in seen.items() if n > 1], (e["path"], "記号が 2 つの割り先に載る")
        stale = sorted(set(seen) - have)
        assert not stale, (f"{e['path']}: 割り先の表の記号がファイルに無い(名を変えた・消した)。表を直す: {stale}")
        assert any(r["dest"].startswith(tuple(frozen["scope"]["dirs"])) for r in e["rows"]), e["path"]


def test_owner_table_covers_the_declared_columns(frozen):
    """持ち主の表が宣言の列(``agents``)と同じ集合で、重ならない。

    心の列は世界の置き場の列と名が重ならない。表の各組の列は心の列でなく、``owner`` が持ち主の表と合う。"""
    decl = SA.declared_columns(PL.PKG)
    owners = frozen["owners"]
    flat = [c for cols in owners.values() for c in cols]
    assert len(flat) == len(set(flat)), "持ち主の表で列が 2 つの持ち主に載る"
    assert set(flat) == set(decl["agents"]), ("agents の列と持ち主の表が違う。新しい列は持ち主を決めて表に足す: "
                                              f"表だけ={sorted(set(flat) - set(decl['agents']))} "
                                              f"宣言だけ={sorted(set(decl['agents']) - set(flat))}")
    world_places = {c for p in frozen["world_places"] for c in decl[p]}
    assert not set(owners["mind"]) & world_places
    owner_of = {c: o for o, cols in owners.items() for c in cols}
    for e in frozen["key_counts"]:
        assert e["column"] not in owners["mind"], e
        assert e["owner"] == owner_of.get(e["column"], "world"), e


def test_other_object_notes_point_at_frozen_keys(frozen):
    """別物(列と同じ名の別の物の欄)の注は、表の組の数の内側にある。"""
    n = 0
    for e in frozen["key_counts"]:
        oo = e.get("other_object")
        if oo:
            assert 0 < int(oo["count"]) <= int(e["count"]) and oo["note"], e
            n += int(oo["count"])
    assert n == frozen["totals_other_object"], "表の totals_other_object を注の数の和に合わせる"


def test_negative_controls(tmp_path, frozen):
    """負の対照: 読みが 1 つ増えると「増えた」、1 つ減ると「減った」、割り先を引けない読みは unknown に出る。

    合成の木の心のディレクトリに世界の列の読みを 1 つ置く・表の数を 1 つずらす・割るファイルに表に無い記号の読みを置く。"""
    d = frozen["scope"]["dirs"][0]
    fp = tmp_path / d / "fake_reader.py"
    fp.parent.mkdir(parents=True)
    fp.write_text("def peek(r, a):\n    return r.hunger[a]\n", encoding="utf-8")
    res = SA.scan(tmp_path, files=[fp], names={"hunger"})
    now, unknown = mind_reads(res, tmp_path, frozen)
    assert now == Counter({(f"{d}fake_reader.py", "peek", "hunger"): 1}) and not unknown
    assert compare(now, Counter()) == [f"増えた {d}fake_reader.py [peek] hunger: 表 0 → 今 1"]
    fz = frozen_counts(frozen)
    k = sorted(fz)[0]
    less = fz.copy()
    less[k] -= 1
    assert [x[:3] for x in compare(fz, +less)] == ["増えた"]
    assert [x[:3] for x in compare(+less, fz)] == ["減った"]
    # 割るファイルで、割り先の表に無い記号の読み
    e = frozen["scope"]["split"][0]
    fs = tmp_path / e["path"]
    fs.parent.mkdir(parents=True, exist_ok=True)
    fs.write_text("def no_such_symbol_in_the_table(r, a):\n    return r.hunger[a]\n", encoding="utf-8")
    _, unknown = mind_reads(SA.scan(tmp_path, files=[fs], names={"hunger"}), tmp_path, frozen)
    assert unknown and "no_such_symbol_in_the_table" in unknown[0]


def main() -> int:
    """今の ``key_counts`` を JSON で出す(表を直すときの材料。表の注 ``other_object`` と ``owner`` は手で合わせる)。"""
    doc = load_frozen()
    now, unknown = mind_reads(_scan(), PL.PKG, doc)
    owner_of = {c: o for o, cols in doc["owners"].items() for c in cols}
    rows = [{"path": p, "symbol": s, "column": c, "owner": owner_of.get(c, "world"), "count": n}
            for (p, s, c), n in sorted(now.items())]
    json.dump({"key_counts": rows, "totals": {"sites": sum(now.values()), "keys": len(now)}, "unknown": unknown},
              sys.stdout, ensure_ascii=False, indent=1)
    print()
    return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
