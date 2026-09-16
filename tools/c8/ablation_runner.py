# -*- coding: utf-8 -*-
"""ablation_runner.py — ablation **第1陣 6 本**(知覚契約書 §8)の腕定義表と実行器。

正典
- 知覚契約書 **§8**「ablation の優先順位規則(決定 09-06)…**第1陣(Phase 2・L2=総 GPU 時間
  20% の枠内)=6 本**: ①チャネル固定枠 vs 同一総トークンの単一ランキング(義務)
  ②p_notice の d50 0.5×/2×(指標=情報到達半径) ③近接入替の不応期 15 分±50%
  ④聴覚 ΔSNR −3/−5 ⑤日次内省 1.05 回/日 vs 2-3 回/日 ⑥広告ゼロ」。
- 同 **§9**「完了条件(スケール前): 指標 B の事前登録つき再測+ablation ①」。
- 予算宣言表 **L2**「ablation・感度試験の取り分=総 GPU 時間の 20% を予約」。
- 実装計画書 **§9.1 C8**「ablation 第1陣 6 本(20% 予約枠)…検収=各 expedient の
  『結果を駆動していない』証明」。
- 方法論「ablation マトリクスは完了条件(余力があれば項目ではない)」。

本ツールがすること
    ① **腕定義表**(``ablations_v1.json``)を持つ: id・設計出典・切替方法(既存フラグ /
       ``--ablate`` id / 未実装=差分案)・対照・測る指標・所要(呼数・GPU 時間)。
    ② ``--arm <id>`` で 1 腕を回す。既定 5,000 体×1,440 tick(``--ticks 24`` でスモーク)を
       ``shibuya.cli.run`` で走らせ、腕ごとの結果 JSON/Markdown を書く。
    ③ **切替口が無い腕**は回さずに差分案を印字して終わる(自前で src/ を触らない)。
    ④ mock でも回るが、**プロンプト本文しか変えない腕(①⑥⑦)は mock では差が出ない**
       (MockLLM が本文を読まない=C6 実測)。その旨を「実 LLM 必須」と印字する。
    ⑤ **M1 接地率(2 段)・M2 未定義率・M3 上位未定義語**を集計する(``_grounding`` /
       ``_undefined_registry`` の docstring に分母・分子の式。``AB7-OPEN-INTENT`` の
       仕様書 ``docs/design/v2-open-intent-arm-spec.md`` §1)。**第1陣の 6 本でも同じ列が出る**
       (列追加のみ・既存の値は動かさない)。

第1陣より後に足した腕(2026-09-16 現在 ``AB7-OPEN-INTENT`` の 1 本)は表の ``first_wave``
の外にいる。``first_wave_ids`` が第1陣の名指しで、``validate_table`` はそれを使う。

親がサーバーで叩く例::

    python tools/c8/ablation_runner.py --list
    python tools/c8/ablation_runner.py --arm AB1-BUDGET-MODE \\
        --endpoints http://127.0.0.1:8000,http://127.0.0.1:8001 \\
        --world data/world/v2 --agents 5000 --ticks 1440 --out docs/bench/c8
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c8lib  # noqa: E402
from c8lib import c6lib  # noqa: E402

#: ``runs[].kwargs`` に許すキー(**ここに無いキーは実行しない**=腕定義表からの任意コード実行を防ぐ)。
ALLOWED_KWARGS: frozenset[str] = frozenset(
    {
        "budget_mode",           # 実装済(§3.2 ablation ①)
        "p_notice_ablation",     # 実装済(§3.1 A0-A4)
        "processes_disabled",    # 実装済(過程 id / AB-* id)
        "processes_enabled",     # 実装済
        "salient_rate_per_10k",  # 実装済(顕著行為の発生率)
        "use_population",        # 実装済(下限対照)
        # ---- C8 切替口 ②③⑥(2026-09-09 実装済・サブ U・親検収) ----
        "p_notice_d50_scale",    # 実装済(② d50 倍率)
        "refractory_scale",      # 実装済(③ 不応期倍率表)
        "signage",               # 実装済(⑥ 看板行の有無)
        # ---- AB7-OPEN-INTENT(自由意図の腕・2026-09-16 実装) ----
        "intent_mode",           # 実装済(vocab | open・B0 の出力規約だけを入れ替える)
    }
)

#: 未実装の切替口(``pending`` の腕が使うキー)。②③⑥ は 2026-09-09 に実装済=いまは空。
PENDING_KWARGS: frozenset[str] = frozenset()


def arm_by_id(table: Mapping[str, Any], arm_id: str) -> dict[str, Any]:
    """腕定義表から 1 腕を引く(前方一致・大文字小文字を無視)。"""
    key = str(arm_id).strip().upper()
    arms = list(table.get("arms", ()))
    exact = [a for a in arms if str(a.get("id", "")).upper() == key]
    if exact:
        return dict(exact[0])
    pref = [a for a in arms if str(a.get("id", "")).upper().startswith(key)]
    idx = [a for a in arms if str(a.get("index", "")) == arm_id]
    hit = pref or idx
    if len(hit) == 1:
        return dict(hit[0])
    raise KeyError(f"腕 id が引けない: {arm_id!r}(候補 {[a['id'] for a in arms]})")


def first_wave_ids(table: Mapping[str, Any]) -> list[str]:
    """知覚契約書 §8 の**第1陣 6 本**の id(表の ``first_wave.ids`` が正典)。

    第1陣より後に足した腕(``AB7-OPEN-INTENT`` など・別の設計書が出典)は含まない。
    表に ``first_wave`` が無い旧版では**先頭 6 本**を第1陣とみなす(後方互換)。
    """
    fw = table.get("first_wave")
    if isinstance(fw, Mapping) and fw.get("ids"):
        return [str(x) for x in fw["ids"]]
    return [str(a.get("id", "")) for a in list(table.get("arms", ()))[:6]]


def validate_table(table: Mapping[str, Any]) -> list[str]:
    """腕定義表の自己検査(テストと ``--list`` が使う)。**問題の一覧を返す**(例外にしない)。"""
    problems: list[str] = []
    arms = list(table.get("arms", ()))
    wave1 = first_wave_ids(table)
    if len(wave1) != 6:
        problems.append(f"第1陣は 6 本のはず(いま {len(wave1)} 本)")
    if [str(a.get("id", "")) for a in arms[: len(wave1)]] != wave1:
        problems.append(f"第1陣 6 本は表の先頭に §8 の順で並ぶはず(いま {[a.get('id') for a in arms]})")
    seen: set[str] = set()
    for a in arms:
        aid = str(a.get("id", ""))
        if not aid or aid in seen:
            problems.append(f"id が空か重複: {aid!r}")
        seen.add(aid)
        for field in ("rank", "index", "name", "design_source", "switch", "control", "metrics", "cost", "status"):
            if field not in a:
                problems.append(f"{aid}: 欄 {field} が無い")
        sw = a.get("switch", {})
        if not isinstance(sw, Mapping) or "implemented" not in sw:
            problems.append(f"{aid}: switch.implemented が無い")
        elif not sw.get("implemented") and not sw.get("diff_proposal"):
            problems.append(f"{aid}: 未実装なのに diff_proposal が無い")
        for m in a.get("metrics", ()):
            if m not in table.get("metrics", {}) and m != "conversation_sessions":
                problems.append(f"{aid}: 指標 {m} が metrics 辞書に無い")
        for r in a.get("runs", ()):
            bad = set(r.get("kwargs", {})) - ALLOWED_KWARGS
            if bad:
                problems.append(f"{aid}/{r.get('tag')}: 許されない kwargs {sorted(bad)}")
            if set(r.get("kwargs", {})) & PENDING_KWARGS and not r.get("pending"):
                problems.append(f"{aid}/{r.get('tag')}: 未実装の口なのに pending でない")
    ranks = [a.get("rank") for a in arms]
    if sorted(ranks) != list(range(1, len(arms) + 1)):
        problems.append(f"rank は 1..{len(arms)} の通し番号(いま {ranks})")
    return problems


def table_markdown(table: Mapping[str, Any]) -> str:
    """腕定義表 → Markdown(``--list`` と計器盤が使う・**純関数**)。"""
    rows = []
    for a in table.get("arms", ()):
        sw = a.get("switch", {})
        cost = a.get("cost", {})
        rows.append(
            [
                a.get("rank"),
                a.get("index"),
                a.get("id"),
                a.get("name"),
                "実装済" if sw.get("implemented") else ("機能未実装" if a.get("status") == "blocked_feature" else "切替口なし"),
                sw.get("how", "")[:60],
                "mock可" if sw.get("mock_effective") else "**実 LLM 必須**",
                cost.get("runs"),
                c8lib.fmt(cost.get("gpu_hours"), 2),
                a.get("status"),
            ]
        )
    extra = [str(a.get("id")) for a in table.get("arms", ()) if str(a.get("id")) not in set(first_wave_ids(table))]
    md = [
        "# ablation 腕定義表(第1陣 6 本=知覚契約書 §8"
        + (f" ・追加腕 {len(extra)} 本={'・'.join(extra)}" if extra else "")
        + ")",
        "",
        c8lib.markdown_table(
            ["順", "番", "id", "腕", "切替", "切替方法", "mock", "ラン数", "GPU h", "状態"], rows
        ),
        "",
        f"- 予算 **L2** {table.get('budget', {}).get('declared', '')}"
        f"(本表の枠の目安 {c8lib.fmt(table.get('budget', {}).get('reserve_hours_per_sim_day'), 1)} h)",
        f"- 共有ベースライン込みの合計: {table.get('totals', {}).get('runs_with_shared_baseline')} ラン ・"
        f" 呼 {c8lib.fmt(table.get('totals', {}).get('calls_with_shared_baseline'))} ・"
        f" {c8lib.fmt(table.get('totals', {}).get('gpu_hours_with_shared_baseline'), 2)} h"
        f"(L2 枠内={c8lib.fmt(table.get('totals', {}).get('within_l2'))})",
    ]
    for q in table.get("open_questions", ()):
        md.append(f"- **親判断待ち**: {q}")
    return "\n".join(md)


def run_metrics(res: Any, tape_path: Path | None) -> dict[str, Any]:
    """1 ランの結果 → 指標辞書(**腕の比較はこの辞書の上で行う**)。"""
    rc = {k: float(v) for k, v in getattr(res, "renderer_counters", {}).items()}
    out: dict[str, Any] = {
        "llm_calls": int(getattr(res, "llm_calls", 0)),
        "calls_per_agent_day": float(getattr(res, "llm_calls", 0)) / max(1, int(getattr(res, "n_agents", 1))),
        "format_error_rate": float(getattr(res, "parse_error_rate", 0.0)),
        "format_error_rate_strict": float(getattr(res, "parse_error_rate_strict", 0.0)),
        "undefined_action_count": int(getattr(res, "undefined_action_count", 0)),
        "conversation_sessions": int(getattr(res, "conversation_sessions", 0)),
        "prompt_tokens_mean": rc.get("prompt_tokens_mean", float("nan")),
        "group_tokens": {
            "shared_static": rc.get("tokens_shared_static_mean", float("nan")),
            "cell": rc.get("tokens_cell_mean", float("nan")),
            "individual": rc.get("tokens_individual_mean", float("nan")),
        },
        "diagnostics_day": _diagnostics_day(res),
        "conserved": bool(getattr(res, "conserved", False)),
        "census_pass": bool(getattr(res, "census_pass", False)),
        "salient_events": int(getattr(res, "salient_events", 0)),
        "noticed": int(getattr(res, "noticed", 0)),
        "final_hash": str(getattr(res, "final_hash", "")),
        "budget_mode": str(getattr(res, "budget_mode", "")),
        "intent_mode": str(getattr(res, "intent_mode", "")),
        "run_manifest_fields": _manifest_fields(res),
    }
    out["notice_reach"] = out["noticed"] / max(1, out["salient_events"])
    out["undefined_registry"] = _undefined_registry(res)  # M2/M3(台帳側)
    if tape_path is not None and Path(tape_path).exists():
        from shibuya.engine.tape import Tape

        # D-58: 繰り延べ行(応答空)は行動分布・書式の分母に入れない
        texts = [str(r.response) for r in Tape(tape_path).rows() if not r.deferred]
        sc = c6lib.score_texts(texts)
        out["action_counts"] = sc["action_counts"]
        out["undefined_rate"] = sc["undefined_rate"]
        out["role_action_rate"] = sc["role_action_rate"]
        out["n_texts"] = len(texts)
        out["grounding"] = _grounding(sc)  # M1(2 段)・M2(テープ側)
    return out


#: M3 の上位語の本数(open-intent 仕様書 §1「top30」)。
M3_TOP_K: int = 30


def _grounding(sc: Mapping[str, Any]) -> dict[str, Any]:
    """**M1 接地率(2 段)と M2 未定義率** — テープから再計算できる形(open-intent 仕様書 §1)。

    分母 ``n`` は**繰り延べでないテープ行の応答本文の数**(``Tape(tape).rows()`` のうち
    ``not r.deferred``・D-58 の分母。``run_metrics`` の ``n_texts`` と同じ)。各行の
    ``calls.parquet`` の ``response`` 列を ``llm.parser.parse_two_line`` に通し、行動欄を
    **互いに排他な 3 つ**に分ける(``c6lib.score_texts`` が同じ走査で数えた値を読み直すだけ=
    採点の定義を 2 つ持たない)。

    ====================  ==========================================================
    欄                    式(分子 ÷ n)
    ====================  ==========================================================
    ``grounded_direct``   ``ParseResult.action is not None`` の行数 ÷ n
                          = 行動欄が **24 語**(``contract.ALL_ACTION_WORDS`` = 12 語
                          + 役割語 12)に**直接一致**した割合。ラベル別名・位置引数の
                          読み取りは parser の判定に従う(書式エラー率と同じ物差し)
    ``grounded_dictionary``  ``action is None`` かつ ``undefined.map_synonym(raw_action)``
                          が語を返した行数 ÷ n = **段0 辞書**(``SYNONYMS``)で写せた割合
    ``undefined_rate``    ``action is None`` かつ ``map_synonym`` も ``None`` の行数 ÷ n
                          = **M2**。``score_texts`` の ``undefined_rate`` と同値で、
                          行動分布では ``action_counts["(未定義)"]`` として数えた行
    ====================  ==========================================================

    3 つの件数の和は厳密に ``n``(同じ 1 行が 2 つに数えられることはない)。
    ``grounded_total = grounded_direct + grounded_dictionary = 1 − undefined_rate``。

    親の再計算手順: ``calls.parquet`` の ``deferred == 0`` の行の ``response`` を並べ、
    ``c6lib.score_texts(texts)`` を呼べば ``n`` ・``dictionary_mapped`` ・
    ``action_counts["(未定義)"]`` が出る=上の 3 式がそのまま再現する。
    """
    n = int(sc.get("n", 0))
    n_dict = int(sc.get("dictionary_mapped", 0))
    n_undef = int(dict(sc.get("action_counts", {})).get("(未定義)", 0))
    n_direct = n - n_dict - n_undef
    den = max(1, n)
    return {
        "n": n,
        "denominator": "非繰り延べのテープ行(D-58)",
        "n_direct": n_direct,
        "n_dictionary": n_dict,
        "n_undefined": n_undef,
        "grounded_direct": n_direct / den,
        "grounded_dictionary": n_dict / den,
        "grounded_total": (n_direct + n_dict) / den,
        "undefined_rate": n_undef / den,
    }


def _undefined_registry(res: Any, *, k: int = M3_TOP_K) -> dict[str, Any]:
    """**M2 未定義率と M3 上位未定義語** — ランの台帳側(open-intent 仕様書 §1)。

    出所は ``RunResult.undefined_registry``(``run_day`` が ``bridge.undefined`` を挿す・
    艦隊経路の ``FleetBridge`` も**同じ台帳を共有**する)。台帳が無い結果(スタブ・旧版)では
    空辞書を返す=**推測で埋めない**。

    分母 ``n_calls`` は**解釈まで進んだ呼**= ``RunResult.bridge_counters["llm_calls"]``
    (= ``LLMBridge.n_calls``)。``RunResult.llm_calls`` は**発射数**で繰り延べ・再送を含む
    ため分母には使わない(D-58)。

    - ``undefined_rate``  = ``counters()["undefined_records"]`` ÷ n_calls(= M2・台帳側)
    - ``dictionary_rate`` = ``counters()["dictionary_mapped"]`` ÷ n_calls(= M1 の 2 段目)
    - ``grounded_direct`` = (n_calls − undefined_records − dictionary_mapped) ÷ n_calls
      (台帳は ``ParseResult.action is None`` のときだけ ``observe`` を通るので、
      残りが 24 語直接一致=段4 判例が 0 件のとき。判例件数は ``counters()["adopted"]``)
    - ``top_words``: ``registry.top_words(30)`` の ``(語, 出現数)`` に
      ``registry.distinct_agents(語)`` を付け、``distinct_agents >= threshold_agents``
      (行動契約書 §7 段2 の N=10)に ``reached_threshold: true`` の印を付ける(= M3)

    **台帳側 M2 とテープ側 M2 の関係(親確認・第200)**: 同じ値には**ならない**。
    ``UndefinedActionRegistry.observe`` は**行動欄が空**(書式エラーで ``raw_action`` が
    None/空)の応答を ``counts`` に入れず stage 1 の結果だけ返す(``undefined.py``
    ``observe`` 冒頭)。一方テープ側 ``score_texts`` は同じ応答を ``(未定義)`` に数える。
    したがって **テープ側 undefined_rate = 台帳側 undefined_rate + 行動欄が空の応答の割合**
    (≒書式エラー率の一部)であり、台帳側 ``grounded_direct`` はその分だけ**過大**。
    親の照合はこの式で行い、それ以上ずれたら繰り延べ行の扱いかテープの取りこぼしを疑う。
    台帳の ``undefined_dropped`` は記録リング(``log.maxlen``)の溢れで、``counts`` には
    影響しない(M2 の分子は ``counts`` 由来)。
    """
    reg = getattr(res, "undefined_registry", None)
    if reg is None or not hasattr(reg, "counters"):
        return {}
    counters = {str(a): int(b) for a, b in reg.counters().items()}
    bc = getattr(res, "bridge_counters", {}) or {}
    n_calls = int(float(bc.get("llm_calls", 0)) or 0)
    den = max(1, n_calls)
    n_undef = counters.get("undefined_records", 0)
    n_dict = counters.get("dictionary_mapped", 0)
    threshold = int(getattr(reg, "threshold_agents", 10))
    top = [
        {
            "word": str(w),
            "count": int(c),
            "distinct_agents": int(reg.distinct_agents(w)),
            "reached_threshold": bool(int(reg.distinct_agents(w)) >= threshold),
        }
        for w, c in reg.top_words(int(k))
    ]
    return {
        "n_calls": n_calls,
        "denominator": "bridge_counters['llm_calls'](=解釈まで進んだ呼・発射数ではない)",
        "counters": counters,
        "undefined_rate": n_undef / den,
        "dictionary_rate": n_dict / den,
        "grounded_direct": (n_calls - n_undef - n_dict) / den,
        "threshold_agents": threshold,
        "top_k": int(k),
        "top_words": top,
        "n_reached_threshold": sum(1 for r in top if r["reached_threshold"]),
    }


def _diagnostics_day(res: Any) -> dict[str, float]:
    """``RunResult.diagnostics_day()``(**メソッド**)を安全に呼ぶ。"""
    fn = getattr(res, "diagnostics_day", None)
    if callable(fn):
        try:
            return {k: float(v) for k, v in fn().items()}
        except Exception:  # pragma: no cover - スタブ結果
            return {}
    return dict(fn or {})


def _manifest_fields(res: Any) -> dict[str, Any]:
    try:
        f = res.run_manifest_fields()
    except Exception:  # pragma: no cover - mock/stub の結果
        return {}
    # D-66(2026-09-11): 計画実行層の腕 3 つを足した(AB-PLAN-EXECUTOR を C8 で回すため)。
    # AB7(2026-09-16): 自由意図の腕の同定欄 ``intent_mode`` を足した。
    return {k: v for k, v in f.items() if k in ("budget_mode", "ablations", "template_sha256", "catalog_sha16", "replay_date", "p_notice_ablation", "p_notice_d50_scale", "refractory_scale", "signage", "plan_executor", "exit_mode", "attendance_rate", "intent_mode")}


def compare_runs(baseline: Mapping[str, Any], arm: Mapping[str, Any]) -> dict[str, Any]:
    """baseline と腕の指標を突き合わせる(**純関数**)。

    行動語分布があれば JSD[bits] を出す(帰無参照=T7 の seed 違い 0.0035 bits・C6 実測)。
    """
    out: dict[str, Any] = {
        "identical_final_hash": baseline.get("final_hash") == arm.get("final_hash"),
        "d_llm_calls": int(arm.get("llm_calls", 0)) - int(baseline.get("llm_calls", 0)),
        "d_format_error_rate": float(arm.get("format_error_rate", 0.0)) - float(baseline.get("format_error_rate", 0.0)),
        "d_notice_reach": float(arm.get("notice_reach", 0.0)) - float(baseline.get("notice_reach", 0.0)),
        "d_prompt_tokens_mean": float(arm.get("prompt_tokens_mean", float("nan"))) - float(baseline.get("prompt_tokens_mean", float("nan"))),
    }
    a, b = baseline.get("action_counts"), arm.get("action_counts")
    if isinstance(a, Mapping) and isinstance(b, Mapping) and a and b:
        out["action_jsd"] = c6lib.jsd_counts(dict(a), dict(b))
        out["null_reference_bits"] = 0.0035  # T7(seed 違い)受入報告 C6 §3
        out["exceeds_null"] = bool(out["action_jsd"] > out["null_reference_bits"])
    # M1/M2 の差(AB7・2026-09-16)。**テープが無い側があれば欄を作らない**=推測で埋めない。
    gb, ga = baseline.get("grounding"), arm.get("grounding")
    if isinstance(gb, Mapping) and isinstance(ga, Mapping):
        for key in ("grounded_direct", "grounded_dictionary", "grounded_total", "undefined_rate"):
            out[f"d_{key}"] = float(ga.get(key, 0.0)) - float(gb.get(key, 0.0))
    return out


def execute_arm(
    arm: Mapping[str, Any],
    *,
    agents: int,
    ticks: int,
    seed: int,
    world_dir: Path | None,
    out_dir: Path,
    fleet: Any | None,
    tape_root: Path,
    fleet_factory: Any | None = None,
    fleet_wait_s: float = 0.0,
) -> dict[str, Any]:
    """1 腕を回す(``runs`` の各構成を順に)。**切替口が無ければ回さない**。

    ``fleet_factory``(呼ぶと新しい ``FleetClient`` を返す)を渡すと**ランごとに作って閉じる**。
    ``run_day`` はランの終わりに艦隊クライアントを閉じる(``FleetBridge.close``)ので、1 つの
    クライアントを baseline と腕の 2 ランで共有すると 2 ラン目が「close() 済み」で落ちる
    (C8 初回実行 09-10 の失敗)。``fleet_wait_s`` は本番既定 120(D-26)= tick ごとに応答を
    待たせないと 1,440 tick を数分で駆け抜けて応答がほぼ全部繰り延べになる。
    """
    sw = dict(arm.get("switch", {}))
    if fleet is None and fleet_factory is not None:
        fleet = fleet_factory  # 経路判定のためだけ(実体はランごとに作る)
    payload: dict[str, Any] = {
        "arm": arm.get("id"),
        "index": arm.get("index"),
        "name": arm.get("name"),
        "design_source": arm.get("design_source"),
        "switch": sw,
        "status": arm.get("status"),
        "scale": {"agents": agents, "ticks": ticks, "seed": seed},
        "route": "fleet" if fleet is not None else "mock",
        "runs": [],
        "notes": [],
    }
    if not sw.get("implemented"):
        payload["notes"].append(
            "切替口が未実装のため**回していない**。差分案: " + str(sw.get("diff_proposal", ""))
        )
        payload["executed"] = False
        return payload
    if fleet is None and not sw.get("mock_effective"):
        payload["notes"].append(
            "**実 LLM 必須**: " + str(sw.get("mock_note", "mock では腕の差が出ない"))
        )
    tape_root.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for run in arm.get("runs", ()):
        if run.get("pending"):
            payload["notes"].append(f"{run.get('tag')}: 未実装の口(pending)=飛ばした")
            continue
        kwargs = dict(run.get("kwargs", {}))
        bad = set(kwargs) - ALLOWED_KWARGS
        if bad:
            raise ValueError(f"許されない kwargs: {sorted(bad)}")
        tag = str(run.get("tag"))
        tape = tape_root / f"{arm.get('id')}__{tag}"
        client = fleet_factory() if fleet_factory is not None else fleet
        extra = dict(kwargs)
        if client is not None and fleet_wait_s > 0.0:
            extra["fleet_wait_s"] = float(fleet_wait_s)
        try:
            res, route = c6lib.run_smoke(
                n_agents=agents,
                seed=seed,
                ticks=ticks,
                world_dir=world_dir,
                tape_path=tape,
                fleet=client,
                extra=extra,
            )
        finally:
            if fleet_factory is not None and client is not None and hasattr(client, "close"):
                client.close()  # 2 回目は no-op(FleetClient.close は冪等)
        m = run_metrics(res, tape)
        m.update({"tag": tag, "kwargs": kwargs, "is_baseline": bool(run.get("is_baseline")), "route": route})
        results.append(m)
    payload["runs"] = results
    payload["executed"] = bool(results)
    base = next((r for r in results if r.get("is_baseline")), results[0] if results else None)
    if base is not None:
        payload["comparisons"] = [
            {"tag": r["tag"], **compare_runs(base, r)} for r in results if r is not base
        ]
    return payload


def arm_markdown(payload: Mapping[str, Any]) -> str:
    """1 腕の結果 → Markdown(**純関数**)。"""
    md = [
        f"# ablation {payload.get('index','')} {payload.get('arm')} — {payload.get('name')}",
        "",
        f"- 設計出典: {payload.get('design_source')}",
        f"- 規模: {payload.get('scale')} ・経路: {payload.get('route')}",
        f"- 切替: {'実装済' if payload.get('switch', {}).get('implemented') else '**未実装**'}"
        f" / {payload.get('switch', {}).get('how','')}",
    ]
    for n in payload.get("notes", ()):
        md += ["", f"> {n}"]
    runs = list(payload.get("runs", ()))
    if runs:
        md += [
            "",
            "## 腕ごとの実測",
            "",
            c8lib.markdown_table(
                ["構成", "呼数", "呼/体/日", "書式エラー率", "入力tok平均", "気づき/事象", "保存則", "final_hash"],
                [
                    [
                        r["tag"], c8lib.fmt(r["llm_calls"]), c8lib.fmt(r["calls_per_agent_day"], 2),
                        c8lib.fmt(r["format_error_rate"], 4), c8lib.fmt(r["prompt_tokens_mean"], 1),
                        c8lib.fmt(r["notice_reach"], 3), c8lib.fmt(r["conserved"]), r["final_hash"][:16],
                    ]
                    for r in runs
                ],
            ),
        ]
    grounded = [r for r in runs if isinstance(r.get("grounding"), Mapping)]
    if grounded:
        md += [
            "",
            "## M1 接地率(2 段)・M2 未定義率",
            "",
            "> 分母=非繰り延べのテープ行(D-58)。直接一致=24 語(12 語+役割語 12)"
            "・段0=``undefined.map_synonym`` で写せた分。3 つの和は 1.0。",
            "",
            c8lib.markdown_table(
                ["構成", "n", "M1 直接一致", "M1 段0 辞書", "M1 接地計", "M2 未定義率"],
                [
                    [
                        r["tag"], c8lib.fmt(r["grounding"]["n"]),
                        c8lib.fmt(r["grounding"]["grounded_direct"], 4),
                        c8lib.fmt(r["grounding"]["grounded_dictionary"], 4),
                        c8lib.fmt(r["grounding"]["grounded_total"], 4),
                        c8lib.fmt(r["grounding"]["undefined_rate"], 4),
                    ]
                    for r in grounded
                ],
            ),
        ]
    for r in runs:
        reg = r.get("undefined_registry")
        if not isinstance(reg, Mapping) or not reg.get("top_words"):
            continue
        md += [
            "",
            f"## M3 上位未定義語({r['tag']}・top {reg.get('top_k')}・"
            f"★=異なる個体 {reg.get('threshold_agents')} 体に到達=§7 段2 の閾値)",
            "",
            c8lib.markdown_table(
                ["語", "出現数", "distinct agents", "閾値到達"],
                [
                    [w["word"], c8lib.fmt(w["count"]), c8lib.fmt(w["distinct_agents"]),
                     "★" if w["reached_threshold"] else ""]
                    for w in reg["top_words"]
                ],
            ),
        ]
    cmps = list(payload.get("comparisons", ()))
    if cmps:
        md += [
            "",
            "## baseline との差",
            "",
            c8lib.markdown_table(
                ["構成", "行動分布 JSD[bits]", "帰無参照", "帰無超え", "Δ呼数", "Δ書式エラー率", "final_hash 一致"],
                [
                    [
                        c["tag"], c8lib.fmt(c.get("action_jsd"), 4), c8lib.fmt(c.get("null_reference_bits"), 4),
                        c8lib.fmt(c.get("exceeds_null")), c8lib.fmt(c.get("d_llm_calls")),
                        c8lib.fmt(c.get("d_format_error_rate"), 4), c8lib.fmt(c.get("identical_final_hash")),
                    ]
                    for c in cmps
                ],
            ),
        ]
    return "\n".join(md)


def main(argv: Sequence[str] | None = None) -> int:
    ap = c6lib.common_parser("ablation 第1陣 6 本(知覚契約書 §8)の腕定義表と実行器")
    ap.set_defaults(out="docs/bench/c8", ticks=1440)
    ap.add_argument("--arm", default="", help="回す腕の id(例 AB1-BUDGET-MODE / AB1 / ①)")
    ap.add_argument("--list", action="store_true", help="腕定義表を印字して終わる")
    ap.add_argument("--table", default="", help="腕定義表 JSON(既定 tools/c8/ablations_v1.json)")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--max-tokens", type=int, default=96)
    ap.add_argument("--tape-dir", default="", help="テープの置き場(既定=--out/c8_tapes)")
    ap.add_argument("--fleet-wait-s", type=float, default=120.0,
                    help="tick ごとに艦隊の応答を待つ上限秒(本番既定 120=D-26。0 なら非ブロッキング)")
    args = ap.parse_args(list(argv) if argv is not None else None)

    table = c8lib.load_ablations(args.table or None)
    problems = validate_table(table)
    if args.list or not args.arm:
        print(table_markdown(table))
        if problems:
            print("\n**自己検査で見つかった問題**")
            for p in problems:
                print(f"- {p}")
        paths = c8lib.write_outputs(args.out, "ablations_v1_table", table, table_markdown(table))
        print(json.dumps({"out": paths, "problems": problems}, ensure_ascii=False))
        return 0 if not problems else 1

    arm = arm_by_id(table, args.arm)
    endpoints = c6lib.endpoints_of(args)

    def _factory() -> Any:  # ランごとに新しいクライアント(run_day が終わりに閉じるため)
        return c6lib.build_fleet_client(
            endpoints, model=args.model, mode="ablation", run_id=args.run_id,
            run_seed=args.seed, temperature=args.temperature, max_tokens=args.max_tokens,
        )

    payload = execute_arm(
        arm,
        agents=args.agents,
        ticks=args.ticks,
        seed=args.seed,
        world_dir=c6lib.world_dir_of(args),
        out_dir=Path(args.out),
        fleet=None,
        tape_root=Path(args.tape_dir) if args.tape_dir else Path(args.out) / "c8_tapes",
        fleet_factory=_factory if endpoints else None,
        fleet_wait_s=float(args.fleet_wait_s),
    )
    md = arm_markdown(payload)
    paths = c8lib.write_outputs(args.out, f"ablation_{arm['id']}", payload, md)
    print(md)
    print(json.dumps({"out": paths, "executed": payload.get("executed")}, ensure_ascii=False))
    return 0 if payload.get("executed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
