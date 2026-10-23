"""engine.contact.attention — 目と心の向き(第 6 期 6-4 C1・決定 10-12 §4-4 CT0「使っている間の気づきにくさ」=係数を掛けない)。

正(CT0): 目の向き=視線の先を状態に持つ(画面を見ている間、周りは周辺視の粗い気配だけ・気づくまでは起き得るが認識はしない・顔を
上げるのは本人の判断か体の反射)。心の向き=関心の的を状態に持つ(通話・会話・画面のとき、周りの出来事は割り込めたときだけ
処理される=驚き駆動の入口と同じきっかけ)。割り込めなかった出来事の入力への載せ方は 3 つの腕で比べる。「気づいた」は記憶に
残ったかで測る。D-121 の見落としの係数と歩きスマホの係数は 1-2 で消した=ここでも掛けない(決定 10-12 §4-4 CT0)。

持ち主 :class:`Attention`(状態台帳の腕の行 ``CT1A``=軸 1 behavior・軸 2 required・腕 c1 のランだけ):

- ``_gaze``(視線の先 前/画面/手元/相手)・``_focus``(関心の的 周り/画面/通話/会話)・``_gaze_since``(今の視線になった時刻)・
  ``_prev_act``(前の刻みの活動=暇になった境目を見る)。
- 関心の的の決め方(状態から): 通話中 → 通話・視線が画面 → 画面・対面の会話のセッションに参加 → 会話・ほか → 周り。
- 視線が画面になるのは本人の判断(スマホを見る・今読む)だけ。前に戻るのは本人の判断(顔を上げる)か体の反射
  (``engine.body.system1.loud_sound_notice``=3-5 の器=値は空=本段では起きない=計器だけ)か寝たとき(本人が寝るを選んだ=画面は
  閉じる・仮採用)。

形(係数を掛けない):

- **周辺視の粗い気配**(:func:`coarsen`): 視線が画面の体の知覚の事実(``Percept``)は、見えた物(店・目印・看板)を認識しない
  (``seen_objects`` が空・``signage_shown`` が偽)・見えた人は周辺視の範囲(``PERIPHERAL_RANGE_M``)の中の人の数だけ
  (``AttentionView.people_hint``=誰か・何をしているかは分からない)。範囲と細かさの形=確率は使わない。
- **割り込み**(:data:`INTERRUPT_CONDITIONS`): 関心の的が周りでない体は、周りの出来事(B4 の顕著行為)を、その刻みに驚き駆動の
  入口(起床条件 (i) セルの B4 の変化=``WakeCondition.CELL_BLOCK``=``engine.change_detect`` の形)で起きたときだけ処理する。
  処理しなかった出来事は (1) 描画の入力では腕で載せ方を変え(:func:`coarsen`)、(2) 顕著行為の過程の「気づいた体」から外す
  (:func:`gate_salient`=記憶の書き手が気づきとして覚えない=記憶に残らない)。

**未リサーチ(expedient)**(記録 ct_c1/README.md・つなぎの台帳 ``DOC-ct-c1-attention-*``): 周辺視の範囲 2.0 m(2-2 の会話の距離 B3
と同じ値)・関心の的の決め方の順(通話 > 画面 > 会話 > 周り)・寝たら画面を閉じる・暇な活動=待機と乗車(決定の例「待ち・電車」)。

逐次ループ宣言: :func:`gate_salient` は その刻みの顕著行為の数ぶん(≤ 200=顕著イベントの予算)。:func:`coarsen` は見えた人の
数ぶん(≤ 数人=描画の近接の上位)。ほかは体の配列の演算。
"""

from __future__ import annotations

import dataclasses
from typing import Any, Final

import numpy as np

from shibuya.agents.state import Activity, WakeCondition
from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_MINUTE
from shibuya.engine.contact.arm import LEDGER_ARM
from shibuya.perception.contact_view import FOCUS_WORDS, GAZE_WORDS, AttentionView

__all__ = [
    "GAZE_FRONT", "GAZE_SCREEN", "GAZE_HAND", "GAZE_PARTNER", "FOCUS_SURROUND", "FOCUS_SCREEN", "FOCUS_CALL",
    "FOCUS_TALK", "PERIPHERAL_RANGE_M", "INTERRUPT_CONDITIONS", "IDLE_ACTIVITIES", "Attention", "coarsen",
    "gate_salient", "interrupted_of", "PROVISIONAL_VALUES",
]

GAZE_FRONT, GAZE_SCREEN, GAZE_HAND, GAZE_PARTNER = 0, 1, 2, 3
FOCUS_SURROUND, FOCUS_SCREEN, FOCUS_CALL, FOCUS_TALK = 0, 1, 2, 3
assert len(GAZE_WORDS) == 4 and len(FOCUS_WORDS) == 4

