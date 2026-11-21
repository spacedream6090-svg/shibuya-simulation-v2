"""〔第347 止めた切替口の削除・案 s1〕旧のセルの移動(``legacy``)を試験の中だけで選ぶ助け。

切替口 ``--space legacy``(環境変数 ``SHIBUYA_SPACE``・``run_day(space="legacy")``・``cli.run(space="legacy")``)は消した=
ランの口からは選べない(返事その 8 §1-2 Q7 (d)・§1-10)。旧のセルの移動そのものは残っていて、組み立ては
``world.model.space.nav1`` の非公開の印 ``_LEGACY_FOR_TESTS`` が立っていれば legacy を選ぶ(manifest の ``space.requested`` と
``space.effective`` は legacy・``space.reason`` は試験の中だけの口の文)。本番の形で資産の無い段の世界(``v2_stage_2-3``・
``v2_stage_4-3``・``v2_pre_4-3``)も、この口なら止めずに回る(前の ``space="legacy"`` の頼み方と同じ道)。

ランの口(CLI・環境変数・``run_day`` の引数・設定の箱の欄)には触らない。印は ``monkeypatch`` で立てるので、試験が終われば戻る。
同じプロセスで ``cli.run`` を呼ぶ道具(md23 の ``run_collect`` ほか)にも届く。子のプロセスには届かない。
記録 ``docs/bench/analysis/switch-removal-347/README.md``。
"""

from __future__ import annotations

import pytest

from shibuya.world.model.space import nav1 as N


def legacy_space(mp: pytest.MonkeyPatch) -> None:
    """旧のセルの移動を選ぶ印を立てる(``mp`` が戻すまで)。"""
    mp.setattr(N, "_LEGACY_FOR_TESTS", True)
