# -*- coding: utf-8 -*-
"""adjudicate — 未定義行動台帳 → 契約行の草案(段2)+静的検査(段3)。**ラン後オフライン**。

位置づけ(正典)
    語彙成長の設計 v0 ``docs/design/v2-vocab-growth-design.md`` §2「ラン後 tools/vocab/adjudicate.py
    (中間の輪・オフライン・バッチ)」と、ユーザー決定 2026-09-17(A〜K)。
    行動契約書 §7 段2〜段3 を**ランの中から出す**改訂で、``run.py`` に注入口は作らない
    (設計 D (a)・§2 の「run.py への注入口(adjudicator=)は作らない」)。

決定(2026-09-17)の実装対応
    A (b)+(c) 台帳は**全件保持**・起草の順位は**被覆**(体数×セル数×時間帯数)・1 バッチの
        **件数予算 10**・N=10 体は「被覆の下限」に降格(未満は ``HELD_BELOW_THRESHOLD``)。
    B (b)   **検証可能な必須欄**(``REQUIRED_FIELDS``)。対象クラス+affordance を必須にして
        決定台帳 09-17 の「オブジェクト由来」原則を草案の形で強制する。
    C       自動検査 4 つのうち、本スクリプトは**静的検査 (s1)〜(s6) だけ**を実装する。
        動的検査 ①(mock 5,000 体で発火・保存則が閉じる)③(世界状態が実際に変わる)
        ④(受入行・checkpoint 系列が悪化しない)は **affordance をエンジンに実装したあと**で
        なければ測れないので、ここでは ``needs_dynamic`` の印を付けるだけ。
    E       草案は (対象クラス, affordance) の直積で書かせる(動詞の追加ではない)。
    G       指紋 6 つを出力 JSON の ``fingerprints`` に必ず書く。
    I       ``stage0_target`` / ``policy_class`` / ``nearest_existing``(difflib 距離)の列。
    K       裁定モデル名・温度・エンドポイント数を出力に記録(mock なら ``client="mock"``)。

自前の細部(**expedient**・設計書に数値が無い分。指紋として出力に書く)
- 被覆の式に ``max(1, …)`` を入れる(セル/時間帯が復元できない入力で 0 倍にしないため)。
- 重複判定の距離 ``DUPLICATE_RATIO = 0.75``(difflib の ``SequenceMatcher.ratio``)。
- 起草プロンプト ``DRAFT_PROMPT_VERSION``(``ADJUDICATION_TEMPLATE`` の**前半を再利用**し、
  出力形だけ JSON に替えた固定文)。sha256 を出力に記録する。
- ``cost`` を ``{"time_min": int, "money_yen": int}`` の形に固定した(「時間/金」の検査可能形)。

使い方::

    python tools/vocab/adjudicate.py data/vocab/ab7_open_s1.json data/vocab/ab7_open_s2.json \\
        --out docs/bench/vocab/ab7_open_s1s2_mock            # mock 起草(既定)
    python tools/vocab/adjudicate.py … --llm fleet --endpoints http://127.0.0.1:8000 --model <name>

逐次ループ宣言(P4): 語数(≤30)ぶんのループ 1 本 × 1 呼/語。ラン後のバッチで、ランの毎 tick
経路には入らない(設計 §2「起草の呼数は語数×1 呼=数十呼=PC で回る」)。
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:  # pragma: no cover - 実行時の経路
    sys.path.insert(0, str(REPO_ROOT / "src"))

from shibuya.agents.state import ResultCode  # noqa: E402
from shibuya.economy.accounts import AccountCode, BalanceLine, Sector  # noqa: E402
from shibuya.llm.contract import ALL_ACTION_WORDS  # noqa: E402
from shibuya.llm.undefined import (  # noqa: E402
    ADJUDICATION_TEMPLATE,
    DEFAULT_THRESHOLD_AGENTS,
    REVIEW_KEYWORDS,
    SYNONYM_TABLE_VERSION,
    SYNONYMS,
    map_synonym,
)

__all__ = [
    "POLICY_PATH",
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "DRAFT_PROMPT_VERSION",
    "DRAFT_PROMPT_TEMPLATE",
    "DEFAULT_BUDGET",
    "DUPLICATE_RATIO",
    "ADOPTION_ORDER",
    "ACCOUNT_NAMES",
    "RESULT_CODE_NAMES",
    "Verdict",
    "MockAdjudicator",
    "FleetAdjudicator",
    "load_policy",
    "load_registry",
    "merge_registries",
    "coverage",
    "nearest_existing",
    "build_prompt",
    "static_checks",
    "run_batch",
    "render_report",
    "main",
]

# ---------------------------------------------------------------- 定数(指紋)

#: 語彙政策 v0(本文 = docs/design/v2-synonym-policy-v0.md §2)の機械可読な写し。
POLICY_PATH = Path(__file__).resolve().parent / "synonym_policy_v0.json"

#: 草案の**必須欄と並び**(決定 B (b)・指紋その2)。欠けたら不採用。
REQUIRED_FIELDS: tuple[str, ...] = (
    "word",
    "target_class",
    "affordance",
    "preconditions",
    "effects",
    "cost",
    "failure_codes",
    "conservation_accounts",
    "pattern_ledger_row",
    "rationale",
)

#: 欄の型(s1 の型検査)。``list`` は文字列の並び、``dict`` は ``cost`` の 2 欄。
FIELD_TYPES: Mapping[str, str] = {
    "word": "str",
    "target_class": "str",
    "affordance": "snake_case",
    "preconditions": "list[str]",
    "effects": "list[str]",
    "cost": "cost",
    "failure_codes": "list[str]",
    "conservation_accounts": "list[str]",
    "pattern_ledger_row": "str",
    "rationale": "str",
}

#: 1 バッチの件数予算(決定 A・指紋その1)。
DEFAULT_BUDGET: int = 10

#: 重複判定の距離(difflib ``SequenceMatcher.ratio``・**expedient**・指紋その4)。
#: これ以上近い既存表層があれば「新語ではなく**辞書行の追加**で済む」と判定する。
DUPLICATE_RATIO: float = 0.75

#: 採用順序(語彙政策 v0 §4-2・指紋その5)。
ADOPTION_ORDER: tuple[str, ...] = ("食事", "観察/注意", "知らせる/対応する")

#: 保存則の科目表(``economy/accounts.py`` の ``AccountCode``)。s3 はここに実在するかを見る。
ACCOUNT_NAMES: tuple[str, ...] = tuple(a.name for a in AccountCode)

#: 既存の失敗コード(``agents/state.py`` の ``ResultCode``)。s2 の「再利用」の判定表。
RESULT_CODE_NAMES: tuple[str, ...] = tuple(c.name for c in ResultCode)

#: 失敗コードが**紛れ込んではいけない**別の名前空間(s2 の衝突検査)。
_OTHER_NAMESPACES: Mapping[str, tuple[str, ...]] = {
    "AccountCode": ACCOUNT_NAMES,
    "Sector": tuple(s.name for s in Sector),
    "BalanceLine": tuple(b.name for b in BalanceLine),
}

_FAILURE_CODE_OK = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
_AFFORDANCE_OK = "abcdefghijklmnopqrstuvwxyz0123456789_"


class Verdict:
    """段3(静的)の判定語。**今日はどれも自動採用ではない**(動的検査が未実施)。"""

    HELD_BELOW_THRESHOLD = "HELD_BELOW_THRESHOLD"  # 被覆の下限 N 未満(保持のみ)
    HELD_BUDGET = "HELD_BUDGET"  # 件数予算の外(保持のみ)
    REJECTED = "REJECTED"  # 静的検査で不採用
    DICTIONARY_ROW_SUFFICES = "DICTIONARY_ROW_SUFFICES"  # 新語不要=辞書行の追加で済む
    NEEDS_DYNAMIC = "NEEDS_DYNAMIC"  # 静的は通った → 動的検査 ①③④ 待ち


# ---------------------------------------------------------------- 起草プロンプト

_TEMPLATE_MARK = "出力は次の5行に限ります"
if _TEMPLATE_MARK not in ADJUDICATION_TEMPLATE:  # pragma: no cover - 文面凍結が破られたとき
    raise RuntimeError(
        "ADJUDICATION_TEMPLATE の文面が変わった(『出力は次の5行に限ります』が無い)。"
        "DRAFT_PROMPT_VERSION を上げて本スクリプトの前半再利用を見直すこと"
    )

#: 起草プロンプトの版(**文面を変えたら上げる**。sha256 も出力に記録する)。
DRAFT_PROMPT_VERSION: str = "vocab-draft-v0"

#: 段2 起草の固定文。``ADJUDICATION_TEMPLATE`` の**前半(役割・語・観測数・既存語彙)を再利用**し、
#: 出力形だけ「5 行」から「検証可能な必須欄を持つ JSON 1 個」に替えた(決定 B (b))。
DRAFT_PROMPT_TEMPLATE: str = (
    ADJUDICATION_TEMPLATE.split(_TEMPLATE_MARK)[0]
    + "被覆: 異なるセル {cells}・異なる時間帯 {hours}\n"
    + "出力は **JSON オブジェクト 1 個**に限ります(前後に説明を書かない)。\n"
    + "行動語そのものを足すのではなく、**対象クラス(オブジェクト種別)がどんな操作"
    + "(affordance)を提供するか**の形で書いてください。\n"
    + "欄は次の 10 個すべてを必ず入れます。\n"
    + '{{"word": "<行動語>",\n'
    + ' "target_class": "<対象クラス=オブジェクト種別。例: 飲食店・改札・棚>",\n'
    + ' "affordance": "<英語 snake_case・対象クラスが提供する操作>",\n'
    + ' "preconditions": ["<エンジンが検査できる条件・既存の状態変数名で>"],\n'
    + ' "effects": ["<状態差分・変数名と向き。例 satiety+ / money->"],\n'
    + ' "cost": {{"time_min": <所要分・整数>, "money_yen": <円・整数>}},\n'
    + ' "failure_codes": ["<大文字 SNAKE_CASE>"],\n'
    + ' "conservation_accounts": ["<科目名>"],\n'
    + ' "pattern_ledger_row": "<どの現実パターン照合に使うか1行>",\n'
    + ' "rationale": "<なぜこの形かを1〜2文>"}}\n'
    + "既存の失敗コード(再利用してよい): {result_codes}\n"
    + "既存の科目(この名前以外は書かない): {accounts}\n"
)

#: 起草プロンプトの sha256(文面凍結の証拠・出力 JSON へ)。
DRAFT_PROMPT_SHA256: str = hashlib.sha256(DRAFT_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()


def build_prompt(row: Mapping[str, Any]) -> str:
    """1 語ぶんの起草プロンプト(温度 0・1 語 1 呼)。"""
    return DRAFT_PROMPT_TEMPLATE.format(
        word=row["word"],
        count=int(row["n_rows"]),
        agents=int(row["distinct_agents"]),
        cells=int(row["distinct_cells"]),
        hours=int(row["distinct_hours"]),
        vocab="/".join(ALL_ACTION_WORDS),
        result_codes="/".join(RESULT_CODE_NAMES),
        accounts="/".join(ACCOUNT_NAMES),
    )


# ---------------------------------------------------------------- 裁定クライアント


class MockAdjudicator:
    """**決定論の定型草案**を返す mock(テストと配線確認用・LLM を呼ばない)。

    中身は意図的に**空の型どおり**(対象クラス・失敗コード・科目は埋めない)。実 LLM 起草の
    代わりに意味を作ってしまうと「設計者の指紋」になるため、置くのは形だけにする。
    ``affordance`` は語から決定論に作った印(``act_<sha256 の 8 桁>``)。
    """

    name = "mock"
    model = "mock"
    temperature = 0.0
    n_endpoints = 0

    def draft(self, prompt: str, *, word: str) -> str:
        del prompt
        tag = hashlib.sha256(word.encode("utf-8")).hexdigest()[:8]
        return json.dumps(
            {
                "word": word,
                "target_class": "TBD",
                "affordance": f"act_{tag}",
                "preconditions": [],
                "effects": [],
                "cost": {"time_min": 0, "money_yen": 0},
                "failure_codes": [],
                "conservation_accounts": [],
                "pattern_ledger_row": "[mock] 起草未実施——実 LLM 起草で埋める",
                "rationale": "mock の定型草案(決定論)。意味は入れない。",
                "placeholder": True,
            },
            ensure_ascii=False,
        )


class FleetAdjudicator:
    """実 vLLM 艦隊に 1 語 1 呼・**温度 0**(決定 K)。"""

    name = "fleet"

    def __init__(self, endpoints: Sequence[str], model: str = "", *, max_tokens: int = 768) -> None:
        from shibuya.llm.fleet import FleetClient, FleetConfig

        eps = tuple(e.strip() for e in endpoints if e.strip())
        if not eps:
            raise SystemExit("--llm fleet には --endpoints が要る")
        self.temperature = 0.0
        self.n_endpoints = len(eps)
        self._client = FleetClient(
            FleetConfig(endpoints=eps, model=model, temperature=0.0, t1_max_tokens=int(max_tokens))
        )
        self.model = model or getattr(self._client, "model", "") or ""

    def draft(self, prompt: str, *, word: str) -> str:
        from shibuya.llm import LLMRequest

        req = LLMRequest(
            agent_id=0,
            tick=0,
            wake_class=0,
            prompt=prompt,
            params={"temperature": 0.0},
            call_id=f"adjudicate:{word}",
        )
        return str(self._client.complete(req).text)


# ---------------------------------------------------------------- 入力


def load_policy(path: Path | str = POLICY_PATH) -> dict[str, Any]:
    """語彙政策 v0(写し)を読む。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_registry(path: Path | str) -> dict[str, Any]:
    """``shibuya.cli.undefined_registry_payload`` が書いた JSON を読む(形を検査)。"""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    schema = str(doc.get("schema", ""))
    if not schema.startswith("shibuya.vocab/undefined-registry/"):
        raise ValueError(f"未定義台帳の JSON ではない(schema={schema!r}): {Path(path).name}")
    return doc


