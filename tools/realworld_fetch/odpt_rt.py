#!/usr/bin/env python3
"""A4: ODPT リアルタイム(運行情報 TrainInformation・列車の在線 Train・バスの在線 Bus)。

第333(ユーザー決定 2026-10-13・回答 10-13b §5)で集め方を変えた:
  オープン枠   提供のある operator × {TrainInformation, Train, Bus} を**全部**取り、
               路線で絞らず全レコードを保存する(範囲を広げるときの材料)。operator の表
               `OPEN_RT_OPERATORS` は §A の洗い出し(2026-10-13 夜)から。
  チャレンジ枠 **作品に使う範囲だけ**(東急 東横線・田園都市線と京王 井の頭線の運行情報、
               JR 東日本 山手線・埼京線・湘南新宿ラインの在線)。先回りの収集はしない
               (チャレンジ限定ライセンス 第 4 条 1 項=用途が応募作品に限られる)。

保存: `odpt_rt/<YYYY>/<MM>/<YYYY-MM-DD>/<種類>_<operator>_<HHMMSS>.json.gz`(gzip・標準ライブラリ)。
  チャレンジ枠の operator は `<operator>-challenge`(オープン枠のファイルと名前がぶつからない)。
種類ごとの間隔 `CADENCE`(秒): タスクが 5 分ごとに起動しても、間隔に満たない種類は飛ばす。
  最後に取った時刻は `odpt_rt/_last_fetch.json`(飛ばした回数もここに数だけ残す。台帳には書かない)。
変化した分だけ保存 `DEDUPE`: 直前の保存と `data` が同じ(`dc:date`・`dct:valid` を除いた正準 JSON の
  ハッシュが同じ)なら保存せず、台帳行に `unchanged: true` と `same_as`(同じ中身のファイル名)を残す。
  ただし日付が変わって最初の取得は必ず保存する(各日のフォルダだけで、その日の始めの状態が分かる)。

**APIキーは環境変数からのみ読む**: オープン枠 `ODPT_API_KEY` / チャレンジ枠 `ODPT_CHALLENGE_API_KEY`。
  値はコード・ログ・保存物・報告に一切出さない(`common.register_secret` → `scrub`)。
★ `dct:valid`(= `dc:date` + 5分)を過ぎたレコードは ODPT ガイドラインにより使用しない。
   期限切れは `data` から外し、件数と識別子を `_meta` に残す(黙って消さない)。
★ 検索の口は 1 応答 1,000 件で打ち切られる。1,000 件に達した応答は `capped: true` を台帳と `_meta` に残す。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date as _date
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlencode

from . import common, ledger

SOURCE = "odpt_rt"
OPEN_BASE = "https://api.odpt.org/api/v4/"
CHALLENGE_BASE = "https://api-challenge.odpt.org/api/v4/"
OPEN_KEY_ENV = "ODPT_API_KEY"
CHALLENGE_KEY_ENV = "ODPT_CHALLENGE_API_KEY"
API_CAP = 1000


def is_capped(n: int) -> bool:
    """検索の口の打ち切りに当たった疑い。上限は種類で違う(多くは 1,000。BusstopPole は 10,000 の
    応答を見た=2026-10-13)ので、1,000 の倍数ちょうどを「当たった疑い」とみなす。"""
    return n >= API_CAP and n % API_CAP == 0


RT_TYPES = ("odpt:TrainInformation", "odpt:Train", "odpt:Bus")
# ファイル名と台帳の target に使う短い名前。
TYPE_FILE = {"odpt:TrainInformation": "traininformation", "odpt:Train": "train", "odpt:Bus": "bus"}
TYPE_TARGET = {"odpt:TrainInformation": "TrainInformation", "odpt:Train": "Train", "odpt:Bus": "Bus"}

# 渋谷駅に乗り入れる9路線。scope = そのデータが取れる枠(実測 §2-4)。
# 第333 からは **チャレンジ枠の行だけ**を使う(作品の範囲)。オープン枠は OPEN_RT_OPERATORS で全路線。
RAILWAYS: list[dict] = [
    {"key": "jr_yamanote", "label": "JR山手線", "operator": "odpt.Operator:JR-East",
     "railway": "odpt.Railway:JR-East.Yamanote", "train": "challenge", "info": None},
    {"key": "jr_saikyo", "label": "JR埼京線", "operator": "odpt.Operator:JR-East",
     "railway": "odpt.Railway:JR-East.SaikyoKawagoe", "train": "challenge", "info": None},
    {"key": "jr_shonanshinjuku", "label": "JR湘南新宿ライン", "operator": "odpt.Operator:JR-East",
     "railway": "odpt.Railway:JR-East.ShonanShinjuku", "train": "challenge", "info": None},
    {"key": "tokyu_toyoko", "label": "東急東横線", "operator": "odpt.Operator:Tokyu",
     "railway": "odpt.Railway:Tokyu.Toyoko", "train": None, "info": "challenge"},
    {"key": "tokyu_denentoshi", "label": "東急田園都市線", "operator": "odpt.Operator:Tokyu",
     "railway": "odpt.Railway:Tokyu.DenEnToshi", "train": None, "info": "challenge"},
    {"key": "keio_inokashira", "label": "京王井の頭線", "operator": "odpt.Operator:Keio",
     "railway": "odpt.Railway:Keio.Inokashira", "train": None, "info": "challenge"},
    {"key": "metro_ginza", "label": "東京メトロ銀座線", "operator": "odpt.Operator:TokyoMetro",
     "railway": "odpt.Railway:TokyoMetro.Ginza", "train": None, "info": "open"},
    {"key": "metro_hanzomon", "label": "東京メトロ半蔵門線", "operator": "odpt.Operator:TokyoMetro",
     "railway": "odpt.Railway:TokyoMetro.Hanzomon", "train": None, "info": "open"},
    {"key": "metro_fukutoshin", "label": "東京メトロ副都心線", "operator": "odpt.Operator:TokyoMetro",
     "railway": "odpt.Railway:TokyoMetro.Fukutoshin", "train": None, "info": "open"},
]

# オープン枠で提供のある operator(第333 §A の洗い出し・2026-10-13 22 時台の照会で 1 件以上)。
# 夜の照会なので、在線(Train・Bus)は昼に増える operator がありうる(記録 §A の注。昼の照会は
# `--source odpt_static --survey --static-types odpt:TrainInformation,odpt:Train,odpt:Bus`)。
OPEN_RT_OPERATORS: dict[str, tuple[str, ...]] = {
    "odpt:TrainInformation": (
        "odpt.Operator:MIR", "odpt.Operator:TWR", "odpt.Operator:TamaMonorail",
        "odpt.Operator:Toei", "odpt.Operator:TokyoMetro", "odpt.Operator:YokohamaMunicipal",
    ),
    "odpt:Train": ("odpt.Operator:Toei", "odpt.Operator:YokohamaMunicipal"),
    "odpt:Bus": ("odpt.Operator:SeibuBus", "odpt.Operator:Toei", "odpt.Operator:YokohamaMunicipal"),
}
# OR でつなげる値の数の上限(2026-10-13 実測: 10 個まで受け、11 個で HTTP 400)。
OR_MAX_VALUES = 10

# 種類ごとの取得の間隔(秒)。**仮の値**(親が用途=遅延の日の再現から決める)。
CADENCE: dict[str, int] = {"odpt:TrainInformation": 300, "odpt:Train": 300, "odpt:Bus": 300}
# タスクの起動の揺れ(数秒〜数十秒)で 1 回分を飛ばさないための余裕(expedient)。
# 経過が「間隔 − 余裕」以上なら取る。例: 間隔 300・余裕 60 なら 240 秒以上で取る。
CADENCE_SLACK_S = 60
# 変化した分だけ保存するか(種類ごと)。運行情報はめったに変わらない=on。在線は毎回変わる=off。
DEDUPE: dict[str, bool] = {"odpt:TrainInformation": True, "odpt:Train": False, "odpt:Bus": False}
# 同じ中身かを比べるとき除く欄(毎回変わる生成時刻と有効期限)。
DEDUPE_IGNORE_KEYS = ("dc:date", "dct:valid")

STATE_NAME = "_last_fetch.json"
STATE_SCHEMA = 1

CAVEATS = [
    "チャレンジ枠(api-challenge)のデータは公共交通オープンデータチャレンジ限定ライセンス。用途は"
    "応募作品に限られ(第 4 条 1 項)、第三者が再利用できる形での公開・再配布をしない(第 8 条 4 項(1))。"
    "成果物には集計値・グラフだけを載せる。",
    "オープン枠も基本ライセンス 第 8 条 4 項(1) で同じ型の再配布の禁止がある。出典表示は必須。",
    "dct:valid(= dc:date + 5分)を過ぎたレコードは使用しない。期限切れは data から外し、"
    "件数を _meta.n_expired に記録している。",
    "リアルタイム情報を表示する際はデータ生成時刻(dc:date)と出典を必ず併記すること。",
    "検索の口は 1 応答 1,000 件で打ち切られる。_meta.capped が true の応答は欠けている可能性がある。",
]

README_TEXT = """# odpt_rt/ — ODPT リアルタイム(取り扱い注意)

