# -*- coding: utf-8 -*-
"""ca31(第 3 期 3-1 暦 1a 影)のつなぎの台帳の行を足し直す道具(何度回しても同じ結果)。

- 構築の段 W20cal の宣言(``StageResult.expedients`` の 9 つ=``W20cal#1``〜``#9``・docstring の見出し 1 つ=``HD-…``)を
  ``engine.bridging.scan`` の今の鍵で足し直す(前の版の行は消してから足す=文を直したら回し直す)。
- W17 のつなぎの行(``BR-W17-IO-SLEEP``)に量を書き足す(量は数える道具 ``count_w17_bridges_ca31.py`` の出力
  ``ca31/w17_bridges_count.json`` から読む=直書きしない・検収 低 5)。W20cal#5 には二重計上の量を段のヘッダ
  (``calendar_1a.header.json`` の ``notes.duty_role_double_count``)から書き足す。3-1 で外れない K9 の 3 行(``BR-K9-MONDAY``・``W17#2``・
  ``DOC-md23-weekend-run-test-only``)の外す段を 3-1 → 6-2 に改める(親の判断 第336 (2)=1a は影なので外せない・1b で外す)。
- W16 の席があるのにペルソナが非就業の体の行 ``DOC-ca31-w16-seat-but-nonworking`` を足す(親の判断 第336 (3))。
- W16 の席があって学校段階の体(席を優先=勤務・授業は空欄)の行 ``DOC-ca31-w16-seat-and-school`` を足す(親の判断
  第337 中 1)。数は段のヘッダの ``calendar_counters`` から読む。

使い方(リポの根で・作業木の src): ``python docs/bench/analysis/wallbounce-1012/ca31/tools/ledger_rows_ca31.py``
台帳の書き方は今の形(``json.dumps(indent=1, ensure_ascii=False)``+改行)のまま。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "src"))

from shibuya.engine.bridging import scan as S  # noqa: E402
from shibuya.engine.calendar_shadow import STAGE_DIR  # noqa: E402

LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
MODULE = "src/shibuya/build/sched/w20_calendar_1a.py"
SINCE = "2026-10-15"
RECORD = "docs/bench/analysis/wallbounce-1012/ca31/README.md"
HEADER = REPO / STAGE_DIR / "calendar_1a.header.json"
COUNTS = HERE.parent / "w17_bridges_count.json"
REST = HERE.parent / "rest_effect.json"


def _n(x: float | int) -> str:
    return f"{int(x):,}"

#: 宣言の順 → (外す段, 外す段の根拠, 理由)。宣言の文は scan の値をそのまま ``what`` に写す。
STAGE_ROWS: list[tuple[str, str, str]] = [
    ("7", "inferred",
     "構築の段 W20cal(暦 1a)が宣言した近似(StageResult.expedients の 1 番目)。決定 10-12 §4-1 CA1「始業・終業の統計と実企業の"
     "データが見つかるまでは社会生活基本調査 第 31/36 表からの逆算でつなぎ、入力の写しになることを宣言する」(R-99 A1=始業・"
     "終業の時刻そのものの公的統計は無い)。外す段は計画に無い=主張の前に感度試験で示す(7)。記録 " + RECORD),
    ("4-1", "inferred",
     "W20cal の 2 番目。片道の通勤時間はペルソナの arrival_lead_min(v1 の在庫・意味は未確認)。AT2「通勤はランの前に積んだ経験と"
     "して実際の道のりから初期値を作る」=第 4 期 4-1 の段 6(開始前の経験・通勤の道)で外す"),
    ("6-2", "inferred",
     "W20cal の 3 番目。曜日の予定の率=社会生活基本調査 第74-6表(従業上の地位・勤務形態 × 曜日・東京都)の仕事の率そのもの"
     "(実現値=休んだ後の率=予定の率の下限・親の判断 第336 (1))・W16 に職業の列が無い(親の判断 2026-10-15 の 1)・曜日ごとに"
     "独立に引く。就業構造基本調査 第19表は年間の整合の計器(診断)。CA1「曜日は産業別・雇用形態別の統計から」。雇い主が枠を"
     "出す段(カレンダー 3=計画 6-2)で外す"),
    ("4-1", "plan",
     "W20cal の 4 番目。従業上の地位は W16 に無い=ペルソナの employment(国勢調査の 6 値)から作り、経済センサス 第6-2表の"
     "無期/有期の 6 区分への写像を宣言する(親の判断 2026-10-15 の 3・R-116 §5)。正規=無期・非正規=有期の読み替えは近似"
     "(R-99 §3-3)。第 4 期 段 3(属性=地位)で置き換える(4-1)。記録 " + RECORD),
    ("4-1", "plan",
     "W20cal の 5 番目。CA1「duty_role の人数は v1 の在庫=経済センサスとの二重計上を確かめ、雇用形態は従業上の地位で引き直す」"
     "=duty_role の体だけ第6-2表(渋谷区・中分類)で引き直す(親の判断 2026-10-15 の 4)。役割 → 職業・産業・中分類・場所・"
     "交替制の当てはめ(DUTY_ROLE_SPEC)・職業の分かる体だけ曜日の形に第74-9表の比・W16 の事業所の体の勤務場所は建物。"
     "二重計上の表は記録 " + RECORD + "。第 4 期 段 4(組織と役割)で置き換える(4-1)"),
    ("4-1", "plan",
     "W20cal の 6 番目。公務(産業大分類 S)は industry_key の 15 語に無い=新しい語を足さず空欄の宣言(親の判断 2026-10-15 の 2)。"
     "警察官・消防士・救急隊員・指令・議員の産業の欄・ペルソナの PA が空欄=第19表は産業の総数の行。第 4 期(人口の作り直し)で外す"),
    ("6-2", "inferred",
     "W20cal の 7 番目。CA1「学校は公式の時程と休業日を使う(取得先は許可を取ってから)」=本段では取得しない=授業の時間帯は空欄・"
     "通学の曜日は月〜金(規則)。時程の取得の許可の後(カレンダー 3=計画 6-2 の祝日・休業日と一緒)に外す"),
    ("6-2", "plan",
     "W20cal の 8 番目。CA1「正規雇用は毎週固定、非正規とシフト勤務は週ごとにする(雇い主がエージェントになるまでのつなぎ)」。"
     "雇い主が枠を出す段(カレンダー 3=計画 6-2)で外す"),
    ("6-2", "plan",
     "W20cal の 9 番目(親の判断 第337 (2))。週 1 日の休みそのものは規則の表の行 labor.weekly_rest_day(労働基準法 35 条 1 項・"
     "対象=無期・有期・臨時・有給役員は 9 条の労働者でないので対象外=親の判断 第337 (1))。休みの曜日の選び方=その曜日の"
     "働かない率(1 − 第74-6表の率)に比例して体・週の鍵で 1 日(毎週固定の体は週 0=毎週同じ休み)は当てはめ。35 条 2 項(4 週 4 日の"
     "変形休日制)は入れない。雇い主が枠を出す段(カレンダー 3=計画 6-2)で外す。記録 " + RECORD),
]


def main() -> int:
    head = json.loads(HEADER.read_text(encoding="utf-8"))
    cc = head["notes"]["calendar_counters"]
    cnt = json.loads(COUNTS.read_text(encoding="utf-8"))
    dup = [r for r in head["notes"]["duty_role_double_count"] if r["census_middles"] == ["42"]]
    rail_area = {r["census_area_13chome_employees"] for r in dup}
    rail_w16 = {r["w16_census_workers_same_key"] for r in dup}
    if len(rail_area) != 1 or len(rail_w16) != 1:
        raise SystemExit("中分類 42 の行の町丁目の表の人数が 1 つに決まらない")
    dup_txt = ("・".join(f"{r['duty_role']} {_n(r['bodies'])}" for r in sorted(dup, key=lambda r: -r["bodies"]))
               + f"={_n(sum(r['bodies'] for r in dup))} 体")
    STAGE_ROWS[4] = (STAGE_ROWS[4][0], STAGE_ROWS[4][1], STAGE_ROWS[4][2] + (
        f"〔第337・量〕二重計上: 中分類 42 鉄道業の町丁目の表(13 町丁目)の {_n(rail_area.pop())} 人は W16 の事業所の体"
        f"(産業の鍵 TR {_n(rail_w16.pop())} 体)に入っている上に、duty_role の{dup_txt}を足している(段のヘッダ "
        "notes.duty_role_double_count)"))
    reg = json.loads(REST.read_text(encoding="utf-8"))["rows"]["正規の職員・従業員"]["rest_effect"]
    STAGE_ROWS[8] = (STAGE_ROWS[8][0], STAGE_ROWS[8][1], STAGE_ROWS[8][2] + (
        f"〔量〕休みを入れた分だけ行の曜日の率は第74-6表の実現値を下回る=正規の行で平日 {reg[0] * 100:+.1f}・土 "
        f"{reg[1] * 100:+.1f}・日 {reg[2] * 100:+.1f} 点(休みの有無の 2 本の差・期待値 −P7 × q_d=記録 rest_effect.json・"
        "道具 rest_effect_ca31.py)"))
    raw = LEDGER.read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    rows = doc["bridges"]
    decls = [d for d in S.scan_package() if d.path == MODULE]
    exp = [d for d in decls if d.form == S.FORM_EXPEDIENTS]
    heads = [d for d in decls if d.form == S.FORM_HEADING]
    if len(exp) != len(STAGE_ROWS) or len(heads) != 1:
        raise SystemExit(f"宣言の数が違う(expedients {len(exp)}・見出し {len(heads)})")
    keep = [r for r in rows if not (r["id"].startswith("W20cal#") or r["id"].startswith("HD-build.sched.w20_calendar_1a-")
                                    or r["id"].startswith("DOC-ca31-"))]
    new: list[dict] = []
    for i, (d, (at, basis, why)) in enumerate(zip(exp, STAGE_ROWS), start=1):
        new.append({"id": f"W20cal#{i}", "what": d.text, "why": why, "remove_at": at, "declared_in": d.declared_in,
                    "conf": "expedient", "since": SINCE, "status": "active", "remove_basis": basis})
    h = heads[0]
    key = h.declared_in.rsplit(":", 1)[-1]
    new.append({
        "id": f"HD-build.sched.w20_calendar_1a-{key}",
        "what": f"{MODULE} の docstring の見出し「{h.text}」の下の項 {h.items} 個",
        "why": "コードの宣言(第 4 形=docstring の expedient(…) の見出し・このファイルの 1 つ目・見出し単位で 1 行=親の判断 第334・"
               "同じファイルの StageResult.expedients の要旨(項は W20cal#1〜#9 の行と重なる))。外す段: カレンダー 1b〜3(計画 6-2)",
        "remove_at": "6-2", "declared_in": h.declared_in, "conf": "expedient", "since": SINCE, "status": "active",
        "remove_basis": "inferred",
    })
    by_id = {r["id"]: r for r in keep}
    io = by_id["BR-W17-IO-SLEEP"]
    tag = "〔第 3 期 3-1・量〕"
    base_why = io["why"].split(tag)[0]
    rule = cnt["derive_rule_default"]
    io["why"] = (base_why + tag + f"W17 v2 の月曜の行(K9 で全部の日)で、来街者(種別 1・6・7){_n(cnt['visitors'])} 体のうち "
                 f"{_n(cnt['visitors_with_blocks_' + rule])} 体の来訪(在圏ブロック=読み口 {rule}・読み口 v1 なら "
                 f"{_n(cnt['visitors_with_blocks_v1'])})と、就寝の行 {_n(cnt['sleep_rows'])} 行({_n(cnt['sleep_agents'])} 体・"
                 f"舞台に住む体 {_n(cnt['sleep_agents_home_in'])}・宿泊 {_n(cnt['sleep_agents_lodging'])})をエンジンが実行している"
                 "(数え方の道具 docs/bench/analysis/wallbounce-1012/ca31/tools/count_w17_bridges_ca31.py)。3-1 は影の段=勤務と"
                 "授業の影だけを W20 から作り(計器)、出入りと就寝は今のまま(記録 " + RECORD + ")")
    # 親の判断 第336 (2): K9 の 3 行は 1a(影)では外せない=外す段を 6-2(カレンダー 1b=出入りを本人へ)に改める
    tag2 = "〔第336・3-1〕"
    for rid in ("BR-K9-MONDAY", "W17#2", "DOC-md23-weekend-run-test-only"):
        r = by_id[rid]
        r["why"] = r["why"].split(tag2)[0] + tag2 + "1a は影なので外せない=6-2 へ(親)"
        r["remove_at"] = "6-2"
    # 親の判断 第336 (3): 席があるのに非就業の体
    new.append({
        "id": "DOC-ca31-w16-seat-but-nonworking",
        "what": f"W16 の席(種別 0・2)があるのにペルソナの employment が非就業の体 {_n(cc['seat_nonworking'])}(うち学校段階 "
                f"{_n(cc['seat_and_school'] - cc['seat_and_school_work'])}・W16 の弱点=ペルソナと席の食い違い)。W20 は勤務の約束を"
                "空欄にした(席は W16 のまま・数を段のヘッダの calendar_counters.seat_nonworking に出す)",
        "why": "親の判断 第336 (3)。空欄は「勤務の予定を作らない」だけで、非正規=週ごとの抽選に置くより仮定が少ない(雇用形態と"
               "曜日と時刻を足さない)。席とペルソナを合わせるのは第 4 期 段 10(W16 の差し替え)。記録 " + RECORD,
        "remove_at": "4-1", "declared_in": RECORD, "conf": "expedient", "since": SINCE, "status": "active",
        "remove_basis": "plan", "code_at": [MODULE],
    })
    # 親の判断 第337 中 1: 席があって学校段階の体=席を優先して勤務(授業は空欄)
    new.append({
        "id": "DOC-ca31-w16-seat-and-school",
        "what": f"W16 の席(種別 0・2)があってペルソナが学校段階か学校のセルを持つ体 {_n(cc['seat_and_school'])}"
                f"(うち勤務の約束 {_n(cc['seat_and_school_work'])}・ペルソナが非就業の "
                f"{_n(cc['seat_and_school'] - cc['seat_and_school_work'])} は空欄)。W20 は席を優先して勤務の約束にし、授業は"
                "空欄にした(数を段のヘッダの calendar_counters.seat_and_school と seat_and_school_work に出す)",
        "why": "親の判断 第337 中 1(検収)。W16 の席は明示の事実で、ペルソナの学校段階は素材の推定=席を優先した。働く学生の"
               "授業を落とす歪み(授業と勤務の両方を持つ体は作らない)。席とペルソナを合わせるのは第 4 期 段 10(W16 の差し替え)。"
               "記録 " + RECORD,
        "remove_at": "4-1", "declared_in": RECORD, "conf": "expedient", "since": SINCE, "status": "active",
        "remove_basis": "plan", "code_at": [MODULE],
    })
    doc["bridges"] = keep + new
    out = (json.dumps(doc, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    LEDGER.write_bytes(out)
    print(f"行 {len(keep)} → {len(doc['bridges'])}(W20cal {len(exp)}・見出し 1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
