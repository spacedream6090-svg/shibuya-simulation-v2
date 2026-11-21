"""world.processes.absent — 「無いと宣言」する過程と判断の一覧(第340 段 2 の 6・回答 11-01 §2・§10-3)。

正典
- 回答 11-01 §2「まだ判断の口が無い過程は『無い』と宣言する」・§10-3「無いと宣言する過程(文案は routing §3)」。
- 文案: ``docs/reference/decision-routing-2026-11-01.md`` §3-1(主体が居ない過程)・§3-2(口がまだ無い判断)。
- 指示書 ``docs/design/prompt-2026-11-01.md`` 段 2 の 6: 納品と発注は「無い」ではなく、納品=入力(境界の外からの
  物の流れ・量は錨から外す)、発注=店の初期の予定(固定の注文・店主の口ができたら本人へ)として宣言する。

本モジュールは**宣言だけ**を持つ(エンジンの挙動を変えない)。いまエンジンの規則が動いている過程は
``Absence.engine_now`` にそう書く。規則を外すのは別の段(率の規則=段 2 の 3・4)で、外す段が指示書に無い過程は
「親が決める」と書いた。一覧は計器 ``tools/instruments/absent_declarations.py`` が Markdown に出す(版上げごと)。

「無い」の例外(〔検収 中-3〕): ``engine_stopped=True`` の宣言だけが循環の検査の例外になる。True は、口が無いので
起きない判断(no_port の 12 件と補足)・採用と解雇・発注と、率の規則を外す段(ce52662・``engine.rate_rules`` の既定 off)で
止まった 5 件=宅配(``parcels``)・倒れる(``collapse``)・催しの注入(``event_injection``)・ポイ捨て(``litter``)・
売れ残りの廃棄(``leftover_waste``)と、〔11-02r §1 #7〕「無い」の過程を止める段(``engine.absent_processes`` の既定
stopped)で止まった 5 件=ごみ収集・街路の清掃・道路工事・救急と警察の出動・電気と水。False は納品(入力の宣言・
``delivery_inbound`` の E5 と気象の文と一緒に次の版上げ)だけ。

文案の扱い: routing §3 の文案はそのまま写した(「外す段」の空欄も「空欄」のまま)。routing §3 に文案の無いもの
(電気と水の負荷=回答 11-01 §10-2 の 6-8・納品と発注の言い換え=指示書 段 2 の 6)は同じ形で実装役が書き、
``source`` に「実装役の文」と書いた。
"""

from __future__ import annotations

from typing import Final

from shibuya.world.ledger.records import Absence

__all__ = [
    "ROUTING_DOC",
    "NO_ACTOR",
    "REPLACED",
    "NO_PORT",
    "NO_PORT_EXTRA",
    "RATE_REMOVED",
    "ABSENCES",
    "by_id",
    "by_world_process",
    "by_routing_row",
]

ROUTING_DOC: Final[str] = "docs/reference/decision-routing-2026-11-01.md"
_S31 = f"{ROUTING_DOC} §3-1"
_S32 = f"{ROUTING_DOC} §3-2"
_NO_PORT_NOW = "口が無いので今も起きない({where})"
_RATE_OFF = ("外した(率の規則 {rule}=既定 off・engine/rate_rules.py・段 2 の 3・4)。旧道 `--rate-rules legacy` では {where} が"
             "動く(1 版だけ=次の版上げで消す)")
_ABSENT_OFF = ("止めた(「無い」の過程 {name}=既定 stopped・engine/absent_processes.py・11-02r §1 #7)。旧道 "
               "`--absent-processes legacy` では {where} が動く(1 版だけ=次の版上げで消す)")

