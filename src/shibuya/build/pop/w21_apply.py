"""W21 段 10「差し替え」(第 4 期 4-1 段 10=4-3 版上げ 3 回目)の組み立て。版 1.1.0(検収の直し=通学者を残す・担当の体の
機能定員と種別 8・乗務員の提供者・外の雇用主の雇用の行・提供者の使い回しの門)。

    python -m shibuya.build.pop.w21_apply --out data/world/v2_stage_4-3 --data data [--world data/world/v2]

- 前提: ``--out`` に本体の v2 の写し(W17 のプロンプトと応答の jsonl を除く)と、W21 の資産(段 1〜3=``w21_*``・段 4〜7=
  W21b 1.2.0・段 8〜10=W21c 1.3.0)がある(活性化の道具 ``docs/bench/analysis/wallbounce-1012/pop43/tools/activate_pop43.py
  stage`` が組む)。``--world``(元の W16・W17=本体の v2)は**読むだけ**。``--out`` の W16 の出力(``w16_*``)と W17 の週次表と
  見出し(``W16.header.json``・``W17.header.json``)を書き換え、W20cal(暦 1a の影)の週の表を新しい母集団で組む。本体の
  ``data/world/v2`` には書かない(:func:`check_out_apply`)。
- 出力(:data:`OUTPUTS_APPLY`)と ``w21_apply_manifest.json``・``W21apply.header.json``。``w21_apply_build_hash``=出力の sha256 を
  連ねた文字列の sha256(2 回組んで一致=試験と記録)。

親の判断(PENDING 仮-33=段 10 の 10 問の正)の実装の形:

1. **運輸の二重**: W21 の駅員・電車運転士・車掌を採り、W16 の鉄道の行(駅員 300・電車運転士 60・車掌 40)を外す。バス
   運転士 120・タクシー運転手 350 は残す(:data:`W16_GROUP_ACTION`)。〔1.1.0・検収 M2〕W21 の担当の体(:data:`CREW_ROLES`)は
   **機能定員**(外す W16 の乗務員の同じ担当の語の数・W21 に居る数が上限)まで種別 8(乗務員)・目的=職務にし、日課の提供者は
   外す W16 の乗務員の同じ担当の語から選ぶ(交代勤務の日課・居なければ止まる)。定員の外の担当の体は種別 0・2 のまま通勤者の
   日課(宣言)。
2. **地位の分け**: 段 4〜7 を W21b 1.2.0 で組み直した資産を読む(本モジュールは分けない)。
3. **番号の対応表**: W16 の残す行の ``agent_id`` は不変(再現の鍵)・W21 の人は ``agent_id = BASE + person_id``(``BASE``=W16 の
   ``agent_id`` の最大 + 1=全単射・``w21_agent_map.parquet``)。権利台帳の ``holder_id``(``person_id``)も同じ写像で
   ランの番号へ(``w21_rights_run.parquet``)。店の持ち主の行(閉じた表の外)は入れない(PENDING §1-1「閉じた表の店」の判断の後)。
4. **W20 の口**: 8 区分から第 31/36 表の行へ直接(``build.sched.w20_w21_port.employment_from_w21``)・電車で通う人の片道は
   W20 の既定 30 分(〔1.1.0・親の判断〕舞台の中の道のりでは埋めない)。
5〜9. 段 9 の口(W21c 1.3.0): CP5-3 は POI の番号(``w21_persona.naming_check_ids``)・型の無い言語は日本語の型で代えて印・
   区別できない人は通う駅の口の路線の名で区別。
6. **人物の欄**: engine の側(``engine.decision.persona``)が ``w21_persona_{short,long}.parquet`` を母集団の ``w21_person_id``
   の列で読む(本モジュールは列を置くだけ)。
10. **W16 の残りの群**: 来街者・定期来街者・訪日来街者(96,006 行)と指令・路上の役割・救急隊員・夜間清掃員は残す。
    〔1.1.0・検収 M1〕通学者(33,385 行・複製 16,695 を含む)も残す(W21 に外から来る通学者の体が無い=つなぎ)。

〔1.1.0・検収 M3〕**外の雇用主**: 勤め先のセルはあるが組織の無い W21 の体(席の外=``no_seat_overflow``・``no_seat_industry``)に、
権利台帳の雇用の行を「体 → 外の雇用主(組織の番号 :data:`OUTSIDE_EMPLOYER_ORG`=閉じた表の外の番号)」で 1 行置く(engine の
給料日は外界から払う=登録済みの faucet「域外雇用主の賃金」)。

W17(週次表)の扱い〔**親の判断が要る=仮採用・記録 pop43 の問い 1**〕: W17 は凍結(CA1)で、W21 の人の行は無い(エンジンの
計画実行層は母集団の全員の行を要る=``WeeklySchedule.restrict_to``)。そこで W21 の人ごとに、外す W16 の行の体から**提供者**を
1 人選び、その体の 7 日の行を写す(:func:`donor_schedules`・場所が自宅・職場・学校の行のセルは受け手の家・勤め先で置き換え・
学校のセルは提供者のまま=W21 に学校のセルが無い)。選び方は (種別・勤め先のセルの有無・駅の口の有無・授業の有無・男女・年齢
5 歳)の層で、層に提供者が居なければ年齢 → 男女 → 授業 → 駅の口 → 勤め先の順に外して広げる。層の中は Philox の並べ替えで、
使っていない提供者を先に・足りなければ繰り返す(数を記録)。

近似の宣言は :data:`W21APPLY_EXPEDIENTS`(つなぎの台帳に 1 行ずつ)。

逐次ループ宣言(P4): W16 の群の数ぶん(≤ 40)・提供者の層の数ぶん(層の段 6 × 層の数 ≤ 約 3,000)・出力の数ぶん。体ごとの for は
無い(W20cal の ``attributes_from_columns`` は残す W16 の体の数ぶん=W20cal の宣言のまま)。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from shibuya.core.rng import k19_counter_array, philox_array, unit_float

from ..geo import common as C
from ..sched import w20_calendar_1a as W20
from ..sched import w20_w21_port as WP
from . import attr_fns as A
from . import w21_build as W
from . import w21_build_b as WB
from . import w21_build_c as WCB
from . import w21_sources as S

__all__ = ["STAGE_APPLY", "STAGE_VERSION_APPLY", "OUTPUTS_APPLY", "MANIFEST_APPLY", "W21APPLY_EXPEDIENTS",
           "W16_GROUP_ACTION", "UnknownW16GroupError", "ProtectedOutputErrorApply", "check_out_apply", "w16_actions",
           "w21_population_columns", "merge_population", "donor_schedules", "rights_run_rows", "apply", "main",
           "POPULATION_COLUMNS", "W17_COLUMNS", "DONOR_LEVELS", "AGE_EDGES", "SWAP_ASSET", "REPLACED_W16_OUTPUTS",
           "select_crews", "CREW_ROLES", "CREW_DONOR_LEVELS", "DONOR_MAX_REUSE", "OUTSIDE_EMPLOYER_ORG",
           "OUTSIDE_EMPLOYER_SEATS", "KIND_CREW", "PURPOSE_DUTY"]

STAGE_APPLY: Final[str] = "W21apply"
STAGE_VERSION_APPLY: Final[str] = "1.1.0"
#: 差し替えの資産の置き場の名(``data/world`` の下)。
SWAP_ASSET: Final[str] = "v2_stage_4-3"
#: 書き換える W16 の出力(W16 の見出しの出力の名=``w16_chome.parquet`` は国勢調査の町丁目の表=そのまま写す)。
REPLACED_W16_OUTPUTS: Final[tuple[str, ...]] = ("w16_population.parquet", "w16_households.parquet",
                                                "w16_duty_roster.parquet", "w16_gates.json", "w16_cohorts.json")
#: 本段の出力(W16・W17 の出力の名を含む=見出しは別)。
OUTPUTS_APPLY: Final[tuple[str, ...]] = (
    *REPLACED_W16_OUTPUTS, "w17_schedule.parquet", "w21_agent_map.parquet", "w21_rights_run.parquet",
    "w20_calendar_1a.parquet", "w20_calendar_1a_materials.json", "w21_apply_checks.json",
)
MANIFEST_APPLY: Final[str] = "w21_apply_manifest.json"
#: W20cal(暦 1a)の見出しの名(W20cal と同じ=``build.sched.w20_calendar_1a.HEADER_NAME``)。
CALENDAR_HEADER: Final[str] = W20.HEADER_NAME

#: W16 の母集団の列と型(``w16_population.parquet`` の並び=engine の ``agents.population`` が読む)+差し替えで足す列。
POPULATION_COLUMNS: Final[tuple[tuple[str, pa.DataType], ...]] = (
    ("agent_id", pa.int32()), ("kind", pa.int8()), ("purpose", pa.int8()), ("age", pa.uint8()), ("sex", pa.int8()),
    ("home_cell", pa.int32()), ("work_cell", pa.int32()), ("school_cell", pa.int32()), ("direction_node", pa.int32()),
    ("chome_key", pa.string()), ("household_id", pa.int32()), ("home_building", pa.int32()), ("org_id", pa.int32()),
    ("industry_key", pa.string()), ("duty_role", pa.string()), ("pool_layer", pa.int8()), ("pool_index", pa.int32()),
    ("synthetic", pa.bool_()), ("is_foreign", pa.bool_()),
    # 〔段 10〕差し替えで足す列(W16 の残す行は −1 か空欄): W21 の人の番号・月の賃金(段 5)・賃金の写像の語(職業大分類の名=
    # 賃金構造の職種の名・雇用の語=W16 の 6 値)
    ("w21_person_id", pa.int32()), ("wage_monthly", pa.int64()), ("persona_occupation", pa.string()),
    ("persona_employment", pa.string()),
)
#: W17 の週次表の列と型(``w17_schedule.parquet`` と同じ)。
W17_COLUMNS: Final[tuple[tuple[str, pa.DataType], ...]] = (
    ("agent_id", pa.int32()), ("day", pa.int8()), ("seq", pa.int16()), ("start_min", pa.int16()),
    ("end_min", pa.int16()), ("activity_code", pa.int8()), ("place_kind", pa.int8()), ("target_cell", pa.int32()),
    ("block_kind", pa.int8()),
)
#: W17 の場所語の番号(``agents.weekly.PLACE_WORDS`` の並び=自宅 0・職場 1・学校 2)。
PLACE_HOME, PLACE_WORK, PLACE_SCHOOL = 0, 1, 2
#: 年齢の層(``agents.population.AGE_EDGES`` と同じ 16 階級)。
AGE_EDGES: Final[np.ndarray] = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75], dtype=np.int64)
AGE_EDGES.flags.writeable = False
#: W16 の目的の語の番号(``w16_population.PURPOSE_NAMES``=勤務 0・居住 4)。
PURPOSE_WORK, PURPOSE_RESIDE = 0, 4

#: W16 の群(種別, 担当の語)→ 扱い(親の判断 仮-33 の (1)・(10)・PENDING 仮-31)。ここに無い群は止める
#: (:class:`UnknownW16GroupError`=黙って残さない・外さない)。
W16_GROUP_ACTION: Final[Mapping[tuple[int, str], str]] = MappingProxyType({
    (0, ""): "remove", (2, ""): "remove", (3, ""): "remove", (3, "議員"): "remove", (5, ""): "keep",
    (8, "警察官"): "remove", (8, "消防士"): "remove", (8, "清掃作業員"): "remove", (8, "納品ドライバー"): "remove",
    (8, "駅員"): "remove", (8, "電車運転士"): "remove", (8, "車掌"): "remove",
    (1, ""): "keep", (4, "指令"): "keep", (4, ""): "keep", (6, ""): "keep", (7, ""): "keep",
    (8, "バス運転士"): "keep", (8, "タクシー運転手"): "keep", (8, "夜間清掃員"): "keep", (8, "救急隊員"): "keep",
    (8, "キッチンカー営業者"): "keep", (8, "ストリートミュージシャン"): "keep", (8, "ティッシュ配り"): "keep",
    (8, "募金スタッフ"): "keep", (8, "街頭演説者"): "keep", (8, "路上占い師"): "keep", (8, "路上支援員"): "keep",
    (8, "路上生活者"): "keep", (8, "配信者"): "keep",
})
#: 提供者の層の段(左から外して広げる・最後は種別だけ)。
DONOR_LEVELS: Final[tuple[tuple[str, ...], ...]] = (
    ("kind", "work", "entry", "school", "sex", "age"), ("kind", "work", "entry", "school", "sex"),
    ("kind", "work", "entry", "school"), ("kind", "work", "entry"), ("kind", "work"), ("kind",),
)
#: 乱数の用途名(Philox・鍵=体の番号)。
RNG_DONOR_ORDER: Final[str] = "w21apply.w17.donor.order"
RNG_RECIPIENT_ORDER: Final[str] = "w21apply.w17.recipient.order"
RNG_CREW_SELECT: Final[str] = "w21apply.crew.select"
#: 〔1.1.0・検収 L4〕1 人の提供者を使ってよい回数の上限(超えたら止まる=黙って同じ日課を増やさない・expedient)。
DONOR_MAX_REUSE: Final[int] = 3
#: 〔1.1.0・検収 M2〕機能定員まで乗務員(種別 8)にする W21 の担当の語(W16 の乗務員の同じ語の行を外す担当)。
CREW_ROLES: Final[tuple[str, ...]] = ("警察官", "消防士", "清掃作業員", "納品ドライバー", "駅員", "電車運転士", "車掌")
KIND_CREW: Final[int] = 8
PURPOSE_DUTY: Final[int] = 5
#: 乗務員の提供者の層の段(担当の語は外さない=居なければ止まる)。
CREW_DONOR_LEVELS: Final[tuple[tuple[str, ...], ...]] = (("role", "sex", "age"), ("role", "sex"), ("role",))
#: 〔1.1.0・検収 M3〕外の雇用主の組織の番号(閉じた表の外=W6 の組織の番号の外・``engine.rights.initial`` と同じ値=試験)。
OUTSIDE_EMPLOYER_ORG: Final[int] = (1 << 31) - 1
#: 外の雇用主の雇用の行を置く体の席の状態(勤め先のセルはあるが組織が無い=段 4 の席の外)。
OUTSIDE_EMPLOYER_SEATS: Final[tuple[str, ...]] = ("no_seat_overflow", "no_seat_industry")
OUTSIDE_EMPLOYER_SOURCE: Final[str] = "w21apply:外の雇用主(席の外=勤め先のセルはあるが組織が無い・閉じた表の外の番号)"

#: 段 10 の近似の宣言(つなぎの台帳の行と 1 対 1)。
W21APPLY_EXPEDIENTS: Final[tuple[str, ...]] = (
    "W17 の週次表の W21 の人の行=外す W16 の体(種別 0・2・3)から提供者を 1 人選んで 7 日の行を写す(層=種別・勤め先のセルの有無・駅の口の有無・授業の有無・男女・年齢 5 歳・層に居なければ年齢 → 男女 → 授業 → 駅の口 → 勤め先の順に外す・層の中は Philox の並べ替えで使っていない提供者から・足りなければ繰り返す・1 人の提供者は 3 回まで=超えたら止まる)・自宅と職場の行のセルは受け手の家と勤め先・学校の行のセルは提供者のまま(W21 に学校のセルが無い)=W17 は凍結(CA1)・W21 の日課は判断モデルとカレンダー 1b〜3 の段で本人の判断に移す(親の判断=仮採用)",
    "W21 の人の種別=W21b の w16_kind(住民 3・区内で働く住民 2・外から来て働く人 0)・目的=勤務(種別 0)か居住・方面の節点=W12 の外の口の番号(駅の口の語の並び)・機能定員の外の W21 の担当の体(警察官・消防士ほか)は種別 0・2 のまま通勤者の日課(定員先取りに入らない=engine の先取りは種別 0・2 の体を除く)",
    "W16 の残す群=来街者・定期来街者・訪日来街者・通学者・指令・バス運転士・タクシー運転手・夜間清掃員・救急隊員・路上の役割 9 語(W21 に体が無い=来街者は判断モデルの後・運輸は W6 に会社が無い)・外す群=住民・区内で働く住民・外から来て働く人・議員・警察官・消防士・清掃作業員・納品ドライバー・駅員・電車運転士・車掌(親の判断 仮-33 (1)・(10)・検収 M1)",
    "通学者(W16 の種別 5・33,385 行・複製 16,695 を含む)は W16 のまま残す(W21 に外から来る通学者の体が無い=段 7 は層の表だけ=W21 に通学者の体が入る段で外す・検収 M1)",
    "権利台帳の初期の行=雇用(体 → 組織)は母集団の org_id(W21 の org_index)から今の口で・店の担当(体 → 店)は W21c の 9,833 行(担当のいる 284 店)・担当のいない店は今の丸振り(出どころの語を分ける)・住まい(世帯主 → 住まい=所有と賃借)は W21b の行・店の賃借(店 → 区画)は今の口・店の持ち主(組織 → 店=閉じた表の外)は入れない(PENDING §1-1 の判断の後)",
    "W16 の見出しの近似の宣言と段の版の表は W16 1.0.0 のまま(残す行の作り方)・差し替えの宣言は本表(W21apply)・W16 の見出しの門は差し替えの門に置き換え(W16 1.0.0 の門は notes に残す)",
    "W20cal(暦 1a の影)の週の表=残す W16 の体は W16 の口(attributes_from_columns+ペルソナの在庫)・W21 の体は W21 の口(attributes_from_w21+employment_from_w21)で、同じ calendar_from_attributes と同じ params(param_hash 不変)で組む・見出しは ALL_STAGES の外のまま(build_hash に入れない=親の判断)",
    "W21 の担当の体の機能定員=外す W16 の乗務員の同じ担当の語の数(警察官 140・消防士 45・清掃作業員 12・納品ドライバー 10・駅員 300・電車運転士 60・車掌 40)を上限に W21 に居る数まで・選ぶ順は人ごとの Philox・選んだ体は種別 8(乗務員)・目的=職務・日課の提供者は外す W16 の乗務員の同じ担当の語から(層=担当の語・男女・年齢 5 歳・担当の語は外さない=居なければ止まる)・定員は W16 の v1 の在庫の数(実の要員規模は未取得=検収 M2・親の判断)",
    "外の雇用主=勤め先のセルはあるが組織の無い W21 の体(段 4 の席の外=席の超過と席の無い業種)に、権利台帳の雇用の行を体 → 組織の番号 2^31−1(閉じた表の外の番号=外の雇用主)で 1 行・給料日の賃金は外界から(登録済みの faucet「域外雇用主の賃金」)・額は W21 の月の賃金=雇用主が権利台帳の中身で埋まるまでのつなぎ(検収 M3・親の判断=仮採用)",
)


class UnknownW16GroupError(ValueError):
    """W16 の在庫の群(種別, 担当の語)が :data:`W16_GROUP_ACTION` に無い(黙って残さない・外さない)。"""


class ProtectedOutputErrorApply(ValueError):
    """``--out`` が本体の v2・読む世界資産の中・差し替えの資産の置き場の外を指している(何も書かずに止める)。"""


def check_out_apply(data: Path, out: Path, world: Path) -> None:
    """出力先の検査: 本体の ``data/world/v2``・``--world`` の中なら止める。``data/world`` の下なら置き場の名が
    :data:`SWAP_ASSET` か ``SWAP_ASSET`` で始まる名(2 回目の組み立ての置き場)だけを許す。"""
    o = Path(out).resolve()
    for root in ((Path(data) / "world" / "v2").resolve(), Path(world).resolve()):
        if o == root or root in o.parents:
            raise ProtectedOutputErrorApply(f"段 10 は本体の v2・読む世界資産の中に書かない: {o.name}")
    wroot = (Path(data) / "world").resolve()
    if wroot in o.parents:
        top = o.relative_to(wroot).parts[0]
        if not top.startswith(SWAP_ASSET):
            raise ProtectedOutputErrorApply(f"段 10 は {SWAP_ASSET} の置き場の外の資産に書かない: {top}")


# ============================================================================== W16 の群
def _s(x: Any) -> np.ndarray:
    a = np.asarray(x, dtype=object)
    return np.where(np.equal(a, None), "", a).astype(str).astype(object)


def w16_actions(kind: Any, duty: Any) -> tuple[np.ndarray, dict[str, Any]]:
    """W16 の行ごとの扱い(``True``=残す)と群の表(種別|担当 → 行の数・扱い)。知らない群は止める。"""
    k = np.asarray(kind, dtype=np.int64)
    d = _s(duty)
    key = np.char.add(np.char.add(k.astype(str), "|"), d.astype(str))
    uk, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
    acts: list[str] = []
    table: dict[str, Any] = {}
    for word, c in zip(uk.tolist(), cnt.tolist()):  # 逐次: 群の数(≤ 40)
        ks, ds = word.split("|", 1)
        act = W16_GROUP_ACTION.get((int(ks), ds))
        if act is None:
            raise UnknownW16GroupError(f"W16 の群が扱いの表に無い: 種別 {ks}・担当 {ds!r}({c} 行)")
        acts.append(act)
        table[word] = {"rows": int(c), "action": act}
    keep = np.asarray([a == "keep" for a in acts], dtype=bool)[np.asarray(inv).reshape(-1)] if uk.size else \
        np.zeros(0, dtype=bool)
    return keep, table


# ============================================================================== W21 の人 → W16 の列
def _entry_index(entry: np.ndarray, node_ids: list[str]) -> np.ndarray:
    pos = {nid: i for i, nid in enumerate(node_ids)}
    u, inv = np.unique(entry.astype(str), return_inverse=True)
    unknown = [x for x in u.tolist() if x and x not in pos]
    if unknown:
        raise KeyError(f"W21 の駅の口の語が W12 の外の口に無い: {unknown}")
    lut = np.asarray([pos.get(x, -1) for x in u.tolist()], dtype=np.int64)  # 逐次: 語の種類(≤ 10)
    return lut[np.asarray(inv).reshape(-1)] if entry.size else np.zeros(0, dtype=np.int64)


def w21_population_columns(people: Mapping[str, Any], persons: Mapping[str, Any], money: Mapping[str, Any],
                           node_ids: list[str], base: int) -> dict[str, np.ndarray]:
    """W21 の人の表(``w21_people``・段 1〜3 の ``w21_persons``・段 5 の ``w21_money``)→ W16 の母集団の列(:data:`POPULATION_COLUMNS`
    の並び・``agent_id = base + person_id``)。知らない種別・人の番号の欠け・重なりは止める。"""
    pid = np.asarray(people["person_id"], dtype=np.int64)
    n = int(pid.size)
    if n and not np.array_equal(np.sort(pid), np.arange(n)):
        raise ValueError("W21 の person_id が 0..n−1 の並びでない(番号の対応表が全単射にならない)")
    kind = np.asarray(people["w16_kind"], dtype=np.int64)
    bad = sorted(set(np.unique(kind).tolist()) - {0, 2, 3})
    if bad:
        raise ValueError(f"W21 の人の w16_kind が 0・2・3 の外: {bad}")
    pos = np.full(n, -1, dtype=np.int64)
    pos[pid] = np.arange(n)
    # 段 1〜3 の住民の列(外国籍・家の建物)
    rp = np.asarray(persons["person_id"], dtype=np.int64)
    fo = np.zeros(n, dtype=bool)
    fo[pos[rp]] = np.asarray(persons["is_foreign"], dtype=bool)
    hb = np.full(n, -1, dtype=np.int64)
    hb[pos[rp]] = np.asarray(persons["home_building"], dtype=np.int64)
    mp = np.asarray(money["person_id"], dtype=np.int64)
    wage = np.full(n, -1, dtype=np.int64)
    wage[pos[mp]] = np.asarray(money["wage_monthly"], dtype=np.int64)
    occ_word = WP._map(_s(people["occupation_major"]), WP.OCC_OF_MAJOR, "").astype(object)
    emp_word = WP._map(_s(people["employment_status"]), dict(A.W16_EMPLOYMENT_OF), "非就業").astype(object)
    emp_word = np.where(emp_word == "非就業", "", emp_word).astype(object)
    age = np.asarray(people["age"], dtype=np.int64)
    if (age < 0).any() or (age > 255).any():
        raise ValueError("W21 の年齢が 0〜255 の外")
    return {
        "agent_id": (base + pid).astype(np.int64), "kind": kind,
        "purpose": np.where(kind == 0, PURPOSE_WORK, PURPOSE_RESIDE).astype(np.int64), "age": age,
        "sex": np.asarray(people["sex"], dtype=np.int64),
        "home_cell": np.asarray(people["home_cell"], dtype=np.int64),
        "work_cell": np.asarray(people["work_cell"], dtype=np.int64),
        "school_cell": np.full(n, -1, dtype=np.int64),
        "direction_node": _entry_index(_s(people["entry_node"]), node_ids),
        "chome_key": _s(people["home_chome_key"]), "household_id": np.asarray(people["household_id"], dtype=np.int64),
        "home_building": hb, "org_id": np.asarray(people["org_index"], dtype=np.int64),
        "industry_key": _s(people["industry_key"]), "duty_role": _s(people["duty_role"]),
        "pool_layer": np.full(n, -1, dtype=np.int64), "pool_index": np.full(n, -1, dtype=np.int64),
        "synthetic": np.zeros(n, dtype=bool), "is_foreign": fo,
        "w21_person_id": pid, "wage_monthly": wage, "persona_occupation": occ_word, "persona_employment": emp_word,
    }


def merge_population(w16: Mapping[str, Any], keep: np.ndarray, w21: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
    """W16 の残す行(``agent_id`` 不変)+W21 の行 → 母集団の列(``agent_id`` の昇順)。番号が重なれば止める。"""
    kept = {name: np.asarray(w16[name])[keep] for name, _t in POPULATION_COLUMNS[:19]}
    m = int(np.count_nonzero(keep))
    kept["w21_person_id"] = np.full(m, -1, dtype=np.int64)
    kept["wage_monthly"] = np.full(m, -1, dtype=np.int64)
    kept["persona_occupation"] = np.full(m, "", dtype=object)
    kept["persona_employment"] = np.full(m, "", dtype=object)
    out: dict[str, np.ndarray] = {}
    for name, _t in POPULATION_COLUMNS:
        a, b = np.asarray(kept[name]), np.asarray(w21[name])
        out[name] = np.concatenate([a.astype(object) if b.dtype == object or a.dtype == object else a,
                                    b.astype(object) if a.dtype == object or b.dtype == object else b])
    aid = np.asarray(out["agent_id"], dtype=np.int64)
    order = np.argsort(aid, kind="stable")
    out = {k: v[order] for k, v in out.items()}
    aid = aid[order]
    if aid.size and np.any(aid[1:] == aid[:-1]):
        raise ValueError("母集団の agent_id が重なる(W16 の残す行と W21 の行)")
    return out


# ============================================================================== W17 の提供者
def _u(seed: int | str, domain: str, ids: np.ndarray) -> np.ndarray:
    return unit_float(philox_array(seed, domain, k19_counter_array(np.asarray(ids, dtype=np.int64)), words=1))[:, 0]


def _age_band(age: np.ndarray) -> np.ndarray:
    return np.searchsorted(AGE_EDGES[1:], np.asarray(age, dtype=np.int64), side="right").astype(np.int64)


def _key(feat: Mapping[str, np.ndarray], names: tuple[str, ...]) -> np.ndarray:
    k = np.zeros(np.asarray(feat[names[0]]).size, dtype=np.int64)
    for nm in names:  # 逐次: 層の欄の数(≤ 6)
        k = k * 32 + np.asarray(feat[nm], dtype=np.int64)
    return k


def donor_schedules(w17: Mapping[str, np.ndarray], donors: Mapping[str, np.ndarray],
                    recipients: Mapping[str, np.ndarray], seed: int | str, *,
                    levels: tuple[tuple[str, ...], ...] = DONOR_LEVELS,
                    max_reuse: int = DONOR_MAX_REUSE) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray],
                                                               dict[str, Any]]:
    """W21 の人(受け手)に外す W16 の体(提供者)の 7 日の行を写す。

    Args:
        w17: W17 の週次表の列(``agent_id`` の昇順・:data:`W17_COLUMNS`)。
        donors: 提供者の欄 ``agent_id``・``kind``・``work``・``entry``・``school``(0/1)・``sex``・``age``。
        recipients: 受け手の欄(同じ欄+``new_id``(ランの番号)・``home_cell``・``work_cell``・``person_id``)。
        seed: 母集団の seed(並べ替えの鍵)。
        levels: 層の段(左から外して広げる・``age`` は 5 歳の階級に)。欄は ``donors``・``recipients`` に要る。
        max_reuse: 〔検収 L4〕1 人の提供者を使ってよい回数の上限(超えたら ``ValueError``=止まる)。

    Returns:
        (写した行の列, 受け手ごとの提供者の番号と層の段, 計器)。
    """
    d_id = np.asarray(donors["agent_id"], dtype=np.int64)
    nd = int(d_id.size)
    nr = int(np.asarray(recipients["new_id"]).size)
    if nd == 0 and nr:
        raise ValueError("提供者が居ない")
    names_all = sorted({n for lv in levels for n in lv})
    dfeat = {k: (_age_band(donors[k]) if k == "age" else np.asarray(donors[k], dtype=np.int64)) for k in names_all}
    rfeat = {k: (_age_band(recipients[k]) if k == "age" else np.asarray(recipients[k], dtype=np.int64))
             for k in names_all}
    ud = _u(seed, RNG_DONOR_ORDER, d_id)
    ur = _u(seed, RNG_RECIPIENT_ORDER, np.asarray(recipients["person_id"], dtype=np.int64))
    used = np.zeros(nd, dtype=np.int64)
    chosen = np.full(nr, -1, dtype=np.int64)
    level = np.full(nr, -1, dtype=np.int64)
    for lv, names in enumerate(levels):  # 逐次: 層の段の数(≤ 6)
        todo = np.flatnonzero(chosen < 0)
        if todo.size == 0:
            break
        kd = _key(dfeat, names)
        kr = _key(rfeat, names)[todo]
        common = np.intersect1d(np.unique(kr), np.unique(kd))
        for key in common.tolist():  # 逐次: 層の数ぶん(体の数に比例しない)
            rr = todo[kr == key]
            rr = rr[np.argsort(ur[rr], kind="stable")]
            dd = np.flatnonzero(kd == key)
            pos = 0
            while pos < rr.size:  # 逐次: 使い回しの回の数(≤ max_reuse)
                dd = dd[used[dd] < int(max_reuse)]  # 〔検収 L4〕上限に達した提供者は使わない(次の段へ)
                if dd.size == 0:
                    break
                dd = dd[np.lexsort((ud[dd], used[dd]))]  # 使った回数の少ない提供者から・同じなら Philox の順
                take = min(int(dd.size), int(rr.size - pos))
                pick = dd[:take]
                chosen[rr[pos:pos + take]] = pick
                level[rr[pos:pos + take]] = lv
                used[pick] += 1
                pos += take
    if (chosen < 0).any():
        raise ValueError(f"提供者の決まらない受け手 {int((chosen < 0).sum())} 人(層の最後の段の提供者が居ない)")
    if used.size and int(used.max()) > int(max_reuse):
        raise ValueError(f"1 人の提供者の使い回しが上限 {max_reuse} 回を超える(最大 {int(used.max())} 回)")
    # ---- 行を写す(提供者の 7 日の行=W17 は agent_id の昇順)----
    aid = np.asarray(w17["agent_id"], dtype=np.int64)
    if aid.size and np.any(aid[1:] < aid[:-1]):
        raise ValueError("W17 の週次表が agent_id の昇順でない")
    did = d_id[chosen]
    lo = np.searchsorted(aid, did, side="left")
    hi = np.searchsorted(aid, did, side="right")
    cnt = hi - lo
    if (cnt == 0).any():
        raise ValueError("W17 に行の無い提供者がいる")
    tot = int(cnt.sum())
    idx = np.repeat(lo, cnt) + (np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt))
    owner = np.repeat(np.arange(nr), cnt)
    rows = {name: np.asarray(w17[name])[idx].copy() for name, _t in W17_COLUMNS}
    rows["agent_id"] = np.asarray(recipients["new_id"], dtype=np.int64)[owner]
    pk = np.asarray(rows["place_kind"], dtype=np.int64)
    cell = np.asarray(rows["target_cell"], dtype=np.int64)
    home = np.asarray(recipients["home_cell"], dtype=np.int64)[owner]
    work = np.asarray(recipients["work_cell"], dtype=np.int64)[owner]
    cell = np.where(pk == PLACE_HOME, home, cell)
    work_rows = pk == PLACE_WORK
    work_blank = work_rows & (work < 0)
    cell = np.where(work_rows, work, cell)
    rows["target_cell"] = cell
    school_rows = pk == PLACE_SCHOOL
    r_school = np.asarray(recipients["school"], dtype=np.int64)[owner] > 0
    reuse = np.bincount(chosen, minlength=nd)
    info = {
        "recipients": nr, "donors": nd, "rows": tot,
        "level_counts": {"+".join(levels[k]): int((level == k).sum()) for k in range(len(levels))},
        "max_reuse_limit": int(max_reuse),
        "donors_used": int((reuse > 0).sum()), "donors_used_twice_or_more": int((reuse > 1).sum()),
        "max_reuse": int(reuse.max()) if reuse.size else 0,
        "recipients_with_reused_donor": int((reuse[chosen] > 1).sum()),
        "work_rows_without_work_cell": int(work_blank.sum()),
        "school_rows_kept_donor_cell": int((school_rows & r_school).sum()),
        "school_rows_of_recipients_without_school": int((school_rows & ~r_school).sum()),
        "home_rows": int((pk == PLACE_HOME).sum()), "work_rows": int(work_rows.sum()),
        "school_rows": int(school_rows.sum()),
    }
    return rows, {"donor_agent_id": did, "level": level}, info


def select_crews(person_id: Any, duty: Any, quota: Mapping[str, int], seed: int | str) -> np.ndarray:
    """〔検収 M2〕W21 の担当の体のうち機能定員(``quota``=担当の語 → 数)まで選ぶ(人ごとの Philox の順で先頭から)。
    返り値は選んだ体の印(bool)。逐次ループ宣言: 担当の語の数(≤ 7)。"""
    pid = np.asarray(person_id, dtype=np.int64)
    d = _s(duty)
    u = _u(seed, RNG_CREW_SELECT, pid)
    out = np.zeros(pid.size, dtype=bool)
    for role, q in quota.items():  # 逐次: 担当の語の数
        idx = np.flatnonzero(d == role)
        if idx.size == 0 or int(q) <= 0:
            continue
        idx = idx[np.argsort(u[idx], kind="stable")]
        out[idx[: int(q)]] = True
    return out


# ============================================================================== 権利台帳
def rights_run_rows(staff: Mapping[str, Any], rights_b: Mapping[str, Any], base: int,
                    outside_employer: Any = None) -> dict[str, np.ndarray]:
    """engine の ``rights.initial`` が読む行(体の番号=ランの ``agent_id``): 店の担当(W21c の体 → 店)と住まい(W21b の
    世帯主 → 住まい=所有と賃借)と〔1.1.0・検収 M3〕外の雇用主(``outside_employer``=人の番号の並び → 組織の番号
    :data:`OUTSIDE_EMPLOYER_ORG`)。店の持ち主(閉じた表の外)と雇用(体 → 組織=母集団の org_id から engine が作る)と店の賃借
    (engine が POI から作る)は入れない。"""
    blocks = []
    hk = _s(staff["holder_kind"])
    ok_ = _s(staff["object_kind"])
    kd = _s(staff["kind"])
    if not (np.all(hk == "agent") and np.all(ok_ == "store") and np.all(kd == "employ")):
        raise ValueError("W21c の店の担当の行が 体 → 店 の雇用でない")
    blocks.append(("store_staff", np.asarray(staff["holder_id"], dtype=np.int64), ok_, np.asarray(staff["object_id"],
                                                                                                  dtype=np.int64),
                   kd, _s(staff["source"])))
    bhk = _s(rights_b["holder_kind"])
    bok = _s(rights_b["object_kind"])
    sel = (bhk == "agent") & (bok == "dwelling")
    bkd = _s(rights_b["kind"])[sel]
    if not np.all(np.isin(bkd, ["own", "lease"])):
        raise ValueError("W21b の住まいの行の種類が所有・賃借の外")
    blocks.append(("dwelling", np.asarray(rights_b["holder_id"], dtype=np.int64)[sel], bok[sel],
                   np.asarray(rights_b["object_id"], dtype=np.int64)[sel], bkd, _s(rights_b["source"])[sel]))
    if outside_employer is not None:
        oe = np.asarray(outside_employer, dtype=np.int64)
        blocks.append(("outside_employer", oe, np.full(oe.size, "org", dtype=object),
                       np.full(oe.size, OUTSIDE_EMPLOYER_ORG, dtype=np.int64), np.full(oe.size, "employ", dtype=object),
                       np.full(oe.size, OUTSIDE_EMPLOYER_SOURCE, dtype=object)))
    out: dict[str, list[np.ndarray]] = {k: [] for k in ("holder_agent_id", "object_kind", "object_id", "kind", "source",
                                                        "block", "holder_person_id")}
    for name, hid, okd, oid, kdd, src in blocks:  # 逐次: 塊の数(≤ 3)
        out["holder_agent_id"].append(base + hid)
        out["holder_person_id"].append(hid)
        out["object_kind"].append(okd)
        out["object_id"].append(oid)
        out["kind"].append(kdd)
        out["source"].append(src)
        out["block"].append(np.full(hid.size, name, dtype=object))
    return {k: np.concatenate(v) for k, v in out.items()}


# ============================================================================== 組み立て
def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


#: pyarrow の型の名 → numpy の型(pandas を使わない)。
_NP_OF: Final[Mapping[str, Any]] = MappingProxyType({
    "int8": np.int8, "int16": np.int16, "int32": np.int32, "int64": np.int64, "uint8": np.uint8, "bool": np.bool_,
    "float": np.float32, "double": np.float64,
})


def _table(columns: Mapping[str, Any], spec: tuple[tuple[str, pa.DataType], ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, typ in spec:
        v = columns[name]
        if pa.types.is_string(typ):
            out[name] = pa.array(np.asarray(v, dtype=object).astype(str).tolist(), type=typ)
        else:
            out[name] = pa.array(np.asarray(v).astype(_NP_OF[str(typ)]), type=typ)
    return out


def _read(guard: S.W21Guard, path: Path, columns: tuple[str, ...] | None = None) -> dict[str, np.ndarray]:
    """守りを通して表を読む(md5 を記録)→ 列 → 配列(語の列は object の配列・None は空欄)。"""
    guard.md5_only(path)
    t = pq.read_table(path, columns=list(columns) if columns else None)
    out: dict[str, np.ndarray] = {}
    for name in t.schema.names:  # 逐次: 列の数
        col = t.column(name)
        if pa.types.is_string(col.type) or pa.types.is_large_string(col.type):
            out[name] = _s(col.to_pylist())
        elif pa.types.is_integer(col.type) or pa.types.is_floating(col.type) or pa.types.is_boolean(col.type):
            out[name] = col.to_numpy(zero_copy_only=False)
        else:
            out[name] = np.asarray(col.to_pylist(), dtype=object)
    return out


def _verify_manifest(guard: S.W21Guard, out: Path, man_name: str, files: tuple[str, ...]) -> dict[str, Any]:
    man = json.loads(guard.read_bytes(out / man_name).decode("utf-8"))
    want = {o["path"]: o["sha256"] for o in man["outputs"]}
    for f in files:  # 逐次: ファイルの数
        if want.get(f) != _sha(guard.read_bytes(out / f)):
            raise S.MissingSourceError(f"W21 の資産の sha256 が manifest と違う: {f}")
    return man


def apply(data: Path, out: Path, *, world: Path | None = None, seed: int | str = W.DEFAULT_SEED
          ) -> tuple[C.StageResult, dict[str, Any]]:
    """段 10 の差し替えを ``out`` に組む。返り値は(見出し, manifest)。"""
    data, out = Path(data), Path(out)
    world = W.source_world(data, world)  # 差し替えた世界からは組まない=退避の W16 の世界(元の W16・W17)
    check_out_apply(data, out, world)
    t0 = time.perf_counter()
    guard = S.W21Guard.for_build(data, world=world, out=out)
    with guard.active():
        man_a = _verify_manifest(guard, out, W.MANIFEST_NAME, ("w21_persons.parquet", "w21_households.parquet"))
        man_b = _verify_manifest(guard, out, WB.MANIFEST_B, ("w21_people.parquet", "w21_rights_initial.parquet",
                                                             "w21_money.parquet"))
        man_c = _verify_manifest(guard, out, WCB.MANIFEST_C, ("w21c_rights_store_staff.parquet",
                                                              "w21_persona_short.parquet", "w21_persona_long.parquet"))
        if man_b.get("stage_version") != WB.STAGE_VERSION_B or man_c.get("stage_version") != WCB.STAGE_VERSION_C:
            raise S.MissingSourceError(f"W21b・W21c の版が今のコードと違う({man_b.get('stage_version')}・"
                                       f"{man_c.get('stage_version')})=段 4〜10 を組み直す")
        people = _read(guard, out / "w21_people.parquet")
        persons = _read(guard, out / "w21_persons.parquet", ("person_id", "is_foreign", "home_building", "school_kind"))
        households = _read(guard, out / "w21_households.parquet",
                           ("household_id", "chome_key", "home_cell", "home_building", "size"))
        money = _read(guard, out / "w21_money.parquet", ("person_id", "wage_monthly"))
        rights_b = _read(guard, out / "w21_rights_initial.parquet")
        staff = _read(guard, out / "w21c_rights_store_staff.parquet")
        w16 = _read(guard, world / "w16_population.parquet")
        roster = _read(guard, world / "w16_duty_roster.parquet")
        w17 = _read(guard, world / "w17_schedule.parquet")
        ext = guard.read_parquet(world / "w12_external_nodes.parquet", ["node_id"])
        h16 = json.loads(guard.read_bytes(world / "W16.header.json").decode("utf-8"))
        h17 = json.loads(guard.read_bytes(world / "W17.header.json").decode("utf-8"))
        cohorts16 = json.loads(guard.read_bytes(world / "w16_cohorts.json").decode("utf-8"))
        gates16 = json.loads(guard.read_bytes(world / "w16_gates.json").decode("utf-8"))
    node_ids = [str(x) for x in ext["node_id"]]

    # ---- W16 の群の扱い ----
    keep, groups = w16_actions(w16["kind"], w16["duty_role"])
    base = int(np.asarray(w16["agent_id"], dtype=np.int64).max()) + 1
    w21 = w21_population_columns(people, persons, money, node_ids, base)
    # ---- 〔1.1.0・検収 M2〕担当の体の機能定員=外す W16 の乗務員の同じ語の数(W21 に居る数が上限)まで種別 8・目的=職務 ----
    k16 = np.asarray(w16["kind"], dtype=np.int64)
    d16 = _s(w16["duty_role"])
    crew_w16 = ~keep & (k16 == KIND_CREW) & np.isin(d16, list(CREW_ROLES))
    quota = {r: min(int((crew_w16 & (d16 == r)).sum()), int((w21["duty_role"] == r).sum())) for r in CREW_ROLES}
    crew = select_crews(w21["w21_person_id"], w21["duty_role"], quota, seed)
    w21["kind"] = np.where(crew, KIND_CREW, w21["kind"]).astype(np.int64)
    w21["purpose"] = np.where(crew, PURPOSE_DUTY, w21["purpose"]).astype(np.int64)
    pop = merge_population(w16, keep, w21)

    # ---- W17: 残す行+提供者の行 ----
    aid16 = np.asarray(w16["agent_id"], dtype=np.int64)
    w17_aid = np.asarray(w17["agent_id"], dtype=np.int64)
    keep_ids = aid16[keep]
    keep_rows = np.isin(w17_aid, keep_ids)
    dmask = ~keep & np.isin(np.asarray(w16["kind"], dtype=np.int64), [0, 2, 3])
    donors = {"agent_id": aid16[dmask], "kind": np.asarray(w16["kind"], dtype=np.int64)[dmask],
              "work": (np.asarray(w16["work_cell"], dtype=np.int64)[dmask] >= 0).astype(np.int64),
              "entry": (np.asarray(w16["direction_node"], dtype=np.int64)[dmask] >= 0).astype(np.int64),
              "school": (np.asarray(w16["school_cell"], dtype=np.int64)[dmask] >= 0).astype(np.int64),
              "sex": np.asarray(w16["sex"], dtype=np.int64)[dmask], "age": np.asarray(w16["age"], dtype=np.int64)[dmask]}
    school_kind = np.full(int(np.asarray(people["person_id"]).size), "", dtype=object)
    pos = np.asarray(people["person_id"], dtype=np.int64)
    school_kind[np.searchsorted(pos, np.asarray(persons["person_id"], dtype=np.int64))] = _s(persons["school_kind"])
    attrs21 = WP.attributes_from_w21({**{c: people[c] for c in WP.W21_INPUT_COLUMNS if c in people},
                                      "school_kind": school_kind})
    import dataclasses

    attrs21 = dataclasses.replace(attrs21, kind=np.asarray(w21["kind"], dtype=np.int64))  # 種別 8 の体を W20 へも
    recipients = {"new_id": w21["agent_id"], "person_id": w21["w21_person_id"], "kind": w21["kind"],
                  "work": (w21["work_cell"] >= 0).astype(np.int64), "entry": (w21["direction_node"] >= 0).astype(np.int64),
                  "school": np.asarray(attrs21.school, dtype=np.int64), "sex": w21["sex"], "age": w21["age"],
                  "home_cell": w21["home_cell"], "work_cell": w21["work_cell"]}
    w17_in = {name: np.asarray(w17[name]) for name, _t in W17_COLUMNS}
    nc = ~crew
    rec_nc = {k: np.asarray(v)[nc] for k, v in recipients.items()}
    rows_nc, of_nc, donor_info = donor_schedules(w17_in, donors, rec_nc, seed)
    # 〔検収 M2〕機能定員の乗務員=外す W16 の乗務員の同じ担当の語から(交代勤務の日課・居なければ止まる)
    role_code = {r: i for i, r in enumerate(CREW_ROLES)}
    cdon = {"agent_id": aid16[crew_w16], "role": np.array([role_code[r] for r in d16[crew_w16].tolist()], dtype=np.int64),
            "sex": np.asarray(w16["sex"], dtype=np.int64)[crew_w16],
            "age": np.asarray(w16["age"], dtype=np.int64)[crew_w16]}
    rec_c = {k: np.asarray(v)[crew] for k, v in recipients.items()}
    rec_c["role"] = np.array([role_code[r] for r in w21["duty_role"][crew].tolist()], dtype=np.int64)
    # 乗務員は使い回さない(機能定員 ≤ 外す W16 の乗務員の数=提供者が足りる)
    rows_c, of_c, crew_info = donor_schedules(w17_in, cdon, rec_c, seed, levels=CREW_DONOR_LEVELS, max_reuse=1)
    rows_new = {name: np.concatenate([np.asarray(rows_nc[name]), np.asarray(rows_c[name])]) for name, _t in W17_COLUMNS}
    donor_of = {"donor_agent_id": np.zeros(crew.size, dtype=np.int64), "level": np.zeros(crew.size, dtype=np.int64)}
    for k in donor_of:  # 逐次: 欄の数(2)
        donor_of[k][nc] = of_nc[k]
        donor_of[k][crew] = of_c[k]
    donor_info = {**donor_info, "crew": crew_info}
    w17_out = {name: np.concatenate([np.asarray(w17_in[name])[keep_rows], np.asarray(rows_new[name])])
               for name, _t in W17_COLUMNS}
    order = np.lexsort((np.asarray(w17_out["seq"], dtype=np.int64), np.asarray(w17_out["day"], dtype=np.int64),
                        np.asarray(w17_out["agent_id"], dtype=np.int64)))
    w17_out = {k: v[order] for k, v in w17_out.items()}

    # ---- 番号の対応表・権利台帳・世帯・担当の名簿 ----
    n_keep = int(keep.sum())
    n21 = int(w21["agent_id"].size)
    amap = {
        "agent_id": np.r_[keep_ids, w21["agent_id"]],
        "source": np.r_[np.full(n_keep, "w16", dtype=object), np.full(n21, "w21", dtype=object)],
        "w16_agent_id": np.r_[keep_ids, np.full(n21, -1, dtype=np.int64)],
        "w21_person_id": np.r_[np.full(n_keep, -1, dtype=np.int64), w21["w21_person_id"]],
        "w17_donor_agent_id": np.r_[np.full(n_keep, -1, dtype=np.int64), donor_of["donor_agent_id"]],
        "w17_donor_level": np.r_[np.full(n_keep, -1, dtype=np.int64), donor_of["level"]],
    }
    mo = np.argsort(amap["agent_id"], kind="stable")
    amap = {k: v[mo] for k, v in amap.items()}
    seat = _s(people["seat_status"])
    oe_pid = np.asarray(people["person_id"], dtype=np.int64)[np.isin(seat, list(OUTSIDE_EMPLOYER_SEATS))]
    rights = rights_run_rows(staff, rights_b, base, outside_employer=oe_pid)
    hh = {k: np.asarray(households[k]) for k in ("household_id", "chome_key", "home_cell", "home_building", "size")}
    r_aid = np.asarray(roster["agent_id"], dtype=np.int64)
    r_keep = np.isin(r_aid, keep_ids)
    duty21 = w21["duty_role"] != ""
    roster_out = {
        "agent_id": np.r_[r_aid[r_keep], w21["agent_id"][duty21]],
        "kind": np.r_[np.asarray(roster["kind"], dtype=np.int64)[r_keep], w21["kind"][duty21]],
        "role": np.r_[_s(roster["role"])[r_keep], w21["duty_role"][duty21]],
        "post": np.r_[_s(roster["post"])[r_keep], np.full(int(duty21.sum()), "", dtype=object)],
        "age": np.r_[np.asarray(roster["age"], dtype=np.int64)[r_keep], w21["age"][duty21]],
        "sex": np.r_[np.asarray(roster["sex"], dtype=np.int64)[r_keep], w21["sex"][duty21]],
        "work_cell": np.r_[np.asarray(roster["work_cell"], dtype=np.int64)[r_keep], w21["work_cell"][duty21]],
        "direction_node": np.r_[np.asarray(roster["direction_node"], dtype=np.int64)[r_keep],
                                w21["direction_node"][duty21]],
    }

    # ---- W20cal(暦 1a の影)----
    cal = _calendar(data, world, w16, keep, attrs21, _s(people["emp_status"]), w21["agent_id"])

    # ---- 計器と門 ----
    kind_all = np.asarray(pop["kind"], dtype=np.int64)
    w16_kept_same = all(np.array_equal(np.asarray(pop[name])[: n_keep], np.asarray(w16[name])[keep])
                        for name, _t in POPULATION_COLUMNS[:19])
    cohorts = _cohorts(cohorts16, groups, w21, man_a, man_b)
    sched_agents = np.unique(np.asarray(w17_out["agent_id"], dtype=np.int64))
    days_ok = _days_per_agent(w17_out)
    checks = {
        "schema": "w21apply.checks/1",
        "note": "段 10 の差し替えの計器(合否は付けない=門は見出し)。人の行は写さない(数だけ)",
        "w16_groups": groups,
        "counts": {"w16_rows": int(aid16.size), "w16_kept": n_keep, "w16_removed": int((~keep).sum()),
                   "w21_added": n21, "population": int(kind_all.size), "base_agent_id": base,
                   "by_kind": {str(k): int(v) for k, v in zip(*np.unique(kind_all, return_counts=True))},
                   "duty_roles": {str(k): int(v) for k, v in zip(*np.unique(np.asarray(pop["duty_role"], dtype=object)
                                                                          .astype(str), return_counts=True)) if k}},
        "w17": {"rows_before": int(w17_aid.size), "rows_kept": int(keep_rows.sum()), "rows_added": int(rows_new["agent_id"].size),
                "rows_after": int(np.asarray(w17_out["agent_id"]).size), "donor": donor_info},
        "rights": {"rows": int(rights["holder_agent_id"].size),
                   "by_block": {str(k): int(v) for k, v in zip(*np.unique(rights["block"].astype(str), return_counts=True))},
                   "stores_with_staff": int(np.unique(rights["object_id"][rights["block"] == "store_staff"]).size)},
        "calendar_1a": cal["notes"],
        "wage_given": int((np.asarray(pop["wage_monthly"]) >= 0).sum()),
        "crew": {"quota": quota, "selected": {r: int((crew & (w21["duty_role"] == r)).sum()) for r in CREW_ROLES},
                 "w21_duty_bodies": {r: int((w21["duty_role"] == r).sum()) for r in CREW_ROLES},
                 "w16_crew_rows_removed": {r: int((crew_w16 & (d16 == r)).sum()) for r in CREW_ROLES},
                 "kind8_w21": int(crew.sum())},
        "outside_employer": {"bodies": int(oe_pid.size), "by_seat": {st: int((seat == st).sum()) for st in
                                                                    OUTSIDE_EMPLOYER_SEATS},
                             "org_id": OUTSIDE_EMPLOYER_ORG},
    }
    gates = [
        C.Gate("population_rows", int(kind_all.size), n_keep + n21),
        C.Gate("agent_id_duplicates", int(kind_all.size - np.unique(np.asarray(pop["agent_id"])).size), 0),
        C.Gate("w16_kept_rows_unchanged", bool(w16_kept_same), True),
        C.Gate("agent_map_bijective", bool(np.array_equal(np.sort(amap["agent_id"]), np.asarray(pop["agent_id"])))
               and int(np.unique(amap["w21_person_id"][amap["w21_person_id"] >= 0]).size) == n21, True),
        C.Gate("w17_covers_population", bool(np.array_equal(sched_agents, np.asarray(pop["agent_id"], dtype=np.int64))),
               True),
        C.Gate("w17_days_per_agent_ge_1", int(days_ok), int(kind_all.size)),
        C.Gate("rights_holders_in_population", int(np.isin(rights["holder_agent_id"], pop["agent_id"]).sum()),
               int(rights["holder_agent_id"].size)),
        C.Gate("w20cal_param_hash_unchanged", cal["param_hash"], cal["param_hash_reference"]),
        C.Gate("w16_removed_rows", int((~keep).sum()), None),
        C.Gate("donor_max_reuse_le_limit", max(donor_info["max_reuse"], crew_info["max_reuse"]),
               passed=max(donor_info["max_reuse"], crew_info["max_reuse"]) <= DONOR_MAX_REUSE),
        C.Gate("crew_kind8_equals_quota", int(crew.sum()), int(sum(quota.values()))),
    ]

    # ---- 書く ----
    pop_tbl = _table(pop, POPULATION_COLUMNS)
    roster_spec = (("agent_id", pa.int32()), ("kind", pa.int8()), ("role", pa.string()), ("post", pa.string()),
                   ("age", pa.uint8()), ("sex", pa.int8()), ("work_cell", pa.int32()), ("direction_node", pa.int32()))
    hh_spec = (("household_id", pa.int32()), ("chome_key", pa.string()), ("home_cell", pa.int32()),
               ("home_building", pa.int32()), ("size", pa.int16()))
    map_spec = (("agent_id", pa.int32()), ("source", pa.string()), ("w16_agent_id", pa.int32()),
                ("w21_person_id", pa.int32()), ("w17_donor_agent_id", pa.int32()), ("w17_donor_level", pa.int8()))
    rights_spec = (("holder_agent_id", pa.int64()), ("holder_person_id", pa.int64()), ("object_kind", pa.string()),
                   ("object_id", pa.int64()), ("kind", pa.string()), ("source", pa.string()), ("block", pa.string()))
    gates16_new = {"schema": "w21apply.w16_gates/1", "w16_1_0_0": gates16,
                   "swap": {g.name: g.to_json() for g in gates}}
    outputs = [
        C.write_parquet(out, "w16_population.parquet", pop_tbl),
        C.write_parquet(out, "w16_households.parquet", _table(hh, hh_spec)),
        C.write_parquet(out, "w16_duty_roster.parquet", _table(roster_out, roster_spec)),
        C.write_json(out, "w16_gates.json", gates16_new),
        C.write_json(out, "w16_cohorts.json", cohorts, rows=len(cohorts["cohorts"])),
        C.write_parquet(out, "w17_schedule.parquet", _table(w17_out, W17_COLUMNS)),
        C.write_parquet(out, "w21_agent_map.parquet", _table(amap, map_spec)),
        C.write_parquet(out, "w21_rights_run.parquet", _table(rights, rights_spec)),
        C.write_parquet(out, W20.OUTPUT_NAME, cal["table"], schema=W20.TABLE_SCHEMA),
        C.write_json(out, W20.MATERIALS_NAME, cal["materials"]),
        C.write_json(out, "w21_apply_checks.json", checks),
    ]
    by = {o["path"]: o for o in outputs}
    build_hash = C.sha256_bytes("".join(o["sha256"] for o in outputs).encode("utf-8"))
    sources = {"w21_build_hash": man_a["w21_build_hash"], "w21b_build_hash": man_b["w21b_build_hash"],
               "w21c_build_hash": man_c["w21c_build_hash"], "w16_header_param_hash": h16["param_hash"],
               "w17_header_param_hash": h17["param_hash"]}
    params = {"seed": seed, "base_agent_id": base, "w16_group_action": {f"{k[0]}|{k[1]}": v for k, v in
                                                                         sorted(W16_GROUP_ACTION.items())},
              "donor_levels": ["+".join(x) for x in DONOR_LEVELS], "age_edges": AGE_EDGES.tolist(),
              "rng_domains": [RNG_DONOR_ORDER, RNG_RECIPIENT_ORDER, RNG_CREW_SELECT], "sources": sources,
              "donor_max_reuse": DONOR_MAX_REUSE, "crew_roles": list(CREW_ROLES), "crew_quota": quota,
              "crew_donor_levels": ["+".join(x) for x in CREW_DONOR_LEVELS],
              "outside_employer": {"org_id": OUTSIDE_EMPLOYER_ORG, "seats": list(OUTSIDE_EMPLOYER_SEATS)}}
    # ---- W16・W17 の見出し(段の版を上げる・出力の sha を今の出力に・近似の宣言と版の表は W16 1.0.0 のまま)----
    h16n = dict(h16)
    h16n["stage_version"] = "2.0.0"
    h16n["params"] = {**h16["params"], "w21_apply": params}
    h16n["param_hash"] = C.param_hash(h16n["params"])
    h16n["input_hash"] = C.sha256_bytes("\n".join([h16["input_hash"], *sources.values()]).encode("utf-8"))
    chome = next(o for o in h16["outputs"] if o["path"] == "w16_chome.parquet")
    h16n["outputs"] = [by["w16_population.parquet"], by["w16_households.parquet"], by["w16_duty_roster.parquet"],
                       chome, by["w16_gates.json"], by["w16_cohorts.json"]]
    h16n["gates"] = {g.name: g.to_json() for g in gates}
    h16n["notes"] = {"w16_1_0_0": h16["notes"], "w16_1_0_0_gates": h16["gates"],
                     "w21_apply": {"manifest": MANIFEST_APPLY, "w21_apply_build_hash": build_hash,
                                   "counts": checks["counts"]}}
    h17n = dict(h17)
    h17n["stage_version"] = "2.1.0"
    h17n["params"] = {**h17["params"], "w21_apply_donor": {"levels": params["donor_levels"],
                                                           "rng_domains": params["rng_domains"], "seed": seed}}
    h17n["param_hash"] = C.param_hash(h17n["params"])
    h17n["input_hash"] = C.sha256_bytes("\n".join([h17["input_hash"], by["w16_population.parquet"]["sha256"]])
                                        .encode("utf-8"))
    h17n["outputs"] = [by["w17_schedule.parquet"] if o["path"] == "w17_schedule.parquet" else o for o in h17["outputs"]]
    h17n["gates"] = {**h17["gates"], "w21_apply_w17_covers_population":
                     C.Gate("w21_apply_w17_covers_population", gates[4].value, True).to_json()}
    h17n["notes"] = {**h17["notes"], "w21_apply": {"donor": donor_info, "rows_kept": int(keep_rows.sum())}}
    (out / "W16.header.json").write_bytes(C.canonical_json_bytes(h16n) + b"\n")
    (out / "W17.header.json").write_bytes(C.canonical_json_bytes(h17n) + b"\n")
    (out / CALENDAR_HEADER).write_bytes(C.canonical_json_bytes(cal["header"](by)) + b"\n")
    manifest = {
        "schema": "w21apply.manifest/1", "stage": STAGE_APPLY, "stage_version": STAGE_VERSION_APPLY,
        "population_seed": seed, "params": params, "outputs": outputs, "w21_apply_build_hash": build_hash,
        "counts": checks["counts"], "expedients": list(W21APPLY_EXPEDIENTS),
        "headers_rewritten": ["W16.header.json", "W17.header.json", CALENDAR_HEADER],
    }
    C.write_json(out, MANIFEST_APPLY, manifest)
    res = C.StageResult(stage=STAGE_APPLY, stage_version=STAGE_VERSION_APPLY,
                        input_hash=C.sha256_bytes("\n".join(sources.values()).encode("utf-8")),
                        param_hash=C.param_hash(params), params=params, outputs=outputs,
                        catalog_classes=["人(母集団の差し替え)", "週次表(提供者の写し)", "権利台帳の初期の行"],
                        expedients=list(W21APPLY_EXPEDIENTS),
                        notes={"w21_apply_build_hash": build_hash, "counts": checks["counts"],
                               "seconds_nondeterministic": round(time.perf_counter() - t0, 1)})
    res.gates = gates
    header = res.to_json()
    header["notes"] = {k: v for k, v in header["notes"].items() if k != "seconds_nondeterministic"}
    (out / f"{STAGE_APPLY}.header.json").write_bytes(C.canonical_json_bytes(header) + b"\n")
    return res, manifest


def _days_per_agent(w17: Mapping[str, np.ndarray]) -> int:
    """週次表で 1 日以上の行を持つ体の数(全員=門)。"""
    return int(np.unique(np.asarray(w17["agent_id"], dtype=np.int64)).size)


def _cohorts(cohorts16: Mapping[str, Any], groups: Mapping[str, Any], w21: Mapping[str, np.ndarray],
             man_a: Mapping[str, Any], man_b: Mapping[str, Any]) -> dict[str, Any]:
    """群の表(W16 の残す群+W21 の層)。"""
    keep_rows = sum(v["rows"] for v in groups.values() if v["action"] == "keep")
    kind = np.asarray(w21["kind"], dtype=np.int64)
    rows = [{"cohort": "w16_kept", "n": int(keep_rows), "source": "W16 1.0.0 の残す群(来街者・指令・運輸・路上の役割ほか)",
             "groups": {k: v["rows"] for k, v in groups.items() if v["action"] == "keep"}},
            {"cohort": "resident", "n": int((kind == 3).sum()), "source": "W21(段 1〜3・国勢調査の小地域=住民)",
             "w21_build_hash": man_a["w21_build_hash"]},
            {"cohort": "resident_worker_in_area", "n": int((kind == 2).sum()), "source": "W21b(段 4・舞台で働く住民)",
             "w21b_build_hash": man_b["w21b_build_hash"]},
            {"cohort": "commuter", "n": int((kind == 0).sum()), "source": "W21b(段 4・外から来て働く人)",
             "w21b_build_hash": man_b["w21b_build_hash"]}]
    return {"schema": "w21apply.cohorts/1", "cohorts": rows, "n_total": int(keep_rows + kind.size),
            "w16_1_0_0": dict(cohorts16), "note": "段 10 の差し替え(W16 の残す群+W21)。人数は目標ではなく結果"}


def _calendar(data: Path, world: Path, w16: Mapping[str, Any], keep: np.ndarray, attrs21: Any, emp8: np.ndarray,
              agent21: np.ndarray) -> dict[str, Any]:
    """W20cal の週の表を新しい母集団で組む(残す W16 の体=W16 の口・W21 の体=W21 の口・同じ params)。"""
    guard = W20.R99Guard()
    ap = W20.TR.anchor_path()
    with guard.active():
        anchor = W20.TR.load_anchor(ap)
        mat_doc = W20.build_materials(data, anchor_path=ap, guard=guard)
        materials = W20.Materials(mat_doc)
        cols = {k: np.asarray(w16[k])[keep] for k in ("agent_id", "kind", "age", "home_cell", "work_cell", "school_cell",
                                                     "industry_key", "duty_role", "pool_layer", "pool_index")}
        cols_l = {k: (v.tolist()) for k, v in cols.items()}
        pool = W20.read_pool_fields(data.joinpath(*W20.PF_POOL_DIR), np.asarray(cols["pool_layer"]),
                                    np.asarray(cols["pool_index"]))
        a16 = W20.attributes_from_columns(cols_l, pool)
        e16 = W20.draw_employment_status(a16, materials, anchor)
        a21 = _with_agent_ids(attrs21, agent21)
        e21 = WP.employment_from_w21(a21, emp8, anchor)
        attrs = _concat_attrs(a16, a21)
        emp = _concat_emp(e16, e21)
        rules_path = Path(__file__).resolve().parents[4] / W20.RULES_TABLE_RELPATH
        rest_rule = W20.load_weekly_rest_rule(rules_path)
        built = W20.calendar_from_attributes(attrs, emp, materials, anchor, n_weeks=W20.N_WEEKS, rest_rule=rest_rule)
    tab = built["columns"]
    order = np.lexsort((tab["weekday"], tab["week"], tab["agent_id"]))
    tab = {k: np.asarray(v)[order] for k, v in tab.items()}
    params = W20.stage_params(W20.N_WEEKS, rest_rule)
    ref = _reference_param_hash(world, data)
    stats = W20.table_stats(tab)
    notes = {"stats": stats, "employment_counters_w16": e16.counters, "employment_counters_w21": e21.counters,
             "calendar_counters": built["counters"], "annual_check_t19": built["annual_check"],
             "status_bodies": {W20.STATUS_WORDS[s]: int((np.asarray(emp.status) == s).sum())
                               for s in range(len(W20.STATUS_WORDS))},
             "emp_row_bodies": {W20.EMP_ROWS[i]: int((np.asarray(emp.emp_row) == i).sum())
                                for i in range(len(W20.EMP_ROWS))},
             "bodies_w16": int(a16.n), "bodies_w21": int(a21.n), "r99_opened": sorted(guard.opened)}

    def header(by: Mapping[str, Any]) -> dict[str, Any]:
        res = C.StageResult(
            stage=W20.STAGE, stage_version=W20.STAGE_VERSION,
            input_hash=C.sha256_bytes("\n".join([by["w16_population.parquet"]["sha256"],
                                                 C.sha256_bytes(C.canonical_json_bytes(mat_doc))]).encode("utf-8")),
            param_hash=C.param_hash(params), params=params,
            outputs=[by[W20.OUTPUT_NAME], by[W20.MATERIALS_NAME]],
            gates=[C.Gate("validation_tables_opened",
                          len(set(guard.opened) & {x.lower() for x in W20.R99_VALIDATION_FILES}), 0),
                   C.Gate("rows_equal_bodies_x_days", int(tab["agent_id"].size), int(attrs.n * W20.N_WEEKS * W20.N_DAYS)),
                   C.Gate("work_days_per_week_mean", stats["work_days_per_week_mean"])],
            catalog_classes=["人(ペルソナ)", "約束(勤務・授業)"],
            expedients=list(W21APPLY_EXPEDIENTS),  # 段 10 の宣言(W20cal 1.0.0 の宣言はモジュール w20_calendar_1a のまま)
            notes={**notes, "w21_apply": True})
        return res.to_json()

    return {"table": tab, "materials": mat_doc, "param_hash": C.param_hash(params), "param_hash_reference": ref,
            "notes": notes, "header": header}


def _reference_param_hash(world: Path, data: Path) -> str:
    """W20cal 1.0.0 の見出し(``data/world/v2_stage_3-1``)の param_hash(無ければ今の params から=門は自明に通る)。"""
    p = Path(data) / "world" / "v2_stage_3-1" / W20.HEADER_NAME
    if p.exists():
        return str(json.loads(p.read_text(encoding="utf-8"))["param_hash"])
    return C.param_hash(W20.stage_params(W20.N_WEEKS, W20.load_weekly_rest_rule(
        Path(__file__).resolve().parents[4] / W20.RULES_TABLE_RELPATH)))


def _with_agent_ids(attrs: Any, agent_id: np.ndarray) -> Any:
    import dataclasses

    return dataclasses.replace(attrs, agent_id=np.asarray(agent_id, dtype=np.int64))


def _concat_attrs(a: Any, b: Any) -> Any:
    import dataclasses

    out = {}
    for f in dataclasses.fields(a):
        va, vb = getattr(a, f.name), getattr(b, f.name)
        if isinstance(va, list):
            out[f.name] = list(va) + list(vb)
        elif va is None or vb is None:
            na, nb = a.n, b.n
            va = np.zeros(na, dtype=bool) if va is None else va
            vb = np.zeros(nb, dtype=bool) if vb is None else vb
            out[f.name] = np.concatenate([np.asarray(va), np.asarray(vb)])
        else:
            out[f.name] = np.concatenate([np.asarray(va), np.asarray(vb)])
    return W20.Attributes(**out)


def _concat_emp(a: Any, b: Any) -> Any:
    ctr = {k: int(a.counters.get(k, 0)) + int(b.counters.get(k, 0)) for k in set(a.counters) | set(b.counters)}
    return W20.Employment(status=np.concatenate([a.status, b.status]), emp_row=np.concatenate([a.emp_row, b.emp_row]),
                          source=np.concatenate([np.asarray(a.source), np.asarray(b.source)]), counters=ctr)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.pop.w21_apply")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--world", type=Path, default=None, help="元の W16・W17 の世界資産(既定 <data>/world/v2・読むだけ)")
    ap.add_argument("--seed", type=int, default=W.DEFAULT_SEED)
    a = ap.parse_args(argv)
    data = a.data.resolve()
    world = W.source_world(data, a.world).resolve()  # 〔段 10〕差し替えた世界なら退避の W16 の世界
    try:
        check_out_apply(data, a.out.resolve(), world)
    except ProtectedOutputErrorApply as e:
        print(f"[W21apply] 止めた(何も書いていない): {e}", file=sys.stderr)
        return 2
    res, man = apply(data, a.out.resolve(), world=world, seed=a.seed)
    print(f"[W21apply] population={man['counts']['population']} w16_kept={man['counts']['w16_kept']} "
          f"w21_added={man['counts']['w21_added']} w21_apply_build_hash={man['w21_apply_build_hash']}")
    for g in res.gates:
        print(f"[W21apply] gate {g.name} = {g.to_json()}")
    return 0 if res.all_passed else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
