"""engine.step_scope — 何かあった体だけ(第 6 期 6-3 時計の段 T3・腕 ``--step-scope changed``)。

正典: 決定 10-12 §4-2 TM6 の T3(何かあった人だけ=まず「全員を毎回見る版」との一致の確認・その後に驚き駆動=カレンダー 1b と
同じ版上げ)・TM5(体の変化は次に段の境目を越える時刻を予約する=3-5 の腕 reserve)・時間のモデルの草案 TM5 の背景(全員に毎回
かけている 4 つの処理=スケジューラ・反映・知覚・変化の検出)。記録 ``docs/bench/analysis/wallbounce-1012/tm234/README.md``。

腕(切替口): ``--step-scope {all,changed}``(環境変数 ``SHIBUYA_STEP_SCOPE``・:func:`set_arm`)。既定 ``all``=今の全員を
毎回見る版(持ち主を作らない)。``changed`` は刻みの処理のうち体の数に比例する走査を「何かあった体」の配列に絞る。

絞る処理(配列の絞り込み=体ごとの Python のループは無い):

1. **反映(体の自然な変化)**: 本人の体の層の TM5 の予約(3-5 の腕 reserve=予約の境目)を使う(組み立てが腕 changed のときは
   体の層を reserve で作る)。予約の来た体と入力の変わった体だけを規則に通す。
2. **変化の検出(内受容の段の跨ぎ)**: 検出器 ``ChangeDetector.detect`` の内受容 3 変数の判定を、「変化の印」の付いた体だけに
   通す(``scope=`` の口)。変化の印=前の検出の後に内受容の値(空腹・疲れ・体感温度)か段が変わった体 ∪ 前の検出で段を
   跨いだ体(段は 1 回に 1 段しか動かない=跨いだ体は次の検出でもう 1 段跨ぐことがある)。最初の検出(組み立ての後・再開の
   後)は写しが無い=全員。

事象(到着・退出・会話・購入・予約の境目・知らせ・判断の予定)と印の関係: 到着と退出は計画実行層の日の事象の表・会話は
会話の管理のセッション・購入と食事は解決の段階 C の行・知らせ(計画の境目・活動の満了)と判断の予定は起床の候補の配列で、
どれも前から事象の数ぶんの配列で処理している。そのうち内受容の値を動かすもの(食事・休み・就寝・移動の消費・体感温度)は、
値の変化として変化の印に現れる。書き手が resolve の 11 の関数に散っていて 1 つの知らせの口が無いため、印は写しとの比べ
(内受容の値と段の 6 列)で付ける(つなぎの台帳 ``DOC-tm234-t3-mark-by-copy``=3-5 の ``BR-BODY-RESERVE-DETECT`` と
同じ形・外す段=驚き駆動の版上げで書き手の知らせの口に替える)。

絞らない処理(記録 §T3): セルの描画欄の変化の起床(変化したセルの事象から引く・体の走査は numba の 1 本)・知覚の前計算
(セルごと)・空腹の語の段の時間の延べ(``EnergyLayer.after_tick``=全員の和の計器)・計器 observe。

受入: 腕 changed と既定 all が byte-check 19 構成で final・テープ・25 欄とも同じ(記録 §T3 の表)。変化の印は
「判定の結果が変わりうる体」の上界(値も段も変わらず前に跨いでいない体は、判定の入力が前と同じ=前と同じく跨がない)。

状態(状態台帳の腕の行 ``T3M``=軸 1 diag・軸 2 discardable): 内受容の値と段の写し(体 × 6 列の uint8)・前の検出で跨いだ体・
計器。再開では写しを捨てる(再開の後の最初の検出は全員=通しと同じ結果)。

逐次ループ宣言(P4): なし(写しの比べと絞り込みは配列演算・内受容 3 変数 × 段の境目 3 つの定数回)。
"""

from __future__ import annotations

import os
import time
from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

from shibuya.engine import owner_guard as _OG
from shibuya.engine.change_detect import INTERO_VARS

__all__ = [
    "SCHEMA", "ENV", "FP_KEY", "ARM_ALL", "ARM_CHANGED", "ARMS", "DEFAULT_ARM", "arm", "set_arm", "is_default",
    "NARROWED", "NOT_NARROWED", "StepScope", "CONFIG_KEYS", "OBSERVED_KEYS", "manifest_fields", "make",
]

