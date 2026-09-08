"""core.soa — SoA(構造体の配列でなく配列の構造体)レジストリとバイト予算宣言(M9)。

正典
- 実装計画書 §3: 「SoA: 1フィールド=1本のNumPy配列+dtypeレジストリ(M9)。**個体オブジェクトを
  作らない**。セル(100m・453)を第一のチャンク。」
- 予算宣言表 M9: 「全状態フィールドにバイト予算宣言+テスト強制(**宣言なきフィールドはマージ不可**)」。
- 予算宣言表 M1: 個体状態の総和 **≤30KB/体**(40万体≈12GB)。内訳 M2-M6。
- CLAUDE.md §4: 全 cap/近似に ``mechanism|expedient`` タグ。

使い方
    reg = Registry.for_agents(n_agents=5_000)
    xy = reg.declare("pos_xy", np.float32, (2,), byte_budget_per_agent=8,
                     mechanism=True, doc="平面座標[m](M2 SoAコア)")
    reg.pos_xy[:] = ...
    reg.state_hash()      # 全配列の blake3(宣言順)
    reg.budget_report()   # 宣言 vs 実バイト

バイト予算の単位(**設計書の算術から導出・自前解釈ではない**)
    M3「≤12.8KB/体(64スロット×200B)」= 12,800 B、M1「≤30KB/体(40万体≈12GB)」= 12e9 B より、
    本書の KB/GB は **10進(1KB=1000B)**。``_bytes_from_limit`` はこの解釈を実装する。

逐次ループ宣言(P4)
- ``state_hash`` / ``bytes_total`` / ``budget_report``: **フィールド数**ぶんのループ(数十本の想定)。
  個体数に比例するループは持たない(配列丸ごとを blake3 に渡す)。

expedient(本モジュール分)
- セル側レジストリの**個体あたり上限**: 予算表にセル1つあたりのバイト行が存在しない
  (M10 は可視性テーブル総額 ≤512MB)。よって cell レジストリの既定 cap は None(=総額側で見る)。
- 属性アクセス(``reg.pos_xy``)は利便のための自前規約(設計書に規定なし)。正典は ``reg.arrays``。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final, Iterator, Mapping

import blake3
import numpy as np

from shibuya.core import budget as _budget

__all__ = [
    "FieldDecl",
    "FieldReport",
    "BudgetReport",
    "Registry",
    "AGENT_CAP_BUDGET_ROW",
    "CELL_CAP_BUDGET_ROW",
    "default_per_entity_byte_cap",
]

#: 個体あたりバイト上限の根拠行(予算宣言表)。
AGENT_CAP_BUDGET_ROW: Final[str] = "M1"
#: セルあたりバイト上限の根拠行は**存在しない**(expedient: 総額 M8/M10 側で見る)。
CELL_CAP_BUDGET_ROW: Final[str | None] = None

_UNIT_BYTES: Final[dict[str, int]] = {"B": 1, "KB": 1_000, "MB": 1_000_000, "GB": 1_000_000_000}
_UNIT_RE = re.compile(r"^(B|KB|MB|GB)")


def _bytes_from_limit(limit: tuple[float, str] | None) -> int | None:
    """``parse_limit`` の戻り (値, 単位) → バイト数。単位が B/KB/MB/GB 以外なら None。"""
    if limit is None:
        return None
    value, unit = limit
    m = _UNIT_RE.match(unit.strip())
    if m is None:
        return None
    return int(round(value * _UNIT_BYTES[m.group(1)]))


def default_per_entity_byte_cap(kind: str, budget_md_path: str | None = None) -> int | None:
    """種別(``"agent"``/``"cell"``)ごとの既定バイト上限を予算宣言表から読む。

    ``agent`` は M1(≤30KB/体 → 30,000 B)。``cell`` は該当行が無いため None。
    """
    if kind == "cell":
        return None
    if kind != "agent":
        raise ValueError(f"未知の kind: {kind!r}(agent か cell)")
    rows = _budget.budget_by_id(_budget.load_budget_table(budget_md_path))
    row = rows[AGENT_CAP_BUDGET_ROW]
    cap = _bytes_from_limit(_budget.parse_limit(row.declared))
    if cap is None:
        raise ValueError(f"予算行 {AGENT_CAP_BUDGET_ROW} からバイト上限を読めない: {row.declared!r}")
    return cap


@dataclass(frozen=True)
class FieldDecl:
    """1フィールドの宣言(M9)。

    Attributes:
        name: フィールド名(Python 識別子)。
        dtype: NumPy dtype。
        shape_per_entity: 個体1つあたりの形(スカラーなら ``()``)。
        byte_budget_per_entity: **宣言**バイト数/個体(M9・実バイトの上限)。
        mechanism: True=mechanism / False=expedient(CLAUDE.md §4)。
        doc: 1行の説明(どの予算行の内訳か等)。
    """

    name: str
    dtype: np.dtype
    shape_per_entity: tuple[int, ...]
    byte_budget_per_entity: int
    mechanism: bool
    doc: str

    @property
    def elements_per_entity(self) -> int:
        n = 1
        for s in self.shape_per_entity:
            n *= int(s)
        return n

    @property
    def actual_bytes_per_entity(self) -> int:
        return int(self.dtype.itemsize) * self.elements_per_entity

    @property
    def tag(self) -> str:
        return "mechanism" if self.mechanism else "expedient"


@dataclass(frozen=True)
class FieldReport:
    """``budget_report`` の1行。"""

    name: str
    dtype: str
    shape_per_entity: tuple[int, ...]
    declared_bytes_per_entity: int
    actual_bytes_per_entity: int
    actual_bytes_total: int
    mechanism: bool
    within_budget: bool


@dataclass(frozen=True)
class BudgetReport:
    """レジストリ全体の予算報告。"""

    kind: str
    n_entities: int
    per_entity_byte_cap: int | None
    cap_source: str
    declared_bytes_per_entity: int
    actual_bytes_per_entity: int
    actual_bytes_total: int
    fields: tuple[FieldReport, ...]

    @property
    def within_cap(self) -> bool:
        if self.per_entity_byte_cap is None:
            return True
        return self.declared_bytes_per_entity <= self.per_entity_byte_cap

    def as_text(self) -> str:
        head = (
            f"[{self.kind}] n={self.n_entities} "
            f"declared={self.declared_bytes_per_entity}B/体 actual={self.actual_bytes_per_entity}B/体 "
            f"cap={self.per_entity_byte_cap}B({self.cap_source}) total={self.actual_bytes_total}B"
        )
        lines = [head]
        for f in self.fields:
            tag = "mechanism" if f.mechanism else "expedient"
            lines.append(
                f"  {f.name:24s} {f.dtype:8s} {str(f.shape_per_entity):10s} "
                f"decl={f.declared_bytes_per_entity:6d} act={f.actual_bytes_per_entity:6d} {tag}"
            )
        return "\n".join(lines)


_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SEP = b"\x1f"


class Registry:
    """SoA 状態のレジストリ(個体オブジェクトを作らない)。

    フィールドは ``declare`` でのみ増える。``declare`` は **バイト予算の宣言を必須**にし
    (M9)、宣言の総和が種別ごとの上限(agent=M1)を超えると ``ValueError`` を投げる。
    """

    def __init__(
        self,
        n_entities: int,
        *,
        kind: str = "agent",
        per_entity_byte_cap: int | None | str = "auto",
        budget_md_path: str | None = None,
    ) -> None:
        """
        Args:
            n_entities: 個体数(agent)またはセル数(cell)。
            kind: ``"agent"`` か ``"cell"``。
            per_entity_byte_cap: ``"auto"``=予算表から読む(agent→M1・cell→None)。
                明示の int で上書き可(縮小ランの検査用)。None=上限なし。
            budget_md_path: 予算表 Markdown の場所(既定=リポジトリ探索)。
        """
        if int(n_entities) < 0:
            raise ValueError("n_entities は 0 以上")
        if kind not in ("agent", "cell"):
            raise ValueError(f"未知の kind: {kind!r}(agent か cell)")
        self.n_entities = int(n_entities)
        self.kind = kind
        if isinstance(per_entity_byte_cap, str):
            if per_entity_byte_cap != "auto":
                raise ValueError("per_entity_byte_cap は int / None / 'auto'")
            self.per_entity_byte_cap = default_per_entity_byte_cap(kind, budget_md_path)
            self.cap_source = (
                f"予算行 {AGENT_CAP_BUDGET_ROW}" if kind == "agent" else "該当行なし(expedient)"
            )
        else:
            self.per_entity_byte_cap = (
                None if per_entity_byte_cap is None else int(per_entity_byte_cap)
            )
            self.cap_source = "呼び出し側指定"
        self._decls: dict[str, FieldDecl] = {}
        self._arrays: dict[str, np.ndarray] = {}

    # ---- 生成ヘルパ ----
    @classmethod
    def for_agents(cls, n_agents: int, **kw: Any) -> "Registry":
        """個体レジストリ(上限=予算行 M1)。"""
        return cls(n_agents, kind="agent", **kw)

    @classmethod
    def for_cells(cls, n_cells: int, **kw: Any) -> "Registry":
        """セルレジストリ(個体あたり上限の予算行は存在しない=None)。"""
        return cls(n_cells, kind="cell", **kw)

    # ---- 宣言 ----
    def declare(
        self,
        field: str,
        dtype: Any,
        shape_per_agent: tuple[int, ...] = (),
        *,
        byte_budget_per_agent: int | None = None,
        mechanism: bool | None = None,
        doc: str = "",
        fill: Any = None,
    ) -> np.ndarray:
        """フィールドを宣言して配列を確保する。

        Args:
            field: フィールド名。
            dtype: NumPy dtype。
            shape_per_agent: 個体1つあたりの形(セルレジストリでは「セル1つあたり」)。
            byte_budget_per_agent: **必須**(M9)。個体あたりの宣言バイト数。
            mechanism: **必須**。True=mechanism / False=expedient。
            doc: 1行説明(どの予算行の内訳か)。
            fill: 初期値(None なら 0 埋め)。

        Returns:
            確保した配列(形は ``(n_entities, *shape_per_agent)``)。

        Raises:
            ValueError: 予算宣言・タグがない / 実バイトが宣言を超える / 総和が cap を超える /
                名前が不正・重複。
        """
        if not _NAME_RE.match(field):
            raise ValueError(f"フィールド名が不正: {field!r}")
        if field in self._decls:
            raise ValueError(f"フィールドの重複宣言: {field!r}")
        if byte_budget_per_agent is None:
            raise ValueError(
                f"M9: フィールド {field!r} にバイト予算宣言がない(宣言なきフィールドはマージ不可)"
            )
        if mechanism is None:
            raise ValueError(f"CLAUDE.md §4: フィールド {field!r} に mechanism|expedient タグがない")
        if not doc:
            raise ValueError(f"M9: フィールド {field!r} に doc(1行説明)がない")
        budget = int(byte_budget_per_agent)
        if budget <= 0:
            raise ValueError(f"バイト予算は正: {field}={budget}")

        shape = tuple(int(s) for s in shape_per_agent)
        for s in shape:
            if s <= 0:
                raise ValueError(f"shape_per_agent は正の整数のみ: {shape}")
        decl = FieldDecl(field, np.dtype(dtype), shape, budget, bool(mechanism), doc)

        if decl.actual_bytes_per_entity > budget:
            raise ValueError(
                f"M9: フィールド {field!r} の実バイト {decl.actual_bytes_per_entity}B/体 が"
                f"宣言 {budget}B/体 を超える"
            )
        new_declared = self.declared_bytes_per_entity + budget
        if self.per_entity_byte_cap is not None and new_declared > self.per_entity_byte_cap:
            raise ValueError(
                f"{self.cap_source}: 宣言総和 {new_declared}B/体 が上限 "
                f"{self.per_entity_byte_cap}B/体 を超える(追加フィールド {field!r}={budget}B)"
            )

        arr = np.zeros((self.n_entities, *shape), dtype=decl.dtype)
        if fill is not None:
            arr[...] = fill
        self._decls[field] = decl
        self._arrays[field] = arr
        return arr

    # ---- 参照 ----
    @property
    def arrays(self) -> Mapping[str, np.ndarray]:
        """フィールド名 → 配列(宣言順の辞書コピー)。"""
        return dict(self._arrays)

    @property
    def decls(self) -> tuple[FieldDecl, ...]:
        """宣言順のフィールド宣言。"""
        return tuple(self._decls.values())

    def field(self, name: str) -> np.ndarray:
        """フィールド配列を名前で引く。"""
        try:
            return self._arrays[name]
        except KeyError:
            raise KeyError(f"未宣言のフィールド: {name!r}") from None

    def __getattr__(self, name: str) -> np.ndarray:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.__dict__["_arrays"][name]
        except KeyError:
            raise AttributeError(f"未宣言のフィールド: {name!r}") from None

    def __contains__(self, name: object) -> bool:
        return name in self._arrays

    def __iter__(self) -> Iterator[str]:
        return iter(self._arrays)

    def __len__(self) -> int:
        return len(self._arrays)

    # ---- 予算 ----
    @property
    def declared_bytes_per_entity(self) -> int:
        """宣言バイト/個体の総和。"""
        return sum(d.byte_budget_per_entity for d in self._decls.values())

    @property
    def actual_bytes_per_entity(self) -> int:
        """実バイト/個体の総和。"""
        return sum(d.actual_bytes_per_entity for d in self._decls.values())

    def bytes_total(self) -> int:
        """確保済み配列の実バイト総額(``arr.nbytes`` の和)。"""
        return int(sum(int(a.nbytes) for a in self._arrays.values()))

    def budget_report(self) -> BudgetReport:
        """宣言 vs 実バイトの報告(M9 のテスト強制に使う)。"""
        fields = tuple(
            FieldReport(
                name=d.name,
                dtype=d.dtype.str,
                shape_per_entity=d.shape_per_entity,
                declared_bytes_per_entity=d.byte_budget_per_entity,
                actual_bytes_per_entity=d.actual_bytes_per_entity,
                actual_bytes_total=int(self._arrays[d.name].nbytes),
                mechanism=d.mechanism,
                within_budget=d.actual_bytes_per_entity <= d.byte_budget_per_entity,
            )
            for d in self._decls.values()
        )
        return BudgetReport(
            kind=self.kind,
            n_entities=self.n_entities,
            per_entity_byte_cap=self.per_entity_byte_cap,
            cap_source=self.cap_source,
            declared_bytes_per_entity=self.declared_bytes_per_entity,
            actual_bytes_per_entity=self.actual_bytes_per_entity,
            actual_bytes_total=self.bytes_total(),
            fields=fields,
        )

    # ---- ハッシュ ----
    def state_hash(self) -> str:
        """全配列の blake3(**宣言順**・名前/dtype/形/生バイトを連結)→ 64桁16進。

        checkpoint 往復・録画リプレイ回帰(T2)の一致判定に使う。
        """
        h = blake3.blake3()
        h.update(b"shibuya.core.soa/v1" + _SEP)
        h.update(self.kind.encode("utf-8") + _SEP)
        h.update(str(self.n_entities).encode("ascii") + _SEP)
        for d in self._decls.values():
            arr = self._arrays[d.name]
            h.update(d.name.encode("utf-8") + _SEP)
            h.update(d.dtype.str.encode("ascii") + _SEP)
            h.update(str(arr.shape).encode("ascii") + _SEP)
            flat = np.ascontiguousarray(arr).reshape(-1)
            h.update(flat.view(np.uint8) if flat.size else b"")
            h.update(_SEP)
        return h.hexdigest()
