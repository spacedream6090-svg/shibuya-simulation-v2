"""engine.growth_decl — エンジン側の**状態成長宣言**(D-R2-6 の YAML 5 欄・データ非依存の定数)。

正典
- 世界過程設計書 §6 **D-R2-6**: YAML 5 欄 ``per_agent_bytes`` / ``per_cell_bytes`` /
  ``per_day_growth``(``O(1)|O(N)|O(N·t)+係数``)/ ``retention``(**生ログ保持日数と圧縮先**)/
  ``worst_case_ops_per_tick``。**ゲート=24step スモークの実測を1日/30日へ外挿し予算書 M 行超で
  CI 失敗**。
- 実装計画書 §5: 「40万体×1日: **テープ1.2-1.6GB(圧縮後)**+診断/取引/行動ログ数百MB=
  1.5-2.0GB(S1≤5GB内)」「**個体×tickの全記録は禁止**(セル別集計へ)」。
- 予算宣言表 **S1** 恒久記録 ≤5GB/シミュ日・**L4** 平均10呼/体/日。

本ファイルは**定数だけ**を持つ(測定は ``engine.run`` が行い ``core.growth.check_growth`` に渡す)。

expedient(本モジュール分)
- 1 行あたりバイト数(``*_ROW_BYTES``)は実測ではなく見積り。テープ 400 B/呼 は
  実装計画書の「400万呼で 1.2-1.6GB(圧縮後)」= 300-400 B/呼 の上端を採った。
- ``pending_apply`` / ``intent_buffer`` / ``arbiter_backlog`` は有界バッファなので
  ``per_day_growth = O(1)``・係数 0(**日をまたいで伸びない**)。実測側には
  「その日の最大在庫バイト」を渡す(増分の読みとしては保守側)。
- cap の値(16 MB / 16 MB / 32 MB / 64 MB / 5 GB)は S1 と M8 から親が割り当てた見積り。
  予算表に個別行が無い=**delta 改版でこの割当を正典化する必要がある**。
"""

from __future__ import annotations

from typing import Final, Mapping

from shibuya.core.growth import GrowthDeclaration, Retention

__all__ = [
    "PENDING_APPLY_ROW_BYTES",
    "ARBITER_PENDING_ROW_BYTES",
    "INTENT_ROW_BYTES",
    "DIAG_ROW_BYTES",
    "TAPE_ROW_BYTES",
    "CALLS_PER_AGENT_PER_DAY",
    "TICKS_PER_DAY",
    "declarations",
    "to_yaml",
]

#: 1 行あたりバイト(見積り・expedient)。
PENDING_APPLY_ROW_BYTES: Final[int] = 128
#: 繰り延べ待ち行列 1 件 = agent_id 8 + condition 1 + class 8 + since_tick 8 → 32 B(切り上げ)。
ARBITER_PENDING_ROW_BYTES: Final[int] = 32
INTENT_ROW_BYTES: Final[int] = 32
DIAG_ROW_BYTES: Final[int] = 128
TAPE_ROW_BYTES: Final[int] = 400

#: 予算行 L4 の制御目標(平均呼数/体/シミュ日)。
CALLS_PER_AGENT_PER_DAY: Final[int] = 10
TICKS_PER_DAY: Final[int] = 1_440


def declarations() -> Mapping[str, GrowthDeclaration]:
    """エンジン側 5 構造体の成長宣言(名前 → 宣言)。"""
    rows = (
        GrowthDeclaration(
            name="pending_apply",
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(1)",
            per_day_growth_coef=0.0,
            retention=Retention(days=1, target="次tick先頭で適用して消える(保持しない)"),
            worst_case_ops_per_tick=TICKS_PER_DAY,  # 1 tick に届く応答数の上界(L4/tick 相当)
            cap=16_000_000,
            cap_budget_row="M8(RSS総額≤24GB の内数として親が割当・要 delta)",
            mechanism=True,
            note="運用設計書 §2.4 pending_apply。tick 内で消費する有界バッファ=日をまたがない。",
            unit="response",
            bytes_per_unit=PENDING_APPLY_ROW_BYTES,
        ),
        GrowthDeclaration(
            name="intent_buffer",
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(1)",
            per_day_growth_coef=0.0,
            retention=Retention(days=1, target="Phase C 適用後に破棄(保持しない)"),
            worst_case_ops_per_tick=0,
            cap=16_000_000,
            cap_budget_row="M8(親が割当・要 delta)",
            mechanism=True,
            note="運用設計書 §2.2 Phase A/B の intent。1 個体 1 件・tick 内で消費。",
            unit="intent",
            bytes_per_unit=INTENT_ROW_BYTES,
        ),
        GrowthDeclaration(
            name="arbiter_backlog",
            per_agent_bytes=ARBITER_PENDING_ROW_BYTES,
            per_cell_bytes=0,
            per_day_growth="O(1)",
            per_day_growth_coef=0.0,
            retention=Retention(days=1, target="合流により1体1件・翌日は同じ上界に張り付く"),
            worst_case_ops_per_tick=0,
            cap=32_000_000,
            cap_budget_row="M8(親が割当・要 delta)",
            mechanism=True,
            note=(
                "知覚契約書 §6 の繰り延べ待ち行列。恒常過負荷(U≈1.74)で滞留するが、"
                "同一体の保留は1呼に合流するので**上界は個体数**(実測 40,000体で最大 39,445 件)。"
                "日をまたいで伸びる項ではない。"
            ),
            unit="pending wake",
            bytes_per_unit=ARBITER_PENDING_ROW_BYTES,
        ),
        GrowthDeclaration(
            name="diagnostics_rows",
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(1)",
            per_day_growth_coef=float(TICKS_PER_DAY * DIAG_ROW_BYTES),
            retention=Retention(days=30, target="日次集約行(Parquet/zstd・日次で畳む)"),
            worst_case_ops_per_tick=1,
            cap=64_000_000,
            cap_budget_row="S1(恒久記録≤5GB/シミュ日 の内数・親が割当)",
            mechanism=True,
            note="予算宣言表 §7-5 の診断行4列+運用列。tick あたり1行=日次では定数増分。",
            unit="row",
            bytes_per_unit=DIAG_ROW_BYTES,
            growth_per_simday=float(TICKS_PER_DAY),
        ),
        GrowthDeclaration(
            name="tape_rows",
            per_agent_bytes=0,
            per_cell_bytes=0,
            per_day_growth="O(N)",
            per_day_growth_coef=float(CALLS_PER_AGENT_PER_DAY * TAPE_ROW_BYTES),
            retention=Retention(days=1, target="日次 Parquet(zstd)へ書き出し・共有ブロックはintern"),
            worst_case_ops_per_tick=0,
            cap=5_000_000_000,
            cap_budget_row="S1",
            mechanism=True,
            note="運用設計書 §2.5 録画テープ(1呼=1行)。L4 の平均10呼/体/日で O(N)。",
            unit="call",
            bytes_per_unit=TAPE_ROW_BYTES,
            growth_per_simday=float(CALLS_PER_AGENT_PER_DAY),
        ),
    )
    return {d.name: d for d in rows}


def to_yaml() -> str:
    """D-R2-6 の YAML 5 欄を文字列で返す(manifest / 検収パックへ貼る用)。"""
    import yaml

    return yaml.safe_dump(
        {"state_growth": [d.to_yaml_row() for d in declarations().values()]},
        allow_unicode=True,
        sort_keys=False,
    )
