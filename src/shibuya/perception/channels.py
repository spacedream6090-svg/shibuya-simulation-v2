"""perception.channels — チャネル別トークン上限表(知覚契約書 §3.2)と有界化(切り詰め)。

正典(§3.2 の表を**逐語で**移したもの。根拠等級 A〜E つき)
    | ブロック | 内訳 | tok | 等級 |
    | B5 220 | 近接人物 上位k(密度逓減3/2/1)×33 | 100 | A(k)/C(33tok→25をablation) |
    |        | 内受容(満腹/体力/体感温度)        |  40 | C |
    |        | 自己状態・所持・直近行動            |  65 | E |
    |        | 被注視                              |  15 | E |
    | B2 150 | 近接路面・通行可能性(<4 m)        |  40 | A |
    |        | 店舗・施設 可視物上位3×20          |  60 | C |
    |        | 看板・広告面1件                     |  25 | C |
    |        | 地物・ランドマーク・出口            |  25 | E |
    | B4 60  | 密度スカラー+流れ方向              |  25 | A |
    |        | 暗騒音段階                          |  10 | D |
    |        | 顕著行為 上位1-2                    |  25 | B(順位)/E(件数) |
    | B4b 40 | 直近サブセルの詳細                  |  40 | C |

§3.2 の宣言(反対証拠の明記)も本モジュールに写す:
    「B5 220>B2 150 は**滞留時間の再現ではなく、クリティカル注視に基づく意図的な歪み**である」。
そして §3.2 の**義務 ablation**「固定枠 vs 同一総トークンの単一ランキング(最近性×重要度×
関連性)」を ``BudgetMode`` で切り替える(第1陣 ablation ①)。本モジュールは
**池の予算**(``pool_token_budget``= そのブロック群のチャネル上限の総和=同一総トークン)・
**チャネル別の顕著性の既定素性**(``RANKING_PRIORS``)・**順位順の打ち切り**
(``take_within_pool``)を持ち、顕著性の計算そのものは ``attention.rank_by_saliency``、
描画への差し込みは ``renderer`` が行う(層内の役割分担)。

逐次ループ宣言(P4): ``truncate_lines``= **行数**ぶんのループ(1チャネル数行)。個体数に比例しない。

expedient(本モジュール分)
- トークン見積り ``estimate_tokens`` = **UTF-8 文字数 ÷ 2**(最低1)。``llm.estimate_tokens`` と
  同一規約だが、層契約(perception と llm は同層=相互 import 禁止)のため**二重定義**。
  値の一致は ``tests/perception/test_channels.py`` が文字列標本で守る。
- 切り詰めは**行単位**(行の途中で切らない)。契約書は上限しか与えていない。行を落とすときは
  末尾から落とす(前の行ほど順位が高い=順位づけは呼び出し側の責任)。
- ``BudgetMode.SINGLE_RANKING`` は**チャネル別の枠(上限 tok と件数)を捨て**、群予算だけを
  守る実装。``RANKING_PRIORS`` の素性(視角・コントラスト・動き・逸脱度)は全て自前で、
  §4 の顕著性が視覚の式である一方 B5 の内受容・自己状態は非視覚なので「視角=1.0」を
  内的信号の既定に置いた(登録簿=実装計画書 §8)。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, Mapping, Sequence

__all__ = [
    "estimate_tokens",
    "Grade",
    "ChannelLimit",
    "CHANNEL_LIMITS",
    "CHANNEL_BY_ID",
    "block_channel_total",
    "BudgetMode",
    "RankingPrior",
    "RANKING_PRIORS",
    "RANKING_POOL_BLOCKS",
    "pool_token_budget",
    "take_within_pool",
    "truncate_lines",
    "TruncationReport",
    "INTENTIONAL_DISTORTION_NOTE",
]

#: §3.2 の「宣言(反対証拠の明記)」。設計意図を**コードに残す**(消したら契約違反)。
INTENTIONAL_DISTORTION_NOTE: Final[str] = (
    "視線滞留では物体・環境37-56%>路面24-51%>人3-21%(Fotios 2014 Table 2)。"
    "B5 220>B2 150 は滞留時間の再現ではなく、クリティカル注視"
    "(近い路面<4 m と遠くの人>4 m=意思決定関連度)に基づく意図的な歪みである。"
)


def estimate_tokens(text: str) -> int:
    """粗いトークン数見積り(expedient: UTF-8 文字数 ÷ 2、最低 1)。

    ``llm.estimate_tokens`` と**同一規約の二重定義**(層契約により import できない)。
    """
    return max(1, len(text) // 2)


class Grade(str, Enum):
    """根拠等級(知覚契約書 §3.2 凡例)。"""

    A = "A"  # 査読済み実測が直接支持
    B = "B"  # 間接支持または非査読一次実測
    C = "C"  # 自前実測か推論
    D = "D"  # 慣行
    E = "E"  # expedient(感度試験で「結果を駆動していない」証明が必要)

    @property
    def mechanism(self) -> bool:
        """A/B は mechanism 扱い、C/D/E は expedient 扱い(CLAUDE.md §4)。"""
        return self in (Grade.A, Grade.B)


@dataclass(frozen=True)
class ChannelLimit:
    """1チャネルの上限(§3.2 の表の1行)。

    Attributes:
        channel_id: ``"B5.near_person"`` 形式(``templates.TEMPLATES`` の接頭辞と対応)。
        block: 所属ブロック(B2/B4/B4b/B5)。
        name: 表の「内訳」列。
        tokens: 表の「tok」列(**上限**)。
        grade: 根拠等級。
        basis: 表の「根拠」列(逐語)。
        max_items: 件数の上限(表に件数が書いてある行のみ。None=件数上限なし)。
        ablation: 予約されている ablation(§8)。
    """

    channel_id: str
    block: str
    name: str
    tokens: int
    grade: Grade
    basis: str
    max_items: int | None = None
    ablation: str = ""

    @property
    def tag(self) -> str:
        return "mechanism" if self.grade.mechanism else "expedient"


#: §3.2 の表(**行の追加/削除は契約書の改版**)。
CHANNEL_LIMITS: Final[tuple[ChannelLimit, ...]] = (
    # ---- B5 220 ----
    ChannelLimit("B5.near_person", "B5", "近接人物 上位k(密度逓減3/2/1)×33", 100, Grade.A,
                 "Cowan 3-5チャンク・MOT 3-4・注視確率0.86・v1実測近接3人",
                 max_items=3, ablation="近接1人あたり33→25 tok / k逓減 vs 固定3"),
    ChannelLimit("B5.intero", "B5", "内受容(満腹/体力/体感温度)", 40, Grade.C,
                 "AgentSocietyがneedsを中核に置く先行例・配分量の根拠なし", max_items=3),
    ChannelLimit("B5.self", "B5", "自己状態・所持・直近行動", 65, Grade.E,
                 "エンジン上の必要"),
    ChannelLimit("B5.watched", "B5", "被注視", 15, Grade.E,
                 "社会的創発の素地(安価)", max_items=1),
    # ---- B2 150 ----
    ChannelLimit("B2.ground", "B2", "近接路面・通行可能性(<4 m)", 40, Grade.A,
                 "near path (<4 m) … critical・クリティカル注視 近路面19.5%(最大)",
                 max_items=1),
    ChannelLimit("B2.visible", "B2", "店舗・施設 可視物上位3×20", 60, Grade.C,
                 "v1プローブ(可視3件)のみ", max_items=3),
    ChannelLimit("B2.signage", "B2", "看板・広告面1件", 25, Grade.C,
                 "件数1はexpedient・p_see/内容キャップは§4", max_items=1),
    ChannelLimit("B2.landmark", "B2", "地物・ランドマーク・出口", 25, Grade.E,
                 "根拠なし", max_items=2),
    # ---- B4 60 ----
    ChannelLimit("B4.density", "B4", "密度スカラー+流れ方向", 25, Grade.A,
                 "ensemble perception(個体化枠を消費しない)", max_items=1),
    ChannelLimit("B4.noise", "B4", "暗騒音段階", 10, Grade.D,
                 "段階化は妥当・段数の根拠なし", max_items=1),
    ChannelLimit("B4.salient", "B4", "顕著行為 上位1-2", 25, Grade.B,
                 "順位(逸脱度優先)=Jovancevic-Misic & Hayhoe 2009/件数=予算由来",
                 max_items=2, ablation="件数±1"),
    # ---- B4b 40 ----
    ChannelLimit("B4b.near", "B4b", "直近サブセルの詳細(遮蔽・段差・行列)", 40, Grade.C,
                 "構造はCivRealm同型・量は根拠なし", max_items=2),
)

#: ``channel_id`` → 行。
CHANNEL_BY_ID: Final[Mapping[str, ChannelLimit]] = {c.channel_id: c for c in CHANNEL_LIMITS}


def block_channel_total(block: str) -> int:
    """あるブロックのチャネル上限の合計(§3.2 の「| ブロック | 内訳 |」の縦計)。"""
    return sum(c.tokens for c in CHANNEL_LIMITS if c.block == block)


class BudgetMode(str, Enum):
    """§3.2 の**義務 ablation**「固定枠 vs 単一ランキング」の切替。"""

    FIXED_SLOTS = "fixed_slots"  # 既定=チャネル別固定枠(§3.2 の表)
    SINGLE_RANKING = "single_ranking"  # ablation ①=枠を捨て総トークンだけ守る

    @classmethod
    def parse(cls, value: "str | BudgetMode") -> "BudgetMode":
        """CLI 語(``fixed``/``ranking``)と Enum 値の両方を受ける(既定=``fixed``)。

        Example:
            >>> BudgetMode.parse("ranking") is BudgetMode.SINGLE_RANKING
            True
            >>> BudgetMode.parse("fixed_slots") is BudgetMode.FIXED_SLOTS
            True
        """
        if isinstance(value, cls):
            return value
        key = str(value).strip().lower()
        table = {
            "fixed": cls.FIXED_SLOTS,
            "fixed_slots": cls.FIXED_SLOTS,
            "ranking": cls.SINGLE_RANKING,
            "single_ranking": cls.SINGLE_RANKING,
        }
        got = table.get(key)
        if got is None:
            raise ValueError(f"未知の budget_mode: {value!r}({sorted(table)})")
        return got


# ------------------------------------------------------------------ ablation ①(単一ランキング)
@dataclass(frozen=True)
class RankingPrior:
    """単一ランキングでチャネルに与える顕著性の既定素性(**全て expedient**)。

    ``attention.SalientItem`` の素性(視角=``size_m``/``distance_m``・局所コントラスト・
    動き・逸脱度)へそのまま渡す。§4 の顕著性は**視覚**の式なので、内受容・自己状態のような
    非視覚チャネルは「視角=1.0(1 m の対象を 1 m で見る)」を内的信号の既定として置いた。
    契約書 §3.2 の語(最近性×重要度×関連性)への写像は登録簿(実装計画書 §8)に書く。
    """

    size_m: float
    distance_m: float
    contrast: float
    motion: float = 0.0
    deviance: float = 0.0


#: チャネル → 既定の顕著性素性(**expedient**・実測の距離/逸脱度がある項目は呼び出し側が上書き)。
RANKING_PRIORS: Final[Mapping[str, RankingPrior]] = {
    # ---- セル依存(B2/B4/B4b) ----
    "B2.ground": RankingPrior(4.0, 2.0, 0.5),            # 近路面 <4 m(§3.2 の等級A行)
    "B2.visible": RankingPrior(6.0, 20.0, 0.5, 0.1),     # 店頭
    "B2.signage": RankingPrior(2.0, 12.0, 0.8, 0.2),     # 看板=高輝度
    "B2.landmark": RankingPrior(25.0, 100.0, 0.4),       # 遠くの大きい物
    "B4.density": RankingPrior(20.0, 15.0, 0.3, 0.6),    # 群集場(ensemble)
    "B4.noise": RankingPrior(20.0, 15.0, 0.2, 0.2),      # 聴覚=視角の代理
    "B4.salient": RankingPrior(1.7, 12.0, 0.5, 0.9, 1.0),  # 逸脱度優先(§4 段2)
    "B4b.near": RankingPrior(2.0, 6.0, 0.5, 0.3, 0.2),   # 直近サブセル
    # ---- 個体(B5) ----
    "B5.near_person": RankingPrior(1.7, 10.0, 0.5, 0.7),  # 距離は実測で上書き
    "B5.intero": RankingPrior(1.0, 1.0, 0.6, 0.0, 0.2),   # 逸脱度=閾値超過で上書き
    "B5.self": RankingPrior(1.0, 1.0, 0.4, 0.1),
    "B5.watched": RankingPrior(1.7, 5.0, 0.5, 0.5, 0.5),
}

#: 予算グループ → 単一ランキングが 1 本の池にまとめるブロック(§2.2 のグループ予算)。
RANKING_POOL_BLOCKS: Final[Mapping[str, tuple[str, ...]]] = {
    "cell": ("B2", "B4", "B4b"),
    "individual": ("B5",),
}


def pool_token_budget(blocks: Sequence[str]) -> int:
    """§3.2「**同一総トークン**」= そのブロック群のチャネル上限の総和。

    Example:
        >>> pool_token_budget(("B2", "B4", "B4b"))
        250
        >>> pool_token_budget(("B5",))
        220
    """
    return sum(block_channel_total(b) for b in blocks)


def take_within_pool(texts: Sequence[str], pool_tokens: int) -> tuple[int, int]:
    """**順位順**に並んだ行列から、池の予算に収まる**先頭 n 件**を返す。

    固定枠と同じ作法で「行の途中では切らない」「入らなければそこで打ち切る」
    (``truncate_lines`` と同じ規約=枠だけが池に替わる)。

    Returns:
        ``(採った件数, 使ったトークン)``。

    Note:
        逐次ループ宣言(P4): 候補件数ぶんのループ1本(1 セル/1 個体で十数件)。個体数に比例しない。
    """
    cap = int(pool_tokens)
    used = 0
    n = 0
    for t in texts:
        cost = estimate_tokens(t)
        if used + cost > cap:
            break
        used += cost
        n += 1
    return n, used


@dataclass(frozen=True)
class TruncationReport:
    """切り詰めの記録(診断行へ出す)。"""

    channel_id: str
    kept: int
    dropped: int
    tokens_before: int
    tokens_after: int

    @property
    def truncated(self) -> bool:
        return self.dropped > 0


def truncate_lines(
    lines: Sequence[str],
    channel_id: str,
    *,
    limit_tokens: int | None = None,
    max_items: int | None = None,
) -> tuple[list[str], TruncationReport]:
    """チャネル上限までの行を残す(**行の途中では絶対に切らない**)。

    Args:
        lines: 順位の高い順に並んだ行。
        channel_id: ``CHANNEL_BY_ID`` の鍵(未登録なら ``limit_tokens`` 必須)。
        limit_tokens: 上限の上書き(ablation 用)。
        max_items: 件数上限の上書き。

    Returns:
        (残した行, 切り詰め記録)。

    Note:
        逐次ループ宣言(P4): 行数ぶんのループ1本(1チャネル数行・個体数に比例しない)。
    """
    spec = CHANNEL_BY_ID.get(channel_id)
    if spec is None and limit_tokens is None:
        raise KeyError(f"未登録チャネル: {channel_id!r}(limit_tokens を渡すこと)")
    cap = int(limit_tokens if limit_tokens is not None else spec.tokens)  # type: ignore[union-attr]
    n_max = max_items if max_items is not None else (spec.max_items if spec else None)

    before = sum(estimate_tokens(ln) for ln in lines)
    kept: list[str] = []
    used = 0
    for ln in lines:
        if n_max is not None and len(kept) >= int(n_max):
            break
        t = estimate_tokens(ln)
        if used + t > cap:
            break
        kept.append(ln)
        used += t
    report = TruncationReport(
        channel_id=channel_id,
        kept=len(kept),
        dropped=len(lines) - len(kept),
        tokens_before=before,
        tokens_after=used,
    )
    return kept, report
