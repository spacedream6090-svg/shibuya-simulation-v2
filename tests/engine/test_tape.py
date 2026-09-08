"""engine.tape のテスト: 1呼=1行 Parquet(zstd)・ブロック intern・完全一致リプレイ。"""

from __future__ import annotations

import pyarrow.parquet as pq
import pytest

from shibuya.engine.tape import (
    BLOCKS_FILENAME,
    CALLS_FILENAME,
    CALLS_SCHEMA,
    Replay,
    Tape,
    TapeMiss,
    TapeRow,
    TapeWriter,
    block_id_for,
)

N_ROWS = 1_000


def _write_tape(path, n=N_ROWS) -> tuple[str, str]:
    """共有ブロック2本 + n 行を書く。"""
    with TapeWriter(path, flush_rows=128) as w:
        shared = w.intern_block("共有静的ブロック(全体で1本)", tokens=750)
        cell = w.intern_block("セル依存ブロック", tokens=250)
        for i in range(n):
            w.append(
                TapeRow(
                    call_id=f"call-{i:05d}",
                    agent_id=i % 97,
                    tick=i % 13,
                    wake_class=i % 4,
                    prompt_hash=f"ph{i:05d}",
                    block_ids=(shared, cell),
                    params_hash="pa-t0",
                    response=f"理由: 予定の時間\n行動: 待機 対象: なし ひと言: なし#{i}",
                    tokens_in=1_300,
                    tokens_out=64,
                )
            )
    return shared, cell


def test_write_read_roundtrip(tmp_path):
    shared, cell = _write_tape(tmp_path)
    assert (tmp_path / CALLS_FILENAME).exists()
    assert (tmp_path / BLOCKS_FILENAME).exists()

    tape = Tape(tmp_path)
    assert len(tape) == N_ROWS
    assert tape.n_blocks == 2, "同一本文のブロックは1回だけ保存(intern)"
    assert tape.block_text(shared).startswith("共有静的")
    rows = list(tape.rows())
    assert rows[0].call_id == "call-00000"
    assert rows[0].block_ids == (shared, cell)
    assert rows[-1].tokens_in == 1_300


def test_parquet_is_zstd_and_schema_is_fixed(tmp_path):
    _write_tape(tmp_path, n=10)
    meta = pq.ParquetFile(tmp_path / CALLS_FILENAME).metadata
    codecs = {
        meta.row_group(g).column(c).compression
        for g in range(meta.num_row_groups)
        for c in range(meta.num_columns)
    }
    assert codecs == {"ZSTD"}
    assert pq.read_schema(tmp_path / CALLS_FILENAME).names == CALLS_SCHEMA.names


def test_block_id_is_content_addressed():
    assert block_id_for("同じ本文") == block_id_for("同じ本文")
    assert block_id_for("同じ本文") != block_id_for("違う本文")
    assert len(block_id_for("x")) == 32


def test_replay_hit_and_miss(tmp_path):
    _write_tape(tmp_path, n=50)
    replay = Replay(Tape(tmp_path))
    assert len(replay) == 50

    got = replay.lookup(agent_id=7, tick=7, wake_class=3, prompt_hash="ph00007")
    assert got.endswith("#7")
    assert replay.hits == 1 and replay.misses == 0

    with pytest.raises(TapeMiss):
        replay.lookup(agent_id=7, tick=7, wake_class=3, prompt_hash="ph99999")
    with pytest.raises(TapeMiss):
        replay.lookup(agent_id=999, tick=7, wake_class=3, prompt_hash="ph00007")
    assert replay.misses == 2
    assert replay.miss_rate == pytest.approx(2 / 3)
    assert replay.counters()["tape_misses"] == 2


def test_replay_key_is_all_four_fields(tmp_path):
    with TapeWriter(tmp_path) as w:
        w.append(TapeRow("c0", 1, 2, 3, "ph", (), "pa", "A"))
        w.append(TapeRow("c1", 1, 2, 0, "ph", (), "pa", "B"))
    replay = Replay(tmp_path)
    assert replay.lookup(1, 2, 3, "ph") == "A"
    assert replay.lookup(1, 2, 0, "ph") == "B"
    assert replay.duplicates == 0


def test_duplicate_keys_are_counted(tmp_path):
    with TapeWriter(tmp_path) as w:
        w.append(TapeRow("c0", 1, 2, 3, "ph", (), "pa", "A"))
        w.append(TapeRow("c1", 1, 2, 3, "ph", (), "pa", "B"))
    replay = Replay(tmp_path)
    assert replay.duplicates == 1
    assert replay.lookup(1, 2, 3, "ph") == "B", "後勝ち(記録順の最後)"


def test_empty_tape_is_readable(tmp_path):
    with TapeWriter(tmp_path):
        pass
    replay = Replay(tmp_path)
    assert len(replay) == 0
    with pytest.raises(TapeMiss):
        replay.lookup(0, 0, 0, "x")
    assert replay.miss_rate == 1.0


def test_missing_tape_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Tape(tmp_path / "nope")
