# -*- coding: utf-8 -*-
"""warmup_gauge — 第 3 期 3-3b **CP5-6 慣らしの自動判定の器**(MSER を「差の系列」に当てる・読むだけ・記録に JSON)。

正典
    決定 10-12 §4-5 CP5-6(問い 1=慣らしは速い指標と遅い指標の両方に自動判定・日数は結果として記録・未収束なら報告・最低 1 週間は
    未リサーチ/問い 2=構え・切り替わり・新しい日常の 3 区間を事前登録・③の始まりは「改変あり」と「改変なし」の差に判定をかけて
    見つける)・PENDING 仮-24(親の判断)・答申 R-117 §4-1〜§4-7(MSER と MSER-5・Hoad & Robinson 2011 の作法・§4-6 の推奨の手順)。
    規則と parameter は ``shibuya.engine.experiment.warmup.RULE``(エンジンが manifest の ``experiment.warmup`` と事前登録の記録に
    写す=登録するのは日付ではなく規則)。この道具はその規則で判定する(規則を道具の中に重ねて持たない)。

MSER(式は White 1997・Franklin & White 2008・Hoad & Robinson 2011 の定義=R-117 §4-1)
    出力の列 y_1…y_n を打ち切り点 d で分け、MSER(n, d) = Σ_{i=d+1}^{n}(y_i − Ȳ(n, d))² / (n − d)²。d* = argmin(同点は小さい d)。
    MSER-5 は 5 個ずつの平均に当てる形。v2 は **1 バッチ=1 シム日**(日のまとめが 5 個まとめの役=R-117 §4-6 段 2)。
    参考の実装 pymser(BSD-3-Clause・``calculate_MSEm``)は**写していない**(依存も増やさない)。候補の範囲・小さい値の置き換え・
    75% の警告が Hoad の作法と違うため(R-117 §4-4)、式だけを原典から書いた(未照合=pymser と同じ入力での値の照合はしていない)。

作法(``RULE``)
    - 候補は d ≤ n − 5(最後の 5 バッチは候補にしない)。
    - d* > n/2 は無効=10% 延ばす(切り上げ・最低 1 日)。延ばす先のデータが無ければ「要延長」(ランを延ばす)。3 回無効なら「未収束」。
    - 複数本は本ごとの差を日ごとに平均してから当てる(問い 1 は 5 本以上・問い 2 は 6 対以上=足りなければ「本数不足」の印)。
    - 指標ごとに当て、慣らしの日数=系列の頭の日から数えた日数(最初の日 + d* − 頭の日・〔検収 L3〕在庫と累計は流量に直すと最初の
      日が落ちるので d* + 1)。W=有効だった指標の慣らしの日数の最大。測る期間は W 以上(全体で 2W 以上)。
    - 累積の系列は使わない(``kind: cumulative`` は拒む)。ランの頭からの累計(md23 の probe の ``conv.opened`` など=
      ``CUMULATIVE_PATHS``)は**累計の印**(``kind: counter``)を付けて日ごとの差(その日の数)に直す。印の無い累計の道筋は拒む
      (〔検収 M1〕宣言の ``kind`` だけを見て黙って通さない)。最初の記録の日は落とす(累計は再開で引き継ぐ=状態台帳 O91)。
      在庫(``kind: stock``)は流量に直す(新しく知った数・忘れた数=計器の側の欄。
      その欄がまだ無い間は日ごとの差=純流量で代える=expedient)。月の周期の指標(``speed: transition``)は慣らしの対象から外し
      「推移の指標」として系列だけ報告する。
    - 本則=差の系列(問い 1=開始日から始めたラン A − k 日前から始めて慣れたラン B の共通の日付の差・問い 2=改変の枝 − A/A の枝)。
      感度の腕=原系列(問い 1 は A の平均・問い 2 は改変の枝の平均)に同じ規則を当てて並べる(原系列は暦と天気で動き続ける=定常に
      達しないと宣言)。

指標の表(``METRICS``=計器の側。CA8 の一覧に流量の欄を足した=置き場の欄は値が null)
    速い=外出(到着の数)・訪問(店で払った行)・食事(置き場)・会話の始まり(累計 → 日ごとの差)・呼数 / 遅い=新しく結んだ約束(置き場)・グループ(置き場)・
    知り合いの数(在庫 → 流量)・新しく知った数と忘れた数(置き場=計器の側に足す欄)・関係の辺(在庫 → 流量)/ 推移=給料・所持金の
    合計(月の周期)。道筋は 2-3 の複数日の mock の道具(``md23/tools/multiday_md23.py``)のランの記録の形
    (``daily``・``probe``・``gauge`` の日ごとの行=``<列の名>.<行の中の道筋>``)。

入力(ランの日次の記録=md23 の 1 本の JSON)
    問い 1: ``{"pairs": [{"a": <開始日から始めたランの記録の道筋>, "b": <k 日前から始めたランの記録の道筋>, "lead_days": k}, …]}``
    (A の日 i と B の日 i + k が同じ日付)。問い 2: ``{"pairs": [{"branch": <道筋>, "aa": <道筋>}, …], "exec_day": 日,
    "notice_day": 日 or null, "end_day": 日 or null}``(同じ基準のランから出した対・日の番号は共通)。道筋は入力の JSON からの相対。

使い方(リポの根で・作業木の src)::

    python tools/instruments/warmup_gauge.py q1 --input <作業用>/q1_pairs.json --out <…>/warmup_q1.json
    python tools/instruments/warmup_gauge.py q2 --input <作業用>/q2_pairs.json --out <…>/warmup_q2.json

読む守り: 入力の道筋に封印と検証側の語(``read_guard.GAUGE_DENY_TOKENS``)があれば開く前に落とす(〔検収 M2〕照らすのは
``read_guard.deny_hit``=小文字にそろえた生の道筋と、当たらなければ実体の道筋=つなぎ・symlink を解いた形)。

〔検収 L8〕指標の表 ``METRICS`` は読み取り専用(行は ``MappingProxyType``・列は tuple)。

逐次ループ宣言: 指標 × 打ち切り点の候補(日の数=数十)× 延長の回数(3)・対の数ぶんの読み。体の数に比例するループは無い。
絶対パスは出力に書かない。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

HERE = Path(os.path.abspath(__file__)).parent
REPO = HERE.parent.parent
if str(REPO / "src") not in sys.path:  # pragma: no cover - 実行時の経路(規則はエンジンの側の 1 か所)
    sys.path.insert(0, str(REPO / "src"))

from shibuya.engine.experiment.warmup import RULE, rule_record, rule_sha256  # noqa: E402

SCHEMA = "shibuya.tools.instruments/warmup_gauge/1"
#: 判定の状態。
VALID, NEEDS_MORE, UNCONVERGED, TOO_SHORT, PLACEHOLDER, TRANSITION, NO_DATA = (
    "有効", "要延長", "未収束", "短すぎる", "置き場", "推移の指標", "データ無し")
PLACEHOLDER_NOTE = "置き場(計る口がまだ無い=計器の側に欄を足す)"

#: ランの記録(md23 の道具の形)のうち、ランの頭からの累計の道筋(``ConversationManager.n_opened`` など=足すだけで戻さない・
#: 再開で引き継ぐ=状態台帳 O91)。この道筋は累計の印(``kind: counter``)が無ければ拒む(〔検収 M1〕)。
CUMULATIVE_PATHS: frozenset[str] = frozenset({"probe.conv.opened", "probe.conv.closed", "probe.conv.joined"})


def _frozen_row(row: Mapping[str, Any]) -> Mapping[str, Any]:
    """指標の表の 1 行を読み取り専用に(列は tuple)。"""
    return MappingProxyType({k: (tuple(v) if isinstance(v, list) else v) for k, v in row.items()})


#: 指標の表(計器の側・CA8 の一覧に流量の欄を足した)。path=None は置き場。読み取り専用(〔検収 L8〕)。
METRICS: tuple[Mapping[str, Any], ...] = tuple(_frozen_row(r) for r in (
    {"id": "outings", "speed": "fast", "kind": "flow", "path": "gauge.arrivals_n",
     "note": "到着の数(外出の回数の代わり=expedient)"},
    {"id": "visits", "speed": "fast", "kind": "flow", "path": "daily.stage2.payment.cash_rows",
     "note": "店で払った行の数(訪問の回数の代わり=expedient)"},
    {"id": "meals", "speed": "fast", "kind": "flow", "path": None, "note": "食事の回数(置き場)"},
    {"id": "conversations", "speed": "fast", "kind": "counter", "path": "probe.conv.opened",
     "note": "会話の始まりの数(md23 の probe の conv.opened=ランの頭からの累計 → 日ごとの差に直す=〔検収 M1〕)"},
    {"id": "calls", "speed": "fast", "kind": "flow", "path": "daily.llm_calls", "note": "1 日の LLM の呼数"},
    {"id": "promises_new", "speed": "slow", "kind": "flow", "path": None,
     "note": "新しく結んだ約束の数(置き場=CA8 の約束の数)"},
    {"id": "groups", "speed": "slow", "kind": "stock", "path": None, "note": "その日の終わりのグループの数(置き場)"},
    {"id": "acquaintances", "speed": "slow", "kind": "stock", "path": "probe.relations.acquaintance_edges",
     "flows": ["acquaintances_new", "acquaintances_forgotten"],
     "note": "知り合いの数(在庫)=流量に直す(総流量の欄が無い間は日ごとの差=純流量)"},
    {"id": "acquaintances_new", "speed": "slow", "kind": "flow", "path": None,
     "note": "新しく知った数(CA8 の一覧に足す欄=計器の側・置き場)"},
    {"id": "acquaintances_forgotten", "speed": "slow", "kind": "flow", "path": None,
     "note": "忘れた数(CA8 の一覧に足す欄=計器の側・置き場)"},
    {"id": "edges_live", "speed": "slow", "kind": "stock", "path": "probe.relations.edges_live",
     "note": "生きている関係の辺の数(在庫)=流量に直す"},
    {"id": "wages", "speed": "transition", "kind": "flow", "path": "daily.stage2.wages.amount",
     "note": "給料の額(月の周期=慣らしの対象の外・推移の指標)"},
    {"id": "cash_total", "speed": "transition", "kind": "stock", "path": "probe.money.cash_total",
     "note": "所持金の合計(月の周期=推移の指標)"},
))
SPEEDS = ("fast", "slow", "transition")
#: 指標の種類。flow=その日の数・stock=在庫(流量に直す)・counter=ランの頭からの累計(日ごとの差に直す)・cumulative=累積の
#: 系列(累積の平均など=拒む)。
KINDS = ("flow", "stock", "counter", "cumulative")


def _read_guard() -> Any:
    name = "read_guard_warmup"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / "read_guard.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def check_path(path: str | Path) -> None:
    """入力の道筋に封印と検証側の語があれば開く前に落とす(``read_guard.deny_hit``=小文字にそろえて照らし、当たらなければ
    実体の道筋(つなぎ・symlink を解いた形)でも照らす=〔検収 M2〕)。"""
    hit = _read_guard().deny_hit(path)
    if hit:
        raise PermissionError(f"慣らしの計器は封印と検証側を読まない(道筋に {hit!r})")


# ================================================================ MSER(式は原典から・R-117 §4-1)
def mser_curve(y: Sequence[float]) -> list[float]:
    """d = 0 … n − 1 の MSER(n, d) = Σ_{i>d}(y_i − Ȳ(n,d))² / (n − d)²。"""
    vals = [float(v) for v in y]
    n = len(vals)
    out = []
    for d in range(n):  # 逐次ループ宣言: 打ち切り点の候補の数ぶん(日の数)
        tail = vals[d:]
        m = sum(tail) / len(tail)
        ss = sum((v - m) ** 2 for v in tail)
        out.append(ss / float(len(tail)) ** 2)
    return out


def mser_point(y: Sequence[float], *, exclude_last: int | None = None) -> dict[str, Any]:
    """打ち切り点 d*(候補は d ≤ n − ``exclude_last``=最後の数バッチを候補にしない)。候補が無ければ ``d_star=None``。"""
    k = int(RULE["exclude_last_batches"] if exclude_last is None else exclude_last)
    n = len(y)
    last = n - k
    if last < 0:
        return {"n": n, "d_star": None, "candidates": 0, "curve": []}
    curve = mser_curve(y)[: last + 1]
    best = min(range(len(curve)), key=lambda d: (curve[d], d))
    return {"n": n, "d_star": int(best), "candidates": len(curve), "curve": [round(c, 12) for c in curve]}


def mser_rule(y: Sequence[float], *, n0: int | None = None) -> dict[str, Any]:
    """MSER の作法(``RULE``): 初めの長さ ``n0``(既定=全部)で当て、d* > n/2 なら 10% 延ばして当て直す。

    延ばす先のデータが無ければ「要延長」(必要な長さ ``need_n``)。``max_invalid`` 回無効なら「未収束」。"""
    vals = [float(v) for v in y]
    n = len(vals) if n0 is None else min(int(n0), len(vals))
    attempts: list[dict[str, Any]] = []
    frac = float(RULE["invalid_if_d_over_n"])
    while True:  # 逐次ループ宣言: 延長の回数(最大 RULE["max_invalid"]=3)
        pt = mser_point(vals[:n])
        if pt["d_star"] is None:
            return {"status": TOO_SHORT, "d_star": None, "n": n, "attempts": attempts,
                    "note": f"候補が無い(n − {RULE['exclude_last_batches']} < 0)"}
        ok = pt["d_star"] <= frac * n
        attempts.append({"n": n, "d_star": pt["d_star"], "valid": ok})
        if ok:
            return {"status": VALID, "d_star": pt["d_star"], "n": n, "attempts": attempts, "note": ""}
        if len(attempts) >= int(RULE["max_invalid"]):
            return {"status": UNCONVERGED, "d_star": pt["d_star"], "n": n, "attempts": attempts,
                    "note": f"{RULE['max_invalid']} 回無効=未収束(報告する)"}
        grow = max(int(RULE["extend_min_batches"]), math.ceil(float(RULE["extend_fraction"]) * n))
        if n + grow > len(vals):
            return {"status": NEEDS_MORE, "d_star": pt["d_star"], "n": n, "attempts": attempts,
                    "need_n": n + grow, "note": f"d* > n/2 で無効=ランを {n + grow} 日まで延ばす"}
        n += grow


# ================================================================ 系列の作り方
def get_path(doc: Any, path: str) -> Any:
    cur = doc
    for part in path.split("."):
        if isinstance(cur, Mapping) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(path)
    return cur


def day_series(run: Mapping[str, Any], path: str) -> dict[int, float]:
    """md23 のランの記録 → 日の番号 → 値(``<列の名>.<行の中の道筋>``・値の無い日は飛ばす)。"""
    head, _, rest = path.partition(".")
    rows = run.get(head)
    if not isinstance(rows, list):
        return {}  # ランの記録にその列が無い=データ無し
    out: dict[int, float] = {}
    for r in rows:  # 逐次ループ宣言: 日の数ぶん
        try:
            v = get_path(r, rest)
        except KeyError:
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            continue
        out[int(r["day"])] = float(v)
    return out


def to_flow(series: Mapping[int, float]) -> dict[int, float]:
    """在庫 → 流量(総流量の欄が無い間の代わり=日ごとの差=純流量・expedient)・累計 → その日の数(〔検収 M1〕)。
    最初の日は前の日が無いので落ちる。"""
    days = sorted(series)
    return {d: series[d] - series[p] for p, d in zip(days, days[1:]) if d == p + 1}


def check_metric(metric: Mapping[str, Any]) -> None:
    """指標の種類の検査: 知らない種類・累積の系列(``kind: cumulative``)・累計の印の無い累計の道筋(``CUMULATIVE_PATHS``)は拒む。"""
    kind = metric.get("kind", "flow")
    if kind not in KINDS:
        raise ValueError(f"指標 {metric.get('id')} の kind は {KINDS}")
    if kind == "cumulative":
        raise ValueError(f"指標 {metric.get('id')}: 累積の系列は使わない(Hoad & Robinson 2011=打ち切り点が終わりに寄る)")
    if metric.get("path") in CUMULATIVE_PATHS and kind != "counter":
        raise ValueError(f"指標 {metric.get('id')}: 道筋 {metric.get('path')} はランの頭からの累計=累計の印(kind: counter)を"
                         f"付けて日ごとの差に直す(印の無い累計は使わない=〔検収 M1〕・いま kind={kind!r})")


def _prepared(series: Mapping[int, float], metric: Mapping[str, Any], *, convert: bool = True) -> dict[int, float]:
    """種類の検査の後、在庫と累計は日ごとの差に直す(``convert=False`` は直す前の系列=系列の頭の日を知るため)。"""
    check_metric(metric)
    if convert and metric.get("kind", "flow") in ("stock", "counter"):
        return to_flow(series)
    return dict(series)


def mean_of(rows: Sequence[Mapping[int, float]]) -> tuple[list[int], list[float]]:
    """日ごとの平均(全部の本に値のある日だけ・日の昇順)。"""
    if not rows:
        return [], []
    common = sorted(set.intersection(*[set(r) for r in rows]))
    return common, [sum(r[d] for r in rows) / len(rows) for d in common]


def difference_rows(pairs: Sequence[tuple[Mapping[int, float], Mapping[int, float], int]]) -> list[dict[int, float]]:
    """(x, y, ずれ) の列 → 本ごとの差の系列 D_d = x_d − y_{d + ずれ}(x の日の番号で)。"""
    out = []
    for x, y, lead in pairs:
        out.append({d: x[d] - y[d + int(lead)] for d in x if (d + int(lead)) in y})
    return out


def _contiguous(days: Sequence[int], vals: Sequence[float], start: int | None = None) -> tuple[list[int], list[float]]:
    """``start`` 以後の連続した日の頭からの列(穴があればそこで切る)。"""
    pairs = [(d, v) for d, v in zip(days, vals) if start is None or d >= start]
    out_d, out_v = [], []
    for d, v in pairs:
        if out_d and d != out_d[-1] + 1:
            break
        out_d.append(d)
        out_v.append(v)
    return out_d, out_v


def _judge(days: list[int], vals: list[float], n0: int | None, head: int | None) -> dict[str, Any]:
    """MSER の作法で判定し、慣らしの日数(〔検収 L3〕系列の頭の日 ``head`` から数えた日数=最初の日 + d* − 頭の日)を足す。"""
    if not vals:
        return {"status": NO_DATA, "d_star": None, "n": 0, "attempts": [], "first_day": None, "head_day": head,
                "warmup_days": None, "series": [], "note": "ランの記録にこの指標の値が無い"}
    r = mser_rule(vals, n0=n0)
    r["first_day"] = days[0] if days else None
    r["head_day"] = head
    r["warmup_days"] = (None if r["d_star"] is None or head is None or not days
                        else int(days[0]) + int(r["d_star"]) - int(head))
    r["series"] = [round(v, 9) for v in vals]
    return r


def _metric_rows(metrics: Iterable[Mapping[str, Any]], build: Any, n0: int | None) -> tuple[list[dict], list[dict]]:
    rows, transition = [], []
    for m in metrics:  # 逐次ループ宣言: 指標の数ぶん
        base = {"id": m["id"], "speed": m["speed"], "kind": m.get("kind", "flow"), "path": m.get("path"),
                "note": m.get("note", "")}
        if m.get("speed") not in SPEEDS:
            raise ValueError(f"指標 {m.get('id')} の speed は {SPEEDS}")
        check_metric(m)  # 累積・印の無い累計は置き場でも拒む
        if m.get("path") is None:
            rows.append({**base, "status": PLACEHOLDER, "d_star": None, "warmup_days": None,
                         "note": PLACEHOLDER_NOTE + "・" + base["note"]})
            continue
        if m["speed"] == "transition":
            days, vals, _head = build(m, raw=True)
            transition.append({**base, "status": TRANSITION, "days": days, "series": [round(v, 9) for v in vals]})
            continue
        days, vals, head = build(m, raw=False)
        main = _judge(days, vals, n0, head)
        rdays, rvals, rhead = build(m, raw=True)
        arm = _judge(rdays, rvals, n0, rhead)
        rows.append({**base, **{k: main[k] for k in ("status", "d_star", "n", "attempts", "first_day", "head_day",
                                                      "warmup_days", "series")},
                     "need_n": main.get("need_n"),
                     "arm_raw": {k: arm.get(k) for k in ("status", "d_star", "n", "warmup_days")}})
    return rows, transition


def _bundle(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """束ね: W=有効だった指標の慣らしの日数(系列の頭の日から数えた日数=〔検収 L3〕d* そのものではない)の最大。"""
    judged = [r for r in rows if r["status"] not in (PLACEHOLDER, NO_DATA)]
    valid = [int(r["warmup_days"]) for r in judged if r["status"] == VALID and r.get("warmup_days") is not None]
    bad = sorted(r["id"] for r in judged if r["status"] != VALID)
    w = max(valid) if valid else None
    return {"W": w, "measure_from_day": w, "measure_min_days": w, "total_min_days": None if w is None else 2 * w,
            "valid": sorted(r["id"] for r in judged if r["status"] == VALID), "not_valid": bad,
            "status": ("無し" if w is None else ("一部が有効でない" if bad else "全部有効")),
            "unit": "days_from_series_head", "min_days_untested": RULE["min_days"]}


def _head(kind: str, n_pairs: int, need: int) -> dict[str, Any]:
    rec = rule_record()
    return {"schema": SCHEMA, "question": kind, "rule_sha256": rule_sha256(), "rule": rec["rule"],
            "marks": rec["marks"], "metrics_sha256": metrics_sha256(), "pairs": n_pairs, "pairs_min": need,
            "pairs_enough": n_pairs >= need,
            "declaration": ("差の系列に MSER を当てる形=expedient(先例なし・R-117 §6-2)。原系列の腕は暦と天気で動き続ける"
                            "(定常に達しない)ことを宣言して並べる")}


def _plain(v: Any) -> Any:
    if isinstance(v, Mapping):
        return {str(k): _plain(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    return v


def metrics_sha256(metrics: Sequence[Mapping[str, Any]] = METRICS) -> str:
    body = json.dumps(_plain(list(metrics)), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


# ================================================================ 問い 1・問い 2
def question1(pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any], int]], *,
              metrics: Sequence[Mapping[str, Any]] = METRICS, n0: int | None = None) -> dict[str, Any]:
    """問い 1(基準のランの慣らしの日数): (A=開始日から, B=k 日前から, k) の列。差の系列 A − B を日ごとに平均して当てる。"""

    def build(m: Mapping[str, Any], *, raw: bool) -> tuple[list[int], list[float], int | None]:
        def series(convert: bool) -> tuple[list[int], list[float]]:
            sa = [_prepared(day_series(a, m["path"]), m, convert=convert) for a, _b, _k in pairs]
            if raw:  # 感度の腕=原系列(A の平均)
                return _contiguous(*mean_of(sa))
            sb = [_prepared(day_series(b, m["path"]), m, convert=convert) for _a, b, _k in pairs]
            return _contiguous(*mean_of(difference_rows([(x, y, k) for x, y, (_a, _b, k) in zip(sa, sb, pairs)])))

        d, v = series(True)
        hd, _hv = series(False)  # 系列の頭の日=直す前の系列の最初の日(〔検収 L3〕)
        return d, v, (hd[0] if hd else None)

    rows, transition = _metric_rows(metrics, build, n0)
    out = _head("q1", len(pairs), int(RULE["q1"]["pairs_min"]))
    out.update(metrics=rows, transition=transition, bundle=_bundle(rows),
               lead_days=sorted({int(k) for _a, _b, k in pairs}))
    return out


def question2(pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]], *, exec_day: int,
              notice_day: int | None = None, end_day: int | None = None,
              metrics: Sequence[Mapping[str, Any]] = METRICS, n0: int | None = None) -> dict[str, Any]:
    """問い 2(3 区間): (改変の枝, A/A の枝) の列。実行の日から先の差の系列(改変 − A/A)の日ごとの平均に同じ規則を当て、
    実行の日から数えた慣らしの日数 W で新しい日常の始まり(実行の日 + W)とする(流量で実行の日から値があれば W=d*)。構えは告知の日〜実行の日(申込書の欄で決まる=判定は要らない)。"""

    def build(m: Mapping[str, Any], *, raw: bool) -> tuple[list[int], list[float], int | None]:
        sbr = [_prepared(day_series(b, m["path"]), m) for b, _a in pairs]
        if raw:  # 感度の腕=原系列(改変の枝の平均)
            d, v = mean_of(sbr)
        else:
            saa = [_prepared(day_series(a, m["path"]), m) for _b, a in pairs]
            d, v = mean_of(difference_rows([(x, y, 0) for x, y in zip(sbr, saa)]))
        if end_day is not None:
            keep = [(x, y) for x, y in zip(d, v) if x <= int(end_day)]
            d, v = [x for x, _y in keep], [y for _x, y in keep]
        dd, vv = _contiguous(d, v, start=int(exec_day))
        return dd, vv, int(exec_day)  # 系列の頭の日=実行の日(切り替わりの区間は実行の日から数える)

    rows, transition = _metric_rows(metrics, build, n0)
    out = _head("q2", len(pairs), int(RULE["q2"]["pairs_min"]))
    bundle = _bundle(rows)
    w = bundle["W"]
    nn = None if w is None else int(exec_day) + int(w)
    out.update(metrics=rows, transition=transition, bundle=bundle, intervals={
        "prepare": None if notice_day is None else [int(notice_day), int(exec_day)],
        "switch": None if nn is None else [int(exec_day), nn],
        "new_normal": None if nn is None else [nn, end_day],
        "rule": dict(RULE["q2"]["bounds"])})
    return out


# ================================================================ CLI
def _load(path: Path) -> Any:
    check_path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _metrics_arg(args: argparse.Namespace) -> Sequence[Mapping[str, Any]]:
    return METRICS if not args.metrics else _load(Path(args.metrics))


def cmd_q1(args: argparse.Namespace) -> int:
    spec = _load(Path(args.input))
    root = Path(args.input).parent
    pairs = [(_load(root / p["a"]), _load(root / p["b"]), int(p["lead_days"])) for p in spec["pairs"]]
    out = question1(pairs, n0=args.n0, metrics=_metrics_arg(args))
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"[warmup q1] W={out['bundle']['W']} {out['bundle']['status']} pairs={out['pairs']}")
    return 0


def cmd_q2(args: argparse.Namespace) -> int:
    spec = _load(Path(args.input))
    root = Path(args.input).parent
    pairs = [(_load(root / p["branch"]), _load(root / p["aa"])) for p in spec["pairs"]]
    out = question2(pairs, exec_day=int(spec["exec_day"]), notice_day=spec.get("notice_day"),
                    end_day=spec.get("end_day"), n0=args.n0, metrics=_metrics_arg(args))
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"[warmup q2] W={out['bundle']['W']} {out['bundle']['status']} pairs={out['pairs']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn in (("q1", cmd_q1), ("q2", cmd_q2)):
        sp = sub.add_parser(name)
        sp.add_argument("--input", required=True)
        sp.add_argument("--out", required=True)
        sp.add_argument("--n0", type=int, default=None, help="初めの長さ(日・既定=全部=延ばす余地なし)")
        sp.add_argument("--metrics", default="", help="指標の表の JSON(既定=METRICS=計器の側の表)")
        sp.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
