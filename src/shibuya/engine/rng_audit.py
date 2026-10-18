"""K19 の検査(10f・K25 (a)): ``core.rng`` の流れが 1 ブロック(4 語)を超えて引き、隣の鍵の流れとブロックが重なるか。

``core.rng.philox(seed, 用途, c0, c1, c2, c3)`` の Philox4x64 は、引くたびにカウンタの 0 語目(``c0``)を 1 ずつ進める
(1 ブロック=4 語)。``c0`` に体や tick などの値を置いた流れが 2 ブロック以上を引くと、``c0`` が 1 大きい別の流れ
(隣の体・次の tick)と同じブロックを使う=乱数が相関する(10c の検収 P1・P2・P3・R3・R4)。

- **静的(AST)**: ``stream()``・``philox()`` の呼び手を一覧にし、1 語目が無いか定数(隣が無い)・引く語数が定数で
  4 以内のものを「静的に安全」、そのほかを「静的に決まらない」に分ける。安全な一覧は固定し(``SAFE_SITES``)、
  決まらない一覧は理由つきの表(``UNDETERMINED_SITES``)に載っていなければ落とす=新しい呼び手を実行時の検査に回す合図。
- **実行時**: ``core.rng.philox`` を包んで、ランで作った全部の流れの「使ったブロック」と、同じ (用途名, 1〜3 語目) の
  別の流れとの重なりを数える(``StreamRecorder``)。実際の重なりがある用途名と、``c0`` に値を置いて 2 ブロック以上を
  引いた用途名は、理由つきの許可の表(``K19_ALLOW``)に載っていなければ落とす。
- 〔10e(E4)〕重なりを直した: K19 の 8 用途名は ``--rng-scheme counter``(既定)では鍵の 0 語目を空けた(``core.rng.k19_counters``・
  10c の counter の 2 本と同じ形)。許可の表から ``overlap`` を消し、**重なりが 1 つでも出たら落ちる**。
  〔第330・RET〕旧の並びの流れを作る切替口 ``stateful`` は版上げ 1 回目の後に消した=許可の表の扱い ``stateful`` の
  8 用途名も消した(``world.salient``・``world.public_service_dispatch`` の日の頭の Generator は作らなくなった)。
  束ねる鍵に master seed を入れた(10f 第 3 段の検収 U8: 3 つの seed の別の鍵どうしを重なりと数えない)。同じ鍵の
  作り直しは、理由つきの表(``K19_RECREATED``)に載る用途名だけに許す。

数え方・分類の規則は実行役の自前の構成(**未リサーチ(expedient)**・10f の材料 §4 の案)。0 語目の繰り上がり(2^64)は
扱わない。
"""

from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Iterable, Mapping

# ================================================================ 静的(AST)
#: 〔第 2 期 2-2〕``philox_array``(配列で回す Philox=行ごとに 1 本の流れ・引く語数は ``words``)を足した。
RNG_FUNCS: Final[tuple[str, ...]] = ("stream", "philox", "philox_array")
#: 棄却のある分布(引く語数が値で変わる)。
REJECT: Final[frozenset[str]] = frozenset({
    "standard_normal", "normal", "exponential", "lognormal", "geometric", "poisson", "gamma", "beta",
    "standard_exponential", "standard_gamma", "binomial", "negative_binomial", "zipf", "hypergeometric",
    "multinomial", "dirichlet", "multivariate_normal", "weibull", "pareto", "vonmises", "logseries"})
VARSIZE: Final[frozenset[str]] = frozenset({"permutation", "shuffle", "permuted", "choice"})

SAFE_NO_NEIGHBOR: Final[str] = "1 語目が無いか定数=隣の流れが無い"
SAFE_STATIC: Final[str] = "静的に 4 語以内"
OVER_STATIC: Final[str] = "静的に 4 語を超える"
UNDETERMINED: Final[str] = "静的には決まらない"


@dataclass(frozen=True)
class StreamSite:
    path: str
    func: str
    domain: str
    line: int
    word0: str
    draws: tuple[str, ...]
    verdict: str

    @property
    def key(self) -> tuple[str, str, str]:
        """行番号を使わない同定(ファイル・関数・用途名)。"""
        return (self.path, self.func, self.domain)


