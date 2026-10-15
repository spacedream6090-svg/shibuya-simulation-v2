"""第 6 期 6-5: つなぎの台帳(docs/design/bridging-ledger.json)の末尾に 6-5 の行を足す(同じ id があれば足さない=何度でも)。

〔検収 L7〕id の段の名は回答 10-12 の 6-2 の表の名(M1=想起の式と統合=人も記憶の一つを含む・M2=手がかり・M3=印象・
M4=個人差・M5=同席と浅い痕跡)。発注の名(M4=思い浮かぶ/見覚え・M5=人も記憶)は why に書く。〔検収 M1・M2・M4〕の行
(``-m4-rate-variation`` の seed・``-m1-row-caps``・``-m1-shop-uncapped``)を直した/足した。``--replace`` は台帳の本段の
行(``DOC-mr65-*``)を ROWS で置き換える(並びは本段の行の最初の位置から・ほかの行は変えない)。

使い方(リポの根で): ``python docs/bench/analysis/wallbounce-1012/mr65/tools/add_bridges_mr65.py``
台帳の形(indent 1・ensure_ascii False・LF)は前のまま。足すのは末尾だけ(並行の作業木との取り込みで当たりを小さく)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/wallbounce-1012/mr65/README.md"
BUILD = "src/shibuya/engine/systems/build.py"
SHOPS = "src/shibuya/engine/memory_shops.py"
SM = "src/shibuya/engine/store_memory.py"
SC = "src/shibuya/engine/store_choice.py"
SINCE = "2026-10-15"
M1 = "src/shibuya/engine/memory_m1.py"
MS = "src/shibuya/engine/memory_store.py"
ME = "src/shibuya/engine/memory_embed.py"
MM = "src/shibuya/engine/memory.py"
RP = "src/shibuya/engine/relations_people.py"
MT = "src/shibuya/engine/memory_trace.py"
MI = "src/shibuya/engine/memory_impression.py"


def _row(id_: str, what: str, why: str, code_at: list[str], *, remove_at: str = "6-5", basis: str = "plan") -> dict:
    return {"id": id_, "what": what, "why": why, "remove_at": remove_at, "declared_in": DECL, "conf": "expedient",
            "since": SINCE, "status": "active", "remove_basis": basis, "code_at": code_at}


ROWS = [
    _row("DOC-mr65-m1-k-recent",
         "M1 の折衷形で本当の時刻を持つ直近の回数 k=3(K_RECENT)",
         "決定 10-12 §4-6 MR1 (b)「直近の数回は本当の時刻・古い分は近似」。回数の錨は無い(R-87 §1-3 の例 k=3)=expedient。"
         "MR10=腕で測ってから 6-5 の終わりにまとめて既定にする段で感度の腕(1/3/5)を回す", [M1, MS]),
    _row("DOC-mr65-m1-t-min",
         "M1 の最短の符号化時間 1 秒(T_MIN_S・t=0 を避ける下の切り)",
         "決定 10-12 §4-6 MR1「t が 0 にならないよう最短の符号化時間を置く」。値の錨は無い=expedient・感度の腕 0.05/1/60 秒",
         [M1]),
    _row("DOC-mr65-m1-tau-provisional",
         "M1 の境目 τ の仮の値=−3.738(M0 の τ −2.0 で n=1 の行が下回る時刻と、M1 で n=1・初めての成功の行が下回る時刻を"
         "同じにする値=tau_from_m0)",
         "決定 10-12 §4-6 MR1「境目 τ は現実のデータで較正(expedient)」。人の記憶のデータは検証側(パターン台帳 §10・MR9)="
         "本段では較正しない=仮の値を宣言。較正の手順と相手は親とユーザーの判断(6-5 の既定化の前)", [M1, MS, MM]),
    _row("DOC-mr65-m1-kind-table",
         "種類ごとの忘れる速さと足す項(出来事 d=0.5+0.5×重要度・人 d=0.5+0・印象 d=0.5+0・見覚え d=0.35・はっきりの幅 1.0)",
         "決定 10-12 §4-6 MR1 (d)・MR12 (a)(形は研究に合わせ値は expedient の腕)。出来事の足す項の重み 0.5 は M0 の score の"
         "w_i と同じ値・見覚えの d は「親しみは遅い」の形だけ(値の錨は無い)", [M1]),
    _row("DOC-mr65-m1-recognition",
         "見覚えの手がかりの重み W_CUE=1.0・忘れる(消す)の幅 FORGET_MARGIN=1.0(1 回だけ会った人は思い浮かぶ約 29 分・"
         "見覚え約 9 日・消えるまで約 5 か月=倍率 1)",
         "決定 10-12 §4-6 MR4・人も記憶の一つ(見覚え=目の前の手がかりを足すと超える・十分下がったら消す)。値の錨は無い="
         "expedient。確かめは Roberts & Dunbar の向き・R-69・Dunbar の層・Milgram(検証側=値を構築に使わない)。段の名: "
         "発注の M4(思い浮かぶ/見覚え)=回答 10-12 の 6-2 の M1(想起の式と統合)", [M1, MS, RP]),
    _row("DOC-mr65-m4-rate-variation",
         "忘れる速さの人ごとの倍率 1+0.15·z(z は Philox の標準正規・±3σ で切る・鍵=体の番号・seed=ランの母集団の seed="
         "組み立てが enable_memory_store に渡す)",
         "決定 10-12 §4-6 MR8(Sense 2018 の 15%=錨)・回答 10-12 の 6-2 の M4(個人差)。切り ±3σ と鍵を体の番号にする形"
         "(母集団の元 id は器に届かない)は expedient。〔検収 M1〕seed はプロセスの大域の値(cli が置く)をやめ、ランごとに"
         "組み立てが母集団の seed を渡す(10f S1)", [M1, MM, BUILD]),
    _row("DOC-mr65-m2-embed",
         "意味の手がかりの重み W_CTX=1.0・一致の境目 cos≥0.5・Ruri の接頭辞(検索クエリ/検索文書=モデルカードで確かめる前)・"
         "埋め込みを float16 に丸める・試験用の代わり ngram-test・版の固定(30m 24899e5d・130m e3114c6e)",
         "決定 10-12 §4-6 MR2。重みは本段で取得していない(転送先 us.aws.cdn.hf.co が許可の一覧の外)=Ruri の道は未試験。"
         "W_CTX の感度の腕 {0, 0.5, 1, 2}(R-87 §4-1)", [ME, MS, MM]),
    _row("DOC-mr65-m2-cue-text",
         "手がかりの文: 会話の番の発言(ひと言)と理由だけが口に来る(判断の呼の理由・予定の文は口へ結線していない)",
         "決定 10-12 §4-6 MR2 問い 4。判断の系(llm_io・judge)から本人の直前の理由を渡す結線は本段の範囲の外(系は触らない)="
         "語彙 v3 はひと言が無い=会話中も本人の理由に戻る", [MM, ME], basis="inferred"),
    _row("DOC-mr65-m1-people-initial",
         "人も記憶の腕の最初の関係=今の関係の層の機械的初期化の辺(W16 の世帯・W17 の共在)を開始前の経験として人の行へ",
         "決定 10-12 §4-6「最初の関係はデータから開始前の経験として入れる」。4-1 段 4 の w21_relations_initial が本体に無い間の"
         "つなぎ(初期辺の上限 15=Q111 は入れる側の引数のまま)。段の名: 発注の M5(人も記憶)=回答 10-12 の 6-2 の M1"
         "(人と店と出来事を同じ器に)", [RP, MS], remove_at="4-1", basis="inferred"),
    _row("DOC-mr65-m1-people-limits",
         "人も記憶の腕は知人出現の起床・同席の腕を作らない(要求は計器に数える)・連絡先の印の配列を持たない・人の行の目印は"
         "仮の行・好意の符号は 0・再開に対応しない(器が記憶の表の写しでない)",
         "回答 10-12 の 6-2(M5 は目の向きと空間の段が先)・MR6(注意が向いたときを 1 回=口 note_attended だけ)。器(腕)の段の"
         "限界。段の名: 発注の M5(人も記憶)=6-2 の M1・同席(注意を向けたときに 1 回)は 6-2 の M5", [RP, MM, MS],
         basis="inferred"),
    _row("DOC-mr65-grain-day",
         "体の出来事の粒度の腕 day(同じ記憶の行は日に 1 行だけ記録へ・目印は日の最初の回・再開に対応しない)",
         "第 2 期 2-3 の DOC-md23-body-events-volume(14.6 行/体/日・39 万体 7 日で約 4 GB)を 6-5 で決め直す案の 1 つ(腕)。"
         "既定にするかは 6-5 の既定化で親とユーザーが決める", [MM, MS]),
    _row("DOC-mr65-render-words",
         "言葉(うろ覚え)と粗さ(要旨だけ)を項の頭の印「(うろ覚え)」「(要旨だけ)」で描く口(render_memories(words=True))=今の"
         "描画には結線していない", "決定 10-12 §4-6 MR-0。表記は未リサーチ。描画(perception/renderer.py)の 1 か所の結線と"
         "テンプレの版は親の判断", [MS], basis="inferred"),
    _row("DOC-mr65-m5-trace-window",
         "浅い痕跡の「視野のどこに・どれだけ」を「同じ場所(where)で 1 刻み以内」で近似(目の向きは空間の段の後)・話し手の指した"
         "相手の見えない欄 Percept.heard_referents は空(値を作る口は会話と空間の段の後)",
         "決定 10-12 §4-6(注意を向けずに見ていた人)・回答 10-12 の 6-2 の M5(同席と浅い痕跡・GPU 要・目の向きと空間の段が"
         "先)=口だけ",
         [MT, "src/shibuya/perception/facts.py"], remove_at="5-2", basis="inferred"),
    _row("DOC-mr65-m1-shop-scale",
         "M1 の腕で店の評価の行(器の外=今の sm_* と今の式)を出来事と同じ順に並べるとき、店の行の score を境目の差"
         "(M1 の τ − 今の τ)だけずらす",
         "決定 10-12 §4-6(人と店と出来事を同じ器に入れ上限をなくす=回答 10-12 の 6-2 の M1)。店の行の強さは M1 の式でなく"
         "店の記憶の式のまま(腕 memory の器の店の行の表=DOC-mr65-m1-shop-uncapped も同じ式)=尺度をそろえるだけの仮採用",
         [MS], basis="inferred"),
    _row("DOC-mr65-m1-row-caps",
         "上限なしの腕(人も記憶の一つ)の種類ごとの行の上限=出来事 256・人 256・店 256 行/体(ROW_CAPS_DEFAULT)・器の行の幅は"
         "出来事+人の上限の和(512)まで倍に・その種類の行が上限に届いた体は思い浮かぶ強さ A(手がかり無し)の一番低い行を消す"
         "(同点は最後に触れた時刻の古い順・次に行の番号)",
         "〔検収 M2〕上限なしの腕の器が複数日で太る(満杯の体が 1 体出ると全員の幅を倍・出来事の行は見覚えの式ではほぼ消えない)。"
         "値の錨は無い=expedient・感度の腕の口 set_row_caps。「忘れた=見覚えも無い」で消す規則は前のまま(意味は変えない)。"
         "外す条件=既定化の前に 5,000 体・7 日の測りと 39 万体の見積りがバイト予算の中(記録 §7)", [MS, M1]),
    _row("DOC-mr65-m1-shop-uncapped",
         "人も記憶の一つの腕の店の評価の行=器の店の行の表(ShopTable=状態台帳の腕の行 M0S)・幅 32 から倍に上限 256・上限で"
         "思い浮かぶ強さ A(店の記憶の式)の一番低い行を上書き(親の既定は score=A+0.5×min(4, 精度) の最小)・体の表 sm_* は"
         "書かない(空のまま)",
         "〔検収 M4〕元の発注の項 4(店 32 件の固定の上限を外す道=腕)・回答 10-12 の 6-2 の M1(人と店と出来事を同じ器に)。"
         "上限・最初の幅・消し方は expedient(DOC-mr65-m1-row-caps と同じ作り)。店の記憶の書き手・σ・減衰・読み口は前のまま"
         "(行の口 columns・_evict_slots・_put だけ差し替え)", [SHOPS, SM, MM, SC]),
    _row("DOC-mr65-m3-impression-form",
         "印象の器の形(体と相手の組ごとの履歴・寝たときは追記のあった相手だけ書き直す・意味の記憶=体ごとの結論の列)",
         "決定 10-12 §4-6 MR3 (e)・MR13 (c)。GPU が要る=器だけ(ランに結線していない)・形は未リサーチ", [MI],
         basis="inferred"),
]


def main() -> int:
    raw = LEDGER.read_text(encoding="utf-8")
    doc = json.loads(raw)
    if "--replace" in sys.argv[1:]:
        old = [j for j, r in enumerate(doc["bridges"]) if str(r["id"]).startswith("DOC-mr65-")]
        at = old[0] if old else len(doc["bridges"])
        rest = [r for r in doc["bridges"] if not str(r["id"]).startswith("DOC-mr65-")]
        doc["bridges"] = rest[:at] + ROWS + rest[at:]
        LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"置き換えた行 {len(old)} → {len(ROWS)}・台帳 {len(doc['bridges'])} 行")
        return 0
    have = {r["id"] for r in doc["bridges"]}
    added = [r for r in ROWS if r["id"] not in have]
    doc["bridges"].extend(added)
    LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"足した行 {len(added)}・台帳 {len(doc['bridges'])} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
