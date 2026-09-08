"""world.processes.relations — 世界側台帳の**関係(第1級)4本**(D-R2-2・§2)。

正典(§2 のコードブロックを逐語で写す)
    realizes(WorldProcess | AgentAction, PlanSpec) — 属性 executor: {llm_agent | engine_rule | none}
      ※「フォールバック」の正体は PlanSpec が世界過程に変わることではなく、この executor の切り替え。
        conf宣言つきフォールバック台帳(§1末尾)= executor=engine_rule 行の一覧そのもの
        (カバー率・返済期限を一元管理)
    records(ActualLog, WorldProcess | AgentAction)
    revises(Agent, PlanSpec) — 運転整理(指令)・値上げ(店主)・営業時間変更はここで発火
    counts_as(物理的事実, 制度的事実, 文脈) — 構成的規則(「制服を着た者は駅員として扱う」等・SAI/Searle)

expedient(本モジュール分)
- ``Realizes`` の ``coverage`` は**自由文**(「カバー率」の数値表現を設計書が定めていない)。
  数値が要る局面では ``coverage_ratio``(0-1・任意)を併記する。
- ``counts_as`` の3欄はすべて自由文。文脈(``context``)を**必須**にしたのは
  「文脈なしの counts_as は構成的規則にならない」という Searle の形式(X counts as Y in C)による。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Sequence

from shibuya.world.processes.records import Executor

__all__ = [
    "SubjectType",
    "RelationKind",
    "Realizes",
    "Records",
    "Revises",
    "CountsAs",
    "Relation",
    "FallbackRow",
    "fallback_ledger",
    "relation_key",
]


class SubjectType(str, Enum):
    """``realizes`` / ``records`` の主体側(§2「WorldProcess | AgentAction」)。"""

    WORLD_PROCESS = "world_process"
    AGENT_ACTION = "agent_action"


class RelationKind(str, Enum):
    """関係4本の種別。"""

    REALIZES = "realizes"
    RECORDS = "records"
    REVISES = "revises"
    COUNTS_AS = "counts_as"


@dataclass(frozen=True)
class Realizes:
    """``realizes(WorldProcess | AgentAction, PlanSpec)`` — **属性 executor が必須**。

    Attributes:
        subject_id: 世界過程 id またはエージェント行動 id。
        subject_type: ``SubjectType``。
        plan_spec_id: 実現される ``PlanSpec`` の id。
        executor: ``llm_agent`` / ``engine_rule`` / ``none``。
        conf: ``engine_rule`` のときの信頼度(0<conf≤1)。§1「conf宣言つきフォールバック」。
        coverage: そのフォールバックが覆っている範囲(自由文=expedient)。
        coverage_ratio: 覆っている割合(0-1・任意。数値が要るときだけ)。
        repayment_due: 返済期限(いつエージェント化するか)。

    Raises:
        TypeError: ``executor`` が ``Executor`` でない(=属性 executor 必須)。
        ValueError: ``engine_rule`` なのに conf / coverage / repayment_due が欠けている。
    """

    subject_id: str
    subject_type: SubjectType
    plan_spec_id: str
    executor: Executor
    conf: float | None = None
    coverage: str = ""
    coverage_ratio: float | None = None
    repayment_due: str = ""
    note: str = ""

    kind: RelationKind = RelationKind.REALIZES

    def __post_init__(self) -> None:
        if not self.subject_id.strip() or not self.plan_spec_id.strip():
            raise ValueError("realizes: subject_id と plan_spec_id は必須")
        if not isinstance(self.subject_type, SubjectType):
            raise TypeError("realizes: subject_type は SubjectType")
        if not isinstance(self.executor, Executor):
            raise TypeError(
                "realizes は属性 executor: {llm_agent|engine_rule|none} を必ず持つ(§2)"
            )
        if self.executor is Executor.ENGINE_RULE:
            if self.conf is None or not (0.0 < float(self.conf) <= 1.0):
                raise ValueError(
                    f"{self.subject_id}->{self.plan_spec_id}: engine_rule は conf∈(0,1] が必須"
                    "(conf宣言つきフォールバック・§1)"
                )
            if not self.coverage.strip() or not self.repayment_due.strip():
                raise ValueError(
                    f"{self.subject_id}->{self.plan_spec_id}: engine_rule は"
                    "カバー率と返済期限が必須(§1 末尾のフォールバック台帳)"
                )
        elif self.conf is not None:
            raise ValueError(
                f"{self.subject_id}->{self.plan_spec_id}: conf は engine_rule のときだけ"
            )
        if self.coverage_ratio is not None and not (0.0 <= float(self.coverage_ratio) <= 1.0):
            raise ValueError("coverage_ratio は 0-1")

    @property
    def is_fallback(self) -> bool:
        return self.executor is Executor.ENGINE_RULE

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "subject_id": self.subject_id,
            "subject_type": self.subject_type.value,
            "plan_spec_id": self.plan_spec_id,
            "executor": self.executor.value,
            "conf": self.conf,
            "coverage": self.coverage,
            "coverage_ratio": self.coverage_ratio,
            "repayment_due": self.repayment_due,
            "note": self.note,
        }


@dataclass(frozen=True)
class Records:
    """``records(ActualLog, WorldProcess | AgentAction)``。"""

    actual_log_id: str
    target_id: str
    target_type: SubjectType
    note: str = ""

    kind: RelationKind = RelationKind.RECORDS

    def __post_init__(self) -> None:
        if not self.actual_log_id.strip() or not self.target_id.strip():
            raise ValueError("records: actual_log_id と target_id は必須")
        if not isinstance(self.target_type, SubjectType):
            raise TypeError("records: target_type は SubjectType")

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "actual_log_id": self.actual_log_id,
            "target_id": self.target_id,
            "target_type": self.target_type.value,
            "note": self.note,
        }


@dataclass(frozen=True)
class Revises:
    """``revises(Agent, PlanSpec)`` — 運転整理(指令)・値上げ(店主)・営業時間変更。

    Attributes:
        agent_id: 改訂した主体(指令エージェント・店主…)。§1 追補「単一の改訂権者」。
        plan_spec_id: 改訂された PlanSpec。
        at_tick: 改訂 tick(新版の transaction time)。
        new_version: 改訂後の版番号(1 以上・改訂前より大きい)。
        reason: 理由(障害・値上げ・時短…)。
    """

    agent_id: str
    plan_spec_id: str
    at_tick: int
    new_version: int
    reason: str = ""

    kind: RelationKind = RelationKind.REVISES

    def __post_init__(self) -> None:
        if not self.agent_id.strip() or not self.plan_spec_id.strip():
            raise ValueError("revises: agent_id と plan_spec_id は必須")
        if int(self.at_tick) < 0:
            raise ValueError("revises: at_tick は 0 以上")
        if int(self.new_version) < 2:
            raise ValueError("revises: new_version は 2 以上(初版 1 を書き換えた結果)")

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "agent_id": self.agent_id,
            "plan_spec_id": self.plan_spec_id,
            "at_tick": int(self.at_tick),
            "new_version": int(self.new_version),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CountsAs:
    """``counts_as(物理的事実, 制度的事実, 文脈)`` — 構成的規則(Searle: X counts as Y in C)。"""

    physical_fact: str
    institutional_fact: str
    context: str
    note: str = ""

    kind: RelationKind = RelationKind.COUNTS_AS

    def __post_init__(self) -> None:
        if not self.physical_fact.strip():
            raise ValueError("counts_as: 物理的事実(X)は必須")
        if not self.institutional_fact.strip():
            raise ValueError("counts_as: 制度的事実(Y)は必須")
        if not self.context.strip():
            raise ValueError(
                "counts_as: 文脈(C)は必須 — 文脈なしの counts_as は構成的規則にならない"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "physical_fact": self.physical_fact,
            "institutional_fact": self.institutional_fact,
            "context": self.context,
            "note": self.note,
        }


#: 関係の合併型。
Relation = Realizes | Records | Revises | CountsAs


def relation_key(rel: Relation) -> tuple[str, ...]:
    """決定論ソート用の鍵(``to_json`` の並びを固定する)。"""
    d = rel.as_dict()
    return tuple(str(d.get(k, "")) for k in sorted(d))


@dataclass(frozen=True)
class FallbackRow:
    """conf宣言つきフォールバック台帳(§1 末尾)の1行。"""

    plan_spec_id: str
    subject_id: str
    subject_type: str
    conf: float
    coverage: str
    coverage_ratio: float | None
    repayment_due: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_spec_id": self.plan_spec_id,
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "conf": float(self.conf),
            "coverage": self.coverage,
            "coverage_ratio": self.coverage_ratio,
            "repayment_due": self.repayment_due,
        }


def fallback_ledger(relations: Iterable[Relation] | Sequence[Relation]) -> tuple[FallbackRow, ...]:
    """§1「conf宣言つきフォールバック台帳 = executor=engine_rule 行の一覧そのもの」。

    Args:
        relations: 関係の列(``Realizes`` 以外は無視する)。

    Returns:
        ``(plan_spec_id, subject_id)`` 昇順の ``FallbackRow`` タプル。
    """
    rows = [
        FallbackRow(
            plan_spec_id=r.plan_spec_id,
            subject_id=r.subject_id,
            subject_type=r.subject_type.value,
            conf=float(r.conf) if r.conf is not None else 0.0,
            coverage=r.coverage,
            coverage_ratio=r.coverage_ratio,
            repayment_due=r.repayment_due,
        )
        for r in relations
        if isinstance(r, Realizes) and r.is_fallback
    ]
    return tuple(sorted(rows, key=lambda x: (x.plan_spec_id, x.subject_id)))
