"""engine.bridging.ledger — つなぎの台帳(第 1 期 1-4・CA8・計器の最初)。

決定: 実装の計画 10-12 §1 の 3(新しいつなぎは台帳に載せ「外す段」を書く・計器の最初に置く)・口の約束 1-4
(``Bridge`` の欄・台帳は docs(git)に置く=回答 10-13b §3)・回答 10-13b §4-2 の 2(不応期 11 種と起床条件の
クラスは「T3 で外す」)。

- 台帳の正は ``docs/design/bridging-ledger.json``(git・件数が計器なので履歴が要る)。1 行=``Bridge``。
- 読み口は ``load``(道筋を渡す)と ``default_ledger``(リポの台帳・1 回だけ読む)。件数 ``bridges_count`` は
  manifest の ``bridges_count`` と日次の記録の同じ名の欄に載る(TM9 の欄=T0 で null にした欄)。台帳の中身の sha
  ``bridges_version`` は manifest に載る(検収 L1=件数が同じ書き換えもランの記録から見分ける)。
- **件数は宣言の行の数で、一意のつなぎの数ではない**(同じ近似をコードと文書の 2 か所以上で宣言した行がある=
  記録 r14/README.md §3-3 の重なりの一覧。重なりの id を行に持たせるのは 2-0 の課題)。
- **表を読んでも挙動は変わらない**(読み手は manifest と記録だけ)。
- コードの expedient の宣言(``engine.bridging.scan`` が数える 6 形)は ``declared_in`` が ``src/...#<形>:<鍵>``
  の行と 1 対 1(試験 ``tests/engine/bridging/test_bridging_ledger.py``)。文書で宣言したつなぎは ``declared_in`` が
  ``docs/...``(コードの宣言が無くてよい=逆向きは文書だけの行を許す)。
- ``status``: ``active`` の行だけを数え、突き合わせる(検収 L2)。外したつなぎは ``removed`` で残してよい(コードの
  宣言を消した後の履歴)。``removed`` の行がまだコードにある宣言を指すと、その宣言は「台帳に行が無い」で落ちる。
- ``remove_at`` は計画の段の番号(``PLAN_STAGES`` の閉じた表)。``7`` は第 7 期(評価と主張の前の条件)=外す段が
  計画に無く、主張の前に感度試験で「結果を駆動していない」ことを示す行(CLAUDE.md §4)。
- ``remove_basis``: ``plan``=計画・決定・回答の文に外す段が書いてある / ``declared``=コードの宣言の返済期限
  (``repayment_due``)が書く行き先を計画の段に読み替えた / ``inferred``=実装役が段を当てた(仮採用・親が確かめる)。
  ``code_at``: 文書で宣言した行の、関わるコードの場所(読むだけの手がかり)。``rule_id``: 規則の表の行に結ぶ直書きの
  係数の行(検収 L7・口の約束 1-4 の約束 (1)「既存の直書きの係数は 4-2 まで残す=つなぎとして台帳へ」)。この 3 欄は
  口の約束の欄に足した(仮採用)。

先例: TRACE(Grimm ほか 2014)の「仮定ごとに根拠と確かめ方」の文書の型・MATSim の ``config_reduced``(既定と違う
設定だけ)。「外す段つきの行をコードの宣言と AST で 1 対 1 に突き合わせる」先例は無い(R-113 §4=自前の構成)。

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
    "SCHEMA", "LEDGER_RELPATH", "CONFS", "STATUSES", "REMOVE_BASES", "PLAN_STAGES",
    "Bridge", "BridgeLedger", "load", "default_path", "default_ledger", "bridges_count", "bridges_version",
    "canonical_sha", "code_mismatch",
]

#: 台帳の形式の版(欄を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.bridging-ledger/1"
#: リポの根からの台帳の道筋。
LEDGER_RELPATH: Final[str] = "docs/design/bridging-ledger.json"
CONFS: Final[tuple[str, ...]] = ("expedient", "mechanism")
STATUSES: Final[tuple[str, ...]] = ("active", "removed")
REMOVE_BASES: Final[tuple[str, ...]] = ("plan", "declared", "inferred")
#: 外す段の閉じた表(実装の計画 10-12 §2 の段の番号・``5-N``=空間の段 N・``T1``〜``T4``=時計の段・``7``=第 7 期)。
#: 〔第 2 期 2-3b・親の指示〕``2-3c``(鉄道の続き=終点の到着・直通の二重計上のまとめ方=2-3b は渋谷の発車だけ)を足した。
PLAN_STAGES: Final[frozenset[str]] = frozenset({
    *(f"1-{i}" for i in range(11)), "1-0b", "1-8b",
    "2-0", "2-0b", "2-1", "2-2", "2-3", "2-3b", "2-3c", "2-4",
    *(f"3-{i}" for i in range(1, 6)),
    "4-1", "4-1b", "4-2", "4-3",
    *(f"5-{i}" for i in range(7)),
    "5-1b",  # 〔第 5 期 空間の段 1 の再検収 H1・親の判断〕抽出のランの密度の推定の直し(段 1 の後の小さな段)
    *(f"6-{i}" for i in range(1, 8)),
    "7", "T1", "T2", "T3", "T4",
    # 〔小さな版上げ・meal_w17 検収 L6〕``next-bump``=次の版上げ(回答 10-13b §0-6「版上げで新しい道を既定にしたら、古い道の
    # 切替口は次の版上げで消す」=旧値の再現のためだけの切替口の行)。段の番号ではなく版上げの順で決まる
    "next-bump",
})
_DOC_PREFIX = "docs/"
_CODE_PREFIX = "src/"
_RULE_ID = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)*$")
_FIELDS: Final[tuple[str, ...]] = (
    "id", "what", "why", "remove_at", "declared_in", "conf", "since", "status", "remove_basis")


def _iso_date(value: str, name: str) -> str:
    try:
        _dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} は YYYY-MM-DD(いま {value!r})") from exc
    return value


@dataclass(frozen=True, slots=True)
class Bridge:
    """つなぎの台帳の 1 行(凍結)。"""

    id: str
    what: str
    why: str
    remove_at: str
    declared_in: str
    conf: str
    since: str
    status: str = "active"
    remove_basis: str = "plan"
    code_at: tuple[str, ...] = field(default=())
    rule_id: str = ""

    def __post_init__(self) -> None:
        for name in _FIELDS:
            v = getattr(self, name)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"Bridge.{name} は空でない文字列(id={self.id!r})")
        if self.remove_at not in PLAN_STAGES:
            raise ValueError(f"Bridge.remove_at は計画の段の番号(id={self.id!r}・いま {self.remove_at!r})")
        if self.conf not in CONFS:
            raise ValueError(f"Bridge.conf は {CONFS}(id={self.id!r})")
        if self.status not in STATUSES:
            raise ValueError(f"Bridge.status は {STATUSES}(id={self.id!r})")
        if self.remove_basis not in REMOVE_BASES:
            raise ValueError(f"Bridge.remove_basis は {REMOVE_BASES}(id={self.id!r})")
        if not self.declared_in.startswith((_DOC_PREFIX, _CODE_PREFIX)):
            raise ValueError(f"Bridge.declared_in は docs/ か src/ で始まる(id={self.id!r})")
        if self.declared_in.startswith(_CODE_PREFIX) and "#" not in self.declared_in:
            raise ValueError(f"コードの宣言の declared_in は <道筋>#<形>:<鍵>(id={self.id!r})")
        _iso_date(self.since, "Bridge.since")
        code_at = tuple(self.code_at)
        if any(not isinstance(c, str) or not c.startswith(_CODE_PREFIX) for c in code_at):
            raise ValueError(f"Bridge.code_at は src/ で始まる道筋の並び(id={self.id!r})")
        object.__setattr__(self, "code_at", code_at)
        if not isinstance(self.rule_id, str) or (self.rule_id and not _RULE_ID.match(self.rule_id)):
            raise ValueError(f"Bridge.rule_id は規則の表の id の形か空(id={self.id!r})")

    @property
    def declared_in_code(self) -> bool:
        """コードの宣言(``src/...#<形>:<鍵>``)の行か。"""
        return self.declared_in.startswith(_CODE_PREFIX)

    @property
    def declared_path(self) -> str:
        """宣言の置き場のファイルの道筋(``#`` と `` §…`` の注を落とした部分)。"""
        return self.declared_in.split("#", 1)[0].split(" ", 1)[0]

    def as_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {k: getattr(self, k) for k in _FIELDS}
        if self.code_at:
            d["code_at"] = list(self.code_at)
        if self.rule_id:
            d["rule_id"] = self.rule_id
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Bridge":
        if not isinstance(d, Mapping):
            raise ValueError(f"Bridge の行は辞書(いま {type(d).__name__})")
        known = {*_FIELDS, "code_at", "rule_id"}
        extra = set(d) - known
        if extra:
            raise ValueError(f"Bridge に知らない欄 {sorted(extra)}(id={d.get('id')!r})")
        missing = {"id", "what", "why", "remove_at", "declared_in", "conf", "since"} - set(d)
        if missing:
            raise ValueError(f"Bridge に要る欄が無い {sorted(missing)}(id={d.get('id')!r})")
        kw = dict(d)
        kw["code_at"] = tuple(kw.get("code_at", ()))
        return cls(**kw)


class BridgeLedger:
    """つなぎの台帳(読むだけ)。行の差し替え・属性の付け替えはできない(1-3 検収 L2 の守り)。"""

    __slots__ = ("_rows", "_by_id", "_sha", "_frozen")

    def __init__(self, rows: Iterable[Bridge], *, sha: str = "") -> None:
        rows_t = tuple(rows)
        if any(not isinstance(r, Bridge) for r in rows_t):
            raise TypeError("BridgeLedger の行は Bridge")
        by_id: dict[str, Bridge] = {}
        code_keys: set[str] = set()
        for r in rows_t:
            if r.id in by_id:
                raise ValueError(f"つなぎの台帳の id が重なる: {r.id!r}")
            by_id[r.id] = r
            if r.declared_in_code and r.status == "active":
                if r.declared_in in code_keys:
                    raise ValueError(f"同じコードの宣言を active の 2 行が指す: {r.declared_in!r}")
                code_keys.add(r.declared_in)
        object.__setattr__(self, "_rows", rows_t)
        object.__setattr__(self, "_by_id", MappingProxyType(by_id))
        object.__setattr__(self, "_sha", str(sha))
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"BridgeLedger は読むだけ({name} は書けない)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"BridgeLedger は読むだけ({name} は消せない)")

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self) -> Iterator[Bridge]:
        return iter(self._rows)

    @property
    def rows(self) -> tuple[Bridge, ...]:
        return self._rows

    @property
    def by_id(self) -> Mapping[str, Bridge]:
        return self._by_id

    @property
    def sha(self) -> str:
        """台帳の中身の sha256(正規化した JSON の先頭 16 桁)。manifest の ``bridges_version``。"""
        return self._sha

    def get(self, bridge_id: str) -> Bridge:
        return self._by_id[bridge_id]

    def active(self) -> tuple[Bridge, ...]:
        return tuple(r for r in self._rows if r.status == "active")

    def count(self) -> int:
        """計器の件数(``status=active`` の行の数=宣言の行の数で、一意のつなぎの数ではない)。"""
        return len(self.active())

    def code_keys(self) -> frozenset[str]:
        """コードの宣言を指す active の行の ``declared_in``(``removed`` の行は突き合わせの外=検収 L2)。"""
        return frozenset(r.declared_in for r in self.active() if r.declared_in_code)

    def by_remove_at(self) -> dict[str, int]:
        """外す段ごとの件数(active の行・段の名の順)。"""
        out: dict[str, int] = {}
        for r in self.active():
            out[r.remove_at] = out.get(r.remove_at, 0) + 1
        return dict(sorted(out.items()))


