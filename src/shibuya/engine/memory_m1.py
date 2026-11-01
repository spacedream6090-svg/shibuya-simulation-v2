"""engine.memory_m1 — 記憶 MR 第 6 期 6-5 の GPU の前に作る分(強さの式 M1・個人差・思い浮かぶ/見覚え・腕の切替口)。

正: 決定 10-12 §4-6(MR-0・MR1・MR4・人も記憶の一つ・MR8・MR10・MR12)・回答 10-12 の 6-2(段 M0〜M5)・計画 6-5 の行。
**全部 腕**(既定=今のまま=19 構成で不変)。MR10=各段をまず腕で入れて 1 つずつ測り、まとめて 1 回で既定にする。

腕(切替口=環境変数か CLI・組み立ての時に読む=記憶の器を作る ``MemoryLayer.enable_memory_store`` が読む)
    - ``--memory-model {m0,m1}``(``SHIBUYA_MEMORY_MODEL``): m0=今の式(刻みの単位の近似・+1)/ m1=ACT-R の折衷形(秒)。
    - ``--memory-cue {id,embed}``(``SHIBUYA_MEMORY_CUE``): id=その場の手がかり(ID の一致)/ embed=意味の手がかり
      (``engine.memory_embed``・``--memory-embed-model``)。
    - ``--memory-people {table,memory}``(``SHIBUYA_MEMORY_PEOPLE``): table=今の関係の層 / memory=人も記憶の一つ
      (同じ器・同じ式・上限なし・忘れる=消す=``engine.relations_people``)。
    - ``--memory-grain {each,day}``(``SHIBUYA_MEMORY_GRAIN``): 体の出来事を記録へ書く粒度(each=今=1 回 1 行/
      day=同じ記憶の行は日に 1 行=2-3 の 14.6 行/体/日を減らす案)。
    どの腕も記憶の器(``--memory-store events``)のランでだけ効く。器の無いラン(記憶 off を含む=〔検収 L6〕)で既定と違う
    腕を選ぶと組み立てで止める(黙って効かないランを作らない)。people=memory は model=m1 が前提(人の行の強さは M1 の式)。
    〔検収 L1〕腕の名と埋め込みのモデルの名と版(:func:`config_of`)は manifest の設定の節(``memory_summary.mr65_arms``)と
    設定の指紋(鍵 :data:`FP_KEY`)に入る(既定と違う腕のランだけ=既定のランの指紋と manifest の欄は前のまま)=再開で腕と
    埋め込みのモデルの取り違えを止める。

M1 の強さ(MR1 (b)+(d)・MR-0・System 1 の数=LLM には見せない)::

    B = ln( Σ_{j ≤ k} t_j^(−d) + [n > k]·(n − k)·(t_n^(1−d) − t_k^(1−d)) / ((1 − d)(t_n − t_k)) )
    A = B + β_種類

- 直近の ``k`` 回(:data:`K_RECENT`)は本当の時刻 ``t_j``(秒・その回から今まで)、古い ``n − k`` 回は最初の時刻 ``t_n``
  (寿命)から近似する(ACT-R の最適化学習の近似の折衷形=Petrov 2006 の式 (3)・式の写しは親の一次確認の候補)。
  ``n ≤ k`` なら正確な式 ``ln Σ t_j^(−d)`` そのもの。
- **時刻は秒で持ち +1 をやめる**(MR1)。``t`` が 0 にならないよう最短の符号化時間 :data:`T_MIN_S` で下から切る。正確な式では
  単位を変えると全部の強さが ``−d·ln(単位)`` だけ同じにずれ、境目 τ に吸収される(試験 ``test_m1_units_shift_all``)。
- ``d``=0.5(ACT-R 7 参照マニュアルの :bll の推奨値=R-87 §1-1)。人ごとに約 15% のばらつきを掛ける(MR8・Sense, Meijer &
  van Rijn 2018 の忘却率 .296±.046=変動係数 15.5%=R-68 §4-1。境目 τ は全員同じ)。
- ``β``(種類ごとの足す項・MR1 (d)): 出来事=重要度の項(``W_IMPORTANCE × 重要度``=M0 の score の w_i と同じ値)・人=無し・
  店=精度の項(店の行は器の外=今の ``sm_*``)。種類ごとの ``d``(MR12 (a)・形は研究に合わせ値は expedient の腕):
  :data:`KIND_SPECS`。
- 思い浮かぶ(MR4・MR5)= ``A ≥ τ``。見覚え = 親しみの種類(遅い=``D_FAMILIAR``)の強さに目の前の手がかり
  ``W_CUE`` を足すと ``τ`` を超える。忘れる(消す)= 見覚えにも ``FORGET_MARGIN`` だけ届かない(上限なしの腕だけ)。
- 言葉(MR-0): ``A ≥ τ + CLEAR_MARGIN`` は「はっきり」・``τ ≤ A`` は「うろ覚え」・見覚えだけは「見覚えがある」。
  浅い痕跡だけは「見たような気もする」(``engine.memory_trace``)。

**未リサーチ(expedient)**(つなぎの台帳の行 ``DOC-mr65-*``・値は感度の腕): ``K_RECENT``=3・``T_MIN_S``=1 秒・
``W_IMPORTANCE``=0.5(M0 の w_i)・``W_CUE``=1.0・``D_FAMILIAR``=0.35・``FORGET_MARGIN``=1.0・``CLEAR_MARGIN``=1.0・
境目 τ の仮の値(:func:`tau_from_m0`=M0 の境目と「n=1・初めての成功の行」が同じ時刻に越える値=人の記憶のデータでの較正は
**しない**=検証側)・ばらつきの切り(±3σ)。

人ごとの鍵(MR8): ``core.rng`` の Philox(用途名 ``memory.forgetting_rate``=母集団の側)を体の番号で引く。seed は
〔検収 M1〕組み立て(``engine.systems.build`` → ``MemoryLayer.enable_memory_store(population_seed=…)``)がランごとに母集団の
seed を渡す(プロセスの大域の値を持たない=前のランの値が残らない・10f S1)。manifest の ``m1.rate_seed`` に出る。

逐次ループ宣言(P4): なし(全部 配列演算。:func:`base_level` は行 × k の配列・:func:`forgetting_scale` は体の数の配列)。
"""

