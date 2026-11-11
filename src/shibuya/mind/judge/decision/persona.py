"""engine.decision.persona — 人物の欄(第 4 期 4-3 段 10・親の判断 仮-33 (6)=判断の入力に短い版・LLM の入力に長い版)。

正: 設計書 PS7(``docs/design/v2-persona-population-rebuild-design.md`` §2-5)・決定 10-12 §4-7 DM4(短い版と長い版を 1 つの
仕組みで・共通部分を前に)・段 9 の文(``data/world/<差し替え>/w21_persona_{short,long}.parquet``=事実から決まった形で組んだ文・
LLM に書かせない)・記録 pop41c §4。

- **欄**: :class:`PersonaTable`=ランの体の並び(SoA の行)ごとの短い版と長い版の文(読むだけ・書き込み禁止の配列)・言語の印
  (``lang_basis``)・文の出どころ(``text_source``)・名指しの番号(``named_poi``・``named_org``=CP5-3 を番号で見る口)。母集団が
  差し替えの版(``Population.w21_person_id``)のときだけ :func:`load_persona` が作る。W16 の残す行(来街者・運輸ほか)は文が
  空(人物の文の材料が無い)。
- **置き場**: :func:`persona_blocks` が描画のブロックの名 :data:`BLOCK_SHORT`(短い版=B6 の前)・:data:`BLOCK_LONG`(長い版=
  B5 の前)で返し、``engine.decision.port.compose`` が個体の部分の頭に置く(共通部分 B0〜B4b は触らない=短い版と長い版の
  頭は同じバイトのまま)。今のランの判断の入力(J0 の知覚の描画)には入れない(``compose`` を使う 6-1 の器と判断モデルの段が
  読む=既定のランの結果は動かない)。
- **差し替えの口**: :func:`override`(4-1b の腕「LLM が書いた人物像」を刺す=体の行と新しい文と出どころの名・元の文は
  ``original`` に残す・表に無い体と空の出どころは止める)。

逐次ループ宣言(P4): なし(配列演算。``load_persona`` は表の読みと引き直しだけ)。
"""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import numpy as np

__all__ = ["PERSONA_FILES", "VERSIONS", "BLOCK_SHORT", "BLOCK_LONG", "BLOCK_OF_VERSION", "PersonaTable",
           "PersonaError", "load_persona", "persona_blocks", "override"]

#: 段 9 の文の表(``build.pop.w21_build_c.OUTPUTS_C`` の名と同じ=試験が突き合わせる)。
PERSONA_FILES: Final[Mapping[str, str]] = MappingProxyType({"short": "w21_persona_short.parquet",
                                                           "long": "w21_persona_long.parquet"})
#: 版(``engine.decision.port.LENGTHS`` と同じ語)。
VERSIONS: Final[tuple[str, ...]] = ("short", "long")
#: 描画のブロックの名(``compose`` が個体の部分の頭に置く=短い版は B6 の前・長い版は B5 の前)。
BLOCK_SHORT: Final[str] = "PS"
BLOCK_LONG: Final[str] = "PL"
BLOCK_OF_VERSION: Final[Mapping[str, str]] = MappingProxyType({"short": BLOCK_SHORT, "long": BLOCK_LONG})
_READ_COLUMNS: Final[tuple[str, ...]] = ("person_id", "text", "text_source", "lang", "lang_basis", "named_poi",
                                         "named_org")


class PersonaError(ValueError):
    """人物の欄の読み・差し替えの口の誤り(表に無い体・空の出どころ・列の欠け・人の番号の重なり)。"""


def _ro(a: Any, dtype: Any = None) -> np.ndarray:
    out = np.array(a, dtype=dtype, copy=True)
    out.setflags(write=False)
    return out


