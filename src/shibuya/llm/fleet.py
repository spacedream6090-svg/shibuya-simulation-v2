"""llm.fleet — 実 vLLM 艦隊クライアント(httpx 非同期 × N レプリカ)と艦隊ブリッジ。

エンジンの tick ループを**止めない**ことが本モジュールの存在理由。engine 側は
``submit`` で呼を投げ、``poll``/``drain`` で受け取る(呼の往復は背景スレッドの
イベントループが回す)。

正典
- 実装計画書 §7「U8/U9 追補(艦隊接続)」
    - 検証ラン=``--prefix-caching-hash-algo sha256_cbor`` + 実行モード
      (smoke/calibration/holdout/ablation/production)別 ``cache_salt`` を manifest に記録。
    - 順序制御: ブロック順序固定・同一(セル, 時間帯)の呼を同一時刻にまとめて発射・
      **同一 GPU に寄せない**(BN-4=セルアフィニティ不採用)・レプリカ配分=
      ``xxhash(call_id) mod 7``・不均衡時は least-in-flight。
    - 失敗の意味論: 接続エラー=**同一レプリカ1回→別レプリカ1回**/タイムアウト
      (TTFT 60 s・e2e 300 s=expedient)=**繰り延べ(破棄禁止・憲法1)**/書式エラー=
      **温度 0 で 1 回再生成**→未定義行動5段/キュー満杯=**非ブロッキングで「入らなかった」を
      返し**アービタが繰り延べ。**全て診断行に計数**。
- 実装計画書 §2 部品表: 「レプリカごとに AsyncClient+Limits(64,64,None)+Semaphore(64)」。
- 実装計画書 §3 層契約: ``llm`` は ``world``/``agents``/``perception``/``engine`` を import しない。
- 予算宣言表 L6「**64 in-flight/GPU**(bounded)」(ベンチ第3段の並行度の膝 c64)・
  L4「上限 400 万呼/日(o64)」。数値は**表から読む**(コード側に複製しない=``core.budget``)。
- 認知設計書 §1 δ_think レーン表 / §2 U19 思考トークン:
  T1=思考 0・出力 64 tok / T2 routine=2,048 / T2 critical=7,500・インフラ保護
  ``max_tokens = ceil(1.5*B_world)+96``・``stop_reason=="length"`` は ``infra_clip`` 計数。
- 運用設計書 §1.2 LLM艦隊行(``cache_salt``・``prefix_caching_hash_algo``)・§2.4
  (応答は到着順に適用しない=適用順は ``apply_key`` の昇順。**本モジュールが返す順は非決定**)。
- 行動契約書 §1(2行形)・§7(未定義行動5段)。

**親の指示との差分(黙って解決しない)— in-flight 上限の分母**
    指示は「``max_in_flight`` 合計 L6=64(予算行を読む)」。ところが**予算行 L6 の文面は
    「64 in-flight/GPU(bounded)」**(=レプリカごと)で、実装計画書 §2 部品表も
    「レプリカごとに AsyncClient+Limits(64,64,None)+**Semaphore(64)**」と書いている。
    合計 64 にすると 7 レプリカで 1 台あたり 9 並行=ベンチ第3段の膝 c64 を大きく下回り、
    L4(400 万呼/日)が成立しない。そこで
      - ``per_replica_in_flight`` = 予算行 L6 の実数(=64/GPU・表から読む)
      - ``max_in_flight``(合計)= ``per_replica × レプリカ数``(既定・明示指定で上書き可)
    とした。**合計 64 に寄せる判断は親**(``FleetConfig(max_in_flight=64)`` で即座に切替可)。

層契約でできないこと(**黙って解決しない**)
    - ``engine.llm_bridge.LLMBridge`` / ``RenderedPrompt`` / ``engine.tape.TapeRow`` /
      ``agents.state.ResultCode`` は engine・agents 層にあるため import できない。よって
      ・入口は本モジュールの ``LLMCall``(呼び出し側が ``RenderedPrompt`` から詰める)
      ・テープは ``TapeSink`` プロトコル + ``tape_row_factory``(``engine.tape.TapeRow`` を
        呼び出し側が渡す=依存性逆転。``llm.TapeLookup`` と同じ手口)
      ・``ResultCode`` への写像は従来どおり ``engine.commit`` が行う(本モジュールは
        ``action_code``/``target``/``undefined_stage`` までを返す)
      ・δ_think の**秒→tick 換算は engine 側**(``engine.llm_bridge.delta_think_ticks``)。
        本モジュールは ``lane`` を素通しし、レーンから決まるのは **max_tokens と
        enable_thinking だけ**。``LANE_THINK_TOKENS`` は層契約のための複製で、
        ``tests/llm/test_fleet_contract.py`` の等価テストが engine 側と同値に固定する。

逐次ループ宣言(P4・実装計画書 §6)
- ``plan_batch``: 呼数ぶんのループ 1 本(1 tick の選抜=平均 35 呼・L4 の制御目標)。
- ``FleetClient.submit``: 同上(発射のスケジュール)。``poll``/``drain``: 完了件数ぶん。
- ``_run_call``: 1 呼につき最大 3 試行(接続エラー時)+書式再生成 1 回=定数回。
- ストリーミング解析は 1 応答のチャンク数ぶん(出力 64 tok=数十行)。
いずれも個体数・セル数に比例しない。

expedient(本モジュール分・登録簿 §8「C6 艦隊接続」へ転記)
- TTFT/e2e の既定値(60 s/300 s)は §7 の expedient をそのまま採る。**TTFT の定義**は
  「最初の ``data:`` 行が届くまで」(非ストリーミングでは e2e と同値に潰れる)。
- 接続エラーの類別: 送受信例外・HTTP 5xx・429 を「接続エラー」に含める(§7 は「接続エラー」
  としか書いていない)。4xx(429 以外)と本文不正は再試行しない ``error_other``。
- **別レプリカ = ``(primary + 1) mod N``**(``tools/gen/fleet_gen.py`` の先例に合わせた)。
- least-in-flight の発動条件=「割当先が per-replica 上限に達している」または
  「最小との差 ≥ ``imbalance_threshold``(既定 8)」。閾値の出所なし。
- 同一(セル, 5分帯)グループの**同一レプリカ回避**は、``xxhash(call_id) mod N`` を
  第一とし、衝突した後続だけを次の空きレプリカへずらす(§7 の配分規則を壊さない最小の補正)。
- seed 導出 = ``xxh64(call_id, seed=run_seed) & 0x7fffffff``(§7 は「seed=hash(call_id, run_seed)」
  としか書いていない)。
- ``cache_salt`` 導出 = ``blake3("shibuya.cache_salt" ‖ 0x1F ‖ mode ‖ 0x1F ‖ run_id)`` の先頭 16 B。
  設計書は「モード別 cache_salt を manifest に記録」までしか定めていない。
- 待ち行列容量(既定=合計 in-flight 上限 × 4)・レイテンシ標本のリング長(既定 50,000)。
- ``structured_outputs`` は**使わない**(本線は 2 行形パーサ=知覚契約書 §2.5)。
"""

from __future__ import annotations

import asyncio
import json
import math
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Final, Mapping, Protocol, Sequence, runtime_checkable

import httpx

from shibuya.core.budget import budget_by_id, load_budget_table
from shibuya.core.hashing import blake3_hex, sha256_cbor, xxh64
from shibuya.llm import (
    ACTION_CODES,
    UNDEFINED_ACTION,
    LLMRequest,
    LLMResponse,
    ParseResult,
    Target,
    UndefinedActionRegistry,
    estimate_tokens,
    parse_two_line,
)
from shibuya.llm.contract import NO_TARGET_VALUE
from shibuya.manifest.schema import Mode

__all__ = [
    "LANE_THINK_TOKENS",
    "LANE_TIER",
    "INFRA_CLIP_FACTOR",
    "INFRA_CLIP_SLACK",
    "DEFAULT_TTFT_TIMEOUT_S",
    "DEFAULT_E2E_TIMEOUT_S",
    "DEFAULT_TEMPERATURE",
    "DEFAULT_T1_MAX_TOKENS",
    "DEFAULT_IMBALANCE_THRESHOLD",
    "CACHE_SALT_DOMAIN",
    "Outcome",
    "FleetConfig",
    "LLMCall",
    "LLMResult",
    "Deferred",
    "FleetDeferredError",
    "TapeSink",
    "FleetTapeRow",
    "DEBUG_FILENAME",
    "DEFAULT_DEBUG_MAX_ROWS",
    "FleetClient",
    "FleetBridge",
    "FleetBridgeResult",
    "cache_salt_for",
    "seed_for",
    "route_primary",
    "plan_batch",
    "max_tokens_for",
    "l6_in_flight_per_gpu",
    "l4_calls_per_day",
    "split_system_user",
    "call_from_request",
]

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

