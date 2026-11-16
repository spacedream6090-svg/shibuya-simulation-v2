"""試験の中だけの助け: 率の形の規則と「無い」と宣言した過程の旧道(部品の口)を、ランの組み立てに挿す(第347 止めた切替口の
削除・記録 ``docs/bench/analysis/switch-removal-347/README.md``)。

切替口 ``--rate-rules legacy``・``--absent-processes legacy``(と、旧道でだけ効く ``run_day(salient_rate_per_10k=…)``)を消した
後も、旧道の中身は部品の口(過程の引数 ``rate_rules="legacy"``・``absent_processes="legacy"``・``SalientProcess`` の
``rate_per_10k_per_day``・``WorldProcessRunner`` の ``salient_rate_per_10k``・``PlanExecutor`` の ``rate_rules``)として残る。
本モジュールは、ランの中で「倒れる → 出動 → 到着」やごみ・宅配・催しの行を起こして確かめる試験のために、組み立てが作る
実行器と計画実行層の初期化を包んで、その部品の口を挿す(第346 の検収 M2 で ``proximity.rule_from`` を試験の中で差し替えたのと
同じ形)。ランの口(CLI・環境変数・``run_day`` の引数・設定の箱の欄)には触らない。

注: 組み立てが読む腕(設定の箱の ``cfg.rate_rules``・``cfg.absent_processes``)は既定のままなので、manifest の
``rate_rules.mode``・``absent_processes.mode`` と状態のファイルの見出しは既定(off・stopped)を書き、計数(``counts``)だけが
旧道の件数を持つ。manifest の mode を見る試験には使わない。

逐次ループ宣言: なし。
"""

from __future__ import annotations

from typing import Any

__all__ = ["legacy_world_rules"]


def legacy_world_rules(mp: Any, *, rate: bool = True, absent: bool = True, salient_rate: float | None = None) -> None:
    """``mp``(``pytest.MonkeyPatch``)の間だけ、組み立てが作る実行器(と ``rate`` なら計画実行層)に旧道の部品の口を挿す。

    Args:
        rate: 率の形の規則の旧道(``rate_rules="legacy"``・実行器の 6 過程と計画実行層の E8)。
        absent: 「無い」と宣言した過程 5 件の旧道(``absent_processes="legacy"``)。
        salient_rate: 倒れる率[件/1 万体/日](``None``=部品の既定 3.0)。旧道の顕著行為の過程にだけ効く。
    """
    from shibuya.engine import presence as PE
    from shibuya.world.laws import runner as RN

    runner_init = RN.WorldProcessRunner.__init__

    def _runner_init(self: Any, *a: Any, **k: Any) -> None:
        if rate:
            k["rate_rules"] = "legacy"
        if absent:
            k["absent_processes"] = "legacy"
        if salient_rate is not None:
            k["salient_rate_per_10k"] = float(salient_rate)
        runner_init(self, *a, **k)

    mp.setattr(RN.WorldProcessRunner, "__init__", _runner_init)
    if rate:
        presence_init = PE.PlanExecutor.__init__

        def _presence_init(self: Any, *a: Any, **k: Any) -> None:
            k["rate_rules"] = "legacy"
            presence_init(self, *a, **k)

        mp.setattr(PE.PlanExecutor, "__init__", _presence_init)
