"""第 6 期 6-2 カレンダー 1b: つなぎの台帳(docs/design/bridging-ledger.json)に本段の行を足し、2 行に注を書き足す(何度でも)。

- 足す行: ``DOC-ca1b-*``(本段の仮採用・宣言は記録 ca1b/README.md・status は active)。同じ id があれば足さない。
- 注を書き足す行: ``BR-W17-IO-SLEEP``・``BR-E4-EXIT-VANISH``(腕 1b で外れる部分/残る部分。status と外す段は変えない=
  既定(w17)では生きている)。同じ注があれば足さない。
- 台帳の形(indent 1・ensure_ascii False・LF)は前のまま。足すのは末尾だけ(並行の作業木との取り込みで当たりを小さく)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/ca1b/tools/add_bridges_ca1b.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/wallbounce-1012/ca1b/README.md"
CS = "src/shibuya/engine/calendar_self.py"
PR = "src/shibuya/engine/presence.py"
TR = "src/shibuya/engine/tools/registry.py"
SINCE = "2026-10-15"
NOTE_TAG = "〔第 6 期 6-2・腕 --calendar 1b〕"


def _row(id_: str, what: str, why: str, code_at: list[str], *, remove_at: str, basis: str = "inferred") -> dict:
    return {"id": id_, "what": what, "why": why, "remove_at": remove_at, "declared_in": DECL, "conf": "expedient",
            "since": SINCE, "status": "active", "remove_basis": basis, "code_at": code_at}


ROWS = [
    _row("DOC-ca1b-scope",
         "カレンダー 1b で本人へ渡すのは時刻つきの勤務の約束だけ(授業=時刻が空欄・自宅で働く・家も約束の場所も域外の体は W17 の"
         "まま)。管理する体はその日の W17 の到着・退出を全部止める(約束の外の来訪も)・来街者の来訪と就寝・起床は W17 のまま",
         "決定 10-12 §4-1 CA2 (b)・CA9(1b=勤務・通学の出入り・寝る起きる=疲労の後・来街者=判断モデルの後)。学校の時程は空欄"
         "(W20cal#7)=授業の出入りは渡せない。約束の外の来訪を止めるのは、同じ体の出入りを W17 と本人の 2 つが動かさないため"
         "(仮採用)。〔検収 L9〕外す段=来街者と通学を本人へ渡す段(判断モデルの後=6-6)", [CS, PR], remove_at="6-6",
         basis="plan"),
    _row("DOC-ca1b-placement-initial",
         "置き場所の初期の割り振り=アプリ・アラーム・手帳・頭の中を体の鍵で等分(W20 の置き場所の欄は 1a で空欄)",
         "決定 10-12 §4-1 AT1・CA3(置き場所は性質で書く)。人ごとの置き場所の実データは無い=未リサーチ(expedient)。本人が"
         "ランの始まりに自分の予定を書く段(初めの個人の予定 (c)=カレンダー段 2・C1 と束ねる=6-4)で置き換える〔検収 L9〕",
         [CS], remove_at="6-4"),
    _row("DOC-ca1b-margin",
         "余裕(出発を早める分)=0・5・10・15 分を体の鍵で等分(仮のモデルの本人の判断)",
         "決定 10-12 §4-1 AT2「余裕は本人の判断」。判断モデルができるまでの仮の値(錨は空欄=R-89 の時間厳守は検証側)",
         [CS], remove_at="6-6"),
    _row("DOC-ca1b-look-interval",
         "頭の中の予定を思い出す機会=本人が時計を見る間隔 30 分(位相は体の鍵)・思い出したときは予定を入力に載せる",
         "決定 10-12 §4-1 AT1「頭の中=記憶で思い出せたとき・MR7 までは頭の中の予定も入力に載せるつなぎ」。間隔の錨は無い"
         "=未リサーチ(expedient)", [CS], remove_at="6-5", basis="plan"),
    _row("DOC-ca1b-planner-look",
         "手帳を見る時刻=その日の最初に起きている刻み(見た後は頭の中=時計を見る習慣へ)",
         "決定 10-12 §4-1 AT1「手帳や壁=見たとき」。いつ見るかは本人の行動=判断モデルまでの仮の習慣(expedient)",
         [CS], remove_at="6-6"),
    _row("DOC-ca1b-approx-time",
         "時計を見ないときの時刻=30 分に丸めた「ごろ」(手帳を見たとき)",
         "決定 10-12 §4-2 TM8「見なければおおよそ」。丸めの幅は未リサーチ(R-111 §1-3 の空欄=時計を見ない日常の時刻の誤差)",
         [CS], remove_at="7"),
    _row("DOC-ca1b-estimate-initial",
         "見積りの初期値=舞台の中は W3 の歩行グラフの節の数(1 刻み 1 節)・域外は下の域外の時間・幅=その路線の便の間隔の"
         "中央値(待ちの最大)",
         "決定 10-12 §4-1 AT2(通勤はランの前に積んだ経験=実際の道のりから初期値・見積りは幅)。4-1 段 6 の通勤の道のり "
         "w21_prior は人口が活性化していない(本体の母集団は W16)=W3 の最短の道のりから作った。辺の幾何の腕では実際の歩きと"
         "ずれる(直近の平均で直る)", [CS], remove_at="4-3"),
    _row("DOC-ca1b-estimate-update",
         "見積りの更新=直近 5 回の行きの実感の値の平均・幅=直近の最小と最大(2 回より少なければ最初の幅)",
         "決定 10-12 §4-1 AT2「更新は記憶の仕組み(それまでは直近の平均)」。回数と幅の作り方は未リサーチ(expedient)",
         [CS], remove_at="6-5", basis="plan"),
    _row("DOC-ca1b-outside-time",
         "域外の時間=W20 の片道の通勤時間(ペルソナの lead)−舞台の中の歩きの時間(下限 0)。域外からは「出発+域外の時間」より"
         "後に最初にホームへ入るその路線の便で着く(域外の駅での待ちの分は着く便までの差・乗り残しと遅れは扱わない)",
         "決定 10-12 §1-3 の 1(範囲の外は粗い形)・§4-1 AT3(第 1 段では遅れを出さない)。片道の時間は v1 の在庫(W20cal#2)",
         [CS], remove_at="7"),
    _row("DOC-ca1b-end-notice",
         "約束の終わりの時刻に帰りの機会を 1 回(職場の時計=分単位)。本人の記録を参照しない機会(検査の数は end_notices)",
         "決定 10-12 §4-1 CA9 段 3(雇い主・職場の連絡=C3 と束ねる=6-4)まで。終業のチャイムや同僚の退勤の代わり(仮採用)"
         "〔検収 L9〕", [CS], remove_at="6-4", basis="plan"),
    _row("DOC-ca1b-blank-place-cell",
         "目的のセルが空欄の約束の場所(担当区域・乗り物の一部)は駅の口のセルを行き先の代わりにする",
         "W20 の担当区域と一部の乗り物はセルが空欄(W20cal#5)。場所は空間の段と人口の活性化で埋まる(仮採用)", [CS],
         remove_at="4-3"),
    _row("DOC-ca1b-gate-exit",
         "非鉄道の方面(8・9)の体と、路線に便もホームも無い体は、駅の口のセルへ歩いて境界を越える(境界のセルの代わり)",
         "決定 10-12 §1-3 の 1(出入りは境界を歩くか乗り物で越える)。境界のセルは空間の段の宿題(計画実行層の E3 と同じ)",
         [CS], remove_at="5-2"),
    _row("DOC-ca1b-commuter-pass",
         "本人の退出の歩き(自分の路線のホームへ)は計画の退出の印 EXIT_WALK_FLAG を立てる=運賃の免除(定期券の代わり)",
         "9b の計画の退出の運賃の免除と同じ扱い(所持金が足りない勤め人が帰れなくなる穴を作らない)。支払いの方法と定期券は"
         "経済の中身の段", [CS], remove_at="4-2"),
    _row("DOC-ca1b-retry-cap",
         "歩きが途切れた体(本人がほかの行為を選んだ・待ちの打ち切り)はその場に居続け、次に時計を見る時刻(30 分後)に出入りを"
         "もう一度出す・1 日 8 回まで(上限は安全装置・当たったら数える)",
         "決定 10-12 §1-3 の 1(体は消えない=E4 を外す)。再提示の時刻と上限は未リサーチ(expedient)・判断モデルまで",
         [CS], remove_at="6-6"),
    _row("DOC-ca1b-felt-form",
         "経過時間の実感=待ちは 1.9+0.72×実際[分](Watkins 2011)・待ち以外(歩く・乗る・域外)は比 1・本人に渡す言葉は 5 分に"
         "丸める・見積りの更新は実感の値・実際の値は記録へ。〔検収 L12〕待ちの式は出典の範囲(3〜15 分)の中だけ・外は比 1",
         "決定 10-12 §4-1「経過時間の実感」(係数は決め打ちせず研究から)。R-111 §1-2 #1 の錨の値そのまま・ほかの項(到着表示・"
         "夕方・便数・いらだち)は 0・待ち以外は R-111 §1-3 の空欄", [CS], remove_at="7"),
    _row("DOC-ca1b-provisional-model",
         "仮のモデル(判断モデルまでのつなぎ): 予定の出発=約束の始まり−見積り(mock=幅の上・古典=幅の真ん中)−余裕・「まだ」の"
         "ときの次に見る時刻=予定の出発(時計を見ていれば)・帰り=終わりの時刻",
         "決定 10-12 §4-1 CA5 問い 2(モックは「そのまま」寄り)・回答 10-12 §2-1(GPU の前は仮のモデル)。GPU が届いたら判断"
         "モデルの測定と選定から入れる", [CS], remove_at="6-1", basis="plan"),
    _row("DOC-ca1b-forecast-blank",
         "道具の台帳の「天気予報」の中身は空欄(範囲の外の実データ=気象庁の府県天気予報の本文の取得物がランの日に無い)",
         "決定 10-12 §4-4 CT0(天気予報はカレンダー 1b と一緒・範囲の外の情報は実データを境界の入力に)。data/realworld/jma_xml "
         "は防災情報 XML の長期フィードの一覧(2026-08-07〜)で、ランの日の予報の本文ではない", [TR], remove_at="7"),
    _row("DOC-ca1b-events-what",
         "出発と帰るの判断の出来事の what は「行為:移動」(語彙に出発・帰るの語が無い)・原因は LlmCall(源 plan と提示の番号)",
         "口の約束 1-3(閉じた語彙)・1-8 の約束 (3)。語を足すのは語彙の版上げ(6-4 C1 で道具の行為の語と一緒=親の判断)"
         "〔検収 L9〕", [CS], remove_at="6-4"),
]

ROWS += [
    _row("DOC-ca1b-left-at-work",
         "〔検収 H1〕勤務中に本人の行為(乗車など)で舞台を出た体には、約束が続いている間は歩きの途切れと同じ規則で次の機会を"
         "出す(時計を見る習慣の 30 分後・1 日 8 回まで・上限の後は終わりの時刻の機会)=戻るかは本人の判断。mock の行為の抽選は"
         "変えない(仮のモデル)",
         "決定 10-12 §4-1 CA2 (b)(出入りは本人の判断)・§1-3 の 1。再提示の時刻と上限は DOC-ca1b-retry-cap と同じ(未リサーチ)。"
         "計画一致率と在場率は体の位置で数える(段の値は *_phase の欄)", [CS], remove_at="6-6"),
    _row("DOC-ca1b-observation-form",
         "〔検収 M2 (a)〕判断の入力の観測は 1-2 の Percept(time_view)でなく独自の Observation(読んだ時刻・分かおおよそか・"
         "言葉・居る所・きっかけ)",
         "口の約束 1-2(知覚の事実の形)。域外に居る体の場面(SceneView)・体の段を作る口が無い=Percept を作れない。1b の既定化"
         "(6-2 の版上げ)の前に Percept に統一する", [CS], remove_at="6-2", basis="plan"),
    _row("DOC-ca1b-llm-run-mock-port",
         "〔検収 M2 (c)〕LLM のランでも 1b の出入りの判断は層が持つ仮のモデル(mock/古典の規則)の口で、ランの判断の口ではない",
         "回答 10-12 §2-1(GPU の前は仮のモデル)。1b の既定化(6-2 の版上げ)でランの判断の口(J0)に載せる", [CS],
         remove_at="6-2", basis="plan"),
    _row("DOC-ca1b-alarm-system1",
         "〔検収 L4〕アラームは鳴った数を数えるだけ=周りの出来事として System 1(1-2 の Percept の B 群・nearby_change)へは"
         "届けていない・寝ていても起こさない(起こすのは W17 の起床のまま)",
         "決定 10-12 §4-1 AT1「アラーム=鳴る」・CT3(通知は周りの出来事の 1 つとして System 1 へ)。届ける口は C1 の通知の段"
         "(6-4)・起こすのは疲労の後", [CS], remove_at="6-4"),
    _row("DOC-ca1b-tools-n-tools",
         "〔検収 L8〕道具の台帳に時計と天気予報を足したので、既定(w17)の manifest の tools.n_tools が 7 → 9(25 欄の外・"
         "記録だけ・1-7 の C0 は器だけ=既定の候補と描画は不変)",
         "決定 10-12 §4-4 CT0(天気予報と時計はカレンダー 1b と一緒)。口の約束 1-4 の約束 (3)「既存の欄の値は不変」の例外"
         "として宣言(親の判断)", ["src/shibuya/engine/tools/registry.py"], remove_at="6-2"),
    _row("DOC-ca1b-initial-inside",
         "〔検収 L10〕0 時の初期配置で計画実行層が W17 の在圏ブロック(0 時から)に従って管理する体を舞台に置く(5,000 体で 2 体)"
         "=初期の状態(連続性の検査の外)",
         "決定 10-12 §1-3 の 1「ランの始まりに全員を置くことだけは初期の状態として例外」。初期配置を W20 の約束から作るのは "
         "1b の既定化の段", [CS, PR], remove_at="6-2"),
]

NOTES = {
    "BR-W17-IO-SLEEP": (
        f"{NOTE_TAG}外れる部分=その日に時刻つきの勤務の約束を持つ体(W16 の勤め人の大半)の到着・退出(W17 の ARRIVE/DEPART と張り"
        "直しの到着)は計画実行層が実行せず、本人の判断(候補の口)と世界(ホームで来た電車・歩き・境界)で動く。残る部分=就寝・"
        "起床(全員・疲労の後)・来街者の来訪・授業(時刻が空欄)・自宅で働く体・家も場所も域外の体・出勤率のくじで休む体の"
        "出入り。既定(w17)では今のまま(記録 docs/bench/analysis/wallbounce-1012/ca1b/README.md)"),
    "BR-E4-EXIT-VANISH": (
        f"{NOTE_TAG}外れる部分=本人が出入りを決める体は、退出の途中で別の行為を選んでも消さずその場に居続け、次の機会に本人が"
        "決め直す(体の連続性の検査 exits_unexplained=0)。残る部分=W17 で出入りする体(来街者ほか)の即時の退出(既定の "
        "--exit-mode immediate)と、9a の歩いて乗る退出の打ち切り。既定(w17)では今のまま"),
}


def main() -> int:
    doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    if "--replace" in sys.argv[1:]:  # 〔検収〕本段の行を ROWS で置き換える(並びは本段の最初の行の位置から)
        old = [j for j, r in enumerate(doc["bridges"]) if str(r["id"]).startswith("DOC-ca1b-")]
        at = old[0] if old else len(doc["bridges"])
        rest = [r for r in doc["bridges"] if not str(r["id"]).startswith("DOC-ca1b-")]
        doc["bridges"] = rest[:at] + ROWS + rest[at:]
    by = {r["id"]: r for r in doc["bridges"]}
    noted = 0
    for rid, note in NOTES.items():
        r = by[rid]
        if NOTE_TAG not in r["why"]:
            r["why"] = r["why"] + note
            noted += 1
    have = set(by)
    added = [r for r in ROWS if r["id"] not in have]
    doc["bridges"].extend(added)
    LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"足した行 {len(added)}・注を足した行 {noted}・台帳 {len(doc['bridges'])} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