#: レーン → デコード階層(manifest ``llm_fleet.decoding{T1,T2}`` の欄名)。
LANE_TIER: Final[Mapping[str, str]] = {
    "L0": "T1",
    "L1": "T1",
    "L2": "T2",
    "L3": "T2",
    "L4": "T1",
}

#: U19 ③ インフラ保護 ``max_tokens = ceil(1.5*B_world) + 96``。
INFRA_CLIP_FACTOR: Final[float] = 1.5
INFRA_CLIP_SLACK: Final[int] = 96

#: §7 の expedient。
DEFAULT_TTFT_TIMEOUT_S: Final[float] = 60.0
DEFAULT_E2E_TIMEOUT_S: Final[float] = 300.0

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

#: least-in-flight の発動閾値(expedient)。
DEFAULT_IMBALANCE_THRESHOLD: Final[int] = 8

#: 書式デバッグ jsonl の名前と既定の行数上限(診断のみ・既定 off)。
DEBUG_FILENAME: Final[str] = "format_debug.jsonl"
DEFAULT_DEBUG_MAX_ROWS: Final[int] = 5_000

#: ``cache_salt`` 導出のドメイン語(``core.rng`` の鍵導出と同じ 0x1F 区切りの作法)。
CACHE_SALT_DOMAIN: Final[str] = "shibuya.cache_salt"

_SEP: Final[bytes] = b"\x1f"

#: 予算表 L6 の宣言値セルから「64 in-flight」を取る(``parse_limit`` は比較子つきしか拾わない)。
_L6_RE = re.compile(r"(\d[\d,]*)\s*in-flight")
#: 予算表 L4 の宣言値セルから「400万呼/日」を取る。
_L4_RE = re.compile(r"(\d[\d,]*)\s*(万|億)?\s*呼/日")
_MULT: Final[Mapping[str, int]] = {"": 1, "万": 10_000, "億": 100_000_000}


def l6_in_flight_per_gpu(budget_md: str | None = None) -> int:
    """予算行 L6「**64 in-flight/GPU**(bounded)」を読む(数値をコード側に複製しない)。

    Raises:
        ValueError: L6 行が読めなかった(表の文面が変わった=改版の合図)。
    """
    row = budget_by_id(load_budget_table(budget_md))["L6"]
    m = _L6_RE.search(row.declared)
    if m is None:
        raise ValueError(f"予算行 L6 から in-flight 数が読めない: {row.declared!r}")
    return int(m.group(1).replace(",", ""))


def l4_calls_per_day(budget_md: str | None = None) -> int:
    """予算行 L4「上限 400 万呼/日(o64)」を読む(憲法1 の監査点)。"""
    row = budget_by_id(load_budget_table(budget_md))["L4"]
    m = _L4_RE.search(row.declared)
    if m is None:
        raise ValueError(f"予算行 L4 から呼数上限が読めない: {row.declared!r}")
    return int(m.group(1).replace(",", "")) * _MULT[m.group(2) or ""]


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


#: 「答えが返らなかった」帰結=呼び出し側(アービタ)が**繰り延べる**もの(憲法1: 破棄禁止)。
DEFERRED_OUTCOMES: Final[frozenset[Outcome]] = frozenset(
    {Outcome.DEFERRED_TIMEOUT, Outcome.DEFERRED_QUEUE_FULL, Outcome.ERROR_OTHER}
)


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


# ---------------------------------------------------------------- 設定


@dataclass(frozen=True)
class FleetConfig:
    """艦隊設定(manifest ``llm_fleet`` 節のうちクライアントが要る分)。

    Attributes:
        endpoints: ``http://host:port`` のレプリカ列(既定艦隊は 7 本=``mod 7``)。
        model: served-model-name(空なら ``discover_model`` で ``/v1/models`` の先頭)。
        mode: 実行モード(``cache_salt`` の勘定分離に効く)。
        run_id: manifest の自己ハッシュ(``cache_salt`` の第2要素)。
        run_seed: seed 導出の鍵(既定 0)。
        cache_salt: 明示指定(空なら ``mode``/``run_id`` から導出)。
        per_replica_in_flight: 予算行 L6(``None``=表から読む=64/GPU)。
        max_in_flight: 合計上限(``None``=``per_replica × レプリカ数``)。
        queue_capacity: 受理待ち+実行中の合計上限(``None``=``max_in_flight × 4``)。
            これを超える ``submit`` は**非ブロッキングで** ``DEFERRED_QUEUE_FULL`` を返す。
        ttft_timeout_s / e2e_timeout_s: §7 の expedient(60 s / 300 s)。
        temperature / top_p / t1_max_tokens: T1 のデコード設定
            (既定 ``DEFAULT_TEMPERATURE``=0.7 / 1.0 / ``DEFAULT_T1_MAX_TOKENS``=96)。
        t2_temperature / t2_top_p: T2 のデコード設定(``None``=T1 と同じ)。
        enable_thinking: T1 は False 固定(U19: 思考 0)。T2 帯は本欄によらず True。
        stream: SSE ストリーミング(TTFT を実測するため既定 True)。
        format_retry: 書式エラー時に温度 0 で 1 回だけ再生成する(§7)。
        group_spread: 同一(セル, 5分帯)を同一レプリカに寄せない(BN-4)。
        imbalance_threshold: least-in-flight の発動閾値。
        latency_samples: レイテンシ標本のリング長(p50/p99 の母数)。
    """

    endpoints: tuple[str, ...]
    model: str = ""
    mode: Mode = Mode.SMOKE
    run_id: str = ""
    run_seed: int = 0
    cache_salt: str = ""
    per_replica_in_flight: int | None = None
    max_in_flight: int | None = None
    queue_capacity: int | None = None
    ttft_timeout_s: float = DEFAULT_TTFT_TIMEOUT_S
    e2e_timeout_s: float = DEFAULT_E2E_TIMEOUT_S
    connect_timeout_s: float = 10.0
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = 1.0
    t1_max_tokens: int = DEFAULT_T1_MAX_TOKENS
    t2_temperature: float | None = None
    t2_top_p: float | None = None
    enable_thinking: bool = False
    stream: bool = True
    format_retry: bool = True
    group_spread: bool = True
    imbalance_threshold: int = DEFAULT_IMBALANCE_THRESHOLD
    latency_samples: int = 50_000
    budget_md: str | None = None

    def __post_init__(self) -> None:
        if not self.endpoints:
            raise ValueError("endpoints が空(レプリカが 1 本も無い)")
        if len(set(self.endpoints)) != len(self.endpoints):
            raise ValueError(f"endpoints が重複している: {self.endpoints}")
        if self.ttft_timeout_s <= 0 or self.e2e_timeout_s <= 0:
            raise ValueError("タイムアウトは正の秒数")
        if self.ttft_timeout_s > self.e2e_timeout_s:
            raise ValueError("TTFT タイムアウトは e2e 以下でなければならない")

    @property
    def n_replicas(self) -> int:
        return len(self.endpoints)

    def resolved_cache_salt(self) -> str:
        """明示 ``cache_salt`` があればそれ、無ければ ``(mode, run_id)`` から導出。"""
        return self.cache_salt or cache_salt_for(self.mode, self.run_id)

    def resolved_per_replica(self) -> int:
        """1 レプリカあたり in-flight 上限(``None`` なら予算行 L6 を読む)。"""
        if self.per_replica_in_flight is not None:
            return int(self.per_replica_in_flight)
        return l6_in_flight_per_gpu(self.budget_md)

    def resolved_max_in_flight(self) -> int:
        if self.max_in_flight is not None:
            return int(self.max_in_flight)
        return self.resolved_per_replica() * self.n_replicas

    def resolved_queue_capacity(self) -> int:
        if self.queue_capacity is not None:
            return int(self.queue_capacity)
        return self.resolved_max_in_flight() * 4

    def manifest_fields(self) -> Mapping[str, Any]:
        """manifest ``llm_fleet`` に記録する欄(§7「manifest に記録」)。"""
        return {
            "prefix_caching_hash_algo": "sha256_cbor",
            "cache_salt": self.resolved_cache_salt(),
            "mode": self.mode.value if isinstance(self.mode, Mode) else str(self.mode),
            "routing": {"rule": "xxhash(call_id) mod N", "cell_affinity": False},
            "n_replicas": self.n_replicas,
            "in_flight_cap_per_replica": self.resolved_per_replica(),
            "in_flight_cap_total": self.resolved_max_in_flight(),
            "queue_capacity": self.resolved_queue_capacity(),  # 受理待ち枠(C7 D-55/D-58 の律速)
            "ttft_timeout_s": self.ttft_timeout_s,
            "e2e_timeout_s": self.e2e_timeout_s,
            # 運用設計書 §1.2 の ``decoding{T1,T2}`` と同じ欄形(下位欄も同じ 4 つ)。
            "decoding": {
                "T1": {
                    "temperature": float(self.temperature),
                    "top_p": float(self.top_p),
                    "max_tokens": int(max_tokens_for("L1", self.t1_max_tokens)),
                    "seed": "xxh64(call_id, run_seed)",
                },
                "T2": {
                    "temperature": float(
                        self.temperature if self.t2_temperature is None else self.t2_temperature
                    ),
                    "top_p": float(self.top_p if self.t2_top_p is None else self.t2_top_p),
                    "max_tokens": int(max_tokens_for("L2", self.t1_max_tokens)),
                    "seed": "xxh64(call_id, run_seed)",
                },
            },
            "stream": bool(self.stream),
            "format_retry": bool(self.format_retry),
        }


