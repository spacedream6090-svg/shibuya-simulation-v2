#!/usr/bin/env python3
"""第333: ODPT オープン枠の静的データ(時刻表・駅・路線・バス停と系統・乗降人員・運賃)の版の保存。

ユーザー決定(回答 10-13b §5 の 2): 静的データは毎日は取らない。**ダイヤ改正ごとに版を 1 回取って
残す**(古い版は API から消えるため)。対象は渋谷に限らずオープン枠全体を広めに。チャレンジ枠の
静的データは取らない(今の `data/odpt/challenge/` のまま・限定ライセンス 第 4 条 1 項)。

  --source odpt_static            版を 1 回取る(`odpt_static/<取得日>/<datatype>_<operator>.json.gz`)
  --source odpt_static --check    保存済みの最新版と API の `dct:issued` の最大を比べ、新しい版がある
                                  operator × 種類だけを一覧にする(保存はしない)
  survey()                        operator × 種類の件数・バイト・日付の範囲の表(記録の §A 用)

ODPT の検索の口は 1 回の応答が **1,000 件で打ち切られる**(2026-10-12・10-13 実測)。打ち切りに
当たった operator × 種類は、路線 → 曜日(calendar)→ 方向の順に問い合わせを分けて取り直す
(`SPLIT_KEYS`)。分けても 1,000 件に当たった区画は `_meta.capped_parts` に残す(黙って欠かさない)。
ダンプの口(`<種類>.json`)は 2026-10-13 に別ドメイン(blob)への転送を返したので使わない
(取得してよいドメインの外=転送を追わない)。

APIキーは環境変数 `ODPT_API_KEY` からだけ読み、値は出力しない(`common.resolve_key` → `scrub`)。
"""
from __future__ import annotations

import gzip
import json
from datetime import datetime
from pathlib import Path

from . import common, ledger, odpt_rt

SOURCE = "odpt_static"
OPEN_KEY_ENV = odpt_rt.OPEN_KEY_ENV
API_CAP = 1000          # 検索の口の 1 応答の上限(実測)。これに当たった応答は欠けている可能性がある

# 航空会社(フライトの情報だけ。鉄道・バスの種類を持たない)。Airport 系は対象外(親の指示)。
AIRLINE_OPERATORS = frozenset({
    "odpt.Operator:ADO", "odpt.Operator:AJX", "odpt.Operator:ANA", "odpt.Operator:IBX",
    "odpt.Operator:JAL", "odpt.Operator:JTA", "odpt.Operator:ORC", "odpt.Operator:RAC",
    "odpt.Operator:SFJ", "odpt.Operator:SNJ", "odpt.Operator:TZP",
})

RT_TYPES = ("odpt:TrainInformation", "odpt:Train", "odpt:Bus")
STATIC_TYPES = (
    "odpt:Railway", "odpt:Station", "odpt:StationTimetable", "odpt:TrainTimetable",
    "odpt:TrainType", "odpt:RailDirection", "odpt:Calendar",
    "odpt:BusroutePattern", "odpt:BusstopPole", "odpt:BusTimetable",
    "odpt:PassengerSurvey", "odpt:RailwayFare", "odpt:BusroutePatternFare",
)
# 洗い出しだけに入れる種類(版の取得には入れない=親の判断待ち)。
# BusstopPoleTimetable は BusTimetable を標柱ごとに並べ替えた形で、量が大きい。
SURVEY_EXTRA_TYPES = ("odpt:BusstopPoleTimetable",)
SURVEY_TYPES = RT_TYPES + STATIC_TYPES + SURVEY_EXTRA_TYPES

CAVEATS = [
    "オープン枠(公共交通オープンデータ基本ライセンス)。第 8 条 4 項(1): 第三者が再利用できる形での"
    "公開・再配布をしない。成果物には集計値・グラフだけを載せる。",
    "検索の口は 1 応答 1,000 件で打ち切られる。打ち切りに当たった区画は問い合わせを分けて取り直し、"
    "それでも当たった区画は _meta.capped_parts に残した。",
]


# ------------------------------------------------------------------ 小道具
is_capped = odpt_rt.is_capped


