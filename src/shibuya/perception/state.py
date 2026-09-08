"""perception.state — 知覚側が持つ個体 SoA(予算行 **M12** と prefix 抑止の前回ハッシュ)。

正典
- 知覚契約書 §3.1 性能予算:「追加状態=**向き量子化1 byte+課題従事フラグ1 byte=2 byte/体**
  =800 KB」。
- 知覚契約書 §7 予算 delta:「**M12** = p_notice状態2 byte + invocation distance 2 byte/体」。
- 知覚契約書 §5:「ハッシュ三役: B2/B4 のバイト列ハッシュ=キャッシュキー(prefix)・
  変化検出器・**dormant 再送抑止**」→ 抑止には「前回その個体へ送ったハッシュ」が要る。
- 実装計画書 §3: 「SoA: 1フィールド=1本の NumPy 配列+dtype レジストリ(M9)。
  **個体オブジェクトを作らない**」。

**invocation distance の所有者(親へ報告・黙って二重に持たない)**
    ``agents.state.AgentState`` が既に ``invocation_distance``(uint16・M12)を宣言している
    (C2 が実装済み)。M12 の 2 byte を**二重計上しない**ため、本レジストリは既定では
    宣言しない。``PerceptionState(n, include_invocation_distance=True)`` は、知覚側だけを
    単体で回すベンチ/テスト用の逃げ道(その場合 M12 の 4 byte は本レジストリに閉じる)。

バイト予算(宣言)
    heading 1 + task_flag 1 = **2 byte/体**(M12 の p_notice 状態・契約書の逐語)
    last_b2_hash 8 + last_b4_hash 8 = **16 byte/体**(契約書に行が無い=本モジュールの宣言)
      理由: dormant 再送抑止(§5 三役の 3 本目)は「前回送ったバイト列」を個体ごとに覚えて
      いないと成立しない。u64 より短くすると衝突で**送るべき変化を握り潰す**(取りこぼしは
      再送抑止では致命的)。40万体で 6.4 MB=M8 の総額に対して無視できる。
    合計 ≤ ``PERCEPTION_BYTE_CAP`` = 24 byte/体(M1 30KB/体 の内数として自主的に切った上限)。

逐次ループ宣言(P4): ``_set_writeable`` のフィールド数ぶんのみ(4-5 本)。

expedient(本モジュール分)
- 向きの量子化=**16 セクタ**(22.5°刻み)。契約書は「向き量子化1 byte」としか書かない。
  256 段(1.4°刻み)も 1 byte に入るが、m_ecc の効き(E2=6.22°)に対して 22.5° 刻みは粗い側=
  **保守的**(偏心の効果を弱く見積もる)。ablation で 64 セクタと比べる枠を残す。
- 自主上限 24 byte/体(予算表に知覚側の行が無い)。
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Final, Iterator

import numpy as np

from shibuya.core.soa import Registry
from shibuya.perception.p_notice import HEADING_SECTORS, DensityClass, TaskLoad

__all__ = [
    "PERCEPTION_BYTE_CAP",
    "HEADING_SECTORS",
    "TaskLoad",
    "DensityClass",
    "PerceptionState",
    "heading_from_vector",
]

#: 知覚側 SoA の個体あたり自主上限[byte](M1 30,000 B/体 の内数)。
PERCEPTION_BYTE_CAP: Final[int] = 24


def heading_from_vector(dx: np.ndarray, dy: np.ndarray, sectors: int = HEADING_SECTORS) -> np.ndarray:
    """進行方向ベクトル → 量子化された向き(0..sectors-1 の uint8)。

    セクタ 0 = +x 方向。境界は各セクタの中心が ``k·360/sectors`` 度になるよう丸める。
    """
    ang = np.degrees(np.arctan2(np.asarray(dy, dtype=np.float64), np.asarray(dx, dtype=np.float64)))
    q = np.rint(((ang % 360.0) / (360.0 / sectors))) % sectors
    return q.astype(np.uint8)


class PerceptionState:
    """知覚側の個体 SoA。

    Example:
        >>> st = PerceptionState(4)
        >>> st.declared_bytes_per_agent
        18
        >>> st.heading[:] = 3
        >>> st.freeze(); st.heading.flags.writeable
        False
    """

    def __init__(
        self,
        n: int,
        *,
        include_invocation_distance: bool = False,
        cap_bytes: int | None = PERCEPTION_BYTE_CAP,
    ) -> None:
        """
        Args:
            n: 個体数。
            include_invocation_distance: True で ``invocation_distance`` をこちらに持つ
                (``agents.state`` が持たない単体ベンチ用)。
            cap_bytes: 個体あたりバイト上限(既定 24 B/体)。
        """
        self.n = int(n)
        self.registry = Registry.for_agents(self.n, per_entity_byte_cap=cap_bytes)
        r = self.registry
        # ---- M12: p_notice 状態 2 byte/体(契約書 §3.1 逐語) ----
        r.declare("heading", np.uint8, byte_budget_per_agent=1, mechanism=True,
                  doc="向きの量子化(16セクタ・22.5°刻み・M12 p_notice の m_ecc)")
        r.declare("task_flag", np.uint8, byte_budget_per_agent=1, mechanism=True,
                  doc="課題従事フラグ(TaskLoad 手空き/歩きスマホ/会話・M12 p_notice の m_load)")
        # ---- dormant 再送抑止(§5 三役の 3 本目) ----
        r.declare("last_b2_hash", np.uint64, byte_budget_per_agent=8, mechanism=True,
                  doc="前回その個体へ送った B2 の描画バイト xxh64(dormant 再送抑止)")
        r.declare("last_b4_hash", np.uint64, byte_budget_per_agent=8, mechanism=True,
                  doc="前回その個体へ送った B4 の描画バイト xxh64(dormant 再送抑止)")
        if include_invocation_distance:
            r.declare("invocation_distance", np.uint16, byte_budget_per_agent=2, mechanism=False,
                      doc="次の計画境界までの残時間[分](M12・agents.state が持つときは重複宣言しない)")
        self._frozen = False

    # ---- 素通し ----
    def __getattr__(self, name: str) -> np.ndarray:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.__dict__["registry"].field(name)
        except (KeyError, AttributeError):
            raise AttributeError(f"未宣言のフィールド: {name!r}") from None

    def __len__(self) -> int:
        return self.n

    # ---- 書き込みガード(resolve 単一書き手・agents/world と同じ規律) ----
    @property
    def frozen(self) -> bool:
        return self._frozen

    def _set_writeable(self, flag: bool) -> None:
        """全配列の書き込み可否を切り替える(逐次ループ宣言: フィールド数ぶん)。

        Note:
            ``agents.state``/``world.state`` と違い **公開の ``thaw`` を持たない**。
            ``tests/engine/test_two_phase.py`` の静的検査(「``.thaw(`` を呼んでよいのは
            agents/state.py と world/state.py だけ」)の趣旨=「解除口を公開しない」に
            より強く従うため。解除は ``writable()`` の中でだけ起きる。
        """
        for arr in self.registry.arrays.values():
            arr.flags.writeable = flag

    def freeze(self) -> None:
        """全配列を読み取り専用にする。"""
        self._set_writeable(False)
        self._frozen = True

    @contextmanager
    def writable(self) -> Iterator["PerceptionState"]:
        """``with st.writable():`` の間だけ書ける(唯一の解除口)。"""
        was_frozen = self._frozen
        if was_frozen:
            self._set_writeable(True)
            self._frozen = False
        try:
            yield self
        finally:
            if was_frozen:
                self.freeze()

    # ---- 監査 ----
    @property
    def declared_bytes_per_agent(self) -> int:
        return self.registry.declared_bytes_per_entity

    def bytes_total(self) -> int:
        return self.registry.bytes_total()

    def budget_report(self):  # type: ignore[no-untyped-def]
        """M9 の宣言 vs 実バイト報告。"""
        return self.registry.budget_report()

    def state_hash(self) -> str:
        return self.registry.state_hash()
