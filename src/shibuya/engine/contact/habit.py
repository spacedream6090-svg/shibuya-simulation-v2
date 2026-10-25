"""engine.contact.habit — CT4 の習慣(本人の過去の連絡の判断から作る・第 6 期 6-4 C2・腕 ``SHIBUYA_CONTACT_HABIT``)。

正: 決定 10-12 §4-4 CT4「『読む・いつ返す・返すか無視か』は、その人自身の過去の判断から作った習慣で決めてかまいません(10-03 §7-3
の繰り返しの自動化)。記録が少ないうち・大事な誘い・驚きのときは判断モデルに戻します。文は LLM です。習慣は状態(勤務中・家・
移動中)ごとに分けます。癖の強まりは計器で見て、ときどき判断モデルへ戻します」・10-03 §7-3 4-1 (a)(同じ状況で同じ行動を繰り返す
ほど決定モデルが LLM を呼ばずに選ぶ)。〔親の判断 2026-10-23=問い 2〕習慣で答えるのは**範囲の外に居る体だけ**(CT4 の見出し
=範囲の外にいる人・``engine.contact.layer._habit_or_decide``)。範囲の中の体はいつも判断の口(選びは数える)。

持ち主 :class:`HabitBook`(状態台帳の腕の行 ``CT1H``=軸 1 behavior・軸 2 required・道筋 ``contact.habit``): 体 → 状態 × 判断 ×
選んだ語の回数(``_counts``・体ごとに 24 個の整数の列=状態 4 × 判断 2 × 語 3)。**素は本人の選び**(判断の口で選んだ語と、習慣で
答えた語=繰り返すほど強まる=計器で見る)。出来事の記録(``連絡:読んだ/後で/無視``・返事の ``連絡:送った``)と同じ時に層が数える
=記録の有無で表が変わらない(口の約束 1-3 の (1))。腕 off のランは何も数えない(記録の無い体は習慣が無い)。

- 状態(:data:`STATE_WORDS`): 勤務中=勤め先のセルに居る(範囲の中)・家=住まいのセルに居る(範囲の外の住まいの体は範囲の外で
  居る刻み=充電と同じ当てはめ=親の判断 2026-10-23)・移動中=移動・乗車・待機の活動か出入りの途中・ほか=それ以外(状態は本人の今の活動と場所から=
  宣言)。並びは「移動中 → 家 → 勤務中 → ほか」の順に当てる。範囲の外に居る体(出入りの状態 2)の活動は範囲の外では「待機」のまま
  =移動中に数えない(家と見なす刻みでなければ「ほか」)。
- 判断(:data:`HABIT_KINDS`): 気づいた通知(今読む/後で/無視)と読んだ後(返す/スタンプを送る/返さない)。
- 習慣の答え(:meth:`HabitBook.answer`)=その体のその状態のその判断の記録が ``HABIT_MIN_RECORDS`` 以上のとき、いちばん多く選んだ
  語(同じ回数なら語の並びの先)。それ未満は ``None``(判断の口へ)。大事な誘い・驚き・ときどき(``HABIT_RECHECK_SHARE``・
  乱数の用途名 ``contact.habit``)に戻すのは呼び手(``engine.contact.layer``)。

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ct-c2-habit``): 閾値 ``HABIT_MIN_RECORDS``=5・戻す割合 ``HABIT_RECHECK_SHARE``=0.1・
状態の分け方(4 つ・当てる順)・答え=いちばん多い語(確率で引かない)・習慣で答えた語も記録に数える(強まる形)。

逐次ループ宣言: なし(1 体 1 回の読み書き)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

from shibuya.agents.state import Activity
from shibuya.engine.contact.arm import LEDGER_ARM

__all__ = [
    "STATE_WORK", "STATE_HOME", "STATE_MOVING", "STATE_OTHER", "STATE_WORDS", "HABIT_KINDS", "HABIT_MIN_RECORDS",
    "HABIT_RECHECK_SHARE", "MOVING_ACTIVITIES", "HabitBook", "states_of", "PROVISIONAL_VALUES",
]

STATE_WORK, STATE_HOME, STATE_MOVING, STATE_OTHER = 0, 1, 2, 3
STATE_WORDS: Final[tuple[str, ...]] = ("勤務中", "家", "移動中", "ほか")
#: 判断の種類の名 → 語の並び(``engine.contact.port`` の候補の語と同じ文字列)。
HABIT_KINDS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "notice": ("今読む", "後で", "無視"),
    "reply": ("返す", "スタンプを送る", "返さない"),
})
_KIND_NAMES: Final[tuple[str, ...]] = tuple(HABIT_KINDS)
_N_CHOICES: Final[int] = 3
_ROW: Final[int] = len(STATE_WORDS) * len(_KIND_NAMES) * _N_CHOICES
#: 習慣で答えるのに要る記録の数(その体のその状態のその判断の選びの数)。
HABIT_MIN_RECORDS: Final[int] = 5
#: 習慣で答えられるときも判断の口へ戻す割合(癖の強まりを見る=ときどき戻す)。
HABIT_RECHECK_SHARE: Final[float] = 0.1
#: 移動中と数える活動(移動・乗車・待機)。
MOVING_ACTIVITIES: Final[frozenset[int]] = frozenset({int(Activity.MOVING), int(Activity.RIDING), int(Activity.WAITING)})

PROVISIONAL_VALUES: Final[tuple[str, ...]] = (
    "習慣の閾値 5 回・ときどき戻す割合 0.1・答え=いちばん多く選んだ語・習慣で答えた語も数える",
    "状態=移動中(範囲の中の移動・乗車・待機・出入りの途中)→ 家(住まいのセル)→ 勤務中(勤め先のセル)→ ほか の順に当てる",
)


def states_of(activity: Any, cells: Any, transit: Any, at_home: Any, work_cell: Any) -> np.ndarray:
    """体ごとの状態(勤務中・家・移動中・ほか)。``work_cell`` が ``None`` なら勤務中は無い。"""
    act = np.asarray(activity, dtype=np.int64)
    cells = np.asarray(cells, dtype=np.int64)
    tr = np.asarray(transit, dtype=np.int64)
    out = np.full(act.shape[0], STATE_OTHER, dtype=np.int8)
    if work_cell is not None:
        wc = np.asarray(work_cell, dtype=np.int64)[: act.shape[0]]
        out[(wc >= 0) & (cells == wc) & (tr == 0)] = STATE_WORK
    out[np.asarray(at_home, dtype=bool)] = STATE_HOME
    # 範囲の中の移動・乗車・待機か出入りの途中(範囲の外の体の活動は「待機」のまま=移動中に数えない=5,000 体の世界で確かめた)
    out[(np.isin(act, tuple(MOVING_ACTIVITIES)) & (tr == 0)) | (tr == 1)] = STATE_MOVING
    return out


def _slot(state: int, kind: str, choice: int) -> int:
    return (int(state) * len(_KIND_NAMES) + _KIND_NAMES.index(kind)) * _N_CHOICES + int(choice)


class HabitBook:
    """体ごとの連絡の選びの回数(状態台帳の腕の行 ``CT1H``・持ち主の道筋 ``contact.habit``)。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

    def __init__(self) -> None:
        self._counts: dict[int, list[int]] = {}

    def records(self, agent: int, state: int, kind: str) -> int:
        row = self._counts.get(int(agent))
        if row is None:
            return 0
        s = _slot(state, kind, 0)
        return int(sum(row[s:s + _N_CHOICES]))

    def note(self, agent: int, state: int, kind: str, word: str) -> None:
        """本人の選び 1 回を数える(判断の口で選んだ語・習慣で答えた語)。"""
        words = HABIT_KINDS[kind]
        if word not in words:
            return
        row = self._counts.setdefault(int(agent), [0] * _ROW)
        row[_slot(state, kind, words.index(word))] += 1

    def answer(self, agent: int, state: int, kind: str) -> str | None:
        """習慣の答え(記録が閾値以上のときいちばん多く選んだ語・同じ回数なら並びの先)。それ未満は ``None``。"""
        if self.records(agent, state, kind) < HABIT_MIN_RECORDS:
            return None
        row = self._counts[int(agent)]
        s = _slot(state, kind, 0)
        seg = row[s:s + _N_CHOICES]
        return HABIT_KINDS[kind][int(np.argmax(np.asarray(seg)))]

    def tally(self) -> dict[str, Any]:
        """計器: 習慣の表のある体の数・状態と判断ごとの記録の延べと、閾値以上の体の数・語ごとの延べ。"""
        out: dict[str, Any] = {"agents": len(self._counts)}
        for st, sw in enumerate(STATE_WORDS):  # 状態の数ぶん(4)
            for kind, words in HABIT_KINDS.items():  # 判断の数ぶん(2)
                s = _slot(st, kind, 0)
                rec = [sum(r[s:s + _N_CHOICES]) for r in self._counts.values()]
                if not any(rec):
                    continue
                out[f"{sw}:{kind}"] = {
                    "records": int(sum(rec)), "agents_over_min": int(sum(1 for x in rec if x >= HABIT_MIN_RECORDS)),
                    "by_word": {w: int(sum(r[s + i] for r in self._counts.values())) for i, w in enumerate(words)},
                }
        return out
