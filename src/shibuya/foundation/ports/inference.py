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
from shibuya.foundation.hashing import sha256_cbor
import math
from enum import Enum
from typing import Final
from shibuya.foundation.hashing import blake3_hex, xxh64
from shibuya.foundation.manifest.schema import Mode

__all__ = [
    "estimate_tokens", "LLMRequest", "LLMResponse", "LLMClient", "TapeLookup",
    "LANE_THINK_TOKENS", "INFRA_CLIP_FACTOR", "INFRA_CLIP_SLACK", "DEFAULT_TEMPERATURE", "DEFAULT_T1_MAX_TOKENS",
    "CACHE_SALT_DOMAIN", "Outcome", "LLMCall", "LLMResult", "Deferred", "FleetDeferredError", "cache_salt_for",
    "seed_for", "route_primary", "max_tokens_for", "split_system_user",
    "RenderedPrompt", "Renderer",
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


# ---------------------------------------------------------------- 定数(設計書の写し)

#: レーン → 思考トークン上限 ``B_world``(認知設計書 §1/§2)。
#: **層契約のための複製**(正典は ``engine.llm_bridge.LANE_THINK_TOKENS``)。等価テストで固定。
LANE_THINK_TOKENS: Final[Mapping[str, int]] = {
    "L0": 0,
    "L1": 0,
    "L2": 2_048,
    "L3": 7_500,
    "L4": 0,
}

#: U19 ③ インフラ保護 ``max_tokens = ceil(1.5*B_world) + 96``。
INFRA_CLIP_FACTOR: Final[float] = 1.5
INFRA_CLIP_SLACK: Final[int] = 96

#: T1 の既定温度。**運用設計書 §1.2 の設定節は ``decoding{T1,T2}`` の欄形しか定めておらず
#: 数値を持たない**ので、数値の出所は次の3つ(いずれも 0.7):
#: 知覚契約書 §2.5「温度0.7・実データ場面での再測は Phase 2=事前登録」/同 §2 卒業条件表
#: 「Phase 2 実データ・温度0.7 で再確認|≤0.10」/運用設計書 §1.3「**本番(温度0.7)**」。
#: C3 の ``engine.run`` 既定 0.0 は **mock ランの決定論**のための値で、実艦隊には適用しない。
DEFAULT_TEMPERATURE: Final[float] = 0.7

#: T1 の既定 ``max_tokens``(**expedient**)。2 行形の最大= 理由 40 字 + 行動語 + 対象 +
#: ひと言 20 字 + ラベル ≒ 70 tok。認知設計書 §1 の「出力 64 tok」は**思考 0 の帯**であって
#: 出力上限の下限ではない。64 だと長めの対象(``g<ix>_<iy>_<GL|UG|DECK>``)で切れ得るので
#: 96 を既定にする(切れたら ``finish_reason=="length"``=``fleet_infra_clip`` に出る)。
DEFAULT_T1_MAX_TOKENS: Final[int] = 96

#: ``cache_salt`` 導出のドメイン語(``core.rng`` の鍵導出と同じ 0x1F 区切りの作法)。
CACHE_SALT_DOMAIN: Final[str] = "shibuya.cache_salt"

_SEP: Final[bytes] = b"\x1f"


def max_tokens_for(lane: str, t1_max_tokens: int) -> int:
    """レーン → ``max_tokens``(U19 ③ インフラ保護)。

    T1 帯(L0/L1/L4)は思考 0 なので**出力上限そのもの**(既定 64 tok)。
    T2 帯(L2/L3)は ``ceil(1.5*B_world)+96``(L2=3,168・L3=11,346)。
    """
    b_world = LANE_THINK_TOKENS[lane]
    if b_world == 0:
        return int(t1_max_tokens)
    return int(math.ceil(INFRA_CLIP_FACTOR * b_world)) + INFRA_CLIP_SLACK


def cache_salt_for(mode: Mode | str, run_id: str) -> str:
    """実行モード別 ``cache_salt``(運用設計書 §1.2・実装計画書 §7)。

    同じ ``(mode, run_id)`` なら同じ・モードが違えば違う(=較正と holdout が prefix
    キャッシュを共有しない=**勘定分離**を vLLM 側でも効かせる)。

    Args:
        mode: ``manifest.schema.Mode`` かその値の文字列。
        run_id: manifest 正規化本文の自己ハッシュ(押印前は空文字でよい)。

    Returns:
        32 桁 16 進(blake3 先頭 16 バイト)。
    """
    name = mode.value if isinstance(mode, Mode) else str(mode)
    if name not in {m.value for m in Mode}:
        raise ValueError(f"未知の実行モード: {name!r}(設計書 §1.2 の 5 値)")
    payload = (
        CACHE_SALT_DOMAIN.encode("utf-8") + _SEP + name.encode("utf-8") + _SEP + run_id.encode("utf-8")
    )
    return blake3_hex(payload, length=16)


def seed_for(call_id: str, run_seed: int) -> int:
    """呼ごとのデコード seed(``xxh64(call_id, seed=run_seed)`` の下位 31 bit)。

    ラン(``run_seed``)と呼(``call_id``)から決まる=**呼び出し順に依存しない**
    (運用設計書 §2.5 のカウンタベース RNG と同じ性質)。
    """
    return int(xxh64(call_id.encode("utf-8"), seed=int(run_seed) & 0xFFFF_FFFF_FFFF_FFFF)) & 0x7FFF_FFFF


def route_primary(call_id: str, n_replicas: int) -> int:
    """レプリカ配分 ``xxhash(call_id) mod N``(実装計画書 §7・N=7 が既定艦隊)。"""
    if n_replicas <= 0:
        raise ValueError("n_replicas は 1 以上")
    return int(xxh64(call_id.encode("utf-8")) % n_replicas)


def split_system_user(text: str, system_block: str) -> tuple[str, str]:
    """描画本文を ``(system, user)`` に割る(B0=system・残り=user)。

    prefix 共有の単位を「静的ブロック=system メッセージ」に揃えるための補助。
    先頭が ``system_block`` で始まらないときは ``("", text)`` を返す(**推測で切らない**)。
    """
    if system_block and text.startswith(system_block):
        rest = text[len(system_block) :]
        return system_block, rest[1:] if rest.startswith("\n") else rest
    return "", text


# ---------------------------------------------------------------- 呼と結果


class Outcome(str, Enum):
    """1 呼の帰結(§7「全て診断行に計数」の分類)。

    ``FleetClient`` が付けるもの:
        ``OK`` / ``FORMAT_RETRY_OK``(温度 0 の再生成で書式が通った) /
        ``ERROR_RETRIED_OK``(接続エラーの再試行で通った) /
        ``DEFERRED_TIMEOUT`` / ``DEFERRED_QUEUE_FULL`` / ``ERROR_OTHER``。
    ``FleetBridge`` が付けるもの:
        ``UNDEFINED``(再生成後も語彙一致せず §7 の未定義行動5段へ回した)。
    """

    OK = "ok"
    FORMAT_RETRY_OK = "format_retry_ok"
    UNDEFINED = "undefined"
    DEFERRED_TIMEOUT = "deferred_timeout"
    DEFERRED_QUEUE_FULL = "deferred_queue_full"
    ERROR_RETRIED_OK = "error_retried_ok"
    ERROR_OTHER = "error_other"


@dataclass(frozen=True)
class LLMCall:
    """艦隊へ投げる 1 呼(engine 側 ``RenderedPrompt`` + 起床情報を層契約越しに運ぶ器)。

    Attributes:
        call_id: 呼び出し id。**ルーティングの入力**(``xxhash(call_id) mod N``)。
            engine の既定は ``"<tick>:<agent>:<class>"``(``engine.llm_bridge``)。
        agent_id / tick / wake_class: テープ鍵の第1-3要素(実効クラス)。
        prompt: 連結した本文。**テープ鍵の第4要素 ``sha256_cbor(prompt)`` の入力**
            (mock ランと同じ鍵になるよう、system/user に割る前の本文を持つ)。
        system / user: チャット形の 2 メッセージ。``user`` が空なら ``prompt`` を使う。
        blocks: ``(block_id, text)`` の共有ブロック(テープの intern 用・順序は本文の一部)。
        lane: δ_think レーン(``L0``..``L4``)。max_tokens と enable_thinking を決める。
        cell / time_bucket: 順序制御のグループ鍵(同一(セル, 5分帯)は同時発射・同一 GPU 回避)。
        since_tick: **最初に起床条件が立った tick**(``arbiter.WakeCandidates.since_tick``)。
            繰り延べを起床候補へ再投入するとき待ち時間の基準を失わないために運ぶ。
            ``-1``(既定)なら ``tick`` を使う。
        prompt_hash_hint: レンダラ側の指紋(blake3・診断用。テープ鍵ではない)。
        params_extra: デコード設定の追加(診断・ablation 用)。
    """

    call_id: str
    agent_id: int
    tick: int
    wake_class: int
    prompt: str
    system: str = ""
    user: str = ""
    blocks: tuple[tuple[str, str], ...] = ()
    lane: str = "L1"
    cell: int = -1
    time_bucket: int = 0
    condition: int = 0
    since_tick: int = -1
    prompt_hash_hint: str = ""
    params_extra: Mapping[str, Any] = field(default_factory=dict)
    #: テープ版 3(記憶 第 1 段 6b): 描画の B5「記憶」行に載せた記憶の行番号(記憶の無いラン=空)。
    recalled_rows: tuple[int, ...] = ()
    #: テープ版 4(10e・E5・A8): 引いた記憶の同定(``recalled_rows`` と同じ並び)。最初に書かれた時刻(通しの T)・
    #: 種類(``memory.EVENT_KINDS``・店の行は ``STORE_ITEM_KIND``)・対象(``mem_object`` の符号化・店の行は POI)。
    recalled_first_tick: tuple[int, ...] = ()
    recalled_kind: tuple[int, ...] = ()
    recalled_object: tuple[int, ...] = ()
    #: テープ版 4: 「(知人)」の印を見せた相手の体 id(B5 の本文に出た順・重複なし)。
    acquaintance_ids: tuple[int, ...] = ()
    #: テープ版 4(K1): 本人ブロックの本文(B5 は列に直接・B6 はブロック表に intern)。
    b5_text: str = ""
    b6_text: str = ""

    @property
    def block_ids(self) -> tuple[str, ...]:
        return tuple(b for b, _ in self.blocks)

    @property
    def user_text(self) -> str:
        return self.user or self.prompt

    @property
    def group_key(self) -> tuple[int, int]:
        """順序制御のグループ(セル, 5分帯)。"""
        return (int(self.cell), int(self.time_bucket))

    @property
    def wake_since(self) -> int:
        """起床候補へ戻すときの ``since_tick``(未設定なら発射 tick)。"""
        return int(self.since_tick) if int(self.since_tick) >= 0 else int(self.tick)


@dataclass(frozen=True)
class LLMResult:
    """答えが返った 1 呼。"""

    call: LLMCall
    text: str
    outcome: Outcome
    replica: int
    endpoint: str
    tokens_in: int = 0
    tokens_out: int = 0
    ttft_s: float = 0.0
    e2e_s: float = 0.0
    attempts: int = 1
    format_retried: bool = False
    #: **書式再生成の前**に返ってきた生応答(``format_retried`` のときだけ入る)。
    #: テープには最終応答しか残らないので、初回失敗の原因分析はここからしか採れない
    #: (``FleetBridge(debug_dir=…)`` が jsonl へ落とす。既定は保持するだけで書かない)。
    first_text: str = ""
    finish_reason: str = "stop"
    infra_clip: bool = False

    @property
    def call_id(self) -> str:
        return self.call.call_id

    @property
    def source(self) -> str:
        """``LLMResponse.source`` 相当(診断行で mock/tape と区別する)。"""
        return f"fleet:{self.replica}"

    @property
    def deferred(self) -> bool:
        return False


@dataclass(frozen=True)
class Deferred:
    """答えが返らなかった 1 呼。**破棄しない**(呼び出し側が次 tick へ繰り延べる)。

    Attributes:
        outcome: ``DEFERRED_TIMEOUT`` / ``DEFERRED_QUEUE_FULL`` / ``ERROR_OTHER``。
        reason: 診断用の逐語(例外型名・HTTP ステータス等)。
        replica: 最後に当たったレプリカ(キュー満杯なら割当予定だったもの)。
    """

    call: LLMCall
    outcome: Outcome
    reason: str = ""
    replica: int = -1
    attempts: int = 0
    e2e_s: float = 0.0

    @property
    def call_id(self) -> str:
        return self.call.call_id

    @property
    def deferred(self) -> bool:
        return True


class FleetDeferredError(RuntimeError):
    """同期 1 呼経路(``FleetClient.complete``)で繰り延べになった。

    同期経路は**繰り延べを値で表現できない**ので、黙って空応答を返さず例外にする
    (空応答を返すと ``engine.llm_bridge`` が未定義行動→待機に落とし、呼が消える=憲法1 違反)。
    本番経路は ``submit``/``poll``/``drain``。
    """

    def __init__(self, deferred: Deferred) -> None:
        super().__init__(f"{deferred.outcome.value}: {deferred.reason} (call_id={deferred.call_id})")
        self.deferred = deferred


# ------------------------------------------------------------------ プロンプト生成
@dataclass(frozen=True)
class RenderedPrompt:
    """レンダラの出力。

    Attributes:
        text: プロンプト本文(``prompt_hash`` はこの本文から取る)。
        blocks: 共有ブロック ``(block_id, text)``(テープの intern 用)。
        targets: mock 用の「対象」候補(実クライアントは本文で渡す)。
        prompt_hash: レンダラ側の指紋(``perception.Rendered.prompt_hash`` = blake3)。
            空文字なら bridge は ``LLMRequest.prompt_hash``(sha256_cbor)を使う。
        group_tokens: 予算グループ → 推定トークン(診断行の素材・空なら測らない)。
    """

    text: str
    blocks: tuple[tuple[str, str], ...] = ()
    targets: tuple[str, ...] = ()
    prompt_hash: str = ""
    group_tokens: tuple[tuple[str, int], ...] = ()
    #: 記憶 第 1 段 6b: B5「記憶」行に載せた記憶の行番号(テープ版 3 の列・記憶の無いラン=空)。
    recalled_rows: tuple[int, ...] = ()
    #: テープ版 4(10e・E5・A8): 引いた記憶の同定(``recalled_rows`` と同じ並び)。最初に書かれた時刻(通しの T)・
    #: 種類(``memory.EVENT_KINDS``・店の行は ``STORE_ITEM_KIND``)・対象(``mem_object`` の符号化・店の行は POI)。
    recalled_first_tick: tuple[int, ...] = ()
    recalled_kind: tuple[int, ...] = ()
    recalled_object: tuple[int, ...] = ()
    #: テープ版 4: 「(知人)」の印を見せた相手の体 id(B5 の本文に出た順・重複なし)。
    acquaintance_ids: tuple[int, ...] = ()
    #: テープ版 4(K1): 本人ブロックの本文。B5 は列に直接・B6 はブロック表に intern(空=描画が無い経路)。
    b5_text: str = ""
    b6_text: str = ""
    #: 第 1 期 1-2: 描いた知覚の事実(``perception.facts.Percept``・本物の描画だけ・スタブは None)。テープには書かない
    #: (刻みの中の一時=``TickScratch.percepts`` と判断の入力へ渡す)。
    percept: Any = None

    @property
    def block_ids(self) -> tuple[str, ...]:
        return tuple(b for b, _ in self.blocks)


@runtime_checkable
class Renderer(Protocol):
    """観測ブロック(B0-B6)→プロンプト本文の契約。本物は ``perception.renderer.Renderer``。"""

    def render(
        self,
        *,
        agent_id: int,
        tick: int,
        cell: int,
        activity: int,
        hunger: int,
        wake_class: int,
        condition: int,
        last_action: int,
        inviter: int = -1,
    ) -> RenderedPrompt:  # pragma: no cover - 契約のみ
        ...
