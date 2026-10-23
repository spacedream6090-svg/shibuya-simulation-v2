"""economy.wages — 職業 × 性 × 年齢 × 雇用形態の賃金(賃金構造基本統計調査 令和 7 年=R-107・EC2 の最初の資産)。

正: ユーザー決定 2026-10-17(回答 10-13b §7 の 3=2-1 の賃金は職業ごとの実データから・W17 の勤務時間とは別に入れる・
「賃金の額が現実の 1/4」の宣言を解く)・§0-6(小さな版上げ)・決定 10-12 §4-11(EC2=賃金構造基本統計調査が最初の資産)・
答申 R-107 §1-1・記録 pop41b §4(4-1 段 5 の ``build.pop.attr_fns.wage_monthly`` ほか=属性から作る純粋な関数)。

**二重に作らない**: 賃金の表の読み解き・属性と分位から額を出す式・写像・床の式は ``core.wage_formula``(4-1 段 5 から
移した=build と実行時の両方が呼ぶ)にあり、本モジュールはその名を同じ物として見せる(``from shibuya.core.wage_formula import``)。
本モジュールに置くのは、写しの読み口(:func:`load_wage_tables`)・最低賃金の床の値(:func:`min_wage_floor`=規則の表=
``economy.anchors``)・注記の型(:class:`WageTablesAbsentWarning`)だけ。

実行時の読み口(:func:`load_wage_tables`): 構築側の写し ``data/research_cache/pop41b/derived/wage_t{9,6,18,2}.json``
(4-1 段 4〜7 の台帳 ``build.pop.w21_sources.SOURCES_B`` の 4 行=#46 構築側)を md5 を照らして読む(元の xlsx は開かない=写しに
書いてある元の md5 を照らす)。写しが無い写し(data の無い CI)は ``None``(呼び手が注記して旧の道に戻す)。

W16 の体の写像(:data:`OCCUPATION_OF_PERSONA_WORD`・:data:`FORM_OF_PERSONA_EMPLOYMENT`・**未リサーチ(expedient)**・つなぎの台帳
``DOC-wage_occ-*``・外す段 4-3=第 4 期 段 10 の W21 への差し替え): ペルソナの ``occupation_major`` の語(職業大分類の名=賃金構造の
職種の名と同じ語)→ 職種の番号・``employment`` の語 → 雇用形態(正規=正社員・正職員/非正規=正社員・正職員以外/役員・自営業主・
家族従業者=賃金構造の対象外なので正社員・正職員の表で)。職業の語が写せない体(非就業・通学・ペルソナの無い体)は、雇用形態と
年齢(と性)だけの平均(職種ごとの値を第18表の労働者数で重みづけ)。W16 の語に短時間の印は無い=短時間の表(第 2 表)は
W21 の ``part_time`` の体から(段 10 の差し替えで自動)。

乱数: 体ごとの分位 u は ``core.rng.philox_array``(用途名 :data:`WAGE_DOMAIN`=母集団の側・0 語目を空け 1 語目に体の鍵=
``k19_counter_array``・1 語だけ引く)。``build.pop.attr_fns.AttrKey.uniform`` と同じ引き方(試験が突き合わせる)。

逐次ループ宣言(P4): 表の行の数ぶん(読み解き)・写せない体の平均は職種 11 × 性 2 の数ぶん。体の数に比例するループは無い。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from shibuya.core.wage_formula import (  # noqa: F401 — 同じ物を見せる(二重に作らない)
    WAGE_OCCUPATIONS,
    WAGE_AGE_EDGES,
    WAGE_CLASS_FLOOR_YEN,
    WAGE_TOP_FACTOR,
    SEXES,
    FORM_REGULAR,
    FORM_NON_REGULAR,
    FORM_PART_TIME,
    WAGE_DOMAIN,
    WAGE_TABLE_FIELDS,
    WageTables,
    parse_wage_tables,
    wage_quantile,
    wage_values,
    wage_uniform,
    OCCUPATION_OF_PERSONA_WORD,
    FORM_OF_PERSONA_EMPLOYMENT,
    BASIS_OCCUPATION,
    BASIS_AVERAGE,
    BASIS_GIVEN,
    BASIS_NAMES,
    occupation_wages,
    median_check,
    month_hours,
    apply_floor,
    _codes,
)

__all__ = [
    "WAGE_OCCUPATIONS",
    "WAGE_AGE_EDGES",
    "WAGE_CLASS_FLOOR_YEN",
    "WAGE_TOP_FACTOR",
    "SEXES",
    "FORM_REGULAR",
    "FORM_NON_REGULAR",
    "FORM_PART_TIME",
    "WAGE_DOMAIN",
    "WAGE_TABLE_FIELDS",
    "WageTables",
    "parse_wage_tables",
    "wage_quantile",
    "wage_values",
    "wage_uniform",
    "OCCUPATION_OF_PERSONA_WORD",
    "FORM_OF_PERSONA_EMPLOYMENT",
    "BASIS_OCCUPATION",
    "BASIS_AVERAGE",
    "BASIS_GIVEN",
    "BASIS_NAMES",
    "occupation_wages",
    "median_check",
    "month_hours",
    "apply_floor",
    "DERIVED_RELDIR", "DERIVED_FILES", "load_wage_tables", "WageTablesAbsentWarning", "min_wage_floor",
]

#: 構築側の写しの置き場(リポの根から)。
DERIVED_RELDIR: Final[str] = "data/research_cache/pop41b/derived"
#: 写し 4 本(id → (ファイル名, 写しの md5, 元の xlsx の md5))。``build.pop.w21_sources.SOURCES_B`` の同じ id の行の写し
#: (build は実行時に import できない=試験が突き合わせる)。
DERIVED_FILES: Final[Mapping[str, tuple[str, str, str]]] = MappingProxyType({
    "wage_t9": ("wage_t9.json", "3b9a446728619f5b0c600f3fe1789fb5", "329bfe762939fd7d4b86123872a79096"),
    "wage_t6": ("wage_t6.json", "6c6546a84d0d2c702bfcb0575bee6167", "c12cbe20a3315dcdf45496be650939d5"),
    "wage_t18": ("wage_t18.json", "b1e80e3f9b1fbc5dd9436452d4fe6f50", "ba8d70a2a82410ea4c03b49f301dc2ce"),
    "wage_t2": ("wage_t2.json", "ad8a1f6a629dd816f023206b79bd4b4c", "9367a705b1f3d95b9331af5fe681c0e3"),
})

def min_wage_floor(asof: Any, rules: Any = None) -> tuple[int | None, str]:
    """〔検収 M1〕``asof`` の日に効いている最低賃金の床[円/時]と出どころ(規則の表の ``minimum_wage.tokyo``)。

    読み手は ``economy.anchors.min_wage_floor``(規則の表を読むのは anchors だけ)。**直書きの値に戻さない**: 表に版の無い日・
    表の無い写しは ``(None, "none")``=床なし(宣言=記録 wage_occ §13)。
    """
    from shibuya.economy import anchors as _AN

    return _AN.min_wage_floor(asof, rules)


class WageTablesAbsentWarning(UserWarning):
    """賃金の表の写しが無い写し(data の無い CI)の注記。``engine.economy_stage2.DataAbsentWarning`` と同じ UserWarning の系
    (economy は層の契約で engine の段階 2 の組み立てを import できない=別の型に置いた)。"""



def load_wage_tables(root: str | Path | None = None) -> WageTables | None:
    """構築側の写し 4 本(:data:`DERIVED_FILES`)を md5 を照らして読む。無い写しは ``None``(md5 が違えば止める)。

    Args:
        root: 写しの置き場(``None``=リポの根からの :data:`DERIVED_RELDIR`)。
    """
    if root is None:
        from shibuya.engine.calendar import resolve_repo_path

        base = resolve_repo_path(DERIVED_RELDIR)
    else:
        base = Path(root)
    rows: dict[str, tuple[list[str], list[list[Any]]]] = {}
    md5: dict[str, str] = {}
    for sid, (name, want, src_md5) in DERIVED_FILES.items():  # 逐次: 写しの数(4)
        p = base / name
        if not p.is_file():
            return None
        raw = p.read_bytes()
        got = hashlib.md5(raw).hexdigest()  # noqa: S324 — 同定の印(暗号ではない)
        if got != want:
            raise ValueError(f"賃金の表の写しの md5 が台帳と違う: {name}({got[:8]} != {want[:8]})")
        doc = json.loads(raw.decode("utf-8"))
        if doc.get("source_md5") != src_md5:
            raise ValueError(f"賃金の表の写しの元の md5 が台帳と違う: {name}")
        rows[sid] = (list(doc["items"]), list(doc["rows"]))
        md5[name] = got
    parsed = parse_wage_tables(rows["wage_t9"][1], rows["wage_t6"][1], rows["wage_t18"][0], rows["wage_t18"][1],
                               rows["wage_t2"][0], rows["wage_t2"][1])
    return WageTables(**parsed, md5=md5)
