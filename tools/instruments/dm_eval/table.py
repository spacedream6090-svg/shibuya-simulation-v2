# -*- coding: utf-8 -*-
"""dm_eval.table — 表「人らしさ × 速さ × 1 シム日あたりの GPU 時間」(DM1・§1-9・第 6 期 6-1 の器)。

- 行=当て口ごと × 言語ごと × 長さの腕ごと。並びは当て口の宣言の順(対照 → 基準 → 候補)・**順位の列は持たない・
  指標で並べ替えない**(ユーザーが選ぶ=§1-9・DM1)。
- 値の無い欄は ``None``。Markdown と JSON の ``blank`` では、その理由を 2 つの印のどちらかで示す(``blank_reason``):
  「GPU の後で埋める」(口だけの当て口の欄・(G) との比べ・トークン数)と「該当なし(…)」(自分との比べ・検証側の
  人のデータ・材料に無い第一言語・その当て口が返さない驚き・GPU を使わない当て口の GPU 時間など。括弧に理由)。
- 提示の並びを見ていない当て口(テープ)の行は、注の先頭に「位置の偏りの列は構成上 0」と書く(表だけを読んで
  「8B に位置の偏りが無い」と読めないように)。
- 言語の欄: 材料は日本語だけ(``ja``)。住人の第一言語の欄は「該当なし(材料なし)」(§4-8)。日本語の外の行は材料が
  無い=作らない(``languages`` に書く)。
"""

from __future__ import annotations

import json
from typing import Any, Final, Mapping, Sequence

import dm_eval  # noqa: F401
from dm_eval.judge import ROLE_WORDS

#: 列(鍵, 見出し)。順位の列は無い。
COLUMNS: Final[tuple[tuple[str, str], ...]] = (
    ("scorer", "当て口"),
    ("role", "役割"),
    ("implemented", "実装"),
    ("lang", "言語"),
    ("first_language", "第一言語の欄"),
    ("arm", "長さの腕"),
    ("jsd_vs_classical", "一致 JSD(対 古典)"),
    ("spearman_vs_classical", "順位相関(対 古典)"),
    ("jsd_vs_tape", "一致 JSD(対 テープ)"),
    ("top1_agree_vs_tape", "1 位の一致率(対 テープ)"),
    ("jsd_vs_g", "一致 JSD(対 (G))"),
    ("self_consistency_2", "自己整合(並びを変えて同じ 1 位)"),
    ("top1_change_rate", "1 位が変わる率"),
    ("number1_rate", "番号 1 を選ぶ率"),
    ("pbs", "PBS"),
    ("number1_p", "番号 1 の検定の p"),
    ("margin_mean", "迷い 差(平均)"),
    ("entropy_mean", "迷い エントロピー(平均)"),
    ("surprise", "驚き(0〜5)"),
    ("other_rate", "その他の率"),
    ("human_match", "人のデータとの照合"),
    ("wall_s_per_item", "1 件の壁時計(秒・CPU)"),
    ("tokens_in", "入力トークン"),
    ("gpu_hours_per_sim_day", "1 シム日あたりの GPU 時間"),
    ("notes", "注"),
)
COLUMN_KEYS: Final[tuple[str, ...]] = tuple(k for k, _ in COLUMNS)
ORDER_NOTE: Final[str] = "並びは当て口の宣言の順(対照 → 基準 → 候補)。順位は付けない(ユーザーが選ぶ=決定 10-12 §1-9・DM1)"

#: 空の欄の 2 つの印(「GPU の後で埋める」と「該当なし(理由)」)。
BLANK_GPU: Final[str] = "GPU の後で埋める"
BLANK_SELF: Final[str] = "該当なし(自分との比べ)"
BLANK_VALIDATION: Final[str] = "該当なし(検証側=値を入れない)"
BLANK_MATERIAL: Final[str] = "該当なし(材料なし=§4-8)"
BLANK_NOT_RETURNED: Final[str] = "該当なし(この当て口は返さない)"
BLANK_NO_TEXT: Final[str] = "該当なし(文を読まない)"
BLANK_NO_GPU: Final[str] = "該当なし(GPU を使わない)"
BLANK_UNDEFINED: Final[str] = "該当なし(定義できない)"
BLANK_LABELS: Final[tuple[str, ...]] = (BLANK_GPU, BLANK_SELF, BLANK_VALIDATION, BLANK_MATERIAL, BLANK_NOT_RETURNED,
                                        BLANK_NO_TEXT, BLANK_NO_GPU, BLANK_UNDEFINED)
#: 自分との比べの欄(当て口 → 列)。
_SELF_COLUMNS: Final[Mapping[str, tuple[str, ...]]] = {
    "classical": ("jsd_vs_classical", "spearman_vs_classical"),
    "tape": ("jsd_vs_tape", "top1_agree_vs_tape"),
}
#: 位置の偏りの列(提示の並びを見ていない当て口では構成上 0)。
BIAS_COLUMNS: Final[tuple[str, ...]] = ("self_consistency_2", "top1_change_rate", "number1_rate", "pbs", "number1_p")


def blank_reason(row: Mapping[str, Any], key: str) -> str | None:
    """空の欄の印(値があれば ``None``・注の欄は空でよい=``""``)。"""
    if row.get(key) is not None:
        return None
    if key == "notes":
        return ""
    if key in _SELF_COLUMNS.get(str(row.get("scorer")), ()):
        return BLANK_SELF
    if key == "human_match":
        return BLANK_VALIDATION
    if key == "first_language":
        return BLANK_MATERIAL
    if not row.get("implemented") or key == "jsd_vs_g":
        return BLANK_GPU
    if key == "surprise":
        return BLANK_NOT_RETURNED
    if key == "tokens_in":
        return BLANK_NO_TEXT
    if key == "gpu_hours_per_sim_day":
        return BLANK_NO_GPU
    return BLANK_UNDEFINED


