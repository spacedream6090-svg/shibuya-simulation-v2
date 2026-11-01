"""engine.experiment.ensemble — 探索と確認・アンサンブルの封印・事前登録(CP14)・対の差の形・技量スコアの器(第 3 期 3-3)。

決定 10-12 §4-5「探索と確認」「複数ランの作り方」・CP14・R-71 §2・§8-3。

- **アンサンブル**: 初期状態 × モデル × 偶然。初期状態の番号 ``i`` → 母集団の seed と環境の seed(10f の seed の 3 分割の 2 つ
  =``seed0 + i``)・偶然の番号 ``c`` → 動きの seed(salt=``seed0 + c``)・モデル=申込書の札。並びは決定的。
- **封印**(``seal``・〔親の判断 M2〕**単位=初期状態**): 回す前に初期状態の半分を封印する。並べ方=アンサンブルの指紋と初期状態の
  正準の JSON の sha256 の昇順・先頭 ``n // 2`` を封印(holdout と同じ規律=探索と確認は初期状態を共有しない・モデルの札と
  偶然の seed は各半分の中で組む)。封印の指紋 ``sealed_sha256``(sha256)を記録に書く。``Seal`` は指紋と数だけを持ち、封印した
  初期状態の一覧を持たない。``members(form)`` は**自分の半分だけ**を返す(探索=封印していない半分・確認=封印した半分)。
- **入口**(``entrance``・〔親の判断 M1〕): 組み立てがランの seed の 3 つとモデルの札でメンバーと半分を決め、探索の申込書が封印した
  半分の初期状態で回ろうとしたら止める(``ValueError``)。確認の申込書は封印した半分だけで回り、事前登録の封印の指紋を照合する。
  manifest の ``experiment`` に ``member``・``half`` を書く。
- **事前登録**(``preregister``・CP14 の封印の形式): 申込書と指標の定義の正準の JSON の指紋(sha256 と blake3=計画 §4 の
  blake3 も並べた)・封印の指紋・問い・指標・技量スコアの器を 1 つの JSON(``record_sha256`` つき)にする=公開の記録
  (``docs/predictions/``)に書ける形。書くのは呼び手(本段では置き場を作らない)。
- **対の差の形**(``paired_values``・``metrics_spec``): 基準の枝と改変の枝(か A/A の 2 本)の checkpoints の JSON の組の列 →
  ``tools/c7/salt_compare.py`` の ``--values`` の形 ``{指標の id: {"base": [...], "arm": [...]}}`` と ``--metrics`` の形。
  最低 6 対(両側 α=0.05 の p の下限 2/2^6=R-71 §2-3)=``pairs_status``。
- **技量スコア**(CP14・``skill_container``・``skill_score``): **器だけ**=単純な基準(去年の同じ日・平均・前の週)に対する当たりの比
  ``1 − 誤差/基準の誤差`` の式の置き場と欄。値は空(``None``)。
- 〔第 3 期 3-3b・仮-24〕技量スコアの**隣に生の点数**の欄(``raw``=fair CRPS・基準の CRPS(点の予測は絶対誤差)・rank histogram・
  広がりと誤差の比=√((M+1)/M) の補正つき)。技量スコアの形は元の点数が proper でも一般に proper でない(Gneiting & Raftery
  2007 の式 (8) の注意=R-117 §2-3)ので、複数の予測の優劣は生の点数で決める。値は計器 ``tools/instruments/skill_gauge.py`` が
  埋める(器の値は空)。
- 〔3-3b・仮-24〕事前登録の記録に封印の証拠の欄(``evidence``=手元の git の commit と公開リポへの push の記録・第三者の時刻印は
  無し=値は公開する呼び手が埋める・ランの manifest の ``git_commit`` 等は今の形のまま)と慣らしの規則(``warmup``=
  ``engine.experiment.warmup.rule_record``)を足した。
- 〔3-3b・仮-24〕**床の分布**(``floor_values``・``floor_summary``): A/A の枝 2 本の組の列 → 指標ごとの差(b − a)の分布(R-117 §1-2・
  §6-1=実 LLM では A/A の対の差がばらつきの床)。

未リサーチ(expedient): seed の割り振り(``seed0 + 番号``)・封印の並べ方(初期状態の sha256 の昇順・先頭 ``n // 2``)・初期状態が 1 つのアンサンブルは封印が空(確認には初期状態が 2 つ以上要る)・事前登録の JSON の欄・
blake3 と sha256 を並べたこと。

逐次ループ宣言: メンバーの数ぶん(ランの外で 1 回)。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Final, Mapping, Sequence

from shibuya.engine.experiment.form import CONFIRM, EXPLORE, ExperimentForm, canonical_json, sha256_hex

__all__ = [
    "Member", "members", "Seal", "seal", "seal_record", "entrance", "HALF_EXPLORE", "HALF_CONFIRM", "preregister",
    "paired_values", "metrics_spec",
    "pairs_status", "MIN_PAIRS_TWO_SIDED", "MIN_PAIRS_ONE_SIDED", "skill_score", "skill_container",
    "SKILL_BASELINES", "SEAL_SCHEMA", "PREREG_SCHEMA", "SKILL_SCHEMA", "get_path",
    "RAW_SCORES", "EVIDENCE_SCHEMA", "evidence_container", "floor_values", "floor_summary", "FLOOR_SCHEMA",
]

SEAL_SCHEMA: Final[str] = "shibuya.engine.experiment/seal/1"
PREREG_SCHEMA: Final[str] = "shibuya.engine.experiment/preregistration/1"
SKILL_SCHEMA: Final[str] = "shibuya.engine.experiment/skill/1"
#: R-71 §2-3: 両側 α=0.05 に届く最小の対の数・向きを事前登録した片側の最小。
MIN_PAIRS_TWO_SIDED: Final[int] = 6
MIN_PAIRS_ONE_SIDED: Final[int] = 5
#: CP14 の単純な基準(去年の同じ日・平均・前の週)。
SKILL_BASELINES: Final[tuple[str, ...]] = ("last_year_same_day", "mean", "previous_week")
#: 〔3-3b〕技量スコアの隣に並べる生の点数(仮-24・R-117 §2-3)。
RAW_SCORES: Final[tuple[str, ...]] = ("crps_fair", "rank_histogram", "spread_skill")
EVIDENCE_SCHEMA: Final[str] = "shibuya.engine.experiment/seal-evidence/1"
FLOOR_SCHEMA: Final[str] = "shibuya.engine.experiment/floor/1"


@dataclass(frozen=True)
class Member:
    """アンサンブルの 1 本(初期状態の番号・モデルの札・偶然の番号と、それぞれの seed)。"""

    initial: int
    model: str
    chance: int
    population_seed: int
    environment_seed: int
    seed: int

    def to_dict(self) -> dict[str, Any]:
        return {"initial": self.initial, "model": self.model, "chance": self.chance,
                "population_seed": self.population_seed, "environment_seed": self.environment_seed, "seed": self.seed}

    def run_kwargs(self) -> dict[str, Any]:
        """``cli.run`` の seed の 3 つ(母集団・環境・動き)と申込書のモデルの札(``experiment_model``)。"""
        return {"seed": self.seed, "population_seed": self.population_seed, "environment_seed": self.environment_seed,
                "experiment_model": self.model}


def _all_members(form: ExperimentForm) -> tuple[Member, ...]:
    """アンサンブルの全部(初期状態 × モデル × 偶然・並び=初期状態 → モデル → 偶然)。**封印の内側の関数**(外へは出さない)。"""
    e = form.ensemble
    s0 = int(e["seed0"])
    out = []
    for i in range(int(e["initial"])):  # 逐次ループ宣言: メンバーの数ぶん
        for m in e["model"]:
            for c in range(int(e["chance"])):
                out.append(Member(initial=i, model=str(m), chance=c, population_seed=s0 + i,
                                  environment_seed=s0 + i, seed=s0 + c))
    return tuple(out)


def _initial_dict(form: ExperimentForm, i: int) -> dict[str, int]:
    s0 = int(form.ensemble["seed0"])
    return {"initial": int(i), "population_seed": s0 + int(i), "environment_seed": s0 + int(i)}


def _ensemble_sha(form: ExperimentForm) -> str:
    return sha256_hex({"schema": SEAL_SCHEMA, "ensemble": form.ensemble})


def _sealed_initials(form: ExperimentForm) -> frozenset[int]:
    """封印した初期状態の番号(**封印の内側の関数**)。並べ方=アンサンブルの指紋と初期状態の正準の JSON の sha256 の昇順・先頭
    ``n // 2``。"""
    esha = _ensemble_sha(form)
    n = int(form.ensemble["initial"])
    order = sorted(range(n), key=lambda i: hashlib.sha256(
        (esha + canonical_json(_initial_dict(form, i))).encode("utf-8")).hexdigest())
    return frozenset(order[: n // 2])


#: 半分の名(探索の半分=封印していない初期状態・確認の半分=封印した初期状態)。
HALF_EXPLORE: Final[str] = "explore"
HALF_CONFIRM: Final[str] = "confirm"


class Seal:
    """封印(回す前に作る・**単位=初期状態**=母集団と環境の seed の組)。公開するのは指紋と数だけ。

    探索の半分と確認の半分は初期状態を共有しない(holdout と同じ規律)。モデルの札と偶然の seed は各半分の中で組む。封印した
    初期状態の一覧は持たない(``members_for``・``half_of`` がそのつど申込書から作る)。欄は付け替えられない。
    """

    __slots__ = ("ensemble_sha256", "sealed_sha256", "n_initial", "n_sealed_initial", "n_members")

    def __init__(self, form: ExperimentForm) -> None:
        sealed = _sealed_initials(form)
        esha = _ensemble_sha(form)
        rows = [_initial_dict(form, i) for i in sorted(sealed)]
        object.__setattr__(self, "ensemble_sha256", esha)
        object.__setattr__(self, "sealed_sha256", sha256_hex({"schema": SEAL_SCHEMA, "unit": "initial",
                                                               "ensemble_sha256": esha, "sealed_initials": rows}))
        object.__setattr__(self, "n_initial", int(form.ensemble["initial"]))
        object.__setattr__(self, "n_sealed_initial", len(sealed))
        object.__setattr__(self, "n_members", len(_all_members(form)))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("封印の欄は付け替えられない")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("封印の欄は消せない")

    def _check(self, form: ExperimentForm) -> None:
        if _ensemble_sha(form) != self.ensemble_sha256:
            raise ValueError("申込書のアンサンブルがこの封印と違う")

    def half_of(self, form: ExperimentForm, member: Member) -> str:
        """メンバーの半分(``explore``=封印していない初期状態・``confirm``=封印した初期状態)。"""
        self._check(form)
        return HALF_CONFIRM if int(member.initial) in _sealed_initials(form) else HALF_EXPLORE

    def members_for(self, form: ExperimentForm, *, half: str | None = None) -> tuple[Member, ...]:
        """申込書が受け取ってよい半分(探索=封印していない半分・確認=封印した半分)。

        ``half`` を ``"confirm"``(封印した半分)にして探索の申込書で呼ぶと ``PermissionError``(探索は封印を読めない)。確認の
        申込書は事前登録の ``seal_sha256`` がこの封印の指紋と同じでなければ ``PermissionError``。
        """
        self._check(form)
        want = half or (HALF_CONFIRM if form.kind == CONFIRM else HALF_EXPLORE)
        if want not in (HALF_EXPLORE, HALF_CONFIRM):
            raise ValueError("half は explore か confirm")
        if want == HALF_EXPLORE and form.kind == CONFIRM:
            raise PermissionError("確認のランは封印した半分で回す(探索の半分は使わない)")
        if want == HALF_CONFIRM:
            if form.kind == EXPLORE:
                raise PermissionError("探索は封印した半分を読めない(holdout と同じ規律)")
            pre = form.preregistration
            if pre is None or pre["seal_sha256"] != self.sealed_sha256:
                raise PermissionError("確認の申込書の事前登録の封印の指紋がこの封印と違う")
        sealed = _sealed_initials(form)
        return tuple(m for m in _all_members(form) if (m.initial in sealed) == (want == HALF_CONFIRM))


def seal(form: ExperimentForm) -> Seal:
    """アンサンブルの半分を封印する(単位=初期状態・決定的=同じアンサンブルなら探索と確認の申込書で同じ封印)。"""
    return Seal(form)


def members(form: ExperimentForm) -> tuple[Member, ...]:
    """申込書が回してよいメンバー(**自分の半分だけ**=探索は封印していない半分・確認は封印した半分)。"""
    return seal(form).members_for(form)


def seal_record(s: Seal, form: ExperimentForm) -> dict[str, Any]:
    """封印の記録(封印の中身は書かない=指紋と数と、探索の申込書なら封印していない半分)。"""
    opened = s.members_for(form, half=HALF_EXPLORE) if form.kind == EXPLORE else ()
    return {"schema": SEAL_SCHEMA, "unit": "initial", "ensemble_sha256": s.ensemble_sha256,
            "sealed_sha256": s.sealed_sha256, "n_initial": s.n_initial, "n_sealed_initial": s.n_sealed_initial,
            "n_members": s.n_members, "open": [m.to_dict() for m in opened]}


def _same_seed(a: Any, b: int) -> bool:
    if isinstance(a, bool):
        return False
    try:
        return int(a) == int(b)
    except (TypeError, ValueError):
        return False


def entrance(form: ExperimentForm, *, seed: Any, population_seed: Any, environment_seed: Any,
             model: str | None = None) -> tuple[Member, str]:
    """ランの入口の封印の検査(組み立てが呼ぶ): このランの seed の 3 つとモデルの札がアンサンブルのどのメンバーで、どちらの
    半分かを返す。探索の申込書が封印した半分の初期状態で回ろうとした・確認の申込書が封印していない半分で回ろうとした・
    確認の事前登録の封印の指紋が違う・アンサンブルの外の seed・モデルの札が決まらない、は ``ValueError``(止める)。"""
    models = tuple(form.ensemble["model"])
    if model is None:
        if len(models) != 1:
            raise ValueError(f"申込書のモデルの札が {len(models)} つ: どの札のランかを渡す(experiment_model)")
        model = models[0]
    if model not in models:
        raise ValueError(f"モデルの札 {model!r} は申込書のアンサンブル {list(models)} に無い")
    hit = [m for m in _all_members(form) if m.model == model and _same_seed(seed, m.seed)
           and _same_seed(population_seed, m.population_seed) and _same_seed(environment_seed, m.environment_seed)]
    if not hit:
        raise ValueError(f"このランの seed(動き {seed!r}・母集団 {population_seed!r}・環境 {environment_seed!r})は申込書の"
                         "アンサンブルのメンバーでない(封印を確かめられないランは回さない)")
    s = seal(form)
    member = hit[0]
    half = s.half_of(form, member)
    if form.kind == EXPLORE and half == HALF_CONFIRM:
        raise ValueError("探索の申込書が封印した半分の初期状態で回ろうとした(holdout と同じ規律=止める)")
    if form.kind == CONFIRM:
        if half != HALF_CONFIRM:
            raise ValueError("確認の申込書は封印した半分の初期状態だけで回る")
        pre = form.preregistration
        if pre is None or pre["seal_sha256"] != s.sealed_sha256:
            raise ValueError("確認の申込書の事前登録の封印の指紋がこの封印と違う")
    return member, half


# ================================================================ 事前登録(CP14)
def preregister(draft: Mapping[str, Any], s: Seal, *, registered_at: str | None = None
                ) -> tuple[dict[str, Any], ExperimentForm]:
    """確認のランの事前登録: 下書き(申込書の辞書・事前登録の欄なし)→(公開の記録の JSON, 確認の申込書)。

    登録の指紋=申込書(種類=確認・事前登録の欄を除く)と指標の定義の正準の JSON の sha256(``ExperimentForm.registration_digest``
    と同じ値)と blake3。封印の指紋を入れる。``registered_at``(時刻の文字列)は記録に書くだけで指紋に入れない。
    """
    import blake3 as _blake3

    d = dict(draft)
    d.pop("preregistration", None)
    norm = ExperimentForm.from_dict({**d, "kind": EXPLORE}).to_dict()
    norm["kind"] = CONFIRM
    norm.pop("preregistration")
    reg = sha256_hex(norm)
    form = ExperimentForm.from_dict({**norm, "preregistration": {"seal_sha256": s.sealed_sha256,
                                                                 "registration_sha256": reg}})
    record: dict[str, Any] = {
        "schema": PREREG_SCHEMA, "registration_sha256": reg,
        "registration_blake3": _blake3.blake3(canonical_json(norm).encode("utf-8")).hexdigest(),
        "seal_sha256": s.sealed_sha256, "ensemble_sha256": s.ensemble_sha256, "question": form.question,
        "metrics": canonical_json(form.metrics), "form_sha256": form.sha256(), "registered_at": registered_at,
        "skill": skill_container(form),
        # 〔3-3b・仮-24〕封印の証拠の欄(値は公開する呼び手が埋める)と慣らしの規則(日付ではなく規則)
        "evidence": evidence_container(),
        "warmup": _warmup_record(),
    }
    body = {k: v for k, v in record.items() if k != "registered_at"}
    record["record_sha256"] = sha256_hex(body)
    return record, form


# ================================================================ 対の差 → salt_compare の形
def get_path(doc: Mapping[str, Any], path: str) -> Any:
    """``a.b.c`` の道筋で入れ子の辞書を引く(無ければ ``KeyError``)。"""
    cur: Any = doc
    for part in path.split("."):
        if isinstance(cur, Mapping) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(f"道筋 {path!r} が無い({part!r} で止まった)")
    return cur


def _metric_list(form: ExperimentForm) -> list[Mapping[str, Any]]:
    return [form.metrics["primary"], *form.metrics["secondary"]]


def paired_values(form: ExperimentForm, pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]
                  ) -> dict[str, dict[str, list[float]]]:
    """(基準の枝, 改変の枝) の checkpoints の JSON の組の列(salt の順)→ ``salt_compare.py --values`` の形。"""
    out: dict[str, dict[str, list[float]]] = {}
    for m in _metric_list(form):
        out[str(m["id"])] = {"base": [float(get_path(b, str(m["path"]))) for b, _a in pairs],
                             "arm": [float(get_path(a, str(m["path"]))) for _b, a in pairs]}
    return out


def metrics_spec(form: ExperimentForm, *, alpha: float = 0.05) -> dict[str, Any]:
    """``salt_compare.py --metrics`` の形(主=1 つ・副=Holm。向きの事前登録の印は確認の申込書だけ)。"""
    pre = form.kind == CONFIRM

    def one(m: Mapping[str, Any]) -> dict[str, Any]:
        d: dict[str, Any] = {"id": str(m["id"]), "path": str(m["path"]), "preregistered": bool(pre)}
        if m.get("direction") is not None:
            d["direction"] = str(m["direction"])
        return d

    return {"alpha": float(alpha), "family_size": None, "primary": one(form.metrics["primary"]),
            "secondary": [one(m) for m in form.metrics["secondary"]], "exploratory": []}


def pairs_status(n_pairs: int, *, one_sided: bool = False) -> dict[str, Any]:
    """対の数が R-71 の最低に届くか(両側 6 対・向きを事前登録した片側 5 対)。"""
    need = MIN_PAIRS_ONE_SIDED if one_sided else MIN_PAIRS_TWO_SIDED
    return {"n_pairs": int(n_pairs), "needed": need, "ok": int(n_pairs) >= need,
            "p_floor": (1.0 if one_sided else 2.0) / float(2 ** int(n_pairs)) if n_pairs > 0 else 1.0}


# ================================================================ 技量スコア(器だけ)
def skill_score(error: float, baseline_error: float) -> float:
    """CP14 の技量スコア=1 − 誤差/基準の誤差(気象と同じ。基準の誤差 0 は ``ValueError``)。"""
    if float(baseline_error) == 0.0:
        raise ValueError("基準の誤差が 0 の技量スコアは定義しない")
    return 1.0 - float(error) / float(baseline_error)


def skill_container(form: ExperimentForm) -> dict[str, Any]:
    """技量スコアの器(指標ごとに単純な基準 3 つの誤差と値の欄・**値は空**=答え合わせの段で埋める)。

    〔3-3b〕隣に生の点数の欄 ``raw``(fair CRPS・基準の CRPS・rank histogram・広がりと誤差の比・メンバーの数)と注を足した
    (値は空=``tools/instruments/skill_gauge.py`` が埋める)。"""
    return {"schema": SKILL_SCHEMA, "formula": "1 - error / baseline_error", "baselines": list(SKILL_BASELINES),
            "metrics": {str(m["id"]): {"error": None, "baseline_error": {b: None for b in SKILL_BASELINES},
                                       "skill": {b: None for b in SKILL_BASELINES},
                                       "raw": {"crps_fair": None, "baseline_crps": {b: None for b in SKILL_BASELINES},
                                               "rank_histogram": None, "spread_skill": None, "members": None}}
                        for m in _metric_list(form)},
            "raw_scores": list(RAW_SCORES), "error_measure": "crps",
            "spread_skill_correction": "sqrt((M + 1) / M)",
            "raw_note": ("技量スコアは元の点数が proper でも一般に proper でない(Gneiting & Raftery 2007 の式 (8) の注意)=複数の"
                         "予測の優劣は生の点数(fair CRPS)で決める")}


def evidence_container() -> dict[str, Any]:
    """〔3-3b・仮-24〕CP14 の封印の証拠の欄(手元の git の commit と公開リポへの push の記録・第三者の時刻印は無し)。値は空=
    公開する呼び手が埋める。ランの manifest の ``git_commit``・``git_dirty``・``git_diff_sha256`` は今の形のまま。"""
    return {"schema": EVIDENCE_SCHEMA, "kind": "git+push", "git_commit": None, "pushed_to": None, "pushed_at": None,
            "third_party_timestamp": False,
            "note": "手元の git の commit と公開リポへの push の記録を封印の時刻の証拠にする(第三者の時刻印は使わない=仮-24)"}


def _warmup_record() -> dict[str, Any]:
    from shibuya.engine.experiment import warmup as _WU

    return _WU.rule_record()


# ================================================================ 床の分布(〔3-3b〕(d) の 2)
def _num(doc: Mapping[str, Any], path: str) -> float | None:
    try:
        v = get_path(doc, path)
    except KeyError:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    return float(v)


def floor_values(form: ExperimentForm, aa_pairs: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]]
                 ) -> dict[str, dict[str, list[float | None]]]:
    """A/A の枝 2 本の組 (a, b) の列(各メンバーの T 以後の 2 本の checkpoints の JSON)→ 指標ごとの値と差 b − a。
    道筋が無い・数でない値は ``None``(差も ``None``)。"""
    out: dict[str, dict[str, list[float | None]]] = {}
    for m in _metric_list(form):
        a = [_num(x, str(m["path"])) for x, _y in aa_pairs]
        b = [_num(y, str(m["path"])) for _x, y in aa_pairs]
        out[str(m["id"])] = {"a": a, "b": b,
                             "diff": [None if (u is None or v is None) else v - u for u, v in zip(a, b)]}
    return out


def floor_summary(values: Mapping[str, Mapping[str, Sequence[float | None]]]) -> dict[str, dict[str, Any]]:
    """床の分布の要約(指標ごと: 対の数・平均・標準偏差(n − 1)・最小・最大・絶対値の最大・差 0 の割合・差の列)。"""
    out: dict[str, dict[str, Any]] = {}
    for mid, v in values.items():
        d = [float(x) for x in v.get("diff", ()) if x is not None]
        n = len(d)
        if n == 0:
            out[str(mid)] = {"schema": FLOOR_SCHEMA, "n": 0, "mean": None, "sd": None, "min": None, "max": None,
                             "abs_max": None, "zero_share": None, "diffs": list(v.get("diff", ()))}
            continue
        mean = sum(d) / n
        sd = (sum((x - mean) ** 2 for x in d) / (n - 1)) ** 0.5 if n > 1 else None
        out[str(mid)] = {"schema": FLOOR_SCHEMA, "n": n, "mean": mean, "sd": sd, "min": min(d), "max": max(d),
                         "abs_max": max(abs(x) for x in d), "zero_share": sum(1 for x in d if x == 0.0) / n,
                         "diffs": list(v.get("diff", ()))}
    return out
