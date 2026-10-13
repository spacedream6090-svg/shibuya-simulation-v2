"""engine.rules.table — 規則の表(第 1 期 1-4・CP10・決定 10-12 §1-12「現実の法と制度に基づいて実装する」)。

法と制度を「出典と版つきの規則の表」として持つ器。1 行=``Rule``:

- ``kind``: ``machine``=機械が守らせる(税の計算・天引き・改札など=規範の MAS の regimentation)/ ``human``=人が
  知っていて人が取り締まる(条例・営業の規制など=enforcement。違反は記録し、周りの人が事後に反応する)。
- ``source``: 出典(法令名・条・版・URL。e-Gov の法令 ID と取得日があれば添える=R-106 §5-3)。1 つ以上。
- ``asof``: この行の値が効く最初の日(施行日)。``Rules.get(id, asof)`` は ``asof`` の日に効いている版(``asof`` が
  その日以前の行のうち最も新しい行)を返す=OpenFisca 型の「施行日つきの列」(R-106 §5-3)。
- ``params``: 値(JSON の値だけ・凍結)。``applies_to``: PlanSpec の条件の形を参照する欄(今は文字列の条件式か空)。

**1-4 では読み手を作らない**(口の約束 1-4 の約束 (1)=表を読んでも挙動は変わらない)。既存の直書きの係数は 4-2 まで
そのまま残し、つなぎの台帳に載せる。中身(実在の規則)は E4(R-106)の後に 4-2 で入れる。1-4 の中身は 3 行だけ
(``docs/design/rules-table.json``)。表の sha(正規化した JSON の sha256 の先頭 16 桁=改行の違いに左右されない)を
manifest の ``rules_version`` と日次の記録の同じ名の欄に出す(CP10: どのランも開始時の版で最後まで走る)。

先例: OpenFisca(値を日付ごとに持ち出典の URL を付ける・AGPL-3.0=読むだけ)・Catala・e-Gov 法令 API v2 の時点の
指定(R-106 §5・R-113 §4)。コードは写していない。

逐次ループ宣言: なし(読むのはランごとに 1 回)。
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import warnings
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Iterable, Iterator, Mapping

__all__ = [
    "SCHEMA", "TABLE_RELPATH", "KINDS", "KIND_MACHINE", "KIND_HUMAN",
    "Source", "Rule", "Rules", "RuleNotInForce", "load", "default_path", "default_rules", "rules_version",
    "canonical_sha",
]

#: 表の形式の版(欄を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.rules-table/1"
#: リポの根からの表の道筋。
TABLE_RELPATH: Final[str] = "docs/design/rules-table.json"
KIND_MACHINE: Final[str] = "machine"
KIND_HUMAN: Final[str] = "human"
KINDS: Final[tuple[str, ...]] = (KIND_MACHINE, KIND_HUMAN)
_ID = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)*$")


class RuleNotInForce(LookupError):
    """``asof`` の日に効いている版が表に無い(施行の前・または表に版が無い)。"""


def _iso_date(value: Any, name: str) -> str:
    if isinstance(value, _dt.date):
        return value.isoformat()
    try:
        return _dt.date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise ValueError(f"{name} は YYYY-MM-DD(いま {value!r})") from exc


def _freeze(v: Any, where: str) -> Any:
    """JSON の値を凍結した形に(dict → MappingProxyType・list → tuple)。JSON の外の型は ValueError。"""
    if isinstance(v, Mapping):
        if any(not isinstance(k, str) for k in v):
            raise ValueError(f"{where}: 鍵は文字列")
        return MappingProxyType({k: _freeze(x, f"{where}.{k}") for k, x in v.items()})
    if isinstance(v, (list, tuple)):
        return tuple(_freeze(x, where) for x in v)
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    raise ValueError(f"{where}: JSON の値だけ(いま {type(v).__name__})")


def _thaw(v: Any) -> Any:
    if isinstance(v, Mapping):
        return {k: _thaw(x) for k, x in v.items()}
    if isinstance(v, tuple):
        return [_thaw(x) for x in v]
    return v


@dataclass(frozen=True, slots=True)
class Source:
    """規則の出典 1 つ(法令名・条・版・URL は必須)。"""

    law: str
    article: str
    version: str
    url: str
    law_id: str = ""
    retrieved: str = ""

    def __post_init__(self) -> None:
        for name in ("law", "article", "version", "url"):
            v = getattr(self, name)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"Source.{name} は必須(空でない文字列)")
        if not self.url.startswith("https://"):
            raise ValueError(f"Source.url は https:// で始まる(いま {self.url!r})")
        if self.retrieved:
            _iso_date(self.retrieved, "Source.retrieved")

    def as_dict(self) -> dict[str, str]:
        d = {"law": self.law, "article": self.article, "version": self.version, "url": self.url}
        if self.law_id:
            d["law_id"] = self.law_id
        if self.retrieved:
            d["retrieved"] = self.retrieved
        return d


@dataclass(frozen=True, slots=True)
class Rule:
    """規則の表の 1 行(凍結)。"""

    id: str
    kind: str
    source: tuple[Source, ...]
    asof: str
    params: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    applies_to: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _ID.match(self.id):
            raise ValueError(f"Rule.id は小文字・数字・_ を . でつないだ名(いま {self.id!r})")
        if self.kind not in KINDS:
            raise ValueError(f"Rule.kind は {KINDS}(id={self.id!r})")
        src = tuple(self.source)
        if not src or any(not isinstance(s, Source) for s in src):
            raise ValueError(f"Rule.source は Source を 1 つ以上(id={self.id!r}・出典と版は必須)")
        object.__setattr__(self, "source", src)
        object.__setattr__(self, "asof", _iso_date(self.asof, f"Rule.asof(id={self.id!r})"))
        if not isinstance(self.params, Mapping):
            raise ValueError(f"Rule.params は辞書(id={self.id!r})")
        object.__setattr__(self, "params", _freeze(self.params, f"Rule.params(id={self.id!r})"))
        if not isinstance(self.applies_to, str) or not isinstance(self.note, str):
            raise ValueError(f"Rule.applies_to と note は文字列(id={self.id!r})")

    def as_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self.id, "kind": self.kind, "asof": self.asof,
                             "source": [s.as_dict() for s in self.source], "params": _thaw(self.params),
                             "applies_to": self.applies_to}
        if self.note:
            d["note"] = self.note
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Rule":
        known = {"id", "kind", "asof", "source", "params", "applies_to", "note"}
        extra = set(d) - known
        if extra:
            raise ValueError(f"Rule に知らない欄 {sorted(extra)}(id={d.get('id')!r})")
        missing = {"id", "kind", "asof", "source"} - set(d)
        if missing:
            raise ValueError(f"Rule に要る欄が無い {sorted(missing)}(id={d.get('id')!r})")
        srcs = d["source"]
        if not isinstance(srcs, list):
            raise ValueError(f"Rule.source は並び(id={d.get('id')!r})")
        return cls(id=d["id"], kind=d["kind"], asof=d["asof"],
                   source=tuple(Source(**s) for s in srcs), params=d.get("params", {}),
                   applies_to=d.get("applies_to", ""), note=d.get("note", ""))


class Rules:
    """規則の表(読むだけ)。行の差し替え・属性の付け替えはできない(1-3 検収 L2 の守り)。"""

    __slots__ = ("_by_id", "_sha", "_n")

    def __init__(self, rows: Iterable[Rule], *, sha: str = "") -> None:
        groups: dict[str, list[Rule]] = {}
        n = 0
        for r in rows:
            if not isinstance(r, Rule):
                raise TypeError("Rules の行は Rule")
            groups.setdefault(r.id, []).append(r)
            n += 1
        by_id: dict[str, tuple[Rule, ...]] = {}
        for rid, rs in groups.items():
            rs.sort(key=lambda r: r.asof)
            dates = [r.asof for r in rs]
            if len(set(dates)) != len(dates):
                raise ValueError(f"同じ規則 {rid!r} に同じ asof の行が 2 つ")
            by_id[rid] = tuple(rs)
        object.__setattr__(self, "_by_id", MappingProxyType(dict(sorted(by_id.items()))))
        object.__setattr__(self, "_sha", str(sha))
        object.__setattr__(self, "_n", n)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"Rules は読むだけ({name} は書けない)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"Rules は読むだけ({name} は消せない)")

    def __len__(self) -> int:
        return self._n

    def __iter__(self) -> Iterator[Rule]:
        for rs in self._by_id.values():
            yield from rs

    @property
    def sha(self) -> str:
        """表の中身の sha256(正規化した JSON の先頭 16 桁)。manifest の ``rules_version``。"""
        return self._sha

    def ids(self) -> tuple[str, ...]:
        return tuple(self._by_id)

    def versions(self, rule_id: str) -> tuple[Rule, ...]:
        """規則 ``rule_id`` の全部の版(asof の昇順)。無い id は ``KeyError``。"""
        return self._by_id[rule_id]

    def get(self, rule_id: str, asof: str | _dt.date) -> Rule:
        """``asof`` の日に効いている版。無い id は ``KeyError``・施行の前は ``RuleNotInForce``。"""
        day = _iso_date(asof, "asof")
        rs = self._by_id[rule_id]
        hit = [r for r in rs if r.asof <= day]
        if not hit:
            raise RuleNotInForce(f"{rule_id!r} は {day} に効いている版が無い(最初の版 {rs[0].asof})")
        return hit[-1]


def canonical_sha(obj: Any) -> str:
    """正規化した JSON(鍵の昇順・区切りの空白なし・UTF-8)の sha256 の先頭 16 桁(改行の違いに左右されない)。"""
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def default_path() -> Path:
    """リポの表の道筋(``<リポの根>/docs/design/rules-table.json``)。"""
    return Path(__file__).resolve().parents[4] / TABLE_RELPATH


def load(path: str | Path | None = None) -> Rules:
    """表を読む(形式の版・欄の検査つき)。"""
    p = Path(path) if path is not None else default_path()
    doc = json.loads(p.read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"規則の表の形式が違う: {doc.get('schema')!r}(期待 {SCHEMA!r})")
    return Rules((Rule.from_dict(d) for d in doc.get("rules", [])), sha=canonical_sha(doc))


@lru_cache(maxsize=1)
def default_rules() -> Rules:
    """リポの表(1 回だけ読む)。"""
    return load(None)


def rules_version() -> str | None:
    """manifest と日次の記録の ``rules_version``(表の sha)。表のファイルが無い写しでは ``None``(ランは止めない)。"""
    try:
        return default_rules().sha
    except FileNotFoundError:
        warnings.warn(f"規則の表 {TABLE_RELPATH} が無い写し: rules_version は null", RuntimeWarning, stacklevel=2)
        return None
