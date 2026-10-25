"""engine.speech_clock — 会話の時計(第 6 期 6-3 時計の段 T2・TM3・腕 ``--talk-clock mora``)。

正典: 決定 10-12 §4-2 TM3(発言の長さ = モーラ数 × その人の話す速さ=人ごとの値+その時々の揺れ・リサーチ C4/間は日本語の値/
考える時間は TM2 の側で数え二重に数えない/あいづち・重なりは後/まとめの中は時刻順に順番に回し持ち越す (f)/上限は安全装置だけで
当たったら記録/1 つの会話の中はまとめない・違う会話どうしはバッチ/1 回の LLM に会話全部を書かせない)・TM6 の T2・TM7(時刻は
ナノ秒の整数・乱数は出来事の時刻と中身に結ぶ)・TM1(続いているチャットは同じ細かい時計=打つ時間・読む間=CT の C1)。
答申 R-111 §3 C4(話す速さ)・R-73 §4-2(間)。記録 ``docs/bench/analysis/wallbounce-1012/tm234/README.md``。

腕(切替口): ``--talk-clock {table,mora}``(環境変数 ``SHIBUYA_TALK_CLOCK``・:func:`set_arm`)。既定 ``table``=今の 1 ターンの
長さの表(行動契約書 §3「1 呼=1 発話ブロック」=会話の番 1 つが刻み 1 つ)=持ち主を作らない(結果・manifest は今のまま)。
``mora`` は組み立てが :class:`TalkClock` を作り、会話の番の発話ごとに「モーラ数 × その人の話す速さ」で発言の長さを決め、
会話ごとの時計(発言の始まり・終わり・次の発言の始まり=終わり+間)を持つ。発言は計算のまとめの窓の待ち行列の事象(種類
``talk``)として時刻順に処理し、会話の計器(発言の長さ・話す速さ・会話の長さ・持ち越し・上限)を数える。

世界との関係(つなぎの台帳 ``DOC-tm234-talk-clock-meter-only``): 会話の番は今も刻みに 1 回(系 decide・llm_receive)で、
時計は会話の中の時刻を数えて記録するだけ(世界の状態・テープ・final は変えない=19 構成の byte-check)。会話の番を窓の中で
時刻順に続けて回す(違う会話どうしを 1 回の LLM にまとめ、同じ会話の次の番は前の番が返ってから)のは版上げ(T2 の既定化)。

時計の規則(仮採用=記録 §T2 の表・つなぎの台帳 ``DOC-tm234-*``):

1. 発言の長さ[ns] = モーラ数 × 人ごとのモーラの長さ × 発言ごとの揺れ × 相手の項(四捨五入で整数)。モーラ数は本文から
   ``engine.speech.port.mora_count``(仮名の数の近似=1-8b の読みの規則)。仮名も漢字も無い本文(英語など)は欄だけ=
   長さは今の表(刻み 1 つ)でつなぐ(``lang_other`` に数える)。本文の無い番(ひと言が空・「なし」)は発言にしない(``silent``)。
2. 人ごとのモーラの長さ: 対数の正規(中心 ln 0.151 秒)を CEJC の話者 18 人の範囲 [0.124, 0.198] 秒で切った形。幅 σ は
   範囲 ÷ d2(18)=3.640(正規の標本 18 の範囲の期待値=範囲から SD への換算)。乱数は母集団の seed と体の番号(Philox)。
3. 発言ごとの揺れ: 平均 1 の対数正規・CV 0.42(Quené 2005 の話者の中の CV=句の長さの項を入れないときの値)。乱数は動きの
   seed と(話し手・発言を作った時刻・会話の番号)=TM7 (d)。
4. 相手の項: 関係の層で話し手から相手に生きている辺(A ≥ τ)があれば親しい=1・無ければ知らない相手=モーラの長さ ×
   (1 + 0.096)(Yuan 2006 の英語 +10.9%・中国語 +8.3% の平均=親しい相手に速い)。関係の層の無いランは欄だけ(1・
   ``familiar_unknown`` に数える)。
5. 間: 日本語の応答の間の平均 +7 ms(中央値 0 ms・Stivers 2009)の定数。考える時間(TM2=今の表 L4 0.2 秒)は足さない
   (二重に数えない=考える時間は TM2 の側の ``t_apply`` が数える)。
6. 会話の時計: 最初の発言は作った時刻に始まる。次の発言の始まり = 前の発言の終わり + 間(会話の中の時刻=TM3 の時計)。発言の
   事象は「始まり」と「今処理している時刻」の遅い方に置く。始まりが今より前(会話の番は刻みに 1 回なので、ふつうは前の窓に
   入るはずだった)=持ち越し(``carried``・遅れ ``lag_ns``)=TM3 (f) の「収まらない分は次の窓へ」。
7. 1 つの会話の中はまとめない: 同じ会話の発言を同じ処理の束(同じ時刻・同じ種類の続き)に入れたら止める(``RuntimeError``)。
   次の発言は前の発言の事象を処理してから予約する。違う会話どうしは同じ束で処理する(``batch_max``)。
8. 上限(安全装置): 1 つの会話が 1 つの窓で処理する発言の数 ``cap_per_window``(既定 2^10)。当たったら次の窓の頭へ持ち越して
   ``cap_hits`` に数える(止めない)。
9. 締めの定型 1 発話(エンジン生成)・あいづち・重なりは時計に入れない(TM3「後で扱う」)。

C1(チャットの会話の状態)が刺す口: :data:`MODALITIES`(``対面``=話す・``チャット``=打つ)と :class:`ChatTiming`
(打つ時間 ``typing_ns``・読む間 ``read_gap_ns``=値は空欄=None・C1 で入れる)。``チャット`` の発言は今は時計に載せず
``chat_blank`` に数える。

状態(状態台帳の腕の行 ``TCR``・``TCC``=軸 1 diag・軸 2 discardable=どちらのハッシュにも状態のファイルにも入らない):
人ごとのモーラの長さの控え(母集団の seed と体から引き直せる)・会話ごとの時計・予約した発言・計器。再開のランは空から
(話し中の会話は再開の後の最初の発言から時計を始め直す)。

逐次ループ宣言(P4): ``on_turn`` は会話の番 1 つ(呼数に比例)・``on_dispatch`` は束の発言の数ぶん(≤ 処理中の会話の数)・
``on_close`` は終わった会話の数ぶん。体の数に比例するループは無い。
"""

