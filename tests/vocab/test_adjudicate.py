"""``tools/vocab/adjudicate.py``(段2 起草 + 段3 静的検査)の検査。

正典: 語彙成長の設計 v0(docs/design/v2-vocab-growth-design.md)§2〜§3 とユーザー決定
2026-09-17(A (b)+(c) 全件保持+被覆順位+件数予算 10 / B 検証可能な必須欄 / C 4 検査 /
I 人手+距離列 / K 裁定モデル・温度・エンドポイント数を記録)。

**LLM は呼ばない**(mock と stub だけ)。
"""

from __future__ import annotations

import json

import pytest

from shibuya.cli import undefined_registry_payload
from shibuya.llm import UndefinedActionRegistry
from shibuya.llm.undefined import SYNONYMS


# ---------------------------------------------------------------- 素材


def _payload(spec, *, source="test"):
    """``{語: [(agent_id, tick, cell), …]}`` → 未定義台帳 JSON(本番と同じ builder)。"""
    reg = UndefinedActionRegistry(adjudicator=None)
    cells: dict[tuple[int, int], str] = {}
    for word, rows in spec.items():
        for agent_id, tick, cell in rows:
            out = reg.observe(word, agent_id, tick, "")
            assert out.stage == 1, f"{word} は段0 辞書で写ってしまう(素材として使えない)"
            if cell is not None:
                cells[(agent_id, tick)] = cell
    return undefined_registry_payload(reg, source=source, cells=cells)


def _rows(n_agents, *, cells=1, hours=1, base=0):
    """``n_agents`` 体 × ``cells`` セル × ``hours`` 時間帯の観測を作る。"""
    out = []
    for i in range(n_agents):
        out.append((base + i, (i % hours) * 60 + 1, f"c{base}_{i % cells}"))
    return out


_GOOD = {
    "target_class": "飲食店",
    "affordance": "eat_meal",
    "preconditions": ["同一セルに飲食店がある"],
    "effects": ["satiety+"],
    "cost": {"time_min": 20, "money_yen": 800},
    "failure_codes": ["NOT_IN_EATERY"],
    "conservation_accounts": ["CONSUMPTION"],
    "pattern_ledger_row": "外食の時間帯分布と照合する",
    "rationale": "対象クラスが提供する操作として書いた。",
}


class _Stub:
    """語ごとに決めた JSON を返す stub(欠落・キーワード混入を作るため)。"""

    name = "stub"
    model = "stub-model"
    temperature = 0.0
    n_endpoints = 0

    def __init__(self, by_word=None, default=None):
        self.by_word = dict(by_word or {})
        self.default = default if default is not None else dict(_GOOD)
        self.prompts: list[str] = []

    def draft(self, prompt, *, word):
        self.prompts.append(prompt)
        body = dict(self.by_word.get(word, self.default))
        body.setdefault("word", word)
        return "```json\n" + json.dumps(body, ensure_ascii=False) + "\n```"


# ---------------------------------------------------------------- (i) 順位=被覆


def test_rank_is_the_coverage_of_agents_cells_hours(adjudicate):
    """順位は 体数×セル数×時間帯数(件数=行数ではない)。決定 A (c)。"""
    payload = _payload(
        {
            # 行数は同じ 24 でも被覆が違う → 被覆の大きい方が上位
            "ほげ": _rows(24, cells=6, hours=4, base=0),
            "ふが": _rows(24, cells=1, hours=1, base=100),
            "ぴよ": _rows(24, cells=2, hours=12, base=200),
        }
    )
    res = adjudicate.run_batch([payload], client=_Stub())
    words = [r["word"] for r in res["words"]]
    covs = [r["coverage"] for r in res["words"]]
    assert covs == sorted(covs, reverse=True)
    assert [r["rank"] for r in res["words"]] == [1, 2, 3]
    assert words[0] == "ぴよ" and words[-1] == "ふが"
    top = res["words"][0]
    assert top["coverage"] == top["distinct_agents"] * top["distinct_cells"] * top["distinct_hours"]
    assert top["n_rows"] == 24  # 行数では 3 語とも同じ


# ---------------------------------------------------------------- (ii) 下限未満は保持のみ


