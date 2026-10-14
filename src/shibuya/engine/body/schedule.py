"""engine.body.schedule — TM5「次に段階の境目を越える時刻を予約」の口(第 3 期 3-5・腕 ``--body-schedule``)。

正: 決定 10-12 §4-2 TM5((c) 体の変化(空腹・疲れ)は次に段階の境目を越える時刻を予約する・「全員を毎回見る版」と一致する
ことを受入の条件にする)・TM6 の T3(何かあった人だけ=まず一致の確認)・計画 10-12 の 3-5 の行(T3 で有効=今は既定 off)。

腕(切替口): ``--body-schedule {sweep,reserve}``(環境変数 ``SHIBUYA_BODY_SCHEDULE``・:func:`set_arm`)。既定 ``sweep``=
今の毎刻みの全員の走査。``reserve``=体ごとに「次に段の境目を越える刻み」を見込んで予約の列(``engine.scheduler.Scheduler``
=1 分のバケットを流用)に置き、予約の刻みに来た体と、前の体の刻みから入力が変わった体だけを規則に通す。腕は組み立ての
ときに読む(``run_day`` の引数にしない=設定の指紋に入れない=近接・在席の腕と同じ扱い)。結果は sweep と同じでなければ
ならない(受入=byte-check 19 構成で final・テープ・段の境目の列が同じ)。予約の列は状態台帳の行 ``BD``(軸 1 diag・
軸 2 discardable=再開では状態から引き直す。下界の予約なので引き直した列は通しの列と違ってよい=結果は同じ)。

段の境目(予約する変化):

- 疲れ(0〜10 の目盛の 1 つずつ): 体の刻み(30 刻みごと)に +1(上限 10)・就寝中は −2、休みの刻み(10 刻みごと)に休んで
  いる体は −1。変わらない体=起きていて 10・就寝中で 0・休みでない(→ 予約なし=入力が変わるまで見ない)。
- 空腹 v1(0〜10 の目盛): 体の刻みに +1(10 で止まる)。
- 空腹(エネルギー収支): 語の段(満腹/ふつう/空腹/とても空腹)の次の境目=食後の消費が ``区切り × EER/3`` を越える刻み
  (:func:`engine.body.rules.steps_to_hunger_edge`)。予約は浮動小数の積み上げの誤差の幅+2 刻みだけ早める(早い予約は
  境目の手前で空振りして引き直す=値は sweep と同じ。遅い予約は値を変える=負の対照)。
- 暑さ(体感温度 0〜10): その日の 5 分の窓 × セルの体感温度の表(``EnvironmentProcess.felt_day_table``)から、体のいるセル
  の値が次に変わる窓。表が替わる(日の頭・天気の日付の差し替え)と全員を見直す。

引き直しの条件(仮採用・:data:`RESERVE_EXPEDIENTS` の 1): 前に規則に通した後の写しと比べて、活動・活動の種別と期限・
1 刻みの消費(活動と乗車の状態から来る METs)・空腹・疲れ・食後の消費(食事と軽食)が違う体は、その刻みで規則に通して
予約を引き直す。体感温度はセル(移動)が違う体。活動を書く口が resolve に約 40 か所あり 1 つの口が無いため、口ごとの
知らせでなく写しとの比べで見つける(T3 で口の知らせに替える候補)。

エネルギーの積み上げ(食後の消費・収支)は全員を毎刻み配列で足す(:data:`RESERVE_EXPEDIENTS` の 2=float32 の足し算の順を
変えると値が 1 ulp 動く=予約するのは段の写しの更新だけ)。

逐次ループ宣言(P4・腕 reserve のときだけ):

1. 予約の列(``Scheduler.schedule_many``)は**相異なる予約の刻みの数**ぶん(≤ 1 日の刻みの数・体数に比例しない)。
2. 予約の取り出しは**前の取り出しから進んだ刻み/窓の数**ぶん(内受容=ふつう 1・エネルギー収支の無いランは体の刻みの
   周期まで・体感温度=ふつう 1)。
体数に比例する Python のループは無い(写しの比べ・規則・見込みは配列演算)。
"""

from __future__ import annotations

import functools
import hashlib
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Final

import numpy as np

from shibuya.agents.state import Activity
from shibuya.engine.scheduler import COL_AGENT, COL_SEQ, Scheduler
from shibuya.engine.body import rules as BR
from shibuya.engine.energy import HUNGER_RATIO_EDGES

