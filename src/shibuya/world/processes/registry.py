"""world.processes.registry — 世界側台帳(**名前空間・ID体系は1つ**・D-R2-2)。

正典
- 世界過程設計書 §2「原則: 台帳(名前空間・ID体系・概念モデル)は1つ、レコード型は3つ」。
- §2「門前条件の二重化(台帳に対応行のない実体は作れない=R1運用規則1)は3レコード型すべてに適用」
  → ``add_process`` / ``add_plan_spec`` / ``add_detail`` は登録時に**憲法5 検査を通す**。
- §3 実装原則2「状態成長の宣言を必須化」→ ``add_process`` は ``GrowthDeclaration`` を要求する。
- §5 D-R2-4「ビルド時検査: (a)(b) のどちらかが非空 ∧ 参照先が実在」。
- 世界カタログ v0.2(``manifest.world_catalog``)= W18 世界被覆指標の**分母**。各世界過程は
  自分が埋めるカタログクラスを宣言し、``coverage_report`` が被覆率を返す。

層契約: ``world`` → ``core`` / ``manifest`` のみ。

expedient(本モジュール分)
- ``registry_hash`` は ``to_json``(UTF-8)の blake3。**JSON の書式(キー順・区切り)が鍵の一部**
  なので、書式を変えるとハッシュが変わる=manifest 側の版と同時に動かす必要がある。
- ``coverage_report`` の「フォールバック比率」は**行数**の割合(重み付けなし)。
  設計書は「カバー率」の定義を与えていない。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from shibuya.core.hashing import blake3_hex
from shibuya.manifest.world_catalog import WorldCatalog, load_world_catalog, verify_frozen
from shibuya.world.processes import constitution as C
from shibuya.world.processes.records import (
    DetailDeclaration,
    Executor,
    PlanSpec,
    WorldProcess,
)
from shibuya.world.processes.relations import (
    FallbackRow,
    Realizes,
    Records,
    Relation,
    Revises,
    SubjectType,
    fallback_ledger,
    relation_key,
)

__all__ = [
    "CoverageReport",
    "WorldRegistry",
]


@dataclass(frozen=True)
class CoverageReport:
    """executor 別の内訳と、世界カタログ(分母57)の被覆。"""

    n_processes: int
    by_executor: Mapping[str, int]
    share_by_executor: Mapping[str, float]
    n_fallback_processes: int
    n_fallback_relations: int
    catalog_version: str
    catalog_n_classes: int
    catalog_classes_covered: tuple[str, ...]

    @property
    def catalog_coverage(self) -> float:
        """W18 世界被覆指標の粗い分子/分母(**宣言ベース**・実装の深さ d は別勘定)。"""
        if self.catalog_n_classes == 0:
            return 0.0
        return len(self.catalog_classes_covered) / float(self.catalog_n_classes)

    def as_dict(self) -> dict[str, Any]:
        return {
            "n_processes": self.n_processes,
            "by_executor": dict(self.by_executor),
            "share_by_executor": {k: round(v, 6) for k, v in self.share_by_executor.items()},
            "n_fallback_processes": self.n_fallback_processes,
            "n_fallback_relations": self.n_fallback_relations,
            "catalog_version": self.catalog_version,
            "catalog_n_classes": self.catalog_n_classes,
            "catalog_classes_covered": list(self.catalog_classes_covered),
            "catalog_coverage": round(self.catalog_coverage, 6),
        }

    def as_text(self) -> str:
        parts = [f"世界側台帳: 過程 {self.n_processes} 行"]
        for k in sorted(self.by_executor):
            parts.append(f"  {k:12s} {self.by_executor[k]:3d} ({self.share_by_executor[k]:.1%})")
        parts.append(
            f"  フォールバック: 過程 {self.n_fallback_processes} / realizes "
            f"{self.n_fallback_relations}"
        )
        parts.append(
            f"  カタログ被覆(宣言ベース): {len(self.catalog_classes_covered)}"
            f"/{self.catalog_n_classes} = {self.catalog_coverage:.1%} ({self.catalog_version})"
        )
        return "\n".join(parts)


class WorldRegistry:
    """世界過程・計画仕様・細部・関係を1つの名前空間で保持する台帳。

    Args:
        name: 台帳名(``to_json`` に入る)。
        catalog: 世界カタログ(None なら凍結 JSON を読み ``verify_frozen`` で門を通す)。
        channel_ids / pattern_ids / output_ids: 憲法5 検査の実在 id 集合
            (None なら ``constitution`` の凍結写し)。
        strict: True(既定)なら登録時に憲法5 違反で ``ValueError``。
    """

    def __init__(
        self,
        name: str = "v2-world-ledger",
        *,
        catalog: WorldCatalog | None = None,
        channel_ids: Iterable[str] | None = None,
        pattern_ids: Iterable[str] | None = None,
        output_ids: Iterable[str] | None = None,
        strict: bool = True,
    ) -> None:
        self.name = str(name)
        if catalog is None:
            catalog = load_world_catalog()
            verify_frozen(catalog)
        self._catalog = catalog
        self._catalog_classes = frozenset(r["クラス"] for r in catalog.rows)
        self._channel_ids = tuple(
            C.PERCEPTION_CHANNEL_IDS if channel_ids is None else channel_ids
        )
        self._pattern_ids = tuple(C.PATTERN_IDS if pattern_ids is None else pattern_ids)
        self._output_ids = tuple(C.DIAGNOSTIC_OUTPUT_IDS if output_ids is None else output_ids)
        self.strict = bool(strict)
        self._processes: dict[str, WorldProcess] = {}
        self._plan_specs: dict[str, PlanSpec] = {}
        self._details: dict[str, DetailDeclaration] = {}
        self._relations: list[Relation] = []

    # ------------------------------------------------------------------ 参照
    @property
    def catalog(self) -> WorldCatalog:
        return self._catalog

    @property
    def processes(self) -> tuple[WorldProcess, ...]:
        """id 昇順(決定論)。"""
        return tuple(self._processes[k] for k in sorted(self._processes))

    @property
    def plan_specs(self) -> tuple[PlanSpec, ...]:
        return tuple(self._plan_specs[k] for k in sorted(self._plan_specs))

    @property
    def details(self) -> tuple[DetailDeclaration, ...]:
        return tuple(self._details[k] for k in sorted(self._details))

    @property
    def relations(self) -> tuple[Relation, ...]:
        return tuple(sorted(self._relations, key=relation_key))

    def process(self, pid: str) -> WorldProcess:
        return self._processes[pid]

    def plan_spec(self, sid: str) -> PlanSpec:
        return self._plan_specs[sid]

    # ------------------------------------------------------------------ 登録
    def _check_catalog(self, subject_id: str, classes: Sequence[str]) -> None:
        unknown = [c for c in classes if c not in self._catalog_classes]
        if unknown:
            raise ValueError(
                f"{subject_id}: 世界カタログ v0.2 に無いクラス {unknown}"
                f"(分母は凍結資産・{self._catalog.version}/{self._catalog.sha16})"
            )

    def _check_c5(
        self, subject_type: str, subject_id: str, reaches: Sequence[str], contributes: Sequence[str]
    ) -> tuple[C.Violation, ...]:
        violations, _ = C.check_declaration(
            subject_type,
            subject_id,
            reaches,
            contributes,
            channel_ids=self._channel_ids,
            pattern_ids=self._pattern_ids,
            output_ids=self._output_ids,
        )
        if violations and self.strict:
            joined = " / ".join(str(v) for v in violations)
            raise ValueError(f"憲法5(D-R2-4)違反で登録できない: {joined}")
        return violations

    def add_process(self, p: WorldProcess) -> WorldProcess:
        """世界過程を登録する(門前条件・成長宣言・カタログ・憲法5 を検査)。

        Raises:
            TypeError: ``WorldProcess`` でない。
            ValueError: id 重複 / カタログに無いクラス / 憲法5 違反(``strict``)。
        """
        if not isinstance(p, WorldProcess):
            raise TypeError("add_process は WorldProcess を取る")
        if p.id in self._processes:
            raise ValueError(f"世界過程 id の重複: {p.id}(台帳の名前空間は1つ)")
        # 成長宣言は WorldProcess.__post_init__ が型で強制済み(§3 実装原則2)。
        self._check_catalog(p.id, p.catalog_classes)
        self._check_c5("world_process", p.id, p.reaches, p.contributes)
        self._processes[p.id] = p
        return p

    def add_plan_spec(self, s: PlanSpec) -> PlanSpec:
        """計画仕様を登録する(公示範囲・遵守率観測欄は型が強制済み)。"""
        if not isinstance(s, PlanSpec):
            raise TypeError("add_plan_spec は PlanSpec を取る")
        if s.id in self._plan_specs:
            raise ValueError(f"計画仕様 id の重複: {s.id}")
        self._check_catalog(s.id, s.catalog_classes)
        self._check_c5(
            "plan_spec",
            s.id,
            tuple(s.reaches) + tuple(s.announcement_scope.channel_ids),
            s.contributes,
        )
        self._plan_specs[s.id] = s
        return s

    def add_detail(self, d: DetailDeclaration) -> DetailDeclaration:
        """細部(世界状態フィールド)を登録する。"""
        if not isinstance(d, DetailDeclaration):
            raise TypeError("add_detail は DetailDeclaration を取る")
        if d.id in self._details:
            raise ValueError(f"細部 id の重複: {d.id}")
        if d.owner_process_id not in self._processes:
            raise ValueError(f"{d.id}: 未登録の世界過程 {d.owner_process_id!r} に属する細部は作れない")
        self._check_c5("detail", d.id, d.reaches, d.contributes)
        self._details[d.id] = d
        return d

    def add_relation(self, r: Relation) -> Relation:
        """関係(realizes / records / revises / counts_as)を登録する。

        Raises:
            ValueError: 参照先の世界過程・計画仕様が台帳に無い(門前条件の二重化)。
        """
        if isinstance(r, Realizes):
            if r.plan_spec_id not in self._plan_specs:
                raise ValueError(f"realizes: 未登録の PlanSpec {r.plan_spec_id!r}")
            if (
                r.subject_type is SubjectType.WORLD_PROCESS
                and r.subject_id not in self._processes
            ):
                raise ValueError(f"realizes: 未登録の世界過程 {r.subject_id!r}")
        elif isinstance(r, Records):
            if (
                r.target_type is SubjectType.WORLD_PROCESS
                and r.target_id not in self._processes
            ):
                raise ValueError(f"records: 未登録の世界過程 {r.target_id!r}")
        elif isinstance(r, Revises):
            if r.plan_spec_id not in self._plan_specs:
                raise ValueError(f"revises: 未登録の PlanSpec {r.plan_spec_id!r}")
        self._relations.append(r)
        return r

    # ------------------------------------------------------------------ 台帳の出力
    def fallback_ledger(self) -> tuple[FallbackRow, ...]:
        """§1 末尾「conf宣言つきフォールバック台帳」= executor=engine_rule の一覧。

        ``realizes`` 関係の engine_rule 行に加え、**PlanSpec を持たない engine_rule 過程**
        (例: 断面自動車交通)も同じ表に載せる(返済期限を1本で管理するため)。
        """
        rows = list(fallback_ledger(self._relations))
        covered = {(r.subject_id, r.plan_spec_id) for r in rows}
        for p in self.processes:
            if not p.is_fallback:
                continue
            if any(sid == p.id for sid, _ in covered):
                continue
            rows.append(
                FallbackRow(
                    plan_spec_id="",  # 実現している PlanSpec が無い(過程そのものの代替)
                    subject_id=p.id,
                    subject_type=SubjectType.WORLD_PROCESS.value,
                    conf=float(p.conf) if p.conf is not None else 0.0,
                    coverage=p.coverage,
                    coverage_ratio=None,
                    repayment_due=p.repayment_due,
                )
            )
        return tuple(sorted(rows, key=lambda x: (x.plan_spec_id, x.subject_id)))

    def coverage_report(self) -> CoverageReport:
        """executor 別の行数・比率と、世界カタログの被覆(宣言ベース)。"""
        procs = self.processes
        counts: dict[str, int] = {e.value: 0 for e in Executor}
        for p in procs:
            counts[p.executor.value] += 1
        n = len(procs)
        share = {k: (v / n if n else 0.0) for k, v in counts.items()}
        covered = sorted({c for p in procs for c in p.catalog_classes})
        covered += sorted(
            {c for s in self.plan_specs for c in s.catalog_classes if c not in covered}
        )
        return CoverageReport(
            n_processes=n,
            by_executor=counts,
            share_by_executor=share,
            n_fallback_processes=sum(1 for p in procs if p.is_fallback),
            n_fallback_relations=sum(
                1 for r in self._relations if isinstance(r, Realizes) and r.is_fallback
            ),
            catalog_version=self._catalog.version,
            catalog_n_classes=self._catalog.n_classes,
            catalog_classes_covered=tuple(sorted(set(covered))),
        )

    def to_json(self) -> str:
        """決定論 JSON(キー昇順・行 id 昇順・関係は ``relation_key`` 昇順)。"""
        payload = {
            "name": self.name,
            "catalog": {
                "version": self._catalog.version,
                "sha16": self._catalog.sha16,
                "n_classes": self._catalog.n_classes,
            },
            "processes": [p.as_dict() for p in self.processes],
            "plan_specs": [s.as_dict() for s in self.plan_specs],
            "details": [d.as_dict() for d in self.details],
            "relations": [r.as_dict() for r in self.relations],
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def registry_hash(self) -> str:
        """manifest 用の台帳ハッシュ(blake3・``to_json`` の UTF-8 バイト列)。"""
        return blake3_hex(self.to_json().encode("utf-8"))

    def check_constitution5(self, **kwargs: Any) -> C.ConstitutionReport:
        """``constitution.check_constitution5`` をこの台帳に適用する薄い委譲。"""
        return C.check_constitution5(
            self,
            kwargs.pop("perception_channel_ids", self._channel_ids),
            kwargs.pop("pattern_ids", self._pattern_ids),
            kwargs.pop("output_ids", self._output_ids),
            **kwargs,
        )

    def __repr__(self) -> str:  # pragma: no cover - 診断用
        return (
            f"WorldRegistry(name={self.name!r}, processes={len(self._processes)}, "
            f"plan_specs={len(self._plan_specs)}, details={len(self._details)}, "
            f"relations={len(self._relations)})"
        )
