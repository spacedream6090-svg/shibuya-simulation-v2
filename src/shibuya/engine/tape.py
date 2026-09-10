"""engine.tape — LLM 録画テープ(1呼=1行 Parquet/zstd)と完全一致リプレイ。

正典
- 実装計画書 §3: 「録画テープ: **1呼=1行Parquet(zstd)**、共有ブロックは ``block_id`` で intern。
  リプレイは**完全一致**・テープ外は失敗。」
- 運用設計書 §2.5: 「録画リプレイ=LLMテープ(1呼=1行・共有ブロックはID化・``params_hash``)から
  **(agent_id, tick, wake_class, prompt_hash) 完全一致**で引く。テープ外は失敗
  (**黙って実LLMへ落とさない**)・テープ外率を診断行へ。」
- 運用設計書 §1.3: bit 再現はテープリプレイ(デバッグ・検死)専用。

ファイル構成(自前規約=expedient・設計書は「1呼=1行Parquet(zstd)」までしか定めていない)
    <dir>/calls.parquet   1呼=1行(下記スキーマ)
    <dir>/blocks.parquet  共有プロンプトブロック(block_id → text)。``block_id`` は
                          ``blake3(text)`` の先頭16バイト=32桁16進(内容アドレス=重複排除が自明)。

calls.parquet のスキーマ(列順も規約)
    **版1**(``shibuya.tape/1``・C2〜C7):
      call_id(string) / agent_id(int32) / tick(int64) / wake_class(int8) /
      prompt_hash(string) / block_ids(list<string>) / params_hash(string) /
      response(string) / tokens_in(int32) / tokens_out(int32)
    **版2**(``shibuya.tape/2``・D-58・2026-09-10)= 版1 の 10 列に**末尾3列を追加**:
      deferred(int8: 0=応答が返った / 1=繰り延べ) /
      deferred_reason(string: ``llm.fleet.Outcome`` の値。応答行は "") /
      observed_tick(int64: エンジンがこの呼の帰結を**観測した** tick。
                    −1=同 tick 同期(mock/スタブ経路=版1 と同義))

D-58「テープ繰り延べ行」(2026-09-10・自前規約は実装計画書 §8 に記載)
    運用設計書 §2.5 は「1呼=1行」。艦隊経路では**答えが返らなかった呼**(queue full /
    タイムアウト)が翌 tick の起床候補へ再投入される(憲法1=破棄禁止)が、版1 は
    応答の返った呼しか行を持たないため再生が本番と分岐した(本番 c7-day-2 で
    tape_miss 98.7%)。版2 は**繰り延べも 1 行**(応答空・``deferred=1``)にして
    §2.5 の趣旨(1呼=1行・完全一致で引く・テープ外は失敗)を保ったまま拡張する。
    ``observed_tick`` は、応答が**発射 tick より後**に届く艦隊経路で ``t_apply``
    (=運用設計書 §2.4)を再生側で再現するために要る(同期経路は −1)。

逐次ループ宣言(P4)
- ``TapeWriter.append`` / ``flush``: 1呼ごとの Python 呼び出しと、バッファ行数ぶんの
  列組み立てループ(LLM 呼び出し自体が 1件/呼で、1呼=数十〜数百 ms のため律速にならない)。
  行は ``flush_rows`` ごとに Arrow へ一括変換する。
- ``Replay.__init__``: テープ行数ぶんのループ1本(索引作成)。リプレイ=デバッグ・検死専用
  (§1.3)であり本番ランの経路ではない。

expedient
- ``block_id`` の長さ(16バイト)・``call_id`` を文字列にした点(§7 のルーティング
  ``xxhash(call_id) mod 7`` が文字列前提)。
- テープ外を ``TapeMiss`` 例外にした点(「失敗」の具体形は設計書に規定なし)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

import pyarrow as pa
import pyarrow.parquet as pq

from shibuya.core.hashing import blake3_hex

__all__ = [
    "CALLS_FILENAME",
    "BLOCKS_FILENAME",
    "TAPE_COMPRESSION",
    "CALLS_SCHEMA",
    "CALLS_SCHEMA_V1_NAMES",
    "TAPE_SCHEMA_VERSION",
    "TAPE_SCHEMA_METADATA_KEY",
    "BLOCKS_SCHEMA",
    "TapeMiss",
    "TapeDeferred",
    "TapeRow",
    "TapeHit",
    "TapeWriter",
    "Tape",
    "Replay",
    "block_id_for",
]

CALLS_FILENAME = "calls.parquet"
BLOCKS_FILENAME = "blocks.parquet"
TAPE_COMPRESSION = "zstd"
BLOCK_ID_BYTES = 16

#: テープのスキーマ版(Parquet のスキーマ metadata に入る)。D-58 で 1 → 2。
TAPE_SCHEMA_VERSION = "shibuya.tape/2"
TAPE_SCHEMA_METADATA_KEY = b"shibuya.tape.schema"

#: 版1 の列(**この 10 列は順序ごと不変**=版2 は末尾に足すだけ)。
CALLS_SCHEMA_V1_NAMES: tuple[str, ...] = (
    "call_id",
    "agent_id",
    "tick",
    "wake_class",
    "prompt_hash",
    "block_ids",
    "params_hash",
    "response",
    "tokens_in",
    "tokens_out",
)

CALLS_SCHEMA = pa.schema(
    [
        pa.field("call_id", pa.string(), nullable=False),
        pa.field("agent_id", pa.int32(), nullable=False),
        pa.field("tick", pa.int64(), nullable=False),
        pa.field("wake_class", pa.int8(), nullable=False),
        pa.field("prompt_hash", pa.string(), nullable=False),
        pa.field("block_ids", pa.list_(pa.string()), nullable=False),
        pa.field("params_hash", pa.string(), nullable=False),
        pa.field("response", pa.string(), nullable=False),
        pa.field("tokens_in", pa.int32(), nullable=False),
        pa.field("tokens_out", pa.int32(), nullable=False),
        # ---- 版2(D-58)。旧テープには無い=読むときは既定値へ落とす ----
        pa.field("deferred", pa.int8(), nullable=False),
        pa.field("deferred_reason", pa.string(), nullable=False),
        pa.field("observed_tick", pa.int64(), nullable=False),
    ],
    metadata={TAPE_SCHEMA_METADATA_KEY: TAPE_SCHEMA_VERSION.encode("utf-8")},
)

#: 版2 で足した列と「旧テープを読むときの既定値」。
CALLS_SCHEMA_V2_DEFAULTS: Mapping[str, Any] = {
    "deferred": 0,
    "deferred_reason": "",
    "observed_tick": -1,
}

BLOCKS_SCHEMA = pa.schema(
    [
        pa.field("block_id", pa.string(), nullable=False),
        pa.field("text", pa.string(), nullable=False),
        pa.field("tokens", pa.int32(), nullable=False),
    ]
)


class TapeMiss(LookupError):
    """テープに無い呼び出しを引いた(=リプレイ失敗。実LLMへは落とさない)。"""


class TapeDeferred(LookupError):
    """引いた行が**繰り延べ行**だった(=この呼に応答は無い・D-58)。

    ``TapeMiss`` の兄弟であって**部分型ではない**: テープ外(失敗)と繰り延べ(記録どおり)
    は別事象で、``except TapeMiss`` で握ると繰り延べがテープ外率へ混じる。
    文字列を返す ``TapeLookup`` 契約(``lookup``)では「応答が無い」を値で表せないので
    例外にした(``llm.fleet.FleetDeferredError`` と同じ手口)。呼び出し側が繰り延べを
    値で受けたいときは ``Replay.lookup_row`` を使う。

    Attributes:
        observed_tick: エンジンが繰り延べを観測した tick(再投入の tick)。
        reason: ``llm.fleet.Outcome`` の値(``deferred_queue_full`` 等)。
    """

    def __init__(self, message: str, *, observed_tick: int = -1, reason: str = "") -> None:
        super().__init__(message)
        self.observed_tick = int(observed_tick)
        self.reason = reason


@dataclass(frozen=True)
class TapeHit:
    """``Replay.lookup_row`` の戻り(1行ぶんの再生に要る欄だけ)。"""

    response: str
    deferred: int = 0
    deferred_reason: str = ""
    observed_tick: int = -1

    @property
    def is_deferred(self) -> bool:
        return bool(self.deferred)


def block_id_for(text: str) -> str:
    """共有プロンプトブロックの内容アドレス ``blake3(text)[:16]`` の16進32桁。"""
    return blake3_hex(text.encode("utf-8"), length=BLOCK_ID_BYTES)


@dataclass(frozen=True)
class TapeRow:
    """1呼=1行(``deferred=1`` なら「答えの返らなかった 1 呼」=D-58)。

    Attributes:
        deferred: 0=応答が返った / 1=繰り延べ(``response`` は空・トークンは 0)。
        deferred_reason: ``llm.fleet.Outcome`` の値(``deferred_queue_full`` /
            ``deferred_timeout`` / ``error_other``)。応答行は ""。
        observed_tick: エンジンが帰結を**観測した** tick(艦隊は発射 tick より後になりうる)。
            −1 = 同 tick 同期(mock/テープ再生の既定=版1 のテープと同義)。
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

    @property
    def key(self) -> tuple[int, int, int, str]:
        """リプレイ鍵 (agent_id, tick, wake_class, prompt_hash)。"""
        return (int(self.agent_id), int(self.tick), int(self.wake_class), self.prompt_hash)

    @property
    def is_deferred(self) -> bool:
        return bool(self.deferred)


