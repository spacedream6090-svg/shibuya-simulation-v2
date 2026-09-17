# -*- coding: utf-8 -*-
"""holdout_compare.py — **封印された KDDI holdout を 1 回だけ開いて**形状5指標を照合する。

規律(これを破ると C7 の受入そのものが無効になる)
- 世界データ構築仕様書 §0-5「**holdout規律**: KDDI形状5指標・スクランブル通行量・
  訪日訪問率/滞在時間・商圏シェアは構築に**一切使わない**(総量1スカラーのみ)」。
- 実装計画書 §9.1 C7「**holdout照合は事後1回のみ**(KDDI形状5指標)」。
- パターン台帳 D1′「値は**形状と比のみ**(絶対水準不使用)」。
  → 本ツールは**シェア・順位・比しか出さない**。実数(拡大推計値)は
     読み取り直後に正規化して捨て、報告にも JSON にも載せない。

封印の扱い
1. ``--open-seal`` を**明示**しないと 1 バイトも読まない(付け忘れで開くことがない)。
2. ``W19`` の封印(``data/world/v2/w19_freeze.json`` の ``holdout_seal``)を先に読み、
   メンバーの **sha256 が封印時と一致**することを確認する(取り違え・差し替えの検出)。
3. **開封記録**(``holdout_open_record.json``)を書く(既存の記録は ``previous_openings`` に残る・第176)。既に記録があれば ``--force``
   なしでは**拒否**する(=「事後1回のみ」の機械的な担保)。
4. ``--manifest <run_manifest.json> --write-manifest`` を付けたときだけ、その manifest へ
   ``holdout_open`` 欄を足す。既定は**記録ファイルだけ**を書き、manifest へ入れる断片を印字する。

生データの形(**本ツールは書式を仮定し、外れたら止まる**)
    ``data/realworld/kddi_la/la_raw_powerbi_2024.json`` は Power BI 公開ダッシュボード由来の
    テーブル束で、答申(v2-world-data-build-research.md §4.2 の実測構造表)によれば

      | テーブル | 件数 | 粒度 |
      |---|---|---|
      | ``taizai_seibetu``    | 20,112 | 滞在5エリア × 年 × 月 × **時間帯(5-28時=24区分)** × 性別 |
      | ``taizai_zokuseibetu``|  1,257 | 滞在5エリア × 年 × 月 × 属性(居住者/勤務者/来街者) |

    欄名は ``--field-map`` で差し替えられる(既定は別名表による best-effort)。
    **合わなければ例外で止まる**=推測で埋めない(CLAUDE.md §5)。

事前登録の版(``--prereg-version``)
    既定 ``v1.2`` = **1 ランの点**を 5 指標の線で合否にする(従来の挙動・1 バイトも変えない)。
    ``v1.3`` = ``docs/bench/c7/prereg_arms_v1.md`` §7 の **seed アンサンブル判定**。
    ``--occupancy`` を seed の本数だけ並べる(2 本以上が必須)。計算は ``prereg_v13.py``
    (家族 95% の区間・同値検定・H3 の格下げ・H1 の昼窓・GET 包絡・fair CRPS)。
    **合格線 H1〜H5 の値は v1.2 と同じ**——変わるのは線の当て方だけ。

テストは合成 holdout(同じ形の偽データ)で行う(``tests/c7/test_holdout_compare.py``・
``tests/c7/test_prereg_v13.py``)。

例(親・サーバー)::

    python tools/c7/holdout_compare.py --open-seal \\
        --occupancy docs/bench/c7/c7_occupancy.json \\
        --data-root data --world data/world/v2 --out docs/bench/c7 --run-id <run_id>

    # v1.3(3 seed のアンサンブル)
    python tools/c7/holdout_compare.py --open-seal --prereg-version v1.3 \\
        --occupancy docs/bench/c7/occupancy_c7-day-4.json \\
        --occupancy docs/bench/c7/occupancy_c7-day-4-s2.json \\
        --occupancy docs/bench/c7/occupancy_c7-day-4-s3.json \\
        --data-root data --world data/world/v2 --out docs/bench/c7/holdout/c7-day-4
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c7lib  # noqa: E402
import prereg_v13  # noqa: E402

AREA_IDS = c7lib.AREA_IDS
ATTR_IDS = c7lib.ATTR_IDS

#: 封印層のうち本ツールが開くもの(KDDI Location Analyzer 生 JSON)。
LAYER = "kddi_la"

#: 開封記録の既定の置き場。
DEFAULT_RECORD = "docs/bench/c7/holdout_open_record.json"

#: 事前登録の版。``v1.2``=1 ランの点判定(既定・従来どおり)/``v1.3``=seed アンサンブル判定。
PREREG_VERSIONS: tuple[str, ...] = ("v1.2", "v1.3")

#: 欄名の別名(生データの実欄名が分からないので best-effort・**expedient**)。
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "area": (r"^名称$", r"エリア", r"^area", r"^name"),
    "year": (r"^年$", r"^year", r"年度"),
    "month": (r"^月$", r"^month"),
    "hour": (r"時間帯", r"^時$", r"^hour", r"時間"),
    "sex": (r"性別", r"^sex"),
    "attr": (r"属性", r"渋谷との関係", r"^attr", r"関係"),
    "value": (r"人数.*合計", r"^人数$", r"^値$", r"^value$", r"合計"),
}

#: 公式表記 → area id。
AREA_NAME_TO_ID: dict[str, str] = {c7lib.AREA_JA[a]: a for a in AREA_IDS}
#: 属性の表記 → attr id。
ATTR_NAME_TO_ID: dict[str, str] = {c7lib.ATTR_JA[a]: a for a in ATTR_IDS}

DEFAULT_FIELD_MAP: dict[str, Any] = {
    "hour_table": "taizai_seibetu",
    "attr_table": "taizai_zokuseibetu",
    "year": None,          # None = 全年を使わず「最新年」を自動選択
    "fields": {},          # 明示指定(空なら FIELD_ALIASES で解決)
    "area_names": AREA_NAME_TO_ID,
    "attr_names": ATTR_NAME_TO_ID,
}


# ---------------------------------------------------------------- 封印


class SealError(RuntimeError):
    """封印規律に反する操作(未指定の開封・二度目の開封・sha256 不一致)。"""


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def load_seal(world_dir: str | Path, layer: str = LAYER) -> dict[str, Any]:
    """``w19_freeze.json`` の封印から 1 層を取り出す(**中身は開かない**)。"""
    doc = json.loads((Path(world_dir) / "w19_freeze.json").read_text(encoding="utf-8"))
    for lyr in doc["holdout_seal"]["layers"]:
        if lyr["name"] == layer:
            return lyr
    raise SealError(f"封印層 {layer} が w19_freeze.json に無い")


def check_seal(data_root: str | Path, seal: Mapping[str, Any]) -> dict[str, Any]:
    """封印メンバーの sha256 が封印時と一致するか(**中身は読まない**・ハッシュだけ)。"""
    members = list(seal.get("member_files", []))
    if not members:
        raise SealError(f"封印層 {seal.get('name')} にメンバーが 1 件も無い(封印が壊れている)")
    rows = []
    ok = True
    for entry in members:
        p = Path(data_root) / entry["path"]
        exists = p.exists()
        actual = sha256_file(p) if exists else None
        match = bool(exists and actual == entry["sha256"])
        ok = ok and match
        rows.append({
            "path": entry["path"], "exists": exists,
            "sha256_sealed": entry["sha256"], "sha256_now": actual,
            "bytes": entry.get("bytes"), "match": match,
        })
    return {"layer": seal["name"], "member_hash": seal.get("member_hash"),
            "sealed_utc": seal.get("sealed_utc"), "files": rows, "ok": ok}


def read_open_record(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def guard_open(record_path: str | Path, *, open_seal: bool, force: bool) -> dict[str, Any] | None:
    """開封の門番。``--open-seal`` 無し / 既に開封済みで ``--force`` 無し は例外。"""
    if not open_seal:
        raise SealError(
            "holdout は封印されている。開くには --open-seal を明示すること"
            "(実装計画書 §9.1 C7『holdout照合は事後1回のみ』)。"
        )
    prev = read_open_record(record_path)
    if prev is not None and not force:
        raise SealError(
            f"既に開封記録がある({record_path}・{prev.get('opened_utc')}・"
            f"run_id={prev.get('run_id')})。事後照合は 1 回のみ。"
            "やり直すなら --force を明示し、理由を登録簿へ書くこと。"
        )
    return prev


def write_open_record(record_path: str | Path, payload: Mapping[str, Any]) -> Path:
    """開封記録を書く。**既存の記録は消さず** ``previous_openings``(古い順)に積む。

    第176(層2 指摘 A): 事前登録した腕を同一セッションで続けて照合すると 2 本目以降は ``--force`` で
    通るが、上書きすると主張腕の初回開封(forced=false)の証跡が消える。最上位は常に最新の開封・
    ``previous_openings[0]`` が初回。
    """
    p = Path(record_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc = dict(payload)
    prev = read_open_record(p)
    if prev is not None:
        hist = list(prev.get("previous_openings", []))
        hist.append({k: v for k, v in prev.items() if k != "previous_openings"})
        doc["previous_openings"] = hist
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


# ---------------------------------------------------------------- 生データの読み取り


def find_table(doc: Any, key: str) -> list[Any]:
    """入れ子のどこかにある ``key`` のテーブルを取り出す(**最初の一致**)。"""
    if isinstance(doc, Mapping):
        if key in doc and isinstance(doc[key], (list, tuple)):
            return list(doc[key])
        if key in doc and isinstance(doc[key], Mapping):
            inner = doc[key]
            for cand in ("rows", "records", "data", "values"):
                if isinstance(inner.get(cand), (list, tuple)):
                    return list(inner[cand])
        for v in doc.values():
            try:
                return find_table(v, key)
            except KeyError:
                continue
    elif isinstance(doc, (list, tuple)):
        for v in doc:
            try:
                return find_table(v, key)
            except KeyError:
                continue
    raise KeyError(key)


def resolve_fields(sample: Mapping[str, Any], want: Iterable[str],
                   explicit: Mapping[str, str] | None = None) -> dict[str, str]:
    """レコード 1 件の欄名から論理欄 → 実欄名を決める。決まらなければ例外。"""
    exp = dict(explicit or {})
    keys = list(sample.keys())
    out: dict[str, str] = {}
    for logical in want:
        if logical in exp:
            if exp[logical] not in sample:
                raise KeyError(f"--field-map が指す欄 {exp[logical]!r} が生データに無い: {keys}")
            out[logical] = exp[logical]
            continue
        for pat in FIELD_ALIASES.get(logical, ()):
            hit = [k for k in keys if re.search(pat, str(k))]
            if hit:
                out[logical] = hit[0]
                break
        else:
            raise KeyError(
                f"論理欄 {logical!r} に対応する欄が生データに無い(候補={keys})。"
                "--field-map で明示すること(推測で埋めない)。"
            )
    return out


_INT_RE = re.compile(r"-?\d+")


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, np.integer)):
        return int(value)
    m = _INT_RE.search(str(value))
    return int(m.group(0)) if m else None


def _as_float(value: Any) -> float:
    if isinstance(value, (int, float, np.number)):
        return float(value)
    s = str(value).replace(",", "")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else 0.0


def hour_bin_to_sim_hour(raw: Any) -> int | None:
    """KDDI の時間帯(5..28)→ 世界内の時(0-23)。``28時`` は翌 4 時。"""
    v = _as_int(raw)
    if v is None:
        return None
    if not (0 <= v <= 28):
        return None
    return int(v % 24)


def observed_hour_share(records: Sequence[Mapping[str, Any]], field_map: Mapping[str, Any]
                        ) -> tuple[np.ndarray, dict[str, Any]]:
    """滞在×時間帯テーブル → ``(5, 24)`` の**時刻シェア**(絶対水準は返さない)。"""
    if not records:
        raise ValueError("時間帯テーブルが空")
    fields = resolve_fields(records[0], ("area", "year", "hour", "value"),
                            field_map.get("fields"))
    names = dict(field_map.get("area_names") or AREA_NAME_TO_ID)
    years = {(_as_int(r[fields["year"]])) for r in records}
    years.discard(None)
    year = field_map.get("year") or (max(years) if years else None)

    acc = np.zeros((len(AREA_IDS), 24), dtype=np.float64)
    used = skipped = 0
    unknown_areas: set[str] = set()
    for rec in records:
        if year is not None and _as_int(rec[fields["year"]]) != int(year):
            continue
        aid = names.get(str(rec[fields["area"]]).strip())
        if aid is None:
            unknown_areas.add(str(rec[fields["area"]]).strip())
            skipped += 1
            continue
        h = hour_bin_to_sim_hour(rec[fields["hour"]])
        if h is None:
            skipped += 1
            continue
        acc[AREA_IDS.index(aid), h] += _as_float(rec[fields["value"]])
        used += 1
    if used == 0:
        raise ValueError(f"使えたレコードが 0 件(year={year}・欄={fields})")
    totals = acc.sum(axis=1, keepdims=True)
    if not (totals > 0).all():
        raise ValueError("合計が 0 のエリアがある(欄の対応が誤っている可能性)")
    meta = {"year": year, "n_used": used, "n_skipped": skipped,
            "fields": fields, "unknown_area_labels": sorted(unknown_areas)}
    return acc / totals, meta


def observed_area_share(records: Sequence[Mapping[str, Any]], field_map: Mapping[str, Any]
                        ) -> tuple[np.ndarray, dict[str, Any]]:
    """同じテーブルから ``(5,)`` の**エリア構成シェア**(1 日合計の相対量)。"""
    share, meta = _observed_area_totals(records, field_map)
    return share, meta


def _observed_area_totals(records: Sequence[Mapping[str, Any]], field_map: Mapping[str, Any]
                          ) -> tuple[np.ndarray, dict[str, Any]]:
    fields = resolve_fields(records[0], ("area", "year", "value"), field_map.get("fields"))
    names = dict(field_map.get("area_names") or AREA_NAME_TO_ID)
    years = {(_as_int(r[fields["year"]])) for r in records}
    years.discard(None)
    year = field_map.get("year") or (max(years) if years else None)
    acc = np.zeros(len(AREA_IDS), dtype=np.float64)
    used = 0
    for rec in records:
        if year is not None and _as_int(rec[fields["year"]]) != int(year):
            continue
        aid = names.get(str(rec[fields["area"]]).strip())
        if aid is None:
            continue
        acc[AREA_IDS.index(aid)] += _as_float(rec[fields["value"]])
        used += 1
    s = acc.sum()
    if s <= 0:
        raise ValueError("エリア構成の合計が 0")
    return acc / s, {"year": year, "n_used": used, "fields": fields}


def observed_attr_share(records: Sequence[Mapping[str, Any]], field_map: Mapping[str, Any]
                        ) -> tuple[np.ndarray, dict[str, Any]]:
    """属性テーブル → ``(5, 3)`` の**エリア内属性シェア**。"""
    if not records:
        raise ValueError("属性テーブルが空")
    fields = resolve_fields(records[0], ("area", "year", "attr", "value"),
                            field_map.get("fields"))
    names = dict(field_map.get("area_names") or AREA_NAME_TO_ID)
    attrs = dict(field_map.get("attr_names") or ATTR_NAME_TO_ID)
    years = {(_as_int(r[fields["year"]])) for r in records}
    years.discard(None)
    year = field_map.get("year") or (max(years) if years else None)
    acc = np.zeros((len(AREA_IDS), len(ATTR_IDS)), dtype=np.float64)
    used = 0
    unknown: set[str] = set()
    for rec in records:
        if year is not None and _as_int(rec[fields["year"]]) != int(year):
            continue
        aid = names.get(str(rec[fields["area"]]).strip())
        att = attrs.get(str(rec[fields["attr"]]).strip())
        if aid is None or att is None:
            if att is None:
                unknown.add(str(rec[fields["attr"]]).strip())
            continue
        acc[AREA_IDS.index(aid), ATTR_IDS.index(att)] += _as_float(rec[fields["value"]])
        used += 1
    tot = acc.sum(axis=1, keepdims=True)
    if not (tot > 0).all():
        raise ValueError("合計が 0 のエリアがある(属性テーブル)")
    return acc / tot, {"year": year, "n_used": used, "fields": fields,
                       "unknown_attr_labels": sorted(unknown)}


def read_holdout(path: str | Path, field_map: Mapping[str, Any] | None = None
                 ) -> dict[str, Any]:
    """封印ファイルを開いて**形状だけ**取り出す(絶対水準はここで捨てる)。"""
    fm = {**DEFAULT_FIELD_MAP, **(dict(field_map) if field_map else {})}
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    hour_rows = find_table(doc, fm["hour_table"])
    obs_share, meta_h = observed_hour_share(hour_rows, fm)
    obs_area, meta_a = observed_area_share(hour_rows, fm)
    out: dict[str, Any] = {
        "obs_hour_share": obs_share,
        "obs_area_share": obs_area,
        "meta": {"hour": meta_h, "area": meta_a, "n_hour_rows": len(hour_rows)},
    }
    try:
        attr_rows = find_table(doc, fm["attr_table"])
        out["obs_attr_share"], out["meta"]["attr"] = observed_attr_share(attr_rows, fm)
        out["meta"]["n_attr_rows"] = len(attr_rows)
    except (KeyError, ValueError) as exc:
        out["obs_attr_share"] = None
        out["meta"]["attr_error"] = f"{type(exc).__name__}: {exc}"
    return out


# ---------------------------------------------------------------- ラン側


def sim_from_occupancy(doc: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray | None]:
    """``c7_occupancy.json`` → ``(24, 5)`` 在圏数と ``(5, 3)`` 属性数。"""
    tbl = np.asarray(doc["area_hour_counts"], dtype=np.float64)
    if tbl.shape != (24, len(AREA_IDS)):
        raise ValueError(f"area_hour_counts の形が違う: {tbl.shape}")
    attr = doc.get("area_attr_counts")
    return tbl, (np.asarray(attr, dtype=np.float64) if attr is not None else None)


# ---------------------------------------------------------------- 報告


def compare(sim_table: np.ndarray, holdout: Mapping[str, Any],
            sim_attr: np.ndarray | None = None,
            prereg: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """5 指標を計算する(**純関数**・テストの入口)。"""
    return c7lib.five_metrics(
        sim_table,
        holdout["obs_hour_share"],
        sim_attr=sim_attr,
        obs_attr=holdout.get("obs_attr_share"),
        obs_area_share=holdout.get("obs_area_share"),
        prereg=prereg,
    )


def report(res: Mapping[str, Any], seal: Mapping[str, Any], meta: Mapping[str, Any],
           v13_section: str | None = None) -> str:
    """照合の Markdown。``v13_section`` は ``--prereg-version v1.3`` のときだけ末尾に足す
    (既定 None = v1.2 の出力は 1 バイトも変わらない)。"""
    lines = [
        "# C7 holdout 照合(KDDI 形状5指標・**事後1回のみ**)",
        "",
        f"- 封印層: `{seal['layer']}` / member_hash `{str(seal.get('member_hash'))[:16]}…`"
        f" / 封印時刻 {seal.get('sealed_utc')} / sha256 一致 "
        f"{'OK' if seal.get('ok') else '**NG**'}",
        f"- holdout 年: {meta.get('hour', {}).get('year')} / 使用レコード "
        f"{meta.get('hour', {}).get('n_used')}(時間帯表 {meta.get('n_hour_rows')} 行)",
        "- 出力は**シェア・順位・比のみ**(D1′「値は形状と比のみ」)。",
        "",
        c7lib.metrics_markdown(res),
        "",
        f"総合: {res['n_pass']}/{res['n_measured']} 合格 → "
        f"**{'PASS' if res['pass'] else 'FAIL'}**",
    ]
    if v13_section:
        lines += ["", v13_section]
    return "\n".join(lines)


def validate_prereg_version(prereg_version: str, occupancy_paths: Sequence[str]) -> str:
    """版と ``--occupancy`` の本数の整合。**ファイルには一切触らない**(封印の前に呼ぶ)。

    - ``v1.3`` は seed アンサンブル判定なので ``--occupancy`` が **2 本以上**必要。
    - ``v1.2`` は 1 ランの点判定なので **1 本だけ**(複数渡すなら版を上げる)。
    """
    if prereg_version not in PREREG_VERSIONS:
        raise ValueError(f"--prereg-version は {PREREG_VERSIONS} のどれか: {prereg_version!r}")
    n = len(list(occupancy_paths))
    if n == 0:
        raise ValueError("--occupancy が 1 本も無い")
    if prereg_version == "v1.3" and n < 2:
        raise ValueError(
            "--prereg-version v1.3 は seed アンサンブル判定なので --occupancy が 2 本以上必要"
            f"(渡されたのは {n} 本)。1 本で照合するなら --prereg-version v1.2"
            "(事前登録 v1.3 §7)。")
    if prereg_version == "v1.2" and n > 1:
        raise ValueError(
            f"--prereg-version v1.2 は 1 ランの点判定なので --occupancy は 1 本"
            f"(渡されたのは {n} 本)。複数 seed を照合するなら --prereg-version v1.3。")
    return prereg_version


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="C7: 封印された KDDI holdout を 1 回だけ開いて形状5指標を照合する")
    ap.add_argument("--open-seal", action="store_true",
                    help="**明示**しないと holdout を 1 バイトも読まない")
    ap.add_argument("--force", action="store_true", help="開封記録があっても開く(理由を登録簿へ)")
    ap.add_argument("--data-root", default="data", help="data 根(封印パスの起点)")
    ap.add_argument("--world", default="data/world/v2", help="w19_freeze.json のある場所")
    ap.add_argument("--occupancy", action="append", required=True, metavar="JSON",
                    help="occupancy_series.py が出した JSON。v1.3 は seed の本数だけ並べる")
    ap.add_argument("--prereg-version", choices=PREREG_VERSIONS, default="v1.2",
                    help="事前登録の版(既定 v1.2=1 ランの点判定・v1.3=seed アンサンブル判定)")
    ap.add_argument("--field-map", default=None, help="生データの欄名対応 JSON")
    ap.add_argument("--prereg", default=None, help="事前登録の合格線 JSON(既定 PREREG_V0)")
    ap.add_argument("--record", default=DEFAULT_RECORD, help="開封記録の置き場")
    ap.add_argument("--manifest", default=None, help="ラン manifest JSON(開封記録の書き込み先)")
    ap.add_argument("--write-manifest", action="store_true",
                    help="manifest に holdout_open 欄を実際に足す(既定は断片を印字するだけ)")
    ap.add_argument("--run-id", default="", help="照合したランの run_id")
    ap.add_argument("--out", default="docs/bench/c7", help="出力ディレクトリ")
    args = ap.parse_args(argv)

    # 版と本数の整合は**封印に触る前**に見る(ここは一切 IO をしない=開封の門番より先で安全)。
    occ_paths = list(args.occupancy)
    try:
        validate_prereg_version(args.prereg_version, occ_paths)
    except ValueError as exc:
        ap.error(str(exc))

    guard_open(args.record, open_seal=args.open_seal, force=args.force)

    seal_layer = load_seal(args.world)
    seal = check_seal(args.data_root, seal_layer)
    if not seal["ok"]:
        raise SealError(
            "封印メンバーの sha256 が封印時と一致しない(取り違え/差し替え)。"
            f"詳細: {json.dumps(seal['files'], ensure_ascii=False)}"
        )

    field_map = json.loads(Path(args.field_map).read_text(encoding="utf-8")) if args.field_map else None
    prereg = json.loads(Path(args.prereg).read_text(encoding="utf-8")) if args.prereg else None

    target = Path(args.data_root) / seal_layer["member_files"][0]["path"]
    holdout = read_holdout(target, field_map)

    per_seed: list[dict[str, Any]] = []
    per_seed_h1_day: list[dict[str, Any]] = []
    sim_shares: list[np.ndarray] = []
    occ_files: list[dict[str, Any]] = []
    for path in occ_paths:
        occ = json.loads(Path(path).read_text(encoding="utf-8"))
        sim_table, sim_attr = sim_from_occupancy(occ)
        per_seed.append(compare(sim_table, holdout, sim_attr, prereg))
        occ_files.append({"path": path, "sha256": sha256_file(path)})
        if args.prereg_version == "v1.3":
            per_seed_h1_day.append(prereg_v13.h1_day_window(
                sim_table, holdout["obs_hour_share"], prereg=prereg))
            sim_shares.append(c7lib.hour_share(sim_table))
    res = per_seed[0]   # v1.2 の表は 1 本目(主張腕)のまま出す

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "shibuya.tools.c7/holdout_compare/1",
        "seal": seal,
        "holdout_meta": holdout["meta"],
        "occupancy": occ_paths[0],
        "run_id": args.run_id,
        "metrics": {k: res[k] for k in ("H1", "H2", "H3", "H4", "H5")},
        "prereg": res["prereg"],
        "n_measured": res["n_measured"],
        "n_pass": res["n_pass"],
        "pass": res["pass"],
    }
    v13_md: str | None = None
    v13: dict[str, Any] | None = None
    if args.prereg_version == "v1.3":
        v13 = prereg_v13.ensemble_verdict(
            per_seed, prereg=res["prereg"], per_seed_h1_day=per_seed_h1_day, labels=occ_paths)
        envelope = prereg_v13.get_envelope(sim_shares, holdout["obs_hour_share"])
        crps = prereg_v13.fair_crps_table(sim_shares, holdout["obs_hour_share"])
        v13_md = prereg_v13.report_v13(v13, envelope, crps, labels=occ_paths)
        payload["prereg_version"] = args.prereg_version
        payload["occupancy_seeds"] = occ_paths
        payload["per_seed_metrics"] = [
            {k: r[k] for k in ("H1", "H2", "H3", "H4", "H5")} for r in per_seed]
        payload["v13"] = {"verdict": v13, "envelope": envelope, "fair_crps": crps}
        payload = prereg_v13.apply_ensemble_verdict(payload, v13)  # 受入表(c7_accept)が読むトップレベルを v1.3 に(第216)
    (out_dir / "c7_holdout_compare.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    md = report(res, seal, holdout["meta"], v13_md)
    (out_dir / "c7_holdout_compare.md").write_text(md, encoding="utf-8")

    record = {
        "schema": "shibuya.tools.c7/holdout_open_record/1",
        "layer": seal["layer"],
        "opened_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "run_id": args.run_id,
        "tool": "tools/c7/holdout_compare.py",
        "member_hash": seal.get("member_hash"),
        "sealed_utc": seal.get("sealed_utc"),
        "files": [{"path": f["path"], "sha256": f["sha256_now"], "bytes": f["bytes"]}
                  for f in seal["files"]],
        "forced": bool(args.force),
        "prereg_version": args.prereg_version,
        # seed ごとの occupancy パス+sha256(どのランを照合したかを開封記録だけで追える)。
        "occupancy_files": occ_files,
        "result": {"n_pass": payload["n_pass"], "n_measured": payload["n_measured"], "pass": payload["pass"],
                   "source": payload.get("verdict_source", "v1.2 point")},
    }
    if v13 is not None:
        record["result_v13"] = {
            "n_pass": v13["n_pass"], "n_measured": v13["n_measured"],
            "n_undecided": v13["n_undecided"], "n_fail": v13["n_fail"], "pass": v13["pass"],
        }
    write_open_record(args.record, record)

    if args.manifest:
        mp = Path(args.manifest)
        if args.write_manifest:
            doc = json.loads(mp.read_text(encoding="utf-8"))
            doc["holdout_open"] = record
            mp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"[manifest] {mp} に holdout_open を書いた")
        else:
            print("[manifest] 次の断片を manifest へ足すこと(--write-manifest で自動):")
            print(json.dumps({"holdout_open": record}, ensure_ascii=False, indent=1))

    print(md)
    if v13 is not None:
        # v1.3 はアンサンブルの判定が総合(undecided は合格にしない)。
        return 0 if v13["pass"] else 1
    return 0 if res["pass"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