# ================================================================== §3-1 主体が居ない過程(回答 11-01 §10-3 の 8 つ)
NO_ACTOR: Final[tuple[Absence, ...]] = (
    Absence(
        id="absent.waste_collection",
        subject="ごみ収集",
        kind="no_actor",
        statement="ごみの収集は世界に無い。理由: 主体(収集員の体)が居ない。外す段: 収集員の体を置く段(空欄)",
        reason="主体(収集員の体)が居ない",
        remove_at="収集員の体を置く段(空欄)",
        effect="ごみが溜まる一方。W1 は収集ができるまで比べられない",
        engine_now=_ABSENT_OFF.format(name="waste_collection", where="06〜10 時にセル順=engine/processes/goods_flow.py"),
        routing_rows=(103,),
        world_process_id="waste_collection",
        source=_S31,
        engine_stopped=True,
        stage="next-bump",
    ),
    Absence(
        id="absent.street_cleaning",
        subject="街路の清掃",
        kind="no_actor",
        statement="道の清掃は世界に無い。理由: 主体(清掃員の体)が居ない。外す段: 清掃員の体を置く段(空欄)",
        reason="主体(清掃員の体)が居ない",
        remove_at="清掃員の体を置く段(空欄)",
        effect="ポイ捨てが残る",
        engine_now=_ABSENT_OFF.format(name="street_cleaning",
                                      where="05〜07・13〜15 時に 8 セル/刻み=engine/processes/goods_flow.py"),
        routing_rows=(104,),
        world_process_id="street_cleaning",
        source=_S31,
        engine_stopped=True,
        stage="next-bump",
    ),
    Absence(
        id="absent.parcel_delivery",
        subject="宅配",
        kind="no_actor",
        statement=(
            "宅配は世界に無い。理由: 主体(配達員の体)と注文が居ない。27,000 個/日は区按分の集計で、錨 W2 と循環する。"
            "外す段: 配達員と注文の主体を置く段(空欄)。W2 は検証の錨に残す"
        ),
        reason="主体(配達員の体)と注文が居ない・27,000 個/日は区按分の集計で錨 W2 と循環する",
        remove_at="配達員と注文の主体を置く段(空欄)",
        effect="宅配の車と人が街から消える(7,657 個/日 [A])",
        engine_now=_RATE_OFF.format(rule="parcels", where="区按分 27,000 個/日=engine/processes/logistics.py"),
        routing_rows=(105,),
        world_process_id="delivery_last_mile",
        source=_S31,
        keeps_anchor=("W2",),
        engine_stopped=True,
        stage="next-bump",
    ),
    Absence(
        id="absent.road_works",
        subject="道路工事",
        kind="no_actor",
        statement="道路工事は世界に無い。理由: 主体(業者の体)が居ない。外す段: 業者と占用許可を置く段(台帳の返済は Phase 3)",
        reason="主体(業者の体)が居ない",
        remove_at="業者と占用許可を置く段(台帳の返済は Phase 3)",
        effect="夜の通行止め(12 件/日 [A])が無くなる",
        engine_now=_ABSENT_OFF.format(name="road_works", where="毎晩 6 辺・22〜05 時=engine/processes/logistics.py"),
        routing_rows=(106,),
        world_process_id="road_works_occupancy",
        source=_S31,
        engine_stopped=True,
        stage="next-bump",
    ),
    Absence(
        id="absent.public_service_dispatch",
        subject="救急と警察の出動",
        kind="no_actor",
        statement=(
            "救急と警察の出動は世界に無い。理由: 主体(隊員と指令の体)が居ない。出力が錨 W3 に入る。"
            "外す段: 通報を受ける体と隊員を置く段(空欄)。W3 は錨に残す・体の式ができるまで検証から外す"
        ),
        reason="主体(隊員と指令の体)が居ない・出力が錨 W3 に入る",
        remove_at="通報を受ける体と隊員を置く段(空欄)",
        effect="倒れた人が運ばれない。#56 通報の効果先も無い",
        engine_now=_ABSENT_OFF.format(name="dispatch", where="倒れたら 100% 出動・中央値 8 分=engine/processes/civic.py"),
        routing_rows=(110,),
        world_process_id="public_service_dispatch",
        source=f"{_S31}+W3 の文は回答 11-01 §3 の読みに統一(検収 低-8)",
        keeps_anchor=("W3",),
        engine_stopped=True,
        stage="next-bump",
    ),
    Absence(
        id="absent.event_injection",
        subject="催しの人の注入",
        kind="no_actor",
        statement=(
            "催しのための外からの人の注入は世界に無い。理由: 200 人は集計の量で、主催者も居ない。"
            "外す段: 催しの情報を外の人に届ける入口と、本人の『来るか』の口ができたら、来る人は本人の判断で現れる"
        ),
        reason="200 人は集計の量で、主催者も居ない",
        remove_at="催しの情報を外の人に届ける入口と、本人の『来るか』の口ができたら(指示書 段 3)",
        effect="催しの日の人出が 0 になる",
        engine_now=_RATE_OFF.format(rule="event_injection", where="18 時に 200 人を会場へ・21 時に出す=engine/processes/civic.py"),
        routing_rows=(10,),
        world_process_id="large_event",
        source=_S31,
        engine_stopped=True,
        stage="next-bump",
    ),
    Absence(
        id="absent.hiring_firing",
        subject="採用と解雇",
        kind="no_actor",
        statement=(
            "採用と解雇は世界に無い。理由: 主体(雇い主のエージェント)が居ない。雇用は構築時の W21 の行で固定。"
            "外す段: 雇い主のエージェント(空欄)"
        ),
        reason="主体(雇い主のエージェント)が居ない",
        remove_at="雇い主のエージェント(空欄)",
        effect="雇用はランの間ずっと同じ",
        engine_now=_NO_PORT_NOW.format(where="W21 の雇用の行は構築時に固定=routing §1-9"),
        source=f"{_S31}(§1-9 の組織の行)",
        engine_stopped=True,
        stage="7",
    ),
    Absence(
        id="absent.power_water",
        subject="電気と水の負荷",
        kind="no_actor",
        statement=(
            "電気と水の負荷は世界に無い。理由: 人数 × 原単位は集計の量で、原単位に出典が無く、機器を使う本人の行為も"
            "建物の主体も居ない。外す段: 機器を使う行為か建物の主体を置く段(空欄)。W5 は錨に残す(実数は空欄)"
        ),
        reason="人数 × 原単位は集計の量(原単位は出典なし)・機器を使う本人の行為も建物の主体も居ない",
        remove_at="機器を使う行為か建物の主体を置く段(空欄)",
        effect="電気と水の日負荷の形が出なくなる(W5 は実数が空欄なので照合は元から無い)",
        engine_now=_ABSENT_OFF.format(name="infra", where="人数 × 0.35 kWh・0.012 m³/時=engine/processes/civic.py"),
        routing_rows=(43,),
        world_process_id="infra_daily_load",
        source="回答 11-01 §10-2(6-8)・routing §6-8 の (a)=文は実装役(routing §3 に文案なし)",
        keeps_anchor=("W5",),
        engine_stopped=True,
        stage="next-bump",
    ),
)

