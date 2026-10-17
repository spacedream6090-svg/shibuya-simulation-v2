"""engine.batching — 計算のまとめ(バッチ)の窓(第 3 期 3-2・時計の段 T1)。

正典: 決定 10-12 §4-2(全員一斉の 1 分の刻みを廃止=残すのは計算のまとめだけで結果は変えない・TM3 (f)「まとめの中は
時刻順に順番に回し、持ち越す・上限は安全装置だけで当たったら記録」・TM4「既定の幅は試験で決める」・TM6 の T1
「まとめの導入(幅 60 秒で今と同じ・試験の道具)」・TM1「電話は窓の境目で届ける」)・10-03 §7-5(窓の中では時刻の順に処理
する・窓の幅が結果を変えてはいけない)・§7-6(会話の往復は窓の中で続けて回す)。記録
``docs/bench/analysis/wallbounce-1012/tm32/README.md``。

進行役(``engine.systems.conductor.conduct``)は「次に処理する時刻の窓 [t, t+W)」を持ち、窓の中の事象を時刻順に順番に
処理する。待ち行列は ``engine.scheduler.Scheduler``(バケットの輪+遠未来の heapq)を流用し、バケットの幅を W にする。
T1 の世界の事象は「刻みの事象」(世界の 1 回の系の並び=刻みの幅ごと・持ち主は世界 ``WORLD``)だけ=事象の時刻の粒度は
刻みの幅(60 秒)。粒度を細かくするのは T2(つなぎの台帳の行 ``DOC-tm32-*``)。

窓の規則(T1 の宣言・実装役の構成=未リサーチ・記録 tm32/README.md §3):

1. 窓の頭はランの始め(通しの時刻のナノ秒)から W ずつ進む。W は刻みの幅の約数の秒(既定 ``STEP_SECONDS``)=刻みの
   事象はいつも窓の頭に乗る(系に渡す ``TickCtx`` の時刻=窓の頭=今の ``t_ns`` と同じ)。
2. 窓に入るのは、時刻が [t, t+W) の予約と、前の窓からの持ち越し(時刻が窓の頭より前)。
3. 窓の中の順: 時刻 → 体の番号(世界 ``WORLD``=-1 は体より先)→ 事象の種類の順位 → 予約の番号(``seq``)。同じ時刻の
   行は種類の続きごとに 1 回の処理(体の番号の配列)にまとめる。
4. 処理の中で予約した事象は、窓の終わりより前なら同じ窓で時刻順に続けて回す(TM3 (f))。窓の終わり以降は待ち行列へ。
   処理中の時刻より前への予約は ``ValueError``(過去への予約)。
5. 届け方 ``boundary`` の種類(TM1 の電話の形)は、時刻を窓の境目に切り上げ、処理中の窓の中なら次の窓の頭に置く
   (遅れ ≤ W・計器 ``boundary_delay_ns_*``)。T1 の世界には使う種類が無い(合成の試験と道具だけ)。
6. 上限(安全装置): 1 つの窓で処理した事象の数が上限 ``cap`` に届いたら、窓の中の残りを次の窓へ持ち越す(止めない・
   持ち越した数と上限に当たった窓の数を数える=manifest の ``batching``)。

状態台帳の行 ``BW``(軸 1 diag・軸 2 discardable): T1 の待ち行列に入るのは次の刻みの事象だけで、刻みの番号から作り直せる
(再開のランは進行役がランの始めに作り直す)。T2 で刻みの外の事象が入ったら行の軸を見直す(つなぎの台帳)。

逐次ループ宣言(P4):
1. ``WindowQueue.run_window``: 窓の中の相異なる時刻の数ぶん(処理の中の予約で増える・上限で止まる)。
2. 同じ時刻の行の種類の続きの数ぶん(処理の関数を呼ぶ回数)。体ごとの Python のループは持たない(並べ替えと切り出しは NumPy)。
進行役の窓のループ(窓の数ぶん)は ``engine.systems.conductor`` の宣言。
"""

from __future__ import annotations

import contextlib
import os
from types import MappingProxyType
from typing import Any, Callable, Final, Iterator, Mapping

import numpy as np

from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS
from shibuya.engine.scheduler import Scheduler