@dataclass
class TapeWriter:
    """テープ書き出し(Parquet/zstd)。``with`` で使うか ``close()`` を呼ぶこと。

    Example:
        >>> with TapeWriter(dir_path) as w:               # doctest: +SKIP
        ...     bid = w.intern_block("共有静的ブロック")
        ...     w.append(TapeRow("c0", 1, 0, 0, "ph", (bid,), "pa", "理由: …"))
    """

    path: Path
    flush_rows: int = 4_096
    _rows: list[TapeRow] = field(default_factory=list, init=False, repr=False)
    _blocks: dict[str, tuple[str, int]] = field(default_factory=dict, init=False, repr=False)
    _writer: pq.ParquetWriter | None = field(default=None, init=False, repr=False)
    _n_written: int = field(default=0, init=False, repr=False)
    _n_deferred: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.mkdir(parents=True, exist_ok=True)

    # ---- ブロック intern ----
    def intern_block(self, text: str, tokens: int = -1) -> str:
        """共有プロンプトブロックを登録して ``block_id`` を返す(同一本文は1回だけ保存)。"""
        bid = block_id_for(text)
        if bid not in self._blocks:
            self._blocks[bid] = (text, int(tokens))
        return bid

    @property
    def n_blocks(self) -> int:
        return len(self._blocks)

    @property
    def n_rows(self) -> int:
        """書き出し済み+バッファ中の行数。"""
        return self._n_written + len(self._rows)

    @property
    def n_deferred_rows(self) -> int:
        """うち繰り延べ行(``deferred=1``)の数(D-58 の監査点)。"""
        return self._n_deferred

    # ---- 行の追加 ----
    def append(self, row: TapeRow) -> None:
        """1呼を追加する(応答行でも**繰り延べ行**でも同じ口)。"""
        self._rows.append(row)
        if row.deferred:
            self._n_deferred += 1
        if len(self._rows) >= self.flush_rows:
            self.flush()

    def extend(self, rows: Iterable[TapeRow]) -> None:
        for r in rows:
            self.append(r)

    def flush(self) -> None:
        """バッファを Parquet へ書き出す。"""
        if not self._rows:
            return
        table = pa.Table.from_pydict(
            {
                "call_id": [r.call_id for r in self._rows],
                "agent_id": [int(r.agent_id) for r in self._rows],
                "tick": [int(r.tick) for r in self._rows],
                "wake_class": [int(r.wake_class) for r in self._rows],
                "prompt_hash": [r.prompt_hash for r in self._rows],
                "block_ids": [list(r.block_ids) for r in self._rows],
                "params_hash": [r.params_hash for r in self._rows],
                "response": [r.response for r in self._rows],
                "tokens_in": [int(r.tokens_in) for r in self._rows],
                "tokens_out": [int(r.tokens_out) for r in self._rows],
                "deferred": [int(r.deferred) for r in self._rows],
                "deferred_reason": [r.deferred_reason for r in self._rows],
                "observed_tick": [int(r.observed_tick) for r in self._rows],
            },
            schema=CALLS_SCHEMA,
        )
        if self._writer is None:
            self._writer = pq.ParquetWriter(
                self.path / CALLS_FILENAME, CALLS_SCHEMA, compression=TAPE_COMPRESSION
            )
        self._writer.write_table(table)
        self._n_written += len(self._rows)
        self._rows.clear()

    def close(self) -> None:
        """バッファを吐き、ブロック表を書いて閉じる。"""
        self.flush()
        if self._writer is not None:
            self._writer.close()
            self._writer = None
        elif not (self.path / CALLS_FILENAME).exists():
            pq.write_table(
                CALLS_SCHEMA.empty_table(),
                self.path / CALLS_FILENAME,
                compression=TAPE_COMPRESSION,
            )
        ids = sorted(self._blocks)
        blocks = pa.Table.from_pydict(
            {
                "block_id": ids,
                "text": [self._blocks[b][0] for b in ids],
                "tokens": [self._blocks[b][1] for b in ids],
            },
            schema=BLOCKS_SCHEMA,
        )
        pq.write_table(blocks, self.path / BLOCKS_FILENAME, compression=TAPE_COMPRESSION)

    def __enter__(self) -> "TapeWriter":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class Tape:
    """テープの読み出し(``calls.parquet`` + ``blocks.parquet``)。

    **後方互換**(D-58): 版2 で足した 3 列が無い旧テープ(``shibuya.tape/1``)は
    ``deferred=0`` / ``deferred_reason=""`` / ``observed_tick=-1`` として読む
    (=「全部が同 tick に応答が返った呼」= 版1 の意味そのもの)。
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        calls_path = self.path / CALLS_FILENAME
        if not calls_path.exists():
            raise FileNotFoundError(f"テープが無い: {calls_path}")
        self.calls: pa.Table = pq.read_table(calls_path)
        blocks_path = self.path / BLOCKS_FILENAME
        self.blocks: pa.Table = (
            pq.read_table(blocks_path) if blocks_path.exists() else BLOCKS_SCHEMA.empty_table()
        )
        self._block_text: dict[str, str] = dict(
            zip(self.blocks.column("block_id").to_pylist(), self.blocks.column("text").to_pylist())
        )

    def __len__(self) -> int:
        return self.calls.num_rows

    @property
    def n_blocks(self) -> int:
        return self.blocks.num_rows

    @property
    def schema_version(self) -> str:
        """テープのスキーマ版。metadata が無く新列も無ければ ``shibuya.tape/1``。"""
        meta = self.calls.schema.metadata or {}
        raw = meta.get(TAPE_SCHEMA_METADATA_KEY)
        if raw:
            return raw.decode("utf-8")
        has_v2 = all(n in self.calls.column_names for n in CALLS_SCHEMA_V2_DEFAULTS)
        return TAPE_SCHEMA_VERSION if has_v2 else "shibuya.tape/1"

    @property
    def has_deferred_columns(self) -> bool:
        """版2 の 3 列を持っているか(旧テープは False=全行 deferred 0 として読む)。"""
        return all(n in self.calls.column_names for n in CALLS_SCHEMA_V2_DEFAULTS)

    def block_text(self, block_id: str) -> str:
        """``block_id`` → 本文。未知なら KeyError。"""
        return self._block_text[block_id]

    def column(self, name: str) -> list[Any]:
        """列を Python リストで返す。**旧テープに無い列は既定値で埋める**(D-58 後方互換)。"""
        if name in self.calls.column_names:
            return self.calls.column(name).to_pylist()
        return [CALLS_SCHEMA_V2_DEFAULTS[name]] * self.calls.num_rows

    def rows(self) -> Iterator[TapeRow]:
        """全行を ``TapeRow`` として返す(逐次ループ宣言: 行数ぶん・検死用)。"""
        cols = {name: self.column(name) for name in CALLS_SCHEMA.names}
        for i in range(self.calls.num_rows):
            yield TapeRow(
                call_id=cols["call_id"][i],
                agent_id=cols["agent_id"][i],
                tick=cols["tick"][i],
                wake_class=cols["wake_class"][i],
                prompt_hash=cols["prompt_hash"][i],
                block_ids=tuple(cols["block_ids"][i]),
                params_hash=cols["params_hash"][i],
                response=cols["response"][i],
                tokens_in=cols["tokens_in"][i],
                tokens_out=cols["tokens_out"][i],
                deferred=cols["deferred"][i],
                deferred_reason=cols["deferred_reason"][i],
                observed_tick=cols["observed_tick"][i],
            )


class Replay:
    """テープからの完全一致リプレイ。**テープ外は必ず失敗**(実LLMへ落とさない)。

    Attributes:
        hits: 一致した回数。
        misses: テープ外だった回数(診断行「テープ外率」の分子)。
    """

    def __init__(self, tape: Tape | str | Path) -> None:
        self.tape = tape if isinstance(tape, Tape) else Tape(tape)
        self._index: dict[tuple[int, int, int, str], str] = {}
        #: 版2 の欄 ``(deferred, observed_tick, deferred_reason)``。**既定でない行だけ**入れる
        #: (旧テープ・mock テープでは空 dict のまま=RAM も走査も版1 と同じ)。
        self._meta: dict[tuple[int, int, int, str], tuple[int, int, str]] = {}
        self._duplicates = 0
        # 逐次ループ宣言: テープ行数ぶんの索引作成(検死・デバッグ用の経路)。
        # ``Tape.rows()`` を使わず**索引に要る 8 列だけ**を materialize する
        # (``block_ids`` は list<string> で行あたり数十バイトの Python オブジェクトになり、
        #  390 万行の本番テープでは索引作成の RSS を数 GB 動かす)。
        t = self.tape
        agent = t.column("agent_id")
        tick = t.column("tick")
        wclass = t.column("wake_class")
        phash = t.column("prompt_hash")
        resp = t.column("response")
        defer = t.column("deferred")
        reason = t.column("deferred_reason")
        observed = t.column("observed_tick")
        for i in range(len(agent)):
            key = (int(agent[i]), int(tick[i]), int(wclass[i]), phash[i])
            if key in self._index:
                self._duplicates += 1
            self._index[key] = resp[i]
            d, o = int(defer[i]), int(observed[i])
            if d or o >= 0:
                self._meta[key] = (d, o, reason[i])
            elif self._meta:
                self._meta.pop(key, None)  # 後勝ち(同一鍵の上書き)
        self.hits = 0
        self.misses = 0
        #: うち繰り延べ行を引いた回数(D-58・診断行 ``tape_deferred``)。
        self.deferred_hits = 0

    def __len__(self) -> int:
        return len(self._index)

    @property
    def duplicates(self) -> int:
        """同一鍵が複数回記録されていた件数(後勝ち)。0 でないランは順序の再現に注意。"""
        return self._duplicates

    @property
    def miss_rate(self) -> float:
        """テープ外率(診断行へ載せる値)。"""
        total = self.hits + self.misses
        return (self.misses / total) if total else 0.0

    @property
    def n_deferred_rows(self) -> int:
        """テープに入っている繰り延べ行の数(索引ベース=同一鍵は後勝ち)。"""
        return sum(1 for d, _, _ in self._meta.values() if d)

    def lookup_row(
        self, agent_id: int, tick: int, wake_class: int, prompt_hash: str
    ) -> TapeHit:
        """完全一致で 1 行を引く(**繰り延べ行も値で返す**=D-58)。

        Raises:
            TapeMiss: 一致する行が無い(**黙って実LLMへ落とさない**)。
        """
        key = (int(agent_id), int(tick), int(wake_class), prompt_hash)
        try:
            response = self._index[key]
        except KeyError:
            self.misses += 1
            raise TapeMiss(
                f"テープ外: agent={agent_id} tick={tick} class={wake_class} prompt={prompt_hash}"
            ) from None
        self.hits += 1
        if self._meta:
            deferred, observed, reason = self._meta.get(key, (0, -1, ""))
            if deferred:
                self.deferred_hits += 1
            return TapeHit(response, deferred, reason, observed)
        return TapeHit(response)

    def lookup(self, agent_id: int, tick: int, wake_class: int, prompt_hash: str) -> str:
        """(agent_id, tick, wake_class, prompt_hash) 完全一致で応答を引く。

        Raises:
            TapeMiss: 一致する行が無い(**黙って実LLMへ落とさない**)。
            TapeDeferred: 引いた行が繰り延べ行だった(応答が無い=文字列で表せない)。
        """
        hit = self.lookup_row(agent_id, tick, wake_class, prompt_hash)
        if hit.deferred:
            raise TapeDeferred(
                f"繰り延べ行: agent={agent_id} tick={tick} class={wake_class} "
                f"reason={hit.deferred_reason}",
                observed_tick=hit.observed_tick,
                reason=hit.deferred_reason,
            )
        return hit.response

    def counters(self) -> Mapping[str, float]:
        """診断行に載せる計数。"""
        return {
            "tape_hits": self.hits,
            "tape_misses": self.misses,
            "tape_miss_rate": self.miss_rate,
            "tape_deferred": self.deferred_hits,
        }