from __future__ import annotations

import math
import os
from types import MappingProxyType
from typing import Any, Final, Mapping, NamedTuple

import numpy as np

from shibuya.core.rng import k19_counter_array, philox_array, unit_float
from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_MINUTE

__all__ = [
    "MODEL_M0", "MODEL_M1", "MODELS",
    "CUE_ID", "CUE_EMBED", "CUES",
    "PEOPLE_TABLE", "PEOPLE_MEMORY", "PEOPLES",
    "GRAIN_EACH", "GRAIN_DAY", "GRAINS",
    "EMBED_MODELS", "DEFAULT_EMBED_MODEL",
    "MemoryArms", "arms", "set_arm", "arms_on", "check_arms", "config_of", "FP_KEY",
    "RATE_DOMAIN", "D_ACTR", "K_RECENT", "T_MIN_S", "CV_RATE", "RATE_CLIP_SIGMA", "W_IMPORTANCE", "W_CUE",
    "D_FAMILIAR", "FORGET_MARGIN", "CLEAR_MARGIN", "PERSON_KIND", "IMPRESSION_KIND", "KIND_SPECS", "KindSpec",
    "NO_TIME", "PARAMS",
    "forgetting_scale", "base_level", "exact_base_level", "touch_times", "tau_from_m0", "clarity_words",
    "recall_mask", "recognize_mask", "forget_mask", "WORD_CLEAR", "WORD_VAGUE", "WORD_FAMILIAR", "WORD_TRACE",
]

# ================================================================ 腕(切替口)
MODEL_M0: Final[str] = "m0"
MODEL_M1: Final[str] = "m1"
MODELS: Final[tuple[str, ...]] = (MODEL_M0, MODEL_M1)
CUE_ID: Final[str] = "id"
CUE_EMBED: Final[str] = "embed"
CUES: Final[tuple[str, ...]] = (CUE_ID, CUE_EMBED)
PEOPLE_TABLE: Final[str] = "table"
PEOPLE_MEMORY: Final[str] = "memory"
PEOPLES: Final[tuple[str, ...]] = (PEOPLE_TABLE, PEOPLE_MEMORY)
GRAIN_EACH: Final[str] = "each"
GRAIN_DAY: Final[str] = "day"
GRAINS: Final[tuple[str, ...]] = (GRAIN_EACH, GRAIN_DAY)
#: 埋め込みの腕のモデル(MR2 問い 2=Ruri-v3-30m と 130m を両方腕で)。``ngram-test`` は重みの要らない試験用の代わり
#: (文字の n-gram の袋=意味の手がかりではない・経路と計算量を測るためだけ=``engine.memory_embed``)。
EMBED_MODELS: Final[tuple[str, ...]] = ("ruri-v3-30m", "ruri-v3-130m", "ngram-test")
DEFAULT_EMBED_MODEL: Final[str] = "ruri-v3-30m"

