"""build.sched.trial — D-68 下見(2,000 体・多腕)の**別経路**モジュール。

位置づけ
    本番 W17(``w17_schedule.py``)は**一切変えない**。本モジュールは同じプール・同じ
    ``fleet_gen`` 入力形式・同じ語彙を使いながら、**腕ごとに違うプロンプトと文法**で
    2,000 体ぶんのプロンプトを書き、応答を**修復せずに**測って報告するだけの経路。
    出力は ``data/world/v2/trials/<arm>/`` に置き、名前は本番の glob
    ``w17_responses*.jsonl`` / ``w17_prompts*.jsonl`` に**当たらない**
    (``files_avoid_production_globs`` が機械検査する)。

正典
    ``docs/design/v2-d68-pilot-design.md``(§1 5 腕・§2 P1 の勤務窓投入・§3 P2 の 2 段・
    §4 標本 2,000 体の層化と seed 規約・§6 ゲート再定義。§8 決定項 12 件は全て推奨で確定)。
    背景 ``docs/research/v2-d68-behavioral-diversity-research.md`` §6(第30/31/35/36表)・§11。
    ブロック形式 ``docs/design/v2-plan-executor-design.md`` §9。

腕(§1)
    ========  ====================================================================
    P0        凍結資産(``w17_schedule.parquet``)を**読むだけ**=前値の記録。呼 0。
    P0b       P0 と同一のプロンプト・seed だけ違う(同腕 2 標本のフロア)。
    P1a       事実行に雇用形態・自分の出勤/帰宅 HH:MM。例示の時刻を丸めない。regex {4,5}。
    P1b       P1a + regex {3,10}。
    P2        段1(同一性・面接形式)→ 段2(ブロック形式の週次表)。
    P2-32B    P2 と**同じプロンプト**(seed も同じ)で 200 体。モデルは親が fleet_gen 側で選ぶ。
    ========  ====================================================================

修復しない
    ``repair_day`` / ``repair`` は**呼ばない**(P0b だけ「前値と同じ土俵」を作るために
    修復版も別に出す)。検査は落ちた件数を**数えるだけ**。raking は 12% と 0% の両方
    (決定項 9)を通して ``jsd_before`` / ``jsd_after`` を出す。

逐次ループ宣言(P4)
    体数ぶんのループが 3 本(①勤務窓の抽選 ②プロンプト生成 ③応答のパースと検査)。
    いずれも下見 2,000 体規模・構築時 1 回・I1 の外。

expedient(§8 登録簿へ・切替口つき)
    - 非正規の内訳を第31表の**全国人数比**で按分(パート/アルバイト/契約/嘱託/派遣。
      「26_その他」は按分から外す)。切替口 ``EMPLOYMENT_MIX``。
    - 自営業主を 雇人のある/ない業主 の人数比(= 28:72)で按分。同上。
    - ``arrival_lead_min`` 欠損は 30 分(``LEAD_DEFAULT_MIN``・計数 ``lead_default``)。
      欄の意味(通勤時間か余裕時間か)は未確認=設計書 §7 リスク 5。
    - 勤務長を [4 h, 12 h] にクリップ(``WORK_LEN_MIN/MAX_MIN``・計数 ``work_len_clipped``)。
      クリップは**始業を固定して終業を動かす**。
    - 行動者率を**曜日に独立**に適用(第31表の行動者率は平日の値。D-67 (b) 0.88 と同源=
      重ねるときは二重掛けにしない)。切替口 ``--no-absent``。
    - 開端ビン(``-4:45`` / ``19:00-`` / ``-10:45`` / ``4:00-``)の幅を 60 分とみなす
      (``OPEN_BIN_SPAN_MIN``)。帰宅表の ``不詳`` 列は落として構成比を再正規化。
    - 宿泊客の判定= **訪日来街者(kind 7)だけ**(プールに宿泊欄が無い)。切替口 ``--stay-kinds``。
    - 段1 の固有名詞・数字検査は W14 の残差方式の**簡易版**(build.sched は perception を
      import しない=層契約)。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Final, Iterable, Iterator, NamedTuple, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from shibuya.core.hashing import blake3_u64

from ..geo import common as C
from ..pop.w16_population import (
    KIND_COMMUTER,
    KIND_CREW,
    KIND_DISPATCHER,
    KIND_FOREIGN_VISITOR,
    KIND_NAMES,
    KIND_REGULAR_VISITOR,
    KIND_RESIDENT,
    KIND_STUDENT,
    KIND_VISITOR,
    KIND_WORKER,
)
from . import pool_facts as PF
from . import vocab as V
from . import w17_schedule as W17

__all__ = [
    "TRIAL_VERSION",
    "TRIAL_N_PER_KIND",
    "ARMS",
    "ArmSpec",
    "TrialFacts",
    "build_anchor",
    "load_anchor",
    "draw_windows",
    "sample_rows",
    "arm_prompts",
    "write_arm_prompts",
    "parse_blocks",
    "ingest_arm",
    "files_avoid_production_globs",
    "main",
]

TRIAL_VERSION: Final[str] = "0.1.0"

# ================================================================= 標本(§4)
#: 種別 → 下見の体数(設計書 §4 の表・合計 2,000)。
TRIAL_N_PER_KIND: Final[dict[int, int]] = {
    KIND_COMMUTER: 1_090,   # 0 通勤
    KIND_VISITOR: 296,      # 1 来街
    KIND_WORKER: 36,        # 2 従業
    KIND_RESIDENT: 185,     # 3 住民
    KIND_DISPATCHER: 10,    # 4 指令(下限)
    KIND_STUDENT: 169,      # 5 通学
    KIND_REGULAR_VISITOR: 101,  # 6 定期来街
    KIND_FOREIGN_VISITOR: 88,   # 7 訪日
    KIND_CREW: 25,          # 8 乗務(下限)
}
#: 32B 比較腕の体数(決定項 5「200 体だけ」・種別層化の**先頭**=2,000 体の入れ子)。
TRIAL_N_32B: Final[int] = 200

# ================================================================= seed 規約(§4)
#: 下見の seed ドメイン頭。本番(``w17_schedule.SEED_TAG`` = ``…/W17/v1``)と**別**。
SEED_TAG_V2: Final[bytes] = b"shibuya.build.sched/W17/v2/"


def u01(domain: str, agent_id: int) -> float:
    """``blake3(SEED_TAG_V2 ‖ domain ‖ ":" ‖ agent_id)`` → ``[0, 1)`` の一様乱数。

    設計書 §2-2 の ``seed=blake3("shibuya.build.sched/W17/v2/depart:"‖agent_id)`` の実装形。
    ``>> 11`` で倍精度に厳密に載る 53 bit にしてから割る(決定論・プラットフォーム非依存)。

    Example:
        >>> 0.0 <= u01("depart", 1) < 1.0
        True
        >>> u01("depart", 1) == u01("depart", 1)
        True
        >>> u01("depart", 1) != u01("return", 1)
        True
    """
    h = blake3_u64(SEED_TAG_V2 + domain.encode("ascii") + b":" + str(int(agent_id)).encode("ascii"))
    return (h >> 11) / float(1 << 53)


def arm_seed(arm: str, agent_id: int) -> int:
    """腕タグ入りの生成 seed(§4「seed ドメインに腕タグを入れる」)。

    **勤務窓の抽選には腕タグを入れない**(P1a と P1b で窓が変わると M3/M4 の帰属が付かない)。
    腕タグが効くのは LLM に渡す ``seed`` だけ= P0b は「P0 と同じ文面・seed だけ違う」。
    """
    h = blake3_u64(
        SEED_TAG_V2 + b"seed/" + arm.encode("ascii") + b":" + str(int(agent_id)).encode("ascii")
    )
    return h % W17.SEED_MOD


# ================================================================= e-Stat 表(§2・アンカー)
#: アンカー台帳の場所(新規・親が ``verified_by`` を後で付ける)。
ANCHOR_NAME: Final[str] = "commute_time_dist_r3.json"
ANCHOR_DIR: Final[tuple[str, ...]] = ("docs", "bench", "anchors")
#: 第31表(出勤)・第36表(帰宅)の取得済みファイル(``data/research_cache``)。
ESTAT_DEPART: Final[str] = "estat_r3_avgtime_000032224421.xlsx"
ESTAT_RETURN: Final[str] = "estat_r3_avgtime_000032224427.xlsx"
ESTAT_STATINF: Final[dict[str, str]] = {"depart": "000032224421", "return": "000032224427"}
#: 開端ビン(``-4:45`` / ``19:00-`` など)の幅[分](expedient)。
OPEN_BIN_SPAN_MIN: Final[int] = 60
#: 答申 §10 の行キー(曜日=平日・地域=全国・男女=総数)。
ESTAT_FILTER: Final[tuple[str, str, str]] = ("1_平日", "0_全国", "0_総数")
#: (従業上の地位, 雇用形態)→ 台帳の行名。
ESTAT_ROWS: Final[dict[tuple[str, str], str]] = {
    ("0_総数", "0_総数"): "総数",
    ("1_雇用されている人", "1_正規の職員・従業員"): "正規の職員・従業員",
    ("1_雇用されている人", "2_正規の職員・従業員以外"): "正規以外",
    ("1_雇用されている人", "21_パート"): "パート",
    ("1_雇用されている人", "22_アルバイト"): "アルバイト",
    ("1_雇用されている人", "23_契約社員"): "契約社員",
    ("1_雇用されている人", "24_嘱託"): "嘱託",
    ("1_雇用されている人", "25_労働者派遣事業所の派遣社員"): "派遣社員",
    ("2_会社などの役員", "0_総数"): "会社などの役員",
    ("3_雇人のある業主", "0_総数"): "雇人のある業主",
    ("4_雇人のない業主", "0_総数"): "雇人のない業主",
    ("5_自家営業の手伝い(家族従業者)", "0_総数"): "家族従業者",
}
#: プールの ``employment`` → 台帳の行名(按分するものは複数・重みは人数比で**実行時に**決める)。
EMPLOYMENT_MIX: Final[dict[str, tuple[str, ...]]] = {
    "正規": ("正規の職員・従業員",),
    # 決定項 2: 非正規は第31表の全国人数比で按分(「26_その他」は外す=expedient)
    "非正規": ("パート", "アルバイト", "契約社員", "嘱託", "派遣社員"),
    "役員": ("会社などの役員",),
    # 自営業主は 雇人のある/ない業主 の人数比(= 28:72)で按分(expedient)
    "自営業主": ("雇人のある業主", "雇人のない業主"),
    "家族従業者": ("家族従業者",),
    "非就業": (),
}

_XL_NS: Final[str] = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_COL_RE: Final[re.Pattern[str]] = re.compile(r"([A-Z]+)")


def _read_xlsx_rows(path: Path) -> list[list[str]]:
    """xlsx(1 シート目)→ 行 × 列の文字列表。**標準ライブラリだけ**で読む。

    ``openpyxl`` / ``pandas`` はこの venv に無い(入れる決定もしていない)。e-Stat の
    平均時刻編は共有文字列+数値の単純な表なので、``zipfile`` + ``ElementTree`` で足りる。
    """
    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(_XL_NS + "si"):
                shared.append("".join(t.text or "" for t in si.iter(_XL_NS + "t")))
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows: list[list[str]] = []
    for r in sheet.iter(_XL_NS + "row"):  # 逐次: 表の行数(324 行)
        cells: dict[int, str] = {}
        for c in r.findall(_XL_NS + "c"):
            ref = c.get("r") or ""
            m = _COL_RE.match(ref)
            if m is None:
                continue
            idx = 0
            for ch in m.group(1):
                idx = idx * 26 + (ord(ch) - 64)
            idx -= 1
            t = c.get("t")
            v = c.find(_XL_NS + "v")
            if t == "s":
                cells[idx] = shared[int(v.text)] if v is not None and v.text else ""
            elif t == "inlineStr":
                node = c.find(_XL_NS + "is")
                cells[idx] = "".join(x.text or "" for x in node.iter(_XL_NS + "t")) if node is not None else ""
            else:
                cells[idx] = (v.text or "") if v is not None else ""
        n = max(cells) + 1 if cells else 0
        rows.append([cells.get(i, "") for i in range(n)])
    return rows


def _bin_minutes(labels: Sequence[str]) -> list[int | None]:
    """時刻区分ラベル(``01_-4:45`` / ``54_0:00`` / ``71_不詳``)→ ビン開始の分。

    帰宅表は 10:45 → 翌 4:00 まで並ぶので、**時刻が戻ったら 1440 を足す**(翌日扱い)。
    ``不詳`` は ``None``(呼び出し側が落として再正規化する)。

    Example:
        >>> _bin_minutes(["01_-4:45", "02_5:00", "03_5:15"])
        [285, 300, 315]
        >>> _bin_minutes(["53_23:45", "54_0:00"])
        [1425, 1440]
    """
    out: list[int | None] = []
    prev = -1
    base = 0
    for lab in labels:
        body = lab.split("_", 1)[1] if "_" in lab else lab
        if "不詳" in body:
            out.append(None)
            continue
        t = body.strip("-")
        h, _, mm = t.partition(":")
        m = int(h) * 60 + int(mm)
        if prev >= 0 and m + base < prev:
            base += 1440
        m += base
        out.append(m)
        prev = m
    return out


def _read_estat_table(path: Path) -> dict[str, Any]:
    """第31表 / 第36表 → ``{"bins": [...], "rows": {行名: {...}}}``(構成比は % のまま)。"""
    rows = _read_xlsx_rows(path)
    labels = [x for x in rows[6][8:] if x]
    mins = _bin_minutes(labels)
    bins: list[dict[str, Any]] = []
    keep: list[int] = []
    for j, (lab, m) in enumerate(zip(labels, mins)):
        if m is None:
            continue
        body = lab.split("_", 1)[1]
        if body.startswith("-"):  # 開端(下)
            lo, width = m + 15 - OPEN_BIN_SPAN_MIN, OPEN_BIN_SPAN_MIN
        elif body.endswith("-"):  # 開端(上)
            lo, width = m, OPEN_BIN_SPAN_MIN
        else:
            lo, width = m, 15
        bins.append({"label": body, "start_min": int(lo), "width_min": int(width)})
        keep.append(j)
    out_rows: dict[str, Any] = {}
    for r in rows[9:]:  # 逐次: 表の行数
        if len(r) < 9 or (r[0], r[1], r[2]) != ESTAT_FILTER:
            continue
        name = ESTAT_ROWS.get((r[3], r[4]))
        if name is None:
            continue
        raw = []
        for j in keep:
            v = r[8 + j] if 8 + j < len(r) else ""
            raw.append(float(v) if v not in ("", None, "-", "…", "***") else 0.0)
        total = sum(raw)
        out_rows[name] = {
            "row_key": {"曜日": r[0], "地域区分": r[1], "男女": r[2],
                        "従業上の地位": r[3], "雇用形態": r[4]},
            "population_k": float(r[5]) if r[5] else 0.0,
            "actor_rate": round(float(r[6]) / 100.0, 6) if r[6] else 0.0,
            "mean_hhmm": str(r[7]),
            "share_sum_pct": round(total, 4),
            "share": [round(x / total, 8) for x in raw] if total > 0 else [0.0] * len(raw),
        }
    return {"bins": bins, "rows": out_rows}


def build_anchor(cache_dir: str | Path, out_path: str | Path) -> dict[str, Any]:
    """第31表(出勤)+第36表(帰宅)→ ``docs/bench/anchors/commute_time_dist_r3.json``。

    ``verified_by`` は ``None`` で置く(**親が一次確認して後で入れる**= CLAUDE.md §5)。
    """
    cache = Path(cache_dir)
    depart = _read_estat_table(cache / ESTAT_DEPART)
    ret = _read_estat_table(cache / ESTAT_RETURN)
    mix: dict[str, dict[str, float]] = {}
    for emp, names in EMPLOYMENT_MIX.items():
        if len(names) <= 1:
            mix[emp] = {n: 1.0 for n in names}
            continue
        pops = {n: depart["rows"][n]["population_k"] for n in names}
        s = sum(pops.values())
        mix[emp] = {n: round(p / s, 8) for n, p in pops.items()}
    doc = {
        "schema": "shibuya.build.sched/commute_time_dist_r3/1",
        "version": "v0",
        "created": "2026-09-11",
        "purpose": (
            "D-68 下見 P1 の勤務窓投入(設計書 v2-d68-pilot-design.md §2)が読む唯一の"
            "現実側入力。令和3年社会生活基本調査 平均時刻編 第31表(出勤)・第36表(帰宅)の"
            "雇用形態別 15 分ビン構成比。数値はここにしか置かない(コード側に定数を複製しない)。"
        ),
        "source": {
            "survey": "総務省統計局 令和3年社会生活基本調査 平均時刻編(調査票A)",
            "license": "政府標準利用規約(第2.0版)/ 出典の明示が条件",
            "tables": {
                "depart": {
                    "table": "第31表 曜日,出勤,男女,従業上の地位,雇用形態,時刻区分別行動者数(構成比)(有業者)-全国",
                    "statInfId": ESTAT_STATINF["depart"],
                    "url": f"https://www.e-stat.go.jp/stat-search/file-download?statInfId={ESTAT_STATINF['depart']}&fileKind=0",
                    "local": f"data/research_cache/{ESTAT_DEPART}",
                },
                "return": {
                    "table": "第36表 曜日,仕事からの帰宅時間,男女,従業上の地位,雇用形態,時刻区分別行動者数(構成比)(有業者)-全国",
                    "statInfId": ESTAT_STATINF["return"],
                    "url": f"https://www.e-stat.go.jp/stat-search/file-download?statInfId={ESTAT_STATINF['return']}&fileKind=0",
                    "local": f"data/research_cache/{ESTAT_RETURN}",
                },
            },
            "row_filter": {"曜日": ESTAT_FILTER[0], "地域区分": ESTAT_FILTER[1], "男女": ESTAT_FILTER[2]},
        },
        "rules": [
            "share は原表の構成比(%)を合計 1 に再正規化した値。帰宅表の『不詳』列は落としてから再正規化した(expedient)。",
            f"開端ビン(-4:45 / 19:00- / -10:45 / 4:00-)の幅は {OPEN_BIN_SPAN_MIN} 分とみなす(expedient)。",
            "start_min は 0 時起点の分。帰宅表の 0:00 以降のビンは 1440 を足した値(翌日)。",
            "employment_mix は第31表の推定人口(千人)から作った按分重み(決定項 2・自営業主 28:72)。",
            "合格線(PASS/FAIL の閾値)は書かない=判定は親(CLAUDE.md §2)。",
        ],
        "depart": depart,
        "return": ret,
        "employment_mix": mix,
        "tag": "anchor",
        "verified_by": None,
    }
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=False).encode("utf-8") + b"\n")
    return doc


def anchor_path(repo_root: str | Path | None = None) -> Path:
    """アンカー台帳の既定の場所(``<repo>/docs/bench/anchors/commute_time_dist_r3.json``)。"""
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[4]
    return root.joinpath(*ANCHOR_DIR, ANCHOR_NAME)


# ================================================================= 逆関数法(§2-2)
class BinTable(NamedTuple):
    """1 行ぶんの 15 分ビン表(逆関数法の入力)。

    Attributes:
        start: ビン開始の分(昇順)。
        width: ビンの幅[分]。
        cdf: 構成比の累積(末尾 1.0)。
        actor_rate: 行動者率(その日に出勤した割合)。
    """

    start: np.ndarray
    width: np.ndarray
    cdf: np.ndarray
    actor_rate: float


def _bin_table(table: dict[str, Any], row: str) -> BinTable:
    bins = table["bins"]
    r = table["rows"][row]
    share = np.asarray(r["share"], dtype=np.float64)
    s = share.sum()
    if s > 0:
        share = share / s
    return BinTable(
        start=np.asarray([b["start_min"] for b in bins], dtype=np.int64),
        width=np.asarray([b["width_min"] for b in bins], dtype=np.int64),
        cdf=np.cumsum(share),
        actor_rate=float(r["actor_rate"]),
    )


def inverse_sample(bt: BinTable, u: float) -> int:
    """逆関数法 + **ビン内一様**。``u ∈ [0,1)`` → 分。

    ビン ``j`` を ``searchsorted(cdf, u)`` で引き、**同じ u の残差**でビン内の位置を決める
    (乱数を 2 本引かない=1 本の一様変数からの厳密な連続逆変換)。

    Example:
        >>> bt = BinTable(np.array([0, 15]), np.array([15, 15]), np.array([0.5, 1.0]), 1.0)
        >>> inverse_sample(bt, 0.0), inverse_sample(bt, 0.5), inverse_sample(bt, 0.999)
        (0, 15, 29)
    """
    j = int(np.searchsorted(bt.cdf, float(u), side="right"))
    j = min(j, int(bt.cdf.size) - 1)
    lo = float(bt.cdf[j - 1]) if j > 0 else 0.0
    p = float(bt.cdf[j]) - lo
    frac = (float(u) - lo) / p if p > 1e-15 else 0.0
    frac = min(max(frac, 0.0), 1.0 - 1e-12)
    return int(bt.start[j] + math.floor(frac * bt.width[j]))


def load_anchor(path: str | Path | None = None) -> dict[str, Any]:
    """アンカー台帳を読む(無ければ ``FileNotFoundError``)。"""
    p = Path(path) if path is not None else anchor_path()
    return json.loads(p.read_text(encoding="utf-8"))


def employment_row(anchor: dict[str, Any], employment: str, u: float) -> str:
    """雇用形態 → 第31表の行名(按分は ``employment_mix`` の重みで逆関数法)。

    Example:
        >>> a = {"employment_mix": {"非正規": {"パート": 0.5, "アルバイト": 0.5}}}
        >>> employment_row(a, "非正規", 0.0), employment_row(a, "非正規", 0.9)
        ('パート', 'アルバイト')
        >>> employment_row(a, "非就業", 0.5)
        ''
    """
    mix = anchor.get("employment_mix", {}).get(str(employment), {})
    if not mix:
        return ""
    names = list(mix)
    c = 0.0
    for name in names:  # 逐次: 高々 5
        c += float(mix[name])
        if u < c:
            return name
    return names[-1]


# ================================================================= 勤務窓(§2)
#: ``arrival_lead_min`` 欠損時の既定[分](expedient・決定項 3 の (b) をフォールバックに)。
LEAD_DEFAULT_MIN: Final[int] = 30
#: 勤務長のクリップ範囲[分](expedient)。
WORK_LEN_MIN_MIN: Final[int] = 4 * 60
WORK_LEN_MAX_MIN: Final[int] = 12 * 60
#: 宿泊客とみなす種別(expedient・プールに宿泊欄が無い)。
STAY_KINDS_DEFAULT: Final[tuple[int, ...]] = (KIND_FOREIGN_VISITOR,)


@dataclass(frozen=True)
class TrialFacts:
    """下見の追加事実(行順=``AgentFacts`` の行順)。

    Attributes:
        emp: プールの ``employment``(そのまま)。
        row: 第31表の行名(窓を引かなかった体は ``""``)。
        depart: 出勤時刻[分](引かなかったら −1)。
        arrive: 帰宅時刻[分](1440 を超えうる=翌日)。
        lead: 片道通勤時間[分](``arrival_lead_min`` または既定)。
        duty_open / duty_close: 始業・終業[分](クリップ後)。
        work_days: **欠勤を引いた後**の曜日ビットマスク。
        stay: 宿泊客か(就寝地=宿泊施設の制約が付く)。
        counters: expedient の発火計数。
    """

    n: int
    emp: list[str]
    row: list[str]
    depart: np.ndarray
    arrive: np.ndarray
    lead: np.ndarray
    duty_open: np.ndarray
    duty_close: np.ndarray
    work_days: np.ndarray
    stay: np.ndarray
    counters: dict[str, int] = field(default_factory=dict)


def draw_windows(
    f: W17.AgentFacts,
    anchor: dict[str, Any],
    *,
    rows: Sequence[int] | np.ndarray | None = None,
    absent: bool = True,
    stay_kinds: Sequence[int] = STAY_KINDS_DEFAULT,
) -> TrialFacts:
    """設計書 §2 の写像(雇用形態 → 行 → 出勤/帰宅 → 始業/終業 → 欠勤)を体ごとに引く。

    窓を引くのは **``duty_activity == ACT_WORK`` かつ雇用形態が就業**の体だけ。
    非就業・来街者・通学者は引かない(通学は本番のまま)。

    Note:
        逐次ループ宣言(P4): 体数ぶんのループ 1 本(下見 2,000 体・構築時 1 回)。
    """
    n = f.n
    want = np.zeros(n, dtype=bool)
    want[np.asarray(rows, dtype=np.int64) if rows is not None else slice(None)] = True
    emp_col = f.pool.col("employment")
    lead_col = f.pool.arrival_lead_min
    stay_set = set(int(k) for k in stay_kinds)

    emp: list[str] = [""] * n
    row_name: list[str] = [""] * n
    depart = np.full(n, -1, dtype=np.int32)
    arrive = np.full(n, -1, dtype=np.int32)
    lead = np.full(n, -1, dtype=np.int32)
    duty_open = np.full(n, -1, dtype=np.int32)
    duty_close = np.full(n, -1, dtype=np.int32)
    work_days = np.asarray(f.work_days, dtype=np.uint8).copy()
    stay = np.zeros(n, dtype=bool)
    ctr: dict[str, int] = {
        "window_drawn": 0, "lead_default": 0, "work_len_clipped": 0,
        "absent_day": 0, "no_employment_row": 0, "stay_bodies": 0,
    }
    dep_t = anchor["depart"]
    ret_t = anchor["return"]
    cache: dict[str, tuple[BinTable, BinTable]] = {}

    for i in range(n):  # 逐次ループ宣言(P4): 体数ぶん・構築時 1 回
        if not want[i]:
            continue
        aid = int(f.agent_id[i])
        if int(f.kind[i]) in stay_set:
            stay[i] = True
            ctr["stay_bodies"] += 1
        e = str(emp_col[i] or "")
        emp[i] = e
        if int(f.duty_activity[i]) != V.ACT_WORK:
            continue
        name = employment_row(anchor, e, u01("employment", aid))
        if not name:
            ctr["no_employment_row"] += 1
            continue
        row_name[i] = name
        if name not in cache:
            cache[name] = (_bin_table(dep_t, name), _bin_table(ret_t, name))
        bt_dep, bt_ret = cache[name]
        d = inverse_sample(bt_dep, u01("depart", aid))
        a = inverse_sample(bt_ret, u01("return", aid))
        lv = int(lead_col[i])
        if lv <= 0:
            lv = LEAD_DEFAULT_MIN
            ctr["lead_default"] += 1
        lo = d + lv
        hi = a - lv
        if hi - lo < WORK_LEN_MIN_MIN:
            hi = lo + WORK_LEN_MIN_MIN
            ctr["work_len_clipped"] += 1
        elif hi - lo > WORK_LEN_MAX_MIN:
            hi = lo + WORK_LEN_MAX_MIN
            ctr["work_len_clipped"] += 1
        depart[i], arrive[i], lead[i] = d, a, lv
        duty_open[i], duty_close[i] = lo, hi
        ctr["window_drawn"] += 1
        if absent:  # §2-5 行動者率で曜日ごとに引く(曜日独立= expedient)
            mask = int(work_days[i])
            for dday in range(V.N_DAYS):  # 逐次: 7 回
                if not (mask >> dday) & 1:
                    continue
                if u01(f"absent:{dday}", aid) >= bt_dep.actor_rate:
                    mask &= ~(1 << dday)
                    ctr["absent_day"] += 1
            work_days[i] = mask
    return TrialFacts(
        n=n, emp=emp, row=row_name, depart=depart, arrive=arrive, lead=lead,
        duty_open=duty_open, duty_close=duty_close, work_days=work_days, stay=stay,
        counters=ctr,
    )


# ================================================================= 標本(§4)
def sample_rows(
    f: W17.AgentFacts, per_kind: dict[int, int] | None = None, *, total: int | None = None
) -> np.ndarray:
    """種別ごとの層化標本(``_mix64(agent_id)`` 昇順の先頭 n 体・``pilot_rows`` と同規約)。

    ``total`` を与えると ``per_kind`` の比を保ったまま最大剰余法で ``total`` 体まで縮める
    (32B 比較腕の 200 体=**2,000 体の入れ子**= 種別層化の先頭)。
    """
    want = dict(TRIAL_N_PER_KIND if per_kind is None else per_kind)
    if total is not None and total > 0:
        base = np.asarray([want.get(k, 0) for k in range(len(KIND_NAMES))], dtype=np.float64)
        got = W17._largest_remainder(base, int(total))
        want = {k: int(got[k]) for k in range(len(KIND_NAMES)) if base[k] > 0}
        for k in want:  # 在庫のある種別は必ず 1 体は残す
            want[k] = max(1, want[k])
    key = W17._mix64(f.agent_id.astype(np.uint64))
    picked: list[np.ndarray] = []
    for k in range(len(KIND_NAMES)):  # 逐次: 種別数(9)
        n = int(want.get(k, 0))
        if n <= 0:
            continue
        rows = np.flatnonzero(f.kind == k)
        if rows.size == 0:
            continue
        order = np.argsort(key[rows], kind="stable")
        picked.append(rows[order[: min(n, rows.size)]])
    return np.sort(np.concatenate(picked)) if picked else np.zeros(0, dtype=np.int64)


# ================================================================= 腕(§1)
#: 例示の時刻を**丸めない**ための差し替え表(P1 以降)。左=本番 ``SYSTEM_COMMON`` の行。
_FEWSHOT_ROUND: Final[tuple[str, ...]] = (
    "0000-0700 就寝 自宅", "0700-0800 支度 自宅", "0800-0900 移動 職場",
    "0900-1800 勤務 職場", "1800-1900 食事 飲食店",
)
_FEWSHOT_ODD: Final[tuple[str, ...]] = (
    "0000-0652 就寝 自宅", "0652-0723 支度 自宅", "0723-0807 移動 職場",
    "0807-1738 勤務 職場", "1738-1907 食事 飲食店",
)
_LINES_RULE_TMPL: Final[str] = "各日の活動行は{lo}行から{hi}行"


def _p1_system(kind: int, lines: tuple[int, int]) -> str:
    """P1 系の system(本番テンプレから **例示の時刻**と**行数規則**だけを差し替える)。

    本番の文面を起点にするのは「腕の差= 編集した箇所だけ」を言えるようにするため。
    差し替え元が見つからなければ ``AssertionError``(本番テンプレの改版を検出する)。
    """
    text = W17.system_prompt(int(kind))
    for old, new in zip(_FEWSHOT_ROUND, _FEWSHOT_ODD):
        assert old in text, f"本番テンプレに例示行が無い: {old}"
        text = text.replace(old, new)
    old_rule = _LINES_RULE_TMPL.format(lo=W17.LINES_PER_DAY_MIN, hi=W17.LINES_PER_DAY_MAX)
    assert old_rule in text, f"本番テンプレに行数規則が無い: {old_rule}"
    return text.replace(old_rule, _LINES_RULE_TMPL.format(lo=lines[0], hi=lines[1]))


# ---------------------------------------------------------------- P2 段1(同一性)
IDENTITY_MAX_TOKENS: Final[int] = 320
IDENTITY_CHARS_MIN: Final[int] = 200
IDENTITY_CHARS_MAX: Final[int] = 420
#: §3 の質問 3 つ(**性格・価値観・趣味は聞かない**=設計者の指紋を最小に)。
IDENTITY_QUESTIONS: Final[tuple[str, ...]] = (
    "ふだんの平日、朝は何時ごろ動き出して、どんな順で一日が進みますか。",
    "帰りに寄るところはありますか。",
    "休みの日は平日と何が違いますか。",
)
#: 役割づけの 1 文。**system ではなく user の先頭**(事実行の前)に置く。
#: 文面は設計書 §3 のまま・並びだけ変える= system を全員共通に保って
#: vLLM の prefix キャッシュを効かせるため(本番 W17 の SYSTEM_COMMON と同じ規約)。
IDENTITY_ROLE_LINE: Final[str] = "あなたは{name}さん本人です。"
#: 段1 の system(**全員共通**= 体ごとの語を 1 つも含まない)。
IDENTITY_SYSTEM: Final[str] = "\n".join(
    (
        "生活時間調査の面接に本人として答えます。",
        "3文から5文・話し言葉で、自分の一日の運びを話してください。",
        "次の4つは書かない:",
        "1. 与えられていない固有名詞(店名・地名・会社名・路線名・人の名前)。",
        "2. 与えられていない数字。",
        "3. 箇条書き・見出し・記号。",
        "4. 挨拶と自己紹介の決まり文句。",
    )
)

# ---------------------------------------------------------------- P2 段2(ブロック形式)
BLOCK_MAX_TOKENS: Final[int] = 1_024
#: ``block_kind``(計画実行層設計書 §9)。
BK_OUTSIDE, BK_HOME, BK_INAREA, BK_SLEEP, BK_MOVE = range(5)
BLOCK_KIND_WORDS: Final[tuple[str, ...]] = ("域外", "自宅", "在圏", "就寝", "移動")
#: 深夜(0〜4 時)に置かない活動語(D-63 (iii)・**文法から外す**)。
NIGHT_BAN_ACTS: Final[tuple[str, ...]] = ("支度", "乗車")
NIGHT_END_MIN: Final[int] = 4 * 60
#: 開始時刻の深夜側・昼側(``V.TIME_PATTERN`` をちょうど 2 つに割る)。
_NIGHT_START_RE: Final[str] = r"0[0-3][0-5][0-9]"
_DAY_START_RE: Final[str] = r"(?:0[4-9]|1[0-9]|2[0-4])[0-5][0-9]"

#: 段2 の system の共通部(**全員共通**= 先頭に置いて prefix キャッシュを効かせる)。
#: 体ごとの 1〜3 行(自宅の区分・宿泊・種別)は ``arm_system`` が**末尾**に足す。
BLOCK_SYSTEM_COMMON: Final[str] = "\n".join(
    (
        "自分の1週間(7日)の過ごし方を表にします。",
        "書式は2種類の行だけ:",
        "・曜日の見出し行 = d0 d1 d2 d3 d4 d5 d6 のどれか1つだけを書いた行"
        "(d0=月曜 d1=火曜 d2=水曜 d3=木曜 d4=金曜 d5=土曜 d6=日曜)。",
        "・ブロック行 = 「<開始HHMM>-<終了HHMM> <区分> <活動語> <場所語>」の4列を"
        "半角空白1つで区切る。",
        "区分は5つの数字のどれか: 0=渋谷の外 1=自宅(渋谷の中) 2=渋谷の中(自宅の外) "
        "3=就寝 4=移動",
        "活動語は次の12語だけを使う: " + " ".join(V.ACTIVITY_WORDS),
        "場所語は次の12語だけを使う: " + " ".join(V.PLACE_WORDS),
        "例:",
        "d0",
        "0000-0652 3 就寝 自宅",
        "0652-0723 1 支度 自宅",
        "0723-0807 4 移動 駅",
        "0807-1738 2 勤務 職場",
        "1738-1907 2 食事 飲食店",
        "1907-2400 1 休憩 自宅",
        "d1",
        "(以下 d6 まで同じ形で続ける)",
        "規則:",
        "1. d0 から d6 まで 7 日ぶんの見出し行を必ず書く。各日のブロック行は3行から10行。",
        "2. 時刻は4桁(0700)。各日は 0000 から始めて 2400 で終える。"
        "**時間に切れ目を作らない**(前の行の終了時刻=次の行の開始時刻)。",
        "3. 各日に「就寝」の行を必ず1本以上入れる。",
        "4. 0時台から3時台に「支度」と「乗車」は置かない。",
        "5. 就寝の行の区分は 3、移動と乗車の行の区分は 4。",
        "6. 表以外は何も書かない。前置き・説明・記号・箇条書き・空行を書かない。"
        "行末に空白を置かない。",
    )
)
#: 体ごとに足す 1 行(自宅の区分・宿泊)。
BLOCK_HOME_IN: Final[str] = "あなたの自宅は渋谷の中にある。自宅で過ごす行(就寝を除く)の区分は 1。"
BLOCK_HOME_OUT: Final[str] = "あなたの自宅は渋谷の外にある。自宅で過ごす行(就寝を除く)の区分は 0。"
BLOCK_STAY: Final[str] = "あなたは渋谷に泊まる。就寝の行は 場所語=宿泊施設 で書く(区分は 3)。"


@dataclass(frozen=True)
class ArmSpec:
    """1 腕の凍結仕様(system 文・例示・事実行・regex・修復方針・raking 予算)。

    Attributes:
        name: 腕名(``p0b`` / ``p1a`` / ``p1b`` / ``p2`` / ``p2_32b``)。
        facts: 事実行の水準(``"p0"`` = 本番のまま / ``"p1"`` = +雇用形態と出勤/帰宅 /
            ``"p2"`` = 面接形式の事実行)。
        lines: 1 日の行数(regex の ``{lo,hi}``)。
        block: ブロック形式か(``block_kind`` 欄を持つ)。
        stage: 2 段腕の段(0=単段 / 1=同一性 / 2=週次表)。
        max_tokens: 生成上限。
        repair: 取り込みで本番の ``repair_day`` を通した版も出すか(P0b のみ True)。
        rake_fracs: raking 予算(決定項 9: 12% と 0% の両方)。
        seed_arm: seed に使う腕タグ(P2-32B は P2 と**同じ**=文面もバイト一致)。
        n_total: 体数の上限(``None`` = 2,000 体の層化そのまま)。
    """

    name: str
    facts: str
    lines: tuple[int, int]
    block: bool = False
    stage: int = 0
    max_tokens: int = W17.MAX_TOKENS
    temperature: float = W17.TEMPERATURE
    repair: bool = False
    rake_fracs: tuple[float, ...] = (0.12, 0.0)
    seed_arm: str = ""
    n_total: int | None = None

    @property
    def seed_tag(self) -> str:
        return self.seed_arm or self.name


ARMS: Final[dict[str, ArmSpec]] = {
    "p0b": ArmSpec(name="p0b", facts="p0", lines=(W17.LINES_PER_DAY_MIN, W17.LINES_PER_DAY_MAX),
                   repair=True),
    "p1a": ArmSpec(name="p1a", facts="p1", lines=(W17.LINES_PER_DAY_MIN, W17.LINES_PER_DAY_MAX)),
    "p1b": ArmSpec(name="p1b", facts="p1", lines=(3, 10)),
    "p2": ArmSpec(name="p2", facts="p2", lines=(3, 10), block=True, stage=2,
                  max_tokens=BLOCK_MAX_TOKENS),
    "p2_32b": ArmSpec(name="p2_32b", facts="p2", lines=(3, 10), block=True, stage=2,
                      max_tokens=BLOCK_MAX_TOKENS, seed_arm="p2", n_total=TRIAL_N_32B),
}
#: ``--arm P0`` は凍結資産を読むだけ(呼 0)。
ARM_FROZEN: Final[str] = "p0"


def arm_of(name: str) -> ArmSpec:
    key = str(name).strip().lower().replace("-", "_")
    if key not in ARMS:
        raise ValueError(f"未知の腕: {name}(候補 {sorted(ARMS)} と {ARM_FROZEN})")
    return ARMS[key]


# ---------------------------------------------------------------- system / user / regex
def arm_system(spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts, i: int) -> str:
    """腕と体 → system 文。"""
    if spec.facts == "p0":
        return W17.system_prompt(int(f.kind[i]))
    if spec.facts == "p1":
        return _p1_system(int(f.kind[i]), spec.lines)
    if spec.stage == 1:
        return IDENTITY_SYSTEM
    lines = [BLOCK_SYSTEM_COMMON]
    lines.append(BLOCK_HOME_IN if int(f.home_cell[i]) >= 0 else BLOCK_HOME_OUT)
    if bool(t.stay[i]):
        lines.append(BLOCK_STAY)
    lines.append(W17.SYSTEM_KIND_LINE[int(f.kind[i])])
    return "\n".join(lines)


def _emp_word(t: TrialFacts, i: int) -> str:
    """事実行に載せる雇用形態(按分で引いた第31表の行名を括弧で添える)。"""
    e = t.emp[i] or "不明"
    r = t.row[i]
    return f"{e}({r})" if r and r != e else e


def arm_user(spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts, i: int,
             identity: str = "") -> str:
    """腕と体 → user 文(事実行)。"""
    if spec.facts == "p0":
        return W17.user_prompt(f, i)
    p = f.pool
    has_window = int(t.duty_open[i]) >= 0
    if spec.facts == "p1":
        lines = W17.user_prompt(f, i).split("\n")
        out: list[str] = [lines[0]]
        if has_window:
            out.append(f"雇用形態: {_emp_word(t, i)}")
        for ln in lines[1:]:
            if has_window and ln.startswith("勤務: "):
                where = "渋谷の外(域外)" if bool(f.duty_outside[i]) else "渋谷"
                out.append(
                    f"勤務: {where} {W17._days_word(int(t.work_days[i]))} "
                    f"{W17._hm(int(t.duty_open[i]))}-{W17._hm(int(t.duty_close[i]))}"
                )
                out.append(
                    f"出勤: {W17._hm(int(t.depart[i]))} 帰宅: {W17._hm(int(t.arrive[i]))}"
                )
                continue
            out.append(ln)
        return "\n".join(out)

    # --- P2: 面接形式の事実行(§3)---
    sex = W17._SEX_WORDS[int(f.sex[i])] if 0 <= int(f.sex[i]) < 2 else "不明"
    occ = (p.col("occupation")[i] or p.col("role")[i] or p.col("post")[i]
           or KIND_NAMES[int(f.kind[i])])
    name = p.col("name")[i] or KIND_NAMES[int(f.kind[i])]
    # 役割づけは **user の先頭**(事実行の前)= system を全員共通に保つため。
    out = [IDENTITY_ROLE_LINE.format(name=name), f"名前: {name}",
           f"{int(f.age[i])}歳 {sex} {occ}"]
    if t.emp[i]:
        out.append(f"雇用形態: {_emp_word(t, i)}")
    if p.col("rank")[i]:
        out.append(f"役職: {p.col('rank')[i]}")
    if p.col("industry_major")[i]:
        out.append(f"業種: {p.col('industry_major')[i]}")
    if int(f.home_cell[i]) >= 0:
        out.append("自宅: 渋谷")
    else:
        line = p.col("residence_line")[i]
        out.append("自宅: 域外" + (f"({line})" if line else ""))
    if p.col("commute_mode")[i]:
        out.append(f"出入口: {p.col('commute_mode')[i]}")
    duty = int(f.duty_activity[i])
    if duty == V.ACT_WORK and has_window:
        where = "渋谷の外(域外)" if bool(f.duty_outside[i]) else "渋谷"
        out.append(f"勤務: {where} {W17._days_word(int(t.work_days[i]))} "
                   f"{W17._hm(int(t.duty_open[i]))}-{W17._hm(int(t.duty_close[i]))}")
        out.append(f"出勤: {W17._hm(int(t.depart[i]))} 帰宅: {W17._hm(int(t.arrive[i]))}")
    elif duty == V.ACT_SCHOOL:
        stage = f.duty_stage[i] or p.col("school_stage")[i] or "学校"
        out.append(f"通学: {stage} {W17._days_word(int(f.work_days[i]))} "
                   f"{W17._hm(int(f.work_open[i]))}-{W17._hm(int(f.work_close[i]))}")
    if int(f.visit_days[i]):
        purpose = p.col("visit_purpose")[i] or "来街"
        cadence = p.col("visit_cadence")[i]
        out.append(f"来訪日: {W17._days_word(int(f.visit_days[i]))} 目的: {purpose}"
                   + (f" 頻度: {cadence}" if cadence else ""))
    if bool(t.stay[i]):
        out.append("渋谷に泊まる(就寝は宿泊施設)。")
    out.append(f"就寝: {W17._hm(int(f.bed_min[i]))}ごろ 睡眠{int(f.sleep_min[i])}分")
    if spec.stage == 1:
        out.append("")
        out.extend(IDENTITY_QUESTIONS)
        return "\n".join(out)
    head = [identity.strip(), ""] if identity.strip() else []
    return "\n".join(head + out + ["あなたが上で話したとおりの1週間を表にしてください。"])


def block_regex(spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts, i: int) -> str:
    """ブロック形式の構造化出力 regex。

    形: ``d0\\n<最初の行>(?:\\n<行>){1,8}\\n<最後の行>\\nd1…``。
    - 最初の行の開始は ``0000``・最後の行の終了は ``2400``(= §3「切れ目なく」の端点を
      **文法で**固定する。内側の連続性は regex では書けないので検査で数える)。
    - **0〜3 時台に始まる行からは 支度/乗車 を外す**(§3・D-63 (iii))。
    - 場所語は ``W17.place_set``(事実にない場所を出せない)。
    """
    acts_all = "|".join(V.ACTIVITY_WORDS)
    acts_night = "|".join(w for w in V.ACTIVITY_WORDS if w not in NIGHT_BAN_ACTS)
    places = "|".join(W17.place_set(f, i))
    tail = f" [0-4] (?:{{acts}}) (?:{places})"

    def line(start: str, end: str, night_only: bool | None) -> str:
        if night_only is True:
            return f"{start}-{end}" + tail.format(acts=acts_night)
        if night_only is False:
            return f"{start}-{end}" + tail.format(acts=acts_all)
        return (
            f"(?:{_NIGHT_START_RE}-{end}" + tail.format(acts=acts_night) + "|"
            + f"{_DAY_START_RE}-{end}" + tail.format(acts=acts_all) + ")"
        )

    first = line("0000", V.TIME_PATTERN, True)          # 0000 始まり=深夜側
    mid = line("", V.TIME_PATTERN, None)
    last = line("", "2400", None)
    lo, hi = spec.lines
    mid_lo, mid_hi = max(0, lo - 2), max(0, hi - 2)
    visit = int(f.visit_days[i])
    parts: list[str] = []
    for d in range(V.N_DAYS):
        if visit and not ((visit >> d) & 1):
            # 来訪日でない日も**在宅の 1 日**を書かせる(被覆率を測るため見出しだけにしない)
            pass
        parts.append(f"d{d}(?:\\n{first})(?:\\n{mid}){{{mid_lo},{mid_hi}}}(?:\\n{last})")
    return "\\n".join(parts) + "\\n?"


def arm_regex(spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts, i: int) -> str:
    """腕と体 → 構造化出力 regex(段1 は regex なし)。"""
    if spec.stage == 1:
        return ""
    if spec.block:
        return block_regex(spec, f, t, i)
    if spec.lines == (W17.LINES_PER_DAY_MIN, W17.LINES_PER_DAY_MAX):
        return W17.prompt_regex(f, i)
    base = W17.prompt_regex(f, i)
    old = f"{{{W17.LINES_PER_DAY_MIN},{W17.LINES_PER_DAY_MAX}}}"
    assert old in base, "本番 regex の行数指定が見つからない"
    return base.replace(old, f"{{{spec.lines[0]},{spec.lines[1]}}}")


def arm_prompt_of(
    spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts, i: int, identity: str = ""
) -> W17.SchedPrompt:
    """1 体ぶんのプロンプト(本番 ``SchedPrompt`` と**同じ 1 行の形**= fleet_gen 入力)。"""
    return W17.SchedPrompt(
        id=str(int(f.agent_id[i])),
        system=arm_system(spec, f, t, i),
        user=arm_user(spec, f, t, i, identity=identity),
        seed=arm_seed(spec.seed_tag, int(f.agent_id[i])),
        max_tokens=IDENTITY_MAX_TOKENS if spec.stage == 1 else spec.max_tokens,
        regex=arm_regex(spec, f, t, i),
    )


def arm_prompts(
    spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts, rows: Sequence[int] | np.ndarray,
    identities: dict[str, str] | None = None,
) -> list[W17.SchedPrompt]:
    """標本ぶんのプロンプト列(行順=``rows`` の順=決定論)。

    Note:
        逐次ループ宣言(P4): 標本体数ぶんのループ 1 本(2,000)。
    """
    ids = identities or {}
    return [
        arm_prompt_of(spec, f, t, int(r), identity=ids.get(str(int(f.agent_id[int(r)])), ""))
        for r in rows
    ]


# ================================================================= ファイル名規約
PROD_GLOBS: Final[tuple[str, ...]] = (
    W17.RESPONSES_GLOB, "w17_prompts*.jsonl", W17.SCHEDULE_NAME, "W17.header.json",
    W17.PILOT_PROMPTS_NAME, W17.PILOT_RESPONSES_NAME,
)


def trial_file(arm: str, suffix: str, *, stage: int = 0) -> str:
    """下見の出力名(``w17_trial_<arm>[_stage2]_<suffix>``)。"""
    tag = f"{arm}_stage{stage}" if stage else arm
    return f"w17_trial_{tag}_{suffix}"


def files_avoid_production_globs(names: Iterable[str]) -> list[str]:
    """本番 glob に当たる名前を返す(空なら安全)。**テストが機械検査する**(§7 リスク 8)。

    Example:
        >>> files_avoid_production_globs(["w17_trial_p1a_prompts.jsonl"])
        []
        >>> files_avoid_production_globs(["w17_responses.0of8.jsonl"])
        ['w17_responses.0of8.jsonl']
    """
    bad: list[str] = []
    for n in names:
        base = Path(n).name
        if any(fnmatch(base, g) for g in PROD_GLOBS):
            bad.append(n)
    return bad


def arm_dir(out_root: str | Path, arm: str) -> Path:
    return Path(out_root) / arm


def write_arm_prompts(
    out_root: str | Path, spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts,
    rows: Sequence[int] | np.ndarray, *, identities: dict[str, str] | None = None,
) -> dict[str, Any]:
    """腕のプロンプト jsonl を書く(1 行の形は本番の fleet_gen 入力と同じ)。"""
    d = arm_dir(out_root, spec.name)
    d.mkdir(parents=True, exist_ok=True)
    stage = 2 if (spec.stage == 2 and identities is not None) else spec.stage
    name = trial_file(spec.name, "prompts.jsonl", stage=stage if spec.stage else 0)
    bad = files_avoid_production_globs([name])
    if bad:  # pragma: no cover - 名前規約を変えたときだけ
        raise RuntimeError(f"本番 glob に当たる名前: {bad}")
    prompts = arm_prompts(spec, f, t, rows, identities=identities)
    path = d / name
    tok_sum = tok_max = 0
    with open(path, "wb") as fh:
        for p in prompts:
            fh.write(C.canonical_json_bytes(p.to_json()) + b"\n")
            tk = W17.estimate_tokens(p.system) + W17.estimate_tokens(p.user)
            tok_sum += tk
            tok_max = max(tok_max, tk)
    n = len(prompts)
    kinds: dict[str, int] = {}
    for r in rows:
        k = KIND_NAMES[int(f.kind[int(r)])]
        kinds[k] = kinds.get(k, 0) + 1
    return {
        "arm": spec.name,
        "stage": stage,
        "path": str(path),
        "name": name,
        "rows": n,
        "bytes": path.stat().st_size,
        "sha256": C.sha256_file(path),
        "prompts_sha256": W17.prompts_sha256(prompts),
        "system_sha256": _system_sha(prompts),
        "regex_sha256": _regex_sha(prompts),
        "prompt_tokens_mean": round(tok_sum / n, 2) if n else 0.0,
        "prompt_tokens_max": tok_max,
        "max_tokens": prompts[0].max_tokens if prompts else spec.max_tokens,
        "temperature": spec.temperature,
        "kinds": dict(sorted(kinds.items())),
    }


#: ``system_sha256`` に並べる代表の本数(P2 は体ごとに名前が入るので 2,000 通りになる)。
_SYSTEM_SHA_TOP: Final[int] = 12


def _system_sha(prompts: Sequence[W17.SchedPrompt]) -> dict[str, Any]:
    """相異なる system 文の SHA(先頭 16 桁)→ 件数。多い順に ``_SYSTEM_SHA_TOP`` 本まで。

    ``n_distinct`` が体数に近い腕(P2 は system の先頭に本人の名前が入る)は
    **vLLM の prefix キャッシュが効かない**=親の確認事項。``shared_prefix_chars`` は
    先頭から何文字が全体で共通かで、その目安になる。
    """
    seen: dict[str, int] = {}
    distinct: dict[str, None] = {}
    for p in prompts:
        h = C.sha256_bytes(p.system.encode("utf-8"))[:16]
        seen[h] = seen.get(h, 0) + 1
        distinct.setdefault(p.system, None)
    top = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))[:_SYSTEM_SHA_TOP]
    shared = len(os.path.commonprefix(list(distinct))) if distinct else 0
    return {
        "n_distinct": len(seen),
        "shared_prefix_chars": shared,
        "top": dict(top),
    }


def _regex_sha(prompts: Sequence[W17.SchedPrompt]) -> dict[str, Any]:
    seen: set[str] = set()
    first = ""
    for p in prompts:
        if p.regex and not first:
            first = p.regex
        seen.add(p.regex)
    return {
        "n_distinct": len(seen),
        "sha256_first": C.sha256_bytes(first.encode("utf-8"))[:16] if first else "",
        "chars_first": len(first),
    }


# ================================================================= ブロック形式パーサ
class Block(NamedTuple):
    """ブロック 1 件(``block_kind`` を持つ活動)。"""

    day: int
    start: int
    end: int
    block_kind: int
    activity: int
    place: int


_BLOCK_RE: Final[re.Pattern[str]] = re.compile(
    r"^(?P<h1>\d{1,2}):?(?P<m1>\d{2})\s*[-‐-―~〜～]\s*"
    r"(?P<h2>\d{1,2}):?(?P<m2>\d{2})\s+(?P<bk>[0-4])\s+(?P<act>\S+)\s+(?P<place>\S+)\s*$"
)
_DAY_RE: Final[re.Pattern[str]] = re.compile(r"^d([0-6])$")
_ACT_INDEX: Final[dict[str, int]] = {w: i for i, w in enumerate(V.ACTIVITY_WORDS)}
_PLACE_INDEX: Final[dict[str, int]] = {w: i for i, w in enumerate(V.PLACE_WORDS)}


def parse_blocks(raw: str) -> tuple[list[Block], dict[str, int]]:
    """ブロック形式の応答本文 → (ブロック列, 理由の計数)。**壊れた行はその行だけ捨てる**。

    ``V.parse_text`` と同じ流儀(正規化は ``V.canonical_text``・同義語表で直した印は
    ``fix_*`` で失敗率に数えない)。日をまたぐ行は ``V.parse_line`` と同様に 2 件へ割る。

    Example:
        >>> blocks, bad = parse_blocks("d0\\n0000-0700 3 就寝 自宅\\nだめな行")
        >>> [(b.block_kind, b.activity) for b in blocks], bad
        ([(3, 0)], {'format': 1})
    """
    out: list[Block] = []
    bad: dict[str, int] = {}
    day: int | None = None
    for ln in V.canonical_text(raw).split("\n"):  # 逐次: 応答の行数
        if not ln:
            continue
        head = _DAY_RE.match(ln)
        if head is not None:
            day = int(head.group(1))
            continue
        m = _BLOCK_RE.match(ln)
        if m is None or day is None:
            bad["format"] = bad.get("format", 0) + 1
            continue
        h1, m1 = int(m.group("h1")), int(m.group("m1"))
        h2, m2 = int(m.group("h2")), int(m.group("m2"))
        if m1 >= 60 or m2 >= 60 or h1 > 24 or h2 > 24:
            bad["bad_time"] = bad.get("bad_time", 0) + 1
            continue
        start, end = h1 * 60 + m1, h2 * 60 + m2
        if start >= V.MINUTES_PER_DAY or start == end:
            bad["bad_time"] = bad.get("bad_time", 0) + 1
            continue
        act = _ACT_INDEX.get(m.group("act"))
        if act is None:
            near = V.ACTIVITY_SYNONYMS.get(m.group("act"))
            if near is None:
                bad["unknown_activity"] = bad.get("unknown_activity", 0) + 1
                continue
            act = _ACT_INDEX[near]
            bad["fix_activity"] = bad.get("fix_activity", 0) + 1
        place = _PLACE_INDEX.get(m.group("place"))
        if place is None:
            near = V.PLACE_SYNONYMS.get(m.group("place"))
            if near is None:
                bad["unknown_place"] = bad.get("unknown_place", 0) + 1
                continue
            place = _PLACE_INDEX[near]
            bad["fix_place"] = bad.get("fix_place", 0) + 1
        bk = int(m.group("bk"))
        if end > start:
            out.append(Block(day, start, end, bk, act, place))
        else:  # 日をまたぐ行は割る(V.parse_line と同規約)
            out.append(Block(day, start, V.MINUTES_PER_DAY, bk, act, place))
            if end > 0:
                out.append(Block((day + 1) % V.N_DAYS, 0, end, bk, act, place))
        if len(out) >= V.MAX_ACTS_PER_RESPONSE:
            bad["truncated"] = bad.get("truncated", 0) + 1
            break
    return out, bad


def derive_block_kind(activity: int, place: int, home_in_area: bool) -> int:
    """(活動語, 場所語, 自宅が域内か)→ ``block_kind``(現行形式の腕のための決定論的写像)。

    Example:
        >>> derive_block_kind(V.ACT_SLEEP, V.PLACE_HOME, True)
        3
        >>> derive_block_kind(V.ACT_MOVE, V.PLACE_STATION, True)
        4
        >>> derive_block_kind(V.ACT_REST, V.PLACE_HOME, False)
        0
    """
    if activity == V.ACT_SLEEP:
        return BK_SLEEP
    if activity in (V.ACT_MOVE, V.ACT_RIDE):
        return BK_MOVE
    if place == V.PLACE_OUTSIDE:
        return BK_OUTSIDE
    if place == V.PLACE_HOME:
        return BK_HOME if home_in_area else BK_OUTSIDE
    return BK_INAREA


def block_kind_conflict(bk: int, activity: int, place: int, home_in_area: bool) -> str:
    """``block_kind`` と 活動語/場所語 の矛盾(空文字なら矛盾なし)。

    Example:
        >>> block_kind_conflict(1, V.ACT_SLEEP, V.PLACE_HOME, True)
        'sleep_kind'
        >>> block_kind_conflict(2, V.ACT_REST, V.PLACE_HOME, False)
        'home_outside'
        >>> block_kind_conflict(3, V.ACT_SLEEP, V.PLACE_HOTEL, False)
        ''
    """
    is_sleep = activity == V.ACT_SLEEP
    is_move = activity in (V.ACT_MOVE, V.ACT_RIDE)
    if is_sleep != (bk == BK_SLEEP):
        return "sleep_kind"
    if is_move != (bk == BK_MOVE):
        return "move_kind"
    if bk in (BK_SLEEP, BK_MOVE):
        return ""
    home_outside = place == V.PLACE_HOME and not home_in_area
    if bk == BK_HOME and not (place == V.PLACE_HOME and home_in_area):
        return "home_kind"
    if bk == BK_OUTSIDE and not (place == V.PLACE_OUTSIDE or home_outside):
        return "outside_kind"
    if bk == BK_INAREA and (place == V.PLACE_OUTSIDE or home_outside):
        return "home_outside" if home_outside else "inarea_kind"
    return ""


# ================================================================= 段1 の検査(§3)
_BULLET_HEAD: Final[re.Pattern[str]] = re.compile(r"^\s*(?:[-*・•>#\d]+[.)]?\s|【)")
_GREETING: Final[tuple[str, ...]] = (
    "こんにちは", "はじめまして", "初めまして", "と申します", "よろしくお願い",
    "失礼します", "お世話になっ",
)
_DIGITS: Final[re.Pattern[str]] = re.compile(r"\d+")
#: 固有名詞の疑い(**W14 残差方式の簡易版**= 事実行に無いカタカナ語・○○駅/店/線 など)。
_PROPER: Final[re.Pattern[str]] = re.compile(
    r"[ァ-ヶー]{3,}|[一-鿿]{2,}(?:駅|線|店|社|区|市|町|大学|高校|通り)"
)


def check_identity(text: str, facts: str) -> list[str]:
    """段1 の応答検査(字数 200〜420 と禁止 4 つ)。落ちた理由の list(空なら合格)。

    Example:
        >>> check_identity("あ" * 250, "事実")
        []
        >>> check_identity("短い", "事実")
        ['chars']
        >>> "bullet" in check_identity("あ" * 250 + "\\n- 箇条書き", "事実")
        True
    """
    body = V.canonical_text(text)
    why: list[str] = []
    if not (IDENTITY_CHARS_MIN <= len(body) <= IDENTITY_CHARS_MAX):
        why.append("chars")
    for tok in _PROPER.findall(body):  # 逐次: 応答の語数
        if tok not in facts:
            why.append("proper_noun")
            break
    for tok in _DIGITS.findall(body):
        if tok not in facts:
            why.append("number")
            break
    if any(_BULLET_HEAD.match(ln) for ln in text.split("\n")):
        why.append("bullet")
    if any(g in body for g in _GREETING):
        why.append("greeting")
    return why


# ================================================================= 取り込み(報告のみ)
@dataclass
class TrialReport:
    """腕ごとの検査結果(``w17_trial_<arm>_report.json`` の中身)。"""

    arm: str
    stage: int
    n_agents: int
    n_response_rows: int = 0
    n_with_response: int = 0
    parse_bad: dict[str, int] = field(default_factory=dict)
    n_parsed: int = 0
    n_kept: int = 0
    check_fail: dict[str, int] = field(default_factory=dict)
    n_check_failed: int = 0
    coverage: list[int] = field(default_factory=list)
    gaps: int = 0
    overlaps: int = 0
    day_sleep: list[int] = field(default_factory=list)
    lines_per_day: list[int] = field(default_factory=list)
    duty_dev: list[int] = field(default_factory=list)
    duty_dev_p1: list[int] = field(default_factory=list)
    completion_tokens: list[int] = field(default_factory=list)
    identity: dict[str, Any] = field(default_factory=dict)
    raking: dict[str, Any] = field(default_factory=dict)
    engine_modified: dict[str, Any] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    inputs: list[dict[str, Any]] = field(default_factory=list)

    # ---- 由来別の修正率(決定項 10)----
    @property
    def parse_fail_rate(self) -> float:
        bad = sum(v for k, v in self.parse_bad.items() if k in V.FAILURE_REASONS)
        return bad / max(1, bad + self.n_parsed)

    @property
    def llm_modified_rate(self) -> float:
        """**LLM 由来**= パース失敗 + 検査落ち / (パース失敗 + パースできた活動)。"""
        bad = sum(v for k, v in self.parse_bad.items() if k in V.FAILURE_REASONS)
        return (bad + self.n_check_failed) / max(1, bad + self.n_parsed)

    @staticmethod
    def _stats(xs: Sequence[int]) -> dict[str, float]:
        if not xs:
            return {"n": 0, "mean": 0.0, "sd": 0.0, "p50": 0.0, "p90": 0.0, "max": 0.0}
        a = np.asarray(xs, dtype=np.float64)
        return {
            "n": int(a.size), "mean": round(float(a.mean()), 3),
            "sd": round(float(a.std()), 3), "p50": round(float(np.percentile(a, 50)), 1),
            "p90": round(float(np.percentile(a, 90)), 1), "max": round(float(a.max()), 1),
        }

    def to_json(self) -> dict[str, Any]:
        cov = np.asarray(self.coverage, dtype=np.float64) / V.MINUTES_PER_DAY if self.coverage else np.zeros(0)
        sleep = np.asarray(self.day_sleep, dtype=np.float64) if self.day_sleep else np.zeros(0)
        return {
            "schema": "shibuya.build.sched/trial_report/1",
            "trial_version": TRIAL_VERSION,
            "arm": self.arm,
            "stage": self.stage,
            "n_agents": self.n_agents,
            "n_response_rows": self.n_response_rows,
            "n_with_response": self.n_with_response,
            "response_rate": round(self.n_with_response / max(1, self.n_agents), 6),
            "parse": {
                "n_parsed": self.n_parsed,
                "n_kept": self.n_kept,
                "fail_rate": round(self.parse_fail_rate, 6),
                "reasons": dict(sorted(self.parse_bad.items())),
            },
            "checks": {
                "coverage_mean": round(float(cov.mean()), 6) if cov.size else 0.0,
                "coverage_ge_0999_rate": round(float((cov >= 0.999).mean()), 6) if cov.size else 0.0,
                "n_agent_days": int(cov.size),
                "gaps": self.gaps,
                "overlaps": self.overlaps,
                "has_sleep_rate": round(float((sleep > 0).mean()), 6) if sleep.size else 0.0,
                "night_violations": self.check_fail.get("night", 0),
                "night_violation_rate": round(
                    self.check_fail.get("night", 0) / max(1, self.n_parsed), 6),
                "block_kind_conflicts": {
                    k[3:]: v for k, v in sorted(self.check_fail.items()) if k.startswith("bk_")
                },
                "stay_sleep_place_violations": self.check_fail.get("stay_sleep_place", 0),
                "lines_per_day": self._stats(self.lines_per_day),
                "duty_window_dev_min": self._stats(self.duty_dev),
                "duty_window_dev_vs_p1_min": self._stats(self.duty_dev_p1),
                "reasons": dict(sorted(self.check_fail.items())),
            },
            "modified": {
                "llm": {
                    "rate": round(self.llm_modified_rate, 6),
                    "n_parse_failed": sum(
                        v for k, v in self.parse_bad.items() if k in V.FAILURE_REASONS),
                    "n_check_failed": self.n_check_failed,
                    "denominator": sum(
                        v for k, v in self.parse_bad.items() if k in V.FAILURE_REASONS
                    ) + self.n_parsed,
                    "note": "パース失敗+検査落ち / (パース失敗+パースできた活動)。修復はしない。",
                },
                "engine": self.engine_modified,
            },
            "raking": self.raking,
            "identity": self.identity,
            "completion_tokens": self._stats(self.completion_tokens),
            "window_counters": dict(sorted(self.counters.items())),
            "inputs": self.inputs,
            "outputs": self.outputs,
        }


def _response_rows(paths: Sequence[Path]) -> Iterator[tuple[str, str, int]]:
    """応答 jsonl → ``(id, text, completion_tokens)``。同じ id は**最後の行**を採る。"""
    last: dict[str, tuple[str, int]] = {}
    order: list[str] = []
    for p in paths:
        with open(p, "r", encoding="utf-8") as fh:
            for line in fh:  # 逐次: 応答行数
                if not line.strip():
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                rid = str(d.get("id", ""))
                if not rid:
                    continue
                if rid not in last:
                    order.append(rid)
                last[rid] = (str(d.get("text", "") or ""), int(d.get("completion_tokens", 0) or 0))
    for rid in order:
        text, tok = last[rid]
        yield rid, text, tok


def _to_blocks(
    spec: ArmSpec, text: str, home_in: bool
) -> tuple[list[Block], dict[str, int]]:
    """腕に応じたパーサ(現行形式 / ブロック形式)。現行形式は ``block_kind`` を派生させる。"""
    if spec.block:
        return parse_blocks(text)
    acts, bad = V.parse_text(text)
    return (
        [Block(a.day, a.start, min(a.end, V.MINUTES_PER_DAY),
               derive_block_kind(a.activity, a.place, home_in), a.activity, a.place)
         for a in acts],
        bad,
    )


def ingest_arm(
    world_dir: str | Path,
    out_root: str | Path,
    spec: ArmSpec,
    f: W17.AgentFacts,
    t: TrialFacts,
    rows: Sequence[int] | np.ndarray,
    responses: Sequence[Path],
    *,
    write_parquet: bool = True,
    curves: dict[str, np.ndarray] | None = None,
    share: np.ndarray | None = None,
) -> TrialReport:
    """応答を読み、**修復せずに**検査して報告する(P0b だけ修復版も別に出す)。

    Note:
        逐次ループ宣言(P4): 応答体数ぶんのループ 1 本(下見 2,000)。
    """
    world_dir = Path(world_dir)
    rows = np.asarray(rows, dtype=np.int64)
    rep = TrialReport(arm=spec.name, stage=spec.stage, n_agents=int(rows.size))
    rep.counters = dict(t.counters)
    rep.inputs = [
        {"path": Path(p).name, "sha256": C.sha256_file(Path(p)), "bytes": Path(p).stat().st_size}
        for p in responses
    ]
    id_to_row = {str(int(f.agent_id[int(r)])): int(r) for r in rows}

    # --- 段1(同一性)は別の検査 ---
    if spec.stage == 1:
        ok = 0
        why_counts: dict[str, int] = {}
        chars: list[int] = []
        for rid, text, tok in _response_rows(responses):
            r = id_to_row.get(rid)
            if r is None:
                continue
            rep.n_with_response += 1
            if tok > 0:
                rep.completion_tokens.append(tok)
            chars.append(len(V.canonical_text(text)))
            why = check_identity(text, arm_user(spec, f, t, r))
            if not why:
                ok += 1
            for w in why:
                why_counts[w] = why_counts.get(w, 0) + 1
        rep.n_response_rows = rep.n_with_response
        rep.identity = {
            "n_checked": rep.n_with_response,
            "pass_rate": round(ok / max(1, rep.n_with_response), 6),
            "reasons": dict(sorted(why_counts.items())),
            "chars": TrialReport._stats(chars),
        }
        return rep

    b_agent: list[int] = []
    b_day: list[int] = []
    b_start: list[int] = []
    b_end: list[int] = []
    b_act: list[int] = []
    b_place: list[int] = []
    b_bk: list[int] = []
    raw_by_row: dict[int, list[V.Act]] = {}

    for rid, text, tok in _response_rows(responses):  # 逐次(P4): 応答体数ぶん
        r = id_to_row.get(rid)
        if r is None:
            continue
        rep.n_with_response += 1
        if tok > 0:
            rep.completion_tokens.append(tok)
        home_in = int(f.home_cell[r]) >= 0
        blocks, bad = _to_blocks(spec, text, home_in)
        for k, v in bad.items():
            rep.parse_bad[k] = rep.parse_bad.get(k, 0) + v
        rep.n_parsed += len(blocks)
        if spec.repair:
            raw_by_row[r] = [V.Act(b.day, b.start, b.end, b.activity, b.place) for b in blocks]
        kept = _check_blocks(rep, spec, f, t, r, blocks, home_in)
        for b in kept:
            b_agent.append(r)
            b_day.append(b.day)
            b_start.append(b.start)
            b_end.append(min(b.end, V.MINUTES_PER_DAY))
            b_act.append(b.activity)
            b_place.append(b.place)
            b_bk.append(b.block_kind)
    rep.n_response_rows = rep.n_with_response
    rep.n_kept = len(b_agent)

    agent_row = np.asarray(b_agent, dtype=np.int32)
    day = np.asarray(b_day, dtype=np.int32)
    start = np.asarray(b_start, dtype=np.int32)
    end = np.asarray(b_end, dtype=np.int32)
    activity = np.asarray(b_act, dtype=np.int8)
    place = np.asarray(b_place, dtype=np.int8)
    bkind = np.asarray(b_bk, dtype=np.int8)

    cv = curves if curves is not None else W17.hour_curves(world_dir)
    rep.raking = _rake_both(spec, agent_row, day, start, end, activity, cv)
    rep.engine_modified = {
        "rake_n_moved": rep.raking.get(f"{spec.rake_fracs[0]:.2f}", {}).get("n_moved", 0),
        "repair_n_modified": 0,
        "repair_n_dropped": 0,
        "denominator": rep.n_kept,
        "rate": round(
            rep.raking.get(f"{spec.rake_fracs[0]:.2f}", {}).get("n_moved", 0)
            / max(1, rep.n_kept), 6),
        "note": "エンジン由来= 修復 + raking。下見は修復しない(P0b の repaired だけ別掲)。",
    }

    if write_parquet:
        d = arm_dir(out_root, spec.name)
        d.mkdir(parents=True, exist_ok=True)
        rep.outputs.append(_write_trial_parquet(
            d / trial_file(spec.name, "schedule.parquet"),
            f, spec.name, agent_row, day, start, end, activity, place, bkind))

    # --- P0b は「前値と同じ土俵」= 本番の修復を通した版も別に出す ---
    if spec.repair and raw_by_row:
        sh = share if share is not None else W17.open_share(world_dir)
        ctr = W17.RepairCounters()
        r_agent: list[int] = []
        r_day: list[int] = []
        r_start: list[int] = []
        r_end: list[int] = []
        r_act: list[int] = []
        r_place: list[int] = []
        r_bk: list[int] = []
        n_mod = n_drop = 0
        for r in sorted(raw_by_row):  # 逐次: 応答体数ぶん
            acts, flags, dropped = W17.repair(raw_by_row[r], f, r, sh, ctr)
            n_mod += int(sum(1 for x in flags if x))
            n_drop += int(dropped)
            home_in = int(f.home_cell[r]) >= 0
            for a in acts:
                r_agent.append(r)
                r_day.append(a.day)
                r_start.append(a.start)
                r_end.append(min(a.end, V.MINUTES_PER_DAY))
                r_act.append(a.activity)
                r_place.append(a.place)
                r_bk.append(derive_block_kind(a.activity, a.place, home_in))
        rep.engine_modified["repair_n_modified"] = n_mod
        rep.engine_modified["repair_n_dropped"] = n_drop
        rep.engine_modified["repair_rules"] = dict(sorted(ctr.counts.items()))
        rep.engine_modified["repaired_rows"] = len(r_agent)
        rep.engine_modified["rate"] = round(
            (n_mod + n_drop + rep.engine_modified["rake_n_moved"]) / max(1, rep.n_kept), 6)
        if write_parquet:
            d = arm_dir(out_root, spec.name)
            rep.outputs.append(_write_trial_parquet(
                d / trial_file(spec.name, "repaired_schedule.parquet"), f,
                spec.name + "_repaired",
                np.asarray(r_agent, dtype=np.int32), np.asarray(r_day, dtype=np.int32),
                np.asarray(r_start, dtype=np.int32), np.asarray(r_end, dtype=np.int32),
                np.asarray(r_act, dtype=np.int8), np.asarray(r_place, dtype=np.int8),
                np.asarray(r_bk, dtype=np.int8)))
    return rep


def _check_blocks(
    rep: TrialReport, spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts, r: int,
    blocks: Sequence[Block], home_in: bool,
) -> list[Block]:
    """1 体ぶんの検査(**修復しない**=数えるだけ)。返り値=そのまま採る活動。"""
    by_day: list[list[Block]] = [[] for _ in range(V.N_DAYS)]
    for b in blocks:
        if 0 <= b.day < V.N_DAYS:
            by_day[b.day].append(b)
    kept: list[Block] = []
    duty = int(f.duty_activity[r])
    for d in range(V.N_DAYS):  # 逐次: 7 回
        acts = sorted(by_day[d], key=lambda x: (x.start, x.end))
        if not acts:
            rep.coverage.append(0)
            rep.day_sleep.append(0)
            rep.lines_per_day.append(0)
            continue
        rep.lines_per_day.append(len(acts))
        covered = np.zeros(V.MINUTES_PER_DAY, dtype=bool)
        sleep_min = 0
        prev_end = 0
        for b in acts:
            lo, hi = max(0, b.start), min(V.MINUTES_PER_DAY, b.end)
            if hi > lo:
                covered[lo:hi] = True
            if b.activity == V.ACT_SLEEP:
                sleep_min += max(0, hi - lo)
            if b.start < prev_end:
                rep.overlaps += 1
            elif b.start > prev_end:
                rep.gaps += 1
            prev_end = max(prev_end, hi)
            fail = ""
            if b.start < NIGHT_END_MIN and V.ACTIVITY_WORDS[b.activity] in NIGHT_BAN_ACTS:
                fail = "night"
            else:
                why = block_kind_conflict(b.block_kind, b.activity, b.place, home_in)
                if why:
                    fail = "bk_" + why
            # 決定項 12: 宿泊する体の**来訪日の**就寝地は宿泊施設(在圏)。
            # 来訪日でない日は舞台の外の自宅で寝るので対象外。
            if not fail and bool(t.stay[r]) and b.activity == V.ACT_SLEEP \
                    and bool((int(f.visit_days[r]) >> d) & 1) and b.place != V.PLACE_HOTEL:
                fail = "stay_sleep_place"
            if fail:
                rep.check_fail[fail] = rep.check_fail.get(fail, 0) + 1
                rep.n_check_failed += 1
            kept.append(b)
        if prev_end < V.MINUTES_PER_DAY:
            rep.gaps += 1
        rep.coverage.append(int(covered.sum()))
        rep.day_sleep.append(sleep_min)
        # --- 勤務窓との差(§2-6 duty_clamped の置換)---
        if duty >= 0:
            duty_acts = [b for b in acts if b.activity in (V.ACT_WORK, V.ACT_SCHOOL)]
            if duty_acts:
                s = min(b.start for b in duty_acts)
                e = max(b.end for b in duty_acts)
                if (int(f.work_days[r]) >> d) & 1 and int(f.work_open[r]) >= 0:
                    rep.duty_dev.append(abs(s - int(f.work_open[r])))
                    rep.duty_dev.append(abs(e - min(V.MINUTES_PER_DAY, int(f.work_close[r]))))
                if (int(t.work_days[r]) >> d) & 1 and int(t.duty_open[r]) >= 0:
                    rep.duty_dev_p1.append(abs(s - int(t.duty_open[r])))
                    rep.duty_dev_p1.append(abs(e - min(V.MINUTES_PER_DAY, int(t.duty_close[r]))))
    return kept


def _rake_both(
    spec: ArmSpec, agent_row: np.ndarray, day: np.ndarray, start: np.ndarray,
    end: np.ndarray, activity: np.ndarray, curves: dict[str, np.ndarray],
) -> dict[str, Any]:
    """決定項 9: raking を **12% と 0% の両方**で通して JSD の前後を出す(配列は壊さない)。"""
    out: dict[str, Any] = {}
    for frac in spec.rake_fracs:
        s, e = start.copy(), end.copy()
        mod = np.zeros(s.size, dtype=bool)
        r = W17.rake(agent_row, day, s, e, activity, mod, curves,
                     budget_rows=int(frac * s.size))
        out[f"{frac:.2f}"] = {
            "budget_rows": r.budget_rows,
            "n_moved": r.n_moved,
            "n_candidates": r.n_candidates,
            "rolled_back": r.rolled_back,
            "jsd_before": {k: round(v, 6) for k, v in sorted(r.jsd_before.items())},
            "jsd_after": {k: round(v, 6) for k, v in sorted(r.jsd_after.items())},
            "jsd_max_before": round(r.max_before, 6),
            "jsd_max_after": round(r.max_after, 6),
        }
    return out


#: 下見 parquet のスキーマ(本番 W17 の列 + ``block_kind`` + ``arm``)。
TRIAL_SCHEMA: Final[pa.Schema] = pa.schema(
    [
        ("agent_id", pa.int32()),
        ("day", pa.int8()),
        ("seq", pa.int16()),
        ("start_min", pa.int16()),
        ("end_min", pa.int16()),
        ("activity_code", pa.int8()),
        ("place_kind", pa.int8()),
        ("target_cell", pa.int32()),
        ("block_kind", pa.int8()),
        ("arm", pa.string()),
    ]
)


def _write_trial_parquet(
    path: Path, f: W17.AgentFacts, arm: str, agent_row: np.ndarray, day: np.ndarray,
    start: np.ndarray, end: np.ndarray, activity: np.ndarray, place: np.ndarray,
    bkind: np.ndarray,
) -> dict[str, Any]:
    """下見の活動表 parquet(``agents.weekly._COLUMNS`` をそのまま含む=物差しが読める)。"""
    order = np.lexsort((start, day, agent_row)).astype(np.int64)
    agent_row, day, start, end = agent_row[order], day[order], start[order], end[order]
    activity, place, bkind = activity[order], place[order], bkind[order]
    seq = W17._sequence_within_group(agent_row, day)
    cells = W17._target_cells(f, agent_row, place)
    table = pa.table(
        {
            "agent_id": pa.array(f.agent_id[agent_row].astype(np.int32), type=pa.int32()),
            "day": pa.array(day.astype(np.int8), type=pa.int8()),
            "seq": pa.array(seq.astype(np.int16), type=pa.int16()),
            "start_min": pa.array(start.astype(np.int16), type=pa.int16()),
            "end_min": pa.array(end.astype(np.int16), type=pa.int16()),
            "activity_code": pa.array(activity.astype(np.int8), type=pa.int8()),
            "place_kind": pa.array(place.astype(np.int8), type=pa.int8()),
            "target_cell": pa.array(cells.astype(np.int32), type=pa.int32()),
            "block_kind": pa.array(bkind.astype(np.int8), type=pa.int8()),
            "arm": pa.array([arm] * int(agent_row.size), type=pa.string()),
        },
        schema=TRIAL_SCHEMA,
    )
    pq.write_table(table, path, compression="zstd", compression_level=3, version="2.6")
    return {
        "path": str(path), "name": path.name, "rows": int(agent_row.size),
        "bytes": path.stat().st_size, "sha256": C.sha256_file(path),
    }


# ================================================================= モック応答(検収用)
def mock_text(spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts, i: int) -> str:
    """その体の事実に素直に従った応答本文(**検収のドライラン用**・LLM は呼ばない)。

    現行形式は本番テストの ``mock_week`` と同じ発想。ブロック形式は「0000 から 2400 まで
    切れ目なく・就寝あり・深夜に支度/乗車なし」を満たす 1 週間を組む。
    """
    if spec.stage == 1:
        # 検査(字数 200〜420・禁止 4 つ)を**通る**形にする= report の全欄が埋まることを示す。
        # 固有名詞も数字も入れない(モックが検査を素通りしていないことは tests が別に見る)。
        base = (
            "朝はだいたい決まった時間に目が覚めて、顔を洗って着替えて、"
            "そのまま家を出るのが毎日の流れですね。"
            "駅までは歩いて向かって、だいたい同じ車両に乗って出ていきます。"
            "仕事が終わったら、まっすぐ帰る日もあれば、"
            "途中で買い物をしたり、軽く食べて帰る日もあります。"
            "休みの日は朝もゆっくりで、昼ごろに出かけて買い物をするくらいで、"
            "あとは家で過ごしていることが多いです。"
        )
        while len(base) < IDENTITY_CHARS_MIN:  # 逐次: 高々数回
            base += "曜日によって多少はずれますが、だいたいこの繰り返しです。"
        return base[:IDENTITY_CHARS_MAX]

    home_in = int(f.home_cell[i]) >= 0
    duty = int(f.duty_activity[i])
    lo = int(t.duty_open[i]) if int(t.duty_open[i]) >= 0 else int(f.work_open[i])
    hi = int(t.duty_close[i]) if int(t.duty_close[i]) >= 0 else int(f.work_close[i])
    lo = min(max(int(lo), 300), 1_200) if lo and lo > 0 else 540
    hi = min(max(int(hi), lo + 240), 1_380)
    days = int(t.work_days[i]) if int(t.duty_open[i]) >= 0 else int(f.work_days[i])
    visit = int(f.visit_days[i])
    place_ok = set(W17.place_set(f, i))
    duty_place = V.PLACE_WORDS[V.PLACE_SCHOOL if duty == V.ACT_SCHOOL else V.PLACE_WORK]
    if duty_place not in place_ok:
        duty_place = V.PLACE_WORDS[V.PLACE_OUTSIDE] if V.PLACE_WORDS[V.PLACE_OUTSIDE] in place_ok \
            else V.PLACE_WORDS[V.PLACE_STREET]
    out_word = V.PLACE_WORDS[V.PLACE_OUTSIDE] if V.PLACE_WORDS[V.PLACE_OUTSIDE] in place_ok \
        else V.PLACE_WORDS[V.PLACE_STREET]
    home_word = V.PLACE_WORDS[V.PLACE_HOME]

    lines: list[str] = []
    for d in range(V.N_DAYS):
        lines.append(f"d{d}")
        works = duty >= 0 and (days >> d) & 1
        visiting = bool(visit) and bool((visit >> d) & 1)
        # 決定項 12: 宿泊する体は**来訪日だけ**宿泊施設で寝る(それ以外の日は自宅)。
        sleep_place = V.PLACE_WORDS[V.PLACE_HOTEL] if (bool(t.stay[i]) and visiting)             else home_word
        if not spec.block:
            if visiting:
                lines += [
                    V.format_body(600, 630, V.ACT_RIDE, V.PLACE_STATION),
                    V.format_body(630, 780, V.ACT_SHOP, V.PLACE_SHOP),
                    V.format_body(780, 840, V.ACT_MEAL, V.PLACE_FOOD),
                    V.format_body(840, 900, V.ACT_RIDE, V.PLACE_OUTSIDE),
                ]
            elif works:
                lines += [
                    V.format_body(0, max(60, lo - 90), V.ACT_SLEEP, V.PLACE_HOME),
                    V.format_body(max(60, lo - 90), max(90, lo - 45), V.ACT_PREP, V.PLACE_HOME),
                    V.format_body(max(90, lo - 45), lo, V.ACT_MOVE, V.PLACE_STATION),
                    V.format_body(lo, hi, duty, V.PLACE_SCHOOL if duty == V.ACT_SCHOOL
                                  else V.PLACE_WORK),
                    V.format_body(hi, min(1440, hi + 60), V.ACT_MEAL, V.PLACE_FOOD),
                ]
            else:
                lines += [
                    V.format_body(0, 420, V.ACT_SLEEP, V.PLACE_HOME),
                    V.format_body(420, 480, V.ACT_PREP, V.PLACE_HOME),
                    V.format_body(660, 780, V.ACT_SHOP, V.PLACE_SHOP),
                    V.format_body(780, 840, V.ACT_MEAL, V.PLACE_FOOD),
                ]
            continue
        # --- ブロック形式(切れ目なし・0000-2400)---
        if works:
            cuts = [(0, max(60, lo - 90), "就寝", sleep_place),
                    (max(60, lo - 90), max(90, lo - 45), "支度", home_word),
                    (max(90, lo - 45), lo, "移動", "駅"),
                    (lo, hi, V.ACTIVITY_WORDS[duty], duty_place),
                    (hi, min(1_410, hi + 60), "移動", "駅"),
                    (min(1_410, hi + 60), 1_440, "就寝", sleep_place)]
        elif visiting:
            cuts = [(0, 540, "就寝", sleep_place),
                    (540, 600, "乗車", "駅"),
                    (600, 780, "買物", "物販店"),
                    (780, 840, "食事", "飲食店"),
                    (840, 900, "乗車", out_word),
                    (900, 1_440, "就寝", sleep_place)]
        else:
            cuts = [(0, 480, "就寝", sleep_place),
                    (480, 540, "支度", home_word),
                    (540, 780, "休憩", home_word),
                    (780, 840, "食事", "飲食店"),
                    (840, 1_380, "休憩", home_word),
                    (1_380, 1_440, "就寝", sleep_place)]
        for s, e, act, pl in cuts:
            if e <= s:
                continue
            if pl not in place_ok:
                pl = out_word if out_word in place_ok else home_word
            bk = derive_block_kind(_ACT_INDEX[act], _PLACE_INDEX[pl], home_in)
            lines.append(f"{s // 60:02d}{s % 60:02d}-{e // 60:02d}{e % 60:02d} {bk} {act} {pl}")
    return "\n".join(lines)


def write_mock_responses(
    out_root: str | Path, spec: ArmSpec, f: W17.AgentFacts, t: TrialFacts,
    rows: Sequence[int] | np.ndarray,
) -> Path:
    """検収のドライラン用のモック応答 jsonl(``fleet_gen`` の出力形式)。"""
    d = arm_dir(out_root, spec.name)
    d.mkdir(parents=True, exist_ok=True)
    path = d / trial_file(spec.name, "mock_responses.jsonl",
                          stage=spec.stage if spec.stage else 0)
    bad = files_avoid_production_globs([path.name])
    if bad:  # pragma: no cover
        raise RuntimeError(f"本番 glob に当たる名前: {bad}")
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:  # 逐次: 標本体数ぶん
            i = int(r)
            text = mock_text(spec, f, t, i)
            fh.write(json.dumps({
                "id": str(int(f.agent_id[i])), "rep": 0, "model": "mock",
                "endpoint": "mock", "text": text, "finish_reason": "stop",
                "prompt_tokens": 0, "completion_tokens": max(1, len(text) // 2),
                "latency_s": 0.0,
            }, ensure_ascii=False) + "\n")
    return path


# ================================================================= CLI
def _rss_mb() -> float:
    """常駐セット[MB](報告用・ハッシュ対象には入れない)。"""
    try:  # Windows
        import ctypes
        from ctypes import wintypes

        class _PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        k32 = ctypes.WinDLL("kernel32")
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi")
        psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(_PMC), wintypes.DWORD]
        pmc = _PMC()
        pmc.cb = ctypes.sizeof(_PMC)
        if not psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return 0.0
        return round(pmc.WorkingSetSize / 1e6, 1)
    except Exception:  # pragma: no cover - 非 Windows
        try:
            import resource

            return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)
        except Exception:
            return 0.0


def _parse_per_kind(spec: str | None) -> dict[int, int] | None:
    """``--n-per-kind``: ``"40"``(全種別 40)か ``"0=100,3=20"``(種別ごと)。"""
    if not spec:
        return None
    s = str(spec).strip()
    if "=" not in s:
        n = int(s)
        return {k: n for k in TRIAL_N_PER_KIND}
    out = dict(TRIAL_N_PER_KIND)
    for part in s.split(","):
        k, _, v = part.partition("=")
        out[int(k)] = int(v)
    return out


def _load_identities(path: str | Path) -> dict[str, str]:
    """段1 の応答 jsonl → ``{agent_id: 本人の言葉}``(検査に落ちた体は空=事実だけで書かせる)。"""
    out: dict[str, str] = {}
    for rid, text, _tok in _response_rows([Path(path)]):
        body = V.canonical_text(text)
        out[rid] = body if not check_identity(text, "") or len(body) >= IDENTITY_CHARS_MIN else ""
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m shibuya.build.sched.trial")
    ap.add_argument("--arm", required=True, help=f"腕({', '.join(sorted(ARMS))} または {ARM_FROZEN})")
    ap.add_argument("--out", type=Path, default=Path("data/world/v2/trials"),
                    help="下見の出力根(既定 data/world/v2/trials)")
    ap.add_argument("--world", type=Path, default=Path("data/world/v2"), help="W16/W7/W6/W12 の場所")
    ap.add_argument("--data", type=Path, default=Path("data"), help="入力データ根(プール)")
    ap.add_argument("--anchor", type=Path, default=None, help="commute_time_dist_r3.json の場所")
    ap.add_argument("--build-anchor", action="store_true",
                    help="第31/36表の xlsx からアンカー台帳を作り直す")
    ap.add_argument("--n-per-kind", default="", help='種別ごとの体数("40" か "0=100,3=20")')
    ap.add_argument("--stage", type=int, default=0, help="2 段腕の段(1=同一性 / 2=週次表)")
    ap.add_argument("--identity", type=Path, default=None, help="段1 の応答 jsonl(--stage 2 用)")
    ap.add_argument("--model-tag", default="", help='"32b" で 200 体の比較腕にする')
    ap.add_argument("--ingest", type=Path, action="append", default=None, help="応答 jsonl")
    ap.add_argument("--mock", action="store_true", help="モック応答を書いてそれを取り込む")
    ap.add_argument("--no-absent", action="store_true", help="行動者率による欠勤を引かない")
    ap.add_argument("--stay-kinds", default="", help="宿泊客とみなす種別(既定 7=訪日)")
    ap.add_argument("--no-parquet", action="store_true", help="parquet を書かない")
    args = ap.parse_args(argv)

    t0 = time.perf_counter()
    out_root = args.out.resolve()
    anchor_file = args.anchor or anchor_path()
    if args.build_anchor:
        doc = build_anchor(args.data / "research_cache", anchor_file)
        print(f"[anchor] {anchor_file} rows={len(doc['depart']['rows'])} "
              f"bins={len(doc['depart']['bins'])}/{len(doc['return']['bins'])} "
              f"sha256={C.sha256_file(Path(anchor_file))[:16]}…")

    arm_name = str(args.arm).strip().lower().replace("-", "_")
    if args.model_tag.strip().lower() == "32b" and arm_name == "p2":
        arm_name = "p2_32b"

    facts = W17.build_facts(args.world, args.data)
    if arm_name == ARM_FROZEN:  # P0 = 凍結資産を読むだけ
        return _report_frozen(args.world, out_root, facts, args)

    spec = arm_of(arm_name)
    if args.stage:
        spec = ArmSpec(**{**spec.__dict__, "stage": int(args.stage)})
    try:
        anchor = load_anchor(anchor_file)
    except FileNotFoundError:
        print(f"アンカー台帳が無い: {anchor_file}(--build-anchor で作る)", file=sys.stderr)
        return 2
    stay = tuple(int(x) for x in args.stay_kinds.split(",") if x.strip()) \
        if args.stay_kinds else STAY_KINDS_DEFAULT
    rows = sample_rows(facts, _parse_per_kind(args.n_per_kind), total=spec.n_total)
    tf = draw_windows(facts, anchor, rows=rows, absent=not args.no_absent, stay_kinds=stay)

    identities = None
    if spec.stage == 2 and args.identity is not None:
        identities = _load_identities(args.identity)
    rec = write_arm_prompts(out_root, spec, facts, tf, rows, identities=identities)
    print(f"[{spec.name}] {rec['name']} rows={rec['rows']} sha256={rec['sha256'][:16]}… "
          f"prompts_sha256={rec['prompts_sha256'][:16]}… bytes={rec['bytes']:,} "
          f"入力tok 平均={rec['prompt_tokens_mean']} 最大={rec['prompt_tokens_max']} "
          f"max_tokens={rec['max_tokens']} regex={rec['regex_sha256']}")
    print(f"[{spec.name}] 種別内訳 {rec['kinds']}")
    print(f"[{spec.name}] 窓の計数 {dict(sorted(tf.counters.items()))}")

    resp: list[Path] = list(args.ingest or [])
    if args.mock:
        resp.append(write_mock_responses(out_root, spec, facts, tf, rows))
    if not resp:
        print(f"[{spec.name}] 応答なし= プロンプトだけ書いた "
              f"({time.perf_counter() - t0:.2f}s RSS={_rss_mb()} MB)")
        return 0
    rep = ingest_arm(args.world, out_root, spec, facts, tf, rows, resp,
                     write_parquet=not args.no_parquet)
    body = rep.to_json()
    body["prompts"] = rec
    body["elapsed_s"] = round(time.perf_counter() - t0, 2)
    body["rss_mb"] = _rss_mb()
    d = arm_dir(out_root, spec.name)
    rpath = d / trial_file(spec.name, "report.json", stage=spec.stage if spec.stage else 0)
    rpath.write_bytes(json.dumps(body, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    for key in ("n_agents", "n_with_response", "parse", "checks", "modified", "raking",
                "identity", "completion_tokens", "window_counters"):
        print(f"[{spec.name}] {key} = {json.dumps(body[key], ensure_ascii=False)}")
    print(f"[{spec.name}] report {rpath} ({body['elapsed_s']}s RSS={body['rss_mb']} MB)")
    return 0


def _report_frozen(world: Path, out_root: Path, facts: W17.AgentFacts, args) -> int:
    """``--arm P0``: 凍結資産を**読むだけ**の前値記録(書き換えない・呼 0)。"""
    path = Path(world) / W17.SCHEDULE_NAME
    rows = sample_rows(facts, _parse_per_kind(args.n_per_kind))
    body: dict[str, Any] = {
        "schema": "shibuya.build.sched/trial_report/1",
        "trial_version": TRIAL_VERSION,
        "arm": ARM_FROZEN,
        "n_calls": 0,
        "note": "P0 は凍結資産を読むだけ(前値の記録)。物差しは tools/w17/diversity_yardstick.py。",
        "n_agents": int(rows.size),
        "sample_agent_ids_head": [int(x) for x in facts.agent_id[rows[:10]]],
    }
    if path.exists():
        body["frozen_asset"] = {
            "path": str(path), "name": path.name, "bytes": path.stat().st_size,
            "sha256": C.sha256_file(path),
            "rows": int(pq.ParquetFile(path).metadata.num_rows),
        }
    else:
        body["frozen_asset"] = None
    d = arm_dir(out_root, ARM_FROZEN)
    d.mkdir(parents=True, exist_ok=True)
    rpath = d / trial_file(ARM_FROZEN, "report.json")
    rpath.write_bytes(json.dumps(body, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    print(f"[p0] {rpath} frozen={body['frozen_asset']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
