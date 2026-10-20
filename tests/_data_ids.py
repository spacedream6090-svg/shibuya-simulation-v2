# -*- coding: utf-8 -*-
"""data が要る試験の印 ``requires_data(<id>, ...)`` の登録表(第333・3-2-4)。

data(gitignore 下の ``data/``)が無い環境(CI・取り出したばかりの写し・data のつなぎの無い作業木)では、
data を読む試験を**落とさず飛ばす**。飛ばし方は 1 つにそろえる:

- 試験には ``@pytest.mark.requires_data("<id>", ...)`` を付ける(モジュールの ``pytestmark``・関数・既存の
  別名 ``real_data = pytest.mark.requires_data(...)`` のどれでもよい)。id を複数並べたら全部そろったときだけ回す。
- 判定はルートの ``tests/conftest.py`` の ``pytest_collection_modifyitems`` が本表で行い、無ければ
  一律の理由 ``requires_data: <id> が無い`` で飛ばす。``pytest_terminal_summary`` が id ごとの飛ばした数を出す
  (合否にはしない)。
- 関数の途中でしか判定できない所(前に data の要らない assert がある・fixture の中)は
  :func:`skip_unless` を呼ぶ(理由の文言は印と同じ)。

id の形:

- ``<base>``: 下の :data:`SPECIAL` の判定(``world_v2`` は世界資産を読み込める 6 ファイルがそろっていること=
  ``shibuya.world.assets.assets_available`` と同じ)か、:data:`ROOTS` の置き場があること。
- ``<base>:<相対パス>``: :data:`ROOTS` の置き場の下にそのファイル(またはディレクトリ)があること。
  例 ``world_v2:w17_schedule.parquet``・``realworld:road_census_r3/kasyo13.csv``。
  前の ``skipif`` が見ていたファイルをそのまま id にしてある(data のある機械で回る試験の集合を変えない)。

data ではない理由(git の commit の有無・環境変数待ち・合成の世界の形・golden の行の有無・辞書の版)は
本表に載せず、今までどおりの ``pytest.skip`` のまま。
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "data"

#: 置き場(id の ``<base>``)。``<base>:<相対パス>`` はこの下を見る。長い道筋を先に照合する(:func:`id_of`)。
ROOTS: dict[str, Path] = {
    "world_v2": DATA / "world" / "v2",          # 世界資産(W0〜W20 の出力)
    "osm": DATA / "realworld" / "osm",           # OSM の抽出(ODbL)
    "estat": DATA / "realworld" / "estat",       # e-Stat の小地域の境界ほか
    "plateau_2025": DATA / "realworld" / "plateau_2025",  # PLATEAU 2025 の生 CityGML
    "realworld": DATA / "realworld",             # 上の 3 つ以外の現実データ(道路交通センサスなど)
    "plateau": DATA / "plateau",                 # PLATEAU の生 GML と npz
    "odpt": DATA / "odpt",                       # ODPT の駅と時刻表
    "persona_pool": DATA / "persona_pool_v2",    # 人物の素材の pool
    "tape": DATA / "tape",                       # 回収したテープ
    "calendar": DATA / "calendar",               # 祝日の表(無ければ conftest が fixture を写す)
    # 〔第 2 期 2-3b〕W12 の実ダイヤの入力(どちらも gitignore の下・読むだけ)
    "user_timetables": DATA / "user_timetables",  # ユーザーが入手した時刻表の読み取り+ODPT チャレンジ枠の CSV
    "odpt_static": DATA / "realworld_live" / "odpt_static",  # ODPT オープン枠の静的データ(版の日付のフォルダ)
    # 〔第 2 期 2-3〕W9 の影を 7 日の窓に広げた世界資産(活性化は 2-4・本体の v2 は上書きしない)
    "world_stage_2-3": DATA / "world" / "v2_stage_2-3",
    # 〔第 4 期 4-3〕段 10 の差し替えの世界資産(活性化は親=本体の v2 は上書きしない)
    "world_stage_4-3": DATA / "world" / "v2_stage_4-3",
    # 〔第 6 期 6-1〕判断モデルの評価の器(tools/instruments/dm_eval)の実データ(どちらも gitignore の下・読むだけ)
    "evalset": DATA / "evalset",                  # 固定の評価セット(1-10 の situations.jsonl・summary.json)
    "server_retrieval": DATA / "server_retrieval",  # サーバーから回収したテープの元の置き場(1-10 の材料の大半)
}


def _world_v2_loadable() -> bool:
    from shibuya.world.assets import assets_available

    return assets_available(ROOTS["world_v2"])


def _timetables() -> bool:
    return (ROOTS["world_v2"] / "w12_timetables.parquet").exists()


def _w17_promoted() -> bool:
    """実 W17(``w17_schedule.parquet``)が昇格版(golden の鍵の md5)であること。"""
    p = ROOTS["world_v2"] / "w17_schedule.parquet"
    if not p.exists():
        return False
    from shibuya.build import run as build_run

    keys = tuple(build_run.PROTECTED_OUTPUTS["W17"]["w17_schedule.parquet"])
    return hashlib.md5(p.read_bytes()).hexdigest().startswith(keys)


def _calendar() -> bool:
    return (ROOTS["calendar"] / "syukujitsu.csv").is_file()


#: 置き場の有無では決まらない id(判定の関数)。
SPECIAL: dict[str, Callable[[], bool]] = {
    "world_v2": _world_v2_loadable,   # 世界資産を読み込める(6 ファイル)
    "timetables": _timetables,         # 鉄道の時刻表の資産(W12)
    "w17_promoted": _w17_promoted,     # 実 W17 が昇格版(golden の鍵)
    "calendar": _calendar,             # 祝日の CSV
}

PREFIX = "requires_data"


def reason(data_id: str) -> str:
    """飛ばすときの一律の理由。"""
    return f"{PREFIX}: {data_id} が無い"


def _split(data_id: str) -> tuple[str, str]:
    base, sep, rel = data_id.partition(":")
    return base, rel if sep else ""


def check_id(data_id: str) -> None:
    """登録の無い id(書き間違い)なら ``ValueError``。"""
    base, rel = _split(data_id)
    if rel:
        if base not in ROOTS:
            raise ValueError(f"requires_data: 置き場の無い id {data_id!r}(登録={sorted(ROOTS)})")
        return
    if base not in SPECIAL and base not in ROOTS:
        raise ValueError(f"requires_data: 未登録の id {data_id!r}(登録={sorted(set(ROOTS) | set(SPECIAL))})")


@lru_cache(maxsize=None)
def present(data_id: str) -> bool:
    """id の data があるか(プロセスの中で 1 回だけ判定して覚える)。"""
    check_id(data_id)
    base, rel = _split(data_id)
    if rel:
        return (ROOTS[base] / rel).exists()
    if base in SPECIAL:
        return bool(SPECIAL[base]())
    return ROOTS[base].is_dir()


def first_missing(ids: Iterable[str]) -> str | None:
    """並べた id のうち最初に無いもの(全部あれば ``None``)。"""
    for i in ids:
        if not present(i):
            return i
    return None


def skip_unless(data_id: str, *, have: bool | None = None) -> None:
    """関数の途中で data の有無を見て飛ばす(理由は印と同じ)。

    ``have`` を渡したら本表の判定の代わりにその値を使う(読み込んだ資産の中身で決まるもの)。id は数えるために要る。
    """
    check_id(data_id)
    ok = present(data_id) if have is None else bool(have)
    if not ok:
        pytest.skip(reason(data_id))


def id_of(path: str | Path) -> str:
    """data の下の道筋 → id(``<base>:<相対パス>``)。相対の道筋はリポの根からと読む。"""
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    best: tuple[int, str, Path] | None = None
    for base, root in ROOTS.items():
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        depth = len(root.parts)
        if best is None or depth > best[0]:
            best = (depth, base, rel)
    if best is None:
        raise ValueError(f"requires_data: data の置き場の外の道筋 {path}")
    _, base, rel = best
    if not rel.parts:
        return base
    return f"{base}:{rel.as_posix()}"


def ids_of(*paths: str | Path) -> tuple[str, ...]:
    """複数の道筋 → id の並び(``pytest.mark.requires_data(*ids_of(a, b))`` の形で使う)。"""
    return tuple(id_of(p) for p in paths)