# ================================================================== 「無い」ではないもの(指示書 段 2 の 6)
REPLACED: Final[tuple[Absence, ...]] = (
    Absence(
        id="absent.inbound_delivery",
        subject="納品",
        kind="input",
        statement=(
            "納品は世界の外から来る物の流れ(入力)として宣言する。配送員は外から入る人。納品の量は錨から外す。"
            "発注は店主の判断で、それまでは店の初期の予定(固定の注文)"
        ),
        reason="例外にしない(回答 11-01 §10-1)。配送員の体は範囲の中に居ない=物の流れは境界の外の決定",
        remove_at="発注=店主の口(A2)ができたら本人の判断へ。配送員の体を置く段(空欄)",
        effect="棚に物が入り続ける(在庫は 05〜08 時の納品で補われる)",
        engine_now="エンジンの規則がまだ動く(05〜08 時の乱数・15% 遅れ=engine/processes/goods_flow.py)。入力の欄は "
        "input.inbound_goods(値は段 0 の後)",
        routing_rows=(102,),
        world_process_id="delivery_inbound",
        source="回答 11-01 §10-1・指示書 段 2 の 6=文は実装役(routing §3-1 の「納品は世界に無い」を置き換えた)",
        engine_stopped=False,
        stage="6-6",
    ),
    Absence(
        id="absent.ordering",
        subject="発注",
        kind="initial_plan",
        statement=(
            "発注は世界の住人の判断としてはまだ無い。店の初期の予定(固定の注文)として宣言する。"
            "店主の口(A2)ができたら本人の判断へ"
        ),
        reason="主体(店主・本部)の発注の口が無い",
        remove_at="店主の口(A2)ができたら",
        effect="注文は構築時の固定のまま",
        engine_now=_NO_PORT_NOW.format(where="納品のロット=補充ロット × 2 の固定=engine/processes/goods_flow.py"),
        source="回答 11-01 §10-1・指示書 段 2 の 6=文は実装役(routing §3-1 の「発注は世界に無い」を置き換えた)",
        engine_stopped=True,
        stage="7",
    ),
)