def test_below_threshold_is_held_not_dropped(adjudicate):
    """N=10 体未満は起草せず**保持する**(全件保持・決定 A (b))。"""
    payload = _payload({"ほげ": _rows(12, cells=3), "ふが": _rows(9, cells=9, hours=9, base=100)})
    stub = _Stub()
    res = adjudicate.run_batch([payload], client=stub)
    by_word = {r["word"]: r for r in res["words"]}
    assert set(by_word) == {"ほげ", "ふが"}  # 捨てない
    assert by_word["ふが"]["verdict"] == adjudicate.Verdict.HELD_BELOW_THRESHOLD
    assert by_word["ふが"]["draft"] is None
    assert by_word["ふが"]["rank"] == 1  # 被覆は最大でも、体数の下限で保持のみ
    assert by_word["ほげ"]["verdict"] == adjudicate.Verdict.NEEDS_DYNAMIC
    assert stub.prompts and all("ふが" not in p for p in stub.prompts)


def test_batch_budget_holds_the_rest(adjudicate):
    """件数予算(既定 10)を超えた語は ``HELD_BUDGET``(保持のみ)。"""
    payload = _payload(
        {"ほげ": _rows(12, cells=4, base=0), "ふが": _rows(12, cells=2, base=100)}
    )
    res = adjudicate.run_batch([payload], client=_Stub(), budget=1)
    verdicts = [r["verdict"] for r in res["words"]]
    assert verdicts[0] == adjudicate.Verdict.NEEDS_DYNAMIC
    assert verdicts[1] == adjudicate.Verdict.HELD_BUDGET
    assert res["summary"]["n_drafted"] == 1


# ---------------------------------------------------------------- (iii) 必須欄の欠落


def test_missing_required_field_is_rejected(adjudicate):
    """必須欄(決定 B (b))が欠けたら不採用。理由に欄名が出る。"""
    broken = {k: v for k, v in _GOOD.items() if k != "effects"}
    res = adjudicate.run_batch(
        [_payload({"ほげ": _rows(12, cells=3)})], client=_Stub({"ほげ": broken})
    )
    row = res["words"][0]
    assert row["verdict"] == adjudicate.Verdict.REJECTED
    assert "MISSING_FIELD:effects" in row["reasons"]
    assert row["checks"]["s1_fields"]["missing"] == ["effects"]


def test_bad_affordance_and_bad_account_and_bad_code_are_rejected(adjudicate):
    """(s1) affordance は snake_case /(s2) 失敗コードは大文字 SNAKE /(s3) 科目は科目表に実在。"""
    bad = dict(_GOOD)
    bad.update(
        affordance="EatMeal",
        failure_codes=["not_in_eatery"],
        conservation_accounts=["SALES"],
    )
    res = adjudicate.run_batch(
        [_payload({"ほげ": _rows(12, cells=3)})], client=_Stub({"ほげ": bad})
    )
    row = res["words"][0]
    assert row["verdict"] == adjudicate.Verdict.REJECTED
    assert "BAD_TYPE:affordance(snake_case)" in row["reasons"]
    assert "BAD_FAILURE_CODE:not_in_eatery" in row["reasons"]
    assert "UNKNOWN_ACCOUNT:SALES" in row["reasons"]
    assert row["checks"]["s3_accounts"]["table"] == "economy/accounts.py AccountCode"


def test_existing_failure_code_is_reuse_not_collision(adjudicate):
    """既存 ``ResultCode`` の名前は**再利用**(不採用にしない)。別名前空間の名前は衝突。"""
    ok = dict(_GOOD, failure_codes=["MONEY_SHORT", "ZZ_BRAND_NEW_CODE"])
    collide = dict(_GOOD, failure_codes=["RENT"])  # AccountCode の名前
    res = adjudicate.run_batch(
        [_payload({"ほげ": _rows(12, cells=3), "ふが": _rows(12, cells=3, base=100)})],
        client=_Stub({"ほげ": ok, "ふが": collide}),
    )
    by_word = {r["word"]: r for r in res["words"]}
    assert by_word["ほげ"]["verdict"] == adjudicate.Verdict.NEEDS_DYNAMIC
    assert by_word["ほげ"]["checks"]["s2_failure_codes"]["reused_existing"] == ["MONEY_SHORT"]
    assert by_word["ほげ"]["checks"]["s2_failure_codes"]["new"] == ["ZZ_BRAND_NEW_CODE"]
    assert by_word["ふが"]["verdict"] == adjudicate.Verdict.REJECTED
    assert "CODE_NAMESPACE_COLLISION:RENT(AccountCode)" in by_word["ふが"]["reasons"]


# ---------------------------------------------------------------- (iv) 段3 のキーワード