__all__ = [
    "SCHEMA", "ENV", "FP_KEY", "DEFAULT_WIDTH_S", "WIDTHS_S", "DEFAULT_CAP_EVENTS", "WORLD", "KIND_STEP",
    "IN_WINDOW", "BOUNDARY", "DELIVERIES", "ORDER", "HORIZON_STEPS", "COL_T", "COL_AGENT", "COL_KIND", "COL_SEQ",
    "arm", "set_arm", "is_default", "parse_width", "WindowQueue", "manifest_fields", "config_keys", "observed_keys",
]

#: manifest の ``batching`` の形の版(欄の意味を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.engine.batching/1"
#: 幅の腕の環境変数(CLI ``--batch-width-s`` と同じ・指定は CLI が強い)。
ENV: Final[str] = "SHIBUYA_BATCH_WIDTH_S"
#: 設定の指紋(``engine.resume.fingerprint``)に足す鍵(腕のときだけ=既定のランの指紋は今のまま)。
FP_KEY: Final[str] = "batch_width_s"
#: 既定の幅[秒](刻みの幅と同じ=今と同じ結果)。
DEFAULT_WIDTH_S: Final[int] = STEP_SECONDS
#: 腕で選べる幅[秒](刻みの幅の約数=刻みの事象がいつも窓の頭に乗る)。
WIDTHS_S: Final[tuple[int, ...]] = tuple(w for w in range(1, STEP_SECONDS + 1) if STEP_SECONDS % w == 0)
#: 1 つの窓で処理する事象の数の上限(安全装置・仮採用=記録 tm32/README.md §9・つなぎの台帳 DOC-tm32-window-cap)。
#: 2^24 は 39 万体 × 窓あたり 43 件=ふつうのランでは当たらない値(当たったら持ち越して manifest に記録・止めない)。
DEFAULT_CAP_EVENTS: Final[int] = 1 << 24
#: 世界の事象の持ち主の番号(体の番号 0.. より先に並ぶ)。
WORLD: Final[int] = -1
#: 刻みの事象(世界の 1 回の系の並び)の種類の番号。
KIND_STEP: Final[int] = 0
#: 届け方(窓の中で時刻どおり/窓の境目で届ける=TM1 の電話)。
IN_WINDOW: Final[str] = "in_window"
BOUNDARY: Final[str] = "boundary"
DELIVERIES: Final[tuple[str, ...]] = (IN_WINDOW, BOUNDARY)
#: 窓の中の順の宣言(manifest の設定の欄に写す)。
ORDER: Final[str] = "t_ns>agent(world=-1 first)>kind_rank>seq"
#: 事象の種類の番号の上限(順位の表の長さ)。
_N_KINDS: Final[int] = 64
#: 待ち行列の輪の地平(刻みの数=輪のバケットの数は「刻みの幅 ÷ W × これ」)。T1 の待ち行列は次の刻みの事象 1 つだけ=
#: 2 刻みぶんで足りる(それより先の予約は Scheduler の遠未来の heapq)。輪を短くして試験の差の測り(段 B)の手間を小さくした
#: (1 日ぶんの 1,440 の輪では 1 回の snapshot に約 1 ms)。T2 で窓の中の事象が増えたら測って決め直す(実装役の当て)。
HORIZON_STEPS: Final[int] = 2

#: 事象の行の列(int64)。
COL_T: Final[int] = 0
COL_AGENT: Final[int] = 1
COL_KIND: Final[int] = 2
COL_SEQ: Final[int] = 3
_N_COLS: Final[int] = 4
_EMPTY = np.empty((0, _N_COLS), dtype=np.int64)
_EMPTY.setflags(write=False)

#: 計器の欄(順も manifest の順)。
_METER_KEYS: Final[tuple[str, ...]] = (
    "windows", "windows_with_events", "events", "dispatches", "in_window", "carried", "cap_hits",
    "max_events_window", "boundary_events", "boundary_delay_ns_max", "boundary_delay_ns_sum",
)


def parse_width(value: Any) -> int:
    """幅の値(秒の整数・文字列も可)を検査して返す。``WIDTHS_S`` の外は ``ValueError``。"""
    if isinstance(value, bool):
        raise ValueError(f"まとめの幅は {WIDTHS_S} のどれか(秒の整数・いま {value!r})")
    try:
        w = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"まとめの幅は {WIDTHS_S} のどれか(秒の整数・いま {value!r})") from None
    if w not in WIDTHS_S:
        raise ValueError(f"まとめの幅は {WIDTHS_S} のどれか(刻みの幅 {STEP_SECONDS} 秒の約数・いま {w})")
    return w


