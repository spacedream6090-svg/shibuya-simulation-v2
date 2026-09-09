"""W14 看板(a)文面: プロンプト生成の決定論・取り込みゲート・固有名詞検査。

対応する仕様行
- §1 W14「同店2回生成でバイト一致(温度0)・文面SHA・呼 2,337」
- D-W18「固有名詞は入力(POI名)由来のみ(入力にない固有名詞を含む文は不合格)」
- 知覚契約書 §2.4 正規化規約 9 項・§3.2「看板・広告面1件 25 tok」
- 広告答申 §4「自由文をそのまま渡さない・構造化属性へ還元・命令文除去」
"""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from shibuya.build.geo import common as C
from shibuya.build.lang import common as L
from shibuya.build.lang import w14_signage as W14

from .conftest import duplicate_reps, write_responses

DATA_DIR = Path("data/world/v2")


def passed_except(res, skip: set[str]) -> bool:
    """``poi_rows``(実資産 2,337 の釘付け)以外のゲートが全部通ったか。"""
    return all(g.to_json()["pass"] for g in res.gates if g.name not in skip)

#: ゲートを全部通る想定の文面(店名・業種・営業時間・価格帯だけ)。
#: 営業時間の表現は **user プロンプトが渡す表現をそのまま使う**(2026-09-09 の圧縮規則)。
GOOD = {
    "p_a": "Journal Standardは物販店。平日は10時から22時。価格帯は中程度。",
    "p_b": "ベーカリー宮下は飲食店。毎日7時から19時。価格帯は低め。",
    "p_c": "ローソンはコンビニエンスストア。24時間営業。価格帯は中程度。",
    "p_d": "観世能楽堂の表示。平日は9時から17時30分。",
}


# ---------------------------------------------------------------- プロンプト生成
def test_prompts_are_deterministic(world_dir: Path):
    """同じ入力から 2 回作って SHA が一致する(§0-1 決定論)。"""
    a = W14.build_prompts(world_dir)
    b = W14.build_prompts(world_dir)
    assert L.prompts_sha256(a) == L.prompts_sha256(b)
    assert [p.id for p in a] == ["p_a", "p_b", "p_c", "p_d"]


def test_prompt_fields_match_fleet_gen_format(world_dir: Path):
    """``tools/gen/fleet_gen.py`` が読む欄が揃っている(温度0・seed固定・repeat 2)。"""
    p = W14.build_prompts(world_dir)[0].to_json()
    assert set(p) >= {"id", "system", "user", "max_tokens", "temperature", "seed", "repeat"}
    assert p["temperature"] == 0.0
    assert p["seed"] == L.SEED
    assert p["repeat"] == 2
    assert p["max_tokens"] == W14.MAX_TOKENS
    assert p["thinking"] is False


def test_prompt_states_the_three_rules(world_dir: Path):
    """プロンプトに「固有名詞」「評価語/誘導」「表記」の 3 規則が明記されている。"""
    sysmsg = W14.build_prompts(world_dir)[0].system
    assert "固有名詞" in sysmsg
    assert "評価語" in sysmsg and "命令文" in sysmsg
    assert "漢数字は使わない" in sysmsg
    assert f"{W14.CHAR_LIMIT}字以内" in sysmsg