def op_short(op: str) -> str:
    """`odpt.Operator:TokyoMetro` → `TokyoMetro`(ファイル名用)。"""
    return str(op).split(":", 1)[-1] if ":" in str(op) else str(op)


def type_short(datatype: str) -> str:
    """`odpt:StationTimetable` → `stationtimetable`(ファイル名用)。"""
    return str(datatype).split(":", 1)[-1].lower()


def _str_range(values) -> tuple[str | None, str | None]:
    vals = sorted(v for v in values if isinstance(v, str) and v)
    return (vals[0], vals[-1]) if vals else (None, None)


def record_stats(records: list) -> dict:
    """件数と `dct:issued`・`dc:date`・`dct:valid` の範囲(文字列の最小・最大)。値の中身は持たない。"""
    recs = [r for r in records if isinstance(r, dict)]
    i_min, i_max = _str_range(r.get("dct:issued") for r in recs)
    d_min, d_max = _str_range(r.get("dc:date") for r in recs)
    v_min, v_max = _str_range(r.get("dct:valid") for r in recs)
    return {"n": len(records), "issued_min": i_min, "issued_max": i_max,
            "date_min": d_min, "date_max": d_max, "valid_min": v_min, "valid_max": v_max}


def _fetch(datatype: str, params: dict, key: str, *, timeout: float, retries: int,
           sleep_fn=None):
    """オープン枠の検索の口。戻り値 = (list か None, HttpResult)。転送は同じホストだけ追う。"""
    return odpt_rt._fetch("open", datatype, params, key, timeout=timeout, retries=retries,
                          sleep_fn=sleep_fn)


def list_operators(key: str, *, timeout: float = 60.0, retries: int = 1, sleep_fn=None):
    """オープン枠の `odpt:Operator` の一覧(owl:sameAs の並び)。失敗なら (None, res)。"""
    data, res = _fetch("odpt:Operator", {}, key, timeout=timeout, retries=retries,
                       sleep_fn=sleep_fn)
    if data is None:
        return None, res
    ops = sorted({str(r.get("owl:sameAs")) for r in data
                  if isinstance(r, dict) and r.get("owl:sameAs")})
    return ops, res


