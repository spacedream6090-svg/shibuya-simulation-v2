"""llm: 艦隊クライアント/パーサ/録画テープ。world/agents を import しない(mock LLMが成立する)。

層契約: docs/design/v2-implementation-plan.md §3(import-linter で強制)。
本モジュールは **クライアント契約(Request/Response/Protocol)** と **行動語彙・2行形の定数**
だけを定義する。実装は ``shibuya.llm.mock``(MockLLM/TapeLLM)。

正典
- 行動契約書 §1 出力形: 1行目「理由: <40字以内・1文>」/ 2行目
  「行動: <語彙1語> **対象: <セルID|物カテゴリ|人ID|なし>** ひと言: <20字以内|なし>」。
- 行動契約書 §2.1: **種別横断12語**(移動・乗車・降車・購入・待機・会話・退去・通報・手伝い・
  断る・休憩・就寝)。§2.2 種別固有(接客・補充・開閉店・価格改定・発車/停車・放送・遅延報告・
  計画改訂)は**全員に見せ権限だけ検査**する語。
- 知覚契約書 §2.5(2行形・ラベル基準の寛容行指向パーサ)。
- 運用設計書 §2.5: 録画リプレイは (agent_id, tick, wake_class, prompt_hash) の**完全一致**。

**層契約との衝突(親へ報告済み・回避策)**
    C2 の指示は「``TapeLLM`` が ``Replay`` 経由でテープから答える」だが、``Replay`` は
    ``shibuya.engine.tape`` にあり、**llm から engine への import は禁止**(pyproject の
    import-linter 契約「llm は world/agents を import しない」に engine が列挙されている)。
    そこで llm 側は ``TapeLookup`` プロトコル(``lookup(agent_id, tick, wake_class,
    prompt_hash) -> str``)だけを定義し、``TapeLLM`` は**それを満たす任意のオブジェクト**を
    注入で受ける(``engine.tape.Replay`` はこの形をそのまま満たす)。import は発生しない。

expedient(本パッケージ分)
- ``prompt_hash`` / ``params_hash`` = ``core.hashing.sha256_cbor``(vLLM の
  ``--prefix-caching-hash-algo sha256_cbor`` と**算法名を揃える**ためであって、vLLM 内部の
  鍵とバイト一致するという意味ではない)。
- トークン数の見積り(``estimate_tokens``)は「UTF-8 の文字数 ÷ 2」の粗い近似。
  実測トークナイザに差し替えるまでの暫定(mock/テストの帳尻用)。
- 行動語彙の定数をここに置いたのは、行動パーサ(C3 以降・agents 側)がまだ無いため。
  パーサ実装時に**正典の置き場所を1つに決める**必要がある(現状は本ファイルが唯一の定義)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Final, Mapping, Protocol, runtime_checkable

from shibuya.core.hashing import sha256_cbor

__all__ = [
    "ACTION_VOCAB_12",
    "ACTION_VOCAB_ROLE",
    "TWO_LINE_RE",
    "NO_TARGET",
    "format_two_line",
    "estimate_tokens",
    "LLMRequest",
    "LLMResponse",
    "LLMClient",
    "TapeLookup",
    "MockLLM",
    "TapeLLM",
]

#: 行動契約書 §2.1 種別横断12語(表の出現順)。
ACTION_VOCAB_12: Final[tuple[str, ...]] = (
    "移動",
    "乗車",
    "降車",
    "購入",
    "待機",
    "会話",
    "退去",
    "通報",
    "手伝い",
    "断る",
    "休憩",
    "就寝",
)

#: 行動契約書 §2.2 種別固有(権限はエンジンが検査・語彙自体は全員に見せる)。
ACTION_VOCAB_ROLE: Final[tuple[str, ...]] = (
    "接客",
    "補充",
    "開閉店",
    "価格改定",
    "発車",
    "停車",
    "放送",
    "遅延報告",
    "計画改訂",
)

#: 「対象」が無いときの語(行動契約書 §1)。
NO_TARGET: Final[str] = "なし"

#: 2行形の書式検査(ラベル基準・テスト用の最小形。正典のパーサは C3 以降で別に置く)。
TWO_LINE_RE: Final[re.Pattern[str]] = re.compile(
    r"^理由: (?P<reason>[^\n]{1,40})\n行動: (?P<action>\S+) 対象: (?P<target>\S+) ひと言: (?P<comment>[^\n]{1,20})$"
)


def format_two_line(reason: str, action: str, target: str = NO_TARGET, comment: str = NO_TARGET) -> str:
    """行動契約書 §1 の固定2行形に整形する(字数は呼び出し側が守る)。"""
    return f"理由: {reason}\n行動: {action} 対象: {target} ひと言: {comment}"


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


from shibuya.llm.mock import MockLLM, TapeLLM  # noqa: E402  (契約定義の後に実装を読む=循環回避)
