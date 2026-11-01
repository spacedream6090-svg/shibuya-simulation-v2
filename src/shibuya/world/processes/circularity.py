"""world.processes.circularity — 循環(同じ値の系で動かして採点する)の機械検査(第340 段 2 の 2・回答 11-01 §3)。

正典: 回答 11-01 §3「つなぎの台帳と WorldProcess に ``drives_from``(何の系の値で動くか)の欄、パターン台帳の各行に
『採点する系』、較正に使った錨に ``burned``。CI で突き合わせ、重なれば落とす(W19・read_guard と同じ型)」。

突き合わせの規則(本モジュールの読み)
    主体 S(世界過程・PlanSpec・つなぎの台帳の行)の ``drives_from`` に系 X があり、S の ``contributes`` に入る
    パターン行 R が X を採点する(R の ID が X か、R の「採点する系」が X)とき、**重なり**とする。重なりの例外は
    2 つ: (1) R の ``burned`` が ``burned``/``外す`` で始まる(較正に使った・一時的に検証から外した)、(2) S に
    「無いと宣言」(``Absence`` の no_actor/no_port)があり、**エンジンがもう動かしていない**(``engine_stopped=True``)うえ、
    R がその宣言の錨(``keeps_anchor`` と結ぶ過程の ``contributes``)に入る(〔検収 中-3・低-2〕)。宣言があっても
    ``engine_stopped=False`` なら例外にせず、「宣言と実装が食い違う」と出して落とす。``要確認`` の印は例外にしない。
    ``drives_from`` の ``none`` と未記入は突き合わせない。系は行の ID と「採点する系」の欄の語(``data:<id>`` を含む)の
    どれでも重なりを見る(〔検収 中-1〕)。

    代打の条件 ⑤(代打の出力が、その過程の検証に使う錨の系に入らない)は ``stand_in_overlap`` で別に見る
    (疑いの 5 行の記録用=落とすのは親が決める)。

読む物: パターン台帳(Markdown・列の名で引く)・つなぎの台帳の JSON(行の欄 ``drives_from`` ほか)・世界の台帳
(``first_batch.build_registry``)。層契約により engine の台帳の読み口は使わない(JSON を直に読む)。

逐次ループ宣言: なし(試験と道具が 1 回呼ぶだけ・ランの中では呼ばない)。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Mapping

from shibuya.world.processes import absent as _AB
from shibuya.world.processes.constitution import (
    ENV_PATTERN_MD,
    PATTERN_LEDGER_RELPATH,
    _doc_path,
    _repo_root,
    _split_row,
)
from shibuya.world.processes.records import DRIVES_NONE

__all__ = [
    "COL_SCORING",
    "COL_BURNED",
    "BRIDGE_LEDGER_RELPATH",
    "PatternScoring",
    "Subject",
    "Overlap",
    "parse_pattern_scoring",
    "load_ledger_rows",
    "subjects_from_registry",
    "subjects_from_ledger",
    "find_overlaps",
    "stand_in_overlap",
]

COL_SCORING: Final[str] = "採点する系"
COL_BURNED: Final[str] = "burned"
BRIDGE_LEDGER_RELPATH: Final[str] = "docs/design/bridging-ledger.json"
MISMATCH: Final[str] = "無いと宣言したが規則がまだ動く=宣言と実装が食い違う"
#: ``burned`` の欄のうち突き合わせの例外にする頭の語。
_EXEMPT_HEADS: Final[tuple[str, ...]] = ("burned", "外す")


@dataclass(frozen=True)
class PatternScoring:
    """パターン台帳の 1 行の「採点する系」と ``burned``。"""

    id: str
    scoring: str
    burned: str

    @property
    def exempt(self) -> bool:
        """突き合わせの例外か(``burned``/``外す`` で始まる)。"""
        return self.burned.startswith(_EXEMPT_HEADS)

    @property
    def systems(self) -> frozenset[str]:
        """この行が採点する系の id(行の ID と「採点する系」の欄の・区切りの語)。"""
        parts = {p.strip() for p in self.scoring.replace("、", "・").split("・") if p.strip()}
        return frozenset({self.id, *parts})


@dataclass(frozen=True)
class Subject:
    """突き合わせの主体(世界過程・PlanSpec・つなぎの台帳の行)。"""

    kind: str
    id: str
    drives_from: tuple[str, ...]
    contributes: tuple[str, ...]
    absent_id: str = ""
    absent_stopped: bool = False
    absent_anchors: tuple[str, ...] = ()
    calibration_declined: tuple[str, ...] = ()
    world_process: str = ""
    note: str = ""

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.id}"


@dataclass(frozen=True)
class Overlap:
    """重なり 1 件。``exempt`` が空なら CI で落とす候補。"""

    subject: str
    system: str
    pattern_id: str
    exempt: str = ""
    detail: str = field(default="", compare=False)

    def as_dict(self) -> dict[str, str]:
        return {"subject": self.subject, "system": self.system, "pattern_id": self.pattern_id,
                "exempt": self.exempt, "detail": self.detail}


def parse_pattern_scoring(path: str | Path | None = None) -> dict[str, PatternScoring]:
    """パターン台帳の §1・§9 の表(先頭の列 ``ID``/``行``・§2 の封印表を除く)から 2 列を列の名で読む。

    Raises:
        ValueError: 2 列のある表が 1 つも無い(列を足す前の台帳)。
    """
    md = _doc_path(PATTERN_LEDGER_RELPATH, ENV_PATTERN_MD, path)
    out: dict[str, PatternScoring] = {}
    cols: tuple[int, int] | None = None
    sealed = False
    for raw in md.read_text(encoding="utf-8").split("\n"):
        line = raw.strip()
        if line.startswith("## "):
            sealed = line.startswith("## 2.")
        cells = _split_row(raw)
        if not cells:
            cols = None
            continue
        if cells[0] in ("ID", "行") and not sealed:
            cols = (cells.index(COL_SCORING), cells.index(COL_BURNED)) if COL_SCORING in cells else None
            continue
        if cols is None or set(line) <= set("|-: "):
            continue
        rid = cells[0]
        if not rid or rid.startswith("~~"):
            continue
        out[rid] = PatternScoring(rid, cells[cols[0]], cells[cols[1]])
    if not out:
        raise ValueError(f"{md}: 「{COL_SCORING}」と「{COL_BURNED}」の列のある表が無い")
    return out


def load_ledger_rows(path: str | Path | None = None) -> list[dict[str, Any]]:
    """つなぎの台帳の行(JSON の辞書のまま)。"""
    p = Path(path) if path is not None else _repo_root(BRIDGE_LEDGER_RELPATH) / BRIDGE_LEDGER_RELPATH
    return list(json.loads(p.read_text(encoding="utf-8"))["bridges"])


def _absence_info(a: Any, contributes: Iterable[str]) -> tuple[str, bool, tuple[str, ...]]:
    if a is None or a.kind not in ("no_actor", "no_port"):
        return "", False, ()
    anchors = tuple(dict.fromkeys([*a.keeps_anchor, *contributes]))
    return a.id, bool(a.engine_stopped), anchors


def subjects_from_registry(registry: Any) -> list[Subject]:
    """世界の台帳の過程と PlanSpec(``drives_from`` を書いたものだけ)。"""
    out: list[Subject] = []
    for kind, items in (("world_process", registry.processes), ("plan_spec", registry.plan_specs)):
        for p in items:
            if not p.drives_from:
                continue
            ab, stopped, anchors = _absence_info(p.absence, p.contributes)
            out.append(Subject(kind, p.id, tuple(p.drives_from), tuple(p.contributes), ab, stopped, anchors))
    return out


def subjects_from_ledger(rows: Iterable[Mapping[str, Any]], registry: Any) -> list[Subject]:
    """つなぎの台帳の active の行のうち ``drives_from`` を書いた行。``contributes`` は行の欄と、結んだ世界過程
    (``world_process``)の ``contributes`` の合併。無いの宣言は結んだ世界過程か routing の行から引く。"""
    procs = {p.id: p for p in (*registry.processes, *registry.plan_specs)}
    by_row = _AB.by_routing_row()
    out: list[Subject] = []
    for r in rows:
        if r.get("status") != "active" or not r.get("drives_from"):
            continue
        wp = str(r.get("world_process", ""))
        contrib = list(r.get("contributes", ()))
        absence = None
        if wp:
            p = procs.get(wp)
            if p is None:
                raise ValueError(f"{r['id']}: world_process {wp!r} が世界の台帳に無い")
            contrib += [c for c in p.contributes if c not in contrib]
            absence = p.absence
        n = r.get("routing_row", 0)
        if (absence is None or absence.kind not in ("no_actor", "no_port")) and n in by_row:
            absence = by_row[n]
        ab, stopped, anchors = _absence_info(absence, contrib)
        out.append(Subject("bridge", r["id"], tuple(r["drives_from"]), tuple(contrib), ab, stopped, anchors,
                           tuple(r.get("calibration_declined", ())), wp, str(r.get("drives_note", ""))))
    return out


def find_overlaps(subjects: Iterable[Subject], scoring: Mapping[str, PatternScoring]) -> list[Overlap]:
    """``drives_from`` と「採点する系」の重なり(例外の印つき)。"""
    out: list[Overlap] = []
    for s in subjects:
        for x in s.drives_from:
            if x == DRIVES_NONE:
                continue
            for pid in s.contributes:
                ps = scoring.get(pid)
                systems = ps.systems if ps is not None else frozenset({pid})
                if x not in systems:
                    continue
                note = ""
                if ps is not None and ps.exempt:
                    ex = "burned"
                elif s.absent_id and s.absent_stopped and pid in s.absent_anchors:
                    ex = "absent"
                else:
                    ex = ""
                    if s.absent_id and not s.absent_stopped:
                        note = f"・{MISMATCH}"
                out.append(Overlap(s.key, x, pid, ex,
                                   f"burned={ps.burned if ps else '(台帳に行なし)'}・absent={s.absent_id or '—'}{note}"))
    return out


def stand_in_overlap(subject_contributes: Iterable[str], anchors: Iterable[str]) -> tuple[str, ...]:
    """代打の条件 ⑤ の見方: 代打の出力が入る錨(``contributes``)と、疑いの錨の重なり。"""
    c = set(subject_contributes)
    return tuple(a for a in anchors if a in c)