def merge_registries(payloads: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """複数ラン(seed 1/2 など)の台帳を合算して語ごとの行を作る(**全件保持**)。

    合算の定義(指紋):
    - ``n_rows`` は**和**(同じ語を 2 ラン合わせた行数)。
    - ``distinct_agents`` は ``(由来, agent_id)`` の**併合**(体は run ごとの実体なので、
      2 ラン両方に出た同じ id は 2 体と数える)。
    - ``distinct_cells`` / ``distinct_hours`` は**セル id / 時間帯の併合**(世界と時刻は
      ラン間で同じ実体)。
    - ``per_source`` に由来ごとの内訳を残す(親が seed ごとの値と照合できるように)。
    """
    rows: dict[str, dict[str, Any]] = {}
    for i, payload in enumerate(payloads):
        # 由来の印。無ければ ``source#i``(同じ印の 2 入力で体を取り違えないため必ず一意)
        tag = str((payload.get("tape") or {}).get("tag") or "") or (
            f"{payload.get('source', 'src')}#{i}"
        )
        by_word: dict[str, dict[str, Any]] = {}
        for rec in payload.get("records", []):
            w = by_word.setdefault(rec["word"], {"agents": set(), "cells": set(), "hours": set()})
            w["agents"].add((tag, int(rec["agent_id"])))
            if rec.get("cell") is not None:
                w["cells"].add(str(rec["cell"]))
            w["hours"].add(int(rec["tick"]) // 60)
        for word, agg in payload.get("words", {}).items():
            got = by_word.get(word, {"agents": set(), "cells": set(), "hours": set()})
            row = rows.setdefault(
                word,
                {
                    "word": word,
                    "n_rows": 0,
                    "_agents": set(),
                    "_cells": set(),
                    "_hours": set(),
                    "first_tick": int(agg.get("first_tick", 0)),
                    "samples": [],
                    "per_source": {},
                },
            )
            row["n_rows"] += int(agg.get("n_rows", 0))
            row["_agents"] |= got["agents"]
            row["_cells"] |= got["cells"]
            row["_hours"] |= got["hours"]
            row["first_tick"] = min(int(row["first_tick"]), int(agg.get("first_tick", 0)))
            for s in agg.get("samples", []):
                if len(row["samples"]) < 3:
                    row["samples"].append({**s, "source": tag})
            row["per_source"][tag] = {
                "n_rows": int(agg.get("n_rows", 0)),
                "distinct_agents": int(agg.get("distinct_agents", 0)),
                "distinct_cells": int(agg.get("distinct_cells", 0)),
                "distinct_hours": int(agg.get("distinct_hours", 0)),
            }
    out: list[dict[str, Any]] = []
    for row in rows.values():
        row["distinct_agents"] = len(row.pop("_agents"))
        row["distinct_cells"] = len(row.pop("_cells"))
        row["distinct_hours"] = len(row.pop("_hours"))
        out.append(row)
    return out


def coverage(row: Mapping[str, Any]) -> int:
    """被覆(決定 A (c)): ``体数 × max(1, セル数) × max(1, 時間帯数)``。

    ``max(1, …)`` は、セル/時間帯を復元できない入力(台帳だけの JSON)で積を 0 に
    しないための **expedient**(指紋その1 に書く)。
    """
    return (
        int(row["distinct_agents"])
        * max(1, int(row["distinct_cells"]))
        * max(1, int(row["distinct_hours"]))
    )


# ---------------------------------------------------------------- 列(決定 I)


def _candidates() -> dict[str, dict[str, str]]:
    """重複判定の相手=**既存 24 語 + 段0 辞書表層 100 行**。"""
    out: dict[str, dict[str, str]] = {}
    for w in ALL_ACTION_WORDS:
        out[w] = {"kind": "vocab", "canonical": w}
    for surface, canonical in SYNONYMS.items():
        out.setdefault(surface, {"kind": "dictionary", "canonical": canonical})
    return out


def nearest_existing(word: str, policy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """既存語との距離(決定 I (b)・``difflib.SequenceMatcher.ratio``)。

    Returns:
        ``{"surface", "kind", "canonical", "ratio", "policy_class"}``。候補が無ければ ratio 0。
    """
    rows = dict((policy or {}).get("rows", {}))
    best: tuple[float, str, dict[str, str]] | None = None
    for surface, meta in _candidates().items():
        ratio = difflib.SequenceMatcher(None, word, surface).ratio()
        # 同率は表層の辞書順で決める(候補表の並びに依らない=決定論)
        if best is None or ratio > best[0] or (ratio == best[0] and surface < best[1]):
            best = (ratio, surface, meta)
    if best is None or best[0] <= 0.0:
        # 一致する文字が 1 つも無い(避雨・避難 など)。**辞書順の先頭を「最近傍」と書かない**。
        return {"surface": "", "kind": "", "canonical": "", "ratio": 0.0, "policy_class": "—"}
    ratio, surface, meta = best
    return {
        "surface": surface,
        "kind": meta["kind"],
        "canonical": meta["canonical"],
        "ratio": round(float(ratio), 4),
        "policy_class": str(rows.get(surface, {}).get("class", "—")),
    }


def _policy_class(word: str, policy: Mapping[str, Any]) -> str:
    """語彙政策 v0 の分類(辞書に行が無い語=台帳の語は ``未定義``)。"""
    row = dict(policy.get("rows", {})).get(word)
    return str(row["class"]) if row else "未定義"


# ---------------------------------------------------------------- 段3(静的検査)


def _is_list_of_str(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _type_ok(field: str, value: Any) -> bool:
    kind = FIELD_TYPES[field]
    if kind == "str":
        return isinstance(value, str) and bool(value.strip())
    if kind == "snake_case":
        return (
            isinstance(value, str)
            and bool(value)
            and value[0].isalpha()
            and all(c in _AFFORDANCE_OK for c in value)
        )
    if kind == "list[str]":
        return _is_list_of_str(value)
    if kind == "cost":
        return (
            isinstance(value, dict)
            and {"time_min", "money_yen"} <= set(value)
            and all(isinstance(value[k], (int, float)) for k in ("time_min", "money_yen"))
        )
    return False  # pragma: no cover - FIELD_TYPES に無い種別


def static_checks(
    row: Mapping[str, Any],
    draft: Mapping[str, Any] | None,
    raw_text: str,
    *,
    total_rows: int,
    duplicate_ratio: float = DUPLICATE_RATIO,
) -> tuple[dict[str, Any], str, list[str]]:
    """段3 の**静的**検査 (s1)〜(s6) → ``(checks, verdict, reasons)``。

    動的検査 ①(発火と保存則)③(世界状態の差分)④(非退化)は、affordance をエンジンに
    実装したあとの mock ランでしか測れない。ここでは判定せず ``needs_dynamic`` を立てる。
    """
    checks: dict[str, Any] = {}
    reasons: list[str] = []

    # (s5) 既存語との重複。草案が無くても出せる列なので先に計算する。
    near = row.get("nearest_existing") or {}
    duplicate = float(near.get("ratio", 0.0)) >= float(duplicate_ratio)
    checks["s5_duplicate"] = {
        "nearest": near,
        "threshold": float(duplicate_ratio),
        "duplicate": bool(duplicate),
        "verdict": "辞書行の追加で済む" if duplicate else "新語の候補",
    }

    # (s6) 「使用」の静的見積り(②の静的版=動的に減るはずの行数と体数)。
    checks["s6_usage"] = {
        "n_rows": int(row["n_rows"]),
        "distinct_agents": int(row["distinct_agents"]),
        "share_of_undefined_rows": (
            round(int(row["n_rows"]) / total_rows, 6) if total_rows else 0.0
        ),
        "note": "②(該当行 −50% 以上)は動的検査。ここは分母と分子の静的見積りだけ",
    }

    if draft is None:
        checks["s1_fields"] = {"parsed": False, "missing": list(REQUIRED_FIELDS), "bad_type": []}
        reasons.append("PARSE_FAILED:草案が JSON として読めない")
        return checks, Verdict.REJECTED, reasons

    # (s1) 必須欄の存在と型
    missing = [f for f in REQUIRED_FIELDS if f not in draft]
    bad_type = [f for f in REQUIRED_FIELDS if f in draft and not _type_ok(f, draft[f])]
    checks["s1_fields"] = {
        "parsed": True,
        "order": list(REQUIRED_FIELDS),
        "missing": missing,
        "bad_type": bad_type,
    }
    reasons += [f"MISSING_FIELD:{f}" for f in missing]
    reasons += [f"BAD_TYPE:{f}({FIELD_TYPES[f]})" for f in bad_type]

    # (s2) 失敗コードの命名規則と名前空間の衝突
    codes = draft.get("failure_codes") if _is_list_of_str(draft.get("failure_codes")) else []
    bad_name = [
        c for c in codes
        if not c or not c[0].isupper() or any(ch not in _FAILURE_CODE_OK for ch in c)
    ]
    reused = [c for c in codes if c in RESULT_CODE_NAMES]
    collide = [
        {"code": c, "namespace": ns}
        for c in codes
        if c not in RESULT_CODE_NAMES
        for ns, names in _OTHER_NAMESPACES.items()
        if c in names
    ]
    checks["s2_failure_codes"] = {
        "codes": list(codes),
        "reused_existing": reused,
        "new": [c for c in codes if c not in RESULT_CODE_NAMES],
        "bad_name": bad_name,
        "namespace_collision": collide,
    }
    reasons += [f"BAD_FAILURE_CODE:{c}" for c in bad_name]
    reasons += [f"CODE_NAMESPACE_COLLISION:{c['code']}({c['namespace']})" for c in collide]

    # (s3) 保存則の科目が科目表に実在するか
    accounts = (
        draft.get("conservation_accounts")
        if _is_list_of_str(draft.get("conservation_accounts"))
        else []
    )
    unknown = [a for a in accounts if a not in ACCOUNT_NAMES]
    checks["s3_accounts"] = {
        "accounts": list(accounts),
        "unknown": unknown,
        "table": "economy/accounts.py AccountCode",
    }
    reasons += [f"UNKNOWN_ACCOUNT:{a}" for a in unknown]

    # (s4) 保存則・性能予算に触れる語(§7 段3)→ 自動不採用
    text = raw_text + "\n" + json.dumps(draft, ensure_ascii=False)
    hits = [k for k in REVIEW_KEYWORDS if k in text]
    checks["s4_review_keywords"] = {"keywords": list(REVIEW_KEYWORDS), "hits": hits}
    reasons += [f"REVIEW_KEYWORD:{k}" for k in hits]

    if reasons:
        return checks, Verdict.REJECTED, reasons
    if duplicate:
        return checks, Verdict.DICTIONARY_ROW_SUFFICES, [f"NEAR_EXISTING:{near.get('surface', '')}"]
    return checks, Verdict.NEEDS_DYNAMIC, []


def _extract_json(text: str) -> dict[str, Any] | None:
    """応答本文から JSON オブジェクトを 1 個取り出す(前後の説明は捨てる)。"""
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


# ---------------------------------------------------------------- バッチ


def _fingerprints(client: Any, *, budget: int, threshold: int) -> dict[str, Any]:
    """決定 G「宣言する指紋は最低 6」。"""
    return {
        "1_thresholds": {
            "threshold_agents": int(threshold),
            "batch_budget": int(budget),
            "coverage_formula": "distinct_agents × max(1, distinct_cells) × max(1, distinct_hours)",
            "note": "N は『被覆の下限』に降格(決定 A)。max(1,…) は expedient",
        },
        "2_field_order": list(REQUIRED_FIELDS),
        "3_adjudicator": {
            "client": getattr(client, "name", "?"),
            "model": getattr(client, "model", ""),
            "temperature": float(getattr(client, "temperature", 0.0)),
            "n_endpoints": int(getattr(client, "n_endpoints", 0)),
            "prompt_version": DRAFT_PROMPT_VERSION,
            "prompt_sha256": DRAFT_PROMPT_SHA256,
        },
        "4_pass_lines": {
            "static": {
                "required_fields": "全欄そろい型が合うこと",
                "duplicate_ratio": DUPLICATE_RATIO,
                "review_keywords": list(REVIEW_KEYWORDS),
            },
            "dynamic_not_measured_today": {
                "conservation_residual": 0,
                "usage_reduction": 0.5,
                "state_delta": "非零",
                "accept_pass_rows": "減らない",
            },
        },
        "5_adoption_order": list(ADOPTION_ORDER),
        "6_version_policy": {
            "synonym_table_version": SYNONYM_TABLE_VERSION,
            "granularity": "ラン単位(版を上げて次ランから有効・決定 F (a))",
            "mapping_table_required": True,
        },
    }


def run_batch(
    payloads: Sequence[Mapping[str, Any]],
    *,
    client: Any | None = None,
    budget: int = DEFAULT_BUDGET,
    threshold_agents: int = DEFAULT_THRESHOLD_AGENTS,
    policy: Mapping[str, Any] | None = None,
    inputs: Iterable[str] = (),
) -> dict[str, Any]:
    """段2 起草 + 段3 静的検査を 1 バッチぶん回す(**純関数**・I/O は呼び出し側)。"""
    client = client or MockAdjudicator()
    policy = policy if policy is not None else load_policy()

    rows = merge_registries(payloads)
    total_rows = sum(int(r["n_rows"]) for r in rows)
    for row in rows:
        row["coverage"] = coverage(row)
        row["stage0_target"] = map_synonym(str(row["word"]))[0]
        row["policy_class"] = _policy_class(str(row["word"]), policy)
        row["nearest_existing"] = nearest_existing(str(row["word"]), policy)
    rows.sort(key=lambda r: (-int(r["coverage"]), -int(r["n_rows"]), str(r["word"])))
    for i, row in enumerate(rows, start=1):
        row["rank"] = i

    n_drafted = 0
    for row in rows:
        eligible = int(row["distinct_agents"]) >= int(threshold_agents)
        row["eligible"] = eligible
        if not eligible:
            row["verdict"] = Verdict.HELD_BELOW_THRESHOLD
            row["reasons"] = [f"BELOW_THRESHOLD:{row['distinct_agents']}<{threshold_agents}"]
            row["draft"] = None
            row["checks"] = {}
            continue
        if n_drafted >= int(budget):
            row["verdict"] = Verdict.HELD_BUDGET
            row["reasons"] = [f"OVER_BUDGET:{budget}"]
            row["draft"] = None
            row["checks"] = {}
            continue
        prompt = build_prompt(row)
        raw = str(client.draft(prompt, word=str(row["word"])))
        draft = _extract_json(raw)
        checks, verdict, reasons = static_checks(row, draft, raw, total_rows=total_rows)
        row["draft"] = draft
        row["draft_raw_len"] = len(raw)
        row["checks"] = checks
        row["verdict"] = verdict
        row["reasons"] = reasons
        row["needs_dynamic"] = verdict == Verdict.NEEDS_DYNAMIC
        n_drafted += 1

    return {
        "schema": "shibuya.vocab/drafts/1",
        "stage": "段2 起草 + 段3 静的検査(動的検査 ①③④ は未実施)",
        "inputs": list(inputs),
        "sources": [
            {
                "source": str(p.get("source", "")),
                "tag": str((p.get("tape") or {}).get("tag", "")),
                "n_words": int(p.get("summary", {}).get("n_words", 0)),
                "n_records_kept": int(p.get("summary", {}).get("n_records_kept", 0)),
                "cell_source": str(p.get("cell_source", "")),
                "versions": dict(p.get("versions", {})),
            }
            for p in payloads
        ],
        "fingerprints": _fingerprints(client, budget=budget, threshold=threshold_agents),
        "summary": {
            "n_words": len(rows),
            "n_rows": int(total_rows),
            "n_drafted": n_drafted,
            "n_held_below_threshold": sum(
                1 for r in rows if r["verdict"] == Verdict.HELD_BELOW_THRESHOLD
            ),
            "n_held_budget": sum(1 for r in rows if r["verdict"] == Verdict.HELD_BUDGET),
            "n_rejected": sum(1 for r in rows if r["verdict"] == Verdict.REJECTED),
            "n_dictionary_row": sum(
                1 for r in rows if r["verdict"] == Verdict.DICTIONARY_ROW_SUFFICES
            ),
            "n_needs_dynamic": sum(1 for r in rows if r["verdict"] == Verdict.NEEDS_DYNAMIC),
        },
        "words": rows,
    }


# ---------------------------------------------------------------- 報告


def render_report(result: Mapping[str, Any], *, top_k: int = 10) -> str:
    """親検収用の Markdown(上位 k 語の表・不採用理由・要動的検査)。**相対パスのみ**。"""
    fp = result["fingerprints"]
    adj = fp["3_adjudicator"]
    lines: list[str] = []
    lines.append("# 段2 起草 + 段3 静的検査 — 未定義行動の裁定バッチ(D-71・オフライン)")
    lines.append("")
    lines.append(
        f"> 入力 {len(result['sources'])} 本 / 語 {result['summary']['n_words']} / "
        f"未定義行 {result['summary']['n_rows']:,}。"
        f"起草 {result['summary']['n_drafted']}(件数予算 "
        f"{fp['1_thresholds']['batch_budget']})・"
        f"裁定 {adj['client']}(model={adj['model'] or '—'}・温度 {adj['temperature']}・"
        f"endpoints {adj['n_endpoints']})・プロンプト {adj['prompt_version']} "
        f"sha256 {adj['prompt_sha256'][:16]}…"
    )
    lines.append(">")
    lines.append(
        "> **動的検査 ①(発火と保存則)③(世界状態の差分)④(非退化)は未実施**"
        "(affordance をエンジンに実装したあとの mock ランで測る)。ここは静的 (s1)〜(s6) のみ。"
    )
    lines.append("")

    lines.append("## 1. 入力")
    lines.append("")
    lines.append("| 入力 | 語 | 記録行 | セル | 辞書版 |")
    lines.append("|---|---:|---:|---|---|")
    for path, src in zip(
        list(result["inputs"]) + [""] * len(result["sources"]), result["sources"]
    ):
        lines.append(
            f"| {path or src['tag'] or src['source']} | {src['n_words']} | "
            f"{src['n_records_kept']:,} | {src['cell_source']} | "
            f"{src['versions'].get('synonym_table', '—')} |"
        )
    lines.append("")

    lines.append(f"## 2. 上位 {top_k} 語(順位=被覆 体×セル×時間帯)")
    lines.append("")
    lines.append(
        "| 位 | 語 | 行 | 体 | セル | 時間帯 | 被覆 | 段0 写像先 | 政策分類 | "
        "最近傍(距離) | 判定 |"
    )
    lines.append("|---:|---|---:|---:|---:|---:|---:|---|---|---|---|")
    for row in list(result["words"])[:top_k]:
        near = row["nearest_existing"]
        near_txt = (
            f"{near['surface']}→{near['canonical']}({near['ratio']:.2f})"
            if near["surface"]
            else "—(0.00)"
        )
        lines.append(
            f"| {row['rank']} | {row['word']} | {row['n_rows']:,} | {row['distinct_agents']:,} | "
            f"{row['distinct_cells']} | {row['distinct_hours']} | {row['coverage']:,} | "
            f"{row['stage0_target'] or '—'} | {row['policy_class']} | "
            f"{near_txt} | {row['verdict']} |"
        )
    lines.append("")

    lines.append("## 3. 不採用・保持の理由")
    lines.append("")
    rejected = [r for r in result["words"] if r["verdict"] == Verdict.REJECTED]
    if rejected:
        lines.append("| 語 | 理由 |")
        lines.append("|---|---|")
        for row in rejected:
            lines.append(f"| {row['word']} | {' / '.join(row['reasons'])} |")
        lines.append("")
    else:
        lines.append("- 静的検査での不採用は **0 件**。")
    held_n = result["summary"]["n_held_below_threshold"]
    held_b = result["summary"]["n_held_budget"]
    lines.append(
        f"- 保持のみ: 被覆の下限 N={fp['1_thresholds']['threshold_agents']} 体 未満 **{held_n} 語** / "
        f"件数予算の外 **{held_b} 語**(**全件保持**・次バッチへ繰り越す)"
    )
    dict_rows = [r for r in result["words"] if r["verdict"] == Verdict.DICTIONARY_ROW_SUFFICES]
    if dict_rows:
        lines.append(
            "- 新語不要(s5・辞書行の追加で済む・距離 ≥ "
            f"{fp['4_pass_lines']['static']['duplicate_ratio']}): "
            + " / ".join(
                f"{r['word']}→{r['nearest_existing']['surface']}"
                f"(→{r['nearest_existing']['canonical']}・"
                f"{r['nearest_existing']['ratio']:.2f})"
                for r in dict_rows
            )
        )
        lines.append(
            "  - **これは自動却下ではない**(決定 I は (a) 人手 +(b) 距離の列。"
            "(c) 類似での自動却下は『意味損失を再生産する』として採らない)。"
            "字面の距離は写像先の意味を見ないので、**親が 1 行ずつ確かめる**。"
        )
    lines.append("")

    lines.append("## 4. 要動的検査(①③④)と人手判断")
    lines.append("")
    dyn = [
        r for r in result["words"]
        if r["verdict"] in (Verdict.NEEDS_DYNAMIC, Verdict.DICTIONARY_ROW_SUFFICES)
    ]
    if dyn:
        lines.append("| 語 | 判定 | 対象クラス | affordance | 該当行(②の静的見積り) |")
        lines.append("|---|---|---|---|---:|")
        for row in dyn:
            d = row["draft"] or {}
            lines.append(
                f"| {row['word']} | {row['verdict']} | {d.get('target_class', '—')} | "
                f"{d.get('affordance', '—')} | "
                f"{row['checks']['s6_usage']['n_rows']:,} 行 / "
                f"{row['checks']['s6_usage']['distinct_agents']:,} 体 |"
            )
    else:
        lines.append("- 静的を通った草案は **0 件**。")
    lines.append("")

    lines.append("## 5. 指紋(決定 G・6 つ)")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(fp, ensure_ascii=False, indent=1))
    lines.append("```")
    lines.append("")
    lines.append("## 6. 空欄")
    lines.append("")
    lines.append(
        "- 動的検査 ①③④ の値(affordance の実装待ち)。② の合格線 −50% も動的。"
    )
    if adj["client"] == "mock":
        lines.append(
            "- **草案の中身**(対象クラス・前提・効果・失敗コード・科目)。mock は"
            "決定論の定型(空の型)しか返さない=意味は実 LLM 起草で埋める。"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- 入口


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("registry", nargs="+", help="未定義台帳 JSON(複数可・合算する)")
    ap.add_argument("--out", type=str, required=True, help="出力ディレクトリ(drafts.json / report.md)")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET, help="1 バッチの件数予算(決定 A)")
    ap.add_argument(
        "--threshold-agents", type=int, default=DEFAULT_THRESHOLD_AGENTS,
        help="被覆の下限 N(体数・既定 10)。未満は保持のみ",
    )
    ap.add_argument("--top-k", type=int, default=10, help="報告に載せる上位語数")
    ap.add_argument("--llm", choices=("mock", "fleet"), default="mock", help="裁定 LLM の経路")
    ap.add_argument("--endpoints", type=str, default="", help="カンマ区切り http://host:port")
    ap.add_argument("--model", type=str, default="", help="served-model-name")
    args = ap.parse_args(argv)

    client: Any = MockAdjudicator()
    if args.llm == "fleet":
        client = FleetAdjudicator(str(args.endpoints).split(","), str(args.model))

    payloads = [load_registry(p) for p in args.registry]
    result = run_batch(
        payloads,
        client=client,
        budget=int(args.budget),
        threshold_agents=int(args.threshold_agents),
        inputs=[_relative(Path(p)) for p in args.registry],
    )

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "drafts.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (out_dir / "report.md").write_text(
        render_report(result, top_k=int(args.top_k)), encoding="utf-8"
    )
    s = result["summary"]
    print(
        f"{out_dir.name}/drafts.json + report.md: 語 {s['n_words']} / 起草 {s['n_drafted']} / "
        f"不採用 {s['n_rejected']} / 辞書行で済む {s['n_dictionary_row']} / "
        f"要動的検査 {s['n_needs_dynamic']} / 保持 "
        f"{s['n_held_below_threshold'] + s['n_held_budget']}"
    )
    for row in result["words"][: int(args.top_k)]:
        print(
            f"  {row['rank']:2d}. {row['word']}: {row['n_rows']} 行 / "
            f"{row['distinct_agents']} 体 / {row['distinct_cells']} セル / "
            f"{row['distinct_hours']} 時間帯 → 被覆 {row['coverage']:,} … {row['verdict']}"
        )
    return 0


def _relative(path: Path) -> str:
    """リポジトリ相対の POSIX 表記(外なら名前だけ)。**絶対パスを書かない**。"""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.name


if __name__ == "__main__":  # pragma: no cover - スクリプト入口
    raise SystemExit(main())