@pytest.mark.parametrize(
    "content,hours,closed",
    [
        # 平日だけ営業 → 群にまとめる
        ("[[[600,1320]],[[600,1320]],[[600,1320]],[[600,1320]],[[600,1320]],[],[]]",
         "平日は10時から22時", "土曜、日曜"),
        # 全曜日 24 時間 → 「24時間営業(毎日)」(第1回生成の「毎日終日」は数字が無く、
        # モデルが 10 時-22 時を捏造して 74 件が N4 で落ちた)
        ("[[[0,1440]],[[0,1440]],[[0,1440]],[[0,1440]],[[0,1440]],[[0,1440]],[[0,1440]]]",
         "24時間営業(毎日)", "なし"),
        # 群の一部だけ営業 → 「平日」と書かず曜日を出す
        ("[[[1320,1560]],[],[],[],[],[],[]]", "月曜は22時から翌2時",
         "火曜、水曜、木曜、金曜、土曜、日曜"),
        ("[[[540,1050]],[[540,1050]],[[540,1050]],[[540,1050]],[[540,1050]],[],[]]",
         "平日は9時から17時30分", "土曜、日曜"),
        # 全曜日同一 → 毎日
        ("[" + ",".join(["[[600,1320]]"] * 7) + "]", "毎日10時から22時", "なし"),
        # 群の中で日ごとに違う → 代表日(営業分数が最大)1 帯 + 但し書き
        ("[[[420,1260]],[[420,1260]],[[420,1260]],[[420,1260]],[[420,1260]],"
         "[[480,1200]],[[480,1140]]]", "7時から21時(曜日で異なる)", "なし"),
        # 1 日に複数区間 + 群で違う → 2 帯だと 24 字を超えるので代表日 1 帯へ畳む
        ("[" + ",".join(["[[690,900],[1020,1320]]"] * 5 + ["[[690,1320]]"] * 2) + "]",
         "11時30分から22時(曜日と時間帯で異なる)", "なし"),
        # 2 帯が 24 字に収まるときは 2 帯のまま
        ("[" + ",".join(["[[600,1320]]"] * 5 + ["[[660,1260]]"] * 2) + "]",
         "平日は10時から22時、土日は11時から21時", "なし"),
    ],
)
def test_opening_hours_japanese(content: str, hours: str, closed: str):
    assert W14.format_opening_hours(content) == (hours, closed)


def test_opening_hours_phrase_stays_short(capsys):
    """**実資産**: 圧縮後の営業時間表現が 45 字の本文に収まる長さに落ちている。"""
    import re
    import statistics

    if not (DATA_DIR / "w7_plan_spec.parquet").exists():
        pytest.skip("data/world/v2 が無い")
    hs = [
        re.search(r"営業時間: (.*)", p.user).group(1)
        for p in W14.build_prompts(DATA_DIR)
    ]
    with capsys.disabled():
        print(
            f"\n[W14] 営業時間表現 平均 {statistics.mean(map(len, hs)):.1f} 字 / "
            f"最大 {max(map(len, hs))} 字 / 24 字超 {sum(1 for h in hs if len(h) > 24)} 件"
        )
    assert statistics.mean(map(len, hs)) <= 14
    assert max(map(len, hs)) <= 30


# ---------------------------------------------------------------- 取り込み
def test_ingest_freezes_good_answers(world_dir: Path, tmp_path: Path):
    resp = write_responses(tmp_path / "r.jsonl", duplicate_reps(GOOD))
    rep = W14.ingest(world_dir, resp)
    assert rep.n_prompts == 4
    assert [v.id for v in rep.frozen] == ["p_a", "p_b", "p_c", "p_d"], rep.reason_counts()
    assert rep.rep_match_rate == 1.0
    assert rep.fail_rate == 0.0
    assert all(v.tokens <= W14.TOKEN_CAP for v in rep.frozen)


def test_rep_mismatch_is_rejected(world_dir: Path, tmp_path: Path):
    """温度 0 なのに rep0/rep1 が違う店は凍結しない(§1 W14 ゲート)。"""
    rows = duplicate_reps(GOOD)
    rows = [(i, r, t + "。" if (i, r) == ("p_a", 1) else t) for i, r, t in rows]
    resp = write_responses(tmp_path / "r.jsonl", rows)
    rep = W14.ingest(world_dir, resp)
    bad = {v.id: v for v in rep.rejected}
    assert "p_a" in bad and "rep_mismatch" in bad["p_a"].reasons
    assert rep.rep_match_rate == 0.75


def test_missing_response_is_rejected_not_crashed(world_dir: Path, tmp_path: Path):
    rows = [r for r in duplicate_reps(GOOD) if r[0] != "p_c"]
    resp = write_responses(tmp_path / "r.jsonl", rows)
    rep = W14.ingest(world_dir, resp)
    assert {v.id for v in rep.rejected} == {"p_c"}
    assert rep.rejected[0].reasons == ("missing",)


