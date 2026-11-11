"""``tests/_places.py`` の対応表の確かめ(検収 M-2)と、解けない名の扱い(検収 L-1)。

``tests/_places.py`` は、移す前と移した後の木で「元の置き場」を引くために道具の対応表 ``tools/pkgmove/map.toml`` を読む。
空や古い表を黙って受けると、層の試験の範囲が黙って縮む(検収の P03・P05)。表を読む所 ``origins_from`` が、形の名・行の
有無・行の鍵と、**今の木の ``.py`` が表の ``old`` か ``move`` の ``new`` に必ず在ること**を確かめて止めることを、負の対照で
確かめる。〔再検収 M-4・L-6・L-7・L-8〕道が変わらない行(move でない行と、old と new が同じ move の行)の集合の固定・宣言の道の
引き方・元の道の重なり。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import tomllib

import pytest

from shibuya import cli
from tests import _places as PL

GOOD_HEAD = f'schema = "{PL.MAP_SCHEMA}"\n'

#: 〔再検収 M-4・L-8〕対応表で道が変わらない行の old: **move でない行(keep・split・delete・empty)の old の全部と、move で
#: old と new が同じ行の old**。第 3 回の後の表から数えた 122 行(keep 94=build 79・economy の直下 14・根の頭 1/split 24/
#: delete 2/empty 2)。こうした行で新しいファイルを載せると、元の置き場が今の道になり、元の置き場で決める範囲(層の守り・c8 の
#: 漏れの確かめ)から黙って外れる。段 4 の終わりに範囲を新しい包みへ移すまでは、新しいファイルの行は move の形(old=移す前の
#: 置き場に在ったとしたらの道・new=今の道)で書く。移す前から在って動かない置き場(build・economy の直下など)に足すときだけ
#: move でない行にし、この一覧にも足す(``PL.ADD_ROW_HELP``)。
NON_MOVE_ROWS: frozenset[str] = frozenset({
    "__init__.py", "cli.py",
    "agents/__init__.py", "agents/state.py",
    "build/__init__.py", "build/audit/__init__.py", "build/audit/run.py", "build/audit/w18_coverage.py",
    "build/audit/w19_freeze.py", "build/audit/w20_acceptance_pack.py", "build/catalog_freeze.py",
    "build/field/__init__.py", "build/field/common.py", "build/field/road_names.py", "build/field/run.py",
    "build/field/street_grid.py", "build/field/w10_noise.py", "build/field/w10_ruler.py",
    "build/field/w12_external_nodes.py", "build/field/w12_rail_events.py", "build/field/w12_real_timetables.py",
    "build/field/w13_weather.py", "build/field/w7_planspec.py", "build/geo/__init__.py", "build/geo/common.py",
    "build/geo/poi_class.py", "build/geo/run.py", "build/geo/w0_crs.py", "build/geo/w11_station_exits.py",
    "build/geo/w1_walk_graph.py", "build/geo/w2_cells.py", "build/geo/w3_distances.py", "build/geo/w4_heights.py",
    "build/geo/w5_entrances.py", "build/geo/w6_poi_org.py", "build/lang/__init__.py", "build/lang/common.py",
    "build/lang/run.py", "build/lang/w14_signage.py", "build/lang/w15_cell_static.py", "build/pop/__init__.py",
    "build/pop/attr_fns.py", "build/pop/fitting.py", "build/pop/pool.py", "build/pop/run.py",
    "build/pop/shapefile.py", "build/pop/w16_population.py", "build/pop/w21_apply.py", "build/pop/w21_attrs.py",
    "build/pop/w21_build.py", "build/pop/w21_build_b.py", "build/pop/w21_build_c.py", "build/pop/w21_check.py",
    "build/pop/w21_checks.py", "build/pop/w21_frame.py", "build/pop/w21_households.py", "build/pop/w21_money.py",
    "build/pop/w21_org.py", "build/pop/w21_outside.py", "build/pop/w21_persona.py", "build/pop/w21_port10.py",
    "build/pop/w21_prior.py", "build/pop/w21_sources.py", "build/pop/w21_tables.py", "build/run.py",
    "build/sched/__init__.py", "build/sched/pool_facts.py", "build/sched/run.py", "build/sched/trial.py",
    "build/sched/vocab.py", "build/sched/w17_schedule.py", "build/sched/w20_calendar_1a.py",
    "build/sched/w20_w21_port.py", "build/space/__init__.py", "build/space/mesh.py", "build/space/navmesh1.py",
    "build/space/raster.py", "build/space/sources.py", "build/vis/__init__.py", "build/vis/png.py",
    "build/vis/run.py", "build/vis/w8_visibility.py", "build/vis/w9_shadow.py",
    "census/__init__.py",
    "economy/__init__.py", "economy/accounts.py", "economy/anchors.py", "economy/census.py", "economy/checks.py",
    "economy/credit.py", "economy/entry_capital.py", "economy/goods.py", "economy/ledger.py", "economy/ops.py",
    "economy/pricing.py", "economy/stage2.py", "economy/tax_deposit.py", "economy/taxes.py", "economy/wages.py",
    "engine/arbiter.py", "engine/calendar.py", "engine/calendar_shadow.py", "engine/change_detect.py",
    "engine/chooser.py", "engine/commit.py", "engine/events/body.py", "engine/llm_bridge.py", "engine/poi_target.py",
    "engine/presence.py", "engine/relations.py", "engine/resolve.py", "engine/run.py", "engine/tools/record.py",
    "engine/tools/registry.py",
    "llm/__init__.py", "llm/fleet.py", "llm/mock.py", "llm/undefined.py",
    "perception/attention.py", "perception/renderer.py",
    "world/__init__.py", "world/assets.py",
})


def non_move_rows(map_text: str) -> set[str]:
    """表の move でない行の old と、move で old と new が同じ行の old。"""
    rows = tomllib.loads(map_text)["row"]
    return {r["old"] for r in rows if r["kind"] != "move" or r.get("new") == r["old"]}


def _real_map() -> str:
    return PL.MAP.read_text(encoding="utf-8")


def test_the_real_map_explains_the_current_tree():
    got = PL.origins_from(_real_map(), PL.PKG)
    assert got == PL.origins()
    files = sorted(p.relative_to(PL.PKG).as_posix() for p in PL.PKG.rglob("*.py") if "__pycache__" not in p.parts)
    assert sorted(got) == files and len(files) > 300


@pytest.mark.parametrize("text,word", [
    (GOOD_HEAD + "row = []\n", "行が無い"),
    ('schema = "other/1"\n' + "row = []\n", "形の名"),
    ("row = [\n", "読めない"),
])
def test_an_empty_or_foreign_map_stops(text, word):
    with pytest.raises(PL.PlacesMapError, match=word):
        PL.origins_from(text, PL.PKG)


def test_a_map_with_renamed_row_keys_stops():
    text = _real_map().replace("\nold = ", "\nsrc = ")
    assert text != _real_map()
    with pytest.raises(PL.PlacesMapError, match="old か kind"):
        PL.origins_from(text, PL.PKG)


def test_a_map_missing_one_row_stops():
    """1 行欠けた(古い)表: 今の木にある ``cli.py`` の行を抜くと、``cli.py`` が表に無いファイルとして止まる。"""
    rel = PL.rel_of(cli)
    blocks = _real_map().split("\n[[row]]\n")
    keep = [b for b in blocks if f'\nold = "{rel}"\n' not in f"\n{b}\n"]
    assert len(keep) == len(blocks) - 1
    with pytest.raises(PL.PlacesMapError, match=rel):
        PL.origins_from("\n[[row]]\n".join(keep), PL.PKG)


def test_a_fake_tree_maps_moves_and_allows_only_empty_new_heads(tmp_path):
    pkg = tmp_path / "pkg"
    (pkg / "sub").mkdir(parents=True)
    (pkg / "a.py").write_text("A = 1\n", encoding="utf-8")
    (pkg / "sub" / "x.py").write_text("X = 1\n", encoding="utf-8")
    (pkg / "sub" / "__init__.py").write_bytes(b"")
    text = (GOOD_HEAD + '[[row]]\nold = "a.py"\nkind = "keep"\nnew = "a.py"\n\n'
            '[[row]]\nold = "x.py"\nkind = "move"\nnew = "sub/x.py"\n')
    assert PL.origins_from(text, pkg) == {"a.py": "a.py", "sub/__init__.py": "sub/__init__.py", "sub/x.py": "x.py"}
    (pkg / "sub" / "__init__.py").write_text('"""頭。"""\n', encoding="utf-8")  # 中身のある頭は表に要る
    with pytest.raises(PL.PlacesMapError, match="sub/__init__.py"):
        PL.origins_from(text, pkg)
    (pkg / "sub" / "__init__.py").write_bytes(b"")
    (pkg / "b.py").write_text("B = 1\n", encoding="utf-8")  # 表に無いファイル
    with pytest.raises(PL.PlacesMapError, match="b.py"):
        PL.origins_from(text, pkg)


def test_rows_that_keep_their_place_are_frozen():
    """〔再検収 M-4・L-8〕道が変わらない行(move でない行と、move で old と new が同じ行)は黙って足せない: 表の集合が固定の
    一覧と同じ。"""
    got = non_move_rows(_real_map())
    added = sorted(got - NON_MOVE_ROWS)
    gone = sorted(NON_MOVE_ROWS - got)
    assert not added, f"道が変わらない行(move でない行か old と new が同じ行)が増えた {added}。{PL.ADD_ROW_HELP}"
    assert not gone, f"道が変わらない行が減った {gone}(表から行を消したか move に替えたなら、NON_MOVE_ROWS からも消す)"
    assert len(NON_MOVE_ROWS) == 122


@pytest.mark.parametrize("kind", ["keep", "split", "delete", "empty", "move"])
def test_a_non_move_row_for_a_new_file_is_caught_and_a_move_row_is_not(kind):
    """負の対照: 新しい置き場のファイルを道が変わらない行(keep・split・delete・empty か、old と new が同じ move)で載せた表は
    固定の一覧に当たり、move の形(old=移す前の置き場に在ったとしたらの道)で載せた表は当たらない。どの表も ``origins_from`` は
    受ける(表の規則は変えない)。"""
    new = "zz_pkg_after_the_move/zz_new.py"
    same_row = f'\n[[row]]\nnum = "zz"\nold = "{new}"\npackage = "zz"\nkind = "{kind}"\nnew = "{new}"\n'
    move_row = (f'\n[[row]]\nnum = "zz"\nold = "zz_before/zz_new_after_the_move.py"\npackage = "zz"\nkind = "move"\n'
                f'new = "{new}"\nstage = "zz"\n')
    assert non_move_rows(_real_map() + same_row) - NON_MOVE_ROWS == {new}
    assert non_move_rows(_real_map() + move_row) == non_move_rows(_real_map())
    assert PL.origins_from(_real_map() + same_row, PL.PKG) == PL.origins_from(_real_map() + move_row, PL.PKG) == PL.origins()


def test_current_index_stops_when_two_files_share_one_origin():
    """〔再検収 L-7〕2 つの今のファイルが同じ元の道を持てば ``current_of`` の索引は止める。"""
    assert PL.current_index({"a/x.py": "o/x.py", "b/y.py": "o/y.py"}) == {"o/x.py": "a/x.py", "o/y.py": "b/y.py"}
    with pytest.raises(AssertionError, match="元の道が重なる"):
        PL.current_index({"a/x.py": "o/x.py", "b/x.py": "o/x.py"})


def test_declared_path_now_reads_the_origin_first_then_the_tree(tmp_path):
    """〔再検収 L-6〕宣言の道は、表の元の道として引ければ今の道へ・引けなければ今の木に在るか・どちらでもなければ止める。"""
    pkg = tmp_path / "pkg"
    for rel in ("new/x.py", "old/x.py", "fresh/y.py"):
        (pkg / rel).parent.mkdir(parents=True, exist_ok=True)
        (pkg / rel).write_text("X = 1\n", encoding="utf-8")
    # old/x.py の元のファイルは new/x.py へ移り、old/x.py には別の元(older/x.py)のファイルが在る
    org = {"new/x.py": "old/x.py", "old/x.py": "older/x.py", "fresh/y.py": "fresh/y.py"}
    assert PL.declared_path_now("old/x.py", org, pkg) == "new/x.py"  # 元の道を先に引く(偶然の一致に引きずられない)
    assert PL.declared_path_now("older/x.py", org, pkg) == "old/x.py"
    assert PL.declared_path_now("fresh/y.py", org, pkg) == "fresh/y.py"
    org2 = {"new/x.py": "old/x.py", "old/x.py": "older/x.py"}  # fresh/y.py は表に無い(段 4 の後に新しい道で書いた宣言)
    assert PL.declared_path_now("fresh/y.py", org2, pkg) == "fresh/y.py"
    with pytest.raises(KeyError):
        PL.declared_path_now("gone/z.py", org, pkg)  # 元の道でも今の木の道でもない


def test_unresolvable_shibuya_names_are_hits():
    """検収 L-1: 木のどのモジュールにも包みにも解けない ``shibuya.`` の名は、層の試験の違反(``Names.hits``)。"""
    name = f"{PL.PKG.name}.{cli.__name__.rpartition('.')[2]}_zz_future"
    assert PL.unknown(name) and not PL.unknown(cli.__name__) and not PL.unknown(PL.PKG.name)
    empty = PL.Names(frozenset(), frozenset())
    assert empty.hits(name) and not empty.hits(cli.__name__) and not empty.has(name)