# ---------------------------------------------------------------- 順序制御(純関数)


def plan_batch(
    calls: Sequence[LLMCall],
    n_replicas: int,
    *,
    in_flight: Sequence[int] | None = None,
    per_replica_cap: int = 64,
    imbalance_threshold: int = DEFAULT_IMBALANCE_THRESHOLD,
    group_spread: bool = True,
) -> tuple[tuple[LLMCall, int], ...]:
    """1 バッチの発射順とレプリカ割当を決める**純関数**(実装計画書 §7 順序制御)。

    規則(適用順)
      1. **グループ化**: ``(cell, 5分帯)`` で束ね、``(cell, time_bucket, call_id)`` 昇順で並べる
         =同一(セル, 時間帯)の呼が**隣り合って同時に発射される**。
      2. **一次配分**: ``xxhash(call_id) mod N``。
      3. **同一 GPU 回避**(BN-4・``group_spread``): 同じグループの後続が同じレプリカに
         当たったら、次の未使用レプリカへずらす(グループ員数 > N なら使用集合を畳んで再開)。
      4. **least-in-flight**: 割当先が ``per_replica_cap`` に達している、または最小との差が
         ``imbalance_threshold`` 以上なら、最小負荷レプリカ(同点は index 昇順)へ移す。

    Args:
        calls: この tick の呼。
        n_replicas: レプリカ数。
        in_flight: 現在の実行中件数(``None``=全 0)。
        per_replica_cap: 1 レプリカの in-flight 上限(予算行 L6)。
        imbalance_threshold: least-in-flight の発動閾値。
        group_spread: 3 の補正を効かせるか(ablation 用に切れる)。

    Returns:
        ``((call, replica_index), …)``。**同じ入力からは常に同じ出力**(T3/T4 の性質)。

    逐次ループ宣言(P4): 呼数ぶんのループ 1 本。
    """
    if n_replicas <= 0:
        raise ValueError("n_replicas は 1 以上")
    load = [int(x) for x in (in_flight if in_flight is not None else [0] * n_replicas)]
    if len(load) != n_replicas:
        raise ValueError("in_flight の長さがレプリカ数と違う")

    ordered = sorted(calls, key=lambda c: (int(c.cell), int(c.time_bucket), c.call_id))
    used_by_group: dict[tuple[int, int], set[int]] = {}
    out: list[tuple[LLMCall, int]] = []
    for call in ordered:  # 逐次ループ宣言: 呼数ぶん(1 tick 平均 35)
        chosen = route_primary(call.call_id, n_replicas)
        if group_spread and n_replicas > 1:
            used = used_by_group.setdefault(call.group_key, set())
            if len(used) >= n_replicas:
                used.clear()
            if chosen in used:
                for k in range(1, n_replicas):
                    cand = (chosen + k) % n_replicas
                    if cand not in used:
                        chosen = cand
                        break
            used.add(chosen)
        lo = min(load)
        if load[chosen] >= per_replica_cap or (load[chosen] - lo) >= imbalance_threshold:
            chosen = load.index(lo)
        load[chosen] += 1
        out.append((call, chosen))
    return tuple(out)


# ---------------------------------------------------------------- テープ(依存性逆転)


@runtime_checkable
class TapeSink(Protocol):
    """録画テープの書き出し口(``engine.tape.TapeWriter`` がこの形を満たす)。"""

    def intern_block(self, text: str, tokens: int) -> str:  # pragma: no cover - 契約のみ
        ...

    def append(self, row: Any) -> None:  # pragma: no cover - 契約のみ
        ...


@dataclass(frozen=True)
class FleetTapeRow:
    """``engine.tape.TapeRow`` と**同じ欄名**の既定行(テープ実体を注入しないときの器)。

    末尾 3 欄は D-58(テープ版2)。``deferred=1`` の行は「答えが返らなかった 1 呼」で、
    ``observed_tick`` はエンジンがその帰結を**観測した** tick(発射 tick とは別物)。
    """

    call_id: str
    agent_id: int
    tick: int
    wake_class: int
    prompt_hash: str
    block_ids: tuple[str, ...]
    params_hash: str
    response: str
    tokens_in: int = 0
    tokens_out: int = 0
    deferred: int = 0
    deferred_reason: str = ""
    observed_tick: int = -1


# ---------------------------------------------------------------- 診断


class _Latency:
    """レイテンシ標本(直近 ``maxlen`` 件のリング)。p50/p99 は線形補間なしの順位統計。"""

    __slots__ = ("_d",)

    def __init__(self, maxlen: int) -> None:
        self._d: deque[float] = deque(maxlen=max(1, int(maxlen)))

    def add(self, v: float) -> None:
        self._d.append(float(v))

    def quantile(self, q: float) -> float:
        if not self._d:
            return 0.0
        xs = sorted(self._d)
        idx = min(len(xs) - 1, max(0, int(math.ceil(q * len(xs))) - 1))
        return xs[idx]

    def __len__(self) -> int:
        return len(self._d)


# ---------------------------------------------------------------- クライアント


class _RetryableHTTP(Exception):
    """再試行してよい HTTP 応答(5xx・429)。"""


class _FatalHTTP(Exception):
    """再試行しない HTTP 応答(4xx・本文不正)。"""


#: 「接続エラー」= §7 の再試行対象(同一レプリカ1回→別レプリカ1回)。
#: ``httpx.NetworkError`` が Connect/Read/Write/Close の親・``PoolTimeout``/``ConnectTimeout`` は
#: 「繋がらなかった」側なので**タイムアウトではなく接続エラー**に入れる(expedient)。
_RETRYABLE_EXC: Final[tuple[type[BaseException], ...]] = (
    _RetryableHTTP,
    httpx.ConnectTimeout,
    httpx.PoolTimeout,
    httpx.NetworkError,
    httpx.RemoteProtocolError,
)


def _classify(exc: BaseException) -> str:
    """例外 → ``"timeout"``(繰り延べ) / ``"retryable"``(接続エラー) / ``"fatal"``(error_other)。

    順序が意味を持つ: 組み込み ``TimeoutError`` は ``OSError`` の派生・
    ``httpx.ConnectTimeout``/``PoolTimeout`` は ``httpx.TimeoutException`` の派生。
    """
    if isinstance(exc, _FatalHTTP):
        return "fatal"
    if isinstance(exc, _RETRYABLE_EXC):
        return "retryable"
    if isinstance(exc, (asyncio.TimeoutError, httpx.TimeoutException)):
        return "timeout"
    if isinstance(exc, OSError):
        return "retryable"
    return "fatal"


class _Replica:
    __slots__ = ("index", "endpoint", "client", "sem")

    def __init__(self, index: int, endpoint: str, client: httpx.AsyncClient, limit: int) -> None:
        self.index = index
        self.endpoint = endpoint
        self.client = client
        self.sem = asyncio.Semaphore(limit)