#: 周辺視の範囲[m](この中の人だけ気配として数える)。2-2 の会話の距離 B3(2.0 m)と同じ値=仮の値。
PERIPHERAL_RANGE_M: Final[float] = 2.0
#: 驚き駆動の入口(割り込めた)と数える起床条件=セルの B4 の変化(``engine.change_detect`` の (i))。
INTERRUPT_CONDITIONS: Final[frozenset[int]] = frozenset({int(WakeCondition.CELL_BLOCK)})
#: 暇な活動(決定 CT3 の例「待ち・電車」=待機と乗車)。
IDLE_ACTIVITIES: Final[frozenset[int]] = frozenset({int(Activity.WAITING), int(Activity.RIDING)})

#: 本モジュールの仮の値の宣言(つなぎの台帳 DOC-ct-c1-attention-* と 1 対 1)。
PROVISIONAL_VALUES: Final[tuple[str, ...]] = (
    "周辺視の範囲 2.0 m(2-2 の会話の距離 B3 と同じ値)・人の気配の数は粗い段で見せる",
    "関心の的の順 通話 > 画面 > 会話 > 周り・寝たら画面を閉じる・暇な活動=待機と乗車",
    "割り込み=その刻みに起床条件 (i)(セルの B4 の変化)で起きた体(驚き駆動の入口の代わり=T3 で本人の予想との差に替える)",
)


