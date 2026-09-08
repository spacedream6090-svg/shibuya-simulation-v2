"""build.audit の単体テスト(実データ不要)。

- 被覆指標の算術を**手で解ける3クラスの合成カタログ**で固定する
- カタログ欄のパース(現実数量・深度・門)
- holdout 封印の member_hash が決定論(順序に依らない)
- ゲート表 markdown が落ちたゲートを隠さない
"""

from __future__ import annotations

import math

import pytest

from shibuya.build.geo import common as C
from shibuya.build.audit import w18_coverage as W18
from shibuya.build.audit import w19_freeze as W19
from shibuya.build.audit import w20_acceptance_pack as W20


# ---------------------------------------------------------------- パース


def test_parse_n_real():
    assert W18.parse_n_real("7,210(OSM)/6,311棟(PLATEAU)✔") == 7210.0
    assert W18.parse_n_real("4,944エッジ/186.7km ✔") == 4944.0
    assert W18.parse_n_real("空欄(OSM waterway要確認)") is None
    assert W18.parse_n_real("観察対象") is None
    assert W18.parse_n_real("") is None
    # 単位が違う数を素直に拾ってしまう既知の癖(QUANTITY_MAP の comparable で外す)
    assert W18.parse_n_real("6事業者/出口=**未取得**") == 6.0
    assert W18.parse_n_real("PLATEAU DEM 2m(v1で使用)") == 2.0


def test_parse_depth_and_gate():
    assert W18.parse_depth("2") == 2
    assert W18.parse_depth("**0**") == 0
    assert W18.parse_depth("2(在館・待ち行列の集約のみ)") == 2
    assert W18.parse_depth("0(観察のみ)") == 0
    assert W18.parse_depth("") == 0
    assert W18.parse_gate("✔") is True
    assert W18.parse_gate("✔(日陰・体力)") is True
    assert W18.parse_gate("△") is False
    assert W18.parse_gate("—") is False


def test_weight_formula_and_cap():
    assert W18.weight(None) == 1.0
    assert W18.weight(0) == 1.0
    assert W18.weight(9) == pytest.approx(2.0)
    assert W18.weight(99) == pytest.approx(3.0)
    assert W18.weight(10**9) == W18.W_CAP  # 上限 6


# ---------------------------------------------------------------- 指標の算術


def _synthetic_rows() -> list[dict[str, str]]:
    """3クラスの合成カタログ。重みが手で出せる値(9 / 99 / なし)にしてある。"""
    return [
        {"#": "1", "型": "E", "クラス": "A", "現実数量(bbox/区)": "9",
         "v1状態": "", "v2現在d": "0", "初回後d": "2", "gate": "✔", "陣": ""},
        {"#": "2", "型": "P", "クラス": "B", "現実数量(bbox/区)": "99",
         "v1状態": "", "v2現在d": "0", "初回後d": "4", "gate": "✔", "陣": ""},
        {"#": "3", "型": "N", "クラス": "C", "現実数量(bbox/区)": "空欄",
         "v1状態": "", "v2現在d": "0", "初回後d": "3", "gate": "—", "陣": ""},
    ]


def test_compute_index_known_answers():
    # w_A=2, w_B=3, w_C=1 → Σw=6
    # 実装: A(N_sim=9=一致)・C(数量なし)。B は未実装。
    out = W18.compute_index(
        _synthetic_rows(),
        implemented={"A": ["W1"], "C": ["W7"]},
        n_sim={"A": 9.0, "C": 12.0},
        comparable={"A": True, "C": False},
    )
    v = out["vector"]
    assert out["weight_total"] == pytest.approx(6.0)
    # C(被覆) = 門を通った実装済み(d≥1) = A のみ → 2/6
    assert v["C"] == pytest.approx(2.0 / 6.0, abs=1e-6)
    assert v["C_quantified"] == pytest.approx(2.0 / 6.0, abs=1e-6)
    # Q = w_A·min(1, 9/9) / 6 = 2/6
    assert v["Q"] == pytest.approx(2.0 / 6.0, abs=1e-6)
    # D = Σ_G w·d /(4Σw) = (2·2 + 3·0)/(4·6)  ※C は門を通っていないので計上外
    assert v["D"] == pytest.approx(4.0 / 24.0, abs=1e-6)
    assert v["V"] == 0.0 and v["R"] is None
    assert out["X"] == 0.0
    # 死蔵候補 = 実装済み・N_real なし・未検証 → C
    assert out["dead_stock_candidates"] == ["C"]
    assert out["orphans"] == []
    assert [c["class"] for c in out["per_class"]] == ["A", "B", "C"]
    assert out["per_class"][1]["depth"] == 0  # 未実装は d=0


def test_compute_index_commission_and_undercount():
    # A を 18(=2倍)実装 → X = w_A·(2−1)/Σw = 2/6・Q は上振れを加点しない(min(1,·)=1)
    over = W18.compute_index(
        _synthetic_rows(), {"A": ["W1"]}, {"A": 18.0}, {"A": True}
    )
    assert over["X"] == pytest.approx(2.0 / 6.0, abs=1e-6)
    assert over["vector"]["Q"] == pytest.approx(2.0 / 6.0, abs=1e-6)
    # A を 3 しか実装しない → Q = w_A·(3/9)/Σw、X=0
    under = W18.compute_index(
        _synthetic_rows(), {"A": ["W1"]}, {"A": 3.0}, {"A": True}
    )
    assert under["X"] == 0.0
    assert under["vector"]["Q"] == pytest.approx(2.0 * (3.0 / 9.0) / 6.0, abs=1e-6)