from __future__ import annotations

import math
import os
import unicodedata
from statistics import NormalDist
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import numpy as np

from shibuya.core.rng import k19_counters, stream
from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS
from shibuya.engine import owner_guard as _OG
from shibuya.engine.speech.port import mora_count
from shibuya.llm.contract import NO_TARGET

__all__ = [
    "SCHEMA", "ENV", "FP_KEY", "ARM_TABLE", "ARM_MORA", "ARMS", "DEFAULT_ARM", "arm", "set_arm", "is_default",
    "RATE_DOMAIN", "JITTER_DOMAIN", "KIND_TALK", "RANK_TALK", "MORA_LEN_MEAN_S", "MORA_LEN_FAST_S", "MORA_LEN_SLOW_S",
    "N_SPEAKERS", "D2_N18", "WITHIN_CV", "WITHIN_CV_PHRASE", "FAMILIAR_FASTER", "GAP_MEAN_MS", "GAP_MEDIAN_MS",
    "SIGMA_BETWEEN", "SIGMA_WITHIN", "FAMILIAR_DELTA", "GAP_NS", "THINK_TIME_COUNTED_BY", "ANCHORS",
    "DEFAULT_CAP_PER_WINDOW", "MODALITY_FACE", "MODALITY_CHAT", "MODALITIES", "LANG_JA", "LANG_OTHER", "LANG_NONE",
    "BINS", "language_of", "person_mora_len_s", "utterance_jitter", "SpeechTiming", "ChatTiming", "QueueRouter",
    "TalkClock", "CONFIG_KEYS", "OBSERVED_KEYS", "manifest_fields", "make",
]

#: manifest の ``talk_clock`` の形の版。
SCHEMA: Final[str] = "shibuya.engine.speech_clock/1"
#: 腕の環境変数(CLI ``--talk-clock`` と同じ・指定は CLI が強い)。
ENV: Final[str] = "SHIBUYA_TALK_CLOCK"
#: 設定の指紋の鍵(腕のときだけ足す=既定のランの指紋は今のまま)。
FP_KEY: Final[str] = "talk_clock"
ARM_TABLE: Final[str] = "table"
ARM_MORA: Final[str] = "mora"
ARMS: Final[tuple[str, ...]] = (ARM_TABLE, ARM_MORA)
DEFAULT_ARM: Final[str] = ARM_TABLE

_raw = os.environ.get(ENV, "").strip().lower()
if _raw and _raw not in ARMS:
    raise ValueError(f"{ENV} は {ARMS} のどれか(いま {_raw!r})")
_ARM: str = _raw or DEFAULT_ARM
del _raw