_ENV: Final[Mapping[str, tuple[str, tuple[str, ...], str]]] = MappingProxyType({
    "model": ("SHIBUYA_MEMORY_MODEL", MODELS, MODEL_M0),
    "cue": ("SHIBUYA_MEMORY_CUE", CUES, CUE_ID),
    "people": ("SHIBUYA_MEMORY_PEOPLE", PEOPLES, PEOPLE_TABLE),
    "embed_model": ("SHIBUYA_MEMORY_EMBED_MODEL", EMBED_MODELS, DEFAULT_EMBED_MODEL),
    "grain": ("SHIBUYA_MEMORY_GRAIN", GRAINS, GRAIN_EACH),
})


def _from_env(key: str) -> str:
    var, allowed, default = _ENV[key]
    v = os.environ.get(var, default).strip().lower() or default
    if v not in allowed:
        raise ValueError(f"{var} は {allowed} のどれか(いま {v!r})")
    return v


#: 腕の値(切替口)。〔検収 M1〕人ごとの忘れる速さの seed はここに持たない(組み立てがランごとに母集団の seed を渡す)。
_STATE: dict[str, str] = {k: _from_env(k) for k in _ENV}
#: 〔検収 L1〕設定の指紋の鍵(既定と違う腕のランだけ足す=``engine.systems.build``)。
FP_KEY: Final[str] = "memory_mr65"


class MemoryArms(NamedTuple):
    """6-5 の腕のいまの値(組み立てが 1 回読む)。"""

    model: str
    cue: str
    people: str
    embed_model: str
    grain: str


def arms() -> MemoryArms:
    """いまの腕(既定は ``m0``・``id``・``table``・``ruri-v3-30m``・``each``)。"""
    return MemoryArms(_STATE["model"], _STATE["cue"], _STATE["people"], _STATE["embed_model"], _STATE["grain"])


def set_arm(key: str, value: str) -> None:
    """腕を選ぶ(CLI・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。"""
    if key not in _ENV:
        raise KeyError(f"6-5 の腕は {tuple(_ENV)} のどれか(いま {key!r})")
    _var, allowed, _d = _ENV[key]
    v = str(value)
    if v not in allowed:
        raise ValueError(f"--memory-{key.replace('_', '-')} は {allowed} のどれか(いま {v!r})")
    _STATE[key] = v


def arms_on() -> bool:
    """既定と違う腕が 1 つでもあるか(``cli.run`` のランの種類=結果を変える腕は「腕」に数える)。"""
    return any(_STATE[k] != _ENV[k][2] for k in ("model", "cue", "people", "grain"))


def check_arms(*, store_on: bool) -> MemoryArms:
    """組み立ての前の検査(器の無いランで既定と違う腕・people=memory で model=m0)→ いまの腕。違えば ``ValueError``。"""
    a = arms()
    if not store_on and arms_on():
        raise ValueError("6-5 の記憶の腕(--memory-model/--memory-cue/--memory-people/--memory-grain)は記憶の器のラン"
                         "(--memory on と --memory-store events)でだけ効く(黙って効かないランを作らない)")
    if a.people == PEOPLE_MEMORY and a.model != MODEL_M1:
        raise ValueError("--memory-people memory(人も記憶の一つ)は --memory-model m1 が前提(人の行の強さは M1 の式)")
    return a