def _rng_aliases(tree: ast.AST) -> tuple[dict[str, str], set[str]]:
    """``from shibuya.core.rng import stream as _s`` の別名と、``from shibuya.core import rng as R`` のモジュールの名前。"""
    names: dict[str, str] = {}
    mods: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[-1] == "rng":
            for a in n.names:
                if a.name in RNG_FUNCS:
                    names[a.asname or a.name] = a.name
        elif isinstance(n, ast.ImportFrom) and (n.module or "").endswith("core"):
            for a in n.names:
                if a.name == "rng":
                    mods.add(a.asname or a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if a.name.endswith("core.rng"):
                    mods.add(a.asname or a.name)
    return names, mods


def _str_consts(tree: ast.Module) -> dict[str, str]:
    out: dict[str, str] = {}
    for n in tree.body:
        tg = val = None
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            tg, val = n.targets[0].id, n.value
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
            tg, val = n.target.id, n.value
        if tg and isinstance(val, ast.Constant) and isinstance(val.value, str):
            out[tg] = val.value
    return out


def _words(meth: str, call: ast.Call) -> str:
    """1 回の呼び出しで引く語数(数字)か、決まらない理由。"""
    size = next((k.value for k in call.keywords if k.arg == "size"), None)
    if meth in REJECT:
        return "不定(棄却)"
    if meth in VARSIZE:
        if meth == "choice" and size is None and len(call.args) <= 1 and not call.keywords:
            return "1"
        return "不定(大きさが式)"
    if meth in {"random", "random_raw", "integers", "uniform"}:
        arg = size
        if arg is None:
            if meth in {"random", "random_raw"} and call.args:
                arg = call.args[0]
            elif meth in {"integers", "uniform"} and len(call.args) >= 3:
                arg = call.args[2]
        if arg is None:
            return "1"
        if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
            return str(arg.value)
        if isinstance(arg, ast.Tuple) and all(isinstance(e, ast.Constant) and isinstance(e.value, int)
                                              for e in arg.elts):
            p = 1
            for e in arg.elts:
                p *= int(e.value)  # type: ignore[union-attr]
            return str(p)
        return "不定(大きさが式)"
    return f"不定({meth})"


def _func_of(node: ast.AST, par: dict[ast.AST, ast.AST]) -> str:
    names: list[str] = []
    p = par.get(node)
    while p is not None:
        if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(p.name)
        p = par.get(p)
    return ".".join(reversed(names)) or "<module>"


def scan_sites(root: Path, files: Iterable[Path] | None = None) -> list[StreamSite]:
    """``root``(= ``src/shibuya``)の下の ``stream()``・``philox()`` の呼び手(``core/rng.py`` と ``build/`` を除く)。"""
    root = Path(root)
    fl = list(files) if files is not None else sorted(
        p for p in root.rglob("*.py") if "build" not in p.relative_to(root).parts)
    out: list[StreamSite] = []
    for p in fl:
        rel = p.relative_to(root).as_posix()
        if rel == "core/rng.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        consts = _str_consts(tree)
        names, mods = _rng_aliases(tree)
        par: dict[ast.AST, ast.AST] = {}
        for n in ast.walk(tree):
            for ch in ast.iter_child_nodes(n):
                par[ch] = n
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Name) and f.id in names:
                real = names[f.id]
            elif (isinstance(f, ast.Attribute) and f.attr in RNG_FUNCS and isinstance(f.value, ast.Name)
                  and f.value.id in mods):
                real = f.attr
            else:
                continue  # httpx の ``client.stream`` など(core.rng の外の同名)
            dn = n.args[1] if len(n.args) >= 2 else next((k.value for k in n.keywords if k.arg == "domain"), None)
            if isinstance(dn, ast.Constant) and isinstance(dn.value, str):
                dom = dn.value
            elif isinstance(dn, ast.Name) and dn.id in consts:
                dom = consts[dn.id]
            else:
                dom = "expr:" + (ast.unparse(dn) if dn is not None else "?")
            ctrs = n.args[2:]
            if real == "philox_array":
                # 〔第 2 期 2-2〕行ごとに 1 本の流れ(カウンタ=配列の行=0 語目は式)・引く語数=``words``(既定 1)
                wk = next((k.value for k in n.keywords if k.arg == "words"), None)
                wn = "1" if wk is None else (str(wk.value) if isinstance(wk, ast.Constant)
                                             and isinstance(wk.value, int) else "不定(大きさが式)")
                total_a = int(wn) if wn.isdigit() else None
                verdict_a = (UNDETERMINED if total_a is None else (SAFE_STATIC if total_a <= 4 else OVER_STATIC))
                out.append(StreamSite(rel, _func_of(n, par), dom, n.lineno, "array", (f"philox_array:{wn}",),
                                      verdict_a))
                continue
            if any(isinstance(c, ast.Starred) for c in ctrs):
                w0 = "starred"
            elif not ctrs:
                w0 = "none"
            elif isinstance(ctrs[0], ast.Constant) and isinstance(ctrs[0].value, int):
                w0 = f"const({ctrs[0].value})"
            else:
                w0 = "expr"
            draws: list[str] = []
            node_for_chain: ast.AST = n
            up = par.get(n)
            if isinstance(up, ast.Call) and isinstance(up.func, ast.Attribute) and up.func.attr == "Generator":
                node_for_chain = up
            pa = par.get(node_for_chain)
            if isinstance(pa, ast.Attribute) and isinstance(par.get(pa), ast.Call):
                draws.append(f"{pa.attr}:{_words(pa.attr, par[pa])}")  # type: ignore[arg-type]
            elif isinstance(pa, ast.Assign) and len(pa.targets) == 1 and isinstance(
                    pa.targets[0], (ast.Name, ast.Attribute)):
                tgt = ast.unparse(pa.targets[0])
                fn: ast.AST | None = pa
                while fn is not None and not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
                    fn = par.get(fn)
                for m in (ast.walk(fn) if fn is not None else []):
                    if (isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute)
                            and ast.unparse(m.func.value) == tgt):
                        draws.append(f"{m.func.attr}:{_words(m.func.attr, m)}")
                if not draws:
                    draws.append(f"(返り値を {tgt} に保持・同じ関数の中で引かない)")
            if not draws:
                draws.append("(返り値を渡す・保持=静的には追えない)")
            fixed = [d.split(":", 1)[1] for d in draws if ":" in d]
            total = sum(int(x) for x in fixed) if fixed and all(x.isdigit() for x in fixed) else None
            if w0 == "none" or w0.startswith("const"):
                verdict = SAFE_NO_NEIGHBOR
            elif total is not None and total <= 4:
                verdict = SAFE_STATIC
            elif total is not None:
                verdict = OVER_STATIC
            else:
                verdict = UNDETERMINED
            out.append(StreamSite(rel, _func_of(n, par), dom, n.lineno, w0, tuple(draws), verdict))
    return out