def _np(aid: str, subject: str, rows: tuple[int, ...], statement: str, reason: str, remove_at: str, where: str,
        *, keeps: tuple[str, ...] = (), now: str = "", stage: str = "11-01p-3", stopped: bool = True,
        source: str = _S32) -> Absence:
    return Absence(
        id=aid,
        subject=subject,
        kind="no_port",
        statement=statement,
        reason=reason,
        remove_at=remove_at,
        engine_now=now or _NO_PORT_NOW.format(where=where),
        routing_rows=rows,
        source=source,
        keeps_anchor=keeps,
        engine_stopped=stopped,
        stage=stage,
    )


# ================================================================== §3-2 口がまだ無い判断(回答 11-01 §10-3 の 13 件)
NO_PORT: Final[tuple[Absence, ...]] = (
    _np("absent.skip_train", "電車を見送る", (21,),
        "来た電車を見送る人は世界に無い。理由: 口が無い(先着順で必ず乗る)。外す段: 便の候補を判断へ渡す口ができたら",
        "口が無い(先着順で必ず乗る)", "便の候補を判断へ渡す口ができたら", "停車中の先頭の便に必ず乗せる"),
    _np("absent.item_qty", "品と数を選ぶ", (37,),
        "品と数を選ぶ人は世界に無い。理由: 口が無い(1 行 1 個・棚の並び)。外す段: 品の知覚と数の欄(DM13)ができたら",
        "口が無い(1 行 1 個・棚の並び)", "品の知覚と数の欄(DM13)ができたら", "1 行 1 個・品は棚の並び"),
    _np("absent.price_balk", "値段を見て見送る", (38,),
        "値段を見て見送る人は世界に無い。理由: 口が無い(値段は買えなかった後にしか見えない)。外す段: 値段の知覚(B2)ができたら",
        "口が無い(値段は買えなかった後にしか見えない)", "値段の知覚(B2)ができたら", "値段は買えなかった後にしか見せない"),
    _np("absent.third_joiner", "3 人目として加わる", (53,),
        "会話に 3 人目として加わる人は世界に無い。理由: 上限 2。外す段: 腕 3 を既定にしたら",
        "上限 2", "腕 3 を既定にしたら", "会話の上限 2"),
    _np("absent.replan", "予定を考え直す", (64,),
        "予定を日中に考え直す人は世界に無い(既定)。理由: 口が無い。外す段: DM8(変化と時刻の入口)ができたら",
        "口が無い", "DM8(変化と時刻の入口)ができたら", "腕 1b に plan/continue/deliberate があるだけ"),
    _np("absent.eat_home", "家で食べる", (80,),
        "範囲の中の家で食べる人は世界に無い。理由: 口が無い(`--home-meal off`)。外す段: 家の食事の行為と物ができたら",
        "口が無い(`--home-meal off`)", "家の食事の行為と物ができたら", "`--home-meal off`"),
    _np("absent.deliberate", "よく考える", (95,),
        "よく考えるか決める段は世界に無い(既定は起床のたびに全部 L2)。理由: 口が無い。外す段: DM5 と上の層(J3)ができたら",
        "口が無い", "DM5 と上の層(J3)ができたら", "既定は起床のたびに全部 L2"),
    _np("absent.utterance", "ひと言", (49,),
        "会話のひと言は世界に無い(既定)。理由: 語彙 v3 に欄が無く、`--speech-port off`。外す段: 発話の口を既定にしたら",
        "語彙 v3 に欄が無く、`--speech-port off`", "発話の口を既定にしたら", "`--speech-port off`", stage="6-4"),
    _np("absent.reflect_day", "1 日の振り返り", (94,),
        "1 日の振り返りは世界に無い。理由: 就寝で数えるだけで呼ばない。外す段: 就寝時の熟考の口ができたら",
        "就寝で数えるだけで呼ばない", "就寝時の熟考の口ができたら", "就寝で数えるだけ", stage="6-7"),
    _np("absent.plan_fix_surprise", "予想と違って直す", (96,),
        "予想と違って計画を直す人は世界に無い。理由: 予想の欄が空。外す段: 予想の器ができたら",
        "予想の欄が空", "予想の器ができたら", "予想の欄 `prediction` が空", stage="6-7"),
    _np("absent.serve_customer", "接客", (100,),
        "接客は世界に無い。理由: 役割語に適用が無い。外す段: 効果先と店員の発話の口ができたら",
        "役割語に適用が無い", "効果先と店員の発話の口ができたら", "役割語「接客」に適用が無い", stage="6-6"),
    _np("absent.change_price", "値段を変える", (101,),
        "値段を変える店主は世界に無い。価格は構築時の値で固定。理由: 店主の体と価格の口が無い。"
        "外す段: 店主の体と役割語『価格改定』の適用ができたら。改定確率(Calvo)と β は結線しない",
        "店主の体と価格の口が無い", "店主の体と役割語『価格改定』の適用ができたら",
        "pricing.py の改定はエンジンに結線されていない", keeps=("E7",), stage="next-bump"),
    _np("absent.collapse", "倒れる", (83,),
        "急に倒れる人は世界に無い(率を外した後)。理由: 体の式がまだ無い。外す段: WBGT→熱中症の体の式ができたら。"
        "W3 は錨に残す・体の式ができるまで検証から外す",
        "体の式がまだ無い", "WBGT→熱中症の体の式ができたら(B8)", "",
        keeps=("W3",), stage="next-bump", stopped=True, source=f"{_S32}+W3 の文は回答 11-01 §3 の読みに統一(検収 低-8)",
        now=_RATE_OFF.format(rule="collapse", where="1 万体あたり 1 日 3.0 件=engine/body/rules.py BR-BODY-COLLAPSE-RATE")),
)

