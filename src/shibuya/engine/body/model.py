"""engine.body.model — 本人の体の層 ``BodyModel``(状態台帳の外の状態の持ち主 ``body``=行 ``BD``・第 3 期 3-5)。

体の層は ③ 群(意図しない体と System 1 の反応)の持ち主。値の式は :mod:`engine.body.rules`(3-5 より前の場所と同じ値)、
TM5 の予約は :mod:`engine.body.schedule`。組み立てが 1 つ作り(既定の腕 sweep でも作る=manifest の ``body`` と段の境目の
列の計器のため)、ランの間は次の口から呼ばれる:

- **書く口は 2 つ**(体の層の欄=予約の列 ``_reservations`` と計器 ``_body_meter`` を書くのはこの 2 つとその下請けだけ):
  :meth:`initial`(刻み 0 の体の状態=``resolve.initialize``・``initialize_energy`` が呼ぶ・予約を空に戻す)と
  :meth:`step`(``part="interoception"``=体の刻みの空腹と疲れ=``resolve.advance_body`` が呼ぶ/``part="felt"``=5 分の
  窓の体感温度=``EnvironmentProcess.step`` が呼ぶ)。どちらも SoA は書かない=書く値を返し、書くのは ``engine.resolve``
  (書き込み口は resolve 一本のまま)。
- **値だけの口**(状態を持たない): :meth:`felt_temperature`・:meth:`felt_cells`(体感温度の写像)・:meth:`collapse_draw`
  (倒れる=顕著行為の引き金)。
- 読む口: :meth:`observed`・:attr:`meter_view`・:meth:`manifest_fields`。

欄は組み立ての 1 回だけ置ける(付け替え・消すのは断る=近接の層と同じ守り)。

段の境目の列(計器・腕の一致の受入): 体の規則(:meth:`step`)が値を変えた (刻み, 種類, 体, 前の値, 後の値) を、刻みごと・
種類の順(空腹 → 疲れ → 暑さ)・体の昇順で鎖のハッシュ ``boundary_digest`` に足し、種類ごとの数を数える。sweep と reserve
で同じでなければならない(:mod:`engine.body.schedule` の受入)。〔3-5 検収 L6・親の判断〕この計器は環境変数
``SHIBUYA_BODY_BOUNDARY_GAUGE=1`` のとき(か ``BodyModel(gauge=True)``)だけ数える(新旧の値の比べと鎖のハッシュの分の時間を
既定のランに足さない)。既定は数えない=manifest の ``body.boundaries``・``boundary_digest`` は null。腕の一致の試験と記録の
比べは立てて回す。

逐次ループ宣言(P4): 体数に比例する Python のループは無い。
"""

from __future__ import annotations

import os
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping

import numpy as np

from shibuya.core.time_consts import STEP_SECONDS
from shibuya.engine.body import rules as BR
from shibuya.engine.body import schedule as BS
from shibuya.engine.body import system1 as S1

__all__ = ["SCHEMA", "BodyModel", "PARTS", "PART_INTERO", "PART_FELT", "CONFIG_KEYS", "OBSERVED_KEYS",
           "manifest_fields", "DIGEST_START", "GAUGE_ENV", "gauge_on"]

#: manifest の ``body`` の形の版(欄の意味を変えたら上げる)。
SCHEMA: Final[str] = "shibuya.engine.body/1"
PART_INTERO: Final[str] = "interoception"
PART_FELT: Final[str] = "felt"
PARTS: Final[tuple[str, ...]] = (PART_INTERO, PART_FELT)
#: 段の境目の列の鎖のハッシュの始まり。
DIGEST_START: Final[str] = "0" * 64
#: 〔3-5 検収 L6〕段の境目の計器を数える環境変数(``1`` のときだけ・既定は数えない)。
GAUGE_ENV: Final[str] = "SHIBUYA_BODY_BOUNDARY_GAUGE"


def gauge_on() -> bool:
    """段の境目の計器を数えるか(環境変数 ``SHIBUYA_BODY_BOUNDARY_GAUGE`` が ``1``)。組み立てのときに読む。"""
    return os.environ.get(GAUGE_ENV, "").strip() == "1"