#: 静的に安全な呼び手(ファイル・関数・用途名)。増えても減っても落とす(10f の時点の 15 か所・〔第330〕B6 で 1 つ足して 16 か所・
#: 〔第330・RET〕legacy の天気の 2 か所(`EnvironmentProcess._pick_day`・`select_day`)を消して 14 か所・〔第 2 期 2-2〕+1=15 か所・〔第 6 期 6-5〕+1=16 か所・
#: 〔第 6 期 6-3〕+2=18 か所・〔賃金の小さな版上げ〕+1=19 か所)。
SAFE_SITES: Final[frozenset[tuple[str, str, str]]] = frozenset({
    # 1 語目が無いか定数(隣の流れが無い)7 か所
    ("agents/population.py", "sample_population", "w16.sample.reserved"),
    ("cli.py", "household_wallets", "wallet.initial"),
    ("engine/processes/civic.py", "PublicServiceDispatchProcess._counter_stream", "world.public_service_dispatch.counter"),
    ("engine/processes/rail.py", "RailProcess._assign_external", "engine.processes.rail"),
    ("engine/processes/rail.py", "RailProcess._build_external_home", "engine.processes.rail"),
    ("engine/processes/salient.py", "SalientProcess._collapse_events", "world.salient.counter"),
    ("world/assets.py", "synthetic_assets", "world.synthetic"),
    # 引く語数が定数で 4 以内 7 か所(〔第330〕+1・RET −2)
    ("engine/chooser.py", "draw_index", "engine.chooser"),
    ("engine/classical.py", "ClassicalPolicy.answer", "policy.classical"),  # 〔1-8 J0〕render の中身を answer へ移した
    ("engine/conversation.py", "ConversationManager._accepts", "expr:self.domain"),
    # 〔第330・10e B6〕天気の規則 calendar の再生日の抽選(鍵 1 語=層の名前と日番号のハッシュ・引く語数 2)
    ("engine/processes/environment.py", "sample_calendar_day", "engine.processes.environment"),
    ("llm/mock.py", "MockLLM._draws", "expr:self.domain"),
    ("llm/mock.py", "MockLLM._move_target", "expr:self.domain + _MOVE_TARGET_DOMAIN_SUFFIX"),
    ("llm/mock.py", "MockLLM._shop_target", "expr:self.domain + _SHOP_TARGET_DOMAIN_SUFFIX"),
    # 〔第 2 期 2-2 段 11a〕知人に気づく抽選(0 語目を空け 1〜3 語目に時刻の鍵・体・相手=k19_counters・1 語だけ引く)
    ("engine/proximity.py", "ProximityRule.notice_u", "proximity.notice"),
    # 〔第 6 期 6-5〕忘れる速さの人ごとのばらつき(0 語目を空け 1 語目に体の番号=k19_counter_array・2 語だけ引く)
    ("engine/memory_m1.py", "forgetting_scale", "memory.forgetting_rate"),
    # 〔第 6 期 6-3 T2〕会話の時計の人ごとの話す速さ(0 語目を空け 1 語目に体の番号=k19_counters・1 語だけ引く)と発言ごとの揺れ
    # (0 語目を空け 1〜3 語目に話し手・作った時刻・会話の番号=k19_counters・1 語だけ引く)
    ("engine/speech_clock.py", "person_mora_len_s", "talk.rate"),
    ("engine/speech_clock.py", "utterance_jitter", "talk.jitter"),
    # 〔賃金の小さな版上げ・2026-10-17〕賃金の分位(0 語目を空け 1 語目に体の鍵=k19_counter_array・1 語だけ引く)
    ("core/wage_formula.py", "wage_uniform", "economy.wage"),
    # 〔第 6 期 6-4 C1〕最初の道具の状態(0 語目を空け 1・2 語目に体の番号と欄の番号=k19_counter_array・1 語だけ引く)と
    # 連絡の判断の仮のモデルの選び(0 語目を空け刻みの鍵・体・判断の番号=k19_counters・1 語だけ引く)
    ("engine/contact/device.py", "Devices.__init__", "contact.device"),
    ("engine/contact/port.py", "ContactPort._draw", "contact.mock"),
})

