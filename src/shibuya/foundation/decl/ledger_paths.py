"""engine.bridging.ledger_paths — 今の道 → つなぎの台帳に書いてある道の対応(移す段 4 の下ごしらえ・親の決定 1=案 (b))。

つなぎの台帳(``docs/design/bridging-ledger.json``)の ``declared_in`` は、コードの宣言の置き場を ``src/shibuya/…`` の
道筋で持つ。コードの区分を移す段 4 では台帳を書き換えない(台帳の中身の sha が manifest の ``bridges_version`` に入る=
書き換えると既定の結果が動く)。代わりに、移したファイルの今の道から台帳に書いてある道を引く表を本モジュールの 1 か所に
置き、宣言の同定の文字列(``engine.bridging.scan.declared_in_of``)は台帳の道で作る。

- 表 :data:`LEDGER_PATHS` は「今の道(リポの根からの道筋)→ 台帳の道」。**手で書かない**: 移す道具
  (``tools/pkgmove/``)が段ごとに書き足す(許可の一覧の (d))。段 4 の前は空=今の結果も試験も変わらない。
- 戻し方(次の版上げ=``bridges_version`` が動いてよい段): 道具で台帳の道を今の道に書き換え、表を空にする。
- 本モジュールは何も import しない(読み手は宣言の走査と試験だけ=ランの中では読まない)。

逐次ループ宣言: なし。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Mapping

__all__ = ["LEDGER_PATHS", "ledger_path", "current_path"]

#: 今の道 → 台帳に書いてある道(リポの根からの道筋・``/`` 区切り)。移す道具が書き足す(鍵の昇順・1 行 1 組)。
LEDGER_PATHS: Final[Mapping[str, str]] = MappingProxyType({
    "src/shibuya/economy/rules_bind.py": "src/shibuya/engine/economy_rules.py",
    "src/shibuya/economy/stage2_bind.py": "src/shibuya/engine/economy_stage2.py",
    "src/shibuya/economy/wage_formula.py": "src/shibuya/core/wage_formula.py",
    "src/shibuya/foundation/arms/calendar2.py": "src/shibuya/engine/calendar2/arm.py",
    "src/shibuya/foundation/arms/calendar3.py": "src/shibuya/engine/calendar3/arm.py",
    "src/shibuya/foundation/arms/contact.py": "src/shibuya/engine/contact/arm.py",
    "src/shibuya/foundation/arms/duties.py": "src/shibuya/engine/duties/arm.py",
    "src/shibuya/foundation/budget.py": "src/shibuya/core/budget.py",
    "src/shibuya/foundation/decl/bridging.py": "src/shibuya/engine/bridging/ledger.py",
    "src/shibuya/foundation/decl/ledger_paths.py": "src/shibuya/engine/bridging/ledger_paths.py",
    "src/shibuya/foundation/growth.py": "src/shibuya/core/growth.py",
    "src/shibuya/foundation/hashing.py": "src/shibuya/core/hashing.py",
    "src/shibuya/foundation/journal/links.py": "src/shibuya/engine/events/links.py",
    "src/shibuya/foundation/journal/log.py": "src/shibuya/engine/events/log.py",
    "src/shibuya/foundation/manifest/canonical.py": "src/shibuya/manifest/canonical.py",
    "src/shibuya/foundation/manifest/schema.py": "src/shibuya/manifest/schema.py",
    "src/shibuya/foundation/manifest/sections.py": "src/shibuya/engine/manifest_sections.py",
    "src/shibuya/foundation/paths.py": "src/shibuya/core/paths.py",
    "src/shibuya/foundation/ports/decision.py": "src/shibuya/engine/decision/port.py",
    "src/shibuya/foundation/ports/experiment_gate.py": "src/shibuya/engine/experiment/gate.py",
    "src/shibuya/foundation/ports/ledger.py": "src/shibuya/engine/ledger_api.py",
    "src/shibuya/foundation/ports/percept.py": "src/shibuya/perception/facts.py",
    "src/shibuya/foundation/ports/percept_contact.py": "src/shibuya/perception/contact_view.py",
    "src/shibuya/foundation/queues/batching.py": "src/shibuya/engine/batching.py",
    "src/shibuya/foundation/queues/scheduler.py": "src/shibuya/engine/scheduler.py",
    "src/shibuya/foundation/rng.py": "src/shibuya/core/rng.py",
    "src/shibuya/foundation/serialize.py": "src/shibuya/core/serialize.py",
    "src/shibuya/foundation/soa.py": "src/shibuya/core/soa.py",
    "src/shibuya/foundation/text/channels.py": "src/shibuya/perception/channels.py",
    "src/shibuya/foundation/text/hashes.py": "src/shibuya/perception/hashes.py",
    "src/shibuya/foundation/text/normalize.py": "src/shibuya/perception/normalize.py",
    "src/shibuya/foundation/text/templates.py": "src/shibuya/perception/templates.py",
    "src/shibuya/foundation/time_consts.py": "src/shibuya/core/time_consts.py",
    "src/shibuya/foundation/types.py": "src/shibuya/core/types.py",
    "src/shibuya/foundation/vocab/actions.py": "src/shibuya/llm/contract.py",
    "src/shibuya/foundation/vocab/contact_flags.py": "src/shibuya/engine/tools/contacts.py",
    "src/shibuya/foundation/vocab/events.py": "src/shibuya/engine/events/vocab.py",
    "src/shibuya/foundation/write_guard.py": "src/shibuya/engine/systems/guard.py",
    "src/shibuya/foundation/write_permit.py": "src/shibuya/core/write_permit.py",
    "src/shibuya/world/body/energy.py": "src/shibuya/engine/energy.py",
    "src/shibuya/world/body/model.py": "src/shibuya/engine/body/model.py",
    "src/shibuya/world/body/reactions.py": "src/shibuya/engine/body/system1.py",
    "src/shibuya/world/body/rules.py": "src/shibuya/engine/body/rules.py",
    "src/shibuya/world/body/schedule.py": "src/shibuya/engine/body/schedule.py",
    "src/shibuya/world/facts/mock_schedule.py": "src/shibuya/agents/schedule.py",
    "src/shibuya/world/facts/population_reader.py": "src/shibuya/agents/population.py",
    "src/shibuya/world/facts/rights/initial.py": "src/shibuya/engine/rights/initial.py",
    "src/shibuya/world/facts/rights/ledger.py": "src/shibuya/engine/rights/ledger.py",
    "src/shibuya/world/facts/rights/record.py": "src/shibuya/engine/rights/record.py",
    "src/shibuya/world/facts/rules/table.py": "src/shibuya/engine/rules/table.py",
    "src/shibuya/world/facts/weekly_reader.py": "src/shibuya/agents/weekly.py",
    "src/shibuya/world/laws/civic.py": "src/shibuya/engine/processes/civic.py",
    "src/shibuya/world/laws/crowd.py": "src/shibuya/engine/processes/crowd.py",
    "src/shibuya/world/laws/environment.py": "src/shibuya/engine/processes/environment.py",
    "src/shibuya/world/laws/goods_flow.py": "src/shibuya/engine/processes/goods_flow.py",
    "src/shibuya/world/laws/logistics.py": "src/shibuya/engine/processes/logistics.py",
    "src/shibuya/world/laws/opening.py": "src/shibuya/engine/processes/opening.py",
    "src/shibuya/world/laws/rail.py": "src/shibuya/engine/processes/rail.py",
    "src/shibuya/world/laws/rail_events.py": "src/shibuya/engine/processes/rail_events.py",
    "src/shibuya/world/laws/runner.py": "src/shibuya/engine/processes/runner.py",
    "src/shibuya/world/laws/salient.py": "src/shibuya/engine/processes/salient.py",
    "src/shibuya/world/laws/switch_absent.py": "src/shibuya/engine/absent_processes.py",
    "src/shibuya/world/laws/switch_rate.py": "src/shibuya/engine/rate_rules.py",
    "src/shibuya/world/laws/switch_seat.py": "src/shibuya/engine/seat_release.py",
    "src/shibuya/world/laws/traffic.py": "src/shibuya/engine/processes/traffic.py",
    "src/shibuya/world/ledger/absent.py": "src/shibuya/world/processes/absent.py",
    "src/shibuya/world/ledger/actual_log.py": "src/shibuya/world/processes/actual_log.py",
    "src/shibuya/world/ledger/constitution.py": "src/shibuya/world/processes/constitution.py",
    "src/shibuya/world/ledger/first_batch.py": "src/shibuya/world/processes/first_batch.py",
    "src/shibuya/world/ledger/inputs.py": "src/shibuya/world/processes/inputs.py",
    "src/shibuya/world/ledger/records.py": "src/shibuya/world/processes/records.py",
    "src/shibuya/world/ledger/registry.py": "src/shibuya/world/processes/registry.py",
    "src/shibuya/world/ledger/relations.py": "src/shibuya/world/processes/relations.py",
    "src/shibuya/world/ledger/world_catalog.py": "src/shibuya/manifest/world_catalog.py",
    "src/shibuya/world/model/geometry.py": "src/shibuya/engine/geometry.py",
    "src/shibuya/world/model/graph.py": "src/shibuya/world/graph.py",
    "src/shibuya/world/model/navmesh.py": "src/shibuya/world/navmesh.py",
    "src/shibuya/world/model/navmesh_route.py": "src/shibuya/world/navmesh_route.py",
    "src/shibuya/world/model/notice_reach.py": "src/shibuya/perception/p_notice.py",
    "src/shibuya/world/model/percept_state.py": "src/shibuya/perception/state.py",
    "src/shibuya/world/model/proximity.py": "src/shibuya/engine/proximity.py",
    "src/shibuya/world/model/solar.py": "src/shibuya/engine/solar.py",
    "src/shibuya/world/model/space/nav1.py": "src/shibuya/engine/space/nav1.py",
    "src/shibuya/world/model/spatial_index.py": "src/shibuya/engine/spatial_index.py",
    "src/shibuya/world/model/state.py": "src/shibuya/world/state.py",
    "src/shibuya/world/things/device.py": "src/shibuya/engine/contact/device.py",
})


def ledger_path(path: str) -> str:
    """今の道 → 台帳に書いてある道(表に無ければそのまま)。"""
    return LEDGER_PATHS.get(path, path)


def current_path(path: str) -> str:
    """台帳に書いてある道 → 今の道(表に無ければそのまま)。表の値が重なれば ``ValueError``。"""
    inv: dict[str, str] = {}
    for now, old in LEDGER_PATHS.items():
        if old in inv:
            raise ValueError(f"台帳の道が 2 つの今の道から引かれる: {old}")
        inv[old] = now
    return inv.get(path, path)
