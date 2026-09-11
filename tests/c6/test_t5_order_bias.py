"""**T5 順序バイアス**(運用設計書 §1.4「24step スモークで個体 ID 順との相関 **|r| ≤ 0.05**」)。

測る 3 量(親指示)
    ① 起床回数 ② 起床 tick の平均 ③ アービタで選ばれた回数。
    ②③ は ``RecordingLLM``(``LLMRequest`` の ``agent_id``/``tick`` を控える)で直接取れる。
    ① は **``budget`` を外したラン**(``run_day(budget=1e9)``)の呼数で代用する
    ——アービタが 1 件も落とさないので「選ばれた回数=起床候補の回数」になる(expedient)。

検出力(expedient・登録簿へ)
    |r| の標準誤差は約 ``1/√n_calls``。24 step・5,000 体では呼が約 830 件 = SE≈0.035 なので、
    **|r| ≤ 0.05 を意味のある判定にするには呼が 400 件以上要る**(2,000 体では 333 件・
    SE≈0.055 で閾値と同じ桁になり、seed によって ±0.16 まで揺れることを実測した)。
    そこで CI の標準ケースは **5,000 体 × 24 tick × 3 seed**(§9.1 C6 のスモーク規模)にする。

**実データでは生の相関を判定に使わない(親確認・2026-09-09)**
    W16 の ``agent_id`` は**種別ごとの塊**で並ぶ(住民 0-43,588・通勤 43,588-259,360・
    通学 259,360-・来街 312,745-・訪日 330,607-・乗務 388,751-・指令 390,043-)。
    種別ごとに起床の出方が違う(来街者はほぼ呼ばれない・通勤者は計画境界で呼ばれる)ので、
    **ID と起床回数の生の相関は種別構成の差**を拾う(W17 週次表が載った 09-09 以降は
    生の ρ が −0.12 まで動く)。**T5(v1 の C-8)の検査対象は処理順のバイアス**なので、
    実データは ``c6lib.stratified_order_bias_report`` で**種別を層に固定**して評価する。

**判定の格付け(親指示 09-09・層2 再確認)**
    **主判定**(3 量すべてについて・``stratified_order_bias_report`` の ``ok``)
      ① **呼数**で重み付けした層内 |ρ| の平均 ≤0.05(体数で重み付けると、呼がほぼ 0 の
         来街者層が平均を薄めるため) ② **最大の層(通勤)単独** ≤0.05
      ③ **kind を統制した部分相関** |r| ≤0.05(層をまたいで同じ向きに乗るバイアスを 1 本で見る)
    **副判定**: 母集団反転の符号反転 ``|ρ_順 + ρ_逆| ≤ 0.05``(``c6lib.reversal_symmetry``)。
      処理順のバイアスは反転しても同じ向きに乗るので、符号が返れば構成の効果と言える。
    **傍証**: 反転との KS/JSD。これは「個体別呼数の**多重集合**」の比較なので、
      **全個体に同じ向きで乗る処理順バイアスには構造的に無反応**(並べ替えても多重集合は同じ)。
      主判定には使わない。
    **報告値**: 生の相関(種別構成を含む)。合成個体(母集団なし)は行が i.i.d. なので
    生の相関(``order_bias_report``)のままでよい。

**C6-b で見つかった順序バイアス → 09-09 に是正済み**
    24 step では隠れるが、**240 tick・予算無制限**の診断ランでは会話ターン起床(class 0)
    だけ ``r ≈ −0.14`` の ID 相関が出ていた。原因は ``engine.commit.pair_partners`` の
    「**セル内の最小 id を相手にする**」規則で、若い id ほど会話に誘われた。
    C6 の会話招待の設計準拠化(被招待も起床する)で ``wake_count`` の ID 相関が
    |r|≈0.10 まで上がり、本テストが検出した。**是正**: ``pair_partners(order_key=)`` を足し、
    ``intents_from_responses(run_salt=)`` から ``core.hashing.wake_tiebreak_array``
    (blake3 撹拌)を渡す形にした(``order_key=None`` は後方互換の ID 順で、単体テストだけが使う)。
    是正後 ``wake_count |r|=0.0017``。並びの規則は
    ``test_t5_conversation_partner_rule_is_stirred_not_id_ordered`` が釘付ける。
"""

from __future__ import annotations

import collections

import numpy as np
import pytest

from shibuya.engine.commit import pair_partners
from shibuya.engine.run import run_day
from shibuya.llm.mock import MockLLM
from shibuya.world.state import World

