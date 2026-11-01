# -*- coding: utf-8 -*-
"""dm_eval.cli — 評価の器を 1 回通して、記録の JSON と表を書く(第 6 期 6-1・読むだけ・GPU とネットワークは使わない)。

使い方(リポの根で・``PYTHONPATH`` に作業木の ``src``)::

    python tools/instruments/dm_eval/cli.py run --out-dir docs/bench/analysis/wallbounce-1012/dm61

書くもの(``--out-dir`` の下・既にあれば ``--overwrite`` が無い限り書かない):
    - ``result.json``: 入力の md5・候補の集計・長さの集計・当て口ごとの採点(一致・迷い・その他の率・位置の偏り・
      速さの欄)・正の対照・テープの固定の並び・厳密モードの検査・空欄の宣言・``digest``(壁時計を除いた決定的な部分の
      sha256=golden)。**テープの本文と状況の文は写さない**(集計だけ)。絶対パスは書かない。
    - ``table.md``・``table.json``: 表「人らしさ × 速さ × 1 シム日あたりの GPU 時間」(順位なし)。

〔11-01 段 1 の 3〕
    - ``--scenes evalset|consumption|both``(既定 evalset=今のまま)。consumption=同梱の消費の場面
      (``scenes/consumption_v1.jsonl``・4 判断点)。both は ``--out-dir`` の下の ``evalset/`` と ``consumption/`` に書く。
    - 比べの節 ``compare``(推論の形・決定論=同一入力 ``--determinism-repeats`` 回(既定 32)・自由記述の破綻率・VRAM の
      欄)と、その digest ``compare_digest``。``digest`` は ``compare`` を含まない(1-10 の記録の golden を変えない)。
    - (G) と候補の口(GPU の後): ``--vllm-model``(127.0.0.1 の艦隊の logprob=(G) の基準・``g_…`` の名)・
      ``--hf-model``(手元の重みの道筋=候補)。指定しなければ口だけ(今のまま)。``--length short|long``(既定 short)
      は両方の口が読む文の版(DM4)。
    - 結果の欄 ``scene_set``(evalset/consumption/both)と ``material``(この結果の材料)。どちらも ``digest`` の外
      (SCHEMA は据え置き)。
    - モデルの口の失敗(``judge.ScoreFailed``)は場面ごとに捕まえて ``compare.scorers[名].failures`` に記録し、その場面を
      採点から外して続ける(全体は止めない)。

関数 ``evaluate`` は data を読まない(状況と経験を渡す)=合成の状況で試験できる。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

if __package__ in (None, ""):  # pragma: no cover - スクリプトとして実行したとき
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dm_eval  # noqa: E402
from dm_eval import bias as B  # noqa: E402
from dm_eval import judge as J  # noqa: E402
from dm_eval import situations as S  # noqa: E402
from dm_eval import table as T  # noqa: E402
from shibuya.engine.decision.port import OTHER_ID, Candidate  # noqa: E402

#: 決定的でない欄(digest から外す)。
_VOLATILE_KEYS = frozenset({"wall_s_per_item", "wall_s", "timing"})
_DIGEST_DECIMALS = 10
#: digest から外す節(表=見せ方・比べの節=〔11-01〕で足した物=自分の digest を持つ)。
_DIGEST_EXCLUDED = ("digest", "table", "compare", "compare_digest", "scene_set", "material")
#: 失敗の記録に残す件の上限(数は全部数える)。
_FAILURE_ITEMS = 20
#: 比べの節の形の版。
COMPARE_SCHEMA = "shibuya.tools.dm_eval.compare/1"
#: (G) の口だけの当て口の名(``judge.GScorer``)。
G_PORT_NAME = J.GScorer.name

LIMITS = (
    "正解の表は作らない(人のデータと考慮集合の研究の値は検証側=パターン台帳 §10-1・人のデータとの照合は欄だけ)",
    "言語は日本語だけ(材料の B0 が日本語で書くと決めている)・住人の第一言語の欄は空欄(§4-8)",
    "B5・B6 が無い(1-10 §5 の 1)=近い予定・近くの人・空腹と疲れ・招待が入力に無い=体と事情の無い判断(親の注 §9 の (b))",
    "テープの当て口は B0 の固定の並びへの答え=ここで入れ替えた並びは見ていない(並べ替えに対しては構成上 0)",
    "Clef-flash・Clef・Kev-9B・即断・(G) は口だけ=人らしさ・速さ・GPU 時間の欄は GPU の後(S6)",
    "長さの腕 t300 は B0 を外すだけ(DM4 (a) の人ごとの短い特徴量の描画は engine に無い)・トークン数は後で測る",
)
#: 〔11-01〕消費の場面の限界。
CONSUMPTION_LIMITS = (
    "場面は自前(架空の店・丸い仮の値・実在の店名と施設名と人名を使わない)=人の正解は無い・現実の値段の分布ではない",
    "判断に要る事実(所持金・体・事情・直前の結果)は短い版に入る B6 に置いた(engine の B6 の行テンプレの外の頭=自前)。"
    "DM4 の短い版に状態の欄を足す(src 側)は段 3 の問い=親。直すまで消費の場面の (G) との一致を選定の根拠にしない",
    "語彙は v3(待機は欠番=使わない)。足した語 buy_skip・price_skip・revisit・no_revisit は古典の当て口では「その他」"
    "に入る=基準として弱い",
    "テープ(8B の記録)は無い=テープの列は「基準の記録なし」・8B との比べは (G) の口(GPU の後)",
    "候補の源(経験・できること・続ける)の付け方は自前(expedient)・候補は場面ごとに 6 つ+その他",
    "言語は日本語だけ・住人の第一言語の欄は空欄(§4-8)",
)
#: 〔11-01〕消費の場面の空欄の宣言(1-10 の BLANK_SOURCES の代わり)。
CONSUMPTION_BLANKS = {
    "plan": "近い予定=場面に無い(判断の契機は B6 の起床の文)",
    "experience:memory": "記憶は B6 事情の 1 行だけ(場面によって無し)",
    "tape": "8B の記録が無い(GPU の後に (G) で埋める)",
}


def _round(x: Any) -> Any:
    if isinstance(x, float):
        return round(x, _DIGEST_DECIMALS)
    if isinstance(x, Mapping):
        return {str(k): _round(v) for k, v in x.items() if str(k) not in _VOLATILE_KEYS}
    if isinstance(x, (list, tuple)):
        return [_round(v) for v in x]
    return x


def _sha(body: Any) -> str:
    canon = json.dumps(_round(body), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def digest_of(result: Mapping[str, Any]) -> str:
    """壁時計を除き、小数を 10 桁に丸めた決定的な部分の sha256(golden)。比べの節と表は含めない。"""
    return _sha({k: v for k, v in result.items() if k not in _DIGEST_EXCLUDED})


def compare_digest_of(compare: Mapping[str, Any]) -> str:
    """比べの節の digest(壁時計を除く)。"""
    return _sha(compare)


def table_footnotes(floor: Mapping[str, Any], tape_fixed: Mapping[str, Any] | None,
                    compare: Mapping[str, Any] | None = None) -> list[str]:
    """表の脚注(PBS の帰無の床=フロア併記・提示の並びを見ていない当て口の注・比べの列の読み方)。"""
    out = []
    for n, f in floor.items():
        out.append(f"PBS の帰無の床(中身だけで選ぶ当て口の模擬・候補 {n}・{f['reps']:,} 回): 平均 {f['mean']:.3f}・"
                   f"5〜95% {f['p05']:.3f}〜{f['p95']:.3f}(この幅の中の PBS は偏りの証拠にならない)")
    if tape_fixed is not None:
        out.append("テープの行: " + T.order_blind_note(tape_fixed))
    if compare is not None:
        out.append("分布の広がり=「迷い エントロピー(平均)」の列(自然対数)")
        out.append(f"決定論=同一入力 {compare.get('determinism_repeats')} 回(1 つの当て口で続けて・まとめない)で分布が"
                   "全回バイト一致の件の率。決定論が無い当て口は落とさない(回答 11-01 §11=分岐と A/A に要る seed の"
                   "本数で評価する・その式は空欄)")
        out.append(f"(G) の基準: {compare.get('g_reference')}({compare.get('g_status')})")
        out.append("日本語での破綻率: Noul=丁寧語と活用を正規化した後でどの候補にも「その他」にも当たらない率"
                   "(その他の率の列は Noul の行では明示の「その他」だけ=破綻を 2 回数えない)・Choice/Score="
                   "候補(その他を含む)の文字列の確率の和が 1e-3 未満か切り出しが字面と違った件の率")
        if compare.get("material") == "consumption":
            out.append("消費の場面: DM4 の短い版に状態の欄を足す(src 側)は段 3 の問い=親。直すまで (G) との一致を"
                       "判断モデルの選定の根拠にしない")
            out.append("数の列(何をいくつ): 数の平均=購入の候補の中での数の期待値(分布で重みづけ)の場面の平均・数の一致率="
                       "(G) の 1 位が数の候補の場面で 1 位の数が同じ率・数の差の平均=期待値の差の絶対値の平均")
    return out


def default_factories(mock_seed: str | int = "dm61-mock") -> tuple[Callable[[], J.Scorer], ...]:
    """表の並び(宣言の順=対照 → 基準 → 候補)の当て口を作る関数(``judge.scorer_registry`` と同じ並び)。"""
    return (lambda: J.MockScorer(mock_seed), J.ClassicalScorer, J.TapeScorer, J.GScorer,
            lambda: J.ClefScorer("flash"), lambda: J.ClefScorer("full"), J.KevScorer, J.SokudanScorer)


def qty_measures(dists: Mapping[str, Mapping[str, float]], fields: Mapping[str, Mapping[str, Mapping[str, Any]]],
                 ref: Mapping[str, Mapping[str, float]] | None = None) -> dict[str, Any]:
    """〔11-01 検収 低 7〕何をいくつの数の指標(数の欄 ``qty`` が 2 通り以上ある場面=何をいくつだけ)。

    - ``qty_mean``: 場面ごとの数の期待値(数の候補の中で分布で重みづけ)の平均。
    - ``agree_vs_g``: 基準(G)の 1 位が数の候補の場面で、当て口の 1 位の数が同じ率(品は問わない)。
    - ``absdiff_vs_g``: 期待値の差の絶対値の平均(両方の期待値がある場面)。
    """
    def expect(d: Mapping[str, float], q: Mapping[str, int]) -> float | None:
        w = sum(float(d.get(c, 0.0)) for c in q)
        return sum(float(d.get(c, 0.0)) * q[c] for c in q) / w if w > 0 else None

    means: list[float] = []
    agree: list[float] = []
    diffs: list[float] = []
    n = 0
    for sid in sorted(dists):
        q = {cid: int(f["qty"]) for cid, f in (fields.get(sid) or {}).items() if "qty" in f}
        if len(set(q.values())) < 2:  # 数を選ぶ場面だけ(数が 1 通りの購入の候補は数えない)
            continue
        n += 1
        e = expect(dists[sid], q)
        if e is not None:
            means.append(e)
        if ref is not None and sid in ref:
            gt = J.top1(ref[sid])
            if gt in q:
                st = J.top1(dists[sid])
                agree.append(1.0 if q.get(st) == q[gt] else 0.0)
            eg = expect(ref[sid], q)
            if e is not None and eg is not None:
                diffs.append(abs(e - eg))
    return {"n": n, "qty_mean": (sum(means) / len(means)) if means else None,
            "agree_vs_g": (sum(agree) / len(agree)) if agree else None, "n_agree": len(agree),
            "absdiff_vs_g": (sum(diffs) / len(diffs)) if diffs else None}


def _items(situations: Sequence[S.Situation], ords: Mapping[str, Sequence[tuple[Candidate, ...]]], probe: J.Scorer,
           arm: str, *, first_only: bool = False, limit: int | None = None
           ) -> list[tuple[S.Situation, tuple[Candidate, ...], str | None]]:
    """厳密モードと決定論の検査の入力(文を読む当て口だけ文を描く=読まない当て口は今のまま ``None``)。"""
    out = []
    for s in situations:
        for pres in (ords[s.sid][:1] if first_only else ords[s.sid]):
            text = (S.render(s, pres, length=probe.prompt_length, arm=arm).text
                    if probe.reads_text and probe.implemented else None)
            out.append((s, pres, text))
    return out[:limit] if limit else out


def evaluate(situations: Sequence[S.Situation], experience: Mapping[str, Sequence[str]] | None = None, *,
             seed: str | int = S.DEFAULT_SEED, n_orders: int = S.DEFAULT_N_ORDERS,
             mock_seed: str | int = "dm61-mock", arms: Sequence[str] = tuple(S.LENGTH_ARMS),
             strict: bool = True, scorer_factories: Sequence[Callable[[], J.Scorer]] | None = None,
             candidates: Mapping[str, Sequence[Candidate]] | None = None, material: str = "evalset",
             points: Mapping[str, str] | None = None, g_name: str = G_PORT_NAME,
             determinism_repeats: int = J.DETERMINISM_REPEATS, determinism_limit: int | None = None,
             compare: bool = True, vocab_version: str = S.VOCAB_VERSION,
             fields: Mapping[str, Mapping[str, Mapping[str, Any]]] | None = None,
             scene_set: str | None = None) -> dict[str, Any]:
    """状況(と本人の経験の代わり)→ 採点の結果(data は読まない)。

    〔11-01〕``candidates``(状況の id → 候補)を渡すと場面の候補を使う(消費の場面)。``scorer_factories`` は当て口を
    作る関数の並び(既定=``default_factories``)。``material`` は ``evalset`` か ``consumption``。``compare=True`` で
    比べの節(``digest`` の外)を作る。``fields``(状況の id → 候補の id → 品・数・値段)があれば数の指標を出す。
    """
    if material not in ("evalset", "consumption"):
        raise ValueError(f"material は evalset か consumption(いま {material!r})")
    t_all = time.perf_counter()
    exp = dict(experience or {})
    if candidates is None:
        cands = {s.sid: S.candidates_for(s, exp.get(s.sid, ())) for s in situations}
    else:
        cands = {s.sid: tuple(candidates[s.sid]) for s in situations}
    ords = {s.sid: S.orders(cands[s.sid], s.sid, n_orders=n_orders, seed=seed) for s in situations}
    kinds = {sid: {**{c.id: c.kind for c in cs}, OTHER_ID: OTHER_ID} for sid, cs in cands.items()}
    lengths = S.iter_lengths(situations, {sid: o[0] for sid, o in ords.items()})

    factories = tuple(scorer_factories) if scorer_factories is not None else default_factories(mock_seed)
    scorers = tuple(f() for f in factories)
    computed: dict[str, dict[str, Any]] = {}
    breakdown: dict[str, dict[str, Any]] = {}
    failures: dict[str, dict[str, Any]] = {}
    for sc in scorers:
        if not sc.implemented:
            continue
        per_arm: dict[str, Any] = {}
        cache: tuple[dict[str, list[B.Record]], float | None] | None = None
        traced = hasattr(sc, "trace_summary")
        for arm in arms:
            if cache is None or sc.reads_text:
                if traced:
                    sc.trace_reset()
                box: list[dict[str, Any]] = []
                cache = B.score_orders(sc, situations, ords, arm=arm, length=sc.prompt_length, failures=box)
                failures.setdefault(sc.name, {})[arm] = {"n": len(box), "items": box[:_FAILURE_ITEMS]}
                if traced:
                    breakdown.setdefault(sc.name, {})[arm] = sc.trace_summary()
            else:
                failures.setdefault(sc.name, {})[arm] = failures[sc.name][arms[0]]
            records, wall = cache
            per_arm[arm] = {"records": records, "wall": wall}
        computed[sc.name] = per_arm

    def first_dists(name: str, arm: str) -> dict[str, dict[str, float]]:
        return {sid: recs[0][1] for sid, recs in computed[name][arm]["records"].items()}

    def vs(ref: str, sc: J.Scorer, d0: Mapping[str, Mapping[str, float]], arm: str) -> dict[str, Any] | None:
        if sc.name == ref or ref not in computed:
            return None
        return J.agreement(d0, first_dists(ref, arm), kinds)

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
                "agreement_vs_classical": vs("classical", sc, d0, arm),
                "agreement_vs_tape": vs("tape", sc, d0, arm),
                "agreement_vs_g": vs(g_name, sc, d0, arm),
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
    tape_fixed = B.tape_fixed_order(situations) if material == "evalset" else None

    strict_out: list[dict[str, Any]] = []
    if strict:
        for make in factories:
            probe = make()
            try:
                strict_out.append(J.strict_check(make, _items(situations, ords, probe, arms[0])))
            except J.ScoreFailed as e:
                strict_out.append({"name": probe.name, "status": "失敗", **J.failure_record(e),
                                   "identical_repeat": None, "identical_reordered": None})

    blank_sources = dict(S.BLANK_SOURCES) if material == "evalset" else dict(CONSUMPTION_BLANKS)
    cand_summary = S.describe_candidates(cands)
    cand_summary["blank_sources"] = blank_sources
    result: dict[str, Any] = {
        "schema": dm_eval.SCHEMA,
        "params": {"seed": str(seed), "mock_seed": str(mock_seed), "n_orders": int(n_orders),
                   "rotation_offsets": {str(n): list(S.rotation_offsets(n, n_orders)) for n in sizes},
                   "arms": {a: int(S.LENGTH_ARMS[a]) for a in arms},
                   "arm_drop_blocks": {a: list(S.ARM_DROP_BLOCKS[a]) for a in arms},
                   "chars_per_token": S.CHARS_PER_TOKEN, "vocab_version": vocab_version,
                   "experience_k": S.EXPERIENCE_K, "present_domain": S.PRESENT_DOMAIN},
        "n_situations": len(situations),
        "languages": {"ja": len(situations), "日本語の外": None},
        "first_language": None,
        "experience": {"situations_with_experience": sum(1 for s in situations if exp.get(s.sid)),
                       "words_total": sum(len(exp.get(s.sid, ())) for s in situations)},
        "candidates": cand_summary,
        "lengths": lengths,
        "scorers": out_scorers,
        "controls": controls,
        "tape_fixed_order": tape_fixed,
        "pbs_null_floor": floor,
        "strict": strict_out,
        "human": dict(J.HUMAN_FIELDS),
        "speed_formula": J.GPU_HOURS_FORMULA,
        "calls_basis": dict(J.CALLS_PER_DAY_BASIS),
        "limits": list(LIMITS if material == "evalset" else CONSUMPTION_LIMITS),
        "timing": {"wall_s": time.perf_counter() - t_all},
    }

    cmp: dict[str, Any] | None = None
    if compare:
        g_sc = next((sc for sc in scorers if sc.name == g_name), None)
        per: dict[str, Any] = {}
        g_d0 = ({arm: first_dists(g_name, arm) for arm in arms} if g_name in computed else None)
        for make, sc in zip(factories, scorers):
            try:
                det = J.determinism_check(make, _items(situations, ords, sc, arms[0], first_only=True,
                                                       limit=determinism_limit), repeats=determinism_repeats)
            except J.ScoreFailed as e:
                det = {"name": sc.name, "status": "失敗", **J.failure_record(e),
                       "n_repeats": int(determinism_repeats), "item_agree_rate": None, "top1_agree_rate": None}
            qty = None
            if fields is not None and sc.name in computed:
                qty = {arm: qty_measures(first_dists(sc.name, arm), fields,
                                         None if (g_d0 is None or sc.name == g_name) else g_d0[arm]) for arm in arms}
            per[sc.name] = {"form": sc.form, "uses_gpu": bool(sc.uses_gpu), "prompt_length": sc.prompt_length,
                            "determinism": det, "breakdown": breakdown.get(sc.name), "failures": failures.get(sc.name),
                            "qty": qty, "vram_gb": None,
                            "vram_status": "GPU の後(欄だけ)" if sc.uses_gpu else "GPU を使わない"}
        by_point = None
        if points is not None:
            by_point = {p: 0 for p in S.DECISION_POINTS}
            for s in situations:
                by_point[points[s.sid]] = by_point.get(points[s.sid], 0) + 1
        cmp = {"schema": COMPARE_SCHEMA, "material": material, "by_point": by_point,
               "g_reference": g_name,
               "g_status": "検査済み" if (g_sc is not None and g_sc.implemented) else "GPU の後(S6)",
               "determinism_repeats": int(determinism_repeats),
               "determinism_items": len(_items(situations, ords, J.MockScorer(mock_seed), arms[0], first_only=True,
                                               limit=determinism_limit)),
               "scorers": per,
               "columns": {"spread": "迷い エントロピー(平均)=entropy_mean", "position": "position_bias(巡回・PBS)",
                           "seconds": "speed.wall_s_per_item", "vram": "GPU の後(欄だけ)",
                           "japanese_breakdown": "breakdown[腕].breakdown_rate(Noul=正規化の後で当たらない率・"
                                                 "Choice/Score=候補の確率の和が下限未満か切り出しの不一致の率)",
                           "qty": "qty[腕](何をいくつの場面だけ)", "failures": "failures[腕](場面ごとの失敗)"}}
        result["compare"] = cmp
        result["compare_digest"] = compare_digest_of(cmp)

    result["scene_set"] = str(scene_set or material)
    result["material"] = material
    rows = T.build_rows(out_scorers, arms=arms, tape_fixed=tape_fixed, compare=cmp)
    missing_refs = [r for r in ("tape", "classical") if r not in computed]
    result["table"] = {"columns": list(T.COLUMN_KEYS), "rows": rows,
                       "blank": T.blanks_of(rows, missing_refs=missing_refs), "order": T.ORDER_NOTE,
                       "footnotes": table_footnotes(floor, tape_fixed, cmp), "missing_refs": missing_refs}
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
    miss = result["table"].get("missing_refs", ())
    langs = {"ja": f"{result['n_situations']} 件", "日本語の外": None}
    files = {
        "result.json": json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
        "table.md": T.to_markdown(rows, languages=langs, footnotes=result["table"]["footnotes"], missing_refs=miss),
        "table.json": T.to_json(rows, languages=langs, footnotes=result["table"]["footnotes"], missing_refs=miss),
    }
    for name, text in files.items():
        _write(out_dir / name, text, overwrite)
    return {name: hashlib.md5(text.encode("utf-8")).hexdigest() for name, text in files.items()}


def _slug(text: str) -> str:
    return re.sub(r"[^0-9a-z]+", "_", str(text).split("/")[-1].lower()).strip("_") or "model"


def model_factories(args: argparse.Namespace, *, material: str) -> tuple[tuple[Callable[[], J.Scorer], ...], str]:
    """引数 → (当て口を作る関数の並び・(G) の名)。重みと艦隊は作るときに触らない(呼ぶときだけ)。

    消費の場面ではテープの当て口を外し(記録が無い)、古典の当て口は語彙 v3 で読む。``--vllm-model`` があれば (G) の
    口だけの当て口を艦隊の logprob の当て口(名 ``g_<model>``・基準)に替える。``--hf-model`` があれば候補として最後に
    足す。重み(口の後ろ)は 1 つを共有。``--length`` は両方の口が読む文の版。
    """
    base = list(default_factories(args.mock_seed))
    names = ["mock", "classical", "tape", G_PORT_NAME, "clef_flash", "clef", "kev_9b", "sokudan_ja_310m"]
    if material == "consumption":
        k = names.index("tape")
        del base[k], names[k]
        base[names.index("classical")] = lambda: J.ClassicalScorer(vocab_version=S.CONSUMPTION_VOCAB_VERSION)
    length = getattr(args, "length", "short")
    g_name = G_PORT_NAME
    if getattr(args, "vllm_model", None):
        from dm_eval.backends.base import LogprobChoiceScorer
        from dm_eval.backends.vllm import VLLMLogprobScorer

        vb = VLLMLogprobScorer(args.vllm_model, port=int(args.vllm_port), mode=args.vllm_mode,
                               api_key_env=args.vllm_api_key_env)
        g_name = f"g_{_slug(args.vllm_model)}"
        vform = args.vllm_form

        def make_g(vb: Any = vb, g_name: str = g_name, vform: str = vform, length: str = length) -> J.Scorer:
            return LogprobChoiceScorer(vb, vform, name=g_name, role=J.ROLE_BASELINE, length=length)

        base[names.index(G_PORT_NAME)] = make_g
    if getattr(args, "hf_model", None):
        from dm_eval.backends.base import LogprobChoiceScorer
        from dm_eval.backends.hf import HFCausalChoiceScorer

        hb = HFCausalChoiceScorer(args.hf_model, device=args.hf_device)
        hname = args.hf_name or f"hf_{_slug(args.hf_model)}"
        hform = args.hf_form

        def make_h(hb: Any = hb, hname: str = hname, hform: str = hform, length: str = length) -> J.Scorer:
            return LogprobChoiceScorer(hb, hform, name=hname, length=length)

        base.append(make_h)
    return tuple(base), g_name


def _run_material(a: argparse.Namespace, material: str, out_dir: Path, scene_set: str) -> dict[str, Any]:
    factories, g_name = model_factories(a, material=material)
    det_limit = int(a.determinism_limit) or None
    if material == "evalset":
        sits = S.load_situations()
        tapes_md5 = None
        if not a.no_tape_experience:
            tapes_md5 = S.verify_tape_md5(sits)  # 1-10 の summary の md5 と違えば読まない
            if not tapes_md5["ok"]:
                raise ValueError(f"テープの md5 が 1-10 の記録と違う: {tapes_md5['mismatch']}")
        exp = {} if a.no_tape_experience else S.tape_experience(sits)
        res = evaluate(sits, exp, seed=a.seed, n_orders=a.n_orders, mock_seed=a.mock_seed,
                       scorer_factories=factories, g_name=g_name, determinism_repeats=a.determinism_repeats,
                       determinism_limit=det_limit, scene_set=scene_set)
        inputs = {"situations": f"data/evalset/evalset-1-10/{S.SITUATIONS_NAME}", "situations_md5": S.SITUATIONS_MD5,
                  "summary": f"data/evalset/evalset-1-10/{S.SUMMARY_NAME}", "summary_md5": S.SUMMARY_MD5,
                  "tapes": len({s.tape for s in sits}), "tape_experience": not a.no_tape_experience,
                  "tapes_md5": tapes_md5}
    else:
        sc = S.load_scene_file(S.CONSUMPTION_SCENES)
        res = evaluate(sc.situations, None, seed=a.seed, n_orders=a.n_orders, mock_seed=a.mock_seed,
                       scorer_factories=factories, candidates=sc.candidates, material="consumption",
                       points=sc.points, g_name=g_name, determinism_repeats=a.determinism_repeats,
                       determinism_limit=det_limit, vocab_version=S.CONSUMPTION_VOCAB_VERSION, fields=sc.fields,
                       scene_set=scene_set)
        inputs = {"scenes": f"tools/instruments/dm_eval/scenes/{S.CONSUMPTION_SCENES.name}", "scenes_md5": dict(sc.md5),
                  "n_scenes": len(sc.situations), "by_point": sc.by_point()}
    md5s = write_outputs(res, out_dir, overwrite=a.overwrite, inputs=inputs)
    return {"digest": res["digest"], "compare_digest": res.get("compare_digest"), "files": md5s,
            "wall_s": round(res["timing"]["wall_s"], 2)}


def main(argv: Sequence[str] | None = None) -> int:
    from dm_eval.backends.base import FORMS
    from dm_eval.backends.vllm import DEFAULT_API_KEY_ENV, MODES

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="評価セットを 1 回通して記録を書く")
    r.add_argument("--out-dir", required=True)
    r.add_argument("--scenes", choices=("evalset", "consumption", "both"), default="evalset",
                   help="evalset=1-10 の 340 件(既定)・consumption=消費の場面・both=両方(out-dir の下に 2 つ)")
    r.add_argument("--seed", default=S.DEFAULT_SEED)
    r.add_argument("--n-orders", type=int, default=S.DEFAULT_N_ORDERS)
    r.add_argument("--mock-seed", default="dm61-mock")
    r.add_argument("--no-tape-experience", action="store_true", help="本人の経験の代わり(テープの前の呼)を使わない")
    r.add_argument("--determinism-repeats", type=int, default=J.DETERMINISM_REPEATS, help="同一入力の回数(既定 32)")
    r.add_argument("--determinism-limit", type=int, default=0, help="決定論の検査の件の上限(0=全部)")
    r.add_argument("--vllm-model", default=None, help="(G) の基準=127.0.0.1 の艦隊のモデルの名(GPU の後)")
    r.add_argument("--vllm-port", type=int, default=8000)
    r.add_argument("--vllm-mode", choices=MODES, default=MODES[0], help="prompt_logprobs(既定)か echo(腕)")
    r.add_argument("--vllm-form", choices=tuple(FORMS), default="choice_number")
    r.add_argument("--vllm-api-key-env", default=DEFAULT_API_KEY_ENV)
    r.add_argument("--hf-model", default=None, help="候補=手元の重みの道筋(transformers・GPU の後)")
    r.add_argument("--hf-form", choices=tuple(FORMS), default="choice_number")
    r.add_argument("--hf-device", default="cuda")
    r.add_argument("--hf-name", default=None)
    r.add_argument("--length", choices=("short", "long"), default="short",
                   help="(G) と候補の口が読む文の版(DM4・既定 short)")
    r.add_argument("--overwrite", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out_dir)
    if a.scenes == "both":
        summary = {m: _run_material(a, m, out / m, "both") for m in ("evalset", "consumption")}
        print(json.dumps(summary, ensure_ascii=False))
    else:
        print(json.dumps(_run_material(a, a.scenes, out, a.scenes), ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
