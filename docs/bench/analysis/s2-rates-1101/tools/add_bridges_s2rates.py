"""11-01 段 2 の 3・4(率の形の規則を外す): つなぎの台帳(docs/design/bridging-ledger.json)を本段に合わせて直す(何度でも)。

- 閉じる行: ``BR-ATTENDANCE-LOTTERY``(出勤率のくじ=道ごと消した)を ``removed`` にし、``why`` の末尾に閉じた注を足す。
- 注を足す行: 既定から外したが、旧道の切替口 ``--rate-rules legacy`` のためにコードの宣言が残る行(倒れる率・大規模イベントの
  過程とフォールバック・宅配の過程・5 つの docstring の見出し・乗車の混雑率の行・店の仕事の売れ残りのつなぎ)。``status`` は
  active のまま(宣言がコードにある=1 対 1 の試験)。注は印 ``〔11-01 段 2 の 3・4〕`` で 1 回だけ足す。
- 足す行(末尾): ``DOC-s2rates-*``(本段の仮採用・宣言は記録 s2-rates-1101/README.md)。同じ id の行があれば、その位置のまま
  中身を今の文に置き換える。
- 台帳の形(indent 1・ensure_ascii False・LF)は前のまま。

使い方(リポの根で): ``python docs/bench/analysis/s2-rates-1101/tools/add_bridges_s2rates.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/s2-rates-1101/README.md"
RR = "src/shibuya/engine/rate_rules.py"
SINCE = "2026-11-01"
MARK = "〔11-01 段 2 の 3・4〕"

#: 閉じる行(id → 足す注)。
CLOSE = {
    "BR-ATTENDANCE-LOTTERY": (
        MARK + "閉じた(removed): 出勤率のくじを道ごと消した(engine/presence.py の attendance_draw と ATTENDANCE_KINDS・"
        "PlanExecutor と run_day の引数 attendance_rate・CLI の --attendance-rate・manifest の attendance_rate)。判断モデルの口が"
        "できるまで「全員出勤」と宣言する(回答 11-01 §2・engine/rate_rules.py の attendance)。旧の既定 1.0 も全員出勤=既定の"
        "結果は変わらない(記録 " + DECL + ")"
    ),
}

#: 注を足す行(id → 足す注)。
NOTE = {
    "BR-BODY-COLLAPSE-RATE": (
        MARK + "既定(--rate-rules off)で外した=体の式ができるまで倒れる人は無い(W3 は錨に残す・回答 11-01 §2・§3・§9)。"
        "値 3.0 は旧道(切替口 legacy)だけが使う=次の版上げで宣言ごと消す。出動の過程は残す(発火しない)"
    ),
    "PR-large_event": (
        MARK + "既定(--rate-rules off)で人の注入(18:00 の 200 人・21:00 の退出)を外した=催しの人の注入は無い。会場 3 セルの"
        "開催と記録は残す。注入は旧道(切替口 legacy)だけ=次の版上げで消す。催しの情報を外の人に届く入力にするのは段 3"
    ),
    "FB-large_event": (
        MARK + "既定(--rate-rules off)で人の注入を外した(PR-large_event の注と同じ)。宣言の形(executor・conf)は S2-ledger が"
        "直す"
    ),
    "PR-delivery_last_mile": (
        MARK + "既定(--rate-rules off)で宅配の過程を動かさない=宅配は無い(W2 は錨に残す=駆動と採点の循環を解く)。区按分は"
        "旧道(切替口 legacy)だけ=次の版上げで消す。宣言の形は S2-ledger が直す"
    ),
    "HD-engine.presence-b560bcbc": (
        MARK + "項 E6(出勤率)は消した=全員出勤・項 E8(到着の分散)は既定から外した=全員が E1 の便(旧道は切替口 legacy)。"
        "項の数は 9 のまま(項の文に注を足した)"
    ),
    "HD-engine.processes.civic-fe8b67d5": (
        MARK + "項「大規模イベント」の注入は既定から外した(旧道は切替口 legacy)。項の数は 6 のまま"
    ),
    "HD-engine.processes.goods_flow-fe8b67d5": (
        MARK + "項「売れ残り → ビン」と項「街路ごみ」は既定から外した=売れ残りの廃棄は無い・ポイ捨ては無い(旧道は切替口 "
        "legacy)。項の数は 8 のまま"
    ),
    "HD-engine.processes.logistics-fe8b67d5": (
        MARK + "項「宅配」は既定から外した=宅配は無い(旧道は切替口 legacy)。項の数は 4 のまま"
    ),
    "HD-engine.processes.rail-1af925f4": (
        MARK + "見出しの外の §2.6 の受け入れ確率(150〜200% で 1.0→0.7)は既定から外した=200% の上限だけ物理として残す"
        "(旧道は切替口 legacy)。見出しの項の数は 6 のまま"
    ),
    "DOC-tt23c-rail-congestion": (
        MARK + "受け入れ確率(受容関数)は既定から外した=200% の上限だけ(5,000 体では前も今も乗り残し 0)"
    ),
    "DOC-du1-unstaffed-bridge": (
        MARK + "このうち売れ残りの 05:00 のつなぎ(廃棄率)は既定から外した=担当の体の居ない店の売れ残りは捨てられない"
        "(担当の体が捨てる分=腕 duties は残る・旧道は切替口 legacy)"
    ),
}


def _row(id_: str, what: str, why: str, code_at: list[str], *, remove_at: str, basis: str = "plan") -> dict:
    return {"id": id_, "what": what, "why": why, "remove_at": remove_at, "declared_in": DECL, "conf": "expedient",
            "since": SINCE, "status": "active", "remove_basis": basis, "code_at": code_at}


ROWS = [
    _row("DOC-s2rates-legacy-switch",
         "切替口 --rate-rules legacy(環境変数 SHIBUYA_RATE_RULES=legacy)は 11-01 段 2 の 4 の版上げの前の値の再現のためだけの道"
         "(催しの 200 人注入・E8 の到着の分散・乗車の受け入れ確率・ポイ捨て 0.05 g/人/刻み・売れ残りの廃棄率・宅配の区按分・"
         "倒れる率 3.0 件/万体/日)。出勤率のくじは戻らない(道ごと消した)",
         "回答 10-13b §0-6(版上げで新しい道を既定にしたら古い道の切替口は次の版上げで消す・旧値の再現は安定版のタグで)。"
         "legacy の 5,000 体 × 1 日 mock は前の版と final が一致(記録 " + DECL + ")。次の版上げで切替口を消すときに書き直す"
         "試験(旧道に固定した試験=検収 L5): test_du_runs の朝のつなぎ・test_cp2_event_links の補充の行・test_resume_10d の"
         "宅配の張り直し・test_state_ledger_10b の t7 の旧道の 1 本・倒れる率の試験の口を使う試験(test_salient・"
         "test_rng_scheme_10c・test_ablation23_switches・test_resume_10d・test_salt_seed_split_10f・test_state_checks_10f・"
         "test_version_bump_10e)・旧道の規則を見る過程の試験(test_civic・test_goods_flow・test_logistics・test_rail_return・"
         "test_presence_executor の E8 の 3 本と催しの経路)",
         [RR, "src/shibuya/cli.py"], remove_at="next-bump"),
    _row("DOC-s2rates-event-held-log",
         "催しの人の注入を外した後も、会場 3 セルの抽選と開催の記録(ActualLog の SCHEDULED の行=18:00 と 21:00)は残す"
         "(旧道の注入と退出の行と同じ形・体は動かさない)",
         "指示書 11-01 段 2 の 4「催しの開催そのもの(会場 3 セル)は残す」。開催の情報を外の人に届く入力にし、来るかを本人が"
         "決めるのは段 3(回答 11-01 §2・§8)。会場の決め方(日の鍵の乱数で 3 セル)は今のまま=未リサーチ(expedient)",
         # 11-01p の「段 3」は PLAN_STAGES に無い=判断モデルの口の段 6-1 を当てた(仮・親の判断=記録の問い)
         ["src/shibuya/engine/processes/civic.py"], remove_at="6-1", basis="inferred"),
    _row("DOC-s2rates-collapse-test-knob",
         "倒れる率を直に渡す口(run_day の salient_rate_per_10k・SalientProcess の rate_per_10k_per_day)は旧道(--rate-rules legacy)"
         "でだけ効く。腕 off では無視して率 0(removed の印と食い違わない=検収 L3)。manifest の rate_rules.counts に実効の率と"
         "件数が出る",
         "既存の試験と道具(tools/c7/salt_runs.py の腕 sal ほか)が出動の経路を見るのにこの口を使う=その試験は旧道で回す。"
         "次の版上げで旧道と一緒に口を消す(記録 " + DECL + ")",
         ["src/shibuya/engine/processes/salient.py", "src/shibuya/engine/run.py"], remove_at="next-bump",
         basis="inferred"),
    _row("DOC-s2rates-waste-band-na",
         "腕 off(既定)のランの店の廃棄の帯(runner.waste_sink_report の band_ok・月次 MER の waste_band_ok)は非該当(None・"
         "理由 band_na/waste_band_na=売れ残りの廃棄率を外した)。帯は初期在庫 × SKU の廃棄率の静的な期待(外した #99)で、比べる"
         "相手が無い。値(帯・内訳・店の回収量)は残す。要約は「非該当(…)」と書き、tools/c7/c7lib.py は None と読む",
         "検収 M1(既定のランが毎回 NG を出し、原因が外した規則であることが宣言されていなかった)・回答 11-01 §2。店の売れ残りの"
         "廃棄が店員の判断(腕 duties)で既定になったら、帯をその出力と比べ直す",
         ["src/shibuya/engine/processes/runner.py", "src/shibuya/economy/census.py", "src/shibuya/cli.py",
          "src/shibuya/engine/run.py"], remove_at="6-6", basis="inferred"),
]


def _note(row: dict, text: str) -> bool:
    if MARK in row["why"]:
        return False
    row["why"] = row["why"] + text
    return True


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = data["bridges"]
    pos = {r["id"]: i for i, r in enumerate(rows)}
    missing = [k for k in (*CLOSE, *NOTE) if k not in pos]
    if missing:
        print(f"台帳に無い行(止める): {missing}")
        return 1
    changed = 0
    for rid, text in CLOSE.items():
        r = rows[pos[rid]]
        changed += int(_note(r, text))
        if r["status"] != "removed":
            r["status"] = "removed"
            changed += 1
    for rid, text in NOTE.items():
        changed += int(_note(rows[pos[rid]], text))
    added = 0
    for r in ROWS:
        if r["id"] in pos:
            rows[pos[r["id"]]] = r
            continue
        rows.append(r)
        added += 1
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"直した行 {changed}・足した行 {added}・台帳 {len(rows)} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