from .conftest import WORLD_DIR, real_data

TICKS = 24
N_AGENTS = 5_000
#: |r| ≤ 0.05 を判定に使うための最小呼数(SE≈1/√n < 0.05)。
MIN_CALLS_FOR_POWER = 400


def _run(n_agents, seed, *, ticks=TICKS, world=None, world_dir=None, budget=None, population=None):
    import c6lib

    rec = c6lib.RecordingLLM(MockLLM(master_seed=seed))
    res = run_day(
        n_agents=n_agents,
        seed=seed,
        world=world,
        ticks=ticks,
        checkpoint_every=ticks,
        n_cells=139,
        llm=rec,
        world_dir=world_dir,
        budget=budget,
        population=population,
        # D-56(就寝抑止)の帰無腕。tick 0 は世界内 00:00 で全員 ``SLEEPING`` なので、
        # 既定のままだと 24 tick の窓に呼が 1 本も立たず |r|≤0.05 の検出力が無くなる。
        # T5 が見るのは**選抜の順序バイアス**(``arbitrate`` の lexsort)であって就寝規則
        # ではない(抑止を入れた並び順不変は tests/engine/test_sleep_suppression_d56.py)。
        sleep_suppression=False,
        # D-62(就寝は計画の実行)の帰無腕。既定だと tick 0 の ``activity`` が W17 週次表の
        # 0:00 時点の活動から立つので、「24 tick の窓で誰が起こされるか」に**週次表という
        # 体ごとの共変量**が入る(実測: 層内 |ρ| mean_wake_tick 0.0784 > 0.05。selected_count
        # 0.0210 / wake_count 0.0219 は閾値内)。これは ``arbitrate`` の並び順のバイアスでは
        # なく**構成のバイアス**で、種別(kind)の層別では落ちない。T5 が測るのは前者なので
        # ここは D-62 前の種(全員 SLEEPING)で回す。**親へ報告済み**(W17 を共変量に入れた
        # 層別にするかは未決)。
        plan_sleep=False,
        # D-66(計画実行層)の帰無腕。既定だと tick 0 に**域外常住 88.8% が舞台の外**へ置かれ、
        # さらに域外抑止(``outside_suppression``)でその体の候補が全部落ちるので、24 tick の窓で
        # 呼ばれるのは在圏の住民・従業者にほぼ限られる=**構成のバイアス**が層内 |ρ| に入る
        # (実測: 層内 |ρ| mean_wake_tick 0.0960 / selected_count 0.0626 > 0.05・呼 826 のうち
        #  648 が RESIDENT)。T5 が測るのは ``arbitrate`` の**並び順**のバイアスなので、
        # ``sleep_suppression``/``plan_sleep`` と同じ理由でここは D-66 前の種で回す。
        # **親へ報告済み(PENDING D-64 と同じ論点)**。
        plan_executor=False,
    )
    return res, rec


# ---------------------------------------------------------------- 合成世界(CI で走る)
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_t5_order_bias_on_the_synthetic_world(c6lib, seed, capsys):
    _, sel = _run(N_AGENTS, seed)
    _, wake = _run(N_AGENTS, seed, budget=1e9)
    rep = c6lib.order_bias_report(N_AGENTS, sel.calls, wake.calls)
    with capsys.disabled():
        print(
            f"\n[T5 合成 seed={seed} 呼={rep['n_selected_calls']}] "
            + " / ".join(
                f"{k} r={v['pearson']:+.4f} ρ={v['spearman']:+.4f}"
                for k, v in rep["rows"].items()
            )
        )
    assert rep["n_selected_calls"] >= MIN_CALLS_FOR_POWER, "呼が少なすぎて |r|≤0.05 を判定できない"
    assert rep["ok"], rep


def test_t5_report_shape_is_the_three_declared_quantities(c6lib):
    rep = c6lib.order_bias_report(10, [(1, 0), (2, 3)], [(1, 0), (2, 3), (9, 5)])
    assert set(rep["rows"]) == {"selected_count", "mean_wake_tick", "wake_count"}
    assert rep["threshold"] == c6lib.T5_MAX_ABS_R == 0.05


# ---------------------------------------------------------------- 実データ 5,000 体 × 24 tick
def _real_population(n: int = N_AGENTS, seed: int = 1):
    """``engine.run._resolve_population`` と**同じ規約**で 5,000 体を取る(層=kind を得るため)。"""
    from shibuya.agents.population import load_population, sample_population

    return sample_population(load_population(WORLD_DIR, n=None, seed=seed), n, seed)