def test_compute_index_on_frozen_catalog_is_bounded():
    from shibuya.manifest.world_catalog import load_world_catalog

    cat = load_world_catalog()
    out = W18.compute_index(list(cat.rows), {}, {}, {})
    for key in ("C", "C_quantified", "Q", "D", "V"):
        assert 0.0 <= out["vector"][key] <= 1.0
    assert out["vector"]["C"] == 0.0  # 何も実装していなければ被覆 0
    assert out["X"] == 0.0
    # 分母は 57 クラス全部(実装済みだけではない)
    assert len(out["per_class"]) == cat.n_classes
    assert out["weight_total"] == pytest.approx(
        sum(W18.weight(W18.parse_n_real(r["現実数量(bbox/区)"])) for r in cat.rows)
    )


def test_alias_and_quantity_maps_point_at_real_classes():
    from shibuya.manifest.world_catalog import load_world_catalog

    known = {row["クラス"] for row in load_world_catalog().rows}
    for src, dst in W18.CLASS_ALIASES.items():
        assert dst in known, f"別名の行き先がカタログに無い: {src} -> {dst}"
        assert src not in known, f"別名の元がカタログのクラス名と衝突: {src}"
    for name in W18.QUANTITY_MAP:
        assert name in known, f"数量表のクラスがカタログに無い: {name}"


# ---------------------------------------------------------------- 封印


def test_seal_member_hash_is_deterministic_and_order_free(tmp_path):
    root = tmp_path
    layer = root / "secret"
    layer.mkdir()
    (layer / "b.csv").write_bytes(b"beta")
    (layer / "a.csv").write_bytes(b"alpha")
    (layer / "sub").mkdir()
    (layer / "sub" / "c.csv").write_bytes(b"gamma")

    h1, members = W19.seal_layer(root, ("secret",))
    h2, members2 = W19.seal_layer(root, ("secret",))
    assert h1 == h2
    assert [m["path"] for m in members] == [m["path"] for m in members2]
    assert len(members) == 3
    # 中身が変われば封印も変わる
    (layer / "a.csv").write_bytes(b"ALPHA")
    h3, _ = W19.seal_layer(root, ("secret",))
    assert h3 != h1
    # 単一ファイル層も同じ規則
    (root / "one.json").write_bytes(b"{}")
    h4, one = W19.seal_layer(root, ("one.json",))
    assert len(one) == 1 and h4 == W19.C.sha256_bytes(one[0]["sha256"].encode("utf-8"))


def test_holdout_static_scan_flags_a_planted_reference(tmp_path):
    (tmp_path / "clean.py").write_text("x = 1\n", encoding="utf-8")
    assert W19.scan_build_sources(tmp_path) == {}
    (tmp_path / "bad.py").write_text("p = 'data/realworld/kddi_la/x.json'\n", encoding="utf-8")
    hits = W19.scan_build_sources(tmp_path)
    assert hits == {"bad.py": ["kddi_la"]}
    # 本モジュール自身は検査対象から外れる
    (tmp_path / W19.SELF_NAME).write_text("kddi_la shibuya_jinryu boundary_counts", encoding="utf-8")
    assert W19.SELF_NAME not in W19.scan_build_sources(tmp_path)


def test_holdout_tokens_cover_all_layers():
    assert set(W19.HOLDOUT_TOKENS) == {name for name, _ in W19.HOLDOUT_LAYERS}
    assert W19.SEAL_SCHEME in {"D", "S", "P"}
    assert W19.SEALED_UTC.endswith("Z")


# ---------------------------------------------------------------- 検収パック


def test_gate_table_markdown_lists_failures():
    headers = [
        {
            "stage": "W1",
            "outputs": [{"sha256": "a" * 64}],
            "gates": {
                "ok": {"value": 1, "expected": 1, "pass": True},
                "ng": {"value": 0, "expected": 202, "pass": False},
            },
        }
    ]
    md = W20.gate_table_markdown(headers)
    assert "PASS 1 / FAIL 1" in md
    assert "| W1 | ng | 0 | 202 |" in md
    assert "| W1 | ok | 1 | 1 | PASS |" in md
    assert "なし。" not in md
    # 先頭で build_hash を名乗る(パックの自己識別)
    assert f"- build_hash: `{W20.upstream_build_hash(headers)}`" in md.splitlines()[2]


def test_gate_table_markdown_when_all_pass():
    md = W20.gate_table_markdown(
        [
            {
                "stage": "W0",
                "outputs": [],
                "gates": {"a": {"value": 1, "expected": None, "pass": True}},
            }
        ]
    )
    assert "なし。" in md
    assert "| W0 | a | 1 | - | PASS |" in md


def test_upstream_build_hash_is_output_digest_chain():
    """パックの build_hash = 出力 sha256 を W 番号順に連ねた sha256(build.run と同じ作り方)。"""
    headers = [
        {"stage": "W0", "outputs": [{"sha256": "0" * 64}, {"sha256": "1" * 64}]},
        {"stage": "W1", "outputs": [{"sha256": "2" * 64}]},
    ]
    want = C.sha256_bytes(("0" * 64 + "1" * 64 + "2" * 64).encode("utf-8"))
    assert W20.upstream_build_hash(headers) == want
    assert len(W20.upstream_build_hash(headers)) == 64
    # 上流の出力が1バイトでも変われば別値になる
    headers[1]["outputs"][0]["sha256"] = "3" * 64
    assert W20.upstream_build_hash(headers) != want


def test_math_helpers_are_pure():
    # weight は方法論の式そのもの
    for n in (1, 10, 1000):
        assert W18.weight(n) == pytest.approx(min(6.0, 1.0 + math.log10(1.0 + n)))
