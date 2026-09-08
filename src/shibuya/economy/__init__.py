"""economy: 台帳/transfer/検算/センサス入力。engine の transfer 単一API経由のみ。

層契約: docs/design/v2-implementation-plan.md §3(import-linter で強制)。
economy は engine(``engine.ledger_api`` の Protocol)と core/manifest だけを import し、
**world / agents / perception / llm は import しない**(pyproject の forbidden 契約)。

C4 第1陣(境界・経済設計書 §2.7 + 世界過程設計書 §7.1):
- ``accounts``: 6部門・貸借対照表6行・取引科目の列挙と faucet/sink 表
- ``ledger``: ``transfer`` 単一API + 取引フロー行列 + 生ログ(D-R2-6)
- ``goods``: ``move_goods`` 単一API + SKU 別収支 + 廃棄 band(U-Goods)
- ``checks``: 検算2本・残差ゲート・退蔵・ex nihilo
- ``census``: 日次(軽量)センサス・月次 MER・ゲート
- ``pricing``: 行5 価格形成のエンジン側(内生フロア・Calvo・逸脱比例コスト)
- ``anchors``: §2.5 の金額アンカー(公的値)と初期財布・月次賃金
"""

from shibuya.economy.accounts import (
    ACCOUNTS,
    AccountCode,
    BalanceLine,
    FlowKind,
    Sector,
    faucet_sink_table,
    flow_kind,
    is_allowed,
)
from shibuya.economy.checks import (
    check_all,
    flow_matrix_balanced,
    hoard_report,
    net_worth_equals_real_assets,
    residual_gate,
)
from shibuya.economy.goods import GoodsCode, GoodsLedger, GoodsRef, NodeKind, SkuRegistry
from shibuya.economy.ledger import Ledger

__all__ = [
    "Sector",
    "BalanceLine",
    "AccountCode",
    "FlowKind",
    "ACCOUNTS",
    "is_allowed",
    "flow_kind",
    "faucet_sink_table",
    "Ledger",
    "GoodsLedger",
    "GoodsCode",
    "GoodsRef",
    "NodeKind",
    "SkuRegistry",
    "check_all",
    "flow_matrix_balanced",
    "net_worth_equals_real_assets",
    "residual_gate",
    "hoard_report",
]
