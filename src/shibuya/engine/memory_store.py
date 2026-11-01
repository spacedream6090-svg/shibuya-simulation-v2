"""engine.memory_store — 記憶の器 M0(第 1 期 1-6・MR-0・MR11 (b)・MR16)。

口の約束: ``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-6 記憶の器 M0」。置き場は口の約束の
``engine/memory/store.py`` でなく 1 本のモジュール ``engine/memory_store.py``(親の判断=今の ``engine/memory.py`` を
package にせず、import-linter と setuptools の検査の中に置く)。計画 1-6=M0 は**器と出どころだけ**
(強さの秒化・容量の廃止・表の統合は M1 の腕)。決定 10-12 §4-6 MR-0・MR11 (b)・MR16・回答 10-13b §3(テープの列は版 4 の
中で足してよい)。

記憶の行(体ごとに ``n_rows`` 行の範囲 ``[体 × n_rows, (体 + 1) × n_rows)``=SoA の列)
    - ``event_id``(目印): 出来事の id ``(t_ns, seq)``(1-3 の ``EventId``)。同じ鍵の出来事が重なった行は**最後の出来事**を
      指す(今の表の ``mem_last``・``mem_cell`` と同じ「最後の回」)。
    - ``strength``(System 1 の数=MR-0・LLM には見せない): 回数 ``n``・重要度 ``importance``・最初に書かれた時刻
      ``first_ns``。想起の強さ A はこれと「いま」から System 1 が計算する(M0 は今の式=``engine.memory.activation_rows``・
      刻みの単位の近似 #56。秒化は M1)。
    - ``annotation``(一人ずつの注釈): 会話の要旨(今の ``MemoryLayer.gist`` と同じ 40 字・体あたり 16 件・古い順に落とす)。
    - ``origin``(出どころの欄=範囲の外からの印): ``None``=出来事の記録(1-3)にある出来事への目印 / ``"legacy"``=記録に
      無い出来事の**仮の行**。〔第 2 期 2-3〕腕のランでは記憶の書き手が体の出来事を記録に書き(``engine.events.body``)、
      器の目印はその出来事(``None``)になる。``legacy`` は記録の無い器(``--events off``)と、器だけを使う試験の道に残る。
    - ``shown``(録画=MR16): 最後に LLM に見せた時刻 ``t_ns``(−1=まだ見せていない)。この呼び出しで見せたか=
      ``shown_ns`` がその呼び出しの時刻と同じか。
    仮の出来事の表(``_lg_*``): 記録に無い出来事の中身(種類・相手・対象・結果・セル)。行と同じ番地 k に置き、目印は
    ``(t_ns, −1 − k)``(seq が負=記録の外の仮の id。記録の id の seq は 0 以上なので重ならない)。〔第 2 期 2-3〕記録の
    目印の行(``None``)もこの表に中身の写しを持つ(想起は配列で中身を引く・記録は保持窓 7 日で行を落とし再開では空から=
    中身を記録だけに置くと想起が引けない)。中身の写しが記録の行と合うこと(``who``=体・``what``=種類)は覚えるときに
    確かめる(:meth:`MemoryStore.remember`)。
    〔第 2 期 2-3〕記録の目印の seq(``_ms_log_seq``・−1=仮の行): 状態台帳の腕の行 ``M0L``(軸 1 no・軸 2 required=腕の
    ランだけ状態のファイルと full-hash の末尾)。再開では作り直し(:meth:`MemoryStore.rebuild`)がこの列から目印を戻す
    (前の日の出来事は再開のランの記録に無い=記録は discardable・目印は残る=宣言・記録 md23/README.md)。

書く口は 2 つ: :meth:`MemoryStore.remember`(出来事を覚える=同じ鍵は重ねる・空の行・満杯なら score 最小を追い出す=
今の表 ``engine.memory`` と同じ規則・〔2-3〕目印は記録にある出来事の id だけ=無い id は ``ValueError``)と
:meth:`MemoryStore.mark_shown`(録画)。ほかに再開のときの作り直し
:meth:`MemoryStore.rebuild`(系の外だけ・行 M0 の欄だけ)(記憶の表から作り直す=状態台帳の行 M0 は「作り直せる」)と、テープの列へ渡す控えの取り出し
:meth:`MemoryStore.take_shown`。欄の付け替えは ``__setattr__`` が落とす(配列の中身の書き換えは口の中だけ=約束)。

読み口 :meth:`MemoryStore.recall` は ``MemoryView`` の組を返す。``MemoryView`` は LLM に見せる形=言葉(はっきり/うろ覚え
=強さの段)と中身の粗さ(MR-0)と中身の ID(描き方が語にする)だけで、強さの数を持たない。:func:`render_memories` は
``MemoryView`` を今の描き方(B5「記憶」の 1 行・テンプレ v1.3)と同じバイトの文にする(1-2 の ``Percept`` への結線は
1-2 の取り込みの後)。

腕(切替口): ``--memory-store events``(環境変数 ``SHIBUYA_MEMORY_STORE``・:func:`set_arm`)。既定 ``mem``=今の表だけ
(器を作らない=final・テープ不変)。``events`` で ``--memory on`` のランに器を作り、今の表に書く所で同じ出来事を器にも
書き、想起を器から引く(候補は今の表の想起と同じ=同値の試験)。テープに列 ``recalled_event_ids`` を 1 つ足す(版 4 の
中)。器は結果を変えないので設定の指紋には入れない(出来事の記録の切替口と同じ扱い)。腕の名は manifest
``memory_summary.memory_store.arm`` に出る。

先例(形だけ借りた): AI Town ``convex/aiTown/agentDescription.ts`` ほかの ``memoryFields``(MIT・共有の会話を
``conversationId`` で指し、本人視点の要約・重要度・最後に引いた時刻を持つ)。R-113 の 1-6 の節。コードは写していない。

**未リサーチ(expedient)**: 言葉の段の境目(A ≥ τ を「はっきり」=想起の閾値と同じ)・中身の粗さの段(M0 は「そのまま」
だけ)・仮の出来事の表の形・テープの列の値の形(``"t_ns:seq"`` の文字列)。

〔第 6 期 6-5・全部 腕〕器の子の持ち主と設定(:meth:`MemoryStore.enable_arms`=組み立てで 1 回・既定は置かない=今の器のまま):
``m1``=M1 の強さ(``engine.memory_m1.M1State``=ACT-R の折衷形・秒・想起の候補と順と言葉)・``cue``=意味の手がかり
(``engine.memory_embed.CueState``)・``uncapped``=人も記憶の一つ(人の行=種類 ``memory_m1.PERSON_KIND``・出来事の上限を外す・
忘れる=消す・満杯なら幅を倍に=器は記憶の表の写しでない)・``grain``=体の出来事の粒度(day=同じ記憶の行は日に 1 行だけ記録へ=
``remember(keep_pointer=)``)。記録 ``docs/bench/analysis/wallbounce-1012/mr65/README.md``。
〔検収 M2〕上限なしの腕の幅は種類ごとの上限(:data:`ROW_CAPS_DEFAULT`=出来事・人・店の各 256 行/体=expedient)の和まで。
その種類の行が上限に届いた体は思い浮かぶ強さ A の一番低い行を消す(「忘れた=見覚えも無い」で消す規則は前のまま)。
〔検収 M4〕店の評価の行は器の子の持ち主 ``shops``(``engine.memory_shops.ShopTable``・状態台帳の腕の行 ``M0S``)=上限 32 の
固定の表 ``sm_*`` を外す道(同じ作り=幅を倍に・上限で A の一番低い行を消す)。

逐次ループ宣言(P4): ``remember`` は配列演算(1 回の呼びで 1 体 1 件・追い出した行の注釈を落とすのは追い出しの件数ぶん)。
``recall`` は 1 体の ``n_rows`` 行の配列演算と、ほかの表の候補がある(7c)ときの k 件で止まる走査(≤ n_rows+店の行)。
``mark_shown`` は見せた行の数ぶん(≤ 3)。``rebuild`` は注釈の件数ぶん(再開のときに 1 回)。``summary`` は配列演算。
〔6-5〕上限なしの腕の幅を倍にする口(``_resize``)は注釈の件数ぶん(広げる回=log2)・消す口は消した行の数ぶん。
"""

from __future__ import annotations

import fnmatch
import functools
import os
from collections import Counter, OrderedDict
from datetime import datetime
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping, NamedTuple, Sequence

import numpy as np

from shibuya.core.time_consts import NS_PER_SECOND, NS_PER_STEP
from shibuya.engine import memory_m1 as _M1
from shibuya.engine.events import body as _BODY
from shibuya.engine.events import vocab as _VOCAB
from shibuya.engine.events.log import NS_PER_DAY, RETENTION_DAYS, EventId
from shibuya.engine.familiarity import place_thing
from shibuya.engine.memory import (
    EVENT_KINDS,
    GIST_PER_AGENT,
    IMPORTANCE,
    IMPORTANCE_MAX,
    KIND_NAMES,
    MEMORY_D,
    MEMORY_W_I,
    MEMORY_W_R,
    RECALL_TAU,
    STORE_ITEM_KIND,
    RecallItem,
    activation_rows,
)
from shibuya.engine.systems import guard as _G

__all__ = [
    "ARM_MEM",
    "ARM_EVENTS",
    "ARMS",
    "arm",
    "set_arm",
    "ORIGIN_LEGACY",
    "ORIGINS",
    "CLARITY_WORDS",
    "GRAIN_WORDS",
    "TAPE_COLUMN",
    "ROW_BYTES",
    "LEGACY_BYTES",
    "ROW_PATH",
    "SHOWN_PATH",
    "Cue",
    "LegacyEvent",
    "LoggedEvent",
    "LOG_SEQ_PATH",
    "LOG_SEQ_BYTES",
    "M1_PATH",
    "CUE_PATH",
    "SHOP_PATH",
    "ROW_CAPS_DEFAULT",
    "set_row_caps",
    "row_caps",
    "set_rows0",
    "rows0",
    "MemoryView",
    "ShopPool",
    "RecallReport",
    "MemoryStore",
    "clarity_of",
    "event_id_text",
    "to_item",
    "render_memories",
]

# ================================================================ 腕(切替口)
#: 既定=今の記憶の表(``mem_*``)だけ。
ARM_MEM: Final[str] = "mem"
#: 記憶の器(出来事の記録への目印)を作って想起を器から引く腕。
ARM_EVENTS: Final[str] = "events"
ARMS: Final[tuple[str, ...]] = (ARM_MEM, ARM_EVENTS)
_ARM: str = os.environ.get("SHIBUYA_MEMORY_STORE", ARM_MEM).strip().lower() or ARM_MEM
if _ARM not in ARMS:
    raise ValueError(f"SHIBUYA_MEMORY_STORE は {ARMS} のどれか(いま {_ARM!r})")