def config_of(a: MemoryArms, *, row_caps: Mapping[str, int] | None = None) -> dict[str, Any]:
    """〔検収 L1〕腕の値 → 設定の節と設定の指紋に入れる値(既定の腕なら空=既定のランの指紋と manifest の欄は前のまま)。

    腕の名 4 つ(``model``・``cue``・``people``・``grain``)と、意味の手がかりの腕のときは埋め込みのモデルの名と版の同定
    (Ruri は重みの sha256=``engine.memory_embed.RURI_PINS``・``ngram-test`` は作りの名と次元)、人も記憶の一つの腕のときは
    種類ごとの行の上限(``row_caps``=``engine.memory_store.row_caps``)。
    """
    if not (a.model != _ENV["model"][2] or a.cue != _ENV["cue"][2] or a.people != _ENV["people"][2]
            or a.grain != _ENV["grain"][2]):
        return {}
    out: dict[str, Any] = {"model": a.model, "cue": a.cue, "people": a.people, "grain": a.grain}
    if a.cue == CUE_EMBED:
        from shibuya.engine.memory_embed import model_identity

        out["embed_model"] = a.embed_model
        out["embed_identity"] = model_identity(a.embed_model)
    if a.people == PEOPLE_MEMORY and row_caps is not None:
        out["row_caps"] = {str(k): int(v) for k, v in sorted(row_caps.items())}
    return out


# ================================================================ 定数(出典と expedient)
#: 人ごとの忘れる速さの乱数の用途名(母集団の側=``engine.run.POPULATION_RNG_DOMAINS``)。
RATE_DOMAIN: Final[str] = "memory.forgetting_rate"
#: 忘れる速さ d(ACT-R 7 参照マニュアルの :bll の推奨値=R-87 §1-1・Anderson & Schooler 1991 の値ではない)。
D_ACTR: Final[float] = 0.5
#: 直近の本当の時刻を持つ回数(expedient=R-87 §1-3 の例 k=3)。
K_RECENT: Final[int] = 3
#: 最短の符号化時間[秒](t=0 を避ける下の切り=expedient・感度の腕 0.05/1/60)。
T_MIN_S: Final[float] = 1.0
#: 忘れる速さの人ごとの変動係数(Sense, Meijer & van Rijn 2018 Front Educ 3:112: .296±.046=15.5%・R-68 §4-1)。
CV_RATE: Final[float] = 0.15
#: ばらつきの切り(±σ の数・expedient=Sense 2018 の範囲 .186〜.442 は −2.4σ〜+3.1σ)。
RATE_CLIP_SIGMA: Final[float] = 3.0
#: 出来事の足す項の重み(重要度 1 につき・M0 の score の w_i と同じ値=expedient)。
W_IMPORTANCE: Final[float] = 0.5
#: 見覚えの「目の前の手がかり」の重み(expedient・感度の腕 0.5/1/2)。
W_CUE: Final[float] = 1.0
#: 見覚え(親しみの種類=遅い)の d(MR4・MR12 の形=親しみは遅い減衰・値は expedient)。1 回だけ会った人(n=1・倍率 1)は
#: 思い浮かぶのが約 29 分・見覚えが約 9 日・忘れる(消す)のが約 5 か月(τ=M1 の仮の値・W_CUE=1・FORGET_MARGIN=1 のとき)。
D_FAMILIAR: Final[float] = 0.35
#: 忘れる(消す)=見覚えにもこの幅だけ届かない(expedient)。
FORGET_MARGIN: Final[float] = 1.0
#: 「はっきり」の幅(A ≥ τ + この値・expedient)。
CLEAR_MARGIN: Final[float] = 1.0
#: 人の行の種類(器の行の種類の番号=``engine.memory.EVENT_KINDS`` 1〜11 と店の行 12 の外)。
PERSON_KIND: Final[int] = 13
#: 印象の行の種類(M3 の器=意味の記憶・本段では書かない)。
IMPRESSION_KIND: Final[int] = 14
#: 「時刻なし」の印(直近の時刻の欄の空き・最初の時刻より前の経験=負の時刻と重ならない値)。
NO_TIME: Final[int] = int(np.iinfo(np.int64).min)

WORD_CLEAR: Final[str] = "はっきり"
WORD_VAGUE: Final[str] = "うろ覚え"
WORD_FAMILIAR: Final[str] = "見覚えがある"
WORD_TRACE: Final[str] = "見たような気もする"


class KindSpec(NamedTuple):
    """種類ごとの忘れる速さと足す項(MR1 (d)・MR12 (a))。``additive``: ``importance``・``none``。"""

    d: float
    additive: str