#: manifest の ``body`` の子の鍵(設定=ランの前に決まる/観測=ランの結果)。``engine.manifest_sections`` と同じ並び。
CONFIG_KEYS: Final[tuple[str, ...]] = ("schema", "owner", "arm", "arms", "rules", "expedients", "reserve_expedients",
                                       "system1")
OBSERVED_KEYS: Final[tuple[str, ...]] = ("steps", "agent_evals", "due", "replans", "reservations", "felt_frames",
                                         "felt_evals", "felt_due", "felt_moved", "felt_reservations", "felt_tables",
                                         "pending", "boundaries", "boundary_digest")


def _new_meter() -> dict[str, Any]:
    return {
        "steps": 0, "agent_evals": 0, "due": 0, "replans": 0, "reservations": 0,
        "felt_frames": 0, "felt_evals": 0, "felt_due": 0, "felt_moved": 0, "felt_reservations": 0, "felt_tables": 0,
        "boundaries": {k: 0 for k in BS.BOUNDARY_KINDS}, "boundary_digest": DIGEST_START,
    }


class BodyModel:
    """本人の体の層(持ち主 ``body``)。``arm``=TM5 の腕(``sweep``/``reserve``)・``n``=体の数・``gauge``=段の境目の計器を
    数えるか(既定は環境変数 ``SHIBUYA_BODY_BOUNDARY_GAUGE``)。"""

    __slots__ = ("arm", "n", "step_seconds", "gauge", "_reservations", "_body_meter")

    def __init__(self, n_agents: int, *, arm: str | None = None, step_seconds: int = STEP_SECONDS,
                 gauge: bool | None = None) -> None:
        a = BS.arm() if arm is None else str(arm)
        if a not in BS.ARMS:
            raise ValueError(f"体の予約の腕は {BS.ARMS} のどれか(いま {a!r})")
        self.arm = a
        self.n = int(n_agents)
        self.step_seconds = int(step_seconds)
        self.gauge = gauge_on() if gauge is None else bool(gauge)
        self._reservations = BS.BodySchedule(self.n, a)
        self._reservations.reset()
        self._body_meter = _new_meter()

    def __setattr__(self, name: str, value: Any) -> None:
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"体の層の欄 {name} は付け替えられない(書く口は step・initial だけ)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"体の層の欄 {name} は消せない")

    # ================================================================= 値だけの口(状態を持たない)
    #: 体感温度の写像(暑さ段 → 体感 × 日陰)=全員の値(``uint8``)。
    felt_temperature = staticmethod(BR.felt_temperature)
    #: 体感温度のセルごとの値(末尾は舞台の外の体)。
    felt_cells = staticmethod(BR.felt_cells)
    #: 倒れる(顕著行為の引き金=ポアソン)。
    collapse_draw = staticmethod(BR.collapse_draw)

    # ================================================================= 書く口 1: 刻み 0 の体の状態(D18)
    def initial(self, n: int | None = None, *, energy: Any = None, eer: np.ndarray | None = None) -> BR.BodyInitial:
        """刻み 0 の体の状態(``energy`` を渡すとエネルギー収支の食後の消費・空腹の写しと段)。予約と写しを空に戻す
        (次の刻みで全員を規則に通す)。値は 3-5 より前の ``resolve.initialize``・``initialize_energy`` と同じ。"""
        self._reservations.reset()
        if energy is not None:
            return BR.initial_energy_values(energy, np.asarray(eer))
        return BR.initial_values(self.n if n is None else int(n))

    # ================================================================= 書く口 2: 体の刻み・体感温度の窓
    def step(self, part: str, r: Any, now: int, **kw: Any) -> Any:
        """体の規則を 1 回。``part="interoception"``(空腹と疲れ・``energy``・``activity_columns``)は
        :class:`engine.body.rules.InteroUpdate` か None、``part="felt"``(``cells``・``frame``・``serial``・``table_fn``)は
        ``(書く体 or None=全員, 値)``。``r`` は ``agents.registry``(読むだけ)。"""
        if part == PART_INTERO:
            return self._step_intero(r, int(now), energy=kw.get("energy"),
                                     activity_columns=bool(kw.get("activity_columns", False)))
        if part == PART_FELT:
            return self._step_felt(r, int(now), cells=kw["cells"], frame=int(kw["frame"]), serial=int(kw["serial"]),
                                   table_fn=kw.get("table_fn"))
        raise ValueError(f"体の刻みの部分は {PARTS} のどれか(いま {part!r})")

    # ---- 下請け(step だけが呼ぶ) ----
    def _note(self, now: int, kind: str, ids: np.ndarray | None, old: np.ndarray, new: np.ndarray | None) -> None:
        """体の規則が値を変えた体を段の境目の列に足す(``ids``=None は全員・計器を数えるランだけ)。"""
        if new is None or not self.gauge:
            return
        ch = np.asarray(new) != np.asarray(old)
        if not ch.any():
            return
        who = np.flatnonzero(ch) if ids is None else np.asarray(ids, dtype=np.int64)[ch]
        m = self._body_meter
        m["boundaries"][kind] += int(who.size)
        m["boundary_digest"] = BS.chain_digest(m["boundary_digest"], now, kind, who,
                                               np.asarray(old)[ch], np.asarray(new)[ch])

    def _step_intero(self, r: Any, now: int, *, energy: Any, activity_columns: bool) -> BR.InteroUpdate | None:
        m = self._body_meter
        if self.arm == BS.ARM_SWEEP:
            upd = BR.interoception(r, now, energy=energy, activity_columns=activity_columns)
            if upd is None:
                return None
            m["steps"] += 1
            m["agent_evals"] += self.n
            self._note(now, "hunger", None, r.hunger, upd.hunger)
            self._note(now, "fatigue", None, r.fatigue, upd.fatigue)
            return upd
        return self._reserve_intero(r, now, energy=energy, ac=activity_columns)

    def _reserve_intero(self, r: Any, now: int, *, energy: Any, ac: bool) -> BR.InteroUpdate | None:
        """TM5 の予約の腕の体の刻み(予約の来た体と入力の変わった体だけを規則に通す・値は sweep と同じ)。"""
        body_now, rest_now = BR.rule_steps(now, ac)
        if energy is None and not (body_now or rest_now):
            return None
        plan, m = self._reservations, self._body_meter
        spent = since = None
        if energy is not None:  # エネルギーの積み上げは全員(RESERVE_EXPEDIENTS の 2)
            spent = BR.energy_spent(energy, r.activity, r.transit_state, r.activity_kind if ac else None, r.eer_kcal)
            since = r.since_meal_kcal + spent
        primed = plan.intero_primed
        changed = plan.intero_changed(r, activity_columns=ac, spent=spent)
        due = plan.intero_due(now)
        if primed:
            mask = changed.copy()
            mask[due] = True
            ids: np.ndarray | None = np.flatnonzero(mask)
            m["due"] += int(due.size)
            m["replans"] += int(np.count_nonzero(changed))
        else:
            ids = None
        m["steps"] += 1
        m["agent_evals"] += self.n if ids is None else int(ids.size)
        sel: Any = slice(None) if ids is None else ids
        act = r.activity[sel]
        kind = r.activity_kind[sel] if ac else None
        until = r.activity_until[sel] if ac else None
        f_old = r.fatigue[sel]
        h_old = r.hunger[sel]
        rule_now = body_now or rest_now
        f_new = BR.fatigue_after(f_old, act, kind, until, now, body_now, rest_now) if rule_now else f_old
        if energy is None:
            h_new = BR.hunger_v1_after(h_old, body_now)
            write_h = body_now
        else:
            h_new = BR.hunger_copy_of(energy, since[sel], r.eer_kcal[sel])
            write_h = True
        self._note(now, "hunger", ids, h_old, h_new if write_h else None)
        self._note(now, "fatigue", ids, f_old, f_new if rule_now else None)
        at = BS.next_intero_steps(
            now, f=f_new, h=h_new, act=act, kind=kind, until=until, activity_columns=ac, energy=energy,
            since=None if since is None else since[sel], eer=None if energy is None else r.eer_kcal[sel],
            spent=None if spent is None else spent[sel])
        m["reservations"] += plan.intero_plan(now, np.arange(self.n, dtype=np.int64) if ids is None else ids, at)
        plan.intero_snapshot(r, ids, f=f_new, h=h_new, activity_columns=ac, spent=spent, since=since)
        return BR.InteroUpdate(ids, f_new if rule_now else None, ids, h_new if write_h else None, since, spent)

    def _step_felt(self, r: Any, now: int, *, cells: np.ndarray, frame: int, serial: int,
                   table_fn: Callable[[], np.ndarray] | None) -> tuple[np.ndarray | None, np.ndarray]:
        m = self._body_meter
        cells = np.asarray(cells, dtype=np.uint8)
        n_cells = int(cells.size) - 1
        cols = BR.felt_columns(r.cell, n_cells)
        m["felt_frames"] += 1
        if self.arm == BS.ARM_SWEEP:
            vals = cells[cols]
            m["felt_evals"] += self.n
            self._note(now, "thermal", None, r.thermal, vals)
            return None, vals
        plan = self._reservations
        if table_fn is None:
            raise ValueError("体感温度の予約の腕は日の表の口(table_fn)が要る")
        table = table_fn()
        ids: np.ndarray | None
        if table is not plan.felt_table:  # 表が替わった(日の頭・天気の日付の差し替え・最初)=全員を見直す
            plan.felt_new_table(table, serial, int(table.shape[0]))
            m["felt_tables"] += 1
            ids = None
        else:
            due = plan.felt_due(serial)
            moved = cols != plan.felt_col
            m["felt_due"] += int(due.size)
            m["felt_moved"] += int(np.count_nonzero(moved))
            moved[due] = True
            ids = np.flatnonzero(moved)
        if not np.array_equal(table[int(frame)], cells):  # 守り: 予約の前提(その日の表)が今の窓の値と同じ
            raise RuntimeError(f"体感温度の日の表が窓 {frame} の今の値と違う(予約の前提が崩れた・刻み {now})")
        sel: Any = slice(None) if ids is None else ids
        c = cols[sel]
        vals = cells[c]
        m["felt_evals"] += self.n if ids is None else int(ids.size)
        self._note(now, "thermal", ids, r.thermal[sel], vals)
        m["felt_reservations"] += plan.felt_plan(serial, frame, np.arange(self.n, dtype=np.int64) if ids is None
                                                 else ids, c)
        return ids, vals

    # ================================================================= 読む口
    @property
    def meter_view(self) -> Mapping[str, Any]:
        """計器の読むだけの写し。"""
        return MappingProxyType({k: (MappingProxyType(dict(v)) if isinstance(v, dict) else v)
                                 for k, v in self._body_meter.items()})

    def reserved_steps(self) -> np.ndarray:
        """体ごとの生きている内受容の予約の刻み(−1=予約なし・写し=試験と記録の読み口)。"""
        return np.where(self._reservations.intero_seq >= 0, self._reservations.intero_at, -1).astype(np.int64)

    def reserved_frames(self) -> np.ndarray:
        """体ごとの生きている体感温度の予約の窓の通し番号(−1=予約なし・写し)。"""
        return np.where(self._reservations.felt_seq >= 0, self._reservations.felt_at, -1).astype(np.int64)

    def observed(self) -> dict[str, Any]:
        """manifest の ``body`` の観測の子。"""
        m = self._body_meter
        out = {k: (dict(m[k]) if isinstance(m[k], dict) else m[k]) for k in OBSERVED_KEYS if k in m}
        out["pending"] = self._reservations.pending()
        if not self.gauge:  # 〔3-5 検収 L6〕段の境目の計器を数えないラン(既定)は null
            out["boundaries"] = out["boundary_digest"] = None
        return {k: out[k] for k in OBSERVED_KEYS}


def manifest_fields(layer: "BodyModel | None") -> dict[str, Any]:
    """manifest の ``body``(持ち主・腕・規則の出典の表・器だけの 3 件=設定/予約と段の境目の計器=観測)。
    体の層の無いラン(合成の ``run_day`` の古い呼び方)は観測の子が null。"""
    cfg: dict[str, Any] = {
        "schema": SCHEMA,
        "owner": "body",
        "arm": BS.DEFAULT_ARM if layer is None else layer.arm,
        "arms": list(BS.ARMS),
        "rules": [{"id": x.id, "what": x.what, "conf": x.conf, "source": x.source, "bridge": x.bridge,
                   "inventory": x.inventory, "port": x.port} for x in BR.BODY_RULES],
        "expedients": list(BR.BODY_EXPEDIENTS),
        "reserve_expedients": list(BS.RESERVE_EXPEDIENTS),
        "system1": S1.manifest_rows(),
    }
    obs = layer.observed() if layer is not None else {k: None for k in OBSERVED_KEYS}
    return {**cfg, **obs}
