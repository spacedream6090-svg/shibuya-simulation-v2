"""engine.economy_rules — 第 4 期 4-2 の規則の表の中身を経済の段階 2 に挿す腕と、給与の天引きの加入の判定の材料。

正: 計画 10-12 第 4 期 4-2・§3 版上げ 3 回目(R-118 §7-1 の「4-3 に束ねる分」)・PENDING 仮-40(Q1〜Q7=親の判断・仮採用)。

腕(旧道の切替口): 環境変数 ``SHIBUYA_RULES_42`` {``on``,``off``}(:func:`set_arm`・既定 ``on``)。``on``=給料日に税と社会保険を
天引きし雇用主の分も払う・レジの消費税は店の預かり金に積んで申告の期限に政府へ移す(Q1)。``off``=4-2 の前の値の再現
(天引き 0・レジの税は売った時点で政府へ)=**次の版上げで消す**(回答 10-13b §0-6・つなぎの台帳 ``DOC-rules42-legacy-switch``)。
腕は組み立てのときに読む(``engine.economy_stage2.attach`` が :func:`payroll_inputs` の結果を ``Stage2Plan.law`` に渡す)。
状態のファイルとハッシュには、腕の行(状態台帳 ``TXD``=店の預かり消費税)が持ち主の居るランだけ入る=``off`` のランは
腕を足す前と同じバイト。

〔第 4 期 4-2b〕腕(旧道の切替口): 環境変数 ``SHIBUYA_RULES_42B`` {``on``,``off``}(:func:`set_arm_42b`・既定 ``on``)。
``on``=規則の表の空欄 3 件を埋めた値(R-118 §10-2=住民税の基礎控除・調整控除・非課税/厚年 70 歳・健保 75 歳の年齢の上限/
子ども・子育て拠出金 0.36%=事業主だけ)で天引きする。``off``=4-2 の値(f27377a)の再現=**次の版上げで消す**(つなぎの台帳
``DOC-rules42b-legacy-switch``)。``SHIBUYA_RULES_42=on`` のランだけに効く(off なら天引きそのものが無い)。組み立てで読み、
:class:`PayrollInputs` の ``rules_42b`` に載せる(経済の側は ``economy.taxes.payroll_tables`` の ``r42b`` で値を選ぶ)。

加入の判定の材料(:class:`PayrollInputs`=engine は economy を import できない=値だけ渡す):

- 役割と週の時間の目安: 差し替えの世界の初期の権利の表 ``w21_rights_initial.parquet`` の雇用の行(体 → 組織)の ``role``・
  ``weekly_hours_hint``(W21b)。体は母集団の ``w21_person_id`` で引く(行と体は 1 対 1=親の確かめ 147,065 行)。表の無い世界・
  W16 の残す体・外の雇用主の体は材料なし(役割 −1・時間 NaN)=判定の材料が無い体(宣言=未加入)。
- 雇用主の被保険者の数: 同じ表の組織ごとに、週の時間の目安が「通常の労働者の 4 分の 3」以上で役割が雇われる側の行の数
  (母集団の全体=縮小ランの抽出によらない)。短時間の加入(特定適用事業所=被保険者 51 人以上・R-118 §2-3)の判定に使う。
- 学生: 体の種別 ``STUDENT``(W16 の種別)だけ(W21 の通学の欄は住民の表だけにある=使っていない=宣言)。
- 年齢: 母集団の ``age``(介護保険 40〜64 歳・〔4-2b〕厚年 70 歳・健保 75 歳の上限と住民税の未成年者の非課税)。

逐次ループ宣言: なし(組み立てで 1 回・配列演算。役割の語の種類の数だけの Python ループ)。
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import numpy as np

__all__ = [
    "ARM_ON", "ARM_OFF", "ARMS", "DEFAULT_ARM", "arm", "set_arm", "RIGHTS_INITIAL_FILE", "PayrollInputs",
    "payroll_inputs", "FULL_TIME_WEEKLY_HOURS", "NON_EMPLOYEE_ROLES", "ENV_42B", "DEFAULT_ARM_42B", "arm_42b",
    "set_arm_42b",
]

ARM_ON: Final[str] = "on"
ARM_OFF: Final[str] = "off"
ARMS: Final[tuple[str, ...]] = (ARM_ON, ARM_OFF)
DEFAULT_ARM: Final[str] = ARM_ON
_ARM: str = os.environ.get("SHIBUYA_RULES_42", DEFAULT_ARM).strip().lower() or DEFAULT_ARM
if _ARM not in ARMS:
    raise ValueError(f"SHIBUYA_RULES_42 は {ARMS} のどれか(いま {_ARM!r})")
#: 〔第 4 期 4-2b〕空欄 3 件を埋めた値の腕の環境変数(旧道の切替口=次の版上げで消す)。
ENV_42B: Final[str] = "SHIBUYA_RULES_42B"
DEFAULT_ARM_42B: Final[str] = ARM_ON
_ARM_42B: str = os.environ.get(ENV_42B, DEFAULT_ARM_42B).strip().lower() or DEFAULT_ARM_42B
if _ARM_42B not in ARMS:
    raise ValueError(f"{ENV_42B} は {ARMS} のどれか(いま {_ARM_42B!r})")

#: 差し替えの世界の初期の権利の表(W21b・役割と週の時間の目安を持つ)。
RIGHTS_INITIAL_FILE: Final[str] = "w21_rights_initial.parquet"
#: 「通常の労働者」の週の所定労働時間の 4 分の 3[時](通常の労働者=週 40 時間=労基法 32 条の上限で代える=未リサーチ
#: (expedient)・つなぎの台帳 ``DOC-rules42-full-time-hours``)。雇用主の被保険者の数の数え方にだけ使う(体の判定は economy)。
FULL_TIME_WEEKLY_HOURS: Final[float] = 40.0 * 3.0 / 4.0
#: 雇われる側でない役割(W21b の語・業主=自営の本人・家族従業者・内職=自分で納める側=R-118 §2-6 の human)。
NON_EMPLOYEE_ROLES: Final[tuple[str, ...]] = ("業主", "家族従業者", "内職")


def arm() -> str:
    """いまの腕(``on``=既定・``off``=4-2 の前の値の再現)。組み立てのときに読む。"""
    return _ARM


def set_arm(name: str) -> None:
    """腕を選ぶ(試験と byte-check の切替口)。"""
    global _ARM
    if str(name) not in ARMS:
        raise ValueError(f"SHIBUYA_RULES_42 は {ARMS} のどれか(いま {name!r})")
    _ARM = str(name)


def arm_42b() -> str:
    """〔第 4 期 4-2b〕いまの腕(``on``=既定=空欄 3 件を埋めた値・``off``=4-2 の値の再現)。組み立てのときに読む。"""
    return _ARM_42B


def set_arm_42b(name: str) -> None:
    """〔第 4 期 4-2b〕腕を選ぶ(試験と byte-check の切替口)。"""
    global _ARM_42B
    if str(name) not in ARMS:
        raise ValueError(f"{ENV_42B} は {ARMS} のどれか(いま {name!r})")
    _ARM_42B = str(name)


@dataclass(frozen=True)
class PayrollInputs:
    """給与の天引きの加入の判定の材料(体ごと・読むだけ)。

    Attributes:
        role_code: 役割の語の番号(:attr:`role_vocab` の索引・−1=材料なし)。
        role_vocab: 役割の語(昇順)。
        weekly_hours: 週の時間の目安[時](NaN=材料なし)。
        employer_insured: 体の雇用主の被保険者の数(週の時間の目安が通常の労働者の 4 分の 3 以上の雇われる側の行の数・
            −1=材料なし)。
        student: 学生か(体の種別 STUDENT)。
        age: 年齢(−1=不明)。
        source: 材料の出どころ(``w21_rights_initial`` か ``absent``・``no_population``)。
        matched: 材料のある体の数(計器)。
        rules_42b: 〔第 4 期 4-2b〕空欄 3 件を埋めた値で天引きするか(組み立てのときの腕 ``SHIBUYA_RULES_42B``・
            直に作るときの既定は真=既定の腕と同じ)。
    """

    role_code: np.ndarray
    role_vocab: tuple[str, ...]
    weekly_hours: np.ndarray
    employer_insured: np.ndarray
    student: np.ndarray
    age: np.ndarray
    source: str
    matched: int = 0
    rules_42b: bool = True

    def __post_init__(self) -> None:
        for name in ("role_code", "weekly_hours", "employer_insured", "student", "age"):
            a = np.array(getattr(self, name), copy=True)
            a.setflags(write=False)
            object.__setattr__(self, name, a)
        object.__setattr__(self, "role_vocab", tuple(str(w) for w in self.role_vocab))

    @property
    def n(self) -> int:
        return int(self.role_code.size)

    def employee_like(self) -> np.ndarray:
        """雇われる側の役割か(材料なしは真=役割で外さない・時間の材料が無ければ社会保険は未加入)。"""
        bad = np.array([w in NON_EMPLOYEE_ROLES for w in self.role_vocab], dtype=bool)  # 逐次: 語の種類の数
        out = np.ones(self.n, dtype=bool)
        k = self.role_code >= 0
        if bad.size:
            out[k] = ~bad[self.role_code[k]]
        return out

    def record(self) -> dict[str, Any]:
        """manifest の ``economy.stage2.plan.law``(設定の節=材料の出どころ・語・定数だけ)。〔検収 H1〕抽出で動く数は
        :meth:`material_counts`(観測の ``economy.stage2.rules.payroll_inputs``)。"""
        return {"source": self.source, "role_vocab": list(self.role_vocab),
                "full_time_weekly_hours": float(FULL_TIME_WEEKLY_HOURS), "non_employee_roles": list(NON_EMPLOYEE_ROLES)}

    def material_counts(self) -> dict[str, int]:
        """〔検収 H1〕材料の数(母集団の抽出=seed で動く=観測)。"""
        return {"bodies": self.n, "matched": int(self.matched), "students": int(self.student.sum()),
                "hours_known": int(np.isfinite(self.weekly_hours).sum())}


def _empty(n: int, kinds: Any, age: Any, source: str) -> PayrollInputs:
    return PayrollInputs(role_code=np.full(n, -1, np.int16), role_vocab=(), weekly_hours=np.full(n, np.nan, np.float32),
                         employer_insured=np.full(n, -1, np.int32), student=_student(kinds, n), age=_age(age, n),
                         source=source, rules_42b=_ARM_42B == ARM_ON)


def _student(kinds: Any, n: int) -> np.ndarray:
    from shibuya.agents.state import AgentKind

    k = np.zeros(n, dtype=np.int64)
    src = np.asarray(kinds, dtype=np.int64).ravel()[:n]
    k[: src.size] = src
    return k == int(AgentKind.STUDENT)


def _age(age: Any, n: int) -> np.ndarray:
    out = np.full(n, -1, dtype=np.int16)
    if age is not None:
        a = np.asarray(age, dtype=np.int64).ravel()[:n]
        out[: a.size] = a
    return out


def payroll_inputs(pop: Any, world_dir: Any, n_agents: int, kinds: Any) -> PayrollInputs:
    """体ごとの加入の判定の材料を組み立てる(:class:`PayrollInputs`)。表の無い世界・母集団の無いランは材料なし。"""
    n = int(n_agents)
    if pop is None:
        return _empty(n, kinds, None, "no_population")
    m = min(n, int(pop.n))
    age = np.asarray(pop.age, dtype=np.int64)[:m]
    pid_all = getattr(pop, "w21_person_id", None)
    path = None if world_dir is None else Path(world_dir) / RIGHTS_INITIAL_FILE
    if pid_all is None or path is None or not path.exists():
        if pid_all is not None:
            from shibuya.engine.economy_stage2 import DataAbsentWarning

            warnings.warn(f"{RIGHTS_INITIAL_FILE} が無い写し: 給与の天引きの加入の判定の材料なし(社会保険は未加入)",
                          DataAbsentWarning, stacklevel=2)
        return _empty(n, kinds, age, "absent" if pid_all is not None else "no_w21")
    import pyarrow.parquet as pq  # 遅延 import

    t = pq.read_table(path, columns=["holder_kind", "holder_id", "object_kind", "object_id", "kind", "role",
                                     "weekly_hours_hint"])
    hk = np.asarray(t.column("holder_kind").to_pylist(), dtype=object)
    ok_ = np.asarray(t.column("object_kind").to_pylist(), dtype=object)
    kd = np.asarray(t.column("kind").to_pylist(), dtype=object)
    sel = (hk == "agent") & (ok_ == "org") & (kd == "employ")
    holder = np.asarray(t.column("holder_id").to_numpy(zero_copy_only=False), dtype=np.int64)[sel]
    org = np.asarray(t.column("object_id").to_numpy(zero_copy_only=False), dtype=np.int64)[sel]
    role = np.asarray(t.column("role").to_pylist(), dtype=object)[sel].astype(str)
    hours = np.asarray(t.column("weekly_hours_hint").to_numpy(zero_copy_only=False), dtype=np.float64)[sel]
    vocab = tuple(sorted({str(w) for w in role.tolist() if str(w)}))
    lut = {w: i for i, w in enumerate(vocab)}
    rcode = np.array([lut.get(str(w), -1) for w in role.tolist()], dtype=np.int16)  # 逐次: 行の数(組み立てで 1 回)
    bad = np.array([w in NON_EMPLOYEE_ROLES for w in vocab], dtype=bool)
    emp_like = np.ones(rcode.size, dtype=bool)
    k = rcode >= 0
    if bad.size:
        emp_like[k] = ~bad[rcode[k]]
    full = emp_like & np.isfinite(hours) & (hours >= FULL_TIME_WEEKLY_HOURS)
    insured = np.zeros(int(org.max()) + 1 if org.size else 0, dtype=np.int64)
    if org.size:
        np.add.at(insured, org[full], 1)
    # 体 → 行(人の番号で引く。1 人 1 行=親の確かめ。重なれば最初の行)
    order = np.argsort(holder, kind="stable")
    hs = holder[order]
    pid = np.asarray(pid_all, dtype=np.int64)[:m]
    pos = np.clip(np.searchsorted(hs, pid), 0, max(hs.size - 1, 0))
    hit = (pid >= 0) & (hs.size > 0) & (hs[pos] == pid) if hs.size else np.zeros(m, dtype=bool)
    row = np.where(hit, order[pos], -1)
    rc = np.full(n, -1, dtype=np.int16)
    wh = np.full(n, np.nan, dtype=np.float32)
    ei = np.full(n, -1, dtype=np.int32)
    got = np.flatnonzero(row >= 0)
    rc[got] = rcode[row[got]]
    wh[got] = hours[row[got]].astype(np.float32)
    o = org[row[got]]
    ei[got] = np.where(o < insured.size, insured[np.clip(o, 0, max(insured.size - 1, 0))], 0).astype(np.int32)
    return PayrollInputs(role_code=rc, role_vocab=vocab, weekly_hours=wh, employer_insured=ei,
                         student=_student(kinds, n), age=_age(age, n), source="w21_rights_initial",
                         matched=int(got.size), rules_42b=_ARM_42B == ARM_ON)