class PersonaTable:
    """ランの体の並びごとの人物の文(読むだけ)。``texts[版]`` は SoA の行の並びの文(文の無い体は空)。"""

    __slots__ = ("texts", "original", "source", "lang", "lang_basis", "named_poi", "named_org", "person_id", "meta")

    def __init__(self, *, texts: Mapping[str, Any], source: Mapping[str, Any], lang: Any, lang_basis: Any,
                 named_poi: Mapping[str, Any], named_org: Any, person_id: Any,
                 original: Mapping[str, Any] | None = None, meta: Mapping[str, Any] | None = None) -> None:
        n = int(np.asarray(person_id).size)
        for v in VERSIONS:
            if np.asarray(texts[v]).size != n:
                raise PersonaError(f"{v} の文の数 {np.asarray(texts[v]).size} が体の数 {n} と違う")
        self.texts = MappingProxyType({v: _ro(texts[v], object) for v in VERSIONS})
        self.original = MappingProxyType({v: _ro((original or {}).get(v, np.full(n, None, dtype=object)), object)
                                          for v in VERSIONS})
        self.source = MappingProxyType({v: _ro(source[v], object) for v in VERSIONS})
        self.lang = _ro(lang, object)
        self.lang_basis = _ro(lang_basis, object)
        self.named_poi = MappingProxyType({v: _ro(named_poi[v], object) for v in VERSIONS})
        self.named_org = _ro(named_org, np.int64)
        self.person_id = _ro(person_id, np.int64)
        self.meta = MappingProxyType(dict(meta or {}))

    @property
    def n(self) -> int:
        return int(self.person_id.size)

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            raise AttributeError(f"PersonaTable は読むだけ({name})")
        object.__setattr__(self, name, value)

    def named_ids(self, row: int, version: str = "long") -> tuple[tuple[int, ...], int]:
        """〔CP5-3〕その体の文に名の出る POI の番号と勤め先の組織の番号(−1=無し)=番号で名指しを見る口。"""
        if version not in VERSIONS:
            raise PersonaError(f"版は {VERSIONS} のどれか(いま {version!r})")
        p = self.named_poi[version][int(row)]
        return tuple(int(x) for x in (p if p is not None else ())), int(self.named_org[int(row)])

    def record(self) -> dict[str, Any]:
        """manifest に写す欄(数だけ=文は写さない)。"""
        has = {v: int(sum(1 for t in self.texts[v] if t)) for v in VERSIONS}
        src = {v: {str(k): int(c) for k, c in zip(*np.unique(self.source[v].astype(str), return_counts=True))}
               for v in VERSIONS}
        basis = {str(k): int(c) for k, c in zip(*np.unique(self.lang_basis.astype(str), return_counts=True))}
        return {"bodies": self.n, "with_text": has, "text_source": src, "lang_basis": basis, **dict(self.meta)}


def load_persona(world_dir: Any, person_id: Any) -> PersonaTable | None:
    """段 9 の文の表を読み、ランの体の並び(``person_id``=母集団の ``w21_person_id``・−1=W16 の残す行=文なし)に引き直す。

    表が無ければ ``None``(本体の v2=人物の欄は無い)。表に無い人の番号(≥0)は止める(黙って空にしない)。
    """
    if world_dir is None:
        return None
    paths = {v: Path(world_dir) / PERSONA_FILES[v] for v in VERSIONS}
    if not all(p.exists() for p in paths.values()):
        return None
    import pyarrow.parquet as pq  # 遅延 import(表の無いランに読み込ませない)

    pid = np.asarray(person_id, dtype=np.int64)
    n = int(pid.size)
    texts, source, named = {}, {}, {}
    lang = np.full(n, "", dtype=object)
    basis = np.full(n, "", dtype=object)
    org = np.full(n, -1, dtype=np.int64)
    for v in VERSIONS:  # 逐次: 版の数(2)
        names = pq.read_schema(paths[v]).names
        miss = [c for c in _READ_COLUMNS if c not in names]
        if miss:
            raise PersonaError(f"{PERSONA_FILES[v]} に要る列が無い: {miss}")
        t = pq.read_table(paths[v], columns=list(_READ_COLUMNS))
        tp = t.column("person_id").to_numpy(zero_copy_only=False).astype(np.int64)
        if np.unique(tp).size != tp.size:
            raise PersonaError(f"{PERSONA_FILES[v]} の person_id が重なる")
        order = np.argsort(tp, kind="stable")
        want = pid >= 0
        k = np.clip(np.searchsorted(tp[order], pid[want]), 0, max(tp.size - 1, 0))
        if want.any() and (tp.size == 0 or not np.array_equal(tp[order][k], pid[want])):
            raise PersonaError(f"{PERSONA_FILES[v]} に無い人の番号がある(世界資産と母集団の版が違う)")
        rows = order[k]
        tx = np.full(n, "", dtype=object)
        sc = np.full(n, "", dtype=object)
        nm = np.full(n, None, dtype=object)
        col_t = np.asarray(t.column("text").to_pylist(), dtype=object)
        col_s = np.asarray(t.column("text_source").to_pylist(), dtype=object)
        col_n = t.column("named_poi").combine_chunks()
        tx[want] = np.where(np.equal(col_t[rows], None), "", col_t[rows])
        sc[want] = col_s[rows]
        nm_w = np.empty(int(want.sum()), dtype=object)
        nm_w[:] = col_n.take(rows.astype(np.int64)).to_pylist()  # 〔検収 L3〕pyarrow の take=体ごとの Python の for は無い
        nm[want] = nm_w
        texts[v], source[v], named[v] = tx, sc, nm
        if v == "long":
            lang[want] = np.asarray(t.column("lang").to_pylist(), dtype=object)[rows]
            basis[want] = np.asarray(t.column("lang_basis").to_pylist(), dtype=object)[rows]
            org[want] = t.column("named_org").to_numpy(zero_copy_only=False).astype(np.int64)[rows]
    return PersonaTable(texts=texts, source=source, lang=lang, lang_basis=basis, named_poi=named, named_org=org,
                        person_id=pid, meta={"files": dict(PERSONA_FILES)})


