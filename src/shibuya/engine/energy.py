"""engine.energy — 体のエネルギー収支(5 段目 5a・D-118 K1〜K9・第291)。

正典
- ``docs/design/v2-energy-classical-implementation-agenda.md`` §1(段 5a の 1〜10・第291 の訂正)。
- 草案 ``docs/design/v2-hunger-choice-attention-draft.md`` §1-2・§1-2b(紙上計算と D-111 の予想表)・
  §1-3(照合と較正の分離 K6 (i))・§1-6(K1〜K9)。
- 錨 ``docs/bench/anchors/hunger_energy_anchors_v0.json``(追跡ファイル・
  ``tools/hunger/build_hunger_anchors.py`` が ``data/calib/hunger/`` から決定論で生成)。
  **エンジンは data/ を読まない**。

本モジュールの役割
- **値を決めるだけ**(体の定数・消費・摂取の比・語の段・範囲外の食事の予定)。SoA への書き込みは
  ``engine.resolve`` の ``initialize_energy`` / ``advance_body`` / ``_complete_eat`` /
  ``_complete_buy`` / ``energy_out_of_area_meal`` だけ(運用設計書 §2.2 Phase C の単一書き手)。
- ラン中の**診断**(食事の件数・時刻の分布・語の段の時間・体ごとの食事の印)は ``EnergyLayer`` が
  持つ(state_hash には入らない=挙動に効かない)。

式(アジェンダ §1)
- 体重 ``weight_kg``: 第14表(性 × 年齢)の平均 ± SD から ``core.rng.stream(seed, "body.weight", i)``
  の正規抽選。z は ±3 に丸め(=平均 ± 3SD)・5 kg 未満は 5 kg。0 歳は 1 歳の行。
- EER ``eer_kcal`` = 表3 の体重 1 kg 当たり基礎代謝量基準値 × 体重 × 表4 の PAL ふつう
  + N(0, 199 男 / 164 女)(``stream(seed, "body.eer", i)``・成人の SD を全年齢に使う=宣言)。
  下限=基礎代謝量(PAL 1.0 相当)= ``EER_FLOOR_PAL``(宣言・幼児で個人差が負に振れたとき用)。
- 消費(K1 (c)): 毎 tick ``eer/1440 × 分/tick × METs(活動)/AVG_METS``(感度腕 ``bmr``=
  ``BMR × METs × 分/1440``)。範囲外(``transit_state==2``)は ``METs=AVG_METS``(基準日の平均)。
- 摂取(K7 (a)): 食事=時間帯の比(第13表 朝:昼:夕 を 3 食で 1.0 に正規化・性 × 年齢)× EER・
  ``since_meal=0``。軽食=第13表の「間」/(朝+昼+夕+間)× EER・飲料=``DRINK_SHARE`` × EER・
  ``since_meal = max(0, since_meal − 摂取)``。
- 語(K2 (a)): ``since_meal / (eer/3)`` の比 → 満腹 <0.25 / ふつう / 空腹 ≥0.75 / とても空腹 ≥1.5。
  ``hunger`` はその写し(1 / 5 / 8 / 10)= ``INTERO_UP_EDGES=(4,7,9)`` の跨ぎがそのまま段の跨ぎ。
- 範囲外の食事(K9 (a)): W17 の食事行の開始(その時刻に域外)+食事行の無い時間帯は既定の時刻
  (朝 7:29・夕 19:18=第18-1表 東京都 平日・昼=第7-1表 平日 東京都 総数の最大区分の開始)。

逐次ループ宣言(P4)
1. ``EnergyModel.draw_bodies``: **起動時 1 回・体数ぶん**(体ごとの乱数流を 2 本作る=アジェンダの
   ``stream(seed, "body.weight", agent)`` をそのまま使うため。実測 ≈9 µs/体/本)。
2. ``EnergyModel.__init__``: 錨の表の行数ぶん(≤ 31・起動時 1 回)。
3. ``OutOfAreaMeals.__init__``: 時間帯 3 つぶん(起動時 1 回)。体・行はすべて配列演算。
4. tick ごと(``expenditure`` / ``stage_of`` / ``EnergyLayer.after_tick`` / ``due``): **なし**
   (配列演算だけ)。

expedient(本モジュール分・宣言)
- ``AVG_METS=1.379``(座位中心の基準日・アジェンダ §1-2)・語の区切り 0.25/0.75/1.5(草案 §1-5)・
  ``DRINK_SHARE=0.03``・性別不明(−1)は男女の表の平均(第13表は総数)・時間帯の窓(朝 5:00〜10:59・
  昼 11:00〜15:59・夕 17:00〜23:59・その他は昼の比)・範囲外の METs=AVG_METS・
  初期値 ``since_meal = EER × (1440 − 夕食の既定分)/1440``(前夜の夕食から 0:00 まで基準日の速さ)・
  EER の下限=基礎代謝量・範囲外の食事の「食事行が無い」は時間帯(朝/昼/夕の窓)ごとに見る・
  範囲外の食事行=活動語「食事」の行の開始にその体が域外(``transit_state==2``)に居る行
  (場所語「域外」の行に限らない=域外居住者の自宅の食事行を含む)。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Mapping

import numpy as np

from shibuya.agents.state import Activity, ActivityKind
from shibuya.core.rng import stream

__all__ = [
    "ANCHORS_PATH",
    "HUNGER_MODELS",
    "DEFAULT_HUNGER_MODEL",
    "ENERGY_RATES",
    "DEFAULT_ENERGY_RATE",
    "AVG_METS",
    "METS_CODE",
    "HUNGER_RATIO_EDGES",
    "HUNGER_STAGE_VALUES",
    "HUNGER_STAGE_KEYS",
    "MEAL_WINDOWS_MIN",
    "DRINK_SHARE",
    "SNACK_CATS",
    "SNACK_SUBCATS",
    "DRINK_SUBCATS",
    "INTAKE_NONE",
    "INTAKE_SNACK",
    "INTAKE_DRINK",
    "SLOT_BREAKFAST",
    "SLOT_LUNCH",
    "SLOT_DINNER",
    "SLOT_OTHER",
    "EER_FLOOR_PAL",
    "check_hunger_model",
    "check_energy_rate",
    "load_anchors",
    "EnergyModel",
    "OutOfAreaMeals",
    "EnergyLayer",
]

#: 錨の追跡ファイル(リポ直下からの相対)。
ANCHORS_PATH: Final[Path] = (
    Path(__file__).resolve().parents[3] / "docs" / "bench" / "anchors" / "hunger_energy_anchors_v0.json"
)

#: 空腹のモデル(``--hunger-model``)。``v1``=旧規則(+1/30 分・購入/食事で −4)。
HUNGER_MODELS: Final[tuple[str, ...]] = ("v1", "energy")
#: **CLI の既定**(K5 (a))。``run_day`` のライブラリ既定は ``v1``(語彙・L4 と同じ分け方)。
DEFAULT_HUNGER_MODEL: Final[str] = "energy"
#: 消費の式(``--energy-rate``)。``eer``=K1 (c)・``bmr``=K1 (a) の感度腕。
ENERGY_RATES: Final[tuple[str, ...]] = ("eer", "bmr")
DEFAULT_ENERGY_RATE: Final[str] = "eer"

#: 基準日の平均 METs(宣言・座位中心の 1 日=(7.5×1.0+14.5×1.3+1.5×3.5+0.5×3.0)/24=33.1/24)。
AVG_METS: Final[float] = 1.379
#: 活動の種別 → METs のコード(改訂版メッツ表 2012)。値は錨から読む。
METS_CODE: Final[dict[str, str]] = {
    "sleep": "07030",      # 睡眠 1.0
    "sitting": "07020",    # その場/在店/なし/乗車(座位の代理)1.3
    "walk_dest": "17190",  # 目的地つき移動 3.5
    "wander": "17170",     # あたり 3.0
}
#: 語の段の区切り(``since_meal / (eer/3)``・expedient・草案 §1-5)。
HUNGER_RATIO_EDGES: Final[tuple[float, float, float]] = (0.25, 0.75, 1.5)
#: 段 → ``hunger`` の写し(0〜10 の目盛・``INTERO_UP_EDGES=(4,7,9)`` の跨ぎ=段の跨ぎ)。
HUNGER_STAGE_VALUES: Final[tuple[int, int, int, int]] = (1, 5, 8, 10)
#: 段の鍵(manifest・記録用。語そのものは ``perception.templates.HUNGER_WORDS``)。
HUNGER_STAGE_KEYS: Final[tuple[str, str, str, str]] = ("full", "normal", "hungry", "very_hungry")

#: 時間帯の窓[分](朝 5〜10 時台・昼 11〜15 時台・夕 17〜23 時台・その他は昼の比=宣言)。
MEAL_WINDOWS_MIN: Final[dict[str, tuple[int, int]]] = {
    "breakfast": (300, 660),
    "lunch": (660, 960),
    "dinner": (1020, 1440),
}
SLOT_BREAKFAST: Final[int] = 0
SLOT_LUNCH: Final[int] = 1
SLOT_DINNER: Final[int] = 2
#: 窓の外(比は昼を使う)。
SLOT_OTHER: Final[int] = 3

#: 飲料の摂取(EER の比・expedient のまま=アジェンダ §1-3)。
DRINK_SHARE: Final[float] = 0.03
#: 軽食になる購入の対象(cat food / subcat convenience)。
SNACK_CATS: Final[tuple[str, ...]] = ("food",)
SNACK_SUBCATS: Final[tuple[str, ...]] = ("convenience",)
#: 飲料になる購入の対象(subcat drink/vending。**実資産の W6 には 0 件**=口だけ)。
DRINK_SUBCATS: Final[tuple[str, ...]] = ("drink", "vending")
INTAKE_NONE: Final[int] = 0
INTAKE_SNACK: Final[int] = 1
INTAKE_DRINK: Final[int] = 2

#: EER の下限(基礎代謝量 × この PAL)。個人差 N(0, 199/164) が幼児で負に振れる時の床(宣言)。
EER_FLOOR_PAL: Final[float] = 1.0
#: 体重の z の丸め(平均 ± 3SD)と下限[kg](アジェンダ §1-1・第291)。
WEIGHT_Z_CLIP: Final[float] = 3.0
WEIGHT_MIN_KG: Final[float] = 5.0

_SEX_MALE: Final[int] = 0
_SEX_FEMALE: Final[int] = 1
#: 性別不明(−1)の表の行(男女の平均・第13表は総数)。
_SEX_UNKNOWN_ROW: Final[int] = 2


def check_hunger_model(value: str) -> str:
    v = str(value)
    if v not in HUNGER_MODELS:
        raise ValueError(f"hunger_model は {HUNGER_MODELS} のどれか(いま {value!r})")
    return v


def check_energy_rate(value: str) -> str:
    v = str(value)
    if v not in ENERGY_RATES:
        raise ValueError(f"energy_rate は {ENERGY_RATES} のどれか(いま {value!r})")
    return v


def load_anchors(path: str | Path | None = None) -> tuple[dict[str, Any], str]:
    """錨の追跡ファイルを読む → ``(辞書, md5)``。"""
    p = Path(path) if path is not None else ANCHORS_PATH
    raw = p.read_bytes()
    return json.loads(raw.decode("utf-8")), hashlib.md5(raw).hexdigest()


def _sex_rows(male: list[float], female: list[float]) -> np.ndarray:
    """(3, k) = 男・女・不明(男女の平均)。"""
    m = np.asarray(male, dtype=np.float64)
    f = np.asarray(female, dtype=np.float64)
    return np.stack([m, f, (m + f) / 2.0])


def _sex_index(sex: np.ndarray) -> np.ndarray:
    s = np.asarray(sex, dtype=np.int64)
    return np.where((s == _SEX_MALE) | (s == _SEX_FEMALE), s, _SEX_UNKNOWN_ROW)


def _class_index(age: np.ndarray, age_lo: np.ndarray) -> np.ndarray:
    """年齢 → 階級の索引(下端の表で右寄せ二分探索・下限未満は 0 番)。"""
    a = np.asarray(age, dtype=np.int64)
    return np.clip(np.searchsorted(age_lo, a, side="right") - 1, 0, age_lo.size - 1)


def minute_slot(minute: np.ndarray | int) -> np.ndarray:
    """その日の分 → 時間帯(朝 0 / 昼 1 / 夕 2 / その他 3)。"""
    m = np.asarray(minute, dtype=np.int64) % 1440
    out = np.full(m.shape, SLOT_OTHER, dtype=np.int8)
    for s, key in ((SLOT_BREAKFAST, "breakfast"), (SLOT_LUNCH, "lunch"), (SLOT_DINNER, "dinner")):
        lo, hi = MEAL_WINDOWS_MIN[key]
        out[(m >= lo) & (m < hi)] = s
    return out


@dataclass
class EnergyModel:
    """錨から組んだ表と式(純関数)。書き込みはしない。"""

    anchors: Mapping[str, Any]
    anchors_md5: str = ""
    rate: str = DEFAULT_ENERGY_RATE
    minutes_per_tick: float = 1.0

    def __post_init__(self) -> None:
        self.rate = check_energy_rate(self.rate)
        a = self.anchors
        dri = a["dri2025"]
        self.dri_age_lo = np.asarray(dri["age_lo"], dtype=np.int64)
        self.bmr_per_kg = _sex_rows(dri["bmr_per_kg_kcal"]["male"], dri["bmr_per_kg_kcal"]["female"])
        self.pal_normal = np.asarray(dri["pal_normal"], dtype=np.float64)
        sd = dri["eer_sd_kcal_day"]
        self.eer_sd = np.asarray(
            [sd["male"], sd["female"], (sd["male"] + sd["female"]) / 2.0], dtype=np.float64
        )
        w = a["nhns_t14_weight"]
        self.w_age_lo = np.asarray(w["age_lo"], dtype=np.int64)
        self.w_mean = _sex_rows(w["weight_kg"]["male"]["mean"], w["weight_kg"]["female"]["mean"])
        self.w_sd = _sex_rows(w["weight_kg"]["male"]["sd"], w["weight_kg"]["female"]["sd"])
        t13 = a["nhns_t13_meal_kcal"]
        self.s_age_lo = np.asarray(t13["age_lo"], dtype=np.int64)
        sh = t13["shares"]
        # (3 性, 4 時間帯(朝/昼/夕/その他=昼), k 階級)
        self.meal_share = np.stack([
            np.stack([
                np.asarray(sh[sx]["breakfast"], dtype=np.float64),
                np.asarray(sh[sx]["lunch"], dtype=np.float64),
                np.asarray(sh[sx]["dinner"], dtype=np.float64),
                np.asarray(sh[sx]["lunch"], dtype=np.float64),
            ])
            for sx in ("male", "female", "total")
        ])
        self.snack_share = np.stack([
            np.asarray(sh[sx]["snack_of_four"], dtype=np.float64) for sx in ("male", "female", "total")
        ])
        mets = a["mets_2012"]["mets"]
        self.mets_sleep = float(mets[METS_CODE["sleep"]])
        self.mets_sitting = float(mets[METS_CODE["sitting"]])
        self.mets_walk_dest = float(mets[METS_CODE["walk_dest"]])
        self.mets_wander = float(mets[METS_CODE["wander"]])
        t18 = a["ssb2021_t18_1_weekday"]["tokyo"]
        self.default_meal_min = {
            "breakfast": int(t18["breakfast_start"]["mean_min"]),
            "lunch": int(a["derived"]["lunch_default"]["start_min"]),
            "dinner": int(t18["dinner_start"]["mean_min"]),
        }
        self.ticks_per_day = 1440.0 / float(self.minutes_per_tick)

    # ---- 体の定数(ラン開始時に 1 回) ----
    def draw_bodies(
        self, age: np.ndarray, sex: np.ndarray, seed: int | str
    ) -> tuple[np.ndarray, np.ndarray]:
        """体重と EER(``float32``)。逐次ループ宣言 1(起動時 1 回・体数ぶん)。"""
        n = int(np.asarray(age).size)
        zw = np.empty(n, dtype=np.float64)
        ze = np.empty(n, dtype=np.float64)
        for i in range(int(n)):  # 逐次ループ宣言 1: 起動時 1 回・体数ぶん
            zw[i] = stream(seed, "body.weight", i).standard_normal()
            ze[i] = stream(seed, "body.eer", i).standard_normal()
        return self.bodies_from_z(age, sex, zw, ze)

    def bodies_from_z(
        self, age: np.ndarray, sex: np.ndarray, zw: np.ndarray, ze: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """標準正規の値 → 体重と EER(配列演算・テストが z を直に渡せる口)。"""
        si = _sex_index(sex)
        wi = _class_index(age, self.w_age_lo)
        mean = self.w_mean[si, wi]
        sd = self.w_sd[si, wi]
        z = np.clip(np.asarray(zw, dtype=np.float64), -WEIGHT_Z_CLIP, WEIGHT_Z_CLIP)
        weight = np.maximum(mean + sd * z, WEIGHT_MIN_KG)
        bmr = self.bmr_kcal(age, sex, weight)
        di = _class_index(age, self.dri_age_lo)
        eer = bmr * self.pal_normal[di] + self.eer_sd[si] * np.asarray(ze, dtype=np.float64)
        eer = np.maximum(eer, bmr * EER_FLOOR_PAL)
        return weight.astype(np.float32), eer.astype(np.float32)

    def bmr_kcal(self, age: np.ndarray, sex: np.ndarray, weight: np.ndarray) -> np.ndarray:
        """基礎代謝量[kcal/日]=表3 の体重 1 kg 当たり × 体重。"""
        si = _sex_index(sex)
        di = _class_index(age, self.dri_age_lo)
        return self.bmr_per_kg[si, di] * np.asarray(weight, dtype=np.float64)

    def eer_reference(self, age: int, sex: int, weight: float) -> float:
        """個人差なしの EER(テスト・紙上計算の検算用)。"""
        a = np.asarray([age])
        s = np.asarray([sex])
        di = _class_index(a, self.dri_age_lo)
        return float(self.bmr_kcal(a, s, np.asarray([weight]))[0] * self.pal_normal[di][0])

    # ---- 消費(毎 tick・配列演算) ----
    def mets_of(
        self,
        activity: np.ndarray,
        transit_state: np.ndarray,
        activity_kind: np.ndarray | None,
    ) -> np.ndarray:
        """活動 → METs(``float32``)。就寝 1.0・歩行中(``MOVING``)は あたり 3.0 / それ以外 3.5・
        他(その場/在店/なし/乗車/待機/会話)1.3・範囲外(``transit_state==2``)は ``AVG_METS``。"""
        act = np.asarray(activity)
        mets = np.full(act.shape, self.mets_sitting, dtype=np.float32)
        moving = act == int(Activity.MOVING)
        if activity_kind is not None:
            wander = moving & (np.asarray(activity_kind) == int(ActivityKind.WANDER))
            mets[moving] = self.mets_walk_dest
            mets[wander] = self.mets_wander
        else:
            mets[moving] = self.mets_walk_dest
        mets[act == int(Activity.SLEEPING)] = self.mets_sleep
        mets[np.asarray(transit_state) == 2] = AVG_METS
        return mets

    def expenditure(
        self,
        eer: np.ndarray,
        mets: np.ndarray,
        bmr: np.ndarray | None = None,
    ) -> np.ndarray:
        """1 tick の消費[kcal](``float32``)。``eer`` 腕=EER/1440×分×METs/AVG・``bmr`` 腕=BMR×METs×分/1440。"""
        per_min = float(self.minutes_per_tick) / 1440.0
        if self.rate == "bmr":
            if bmr is None:
                raise ValueError("energy_rate='bmr' は体ごとの BMR が要る")
            return (np.asarray(bmr, dtype=np.float32) * np.float32(per_min) * mets).astype(np.float32)
        return (
            np.asarray(eer, dtype=np.float32) * np.float32(per_min / AVG_METS) * mets
        ).astype(np.float32)

    # ---- 語の段 ----
    @staticmethod
    def stage_of(since_meal: np.ndarray, eer: np.ndarray) -> np.ndarray:
        """``since_meal / (eer/3)`` → 段 0〜3(``int8``)。"""
        meal = np.maximum(np.asarray(eer, dtype=np.float32), np.float32(1e-3)) / np.float32(3.0)
        ratio = np.asarray(since_meal, dtype=np.float32) / meal
        return np.searchsorted(
            np.asarray(HUNGER_RATIO_EDGES, dtype=np.float32), ratio, side="right"
        ).astype(np.int8)

    @staticmethod
    def hunger_copy(stage: np.ndarray) -> np.ndarray:
        """段 → ``hunger`` の写し(``uint8``・1/5/8/10)。"""
        return np.asarray(HUNGER_STAGE_VALUES, dtype=np.uint8)[np.asarray(stage, dtype=np.int64)]

    # ---- 摂取の比 ----
    def meal_share_of(self, age: np.ndarray, sex: np.ndarray, minute: int | np.ndarray) -> np.ndarray:
        """食事 1 回の EER の比(時間帯 × 性 × 年齢)。"""
        si = _sex_index(sex)
        ci = _class_index(age, self.s_age_lo)
        slot = np.broadcast_to(minute_slot(minute), si.shape).astype(np.int64)
        return self.meal_share[si, slot, ci]

    def meal_share_for_slot(self, age: np.ndarray, sex: np.ndarray, slot: np.ndarray) -> np.ndarray:
        si = _sex_index(sex)
        ci = _class_index(age, self.s_age_lo)
        return self.meal_share[si, np.asarray(slot, dtype=np.int64), ci]

    def snack_share_of(self, age: np.ndarray, sex: np.ndarray) -> np.ndarray:
        si = _sex_index(sex)
        ci = _class_index(age, self.s_age_lo)
        return self.snack_share[si, ci]

    def initial_since_meal(self, eer: np.ndarray) -> np.ndarray:
        """tick 0(0:00)の食後の消費=前夜の夕食(既定の分)から 0:00 まで基準日の速さ(宣言)。"""
        frac = (1440 - self.default_meal_min["dinner"]) / 1440.0
        return (np.asarray(eer, dtype=np.float64) * frac).astype(np.float32)

    @staticmethod
    def poi_intake_kind(poi_cat: Any, poi_subcat: Any, n_poi: int) -> np.ndarray:
        """POI → 購入の摂取の種類(``int8``・0 なし / 1 軽食 / 2 飲料)。起動時 1 回。"""
        cats = [str(c) for c in (poi_cat if poi_cat is not None else ())]
        subs = [str(s) for s in (poi_subcat if poi_subcat is not None else ())]
        if len(cats) != n_poi:
            cats = [""] * n_poi
        if len(subs) != n_poi:
            subs = [""] * n_poi
        c = np.asarray(cats, dtype=object)
        s = np.asarray(subs, dtype=object)
        out = np.zeros(n_poi, dtype=np.int8)
        if n_poi:
            snack = np.isin(c, SNACK_CATS) | np.isin(s, SNACK_SUBCATS)
            drink = np.isin(s, DRINK_SUBCATS)
            out[snack] = INTAKE_SNACK
            out[drink] = INTAKE_DRINK
        return out

    def manifest_fields(self) -> dict[str, Any]:
        mets = self.anchors["mets_2012"]["mets"]
        return {
            "rate": self.rate,
            "avg_mets": AVG_METS,
            "mets": {role: {"code": code, "mets": float(mets[code])} for role, code in METS_CODE.items()},
            "mets_out_of_area": AVG_METS,
            "hunger_ratio_edges": list(HUNGER_RATIO_EDGES),
            "hunger_stage_values": list(HUNGER_STAGE_VALUES),
            "meal_windows_min": {k: list(v) for k, v in MEAL_WINDOWS_MIN.items()},
            "share_source": "nhns_t13 (breakfast:lunch:dinner normalized to 1.0 by sex x age; "
                            "snack = snack/(4 meals)); other slots use lunch",
            "drink_share": DRINK_SHARE,
            "default_meal_min": dict(self.default_meal_min),
            "initial_since_meal": "eer x (1440 - default dinner min)/1440",
            "eer_floor_pal": EER_FLOOR_PAL,
            "anchors": "docs/bench/anchors/hunger_energy_anchors_v0.json",
            "anchors_md5": self.anchors_md5,
        }


class OutOfAreaMeals:
    """範囲外の食事の予定(K9 (a))。起動時に 1 日ぶんの (tick, 体, 時間帯) を組む。

    - W17 の**食事行**(活動語「食事」)の開始 → その時刻に域外(``transit_state==2``)なら食事。
    - 時間帯(朝/昼/夕)に食事行が 1 本も無い体は**既定の時刻**(朝 7:29・昼 12:15・夕 19:18)に、
      その時刻に域外なら食事(アジェンダ §1-5 の文言どおり=W17 の就寝中かどうかは見ない)。
    - 週次表の無いラン(合成・母集団なし)は全員に既定の時刻だけ(域外に居なければ何も起きない)。
    """

    def __init__(
        self,
        model: EnergyModel,
        n_agents: int,
        ticks: int,
        weekly: Any = None,
        day_index: int = 0,
        tick_seconds: int = 60,
    ) -> None:
        n = int(n_agents)
        agent_parts: list[np.ndarray] = []
        minute_parts: list[np.ndarray] = []
        slot_parts: list[np.ndarray] = []
        from_row_parts: list[np.ndarray] = []
        has_row = np.zeros((n, 3), dtype=bool)
        if weekly is not None:
            from shibuya.agents.weekly import ACTIVITY_WORDS, N_DAYS

            eat_code = ACTIVITY_WORDS.index("食事")
            m = min(n, int(weekly.n_agents))
            d = int(day_index) % N_DAYS
            lo = np.asarray(weekly.day_offset[d::N_DAYS][:m], dtype=np.int64)
            hi = np.asarray(weekly.day_offset[d + 1::N_DAYS][:m], dtype=np.int64)
            counts = hi - lo
            total = int(counts.sum())
            if total:
                rows = np.repeat(np.arange(m, dtype=np.int64), counts)
                base = np.repeat(np.cumsum(counts) - counts, counts)
                idx = np.repeat(lo, counts) + (np.arange(total, dtype=np.int64) - base)
                eat = np.asarray(weekly.activity, dtype=np.int64)[idx] == eat_code
                a_eat = rows[eat]
                s_eat = np.asarray(weekly.start_min, dtype=np.int64)[idx[eat]]
                slot = minute_slot(s_eat).astype(np.int64)
                agent_parts.append(a_eat)
                minute_parts.append(s_eat)
                slot_parts.append(slot)
                from_row_parts.append(np.ones(a_eat.size, dtype=bool))
                in_window = slot < 3
                has_row[a_eat[in_window], slot[in_window]] = True
        for s, key in enumerate(("breakfast", "lunch", "dinner")):
            need = np.flatnonzero(~has_row[:, s])
            agent_parts.append(need.astype(np.int64))
            minute_parts.append(np.full(need.size, model.default_meal_min[key], dtype=np.int64))
            slot_parts.append(np.full(need.size, s, dtype=np.int64))
            from_row_parts.append(np.zeros(need.size, dtype=bool))
        agent = np.concatenate(agent_parts) if agent_parts else np.empty(0, dtype=np.int64)
        minute = np.concatenate(minute_parts) if minute_parts else np.empty(0, dtype=np.int64)
        slot = np.concatenate(slot_parts) if slot_parts else np.empty(0, dtype=np.int64)
        from_row = np.concatenate(from_row_parts) if from_row_parts else np.empty(0, dtype=bool)
        tick = (minute * 60) // int(tick_seconds)
        keep = tick < int(ticks)
        order = np.lexsort((agent[keep], tick[keep]))
        self.tick = tick[keep][order].astype(np.int64)
        self.agent = agent[keep][order].astype(np.int64)
        self.slot = slot[keep][order].astype(np.int8)
        self.from_row = from_row[keep][order]
        self.n_rows = int(np.count_nonzero(from_row))
        self.n_defaults = int(from_row.size - self.n_rows)
        self._start = np.searchsorted(self.tick, np.arange(int(ticks) + 1, dtype=np.int64), side="left")

    def due(self, tick: int, transit_state: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """この tick に域外で食べる ``(体, 時間帯, 行由来か)``(配列演算)。"""
        t = int(tick)
        if t < 0 or t + 1 >= self._start.size:
            e = np.empty(0, dtype=np.int64)
            return e, np.empty(0, dtype=np.int8), np.empty(0, dtype=bool)
        lo, hi = int(self._start[t]), int(self._start[t + 1])
        if hi <= lo:
            e = np.empty(0, dtype=np.int64)
            return e, np.empty(0, dtype=np.int8), np.empty(0, dtype=bool)
        ids = self.agent[lo:hi]
        out = np.asarray(transit_state)[ids] == 2
        return ids[out], self.slot[lo:hi][out], self.from_row[lo:hi][out]


@dataclass
class EnergyLayer:
    """ラン 1 本ぶんの エネルギー収支(模型+範囲外の予定+診断)。"""

    model: EnergyModel
    n_agents: int
    out_of_area: OutOfAreaMeals | None = None
    #: ``bmr`` 腕の体ごとの基礎代謝量(派生の定数・state_hash に入らない)。
    bmr: np.ndarray | None = None
    #: 購入の対象 POI → 摂取の種類(0 なし / 1 軽食 / 2 飲料)。
    poi_intake: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int8))
    # ---- 診断(挙動に効かない) ----
    counts: dict[str, int] = field(default_factory=dict)
    intake_kcal: dict[str, float] = field(default_factory=dict)
    meal_start_in: np.ndarray = field(default_factory=lambda: np.zeros(96, dtype=np.int64))
    meal_start_out: np.ndarray = field(default_factory=lambda: np.zeros(96, dtype=np.int64))
    snack_start: np.ndarray = field(default_factory=lambda: np.zeros(96, dtype=np.int64))
    #: 語の段 × tick の延べ(行: 0 起きて範囲内 / 1 就寝中 / 2 範囲外・乗車中)。
    stage_ticks: np.ndarray = field(default_factory=lambda: np.zeros((3, 4), dtype=np.int64))
    #: 同(起きて範囲内)を 1 時間ごと(24 × 4)。
    stage_ticks_awake_by_hour: np.ndarray = field(
        default_factory=lambda: np.zeros((24, 4), dtype=np.int64)
    )
    meal_bits: np.ndarray | None = None
    n_meals: np.ndarray | None = None
    n_snacks: np.ndarray | None = None

    def __post_init__(self) -> None:
        n = int(self.n_agents)
        self.meal_bits = np.zeros(n, dtype=np.uint8)
        self.n_meals = np.zeros(n, dtype=np.uint8)
        self.n_snacks = np.zeros(n, dtype=np.uint8)
        for k in ("meals_in_area", "meals_out_of_area", "meals_out_from_row",
                  "meals_out_default", "snacks", "drinks"):
            self.counts.setdefault(k, 0)
        for k in ("meal_in", "meal_out", "snack", "drink"):
            self.intake_kcal.setdefault(k, 0.0)

    # ---- resolve から(成立した行だけ) ----
    def note(self, kind: str, ids: np.ndarray, minute: int, kcal: float,
             slots: np.ndarray | None = None, from_row: np.ndarray | None = None) -> None:
        """摂取の記録(診断)。``kind`` は meal_in / meal_out / snack / drink。"""
        ids = np.asarray(ids, dtype=np.int64)
        if ids.size == 0:
            return
        q = (int(minute) % 1440) // 15
        self.intake_kcal[kind] = self.intake_kcal.get(kind, 0.0) + float(kcal)
        if kind in ("meal_in", "meal_out"):
            key = "meals_in_area" if kind == "meal_in" else "meals_out_of_area"
            self.counts[key] += int(ids.size)
            (self.meal_start_in if kind == "meal_in" else self.meal_start_out)[q] += int(ids.size)
            s = (
                np.asarray(slots, dtype=np.int64)
                if slots is not None
                else np.broadcast_to(minute_slot(minute), ids.shape).astype(np.int64)
            )
            win = s < 3
            np.bitwise_or.at(self.meal_bits, ids[win], (1 << s[win]).astype(np.uint8))
            np.add.at(self.n_meals, ids, 1)
            if kind == "meal_out" and from_row is not None:
                fr = np.asarray(from_row, dtype=bool)
                self.counts["meals_out_from_row"] += int(np.count_nonzero(fr))
                self.counts["meals_out_default"] += int(np.count_nonzero(~fr))
        elif kind == "snack":
            self.counts["snacks"] += int(ids.size)
            self.snack_start[q] += int(ids.size)
            np.add.at(self.n_snacks, ids, 1)
        elif kind == "drink":
            self.counts["drinks"] += int(ids.size)

    # ---- run のループから(読むだけ) ----
    def after_tick(self, agents: Any, tick: int, minute: int) -> None:
        """語の段の時間の延べ(配列演算)。"""
        r = agents.registry
        stage = np.searchsorted(np.asarray((4, 7, 9)), np.asarray(r.hunger), side="right")
        asleep = np.asarray(r.activity) == int(Activity.SLEEPING)
        away = np.asarray(r.transit_state) != 0
        awake_in = ~asleep & ~away
        self.stage_ticks[0] += np.bincount(stage[awake_in], minlength=4)[:4]
        self.stage_ticks[1] += np.bincount(stage[asleep & ~away], minlength=4)[:4]
        self.stage_ticks[2] += np.bincount(stage[away], minlength=4)[:4]
        self.stage_ticks_awake_by_hour[(int(minute) % 1440) // 60] += np.bincount(
            stage[awake_in], minlength=4
        )[:4]

    # ---- ランの終わり ----
    def summary(self, agents: Any) -> dict[str, Any]:
        r = agents.registry
        bal = np.asarray(r.energy_balance, dtype=np.float64)
        eer = np.asarray(r.eer_kcal, dtype=np.float64)
        intake_total = float(sum(self.intake_kcal.values()))
        expenditure_total = float(intake_total - bal.sum())
        n = max(1, int(bal.size))

        def q(x: np.ndarray) -> dict[str, float]:
            if x.size == 0:
                return {"n": 0}
            p = np.percentile(x, [5, 25, 50, 75, 95])
            return {"n": int(x.size), "mean": round(float(x.mean()), 1),
                    "p5": round(float(p[0]), 1), "p25": round(float(p[1]), 1),
                    "p50": round(float(p[2]), 1), "p75": round(float(p[3]), 1),
                    "p95": round(float(p[4]), 1)}

        nm = np.asarray(self.n_meals, dtype=np.int64)
        by_meals = {str(k): q(bal[nm == k]) for k in range(4)}
        by_meals["4+"] = q(bal[nm >= 4])
        ratio = bal / np.maximum(eer, 1.0)
        by_meals_ratio = {str(k): q(ratio[nm == k]) for k in range(4)}
        by_meals_ratio["4+"] = q(ratio[nm >= 4])
        three = (np.asarray(self.meal_bits) & 7) == 7
        age = np.asarray(r.age, dtype=np.int64)
        sex = np.asarray(r.sex, dtype=np.int64)
        has_b = (np.asarray(self.meal_bits) & 1) != 0

        def skip(mask: np.ndarray) -> dict[str, float]:
            k = int(np.count_nonzero(mask))
            if k == 0:
                return {"n": 0}
            return {"n": k, "skip_pct": round(100.0 * float(np.count_nonzero(mask & ~has_b)) / k, 1)}

        twenties = (age >= 20) & (age <= 29)
        st = self.stage_ticks
        shares = {}
        for row, name in enumerate(("awake_in_area", "asleep_in_area", "away")):
            tot = int(st[row].sum())
            shares[name] = {
                HUNGER_STAGE_KEYS[k]: (round(float(st[row, k]) / tot, 4) if tot else 0.0)
                for k in range(4)
            }
            shares[name]["agent_ticks"] = tot
        return {
            "counts": dict(self.counts),
            "intake_kcal": {k: round(v, 1) for k, v in self.intake_kcal.items()},
            "census": {
                "intake_kcal": round(intake_total, 1),
                "expenditure_kcal": round(expenditure_total, 1),
                "balance_kcal": round(float(bal.sum()), 1),
            },
            "census_per_agent": {
                "intake_kcal": round(intake_total / n, 1),
                "expenditure_kcal": round(expenditure_total / n, 1),
                "balance_kcal": round(float(bal.sum()) / n, 1),
                "eer_kcal": round(float(eer.mean()), 1),
            },
            "balance_kcal": q(bal),
            "balance_kcal_by_meals": by_meals,
            "balance_over_eer_by_meals": by_meals_ratio,
            "agents_with_three_meals": int(np.count_nonzero(three)),
            "meals_per_agent": {str(k): int(np.count_nonzero(nm == k)) for k in range(4)}
            | {"4+": int(np.count_nonzero(nm >= 4))},
            "breakfast_skip": {
                "all": skip(np.ones(age.size, dtype=bool)),
                "age20_29": skip(twenties),
                "age20_29_male": skip(twenties & (sex == 0)),
                "age20_29_female": skip(twenties & (sex == 1)),
            },
            "stage_time_share": shares,
            "stage_ticks_awake_by_hour": self.stage_ticks_awake_by_hour.tolist(),
            "meal_start_in_15min": self.meal_start_in.tolist(),
            "meal_start_out_15min": self.meal_start_out.tolist(),
            "snack_start_15min": self.snack_start.tolist(),
            "out_of_area_schedule": (
                {"from_rows": self.out_of_area.n_rows, "defaults": self.out_of_area.n_defaults}
                if self.out_of_area is not None
                else {}
            ),
            "weight_kg": q(np.asarray(r.weight_kg, dtype=np.float64)),
            "eer_kcal": q(eer),
        }