#: 記憶の種類ごとの表(MR12 (a)=形は研究に合わせ値は expedient の腕)。出来事(1〜11)・人・印象(M3 の器)。
KIND_SPECS: Final[Mapping[str, KindSpec]] = MappingProxyType({
    "episode": KindSpec(D_ACTR, "importance"),
    "person": KindSpec(D_ACTR, "none"),
    "impression": KindSpec(D_ACTR, "none"),
})

#: manifest に写す値(``memory_summary.memory_store.m1.params``)。〔検収 L4〕中の表も読み取り専用(``M1State.summary`` は
#: 普通の dict に写してから出す=写しを書き換えても表は変わらない)。
PARAMS: Final[Mapping[str, Any]] = MappingProxyType({
    "d": D_ACTR, "k_recent": K_RECENT, "t_min_s": T_MIN_S, "cv_rate": CV_RATE, "rate_clip_sigma": RATE_CLIP_SIGMA,
    "w_importance": W_IMPORTANCE, "w_cue": W_CUE, "d_familiar": D_FAMILIAR, "forget_margin": FORGET_MARGIN,
    "clear_margin": CLEAR_MARGIN,
    "kinds": MappingProxyType({k: MappingProxyType({"d": v.d, "additive": v.additive}) for k, v in KIND_SPECS.items()}),
})


def _plain(v: Any) -> Any:
    """読み取り専用の表 → 普通の dict の深い写し(manifest の JSON に出す)。"""
    if isinstance(v, Mapping):
        return {str(k): _plain(x) for k, x in v.items()}
    return v


# ================================================================ 人ごとのばらつき(MR8)
def forgetting_scale(seed: int | str, agent_keys: Any, *, cv: float = CV_RATE,
                     clip_sigma: float = RATE_CLIP_SIGMA) -> np.ndarray:
    """体の鍵の配列 → 忘れる速さの倍率 ``1 + cv·z``(z は標準正規=Philox の 2 語から Box-Muller・±``clip_sigma`` で切る)。

    同じ (seed, 鍵) は常に同じ値(体の数を増やしても既存の体の値は変わらない=カウンタの鍵)。
    """
    keys = np.atleast_1d(np.asarray(agent_keys, dtype=np.int64))
    if keys.size == 0:
        return np.zeros(0, dtype=np.float64)
    raw = philox_array(seed, RATE_DOMAIN, k19_counter_array(keys), words=2)
    u1 = 1.0 - unit_float(raw[:, 0])  # (0, 1]
    u2 = unit_float(raw[:, 1])
    z = np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * math.pi * u2)
    z = np.clip(z, -float(clip_sigma), float(clip_sigma))
    return 1.0 + float(cv) * z


# ================================================================ 強さ(MR1)
def base_level(recent_ns: Any, n: Any, first_ns: Any, now_ns: int, d: Any, *, t_min_s: float = T_MIN_S) -> np.ndarray:
    """行の配列 → 基底の強さ B(ACT-R の折衷形・秒)。``n == 0`` の行は −inf。

    Args:
        recent_ns: ``(行, k)`` の直近の回の時刻[ns](新しい順・空きは :data:`NO_TIME`)。有効な数 ``k_i ≤ min(n, k)``。
        n: 回数(行)。
        first_ns: 最初の回の時刻[ns](行)。
        now_ns: いまの時刻[ns]。
        d: 忘れる速さ(スカラーか行の配列・0 < d < 1)。
        t_min_s: 最短の符号化時間[秒](``t`` の下の切り)。
    """
    rec = np.atleast_2d(np.asarray(recent_ns, dtype=np.int64))
    nn = np.asarray(n, dtype=np.float64).reshape(-1)
    m = nn.size
    if rec.shape[0] != m:
        rec = rec.reshape(m, -1)
    fst = np.asarray(first_ns, dtype=np.int64).reshape(-1)
    dd = np.broadcast_to(np.asarray(d, dtype=np.float64), (m,)).astype(np.float64)
    if ((dd <= 0.0) | (dd >= 1.0)).any():
        raise ValueError("d は 0 < d < 1")
    tmin = float(t_min_s)
    valid = rec != NO_TIME
    t = np.where(valid, np.maximum((int(now_ns) - rec).astype(np.float64) / NS_PER_SECOND, tmin), 1.0)
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        terms = np.where(valid, t ** (-dd[:, None]), 0.0)
        recent_sum = terms.sum(axis=1)
        k_i = valid.sum(axis=1).astype(np.float64)
        # 有効な直近の時刻のうち一番古いもの(無ければ 0=式 (2) の近似 n·t_n^(−d)/(1−d) になる)
        t_k = np.where(k_i > 0, np.where(valid, t, -np.inf).max(axis=1), 0.0)
        t_n = np.maximum(np.maximum((int(now_ns) - fst).astype(np.float64) / NS_PER_SECOND, tmin), t_k)
        rest = np.maximum(nn - k_i, 0.0)
        one = 1.0 - dd
        gap = t_n - t_k
        approx = np.where(gap > 1e-9, (t_n ** one - t_k ** one) / (one * np.where(gap > 1e-9, gap, 1.0)),
                          t_n ** (-dd))
        total = recent_sum + rest * approx
        out = np.where(nn > 0, np.log(total), -np.inf)
    return out


