"""world.processes — **世界側台帳**(D-R2-2 レコード型3+関係4)と**憲法5 の機械検査**(D-R2-4)。

正典: [docs/design/v2-world-process-design.md](../../../../docs/design/v2-world-process-design.md)
§2(台帳1つ・レコード型3・関係4・軸4)/ §3(実装原則・状態成長宣言)/ §4(16行表の executor)/
§5(憲法5 の確定文=D-R2-4)/ §6(D-R2-5 第1陣・D-R2-6 成長宣言)/ §7(U-Goods と拡張ロードマップ)。

モジュール構成
    ``records``              レコード型3(WorldProcess / PlanSpec / ActualLogEntry)+ 細部宣言
    ``relations``            関係4(realizes / records / revises / counts_as)+ フォールバック台帳
    ``registry``             名前空間1つの台帳(登録時検査・被覆報告・決定論 JSON・台帳ハッシュ)
    ``constitution``         憲法5 の機械検査(id 集合の凍結写しと Markdown 読み直し)
    ``deletion_candidates``  削除候補台帳ファイル(``runs/`` へ冪等追記)
    ``first_batch``          第1陣+前倒し分の宣言(データのみ)
    ``actual_log``           追記専用 ActualLog(固定幅 numpy・保持窓・増分索引・遵守率)

層契約: ``world`` は ``core`` と ``manifest`` のみ import する(import-linter で強制)。
"""

from shibuya.world.processes.actual_log import ActualLog, ComplianceRate, plan_compliance
from shibuya.world.processes.constitution import (
    DIAGNOSTIC_OUTPUT_IDS,
    PATTERN_IDS,
    PERCEPTION_CHANNEL_IDS,
    PROPOSED_CHANNEL_IDS,
    SEALED_PATTERN_IDS,
    SUSPENDED_CHANNEL_IDS,
    ConstitutionReport,
    DeletionCandidate,
    Violation,
    check_constitution5,
    parse_pattern_ledger_ids,
    parse_perception_channel_ids,
)
from shibuya.world.processes.deletion_candidates import (
    DEFAULT_LEDGER_PATH,
    append_candidates,
    load_candidates,
)
from shibuya.world.processes.records import (
    ActualLogEntry,
    AnnouncementScope,
    Clock,
    DetailDeclaration,
    DeviationVocab,
    Executor,
    Modality,
    NormKind,
    PlanSpec,
    ProcessKind,
    Validity,
    Violability,
    WorldProcess,
)
from shibuya.world.processes.registry import CoverageReport, WorldRegistry
from shibuya.world.processes.relations import (
    CountsAs,
    FallbackRow,
    Realizes,
    Records,
    Relation,
    Revises,
    SubjectType,
    fallback_ledger,
)

__all__ = [
    # records
    "WorldProcess",
    "PlanSpec",
    "ActualLogEntry",
    "DetailDeclaration",
    "Executor",
    "ProcessKind",
    "Modality",
    "NormKind",
    "Violability",
    "Clock",
    "DeviationVocab",
    "Validity",
    "AnnouncementScope",
    # relations
    "Realizes",
    "Records",
    "Revises",
    "CountsAs",
    "Relation",
    "SubjectType",
    "FallbackRow",
    "fallback_ledger",
    # registry
    "WorldRegistry",
    "CoverageReport",
    # constitution
    "check_constitution5",
    "ConstitutionReport",
    "Violation",
    "DeletionCandidate",
    "PERCEPTION_CHANNEL_IDS",
    "SUSPENDED_CHANNEL_IDS",
    "PROPOSED_CHANNEL_IDS",
    "PATTERN_IDS",
    "SEALED_PATTERN_IDS",
    "DIAGNOSTIC_OUTPUT_IDS",
    "parse_perception_channel_ids",
    "parse_pattern_ledger_ids",
    # deletion candidates
    "append_candidates",
    "load_candidates",
    "DEFAULT_LEDGER_PATH",
    # actual log
    "ActualLog",
    "ComplianceRate",
    "plan_compliance",
]
