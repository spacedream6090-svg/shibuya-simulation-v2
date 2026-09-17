"""engine.llm_bridge — エンジンと LLM クライアントの**唯一の接点**(録画/リプレイ・δ_think・解釈)。

ここを通らない LLM 呼び出しはエンジンに存在しない。1呼につき必ず
①プロンプト生成(``Renderer``)②δ_think による ``t_apply`` 決定 ③テープ書き出し
④2行形パース ⑤未定義行動5段(§7)への受け渡し を行う。

正典
- 認知設計書 §1 δ_think レーン表: L0=0 / **L1 出力64・思考0=2.6秒** / L2 2,048tok=**82秒** /
  L3 7,500tok=300秒/ブロック / L4 会話=0.2秒。換算 α_think=0.04秒/tok。
- 運用設計書 §2.4: 応答は ``pending_apply`` へ・``t_apply = 起床 + δ_perc + δ_think`` を
  分tickへ**切り上げ**。
- 運用設計書 §2.5: 「録画リプレイ=LLMテープ(1呼=1行・共有ブロックはID化・``params_hash``)から
  **(agent_id, tick, wake_class, prompt_hash) 完全一致**で引く。テープ外は失敗
  (**黙って実LLMへ落とさない**)・テープ外率を診断行へ。」
- 知覚契約書 §2.4 ⑨: 「時刻表記は**5分丸め**」= ``StubRenderer`` が ``tick//5`` を使う理由。
- 行動契約書 §7: 未定義行動は段0(辞書)→段1(記録+フィードバック)。**待機へ落とす**のは
  ``engine.commit.intents_from_responses``(安全弁=§2 共通必須事項③)。

**C6 の段0 辞書写像を ``parse`` に載せない理由(親判断待ち・09-09)**
    ``llm.parser.ParseResult.with_dictionary_mapping(word)`` は「段0 で救えた語を parse に
    載せる口」として C6 で足された。だが本 bridge は**呼ばない**:
      ① 既存の契約テスト(``tests/engine/test_undefined_action.py``)が
         「``res.parse.action is None`` かつ ``raw_action`` は逐語」を pin している
         =``BridgeResult.parse`` は**生の応答の記述**という取り決め。
      ② ``engine.run`` は会話ターンで ``conv.utterance(action=res.parse.action)`` を呼ぶので、
         ここを埋めると**発話ブロックの中身が変わる**(mock 経路の挙動不変の約束に触れる)。
    救えた事実は ``action_code`` と ``undefined_stage=0``・診断行 ``dictionary_mapped`` に残る。
    載せるべきかは親判断(会話発話に写像後の語を使うか)。

**親の指示との差分(黙って解決しない)その2 — prompt_hash が 2 本ある**
    親の指示は「``prompt_hash`` は ``Rendered.prompt_hash`` から取る」。ところが
    **テープの完全一致鍵**(運用設計書 §2.5)を引くのは ``llm.mock.TapeLLM`` で、
    そこが使うのは ``LLMRequest.prompt_hash``(= ``sha256_cbor(prompt)``)である。
    ``Rendered.prompt_hash`` は ``blake3(連結ブロック)`` なので**別の値**。
    テープ行の鍵をレンダラ側の値に差し替えると、``TapeLLM`` の lookup 鍵と食い違って
    リプレイが全件テープ外になる(``llm/`` は本工程で変更禁止=鍵の計算元を揃えられない)。
    そこで **両方を持つ**:
      - ``BridgeResult.prompt_hash`` = レンダラの指紋(親の指示どおり・診断/監査用)
      - ``BridgeResult.tape_prompt_hash`` と ``TapeRow.prompt_hash`` = ``LLMRequest`` の値
        (=録画/再生の鍵。record と replay で同じ本文から同じ手順で作るので一致は保たれる)
    どちらもプロンプト本文の決定論的な関数なので、決定性・再現性の主張は変わらない。

**親の指示との差分(黙って解決しない)**
    指示は「L1: 0 tick」。認知設計書 §1 の L1 は **2.6 秒**で、これを分tickへ切り上げると
    **1 tick** になる(``engine.run`` の既存定数 ``DELTA_THINK_TICKS=1`` と同値)。本モジュールは
    設計書どおり ``ceil(δ_think 秒 / tick 秒)`` を採り、L1=1 tick とした。
    tick の骨格は「①前tickまでに届いた応答を適用」が「④LLM呼」より前にあるため、
    ``t_apply=tick`` と ``t_apply=tick+1`` は**同じ tick(tick+1)で適用され挙動が一致する**。

**D-58 テープ繰り延べ行(2026-09-10)**
    艦隊経路では「答えが返らなかった呼」(queue full/タイムアウト)が翌 tick の起床候補へ
    再投入される(憲法1=破棄禁止)。版1 のテープはこれを記録しなかったので、再生が本番と
    分岐した(c7-day-2 で tape_miss 98.7%)。版2(``engine.tape``)は繰り延べも 1 行にし、
    本 bridge は ``mode="replay"`` で
      - 繰り延べ行を引いたら ``BridgeResult(deferred=True, observed_tick=…)`` を返す
        (**パースも未定義行動5段も通さない**=本番の ``FleetBridge`` が ``Deferred`` を
        素通しするのと同じ)。intent は作られない。
      - 応答行の ``observed_tick``(帰結を観測した tick)をそのまま返す。``t_apply`` を
        本番と同じに置き直すのは ``engine.run``(艦隊の到着 tick を知っているのはそこ)。
    どちらも旧テープでは既定値(deferred=0・observed_tick=−1)なので、mock 経路の
    挙動は 1 バイトも変わらない。

逐次ループ宣言(P4)
- ``LLMBridge.call``: 1呼=1回(ループなし)。呼数ぶんのループは呼び出し側
  (``engine.run._call_llm`` 相当・宣言済み)にある。
- ``StubRenderer.render``: ループなし。

expedient(本モジュール分)
- ``StubRenderer`` の文面 ``[a<agent>|c<cell>|t5<tick//5>|w<class>]``(B0-B6 の本物の
  レンダラは C3-subE)。**文面凍結の対象ではない**(スタブであることを名前で宣言している)。
- ``call_id = "<tick>:<agent>:<class>"``(艦隊ルーティング ``xxhash(call_id) mod 7`` 用)。
- 役割語(§2.2)は ``_APPLY`` に対応分岐が無い(効果先は C4)。intent としては
  **待機**へ落とし、``role_action`` 計数と ``NO_PERMISSION`` 相当の印だけ残す。
- テープ外(``TapeMiss``)のときは本文を空にして未定義行動扱い(=待機)。**実LLMは呼ばない**。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Protocol, runtime_checkable

from shibuya.engine.tape import (
    Replay,
    Tape,
    TapeMiss,
    TapeRow,
    TapeWriter,
    block_id_for,
)
from shibuya.llm import (
    ACTION_CODES,
    UNDEFINED_ACTION,
    LLMRequest,
    ParseResult,
    Target,
    TapeLLM,
    UndefinedActionRegistry,
    estimate_tokens,
    parse_two_line,
)
from shibuya.llm.contract import (
    DEFAULT_VOCAB_VERSION,
    EAT_ACTION_CODE,
    NO_TARGET_VALUE,
    ACTION_WORD_EAT,
    check_vocab_version,
    engine_action_codes,
)
from shibuya.perception import templates as PT

__all__ = [
    "ALPHA_THINK_SECONDS_PER_TOKEN",
    "LANE_SECONDS",
    "LANE_THINK_TOKENS",
    "DEFAULT_LANE",
    "ACTION_WORD_BY_CODE",
    "SHARED_BLOCK_IDS",
    "delta_think_ticks",
    "RenderedPrompt",
    "Renderer",
    "StubRenderer",
    "PerceptionRendererAdapter",
    "STUB_SHARED_BLOCK",
    "BridgeResult",
    "LLMBridge",
]

#: 行動コード → 行動語(``llm.contract.ACTION_CODES`` の逆写像)。B6「直前に試みた行動」用。
#: **語彙 v2 の「食事」(24)も入れてある**: コード 24 は v1 のランには 1 件も現れないので
#: 既定の描画は 1 バイトも動かず、v2 のランでだけ B6 が「直前の食事は…」と言えるようになる。
ACTION_WORD_BY_CODE: Final[Mapping[int, str]] = {
    **{int(v): k for k, v in ACTION_CODES.items()},
    EAT_ACTION_CODE: ACTION_WORD_EAT,
}

#: テープへ intern する**共有ブロック**(B5/B6 は個体依存なので intern しない)。
SHARED_BLOCK_IDS: Final[tuple[str, ...]] = tuple(
    b for b in PT.BLOCK_IDS if b not in ("B5", "B6")
)

#: 認知設計書 §1「換算=既決 α_think 0.04秒/tok(線形・対数圧縮不採用)」。
ALPHA_THINK_SECONDS_PER_TOKEN: Final[float] = 0.04

#: レーン → δ_think[秒](認知設計書 §1 の表を逐語で写した)。
LANE_SECONDS: Final[Mapping[str, float]] = {
    "L0": 0.0,  # 反射/習慣(T0): δ_perc のみ
    "L1": 2.6,  # 速い判断(T1): 出力64tok・思考0
    "L2": 82.0,  # 通常熟慮(T2): 2,048tok
    "L3": 300.0,  # 重大熟慮(T2): 7,500tok/ブロック
    "L4": 0.2,  # 会話応答: δ_min 0.2秒
}

#: レーン → 思考トークン上限(認知設計書 §2 の ``B_world``)。
LANE_THINK_TOKENS: Final[Mapping[str, int]] = {
    "L0": 0,
    "L1": 0,
    "L2": 2_048,
    "L3": 7_500,
    "L4": 0,
}

#: 既定レーン(通常の起床=T1)。
DEFAULT_LANE: Final[str] = "L1"


def delta_think_ticks(lane: str = DEFAULT_LANE, tick_seconds: int = 60) -> int:
    """レーン → δ_think[tick](**分tickへ切り上げ**・運用設計書 §2.4)。

    Args:
        lane: ``L0``..``L4``。
        tick_seconds: 1 tick の秒数。

    Returns:
        切り上げた tick 数(L0=0・L1=1・L2=2・L3=5 @tick_seconds=60)。

    Raises:
        KeyError: 未知のレーン(**黙って既定に落とさない**)。
    """
    seconds = LANE_SECONDS[lane]
    if tick_seconds <= 0:
        raise ValueError("tick_seconds は正の整数")
    return int(math.ceil(seconds / float(tick_seconds)))


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


#: スタブの共有静的ブロック(B0 相当の place holder)。
STUB_SHARED_BLOCK: Final[str] = "[B0|stub|出力は2行形: 理由/行動・対象・ひと言]"


class StubRenderer:
    """決定論の最小プロンプト(``prompt_hash`` が (agent, cell, tick//5, wake_class) で決まる)。

    ``tick//5`` は知覚契約書 §2.4 ⑨「時刻表記は**5分丸め**」に合わせた粒度。
    テープ鍵に意味を持たせつつ、5分間はプロンプトが変わらない=prefix キャッシュが効く形。
    """

    def __init__(self, *, time_bucket_ticks: int = 5, shared_block: str = STUB_SHARED_BLOCK) -> None:
        if time_bucket_ticks < 1:
            raise ValueError("time_bucket_ticks は 1 以上")
        self.time_bucket_ticks = int(time_bucket_ticks)
        self.shared_block = shared_block
        self._blocks: tuple[tuple[str, str], ...] = ((block_id_for(shared_block), shared_block),)

    def render(
        self,
        *,
        agent_id: int,
        tick: int,
        cell: int,
        activity: int = 0,
        hunger: int = 0,
        wake_class: int = 0,
        condition: int = 0,
        last_action: int = -1,
        inviter: int = -1,
    ) -> RenderedPrompt:
        # ``inviter`` はスタブでは**使わない**(テープ鍵とプロンプト本文を動かさない)。
        bucket = int(tick) // self.time_bucket_ticks
        text = f"[a{int(agent_id)}|c{int(cell)}|t5{bucket}|w{int(wake_class)}]"
        return RenderedPrompt(text=text, blocks=self._blocks)

    def prepare_tick(self, tick: int, **_kwargs: Any) -> None:
        """1 tick 1 回の前計算(スタブは何もしない・呼ばれても落ちないための空実装)。"""


class PerceptionRendererAdapter:
    """``perception.renderer.Renderer`` を bridge の ``Renderer`` 契約へ橋渡しする。

    知覚側は ``render(agent_id, tick, wake_reason, last_result, last_action)`` で、
    bridge 側は ``render(*, agent_id, tick, cell, activity, hunger, wake_class, condition,
    last_action)``。**引数名と last_action の型(コード vs 語)が違うだけ**なので、
    知覚側を書き換えず本アダプタで吸収する(知覚モジュールは C3-subE の凍結対象)。

    写像
      - ``condition``(``agents.state.WakeCondition``)→ 知覚側 ``wake_reason``
        (``templates.WAKE_REASON_TEXT`` の索引=同じ 11 行の並び)。
      - ``last_action``(行動コード)→ 行動語(``ACTION_WORD_BY_CODE``)。-1 は None
        (知覚側が ``activity`` で代用する既定の道)。
      - ``last_result`` は渡さない = 知覚側が ``agents.last_result`` を読む(SoA が正)。

    Attributes:
        group_token_sums / n_renders: 診断行「グループ別の平均トークン」の素材。

    逐次ループ宣言(P4): ``render`` は 1 呼につき共有ブロック数(6)ぶんのループのみ。
    """

    def __init__(self, renderer: Any) -> None:
        self.renderer = renderer
        #: 描画バイトの xxh64 → テープの ``block_id``(blake3 の再計算を避ける)。
        self._block_id: dict[int, str] = {}
        self.group_token_sums: dict[str, int] = {g: 0 for g in PT.GROUP_TOKEN_BUDGET}
        self.n_renders = 0
        self.prompt_tokens_sum = 0

    # ---- 1 tick 1 回の前計算 ----
    def prepare_tick(self, tick: int, **kwargs: Any) -> None:
        self.renderer.prepare_tick(int(tick), **kwargs)

    @property
    def b4_field_rows(self) -> Any:
        """この tick の B4 描画欄 ``(n_cells, 4)`` int32(変化検出器へ渡す1本)。"""
        return self.renderer.b4_field_rows

    @property
    def assets(self) -> Any:
        """知覚側資産(``engine.run`` が歩行可能面積=LOS の分母を取り出す口)。"""
        return self.renderer.assets

    # ---- 1 起床 1 描画 ----
    def render(
        self,
        *,
        agent_id: int,
        tick: int,
        cell: int = -1,
        activity: int = 0,
        hunger: int = 0,
        wake_class: int = 0,
        condition: int = 0,
        last_action: int = -1,
        inviter: int = -1,
    ) -> RenderedPrompt:
        word = ACTION_WORD_BY_CODE.get(int(last_action))
        out = self.renderer.render(
            int(agent_id), int(tick), wake_reason=int(condition), last_action=word,
            inviter=int(inviter) if int(inviter) >= 0 else None,
        )
        blocks: list[tuple[str, str]] = []
        for bid in SHARED_BLOCK_IDS:  # 逐次ループ宣言: 共有ブロック 6 本
            body = out.blocks[bid]
            key = int(out.block_hashes[bid])
            tape_id = self._block_id.get(key)
            text = body.decode("utf-8")
            if tape_id is None:
                tape_id = block_id_for(text)
                self._block_id[key] = tape_id
            blocks.append((tape_id, text))
        self.n_renders += 1
        for g, v in out.group_tokens.items():
            self.group_token_sums[g] = self.group_token_sums.get(g, 0) + int(v)
        self.prompt_tokens_sum += int(out.tokens_total)
        return RenderedPrompt(
            text=out.text,
            blocks=tuple(blocks),
            prompt_hash=out.prompt_hash,
            group_tokens=tuple(sorted(out.group_tokens.items())),
        )

    # ---- 診断 ----
    def counters(self) -> Mapping[str, float]:
        """診断行(グループ別平均トークン・キャッシュ命中率・切り詰め数)。"""
        n = max(1, self.n_renders)
        out: dict[str, float] = {
            "render_calls": float(self.n_renders),
            "render_cache_hit_rate": float(self.renderer.cache_hit_rate),
            "render_truncations": float(self.renderer.truncation_count),
            "prompt_tokens_mean": self.prompt_tokens_sum / n,
        }
        for g, v in self.group_token_sums.items():
            out[f"tokens_{g}_mean"] = v / n
        return out


# ------------------------------------------------------------------ 1呼の結果
@dataclass(frozen=True)
class BridgeResult:
    """1呼の結果(エンジンが intent を組むのに必要なものだけ)。

    Attributes:
        agent_id / tick / wake_class / condition: 呼の鍵。
        t_apply: 応答を適用する tick(``tick + δ_think``)。
        lane: 使った δ_think レーン。
        text: 応答本文(テープ外なら空文字)。
        parse: パーサの結果。
        action_code: エンジンの行動コード(``UNDEFINED_ACTION`` を含む)。
        target: 「対象」欄の解釈。
        undefined_stage: §7 の段(写ったら 0/4・記録なら 1・裁定を出したら 2・該当なしは -1)。
        role_action: §2.2 の役割語だったか(権限検査待ち=当面 待機 へ落とす)。
        tape_miss: リプレイでテープ外だったか。
        deferred: リプレイで**繰り延べ行**を引いたか(D-58)。True のとき ``text`` は空・
            ``parse``/``action_code`` は意味を持たない(呼び出し側は intent を作らず
            起床候補へ再投入する=本番の艦隊経路と同じ扱い)。
        deferred_reason: ``llm.fleet.Outcome`` の値(``deferred_queue_full`` 等)。
        observed_tick: テープが記録した「エンジンが帰結を観測した tick」。−1=同 tick 同期
            (mock 経路・版1 のテープ)。応答行では ``t_apply`` の再現に、繰り延べ行では
            再投入 tick の再現に使う。
        source: ``mock`` / ``tape`` / 実艦隊名。
    """

    agent_id: int
    tick: int
    wake_class: int
    condition: int
    t_apply: int
    lane: str
    text: str
    parse: ParseResult
    action_code: int
    target: Target
    prompt_hash: str
    #: テープ鍵の第4要素(``LLMRequest.prompt_hash`` = sha256_cbor(prompt))。
    #: ``prompt_hash`` はレンダラ側の指紋(blake3)が入るので**別欄で保つ**(下の Note)。
    tape_prompt_hash: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    undefined_stage: int = -1
    undefined_feedback: str = ""
    role_action: bool = False
    tape_miss: bool = False
    deferred: bool = False
    deferred_reason: str = ""
    observed_tick: int = -1
    source: str = ""

    @property
    def format_ok(self) -> bool:
        return self.parse.format_ok


class LLMBridge:
    """エンジン ↔ LLM の一本道。``mode="record"`` は実クライアント/mock、``"replay"`` はテープ。

    Args:
        llm: ``llm.LLMClient``(``mode="record"`` で必須)。
        renderer: プロンプト生成(既定 ``StubRenderer``)。
        tape: 録画先(``None`` なら記録しない)。
        mode: ``"record"`` / ``"replay"``。
        replay: ``engine.tape.Replay``(または テープのパス)。``mode="replay"`` で必須。
        params: デコード設定(``params_hash`` に入る)。
        lane: 既定の δ_think レーン。
        tick_seconds: 1 tick の秒数(δ_think の切り上げに使う)。
        undefined: 未定義行動5段の台帳(``None`` なら新規に作る)。
        vocab_version: 行動語彙の版(D-71 §3 F)。パーサ・段0 辞書・行動コードの解決に効く。
            既定 ``"v1"`` は**現行と 1 バイトも変わらない**。

    Note:
        ``mode="replay"`` で ``TapeMiss`` が出たら**計数して空応答を返す**。実LLMへは落とさない
        (運用設計書 §2.5)。
    """

    def __init__(
        self,
        llm: Any | None = None,
        *,
        renderer: Renderer | None = None,
        tape: TapeWriter | None = None,
        mode: str = "record",
        replay: Replay | Tape | str | Path | None = None,
        params: Mapping[str, Any] | None = None,
        lane: str = DEFAULT_LANE,
        tick_seconds: int = 60,
        undefined: UndefinedActionRegistry | None = None,
        vocab_version: str = DEFAULT_VOCAB_VERSION,
    ) -> None:
        if mode not in ("record", "replay"):
            raise ValueError("mode は record|replay")
        self.mode = mode
        self.vocab_version = check_vocab_version(vocab_version)
        #: その版で**エンジンに適用分岐がある**語 → コード(役割語は含まない)。
        self._engine_codes = engine_action_codes(self.vocab_version)
        self.renderer: Renderer = renderer if renderer is not None else StubRenderer()
        self.tape = tape
        self.params: Mapping[str, Any] = dict(params or {})
        self.lane = lane
        self.tick_seconds = int(tick_seconds)
        self.undefined = (
            undefined
            if undefined is not None
            else UndefinedActionRegistry(vocab_version=self.vocab_version)
        )
        self.replay: Replay | None = None
        if mode == "replay":
            if replay is None:
                raise ValueError("mode='replay' には replay(Replay かテープのパス)が要る")
            self.replay = replay if isinstance(replay, Replay) else Replay(replay)
            self.client: Any = TapeLLM(self.replay)
        else:
            if llm is None:
                raise ValueError("mode='record' には llm クライアントが要る")
            self.client = llm
        # ---- 計数(診断行) ----
        self.n_calls = 0
        #: **実効**基準の書式エラー(C6 ラベル別名を許容した後)。
        self.n_parse_errors = 0
        #: **厳密**基準(C6 以前の別名表だけ)。受入指標の定義を動かさないための併記。
        self.n_parse_errors_strict = 0
        #: C6 で足したラベル別名で読めた応答 / §7 段0 の辞書写像で救えた語。
        self.n_label_alias = 0
        self.n_positional = 0
        self.n_dictionary_mapped = 0
        self.n_unknown_action = 0
        self.n_undefined_mapped = 0
        self.n_role_actions = 0
        self.n_tape_misses = 0
        #: 再生で**繰り延べ行**を引いた回数(D-58)。record 経路(mock)では常に 0。
        self.n_deferred = 0
        self.n_tape_rows = 0
        #: すでに intern 済みの共有ブロック id(blake3 の再計算を避ける)。
        self._interned: set[str] = set()

    # ---------------------------------------------------------------- 1 tick 1 回
    def prepare_tick(self, tick: int, **kwargs: Any) -> None:
        """レンダラの tick 前計算を通す(持っていないレンダラは何もしない)。"""
        fn = getattr(self.renderer, "prepare_tick", None)
        if fn is not None:
            fn(int(tick), **kwargs)

    # ---------------------------------------------------------------- 1呼
    def call(
        self,
        agent_id: int,
        tick: int,
        wake_class: int,
        condition: int = 0,
        *,
        cell: int = -1,
        activity: int = 0,
        hunger: int = 0,
        last_action: int = -1,
        lane: str | None = None,
        targets: tuple[str, ...] = (),
        inviter: int = -1,
    ) -> BridgeResult:
        """1呼。**必ず**テープへ書き、必ずパースし、必ず ``t_apply`` を決める。

        Args:
            last_action: **直前に試みた**行動コード(``agents.last_action``・-1=なし)。
                B6「直前の結果」の主語になる(行動契約書 §6)。
            inviter: 被招待起床(``WakeCondition.CONVERSATION_TURN`` で返事待ち)のとき
                **招待者の個体 id**。レンダラが B6 起床行で名指す(知覚契約書 §6 起床(ii))。
                -1=招待なし(描画は 1 バイトも変わらない)。
        """
        lane = lane or self.lane
        rendered = self.renderer.render(
            agent_id=int(agent_id),
            tick=int(tick),
            cell=int(cell),
            activity=int(activity),
            hunger=int(hunger),
            wake_class=int(wake_class),
            condition=int(condition),
            last_action=int(last_action),
            inviter=int(inviter),
        )
        request = LLMRequest(
            agent_id=int(agent_id),
            tick=int(tick),
            wake_class=int(wake_class),
            prompt=rendered.text,
            block_ids=rendered.block_ids,
            params=self.params,
            targets=targets or rendered.targets,
            call_id=f"{int(tick)}:{int(agent_id)}:{int(wake_class)}",
        )

        text = ""
        source = ""
        tokens_in = estimate_tokens(request.prompt)
        tokens_out = 0
        tape_miss = False
        observed_tick = -1
        if self.replay is not None:
            # ---- 再生: テープ行を 1 回だけ引く(D-58)----
            # ``LLMClient`` 契約(``TapeLLM``)は**応答文字列しか運べない**ので、版2 の
            # ``deferred``/``observed_tick`` を受け取るためにここだけ ``Replay`` を直に引く
            # (llm 層の契約は変えない=``TapeLLM`` は従来どおり使える)。
            # 逐次ループ宣言: 追加ループなし(dict 参照 1〜2 回)。再生は検死経路(§1.3)。
            try:
                hit = self.replay.lookup_row(
                    int(agent_id), int(tick), int(wake_class), request.prompt_hash
                )
            except TapeMiss:
                tape_miss = True
                self.n_tape_misses += 1
                source = "tape_miss"
            else:
                observed_tick = int(hit.observed_tick)
                if hit.deferred:
                    # **答えの返らなかった呼**。パースも未定義行動5段も通さない
                    # (本番の ``FleetBridge._interpret`` が ``Deferred`` を素通しするのと同じ)。
                    self.n_deferred += 1
                    self._append_tape(
                        request,
                        rendered,
                        text="",
                        tokens_in=0,
                        tokens_out=0,
                        deferred=1,
                        deferred_reason=hit.deferred_reason,
                        observed_tick=observed_tick,
                    )
                    return BridgeResult(
                        agent_id=int(agent_id),
                        tick=int(tick),
                        wake_class=int(wake_class),
                        condition=int(condition),
                        t_apply=int(tick) + delta_think_ticks(lane, self.tick_seconds),
                        lane=lane,
                        text="",
                        parse=parse_two_line("", self.vocab_version),
                        action_code=UNDEFINED_ACTION,
                        target=NO_TARGET_VALUE,
                        prompt_hash=rendered.prompt_hash or request.prompt_hash,
                        tape_prompt_hash=request.prompt_hash,
                        deferred=True,
                        deferred_reason=hit.deferred_reason,
                        observed_tick=observed_tick,
                        source="tape_deferred",
                    )
                text = hit.response
                source = getattr(self.client, "source", "tape")
                tokens_out = estimate_tokens(text)
        else:
            try:
                response = self.client.complete(request)
                text = response.text
                source = response.source
                tokens_in = int(response.tokens_in) or tokens_in
                tokens_out = int(response.tokens_out)
            except TapeMiss:  # pragma: no cover - 実クライアントは投げない(保険)
                tape_miss = True
                self.n_tape_misses += 1
                source = "tape_miss"
        self.n_calls += 1

        parse = parse_two_line(text, self.vocab_version)
        action_code = parse.action_code
        role_action = bool(parse.is_role_action)
        if role_action:
            self.n_role_actions += 1
            # 役割語は effects 先が C4。当面は安全弁(待機)へ落とす(expedient)。
            action_code = int(self._engine_codes["待機"])
        if not parse.format_ok:
            self.n_parse_errors += 1  # 実効(別名許容後)
        if not parse.strict_format_ok:
            self.n_parse_errors_strict += 1  # 厳密(定義を動かさない受入指標)
        if parse.alias_used:
            self.n_label_alias += 1
        if parse.positional_used:
            self.n_positional += 1

        stage = -1
        feedback = ""
        if parse.action is None:
            self.n_unknown_action += 1
            outcome = self.undefined.observe(
                parse.raw_action, int(agent_id), int(tick), request.prompt_hash
            )
            stage = outcome.stage
            feedback = outcome.feedback
            if outcome.mapped and outcome.word in self._engine_codes:
                action_code = int(self._engine_codes[outcome.word])
                self.n_undefined_mapped += 1
                if outcome.stage == 0:
                    self.n_dictionary_mapped += 1
                # **``parse`` は書き換えない**(親判断待ち・下の Note)。
            else:
                action_code = UNDEFINED_ACTION

        self._append_tape(
            request,
            rendered,
            text=text,
            tokens_in=int(tokens_in),
            tokens_out=int(tokens_out),
            observed_tick=observed_tick,
        )

        return BridgeResult(
            agent_id=int(agent_id),
            tick=int(tick),
            wake_class=int(wake_class),
            condition=int(condition),
            t_apply=int(tick) + delta_think_ticks(lane, self.tick_seconds),
            lane=lane,
            text=text,
            parse=parse,
            action_code=int(action_code),
            target=parse.target if parse.action is not None else NO_TARGET_VALUE,
            prompt_hash=rendered.prompt_hash or request.prompt_hash,
            tape_prompt_hash=request.prompt_hash,
            tokens_in=int(tokens_in),
            tokens_out=int(tokens_out),
            undefined_stage=stage,
            undefined_feedback=feedback,
            role_action=role_action,
            tape_miss=tape_miss,
            observed_tick=observed_tick,
            source=source,
        )

    # ---------------------------------------------------------------- テープ書き出し
    def _append_tape(
        self,
        request: LLMRequest,
        rendered: RenderedPrompt,
        *,
        text: str,
        tokens_in: int,
        tokens_out: int,
        deferred: int = 0,
        deferred_reason: str = "",
        observed_tick: int = -1,
    ) -> None:
        """1行(応答行 or 繰り延べ行)を書く。``tape`` が無ければ何もしない。

        逐次ループ宣言(P4): 共有ブロック数(≤6)ぶんのループ 1 本(既存と同じ)。
        """
        if self.tape is None:
            return
        for block_id, block_text in rendered.blocks:
            if block_id in self._interned:
                continue  # 共有ブロック表は内容アドレスで一意=2 回目以降は無駄打ち
            self.tape.intern_block(block_text, estimate_tokens(block_text))
            self._interned.add(block_id)
        self.tape.append(
            TapeRow(
                call_id=request.call_id,
                agent_id=int(request.agent_id),
                tick=int(request.tick),
                wake_class=int(request.wake_class),
                prompt_hash=request.prompt_hash,
                block_ids=request.block_ids,
                params_hash=request.params_hash,
                response=text,
                tokens_in=int(tokens_in),
                tokens_out=int(tokens_out),
                deferred=int(deferred),
                deferred_reason=deferred_reason,
                observed_tick=int(observed_tick),
            )
        )
        self.n_tape_rows += 1

    # ---------------------------------------------------------------- 診断
    @property
    def parse_error_rate(self) -> float:
        """**実効**書式エラー率(C6 ラベル別名を許容した後・診断行の主指標)。"""
        return (self.n_parse_errors / self.n_calls) if self.n_calls else 0.0

    @property
    def parse_error_rate_strict(self) -> float:
        """**厳密**書式エラー率(C6 以前の別名表だけ=B11 実測 1.000 と同じ物差し)。"""
        return (self.n_parse_errors_strict / self.n_calls) if self.n_calls else 0.0

    @property
    def tape_miss_rate(self) -> float:
        """テープ外率(運用設計書 §2.5「テープ外率を診断行へ」)。"""
        return (self.n_tape_misses / self.n_calls) if self.n_calls else 0.0

    def counters(self) -> Mapping[str, float]:
        """診断行に載せる計数。"""
        n = max(1, self.n_calls)
        out: dict[str, float] = {
            "llm_calls": self.n_calls,
            # ---- 二重指標(C6・09-09)。主=実効・併記=厳密 ----
            "parse_errors": self.n_parse_errors,
            "parse_error_rate": self.parse_error_rate,
            "parse_errors_strict": self.n_parse_errors_strict,
            "parse_error_rate_strict": self.parse_error_rate_strict,
            "label_alias_used": self.n_label_alias,
            "label_alias_rate": self.n_label_alias / n,
            "positional_used": self.n_positional,
            "positional_rate": self.n_positional / n,
            # ``dictionary_mapped``(件数)は下の ``undefined.counters()`` が正典。
            # ここは率だけ出す(同じ台帳を複数 bridge で共有しうるため件数は重複させない)。
            "dictionary_mapped_rate": self.n_dictionary_mapped / n,
            "unknown_action": self.n_unknown_action,
            "undefined_mapped": self.n_undefined_mapped,
            "role_actions": self.n_role_actions,
            "tape_misses": self.n_tape_misses,
            "tape_miss_rate": self.tape_miss_rate,
            "tape_deferred": self.n_deferred,
            "tape_rows": self.n_tape_rows,
        }
        out.update({k: float(v) for k, v in self.undefined.counters().items()})
        return out

    def close(self) -> None:
        """テープを閉じる(``TapeWriter`` を持っているときだけ)。"""
        if self.tape is not None:
            self.tape.close()