このディレクトリの中身は **公共交通オープンデータセンター(ODPT)** のデータです。
取得器は `tools/realworld_fetch/odpt_rt.py`(第333 で集め方を変えた)。

## 中身

- `<YYYY>/<MM>/<YYYY-MM-DD>/<種類>_<operator>_<HHMMSS>.json.gz`(gzip した JSON。`_meta` と `data`)
  - 種類: `traininformation`(運行情報)・`train`(列車の在線)・`bus`(バスの在線)
  - `<operator>` が `-challenge` で終わるファイルはチャレンジ枠
- **オープン枠**: 提供のある事業者の全路線・全レコードを保存(路線で絞らない)
- **チャレンジ枠**: 作品に使う範囲だけ(東急 東横線・田園都市線と京王 井の頭線の運行情報、
  JR 東日本 山手線・埼京線・湘南新宿ラインの在線)。範囲を広げる先回りの収集はしない
- `_last_fetch.json`: 種類 × 事業者ごとの最後の取得時刻と、間隔に満たず飛ばした回数
- 変化した分だけ保存(既定は運行情報だけ): 直前と同じ中身なら保存せず、台帳 `_ledger.jsonl` の行に
  `unchanged: true` と `same_as`(同じ中身のファイル名)を残す。日付が変わって最初の取得は必ず保存する