@pytest.mark.parametrize(
    "text,reason",
    [
        ("Journal Standardの表示。渋谷駅の目の前。", "N5_known_proper"),
        ("Journal Standardの表示。ヒカリエの隣。", "N5_known_proper"),
        ("Journal Standardは物販店。平日は9時から21時。", "N4_digit"),
        ("Journal Standardの表示。Adidasも扱う。", "N1_latin"),
        ("Journal Standardの表示。ブランドはナイキ。", "N2_katakana"),
        ("Journal Standardの表示。宮下公園の前。", "N3_place_suffix"),
        ("Journal Standardの表示。歌庯場を併設。", "N7_kanji"),
        ("Journal Standardの表示。商品は七個。", "N6_kansuji"),
        ("Journal Standardの表示。月金は10時から22時。", "A1_weekday_abbr"),
        ("Journal Standardの表示。人気の物販店。", "E1_evaluative"),
        ("Journal Standardの表示。ぜひお立ち寄りを。", "E2_inducement"),
        ("Journal Standardの表示。今すぐご来店ください。", "E2_inducement"),
        ("Journal Standardの表示。あなたの街の物販店。", "I1_individual"),
        ("Journal Standardの表示。物販店など。", "A1_abbreviation"),
    ],
)
def test_bad_answers_are_rejected_with_the_right_rule(
    world_dir: Path, tmp_path: Path, text: str, reason: str
):
    """入力に無い固有名詞・数字・評価語・誘導・個体語・省略記法を弾く(陽性例)。"""
    rows = duplicate_reps({**GOOD, "p_a": text})
    resp = write_responses(tmp_path / "r.jsonl", rows)
    rep = W14.ingest(world_dir, resp)
    bad = {v.id: v for v in rep.rejected}
    assert "p_a" in bad, f"見逃した: {text}"
    assert reason in bad["p_a"].reasons, bad["p_a"].reasons


def test_input_derived_proper_nouns_pass(world_dir: Path, tmp_path: Path):
    """**陰性例**: 入力(POI 名)由来の固有名詞は通る。"""
    rows = duplicate_reps({**GOOD, "p_c": "ローソンの表示。コンビニエンスストア。24時間営業。"})
    resp = write_responses(tmp_path / "r.jsonl", rows)
    rep = W14.ingest(world_dir, resp)
    assert not rep.rejected, rep.reason_counts()


@pytest.mark.parametrize(
    "text,reason",
    [
        ("Journal Standardの表示。\n物販店。", "multiline"),
        ("", "empty"),
        ("Journal Standardの表示。" + "物販店です。" * 12, "too_long"),
    ],
)
def test_normalization_rules(world_dir: Path, tmp_path: Path, text: str, reason: str):
    """§2.4 の正規化(1行・空でない)と §3.2 の長さ上限。"""
    rows = duplicate_reps({**GOOD, "p_a": text})
    resp = write_responses(tmp_path / "r.jsonl", rows)
    rep = W14.ingest(world_dir, resp)
    bad = {v.id: v for v in rep.rejected}
    assert reason in bad["p_a"].reasons, bad["p_a"].reasons


def test_whitespace_and_quotes_are_normalized(world_dir: Path, tmp_path: Path):
    """全角空白・引用符・句点まわりの空白は正規化して凍結する(通したものを凍結)。

    句点のあとの空白を落とすのは、描画時に通る ``strip_imperatives`` が文単位で ``strip()``
    してから連結するため(凍結バイト列 = 描画バイト列 を保つ)。
    """
    raw = "  「Ｊournal Standardの表示。 物販店。」 "
    rows = duplicate_reps({**GOOD, "p_a": raw})
    resp = write_responses(tmp_path / "r.jsonl", rows)
    frozen = {v.id: v.text for v in W14.ingest(world_dir, resp).frozen}
    assert frozen["p_a"] == "Journal Standardの表示。物販店。"


def test_frozen_text_survives_strip_imperatives_bytewise(world_dir: Path, tmp_path: Path):
    """凍結文は描画側の命令文除去を通しても**バイトが動かない**(文面凍結宣言 §1 条5)。"""
    from shibuya.perception.attention import strip_imperatives

    resp = write_responses(tmp_path / "r.jsonl", duplicate_reps(GOOD))
    for v in W14.ingest(world_dir, resp).frozen:
        assert strip_imperatives(v.text).kept == v.text


# ---------------------------------------------------------------- 段階本体
def test_run_without_responses_writes_prompts_only(world_dir: Path):
    ctx = C.Ctx(data=world_dir, out=world_dir)
    res = W14.run(ctx)
    assert passed_except(res, {"poi_rows"})
    assert [o["path"] for o in res.outputs] == ["w14_prompts.jsonl"]
    assert not (world_dir / "w14_signage.parquet").exists()
    assert res.catalog_classes == []


