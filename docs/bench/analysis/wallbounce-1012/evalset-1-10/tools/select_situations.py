#!/usr/bin/env python
"""evalset-1-10 — 固定の評価セットの状況の選び(第 1 期 1-10・N-3 の前倒し・記録だけの道具)。

エンジンにも試験にも配線しない道具。実 LLM のテープ 53 本(10e の記録 §RET-1 の「手元の 53 本の実テープ」)から、
判断モデルの評価セットに使う「状況」(1 回の呼び出し=入力の文と出力の 2 行)を、**入力の側の軸**で層に分け、
固定の鍵で決定的に抜き取る。採点・比較はしない(第 6 期 6-1)。規則の本文は ``../README.md`` §2。

要点
- 層は入力の側だけで作る。出力の本文では選ばない(Q57「中身を誘導しない」)。
- 主の層 = 種別(B1)× 時間帯(B3 の時刻を 4 時間ごとに 6 帯)× 場所の種類(B2 と B4b)。主のセルごとに同じ数
  (既定 3)を取る。取る順は「1 巡目に全セルから 1 つずつ → 2 巡目 → …」。
- 副の層 = 起床の級(テープの ``wake_class``=繰り延べの昇格の後の実効クラス)。主のセルの中では、それまでに選んだ
  数が最も少ない級から取る。暑さ(B3 体感)は数えて記録するが選びには使わない(この材料では暑さが時刻だけで決まる
  =全テープが同じ天気の日の再生。暑さで均すと 08-11 の帯が 11 時に寄る。README §2-3)。
- 層の中の順は行ごとの鍵 ``derive_key(SEED, "evalset-1-10|<テープ>|<行>|<call_id>")[0]``(``shibuya.core.rng``)の
  昇順。主のセルを回す順も同じ鍵の関数(``evalset-1-10|cell|<種別>|<時間帯>|<場所>``)で決める。
- 同じ入力(``prompt_hash`` が同じ=B5・B6 まで同じ全文)は 1 回だけ取る。
- 母集団は既定で B0 が語彙 v1(12 語)のテープだけ(``--b0 all`` で全部)。B0 の違う腕(自由記述・ヒント・語彙 v2)は
  出力が別の問いへの答えなので、参照の出力として混ぜない(仮採用・README §7)。

読むもの: 下の ``TAPES`` の ``calls.parquet`` と ``blocks.parquet`` だけ。フォルダを探索しない(``data/realworld_live`` と
封印した層には触れない)。書くもの: ``--out`` の ``situations.jsonl`` と ``summary.json`` だけ。絶対パスは書かない。

逐次ループ宣言: 行ごとの鍵(blake3)を作る Python のループ 1 本(テープの行数ぶん・約 1,500 万行で数十秒)。
道具なので性能の予算は置かない。

使い方::

    python docs/bench/analysis/wallbounce-1012/evalset-1-10/tools/select_situations.py            # 既定
    python .../select_situations.py --out <別の場所>                                               # 再現の確認
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
EVALSET_DIR = HERE.parent
REPO = HERE.parents[5]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from shibuya.core.rng import derive_key  # noqa: E402

TOOL_VERSION = "evalset-1-10/1"
#: 抜き取りの鍵の master seed(``derive_key`` の第 1 引数)。変えると別のセットになる。
SEED = "evalset-1-10"
KEY_FMT = "evalset-1-10|{tape}|{row}|{call_id}"
CELL_KEY_FMT = "evalset-1-10|cell|{kind}|{tband}|{scene}"

#: 実 LLM のテープ 53 本(リポの根からの相対・``calls.parquet`` の置き場)。10e の記録 §RET-1 の定義
#: (``data/`` の下の ``calls.parquet`` で ``realworld_live`` を除き ``run_meta.json`` の無いもの)で 2026-10-14 に数えた一覧。
TAPES: tuple[str, ...] = (
    "data/server_retrieval/2026-09-16/c5/c8/c8_tapes/AB1-BUDGET-MODE__fixed_slots",
    "data/server_retrieval/2026-09-16/c5/c8/c8_tapes/AB1-BUDGET-MODE__single_ranking",
    "data/server_retrieval/2026-09-16/c5/c8/c8_tapes/AB6-AD-ZERO__signage_off",
    "data/server_retrieval/2026-09-16/c5/c8/c8_tapes/AB6-AD-ZERO__signage_on",
    "data/server_retrieval/2026-09-16/c5/c8_ab1s2/c8_tapes/AB1-BUDGET-MODE__fixed_slots",
    "data/server_retrieval/2026-09-16/c5/c8_ab1s2/c8_tapes/AB1-BUDGET-MODE__single_ranking",
    "data/server_retrieval/2026-09-16/c5/c8_s2/c8_tapes/AB6-AD-ZERO__signage_off",
    "data/server_retrieval/2026-09-16/c5/c8_s2/c8_tapes/AB6-AD-ZERO__signage_on",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-day-1",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-day-2",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-day-3",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-smoke-1",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-smoke-2",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-smoke-4",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-t6-a",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-t6-b",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-t7-s1",
    "data/server_retrieval/2026-09-16/v2_data/tape/c6-t7-s2",
    "data/server_retrieval/2026-09-16/v2_data/tape/c7-day-1",
    "data/server_retrieval/2026-09-16/v2_data/tape/c7-day-2",
    "data/server_retrieval/2026-09-16/v2_data/tape/c7-day-3",
    "data/server_retrieval/2026-09-16/v2_data/tape/c7-day-4",
    "data/server_retrieval/2026-09-17/tape/c7-day-4-s2",
    "data/server_retrieval/2026-09-17/tape/c7-day-4-s3",
    "data/server_retrieval/2026-09-17/tape/c9b-smoke-s1",
    "data/tape/c8_ab6b_s1/AB6b-AD-NOTICE__ad_zero",
    "data/tape/c8_ab6b_s1/AB6b-AD-NOTICE__p_see_0_14",
    "data/tape/c8_ab6b_s1/AB6b-AD-NOTICE__p_see_0_30",
    "data/tape/c8_ab6b_s1/AB6b-AD-NOTICE__p_see_1_00",
    "data/tape/c8_ab6b_s2/AB6b-AD-NOTICE__ad_zero",
    "data/tape/c8_ab6b_s2/AB6b-AD-NOTICE__p_see_0_14",
    "data/tape/c8_ab6b_s2/AB6b-AD-NOTICE__p_see_0_30",
    "data/tape/c8_ab6b_s2/AB6b-AD-NOTICE__p_see_1_00",
    "data/tape/c8_ab6c_s1/AB6c-AD-NOTICE-UNCAPPED__ad_zero",
    "data/tape/c8_ab6c_s1/AB6c-AD-NOTICE-UNCAPPED__p_see_0_14",
    "data/tape/c8_ab6c_s1/AB6c-AD-NOTICE-UNCAPPED__p_see_0_30",
    "data/tape/c8_ab6c_s1/AB6c-AD-NOTICE-UNCAPPED__p_see_1_00",
    "data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open",
    "data/tape/c8_ab7_s1/AB7-OPEN-INTENT__vocab",
    "data/tape/c8_ab7_s2/AB7-OPEN-INTENT__open",
    "data/tape/c8_ab7_s2/AB7-OPEN-INTENT__vocab",
    "data/tape/c8_ab7b_s1/AB7b-HINT-INTENT__hint",
    "data/tape/c8_ab7b_s1/AB7b-HINT-INTENT__vocab",
    "data/tape/c8_ab7c_s1/AB7c-VOCAB-V2__open_v2",
    "data/tape/c8_ab7c_s1/AB7c-VOCAB-V2__vocab_v1",
    "data/tape/c8_ab7c_s1/AB7c-VOCAB-V2__vocab_v2",
    "data/tape/c8_ab7c_s2/AB7c-VOCAB-V2__open_v2",
    "data/tape/c8_ab7c_s2/AB7c-VOCAB-V2__vocab_v1",
    "data/tape/c8_ab7c_s2/AB7c-VOCAB-V2__vocab_v2",
    "data/tape/c8_ab8_s1/AB8-L4-SCALE__l4_unlimited",
    "data/tape/c8_ab8_s1/AB8-L4-SCALE__l4_x0.5",
    "data/tape/c8_ab8_s1/AB8-L4-SCALE__l4_x1",
    "data/tape/c8_ab8_s1/AB8-L4-SCALE__l4_x2",
)
assert len(TAPES) == 53 and len(set(TAPES)) == 53

#: 保存されている共有ブロックの並び(版 1・版 2 のテープの ``block_ids`` は全行この 6 つ。B5・B6 は保存されていない)。
BLOCK_ORDER: tuple[str, ...] = ("B0", "B1", "B2", "B3", "B4", "B4b")

# ---- 軸の水準(テープの文の語そのまま。知らない語が出たら止める) ----
#: B1 の種別語(``perception.templates.KIND_WORDS`` の 5 語。表に無い種別=通学者・定期来街者・訪日来街者・乗務員は
#: 描画で「来街者」に落ちていた)。
KIND_LEVELS: tuple[str, ...] = ("居住者", "通勤者", "従業者", "来街者", "指令")
#: B3 の時刻(時)を 4 時間ごとに区切る(区切りは機械的=設計者の時間の見立てを入れない)。
TBAND_LEVELS: tuple[str, ...] = ("00-03", "04-07", "08-11", "12-15", "16-19", "20-23")
#: 場所の種類(B2 と B4b から。上から順に当てはめる)。README §2-2。
SCENE_LEVELS: tuple[str, ...] = ("駅", "店の行列", "店の見える街路", "その他の街路")
#: B3 体感の暑さの段(``perception.templates.HEAT_STAGE_WORDS``)。
HEAT_LEVELS: tuple[str, ...] = ("快適", "やや暑い", "暑い", "厳しい暑さ", "危険な暑さ")
#: テープの ``wake_class``(昇格の後の実効クラス=``core.types.EventClass`` の 0〜3)。
WAKE_LEVELS: tuple[str, ...] = ("0 会話+昇格", "1 計画境界", "2 個体", "3 セル")

N_KIND, N_TB, N_SC, N_HEAT, N_WAKE = (len(KIND_LEVELS), len(TBAND_LEVELS), len(SCENE_LEVELS),
                                       len(HEAT_LEVELS), len(WAKE_LEVELS))
N_PRIMARY = N_KIND * N_TB * N_SC
N_SUB = N_HEAT * N_WAKE
N_GROUP = N_PRIMARY * N_SUB

#: 場所の種類の手がかりの語(README §2-2・仮採用)。
STATION_WORDS: tuple[str, ...] = ("駅", "改札")
STATION_BANDS: tuple[str, ...] = ("地下", "デッキ")
SHOP_WORDS: tuple[str, ...] = ("店", "コンビニ", "飲食", "物販", "娯楽", "カフェ", "商業")

RE_KIND = re.compile(r"^\[B1 種別\] あなたは(.+?)です。$", re.M)
RE_PLACE = re.compile(r"^\[B2 場所\] 現在地はセル(\S+?)\((.+?)\)です。$", re.M)
RE_TIME = re.compile(r"^\[B3 時刻\] 現在時刻は(\d+)時(\d+)分です。$", re.M)
RE_WEATHER = re.compile(r"^\[B3 天候\] 天候は(.+?)、日照は(.+?)です。$", re.M)
RE_HEAT = re.compile(r"^\[B3 体感\] 暑さは(.+?)です。$", re.M)
RE_DENSITY = re.compile(r"^\[B4 密度\] 歩行者密度は段階([A-F])です。", re.M)
RE_NOISE = re.compile(r"^\[B4 騒音\] 環境騒音は(.+?)\(", re.M)
#: 出力の行動語(記述の集計だけに使う。選びには使わない)。
RE_ACTION = re.compile(r"行動[::]\s*(\S+)")

CALL_COLS: tuple[str, ...] = ("call_id", "agent_id", "tick", "wake_class", "prompt_hash", "block_ids",
                              "params_hash", "response", "tokens_in", "tokens_out")


def _line(text: str, prefix: str) -> str:
    for ln in text.splitlines():
        if ln.startswith(prefix):
            return ln
    return ""


def block_tag(text: str) -> str:
    """共有ブロックの名(本文の頭の印から)。"""
    for tag in ("B1", "B2", "B3", "B4b", "B4", "B5", "B6"):
        if text.startswith(f"[{tag} "):
            return tag
    return "B0" if not text.startswith("[") else "?"


def b0_variant(text: str) -> str:
    """B0 の出力規約の「行動」欄から版を読む(v1=12 語・v2=食事つき 13 語・open=自由記述・hint=12 語+自由記述)。"""
    line = _line(text, "行動: <")
    if "選ぶのが基本" in line:
        return "hint"
    if "10字以内の動詞句で" in line:
        return "open"
    if "/ 食事 から1語" in line:
        return "v2"
    if "/ 就寝 から1語" in line:
        return "v1"
    return "other"


def scene_of(b2: str, b4b: str) -> tuple[int, dict[str, Any]]:
    """場所の種類(上から順に当てはめる): 駅 > 店の行列 > 店の見える街路 > その他の街路。"""
    m = RE_PLACE.search(b2)
    if not m:
        raise ValueError(f"B2 に場所の行が無い: {b2[:80]!r}")
    place_id, band = m.group(1), m.group(2)
    vis = _line(b2, "[B2 可視]")
    lm = _line(b2, "[B2 地物]")
    station = band in STATION_BANDS or any(w in vis or w in lm for w in STATION_WORDS)
    queue = "行列に" in b4b
    vis_wo_front = vis.replace("店頭", "")  # 「<施設>の店頭」は施設の種類によらない定型の語=店の手がかりにしない
    shop = any(w in vis_wo_front for w in SHOP_WORDS)
    code = 0 if station else (1 if queue else (2 if shop else 3))
    return code, {"place_id": place_id, "band": band, "station_word": station, "queue": queue, "shop_word": shop}


class TapeBlocks:
    """1 本のテープの共有ブロック表と、ブロックごとの軸の値。"""

    def __init__(self, blocks: pa.Table) -> None:
        self.ids = blocks.column("block_id")
        self.texts: list[str] = blocks.column("text").to_pylist()
        n = len(self.texts)
        self.tags = [block_tag(t) for t in self.texts]
        self.tag_code = np.array([BLOCK_ORDER.index(t) if t in BLOCK_ORDER else -1 for t in self.tags], dtype=np.int8)
        self.kind = np.full(n, -1, dtype=np.int16)
        self.hour = np.full(n, -1, dtype=np.int16)
        self.heat = np.full(n, -1, dtype=np.int16)
        self.b2_scene_station = np.zeros(n, dtype=bool)
        self.b2_shop = np.zeros(n, dtype=bool)
        self.b4b_queue = np.zeros(n, dtype=bool)
        self.b0_variant: dict[int, str] = {}
        for i, (t, tag) in enumerate(zip(self.texts, self.tags)):
            if tag == "B0":
                self.b0_variant[i] = b0_variant(t)
            elif tag == "B1":
                m = RE_KIND.search(t)
                if not m or m.group(1) not in KIND_LEVELS:
                    raise ValueError(f"知らない種別: {t!r}")
                self.kind[i] = KIND_LEVELS.index(m.group(1))
            elif tag == "B2":
                _, f = scene_of(t, "")
                self.b2_scene_station[i] = f["station_word"]
                self.b2_shop[i] = f["shop_word"]
            elif tag == "B3":
                m = RE_TIME.search(t)
                h = RE_HEAT.search(t)
                if not m or not h or h.group(1) not in HEAT_LEVELS:
                    raise ValueError(f"B3 が読めない: {t!r}")
                self.hour[i] = int(m.group(1))
                self.heat[i] = HEAT_LEVELS.index(h.group(1))
            elif tag == "B4b":
                self.b4b_queue[i] = "行列に" in t


def _file_md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def _topk_per_group(group: np.ndarray, key: np.ndarray, k: int) -> np.ndarray:
    """群ごとに鍵の小さい順に k 個までの添字(入力の並びの添字)。"""
    if group.size == 0:
        return np.zeros(0, dtype=np.int64)
    order = np.lexsort((key, group))
    g = group[order]
    first = np.ones(g.size, dtype=bool)
    first[1:] = g[1:] != g[:-1]
    start = np.maximum.accumulate(np.where(first, np.arange(g.size), 0))
    rank = np.arange(g.size) - start
    return order[rank < k]


def scan_tape(tape: str, k: int, b0_pool: str) -> tuple[dict[str, Any], list[dict[str, Any]], np.ndarray]:
    """1 本のテープを読み、(テープの記録・候補の行・群ごとの母集団の行数)を返す。"""
    d = REPO / tape
    calls_p, blocks_p = d / "calls.parquet", d / "blocks.parquet"
    rec: dict[str, Any] = {"tape": tape, "bytes_calls": calls_p.stat().st_size,
                           "md5_calls": _file_md5(calls_p),
                           "md5_blocks": _file_md5(blocks_p) if blocks_p.exists() else None}
    counts = np.zeros(N_GROUP, dtype=np.int64)
    try:
        pf = pq.ParquetFile(calls_p)
    except Exception as e:  # noqa: BLE001 — 壊れたテープは記録して飛ばす
        rec.update(readable=False, reason=f"{type(e).__name__}: {str(e)[:120]}", in_pool=False)
        return rec, [], counts
    md = pf.schema_arrow.metadata or {}
    schema = (md.get(b"shibuya.tape.schema") or b"").decode() or "shibuya.tape/1(印なし)"
    names = pf.schema_arrow.names
    has_def = "deferred" in names
    tb = TapeBlocks(pq.read_table(blocks_p))
    variants = sorted(set(tb.b0_variant.values()))
    rec.update(readable=True, schema=schema, ncols=len(names), rows=pf.metadata.num_rows, b0_variants=variants)
    in_pool = (b0_pool == "all") or (variants == [b0_pool])
    rec["in_pool"] = in_pool
    if not in_pool:
        rec["reason"] = f"B0 の版が {variants}(母集団は {b0_pool})"
        return rec, [], counts
    cols = list(CALL_COLS) + (["deferred"] if has_def else [])
    cands: list[dict[str, Any]] = []
    offset = 0
    n_elig = 0
    n_deferred = 0
    for batch in pf.iter_batches(batch_size=1 << 18, columns=cols):
        n = batch.num_rows
        bl = batch.column("block_ids")
        lens = pc.list_value_length(bl).to_numpy(zero_copy_only=False)
        if not np.all(lens == len(BLOCK_ORDER)):
            raise ValueError(f"{tape}: block_ids の長さが {len(BLOCK_ORDER)} でない行がある")
        idx_arr = pc.index_in(pc.list_flatten(bl), value_set=tb.ids)
        if idx_arr.null_count:
            raise ValueError(f"{tape}: ブロック表に無い block_id がある")
        idx = idx_arr.to_numpy(zero_copy_only=False).astype(np.int64).reshape(n, len(BLOCK_ORDER))
        if not np.all(tb.tag_code[idx] == np.arange(len(BLOCK_ORDER), dtype=np.int8)):
            raise ValueError(f"{tape}: block_ids の並びが {BLOCK_ORDER} でない行がある")
        elig = pc.greater(pc.utf8_length(batch.column("response")), 0).to_numpy(zero_copy_only=False)
        if has_def:
            dfr = batch.column("deferred").to_numpy(zero_copy_only=False)
            n_deferred += int((dfr != 0).sum())
            elig &= dfr == 0
        wake = batch.column("wake_class").to_numpy(zero_copy_only=False).astype(np.int64)
        if np.any((wake < 0) | (wake >= N_WAKE)):
            raise ValueError(f"{tape}: wake_class が 0〜3 の外")
        kind = tb.kind[idx[:, 1]].astype(np.int64)
        hour = tb.hour[idx[:, 3]].astype(np.int64)
        heat = tb.heat[idx[:, 3]].astype(np.int64)
        station = tb.b2_scene_station[idx[:, 2]]
        queue = tb.b4b_queue[idx[:, 5]]
        shop = tb.b2_shop[idx[:, 2]]
        scene = np.where(station, 0, np.where(queue, 1, np.where(shop, 2, 3))).astype(np.int64)
        tband = hour // 4
        primary = (kind * N_TB + tband) * N_SC + scene
        group = primary * N_SUB + heat * N_WAKE + wake
        el = np.nonzero(elig)[0]
        n_elig += el.size
        counts += np.bincount(group[el], minlength=N_GROUP)
        call_ids = batch.column("call_id").to_pylist()
        keys = np.fromiter(
            (derive_key(SEED, KEY_FMT.format(tape=tape, row=offset + int(i), call_id=call_ids[i]))[0] for i in el),
            dtype=np.uint64, count=el.size,
        )
        top = el[_topk_per_group(group[el], keys, k)]
        top_keys = keys[np.searchsorted(el, top)]
        sub = batch.take(pa.array(top, type=pa.int64())).drop_columns(["block_ids"]).to_pylist()
        for j, r in enumerate(sub):
            i = int(top[j])
            r.pop("deferred", None)
            r.update(tape=tape, schema=schema, row=offset + i, key=int(top_keys[j]), group=int(group[i]),
                     blocks=[tb.texts[int(b)] for b in idx[i]])
            cands.append(r)
        offset += n
    rec.update(eligible_rows=n_elig, deferred_rows=n_deferred)
    # テープの中で群ごとに k 個へ
    cands.sort(key=lambda r: (r["group"], r["key"]))
    kept: list[dict[str, Any]] = []
    per: collections.Counter[int] = collections.Counter()
    for r in cands:
        if per[r["group"]] < k:
            kept.append(r)
            per[r["group"]] += 1
    return rec, kept, counts


def decode_group(g: int) -> tuple[int, int, int, int, int]:
    primary, sub = divmod(g, N_SUB)
    heat, wake = divmod(sub, N_WAKE)
    ks, scene = divmod(primary, N_SC)
    kind, tband = divmod(ks, N_TB)
    return kind, tband, scene, heat, wake


def select(cands: list[dict[str, Any]], per_cell: int, k: int) -> list[dict[str, Any]]:
    """主のセルを鍵の順に回し、1 巡ごとに各セルから 1 つ取る。セルの中は起床の級の数が少ないものから。"""
    # 全テープを通して群ごとに k 個(同じ prompt_hash は鍵の最も小さい 1 つだけ)
    cands = sorted(cands, key=lambda r: (r["group"], r["key"]))
    # by_cell[主のセル][起床の級] = 鍵の昇順の候補。暑さは群の数え方にだけ使い、選びでは分けない
    # (この材料では暑さが時刻で決まる=全テープが同じ天気の日の再生。README §2-3)。
    by_cell: dict[int, dict[int, list[dict[str, Any]]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    seen_in_group: dict[int, set[str]] = collections.defaultdict(set)
    for r in cands:
        g = r["group"]
        if r["prompt_hash"] in seen_in_group[g] or len(seen_in_group[g]) >= k:
            continue
        seen_in_group[g].add(r["prompt_hash"])
        primary, sub = divmod(g, N_SUB)
        _, wake = divmod(sub, N_WAKE)
        by_cell[primary][wake].append(r)
    for subs in by_cell.values():
        for rows in subs.values():
            rows.sort(key=lambda r: r["key"])
    cell_order = sorted(
        by_cell,
        key=lambda p: derive_key(SEED, CELL_KEY_FMT.format(
            kind=KIND_LEVELS[decode_group(p * N_SUB)[0]], tband=TBAND_LEVELS[decode_group(p * N_SUB)[1]],
            scene=SCENE_LEVELS[decode_group(p * N_SUB)[2]]))[0],
    )
    cnt_wake = np.zeros(N_WAKE, dtype=np.int64)
    chosen: list[dict[str, Any]] = []
    chosen_ph: set[str] = set()
    pos: dict[tuple[int, int], int] = collections.defaultdict(int)
    for rnd in range(per_cell):
        for p in cell_order:
            best: tuple[int, int, int] | None = None
            best_r = None
            for wake, rows in by_cell[p].items():
                while pos[(p, wake)] < len(rows) and rows[pos[(p, wake)]]["prompt_hash"] in chosen_ph:
                    pos[(p, wake)] += 1
                if pos[(p, wake)] >= len(rows):
                    continue
                r = rows[pos[(p, wake)]]
                score = (int(cnt_wake[wake]), r["key"], wake)
                if best is None or score < best:
                    best, best_r = score, r
            if best is None or best_r is None:
                continue
            wake = best[2]
            pos[(p, wake)] += 1
            cnt_wake[wake] += 1
            chosen_ph.add(best_r["prompt_hash"])
            best_r["round"] = rnd + 1
            chosen.append(best_r)
    return chosen


def same_prompt_scan(pool_tapes: list[str], hashes: set[str]) -> dict[str, dict[str, Any]]:
    """選んだ入力と同じ prompt_hash の行を母集団の全テープから数える(同じ入力の再実行のぶれの材料)。"""
    acc: dict[str, dict[str, Any]] = {h: {"rows": 0, "tapes": set(), "outputs": set()} for h in hashes}
    vs = pa.array(sorted(hashes))
    for tape in pool_tapes:
        pf = pq.ParquetFile(REPO / tape / "calls.parquet")
        names = pf.schema_arrow.names
        cols = ["prompt_hash", "response"] + (["deferred"] if "deferred" in names else [])
        for batch in pf.iter_batches(batch_size=1 << 18, columns=cols):
            m = pc.is_in(batch.column("prompt_hash"), value_set=vs)
            if not pc.any(m).as_py():
                continue
            sub = batch.filter(m).to_pylist()
            for r in sub:
                if r.get("deferred", 0) or not r["response"]:
                    continue
                a = acc[r["prompt_hash"]]
                a["rows"] += 1
                a["tapes"].add(tape)
                a["outputs"].add(r["response"])
    return {h: {"rows": a["rows"], "tapes": len(a["tapes"]), "distinct_outputs": len(a["outputs"])} for h, a in acc.items()}


def facts_of(blocks: list[str]) -> dict[str, Any]:
    b2, b3, b4, b4b = blocks[2], blocks[3], blocks[4], blocks[5]
    _, f = scene_of(b2, b4b)
    t = RE_TIME.search(b3)
    w = RE_WEATHER.search(b3)
    dn = RE_DENSITY.search(b4)
    nz = RE_NOISE.search(b4)
    return {
        "hour": int(t.group(1)), "minute": int(t.group(2)),
        "place_id": f["place_id"], "band": f["band"],
        "weather": w.group(1) if w else None, "daylight": w.group(2) if w else None,
        "density": dn.group(1) if dn else None, "noise": nz.group(1) if nz else None,
        "salient_event": "目につく出来事: " in b4,
        "queue_within_25m": f["queue"], "station_word_or_band": f["station_word"], "shop_word": f["shop_word"],
    }


def tape_step(tape: str) -> str:
    name = tape.rsplit("/", 1)[-1]
    if name.startswith("c6-"):
        return "C6"
    if name.startswith("c7-"):
        return "C7"
    if name.startswith("c9b-"):
        return "C9b"
    return "C8"


def axis_counts(counts: np.ndarray) -> dict[str, dict[str, int]]:
    c = counts.reshape(N_KIND, N_TB, N_SC, N_HEAT, N_WAKE)
    return {
        "kind": {lv: int(c[i].sum()) for i, lv in enumerate(KIND_LEVELS)},
        "time_band": {lv: int(c[:, i].sum()) for i, lv in enumerate(TBAND_LEVELS)},
        "scene": {lv: int(c[:, :, i].sum()) for i, lv in enumerate(SCENE_LEVELS)},
        "heat": {lv: int(c[:, :, :, i].sum()) for i, lv in enumerate(HEAT_LEVELS)},
        "wake": {lv: int(c[:, :, :, :, i].sum()) for i, lv in enumerate(WAKE_LEVELS)},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=EVALSET_DIR, help="situations.jsonl と summary.json の置き場")
    ap.add_argument("--per-cell", type=int, default=3, help="主のセルあたりの状況の数(既定 3)")
    ap.add_argument("--k", type=int, default=8, help="群ごとに持つ候補の数(重複を除く余裕・既定 8)")
    ap.add_argument("--b0", choices=("v1", "all"), default="v1", help="母集団にする B0 の版(既定 v1)")
    args = ap.parse_args(argv)
    if args.k < args.per_cell:
        ap.error("--k は --per-cell 以上")

    tape_recs: list[dict[str, Any]] = []
    all_cands: list[dict[str, Any]] = []
    pool_counts = np.zeros(N_GROUP, dtype=np.int64)
    b0_texts: dict[str, str] = {}
    for tape in TAPES:
        rec, cands, counts = scan_tape(tape, args.k, args.b0)
        rec["step"] = tape_step(tape)
        tape_recs.append(rec)
        all_cands.extend(cands)
        pool_counts += counts
        for r in cands:
            b0 = r["blocks"][0]
            bid = f"{b0_variant(b0)}-{hashlib.md5(b0.encode('utf-8')).hexdigest()[:12]}"
            b0_texts.setdefault(bid, b0)
            r["b0_id"] = bid
        print(f"[scan] {tape}: readable={rec.get('readable')} in_pool={rec.get('in_pool')} "
              f"eligible={rec.get('eligible_rows', 0)} cands={len(cands)}", flush=True)

    chosen = select(all_cands, args.per_cell, args.k)
    chosen.sort(key=lambda r: r["key"])
    pool_tapes = [r["tape"] for r in tape_recs if r.get("in_pool")]
    dup = same_prompt_scan(pool_tapes, {r["prompt_hash"] for r in chosen})

    sel_counts = np.zeros(N_GROUP, dtype=np.int64)
    by_tape: collections.Counter[str] = collections.Counter()
    out_lines: list[str] = []
    for n, r in enumerate(chosen, start=1):
        kind, tband, scene, heat, wake = decode_group(r["group"])
        sel_counts[r["group"]] += 1
        by_tape[r["tape"]] += 1
        resp = r["response"]
        row = {
            "sid": f"e110-{n:04d}",
            "key": f"{r['key']:016x}",
            "round": r["round"],
            "tape": r["tape"], "tape_step": tape_step(r["tape"]), "tape_schema": r["schema"],
            "row": r["row"], "call_id": r["call_id"], "agent_id": r["agent_id"], "tick": r["tick"],
            "wake_class": r["wake_class"], "prompt_hash": r["prompt_hash"], "params_hash": r["params_hash"],
            "strata": {"kind": KIND_LEVELS[kind], "time_band": TBAND_LEVELS[tband], "scene": SCENE_LEVELS[scene],
                       "heat": HEAT_LEVELS[heat], "wake": WAKE_LEVELS[wake]},
            "body": {"heat": HEAT_LEVELS[heat], "hunger": None, "fatigue": None},
            "judgment_kind": "行動の選び(2 行形)",
            "lang": "ja",
            "vocab": r["b0_id"].split("-", 1)[0],
            "facts": facts_of(r["blocks"]),
            "b0_id": r["b0_id"],
            "input_text": "\n".join(r["blocks"][1:]),
            "input_missing": ["B5", "B6"],
            "output": resp,
            "output_lines": len([ln for ln in resp.splitlines() if ln.strip()]),
            "tokens_in": r["tokens_in"], "tokens_out": r["tokens_out"],
            "same_prompt": dup[r["prompt_hash"]],
        }
        out_lines.append(json.dumps(row, ensure_ascii=False))
    for rec in tape_recs:
        rec["selected"] = int(by_tape.get(rec["tape"], 0))

    args.out.mkdir(parents=True, exist_ok=True)
    jl = args.out / "situations.jsonl"
    data = ("\n".join(out_lines) + "\n").encode("utf-8")
    jl.write_bytes(data)

    prim_pool = pool_counts.reshape(N_PRIMARY, N_SUB).sum(axis=1)
    prim_sel = sel_counts.reshape(N_PRIMARY, N_SUB).sum(axis=1)

    def cell_name(p: int) -> str:
        kind, tband, scene, _, _ = decode_group(p * N_SUB)
        return f"{KIND_LEVELS[kind]}|{TBAND_LEVELS[tband]}|{SCENE_LEVELS[scene]}"

    pool_axes = axis_counts(pool_counts)
    summary = {
        "tool": TOOL_VERSION,
        "seed": SEED, "key_format": KEY_FMT, "cell_order_key_format": CELL_KEY_FMT,
        "key_function": "shibuya.core.rng.derive_key(seed, domain)[0](uint64・昇順)",
        "per_cell": args.per_cell, "k_candidates": args.k, "b0_pool": args.b0,
        "balance": {"primary": ["kind", "time_band", "scene"], "secondary": ["wake"], "recorded_only": ["heat"]},
        "levels": {"kind": list(KIND_LEVELS), "time_band": list(TBAND_LEVELS), "scene": list(SCENE_LEVELS),
                   "heat": list(HEAT_LEVELS), "wake": list(WAKE_LEVELS)},
        "scene_rule": {"order": list(SCENE_LEVELS), "station_words": list(STATION_WORDS),
                       "station_bands": list(STATION_BANDS), "queue_word": "行列に",
                       "shop_words": list(SHOP_WORDS), "shop_words_exclude": "店頭"},
        "tapes": tape_recs,
        "pool": {
            "rows": int(pool_counts.sum()),
            "by_axis": pool_axes,
            "empty_levels": {ax: [lv for lv, c in d.items() if c == 0] for ax, d in pool_axes.items()},
            "primary_cells": {cell_name(p): int(prim_pool[p]) for p in range(N_PRIMARY)},
            "time_band_x_heat": {
                TBAND_LEVELS[t]: {HEAT_LEVELS[h]: int(pool_counts.reshape(N_KIND, N_TB, N_SC, N_HEAT, N_WAKE)[:, t, :, h].sum())
                                  for h in range(N_HEAT)} for t in range(N_TB)},
        },
        "selected": {
            "n": len(chosen),
            "by_axis": axis_counts(sel_counts),
            "by_tape": dict(sorted(by_tape.items())),
            "by_step": dict(collections.Counter(tape_step(r["tape"]) for r in chosen)),
            "primary_cells": {cell_name(p): int(prim_sel[p]) for p in range(N_PRIMARY)},
            "empty_primary_cells": [cell_name(p) for p in range(N_PRIMARY) if prim_pool[p] == 0],
            "short_primary_cells": [cell_name(p) for p in range(N_PRIMARY)
                                    if 0 < prim_sel[p] < args.per_cell or (prim_pool[p] > 0 and prim_sel[p] == 0)],
            "same_prompt_rows_gt1": sum(1 for r in chosen if dup[r["prompt_hash"]]["rows"] > 1),
            "same_prompt_distinct_outputs_gt1": sum(1 for r in chosen if dup[r["prompt_hash"]]["distinct_outputs"] > 1),
            # 記述だけ(選びの後に数える・選びには使っていない): 出力の「行動:」の後の最初の語
            "output_action_words": dict(collections.Counter(
                (m.group(1) if (m := RE_ACTION.search(r["response"])) else "(読めない)") for r in chosen).most_common()),
        },
        "b0_texts": b0_texts,
        "output": {"situations.jsonl": {"lines": len(out_lines), "bytes": len(data),
                                        "md5": hashlib.md5(data).hexdigest()}},
    }
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n",
                                           encoding="utf-8", newline="\n")
    print(f"[done] situations={len(chosen)} bytes={len(data)} md5={hashlib.md5(data).hexdigest()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
