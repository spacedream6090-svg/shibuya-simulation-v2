"""world.graph — 歩行グラフと next-hop 経路(ベクトル化)。

正典
- 世界データ構築仕様書 W1(歩行グラフ)・W3(全点対前計算=next-hop 表とセル間距離)。
- 行動契約書 §2.1「移動」: 前提=経路が存在・同層で連結。効果=位置は経路上へ
  (**到着時刻はエンジン**)。失敗=到達不能/途中打ち切り。
- 実装計画書 §3: 個体ごとの Python ループを持たない(SoA 配列演算)。

逐次ループ宣言(P4): なし(``route_next_node`` は 2 本の配列によるファンシー添字1回)。

expedient(本モジュール分)
- 1 tick=1 ノード前進(``step_once``)。合成世界(1 セル=1 ノード・100 m)では
  6 km/h の歩行に一致するが、実資産(W1)のノード間隔ではもっと遅い。
  実速度・群衆物理は U15(C4 以降)で置き換わる=**C2 の暫定**。
- ``next_hop`` が負値(到達不能)のときは前進しない(``ResultCode.UNREACHABLE`` は
  呼び出し側=resolve が付ける)。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from shibuya.world.assets import WorldAssets

__all__ = ["WalkGraph"]


@dataclass(frozen=True)
class WalkGraph:
    """歩行グラフ(不変)。``WorldAssets`` の薄いビュー。"""

    assets: WorldAssets

    @property
    def n_nodes(self) -> int:
        return self.assets.n_nodes

    @property
    def node_cell(self) -> np.ndarray:
        return self.assets.node_cell

    @property
    def node_xy(self) -> np.ndarray:
        return self.assets.node_xy

    def route_next_node(self, node, target_node) -> np.ndarray:
        """``node`` から ``target_node`` へ向かう**次のノード**(配列でまとめて引く)。

        Args:
            node: 現在ノードの配列(int)。-1 は「不在」。
            target_node: 目的ノードの配列(int)。-1 は「目的なし」。

        Returns:
            次ノードの int32 配列。目的なし/不在/到達不能は **-1**。
        """
        u = np.asarray(node, dtype=np.int64).ravel()
        v = np.asarray(target_node, dtype=np.int64).ravel()
        if u.shape != v.shape:
            raise ValueError("node と target_node の長さが違う")
        n = self.n_nodes
        ok = (u >= 0) & (u < n) & (v >= 0) & (v < n)
        out = np.full(u.shape, -1, dtype=np.int32)
        if not np.any(ok):
            return out
        uu = u[ok]
        vv = v[ok]
        nxt = np.asarray(self.assets.next_hop[uu, vv], dtype=np.int32)
        # 到達不能(負)と自己ループ(目的地に到着済み)を落とす
        nxt = np.where(nxt < 0, np.int32(-1), nxt)
        out[ok] = nxt
        return out

    def step_once(self, node, target_node) -> tuple[np.ndarray, np.ndarray]:
        """1 tick ぶん前進した後のノードと「到着したか」のマスクを返す。

        Returns:
            ``(new_node, arrived)``。``new_node`` は前進できないとき入力のまま。
        """
        u = np.asarray(node, dtype=np.int64).ravel()
        v = np.asarray(target_node, dtype=np.int64).ravel()
        nxt = self.route_next_node(u, v)
        can_move = (nxt >= 0) & (u >= 0) & (v >= 0)
        new_node = np.where(can_move, nxt.astype(np.int64), u).astype(np.int32)
        arrived = (new_node.astype(np.int64) == v) & (v >= 0)
        return new_node, arrived

    def cell_of(self, node) -> np.ndarray:
        """ノード → セル索引(-1 は場外)。"""
        u = np.asarray(node, dtype=np.int64).ravel()
        out = np.full(u.shape, -1, dtype=np.int32)
        ok = (u >= 0) & (u < self.n_nodes)
        out[ok] = self.assets.node_cell[u[ok]]
        return out

    def xy_of(self, node) -> np.ndarray:
        """ノード → 平面座標(``(n,2)`` float32・不在は 0)。"""
        u = np.asarray(node, dtype=np.int64).ravel()
        out = np.zeros((u.size, 2), dtype=np.float32)
        ok = (u >= 0) & (u < self.n_nodes)
        out[ok] = self.assets.node_xy[u[ok]]
        return out
