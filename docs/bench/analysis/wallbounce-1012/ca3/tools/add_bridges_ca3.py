"""第 6 期 6-2 カレンダー 3: つなぎの台帳(docs/design/bridging-ledger.json)に本段の行を末尾に足す(何度でも)。

- 足す行: ``DOC-ca3-*``(本段の仮採用・宣言は記録 ca3/README.md・status は active)。同じ id の行があれば、その位置のまま
  中身を今の文に置き換える(何度回しても同じ台帳)。
- 台帳の形(indent 1・ensure_ascii False・LF)は前のまま。足すのは末尾だけ(並行の作業木との取り込みで当たりを小さく)。
- 外す段に ``next-bump`` は使わない(腕の既定化は実 LLM の後=6-2 の版上げ・雇い主のエージェントは 6-6 ②)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/ca3/tools/add_bridges_ca3.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/wallbounce-1012/ca3/README.md"
LY = "src/shibuya/engine/calendar3/layer.py"
PT = "src/shibuya/engine/calendar3/port.py"
RO = "src/shibuya/engine/calendar3/roster.py"
KN = "src/shibuya/engine/calendar3/knowledge.py"
BLD = "src/shibuya/engine/systems/build.py"
SINCE = "2026-10-21"


def _row(id_: str, what: str, why: str, code_at: list[str], *, remove_at: str, basis: str = "inferred") -> dict:
    return {"id": id_, "what": what, "why": why, "remove_at": remove_at, "declared_in": DECL, "conf": "expedient",
            "since": SINCE, "status": "active", "remove_basis": basis, "code_at": code_at}


ROWS = [
    _row("DOC-ca3-scheduler-pick",
         "雇い主の口=組織(権利台帳の雇用の行 体 → 組織・外の雇用主の番号は除く・組織の行の無い体は店の担当の行の店)ごとのシフトを"
         "組む人=その単位の担当(台帳の行の順)のうち役割の語「店長」の体の最初の 1 人・居なければ最初の担当・ランの体の中で担当が"
         "働く人本人だけなら本人が組む(連絡は要らない=休みの申し出と遅れの連絡もしない)",
         "決定 10-12 §4-1 CA1「雇い主がエージェントになるまでのつなぎ」・§1-5 の 55 件の ②。雇い主のエージェント(店長の判断=GPU)は "
         "6-6 ②。5,000 体の抽出では単位の担当がランに居ないことが多い(本人が組む単位が多い=抽出の形)", [RO], remove_at="6-6",
         basis="plan"),
    _row("DOC-ca3-frame-form",
         "枠(雇い主の候補の素)=その人の W20 の勤務の日の (始業・終業・勤め先のセル・場所の種類) の重ならない組(その人の約束の形・"
         "W20 は週 0 の 1 週だけ=どの週も同じ形)。候補=休み+枠 1 つずつ・7 日を日ごとに選ぶ。正規雇用(W20 の毎週固定)は触らない",
         "CA1(勤務の時刻は W20=第 31/36 表の逆算のつなぎ)。枠の形と数を店の営業時間の区切りや人数から作るのは雇い主のエージェントの"
         "段(6-6 ②)=未リサーチ(expedient)", [RO, LY], remove_at="6-6", basis="plan"),
    _row("DOC-ca3-port-candidates",
         "カレンダー 3 の判断の候補の語と源の当て方(その日の枠・知らせ 10/30/60 分前と知らせない・休みを申し出る/申し出ない・休みたい"
         "日・受ける/断る・自分の行を休みにする/そのまま・遅れると連絡する/このまま)と仮のモデル(mock=候補を語と id の順に並べ乱数の"
         "余りで一様に選ぶ)。C3 の連絡の手段と宛先は C1 の宛先の判断(相手にメッセージ・相手に電話・職場のグループ)・文は C1 の文の口",
         "回答 2-1(GPU の前は仮のモデル)。数は振る舞いのモデルではない=判断モデル(6-1)と LLM で置き換える", [PT, LY],
         remove_at="6-1"),
    _row("DOC-ca3-compose-opportunity",
         "シフトを組む機会=週の境目の前の決まった刻み(〔検収 M1〕週の最後の平日=金曜の頭)に始まり、雇い主が起きていて主の判断の呼びの"
         "無い最初の刻み(範囲の外の体は寝ていなければ起きている)に翌週(次の月曜から)7 日を一度に組む(週が始まった後に組んだら数える)。"
         "試験用の印のランだけ、土日に始まるランの 0 日目の頭にも 1 回(金曜が来ない)。組んだシフトは雇い主の記録(_plan)に持つ。"
         "雇い主の口の表は最初の刻みの頭に作る(〔検収 H1〕再開では状態を戻して権利台帳を作り直した後=通しと同じ)",
         "発注「毎週 1 回(週の境目の前の決まった刻み=本人の判断の刻み)」・親の判断(問い 1=つなぎで受入・M1=金曜)。曜日と刻みは暦の口"
         "から(時刻の直書きなし)。いつ組むかを本人が決めるのは雇い主のエージェントの段(6-6 ②)=未リサーチ(expedient)", [LY],
         remove_at="6-6", basis="plan"),
    _row("DOC-ca3-labor-record-only",
         "労働時間の行(規則の表の human の行 labor.statutory_hours=週 40 時間・1 日 8 時間・labor.weekly_rest_day=毎週 1 回の休日)と店の"
         "営業時間(店の担当の行の店の W7 の営業の表=祝日は PH の行)は読むだけで止めない=超えた数・営業時間の外の枠の数を記録する"
         "(休憩は除かずに数える・36 協定と変形労働時間制は入れていない)",
         "CP3(法は止めずに記録)・規則の表の human の行=人が取り締まる側。人数の上限は規則が無い=空欄(記録だけ)", [LY],
         remove_at="7"),
    _row("DOC-ca3-store-closed-days-frame",
         "店の休業日は「店の決まり」として組織の口(StoreRules.closed_days)が知らせる=本段は枠だけ(中身は空)",
         "CA11「店の休業日は常連/検索/行って分かる人が知ります」。中身は店のエージェントと C4(店の検索)の段", [KN, LY],
         remove_at="6-6", basis="plan"),
    _row("DOC-ca3-trial-mark",
         "試験用の印(SHIBUYA_CALENDAR_3_TRIAL=on・腕 arm のときだけ)のランは開始日の検査の規則の違反(0 日目が月曜でない・祝日・"
         "連続する平日に収まらない)を止めずに manifest の calendar_3.trial に記録する(止める違反=祝日の表が読めない・範囲の外は今の"
         "まま)。日曜始まりの 2 日と祝日を含む日付のランはこの印で回した(分析に使わない)",
         "CA10「試験用(分析に使わない印)」・CA1「祝日を含むランは第 3 段まで回さない」(本段が第 3 段)。分析用の週末と祝日のランは"
         "第 1 段と来街者の来訪が判断モデルで動いてから(CA10)", [BLD], remove_at="6-2", basis="plan"),
    _row("DOC-ca3-weekend-k9",
         "日曜始まりのランの 0 日目は W17 の日曜の行が無い(K9=月曜の行だけ・0 日目は暦の曜日のまま)=体は全員が範囲の外で待つ(主の判断の"
         "呼び 0)。日曜 → 月曜の 2 日は 0 日目と 1 日目の計画境界の表が違う=活動層・方策 classical・想起優先の候補合成のあるランは"
         "日の頭の張り直し(K9 の外)で止まる=活動層を外して回した。0 日目は全員が寝ていない=試験用の印の 0 日目の組む機会は 0 時に"
         "寄る(計器 composed.hour_of_day)",
         "K9 (a)・A1-3。週末の行は W17 の作り直しか判断モデルの段(CA10)。本段のランは構造の確かめだけ(数は振る舞いのモデルではない)",
         [LY], remove_at="6-1"),
    _row("DOC-ca3-resend",
         "送れなかった C3 の連絡(寝ている・電源が無い・通話中・呼び出し中)は控え、次に考えた刻みに送り直す・電話がつながらなかったら"
         "MAX_SEND_TRIES=3 回まで控えに戻す・控えの中身は 7 日で落とす(有界)",
         "C1 の送る口の性質のつなぎ(expedient)。送り直すかは本人の判断=判断モデル(6-1)", [LY], remove_at="6-1"),
    _row("DOC-ca3-request-opportunity",
         "休みの申し出の機会=届いたシフトを書いた直後(同じ刻み)・遅れの連絡の機会=勤務の行の知らせ(本人が選んだ時刻)の後に考えた"
         "刻みで勤め先のセルに居ないとき・電話の申し出は同じ通話で返事を返す",
         "CA1「休むかどうかは本人の判断」・CT1 の C3(遅刻の職場への連絡)。機会の形は実装役の構成(expedient)=判断モデル(6-1)",
         [LY], remove_at="6-1"),
    _row("DOC-ca3-row-form",
         "働く人が書く勤務の行=カレンダー 2 の器(PromiseBook)の種類「勤務」・置き場所=アプリ・確かさ=確定・元の会話=その連絡"
         "(道具・会話の鍵・メッセージの番号か通話)・誰と=雇い主・何を=「勤務」。知らせの時刻だけ本人の判断",
         "発注(置き場所=アプリ・確かさ=確定・元の会話=その連絡)。置き場所と確かさを本人が選ぶのは判断モデルの段(6-1)", [LY],
         remove_at="6-1"),
    _row("DOC-ca3-rows-not-executed",
         "組んだシフトと勤務の行は本人の予定に書くだけで、出入り(勤務への出発と帰り)は今のまま(W17 の行・腕 1b は W20 の約束)=勤務の"
         "行はカレンダー 2 の見える予定と出発の判断と重なりの警告の外",
         "発注「本段はシフトを組んで知らせるだけ・他は触らない」。勤務の行を出入りの約束に結ぶのは 1b の既定化(6-2 の版上げ)と 6-6 ②",
         [LY], remove_at="6-2", basis="plan"),
    _row("DOC-ca3-not-default",
         "腕 --calendar-3 arm は既定にしない(C1 とカレンダー 2 の腕に束ねる=どちらも既定にしていない)",
         "CA9(段 3 の版上げは C3 と束ねる=実 LLM と雇い主のエージェントの後)・10-13b §0-6", [LY], remove_at="6-2",
         basis="plan"),
    _row("BR-CT1-CHARGE-AT-HOME",
         "連絡の道具 C1 の電池の充電=エンジン規則(腕 c1 のランだけ): 体が家に居る刻みは電池が CHARGE_PER_HOUR=0.5/時(満充電まで "
         "2 時間相当=仮の値)で増える・家に居る=住まいのセルに居る(範囲の中)か、住まいが範囲の外の体が範囲の外で寝ている刻み(住まいの"
         "場所が無い=宣言)・職場では増えない・電池が 0 でなくなった体は電源が入り、網が預かっていたメッセージを届ける(連絡:届いた)",
         "決定 10-12 §2 の 2「まだ人の行動で作れない変化はエンジン規則でつなぐ=conf 宣言つき」。充電は本人の行動(判断モデルの段 6-6)。"
         "C1 に充電が無いと 4 日を超える腕のランで全員の電池が 0 になり C3 の連絡が通らない(カレンダー 3 の検収の直しで見つけた)。"
         "速さと家の決め方は未リサーチ(expedient)",
         ["src/shibuya/engine/contact/device.py", "src/shibuya/engine/contact/layer.py",
          "src/shibuya/engine/contact/deliver.py"], remove_at="6-6"),
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