def exact_base_level(times_ns: Any, now_ns: int, d: float, *, t_min_s: float = T_MIN_S) -> float:
    """正確な式 ``ln Σ t_j^(−d)``(試験の参照=全部の回の時刻)。"""
    ts = np.asarray(times_ns, dtype=np.int64).reshape(-1)
    if ts.size == 0:
        return float("-inf")
    t = np.maximum((int(now_ns) - ts).astype(np.float64) / NS_PER_SECOND, float(t_min_s))
    return float(np.log((t ** (-float(d))).sum()))


def touch_times(recent_ns: np.ndarray, rows: np.ndarray, t_ns: Any) -> None:
    """``recent_ns[rows]`` の直近の時刻に ``t_ns`` を足す(新しい順に 1 つずらす・空きは :data:`NO_TIME`)。その場で書く。

    呼び手は書く口の中だけ(``MemoryStore.remember``・人の行の口)。逐次ループ宣言: なし(行 × k の配列演算)。
    """
    r = np.asarray(rows, dtype=np.int64)
    if r.size == 0:
        return
    tt = np.broadcast_to(np.asarray(t_ns, dtype=np.int64), (r.size,))
    cur = recent_ns[r]
    shifted = np.empty_like(cur)
    shifted[:, 0] = tt
    shifted[:, 1:] = cur[:, :-1]
    recent_ns[r] = shifted


def tau_from_m0(tau_m0: float, *, d: float = D_ACTR, importance_ref: int = 2,
                w_importance: float = W_IMPORTANCE) -> float:
    """M1 の境目 τ の仮の値(expedient・人のデータで較正しない=検証側)。

    M0 の式 ``A = ln(n/(1−d)) − d·ln(L+1)``(L=分)で n=1 の行が τ_m0 を下回る時刻 L* と、M1 の式で「n=1・初めての成功の行」
    (重要度 ``importance_ref``=成功 1+初回 1=2)が同じ時刻に τ を下回るように選ぶ: ``τ = −d·ln(L*[秒]) + w·重要度``。
    """
    L_min = math.exp((math.log(1.0 / (1.0 - float(d))) - float(tau_m0)) / float(d)) - 1.0
    L_s = L_min * SECONDS_PER_MINUTE
    return -float(d) * math.log(L_s) + float(w_importance) * float(importance_ref)


# ================================================================ 思い浮かぶ/見覚え/忘れる(MR4・人も記憶の一つ)
def recall_mask(A: Any, tau: float) -> np.ndarray:
    """思い浮かぶ=``A ≥ τ``。"""
    return np.asarray(A, dtype=np.float64) >= float(tau)


def recognize_mask(A_fam: Any, tau: float, cue_present: Any, *, w_cue: float = W_CUE) -> np.ndarray:
    """見覚え=親しみの強さに目の前の手がかりを足すと ``τ`` を超える(手がかりの無い行は偽)。"""
    a = np.asarray(A_fam, dtype=np.float64)
    c = np.broadcast_to(np.asarray(cue_present, dtype=bool), a.shape)
    return c & (a + float(w_cue) >= float(tau))


def forget_mask(A_fam: Any, tau: float, *, w_cue: float = W_CUE, margin: float = FORGET_MARGIN) -> np.ndarray:
    """忘れる(消す)=手がかりがあっても見覚えに ``margin`` だけ届かない(上限なしの腕だけが使う)。"""
    return np.asarray(A_fam, dtype=np.float64) + float(w_cue) < float(tau) - float(margin)