class FleetClient:
    """実 vLLM 艦隊への非同期クライアント(engine の同期ループから使う)。

    使い方(engine 側)::

        client = FleetClient(FleetConfig(endpoints=(...,), model="Qwen3-8B-INT8"))
        deferred = client.submit(calls)      # 非ブロッキング。返るのは「入らなかった」分だけ
        ...                                  # tick の残りの処理(エンジンは止まらない)
        done = client.poll()                 # 届いた分を受け取る(順序は非決定)

    ``LLMClient`` プロトコル(``complete``)も満たすので、既存の
    ``engine.llm_bridge.LLMBridge(llm=client)`` にそのまま挿さる(**1 呼ずつの同期経路**=
    スモーク/デバッグ用。繰り延べは例外 ``FleetDeferredError`` になる)。

    Args:
        config: 艦隊設定。
        transport_factory: ``endpoint -> httpx.AsyncBaseTransport``(テストの偽 vLLM 用)。
        format_check: 応答本文 → 書式 OK か(既定=2行形パーサ)。``None`` で再生成を切る。
    """

    def __init__(
        self,
        config: FleetConfig,
        *,
        transport_factory: Callable[[str], httpx.AsyncBaseTransport] | None = None,
        format_check: Callable[[str], bool] | None = None,
    ) -> None:
        self.config = config
        self.cache_salt = config.resolved_cache_salt()
        self.per_replica = config.resolved_per_replica()
        self.max_in_flight = config.resolved_max_in_flight()
        self.queue_capacity = config.resolved_queue_capacity()
        self.model = config.model
        self._transport_factory = transport_factory
        self._format_check: Callable[[str], bool] | None = (
            format_check if format_check is not None else (_format_ok if config.format_retry else None)
        )
        if not config.format_retry:
            self._format_check = None

        n = config.n_replicas
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)
        self._in_flight = [0] * n
        self._peak_in_flight = [0] * n
        self._calls_per_replica = [0] * n
        self._outstanding = 0
        self._results: list[LLMResult | Deferred] = []
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._replicas: list[_Replica] = []
        self._closed = False

        # ---- 診断計数 ----
        self.n_submitted = 0
        self.n_ok = 0
        self.n_format_retry = 0
        self.n_format_retry_ok = 0
        self.n_deferred_timeout = 0
        self.n_deferred_queue_full = 0
        self.n_error_retried_ok = 0
        self.n_error_other = 0
        self.n_retry_same = 0
        self.n_retry_other = 0
        self.n_infra_clip = 0
        self.n_no_alternate_replica = 0
        self.tokens_in = 0
        self.tokens_out = 0
        self._ttft = _Latency(config.latency_samples)
        self._e2e = _Latency(config.latency_samples)

    # ------------------------------------------------------------ ループ管理
    def start(self) -> None:
        """背景スレッド(イベントループ)を立てる。``submit`` が呼べば自動で呼ばれる。"""
        if self._thread is not None:
            return
        if self._closed:
            raise RuntimeError("close() 済みの FleetClient は再利用できない")
        ready = threading.Event()

        def _run() -> None:
            loop = asyncio.new_event_loop()
            self._loop = loop
            asyncio.set_event_loop(loop)
            loop.call_soon(ready.set)
            try:
                loop.run_forever()
            finally:
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                finally:
                    loop.close()

        self._thread = threading.Thread(target=_run, name="shibuya-fleet", daemon=True)
        self._thread.start()
        ready.wait(timeout=10.0)
        if self._loop is None:  # pragma: no cover - 起動失敗
            raise RuntimeError("艦隊クライアントのイベントループが起動しなかった")
        self._call_soon_sync(self._setup_clients())

    def _call_soon_sync(self, coro: Any, timeout: float | None = 30.0) -> Any:
        assert self._loop is not None
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)

    async def _setup_clients(self) -> None:
        cfg = self.config
        limits = httpx.Limits(
            max_connections=self.per_replica,
            max_keepalive_connections=self.per_replica,
            keepalive_expiry=None,
        )
        timeout = httpx.Timeout(
            connect=cfg.connect_timeout_s,
            read=cfg.e2e_timeout_s,
            write=cfg.e2e_timeout_s,
            pool=cfg.e2e_timeout_s,
        )
        self._replicas = []
        for i, ep in enumerate(cfg.endpoints):
            transport = self._transport_factory(ep) if self._transport_factory is not None else None
            client = httpx.AsyncClient(
                base_url=ep.rstrip("/"), limits=limits, timeout=timeout, transport=transport
            )
            self._replicas.append(_Replica(i, ep.rstrip("/"), client, self.per_replica))

    def close(self) -> None:
        """背景スレッドと全 AsyncClient を閉じる(冪等)。"""
        if self._closed:
            return
        self._closed = True
        if self._loop is not None and self._thread is not None:
            try:
                self._call_soon_sync(self._close_clients(), timeout=30.0)
            finally:
                self._loop.call_soon_threadsafe(self._loop.stop)
                self._thread.join(timeout=10.0)
        self._loop = None
        self._thread = None

    async def _close_clients(self) -> None:
        for rep in self._replicas:
            await rep.client.aclose()
        self._replicas = []

    def __enter__(self) -> "FleetClient":
        self.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ------------------------------------------------------------ モデル発見
    def discover_model(self, timeout: float = 30.0) -> str:
        """``/v1/models`` の先頭 id を採る(``config.model`` が空のとき)。"""
        self.start()
        model = self._call_soon_sync(self._discover_model(), timeout=timeout)
        self.model = model
        return model

    async def _discover_model(self) -> str:
        last: Exception | None = None
        for rep in self._replicas:
            try:
                r = await rep.client.get("/v1/models")
                r.raise_for_status()
                data = r.json().get("data", [])
                if data:
                    return str(data[0]["id"])
            except Exception as exc:  # noqa: BLE001 - どのレプリカでも良い
                last = exc
        raise RuntimeError(f"/v1/models からモデル名が取れない: {last}")

    # ------------------------------------------------------------ 発射
    def submit(self, calls: Sequence[LLMCall]) -> list[LLMResult | Deferred]:
        """呼を発射する(**非ブロッキング**)。

        Returns:
            その場で決まった帰結だけ。現状は「キューに入らなかった」
            ``Deferred(DEFERRED_QUEUE_FULL)`` のみ(§7)。受理された呼の答えは
            ``poll``/``drain`` から届く。

        Note:
            結果の**返る順は非決定**(レプリカの速さで前後する)。決定性は
            engine 側の ``apply_key=(t_apply, event_class, blake3(...))`` 昇順の
            適用(運用設計書 §2.4)が担保する。
        """
        if not calls:
            return []
        self.start()
        if self.model == "":
            self.discover_model()
        with self._lock:
            snapshot = list(self._in_flight)
            room = self.queue_capacity - self._outstanding
        plan = plan_batch(
            calls,
            self.config.n_replicas,
            in_flight=snapshot,
            per_replica_cap=self.per_replica,
            imbalance_threshold=self.config.imbalance_threshold,
            group_spread=self.config.group_spread,
        )
        rejected: list[LLMResult | Deferred] = []
        accepted: list[tuple[LLMCall, int]] = []
        for call, replica in plan:  # 逐次ループ宣言: 呼数ぶん
            if len(accepted) >= room:
                rejected.append(
                    Deferred(
                        call=call,
                        outcome=Outcome.DEFERRED_QUEUE_FULL,
                        reason=f"queue_capacity={self.queue_capacity}",
                        replica=replica,
                    )
                )
                continue
            accepted.append((call, replica))
        with self._lock:
            self.n_submitted += len(plan)
            self.n_deferred_queue_full += len(rejected)
            for _, replica in accepted:
                self._in_flight[replica] += 1
                self._peak_in_flight[replica] = max(
                    self._peak_in_flight[replica], self._in_flight[replica]
                )
                self._outstanding += 1
        assert self._loop is not None
        for call, replica in accepted:
            asyncio.run_coroutine_threadsafe(self._run_call(call, replica), self._loop)
        return rejected

    def poll(self) -> list[LLMResult | Deferred]:
        """届いている分を取り出す(**非ブロッキング**・空なら空リスト)。"""
        with self._lock:
            out = self._results
            self._results = []
        return out

    def drain(self, timeout: float | None = None) -> list[LLMResult | Deferred]:
        """実行中が空になるまで待って全部取り出す(スモーク/テスト用)。

        Args:
            timeout: 上限秒(``None``=``e2e_timeout_s + 30``)。時間切れでも**捨てない**
                (残りは次の ``poll`` で届く)。
        """
        limit = self.config.e2e_timeout_s + 30.0 if timeout is None else float(timeout)
        deadline = time.monotonic() + limit
        with self._cond:
            self._cond.wait_for(
                lambda: self._outstanding == 0, timeout=max(0.0, deadline - time.monotonic())
            )
            out = self._results
            self._results = []
        return out

    def wait_idle(self, timeout: float | None = None) -> bool:
        """実行中が 0 になるまで待つ(結果は取り出さない)。"""
        limit = self.config.e2e_timeout_s + 30.0 if timeout is None else float(timeout)
        with self._cond:
            return bool(
                self._cond.wait_for(lambda: self._outstanding == 0, timeout=max(0.0, limit))
            )

    @property
    def outstanding(self) -> int:
        with self._lock:
            return self._outstanding

    @property
    def in_flight(self) -> tuple[int, ...]:
        with self._lock:
            return tuple(self._in_flight)

    # ------------------------------------------------------------ 1 呼の本体
    def _finish(self, res: LLMResult | Deferred, replica: int) -> None:
        with self._cond:
            self._in_flight[replica] -= 1
            self._outstanding -= 1
            self._results.append(res)
            self._cond.notify_all()

    def _move_replica(self, frm: int, to: int) -> None:
        with self._lock:
            self._in_flight[frm] -= 1
            self._in_flight[to] += 1
            self._peak_in_flight[to] = max(self._peak_in_flight[to], self._in_flight[to])

    def _payload(self, call: LLMCall, *, force_greedy: bool = False) -> dict[str, Any]:
        cfg = self.config
        tier = LANE_TIER[call.lane]
        temp = cfg.temperature if tier == "T1" else (cfg.t2_temperature or cfg.temperature)
        top_p = cfg.top_p if tier == "T1" else (cfg.t2_top_p or cfg.top_p)
        if force_greedy:
            temp, top_p = 0.0, 1.0
        messages: list[dict[str, str]] = []
        if call.system:
            messages.append({"role": "system", "content": call.system})
        messages.append({"role": "user", "content": call.user_text})
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens_for(call.lane, cfg.t1_max_tokens),
            "temperature": float(temp),
            "top_p": float(top_p),
            "seed": seed_for(call.call_id, cfg.run_seed),
            "chat_template_kwargs": {"enable_thinking": LANE_TIER[call.lane] == "T2"},
        }
        if self.cache_salt:
            payload["cache_salt"] = self.cache_salt
        if cfg.stream:
            payload["stream"] = True
            payload["stream_options"] = {"include_usage": True}
        if call.params_extra:
            payload.update(dict(call.params_extra))
        return payload

    async def _run_call(self, call: LLMCall, replica: int) -> None:
        cfg = self.config
        n = cfg.n_replicas
        alternate = (replica + 1) % n
        if n == 1:
            with self._lock:
                self.n_no_alternate_replica += 1
        # §7「接続エラー=同一レプリカ1回→別レプリカ1回」= 初回 + 同一 1 + 別 1
        order = [replica, replica, alternate]
        current = replica
        last_reason = ""
        attempts = 0
        t_start = time.perf_counter()
        try:
            for step, target in enumerate(order):
                if target != current:
                    self._move_replica(current, target)
                    current = target
                    with self._lock:
                        self.n_retry_other += 1
                elif step == 1:
                    with self._lock:
                        self.n_retry_same += 1
                rep = self._replicas[current]
                attempts += 1
                try:
                    async with rep.sem:
                        text, finish, ptok, ctok, ttft, e2e = await self._attempt(
                            rep, self._payload(call)
                        )
                except Exception as exc:  # noqa: BLE001 - 分類してから捌く
                    kind = _classify(exc)
                    if kind == "retryable":  # §7 接続エラー = 同一1回 → 別1回
                        last_reason = f"{type(exc).__name__}: {exc}"
                        continue
                    if kind == "timeout":
                        # §7: タイムアウトは**繰り延べ**(再試行しない・破棄しない=憲法1)
                        with self._lock:
                            self.n_deferred_timeout += 1
                        outcome_d, reason_d = (
                            Outcome.DEFERRED_TIMEOUT,
                            f"timeout ttft={cfg.ttft_timeout_s}s e2e={cfg.e2e_timeout_s}s"
                            f" ({type(exc).__name__})",
                        )
                    else:
                        with self._lock:
                            self.n_error_other += 1
                        outcome_d, reason_d = (
                            Outcome.ERROR_OTHER,
                            f"{type(exc).__name__}: {exc}",
                        )
                    self._finish(
                        Deferred(
                            call=call,
                            outcome=outcome_d,
                            reason=reason_d,
                            replica=current,
                            attempts=attempts,
                            e2e_s=time.perf_counter() - t_start,
                        ),
                        current,
                    )
                    return

                outcome = Outcome.ERROR_RETRIED_OK if attempts > 1 else Outcome.OK
                format_retried = False
                first_text = ""
                # §7: 書式エラー = 温度 0 で 1 回再生成
                if self._format_check is not None and not self._format_check(text):
                    with self._lock:
                        self.n_format_retry += 1
                    format_retried = True
                    first_text = text  # 初回の生応答を残す(診断・テープには載らない)
                    try:
                        async with rep.sem:
                            r2 = await self._attempt(rep, self._payload(call, force_greedy=True))
                        text, finish, ptok2, ctok2, ttft2, e2e2 = r2
                        ptok += ptok2
                        ctok += ctok2
                        e2e += e2e2
                        ttft = min(ttft, ttft2)
                        attempts += 1
                        if self._format_check(text):
                            with self._lock:
                                self.n_format_retry_ok += 1
                            outcome = Outcome.FORMAT_RETRY_OK
                    except Exception:  # noqa: BLE001
                        # 再生成が落ちても**元の応答は捨てない**(書式エラーのまま先へ=段0-1 へ)
                        pass

                infra_clip = finish == "length"
                with self._lock:
                    # 終端計数は**排他**(合計が呼数に一致する=診断行の帳尻)。
                    # 接続エラー再試行と書式再生成が重なった呼は FORMAT_RETRY_OK 側に数え、
                    # 接続再試行の事実は fleet_conn_retry_* に残す。
                    if outcome is Outcome.OK:
                        self.n_ok += 1
                    elif outcome is Outcome.ERROR_RETRIED_OK:
                        self.n_error_retried_ok += 1
                    self.tokens_in += int(ptok)
                    self.tokens_out += int(ctok)
                    self._calls_per_replica[current] += 1
                    self.n_infra_clip += int(infra_clip)
                    self._ttft.add(ttft)
                    self._e2e.add(e2e)
                self._finish(
                    LLMResult(
                        call=call,
                        text=text,
                        outcome=outcome,
                        replica=current,
                        endpoint=rep.endpoint,
                        tokens_in=int(ptok),
                        tokens_out=int(ctok),
                        ttft_s=float(ttft),
                        e2e_s=float(e2e),
                        attempts=attempts,
                        format_retried=format_retried,
                        first_text=first_text,
                        finish_reason=finish,
                        infra_clip=infra_clip,
                    ),
                    current,
                )
                return
            # 全試行が接続エラー: 破棄せず繰り延べ(憲法1)
            with self._lock:
                self.n_error_other += 1
            self._finish(
                Deferred(
                    call=call,
                    outcome=Outcome.ERROR_OTHER,
                    reason=last_reason or "connection error",
                    replica=current,
                    attempts=attempts,
                    e2e_s=time.perf_counter() - t_start,
                ),
                current,
            )
        except BaseException as exc:  # pragma: no cover - 保険(呼を必ず解放する)
            with self._lock:
                self.n_error_other += 1
            self._finish(
                Deferred(
                    call=call,
                    outcome=Outcome.ERROR_OTHER,
                    reason=f"{type(exc).__name__}: {exc}",
                    replica=current,
                    attempts=attempts,
                ),
                current,
            )

    async def _attempt(
        self, rep: _Replica, payload: Mapping[str, Any]
    ) -> tuple[str, str, int, int, float, float]:
        """1 試行。``(text, finish_reason, tokens_in, tokens_out, ttft_s, e2e_s)``。"""
        if payload.get("stream"):
            return await asyncio.wait_for(
                self._attempt_stream(rep, payload), self.config.e2e_timeout_s
            )
        return await asyncio.wait_for(self._attempt_once(rep, payload), self.config.e2e_timeout_s)

    async def _attempt_once(
        self, rep: _Replica, payload: Mapping[str, Any]
    ) -> tuple[str, str, int, int, float, float]:
        t0 = time.perf_counter()
        r = await rep.client.post("/v1/chat/completions", json=dict(payload))
        _raise_for_status(r.status_code, r.text)
        d = r.json()
        ch = d["choices"][0]
        usage = d.get("usage") or {}
        e2e = time.perf_counter() - t0
        text = ch["message"].get("content") or ""
        return (
            text,
            str(ch.get("finish_reason") or "stop"),
            int(usage.get("prompt_tokens", 0)),
            int(usage.get("completion_tokens", 0) or estimate_tokens(text)),
            e2e,  # 非ストリーミングでは TTFT は e2e に潰れる(expedient)
            e2e,
        )

    async def _attempt_stream(
        self, rep: _Replica, payload: Mapping[str, Any]
    ) -> tuple[str, str, int, int, float, float]:
        cfg = self.config
        t0 = time.perf_counter()
        parts: list[str] = []
        finish = "stop"
        ptok = 0
        ctok = 0
        ttft = 0.0
        async with rep.client.stream("POST", "/v1/chat/completions", json=dict(payload)) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", "replace")
                _raise_for_status(resp.status_code, body)
            lines = resp.aiter_lines()
            first = await asyncio.wait_for(_next_data(lines), cfg.ttft_timeout_s)
            ttft = time.perf_counter() - t0
            chunk = first
            while chunk is not None:
                text_piece, fin, p, c = _read_chunk(chunk)
                if text_piece:
                    parts.append(text_piece)
                if fin:
                    finish = fin
                ptok = p or ptok
                ctok = c or ctok
                chunk = await _next_data(lines)
        text = "".join(parts)
        return (
            text,
            finish,
            ptok,
            ctok or estimate_tokens(text),
            ttft,
            time.perf_counter() - t0,
        )

    # ------------------------------------------------------------ 同期1呼(LLMClient 契約)
    def complete(self, request: LLMRequest) -> LLMResponse:
        """``llm.LLMClient`` 契約(既存 ``engine.llm_bridge.LLMBridge`` へ挿す口)。

        Raises:
            FleetDeferredError: 繰り延べ(タイムアウト・キュー満杯・接続エラー枯渇)。
                同期経路は繰り延べを値で表現できないので**黙って空応答にしない**。
        """
        call = call_from_request(request)
        rejected = self.submit([call])
        if rejected:
            raise FleetDeferredError(rejected[0])  # type: ignore[arg-type]
        deadline = time.monotonic() + self.config.e2e_timeout_s + 30.0
        while True:
            for res in self.drain(timeout=max(0.0, deadline - time.monotonic())):
                if res.call_id != call.call_id:  # pragma: no cover - 同期経路は1呼ずつ
                    with self._lock:
                        self._results.append(res)
                    continue
                if isinstance(res, Deferred):
                    raise FleetDeferredError(res)
                return LLMResponse(
                    text=res.text,
                    tokens_in=int(res.tokens_in) or estimate_tokens(request.prompt),
                    tokens_out=int(res.tokens_out),
                    source=res.source,
                    finish_reason=res.finish_reason,
                )
            if time.monotonic() >= deadline:  # pragma: no cover - 保険
                raise FleetDeferredError(
                    Deferred(call=call, outcome=Outcome.DEFERRED_TIMEOUT, reason="drain deadline")
                )

    # ------------------------------------------------------------ 診断行
    def counters(self) -> Mapping[str, float]:
        """診断行(運用 5 診断行に対応する艦隊側の計数)。"""
        with self._lock:
            n = max(1, self.n_submitted)
            out: dict[str, float] = {
                "fleet_calls": float(self.n_submitted),
                "fleet_ok": float(self.n_ok),
                "fleet_error_retried_ok": float(self.n_error_retried_ok),
                "fleet_format_retry": float(self.n_format_retry),
                "fleet_format_retry_ok": float(self.n_format_retry_ok),
                "fleet_format_retry_rate": self.n_format_retry / n,
                "fleet_answered": float(
                    self.n_ok + self.n_format_retry_ok + self.n_error_retried_ok
                ),
                "fleet_deferred_timeout": float(self.n_deferred_timeout),
                "fleet_deferred_queue_full": float(self.n_deferred_queue_full),
                "fleet_deferred_rate": (self.n_deferred_timeout + self.n_deferred_queue_full) / n,
                "fleet_error_other": float(self.n_error_other),
                "fleet_conn_retry_same": float(self.n_retry_same),
                "fleet_conn_retry_other": float(self.n_retry_other),
                "fleet_no_alternate_replica": float(self.n_no_alternate_replica),
                "fleet_infra_clip": float(self.n_infra_clip),
                "fleet_tokens_in": float(self.tokens_in),
                "fleet_tokens_out": float(self.tokens_out),
                "fleet_ttft_p50": self._ttft.quantile(0.50),
                "fleet_ttft_p99": self._ttft.quantile(0.99),
                "fleet_e2e_p50": self._e2e.quantile(0.50),
                "fleet_e2e_p99": self._e2e.quantile(0.99),
                "fleet_outstanding": float(self._outstanding),
            }
            # 帳尻(憲法1 の監査点): 答えが返った + 繰り延べ + error_other = 呼数。
            out["fleet_accounted"] = (
                out["fleet_answered"]
                + out["fleet_deferred_timeout"]
                + out["fleet_deferred_queue_full"]
                + out["fleet_error_other"]
            )
            for i in range(self.config.n_replicas):
                out[f"fleet_in_flight_r{i}"] = float(self._in_flight[i])
                out[f"fleet_peak_in_flight_r{i}"] = float(self._peak_in_flight[i])
                out[f"fleet_calls_r{i}"] = float(self._calls_per_replica[i])
        return out