def code_mismatch(ledger: BridgeLedger, declared: Iterable[str]) -> tuple[list[str], list[str]]:
    """コードの宣言(``scan`` の ``declared_in`` の並び)と台帳の active の行の突き合わせ。

    Returns:
        (台帳に active の行の無いコードの宣言, コードの宣言を指すのにコードに無い active の行の ``declared_in``)。
        どちらも空=1 対 1。文書で宣言した行(``docs/...``)と ``removed`` の行は突き合わせない。
    """
    code = set(declared)
    keys = ledger.code_keys()
    return sorted(d for d in code if d not in keys), sorted(k for k in keys if k not in code)


def canonical_sha(obj: Any) -> str:
    """正規化した JSON(鍵の昇順・区切りの空白なし・UTF-8)の sha256 の先頭 16 桁(改行の違いに左右されない)。"""
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def default_path() -> Path:
    """リポの台帳の道筋(``<リポの根>/docs/design/bridging-ledger.json``)。"""
    return Path(__file__).resolve().parents[4] / LEDGER_RELPATH


def load(path: str | Path | None = None) -> BridgeLedger:
    """台帳を読む(形式の版・欄の検査つき。壊れた JSON・知らない欄・不正な値は ``ValueError``)。"""
    p = Path(path) if path is not None else default_path()
    try:
        doc = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"つなぎの台帳 {p.name} の JSON が壊れている: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise ValueError(f"つなぎの台帳の形式が違う(期待 {SCHEMA!r})")
    rows = doc.get("bridges")
    if not isinstance(rows, list):
        raise ValueError("つなぎの台帳の bridges は並び")
    return BridgeLedger([Bridge.from_dict(d) for d in rows], sha=canonical_sha(doc))


@lru_cache(maxsize=1)
def default_ledger() -> BridgeLedger:
    """リポの台帳(1 回だけ読む)。"""
    return load(None)


def _or_none(get: Any, name: str) -> Any:
    try:
        return get(default_ledger())
    except FileNotFoundError:
        warnings.warn(f"つなぎの台帳 {LEDGER_RELPATH} が無い写し: {name} は null", RuntimeWarning, stacklevel=3)
        return None


def bridges_count() -> int | None:
    """manifest と日次の記録の ``bridges_count``(active の行の数)。台帳のファイルが無い写し(``git archive`` で
    ``src`` だけを取った木など)では ``None``=欄は今までどおり null(ランは止めない)。壊れた台帳は ``ValueError``。"""
    return _or_none(lambda led: led.count(), "bridges_count")


def bridges_version() -> str | None:
    """manifest の ``bridges_version``(台帳の中身の sha=検収 L1)。台帳のファイルが無い写しでは ``None``。"""
    return _or_none(lambda led: led.sha, "bridges_version")