def _pbs_of(bias: Mapping[str, Any] | None) -> float | None:
    if not bias:
        return None
    vals = [v.get("pbs") for v in (bias.get("pbs_by_n") or {}).values() if v.get("pbs") is not None]
    return vals[0] if len(vals) == 1 else None


def order_blind_note(tape_fixed: Mapping[str, Any] | None) -> str:
    """提示の並びを見ていない当て口の注(表だけを読んで位置の偏りが無いと読めないように)。"""
    rate = None if not tape_fixed else tape_fixed.get("position1_rate")
    fixed = "" if rate is None else f"・固定の並びでの位置 1 の率 {rate:.2f} は位置と中身が重なり分けられない"
    return ("位置の偏りの列は構成上 0(テープの LLM はここで入れ替えた並びを見ていない=8B の位置の偏りの測りではない"
            f"{fixed})")


def build_rows(scorers: Sequence[Mapping[str, Any]], *, arms: Sequence[str], lang: str = "ja",
               tape_fixed: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """当て口ごとの結果(``cli.evaluate`` の ``scorers`` の各要素)→ 表の行。"""
    rows: list[dict[str, Any]] = []
    for sc in scorers:
        d = sc["describe"]
        for arm in arms:
            r = (sc.get("by_arm") or {}).get(arm) or {}
            ag_c = r.get("agreement_vs_classical") or {}
            ag_t = r.get("agreement_vs_tape") or {}
            bias = r.get("position_bias") or {}
            hes = r.get("hesitation") or {}
            spd = r.get("speed") or {}
            notes = []
            if d["implemented"] and not d.get("sees_presented_order", True):
                notes.append(order_blind_note(tape_fixed))
            if not d["implemented"]:
                notes.append("口だけ=重みの取得と GPU の後(S6)")
            extra = (d.get("meta") or {}).get("extra_measures")
            if extra:
                notes.append("追加の測り(GPU の後で埋める): " + "・".join(sorted(extra)))
            if d["implemented"] and not d["reads_text"]:
                notes.append("文を読まない=腕で結果は変わらない")
            row = {
                "scorer": d["name"], "role": ROLE_WORDS.get(d["role"], d["role"]),
                "implemented": bool(d["implemented"]), "lang": lang, "first_language": None, "arm": arm,
                "jsd_vs_classical": ag_c.get("jsd_mean"), "spearman_vs_classical": ag_c.get("spearman_mean"),
                "jsd_vs_tape": ag_t.get("jsd_mean"), "top1_agree_vs_tape": ag_t.get("top1_agree"),
                "jsd_vs_g": None,
                "self_consistency_2": bias.get("self_consistency_2"), "top1_change_rate": bias.get("top1_change_rate"),
                "number1_rate": bias.get("number1_rate"), "pbs": _pbs_of(bias),
                "number1_p": (bias.get("number1_test") or {}).get("p"),
                "margin_mean": hes.get("margin_mean"), "entropy_mean": hes.get("entropy_mean"),
                "surprise": None, "other_rate": r.get("other_rate"), "human_match": None,
                "wall_s_per_item": spd.get("wall_s_per_item"), "tokens_in": spd.get("tokens_in"),
                "gpu_hours_per_sim_day": spd.get("gpu_hours_per_sim_day"), "notes": "・".join(notes) or None,
            }
            assert tuple(row) == COLUMN_KEYS
            rows.append(row)
    return rows


def blanks_of(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """行ごとの空の欄 → 印(注の欄は除く)。"""
    out = []
    for r in rows:
        out.append({k: str(blank_reason(r, k)) for k in COLUMN_KEYS if k != "notes" and r.get(k) is None})
    return out


def _cell(row: Mapping[str, Any], key: str) -> str:
    v = row.get(key)
    if v is None:
        return str(blank_reason(row, key))
    if isinstance(v, bool):
        return "実装" if v else "口だけ"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v).replace("|", "/")


def to_markdown(rows: Sequence[Mapping[str, Any]], *, languages: Mapping[str, Any] | None = None,
                footnotes: Sequence[str] = ()) -> str:
    """表を Markdown に(空の欄は ``blank_reason`` の印)。"""
    lines = ["| " + " | ".join(h for _k, h in COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for r in rows:
        lines.append("| " + " | ".join(_cell(r, k) for k in COLUMN_KEYS) + " |")
    lines.append("")
    lines.append(f"- {ORDER_NOTE}")
    lines.append(f"- 空の欄の印: 「{BLANK_GPU}」と「該当なし(理由)」の 2 種")
    for f in footnotes:
        lines.append(f"- {f}")
    if languages:
        for lang, v in languages.items():
            lines.append(f"- 言語 {lang}: {'該当なし(材料なし)' if v is None else v}")
    return "\n".join(lines) + "\n"


def to_json(rows: Sequence[Mapping[str, Any]], *, languages: Mapping[str, Any] | None = None,
            footnotes: Sequence[str] = ()) -> str:
    doc = {"columns": [{"key": k, "header": h} for k, h in COLUMNS], "rows": list(rows), "blank": blanks_of(rows),
           "order": ORDER_NOTE, "footnotes": list(footnotes), "languages": dict(languages or {})}
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
