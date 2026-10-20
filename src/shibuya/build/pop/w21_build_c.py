"""W21 段 8〜9 と段 10 の材料(第 4 期 4-1「点検・見せ方・差し替えの材料」)の組み立て。版 1.2.0。

    python -m shibuya.build.pop.w21_build_c --out data/world/v2_stage_4-1c --data data
        [--base data/world/v2_stage_4-1b] [--world data/world/v2] [--seed 20260909]

- 段 1〜7 の資産(``--base``=``v2_stage_4-1b``=段 1〜3 の写しと段 4〜7 の出力)を**読むだけ**で使い(manifest の sha256 と
  照らす)、段 8〜9 の出力と段 10 の材料を ``--out`` に書く。本体の ``data/world/v2``・``--world``・``--base``・段 1〜3 の資産
  ``v2_stage_4-1`` には書かない(:func:`check_out_c`・読み口の守り)。W21 は ``build.run`` の段に入らない=本体の build_hash は
  動かない(差し替えは段 10=4-3・別の発注)。
- 段 8 点検(``w21_check``・合否なし)・段 9 見せ方(``w21_persona``=事実から決まった形で組み立てる・LLM に書かせない)・
  段 10 の材料(``w21_port10``・``build.sched.w20_w21_port``)・関数(``attr_fns`` の段 9〜10)・計器(``w21_checks``)。
- 出力(:data:`OUTPUTS_C`)と ``w21c_manifest.json``・``W21c.header.json``。``w21c_build_hash``=出力の sha256 を連ねた文字列の
  sha256。時刻など決まらない値は書かない(2 回組んで一致)。人物の文は資産の parquet にだけ書く(記録・計器には写さない)。
- 近似の宣言は :data:`W21C_EXPEDIENTS`(つなぎの台帳に 1 行ずつ)。

逐次ループ宣言(P4): 段の手順の数ぶん。各手順の宣言は各モジュール。体ごとの for は無い。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any, Final, Mapping

import numpy as np
import pyarrow as pa

from ..geo import common as C
from ..sched import w20_w21_port as WP
from . import attr_fns as A
from . import w21_attrs as WA
from . import w21_build as W
from . import w21_check as K
from . import w21_checks as WC
from . import w21_outside as X
from . import w21_persona as P
from . import w21_port10 as T10
from . import w21_sources as S

__all__ = ["STAGE_C", "STAGE_VERSION_C", "OUTPUTS_C", "MANIFEST_C", "BASE_FILES_C", "W21C_EXPEDIENTS", "OWN_ASSET_C",
           "BASE_ASSET_C", "STAGE13_ASSET", "WORLD_COLUMNS_C", "VERIFY_SIDE_LANGUAGE", "ProtectedOutputErrorC",
           "check_out_c", "build_c", "load_inputs", "persona_facts", "language_columns", "main"]

STAGE_C: Final[str] = "W21c"
#: 1.2.0 → 1.3.0(第 4 期 4-3 段 10・親の判断 仮-33: 地位の分けは段 4(W21b 1.2.0)へ移した=本段は分けの記録と数え直しの
#: 写しの検査だけ (2)・型の無い言語は日本語の型で代えて印 (7)・通う駅の口の路線を文に (9)・W20 の口は 8 区分から第 31/36 表の
#: 行へ直接 (4)・電車で通う人の片道は段 6 の道のり (4))。
STAGE_VERSION_C: Final[str] = "1.3.0"
#: 段 10 の差し替えの資産の置き場の名(段 8〜10 を組み直してここにも書ける=``check_out_c``)。
SWAP_ASSET_C: Final[str] = "v2_stage_4-3"
OUTPUTS_C: Final[tuple[str, ...]] = (
    "w21_persona_short.parquet", "w21_persona_long.parquet", "w21_check.json", "w21c_w20_attributes.parquet",
    "w21c_status_split.parquet", "w21c_rights_store_staff.parquet", "w21c_w16_keep.json", "w21_checks_c.json",
)
MANIFEST_C: Final[str] = "w21c_manifest.json"
#: 段 1〜7 の資産のうち読むもの(段 4〜7 は ``w21b_manifest.json``・段 1〜3 は ``w21_manifest.json`` の sha256 と照らす)。
BASE_FILES_C: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "w21b_manifest.json": ("w21_people.parquet", "w21_org.parquet", "w21_rights_initial.parquet", "w21_money.parquet",
                           "w21_money_households.parquet", "w21_prior_places.parquet"),
    "w21_manifest.json": ("w21_persons.parquet", "w21_households.parquet"),
})
OWN_ASSET_C: Final[str] = "v2_stage_4-1c"
BASE_ASSET_C: Final[str] = "v2_stage_4-1b"
STAGE13_ASSET: Final[str] = "v2_stage_4-1"
#: 言語と国籍の**検証側の区分**の取得物の名の語(R-110 §3-5 の「検証の候補(言語の結果)」=受入環境のアンケート・行動特性
#: 調査の満足度)。台帳(``SOURCES_C``)に無い=読み口が開く前に止める。組み立てが読んだファイルにこの語が無いことを門で数える。
VERIFY_SIDE_LANGUAGE: Final[tuple[str, ...]] = ("mlit_ukeire", "inbound_behavior")
#: 世界資産から読む列(W16 は在庫の比べと段 10 の表だけ=種別・担当・複製と多様性の属性)。
WORLD_COLUMNS_C: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "w6_org.parquet": ("name", "industry_key", "employees"),
    "w6_poi.parquet": ("name", "cat", "subcat"),
    "w16_population.parquet": ("kind", "age", "sex", "industry_key", "duty_role", "household_id", "home_cell",
                               "work_cell", "synthetic"),
    # 〔1.3.0〕通う駅の口の路線の名(構築側の欄だけ=乗降人員の欄は読まない)
    "w12_external_nodes.parquet": ("node_id", "kind", "lines"),
})

#: 段 8〜10 の近似の宣言(つなぎの台帳の行と 1 対 1)。
W21C_EXPEDIENTS: Final[tuple[str, ...]] = (
    "国籍=住民の外国人だけを渋谷区の国籍の人数の比(東京都 外国人人口 第3表=住民基本台帳 2026-01-01)で引く・年齢と男女で条件づけない(在留外国人統計 T2 の年齢 × 男女は取り出していない)・外から来て働く人の国籍は空欄(材料なし)",
    "第一言語=国籍 → 主な言語の写像(渋谷区の上位 20 の国籍だけ・フィリピン・インド・シンガポールとほかの国は空欄)=未リサーチ(母語の公的な統計は無い=R-110 §3-3)",
    "日本語の会話の程度=在留外国人に対する基礎調査 令和 6 年度の国籍別の 6 段の割合(R-110 §3-2 の引)で 18 歳以上だけ引く・表に無い国籍は「その他」の行・韓国の行は特別永住者を除く表",
    "人物の文の言語=第一言語が日本語か英語の人はその言語の型・第一言語も国籍も空欄の人(外から来て働く人)は日本語の型・ほかの言語の人と外国籍で第一言語が空欄の人は日本語の型で代えて印を付ける(lang_basis=substitute_ja・本当の第一言語は欄と人物の行に残る=段 10 の親の判断 仮-33 (7))",
    "人物の文の型(行の並びと語の表)=自前: 年齢は 13 歳未満は歳・ほかは十年ごとの前半/後半・人数と年数は漢数字か英語の綴り・時間と分は日本語の型だけ数字・お金は 2 桁の有効数字・1 億円以上は万円の単位・勤め先の種類と町丁目の名は英語の型でも日本語のまま",
    "短い版=人物・暮らし・仕事と学校・通勤・お金・なじみの場所の上位 3・長い版=短い版に家族・職場・勤め先・住まい・お金(詳しく)・ほかのなじみの場所・言葉の行を足す(TIPI-J の行は腕のときだけ)=自前",
    "通勤の分=歩く道のり ÷ 1.34 m/s(Weidmann の自由速度=engine.geometry の参照値と同じ値・attr_fns.walk_seconds)・人物の文は分に四捨五入(丸めた言葉)・W20 の片道は分に切り上げ(整数の分)・目安のトークン=日本語は字数 × 1.0(6-1 の器と同じ)・英語は字数 ÷ 4(未計測)",
    "同居人の続き柄=世帯主から見た続き柄の組 → 本人から見た区分の表(決まらない組は親族か同居人)=自前",
    "権利台帳の体 → 店の雇用の行=店の持ち主の組織に所属した体を組織の店へ順に振る(組織の長 → 部署の長 → 人の番号・店が 2 つ以上なら順に回す)・持ち主の無い店は行なし",
    "W20 への口=W21 の人の表 → Attributes(職業は occupation_major・担当は DUTY_ROLE_SPEC と DUTY_ROLE_SPEC_W21 の鍵・地位は W21 の 8 区分から第 31/36 表の行へ直接=家庭内職者は雇人のない業主の行・パートは第 31 表の非正規の按分から派遣社員を除いた 4 行の重み・歩く人の通勤の分=道のり ÷ 1.34 m/s・電車の人は空欄=W20 の 30 分(舞台の中の道のりだけでは数分になる=所要時間の表が構築側に入る段まで)・学校のセルは無い・認定こども園と保育園は授業でない・働く在学者は勤務を先に)",
    "W21 用の担当の語の表 DUTY_ROLE_SPEC_W21 の 4 語(店長・補充・配送作業員・警備員)の職業・産業・中分類・場所・交替制の当てはめ(W20 の DUTY_ROLE_SPEC は土台のまま=W20cal の param_hash は動かない)",
    "点検の比べ方=舞台の分布を区全体の表の形と比べる(従業地 第15-1表・2025 第15-1表・第10表・第6-2表)・W21 の夫婦=世帯主と配偶者だけ・子=続き柄が子",
    "多様性の属性=年齢 5 歳・男女・産業の語・世帯の人数・家のセル・勤め先のセル・ペアの距離=20 万組(Philox の鍵)",
    "通う駅の口=電車の人の通勤の行に W12 の鉄道の外の口の路線の名(・でつなぐ)を足す(区別の事実=段 10 の親の判断 仮-33 (9)・路線の名は英語の型でも日本語のまま)・路線は W21b の駅の口(大都市交通センサスの路線別の流入の比で引いた=常住地からの経路ではない=同じ文の常住地と食い違いうる・常住地 → 路線の材料が無い)・常住地の市区町村の中の場所は材料が無い",
)
#: 段 10 に結ぶ宣言(つなぎの台帳の remove_at=4-3)の番号(0 から)。〔1.3.0〕段 10 で決めた=4-3 に結ぶ宣言は無い(置き場・W16 の在庫の案=removed・地位の分け=W21b へ・体 → 店と W20 の口と 4 語=外す段を改めた=記録 pop43)。
STAGE10_ROWS_OF_DECLARATIONS: Final[tuple[int, ...]] = ()


class ProtectedOutputErrorC(ValueError):
    """``--out`` が本体の v2・読む世界資産・段 1〜7 の資産・既存の置き場の中を指している(何も書かずに止める)。"""


def check_out_c(data: Path, out: Path, world: Path, base: Path, *, in_place: bool = False) -> None:
    """出力先の検査: 本体の ``data/world/v2``・``--world``・``--base``(段 1〜7)・段 1〜3 の資産の中と、``data/world`` の下の
    既存の置き場(``v2_stage_4-1c*`` と差し替えの置き場を除く)の中なら止める。

    〔1.3.0〕``in_place``=段 10 の差し替えの資産を組むとき(段 4〜7 を同じ置き場に組み直した=``--base`` と ``--out`` が同じ)
    だけ、``--base`` と同じ置き場を許す(``--base`` の下の別の置き場は止める)。"""
    o = Path(out).resolve()
    b = Path(base).resolve()
    roots = ((Path(data) / "world" / "v2").resolve(), Path(world).resolve(),
             *(() if (in_place and o == b) else (b,)),
             (Path(data) / "world" / STAGE13_ASSET).resolve(), (Path(data) / "world" / BASE_ASSET_C).resolve())
    for root in roots:
        if o == root or root in o.parents:
            raise ProtectedOutputErrorC(f"段 8〜10 は本体の v2・世界資産・段 1〜7 の資産の中に書かない: {o.name}")
    wroot = (Path(data) / "world").resolve()
    if wroot in o.parents:
        top = o.relative_to(wroot).parts[0]
        if (wroot / top).exists() and not (top.startswith(OWN_ASSET_C) or top == SWAP_ASSET_C):
            raise ProtectedOutputErrorC(f"段 8〜10 は既存の資産の置き場に書かない: {top}")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_inputs(guard: S.W21Guard, data: Path, base: Path, world: Path) -> SimpleNamespace:
    """段 1〜7 の資産(sha256 を manifest と照らす)・世界資産の列・材料の表を読む。"""
    mans: dict[str, Any] = {}
    files: dict[str, str] = {}
    for man_name, names in BASE_FILES_C.items():  # 逐次: manifest の数(2)
        man = json.loads(guard.read_bytes(base / man_name).decode("utf-8"))
        mans[man_name] = man
        want = {o["path"]: o["sha256"] for o in man["outputs"]}
        for f in names:  # 逐次: ファイルの数(≤ 6)
            sha = _sha(guard.read_bytes(base / f))
            if want.get(f) != sha:
                raise S.MissingSourceError(f"段 1〜7 の資産の sha256 が manifest と違う: {f}")
            files[f] = sha
    rd = {f.rsplit(".", 1)[0]: guard.read_parquet(base / f) for names in BASE_FILES_C.values() for f in names}
    w6o = guard.read_parquet(world / "w6_org.parquet", WORLD_COLUMNS_C["w6_org.parquet"])
    poi = guard.read_parquet(world / "w6_poi.parquet", WORLD_COLUMNS_C["w6_poi.parquet"])
    w16 = guard.read_parquet(world / "w16_population.parquet", WORLD_COLUMNS_C["w16_population.parquet"])
    ext = guard.read_parquet(world / "w12_external_nodes.parquet", WORLD_COLUMNS_C["w12_external_nodes.parquet"])
    entry_lines = {str(nid): "・".join(json.loads(ls or "[]")) for nid, k, ls in
                   zip(ext["node_id"], ext["kind"], ext["lines"]) if k == "rail"}  # 逐次: 外の口の数(10)
    g = W.prepare(guard, data, world)
    tables3, _unk = WA.build_tables(guard, g.keys80, g.tg.stage_idx, g.tg.coverage, g.tg.ratios["r_pop"])
    org4 = X.origins(guard)
    _d62, it62, rows62 = S.read_derived_rows(guard, "ecen21_t6_2")
    juki3 = K.read_jukiki(guard, "jukiki_tokyo_t3_2026_01")
    juki1 = K.read_jukiki(guard, "jukiki_tokyo_t1_2026_07")
    e15 = S.read_derived(guard, "c20_e15")
    b15 = S.read_derived(guard, "c25_b15")
    names3 = sorted(juki3, key=lambda k: (-juki3[k], k))
    tc = A.AttrTablesC(nationality_names=np.array(names3, dtype=object),
                       nationality_w=np.array([juki3[k] for k in names3]),
                       status_split=T10.status_split_table(rows62, it62),
                       md5=dict(sorted(guard.files_read.items()))).freeze()
    chome_names = {str(r["KEY_CODE"]): str(r["S_NAME"]) for r in g.chome}
    origin_names = {str(c): str(nm) for c, nm in zip(org4["codes"].tolist(), org4["names"].tolist())}
    origin_names[S.WARD_CODE] = "渋谷区の別の町"
    return SimpleNamespace(mans=mans, files=files, people=rd["w21_people"], org=rd["w21_org"],
                           rights=rd["w21_rights_initial"], money=rd["w21_money"], money_h=rd["w21_money_households"],
                           places=rd["w21_prior_places"], persons=rd["w21_persons"], households=rd["w21_households"],
                           w6o=w6o, poi=poi, w16=w16, g=g, tables3=tables3, rows62=rows62, it62=it62, juki3=juki3,
                           juki1=juki1, e15=e15, b15=b15, tc=tc, chome_names=chome_names, origin_names=origin_names,
                           entry_lines=entry_lines)


def _pk3(pid: np.ndarray) -> np.ndarray:
    return np.stack([pid, np.zeros(pid.size, np.int64), np.zeros(pid.size, np.int64)], axis=1)


def language_columns(inp: SimpleNamespace, seed: int | str) -> dict[str, np.ndarray]:
    """段 9 の言語の列(国籍・第一言語・日本語の程度=``people`` の並び)。"""
    p = inp.people
    pid = np.asarray(p["person_id"], dtype=np.int64)
    pos = np.full(int(pid.max()) + 1, -1, dtype=np.int64)
    pos[pid] = np.arange(pid.size)
    fo = np.zeros(pid.size, dtype=bool)
    fo[pos[np.asarray(inp.persons["person_id"], dtype=np.int64)]] = np.asarray(inp.persons["is_foreign"], dtype=bool)
    kind = np.asarray(p["kind"], dtype=object)
    k3 = _pk3(pid)
    nat = A.call("nationality", {"kind": kind, "is_foreign": fo}, inp.tc, A.AttrKey(seed, "w21c.nationality", k3))
    fl = A.call("first_language", {"nationality": nat}, inp.tc, A.AttrKey(seed, "w21c.first_language", k3))
    jl = A.call("japanese_level", {"nationality": nat, "age": np.asarray(p["age"], dtype=np.int64)}, inp.tc,
                A.AttrKey(seed, "w21c.japanese_level", k3))
    return {"nationality": nat, "first_language": fl, "japanese_level": jl, "is_foreign": fo}


def persona_facts(inp: SimpleNamespace, lang_cols: Mapping[str, np.ndarray]) -> P.PersonaFacts:
    """段 9 の事実の表(``w21_persona.facts_from_w21`` に資産の表を渡すだけ)。"""
    return P.facts_from_w21(inp.people, inp.persons, inp.households, inp.money, inp.money_h, inp.places, inp.poi,
                            np.asarray(inp.w6o["name"], dtype=object), inp.org, lang_cols, inp.chome_names,
                            inp.origin_names, entry_lines=getattr(inp, "entry_lines", None))


def build_c(data: Path, out: Path, *, base: Path | None = None, world: Path | None = None,
            seed: int | str = W.DEFAULT_SEED, in_place: bool = False) -> tuple[C.StageResult, dict[str, Any]]:
    """段 8〜9 と段 10 の材料を組んで ``out`` に書く。返り値は(見出し, manifest)。"""
    data, out = Path(data), Path(out)
    world = W.source_world(data, world)  # 〔段 10〕差し替えた世界からは組まない=退避の W16 の世界
    base = Path(base) if base is not None else data / "world" / BASE_ASSET_C
    check_out_c(data, out, world, base, in_place=in_place)
    out.mkdir(parents=True, exist_ok=True)
    guard = S.W21Guard.for_build(data, world=world, out=out, extra_dirs=(base,), extra_sources=S.SOURCES_C)
    with guard.active():
        return _build_c(guard, data, out, world, base, seed)


def _school_kind(inp: SimpleNamespace) -> np.ndarray:
    pid = np.asarray(inp.people["person_id"], dtype=np.int64)
    pos = np.full(int(pid.max()) + 1, -1, dtype=np.int64)
    pos[pid] = np.arange(pid.size)
    out = np.full(pid.size, "", dtype=object)
    out[pos[np.asarray(inp.persons["person_id"], dtype=np.int64)]] = np.asarray(inp.persons["school_kind"], dtype=object)
    return out


def _codes(words: Any, vocab: tuple[str, ...]) -> np.ndarray:
    w = np.asarray(words, dtype=object).astype(str)
    u, inv = np.unique(w, return_inverse=True)
    lut = np.array([vocab.index(x) if x in vocab else -1 for x in u.tolist()], dtype=np.int64)  # 逐次: 語の種類
    return lut[np.asarray(inv).reshape(-1)] if w.size else np.zeros(0, dtype=np.int64)


def _build_c(guard: S.W21Guard, data: Path, out: Path, world: Path, base: Path,
             seed: int | str) -> tuple[C.StageResult, dict[str, Any]]:
    inp = load_inputs(guard, data, base, world)
    p = inp.people
    pid = np.asarray(p["person_id"], dtype=np.int64)
    n = int(pid.size)
    kind = np.asarray(p["kind"], dtype=object).astype(str)

    # ================================================================ 段 9 見せ方
    lang = language_columns(inp, seed)
    facts = persona_facts(inp, lang)
    tabs = P.build_tables(facts)
    long_t, short_t = tabs["long"], tabs["short"]
    long_g = P.text_groups(long_t["text"])
    short_g = P.text_groups(short_t["text"])
    built = np.asarray(long_t["text_status"]) == "built"
    # 〔検収 L12〕短い版が長い版の頭か=pyarrow で頭を切り出して比べる(体ごとの Python の呼び出しは無い)
    not_prefix = P.prefix_mismatches(short_t["text"], long_t["text"])

    # ================================================================ 段 10 の材料
    people_w20 = {**{c: p[c] for c in WP.W21_INPUT_COLUMNS if c in p}, "school_kind": _school_kind(inp)}
    attrs = WP.attributes_from_w21(people_w20)
    # 〔1.3.0・仮-33 (2)〕地位の分けは段 4(W21b 1.2.0)が席の前に入れた=ここでは分けない(二重に分けない)。分けの前の地位は
    # W21b の列 ``emp_status_before_split``(地位が変わった人だけ)・分けの後=今の ``emp_status``。数え直しは分けの前と後の両方
    # (後=段 4 の所属と同じ=写しの検査の門)。
    st_after = np.asarray(p["emp_status"], dtype=object).astype(str).astype(object)
    if "emp_status_before_split" not in p:
        raise S.MissingSourceError("段 4〜7 の資産が 1.2.0 より前(地位の分けの列 emp_status_before_split が無い)")
    bsplit = np.asarray(p["emp_status_before_split"], dtype=object).astype(str)
    st_before = np.where(bsplit != "", bsplit, st_after).astype(object)
    o_ind = np.asarray(inp.w6o["industry_key"], dtype=object).astype(str)
    o_seats = np.asarray(inp.w6o["employees"], dtype=np.int64)
    org_b, filled_b, rep_b = T10.seat_recount(p, o_ind, o_seats, inp.rows62, inp.it62, st_before, seed)
    org_a, filled_a, rep_a = T10.seat_recount(p, o_ind, o_seats, inp.rows62, inp.it62, st_after, seed)
    org_index = np.asarray(p["org_index"], dtype=np.int64)
    cand = (kind == "commuter") & (st_before == "self_employed")
    staff = T10.store_staff_rows(p, inp.rights)
    duty = np.asarray(p["duty_role"], dtype=object).astype(str)
    keep = T10.w16_keep_table(inp.w16["kind"], inp.w16["duty_role"], inp.w16["synthetic"],
                              WC.counts_by(duty[duty != ""]),
                              {"residents": int((kind == "resident").sum()), "commuters": int((kind == "commuter").sum())})

    # ================================================================ 段 8 点検
    stage_keys = [inp.g.keys80[i] for i in inp.g.tg.stage_idx]
    check = {
        "schema": K.SCHEMA,
        "note": ("段 8 の点検(合否は付けない=CA8 と同じ診断)。basis が「構築に使った表」の行は点検だけで、検証の証拠にしない"
                 "(設計書 PS6 の注)。人物の文は写さない(数だけ)"),
        "distribution": K.distribution_rows(
            people=p, households=inp.households, tg=inp.g.tg, ward=inp.g.ward, tables3=inp.tables3, e15=inp.e15,
            b15=inp.b15, nationality=lang["nationality"], japanese_level=lang["japanese_level"], juki_t3=inp.juki3,
            juki_t1=inp.juki1, rows62=inp.rows62, items62=inp.it62, stage_keys=stage_keys),
        "doubles": K.double_rows(p, inp.rights, inp.org, keep),
        "uniqueness": K.uniqueness(p, inp.households, inp.places, long_g, short_g),
        "diversity": K.diversity_vs_w16(p, inp.w16, seed=seed),
        "foreigners": {"w21_stage_foreigners": int(lang["is_foreign"].sum()),
                       "ward_basis_2025_imputed": round(float(inp.g.ward.foreign_total), 1),
                       "jukiki_2026_01_ward": round(float(sum(inp.juki3.values())), 1),
                       "jukiki_2026_07_ward_top10_plus_other": round(float(sum(inp.juki1.values())), 1),
                       "note": "人数の錨にどれを使うかで 5〜18% 動く(R-110 §3-1 のフロア)。W21 は 2025 の補完値(仮-23)"},
    }

    # ================================================================ 計器
    def lens(t: Mapping[str, Any]) -> dict[str, Any]:
        lg = np.asarray(t["lang"]).astype(str)
        return {lg_: {"chars": WC.length_summary(np.asarray(t["chars"])[lg == lg_]),
                      "tokens_hint": WC.length_summary(np.asarray(t["tokens_hint"])[lg == lg_]),
                      "lines": WC.length_summary(np.asarray(t["lines"])[lg == lg_])} for lg_ in P.LANGS}

    seat_tot = {k: {kk: int(sum(v[kk] for v in rep.values())) for kk in ("seats", "people", "filled", "vacant",
                                                                          "overflow")}
                for k, rep in (("before", rep_b), ("after", rep_a))}
    checks_c = {
        "schema": "w21c.checks/1",
        "note": "段 8〜10 の計器(合否なし)。人物の文は写さない(長さと数だけ)",
        "counts": {"people": n, "persona_rows": int(np.asarray(long_t["person_id"]).size),
                   "persona_built": int(built.sum()), "persona_no_template": int((~built).sum())},
        "persona": {
            "lengths": {"short": lens(short_t), "long": lens(long_t)},
            "first_language": WC.counts_by(lang["first_language"]),
            "lang": WC.counts_by(long_t["lang"]), "lang_basis": WC.counts_by(long_t["lang_basis"]),
            "nationality_top": dict(sorted(WC.counts_by(lang["nationality"][lang["is_foreign"]]).items(),
                                           key=lambda kv: (-kv[1], kv[0]))[:20]),
            "japanese_level": WC.counts_by(lang["japanese_level"][lang["japanese_level"] >= 0]),
            "short_is_prefix_of_long": int(built.sum()) - not_prefix, "short_not_prefix": not_prefix,
            "tipi_filled": 0, "ps2_blank_fields": list(P.PS2_BLANK_FIELDS),
            "note": "長さは決め打ちしない(事実のある行だけ)。目安のトークン=日本語は字数 × 1.0・英語は字数 ÷ 4(未計測)",
        },
        "stage10": {
            "w20_attributes": {"rows": attrs.n, "employed": int(np.count_nonzero(attrs.employed)),
                               "school": int(np.count_nonzero(attrs.school)),
                               "seat_and_school": int(np.count_nonzero(attrs.seat_and_school)),
                               "lead_from_walk": int((attrs.lead_min > 0).sum()),
                               "lead_blank_to_default": int((attrs.employed & (attrs.lead_min < 0)
                                                             & (attrs.workplace != WP.W.WP_HOME)).sum()),
                               "duty_place_hint": int((attrs.place_hint > 0).sum()),
                               "duty_shift": int(np.count_nonzero(attrs.shift)),
                               "occupation_known": int((np.asarray(attrs.occupation, dtype=object) != "").sum())},
            "status_split": {"candidates": int(cand.sum()),
                             "before": WC.counts_by(st_before[cand]), "after": WC.counts_by(st_after[cand])},
            "seat_recount": {**seat_tot, "breakdown": _seat_breakdown(cand, kind, st_before, org_b, org_a),
                             "before_matches_stage4": bool(np.array_equal(org_b, org_index)),
                             "after_matches_stage4": bool(np.array_equal(org_a, org_index)),
                             "overflow_reduction": seat_tot["before"]["overflow"] - seat_tot["after"]["overflow"],
                             "seated_increase": seat_tot["after"]["filled"] - seat_tot["before"]["filled"]},
            "store_staff": {"rows": int(np.asarray(staff["right_id"]).size),
                            "stores_with_staff": int(np.unique(np.asarray(staff["object_id"])).size),
                            "people": int(np.unique(np.asarray(staff["holder_id"])).size),
                            "stores_with_owner": int(((np.asarray(inp.rights["kind"], dtype=object) == "own")
                                                      & (np.asarray(inp.rights["object_kind"], dtype=object)
                                                         == "store")).sum()),
                            "stores_without_staff": int(np.asarray(inp.poi["name"], dtype=object).size
                                                        - np.unique(np.asarray(staff["object_id"])).size)},
            "w16_keep": {k: keep[k] for k in ("w16_total", "rows_removed_stage10", "rows_kept",
                                              "w21_duty_double_with_kept_transport")},
        },
    }

    # ================================================================ 出力
    def tbl(d: Mapping[str, Any]) -> dict[str, Any]:
        o: dict[str, Any] = {}
        for k, v in d.items():
            if isinstance(v, np.ndarray) and v.dtype == object:
                o[k] = pa.array(v.tolist(), type=pa.string())
            else:
                o[k] = v
        return o

    split_rows = np.flatnonzero(cand)
    split_tbl = {"person_id": pid[split_rows].astype(np.int32),
                 "industry_major": np.asarray(p["industry_major"], dtype=object)[split_rows],
                 "emp_status_before": st_before[split_rows], "emp_status_after": st_after[split_rows],
                 "org_index_before": org_b[split_rows].astype(np.int32), "org_index_after": org_a[split_rows].astype(np.int32)}
    attr_tbl = {
        "agent_id": np.asarray(attrs.agent_id, dtype=np.int32), "kind": np.asarray(attrs.kind, dtype=np.int8),
        "age": np.asarray(attrs.age, dtype=np.int16), "industry": np.array(attrs.industry, dtype=object),
        "duty_role": np.array(attrs.duty_role, dtype=object), "occupation": np.array(attrs.occupation, dtype=object),
        "employment_pool": np.array(attrs.employment_pool, dtype=object), "employed": np.asarray(attrs.employed),
        "workplace": np.asarray(attrs.workplace, dtype=np.int8), "school": np.asarray(attrs.school),
        "work_cell": np.asarray(attrs.work_cell, dtype=np.int32), "school_cell": np.asarray(attrs.school_cell, dtype=np.int32),
        "home_cell": np.asarray(attrs.home_cell, dtype=np.int32), "lead_min": np.asarray(attrs.lead_min, dtype=np.int16),
        "census_middles": np.array(["|".join(m) for m in attrs.census_middles], dtype=object),
        "place_hint": np.asarray(attrs.place_hint, dtype=np.int8), "shift": np.asarray(attrs.shift),
        "seat_nonworking": np.asarray(attrs.seat_nonworking), "seat_and_school": np.asarray(attrs.seat_and_school),
    }
    outputs = [
        C.write_parquet(out, OUTPUTS_C[0], tbl(short_t)),
        C.write_parquet(out, OUTPUTS_C[1], tbl(long_t)),
        C.write_json(out, OUTPUTS_C[2], check),
        C.write_parquet(out, OUTPUTS_C[3], tbl(attr_tbl)),
        C.write_parquet(out, OUTPUTS_C[4], tbl(split_tbl)),
        C.write_parquet(out, OUTPUTS_C[5], tbl(staff)),
        C.write_json(out, OUTPUTS_C[6], keep),
        C.write_json(out, OUTPUTS_C[7], checks_c),
    ]
    build_hash = C.sha256_bytes("".join(o["sha256"] for o in outputs).encode("utf-8"))
    rparams = {"seed": seed, "attr_fns": A.registry_versions(stages=(9, 10)),
               "rng_domains": ["w21c.nationality", "w21c.first_language", "w21c.japanese_level",
                               "w21c.commuter.status_split", "w21b.org.seat(段 4 と同じ=数え直し)", "w21c.check.pairs.<層>"],
               "constants": {"chars_per_token": dict(P.CHARS_PER_TOKEN), "walk_speed_ms": A.WALK_SPEED_REFERENCE_MS,
                             "pairs": K.PAIRS, "japanese_level_min_age": A.JAPANESE_LEVEL_MIN_AGE}}
    read_files = dict(sorted(guard.files_read.items()))
    srcs = [{"sid": s.sid, "title": s.title, "stat_inf_id": s.stat_inf_id, "path": s.rel, "md5": s.md5,
             "derived": s.derived_rel, "derived_md5": s.derived_md5, "year": s.year, "r116_row": s.r116_row,
             "side": s.side} for s in (*S.SOURCES, *S.SOURCES_B, *S.SOURCES_C) if s.rel in read_files or
            (s.derived_rel and s.derived_rel in read_files)]
    manifest = {
        "schema": "w21c.manifest/1", "stage": STAGE_C, "stage_version": STAGE_VERSION_C, "population_seed": seed,
        "params": rparams,
        "base": {"asset": BASE_ASSET_C, "w21b_build_hash": inp.mans["w21b_manifest.json"]["w21b_build_hash"],
                 "w21_build_hash": inp.mans["w21_manifest.json"]["w21_build_hash"], "files": dict(sorted(inp.files.items()))},
        "sources": srcs, "verify_side_rows": [r.row for r in S.VERIFY_SIDE], "read": read_files,
        "constants_cited": {"japanese_level_r6": {"levels": list(A.JAPANESE_LEVELS),
                                                  "table": {k: list(v) for k, v in A.JAPANESE_LEVEL_TABLE.items()},
                                                  "row": "R-110 §3-2(#25 p.70〜71・引)"},
                            "nationality_language": dict(A.NATIONALITY_LANGUAGE)},
        "counts": checks_c["counts"], "outputs": outputs, "w21c_build_hash": build_hash,
        "expedients": list(W21C_EXPEDIENTS),
    }
    C.write_json(out, MANIFEST_C, manifest)
    res = C.StageResult(stage=STAGE_C, stage_version=STAGE_VERSION_C,
                        input_hash=C.input_hash([guard.paths_read[q] for q in read_files]),
                        param_hash=C.param_hash(rparams), params=rparams, outputs=outputs,
                        catalog_classes=["点検(PS6・合否なし)", "人物の文(PS7・短い版と長い版)", "段 10 の材料"],
                        expedients=list(W21C_EXPEDIENTS),
                        notes={"w21c_build_hash": build_hash, "counts": checks_c["counts"]})
    res.gates = [
        C.Gate("people", n, None),
        C.Gate("person_id_duplicates", int(n - np.unique(pid).size), 0),
        C.Gate("persona_rows_equal_people", int(np.asarray(long_t["person_id"]).size), n),
        C.Gate("short_not_prefix_of_long", not_prefix, 0),
        C.Gate("seat_recount_matches_stage4", bool(np.array_equal(org_a, org_index)), True),
        C.Gate("language_verify_side_opened", sum(1 for q in read_files if any(t in q for t in VERIFY_SIDE_LANGUAGE)),
               0),
    ]
    C.write_header(out, res)
    return res, manifest


def _seat_breakdown(cand: np.ndarray, kind: np.ndarray, status: np.ndarray, org_b: np.ndarray, org_a: np.ndarray
                    ) -> dict[str, Any]:
    """〔検収 中 2〕地位の分けの前後の席の内訳: 候補(分けた外から来て働く人)/候補でない × 席を得た・失った・勤め先が
    変わった(同じ地位の区分の中で埋める順が変わる)。失った人と勤め先が変わった人は種類と地位で数える。"""
    sb, sa = org_b >= 0, org_a >= 0
    out: dict[str, Any] = {}
    for name, m in (("candidates", cand), ("others", ~cand)):  # 逐次: 2 群
        gained, lost = m & ~sb & sa, m & sb & ~sa
        changed = m & sb & sa & (org_b != org_a)
        out[name] = {"people": int(m.sum()), "seated_before": int((m & sb).sum()), "seated_after": int((m & sa).sum()),
                     "gained": int(gained.sum()), "lost": int(lost.sum()), "workplace_changed": int(changed.sum()),
                     "lost_by_kind_status": WC.counts_by(np.char.add(np.char.add(np.asarray(kind[lost]).astype(str), "|"),
                                                                     np.asarray(status[lost]).astype(str))),
                     "changed_by_kind": WC.counts_by(np.asarray(kind[changed]).astype(str))}
    out["workplace_changed_total"] = out["candidates"]["workplace_changed"] + out["others"]["workplace_changed"]
    out["note"] = ("分けは段 10 で人の表に入れて段 4〜7 を組み直す(親の仮採用)=候補でない人の席の喪失と勤め先の変化は宣言"
                   "(同じ乱数の鍵・同じ席=埋める順が変わるため)")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.pop.w21_build_c")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--base", type=Path, default=None, help="段 1〜7 の資産(既定 <data>/world/v2_stage_4-1b・読むだけ)")
    ap.add_argument("--world", type=Path, default=None, help="読む世界資産(既定 <data>/world/v2・読むだけ)")
    ap.add_argument("--seed", type=int, default=W.DEFAULT_SEED)
    ap.add_argument("--in-place", action="store_true",
                    help="段 10 の差し替えの資産を組むとき(--base と --out が同じ置き場=段 4〜7 を組み直した置き場)")
    a = ap.parse_args(argv)
    data = a.data.resolve()
    world = W.source_world(data, a.world).resolve()  # 〔段 10〕差し替えた世界なら退避の W16 の世界
    base = (a.base or a.data / "world" / BASE_ASSET_C).resolve()
    try:
        check_out_c(data, a.out.resolve(), world, base, in_place=a.in_place)
    except ProtectedOutputErrorC as e:
        print(f"[W21c] 止めた(何も書いていない): {e}", file=sys.stderr)
        return 2
    res, man = build_c(data, a.out.resolve(), base=base, world=world, seed=a.seed, in_place=a.in_place)
    print(f"[W21c] people={man['counts']['people']} persona_built={man['counts']['persona_built']} "
          f"w21c_build_hash={man['w21c_build_hash']}")
    return 0 if res.all_passed else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