def clarity_words(A: Any, tau: float, *, margin: float = CLEAR_MARGIN) -> np.ndarray:
    """強さ → 言葉(MR-0): ``A ≥ τ + margin`` は「はっきり」・``A ≥ τ`` は「うろ覚え」・それ以外は空文字。"""
    a = np.asarray(A, dtype=np.float64)
    return np.where(a >= float(tau) + float(margin), WORD_CLEAR, np.where(a >= float(tau), WORD_VAGUE, ""))


# ================================================================ 状態(器の子の持ち主 mem_layer.memory_store.m1)
def _kind_d(kind: np.ndarray) -> np.ndarray:
    """行の種類 → 種類ごとの d(:data:`KIND_SPECS`)。"""
    k = np.asarray(kind, dtype=np.int64)
    return np.where(k == PERSON_KIND, KIND_SPECS["person"].d,
                    np.where(k == IMPRESSION_KIND, KIND_SPECS["impression"].d, KIND_SPECS["episode"].d))


def _kind_beta(kind: np.ndarray, importance: np.ndarray) -> np.ndarray:
    """行の種類 → 足す項 β(出来事=``W_IMPORTANCE × 重要度``・人と印象=0)。"""
    k = np.asarray(kind, dtype=np.int64)
    episode = (k >= 1) & (k < PERSON_KIND - 1)  # 1〜11(12=店の行は器の外)
    return np.where(episode, W_IMPORTANCE * np.asarray(importance, dtype=np.float64), 0.0)


