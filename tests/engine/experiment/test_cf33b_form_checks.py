"""第 3 期 3-3b 申込書の点検(``engine.experiment.checks``)と省略できる欄(CP5-1・CP5-3・仮-24)。

- 省略できる欄 ``unexpected``・``known_to_model``: 既定のときは正準の形に書かない=3-3 の申込書の指紋は変わらない・書けば指紋に入る・
  型の誤りと知らない欄は ``ValueError``。
- CP5-1: 始まり 0 で改変があり告知が無い(または ``unexpected=true``)申込書は警告と記録(拒まない=ランは回る)。始まりが 0 でない・
  告知のある予期した改変・A/A は警告しない。「最初から」の順番は宣言だけ(``order_implemented=False``)。
- CP5-3: 名指しの機械の検査(``naming_hits``=1 つの道具)で、ペルソナの文の名指しと自己申告の語(混入の疑い)を探す(植えた名は
  見つかる・無い名は見つからない=負の対照)。
"""

from __future__ import annotations

import warnings

import pytest

from shibuya import cli
from shibuya.engine.experiment import checks as CK
from shibuya.engine.experiment import form as F
from shibuya.engine.experiment.form import ExperimentForm, canonical_json

from tests.engine.experiment._x33 import BASE, NS_HOUR, form, form_dict


# ================================================================= 省略できる欄
def test_optional_fields_do_not_change_old_forms():
    f = form()
    d = f.to_dict()
    assert tuple(d) == F.FORM_FIELDS and "unexpected" not in f.to_json() and "known_to_model" not in f.to_json()
    # 3-3 の形(省略できる欄の無い辞書)の正準の JSON と同じ=指紋は変わらない
    assert f.to_json() == canonical_json({k: d[k] for k in F.FORM_FIELDS})
    assert f.unexpected is None and f.known_to_model == ()
    g = form(unexpected=True, known_to_model=["実在の改定", "実在の改定", "閉店の知らせ"])
    assert g.unexpected is True and g.known_to_model == ("実在の改定", "閉店の知らせ")  # 昇順・重なりは 1 つ
    assert g.sha256() != f.sha256() and g.registration_digest() != f.registration_digest()
    assert ExperimentForm.from_json(g.to_json()) == g
    assert form(unexpected=False).to_dict()["unexpected"] is False
    assert form(known_to_model=[]).to_json() == f.to_json() and form(unexpected=None).to_json() == f.to_json()


@pytest.mark.parametrize("over,msg", [
    (dict(unexpected="yes"), "unexpected"),
    (dict(known_to_model="閉店"), "known_to_model"),
    (dict(known_to_model=[""]), "known_to_model"),
    (dict(known_to_model=[3]), "known_to_model"),
    (dict(surprise=True), "知らない欄"),
])
def test_optional_field_errors(over, msg):
    with pytest.raises(ValueError, match=msg):
        ExperimentForm.from_dict(form_dict(**over))


def test_aa_keeps_the_declarations():
    g = form(unexpected=True, known_to_model=["閉店の知らせ"])
    a = g.aa()
    assert a.content == () and a.notice is None and a.unexpected is True and a.known_to_model == ("閉店の知らせ",)
    assert ExperimentForm.from_json(a.to_json()) == a


# ================================================================= CP5-1
def test_start0_check_flags_unexpected_changes_from_the_start():
    flag = CK.start0_check(form(start=0))  # 告知なし
    assert flag["warning"] is True and "告知が無い" in flag["reason"] and flag["order_implemented"] is False
    said = CK.start0_check(form(start=0, notice={"to": [1]}, unexpected=True))
    assert said["warning"] is True and "unexpected=true" in said["reason"]
    assert CK.start0_check(form(start=0, notice={"to": [1]}))["warning"] is False  # 告知のある予期した改変
    assert CK.start0_check(form(start=0, notice={"to": [1]}, unexpected=False))["warning"] is False
    assert CK.start0_check(form(start=NS_HOUR, unexpected=True))["warning"] is False  # 途中から=推奨の形
    assert CK.start0_check(form(start=0).aa())["warning"] is False  # A/A(改変が空)
    with pytest.warns(CK.ExperimentWarning, match="CP5-1"):
        CK.warn_start0(form(start=0))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        CK.warn_start0(form(start=NS_HOUR))  # 警告しない


def test_start0_warns_and_records_but_does_not_refuse():
    kw = dict(n_agents=40, seed=1, world_dir=None, n_cells=9, ticks=240, renderer="stub", vocab_version="v3")
    f = form(start=0)
    with pytest.warns(CK.ExperimentWarning):
        res = cli.run(**kw, experiment=f)
    m = res.run_manifest_fields()["experiment"]
    assert m["start0"]["warning"] is True and m["start0"]["rule"] == CK.START0_RULE
    assert m["start0"]["order"] == CK.START0_ORDER and m["applied"] + m["unapplied"] >= 1  # 回った(拒まない)


# ================================================================= CP5-3
def test_naming_hits_is_one_tool_for_persona_and_contamination():
    names = ["架空の通り", "架空の店"]
    assert CK.naming_hits("朝は架空の通りを歩く", names) == ["架空の通り"]
    assert CK.naming_hits("朝は公園を歩く", names) == []  # 負の対照
    p = CK.persona_naming({2: "架空の店で働く", 1: "家で過ごす"}, names)
    assert p["found"] and p["hits"] == [{"id": 2, "hits": ["架空の店"]}] and p["texts"] == 2
    assert not CK.persona_naming({1: "家で過ごす"}, names)["found"]
    g = form(known_to_model=["運賃の改定"])
    d = CK.contamination(g)
    assert d["declared"] == ["運賃の改定"] and d["checked"] is False and d["suspected"] is True
    c = CK.contamination(g, {1: "来月の運賃の改定が話題", 2: "雨"})
    assert c["checked"] and c["hits"] == [{"id": 1, "hits": ["運賃の改定"]}]
    e = CK.contamination(form(), {1: "来月の運賃の改定が話題"})
    assert e["declared"] == [] and e["hits"] == [] and e["suspected"] is False  # 自己申告が空=疑いの記録なし


def test_known_to_model_is_in_the_manifest():
    kw = dict(n_agents=40, seed=1, world_dir=None, n_cells=9, ticks=240, renderer="stub", vocab_version="v3")
    res = cli.run(**kw, experiment=form(start=NS_HOUR, known_to_model=["運賃の改定"]))
    m = res.run_manifest_fields()["experiment"]
    assert m["known_to_model"] == ["運賃の改定"] and m["start0"]["warning"] is False


def test_base_form_is_unchanged():
    """3-3 の雛形(BASE)に省略できる欄は無い。"""
    assert set(BASE) <= set(F.FORM_FIELDS) and set(F.OPTIONAL_FIELDS) == {"unexpected", "known_to_model"}
