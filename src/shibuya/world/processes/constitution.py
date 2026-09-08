"""world.processes.constitution — **憲法5 の機械検査**(D-R2-4・決定2026-09-07)。

正典(世界過程設計書 §5 の確定文・逐語)
    「全ての細部・世界過程は、(a)少なくとも1つの**知覚契約経由でエージェントに届く**か、
     (b)少なくとも1つの**パターン照合または観測出力に寄与する**か、いずれかを宣言できなければ
     実装しない。宣言した届き先が消えた細部は、削除候補として台帳に自動的に載る。」

    実装形(D-R2-4)= レジストリの各世界過程・細部に必須欄 ``reaches=[知覚チャネルID…]``
    (知覚契約書 §3 の行 ID)と ``contributes=[パターンID/観測出力ID…]``(パターン台帳行・計器盤出力)。
    **ビルド時検査**: (a)(b) のどちらかが非空 ∧ 参照先が実在。参照先が消えたら CI が
    「削除候補」行を台帳へ自動追記。**PlanSpec の必須欄**: 「公示範囲」と「遵守率観測」。
    公示されない計画は (a) を満たさず作れない。

id 集合の正典は **Markdown 側**(知覚契約書 §3 の表 / パターン台帳の表)。本モジュールは
凍結写しの定数を持ち、``parse_*`` で Markdown を読み直して**定数と一致すること**を
テストで検査する(``core.budget`` と同じ「正典は Markdown・コードは読むだけ」の作法)。

expedient(本モジュール分)
- **保留チャネル**(知覚契約書 §3「嗅覚 … 状態=**保留**」)を ``reaches`` に書くのは違反にした。
  設計書に明文の禁止はないが、「対応行なし・保留」のチャネルは届き先として成立しない。
- **封印行**(パターン台帳 §2 S1/S2/S3)を ``contributes`` に書くのは違反にした。根拠=台帳 §2
  運用「**以後の設計議論で言及・参照しない**」。ただし知覚契約書 §3 の「台帳行」欄が
  S3 を2箇所で参照しており(看板(b)・人物③)、両文書は既に矛盾している(親へ報告済み)。
- **破棄行**(``~~D2~~`` / ``~~D3~~``)は id としては存在しないものとして扱う。
- 観測出力 id の既定集合は台帳 §3「診断(合否なし・報告のみ)」の5行のみ。計器盤の出力 id 体系は
  未定義なので、追加は ``output_ids`` 引数で呼び出し側が渡す。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Iterable, Protocol, Sequence

from shibuya.world.processes.records import (
    DetailDeclaration,
    PlanSpec,
    WorldProcess,
)

__all__ = [
    "PERCEPTION_CONTRACT_RELPATH",
    "PATTERN_LEDGER_RELPATH",
    "ENV_PERCEPTION_MD",
    "ENV_PATTERN_MD",
    "PERCEPTION_CHANNEL_IDS",
    "SUSPENDED_CHANNEL_IDS",
    "PROPOSED_CHANNEL_IDS",
    "PATTERN_IDS",
    "SEALED_PATTERN_IDS",
    "DISCARDED_PATTERN_IDS",
    "DIAGNOSTIC_OUTPUT_IDS",
    "LedgerIds",
    "parse_perception_channel_ids",
    "parse_pattern_ledger_ids",
    "Violation",
    "DeletionCandidate",
    "ConstitutionReport",
    "check_declaration",
    "check_constitution5",
]

PERCEPTION_CONTRACT_RELPATH = "docs/design/v2-perception-contract.md"
PATTERN_LEDGER_RELPATH = "docs/design/v2-pattern-ledger.md"
ENV_PERCEPTION_MD = "SHIBUYA_PERCEPTION_MD"
ENV_PATTERN_MD = "SHIBUYA_PATTERN_LEDGER_MD"

# ------------------------------------------------------------------ 凍結写し(id 集合)
#: 知覚契約書 §3「チャネル仕様表」の**チャネル列**(表の行 id)。docs 上の行 52-66。
#: 「嗅覚」は状態=保留(``SUSPENDED_CHANNEL_IDS``)だが、表の行としては存在する。
PERCEPTION_CHANNEL_IDS: Final[tuple[str, ...]] = (
    "可視性",  # §3 l.52  T1セル→可視物 / B2・B5
    "人物①",  # §3 l.53  密度・流れ(Fruin LOS型段階)/ B4
    "人物②",  # §3 l.54  行列・人だかり・グループ(上位k)/ B4
    "人物③",  # §3 l.55  顕著な行為(倒れる・叫び・警察)/ B4(到達分)
    "人物④",  # §3 l.56  知人∩セル+近接他者上位k / B5
    "人物⑤",  # §3 l.57  被注視性 / B5
    "看板(a)",  # §3 l.58  店舗基本属性 / B2
    "看板(b)",  # §3 l.59  広告 / B2→B5(通過分)
    "看板(c)",  # §3 l.60  駅案内(エンジン経路側)/ ブロック「—」・状態「後続」
    "内受容",  # §3 l.61  満腹・体力・体感温度(0-10)/ B5(閾値割れ)
    "聴覚: 静的場",  # §3 l.62  道路交通(ASJ RTN-Model 2018)/ B4(段階)
    "聴覚: 密度項",  # §3 l.63  多数話者エネルギー和+Lombard / B4(段階)
    "聴覚: イベント",  # §3 l.64  noise_event→2段半径 / B4・B5
    "聴覚: 傍受",  # §3 l.65  可聴r≈2m→3段ゲート / B5
    "嗅覚",  # §3 l.66  「— / 対応行なし / **保留**」
)

#: 状態が「保留」で届き先として使えないチャネル(知覚契約書 §3)。
SUSPENDED_CHANNEL_IDS: Final[tuple[str, ...]] = ("嗅覚",)

#: **知覚契約書 §3 に無い**が第1陣の宣言で必要になった候補(=ユーザー承認が要る設計追加)。
#: B3(時間帯・天候・日照・大事件)は §2.2 の**ブロック**であってチャネル行ではない
#: ——§3 の表にブロック B3 を持つ行が1つも無い(表の ブロック列は B2/B4/B4b/B5 のみ)。
#: 第1陣の 昼夜・天候 は「内受容(体感温度)」「人物③(照明係数 m_light)」経由で (a) を満たすので、
#: **本モジュールは提案 id を既定の検査集合に入れない**(黙って発明しない・§4 の規律)。
PROPOSED_CHANNEL_IDS: Final[tuple[str, ...]] = (
    "時間帯・天候(B3)",  # 提案: B3 の内容(時間帯・天候・日照)を届けるチャネル行の新設
    "大事件(B3)",  # 提案: B3 の「大事件(常時関連)」を届けるチャネル行の新設
)

#: パターン台帳の**照合行 id**(§1 階層A-G + §9 世界側新規行)。破棄行・封印行は含まない。
PATTERN_IDS: Final[tuple[str, ...]] = (
    # 階層A 個人行動(9)
    "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9",
    # 階層B 関係(4)
    "B1", "B2", "B3", "B4",
    # 階層C 集団・情報(4)
    "C1", "C2", "C3", "C4",
    # 階層D 都市集計・空間(8・D2/D3 は破棄)
    "D1′", "D1b", "D4′", "D5", "D6", "D7", "D8", "D10",
    # 階層E 経済(7)
    "E1", "E2", "E3", "E4", "E5", "E6", "E7",
    # 階層F 人口初期条件(3)
    "F1", "F2", "F3",
    # 階層G 広告・情報接触(4)
    "AD2", "AD3", "AD4", "AD5",
    # §9 世界側の新規行(9)
    "W1", "W2", "W3", "W5", "W6", "D5′", "D10′", "D11′", "D12′",
)

#: 封印(§2)。**以後の設計議論で言及・参照しない**ため ``contributes`` に書けない。
SEALED_PATTERN_IDS: Final[tuple[str, ...]] = ("S1", "S2", "S3")

#: 破棄済み(§1 階層D の ``~~D2~~`` / ``~~D3~~``・2026-09-03)。
DISCARDED_PATTERN_IDS: Final[tuple[str, ...]] = ("D2", "D3")

#: 観測出力 id の既定集合 = パターン台帳 §3「診断(合否なし・報告のみ・v1から継承)」の5行。
DIAGNOSTIC_OUTPUT_IDS: Final[tuple[str, ...]] = (
    "cog_calls_per_person_day",
    "cog_zero_call_share",
    "cog_calls_distribution",
    "cog_lane_coverage",
    "cog_attr_coverage",
)


# ------------------------------------------------------------------ Markdown 読み直し
def _repo_root(relpath: str) -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / relpath).is_file():
            return parent
    raise FileNotFoundError(f"{relpath} が見つからない({here} から上位を探索)")


def _doc_path(relpath: str, env: str, override: str | Path | None) -> Path:
    if override is not None:
        return Path(override)
    from_env = os.environ.get(env)
    if from_env:
        return Path(from_env)
    return _repo_root(relpath) / relpath


_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")
_STRIKE_RE = re.compile(r"^~~(?P<id>.+?)~~$")


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if not s.startswith("|") or not s.endswith("|"):
        return []
    return [c.strip() for c in s[1:-1].split("|")]


def parse_perception_channel_ids(path: str | Path | None = None) -> tuple[str, ...]:
    """知覚契約書 §3 チャネル仕様表の**チャネル列**を出現順で返す。

    Args:
        path: Markdown のパス。None なら ``SHIBUYA_PERCEPTION_MD`` → リポジトリルート。

    Returns:
        行 id のタプル(``("可視性", "人物①", …, "嗅覚")``)。

    Raises:
        ValueError: 表の見出しが見つからない / 1行も読めなかった。
    """
    md = _doc_path(PERCEPTION_CONTRACT_RELPATH, ENV_PERCEPTION_MD, path)
    ids: list[str] = []
    in_table = False
    for raw in md.read_text(encoding="utf-8").split("\n"):
        cells = _split_row(raw)
        if not cells:
            in_table = False
            continue
        if cells[0] == "チャネル":
            in_table = True
            continue
        if not in_table or _SEPARATOR_RE.match(raw.strip()):
            continue
        cid = cells[0]
        if cid and cid not in ids:
            ids.append(cid)
    if not ids:
        raise ValueError(f"{md}: §3 チャネル仕様表(見出し「チャネル」)が読めなかった")
    return tuple(ids)


@dataclass(frozen=True)
class LedgerIds:
    """パターン台帳から読んだ行 id の3分類。"""

    active: tuple[str, ...]
    sealed: tuple[str, ...]
    discarded: tuple[str, ...]

    @property
    def all_ids(self) -> tuple[str, ...]:
        return self.active + self.sealed + self.discarded


def parse_pattern_ledger_ids(path: str | Path | None = None) -> LedgerIds:
    """パターン台帳の表(先頭列見出しが ``ID`` または ``行``)から行 id を読む。

    ``~~D2~~`` のような取り消し線は**破棄行**、§2 の封印表の行は**封印行**に分類する。

    Args:
        path: Markdown のパス。None なら ``SHIBUYA_PATTERN_LEDGER_MD`` → リポジトリルート。

    Raises:
        ValueError: 1行も読めなかった。
    """
    md = _doc_path(PATTERN_LEDGER_RELPATH, ENV_PATTERN_MD, path)
    active: list[str] = []
    sealed: list[str] = []
    discarded: list[str] = []
    in_table = False
    sealed_section = False
    for raw in md.read_text(encoding="utf-8").split("\n"):
        line = raw.strip()
        if line.startswith("## "):
            sealed_section = line.startswith("## 2.")
        cells = _split_row(raw)
        if not cells:
            in_table = False
            continue
        if cells[0] in ("ID", "行"):
            in_table = True
            continue
        if not in_table or _SEPARATOR_RE.match(line):
            continue
        rid = cells[0]
        if not rid:
            continue
        m = _STRIKE_RE.match(rid)
        if m:
            v = m.group("id")
            if v not in discarded:
                discarded.append(v)
            continue
        if sealed_section:
            if rid not in sealed:
                sealed.append(rid)
        elif rid not in active:
            active.append(rid)
    if not active:
        raise ValueError(f"{md}: 照合行 id(先頭列 ID/行)が読めなかった")
    return LedgerIds(tuple(active), tuple(sealed), tuple(discarded))


# ------------------------------------------------------------------ 検査結果の型
@dataclass(frozen=True)
class Violation:
    """憲法5 検査の違反1件。"""

    subject_type: str  # "world_process" | "plan_spec" | "detail"
    subject_id: str
    code: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "code": self.code,
            "detail": self.detail,
        }

    def __str__(self) -> str:
        return f"[{self.code}] {self.subject_type}:{self.subject_id} — {self.detail}"


@dataclass(frozen=True)
class DeletionCandidate:
    """「宣言した届き先が消えた細部は、削除候補として台帳に自動的に載る」(§5 確定文)。"""

    subject_type: str
    subject_id: str
    reason: str
    vanished_targets: tuple[str, ...] = ()
    detected_at: str = ""

    @property
    def dedupe_key(self) -> tuple[str, str]:
        """台帳の重複排除鍵(過程 id + 理由)。"""
        return (self.subject_id, self.reason)

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "reason": self.reason,
            "vanished_targets": list(self.vanished_targets),
            "detected_at": self.detected_at,
        }


@dataclass(frozen=True)
class ConstitutionReport:
    """``check_constitution5`` の報告(CI ゲート用)。"""

    violations: tuple[Violation, ...]
    deletion_candidates: tuple[DeletionCandidate, ...]
    n_processes: int
    n_plan_specs: int
    n_details: int
    warnings: tuple[Violation, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.violations

    def as_text(self) -> str:
        head = (
            f"憲法5 の機械検査(D-R2-4): 過程 {self.n_processes} / 計画 {self.n_plan_specs} / "
            f"細部 {self.n_details} → {'OK' if self.ok else 'NG'}"
        )
        lines = [head]
        for v in self.violations:
            lines.append(f"  違反 {v}")
        for w in self.warnings:
            lines.append(f"  警告 {w}")
        for c in self.deletion_candidates:
            lines.append(
                f"  削除候補 {c.subject_type}:{c.subject_id} — {c.reason} "
                f"{list(c.vanished_targets)}"
            )
        return "\n".join(lines)


# ------------------------------------------------------------------ 検査本体
def check_declaration(
    subject_type: str,
    subject_id: str,
    reaches: Sequence[str],
    contributes: Sequence[str],
    *,
    channel_ids: Iterable[str],
    pattern_ids: Iterable[str],
    output_ids: Iterable[str] = (),
    suspended_channel_ids: Iterable[str] = SUSPENDED_CHANNEL_IDS,
    sealed_pattern_ids: Iterable[str] = SEALED_PATTERN_IDS,
    discarded_pattern_ids: Iterable[str] = DISCARDED_PATTERN_IDS,
) -> tuple[tuple[Violation, ...], tuple[str, ...]]:
    """1件ぶんの (a)/(b) 検査。

    Args:
        subject_type: ``"world_process"`` / ``"plan_spec"`` / ``"detail"``。
        subject_id: 対象 id。
        reaches: (a) 知覚チャネル id の列。
        contributes: (b) パターン id / 観測出力 id の列。
        channel_ids: 実在する知覚チャネル id。
        pattern_ids: 実在するパターン台帳行 id。
        output_ids: 実在する観測出力 id。
        suspended_channel_ids: 保留チャネル(届き先にできない)。
        sealed_pattern_ids: 封印行(参照禁止)。
        discarded_pattern_ids: 破棄行(存在しない)。

    Returns:
        ``(違反タプル, 消えた届き先タプル)``。
    """
    channels = set(channel_ids)
    patterns = set(pattern_ids)
    outputs = set(output_ids)
    suspended = set(suspended_channel_ids)
    sealed = set(sealed_pattern_ids)
    discarded = set(discarded_pattern_ids)

    violations: list[Violation] = []
    vanished: list[str] = []

    if not reaches and not contributes:
        violations.append(
            Violation(
                subject_type,
                subject_id,
                "C5-EMPTY",
                "(a) reaches も (b) contributes も空 — 憲法5「宣言できなければ実装しない」",
            )
        )

    for cid in reaches:
        if cid in suspended:
            violations.append(
                Violation(
                    subject_type,
                    subject_id,
                    "C5-SUSPENDED-CHANNEL",
                    f"知覚チャネル {cid!r} は知覚契約書 §3 で状態=保留(届き先にできない)",
                )
            )
        elif cid not in channels:
            vanished.append(cid)
            violations.append(
                Violation(
                    subject_type,
                    subject_id,
                    "C5-UNKNOWN-TARGET",
                    f"reaches の {cid!r} は知覚契約書 §3 のチャネル行に無い",
                )
            )

    for pid in contributes:
        if pid in sealed:
            violations.append(
                Violation(
                    subject_type,
                    subject_id,
                    "C5-SEALED-PATTERN",
                    f"封印行 {pid!r} は設計で参照しない(パターン台帳 §2 運用規則5)",
                )
            )
        elif pid in discarded:
            vanished.append(pid)
            violations.append(
                Violation(
                    subject_type,
                    subject_id,
                    "C5-DISCARDED-PATTERN",
                    f"{pid!r} は破棄済みの台帳行(2026-09-03)",
                )
            )
        elif pid not in patterns and pid not in outputs:
            vanished.append(pid)
            violations.append(
                Violation(
                    subject_type,
                    subject_id,
                    "C5-UNKNOWN-TARGET",
                    f"contributes の {pid!r} はパターン台帳行にも観測出力 id にも無い",
                )
            )

    return tuple(violations), tuple(vanished)


class _RegistryLike(Protocol):
    """``check_constitution5`` が必要とする最小の面(循環 import を避けるための構造型)。"""

    @property
    def processes(self) -> tuple[WorldProcess, ...]: ...

    @property
    def plan_specs(self) -> tuple[PlanSpec, ...]: ...

    @property
    def details(self) -> tuple[DetailDeclaration, ...]: ...


def check_constitution5(
    registry: _RegistryLike,
    perception_channel_ids: Iterable[str] | None = None,
    pattern_ids: Iterable[str] | None = None,
    output_ids: Iterable[str] | None = None,
    *,
    detected_at: str = "",
) -> ConstitutionReport:
    """D-R2-4 のビルド時検査を台帳全体に適用する。

    検査項目:
        1. 各世界過程・細部・計画で (a) または (b) が非空(``C5-EMPTY``)。
        2. 参照先 id が実在(``C5-UNKNOWN-TARGET`` / ``C5-DISCARDED-PATTERN``)。
        3. 保留チャネル・封印行の参照禁止(``C5-SUSPENDED-CHANNEL`` / ``C5-SEALED-PATTERN``)。
        4. PlanSpec は公示範囲が非空(``C5-PLANSPEC-SCOPE``)+遵守率観測欄が非空
           (``C5-PLANSPEC-COMPLIANCE``)。
        5. 宣言した届き先が**全て**消えた実体 → 削除候補(``deletion_candidates``)。

    Args:
        registry: ``processes`` / ``plan_specs`` / ``details`` を持つレジストリ。
        perception_channel_ids: 実在チャネル id(None なら ``PERCEPTION_CHANNEL_IDS``)。
        pattern_ids: 実在パターン id(None なら ``PATTERN_IDS``)。
        output_ids: 実在観測出力 id(None なら ``DIAGNOSTIC_OUTPUT_IDS``)。
        detected_at: 削除候補行に載せる検出時刻(空なら書かない=ファイルが決定論になる)。

    Returns:
        ``ConstitutionReport``。``ok`` が False なら CI 失敗にする。
    """
    channels = tuple(PERCEPTION_CHANNEL_IDS if perception_channel_ids is None else perception_channel_ids)
    patterns = tuple(PATTERN_IDS if pattern_ids is None else pattern_ids)
    outputs = tuple(DIAGNOSTIC_OUTPUT_IDS if output_ids is None else output_ids)

    violations: list[Violation] = []
    candidates: list[DeletionCandidate] = []

    def _one(subject_type: str, subject_id: str, reaches: Sequence[str], contributes: Sequence[str]) -> None:
        vs, vanished = check_declaration(
            subject_type,
            subject_id,
            reaches,
            contributes,
            channel_ids=channels,
            pattern_ids=patterns,
            output_ids=outputs,
        )
        violations.extend(vs)
        declared = tuple(reaches) + tuple(contributes)
        if not declared:
            candidates.append(
                DeletionCandidate(
                    subject_type,
                    subject_id,
                    "(a)(b) いずれの宣言もない(憲法5・知覚契約書 §1 不変条件2)",
                    (),
                    detected_at,
                )
            )
        elif vanished and len(set(vanished)) == len(set(declared)):
            candidates.append(
                DeletionCandidate(
                    subject_type,
                    subject_id,
                    "宣言した届き先が全て消えた(D-R2-4 の自動追記)",
                    tuple(sorted(set(vanished))),
                    detected_at,
                )
            )

    # 逐次ループ宣言(P4): 台帳の行数(数十)ぶん。個体数・tick 数には比例しない。
    procs = tuple(registry.processes)
    specs = tuple(registry.plan_specs)
    details = tuple(registry.details)

    for p in procs:
        _one("world_process", p.id, p.reaches, p.contributes)
    for d in details:
        _one("detail", d.id, d.reaches, d.contributes)
    for s in specs:
        if s.announcement_scope.is_empty:
            violations.append(
                Violation(
                    "plan_spec",
                    s.id,
                    "C5-PLANSPEC-SCOPE",
                    "公示範囲が空 — 公示されない計画は (a) を満たさず作れない(D-R2-4)",
                )
            )
        if not s.compliance_field.strip():
            violations.append(
                Violation(
                    "plan_spec",
                    s.id,
                    "C5-PLANSPEC-COMPLIANCE",
                    "遵守率観測欄(ActualLog との一致率)が空(D-R2-4 必須欄)",
                )
            )
        _one(
            "plan_spec",
            s.id,
            tuple(s.reaches) + tuple(s.announcement_scope.channel_ids),
            s.contributes,
        )

    return ConstitutionReport(
        violations=tuple(violations),
        deletion_candidates=tuple(candidates),
        n_processes=len(procs),
        n_plan_specs=len(specs),
        n_details=len(details),
    )
