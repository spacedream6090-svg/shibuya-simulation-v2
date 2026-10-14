"""engine.events.log — 出来事の記録(第 1 期 1-3・CP12・CT9・5W1H)。

口の約束: ``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-3 出来事の記録」。

- ``Event``(凍結の dataclass): ``id``(通し・決定的=``(t_ns, seq)``)・``t_ns``(``SimTime``)・``who``(体の id か
  持ち主の名)・``what``(語彙表 ``engine.events.vocab`` の語)・``whom``・``where``(セル/ノード/POI)・``how_much``・
  ``via``(CT9 の道具の欄)・``received_ns``/``read_ns``(届いた/読んだ)・``origin``(範囲の外からの印)・``cause``。
- ``cause`` は **3 種類だけ**: ``LlmCall(call_id, input_event_ids)``・``Process(name)``・``Experiment(cond_id)``。
  第 4 の型は作れない(根 ``_Cause`` の ``__init_subclass__`` が 3 つの名と置き場の外を落とし、3 つを定義した後は
  封じる)。``Experiment`` を作れるのは ``engine/experiment/gate.py`` の ``admit`` だけ(CP12・実行時=呼び手の
  フレームの検査・静的=``tests/engine/events/test_e_cause_three_kinds.py`` の AST)。
- 書く口は ``EventLog.append(ev)`` の 1 つ。id は記録が付ける(``(t_ns, seq)``・``seq`` は同じ ``t_ns`` の中の通し)。
  記録の時計は進行役が刻みの頭で置く(``begin_step``)。出来事の時刻はいまの刻みの頭より前にできない
  (「書き込むその場で直接の原因だけを記録する」CP12)。
- 中身は列ごとの配列(SoA 風・1 行 ``ROW_BYTES`` B)。日の締めで保持窓(``RETENTION_DAYS`` 日=ActualLog の
  D-R2-6 と同じ)の外の行を落とす(1 日の行数と種類の分布は manifest の日次の記録に残る)。
- 〔第 1 期 1-8 J0・1-3 の検収 M2〕**原因の表も列**(``_CZ_COLS``=種類の番号・参照の番号・call_id の 3 つの整数
  (``"{T}:{体}:{級}"``=テープの call_id の形)・入力の出来事 id の範囲・選んだ候補の源と提示の番号=1-8 の検収 M1)と
  入力の id の 2 列(``_ci_t``・``_ci_seq``)。1-3 の「呼び出しごとに Python の物 1 つ」(実測 198〜1,002 B/呼)を
  39 B+入力 1 つ 12 B/呼にした(記録 ``docs/bench/analysis/wallbounce-1012/j0/README.md``)。読み口 ``event(i).cause`` は今の 3 型を組み立てて返す
  (``LlmCall`` と ``Process`` は列から作る・``Experiment`` は口 ``gate.admit`` が作った物を小さな表に持って返す=
  口の外では作らない)。同じ原因の行は 1 つにまとめる: 過程と実験は名で・LLM の呼び出しは「直前に書いた LLM の
  呼び出しと同じ」ときだけ(呼び出しごとの dict を持たない)。参照の番号は、過程=``V.CAUSE_PROCESS_NAMES`` の番号・
  実験=実験の表の番号・LLM の呼び出し=テープの形でない call_id の文字列の表の番号(テープの形なら -1)。

約束(口の約束 1-3): (1) 記録の有無で final・テープ・behavior-hash は変わらない(状態台帳の行 ``E``=軸 1 diag・
軸 2 discardable=どちらのハッシュにも状態のファイルにも入らない)。(2) 既存の ActualLog・金と物の生ログ・テープは
消さず、``Event.id`` への目印で結ぶ(1-3 では ActualLog=``world.processes.actual_log`` の目印の列)。(3) 1 日の行数と
種類の分布を manifest の日次の記録に出す。(4) 書く系は ``writes.paths`` に ``E:events.*`` を宣言する(段 B と、
段 C と同じ実行時の検査 ``engine.systems.guard.events_write_allowed``)。

切替口(腕): 既定は記録する。``SHIBUYA_EVENTS=off``・``set_enabled(False)``・CLI ``--events off`` で記録しない
(``append`` は何もせず ``None`` を返す)。記録は結果を変えないので設定の指紋には入れない(書きの検査の切替口
``SHIBUYA_WRITE_GUARD`` と同じ扱い)。記録したかは manifest の日次の記録 ``events.on`` に出る。

先例(形だけ借りた): AI Town ``convex/engine/abstractGame.ts``(MIT・外からの入力を番号つきの 1 本の表に通す)・
MATSim/SUMO の events(時刻順の 1 本のログ)。R-113 §3。

**未リサーチ(expedient)**: 列の型と幅・保持窓 7 日(ActualLog に合わせた)・``who`` の持ち主の名の書き方
(``runner.<過程>``・区切りは ``engine``)。

逐次ループ宣言: ``append`` は 1 行=定数時間(列の倍化は償却)。``close_day`` は保持窓の外の行を落とす numpy の
ベクトル演算と原因の表の詰め直し(行数に比例・1 日 1 回)。``event`` は 1 行=入力の id の数ぶん(原因の組み立て)。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Any, ClassVar, Final, Iterator, Mapping, Union

import numpy as np

from shibuya.core.growth import GrowthDeclaration, Retention
from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_DAY, STEPS_PER_DAY
from shibuya.core.types import SimTime
from shibuya.engine.events import vocab as V
from shibuya.engine.systems import guard as _G

__all__ = [
    "EventId", "Event", "EVENT_FIELDS", "LlmCall", "Process", "CAUSE_TYPES", "CAUSE_KINDS", "Cause",
    "CANDIDATE_SOURCES",
    "EventLog", "ROW_BYTES", "CAUSE_ROW_BYTES", "INPUT_ID_BYTES", "RETENTION_DAYS", "NS_PER_DAY", "enabled",
    "set_enabled",
]

#: 出来事の id=``(t_ns, seq)``(``seq`` は同じ ``t_ns`` の中の通し)。並べると時刻順。
EventId = tuple[int, int]

NS_PER_DAY: Final[int] = SECONDS_PER_DAY * NS_PER_SECOND
#: 生の行の保持窓(日)。ActualLog の D-R2-6 の窓と同じ(目印の両側が同じ日数だけ残る)。expedient。
RETENTION_DAYS: Final[int] = 7

#: 切替口(既定は記録する)。
_ENABLED: bool = os.environ.get("SHIBUYA_EVENTS", "on").strip().lower() not in ("off", "0", "false", "no")


def enabled() -> bool:
    """出来事を記録するか(切替口 ``SHIBUYA_EVENTS``・``set_enabled``)。"""
    return _ENABLED


def set_enabled(flag: bool) -> None:
    """記録を入れる/外す(腕・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランの記録は変わらない)。"""
    global _ENABLED
    _ENABLED = bool(flag)


def _is_int(x: Any) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, (bool, np.bool_))


# ================================================================ 原因(3 種類だけ)
_CAUSE_NAMES: Final[tuple[str, ...]] = ("LlmCall", "Process", "Experiment")
#: 〔第 1 期 1-8 J0・検収 M1〕判断の口の候補の源(``LlmCall.source`` の語・並びは原因の表の列 ``_cz_src`` の番号)=DM-0 の
#: 5 つの源+J0 のつなぎの印 ``vocab``(``engine.decision.port.ALL_SOURCES`` と同じ=試験と口の層の組み立てで突き合わせる)。
CANDIDATE_SOURCES: Final[tuple[str, ...]] = ("experience", "affordance", "plan", "continue", "deliberate", "vocab")
#: ``LlmCall.number``(提示の番号)の上限(原因の表の列は i1)。
_NUMBER_MAX: Final[int] = 127
_SEALED: bool = False


class _Cause:
    """原因の型の根。子は ``LlmCall``・``Process``・``Experiment`` の 3 つだけ(この置き場で 1 回だけ定義できる)。"""

    __slots__ = ()
    kind: ClassVar[str] = ""

    def __init_subclass__(cls, **kw: Any) -> None:
        super().__init_subclass__(**kw)
        if _SEALED or cls.__module__ != __name__ or cls.__name__ not in _CAUSE_NAMES or cls.__bases__ != (_Cause,):
            raise TypeError(
                f"出来事の原因は 3 種類だけ(LLM の呼び出し・過程・実験の条件=CP12)。第 4 の型 {cls.__qualname__} は作れない")


@dataclass(frozen=True)
class LlmCall(_Cause):
    """原因=LLM の呼び出し(``call_id``=テープの ``call_id`` 列と同じ値・``input_event_ids``=入力に入っていた出来事の id)。

    〔第 1 期 1-8 J0・検収 M1〕判断の口(``engine.decision``)を通った呼び出しは、選んだ候補の源 ``source``
    (``CANDIDATE_SOURCES`` の語=5 つの源+つなぎの印 ``vocab``)と提示の番号 ``number``(1 から)も持つ(口の約束 1-8 の
    約束 (3)=候補の源のどれから来たかを判断ごとに記録)。口を通らない呼び出しは どちらも ``None``。
    """

    call_id: str
    input_event_ids: tuple[EventId, ...] = ()
    source: str | None = None
    number: int | None = None
    kind: ClassVar[str] = "llm_call"

    def __post_init__(self) -> None:
        if not isinstance(self.call_id, str) or not self.call_id.strip():
            raise ValueError("LlmCall.call_id は空でない文字列(テープの call_id 列と同じ値)")
        ids = []
        for x in self.input_event_ids:
            if not (isinstance(x, tuple) and len(x) == 2 and _is_int(x[0]) and _is_int(x[1])):
                raise ValueError(f"LlmCall.input_event_ids の要素は (t_ns, seq) の組(いま {x!r})")
            ids.append((int(x[0]), int(x[1])))
        object.__setattr__(self, "input_event_ids", tuple(ids))
        if self.source is not None and self.source not in CANDIDATE_SOURCES:
            raise ValueError(f"LlmCall.source は {CANDIDATE_SOURCES} のどれか None(いま {self.source!r})")
        if self.number is not None:
            if not _is_int(self.number) or not 1 <= int(self.number) <= _NUMBER_MAX:
                raise ValueError(f"LlmCall.number は 1〜{_NUMBER_MAX} の整数か None(いま {self.number!r})")
            object.__setattr__(self, "number", int(self.number))


@dataclass(frozen=True)
class Process(_Cause):
    """原因=過程(世界過程の名か区切りの名=``vocab.PROCESS_NAMES``・〔1-5〕検査の名=``vocab.CHECK_PROCESSES``)。"""

    name: str
    kind: ClassVar[str] = "process"

    def __post_init__(self) -> None:
        if self.name not in V.CAUSE_PROCESS_NAMES:
            raise ValueError(f"Process の名が過程の名の表の外: {self.name!r}(表は {V.CAUSE_PROCESS_NAMES})")


def _only_from_gate(caller: Any) -> None:
    """CP12(実行時): ``Experiment`` を作る呼び手が ``engine.experiment.gate.admit`` でなければ ``PermissionError``。

    書きの検査の切替口(``SHIBUYA_WRITE_GUARD=off``)でも外さない: 書きの検査は値を変えない検査で重さの測りのために
    外せるが、この検査は記録の原因の正しさそのもの(外すと実験でない出来事に実験の印が付き、分岐の差の帰属が
    壊れる)。実験の口を通る回数は少ない=重さの理由も無い。
    """
    from shibuya.engine.experiment import gate as _GATE

    if caller is None or caller.f_code is not _GATE.ADMIT_CODE:
        where = "?" if caller is None else f"{caller.f_code.co_filename}:{caller.f_lineno} {caller.f_code.co_name}"
        raise PermissionError(
            "CP12: 実験の条件(原因の種類 experiment)を作れるのは engine/experiment/gate.py の admit だけ"
            f"(呼び手 {where})")


@dataclass(frozen=True, init=False)
class Experiment(_Cause):
    """原因=実験の条件(``cond_id``)。**作れるのは ``engine/experiment/gate.py`` の ``admit`` だけ**(CP12)。"""

    cond_id: str
    kind: ClassVar[str] = "experiment"

    def __init__(self, cond_id: str) -> None:
        _only_from_gate(sys._getframe(1))  # 先に見る(既存の物の __init__ を呼び直しても中身を書き換えない)
        if not isinstance(cond_id, str) or not cond_id.strip():
            raise ValueError("Experiment.cond_id は空でない文字列")
        object.__setattr__(self, "cond_id", cond_id)

    def __reduce__(self) -> Any:  # pickle で口の外から作らせない
        raise TypeError("Experiment は pickle で作れない(CP12: 実験の条件の口は gate.admit だけ)")

    def __copy__(self) -> "Experiment":
        return self

    def __deepcopy__(self, memo: Any) -> "Experiment":
        return self


_SEALED = True

#: 原因の型(この 3 つだけ・並びがコード)。
CAUSE_TYPES: Final[tuple[type, ...]] = (LlmCall, Process, Experiment)
CAUSE_KINDS: Final[tuple[str, ...]] = tuple(c.kind for c in CAUSE_TYPES)
Cause = Union[LlmCall, Process, Experiment]


# ================================================================ 出来事
@dataclass(frozen=True, slots=True, kw_only=True)
class Event:
    """出来事 1 行(5W1H+誰に+どれだけ+原因)。書き手は ``id`` を付けない(``EventLog.append`` が付ける)。"""

    id: EventId | None = None
    t_ns: SimTime
    who: int | str
    what: str
    whom: int | str | None = None
    where: tuple[str, int] | None = None
    how_much: int | None = None
    via: str = V.VIA_NONE
    received_ns: SimTime | None = None
    read_ns: SimTime | None = None
    origin: str | None = None
    cause: Cause

    def __post_init__(self) -> None:
        if self.id is not None:
            if not (isinstance(self.id, tuple) and len(self.id) == 2 and _is_int(self.id[0]) and _is_int(self.id[1])):
                raise ValueError(f"Event.id は (t_ns, seq) の組か None(いま {self.id!r})")
            object.__setattr__(self, "id", (int(self.id[0]), int(self.id[1])))
        if not _is_int(self.t_ns) or int(self.t_ns) < 0:
            raise ValueError(f"Event.t_ns は 0 以上の整数(ナノ秒・SimTime)(いま {self.t_ns!r})")
        object.__setattr__(self, "t_ns", int(self.t_ns))
        object.__setattr__(self, "who", _actor(self.who, "who", none_ok=False))
        V.code_of(self.what)
        object.__setattr__(self, "whom", _actor(self.whom, "whom", none_ok=True))
        if self.where is not None:
            w = self.where
            if not (isinstance(w, tuple) and len(w) == 2 and w[0] in V.WHERE_KINDS and _is_int(w[1]) and int(w[1]) >= 0):
                raise ValueError(f"Event.where は (種類, 番号) の組(種類は {V.WHERE_KINDS})か None(いま {w!r})")
            object.__setattr__(self, "where", (str(w[0]), int(w[1])))
        if self.how_much is not None:
            if not _is_int(self.how_much) or int(self.how_much) == _NONE_I64:
                raise ValueError(f"Event.how_much は整数か None(いま {self.how_much!r})")
            object.__setattr__(self, "how_much", int(self.how_much))
        if self.via not in V.VIA_CODES:
            raise ValueError(f"Event.via は {V.VIA_WORDS} のどれか(いま {self.via!r})")
        for name in ("received_ns", "read_ns"):
            x = getattr(self, name)
            if x is not None:
                if not _is_int(x) or int(x) < 0:
                    raise ValueError(f"Event.{name} は 0 以上の整数か None(いま {x!r})")
                object.__setattr__(self, name, int(x))
        if self.received_ns is not None and self.received_ns < self.t_ns:
            raise ValueError("Event.received_ns は t_ns より前にできない(届くのは起きた後)")
        if self.read_ns is not None and (self.received_ns is None or self.read_ns < self.received_ns):
            raise ValueError("Event.read_ns は received_ns の後(届く前に読めない)")
        if self.origin is not None and (not isinstance(self.origin, str) or not self.origin.strip()):
            raise ValueError("Event.origin は空でない文字列か None")
        if type(self.cause) not in CAUSE_TYPES:
            raise TypeError(f"Event.cause は {tuple(c.__name__ for c in CAUSE_TYPES)} のどれか(いま {type(self.cause)!r})")


#: ``Event`` の欄の名と順(口の約束 1-3)。
EVENT_FIELDS: Final[tuple[str, ...]] = tuple(f.name for f in fields(Event))


def _actor(x: Any, name: str, *, none_ok: bool) -> int | str | None:
    if x is None:
        if none_ok:
            return None
        raise ValueError(f"Event.{name} は必須(体の id か持ち主の名)")
    if isinstance(x, str):
        if not x.strip():
            raise ValueError(f"Event.{name} の名が空")
        return x
    if _is_int(x) and int(x) >= 0:
        return int(x)
    raise ValueError(f"Event.{name} は 0 以上の体の id か持ち主の名(いま {x!r})")


# ================================================================ 記録(列ごとの配列)
_NONE_I64: Final[int] = int(np.iinfo(np.int64).min)

#: 列(属性の名・型・空の値)。``ROW_BYTES`` はこの和。
_COLS: Final[tuple[tuple[str, Any, int], ...]] = (
    ("_ev_t_ns", np.int64, 0),
    ("_ev_seq", np.int32, -1),
    ("_ev_who", np.int64, _NONE_I64),
    ("_ev_what", np.int16, -1),
    ("_ev_whom", np.int64, _NONE_I64),
    ("_ev_where_kind", np.int8, -1),
    ("_ev_where_id", np.int64, -1),
    ("_ev_how_much", np.int64, _NONE_I64),
    ("_ev_via", np.int8, -1),
    ("_ev_received_ns", np.int64, -1),
    ("_ev_read_ns", np.int64, -1),
    ("_ev_origin", np.int32, -1),
    ("_ev_cause", np.int32, -1),
)
ROW_BYTES: Final[int] = int(sum(np.dtype(t).itemsize for _n, t, _f in _COLS))
_COL_NAMES: Final[tuple[str, ...]] = tuple(n for n, _t, _f in _COLS)

#: 〔1-8 J0・1-3 の検収 M2〕原因の表の列(属性の名・型・空の値)。``CAUSE_ROW_BYTES`` はこの和(入力の id は別の 2 列)。
_CZ_COLS: Final[tuple[tuple[str, Any, int], ...]] = (
    ("_cz_kind", np.int8, -1),         # CAUSE_KINDS の番号
    ("_cz_ref", np.int32, -1),         # 過程の名の番号・実験の表の番号・テープの形でない call_id の番号(形なら -1)
    ("_cz_call_t", np.int64, 0),       # call_id の 1 つ目(発射の刻みの番号 T)
    ("_cz_call_agent", np.int64, 0),   # call_id の 2 つ目(体)
    ("_cz_call_cls", np.int32, 0),     # call_id の 3 つ目(起床の級)
    ("_cz_in_start", np.int64, 0),     # 入力の出来事 id の範囲の頭(``_ci_*`` の位置)
    ("_cz_in_len", np.int32, 0),       # 入力の出来事 id の数
    ("_cz_src", np.int8, -1),          # 〔検収 M1〕選んだ候補の源(CANDIDATE_SOURCES の番号・口を通らない呼び出しは -1)
    ("_cz_num", np.int8, -1),          # 〔検収 M1〕選んだ提示の番号(1 から・口を通らない呼び出しは -1)
)
CAUSE_ROW_BYTES: Final[int] = int(sum(np.dtype(t).itemsize for _n, t, _f in _CZ_COLS))
_CZ_NAMES: Final[tuple[str, ...]] = tuple(n for n, _t, _f in _CZ_COLS)
#: 入力の出来事 id の 2 列(``(t_ns, seq)``)。1 つ ``INPUT_ID_BYTES`` B。
_CI_COLS: Final[tuple[tuple[str, Any, int], ...]] = (("_ci_t", np.int64, 0), ("_ci_seq", np.int32, 0))
_CI_NAMES: Final[tuple[str, ...]] = tuple(n for n, _t, _f in _CI_COLS)
INPUT_ID_BYTES: Final[int] = int(sum(np.dtype(t).itemsize for _n, t, _f in _CI_COLS))
_K_LLM, _K_PROC, _K_EXP = CAUSE_KINDS.index("llm_call"), CAUSE_KINDS.index("process"), CAUSE_KINDS.index("experiment")
#: 過程の名 → 原因の表の参照の番号。〔1-8 の取り込み・検収 H1〕``Process`` の検査と同じ 1 つの定数
#: ``V.CAUSE_PROCESS_NAMES``(世界過程+区切り+1-5 の検査の名 ``rights``)から作る(``PROCESS_NAMES`` から作ると
#: ``Process("rights")`` を書くと ``KeyError``)。
_PROC_CODE: Final[Mapping[str, int]] = MappingProxyType({n: i for i, n in enumerate(V.CAUSE_PROCESS_NAMES)})
_SRC_CODE: Final[Mapping[str, int]] = MappingProxyType({n: i for i, n in enumerate(CANDIDATE_SOURCES)})
_I32 = 1 << 31


def _canonical_call_id(call_id: str) -> tuple[int, int, int] | None:
    """テープの形 ``"{T}:{体}:{級}"``(10 進の整数・先頭の 0 なし・級は負もある)なら 3 つの整数、ほかは ``None``。"""
    parts = call_id.split(":")
    if len(parts) != 3:
        return None
    try:
        t, a, c = (int(x) for x in parts)
    except ValueError:
        return None
    if f"{t}:{a}:{c}" != call_id or t < 0 or a < 0 or not (-_I32 <= c < _I32):
        return None
    return t, a, c


class EventLog:
    """出来事の記録(書く口は ``append`` の 1 つ)。

    Args:
        enabled: 記録するか(``False``=何もしない=切替口)。
        retention_days: 生の行の保持窓(日)。
        capacity: 最初の列の長さ(足りなくなったら倍に)。
    """

    __slots__ = ("enabled", "retention_days") + _COL_NAMES + (
        "_ev_n", "_ev_names", "_ev_name_codes", "_ev_now_ns", "_ev_seq_next",
        "_ev_day_mark", "_ev_n_appended", "_ev_n_evicted") + _CZ_NAMES + _CI_NAMES + (
        "_cz_n", "_ci_n", "_cz_proc_rows", "_cz_exp_rows", "_cz_experiments", "_cz_texts", "_cz_last_llm")

    def __init__(self, *, enabled: bool = True, retention_days: int = RETENTION_DAYS, capacity: int = 1024) -> None:
        if int(retention_days) <= 0 or int(capacity) <= 0:
            raise ValueError("retention_days・capacity は正")
        self.enabled = bool(enabled)
        self.retention_days = int(retention_days)
        for n, t, f in _COLS:
            setattr(self, n, np.full(int(capacity), f, dtype=t))
        self._ev_n = 0
        #: 持ち主の名・出どころの印の表(列には番号=``who``/``whom`` は ``-1-番号``・``origin`` は番号)。
        self._ev_names: list[str] = []
        self._ev_name_codes: dict[str, int] = {}
        #: 原因の表(列=``_CZ_COLS``・出来事の列 ``_ev_cause`` には行の番号)。日の締めで生きている行が指すものだけに
        #: 詰め直す。入力の出来事 id は ``_ci_t``・``_ci_seq`` の範囲。
        for n, t, f in _CZ_COLS + _CI_COLS:
            setattr(self, n, np.full(64, f, dtype=t))
        self._cz_n = 0
        self._ci_n = 0
        #: 過程の名の番号 → 行・実験の条件の名 → 行(どちらも名の数で頭打ち)。
        self._cz_proc_rows: dict[int, int] = {}
        self._cz_exp_rows: dict[str, int] = {}
        #: 実験の条件の原因(``gate.admit`` が作った物・条件の数で頭打ち)と、テープの形でない call_id の文字列。
        self._cz_experiments: list[Experiment] = []
        self._cz_texts: list[str] = []
        #: 直前に書いた LLM の呼び出しの原因とその行(同じ呼び出しの行を続けて書くときだけ 1 つにまとめる)。
        self._cz_last_llm: tuple[LlmCall, int] | None = None
        #: 記録の時計(いまの刻みの頭の時刻)。出来事の時刻はこれより前にできない。
        self._ev_now_ns = 0
        #: ``t_ns`` → 次の ``seq``(刻みの頭で古い時刻を落とす)。
        self._ev_seq_next: dict[int, int] = {}
        #: 前の日の締めの時点の通しの行数(日ごとの行数の起点)。
        self._ev_day_mark = 0
        self._ev_n_appended = 0
        self._ev_n_evicted = 0

    # ------------------------------------------------------------------ 時計
    def begin_step(self, t_ns: SimTime) -> None:
        """記録の時計を刻みの頭の時刻にする(進行役が呼ぶ)。"""
        t = int(t_ns)
        self._ev_now_ns = t
        if self._ev_seq_next and min(self._ev_seq_next) < t:
            self._ev_seq_next = {k: v for k, v in self._ev_seq_next.items() if k >= t}

    @property
    def now_ns(self) -> SimTime:
        return self._ev_now_ns

    # ------------------------------------------------------------------ 書く口(1 つ)
    def append(self, ev: Event) -> EventId | None:
        """出来事を 1 行書き、id ``(t_ns, seq)`` を返す(記録しないときは ``None``)。**書く口はこれ 1 つ**。"""
        if type(ev) is not Event:
            raise TypeError(f"EventLog.append は Event だけを受け取る(いま {type(ev)!r})")
        if ev.id is not None:
            raise ValueError("Event.id は記録が付ける(読み返した行・id を付けた行は書けない)")
        if type(ev.cause) not in CAUSE_TYPES:
            raise TypeError(f"出来事の原因は 3 種類だけ(いま {type(ev.cause)!r})")
        if type(ev.cause) is Experiment:
            # CP12(書くとき=検収 M1): 実験の条件の行を書けるのも gate.admit だけ。型を作るときの検査だけでは、
            # 読み戻した原因の使い回しと __init__ を通らない偽物(object.__new__・__class__ の差し替え)が通る。
            # 書きの検査の切替口(SHIBUYA_WRITE_GUARD=off)でも外さない(_only_from_gate の注のとおり)。
            _only_from_gate(sys._getframe(1))
        if not self.enabled:
            return None
        if not _G.events_write_allowed():
            raise PermissionError(f"系 {_G.CURRENT} は出来事の記録(E:events.*)を書く宣言を持たない(1-3・writes.paths)")
        t = ev.t_ns
        if t < self._ev_now_ns:
            raise ValueError(f"出来事の時刻 {t} がいまの刻みの頭 {self._ev_now_ns} より前(書き込むその場で記録する=CP12)")
        seq = self._ev_seq_next.get(t, 0)
        self._ev_seq_next[t] = seq + 1
        i = self._ev_n
        if i >= self._ev_t_ns.size:
            self._grow(i + 1)
        self._ev_t_ns[i] = t
        self._ev_seq[i] = seq
        self._ev_who[i] = self._actor_code(ev.who)
        self._ev_what[i] = V.VOCAB_CODES[ev.what]
        self._ev_whom[i] = self._actor_code(ev.whom)
        if ev.where is not None:
            self._ev_where_kind[i] = V.WHERE_KINDS.index(ev.where[0])
            self._ev_where_id[i] = ev.where[1]
        if ev.how_much is not None:
            self._ev_how_much[i] = ev.how_much
        self._ev_via[i] = V.VIA_CODES[ev.via]
        if ev.received_ns is not None:
            self._ev_received_ns[i] = ev.received_ns
        if ev.read_ns is not None:
            self._ev_read_ns[i] = ev.read_ns
        if ev.origin is not None:
            self._ev_origin[i] = self._name_code(ev.origin)
        self._ev_cause[i] = self._cause_code(ev.cause)
        self._ev_n = i + 1
        self._ev_n_appended += 1
        return (t, seq)

    # ------------------------------------------------------------------ 内部の表
    def _grow(self, need: int) -> None:
        cap = max(self._ev_t_ns.size * 2, int(need))
        for n, t, f in _COLS:
            old = getattr(self, n)
            new = np.full(cap, f, dtype=t)
            new[: self._ev_n] = old[: self._ev_n]
            setattr(self, n, new)

    def _name_code(self, s: str) -> int:
        c = self._ev_name_codes.get(s)
        if c is None:
            c = len(self._ev_names)
            self._ev_names.append(s)
            self._ev_name_codes[s] = c
        return c

    def _actor_code(self, x: int | str | None) -> int:
        if x is None:
            return _NONE_I64
        if isinstance(x, str):
            return -1 - self._name_code(x)
        return int(x)

    def _actor_of(self, v: int) -> int | str | None:
        v = int(v)
        if v == _NONE_I64:
            return None
        if v < 0:
            return self._ev_names[-1 - v]
        return v

    def _cause_code(self, c: Any) -> int:
        """原因 → 原因の表の行(無ければ 1 行足す)。過程と実験は名でまとめ、LLM の呼び出しは直前と同じときだけ。"""
        tc = type(c)
        if tc is Process:
            pc = _PROC_CODE[c.name]
            k = self._cz_proc_rows.get(pc)
            if k is None:
                k = self._cz_add(_K_PROC, pc)
                self._cz_proc_rows[pc] = k
            return k
        if tc is Experiment:
            k = self._cz_exp_rows.get(c.cond_id)
            if k is None:
                k = self._cz_add(_K_EXP, len(self._cz_experiments))
                self._cz_experiments.append(c)
                self._cz_exp_rows[c.cond_id] = k
            return k
        last = self._cz_last_llm
        if last is not None and last[0] == c:
            return last[1]
        parts = _canonical_call_id(c.call_id)
        if parts is None:
            k = self._cz_add(_K_LLM, len(self._cz_texts))
            self._cz_texts.append(c.call_id)
        else:
            k = self._cz_add(_K_LLM, -1)
            self._cz_call_t[k], self._cz_call_agent[k], self._cz_call_cls[k] = parts
        if c.source is not None:
            self._cz_src[k] = _SRC_CODE[c.source]
        if c.number is not None:
            self._cz_num[k] = c.number
        ids = c.input_event_ids
        if ids:
            m = len(ids)
            j = self._ci_n
            if j + m > self._ci_t.size:
                self._grow_cols(_CI_COLS, j, j + m)
            self._ci_t[j: j + m] = [x[0] for x in ids]
            self._ci_seq[j: j + m] = [x[1] for x in ids]
            self._cz_in_start[k] = j
            self._cz_in_len[k] = m
            self._ci_n = j + m
        self._cz_last_llm = (c, k)
        return k

    def _cz_add(self, kind: int, ref: int) -> int:
        k = self._cz_n
        if k >= self._cz_kind.size:
            self._grow_cols(_CZ_COLS, k, k + 1)
        self._cz_kind[k] = kind
        self._cz_ref[k] = ref
        self._cz_n = k + 1
        return k

    def _grow_cols(self, cols: tuple[tuple[str, Any, int], ...], used: int, need: int) -> None:
        cap = max(getattr(self, cols[0][0]).size * 2, int(need))
        for n, t, f in cols:
            old = getattr(self, n)
            new = np.full(cap, f, dtype=t)
            new[:used] = old[:used]
            setattr(self, n, new)

    def _cause_at(self, k: int) -> Cause:
        """原因の表の行 → 今の 3 型の物(``LlmCall`` と ``Process`` は列から作る・``Experiment`` は持っている物)。"""
        kind = int(self._cz_kind[k])
        ref = int(self._cz_ref[k])
        if kind == _K_PROC:
            return Process(V.CAUSE_PROCESS_NAMES[ref])
        if kind == _K_EXP:
            return self._cz_experiments[ref]
        cid = (self._cz_texts[ref] if ref >= 0 else
               f"{int(self._cz_call_t[k])}:{int(self._cz_call_agent[k])}:{int(self._cz_call_cls[k])}")
        a, m = int(self._cz_in_start[k]), int(self._cz_in_len[k])
        src, num = int(self._cz_src[k]), int(self._cz_num[k])
        return LlmCall(cid, tuple(zip(self._ci_t[a: a + m].tolist(), self._ci_seq[a: a + m].tolist())),
                       source=None if src < 0 else CANDIDATE_SOURCES[src], number=None if num < 0 else num)

    # ------------------------------------------------------------------ 読む口(試験・計器・後の段の読み手)
    def __len__(self) -> int:
        return self._ev_n

    @property
    def n_appended(self) -> int:
        """これまでに書いた行の数(保持窓で落とした分を含む)。"""
        return self._ev_n_appended

    @property
    def n_evicted(self) -> int:
        return self._ev_n_evicted

    @property
    def nbytes(self) -> int:
        """生きている行の列のバイト(``行数 × ROW_BYTES``。名と原因の表は ``n_names``・``n_causes``)。"""
        return self._ev_n * ROW_BYTES

    @property
    def n_names(self) -> int:
        return len(self._ev_names)

    @property
    def n_causes(self) -> int:
        return self._cz_n

    @property
    def cause_nbytes(self) -> int:
        """〔1-8 J0・1-3 の検収 M2〕原因の表の生きている行の列のバイト(行 × ``CAUSE_ROW_BYTES``+入力の id × ``INPUT_ID_BYTES``)。
        実験の表と、テープの形でない call_id の文字列(試験だけ)は入らない。"""
        return self._cz_n * CAUSE_ROW_BYTES + self._ci_n * INPUT_ID_BYTES

    def ids(self) -> tuple[np.ndarray, np.ndarray]:
        """生きている行の id の 2 列 ``(t_ns, seq)``(読み取り専用の写し)。"""
        return self._ev_t_ns[: self._ev_n].copy(), self._ev_seq[: self._ev_n].copy()

    def index_of(self, eid: EventId) -> int:
        """id の行の位置(無ければ ``-1``)。"""
        n = self._ev_n
        hit = np.flatnonzero((self._ev_t_ns[:n] == int(eid[0])) & (self._ev_seq[:n] == int(eid[1])))
        return int(hit[0]) if hit.size else -1

    def event(self, i: int) -> Event:
        """位置 ``i`` の行を ``Event``(id つき)に戻す。"""
        if not 0 <= int(i) < self._ev_n:
            raise IndexError(i)
        i = int(i)
        wk = int(self._ev_where_kind[i])
        hm = int(self._ev_how_much[i])
        rc, rd, og = int(self._ev_received_ns[i]), int(self._ev_read_ns[i]), int(self._ev_origin[i])
        return Event(
            id=(int(self._ev_t_ns[i]), int(self._ev_seq[i])), t_ns=int(self._ev_t_ns[i]),
            who=self._actor_of(self._ev_who[i]), what=V.VOCAB[int(self._ev_what[i])],
            whom=self._actor_of(self._ev_whom[i]),
            where=None if wk < 0 else (V.WHERE_KINDS[wk], int(self._ev_where_id[i])),
            how_much=None if hm == _NONE_I64 else hm, via=V.VIA_WORDS[int(self._ev_via[i])],
            received_ns=None if rc < 0 else rc, read_ns=None if rd < 0 else rd,
            origin=None if og < 0 else self._ev_names[og], cause=self._cause_at(int(self._ev_cause[i])),
        )

    def get(self, eid: EventId) -> Event:
        i = self.index_of(eid)
        if i < 0:
            raise KeyError(eid)
        return self.event(i)

    def events(self) -> Iterator[Event]:
        """生きている行を順に(試験・診断用。大きい記録には使わない)。"""
        for i in range(self._ev_n):
            yield self.event(i)

    def what_counts(self, start: int = 0) -> dict[str, int]:
        """位置 ``start`` から後の生きている行の ``what`` の分布(語彙表の順・0 は出さない)。"""
        c = np.bincount(self._ev_what[int(start): self._ev_n].astype(np.int64), minlength=len(V.VOCAB))
        return {V.VOCAB[k]: int(c[k]) for k in np.flatnonzero(c)}

    def cause_counts(self, start: int = 0) -> dict[str, int]:
        """位置 ``start`` から後の生きている行の原因の種類の分布。"""
        if self._ev_n <= int(start):
            return {}
        kinds = self._cz_kind[: self._cz_n].astype(np.int64)  # 種類の番号は CAUSE_KINDS の並び
        c = np.bincount(kinds[self._ev_cause[int(start): self._ev_n].astype(np.int64)], minlength=len(CAUSE_KINDS))
        return {CAUSE_KINDS[k]: int(c[k]) for k in np.flatnonzero(c)}

    # ------------------------------------------------------------------ 日の締め(計器と保持窓)
    def close_day(self, day: int) -> dict[str, Any]:
        """日 ``day`` の締め: その日の行数・バイト・``what`` と原因の種類の分布を返し、保持窓の外の行を落とす。

        manifest の日次の記録 ``events`` の中身(計器)。記録しないときは ``{"on": False, ...}``(形は同じ)。
        """
        if not self.enabled:
            return {"on": False, "rows": 0, "bytes": 0, "by_what": {}, "by_cause": {}, "live_rows": 0,
                    "live_bytes": 0, "evicted": 0}
        n_day = self._ev_n_appended - self._ev_day_mark
        start = max(0, self._ev_n - n_day)
        out: dict[str, Any] = {"on": True, "rows": int(n_day), "bytes": int(n_day * ROW_BYTES),
                               "by_what": self.what_counts(start), "by_cause": self.cause_counts(start)}
        dropped = self._evict_before((int(day) + 1 - self.retention_days) * NS_PER_DAY)
        self._ev_day_mark = self._ev_n_appended
        out.update({"live_rows": int(self._ev_n), "live_bytes": int(self.nbytes), "evicted": int(dropped)})
        return out

    def _evict_before(self, cutoff_ns: int) -> int:
        n = self._ev_n
        if cutoff_ns <= 0 or n == 0:
            return 0
        keep = self._ev_t_ns[:n] >= int(cutoff_ns)
        n_keep = int(keep.sum())
        if n_keep == n:
            return 0
        for name, _t, f in _COLS:
            col = getattr(self, name)
            kept = col[:n][keep]
            col[:n_keep] = kept
            col[n_keep:n] = f
        self._ev_n = n_keep
        # 原因の表を生きている行が指すものだけに詰め直す(LLM の呼び出しは 1 回ごとに原因が 1 つ=表が伸び続けない)
        live = np.unique(self._ev_cause[:n_keep])
        remap = np.full(self._cz_n, -1, dtype=np.int32)
        remap[live] = np.arange(live.size, dtype=np.int32)
        self._compact_causes(live)
        self._ev_cause[:n_keep] = remap[self._ev_cause[:n_keep]]
        if self._cz_last_llm is not None:
            r = int(remap[self._cz_last_llm[1]])
            self._cz_last_llm = None if r < 0 else (self._cz_last_llm[0], r)
        dropped = n - n_keep
        self._ev_n_evicted += dropped
        return dropped

    def _compact_causes(self, live: np.ndarray) -> None:
        """原因の表を ``live``(残す行の番号・昇順)だけにする。入力の id とテープの形でない call_id の表も詰める。"""
        n_live = int(live.size)
        kind = self._cz_kind[live].copy()
        ref = self._cz_ref[live].copy()
        start = self._cz_in_start[live]
        ln = self._cz_in_len[live].astype(np.int64)
        # 入力の id: 残す行の範囲をつないだ位置(``np.repeat`` で範囲を 1 本の添字にする)
        tot = int(ln.sum())
        new_start = np.zeros(n_live, dtype=np.int64)
        if n_live:
            np.cumsum(ln[:-1], out=new_start[1:])
        if tot:
            idx = np.repeat(start - new_start, ln) + np.arange(tot, dtype=np.int64)
            ci_t, ci_seq = self._ci_t[idx].copy(), self._ci_seq[idx].copy()
        # テープの形でない call_id の文字列(LLM の行で ref ≥ 0)
        texts: list[str] = []
        txt_rows = np.flatnonzero((kind == _K_LLM) & (ref >= 0))
        for j in txt_rows.tolist():  # 逐次ループ宣言: テープの形でない call_id の行の数(ランでは 0)
            texts.append(self._cz_texts[int(ref[j])])
            ref[j] = len(texts) - 1
        made = {"_cz_kind": kind, "_cz_ref": ref, "_cz_in_start": new_start, "_cz_in_len": ln.astype(np.int32)}
        for n, _t, f in _CZ_COLS:
            col = getattr(self, n)
            col[:n_live] = made[n] if n in made else col[live].copy()
            col[n_live: self._cz_n] = f
        if tot:
            self._ci_t[:tot] = ci_t
            self._ci_seq[:tot] = ci_seq
        self._ci_t[tot: self._ci_n] = 0
        self._ci_seq[tot: self._ci_n] = 0
        self._cz_n, self._ci_n, self._cz_texts = n_live, tot, texts
        self._cz_proc_rows = {int(ref[j]): int(j) for j in np.flatnonzero(kind == _K_PROC).tolist()}
        self._cz_exp_rows = {self._cz_experiments[int(ref[j])].cond_id: int(j)
                             for j in np.flatnonzero(kind == _K_EXP).tolist()}

    # ------------------------------------------------------------------ 成長の宣言(D-R2-6 の 5 欄)
    def growth_declaration(self, *, rows_per_agent_day: float = 1.0, cap_bytes: int = 256 * 1024 * 1024,
                           decision_rows_per_agent_day: float = 0.0) -> GrowthDeclaration:
        """この記録の成長の宣言(1-3 の見込み=未リサーチ(expedient)。ランの成長の報告にはまだ載せない)。

        ``decision_rows_per_agent_day``: 〔第 1 期 1-8 J0・検収 L2〕腕 ``--decision-port port`` のランだけ渡す判断の出来事の
        行(1 判断 1 行=出来事の行 ``ROW_BYTES``+原因の表の行 ``CAUSE_ROW_BYTES``)。既定 0=腕 legacy(今の宣言のまま)。
        口の層 ``engine.decision.layer.DecisionLayer.event_growth`` が mock の実測の値で渡す。
        """
        d = float(decision_rows_per_agent_day)
        if d < 0.0:
            raise ValueError("decision_rows_per_agent_day は 0 以上")
        rows = float(rows_per_agent_day) + d
        note = ("expedient(1-3)。1 行 ROW_BYTES の列(SoA)。保持窓は ActualLog と同じ 7 日。1-3 で配線したのは世界過程"
                "(ActualLog の行)と区切りだけ=行数は 1 日の実測を記録に書いた(全部の系を載せた後に見直す)")
        if d > 0.0:
            note += (f"。1-8 J0 の腕 port: 判断の出来事 {d:g} 行/体/日 × (ROW_BYTES {ROW_BYTES}+原因の表の行 "
                     f"CAUSE_ROW_BYTES {CAUSE_ROW_BYTES}) B を足した(記録 j0/README.md §5)")
        return GrowthDeclaration(
            name="event_log", per_agent_bytes=0, per_cell_bytes=0, per_day_growth="O(N)",
            per_day_growth_coef=float(rows_per_agent_day * ROW_BYTES + d * (ROW_BYTES + CAUSE_ROW_BYTES)),
            retention=Retention(self.retention_days, "manifest の日次の記録(行数と種類の分布)"),
            worst_case_ops_per_tick=int(max(1.0, rows * 1000 / STEPS_PER_DAY)), cap=int(cap_bytes),
            cap_budget_row="S1", mechanism=False, note=note,
            unit="行", bytes_per_unit=ROW_BYTES, growth_per_simday=rows,
        )
