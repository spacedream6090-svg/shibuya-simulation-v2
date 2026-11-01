"""第 6 期 6-4 C2 のつなぎの台帳の行を足す・外す(冪等=何度回しても同じ・取り込みの 3 方向の合わせに使う)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/ct_c2/tools/add_bridges_ct_c2.py [台帳の道筋]``(既定
``docs/design/bridging-ledger.json``)。

- 外す行(``REMOVED``): ``status`` を ``removed`` にし、``why`` の末尾に注を足す(もう同じ注があれば何もしない)。
- 足す行(``ROWS``=12 行): 台帳の末尾に足す(同じ id の行があれば中身を置き換える=冪等)。
- 書き方は台帳の今の形(``json.dumps(indent=1, ensure_ascii=False)``+改行・LF)。土台 ``6115860`` の台帳に回すと、作業木の台帳と
  1 バイト同じになる(記録 ct_c2/README.md §8)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REMOVED = json.loads(r'''{
 "DOC-ct-c1-book-scope": {
  "status": "removed",
  "why_suffix": "〔第 6 期 6-4 C2・2026-10-22=removed〕連絡先の交換・グループ・店の番号を調べるは本人の行動になった(DOC-ct-c2-exchange・DOC-ct-c2-groups・DOC-ct-c2-store-number)。宛先の出どころの範囲(関係の層の印・人も記憶の腕・関係の層の無いランは家族)は今のまま=DOC-ct-c2-exchange に注"
 },
 "DOC-ct-c1-habit": {
  "status": "removed",
  "why_suffix": "〔第 6 期 6-4 C2・2026-10-22=removed〕CT4 の習慣を腕 SHIBUYA_CONTACT_HABIT(既定 off=判断の口だけ)で作った(DOC-ct-c2-habit・DOC-ct-c2-habit-scope)"
 },
 "BR-CT1-CHARGE-AT-HOME": {
  "status": "removed",
  "why_suffix": "〔第 6 期 6-4 C2・2026-10-22=removed〕充電は本人の行動になった(道具の知らせ → 家で本人が充電する/やめるを選ぶ・差した体だけ物理で増える=記録 docs/bench/analysis/wallbounce-1012/ct_c2/README.md)。値 0.5/時は物理の値として DOC-ct-c2-charge-rate に移した"
 }
}''')
ROWS = json.loads(r'''[
 {
  "id": "DOC-ct-c2-charger-at-home",
  "what": "充電器は家にある=全員 1 台(持ち物の実データが無い)・家=住まいのセルに居る(範囲の中)か、住まいが範囲の外の体が範囲の外に居る刻み(範囲の外の活動は作っていない=「寝ている」が立たないのでカレンダー 3 の「範囲の外で寝ている刻み」は空振りだった=親の判断 2026-10-23)・職場や範囲の中の外出先では充電できない",
  "why": "CT0 の共通の決まり 2(持ち物は初めは実データ=母集団の側)。持ち物の台帳の実データが無い。境界の層(外の人の活動)ができたら範囲の外での家と外出先を分けて外す(外す段=7=主の前の感度試験の一覧)。充電する/やめるは本人の判断のまま=範囲の外に居る刻みを全部家とする当てはめで充電が過大に出る向きは判断の呼びで抑える",
  "remove_at": "7",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/device.py",
   "src/shibuya/engine/contact/layer.py"
  ]
 },
 {
  "id": "DOC-ct-c2-charge-rate",
  "what": "充電の物理の値=差した体の電池は 50%/時で増える(満充電まで 2 時間相当=つなぎ BR-CT1-CHARGE-AT-HOME の値をそのまま)・差している間は減らない・電池が戻れば電源が入る",
  "why": "CT0(途中は本人の行動と物理で動く)。速さの実データは未リサーチ(expedient)=結果を駆動していないことは主張の前に感度試験で",
  "remove_at": "7",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/device.py"
  ]
 },
 {
  "id": "DOC-ct-c2-charge-opportunity",
  "what": "充電の判断の機会=家で(a)道具の「電池が少ない」の知らせ(20%・10% を下に越えた刻み)に気づいた刻み(b)電池が少ないと知っていて家に着いた・起きた・寝た刻み(c)〔検収 L6〕家に居て電池が閾値の下の体がその刻みに主の判断か連絡の判断をしたとき(判断のたびに候補を出す=発注の「家にいて充電器がある刻み」)/充電をやめる=満充電の知らせに気づいた刻み・主の判断が先(次の刻みに回す)・電源が切れたら本人は知る・画面を見ている体は電池の表示を見る・家を離れたら抜ける(物理)",
  "why": "CT0 の共通の決まり 2・3・CT3(通知は System 1 の刺激)。人の手続き(寝る前に充電する等)はコードに書かず本人の判断に置き、機会の当て方だけを宣言した=判断モデルの段で見直す",
  "remove_at": "6-1",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/layer.py",
   "src/shibuya/engine/contact/device.py"
  ]
 },
 {
  "id": "DOC-ct-c2-habit",
  "what": "CT4 の習慣の値と範囲=習慣で答えるのは範囲の外に居る体(セル −1)だけ・範囲の中の体はいつも判断の口(選びは数える)・閾値 5 回(その体のその状態のその判断の選びの数)・ときどき判断の口へ戻す割合 0.1(乱数の用途名 contact.habit)・答え=いちばん多く選んだ語(同数は並びの先・確率で引かない)・習慣で答えた語も数える(強まる形)・状態=移動中 → 家 → 勤務中 → ほか の順に当てる・習慣の答えの原因=判断の種類 14/15 の呼びの id(源=経験・呼び数に数えない)",
  "why": "CT4(習慣で決めてかまわない・記録が少ないうち/大事な誘い/驚きは判断モデルへ・状態ごと・ときどき戻す)・10-03 §7-3 4-1 (a)。値は未リサーチ(expedient)",
  "remove_at": "6-1",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "plan",
  "code_at": [
   "src/shibuya/engine/contact/layer.py",
   "src/shibuya/engine/contact/habit.py"
  ]
 },
 {
  "id": "DOC-ct-c2-habit-scope",
  "what": "習慣の範囲=範囲の外に居る体(セル −1)だけ(親の判断 2026-10-23=CT4 の見出しのとおり)・驚き=起床条件 (i)(範囲の外の体には来ない=実際には戻す条件は記録が少ない・大事な誘い・ときどきの 3 つ)・大事な誘い=カレンダー 2 の返事待ちの誘い(腕 calendar-2 のランだけ)",
  "why": "CT4(範囲の外にいる人は本人が返す・習慣で決めてかまわない)・10-03 §7-3 の注。境界の層(外の人の活動)ができたら範囲の外の体の驚きの入口と状態を作り直して外す(外す段=7)",
  "remove_at": "7",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/layer.py"
  ]
 },
 {
  "id": "DOC-ct-c2-exchange",
  "what": "連絡先の交換の機会=対面の会話の自分の最初の番(会話の番の控え note_face_turn)・持ちかける/応じるは本人の判断(仮のモデルは一様)・交換で足す印はメッセージだけ・両方の電源が入り起きているとき・印は連絡の層の帳(ContactBook._exchanged=関係の層の辺の欄の外の相手も持てる)・交換の頻度は空欄(計器だけ)・〔検収 L2〕主の判断が先(持ちかける/応じるをその刻みに主の判断の呼びのあった体は次の刻みに回す)",
  "why": "CT5((c) 個人の連絡先は関係の記憶に手段ごとの印・交換は本人の行動・頻度は空欄で計器だけ)。関係の層の欄に書くのは §4-6 の段",
  "remove_at": "6-1",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/layer.py",
   "src/shibuya/engine/contact/book.py",
   "src/shibuya/engine/systems/llm_io.py"
  ]
 },
 {
  "id": "DOC-ct-c2-groups",
  "what": "友人のグループ=候補の口(画面の判断の「グループを作る/招く/抜ける」・作るは連絡先から 1 人を招く)・招待は招かれた体が画面を見たときに古い順に 1 つ答える(通知の刺激は無い)・〔検収 L7〕抜けて成員が 0 人になったグループは無くなる(招待も消える)・家族と職場は実データのまま(抜けない・招かない)",
  "why": "CT5(友人は慣らし期間で本人たちが作る)。慣らし期間は本段の外=候補の口だけ",
  "remove_at": "6-1",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/layer.py",
   "src/shibuya/engine/contact/book.py"
  ]
 },
 {
  "id": "DOC-ct-c2-store-number",
  "what": "店の番号=場所の表(W6 の POI の欄=engine.tools.places.PhoneTable)が空欄の間は「店の番号を調べる」の候補が出ない(調べた数 0)・店に電話をかける口は無い(店のエージェントの後)",
  "why": "CT5(店や組織の番号は場所の表の側・調べる/保存するは本人の行動)。表の中身は BR-PHONE-TABLE-BLANK(OSM の phone タグ)",
  "remove_at": "6-6",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/layer.py",
   "src/shibuya/engine/contact/book.py"
  ]
 },
 {
  "id": "DOC-ct-c2-video",
  "what": "ビデオ通話の電池の減り 20%/時(通話より大きい=仮の値)・宛先=電話の連絡先と同じ・終わった後は画面を見たまま(顔を上げるのは本人)・知覚の事実は tool_state の call_via(Percept の形と版は変えない)",
  "why": "CT1 の C2(電話の器の種類違い)。値は未リサーチ(expedient)",
  "remove_at": "7",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/layer.py",
   "src/shibuya/engine/contact/device.py",
   "src/shibuya/engine/contact/calls.py"
  ]
 },
 {
  "id": "DOC-ct-c2-receipts",
  "what": "既読の印を送った側の画面の判断の候補(「画面を見続ける」)の文に載せる=送ったメッセージの通数・既読の延べ/届け先の延べ(驚き=予想とのずれは判断の側)",
  "why": "CT2(既読は道具の性質・送った側の予想とのずれ=驚き)・C1 の記録の限界。載せ方の形は実装役の構成",
  "remove_at": "6-1",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/layer.py",
   "src/shibuya/engine/contact/deliver.py"
  ]
 },
 {
  "id": "DOC-ct-c2-tool-rows",
  "what": "道具の台帳の行(メッセージ・ビデオ通話・充電器・店の番号を調べる・郵便・置き手紙)は腕 c1 のランの台帳だけに足す(既定のランの台帳と manifest の tools は今のまま)・各欄の値は実装役が当てた",
  "why": "CT0(道具は台帳に 1 行ずつ足す)・C1 の記録の限界(メッセージの道具の行が無い)。既定に入れるのは腕 c1 の版上げのとき",
  "remove_at": "6-6",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/tools.py",
   "src/shibuya/engine/systems/build.py"
  ]
 },
 {
  "id": "DOC-ct-c2-c6-letter",
  "what": "C6 手紙ほか=郵便・置き手紙は道具の台帳の行だけ(実体は物=第 5 期 段 2・配達=6-6 ②の後)",
  "why": "CT1(C6 手紙ほか)。発注=本段は行だけ",
  "remove_at": "5-2",
  "declared_in": "docs/bench/analysis/wallbounce-1012/ct_c2/README.md",
  "conf": "expedient",
  "since": "2026-10-22",
  "status": "active",
  "remove_basis": "inferred",
  "code_at": [
   "src/shibuya/engine/contact/tools.py"
  ]
 }
]''')


def apply(doc: dict) -> dict:
    by = {x["id"]: x for x in doc["bridges"]}
    for rid, ch in REMOVED.items():  # 逐次: 外す行の数ぶん
        x = by[rid]
        x["status"] = ch["status"]
        if not x["why"].endswith(ch["why_suffix"]):
            x["why"] = x["why"] + ch["why_suffix"]
    for row in ROWS:  # 逐次: 足す行の数ぶん
        if row["id"] in by:
            by[row["id"]].clear()
            by[row["id"]].update(row)
        else:
            doc["bridges"].append(dict(row))
    return doc


def main(argv: list[str]) -> int:
    path = Path(argv[0] if argv else "docs/design/bridging-ledger.json")
    doc = apply(json.loads(path.read_text(encoding="utf-8")))
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(doc["bridges"]), sum(1 for x in doc["bridges"] if x["status"] == "active"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
