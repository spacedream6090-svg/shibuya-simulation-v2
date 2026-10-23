"""W21(第 4 期 4-1 段 1〜3)の材料の台帳と読み口の守り(read_guard)。

- 検証側の表(R-116 §1 の 11 行・パターン台帳 §10)を開くと止まる(負の対照)・構築側は通る。
- 読み口を通らない Python の ``open`` も守りの間は止まる(監査フック)。
- 〔検収 M1〕書き込みのモードは出力先の下だけ(本体の v2 への書きは落ちる)・``--out`` が本体の v2 の中なら止める。
- 〔検収 L1〕PT 2018 c-2 は見出しの行だけで列の位置を決め、許可の 2 列(舞台の外のゾーンの発生量・自宅以外からの私事)
  とゾーン・時間帯だけを読む(実ファイルと同じ形=29 列・2 段の見出し・単位の行の合成のファイル・監査フックで確かめる)。
- W21 の組み立ては c-2 を開けない(台帳に無い=許可の一覧の外)。
- 構築のコードに封印の層の名が無い(W19 の静的ゲート)。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from shibuya.build.audit import w19_freeze
from shibuya.build.pop import w21_sources as S

R116_VERIFY_ROWS = ("#11", "#16", "#17", "#42", "#45", "#47", "#49", "#50", "#57", "#58", "#59")


def test_verify_side_is_the_eleven_rows_of_r116():
    assert tuple(r.row for r in S.VERIFY_SIDE) == R116_VERIFY_ROWS
    assert all(r.tokens and r.what for r in S.VERIFY_SIDE)
    # 封印の層の名は W19 の表から取る(本ファイルに書かない)
    toks = {t for r in S.VERIFY_SIDE for t in r.tokens}
    assert set(w19_freeze.HOLDOUT_TOKENS) <= toks


def test_registry_is_build_side_and_never_verify_side(tmp_path):
    g = S.W21Guard.for_build(tmp_path)
    assert len({s.sid for s in S.SOURCES}) == len(S.SOURCES)
    for s in S.SOURCES:
        assert s.side == "build" and len(s.md5) == 32
        g.check(tmp_path.joinpath(*s.path))  # 検証側の語が無く、許可の一覧にある
        if s.derived:
            assert s.derived_md5 and len(s.derived_md5) == 32
            g.check(tmp_path.joinpath(*s.derived))
        assert "pt2018" not in s.rel and "pt6_" not in s.rel


@pytest.mark.parametrize("row", S.VERIFY_SIDE, ids=lambda r: r.row)
def test_negative_control_verify_side_paths_are_stopped_before_opening(tmp_path, row):
    """負の対照: 検証側の語のある道筋は、許可の一覧に足しても(=構築側と取り違えても)開く前に止まる。"""
    for tok in row.tokens:
        p = (tmp_path / "data" / tok.strip("/") / "x.csv") if "/" in tok else (tmp_path / "data" / f"x_{tok}_y.csv")
        g = S.W21Guard.for_build(tmp_path / "data", extra=[p])
        with pytest.raises(S.VerificationSideError):
            g.check(p)
        with pytest.raises(S.VerificationSideError):
            g.read_bytes(p)


def test_unlisted_paths_are_stopped_and_listed_ones_pass(tmp_path):
    data = tmp_path / "data"
    s = S.source("sa_t09")
    f = data.joinpath(*s.path)
    f.parent.mkdir(parents=True)
    f.write_bytes(b"abc")
    g = S.W21Guard.for_build(data)
    with pytest.raises(S.NotAllowedError):
        g.check(data / "research_cache" / "r116" / "other.csv")
    with pytest.raises(S.MissingSourceError):  # 台帳の md5 と違う
        g.source_bytes("sa_t09")
    assert g.read_bytes(f) == b"abc"
    assert g.opened["research_cache/r116/census2020_sa_h09_13_labour_force.csv"] == hashlib.md5(b"abc").hexdigest()


def test_audit_hook_stops_raw_open_of_verify_side_and_unlisted_files(tmp_path):
    data = tmp_path / "data"
    (data / "calib" / "pt2018").mkdir(parents=True)
    bad = data / "calib" / "pt2018" / "pt6_b-4.csv"
    bad.write_bytes(b"x")
    other = data / "realworld" / "x.json"
    other.parent.mkdir(parents=True)
    other.write_bytes(b"{}")
    out = tmp_path / "out"
    g = S.W21Guard.for_build(data, out=out)
    with g.active():
        with pytest.raises(S.VerificationSideError):
            open(bad, "rb").close()
        with pytest.raises(S.NotAllowedError):
            open(other, "rb").close()
        out.mkdir()
        (out / "ok.txt").write_text("ok", encoding="utf-8")  # 出力先は書ける
        (tmp_path / "outside.txt").write_text("ok", encoding="utf-8")  # 守る根(data)の外は守らない
    # 守りの外では止めない(フックは空なら何もしない)
    assert open(bad, "rb").read() == b"x"


def test_negative_control_write_mode_into_the_main_v2_is_stopped(tmp_path):
    """〔検収 M1〕本体の v2(読むのは許す世界資産)へ書き込みのモードで開くと止まる・出力先は書ける。"""
    data = tmp_path / "data"
    v2 = data / "world" / "v2"
    v2.mkdir(parents=True)
    (v2 / "w16_population.parquet").write_bytes(b"orig")
    out = data / "world" / "v2_stage_4-1"
    g = S.W21Guard.for_build(data, world=v2, out=out)
    with g.active():
        assert open(v2 / "w16_population.parquet", "rb").read() == b"orig"  # 読むのは許す
        for mode in ("wb", "ab", "r+b", "xb"):
            with pytest.raises(S.NotAllowedError):
                open(v2 / ("new.bin" if mode == "xb" else "w16_population.parquet"), mode).close()
        import os
        with pytest.raises(S.NotAllowedError):
            os.close(os.open(v2 / "w16_population.parquet", os.O_WRONLY | os.O_TRUNC))
        out.mkdir(parents=True)
        (out / "w21_frame.json").write_bytes(b"{}")  # 出力先は書ける
    assert (v2 / "w16_population.parquet").read_bytes() == b"orig" and not (v2 / "new.bin").exists()


def test_negative_control_out_inside_the_main_v2_is_refused(tmp_path):
    """〔検収 M1〕``--out`` が本体の v2・読む世界資産・既存の資産の置き場の中なら、何も書かずに止める。"""
    from shibuya.build.pop import w21_build as W

    data = tmp_path / "data"
    v2 = data / "world" / "v2"
    v2.mkdir(parents=True)
    (data / "world" / "v2_stage_2-4").mkdir()
    for bad in (v2, v2 / "sub", data / "world" / "v2_stage_2-4"):
        with pytest.raises(W.ProtectedOutputError):
            W.check_out(data, bad, v2)
        with pytest.raises(W.ProtectedOutputError):
            W.build(data, bad)
        assert W.main(["--out", str(bad), "--data", str(data)]) == 2
    assert not list(v2.rglob("w21_*")) and not (v2 / "W21.header.json").exists()
    W.check_out(data, data / "world" / "v2_stage_4-1", v2)  # W21 の段の資産の置き場は通る
    W.check_out(data, tmp_path / "elsewhere", v2)


#: 実ファイルの形(29 列=ゾーン・ゾーン名・時間帯+発生量 13+集中量 13・表題の行・空の行・2 段の見出し・単位の行)。
_PURPOSES = ["計", "自宅－勤務", "自宅－通学", "自宅－業務", "自宅－私事", "自宅－帰宅", "勤務・業務", "私事", "帰宅",
             "通学", "業務", "その他", "不明"]


def _pt_csv(path: Path, purposes_gen=None) -> None:
    gen_l = purposes_gen or _PURPOSES
    title = ["表 c-2 ゾーン別目的種類別発着時間帯別発生集中量"] + [""] * 28
    upper = ["", "", ""] + ["発生量"] + [""] * 12 + ["集中量"] + [""] * 12
    lower = ["ゾーン", "ゾーン名称", "時間帯"] + gen_l + _PURPOSES
    unit = ["", "", ""] + ["トリップ"] * 26
    rows = [",".join(title), "", ",".join(upper), ",".join(lower), ",".join(unit)]
    for zone in (":0241 ", ":0100 "):
        for t in ("7時台", "8時台"):
            gen = ["888888" if zone.strip() == ":0241" and lab != "私事" else str(10 + i) for i, lab in enumerate(gen_l)]
            conc = ["999999"] * 13  # 集中量=検証側の印(読まれても返ってもいけない)
            rows.append(",".join([zone, "渋谷", t, *gen, *conc]))
    rows.append("注) 合成の表")
    path.write_bytes(("\n".join(rows) + "\n").encode("cp932"))


def _pt_events(fn):
    """``fn`` の間の監査のイベント(PT の値の列・open)を集める。"""
    import sys

    seen: list[tuple[str, tuple]] = []
    on = [True]

    def hook(ev, args):
        if on[0] and ev in (S.PT_C2_AUDIT_EVENT, "open"):
            seen.append((ev, args))

    sys.addaudithook(hook)
    try:
        out = fn()
    finally:
        on[0] = False
    return out, seen


def test_pt_c2_reads_only_the_allowed_columns(tmp_path):
    """〔検収 L1〕見出しの行だけで列の位置を決め、値は許可の 2 列+ゾーン・時間帯だけを読む(集中量の列は読み込まない)。"""
    data = tmp_path / "data"
    p = data / "synthetic" / "c2_like.csv"
    p.parent.mkdir(parents=True)
    _pt_csv(p)
    g = S.W21Guard.for_build(data, extra=[p])
    lay = S.pt_c2_layout(g, p)
    assert lay["n_columns"] == 29 and lay["header_lines"] == 5
    assert lay["generation_total"] == 3 and lay["private_non_home"] == 3 + _PURPOSES.index("私事")
    assert lay["concentration"] == list(range(16, 29))
    got, seen = _pt_events(lambda: S.read_pt_c2_build_side(g, p))
    read_cols = [args[1] for ev, args in seen if ev == S.PT_C2_AUDIT_EVENT]
    assert read_cols == [(0, 2, 3, 10)]  # ゾーン・時間帯・発生量の計・自宅以外からの私事だけ
    assert not set(read_cols[0]) & set(lay["concentration"])
    dump = json.dumps(got, ensure_ascii=False)
    assert "999999" not in dump and "888888" not in dump  # 集中量も舞台の発生量の計も返らない
    assert got["stage_private"] == {"0241": {"7時台": 17.0, "8時台": 17.0}}
    assert got["outside"]["0100"]["7時台"] == {"generation_total": 10.0, "private_non_home": 17.0}


def test_negative_control_pt_c2_refuses_columns_outside_the_allow_list_before_opening(tmp_path):
    """許可の外の列(集中量)を頼むと、ファイルを開く前に止まる(open も値の列のイベントも出ない)。"""
    import sys

    data = tmp_path / "data"
    p = data / "synthetic" / "c2_like.csv"
    p.parent.mkdir(parents=True)
    _pt_csv(p)
    g = S.W21Guard.for_build(data, extra=[p])
    events: list[str] = []
    live = [True]

    def hook(ev, args):
        if live[0] and (ev == S.PT_C2_AUDIT_EVENT or (ev == "open" and str(args[0]).endswith("c2_like.csv"))):
            events.append(ev)

    sys.addaudithook(hook)
    try:
        with pytest.raises(S.VerificationSideError):
            S.read_pt_c2_build_side(g, p, columns=("generation_total", "concentration_total"))
    finally:
        live[0] = False
    assert events == []


def test_negative_control_pt_c2_layout_mismatch_reads_no_values(tmp_path):
    """「自宅以外からの私事」が発生量の塊に無い形(列の並びが想定と違う)なら、値の列のイベントを出さずに止める。"""
    data = tmp_path / "data"
    p = data / "synthetic" / "c2_bad.csv"
    p.parent.mkdir(parents=True)
    _pt_csv(p, purposes_gen=[x if x != "私事" else "その他2" for x in _PURPOSES])
    g = S.W21Guard.for_build(data, extra=[p])
    import sys

    events: list[str] = []
    live = [True]
    sys.addaudithook(lambda ev, args: events.append(ev) if live[0] and ev == S.PT_C2_AUDIT_EVENT else None)
    with pytest.raises(ValueError):
        S.read_pt_c2_build_side(g, p)
    live[0] = False
    assert events == []


def test_w21_build_cannot_open_pt_c2(tmp_path):
    data = tmp_path / "data"
    p = data / "calib" / "pt2018" / "pt6_c-2.csv"
    p.parent.mkdir(parents=True)
    _pt_csv(p)
    g = S.W21Guard.for_build(data)  # 組み立ての守り=台帳の表だけ
    with pytest.raises(S.NotAllowedError):
        S.read_pt_c2_build_side(g, p)


def test_build_sources_do_not_name_sealed_layers():
    root = Path(w19_freeze.__file__).resolve().parents[1]
    hits = w19_freeze.scan_build_sources(root)
    assert not [k for k in hits if "w21" in k or "attr_fns" in k], hits
