"""build.sched.pool_facts — ペルソナプールの「生活の素材」欄だけを引く読み取り器。

なぜ ``build.pop.pool`` を使わないか
    ``build.pop.pool.read_layer`` は W16 が要る欄(年齢・性別・産業など)だけを列化する。
    W17 のプロンプトに載せたいのは ``occupation`` / ``shift_pattern`` / ``work_days`` /
    ``visit_cadence`` / ``duty_pattern`` / ``bedtime_min`` / ``sleep_steps`` のような
    **生活時間の素材**で、そのうち多くは ``pool.py`` の ``_STR_FIELDS`` に無い(``shift_pattern``
    と ``duty_pattern`` は dict なので列化されていない)。``build.pop`` は本工程の編集対象外
    なので、**W17 側に必要な欄だけを読む口を置く**(pool.py と同じ行順=``pool_index``)。

メモリ
    プールは 100 万行(L4 だけで 79 万)。W17 が要るのは W16 が実際に参照した
    ``(pool_layer, pool_index)`` の分だけ(39 万)なので、**必要な行だけ ``json.loads`` する**
    (行番号は数えるだけで飛ばす)。実測: 全層で数秒・RSS は 100 MB 級。

逐次ループ宣言(P4): プール行数ぶんのループ 1 本(構築時 1 回・I1 の外)。

expedient(本モジュール分・登録簿へ)
- ``sleep_steps`` の単位を **1 step = 10 分**と読む(v1 プールに単位の記載がない。
  中央値 42 step = 7.0 h が NHK 国民生活時間調査の睡眠時間と整合するので採る)。
- ``work_days`` / ``duty_pattern.days`` の文字列 → 曜日ビットマスクの解釈表。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Sequence

import numpy as np

__all__ = [
    "LAYERS",
    "SLEEP_STEP_MINUTES",
    "ALL_DAYS_MASK",
    "WEEKDAY_MASK",
    "WEEKEND_MASK",
    "parse_days",
    "parse_hhmm",
    "PoolFacts",
    "read_facts",
    "layer_files",
]

#: 層名(``build.pop.pool.LAYERS`` と同じ・二重定義)。
LAYERS: Final[tuple[str, ...]] = ("L1", "L2", "L3", "L4", "L5")

#: ``sleep_steps`` 1 step の分(expedient)。
SLEEP_STEP_MINUTES: Final[int] = 10

ALL_DAYS_MASK: Final[int] = 0b1111111
WEEKDAY_MASK: Final[int] = 0b0011111  # d0..d4 = 月..金
WEEKEND_MASK: Final[int] = 0b1100000  # d5,d6 = 土日

_DAY_TOKENS: Final[dict[str, int]] = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
    "月": 0, "火": 1, "水": 2, "木": 3, "金": 4, "土": 5, "日": 6,
}

#: 引く文字列欄(そのまま保持)。
_STR_FIELDS: Final[tuple[str, ...]] = (
    "occupation", "work_days", "visit_cadence", "visit_purpose", "school_stage",
    "commute_mode", "role", "post", "residence_line", "subtype",
)


def parse_days(spec: object) -> int:
    """``"mon-fri"`` / ``"all"`` / ``"sat,sun"`` → 曜日ビットマスク(bit d = 曜日 d)。

    読めない綴りは ``0``(=不明)を返す。呼び出し側が種別ごとの既定で埋める。

    Example:
        >>> parse_days("mon-fri") == WEEKDAY_MASK
        True
        >>> parse_days("all") == ALL_DAYS_MASK
        True
        >>> parse_days("weekday") == WEEKDAY_MASK
        True
        >>> parse_days(None)
        0
    """
    if spec is None:
        return 0
    s = str(spec).strip().lower()
    if not s:
        return 0
    if s in ("all", "everyday", "daily", "毎日"):
        return ALL_DAYS_MASK
    if s in ("weekday", "weekdays", "平日"):
        return WEEKDAY_MASK
    if s in ("weekend", "weekends", "土日"):
        return WEEKEND_MASK
    mask = 0
    for part in s.replace("・", ",").replace("／", ",").replace("/", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            i, j = _DAY_TOKENS.get(a.strip()), _DAY_TOKENS.get(b.strip())
            if i is None or j is None:
                continue
            d = i
            while True:  # 逐次: 最大 7 回
                mask |= 1 << d
                if d == j:
                    break
                d = (d + 1) % 7
        else:
            i = _DAY_TOKENS.get(part)
            if i is not None:
                mask |= 1 << i
    return mask


def parse_hhmm(spec: object) -> int:
    """``"09:00"`` / ``"0900"`` → 分。読めなければ ``-1``。

    Example:
        >>> parse_hhmm("09:00"), parse_hhmm("2230"), parse_hhmm(None)
        (540, 1350, -1)
    """
    if spec is None:
        return -1
    s = str(spec).strip()
    if ":" in s:
        a, _, b = s.partition(":")
    elif len(s) == 4 and s.isdigit():
        a, b = s[:2], s[2:]
    else:
        return -1
    try:
        h, m = int(a), int(b)
    except ValueError:
        return -1
    if not (0 <= h <= 24 and 0 <= m < 60):
        return -1
    return h * 60 + m


@dataclass(frozen=True)
class PoolFacts:
    """要求した ``(layer, index)`` の並びに対応する素材(行順=要求順)。

    Attributes:
        n: 行数。
        text: 文字列欄の辞書(欄名 → 長さ n の list[str]。欠測は ``""``)。
        shift_open / shift_close: ``shift_pattern`` の分(不明 −1)。
        work_days: 曜日ビットマスク(不明 0)。
        duty_hours: ``duty_pattern.shift_hours``(不明 −1)。
        duty_days: ``duty_pattern.days`` のビットマスク(不明 0)。
        duty_rotates: 交代制か。
        bedtime_min: 就寝時刻[分](不明 −1)。
        sleep_min: 睡眠長[分](``sleep_steps`` × 10。不明 −1)。
        found: その行の素材が実際に読めたか(``pool_index<0`` などは False)。
    """

    n: int
    text: dict[str, list[str]]
    shift_open: np.ndarray
    shift_close: np.ndarray
    work_days: np.ndarray
    duty_hours: np.ndarray
    duty_days: np.ndarray
    duty_rotates: np.ndarray
    bedtime_min: np.ndarray
    sleep_min: np.ndarray
    found: np.ndarray

    def col(self, field: str) -> list[str]:
        return self.text[field]


def layer_files(root: Path, name: str) -> list[Path]:
    """層の part ファイル(名前順=``pool_index`` の順・``build.pop.pool`` と同規約)。"""
    return sorted((Path(root) / name).glob("part-*.jsonl"))


def _blank(n: int) -> PoolFacts:
    return PoolFacts(
        n=n,
        text={f: [""] * n for f in _STR_FIELDS},
        shift_open=np.full(n, -1, dtype=np.int16),
        shift_close=np.full(n, -1, dtype=np.int16),
        work_days=np.zeros(n, dtype=np.uint8),
        duty_hours=np.full(n, -1, dtype=np.int8),
        duty_days=np.zeros(n, dtype=np.uint8),
        duty_rotates=np.zeros(n, dtype=bool),
        bedtime_min=np.full(n, -1, dtype=np.int16),
        sleep_min=np.full(n, -1, dtype=np.int16),
        found=np.zeros(n, dtype=bool),
    )


def _fill(facts: PoolFacts, row: int, d: dict) -> None:
    for f in _STR_FIELDS:
        v = d.get(f)
        facts.text[f][row] = "" if v is None else str(v)
    shift = d.get("shift_pattern")
    if isinstance(shift, dict):
        facts.shift_open[row] = parse_hhmm(shift.get("open"))
        facts.shift_close[row] = parse_hhmm(shift.get("close"))
        facts.work_days[row] = parse_days(shift.get("days"))
    if not facts.work_days[row]:
        facts.work_days[row] = parse_days(d.get("work_days"))
    duty = d.get("duty_pattern")
    if isinstance(duty, dict):
        try:
            facts.duty_hours[row] = max(-1, min(24, int(duty.get("shift_hours") or -1)))
        except (TypeError, ValueError):
            facts.duty_hours[row] = -1
        facts.duty_days[row] = parse_days(duty.get("days"))
        facts.duty_rotates[row] = bool(duty.get("rotates"))
    bed = d.get("bedtime_min")
    if isinstance(bed, (int, float)):
        facts.bedtime_min[row] = int(bed) % 1440
    steps = d.get("sleep_steps")
    if isinstance(steps, (int, float)):
        facts.sleep_min[row] = min(1439, int(steps) * SLEEP_STEP_MINUTES)
    facts.found[row] = True


def read_facts(
    pool_root: str | Path,
    pool_layer: Sequence[int] | np.ndarray,
    pool_index: Sequence[int] | np.ndarray,
) -> PoolFacts:
    """``(pool_layer, pool_index)`` の並びに対応する素材を読む。

    Args:
        pool_root: ``data/persona_pool_v2``。
        pool_layer: 層番号(1..5=L1..L5・0 以下=素材なし)。W16 の ``pool_layer`` 列。
        pool_index: 層内の行番号(W16 の ``pool_index`` 列・負は素材なし)。

    Returns:
        ``PoolFacts``(行順=引数の並び)。

    Note:
        逐次ループ宣言(P4): プール行数ぶんのループ 1 本(必要行だけ ``json.loads``)。
    """
    root = Path(pool_root)
    layer = np.asarray(pool_layer, dtype=np.int64)
    index = np.asarray(pool_index, dtype=np.int64)
    if layer.shape != index.shape:
        raise ValueError("pool_layer と pool_index は同じ長さ")
    facts = _blank(int(layer.size))

    for lno, name in enumerate(LAYERS, start=1):
        want = np.flatnonzero((layer == lno) & (index >= 0))
        if want.size == 0:
            continue
        # 層内行番号 → 出力行(同じ素材を複数体が参照する=追加生成分があるので list)
        order = np.argsort(index[want], kind="stable")
        want = want[order]
        wanted_idx = index[want]
        cursor = 0  # wanted_idx の走査位置
        row_no = 0  # 層内の行番号
        for path in layer_files(root, name):
            if cursor >= wanted_idx.size:
                break
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    if cursor < wanted_idx.size and row_no == wanted_idx[cursor]:
                        d = json.loads(line)
                        while cursor < wanted_idx.size and wanted_idx[cursor] == row_no:
                            _fill(facts, int(want[cursor]), d)
                            cursor += 1
                    row_no += 1
                    if cursor >= wanted_idx.size:
                        break
    return facts
