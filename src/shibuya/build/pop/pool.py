"""build.pop.pool — v1 ペルソナプール(素材)の読み取りと列化。

位置づけ(決定台帳「母集団合成」③): プールは**名簿ではなく素材**。W16 は
「再重み付け(層化抽出)+ 方面 OD 差し替え + 年齢×性別 raking」で使い、足りない層は
**追加生成**(素材を種にして属性を引き直す)で埋める。

読むもの(``data/persona_pool_v2/``)
- ``meta.json``: 層別の生成数(件数照合=答申 Q6-a 段1「在庫棚卸し」のゲート)。
- ``L1..L5/part-*.jsonl``: 1 行 1 体の JSON(UTF-8)。**必要な欄だけ**列に落とす
  (1,000,000 行 × 約 800 B = 約 800 MB を辞書のまま抱えない)。

逐次ループ宣言(P4)
- ``read_layer``: **プール行数**ぶんのループ(JSONL の 1 行 1 体・約 100 万行で 6 秒級)。
  W16 は 1 回限りの構築段階(呼数 0・I1 の外)なので逐次で構わない。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np

__all__ = [
    "LAYERS",
    "SEX_CODES",
    "PoolLayer",
    "Pool",
    "layer_files",
    "read_layer",
    "read_pool",
]

#: 層名(L1 常住 / L2 通勤=従業 / L3 定期来街 / L4 確率的来街 / L5 職務)。
LAYERS: Final[tuple[str, ...]] = ("L1", "L2", "L3", "L4", "L5")

#: 性別コード(0=男・1=女)。プールの ``gender`` は「男」「女」の 1 文字。
SEX_CODES: Final[dict[str, int]] = {"男": 0, "女": 1}

#: 列に落とす文字列欄(``str`` のまま持ち、コード化は呼び出し側)。
_STR_FIELDS: Final[tuple[str, ...]] = (
    "presence",
    "workplace_scope",
    "commute_mode",
    "school_stage",
    "role",
    "subtype",
    "residence_line",
    "org_id",
    "industry_key",
    "visit_purpose",
    "household_type",
    "post",
    "occupation",
)


@dataclass(frozen=True)
class PoolLayer:
    """1 層ぶんの列(行順=ファイル順=``pool_index``)。

    Attributes:
        name: ``"L1"`` など。
        n: 行数。
        age: ``(n,)`` int16。
        sex: ``(n,)`` int8(0=男・1=女・不明は −1)。
        is_foreign: ``(n,)`` bool。
        visit_rate: ``(n,)`` float32(L4 以外は 0)。
        text: 文字列欄の辞書(欄名 → 長さ n の list[str]。欠測は ``""``)。
    """

    name: str
    n: int
    age: np.ndarray
    sex: np.ndarray
    is_foreign: np.ndarray
    visit_rate: np.ndarray
    text: dict[str, list[str]]

    def col(self, field: str) -> list[str]:
        return self.text[field]

    def age_sex_table(self, age_edges: np.ndarray) -> np.ndarray:
        """``(len(age_edges), 2)`` の年齢階級×性別 分割表(raking の種)。"""
        bins = np.searchsorted(age_edges[1:], self.age, side="right")
        tab = np.zeros((age_edges.size, 2), dtype=np.float64)
        ok = self.sex >= 0
        np.add.at(tab, (bins[ok], self.sex[ok].astype(np.int64)), 1.0)
        return tab


@dataclass(frozen=True)
class Pool:
    """全層。``meta`` は ``meta.json`` の中身。"""

    root: Path
    meta: dict[str, Any]
    layers: dict[str, PoolLayer]

    @property
    def total(self) -> int:
        return sum(lyr.n for lyr in self.layers.values())

    def counts(self) -> dict[str, int]:
        return {name: lyr.n for name, lyr in self.layers.items()}

    def meta_counts(self) -> dict[str, int]:
        return {k: int(v) for k, v in dict(self.meta.get("layer_counts", {})).items()}

    def inventory_matches_meta(self) -> bool:
        """件数照合(答申 Q6-a 段1 の合否ライン=``meta.json`` と一致)。"""
        return self.counts() == self.meta_counts()


def layer_files(root: Path, name: str) -> list[Path]:
    """層の part ファイル(名前順=決定論)。"""
    return sorted((root / name).glob("part-*.jsonl"))


def read_layer(root: Path, name: str) -> PoolLayer:
    """1 層を読んで列化する。逐次ループ宣言(P4): プール行数ぶん。"""
    ages: list[int] = []
    sexes: list[int] = []
    foreign: list[bool] = []
    rates: list[float] = []
    text: dict[str, list[str]] = {f: [] for f in _STR_FIELDS}
    for path in layer_files(root, name):
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                ages.append(int(d.get("age") or 0))
                sexes.append(SEX_CODES.get(str(d.get("gender") or ""), -1))
                foreign.append(bool(d.get("is_foreign") or False))
                vr = d.get("visit_rate")
                rates.append(float(vr) if isinstance(vr, (int, float)) else 0.0)
                for f in _STR_FIELDS:
                    v = d.get(f)
                    text[f].append("" if v is None else str(v))
    n = len(ages)
    return PoolLayer(
        name=name,
        n=n,
        age=np.asarray(ages, dtype=np.int16),
        sex=np.asarray(sexes, dtype=np.int8),
        is_foreign=np.asarray(foreign, dtype=bool),
        visit_rate=np.asarray(rates, dtype=np.float32),
        text=text,
    )


def read_pool(root: str | Path, layers: tuple[str, ...] = LAYERS) -> Pool:
    """``data/persona_pool_v2`` を読む。"""
    root = Path(root)
    meta_path = root / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return Pool(root=root, meta=meta, layers={name: read_layer(root, name) for name in layers})
