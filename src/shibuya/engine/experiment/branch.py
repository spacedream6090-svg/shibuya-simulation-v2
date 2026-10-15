"""engine.experiment.branch — 「T0 までテープを再生して T0 から今の方策」の分岐と R-71 の 4 つの確認(第 3 期 3-3・CP5-2)。

決定 10-12 §4-5 CP5-2 (c): 状態の保存は日の境目のまま、改変はその日の好きな時刻 T0 に当てる。T0 までは基準のランの録画(テープ)を
再生して同じ動きにし(LLM を呼ばない)、T0 からだけ今の方策(mock・古典・注入した LLM)を使う。T0 までの一致を R-71 の 4 つの確認で
**毎回**確かめる。

**基準のランの記録**(``base_dir``・CLI の ``--experiment-branch``)の置き方(``cli`` の既存の引数で作れる形):

- ``tape/``(``--tape``・録画テープ)・``state/``(``--state-out``・日の境目の状態のファイル ``state-T<T>.npz``)・
  ``checkpoints.json``(``--checkpoints-out``・``shibuya.cli/checkpoints/2``=checkpoint の 2 つのハッシュと manifest)。

**分岐のランの組み立て**(``run_branch``): T0 より前の最後の日の境目の状態(``finished: false``)から再開し(無ければ 0 から)、
LLM の口を ``BranchClient`` に包む(T0 より前の呼はテープの完全一致で答える=テープ外は数えて空の応答=実 LLM へ落とさない。
古典の方策はエンジンの中の決定論の方策で内部の状態を持つので T0 より前も方策に答えさせ、テープとの食い違いを数える)。
同じ組み立てで 4 本回す: A/A の枝 2 本(同じ申込書で改変を空に=``ExperimentForm.aa``)と改変の枝 2 本(2 本目は (c) の
指紋の窓をかけた回し直し=1 本目と final が同じことも確かめる)。

**4 つの確認**(R-71 §1-6・§8-1)。結果は ``branch_report.json`` と、改変の枝の manifest の ``experiment.checks``:

- (a) 入力の一致: 基準と各枝の manifest の**設定の節**の差が腕の欄(``run_kind``・``experiment``)と、決定から導かれる欄(天気の
  差し替え → ``replay_date``・``weather``/祝日 → ``calendar``)だけ。seed の 3 つ・母集団と日課のハッシュが同じ。
- (b) T0 より前の全 checkpoint の behavior-hash が基準と同じ(各枝)・T0 より前のテープ外の呼 0・古典のテープとの食い違い 0・
  再開した状態のファイルのハッシュが基準のその日の締めの後のハッシュと同じ。
- (c) T0 以後で最初に食い違った刻みと部品(〔検収 L1〕): T0 以後の**全 checkpoint** を走査して最初に behavior-hash が食い違った
  checkpoint を見つけ(粗い比べ)、その前で一致した最後の checkpoint からの刻みの窓に系ごとの指紋(``engine.systems.probe`` の形
  =系の境目ごとの全欄の digest)をかけて A/A の枝と改変の枝を回し直し、最初に食い違った (刻み, 系, 欄) を特定する。申込書
  自身の欄(``X:``)と出来事の記録(``E:``)を除いた「世界の最初の食い違い」と、除かない最初の食い違いの 2 つ。見つからなければ
  ``None`` と理由。
- (d) A/A: A/A の枝 2 本の全 checkpoint(刻み・behavior・full)と final が**厳密に**同じ・A/A の枝の final が基準の final と同じ
  (改変を空にした枝は基準と同じ)。
- 〔親の判断 M3〕**実行の内訳**(4 つの確認とは別): 対象の店の T0 以後の開け閉めのうち担当の従業者の役割行動とつなぎ(conf 0.5)
  の件数・担当のいる店の数(``execution``)と、決定 10-12 §1-1 の「分岐でフォールバックを使わない」の判定 ``executed_by_agents``
  (summary の ``ok`` には入れない=``ok`` は 4 つの確認だけ)。つなぎを止める腕は 6-6(人の仕事を働く人のエージェントへ)まで宣言。

層の契約: engine は cli を import できない(cli は economy を import する)=ランを回す口は呼び手が渡す(``runner``=
``cli.run``)。``tools/c7/salt_compare.py`` の検定は読む役の道具なので import しない(本数と並べ替え検定は
``engine.experiment.ensemble`` が道具の形に渡す)。

未リサーチ(expedient): 窓の取り方(一致した最後の checkpoint の次の刻みから最初に食い違った checkpoint まで)・状態の選び方(T0
より前の最後の日の境目)・(c) で除く欄の接頭辞・艦隊(非同期の実 LLM)の分岐は未実装(宣言)・腕 ``--decision-port port`` の mock は口が mock を直に持つので T0 より前も
mock が答える(結果は同じ=(b) で確かめる)。

逐次ループ宣言: ``run_branch`` はランを 4 本(ランの数ぶん)。確認は checkpoint の数・指紋の行の数に比例(ランの外で 1 回)。
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, ClassVar, Final, Mapping, Sequence

from shibuya.core.time_consts import SECONDS_PER_DAY
from shibuya.engine import manifest_sections as _MS
from shibuya.engine.experiment.form import ExperimentForm

__all__ = [
    "BranchSpec", "BranchClient", "BranchOutcome", "run_branch", "payload_of", "input_match", "pre_t0_match",
    "first_divergence_coarse", "probe_first_divergence", "aa_match", "choose_state", "BASE_TAPE", "BASE_STATE",
    "BASE_CHECKPOINTS", "REPORT_NAME", "REPORT_SCHEMA", "ARM_KEYS", "DERIVED_BY_DECISION",
    "SELF_KEY_PREFIXES", "NONPORTABLE_DIGESTS", "RESUME_DERIVED", "nonportable_keys", "execution_breakdown",
    "executed_by_agents", "TABLE_DECISIONS",
]

BASE_TAPE: Final[str] = "tape"
BASE_STATE: Final[str] = "state"
BASE_CHECKPOINTS: Final[str] = "checkpoints.json"
REPORT_NAME: Final[str] = "branch_report.json"
REPORT_SCHEMA: Final[str] = "shibuya.engine.experiment/branch-report/1"
#: (a) で許す設定の欄(腕の欄=ランの種類と申込書の節)。
ARM_KEYS: Final[tuple[str, ...]] = ("run_kind", "experiment")
#: (a) 決定から導かれて動いてよい設定の欄。
DERIVED_BY_DECISION: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "weather_date": ("replay_date", "weather"),
    "holiday": ("calendar",),
})
#: (c) 「世界の最初の食い違い」から除く欄の接頭辞(申込書の控え=状態台帳の行 X・出来事の記録=行 E)。
SELF_KEY_PREFIXES: Final[tuple[str, ...]] = ("X:", "E:")
#: 系ごとの指紋の digest のうち、ランをまたいで比べられないもの(``probe.snapshot`` の代わりの digest=入れ子の物の番号 ``id``
#: を含む ``X:``・読めない ``ERR:``)。ランをまたぐ比べ((c)・(d))から外し、外した欄の名を報告に書く。
NONPORTABLE_DIGESTS: Final[tuple[str, ...]] = ("X:", "ERR:")
#: (a) 再開のランで動く設定の欄(10f の節の表で設定に入っている計器)。基準=通しの刻みの数・枝=再開からの刻みの数を宣言して許す。
#: 〔第 2 期 2-4 V5〕``group_norms.cost.ticks`` は節の表で観測に移した=2-4 より後の manifest どうしの比べでは設定の差に出ない
#: (比べは基準の manifest の節の表で見るので、2-4 より前に録った基準との比べのために残す)。
RESUME_DERIVED: Final[Mapping[str, str]] = MappingProxyType({
    "group_norms.cost.ticks": "集団の規範の計器が回った刻みの数(再開のランは再開の時刻からの数=節の表で設定に入っている計器)",
})
_STATE_RE = re.compile(r"^state-T(\d{8})\.npz$")


# ================================================================ T0 で切り替える LLM の口
@dataclass(frozen=True)
class BranchSpec:
    """分岐の指定(基準のランのテープのディレクトリ・T0 の刻み)。``cli.run`` が組み立てに渡す(``layer.staged``)。"""

    tape: str
    t0_step: int

    def make_client(self, client: Any) -> "BranchClient":
        """組み立て(``layer.make_layer``)が LLM の口を包む口(3-3 の形=``BranchClient``)。"""
        return BranchClient(client, self)


class BranchClient:
    """LLM の口(``LLMClient`` 契約=``complete``)を T0 で切り替える。T0 より前はテープ・T0 からは今の方策。

    - 状態を持たない口(mock・注入した LLM): T0 より前はテープの完全一致(``Replay.lookup``)。テープ外は数えて ``TapeMiss`` を
      投げる(橋が数えて空の応答=実 LLM へは落とさない=運用設計書 §2.5)。
    - 古典の方策(``ClassicalPolicy``=内部の状態を持つエンジンの方策): T0 より前も方策に答えさせ(状態を同じに進める)、
      テープの答えとの食い違いを数える(``mismatch``)。
    - 〔3-3b 検収 L8〕計器の数(``n_replayed``・``n_miss``・``n_policy_before``・``n_mismatch``・``n_live``)は読み取り専用の
      属性(中身は口の中の ``_meters``=口のメソッドだけが足す)。外からの代入は ``AttributeError``((b) が頼る数を書き換えない)。
    """

    #: 計器の数の名(読み取り専用の属性)。
    METER_NAMES: ClassVar[tuple[str, ...]] = ("n_replayed", "n_miss", "n_policy_before", "n_mismatch", "n_live")

    def __init__(self, live: Any, spec: BranchSpec) -> None:
        from shibuya.engine.classical import ClassicalPolicy
        from shibuya.engine.tape import Replay

        self.live = live
        self._meters: dict[str, Any] = {k: 0 for k in self.METER_NAMES}
        self.t0_step = int(spec.t0_step)
        self.replay = Replay(spec.tape)
        self.stateful = isinstance(live, ClassicalPolicy)

    n_replayed = property(lambda self: self._meters["n_replayed"], doc="T0 より前にテープから答えた呼の数")
    n_miss = property(lambda self: self._meters["n_miss"], doc="T0 より前のテープ外の呼の数")
    n_policy_before = property(lambda self: self._meters["n_policy_before"], doc="T0 より前に古典の方策が答えた呼の数")
    n_mismatch = property(lambda self: self._meters["n_mismatch"], doc="T0 より前の古典の方策とテープの食い違いの数")
    n_live = property(lambda self: self._meters["n_live"], doc="T0 から今の方策が答えた呼の数")

    def complete(self, request: Any) -> Any:
        from shibuya.engine.tape import TapeMiss
        from shibuya.llm import LLMResponse, estimate_tokens

        m = self._meters
        if int(request.tick) < self.t0_step:
            key = (int(request.agent_id), int(request.tick), int(request.wake_class), request.prompt_hash)
            if self.stateful:
                resp = self.live.complete(request)
                m["n_policy_before"] += 1
                try:
                    if self.replay.lookup(*key) != resp.text:
                        m["n_mismatch"] += 1
                except TapeMiss:
                    m["n_miss"] += 1
                return resp
            try:
                text = self.replay.lookup(*key)
            except TapeMiss:
                m["n_miss"] += 1
                raise
            m["n_replayed"] += 1
            return LLMResponse(text=text, tokens_in=estimate_tokens(request.prompt), tokens_out=estimate_tokens(text),
                               source="tape")
        m["n_live"] += 1
        return self.live.complete(request)

    async def acomplete(self, request: Any) -> Any:
        return self.complete(request)

    def replay_meter(self) -> dict[str, Any]:
        """T0 より前の再生の計器(manifest の ``experiment.replay``)。"""
        return {"t0_step": self.t0_step, "stateful_policy": bool(self.stateful), "replayed_before_t0": self.n_replayed,
                "tape_miss_before_t0": self.n_miss, "policy_before_t0": self.n_policy_before,
                "policy_mismatch_before_t0": self.n_mismatch, "live_from_t0": self.n_live}

    def __getattr__(self, name: str) -> Any:  # 包んだ口の属性(source など)はそのまま
        if name in ("live", "_meters"):
            raise AttributeError(name)
        return getattr(self.live, name)


# ================================================================ ランの結果 → 比べる形
def payload_of(res: Any) -> dict[str, Any]:
    """``RunResult`` → checkpoint の 2 つのハッシュと manifest(``cli.checkpoints_payload`` と同じ鍵の部分)。"""
    cps = []
    for c in res.checkpoints:
        cps.append({"tick": int(c.tick), "agents_hash": c.agents_hash, "world_hash": c.world_hash,
                    "population_hash": c.population_hash, "schedule_hash": c.schedule_hash,
                    "activity_hash": c.activity_hash, "behavior_hash": c.behavior_hash, "full_hash": c.full_hash})
    return {"seed": res.seed, "n_agents": int(res.n_agents), "final_hash": res.final_hash, "checkpoints": cps,
            "manifest": json.loads(json.dumps(res.run_manifest_fields(), ensure_ascii=False, default=str))}


def _flatten(d: Any, prefix: str = "") -> dict[str, str]:
    """入れ子の辞書 → ``a.b.c`` の葉(列と値は決定的な JSON の文字列=NaN もそのまま書く)。"""
    if isinstance(d, Mapping) and d:
        out: dict[str, str] = {}
        for k, v in d.items():
            out.update(_flatten(v, f"{prefix}.{k}" if prefix else str(k)))
        return out
    if not prefix:
        return {}
    return {prefix: json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)}


def _cps(doc: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
    return {int(c["tick"]): c for c in doc.get("checkpoints", [])}


# ================================================================ 4 つの確認
def input_match(base: Mapping[str, Any], run: Mapping[str, Any], *, derived: Sequence[str] = (),
                resume_expect: Mapping[str, tuple[Any, Any]] | None = None) -> dict[str, Any]:
    """(a) 入力の一致(基準と枝の manifest の設定の節の差が腕の欄と導かれる欄だけ・seed と母集団と日課が同じ)。

    ``resume_expect``: 再開のランで動く設定の欄(``RESUME_DERIVED``)→ (基準の値, 枝の値) の宣言。実際の値が宣言と同じときだけ
    許す(``resume_derived`` に書く・違えば腕の外の差)。
    """
    bm, rm = base.get("manifest") or {}, run.get("manifest") or {}
    paths = (bm.get("manifest_sections") or {}).get("paths") or _MS.PATHS
    fb, fr = _flatten(bm), _flatten(rm)
    allowed = tuple(ARM_KEYS) + tuple(derived)
    expect = {k: (json.dumps(v[0]), json.dumps(v[1])) for k, v in (resume_expect or {}).items()}
    diffs, outside, resumed = [], [], []
    for k in sorted(set(fb) | set(fr)):
        if fb.get(k) == fr.get(k):
            continue
        sec = _MS.section_of(k, paths)
        if sec in (_MS.OBSERVED, _MS.ENVIRONMENT):
            continue
        diffs.append(k)
        if k in expect and (fb.get(k), fr.get(k)) == expect[k]:
            resumed.append({"key": k, "base": fb.get(k), "run": fr.get(k), "reason": RESUME_DERIVED.get(k, "")})
            continue
        if not any(k == a or k.startswith(a + ".") for a in allowed):
            outside.append(k)
    cb, cr = base.get("checkpoints") or [], run.get("checkpoints") or []
    same_pop = bool(cb and cr) and cb[0].get("population_hash") == cr[0].get("population_hash")
    same_sched = bool(cb and cr) and cb[0].get("schedule_hash") == cr[0].get("schedule_hash")
    seeds = {k: (str(bm.get(k)), str(rm.get(k))) for k in ("population_seed", "environment_seed")}
    seeds["seed"] = (str(base.get("seed")), str(run.get("seed")))
    same_seeds = all(a == b for a, b in seeds.values())
    ok = not outside and same_pop and same_sched and same_seeds
    return {"ok": bool(ok), "config_diffs": diffs, "config_diffs_outside_arm": outside, "allowed": list(allowed),
            "resume_derived": resumed, "population_hash_same": same_pop, "schedule_hash_same": same_sched,
            "seeds_same": same_seeds}


def pre_t0_match(base: Mapping[str, Any], run: Mapping[str, Any], t0_step: int, *,
                 replay: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """(b) T0 より前の checkpoint(刻み < T0)の behavior-hash が全部基準と同じ・テープ外 0・古典の食い違い 0。"""
    cb, cr = _cps(base), _cps(run)
    steps = sorted(t for t in set(cb) & set(cr) if t < int(t0_step))
    bad = [t for t in steps if cb[t].get("behavior_hash") != cr[t].get("behavior_hash")]
    miss = int((replay or {}).get("tape_miss_before_t0", 0))
    mism = int((replay or {}).get("policy_mismatch_before_t0", 0))
    # 〔3-3b〕切り替えの口の箱の計器(刻みをまたいで残った数・切り替えの刻みに残っていた数=どちらも 0 が条件)。空にしてから
    # 数えるので作りから 0=空にする処理の退化を捕まえる計器(〔検収 L1〕)。刻みの外へ物を持ち越さない守りの本体は、艦隊で録った
    # テープ(到着待ちの行=O96 replay_inbox に T をまたいで残る物)を回す前に拒むこと(run_branch・switch.tape_crossing)
    box = int((replay or {}).get("box_carried", 0) or 0) + int((replay or {}).get("box_at_switch", 0) or 0)
    out: dict[str, Any] = {"T0_step": int(t0_step), "checkpoints_before_T0": len(steps),
                           "first_bad_step": bad[0] if bad else None, "tape_miss_before_t0": miss,
                           "policy_mismatch_before_t0": mism, "box_left": box}
    if not steps:
        out.update(ok=None, status="未検査", note="T0 より前の checkpoint が無い(checkpoint の間隔を狭める)")
        if box:
            out.update(ok=False, status="fail", note="再生の箱に刻みの外の物が残った")
    else:
        good = not bad and miss == 0 and mism == 0 and box == 0
        out.update(ok=good, status="ok" if good else "fail", note="")
    return out


_HASH_KEYS: Final[tuple[str, ...]] = ("agents_hash", "world_hash", "activity_hash", "behavior_hash", "full_hash")


def first_divergence_coarse(a: Mapping[str, Any], b: Mapping[str, Any], *, from_step: int) -> dict[str, Any]:
    """(c) の粗い比べ: 刻み ≥ ``from_step`` の checkpoint で最初に behavior-hash が違う刻みと、違うハッシュの名。"""
    ca, cb = _cps(a), _cps(b)
    steps = sorted(t for t in set(ca) & set(cb) if t >= int(from_step))
    for t in steps:
        if ca[t].get("behavior_hash") != cb[t].get("behavior_hash"):
            prev = [s for s in steps if s < t]
            return {"first_step": t, "hashes_differ": sorted(k for k in _HASH_KEYS if ca[t].get(k) != cb[t].get(k)),
                    "last_match_step": prev[-1] if prev else None, "checkpoints_compared": len(steps)}
    return {"first_step": None, "hashes_differ": [], "last_match_step": steps[-1] if steps else None,
            "checkpoints_compared": len(steps)}


def _filter(entries: Sequence[Any], skip: tuple[str, ...]) -> list[tuple[int, str, tuple[tuple[str, str], ...]]]:
    """指紋の行から、除く欄(接頭辞 ``skip``)とランをまたいで比べられない digest(``NONPORTABLE_DIGESTS``)を外す。"""
    out = []
    for t, name, items in entries:
        its = tuple((str(k), str(v)) for k, v in items
                    if not (skip and str(k).startswith(skip)) and not str(v).startswith(NONPORTABLE_DIGESTS))
        if its:
            out.append((int(t), str(name), its))
    return out


def nonportable_keys(entries: Sequence[Any]) -> list[str]:
    """ランをまたいで比べられない digest の欄の名(報告の限界の表)。"""
    return sorted({str(k) for _t, _n, items in entries for k, v in items if str(v).startswith(NONPORTABLE_DIGESTS)})


def probe_first_divergence(ea: Sequence[Any], eb: Sequence[Any], *,
                           skip: tuple[str, ...] = ()) -> dict[str, Any] | None:
    """2 本の系ごとの指紋の行(``(刻み, 系, ((欄, digest), …))``)の最初の食い違い(同じなら ``None``)。

    返す形: ``step``(食い違った行の早い方の刻み)・``system``・``keys``(値の違う欄)・``a``/``b``(その位置の (刻み, 系))。
    """
    fa, fb = _filter(ea, skip), _filter(eb, skip)
    for i in range(max(len(fa), len(fb))):
        x = fa[i] if i < len(fa) else None
        y = fb[i] if i < len(fb) else None
        if x == y:
            continue
        cand = [e for e in (y, x) if e is not None]  # 同じ刻みなら b(改変の枝)の系を報告する
        first = min(cand, key=lambda e: e[0] if e[0] >= 0 else 1 << 62)
        keys: list[str]
        if x is not None and y is not None and x[:2] == y[:2]:
            dx, dy = dict(x[2]), dict(y[2])
            keys = sorted(k for k in set(dx) | set(dy) if dx.get(k) != dy.get(k))
        else:
            keys = sorted(k for k, _v in first[2])
        return {"index": i, "step": int(first[0]), "system": first[1], "keys": keys,
                "a": None if x is None else [x[0], x[1], sorted(k for k, _v in x[2])],
                "b": None if y is None else [y[0], y[1], sorted(k for k, _v in y[2])]}
    return None


def aa_match(a: Mapping[str, Any], b: Mapping[str, Any], *, probe_a: Sequence[Any] = (),
             probe_b: Sequence[Any] = ()) -> dict[str, Any]:
    """(d) A/A: 全 checkpoint(刻み・behavior・full)と final と系ごとの指紋が厳密に同じか。"""
    la = [(int(c["tick"]), c.get("behavior_hash"), c.get("full_hash")) for c in a.get("checkpoints", [])]
    lb = [(int(c["tick"]), c.get("behavior_hash"), c.get("full_hash")) for c in b.get("checkpoints", [])]
    pd = probe_first_divergence(probe_a, probe_b)
    ok = la == lb and a.get("final_hash") == b.get("final_hash") and pd is None
    bad = [x[0] for x, y in zip(la, lb) if x != y]
    return {"ok": bool(ok), "checkpoints": len(la), "final_same": a.get("final_hash") == b.get("final_hash"),
            "first_bad_step": bad[0] if bad else None, "probe_rows": len(probe_a), "probe_first_divergence": pd}


# ================================================================ 系ごとの指紋の記録(probe の形・欄ごとの digest を残す)
def _recorder(steps: frozenset[int]) -> Any:
    from shibuya.engine.systems import probe as _PR

    class _Recorder(_PR.Probe):
        """``Probe`` の帰属をそのまま使い、行に欄ごとの digest を残す(欄を除いて比べるため)。"""

        def _attribute(self, T: int, name: str, before: Mapping[str, str], after: Mapping[str, str]) -> None:
            changed = tuple(sorted(k for k, v in after.items() if before.get(k) != v and k not in _PR.NONDET_PATHS))
            if changed:
                self.entries.append((int(T), str(name), tuple((k, after[k]) for k in changed)))

    return _Recorder(check=None, ticks=steps)


def _run_probed(runner: Callable[..., Any], kw: Mapping[str, Any], steps: frozenset[int]) -> tuple[Any, list, float]:
    from shibuya.engine.systems import probe as _PR

    rec = _recorder(steps)
    prev = _PR.ACTIVE
    _PR.ACTIVE = rec
    t0 = time.perf_counter()
    try:
        res = runner(**kw)
    finally:
        _PR.ACTIVE = prev
    return res, [[int(t), str(n), [list(x) for x in its]] for t, n, its in rec.entries], time.perf_counter() - t0


# ================================================================ 状態の選び方
def choose_state(state_dir: Path, t0_step: int) -> tuple[Path | None, dict[str, Any] | None]:
    """T0 より前(next_T < T0)の最後の日の境目の状態(``finished: false``)と見出しの写し。無ければ ``(None, None)``=0 から。"""
    best: tuple[int, Path, dict[str, Any]] | None = None
    if state_dir.is_dir():
        for p in sorted(state_dir.iterdir()):  # 逐次ループ宣言: 状態のファイルの数ぶん
            m = _STATE_RE.match(p.name)
            if not m:
                continue
            nt = int(m.group(1))
            side = p.with_suffix(".json")
            if nt >= int(t0_step) or not side.is_file():
                continue
            h = json.loads(side.read_text(encoding="utf-8"))
            if bool(h.get("finished", False)):
                continue
            if best is None or nt > best[0]:
                best = (nt, p, h)
    if best is None:
        return None, None
    return best[1], best[2]


# ================================================================ 分岐
@dataclass
class BranchOutcome:
    """``run_branch`` の結果(報告と 4 本のランの結果=A/A の枝 2 本・改変の枝 2 本(指紋の窓の回し直し))。"""

    report: dict[str, Any]
    twin_a: Any
    twin_b: Any
    branch: Any
    branch_probe: Any = None
    report_path: Path | None = None
    payloads: dict[str, Any] = field(default_factory=dict)


def _in_window(entries: Sequence[Any]) -> list[Any]:
    """指紋の行のうち刻みのある行(窓の中)だけ(ランの終わりの系の行=刻み -1 を外す)。"""
    return [e for e in entries if int(e[0]) >= 0]


def _summary(res: Any, wall: float) -> dict[str, Any]:
    return {"final_hash": res.final_hash, "checkpoints": len(res.checkpoints), "llm_calls": int(res.llm_calls),
            "wall_seconds": round(float(wall), 2)}


def _timed(runner: Callable[..., Any], kw: Mapping[str, Any]) -> tuple[Any, float]:
    t0 = time.perf_counter()
    res = runner(**kw)
    return res, time.perf_counter() - t0


#: 表(営業時間)を実行する人の居る決定(〔親の判断 M3〕実行の内訳を数える決定)。
TABLE_DECISIONS: Final[frozenset[str]] = frozenset({"opening_hours", "closure"})


def execution_breakdown(res: Any, t0_step: int) -> dict[str, Any] | None:
    """〔親の判断 M3〕対象の店の T0 以後の開け閉めの実行の内訳(ActualLog の ``store_opening`` の行=担当の従業者の役割行動 /
    conf 0.5 のつなぎ)と担当のいる店の数。営業時間の過程か控えの無いランは ``None``。"""
    import numpy as np

    from shibuya.world.processes.records import DEVIATION_CODES, DeviationVocab

    layer = getattr(res, "experiment_layer", None)
    runner = getattr(res, "runner", None)
    op = getattr(runner, "opening", None) if runner is not None else None
    log = getattr(runner, "log", None) if runner is not None else None
    if layer is None or op is None or log is None:
        return None
    targets = np.asarray(layer.targets(), dtype=np.int64)
    staff = np.asarray(op.staff_of_poi)
    rows = log.rows_for("store_opening")
    sel = (np.asarray(rows["tick"]) >= int(t0_step)) & np.isin(np.asarray(rows["subject_id"]), targets)
    codes = np.asarray(rows["deviation"])[sel]
    return {
        "targets": int(targets.size), "staffed_targets": int((staff[targets] >= 0).sum()) if targets.size else 0,
        "staffed_pois": int((staff >= 0).sum()),
        "role_actions": int((codes == DEVIATION_CODES[DeviationVocab.SCHEDULED]).sum()),
        "fallback": int((codes == DEVIATION_CODES[DeviationVocab.REPLACEMENT]).sum()),
    }


def executed_by_agents(form: ExperimentForm, exe: Mapping[str, Any] | None) -> bool | None:
    """〔親の判断 M3〕決定 10-12 §1-1「分岐の実験ではエンジンが代わりに実行する仕組みを使わない」の判定(4 つの確認とは別の欄)。

    表を実行する人の居る決定(営業時間・休業)があり、対象の店の T0 以後の開け閉めが 1 件以上あるとき: つなぎが 0 件なら真・
    1 件でも有れば偽。表を実行する人の居ない決定(天気・祝日・催し)だけ・開け閉めが無い・内訳が無いときは ``None``(判定しない)。
    """
    if exe is None or not any(str(d["decision"]) in TABLE_DECISIONS for d in form.content):
        return None
    if int(exe["role_actions"]) + int(exe["fallback"]) == 0:
        return None
    return int(exe["fallback"]) == 0


def run_branch(form: ExperimentForm, base_dir: str | Path, *, runner: Callable[..., Any],
               run_kwargs: Mapping[str, Any], aa_only: bool = False, out_dir: str | Path | None = None,
               write: bool = True, model: str | None = None, live: Callable[[Any], Any] | None = None,
               deterministic: bool | None = None) -> BranchOutcome:
    """基準のランの記録 ``base_dir`` から申込書 ``form`` の分岐を回し、4 つの確認をして ``branch_report.json`` を書く。

    回し方(〔検収 L1〕): 第 1 段=A/A の枝 a と改変の枝を指紋なしで回し、T0 以後の**全 checkpoint** を走査して最初に behavior-hash が
    食い違った checkpoint と、その前で一致した最後の checkpoint を見つける。第 2 段=A/A の枝 b と改変の枝をもう 1 本、その間の
    刻みの窓(T0 以後・最大で checkpoint の間隔)に系ごとの指紋をかけて回し、最初に食い違った (刻み, 系, 欄) を特定する。食い違いが
    無ければ第 2 段の改変の枝は回さず、(c) は ``None`` と理由。

    Args:
        runner: ランを回す口(``cli.run``=台帳つき)。``run_kwargs`` に ``resume_from``・``experiment``・``experiment_branch``
            を足して呼ぶ。
        run_kwargs: 基準のランと同じ引数(``resume_from``・``state_out``・``stop_at_tick``・``tape_path`` は外す。
            ``experiment_model`` はそのまま渡す)。
        aa_only: 改変の枝も改変を空にする(``--experiment-aa``=全部 A/A)。
        out_dir: 報告の置き場(既定 ``base_dir/branches/<申込書の指紋の先頭 16 字>``)。既にある報告は上書きしない。
        model・live・deterministic: 〔3-3b〕T からの切り替えの口(``switch.SwitchSpec``)の仮のモデルの札・T からの口を作る関数
            (``None``=ランの口そのもの)・決定論の宣言(``None``=T からの口の宣言=属性 ``deterministic`` が真偽のとき〔検収 L2〕・
            それも無ければ札から)。決定論なら (d) は A/A の厳密一致を求める(3-3 の約束 (4)(d))・非決定なら T より前の一致と床。

    〔3-3b〕切り替えの口は ``switch.ReplaySwitch``(T は計算のまとめの窓の頭=基準の manifest の ``batching.width_s``・再生の箱は
    刻みごとに空にする・艦隊で録ったテープは拒む)。(c) に A/A の枝 2 本の最初の食い違いとの刻みの差(``vs_aa``)、(d) を
    決定論の確認(``d_determinism``)と床の分布(``d_floor``)に分けた欄を足した(3-3 の欄はそのまま)。
    """
    from shibuya.core.time_consts import NS_PER_SECOND
    from shibuya.engine.experiment import ensemble as _EN
    from shibuya.engine.experiment import switch as _SW
    from shibuya.engine.tape import Tape

    base_dir = Path(base_dir)
    base = json.loads((base_dir / BASE_CHECKPOINTS).read_text(encoding="utf-8"))
    bman = base.get("manifest") or {}
    step_seconds = int(bman.get("tick_seconds") or bman.get("step_seconds"))
    steps_per_day = SECONDS_PER_DAY // step_seconds
    total = int(bman.get("sim_days") or 1) * steps_per_day
    t0 = form.start_step(step_seconds)
    if not (0 < t0 < total):
        raise ValueError(f"分岐の T0(刻み {t0})が基準のランの内側に無い(0〜{total})")
    # 〔3-3b〕T は計算のまとめの窓の頭(3-2 の窓の待ち行列・幅は基準のランの manifest の batching.width_s)
    width_s = int((bman.get("batching") or {}).get("width_s") or step_seconds)
    step_ns = step_seconds * NS_PER_SECOND
    if _SW.window_head_step(int(form.start), width_s * NS_PER_SECOND, step_ns) != t0:
        raise AssertionError("窓の頭の刻みと申込書の T0 の刻みが違う")
    tape = base_dir / BASE_TAPE
    if not tape.is_dir():
        raise ValueError(f"基準のランの記録にテープ({BASE_TAPE}/)が無い")
    cross = _SW.tape_crossing(Tape(tape), t0)
    if cross["fleet_rows_before_t0"]:
        raise ValueError(f"テープに T0 より前に出して後で届く行(艦隊で録った到着待ちの行)が {cross['fleet_rows_before_t0']} 行"
                         f"(うち T0 をまたぐ行 {cross['rows_crossing_t0']}): 再生の箱に刻みの外の物が残る=艦隊の分岐は 6-7 まで")
    state, header = choose_state(base_dir / BASE_STATE, t0)
    begin = int(header["progress"]["next_T"]) if header else 0
    kw = {k: v for k, v in dict(run_kwargs).items()
          if k not in ("resume_from", "state_out", "stop_at_tick", "tape_path", "experiment", "experiment_aa",
                       "experiment_branch")}
    if state is not None:
        kw["resume_from"] = str(state)
    spec = _SW.SwitchSpec(tape=str(tape), t0_step=t0, t0_ns=int(form.start), window_ns=width_s * NS_PER_SECOND,
                          step_ns=step_ns, model=model, deterministic=deterministic, live=live)
    aa_form = form.aa()
    main_form = aa_form if aa_only else form
    kw_aa = {**kw, "experiment": aa_form, "experiment_branch": spec}
    kw_main = {**kw, "experiment": main_form, "experiment_branch": spec}
    # ---- 第 1 段: 指紋なし(A/A の枝 a・改変の枝)
    res_a, wa = _timed(runner, kw_aa)
    res_m, wm = _timed(runner, kw_main)
    ya, ym = payload_of(res_a), payload_of(res_m)
    coarse = first_divergence_coarse(ya, ym, from_step=t0)
    # ---- 第 2 段: 最初に食い違った checkpoint とその前で一致した checkpoint の間に指紋の窓(A/A の枝 b・改変の枝の回し直し)
    res_p, wp, pb, pm = None, 0.0, [], []
    window: list[int] | None = None
    if coarse["first_step"] is None:
        res_b, wb = _timed(runner, kw_aa)
        world = anyd = None
        reason = f"T0 以後の checkpoint {coarse['checkpoints_compared']} 本で食い違いが無い"
    else:
        lo = t0 if coarse["last_match_step"] is None else max(t0, int(coarse["last_match_step"]) + 1)
        hi = int(coarse["first_step"])
        window = [lo, hi]
        steps = frozenset(range(lo, hi + 1))
        res_b, pb, wb = _run_probed(runner, kw_aa, steps)
        res_p, pm, wp = _run_probed(runner, kw_main, steps)
        world = probe_first_divergence(_in_window(pb), _in_window(pm), skip=SELF_KEY_PREFIXES)
        anyd = probe_first_divergence(_in_window(pb), _in_window(pm))
        reason = "" if world is not None else ("窓の中で世界の欄の食い違いが見えない(ランをまたいで比べられない digest の欄"
                                               "だけが違う)")
    yb = payload_of(res_b)
    derived = sorted({k for d in main_form.content for k in DERIVED_BY_DECISION.get(str(d["decision"]), ())})
    lay_a, lay_m = getattr(res_a, "experiment_layer", None), getattr(res_m, "experiment_layer", None)
    rep_a = None if lay_a is None or lay_a.branch is None else lay_a.branch.replay_meter()
    rep_m = None if lay_m is None or lay_m.branch is None else lay_m.branch.replay_meter()
    # (b) の補い(〔検収 L2〕基準の自己一致): 再開に使った基準の状態のファイルの見出しのハッシュ=基準の manifest のその日の締め
    # の後のハッシュ(枝が戻した状態の検算は組み立ての full-hash の検算が受け持つ)
    resume_check: dict[str, Any] | None = None
    if header is not None:
        eod = None
        for r in bman.get("daily") or []:
            if int(r.get("end_T", -1)) == begin:
                eod = (r.get("state_hashes_end_of_day") or {}).get("behavior_hash")
        got = (header.get("hashes") or {}).get("behavior_hash")
        resume_check = {"state_file": state.name if state else None, "next_T": begin,
                        "base_state_matches_base_end_of_day": got == eod, "end_of_day_found": eod is not None,
                        "note": "基準の自己一致(基準の状態のファイルの見出し × 基準の manifest の日ごとの記録)"}
    resume_expect = None
    if state is not None:
        resume_expect = {"group_norms.cost.ticks": (total, total - begin)}
    exe_m, exe_a = execution_breakdown(res_m, t0), execution_breakdown(res_a, t0)
    rep_b = None
    lay_b = getattr(res_b, "experiment_layer", None)
    if lay_b is not None and lay_b.branch is not None:
        rep_b = lay_b.branch.replay_meter()
    aa_coarse = first_divergence_coarse(ya, yb, from_step=t0)
    sw_model = str((rep_a or {}).get("model") or (rep_m or {}).get("model") or "")
    sw_det = bool((rep_a or {}).get("deterministic", True))
    checks = {
        "a_input_match": {"aa": input_match(base, ya, resume_expect=resume_expect),
                          "branch": input_match(base, ym, derived=derived, resume_expect=resume_expect)},
        "b_pre_t0": {"aa": pre_t0_match(base, ya, t0, replay=rep_a), "branch": pre_t0_match(base, ym, t0, replay=rep_m),
                     "resume_state": resume_check,
                     "aa_b": pre_t0_match(base, yb, t0, replay=rep_b)},  # 〔3-3b〕A/A の枝 b も
        "c_first_divergence": {
            "coarse": coarse, "world": world, "any": anyd, "reason": reason, "window_steps": window,
            "probe_rows": {"aa": len(pb), "branch": len(pm)},
            "nonportable_keys": nonportable_keys(list(pb) + list(pm)),
            "branch_repeat_same": None if res_p is None else (res_p.final_hash == res_m.final_hash),
            # 〔3-3b〕A/A の枝 2 本の最初の食い違いと、改変の枝の最初の食い違いとの刻みの差
            "aa_coarse": aa_coarse, "vs_aa": _SW.vs_aa(coarse, aa_coarse),
        },
        "d_aa": dict(aa_match(ya, yb), final_equals_base=ya.get("final_hash") == base.get("final_hash")),
    }
    # 〔3-3b〕(d) の分け=決定論の確認と床の分布(仮-24)
    twins_pre = pre_t0_match(ya, yb, t0)
    checks["d_determinism"] = _SW.determinism(
        model=sw_model, deterministic=sw_det,
        twins_vs_base=(checks["b_pre_t0"]["aa"]["ok"], checks["b_pre_t0"]["aa_b"]["ok"]),
        twins_before_t0=twins_pre["ok"], aa_exact=bool(checks["d_aa"]["ok"]),
        final_equals_base=bool(checks["d_aa"]["final_equals_base"]), expect_base=live is None)
    cpa, cpb = _cps(ya), _cps(yb)
    after = sorted(t for t in set(cpa) & set(cpb) if t >= t0)
    differ = [t for t in after if cpa[t].get("behavior_hash") != cpb[t].get("behavior_hash")]
    floor_metrics = _EN.floor_summary(_EN.floor_values(main_form, [(ya, yb)]))
    checks["d_floor"] = {
        "pairs": 1, "model": sw_model, "deterministic": sw_det, "metrics": floor_metrics,
        "checkpoints_after_t0": len(after), "checkpoints_differ": len(differ),
        "first_differ_step": differ[0] if differ else None,
        "zero": not differ and all(m.get("abs_max") in (0.0, None) for m in floor_metrics.values()),
        "note": ("T 以後の A/A の枝 2 本の差(b − a)。アンサンブルの各メンバーの対を ensemble.floor_values に並べると床の分布に"
                 "なる。決定論の札(mock・古典)では 0"),
    }
    a_ok = checks["a_input_match"]["aa"]["ok"] and checks["a_input_match"]["branch"]["ok"]
    b_vals = [checks["b_pre_t0"]["aa"]["ok"], checks["b_pre_t0"]["branch"]["ok"], checks["b_pre_t0"]["aa_b"]["ok"]]
    if resume_check is not None:
        b_vals.append(bool(resume_check["base_state_matches_base_end_of_day"]))
    b_ok = None if any(v is None for v in b_vals) else all(b_vals)
    d_ok = checks["d_determinism"]["ok"]  # 〔3-3b〕決定論の札でランの口そのもの=3-3 と同じ(A/A が厳密に同じ・final=基準)
    summary = {
        "a": bool(a_ok), "b": b_ok, "d": d_ok,
        "c_step": None if world is None else world["step"],
        "c_system": None if world is None else world["system"],
        # ok は 4 つの確認(a・b・d が通り c を報告した)だけ。§1-1 の実行の条件は別の欄(〔親の判断 M3〕)
        "ok": bool(a_ok) and b_ok is True and d_ok is True,
        "executed_by_agents": executed_by_agents(main_form, exe_m),
        # 〔3-3b〕仮のモデル・(c) の A/A との比べ・(d) の床
        "model": sw_model, "deterministic": sw_det,
        "c_aa_step": checks["c_first_divergence"]["vs_aa"]["aa_first_step"],
        "c_gap_steps": checks["c_first_divergence"]["vs_aa"]["gap_steps"],
        "d_floor_zero": bool(checks["d_floor"]["zero"]),
    }
    report = {
        "schema": REPORT_SCHEMA, "form_sha256": form.sha256(), "aa_form_sha256": aa_form.sha256(),
        "main_form_sha256": main_form.sha256(), "aa_only": bool(aa_only), "T0_ns": int(form.start), "T0_step": t0,
        "resume_from": None if state is None else state.name, "begin_step": begin, "total_steps": total,
        "base": {"final_hash": base.get("final_hash"), "checkpoints": len(base.get("checkpoints") or [])},
        "runs": {"aa_a": _summary(res_a, wa), "aa_b": _summary(res_b, wb), "branch": _summary(res_m, wm),
                 **({"branch_probe": _summary(res_p, wp)} if res_p is not None else {})},
        "checks": checks, "summary": summary,
        "switch": None if lay_m is None or lay_m.branch is None else lay_m.branch.switch_record(),
        "execution": {"branch": exe_m, "aa": exe_a,
                      "note": ("対象の店の T0 以後の開け閉め(ActualLog の store_opening)=担当の従業者の役割行動 / conf 0.5 の"
                               "つなぎ。executed_by_agents は決定 10-12 §1-1 の「分岐でフォールバックを使わない」の判定で、"
                               "summary.ok(4 つの確認)には入れない")},
    }
    if lay_m is not None:
        lay_m.record_checks(summary)  # 持ち主の口(1 回だけ・〔検収 M4〕)
    report["experiment"] = payload_of(res_m)["manifest"].get("experiment")
    path = None
    if write:
        od = Path(out_dir) if out_dir is not None else base_dir / "branches" / form.sha256()[:16]
        od.mkdir(parents=True, exist_ok=True)
        path = od / REPORT_NAME
        if path.exists():
            raise FileExistsError(f"{REPORT_NAME} は既にある(上書きしない)")
        path.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8",
                        newline="\n")
    return BranchOutcome(report=report, twin_a=res_a, twin_b=res_b, branch=res_m, branch_probe=res_p,
                         report_path=path, payloads={"aa_a": ya, "aa_b": yb, "branch": ym})