- 2026-10-13 より前のファイル(`train_<HHMMSS>.json` と `traininformation_<HHMMSS>.json`)は
  渋谷の 9 路線に絞った非圧縮の形

## 用途と再配布の制限(重要)

- チャレンジ枠のファイルは **公共交通オープンデータチャレンジ限定ライセンス**のデータです。
  用途は応募作品に限られ(第 4 条 1 項)、第三者が再利用できる形での公開・再配布はできません
  (第 8 条 4 項(1))。
- オープン枠(基本ライセンス)も第 8 条 4 項(1) で同じ型の再配布の禁止があります。
- したがって:
  - リポジトリにコミットしない(このディレクトリは .gitignore の下)。
  - 論文・発表資料・提出物には **生データを添付しない**。載せてよいのは集計値・グラフのみ。
  - 第三者へファイルを渡さない。

## 出典表示(必須)

> 本データは公共交通オープンデータセンターのデータを利用して作成。

リアルタイム情報を表示するときは、併せて **データ生成時刻(`dc:date`)** を明記してください。

## 有効期限

各レコードの `dct:valid` は `dc:date + 5分` です。ODPT ガイドラインは有効範囲を超えた
データの使用を認めていません。取得器は期限切れレコードを `data` から外し、件数だけを
`_meta.n_expired` に残しています。

## 1,000 件の打ち切り