def _debug_reason(p: ParseResult) -> str:
    """初回パースが落ちた**主因**を 1 語で(jsonl の索引用・expedient な分類)。"""
    if not p.labels:
        return "no_labels"
    missing = [lab for lab in ("理由", "行動", "対象", "ひと言") if lab not in p.labels]
    if p.action is None and p.raw_action:
        return "unknown_action_word"  # 語彙外(→ §7 段0 の辞書へ)
    if missing:
        return "missing_label:" + "+".join(missing)
    if p.alias_used and not p.strict_format_ok:
        return "label_alias:" + "+".join(p.alias_surfaces)
    if not p.raw_action:
        return "no_action_field"
    return "other"


def _format_ok(text: str) -> bool:
    """再生成するかの判定(=**実効**基準・行動契約書 §1)。

    **C6・09-09**: 次のどちらかで読めたら**温度 0 の再生成をしない**。
      ① ``format_ok``(C6 のラベル別名「目的地:」「目的:」や位置読みを許容した寛容判定)。
      ② ``dictionary_candidate``(語彙外だが §7 段0 の辞書で救える語=「探索」→「移動」等)。
    ②を再生成に回すのは無駄な 1 呼(C6 実測で初回失敗の 30% が語彙外)で、しかも
    段0 で確実に救えるので、**辞書写像へ直行**させる(``fleet_dictionary_mapped`` に計上)。
    定義を動かさない受入指標のほうは ``strict_format_ok`` で別に数える。
    """
    p = parse_two_line(text)
    return bool(p.format_ok or p.dictionary_candidate)


