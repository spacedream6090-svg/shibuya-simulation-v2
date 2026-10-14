"""engine.run_kind — ランの種類(第 1 期 1-4・決定 10-12 §4-5 CP5-5「ランの種類を manifest に記録」)。

種類は 4 つ(口の約束 1-4): ``reproduction``(再現)・``counterfactual``(反実仮想)・``arm``(腕)・``test``(試験)。
manifest の一番上の ``run_kind`` に載る(設定の節)。種類は記録だけで、ランの中身は変えない。決めていないラン
(``run_day`` を直に呼んだラン)は ``None``(manifest は null=「決めていない」)。

expedient: ランの種類は ``cli.run`` の引数から決める 1 つの規則=試験(pytest の中)なら ``test``・CLI の既定と違う腕の
引数を 1 つでも渡したら ``arm``・ほかは ``reproduction``(``decide``)。腕かどうかは ``cli.NON_ARM_RUN_KWARGS`` の外の
引数が ``cli.arm_baseline``(``run_day`` の既定+CLI の既定)と違うか(``cli.run_arms``)。``cli.main`` も同じ決め方。
反実仮想は 3-3 の申込書で決める(今の規則は ``counterfactual`` を返さない)。``run_day`` を直に呼ぶランは決めない。

〔第 1 期 1-8b〕``cli.run`` の引数でない腕のうち、結果を変える腕も ``arm`` に数える: 発話の口 ``--speech-port on``(環境変数
``SHIBUYA_SPEECH_PORT=on`` でも同じ=組み立てが読む腕・設定の指紋にも on のときだけ入る)。結果を変えない腕(1-8 J0 の
``--decision-port port``・1-6 の ``--memory-store events``)は数えない。

逐次ループ宣言: なし。
"""

from __future__ import annotations

import os
from typing import Final

__all__ = [
    "RUN_KINDS", "REPRODUCTION", "COUNTERFACTUAL", "ARM", "TEST", "PYTEST_ENV", "in_test", "decide", "check",
    "resolve",
]

REPRODUCTION: Final[str] = "reproduction"
COUNTERFACTUAL: Final[str] = "counterfactual"
ARM: Final[str] = "arm"
TEST: Final[str] = "test"
RUN_KINDS: Final[tuple[str, ...]] = (REPRODUCTION, COUNTERFACTUAL, ARM, TEST)
#: pytest が試験の間だけ立てる環境変数(子のプロセスにも引き継がれる=試験から起こしたランも ``test``)。
PYTEST_ENV: Final[str] = "PYTEST_CURRENT_TEST"


def in_test() -> bool:
    """pytest の試験の中か(``PYTEST_CURRENT_TEST`` が立っているか)。"""
    return bool(os.environ.get(PYTEST_ENV))


def decide(*, arms_on: bool, testing: bool | None = None) -> str:
    """``cli.run`` の規則: 試験 > 腕 > 再現 の順。``testing`` を省くと ``in_test()``。"""
    if in_test() if testing is None else testing:
        return TEST
    return ARM if arms_on else REPRODUCTION


def check(kind: str) -> str:
    """種類の名の検査(4 つの外は ``ValueError``)。"""
    if kind not in RUN_KINDS:
        raise ValueError(f"run_kind は {RUN_KINDS}(いま {kind!r})")
    return kind


def resolve(kind: str | None) -> str | None:
    """manifest に書く種類(``None``=決めていない=null のまま)。"""
    return None if kind is None else check(kind)
