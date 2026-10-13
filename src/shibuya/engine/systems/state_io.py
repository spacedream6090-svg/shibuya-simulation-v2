"""engine.systems.state_io — 箱から状態台帳の持ち主・知覚 SoA・ハッシュの材料を組む口(第 1 期 1-0)。

HEAD ``ee3abc7`` の ``run_day`` の入れ子の関数 ``_hash_owners``・``_pst_now``・``_act_hash_now`` を、箱を受け取る関数にしたもの(中身は同じ)。
持ち主の名・順・``run_day`` の持ち主のクラス(``engine.run._RunDayLocals``)は変えない(ハッシュに道筋の文字列が入る=
草案 §3-3 の 2)。

逐次ループ宣言: なし。
"""

from __future__ import annotations

from typing import Any

from shibuya.core.hashing import blake3_hex
from shibuya.engine.state_hashes import behavior_hash as behavior_state_hash
from shibuya.engine.state_hashes import component_digests
from shibuya.engine.state_hashes import full_hash as full_state_hash

__all__ = ["hash_owners", "pst_now", "act_hash_now", "full_state_hash", "behavior_state_hash", "component_digests"]

# 〔1-0 の注〕``full_state_hash`` は checkpoint・日の締めの後・状態の書き出し・再開の検算がどれも**この名前を通して**呼ぶ
# (試験の差し替えの的を 1 つにする=草案 §3-3 の 15。HEAD では ``engine.run.full_state_hash``)。


def pst_now(b: Any) -> Any:
    """知覚 SoA(顕著行為の過程が持つ・世界過程が無ければ ``None``)。HEAD の ``_pst_now``。"""
    runner = b.layers.runner
    return runner.salient.pstate if runner is not None else None


def hash_owners(b: Any) -> dict[str, Any]:
    """10b: 状態台帳の外の状態の持ち主(``items`` の根の鍵)。HEAD の ``_hash_owners`` と同じ鍵・同じ順・同じ物。"""
    from shibuya.engine.run import _RunDayLocals

    L, io = b.layers, b.llm
    return {
        "act_layer": L.act_layer, "intent_layer": L.intent_layer, "fam_layer": L.fam_layer,
        "mem_layer": L.mem_layer, "poi_resolver": L.poi_resolver, "wom": L.wom, "rel_layer": L.rel_layer,
        "classical": L.classical, "energy": L.energy, "norm_meter": L.norm_meter,
        "presence": L.presence, "conv": L.conv, "arbiter": L.arbiter, "detector": L.detector,
        "runner": L.runner, "ledger": L.ledger, "undefined": L.bridge.undefined,
        "renderer": L.renderer,
        "bridge": L.bridge, "fleet_bridge": L.fleet_bridge,
        "run_day": _RunDayLocals(io.pending, io.fleet_deferred, io.fleet_waiting, io.replay_inbox),
    }


def act_hash_now(b: Any) -> str:
    """活動層(と意図の層)の Python 側の状態のハッシュ(HEAD の ``_act_hash_now``)。"""
    act_layer, intent_layer = b.layers.act_layer, b.layers.intent_layer
    if act_layer is None:
        return ""
    if intent_layer is None:
        return act_layer.state_hash()
    return blake3_hex(f"{act_layer.state_hash()}\x1f{intent_layer.state_hash()}".encode())