_raw = os.environ.get(ENV, "").strip()
_ARM: int = parse_width(_raw) if _raw else DEFAULT_WIDTH_S
del _raw


def arm() -> int:
    """いまの幅の腕[秒](既定 ``DEFAULT_WIDTH_S``)。進行役と組み立て(設定の指紋)が読む。"""
    return _ARM


def set_arm(width_s: Any) -> None:
    """幅の腕を選ぶ(CLI ``--batch-width-s``・試験の切替口)。ランの始めに読む(ランの途中で変えてもそのランは変わらない)。"""
    global _ARM
    _ARM = parse_width(width_s)


def is_default(width_s: int | None = None) -> bool:
    """``width_s``(省略=今の腕)が既定の幅か。"""
    return int(_ARM if width_s is None else width_s) == DEFAULT_WIDTH_S


#: 〔3-2 検収 M1〕書いている途中の ``WindowQueue`` の物の番号(``__init__``・``register``・``schedule``・``run_window`` の
#: 自分の文の間だけ入る=処理の関数と試験の境目を呼んでいる間は外す)。ここに無い物への代入と属性の消去は落とす。
_WRITING: set[int] = set()


@contextlib.contextmanager
def _open(q: "WindowQueue") -> Iterator[None]:
    """``q`` の欄を書ける間(入れ子可=処理の関数の中から予約の口を呼んでも外側の状態に戻る)。"""
    k = id(q)
    was = k in _WRITING
    _WRITING.add(k)
    try:
        yield
    finally:
        if not was:
            _WRITING.discard(k)


@contextlib.contextmanager
def _closed(q: "WindowQueue") -> Iterator[None]:
    """``q`` の欄を書けない間(処理の関数と試験の境目を呼ぶ間=外のコードが走る)。"""
    k = id(q)
    was = k in _WRITING
    _WRITING.discard(k)
    try:
        yield
    finally:
        if was:
            _WRITING.add(k)