def _raise_for_status(status: int, body: str) -> None:
    if status < 400:
        return
    snippet = body[:200].replace("\n", " ")
    if status == 429 or status >= 500:
        raise _RetryableHTTP(f"HTTP {status}: {snippet}")
    raise _FatalHTTP(f"HTTP {status}: {snippet}")


async def _next_data(lines: Any) -> str | None:
    """SSE の次の ``data:`` 本文を返す(``[DONE]`` と終端は ``None``)。"""
    async for line in lines:
        s = line.strip()
        if not s or not s.startswith("data:"):
            continue
        payload = s[5:].strip()
        if payload == "[DONE]":
            return None
        return payload
    return None


def _read_chunk(payload: str) -> tuple[str, str, int, int]:
    """SSE 1 チャンク → ``(content, finish_reason, prompt_tokens, completion_tokens)``。"""
    d = json.loads(payload)
    text = ""
    finish = ""
    for ch in d.get("choices") or ():
        delta = ch.get("delta") or {}
        text += delta.get("content") or ""
        if ch.get("finish_reason"):
            finish = str(ch["finish_reason"])
    usage = d.get("usage") or {}
    return text, finish, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0))


def call_from_request(request: LLMRequest, *, lane: str = "L1") -> LLMCall:
    """``llm.LLMRequest`` → ``LLMCall``(同期経路と既存テストのための橋)。"""
    return LLMCall(
        call_id=request.call_id or f"{request.tick}:{request.agent_id}:{request.wake_class}",
        agent_id=int(request.agent_id),
        tick=int(request.tick),
        wake_class=int(request.wake_class),
        prompt=request.prompt,
        blocks=tuple((b, "") for b in request.block_ids),
        lane=lane,
        time_bucket=int(request.tick) // 5,
    )


# ---------------------------------------------------------------- ブリッジ


@dataclass(frozen=True)
class FleetBridgeResult:
    """1 呼の解釈済み結果(engine が intent を組むのに必要なものだけ)。

    ``engine.llm_bridge.BridgeResult`` と**同じ欄名**を持つ(``t_apply``/``lane`` の
    tick 換算だけは engine 側=``delta_think_ticks`` が付ける)。
    """

    agent_id: int
    tick: int
    wake_class: int
    condition: int
    lane: str
    text: str
    parse: ParseResult
    action_code: int
    target: Target
    prompt_hash: str
    tape_prompt_hash: str
    outcome: Outcome
    tokens_in: int = 0
    tokens_out: int = 0
    undefined_stage: int = -1
    undefined_feedback: str = ""
    role_action: bool = False
    source: str = ""
    call_id: str = ""
    replica: int = -1
    attempts: int = 1
    ttft_s: float = 0.0
    e2e_s: float = 0.0

    @property
    def format_ok(self) -> bool:
        return self.parse.format_ok

    @property
    def deferred(self) -> bool:
        return False


