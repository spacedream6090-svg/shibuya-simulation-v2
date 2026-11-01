"""engine.experiment.checks — 申込書の点検(第 3 期 3-3b・CP5-1 の「始まり 0 の予期しない改変」・CP5-3 の名指しと混入の疑い)。

決定 10-12 §4-5 CP5-1・CP5-3・PENDING 仮-24(答申 R-117 §6-1)。どれも**警告と記録だけ**で、申込書を拒まない(仮-24)。

- **CP5-1 ``start0_check``**: 始まり 0(「最初から」)で改変があり、告知が無い(または申込書に ``unexpected: true``=予期しないと
  書いた)ものを見つけたら警告(``ExperimentWarning``)と記録(manifest の ``experiment.start0``)。理由は R-117 §6-1 の Müller ら
  2020: 最初から回してよいのは住人が始めから知っている改変だけで、予期しない出来事は途中から(T0 > 0)回す。「最初から」の
  ときの順番(改変を当ててから、ランの前の経験=通勤の経験・親しみ・記憶の初期の中身を作る)の口は第 4 期 4-1 段 6 の後=本段は
  宣言(``order``)と欄(``order_implemented=False``)だけ。
- **CP5-3 ``naming_hits``**(名指しの機械の検査=文に名が含まれるかを部分一致で探す 1 つの道具): ペルソナの文が改変した物を名指し
  していないか(``persona_naming``)と、申込書の自己申告の欄 ``known_to_model``(LLM が実在の出来事として知っている改変=実在の
  閉店・運賃の改定など)の語が文に出ていないか(``contamination``=混入の疑い)を、同じ道具で探す。見つけたら記録する(書き直すか
  比較から外すかは呼び手=人が決める)。コードに地名や業種名は書かない(名は呼び手が渡す)。

未リサーチ(expedient): 部分一致で探すこと(表記の揺れ・読みの違いは拾わない)・CP5-1 の旗の条件(告知の有無と自己申告の欄だけで
決める=告知の時刻と内容は見ない)。

逐次ループ宣言: 文の数 × 名の数(ランの外で 1 回)。
"""

from __future__ import annotations

import warnings
from typing import Any, Final, Iterable, Mapping

from shibuya.engine.experiment.form import ExperimentForm

__all__ = [
    "ExperimentWarning", "START0_SCHEMA", "START0_RULE", "START0_ORDER", "start0_check", "warn_start0",
    "naming_hits", "persona_naming", "contamination", "CONTAMINATION_SCHEMA",
]

START0_SCHEMA: Final[str] = "shibuya.engine.experiment/start0/1"
CONTAMINATION_SCHEMA: Final[str] = "shibuya.engine.experiment/contamination/1"
#: CP5-1 の点検の規則(manifest に写す文)。
START0_RULE: Final[str] = ("始まり 0 で改変があり、告知が無いか申込書に unexpected=true と書いた改変は警告と記録(拒まない)。"
                           "予期しない出来事は途中から(T0 > 0)回す(R-117 §6-1・Müller ら 2020)")
#: CP5-1 の「最初から」の順番(宣言だけ・口は第 4 期 4-1 段 6 の後)。
START0_ORDER: Final[str] = "改変を当ててから、ランの前の経験(通勤の経験・親しみ・記憶の初期の中身)を作る"


class ExperimentWarning(UserWarning):
    """申込書の点検の警告(拒まない=仮-24)。"""


def start0_check(form: ExperimentForm) -> dict[str, Any]:
    """CP5-1: 始まり 0 の予期しない改変の点検(manifest の ``experiment.start0``)。旗 ``warning`` は真偽・理由は文。"""
    zero = int(form.start) == 0
    changes = len(form.content) > 0
    notice = form.notice is not None
    unexpected = form.unexpected
    flag = bool(zero and changes and (not notice or unexpected is True))
    if not flag:
        reason = ""
    elif unexpected is True:
        reason = "始まり 0 の改変を申込書が予期しない(unexpected=true)と書いた=住人が前もって知ってしまう"
    else:
        reason = "始まり 0 の改変に告知が無い=予期しない出来事なら住人が前もって知ってしまう"
    return {"schema": START0_SCHEMA, "start_zero": zero, "changes": changes, "notice": notice,
            "unexpected": unexpected, "warning": flag, "reason": reason, "rule": START0_RULE,
            "order": START0_ORDER, "order_implemented": False}


def warn_start0(form: ExperimentForm) -> dict[str, Any]:
    """``start0_check`` の旗が立っていれば ``ExperimentWarning`` を出す(拒まない)。記録を返す。"""
    rec = start0_check(form)
    if rec["warning"]:
        warnings.warn(f"申込書の点検(CP5-1): {rec['reason']}。{START0_RULE}", ExperimentWarning, stacklevel=2)
    return rec


# ================================================================ CP5-3: 名指しの機械の検査(1 つの道具)
def _names(names: Iterable[str]) -> list[str]:
    out = sorted({str(n) for n in names if isinstance(n, str) and n.strip()})
    return out


def naming_hits(text: str, names: Iterable[str]) -> list[str]:
    """文 ``text`` に含まれる名(部分一致・昇順)。名の一覧は呼び手が渡す(コードに地名や業種名を書かない)。"""
    s = str(text)
    return [n for n in _names(names) if n in s]


def _scan(texts: Mapping[Any, str], names: Iterable[str]) -> list[dict[str, Any]]:
    ns = _names(names)
    rows = []
    for k in sorted(texts, key=lambda x: str(x)):  # 逐次ループ宣言: 文の数ぶん
        hits = naming_hits(texts[k], ns)
        if hits:
            rows.append({"id": k, "hits": hits})
    return rows


def persona_naming(texts: Mapping[Any, str], names: Iterable[str]) -> dict[str, Any]:
    """CP5-3: ペルソナの文(id → 文)が改変した物の名(``names``)を名指ししていないか。見つけた文と名の行を返す。"""
    ns = _names(names)
    rows = _scan(texts, ns)
    return {"schema": CONTAMINATION_SCHEMA, "check": "persona_naming", "names": ns, "texts": len(texts),
            "hits": rows, "found": bool(rows),
            "note": "見つけた文は書き直すか比較から外す(決めるのは呼び手)。部分一致=表記の揺れは拾わない(expedient)"}


def contamination(form: ExperimentForm, texts: Mapping[Any, str] | None = None) -> dict[str, Any]:
    """CP5-3: 混入の疑い(申込書の ``known_to_model``=LLM が実在の出来事として知っている改変の語の自己申告)。

    ``texts``(id → 文=ペルソナの文や描画した文)を渡すと、自己申告の語が文に出ているかを ``naming_hits`` で探す。
    渡さなければ宣言だけを記録する(``checked=False``)。自己申告が空なら ``declared`` は空=疑いの記録なし。
    """
    declared = list(form.known_to_model)
    if texts is None:
        return {"schema": CONTAMINATION_SCHEMA, "check": "known_to_model", "declared": declared, "checked": False,
                "texts": 0, "hits": [], "suspected": bool(declared),
                "note": "自己申告の語がある=LLM がその改変を実在の出来事として知っている疑い(比較の解釈に注記する)"}
    rows = _scan(texts, declared)
    return {"schema": CONTAMINATION_SCHEMA, "check": "known_to_model", "declared": declared, "checked": True,
            "texts": len(texts), "hits": rows, "suspected": bool(declared),
            "note": "自己申告の語が文に出た行=混入の疑いが文に現れた所(書き直すか比較から外すかは呼び手)"}