def _kind_labels() -> dict[int, str]:
    from shibuya.agents.state import AgentKind

    return {int(k): k.name for k in AgentKind}


def _print_stratified(tag: str, rep: dict, capsys) -> None:
    with capsys.disabled():
        print(
            f"\n[{tag}] ①層内 呼数加重平均|ρ| ({rep['n_reports']} seed 平均) "
            + " ".join(
                f"{m}={rep['weighted_abs_rho'][m]:.4f}(w={rep['weights'][m]:.0f})"
                for m in rep["metrics"]
            )
        )
        print(
            f"  ②最大層 {rep['largest_stratum']['name']}(n={rep['largest_stratum']['n']}) "
            + " ".join(f"{m}={rep['largest_stratum'][m]:+.4f}" for m in rep["metrics"])
            + " / ③部分相関(kind 統制) "
            + " ".join(f"{m}={rep['partial'][m]:+.4f}" for m in rep["metrics"])
        )
        print(
            "  (報告値) 生ρ "
            + " ".join(f"{m}={rep['raw'][m]['spearman']:+.4f}" for m in rep["metrics"])
        )
        print(
            "  層内ρ(selected_count): "
            + " ".join(
                f"{k}(n={v['n']},呼={v['n_calls']:.0f})={v['selected_count']:+.4f}"
                for k, v in sorted(rep["strata"].items(), key=lambda kv: -kv[1]["n"])
            )
        )


def _stratified_over_seeds(c6lib, pop, seeds=(1, 2, 3), *, with_wake: bool = False) -> dict:
    """母集団を固定して run seed だけ変え、層内報告を Fisher z 平均する(検出力)。"""
    reports = []
    for seed in seeds:
        _, sel = _run(
            N_AGENTS, seed, world=World.load(WORLD_DIR), world_dir=WORLD_DIR, population=pop
        )
        wake = None
        if with_wake:
            _, wake = _run(
                N_AGENTS, seed, world=World.load(WORLD_DIR), world_dir=WORLD_DIR,
                population=pop, budget=1e9,
            )
        reports.append(
            c6lib.stratified_order_bias_report(
                N_AGENTS,
                pop.kind,
                sel.calls,
                wake.calls if wake is not None else None,
                labels=_kind_labels(),
            )
        )
    return c6lib.average_stratified_reports(reports)


@real_data
@pytest.mark.slow
def test_t5_order_bias_on_the_real_world(c6lib, capsys):
    """実データは**種別層内**で判定する(生の相関は種別構成を拾うので報告値)。

    層内 ρ の SE は約 ``1/√(層内で呼ばれた体数)``(通勤 2,346 体でも呼は約 515=SE≈0.044)
    なので、**母集団を固定して run seed 3 本の Fisher z 平均**に閾値を当てる。
    """
    pop = _real_population()
    rep = _stratified_over_seeds(c6lib, pop, with_wake=True)
    _print_stratified("T5 実データ", rep, capsys)
    assert rep["n_selected_calls"] >= MIN_CALLS_FOR_POWER
    assert rep["ok"], rep


