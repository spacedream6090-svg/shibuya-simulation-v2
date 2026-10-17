"""build.sched.w20_w21_port — W21(人口の作り直し)の人の表 → W20(暦 1a)の ``Attributes`` を作る口(第 4 期 4-1 段 10 の材料)。

正: 親の判断(PENDING 仮-31・検収 M1): 段 10 で W21 から W20 の ``Attributes``(:func:`calendar_from_attributes` の入力
19 欄)を作る関数を書く。職業は ``occupation_major`` を直接(第74-9表の職業の名へ)・担当の語は W20 の
:data:`~shibuya.build.sched.w20_calendar_1a.DUTY_ROLE_SPEC` の鍵(**鍵に無い語は止める**=黙って「担当なし」にしない)・
雇用の語は ``attr_fns.W16_EMPLOYMENT_OF`` で W16 の 6 値に写す。W20 の既定(W16 の在庫からの ``attributes_from_world``)は
変えない(本モジュールは別の口)。

W16 の口(``attributes_from_columns``)との違い
- 種別 0・2(席のある体)でも担当の語を読む(W16 の口は席を先にして担当を見ない)。W21 は担当を勤め先が舞台の中の体だけに
  付けた(段 4)ので、担当のある体は席の有無に依らず担当の表の場所と交替制を使う。
- 従業上の地位は W21 が持つ=:attr:`Attributes.census_middles` は全員空(第6-2表の引き直しをしない=W20 の docstring の
  「新しい人口が地位を持てば、この段を飛ばしてその値を渡す」)。地位の写しは ``employment_pool``(6 値)で W20 の
  ``draw_employment_status`` がそのまま読む。
- 職業は全員 ``occupation_major`` から(W16 の口は担当の体だけ)。分類不能(L)と空欄は空。
- 片道の通勤時間: 歩いて通う住民=W21 の歩く道のり ÷ 歩く速さの参照値(``attr_fns.walk_seconds``=人物の文と同じ関数)の分
  (切り上げ=W20 は整数の分・人物の文は四捨五入=丸めた言葉)・
  自宅で働く人=0・ほか(電車の人)は空欄(−1=W20 が 30 分を入れる=``lead_default`` に数える)。
- 学校: 住民の在学の種類のうち授業のある段階(幼稚園・小学校〜大学院)=授業の約束。保育園・認定こども園・未就学のほかは
  授業でない(W20 の ``TEACHING_STAGES`` に合わせた=認定こども園を授業にしない)。学校のセルは W21 に無い=全員 −1。
- 席と学校の両方(働く在学者)は勤務を先に(W20 の親の判断 第337 中 1 と同じ=``seat_and_school`` に数える)。W21 の席は
  働く人だけに付けた=``seat_nonworking`` は全員偽。

担当の語の表: W20 の :data:`~shibuya.build.sched.w20_calendar_1a.DUTY_ROLE_SPEC`(W16 の在庫の 22 語=土台のまま=W20cal の
``param_hash`` を動かさない)と、W21b の 4 語(店長・補充・配送作業員・警備員)の :data:`DUTY_ROLE_SPEC_W21`(同じ形の
当てはめ)。本モジュールだけが両方を引く(親の判断=検収 中 1 (b))。

当てはめの宣言は ``build/pop/w21_build_c.W21C_EXPEDIENTS``(つなぎの台帳と 1 対 1)。

逐次ループ宣言(P4): 担当の語の種類の数ぶん(≤ 25)と、語の種類ごとの写像の引き。体の数に比例するループは無い。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

from shibuya.core.time_consts import SECONDS_PER_MINUTE

from ..pop.attr_fns import W16_EMPLOYMENT_OF, walk_seconds
from . import w20_calendar_1a as W

__all__ = ["UnknownDutyRoleError", "W21_INPUT_COLUMNS", "OCC_OF_MAJOR", "TEACHING_OF_SCHOOL", "WORKPLACE_OF_AREA",
           "DUTY_ROLE_SPEC_W21", "duty_role_spec", "attributes_from_w21", "lead_minutes"]

#: 読む列(``w21_people`` の名と段 3 の在学の種類)。
W21_INPUT_COLUMNS: Final[tuple[str, ...]] = (
    "person_id", "w16_kind", "age", "industry_key", "duty_role", "occupation_major", "employment_status",
    "labour_status", "workplace_area", "school_kind", "home_cell", "work_cell", "commute_mode", "commute_path_m",
)
#: 職業大分類(国勢調査の記号)→ 第74-9表の職業の名(``W.OCC_ROWS``)。L(分類不能)と空欄は空。
OCC_OF_MAJOR: Final[Mapping[str, str]] = MappingProxyType({
    "A": "管理的職業従事者", "B": "専門的・技術的職業従事者", "C": "事務従事者", "D": "販売従事者",
    "E": "サービス職業従事者", "F": "保安職業従事者", "G": "農林漁業従事者", "H": "生産工程従事者",
    "I": "輸送・機械運転従事者", "J": "建設・採掘従事者", "K": "運搬・清掃・包装等従事者",
})
#: 段 3 の在学の種類 → 授業の約束があるか(W20 の ``TEACHING_STAGES`` の語に当たる段階だけ)。
TEACHING_OF_SCHOOL: Final[Mapping[str, bool]] = MappingProxyType({
    "elementary": True, "junior_high": True, "high": True, "junior_college": True, "university": True,
    "graduate": True, "kindergarten": True, "nursery": False, "kodomoen": False, "preschool_other": False,
    "none": False, "": False,
})
#: W21 の勤め先の場所 → W20 の ``WP_*``。
WORKPLACE_OF_AREA: Final[Mapping[str, int]] = MappingProxyType({
    "stage": W.WP_AREA, "home": W.WP_HOME, "ward_outside_stage": W.WP_OUTSIDE, "outside_ward": W.WP_OUTSIDE, "": W.WP_NONE,
})
#: W21b の担当の語のうち W20 の ``DUTY_ROLE_SPEC`` に無い 4 語(``attr_fns.DUTY_WORDS_NOT_IN_W20``)→ (職業, 産業の鍵, 経済
#: センサスの中分類, 場所, 交替制, 勤務の約束がある)。W20 の表と同じ形の当てはめ(未リサーチ・つなぎの台帳 W21C_EXPEDIENTS)。
DUTY_ROLE_SPEC_W21: Final[Mapping[str, tuple[str, str, tuple[str, ...], int, bool, bool]]] = MappingProxyType({
    "店長": ("販売従事者", "", (), W.PLACE_BUILDING, False, True),
    "補充": ("販売従事者", "WR", ("56", "57", "58", "59", "60", "61"), W.PLACE_BUILDING, True, True),
    "配送作業員": ("運搬・清掃・包装等従事者", "TR", ("44", "47"), W.PLACE_AREA, False, True),
    "警備員": ("保安職業従事者", "SV", ("92",), W.PLACE_BUILDING, True, True),
})


def duty_role_spec() -> dict[str, tuple[str, str, tuple[str, ...], int, bool, bool]]:
    """本口が引く担当の語の表(W20 の 22 語+W21 の 4 語=鍵は重ならない)。"""
    both = dict(W.DUTY_ROLE_SPEC)
    dup = set(both) & set(DUTY_ROLE_SPEC_W21)
    if dup:
        raise ValueError(f"担当の語が W20 と W21 の表に重なる: {sorted(dup)}")
    both.update(DUTY_ROLE_SPEC_W21)
    return both


class UnknownDutyRoleError(ValueError):
    """W21 の担当の語が W20 の ``DUTY_ROLE_SPEC`` の鍵に無い(黙って「担当なし」にしない)。"""


def _s(x: Any) -> np.ndarray:
    a = np.asarray(x, dtype=object)
    return np.where(np.equal(a, None), "", a).astype(str)


def _map(words: np.ndarray, table: Mapping[str, Any], default: Any) -> np.ndarray:
    """語の種類ごとに写す(逐次: 語の種類の数)。"""
    u, inv = np.unique(words, return_inverse=True)
    lut = np.array([table.get(x, default) for x in u.tolist()], dtype=object)
    return lut[np.asarray(inv).reshape(-1)] if words.size else np.zeros(0, dtype=object)


def lead_minutes(mode: Any, path_m: Any) -> np.ndarray:
    """片道の通勤時間[分]: 歩き=道のり ÷ 歩く速さの参照値(切り上げ・少なくとも 1)・自宅=0・ほかは −1(空欄)。"""
    md = _s(mode)
    p = np.asarray(path_m, dtype=np.float64)
    out = np.full(md.size, W.BLANK, dtype=np.int64)
    walk = (md == "walk") & (p >= 0)
    out[walk] = np.maximum(1, np.ceil(walk_seconds(p[walk]) / SECONDS_PER_MINUTE)).astype(np.int64)
    out[md == "home"] = 0
    return out


def attributes_from_w21(people: Mapping[str, Any]) -> W.Attributes:
    """W21 の人の表(``w21_people`` の列+段 3 の ``school_kind``=:data:`W21_INPUT_COLUMNS`)→ W20 の ``Attributes``。

    担当の語が ``DUTY_ROLE_SPEC``+:data:`DUTY_ROLE_SPEC_W21` の鍵に無ければ :class:`UnknownDutyRoleError`(負の対照=試験)。``agent_id`` は W21 の
    ``person_id``(ランの体の番号との対応は段 10 の差し替えで決める)。
    """
    miss = [c for c in W21_INPUT_COLUMNS if c not in people]
    if miss:
        raise KeyError(f"W21 の人の表に無い列: {miss}")
    pid = np.asarray(people["person_id"], dtype=np.int64)
    n = int(pid.size)
    duty = _s(people["duty_role"])
    spec = duty_role_spec()
    unknown = sorted(set(np.unique(duty).tolist()) - set(spec) - {""})
    if unknown:
        raise UnknownDutyRoleError(f"W20 の DUTY_ROLE_SPEC と DUTY_ROLE_SPEC_W21 に無い担当の語: {unknown}")

    lab = _s(people["labour_status"])
    area = _s(people["workplace_area"])
    wp = _map(area, WORKPLACE_OF_AREA, W.WP_NONE).astype(np.int8)
    employed = (lab == "employed") & (wp != W.WP_NONE)
    teach = _map(_s(people["school_kind"]), TEACHING_OF_SCHOOL, False).astype(bool)
    school = teach & ~employed
    seat_and_school = teach & employed
    occ = _map(_s(people["occupation_major"]), OCC_OF_MAJOR, "").astype(object)
    ind = _s(people["industry_key"]).astype(object)
    emp_pool = _map(_s(people["employment_status"]), dict(W16_EMPLOYMENT_OF), "非就業").astype(object)
    place = np.zeros(n, dtype=np.int8)
    shift = np.zeros(n, dtype=bool)
    for role in sorted(set(np.unique(duty).tolist()) - {""}):  # 逐次: 担当の語の種類の数(≤ 25)
        _occ, _ind, _mids, pl, sh, job = spec[role]
        m = (duty == role) & employed
        place[m] = pl
        shift[m] = sh
        if not job:
            employed = employed & ~(duty == role)
    return W.Attributes(
        agent_id=pid, kind=np.asarray(people["w16_kind"], dtype=np.int64), age=np.asarray(people["age"], dtype=np.int64),
        industry=ind.tolist(), duty_role=duty.astype(object).tolist(), occupation=occ.tolist(),
        employment_pool=emp_pool.tolist(), employed=employed, workplace=np.where(employed, wp, W.WP_NONE).astype(np.int8),
        school=school, work_cell=np.asarray(people["work_cell"], dtype=np.int64), school_cell=np.full(n, W.BLANK,
                                                                                                      dtype=np.int64),
        home_cell=np.asarray(people["home_cell"], dtype=np.int64),
        lead_min=lead_minutes(people["commute_mode"], people["commute_path_m"]),
        census_middles=[()] * n, place_hint=place, shift=shift,
        seat_nonworking=np.zeros(n, dtype=bool), seat_and_school=seat_and_school,
    )
