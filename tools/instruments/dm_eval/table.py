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
- 〔11-01 段 1 の 3〕比べの列を表の末尾に足した(既存の 25 列は位置も見出しも変えない): 推論の形(Choice/Score/Noul・
  規則・記録)・(G)=8B の logprob との 1 位の一致率(JSD は既存の列)・決定論(同一入力 N 回=既定 32 で全回一致の率と
  回数)・日本語での破綻率(定義は ``backends.base`` の説明)・VRAM(欄だけ=GPU の後)・何をいくつの数の平均と
  (G) との数の一致率と差の平均。分布の広がり=既存の「迷い エントロピー(平均)」。位置の偏り(巡回・PBS)と 1 件の秒は
  既存の列。
"""

from __future__ import annotations

import json
from typing import Any, Final, Mapping, Sequence

import dm_eval  # noqa: F401
from dm_eval.judge import ROLE_WORDS

#: 列(鍵, 見出し)。順位の列は無い。1-10 の記録(dm61)の 25 列は位置も見出しも変えない。
COLUMNS_V1: Final[tuple[tuple[str, str], ...]] = (
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
#: 〔11-01〕足した列(表の末尾=既存の列の位置を変えない・〔検収 低 1〕)。
COLUMNS_1101: Final[tuple[tuple[str, str], ...]] = (
    ("form", "推論の形"),
    ("top1_agree_vs_g", "1 位の一致率(対 (G))"),
    ("determinism_rate", "決定論(同一入力で全回一致の率)"),
    ("determinism_repeats", "決定論の回数"),
    ("breakdown_rate", "日本語での破綻率"),
    ("vram_gb", "VRAM(GB)"),
    ("qty_mean", "数の平均(何をいくつ)"),
    ("qty_agree_vs_g", "数の一致率(対 (G)・何をいくつ)"),
    ("qty_absdiff_vs_g", "数の差の平均(対 (G)・何をいくつ)"),
)
COLUMNS: Final[tuple[tuple[str, str], ...]] = COLUMNS_V1 + COLUMNS_1101
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
BLANK_NOT_MODEL: Final[str] = "該当なし(モデルの答えでない)"
BLANK_NO_REF: Final[str] = "該当なし(基準の記録なし)"
BLANK_NO_QTY: Final[str] = "該当なし(数の候補なし)"
BLANK_LABELS: Final[tuple[str, ...]] = (BLANK_GPU, BLANK_SELF, BLANK_VALIDATION, BLANK_MATERIAL, BLANK_NOT_RETURNED,
                                        BLANK_NO_TEXT, BLANK_NO_GPU, BLANK_UNDEFINED, BLANK_NOT_MODEL, BLANK_NO_REF,
                                        BLANK_NO_QTY)
#: 自分との比べの欄(当て口 → 列)。
_SELF_COLUMNS: Final[Mapping[str, tuple[str, ...]]] = {
    "classical": ("jsd_vs_classical", "spearman_vs_classical"),
    "tape": ("jsd_vs_tape", "top1_agree_vs_tape"),
}
#: 位置の偏りの列(提示の並びを見ていない当て口では構成上 0)。
BIAS_COLUMNS: Final[tuple[str, ...]] = ("self_consistency_2", "top1_change_rate", "number1_rate", "pbs", "number1_p")
#: 〔11-01〕(G)=8B の logprob との比べの列。
G_COLUMNS: Final[tuple[str, ...]] = ("jsd_vs_g", "top1_agree_vs_g", "qty_agree_vs_g", "qty_absdiff_vs_g")
#: 〔11-01 検収 低 7〕「何をいくつ」の数の列。
QTY_COLUMNS: Final[tuple[str, ...]] = ("qty_mean", "qty_agree_vs_g", "qty_absdiff_vs_g")
#: 〔11-01〕(G) の当て口の名の頭(``judge.GScorer``=``g_first_token`` と ``cli`` が作る ``g_…``)。
G_PREFIX: Final[str] = "g_"
#: 〔11-01〕モデルの推論の形(GPU で回す=トークン・VRAM・GPU 時間の欄は「GPU の後で埋める」)。
MODEL_FORMS: Final[frozenset[str]] = frozenset({"Choice", "Score", "Noul"})
#: 〔11-01〕基準の記録が無いときの列(消費の場面=テープの記録なし)。
_REF_COLUMNS: Final[Mapping[str, tuple[str, ...]]] = {
    "tape": ("jsd_vs_tape", "top1_agree_vs_tape"),
    "classical": ("jsd_vs_classical", "spearman_vs_classical"),
}


def blank_reason(row: Mapping[str, Any], key: str, *, missing_refs: Sequence[str] = ()) -> str | None:
    """空の欄の印(値があれば ``None``・注の欄は空でよい=``""``)。``missing_refs`` は記録の無い基準の名。"""
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
    if any(key in _REF_COLUMNS.get(r, ()) for r in missing_refs):
        return BLANK_NO_REF
    model = row.get("form") in MODEL_FORMS
    if key in QTY_COLUMNS and row.get("implemented") and row.get("qty_mean") is None:
        return BLANK_NO_QTY
    if key in G_COLUMNS and row.get("implemented") and str(row.get("scorer", "")).startswith(G_PREFIX):
        return BLANK_SELF
    if not row.get("implemented") or key in G_COLUMNS:
        return BLANK_GPU
    if key == "surprise":
        return BLANK_NOT_RETURNED
    if key == "breakdown_rate":
        return BLANK_NOT_MODEL
    if key in ("tokens_in", "vram_gb", "gpu_hours_per_sim_day") and model:
        return BLANK_GPU
    if key == "tokens_in":
        return BLANK_NO_TEXT
    if key in ("gpu_hours_per_sim_day", "vram_gb"):
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
               tape_fixed: Mapping[str, Any] | None = None, compare: Mapping[str, Any] | None = None
               ) -> list[dict[str, Any]]:
    """当て口ごとの結果(``cli.evaluate`` の ``scorers`` の各要素)→ 表の行。

    〔11-01〕``compare``(``cli.evaluate`` の ``compare`` の節)から推論の形・決定論・破綻率・数の指標・失敗の数を読む
    (無ければ空)。推論の形 Noul の行の「その他の率」は明示の「その他」だけ(破綻を入れない=〔検収 低 5〕)。
    """
    rows: list[dict[str, Any]] = []
    cmp_by = dict((compare or {}).get("scorers") or {})
    for sc in scorers:
        d = sc["describe"]
        cm = cmp_by.get(d["name"]) or {}
        det = cm.get("determinism") or {}
        for arm in arms:
            r = (sc.get("by_arm") or {}).get(arm) or {}
            ag_c = r.get("agreement_vs_classical") or {}
            ag_t = r.get("agreement_vs_tape") or {}
            ag_g = r.get("agreement_vs_g") or {}
            bd = (cm.get("breakdown") or {}).get(arm) or {}
            qty = (cm.get("qty") or {}).get(arm) or {}
            fails = ((cm.get("failures") or {}).get(arm) or {}).get("n", 0)
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
            if d["implemented"] and cm.get("uses_gpu"):
                notes.append("壁時計は GPU の口の実測")
            if fails:
                notes.append(f"失敗 {fails} 場面(採点から外した)")
            other = r.get("other_rate")
            if cm.get("form") == "Noul":
                other = bd.get("other_explicit_rate")
            row = {
                "scorer": d["name"], "role": ROLE_WORDS.get(d["role"], d["role"]),
                "implemented": bool(d["implemented"]), "lang": lang, "first_language": None, "arm": arm,
                "jsd_vs_classical": ag_c.get("jsd_mean"), "spearman_vs_classical": ag_c.get("spearman_mean"),
                "jsd_vs_tape": ag_t.get("jsd_mean"), "top1_agree_vs_tape": ag_t.get("top1_agree"),
                "jsd_vs_g": ag_g.get("jsd_mean"),
                "self_consistency_2": bias.get("self_consistency_2"), "top1_change_rate": bias.get("top1_change_rate"),
                "number1_rate": bias.get("number1_rate"), "pbs": _pbs_of(bias),
                "number1_p": (bias.get("number1_test") or {}).get("p"),
                "margin_mean": hes.get("margin_mean"), "entropy_mean": hes.get("entropy_mean"),
                "surprise": None, "other_rate": other, "human_match": None,
                "wall_s_per_item": spd.get("wall_s_per_item"), "tokens_in": spd.get("tokens_in"),
                "gpu_hours_per_sim_day": spd.get("gpu_hours_per_sim_day"), "notes": "・".join(notes) or None,
                "form": cm.get("form"), "top1_agree_vs_g": ag_g.get("top1_agree"),
                "determinism_rate": det.get("item_agree_rate"),
                "determinism_repeats": det.get("n_repeats") if det.get("item_agree_rate") is not None else None,
                "breakdown_rate": bd.get("breakdown_rate"), "vram_gb": None,
                "qty_mean": qty.get("qty_mean"), "qty_agree_vs_g": qty.get("agree_vs_g"),
                "qty_absdiff_vs_g": qty.get("absdiff_vs_g"),
            }
            assert tuple(row) == COLUMN_KEYS
            rows.append(row)
    return rows


def blanks_of(rows: Sequence[Mapping[str, Any]], *, missing_refs: Sequence[str] = ()) -> list[dict[str, str]]:
    """行ごとの空の欄 → 印(注の欄は除く)。"""
    out = []
    for r in rows:
        out.append({k: str(blank_reason(r, k, missing_refs=missing_refs)) for k in COLUMN_KEYS
                    if k != "notes" and r.get(k) is None})
    return out


def _cell(row: Mapping[str, Any], key: str, missing_refs: Sequence[str] = ()) -> str:
    v = row.get(key)
    if v is None:
        return str(blank_reason(row, key, missing_refs=missing_refs))
    if isinstance(v, bool):
        return "実装" if v else "口だけ"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v).replace("|", "/")


def to_markdown(rows: Sequence[Mapping[str, Any]], *, languages: Mapping[str, Any] | None = None,
                footnotes: Sequence[str] = (), missing_refs: Sequence[str] = ()) -> str:
    """表を Markdown に(空の欄は ``blank_reason`` の印)。"""
    lines = ["| " + " | ".join(h for _k, h in COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    for r in rows:
        lines.append("| " + " | ".join(_cell(r, k, missing_refs) for k in COLUMN_KEYS) + " |")
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
            footnotes: Sequence[str] = (), missing_refs: Sequence[str] = ()) -> str:
    doc = {"columns": [{"key": k, "header": h} for k, h in COLUMNS], "rows": list(rows),
           "blank": blanks_of(rows, missing_refs=missing_refs),
           "order": ORDER_NOTE, "footnotes": list(footnotes), "languages": dict(languages or {})}
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