def test_review_keyword_is_auto_rejected(adjudicate):
    """保存則・性能予算に触れる語(§7 段3)は自動不採用。"""
    hot = dict(_GOOD, rationale="所持金が減るので在庫と突き合わせる。")
    res = adjudicate.run_batch(
        [_payload({"ほげ": _rows(12, cells=3)})], client=_Stub({"ほげ": hot})
    )
    row = res["words"][0]
    assert row["verdict"] == adjudicate.Verdict.REJECTED
    assert "REVIEW_KEYWORD:所持金" in row["reasons"]
    assert "REVIEW_KEYWORD:在庫" in row["reasons"]
    assert row["checks"]["s4_review_keywords"]["hits"] == ["在庫", "所持金"]


# ---------------------------------------------------------------- (v) 重複判定


def test_near_existing_surface_is_judged_dictionary_row(adjudicate):
    """既存表層に近い語(距離 ≥ 0.75)は「辞書行の追加で済む」= 新語ではない(s5)。"""
    res = adjudicate.run_batch(
        [_payload({"買物": _rows(12, cells=3)})], client=_Stub()
    )
    row = res["words"][0]
    assert row["nearest_existing"]["surface"] == "買い物"
    assert row["nearest_existing"]["canonical"] == "購入"
    assert row["nearest_existing"]["ratio"] >= adjudicate.DUPLICATE_RATIO
    assert row["checks"]["s5_duplicate"]["duplicate"] is True
    assert row["verdict"] == adjudicate.Verdict.DICTIONARY_ROW_SUFFICES


def test_far_word_is_not_a_duplicate_and_keeps_the_column(adjudicate):
    """距離が遠い語は重複でない。文字が 1 つも一致しない語は最近傍を**空**にする。"""
    res = adjudicate.run_batch(
        [_payload({"ほげ": _rows(12, cells=3), "ふが": _rows(12, cells=3, base=100)})],
        client=_Stub(),
    )
    by_word = {r["word"]: r for r in res["words"]}
    assert by_word["ほげ"]["checks"]["s5_duplicate"]["duplicate"] is False
    assert 0.0 < by_word["ほげ"]["nearest_existing"]["ratio"] < adjudicate.DUPLICATE_RATIO
    row = by_word["ふが"]
    assert row["checks"]["s5_duplicate"]["duplicate"] is False
    assert row["nearest_existing"]["surface"] == ""  # 辞書順の先頭を最近傍と書かない
    assert row["nearest_existing"]["ratio"] == 0.0
    assert row["stage0_target"] is None  # 台帳の語=段0 で写らなかった語
    assert row["policy_class"] == "未定義"


# ---------------------------------------------------------------- (vi) 出力


def test_main_writes_json_and_md_without_absolute_paths(adjudicate, tmp_path, capsys):
    """``drafts.json`` と ``report.md`` が出て、**絶対パスを含まない**。"""
    src = tmp_path / "reg.json"
    src.write_text(
        json.dumps(_payload({"ほげ": _rows(12, cells=3), "ふが": _rows(4, base=100)}),
                   ensure_ascii=False),
        encoding="utf-8",
    )
    out = tmp_path / "batch"
    assert adjudicate.main([str(src), "--out", str(out)]) == 0
    capsys.readouterr()

    doc = json.loads((out / "drafts.json").read_text(encoding="utf-8"))
    md = (out / "report.md").read_text(encoding="utf-8")
    assert doc["schema"] == "shibuya.vocab/drafts/1"
    assert doc["inputs"] == ["reg.json"]  # リポ外の入力は名前だけ
    assert {r["word"] for r in doc["words"]} == {"ほげ", "ふが"}
    assert "段2 起草" in md and "指紋" in md

    for text in (json.dumps(doc, ensure_ascii=False), md):
        assert str(tmp_path) not in text
        assert str(tmp_path.as_posix()) not in text
        assert ":\\" not in text and ":/" not in text.replace("http://", "").replace("https://", "")


def test_fingerprints_are_six_and_record_the_model(adjudicate):
    """決定 G: 指紋 6 つ/決定 K: 裁定モデル名・温度・エンドポイント数を記録。"""
    res = adjudicate.run_batch([_payload({"ほげ": _rows(12)})], client=_Stub())
    fp = res["fingerprints"]
    assert len(fp) == 6
    assert set(fp) == {
        "1_thresholds", "2_field_order", "3_adjudicator",
        "4_pass_lines", "5_adoption_order", "6_version_policy",
    }
    assert fp["2_field_order"] == list(adjudicate.REQUIRED_FIELDS)
    assert fp["3_adjudicator"]["model"] == "stub-model"
    assert fp["3_adjudicator"]["temperature"] == 0.0
    assert fp["3_adjudicator"]["n_endpoints"] == 0
    assert len(fp["3_adjudicator"]["prompt_sha256"]) == 64
    assert fp["5_adoption_order"][0] == "食事"  # 語彙政策 v0 §4-2