def persona_blocks(table: PersonaTable | None, row: int, length: str) -> dict[str, str]:
    """``compose`` に渡す人物の欄(``{BLOCK_SHORT: 短い版}`` か ``{BLOCK_LONG: 長い版}``・文の無い体と表の無いランは空の辞書)。"""
    if length not in VERSIONS:
        raise PersonaError(f"length は {VERSIONS} のどれか(いま {length!r})")
    if table is None:
        return {}
    text = str(table.texts[length][int(row)] or "")
    return {BLOCK_OF_VERSION[length]: text} if text else {}


def override(table: PersonaTable, rows: Sequence[int] | Any, texts: Sequence[str] | Any, *, version: str, label: str,
             meta: Mapping[str, Any] | None = None) -> PersonaTable:
    """差し替えの口(4-1b の腕「LLM が書いた人物像」): 体の行 ``rows`` の ``version`` の文を ``texts`` に替えた新しい表を返す
    (元の表は書き換えない・元の文は ``original`` に最初の 1 回だけ写す・出どころは ``override:<label>``)。``meta``(書かせた
    LLM と版など)は呼び手が渡す。表に無い行・同じ行の 2 回・空の出どころ・数の食い違いは止める。"""
    if version not in VERSIONS:
        raise PersonaError(f"版は {VERSIONS} のどれか(いま {version!r})")
    if not label:
        raise PersonaError("差し替えの出どころ(label)が空")
    r = np.asarray(rows, dtype=np.int64).reshape(-1)
    new = np.asarray(texts, dtype=object).reshape(-1)
    if r.size != new.size:
        raise PersonaError(f"行の数 {r.size} と文の数 {new.size} が違う")
    if r.size and (r.min() < 0 or r.max() >= table.n):
        raise PersonaError("表に無い体の行がある")
    if np.unique(r).size != r.size:
        raise PersonaError("同じ体が 2 回ある")
    tx = {v: np.array(table.texts[v], dtype=object, copy=True) for v in VERSIONS}
    orig = {v: np.array(table.original[v], dtype=object, copy=True) for v in VERSIONS}
    src = {v: np.array(table.source[v], dtype=object, copy=True) for v in VERSIONS}
    first = np.equal(orig[version][r], None)
    orig[version][r[first]] = tx[version][r[first]]
    tx[version][r] = new
    src[version][r] = f"override:{label}"
    m = dict(table.meta)
    m.setdefault("overrides", [])
    m["overrides"] = [*m["overrides"], {"label": label, "version": version, "rows": int(r.size), **dict(meta or {})}]
    return PersonaTable(texts=tx, source=src, lang=table.lang, lang_basis=table.lang_basis, named_poi=table.named_poi,
                        named_org=table.named_org, person_id=table.person_id, original=orig, meta=m)