# ------------------------------------------------------------------ 洗い出し(§A)
def survey(root: Path, *, operators=None, types=SURVEY_TYPES, include_unfiltered: bool = True,
           timeout: float = 60.0, retries: int = 1, sleep: float = 1.0, sleep_fn=None,
           key: str | None = None, now=None, progress=None) -> tuple[dict, list[dict]]:
    """operator × 種類を 1 本ずつ問い合わせ、件数・バイト(生と gzip 後)・日付の範囲を表にする。

    保存するのは表だけ(`odpt_static/_survey_<日付>_<時刻>.json` と 1 要求 1 行の `.jsonl`)。
    データの値は保存しない。戻り値 = (表の文書, 台帳行)。
    """
    now = now or common.now_jst()
    key = key if key is not None else common.resolve_key(OPEN_KEY_ENV)
    common.register_secret(key)
    d = now.date()
    stamp = now.strftime("%H%M%S")
    base = Path(root) / SOURCE
    base.mkdir(parents=True, exist_ok=True)
    jsonl = base / f"_survey_{d.isoformat()}_{stamp}.jsonl"
    rows: list[dict] = []
    if not key:
        rows.append(ledger.make_entry(SOURCE, "survey", ok=False, date_jst=d.isoformat(),
                                      error=f"key-missing:{OPEN_KEY_ENV}"))
        return {}, rows

    if operators is None:
        ops, res = list_operators(key, timeout=timeout, retries=retries, sleep_fn=sleep_fn)
        rows.append(ledger.make_entry(SOURCE, "survey/odpt:Operator", ok=ops is not None,
                                      http_status=res.status, n_records=len(ops or []),
                                      date_jst=d.isoformat(), error=res.error))
        if ops is None:
            return {}, rows
        common.polite_sleep(sleep, sleep_fn)
        operators = [o for o in ops if o not in AIRLINE_OPERATORS]
    targets: list[str | None] = list(operators)
    if include_unfiltered:
        targets = [None] + targets

    table: list[dict] = []
    for op in targets:
        for dt in types:
            params = {} if op is None else {"odpt:operator": op}
            data, res = _fetch(dt, params, key, timeout=timeout, retries=retries,
                               sleep_fn=sleep_fn)
            body = res.body or b""
            ent = {"operator": op or "*", "datatype": dt, "http_status": res.status,
                   "error": res.error, "bytes_raw": len(body),
                   "bytes_gz": len(gzip.compress(body, compresslevel=common.GZIP_LEVEL,
                                                 mtime=0)) if body else 0,
                   "elapsed_ms": res.elapsed_ms}
            if data is not None:
                ent.update(record_stats(data))
                ent["capped"] = is_capped(len(data))
            else:
                ent.update({"n": None, "capped": None})
            table.append(ent)
            with jsonl.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(common.scrub(json.dumps(ent, ensure_ascii=False, sort_keys=True)) + "\n")
            rows.append(ledger.make_entry(
                SOURCE, f"survey/{dt}/{op or '*'}", ok=data is not None,
                http_status=res.status, n_records=len(data or []), date_jst=d.isoformat(),
                error=res.error,
                extra={"bytes_raw": ent["bytes_raw"], "bytes_gz": ent["bytes_gz"],
                       "capped": ent["capped"]}))
            if progress:
                progress(ent)
            common.polite_sleep(sleep, sleep_fn)

    doc = {
        "_meta": common.build_meta(
            SOURCE, module="odpt_static.py", urls=[odpt_rt.display_url("open", "<種類>",
                                                                        {"odpt:operator": "<op>"})],
            n_records=len(table), n_missing=sum(1 for t in table if t["n"] is None),
            caveats=CAVEATS,
            notes=["件数・バイト・日付の範囲だけの表。データの値は保存していない。",
                   f"航空会社 {len(AIRLINE_OPERATORS)} 社は対象外(フライトの情報だけ)。",
                   "operator='*' は operator で絞らない問い合わせ(1,000 件で打ち切られうる)。"],
            extra={"survey_jst": common.iso_jst(now), "types": list(types),
                   "operators": [o for o in targets if o]}),
        "data": table,
    }
    common.write_json(base / f"_survey_{d.isoformat()}_{stamp}.json", doc)
    return doc, rows


# ------------------------------------------------------------------ 打ち切りの分け方
# 打ち切りに当たったとき、問い合わせをどの欄で分けるか(前から順に。入れ子で深くする)。
# 欄の値の出どころは `_Ctx.values()`。どの欄でも分けられない区画は `capped_parts` に残す。
SPLIT_KEYS: dict[str, tuple[str, ...]] = {
    "odpt:Station": ("odpt:railway",),
    "odpt:StationTimetable": ("odpt:railway", "odpt:station", "odpt:railDirection",
                              "odpt:calendar"),
    "odpt:TrainTimetable": ("odpt:railway", "odpt:railDirection", "odpt:calendar"),
    "odpt:PassengerSurvey": ("odpt:railway", "odpt:station"),
    "odpt:RailwayFare": ("odpt:fromStation",),
    "odpt:BusroutePattern": ("owl:sameAs",),
    "odpt:BusstopPole": ("odpt:busroutePattern",),
    "odpt:BusTimetable": ("odpt:busroutePattern", "odpt:calendar"),
    "odpt:BusroutePatternFare": ("odpt:fromBusroutePattern",),
}
# 値をカンマでつないで 1 本で問い合わせられる(OR になる)と確かめた欄(2026-10-13 実測。2 値の OR の
# 件数が 1 値ずつの和と一致)。ここに無い欄は 1 値ずつ問い合わせる。
OR_KEYS: frozenset[str] = frozenset({
    "owl:sameAs", "odpt:operator", "odpt:railway", "odpt:station", "odpt:fromStation",
    "odpt:calendar", "odpt:railDirection", "odpt:busroutePattern", "odpt:fromBusroutePattern",
})
# OR でつなげる値の数の上限(2026-10-13 実測: 10 個まで受け、11 個で HTTP 400)。
OR_MAX_VALUES = 10
# つないだ値の長さの上限(文字)。URL が長すぎて断られないように(expedient)。
OR_VALUE_BUDGET = 1500
# 打ち切られた応答に出てこない曜日の値を拾うための、よく使われる曜日(expedient)。
STANDARD_CALENDARS = ("odpt.Calendar:Weekday", "odpt.Calendar:SaturdayHoliday",
                      "odpt.Calendar:Saturday", "odpt.Calendar:Holiday", "odpt.Calendar:Sunday")