def arm() -> str:
    """いまの腕(``mem``=既定・``events``=記憶の器)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--memory-store``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--memory-store は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


# ================================================================ 閉じた表
#: 出どころの欄の値(閉じた表・列には番号)。``None``=出来事の記録にある出来事。``"legacy"``=記録に無い出来事の仮の行。
ORIGIN_LEGACY: Final[str] = "legacy"
ORIGINS: Final[tuple[str | None, ...]] = (None, ORIGIN_LEGACY)
_ORIGIN_NAMES: Final[tuple[str, ...]] = ("log", ORIGIN_LEGACY)  # manifest の鍵(None は "log")
_EMPTY_ORIGIN: Final[int] = -1
_LEGACY_CODE: Final[int] = 1
#: 〔2-3〕出どころ None(記録の出来事への目印)の番号。
_LOG_CODE: Final[int] = 0
#: 言葉(強さの段・MR-0)。M0 の境目は想起の閾値 τ(A ≥ τ=はっきり)=expedient。M0 の想起は A ≥ τ の行だけを返す。
CLARITY_WORDS: Final[tuple[str, ...]] = ("はっきり", "うろ覚え")
#: 中身の粗さ(MR-0)。M0 は「そのまま」だけ(粗くする段と描き方は M1 以降)。〔第 2 期 2-3・親の判断 M3〕「要旨だけ」=目印の先
#: (記録の出来事)が記録の保持窓の外に出た行=本文(中身)が無く、要旨(注釈)と強さ(言葉)だけで想起に使う。
GRAIN_WORDS: Final[tuple[str, ...]] = ("そのまま", "要旨だけ")
#: テープの列(録画 MR16・腕 on のランだけ calls.parquet の末尾に足す=版 4 の中)。``recalled_rows`` と同じ並びで、
#: 見せた記憶の行の目印 ``"t_ns:seq"``(器の外の行=店の評価の行は空文字)。
TAPE_COLUMN: Final[str] = "recalled_event_ids"

#: 記憶の行の列(属性の名・型・空の値)。``ROW_BYTES`` はこの和。
_ROW_COLS: Final[tuple[tuple[str, Any, int], ...]] = (
    ("_ms_ev_t_ns", np.int64, -1),      # 目印の時刻
    ("_ms_ev_seq", np.int32, 0),        # 目印の seq(負=仮の出来事の番地 −1−k)
    ("_ms_n", np.uint16, 0),            # 強さ: 回数
    ("_ms_imp", np.uint8, 0),           # 強さ: 重要度
    ("_ms_first_ns", np.int64, 0),      # 強さ: 最初に書かれた時刻
    ("_ms_origin", np.int8, _EMPTY_ORIGIN),  # 出どころ(−1=空の行)
    ("_ms_shown_ns", np.int64, -1),     # 録画: 最後に見せた時刻
)
#: 仮の出来事の表(行と同じ番地)。今の表 ``mem_*`` と同じ型。
_LEGACY_COLS: Final[tuple[tuple[str, Any, int], ...]] = (
    ("_lg_kind", np.uint8, 0),
    ("_lg_partner", np.int32, 0),
    ("_lg_object", np.int32, 0),
    ("_lg_result", np.uint8, 0),
    ("_lg_cell", np.int32, 0),
)
ROW_BYTES: Final[int] = int(sum(np.dtype(t).itemsize for _n, t, _f in _ROW_COLS))
LEGACY_BYTES: Final[int] = int(sum(np.dtype(t).itemsize for _n, t, _f in _LEGACY_COLS))
_COL_NAMES: Final[tuple[str, ...]] = tuple(n for n, _t, _f in _ROW_COLS + _LEGACY_COLS)
#: 行 M0R(録画)の列。作り直し(``rebuild``)は触らない。
_SHOWN_COLS: Final[frozenset[str]] = frozenset({"_ms_shown_ns"})

#: 状態台帳の道筋の代表(系の宣言 ``writes.paths`` がこれに当たれば書いてよい=段 C と同じ実行時の検査)。
ROW_PATH: Final[str] = "M0:mem_layer.memory_store._ms_n"
SHOWN_PATH: Final[str] = "M0R:mem_layer.memory_store._ms_shown_ns"
#: 〔2-3〕記録の目印の seq の列(状態台帳の腕の行 ``M0L``)。
LOG_SEQ_PATH: Final[str] = "M0L:mem_layer.memory_store._ms_log_seq"
#: 〔2-3〕記録の目印の seq の列の 1 行のバイト(i4・行 ``M0L``=腕のランだけ状態のファイルに入る)。
LOG_SEQ_BYTES: Final[int] = 4
#: 〔第 6 期 6-5〕M1 の直近の時刻の列(状態台帳の腕の行 ``M0M``=腕 memory-model・器の子の持ち主 ``m1``)。
M1_PATH: Final[str] = "M0M:mem_layer.memory_store.m1._t_ns"
#: 〔6-5〕意味の手がかりの状態(状態台帳の腕の行 ``M0C``=腕 memory-cue・器の子の持ち主 ``cue``)。
CUE_PATH: Final[str] = "M0C:mem_layer.memory_store.cue._heard"
#: 〔6-5・検収 M4〕上限なしの腕の店の評価の行(状態台帳の腕の行 ``M0S``=腕 memory-people・器の子の持ち主 ``shops``)。
SHOP_PATH: Final[str] = "M0S:mem_layer.memory_store.shops._poi"
#: 〔6-5〕上限なしの腕の店の行の番号の底(器の行の幅が広がるので、器の外の店の行は大きな番号から数える)。
UNCAPPED_SHOP_BASE: Final[int] = 1 << 24
#: 〔6-5〕上限なしの腕の最初の行の幅(既定=記憶の表と同じ ``memory_n``。試験は小さくして広がる道を通す=:func:`set_rows0`)。
_ROWS0: list[int | None] = [None]


def set_rows0(rows: int | None) -> None:
    """上限なしの腕の最初の行の幅(``None``=記憶の表と同じ)。試験と測りの切替口(組み立ての時に読む)。"""
    if rows is not None and int(rows) < 1:
        raise ValueError("rows0 は 1 以上か None")
    _ROWS0[0] = None if rows is None else int(rows)


def rows0() -> int | None:
    return _ROWS0[0]


#: 〔第 6 期 6-5・検収 M2〕上限なしの腕の種類ごとの行の上限(体あたり・**未リサーチ(expedient)**・感度の腕の口=
#: :func:`set_row_caps`)。``episode``=出来事の行(器の行の種類 1〜11)・``person``=人の行(``memory_m1.PERSON_KIND``)・
#: ``shop``=店の評価の行(``engine.memory_shops.ShopTable``)。器の行の幅(出来事と人で共有)は倍にするたびに
#: ``episode + person`` までで止まる。上限の種類の行がいっぱいの体は、思い浮かぶ強さ A(手がかり無し)が一番低いその種類の行
#: から消す(同点は最後に触れた時刻の古い順・次に行の番号=決定的)。つなぎの台帳 ``DOC-mr65-m1-row-caps``。
ROW_CAPS_DEFAULT: Final[Mapping[str, int]] = MappingProxyType({"episode": 256, "person": 256, "shop": 256})
_ROW_CAPS: dict[str, int] = dict(ROW_CAPS_DEFAULT)
#: 器の行の種類の分類(上限の鍵)。
_CAP_KINDS: Final[tuple[str, ...]] = ("episode", "person")


def set_row_caps(**caps: int | None) -> None:
    """上限なしの腕の種類ごとの行の上限(``episode``・``person``・``shop``・``None``=既定の値に戻す)。試験と感度の腕の口
    (組み立ての時に読む)。"""
    for k, v in caps.items():
        if k not in ROW_CAPS_DEFAULT:
            raise KeyError(f"行の上限の種類は {tuple(ROW_CAPS_DEFAULT)} のどれか(いま {k!r})")
        if v is not None and int(v) < 1:
            raise ValueError("行の上限は 1 以上か None")
        _ROW_CAPS[k] = ROW_CAPS_DEFAULT[k] if v is None else int(v)


def row_caps() -> dict[str, int]:
    """いまの種類ごとの行の上限(写し)。"""
    return dict(_ROW_CAPS)


#: 今の表の「店の行と重なる」種類(購入・食事・並ぶ・看板)=7c の重なりの鍵(``engine.memory._SHOP_OBJ_KINDS`` と同じ)。
_SHOP_KINDS: Final[tuple[int, ...]] = (
    EVENT_KINDS["buy"], EVENT_KINDS["eat"], EVENT_KINDS["queue"], EVENT_KINDS["signage"],
)


#: 〔2-3〕出来事の語のコード → 記憶の種類(``engine.events.body.kind_of_what`` の表=覚えるときの中身の写像の検査)。
_KIND_OF_CODE: Final[np.ndarray] = np.asarray([_BODY.kind_of_what(c) for c in range(len(_VOCAB.VOCAB))], dtype=np.int64)
_KIND_OF_CODE.setflags(write=False)

_COL_SPEC: Final[Mapping[str, tuple[Any, int]]] = MappingProxyType(
    {n: (t, f) for n, t, f in _ROW_COLS + _LEGACY_COLS})


def _column(name: str, size: int) -> np.ndarray:
    t, f = _COL_SPEC[name]
    return np.full(int(size), f, dtype=t)


@functools.lru_cache(maxsize=256)
def _permit_has(permit: frozenset[str], path: str) -> bool:
    return path in permit or any(fnmatch.fnmatchcase(path, x) for x in permit if "*" in x)


def _check_permit(path: str, what: str) -> None:
    p = _G.PATHS_PERMIT
    if p is not None and not _permit_has(p, path):
        raise PermissionError(f"系 {_G.CURRENT} は記憶の器の{what}({path.split(':')[0]}:mem_layer.memory_store.*)を"
                              "書く宣言を持たない(1-6・writes.paths)")


# ================================================================ 型
class Cue(NamedTuple):
    """想起の手がかり(System 1 が体の状態から作る=今の 6b の q・ID の一致)。負/0 は「無し」。"""

    cell: int = -1
    partner: int = -1
    obj: int = -1
    kind: int = 0
    result: int = -1


class LegacyEvent(NamedTuple):
    """出来事の記録に無い出来事(仮の行の中身)。配列か整数。``t_ns`` はその回の時刻。"""

    t_ns: Any
    kind: Any
    partner: Any
    obj: Any
    result: Any
    cell: Any


class LoggedEvent(NamedTuple):
    """〔第 2 期 2-3〕出来事の記録にある出来事への目印(``(t_ns, seq)``)と中身の写し。配列か整数。

    中身(種類・相手・対象・結果・セル)は器の想起が配列で引く写し(記録の行の ``what``・``who`` と合うことは覚えるときに確かめる)。
    """

    t_ns: Any
    seq: Any
    kind: Any
    partner: Any
    obj: Any
    result: Any
    cell: Any


class MemoryView(NamedTuple):
    """LLM に見せる形(MR-0): 言葉(``clarity``)と中身の粗さ(``grain``)と中身の ID。**強さの数は持たない**。

    ``row``・``event_id``・``origin``・``first_ns`` は録画の同定(描き方は使わない)。``when_ns`` は描き方の時刻(最後の回)。
    7c の店の評価の行(器の外=今の ``sm_*``)は ``kind=STORE_ITEM_KIND``・``row=n_rows+店の行``・``event_id=None``。
    """

    row: int
    event_id: EventId | None
    origin: str | None
    clarity: str
    grain: str
    kind: int
    partner: int
    obj: int
    result: int
    cell: int
    annotation: str
    when_ns: int
    first_ns: int
    valence: int = 0
    source: int = 0


class ShopPool(NamedTuple):
    """ほかの表の候補(M0 は 7c の店の評価の行=今の ``sm_*``)。器の行と同じ score の順で競わせる。"""

    score: np.ndarray
    live: np.ndarray
    match: np.ndarray
    key: np.ndarray
    view: Callable[[int], MemoryView]


class RecallReport(NamedTuple):
    """1 回の想起の計数(``MemoryLayer`` が manifest の ``memory_summary.recall.counts`` に足す)。"""

    empty: bool
    rows_used: int
    rows_used_below_tau: int
    rows_candidate: int
    rows_candidate_below_tau: int
    filled: int
    dedup_skipped: int
    picked: int


def clarity_of(a: float, tau: float) -> str:
    """強さ A → 言葉(MR-0)。A ≥ τ=はっきり・それ以外=うろ覚え(境目は expedient)。"""
    return CLARITY_WORDS[0] if float(a) >= float(tau) else CLARITY_WORDS[1]


def event_id_text(eid: EventId | None) -> str:
    """目印 → テープの列の文字列 ``"t_ns:seq"``(無ければ空文字)。"""
    return "" if eid is None else f"{int(eid[0])}:{int(eid[1])}"


def to_item(v: MemoryView, ns_per_step: int) -> RecallItem:
    """``MemoryView`` → 今の描き方が読む ``RecallItem``(刻みの番号に戻す=今の表と同じ値)。"""
    return RecallItem(
        row=int(v.row), last_tick=int(v.when_ns) // int(ns_per_step), kind=int(v.kind), partner=int(v.partner),
        obj=int(v.obj), result=int(v.result), cell=int(v.cell), gist=str(v.annotation), valence=int(v.valence),
        source=int(v.source), first_tick=int(v.first_ns) // int(ns_per_step),
    )


# ================================================================ 器
class MemoryStore:
    """記憶の器 M0(体ごとの行の範囲・SoA の列)。書く口は :meth:`remember` と :meth:`mark_shown`。

    Args:
        n_agents: 体の数。
        n_rows: 体あたりの行数(今の表 ``memory_n`` と同じ=M0 は容量も今のまま。容量の廃止は M1)。
        step_seconds: 1 刻みの秒(目印の時刻 ``t_ns`` と刻みの番号の換算=今の式の単位)。
        minutes_per_step: 今の式の L の単位(``MemoryLayer.minutes_per_tick`` と同じ値を渡す)。
        d・w_r・w_i・tau: 今の式の定数(``engine.memory``)。
    """

    __slots__ = _COL_NAMES + (
        "n", "n_rows", "ns_per_step", "minutes_per_step", "d", "w_r", "w_i", "tau", "tape_on",
        "_ms_note", "_ms_note_order", "_ms_tape", "_ms_stats", "_ms_last",
        "_ms_log_seq", "body_events",
        "m1", "cue", "uncapped", "grain", "caps", "shops", "arms_cfg",
    )
    #: 〔2-3〕状態台帳の腕の行の腕の名(行 ``M0L``=``state_ledger.arm_items`` が持ち主の名と照合する)。
    LEDGER_ARM: str = "memory-store"

    def __init__(self, n_agents: int, n_rows: int, *, step_seconds: int, minutes_per_step: float,
                 d: float = MEMORY_D, w_r: float = MEMORY_W_R, w_i: float = MEMORY_W_I,
                 tau: float = RECALL_TAU) -> None:
        if int(n_agents) < 0 or int(n_rows) < 1 or int(step_seconds) < 1:
            raise ValueError("n_agents ≥ 0・n_rows ≥ 1・step_seconds ≥ 1")
        self.n = int(n_agents)
        self.n_rows = int(n_rows)
        self.ns_per_step = int(step_seconds) * NS_PER_SECOND
        self.minutes_per_step = float(minutes_per_step)
        self.d = float(d)
        self.w_r = float(w_r)
        self.w_i = float(w_i)
        self.tau = float(tau)
        #: テープに列を足すランか(組み立てが :meth:`attach_tape` で立てる)。立っていなければ録画の控えを持たない。
        self.tape_on = False
        size = self.n * self.n_rows
        # 記憶の行の列(_ROW_COLS)と仮の出来事の表(_LEGACY_COLS)。型と空の値は表から
        self._ms_ev_t_ns = _column("_ms_ev_t_ns", size)
        self._ms_ev_seq = _column("_ms_ev_seq", size)
        self._ms_n = _column("_ms_n", size)
        self._ms_imp = _column("_ms_imp", size)
        self._ms_first_ns = _column("_ms_first_ns", size)
        self._ms_origin = _column("_ms_origin", size)
        self._ms_shown_ns = _column("_ms_shown_ns", size)
        self._lg_kind = _column("_lg_kind", size)
        self._lg_partner = _column("_lg_partner", size)
        self._lg_object = _column("_lg_object", size)
        self._lg_result = _column("_lg_result", size)
        self._lg_cell = _column("_lg_cell", size)
        #: 〔2-3〕記録の目印の seq(−1=仮の行か空の行)。状態台帳の腕の行 M0L(再開で目印を戻す)。
        self._ms_log_seq = np.full(size, -1, dtype=np.int32)
        #: 〔2-3〕体の出来事の口(``engine.events.body.BodyEventLink``・組み立てが腕と記録のあるランだけ置く)。
        self.body_events: Any = None
        #: 注釈(番地 → 文字列)と体ごとの順(古い順に落とす=今の ``MemoryLayer._gist_order`` と同じ)。
        self._ms_note: dict[int, str] = {}
        self._ms_note_order: dict[int, "OrderedDict[int, None]"] = {}
        #: 録画の控え(呼び出しの鍵 (体, t_ns, 起床の級) → 見せた行の目印の組の列)。テープの列へ渡すと消す。
        self._ms_tape: dict[tuple[int, int, int], list[tuple[str, ...]]] = {}
        #: 計数(manifest ``memory_summary.memory_store.counts``)。
        self._ms_stats: Counter = Counter()
        #: 最後の想起の計数(``MemoryLayer`` が読む)。
        self._ms_last: RecallReport = RecallReport(True, 0, 0, 0, 0, 0, 0, 0)
        #: 〔第 6 期 6-5〕腕の子の持ち主と設定(既定は全部 None/偽/each=今の器のまま。:meth:`enable_arms` が 1 回だけ置く)。
        #: m1=M1 の強さの状態(``engine.memory_m1.M1State``)・cue=意味の手がかり(``engine.memory_embed.CueState``)・
        #: uncapped=人も記憶の一つの腕(上限なし・忘れる=消す・器は記憶の表の写しでない)・grain=体の出来事の粒度。
        self.m1: Any = None
        self.cue: Any = None
        self.uncapped = False
        self.grain = _M1.GRAIN_EACH
        #: 〔検収 M2〕上限なしの腕の種類ごとの行の上限(:func:`row_caps` の写し=組み立てで 1 回)・〔検収 M4〕店の評価の行の
        #: 器の子の持ち主(``engine.memory_shops.ShopTable``=上限なしの腕で店の記憶のあるランだけ)・〔検収 L1〕腕の設定の値
        #: (``memory_m1.config_of``=manifest の ``memory_summary.mr65_arms``)。
        self.caps: Mapping[str, int] = MappingProxyType({})
        self.shops: Any = None
        self.arms_cfg: Mapping[str, Any] = MappingProxyType({})

    def __setattr__(self, name: str, value: Any) -> None:
        # 欄は最初の 1 回(組み立て)だけ置ける。付け替えは口の中で object.__setattr__ を使う(テープの印・最後の想起の計数)
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"記憶の器の欄 {name} は付け替えられない(書く口は remember・mark_shown)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"記憶の器の欄 {name} は消せない(消してから付け替える抜け道を閉じる)")

    # ------------------------------------------------------------------ 範囲と読み口
    def rows_of(self, agent: int) -> range:
        """体 ``agent`` の行の範囲(番地)。"""
        i = int(agent)
        if not 0 <= i < self.n:
            raise IndexError(agent)
        return range(i * self.n_rows, (i + 1) * self.n_rows)

    def has_rows(self, agent: int) -> bool:
        """体に記憶の行が 1 つでもあるか。"""
        r = self.rows_of(agent)
        return bool((self._ms_origin[r.start:r.stop] >= 0).any())

    def event_id(self, agent: int, row: int) -> EventId | None:
        """体の行 ``row`` の目印(空の行は ``None``)。"""
        g = self.rows_of(agent).start + int(row)
        if not 0 <= int(row) < self.n_rows or self._ms_origin[g] < 0:
            return None
        return (int(self._ms_ev_t_ns[g]), int(self._ms_ev_seq[g]))

    def pointer_same_day(self, agent: Any, rows: Any, now_ns: int) -> np.ndarray:
        """〔第 6 期 6-5 粒度 day〕体の行の目印が「記録の出来事で、いまと同じ日」か(読むだけ・配列)。"""
        g = np.asarray(agent, dtype=np.int64) * self.n_rows + np.asarray(rows, dtype=np.int64)
        return ((self._ms_origin[g] == _LOG_CODE) & (self._ms_log_seq[g] >= 0)
                & (self._ms_ev_t_ns[g] // NS_PER_DAY == int(now_ns) // NS_PER_DAY))

    def origin(self, agent: int, row: int) -> str | None:
        g = self.rows_of(agent).start + int(row)
        o = int(self._ms_origin[g])
        if o < 0:
            raise KeyError((agent, row))
        return ORIGINS[o]

    def shown_ns(self, agent: int, row: int) -> int:
        """録画: 体の行を最後に見せた時刻(−1=まだ)。"""
        return int(self._ms_shown_ns[self.rows_of(agent).start + int(row)])

    def annotation(self, agent: int, row: int) -> str | None:
        return self._ms_note.get(self.rows_of(agent).start + int(row))

    @property
    def last_recall(self) -> RecallReport:
        return self._ms_last

    @property
    def store_counts(self) -> dict[str, int]:
        """計数の写し(manifest ``memory_summary.memory_store.counts``)。"""
        return {k: int(v) for k, v in sorted(self._ms_stats.items())}

    def attach_events(self, link: Any) -> None:
        """〔2-3〕体の出来事の口を置く(組み立てが 1 回だけ呼ぶ=記録のある腕のラン)。置いた器の目印は記録の出来事になる。"""
        if self.body_events is not None:
            raise RuntimeError("体の出来事の口は 1 回だけ置く")
        object.__setattr__(self, "body_events", link)

    def attach_tape(self) -> None:
        """テープに列 ``recalled_event_ids`` を足すランで、録画の控えを持つようにする(組み立てが 1 回だけ呼ぶ)。"""
        object.__setattr__(self, "tape_on", True)

    def enable_arms(self, *, m1: Any = None, cue: Any = None, uncapped: bool = False,
                    grain: str = _M1.GRAIN_EACH, config: Mapping[str, Any] | None = None) -> None:
        """〔第 6 期 6-5〕腕の子の持ち主と設定を置く(組み立てが 1 回だけ・系の外)。既定の値のままなら何もしない。

        ``uncapped`` は ``m1`` が前提(人の行の強さと忘れるの判定は M1 の式)。上限なしの器の行の幅は :func:`rows0`(既定=今の
        ``n_rows``)から始め、満杯の体が出たら忘れた行を消し、それでも足りなければ全員の幅を倍にする(〔検収 M2〕幅は
        種類ごとの上限の和 ``episode + person`` まで=:func:`row_caps`・その種類の行が上限に届いた体は A の一番低い行を消す)。
        ``config``(〔検収 L1〕``memory_m1.config_of`` の値)は manifest の設定の節 ``memory_summary.mr65_arms`` に出す。
        """
        if _G.CURRENT is not None:
            raise RuntimeError("6-5 の腕は組み立て(系の外)でだけ置く")
        if self.m1 is not None or self.cue is not None or self.uncapped or self.grain != _M1.GRAIN_EACH:
            raise RuntimeError("6-5 の腕は 1 回だけ置く")
        if grain not in _M1.GRAINS:
            raise ValueError(f"grain は {_M1.GRAINS} のどれか(いま {grain!r})")
        if uncapped and m1 is None:
            raise ValueError("上限なしの腕(人も記憶の一つ)は M1 の強さの状態が前提")
        if uncapped and grain != _M1.GRAIN_EACH:
            raise ValueError("上限なしの腕と粒度 day は同時に選べない(本段は別々に測る)")
        if m1 is not None:
            object.__setattr__(self, "m1", m1)
        if cue is not None:
            object.__setattr__(self, "cue", cue)
        object.__setattr__(self, "grain", str(grain))
        if config:
            object.__setattr__(self, "arms_cfg", MappingProxyType(dict(config)))
        if uncapped:
            object.__setattr__(self, "uncapped", True)
            object.__setattr__(self, "caps", MappingProxyType(row_caps()))
            r0 = rows0()
            if r0 is not None and int(r0) > self.max_width:
                raise ValueError(f"rows0 {r0} が器の行の幅の上限 {self.max_width}(出来事+人の上限)を超える")
            if r0 is not None and int(r0) != self.n_rows and not bool((self._ms_origin >= 0).any()):
                self._resize(int(r0))
            elif r0 is None and self.n_rows > self.max_width:
                raise ValueError(f"器の行の幅 {self.n_rows} が上限 {self.max_width}(出来事+人の上限)を超える")

    @property
    def max_width(self) -> int:
        """〔検収 M2〕上限なしの腕の器の行の幅の上限(出来事と人の上限の和・腕の無い器は今の幅)。"""
        if not self.uncapped:
            return int(self.n_rows)
        return int(sum(int(self.caps[k]) for k in _CAP_KINDS))

    def attach_shops(self, table: Any) -> None:
        """〔第 6 期 6-5・検収 M4〕店の評価の行の器の子の持ち主を置く(組み立てが 1 回だけ・上限なしの腕で店の記憶のあるラン)。

        店の評価の記憶(``engine.store_memory.StoreMemory`` の子 ``engine.memory_shops.UncappedStoreMemory``)が行をこの表に
        書く(体の表 ``agents.registry.sm_*`` は使わない=上限 32 の固定の表を外す道)。
        """
        if _G.CURRENT is not None:
            raise RuntimeError("店の行の表は組み立て(系の外)でだけ置く")
        if not self.uncapped:
            raise RuntimeError("店の行の表は上限なしの腕(--memory-people memory)だけ")
        if self.shops is not None:
            raise RuntimeError("店の行の表は 1 回だけ置く")
        object.__setattr__(self, "shops", table)

    # ------------------------------------------------------------------ 〔6-5〕上限なしの腕(忘れる=消す・幅を広げる)
    def _resize(self, new_rows: int) -> None:
        """体あたりの行の幅を ``new_rows`` に(体の範囲の並びを保つ・広げるだけ=縮めるのは空の器だけ)。口の中だけ。"""
        old = self.n_rows
        new = int(new_rows)
        n = self.n
        if new < old and bool((self._ms_origin >= 0).any()):
            raise RuntimeError("行の幅を縮められるのは空の器だけ")
        keep = min(old, new)
        for name, _t, fill in _ROW_COLS + _LEGACY_COLS:
            cur = getattr(self, name).reshape(n, old)
            out = np.full((n, new), fill, dtype=cur.dtype)
            out[:, :keep] = cur[:, :keep]
            object.__setattr__(self, name, out.reshape(-1))
        cur = self._ms_log_seq.reshape(n, old)
        out = np.full((n, new), -1, dtype=np.int32)
        out[:, :keep] = cur[:, :keep]
        object.__setattr__(self, "_ms_log_seq", out.reshape(-1))
        notes = dict(self._ms_note)
        self._ms_note.clear()
        for g, text in notes.items():  # 逐次ループ宣言: 注釈の件数ぶん(広げるときだけ)
            a, j = divmod(int(g), old)
            self._ms_note[a * new + j] = text
        if self.m1 is not None:
            self.m1.grow(n, old, new)
        if self.cue is not None:
            self.cue.remap(n, old, new)
        object.__setattr__(self, "n_rows", new)
        self._ms_stats["rows_resized"] += 1

    def _delete_rows(self, g: np.ndarray, *, reason: str = "forgotten") -> None:
        """〔6-5〕行を消す(上限なしの腕だけ・口の中から)。``reason``: ``forgotten``=忘れた(見覚えにも届かない)・
        ``evicted_by_a``=〔検収 M2〕種類の上限で思い浮かぶ強さ A の一番低い行。"""
        gg = np.asarray(g, dtype=np.int64)
        if gg.size == 0:
            return
        for name, _t, fill in _ROW_COLS + _LEGACY_COLS:
            getattr(self, name)[gg] = fill
        self._ms_log_seq[gg] = -1
        N = self.n_rows
        for x in gg.tolist():  # 逐次ループ宣言: 消した行の数ぶん
            self._drop_note(int(x) // N, int(x) % N)
        if self.m1 is not None:
            self.m1.clear(gg, reason=reason)
        self._ms_stats[reason] += int(gg.size)

    def _cap_class(self, kind: Any) -> np.ndarray:
        """〔検収 M2〕器の行の種類 → 上限の分類(0=出来事・1=人)。"""
        return (np.asarray(kind, dtype=np.int64) == _M1.PERSON_KIND).astype(np.int64)

    def _at_cap(self, a: np.ndarray, kind: np.ndarray) -> np.ndarray:
        """〔検収 M2〕体の配列と新しい行の種類 → その種類の行が上限に届いている体か(上限なしの腕だけ)。"""
        N = self.n_rows
        g = a[:, None] * N + np.arange(N)[None, :]
        used = self._ms_origin[g] >= 0
        cls = self._cap_class(kind)
        same = used & (self._cap_class(self._lg_kind[g]) == cls[:, None])
        cap = np.asarray([int(self.caps[_CAP_KINDS[c]]) for c in range(len(_CAP_KINDS))], dtype=np.int64)
        return same.sum(axis=1) >= cap[cls]

    def _evict_by_a(self, a: np.ndarray, kind: np.ndarray, now_ns: int) -> np.ndarray:
        """〔検収 M2〕種類の上限に届いた体 → その種類の行のうち思い浮かぶ強さ A(M1・手がかり無し)の一番低い行の番号
        (同点は最後に触れた時刻=目印の時刻の古い順・次に行の番号=決定的)。行を消し(``evicted_by_a``)、番号を返す。"""
        N = self.n_rows
        g = a[:, None] * N + np.arange(N)[None, :]
        cls = self._cap_class(kind)
        mask = (self._ms_origin[g] >= 0) & (self._cap_class(self._lg_kind[g]) == cls[:, None])
        A = np.full(g.shape, np.inf)
        gu = g[mask]
        A[mask] = self.m1.strength(gu, gu // N, int(now_ns), self._ms_n[gu], self._ms_first_ns[gu], self._lg_kind[gu],
                                   self._ms_imp[gu])
        A = np.where(mask, A, np.inf)
        c1 = mask & (A == A.min(axis=1)[:, None])
        t = np.where(c1, self._ms_ev_t_ns[g], np.iinfo(np.int64).max)
        c2 = c1 & (t == t.min(axis=1)[:, None])
        slot = np.argmax(c2, axis=1).astype(np.int64)
        if not bool(c2[np.arange(a.size), slot].all()):
            raise RuntimeError("上限に届いた体にその種類の行が無い(上限の数え方の誤り)")
        self._delete_rows(a * N + slot, reason="evicted_by_a")
        for c in np.unique(cls).tolist():  # 上限の分類の数ぶん(≤ 2)
            self._ms_stats[f"evicted_by_a:{_CAP_KINDS[int(c)]}"] += int(np.count_nonzero(cls == c))
        return slot

    def _forgettable(self, a: np.ndarray, now_ns: int) -> np.ndarray:
        """〔6-5〕体の配列 → ``(体, n_rows)`` の「忘れた(見覚えにも届かない)」行の印(上限なしの腕だけ)。"""
        N = self.n_rows
        g = (a[:, None] * N + np.arange(N)[None, :]).reshape(-1)
        used = self._ms_origin[g] >= 0
        A_fam = np.full(g.size, -np.inf)
        if bool(used.any()):
            gu = g[used]
            A_fam[used] = self.m1.strength(gu, gu // N, int(now_ns), self._ms_n[gu], self._ms_first_ns[gu],
                                           self._lg_kind[gu], self._ms_imp[gu], familiar=True)
        return (used & _M1.forget_mask(A_fam, self.m1.tau)).reshape(a.size, N)

    def _make_room(self, a: np.ndarray, now_ns: int) -> None:
        """〔6-5〕満杯の体に空きを作る: 忘れた行を消す(意味は前のまま=見覚えにも届かない行)→ それでも満杯の体がいれば全員の
        幅を倍にする(〔検収 M2〕幅は :attr:`max_width` まで=種類の上限に届いていない体が満杯なら幅は上限より小さい)。"""
        aa = np.unique(np.asarray(a, dtype=np.int64))
        if aa.size == 0:
            return
        gone = self._forgettable(aa, now_ns)
        if bool(gone.any()):
            r, j = np.nonzero(gone)
            self._delete_rows(aa[r] * self.n_rows + j)
        N = self.n_rows
        full = ~((self._ms_origin.reshape(self.n, N)[aa] < 0).any(axis=1))
        if bool(full.any()):
            new = min(2 * N, self.max_width)
            if new <= N:
                raise RuntimeError(f"器の行の幅が上限 {self.max_width} なのに満杯の体がいる(種類の上限で消す道の誤り)")
            self._resize(new)

    # ------------------------------------------------------------------ System 1 の数(M0=今の式)
    def _activation(self, g0: int, g1: int, now_step: int) -> np.ndarray:
        return activation_rows(self._ms_n[g0:g1], self._ms_first_ns[g0:g1] // self.ns_per_step, int(now_step),
                               self.minutes_per_step, self.d)

    def _evict_scores(self, a: np.ndarray, now_step: int) -> np.ndarray:
        """体の配列 → ``(体, n_rows)`` の score(今の ``MemoryLayer.scores`` と同じ: float32 に丸めて float64 へ)。"""
        N = self.n_rows
        n = self._ms_n.reshape(self.n, N)[a]
        first = self._ms_first_ns.reshape(self.n, N)[a] // self.ns_per_step
        A = activation_rows(n, first, int(now_step), self.minutes_per_step, self.d)
        s = self.w_r * A + self.w_i * self._ms_imp.reshape(self.n, N)[a].astype(np.float64)
        s[self._ms_origin.reshape(self.n, N)[a] < 0] = -np.inf
        return s.astype(np.float32).astype(np.float64)

    # ------------------------------------------------------------------ 書く口 1: 覚える
    def remember(self, agent: Any, event_id: Any, strength: Any, origin: str | None, *,
                 annotation: Sequence[str | None] | None = None, keep_pointer: Any = None) -> np.ndarray:
        """出来事を覚える → 書いた行(体の範囲の中の番号・入力の並び)。

        Args:
            agent: 体(整数か 1 次元の配列)。**1 回の呼びで 1 体 1 件**(今の表の書き手と同じ回の分け方)。
            event_id: 目印。``origin=None`` のときは :class:`LoggedEvent`(記録の id と中身の写し)=**記録にある出来事の
                id だけ**(〔2-3〕無い id・``who`` が体と違う・``what`` が種類と合わない目印は ``ValueError``)。
                ``origin="legacy"`` のときは :class:`LegacyEvent`(記録に無い出来事の中身)=器が行と同じ番地に仮の出来事を
                書き、目印 ``(t_ns, −1 − 番地)`` を付ける。
            strength: System 1 の重みの素(M0=重要度の固定表の base: 失敗 3・会話 2・成功/気づき/看板 1)。新しい行は
                初回 +1・上限 4、重ねた行は base(今の表の規則 M3 (b)・Q56)。回数は重ねるごとに +1。
            origin: ``None``(記録の出来事=〔2-3〕体の出来事の口を置いた器だけ)か ``"legacy"``(記録に無い出来事)。
            annotation: 一人ずつの注釈(会話の要旨・入力の並び・``None`` は付けない=既存の注釈は残す)。
            keep_pointer: 〔第 6 期 6-5・粒度 day の腕〕真の行は目印(記録の出来事の id・出どころ)を変えない(同じ記憶の行の日の
                中の 2 回目からは記録に書かない=呼び手が記録へ書かなかった行・``LoggedEvent`` の seq は −1 でよい)。
                回数・重要度・M1 の直近の時刻は進める。

        〔6-5〕人の行(種類 ``memory_m1.PERSON_KIND``)は鍵が (種類, 相手) だけ(対象の欄=関係の種類は重ねても前の値を残す)・
        重要度 0。上限なしの腕(:attr:`uncapped`)では追い出さず、満杯の体は忘れた行を消すか幅を広げる(:meth:`_make_room`)。
        M1 の腕(:attr:`m1`)では書いた行の直近の時刻を進める。意味の手がかりの腕(:attr:`cue`)では注釈の埋め込みを置く。
        """
        _check_permit(ROW_PATH, "行")
        _check_permit(SHOWN_PATH, "計数と新しい行の録画の印")
        if self.m1 is not None:
            _check_permit(M1_PATH, "M1 の直近の時刻")
        if origin == ORIGIN_LEGACY:
            if not isinstance(event_id, LegacyEvent):
                raise TypeError("出どころ legacy の目印は LegacyEvent(仮の出来事の中身)")
            logged = False
        elif origin is None:
            link = self.body_events
            if link is None or not bool(link.enabled):
                raise ValueError("出どころ None(記録の出来事への目印)は記録にある出来事の id だけ。体の出来事の口の無い器"
                                 "(記録 off・器だけの道)に書けるのは出どころ legacy(記録に無い出来事の仮の行)だけ")
            if not isinstance(event_id, LoggedEvent):
                raise TypeError("出どころ None の目印は LoggedEvent(記録の id と中身の写し)")
            _check_permit(LOG_SEQ_PATH, "記録の目印の seq")
            logged = True
        else:
            raise ValueError(f"出どころは {ORIGINS} のどれか(いま {origin!r}・legacy=記録に無い出来事の仮の行)")
        a = np.atleast_1d(np.asarray(agent, dtype=np.int64))
        m = a.size
        if m == 0:
            return np.zeros(0, dtype=np.int64)
        if np.unique(a).size != m:
            raise ValueError("remember は 1 回の呼びで 1 体 1 件(同じ体の出来事は回を分ける)")
        if (a < 0).any() or (a >= self.n).any():
            raise IndexError("体の番号が範囲の外")
        kept = (np.zeros(m, dtype=bool) if keep_pointer is None
                else np.broadcast_to(np.asarray(keep_pointer, dtype=bool), (m,)).copy())
        if bool(kept.any()) and not logged:
            raise ValueError("keep_pointer は記録の出来事の目印(出どころ None)の行だけ")
        if logged:
            ev = LoggedEvent(*(np.broadcast_to(np.asarray(x, dtype=np.int64), (m,)) for x in event_id))
            if bool(kept.any()):  # 〔6-5 粒度 day〕記録に書かなかった行は目印を確かめない(目印は前のまま)
                w = ~kept
                self._check_logged(a[w], LoggedEvent(*(x[w] for x in ev)))
            else:
                self._check_logged(a, ev)
        else:
            ev = LegacyEvent(*(np.broadcast_to(np.asarray(x, dtype=np.int64), (m,)) for x in event_id))
        if (ev.t_ns < 0).any():
            raise ValueError("出来事の時刻 t_ns は 0 以上")
        base = np.broadcast_to(np.asarray(strength, dtype=np.int64), (m,))
        ann = None if annotation is None else list(annotation)
        if ann is not None and len(ann) != m:
            raise ValueError("annotation は出来事と同じ数")
        now_step = int(ev.t_ns[0]) // self.ns_per_step
        if (ev.t_ns // self.ns_per_step != now_step).any():
            raise ValueError("1 回の呼びの出来事は同じ刻み")
        person = ev.kind == _M1.PERSON_KIND
        any_person = bool(person.any())
        if self.uncapped:  # 〔検収 M2〕種類の上限: 新しい行で、その種類の行が上限に届いた体は A の一番低い行を先に消す
            capped = ~self._hit(a, ev, person, any_person).any(axis=1) & self._at_cap(a, ev.kind)
            if bool(capped.any()):
                self._evict_by_a(a[capped], ev.kind[capped], int(ev.t_ns[0]))
        for _round in range(2):  # 〔6-5〕上限なしの腕で空きを作った後にもう 1 回(逐次ループ宣言: 2 回まで)
            N = self.n_rows
            used = self._ms_origin.reshape(self.n, N)[a] >= 0
            hit = self._hit(a, ev, person, any_person)
            found = hit.any(axis=1)
            slot = np.where(found, np.argmax(hit, axis=1), -1)
            empty = ~used
            new = ~found
            has_empty = empty.any(axis=1)
            slot = np.where(new & has_empty, np.argmax(empty, axis=1), slot)
            evict = new & ~has_empty
            if not (self.uncapped and bool(evict.any())) or _round == 1:
                break
            self._make_room(a[evict], int(ev.t_ns[0]))
        if bool(evict.any()):
            if self.uncapped:
                raise RuntimeError("上限なしの腕で空きを作れなかった(幅を倍にした後も満杯)")
            slot[evict] = np.argmin(self._evict_scores(a[evict], now_step), axis=1)  # 同点は行番号の小さい方
            self._ms_stats["evictions"] += int(np.count_nonzero(evict))
            for x, y in zip(a[evict].tolist(), slot[evict].tolist()):  # 追い出した行の注釈を落とす(件数ぶん)
                self._drop_note(int(x), int(y))
        g = a * N + slot
        if bool(kept.any()) and not bool(found[kept].all()):
            raise ValueError("keep_pointer の行は重ねる行(同じ鍵の行がある)だけ")
        old_n = self._ms_n[g].astype(np.int64)
        n_new = np.where(found, np.minimum(old_n + 1, 65_535), 1)
        first = np.where(found, self._ms_first_ns[g], ev.t_ns)
        imp = np.where(found, np.minimum(base, IMPORTANCE_MAX),
                       np.minimum(base + IMPORTANCE["first_bonus"], IMPORTANCE_MAX))
        if any_person:  # 人の行は重要度 0・関係の種類(対象の欄)は重ねても前の値
            imp = np.where(person, 0, imp)
            obj = np.where(person & found, self._lg_object[g].astype(np.int64), ev.obj)
        else:
            obj = ev.obj
        # 中身(行と同じ番地=仮の出来事の中身か記録の出来事の中身の写し)と目印(最後の回)
        self._lg_kind[g] = ev.kind.astype(np.uint8)
        self._lg_partner[g] = ev.partner.astype(np.int32)
        self._lg_object[g] = obj.astype(np.int32)
        self._lg_result[g] = ev.result.astype(np.uint8)
        self._lg_cell[g] = ev.cell.astype(np.int32)
        gp = g[~kept] if bool(kept.any()) else g  # 目印を書く行(粒度 day の 2 回目からの行は前の目印のまま)
        self._ms_ev_t_ns[gp] = ev.t_ns[~kept] if bool(kept.any()) else ev.t_ns
        if logged:
            sq = ev.seq[~kept] if bool(kept.any()) else ev.seq
            self._ms_ev_seq[gp] = sq.astype(np.int32)
            self._ms_log_seq[gp] = sq.astype(np.int32)
            self._ms_origin[gp] = _LOG_CODE
            self._ms_stats["log_events"] += int(gp.size)
            if bool(kept.any()):
                self._ms_stats["pointer_kept"] += int(np.count_nonzero(kept))
        else:
            self._ms_ev_seq[g] = (-1 - g).astype(np.int32)
            self._ms_log_seq[g] = -1
            self._ms_origin[g] = _LEGACY_CODE
            self._ms_stats["legacy_events"] += int(m)
        self._ms_n[g] = n_new.astype(np.uint16)
        self._ms_imp[g] = imp.astype(np.uint8)
        self._ms_first_ns[g] = first
        self._ms_shown_ns[g[new]] = -1  # 新しい記憶(空の行・追い出した行)はまだ見せていない
        if self.m1 is not None:  # 〔6-5〕M1: 直近の時刻を進める(新しい行は前の回を消してから)
            self.m1.place(g, new, ev.t_ns)
        self._ms_stats["remember"] += int(m)
        self._ms_stats["merged"] += int(np.count_nonzero(found))
        self._ms_stats["new_rows"] += int(np.count_nonzero(new))
        if any_person:
            self._ms_stats["person_touches"] += int(np.count_nonzero(person))
        if ann is not None:
            put: list[tuple[int, str]] = []
            for x, y, t in zip(a.tolist(), slot.tolist(), ann):  # 注釈のある出来事の数ぶん(会話の要旨=1 件)
                if t is not None:
                    self._put_note(int(x), int(y), str(t))
                    put.append((int(x) * N + int(y), str(t)))
            if put and self.cue is not None:  # 〔6-5 MR2 問い 3〕要旨に埋め込みを付ける(1 回のバッチ)
                _check_permit(CUE_PATH, "行の埋め込み")
                self.cue.embed_rows([p[0] for p in put], [p[1] for p in put])
        return slot.astype(np.int64)

    def _hit(self, a: np.ndarray, ev: Any, person: np.ndarray, any_person: bool) -> np.ndarray:
        """体の配列と出来事 → ``(体, 幅)`` の「同じ鍵の行」(種類・相手・対象・結果=人の行は種類と相手だけ)。読むだけ。"""
        N = self.n_rows
        used = self._ms_origin.reshape(self.n, N)[a] >= 0
        rk = self._lg_kind.reshape(self.n, N)[a].astype(np.int64)
        same_or = ((self._lg_object.reshape(self.n, N)[a].astype(np.int64) == ev.obj[:, None])
                   & (self._lg_result.reshape(self.n, N)[a].astype(np.int64) == ev.result[:, None]))
        if any_person:  # 人の行の鍵は (種類, 相手) だけ
            same_or = same_or | person[:, None]
        return (used & (rk == ev.kind[:, None])
                & (self._lg_partner.reshape(self.n, N)[a].astype(np.int64) == ev.partner[:, None]) & same_or)

    def seed_people(self, agent: Any, partner: Any, rel_kind: Any, n: Any, first_ns: Any, last_ns: Any,
                    cell: Any = -1) -> int:
        """〔第 6 期 6-5・人も記憶の一つ〕開始前の経験として人の行を置く(組み立てだけ=系の外・上限なしの腕だけ)→ 行の数。

        最初の関係はデータから(4-1 段 4 の ``w21_relations_initial`` が本体に無い間は、今の関係の層の機械的初期化=W16 の
        世帯と W17 の共在の辺を入れる)。``first_ns``・``last_ns`` は開始前=負の時刻でよい。同じ (体, 相手) は 1 行。
        逐次ループ宣言: なし(体ごとの順位の配列演算・行が足りなければ幅を倍にする回数ぶん)。
        """
        if _G.CURRENT is not None:
            raise RuntimeError("人の行の初期化は組み立て(系の外)だけ")
        if not self.uncapped or self.m1 is None:
            raise RuntimeError("seed_people は人も記憶の一つの腕(上限なし・M1)だけ")
        a = np.asarray(agent, dtype=np.int64).reshape(-1)
        if a.size == 0:
            return 0
        p = np.broadcast_to(np.asarray(partner, dtype=np.int64), a.shape)
        rk = np.broadcast_to(np.asarray(rel_kind, dtype=np.int64), a.shape)
        nn = np.broadcast_to(np.asarray(n, dtype=np.int64), a.shape)
        f0 = np.broadcast_to(np.asarray(first_ns, dtype=np.int64), a.shape)
        f1 = np.broadcast_to(np.asarray(last_ns, dtype=np.int64), a.shape)
        cc = np.broadcast_to(np.asarray(cell, dtype=np.int64), a.shape)
        if bool((self._ms_origin >= 0).any()):
            raise RuntimeError("人の行の初期化はランの始め(器が空)に 1 回だけ")
        key = np.unique(np.stack([a, p], axis=1), axis=0, return_index=True)[1]  # 同じ (体, 相手) は最初の 1 行
        key = np.sort(key)
        a, p, rk, nn, f0, f1, cc = (x[key] for x in (a, p, rk, nn, f0, f1, cc))
        order = np.lexsort((np.arange(a.size), a))
        sa = a[order]
        starts = np.flatnonzero(np.concatenate(([True], sa[1:] != sa[:-1])))
        rank = np.empty(a.size, dtype=np.int64)
        rank[order] = np.arange(a.size) - np.repeat(starts, np.diff(np.append(starts, a.size)))
        if int(rank.max()) >= int(self.caps["person"]):  # 〔検収 M2〕最初の関係も人の行の上限の中
            raise ValueError(f"最初の関係の人の数 {int(rank.max()) + 1} が人の行の上限 {int(self.caps['person'])} を超える"
                             "(入れる側=initial_edges の上限で切る)")
        while int(rank.max()) >= self.n_rows:  # 逐次: 幅を倍にする回数ぶん(幅は max_width まで)
            self._resize(min(2 * self.n_rows, self.max_width))
        g = a * self.n_rows + rank
        self._lg_kind[g] = _M1.PERSON_KIND
        self._lg_partner[g] = p.astype(np.int32)
        self._lg_object[g] = rk.astype(np.int32)
        self._lg_result[g] = 0
        self._lg_cell[g] = cc.astype(np.int32)
        self._ms_ev_t_ns[g] = f1
        self._ms_ev_seq[g] = (-1 - g).astype(np.int32)
        self._ms_log_seq[g] = -1
        self._ms_origin[g] = _LEGACY_CODE
        self._ms_n[g] = np.clip(nn, 1, 65_535).astype(np.uint16)
        self._ms_imp[g] = 0
        self._ms_first_ns[g] = np.minimum(f0, f1)
        self.m1.seed_rows(g, f1)
        self._ms_stats["people_seeded"] += int(g.size)
        return int(g.size)

    def people_rows(self, agent_ids: Any, now_ns: int, *, strength: bool = True,
                    familiar: bool = True) -> tuple[np.ndarray, ...]:
        """〔6-5〕体の配列 → 人の行 ``(相手, 関係の種類, A, 見覚えの A, 行)``(``(体, 幅)``・人でない行は相手 −1・A は −inf)。

        読むだけ(関係の層の読み口=``engine.relations_people``)。〔検収 L3〕``strength=False`` は A を、``familiar=False`` は
        見覚えの A を計算しない(その欄は全部 −inf=相手だけ要る読み口・A だけ要る読み口)。逐次ループ宣言: なし(体 × 幅の
        配列演算)。
        """
        a = np.asarray(agent_ids, dtype=np.int64).reshape(-1)
        N = self.n_rows
        g = a[:, None] * N + np.arange(N)[None, :]
        kind = self._lg_kind[g].astype(np.int64)
        on = (self._ms_origin[g] >= 0) & (kind == _M1.PERSON_KIND)
        partner = np.where(on, self._lg_partner[g].astype(np.int64), -1)
        rel = np.where(on, self._lg_object[g].astype(np.int64), 0)
        A = np.full(g.shape, -np.inf)
        A_fam = np.full(g.shape, -np.inf)
        if bool(on.any()) and self.m1 is not None and (strength or familiar):
            gu = g[on]
            args = (gu, gu // N, int(now_ns), self._ms_n[gu], self._ms_first_ns[gu], self._lg_kind[gu], self._ms_imp[gu])
            if strength:
                A[on] = self.m1.strength(*args)
            if familiar:
                A_fam[on] = self.m1.strength(*args, familiar=True)
        return partner, rel, A, A_fam, np.where(on, g - a[:, None] * N, -1)

    def _check_logged(self, a: np.ndarray, ev: LoggedEvent) -> None:
        """〔2-3〕目印の出来事が記録にあり、``who``=体・``what`` が記憶の種類と合うか(中身の写像)。違えば ``ValueError``。"""
        log = self.body_events.log
        if (ev.seq < 0).any():
            raise ValueError("記録の目印の seq は 0 以上(記録に無い出来事の仮の行は出どころ legacy)")
        pos = log.positions(ev.t_ns, ev.seq)
        if (pos < 0).any():
            j = int(np.flatnonzero(pos < 0)[0])
            raise ValueError(f"記録に無い出来事の id は目印にできない(記録にある出来事の id だけ・いま "
                             f"({int(ev.t_ns[j])}, {int(ev.seq[j])})=記録に無い出来事は出どころ legacy の仮の行)")
        who, what = log.who_what(pos)
        if not np.array_equal(who.astype(np.int64), a):
            raise ValueError("目印の出来事の who が覚える体と違う(体の出来事は本人の記憶にだけ書く)")
        if not np.array_equal(_KIND_OF_CODE[what], ev.kind):
            raise ValueError("目印の出来事の what が記憶の種類と合わない(中身の写像=engine.events.body.kind_of_what)")

    # ------------------------------------------------------------------ 注釈(今の要旨と同じ規則)
    def _drop_note(self, agent: int, row: int) -> None:
        if self._ms_note.pop(agent * self.n_rows + row, None) is not None:
            self._ms_note_order.get(agent, OrderedDict()).pop(row, None)
            if self.cue is not None:  # 〔6-5〕注釈の埋め込みも落とす
                self.cue.drop_rows([agent * self.n_rows + row])

    def _put_note(self, agent: int, row: int, text: str) -> None:
        od = self._ms_note_order.setdefault(agent, OrderedDict())
        od.pop(row, None)
        od[row] = None
        self._ms_note[agent * self.n_rows + row] = text
        while len(od) > GIST_PER_AGENT:  # 体あたり 16 件まで(古い順に落とす)
            old, _ = od.popitem(last=False)
            self._ms_note.pop(agent * self.n_rows + old, None)
            self._ms_stats["notes_dropped"] += 1
            if self.cue is not None:  # 〔6-5〕注釈の埋め込みも落とす
                self.cue.drop_rows([agent * self.n_rows + old])

    def note_cue(self, agent: int, *, heard_by: Sequence[int] = (), heard: str = "", own: str = "") -> None:
        """〔第 6 期 6-5 MR2 問い 4〕手がかりの文を置く(意味の手がかりの腕だけ・会話の番=``MemoryLayer.note_utterance``)。

        ``heard``=話し手の発言(聞き手 ``heard_by`` の「相手の直前の発言」)・``own``=話し手の理由(本人の直前の理由)。
        腕の無い器では何もしない。
        """
        if self.cue is None:
            return
        _check_permit(CUE_PATH, "手がかりの文")
        if heard and heard_by:
            self.cue.note_heard([int(x) for x in heard_by], heard)
        if own:
            self.cue.note_own(int(agent), own)

    # ------------------------------------------------------------------ 書く口 2: 録画
    def mark_shown(self, agent: int, rows: Sequence[int], t_ns: int, *,
                   call: tuple[int, int, int] | None = None) -> tuple[str, ...]:
        """LLM に見せた行の録画(MR16)。``rows`` は描き方が載せた行(``n_rows`` 以上=器の外の行は印を付けない)。

        返り値は ``rows`` と同じ並びの目印の文字列(器の外・空の行は空文字)。``call``(呼び出しの鍵)を渡し、テープに
        列を足すランなら、テープの列へ渡すまで控える(:meth:`take_shown`)。
        """
        _check_permit(SHOWN_PATH, "録画")
        i = int(agent)
        g0 = self.rows_of(i).start
        out: list[str] = []
        for r in rows:  # 見せた行の数ぶん(≤ 3)
            r = int(r)
            g = g0 + r
            if 0 <= r < self.n_rows and self._ms_origin[g] >= 0:
                self._ms_shown_ns[g] = int(t_ns)
                out.append(f"{int(self._ms_ev_t_ns[g])}:{int(self._ms_ev_seq[g])}")
                self._ms_stats["shown_rows"] += 1
            else:
                out.append("")
        ids = tuple(out)
        self._ms_stats["shown_calls"] += 1
        if call is not None and self.tape_on:
            self._ms_tape.setdefault((int(call[0]), int(call[1]), int(call[2])), []).append(ids)
        return ids

    def take_shown(self, call: tuple[int, int, int]) -> tuple[str, ...]:
        """テープの列の値を取り出す(呼び出しの鍵ごとに古い順・無ければ空)。テープの書き手が 1 行ごとに 1 回呼ぶ。"""
        _check_permit(SHOWN_PATH, "録画の控え")
        key = (int(call[0]), int(call[1]), int(call[2]))
        q = self._ms_tape.get(key)
        if not q:
            self._ms_stats["tape_rows_without_shown"] += 1
            return ()
        ids = q.pop(0)
        if not q:
            del self._ms_tape[key]
        self._ms_stats["tape_rows"] += 1
        return ids

    # ------------------------------------------------------------------ 読み口: 想起
    def recall(self, agent: int, t_ns: int, k: int, *, cue: Cue | None = None, pool: ShopPool | None = None,
               tau: float | None = None, cue_text: str | None = None) -> tuple[MemoryView, ...]:
        """1 体の想起 → ``MemoryView`` の組(score の降順・k 件まで)。M0=今の 6b・7c の規則(同値の試験で確かめる)。

        手がかり ``cue`` に一致する行(相手 ∨ 対象 ∨ セル ∨ 直前の結果と同じ種類・結果)のうち ``A ≥ τ`` を score の
        降順に k 件、足りなければ ``A ≥ τ`` の残りから score の順に補う。``pool``(ほかの表の候補=7c の店の行)がある
        ときは同じ score の順に並べ、同じ店の行は先に選んだ方だけ(今の 7c)。計数は :attr:`last_recall`。

        〔第 6 期 6-5〕M1 の腕(:attr:`m1`)は A=M1 の強さ(秒・折衷形・β 込み)・score=A・境目は M1 の τ(``tau`` の引数は
        読まない)・言葉は「はっきり/うろ覚え」。意味の手がかりの腕(:attr:`cue`)は一致を ``cos(手がかりの文, 行の要旨) ≥
        COS_MATCH`` に替え(ID の一致は使わない=意味の手がかりだけの腕)、score に ``W_CTX · cos`` を足す(``cue_text`` が
        無ければ一致 0)。上限なしの腕は人の行を出来事の想起に出さない(人は関係の読み口=``engine.relations_people``)。
        """
        _check_permit(SHOWN_PATH, "想起の計数")
        i = int(agent)
        kk = int(k)
        th = self.tau if tau is None else float(tau)
        r = self.rows_of(i)
        g0, g1 = r.start, r.stop
        used = self._ms_origin[g0:g1] >= 0
        if self.uncapped:  # 〔6-5〕人の行は出来事の想起の外
            used = used & (self._lg_kind[g0:g1] < _M1.PERSON_KIND)
        n_pool = 0 if pool is None else int(np.asarray(pool.score).size)
        if not bool(used.any()) and n_pool == 0:
            object.__setattr__(self, "_ms_last", RecallReport(True, 0, 0, 0, 0, 0, 0, 0))
            return ()
        if self.m1 is not None:  # 〔6-5 M1〕強さ=折衷形(秒)+β・境目=M1 の τ
            th = float(self.m1.tau)
            A = np.full(g1 - g0, -np.inf)
            if bool(used.any()):
                gu = g0 + np.flatnonzero(used)
                A[used] = self.m1.strength(gu, i, int(t_ns), self._ms_n[gu], self._ms_first_ns[gu], self._lg_kind[gu],
                                           self._ms_imp[gu])
            score = A.copy()
        else:
            A = self._activation(g0, g1, int(t_ns) // self.ns_per_step)
            score = self.w_r * A + self.w_i * self._ms_imp[g0:g1]
        kind = self._lg_kind[g0:g1]
        part = self._lg_partner[g0:g1]
        obj = self._lg_object[g0:g1]
        res = self._lg_result[g0:g1]
        cel = self._lg_cell[g0:g1]
        c = Cue() if cue is None else cue
        match = np.zeros(self.n_rows, dtype=bool)
        if int(c.partner) >= 0:
            match |= part == int(c.partner)
        if int(c.obj) >= 0:
            match |= obj == int(c.obj)
        if int(c.cell) >= 0:
            match |= (cel == int(c.cell)) | (obj == int(place_thing(int(c.cell))))
        if int(c.kind) > 0 and 0 <= int(c.result) <= 255:
            match |= (kind == int(c.kind)) & (res == int(c.result))
        if self.cue is not None:  # 〔6-5 MR2〕意味の手がかりだけの腕: 一致=cos ≥ COS_MATCH・score に W_CTX·cos
            from shibuya.engine.memory_embed import COS_MATCH, W_CTX

            _check_permit(CUE_PATH, "手がかりの文の埋め込みの控え")
            cosv = self.cue.cue_cos(np.arange(g0, g1, dtype=np.int64), cue_text)
            if cosv is not None:
                score = score + W_CTX * np.where(used, cosv, 0.0)
                match = cosv >= COS_MATCH
            else:
                match = np.zeros(self.n_rows, dtype=bool)
        # 〔2-3・親の判断 M3〕目印の先が記録の保持窓の外に出た行は本文が無い=手がかりの一致には使わず(要旨と強さだけ)、
        # score の順の補いにだけ出る(LegacyEvent にはしない=目印と出どころはそのまま)
        far = self._beyond_window(g0, g1, int(t_ns))
        match &= used & ~far
        live = used & (A >= th)
        counts = (int(np.count_nonzero(used)), int(np.count_nonzero(used & ~live)),
                  int(np.count_nonzero(match)), int(np.count_nonzero(match & ~live)))
        filled = 0
        dedup = 0
        picked: list[tuple[int, int]] = []  # (0=器の行 / 1=ほかの表, 番号)
        if pool is None:
            cand = np.flatnonzero(match & live)
            cand = cand[np.lexsort((cand, -score[cand]))][:kk]
            picked = [(0, int(j)) for j in cand.tolist()]
            if len(picked) < kk:
                rest = np.flatnonzero(live & ~match)
                rest = rest[np.lexsort((rest, -score[rest]))][: kk - len(picked)]
                filled = int(rest.size)
                picked += [(0, int(j)) for j in rest.tolist()]
        else:
            kd = kind.astype(np.int64)
            shop_like = np.isin(kd, _SHOP_KINDS)
            ob = obj.astype(np.int64)
            ep_key = np.where(shop_like & (ob >= 0) & ~far, ob, -1)
            p_score = np.asarray(pool.score, dtype=np.float64)
            if self.m1 is not None:  # 〔6-5 M1〕店の行は器の外(今の式)=M1 の尺度へは境目の差だけずらして並べる(仮採用)
                p_score = p_score + (float(self.m1.tau) - (self.tau if tau is None else float(tau)))
            p_live = np.asarray(pool.live, dtype=bool)
            p_match = np.asarray(pool.match, dtype=bool)
            p_key = np.asarray(pool.key, dtype=np.int64)

            def order(ep_mask: np.ndarray, st_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
                e = np.flatnonzero(ep_mask)
                s = np.flatnonzero(st_mask)
                sc_ = np.concatenate([score[e], p_score[s]])
                ty = np.concatenate([np.zeros(e.size, dtype=np.int64), np.ones(s.size, dtype=np.int64)])
                ix = np.concatenate([e, s]).astype(np.int64)
                o = np.lexsort((ix, ty, -sc_))
                return ty[o], ix[o]

            keys: set[int] = set()
            for (tys, ixs), is_fill in ((order(match & live, p_match & p_live), False),
                                        (order(live & ~match, p_live & ~p_match), True)):
                for typ, j in zip(tys.tolist(), ixs.tolist()):  # 逐次: k 件で止まる(同じ店の重なりは飛ばす)
                    if len(picked) >= kk:
                        break
                    key = int(ep_key[j]) if typ == 0 else int(p_key[j])
                    if key >= 0 and key in keys:
                        dedup += 1
                        continue
                    picked.append((typ, j))
                    if key >= 0:
                        keys.add(key)
                    if is_fill:
                        filled += 1
        views: list[MemoryView] = []
        for typ, j in picked:  # 高々 k(≤ 3)
            if typ == 1:
                views.append(pool.view(j))  # type: ignore[union-attr]
                continue
            g = g0 + j
            if bool(far[j]):  # 〔M3〕要旨だけ(本文=種類・相手・対象・結果・セルは無い)
                body = {"grain": GRAIN_WORDS[1], "kind": 0, "partner": -1, "obj": -1, "result": 0, "cell": -1}
            else:
                body = {"grain": GRAIN_WORDS[0], "kind": int(kind[j]), "partner": int(part[j]), "obj": int(obj[j]),
                        "result": int(res[j]), "cell": int(cel[j])}
            views.append(MemoryView(
                row=int(j), event_id=(int(self._ms_ev_t_ns[g]), int(self._ms_ev_seq[g])),
                origin=ORIGINS[int(self._ms_origin[g])],
                clarity=(str(_M1.clarity_words(float(A[j]), th)) if self.m1 is not None else clarity_of(float(A[j]), th)),
                annotation=self._ms_note.get(g, ""), when_ns=int(self._ms_ev_t_ns[g]),
                first_ns=int(self._ms_first_ns[g]), **body,
            ))
        object.__setattr__(self, "_ms_last", RecallReport(False, *counts, filled, dedup, len(picked)))
        self._ms_stats["recall_calls"] += 1
        return tuple(views)

    def _beyond_window(self, g0: int, g1: int, now_ns: int) -> np.ndarray:
        """〔第 2 期 2-3・親の判断 M3〕体の行の範囲 → 目印の先(記録の出来事=出どころ None)が記録の保持窓の外に出た行。

        保持窓は記録の ``retention_days``(口が無ければ 1-3 の ``RETENTION_DAYS``)。日の締め ``close_day(d)`` が
        ``(d + 1 − 窓)`` 日より前の行を落とすので、日 D の中では ``D − 窓`` 日より前の日の出来事が窓の外。時刻だけから決まる
        (記録の中身を見ない)=再開しても通しと同じ。仮の行(legacy)は対象の外。逐次ループ宣言: なし(配列演算)。
        """
        days = int(self.body_events.log.retention_days) if self.body_events is not None else int(RETENTION_DAYS)
        cut = (int(now_ns) // NS_PER_DAY - days) * NS_PER_DAY
        return (self._ms_origin[g0:g1] == _LOG_CODE) & (self._ms_ev_t_ns[g0:g1] < cut)

    # ------------------------------------------------------------------ 再開: 記憶の表から作り直す
    def rebuild(self, kind: np.ndarray, first_step: np.ndarray, last_step: np.ndarray, cell: np.ndarray,
                partner: np.ndarray, obj: np.ndarray, result: np.ndarray, importance: np.ndarray, n: np.ndarray,
                notes: dict[tuple[int, int], str], note_order: dict[int, "OrderedDict[int, None]"]) -> int:
        """今の記憶の表(``(体, n_rows)`` の配列)と要旨から器を作り直す(再開のとき・状態台帳の行 M0=作り直せる)。

        器の行は全部が記憶の表の写しなので、行・中身・強さ・注釈は同じ値に戻る。仮の行(legacy)の目印の seq は番地から
        決まる。〔2-3〕記録の目印の行は、戻した記録の目印の seq(``_ms_log_seq``=状態台帳の腕の行 M0L)から目印と出どころを
        戻す(通しのランと同じ目印=先の出来事は再開のランの記録に無い=記録は discardable)。書くのは行 M0 の欄だけ(録画・
        控え・計数=行 M0R と、記録の目印の seq=行 M0L は触らない=再開の器の録画は空から始まる)。系の中(ランの途中)では
        呼べない。→ 行の数。
        """
        if _G.CURRENT is not None:
            raise RuntimeError(f"記憶の器の作り直しは再開の組み立て(系の外)だけ(いまの系 {_G.CURRENT})")
        if self.uncapped or self.grain != _M1.GRAIN_EACH:
            raise RuntimeError("〔6-5〕上限なしの腕(--memory-people memory)と粒度 day の腕(--memory-grain day)のランは再開に"
                               "対応しない(器が記憶の表の写しでない=表から作り直せない・本段の限界=記録 mr65/README.md)")
        _check_permit(ROW_PATH, "行の作り直し")
        N = self.n_rows
        shape = (self.n, N)
        kd = np.asarray(kind)
        if kd.shape != shape:
            raise ValueError(f"記憶の表の形 {kd.shape} が器 {shape} と違う")
        used = (kd != 0).reshape(-1)
        g = np.flatnonzero(used)
        for name, _dt, fill in _ROW_COLS + _LEGACY_COLS:
            if name not in _SHOWN_COLS:  # 行 M0 の列だけ(録画の列は行 M0R)
                getattr(self, name)[:] = fill
        self._lg_kind[g] = kd.reshape(-1)[g]
        self._lg_partner[g] = np.asarray(partner).reshape(-1)[g]
        self._lg_object[g] = np.asarray(obj).reshape(-1)[g]
        self._lg_result[g] = np.asarray(result).reshape(-1)[g]
        self._lg_cell[g] = np.asarray(cell).reshape(-1)[g]
        self._ms_ev_t_ns[g] = np.asarray(last_step, dtype=np.int64).reshape(-1)[g] * self.ns_per_step
        self._ms_ev_seq[g] = (-1 - g).astype(np.int32)
        self._ms_n[g] = np.asarray(n).reshape(-1)[g]
        self._ms_imp[g] = np.asarray(importance).reshape(-1)[g]
        self._ms_first_ns[g] = np.asarray(first_step, dtype=np.int64).reshape(-1)[g] * self.ns_per_step
        self._ms_origin[g] = _LEGACY_CODE
        ls = self._ms_log_seq[g].astype(np.int64)
        lg = ls >= 0
        if bool(lg.any()):  # 〔2-3〕記録の目印の行(戻した行 M0L の seq)
            self._ms_ev_seq[g[lg]] = ls[lg].astype(np.int32)
            self._ms_origin[g[lg]] = _LOG_CODE
        self._ms_note.clear()
        self._ms_note_order.clear()
        for agent, od in note_order.items():  # 注釈の件数ぶん(体あたり ≤ 16)
            new = self._ms_note_order.setdefault(int(agent), OrderedDict())
            for row in od:
                text = notes.get((int(agent), int(row)))
                if text is not None:
                    new[int(row)] = None
                    self._ms_note[int(agent) * N + int(row)] = text
        if self.cue is not None:  # 〔6-5〕要旨の埋め込みを作り直す(行 M0C の hash_skip の欄)
            self.cue.rebuild(dict(self._ms_note))
        return int(g.size)

    # ------------------------------------------------------------------ 実行時の検査(器=記憶の表の写し)
    def check_against_table(self, agent: np.ndarray, rows: np.ndarray, *, kind: np.ndarray, partner: np.ndarray,
                            obj: np.ndarray, result: np.ndarray, cell: np.ndarray, first_step: np.ndarray,
                            last_step: np.ndarray, n: np.ndarray, importance: np.ndarray,
                            log_seq: np.ndarray | None = None, kept: np.ndarray | None = None) -> None:
        """書いた行の器の値が記憶の表の値と同じかを配列で比べ、違えば ``RuntimeError``(読むだけ・M0 の宣言の前提)。

        比べるのは中身(種類・相手・対象・結果・セル)・強さ(回数・重要度・最初の時刻)・目印(最後の時刻と seq)・出どころ。
        ``log_seq`` を渡さないときは仮の行(seq=−1−番地・出どころ legacy・記録の seq −1)、渡すときは記録の目印の行
        (seq=記録の seq・出どころ None)=〔2-3〕。書きの検査の切替口(``SHIBUYA_WRITE_GUARD``)でも外さない(器の値は
        ハッシュに入らない=ずれても final とハッシュに出ないので、ここで止める)。逐次ループ宣言: なし(配列演算)。

        〔第 6 期 6-5・粒度 day〕``kept`` の行(記録に書かなかった日の中の 2 回目から)は目印を前のまま=目印の時刻は表の
        最後の時刻以前で同じ日・出どころは記録・目印の seq は記録の seq(0 以上)と同じ、を確かめる(表の最後の時刻とは比べない)。
        """
        a = np.asarray(agent, dtype=np.int64)
        g = a * self.n_rows + np.asarray(rows, dtype=np.int64)
        ns = self.ns_per_step
        kp = np.zeros(g.size, dtype=bool) if kept is None else np.asarray(kept, dtype=bool)
        w = ~kp
        last_ns = np.asarray(last_step, dtype=np.int64) * ns
        lseq = None if log_seq is None else np.asarray(log_seq, dtype=np.int64)
        pairs = (
            ("種類", self._lg_kind[g], kind), ("相手", self._lg_partner[g], partner), ("対象", self._lg_object[g], obj),
            ("結果", self._lg_result[g], result), ("セル", self._lg_cell[g], cell), ("回数", self._ms_n[g], n),
            ("重要度", self._ms_imp[g], importance),
            ("最初の時刻", self._ms_first_ns[g], np.asarray(first_step, dtype=np.int64) * ns),
            ("目印の時刻", self._ms_ev_t_ns[g][w], last_ns[w]),
            ("目印の seq", self._ms_ev_seq[g][w], (-1 - g if lseq is None else lseq)[w]),
            ("出どころ", self._ms_origin[g], np.full(g.size, _LEGACY_CODE if log_seq is None else _LOG_CODE)),
            ("記録の seq", self._ms_log_seq[g][w], (np.full(g.size, -1) if lseq is None else lseq)[w]),
        )
        bad = [name for name, got, want in pairs
               if not np.array_equal(np.asarray(got).astype(np.int64), np.asarray(want).astype(np.int64))]
        if bool(kp.any()):  # 〔6-5 粒度 day〕前のままの目印
            gk = g[kp]
            t_k = self._ms_ev_t_ns[gk]
            if not (bool((t_k <= last_ns[kp]).all()) and bool((t_k // NS_PER_DAY == last_ns[kp] // NS_PER_DAY).all())
                    and bool((self._ms_ev_seq[gk] == self._ms_log_seq[gk]).all())
                    and bool((self._ms_log_seq[gk] >= 0).all())):
                bad.append("前のままの目印(粒度 day)")
        if bad:
            raise RuntimeError(f"1-6 M0: 記憶の器の値が記憶の表と食い違う({'・'.join(bad)})=器は表の写し")

    # ------------------------------------------------------------------ 計器
    def summary(self) -> dict[str, Any]:
        """manifest ``memory_summary.memory_store``: 腕の名・行数・出どころの分布・録画(計器)。"""
        o = self._ms_origin
        used = o >= 0
        per = used.reshape(self.n, self.n_rows).sum(axis=1) if self.n else np.zeros(0, dtype=np.int64)
        by = np.bincount(o[used].astype(np.int64), minlength=len(ORIGINS))
        return {
            "arm": ARM_EVENTS,
            "n_rows": int(self.n_rows),
            "row_bytes": int(ROW_BYTES),
            "legacy_row_bytes": int(LEGACY_BYTES),
            "rows": int(np.count_nonzero(used)),
            "agents_with_rows": int(np.count_nonzero(per > 0)),
            "origins": {_ORIGIN_NAMES[k]: int(by[k]) for k in range(len(ORIGINS))},
            "annotations": int(len(self._ms_note)),
            "shown_rows_live": int(np.count_nonzero(used & (self._ms_shown_ns >= 0))),
            "tape_pending": int(sum(len(v) for v in self._ms_tape.values())),
            "counts": self.store_counts,
            # 〔2-3〕記録の目印の行のうち、いまの記録に先がある行/無い行(再開のランは前の日の出来事が記録に無い・保持窓の外)
            **self._log_targets(used),
            # 〔第 6 期 6-5〕腕の計器(腕の立ったランだけ=M0 の器だけのランの葉は前と同じ)
            **self._mr65_summary(used, per),
        }

    def _mr65_summary(self, used: np.ndarray, per: np.ndarray) -> dict[str, Any]:
        """〔6-5〕manifest ``memory_summary.memory_store.mr65``(観測・腕の立ったランだけ)。"""
        if self.m1 is None and self.cue is None and not self.uncapped and self.grain == _M1.GRAIN_EACH:
            return {}
        kind = self._lg_kind.astype(np.int64)
        person = used & (kind == _M1.PERSON_KIND)
        pp = person.reshape(self.n, self.n_rows).sum(axis=1) if self.n else np.zeros(0, dtype=np.int64)
        arms = _M1.arms()
        out: dict[str, Any] = {
            "arms": {"model": _M1.MODEL_M1 if self.m1 is not None else _M1.MODEL_M0,
                     "cue": _M1.CUE_EMBED if self.cue is not None else _M1.CUE_ID,
                     "people": _M1.PEOPLE_MEMORY if self.uncapped else _M1.PEOPLE_TABLE,
                     "embed_model": self.cue.model if self.cue is not None else None,
                     "grain": self.grain, "env_at_summary": arms._asdict()},
            "rows_per_agent_max": int(per.max()) if per.size else 0,
            "uncapped": bool(self.uncapped),
            # 「LLM が覚えていないのに話を合わせた割合」(MR6 の 5・値は実 LLM の後=None)
            "played_along_share": None,
        }
        if self.m1 is not None:
            out["m1"] = self.m1.summary(used)
        if self.cue is not None:
            out["cue"] = self.cue.summary()
        if self.uncapped:
            out["people"] = {"rows": int(np.count_nonzero(person)), "agents": int(np.count_nonzero(pp > 0)),
                             "per_agent_max": int(pp.max()) if pp.size else 0,
                             "per_agent_mean": round(float(pp.mean()), 4) if pp.size else 0.0}
            ep = (used & (kind != _M1.PERSON_KIND)).reshape(self.n, self.n_rows).sum(axis=1) if self.n else pp
            st = self._ms_stats
            # 〔検収 M2〕器の行の幅・上限・消した行(忘れた/上限で A の一番低い行)・行のバイト(39 万体の見積りの素)
            out["capacity"] = {
                "width": int(self.n_rows), "width_max": int(self.max_width), "caps": dict(self.caps),
                "episode_per_agent_max": int(ep.max()) if ep.size else 0,
                "rows_resized": int(st.get("rows_resized", 0)), "forgotten": int(st.get("forgotten", 0)),
                "evicted_by_a": int(st.get("evicted_by_a", 0)),
                "evicted_by_a_episode": int(st.get("evicted_by_a:episode", 0)),
                "evicted_by_a_person": int(st.get("evicted_by_a:person", 0)),
                "row_bytes": int(ROW_BYTES + LEGACY_BYTES + LOG_SEQ_BYTES
                                 + (8 * int(self.m1.k) if self.m1 is not None else 0)),
            }
            if self.shops is not None:
                out["shops"] = self.shops.summary()
        return {"mr65": out}

    def arms_config(self) -> dict[str, Any]:
        """〔検収 L1〕manifest の設定の節 ``memory_summary.mr65_arms``(腕の名・埋め込みのモデルの名と版・行の上限)。
        既定の腕の器は空(欄を出さない)。"""
        return {k: (dict(v) if isinstance(v, Mapping) else v) for k, v in self.arms_cfg.items()}

    def _log_targets(self, used: np.ndarray) -> dict[str, int]:
        """〔2-3〕manifest の 2 欄: 記録の目印の行(出どころ None)のうち先がいまの記録にある行(``targets_log_live``)と無い行
        (``targets_log_gone``)。器に口が無いランは両方 0。逐次ループ宣言: なし(記録の位置の二分探索=時刻の種類の数ぶん)。"""
        g = np.flatnonzero(used & (self._ms_origin == _LOG_CODE))
        if g.size == 0 or self.body_events is None:
            return {"targets_log_live": 0, "targets_log_gone": int(g.size)}
        pos = self.body_events.log.positions(self._ms_ev_t_ns[g], self._ms_ev_seq[g].astype(np.int64), verify=False)
        live = int(np.count_nonzero(pos >= 0))
        return {"targets_log_live": live, "targets_log_gone": int(g.size) - live}


# ================================================================ 描き方(今の B5「記憶」の 1 行と同じバイト)
#: 〔第 6 期 6-5〕言葉の描き方の口(``words=True``)の項の頭(「うろ覚え」と「要旨だけ」=未リサーチ(expedient)の表記)。
WORD_PREFIX: Final[Mapping[str, str]] = MappingProxyType({CLARITY_WORDS[1]: "(うろ覚え)", GRAIN_WORDS[1]: "(要旨だけ)"})


def render_memories(views: Sequence[MemoryView], *, clock: Callable[[int], datetime], poi_names: Sequence[str],
                    place_ids: Sequence[str], now_ns: int = 0, ns_per_step: int = NS_PER_STEP,
                    words: bool = False) -> str:
    """``MemoryView`` の組 → B5「記憶」の 1 行(今の描き方=``perception.renderer`` の項と行の組み立て・テンプレ v1.3)。

    ``clock`` は刻みの番号 → 世界内日時(描画の ``clock_fn`` と同じ口)。項の時刻は ``when_ns``(最後の回)、負なら
    ``now_ns``。チャネル 60 tok で末尾の項から落とす所までが描き方(個体枠 300 との突き合わせは描画の側=B5・B6 の
    本文が要る)。M0 の言葉は全部「はっきり」・粗さは「そのまま」(今のテンプレには言葉の欄が無い)。それ以外は
    ``ValueError``(描き方は M1 以降で決める)。0 件は空文字。

    〔第 6 期 6-5〕``words=True``(M1 の言葉の描き方の口=MR-0): 「うろ覚え」と「要旨だけ」の項の頭に :data:`WORD_PREFIX` を
    付ける(「はっきり・そのまま」の項は M0 と同じバイト)。今の描画(``perception.renderer``)には結線していない=LLM に
    言葉を見せるのは描画の側の 1 か所(テンプレの版が動く=親の判断・記録 mr65/README.md)。
    """
    from shibuya.agents.state import RESULT_TEXT
    from shibuya.perception import normalize as _N
    from shibuya.perception.renderer import compose_memory_line, memory_item_text

    texts: list[str] = []
    for v in views:  # 想起の件数ぶん(≤ 3)
        if not words and (v.clarity != CLARITY_WORDS[0] or v.grain != GRAIN_WORDS[0]):
            raise ValueError(f"M0 の描き方は「{CLARITY_WORDS[0]}・{GRAIN_WORDS[0]}」だけ(いま {v.clarity}・{v.grain})")
        if v.clarity not in CLARITY_WORDS or v.grain not in GRAIN_WORDS:
            raise ValueError(f"言葉は {CLARITY_WORDS}・粗さは {GRAIN_WORDS} のどれか(いま {v.clarity}・{v.grain})")
        when = int(v.when_ns) if int(v.when_ns) >= 0 else int(now_ns)
        h, m = _N.format_time(clock(when // int(ns_per_step)))
        head = WORD_PREFIX.get(v.clarity, "") + WORD_PREFIX.get(v.grain, "")
        texts.append(head + memory_item_text(to_item(v, ns_per_step), hhmm=f"{h}:{m}", poi_names=poi_names,
                                             place_ids=place_ids, result_text=RESULT_TEXT))
    return compose_memory_line(texts)[0]
