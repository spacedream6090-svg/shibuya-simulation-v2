# -*- coding: utf-8 -*-
"""c8lib — C8(ablation・感度・計器盤)の純関数と共通部品。

位置づけ
    ``tools/c8/*.py`` の 4 本(ablation_runner・sensitivity・dashboard・ensemble)が共有する
    「計算の部分」だけを集めた。**実サーバー接続も乱数の副作用も置かない**。
    数値ユーティリティ(JSD・ブートストラップ・表・出力)は ``tools/c6/c6lib`` を再利用し、
    受入表の読み取りは ``tools/c7/c7lib`` を再利用する(新規依存を作らない)。
    ``tests/c8`` がこのモジュールをモック入力・小データで検査する。

正典(数値・規則の出どころ)
- 知覚契約書 **§8**「ablation の優先順位規則(決定 09-06)= expedient の量 × 結果を駆動する
  先験的可能性 ÷ コスト の降順。**第1陣(Phase 2・L2=総 GPU 時間 20% の枠内)=6 本**」
  ①チャネル固定枠 vs 同一総トークンの単一ランキング(義務) ②p_notice の d50 0.5×/2×
  ③近接入替の不応期 15 分±50% ④聴覚 ΔSNR −3/−5 ⑤日次内省 1.05 回/日 vs 2-3 回/日
  ⑥広告ゼロ。
- 方法論「②cap が世界の法則化 → 全 cap に ``mechanism|expedient`` タグ。**expedient は
  感度試験 id 必須(振って結果非依存を示す)。示せなければ限界として明記**」・
  「Phase 4 validation+ablation(スケールアップ前=安いうちに)…ablation マトリクスは完了条件」。
- 予算宣言表 **L2**「ablation・感度試験の取り分=総 GPU 時間の 20% を予約(他用途への流用禁止)」。
- 計器盤設計書(R14)**G-1**(3面・ゲートは面2のみ)・**G-2**(実行不能度 I≤3)・
  **G-3**(TRACE 8 要素 → 工程別受入基準)・**G-4**(EnsembleSpec/SweepSpec)・
  **G-5**(``seed = blake3(manifest_sha256 ‖ run_index)``)・**G-6**(完了済みラン表)・
  **G-8**(CRPS + spread-skill・初回 seed 群 8 本)。
- 世界データ構築仕様書 **§2 D-W1〜D-W22** の各行「感度: …」と **§4 expedient 登録簿**。
- 実装計画書 **§8 expedient 登録簿**・**§9.1 C8**「ablation 第1陣 6 本(20% 予約枠)・
  expedient 登録簿の感度試験・忠実度計器盤・アンサンブル運用(Phase 5)/
  検収=各 expedient の『結果を駆動していない』証明」。

自前の細部(expedient・実装計画書 §8 へ写した)
- **感度行の抽出規則**: 設計書から「``感度``(必須)?:」で始まる箇条書きを正規表現で拾い、
  直前の ``### D-W\\d+`` 見出しを行 id にする。文献根拠は無い(漏れ検出のための機械規則)。
- **帰無参照**: 「同じ分布から 2 回引いた 2 標本の JSD」の 95% 点を多項リサンプリングで作る
  (``c6lib.null_jsd_reference`` と同じ考え方・標本数 ``NULL_REPS``)。合格線ではなく
  **「差を検出せず」の下限**として使う(知覚契約書 §8 の指標 B と同じ読み)。
- **構築段階の対照で言えること**: 構築対照(入力側)の差が帰無参照以内なら
  「この expedient はランの結果を駆動しえない」が**言える**(入力が動かないため)。
  超えたときは「駆動する**かもしれない**」までしか言えず、**ラン側の対照が要る**
  (片側の論法・``verdict`` の語で区別する)。
- **GPU 時間の見積り**: 受入報告 C6 の実測(5,000 体×1,440 tick の実 LLM ラン=呼 50,000 を
  7×A5000 で約 29 分)から ``CALLS_PER_SECOND`` を置く。**実測 1 点の外挿=expedient**。
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_C6 = REPO_ROOT / "tools" / "c6"
TOOLS_C7 = REPO_ROOT / "tools" / "c7"
for _p in (TOOLS_C6, TOOLS_C7):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import c6lib  # noqa: E402  (tools/c6 の純関数を再利用)

__all__ = [
    "REPO_ROOT",
    "DESIGN_DIR",
    "ABLATIONS_PATH",
    "SENSITIVITY_PATH",
    "NULL_REPS",
    "CALLS_PER_SECOND",
    "FLEET_GPUS",
    "SensitivityRow",
    "load_json",
    "load_ablations",
    "load_sensitivity",
    "scan_build_spec_sensitivities",
    "scan_plan_sensitivities",
    "scan_first_wave_arms",
    "ledger_gaps",
    "null_jsd_p95",
    "compare_counts",
    "verdict_from_stage",
    "gpu_hours_for_calls",
    "budget_row",
    "markdown_table",
    "write_outputs",
]

DESIGN_DIR = REPO_ROOT / "docs" / "design"
BUILD_SPEC = DESIGN_DIR / "v2-world-data-build-spec.md"
IMPL_PLAN = DESIGN_DIR / "v2-implementation-plan.md"
PERCEPTION_CONTRACT = DESIGN_DIR / "v2-perception-contract.md"

ABLATIONS_PATH = Path(__file__).resolve().parent / "ablations_v1.json"
SENSITIVITY_PATH = Path(__file__).resolve().parent / "sensitivity_v1.json"

#: 帰無参照の標本数(c6lib の ``NULL_REPS`` と同じ 2,000)。
NULL_REPS: int = 2_000

#: 実 LLM 艦隊の実測スループット[呼/秒]。受入報告 C6 §2b(c6-day-1: 5,000 体×1,440 tick=
#: 呼 50,000 を 15:35-16:04=29 分)から。**実測 1 点の外挿=expedient**。
CALLS_PER_SECOND: float = 50_000.0 / (29.0 * 60.0)

#: 艦隊の GPU 枚数(予算宣言表 §5 実測: RTX A5000 ×7)。
FLEET_GPUS: int = 7

# ------------------------------------------------------------------ 入出力(c6lib の再利用)
write_outputs = c6lib.write_outputs


def md_cell(value: Any) -> str:
    """Markdown の表セルへ入れる文字列(``|`` と改行を潰す=表が崩れないように)。

    Example:
        >>> md_cell("|r| ≤ 0.05")
        '\\\\|r\\\\| ≤ 0.05'
    """
    if value is None:
        return "—"
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(headers: Sequence[Any], rows: Iterable[Sequence[Any]]) -> str:
    """``c6lib.markdown_table`` と同じだが**セルの ``|`` を必ず逃がす**。"""
    return c6lib.markdown_table(
        [md_cell(h) for h in headers], [[md_cell(c) for c in r] for r in rows]
    )


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_ablations(path: str | Path | None = None) -> dict[str, Any]:
    """腕定義表(``ablations_v1.json``)を読む。"""
    return load_json(ABLATIONS_PATH if path is None else path)


def load_sensitivity(path: str | Path | None = None) -> dict[str, Any]:
    """感度試験の台帳(``sensitivity_v1.json``)を読む。"""
    return load_json(SENSITIVITY_PATH if path is None else path)


# ------------------------------------------------------------------ 設計書の走査(漏れ検出)
@dataclass(frozen=True)
class SensitivityRow:
    """設計書から機械的に拾った「感度: …」の 1 行。

    Attributes:
        source: 相対パス(``docs/design/…``)。
        anchor: 見出し(``D-W16`` など)か節名。
        text: 「感度:」以降の逐語。
        required: 「感度(必須)」と書かれているか。
    """

    source: str
    anchor: str
    text: str
    required: bool = False

    @property
    def key(self) -> str:
        return f"{self.source}#{self.anchor}"


_SENS_RE = re.compile(r"感度(?:試験)?\s*(?:\(必須\)|\(必須\))?\s*[::]\s*(.+?)(?:$)")
_HEAD_RE = re.compile(r"^###\s+(D-W\d+)")


def scan_build_spec_sensitivities(path: str | Path | None = None) -> list[SensitivityRow]:
    """世界データ構築仕様書 §2 の「感度: …」を全部拾う(**漏れ検出の分母**)。

    箇条書きの先頭が ``- 感度:`` の行だけでなく、``- expedient: …。感度: …`` のように
    **行の途中で宣言されている**ものも拾う(D-W2/D-W3/D-W5/D-W7/D-W9/D-W10/D-W15/D-W17)。

    Returns:
        見出し(``D-W\\d+``)ごとの :class:`SensitivityRow`。見出しの外にある行は捨てる。
    """
    p = Path(BUILD_SPEC if path is None else path)
    rows: list[SensitivityRow] = []
    anchor = ""
    rel = p.relative_to(REPO_ROOT).as_posix() if p.is_relative_to(REPO_ROOT) else p.name
    for line in p.read_text(encoding="utf-8").splitlines():
        h = _HEAD_RE.match(line)
        if h:
            anchor = h.group(1)
            continue
        if line.startswith("## "):
            anchor = ""  # §3 以降へ出たら見出しの外
            continue
        if not anchor or "感度" not in line or not line.lstrip().startswith(("-", "*")):
            continue
        m = _SENS_RE.search(line)
        if m:
            tail = line.split("感度", 1)[1][:10]
            rows.append(SensitivityRow(rel, anchor, m.group(1).strip(), "必須" in tail))
    return rows


def scan_engine_ablation_ids(root: str | Path | None = None) -> dict[str, str]:
    """``src/shibuya/engine/processes/*.py`` が宣言する ``ablation_id``(``AB-*``)を集める。

    世界過程は台帳の門前条件で **1 行 1 感度試験 id** を持つ(実装計画書 §8「第1陣の宣言
    21 過程…各行に感度試験 id(AB-*)と返済期限」)。これらは ``--ablate <AB-*>`` で
    そのまま切れるので、**台帳に載っているか**の突合対象になる。

    Returns:
        ``{AB-id: モジュール名}``。
    """
    base = Path(root) if root is not None else REPO_ROOT / "src" / "shibuya" / "engine" / "processes"
    pat = re.compile(r'ablation_id:\s*Final\[str\]\s*=\s*(?:ABLATION_IDS\[\d+\]|"(AB-[A-Z0-9-]+)")')
    out: dict[str, str] = {}
    for f in sorted(base.glob("*.py")):
        text = f.read_text(encoding="utf-8")
        for m in pat.finditer(text):
            if m.group(1):
                out[m.group(1)] = f.name
        if "ABLATION_IDS" in text and f.name == "salient.py":
            for k in range(5):
                out[f"AB-PNOTICE-A{k}"] = f.name
    return out


def scan_plan_sensitivities(path: str | Path | None = None) -> list[SensitivityRow]:
    """実装計画書 §8 登録簿のうち「感度(試験)?:」を宣言している行を拾う(**報告用**)。

    §8 は自由文なので網羅は保証しない(漏れ検出の**分母には使わない**)。id は行内の
    ``E-…`` / ``AB-…`` / ``RAKE_MAX_FRAC`` 等の識別子、無ければ行番号。
    """
    p = Path(IMPL_PLAN if path is None else path)
    rel = p.relative_to(REPO_ROOT).as_posix() if p.is_relative_to(REPO_ROOT) else p.name
    text = p.read_text(encoding="utf-8").splitlines()
    start = next((i for i, s in enumerate(text) if s.startswith("## §8")), 0)
    stop = next((i for i, s in enumerate(text) if i > start and s.startswith("## §9")), len(text))
    id_re = re.compile(r"(E-[A-Z0-9-]+[a-z]?|AB-[A-Z0-9-]+|RAKE_MAX_FRAC|KIND_TO_ATTR)")
    rows: list[SensitivityRow] = []
    for i in range(start, stop):
        line = text[i]
        if "感度" not in line or not line.lstrip().startswith(("-", "*", "**")):
            continue
        m = id_re.search(line)
        rows.append(SensitivityRow(rel, m.group(1) if m else f"L{i + 1}", line.strip()[:400]))
    return rows


def scan_first_wave_arms(path: str | Path | None = None) -> list[str]:
    """知覚契約書 §8 の「第1陣(…)=6本: ①… ②… ⑥…」を丸数字で切り出す。

    Returns:
        6 本の逐語(丸数字は落とす)。**本数が 6 でなければ設計書が変わった合図**。
    """
    p = Path(PERCEPTION_CONTRACT if path is None else path)
    text = p.read_text(encoding="utf-8")
    m = re.search(r"\*\*第1陣[^*]*=\s*6本\*\*\s*[::]?\s*(.+)", text)
    if m is None:
        return []
    tail = m.group(1)
    tail = tail.split("**第2陣**")[0]
    parts = re.split(r"[①②③④⑤⑥]", tail)
    return [s.strip().strip("。 ") for s in parts[1:7] if s.strip()]


def ledger_gaps(
    rows: Sequence[SensitivityRow], ledger: Mapping[str, Any]
) -> dict[str, list[str]]:
    """設計書の感度行が台帳に載っているか(漏れ)/台帳にしか無い行(過剰)を返す。

    突合は ``anchor``(``D-W16``・``RAKE_MAX_FRAC`` など)を台帳行の ``design_anchor`` と
    照らす。**大文字小文字と全角は正規化しない**(設計書の表記を正とする)。
    """
    have = {str(r.get("design_anchor", "")) for r in ledger.get("rows", [])}
    want = {r.anchor for r in rows}
    return {
        "missing": sorted(want - have),  # 設計書にあるのに台帳に無い=漏れ
        "extra": sorted(x for x in have - want if x),  # 台帳にしか無い(§8 由来など)
    }


# ------------------------------------------------------------------ 判定の道具
def null_jsd_p95(counts: Sequence[float], reps: int = NULL_REPS, seed: int = 20260909) -> float:
    """**同じ分布から 2 回引いた**2 標本の JSD[bits] の 95% 点(帰無参照)。

    ``counts`` の総数 N と形を保ったまま多項分布から 2 標本を引いて JSD を測る、を
    ``reps`` 回。標本ゆらぎだけで出る JSD の大きさが分かるので、**対照との差が
    この値以下なら「差を検出せず」**と読む(知覚契約書 §8 の指標 B と同じ規約)。

    Example:
        >>> round(null_jsd_p95([100.0, 100.0, 100.0], reps=200), 4) < 0.05
        True
    """
    c = np.asarray(counts, dtype=np.float64).ravel()
    total = float(c.sum())
    if total <= 0.0 or c.size < 2:
        return 0.0
    p = c / total
    n = int(round(total))
    rng = np.random.default_rng(seed)
    vals = np.empty(int(reps), dtype=np.float64)
    for i in range(int(reps)):  # 逐次(P4): 標本数ぶん。ツール側=ランの逐次ループではない
        a = rng.multinomial(n, p)
        b = rng.multinomial(n, p)
        vals[i] = c6lib.jsd(a, b)
    return float(np.percentile(vals, 95.0))


def compare_counts(
    declared: Sequence[float],
    control: Sequence[float],
    *,
    reps: int = NULL_REPS,
    seed: int = 20260909,
    labels: Sequence[str] | None = None,
) -> dict[str, Any]:
    """宣言値の分布 vs 対照の分布(**構築段階の対照の標準形**)。

    Returns:
        ``jsd_bits``(距離)・``tvd``(総変動距離=「配置が入れ替わった割合」)・
        ``null_p95``(帰無参照)・``detected``(jsd > null_p95)・``n``・``n_bins``。
    """
    a = np.asarray(declared, dtype=np.float64).ravel()
    b = np.asarray(control, dtype=np.float64).ravel()
    if a.size != b.size:
        raise ValueError(f"分布の長さが違う: {a.size} vs {b.size}")
    sa, sb = float(a.sum()), float(b.sum())
    pa = a / sa if sa > 0 else a
    pb = b / sb if sb > 0 else b
    jsd = c6lib.jsd(a, b)
    null = null_jsd_p95(a, reps=reps, seed=seed)
    out: dict[str, Any] = {
        "jsd_bits": float(jsd),
        "tvd": float(0.5 * np.abs(pa - pb).sum()),
        "null_p95": float(null),
        "detected": bool(jsd > null),
        "n_declared": sa,
        "n_control": sb,
        "n_bins": int(a.size),
    }
    if labels is not None and len(labels) == a.size:
        order = np.argsort(-np.abs(pa - pb))[:5]
        out["top_shifts"] = [
            {"label": str(labels[i]), "declared": float(pa[i]), "control": float(pb[i])}
            for i in order
        ]
    return out


def verdict_from_stage(detected: bool) -> str:
    """構築段階の対照から**言えること**(片側の論法)。

    - ``detected=False``: 入力が帰無参照の中で動かない → **「結果を駆動していない」が言える**
      (``not_driving``)。
    - ``detected=True``: 入力は動く → 駆動する**かもしれない**。ラン側の対照が要る
      (``needs_run``)。構築段階だけで「駆動している」と結論しない。
    """
    return "needs_run" if detected else "not_driving"


def gpu_hours_for_calls(calls: float, calls_per_second: float = CALLS_PER_SECOND) -> float:
    """呼数 → 艦隊の壁時計[時間](**実測 1 点の外挿=expedient**)。"""
    if calls_per_second <= 0.0:
        raise ValueError("calls_per_second は正")
    return float(calls) / float(calls_per_second) / 3_600.0


def budget_row(row_id: str) -> dict[str, Any] | None:
    """予算宣言表の 1 行(Markdown が正典・数値をここに複製しない)。"""
    from shibuya.core.budget import budget_by_id, load_budget_table, parse_limit

    row = budget_by_id(load_budget_table()).get(row_id)
    if row is None:
        return None
    lim = parse_limit(row.declared)
    return {
        "id": row_id,
        "item": row.item,
        "declared": row.declared,
        "limit": None if lim is None else lim[0],
        "unit": None if lim is None else lim[1],
    }


def fmt(value: Any, nd: int = 4) -> str:
    """表用の整形(``None``/NaN は「—」)。"""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "はい" if value else "いいえ"
    if isinstance(value, float):
        if value != value:  # NaN
            return "—"
        return f"{value:.{nd}f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def iter_rows(ledger: Mapping[str, Any], key: str = "rows") -> Iterable[Mapping[str, Any]]:
    for r in ledger.get(key, ()):
        if isinstance(r, Mapping):
            yield r
