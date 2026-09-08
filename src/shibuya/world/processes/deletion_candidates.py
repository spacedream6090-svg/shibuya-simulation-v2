"""world.processes.deletion_candidates — 「削除候補」台帳ファイルの追記器(D-R2-4)。

正典
- 世界過程設計書 §5 確定文「宣言した届き先が消えた細部は、**削除候補として台帳に自動的に載る**」。
  D-R2-4 実装形「参照先が消えたら **CI が「削除候補」行を台帳へ自動追記**」。
- 知覚契約書 §1 不変条件2「宣言のない細部は削除候補として台帳に自動掲載(憲法5の機械検査)」。

置き場: 既定は ``runs/deletion_candidates.json``。
**``docs/`` の下には絶対に書かない**(設計正典は人が delta 改版する・CI が触ってよいのは runs/ だけ)。
``runs/`` は .gitignore 済み=CI の自動追記がコミット差分を汚さない。

追記は**冪等**: 重複排除鍵 = ``(subject_id, reason)``。既存行の ``detected_at`` は保存され、
同じ鍵で再追記しても上書きしない(「いつから削除候補か」が消えると台帳の意味が無い)。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Sequence

from shibuya.world.processes.constitution import DeletionCandidate

__all__ = [
    "DEFAULT_LEDGER_PATH",
    "LEDGER_VERSION",
    "load_candidates",
    "append_candidates",
    "write_candidates",
]

#: 既定の置き場(``docs/`` の下は禁止)。
DEFAULT_LEDGER_PATH = Path("runs/deletion_candidates.json")
LEDGER_VERSION = 1


def _validate_path(path: str | Path) -> Path:
    p = Path(path)
    parts = {q.lower() for q in p.parts}
    if "docs" in parts:
        raise ValueError(
            f"削除候補台帳を docs/ の下に書くことは禁止(設計正典は人が改版する): {p}"
        )
    return p


def _row_from_dict(d: dict[str, Any]) -> DeletionCandidate:
    return DeletionCandidate(
        subject_type=str(d.get("subject_type", "")),
        subject_id=str(d.get("subject_id", "")),
        reason=str(d.get("reason", "")),
        vanished_targets=tuple(d.get("vanished_targets", ()) or ()),
        detected_at=str(d.get("detected_at", "")),
    )


def load_candidates(path: str | Path = DEFAULT_LEDGER_PATH) -> tuple[DeletionCandidate, ...]:
    """台帳ファイルを読む(無ければ空タプル)。

    Raises:
        ValueError: ファイルが壊れている(JSON でない / ``rows`` が無い)。
    """
    p = _validate_path(path)
    if not p.is_file():
        return ()
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - 破損時のみ
        raise ValueError(f"削除候補台帳が壊れている: {p}") from exc
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError(f"削除候補台帳に rows が無い: {p}")
    return tuple(_row_from_dict(r) for r in rows)


def _sorted_unique(rows: Iterable[DeletionCandidate]) -> tuple[DeletionCandidate, ...]:
    merged: dict[tuple[str, str], DeletionCandidate] = {}
    for r in rows:
        key = r.dedupe_key
        if key in merged:
            old = merged[key]
            # 既存行の detected_at を保つ。届き先の集合だけは合併する(増えることがある)。
            merged[key] = DeletionCandidate(
                subject_type=old.subject_type or r.subject_type,
                subject_id=old.subject_id,
                reason=old.reason,
                vanished_targets=tuple(
                    sorted(set(old.vanished_targets) | set(r.vanished_targets))
                ),
                detected_at=old.detected_at or r.detected_at,
            )
        else:
            merged[key] = r
    return tuple(merged[k] for k in sorted(merged))


def write_candidates(
    path: str | Path, rows: Sequence[DeletionCandidate]
) -> tuple[DeletionCandidate, ...]:
    """台帳ファイルを丸ごと書き直す(並びは ``(subject_id, reason)`` 昇順=決定論)。"""
    p = _validate_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    out = _sorted_unique(rows)
    payload = {
        "version": LEDGER_VERSION,
        "source": "world.processes.constitution.check_constitution5 (D-R2-4)",
        "rows": [r.as_dict() for r in out],
    }
    p.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return out


def append_candidates(
    path: str | Path = DEFAULT_LEDGER_PATH,
    candidates: Iterable[DeletionCandidate] = (),
) -> tuple[DeletionCandidate, ...]:
    """削除候補を台帳へ**冪等に**追記する。

    Args:
        path: 台帳ファイル(既定 ``runs/deletion_candidates.json``・``docs/`` 配下は禁止)。
        candidates: 追記する行。``(subject_id, reason)`` が既存と同じなら何も増えない。

    Returns:
        追記後の全行(``(subject_id, reason)`` 昇順)。

    Raises:
        ValueError: ``docs/`` 配下を指した / 既存ファイルが壊れている。
    """
    existing = load_candidates(path)
    return write_candidates(path, tuple(existing) + tuple(candidates))