#: 回答 11-01 §2 の「同じ形で外すもの」のうち「無い」と宣言する 2 件(率の規則=S2-rates が外す・文は実装役)。
RATE_REMOVED: Final[tuple[Absence, ...]] = (
    _np("absent.litter", "ポイ捨て", (42,),
        "ポイ捨ては世界に無い。理由: セルの人数 × 0.05 g/刻みは集計の量(回答 11-01 §2)。"
        "外す段: 持ち物の状態と語彙「捨てる」ができたら",
        "人数 × 率は集計の量", "持ち物の状態と語彙「捨てる」ができたら", "",
        stage="next-bump", stopped=True, source="回答 11-01 §2・routing §6-B #42=文は実装役",
        now=_RATE_OFF.format(rule="litter", where="セルの人数 × 0.05 g/刻み=engine/processes/goods_flow.py")),
    _np("absent.discard_unsold", "売れ残りの廃棄", (99,),
        "売れ残りの廃棄は世界に無い。理由: 05 時に廃棄率を掛けるのは率の形(回答 11-01 §2)。"
        "外す段: 店員の判断(腕 duties)を既定にしたら",
        "廃棄率を掛けるのは率の形", "店員の判断(腕 duties)を既定にしたら", "",
        stage="next-bump", stopped=True, source="回答 11-01 §2・routing §6-B #99=文は実装役",
        now=_RATE_OFF.format(rule="leftover_waste", where="閉店帯に SKU 別 waste_rate を棚へ掛ける=engine/processes/goods_flow.py")),
)

#: 回答 11-01 §10-3 の 13 件の外で、routing §3-2 と §10-1 が同じ形で「成立しない」と書くもの(数えを分ける)。
NO_PORT_EXTRA: Final[tuple[Absence, ...]] = (
    _np("absent.help_refuse_effect", "手伝い・断るの効果", (54, 55),
        "手伝いは成立しない・断っても状態は変わらない。理由: 効果先が無い。外す段: 援助を求める状態と効果先ができたら",
        "効果先が無い", "援助を求める状態と効果先ができたら", "手伝いは mock でいつも失敗・断るは記録だけ"),
)

#: 全部(計器の並びの順)。
ABSENCES: Final[tuple[Absence, ...]] = NO_ACTOR + REPLACED + NO_PORT + RATE_REMOVED + NO_PORT_EXTRA


def by_id() -> dict[str, Absence]:
    out = {a.id: a for a in ABSENCES}
    if len(out) != len(ABSENCES):
        raise ValueError("absent の id が重なる")
    return out


def by_world_process() -> dict[str, Absence]:
    """``world_process_id`` → 宣言(``kind`` が no_actor のものだけ=「無い」の過程)。"""
    return {a.world_process_id: a for a in ABSENCES if a.world_process_id and a.kind == "no_actor"}


def by_routing_row() -> dict[int, Absence]:
    """routing §1 の行の番号 → 宣言(「無い」の宣言=no_actor と no_port だけ)。"""
    out: dict[int, Absence] = {}
    for a in ABSENCES:
        if a.kind not in ("no_actor", "no_port"):
            continue
        for r in a.routing_rows:
            out[r] = a
    return out