class M1State:
    """M1 の強さの状態(記憶の器の子の持ち主 ``mem_layer.memory_store.m1``・状態台帳の腕の行 ``M0M``=腕 memory-model)。

    中身: 行ごとの直近 ``k`` 回の時刻(``_t_ns``・``(行, k)`` の i8・新しい順・空き :data:`NO_TIME`)と体ごとの忘れる速さの
    倍率(``_scale``・f8)。書くのは器の書く口(``MemoryStore.remember``・``seed_people``・上限なしの腕の消す口と広げる口)
    だけ=このクラスの ``place``・``clear``・``seed_rows``・``grow`` を器の口の中から呼ぶ。欄の付け替えは ``__setattr__`` が
    落とす。逐次ループ宣言: なし(配列演算)。
    """

    LEDGER_ARM: str = "memory-model"
    __slots__ = ("n", "k", "tau", "t_min_s", "seed", "_t_ns", "_scale", "_m1_stats")

    def __init__(self, n_agents: int, size: int, *, tau: float, seed: int | str, k: int = K_RECENT,
                 t_min_s: float = T_MIN_S) -> None:
        if int(k) < 1 or float(t_min_s) <= 0.0:
            raise ValueError("k ≥ 1・t_min_s > 0")
        self.n = int(n_agents)
        self.k = int(k)
        self.tau = float(tau)
        self.t_min_s = float(t_min_s)
        self.seed = seed
        self._t_ns = np.full((int(size), self.k), NO_TIME, dtype=np.int64)
        self._scale = forgetting_scale(seed, np.arange(self.n, dtype=np.int64))
        #: 計数(行 M0X)。〔検収 M2〕``grown``=器の行の幅を倍にした回・``forgotten``=忘れた(見覚えにも届かない)行を消した数・
        #: ``evicted_by_a``=種類の上限で思い浮かぶ強さ A の一番低い行を消した数(``cleared`` はその和)。
        self._m1_stats: dict[str, int] = {"touched": 0, "new_rows": 0, "cleared": 0, "seeded": 0, "grown": 0,
                                          "forgotten": 0, "evicted_by_a": 0}

    def __setattr__(self, name: str, value: Any) -> None:
        if not hasattr(self, name):
            object.__setattr__(self, name, value)
            return
        raise AttributeError(f"M1 の状態の欄 {name} は付け替えられない(書く口は器の remember・seed_people)")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"M1 の状態の欄 {name} は消せない")

    @property
    def scale(self) -> np.ndarray:
        """体ごとの忘れる速さの倍率(読み取り専用の view)。"""
        v = self._scale.view()
        v.flags.writeable = False
        return v

    @property
    def recent_ns(self) -> np.ndarray:
        """行ごとの直近の時刻(読み取り専用の view)。"""
        v = self._t_ns.view()
        v.flags.writeable = False
        return v

    # ------------------------------------------------------------------ 器の書く口の中から呼ぶ
    def place(self, g: np.ndarray, new: np.ndarray, t_ns: Any) -> None:
        """書いた行 ``g`` に今の回を足す(新しい行=``new`` は前の回を消してから)。"""
        gg = np.asarray(g, dtype=np.int64)
        nw = np.asarray(new, dtype=bool)
        if bool(nw.any()):
            self._t_ns[gg[nw]] = NO_TIME
            self._m1_stats["new_rows"] += int(np.count_nonzero(nw))
        touch_times(self._t_ns, gg, t_ns)
        self._m1_stats["touched"] += int(gg.size)

    def clear(self, g: np.ndarray, *, reason: str = "forgotten") -> None:
        """消した行の時刻を空に(``reason``: ``forgotten``=忘れた・``evicted_by_a``=種類の上限で A の一番低い行)。"""
        if reason not in ("forgotten", "evicted_by_a"):
            raise ValueError(f"消した理由は forgotten・evicted_by_a のどれか(いま {reason!r})")
        gg = np.asarray(g, dtype=np.int64)
        self._t_ns[gg] = NO_TIME
        self._m1_stats["cleared"] += int(gg.size)
        self._m1_stats[reason] += int(gg.size)

    def seed_rows(self, g: np.ndarray, last_ns: Any) -> None:
        """開始前の経験の行(最初の関係)に最後の回の時刻だけを置く(古い回は近似=最初の時刻と回数から)。"""
        gg = np.asarray(g, dtype=np.int64)
        self._t_ns[gg] = NO_TIME
        self._t_ns[gg, 0] = np.broadcast_to(np.asarray(last_ns, dtype=np.int64), (gg.size,))
        self._m1_stats["seeded"] += int(gg.size)

    def grow(self, n_agents: int, old_rows: int, new_rows: int) -> None:
        """上限なしの腕: 体あたりの行の幅を広げる(体の範囲の並びを保つ)。"""
        t = self._t_ns.reshape(int(n_agents), int(old_rows), self.k)
        out = np.full((int(n_agents), int(new_rows), self.k), NO_TIME, dtype=np.int64)
        keep = min(int(old_rows), int(new_rows))
        out[:, :keep] = t[:, :keep]
        object.__setattr__(self, "_t_ns", out.reshape(-1, self.k))
        self._m1_stats["grown"] += 1

    # ------------------------------------------------------------------ 読み口
    def strength(self, g: Any, agent: Any, now_ns: int, n: Any, first_ns: Any, kind: Any, importance: Any, *,
                 familiar: bool = False) -> np.ndarray:
        """行 ``g``(体 ``agent``)の強さ A=B+β(``familiar`` は見覚えの d=``D_FAMILIAR`` で)。空の行(n=0)は −inf。"""
        gg = np.asarray(g, dtype=np.int64).reshape(-1)
        ag = np.broadcast_to(np.asarray(agent, dtype=np.int64), gg.shape)
        kd = np.asarray(kind, dtype=np.int64).reshape(-1)
        d = (np.full(gg.size, D_FAMILIAR) if familiar else _kind_d(kd)) * self._scale[ag]
        B = base_level(self._t_ns[gg], np.asarray(n).reshape(-1), np.asarray(first_ns).reshape(-1), int(now_ns), d,
                       t_min_s=self.t_min_s)
        return B + _kind_beta(kd, np.asarray(importance).reshape(-1))

    def summary(self, used: np.ndarray) -> dict[str, Any]:
        """manifest ``memory_summary.memory_store.m1``(観測): 値・人ごとの倍率の分布・計数。"""
        s = self._scale
        k_valid = (self._t_ns[np.asarray(used, dtype=bool)] != NO_TIME).sum(axis=1) if self._t_ns.size else np.zeros(0)
        return {
            "params": {**_plain(PARAMS), "tau": round(self.tau, 6)},
            "rate_seed": self.seed if isinstance(self.seed, (int, str)) else str(self.seed),
            "scale": {"mean": round(float(s.mean()), 6) if s.size else None,
                      "sd": round(float(s.std()), 6) if s.size else None,
                      "min": round(float(s.min()), 6) if s.size else None,
                      "max": round(float(s.max()), 6) if s.size else None},
            "rows_by_known_times": {str(i): int(np.count_nonzero(k_valid == i)) for i in range(self.k + 1)},
            "counts": dict(self._m1_stats),
        }
