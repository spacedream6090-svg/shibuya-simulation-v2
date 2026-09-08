"""世界カタログ(被覆指標の分母)の凍結検収。

分母は凍結資産(v0.2・57クラス・SHA 34f9fa9d316587be)。Markdown を1文字でも
触れば SHA が動き、ここで落ちる = 「黙って分母が変わらない」ことの門。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shibuya.build.catalog_freeze import (
    CATALOG_MD_RELPATH,
    catalog_sha16,
    extract_catalog_table,
    freeze,
    parse_catalog_rows,
)
from shibuya.manifest.world_catalog import (
    FROZEN_SHA16,
    FROZEN_VERSION,
    load_world_catalog,
    verify_frozen,
)

EXPECTED_COLUMNS = (
    "#",
    "型",
    "クラス",
    "現実数量(bbox/区)",
    "v1状態",
    "v2現在d",
    "初回後d",
    "gate",
    "陣",
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_MD = REPO_ROOT / CATALOG_MD_RELPATH
PACKAGED_JSON = REPO_ROOT / "src/shibuya/manifest/frozen/world_catalog_v0_2.json"


@pytest.fixture(scope="module")
def table() -> str:
    # SHA 規則の前提: UTF-8・改行変換なし(リポジトリ内は LF)
    with CATALOG_MD.open(encoding="utf-8", newline="") as fh:
        return extract_catalog_table(fh.read())


def test_sha16_recomputed_from_markdown(table: str) -> None:
    """(1) Markdown から再計算した SHA が凍結値と一致する。"""
    assert catalog_sha16(table) == FROZEN_SHA16 == "34f9fa9d316587be"


def test_markdown_is_lf_only() -> None:
    """SHA 規則は実バイト依存 — CRLF が混ざったら SHA が動く。"""
    assert b"\r" not in CATALOG_MD.read_bytes()


def test_packaged_catalog_matches_frozen() -> None:
    """(2) 同梱 JSON の SHA・クラス数が凍結値と一致する。"""
    cat = load_world_catalog()
    assert cat.sha16 == FROZEN_SHA16
    assert cat.version == FROZEN_VERSION == "v0.2"
    assert cat.n_classes == 57
    verify_frozen(cat)  # 例外を投げない


def test_row_numbers_are_1_to_57() -> None:
    """(3) `#` 列は "1".."57" で重複がない。"""
    cat = load_world_catalog()
    numbers = [r["#"] for r in cat.rows]
    assert numbers == [str(i) for i in range(1, 58)]
    assert len(set(numbers)) == 57


def test_columns() -> None:
    """(4) 列名9つが凍結時の通り。"""
    cat = load_world_catalog()
    assert cat.columns == EXPECTED_COLUMNS
    assert all(set(r) == set(EXPECTED_COLUMNS) for r in cat.rows)


def test_freeze_reproduces_packaged_json_byte_for_byte(tmp_path: Path) -> None:
    """(5) freeze() の再実行が同梱 JSON をバイト単位で再現する。"""
    out = tmp_path / "world_catalog_v0_2.json"
    payload = freeze(CATALOG_MD, out, version="v0.2")
    assert payload["sha16"] == FROZEN_SHA16
    assert payload["n_classes"] == 57
    assert out.read_bytes() == PACKAGED_JSON.read_bytes()


def test_parse_catalog_rows_matches_packaged(table: str) -> None:
    rows = parse_catalog_rows(table)
    assert len(rows) == 57
    cat = load_world_catalog()
    assert rows == list(cat.rows)
    # 型は E/P/N/I/R のいずれか(カタログ冒頭の凡例)
    assert {r["型"] for r in rows} <= {"E", "P", "N", "I", "R"}


def test_verify_frozen_rejects_drift() -> None:
    from dataclasses import replace

    cat = load_world_catalog()
    with pytest.raises(ValueError, match="SHA"):
        verify_frozen(replace(cat, sha16="0" * 16))
    with pytest.raises(ValueError, match="クラス数"):
        verify_frozen(replace(cat, rows=cat.rows[:56]))


def test_manifest_does_not_import_build() -> None:
    """層契約の自己点検: manifest 単体を新規プロセスで import しても build を引かない。

    import-linter の契約「build は実行時に import されない」の実行時裏取り。
    """
    import subprocess
    import sys

    code = (
        "import sys;"
        "import shibuya.manifest.world_catalog as wc;"
        "assert wc.load_world_catalog().n_classes == 57;"
        "leaked = [m for m in sys.modules if m.startswith('shibuya.build')];"
        "print('LEAKED' if leaked else 'CLEAN')"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "CLEAN", proc.stdout