SCHEMA: Final[str] = "shibuya.engine.step_scope/1"
ENV: Final[str] = "SHIBUYA_STEP_SCOPE"
FP_KEY: Final[str] = "step_scope"
ARM_ALL: Final[str] = "all"
ARM_CHANGED: Final[str] = "changed"
ARMS: Final[tuple[str, ...]] = (ARM_ALL, ARM_CHANGED)
DEFAULT_ARM: Final[str] = ARM_ALL

_raw = os.environ.get(ENV, "").strip().lower()
if _raw and _raw not in ARMS:
    raise ValueError(f"{ENV} は {ARMS} のどれか(いま {_raw!r})")
_ARM: str = _raw or DEFAULT_ARM
del _raw


def arm() -> str:
    """いまの腕(``all``=既定・``changed``)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(CLI ``--step-scope``・試験の切替口)。組み立ての時に読む。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"--step-scope は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def is_default(name: str | None = None) -> bool:
    return (_ARM if name is None else str(name)) == DEFAULT_ARM


#: 腕 changed で絞る処理(manifest の設定に写す)。
NARROWED: Final[tuple[str, ...]] = ("body:TM5 の予約(3-5 の reserve)", "detect:内受容の段の跨ぎ(変化の印)")
#: 絞らない処理(体の数に比例する走査が残る所・記録 §T3)。
NOT_NARROWED: Final[tuple[str, ...]] = (
    "detect:セルの描画欄の変化の起床(体の走査は numba の 1 本)", "perceive_prepare:セルごとの前計算",
    "energy_after:空腹の語の段の時間の延べ(全員の和の計器)", "observe:計器")

#: 写しの列(内受容の値 3 つと段 3 つ=検出器の判定の入力の全部)。
_COLS: Final[tuple[str, ...]] = tuple(v for v, _ in INTERO_VARS) + tuple(s for _, s in INTERO_VARS)


class StepScope:
    """何かあった体の印(状態台帳の腕の行 ``T3M``・持ち主の名 ``step_scope``)。腕 changed のランだけ組み立てが作る。

    〔6-3 検収 M2〕実行時の守り(``engine.owner_guard``=3-2 の ``WindowQueue`` と同じ形): 欄の代入と消去は ``AttributeError``
    (書く口は ``__init__``・``detect``・``after_detection`` の自分の文だけ・検出器を呼ぶ間は閉じる)。写しの配列と跨いだ体は書けない
    印つき(外から ``x._ss_copy["hunger"][0] = …`` は ``ValueError``)・写しの表と計器は読み取り専用の写し(``MappingProxyType``)。
    """

    #: 状態台帳の腕の行の腕の名(``LedgerRow.arm``)。
    LEDGER_ARM: str = "step-scope"
    name: str = "step_scope"

    def __init__(self, n_agents: int) -> None:
        h = _OG.hidden(self)
        h["copy"] = {}
        h["meter"] = {
            "steps": 0, "full_steps": 0, "marked": 0, "marked_max": 0, "crossed": 0, "full_equiv": 0,
            "detect_seconds_nondeterministic": 0.0,
        }
        with _OG.writing(self):
            self.n = int(n_agents)
            #: 内受容の値と段の写し(列の名 → 書けない印つきの uint8 の配列・最初の検出の前は空=全員)(行 T3M)。
            self._ss_copy: Mapping[str, np.ndarray] = MappingProxyType(h["copy"])
            #: 前の検出で段を跨いだ体(昇順・次の検出で必ず見る・書けない印つき)(行 T3M)。
            self._ss_crossed: np.ndarray = _OG.frozen_array(np.empty(0, dtype=np.int64))
            #: 今の検出で見た体(None=全員)=検出から ``after_detection`` までの作業の値(行 T3M の外=除外の表)。
            self._ss_idx: np.ndarray | None = None
            #: 計器(行 T3M・読み取り専用の写し)。
            self._ss_meter: Mapping[str, Any] = MappingProxyType(h["meter"])

    def __setattr__(self, name: str, value: Any) -> None:
        _OG.guarded_setattr(self, name, value, "変化の印")

    def __delattr__(self, name: str) -> None:
        _OG.guarded_delattr(self, name, "変化の印")

    # ------------------------------------------------------------------ 口
    def marks(self, agents: Any) -> np.ndarray | None:
        """変化の印の付いた体(昇順の int64)。写しが無い(最初の検出・再開の後)ときは None=全員。"""
        if not self._ss_copy:
            return None
        r = agents.registry
        ch = np.zeros(self.n, dtype=bool)
        for c in _COLS:  # 逐次: 列の数ぶん(6)
            ch |= r.field(c).view(np.uint8) != self._ss_copy[c]
        if self._ss_crossed.size:
            ch[self._ss_crossed] = True
        return np.flatnonzero(ch).astype(np.int64)

    def detect(self, detector: Any, world: Any, agents: Any, step: int, *, field_rows: Any = None) -> Any:
        """検出器を変化の印の体だけに通す(``ChangeDetector.detect`` の ``scope=``)。結果は全員を見る版と同じ。"""
        idx = self.marks(agents)
        with _OG.writing(self):
            self._ss_idx = None if idx is None else _OG.frozen_array(idx)
        m = _OG.hidden(self)["meter"]
        t0 = time.perf_counter()
        det = detector.detect(world, agents, step, field_rows=field_rows, scope=idx)
        m["detect_seconds_nondeterministic"] += time.perf_counter() - t0
        m["steps"] += 1
        m["full_equiv"] += self.n
        k = self.n if idx is None else int(idx.size)
        if idx is None:
            m["full_steps"] += 1
        m["marked"] += k
        m["marked_max"] = max(int(m["marked_max"]), k)
        return det

    def after_detection(self, agents: Any, det: Any) -> None:
        """``resolve.apply_detection`` の後: 見た体の写しを今の値と段にし、段を跨いだ体を次の検出の印に残す
        (印の外の体は値も段も写しと同じ=書き直さない)。"""
        r = agents.registry
        h = _OG.hidden(self)
        parts = [c.agent_id for c in det.crossings if c.agent_id.size]
        crossed = np.unique(np.concatenate(parts)).astype(np.int64) if parts else np.empty(0, dtype=np.int64)
        idx = self._ss_idx
        copy, base = h["copy"], h.setdefault("base", {})
        if idx is None or not copy:
            for c in _COLS:  # 逐次: 列の数ぶん(6)
                b = np.array(r.field(c).view(np.uint8), dtype=np.uint8, copy=True)
                base[c] = b  # 持ち主の中の書ける写し
                copy[c] = _OG.frozen_array(b.view())  # 欄には書けない印つきのビュー
        elif idx.size:
            for c in _COLS:  # 逐次: 列の数ぶん(6)
                base[c][idx] = np.array(r.field(c).view(np.uint8)[idx], dtype=np.uint8, copy=True)
        with _OG.writing(self):
            self._ss_idx = None
            self._ss_crossed = _OG.frozen_array(crossed)
        h["meter"]["crossed"] += int(crossed.size)

    # ------------------------------------------------------------------ 計器
    def observed(self) -> dict[str, Any]:
        m = self._ss_meter
        out = {k: (float(v) if isinstance(v, float) else int(v)) for k, v in m.items()}
        steps = max(1, int(m["steps"]))
        out["marked_mean"] = round(int(m["marked"]) / steps, 6)
        out["marked_share"] = round(int(m["marked"]) / max(1, int(m["full_equiv"])), 9)
        return out


CONFIG_KEYS: Final[tuple[str, ...]] = ("schema", "arm", "narrowed", "not_narrowed", "mark_columns", "body_schedule")
OBSERVED_KEYS: Final[tuple[str, ...]] = ("steps", "full_steps", "marked", "marked_max", "crossed", "full_equiv",
                                         "detect_seconds_nondeterministic", "marked_mean", "marked_share")


def manifest_fields(scope: StepScope | None, *, body_schedule: str = "") -> dict[str, Any] | None:
    """manifest の ``step_scope``(腕 changed のランだけ・既定の腕は None=節を出さない)。"""
    if scope is None:
        return None
    return {"schema": SCHEMA, "arm": ARM_CHANGED, "narrowed": list(NARROWED), "not_narrowed": list(NOT_NARROWED),
            "mark_columns": list(_COLS), "body_schedule": str(body_schedule), **scope.observed()}


def make(n_agents: int) -> StepScope | None:
    """組み立ての口: 腕 changed のときだけ印の持ち主を作る(既定 all は None=今の道)。"""
    return StepScope(int(n_agents)) if _ARM == ARM_CHANGED else None