__all__ = [
    "ARM_SWEEP", "ARM_RESERVE", "ARMS", "DEFAULT_ARM", "arm", "set_arm", "RESERVE_EXPEDIENTS", "NEVER",
    "next_intero_steps", "next_felt_frames", "BodySchedule", "BOUNDARY_KINDS",
]

ARM_SWEEP: Final[str] = "sweep"
ARM_RESERVE: Final[str] = "reserve"
ARMS: Final[tuple[str, ...]] = (ARM_SWEEP, ARM_RESERVE)
#: 既定(T3 までは sweep=今の毎刻みの全員の走査)。
DEFAULT_ARM: Final[str] = ARM_SWEEP
#: 予約しない(次の境目が無い=入力が変わるまで見ない)。
NEVER: Final[int] = int(np.iinfo(np.int64).max)
#: 段の境目の列の種類(記録の並び=この順)。
BOUNDARY_KINDS: Final[tuple[str, ...]] = ("hunger", "fatigue", "thermal")

#: 予約の口の近似の宣言(つなぎの台帳の ``BR-BODY-RESERVE-*`` の 2 行と 1 対 1)。
RESERVE_EXPEDIENTS: Final[tuple[str, ...]] = (
    "TM5 の予約の引き直しは、前に規則に通した後の写し(活動・活動の種別と期限・1 刻みの消費・空腹・疲れ・食後の消費・"
    "体感温度はセル)との比べで見つける(活動を書く口が resolve に約 40 か所あり 1 つの口が無い=T3 で口の知らせに替える候補)",
    "TM5 の予約の腕でも、エネルギーの積み上げ(食後の消費・収支)は全員を毎刻み配列で足す(float32 の足し算の順を変えると値が"
    "動く=予約するのは段の写しの更新だけ・閉じた式の積み上げは T3 の版上げの候補)",
)

_ARM: str = os.environ.get("SHIBUYA_BODY_SCHEDULE", DEFAULT_ARM).strip().lower() or DEFAULT_ARM
if _ARM not in ARMS:
    raise ValueError(f"SHIBUYA_BODY_SCHEDULE は {ARMS} のどれか(いま {_ARM!r})")


