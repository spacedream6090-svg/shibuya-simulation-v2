"""core.growth — 状態成長宣言(**正典 = D-R2-6**)と 24step→1日/30日 外挿の検査器。

正典
- 世界過程設計書 §6 **D-R2-6(決定・2026-09-07)**: 「状態成長宣言=YAML 5欄
  ``per_agent_bytes`` / ``per_cell_bytes`` / ``per_day_growth``(``O(1)|O(N)|O(N·t)+係数``)/
  ``retention``(**生ログ保持日数と圧縮先**)/ ``worst_case_ops_per_tick``(P4/P5接続)。
  **ActualLog は O(t) が本質→日次で集約行へ畳み・生ログは保持窓 N 日で退避を強制**。
  ゲート=24step スモークの実測を1日/30日へ外挿し予算書 M 行超で CI 失敗(宣言なき成長の禁止=
  P5 の状態版)。**O(N·t) 以上は宣言必須+「なぜ集約できないか」を記す**。」
- 予算宣言表 §7-6 / 実装計画書 §6: 「状態成長宣言(5欄・24step→30日外挿で M 行超は失敗)」。

**本モジュールの正典は D-R2-6 の 5 欄**(2026-09-08 訂正)。
    旧版(C2 第1弾)は ``{name, unit, bytes_per_unit, growth_per_simday, cap}`` を必須欄にし、
    D-R2-6 の 5 欄を任意欄に落としていた(同モジュールの docstring に「どちらを正典にするかは
    未決」と明記されていた)。**設計書が正典**なので必須/任意を入れ替えた:
      必須 = ``per_agent_bytes`` / ``per_cell_bytes`` / ``per_day_growth`` +
             ``per_day_growth_coef`` / ``retention`` / ``worst_case_ops_per_tick``
      加えて ``name``(同定)と ``cap``(**ゲートの閾値=予算表 M 行の値**)。
             cap は D-R2-6 の 5 欄ではないが、「M 行超で CI 失敗」というゲートの定義上
             M 行の値を宣言に持たせないと機械検査できないため必須のままにした。
      任意 = ``unit`` / ``bytes_per_unit`` / ``growth_per_simday``(旧必須欄。人が読む記録欄
             として残す。機械検査には使わない)。

``per_day_growth`` の意味論(**1 シミュ日あたりの増分**の位数)

    ==========  ===============================  ============================
    位数        その日の増分バイト                 D 日後の累積(宣言側)
    ==========  ===============================  ============================
    O(1)        coef                             coef × D
    O(t)        coef × t(t=経過日数)             coef × D(D+1)/2
    O(N)        coef × N                         coef × N × D
    O(N·t)      coef × N × t                     coef × N × D(D+1)/2
    ==========  ===============================  ============================

    ``N`` は ``check_growth(..., n_entities=…)`` に渡す規模(個体数など)。
    文字列に ``"O(N·t)+2.5"`` のように係数を書いた場合は ``per_day_growth_coef`` と
    一致していなければならない(二重記載の食い違いを検出する)。

逐次ループ宣言(P4): 宣言数(構造体の数=数十)ぶんのループのみ。個体数・tick 数に比例するループなし。

expedient(本モジュール分)
- **実測側**の外挿は線形(測定期間の増分を 1 シミュ日あたりへ割り戻し、実効日数倍する)。
  二乗爆発(runB 教訓)を検出するのが目的なので、線形外挿より速い成長は必ず超過側に出る
  ——ただし「30日で cap 未満だが 31 日目に爆発する」形は検出できない。**宣言側**は
  ``per_day_growth`` の位数どおりに外挿する(``O(N·t)`` は二次)ので、宣言と実測の食い違いは
  ``measured_over_declared`` に出る。
- ``retention.days`` があるときの実効期間 = ``min(horizon_days, retention.days)``
  (保持窓を超えた分は ``retention.target`` へ退避される、という D-R2-6 の運用を素直に写した)。
- ``O(t)``(規模に依存せず時間だけで伸びる)は D-R2-6 の列挙に無いが、tick 単位の診断行など
  実在する形なので**受理する**。受理を本書の expedient として登録。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final, Mapping

__all__ = [
    "MINUTES_PER_SIM_DAY",
    "DEFAULT_HORIZON_DAYS",
    "DEFAULT_SMOKE_STEPS",
    "GROWTH_ORDERS",
    "Retention",
    "GrowthDeclaration",
    "GrowthRow",
    "GrowthReport",
    "check_growth",
]

#: 1 シミュ日の分数(1分tick×1440)。
MINUTES_PER_SIM_DAY: int = 1_440
#: 外挿の地平(D-R2-6「30日」)。
DEFAULT_HORIZON_DAYS: int = 30
#: スモークの既定 step 数(D-R2-6「24step」)。
DEFAULT_SMOKE_STEPS: int = 24

#: ``per_day_growth`` に書ける位数(``O(t)`` は本モジュールの expedient な受理)。
GROWTH_ORDERS: Final[tuple[str, ...]] = ("O(1)", "O(t)", "O(N)", "O(N·t)")

_ORDER_RE = re.compile(
    r"^(?P<order>O\(1\)|O\(t\)|O\(N\)|O\(N·t\))(?:\s*\+\s*(?P<coef>[0-9]+(?:\.[0-9]+)?))?$"
)


@dataclass(frozen=True)
class Retention:
    """D-R2-6 の ``retention`` 欄 = **生ログ保持日数と圧縮先**。

    Attributes:
        days: 生ログの保持日数。``None`` = 無期限(=圧縮先を持たない構造体だけが許される)。
        target: 保持窓を超えた分の**圧縮先/退避先**(例 「日次集約行(daily_agg)」)。
            ``days`` が有限なら必須(空文字は「どこへ畳むか未定」=宣言として不完全)。
    """

    days: int | None
    target: str = ""

    def __post_init__(self) -> None:
        if self.days is not None and int(self.days) <= 0:
            raise ValueError(f"retention.days は正か None: {self.days!r}")
        if self.days is not None and not self.target:
            raise ValueError("D-R2-6: retention に保持日数があるなら圧縮先(target)も要る")

    def as_yaml(self) -> dict[str, Any]:
        return {"days": self.days, "target": self.target}

    def __str__(self) -> str:
        return "無期限" if self.days is None else f"{self.days}日→{self.target}"


@dataclass(frozen=True)
class GrowthDeclaration:
    """1つの成長する構造体の宣言(**D-R2-6 の 5 欄が必須**)。

    必須(D-R2-6 の 5 欄):
        per_agent_bytes: 個体1体あたりの定常バイト(成長しない分)。
        per_cell_bytes: セル1つあたりの定常バイト。
        per_day_growth: 1 シミュ日あたり増分の位数 ``"O(1)"`` / ``"O(t)"`` / ``"O(N)"`` /
            ``"O(N·t)"``(``"O(N·t)+2.5"`` のように係数を併記してもよい)。
        per_day_growth_coef: 上の係数(バイト。位数ごとの意味はモジュール docstring の表)。
        retention: ``Retention``(保持日数+圧縮先)。
        worst_case_ops_per_tick: tick あたり最悪演算数(P4/P5 接続)。

    必須(ゲートの同定と閾値・D-R2-6 の 5 欄ではない):
        name: 構造体名(例 ``"actual_log"``)。
        cap: この構造体が占めてよい総バイト数(**予算表 M 行の値**。超えたら CI 失敗)。

    任意:
        cap_budget_row: cap の根拠となる予算行 id(例 ``"S1"``・``"M8"``)。
        mechanism: True=mechanism / False=expedient(CLAUDE.md §4)。
        note: **O(N·t) なら「なぜ集約できないか」を必ず書く**(D-R2-6)。
        unit / bytes_per_unit / growth_per_simday: 人が読むための記録欄(旧必須欄)。
            機械検査には使わない。
    """

    name: str
    per_agent_bytes: int
    per_cell_bytes: int
    per_day_growth: str
    per_day_growth_coef: float
    retention: Retention
    worst_case_ops_per_tick: int
    cap: int
    cap_budget_row: str | None = None
    mechanism: bool = True
    note: str = ""
    unit: str = ""
    bytes_per_unit: int = 0
    growth_per_simday: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name は必須")
        for field_name in ("per_agent_bytes", "per_cell_bytes"):
            if int(getattr(self, field_name)) < 0:
                raise ValueError(f"{self.name}: {field_name} は 0 以上")
        m = _ORDER_RE.match(str(self.per_day_growth).strip())
        if m is None:
            raise ValueError(
                f"{self.name}: per_day_growth は {GROWTH_ORDERS} のいずれか"
                f"(係数併記可): {self.per_day_growth!r}"
            )
        if float(self.per_day_growth_coef) < 0:
            raise ValueError(f"{self.name}: per_day_growth_coef は 0 以上")
        inline = m.group("coef")
        if inline is not None and abs(float(inline) - float(self.per_day_growth_coef)) > 1e-9:
            raise ValueError(
                f"{self.name}: per_day_growth の併記係数 {inline} と "
                f"per_day_growth_coef {self.per_day_growth_coef} が食い違う"
            )
        if not isinstance(self.retention, Retention):
            raise TypeError(f"{self.name}: retention は Retention(days, target)")
        if int(self.worst_case_ops_per_tick) < 0:
            raise ValueError(f"{self.name}: worst_case_ops_per_tick は 0 以上")
        if int(self.cap) <= 0:
            raise ValueError(f"{self.name}: cap は正(予算 M 行由来)")
        if m.group("order") == "O(N·t)" and not self.note:
            raise ValueError(
                f"{self.name}: D-R2-6「O(N·t) 以上は宣言必須+なぜ集約できないかを記す」→ note が空"
            )
        if int(self.bytes_per_unit) < 0 or float(self.growth_per_simday) < 0:
            raise ValueError(f"{self.name}: 記録欄 bytes_per_unit / growth_per_simday は 0 以上")

    # ---- 位数 ----
    @property
    def order(self) -> str:
        """``per_day_growth`` の位数だけ(係数併記を落とした形)。"""
        m = _ORDER_RE.match(str(self.per_day_growth).strip())
        assert m is not None  # __post_init__ で検査済み
        return m.group("order")

    def declared_bytes_on_day(self, day: int, n_entities: int = 1) -> float:
        """宣言から計算した **day 日目(1 始まり)の増分バイト**。"""
        if day <= 0:
            raise ValueError("day は 1 以上")
        coef = float(self.per_day_growth_coef)
        order = self.order
        if order == "O(1)":
            return coef
        if order == "O(t)":
            return coef * float(day)
        if order == "O(N)":
            return coef * float(n_entities)
        return coef * float(n_entities) * float(day)  # O(N·t)

    def declared_bytes_per_simday(self, n_entities: int = 1) -> float:
        """宣言の「1日目の増分」(実測 B/日 と直接比べる基準値)。"""
        return self.declared_bytes_on_day(1, n_entities)

    def declared_projected_bytes(
        self, horizon_days: int = DEFAULT_HORIZON_DAYS, n_entities: int = 1
    ) -> float:
        """宣言どおりに伸びたときの累積バイト(保持窓を考慮・位数どおりに外挿)。

        ``O(N·t)`` は**二次**で伸びる(``coef·N·D(D+1)/2``)。実測側の線形外挿と違い、
        宣言側は位数を尊重する=「宣言したなら二乗爆発ぶんの cap を確保しているはず」。
        """
        days = int(self.effective_days(horizon_days))
        if days <= 0:
            return 0.0
        coef = float(self.per_day_growth_coef)
        order = self.order
        if order == "O(1)":
            return coef * days
        if order == "O(t)":
            return coef * days * (days + 1) / 2.0
        if order == "O(N)":
            return coef * float(n_entities) * days
        return coef * float(n_entities) * days * (days + 1) / 2.0

    def steady_bytes(self, n_agents: int = 0, n_cells: int = 0) -> int:
        """成長しない定常バイト(``per_agent_bytes×N + per_cell_bytes×C``)。"""
        return int(self.per_agent_bytes) * int(n_agents) + int(self.per_cell_bytes) * int(n_cells)

    def effective_days(self, horizon_days: int = DEFAULT_HORIZON_DAYS) -> float:
        """保持窓を考慮した実効期間(日)。"""
        if self.retention.days is None:
            return float(horizon_days)
        return float(min(horizon_days, int(self.retention.days)))

    def to_yaml_row(self) -> dict[str, Any]:
        """D-R2-6 の YAML 5 欄 + 同定/閾値/記録欄の辞書表現。"""
        return {
            "name": self.name,
            # --- D-R2-6 の 5 欄 ---
            "per_agent_bytes": int(self.per_agent_bytes),
            "per_cell_bytes": int(self.per_cell_bytes),
            "per_day_growth": self.per_day_growth,
            "per_day_growth_coef": float(self.per_day_growth_coef),
            "retention": self.retention.as_yaml(),
            "worst_case_ops_per_tick": int(self.worst_case_ops_per_tick),
            # --- ゲート ---
            "cap": int(self.cap),
            "cap_budget_row": self.cap_budget_row,
            "tag": "mechanism" if self.mechanism else "expedient",
            "note": self.note,
            # --- 記録欄(機械検査は使わない) ---
            "unit": self.unit,
            "bytes_per_unit": int(self.bytes_per_unit),
            "growth_per_simday": float(self.growth_per_simday),
        }


@dataclass(frozen=True)
class GrowthRow:
    """``check_growth`` の 1 構造体分の結果。"""

    name: str
    measured_bytes: int
    sim_days_measured: float
    measured_bytes_per_simday: float
    declared_bytes_per_simday: float
    effective_days: float
    projected_bytes: float
    declared_projected_bytes: float
    cap: int
    within_cap: bool
    #: 実測/宣言 の比(宣言が 0 のときは None)。1 を大きく超える=宣言が甘い。
    measured_over_declared: float | None

    @property
    def headroom_bytes(self) -> float:
        return float(self.cap) - self.projected_bytes


@dataclass(frozen=True)
class GrowthReport:
    """``check_growth`` の報告(CI ゲート用)。"""

    steps: int
    minutes_per_step: int
    horizon_days: int
    sim_days_measured: float
    n_entities: int
    rows: tuple[GrowthRow, ...]
    missing: tuple[str, ...] = ()
    unknown: tuple[str, ...] = ()
    over_cap: tuple[str, ...] = ()
    #: 実測が宣言を ``declared_tolerance`` 倍超えた構造体(宣言の改訂が必要=黙って超えない)。
    over_declared: tuple[str, ...] = ()
    #: 宣言そのものが cap を食い破っている構造体(実測を待たずに設計が破綻している)。
    declared_over_cap: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not (self.missing or self.unknown or self.over_cap or self.declared_over_cap)

    def as_text(self) -> str:
        head = (
            f"状態成長宣言(D-R2-6)の検査: steps={self.steps}×{self.minutes_per_step}分 "
            f"= {self.sim_days_measured:.4f} シミュ日 → {self.horizon_days} 日外挿 "
            f"(N={self.n_entities}) ({'OK' if self.ok else 'NG'})"
        )
        lines = [head]
        for r in self.rows:
            lines.append(
                f"  {r.name:20s} 実測 {r.measured_bytes:12,d}B "
                f"→ {r.measured_bytes_per_simday:14,.0f}B/日 "
                f"→ {r.effective_days:.0f}日 {r.projected_bytes:16,.0f}B "
                f"/ cap {r.cap:16,d}B {'OK' if r.within_cap else 'NG'}"
            )
        if self.missing:
            lines.append(f"  未測定(失敗): {list(self.missing)}")
        if self.unknown:
            lines.append(f"  未宣言の構造体(失敗): {list(self.unknown)}")
        if self.declared_over_cap:
            lines.append(f"  宣言だけで cap 超過(失敗): {list(self.declared_over_cap)}")
        if self.over_declared:
            lines.append(f"  宣言超過(要 delta 改訂): {list(self.over_declared)}")
        return "\n".join(lines)


def check_growth(
    declarations: Mapping[str, GrowthDeclaration] | tuple[GrowthDeclaration, ...],
    measured_after_steps: Mapping[str, int],
    steps: int = DEFAULT_SMOKE_STEPS,
    minutes_per_step: int = 1,
    *,
    horizon_days: int = DEFAULT_HORIZON_DAYS,
    declared_tolerance: float = 1.0,
    n_entities: int = 1,
) -> GrowthReport:
    """24step スモークの実測バイトを 1 日・``horizon_days`` 日へ外挿し cap と突き合わせる。

    Args:
        declarations: 構造体名 → 宣言(タプルでも可)。
        measured_after_steps: 構造体名 → ``steps`` step 後の**増分バイト**(初期状態を除いた成長分)。
        steps: スモークの step 数(既定 24)。
        minutes_per_step: 1 step の分数(1分tick なら 1)。
        horizon_days: 外挿の地平(既定 30 日)。
        declared_tolerance: 実測/宣言 がこの倍率を超えたら ``over_declared`` に載せる
            (失敗にはしない=宣言の delta 改訂を促す)。
        n_entities: ``O(N)``/``O(N·t)`` の N(個体数など)。

    Returns:
        ``GrowthReport``。``ok`` が False なら CI 失敗にする(D-R2-6)。

    Raises:
        ValueError: steps / minutes_per_step / n_entities が非正・実測バイトが負。
    """
    if steps <= 0 or minutes_per_step <= 0:
        raise ValueError("steps・minutes_per_step は正の整数")
    if n_entities <= 0:
        raise ValueError("n_entities は正の整数")
    decls: dict[str, GrowthDeclaration]
    if isinstance(declarations, Mapping):
        decls = dict(declarations)
    else:
        decls = {d.name: d for d in declarations}

    sim_days = (steps * minutes_per_step) / MINUTES_PER_SIM_DAY
    rows: list[GrowthRow] = []
    over_cap: list[str] = []
    over_declared: list[str] = []
    declared_over_cap: list[str] = []

    # 逐次ループ宣言(P4): 宣言数(数十)ぶん。個体数・tick 数には比例しない。
    for name, decl in decls.items():
        declared_proj = decl.declared_projected_bytes(horizon_days, n_entities)
        if declared_proj > float(decl.cap):
            declared_over_cap.append(name)
        if name not in measured_after_steps:
            continue
        measured = int(measured_after_steps[name])
        if measured < 0:
            raise ValueError(f"{name}: 実測バイトが負({measured})")
        per_day = measured / sim_days
        eff_days = decl.effective_days(horizon_days)
        projected = per_day * eff_days
        within = projected <= float(decl.cap)
        declared_per_day = decl.declared_bytes_per_simday(n_entities)
        ratio = (per_day / declared_per_day) if declared_per_day > 0 else None
        rows.append(
            GrowthRow(
                name=name,
                measured_bytes=measured,
                sim_days_measured=sim_days,
                measured_bytes_per_simday=per_day,
                declared_bytes_per_simday=declared_per_day,
                effective_days=eff_days,
                projected_bytes=projected,
                declared_projected_bytes=declared_proj,
                cap=decl.cap,
                within_cap=within,
                measured_over_declared=ratio,
            )
        )
        if not within:
            over_cap.append(name)
        if ratio is not None and ratio > declared_tolerance:
            over_declared.append(name)

    missing = tuple(sorted(set(decls) - set(measured_after_steps)))
    unknown = tuple(sorted(set(measured_after_steps) - set(decls)))
    return GrowthReport(
        steps=steps,
        minutes_per_step=minutes_per_step,
        horizon_days=horizon_days,
        sim_days_measured=sim_days,
        n_entities=int(n_entities),
        rows=tuple(rows),
        missing=missing,
        unknown=unknown,
        over_cap=tuple(over_cap),
        over_declared=tuple(over_declared),
        declared_over_cap=tuple(declared_over_cap),
    )