#: 静的に決まらない呼び手(ファイル・関数・用途名)→ 実行時の検査での扱い。ここに無い呼び手が出たら落とす。
UNDETERMINED_SITES: Final[dict[tuple[str, str, str], str]] = {
    ("agents/population.py", "sample_population", "w16.sample.stratum"):
        "permutation の大きさ=層の人数。0 語目を空け 1 語目に層の番号(10e K19・10c 検収 P1 を直した)=実行時に重なり 0 を見る",
    ("agents/schedule.py", "draw_words", "agent.schedule"):
        "random_raw の語数が式。1 語目は体 × BLOCKS_PER_AGENT の刻みつきの設計=実行時に重なり 0 を見る",
    ("agents/schedule.py", "draw_words_per_agent", "agent.schedule"): "同上(体ごとの流れ)",
    ("engine/energy.py", "EnergyModel.draw_bodies", "body.eer"):
        "正規乱数の棄却。まれに 2 ブロック(10c 検収 R3)。0 語目を空けた(10e K19)=実行時に重なり 0 を見る",
    ("engine/energy.py", "EnergyModel.draw_bodies", "body.weight"): "同上",
    ("engine/processes/civic.py", "LargeEventProcess._plan", "world.large_event"):
        "choice の大きさが式(会場の候補)。1 語目は日の鍵=実行時に見る",
    ("engine/processes/goods_flow.py", "DeliveryInboundProcess._plan", "world.delivery_inbound"):
        "店の数の random・幾何分布・integers。1 語目は日の鍵(10c 検収 P3)=実行時に見る",
    ("engine/processes/logistics.py", "LastMileProcess.__init__", "world.delivery_last_mile"):
        "予約だけ(作って引かない=0 ブロック)。実行時に見る",
    ("engine/processes/logistics.py", "RoadWorksProcess._plan", "world.road_works"):
        "choice の大きさが工事の数。1 語目は日の鍵(10c 検収 R4)=実行時に見る",
    ("engine/decision/port.py", "present_rng", "decision.present"):
        "Generator を返し、呼び手(present)が permutation(候補の数)を引く。0 語目を空け 1〜3 語目に刻みの鍵・体・候補の数"
        "(k19)=実行時に重なり 0 を見る(第 1 期 1-8 J0)",
    ("engine/contact/port.py", "ContactPort.choose", "contact.present"):
        "Generator を present に渡し、present が permutation(候補の数)を引く。0 語目を空け 1〜3 語目に刻みの鍵・体・その刻みの"
        "その体の判断の番号(k19)=実行時に重なり 0 を見る(第 6 期 6-4 C1)",
    ("llm/mock.py", "MockLLM._stream", "expr:self.domain"):
        "Generator を返し、呼び手(MockLLM の応答)が引く。1 語目は tick=実行時に見る",
    ("perception/attention.py", "gate_stage1", "perception.attention.p_see"):
        "random(n) の n が式(呼び手はどれも 1 件=10c 検収)=実行時に見る",
    ("perception/p_notice.py", "notice_event", "perception.p_notice"):
        "random((2, 候補の数))。0 語目を空け事象の番号を 1 語目に(10e K19・10c 検収 P2 を直した)=実行時に重なり 0 を見る",
}


