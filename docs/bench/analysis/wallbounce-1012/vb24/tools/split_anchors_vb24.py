"""第 2 期 2-4 V6: 錨のファイルを較正側(構築側)と検証側に分ける(**値を読まず鍵の名で機械的に**・値は変えない)。

2-0 の検収(混在)・PENDING 仮-13(〔灰〕は決まるまで検証側と同じ扱い)。封印の層の値は画面にも記録にも出さない=本道具は
JSON を読んで鍵の名で振り分けて書くだけ(値を表示しない)。出力の確かめは「2 本を合わせると元と同じ(鍵と値の全部)」と
「鍵の集まり」だけ(``--check``・値は比べるだけで出さない)。

- ``docs/bench/anchors/presence_anchors_v0.json``(混在)→
  ``presence_calib_anchors_v0.json``(較正側=``anchors.core9_*``=中核 9 町丁目の昼夜間人口〔非〕)と
  ``presence_validation_anchors_v0.json``(検証側=ほかの錨=PT 由来〔灰〕・第 4-1 表〔検〕ほか・``purpose``・``rules``)。
  較正側の ``purpose`` は本道具が書く文(元の文は検証側に残る)。
- ``docs/bench/anchors/hunger_energy_anchors_v0.json``(混在・``usage`` が自ら「validation-only」と書く表を含む)→
  ``hunger_energy_build_anchors_v0.json``(構築側=DRI 2025・国民健康・栄養調査 第 14・13 表・METs と、その ``sources``)と
  ``hunger_energy_validation_anchors_v0.json``(検証側=国民健康・栄養調査 第 10 表・社会生活基本調査 第 18-1 表・15 分の
  食事率・その導出 ``derived``・その ``sources``)。``schema``・``generated_by``・``attribution``・``usage`` は両方に写す。
  エンジン(``engine/energy.py``)は 2 本を読んで 1 つの辞書に戻す(読み口は検証側のファイルを読む形のまま=第 18-1 表の
  置き換えはユーザーの判断の後=PENDING §1-1)。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/split_anchors_vb24.py split   # 4 本を書き、元の 2 本を消す
    python docs/bench/analysis/wallbounce-1012/vb24/tools/split_anchors_vb24.py check [--rev HEAD]  # 合わせて元と同じか
    (元は git の版から読むだけ=元の写しを作業用の置き場に作らない)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
A = REPO / "docs" / "bench" / "anchors"
PRESENCE = A / "presence_anchors_v0.json"
PRESENCE_CALIB = A / "presence_calib_anchors_v0.json"
PRESENCE_VALID = A / "presence_validation_anchors_v0.json"
HUNGER = A / "hunger_energy_anchors_v0.json"
HUNGER_BUILD = A / "hunger_energy_build_anchors_v0.json"
HUNGER_VALID = A / "hunger_energy_validation_anchors_v0.json"

#: 在圏の錨: 較正側の錨の名の頭(R-115 §2 の〔非〕=中核 9 町丁目)。ほかの錨は検証側(〔灰〕は決まるまで検証側=仮-13)。
PRESENCE_CALIB_PREFIX = "core9_"
#: 在圏の錨の表の見出し: 両方に写す(構造)/検証側だけ(元の文)。
PRESENCE_META_BOTH = ("schema", "version", "created")
#: 空腹の錨: 構築側の表(DRI・NHNS 第 14・13 表・METs)と、その元(``sources`` の鍵)。ほかの表は検証側。
HUNGER_BUILD_TABLES = ("dri2025", "nhns_t14_weight", "nhns_t13_meal_kcal", "mets_2012")
HUNGER_BUILD_SOURCES = ("bmr_pal_2025.json", "nhns_r6_height_weight.json", "nhns_r6_meal_kcal.json", "mets_selected.json")
HUNGER_META_BOTH = ("schema", "generated_by", "attribution", "usage")
SPLIT_NOTE = ("第 2 期 2-4 V6: 元のファイル {src} を鍵の名で機械的に分けた(値は変えていない・値を読まずに分けた)。"
              "較正側/構築側と検証側の 2 本=記録 docs/bench/analysis/wallbounce-1012/vb24/README.md の V6")


def _dump(doc: dict) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def split_presence(doc: dict) -> tuple[dict, dict]:
    calib: dict = {k: doc[k] for k in PRESENCE_META_BOTH if k in doc}
    valid: dict = {k: doc[k] for k in PRESENCE_META_BOTH if k in doc}
    calib["purpose"] = ("較正側の錨(中核 9 町丁目の昼夜間人口=都の第 11 表〔非〕・R-115 §2)。2-0 の計器と較正が読む。"
                        "検証側の錨は presence_validation_anchors_v0.json(計器も較正も読まない)")
    calib["split_from"] = SPLIT_NOTE.format(src="presence_anchors_v0.json")
    valid["split_from"] = calib["split_from"]
    for k, v in doc.items():
        if k in PRESENCE_META_BOTH or k == "anchors":
            continue
        valid[k] = v  # purpose・rules ほか(元の文)は検証側
    calib["anchors"] = {k: v for k, v in doc["anchors"].items() if k.startswith(PRESENCE_CALIB_PREFIX)}
    valid["anchors"] = {k: v for k, v in doc["anchors"].items() if not k.startswith(PRESENCE_CALIB_PREFIX)}
    return calib, valid


def _builder():
    """錨の生成器 ``tools/hunger/build_hunger_anchors.py``(分け方 ``split_doc`` の正=生成器が同じ 2 本を書く)。"""
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_hunger_anchors", REPO / "tools" / "hunger" / "build_hunger_anchors.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def split_hunger(doc: dict) -> tuple[dict, dict]:
    """生成器の ``split_doc`` で分ける(鍵の名の表=``HUNGER_BUILD_TABLES``・``HUNGER_BUILD_SOURCES`` と同じ)。"""
    b = _builder()
    assert tuple(b.BUILD_TABLES) == HUNGER_BUILD_TABLES and tuple(b.BUILD_SOURCES) == HUNGER_BUILD_SOURCES
    return b.split_doc(doc)


def merge(a: dict, b: dict) -> dict:
    """2 本を 1 つの辞書に戻す(エンジンの読み口と同じ規則: 表と ``sources``・``anchors`` は合わせる・見出しは前の側)。"""
    out = dict(a)
    for k, v in b.items():
        if k in ("sources", "anchors") and isinstance(v, dict):
            out[k] = {**out.get(k, {}), **v}
        elif k not in out:
            out[k] = v
    out.pop("split_from", None)
    return out


def cmd_split(_a: argparse.Namespace) -> int:
    p = json.loads(PRESENCE.read_text(encoding="utf-8"))
    pc, pv = split_presence(p)
    h = json.loads(HUNGER.read_text(encoding="utf-8"))
    hb, hv = split_hunger(h)
    for path, doc in ((PRESENCE_CALIB, pc), (PRESENCE_VALID, pv), (HUNGER_BUILD, hb), (HUNGER_VALID, hv)):
        path.write_text(_dump(doc), encoding="utf-8", newline="\n")
    PRESENCE.unlink()
    HUNGER.unlink()
    print("在圏: 較正側の錨", sorted(pc["anchors"]), "/ 検証側の錨", len(pv["anchors"]), "本(名は出さない)")
    print("空腹: 構築側の表", sorted(k for k in hb if k in HUNGER_BUILD_TABLES), "/ 検証側の表",
          sorted(k for k in hv if k not in HUNGER_META_BOTH and k not in ("sources", "split_from")))
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    """git の版(``--rev``)の元のファイルと、分けた 2 本を合わせたものが鍵と値の全部で同じか(値は出さない・写しを作らない)。"""
    import subprocess

    ok = True
    for orig, x, y, keep_meta in ((PRESENCE, PRESENCE_CALIB, PRESENCE_VALID, ("purpose",)),
                                  (HUNGER, HUNGER_BUILD, HUNGER_VALID, ())):
        rel = orig.relative_to(REPO).as_posix()
        raw = subprocess.run(["git", "show", f"{a.rev}:{rel}"], cwd=REPO, capture_output=True, check=True).stdout
        d0 = json.loads(raw.decode("utf-8"))
        dx = json.loads(x.read_text(encoding="utf-8"))
        dy = json.loads(y.read_text(encoding="utf-8"))
        m = merge(dy, dx) if keep_meta else merge(dx, dy)  # 在圏は元の purpose が検証側にある
        same = m == d0
        ok &= same
        print(orig.name, "合わせると元と同じ:", same, "鍵", sorted(m) == sorted(d0))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("split")
    c = sub.add_parser("check")
    c.add_argument("--rev", default="HEAD")
    a = ap.parse_args(argv)
    return {"split": cmd_split, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
