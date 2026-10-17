# -*- coding: utf-8 -*-
"""dm_eval.cli — 評価の器を 1 回通して、記録の JSON と表を書く(第 6 期 6-1・読むだけ・GPU とネットワークは使わない)。

使い方(リポの根で・``PYTHONPATH`` に作業木の ``src``)::

    python tools/instruments/dm_eval/cli.py run --out-dir docs/bench/analysis/wallbounce-1012/dm61

書くもの(``--out-dir`` の下・既にあれば ``--overwrite`` が無い限り書かない):
    - ``result.json``: 入力の md5・候補の集計・長さの集計・当て口ごとの採点(一致・迷い・その他の率・位置の偏り・
      速さの欄)・正の対照・テープの固定の並び・厳密モードの検査・空欄の宣言・``digest``(壁時計を除いた決定的な部分の
      sha256=golden)。**テープの本文と状況の文は写さない**(集計だけ)。絶対パスは書かない。
    - ``table.md``・``table.json``: 表「人らしさ × 速さ × 1 シム日あたりの GPU 時間」(順位なし)。

関数 ``evaluate`` は data を読まない(状況と経験を渡す)=合成の状況で試験できる。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in (None, ""):  # pragma: no cover - スクリプトとして実行したとき
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dm_eval  # noqa: E402
from dm_eval import bias as B  # noqa: E402
from dm_eval import judge as J  # noqa: E402
from dm_eval import situations as S  # noqa: E402
from dm_eval import table as T  # noqa: E402
from shibuya.engine.decision.port import OTHER_ID  # noqa: E402

#: 決定的でない欄(digest から外す)。
_VOLATILE_KEYS = frozenset({"wall_s_per_item", "wall_s", "timing"})
_DIGEST_DECIMALS = 10

LIMITS = (
    "正解の表は作らない(人のデータと考慮集合の研究の値は検証側=パターン台帳 §10-1・人のデータとの照合は欄だけ)",
    "言語は日本語だけ(材料の B0 が日本語で書くと決めている)・住人の第一言語の欄は空欄(§4-8)",
    "B5・B6 が無い(1-10 §5 の 1)=近い予定・近くの人・空腹と疲れ・招待が入力に無い=体と事情の無い判断(親の注 §9 の (b))",
    "テープの当て口は B0 の固定の並びへの答え=ここで入れ替えた並びは見ていない(並べ替えに対しては構成上 0)",
    "Clef-flash・Clef・Kev-9B・即断・(G) は口だけ=人らしさ・速さ・GPU 時間の欄は GPU の後(S6)",
    "長さの腕 t300 は B0 を外すだけ(DM4 (a) の人ごとの短い特徴量の描画は engine に無い)・トークン数は後で測る",
)


def _round(x: Any) -> Any:
    if isinstance(x, float):
        return round(x, _DIGEST_DECIMALS)
    if isinstance(x, Mapping):
        return {str(k): _round(v) for k, v in x.items() if str(k) not in _VOLATILE_KEYS}
    if isinstance(x, (list, tuple)):
        return [_round(v) for v in x]
    return x


def digest_of(result: Mapping[str, Any]) -> str:
    """壁時計を除き、小数を 10 桁に丸めた決定的な部分の sha256(golden)。"""
    body = {k: v for k, v in result.items() if k not in ("digest", "table")}
    canon = json.dumps(_round(body), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def table_footnotes(floor: Mapping[str, Any], tape_fixed: Mapping[str, Any]) -> list[str]:
    """表の脚注(PBS の帰無の床=フロア併記・提示の並びを見ていない当て口の注)。"""
    out = []
    for n, f in floor.items():
        out.append(f"PBS の帰無の床(中身だけで選ぶ当て口の模擬・候補 {n}・{f['reps']:,} 回): 平均 {f['mean']:.3f}・"
                   f"5〜95% {f['p05']:.3f}〜{f['p95']:.3f}(この幅の中の PBS は偏りの証拠にならない)")
    out.append("テープの行: " + T.order_blind_note(tape_fixed))
    return out


def evaluate(situations: Sequence[S.Situation], experience: Mapping[str, Sequence[str]] | None = None, *,
             seed: str | int = S.DEFAULT_SEED, n_orders: int = S.DEFAULT_N_ORDERS,
             mock_seed: str | int = "dm61-mock", arms: Sequence[str] = tuple(S.LENGTH_ARMS),
             strict: bool = True) -> dict[str, Any]:
    """状況(と本人の経験の代わり)→ 採点の結果(data は読まない)。"""
    t_all = time.perf_counter()
    exp = dict(experience or {})
    cands = {s.sid: S.candidates_for(s, exp.get(s.sid, ())) for s in situations}
    ords = {s.sid: S.orders(cands[s.sid], s.sid, n_orders=n_orders, seed=seed) for s in situations}
    kinds = {sid: {**{c.id: c.kind for c in cs}, OTHER_ID: OTHER_ID} for sid, cs in cands.items()}
    lengths = S.iter_lengths(situations, {sid: o[0] for sid, o in ords.items()})

    scorers = J.scorer_registry(mock_seed=mock_seed)
    computed: dict[str, dict[str, Any]] = {}
    for sc in scorers:
        if not sc.implemented:
            continue
        per_arm: dict[str, Any] = {}
        cache: tuple[dict[str, list[B.Record]], float | None] | None = None
        for arm in arms:
            if cache is None or sc.reads_text:
                cache = B.score_orders(sc, situations, ords, arm=arm)
            records, wall = cache
            per_arm[arm] = {"records": records, "wall": wall}
        computed[sc.name] = per_arm

    def first_dists(name: str, arm: str) -> dict[str, dict[str, float]]:
        return {sid: recs[0][1] for sid, recs in computed[name][arm]["records"].items()}

    out_scorers: list[dict[str, Any]] = []
    for sc in scorers:
        entry: dict[str, Any] = {"describe": sc.describe(), "by_arm": {}}
        for arm in arms:
            if not sc.implemented:
                entry["by_arm"][arm] = {"status": "GPU の後(S6)", "speed": J.speed_fields(sc, None),
                                        "human": dict(J.HUMAN_FIELDS)}
                continue
            d0 = first_dists(sc.name, arm)
            recs = computed[sc.name][arm]["records"]
            entry["by_arm"][arm] = {
                "agreement_vs_classical": None if sc.name == "classical" else
                J.agreement(d0, first_dists("classical", arm), kinds),
                "agreement_vs_tape": None if sc.name == "tape" else J.agreement(d0, first_dists("tape", arm), kinds),
                "agreement_vs_g": None,
                "hesitation": J.hesitation_summary(d0),
                "surprise": None,
                "other_rate": J.other_rate(d0),
                "position_bias": B.position_bias(recs),
                "human": dict(J.HUMAN_FIELDS),
                "speed": J.speed_fields(sc, computed[sc.name][arm]["wall"]),
                "same_as_arm": None if sc.reads_text or arm == arms[0] else arms[0],
            }
        out_scorers.append(entry)

    control = J.FirstNumberControl()
    crecs, _ = B.score_orders(control, situations, ords, arm=arms[0])
    controls = {control.name: {"describe": control.describe(), "position_bias": B.position_bias(crecs)}}
    sizes = sorted({len(c) for c in cands.values()})
    floor = {str(n): B.pbs_null_floor(len(situations), n, S.rotation_offsets(n, n_orders)) for n in sizes}
    tape_fixed = B.tape_fixed_order(situations)

    strict_out: list[dict[str, Any]] = []
    if strict:
        items = [(s, pres, None) for s in situations for pres in ords[s.sid]]
        makers = (lambda: J.MockScorer(mock_seed), J.ClassicalScorer, J.TapeScorer, J.GScorer,
                  lambda: J.ClefScorer("flash"), lambda: J.ClefScorer("full"), J.KevScorer, J.SokudanScorer)
        for make in makers:
            strict_out.append(J.strict_check(make, items))

    result: dict[str, Any] = {
        "schema": dm_eval.SCHEMA,
        "params": {"seed": str(seed), "mock_seed": str(mock_seed), "n_orders": int(n_orders),
                   "rotation_offsets": {str(n): list(S.rotation_offsets(n, n_orders)) for n in sizes},
                   "arms": {a: int(S.LENGTH_ARMS[a]) for a in arms},
                   "arm_drop_blocks": {a: list(S.ARM_DROP_BLOCKS[a]) for a in arms},
                   "chars_per_token": S.CHARS_PER_TOKEN, "vocab_version": S.VOCAB_VERSION,
                   "experience_k": S.EXPERIENCE_K, "present_domain": S.PRESENT_DOMAIN},
        "n_situations": len(situations),
        "languages": {"ja": len(situations), "日本語の外": None},
        "first_language": None,
        "experience": {"situations_with_experience": sum(1 for s in situations if exp.get(s.sid)),
                       "words_total": sum(len(exp.get(s.sid, ())) for s in situations)},
        "candidates": S.describe_candidates(cands),
        "lengths": lengths,
        "scorers": out_scorers,
        "controls": controls,
        "tape_fixed_order": tape_fixed,
        "pbs_null_floor": floor,
        "strict": strict_out,
        "human": dict(J.HUMAN_FIELDS),
        "speed_formula": J.GPU_HOURS_FORMULA,
        "calls_basis": dict(J.CALLS_PER_DAY_BASIS),
        "limits": list(LIMITS),
        "timing": {"wall_s": time.perf_counter() - t_all},
    }
    rows = T.build_rows(out_scorers, arms=arms, tape_fixed=tape_fixed)
    result["table"] = {"columns": list(T.COLUMN_KEYS), "rows": rows, "blank": T.blanks_of(rows),
                       "order": T.ORDER_NOTE, "footnotes": table_footnotes(floor, tape_fixed)}
    result["digest"] = digest_of(result)
    return result


def _write(path: Path, text: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"既にある(--overwrite で上書き): {path.name}")
    path.write_bytes(text.encode("utf-8"))


def write_outputs(result: Mapping[str, Any], out_dir: Path, *, overwrite: bool = False,
                  inputs: Mapping[str, Any] | None = None) -> dict[str, str]:
    """``result.json``・``table.md``・``table.json`` を書く(LF・UTF-8)。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = dict(result)
    if inputs is not None:
        doc = {"inputs": dict(inputs), **doc}
    rows = result["table"]["rows"]
    langs = {"ja": f"{result['n_situations']} 件", "日本語の外": None}
    files = {
        "result.json": json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
        "table.md": T.to_markdown(rows, languages=langs, footnotes=result["table"]["footnotes"]),
        "table.json": T.to_json(rows, languages=langs, footnotes=result["table"]["footnotes"]),
    }
    for name, text in files.items():
        _write(out_dir / name, text, overwrite)
    return {name: hashlib.md5(text.encode("utf-8")).hexdigest() for name, text in files.items()}


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="評価セットを 1 回通して記録を書く")
    r.add_argument("--out-dir", required=True)
    r.add_argument("--seed", default=S.DEFAULT_SEED)
    r.add_argument("--n-orders", type=int, default=S.DEFAULT_N_ORDERS)
    r.add_argument("--mock-seed", default="dm61-mock")
    r.add_argument("--no-tape-experience", action="store_true", help="本人の経験の代わり(テープの前の呼)を使わない")
    r.add_argument("--overwrite", action="store_true")
    a = ap.parse_args(argv)
    sits = S.load_situations()
    tapes_md5 = None
    if not a.no_tape_experience:
        tapes_md5 = S.verify_tape_md5(sits)  # 1-10 の summary の md5 と違えば読まない
        if not tapes_md5["ok"]:
            raise ValueError(f"テープの md5 が 1-10 の記録と違う: {tapes_md5['mismatch']}")
    exp = {} if a.no_tape_experience else S.tape_experience(sits)
    res = evaluate(sits, exp, seed=a.seed, n_orders=a.n_orders, mock_seed=a.mock_seed)
    inputs = {"situations": f"data/evalset/evalset-1-10/{S.SITUATIONS_NAME}", "situations_md5": S.SITUATIONS_MD5,
              "summary": f"data/evalset/evalset-1-10/{S.SUMMARY_NAME}", "summary_md5": S.SUMMARY_MD5,
              "tapes": len({s.tape for s in sits}), "tape_experience": not a.no_tape_experience,
              "tapes_md5": tapes_md5}
    md5s = write_outputs(res, Path(a.out_dir), overwrite=a.overwrite, inputs=inputs)
    print(json.dumps({"digest": res["digest"], "files": md5s, "wall_s": round(res["timing"]["wall_s"], 2)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
