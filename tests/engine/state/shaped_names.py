"""移す段 2-1 の拾い(検収 M4): 短いランの manifest・run_meta・テープの見出し・ハッシュに入る文字列から、モジュールの道の形の
部分を拾う。凍結(``names_frozen.json`` の ``run_path_shaped``)の道具と試験が使う(試験の本体ではない)。

    python tests/engine/state/shaped_names.py <構成の名>      # 拾った結果を JSON で出す(子のプロセスで回す口)

- 道の形: 点の道(``engine.energy``・``shibuya.tape``)と斜線の道(``engine/energy.py``・``src/shibuya/…``)。頭の部品が
  :data:`PACKAGES`(今の包みの名と、移した後の包みの名=計画 ``docs/reference/package-map-final-2026-11-09.md`` §1-1)の
  もの。日本語の文の中に埋まっていても拾う(拾うのは道の形の部分だけ・ASCII の名の境で切る)。
- 拾う所: ``RunResult.run_manifest_fields()`` の鍵と文字列の値・テープの ``run_meta.json`` の鍵と値・テープの Parquet の
  スキーマの metadata の鍵と値・ハッシュに入る文字列(``state_hashes._str`` に渡る名と値・外の状態の行の ``鍵:道筋``)。
- 構成(:data:`CONFIGS`)は子のプロセスで 1 つずつ回す(腕の切替口は読み込みのときに環境変数を読むため・ハッシュの口の
  差し替えをほかの試験に持ち越さないため)。世界資産の構成は data が要る。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

#: 道の形の頭の部品(今の包み 11 と、移した後の包み=計画 §1-1 の 12 から重なりを除いたもの)。固定の一覧(包みを動かしても
#: 前の名の道を拾い続ける)。
PACKAGES: tuple[str, ...] = (
    "agents", "build", "census", "cli", "core", "economy", "engine", "llm", "manifest", "perception", "world",
    "act", "experiments", "foundation", "interfaces", "interim_bundles", "mind", "runtime", "society", "validation",
)
_P = "|".join(PACKAGES)
DOT = re.compile(rf"(?<![A-Za-z0-9_.])(?:shibuya(?:\.[A-Za-z_][A-Za-z0-9_]*)+|(?:{_P})(?:\.[A-Za-z_][A-Za-z0-9_]*)+)",
                 re.ASCII)
SLASH = re.compile(rf"(?<![A-Za-z0-9_./\\-])(?:src/)?(?:shibuya/)?(?:{_P})/[A-Za-z0-9_./]*", re.ASCII)
SOURCES: tuple[str, ...] = ("manifest", "run_meta", "tape_meta", "hash")

#: 腕 on の追加の確かめの 7 変数(``tools/bytecheck/configs.py`` の ``ARMS_ENV`` と同じ)。
ARMS_ENV: dict[str, str] = {
    "SHIBUYA_CALENDAR": "1b", "SHIBUYA_DECISION_PORT": "port", "SHIBUYA_CONTACT": "c1", "SHIBUYA_CONTACT_HABIT": "on",
    "SHIBUYA_CALENDAR_2": "arm", "SHIBUYA_CALENDAR_3": "arm", "SHIBUYA_DUTIES": "arm",
}
_SYN_ALL = dict(vocab_version="v3", memory="on", relations="on", store_memory="on", familiarity="on",
                hunger_model="energy", rel_copresent="on", policy="classical", chooser="classical")
#: 構成の名 → (種類, 引数, 環境変数)。``syn``=合成の小世界の ``run_day``(data 不要)・``world``=世界資産の ``cli.run``。
CONFIGS: dict[str, tuple[str, dict[str, Any], dict[str, str]]] = {
    "syn_default": ("syn", dict(n_agents=60, n_cells=9, ticks=240, checkpoint_every=60), {}),
    "syn_all_arms_classical": ("syn", dict(n_agents=60, n_cells=9, ticks=1440, checkpoint_every=360, **_SYN_ALL), {}),
    "world_v3_default": ("world", dict(n_agents=300, vocab_version="v3", activity=True), {}),
    "world_v3_classical_mem_rel": ("world", dict(n_agents=300, vocab_version="v3", memory="on", relations="on",
                                                 policy="classical", chooser="classical"), {}),
    "world_v1_edge_plateau_old": ("world", dict(n_agents=300, vocab_version="v1", geometry="edge",
                                                area_source="plateau", report_precondition=False), {}),
    "world_v3_arms_env": ("world", dict(n_agents=300, vocab_version="v3", activity=True), dict(ARMS_ENV)),
}


def shaped(text: str) -> list[str]:
    """文字列の中の道の形の部分(出てくる順)。"""
    return [*DOT.findall(text), *SLASH.findall(text)]


def _strings(v: Any, out: set[str]) -> None:
    if isinstance(v, dict):
        for k, x in v.items():
            out.add(str(k))
            _strings(x, out)
    elif isinstance(v, (list, tuple)):
        for x in v:
            _strings(x, out)
    elif isinstance(v, str):
        out.add(v)


def collect_here(name: str) -> dict[str, list[str]]:
    """このプロセスで構成 ``name`` を回して拾う(子のプロセスの中で呼ぶ=ハッシュの口を差し替える)。"""
    import pyarrow.parquet as pq

    from shibuya.runtime.state import hashes as SH

    kind, kw, _env = CONFIGS[name]
    seen: dict[str, set[str]] = {s: set() for s in SOURCES}
    real_str, real_item = SH._str, SH.item_digest

    def _str(f: Any, tag: bytes, s: str) -> None:
        seen["hash"].add(s)
        real_str(f, tag, s)

    def _item(owners: Any, key: str, path: str) -> Any:
        seen["hash"].add(f"{key}:{path}")
        return real_item(owners, key, path)

    SH._str, SH.item_digest = _str, _item
    with tempfile.TemporaryDirectory() as d:
        tape = Path(d) / "tape"
        if kind == "world":
            from shibuya import cli

            res = cli.run(seed=1, world_dir="data/world/v2", tape_path=str(tape), **kw)
        else:
            from shibuya.engine.run import run_day

            res = run_day(seed=1, tape_path=tape, **kw)
        _strings(res.run_manifest_fields(), seen["manifest"])
        _strings(json.loads((tape / "run_meta.json").read_text(encoding="utf-8")), seen["run_meta"])
        for p in sorted(tape.glob("*.parquet")):
            for k, v in (pq.read_schema(p).metadata or {}).items():
                seen["tape_meta"] |= {k.decode("utf-8", "replace"), v.decode("utf-8", "replace")}
    return {s: sorted({m for text in seen[s] for m in shaped(text)}) for s in SOURCES}


def run_config(name: str, *, repo: Path, src: Path) -> dict[str, list[str]]:
    """子のプロセスで構成 ``name`` を回して拾った結果(``repo`` で回す=data の相対の道筋・``src`` を読む)。"""
    env = {k: v for k, v in os.environ.items() if not k.startswith("SHIBUYA_")}
    env.update(CONFIGS[name][2])
    env["PYTHONPATH"] = str(src)
    env["PYTHONIOENCODING"] = "utf-8"
    cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), name], cwd=str(repo), env=env,
                        capture_output=True, text=True, encoding="utf-8", timeout=900)
    if cp.returncode != 0:
        raise RuntimeError(f"{name}: 子のプロセスが失敗(終了コード {cp.returncode}): {cp.stderr[-2000:]}")
    return json.loads(cp.stdout.strip().splitlines()[-1])


if __name__ == "__main__":
    print(json.dumps(collect_here(sys.argv[1]), ensure_ascii=False))
