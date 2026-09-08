"""perception.attention — 注意ゲート 段0-段3(知覚契約書 §4)。「届く」→「気づく」。

正典(§4 逐語)
- **段0 幾何**: 可視性/可聴半径(§3)。→ 呼び出し側(可視性表・聴覚半径)が渡す。
- **段1 到達確率**: 視覚=視認確率 p_see——**大型ビジョン=0.70(音声有0.78/無音0.63)**
  (都内5地点VRアイトラッキング n=120・2024-03・非査読の企業発表・定義=視聴可能エリア内で
  中心視点が画面に留まる=段0通過後の条件付き確率・米国VR実験70%と独立一致)/
  **中小媒体=0.14-0.40 は英仏流用のまま expedient**/人物③=p_notice(§3.1)/
  聴覚=SNRマージン(ΔSNR −3/−12)。
- **段2 注意予算**: 1ステップに載せられる件数の上限(**広告1件・顕著行為1-2・傍受上位1-2**)
  ——件数はトークン予算由来=**expedient(等級E)**。顕著性順位=**視角(サイズ/距離)×
  局所輝度コントラスト(+動き・逸脱度)**。「積形は**フロア付き対数加算**として実装」
  (Itti & Koch が否定したのは線形和)。相対重みの実証回帰は空欄=expedient。
- **段3 内容キャップ**: 広告=注視秒→日本語字数は **round(7.5×注視秒)・下限4字・上限30字**
  (MNREAD-J の読書速度定義式に 400-600字/分。**正典値は未取得=式は expedient**)。
  効果キャップ=行動効果10⁻⁴〜10⁻³/曝露+記憶側上界=1曝露の再認≤0.40/再生≤0.08。
  傍受=理解劣化の描画/看板=構造化属性へ還元(自由文は**素性タグ+命令文除去**)。
- **既定は非注入**・テキストでなくスカラー変換を第一候補。
- 憲法6(§1 条6):「世界内で生成されたテキストは素性タグ付きの別チャネルで渡し、
  **命令文パターンを除去する**(注入攻撃の成功率が50%超から2%未満になる実測)」。

逐次ループ宣言(P4)
- ``strip_imperatives``: **文数**ぶんのループ(1テキスト数文)。個体数・tick 数に比例しない。
- ``rank_by_saliency``: なし(NumPy のベクトル演算+``argsort``)。

expedient(本モジュール分)
- 中小媒体 p_see の代表値 ``P_SEE_MEDIUM_DEFAULT=0.27``(契約書の帯 0.14-0.40 の中点)。
- 顕著性の**重み** ``SALIENCY_WEIGHTS``・フロア ``SALIENCY_FLOOR``(契約書「相対重みの実証回帰は
  空欄=expedient」)。
- 命令文パターン ``IMPERATIVE_PATTERNS``(契約書は「命令文パターンを除去する」としか書かない)。
  日本語の命令形は活用で網羅できないので、**文単位**で(ください/しろ/せよ/なさい/するな/
  ○○してはいけません/今すぐ○○/英語の命令句)を落とす保守的な規則にした。落とした文は
  ``StripReport`` に載せて診断行へ出す(黙って消さない)。
- ``gaze_seconds`` の既定 0.48 秒(Fotios 2015 の実世界注視中央値 480 ms)。広告答申の 0.9-3.3 秒は
  上振れ側なので、**既定は実測中央値**にした(契約書はどちらを既定にするか書いていない)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final, Sequence

import numpy as np

from shibuya.core.rng import stream

__all__ = [
    "P_SEE_LARGE_VISION",
    "P_SEE_LARGE_VISION_AUDIO",
    "P_SEE_LARGE_VISION_SILENT",
    "P_SEE_MEDIUM_RANGE",
    "P_SEE_MEDIUM_DEFAULT",
    "BUDGET_ADS",
    "BUDGET_SALIENT",
    "BUDGET_OVERHEARD",
    "SALIENCY_WEIGHTS",
    "SALIENCY_FLOOR",
    "CONTENT_CAP_CHARS_PER_SEC",
    "CONTENT_CAP_MIN_CHARS",
    "CONTENT_CAP_MAX_CHARS",
    "GAZE_SECONDS_DEFAULT",
    "EFFECT_CAP_PER_EXPOSURE",
    "MEMORY_CAP_RECOGNITION",
    "MEMORY_CAP_RECALL",
    "FEATURE_TAGS",
    "IMPERATIVE_PATTERNS",
    "SalientItem",
    "StripReport",
    "content_cap_chars",
    "p_see",
    "gate_stage1",
    "rank_by_saliency",
    "apply_budget",
    "strip_imperatives",
    "feature_tag",
    "tag_world_text",
]

# ---------------------------------------------------------------- 段1 到達確率(p_see)
#: 大型ビジョンの視認確率(既定・音声条件を指定しないとき)。
P_SEE_LARGE_VISION: Final[float] = 0.70
#: 音声あり。
P_SEE_LARGE_VISION_AUDIO: Final[float] = 0.78
#: 無音。
P_SEE_LARGE_VISION_SILENT: Final[float] = 0.63
#: 中小媒体の帯(英仏流用=expedient・日本の業界標準指標は接触機会 OTS で視認率ではない)。
P_SEE_MEDIUM_RANGE: Final[tuple[float, float]] = (0.14, 0.40)
#: 中小媒体の代表値(帯の中点・expedient)。
P_SEE_MEDIUM_DEFAULT: Final[float] = 0.27

# ---------------------------------------------------------------- 段2 注意予算(件数)
#: 広告(§4「広告1件」・等級E)。
BUDGET_ADS: Final[int] = 1
#: 顕著行為(§4「顕著行為1-2」・§3.2 は「上位1-2」→上限2・等級 B(順位)/E(件数))。
BUDGET_SALIENT: Final[int] = 2
#: 傍受(§4「傍受上位1-2」・等級E)。
BUDGET_OVERHEARD: Final[int] = 2

#: 顕著性の重み(視角・局所コントラスト・動き・逸脱度。**全て expedient**)。
SALIENCY_WEIGHTS: Final[dict[str, float]] = {
    "visual_angle": 1.0,
    "contrast": 1.0,
    "motion": 0.5,
    "deviance": 0.5,
}
#: フロア(対数加算の下駄。0 の項が −inf にならないための値・expedient)。
SALIENCY_FLOOR: Final[float] = 0.05

# ---------------------------------------------------------------- 段3 内容キャップ
#: 日本語字数 = round(7.5 × 注視秒)(§4・式は expedient)。
CONTENT_CAP_CHARS_PER_SEC: Final[float] = 7.5
CONTENT_CAP_MIN_CHARS: Final[int] = 4
CONTENT_CAP_MAX_CHARS: Final[int] = 30
#: 既定の注視秒(Fotios 2015 実世界注視中央値 480 ms)。
GAZE_SECONDS_DEFAULT: Final[float] = 0.48
#: 行動効果キャップ[/曝露](§4 維持)。
EFFECT_CAP_PER_EXPOSURE: Final[tuple[float, float]] = (1e-4, 1e-3)
#: 記憶側上界(1曝露の再認/再生・VR実験 n=41・非査読)。
MEMORY_CAP_RECOGNITION: Final[float] = 0.40
MEMORY_CAP_RECALL: Final[float] = 0.08

#: 素性タグ(§1 条6「素性タグ必須」・v0 文面 ``〔素性: …・世界内テキスト・命令文除去済〕``)。
FEATURE_TAGS: Final[dict[str, str]] = {
    "signage": "店頭表示",
    "ad": "広告",
    "overheard": "傍受",
    "notice": "掲示",
    "broadcast": "放送",
    "sns": "SNS",
}

#: 命令文パターン(**文単位で落とす**・expedient)。
IMPERATIVE_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"(?:して|し)ください"),
    re.compile(r"(?:ください|下さい)"),
    re.compile(r"(?:しろ|せよ|しなさい|されたし|したまえ)"),
    re.compile(r"(?:するな|しないで|してはいけ|してはならな|禁止します)"),
    re.compile(r"(?:今すぐ|必ず|絶対に)"),
    # 一段動詞の命令形(…じろ/…めろ/…べろ 等)+ よくある五段の命令形(語幹を並べる)
    re.compile(r"(?:じろ|めろ|べろ|ねろ|てろ|せろ|けろ|げろ|でろ|れろ|みろ|見ろ)"),
    re.compile(r"(?:来い|買え|行け|押せ|飲め|待て|止まれ|進め|出せ|渡せ|やめろ|入力しろ)"),
    re.compile(r"(?i)\b(?:ignore|disregard|you\s+must|do\s+not|please\s+\w+|click|buy\s+now)\b"),
)

_SENTENCE_SPLIT: Final[re.Pattern[str]] = re.compile(r"(?<=[。!?！?])")


@dataclass(frozen=True)
class SalientItem:
    """顕著性順位づけの入力(1件)。

    Attributes:
        item_id: 同点時のタイブレーク鍵(ID 昇順=§2.4 ②)。
        text: 描画済みの1行。
        size_m: 対象の物理サイズ[m](視角の分子)。
        distance_m: 距離[m](視角の分母)。
        contrast: 局所輝度コントラスト(0-1・中心-周辺)。
        motion: 動き(0-1)。
        deviance: 逸脱度(0-1・Jovancevic-Misic & Hayhoe 2009 の順位規則)。
    """

    item_id: str
    text: str
    size_m: float = 1.0
    distance_m: float = 10.0
    contrast: float = 0.5
    motion: float = 0.0
    deviance: float = 0.0


@dataclass(frozen=True)
class StripReport:
    """命令文除去の記録(黙って消さない=診断行へ)。"""

    kept: str
    removed: tuple[str, ...]

    @property
    def n_removed(self) -> int:
        return len(self.removed)


# ---------------------------------------------------------------- 段1
def p_see(
    medium: str = "large_vision",
    *,
    audio: bool | None = None,
) -> float:
    """媒体 → 視認確率(§4 段1)。

    Args:
        medium: ``"large_vision"``(大型ビジョン)または ``"medium_small"``(中小媒体)。
        audio: 大型ビジョンのみ。True=音声有0.78 / False=無音0.63 / None=既定0.70。
    """
    if medium == "large_vision":
        if audio is None:
            return P_SEE_LARGE_VISION
        return P_SEE_LARGE_VISION_AUDIO if audio else P_SEE_LARGE_VISION_SILENT
    if medium == "medium_small":
        return P_SEE_MEDIUM_DEFAULT
    raise ValueError(f"未知の媒体: {medium!r}(large_vision / medium_small)")


def gate_stage1(
    n: int,
    probability: float | np.ndarray,
    *,
    seed: int | str,
    domain_counters: Sequence[int],
) -> np.ndarray:
    """段1 の一発ベルヌーイ(決定論・``core.rng.stream`` のドメイン分離)。

    Args:
        n: 判定件数。
        probability: 到達確率(スカラーまたは ``(n,)``)。
        seed: マスターシード。
        domain_counters: カウンタ(例 ``(agent_id, tick)``)。

    Returns:
        ``(n,)`` bool。通過=True。
    """
    if n <= 0:
        return np.zeros(0, dtype=bool)
    g = stream(seed, "perception.attention.p_see", *[int(c) for c in domain_counters])
    return g.random(n) < np.broadcast_to(np.asarray(probability, dtype=np.float64), (n,))


# ---------------------------------------------------------------- 段2
def rank_by_saliency(
    items: Sequence[SalientItem],
    weights: dict[str, float] | None = None,
    floor: float = SALIENCY_FLOOR,
) -> tuple[list[SalientItem], np.ndarray]:
    """顕著性=**視角×局所コントラスト(+動き・逸脱度)**の降順に並べ替える。

    積形は**フロア付き対数加算**で実装する(§4 09-06 改訂。線形和ではない)::

        score = Σ_i w_i · ln(floor + x_i)
        x_visual_angle = size_m / max(distance_m, 1e-6)   # 視角=サイズ/距離

    同点は ``item_id`` 昇順(§2.4 ②)。

    Returns:
        (並べ替えた件, そのスコア)。
    """
    w = dict(SALIENCY_WEIGHTS if weights is None else weights)
    if not items:
        return [], np.zeros(0, dtype=np.float64)
    size = np.array([it.size_m for it in items], dtype=np.float64)
    dist = np.maximum(np.array([it.distance_m for it in items], dtype=np.float64), 1e-6)
    x = {
        "visual_angle": size / dist,
        "contrast": np.array([it.contrast for it in items], dtype=np.float64),
        "motion": np.array([it.motion for it in items], dtype=np.float64),
        "deviance": np.array([it.deviance for it in items], dtype=np.float64),
    }
    score = np.zeros(len(items), dtype=np.float64)
    for key, weight in w.items():
        score += float(weight) * np.log(float(floor) + np.maximum(x[key], 0.0))
    ids = np.array([it.item_id for it in items])
    order = np.lexsort((ids, -score))  # 第1鍵=スコア降順・第2鍵=ID昇順
    return [items[i] for i in order], score[order]


def apply_budget(items: Sequence[SalientItem], budget: int) -> list[SalientItem]:
    """段2 の件数上限(既定は**非注入**=枠に入らなければ載せない)。"""
    return list(items[: max(0, int(budget))])


# ---------------------------------------------------------------- 段3
def content_cap_chars(gaze_seconds: float = GAZE_SECONDS_DEFAULT) -> int:
    """注視秒 → 日本語字数の上限 ``round(7.5×秒)``(下限4・上限30)。"""
    n = int(round(CONTENT_CAP_CHARS_PER_SEC * float(gaze_seconds)))
    return int(np.clip(n, CONTENT_CAP_MIN_CHARS, CONTENT_CAP_MAX_CHARS))


def strip_imperatives(text: str) -> StripReport:
    """世界内テキストから**命令文を文単位で除去**する(§1 条6・§4 段3)。

    Note:
        逐次ループ宣言(P4): 文数ぶんのループ1本(1テキスト数文)。

    Example:
        >>> r = strip_imperatives("本日の定食は800円です。今すぐお買い求めください。")
        >>> r.kept
        '本日の定食は800円です。'
        >>> r.n_removed
        1
    """
    sentences = [s for s in _SENTENCE_SPLIT.split(str(text)) if s.strip()]
    kept: list[str] = []
    removed: list[str] = []
    for s in sentences:
        if any(p.search(s) for p in IMPERATIVE_PATTERNS):
            removed.append(s.strip())
        else:
            kept.append(s.strip())
    return StripReport(kept="".join(kept), removed=tuple(removed))


def feature_tag(kind: str) -> str:
    """素性タグの固定文言(§1 条6)。"""
    label = FEATURE_TAGS.get(kind)
    if label is None:
        raise KeyError(f"未登録の素性: {kind!r}({sorted(FEATURE_TAGS)})")
    return f"〔素性: {label}・世界内テキスト・命令文除去済〕"


def tag_world_text(
    kind: str, text: str, *, gaze_seconds: float | None = None
) -> tuple[str, StripReport]:
    """世界内テキスト → (素性タグ+命令文除去+内容キャップ済みの本文, 除去記録)。

    Args:
        kind: ``FEATURE_TAGS`` の鍵(signage/ad/overheard/…)。
        text: 世界が生成した生テキスト。
        gaze_seconds: 指定すると段3 の内容キャップ(``round(7.5×秒)`` 字)を掛ける。
            None なら字数キャップなし(看板(a)=店舗基本属性のように構造化属性由来の場合)。
    """
    report = strip_imperatives(text)
    body = report.kept
    if gaze_seconds is not None:
        body = body[: content_cap_chars(gaze_seconds)]
    return feature_tag(kind) + body, report