def arm() -> str:
    """いまの腕(``table``=既定・``mora``)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--talk-clock``・試験の切替口)。組み立ての時に読む(ランの途中で変えてもそのランは変わらない)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--talk-clock は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def is_default(name: str | None = None) -> bool:
    return (_ARM if name is None else str(name)) == DEFAULT_ARM


#: 乱数の用途(人ごとの話す速さ=母集団の seed・体の番号)。
RATE_DOMAIN: Final[str] = "talk.rate"
#: 乱数の用途(発言ごとの揺れ=動きの seed・話し手・発言を作った時刻・会話の番号=TM7 (d))。
JITTER_DOMAIN: Final[str] = "talk.jitter"
#: 窓の待ち行列の事象の種類(刻みの事象 ``batching.KIND_STEP``=0 の次)と順位(同じ時刻では刻みの事象の後)。
KIND_TALK: Final[int] = 1
RANK_TALK: Final[int] = 1

# ---------------------------------------------------------------- 錨(R-111 §3 C4・R-73 §4-2 の写し=写し検査の形)
#: 日本語の日常会話のモーラの長さの平均[秒](=6.62 モーラ/秒)。石本 2024(CEJC・研究協力者 18 人・途中に間のある発話は
#: 除く)の表 1。R-111 #38 ○・§3-2 の表・R-73 #32 ◎。
MORA_LEN_MEAN_S: Final[float] = 0.151
#: 最速の話者のモーラの長さ[秒](8.06 モーラ/秒・65〜69 歳男性)。同じ表(R-111 §3-1)。
MORA_LEN_FAST_S: Final[float] = 0.124
#: 最遅の話者のモーラの長さ[秒](5.05 モーラ/秒・50〜54 歳女性)。同じ表(R-111 §3-1)。
MORA_LEN_SLOW_S: Final[float] = 0.198
#: 上の範囲の話者の数(R-111 §3-1「CEJC の 18 人」)。
N_SPEAKERS: Final[int] = 18
#: 正規の標本(大きさ 18)の範囲の期待値 d2(管理図の係数・範囲 ÷ d2 = SD の推定)。範囲から幅を出す換算(仮採用)。
D2_N18: Final[float] = 3.640
#: 話者の中の揺れの変動係数(オランダ語の自発話 58 人・20,886 句・句の長さの項なし)。Quené 2005 表 1(R-111 #42 ○)。
WITHIN_CV: Final[float] = 0.42
#: 同じ(句の長さで説明した後)。句の長さの項を入れる段で使う値(今は使わない=記録だけ)。Quené 2005(R-111 #42 ○)。
WITHIN_CV_PHRASE: Final[float] = 0.28
#: 親しい相手(家族・友人)に知らない相手より速い割合(英語 214 対 193 語/分=+10.9%・中国語 247 対 228 字/分=+8.3%)。
#: Yuan ほか 2006 表 2(R-111 #44 ○・§3-1 の再計算)。日本語の値は空欄(R-111 §3-4)。
FAMILIAR_FASTER: Final[tuple[float, float]] = (0.109, 0.083)
#: 日本語の応答の開始の間の平均[ms](10 言語で最速)。Stivers ほか 2009(R-73 #30 ◎・§4-2 の表)。
GAP_MEAN_MS: Final[int] = 7
#: 同じ中央値[ms](R-73 #30 ◎)。
GAP_MEDIAN_MS: Final[int] = 0

# ---- 錨から導いた値(式は docstring の規則 2〜5) ----
#: 人ごとのモーラの長さの対数の幅(= ln(0.198/0.124) ÷ 3.640 ≈ 0.1286)。
SIGMA_BETWEEN: Final[float] = math.log(MORA_LEN_SLOW_S / MORA_LEN_FAST_S) / D2_N18
#: 発言ごとの揺れの対数の幅(CV 0.42 の対数正規 = √ln(1+CV²) ≈ 0.4031)。
SIGMA_WITHIN: Final[float] = math.sqrt(math.log1p(WITHIN_CV * WITHIN_CV))
#: 知らない相手のモーラの長さの倍率 −1(英語と中国語の平均=0.096)。
FAMILIAR_DELTA: Final[float] = sum(FAMILIAR_FASTER) / len(FAMILIAR_FASTER)
#: 間[ns](平均 7 ms)。
GAP_NS: Final[int] = GAP_MEAN_MS * (NS_PER_SECOND // 1000)
#: 考える時間を数える側(TM3「考える時間は TM2 の側で数え、二重に数えない」=時計は間だけを足す)。
THINK_TIME_COUNTED_BY: Final[str] = "TM2(llm_bridge の t_apply・今の表 L4 0.2 秒は時計に足さない)"
#: 1 つの会話が 1 つの窓で処理する発言の数の上限(安全装置=当たったら次の窓へ持ち越して数える)。
DEFAULT_CAP_PER_WINDOW: Final[int] = 1 << 10

#: 出典の表(manifest の ``talk_clock.anchors`` に写す=写し検査の形)。
ANCHORS: Final[Mapping[str, Mapping[str, Any]]] = MappingProxyType({
    "mora_len_mean_s": MappingProxyType({"value": MORA_LEN_MEAN_S, "source": "石本 2024 表 1(CEJC 18 人)",
                                         "ref": "R-111 #38 ○・R-73 #32 ◎"}),
    "mora_len_fast_s": MappingProxyType({"value": MORA_LEN_FAST_S, "source": "石本 2024 表 1(最速 8.06 モーラ/秒)",
                                         "ref": "R-111 #38 ○"}),
    "mora_len_slow_s": MappingProxyType({"value": MORA_LEN_SLOW_S, "source": "石本 2024 表 1(最遅 5.05 モーラ/秒)",
                                         "ref": "R-111 #38 ○"}),
    "n_speakers": MappingProxyType({"value": N_SPEAKERS, "source": "石本 2024(研究協力者 18 人)", "ref": "R-111 §3-1"}),
    "within_cv": MappingProxyType({"value": WITHIN_CV, "source": "Quené 2005 表 1(句の長さの項なし)",
                                   "ref": "R-111 #42 ○"}),
    "within_cv_phrase": MappingProxyType({"value": WITHIN_CV_PHRASE, "source": "Quené 2005(句の長さで説明した後・未使用)",
                                          "ref": "R-111 #42 ○"}),
    "familiar_faster": MappingProxyType({"value": FAMILIAR_FASTER,
                                         "source": "Yuan ほか 2006 表 2(英語 +10.9%・中国語 +8.3%)",
                                         "ref": "R-111 #44 ○"}),
    "gap_mean_ms": MappingProxyType({"value": GAP_MEAN_MS, "source": "Stivers ほか 2009(日本語の平均・中央値 0 ms)",
                                     "ref": "R-73 #30 ◎"}),
    "d2_n18": MappingProxyType({"value": D2_N18, "source": "正規の標本 18 の範囲の期待値(管理図の係数 d2)",
                                "ref": "仮採用(範囲から SD への換算)"}),
})

#: 発言の道具(C1 が刺す口)。``対面``=話す(モーラ × 話す速さ)・``チャット``=打つ(値は空欄=C1)。
MODALITY_FACE: Final[str] = "対面"
MODALITY_CHAT: Final[str] = "チャット"
MODALITIES: Final[tuple[str, ...]] = (MODALITY_FACE, MODALITY_CHAT)
#: 本文の言語の判定(仮名か漢字がある=日本語・英数字だけ=他の言語=欄だけ・どちらも無い=発言にしない)。
LANG_JA: Final[str] = "ja"
LANG_OTHER: Final[str] = "other"
LANG_NONE: Final[str] = "none"

#: 計器の区切り(左閉じ・最後は上限なし)。
BINS: Final[Mapping[str, tuple[float, ...]]] = MappingProxyType({
    "utterance_mora": (0, 2, 4, 6, 8, 12, 16, 24, 32, 48, 64),
    "utterance_s": (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 20.0),
    "rate_mora_per_s": (0.0, 3.0, 4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 9.0, 11.0, 15.0),
    "conversation_s": (0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0, 600.0, 1200.0),
    "turns": (0, 1, 2, 3, 4, 5, 6, 8, 10, 15),
})

_NORM = NormalDist()
_LN_MEAN = math.log(MORA_LEN_MEAN_S)
_Z_LO = (math.log(MORA_LEN_FAST_S) - _LN_MEAN) / SIGMA_BETWEEN
_Z_HI = (math.log(MORA_LEN_SLOW_S) - _LN_MEAN) / SIGMA_BETWEEN
_P_LO = _NORM.cdf(_Z_LO)
_P_HI = _NORM.cdf(_Z_HI)
_MU_WITHIN = -0.5 * SIGMA_WITHIN * SIGMA_WITHIN


def language_of(text: str) -> str:
    """本文の言語(仮名か漢字がある=``ja``・英数字だけ=``other``・どちらも無い=``none``)。"""
    other = False
    for ch in unicodedata.normalize("NFKC", str(text)):  # 逐次: 字数ぶん(≤ 数十字)
        o = ord(ch)
        if 0x3041 <= o <= 0x3096 or 0x30A1 <= o <= 0x30FA or ch == "ー" or 0x4E00 <= o <= 0x9FFF \
                or 0x3400 <= o <= 0x4DBF or ch == "々":
            return LANG_JA
        if ch.isascii() and ch.isalnum():
            other = True
    return LANG_OTHER if other else LANG_NONE


def person_mora_len_s(seed: int | str, agent: int) -> float:
    """体 ``agent`` のモーラの長さ[秒](規則 2=切った対数正規・母集団の seed と体の番号の Philox・状態を持たない)。"""
    u = float(stream(seed, RATE_DOMAIN, *k19_counters(int(agent))).random())
    p = _P_LO + u * (_P_HI - _P_LO)
    p = min(max(p, _P_LO), _P_HI)
    z = _NORM.inv_cdf(min(max(p, 1e-15), 1.0 - 1e-15))
    z = min(max(z, _Z_LO), _Z_HI)
    return float(math.exp(_LN_MEAN + SIGMA_BETWEEN * z))


def utterance_jitter(seed: int | str, speaker: int, t_ns: int, session: int) -> float:
    """発言ごとの揺れ(規則 3=平均 1 の対数正規・CV 0.42)。鍵=話し手・発言を作った時刻[ns]・会話の番号(TM7 (d))。"""
    u = float(stream(seed, JITTER_DOMAIN, *k19_counters(int(speaker), int(t_ns), int(session) + 1)).random())
    z = _NORM.inv_cdf(min(max(u, 1e-15), 1.0 - 1e-15))  # 一様 1 語の逆関数(引く語数が決まる=10e K19 の静的な検査で安全)
    return float(math.exp(_MU_WITHIN + SIGMA_WITHIN * z))


class SpeechTiming:
    """話す道具(``対面``)の時間: 発言の長さ = モーラ数 × モーラの長さ × 揺れ × 相手の項・間 = 日本語の平均。"""

    name: str = "speech"

    @staticmethod
    def duration_ns(mora: int, mora_len_s: float, jitter: float, familiar: bool | None) -> int:
        """発言の長さ[ns](四捨五入の整数)。``familiar`` が False(知らない相手)のときだけ相手の項を掛ける。"""
        f = (1.0 + FAMILIAR_DELTA) if familiar is False else 1.0
        return int(round(float(mora) * float(mora_len_s) * float(jitter) * f * NS_PER_SECOND))

    @staticmethod
    def gap_ns() -> int:
        """発言と次の発言の間[ns](考える時間は足さない=TM2 の側)。"""
        return GAP_NS


class ChatTiming:
    """打つ道具(``チャット``)の時間=C1(チャットの会話の状態)が刺す口。値は空欄(None)=C1 で入れる。"""

    name: str = "chat"

    @staticmethod
    def typing_ns(agent: int, text: str) -> int | None:
        """打つ時間[ns](空欄)。"""
        return None

    @staticmethod
    def read_gap_ns(agent: int, text: str) -> int | None:
        """読む間[ns](空欄)。"""
        return None


#: 道具 → 時間の口。
TIMINGS: Final[Mapping[str, Any]] = MappingProxyType({MODALITY_FACE: SpeechTiming, MODALITY_CHAT: ChatTiming})


class QueueRouter:
    """全体で 1 つの時計(``engine.batching.WindowQueue``)に発言の事象を置く口(区域ごとの時計は
    ``engine.regional_clock.RegionalClock`` が同じ口を持つ)。聞こえる相手への遅れは 0(同じ時計)。"""

    def __init__(self, queue: Any) -> None:
        self.queue = queue

    def schedule(self, t_ns: Any, agents: Any, kind: int) -> np.ndarray:
        return self.queue.schedule(t_ns, agents, kind)

    def now_ns(self) -> int:
        return int(self.queue.now_ns)

    def window_end_ns(self, t_ns: int) -> int:
        """時刻 ``t_ns`` を含む窓の終わり。"""
        w = int(self.queue.width_ns)
        h = int(self.queue.head_ns)
        return h + ((int(t_ns) - h) // w + 1) * w

    def hear_delay_ns(self, t_ns: int, speaker: int, listener: int) -> int:
        return 0


def _bin(edges: Sequence[float], x: float) -> int:
    k = 0
    for i, e in enumerate(edges):  # 逐次: 区切りの数ぶん(≤ 13)
        if x >= e:
            k = i
    return k


def _new_meter() -> dict[str, Any]:
    return {
        "turns": 0, "utterances": 0, "silent": 0, "no_session": 0, "lang_other": 0, "chat_blank": 0,
        "familiar": 0, "unfamiliar": 0, "familiar_unknown": 0, "persons": 0,
        "carried": 0, "lag_ns_sum": 0, "lag_ns_max": 0, "ahead": 0, "cap_hits": 0,
        "dispatches": 0, "batch_max": 0, "batch_sum": 0, "mora_sum": 0, "speech_ns_sum": 0, "utterance_ns_max": 0,
        "gap_ns_sum": 0, "heard": 0, "cross_heard": 0, "hear_delay_ns_sum": 0, "hear_delay_ns_max": 0,
        "conversations": 0, "conv_silent": 0, "conv_open_at_end": 0, "conv_tm3_ns_sum": 0, "conv_table_s_sum": 0,
        "conv_span_s_sum": 0,
    }


#: 計器の区切りごとの数の名 → 区切り。
_HIST: Final[tuple[tuple[str, str], ...]] = (
    ("utterance_mora", "utterance_mora"), ("utterance_s", "utterance_s"), ("rate_person", "rate_mora_per_s"),
    ("rate_utterance", "rate_mora_per_s"), ("conv_tm3_s", "conversation_s"), ("conv_table_s", "conversation_s"),
    ("conv_span_s", "conversation_s"), ("turns", "turns"))

#: 会話の時計の 1 行の欄(``_tc_line`` の値の組の並び)。〔検収 M3〕最後の ``last_made_ns``=前の番を作った時刻。
_LINE = ("first_ns", "next_ns", "last_end_ns", "utterances", "speech_ns", "window", "in_window", "last_made_ns")


class TalkClock:
    """会話の時計(状態台帳の腕の行 ``TCR``・``TCC``・持ち主の名 ``talk_clock``)。腕 ``mora`` のランだけ組み立てが作る。

    〔6-3 検収 M2〕実行時の守り(3-2 の ``WindowQueue`` と同じ形=``engine.owner_guard``): 欄の代入と消去は ``AttributeError``
    (書く口は ``__init__``・``attach`` の自分の文だけ)。中身(話す速さの控え・会話の時計・予約・計器・区切りごとの数)は持ち主の
    中の辞書で書き、欄には読み取り専用の写し(``MappingProxyType``)を置く=外から中身を書くと ``TypeError``。

    Args:
        rate_seed: 人ごとの話す速さの乱数の seed(母集団の seed)。
        jitter_seed: 発言ごとの揺れの乱数の seed(動きの seed)。
        step_s: 刻みの幅[秒](今の表=会話の番 1 つの長さ)。
        rel_layer: 関係の層(親しい相手の判定=生きている辺・無ければ欄だけ)。読むだけ。
        cap_per_window: 1 つの会話が 1 つの窓で処理する発言の数の上限(安全装置)。
    """

    #: 状態台帳の腕の行の腕の名(``LedgerRow.arm``)。
    LEDGER_ARM: str = "talk-clock"
    name: str = "talk_clock"

    def __init__(self, *, rate_seed: int | str, jitter_seed: int | str, step_s: int = STEP_SECONDS,
                 rel_layer: Any = None, cap_per_window: int = DEFAULT_CAP_PER_WINDOW) -> None:
        if int(cap_per_window) < 1:
            raise ValueError(f"上限は 1 以上(いま {cap_per_window})")
        h = _OG.hidden(self)
        h["rate"], h["line"], h["pending"] = {}, {}, {}
        h["hist"] = {k: (0,) * len(BINS[b]) for k, b in _HIST}
        h["meter"] = {**_new_meter(), "hist": MappingProxyType(h["hist"])}
        with _OG.writing(self):
            self.rate_seed = rate_seed
            self.jitter_seed = jitter_seed
            self.step_ns = int(step_s) * NS_PER_SECOND
            self.rel_layer = rel_layer
            self.cap = int(cap_per_window)
            #: 体 → モーラの長さ[秒](行 TCR=母集団の seed と体から引き直せる控え・読み取り専用の写し)。
            self._tc_rate: Mapping[int, float] = MappingProxyType(h["rate"])
            #: 会話の番号 → 時計の行(``_LINE`` の並び・行 TCC・読み取り専用の写し)。
            self._tc_line: Mapping[int, tuple[int, ...]] = MappingProxyType(h["line"])
            #: 予約の番号 → 発言(会話の番号・話し手・始まり[ns]・長さ[ns]・モーラ数・聞く人の組・作った時刻[ns])(行 TCC)。
            self._tc_pending: Mapping[int, tuple[Any, ...]] = MappingProxyType(h["pending"])
            #: 計器(行 TCC・読み取り専用の写し=区切りごとの数も読み取り専用の写し)。
            self._tc_meter: Mapping[str, Any] = MappingProxyType(h["meter"])
            #: 事象を置く口(``QueueRouter`` か ``RegionalClock``・進行役が ``attach`` で置く=参照)。
            self._tc_router: Any = None

    def __setattr__(self, name: str, value: Any) -> None:
        _OG.guarded_setattr(self, name, value, "会話の時計")

    def __delattr__(self, name: str) -> None:
        _OG.guarded_delattr(self, name, "会話の時計")

    # ---- 中身の書く口(持ち主の中だけ) ----
    def _h(self) -> dict[str, Any]:
        return _OG.hidden(self)

    def _hist_add(self, key: str, edges: str, x: float) -> None:
        h = self._h()["hist"]
        v = list(h[key])
        v[_bin(BINS[edges], x)] += 1
        h[key] = tuple(v)

    # ------------------------------------------------------------------ 口
    def attach(self, router: Any) -> None:
        """事象を置く口を挿す(進行役がランの始めに 1 回)。"""
        with _OG.writing(self):
            self._tc_router = router

    def mora_len_s(self, agent: int) -> float:
        """体のモーラの長さ[秒](最初に引いた値を控える=母集団の seed と体から決まる)。"""
        a = int(agent)
        rate = self._h()["rate"]
        v = rate.get(a)
        if v is None:
            v = person_mora_len_s(self.rate_seed, a)
            rate[a] = v
            self._h()["meter"]["persons"] += 1
            self._hist_add("rate_person", "rate_mora_per_s", 1.0 / v)
        return v

    def _familiar(self, agents: Any, speaker: int, listeners: tuple[int, ...], step: int) -> bool | None:
        rel = self.rel_layer
        if rel is None or agents is None or not listeners:
            return None
        acq = rel.acquaintances(agents, int(speaker), int(step))
        return bool(np.isin(np.asarray(listeners, dtype=np.int64), acq).any())

    def on_turn(self, agents: Any, speaker: int, step: int, session: Any, text: str, *,
                modality: str = MODALITY_FACE, made_ns: int | None = None) -> int | None:
        """会話の番の答え 1 つ(``engine.systems.llm_io.utter`` から)→ 発言の事象を予約する。返り値=予約の番号(発言に
        しないときは None)。``step``=作った刻みの番号。``made_ns``=作った時刻[ns](省略=刻みの頭=今の会話の番の形。
        窓の中で次の番を回す版上げの形=発言の事象の処理の中で作るときは、その時刻を渡す=試験で使う口)。

        〔6-3 検収 M3〕同じ会話の前の番と同じ時刻に作った番(=1 回の LLM に同じ会話の番を 2 つ書かせた形)は止める
        (``RuntimeError``・会話の遅れ=持ち越しの有無によらない)。"""
        h = self._h()
        m = h["meter"]
        m["turns"] += 1
        if session is None:
            m["no_session"] += 1
            return None
        if modality not in TIMINGS:
            raise ValueError(f"発言の道具は {MODALITIES} のどれか(いま {modality!r})")
        body = str(text or "").strip()
        lang = language_of(body)
        if lang == LANG_NONE or body == NO_TARGET:  # ひと言が空か「なし」=発言にしない(1-8b の口と同じ)
            m["silent"] += 1
            return None
        sid = int(session.session_id)
        a = int(speaker)
        listeners = tuple(int(p) for p in session.participants if int(p) != a)
        made_ns = int(step) * self.step_ns if made_ns is None else int(made_ns)
        if modality == MODALITY_CHAT:
            timing = ChatTiming
            if timing.typing_ns(a, body) is None or timing.read_gap_ns(a, body) is None:
                m["chat_blank"] += 1
                return None
        line = h["line"].get(sid)
        if line is not None and int(line[7]) == made_ns:
            raise RuntimeError(f"1 つの会話の中の番を同じ時刻にまとめて作った(会話 {sid}・時刻 {made_ns} ns=TM3 の違反"
                               "=1 回の LLM に会話の番を 2 つ書かせない)")
        planned = made_ns if line is None else int(line[1])
        if lang == LANG_OTHER:  # 欄だけ=今の表(刻み 1 つ)でつなぐ
            mora = 0
            dur = self.step_ns
            m["lang_other"] += 1
        else:
            mora = int(mora_count(body))
            fam = self._familiar(agents, a, listeners, int(step))
            key = "familiar_unknown" if fam is None else ("familiar" if fam else "unfamiliar")
            m[key] += 1
            dur = SpeechTiming.duration_ns(mora, self.mora_len_s(a),
                                           utterance_jitter(self.jitter_seed, a, made_ns, sid), fam)
        router = self._tc_router
        if router is None:
            raise RuntimeError("会話の時計に事象を置く口が無い(進行役の attach の前に会話の番が来た)")
        now = int(router.now_ns())
        at = max(planned, now)
        if planned < now:
            lag = now - planned
            m["carried"] += 1
            m["lag_ns_sum"] += lag
            m["lag_ns_max"] = max(int(m["lag_ns_max"]), lag)
        elif planned > now:
            m["ahead"] += 1
        seq = int(router.schedule(at, a, KIND_TALK)[0])
        h["pending"][seq] = (sid, a, planned, int(dur), mora, listeners, made_ns)
        gap = SpeechTiming.gap_ns()
        first = planned if line is None else int(line[0])
        win, inw = (-1, 0) if line is None else (int(line[5]), int(line[6]))
        n_utt = 0 if line is None else int(line[3])
        sp = 0 if line is None else int(line[4])
        h["line"][sid] = (first, planned + int(dur) + gap, planned + int(dur), n_utt, sp, win, inw, made_ns)
        return seq

    def on_dispatch(self, t_ns: int, agents: np.ndarray, seqs: np.ndarray) -> None:
        """発言の事象の束(同じ時刻の ``talk`` の続き)を処理する。同じ会話の発言が 2 つあれば止める(規則 7)。"""
        h = self._h()
        m = h["meter"]
        sids: list[int] = []
        router = self._tc_router
        for s in np.asarray(seqs, dtype=np.int64).tolist():  # 逐次: 束の発言の数ぶん
            row = h["pending"].pop(int(s), None)
            if row is None:
                continue
            sid, a, planned, dur, mora, listeners, made_ns = row
            if sid in sids:
                raise RuntimeError(f"1 つの会話の中の発言を同じ束に入れた(会話 {sid}・時刻 {t_ns} ns=TM3 の違反)")
            line = h["line"].get(sid)
            win = int(router.window_end_ns(int(t_ns))) if router is not None else int(t_ns)
            if line is not None and int(line[5]) == win and int(line[6]) >= self.cap:  # 規則 8 の上限
                m["cap_hits"] += 1
                seq2 = int(router.schedule(win, a, KIND_TALK)[0])
                h["pending"][seq2] = row
                continue
            sids.append(int(sid))
            m["utterances"] += 1
            m["mora_sum"] += int(mora)
            m["speech_ns_sum"] += int(dur)
            m["gap_ns_sum"] += GAP_NS
            m["utterance_ns_max"] = max(int(m["utterance_ns_max"]), int(dur))
            self._hist_add("utterance_mora", "utterance_mora", float(mora))
            self._hist_add("utterance_s", "utterance_s", dur / NS_PER_SECOND)
            if mora > 0 and dur > 0:
                self._hist_add("rate_utterance", "rate_mora_per_s", mora * NS_PER_SECOND / dur)
            for lis in listeners:  # 逐次: 聞く人の数ぶん(≤ 2)
                m["heard"] += 1
                d = int(router.hear_delay_ns(int(t_ns), int(a), int(lis))) if router is not None else 0
                if d > 0:
                    m["cross_heard"] += 1
                    m["hear_delay_ns_sum"] += d
                    m["hear_delay_ns_max"] = max(int(m["hear_delay_ns_max"]), d)
            if line is not None:
                inw = int(line[6]) + 1 if int(line[5]) == win else 1
                h["line"][sid] = (line[0], line[1], line[2], int(line[3]) + 1, int(line[4]) + int(dur), win, inw,
                                  line[7])
        if sids:
            m["dispatches"] += 1
            m["batch_sum"] += len(sids)
            m["batch_max"] = max(int(m["batch_max"]), len(sids))

    def on_close(self, sessions: Sequence[Any]) -> None:
        """終わった会話(``ConversationManager.step`` の戻り)の長さを数えて時計の行を消す。"""
        h = self._h()
        m = h["meter"]
        step_s = self.step_ns / NS_PER_SECOND
        for s in sessions:  # 逐次: 終わった会話の数ぶん
            sid = int(s.session_id)
            line = h["line"].pop(sid, None)
            turns = int(sum(int(v) for v in dict(s.calls).values()))
            table_s = turns * step_s
            span_s = max(0, int(s.closed_tick) - int(s.opened_tick)) * step_s
            m["conversations"] += 1
            m["conv_table_s_sum"] += table_s
            m["conv_span_s_sum"] += span_s
            self._hist_add("conv_table_s", "conversation_s", table_s)
            self._hist_add("conv_span_s", "conversation_s", span_s)
            self._hist_add("turns", "turns", float(turns))
            if line is None:
                m["conv_silent"] += 1
                self._hist_add("conv_tm3_s", "conversation_s", 0.0)
                continue
            tm3 = int(line[2]) - int(line[0])
            m["conv_tm3_ns_sum"] += tm3
            self._hist_add("conv_tm3_s", "conversation_s", tm3 / NS_PER_SECOND)

    # ------------------------------------------------------------------ 計器
    def observed(self) -> dict[str, Any]:
        """manifest の ``talk_clock`` の観測の子。"""
        m = self._tc_meter
        out = {k: (int(v) if isinstance(v, (int, np.integer)) else float(v)) for k, v in m.items() if k != "hist"}
        out["conv_open_at_end"] = len(self._tc_line)
        out["pending_at_end"] = len(self._tc_pending)
        n_u = max(1, int(m["utterances"]))
        out["mean_utterance_s"] = round(int(m["speech_ns_sum"]) / n_u / NS_PER_SECOND, 6)
        out["mean_mora"] = round(int(m["mora_sum"]) / n_u, 6)
        out["mean_rate_mora_per_s"] = (round(int(m["mora_sum"]) * NS_PER_SECOND / int(m["speech_ns_sum"]), 6)
                                       if int(m["speech_ns_sum"]) else None)
        rates = [1.0 / v for v in self._tc_rate.values()]
        out["person_rate_mean"] = round(sum(rates) / len(rates), 6) if rates else None
        out["person_rate_min"] = round(min(rates), 6) if rates else None
        out["person_rate_max"] = round(max(rates), 6) if rates else None
        n_c = int(m["conversations"]) - int(m["conv_silent"])
        out["mean_conv_tm3_s"] = round(int(m["conv_tm3_ns_sum"]) / max(1, n_c) / NS_PER_SECOND, 6)
        out["mean_conv_table_s"] = round(float(m["conv_table_s_sum"]) / max(1, int(m["conversations"])), 6)
        out["mean_conv_span_s"] = round(float(m["conv_span_s_sum"]) / max(1, int(m["conversations"])), 6)
        out["hist"] = {k: list(v) for k, v in m["hist"].items()}
        return out


#: manifest の ``talk_clock`` の設定の子と観測の子(``engine.manifest_sections`` の混ざった辞書)。
CONFIG_KEYS: Final[tuple[str, ...]] = (
    "schema", "arm", "anchors", "sigma_between", "sigma_within", "familiar_delta", "gap_ns", "think_time",
    "mora_rule", "modalities", "cap_per_window", "kind", "rank", "bins")
OBSERVED_KEYS: Final[tuple[str, ...]] = (
    *(k for k in _new_meter() if k != "hist"), "pending_at_end", "mean_utterance_s", "mean_mora",
    "mean_rate_mora_per_s", "person_rate_mean", "person_rate_min", "person_rate_max", "mean_conv_tm3_s",
    "mean_conv_table_s", "mean_conv_span_s", "hist")


def manifest_fields(clock: TalkClock | None) -> dict[str, Any] | None:
    """manifest の ``talk_clock``(腕 mora のランだけ・既定の腕は None=節を出さない)。"""
    if clock is None:
        return None
    cfg: dict[str, Any] = {
        "schema": SCHEMA, "arm": ARM_MORA,
        "anchors": {k: {kk: (list(vv) if isinstance(vv, tuple) else vv) for kk, vv in v.items()}
                    for k, v in ANCHORS.items()},
        "sigma_between": round(SIGMA_BETWEEN, 9), "sigma_within": round(SIGMA_WITHIN, 9),
        "familiar_delta": round(FAMILIAR_DELTA, 9), "gap_ns": GAP_NS, "think_time": THINK_TIME_COUNTED_BY,
        "mora_rule": "engine.speech.port.mora_count(仮名の数の近似・漢字 2 拍)", "modalities": list(MODALITIES),
        "cap_per_window": int(clock.cap), "kind": KIND_TALK, "rank": RANK_TALK,
        "bins": {k: list(v) for k, v in BINS.items()},
    }
    return {**cfg, **clock.observed()}


def make(*, pop_seed: int | str, seed: int | str, step_s: int, rel_layer: Any) -> TalkClock | None:
    """組み立ての口: 腕 mora のときだけ会話の時計を作る(既定 table は None=今の道)。"""
    if _ARM != ARM_MORA:
        return None
    return TalkClock(rate_seed=pop_seed, jitter_seed=seed, step_s=int(step_s), rel_layer=rel_layer)
