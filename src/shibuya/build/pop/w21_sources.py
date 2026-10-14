"""W21(第 4 期 4-1 段 1〜3)の材料の台帳と読み口の守り(read_guard)。

正: 答申 R-116 §1(材料の表 59 行=**区分「検証側=使わない」の 11 行は開かない**)・§3-2(``pop3_sources.py`` の案)・
パターン台帳 §10(検証専用の一覧)・回答 10-13b §1 1-3(PT の分け方)・PENDING 仮-23。

やること
1. **材料の台帳** :data:`SOURCES`: 表ごとに statInfId・ファイル(data 根からの相対)・md5(全桁)・区分(構築)・読む列。
   xlsx の表は ``data/research_cache/pop41/derived/`` の写し(``docs/bench/analysis/wallbounce-1012/pop41/tools/
   xlsx_to_derived.py``=渋谷区の行だけ)を読み、写しの md5 と元の xlsx の md5 の両方を照らす。
2. **検証側の一覧** :data:`VERIFY_SIDE`: R-116 §1 の 11 行(#11・#16・#17・#42・#45・#47・#49・#50・#57・#58・#59)を
   行ごとに「道筋に現れる語」で持つ。封印の層の名は W19 の ``HOLDOUT_TOKENS`` から取る(本ファイルに名を書くと
   W19 の静的ゲートが「構築のコードが封印を開いた」と読むため)。
3. **読み口** :class:`W21Guard`: 読む前に (a) 検証側の語があれば :class:`VerificationSideError`(開く前に止める)
   (b) 許可の一覧(台帳の構築側の道筋+世界資産の入力+出力先)に無ければ :class:`NotAllowedError`。
   :meth:`W21Guard.active` の間は Python の ``open`` の監査フックでも同じ検査をする(読み口を通らない ``open`` も止める)。
   pyarrow の読み(C++)は監査に出ないので、parquet は :meth:`W21Guard.read_parquet` の検査だけで縛る(宣言)。
4. **PT 2018 c-2**(10-13b §1 1-3=構築側は「舞台の外のゾーンの発生量」と「自宅以外からの私事」だけ): 列を絞って返す
   :func:`read_pt_c2_build_side` を置く。集中量の列(12〜20 列目=R-57)は読んだ行から即座に捨て、舞台の 4 ゾーン
   (0240〜0243)は発生量のうち「私事」の列だけを返す。**W21 の組み立ては c-2 を開かない**(段 1 の枠は R-116 §4 の
   値を引く)。本関数は形を合成のファイルで試験するだけ(実ファイルの列の並びは R-57 の記述どおりと仮定=未確認)。

逐次ループ宣言(P4): 表の行の数ぶん(CSV の読み・渋谷区の 80 行×男女 3)。体の数に比例するループは無い。
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Iterator, Mapping, Sequence

import numpy as np

from ..audit.w19_freeze import HOLDOUT_TOKENS

__all__ = [
    "Source",
    "VerifyRow",
    "SOURCES",
    "VERIFY_SIDE",
    "WARD_CODE",
    "VerificationSideError",
    "NotAllowedError",
    "MissingSourceError",
    "W21Guard",
    "SmallArea",
    "Derived",
    "source",
    "verify_tokens",
    "read_small_area",
    "read_derived",
    "read_derived_merged",
    "read_estat_json",
    "read_pt_c2_build_side",
    "pt_c2_layout",
    "PT_STAGE_ZONES",
    "PT_C2_ALLOWED",
    "PT_C2_AUDIT_EVENT",
]

WARD_CODE: Final[str] = "13113"
WARD_NAME: Final[str] = "13113_渋谷区"


# ------------------------------------------------------------------------------------------ 台帳
@dataclass(frozen=True)
class Source:
    """材料の表 1 本(構築側)。``derived`` は xlsx の渋谷区の行の写し(JSON)。"""

    sid: str
    title: str
    stat_inf_id: str
    path: tuple[str, ...]
    md5: str
    year: int
    columns: str = "*"
    derived: tuple[str, ...] | None = None
    derived_md5: str | None = None
    side: str = "build"
    r116_row: str = ""

    @property
    def rel(self) -> str:
        return "/".join(self.path)

    @property
    def derived_rel(self) -> str | None:
        return "/".join(self.derived) if self.derived else None


_R116 = ("research_cache", "r116")
_POP41 = ("research_cache", "pop41")
_DER = ("research_cache", "pop41", "derived")


def _sa(sid: str, title: str, stat: str, base: tuple[str, ...], name: str, md5: str, row: str) -> Source:
    return Source(sid, title, stat, (*base, name), md5, 2020, r116_row=row)


def _xl(sid: str, title: str, stat: str, base: tuple[str, ...], name: str, md5: str, der: str, der_md5: str,
        year: int, row: str) -> Source:
    return Source(sid, title, stat, (*base, name), md5, year, derived=(*_DER, f"{der}.json"), derived_md5=der_md5,
                  r116_row=row)


#: 材料の台帳(構築側だけ・W21 が読む表だけ)。md5 は取得物の全桁(R-116 MANIFEST・本段の MANIFEST と同じ値)。
#: 取得したが読まない表(2025 第15-1表=子の数と年齢・従業地 第15-1表=職業 × 年齢・2025 の原数値の第2-1・10・13-1表)は
#: 載せない(記録 pop41/README.md の材料の表)。
SOURCES: Final[tuple[Source, ...]] = (
    # --- 国勢調査 2020 小地域(町丁目)
    Source("sa_t01", "国勢調査2020 小地域 第1表 男女別人口総数及び世帯総数", "000032163273",
           ("realworld", "estat", "国勢調査2020_小地域_男女別人口総数世帯総数_東京都_渋谷区抽出.json"),
           "538f0b6914f51e70e1ec6556af6251ae", 2020, r116_row="#1"),
    _sa("sa_t02", "同 第2表 男女別人口・外国人人口・世帯数", "000032163274", ("research_cache", "r110"),
        "census2020_sa_h02_13_foreign.csv", "942ae4719b10b4fdea09c0236215c9d4", "#1"),
    Source("sa_t03", "同 第3表 年齢5歳階級・男女別人口", "000032163275",
           ("realworld", "estat", "国勢調査2020_小地域_年齢5歳階級男女別人口_東京都_渋谷区_全階級.json"),
           "f989732c5d7d57757809271b8d43f862", 2020, r116_row="#18"),
    _sa("sa_t04", "同 第4表 男女・配偶関係別人口(15歳以上)", "000032163276", _R116,
        "census2020_sa_h04_13_marital.csv", "7cd2203f67cd8fe6d03b0d7d9cf3d17b", "#19"),
    _sa("sa_t05_2", "同 第5-2表 世帯人員の人数別一般世帯数", "000032163278", _R116,
        "census2020_sa_h05_02_13_hhsize.csv", "61549f3282ae2b006ecc650b2589d4c1", "#20"),
    _sa("sa_t06_1", "同 第6-1表 世帯の家族類型別一般世帯数", "000032163279", _R116,
        "census2020_sa_h06_01_13_family_type.csv", "5df5ed287ecf22c036bd2276712784bf", "#21"),
    _sa("sa_t06_2", "同 第6-2表 世帯の家族類型別一般世帯人員", "000032163280", _POP41,
        "census2020_sa_h06_02_13_family_type_hhsize.csv", "ba23880204a61e699906e1ec9c57bed2", "#21"),
    _sa("sa_t07_1", "同 第7-1表 住宅の所有の関係別一般世帯数", "000032163282", _R116,
        "census2020_sa_h07_01_13_tenure.csv", "eef0a0513275cf625ef7727532321726", "#22"),
    _sa("sa_t08_1", "同 第8-1表 住宅の建て方別一般世帯数", "000032163285", _R116,
        "census2020_sa_h08_01_13_building_type.csv", "810afe1e3e86c3de08e0988e86723097", "#22"),
    _sa("sa_t09", "同 第9表 男女・労働力状態別人口(15歳以上)", "000032210226", _R116,
        "census2020_sa_h09_13_labour_force.csv", "5a1eeb61d5633c37525e9d00cfdcd781", "#32"),
    _sa("sa_t10", "同 第10表 男女・従業上の地位別就業者数", "000032210273", _R116,
        "census2020_sa_h10_13_emp_status.csv", "bae1ce45c0e168504eea4dc12c369577", "#32"),
    _sa("sa_t11", "同 第11表 男女・産業(大分類)別就業者数", "000032210320", _R116,
        "census2020_sa_h11_13_industry.csv", "5466df012c9c3420909989b036074cad", "#32"),
    _sa("sa_t12", "同 第12表 男女・職業(大分類)別就業者数", "000032210367", _R116,
        "census2020_sa_h12_13_occupation.csv", "126009db3ec125f80e961f2b912423d9", "#32"),
    _sa("sa_t14", "同 第14表 男女・在学学校・未就学の種類別人口", "000032210461", _R116,
        "census2020_sa_h14_13_school.csv", "e9b545ffa1276836fb76ec370098e357", "#35"),
    _sa("sa_t16_2", "同 第16-2表 男女・従業地・通学地別就業者数", "000032226889", _R116,
        "census2020_sa_h16_02_13_workplace.csv", "6e5fdedadc5d79be1646c47ed17d6ad1", "#35"),
    _sa("sa_t16_3", "同 第16-3表 男女・従業地・通学地別通学者数(15歳以上)", "000032226936", _POP41,
        "census2020_sa_h16_03_13_school_place.csv", "0b12709ff79fabdeded7289835f7003d", "#35"),
    _sa("sa_t18", "同 第18表 男女・居住期間別人口", "000032181182", _R116,
        "census2020_sa_h18_13_residence_period.csv", "0c2781cf6ec0dc226f21b38c7f915757", "#36"),
    # --- 小地域の境界(W16 と同じ)
    Source("sa_shp", "国勢調査2020 小地域の境界(渋谷区・形)", "-", ("realworld", "estat", "r2ka13113", "r2ka13113.shp"),
           "a6b3cedefaea6ea54feda2c3d01b1fd0", 2020, r116_row="#56"),
    Source("sa_dbf", "国勢調査2020 小地域の境界(渋谷区・属性)", "-", ("realworld", "estat", "r2ka13113", "r2ka13113.dbf"),
           "e060dd087e98bf7ab1331bba00144c86", 2020, r116_row="#56"),
    # --- 国勢調査 2025 人口等基本集計(区)
    _xl("c25w_b02", "国勢調査2025 人口等基本集計 第2-1表 男女・年齢各歳・国籍総数か日本人別人口【不詳補完値】", "000040506653", _R116,
        "census2025_imputed_b02_01_age_single_sex_wards.xlsx", "4f20c1ea22b7a429944c89db391c5716", "c25w_b02_01",
        "c582d6e817b12da532e4a48134ca08cd", 2025, "#5"),
    _xl("c25w_b10", "同 第10表【不詳補完値】", "000040506690", _POP41,
        "census2025_imputed_b10_family_type_hhsize_muni.xlsx", "67443a1adf20e7d5a247c9eaf7d3e941", "c25w_b10",
        "81a4e6747e25b274f4712817b50f4480", 2025, "#24"),
    _xl("c25_b12", "同 第12-1表 世帯主の男女・年齢・配偶関係・家族類型別一般世帯数", "000040506465", _POP41,
        "census2025_b12_01_head_sex_age_marital_family_wards.xlsx", "464503e136a084b039ebb8d140a29589",
        "c25_b12_01", "61ed346b690f13a0824490e292d670be", 2025, "#25"),
    _xl("c25w_b13", "同 第13-1表【不詳補完値】", "000040506697", _POP41,
        "census2025_imputed_b13_01_01_sex_age_relation_marital_family_wards.xlsx",
        "ef5aa9d8f4265478876288de0693797f", "c25w_b13_01", "1fe5ef0538885ec481fc72edae765445", 2025, "#23"),
    _xl("c25w_b13_m", "同 第13-1表【不詳補完値】:男", "000040506698", _POP41, "census2025_imputed_b13_01_02_male.xlsx",
        "a2fe432dd31f388e6f98adbfff3f32fc", "c25w_b13_02", "31b899097b0860bd8873c53b49d965c9", 2025, "#23"),
    _xl("c25w_b13_f", "同 第13-1表【不詳補完値】:女", "000040506699", _POP41, "census2025_imputed_b13_01_03_female.xlsx",
        "44391dda130e1d69a64a68006d77bb55", "c25w_b13_03", "b4af83f8f7c13c2a311c14937693ceaa", 2025, "#23"),
    _xl("c25_b19", "同 第19-1表 夫の年齢(各歳)・妻の年齢(各歳)別夫婦数", "000040506509", _POP41,
        "census2025_b19_01_husband_wife_age_wards.xlsx", "8cb461b2e4217e7538a798df4f35bebe", "c25_b19_01",
        "adb7a77c08de44f8f49d58e97817e240", 2025, "#26"),
    # --- 国勢調査 2020 の遡及の不詳補完値(区)
    _xl("c20w_b02", "国勢調査2020 第2-1表【不詳補完値・遡及】", "000040317620", _POP41,
        "census2020r_imputed_b02_01_age_single_sex_wards.xlsx", "1d74cef79bf3f542b7dd97ffe3c2cf6b", "c20w_b02_01",
        "12b12d7f41610d28456ff57d053e9b07", 2020, "#27"),
    _xl("c20w_b10", "同 第10表【不詳補完値・遡及】", "000040317881", _POP41,
        "census2020r_imputed_b10_family_type_hhsize_muni.xlsx", "0ded399b55f70aff410f28b6c6782d72", "c20w_b10",
        "d27092333748603d8cd5847583d80e76", 2020, "#27"),
    _xl("c20w_b13_m", "同 第13-1表【不詳補完値・遡及】:男", "000040317889", _POP41,
        "census2020r_imputed_b13_01_02_male.xlsx", "632aa39f85c02b31c45619b4b2732d35", "c20w_b13_02",
        "c51b0cd2d2f9fc76c44f0c07bc315c04", 2020, "#27"),
    _xl("c20w_b13_f", "同 第13-1表【不詳補完値・遡及】:女", "000040317890", _POP41,
        "census2020r_imputed_b13_01_03_female.xlsx", "9fb26e0a86387e74c167bcefe265b90b", "c20w_b13_03",
        "fff66f1172abcb0f42c57fc65cf3dbea", 2020, "#27"),
    # --- 国勢調査 2020 就業状態等基本集計(区)
    _xl("c20_c03", "国勢調査2020 就業状態等 第3-1表 男女・年齢・配偶関係・労働力状態・従業上の地位", "000032201197",
        _POP41, "census2020_c03_01_age_marital_labour_status_wards.xlsx", "5ff64a2668f92615b9e5e9248e0ded15",
        "c20_c03_01", "307aa28c6ae1545520dc53857fd18a34", 2020, "#33"),
    _xl("c20_c05", "同 第5-1表 男女・年齢・従業上の地位・産業", "000032201200", _POP41,
        "census2020_c05_01_age_status_industry_wards.xlsx", "4708e7bed8bf8399097ee1a4d6b54d2b", "c20_c05_01",
        "8a1022f204580ebe50316452c9de24a1", 2020, "#33"),
    _xl("c20_c10", "同 第10-1表 男女・年齢・産業・職業", "000032201208", _POP41,
        "census2020_c10_01_age_industry_occupation_wards.xlsx", "0d9309f15c3cc8fbbf83c7c89d180564", "c20_c10_01",
        "6eee1289e1fd67d52a92444ec5549009", 2020, "#33"),
    # --- 国勢調査 2020 従業地・通学地集計(区=従業地/常住地)
    _xl("c20_e08", "国勢調査2020 従業地 第8表 男女・従業上の地位・産業・常住地又は従業地", "000032214499", _POP41,
        "census2020_e08_01_status_industry_workplace_muni.xlsx", "b8a35e7eb2c36bc98ae2883d25047f6d", "c20_e08_01",
        "ecd5bb5aca564896dfffac0e6ced509c", 2020, "#34"),
    _xl("c20_e11", "同 第11-1表 男女・年齢・産業(従業地)", "000032214589", _R116,
        "census2020_e11_01_workplace_sex_age_industry_muni.xlsx", "592730c2d99d1dea11e2a03eb7fd6c36", "c20_e11_01",
        "c0821611e86d5bf2068d251dc762d093", 2020, "#4"),
    _xl("c20_e16", "同 第16-1表 男女・産業・職業(従業地)", "000032214573", _POP41,
        "census2020_e16_01_industry_occupation_workplace_muni.xlsx", "f101bb80efad50b42c1f629d9ec96354",
        "c20_e16_01", "9e9c2941e9befce9fc5b0ad2f4fab281", 2020, "#34"),
    _xl("c20_e01_03", "同 第1-3表 男女・年齢・常住地又は従業地・通学地別通学者数(外から来る通学者)", "000032214143",
        _POP41, "census2020_e01_03_students_sex_age_place_muni.xlsx", "c57efbcad1ff2a76982f8e0356d5e143",
        "c20_e01_03", "f28fb46ce53b4ef2db8e41f90336df0b", 2020, "#53"),
    # --- 経済センサス 2021(駅周辺 13 町丁目の産業の中分類=娯楽業と生活関連の分け方だけに使う)
    Source("ecen21_area", "経済センサス2021 活動調査 町丁目別(駅周辺13町丁目の再集計)", "-",
           ("realworld", "census_r3", "station_area_industry.json"), "afe778fc38d742fe6b100857898a733e", 2021,
           columns="sim_buckets", r116_row="#6"),
)

_BY_ID: Final[Mapping[str, Source]] = MappingProxyType({s.sid: s for s in SOURCES})


def source(sid: str) -> Source:
    return _BY_ID[sid]


# ------------------------------------------------------------------------------------------ 検証側
@dataclass(frozen=True)
class VerifyRow:
    """R-116 §1 の「検証側=使わない」の 1 行。``tokens`` は道筋に現れたら止める語(小文字で照らす)。"""

    row: str
    what: str
    tokens: tuple[str, ...]


#: 封印した層の名(W19 の表から取る=本ファイルに名を書かない)。
_HOLDOUT = tuple(HOLDOUT_TOKENS)

#: R-116 §1 の 11 行(#11・#16・#17・#42・#45・#47・#49・#50・#57・#58・#59)。ファイルの無い行(研究の値)は
#: 語で持ち、読み口の外で値を書かないことは記録で示す。
VERIFY_SIDE: Final[tuple[VerifyRow, ...]] = (
    VerifyRow("#11", "PT 2018 c-2 の 0240〜0243 の集中量・b-4 の時刻別滞留人口・安全確保計画の滞留",
              ("pt6_b-4", "pt6_c-3", "pt6_c-4", "anzen_kakuho", "安全確保計画")),
    VerifyRow("#16", "人流のデータ(滞在人口・区の人流・境界の計数・1 km メッシュ・混雑統計・モバイル空間統計・都のモニタリング)",
              (*_HOLDOUT, "kddi", "jinryu", "realworld_live/odpt_rt", "mesh1km", "konzatsu", "mobile_kukan",
               "monitoring")),
    VerifyRow("#17", "駅の事業者別の利用者数(各社の公表・ODPT の乗降人員・区勢概要)",
              ("passengersurvey", "passenger_survey", "joukou", "kusei_gaiyo", "区勢概要")),
    VerifyRow("#42", "区民意識調査の個票(振り分けの承認まで全部)", ("kumin_ishiki", "ishiki_chosa", "区民意識")),
    VerifyRow("#45", "社会生活基本調査の「一緒にいた時間」・会話の件数・人の記憶の研究の値",
              ("together_time", "conversation_count", "dunbar")),
    VerifyRow("#47", "家計調査の 1 日の消費・現金の保有の調査", ("kakei", "家計調査", "cash_holding")),
    VerifyRow("#49", "住宅・土地統計調査の通勤時間", ("jutaku_tochi", "住宅・土地統計", "commute_time")),
    VerifyRow("#50", "考慮集合の大きさ・習慣の割合・心のさまよい", ("consideration_set", "habit_ratio", "mind_wandering")),
    VerifyRow("#57", "社会生活基本調査 第30表・第4-1/7-1/18-1表・第14/15表・第68-3表",
              ("000032224420", "estat_shakaiseikatsu_r3_4-1", "research_cache/r99", "calib/hunger",
               "diversity_anchors", "presence_validation_anchors", "hunger_energy_validation_anchors",
               "presence_anchors_v0", "hunger_energy_anchors_v0")),
    VerifyRow("#58", "ダイヤ改正の後の利用の推移・犯罪の統計・満員電車の密度", ("crime", "hanzai", "daiya_kaisei_suii")),
    VerifyRow("#59", "封印 S1・S2・K5・holdout H1〜H5", ("/holdout/", "holdout_compare", "jinryu_k5", "sealed_")),
)


def verify_tokens() -> tuple[tuple[str, str], ...]:
    """(行, 語)の組の全部(小文字)。"""
    return tuple((r.row, t.lower()) for r in VERIFY_SIDE for t in r.tokens)


class VerificationSideError(PermissionError):
    """検証側の表(R-116 §1 の 11 行・パターン台帳 §10)を開こうとした(開く前に止める)。"""


class NotAllowedError(PermissionError):
    """W21 の許可の一覧に無い道筋を開こうとした(開く前に止める)。"""


class MissingSourceError(FileNotFoundError):
    """材料の表が無いか、md5 が台帳と違う。"""


def _norm(p: Any) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(p))).replace("\\", "/")


def _hit(path: Any) -> str | None:
    forms = (os.fspath(path).replace("\\", "/").lower(), _norm(path).lower())
    for row, tok in verify_tokens():
        if any(tok in f for f in forms):
            return f"{row}:{tok}"
    return None


def _under(path: str, root: str) -> bool:
    root = root.rstrip("/")
    return path == root or path.startswith(root + "/")


_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC


def _is_write(mode: Any, flags: Any) -> bool:
    """``open`` の監査の引数(モードの文字列 or ``os.open`` のフラグ)が書き込みか。"""
    if isinstance(mode, str):
        return any(c in mode for c in "wax+")
    try:
        return bool(int(flags or 0) & _WRITE_FLAGS)
    except (TypeError, ValueError):
        return False


def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------ 守り
_ACTIVE: list["W21Guard"] = []
_HOOKED = False


def _audit(event: str, args: tuple) -> None:  # pragma: no cover - 監査フック(試験は W21Guard.active で通す)
    if event != "open" or not _ACTIVE:
        return
    path = args[0] if args else None
    if not isinstance(path, (str, bytes, os.PathLike)) or isinstance(path, int):
        return
    try:
        p = os.fsdecode(path)
    except (TypeError, ValueError):
        return
    _ACTIVE[-1].check_open(p, args[1] if len(args) > 1 else "r", args[2] if len(args) > 2 else 0)


@dataclass
class W21Guard:
    """W21 の読み口(許可の一覧と検証側の語)。

    Attributes:
        data: data 根。
        allow: 許すファイル(絶対の道筋の正規形)。
        allow_dirs: 読むのを許すディレクトリ(その下は全部=世界資産の置き場と出力先)。
        write_dirs: 書くのを許すディレクトリ(出力先だけ)。守る根の下で書き込みのモードの ``open`` は、この下で
            なければ止める〔検収 M1=本体の v2 に書かない守り〕。
        protect: 監査フックが守る根(data 根と世界資産の置き場。この下を一覧の外で開いたら止める)。
        opened: 読み口を通って開いたファイル(相対の道筋 → md5)。
    """

    data: Path
    allow: set[str] = field(default_factory=set)
    allow_dirs: list[str] = field(default_factory=list)
    write_dirs: list[str] = field(default_factory=list)
    protect: list[str] = field(default_factory=list)
    opened: dict[str, str] = field(default_factory=dict)
    opened_paths: dict[str, Path] = field(default_factory=dict)

    @classmethod
    def for_build(cls, data: Path, *, world: Path | None = None, out: Path | None = None,
                  extra: Sequence[Path] = ()) -> "W21Guard":
        """台帳の構築側の全部+世界資産(読むだけ)+出力先を許す。守る根は data 根。"""
        g = cls(data=Path(data))
        for s in SOURCES:
            g.allow.add(_norm(Path(data).joinpath(*s.path)))
            if s.derived:
                g.allow.add(_norm(Path(data).joinpath(*s.derived)))
        for e in extra:
            g.allow.add(_norm(e))
        for d in (world, out):
            if d is not None:
                g.allow_dirs.append(_norm(d))
        if out is not None:
            g.write_dirs.append(_norm(out))
        g.protect.append(_norm(data))
        if world is not None:
            g.protect.append(_norm(world))
        return g

    def _allowed(self, p: str) -> bool:
        if p in self.allow:
            return True
        return any(p == d or p.startswith(d.rstrip("/") + "/") for d in self.allow_dirs)

    def check(self, path: Any) -> Path:
        """読む前の検査(検証側 → 一覧の外の順)。通れば ``Path`` を返す。"""
        hit = _hit(path)
        if hit:
            raise VerificationSideError(f"検証側の表は開かない({hit}): {Path(path).name}")
        if not self._allowed(_norm(path)):
            raise NotAllowedError(f"W21 の許可の一覧に無い: {Path(path).name}")
        return Path(path)

    def check_open(self, p: str, mode: Any = "r", flags: Any = 0) -> None:
        """監査フックの検査。読みは許可の一覧・書き込みのモードは出力先の下だけ(守る根の下)。"""
        hit = _hit(p)
        if hit:
            raise VerificationSideError(f"検証側の表は開かない({hit}): {Path(p).name}")
        n = _norm(p)
        if not any(_under(n, r) for r in self.protect):
            return
        if _is_write(mode, flags):
            if not any(_under(n, w) for w in self.write_dirs):
                raise NotAllowedError(f"W21 は出力先の外に書かない(書き込みのモード): {Path(p).name}")
            return
        if not self._allowed(n):
            raise NotAllowedError(f"W21 の許可の一覧に無い: {Path(p).name}")

    @contextlib.contextmanager
    def active(self) -> Iterator["W21Guard"]:
        """守りの間は Python の ``open`` も検査する(監査フック・一度入れたら外せないので空なら何もしない)。"""
        global _HOOKED
        if not _HOOKED:
            sys.addaudithook(_audit)
            _HOOKED = True
        _ACTIVE.append(self)
        try:
            yield self
        finally:
            _ACTIVE.remove(self)

    # 読み口 ----------------------------------------------------------------------------
    def _note(self, p: Path, md5: str) -> None:
        try:
            rel = p.resolve().relative_to(self.data.resolve()).as_posix()
        except ValueError:
            rel = p.name
        self.opened[rel] = md5
        self.opened_paths[rel] = p.resolve()

    def read_bytes(self, path: Any, *, want_md5: str | None = None) -> bytes:
        p = self.check(path)
        if not p.exists():
            raise MissingSourceError(f"材料が無い: {p.name}")
        data = p.read_bytes()
        md5 = hashlib.md5(data).hexdigest()
        if want_md5 is not None and md5 != want_md5:
            raise MissingSourceError(f"md5 が台帳と違う: {p.name}({md5[:8]} != {want_md5[:8]})")
        self._note(p, md5)
        return data

    def md5_only(self, path: Any, *, want_md5: str | None = None) -> str:
        """中身を解かずに md5 だけ取る(xlsx の元の確かめ)。"""
        p = self.check(path)
        if not p.exists():
            raise MissingSourceError(f"材料が無い: {p.name}")
        md5 = _md5(p)
        if want_md5 is not None and md5 != want_md5:
            raise MissingSourceError(f"md5 が台帳と違う: {p.name}({md5[:8]} != {want_md5[:8]})")
        self._note(p, md5)
        return md5

    def read_parquet(self, path: Any, columns: Sequence[str] | None = None) -> dict[str, list]:
        import pyarrow.parquet as pq

        p = self.check(path)
        if not p.exists():
            raise MissingSourceError(f"世界資産が無い: {p.name}")
        self._note(p, _md5(p))
        t = pq.read_table(p, columns=list(columns) if columns is not None else None)
        return {n: t.column(n).to_pylist() for n in t.schema.names}

    def source_bytes(self, sid: str) -> bytes:
        s = source(sid)
        return self.read_bytes(self.data.joinpath(*s.path), want_md5=s.md5)


# ------------------------------------------------------------------------------------------ 読み
@dataclass(frozen=True)
class SmallArea:
    """小地域の表(渋谷区の行)。``values[sex]`` は ``(町丁目, 列)`` の配列(秘匿は nan)。"""

    sid: str
    keys: tuple[str, ...]
    labels: tuple[str, ...]
    values: Mapping[str, np.ndarray]
    ward: Mapping[str, np.ndarray]

    def col(self, label: str, sex: str = "総数") -> np.ndarray:
        return self.values[sex][:, self.labels.index(label)]

    def ward_col(self, label: str, sex: str = "総数") -> float:
        return float(self.ward[sex][self.labels.index(label)])


def _num(s: str) -> float:
    s = s.strip()
    if s in ("-", ""):
        return 0.0
    if s in ("X", "x", "…"):
        return float("nan")
    return float(s)


def read_small_area(guard: W21Guard, sid: str, keys: Sequence[str]) -> SmallArea:
    """小地域の CSV(cp932)から渋谷区の行を読む。``keys`` は町丁目の鍵(11 桁=市区町村 5 桁+町丁字コード)の並び。

    見出しは「市区町村コード」のある行。値の列は「字・丁目名」の右(列の名は上の段の表章項目と合わせない=下の段だけ)。
    男女の列があれば「総数/男/女」ごとに分ける(無ければ「総数」だけ)。鍵に無い行は捨てる。
    """
    text = guard.source_bytes(sid).decode("cp932")
    rows = list(csv.reader(io.StringIO(text)))
    hi = next(i for i, r in enumerate(rows) if "市区町村コード" in r)
    head = rows[hi]
    c_city = head.index("市区町村コード")
    c_code = head.index("町丁字コード")
    c_lvl = head.index("地域階層レベル")
    c_chome = head.index("字・丁目名")
    c_sex = head.index("男女") if "男女" in head else None
    # 男女でない行の次元(第6-1表の「世帯員の年齢による世帯の種類」など)は「総数」の行だけを使う
    c_dim = c_city - 1 if c_sex is None and c_city >= 2 and head[c_city - 1] and not head[c_city - 1].isdigit() else None
    vcols = list(range(c_chome + 1, len(head)))
    labels = tuple(head[j] for j in vcols)
    index = {k: i for i, k in enumerate(keys)}
    sexes = ("総数", "男", "女") if c_sex is not None else ("総数",)
    vals = {s: np.full((len(keys), len(vcols)), np.nan) for s in sexes}
    ward = {s: np.full(len(vcols), np.nan) for s in sexes}
    for r in rows[hi + 1:]:  # 逐次: 表の行の数ぶん
        if len(r) <= c_chome or r[c_city] != WARD_CODE:
            continue
        if c_dim is not None and r[c_dim] != "総数":
            continue
        sx = r[c_sex] if c_sex is not None else "総数"
        if sx not in vals:
            continue
        v = np.array([_num(r[j]) for j in vcols])
        if r[c_lvl] == "1":
            ward[sx] = v
            continue
        i = index.get(WARD_CODE + r[c_code])
        if i is not None:
            vals[sx][i] = v
    return SmallArea(sid, tuple(keys), labels, vals, ward)


@dataclass(frozen=True)
class Derived:
    """xlsx の写し(渋谷区の行)。``table[次元の値の組] = 値の配列``(地域の次元は落とす)。"""

    sid: str
    dims: tuple[str, ...]
    items: tuple[str, ...]
    table: Mapping[tuple[str, ...], np.ndarray]

    def get(self, *dims: str) -> np.ndarray:
        return self.table[tuple(dims)]

    def item(self, label: str) -> int:
        return self.items.index(label)


def read_derived(guard: W21Guard, sid: str) -> Derived:
    """台帳の xlsx の写しを読む(写しの md5 と、写しに書かれた元の xlsx の md5 の両方を台帳と照らす)。"""
    s = source(sid)
    if not s.derived:
        raise ValueError(f"{sid} は写しの表ではない")
    guard.md5_only(guard.data.joinpath(*s.path), want_md5=s.md5)
    doc = json.loads(guard.read_bytes(guard.data.joinpath(*s.derived), want_md5=s.derived_md5).decode("utf-8"))
    if doc.get("source_md5") != s.md5:
        raise MissingSourceError(f"写しの元の md5 が台帳と違う: {sid}")
    dims = tuple(doc["dims"])
    keep = [j for j, d in enumerate(dims) if not d.startswith(("地域", "都道府県"))]
    table: dict[tuple[str, ...], np.ndarray] = {}
    for r in doc["rows"]:
        key = tuple(r[j] for j in keep)
        table[key] = np.array([np.nan if v is None else float(v) for v in r[-1]], dtype=np.float64)
    return Derived(sid, tuple(dims[j] for j in keep), tuple(doc["items"]), table)


def read_derived_merged(guard: W21Guard, sids: Sequence[str]) -> Derived:
    """同じ形の写し(男・女の別表など)を 1 つの表に合わせる(次元と項目が同じこと・鍵の重なりは不可)。"""
    parts = [read_derived(guard, sid) for sid in sids]
    table: dict[tuple[str, ...], np.ndarray] = {}
    for d in parts:
        if d.dims != parts[0].dims or d.items != parts[0].items:
            raise ValueError(f"写しの形が違う: {d.sid} と {parts[0].sid}")
        for k, v in d.table.items():
            if k in table:
                raise ValueError(f"写しの鍵が重なる: {k}")
            table[k] = v
    return Derived("+".join(sids), parts[0].dims, parts[0].items, table)


def read_estat_json(guard: W21Guard, sid: str) -> dict[tuple[str, str], int]:
    """e-Stat API の JSON(第1表・第3表)→ ``(cat01, area) → 値``(W16 と同じ読み方)。"""
    doc = json.loads(guard.source_bytes(sid).decode("utf-8"))
    out: dict[tuple[str, str], int] = {}
    for row in doc["values"]:
        try:
            out[(row["@cat01"], row["@area"])] = int(row["$"])
        except (KeyError, ValueError):
            continue
    return out


# ------------------------------------------------------------------------------------------ PT c-2
#: 舞台の 4 ゾーン(計画基本ゾーン)。集中量はどの列も検証側・舞台の発生量は「自宅以外からの私事」だけ構築側
#: (10-13b §1 1-3)。
PT_STAGE_ZONES: Final[tuple[str, ...]] = ("0240", "0241", "0242", "0243")
#: 読んでよい値の列(名前 → 意味)。これ以外を頼むと開く前に止める〔検収 L1〕。
PT_C2_ALLOWED: Final[Mapping[str, str]] = MappingProxyType({
    "generation_total": "舞台の外のゾーンの発生量(発時間帯・目的の計)",
    "private_non_home": "自宅以外からの私事の発生量(発時間帯)",
})
#: 値を読む前に出す監査のイベント(読む列の位置)。試験の監査フックが「許可の外の列が読まれない」を確かめる。
PT_C2_AUDIT_EVENT: Final[str] = "shibuya.w21.pt_c2.read_columns"
#: 見出しを探す行の上限(表題・空の行・2 段の見出し・単位の行=実ファイルは 5 行)。
_PT_HEADER_MAX_LINES: Final[int] = 12
_PT_UNIT_WORDS: Final[tuple[str, ...]] = ("トリップ", "単位")
_PT_HOME_BASED = re.compile(r"^自宅[－\-―‐ー]")


def _ffill(row: Sequence[str]) -> list[str]:
    out, last = [], ""
    for c in row:  # 逐次: 列の数ぶん(29)
        last = c.strip() or last
        out.append(last)
    return out


def pt_c2_layout(guard: W21Guard, path: Path) -> dict[str, Any]:
    """c-2 の見出しの行だけを文字として読み、列の位置を決める(値の行は読まない)。

    形(実ファイル=29 列): 表題の行・空の行・2 段の見出し(上の段=「発生量」「集中量」の塊・下の段=ゾーン・時間帯・
    目的)・単位の行。単位の行(「トリップ」など)で読むのを止める。見つからなければ止める(値の行を読まないため)。
    """
    p = guard.check(path)
    rows: list[list[str]] = []
    with open(p, "rb") as f:
        for _ in range(_PT_HEADER_MAX_LINES):  # 逐次: 見出しの行の数ぶん
            ln = f.readline()
            if not ln:
                break
            row = next(csv.reader([ln.decode("cp932").rstrip("\r\n")]), [])
            rows.append(row)
            cells = [c.strip() for c in row if c.strip()]
            if len(cells) >= 3 and all(any(w in c for w in _PT_UNIT_WORDS) for c in cells):
                break
        else:
            raise ValueError("c-2 の見出しに単位の行が無い(形が想定と違う=値の行は読まない)")
    if len(rows) < 3:
        raise ValueError("c-2 の見出しが短い")
    unit_i = len(rows) - 1
    upper, lower = _ffill(rows[unit_i - 2]), [c.strip() for c in rows[unit_i - 1]]
    n = max(len(upper), len(lower), len(rows[unit_i]))
    upper += [upper[-1] if upper else ""] * (n - len(upper))
    lower += [""] * (n - len(lower))
    zone = next((j for j, c in enumerate(lower) if "ゾーン" in c), 0)
    tslot = next((j for j, c in enumerate(lower) if "時間帯" in c or "時刻" in c), 1)
    gen = [j for j in range(n) if "発生" in upper[j] and "集中" not in upper[j]]
    conc = [j for j in range(n) if "集中" in upper[j]]
    tot = [j for j in gen if lower[j] in ("計", "合計", "総数")]
    prv = [j for j in gen if "私事" in lower[j] and not _PT_HOME_BASED.match(lower[j])]
    if len(tot) != 1 or len(prv) != 1 or not conc:
        raise ValueError(f"c-2 の列の並びが想定と違う(発生量の計 {len(tot)}・自宅以外の私事 {len(prv)}・集中量 {len(conc)})")
    return {"n_columns": n, "header_lines": unit_i + 1, "zone": zone, "time": tslot,
            "generation_total": tot[0], "private_non_home": prv[0], "concentration": conc}


def read_pt_c2_build_side(guard: W21Guard, path: Path,
                          columns: Sequence[str] = ("generation_total", "private_non_home")) -> dict[str, Any]:
    """PT 2018 c-2 から構築側の列だけを返す〔検収 L1〕。

    1. 頼まれた列が :data:`PT_C2_ALLOWED` の外なら**開く前に**止める(``VerificationSideError``)。
    2. 見出しの行だけを文字として読んで列の位置を決める(:func:`pt_c2_layout`)。許可の列が集中量の塊にあれば止める。
    3. 値は pyarrow の CSV で ``include_columns``(=usecols)に許可の列とゾーン・時間帯だけを渡して読む=集中量の列は
       配列にしない。読む前に監査のイベント :data:`PT_C2_AUDIT_EVENT`(読む列の位置)を出す。
    返り値: ``{"columns": [...], "outside": {ゾーン: {時間帯: {列: 値}}}, "stage_private": {ゾーン: {時間帯: 値}}}``。
    舞台の 4 ゾーンは「自宅以外からの私事」だけ。**W21 の組み立ては呼ばない**(段 1 は R-116 §4 を引く)。
    """
    bad = [c for c in columns if c not in PT_C2_ALLOWED]
    if bad:
        raise VerificationSideError(f"c-2 の許可の外の列は読まない: {bad}")
    lay = pt_c2_layout(guard, path)
    want = {c: lay[c] for c in columns}
    if any(j in lay["concentration"] for j in want.values()):
        raise VerificationSideError("c-2 の許可の列が集中量の塊にある(読まない)")
    import pyarrow as pa
    import pyarrow.csv as pacsv

    keep = sorted({lay["zone"], lay["time"], *want.values()})
    names = [f"c{j}" for j in range(lay["n_columns"])]
    sys.audit(PT_C2_AUDIT_EVENT, Path(path).name, tuple(keep))
    t = pacsv.read_csv(
        guard.check(path),
        read_options=pacsv.ReadOptions(encoding="cp932", skip_rows=lay["header_lines"], column_names=names),
        parse_options=pacsv.ParseOptions(invalid_row_handler=lambda _row: "skip"),
        convert_options=pacsv.ConvertOptions(include_columns=[names[j] for j in keep],
                                             column_types={names[j]: pa.string() for j in keep}),
    )
    zone = [str(z or "").strip().lstrip(":") for z in t.column(names[lay["zone"]]).to_pylist()]
    tsl = [str(x or "").strip() for x in t.column(names[lay["time"]]).to_pylist()]
    vals = {c: [_num(str(v or "")) for v in t.column(names[j]).to_pylist()] for c, j in want.items()}
    outside: dict[str, dict[str, dict[str, float]]] = {}
    stage: dict[str, dict[str, float]] = {}
    for i, (z, ts) in enumerate(zip(zone, tsl)):  # 逐次: 行の数ぶん
        if not z:
            continue
        if z in PT_STAGE_ZONES:
            if "private_non_home" in vals:
                stage.setdefault(z, {})[ts] = vals["private_non_home"][i]
        else:
            outside.setdefault(z, {})[ts] = {c: v[i] for c, v in vals.items()}
    return {"columns": list(want), "outside": outside, "stage_private": stage}
