"""W21 段 4〜7(第 4 期 4-1「組織と関係・お金・開始前の経験・外の人」)の組み立て。版 1.1.0。

    python -m shibuya.build.pop.w21_build_b --out data/world/v2_stage_4-1b --data data
        [--base data/world/v2_stage_4-1] [--world data/world/v2] [--seed 20260909]
        [--division-arm {off,on}] [--affinity {lifestage,distance_only}] [--seat-roles {on,off}]

- 段 1〜3 の資産(``--base``=``v2_stage_4-1`` の W21 の 6 本)を**読むだけ**で使い(manifest の sha256 と照らす)、段 4〜7 の
  出力を ``--out`` に書く。本体の ``data/world/v2``・``--world``・``--base`` には書かない(:func:`check_out_b`・読み口の
  守り)。W21 は ``build.run`` の段の一覧に入れない=本体の build_hash は動かない(差し替えは段 10=4-3)。
- 出力(:data:`OUTPUTS_B`)と ``w21b_manifest.json``・``W21b.header.json``。``w21b_build_hash``=出力の sha256 を
  連ねた文字列の sha256。時刻など決まらない値は書かない(2 回組んで一致)。
- 段 4: ``w21_org``・段 5: ``w21_money``・段 6: ``w21_prior``・段 7: ``w21_outside``・関数: ``attr_fns``(段 4〜7)・
  計器: ``w21_checks``(合否なし)。近似の宣言は :data:`W21B_EXPEDIENTS`(つなぎの台帳に 1 行ずつ)。
- 腕(感度試験の口・既定は宣言の値): 部の段(``--division-arm on``)・なじみの場所の当てはめの業種の合い方(``--affinity
  distance_only``)・席の地位の区分(``--seat-roles off``=業種だけで埋める)。

逐次ループ宣言(P4): 段の手順の数ぶん。各手順の宣言は各モジュール。体ごとの for は無い。
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np
import pyarrow as pa

from shibuya.core.rng import k19_counter_array, philox_array, unit_float

from ..geo import common as C
from . import attr_fns as A
from . import shapefile as SH
from . import w21_attrs as WA
from . import w21_build as W
from . import w21_checks as WC
from . import w21_money as M
from . import w21_org as O
from . import w21_outside as X
from . import w21_prior as P
from . import w21_sources as S
from . import w21_tables as T

__all__ = ["STAGE_B", "STAGE_VERSION_B", "OUTPUTS_B", "MANIFEST_B", "BASE_FILES", "W21B_EXPEDIENTS", "ParamsB",
           "check_out_b", "build_b", "main", "OWN_ASSET_B", "BASE_ASSET", "WORLD_COLUMNS"]

STAGE_B: Final[str] = "W21b"
STAGE_VERSION_B: Final[str] = "1.1.0"
OUTPUTS_B: Final[tuple[str, ...]] = (
    "w21_people.parquet", "w21_org.parquet", "w21_rights_initial.parquet", "w21_relations_initial.parquet",
    "w21_money.parquet", "w21_money_households.parquet", "w21_prior_places.parquet", "w21_outside.parquet",
    "w21_outside_households.parquet", "w21_checks_b.json",
)
MANIFEST_B: Final[str] = "w21b_manifest.json"
#: 段 1〜3 の資産のうち読むもの(manifest の sha256 と照らす)。
BASE_FILES: Final[tuple[str, ...]] = ("w21_frame.json", "w21_households.parquet", "w21_persons.parquet",
                                      "w21_checks.json")
#: 段 4〜7 の資産の置き場の名(``data/world`` の下)と、段 1〜3 の資産の置き場の名。
OWN_ASSET_B: Final[str] = "v2_stage_4-1b"
BASE_ASSET: Final[str] = "v2_stage_4-1"
#: 世界資産から読む列(W12 の外の口は**構築側の欄だけ**=ODPT の乗降人員の欄(検証側 R-116 #17)は読まない)。
WORLD_COLUMNS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "w6_org.parquet": ("org_id", "industry_key", "sector_detail", "employees", "size_band", "building_id", "place_id",
                       "x", "y"),
    "w6_poi.parquet": ("poi_id", "cat", "subcat", "building_id", "place_id"),
    "w12_external_nodes.parquet": ("node_id", "kind", "daily_inflow", "attached_place_ids"),
})

#: 段 4〜7 の近似の宣言(つなぎの台帳の行と 1 対 1)。
W21B_EXPEDIENTS: Final[tuple[str, ...]] = (
    "舞台で働く人の数=区で働く 15 歳以上の就業者(国勢調査 第4表)× 舞台の割合(経済センサス 第28表の町丁目の従業者 × 被覆率 ÷ 区の従業者)=席の配分は経済センサス・人数は国勢調査(仮-23)。町丁目の中は一様",
    "自宅外の区内で働く住民の勤め先の町丁目は区の 80 町丁目を経済センサスの従業者の比で引き、被覆率の確率で舞台の中とする(距離で重みを付けない)",
    "外から来て働く人の男女・年齢は従業地 第11-1表(区で働く人全体=住民を含む)の男女 × 年齢 17 階級・階級の中は一様(95 歳以上は 95〜100 歳)",
    "外から来て働く人の常住地は第4表の流入元の 15 歳以上の就業者の重み・渋谷区の残りの町丁目(輪)は区に住み区内の自宅外で働く人 × 区の住民のうち舞台の外の割合",
    "外から来て働く人と舞台の外で働く住民の駅の口は W12 の鉄道の外の口を大都市交通センサスの路線別の流入の比で引く(常住地と方面を結ばない・渋谷駅だけ=ほかの駅とバスは作らない)",
    "席(W6 の組織の従業者)への所属は業種(industry_key)× 地位の区分(席=経済センサス 第6-2表の 5 区分の割合で組織ごとに分けた席・人=国勢調査の地位の写し)ごとに席と人の少ない方を埋め、組織ごとの数は区分の席に比例(最大剰余)・雇われる人(無期・有期と臨時)の残りは同じ業種の雇われる人の空いた席へ・業主・役員・家族従業者の残りは席の外・人の順は人ごとの乱数・町丁目を見ない(W6 の組織の場所は v1 の建物の配分=W6#1)。腕 --seat-roles off=業種だけで埋める",
    "席の外の人(人が多い業種の残り・業種が空欄=公務など)の勤め先のセルは、勤め先の町丁目の住居系でない建物の床面積で引く(無ければ住居系・無ければ被覆のセル)・組織は空欄",
    "部署の目安 S=1+業種別の課長 1 人あたりの部下(R-80・運輸と複合サービスは産業計 12.6)・部署の数 k=max(1, round(n/S))・人数は均等(SR2 の決定・揺らぎの腕は未実装)・部の段は腕(既定 off)",
    "頭(組織の長・部署の長)は役割の順(役員と業主 → 正社員 → 内職と派遣 → パート → 家族従業者)・同じなら年上・同じなら人の番号(自前)",
    "役割の語: 店(FB・WR・LS・AM)の長=店長・ほかの長=代表(役員・業主)か責任者・部署の長=部署長・ほかは地位(正社員・派遣社員・パート・アルバイト・役員・業主・家族従業者・内職)",
    "②群の担当(duty_role)の規則の表(物流の組織の運転と運搬・施設管理の清掃・警備・店長・小売の補充・席の無い運輸の運転と駅員・公務の保安)=勤め先が舞台の中の体だけ・電車運転士と車掌・警察官と消防士は人ごとの乱数で半々に分ける(内訳は未リサーチ)・W16 の在庫とは別に作る(二重)",
    "権利台帳の店の持ち主=同じ建物で業種の合う W6 の組織(POI の種類 → 業種の写像は自前)・台帳の閉じた表に「所有 → 店」が無い(in_closed_table=偽)",
    "権利台帳の住まい=世帯主 → 住まい(持ち家=所有・借家=賃借・相手と家賃は空欄)・施設等と住宅以外は行なし",
    "週の時間の目安=賃金構造の所定内実労働時間(一般=月 × 12 ÷ 52.1775 週・短時間=1 日 × 日数 × 12 ÷ 52.1775 週)・派遣は一般の正社員以外・パートは短時間",
    "賃金=第18表の職種 × 男女の所定内給与額の階級の度数(階級の中は一様・最も低い階級の下 8 万円・最も高い階級の上は下の 1.5 倍)× 年齢の比(第6表)× 雇用形態の比(第9表)=比は独立の仮定",
    "短時間労働者の時間あたりの賃金=第2表の職種 × 男女 × 第18表の形(分位の値 ÷ 中位数)",
    "世帯の貯蓄=0 円か正かを全国の年齢 × 種類の貯蓄保有率で・正の階級を東京都の世帯数分布(第31-0表)を年齢の平均(全国 第4-4表 × 東京都 ÷ 全国)に合わせて傾けた重み(二分法)で・階級の中は一様・1 億円以上は階級の平均に合う Pareto",
    "通貨性預貯金=貯蓄 × 全国の年齢 × 種類の通貨性預貯金 ÷ 貯蓄の比(比は一定)",
    "負債の有無=全国の年齢 × 種類の負債保有率 × 東京都の貯蓄の階級ごとの率 ÷ 東京都の全体の率・額=負債を持つ世帯の平均(全国 × 東京都の比)=額の広がりは空欄",
    "世帯の資産は 18 歳以上の世帯員に均等に配る(いなければ世帯主)・施設等の人は単身の表・外から来て働く人は自分を世帯主とする総世帯の表で全部を本人に",
    "貸金業の残高=JICC の残高のある人 ÷ 全国の 20 歳以上人口(国勢調査 2025)・額=借入件数の区分の 1 人あたり残高(区分の中の広がりは空欄)・世帯の負債とは別に引く・20 歳未満は 0",
    "住んでいる年数=第18表の区分の中で一様(出生時から=年齢・20 年以上の上の端=年齢)",
    "なじみの場所の容量 C=round(正規(25, 25 × 0.3))を 5〜60 に切る(平均=Alessandretti 2018・幅は未リサーチ)",
    "行ったことのある場所の数 L=C ×(住んでいる週 ÷ 20 週)^0.6・リストに載せる数=min(C, L)・外から来る人は L=C",
    "なじみの場所の当てはめ: 枠を家の側と職場の側に半分ずつ・舞台の外の側は数だけ・POI の重み=生活の段 × 業種の合い方の表(自前)× exp(−道のり/500 m)・重複なしに引く(枠 × 4 回まで)・順位は両側を交互に",
    "外の人は層の表(人は作らない・層は重なる=外から来て働く人は輪と来る可能性のある人の部分集合を含む)・輪は段 2 と同じ目標の作り方で被覆率の外の分を段 1 の枠(区の総数 − 住民)に比で合わせる・来る可能性のある人=第4表の流入元(浜松市の旧 7 区は 2025 の 3 区に区の単位で寄せる)の 2025 の人口(男女 × 年齢 5 歳)・重み=流入元の通勤通学の割合(表に無い符号を除いて和 1)・出現の確からしさは空欄",
    "訪日の国籍=JNTO 2025 の全国の国籍別の割合(渋谷の訪問率は空欄)・1 日の幅は段 1 の枠",
    "通勤の道のり=W3 のセルの代表の点の間の歩行の最短の道のり(セルの中の道のりは 0)・駅の口=W12 の鉄道の外の口の付くセルのうち最も近いもの",
)


@dataclass(frozen=True)
class ParamsB:
    """段 4〜7 の腕(既定は宣言の値)。"""

    division_arm: bool = False
    affinity: str = "lifestage"
    seat_roles: bool = True


class ProtectedOutputErrorB(ValueError):
    """``--out`` が本体の v2・読む世界資産・段 1〜3 の資産・既存の置き場の中を指している(何も書かずに止める)。"""


def check_out_b(data: Path, out: Path, world: Path, base: Path) -> None:
    """出力先の検査: 本体の ``data/world/v2``・``--world``・``--base``(段 1〜3 の資産)の中と、``data/world`` の下の既存の
    置き場(``v2_stage_4-1b*`` を除く)の中なら止める。"""
    o = Path(out).resolve()
    for root in ((Path(data) / "world" / "v2").resolve(), Path(world).resolve(), Path(base).resolve()):
        if o == root or root in o.parents:
            raise ProtectedOutputErrorB(f"段 4〜7 は本体の v2・世界資産・段 1〜3 の資産の中に書かない: {o.name}")
    wroot = (Path(data) / "world").resolve()
    if wroot in o.parents:
        top = o.relative_to(wroot).parts[0]
        if (wroot / top).exists() and not top.startswith(OWN_ASSET_B):
            raise ProtectedOutputErrorB(f"段 4〜7 は既存の資産の置き場に書かない: {top}")


def _u(seed: int | str, domain: str, ids: np.ndarray, words: int = 1) -> np.ndarray:
    return unit_float(philox_array(seed, domain, k19_counter_array(np.asarray(ids, dtype=np.int64)), words=words))


def _codes(words: np.ndarray, vocab: tuple[str, ...]) -> np.ndarray:
    lut = {w: i for i, w in enumerate(vocab)}
    w = np.asarray(words).astype(str)
    uniq, inv = np.unique(w, return_inverse=True)
    return np.array([lut.get(x, -1) for x in uniq.tolist()], dtype=np.int64)[inv] if w.size else np.zeros(0, np.int64)


def build_b(data: Path, out: Path, *, base: Path | None = None, world: Path | None = None,
            seed: int | str = W.DEFAULT_SEED, params: ParamsB = ParamsB()) -> tuple[C.StageResult, dict[str, Any]]:
    """段 4〜7 を組んで ``out`` に書く。返り値は(見出し, manifest)。"""
    data, out = Path(data), Path(out)
    world = Path(world) if world is not None else data / "world" / "v2"
    base = Path(base) if base is not None else data / "world" / BASE_ASSET
    check_out_b(data, out, world, base)
    out.mkdir(parents=True, exist_ok=True)
    guard = S.W21Guard.for_build(data, world=world, out=out, extra_dirs=(base,))
    with guard.active():
        return _build_b(guard, data, out, world, base, seed, params)


def _read_base(guard: S.W21Guard, base: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    man = json.loads(guard.read_bytes(base / W.MANIFEST_NAME).decode("utf-8"))
    want = {o["path"]: o["sha256"] for o in man["outputs"]}
    for f in BASE_FILES:
        sha = hashlib.sha256(guard.read_bytes(base / f)).hexdigest()
        if want.get(f) != sha:
            raise S.MissingSourceError(f"段 1〜3 の資産の sha256 が manifest と違う: {f}")
    persons = guard.read_parquet(base / "w21_persons.parquet")
    hh = guard.read_parquet(base / "w21_households.parquet")
    frame = json.loads(guard.read_bytes(base / "w21_frame.json").decode("utf-8"))
    return man, persons, hh, frame


def _tables_b(guard: S.W21Guard, world: Path, org: Mapping[str, Any], ring_share: float) -> tuple[A.AttrTablesB, dict]:
    w = M.load_wage_tables(guard)
    a = M.load_asset_tables(guard)
    rate, pop20 = M.jicc_holder_rate(guard)
    # 流入元(第4表)+ 輪(区に住み区内の自宅外で働く人 × 区の住民のうち舞台の外の割合)
    ins = org["inside"]
    in_ward_out_home = sum(v["workers"] for k, v in ins.items() if k.startswith("012_"))
    codes = np.array([*org["codes"].tolist(), "13113"], dtype=object)
    names = np.array([*org["names"].tolist(), "渋谷区(舞台の外の町丁目=輪)"], dtype=object)
    ow = np.array([*org["workers"].tolist(), in_ward_out_home * ring_share])
    nodes = guard.read_parquet(world / "w12_external_nodes.parquet", WORLD_COLUMNS["w12_external_nodes.parquet"])
    rail = np.array([k == "rail" for k in nodes["kind"]])
    entry_nodes = np.array(nodes["node_id"], dtype=object)[rail]
    entry_w = np.array(nodes["daily_inflow"], dtype=np.float64)[rail]
    tb = A.AttrTablesB(**w, **a, jicc_holder_rate=float(rate), origin_codes=codes, origin_names=names, origin_w=ow,
                       entry_nodes=entry_nodes, entry_w=entry_w,
                       md5=dict(sorted(guard.files_read.items()))).freeze()
    info = {"jicc_pop20": pop20, "jicc_holder_rate": round(float(rate), 6), "ring_share": round(ring_share, 6),
            "ring_commuter_weight": round(float(in_ward_out_home * ring_share), 3),
            "in_ward_workers_not_home": float(in_ward_out_home)}
    return tb, info


def _work_cells(chome_stage: np.ndarray, u: np.ndarray, g: Any) -> np.ndarray:
    """舞台の町丁目(舞台の中の番号)→ 勤め先のセル(住居系でない建物の床面積で引く・無ければ住居系・無ければ被覆のセル)。"""
    out = np.full(chome_stage.size, -1, dtype=np.int64)
    tg = g.tg
    for ci in np.unique(chome_stage[chome_stage >= 0]).tolist():  # 逐次: 町丁目の数ぶん(≤ 42)
        m = chome_stage == ci
        c80 = int(tg.stage_idx[ci])
        sel = (g.b_chome == c80) & (g.b_cell >= 0) & ~g.b_res
        if not sel.any():
            sel = (g.b_chome == c80) & (g.b_cell >= 0)
        if sel.any():
            w = g.b_floor[sel]
            cells = g.b_cell[sel]
        else:
            cells = np.asarray(g.cover_cells[c80][0], dtype=np.int64)
            w = np.asarray(g.cover_cells[c80][1], dtype=np.float64)  # 被覆のセル(標本点の数の重み)
        if cells.size == 0:
            continue
        c = np.cumsum(w)
        out[m] = cells[np.minimum(np.searchsorted(c / c[-1], u[m], side="right"), cells.size - 1)]
    return out


def _build_b(guard: S.W21Guard, data: Path, out: Path, world: Path, base: Path, seed: int | str,
             params: ParamsB) -> tuple[C.StageResult, dict[str, Any]]:
    base_man, persons, hh, frame = _read_base(guard, base)
    g = W.prepare(guard, data, world)
    tg = g.tg
    tables3, _unk = WA.build_tables(guard, g.keys80, tg.stage_idx, tg.coverage, tg.ratios["r_pop"])
    org4 = X.origins(guard)
    n_res = len(persons["person_id"])
    ring_share = 1.0 - n_res / max(float(g.ward.pop_total), 1.0)
    tb, tinfo = _tables_b(guard, world, org4, ring_share)

    # ================================================================ 段 4
    names80 = tuple(str(r["S_NAME"]) for r in g.chome)
    dims28, items28, rows28 = S.read_derived_rows(guard, "ecen21_t28")
    emp80, ward_emp, miss28 = O.chome_employees(rows28, items28, names80)
    workers_in_ward = org4["inside"]["0_総数（従業地・通学地による人口）"]["workers"]
    N_c, s_stage = O.stage_worker_targets(emp80, ward_emp, tg.stage_idx, tg.coverage, workers_in_ward)
    stage_keys = [g.keys80[i] for i in tg.stage_idx]
    pos_of_key = {k: i for i, k in enumerate(stage_keys)}
    r_pid = np.asarray(persons["person_id"], dtype=np.int64)
    ck_u, ck_inv = np.unique(np.asarray(persons["chome_key"], dtype=object).astype(str), return_inverse=True)
    r_home_chome = np.array([pos_of_key.get(k, -1) for k in ck_u.tolist()], dtype=np.int64)[ck_inv]  # 逐次: 鍵の種類
    r_codes = {name: _codes(persons[name], vocab) for name, vocab in WA.VOCAB.items()}
    area_r, wchome_r = O.assign_resident_workplaces(r_codes["workplace_kind"], r_home_chome, emp80, tg.stage_idx,
                                                    tg.coverage, _u(seed, "w21b.org.workplace", r_pid, 2))
    in_stage_r = np.isin(area_r, [O.WORKPLACE_AREAS.index("home"), O.WORKPLACE_AREAS.index("stage")])
    R_c = np.bincount(wchome_r[in_stage_r], minlength=tg.stage_idx.size)
    M_c = np.maximum(N_c - R_c, 0)
    n_com = int(M_c.sum())
    c_pid = n_res + np.arange(n_com, dtype=np.int64)
    c_chome = np.repeat(np.arange(tg.stage_idx.size), M_c)
    ccnt = np.stack([c_pid, np.zeros(n_com, dtype=np.int64), np.zeros(n_com, dtype=np.int64)], axis=1)
    ca: dict[str, Any] = {"kind": np.full(n_com, "commuter", dtype=object), "chome": np.full(n_com, -1),
                          "marital": np.full(n_com, -1), "workplace_area": np.full(n_com, "stage", dtype=object)}
    k4 = A.AttrKey(seed, "w21b.commuter.sex_age", ccnt)
    ca["sex"] = A.call("commuter_sex", ca, tables3, k4)
    ca["age"] = A.call("commuter_age", ca, tables3, k4)
    ca["emp_status"] = np.full(n_com, -1)
    for name in ("labour_status", "industry_major", "emp_status", "industry_key", "occupation_major",
                 "employment_status"):  # 逐次: 関数の数ぶん
        ca[name] = A.call(name, ca, tables3, A.AttrKey(seed, f"w21b.commuter.{name}", ccnt))
    ca["origin_muni"] = A.call("origin_muni", ca, tb, A.AttrKey(seed, "w21b.commuter.origin", ccnt))

    # ---- 人の表(住民+外から来て働く人)
    n = n_res + n_com
    pid = np.r_[r_pid, c_pid]
    kind = np.r_[np.full(n_res, "resident", dtype=object), ca["kind"]]
    sex = np.r_[np.asarray(persons["sex"], dtype=np.int64), ca["sex"]]
    age = np.r_[np.asarray(persons["age"], dtype=np.int64), ca["age"]]
    num = {k: np.r_[r_codes[k], np.asarray(ca[k], dtype=np.int64)] for k in ("labour_status", "emp_status",
                                                                                "industry_major", "occupation_major")}
    industry_key = np.r_[np.asarray(persons["industry_key"], dtype=object), ca["industry_key"]].astype(str)
    employment_status = np.r_[np.asarray(persons["employment_status"], dtype=object), ca["employment_status"]]
    area = np.r_[area_r, np.full(n_com, O.WORKPLACE_AREAS.index("stage"))]
    wchome = np.r_[wchome_r, c_chome]
    area_w = np.array(O.WORKPLACE_AREAS, dtype=object)[area]
    origin = np.r_[np.full(n_res, "13113", dtype=object), ca["origin_muni"]]
    hcell = np.r_[np.asarray(persons["home_cell"], dtype=np.int64), np.full(n_com, -1)]
    hid = np.r_[np.asarray(persons["household_id"], dtype=np.int64), np.full(n_com, -1)]

    # ---- 席(W6)
    org = guard.read_parquet(world / "w6_org.parquet", WORLD_COLUMNS["w6_org.parquet"])
    o_ind = np.asarray(org["industry_key"], dtype=object).astype(str)
    o_seats = np.asarray(org["employees"], dtype=np.int64)
    o_cell = np.array([g.place_to_cell.get(p, -1) for p in org["place_id"]], dtype=np.int64)
    o_sector = np.asarray(org["sector_detail"], dtype=object).astype(str)
    eligible = (area == O.WORKPLACE_AREAS.index("stage"))
    p_ind = np.where(eligible, industry_key, "")
    _d62, it62, rows62 = S.read_derived_rows(guard, "ecen21_t6_2")
    useat = _u(seed, "w21b.org.seat", pid)[:, 0]
    if params.seat_roles:
        shares = O.ecen_status_shares(rows62, it62)
        sh_org = np.stack([shares.get(k, np.full(5, 0.2)) for k in o_ind.tolist()])  # 逐次: 組織の数(写像の引き)
        st_tmp = np.array([*A.EMP_STATUS, ""], dtype=object)[np.where(num["emp_status"] >= 0, num["emp_status"],
                                                                       len(A.EMP_STATUS))]
        pcls = np.array([WC.CENSUS_TO_ECEN5.get(str(x), -1) for x in np.unique(st_tmp.astype(str)).tolist()],
                        dtype=np.int64)[np.unique(st_tmp.astype(str), return_inverse=True)[1]]
        org_of, filled, seat_report = O.fill_seats_by_role(o_ind, O.class_seats(o_seats, sh_org), p_ind, pcls, useat)
    else:
        org_of, filled, seat_report = O.fill_seats(o_ind, o_seats, p_ind, useat)
    seated = org_of >= 0
    status = np.full(n, "", dtype=object)
    status[seated] = "seated"
    status[eligible & ~seated & np.isin(industry_key, np.unique(o_ind))] = "no_seat_overflow"
    status[eligible & ~seated & ~np.isin(industry_key, np.unique(o_ind))] = "no_seat_industry"
    status[area == O.WORKPLACE_AREAS.index("home")] = "home"
    status[np.isin(area, [O.WORKPLACE_AREAS.index("ward_outside_stage"), O.WORKPLACE_AREAS.index("outside_ward")])] = \
        "outside_stage"
    wcell = np.full(n, -1, dtype=np.int64)
    wcell[seated] = o_cell[org_of[seated]]
    home_w = area == O.WORKPLACE_AREAS.index("home")
    wcell[home_w] = hcell[home_w]
    loose = eligible & ~seated
    wcell[loose] = _work_cells(wchome[loose], _u(seed, "w21b.org.workcell", pid[loose])[:, 0], g)

    # ---- 部署・役割・担当・時間
    st_words = np.array([*A.EMP_STATUS, ""], dtype=object)[np.where(num["emp_status"] >= 0, num["emp_status"],
                                                                     len(A.EMP_STATUS))]
    rank = np.array([A.ROLE_RANK_OF_STATUS.get(str(x), 5) for x in np.unique(st_words.astype(str)).tolist()],
                    dtype=np.int64)[np.unique(st_words.astype(str), return_inverse=True)[1]]
    deps = O.departments(org_of, rank, age, o_ind, division_arm=params.division_arm)
    pk3 = np.stack([pid, np.zeros(n, np.int64), np.zeros(n, np.int64)], axis=1)
    base_role = A.call("org_role", {"emp_status": num["emp_status"]}, tb, A.AttrKey(seed, "w21b.org.role", pk3))
    roles = O.role_words(base_role, deps, org_of, o_ind, rank)
    roles[num["labour_status"] != 0] = ""
    sector = np.where(seated, o_sector[np.clip(org_of, 0, None)], "")
    duty = A.call("duty_role_org", {"industry_key": industry_key, "industry_major": num["industry_major"],
                                    "org_sector": sector, "occupation_major": num["occupation_major"],
                                    "org_role": roles, "org_id": org_of, "workplace_area": area_w}, tb,
                  A.AttrKey(seed, "w21b.org.duty", pk3))
    hours = A.call("weekly_hours", {"emp_status": num["emp_status"], "occupation_major": num["occupation_major"],
                                    "sex": sex}, tb, A.AttrKey(seed, "w21b.org.hours", pk3))
    entry = A.call("entry_node", {"kind": kind, "workplace_area": area_w}, tb,
                   A.AttrKey(seed, "w21b.entry", pk3))
    role_layer = np.where(kind == "commuter", "commuter",
                          np.where(np.isin(area, [O.WORKPLACE_AREAS.index("home"), O.WORKPLACE_AREAS.index("stage")]),
                                   "resident_worker_in_area", "resident"))
    w16_kind = A.call("w16_kind", {"persona_kind": np.full(n, "in_area", dtype=object), "role": role_layer}, tb,
                      A.AttrKey(seed, "w21b.w16_kind", pk3))

    # ---- 権利台帳
    poi = guard.read_parquet(world / "w6_poi.parquet", WORLD_COLUMNS["w6_poi.parquet"])
    poi_cell = np.array([g.place_to_cell.get(p, -1) for p in poi["place_id"]], dtype=np.int64)
    owner = O.store_owners(np.asarray(poi["cat"], dtype=object), np.asarray(poi["subcat"], dtype=object),
                           np.asarray(poi["building_id"], dtype=object), o_ind,
                           np.asarray(org["building_id"], dtype=object))
    rights = _rights(pid, seated, org_of, roles, hours, owner, hh, persons)
    # ---- 関係
    rel = _relations(pid, hid, deps, org_of)

    # ================================================================ 段 5
    people_m = {"person_id": pid, "kind": kind, "age": age, "sex": sex, "household_id": hid,
                "relation": np.r_[np.asarray(persons["relation"], dtype=object), np.full(n_com, "", dtype=object)],
                "emp_status": num["emp_status"], "occupation_major": num["occupation_major"]}
    money_p, money_h = M.build_money(people_m, hh, tb, seed)

    # ================================================================ 段 6
    pk = A.AttrKey(seed, "w21b.prior.years", pk3)
    rp = np.r_[r_codes["residence_period"], np.full(n_com, -1)]
    years = A.call("residence_years", {"residence_period": rp, "age": age}, tb, pk)
    cap = A.call("place_capacity", {"age": age}, tb, A.AttrKey(seed, "w21b.prior.capacity", pk3))
    known = A.call("known_places", {"place_capacity": cap, "residence_years": years}, tb, pk)
    dist = np.load(io.BytesIO(guard.read_bytes(world / "w3_cell_dist.npy")), allow_pickle=False)
    station_cells = _station_cells(guard, world, g)
    mode, path = P.commute_facts(kind, area_w, hcell, wcell, dist, station_cells)
    young = _young_child_households(hid, age)
    pl, pcounts = P.familiar_places(seed, {"person_id": pid, "kind": kind, "age": age, "home_cell": hcell,
                                           "work_cell": wcell, "workplace_area": area_w, "known_places": known,
                                           "place_capacity": cap, "young_child_household": young},
                                    {"poi_id": np.asarray(poi["poi_id"], dtype=object), "cat": poi["cat"],
                                     "subcat": [x or "" for x in poi["subcat"]], "cell": poi_cell}, dist,
                                    arm=params.affinity)

    # ================================================================ 段 7
    pop, missing = X.muni_population(guard, org4["codes"].tolist())
    ring_tg = T.make_targets(g.ct, g.ward, np.clip(1.0 - g.coverage, 0.0, 1.0))
    # 〔検収 L6〕輪の和=段 1 の枠の行(区の総数 − 住民の体の数)に合わせる(町丁目の目標の和との差=住民の整数化の差)
    ring_row = next(r for r in frame["rows"] if r["layer"] == "ward_rest_residents")
    ring_frame = float(ring_row["value"][0])
    oinfo = {"origins": int(len(org4["codes"])), "origins_in_2025_table": int(len(org4["codes"]) - len(missing)),
             "missing_origin_codes": sorted(str(c) for c in missing),
             "remapped_2020_codes": dict(sorted((k, v[0]) for k, v in X.MUNI_CODE_2025.items())),
             "ring_targets_sum": round(float(np.clip(ring_tg.age16_sex, 0.0, None).sum()), 3),
             "ring_frame_value": ring_frame}
    strata = X.outside_strata(org=org4, pop=pop, missing=missing,
                              commuters={"origin_muni": ca["origin_muni"], "sex": ca["sex"], "age": ca["age"]},
                              ring_age16_sex=ring_tg.age16_sex, ring_keys=[g.keys80[i] for i in ring_tg.stage_idx],
                              frame_rows=frame["rows"], ring_total=ring_frame)
    ohh = X.outside_households(guard, org4["codes"].tolist(), org4["names"].tolist())

    # ================================================================ 出力の列
    people_cols = {
        "person_id": pid.astype(np.int32), "kind": kind, "persona_kind": np.full(n, "in_area", dtype=object),
        "role": role_layer.astype(object), "w16_kind": w16_kind.astype(np.int8), "sex": sex.astype(np.int8),
        "age": age.astype(np.int16), "household_id": hid.astype(np.int32),
        "relation": people_m["relation"],
        "home_chome_key": np.r_[np.asarray(persons["chome_key"], dtype=object), np.full(n_com, "", dtype=object)],
        "home_cell": hcell.astype(np.int32), "origin_muni": origin,
        "labour_status": WA.words(num["labour_status"], A.LABOUR),
        "emp_status": st_words, "employment_status": employment_status,
        "industry_major": WA.words(num["industry_major"], A.INDUSTRY_MAJORS), "industry_key": industry_key.astype(object),
        "occupation_major": WA.words(num["occupation_major"], A.OCCUPATION_MAJORS),
        "workplace_area": area_w, "work_chome_key": np.where(wchome >= 0, np.array(stage_keys + [""], dtype=object)
                                                               [np.where(wchome >= 0, wchome, len(stage_keys))], ""),
        "work_cell": wcell.astype(np.int32), "seat_status": status,
        "org_index": org_of.astype(np.int32),
        "org_code": np.where(seated, np.asarray(org["org_id"], dtype=object)[np.clip(org_of, 0, None)], ""),
        "org_role": roles, "department_id": deps["department"].astype(np.int32),
        "is_org_head": deps["is_org_head"], "is_dept_head": deps["is_dept_head"],
        "supervisor_id": np.where(deps["supervisor"] >= 0, pid[np.clip(deps["supervisor"], 0, None)], -1).astype(np.int32),
        "duty_role": duty, "weekly_hours_hint": hours.astype(np.float32), "entry_node": entry,
        "commute_mode": mode, "commute_path_m": path.astype(np.int32),
        "residence_years": years.astype(np.float32), "place_capacity": cap.astype(np.int16),
        "known_places": known.astype(np.int32), "familiar_listed": pcounts["listed_places"].astype(np.int16),
        "familiar_outside": pcounts["outside_places"].astype(np.int16), "synthetic": np.zeros(n, dtype=bool),
    }
    org_cols = _org_table(org, o_ind, o_seats, filled, deps, org_of, pid, o_cell, owner, g)
    checks = _checks(seat_report, N_c, R_c, M_c, s_stage, workers_in_ward, emp80, ward_emp, miss28, status, area_w,
                     kind, industry_key, st_words, seated, roles, duty, rights, rel, money_p, money_h, tb, people_cols,
                     pl, pcounts, strata, ohh, guard, world, deps, tinfo, n, oinfo)

    def tbl(d: Mapping[str, Any]) -> dict[str, Any]:
        return {k: (pa.array(v.tolist(), type=pa.string()) if isinstance(v, np.ndarray) and v.dtype == object
                    and k not in ("count", "count_low", "count_high", "inflow_weight", "appearance_prob", "since_ns",
                                  "until_ns", "cause") else v) for k, v in d.items()}

    outputs = [
        C.write_parquet(out, OUTPUTS_B[0], tbl(people_cols)),
        C.write_parquet(out, OUTPUTS_B[1], tbl(org_cols)),
        C.write_parquet(out, OUTPUTS_B[2], tbl(rights)),
        C.write_parquet(out, OUTPUTS_B[3], tbl(rel)),
        C.write_parquet(out, OUTPUTS_B[4], tbl(money_p)),
        C.write_parquet(out, OUTPUTS_B[5], tbl(money_h)),
        C.write_parquet(out, OUTPUTS_B[6], tbl(pl)),
        C.write_parquet(out, OUTPUTS_B[7], _nullable(strata)),
        C.write_parquet(out, OUTPUTS_B[8], tbl(ohh)),
        C.write_json(out, OUTPUTS_B[9], checks),
    ]
    build_hash = C.sha256_bytes("".join(o["sha256"] for o in outputs).encode("utf-8"))
    rparams = {"seed": seed, "division_arm": params.division_arm, "affinity": params.affinity,
               "seat_roles": params.seat_roles,
               "attr_fns": A.registry_versions(stages=(4, 5, 6)),
               "rng_domains": ["w21b.org.<手順>", "w21b.commuter.<関数>", "w21b.entry", "w21b.money.<量>",
                               "w21b.prior.<側か量>", "w21b.w16_kind"],
               "constants": {"place_capacity_mean": A.PLACE_CAPACITY_MEAN, "place_capacity_cv": A.PLACE_CAPACITY_CV,
                             "rank_exponent": A.RANK_EXPONENT, "heaps_exponent": A.HEAPS_EXPONENT,
                             "capacity_window_weeks": A.CAPACITY_WINDOW_WEEKS,
                             "distance_decay_m": P.DISTANCE_DECAY_M, "side_draw_factor": P.SIDE_DRAW_FACTOR,
                             "adult_age": M.ADULT_AGE, "credit_min_age": A.CREDIT_MIN_AGE}}
    read_files = dict(sorted(guard.files_read.items()))
    srcs = [{"sid": s.sid, "title": s.title, "stat_inf_id": s.stat_inf_id, "path": s.rel, "md5": s.md5,
             "derived": s.derived_rel, "derived_md5": s.derived_md5, "year": s.year, "r116_row": s.r116_row,
             "side": s.side} for s in (*S.SOURCES, *S.SOURCES_B) if s.rel in read_files or
            (s.derived_rel and s.derived_rel in read_files)]
    manifest = {
        "schema": "w21b.manifest/1", "stage": STAGE_B, "stage_version": STAGE_VERSION_B, "population_seed": seed,
        "params": rparams,
        "base": {"asset": BASE_ASSET, "w21_build_hash": base_man["w21_build_hash"],
                 "files": {f: next(o["sha256"] for o in base_man["outputs"] if o["path"] == f) for f in BASE_FILES}},
        "sources": srcs, "verify_side_rows": [r.row for r in S.VERIFY_SIDE], "read": read_files,
        "constants_cited": {"jicc_2026_08": {"holders": A.JICC_HOLDERS, "class_people": list(A.JICC_CLASS_PEOPLE),
                                             "class_mean_yen": list(A.JICC_CLASS_MEAN_YEN), "row": "R-107 §4(引)"},
                            "jnto_2025": {"total": X.JNTO_2025_TOTAL, "row": "R-110 §3-5(引)"},
                            "r80_subordinates": dict(A.R80_SUBORDINATES), "alessandretti_2018": A.PLACE_CAPACITY_MEAN,
                            "song_2010": {"zeta": A.RANK_EXPONENT, "mu": A.HEAPS_EXPONENT}},
        "counts": checks["counts"], "outputs": outputs, "w21b_build_hash": build_hash,
        "expedients": list(W21B_EXPEDIENTS),
    }
    C.write_json(out, MANIFEST_B, manifest)
    res = C.StageResult(stage=STAGE_B, stage_version=STAGE_VERSION_B,
                        input_hash=C.input_hash([guard.paths_read[p] for p in read_files]),
                        param_hash=C.param_hash(rparams), params=rparams, outputs=outputs,
                        catalog_classes=["組織と関係(所属・部署・権利台帳・関係)", "お金(最初の資産)", "開始前の経験(なじみの場所)",
                                         "外の人(層の表)"],
                        expedients=list(W21B_EXPEDIENTS),
                        notes={"w21b_build_hash": build_hash, "counts": checks["counts"]})
    res.gates = [
        C.Gate("people", n, None), C.Gate("commuters", n_com, None),
        C.Gate("person_id_duplicates", int(n - np.unique(pid).size), 0),
        C.Gate("org_heads_with_supervisor", int((deps["is_org_head"] & (deps["supervisor"] >= 0)).sum()), 0),
        C.Gate("members_without_one_supervisor",
               int((seated & ~deps["is_org_head"] & (deps["supervisor"] < 0)).sum()), 0),
        C.Gate("seats_over_capacity", int((filled > o_seats).sum()), 0),
    ]
    C.write_header(out, res)
    return res, manifest


def _nullable(d: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, np.ndarray) and v.dtype == object and k in ("count", "count_low", "count_high",
                                                                      "inflow_weight", "appearance_prob"):
            out[k] = pa.array(v.tolist(), type=pa.float64())
        elif isinstance(v, np.ndarray) and v.dtype == object:
            out[k] = pa.array(v.tolist(), type=pa.string())
        else:
            out[k] = v
    return out


def _station_cells(guard: S.W21Guard, world: Path, g: Any) -> np.ndarray:
    nodes = guard.read_parquet(world / "w12_external_nodes.parquet", WORLD_COLUMNS["w12_external_nodes.parquet"])
    cells: set[int] = set()
    for k, ids in zip(nodes["kind"], nodes["attached_place_ids"]):  # 逐次: 外の口の数ぶん(10)
        if k != "rail":
            continue
        for pidx in json.loads(ids or "[]"):
            c = g.place_to_cell.get(pidx, -1)
            if c >= 0:
                cells.add(int(c))
    return np.array(sorted(cells), dtype=np.int64)


def _young_child_households(hid: np.ndarray, age: np.ndarray) -> np.ndarray:
    h = np.asarray(hid, dtype=np.int64)
    ok = h >= 0
    if not ok.any():
        return np.zeros(h.size, dtype=bool)
    has = np.bincount(h[ok & (np.asarray(age) < 6)], minlength=int(h.max()) + 1) > 0
    return ok & has[np.clip(h, 0, None)]


def _rights(pid: np.ndarray, seated: np.ndarray, org_of: np.ndarray, roles: np.ndarray, hours: np.ndarray,
            owner: np.ndarray, hh: Mapping[str, Any], persons: Mapping[str, Any]) -> dict[str, Any]:
    """権利台帳の開始時点の行(雇用 → 店の持ち主 → 店の賃借 → 住まいの順)。since/until/cause は空欄(開始前から・終わりなし・
    初期状態)。"""
    e = np.flatnonzero(seated)
    poi_j = np.flatnonzero(owner >= 0)
    n_poi = owner.size
    # 住まい(世帯主 → 住まい=世帯の番号)
    h_id = np.asarray(hh["household_id"], dtype=np.int64)
    tenure = np.asarray(hh["tenure"], dtype=object).astype(str)
    rel = np.asarray(persons["relation"], dtype=object).astype(str)
    p_h = np.asarray(persons["household_id"], dtype=np.int64)
    heads = np.flatnonzero(rel == "head")
    head_of = np.full(int(h_id.max()) + 1 if h_id.size else 0, -1, dtype=np.int64)
    head_of[p_h[heads]] = np.asarray(persons["person_id"], dtype=np.int64)[heads]
    tu, tinv = np.unique(tenure, return_inverse=True)
    kind_of = np.array([O.TENURE_RIGHT.get(t, "") for t in tu.tolist()], dtype=object)[tinv]  # 逐次: 語の種類の数
    dw = np.flatnonzero((kind_of != "") & (head_of[h_id] >= 0))
    blocks = [
        ("agent", pid[e], "org", org_of[e], np.full(e.size, "employ", dtype=object),
         "w21b.org:所属(席=W6 経済センサス・人数=国勢調査)", roles[e], hours[e], True, ""),
        ("org", owner[poi_j], "store", poi_j, np.full(poi_j.size, "own", dtype=object),
         "宣言:店の持ち主(同じ建物で業種の合う W6 の組織)", np.full(poi_j.size, "", dtype=object),
         np.full(poi_j.size, np.nan), False, "閉じた表(口の約束 1-5)の所有の対象に店が無い=親の判断"),
        ("store", np.arange(n_poi), "parcel", np.arange(n_poi), np.full(n_poi, "lease", dtype=object),
         "w6_poi(区画にいること)", np.full(n_poi, "", dtype=object), np.full(n_poi, np.nan), True,
         "家賃と貸し手は空欄(BR-RENT-BLANK)"),
        ("agent", head_of[h_id[dw]], "dwelling", h_id[dw], kind_of[dw], "w21_households.tenure(国勢調査 第7-1表)",
         np.full(dw.size, "", dtype=object), np.full(dw.size, np.nan), True, "相手と家賃は空欄"),
    ]
    cols: dict[str, list[np.ndarray]] = {k: [] for k in O.RIGHT_COLUMNS}
    for hk, hidx, ok_, oidx, kd, src, role, hrs, closed, note in blocks:  # 逐次: 塊の数ぶん(4)
        m = len(hidx)
        cols["holder_kind"].append(np.full(m, hk, dtype=object))
        cols["holder_id"].append(np.asarray(hidx, dtype=np.int64))
        cols["object_kind"].append(np.full(m, ok_, dtype=object))
        cols["object_id"].append(np.asarray(oidx, dtype=np.int64))
        cols["kind"].append(np.asarray(kd, dtype=object))
        cols["source"].append(np.full(m, src, dtype=object))
        cols["role"].append(np.asarray(role, dtype=object))
        cols["weekly_hours_hint"].append(np.asarray(hrs, dtype=np.float64))
        cols["in_closed_table"].append(np.full(m, closed, dtype=bool))
        cols["note"].append(np.full(m, note, dtype=object))
    out: dict[str, Any] = {k: np.concatenate(v) for k, v in cols.items() if v}
    m = out["holder_id"].size
    out["right_id"] = np.arange(m, dtype=np.int64)
    out["since_ns"] = pa.nulls(m, type=pa.int64())
    out["until_ns"] = pa.nulls(m, type=pa.int64())
    out["counterparty_kind"] = np.full(m, "", dtype=object)
    out["counterparty_id"] = np.full(m, -1, dtype=np.int64)
    # 〔検収 L9〕engine の cause は 1-3 の出来事の id (t_ns, seq)=同じ形の構造の列(初期状態=全部 null)
    out["cause"] = pa.nulls(m, type=pa.struct([("t_ns", pa.int64()), ("seq", pa.int64())]))
    out["weekly_hours_hint"] = out["weekly_hours_hint"].astype(np.float32)
    return {k: out[k] for k in O.RIGHT_COLUMNS}


def _relations(pid: np.ndarray, hid: np.ndarray, deps: Mapping[str, np.ndarray], org_of: np.ndarray
               ) -> dict[str, Any]:
    """関係の行(有向)。家族=同じ世帯(種別 1)・同僚=同じ組織の同じ部署(種別 2)・上司と部下=部署の長 ↔ 組織の長(種別 2・
    部署が違うときだけ)。強さ・回数・最初と最後は空欄(ラン開始時にエンジンが作る)。"""
    hu, hv = O.relation_pairs(hid)
    du, dv = O.relation_pairs(deps["department"])
    sup = deps["supervisor"]
    s_from = np.flatnonzero((sup >= 0) & (deps["department"] >= 0))
    diff = deps["department"][s_from] != deps["department"][np.clip(sup[s_from], 0, None)]
    su = s_from[diff]
    sv = sup[su]
    u = np.concatenate([hu, du, su, sv])
    v = np.concatenate([hv, dv, sv, su])
    kind = np.concatenate([np.full(hu.size, 1), np.full(du.size + 2 * su.size, 2)]).astype(np.int8)
    basis = np.concatenate([np.full(hu.size, "household", dtype=object), np.full(du.size, "department", dtype=object),
                            np.full(su.size, "reports_to", dtype=object), np.full(su.size, "manages", dtype=object)])
    order = np.lexsort((v, u, kind))
    org = np.where(kind[order] == 2, org_of[u[order]], -1)
    return {"u": pid[u[order]].astype(np.int32), "v": pid[v[order]].astype(np.int32), "kind": kind[order],
            "kind_word": np.where(kind[order] == 1, "household", "work").astype(object), "basis": basis[order],
            "org_index": org.astype(np.int32),
            "department_id": np.where(kind[order] == 2, deps["department"][u[order]], -1).astype(np.int32)}


def _org_table(org: Mapping[str, Any], o_ind: np.ndarray, o_seats: np.ndarray, filled: np.ndarray,
               deps: Mapping[str, np.ndarray], org_of: np.ndarray, pid: np.ndarray, o_cell: np.ndarray,
               owner: np.ndarray, g: Any) -> dict[str, Any]:
    K = o_seats.size
    heads = np.flatnonzero(deps["is_org_head"])
    head = np.full(K, -1, dtype=np.int64)
    head[org_of[heads]] = pid[heads]
    ch = SH.assign_points_to_polygons(np.asarray(org["x"], dtype=np.float64), np.asarray(org["y"], dtype=np.float64),
                                      g.polys)
    ndep = np.zeros(K, dtype=np.int64)
    nd = deps["n_departments_of_org"]
    ndep[: nd.size] = nd
    return {
        "org_index": np.arange(K, dtype=np.int32), "org_code": np.asarray(org["org_id"], dtype=object),
        "industry_key": o_ind.astype(object), "sector_detail": np.asarray(org["sector_detail"], dtype=object),
        "size_band": np.asarray(org["size_band"], dtype=object), "seats": o_seats.astype(np.int32),
        "filled": filled.astype(np.int32), "vacant": (o_seats - filled).astype(np.int32),
        "departments": ndep.astype(np.int16), "head_person_id": head.astype(np.int32),
        "cell": o_cell.astype(np.int32), "building_id": np.asarray(org["building_id"], dtype=object),
        "chome_key": np.where(ch >= 0, np.array(list(g.keys80) + [""], dtype=object)[np.where(ch >= 0, ch, 80)], ""),
        "stores_owned": np.bincount(owner[owner >= 0], minlength=K).astype(np.int16),
    }


def _commute_check(people: Mapping[str, Any]) -> dict[str, Any]:
    """通勤の手段の数と、道のりの 10/50/90% 点〔検収 L2〕=種類で分ける: 歩き(住民の家 → 舞台の勤め先)・外から来て働く人
    (駅 → 勤め先)・舞台の外で働く住民(家 → 駅)。"""
    mode = np.asarray(people["commute_mode"]).astype(str)
    kind = np.asarray(people["kind"]).astype(str)
    path = np.asarray(people["commute_path_m"], dtype=np.int64)
    groups = {"walk_resident_home_to_work": (mode == "walk"),
              "rail_commuter_station_to_work": (mode == "rail") & (kind == "commuter"),
              "rail_resident_home_to_station": (mode == "rail") & (kind == "resident")}
    q = {}
    for name, m in groups.items():  # 逐次: 種類の数(3)
        m = m & (path >= 0)
        if m.any():
            q[name] = {"n": int(m.sum()), "p10_p50_p90": [int(x) for x in np.percentile(path[m], [10, 50, 90])]}
    return {"mode": WC.counts_by(mode), "path_m": q}


def _checks(seat_report, N_c, R_c, M_c, s_stage, workers_in_ward, emp80, ward_emp, miss28, status, area_w, kind,
            industry_key, st_words, seated, roles, duty, rights, rel, money_p, money_h, tb, people, pl, pcounts,
            strata, ohh, guard, world, deps, tinfo, n, oinfo) -> dict[str, Any]:
    d62, it62, rows62 = S.read_derived_rows(guard, "ecen21_t6_2")
    try:
        w16h = json.loads(guard.read_bytes(world / "W16.header.json").decode("utf-8"))
        w16_duty = w16h.get("notes", {}).get("duty_role_counts", {})
    except (FileNotFoundError, OSError, S.MissingSourceError):
        w16_duty = {}
    hh_type = np.where(np.asarray(money_h["hh_type"]).astype(str) == "single", 2, 1)
    sv = np.asarray(money_h["savings"], dtype=np.int64)
    cls = A.savings_class(tb, np.maximum(sv, 0))
    wage = np.asarray(money_p["wage_monthly"], dtype=np.int64)
    occ = np.asarray(people["occupation_major"]).astype(str)
    sexes = np.asarray(people["sex"], dtype=np.int64)
    gen = np.isin(np.asarray(people["emp_status"]).astype(str), ["regular", "dispatched"]) & (wage > 0)
    wage_med = {}
    for oi, oname in enumerate(A.OCCUPATION_MAJORS[:11]):  # 逐次: 職業 11 × 男女
        for s in range(2):
            m = gen & (occ == oname) & (sexes == s)
            if m.sum() >= 30:
                wage_med[f"{oname}|{s}"] = {"n": int(m.sum()), "sim_median": int(np.median(wage[m])),
                                            "t18_median_all_forms": int(tb.wage_median[oi, s])}
    rank = np.asarray(pl["rank"], dtype=np.float64)
    share = np.asarray(pl["visit_share"], dtype=np.float64)
    cap = np.asarray(people["place_capacity"], dtype=np.float64)
    yrs = np.asarray(people["residence_years"], dtype=np.float64)
    known = np.asarray(people["known_places"], dtype=np.float64)
    res = np.asarray(people["kind"]).astype(str) == "resident"
    bins = np.array([0.0, 0.5, 1, 2, 5, 10, 20, 40, 120])
    yb = np.digitize(yrs[res & np.isfinite(yrs)], bins) - 1
    heaps = []
    for b in range(bins.size - 1):  # 逐次: 年の区分(8)
        m = yb == b
        if m.sum() >= 30:
            heaps.append({"years": [float(bins[b]), float(bins[b + 1])], "n": int(m.sum()),
                          "mean_years": round(float(yrs[res & np.isfinite(yrs)][m].mean()), 3),
                          "mean_known": round(float(known[res & np.isfinite(yrs)][m].mean()), 2)})
    layers = {}
    lay = np.asarray(strata["layer"]).astype(str)
    cnt = strata["count"]
    for L in np.unique(lay).tolist():  # 逐次: 層の数ぶん(≤ 10)
        m = lay == L
        vals = [x for x, k in zip(cnt.tolist(), m.tolist()) if k and x is not None]
        lo = [x for x, k in zip(strata["count_low"].tolist(), m.tolist()) if k and x is not None]
        hi = [x for x, k in zip(strata["count_high"].tolist(), m.tolist()) if k and x is not None]
        layers[L] = {"rows": int(m.sum()), "count_sum": round(float(sum(vals)), 1) if vals else None,
                     "count_low_sum": round(float(sum(lo)), 1) if lo else None,
                     "count_high_sum": round(float(sum(hi)), 1) if hi else None,
                     "has_bodies": bool(np.asarray(strata["has_bodies"])[m].any())}
    n_com = int((np.asarray(kind).astype(str) == "commuter").sum())
    counts = {"residents": int(n - n_com), "commuters": n_com, "people": int(n),
              "seated": int(np.asarray(seated).sum()), "rights_rows": int(np.asarray(rights["right_id"]).size),
              "relation_rows": int(np.asarray(rel["u"]).size), "prior_place_rows": int(np.asarray(pl["rank"]).size),
              "outside_rows": int(lay.size), "outside_household_rows": int(np.asarray(ohh["households"]).size)}
    return {
        "schema": "w21b.checks/1",
        "note": "段 8 の先取り・合否は付けない。構築に使った表と法則(なじみの場所)は点検と診断だけで検証の証拠にしない(§10-3)",
        "counts": counts,
        "workers": {"workers_in_ward_census": workers_in_ward, "stage_share_ecen": round(s_stage, 6),
                    "stage_workers_target": int(N_c.sum()), "residents_working_in_stage": int(R_c.sum()),
                    "commuters_made": int(M_c.sum()), "chome_where_residents_exceed_target": int((R_c > N_c).sum()),
                    "ecen_ward_employees": ward_emp, "ecen_matched_employees": round(float(emp80.sum()), 1),
                    "ecen_rows_unmatched": list(miss28)},
        "seats": {"by_industry": seat_report,
                  "total": {k: int(sum(v[k] for v in seat_report.values())) for k in
                            ("seats", "people", "filled", "vacant", "overflow")},
                  "seat_status": WC.counts_by(status), "workplace_area": WC.counts_by(area_w)},
        "roles": {"org_role": WC.counts_by(np.asarray(roles)[np.asarray(seated)]),
                  "role_vs_ecen_6_2": WC.role_distribution(industry_key, st_words, seated, rows62, it62),
                  "departments": int(deps["department"].max()) + 1 if (deps["department"] >= 0).any() else 0,
                  "org_heads": int(deps["is_org_head"].sum()), "dept_heads": int(deps["is_dept_head"].sum())},
        "duty_role": {"w21b": WC.counts_by(np.asarray(duty)[np.asarray(duty).astype(str) != ""]),
                      "w16_inventory_reference": w16_duty,
                      "note": "W16 の在庫(v1 の L5)とは別に作った=同じ人を二重に数えうる(段 10 で W16 の行を外す)"},
        "rights": {"by_kind": WC.counts_by(np.char.add(np.char.add(np.asarray(rights["kind"]).astype(str), "|"),
                                                        np.asarray(rights["object_kind"]).astype(str))),
                   "not_in_closed_table": int((~np.asarray(rights["in_closed_table"])).sum()),
                   "licence_rows": 0, "licence_note": "営業許可は区のオープンデータが未取得=0 行(BR-RIGHTS-LICENCE-BLANK)"},
        "relations": {"by_basis": WC.counts_by(rel["basis"]),
                      "degree_household": WC.degree_summary(np.asarray(rel["u"])[np.asarray(rel["kind"]) == 1], n),
                      "degree_work": WC.degree_summary(np.asarray(rel["u"])[np.asarray(rel["kind"]) == 2], n)},
        "money": {"savings_class_vs_tokyo": WC.savings_class_fit(cls, hh_type, tb.sav_freq, tb.sav_rate_cls, sv == 0),
                  "household_savings_median_yen": int(np.median(sv[sv >= 0])) if (sv >= 0).any() else None,
                  "household_debt_holder_share": round(float((np.asarray(money_h["debt"]) > 0).mean()), 4),
                  "wage_median_by_occupation_sex": wage_med,
                  "wage_blank_employed": int(((wage < 0) & np.isin(np.asarray(people["labour_status"]).astype(str),
                                                                    ["employed"])).sum()),
                  "consumer_credit_holder_share_20plus": round(float(
                      (np.asarray(money_p["consumer_credit"])[np.asarray(people["age"]) >= 20] > 0).mean()), 4),
                  "blank_columns": ["wallet_cash", "card_holding", "account_holding"], "tables": tinfo},
        "prior": {"capacity_mean": round(float(cap.mean()), 3), "capacity_sd": round(float(cap.std()), 3),
                  "capacity_quantiles_10_50_90": [int(x) for x in np.percentile(cap, [10, 50, 90])],
                  "listed_mean": round(float(np.asarray(pcounts["listed_places"]).mean()), 3),
                  "outside_mean": round(float(np.asarray(pcounts["outside_places"]).mean()), 3),
                  "short_of_target_people": int((np.asarray(pcounts["short_of_target"]) > 0).sum()),
                  "short_of_target_places": int(np.asarray(pcounts["short_of_target"]).sum()),
                  "rank_share_loglog_slope": WC.loglog_slope(rank, share),
                  "known_vs_years": heaps,
                  "known_vs_years_loglog_slope": WC.loglog_slope(np.array([h["mean_years"] for h in heaps]),
                                                                 np.array([h["mean_known"] for h in heaps])),
                  "note": "法則は構築に使った=再現は診断だけ(§10-3・検証に使わない)"},
        "outside": {"layers": layers, **oinfo},
        "commute": _commute_check(people),
        "blanks": {c: int((np.asarray(people[c]).astype(str) == "").sum()) for c in
                   ("industry_key", "org_code", "org_role", "duty_role", "entry_node", "origin_muni")},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.pop.w21_build_b")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--base", type=Path, default=None, help="段 1〜3 の資産(既定 <data>/world/v2_stage_4-1・読むだけ)")
    ap.add_argument("--world", type=Path, default=None, help="読む世界資産(既定 <data>/world/v2・読むだけ)")
    ap.add_argument("--seed", type=int, default=W.DEFAULT_SEED)
    ap.add_argument("--division-arm", choices=("off", "on"), default="off")
    ap.add_argument("--affinity", choices=P.AFFINITY_ARMS, default="lifestage")
    ap.add_argument("--seat-roles", choices=("on", "off"), default="on")
    a = ap.parse_args(argv)
    data = a.data.resolve()
    world = (a.world or a.data / "world" / "v2").resolve()
    base = (a.base or a.data / "world" / BASE_ASSET).resolve()
    try:
        check_out_b(data, a.out.resolve(), world, base)
    except ProtectedOutputErrorB as e:
        print(f"[W21b] 止めた(何も書いていない): {e}", file=sys.stderr)
        return 2
    res, man = build_b(data, a.out.resolve(), base=base, world=world, seed=a.seed,
                       params=ParamsB(division_arm=a.division_arm == "on", affinity=a.affinity,
                                      seat_roles=a.seat_roles == "on"))
    print(f"[W21b] people={man['counts']['people']} commuters={man['counts']['commuters']} "
          f"w21b_build_hash={man['w21b_build_hash']}")
    return 0 if res.all_passed else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