def test_mock_adjudicator_is_deterministic_and_empty_by_design(adjudicate):
    """mock は**決定論の定型**(意味を作らない)。2 回呼んでバイト一致。"""
    m = adjudicate.MockAdjudicator()
    a = m.draft("p", word="食事")
    b = m.draft("p", word="食事")
    assert a == b
    body = json.loads(a)
    assert set(adjudicate.REQUIRED_FIELDS) <= set(body)
    assert body["placeholder"] is True
    assert body["failure_codes"] == [] and body["conservation_accounts"] == []


def test_prompt_is_the_frozen_template_plus_json_spec(adjudicate):
    """起草プロンプトは ``ADJUDICATION_TEMPLATE`` の前半を再利用した固定文。"""
    from shibuya.llm.undefined import ADJUDICATION_TEMPLATE

    head = ADJUDICATION_TEMPLATE.split("出力は次の5行に限ります")[0]
    assert adjudicate.DRAFT_PROMPT_TEMPLATE.startswith(head)
    row = {"word": "食事", "n_rows": 678, "distinct_agents": 634,
           "distinct_cells": 197, "distinct_hours": 22}
    prompt = adjudicate.build_prompt(row)
    assert "行動語: 食事" in prompt and "異なる個体 634 体" in prompt
    assert "異なるセル 197" in prompt and "JSON" in prompt
    assert "CONSUMPTION" in prompt and "MONEY_SHORT" in prompt
    assert "{" in prompt and "{word}" not in prompt  # 置換し残しが無い


# ---------------------------------------------------------------- 語彙政策 v0 の写し


def test_policy_json_is_a_faithful_copy_of_the_dictionary(adjudicate):
    """``synonym_policy_v0.json`` は段0 辞書の写し(本文 §2・§3 と一致)。

    辞書の版が上がったときは**写しの更新が要る**(語彙政策 v0 §4-1 の 3 点セット)。
    その場合は「写しと現行辞書の差」を skip の理由に出す(黙って通さない・黙って赤にもしない)。
    """
    from shibuya.llm.undefined import SYNONYM_TABLE_VERSION

    policy = adjudicate.load_policy()
    rows = policy["rows"]
    for surface, row in rows.items():  # 版によらず、残っている行の写像先は一致していること
        if surface in SYNONYMS:
            assert row["canonical"] == SYNONYMS[surface]
    if policy["synonym_table_version"] != SYNONYM_TABLE_VERSION:
        pytest.skip(
            f"辞書版が {SYNONYM_TABLE_VERSION} に上がった(写しは "
            f"{policy['synonym_table_version']})。追加={sorted(set(SYNONYMS) - set(rows))} / "
            f"削除={sorted(set(rows) - set(SYNONYMS))} → "
            "docs/design/v2-synonym-policy-v0.md §2 と tools/vocab/synonym_policy_v0.json の更新が要る"
        )
    assert set(rows) == set(SYNONYMS)
    assert len(rows) == 100
    assert policy["tally"] == {"なし": 61, "軽微": 8, "対象の損失": 17, "意味の損失": 14}
    assert rows["食べる"]["class"] == "意味の損失" and rows["食べる"]["star"] is True
    assert rows["帰宅"]["class"] == "対象の損失"
    assert rows["観察"]["class"] == "意味の損失" and rows["観察"]["policy"] is True


# ---------------------------------------------------------------- 合算


def test_two_runs_are_merged_by_sum_of_rows_and_union_of_coverage(adjudicate):
    """seed 1/2 の合算: 行数は和・体は (由来, id) の併合・セル/時間帯は併合。"""
    a = _payload({"ほげ": _rows(12, cells=3, base=0)}, source="a")
    b = _payload({"ほげ": _rows(12, cells=3, base=0)}, source="b")  # 同じ id の 12 体
    res = adjudicate.run_batch([a, b], client=_Stub())
    row = res["words"][0]
    assert row["n_rows"] == 24
    assert row["distinct_agents"] == 24  # 由来が違えば別の体
    assert row["distinct_cells"] == 3  # セルは同じ世界=併合して 3
    assert set(row["per_source"]) == {"a#0", "b#1"}
    assert row["per_source"]["a#0"]["n_rows"] == 12


@pytest.mark.parametrize("bad", ["{}", '{"schema": "other/1"}'])
def test_load_registry_rejects_a_foreign_json(adjudicate, tmp_path, bad):
    p = tmp_path / "x.json"
    p.write_text(bad, encoding="utf-8")
    with pytest.raises(ValueError, match="未定義台帳"):
        adjudicate.load_registry(p)
