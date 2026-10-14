"""第 3 期 3-3 申込書 ``ExperimentForm``(決定 10-12 §4-5 CP5-4・探索と確認・CP14)。

- 知らない欄は ``ValueError``(一番上・入れ子・決定の欄・事前登録)。
- ``to_json``/``from_json`` の往復(決定的な並び・同じ指紋)。日本語の種類(探索/確認)を受ける。
- 欄の矛盾(終わり ≤ 始まり・L0 の対象・水準の違う決定・告知の時刻・事前登録の有無と指紋)は ``ValueError``。
- 決定の表: 本段の実装は L0(天気の日付・祝日)と L1(営業時間・休業・催し)だけ・L2〜L4 は欄だけ。
- ``engine/experiment/`` のコードに地名と業種名が無い(日本語の固有名詞の一覧は試験の側に置く・負の対照つき)。
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from shibuya.engine.experiment import form as F
from shibuya.engine.experiment.form import DECISIONS, ExperimentForm

from tests.engine.experiment._x33 import NS_DAY, NS_HOUR, form, form_dict

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya"
EXP_DIR = SRC / "engine" / "experiment"


# ================================================================= 欄
def test_fields_and_defaults():
    f = form()
    d = f.to_dict()
    assert tuple(d) == F.FORM_FIELDS
    assert d["kind"] == "explore" and d["subject"] == {"level": "L1", "ids": [0], "category": None}
    assert d["content"] == [{"decision": "closure"}] and d["end"] is None and d["notice"] is None
    assert d["ensemble"] == {"initial": 1, "model": ["mock"], "chance": 1, "aa": True, "seed0": 1}
    assert d["preregistration"] is None and d["aa_of"] is None and f.level == "L1" and not f.is_aa


@pytest.mark.parametrize("where,bad", [
    ("top", {"unknown_field": 1}),
    ("subject", {"subject": {"level": "L1", "ids": [0], "place": "x"}}),
    ("notice", {"notice": {"to": [1], "via": "メッセージ", "when": 0}}),
    ("metrics", {"metrics": {"primary": {"id": "a", "path": "b"}, "tertiary": []}}),
    ("metric", {"metrics": {"primary": {"id": "a", "path": "b", "unit": "人"}}}),
    ("ensemble", {"ensemble": {"initial": 1, "runs": 3}}),
    ("decision", {"content": [{"decision": "closure", "hours": [[0, 60]]}]}),
    ("preregistration", {"kind": "confirm", "preregistration": {"seal_sha256": "0" * 64,
                                                                 "registration_sha256": "0" * 64, "note": "x"}}),
])
def test_unknown_fields_are_errors(where, bad):
    with pytest.raises(ValueError, match="知らない欄"):
        ExperimentForm.from_dict(form_dict(**bad))


def test_json_round_trip_is_deterministic():
    f = form(notice={"to": ["staff", 3], "via": "メッセージ"}, end=2 * NS_DAY,
             content=[{"decision": "opening_hours", "hours": [[600, 1500]]}, {"decision": "event"}])
    text = f.to_json()
    g = ExperimentForm.from_json(text)
    assert g == f and g.to_json() == text and g.sha256() == f.sha256()
    assert json.loads(text) == f.to_dict()
    # 鍵の並びと区切りが決定的(入力の並びに依らない)
    shuffled = dict(reversed(list(json.loads(text).items())))
    assert ExperimentForm.from_dict(shuffled).to_json() == text
    # 入れ子も読み取り専用
    with pytest.raises(TypeError):
        f.subject["level"] = "L0"  # type: ignore[index]


def test_japanese_kind_aliases():
    assert form(kind="探索").kind == "explore"
    with pytest.raises(ValueError, match="kind"):
        form(kind="調査")


@pytest.mark.parametrize("over,msg", [
    (dict(end=NS_DAY), "end は start より後"),
    (dict(subject={"level": "L0", "ids": [1]}, content=[]), "L0"),
    (dict(content=[{"decision": "weather_date", "replay_date": "2026-07-14"}]), "L0"),
    (dict(content=[{"decision": "teleport"}]), "decision"),
    (dict(content=[{"decision": "opening_hours"}]), "必須"),
    (dict(content=[{"decision": "opening_hours", "hours": [[900, 600]]}]), "開く"),
    (dict(notice={"to": [1], "at": NS_DAY, "via": "メッセージ"}), "notice.at"),
    (dict(notice={"to": [1], "via": "無し"}), "notice.via"),
    (dict(notice={"to": [], "via": "メッセージ"}), "notice.to"),
    (dict(question=""), "question"),
    (dict(metrics={"secondary": []}), "primary"),
    (dict(start=-1), "start"),
])
def test_contradictions_are_errors(over, msg):
    with pytest.raises(ValueError, match=msg):
        form(**over)


def test_preregistration_only_for_confirm_and_must_match():
    pre = {"seal_sha256": "a" * 64, "registration_sha256": "b" * 64}
    with pytest.raises(ValueError, match="確認のランだけ"):
        form(preregistration=pre)
    with pytest.raises(ValueError, match="事前登録"):
        form(kind="confirm")
    with pytest.raises(ValueError, match="合わない"):
        form(kind="confirm", preregistration=pre)
    reg = ExperimentForm.from_dict({**form_dict(), "kind": "explore"}).to_dict()
    reg["kind"] = "confirm"
    reg.pop("preregistration")
    ok = form(kind="確認", preregistration={"seal_sha256": "a" * 64, "registration_sha256": F.sha256_hex(reg)})
    assert ok.kind == "confirm" and ok.registration_digest() == F.sha256_hex(reg)


def test_aa_and_start_step():
    f = form(notice={"to": [1], "via": "メッセージ"})
    a = f.aa()
    assert a.is_aa and a.notice is None and a.content == () and a.start == f.start and a.sha256() != f.sha256()
    assert form(start=NS_DAY + 12 * NS_HOUR).start_step(60) == 1440 + 720
    assert form(start=NS_DAY + 1).start_step(60) == 1441  # T0 以後の最初の刻み(切り上げ)


def test_decision_table_levels_and_implementation():
    impl = {k for k, v in DECISIONS.items() if v.implemented}
    assert impl == {"weather_date", "holiday", "opening_hours", "closure", "event"}
    assert {DECISIONS[k].level for k in impl} == {"L0", "L1"}
    assert {v.level for k, v in DECISIONS.items() if not v.implemented} == {"L2", "L3", "L4"}
    # 宣言だけの種類も欄の検査は同じ(知らない欄はエラー)
    with pytest.raises(ValueError, match="知らない欄"):
        form(subject={"level": "L4", "ids": []}, content=[{"decision": "fare", "amount_yen": 10, "line": "x"}])


# ================================================================= 地名と業種名をコードに書かない
#: 日本語の固有名詞(地名・施設名・店の名)と業種名の一覧(試験の側に置く・コードの側には書かない)。
PLACE_NAMES = (
    "渋谷", "道玄坂", "宮益坂", "宇田川", "神南", "神宮前", "原宿", "表参道", "恵比寿", "代官山", "桜丘", "円山町",
    "松濤", "南平台", "鶯谷", "新宿", "池袋", "東京", "青山", "代々木", "明治通り", "公園通り", "センター街", "井の頭",
    "ハチ公", "スクランブル", "ヒカリエ", "パルコ", "西武", "東急", "京王", "小田急", "マークシティ", "宮下",
)
BUSINESS_NAMES = (
    "コンビニ", "カフェ", "喫茶", "居酒屋", "ラーメン", "牛丼", "寿司", "焼肉", "飲食店", "レストラン", "ファストフード",
    "百貨店", "書店", "本屋", "美容室", "理容", "薬局", "ドラッグストア", "銀行", "映画館", "カラオケ", "パチンコ",
    "スーパー", "ホテル", "病院", "松屋", "吉野家", "すき家", "マクドナルド", "スターバックス", "セブン", "ローソン",
    "ファミリーマート",
)


def names_in(text: str) -> list[str]:
    return sorted({w for w in PLACE_NAMES + BUSINESS_NAMES if w in text})


def test_no_place_or_business_names_in_the_experiment_code():
    files = sorted(EXP_DIR.glob("*.py"))
    assert {p.name for p in files} >= {"form.py", "apply.py", "layer.py", "branch.py", "ensemble.py", "gate.py"}
    found = {p.name: names_in(p.read_text(encoding="utf-8")) for p in files}
    assert {k: v for k, v in found.items() if v} == {}
    # 文字列の値(AST)にも無い
    for p in files:
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                assert not names_in(n.value), (p.name, n.value)


def test_name_check_catches_a_planted_name():
    """負の対照: 地名と業種名を書いた行は見つかる。"""
    assert names_in('TARGET = "道玄坂のカフェ"') == ["カフェ", "道玄坂"]
    assert names_in("対象は申込書の値で受ける") == []


# ================================================================= 検収 L3・L4
def test_direct_construction_is_checked_too():
    """〔検収 L3〕``ExperimentForm(...)`` を直に作っても ``__post_init__`` が同じ検査を通す。"""
    import dataclasses

    f = form()
    for bad in (dict(kind="nonsense"), dict(start=-5), dict(question=""), dict(end=0)):
        with pytest.raises(ValueError):
            dataclasses.replace(f, **bad)
    with pytest.raises(ValueError, match="知らない欄"):
        dataclasses.replace(f, content=({"decision": "closure", "x": None},))
    with pytest.raises(ValueError, match="正準"):  # 並びの崩れた番号(from_dict なら昇順にする)
        dataclasses.replace(f, subject={"level": "L1", "ids": [2, 1], "category": None})


def test_aa_of_a_confirm_form_round_trips():
    """〔検収 L4〕確認の申込書の A/A の枝は事前登録を引き継ぎ、元の登録の指紋を aa_of に残す=JSON の往復で通る。"""
    from shibuya.engine.experiment import ensemble as EN

    ens = {"initial": 2, "model": ["mock"], "chance": 1}
    _rec, cf = EN.preregister(form_dict(ensemble=ens), EN.seal(form(ensemble=ens)))
    a = cf.aa()
    assert a.kind == "confirm" and a.is_aa and a.aa_of == cf.registration_digest() == a.preregistration["registration_sha256"]
    assert ExperimentForm.from_json(a.to_json()) == a and a.aa() is a
    with pytest.raises(ValueError, match="aa_of"):  # 改変のある申込書に aa_of は置けない
        ExperimentForm.from_dict({**cf.to_dict(), "aa_of": cf.registration_digest()})
    with pytest.raises(ValueError, match="aa_of"):  # 確認の A/A の印が事前登録と違う
        ExperimentForm.from_dict({**a.to_dict(), "aa_of": "0" * 64})
    e = form().aa()
    assert e.aa_of == form().registration_digest() and ExperimentForm.from_json(e.to_json()) == e
