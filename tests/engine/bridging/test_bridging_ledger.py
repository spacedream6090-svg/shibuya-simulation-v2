"""第 1 期 1-4 つなぎの台帳(CA8・計器の最初・計画 10-12 §1 の 3・口の約束 1-4)。

- 全行に ``remove_at``(計画の段の番号=閉じた表)・``declared_in``・``conf`` がある。
- コードの expedient の宣言(``engine.bridging.scan`` の 6 形=``conf="expedient"``・``expedients=[...]``・docstring の
  ``expedient:`` の段落・docstring の ``expedient(…)`` の見出し=見出し単位・世界過程と PlanSpec の ``mechanism=False``+
  ``repayment_due``・フォールバック台帳の行)と台帳の active の行が 1 対 1(AST と台帳の実行で数えて突き合わせる)。
  文書で宣言した行はコードの宣言が無くてよい。``removed`` の行は突き合わせの外(検収 L2)。
- 負の対照: 仮の expedient を足す(6 形とも)・台帳の行を消す・行を removed にすると突き合わせが落ちる・見出しの下の
  項の数が変わると落ちる。
- 最初の中身: 計画 §1 の 3 の 9 件・#88 の 6 件・西武の 1 部屋(=16 件)・不応期 11 種と起床条件のクラス(T3)・W16 の弱点。
- build の段の行の id は C8 の感度の台帳(D-44)の行の番号と同じ(``W<n>#<i>``)。
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import re
from pathlib import Path

import pytest

from shibuya.agents.state import REFRACTORY_MINUTES, WakeCondition
from shibuya.engine.bridging import ledger as L
from shibuya.engine.bridging import scan as S

ROOT = Path(__file__).resolve().parents[3]
C8 = (ROOT / "docs" / "bench" / "c8" / "sensitivity_v1.md").read_text(encoding="utf-8")

#: 計画 §1 の 3 の 9 件(既存のつなぎ)・#88 の 6 件・西武の 1 部屋(口の約束 1-4 の約束 (2)=16 件)。
PLAN9 = ("BR-W17-IO-SLEEP", "BR-E4-EXIT-VANISH", "BR-ATTENDANCE-LOTTERY", "BR-K9-MONDAY", "BR-SIGNAGE-FICTION",
         "BR-DELIVERY-INBOUND", "BR-THINK-TIME-TABLE", "BR-THINK-ALPHA", "BR-RENT-BLANK")
R88 = ("BR-W18-X", "BR-W12-HOLIDAY-GT-WEEKDAY", "BR-W11-SHINSEN-EXIT", "BR-SHADOW-NEAREST-DAY",
       "BR-WEATHER-STRATUM-WIDEN", "W9#5")
SEIBU = ("BR-SEIBU-ONE-ROOM",)
W16_WEAK = ("BR-W16-REPLICATED-108142", "BR-W16-VISITOR-COUNT-BASIS", "BR-W16-NO-TRANSFER-ONLY")


@pytest.fixture(scope="module")
def ledger() -> L.BridgeLedger:
    return L.default_ledger()


@pytest.fixture(scope="module")
def decls() -> list[S.Declaration]:
    return S.scan_package()


# ================================================================= 欄
def test_every_row_has_remove_at_declared_in_and_conf(ledger):
    assert ledger.count() == len(ledger.active()) >= 16
    assert ledger.count() + sum(1 for r in ledger if r.status == "removed") == len(ledger)
    for r in ledger:
        assert r.remove_at in L.PLAN_STAGES, r.id
        assert r.declared_in.startswith(("docs/", "src/")), r.id
        assert r.conf in L.CONFS and r.status in L.STATUSES and r.remove_basis in L.REMOVE_BASES, r.id
        assert r.what.strip() and r.why.strip(), r.id
        dt.date.fromisoformat(r.since)  # 検収 L3: 日付の形だけ見る(後で足す行の日は自由)
    assert len({r.id for r in ledger}) == len(ledger)


def test_rule_ids_point_to_the_rules_table(ledger):
    """検収 L7: 直書きの係数の行は規則の表の行に結ぶ(``rule_id`` は表にある id)。"""
    from shibuya.engine.rules import table as RT

    linked = [r for r in ledger if r.rule_id]
    assert [r.id for r in linked] == ["BR-MIN-WAGE-HOURLY-1226"]
    for r in linked:
        assert r.rule_id in RT.default_rules().ids() and r.remove_at == "4-2"
    src = (ROOT / "src" / "shibuya" / "economy" / "anchors.py").read_text(encoding="utf-8")
    assert "MIN_WAGE_HOURLY: Final[int] = 1_226" in src


def test_declared_places_exist(ledger):
    for r in ledger:
        assert (ROOT / r.declared_path).is_file(), (r.id, r.declared_path)
        for c in r.code_at:
            assert (ROOT / c).is_file(), (r.id, c)


def test_the_first_contents(ledger):
    ids = set(ledger.by_id)
    assert set(PLAN9 + R88 + SEIBU + W16_WEAK) <= ids
    assert len(PLAN9 + R88 + SEIBU) == 16
    # 〔第 4 期 4-3 段 10〕3 行とも 4-1 → 6-1(来街者・通学者・乗り換えは判断モデルの後=残る複製は通学者 16,695 と指令 24)
    # (前の値は 3 行とも 4-1・記録 pop43/README.md)
    assert {ledger.get(i).remove_at for i in W16_WEAK} == {"6-1"}
    assert {ledger.get(i).status for i in W16_WEAK} == {"active"}
    assert ledger.get("BR-K9-MONDAY").remove_at == "6-2"  # 〔第336・3-1〕1a は影なので外せない=6-2 へ(親)
    assert ledger.get("BR-W17-IO-SLEEP").remove_at == ledger.get("BR-E4-EXIT-VANISH").remove_at == "6-2"
    assert ledger.get("BR-W12-HOLIDAY-GT-WEEKDAY").remove_at == "2-3b"


def test_refractory_eleven_and_the_wake_class_are_removed_at_t3(ledger):
    """回答 10-13b §4-2 の 2: 不応期 11 種と起床条件のクラスは T3 で外す(各 1 行)。"""
    refr = [r for r in ledger if r.id.startswith("BR-REFRACTORY-")]
    names = [wc.name for wc in WakeCondition][: len(REFRACTORY_MINUTES)]
    assert sorted(r.id for r in refr) == sorted(f"BR-REFRACTORY-{n.replace('_', '-')}" for n in names)
    assert len(refr) == len(REFRACTORY_MINUTES) == 11
    for wc in list(WakeCondition)[:11]:
        r = ledger.get(f"BR-REFRACTORY-{wc.name.replace('_', '-')}")
        assert r.remove_at == "T3" and f"{REFRACTORY_MINUTES[int(wc)]} 分" in r.what and wc.name in r.what
        assert r.conf == ("mechanism" if wc.name in ("CONVERSATION_TURN", "PLAN_SLEEPING") else "expedient")
    assert ledger.get("BR-WAKE-CONDITION-CLASS").remove_at == "T3"


# ================================================================= コードの宣言と 1 対 1
def test_code_declarations_and_ledger_rows_are_one_to_one(ledger, decls):
    missing, orphan = L.code_mismatch(ledger, [d.declared_in for d in decls])
    assert missing == [], f"台帳に行の無い expedient の宣言: {missing}"
    assert orphan == [], f"コードに無い宣言を指す台帳の行: {orphan}"
    assert len({d.declared_in for d in decls}) == len(decls)
    assert len(ledger.code_keys()) == len(decls)


def test_the_counts_by_form(decls):
    """記録 r14/README.md の表と同じ数(形が増減したら記録も直す)。"""
    # 〔第 1 期 1-5〕見出し 74 → 76(engine/rights/initial.py・record.py)。〔第 1 期 1-8 J0〕候補の口の 3 つの見出し
    # (port・sources・layer=項 3+2+1)を足した=76 → 79(記録 j0/README.md)。〔第 1 期 1-7〕engine/tools/contacts.py の
    # 見出しを足した=79 → 80(記録 c0/README.md §4)
    # 〔第 2 期 2-3b〕W12 の等間隔の 5 行(W12#4〜#8=removed)を消し、実ダイヤの表 8 行と等間隔の道の表 1 行を足した
    # =expedients 139 → 143(記録 tt23b/README.md §13)
    # 〔第 1 期 1-8b〕engine/speech/port.py の docstring の段落 1(モーラ数)と見出し 2(port.py 項 3・layer.py 項 3)を
    # 足した=docstring 5 → 6・見出し 80 → 82(記録 s8b/README.md)
    # 〔第 2 期 2-2 段 11a〕engine/proximity.py の見出し(項 5)を足した=82 → 83(記録 prox22/README.md)
    # 〔第 2 期 2-3c〕W12 の発着の表の宣言の表 RAIL_EVENT_EXPEDIENTS(1 行=下りの直通の結び)を足した=expedients 143 → 144
    # (記録 tt23c/README.md)
    # 〔第 4 期 4-1 段 1〜3〕build/pop/w21_build.py の表 W21_EXPEDIENTS(27 行=検収の直しで 24 → 27)を足した
    # =expedients 143 → 170(記録 pop41/README.md)
    # 〔第336 取り込み〕本体(2-3c の 1 行=144)の後に W21 の 27 行を足した=144 → 171
    # 〔第 3 期 3-5〕本人の体の層の表 3 本(engine/body/rules.py の BODY_EXPEDIENTS 7・schedule.py の RESERVE_EXPEDIENTS 2・
    # system1.py の SYSTEM1_EXPEDIENTS 3)を足した=171 → 183(記録 bd35/README.md)
    # 〔第 3 期 3-1〕構築の段 W20cal(build/sched/w20_calendar_1a.py)の StageResult.expedients 9 つ(第337 で休みの曜日の
    # 選び方の 1 つを足した)と見出し 1 つ(項 8)を足した=本体の後に 183 → 192・見出し 83 → 84(記録 ca31/README.md)
    # 〔第 4 期 4-1 段 4〜7〕build/pop/w21_build_b.py の表 W21B_EXPEDIENTS(28 行)を足した=本体の後に 192 → 220
    # (記録 pop41b/README.md・見出しは足していない)
    # 〔第 4 期 4-1 段 8〜10〕build/pop/w21_build_c.py の表 W21C_EXPEDIENTS(16 行)を足した=220 → 236
    # (記録 pop41c/README.md・見出しは足していない)
    # 〔小さな版上げ・meal_w17〕engine/energy.py の表 MEAL_DEFAULT_EXPEDIENTS(4 行)を足した=236 → 240
    # (記録 meal_w17/README.md・見出しは足していない)
    # 〔第 4 期 4-3 段 10〕build/pop/w21_apply.py の表 W21APPLY_EXPEDIENTS(9 行=検収の直しで 7 → 9)・w21_build_b.py の 1.2.0 の
    # 1 行(地位の分け)を足し、w21_build_c.py の表を 16 → 14 行(置き場・W16 の在庫の案・地位の分けを消し、通う駅の口を足した)
    # =240 → 248(記録 pop43/README.md・見出しは足していない)
    assert S.count_by_form(decls) == {"conf": 0, "expedients": 248, "docstring": 6, "heading": 84, "process": 18,
                                      "fallback": 5}
    heads = [d for d in decls if d.form == S.FORM_HEADING]
    # 〔第 1 期 1-2〕p_notice の expedient の項 m_load(歩きスマホの負荷の係数)を消した=338 → 337(記録 p12/README.md §15)
    # 〔第 1 期 1-5〕engine/rights/initial.py(項 3)・record.py(項 2)の見出しを足した=71 → 73・337 → 342
    # 〔第 1 期 1-8 J0〕engine/decision/port.py(項 3)・sources.py(項 2)・layer.py(項 1)=73 → 76・342 → 348
    # 〔第 1 期 1-7〕engine/tools/contacts.py(項 3)の見出しを足した=76 → 77・348 → 351(記録 c0/README.md §4)
    # 〔第 1 期 1-8b〕engine/speech/port.py(項 3)・layer.py(項 3)=77 → 79・351 → 357(記録 s8b/README.md)
    # 〔第 2 期 2-2 段 11a〕engine/proximity.py(項 5)=79 → 80・357 → 362(記録 prox22/README.md)
    # 〔第 3 期 3-5〕environment.py の項 3(体感温度)と salient.py の項 1(倒れる率)を本人の体の層の表へ移した=362 → 358
    # 〔第 3 期 3-1〕build/sched/w20_calendar_1a.py(項 8)=80 → 81・358 → 366(本体の後に・記録 ca31/README.md)
    assert len({d.path for d in heads}) == 81 and sum(d.items for d in heads) == 366


def test_process_and_fallback_rows(ledger, decls):
    """第 5 形(世界過程 16+PlanSpec 2)と第 6 形(フォールバック台帳 5 行)=検収 M1。外す段は返済期限から。"""
    from shibuya.world.processes import first_batch as FB

    reg = FB.build_registry()
    by_key = {r.declared_in: r for r in ledger}
    procs = [d for d in decls if d.form == S.FORM_PROCESS]
    assert sorted(d.text for d in procs) == sorted(
        [p.id for p in reg.processes if not p.mechanism] + [s.id for s in reg.plan_specs if not s.mechanism])
    decl = {p.id: p for p in reg.processes} | {s.id: s for s in reg.plan_specs}
    for d in procs:
        r = by_key[d.declared_in]
        due = str(decl[d.text].repayment_due)
        assert r.id == f"PR-{d.text}" and due in r.what
        assert (r.remove_basis == "declared") == ("エージェント" in due) and (r.remove_at == "6-6" or "エージェント" not in due)
    fb = [d for d in decls if d.form == S.FORM_FALLBACK]
    rows = reg.fallback_ledger()
    assert sorted(d.text for d in fb) == sorted(f"{x.subject_id}|{x.plan_spec_id}" for x in rows) and len(rows) == 5
    for d in fb:
        assert by_key[d.declared_in].id == f"FB-{d.text.split('|')[0]}"


def test_literal_declarations_are_copied_verbatim(ledger, decls):
    """文字列の宣言は台帳の ``what`` にそのまま写す(f 文字列と式は構築したときの値=写しの外)。"""
    by_key = {r.declared_in: r for r in ledger}
    for d in decls:
        if d.form not in (S.FORM_CONF, S.FORM_EXPEDIENTS, S.FORM_DOCSTRING):
            continue
        literal = not (d.text.startswith(("f'", 'f"')) or " if " in d.text)
        if literal:
            assert by_key[d.declared_in].what == d.text, d.declared_in


def test_heading_rows_carry_the_heading_and_the_item_count(ledger, decls):
    """第 4 形: 見出し 1 つで 1 行(親の判断 第334)。``what`` に見出しの文と今の項の数・id はファイルと見出しの文の
    sha8(検収 L5=見出しを足しても後ろの id がずれない)。"""
    by_key = {r.declared_in: r for r in ledger}
    for d in (d for d in decls if d.form == S.FORM_HEADING):
        r = by_key[d.declared_in]
        rel = d.path.removeprefix("src/shibuya/")
        key = d.declared_in.rsplit(":", 1)[-1]
        assert r.id == f"HD-{rel.removesuffix('.py').replace('/', '.')}-{key}", (r.id, d.path)
        assert f"「{d.text}」" in r.what and f"項 {d.items} 個" in r.what, r.id
        assert r.conf == "expedient" and r.remove_basis == "inferred" and r.remove_at in L.PLAN_STAGES
    # 1-5: 74 → 76・〔第 1 期 1-8 J0〕+3・〔1-7〕+1・〔1-7 の 1-8 への結線〕layer.py の見出しを替えた=旧い行
    # HD-engine.decision.layer-2d3672ba は removed で残し、新しい見出しの行を足した(active は 80 のまま・行は 81)。
    # 〔第 1 期 1-8b〕engine/speech の見出し 2 行を足した=行 83・active 82・〔第 2 期 2-2〕+1=行 84・active 83
    # 〔第 3 期 3-1〕build/sched/w20_calendar_1a.py の見出し 1 行=行 85・active 84
    assert sum(1 for r in ledger if r.id.startswith("HD-")) == 85
    assert sum(1 for r in ledger if r.id.startswith("HD-") and r.status == "active") == 84
    assert {r.id: r.status for r in ledger}["HD-engine.decision.layer-2d3672ba"] == "removed"


def test_build_stage_ids_are_the_c8_d44_row_ids(ledger):
    """build の段の行の id(``W<n>#<i>``)は C8 の感度の台帳 D-44 の行と同じ項を指す(D-44 の切り詰めた文が頭に合う)。"""
    rows = {}
    for line in C8.splitlines():
        m = re.match(r"^\| (W\d+#\d+) \| W\d+ \| ([^|]+) \|", line)
        if m and m.group(1) not in rows:
            rows[m.group(1)] = m.group(2).strip()
    # 〔第 2 期 2-4・V1 の活性化〕C8 の台帳は活性化の後の build_manifest(126 行)。W12 1.2.0 の実ダイヤの宣言 8 行(C8 の
    # W12#4〜#11)は台帳では走査器の鍵の行(EX-build.field.w12_external_nodes-*)で、前の W12#4〜#8(等間隔の推定の 5 行=
    # 1.1.0 の build_manifest の番号)は removed。=有効な W の行は C8 の同じ番号の行と、C8 のほかの行は有効な EX の行と文で合う。
    stage = [r for r in ledger if re.fullmatch(r"W\d+#\d+", r.id)]
    stage_ids = [r.id for r in stage if r.status == "active"]
    assert len(stage) == 123 and len(stage_ids) == 118 and len(rows) == 126
    assert {r.id for r in stage if r.status != "active"} == {"W12#4", "W12#5", "W12#6", "W12#7", "W12#8"}
    norm = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
    for i in stage_ids:
        assert norm(ledger.get(i).what).startswith(norm(rows[i])), (i, rows[i])
    ex = [r for r in ledger if r.id.startswith("EX-build.") and r.status == "active"]
    rest = {k: v for k, v in rows.items() if k not in set(stage_ids)}
    assert set(rest) == {f"W12#{n}" for n in range(4, 12)}
    for k, v in rest.items():
        hit = [r.id for r in ex if norm(r.what).startswith(norm(v))]
        assert len(hit) == 1, (k, v, hit)


# ================================================================= 負の対照
FAKE_CONF = '''
def f(x):
    return g(x, conf="expedient")
'''
FAKE_DOC = '''"""モジュール。

expedient: 仮の宣言(負の対照)。
"""
'''


def _mismatch(ledger, extra: list[S.Declaration]) -> list[str]:
    return L.code_mismatch(ledger, [d.declared_in for d in S.scan_package()] + [d.declared_in for d in extra])[0]


def test_negative_a_new_conf_expedient_fails(ledger):
    extra = S.scan_source(FAKE_CONF, "src/shibuya/engine/fake_mod.py")
    assert [d.form for d in extra] == ["conf"]
    assert _mismatch(ledger, extra) == [extra[0].declared_in]
    for src in ("conf = 'expedient'\n", "x.conf = 'expedient'\n", "D = {'conf': 'expedient'}\n",
                "g(conf=Conf.EXPEDIENT)\n"):
        assert [d.form for d in S.scan_source(src, "src/x.py")] == ["conf"], src
    assert S.scan_source("g(conf='mechanism')\nconf = 'mechanism'\n", "src/x.py") == []


def test_negative_a_new_item_in_a_stage_list_fails(ledger):
    path = ROOT / "src" / "shibuya" / "build" / "field" / "w10_noise.py"
    text = path.read_text(encoding="utf-8")
    anchor = '"klass→AADT 既定表'
    assert text.count(anchor) == 1
    fake = text.replace(anchor, '"仮の近似(負の対照)",\n            ' + anchor)
    rel = "src/shibuya/build/field/w10_noise.py"
    before = {d.declared_in for d in S.scan_source(text, rel)}
    after = S.scan_source(fake, rel)
    new = [d for d in after if d.declared_in not in before]
    assert [d.text for d in new] == ["仮の近似(負の対照)"]
    missing, _ = L.code_mismatch(ledger, [d.declared_in for d in after])
    assert missing == [new[0].declared_in]
    # append・extend・+=・表も数える
    for src, n in (("r.expedients.append('a')\n", 1), ("r.expedients.extend(['a', 'b'])\n", 2),
                   ("r.expedients += ['a']\n", 1), ("X_EXPEDIENTS = ('a', 'b')\nS(expedients=list(X_EXPEDIENTS))\n", 2),
                   ("S(expedients=[])\n", 0)):
        assert len(S.scan_source(src, "src/x.py")) == n, src


def test_negative_a_new_docstring_paragraph_fails(ledger):
    extra = S.scan_source(FAKE_DOC, "src/shibuya/engine/fake_mod.py")
    assert [(d.form, d.text) for d in extra] == [("docstring", "expedient: 仮の宣言(負の対照)。")]
    assert _mismatch(ledger, extra) == [extra[0].declared_in]
    # 行頭でない注記・未リサーチ(expedient)は数えない
    assert S.scan_source('"""見積り(expedient: 文字数 ÷ 2)。未リサーチ(expedient)。"""\n', "src/x.py") == []


FAKE_HEAD = '''"""モジュール。

expedient(本モジュール分・負の対照)
- 仮の近似 1。
- 仮の近似 2。
"""
'''


def test_negative_a_new_heading_fails(ledger):
    extra = S.scan_source(FAKE_HEAD, "src/shibuya/engine/fake_mod.py")
    assert [(d.form, d.text, d.items) for d in extra] == [("heading", "expedient(本モジュール分・負の対照)", 2)]
    assert _mismatch(ledger, extra) == [extra[0].declared_in]
    # 全角のかっことコロン・関数の docstring も見出し。段落の文だけ(項 0)も 1 件
    src = 'def f():\n    """要旨。\n\n    expedient（自前規約）：\n        表は分の整数。\n    """\n'
    got = S.scan_source(src, "src/x.py")
    assert [(d.form, d.items) for d in got] == [("heading", 0)]
    # 項の中で折り返して行頭に来ただけの ``expedient(…)…。`` は見出しでない(閉じかっこで終わらない)
    wrapped = '"""x\n\nexpedient(本モジュール分)\n- 値は与えていない(「具体値は\n  expedient(感度試験必須)」と明記)。\n"""\n'
    got = S.scan_source(wrapped, "src/x.py")
    assert [(d.text, d.items) for d in got] == [("expedient(本モジュール分)", 1)]


def test_negative_a_changed_item_count_is_caught(ledger, decls):
    """見出しの下の項が増えると、同定(見出しの文)は同じでも台帳の ``what`` の項数と合わなくなる(試験が落ちる)。"""
    path = ROOT / "src" / "shibuya" / "engine" / "processes" / "logistics.py"
    text = path.read_text(encoding="utf-8")
    anchor = "- 宅配: 区按分"
    assert text.count(anchor) == 1
    rel = "src/shibuya/engine/processes/logistics.py"
    d0 = next(d for d in S.scan_source(text, rel) if d.form == S.FORM_HEADING)
    d1 = next(d for d in S.scan_source(text.replace(anchor, "- 仮の項(負の対照)。\n" + anchor), rel)
              if d.form == S.FORM_HEADING)
    assert d1.declared_in == d0.declared_in and d1.items == d0.items + 1
    what = ledger.get(next(r.id for r in ledger if r.declared_in == d0.declared_in)).what
    assert f"項 {d0.items} 個" in what and f"項 {d1.items} 個" not in what


def test_negative_editing_a_declaration_or_dropping_a_row_fails(ledger, decls):
    d0 = next(d for d in decls if d.form == "expedients")
    edited = [S.declared_in_of(d.path, d.form, d.text + "(書き換え)") if d is d0 else d.declared_in for d in decls]
    missing, orphan = L.code_mismatch(ledger, edited)
    assert len(missing) == 1 and orphan == [d0.declared_in]
    fewer = L.BridgeLedger([r for r in ledger if r.declared_in != d0.declared_in])
    assert L.code_mismatch(fewer, [d.declared_in for d in decls]) == ([d0.declared_in], [])


def test_doc_rows_need_no_code_declaration(ledger, decls):
    extra = L.Bridge(id="BR-DOC-ONLY", what="文書だけのつなぎ", why="試験", remove_at="7", conf="expedient",
                     declared_in="docs/design/v2-implementation-plan-2026-10-12.md §1 の 3", since="2026-11-01")
    led = L.BridgeLedger([*ledger, extra])
    assert L.code_mismatch(led, [d.declared_in for d in decls]) == ([], [])
    # 検収 M1 (c): コードが「繋ぎ」と明記した 3 か所は文書の行(関わるコードの場所つき)
    for rid, path in (("BR-START-CELL-OUTSIDE-HOME", "src/shibuya/agents/population.py"),
                      ("BR-MOCK-SCHEDULE-POPULATION", "src/shibuya/engine/run.py"),
                      ("BR-MOCK-ACTION-ANCHOR", "src/shibuya/llm/mock.py")):
        r = ledger.get(rid)
        assert not r.declared_in_code and r.code_at == (path,)
        assert "繋ぎ" in (ROOT / path).read_text(encoding="utf-8")


def test_negative_removed_rows(ledger, decls):
    """検収 L2: ``removed`` の行は数えず突き合わせない。まだコードにある宣言の行を removed にすると落ちる・宣言を消した
    後の removed の行は余りにならない。"""
    d0 = next(d for d in decls if d.form == "expedients")
    rows = [dataclasses.replace(r, status="removed") if r.declared_in == d0.declared_in else r for r in ledger]
    led = L.BridgeLedger(rows)
    assert led.count() == ledger.count() - 1 and len(led) == len(ledger)
    assert L.code_mismatch(led, [d.declared_in for d in decls]) == ([d0.declared_in], [])  # まだコードにある=落ちる
    assert L.code_mismatch(led, [d.declared_in for d in decls if d is not d0]) == ([], [])  # 宣言を消した後は通る


FAKE_PROCESS = '''
X = WorldProcess(id="fake_process", executor=Executor.ENGINE_RULE, mechanism=False,
                 sensitivity_test_id="AB-FAKE", repayment_due="Phase 3(負の対照)")
Y = WorldProcess(id="real_mechanism", mechanism=True, repayment_due="")
Z = GrowthDeclaration(name="n", mechanism=False)
'''


def test_negative_a_new_process_declaration_fails(ledger):
    """第 5 形: ``mechanism=False`` と ``repayment_due=`` の両方がある呼び出しだけ数える(成長の宣言は数えない)。"""
    extra = S.scan_source(FAKE_PROCESS, "src/shibuya/world/processes/fake.py")
    assert [(d.form, d.text) for d in extra] == [("process", "fake_process")]
    assert extra[0].declared_in == "src/shibuya/world/processes/fake.py#process:fake_process"
    assert _mismatch(ledger, extra) == [extra[0].declared_in]


def test_negative_a_new_fallback_row_fails(ledger):
    """第 6 形: フォールバック台帳に行が増えると、台帳に行が無いので落ちる。"""
    from shibuya.world.processes import first_batch as FB
    from shibuya.world.processes.relations import FallbackRow

    rows = list(FB.build_registry().fallback_ledger())
    fake = dataclasses.replace(rows[0], subject_id="fake_engine_rule", plan_spec_id="")
    assert isinstance(fake, FallbackRow)
    got = S.fallback_declarations([*rows, fake])
    keys = [d.declared_in for d in S.scan_package() if d.form != S.FORM_FALLBACK] + [d.declared_in for d in got]
    missing, orphan = L.code_mismatch(ledger, keys)
    assert missing == [f"{S.FALLBACK_PATH}#fallback:fake_engine_rule|"] and orphan == []


# ================================================================= 行の検査と凍結
def _row(**kw) -> L.Bridge:
    base = dict(id="BR-X", what="何", why="なぜ", remove_at="6-2", declared_in="docs/design/x.md", conf="expedient",
                since="2026-10-14")
    base.update(kw)
    return L.Bridge(**base)


@pytest.mark.parametrize("bad", [
    dict(remove_at=""), dict(remove_at="9-9"), dict(remove_at="第 6 期"), dict(conf="guess"), dict(status="gone"),
    dict(declared_in="README.md"), dict(declared_in="src/x.py"), dict(since="昨日"), dict(what=" "),
    dict(remove_basis="maybe"), dict(code_at=("tools/x.py",)), dict(rule_id="Bad Rule"),
])
def test_bad_rows_are_refused(bad):
    with pytest.raises(ValueError):
        _row(**bad)


def test_from_dict_refuses_unknown_fields_and_duplicates():
    d = _row().as_dict()
    assert L.Bridge.from_dict(d) == _row()
    with pytest.raises(ValueError):
        L.Bridge.from_dict({**d, "owner": "x"})
    with pytest.raises(ValueError):
        L.BridgeLedger([_row(), _row()])
    code = dict(declared_in="src/a.py#expedients:00000000")
    with pytest.raises(ValueError):
        L.BridgeLedger([_row(id="A", **code), _row(id="B", **code)])


def test_rows_and_the_ledger_are_frozen(ledger):
    r = ledger.rows[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.remove_at = "7"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        ledger._rows = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        ledger.extra = 1  # type: ignore[attr-defined]
    with pytest.raises(TypeError):
        ledger.by_id["x"] = r  # type: ignore[index]
    assert isinstance(ledger.rows, tuple) and not hasattr(r, "__dict__")


def test_the_ledger_sha_is_canonical(tmp_path):
    doc = json.loads(L.default_path().read_text(encoding="utf-8"))
    p = tmp_path / "l.json"
    p.write_bytes(json.dumps(doc, ensure_ascii=False, indent=2).replace("\n", "\r\n").encode("utf-8"))
    assert L.load(p).sha == L.default_ledger().sha == L.canonical_sha(doc)
    with pytest.raises(ValueError):
        p.write_text(json.dumps({**doc, "schema": "x/1"}), encoding="utf-8")
        L.load(p)
    # 検収 L10: 壊れた JSON・行の欠けも読み込みで落ちる
    for broken in ('{"schema": "shibuya.bridging-ledger/1", "bridges": [', json.dumps({**doc, "bridges": [{"id": "x"}]}),
                   json.dumps({**doc, "bridges": {"a": 1}})):
        p.write_text(broken, encoding="utf-8")
        with pytest.raises(ValueError):
            L.load(p)


def test_a_broken_ledger_stops_the_run_at_the_start(monkeypatch, tmp_path):
    """検収 L10: 壊れた台帳は組み立て(ランの始め)で落ちる=1 日回した後の日の締めまで待たない。"""
    from shibuya.engine.run import run_day

    p = tmp_path / "broken.json"
    p.write_text('{"schema": "shibuya.bridging-ledger/1", "bridges": [{"id": "x"}]}', encoding="utf-8")
    monkeypatch.setattr(L, "default_path", lambda: p)
    L.default_ledger.cache_clear()
    try:
        with pytest.raises(ValueError) as exc:
            run_day(n_agents=10, seed=1, n_cells=9, ticks=5, checkpoint_every=5, processes=False, renderer="stub")
        assert any(Path(str(e.path)).name == "build.py" for e in exc.traceback)  # 組み立ての中で落ちた
    finally:
        L.default_ledger.cache_clear()


def test_counts_by_remove_at_add_up(ledger):
    by = ledger.by_remove_at()
    assert sum(by.values()) == ledger.count()
    assert set(by) <= L.PLAN_STAGES
