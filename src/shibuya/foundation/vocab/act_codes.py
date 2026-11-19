"""foundation.vocab.act_codes — 割る段で ``llm/undefined.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/intake/undefined.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final
from shibuya.foundation.vocab.actions import ACTION_CODES as _CONTRACT_ACTION_CODES
from shibuya.foundation.vocab.actions import ACTION_VOCAB_12
from shibuya.foundation.vocab.actions import EAT_ACTION_CODE
from shibuya.foundation.vocab.actions import NONE_ACTION_CODE
from shibuya.foundation.vocab.actions import ROLE_ACTION_CODES as _CONTRACT_ROLE_ACTION_CODES

__all__ = [
    "TARGET_HINT_WORDS",
    "S2_WITHDRAW", "S2_PAY_CASH", "S2_PAY_ACCOUNT", "S2_MONEY_ACT", "TARGET_HINT_CODES", "TARGET_HINT_NONE",
    "TARGET_HINT_HOME", "TARGET_HINT_WORK", "TARGET_HINT_SCHOOL", "TARGET_HINT_CATEGORY", "TARGET_HINT_APPROACH",
    "TARGET_HINT_LOOK", "ACTION_WORDS", "ACTION_CODES", "ENGINE_STEP", "ACT_MOVE", "ACT_BOARD", "ACT_ALIGHT",
    "ACT_BUY", "ACT_WAIT", "ACT_TALK", "ACT_LEAVE", "ACT_REPORT", "ACT_HELP", "ACT_REFUSE", "ACT_REST", "ACT_SLEEP",
    "ACT_EAT", "ACT_QUEUE", "ACT_NONE", "WANDER_BAD_TARGET", "DELTA_PERC_BASE_NS", "EXPECTATION_K",
    "SLEEP_SLOTS_PER_CELL",
    "TALK_OPEN_METERS", "TALK_LEAVE_METERS", "EXIT_WALK_FLAG",
]


#: 対象ヒントの語(**この並びが正典**。エンジンは索引で運ぶ=``engine.commit.TARGET_HINT_*``)。
#: ``""``=ヒントなし / ``home``/``work``/``school``=W16 の拠点セル(エンジンが解決する) /
#: ``category``=「対象」欄の物カテゴリをそのまま使う / ``approach``=対象(人/物)に近づく /
#: ``look``=対象(人/物)を注意の焦点にする。
TARGET_HINT_WORDS: Final[tuple[str, ...]] = (
    "", "home", "work", "school", "category", "approach", "look",
)


#: 行動語(行動契約書 §2.1 の 12 語・順序=表の出現順)。**正典は ``llm.contract``**。
ACTION_WORDS: Final[tuple[str, ...]] = ACTION_VOCAB_12
#: 行動語 → コード(``llm.contract.ACTION_CODES`` と**同一の値**。二重定義を作らない)。
ACTION_CODES: Final[dict[str, int]] = dict(_CONTRACT_ACTION_CODES)

ACT_MOVE: Final[int] = ACTION_CODES["移動"]
ACT_BOARD: Final[int] = ACTION_CODES["乗車"]
ACT_ALIGHT: Final[int] = ACTION_CODES["降車"]
ACT_BUY: Final[int] = ACTION_CODES["購入"]
ACT_WAIT: Final[int] = ACTION_CODES["待機"]
ACT_TALK: Final[int] = ACTION_CODES["会話"]
ACT_LEAVE: Final[int] = ACTION_CODES["退去"]
ACT_REPORT: Final[int] = ACTION_CODES["通報"]
ACT_HELP: Final[int] = ACTION_CODES["手伝い"]
ACT_REFUSE: Final[int] = ACTION_CODES["断る"]
ACT_REST: Final[int] = ACTION_CODES["休憩"]
ACT_SLEEP: Final[int] = ACTION_CODES["就寝"]
#: **語彙 v2 の「食事」**(D-71 §3 E・飲食店オブジェクトの affordance)。コードは 24
#: =既存 24 語の次(``llm.contract.EAT_ACTION_CODE``)。**語彙 v1 のランでは 1 件も立たない**
#: (パーサが「食事」を語彙語として読まないため)。
ACT_EAT: Final[int] = EAT_ACTION_CODE
#: **語彙 v3 の「並ぶ」**(D-116 C: 役割語から横断語へ・コードは役割語の 22 のまま)。
#: v1/v2 では役割語=``llm_bridge`` が安全弁へ落とすので**エンジンには来ない**。
ACT_QUEUE: Final[int] = int(_CONTRACT_ROLE_ACTION_CODES["並ぶ"])
#: **語彙 v3 の「なし」**(安全弁・コード 25)。v1/v2 のランでは 1 件も立たない。
ACT_NONE: Final[int] = NONE_ACTION_CODE
#: 「対象: あたり」を解決できなかった(域外=セル −1 の体)ときの行き先の印。
#: ``resolve._apply_move`` はこの値を ``BAD_TARGET``(対象不正)にする(v1/v2 では立たない)。
WANDER_BAD_TARGET: Final[int] = -2

#: エンジン内部の継続(経路の1歩)。LLM 由来ではないので負のコード。
ENGINE_STEP: Final[int] = -1

#: δ_perc の基準[ns](単純反応時間 213 ms・知覚契約書 §6)。
DELTA_PERC_BASE_NS: Final[int] = 213_000_000
#: 予期クラス係数 k(C0自発0 / C1予期あり1.0 / C2注意内の社会変化1.6 / C3予期なし4.9 / C4突発6.1)。
EXPECTATION_K: Final[tuple[float, ...]] = (0.0, 1.0, 1.6, 4.9, 6.1)

#: 就寝スロットの1セルあたり容量(expedient)。
SLEEP_SLOTS_PER_CELL: Final[int] = 200


# ------------------------------------------------------------------ 対象ヒント(C9b G5)
#
# 段0 辞書 v4(``llm.undefined.TARGET_HINTS_V4``)が返す**語**を、エンジンが運ぶ**索引**に
# 変える。並びの正典は ``llm.undefined.TARGET_HINT_WORDS``(テストが一致を機械検査)。
# **意思は LLM(何を対象にしたいか)・帰結はエンジン(どのセル/ノードか)** の線を跨がない
# ための 1 段(C9 決定アジェンダ §1 G5)。

#: 対象ヒントの語 → 索引。
TARGET_HINT_CODES: Final[dict[str, int]] = {w: i for i, w in enumerate(TARGET_HINT_WORDS)}
TARGET_HINT_NONE: Final[int] = TARGET_HINT_CODES[""]
TARGET_HINT_HOME: Final[int] = TARGET_HINT_CODES["home"]
TARGET_HINT_WORK: Final[int] = TARGET_HINT_CODES["work"]
TARGET_HINT_SCHOOL: Final[int] = TARGET_HINT_CODES["school"]
TARGET_HINT_CATEGORY: Final[int] = TARGET_HINT_CODES["category"]
TARGET_HINT_APPROACH: Final[int] = TARGET_HINT_CODES["approach"]
TARGET_HINT_LOOK: Final[int] = TARGET_HINT_CODES["look"]


#: 〔第 2 期 2-1〕``IntentBatch.s2_flags`` のビット: 判断の口が「お金を下ろす」を選んだ・支払いの方法の答え(現金/口座)・
#: LLM の答えの行為が金に触れる行為(購入・食事・並ぶ=元の語・遠い店へ歩く移動に変えた行も含む)。
S2_WITHDRAW: Final[int] = 1
S2_PAY_CASH: Final[int] = 2
S2_PAY_ACCOUNT: Final[int] = 4
S2_MONEY_ACT: Final[int] = 8


#: 会話が**成立**する距離[m](G7・§4 改訂「成立距離と離脱距離を分ける」)。
TALK_OPEN_METERS: Final[float] = 2.0
#: 会話が**離脱**になる距離[m](同上。同値だと境界の 2 人が毎 tick 作っては壊す=D-49 と同型)。
TALK_LEAVE_METERS: Final[float] = 3.0


#: 9a: ``plan_flags`` の「計画の退出で歩いている」ビット(``engine.presence`` が立てて落とす)。
EXIT_WALK_FLAG: Final[int] = 1 << 4