def test_run_with_responses_freezes_and_records_hashes(world_dir: Path):
    write_responses(world_dir / "w14_responses.jsonl", duplicate_reps(GOOD))
    ctx = C.Ctx(data=world_dir, out=world_dir)
    res = W14.run(ctx)
    paths = [o["path"] for o in res.outputs]
    assert paths == ["w14_prompts.jsonl", "w14_signage.parquet", "w14_gates.json"]
    assert passed_except(res, {"poi_rows"}), {g.name: g.to_json() for g in res.gates}
    assert res.catalog_classes == ["看板・広告文言"]
    gates = {g.name: g.value for g in res.gates}
    assert gates["frozen_rep_byte_match_rate"] == 1.0
    assert gates["rep_byte_match_rate_all"] == 1.0
    assert gates["rep_mismatch_count"] == 0
    assert gates["n_frozen"] == 4
    # 応答は**入力資産**=input_hash に含まれる(応答を差し替えたら段階の版が動く)
    before = res.input_hash
    write_responses(
        world_dir / "w14_responses.jsonl",
        duplicate_reps({**GOOD, "p_b": "ベーカリー宮下は飲食店。毎日7時から19時。"}),
    )
    assert W14.run(ctx).input_hash != before


def test_run_is_reproducible(world_dir: Path):
    write_responses(world_dir / "w14_responses.jsonl", duplicate_reps(GOOD))
    ctx = C.Ctx(data=world_dir, out=world_dir)
    a = W14.run(ctx)
    b = W14.run(ctx)
    assert a.to_json() == b.to_json()


# ---------------------------------------------------------------- hypothesis
_VOCAB = ["飲食店", "物販店", "営業", "価格帯は中程度", "月曜から金曜", "10時から22時", "表示"]


@settings(max_examples=200, deadline=None)
@given(st.lists(st.sampled_from(_VOCAB), min_size=1, max_size=8))
def test_property_text_covered_by_input_never_violates(words: list[str]):
    """**不変条件**: 生成文が入力文字列に丸ごと含まれるなら固有名詞違反は出ない。

    (検査器は「入力由来の語」を決して落とさない=偽陽性で世界を壊さない側の保証)
    """
    text = "、".join(words) + "。"
    assert L.scan_proper_nouns(text, allowed=text, kanji_strict=True) == []


@settings(max_examples=100, deadline=None)
@given(st.text(alphabet="アイウエオカキクケコサシスセソ", min_size=3, max_size=8))
def test_property_unknown_katakana_is_always_caught(word: str):
    """**不変条件**: 入力にも一般語表にも無いカタカナ語は必ず捕まる(検出漏れなし)。

    一般語(「アイス」等)を部分に含む語は分解して通す仕様なので前提から除く
    (= 検査器の唯一の逃げ道が一般語表であることの裏返し)。
    """
    assume(not any(g in word for g in L.GENERIC_KATAKANA))
    allowed = "業種: 物販店\n価格帯: 中程度"
    v = L.scan_proper_nouns(f"物販店。{word}を扱う。", allowed=allowed)
    assert any(x.rule == "N2_katakana" for x in v), (word, v)


# ---------------------------------------------------------------- 実データ
@pytest.mark.skipif(
    not (DATA_DIR / "w7_plan_spec.parquet").exists(), reason="data/world/v2 が無い"
)
def test_real_data_prompt_count_and_sha(capsys):
    """実資産で 2,337 件・プロンプト SHA・平均トークンを出す(§1 W14 の呼数)。"""
    from shibuya.perception.channels import estimate_tokens

    prompts = W14.build_prompts(DATA_DIR)
    assert len(prompts) == W14.EXPECTED_POI_ROWS
    assert len({p.id for p in prompts}) == len(prompts)
    toks = [estimate_tokens(p.system) + estimate_tokens(p.user) for p in prompts]
    with capsys.disabled():
        print(
            f"\n[W14] prompts={len(prompts)} sha={L.prompts_sha256(prompts)[:16]} "
            f"system_sha={C.sha256_bytes(W14.SYSTEM_PROMPT.encode('utf-8'))[:16]} "
            f"in_tok mean={sum(toks) / len(toks):.1f} max={max(toks)} "
            f"calls={len(prompts) * L.REPEAT}"
        )