def check_sites(sites: Iterable[StreamSite], safe: frozenset[tuple[str, str, str]] | None = None,
                undetermined: dict[tuple[str, str, str], str] | None = None) -> list[str]:
    """静的な一覧の検査(空なら合格)。"""
    safe = SAFE_SITES if safe is None else safe
    und = UNDETERMINED_SITES if undetermined is None else undetermined
    sites = list(sites)
    out: list[str] = []
    got_safe = {s.key for s in sites if s.verdict in (SAFE_NO_NEIGHBOR, SAFE_STATIC)}
    got_und = {s.key for s in sites if s.verdict == UNDETERMINED}
    for s in sites:
        if s.verdict == OVER_STATIC:
            out.append(f"静的に 4 語を超えて引く呼び手(1 語目が値): {s.path}:{s.line} [{s.func}] {s.domain} {s.draws}")
    for k in sorted(got_safe - safe):
        out.append(f"静的に安全な呼び手が増えた(SAFE_SITES に足す): {k}")
    for k in sorted(safe - got_safe):
        out.append(f"SAFE_SITES の呼び手が無いか、安全でなくなった: {k}")
    for k in sorted(got_und - set(und)):
        out.append(f"静的に決まらない呼び手が増えた(実行時の検査に回し、UNDETERMINED_SITES に理由を足す): {k}")
    for k in sorted(set(und) - got_und):
        out.append(f"UNDETERMINED_SITES の呼び手が無い(古い): {k}")
    for k, r in und.items():
        if not r:
            out.append(f"UNDETERMINED_SITES の理由が空: {k}")
    return out


# ================================================================ 実行時の計器
@dataclass
class DomainStats:
    streams: int = 0
    max_blocks: int = 0
    ge2: int = 0
    keyed: bool = False
    actual_overlaps: int = 0
    same_key_recreated: int = 0
    examples: list[dict[str, Any]] = field(default_factory=list)


class _ArrayDraw:
    """``philox_array`` の 1 行の控え(``analyze`` が読む 0 語目の「今の値」=作った値 + 使ったブロックの数)。"""

    __slots__ = ("state",)

    def __init__(self, c0_after: int) -> None:
        self.state = {"state": {"counter": (int(c0_after),)}}