def _rec_id(rec) -> str:
    if isinstance(rec, dict):
        rid = rec.get("owl:sameAs") or rec.get("@id")
        if rid:
            return str(rid)
    return common.canonical_json(rec)


def _vals(records, key) -> set[str]:
    out: set[str] = set()
    for r in records:
        if not isinstance(r, dict):
            continue
        v = r.get(key)
        if isinstance(v, str) and v:
            out.add(v)
        elif isinstance(v, list):
            out.update(x for x in v if isinstance(x, str) and x)
    return out


def _batches(values: list[str], size: int, budget: int = OR_VALUE_BUDGET) -> list[list[str]]:
    """値を、1 本あたり `size` 個(最大 `OR_MAX_VALUES`)まで・つないだ長さ `budget` 字までの束に分ける。"""
    size = max(1, min(int(size), OR_MAX_VALUES))
    out: list[list[str]] = []
    cur: list[str] = []
    cur_len = 0
    for v in values:
        add = len(v) + (1 if cur else 0)
        if cur and (len(cur) >= size or cur_len + add > budget):
            out.append(cur)
            cur, cur_len = [], 0
            add = len(v)
        cur.append(v)
        cur_len += add
    if cur:
        out.append(cur)
    return out


class _Ctx:
    """1 operator の取得の文脈: 要求の数え上げと、分け方の値の出どころ(路線・駅・系統)の控え。"""

    def __init__(self, op: str, key: str, *, timeout: float, retries: int, sleep: float,
                 sleep_fn=None, max_requests: int | None = None):
        self.op, self.key = op, key
        self.timeout, self.retries, self.sleep, self.sleep_fn = timeout, retries, sleep, sleep_fn
        self.max_requests = max_requests
        self.n_requests = 0
        self.failures: list[dict] = []
        self._cache: dict[str, list] = {}
        self._busy: set[str] = set()

    def get(self, datatype: str, params: dict):
        if self.max_requests is not None and self.n_requests >= self.max_requests:
            self.failures.append({"datatype": datatype, "error": "max-requests"})
            return None, None
        self.n_requests += 1
        data, res = _fetch(datatype, params, self.key, timeout=self.timeout,
                           retries=self.retries, sleep_fn=self.sleep_fn)
        common.polite_sleep(self.sleep, self.sleep_fn)
        if data is None:
            self.failures.append({"datatype": datatype, "http_status": res.status,
                                  "error": res.error or "failed"})
        return data, res

    def records_of(self, datatype: str) -> list:
        """この operator の `datatype` の全レコード(分けて取り直した後)。控えておく。

        取得の途中の種類(循環)には、その時点の控え(無ければ空)を返す。
        """
        if datatype in self._cache:
            return self._cache[datatype]
        if datatype in self._busy:
            return []
        self._busy.add(datatype)
        try:
            recs, _ = fetch_complete(self, datatype)
        finally:
            self._busy.discard(datatype)
        self._cache[datatype] = recs
        return recs

    def values(self, key: str, parent: dict, capped_records: list,
               datatype: str = "") -> list[str]:
        if key == "odpt:railway":
            vals = _vals(self.records_of("odpt:Railway"), "owl:sameAs")
            vals |= _vals(capped_records, "odpt:railway")
        elif key == "odpt:railDirection":
            vals = _vals(capped_records, "odpt:railDirection")
            rw = parent.get("odpt:railway")
            for r in self.records_of("odpt:Railway"):
                if isinstance(r, dict) and (rw is None or r.get("owl:sameAs") == rw):
                    vals |= _vals([r], "odpt:ascendingRailDirection")
                    vals |= _vals([r], "odpt:descendingRailDirection")
        elif key == "odpt:calendar":
            vals = _vals(capped_records, "odpt:calendar") | set(STANDARD_CALENDARS)
        elif key in ("odpt:station", "odpt:fromStation"):
            rw = parent.get("odpt:railway")
            vals = {str(s.get("owl:sameAs")) for s in self.records_of("odpt:Station")
                    if isinstance(s, dict) and s.get("owl:sameAs")
                    and (rw is None or s.get("odpt:railway") == rw)}
        elif key in ("odpt:busroutePattern", "odpt:fromBusroutePattern"):
            vals = _vals(self.records_of("odpt:BusroutePattern"), "owl:sameAs")
            vals |= _vals(capped_records, "odpt:busroutePattern")
        elif key == "owl:sameAs" and datatype == "odpt:BusroutePattern":
            # 系統パターンの一覧は、標柱が通る系統パターン(BusstopPole の odpt:busroutePattern)から拾う。
            vals = _vals(self.records_of("odpt:BusstopPole"), "odpt:busroutePattern")
            if "odpt:BusTimetable" in self._cache:
                vals |= _vals(self._cache["odpt:BusTimetable"], "odpt:busroutePattern")
        else:
            vals = set()
        return sorted(v for v in vals if v)


