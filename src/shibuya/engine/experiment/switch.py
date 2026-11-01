"""engine.experiment.switch — T からの切り替えの口(第 3 期 3-3b・CP5-2 の完成)と 4 つの確認の (c)(d) の分け(仮-24)。

決定 10-12 §4-5 CP5-2 (c): 状態の保存は日の境目のまま、改変はその日の好きな時刻 T に当てる。**T までは基準のランの録画(テープ)
を再生して同じ動きにし(LLM を呼ばない)、T からだけ実 LLM を使う**。本段の「実 LLM」は**仮のモデル**(mock か古典=ランの方策・
試験では注入した口)。T までの一致は R-71 の 4 つの確認で毎回確かめる(``branch.run_branch``)。

**切り替えの口 ``ReplaySwitch``**(``branch.BranchClient`` の上に足した形=T より前の答え方は 3-3 と同じ):

- **T は計算のまとめの窓の頭**(``window_head_step``): 3-2 の窓の待ち行列の窓の頭はランの始め(通しの 0)から幅 W ずつ。T が窓の頭で
  なければ ``ValueError``(止める)。T1 の世界の事象は刻みの事象だけ(刻みの頭=いつも窓の頭)なので、切り替わるのは T 以後の最初の
  刻み(``ExperimentForm.start_step`` と同じ切り上げ)。W は基準のランの manifest の ``batching.width_s``(無ければ刻みの幅)。
- **再生の箱に刻みの外の物を残さない**(1-2 の検収 M1=刻みの中の物が刻みをまたいで残ると full-hash が変わった教訓)。守りは 2 つ:
  - **守りの本体=艦隊で録ったテープを拒む**(``tape_crossing``): テープに T より前に出して後で届く行(艦隊で録った到着待ちの行=
    ``deferred`` か ``observed_tick`` ≥ 0)があれば、再生の到着待ち(プロジェクトの語の「再生の箱」=状態台帳 O96
    ``run_day.replay_inbox``)に T をまたいで物が残る・同期の答えでは基準を再現できない=**切り替えを拒む**(艦隊の分岐は 6-7=
    ``DOC-cf33-branch-fleet``)。分岐のランでは橋は口の道(``observed_tick``=−1)を通るので、O96 に物は入らない(作りから空)。
    〔3-3b 検収 L1〕O96 を T の刻みで読む口は無い(系 ``experiment`` の読む欄は系の表で ``layers.experiment`` だけ=系の表は
    この段の範囲の外)=(b) の条件に O96 は入れず、この守りを本体とする(宣言)。
  - **口の中の箱の計器**(``_box``=今の刻みに再生した答え(鍵 → 文の文字列)だけ・刻みが替わったら空にする): 刻みをまたいで残った
    数 ``box_carried`` と切り替えの刻みに残っていた数 ``box_at_switch`` は、空にしてから数えるので**作りから 0**(箱はどこからも
    読まれない=答えはテープか仮のモデルが返す)。空にする処理の退化を捕まえる計器で、(b) は両方 0 を条件にする(負の対照=空に
    しない写しは (b) が落ちる・ランの動きは変わらない)。
- **T からの口**: 既定はランの口(mock・古典)そのもの。``SwitchSpec.live``(口 → 口)を渡すと T からだけその口が答える(実 LLM の
  代わりの注入=試験の非決定の口)。モデルの札(``model``)と決定論か(``deterministic``)は manifest の ``experiment.switch`` に書く。
  決定論かは ① ``SwitchSpec.deterministic``(``run_branch`` の引数)② 口の宣言(〔3-3b 検収 L2〕属性 ``deterministic`` が
  真偽の値のときだけ=注入した決定論の口が自分で宣言する)③ 札(``DETERMINISTIC_MODELS``)の順で決める。宣言の無い注入の口は
  非決定のまま(既定は変えない)。
- 保存の間隔は日の境目のまま(変えない)。

**(c)(d) の分け**(仮-24・R-117 §1-2・§6-1): 実 LLM は A/A の枝 2 本でも食い違う(R-71 §1-5)。

- (d) を「決定論の確認」(``determinism``=T より前の一致と、mock・古典の仮のモデルでは A/A の枝 2 本が厳密に同じ・T からの口が
  ランの口そのものなら A/A の枝の final が基準と同じ)と「床の分布」(``ensemble.floor_values``・``floor_summary``=T 以後の A/A の
  対の差の分布)に分ける。非決定の口(札が mock・古典でない)は厳密一致を求めず、床の分布を出す。
- (c) は改変の枝の最初の食い違い(A/A の枝 a との比べ)と A/A の枝 2 本の最初の食い違いの刻みの差を比べる(``vs_aa``)。

未リサーチ(expedient): 決定論の札の一覧(mock・古典)・箱の単位(刻み)・艦隊で録ったテープを拒むこと(到着待ちの行を 1 行でも
含めば拒む)・「改変の枝が先」の読み(刻みの差 > 0)。

逐次ループ宣言: ``tape_crossing`` はテープの行数ぶん(ランの外で 1 回・配列演算)。口は 1 呼=1 回(箱を空にするのは刻みが替わる
ときだけ)。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, ClassVar, Final, Mapping

import numpy as np

from shibuya.engine.experiment.branch import BranchClient, BranchSpec

__all__ = [
    "SWITCH_SCHEMA", "DETERMINISTIC_MODELS", "DETERMINISM_ATTR", "SwitchSpec", "ReplaySwitch", "window_head_step",
    "tape_crossing", "model_label", "is_deterministic", "declared_determinism", "vs_aa", "determinism",
]

SWITCH_SCHEMA: Final[str] = "shibuya.engine.experiment/switch/1"
#: 決定論の確認(厳密一致)をかける仮のモデルの札(同じ入力に同じ答え=mock と古典の方策)。
DETERMINISTIC_MODELS: Final[tuple[str, ...]] = ("mock", "classical")
#: 〔検収 L2〕注入した口が決定論を宣言する属性の名(値が真偽のときだけ宣言とみなす)。
DETERMINISM_ATTR: Final[str] = "deterministic"


def window_head_step(t0_ns: int, window_ns: int, step_ns: int) -> int:
    """T0 が計算のまとめの窓の頭か(窓の頭=ランの始め 0 から ``window_ns`` ずつ)を確かめ、切り替わる刻み(T0 以後の最初の
    刻み=切り上げ)を返す。窓の頭でなければ ``ValueError``。窓の幅は刻みの幅の約数(3-2 の ``WIDTHS_S``)。"""
    t0, w, s = int(t0_ns), int(window_ns), int(step_ns)
    if w <= 0 or s <= 0 or s % w:
        raise ValueError(f"窓の幅 {w} ns は刻みの幅 {s} ns の約数(3-2 の窓の待ち行列)")
    if t0 < 0 or t0 % w:
        raise ValueError(f"T0({t0} ns)が計算のまとめの窓の頭でない(窓の頭は 0 から {w} ns ずつ=3-2 の窓の待ち行列)")
    return -(-t0 // s)


def tape_crossing(tape: Any, t0_step: int) -> dict[str, int]:
    """テープの行のうち T0 より前に出した艦隊の到着待ちの行(``deferred`` か ``observed_tick`` ≥ 0)の数と、そのうち T0 以後に
    届く行(``observed_tick`` ≥ T0=再生の到着待ちに T0 をまたいで残る物)の数。"""
    steps = np.asarray(tape.column("tick"), dtype=np.int64)
    if steps.size == 0:
        return {"fleet_rows_before_t0": 0, "rows_crossing_t0": 0}
    deferred = np.asarray(tape.column("deferred"), dtype=np.int64)
    observed = np.asarray(tape.column("observed_tick"), dtype=np.int64)
    before = steps < int(t0_step)
    fleet = before & ((deferred != 0) | (observed >= 0))
    crossing = fleet & (observed >= int(t0_step))
    return {"fleet_rows_before_t0": int(fleet.sum()), "rows_crossing_t0": int(crossing.sum())}


def model_label(client: Any) -> str:
    """口の札(古典の方策=``classical``・mock=``mock``・ほかは ``source`` の欄か型の名)。"""
    from shibuya.engine.classical import ClassicalPolicy
    from shibuya.llm.mock import MockLLM

    if isinstance(client, ClassicalPolicy):
        return "classical"
    if isinstance(client, MockLLM):
        return "mock"
    src = getattr(client, "source", None)
    return str(src) if isinstance(src, str) and src else type(client).__name__


def is_deterministic(model: str, declared: bool | None = None) -> bool:
    """決定論の確認をかけるか(宣言があれば宣言・無ければ札が ``DETERMINISTIC_MODELS`` にあるか)。"""
    return bool(declared) if declared is not None else str(model) in DETERMINISTIC_MODELS


def declared_determinism(port: Any) -> bool | None:
    """〔検収 L2〕口が自分で宣言した決定論(属性 ``DETERMINISM_ATTR`` が真偽の値のときだけ・無ければ ``None``=宣言なし)。"""
    v = getattr(port, DETERMINISM_ATTR, None)
    return v if isinstance(v, bool) else None


@dataclass(frozen=True)
class SwitchSpec(BranchSpec):
    """T からの切り替えの指定(``BranchSpec`` に窓と仮のモデルを足した形)。``cli.run`` の ``experiment_branch`` で渡す。

    - ``t0_ns``・``window_ns``・``step_ns``: T0 の時刻と計算のまとめの窓の幅と刻みの幅(``t0_step`` は窓の頭の検査の後の刻み)。
    - ``model``: 仮のモデルの札(``None``=T からの口から ``model_label`` で決める)。``deterministic``: 決定論の宣言(``None``=
      口の宣言(属性 ``deterministic``)から・それも無ければ札から)。
    - ``live``: T からの口を作る関数(ランの口 → 口・``None``=ランの口そのもの)。比べと指紋には入らない。
    """

    t0_ns: int = 0
    window_ns: int = 0
    step_ns: int = 0
    model: str | None = None
    deterministic: bool | None = None
    live: Callable[[Any], Any] | None = field(default=None, compare=False, repr=False)

    def make_client(self, client: Any) -> "ReplaySwitch":
        return ReplaySwitch(client, self)

    def record(self, *, model: str, deterministic: bool, deterministic_by: str | None = None) -> dict[str, Any]:
        """manifest の ``experiment.switch``(設定)。``deterministic_by``=決定論を決めた出どころ(〔検収 L2〕spec・port・label)。"""
        out = {"schema": SWITCH_SCHEMA, "t0_ns": int(self.t0_ns), "t0_step": int(self.t0_step),
               "window_ns": int(self.window_ns), "step_ns": int(self.step_ns), "model": str(model),
               "deterministic": bool(deterministic), "post_is_run_client": self.live is None,
               "before_t0": "tape", "box": "step"}
        if deterministic_by is not None:
            out["deterministic_by"] = str(deterministic_by)
        return out


class ReplaySwitch(BranchClient):
    """T からの切り替えの口(T より前=テープの再生(古典の方策は状態を進めて食い違いを数える)・T から=仮のモデル)。

    再生の箱 ``_box`` は今の刻みに再生した答え(鍵 → 文)だけを持ち、刻みが替わると空にする(``_box_reset``)。箱の計器
    (``box_carried``・``box_at_switch``)は空にしてから数えるので作りから 0=空にする処理の退化を捕まえる計器(〔検収 L1〕)。
    刻みの外へ物を持ち越さない守りの本体は、艦隊で録ったテープ(到着待ちの行)を組み立てで拒むこと(``tape_crossing``)。
    〔検収 L8〕箱の計器の数は読み取り専用の属性(中身は ``_meters``=口のメソッドだけが書く)。
    """

    METER_NAMES: ClassVar[tuple[str, ...]] = BranchClient.METER_NAMES + (
        "box_peak", "box_carried", "box_repeats", "box_at_switch", "first_live_step")

    def __init__(self, live: Any, spec: SwitchSpec) -> None:
        super().__init__(live, spec)
        self.spec = spec
        cross = tape_crossing(self.replay.tape, self.t0_step)
        if cross["fleet_rows_before_t0"]:
            raise ValueError(
                f"テープに T0 より前に出して後で届く行(艦隊で録った到着待ちの行)が {cross['fleet_rows_before_t0']} 行・うち T0 を"
                f"またぐ行 {cross['rows_crossing_t0']}: 再生の箱に刻みの外の物が残る(同期の答えでは再現できない)=艦隊の分岐は"
                "6-7 まで未対応")
        self.cross = cross
        self.post = live if spec.live is None else spec.live(live)
        self.model = model_label(self.post) if spec.model is None else str(spec.model)
        # 〔検収 L2〕決定論の出どころ: ① 指定(run_branch の引数)② 口の宣言(属性 deterministic=真偽)③ 札
        port_decl = declared_determinism(self.post)
        if spec.deterministic is not None:
            declared, self.deterministic_by = spec.deterministic, "spec"
        elif port_decl is not None:
            declared, self.deterministic_by = port_decl, "port"
        else:
            declared, self.deterministic_by = None, "label"
        self.deterministic = is_deterministic(self.model, declared)
        self._box: dict[tuple[int, int, int, str], str] = {}
        self._box_step = -1
        self._meters.update({"box_peak": 0, "box_carried": 0, "box_repeats": 0, "box_at_switch": None,
                             "first_live_step": None})

    box_peak = property(lambda self: self._meters["box_peak"], doc="1 つの刻みの箱の最大の数")
    box_carried = property(lambda self: self._meters["box_carried"],
                           doc="刻みをまたいで箱に残った数(空にしてから数える=作りから 0・空にする処理の退化の計器)")
    box_repeats = property(lambda self: self._meters["box_repeats"], doc="同じ刻みに同じ鍵を再生した数")
    box_at_switch = property(lambda self: self._meters["box_at_switch"],
                             doc="切り替えの刻みに箱に残っていた数(作りから 0・切り替えの刻みに届く前は None)")
    first_live_step = property(lambda self: self._meters["first_live_step"], doc="最初に仮のモデルが答えた刻み")

    def _box_reset(self, step: int) -> None:
        """刻みが替わったら箱を空にする(刻みの外へ持ち越さない)。"""
        self._box = {}
        self._box_step = int(step)

    def _box_enter(self, step: int) -> None:
        """刻みが替わったら箱を空にし、空にした後に残った物(前の刻みの鍵)を数える=作りから 0(空にする処理の退化を捕まえる)。"""
        if step == self._box_step:
            return
        self._box_reset(step)
        m = self._meters
        m["box_carried"] += sum(1 for k in self._box if k[1] != step)
        if step >= self.t0_step and m["box_at_switch"] is None:
            m["box_at_switch"] = len(self._box)

    def complete(self, request: Any) -> Any:
        step = int(request.tick)
        self._box_enter(step)
        m = self._meters
        if step < self.t0_step:
            resp = super().complete(request)
            key = (int(request.agent_id), step, int(request.wake_class), request.prompt_hash)
            if key in self._box:
                m["box_repeats"] += 1
            self._box[key] = str(resp.text)
            m["box_peak"] = max(m["box_peak"], len(self._box))
            return resp
        if m["first_live_step"] is None:
            m["first_live_step"] = step
        m["n_live"] += 1
        return self.post.complete(request)

    def replay_meter(self) -> dict[str, Any]:
        """T より前の再生の計器(3-3 の欄)+切り替えの計器(manifest の ``experiment.replay``=観測)。"""
        m = super().replay_meter()
        m.update({"model": self.model, "deterministic": bool(self.deterministic), "box_peak": int(self.box_peak),
                  "box_carried": int(self.box_carried), "box_repeats": int(self.box_repeats),
                  "box_at_switch": self.box_at_switch, "first_live_step": self.first_live_step,
                  "fleet_rows_before_t0": int(self.cross["fleet_rows_before_t0"]),
                  "rows_crossing_t0": int(self.cross["rows_crossing_t0"])})
        return m

    def switch_record(self) -> dict[str, Any]:
        """manifest の ``experiment.switch``(設定)。"""
        return self.spec.record(model=self.model, deterministic=self.deterministic,
                                deterministic_by=self.deterministic_by)


# ================================================================ (c)(d) の分け
def vs_aa(branch_coarse: Mapping[str, Any], aa_coarse: Mapping[str, Any]) -> dict[str, Any]:
    """(c) 改変の枝の最初の食い違い(A/A の枝 a との比べ)と A/A の枝 2 本の最初の食い違いの刻みの差(A/A − 改変)。"""
    b, a = branch_coarse.get("first_step"), aa_coarse.get("first_step")
    gap = None if a is None or b is None else int(a) - int(b)
    if b is None:
        status = "改変の枝は A/A の枝と食い違わない"
    elif a is None:
        status = "A/A の枝 2 本は食い違わない(床 0)=改変の枝の食い違いは床の外"
    elif gap is not None and gap > 0:
        status = "改変の枝が A/A の枝 2 本より先に食い違う"
    else:
        status = "改変の枝の食い違いは A/A の枝 2 本と同時か後(床に埋もれる)"
    return {"branch_first_step": b, "aa_first_step": a, "gap_steps": gap, "status": status}


def determinism(*, model: str, deterministic: bool, twins_vs_base: tuple[Any, ...], twins_before_t0: Any,
                aa_exact: bool, final_equals_base: bool, expect_base: bool) -> dict[str, Any]:
    """(d) の 1=決定論の確認。

    - 決定論の札(mock・古典): A/A の枝 2 本が厳密に同じ(全 checkpoint と final)・T からの口がランの口そのもの(``expect_base``)
      なら A/A の枝の final が基準と同じ。T より前の一致は (b) が受け持つ(ここでは写すだけ)。
    - 非決定の札: 厳密一致を求めない。T より前に A/A の枝 2 本が同じこと(``twins_before_t0``=checkpoint が無ければ ``None``)。
    """
    pre = None if any(v is None for v in twins_vs_base) else all(bool(v) for v in twins_vs_base)
    if deterministic:
        ok: bool | None = bool(aa_exact) and (bool(final_equals_base) if expect_base else True)
    else:
        ok = None if twins_before_t0 is None else bool(twins_before_t0)
    return {"model": str(model), "deterministic": bool(deterministic), "twins_vs_base_before_t0": pre,
            "twins_before_t0": twins_before_t0, "aa_exact": bool(aa_exact), "aa_exact_required": bool(deterministic),
            "final_equals_base": bool(final_equals_base),
            "final_equals_base_required": bool(deterministic and expect_base), "ok": ok}