@real_data
@pytest.mark.slow
def test_t5_reversed_population_shows_the_bias_is_composition_not_order(c6lib, capsys):
    """``agent_id`` の写像を反転した対照。

    **主判定**: 順・逆のどちらでも層内(3 条件)が通る。
    **副判定**: 生の ρ の**符号が返る** ``|ρ_順 + ρ_逆| ≤ 0.05``。
    **傍証**: 個体別呼数の分布が同じ(KS/JSD)——多重集合の比較なので処理順バイアスには
    無反応。判定には使わない。
    """
    n = N_AGENTS
    pop = _real_population(n)
    rev = c6lib.reverse_population(pop)
    assert not np.array_equal(pop.kind, rev.kind), "反転が効いていない(種別が対称すぎる)"

    reports = {}
    for tag, population in (("順", pop), ("逆", rev)):
        rep = _stratified_over_seeds(c6lib, population)
        reports[tag] = rep
        _print_stratified(f"T5 反転 {tag}", rep, capsys)
        assert rep["ok"], (tag, rep)  # 主判定

    sym = c6lib.reversal_symmetry(reports["順"], reports["逆"])  # 副判定
    with capsys.disabled():
        print(
            "\n[T5 反転 符号] "
            + " / ".join(
                f"{m}: 順{v['forward']:+.4f} 逆{v['reverse']:+.4f} 残差{v['residual']:.4f}"
                for m, v in sym["rows"].items()
            )
        )
    assert sym["ok"], sym

    # 傍証(判定には使わない): 個体別呼数の分布
    _, fwd_rec = _run(n, 1, world=World.load(WORLD_DIR), world_dir=WORLD_DIR, population=pop)
    _, rev_rec = _run(n, 1, world=World.load(WORLD_DIR), world_dir=WORLD_DIR, population=rev)
    fwd, _ = c6lib.per_agent_call_stats(fwd_rec.calls, n)
    bwd, _ = c6lib.per_agent_call_stats(rev_rec.calls, n)
    d, p = c6lib.ks_2samp(fwd, bwd)
    hist_f = {str(int(k)): int(v) for k, v in zip(*np.unique(fwd, return_counts=True))}
    hist_b = {str(int(k)): int(v) for k, v in zip(*np.unique(bwd, return_counts=True))}
    js = c6lib.jsd_counts(hist_f, hist_b)
    with capsys.disabled():
        print(f"\n[T5 反転 傍証] KS D={d:.4f} p={p:.3f} / JSD={js:.5f} bits(多重集合の比較)")


# ---------------------------------------------------------------- 長い地平の診断(既知バイアス)
def test_t5_conversation_partner_rule_is_stirred_not_id_ordered():
    """``pair_partners`` の並びを釘付ける(09-09 の是正後)。

    - ``order_key=None``(後方互換)= **セル内の最小 id**。ID 順バイアスの源なので
      本番経路では使わない。
    - ``order_key`` を渡すと**その順**で先頭が相手になる=呼び出し側が blake3 撹拌鍵
      (``core.hashing.wake_tiebreak_array``)を渡すことで ID 相関が消える。

    規則を変えたらこのテストが落ちる=``test_t5_long_horizon_diagnostic`` の期待値を
    測り直す合図。
    """
    a = np.array([7, 3, 9, 5, 100, 101], dtype=np.int64)
    c = np.array([0, 0, 0, 0, 1, 1], dtype=np.int64)
    # 旧規則(ID 順)
    partner = dict(zip(a.tolist(), pair_partners(a, c).tolist()))
    assert partner == {7: 3, 9: 3, 5: 3, 3: 5, 100: 101, 101: 100}
    # 撹拌鍵を渡すと並びが変わる(セル内で鍵の昇順・先頭が相手・先頭本人は 2 番目)
    key = np.array([1, 5, 0, 2, 1, 0], dtype=np.uint64)
    stirred = dict(zip(a.tolist(), pair_partners(a, c, key).tolist()))
    assert stirred == {9: 7, 7: 9, 5: 9, 3: 9, 101: 100, 100: 101}


@pytest.mark.slow
def test_t5_long_horizon_diagnostic_reports_the_bias_per_wake_class(c6lib, capsys):
    """240 tick・予算無制限の診断ラン。**起床クラス別**に ID 相関を出す(合否は付けない)。

    24 step のスモークでは会話成立が数件しか出ないので、順序バイアスはここでしか見えない。
    """
    _, rec = _run(N_AGENTS, 1, ticks=240, budget=1e9)
    by_class: dict[int, list[tuple[int, int]]] = collections.defaultdict(list)
    for r in rec.records:
        by_class[int(r["wake_class"])].append((r["agent_id"], r["tick"]))
    ids = np.arange(N_AGENTS)
    lines = []
    for wc in sorted(by_class):
        cnt, _ = c6lib.per_agent_call_stats(by_class[wc], N_AGENTS)
        lines.append(
            f"class {wc}: n={len(by_class[wc]):,} r={c6lib.pearson(ids, cnt):+.4f} "
            f"ρ={c6lib.spearman(ids, cnt):+.4f}"
        )
    with capsys.disabled():
        print("\n[T5 診断 240tick 予算無制限] " + " / ".join(lines))
    # 会話クラス(0)以外は閾値内であること(=バイアスの所在を 1 か所に閉じ込める)
    for wc, calls in by_class.items():
        if wc == 0:
            continue
        cnt, _ = c6lib.per_agent_call_stats(calls, N_AGENTS)
        r = c6lib.pearson(ids, cnt)
        assert abs(r) <= c6lib.T5_MAX_ABS_R, f"class {wc} に新しい順序バイアス r={r:+.4f}"
