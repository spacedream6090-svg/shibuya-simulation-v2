"""W15 B2 セル静的文: プロンプト生成の決定論・取り込みゲート・個体語の検出・上限。

対応する仕様行
- §1 W15「入力 W2+W8・出力 セル静的記述 150tok・**同セル2体でバイト差分ゼロ**・呼 ≈600」
- D-W18「固有名詞は入力由来のみ」
- 知覚契約書 §2.2 B2(150 tok)・§2.4 ⑧(B0-B4 に個体依存語を入れない)・
  §3.2 ``B2.visible`` 60 tok(=結線枠)・§5(B2 はセル代表点から見えるもの)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shibuya.build.geo import common as C
from shibuya.build.lang import common as L
from shibuya.build.lang import w15_cell_static as W15

from .conftest import duplicate_reps, write_responses

DATA_DIR = Path("data/world/v2")

#: ゲートを全部通る想定の文面(区画IDと広さは書かない・「など」を使わない・
#: 個数を数字で書かない=2026-09-09 の system 改訂に合わせた形)。
GOOD = {
    "g0_0_GL": "地上の区画で、物販店と飲食店の店頭が見え、駅の出入口が見える",
    "g1_0_GL": "地上の区画で、コンビニエンスストアと物販店が通りに面している",
    "g0_1_UG": "地下の通路に面した区画で、目印になる施設が見える",
}


def passed_except(res, skip: set[str]) -> bool:
    return all(g.to_json()["pass"] for g in res.gates if g.name not in skip)


# ---------------------------------------------------------------- プロンプト生成
def test_prompts_are_deterministic_and_keyed_by_cell(world_dir: Path):
    a = W15.build_prompts(world_dir)
    b = W15.build_prompts(world_dir)
    assert L.prompts_sha256(a) == L.prompts_sha256(b)
    assert [p.id for p in a] == ["g0_0_GL", "g1_0_GL", "g0_1_UG"]
    assert len({p.id for p in a}) == len(a)  # place_id は一意(セルの関数)


def test_prompt_carries_w2_w6_w8_facts(world_dir: Path):
    """W2(層・街区の有無)・W8(可視物・目印)・W6(多い店の種別)がプロンプトに載る。"""
    by_id = {p.id: p.user for p in W15.build_prompts(world_dir)}
    u = by_id["g0_0_GL"]
    assert "層: 地上" in u
    assert "街区: あり" in u  # 第3回: 数ではなく あり/なし(数字をプロンプトから消す)
    # W8 T1 の順序=可視視点数の降順(p_a 30 > p_b 20 > exit 10)
    assert u.index("Journal Standard") < u.index("ベーカリー宮下")
    assert "渋谷駅西口" in u  # exit ラベル(renderer と同じ組み立て)
    assert "多い店の種別: 物販店" in u  # 第3回: 件数つきの構成ではなく 1 語
    assert "層: 地下" in by_id["g0_1_UG"]
    assert "街区: なし" in by_id["g0_1_UG"]


def test_prompt_lists_at_most_two_names_each(world_dir: Path):
    """第3回: 可視物・目印は**上位 2 件**だけ渡す(too_long 181/188 の直接原因を断つ)。"""
    assert W15.MAX_VISIBLE_POI == 2 and W15.MAX_VISIBLE_LANDMARK == 2
    vis, lands = W15._visible_by_cell(world_dir)
    assert all(len(v) <= 2 for v in vis) and all(len(x) <= 2 for x in lands)
    # 選び方は決定論(可視視点数の降順 → target_id 昇順)= renderer と同じ順序の先頭から
    assert vis[0] == ["物販店(Journal Standard)", "飲食店(ベーカリー宮下)"]


def test_prompt_carries_the_length_regex(world_dir: Path):
    """第3回: 長さは指示ではなく**文法**で保証する(fleet_gen → structured_outputs)。"""
    ps = W15.build_prompts(world_dir)
    assert all(p.regex == W15.PROMPT_REGEX for p in ps)
    assert W15.PROMPT_REGEX == "[^" + chr(92) + "n]{10,88}"
    row = ps[0].to_json()
    assert row["regex"] == W15.PROMPT_REGEX
    # 88 字 = 44 tok ≤ TOKEN_CAP 45(= 枠超えが物理的に起きない)
    from shibuya.perception.channels import estimate_tokens

    assert estimate_tokens("あ" * W15.REGEX_MAX_CHARS) <= W15.TOKEN_CAP


def test_w14_prompt_rows_have_no_regex_key(world_dir: Path):
    """W14 は生成済み=**行の形を動かさない**(regex キーを足すと SHA が動く)。"""
    from shibuya.build.lang import w14_signage as W14

    assert "regex" not in W14.build_prompts(world_dir)[0].to_json()


def test_prompt_forbids_individual_and_dynamic_content(world_dir: Path):
    """§2.4 ⑧: 個体語・時刻・天候・混雑を書かせない指示が入っている。"""
    sysmsg = W15.build_prompts(world_dir)[0].system
    assert "あなた" in sysmsg and "使わない" in sysmsg
    assert "時刻" in sysmsg and "天候" in sysmsg and "混雑" in sysmsg
    assert f"{W15.CHAR_LIMIT}字以内" in sysmsg


def test_prompt_states_the_first_and_second_round_fixes(world_dir: Path):
    """第1回・第2回生成の不合格要因を system が名指しで禁じている。

    第1回: 「など」106・個数の数字 50・一人称 5・区画IDの書き写し。
    第2回: too_long 181/188(名前を全部列挙)・一人称 8。
    """
    p = W15.build_prompts(world_dir)[0]
    assert "「など」" in p.system and "「等」" in p.system
    assert "数を書かない" in p.system
    # 一人称の禁止は**冒頭**へ(第2回でも 8 件出たため)
    assert p.system.startswith("あなたは街の一区画を**三人称の客観描写**")
    assert "「私」「僕」「我々」「あなた」など人を指す語は絶対に使いません" in p.system
    assert "区画IDと区画の広さは書かない" in p.system
    assert f"名前を最大{W15.MAX_NAMES_IN_TEXT}つまで" in p.system
    assert f"全体で{W15.CHAR_LIMIT}字以内の**1文**。長さが最優先" in p.system
    # user 側にも短い念押しを置く(system を読み飛ばす場合の保険)
    assert "区画IDと広さは書かない" in p.user
    assert "名前は最大2つまで" in p.user and "数を書かない" in p.user


# ---------------------------------------------------------------- 取り込み
def test_ingest_freezes_good_answers(world_dir: Path, tmp_path: Path):
    resp = write_responses(tmp_path / "r.jsonl", duplicate_reps(GOOD))
    rep = W15.ingest(world_dir, resp)
    assert [v.id for v in rep.frozen] == list(GOOD), rep.reason_counts()
    assert rep.rep_match_rate == 1.0
    assert all(v.tokens <= W15.TOKEN_CAP for v in rep.frozen)
    assert all(v.tokens <= W15.SPEC_TOKEN_CAP for v in rep.frozen)


def test_trailing_kuten_is_stripped_for_the_template(world_dir: Path, tmp_path: Path):
    """テンプレ ``B2.visible`` が「。」を持つので、凍結文の末尾句点は落とす。"""
    resp = write_responses(tmp_path / "r.jsonl", duplicate_reps(GOOD))
    frozen = {v.id: v.text for v in W15.ingest(world_dir, resp).frozen}
    assert all(not t.endswith("。") for t in frozen.values())
    assert frozen["g0_1_UG"].endswith("目印になる施設が見える")


@pytest.mark.parametrize(
    "text,reason",
    [
        # 個体語(§2.4 ⑧)= 同セル 2 体でバイト差分が出る文
        ("あなたの正面に物販店が見える", "I1_individual"),
        ("私の右手に飲食店がある", "I1_individual"),
        ("P-12 が立っている物販店の前", "I2_agent_dependent"),
        # 入力に無い固有名詞
        ("スクランブル交差点に面した区画", "N5_known_proper"),
        # 「宮下公園」は入力に「ベーカリー宮下」があるので N3 では落ちない(分解して通す)。
        # 入力に痕跡の無い地物名を使う。
        ("青葉公園に面した区画", "N3_place_suffix"),
        ("ドンキホーテが見える区画", "N5_known_proper"),
        # 上位 2 件に絞ったあとの「3 件目の名前」= そのセルの入力には無い名前
        ("地上の区画で、Journal Standardとベーカリー宮下とローソンが見える", "N2_katakana"),
        # 入力に無い数字
        ("一辺100メートルの区画で、飲食店が42軒ある", "N4_digit"),
        # 漢数字による迂回
        ("一辺100メートルの区画で、物販店が七軒ある", "N6_kansuji"),
        # 評価語・誘導
        ("一辺100メートルの人気の区画", "E1_evaluative"),
        ("一辺100メートルの区画。ぜひ立ち寄るとよい", "E2_inducement"),
        # 省略記法(§2.4 ⑥)
        ("物販店や飲食店などが見える区画", "A1_abbreviation"),
    ],
)
def test_bad_answers_are_rejected(world_dir: Path, tmp_path: Path, text: str, reason: str):
    rows = duplicate_reps({**GOOD, "g0_0_GL": text})
    resp = write_responses(tmp_path / "r.jsonl", rows)
    bad = {v.id: v for v in W15.ingest(world_dir, resp).rejected}
    assert "g0_0_GL" in bad, f"見逃した: {text}"
    assert reason in bad["g0_0_GL"].reasons, bad["g0_0_GL"].reasons


def test_over_the_wiring_cap_is_rejected(world_dir: Path, tmp_path: Path):
    """結線枠(``B2.visible`` 60 tok = 120 字)を超えた文は凍結しない。"""
    long_text = "一辺100メートルの地上の区画で、物販店と飲食店が見える" * 6
    rows = duplicate_reps({**GOOD, "g0_0_GL": long_text})
    resp = write_responses(tmp_path / "r.jsonl", rows)
    bad = {v.id: v for v in W15.ingest(world_dir, resp).rejected}
    assert "too_long" in bad["g0_0_GL"].reasons


def test_rep_mismatch_is_rejected(world_dir: Path, tmp_path: Path):
    rows = [
        (i, r, t + "だ" if (i, r) == ("g1_0_GL", 1) else t)
        for i, r, t in duplicate_reps(GOOD)
    ]
    resp = write_responses(tmp_path / "r.jsonl", rows)
    rep = W15.ingest(world_dir, resp)
    assert "rep_mismatch" in {r for v in rep.rejected for r in v.reasons}


# ---------------------------------------------------------------- 段階本体
def test_run_without_responses_writes_prompts_only(world_dir: Path):
    res = W15.run(C.Ctx(data=world_dir, out=world_dir))
    assert passed_except(res, {"cell_rows"})
    assert [o["path"] for o in res.outputs] == ["w15_prompts.jsonl"]
    assert not (world_dir / "w15_cell_static.parquet").exists()


def test_run_with_responses_freezes(world_dir: Path):
    write_responses(world_dir / "w15_responses.jsonl", duplicate_reps(GOOD))
    res = W15.run(C.Ctx(data=world_dir, out=world_dir))
    assert passed_except(res, {"cell_rows"}), {g.name: g.to_json() for g in res.gates}
    assert [o["path"] for o in res.outputs] == [
        "w15_prompts.jsonl",
        "w15_cell_static.parquet",
        "w15_gates.json",
    ]
    gates = {g.name: g.value for g in res.gates}
    assert gates["frozen_individual_word_violations"] == 0
    assert gates["individual_word_violations_all"] == 0
    assert gates["frozen_place_id_unique"] == 3
    assert gates["tokens_max_within_spec"] <= W15.SPEC_TOKEN_CAP
    assert res.catalog_classes == []  # 既存クラスの言語化=新規クラスは埋めない


def test_gate_population_is_the_frozen_rows(world_dir: Path, tmp_path: Path):
    """**ゲートの母集団は凍結行**(親決定 2026-09-09)。

    第3回の W15 は fail_rate 0.0154 で合格しながら、rep 不一致 2 件と個体語 3 件"だけ"で
    段階が落ちていた。どの行も凍結されておらず、レンダラは合成文へフォールバックする
    (=世界の品質は保たれている)ので、欠陥は fail_rate 側で一括して数え、個別ゲートで
    **二重に落とさない**。
    """
    rows = [
        (i, r, t + "だ" if (i, r) == ("g1_0_GL", 1) else t)
        for i, r, t in duplicate_reps(GOOD)
    ]
    resp = write_responses(tmp_path / "r.jsonl", rows)
    rep = W15.ingest(world_dir, resp)

    assert rep.rep_mismatch_count == 1
    assert rep.rep_match_rate < 1.0                 # 全応答での実測=報告値
    assert rep.frozen_rep_match_rate == 1.0         # 凍結行は全一致(pin)
    assert "g1_0_GL" not in {v.id for v in rep.frozen}
    assert "rep_mismatch" in {r for v in rep.rejected for r in v.reasons}

    gates = {g.name: g.to_json() for g in L.gate_rows(rep, max_fail_rate=1.0)}
    assert gates["frozen_rep_byte_match_rate"]["value"] == 1.0
    assert gates["rep_byte_match_rate_all"]["expected"] is None  # 報告のみ
    assert gates["rep_mismatch_count"]["value"] == 1
    assert all(g["pass"] for g in gates.values()), gates


def test_individual_word_gate_counts_only_frozen_rows(world_dir: Path):
    """個体語も同じ: 合否は凍結行 0、全応答の件数は報告値。"""
    write_responses(
        world_dir / "w15_responses.jsonl",
        duplicate_reps({**GOOD, "g0_0_GL": "私の正面に物販店と飲食店が見える"}),
    )
    res = W15.run(C.Ctx(data=world_dir, out=world_dir))
    gates = {g.name: g.to_json() for g in res.gates}
    assert gates["frozen_individual_word_violations"] == {
        "value": 0, "expected": 0, "pass": True
    }
    assert gates["individual_word_violations_all"]["value"] == 1
    assert gates["individual_word_violations_all"]["pass"]  # 報告のみ=落とさない
    # 落ちるのは fail_rate だけ(1/3 > 0.05)。個体語ゲートでは落ちない。
    failed = {n for n, g in gates.items() if not g["pass"]}
    assert failed == {"cell_rows", "fail_rate_within_threshold"}, failed


def test_run_is_reproducible(world_dir: Path):
    write_responses(world_dir / "w15_responses.jsonl", duplicate_reps(GOOD))
    ctx = C.Ctx(data=world_dir, out=world_dir)
    assert W15.run(ctx).to_json() == W15.run(ctx).to_json()


# ---------------------------------------------------------------- 実データ
@pytest.mark.skipif(
    not (DATA_DIR / "w8_t1_cell.parquet").exists(), reason="data/world/v2 が無い"
)
def test_real_data_prompt_count_and_sha(capsys):
    """実資産で 520 セル(仕様の「≈600」は推定・C1 実測 520)。"""
    from shibuya.perception.channels import estimate_tokens

    prompts = W15.build_prompts(DATA_DIR)
    assert len(prompts) == W15.EXPECTED_CELL_ROWS
    assert len({p.id for p in prompts}) == len(prompts)
    toks = [estimate_tokens(p.system) + estimate_tokens(p.user) for p in prompts]
    with capsys.disabled():
        print(
            f"\n[W15] prompts={len(prompts)} sha={L.prompts_sha256(prompts)[:16]} "
            f"system_sha={C.sha256_bytes(W15.SYSTEM_PROMPT.encode('utf-8'))[:16]} "
            f"in_tok mean={sum(toks) / len(toks):.1f} max={max(toks)} "
            f"calls={len(prompts) * L.REPEAT}"
        )
