"""engine.experiment.layer — 申込書をランに置く口(組み立て)・系 ``experiment``・manifest の節(第 3 期 3-3)。

- **申込書の受け渡し**: ``run_day`` の引数は増やさない(発注)。``cli.run`` が ``staged(form, branch=…)`` の中で ``run_day`` を
  呼び、組み立て(``engine.systems.build``)が ``current()`` で受け取って箱 ``Fixtures.experiment`` に申込書を置き、持ち主
  ``ExperimentLayer``(箱 ``Layers.experiment``・状態台帳の行 ``X``)を作る。申込書を渡さないランは ``current()`` が ``None``
  =持ち主を作らない=系 ``experiment`` は立たない(``SystemSpec.when``)=**結果は 1 バイトも変わらない**。
- **系 ``experiment``**(刻みの中の最初の系・日の頭の後): ``apply`` を 1 回呼ぶ(効かせる口は ``engine.experiment.apply`` の 1 つ)。
- **ランの種類**: 申込書を渡したランは ``counterfactual``(``engine.run_kind.decide``・``cli.run`` が決める)。設定の指紋には入れない
  (申込書の指紋は manifest の ``experiment`` の節=分岐が基準のランの状態のファイルから再開できるため)。
- **再開**: 申込書つきのランが書く状態のファイルの見出しに ``experiment``(申込書の指紋)を書く。再開のランの申込書が親と違う・
  親が申込書つきなのに申込書を渡さない、は止める(``check_resume``)。親が申込書なし(基準のラン)で申込書を渡すのは分岐
  (始まりが再開の時刻より前の決定は「期間の外」として記録して続ける)。
- **manifest**: 一番上の鍵の末尾 ``experiment``(申込書を渡さないランは ``null``)。設定=形式・申込書の指紋・種類・水準・T0・
  決定の名・登録と封印の指紋・分岐の T0・〔検収 M1〕メンバー(初期状態・モデル・偶然)と半分(explore/confirm)・A/A の枝の印/
  観測=効かせた/効かせていない改変の数と行・計器・T0 より前の再生の計器・4 つの確認の結果(分岐の道具が持ち主の口
  ``record_checks`` で置く)。
- **封印の入口**(〔親の判断 M1〕): 組み立てが ``entrance`` でランの seed の 3 つとモデルの札を申込書のアンサンブルと突き合わせ、
  探索の申込書が封印した半分の初期状態で回ろうとしたら止める(``engine.experiment.ensemble.entrance``)。
- **持ち主の守り**(〔検収 M4〕): 欄は組み立てで 1 回だけ置ける(付け替え・消去は ``AttributeError``)。4 つの確認の結果は
  持ち主の口 ``record_checks`` で 1 回だけ書く。
- 〔第 3 期 3-3b〕組み立ては分岐の指定の口 ``make_client``(3-3 の ``BranchSpec``=``BranchClient``・3-3b の ``SwitchSpec``=T からの
  切り替えの口 ``ReplaySwitch``)で LLM の口を包む。CP5-1 の点検(``checks.warn_start0``=始まり 0 の予期しない改変は警告と記録・
  拒まない)。manifest の設定に 4 欄を足した(末尾=``switch``・``start0``・``known_to_model``・``warmup``・3-3 の欄は変えない)。

未リサーチ(expedient): 系の位置(刻みの中の最初=日の頭の後)・申込書の受け渡しを文脈の変数にしたこと・「最初から」(始まり 0)
は 0 の刻みの頭で当てる(CP5-1 の「改変を当ててから経験を作る」順は未実装=宣言)。

逐次ループ宣言: なし(系は刻みに 1 回 ``apply`` を呼ぶだけ)。
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Final, Iterator, Mapping

from shibuya.core.time_consts import NS_PER_SECOND
from shibuya.engine.experiment import apply as _AP
from shibuya.engine.experiment.form import ExperimentForm

__all__ = [
    "Staged", "staged", "current", "entrance", "ExperimentLayer", "make_layer", "sys_experiment", "check_resume",
    "state_header",
    "manifest_fields", "MANIFEST_SCHEMA", "MANIFEST_CONFIG", "MANIFEST_OBSERVED",
]

MANIFEST_SCHEMA: Final[str] = "shibuya.engine.experiment/manifest/1"
#: manifest の ``experiment`` の子の鍵(設定・観測)。``engine.manifest_sections`` の表と同じ(試験が突き合わせる)。
MANIFEST_CONFIG: Final[tuple[str, ...]] = (
    "schema", "form_sha256", "kind", "level", "aa", "decisions", "t0_ns", "t0_step", "end_ns", "notice",
    "registration_sha256", "preregistration_sha256", "seal_sha256", "branch_t0_step", "member", "half", "aa_of",
    # 〔3-3b〕T からの切り替えの口・CP5-1 の点検・CP5-3 の混入の疑いの自己申告・慣らしの規則(事前登録=日付ではなく規則)
    "switch", "start0", "known_to_model", "warmup",
)
MANIFEST_OBSERVED: Final[tuple[str, ...]] = (
    "applied", "unapplied", "applied_rows", "unapplied_rows", "meter", "replay", "checks",
)


@dataclass(frozen=True)
class Staged:
    """``cli.run`` が組み立てに渡す物(申込書・分岐なら T0 までのテープの切り替えの指定・申込書のモデルの札)。"""

    form: ExperimentForm
    branch: Any = None
    model: str | None = None


_STAGED: contextvars.ContextVar[Staged | None] = contextvars.ContextVar("shibuya_experiment_staged", default=None)


@contextmanager
def staged(form: ExperimentForm, *, branch: Any = None, model: str | None = None) -> Iterator[Staged]:
    """この中で呼んだ ``run_day`` の組み立てが申込書を受け取る(出るときに外す)。``model`` は申込書のアンサンブルのモデルの札
    (札が 1 つなら省略可)。"""
    if not isinstance(form, ExperimentForm):
        raise TypeError("staged の form は ExperimentForm")
    st = Staged(form=form, branch=branch, model=model)
    tok = _STAGED.set(st)
    try:
        yield st
    finally:
        _STAGED.reset(tok)


def current() -> Staged | None:
    """組み立てが読む(申込書を渡さないランは ``None``)。"""
    return _STAGED.get()


def entrance(st: Staged | None, *, seed: Any, population_seed: Any, environment_seed: Any) -> Any:
    """〔親の判断 M1〕ランの入口の封印の検査(組み立てが世界を触る前に呼ぶ)。申込書の無いランは ``None``。メンバーと半分の組を返す。
    探索の申込書が封印した半分の初期状態で回ろうとしたら ``ValueError``(``engine.experiment.ensemble.entrance``)。"""
    if st is None:
        return None
    from shibuya.engine.experiment import ensemble as _EN

    return _EN.entrance(st.form, seed=seed, population_seed=population_seed, environment_seed=environment_seed,
                        model=st.model)


class ExperimentLayer:
    """申込書の持ち主(箱 ``Layers.experiment``・``hash_owners`` の鍵 ``experiment``・状態台帳の行 ``X``)。

    - ``form``・``t0_step``・``begin_step``・``end_step``・``total_steps``・``member``・``half``(定数)・``branch``(参照=T0 まで
      テープを再生する口・分岐でなければ ``None``)。
    - ``handle``(口 ``apply`` が触る世界の物の束と改変の控え ``handle.rec``)・``xchecks``(4 つの確認の結果=分岐の道具がランの
      後に持ち主の口 ``record_checks`` で 1 回だけ書く)は診断(軸 1 diag・軸 2 discardable)。控えを読むのはこのクラスのメソッドと
      口 ``apply`` だけ。
    - 〔検収 M4〕欄は 1 回だけ置ける(付け替え・消去は ``AttributeError``)=ランの途中で申込書を替えて ``staged``・
      ``check_resume`` を通らずに決定を変えることはできない。
    """

    def __init__(self, form: ExperimentForm, handle: _AP.WorldHandle, *, t0_step: int, begin_step: int,
                 end_step: int, total_steps: int, branch: Any = None, member: Any = None, half: str | None = None
                 ) -> None:
        self.form = form
        self.handle = handle
        self.branch = branch
        self.t0_step = int(t0_step)
        self.begin_step = int(begin_step)
        self.end_step = int(end_step)
        self.total_steps = int(total_steps)
        self.member = member
        self.half = half
        self.xchecks: Mapping[str, Any] | None = None

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__dict__:
            raise AttributeError(f"申込書の持ち主の欄 {name} は付け替えられない(組み立てで 1 回だけ置く)")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"申込書の持ち主の欄 {name} は消せない")

    def record_checks(self, summary: Mapping[str, Any]) -> None:
        """4 つの確認の結果の要約を 1 回だけ書く口(分岐の道具 ``branch.run_branch`` がランの後に呼ぶ)。"""
        if self.xchecks is not None:
            raise AttributeError("4 つの確認の結果は 1 回だけ書く")
        from types import MappingProxyType

        object.__setattr__(self, "xchecks", MappingProxyType(dict(summary)))

    def step(self, t_ns: int) -> int:
        """刻みの頭で口を 1 回(系 ``experiment`` が呼ぶ)。"""
        return _AP.apply(self.form, self.handle, int(t_ns))

    def targets(self) -> list[int]:
        """申込書の対象の店の番号(読むだけ・分岐の報告の実行の内訳)。"""
        return [int(x) for x in _AP.targets_of(self.form, self.handle).tolist()]

    def _not_started(self, finished: bool) -> list[dict[str, Any]]:
        """終わったランで始まりに届かなかった決定(期間の外=ランの終わりまでに始まらない)。控えを書き換えずに数える。"""
        if not finished or self.t0_step < self.total_steps:
            return []
        f, rec = self.form, self.handle.rec
        return [{"i": i, "decision": str(d["decision"]), "level": f.level, "t_ns": None, "step": None,
                 "reason": "期間の外(ランの終わりまでに始まらない)", "reason_key": "not_started"}
                for i, d in enumerate(f.content) if i not in rec.decided]

    def manifest(self, *, finished: bool = True) -> dict[str, Any]:
        """manifest の ``experiment``(設定 ``MANIFEST_CONFIG``・観測 ``MANIFEST_OBSERVED``)。"""
        from shibuya.engine.experiment import checks as _CK
        from shibuya.engine.experiment import warmup as _WU

        f, rec, branch = self.form, self.handle.rec, self.branch
        pre = f.preregistration
        unapplied = [dict(r) for r in rec.unapplied] + self._not_started(finished)
        switch = getattr(branch, "switch_record", None) if branch is not None else None
        return {
            "schema": MANIFEST_SCHEMA, "form_sha256": f.sha256(), "kind": f.kind, "level": f.level, "aa": f.is_aa,
            "decisions": [str(d["decision"]) for d in f.content], "t0_ns": int(f.start),
            "t0_step": int(self.t0_step), "end_ns": f.end, "notice": f.notice is not None,
            "registration_sha256": f.registration_digest(),
            "preregistration_sha256": None if pre is None else str(pre["registration_sha256"]),
            "seal_sha256": None if pre is None else str(pre["seal_sha256"]),
            "branch_t0_step": None if branch is None else int(branch.t0_step),
            "member": None if self.member is None else self.member.to_dict(), "half": self.half, "aa_of": f.aa_of,
            "switch": None if switch is None else switch(), "start0": _CK.start0_check(f),
            "known_to_model": list(f.known_to_model), "warmup": _WU.rule_record(),
            "applied": len(rec.applied), "unapplied": len(unapplied),
            "applied_rows": [dict(r) for r in rec.applied], "unapplied_rows": unapplied,
            "meter": dict(rec.tallies), "replay": None if branch is None else branch.replay_meter(),
            "checks": None if self.xchecks is None else dict(self.xchecks),
        }


def make_layer(st: Staged | None, *, world: Any, runner: Any, calendar: Any, events: Any, n_agents: int,
               step_seconds: int, steps_per_day: int, begin_step: int, end_step: int, total_steps: int,
               inherited: bool, bridge: Any = None, fleet: Any = None, entry: Any = None) -> ExperimentLayer | None:
    """組み立ての口: 申込書が無ければ ``None``(今の道)。分岐なら LLM の口を T0 で切り替える口に包む(``bridge.client``)。

    〔3-3b〕包む口は分岐の指定の ``make_client``(``BranchSpec``=3-3 の ``BranchClient``・``SwitchSpec``=``ReplaySwitch``)。
    CP5-1 の点検(始まり 0 の予期しない改変)は警告と記録だけ(拒まない)。"""
    if st is None:
        return None
    form = st.form
    from shibuya.engine.experiment import checks as _CK

    _CK.warn_start0(form)  # 〔3-3b〕CP5-1: 警告と記録(manifest の start0)・拒まない
    branch_client = None
    if st.branch is not None:
        if fleet is not None:
            raise ValueError("分岐(T0 までテープを再生)は艦隊(非同期の実 LLM)に未対応(3-3 の宣言)")
        if bridge is None:
            raise ValueError("分岐には LLM の口(bridge)が要る")
        branch_client = st.branch.make_client(bridge.client)
        bridge.client = branch_client
    step_ns = int(step_seconds) * NS_PER_SECOND
    handle = _AP.WorldHandle(
        world=world, runner=runner, calendar=calendar, events=events, step_seconds=int(step_seconds),
        steps_per_day=int(steps_per_day), n_agents=int(n_agents), begin_ns=int(begin_step) * step_ns,
        inherited=bool(inherited), rec=_AP.ApplyRecord(),
    )
    member, half = entry if entry is not None else (None, None)
    layer = ExperimentLayer(form, handle, t0_step=form.start_step(step_seconds), begin_step=begin_step,
                            end_step=end_step, total_steps=total_steps, branch=branch_client, member=member, half=half)
    _AP.apply(form, handle, int(begin_step) * step_ns, prime=True)  # 再開: 日の頭より前に要る暦の表だけ(行は書かない)
    return layer


def sys_experiment(ctx: Any, b: Any) -> None:
    """系 ``experiment``(刻みの中の最初の系): 申込書の改変を効かせる口 ``apply`` を 1 回呼ぶ。"""
    b.layers.experiment.step(ctx.t_ns)


# ================================================================ 再開
def state_header(layer: ExperimentLayer | None) -> dict[str, Any] | None:
    """状態のファイルの見出しに書く欄(申込書の無いランは ``None``=見出しは今のまま)。"""
    if layer is None:
        return None
    return {"form_sha256": layer.form.sha256(), "t0_step": int(layer.t0_step)}


def check_resume(st: Staged | None, header: Mapping[str, Any] | None) -> bool:
    """再開のランの申込書を親の状態のファイルの見出しと突き合わせる。親から引き継ぐなら ``True``。

    - 親が申込書つき: 同じ申込書でなければ止める(``ValueError``=腕を取り違えた再開)。
    - 親が申込書なし・今のランが申込書つき: 分岐(``False``)。
    """
    parent = None if header is None else header.get("experiment")
    if st is None:
        if parent:
            raise ValueError(f"親の状態は申込書つきのラン(申込書の指紋 {str(parent.get('form_sha256'))[:16]})。"
                             "申込書なしで再開しない")
        return False
    if parent:
        if parent.get("form_sha256") != st.form.sha256():
            raise ValueError("再開の申込書が親と違う(申込書の指紋が違う)")
        return True
    return False


# ================================================================ manifest
def manifest_fields(layer: ExperimentLayer | None, *, finished: bool = True) -> dict[str, Any] | None:
    """manifest の ``experiment``(申込書を渡さないランは ``None``)。中身は持ち主のメソッド ``manifest``。"""
    return None if layer is None else layer.manifest(finished=finished)
