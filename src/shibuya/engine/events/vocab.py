"""engine.events.vocab — 出来事の記録の語彙表(第 1 期 1-3・CP12・5W1H の ``what``)。**閉じた表**。

決定(口の約束 1-3 の〔空欄 1〕=親案どおり・回答 10-13b §3): ``what`` の最初の中身は 4 つの族。

| 族 | 中身 | 正(写しの元) |
|---|---|---|
| ``行為`` | 行為 12 語 | ``llm.contract.ACTION_VOCAB_V3``(語彙 v3 の横断語=import して使う) |
| ``過程`` | 世界過程の名 18 個+区切りの名 2 個 | ``engine.processes.runner.PROCESS_ORDER``(写し)+``BOUNDARY_PROCESSES`` |
| ``金`` | お金の科目 15 個 | ``economy.accounts.ACCOUNT_NAMES``(写し) |
| ``物`` | 物の出入り 8 個 | ``economy.goods.GOODS_CODE_NAMES``(写し) |

- 語は ``族:語``(``"行為:移動"``・``"過程:rail"``・``"金:賃金"``・``"物:販売"``)。族を付けるのは、``金`` と ``物`` に
  同じ語「域外仕入」があるため(族が無いと 1 語で 2 つの意味になる)。
- ``金`` と ``物`` の写し: engine は economy を import できない(層の契約 ``economy > engine``)。値の二重定義の食い違いは
  試験 ``tests/engine/events/test_e_vocab_is_closed.py`` が economy の表と突き合わせて落とす。``過程`` の写しも同じ
  試験が ``PROCESS_ORDER`` と突き合わせる(runner を import すると世界過程の全モジュールを読む=語彙表を軽く保つ)。
- 区切りの名(``day_close``・``checkpoint``)は E(診断)の行の過程の名(口の約束 1-3 の〔空欄 2〕=日の締めと
  checkpoint)。``Process("day_close")`` の名にも使う。**仮採用**(区切りの名を「過程」の族に入れた=発注の
  ``Process("day_close")`` の形に合わせた・未リサーチ(expedient))。
- 表の外の語は ``Event`` を作るときに ``ValueError``(``code_of``)。語を足すのは版上げ(試験の数も変わる)。
- 〔第 1 期 1-5〕語を 1 つ足した: ``行為:許可のない行動``(``ACT_EXTRA_WORDS``・権利に反する行動を止めずに記録する=
  決定 10-12 §1-4・CP3)。行為 12 語の写し(``ACT_WORDS``=語彙 v3)には入れない(判断の語ではなく、行為を権利台帳で
  見た分け)。**表の末尾に足した**=1-3 の 55 語のコードは動かない。原因の名に検査の名 ``rights``(``CHECK_PROCESSES``)
  を足した(``Process("rights")`` の名。``過程:rights`` の語は足していない=検査は自分の行を書かない)。版
  ``events-vocab/1-5``。
- 〔第 1 期 1-7〕族を 1 つ足した: ``道具``(道具を使った出来事=決定 10-12 §4-4 CT0 の共通の決まり 5「使用は全部、出来事の
  記録へ」)。語は道具の台帳の名の写し(``TOOL_WORDS``=``engine.tools.registry`` の名・一致は試験が見る)で、C0 は
  ``道具:看板``(看板を読んだ出来事=腕 ``SHIBUYA_TOOL_EVENTS``・既定 off・``engine.tools.record``)だけ。**表の末尾に足した**
  =1-5 までの 56 語のコードは動かない。原因の名に知覚の名 ``perception``(``PERCEPTION_PROCESSES``=System 1 の知覚・
  ``過程:`` の語ではない)を足した。版 ``events-vocab/1-7``。
- 〔第 1 期 1-8b〕語を 1 つ足した: ``行為:発話``(``SPEECH_WORDS``=発話の口 ``engine.speech`` が会話の番の「ひと言」を 1 回だけ
  書く=``whom``=届け先・``via``=道具・``how_much``=本文のモーラ数)。判断の語彙(v3 の 12 語)の外=``ACT_WORDS`` には入れない。
  **表の末尾(1-7 の ``道具:看板`` の後ろ)に別の組で足した**=1-7 までの 57 語のコード(``道具:看板``=56)は動かない。
  版 ``events-vocab/1-8b``。
- 〔第 2 期 2-1〕金の族に科目の名でない語を 2 つ足した: ``金:引き出し``(ATM・銀行で下ろす=銀行 → 世帯の現金)・``金:カード``
  (口座の決済=カード・電子マネー・IC の引き落とし)。どちらも科目は預金純増(``MONEY_EXTRA_WORDS``=``economy.ops.MONEY_EXTRA_WHAT``
  の写し・試験が突き合わせる)。``金:賃金``・``金:税`` は 1-3 の科目の語にもうある。**表の末尾(1-8b の ``行為:発話`` の後ろ)に
  別の組で足した**=1-8b までの 58 語のコード(``行為:発話``=57)は動かない(``金:引き出し``=58・``金:カード``=59)。原因の名に
  経済の段階 2 の過程の名 ``payroll``・``atm``・``register``(``ECONOMY_PROCESSES``)を末尾(1-7 の ``perception`` の後ろ)に足した
  (``Process(name)`` の名だけ・``過程`` の族の語ではない=1-5 の ``rights`` と同じ)。版 ``events-vocab/2-1``。
- 〔第 3 期 3-3〕族を 1 つ足した: ``実験``(反実仮想の申込書の改変=決定 10-12 §4-5 CP5・CP6・CP12)。語は ``改変``(申込書の決定が
  世界に入った=原因は実験の条件・口は ``engine.experiment.gate.admit`` だけ)と ``届いた情報``(外での決定が境界を越えて届いた=
  告知の宛先ごとに 1 行・``via``=道具・``received_ns``=届いた時刻)。**表の末尾(2-1 の ``金:カード`` の後ろ)に足した**=2-1
  までの 60 語のコード(``金:カード``=59)は動かない(``実験:改変``=60・``実験:届いた情報``=61)。版 ``events-vocab/3-3``。
  **仮採用**(族の名と語は実行役の構成=未リサーチ(expedient)・10-13b §0-3)。

``via``(CT9 の道具の欄)の語: 対面・通話・メッセージ・グループ・SNS・無し(決定 10-12 §4-4 CT9 (b) の 5 つ+無し)。
``where`` の種類: セル・ノード・POI(口の約束 1-3)。

逐次ループ宣言: なし(表を作るのは import のときに 1 回)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping, Final

from shibuya.llm.contract import ACTION_VOCAB_V3

__all__ = [
    "FAMILY_ACT", "FAMILY_PROCESS", "FAMILY_MONEY", "FAMILY_GOODS", "FAMILY_TOOL", "FAMILY_EXPERIMENT", "FAMILIES",
    "ACT_WORDS", "WORLD_PROCESSES", "BOUNDARY_PROCESSES", "PROCESS_NAMES", "MONEY_WORDS", "GOODS_WORDS",
    "ACT_EXTRA_WORDS", "CHECK_PROCESSES", "PERCEPTION_PROCESSES", "CAUSE_PROCESS_NAMES", "TOOL_WORDS", "SPEECH_WORDS",
    "MONEY_EXTRA_WORDS", "ECONOMY_PROCESSES", "EXPERIMENT_WORDS",
    "VOCAB", "VOCAB_CODES", "VOCAB_VERSION", "word", "code_of", "family_of",
    "VIA_WORDS", "VIA_NONE", "VIA_CODES", "WHERE_KINDS",
]

#: 表の版(語を足したら上げる)。
VOCAB_VERSION: Final[str] = "events-vocab/3-3"

FAMILY_ACT: Final[str] = "行為"
FAMILY_PROCESS: Final[str] = "過程"
FAMILY_MONEY: Final[str] = "金"
FAMILY_GOODS: Final[str] = "物"
#: 〔1-7〕道具を使った出来事の族(族の並びの末尾)。
FAMILY_TOOL: Final[str] = "道具"
#: 〔3-3〕反実仮想の申込書の改変の族(族の並びの末尾)。
FAMILY_EXPERIMENT: Final[str] = "実験"
FAMILIES: Final[tuple[str, ...]] = (FAMILY_ACT, FAMILY_PROCESS, FAMILY_MONEY, FAMILY_GOODS, FAMILY_TOOL,
                                    FAMILY_EXPERIMENT)

#: 行為 12 語(語彙 v3 の横断語・並びは v3 の表のまま)。
ACT_WORDS: Final[tuple[str, ...]] = tuple(ACTION_VOCAB_V3)

#: 世界過程の名(``engine.processes.runner.PROCESS_ORDER`` の写し・並びも同じ)。
WORLD_PROCESSES: Final[tuple[str, ...]] = (
    "environment", "rail", "opening", "crowd", "traffic",
    "delivery_inbound", "shelf", "waste", "street_cleaning",
    "last_mile", "bus_taxi", "road_works", "hotel", "infra", "press", "large_event", "dispatch",
    "salient",
)
#: E(診断)の区切りの名(日の締め・checkpoint)。
BOUNDARY_PROCESSES: Final[tuple[str, ...]] = ("day_close", "checkpoint")
#: 世界過程と区切りの名(``過程`` の族の語)。
PROCESS_NAMES: Final[tuple[str, ...]] = WORLD_PROCESSES + BOUNDARY_PROCESSES
#: 〔1-5〕検査の名(``Process(name)`` の名だけ・``過程`` の族の語ではない)。``rights``=権利台帳の検査(許可のない行動)。
CHECK_PROCESSES: Final[tuple[str, ...]] = ("rights",)
#: 〔1-7〕知覚の名(``Process(name)`` の名だけ・``過程`` の族の語ではない)。``perception``=System 1 の知覚(看板を読んだ出来事の原因)。
PERCEPTION_PROCESSES: Final[tuple[str, ...]] = ("perception",)
#: 〔2-1〕経済の段階 2 の過程の名(``Process(name)`` の名だけ)。``payroll``=給料日の賃金・``atm``=ATM の引き出し・
#: ``register``=レジの消費税(``engine.economy_stage2.CAUSE_NAMES`` と同じ)。末尾に足した(前の名の番号は動かない)。
ECONOMY_PROCESSES: Final[tuple[str, ...]] = ("payroll", "atm", "register")
#: ``Process(name)`` の名に使える名(世界過程+区切り+検査+知覚+〔2-1〕経済の段階 2)。
CAUSE_PROCESS_NAMES: Final[tuple[str, ...]] = PROCESS_NAMES + CHECK_PROCESSES + PERCEPTION_PROCESSES + ECONOMY_PROCESSES

#: お金の科目(``economy.accounts.ACCOUNT_NAMES`` の写し・並びも同じ)。
MONEY_WORDS: Final[tuple[str, ...]] = (
    "消費支出", "賃金", "域外仕入", "税", "利子", "家賃", "預金純増",
    "来街者持込", "持ち出し", "参入資本", "配当/内部留保", "減価償却",
    "残差科目", "退蔵項", "逸脱比例コスト",
)
#: 物の出入り(``economy.goods.GOODS_CODE_NAMES`` の写し・並びも同じ)。
GOODS_WORDS: Final[tuple[str, ...]] = (
    "域外仕入", "持込物", "販売", "廃棄ビンへ", "消費", "廃棄搬出", "返品/域外出荷", "棚卸差異",
)


def word(family: str, w: str) -> str:
    """族と語 → 表の語(``"過程:rail"``)。表の外なら ``ValueError``。"""
    q = f"{family}:{w}"
    if q not in VOCAB_CODES:
        raise ValueError(f"出来事の語彙表の外: {q!r}(族は {FAMILIES})")
    return q


#: 〔1-5〕行為の族に足した語(判断の語彙の外=行為を権利台帳で見た分け)。表の末尾に置く(1-3 の語のコードを動かさない)。
ACT_EXTRA_WORDS: Final[tuple[str, ...]] = ("許可のない行動",)
#: 〔1-7〕道具の族の語(道具の台帳の名の写し=``engine.tools.registry.SIGNBOARD``)。表の末尾に置く(1-5 までの語のコードを動かさない)。
TOOL_WORDS: Final[tuple[str, ...]] = ("看板",)
#: 〔1-8b〕行為の族の語 ``発話``(発話の口が書く会話の番の「ひと言」)。1-7 の ``TOOL_WORDS`` の後ろの別の組(1-7 までの語の
#: コードを動かさない=``道具:看板``=56・``行為:発話``=57)。
SPEECH_WORDS: Final[tuple[str, ...]] = ("発話",)
#: 〔2-1〕金の族に足した科目の名でない語(``economy.ops.MONEY_EXTRA_WHAT`` の写し・並びも同じ)。1-8b の ``SPEECH_WORDS`` の後ろの
#: 別の組(1-8b までの語のコードを動かさない=``金:引き出し``=58・``金:カード``=59)。
MONEY_EXTRA_WORDS: Final[tuple[str, ...]] = ("引き出し", "カード")
#: 〔3-3〕実験の族の語(``改変``=申込書の決定が世界に入った・``届いた情報``=外での決定が境界を越えて届いた)。2-1 の
#: ``MONEY_EXTRA_WORDS`` の後ろの別の組(2-1 までの語のコードを動かさない=``実験:改変``=60・``実験:届いた情報``=61)。
EXPERIMENT_WORDS: Final[tuple[str, ...]] = ("改変", "届いた情報")

#: 表の全部(1-3 の 55 語は族の順 → 族の中の順・その後ろに 1-5 で足した語・その後ろに 1-7 で足した語・その後ろに 1-8b で
#: 足した語・その後ろに 2-1 で足した金の 2 語・その後ろに 3-3 で足した実験の 2 語)。コードはこの並びの位置(記録の列に入る int16)。
VOCAB: Final[tuple[str, ...]] = (
    tuple(f"{FAMILY_ACT}:{w}" for w in ACT_WORDS)
    + tuple(f"{FAMILY_PROCESS}:{w}" for w in PROCESS_NAMES)
    + tuple(f"{FAMILY_MONEY}:{w}" for w in MONEY_WORDS)
    + tuple(f"{FAMILY_GOODS}:{w}" for w in GOODS_WORDS)
    + tuple(f"{FAMILY_ACT}:{w}" for w in ACT_EXTRA_WORDS)
    + tuple(f"{FAMILY_TOOL}:{w}" for w in TOOL_WORDS)
    + tuple(f"{FAMILY_ACT}:{w}" for w in SPEECH_WORDS)
    + tuple(f"{FAMILY_MONEY}:{w}" for w in MONEY_EXTRA_WORDS)
    + tuple(f"{FAMILY_EXPERIMENT}:{w}" for w in EXPERIMENT_WORDS)
)
VOCAB_CODES: Final[Mapping[str, int]] = MappingProxyType({w: i for i, w in enumerate(VOCAB)})  # 検収 L7: 実行時に語を足せない
assert len(VOCAB_CODES) == len(VOCAB), "語彙表に同じ語が 2 回ある"


def code_of(what: str) -> int:
    """表の語 → コード。表の外なら ``ValueError``(閉じた表)。"""
    try:
        return VOCAB_CODES[what]
    except (KeyError, TypeError):
        raise ValueError(f"出来事の語彙表の外: {what!r}(表は {len(VOCAB)} 語・形は '族:語')") from None


def family_of(what: str) -> str:
    """表の語の族(``"金:賃金"`` → ``"金"``)。"""
    code_of(what)
    return what.split(":", 1)[0]


#: CT9 の道具の欄(届いた経路)。``無し`` は道具を使わない出来事(世界過程・区切り・本人だけの行為)。
VIA_WORDS: Final[tuple[str, ...]] = ("対面", "通話", "メッセージ", "グループ", "SNS", "無し")
VIA_NONE: Final[str] = "無し"
VIA_CODES: Final[Mapping[str, int]] = MappingProxyType({w: i for i, w in enumerate(VIA_WORDS)})

#: ``where`` の種類(セル・歩行網のノード・POI)。
WHERE_KINDS: Final[tuple[str, ...]] = ("cell", "node", "poi")
