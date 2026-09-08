"""world.processes.records — 世界側台帳の**レコード型3つ**(D-R2-2・決定2026-09-02)。

正典
- 世界過程設計書 §2「**原則: 台帳(名前空間・ID体系・概念モデル)は1つ、レコード型は3つ。**」
  ``WorldProcess`` / ``PlanSpec`` / ``ActualLog``。3型の欄は §2 のコードブロックを逐語で写す。
- §2「分類軸は4本」= 軸1 実行様態 / 軸2 可変性・改訂権者 / 軸3 規範種別 / 軸4 違反可能性。
- §2「門前条件の二重化(台帳に対応行のない実体は作れない=R1運用規則1)は**3レコード型すべてに適用**」。
- §5 D-R2-4(憲法5の確定文): 各世界過程・細部に必須欄 ``reaches`` / ``contributes``。
  **PlanSpec の必須欄**=「公示範囲」と「遵守率観測」。「公示されない計画は(a)を満たさず作れない」。
- §3 実装原則2「状態成長の宣言を必須化」→ ``WorldProcess.growth`` は ``core.growth.GrowthDeclaration``。

層契約: ``shibuya.world`` は ``core`` と ``manifest`` だけを import する
(engine/agents/perception/llm/economy は不可・import-linter で強制)。

expedient(本モジュール分・CLAUDE.md §4)
- **軸2(可変性・改訂権者)** は設計書が値の列挙を持たない(「誰がどれほど変えられるか」)。
  ``WorldProcess.revisability`` / ``PlanSpec.revising_authority`` の**自由文**として持つ=expedient。
- **``DeviationVocab.DELAY``**: §2 の逸脱語彙は「SCHEDULED/CANCELED/REPLACEMENT/SKIPPED/NO_DATA等
  **+delay**」で、delay は列挙値ではなく属性。本モジュールは語彙を全域にするため ``DELAY`` を
  列挙値に**足し**、``delay_minutes != 0 ⇔ deviation == DELAY`` を不変条件にした(expedient)。
- ``conf`` は ``executor=engine_rule`` の行にだけ持たせる(§1「conf宣言つきフォールバック」)。
  LLM が担う行に conf を書くのは意味が無いので**禁止**にした(設計書に明記なし=expedient)。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Final

from shibuya.core.growth import GrowthDeclaration

__all__ = [
    "Executor",
    "ProcessKind",
    "Modality",
    "NormKind",
    "Violability",
    "Clock",
    "DeviationVocab",
    "DEVIATION_CODES",
    "DEVIATION_BY_CODE",
    "ANNOUNCEMENT_BLOCKS",
    "Validity",
    "AnnouncementScope",
    "WorldProcess",
    "PlanSpec",
    "ActualLogEntry",
    "DetailDeclaration",
]


# ------------------------------------------------------------------ 列挙(軸1・軸3・軸4)
class Executor(str, Enum):
    """``realizes`` の属性 executor(§2)。「フォールバック」の正体はこの値の切り替え。"""

    LLM_AGENT = "llm_agent"
    ENGINE_RULE = "engine_rule"
    NONE = "none"


class ProcessKind(str, Enum):
    """§1 の3類 + フォールバック枠。**A は第1級**・B/C は §2 で「導出ラベルへ格下げ」。

    ``AGENT_FALLBACK`` は §1 の3類ではない(**本モジュールの追加=expedient**)。根拠は §1 末尾
    「エージェント化できるのにエンジン規則で代替する場合は、従来どおり conf宣言つきフォールバック
    であり、**その置き場と台帳(カバー率・返済期限)をこのモジュールが一元管理する**」。
    3類のどれかに無理に押し込むと「これは自然過程ではない」という事実が台帳から消えるため、
    別値にして返済対象であることを型で見えるようにした。
    """

    NATURAL = "A_natural"  # 自然過程(誰の行動でもない物理・環境の変化)
    EXTERNAL_SYSTEM = "B_external_system"  # 域外システム過程(bbox の外で進行)
    AGGREGATE = "C_aggregate"  # 集約過程(多数の行動の集計が生む「場」)
    AGENT_FALLBACK = "F_agent_fallback"  # 層2の代替(§1 末尾・返済期限つき)


class Modality(str, Enum):
    """軸1 実行様態(§2 の表・第4値「物理アフォーダンス」は検証答申の追加)。"""

    ENGINE_DRIVEN = "engine_driven"  # エンジンが進める
    PLAN_REFERENCE = "plan_reference"  # 参照(規範・予定)
    DERIVED_FROM_ACTIONS = "derived_from_actions"  # 行動から導出(集約)
    PHYSICAL_AFFORDANCE = "physical_affordance"  # 道路網・線路・建物=brute


class NormKind(str, Enum):
    """軸3 規範種別(§2・Searle / OperA / IG2.0 / SAI)。"""

    CONSTITUTIVE = "constitutive"
    REGULATIVE = "regulative"
    BRUTE_PHYSICAL = "brute-physical"
    DESCRIPTIVE_ONLY = "descriptive-only"


class Violability(str, Enum):
    """軸4 違反可能性(§2・Grossi et al.)。"""

    REGIMENTED = "regimented"  # 違反不能=エンジン強制(原則1)
    ENFORCED = "enforced"  # 違反可能+検知+制裁(行12・14・原則6)
    UNENFORCED = "unenforced"


class Clock(str, Enum):
    """§2 WorldProcess の「時計(物理=連続/制度=日次)」。"""

    PHYSICAL = "physical_continuous"
    INSTITUTIONAL = "institutional_daily"


class DeviationVocab(str, Enum):
    """§2 ActualLog の逸脱語彙(GTFS-RT 式)。``DELAY`` は本モジュールの追加(expedient)。"""

    SCHEDULED = "SCHEDULED"
    CANCELED = "CANCELED"
    REPLACEMENT = "REPLACEMENT"
    SKIPPED = "SKIPPED"
    NO_DATA = "NO_DATA"
    DELAY = "DELAY"


#: 固定幅レコード(``actual_log``)用の数値コード。**順序は凍結**(値が変わると過去ログが読めない)。
DEVIATION_CODES: Final[dict[DeviationVocab, int]] = {
    DeviationVocab.SCHEDULED: 0,
    DeviationVocab.CANCELED: 1,
    DeviationVocab.REPLACEMENT: 2,
    DeviationVocab.SKIPPED: 3,
    DeviationVocab.NO_DATA: 4,
    DeviationVocab.DELAY: 5,
}
DEVIATION_BY_CODE: Final[dict[int, DeviationVocab]] = {v: k for k, v in DEVIATION_CODES.items()}

#: 公示範囲が指せる観測ブロック(D-R2-4「B2/B3 の行」)。
ANNOUNCEMENT_BLOCKS: Final[tuple[str, ...]] = ("B2", "B3")


def _clean_ids(values: tuple[str, ...] | list[str], what: str, owner: str) -> tuple[str, ...]:
    out: list[str] = []
    for v in values:
        s = str(v).strip()
        if not s:
            raise ValueError(f"{owner}: {what} に空の id は書けない")
        if s in out:
            raise ValueError(f"{owner}: {what} に重複 id {s!r}")
        out.append(s)
    return tuple(out)


# ------------------------------------------------------------------ 補助型
@dataclass(frozen=True)
class Validity:
    """有効期間(valid time・§2 PlanSpec)。tick 単位。``valid_to=None`` = 無期限。"""

    valid_from: int = 0
    valid_to: int | None = None

    def __post_init__(self) -> None:
        if int(self.valid_from) < 0:
            raise ValueError(f"valid_from は 0 以上: {self.valid_from!r}")
        if self.valid_to is not None and int(self.valid_to) <= int(self.valid_from):
            raise ValueError(f"valid_to は valid_from より後: {self.valid_from}..{self.valid_to}")

    def covers(self, tick: int) -> bool:
        """``tick`` がこの有効期間に入るか(半開区間 ``[valid_from, valid_to)``)。"""
        return int(self.valid_from) <= int(tick) and (
            self.valid_to is None or int(tick) < int(self.valid_to)
        )

    def as_dict(self) -> dict[str, Any]:
        return {"valid_from": int(self.valid_from), "valid_to": self.valid_to}


@dataclass(frozen=True)
class AnnouncementScope:
    """公示範囲(D-R2-4 の PlanSpec 必須欄)=「どの種別・セルの観測ブロックに載るか」。

    Attributes:
        kinds: 届く種別(B1 の種別語・住民/通勤者/来街者/従業者/乗務員/指令 など)。
        cells: 届くセル(セル id または「駅セル」のような記述)。``("*",)`` = 全セル。
        blocks: 観測ブロック(``B2`` / ``B3`` のみ)。
        channel_ids: その公示が乗る知覚チャネル(知覚契約書 §3 の行 id)。空でもよいが、
            空のときは ``blocks`` だけが (a) の根拠になる。
    """

    kinds: tuple[str, ...] = ()
    cells: tuple[str, ...] = ()
    blocks: tuple[str, ...] = ()
    channel_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "kinds", _clean_ids(tuple(self.kinds), "kinds", "公示範囲"))
        object.__setattr__(self, "cells", _clean_ids(tuple(self.cells), "cells", "公示範囲"))
        object.__setattr__(self, "blocks", _clean_ids(tuple(self.blocks), "blocks", "公示範囲"))
        object.__setattr__(
            self, "channel_ids", _clean_ids(tuple(self.channel_ids), "channel_ids", "公示範囲")
        )
        for b in self.blocks:
            if b not in ANNOUNCEMENT_BLOCKS:
                raise ValueError(f"公示範囲の block は {ANNOUNCEMENT_BLOCKS} のみ(D-R2-4): {b!r}")

    @property
    def is_empty(self) -> bool:
        """D-R2-4「公示されない計画は(a)を満たさず作れない」の判定。"""
        return not (self.blocks and (self.kinds or self.cells))

    def as_dict(self) -> dict[str, Any]:
        return {
            "kinds": list(self.kinds),
            "cells": list(self.cells),
            "blocks": list(self.blocks),
            "channel_ids": list(self.channel_ids),
        }


# ------------------------------------------------------------------ レコード型1: WorldProcess
@dataclass(frozen=True)
class WorldProcess:
    """§2 の ``WorldProcess`` 行。

    §2 の欄との対応:
        ``id`` / ``state_vars``(状態の定義)/ ``update_rule``(更新規則)/ ``clock``(時計)/
        ``mechanism`` + ``sensitivity_test_id`` + ``repayment_due``(mechanism|expedient タグ)/
        ``gate_condition``(門前条件・パターン照合1行)+ ``reaches``/``contributes``
        (世界側台帳行との対応)/ ``growth``(状態成長の宣言 §3)/
        ``dilatable``(時間減速の可否・UGC答申#20)。

    追加欄(D-R2-4・§4・W18):
        ``executor``(§2 realizes の属性を過程側にも持たせ、fallback 台帳を1本で引けるようにした)/
        ``conf`` / ``coverage`` / ``repayment_due``(conf宣言つきフォールバック)/
        ``catalog_classes``(世界カタログ v0.2 のクラス名=W18 被覆指標の入力)/
        ``kind``(§1 の3類)・``modality``(軸1)・``norm_kind``(軸3)・``violability``(軸4)・
        ``revisability``(軸2・自由文=expedient)。

    Raises:
        ValueError: 必須欄が空 / expedient なのに感度試験 id・返済期限が無い /
            ``executor=engine_rule`` なのに conf・カバー率・返済期限が無い。
        TypeError: 列挙欄の型違い / ``growth`` が ``GrowthDeclaration`` でない。
    """

    id: str
    kind: ProcessKind
    state_vars: tuple[str, ...]
    update_rule: str
    clock: Clock
    modality: Modality
    executor: Executor
    growth: GrowthDeclaration
    catalog_classes: tuple[str, ...]
    gate_condition: str
    reaches: tuple[str, ...] = ()
    contributes: tuple[str, ...] = ()
    dilatable: bool = False
    mechanism: bool = True
    sensitivity_test_id: str = ""
    conf: float | None = None
    coverage: str = ""
    repayment_due: str = ""
    norm_kind: NormKind = NormKind.BRUTE_PHYSICAL
    violability: Violability = Violability.REGIMENTED
    revisability: str = ""
    batch: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.id or self.id.strip() != self.id or " " in self.id:
            raise ValueError(f"WorldProcess.id は空白なしの非空文字列: {self.id!r}")
        if not isinstance(self.growth, GrowthDeclaration):
            raise TypeError(f"{self.id}: growth は core.growth.GrowthDeclaration(§3 実装原則2)")
        object.__setattr__(
            self, "state_vars", _clean_ids(tuple(self.state_vars), "state_vars", self.id)
        )
        object.__setattr__(
            self,
            "catalog_classes",
            _clean_ids(tuple(self.catalog_classes), "catalog_classes", self.id),
        )
        object.__setattr__(self, "reaches", _clean_ids(tuple(self.reaches), "reaches", self.id))
        object.__setattr__(
            self, "contributes", _clean_ids(tuple(self.contributes), "contributes", self.id)
        )
        if not self.state_vars:
            raise ValueError(f"{self.id}: 状態の定義(state_vars)は必須")
        if not self.update_rule.strip():
            raise ValueError(f"{self.id}: 更新規則(update_rule)は必須")
        if not self.gate_condition.strip():
            raise ValueError(
                f"{self.id}: 門前条件(パターン照合1行)は必須"
                "(§2「台帳に対応行のない実体は作れない」)"
            )
        if not self.catalog_classes:
            raise ValueError(f"{self.id}: catalog_classes は必須(W18 被覆指標の入力)")
        for enum_field, cls in (
            ("kind", ProcessKind),
            ("clock", Clock),
            ("modality", Modality),
            ("executor", Executor),
            ("norm_kind", NormKind),
            ("violability", Violability),
        ):
            if not isinstance(getattr(self, enum_field), cls):
                raise TypeError(f"{self.id}: {enum_field} は {cls.__name__}")
        if not self.mechanism and not (self.sensitivity_test_id and self.repayment_due):
            raise ValueError(
                f"{self.id}: expedient は感度試験 id と返済期限が必須(§2・CLAUDE.md §4)"
            )
        if self.executor is Executor.ENGINE_RULE:
            if self.conf is None or not (0.0 < float(self.conf) <= 1.0):
                raise ValueError(
                    f"{self.id}: executor=engine_rule は conf∈(0,1] が必須"
                    "(§1 conf宣言つきフォールバック)"
                )
            if not self.coverage.strip() or not self.repayment_due.strip():
                raise ValueError(
                    f"{self.id}: engine_rule フォールバックはカバー率と返済期限が必須(§1 末尾)"
                )
        elif self.conf is not None:
            raise ValueError(
                f"{self.id}: conf は executor=engine_rule の行にだけ書く(expedient 規約)"
            )

    @property
    def tag(self) -> str:
        return "mechanism" if self.mechanism else "expedient"

    @property
    def is_fallback(self) -> bool:
        """conf宣言つきフォールバック台帳(§1 末尾)に載る行か。"""
        return self.executor is Executor.ENGINE_RULE

    @property
    def targets(self) -> tuple[str, ...]:
        """(a)+(b) の届き先の合併(D-R2-4 の検査対象)。"""
        return tuple(self.reaches) + tuple(self.contributes)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "state_vars": list(self.state_vars),
            "update_rule": self.update_rule,
            "clock": self.clock.value,
            "modality": self.modality.value,
            "executor": self.executor.value,
            "growth": self.growth.to_yaml_row(),
            "catalog_classes": list(self.catalog_classes),
            "gate_condition": self.gate_condition,
            "reaches": list(self.reaches),
            "contributes": list(self.contributes),
            "dilatable": bool(self.dilatable),
            "tag": self.tag,
            "sensitivity_test_id": self.sensitivity_test_id,
            "conf": self.conf,
            "coverage": self.coverage,
            "repayment_due": self.repayment_due,
            "norm_kind": self.norm_kind.value,
            "violability": self.violability.value,
            "revisability": self.revisability,
            "batch": self.batch,
            "note": self.note,
        }


# ------------------------------------------------------------------ レコード型2: PlanSpec
@dataclass(frozen=True)
class PlanSpec:
    """§2 の ``PlanSpec`` 行(旧「計画データ」の正式形)。

    §2 の欄: ``id`` / ``content``(内容)/ ``validity``(有効期間=valid time)/
    ``version`` + ``transaction_tick``(版=transaction time)/ ``revising_authority``(改訂権者)/
    ``norm_kind``(軸3)/ ``violability``(軸4)/ ``announcement_scope``(公示範囲)/
    ``compliance_field``(遵守率の観測欄)。

    D-R2-4 の必須欄検査は ``constitution.check_constitution5`` が行うが、
    「公示されない計画は作れない」は**型レベルでも**弾く(``announcement_scope`` 空 → ValueError)。
    """

    id: str
    content: str
    validity: Validity
    version: int
    revising_authority: str
    norm_kind: NormKind
    violability: Violability
    announcement_scope: AnnouncementScope
    compliance_field: str
    catalog_classes: tuple[str, ...]
    gate_condition: str
    transaction_tick: int = 0
    reaches: tuple[str, ...] = ()
    contributes: tuple[str, ...] = ()
    mechanism: bool = True
    sensitivity_test_id: str = ""
    repayment_due: str = ""
    batch: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.id or self.id.strip() != self.id or " " in self.id:
            raise ValueError(f"PlanSpec.id は空白なしの非空文字列: {self.id!r}")
        if not self.content.strip():
            raise ValueError(f"{self.id}: 内容(content)は必須")
        if not isinstance(self.validity, Validity):
            raise TypeError(f"{self.id}: validity は Validity(有効期間=valid time)")
        if not isinstance(self.announcement_scope, AnnouncementScope):
            raise TypeError(f"{self.id}: announcement_scope は AnnouncementScope")
        if int(self.version) < 1:
            raise ValueError(f"{self.id}: 版(version)は 1 以上")
        if int(self.transaction_tick) < 0:
            raise ValueError(f"{self.id}: transaction_tick は 0 以上")
        if not self.revising_authority.strip():
            raise ValueError(f"{self.id}: 改訂権者(revising_authority)は必須(軸2)")
        if not isinstance(self.norm_kind, NormKind) or not isinstance(
            self.violability, Violability
        ):
            raise TypeError(f"{self.id}: norm_kind は NormKind・violability は Violability")
        if self.announcement_scope.is_empty:
            raise ValueError(
                f"{self.id}: 公示範囲が空 — D-R2-4「公示されない計画は(a)を満たさず作れない」"
                "(blocks と kinds/cells の両方が要る)"
            )
        if not self.compliance_field.strip():
            raise ValueError(
                f"{self.id}: 遵守率の観測欄(compliance_field)は必須(D-R2-4・死んだ規範の検出)"
            )
        if not self.gate_condition.strip():
            raise ValueError(f"{self.id}: 門前条件は3レコード型すべてに適用(§2)")
        object.__setattr__(
            self,
            "catalog_classes",
            _clean_ids(tuple(self.catalog_classes), "catalog_classes", self.id),
        )
        if not self.catalog_classes:
            raise ValueError(f"{self.id}: catalog_classes は必須")
        object.__setattr__(self, "reaches", _clean_ids(tuple(self.reaches), "reaches", self.id))
        object.__setattr__(
            self, "contributes", _clean_ids(tuple(self.contributes), "contributes", self.id)
        )
        if not self.mechanism and not (self.sensitivity_test_id and self.repayment_due):
            raise ValueError(f"{self.id}: expedient は感度試験 id と返済期限が必須")

    @property
    def targets(self) -> tuple[str, ...]:
        """(a)+(b)。公示範囲の ``channel_ids`` も (a) の届き先として数える。"""
        return (
            tuple(self.reaches)
            + tuple(self.announcement_scope.channel_ids)
            + tuple(self.contributes)
        )

    def revised(
        self, *, content: str, at_tick: int, authority: str, validity: Validity | None = None
    ) -> "PlanSpec":
        """``revises(Agent, PlanSpec)`` の適用結果(版+1・transaction time 更新)。

        Args:
            content: 新しい内容(運転整理・値上げ・営業時間変更)。
            at_tick: 改訂 tick(= 新しい版の transaction time)。
            authority: 改訂を要求した主体。``revising_authority`` と一致しなければ拒否。
            validity: 有効期間を変える場合。

        Raises:
            PermissionError: 改訂権者でない主体が改訂しようとした(§2 軸2)。
        """
        if authority != self.revising_authority:
            raise PermissionError(
                f"{self.id}: 改訂権者は {self.revising_authority!r}(要求元 {authority!r})"
            )
        return replace(
            self,
            content=content,
            version=int(self.version) + 1,
            transaction_tick=int(at_tick),
            validity=validity if validity is not None else self.validity,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "validity": self.validity.as_dict(),
            "version": int(self.version),
            "transaction_tick": int(self.transaction_tick),
            "revising_authority": self.revising_authority,
            "norm_kind": self.norm_kind.value,
            "violability": self.violability.value,
            "announcement_scope": self.announcement_scope.as_dict(),
            "compliance_field": self.compliance_field,
            "catalog_classes": list(self.catalog_classes),
            "gate_condition": self.gate_condition,
            "reaches": list(self.reaches),
            "contributes": list(self.contributes),
            "tag": "mechanism" if self.mechanism else "expedient",
            "sensitivity_test_id": self.sensitivity_test_id,
            "repayment_due": self.repayment_due,
            "batch": self.batch,
            "note": self.note,
        }


# ------------------------------------------------------------------ レコード型3: ActualLog
@dataclass(frozen=True)
class ActualLogEntry:
    """§2 の ``ActualLog`` 1行(**追記専用・不変**)。

    保持窓と増分索引は行ではなく**格納器**(``world.processes.actual_log.ActualLog``)が持つ
    ——§2「O(t) 成長する唯一の型なので §3 の宣言を型レベルで強制」に対応するのが格納器側。

    Attributes:
        entry_id: 追記の通し番号(格納器が採番)。
        subject_id: 対象(便 id・エージェント id・POI id など整数化された対象)。
        process_id: ``records(ActualLog, WorldProcess|AgentAction)`` の相手。
        tick: 記録した tick。
        deviation: 逸脱語彙。
        delay_minutes: 遅延(分)。``deviation == DELAY`` のときだけ非0。
    """

    entry_id: int
    subject_id: int
    process_id: str
    tick: int
    deviation: DeviationVocab
    delay_minutes: int = 0

    def __post_init__(self) -> None:
        if int(self.entry_id) < 0 or int(self.subject_id) < 0 or int(self.tick) < 0:
            raise ValueError("entry_id / subject_id / tick は 0 以上")
        if not self.process_id.strip():
            raise ValueError("process_id は必須(records 関係の相手)")
        if not isinstance(self.deviation, DeviationVocab):
            raise TypeError("deviation は DeviationVocab(GTFS-RT 式)")
        if self.deviation is DeviationVocab.DELAY:
            if int(self.delay_minutes) == 0:
                raise ValueError("DELAY は delay_minutes != 0(expedient 規約)")
        elif int(self.delay_minutes) != 0:
            raise ValueError(
                f"{self.deviation.value} に delay_minutes は書けない"
                "(DELAY を使う・expedient 規約)"
            )

    @property
    def code(self) -> int:
        return DEVIATION_CODES[self.deviation]

    @property
    def is_compliant(self) -> bool:
        """遵守率の分子(§2「遵守率の観測欄」)= SCHEDULED のみ。"""
        return self.deviation is DeviationVocab.SCHEDULED

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_id": int(self.entry_id),
            "subject_id": int(self.subject_id),
            "process_id": self.process_id,
            "tick": int(self.tick),
            "deviation": self.deviation.value,
            "delay_minutes": int(self.delay_minutes),
        }


# ------------------------------------------------------------------ 細部(憲法5 の「細部」側)
@dataclass(frozen=True)
class DetailDeclaration:
    """憲法5 確定文の「**全ての細部**・世界過程は…宣言できなければ実装しない」の細部側。

    知覚契約書 §1 不変条件2「全世界状態フィールドは届き先(チャネル×ブロック)を宣言する。
    宣言のない細部は削除候補として台帳に自動掲載」の機械可読な受け皿。
    """

    id: str
    owner_process_id: str
    description: str
    reaches: tuple[str, ...] = ()
    contributes: tuple[str, ...] = ()
    note: str = ""

    def __post_init__(self) -> None:
        if not self.id or self.id.strip() != self.id or " " in self.id:
            raise ValueError(f"DetailDeclaration.id は空白なしの非空文字列: {self.id!r}")
        if not self.owner_process_id.strip():
            raise ValueError(f"{self.id}: owner_process_id は必須")
        if not self.description.strip():
            raise ValueError(f"{self.id}: description は必須")
        object.__setattr__(self, "reaches", _clean_ids(tuple(self.reaches), "reaches", self.id))
        object.__setattr__(
            self, "contributes", _clean_ids(tuple(self.contributes), "contributes", self.id)
        )

    @property
    def targets(self) -> tuple[str, ...]:
        return tuple(self.reaches) + tuple(self.contributes)

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner_process_id": self.owner_process_id,
            "description": self.description,
            "reaches": list(self.reaches),
            "contributes": list(self.contributes),
            "note": self.note,
        }