class WindowQueue:
    """計算のまとめの窓と事象の待ち行列(状態台帳の行 ``BW``・持ち主の名 ``batching``)。

    ``register`` で事象の種類(番号・名・処理の関数・順位・届け方)を置き、``schedule`` で予約し、``run_window`` で次の窓を
    1 つ処理する。処理の関数は ``fn(t_ns, agents, seqs)``(同じ時刻・同じ種類の続きの体の番号と予約の番号の配列)。

    〔3-2 検収 M1〕実行時の守り(3-3 の ``ExperimentLayer`` と同じ形): 欄の代入と消去は ``AttributeError``。書く口は
    ``__init__``・``register``(最初の窓より前だけ)・``schedule``・``run_window`` の自分の文だけ(処理の関数と試験の境目を
    呼んでいる間は書けない)。種類の表は読み取り専用(``MappingProxyType``)・順位の表と持ち越しの行は書けない配列
    (``setflags(write=False)``)・計器は読み取り専用の辞書を置き換える形。``register`` は最初の窓が始まった後と、番号か名の
    重複で落ちる(=最初の窓で種類の表を閉じる)。残る穴: 流用した ``Scheduler``(``_bw_sched``)のメソッドを外から直に呼ぶ
    書き(持ち主の物の中の物=ほかの持ち主の層と同じ限界)。

    Example:
        >>> seen = []
        >>> q = WindowQueue(width_s=30, start_ns=0)
        >>> q.register(1, "alarm", lambda t, a, s: seen.append((t, a.tolist())))
        >>> _ = q.schedule([45 * NS_PER_SECOND, 10 * NS_PER_SECOND], [3, 7], 1)
        >>> q.run_window(); q.run_window()
        >>> [(t // NS_PER_SECOND, a) for t, a in seen]
        [(10, [7]), (45, [3])]
    """

    def __init__(self, *, width_s: int, start_ns: int, cap: int = DEFAULT_CAP_EVENTS,
                 step_s: int = STEP_SECONDS) -> None:
        w, s = int(width_s), int(step_s)
        if w <= 0 or s <= 0 or s % w != 0:
            raise ValueError(f"まとめの幅 {width_s} 秒は刻みの幅 {step_s} 秒の約数(正の整数)")
        if int(cap) < 1:
            raise ValueError(f"上限は 1 以上(いま {cap})")
        start = int(start_ns)
        if start % (w * NS_PER_SECOND) != 0:
            raise ValueError(f"最初の窓の頭 {start} ns は幅 {w * NS_PER_SECOND} ns の倍数")
        rank = np.zeros(_N_KINDS, dtype=np.int64)
        rank.setflags(write=False)
        with _open(self):
            self.width_s: int = w
            self.width_ns: int = w * NS_PER_SECOND
            self.step_s: int = s
            self.cap: int = int(cap)
            #: 種類の番号 → (名, 処理の関数, 届け方)(参照・読み取り専用=``register`` が置き換える)。
            self._bw_kinds: Mapping[int, tuple[str, Callable[..., Any], str]] = MappingProxyType({})
            #: 種類の番号 → 順位(並べ替えの鍵・書けない配列=``register`` が置き換える)。
            self._bw_rank = rank
            # ---- 状態(台帳の行 BW) ----
            self._bw_sched = Scheduler(start_tick=start // self.width_ns, tick_seconds=w,
                                       horizon_ticks=HORIZON_STEPS * (s // w))
            self._bw_carry: np.ndarray = _EMPTY
            self._bw_head: int = start
            self._bw_meter: Mapping[str, int] = MappingProxyType({k: 0 for k in _METER_KEYS})
            # ---- 窓の中だけの作業の値 ----
            self._bw_now: int | None = None
            self._bw_end: int | None = None
            self._bw_new: tuple[np.ndarray, ...] = ()

    def __setattr__(self, name: str, value: Any) -> None:
        if id(self) not in _WRITING:
            raise AttributeError(f"まとめの窓の欄 {name} は外から書けない(書く口は register・schedule・run_window)")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"まとめの窓の欄 {name} は消せない")

    def _bump(self, **inc: int) -> None:
        """計器を足す(読み取り専用の辞書を置き換える=書く口の中だけで呼ぶ)。"""
        d = dict(self._bw_meter)
        for k, v in inc.items():
            d[k] += int(v)
        self._bw_meter = MappingProxyType(d)

    def _raise_to(self, key: str, value: int) -> None:
        """計器の最大の欄を ``value`` まで上げる(書く口の中だけで呼ぶ)。"""
        if int(value) > int(self._bw_meter[key]):
            d = dict(self._bw_meter)
            d[key] = int(value)
            self._bw_meter = MappingProxyType(d)

    # ---- 種類 ----
    @property
    def started(self) -> bool:
        """最初の窓が始まったか(始まった後は ``register`` が落ちる=種類の表は閉じている)。"""
        return int(self._bw_meter["windows"]) > 0

    def register(self, kind: int, name: str, fn: Callable[..., Any], *, rank: int = 0,
                 delivery: str = IN_WINDOW) -> None:
        """事象の種類を置く(最初の窓より前だけ・同じ番号か同じ名を 2 回置くと ``ValueError``)。"""
        if self.started:
            raise RuntimeError("種類の表は最初の窓で閉じた(register はランの始めだけ)")
        k = int(kind)
        if not 0 <= k < _N_KINDS:
            raise ValueError(f"種類の番号は 0..{_N_KINDS - 1}(いま {kind})")
        if k in self._bw_kinds:
            raise ValueError(f"種類 {k} はもう置いた({self._bw_kinds[k][0]})")
        if str(name) in {v[0] for v in self._bw_kinds.values()}:
            raise ValueError(f"種類の名 {name!r} はもう置いた")
        if delivery not in DELIVERIES:
            raise ValueError(f"届け方は {DELIVERIES}(いま {delivery!r})")
        kinds = dict(self._bw_kinds)
        kinds[k] = (str(name), fn, str(delivery))
        rk = self._bw_rank.copy()
        rk[k] = int(rank)
        rk.setflags(write=False)
        with _open(self):
            self._bw_kinds = MappingProxyType(kinds)
            self._bw_rank = rk

    # ---- 状態の読み口 ----
    @property
    def head_ns(self) -> int:
        """次に処理する窓の頭(処理中は今の窓の頭)。"""
        return self._bw_head

    @property
    def window_counts(self) -> dict[str, int]:
        """計器の写し(読むだけ。名は状態台帳の外の道筋の属性 ``meter``=1-9・1-8・1-8b と衝突させない)。"""
        return dict(self._bw_meter)

    @property
    def pending(self) -> int:
        """まだ処理していない事象の数(待ち行列+持ち越し)。"""
        return int(self._bw_sched.pending) + int(self._bw_carry.shape[0])

    # ---- 予約 ----
    def schedule(self, t_ns: Any, agents: Any, kind: int) -> np.ndarray:
        """事象を予約して予約の番号(``seq``)の配列を返す(``t_ns`` か ``agents`` の片方はスカラー可)。"""
        k = int(kind)
        if k not in self._bw_kinds:
            raise ValueError(f"置いていない種類 {k}")
        a = np.atleast_1d(np.asarray(agents, dtype=np.int64)).ravel()
        t = np.atleast_1d(np.asarray(t_ns, dtype=np.int64)).ravel()
        if t.size == 1 and a.size != 1:
            t = np.full(a.size, int(t[0]), dtype=np.int64)
        elif a.size == 1 and t.size != 1:
            a = np.full(t.size, int(a[0]), dtype=np.int64)
        if t.size != a.size:
            raise ValueError(f"時刻と体の数が違う({t.size} と {a.size})")
        n = int(t.size)
        if n == 0:
            return np.empty(0, dtype=np.int64)
        active = self._bw_end is not None
        floor = int(self._bw_now) if active else self._bw_head
        if np.any(t < floor):
            raise ValueError(f"過去への予約(処理中の時刻 {floor} ns より前)")
        with _open(self):
            if self._bw_kinds[k][2] == BOUNDARY:  # 5. 窓の境目で届ける(TM1 の電話)
                want = t
                t = -((-t) // self.width_ns) * self.width_ns
                if active:
                    t = np.maximum(t, int(self._bw_end))
                delay = t - want
                self._bump(boundary_events=n, boundary_delay_ns_sum=int(delay.sum()))
                self._raise_to("boundary_delay_ns_max", int(delay.max()))
            seq = np.empty(n, dtype=np.int64)
            inwin = (t < int(self._bw_end)) if active else np.zeros(n, dtype=bool)
            fut = ~inwin
            if fut.any():
                tf = t[fut]
                seq[fut] = self._bw_sched.schedule_many(a[fut], tf // self.width_ns, tf % self.width_ns, k)
            if inwin.any():
                ni = int(np.count_nonzero(inwin))
                s = self._bw_sched.reserve_seq(ni)
                seq[inwin] = s
                rows = np.empty((ni, _N_COLS), dtype=np.int64)
                rows[:, COL_T], rows[:, COL_AGENT], rows[:, COL_KIND], rows[:, COL_SEQ] = t[inwin], a[inwin], k, s
                rows.setflags(write=False)
                self._bw_new = (*self._bw_new, rows)
        return seq

    # ---- 窓 ----
    def _sorted(self, rows: np.ndarray) -> np.ndarray:
        if rows.shape[0] <= 1:
            return rows
        order = np.lexsort((rows[:, COL_SEQ], self._bw_rank[rows[:, COL_KIND]], rows[:, COL_AGENT], rows[:, COL_T]))
        return rows[order]

    def run_window(self, after_dispatch: Callable[[], Any] | None = None) -> None:
        """次の窓 [頭, 頭+W) を 1 つ処理して、頭を W 進める。

        ``after_dispatch`` は処理の関数を呼んだ後ごとに呼ぶ口(進行役が試験の境目を置く=処理の後の控えの変化を系に
        帰属させない)。処理の関数と ``after_dispatch`` を呼んでいる間は欄を書けない(〔3-2 検収 M1〕)。

        〔3-2 検収 L7〕同じ時刻の束(と種類の続き)を処理している間に**同じ時刻**へ足した事象は、束の残りの後(次の回)に
        回る(例: 体 5・9 の束の処理の中で体 3 を同じ時刻に足すと 5 → 9 → 3)=「同時刻は体の番号順」の例外(宣言)。
        """
        with _open(self):
            head = self._bw_head
            end = head + self.width_ns
            b = head // self.width_ns
            st = self._bw_sched.events_at(b)
            self._bw_sched.consume(b)
            ev = st.events
            rows = np.empty((ev.shape[0], _N_COLS), dtype=np.int64)
            if ev.shape[0]:
                rows[:, COL_T] = head + ev[:, 1]
                rows[:, COL_AGENT] = ev[:, 0]
                rows[:, COL_KIND] = ev[:, 2]
                rows[:, COL_SEQ] = ev[:, 3]
            carry = self._bw_carry
            pending = self._sorted(np.concatenate([carry, rows]) if carry.shape[0] else rows)
            self._bw_carry = _EMPTY
            self._bump(windows=1)
            self._bw_end = end
            done = 0
            # 逐次ループ宣言1: 窓の中の相異なる時刻の数ぶん(処理の中の予約で増える・上限で止まる)
            while pending.shape[0]:
                if done >= self.cap:  # 6. 上限(安全装置): 残りを次の窓へ持ち越す(止めない)
                    keep = np.array(pending, dtype=np.int64)
                    keep.setflags(write=False)
                    self._bw_carry = keep
                    self._bump(carried=int(pending.shape[0]), cap_hits=1)
                    break
                t0 = int(pending[0, COL_T])
                k = int(np.searchsorted(pending[:, COL_T], t0, side="right"))
                k = min(k, self.cap - done)
                group, pending = pending[:k], pending[k:]
                self._bw_now = t0
                done += k
                kinds = group[:, COL_KIND]
                cuts = np.flatnonzero(kinds[1:] != kinds[:-1]) + 1
                starts = np.concatenate([[0], cuts]).tolist()
                stops = np.concatenate([cuts, [k]]).tolist()
                self._bump(events=k, dispatches=len(starts))
                # 逐次ループ宣言2: 種類の続きの数ぶん
                for s0, s1 in zip(starts, stops):
                    fn = self._bw_kinds[int(kinds[s0])][1]
                    with _closed(self):  # 外のコード(系の並び・試験の境目)が走る間は欄を書けない
                        fn(t0, group[s0:s1, COL_AGENT], group[s0:s1, COL_SEQ])
                        if after_dispatch is not None:
                            after_dispatch()
                    if self._bw_new:  # 4. 窓の中の予約は同じ窓で時刻順に続けて回す
                        new = np.concatenate(self._bw_new)
                        self._bw_new = ()
                        self._bump(in_window=int(new.shape[0]))
                        pending = self._sorted(np.concatenate([pending, new]))
            if done:
                self._bump(windows_with_events=1)
                self._raise_to("max_events_window", done)
            self._bw_now = None
            self._bw_end = None
            self._bw_head = end

    # ---- manifest ----
    def manifest_fields(self) -> dict[str, Any]:
        """manifest の ``batching``(設定: 形の版・幅・既定の幅・刻みの幅・上限・順・世界の番号・種類/観測: 計器)。"""
        kinds = {name: {"kind": k, "rank": int(self._bw_rank[k]), "delivery": dl}
                 for k, (name, _fn, dl) in sorted(self._bw_kinds.items())}
        out: dict[str, Any] = {
            "schema": SCHEMA, "width_s": self.width_s, "default_width_s": DEFAULT_WIDTH_S, "step_s": self.step_s,
            "cap_events": self.cap, "order": ORDER, "world_id": WORLD, "kinds": kinds,
        }
        out.update({k: int(v) for k, v in self._bw_meter.items()})
        out["pending_at_end"] = self.pending
        return out


def manifest_fields(queue: "WindowQueue | None") -> dict[str, Any] | None:
    """``RunResult`` の manifest の ``batching``(進行役を通らない結果は ``None``)。"""
    return None if queue is None else queue.manifest_fields()


def config_keys() -> tuple[str, ...]:
    """manifest の ``batching`` の設定の子の鍵(``engine.manifest_sections`` の表と試験が突き合わせる)。"""
    return ("schema", "width_s", "default_width_s", "step_s", "cap_events", "order", "world_id", "kinds")


def observed_keys() -> tuple[str, ...]:
    """manifest の ``batching`` の観測の子の鍵。"""
    return (*_METER_KEYS, "pending_at_end")