def arm() -> str:
    """いまの腕(``sweep``=既定・``reserve``=TM5 の予約)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--body-schedule``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--body-schedule は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def _next_multiple(now: int, period: int) -> int:
    return (int(now) // int(period) + 1) * int(period)


def next_intero_steps(now: int, *, f: np.ndarray, h: np.ndarray, act: np.ndarray, kind: np.ndarray | None,
                      until: np.ndarray | None, activity_columns: bool, energy: Any = None,
                      since: np.ndarray | None = None, eer: np.ndarray | None = None,
                      spent: np.ndarray | None = None) -> np.ndarray:
    """規則に通した直後(刻み ``now``)の値から、次に空腹か疲れが変わりうる最初の刻み(``int64``・無ければ :data:`NEVER`)。

    下界(これより前には変わらない)を返す。入力(活動・種別・期限・消費・値)が変わらない限り成り立つ。
    """
    nb = _next_multiple(now, BR.BODY_TICK_PERIOD)
    f = np.asarray(f)
    sleeping = np.asarray(act) == int(Activity.SLEEPING)
    body_change = np.where(sleeping, f > 0, f < BR.INTERO_MAX)
    out = np.where(body_change, nb, NEVER).astype(np.int64)
    if activity_columns and kind is not None and until is not None:
        nr = _next_multiple(now, BR.ACTIVITY_REST_PERIOD_TICKS)
        rest_change = BR.resting(np.asarray(act), np.asarray(kind), np.asarray(until), nr) & (f > 0)
        out = np.minimum(out, np.where(rest_change, nr, NEVER))
    if energy is None:
        out = np.minimum(out, np.where(np.asarray(h) < BR.INTERO_MAX, nb, NEVER))
    else:
        j = BR.steps_to_hunger_edge(since, eer, spent)
        meal = np.maximum(np.asarray(eer, dtype=np.float32), np.float32(1e-3)) / np.float32(3.0)
        # 余白=float32 の積み上げの誤差の上限(1 回の足し算で境目の値の ulp の半分 × 刻みの数 ÷ 1 刻みの消費)+2 刻み
        ulp = np.spacing((meal * np.float32(HUNGER_RATIO_EDGES[-1])).astype(np.float32)).astype(np.float64)
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            err = np.where(np.isfinite(j), j * ulp / np.maximum(np.asarray(spent, dtype=np.float64), 1e-12), 0.0)
        margin = 2.0 + np.ceil(err)
        lead = np.where(np.isfinite(j), np.maximum(j - margin, 1.0), np.inf)
        hit = np.isfinite(lead)
        h_at = np.full(lead.shape, NEVER, dtype=np.int64)
        h_at[hit] = int(now) + lead[hit].astype(np.int64)
        out = np.minimum(out, h_at)
    return out


def next_felt_frames(frame: int, cols: np.ndarray, nxt: np.ndarray) -> np.ndarray:
    """窓 ``frame`` の次に、列 ``cols`` の体感温度が変わる窓(``int64``・その日の中に無ければ :data:`NEVER`)。"""
    nf = nxt[int(frame), np.asarray(cols, dtype=np.int64)].astype(np.int64)
    return np.where(nf < nxt.shape[0], nf, NEVER)


def _next_change_table(table: np.ndarray) -> np.ndarray:
    """体感温度の表(窓 × 列)→ 各窓の後で値が最初に変わる窓(無ければ窓の数)。逐次: 窓の数ぶん(表を作る時 1 回)。"""
    n_f = int(table.shape[0])
    out = np.full(table.shape, n_f, dtype=np.int32)
    for f in range(n_f - 2, -1, -1):  # 逐次ループ宣言: 1 日の窓の数ぶん(288)・表が替わったときだけ
        out[f] = np.where(table[f + 1] != table[f], f + 1, out[f + 1])
    return out


def _writing(fn: Callable[..., Any]) -> Callable[..., Any]:
    """``BodySchedule`` の書く口の印: 呼んでいる間だけ欄の付け替えと持ち主の配列の書きを開ける(出るときに閉じる)。"""

    @functools.wraps(fn)
    def _enter_port_and_call(self: "BodySchedule", *a: Any, **k: Any) -> Any:
        if self.__dict__.get("_port_active"):
            return fn(self, *a, **k)
        object.__setattr__(self, "_port_active", True)
        for arr in self._own_arrays():
            arr.setflags(write=True)
        try:
            return fn(self, *a, **k)
        finally:
            for arr in self._own_arrays():
                arr.setflags(write=False)
            object.__setattr__(self, "_port_active", False)

    return _enter_port_and_call


@dataclass
class BodySchedule:
    """体の層の予約の列(状態台帳の行 ``BD`` の中身)。

    中身は 2 本: 内受容(空腹・疲れ=体の刻み)と体感温度(5 分の窓)。それぞれ予約の列(``Scheduler``・刻み/窓の
    バケット)・体ごとの生きている予約の通し番号(古い予約は取り出す時に落とす)・予約の刻み/窓・引き直しの写し。

    - 〔3-5 検収 M1〕体ごとの配列(通し番号・刻み/窓・列・写し)は**腕 reserve のときだけ**作る。腕 sweep は長さ 0 のまま
      (状態台帳の行 ``BD`` の大きさの宣言「腕 sweep: 計器だけ」のとおり)。
    - 〔3-5 検収 L7〕実行時の守り: 欄の付け替えと消去は書く口(``reset``・``intero_due``・``intero_plan``・
      ``intero_snapshot``・``felt_due``・``felt_new_table``・``felt_plan``=印 ``_writing``)の中だけ。持ち主の配列は口の外では
      読み取り専用(``setflags(write=False)``)。書く口を呼ぶのは ``BodyModel`` の ``step`` と ``initial`` だけ(AST の試験)。
      予約の列の中(``Scheduler``)と、環境の過程の物の日の表 ``felt_table``(参照)は守りの外。
    """

    n: int
    arm: str
    intero: Scheduler | None = None
    intero_seq: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    intero_at: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    intero_snap: dict[str, np.ndarray] = field(default_factory=dict)
    intero_primed: bool = False
    felt: Scheduler | None = None
    felt_seq: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    felt_at: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    felt_col: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.int64))
    felt_table: np.ndarray | None = None
    felt_next: np.ndarray | None = None
    felt_serial: int = -1
    #: 書く口の中か(``_writing`` が開け閉めする・最後の欄=組み立ての中は開いている)。
    _port_active: bool = False

    def __post_init__(self) -> None:
        for arr in self._own_arrays():
            arr.setflags(write=False)

    def __setattr__(self, name: str, value: Any) -> None:
        if self.__dict__.get("_port_active", True):  # 組み立ての中(まだ _port_active が無い)と書く口の中だけ
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"予約の列の欄 {name} は書く口の外では付け替えられない")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"予約の列の欄 {name} は消せない")

    def _own_arrays(self) -> list[np.ndarray]:
        """持ち主の配列(守る物)。日の表 ``felt_table`` は環境の過程の物(参照)なので入れない。"""
        out = [self.intero_seq, self.intero_at, self.felt_seq, self.felt_at, self.felt_col]
        out += list(self.intero_snap.values())
        if self.felt_next is not None:
            out.append(self.felt_next)
        return out

    @property
    def reserve(self) -> bool:
        return self.arm == ARM_RESERVE

    @_writing
    def reset(self) -> None:
        """全部を空に戻す(刻み 0 の体の状態を置いたとき=次の刻みで全員を規則に通す)。体ごとの配列は腕 reserve だけ。"""
        n = int(self.n) if self.reserve else 0
        self.intero = None
        self.intero_seq = np.full(n, -1, dtype=np.int64)
        self.intero_at = np.full(n, -1, dtype=np.int64)
        self.intero_snap = {}
        self.intero_primed = False
        self.felt = None
        self.felt_seq = np.full(n, -1, dtype=np.int64)
        self.felt_at = np.full(n, -1, dtype=np.int64)
        self.felt_col = np.full(n, -1, dtype=np.int64)
        self.felt_table = None
        self.felt_next = None
        self.felt_serial = -1

    # ------------------------------------------------------------------ 内受容
    @_writing
    def intero_due(self, now: int) -> np.ndarray:
        """刻み ``now`` までに予約の来た体(前に取り出した刻みの次から ``now`` まで・生きている予約だけ・並びは問わない=
        体ごとに生きている予約は 1 つなので重ならない)。バケットは消化する。体の刻みを飛ばす刻み(エネルギー収支の無いランの
        体の刻みでも休みの刻みでもない刻み)に置いた予約(早めた予約)も落とさない。"""
        if self.intero is None:
            return np.zeros(0, dtype=np.int64)
        got = []
        for s in range(self.intero.base_tick, int(now) + 1):  # 逐次: 前の取り出しから進んだ刻みの数(≤ 体の刻みの周期)
            ev = self.intero.events_at(s).events
            self.intero.consume(s)
            if ev.shape[0]:
                a = ev[:, COL_AGENT]
                got.append(a[self.intero_seq[a] == ev[:, COL_SEQ]])
        return np.concatenate(got) if got else np.zeros(0, dtype=np.int64)

    def intero_changed(self, r: Any, *, activity_columns: bool, spent: np.ndarray | None) -> np.ndarray:
        """前に規則に通した後の写しと入力が違う体(bool)。写しが無い(最初・再開)なら全員。"""
        s = self.intero_snap
        if not self.intero_primed or not s:
            return np.ones(int(self.n), dtype=bool)
        ch = (r.activity != s["act"]) | (r.fatigue != s["f"]) | (r.hunger != s["h"])
        if activity_columns:
            ch |= (r.activity_kind != s["kind"]) | (r.activity_until != s["until"])
        if spent is not None:
            ch |= (spent != s["rate"]) | (r.since_meal_kcal != s["since"])
        return ch

    @_writing
    def intero_plan(self, now: int, ids: np.ndarray, at: np.ndarray) -> int:
        """体 ``ids`` の次の予約を ``at`` に置き直す(:data:`NEVER` は予約なし)。置いた件数を返す。"""
        ids = np.asarray(ids, dtype=np.int64)
        at = np.asarray(at, dtype=np.int64)
        if self.intero is None:
            self.intero = Scheduler(start_tick=int(now) + 1)
        self.intero_seq[ids] = -1
        self.intero_at[ids] = -1
        ok = at != NEVER
        if not ok.any():
            return 0
        seq = self.intero.schedule_many(ids[ok], at[ok])
        self.intero_seq[ids[ok]] = seq
        self.intero_at[ids[ok]] = at[ok]
        return int(np.count_nonzero(ok))

    @_writing
    def intero_snapshot(self, r: Any, ids: np.ndarray | None, *, f: np.ndarray, h: np.ndarray,
                        activity_columns: bool, spent: np.ndarray | None, since: np.ndarray | None) -> None:
        """規則に通した体 ``ids``(None=全員)の写しを置く。``f``・``h`` は書いた後の値(``ids`` の並び)。
        食後の消費は足した後の全員の値(全員が毎刻み動く)。"""
        n = int(self.n)
        s = self.intero_snap
        if not s:
            s["act"] = np.zeros(n, dtype=np.int8)
            s["f"] = np.zeros(n, dtype=np.uint8)
            s["h"] = np.zeros(n, dtype=np.uint8)
            if activity_columns:
                s["kind"] = np.zeros(n, dtype=np.int8)
                s["until"] = np.zeros(n, dtype=np.int32)
            if spent is not None:
                s["rate"] = np.zeros(n, dtype=np.float32)
                s["since"] = np.zeros(n, dtype=np.float32)
        sel = slice(None) if ids is None else np.asarray(ids, dtype=np.int64)
        s["act"][sel] = r.activity[sel]
        s["f"][sel] = f
        s["h"][sel] = h
        if activity_columns:
            s["kind"][sel] = r.activity_kind[sel]
            s["until"][sel] = r.activity_until[sel]
        if spent is not None:
            s["rate"][sel] = spent[sel]
            s["since"][:] = since
        self.intero_primed = True

    # ------------------------------------------------------------------ 体感温度
    @_writing
    def felt_due(self, serial: int) -> np.ndarray:
        """窓の通し番号 ``serial`` までに予約の来た体(前の窓の次から・生きている予約だけ・並びは問わない=重ならない)。
        取り出した窓の通し番号を覚える(同じ窓の 2 回目は予約の来た体なし)。"""
        if self.felt is None or serial <= self.felt_serial:
            return np.zeros(0, dtype=np.int64)
        got = []
        for s in range(max(self.felt.base_tick, self.felt_serial + 1), int(serial) + 1):  # 逐次: 進んだ窓の数(ふつう 1)
            ev = self.felt.events_at(s).events
            self.felt.consume(s)
            if ev.shape[0]:
                a = ev[:, COL_AGENT]
                got.append(a[self.felt_seq[a] == ev[:, COL_SEQ]])
        self.felt_serial = int(serial)
        return np.concatenate(got) if got else np.zeros(0, dtype=np.int64)

    @_writing
    def felt_new_table(self, table: np.ndarray, serial: int, n_frames: int) -> None:
        """表が替わった(日の頭・天気の日付の差し替え)=予約を全部捨てて、次に変わる窓の表を作る。"""
        self.felt_table = table
        self.felt_next = _next_change_table(table)
        self.felt = Scheduler(horizon_ticks=int(n_frames), start_tick=int(serial) + 1)
        self.felt_seq[:] = -1
        self.felt_at[:] = -1
        self.felt_serial = int(serial)

    @_writing
    def felt_plan(self, serial: int, frame: int, ids: np.ndarray, cols: np.ndarray) -> int:
        """体 ``ids``(列 ``cols``)の次の体感温度の予約を置き直す(その日の中で次に値が変わる窓)。件数を返す。"""
        ids = np.asarray(ids, dtype=np.int64)
        nf = next_felt_frames(frame, cols, self.felt_next)
        self.felt_seq[ids] = -1
        self.felt_at[ids] = -1
        self.felt_col[ids] = np.asarray(cols, dtype=np.int64)
        ok = nf != NEVER
        if not ok.any():
            return 0
        at = int(serial) - int(frame) + nf[ok]
        seq = self.felt.schedule_many(ids[ok], at)
        self.felt_seq[ids[ok]] = seq
        self.felt_at[ids[ok]] = at
        return int(np.count_nonzero(ok))

    def pending(self) -> dict[str, int]:
        """生きている予約の数(計器)。"""
        return {"interoception": int(np.count_nonzero(self.intero_seq >= 0)),
                "felt": int(np.count_nonzero(self.felt_seq >= 0))}


def chain_digest(prev: str, now: int, kind: str, ids: np.ndarray, old: np.ndarray, new: np.ndarray) -> str:
    """段の境目の列の鎖のハッシュ(``sha256(前 ‖ 刻み ‖ 種類 ‖ 体 ‖ 前の値 ‖ 後の値)``・体は昇順)。"""
    h = hashlib.sha256(prev.encode("ascii"))
    h.update(f"|{int(now)}|{kind}|{int(ids.size)}|".encode("ascii"))
    h.update(np.ascontiguousarray(ids, dtype=np.int64).tobytes())
    h.update(np.ascontiguousarray(old, dtype=np.uint8).tobytes())
    h.update(np.ascontiguousarray(new, dtype=np.uint8).tobytes())
    return h.hexdigest()

