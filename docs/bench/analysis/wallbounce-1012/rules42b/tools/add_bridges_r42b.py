"""第 4 期 4-2b 規則の表の空欄 3 件: つなぎの台帳(docs/design/bridging-ledger.json)を直す(何度でも同じ台帳)。

- 直す行(中身を今の文に置き換える=位置はそのまま): ``DOC-rules42-resident-tax-base``(控除は 2 つだけ → 基礎控除・調整控除・
  非課税を入れた)・``DOC-rules42-enrollment-basis``(年齢の上限の空欄の文を外す)・``DOC-rules42-rounding``(〔検収 低 4〕
  拠出金の端数を 1 文)。
- 外す行: ``DOC-rules42-employer-levy-missing``(status を removed に・why の末尾に外した印=4-2 の先例
  ``DOC-ec21-payroll-deduction-blank`` と同じ形)。
- 足す行(末尾): ``DOC-rules42b-*`` 4 行(旧道の切替口=next-bump・後期高齢者医療の空欄・非課税は未成年者だけ・住民税の端数)。
- 台帳の形(indent 1・ensure_ascii False・LF)は前のまま。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/rules42b/tools/add_bridges_r42b.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/wallbounce-1012/rules42b/README.md"
REC = "記録 docs/bench/analysis/wallbounce-1012/rules42b/README.md"
TX = "src/shibuya/economy/taxes.py"
ER = "src/shibuya/engine/economy_rules.py"
S2 = "src/shibuya/economy/stage2.py"
ES2 = "src/shibuya/engine/economy_stage2.py"
SINCE = "2026-10-22"


def _row(id_: str, what: str, why: str, code_at: list[str], *, remove_at: str, basis: str = "inferred") -> dict:
    return {"id": id_, "what": what, "why": why, "remove_at": remove_at, "declared_in": DECL, "conf": "expedient",
            "since": SINCE, "status": "active", "remove_basis": basis, "code_at": code_at}


ADD = [
    _row("DOC-rules42b-legacy-switch",
         "規則の表の空欄 3 件の腕 SHIBUYA_RULES_42B=off(engine/economy_rules.py・PayrollInputs.rules_42b)=4-2 の値の再現"
         "(住民税は給与所得控除と社会保険料控除だけ・厚年と健保の年齢の上限なし・子ども・子育て拠出金 0)のためだけの切替口",
         f"回答 10-13b §0-6(版上げで新しい道を既定にしたら古い道の切替口は次の版上げで消す・旧値の再現は安定版のタグで)({REC})",
         [ER, TX, S2, ES2], remove_at="next-bump", basis="plan"),
    _row("DOC-rules42b-late-elderly-medical-blank",
         "75 歳以上の体の後期高齢者医療の保険料は給料日に何も動かさない(健保・介護・支援金は年齢の上限で 0・後期高齢者医療の"
         "保険料の行は規則の表に無い)=空欄の宣言",
         "R-118 §10-2 で確かめたのは健保の 75 歳の上限(健保法 3 条 1 項ただし書 7 号・高確法 50 条 1 号)だけ。後期高齢者医療の"
         f"保険料(広域連合の料率と納め方)は一次の確認の外=給与から天引きしない(発注 4-2b の 1-2)({REC})",
         [TX], remove_at="7"),
    _row("DOC-rules42b-non-taxable-only-minor",
         "住民税の非課税(地方税法 295 条 1 項 2 号)の特別の 4 つのうち障害者・寡婦・ひとり親は材料が無い=入れていない。"
         "未成年者=今の年齢(母集団の年齢)が 18 歳未満(1 月 1 日の年齢ではない)だけ。扶養ありの限度の式(35 万円 × 人数+31 万円・"
         "42 万円)は扶養 0 の世界=読まない",
         "R-118 §10-2(都主税局の頁の 23 区の額)。体に障害・寡婦・ひとり親の属性が無い(DOC-rules42-dependents-zero と同じ"
         f"扶養 0)({REC})", [TX], remove_at="7"),
    _row("DOC-rules42b-resident-tax-rounding",
         "住民税の端数: 所得割の 100 円未満の切り捨て・都民税と区民税を分けて出す形・6 月分に端数を寄せる形は入れていない"
         "(年の額 ÷ 12 の 1 円未満の切り捨て・調整控除は都 2%+区 3% をまとめた 5% の 1 円未満の切り捨て)",
         f"端数の決まり(地方税法の端数計算と特別徴収の月割り)は一次の確認の外=発注 4-2b の 1-1 で本段の外と宣言({REC})",
         [TX], remove_at="7"),
]

FIX = {
    # 〔検収 低 4〕子ども・子育て拠出金の 1 円未満の切り捨て(expedient)を端数の行に 1 文
    "DOC-rules42-rounding": {
        "what": "端数: 雇用保険の本人の分も社会保険料と同じ 50 銭の決まり・雇用主の分=全額の 1 円未満の切り捨て − 本人の分"
                "(雇用保険の雇用主の分=額面 × 率の切り捨て)・住民税の月の額=年の額 ÷ 12 の切り捨て。〔第 4 期 4-2b〕子ども・"
                "子育て拠出金(事業主だけ)=厚年の標準報酬月額 × 率の 1 円未満の切り捨て(雇用主の分の既存の形・事業主の納付の"
                "端数の決まりは未確認)",
    },
    "DOC-rules42-resident-tax-base": {
        "what": "住民税の特別徴収の元の前年の収入=今の月の賃金 × 12(額面)。合計所得=前年の収入 − 給与所得控除(源泉の別表第一を"
                "月の額面に当てた額 × 12)。〔第 4 期 4-2b〕課税所得=合計所得 − 社会保険料控除(本人の社会保険料等の月の額 × 12)− "
                "基礎控除(規則の表 resident_tax.basic_deduction)・所得割=課税所得 × 10% − 調整控除(resident_tax.adjustment_"
                "credit_tokyo_ward)・非課税(resident_tax.non_taxable_tokyo_ward)を入れた。残る expedient は前年の所得=今の月の"
                "額面 × 12(前年の履歴が無い)と、都外に住む体にも東京都の特別区の率・均等割・控除・非課税の限度を当てること"
                "(端数は DOC-rules42b-resident-tax-rounding・扶養 0 は DOC-rules42-dependents-zero)",
        "why": "Q4=PENDING 仮-40(親の判断・仮採用)。体に前年の所得の履歴が無い(R-118 §5 ⑤)。控除と非課税の限度は R-118 §8 の "
               "12=未確認(記録 docs/bench/analysis/wallbounce-1012/rules42/README.md)〔検収 M1・親の判断〕今ある値で入れられる "
               "2 つの控除だけ入れた。基礎控除・調整控除・非課税の限度は一次の確認の後(記録 docs/bench/analysis/wallbounce-1012/"
               "rules42/README.md §11)〔第 4 期 4-2b〕基礎控除・調整控除・非課税の限度を R-118 §10-2 の親の一次確認の値で規則の"
               f"表に入れた=「控除は 2 つだけ=過大の方向」は外れた({REC})",
    },
    "DOC-rules42-enrollment-basis": {
        "what": "給与の天引きの加入の判定: 判定の材料(W21b の雇用の行の役割と週の時間の目安)が無い体のうち外の雇用主の体でない"
                "もの(W16 の残す体・時間の欄が空の行)は社会保険と雇用保険に未加入(源泉と住民税は天引き)・学生=体の種別 STUDENT "
                "だけ・業主と家族従業者と内職は雇われる側でない=天引きなし・役員と代表は時間で判定(雇用保険の役員の除外は入れて"
                "いない)・31 日以上の雇用の見込みは全員あり・雇用主の被保険者の数=W21b の組織ごとの週 30 時間以上の雇われる側の"
                "行の数。〔第 4 期 4-2b〕年齢の上限(厚年 70 歳・健保 75 歳)の年齢=母集団の年齢(誕生日の前日に資格を失う決まりと"
                "月の途中の扱いは入れていない・年齢 −1=不明は上限の内)",
        "why": "R-118 §2-3 の加入の範囲(4 分の 3・特定適用事業所 51 人以上・週 20 時間以上・学生でない)の材料がそろっていない分の"
               "宣言(発注 4-2 の 2)(記録 docs/bench/analysis/wallbounce-1012/rules42/README.md)〔第 4 期 4-2b〕年齢の上限は "
               "R-118 §10-2 の親の一次確認(厚年法 9 条=70 歳未満・健保法 3 条 1 項ただし書 7 号と高確法 50 条 1 号=75 歳未満)で"
               f"規則の表の欄 age_max_exclusive に入れた=空欄の宣言の文を外した({REC})",
    },
}

REMOVE = {
    "DOC-rules42-employer-levy-missing": (
        "〔第 4 期 4-2b・2026-10-22 外した=removed〕R-118 §10-2 の親の一次確認(子ども・子育て支援法施行令 27 条=千分の 3.6・"
        "日本年金機構の保険料額表の頁)で規則の表の行 child_care_contribution.rate を足し、天引きの雇用主の分に入れた"
        f"(economy/taxes.py・economy/stage2.py・{REC})"),
}


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = data["bridges"]
    pos = {r["id"]: i for i, r in enumerate(rows)}
    for rid, fields in FIX.items():
        rows[pos[rid]].update(fields)
    for rid, mark in REMOVE.items():
        r = rows[pos[rid]]
        r["status"] = "removed"
        if mark not in r["why"]:
            r["why"] = r["why"] + mark
    added = 0
    for r in ADD:
        if r["id"] in pos:
            rows[pos[r["id"]]] = r
            continue
        rows.append(r)
        added += 1
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    act = sum(1 for r in rows if r["status"] == "active")
    print(f"足した行 {added}・台帳 {len(rows)} 行(active {act})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
