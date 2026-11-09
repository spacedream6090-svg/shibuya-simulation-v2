# -*- coding: utf-8 -*-
"""bytecheck.fields — 25 欄の外に足した比べるもの・比べない欄の名前つきの一覧・正準の JSON のハッシュ・差の書き方。

第346 の検収(H1)の指摘: 25 欄(:data:`configs.COMPARE_KEYS`)は、テープの型とスキーマの見出し(``blocks_sha``・
``calls_columns_sha`` は ``to_pylist()`` のハッシュで Arrow の型と metadata が消える)・manifest の 124 欄のうち 115 欄・
``run_meta.json``・途中の checkpoint を比べていなかった。ここで足すもの(:data:`NEW_KEYS`):

- テープの置き場の全ファイルの名(``tape_files``)と、``run_meta.json`` を除く全ファイルの sha256(``tape_sha256``)。
  ``run_meta.json`` は git の commit を持つので、下の欄ごとの比べに回す。
- テープの 2 表の Arrow のスキーマ(列の名・型・null の可否・列とスキーマの metadata=``calls_schema``・``blocks_schema``)。
- manifest(``RunResult.run_manifest_fields()``): 比べない欄(:data:`MANIFEST_SKIP` と :data:`SKIP_SUFFIXES`・ただし
  :data:`SUFFIX_EXEMPT` の下は除かない)を除いた
  正準の JSON の sha256(``manifest_sha``)・一番上の欄ごとのハッシュ(``manifest_fields_sha``)・除いた欄の道筋の一覧
  (``manifest_skipped``=値は比べないが、欄が増えた・消えたは比べる)。
- ``run_meta.json``: 同じ形(:data:`RUN_META_SKIP`・``run_meta_sha``・``run_meta_fields_sha``・``run_meta_skipped``)。
- 全 checkpoint の値(``checkpoints``)と数(``n_checkpoints``)。

比べるかどうかの決め方: 両側で違って当然の欄(git の commit と差分・それから作る env_id・壁時計の秒)だけを名前と理由つきで
外す。外す欄が無いのに値が違う、一覧に無い欄が片側だけにある、は「動いた」になる。

正準の JSON: ``json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str, allow_nan=True)``。
辞書の鍵の並びは見ない。``0`` と ``0.0``・``True`` と ``1`` は違う値として扱う。``NaN`` は両側にあれば同じ(検収 L6)。
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path
from typing import Any, Final, Iterable, Mapping

#: 25 欄の外に足した比べる欄(side の各ランの行に出す・compare が比べる)。古い記録に無い欄は「比べていない」と注を付ける。
NEW_KEYS: Final[tuple[str, ...]] = (
    "tape_files", "tape_sha256", "calls_schema", "blocks_schema",
    "manifest_sha", "manifest_fields_sha", "manifest_skipped",
    "run_meta_sha", "run_meta_fields_sha", "run_meta_skipped",
    "checkpoints", "n_checkpoints",
)

#: テープの置き場で、ファイルのバイトでなく欄ごとに比べるもの(git の commit を持つ)。
TAPE_FIELDWISE: Final[tuple[str, ...]] = ("run_meta.json",)

#: manifest で比べない欄(``a.b`` は入れ子の辞書の道筋 → 理由)。値は比べないが、欄があったことは ``manifest_skipped`` に残す。
MANIFEST_SKIP: Final[dict[str, str]] = {
    "env_id": "環境の ID(environment の code=git の commit・dirty・差分の sha を含めて作る=写しの木は git の外で空の値・"
              "比べる側は作業木の HEAD)",
    "environment.code": "git の commit・dirty・差分の sha256(両側で違って当然)",
    "environment.env_id": "env_id と同じ値",
    "resume.read_seconds": "壁時計の秒(状態を読んだ時間)",
    "resume.restore_seconds": "壁時計の秒(状態を戻した時間)",
}

#: run_meta.json で比べない欄(同じ形)。
RUN_META_SKIP: Final[dict[str, str]] = {
    "env_id": MANIFEST_SKIP["env_id"],
    "environment.code": MANIFEST_SKIP["environment.code"],
    "environment.env_id": MANIFEST_SKIP["environment.env_id"],
}

#: どの深さでも、鍵の名がこれで終わる欄は比べない(エンジンが壁時計と宣言した欄=``relations.wall_seconds_nondeterministic``・
#: ``relations.init.init_seconds_nondeterministic``・``step_scope.detect_seconds_nondeterministic``)。
SKIP_SUFFIXES: Final[tuple[str, ...]] = ("_nondeterministic",)

#: :data:`SKIP_SUFFIXES` を当てない欄(道筋の頭 → 理由)。比べる。
SUFFIX_EXEMPT: Final[dict[str, str]] = {
    "manifest_sections": "manifest の欄を節に分ける表(鍵は欄の道筋・値は節の名=壁時計でない。"
                         "``manifest_sections.paths.relations.wall_seconds_nondeterministic`` などの行がある)",
}

#: 表に値を出す短い一番上の欄の長さの上限(動いた欄の前後の値を読めるように。比べるのはハッシュ)。
SCALAR_MAX: Final[int] = 200


def canon(obj: Any) -> bytes:
    """正準の JSON(鍵を並べる・区切りの空白なし・UTF-8)。"""
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str,
                      allow_nan=True).encode("utf-8")


def sha16(obj: Any) -> str:
    """正準の JSON の sha256 の頭 16 桁。"""
    return hashlib.sha256(canon(obj)).hexdigest()[:16]


def same_value(va: Any, vb: Any) -> bool:
    """2 つの値が同じか(正準の JSON が同じ=辞書の並びは見ない・型の違いは違い・NaN は同じ)。"""
    return canon(va) == canon(vb)


def strip_skipped(doc: Any, skip: Iterable[str], suffixes: Iterable[str] = SKIP_SUFFIXES,
                  exempt: Iterable[str] = tuple(SUFFIX_EXEMPT)) -> tuple[Any, list[str]]:
    """``doc`` から比べない欄を除いた写しと、除いた欄の道筋(``a.b``・list の中は ``a[0].b``)。

    ``skip`` は道筋がそのまま一致する欄。``suffixes`` は鍵の名の終わり(どの深さでも・``exempt`` の頭の下は当てない)。
    """
    skip_set = set(skip)
    sfx = tuple(suffixes)
    heads = tuple(exempt)
    gone: list[str] = []

    def walk(obj: Any, path: str, sfx_on: bool) -> Any:
        if isinstance(obj, Mapping):
            out: dict[Any, Any] = {}
            for k, v in obj.items():
                p = f"{path}.{k}" if path else str(k)
                if p in skip_set or (sfx_on and sfx and str(k).endswith(sfx)):
                    gone.append(p)
                    continue
                out[k] = walk(v, p, sfx_on and p not in heads)
            return out
        if isinstance(obj, (list, tuple)):
            return [walk(v, f"{path}[{i}]", sfx_on) for i, v in enumerate(obj)]
        return obj

    return walk(doc, "", True), sorted(gone)


def _short_scalar(v: Any) -> bool:
    return v is None or isinstance(v, (bool, int, float)) or (isinstance(v, str) and len(v) <= SCALAR_MAX)


def field_digest(doc: Mapping[str, Any] | None, skip: Iterable[str]) -> dict[str, Any]:
    """manifest・run_meta の比べる形: 全体の sha256・一番上の欄ごとのハッシュ・短い値・除いた欄。"""
    stripped, gone = strip_skipped(dict(doc or {}), skip)
    return {"sha": hashlib.sha256(canon(stripped)).hexdigest(),
            "fields": {str(k): sha16(v) for k, v in stripped.items()},
            "scalars": {str(k): v for k, v in stripped.items() if _short_scalar(v)},
            "skipped": gone}


# ------------------------------------------------------------------ テープ
def tape_files(tape: str | Path) -> list[str]:
    """テープの置き場の全ファイル(置き場からの posix の道筋・並べる)。"""
    t = Path(tape)
    return sorted(p.relative_to(t).as_posix() for p in t.rglob("*") if p.is_file())


def file_sha256(path: str | Path) -> str:
    """ファイルのバイトの sha256(全桁)。"""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tape_sha256(tape: str | Path, fieldwise: Iterable[str] = TAPE_FIELDWISE) -> dict[str, str]:
    """テープの置き場の全ファイルの sha256(``fieldwise`` の名のファイルは欄ごとに比べるので除く)。"""
    t = Path(tape)
    skip = set(fieldwise)
    return {rel: file_sha256(t / rel) for rel in tape_files(t) if rel not in skip}


def arrow_schema(schema: Any) -> dict[str, Any]:
    """Arrow のスキーマ(列の名・型・null の可否・列の metadata・スキーマの metadata。``ARROW:schema`` の塊は除く)。"""

    def meta(m: Any) -> dict[str, str]:
        return {k.decode("utf-8", "replace"): v.decode("utf-8", "replace")
                for k, v in (m or {}).items() if k != b"ARROW:schema"}

    cols = []
    for f in schema:
        s = f"{f.name}:{f.type}:{'null' if f.nullable else 'not null'}"
        if f.metadata:
            s += ":" + json.dumps(meta(f.metadata), ensure_ascii=False, sort_keys=True)
        cols.append(s)
    return {"fields": cols, "metadata": meta(schema.metadata)}


# ------------------------------------------------------------------ checkpoint
def checkpoint_rows(points: Iterable[Any]) -> list[dict[str, Any]]:
    """全 checkpoint の値(dataclass なら全欄・それ以外は属性)。"""
    out: list[dict[str, Any]] = []
    for c in points:
        d = dataclasses.asdict(c) if dataclasses.is_dataclass(c) else dict(vars(c))
        out.append(json.loads(canon(d)))
    return out


# ------------------------------------------------------------------ 差の書き方
_ABSENT: Final[str] = "(無い)"


def diff(va: Any, vb: Any) -> dict[str, Any]:
    """動いた欄の差(辞書は違う鍵だけ・list は違う位置だけ・それ以外は前後の値)。"""
    if isinstance(va, Mapping) and isinstance(vb, Mapping):
        keys = list(va) + [k for k in vb if k not in va]
        return {"keys": {str(k): {"a": va.get(k, _ABSENT), "b": vb.get(k, _ABSENT)} for k in keys
                         if k not in va or k not in vb or not same_value(va[k], vb[k])}}
    if isinstance(va, list) and isinstance(vb, list):
        n = max(len(va), len(vb))
        items = {str(i): {"a": va[i] if i < len(va) else _ABSENT, "b": vb[i] if i < len(vb) else _ABSENT}
                 for i in range(n) if i >= len(va) or i >= len(vb) or not same_value(va[i], vb[i])}
        return {"len": [len(va), len(vb)], "items": items}
    return {"a": va, "b": vb}


def named_moves(ra: Mapping[str, Any], rb: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    """``<prefix>_fields_sha`` の動いた欄の名と前後の値(短い値ならその値・長ければハッシュ)。"""
    fa, fb = ra.get(f"{prefix}_fields_sha") or {}, rb.get(f"{prefix}_fields_sha") or {}
    sa, sb = ra.get(f"{prefix}_scalars") or {}, rb.get(f"{prefix}_scalars") or {}
    out: dict[str, Any] = {}
    for k in list(fa) + [k for k in fb if k not in fa]:
        if fa.get(k) == fb.get(k):
            continue
        out[k] = {"a": sa.get(k, fa.get(k, _ABSENT)), "b": sb.get(k, fb.get(k, _ABSENT))}
    return out
