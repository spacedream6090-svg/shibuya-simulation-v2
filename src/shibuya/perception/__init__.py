"""perception: レンダラ/ハッシュ三役/注意ゲート/p_notice → Observation DTO。world/agents/core に依存。

層契約: docs/design/v2-implementation-plan.md §3(import-linter で強制)。

モジュール構成(知覚契約書 R3-8・v1 の節と 1 対 1)
    ``templates``  §1条5 文面凍結・§2.2 ブロック表・§2.5 出力形・段階語彙(法定/LOS 釘付け)
    ``normalize``  §2.4 バイト一致の正規化規約 9 項
    ``channels``   §3.2 チャネル別トークン上限(根拠等級 A-E)+有界化(行単位の切り詰め)
    ``attention``  §4 注意ゲート 段1-段3(p_see・注意予算・内容キャップ・命令文除去)
    ``p_notice``   §3.1 人物③ 2段ヒル型(TTPF+社会伝播)+ablation A0-A4
    ``hashes``     §2.2/§5 ハッシュ三役(prefix キャッシュ鍵・変化検出器・dormant 再送抑止)
    ``state``      §3.1/§7 M12(向き 1B+課題従事 1B)+前回送信ハッシュ
    ``renderer``   §2.1 観測レコード → B0-B6 の決定論描画
"""

from shibuya.perception.attention import (
    BUDGET_ADS,
    BUDGET_OVERHEARD,
    BUDGET_SALIENT,
    P_SEE_LARGE_VISION,
    SalientItem,
    StripReport,
    apply_budget,
    content_cap_chars,
    feature_tag,
    gate_stage1,
    p_see,
    rank_by_saliency,
    strip_imperatives,
    tag_world_text,
)
from shibuya.perception.channels import (
    CHANNEL_BY_ID,
    CHANNEL_LIMITS,
    BudgetMode,
    ChannelLimit,
    Grade,
    TruncationReport,
    estimate_tokens,
    truncate_lines,
)
from shibuya.perception.hashes import (
    b4_field_row,
    block_hash,
    block_hashes,
    field_row_hashes,
    prefix_key,
    should_resend,
)
from shibuya.perception.normalize import (
    AgentDependentWordError,
    assert_no_abbreviation,
    assert_no_agent_dependent_words,
    canonical_whitespace,
    format_time,
    join_lines,
    peg_stage,
    peg_stage_array,
    round_time_5min,
    sort_ids,
    time_band,
)
from shibuya.perception.p_notice import (
    CUTOFF_M,
    D50_DEFAULT_M,
    MAX_EVENTS_PER_TICK,
    Ablation,
    Counters,
    DensityClass,
    EventBudget,
    NoticeResult,
    PNoticeParams,
    TaskLoad,
    notice_event,
    p1_primary,
    p2_social,
)
from shibuya.perception.renderer import PerceptionAssets, Rendered, Renderer
from shibuya.perception.state import PerceptionState
from shibuya.perception.templates import (
    BLOCK_IDS,
    BLOCK_TOKEN_BUDGET,
    GROUP_TOKEN_BUDGET,
    TEMPLATE_VERSION,
    template_sha256,
)

__all__ = [
    # templates
    "TEMPLATE_VERSION",
    "BLOCK_IDS",
    "BLOCK_TOKEN_BUDGET",
    "GROUP_TOKEN_BUDGET",
    "template_sha256",
    # normalize
    "AgentDependentWordError",
    "assert_no_abbreviation",
    "assert_no_agent_dependent_words",
    "canonical_whitespace",
    "format_time",
    "join_lines",
    "peg_stage",
    "peg_stage_array",
    "round_time_5min",
    "sort_ids",
    "time_band",
    # channels
    "CHANNEL_LIMITS",
    "CHANNEL_BY_ID",
    "ChannelLimit",
    "Grade",
    "BudgetMode",
    "TruncationReport",
    "estimate_tokens",
    "truncate_lines",
    # attention
    "P_SEE_LARGE_VISION",
    "BUDGET_ADS",
    "BUDGET_SALIENT",
    "BUDGET_OVERHEARD",
    "SalientItem",
    "StripReport",
    "p_see",
    "gate_stage1",
    "rank_by_saliency",
    "apply_budget",
    "content_cap_chars",
    "strip_imperatives",
    "feature_tag",
    "tag_world_text",
    # p_notice
    "D50_DEFAULT_M",
    "CUTOFF_M",
    "MAX_EVENTS_PER_TICK",
    "Ablation",
    "PNoticeParams",
    "NoticeResult",
    "Counters",
    "EventBudget",
    "TaskLoad",
    "DensityClass",
    "p1_primary",
    "p2_social",
    "notice_event",
    # hashes
    "block_hash",
    "block_hashes",
    "prefix_key",
    "should_resend",
    "b4_field_row",
    "field_row_hashes",
    # state
    "PerceptionState",
    # renderer
    "Renderer",
    "Rendered",
    "PerceptionAssets",
]