class FleetBridge:
    """``engine.llm_bridge`` の ``source="fleet"`` 実装(層契約のため llm 側に置く)。

    入口は ``LLMCall``(呼び出し側が ``PerceptionRendererAdapter`` の ``RenderedPrompt`` から
    詰める)。1 呼につき
      ① 艦隊へ発射(非ブロッキング)②2行形パース ③書式エラー=温度0で1回再生成
      (``FleetClient`` 内)④なお語彙一致しなければ**未定義行動5段**(§7)
      ⑤**実応答をテープへ記録**(リプレイのため)
    を通す。``Deferred`` はそのまま返す(**呼を捨てない**=憲法1・アービタが次 tick へ)。

    **D-58(2026-09-10)**: ``Deferred`` も**テープへ 1 行**書く(応答空・``deferred=1``・
    ``deferred_reason``=``Outcome`` の値・``observed_tick``=呼び出し側が渡す現在 tick)。
    応答行にも ``observed_tick`` を入れる(艦隊は発射 tick より後に届くので、再生側が
    ``t_apply``=運用設計書 §2.4 を復元するのに要る)。``now_tick`` を渡さない経路
    (スモーク・単体テスト)は −1=「同 tick」として記録される。

    Args:
        client: ``FleetClient``。
        tape: ``engine.tape.TapeWriter`` 互換(``intern_block``/``append``)。``None``=記録しない。
        tape_row_factory: テープ行の作り手(既定 ``FleetTapeRow``。engine 側は
            ``engine.tape.TapeRow`` を渡す=**欄名が同じ**なのでそのまま入る)。
        undefined: 未定義行動5段の台帳(``None`` なら新規)。
        params: ``params_hash`` に入るデコード設定(テープ列)。
        debug_dir: **書式の原因分析用**の jsonl 置き場(``None``=off が既定)。
            初回パースが実効または厳密で落ちた呼だけを 1 行 1 呼で落とす
            (``call_id``/``system``/``user``/初回の生応答/再生成の生応答/両基準の判定/理由)。
            **テープ形式は一切変えない**(テープは最終応答 1 行のまま=運用設計書 §2.5)。
        debug_max_rows: jsonl の行数上限(既定 ``DEFAULT_DEBUG_MAX_ROWS``)。
            超えた分は書かず ``fleet_debug_skipped`` に数える(1 日ランで数十 MB にしない)。

    逐次ループ宣言(P4): ``_interpret`` は 1 呼 1 回。``poll``/``drain`` は完了件数ぶん。
    """

    def __init__(
        self,
        client: FleetClient,
        *,
        tape: TapeSink | None = None,
        tape_row_factory: Callable[..., Any] = FleetTapeRow,
        undefined: UndefinedActionRegistry | None = None,
        params: Mapping[str, Any] | None = None,
        debug_dir: str | Path | None = None,
        debug_max_rows: int = DEFAULT_DEBUG_MAX_ROWS,
    ) -> None:
        self.client = client
        self.tape = tape
        self.tape_row_factory = tape_row_factory
        self.undefined = undefined if undefined is not None else UndefinedActionRegistry()
        self.params: Mapping[str, Any] = dict(
            params
            if params is not None
            else {
                "max_tokens": client.config.t1_max_tokens,
                "temperature": client.config.temperature,
                "top_p": client.config.top_p,
                "cache_salt": client.cache_salt,
                "prefix_caching_hash_algo": "sha256_cbor",
            }
        )
        self.source = "fleet"
        #: ``params_hash`` は設定が固定なのでラン中 1 回だけ計算する(テープ列)。
        self._params_hash = sha256_cbor(dict(self.params))
        # ---- 書式デバッグ jsonl(既定 off・診断のみ) ----
        self.debug_dir = Path(debug_dir) if debug_dir is not None else None
        self.debug_max_rows = int(debug_max_rows)
        self._debug_fp: Any = None
        self.n_debug_rows = 0
        self.n_debug_skipped = 0
        if self.debug_dir is not None:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            self._debug_fp = (self.debug_dir / DEBUG_FILENAME).open(
                "a", encoding="utf-8", newline="\n"
            )
        self._interned: set[str] = set()
        # ---- 計数(診断行) ----
        self.n_calls = 0
        #: **実効**基準の書式エラー(C6 ラベル別名を許容した後)。再生成の判定もこちら。
        self.n_parse_errors = 0
        #: **厳密**基準の書式エラー(C6 以前の別名表だけで見た判定=受入指標の定義を動かさない)。
        self.n_parse_errors_strict = 0
        #: C6 で足したラベル別名を使って読めた応答の数(「目的地:」「目的:」等)。
        self.n_label_alias = 0
        #: ラベルを省いた並びを**位置**で読んだ応答の数(``positional_used``)。
        self.n_positional = 0
        #: 語彙外の行動語を §7 段0 の辞書写像で救えた数(「探索」→「移動」等)。
        self.n_dictionary_mapped = 0
        self.n_unknown_action = 0
        self.n_undefined_mapped = 0
        self.n_role_actions = 0
        self.n_deferred = 0
        #: うちテープへ**繰り延べ行**として書いた数(D-58)。``n_tape_rows`` の内数。
        self.n_deferred_rows = 0
        self.n_tape_rows = 0

    # ------------------------------------------------------------ 発射/回収
    def submit(
        self, calls: Sequence[LLMCall], *, now_tick: int = -1
    ) -> list[FleetBridgeResult | Deferred]:
        """呼を発射(非ブロッキング)。返るのは「入らなかった」分の ``Deferred`` だけ。

        Args:
            now_tick: エンジンの**現在 tick**(D-58)。キュー満杯の繰り延べは
                この tick で観測されたものとしてテープの繰り延べ行に記録する。
                ``-1``(既定)=呼び出し側が tick を持たない経路(スモーク・単体)。
        """
        rejected = self.client.submit(calls)
        self.n_deferred += len(rejected)
        for d in rejected:  # 逐次ループ宣言: 却下件数ぶん(通常 0)
            self._record_deferred(d, now_tick)  # type: ignore[arg-type]
        return list(rejected)  # type: ignore[arg-type]

    def poll(self, *, now_tick: int = -1) -> list[FleetBridgeResult | Deferred]:
        """届いた分を解釈して返す(非ブロッキング・順序は非決定)。

        Args:
            now_tick: エンジンの現在 tick(テープの ``observed_tick`` 列・D-58)。
        """
        return [self._interpret(r, now_tick) for r in self.client.poll()]

    def drain(
        self, timeout: float | None = None, *, now_tick: int = -1
    ) -> list[FleetBridgeResult | Deferred]:
        """実行中が空になるまで待って全部解釈して返す(スモーク/テスト用)。"""
        return [self._interpret(r, now_tick) for r in self.client.drain(timeout=timeout)]

    def submit_and_drain(
        self, calls: Sequence[LLMCall], timeout: float | None = None, *, now_tick: int = -1
    ) -> list[FleetBridgeResult | Deferred]:
        """発射→全回収(24 step スモークの単純経路。**tick ループは止まる**)。"""
        out = self.submit(calls, now_tick=now_tick)
        out.extend(self.drain(timeout=timeout, now_tick=now_tick))
        return out

    # ------------------------------------------------------------ 解釈
    def _interpret(
        self, res: LLMResult | Deferred, now_tick: int = -1
    ) -> FleetBridgeResult | Deferred:
        if isinstance(res, Deferred):
            self.n_deferred += 1
            self._record_deferred(res, now_tick)
            return res
        call = res.call
        self.n_calls += 1
        parse = parse_two_line(res.text)
        action_code = parse.action_code
        role_action = bool(parse.is_role_action)
        if role_action:
            self.n_role_actions += 1
            # 役割語の効果先は C4。当面は安全弁(待機)へ落とす(``engine.llm_bridge`` と同規約)。
            action_code = int(ACTION_CODES["待機"])
        if not parse.format_ok:
            self.n_parse_errors += 1  # 実効(別名許容後)=再生成と診断の主指標
        if not parse.strict_format_ok:
            self.n_parse_errors_strict += 1  # 厳密(受入指標の定義そのまま)
        if parse.alias_used:
            self.n_label_alias += 1
        if parse.positional_used:
            self.n_positional += 1

        outcome = res.outcome
        stage = -1
        feedback = ""
        # テープ鍵の第4要素(``engine.llm_bridge`` と同じ算法=``LLMRequest.prompt_hash``)。
        tape_prompt_hash = sha256_cbor(call.prompt)
        if parse.action is None:
            self.n_unknown_action += 1
            out = self.undefined.observe(parse.raw_action, int(call.agent_id), int(call.tick), tape_prompt_hash)
            stage = out.stage
            feedback = out.feedback
            if out.mapped and out.word in ACTION_CODES:
                action_code = int(ACTION_CODES[out.word])
                self.n_undefined_mapped += 1
                if out.stage == 0:
                    self.n_dictionary_mapped += 1
                # ``parse`` は書き換えない(``engine.llm_bridge`` と同じ扱い=親判断待ち)。
            else:
                action_code = UNDEFINED_ACTION
            outcome = Outcome.UNDEFINED

        self._record_tape(call, res, tape_prompt_hash, now_tick)
        self._record_debug(call, res, parse)
        return FleetBridgeResult(
            agent_id=int(call.agent_id),
            tick=int(call.tick),
            wake_class=int(call.wake_class),
            condition=int(call.condition),
            lane=call.lane,
            text=res.text,
            parse=parse,
            action_code=int(action_code),
            target=parse.target if parse.action is not None else NO_TARGET_VALUE,
            prompt_hash=call.prompt_hash_hint or tape_prompt_hash,
            tape_prompt_hash=tape_prompt_hash,
            outcome=outcome,
            tokens_in=int(res.tokens_in),
            tokens_out=int(res.tokens_out),
            undefined_stage=stage,
            undefined_feedback=feedback,
            role_action=role_action,
            source=res.source,
            call_id=call.call_id,
            replica=res.replica,
            attempts=res.attempts,
            ttft_s=res.ttft_s,
            e2e_s=res.e2e_s,
        )

    def _record_debug(self, call: LLMCall, res: LLMResult, final: ParseResult) -> None:
        """初回パースが落ちた呼を jsonl へ 1 行(``debug_dir`` を渡したときだけ)。

        「初回」= 温度 0 の再生成の**前**。``res.first_text`` があればそれが初回、
        無ければ最終応答がそのまま初回(再生成が起きなかった=別名だけで落ちた場合)。
        """
        if self._debug_fp is None:
            return
        first_raw = res.first_text if res.format_retried else res.text
        first = parse_two_line(first_raw) if res.format_retried else final
        if first.format_ok and first.strict_format_ok:
            return  # 初回が実効・厳密の両方で通った呼は書かない
        if self.n_debug_rows >= self.debug_max_rows:
            self.n_debug_skipped += 1
            return
        row = {
            "call_id": call.call_id,
            "agent_id": int(call.agent_id),
            "tick": int(call.tick),
            "wake_class": int(call.wake_class),
            "lane": call.lane,
            "replica": int(res.replica),
            "system": call.system,
            "user": call.user_text,
            "first_raw": first_raw,
            "retry_raw": res.text if res.format_retried else "",
            "format_retried": bool(res.format_retried),
            # 判定(初回 / 最終 それぞれ 実効=format_ok・厳密=strict_format_ok)
            "first_effective_ok": bool(first.format_ok),
            "first_strict_ok": bool(first.strict_format_ok),
            "final_effective_ok": bool(final.format_ok),
            "final_strict_ok": bool(final.strict_format_ok),
            # 理由
            "first_errors": list(first.errors),
            "final_errors": list(final.errors),
            "alias_surfaces": list(first.alias_surfaces),
            "raw_action": first.raw_action,
            "final_action": final.action,
            "labels_found": sorted(first.labels),
            "finish_reason": res.finish_reason,
            "tokens_out": int(res.tokens_out),
            "reason": _debug_reason(first),
        }
        self._debug_fp.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.n_debug_rows += 1

    def _intern_blocks(self, call: LLMCall) -> None:
        for block_id, block_text in call.blocks:  # 逐次ループ宣言: 共有ブロック数(6)
            if block_id in self._interned or not block_text:
                continue
            self.tape.intern_block(block_text, estimate_tokens(block_text))  # type: ignore[union-attr]
            self._interned.add(block_id)

    def _record_tape(
        self, call: LLMCall, res: LLMResult, prompt_hash: str, now_tick: int = -1
    ) -> None:
        if self.tape is None:
            return
        self._intern_blocks(call)
        self.tape.append(
            self.tape_row_factory(
                call_id=call.call_id,
                agent_id=int(call.agent_id),
                tick=int(call.tick),
                wake_class=int(call.wake_class),
                prompt_hash=prompt_hash,
                block_ids=call.block_ids,
                params_hash=self._params_hash,
                response=res.text,
                tokens_in=int(res.tokens_in),
                tokens_out=int(res.tokens_out),
                deferred=0,
                deferred_reason="",
                observed_tick=int(now_tick),
            )
        )
        self.n_tape_rows += 1

    def _record_deferred(self, d: Deferred, now_tick: int = -1) -> None:
        """**繰り延べ行**を 1 行書く(D-58)。

        運用設計書 §2.5 の「1 呼=1 行」を、答えの返らなかった呼へも広げる
        (応答空・``tokens=0``・``deferred=1``)。テープ鍵(agent_id, tick, wake_class,
        prompt_hash)は応答行と同じ作り方=再生は**発射 tick で**この行を引き当てて、
        本番と同じ tick に同じ繰り延べを起こす。

        ``deferred_reason`` は ``Outcome`` の値(閉じた語彙)。自由文の ``Deferred.reason``
        (例外型名・HTTP ステータス)はテープへは入れない(列を非決定にしないため・
        診断行と ``debug_dir`` に残る)。
        """
        if self.tape is None:
            return
        call = d.call
        self._intern_blocks(call)
        self.tape.append(
            self.tape_row_factory(
                call_id=call.call_id,
                agent_id=int(call.agent_id),
                tick=int(call.tick),
                wake_class=int(call.wake_class),
                prompt_hash=sha256_cbor(call.prompt),
                block_ids=call.block_ids,
                params_hash=self._params_hash,
                response="",
                tokens_in=0,
                tokens_out=0,
                deferred=1,
                deferred_reason=d.outcome.value,
                observed_tick=int(now_tick),
            )
        )
        self.n_tape_rows += 1
        self.n_deferred_rows += 1

    # ------------------------------------------------------------ 診断行
    @property
    def parse_error_rate(self) -> float:
        """**実効**書式エラー率(C6 ラベル別名を許容した後)。"""
        return (self.n_parse_errors / self.n_calls) if self.n_calls else 0.0

    @property
    def parse_error_rate_strict(self) -> float:
        """**厳密**書式エラー率(C6 以前の別名表だけで見た判定=受入指標の定義そのまま)。"""
        return (self.n_parse_errors_strict / self.n_calls) if self.n_calls else 0.0

    def counters(self) -> Mapping[str, float]:
        """診断行(艦隊 + 解釈 + 未定義行動5段)。"""
        n = max(1, self.n_calls)
        out: dict[str, float] = {
            "llm_calls": float(self.n_calls),
            # ---- 二重指標(C6・09-09)。主=実効・併記=厳密 ----
            "parse_errors": float(self.n_parse_errors),
            "parse_error_rate": self.parse_error_rate,
            "parse_errors_strict": float(self.n_parse_errors_strict),
            "parse_error_rate_strict": self.parse_error_rate_strict,
            "fleet_format_strict_errors": float(self.n_parse_errors_strict),
            "fleet_label_alias_used": float(self.n_label_alias),
            "fleet_label_alias_rate": self.n_label_alias / n,
            "fleet_positional_used": float(self.n_positional),
            "fleet_positional_rate": self.n_positional / n,
            "fleet_dictionary_mapped": float(self.n_dictionary_mapped),
            "fleet_dictionary_mapped_rate": self.n_dictionary_mapped / n,
            "unknown_action": float(self.n_unknown_action),
            "undefined_mapped": float(self.n_undefined_mapped),
            "role_actions": float(self.n_role_actions),
            "fleet_deferred_total": float(self.n_deferred),
            "tape_rows": float(self.n_tape_rows),
            "tape_deferred_rows": float(self.n_deferred_rows),
            "fleet_debug_rows": float(self.n_debug_rows),
            "fleet_debug_skipped": float(self.n_debug_skipped),
        }
        out.update({k: float(v) for k, v in self.client.counters().items()})
        out.update({k: float(v) for k, v in self.undefined.counters().items()})
        return out

    def close(self) -> None:
        """艦隊クライアントとデバッグ jsonl を閉じる(テープは呼び出し側の持ち物)。"""
        if self._debug_fp is not None:
            self._debug_fp.close()
            self._debug_fp = None
        self.client.close()
