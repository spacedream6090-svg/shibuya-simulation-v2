"""W14/W15 → レンダラの結線: 凍結文があれば使い、無ければ従来の合成文。

対応する仕様行
- 知覚契約書 §1 条5「文面凍結」= ``templates`` 本体と ``template_sha256`` は**不変**。
- §2.4 ⑧「同セル・同時間帯の2体で B0-B4 のバイト差分がゼロ」(=W15 のゲート
  「同セル2体でバイト差分ゼロ」と同じ検査)。
- §2.2 群予算(セル依存 B2+B4+B4b ≤ 250 tok)・§3.2 ``B2.signage`` 25 / ``B2.visible`` 60。
- §5「B2 のバイト列ハッシュ = prefix キャッシュ鍵 = 変化検出器 = dormant 再送抑止」。
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.perception import templates as T
from shibuya.perception.normalize import AgentDependentWordError
from shibuya.perception.renderer import PerceptionAssets, Renderer, _load_frozen_text
from shibuya.world.state import World

FROZEN_TEMPLATE_SHA256 = "161fe181bc325f003d874fb5c91e6142c01449fb09ac5f8b377b715a945608de"
SHARED_BLOCKS = ("B0", "B1", "B2", "B3", "B4", "B4b")

SIGNAGE = "ベーカリー宮下の表示。飲食店。毎日7時から19時。価格帯は低め。"
CELL_STATIC = "一辺100メートルの地上の区画で、物販店と飲食店が見える"
#: 結線枠(``w15_cell_static.TOKEN_CAP`` 45 tok = 90 字 / ``B2.signage`` 25 tok = 50 字)。
CELL_STATIC_MAX_CHARS = 90
SIGNAGE_MAX_CHARS = 50


def build(n_agents: int = 8, n_cells: int = 4, seed: int = 1):
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_agents)
    a.cell[:] = 0
    a.kind[:] = AgentKind.VISITOR
    w.cells.density[:] = w.compute_density(a.cell)
    return w, a


def with_frozen(w: World, *, signage: str = "", static: str = "") -> PerceptionAssets:
    """合成資産に凍結文を差し込む(``PerceptionAssets.load`` が作る形と同じ)。"""
    base = PerceptionAssets.synthetic(w)
    return replace(
        base,
        poi_signage=tuple(signage for _ in range(len(base.poi_name))),
        cell_static=tuple(static for _ in range(base.n_cells)),
        frozen_sources={"w14_signage.parquet": "ab" * 32} if signage else {},
    )


# ---------------------------------------------------------------- テンプレは不変
def test_template_sha256_is_still_frozen():
    """結線でテンプレ本体を触っていない(凍結 SHA 161fe181… が動かない)。"""
    assert T.template_sha256() == FROZEN_TEMPLATE_SHA256


# ---------------------------------------------------------------- 切替(あり/なし)
def test_without_frozen_text_b2_is_the_synthesized_one():
    w, a = build()
    out = Renderer(w, a, seed=7).render(0, 760, 3)
    b2 = out.blocks["B2"].decode("utf-8")
    assert "の店頭" in b2  # 合成の可視物リスト
    assert "の表示。営業は" in b2  # 合成の看板文
    assert CELL_STATIC not in b2


def test_frozen_cell_static_replaces_the_visible_line_only():
    w, a = build()
    plain = Renderer(w, a, seed=7).render(0, 760, 3).blocks["B2"].decode("utf-8")
    frozen = (
        Renderer(w, a, assets=with_frozen(w, static=CELL_STATIC), seed=7)
        .render(0, 760, 3)
        .blocks["B2"]
        .decode("utf-8")
    )
    assert f"[B2 可視] 見えるもの: {CELL_STATIC}。" in frozen
    assert "の店頭" not in frozen
    # 置き換えるのは可視物の行だけ: 場所・路面・看板・地物の行は残る
    for label in ("[B2 場所]", "[B2 路面]", "[B2 看板]", "[B2 地物]"):
        assert label in frozen and label in plain
    assert plain != frozen


def test_frozen_signage_replaces_the_signage_body():
    w, a = build()
    b2 = (
        Renderer(w, a, assets=with_frozen(w, signage=SIGNAGE), seed=7)
        .render(0, 760, 3)
        .blocks["B2"]
        .decode("utf-8")
    )
    assert f"〔素性: 店頭表示・命令文除去済〕{SIGNAGE}" in b2
    assert "の表示。営業は" not in b2


def test_frozen_text_changes_the_b2_hash_and_prefix_key():
    """§5 ハッシュ三役: 文面が変われば prefix 鍵も変わる(キャッシュの取り違えなし)。"""
    w, a = build()
    plain = Renderer(w, a, seed=7).render(0, 760, 3)
    frozen = Renderer(w, a, assets=with_frozen(w, static=CELL_STATIC), seed=7).render(0, 760, 3)
    assert plain.block_hashes["B2"] != frozen.block_hashes["B2"]
    assert plain.prefix_key != frozen.prefix_key
    for b in ("B0", "B1", "B3", "B4", "B4b"):
        assert plain.blocks[b] == frozen.blocks[b], b


# ---------------------------------------------------------------- §2.4 ⑧ / W15 ゲート
def test_two_agents_in_the_same_cell_get_identical_shared_bytes():
    """W15 のゲート「同セル 2 体でバイト差分ゼロ」を描画側で確かめる。"""
    w, a = build()
    r = Renderer(w, a, assets=with_frozen(w, signage=SIGNAGE, static=CELL_STATIC), seed=7)
    x, y = r.render(0, 760, 3), r.render(1, 760, 3)
    for b in SHARED_BLOCKS:
        assert x.blocks[b] == y.blocks[b], b
    assert x.shared_static_bytes() == y.shared_static_bytes()


def test_individual_word_in_frozen_text_is_caught_at_render_time():
    """凍結文に個体語が混ざっていたら描画が落ちる(多重防御・W15 の ingest でも弾く)。"""
    w, a = build()
    poisoned = with_frozen(w, static="P-12 が立っている区画")
    with pytest.raises(AgentDependentWordError):
        Renderer(w, a, assets=poisoned, seed=7).render(0, 760, 3)


# ---------------------------------------------------------------- 予算
def test_budgets_hold_with_frozen_text_at_the_cap():
    """結線枠いっぱい(``B2.visible`` 60 tok=120 字・``B2.signage`` 25 tok=50 字)でも
    ブロック予算 B2 150 と群予算 250 に収まる。"""
    w, a = build()
    static = "あ" * CELL_STATIC_MAX_CHARS
    signage = "い" * SIGNAGE_MAX_CHARS
    out = Renderer(w, a, assets=with_frozen(w, signage=signage, static=static), seed=7).render(
        0, 760, 3
    )
    assert out.within_group_budgets(), out.group_tokens
    assert out.tokens_est["B2"] <= T.BLOCK_TOKEN_BUDGET["B2"], out.tokens_est
    assert static in out.blocks["B2"].decode("utf-8")


def test_oversized_frozen_text_falls_back_to_the_synthesized_list():
    """枠を超える凍結文は切り詰めで落ち、**従来の合成可視物リストへ戻る**(壊れない)。"""
    w, a = build()
    out = Renderer(w, a, assets=with_frozen(w, static="あ" * 400), seed=7).render(0, 760, 3)
    b2 = out.blocks["B2"].decode("utf-8")
    assert "あああ" not in b2
    assert "の店頭" in b2 or "見えるもの: なし" in b2
    assert out.within_group_budgets()


# ---------------------------------------------------------------- ファイル有無で切替
def test_switch_is_decided_by_file_presence_and_records_sha(tmp_path: Path):
    """``_load_frozen_text``: ファイルが無ければ空文字・在れば読んで sha を記録する。"""
    sources: dict[str, str] = {}
    keys = ["p_a", "p_b"]
    assert _load_frozen_text(tmp_path, "w14_signage.parquet", "poi_id", keys, sources) == ("", "")
    assert sources == {}

    pq.write_table(
        pa.table({"poi_id": pa.array(["p_b"]), "text": pa.array([SIGNAGE])}),
        tmp_path / "w14_signage.parquet",
    )
    got = _load_frozen_text(tmp_path, "w14_signage.parquet", "poi_id", keys, sources)
    assert got == ("", SIGNAGE)  # 凍結行の無い POI は空文字=合成文へフォールバック
    assert len(sources["w14_signage.parquet"]) == 64


def test_report_line_carries_the_frozen_sha():
    w, a = build()
    r = Renderer(w, a, assets=with_frozen(w, signage=SIGNAGE), seed=7)
    r.render(0, 760, 3)
    line = r.report()
    assert "w14_signage.parquet=" in line
    assert f"template_sha256={FROZEN_TEMPLATE_SHA256[:16]}" in line


def test_assets_flags():
    w, _ = build()
    assert not PerceptionAssets.synthetic(w).uses_frozen_signage
    assert with_frozen(w, signage=SIGNAGE).uses_frozen_signage
    assert with_frozen(w, static=CELL_STATIC).uses_frozen_cell_static


# ---------------------------------------------------------------- 実データ
@pytest.mark.skipif(
    not Path("data/world/v2/w8_t1_cell.parquet").exists(), reason="data/world/v2 が無い"
)
def test_real_assets_load_without_frozen_files(capsys):
    """実資産には凍結ファイルがまだ無い=従来の合成文のまま(結線が既定を変えない)。"""
    d = Path("data/world/v2")
    w = World.load(d)
    assets = PerceptionAssets.load(d, w)
    n = 50
    a = AgentState(n)
    g = np.random.default_rng(3)
    a.cell[:] = g.integers(0, w.n_cells, size=n)
    a.xy[:] = w.assets.cell_centroid[a.cell]
    r = Renderer(w, a, assets=assets, seed=13)
    worst = {k: 0 for k in T.GROUP_TOKEN_BUDGET}
    for i in range(n):
        out = r.render(i, tick=750, wake_reason=3)
        assert out.within_group_budgets(), out.group_tokens
        for k, v in out.group_tokens.items():
            worst[k] = max(worst[k], v)
    expected = (d / "w14_signage.parquet").exists()
    assert assets.uses_frozen_signage is expected
    with capsys.disabled():
        print(
            f"\n[wiring] frozen_sources={dict(assets.frozen_sources)} "
            f"worst_group={worst} (上限 {dict(T.GROUP_TOKEN_BUDGET)})"
        )


@pytest.mark.skipif(
    not Path("data/world/v2/w8_t1_cell.parquet").exists(), reason="data/world/v2 が無い"
)
def test_real_assets_with_max_length_frozen_text_stay_within_budget(capsys):
    """**実資産 520 セル**に枠いっぱいの凍結文を入れても B2 150 / セル群 250 に収まる。

    (W15 の生成上限を 60 tok に決めた根拠。150 tok をそのまま載せると群予算を超える=
    親判断待ちの delta 案件。)
    """
    d = Path("data/world/v2")
    w = World.load(d)
    base = PerceptionAssets.load(d, w)
    assets = replace(
        base,
        poi_signage=tuple("い" * SIGNAGE_MAX_CHARS for _ in range(len(base.poi_name))),
        cell_static=tuple("あ" * CELL_STATIC_MAX_CHARS for _ in range(base.n_cells)),
    )
    a = AgentState(base.n_cells)
    a.cell[:] = np.arange(base.n_cells)
    a.xy[:] = w.assets.cell_centroid[a.cell]
    r = Renderer(w, a, assets=assets, seed=13)
    worst_b2 = 0
    worst_cell = 0
    for i in range(base.n_cells):
        out = r.render(i, tick=750, wake_reason=3)
        assert out.within_group_budgets(), (i, out.group_tokens)
        worst_b2 = max(worst_b2, out.tokens_est["B2"])
        worst_cell = max(worst_cell, out.group_tokens["cell"])
    with capsys.disabled():
        print(
            f"\n[wiring] 枠いっぱいの凍結文: 最大 B2={worst_b2} tok(上限 "
            f"{T.BLOCK_TOKEN_BUDGET['B2']})・最大セル群={worst_cell} tok(上限 "
            f"{T.GROUP_TOKEN_BUDGET['cell']})"
        )
    assert worst_b2 <= T.BLOCK_TOKEN_BUDGET["B2"]
    assert worst_cell <= T.GROUP_TOKEN_BUDGET["cell"]


@pytest.mark.skipif(
    not Path("data/world/v2/w8_t1_cell.parquet").exists(), reason="data/world/v2 が無い"
)
def test_w15_token_cap_derivation_still_holds(capsys):
    """``w15_cell_static.TOKEN_CAP`` の導出を実資産で再測する。

    導出 = B2 ブロック予算 150 − 「他の B2 行」の最大合計([B2 場所]+[B2 路面]+[B2 看板]
    +[B2 地物])。W6/W8 が更新されて他行が伸びたらここで気づく。
    """
    from shibuya.build.lang import w15_cell_static as W15
    from shibuya.perception.channels import estimate_tokens

    d = Path("data/world/v2")
    w = World.load(d)
    base = PerceptionAssets.load(d, w)
    assets = replace(
        base,
        poi_signage=tuple("い" * SIGNAGE_MAX_CHARS for _ in range(len(base.poi_name))),
        cell_static=tuple("" for _ in range(base.n_cells)),
    )
    a = AgentState(base.n_cells)
    a.cell[:] = np.arange(base.n_cells)
    a.xy[:] = w.assets.cell_centroid[a.cell]
    r = Renderer(w, a, assets=assets, seed=13)
    worst_other = 0
    for i in range(base.n_cells):
        lines = r.render(i, tick=750, wake_reason=3).blocks["B2"].decode("utf-8").splitlines()
        other = [ln for ln in lines if not ln.startswith("[B2 可視]")]
        worst_other = max(worst_other, sum(estimate_tokens(ln) for ln in other))
    headroom = T.BLOCK_TOKEN_BUDGET["B2"] - worst_other
    with capsys.disabled():
        print(
            f"\n[wiring] B2 の他行 最大 {worst_other} tok → 凍結文の枠 {headroom} tok "
            f"(宣言 {W15.TOKEN_CAP})"
        )
    assert W15.TOKEN_CAP <= headroom, "W15 の TOKEN_CAP が B2 予算を割る=枠の再導出が要る"