class StreamRecorder:
    """``core.rng.philox`` を包んで、作った流れを全部覚える(``install`` で入れ、``uninstall`` で戻す)。

    ``philox`` を直に import したモジュール(``agents/schedule.py``・``engine/processes/rail.py`` など)は、
    ``shibuya.`` の下の読み込み済みのモジュールの属性 ``philox`` が元の関数なら差し替える。〔第 2 期 2-2〕``philox_array``
    も同じく包み、1 行を 1 本の流れとして覚える(使ったブロック=``ceil(words / 4)``)。
    """

    def __init__(self) -> None:
        self.made: list[tuple[str, tuple[int, ...], int, Any]] = []
        #: 10e(U8): ``made`` と同じ並びの master seed(正準の文字列)。
        self.seeds: list[str] = []
        self._patched: list[tuple[Any, str, Any]] = []

    def install(self) -> "StreamRecorder":
        import sys

        import shibuya.core.rng as RNG

        orig = RNG.philox
        made = self.made
        seeds = self.seeds

        def wrapped(master_seed: Any, domain: str, *counters: int) -> Any:
            bg = orig(master_seed, domain, *counters)
            made.append((str(domain), tuple(int(c) for c in counters), int(bg.state["state"]["counter"][0]), bg))
            seeds.append(RNG._seed_to_text(master_seed))  # 10e(U8): 束ねる鍵に seed
            return bg

        orig_a = RNG.philox_array

        def wrapped_array(master_seed: Any, domain: str, counters: Any, *, words: int = 1) -> Any:
            out = orig_a(master_seed, domain, counters, words=words)
            blocks = -(-int(words) // 4)
            sd = RNG._seed_to_text(master_seed)
            for row in RNG._counter_array(counters).tolist():  # 逐次: 行の数ぶん(検査の計器だけ)
                ctr = tuple(int(c) for c in row)
                made.append((str(domain), ctr, ctr[0], _ArrayDraw(ctr[0] + blocks)))
                seeds.append(sd)
            return out

        for name, mod in list(sys.modules.items()):
            if (name == "shibuya.core.rng" or name.startswith("shibuya.")) and getattr(mod, "philox", None) is orig:
                self._patched.append((mod, "philox", orig))
                setattr(mod, "philox", wrapped)
            if ((name == "shibuya.core.rng" or name.startswith("shibuya."))
                    and getattr(mod, "philox_array", None) is orig_a):
                self._patched.append((mod, "philox_array", orig_a))
                setattr(mod, "philox_array", wrapped_array)
        return self

    def uninstall(self) -> None:
        for mod, attr, orig in reversed(self._patched):
            setattr(mod, attr, orig)
        self._patched.clear()

    def __enter__(self) -> "StreamRecorder":
        return self.install()

    def __exit__(self, *exc: Any) -> None:
        self.uninstall()

    def analyze(self) -> dict[str, DomainStats]:
        """用途名 → 数え。``blocks`` = 作った時と今の 0 語目の差。重なり = 同じ (master seed, 用途名, 1〜3 語目) で
        0 語目の違う流れどうしの使ったブロックの区間の重なり(カウンタの全語が同じ作り直しは数えない)。
        10e(U8): 束ねる鍵に master seed を入れた(seed が違えば Philox の鍵が違う=重ならない)。"""
        st: dict[str, DomainStats] = defaultdict(DomainStats)
        groups: dict[tuple[Any, ...], list[tuple[int, int, int]]] = defaultdict(list)
        seen: set[tuple[Any, ...]] = set()
        for i, (dom, ctr, c0, bg) in enumerate(self.made):
            sd = self.seeds[i] if i < len(self.seeds) else ""
            blocks = int(bg.state["state"]["counter"][0]) - c0
            d = st[dom]
            d.streams += 1
            d.max_blocks = max(d.max_blocks, blocks)
            d.ge2 += int(blocks >= 2)
            words = ctr + (0,) * (4 - len(ctr))
            if words[0] != 0:
                d.keyed = True
            full = (sd, dom) + tuple(words)
            if full in seen:
                d.same_key_recreated += 1
                continue
            seen.add(full)
            if blocks > 0:
                groups[(sd, dom) + tuple(words[1:])].append((c0 + 1, c0 + blocks, i))
        for key, iv in groups.items():
            if len(iv) < 2:
                continue
            iv.sort()
            hi_end, hi_i = iv[0][1], iv[0][2]
            for s, e, i in iv[1:]:
                if s <= hi_end and self.made[i][1] != self.made[hi_i][1]:
                    d = st[key[1]]
                    d.actual_overlaps += 1
                    if len(d.examples) < 3:
                        d.examples.append({"a": list(self.made[hi_i][1]), "b": list(self.made[i][1])})
                if e > hi_end:
                    hi_end, hi_i = e, i
        return dict(st)


#: 許可の表: 用途名 → (扱い, 理由)。扱いは ``latent``(1 語目に値を置いて 2 ブロック以上を引くが、このランの中では
#: 重ならない形)だけ。10e(E4)で ``overlap`` を消した。〔第330・RET〕扱い ``stateful``(旧値の再現の切替口
#: ``--rng-scheme stateful`` のランでだけ重なりを許した 8 用途名=w16.sample.stratum・body.weight・body.eer・
#: perception.p_notice・world.delivery_inbound・world.road_works・world.salient・world.public_service_dispatch)は切替口と
#: 一緒に消した=いまは空(重なりも潜在も 1 つでも出たら落ちる)。
LATENT: Final[str] = "latent"
K19_ALLOW: Final[dict[str, tuple[str, str]]] = {}
#: 10e(U8): 同じ鍵(seed・用途名・4 語)の流れを作り直してよい用途名と理由。ここに無い用途名の作り直しは落とす。
K19_RECREATED: Final[dict[str, str]] = {
    "w16.sample.stratum": "W16 の抽出が cli の世帯の財布と run_day の母集団で 2 回走る=同じ鍵の同じ列(同じ行を選ぶための設計)",
    "w16.sample.reserved": "w16.sample.stratum と同じ(定員先取り層)",
    "engine.processes.rail": "_build_external_home と _assign_external が同じ鍵 0 で同じ列を引く=規則を同じにするための設計",
}
#: 〔第 1 期 1-8 J0・検収 M2〕腕 ``--decision-port port`` のランの検査だけに足す作り直しの許可(既定の腕の検査には渡さない
#: =既定の腕で mock の同じ鍵を 2 回引く欠陥は今までどおり落ちる)。``recreated_for(decision_port=True)`` で渡す。
K19_RECREATED_DECISION_PORT: Final[Mapping[str, str]] = MappingProxyType({
    "llm.mock": "腕 --decision-port port の MockPort が、mock の応答と同じ鍵(刻み・体・起床の級)から行為の抽選の 1 語目を"
                "引き直す=今の mock と同じ番号を選ぶための設計(MockLLM.action_draw)",
})


def recreated_for(*, decision_port: bool = False) -> dict[str, str]:
    """``check_overlaps`` に渡す作り直しの許可(既定の腕=``K19_RECREATED`` だけ・腕 port のラン=口の分を足す)。"""
    return {**K19_RECREATED, **(K19_RECREATED_DECISION_PORT if decision_port else {})}


def check_overlaps(stats: dict[str, DomainStats], allow: dict[str, tuple[str, str]] | None = None, *,
                   recreated: dict[str, str] | None = None) -> list[str]:
    """実行時の数えの検査(空なら合格)。

    10e(E4): 実際の重なりは 1 つも許さない。潜在(1 語目に値・2 ブロック以上)は ``latent`` の用途名だけ。同じ鍵の
    作り直しは ``K19_RECREATED`` の用途名だけ(U8)。〔第330・RET〕``rng_scheme="stateful"`` の扱いは消した。
    """
    allow = K19_ALLOW if allow is None else allow
    rec_ok = K19_RECREATED if recreated is None else recreated
    out: list[str] = []
    for dom, d in sorted(stats.items()):
        kind = allow.get(dom, ("", ""))[0]
        if d.actual_overlaps:
            out.append(f"{dom}: 実際のブロックの重なり {d.actual_overlaps}(最大 {d.max_blocks} ブロック・例 {d.examples[:2]})"
                       f"が許可されない")
        elif d.keyed and d.ge2 and kind != LATENT:
            out.append(f"{dom}: 1 語目に値を置いて 2 ブロック以上を引く流れ {d.ge2}(最大 {d.max_blocks})が許可の表に無い")
        if d.same_key_recreated and dom not in rec_ok:
            out.append(f"{dom}: 同じ鍵の流れの作り直し {d.same_key_recreated} が K19_RECREATED に無い")
    for dom, (kind, reason) in allow.items():
        if kind != LATENT or not reason:
            out.append(f"{dom}: 許可の扱いか理由が違う({kind!r})")
    for dom, reason in rec_ok.items():
        if not reason:
            out.append(f"{dom}: K19_RECREATED の理由が空")
    return out