class Attention:
    """体ごとの目と心の向き(状態台帳の腕の行 ``CT1A``・持ち主の道筋 ``contact.attn``)。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

    def __init__(self, n_agents: int) -> None:
        n = int(n_agents)
        self.n = n
        self._gaze = np.zeros(n, dtype=np.int8)
        self._focus = np.zeros(n, dtype=np.int8)
        self._gaze_since = np.full(n, -1, dtype=np.int64)
        self._prev_act = np.full(n, -1, dtype=np.int8)
        #: 体 → 最後に System 1 で気づいた通知 ``[時刻, 種類(0 メッセージ/1 着信), 段, チャネルのビット]``(次の刻みの知覚の事実と
        #: 着信の判断が読む)。
        self._notice: dict[int, list[int]] = {}

    # ------------------------------------------------------------------ 読む口
    def gaze(self, a: Any) -> np.ndarray:
        return self._gaze[np.asarray(a, dtype=np.int64)]

    def focus(self, a: Any) -> np.ndarray:
        return self._focus[np.asarray(a, dtype=np.int64)]

    def gaze_all(self) -> np.ndarray:
        v = self._gaze.view()
        v.flags.writeable = False
        return v

    def focus_all(self) -> np.ndarray:
        v = self._focus.view()
        v.flags.writeable = False
        return v

    def on_screen(self) -> np.ndarray:
        return np.flatnonzero(self._gaze == GAZE_SCREEN).astype(np.int64)

    def notice_of(self, a: int) -> list[int] | None:
        """最後に気づいた通知(無ければ ``None``)。"""
        return self._notice.get(int(a))

    def note_notice(self, a: int, t_ns: int, kind: int, level: int, bits: int) -> None:
        """System 1 が通知に気づいた(その体の最後の通知を置き換える)。"""
        self._notice[int(a)] = [int(t_ns), int(kind), int(level), int(bits)]

    # ------------------------------------------------------------------ 本人の行動(書く口)
    def look_at_screen(self, a: Any, t_ns: int) -> None:
        a = np.asarray(a, dtype=np.int64)
        self._gaze[a] = GAZE_SCREEN
        self._gaze_since[a] = int(t_ns)

    def end_screen(self, a: Any, t_ns: int) -> tuple[np.ndarray, list[int]]:
        """視線が画面の体だけ前に戻し、(戻した体・画面を見ていた長さ[分])を返す(長さは今の視線になった時刻から)。"""
        a = np.atleast_1d(np.asarray(a, dtype=np.int64))
        on = a[self._gaze[a] == GAZE_SCREEN]
        since = self._gaze_since[on]
        mins = ((int(t_ns) - since[since >= 0]) // (SECONDS_PER_MINUTE * NS_PER_SECOND)).tolist()
        if on.size:
            self.look_up(on, t_ns)
        return on, [int(x) for x in mins]

    def look_up(self, a: Any, t_ns: int) -> None:
        a = np.asarray(a, dtype=np.int64)
        self._gaze[a] = GAZE_FRONT
        self._gaze_since[a] = int(t_ns)

    # ------------------------------------------------------------------ 状態から(刻みごと)
    def sync(self, in_call: np.ndarray, in_talk: np.ndarray) -> None:
        """関心の的と視線(会話の相手)を今の状態から置き直す(通話 > 画面 > 会話 > 周り)。"""
        screen = self._gaze == GAZE_SCREEN
        f = np.full(self.n, FOCUS_SURROUND, dtype=np.int8)
        f[in_talk] = FOCUS_TALK
        f[screen] = FOCUS_SCREEN
        f[in_call] = FOCUS_CALL
        self._focus[:] = f
        g = self._gaze
        g[(~screen) & in_talk] = GAZE_PARTNER
        g[(~screen) & (~in_talk) & (g == GAZE_PARTNER)] = GAZE_FRONT

    def idle_onset(self, activity: np.ndarray) -> np.ndarray:
        """暇な活動に入った体(前の刻みは暇でない・今は暇)の番号を返し、前の活動を今に置き直す。"""
        act = np.asarray(activity, dtype=np.int64)
        idle = np.isin(act, tuple(IDLE_ACTIVITIES))
        prev_idle = np.isin(self._prev_act.astype(np.int64), tuple(IDLE_ACTIVITIES))
        onset = np.flatnonzero(idle & ~prev_idle & (self._prev_act >= 0)).astype(np.int64)
        self._prev_act[:] = act.astype(np.int8)
        return onset

    def summary(self) -> dict[str, Any]:
        return {"gaze": {GAZE_WORDS[k]: int(np.count_nonzero(self._gaze == k)) for k in range(len(GAZE_WORDS))},
                "focus": {FOCUS_WORDS[k]: int(np.count_nonzero(self._focus == k)) for k in range(len(FOCUS_WORDS))}}


def interrupted_of(wake_reason: Any) -> bool:
    """起きた理由が驚き駆動の入口(セルの B4 の変化)か。"""
    return (not isinstance(wake_reason, str)) and int(wake_reason) in INTERRUPT_CONDITIONS


def coarsen(p: Any, gaze: int, focus: int, *, unnoticed_arm: str, device_view: Any = None) -> Any:
    """知覚の事実 ``p`` を目と心の向きの形にした写し(``mind_dir``=:class:`AttentionView`・``tool_state``=道具の状態)。

    視線が画面: 見えた物を認識しない・見えた人は周辺視の範囲の中の数だけ(気配)。関心の的が周りでなく、驚き駆動の入口で起きて
    いない: B4 の顕著行為を「割り込めなかった出来事」とし、腕 (i)(ii) は描画の入力から落とす((ii) は隅の 1 行を描画が足す)・
    (iii) はそのまま載せる。確率は使わない(同じ入力から同じ写し)。
    """
    interrupted = interrupted_of(p.wake.reason)
    peripheral = int(gaze) == GAZE_SCREEN
    people, objects, signage = p.seen_people, p.seen_objects, bool(p.signage_shown)
    hint = 0
    if peripheral:
        hint = sum(1 for sp in people if float(sp.distance_m) <= PERIPHERAL_RANGE_M)  # 逐次: 見えた人の数ぶん
        people, objects, signage = (), (), False
    scene = p.scene
    unnoticed: tuple[str, ...] = ()
    filtered = False
    if int(focus) != FOCUS_SURROUND and not interrupted and scene.salient:
        unnoticed = tuple(scene.salient)
        if unnoticed_arm in ("i", "ii"):
            scene = dataclasses.replace(scene, salient=())
            filtered = True
    att = AttentionView(gaze=GAZE_WORDS[int(gaze)], focus=FOCUS_WORDS[int(focus)], interrupted=bool(interrupted),
                        peripheral=bool(peripheral), people_hint=int(hint), unnoticed=unnoticed,
                        unnoticed_arm=str(unnoticed_arm), scene_filtered=bool(filtered))
    return dataclasses.replace(p, seen_people=people, seen_objects=objects, signage_shown=signage, scene=scene,
                               mind_dir=att, tool_state=device_view)


def gate_salient(events: Any, focus: np.ndarray, interrupted: np.ndarray
                 ) -> tuple[list[np.ndarray], int, int, dict[str, int]]:
    """その刻みの顕著行為ごとの「気づいた体」から、関心の的が周りでなく割り込めなかった体を外した写しを返す(〔検収 M1〕
    顕著行為の過程のキャッシュは書き換えない=門の結果は連絡の持ち主の側に持つ)。

    Returns:
        (顕著行為ごとの門を通った体の配列・外した延べ・気づいた延べ(外す前)・関心の的ごとの外した延べ)。
    """
    blocked = reached = 0
    by: dict[str, int] = {w: 0 for w in FOCUS_WORDS}
    kept: list[np.ndarray] = []
    for ev in events:  # 逐次ループ宣言: その刻みの顕著行為の数ぶん
        got = np.asarray(getattr(ev, "noticed", ()), dtype=np.int64)
        if got.size == 0:
            kept.append(got.copy())
            continue
        reached += int(got.size)
        f = focus[got]
        keep = (f == FOCUS_SURROUND) | interrupted[got]
        if not bool(keep.all()):
            for k in np.unique(f[~keep]).tolist():  # 関心の的の種類ぶん(≤ 3)
                by[FOCUS_WORDS[int(k)]] += int(np.count_nonzero(f[~keep] == k))
            blocked += int(np.count_nonzero(~keep))
        kept.append(got[keep].copy())
    return kept, blocked, reached, by