def fetch_complete(ctx: _Ctx, datatype: str) -> tuple[list, dict]:
    """operator の `datatype` を、打ち切りに当たったら分けて取り直して全部集める。

    分け方: `SPLIT_KEYS` の欄を前から順に使う。`OR_KEYS` の欄は値をカンマでつないだ束で問い合わせ、
    束が打ち切られたら束を半分にして取り直す。1 値でも打ち切られたら次の欄で分ける。
    `owl:sameAs` で分けるときは、まだ取れていない識別子だけを問い合わせる。
    戻り値 = (レコード(owl:sameAs で重複を除く), 取り方の情報 {n_requests, parts, capped_parts,
    failed_parts, split_keys_used})。
    """
    keys = SPLIT_KEYS.get(datatype, ())
    seen: dict[str, object] = {}
    info = {"parts": 0, "capped_parts": [], "failed_parts": 0, "split_keys_used": []}
    n0 = ctx.n_requests

    def take(data) -> None:
        info["parts"] += 1
        for rec in data:
            seen.setdefault(_rec_id(rec), rec)

    def split(params: dict, data: list, depth: int) -> None:
        """`params` の応答 `data` が打ち切られていたら、次の欄で分ける。"""
        if not is_capped(len(data)):
            return
        for k in keys[depth:]:
            if k in params:
                continue
            vals = ctx.values(k, params, data, datatype)
            if k == "owl:sameAs":
                vals = [v for v in vals if v not in seen]
            if not vals:
                continue
            if k not in info["split_keys_used"]:
                info["split_keys_used"].append(k)
            nxt = keys.index(k) + 1
            if k not in OR_KEYS:
                for v in vals:
                    p = dict(params, **{k: v})
                    d2, _ = ctx.get(datatype, p)
                    if d2 is None:
                        info["failed_parts"] += 1
                        continue
                    take(d2)
                    split(p, d2, nxt)
                return
            pending = list(vals)
            # 親の応答が打ち切られているので、全部の値を 1 束にしても打ち切られる=半分から始める。
            size = min(OR_MAX_VALUES, max(1, (len(pending) + 1) // 2))
            while pending:
                batch = _batches(pending, size)[0]
                pending = pending[len(batch):]
                p = dict(params, **{k: ",".join(batch)})
                d2, _ = ctx.get(datatype, p)
                if d2 is None:
                    info["failed_parts"] += 1
                    continue
                take(d2)
                if is_capped(len(d2)) and len(batch) > 1:
                    size = max(1, len(batch) // 2)          # 打ち切り → 束を半分にして取り直す
                    pending = batch + pending
                    continue
                if is_capped(len(d2)):
                    split(dict(params, **{k: batch[0]}), d2, nxt)
                elif len(d2) < odpt_rt.API_CAP // 3 and size < OR_MAX_VALUES:
                    size = min(OR_MAX_VALUES, size * 2)     # 余裕があれば束を戻す
            return
        info["capped_parts"].append(dict(params))

    p0 = {"odpt:operator": ctx.op}
    d0, _ = ctx.get(datatype, p0)
    if d0 is None:
        info["failed_parts"] += 1
    else:
        take(d0)
        split(p0, d0, 0)
    info["n_requests"] = ctx.n_requests - n0
    return list(seen.values()), info


# ------------------------------------------------------------------ 版の取得
def version_dir(root: Path, d) -> Path:
    return Path(root) / SOURCE / d.isoformat()


def file_name(datatype: str, op: str) -> str:
    return f"{type_short(datatype)}_{op_short(op)}.json.gz"


def _load_index(path: Path) -> dict:
    try:
        idx = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return idx if isinstance(idx, dict) else {}


def fetch_version(root: Path, *, operators=None, types=None, now=None, timeout: float = 60.0,
                  retries: int = 1, sleep: float = 1.0, sleep_fn=None, key: str | None = None,
                  max_requests_per_operator: int | None = None,
                  progress=None) -> tuple[dict, list[dict]]:
    """オープン枠の静的データの版を 1 回取り、`odpt_static/<取得日>/` に残す。

    operator は `odpt:Operator` の一覧(航空会社を除く)、種類は `STATIC_TYPES`。件数 0 の組は
    ファイルを作らず `_index.json` に n=0 で残す。同じ日に取り直すと、その組だけ上書きする。
    戻り値 = (`_index.json` の中身, 台帳行)。
    """
    now = now or common.now_jst()
    key = key if key is not None else common.resolve_key(OPEN_KEY_ENV)
    common.register_secret(key)
    types = tuple(types or STATIC_TYPES)
    d = now.date()
    rows: list[dict] = []
    if not key:
        rows.append(ledger.make_entry(SOURCE, "version", ok=False, date_jst=d.isoformat(),
                                      error=f"key-missing:{OPEN_KEY_ENV}"))
        return {}, rows
    if operators is None:
        ops, res = list_operators(key, timeout=timeout, retries=retries, sleep_fn=sleep_fn)
        rows.append(ledger.make_entry(SOURCE, "version/odpt:Operator", ok=ops is not None,
                                      http_status=res.status, n_records=len(ops or []),
                                      date_jst=d.isoformat(), error=res.error))
        if ops is None:
            return {}, rows
        common.polite_sleep(sleep, sleep_fn)
        operators = [o for o in ops if o not in AIRLINE_OPERATORS]

    vdir = version_dir(root, d)
    vdir.mkdir(parents=True, exist_ok=True)
    idx_path = vdir / "_index.json"
    index = _load_index(idx_path)
    entries = index.get("entries") if isinstance(index.get("entries"), dict) else {}

    for op in operators:
        ctx = _Ctx(op, key, timeout=timeout, retries=retries, sleep=sleep, sleep_fn=sleep_fn,
                   max_requests=max_requests_per_operator)
        for dt in types:
            n_fail0 = len(ctx.failures)
            try:
                recs, how = fetch_complete(ctx, dt)
                ctx._cache.setdefault(dt, recs)
            except Exception as exc:            # 1 組の事故で版全体を止めない
                rows.append(ledger.make_entry(SOURCE, f"{dt}/{op}", ok=False,
                                              date_jst=d.isoformat(),
                                              error=f"{type(exc).__name__}: {exc}"))
                continue
            fails = ctx.failures[n_fail0:]
            st = record_stats(recs)
            ent = {"operator": op, "datatype": dt, "n": len(recs),
                   "issued_min": st["issued_min"], "issued_max": st["issued_max"],
                   "date_min": st["date_min"], "date_max": st["date_max"],
                   "n_requests": how["n_requests"], "parts": how["parts"],
                   "failed_parts": how["failed_parts"], "capped_parts": how["capped_parts"],
                   "split_keys_used": how["split_keys_used"], "file": None,
                   "bytes_raw": 0, "bytes_gz": 0, "fetched_jst": common.iso_jst(now)}
            ok = how["parts"] > 0
            if recs:
                meta = common.build_meta(
                    SOURCE, module="odpt_static.py",
                    urls=[odpt_rt.display_url("open", dt, {"odpt:operator": op})],
                    n_records=len(recs), n_missing=0, caveats=CAVEATS,
                    notes=["オープン枠の静的データの版。値は API の応答のまま。",
                           "打ち切りに当たった区画は split_keys_used の欄で分けて取り直し、"
                           "owl:sameAs で重複を除いた。"],
                    extra={"datatype": dt, "operator": op, "version_date": d.isoformat(),
                           **{k: ent[k] for k in ("issued_min", "issued_max", "date_min",
                                                  "date_max", "n_requests", "parts",
                                                  "failed_parts", "capped_parts",
                                                  "split_keys_used")}})
                path, n_raw, n_gz = common.write_json_gz(vdir / file_name(dt, op),
                                                         {"_meta": meta, "data": recs})
                ent.update({"file": path.name, "bytes_raw": n_raw, "bytes_gz": n_gz})
            entries[f"{op}|{dt}"] = ent
            rows.append(ledger.make_entry(
                SOURCE, f"{dt}/{op}", ok=ok, n_records=len(recs), date_jst=d.isoformat(),
                error=None if ok else (fails[0].get("error") if fails else "failed"),
                extra={k: ent[k] for k in ("n_requests", "parts", "failed_parts", "file",
                                           "bytes_raw", "bytes_gz", "issued_max",
                                           "split_keys_used")}
                | {"n_capped_parts": len(how["capped_parts"])}))
            if progress:
                progress(ent)
    index = {"schema_version": 1, "version_date": d.isoformat(),
             "updated_jst": common.iso_jst(now), "entries": entries}
    text = common.scrub(json.dumps(index, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    idx_path.write_text(text, encoding="utf-8", newline="\n")
    return index, rows


# ------------------------------------------------------------------ 新しい版の有無(--check)
def latest_version(root: Path) -> Path | None:
    base = Path(root) / SOURCE
    if not base.exists():
        return None
    dirs = sorted(p for p in base.iterdir()
                  if p.is_dir() and len(p.name) == 10 and (p / "_index.json").exists())
    return dirs[-1] if dirs else None


def _ver_key(issued, date) -> tuple[str, str]:
    return (issued or "", date or "")


def check(root: Path, *, operators=None, types=None, now=None, timeout: float = 60.0,
          retries: int = 1, sleep: float = 1.0, sleep_fn=None,
          key: str | None = None) -> tuple[dict, list[dict]]:
    """保存済みの最新版と、いま API が返す `dct:issued`(無ければ `dc:date`)の最大を比べる。

    問い合わせは版に入っている組だけ(operator ごと 1 本・分けない)。打ち切りに当たった組は
    1,000 件の範囲の比べになるので `capped` を付ける。operator の一覧も 1 本取り、版に無い
    operator(航空会社を除く)を挙げる。保存はしない(台帳行だけ)。
    """
    now = now or common.now_jst()
    key = key if key is not None else common.resolve_key(OPEN_KEY_ENV)
    common.register_secret(key)
    d = now.date()
    rows: list[dict] = []
    rep = {"version": None, "newer": [], "gone": [], "same": 0, "failed": [],
           "new_operators": [], "n_requests": 0}
    vdir = latest_version(root)
    if vdir is None:
        rep["error"] = "保存済みの版が無い"
        return rep, rows
    rep["version"] = vdir.name
    if not key:
        rows.append(ledger.make_entry(SOURCE, "check", ok=False, date_jst=d.isoformat(),
                                      error=f"key-missing:{OPEN_KEY_ENV}"))
        rep["error"] = f"key-missing:{OPEN_KEY_ENV}"
        return rep, rows
    entries = _load_index(vdir / "_index.json").get("entries") or {}
    want_ops = set(operators) if operators else None
    want_types = set(types) if types else None
    n_req0 = common.request_count()
    for k in sorted(entries):
        ent = entries[k]
        op, dt = ent.get("operator"), ent.get("datatype")
        if not ent.get("n"):
            continue
        if (want_ops and op not in want_ops) or (want_types and dt not in want_types):
            continue
        data, res = _fetch(dt, {"odpt:operator": op}, key, timeout=timeout, retries=retries,
                           sleep_fn=sleep_fn)
        common.polite_sleep(sleep, sleep_fn)
        if data is None:
            rep["failed"].append({"operator": op, "datatype": dt, "error": res.error})
            rows.append(ledger.make_entry(SOURCE, f"check/{dt}/{op}", ok=False,
                                          http_status=res.status, date_jst=d.isoformat(),
                                          error=res.error or "failed"))
            continue
        st = record_stats(data)
        saved = _ver_key(ent.get("issued_max"), ent.get("date_max"))
        now_k = _ver_key(st["issued_max"], st["date_max"])
        item = {"operator": op, "datatype": dt, "saved_issued_max": ent.get("issued_max"),
                "api_issued_max": st["issued_max"], "saved_date_max": ent.get("date_max"),
                "api_date_max": st["date_max"], "capped": is_capped(len(data)),
                "api_n": len(data)}
        if not data:
            rep["gone"].append(item)
        elif now_k[0] > saved[0] or (now_k[0] == saved[0] and now_k[1] > saved[1]):
            rep["newer"].append(item)
        else:
            rep["same"] += 1
        rows.append(ledger.make_entry(SOURCE, f"check/{dt}/{op}", ok=True, http_status=200,
                                      n_records=len(data), date_jst=d.isoformat(),
                                      extra={k2: item[k2] for k2 in ("api_issued_max",
                                                                     "api_date_max", "capped")}))
    if not want_ops:
        ops, res = list_operators(key, timeout=timeout, retries=retries, sleep_fn=sleep_fn)
        if ops is not None:
            have = {e.get("operator") for e in entries.values()}
            rep["new_operators"] = [o for o in ops if o not in have and o not in AIRLINE_OPERATORS]
        else:
            rep["failed"].append({"operator": "*", "datatype": "odpt:Operator",
                                  "error": res.error})
    rep["n_requests"] = common.request_count() - n_req0
    return rep, rows


def format_check(rep: dict) -> str:
    lines = ["-" * 72, f"odpt_static --check(保存済みの最新版 {rep.get('version') or 'なし'})",
             "-" * 72]
    if rep.get("error"):
        lines.append(f"  {rep['error']}")
        return "\n".join(lines)
    for it in rep["newer"]:
        lines.append(f"  新しい版: {it['datatype']} / {it['operator']}  "
                     f"issued {it['saved_issued_max']} → {it['api_issued_max']}  "
                     f"date {it['saved_date_max']} → {it['api_date_max']}"
                     + ("(1,000 件の範囲の比べ)" if it["capped"] else ""))
    for it in rep["gone"]:
        lines.append(f"  API で 0 件: {it['datatype']} / {it['operator']}")
    for op in rep["new_operators"]:
        lines.append(f"  版に無い operator: {op}")
    for it in rep["failed"]:
        lines.append(f"  失敗: {it['datatype']} / {it['operator']}  {it['error']}")
    lines.append(f"  新しい版 {len(rep['newer'])} 組 / 変わらない {rep['same']} 組 / "
                 f"HTTP要求 {rep['n_requests']} 本")
    if rep["newer"] or rep["new_operators"]:
        lines.append("  → `--source odpt_static` で版を取る(全部取り直す。--operators で絞れる)")
    return "\n".join(lines)


def plan() -> list[tuple[str, str]]:
    """`--offline` 用(キーは渡さない)。operator の一覧の 1 本と、種類ごとの問い合わせの形。"""
    out = [("静的 odpt:Operator の一覧(オープン枠)", odpt_rt.display_url("open", "odpt:Operator", {}))]
    for dt in STATIC_TYPES:
        out.append((f"静的 {dt}(operator ごと・打ち切りなら "
                    f"{'→'.join(SPLIT_KEYS.get(dt, ())) or '分けない'} で分ける)",
                    odpt_rt.display_url("open", dt, {"odpt:operator": "<operator>"})))
    return out
