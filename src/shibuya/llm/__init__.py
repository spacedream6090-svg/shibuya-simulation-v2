"""llm: 艦隊クライアント/パーサ/録画テープ。world/agents を import しない(mock LLMが成立する)。

層契約: docs/design/v2-implementation-plan.md §3(import-linter で強制)。
本モジュールは **クライアント契約(Request/Response/Protocol)** を定義し、
行動契約(語彙・契約表・2行形)は ``shibuya.llm.contract``、パーサは ``shibuya.llm.parser``、
未定義行動5段は ``shibuya.llm.undefined``、mock/テープ再生は ``shibuya.llm.mock`` にある。
ここは**それらの再輸出口**でもある(既存の import 経路を壊さないため)。

正典
- 行動契約書 §1 出力形: 1行目「理由: <40字以内・1文>」/ 2行目
  「行動: <語彙1語> **対象: <セルID|物カテゴリ|人ID|なし>** ひと言: <20字以内|なし>」。
- 行動契約書 §2.1: **種別横断12語**(移動・乗車・降車・購入・待機・会話・退去・通報・手伝い・
  断る・休憩・就寝)。§2.2 種別固有(接客・補充・開閉店・価格改定・発車/停車・放送・遅延報告・
  計画改訂・指示・並ぶ/撮影)は**全員に見せ権限だけ検査**する語。
- 知覚契約書 §2.5(2行形・ラベル基準の寛容行指向パーサ)。
- 運用設計書 §2.5: 録画リプレイは (agent_id, tick, wake_class, prompt_hash) の**完全一致**。

**層契約との衝突(親へ報告済み・回避策)**
    C2 の指示は「``TapeLLM`` が ``Replay`` 経由でテープから答える」だが、``Replay`` は
    ``shibuya.engine.tape`` にあり、**llm から engine への import は禁止**(pyproject の
    import-linter 契約「llm は world/agents を import しない」に engine が列挙されている)。
    そこで llm 側は ``TapeLookup`` プロトコル(``lookup(agent_id, tick, wake_class,
    prompt_hash) -> str``)だけを定義し、``TapeLLM`` は**それを満たす任意のオブジェクト**を
    注入で受ける(``engine.tape.Replay`` はこの形をそのまま満たす)。import は発生しない。

**正典の置き場所(C3 で解決)**
    「行動語彙の定数をここに置いたのは、行動パーサがまだ無いため。パーサ実装時に**正典の
    置き場所を1つに決める**必要がある」という C2 の宿題は、``shibuya.llm.contract`` を
    唯一の定義とし、``engine.commit`` もそこを import することで閉じた。

逐次ループ宣言(P4): なし(本モジュールは契約定義と再輸出のみ)。

expedient(本パッケージ分)
- ``prompt_hash`` / ``params_hash`` = ``core.hashing.sha256_cbor``(vLLM の
  ``--prefix-caching-hash-algo sha256_cbor`` と**算法名を揃える**ためであって、vLLM 内部の
  鍵とバイト一致するという意味ではない)。
- トークン数の見積り(``estimate_tokens``)は「UTF-8 の文字数 ÷ 2」の粗い近似。
  実測トークナイザに差し替えるまでの暫定(mock/テストの帳尻用)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

from shibuya.core.hashing import sha256_cbor
from shibuya.llm.contract import (
    ACTION_CODES,
    ACTION_SPECS,
    ACTION_VOCAB_12,
    ACTION_VOCAB_ROLE,
    ALL_ACTION_WORDS,
    COMMENT_MAX_CHARS,
    NO_TARGET,
    NO_TARGET_VALUE,
    REASON_MAX_CHARS,
    ROLE_ACTION_CODES,
    ROLE_ACTION_WORDS,
    ROLE_ACTIONS,
    TWO_LINE_RE,
    UNDEFINED_ACTION,
    ActionSpec,
    Target,
    TargetKind,
    action_code_of,
    format_two_line,
    is_role_action,
    parse_target,
    spec_of,
)

__all__ = [
    # 行動契約(llm.contract の再輸出)
    "ACTION_VOCAB_12",
    "ACTION_VOCAB_ROLE",
    "ROLE_ACTION_WORDS",
    "ALL_ACTION_WORDS",
    "ROLE_ACTIONS",
    "ACTION_CODES",
    "ROLE_ACTION_CODES",
    "ACTION_SPECS",
    "ActionSpec",
    "Target",
    "TargetKind",
    "NO_TARGET",
    "NO_TARGET_VALUE",
    "REASON_MAX_CHARS",
    "COMMENT_MAX_CHARS",
    "UNDEFINED_ACTION",
    "TWO_LINE_RE",
    "format_two_line",
    "parse_target",
    "action_code_of",
    "spec_of",
    "is_role_action",
    # パーサ(llm.parser の再輸出)
    "ParseResult",
    "parse_two_line",
    "find_action_word",
    # 未定義行動5段(llm.undefined の再輸出)
    "UndefinedActionRegistry",
    "UndefinedActionRecord",
    "UndefinedOutcome",
    "Proposal",
    "ProposalStatus",
    "undefined_feedback",
    "map_synonym",
    # クライアント契約
    "estimate_tokens",
    "LLMRequest",
    "LLMResponse",
    "LLMClient",
    "TapeLookup",
    "MockLLM",
    "TapeLLM",
    # 実艦隊クライアント(llm.fleet の再輸出・C6-a)
    "FleetConfig",
    "FleetClient",
    "FleetBridge",
    "FleetBridgeResult",
    "FleetDeferredError",
    "LLMCall",
    "LLMResult",
    "Deferred",
    "Outcome",
    "TapeSink",
    "cache_salt_for",
    "plan_batch",
    "route_primary",
    "split_system_user",
]


def estimate_tokens(text: str) -> int:
    """粗いトークン数見積り(expedient: UTF-8 文字数 ÷ 2、最低 1)。"""
    return max(1, len(text) // 2)


@dataclass(frozen=True)
class LLMRequest:
    """1回の LLM 呼び出し。

    Attributes:
        agent_id: 呼ぶ個体。
        tick: 起床 tick。
        wake_class: 起床クラス(``core.types.EventClass`` の値=class_rank)。
        prompt: 完成したプロンプト本文(共有ブロックを連結したもの)。
        block_ids: プロンプトを構成する共有ブロック id(テープの intern 用・順序は本文の一部)。
        params: デコード設定(temperature/top_p/max_tokens/seed 等)。
        targets: 「対象」欄の候補(mock が選ぶために使う任意欄。実クライアントは本文で渡す)。
        call_id: 呼び出し id(艦隊ルーティング ``xxhash(call_id) mod 7``・テープの列)。
    """

    agent_id: int
    tick: int
    wake_class: int
    prompt: str
    block_ids: tuple[str, ...] = ()
    params: Mapping[str, Any] = field(default_factory=dict)
    targets: tuple[str, ...] = ()
    call_id: str = ""

    @property
    def prompt_hash(self) -> str:
        """プロンプト本文の ``sha256_cbor``(テープの完全一致鍵の第4要素)。"""
        return sha256_cbor(self.prompt)

    @property
    def params_hash(self) -> str:
        """デコード設定の ``sha256_cbor``(テープ列 ``params_hash``)。"""
        return sha256_cbor(dict(self.params))


@dataclass(frozen=True)
class LLMResponse:
    """1回の応答。"""

    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    #: 由来(``"mock"`` / ``"tape"`` / 実艦隊なら engine 名)。診断行で区別する。
    source: str = ""
    finish_reason: str = "stop"


@runtime_checkable
class LLMClient(Protocol):
    """LLM クライアントの最小契約(同期)。非同期は実装側の任意 ``acomplete``。"""

    def complete(self, request: LLMRequest) -> LLMResponse:  # pragma: no cover - 契約のみ
        ...


@runtime_checkable
class TapeLookup(Protocol):
    """録画テープの完全一致検索(``engine.tape.Replay`` がこの形を満たす)。"""

    def lookup(
        self, agent_id: int, tick: int, wake_class: int, prompt_hash: str
    ) -> str:  # pragma: no cover - 契約のみ
        ...


# 契約定義の後に実装/パーサを読む(循環回避)。
from shibuya.llm.mock import MockLLM, TapeLLM  # noqa: E402
from shibuya.llm.parser import (  # noqa: E402
    ParseResult,
    find_action_word,
    parse_two_line,
)
from shibuya.llm.undefined import (  # noqa: E402
    Proposal,
    ProposalStatus,
    UndefinedActionRecord,
    UndefinedActionRegistry,
    UndefinedOutcome,
    map_synonym,
    undefined_feedback,
)

# 艦隊クライアントは**最後**に読む: ``llm.fleet`` が本 ``__init__`` から
# ``LLMRequest``/``parse_two_line``/``UndefinedActionRegistry`` を引くため、
# 上の遅延 import が全部済んだ後でなければ循環する。
from shibuya.llm.fleet import (  # noqa: E402
    Deferred,
    FleetBridge,
    FleetBridgeResult,
    FleetClient,
    FleetConfig,
    FleetDeferredError,
    LLMCall,
    LLMResult,
    Outcome,
    TapeSink,
    cache_salt_for,
    plan_batch,
    route_primary,
    split_system_user,
)
