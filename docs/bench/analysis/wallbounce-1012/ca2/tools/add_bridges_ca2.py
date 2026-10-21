"""第 6 期 6-2 カレンダー 2: つなぎの台帳(docs/design/bridging-ledger.json)に本段の行を末尾に足す(何度でも)。

- 足す行: ``DOC-ca2-*``(本段の仮採用・宣言は記録 ca2/README.md・status は active)。同じ id の行があれば、その位置のまま
  中身を今の文に置き換える(何度回しても同じ台帳)。
- 台帳の形(indent 1・ensure_ascii False・LF)は前のまま。足すのは末尾だけ(並行の作業木との取り込みで当たりを小さく)。
- 外す段に ``next-bump`` は使わない(腕の既定化は実 LLM の後=6-2 の版上げ)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/ca2/tools/add_bridges_ca2.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/wallbounce-1012/ca2/README.md"
LY = "src/shibuya/engine/calendar2/layer.py"
PT = "src/shibuya/engine/calendar2/port.py"
BK = "src/shibuya/engine/calendar2/book.py"
RC = "src/shibuya/engine/calendar2/recall.py"
SINCE = "2026-10-18"


def _row(id_: str, what: str, why: str, code_at: list[str], *, remove_at: str, basis: str = "inferred") -> dict:
    return {"id": id_, "what": what, "why": why, "remove_at": remove_at, "declared_in": DECL, "conf": "expedient",
            "since": SINCE, "status": "active", "remove_basis": basis, "code_at": code_at}


ROWS = [
    _row("DOC-ca2-initial-empty",
         "初めの個人の予定(ランの始まりに本人が自分の予定を書く口 Calendar2Layer.write_initial)は空で始める(仮のモデル="
         "書かない)。慣らし期間で人との約束が生まれるのは会話の番の仕組み",
         "決定 10-12 §4-1 CA2 (c)(d)・5-2「書けるようになるまでは、空で始めるつなぎ」。本人が書けるのは判断モデルの段(6-1)。"
         "統計は検証にだけ使う(錨は読まない)", [LY], remove_at="6-1", basis="plan"),
    _row("DOC-ca2-port-candidates",
         "カレンダー 2 の判断の候補の語と源の当て方(会話の番 3・いつ=日 7 日先まで・正時・長さ 1/2/3 時間と決めない・どこで="
         "ここ/言葉・返事 3・返事を聞いた人の確かさ 2・置き場所 4・知らせ 10/30/60 分前・実行意図・見えた予定 3・変える 4・範囲外の"
         "過ごし方・変える予定の候補=会話の相手との自分の行のうち今見える行の全部(確かめは想起の練習に数えない=選んだ行だけ練習)・"
         "提示の番号の上限 127 を超えるときは本人が日 → 正時で絞る・それでも 120 を超えたら安全装置=始まりの近い順に 120 まで・"
         "当たった回数は manifest の changes.candidates_capped)と仮のモデル"
         "(mock=候補を語と id の順に並べ乱数の余りで一様に選ぶ)・何をと言葉の場所は文の口の定型の文",
         "CA3「約束を結ぶか・内容は本人の判断」・回答 2-1(GPU の前は仮のモデル)。候補の作り方は実装役の構成=未リサーチ"
         "(expedient)。判断モデル(6-1)と LLM で置き換える=数は振る舞いのモデルではない", [PT, LY], remove_at="6-1"),
    _row("DOC-ca2-placement-kinds",
         "置き場所の種類の初期の一覧 4 つ(アプリ・アラーム・手帳・頭の中)と性質の値(知らせ・持ち歩き・見える範囲・忘れやすさ・"
         "思い出し方・重なりの警告)・行の種類 5 つ(二人の約束・本人の予定・本人の計画・アラーム・出来事の実行意図)",
         "CA3「置き場所は性質で書き、種類は増やせる」・5-1「カレンダーに入るもの」。一覧と性質の値は未リサーチ(expedient)="
         "道具の台帳(CT0)の行と結ぶのは 6-4 の C2 以降", [BK], remove_at="7"),
    _row("DOC-ca2-ca7-provisional",
         "アラームと時刻の実行意図は同じ種類の行(結びつく行=約束・上限なし)・出来事がきっかけの実行意図(相手に会ったら確かめる)は"
         "計画の記憶=頭の中の行(きっかけ=相手が同じセル)",
         "決定 10-12 §4-1 CA7 (a)(c)=仮(リサーチ B4)。実行意図の数値の錨は手元に無い(R-68 結論 1)=B4 の答申の後に決め直す",
         [LY, BK], remove_at="6-2", basis="plan"),
    _row("DOC-ca2-head-recall",
         "頭の中の予定の思い出し=記憶 M1 の式(ACT-R の折衷形・d=0.5×人ごとの倍率・τ=M1 の仮の値)・重要度=会話の記憶と同じ値・"
         "思い出す機会=本人が考えた刻み・手がかり=約束の相手が同じセル(W_CUE)・思い出した回は痕跡に足す。記憶の器(1-6)には"
         "予定の行を足していない(器の無いランの形と同じ口=読む側は分岐しない)",
         "CA3「本人には記憶で思い出せたときだけ見せる」・AT1・MR-0・MR1・MR4・MR8。値は記憶 6-5 の仮の値のまま(expedient)。"
         "器に予定の種類を足すか=親の判断", [RC, LY], remove_at="6-5"),
    _row("DOC-ca2-turn-opportunity",
         "誘いの機会=会話の自分の番ごと(対面=会話の番の発話・通話=通話の番・メッセージ=送る判断)・返事は相手の次の番・出した人が"
         "聞くのは自分の次の番(返事が全部そろったとき)か会話の終わり・メッセージは読む前でも次の番で返事を聞く・返事の無い誘いは"
         "会話の終わりで消える・誘いと返事と書くは番と同じ刻みの別の呼び(GPU の後は番の LLM の出力に畳む)",
         "CA3・CA9(段 2=会話とメッセージ・C1 と束ねる)・TM3。会話から約束が生まれる割合は空欄(R-85 §3)=機会の形は実装役の"
         "構成(expedient)。判断モデル(6-1)と会話の番の LLM で置き換える", [LY], remove_at="6-1"),
    _row("DOC-ca2-visibility",
         "見える予定=その日の自分の行だけ・アプリは連絡の道具の無いランでは考えたとき見える(あるランは画面を見ているときと知らせ)・"
         "アラームは鳴ったとき(寝ていれば起きた後に考えたとき)・手帳はその日に最初に考えたとき・頭の中は記憶で思い出せたとき。"
         "〔検収 M2〕会話の番の「自分の約束を変える」の候補も同じ口で見える行だけ(手帳は開く前なら見える=開いた印は付けない)",
         "AT1(置き場所の性質で思い出し方)・CA4「本人に見せるのは置き場所の道具が現実に教えることだけ」。いつ見るかは本人の行動="
         "判断モデルまでの仮の習慣(expedient)", [LY], remove_at="6-1"),
    _row("DOC-ca2-arbitration",
         "見える予定の判断(出発する/まだ/行かない)は、その刻みに主の判断の呼びのあった体ではしない=次の刻みに回す(連絡の道具 C1 と"
         "同じ規則)",
         "C1 の ARBITRATION と同じ形(連絡の判断と主の判断が同じ刻みにぶつかる所)。判断モデルで主の判断の候補に載せる(6-1)",
         [LY], remove_at="6-1"),
    _row("DOC-ca2-exec-scope",
         "約束の場所へ歩くのは地名帳のセルの行だけ(言葉のままの場所と範囲の外の体は出発しても歩けない=記録だけ)・着いた=約束の"
         "セルに入った刻み・5 分前到着の 5 分は CA8 の計器の定義・終わりを決めていない行はその日の最後の刻みで締める",
         "CA4「地名帳に無い場所は言葉のまま持つ」・CA8。言葉の場所を地名帳に結ぶのは本人の検索(C4)・範囲の外の移動は鉄道と境界の"
         "段(仮)", [LY], remove_at="6-4"),
    _row("DOC-ca2-impossible-form",
         "不可能な予定(記録だけ)=間に合わない(今の居場所から歩行グラフの節の数 × 刻みの幅=1 刻み 1 節=1b の見積りと同じ)・閉店中"
         "(約束のセルの店が始まりの分にどれも開いていない=始まりの日の営業の表=今日は今の表・ほかの日は W7 の区間のその日の行)・"
         "過ぎた時刻",
         "CA4「間に合わない・閉店中は記録だけ」・CA8 の計器「不可能な予定」。歩く時間の見積りは空間の段 1(ナビメッシュ)で"
         "置き換える", [LY], remove_at="5-1"),
    _row("DOC-ca2-outside-plan",
         "範囲外の過ごし方=体が範囲の外に出た刻みに本人が本人の計画(頭の中)に書くか選ぶ(何を=文の口)・戻ったら締める・実行は"
         "今のまま(範囲外の食事の予定・W17 の行)",
         "決定 10-12 §4-1 CA6 (b)・10-03 §7-1(範囲外の人の 1 日を移す)。1b の出入りの判断と W17 の行の関係を壊さない形(仮)。"
         "範囲外の過ごし方を本人が決めて実行する段で置き換える", [LY], remove_at="6-6"),
    _row("DOC-ca2-not-default",
         "カレンダー 2 の腕(--calendar-2 arm)は既定にしない。仮のモデルの量(5,000 体・1 日・C1 と束ねたラン)=判断の呼び "
         "370,463 回・約束の族 229,558 行・出来事の記録の全体 31.0+26.0 MB/日のうちカレンダー 2 の分は約 26 MB(行 16.4 MB・原因の表 "
         "9.7 MB)=既定化の条件(1-3 の宣言)を満たしていない。壁時計(参考・並行のランあり)は arm だけ 57.1 秒(既定 44.5 秒)・"
         "C1+arm 378.5 秒(検収 M2 の直しの前 193.8 秒=変える候補を見える行に絞る想起の強さの計算=推測・腕の中だけ)",
         "CA9(段 2 の版上げは C1 と束ねる=実 LLM の後)・10-13b §0-6。既定化は 6-2 の版上げで判断モデルと LLM を入れてから",
         [LY], remove_at="6-2", basis="plan"),
    _row("DOC-ca2-offer-grace",
         "返事の無い誘いの会話が一度も生きていないとき(送ったメッセージは次の窓の境目でチャットの会話になる)に待つ刻みの数 "
         "OFFER_GRACE_STEPS=2(これを過ぎたら誘いを消す)",
         "〔検収 L2〕エンジンが決める待ちの長さ=チャットの会話の状態が届いた後にできる形のつなぎ(expedient)。実 LLM の段(6-2 の"
         "版上げ)で会話の番の出力と届く時刻から決め直す", [LY], remove_at="6-2"),
    _row("DOC-ca2-fleet-turn-unchecked",
         "艦隊の経路(到着の系 llm_receive の会話の番の発話 → Calendar2Layer.note_turn=宣言 CA2G:calendar2._turns)は mock では通らない="
         "段 B で確かめていない",
         "〔検収 宣言〕mock と再生のないランは判断の系の道だけを通る。実 LLM(艦隊)の段で段 B を回して確かめる", [LY],
         remove_at="6-2"),
]


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    pos = {r["id"]: i for i, r in enumerate(data["bridges"])}
    added = 0
    for r in ROWS:
        if r["id"] in pos:  # 本段の行は中身を今の文に置き換える(位置はそのまま=末尾の並びを変えない)
            data["bridges"][pos[r["id"]]] = r
            continue
        data["bridges"].append(r)
        added += 1
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"足した行 {added}・台帳 {len(data['bridges'])} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
