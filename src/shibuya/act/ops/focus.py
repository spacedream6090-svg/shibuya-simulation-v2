"""act.ops.focus — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final
import numpy as np
from shibuya.foundation.vocab.agent_codes import FOCUS_NONE, Activity

__all__ = [
    "FOCUS_TTL_TICKS", "FOCUS_ACQUIRE_M", "FOCUS_LOSE_M",
]


#: 注意の焦点の寿命[tick](UE ``Max Age`` 型・**expedient**)。1 tick=60 秒なので 10 分。
FOCUS_TTL_TICKS: Final[int] = 10
#: 焦点を**取得**できる距離[m](UE ``Sight Radius`` 型・**expedient**)。
FOCUS_ACQUIRE_M: Final[float] = 20.0
#: 焦点を**喪失**する距離[m](UE ``Lose Sight Radius`` 型・取得より広い=ヒステリシス)。
FOCUS_LOSE_M: Final[float] = 30.0


# ---------------------------------------------------------------- C9b 注意の焦点(G4)
def _focus_xy(agents, world, code) -> tuple[np.ndarray, np.ndarray]:
    """焦点コード → ``(対象の平面座標 (k,2), 対象が在るか (k,))``。

    人は ``agents.xy``(**前 tick 末の値**=「最後に見た位置」。同 tick 内の適用順に
    依存させないための選択で、C9a の密度(前 tick 末)と同じ約束・**expedient**)。
    目印は ``world.assets`` の POI 座標(静止物なので遅れは無い)。

    逐次ループ宣言(P4): なし。
    """
    c = np.asarray(code, dtype=np.int64).ravel()
    r = agents.registry
    n_ag = max(0, int(agents.n))
    n_poi = max(0, int(world.n_poi))
    is_p = (c >= 0) & (c < n_ag)
    is_q = (c <= -2) & ((-2 - c) < n_poi)
    person = np.clip(c, 0, max(0, n_ag - 1))
    poi = np.clip(-2 - c, 0, max(0, n_poi - 1))
    pxy = np.asarray(r.xy, dtype=np.float64)[person]
    qxy = np.asarray(world.assets.poi_position(), dtype=np.float64)[poi]
    xy = np.where(is_p[:, None], pxy, qxy)
    return xy, (is_p | is_q)


def _clear_focus(agents, ids) -> None:
    """焦点を落とす(``attention_columns`` の無いランでは何もしない)。"""
    if not getattr(agents, "attention_columns", False) or ids.size == 0:
        return
    r = agents.registry
    r.focus_target[ids] = np.int32(FOCUS_NONE)
    r.focus_ttl[ids] = np.uint8(0)


def _set_focus(agents, world, ids, tick, out, *, require_near: bool) -> None:
    """``out.focus_request`` の対象を ``agents.focus_target`` へ書く(C9b G4)。

    Args:
        ids: 対象になりうる体(この tick に 移動/待機 が通った体)。
        require_near: ``True``= 取得距離 ``FOCUS_ACQUIRE_M`` 以内のときだけ焦点にする
            (「見る」= UE ``Sight Radius`` 型)。``False``=距離を問わない(「近づく」)。

    **要求の無い体の焦点は落とす**: 新しい行動を選ぶことは注意を向け直すことなので、
    「見る/近づく」以外の 移動・待機 を選んだ体は前の焦点を持ち越さない
    (**expedient**——契約書に注意の持続の規定は無い。これで焦点の寿命は
    「次に自分で判断するまで」と ``FOCUS_TTL_TICKS`` の短い方になり、有界化 D-R2-6 を満たす)。

    ``attention_columns`` の無いランでは**何もしない**(欄が無い=checkpoint 不変)。

    逐次ループ宣言(P4): なし。
    """
    req = out.focus_request
    if req is None or not getattr(agents, "attention_columns", False) or ids.size == 0:
        return
    code = req[ids]
    xy, present = _focus_xy(agents, world, code)
    want = (code != FOCUS_NONE) & present & (code != ids.astype(np.int64))
    if require_near and bool(np.any(want)):
        d = np.asarray(agents.registry.xy, dtype=np.float64)[ids] - xy
        want = want & (np.sqrt((d * d).sum(axis=1)) <= FOCUS_ACQUIRE_M)
    _clear_focus(agents, ids[~want])
    take = ids[want]
    if take.size == 0:
        return
    r = agents.registry
    r.focus_target[take] = code[want].astype(np.int32)
    r.focus_ttl[take] = np.uint8(FOCUS_TTL_TICKS)
    out.n_focus += int(take.size)


def _advance_focus(agents, world, out) -> None:
    """焦点の**寿命**と**喪失距離**を進める(UE ``Max Age`` / ``Lose Sight Radius`` 型)。

    ``apply`` の末尾(位置を貼り直した**後**)に 1 回だけ回す=距離は同 tick の最新座標で測る。

    **近づいている最中の体は減衰させない**(``activity==MOVING`` かつ ``target_node≥0``)。
    その体の焦点は**移動の対象そのもの**で、寿命や喪失距離で消すと「誰に近づいていたか」が
    着く前に失われ、``TARGET_GONE`` を出す機会が無くなる(UE の ``Auto Success Range from
    Last Seen Location`` を「最後に見た位置まで歩き切る」形で入れた §4 改訂 G11 の要求)。
    移動は必ず到着か ``UNREACHABLE`` で終わるので、焦点は有界のまま(**expedient**)。

    逐次ループ宣言(P4): なし(配列演算のみ・``attention_columns`` のランだけ)。
    """
    if not getattr(agents, "attention_columns", False):
        return
    r = agents.registry
    approaching = (r.activity == int(Activity.MOVING)) & (r.target_node >= 0)
    live = np.flatnonzero((r.focus_ttl > 0) & (~approaching))
    if live.size == 0:
        return
    r.focus_ttl[live] = (r.focus_ttl[live].astype(np.int16) - 1).astype(np.uint8)
    xy, present = _focus_xy(agents, world, r.focus_target[live])
    d = np.asarray(r.xy, dtype=np.float64)[live] - xy
    far = np.sqrt((d * d).sum(axis=1)) > FOCUS_LOSE_M
    dead = live[(r.focus_ttl[live] == 0) | far | (~present)]
    if dead.size:
        r.focus_target[dead] = np.int32(FOCUS_NONE)
        r.focus_ttl[dead] = np.uint8(0)
        out.n_focus_lost += int(dead.size)
