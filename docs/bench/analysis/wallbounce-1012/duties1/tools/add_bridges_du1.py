"""第 6 期 6-6 ② 第 1 部: つなぎの台帳(docs/design/bridging-ledger.json)に本段の行を末尾に足し、店の仕事の 4 行の文を直す(何度でも)。

- 足す行: ``DOC-du1-*``(本段の仮採用・宣言は記録 duties1/README.md・status は active)。同じ id の行があれば、その位置のまま
  中身を今の文に置き換える(何度回しても同じ台帳)。〔検収の直し〕前の版の行で今は無い id(``DOC-du1-one-staff-per-store``)は
  台帳から消す(未 commit の段の行=消してよい)。
- 直す行: ``PR-store_opening``・``FB-store_opening``・``PR-shelf_stock_restock``・``PR-waste_collection`` の ``why`` の末尾に
  「腕 arm では雇用の行の体が居る店で本人の行動に置き換わる(割合)・既定 off では今のまま」の 1 文を足す(``what``・外す段・状態は
  変えない=外すのは既定化のとき)。
- 〔検収 L8〕割合は引数で渡す(``開閉 補充 廃棄`` の 3 つ・記録 §5 の 5,000 体 1 日の値)。渡さなければ台帳の今の文を保つ(前に
  足した文があればそのまま=冪等・無ければ「未計測」)。
- 台帳の形(indent 1・ensure_ascii False・LF)は前のまま。足すのは末尾だけ(並行の作業木との取り込みで当たりを小さく)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/duties1/tools/add_bridges_du1.py [開閉の率 補充の率 廃棄の率]``
(記録の値の再現: 記録 §8 に書いた 3 つの文を渡す)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/wallbounce-1012/duties1/README.md"
LY = "src/shibuya/engine/duties/layer.py"
PT = "src/shibuya/engine/duties/port.py"
KN = "src/shibuya/engine/duties/knowledge.py"
OP = "src/shibuya/engine/processes/opening.py"
GF = "src/shibuya/engine/processes/goods_flow.py"
BR = "src/shibuya/engine/llm_bridge.py"
BLD = "src/shibuya/engine/systems/build.py"
AS = "src/shibuya/world/assets.py"
SINCE = "2026-10-22"
MARK = "〔6-6 ② 第 1 部〕"
REMOVED_IDS = ("DOC-du1-one-staff-per-store",)


def _row(id_: str, what: str, why: str, code_at: list[str], *, remove_at: str, basis: str = "inferred") -> dict:
    return {"id": id_, "what": what, "why": why, "remove_at": remove_at, "declared_in": DECL, "conf": "expedient",
            "since": SINCE, "status": "active", "remove_basis": basis, "code_at": code_at}


ROWS = [
    _row("DOC-du1-port-candidates",
         "店の仕事の判断の候補の語と源の当て方(開閉=店を開ける/店を閉める/まだ・補充=棚に補充する/接客する/待つ・廃棄=売れ残りを"
         "捨てる/まだ。語は語彙 v3 の役割語 開閉店・補充・接客と安全弁の語 なし+本段の語 廃棄)と仮のモデル(mock=候補を語と id の順に"
         "並べ乱数の余りで一様に選ぶ)",
         "回答 2-1(GPU の前は仮のモデル)。数は振る舞いのモデルではない(開店の遅れ・補充の数は mock の一様な選びで偏る)=判断モデル"
         "(6-1)と LLM で置き換える", [PT, LY], remove_at="6-1"),
    _row("DOC-du1-shop-window",
         "開閉の候補を出す条件=雇用の行の体が店のセルに居て起きていて主の判断の呼びが無い刻みに、店の決まり(営業時間)で "
         "SHOP_LEAD_MINUTES=15 分後に営業なのに閉まっている/15 分後に休みなのに開いている(区切りの 15 分前から食い違う間ずっと)。"
         "〔検収 L6〕先読みが夜中をまたぐと次の日の曜日の行ではなく今日の行列を巻き戻して読む(開閉の過程のつなぎも今日の行列=食い違い"
         "は無い)",
         "発注「候補の口が出す条件=店の決まりの時刻の前後=宣言・時刻を直書きしない」。幅 15 分は実装役の値=未リサーチ(expedient)。"
         "いつ開け閉めを考えるかを本人が決めるのは判断モデルの段(6-6 第 2 部以降)", [LY, KN], remove_at="6-6"),
    _row("DOC-du1-store-rules",
         "店の決まり(営業時間)=W7 の営業時間の表のその日の行(開閉の過程の行列・申込書の決定 L1 を含む)を、その店の雇用の行(体 → 店)"
         "の体だけが店の決まりの口(ShopRules=カレンダー 3 の StoreRules の子)で引ける。〔検収 M3〕答えに出どころの印(W7 の列 src="
         "osm_opening_hours=実データ/chain_default・category_default=構築側の既定=作り物の印・記録の origin=store_rules:<出どころ>)を"
         "付け、計器を出どころで分ける(既定の行の店も答える)。組織の雇用の行から店を引く口は無い・W7 に行の無い店と合成の世界は決まりが"
         "無い(候補を出さない)",
         "決定 10-12 §1-4(人の手続きは住人の知識から)・CA11(店の決まりは組織の口が知らせる)・§1-5 の 6(作り物の印)。組織 → 店の"
         "対応と店の決まりの知らせ方(掲示・研修・店長の指示)は店のエージェントの段(6-6 第 2 部以降)", [KN, LY, AS], remove_at="6-6",
         basis="plan"),
    _row("DOC-du1-shelf-notice",
         "棚の知覚=店の中の気づき(System 1 の刺激・知覚の事実 Percept の形と版は変えない): 雇用の行の体が店に居て、棚の残りが補充点"
         "(ShelfRestockProcess.reorder_point=容量の 95%)の下・営業中・〔検収 M2〕バックヤードに在庫がある(本人は在庫を知っている="
         "空なら候補を出さない・出さなかった数を計器に)で、補充の評価の刻み(5 分)ごとに候補を出す。補充の量と代金の原因(過程 shelf)は"
         "今の役割行動と同じ",
         "発注「知覚の事実の既存の欄に棚の残りの段を入れる・無理なら店の中の気づきとして System 1 の刺激=宣言」。Percept に棚の段を"
         "入れると描画と本文が変わる=本段は気づきの形にした。補充点と刻みは今の補充の過程の expedient の写し", [LY, GF],
         remove_at="6-6"),
    _row("DOC-du1-unstaffed-bridge",
         "その店の雇用の行を持つ体が店のセルに居て起きていない店(雇用の行の無い店・体が別の場所に居る店・体が店で寝ている店)は今の "
         "conf 宣言つきのつなぎのまま=開閉は OpeningProcess の REPLACEMENT(conf 0.5)・補充は 10:00 の engine_rule・売れ残りは 05:00 に"
         "棚 → ビン(雇用の行の体が閉店の作業で捨てた店は除く)。開始の刻みの最初の設定(open_now が負の店)もエンジン(担当の役割行動と"
         "して代打しない)。〔検収 M4〕補充と開閉の「居る」は同じ判定(種別を見ない)",
         "決定 10-12 §2 の 2(まだ人の行動で作れない変化はエンジン規則でつなぐ=conf 宣言つき・カバー率を台帳へ)。カバー率は manifest の "
         "duties.coverage(雇用の行の出どころ別・店の決まりの出どころ別)と記録 §5", [OP, GF, LY], remove_at="6-6", basis="plan"),
    _row("DOC-du1-employment-candidates",
         "〔検収 M1〕店の仕事の候補を出す体=その店の雇用の行(権利台帳の 体 → 店)を持つ体なら誰でも(店のセルに居て起きていて主の判断の"
         "呼びが無い)。1 店 1 刻みの判断は雇用の行の順で最初の 1 人。カバー率は行動した体の雇用の行の出どころ(W21c の担当/丸振り)で"
         "分ける(つなぎは店の担当の表の体の出どころ)。丸振り(1 人の従業者が多くの店)の偏りは母集団の側の行 "
         "DOC-pop43-store-round-robin-kept に残す",
         "親の判断(問い 1)。W21 の 5,000 体では最初の雇用の行の出どころが W21c 68 店/丸振り 2,269 店・雇用の行が 2 行以上の店は 29。"
         "シフトの担当(カレンダー 3 の勤務の行)と結ぶのは 6-6 第 2 部以降", [LY, OP, GF], remove_at="6-6"),
    _row("DOC-du1-no-cleanup",
         "閉店の作業は売れ残りの廃棄だけ(閉店の後の片付け・清掃・レジ締めは無い)。廃棄の候補は雇用の行の体が閉めた店に売れ残り"
         "(棚 × SKU の廃棄率の切り捨て)があるとき・前の 05:00 から 1 回",
         "発注「閉店の後の片付けは本段に無い=宣言」。収集(06:00〜10:00 の清掃作業員)は第 2 部", [LY, GF], remove_at="6-6",
         basis="plan"),
    _row("DOC-du1-labor-record-only",
         "労働時間の行(規則の表の human の行 labor.statutory_hours=1 日 8 時間)と店の決まりの外の開け閉め(〔検収 L2〕幅の中で早め/"
         "幅の外=決まりの時間中に閉めた・決まりの外に開けた、を分ける)は読むだけで止めない=数えるだけ。働いた時間=雇用の行の店の"
         "セルに起きて居た分(〔検収 L3〕店で寝ている刻みは数えない・休憩・ほかの勤め先は数えない)",
         "CP3(法は止めずに記録)・rules42 の形。勤務の時間をカレンダー 3 の勤務の行から数えるのは 6-6 第 2 部以降", [LY],
         remove_at="7"),
    _row("DOC-du1-role-word-path",
         "主の判断の役割語「補充」「開閉店」(LLMBridge.role_sink=腕 arm のランだけ)は、その体が雇用の行を持つ店のセルに居れば同じ刻みに"
         "本人の行動として実行する(開閉店=今の状態の逆・原因=主の判断の call_id)。〔検収 L7〕補充は気づきと同じ条件(営業中・棚が"
         "補充点の下)のときだけ(ほかは数えるだけ)。体の行為は安全弁の語(なし)のまま=店の中の作業。ほかの役割語(接客・価格改定など)は"
         "数えるだけ。仮のモデルの主の判断は役割語を出さない(実 LLM の段で効く)",
         "発注「役割語「補充」を効くように=llm_bridge の「待機」落ちを腕のときだけ外す」。行為の適用の表(_APPLY)に役割語の分岐は"
         "無い=効果は店の仕事の持ち主が引き受けた(体の行為の語は変えない)", [BR, LY], remove_at="6-1"),
    _row("DOC-du1-not-default",
         "店の仕事の腕(--duties arm)は既定にしない=既定のランは今の世界過程のつなぎ(開閉・補充・廃棄をエンジンが代わりにする)の"
         "まま。PR-store_opening・FB-store_opening・PR-shelf_stock_restock・PR-waste_collection の行は既定化のときに外す",
         "回答 2-1(GPU の前は腕で構造だけ)。既定化は判断モデル(6-1)の後の版上げ", [BLD, LY], remove_at="6-6", basis="plan"),
]

EDIT_IDS = ("PR-store_opening", "FB-store_opening", "PR-shelf_stock_restock", "PR-waste_collection")


def _edit_text(rid: str, rates: dict[str, str]) -> str:
    key = {"PR-store_opening": "shop", "FB-store_opening": "shop", "PR-shelf_stock_restock": "shelf",
           "PR-waste_collection": "waste"}[rid]
    what = {"shop": "開閉", "shelf": "補充", "waste": "売れ残りの廃棄"}[key]
    return (f"{MARK}腕 --duties arm では雇用の行の体が居て起きている店で{what}が本人の行動に置き換わる(本人の行動の割合 "
            f"{rates[key]}=記録 {DECL} §5 の 5,000 体 1 日)・既定 off では今のまま(外すのは既定化のとき=DOC-du1-not-default)")


def main(argv: list[str]) -> int:
    rates = dict(zip(("shop", "shelf", "waste"), argv)) if len(argv) == 3 else None
    raw = LEDGER.read_text(encoding="utf-8")
    d = json.loads(raw)
    rows = [r for r in d["bridges"] if r["id"] not in REMOVED_IDS]
    d["bridges"] = rows
    idx = {r["id"]: i for i, r in enumerate(rows)}
    for new in ROWS:  # 逐次: 本段の行の数
        if new["id"] in idx:
            rows[idx[new["id"]]] = new
        else:
            rows.append(new)
    for rid in EDIT_IDS:  # 逐次: 4
        r = rows[idx[rid]]
        why = str(r["why"])
        if rates is None and MARK in why:  # 〔検収 L8〕割合を渡さなければ前の文を保つ
            continue
        if MARK in why:
            why = why[: why.index(MARK)].rstrip("。")
        r["why"] = why.rstrip("。") + "。" + _edit_text(rid, rates or {"shop": "未計測", "shelf": "未計測",
                                                                       "waste": "未計測"})
    LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"台帳 {len(rows)} 行(active {sum(1 for r in rows if r['status'] == 'active')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