検索の口は 1 応答 1,000 件で打ち切られます。1,000 件に達した応答は `_meta.capped: true` です
(欠けている可能性がある)。

## API キー

キーは環境変数 `ODPT_API_KEY` / `ODPT_CHALLENGE_API_KEY` からのみ読みます。
**キーの値はこのディレクトリのどのファイルにも書かれていません**(取得器が保存直前に
機械的にマスクします)。
"""


# ------------------------------------------------------------------ URL
def _query(params: dict) -> str:
    return urlencode(params, safe=":", quote_via=quote)


def api_url(scope: str, datatype: str, params: dict, key: str | None) -> str:
    """実要求 URL(キー入り)。**この戻り値は絶対に print / 保存しない。**"""
    base = CHALLENGE_BASE if scope == "challenge" else OPEN_BASE
    full = dict(params)
    if key:
        full["acl:consumerKey"] = key
    return f"{base}{datatype}?{_query(full)}"


def display_url(scope: str, datatype: str, params: dict) -> str:
    """表示・保存用 URL。consumerKey は常に *** 固定(キーを渡さないので漏れようがない)。"""
    base = CHALLENGE_BASE if scope == "challenge" else OPEN_BASE
    q = _query(params)
    return f"{base}{datatype}?{q}{'&' if q else ''}acl:consumerKey={common.MASK}"


def op_short(op: str) -> str:
    """`odpt.Operator:TokyoMetro` → `TokyoMetro`。"""
    return str(op).split(":", 1)[-1]


def op_token(scope: str, op: str) -> str:
    """ファイル名の operator の部分。チャレンジ枠は `-challenge` を付ける。"""
    return op_short(op) + ("-challenge" if scope == "challenge" else "")


def out_path(root: Path, d: _date, datatype: str, scope: str, op: str, stamp: str) -> Path:
    """`odpt_rt/<Y>/<M>/<D>/<種類>_<operator>_<HHMMSS>.json.gz`。"""
    return (common.day_dir(root, SOURCE, d)
            / f"{TYPE_FILE[datatype]}_{op_token(scope, op)}_{stamp}.json.gz")


def ensure_readme(root: Path) -> Path:
    path = Path(root) / SOURCE / "README.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != README_TEXT:
        path.write_text(README_TEXT, encoding="utf-8", newline="\n")
    return path


# ------------------------------------------------------------------ 取得の単位(job)
def jobs(railways=None, open_operators=None) -> list[dict]:
    """取得の単位 = (枠, 種類, operator) と、その問い合わせの並び。

    オープン枠: `OPEN_RT_OPERATORS` の operator ごとに `?odpt:operator=` を 1 本(絞らない)。
    チャレンジ枠: `RAILWAYS` のチャレンジの行だけ。運行情報は operator ごとに取って作品の路線に絞る。
    在線は路線ごとに問い合わせて operator ごとに 1 ファイルにまとめる(今までと同じ範囲)。
    """
    railways = list(railways or RAILWAYS)
    table = OPEN_RT_OPERATORS if open_operators is None else open_operators
    out: list[dict] = []
    for dt in RT_TYPES:
        for op in table.get(dt, ()):
            out.append({"scope": "open", "datatype": dt, "operator": op,
                        "parts": [{"params": {"odpt:operator": op}, "target": op}],
                        "railway_filter": None})
    info_ops = sorted({r["operator"] for r in railways if r["info"] == "challenge"})
    for op in info_ops:
        wanted = sorted(r["railway"] for r in railways
                        if r["info"] == "challenge" and r["operator"] == op)
        out.append({"scope": "challenge", "datatype": "odpt:TrainInformation", "operator": op,
                    "parts": [{"params": {"odpt:operator": op}, "target": op}],
                    "railway_filter": wanted})
    train_ops = sorted({r["operator"] for r in railways if r["train"] == "challenge"})
    for op in train_ops:
        rs = [r for r in railways if r["train"] == "challenge" and r["operator"] == op]
        out.append({"scope": "challenge", "datatype": "odpt:Train", "operator": op,
                    "parts": [{"params": {"odpt:railway": r["railway"]}, "target": r["key"]}
                              for r in rs],
                    "railway_filter": None})
    return out


def job_key(job: dict) -> str:
    return f"{job['scope']}|{job['datatype']}|{job['operator']}"


def plan(railways=None, open_operators=None) -> list[tuple[str, str]]:
    """`--offline` 用。キーは渡さないので URL に載らない。"""
    out: list[tuple[str, str]] = []
    for job in jobs(railways, open_operators):
        for part in job["parts"]:
            out.append((f"{TYPE_TARGET[job['datatype']]} ({job['scope']}) {part['target']}"
                        f"  間隔 {CADENCE.get(job['datatype'])} 秒",
                        display_url(job["scope"], job["datatype"], part["params"])))
    return out


# ------------------------------------------------------------------ 有効期限・絞り・要約
def _parse_dt(text):
    if not isinstance(text, str) or not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def split_expired(records: list[dict], now: datetime) -> tuple[list[dict], list[str]]:
    """`dct:valid` を過ぎたレコードを外す。戻り値 = (有効, 期限切れの識別子)。"""
    valid, expired = [], []
    for rec in records:
        vt = _parse_dt(rec.get("dct:valid")) if isinstance(rec, dict) else None
        if vt is not None and vt < now:
            expired.append(str(rec.get("owl:sameAs") or rec.get("@id") or "?"))
        else:
            valid.append(rec)
    return valid, expired


def shibuya_railways(records: list[dict], railways=None) -> list[dict]:
    """渋谷9路線に該当するレコードだけを残す(第333 からはチャレンジ枠の作品の範囲にだけ使う)。"""
    wanted = {r["railway"] for r in (railways or RAILWAYS)}
    return [r for r in records if r.get("odpt:railway") in wanted]


def delay_summary(trains: list[dict]) -> dict:
    """在線レコードの遅延(秒)の要約。値が無ければ None(0 と偽らない)。"""
    delays = [r["odpt:delay"] for r in trains
              if isinstance(r.get("odpt:delay"), (int, float))]
    if not delays:
        return {"n": 0, "max_s": None, "mean_s": None, "n_delayed": 0}
    return {"n": len(delays), "max_s": max(delays),
            "mean_s": round(sum(delays) / len(delays), 2),
            "n_delayed": sum(1 for x in delays if x > 0)}


def content_hash(records: list) -> str:
    """`DEDUPE_IGNORE_KEYS` を除いた正準 JSON(レコードの順は問わない)の sha256。"""
    canon = []
    for rec in records:
        if isinstance(rec, dict):
            rec = {k: v for k, v in rec.items() if k not in DEDUPE_IGNORE_KEYS}
        canon.append(common.canonical_json(rec))
    canon.sort()
    return hashlib.sha256("\n".join(canon).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ 状態ファイル
def state_path(root: Path) -> Path:
    return Path(root) / SOURCE / STATE_NAME


def load_state(root: Path) -> dict:
    """`_last_fetch.json` を読む。無い・壊れているときは空(壊れたものは `_broken` に数える)。"""
    path = state_path(root)
    empty = {"schema_version": STATE_SCHEMA, "jobs": {}}
    if not path.exists():
        return empty
    try:
        st = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        empty["n_broken_reads"] = 1
        return empty
    if not isinstance(st, dict) or not isinstance(st.get("jobs"), dict):
        empty["n_broken_reads"] = 1
        return empty
    return st


def save_state(root: Path, st: dict, now: datetime) -> Path:
    st = dict(st)
    st["schema_version"] = STATE_SCHEMA
    st["updated_jst"] = common.iso_jst(now)
    st["cadence_s"] = dict(CADENCE)
    st["dedupe"] = dict(DEDUPE)
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = common.scrub(json.dumps(st, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    return path


def due(entry: dict | None, datatype: str, now: datetime, *, cadence=None) -> bool:
    """間隔に達したか。前回が無い・時計が戻った・読めないときは取る。"""
    if not entry or not entry.get("last_fetch_jst"):
        return True
    last = _parse_dt(entry.get("last_fetch_jst"))
    if last is None:
        return True
    cad = (cadence or CADENCE).get(datatype, 300)
    elapsed = (now - last).total_seconds()
    return not (0 <= elapsed < cad - CADENCE_SLACK_S)


# ------------------------------------------------------------------ バスの打ち切りの取り直し
def static_busroutes(root: Path, op: str) -> set[str]:
    """保存済みの静的データの最新版(`odpt_static/<日付>/busroutepattern_<op>.json.gz`)の系統の一覧。

    版が無ければ空。ネット不使用。
    """
    base = Path(root) / "odpt_static"
    if not base.exists():
        return set()
    name = f"busroutepattern_{op_short(op)}.json.gz"
    for vdir in sorted((p for p in base.iterdir() if p.is_dir() and len(p.name) == 10),
                       reverse=True):
        path = vdir / name
        if path.exists():
            try:
                doc = common.read_json_any(path)
            except (OSError, ValueError, EOFError):
                return set()
            return {r.get("odpt:busroute") for r in doc.get("data", [])
                    if isinstance(r, dict) and isinstance(r.get("odpt:busroute"), str)}
    return set()


def _split_bus(root: Path, op: str, capped_data: list, key: str, *, timeout: float,
               retries: int, sleep: float, sleep_fn=None) -> tuple[list, dict]:
    """バスの在線が打ち切られたとき、系統(`odpt:busroute`)で 10 個ずつに分けて取り直す。

    系統の一覧 = 打ち切られた応答に出た系統 ∪ 静的データの最新版の系統(あれば)。
    戻り値 = (owl:sameAs で重複を除いたレコード, 情報)。
    """
    seen: dict[str, dict] = {}
    for rec in capped_data:
        if isinstance(rec, dict):
            seen.setdefault(str(rec.get("owl:sameAs") or rec.get("@id")), rec)
    from_resp = {r.get("odpt:busroute") for r in capped_data
                 if isinstance(r, dict) and isinstance(r.get("odpt:busroute"), str)}
    from_static = static_busroutes(root, op)
    routes = sorted(from_resp | from_static)
    info = {"split_by": "odpt:busroute", "n_routes": len(routes),
            "route_source": "static+response" if from_static else "response-only",
            "n_split_requests": 0, "n_failed_split": 0, "capped_after_split": False}
    for i in range(0, len(routes), OR_MAX_VALUES):
        batch = routes[i:i + OR_MAX_VALUES]
        data, res = _fetch("open", "odpt:Bus", {"odpt:operator": op,
                                                "odpt:busroute": ",".join(batch)},
                           key, timeout=timeout, retries=retries, sleep_fn=sleep_fn)
        info["n_split_requests"] += 1
        common.polite_sleep(sleep, sleep_fn)
        if data is None:
            info["n_failed_split"] += 1
            continue
        if is_capped(len(data)):
            info["capped_after_split"] = True
        for rec in data:
            if isinstance(rec, dict):
                seen.setdefault(str(rec.get("owl:sameAs") or rec.get("@id")), rec)
    return list(seen.values()), info


# ------------------------------------------------------------------ 取得
def _fetch(scope: str, datatype: str, params: dict, key: str, *, timeout: float,
           retries: int, sleep_fn=None):
    url = api_url(scope, datatype, params, key)     # ← 絶対に print / 保存しない
    res = common.http_get(url, timeout=timeout, retries=retries, sleep_fn=sleep_fn,
                          same_host_only=True)
    res.url_masked = display_url(scope, datatype, params)
    if not res.ok:
        return None, res
    try:
        data = json.loads(res.text())
    except ValueError:
        return None, res
    if not isinstance(data, list):
        res.error = "unexpected-response"
        return None, res
    return data, res


def _key_env(scope: str) -> str:
    return OPEN_KEY_ENV if scope == "open" else CHALLENGE_KEY_ENV


def fetch_snapshot(root: Path, *, now=None, railways=None, timeout: float = 30.0,
                   retries: int = 1, sleep: float = 1.0, sleep_fn=None,
                   open_key: str | None = None, challenge_key: str | None = None,
                   open_operators=None, force: bool = False, cadence=None,
                   dedupe=None) -> tuple[list[dict], list[dict]]:
    """運行情報・在線・バスの 1 スナップショット。戻り値 = (保存した文書のリスト, 台帳行)。

    キー未設定の枠は **リクエストを出さずに** 飛ばし、台帳へ理由を残す。
    間隔に満たない job は飛ばす(台帳に書かない・`_last_fetch.json` に数だけ)。`force` で無視する。
    """
    now = now or common.now_jst()
    cadence = dict(cadence or CADENCE)
    dedupe = dict(DEDUPE if dedupe is None else dedupe)
    open_key = open_key if open_key is not None else common.resolve_key(OPEN_KEY_ENV)
    challenge_key = (challenge_key if challenge_key is not None
                     else common.resolve_key(CHALLENGE_KEY_ENV))
    keys = {"open": open_key, "challenge": challenge_key}
    common.register_secret(open_key)
    common.register_secret(challenge_key)
    ensure_readme(root)
    d = now.date()
    stamp = now.strftime("%H%M%S")
    snap = common.iso_jst(now)
    st = load_state(root)
    st_jobs = st.setdefault("jobs", {})
    docs, rows = [], []

    def _one(job: dict) -> None:
        scope, dt, op = job["scope"], job["datatype"], job["operator"]
        jk = job_key(job)
        ent = st_jobs.setdefault(jk, {})
        base_extra = {"scope": scope, "datatype": dt, "operator": op, "snapshot_jst": snap}
        if not keys[scope]:
            for part in job["parts"]:
                rows.append(ledger.make_entry(
                    SOURCE, f"{TYPE_TARGET[dt]}/{scope}/{part['target']}", ok=False,
                    date_jst=d.isoformat(), error=f"key-missing:{_key_env(scope)}",
                    extra=dict(base_extra)))
            return
        if not force and not due(ent, dt, now, cadence=cadence):
            ent["n_skipped_cadence"] = int(ent.get("n_skipped_cadence", 0)) + 1
            return

        records: list[dict] = []
        urls: list[str] = []
        part_rows: list[dict] = []
        n_expired = 0
        expired_ids: list[str] = []
        n_ok_parts = 0
        any_capped = False
        split_meta = None
        for part in job["parts"]:
            data, res = _fetch(scope, dt, part["params"], keys[scope], timeout=timeout,
                               retries=retries, sleep_fn=sleep_fn)
            urls.append(res.url_masked)
            target = f"{TYPE_TARGET[dt]}/{scope}/{part['target']}"
            if data is None:
                part_rows.append(ledger.make_entry(
                    SOURCE, target, ok=False, http_status=res.status, date_jst=d.isoformat(),
                    error=res.error or "failed", extra=dict(base_extra)))
                common.polite_sleep(sleep, sleep_fn)
                continue
            n_ok_parts += 1
            capped = is_capped(len(data))
            n_api = len(data)
            split_info = None
            if capped and scope == "open" and dt == "odpt:Bus":
                data, split_info = _split_bus(root, op, data, keys[scope], timeout=timeout,
                                              retries=retries, sleep=sleep, sleep_fn=sleep_fn)
                capped = split_info["capped_after_split"] or split_info["n_failed_split"] > 0
                split_meta = split_info
            any_capped = any_capped or capped
            kept = data
            if job["railway_filter"] is not None:
                wanted = set(job["railway_filter"])
                kept = [r for r in kept if isinstance(r, dict) and r.get("odpt:railway") in wanted]
            kept, exp = split_expired(kept, now)
            n_expired += len(exp)
            expired_ids += exp
            for rec in kept:
                if isinstance(rec, dict):
                    rec["_scope"] = scope
            records += kept
            part_rows.append(ledger.make_entry(
                SOURCE, target, ok=True, http_status=200, n_records=len(kept),
                date_jst=d.isoformat(),
                extra=dict(base_extra, n_total=len(data), n_expired=len(exp), complete=not capped,
                           capped=capped, bytes_api=len(res.body or b""),
                           **({"n_api_first": n_api, **split_info} if split_info else {}))))
            common.polite_sleep(sleep, sleep_fn)

        if n_ok_parts == 0:
            rows.extend(part_rows)
            return

        h = content_hash(records)
        last_day = str(ent.get("last_saved_date") or "")
        unchanged = bool(dedupe.get(dt)) and ent.get("last_hash") == h \
            and last_day == d.isoformat() and bool(ent.get("last_file"))
        info: dict = {"unchanged": unchanged}
        if not records:
            # 0 件(運行の無い時間帯など)はファイルを作らない(台帳の行が証拠)。
            info["empty"] = True
            ent["n_empty"] = int(ent.get("n_empty", 0)) + 1
            ent["last_hash"] = h            # 次の比べ元は「0 件」(直前と同じかだけを見る)
        elif unchanged:
            info["same_as"] = ent.get("last_file")
            ent["n_unchanged"] = int(ent.get("n_unchanged", 0)) + 1
        else:
            extra_meta = {
                "datatype": dt, "scope": scope, "operator": op, "snapshot_jst": snap,
                "n_expired": n_expired, "expired_ids": expired_ids, "capped": any_capped,
                "n_parts": len(job["parts"]), "n_failed_parts": len(job["parts"]) - n_ok_parts,
                "content_sha256": h,
            }
            notes = ["dct:valid 超過は data から外し n_expired に件数を残した。"]
            if scope == "open":
                notes.append("オープン枠: 路線で絞らず全レコードを保存した。")
            else:
                notes.append("チャレンジ枠: 作品に使う範囲だけ(RAILWAYS のチャレンジの行)。")
            if job["railway_filter"] is not None:
                extra_meta["railway_filter"] = list(job["railway_filter"])
            if split_meta:
                extra_meta["split"] = split_meta
            if dt in ("odpt:Train", "odpt:Bus"):
                extra_meta["delay_summary"] = delay_summary(records)
            meta = common.build_meta(
                SOURCE, module="odpt_rt.py", urls=urls, n_records=len(records), n_missing=0,
                caveats=CAVEATS, notes=notes, extra=extra_meta)
            doc = {"_meta": meta, "data": records}
            path, n_raw, n_gz = common.write_json_gz(out_path(root, d, dt, scope, op, stamp), doc)
            docs.append(doc)
            info.update({"file": path.name, "bytes_raw": n_raw, "bytes_gz": n_gz})
            ent["last_hash"] = h
            ent["last_file"] = path.name
            ent["last_saved_date"] = d.isoformat()
            ent["n_saved"] = int(ent.get("n_saved", 0)) + 1
        ent["last_fetch_jst"] = snap
        ent["n_fetched"] = int(ent.get("n_fetched", 0)) + 1
        # 保存の情報は成功した行に付ける。バイト数は job の最初の成功行にだけ(足し上げで二重にしない)。
        first_ok = True
        for row in part_rows:
            if row.get("ok"):
                row.setdefault("extra", {}).update(
                    info if first_ok else {k: v for k, v in info.items()
                                           if k not in ("bytes_raw", "bytes_gz")})
                first_ok = False
        rows.extend(part_rows)


    for job in jobs(railways, open_operators):
        try:
            _one(job)
        except Exception as exc:        # 1 つの job の事故で他の job と状態ファイルを失わない
            rows.append(ledger.make_entry(
                SOURCE, f"{TYPE_TARGET[job['datatype']]}/{job['scope']}/{job['operator']}",
                ok=False, date_jst=d.isoformat(), error=f"{type(exc).__name__}: {exc}",
                extra={"scope": job["scope"], "datatype": job["datatype"],
                       "operator": job["operator"], "snapshot_jst": snap}))

    save_state(root, st, now)
    return docs, rows
