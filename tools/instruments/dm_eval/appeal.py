# -*- coding: utf-8 -*-
"""dm_eval.appeal — 「呼びかけへの反応のずれ」の列(第 347・返事その 8 §6-2・記録 2-61 ①・2-62・2-65)。

測り方(記録 2-62): 同じ場面を呼びかけあり・なしで出し、行動の変わる割合を人の研究と比べる。人のデータが無い場面は、
呼びかけの強さ(お願い・命令・今すぐ)でどれだけ変わるかが極端でないかを見る。

場面の組(``scenes/appeal_v1.jsonl``・``situations.load_scene_file(..., point_names=APPEAL_TYPES)``)
    行の欄 ``appeal`` に対の印を持つ。組(``family``)ごとに「ない版」が 1 つ、「ある版」が 1 つ以上。対=(ある版・同じ組の
    ない版)。同じ組の行は候補が同じ(id・語・文・源)で、観測の違いは呼びかけの 1 行だけ(試験で確かめる)。
    種類: 頼み(``request``=Langer ら 1978 の形・大きさ 2 段 × 理由 3 条件)・禁止の表示(``prohibition``=Keizer ら 2008 の
    形・周りの様子 2 段)・店頭の呼びかけ(``shop_call``=人の値なし・強さ 3 段)。

列(当て口ごと・長さの腕ごと)
    分布=並べ替え N 通りの分布を候補の id ごとに平均した物(位置の偏りを均す)。対の 2 つは同じ提示の並び
    (``order_keys``=場面の鍵で並べる=``cli.evaluate(order_keys=…)``)。
    (i) 応じる確率の差 ``comply_diff`` = P(応じる | あり) − P(応じる | なし)(対の平均・種類ごと・条件ごと)
    (ii) 分布の差 ``jsd`` = ``judge.jsd``(底 2・0〜1)の対の平均
    (iii) 1 位が変わった対の割合 ``top1_change``(``judge.top1``=同点は id の順)
    禁止の表示の場面だけ ``violate_diff`` = P(破る | あり) − P(破る | なし)。
    対比(``contrasts``): 頼みの理由の差・大きさの差(Langer)、掲示ありでの周りの様子の差(Keizer)、強さの段の差と幅。

人の値(``HUMAN_CONDITIONS``・``HUMAN_CONTRASTS``)
    記録 2-54 にある値だけ(Langer ら 1978 の率・Keizer ら 2008 は向きの見込みだけ)。どれも「記録 2-54 の文の値(Langer ら 1978 は答申での一次確認なし=R-149 の追補 1 から 11-21 の決定で外し、追補 3 でも原典を読めなかった)」〔第348・前は「R-149 の追補 1 で一次確認中」〕。
    対比の人の値は記録の値の引き算。人の研究の値は「人の割合」、当て口の値は「1 回の判断の確率の平均」=同じ量と読むのは
    住民が分布から引くと見なすとき(限界に書く)。

対照(``default_controls``・列の計算の確かめ用=モデルの測りではない)
    ``AppealFollowControl``(正の対照): 文に出どころの印があれば「応じる」候補に 1、無ければ「何もしない」候補に 1
    → 差 1・JSD 1・1 位が変わる率 1。``AppealIgnoreControl``(負の対照): いつも「何もしない」に 1 → 0・0・0。

``digest`` の外(``cli`` の結果の欄 ``appeal`` と ``appeal_digest``)。既定の走らせ方(evalset)は今のまま。
expedient(未リサーチ): 分布を並べ替えで平均すること・対比の作り方・強さの段の文(命令・今すぐ)・極端かの線は置かない(親)。
逐次ループ宣言: 対の数 × 当て口 × 腕。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import dm_eval  # noqa: F401
from dm_eval import judge as J
from dm_eval import situations as S
from dm_eval.table import BLANK_GPU, BLANK_NO_PAIR
from shibuya.foundation.ports.decision import Candidate

#: 呼びかけの節の形の版。
APPEAL_SCHEMA: Final[str] = "shibuya.tools.dm_eval.appeal/1"
TYPES: Final[tuple[str, ...]] = tuple(S.APPEAL_TYPES)
SIZES: Final[tuple[str, ...]] = ("small", "large")
REASONS: Final[tuple[str, ...]] = ("none", "placebic", "real")
ENVS: Final[tuple[str, ...]] = ("orderly", "disorderly")
STRENGTHS: Final[tuple[str, ...]] = ("please", "command", "now")
SIZE_WORDS: Final[Mapping[str, str]] = MappingProxyType({"small": "小さい頼み", "large": "大きい頼み"})
REASON_WORDS: Final[Mapping[str, str]] = MappingProxyType({"none": "理由なし", "placebic": "形だけの理由",
                                                           "real": "本当の理由"})
ENV_WORDS: Final[Mapping[str, str]] = MappingProxyType({"orderly": "周りが整っている", "disorderly": "周りが乱れている"})
STRENGTH_WORDS: Final[Mapping[str, str]] = MappingProxyType({"please": "お願い", "command": "命令", "now": "今すぐ"})
#: 出どころの印(場面の文の呼びかけの行にだけ出る=``scenes/make_appeal_v1.py`` の ``TAG_*`` と同じ文字列)。
MARKERS: Final[tuple[str, ...]] = ("〔素性: 店頭表示〕", "〔素性: 掲示〕", "〔発話〕")
#: 行の欄 ``appeal`` の鍵。
META_KEYS: Final[frozenset[str]] = frozenset({
    "type", "setting", "family", "present", "channel", "line", "condition", "size", "reason", "env", "strength",
    "level", "body", "comply", "violate", "baseline"})

HUMAN_STATUS: Final[str] = "記録 2-54 の文の値(Langer ら 1978 は答申での一次確認なし=R-149 の追補 1 から 11-21 の決定で外し、追補 3 でも原典を読めなかった)"
_LANGER: Final[str] = "記録 2-54(Langer ら 1978)"
_KEIZER: Final[str] = "記録 2-54(Keizer ら 2008)"


def _h(low: float | None, high: float | None, text: str | None, source: str, blank: str | None = None,
       direction: str | None = None) -> Mapping[str, Any]:
    return MappingProxyType({"low": low, "high": high, "text": text, "direction": direction, "source": source,
                             "status": HUMAN_STATUS, "blank": blank})


#: 人の値(条件ごとの「応じた率」=頼みあり)。記録 2-54 の文だけ(値の写しの元は記録)。
HUMAN_CONDITIONS: Final[Mapping[str, Mapping[str, Any]]] = MappingProxyType({
    "request/small/none": _h(0.60, 0.60, "0.60", _LANGER + "「5 枚 60%」"),
    "request/small/placebic": _h(0.93, 0.94, "0.93〜0.94",
                                 _LANGER + "「理由付き 93〜94%」(形だけの理由と本当の理由を分けて書いていない)"),
    "request/small/real": _h(0.93, 0.94, "0.93〜0.94",
                             _LANGER + "「理由付き 93〜94%」(形だけの理由と本当の理由を分けて書いていない)"),
    "request/large/none": _h(0.24, 0.24, "0.24", _LANGER + "「20 枚 24%」"),
    "request/large/placebic": _h(None, None, None, _LANGER,
                                 blank="記録 2-54 に値が無い(「20 枚 24%」が形だけの理由を含むかは記録から読めない)"),
    "request/large/real": _h(0.42, 0.42, "約 0.42", _LANGER + "「本当の理由で約 42%」"),
})
_SUB: Final[str] = "記録 2-54 の値の引き算"
#: 人の値(対比)。
HUMAN_CONTRASTS: Final[Mapping[str, Mapping[str, Any]]] = MappingProxyType({
    "request/small/placebic_minus_none": _h(0.33, 0.34, "+0.33〜+0.34", f"{_LANGER}・{_SUB}"),
    "request/small/real_minus_none": _h(0.33, 0.34, "+0.33〜+0.34", f"{_LANGER}・{_SUB}"),
    "request/small/real_minus_placebic": _h(None, None, None, _LANGER,
                                            blank="記録 2-54 は理由付きを 93〜94% とまとめて書く"),
    "request/large/placebic_minus_none": _h(None, None, None, _LANGER, blank="記録 2-54 に形だけの理由の値が無い"),
    "request/large/real_minus_none": _h(0.18, 0.18, "約 +0.18", f"{_LANGER}・{_SUB}"),
    "request/large/real_minus_placebic": _h(None, None, None, _LANGER, blank="記録 2-54 に形だけの理由の値が無い"),
    "request/none/small_minus_large": _h(0.36, 0.36, "+0.36", f"{_LANGER}・{_SUB}"),
    "request/placebic/small_minus_large": _h(None, None, None, _LANGER, blank="記録 2-54 に形だけの理由の値が無い"),
    "request/real/small_minus_large": _h(0.51, 0.52, "約 +0.51〜+0.52", f"{_LANGER}・{_SUB}"),
    "prohibition/sign/orderly_minus_disorderly": _h(
        None, None, "向きの見込みだけ(+・未確認)", _KEIZER, direction="+",
        blank="記録 2-54 は「禁止の看板の効き目は周りの様子で変わる」とだけ書く=値も符号も記録には無い。+(整った周りで"
              "従う率が高い)は見込み"),
    "prohibition/sign/violate_disorderly_minus_orderly": _h(
        None, None, "向きの見込みだけ(+・未確認)", _KEIZER, direction="+",
        blank="同上(+=乱れた周りで破る率が高い、は見込み)"),
})
#: 人の値が無いときの印(種類ごと)。
HUMAN_NONE: Final[Mapping[str, str]] = MappingProxyType({
    "prohibition": "人の値なし(記録 2-54 は周りの様子で変わるとだけ書く=対比の表)",
    "shop_call": "人の値なし(強さの段で極端でないかを見る・極端の線は未定=親)",
    "overall": "人の値なし(種類と条件を混ぜた平均)",
})

DEFINITIONS: Final[Mapping[str, str]] = MappingProxyType({
    "distribution": "当て口の分布を並べ替え N 通りで候補の id ごとに平均した物。対の 2 つは同じ提示の並び",
    "comply_diff": "P(応じる | 呼びかけあり) − P(応じる | なし)の対の平均",
    "jsd": "あり・なしの分布の JSD(底 2・0〜1・judge.jsd)の対の平均",
    "top1_change": "1 位の候補(同点は id の順)が、あり・なしで変わった対の割合",
    "violate_diff": "禁止の表示の場面だけ。P(破る | あり) − P(破る | なし)の対の平均(全体の行も禁止の表示の対の平均)",
    "human": "人の値は頼みありの応じた率だけ(呼びかけの無い条件は研究に無い=応じる確率(なし)の人の値は無い)",
    "contrasts": "頼み=同じ場面の中の理由と大きさの差(ある版どうし)・禁止の表示=掲示ありの周りの様子の差(Keizer の形)・"
                 "店頭の呼びかけ=強さの段の差と幅(場面ごとの最大 − 最小)。どれも場面の平均",
})
LIMITS: Final[tuple[str, ...]] = (
    "場面は自前(架空の店と人・実在の店名と施設名と地名と人名を使わない)=人の研究と条件が違う(場面ごとの違いは記録の README)",
    "人の値は記録 2-54 のものだけ(Langer ら 1978 の率・Keizer ら 2008 は向きの見込みだけ)=記録 2-54 の文の値(Langer ら 1978 は答申での一次確認なし=R-149 の追補 1 から 11-21 の決定で外し、追補 3 でも原典を読めなかった)",
    "人の値は人の割合、当て口の値は 1 回の判断の確率の平均=同じ量と読むのは住民が分布から引くと見なすとき",
    "出どころの印は今の印から「命令文除去(済)」を外した形・前置きの印の説明の行も自前=返事その 8 §5 の案が決まったら作り直す",
    "強さ 3 段の命令と今すぐは店の言葉としては不自然(記録 2-62 の段をそのまま当てた)",
    "条件ごとの呼びかけの文は 1 通りだけ(言い回しの揺れを見ていない)・場面は種類ごとに 3〜4 だけ",
    "同じ場面の行は同じ提示の並び(場面 11 通り)=PBS の帰無の床(行が独立の模擬)は狭めに出る・位置の偏りの列は参考",
    "テープ(8B の記録)は無い=テープの列は「基準の記録なし」・8B との比べは (G) の口(GPU の後)",
    "言語は日本語だけ・住人の第一言語の欄は空欄(§4-8)",
)
BLANKS: Final[Mapping[str, str]] = MappingProxyType({
    "plan": "近い予定=場面に無い(B6 事情の 1 行だけ)",
    "experience:memory": "記憶は B6 事情の 1 行だけ(場面によって無し)",
    "tape": "8B の記録が無い(GPU の後に (G) で埋める)",
})
FOOTNOTES: Final[tuple[str, ...]] = (
    "呼びかけの列: 分布は並べ替えの平均・対の 2 つは同じ提示の並び。種類ごと・条件ごと・対比と人の値は appeal_table.md",
    "mock は場面の id ごとに別の乱数で引く=呼びかけの列は無意味(文を読まない)。古典は文を読まず対の事実が同じ=構成上 0",
    "呼びかけの場面は同じ場面の行が同じ提示の並び(11 通り)=PBS の帰無の床(53 行が独立の模擬)は狭めに出る",
)


# ---------------------------------------------------------------------------------------------- 対
@dataclass(frozen=True)
class Pair:
    """呼びかけの対(ある版の id・同じ組のない版の id と印)。"""

    with_sid: str
    without_sid: str
    type: str
    setting: str
    family: str
    condition: str
    size: str | None
    reason: str | None
    env: str | None
    strength: str | None
    level: int | None
    comply: str
    violate: str | None
    baseline: str

    @property
    def key(self) -> str:
        """条件の鍵(``type/condition``)。"""
        return f"{self.type}/{self.condition}"


def _sig(cands: Sequence[Candidate]) -> tuple[tuple[str, str, str, str], ...]:
    return tuple((c.id, c.kind, c.text, c.source) for c in cands)


def _check_meta(sid: str, m: Mapping[str, Any], ids: set[str]) -> None:
    bad = sorted(set(m) - META_KEYS)
    if bad or set(m) != META_KEYS:
        raise ValueError(f"{sid}: 欄 appeal の鍵が違う(余り {bad}・足りない {sorted(META_KEYS - set(m))})")
    t = m["type"]
    if t not in TYPES:
        raise ValueError(f"{sid}: 種類 {t!r} は {TYPES} のどれか")
    for k in ("comply", "baseline"):
        if m[k] not in ids:
            raise ValueError(f"{sid}: {k} の候補 {m[k]!r} が候補に無い")
    if m["comply"] == m["baseline"]:
        raise ValueError(f"{sid}: 応じる候補と何もしない候補が同じ")
    if t == "prohibition":
        if m["violate"] not in ids or m["violate"] in (m["comply"], m["baseline"]):
            raise ValueError(f"{sid}: 禁止の表示の場面は破る候補 violate が要る(応じる・何もしないと別)")
        if m["env"] not in ENVS:
            raise ValueError(f"{sid}: 周りの様子 {m['env']!r} は {ENVS} のどれか")
    elif m["violate"] is not None:
        raise ValueError(f"{sid}: 破る候補は禁止の表示の場面だけ")
    if not isinstance(m["present"], bool):
        raise ValueError(f"{sid}: present は真偽")
    if not m["present"]:
        if m["condition"] is not None or m["body"] is not None:
            raise ValueError(f"{sid}: ない版に条件か呼びかけの文がある")
        return
    if not m["body"] or not m["channel"] or not m["line"]:
        raise ValueError(f"{sid}: ある版に呼びかけの文・出どころ・行が要る")
    if t == "request":
        ok = m["size"] in SIZES and m["reason"] in REASONS and m["condition"] == f"{m['size']}/{m['reason']}"
    elif t == "prohibition":
        ok = m["condition"] == m["env"]
    else:
        ok = (m["strength"] in STRENGTHS and m["condition"] == m["strength"]
              and m["level"] == STRENGTHS.index(m["strength"]) + 1)
    if not ok:
        raise ValueError(f"{sid}: 条件の欄が種類 {t} の形と違う")


def pairs_of(scenes: S.SceneSet) -> tuple[Pair, ...]:
    """場面の組 → 対(並びは場面のファイルの並び)。欄の形・組の作り(ない版 1 つ・ある版 1 つ以上)・同じ候補を検査する。"""
    meta = scenes.appeal
    sids = [s.sid for s in scenes.situations]
    missing = [sid for sid in sids if sid not in meta]
    if missing:
        raise ValueError(f"欄 appeal の無い場面: {missing[:5]}")
    families: dict[str, list[str]] = {}
    settings: dict[str, tuple[Any, ...]] = {}
    for sid in sids:  # 逐次ループ宣言: 場面の数
        m = meta[sid]
        _check_meta(sid, m, {c.id for c in scenes.candidates[sid]})
        if scenes.points[sid] != m["type"]:
            raise ValueError(f"{sid}: 判断点 {scenes.points[sid]!r} と種類 {m['type']!r} が違う")
        fixed = (m["type"], m["comply"], m["violate"], m["baseline"], _sig(scenes.candidates[sid]))
        if settings.setdefault(str(m["setting"]), fixed) != fixed:
            raise ValueError(f"{sid}: 同じ場面 {m['setting']!r} の行で候補か印が違う")
        families.setdefault(str(m["family"]), []).append(sid)
    out: list[Pair] = []
    for fam, members in families.items():
        absent = [x for x in members if not meta[x]["present"]]
        if len(absent) != 1 or len(members) < 2:
            raise ValueError(f"組 {fam!r}: ない版がちょうど 1 つ・ある版が 1 つ以上要る")
        base = absent[0]
        if len({str(meta[x]["setting"]) for x in members}) != 1 or len({meta[x]["env"] for x in members}) != 1:
            raise ValueError(f"組 {fam!r}: 場面と周りの様子は組の中で同じ")
        for x in members:
            if x == base:
                continue
            m = meta[x]
            out.append(Pair(with_sid=x, without_sid=base, type=str(m["type"]), setting=str(m["setting"]), family=fam,
                            condition=str(m["condition"]), size=m["size"], reason=m["reason"], env=m["env"],
                            strength=m["strength"], level=m["level"], comply=str(m["comply"]),
                            violate=m["violate"], baseline=str(m["baseline"])))
    return tuple(out)


def order_keys(scenes: S.SceneSet) -> dict[str, str]:
    """状況の id → 提示の並びの鍵(同じ場面の行=同じ候補は同じ並び=対の 2 つと周りの様子の対比を同じ提示で比べる)。"""
    return {sid: f"appeal|{m['type']}|{m['setting']}" for sid, m in scenes.appeal.items()}


def scenes_summary(pairs: Sequence[Pair], scenes: S.SceneSet) -> dict[str, Any]:
    """場面の組の数(行・対・場面=種類ごと・条件ごとの対の数)。中身の文は写さない。"""
    by_type: dict[str, dict[str, int]] = {}
    for t in TYPES:
        rows = [sid for sid in scenes.appeal if scenes.appeal[sid]["type"] == t]
        by_type[t] = {"rows": len(rows), "pairs": sum(1 for p in pairs if p.type == t),
                      "settings": len({scenes.appeal[sid]["setting"] for sid in rows})}
    return {"n_rows": len(scenes.situations), "n_pairs": len(pairs), "by_type": by_type,
            "by_condition": {k: sum(1 for p in pairs if p.key == k) for k in condition_keys(pairs)}}


# ---------------------------------------------------------------------------------------------- 測り
def mean_dist(records: Sequence[tuple[Sequence[Candidate], Mapping[str, float]]]) -> dict[str, float]:
    """並べ替え N 通りの分布(``bias.score_orders`` の 1 状況の記録)→ 候補の id ごとの平均(鍵の順)。"""
    acc: dict[str, float] = {}
    for _pres, d in records:
        for k, v in d.items():
            acc[k] = acc.get(k, 0.0) + float(v)
    n = len(records)
    return {k: acc[k] / n for k in sorted(acc)} if n else {}


def pair_values(pair: Pair, d_with: Mapping[str, float], d_without: Mapping[str, float]) -> dict[str, Any]:
    """1 つの対の値(応じる確率・差・JSD・1 位が変わったか・禁止の表示は破る確率)。"""
    cw, cn = float(d_with.get(pair.comply, 0.0)), float(d_without.get(pair.comply, 0.0))
    out: dict[str, Any] = {"comply_with": cw, "comply_without": cn, "comply_diff": cw - cn,
                           "jsd": J.jsd(d_with, d_without), "top1_changed": J.top1(d_with) != J.top1(d_without)}
    if pair.violate is not None:
        vw, vn = float(d_with.get(pair.violate, 0.0)), float(d_without.get(pair.violate, 0.0))
        out.update({"violate_with": vw, "violate_without": vn, "violate_diff": vw - vn})
    return out


def _mean(xs: Sequence[float]) -> float | None:
    return (sum(xs) / len(xs)) if xs else None


def group_stats(values: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """対の値の束 → 平均(対の数・応じる確率のあり/なし/差・JSD・1 位が変わった率・破る確率の差)。"""
    vio = [v for v in values if "violate_diff" in v]
    return {"n_pairs": len(values),
            "comply_with_mean": _mean([v["comply_with"] for v in values]),
            "comply_without_mean": _mean([v["comply_without"] for v in values]),
            "comply_diff_mean": _mean([v["comply_diff"] for v in values]),
            "jsd_mean": _mean([v["jsd"] for v in values]),
            "top1_change_rate": _mean([1.0 if v["top1_changed"] else 0.0 for v in values]),
            "violate_diff_mean": _mean([v["violate_diff"] for v in vio]) if vio else None}


def condition_keys(pairs: Sequence[Pair]) -> list[str]:
    """条件の鍵の並び(種類 → 大きさ → 理由 / 周りの様子 / 強さの順・対にある物だけ)。"""
    canon = ([f"request/{s}/{r}" for s in SIZES for r in REASONS] + [f"prohibition/{e}" for e in ENVS]
             + [f"shop_call/{k}" for k in STRENGTHS])
    have = {p.key for p in pairs}
    return [k for k in canon if k in have]


def _contrast(diffs: Sequence[float]) -> dict[str, Any]:
    return {"value": _mean(diffs), "n_settings": len(diffs)}


def contrasts_of(dists: Mapping[str, Mapping[str, float]], pairs: Sequence[Pair]) -> dict[str, dict[str, Any]]:
    """対比(場面の平均)。頼み=理由の差・大きさの差・禁止の表示=周りの様子の差・店頭の呼びかけ=強さの段の差と幅。"""
    def c(sid: str, cid: str) -> float | None:
        return float(dists[sid].get(cid, 0.0)) if sid in dists else None

    out: dict[str, dict[str, Any]] = {}
    req: dict[tuple[str, str, str], float] = {}
    pro: dict[tuple[str, str, str], float] = {}
    vio: dict[tuple[str, str], float] = {}
    shop: dict[tuple[str, str], float] = {}
    for p in pairs:  # 逐次ループ宣言: 対の数
        cw = c(p.with_sid, p.comply)
        if p.type == "request" and cw is not None:
            req[(p.setting, str(p.size), str(p.reason))] = cw
        elif p.type == "prohibition":
            cn = c(p.without_sid, p.comply)
            if cw is not None:
                pro[(p.setting, str(p.env), "sign")] = cw
                vio[(p.setting, str(p.env))] = float(dists[p.with_sid].get(str(p.violate), 0.0))
            if cn is not None:
                pro[(p.setting, str(p.env), "nosign")] = cn
        elif p.type == "shop_call" and cw is not None:
            shop[(p.setting, str(p.strength))] = cw
    rs = sorted({k[0] for k in req})
    if rs:
        for size in SIZES:
            for a, b in (("placebic", "none"), ("real", "none"), ("real", "placebic")):
                out[f"request/{size}/{a}_minus_{b}"] = _contrast(
                    [req[(s, size, a)] - req[(s, size, b)] for s in rs if (s, size, a) in req and (s, size, b) in req])
        for reason in REASONS:
            out[f"request/{reason}/small_minus_large"] = _contrast(
                [req[(s, "small", reason)] - req[(s, "large", reason)] for s in rs
                 if (s, "small", reason) in req and (s, "large", reason) in req])
    ps = sorted({k[0] for k in pro})
    if ps:
        for kind in ("sign", "nosign"):
            out[f"prohibition/{kind}/orderly_minus_disorderly"] = _contrast(
                [pro[(s, "orderly", kind)] - pro[(s, "disorderly", kind)] for s in ps
                 if (s, "orderly", kind) in pro and (s, "disorderly", kind) in pro])
        out["prohibition/sign/violate_disorderly_minus_orderly"] = _contrast(
            [vio[(s, "disorderly")] - vio[(s, "orderly")] for s in ps
             if (s, "disorderly") in vio and (s, "orderly") in vio])
    ss = sorted({k[0] for k in shop})
    if ss:
        for a, b in (("command", "please"), ("now", "command"), ("now", "please")):
            out[f"shop_call/{a}_minus_{b}"] = _contrast(
                [shop[(s, a)] - shop[(s, b)] for s in ss if (s, a) in shop and (s, b) in shop])
        full = [s for s in ss if all((s, k) in shop for k in STRENGTHS)]
        out["shop_call/strength_range"] = _contrast(
            [max(shop[(s, k)] for k in STRENGTHS) - min(shop[(s, k)] for k in STRENGTHS) for s in full])
    return out


def measures(dists: Mapping[str, Mapping[str, float]], pairs: Sequence[Pair]) -> dict[str, Any]:
    """状況の id → 分布(並べ替えの平均)→ 全体・種類ごと・条件ごとの値と対比。片方が採点から外れた対は数えない。"""
    vals: list[tuple[Pair, dict[str, Any]]] = []
    skipped = 0
    for p in pairs:  # 逐次ループ宣言: 対の数
        if p.with_sid in dists and p.without_sid in dists:
            vals.append((p, pair_values(p, dists[p.with_sid], dists[p.without_sid])))
        else:
            skipped += 1
    types = [t for t in TYPES if any(p.type == t for p in pairs)]
    return {"n_pairs": len(vals), "n_pairs_skipped": skipped,
            "overall": group_stats([v for _p, v in vals]),
            "by_type": {t: group_stats([v for p, v in vals if p.type == t]) for t in types},
            "by_condition": {k: group_stats([v for p, v in vals if p.key == k]) for k in condition_keys(pairs)},
            "contrasts": contrasts_of(dists, pairs)}


def dists_of(records: Mapping[str, Sequence[tuple[Sequence[Candidate], Mapping[str, float]]]]
             ) -> dict[str, dict[str, float]]:
    """``bias.score_orders`` の記録 → 状況の id → 並べ替えの平均の分布。"""
    return {sid: mean_dist(recs) for sid, recs in records.items()}


# ---------------------------------------------------------------------------------------------- 対照
class AppealFollowControl(J.Scorer):
    """正の対照: 文に出どころの印(呼びかけの行)があれば「応じる」候補に確率 1、無ければ「何もしない」候補に確率 1。

    文を読む(印を探す)=描画の道筋を通る。応じる候補の id は場面の印から(作るときに渡す)。モデルの測りではない。
    """

    name = "appeal_follow"
    role = J.ROLE_CONTROL
    reads_text = True

    def __init__(self, targets: Mapping[str, tuple[str, str]]) -> None:
        self.targets = MappingProxyType(dict(targets))
        self.meta = MappingProxyType({"rule": "文に出どころの印があれば応じる候補に 1・無ければ何もしない候補に 1",
                                      "markers": MARKERS, "use": "列の計算の確かめ(正の対照)"})
        super().__init__()

    def _score(self, situation: S.Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        if text is None:
            raise ValueError("文の要る当て口")
        comply, base = self.targets[situation.sid]
        return {comply if any(m in text for m in MARKERS) else base: 1.0}


class AppealIgnoreControl(J.Scorer):
    """負の対照: いつも「何もしない」候補に確率 1(呼びかけを見ない)。"""

    name = "appeal_ignore"
    role = J.ROLE_CONTROL

    def __init__(self, targets: Mapping[str, tuple[str, str]]) -> None:
        self.targets = MappingProxyType(dict(targets))
        self.meta = MappingProxyType({"rule": "いつも何もしない候補に 1", "use": "列の計算の確かめ(負の対照)"})
        super().__init__()

    def _score(self, situation: S.Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        return {self.targets[situation.sid][1]: 1.0}


def targets_of(pairs: Sequence[Pair]) -> dict[str, tuple[str, str]]:
    """状況の id → (応じる候補・何もしない候補)。"""
    out: dict[str, tuple[str, str]] = {}
    for p in pairs:
        out[p.with_sid] = (p.comply, p.baseline)
        out[p.without_sid] = (p.comply, p.baseline)
    return out


def default_controls(pairs: Sequence[Pair]) -> tuple[J.Scorer, ...]:
    """記録に載せる対照(正・負)。"""
    t = targets_of(pairs)
    return (AppealFollowControl(t), AppealIgnoreControl(t))


# ---------------------------------------------------------------------------------------------- 節
def section(entries: Sequence[tuple[Mapping[str, Any], bool, Mapping[str, Mapping[str, Any]] | None]], *,
            arms: Sequence[str], pairs: Sequence[Pair], summary: Mapping[str, Any],
            controls: Mapping[str, tuple[Mapping[str, Any], Mapping[str, Any]]]) -> dict[str, Any]:
    """呼びかけの節。``entries`` は当て口ごとの(describe・文を読むか・腕 → 状況 → 並べ替えの記録 / 口だけは None)。
    ``controls`` は対照の名 → (describe・状況 → 並べ替えの記録)(腕は ``arms[0]``)。"""
    scorers: dict[str, Any] = {}
    for desc, reads_text, by_arm in entries:
        name = str(desc["name"])
        if by_arm is None:
            scorers[name] = {"status": "GPU の後(S6)", "role": desc["role"], "reads_text": bool(reads_text),
                             "by_arm": {arm: None for arm in arms}}
            continue
        scorers[name] = {"status": "検査済み", "role": desc["role"], "reads_text": bool(reads_text),
                         "by_arm": {arm: measures(dists_of(by_arm[arm]), pairs) for arm in arms}}
    ctl = {name: {"describe": dict(desc), "arm": arms[0], "measures": measures(dists_of(recs), pairs)}
           for name, (desc, recs) in controls.items()}
    return {"schema": APPEAL_SCHEMA, "scenes": dict(summary), "definitions": dict(DEFINITIONS),
            "human": {"status": HUMAN_STATUS, "conditions": {k: dict(v) for k, v in HUMAN_CONDITIONS.items()},
                      "contrasts": {k: dict(v) for k, v in HUMAN_CONTRASTS.items()}},
            "scorers": scorers, "controls": ctl, "limits": list(LIMITS)}


def summary_table(sec: Mapping[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    """表の末尾の 3 列(当て口 → 腕 → 列)=全体の値。"""
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for name, e in sec["scorers"].items():
        out[name] = {}
        for arm, m in e["by_arm"].items():
            o = (m or {}).get("overall") or {}
            out[name][arm] = {"appeal_comply_diff": o.get("comply_diff_mean"), "appeal_jsd": o.get("jsd_mean"),
                              "appeal_top1_change": o.get("top1_change_rate")}
    return out


# ---------------------------------------------------------------------------------------------- 表(種類・条件・対比)
BREAKDOWN_COLUMNS: Final[tuple[tuple[str, str], ...]] = (
    ("scorer", "当て口"), ("role", "役割"), ("arm", "長さの腕"), ("group", "組"), ("n_pairs", "対の数"),
    ("comply_with", "応じる確率(あり)"), ("comply_without", "応じる確率(なし)"),
    ("comply_diff", "応じる確率の差(あり − なし)"), ("jsd", "分布の差 JSD"), ("top1_change", "1 位が変わった対の率"),
    ("violate_diff", "破る確率の差(あり − なし)"), ("human", "人の値(応じた率・あり)"),
    ("human_source", "人の値の出どころ"), ("human_status", "人の値の状態"), ("notes", "注"),
)
CONTRAST_COLUMNS: Final[tuple[tuple[str, str], ...]] = (
    ("scorer", "当て口"), ("arm", "長さの腕"), ("contrast", "対比"), ("n_settings", "場面の数"), ("value", "値"),
    ("human", "人の値"), ("human_source", "人の値の出どころ"), ("human_status", "人の値の状態"),
)
BLANK_NOT_PROHIBITION: Final[str] = "該当なし(禁止の表示の場面だけ)"
BLANK_NO_HUMAN: Final[str] = "該当なし(人の値なし)"


def group_word(key: str) -> str:
    """組の鍵 → 見出し(``all``・種類・``type/条件``)。"""
    if key == "all":
        return "全体"
    if key in S.APPEAL_TYPES:
        return f"{key}({S.APPEAL_TYPES[key]})"
    parts = key.split("/")
    if parts[0] == "request" and len(parts) == 3:
        return f"{key}({SIZE_WORDS[parts[1]]}・{REASON_WORDS[parts[2]]})"
    if parts[0] == "prohibition":
        return f"{key}(掲示・{ENV_WORDS[parts[1]]})"
    return f"{key}({STRENGTH_WORDS[parts[1]]})"


def _human_cells(key: str) -> tuple[Any, str, str]:
    """組の鍵 → (人の値の文 / None・出どころ・状態か空の理由)。"""
    h = HUMAN_CONDITIONS.get(key)
    if h is not None:
        return (h["text"], h["source"], h["status"] if h["text"] is not None else f"{h['blank']}・{h['status']}")
    t = key.split("/")[0]
    if key == "all":
        return None, HUMAN_NONE["overall"], ""
    return None, HUMAN_NONE.get(t, HUMAN_NONE["overall"]), ""


def _stat_row(base: Mapping[str, Any], key: str, st: Mapping[str, Any] | None) -> dict[str, Any]:
    st = st or {}
    text, src, status = _human_cells(key)
    return {**base, "group": group_word(key), "n_pairs": st.get("n_pairs"),
            "comply_with": st.get("comply_with_mean"), "comply_without": st.get("comply_without_mean"),
            "comply_diff": st.get("comply_diff_mean"), "jsd": st.get("jsd_mean"),
            "top1_change": st.get("top1_change_rate"), "violate_diff": st.get("violate_diff_mean"),
            "human": text, "human_source": src, "human_status": status}


def _measure_rows(base: Mapping[str, Any], m: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = [_stat_row(base, "all", m["overall"])]
    rows += [_stat_row(base, t, st) for t, st in m["by_type"].items()]
    rows += [_stat_row(base, k, st) for k, st in m["by_condition"].items()]
    return rows


def breakdown_rows(sec: Mapping[str, Any]) -> list[dict[str, Any]]:
    """種類・条件ごとの表の行(当て口の宣言の順 → 対照)。文を読まない当て口は最初の腕だけ(腕で変わらない)。"""
    rows: list[dict[str, Any]] = []
    for name, e in sec["scorers"].items():
        arms = list(e["by_arm"])
        role = J.ROLE_WORDS.get(e["role"], e["role"])
        if e["status"] != "検査済み":
            for arm in arms:
                rows.append({**_stat_row({"scorer": name, "role": role, "arm": arm, "notes": "口だけ=GPU の後(S6)"},
                                         "all", None), "_gpu": True})
            continue
        use = arms if e["reads_text"] else arms[:1]
        note = None if e["reads_text"] else f"文を読まない=腕 {'・'.join(arms[1:])} も同じ"
        for arm in use:
            rows += _measure_rows({"scorer": name, "role": role, "arm": arm, "notes": note}, e["by_arm"][arm])
    for name, c in sec["controls"].items():
        rows += _measure_rows({"scorer": name, "role": J.ROLE_WORDS[J.ROLE_CONTROL], "arm": c["arm"],
                               "notes": "列の計算の確かめ(モデルの測りではない)"}, c["measures"])
    return rows


def contrast_rows(sec: Mapping[str, Any]) -> list[dict[str, Any]]:
    """対比の表の行(採点した当て口と対照だけ)。"""
    rows: list[dict[str, Any]] = []

    def add(name: str, arm: str, m: Mapping[str, Any]) -> None:
        for k, v in m["contrasts"].items():
            h = HUMAN_CONTRASTS.get(k)
            if h is None:
                t = k.split("/")[0]
                human, src, status = None, ("人の値なし(研究に無い条件)" if "nosign" in k
                                            else HUMAN_NONE.get(t, HUMAN_NONE["overall"])), ""
            else:
                human, src = h["text"], h["source"]
                status = h["status"] if h["low"] is not None else f"{h['blank']}・{h['status']}"
            rows.append({"scorer": name, "arm": arm, "contrast": k, "n_settings": v["n_settings"], "value": v["value"],
                         "human": human, "human_source": src, "human_status": status})

    for name, e in sec["scorers"].items():
        if e["status"] != "検査済み":
            continue
        for arm in (list(e["by_arm"]) if e["reads_text"] else list(e["by_arm"])[:1]):
            add(name, arm, e["by_arm"][arm])
    for name, c in sec["controls"].items():
        add(name, c["arm"], c["measures"])
    return rows


def _blank(row: Mapping[str, Any], key: str) -> str:
    """空の欄の印(人の値なし・口だけ=GPU の後・禁止の表示の場面だけの列・採点できた対が無い)。"""
    if key == "notes":
        return ""
    if key == "human":
        return BLANK_NO_HUMAN
    if row.get("_gpu"):
        return BLANK_GPU
    if key == "violate_diff" and not str(row.get("group", "")).startswith(("prohibition", "全体")):
        return BLANK_NOT_PROHIBITION
    return BLANK_NO_PAIR


def _cell(row: Mapping[str, Any], key: str) -> str:
    v = row.get(key)
    if v is None:
        return _blank(row, key)
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v).replace("|", "/")


def _md_table(cols: Sequence[tuple[str, str]], rows: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = ["| " + " | ".join(h for _k, h in cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(_cell(r, k) for k, _h in cols) + " |")
    return lines


def to_markdown(sec: Mapping[str, Any]) -> str:
    """呼びかけの表(種類・条件ごと → 対比 → 定義と限界)。"""
    lines = ["# 呼びかけへの反応のずれ(dm_eval・呼びかけの場面)", "",
             f"- 場面 {sec['scenes']['n_rows']} 行・対 {sec['scenes']['n_pairs']}。人の値の状態: {sec['human']['status']}",
             "- 並びは当て口の宣言の順(対照 → 基準 → 候補)→ 呼びかけの対照。順位は付けない", "",
             "## 種類・条件ごと", ""]
    lines += _md_table(BREAKDOWN_COLUMNS, breakdown_rows(sec))
    lines += ["", "## 対比(場面の平均)", ""]
    lines += _md_table(CONTRAST_COLUMNS, contrast_rows(sec))
    lines += ["", "## 定義", ""]
    lines += [f"- {k}: {v}" for k, v in sec["definitions"].items()]
    lines += ["", "## 限界", ""]
    lines += [f"- {x}" for x in sec["limits"]]
    return "\n".join(lines) + "\n"


def to_json(sec: Mapping[str, Any]) -> str:
    """呼びかけの表(JSON)。行の空の欄は印の文で ``blank`` に。"""
    def blanks(rows: Sequence[Mapping[str, Any]], cols: Sequence[tuple[str, str]]) -> list[dict[str, str]]:
        return [{k: _blank(r, k) for k, _h in cols if k != "notes" and r.get(k) is None} for r in rows]

    br = breakdown_rows(sec)
    cr = contrast_rows(sec)
    doc = {"schema": APPEAL_SCHEMA,
           "breakdown": {"columns": [{"key": k, "header": h} for k, h in BREAKDOWN_COLUMNS],
                         "rows": [{k: r.get(k) for k, _h in BREAKDOWN_COLUMNS} for r in br],
                         "blank": blanks(br, BREAKDOWN_COLUMNS)},
           "contrasts": {"columns": [{"key": k, "header": h} for k, h in CONTRAST_COLUMNS],
                         "rows": [{k: r.get(k) for k, _h in CONTRAST_COLUMNS} for r in cr],
                         "blank": blanks(cr, CONTRAST_COLUMNS)},
           "definitions": dict(sec["definitions"]), "limits": list(sec["limits"])}
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
