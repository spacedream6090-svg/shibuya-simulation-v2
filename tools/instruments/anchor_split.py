# -*- coding: utf-8 -*-
"""anchor_split — 錨のファイルを区分(構築側/検証側)ごとに**鍵の名で機械的に**分ける(第337・封印の分離の残り)。

正: 回答 10-13b §7 の 5(封印の値と他のデータが混ざっているファイルの分離の残り)・PENDING 仮-13(〔灰〕は決まるまで
検証側と同じ扱い)・パターン台帳 §10-2(社会生活基本調査=使っていない表は検証側)・§10-3(なじみの場所の法則
=Alessandretti・Song は構築・初期化に使ったので検証に使わない)・R-115 §2(第 31/36 表は W17 v2 の勤務窓の入力=〔写〕)。
2-4 V6 の道具(``docs/bench/analysis/wallbounce-1012/vb24/tools/split_anchors_vb24.py``)と同じ作法。

**値は読まない・画面に出さない**: JSON を読んで鍵の名で振り分けて書くだけ。確かめ(``check``)は
「2 本を合わせると元と鍵と値の全部で同じか」「錨ごとの md5(正規化した JSON)が元と同じか」を真偽と数だけで出す
(値も md5 の桁も出さない)。元は git の版から読む(元の写しを作業用の置き場に作らない)。

本段で分けるもの(``PLANS``):

- ``docs/bench/anchors/diversity_anchors_v0.json``(混在)→
  ``diversity_build_anchors_v0.json``(検証に使わない側=第 31 表の雇用形態別の帯〔写〕・Song 2010 の 3 本と
  Alessandretti 2018 の 2 本(§10-3)・設計書 §5 の前値 ``p0_prior``(現実の錨ではない))と
  ``diversity_validation_anchors_v0.json``(検証側=第 30 表の 6 本〔検〕・Schneider 2013 の 5 本〔灰〕=区分が
  未決なので仮-13 のとおり検証側・元の ``purpose``・``rules``)。``schema``・``version``・``created`` は両方に写す。

    python tools/instruments/anchor_split.py split diversity     # 2 本を書き、元を消す
    python tools/instruments/anchor_split.py check diversity [--rev HEAD]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

REPO = Path(__file__).resolve().parents[2]
A = REPO / "docs" / "bench" / "anchors"


@dataclass(frozen=True)
class Plan:
    src: str
    build: str
    validation: str
    build_anchors: tuple[str, ...]
    validation_anchors: tuple[str, ...]
    meta_both: tuple[str, ...]
    build_extra: tuple[str, ...]      # 錨の外の鍵で構築側へ行くもの
    build_purpose: str
    why: Mapping[str, str]            # 錨の名 → 区分の根拠(記録と試験で使う・読むだけの表)


_DIV_BUILD = ("depart_on_00_30_band_by_employment",
              "song_pi_max", "song_regularity_R", "song_top2_locations_share",
              "activity_set_capacity", "activity_set_jaccard_decay_lambda")
_DIV_VALID = ("tokyo_weekday_depart_on_00_30", "tokyo_weekday_depart_top_bin_share",
              "tokyo_weekday_depart_top_hour_share", "tokyo_weekday_depart_entropy_bits",
              "national_weekday_depart_on_00_30", "national_weekday_depart_entropy_bits",
              "motif_count", "motif_coverage", "motif_threshold",
              "daily_locations_lt7_share", "daily_locations_lognormal")
_WHY: Mapping[str, str] = MappingProxyType({
    **{k: "第 30 表〔検〕(§10-2 の使っていない表=影の段の比較)" for k in _DIV_VALID if "weekday_depart" in k},
    **{k: "Schneider 2013〔灰〕(区分が未決=仮-13 のとおり検証側)" for k in _DIV_VALID
       if k.startswith(("motif_", "daily_locations"))},
    "depart_on_00_30_band_by_employment": "第 31 表〔写〕(W17 v2 の勤務窓の入力=R-115 §2)",
    **{k: "Song 2010(§10-3=構築・初期化に使ったので検証に使わない)" for k in _DIV_BUILD if k.startswith("song_")},
    **{k: "Alessandretti 2018(§10-3=同上)" for k in _DIV_BUILD if k.startswith("activity_set")},
})
PLANS: Mapping[str, Plan] = MappingProxyType({
    "diversity": Plan(
        src="diversity_anchors_v0.json",
        build="diversity_build_anchors_v0.json",
        validation="diversity_validation_anchors_v0.json",
        build_anchors=_DIV_BUILD,
        validation_anchors=_DIV_VALID,
        meta_both=("schema", "version", "created"),
        build_extra=("p0_prior",),
        build_purpose=("検証に使わない側の錨(第 31 表の雇用形態別の帯=W17 v2 の勤務窓の入力〔写〕・Song 2010 と "
                       "Alessandretti 2018=パターン台帳 §10-3)と設計書 §5 の前値 p0_prior(現実の錨ではない)。"
                       "検証側(第 30 表〔検〕・Schneider 2013〔灰〕)は diversity_validation_anchors_v0.json"),
        why=_WHY,
    ),
})
SPLIT_NOTE = ("第337 封印の分離の残り: 元のファイル {src} を鍵の名で機械的に分けた(値は変えていない・値を読まずに分けた)。"
              "構築側(検証に使わない側)と検証側の 2 本=記録 docs/bench/analysis/wallbounce-1012/seal_tidy/README.md")


def _dump(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def split_doc(plan: Plan, doc: dict) -> tuple[dict, dict]:
    """元の辞書 → (構築側, 検証側)。錨の名が表に無いもの・両方にあるものは止める(推測で振らない)。"""
    names = set(doc.get("anchors", {}))
    b, v = set(plan.build_anchors), set(plan.validation_anchors)
    if b & v:
        raise ValueError("構築側と検証側の両方に同じ名がある")
    if names != b | v:
        raise ValueError(f"表に無い錨の名がある/表の名が元に無い(数 {len(names ^ (b | v))})")
    build: dict = {k: doc[k] for k in plan.meta_both if k in doc}
    valid: dict = {k: doc[k] for k in plan.meta_both if k in doc}
    build["purpose"] = plan.build_purpose
    build["split_from"] = SPLIT_NOTE.format(src=plan.src)
    valid["split_from"] = build["split_from"]
    for k, val in doc.items():
        if k in plan.meta_both or k == "anchors":
            continue
        (build if k in plan.build_extra else valid)[k] = val
    build["anchors"] = {k: a for k, a in doc["anchors"].items() if k in b}
    valid["anchors"] = {k: a for k, a in doc["anchors"].items() if k in v}
    return build, valid


def merge(build: dict, valid: dict, *, purpose_from_validation: bool = True) -> dict:
    """2 本を 1 つに戻す(読み手と同じ規則: ``anchors`` は合わせる・見出しは検証側の元の文を優先)。"""
    out: dict = {}
    first, second = (valid, build) if purpose_from_validation else (build, valid)
    for d in (first, second):
        for k, val in d.items():
            if k == "split_from":
                continue
            if k == "anchors":
                out.setdefault("anchors", {}).update(val)
            elif k not in out:
                out[k] = val
    return out


def anchor_md5(a: object) -> str:
    return hashlib.md5(json.dumps(a, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def cmd_split(a: argparse.Namespace) -> int:
    plan = PLANS[a.plan]
    src = A / plan.src
    b, v = split_doc(plan, json.loads(src.read_text(encoding="utf-8")))
    for name, doc in ((plan.build, b), (plan.validation, v)):
        (A / name).write_text(_dump(doc), encoding="utf-8", newline="\n")
    src.unlink()
    print(f"{plan.src}: 構築側の錨 {len(b['anchors'])} 本 {sorted(b['anchors'])}・検証側の錨 {len(v['anchors'])} 本"
          f"(名は出さない)・構築側の錨の外の鍵 {sorted(k for k in b if k in plan.build_extra)}")
    return 0


def check(plan: Plan, rev: str = "HEAD") -> dict:
    """git の版の元と 2 本を比べる(真偽と数だけ)。"""
    rel = (A / plan.src).relative_to(REPO).as_posix()
    raw = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=REPO, capture_output=True, check=True).stdout
    d0 = json.loads(raw.decode("utf-8"))
    db = json.loads((A / plan.build).read_text(encoding="utf-8"))
    dv = json.loads((A / plan.validation).read_text(encoding="utf-8"))
    m = merge(db, dv)
    per = [anchor_md5(d0["anchors"][k]) == anchor_md5({**db["anchors"], **dv["anchors"]}[k]) for k in d0["anchors"]]
    extra_same = all(d0[k] == db[k] for k in plan.build_extra if k in d0)
    return {"merged_equals_original": m == d0, "keys_equal": sorted(m) == sorted(d0),
            "anchors_md5_equal": f"{sum(per)}/{len(per)}", "build_extra_equal": extra_same,
            "no_overlap": not (set(db["anchors"]) & set(dv["anchors"]))}


def cmd_check(a: argparse.Namespace) -> int:
    r = check(PLANS[a.plan], a.rev)
    print(json.dumps(r, ensure_ascii=False))
    ok = r["merged_equals_original"] and r["keys_equal"] and r["build_extra_equal"] and r["no_overlap"]
    n, d = r["anchors_md5_equal"].split("/")
    return 0 if ok and n == d else 1


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("split")
    s.add_argument("plan", choices=sorted(PLANS))
    c = sub.add_parser("check")
    c.add_argument("plan", choices=sorted(PLANS))
    c.add_argument("--rev", default="HEAD")
    a = ap.parse_args(argv)
    return {"split": cmd_split, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
