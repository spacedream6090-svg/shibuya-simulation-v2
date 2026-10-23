"""第 6 期 6-6 ② 第 1 部 店の仕事の試験の共通(腕の切替・合成の世界=店・担当・雇用の行・店の決まり=営業時間の表・物の台帳・
判断の差し替え)。

合成の世界: ``World.synthetic(n_cells=1)``=店 2 つ・体は全員同じセル(担当はいつも店に居る=寝ているときと主の判断の刻みは候補が
出ない)。店の担当は今の丸振りから店 0 を外した(担当の居ない店 ``UN``=エンジンのつなぎ・担当の居る店 ``ST``=店 1=朝に起きて
いる担当・廃棄率のある棚)。店の決まり=どの曜日も 9:00〜21:00
(``RULE_FROM``・``RULE_TO``)。物の台帳は ``cli.build_ledger_bundle``(棚・バックヤード・廃棄)。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np

from shibuya.core.time_consts import MINUTES_PER_HOUR, NS_PER_SECOND, STEP_SECONDS, STEPS_PER_DAY
from shibuya.engine.duties import arm as AD
from shibuya.engine.duties import port as PD

STEP_NS = STEP_SECONDS * NS_PER_SECOND
TPD = int(STEPS_PER_DAY)
#: 店の決まり(営業時間)の既定(どの曜日も同じ)。
RULE_FROM = 9 * MINUTES_PER_HOUR
RULE_TO = 21 * MINUTES_PER_HOUR
N = 80
#: 担当の居る店・担当の居ない店(既定の世界)。
ST, UN = 1, 0
#: 合成の世界の小さなラン(活動層なし・記憶あり・関係なし)。
KW = dict(n_agents=N, seed=1, n_cells=1, ticks=TPD, budget=float(N), sleep_suppression=False, vocab_version="v3",
          memory="on", relations="off", store_memory="off", activity="off", checkpoint_every=60)


def plan_assets(n_poi: int, start: int = RULE_FROM, end: int = RULE_TO, *, per_poi: dict[int, tuple[int, int]] | None = None,
                src: dict[int, str] | None = None):
    """店の決まり(W7 の形の営業時間の表)。曜日 0〜6 と祝日の行(7)に同じ区間。``per_poi`` で店ごとに替えられる。``src`` は
    〔検収 M3〕店ごとの出どころ(W7 の列 src の形=``ProcessAssets.plan_src_names``・``plan_poi_src``)。"""
    from shibuya.world.assets import ProcessAssets

    rows = []
    for p in range(int(n_poi)):
        s, e = (per_poi or {}).get(p, (start, end))
        for d in range(8):
            rows.append((p, d, s, e))
    arr = np.asarray(rows, dtype=np.int64)
    names: tuple[str, ...] = ()
    codes = None
    if src:
        names = tuple(sorted(set(src.values())))
        codes = np.full(int(n_poi), -1, dtype=np.int16)
        for p, s in src.items():
            codes[int(p)] = names.index(s)
    return ProcessAssets(source="test", plan_poi=arr[:, 0].astype(np.int32), plan_day=arr[:, 1].astype(np.int8),
                         plan_start=arr[:, 2].astype(np.int32), plan_end=arr[:, 3].astype(np.int32),
                         plan_src_names=names, plan_poi_src=codes)


def world_fixture(monkeypatch: Any, *, n_cells: int = 1, unstaffed: int = UN,
                  per_poi: dict[int, tuple[int, int]] | None = None, endow: bool = True,
                  src: dict[int, str] | None = None, w21c: list[tuple[int, int]] | None = None) -> dict[str, Any]:
    """合成の世界・物の台帳・店の決まりを組み立ての口に入れる(``run_day(**kw, **extra)`` の ``extra`` を返す)。店の担当は今の
    丸振りから、番号の偶奇が ``unstaffed``(1=奇数・0=偶数・−1=外さない)の店の担当を外す(担当の居ない店)。合成の SKU は
    店 0 の棚が廃棄率 0・店 1 の棚に廃棄率のある SKU(売れ残りの試験は店 1 に担当を置く)。``endow=False`` は再開に渡す台帳。
    ``w21c``=〔検収 M1〕差し替えの世界の初期の行の表の店の担当の組 ``[(体, 店), …]``(出どころ W21c・表の店は表の行の順)。"""
    from shibuya import cli
    from shibuya.engine.rights import initial as RI
    from shibuya.engine.systems import build as B
    from shibuya.world.state import World

    world = World.synthetic(n_cells=int(n_cells), seed=1)
    pa = plan_assets(world.n_poi, per_poi=per_poi, src=src)
    monkeypatch.setattr(B, "load_process_assets_or_synthetic", lambda world_dir, assets: pa)
    if w21c:
        from shibuya.engine.rights.ledger import EMPLOY, STORE

        rows = RI.InitialRows([a for a, _p in w21c], [STORE] * len(w21c), [p for _a, p in w21c], [EMPLOY] * len(w21c),
                              ["w21c:試験"] * len(w21c), ["store_staff"] * len(w21c), 0)
        monkeypatch.setattr(B, "_initial_rights", lambda world_dir, pop, n_agents: rows)
    if unstaffed >= 0:
        real = RI.staff_assignment

        def half(kind: Any, n_store: int) -> np.ndarray:
            out = real(kind, n_store)
            out[int(unstaffed)::2] = -1
            return out

        monkeypatch.setattr(RI, "staff_assignment", half)
    return {"world": world, "ledger": cli.build_ledger_bundle(world, N, endow=endow)}


def fresh(monkeypatch: Any, **kw: Any) -> dict[str, Any]:
    """毎回作り直す世界と台帳(ランごとに新しい物が要る)。"""
    return world_fixture(monkeypatch, **kw)


@contextmanager
def du(on: bool = True) -> Iterator[None]:
    """腕 arm を一時的に選ぶ(組み立てが読む)。"""
    prev = AD.arm()
    AD.set_arm(AD.ARM_ON if on else AD.ARM_OFF)
    try:
        yield
    finally:
        AD.set_arm(prev)


@contextmanager
def choose(monkeypatch: Any, rule: Any) -> Iterator[None]:
    """店の仕事の仮のモデルの選びを試験の規則に差し替える(``rule(ctx, presented) -> 候補の id``)。"""
    monkeypatch.setattr(PD.DutiesPort, "_pick", lambda self, ctx, presented: rule(ctx, presented))
    yield


def by_pref(*prefs: str) -> Any:
    """候補の id の好みの順で選ぶ規則(どれも無ければ (語・id) の順の最初の候補)。"""
    def rule(ctx: Any, presented: Any) -> str:
        for k in prefs:
            for c in presented:
                if c.id == k:
                    return c.id
        return sorted(presented, key=lambda c: (c.kind, c.id))[0].id
    return rule


def duty_events(r: Any) -> list[Any]:
    return [e for e in r.event_log.events() if str(e.what).startswith("仕事:")]
