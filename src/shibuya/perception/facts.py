"""perception.facts — 知覚の事実 ``Percept``(第 1 期 1-2 知覚の分離)。

正典
- 決定 10-12 §1-13「何に気づいたか(知覚の中身)」と「それを渡す形(文章・項目・画像)」を分けて持つ。知覚の約束の出力は
  構造のある事実にし、文章はその描き方の 1 つにする。
- 決定 10-12 §1-6「係数で持たない」(現実で測られた割合は係数として掛けず、検証に使う)。
- 決定 10-12 §4-4 CT2(目の向き・心の向き)・回答 10-13b §4-2(起床 3 種=近接入替・被注視・傍受と知人出現は起床の条件では
  なく知覚の事実。値は空で始め、値を作る仕組みは空間の段)。
- 口の約束 ``docs/design/v2-foundation-contracts-2026-10-13.md`` の「1-2 知覚の分離」。
- 先例(R-113 §6): UE の AI Perception の ``FAIStimulus``(誰が・どこで・どの感覚で=欄の形だけ参考・強さの係数は持たない)・
  SOTOPIA(共有の記録 → 見る人ごとの絞り込み → 文の 3 段)。コードは写していない。

形
- ``Percept``: 1 体・1 刻みの知覚の事実(凍結の dataclass)。``perception.renderer.Renderer.perceive`` が状態から作り、
  ``Renderer.render_percept`` が B0〜B6 の文に描く(描き方の 1 つ)。判断の入力(1-8 の ``DecisionPort.choose(ctx, …)``)にも
  同じ物を渡す(``PerceptCarrier``)。
- その場(セルと刻みで決まる事実=同じセルの全員で同じ)は ``SceneView``、時刻の見方は ``TimeView``(同じ刻みの全員で同じ)。
- **欄だけ(値は空=None)**: ``EMPTY_FIELDS`` の 10 欄(〔6-5〕``heard_referents`` を足した)。値を作る仕組みは後の段(目の向き・心の向き=CT2、持ち物と道具=1-7、
  被注視・傍受・顔ぶれの変化・知人の出現=空間の段、本人の予想=1-8)。``None`` は「仕組みがまだ無い(未計測)」の意味で、
  空の tuple(=測ったが無かった)とは分ける。
- ``Percept`` は刻みの中の一時(``engine.systems.boxes.TickScratch`` の欄 ``percepts``・状態台帳の行 ``P``=軸 1 no・
  軸 2 discardable)。刻みをまたいで持たない(描画は別の刻みの ``Percept`` を受けない=``Renderer.render_percept``)。

係数(1-2 の〔決定〕=係数を消すと結果が動くかを最初に測り、動かなければ消す)
- 歩きスマホの負荷の係数(``p_notice`` の 0.46)と、看板の注視の ``p_see × 活動の乗数``(乗数の表・通話 0.49 など)を
  1-2 で消した。既定のランではどちらも効く道が無かった(歩きスマホの旗を立てる口が無い・乗数の表は既定で全部 1.0)=
  係数を 1.0 にした byte-check が 19 構成で結果不変(記録 ``docs/bench/analysis/wallbounce-1012/p12/README.md``)。
  消した値はパターン台帳 §10 の検証専用(親が設計書に書く)。気づきの差は目の向き・心の向きの仕組み(CT2)から出す。

層契約: 標準ライブラリだけ(perception の他のモジュールも NumPy も import しない=描画と p_notice の両方から読める)。
逐次ループ宣言(P4): なし(欄の数ぶんの表を作るのは起動時と manifest の 1 回)。
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Final, Protocol, runtime_checkable

__all__ = [
    "PERCEPT_SCHEMA",
    "EventRef",
    "OBJECT_KINDS",
    "SOUND_KINDS",
    "NEARBY_CHANGE_KINDS",
    "EMPTY_FIELDS",
    "SeenObject",
    "SeenPerson",
    "Sound",
    "TimeView",
    "BodyView",
    "SelfView",
    "IntentView",
    "WakeView",
    "SceneView",
    "Percept",
    "PerceptCarrier",
    "PerceptDrawing",
    "with_prediction",
    "percept_fields",
    "percept_manifest",
]

#: 形の版(欄を足したり意味を変えたりしたら上げる。manifest の ``percept.schema`` に出る)。〔第 6 期 6-5〕/2=欄
#: ``heard_referents``(話し手が指した相手の見えない ID・空の欄)を末尾に足した。
PERCEPT_SCHEMA: Final[str] = "shibuya.perception/percept/2"

#: 出来事の記録の行の目印(``engine.events.log.EventId`` と同じ形=``(t_ns, seq)``)。層契約(perception は engine を
#: import できない)のため形を写す。一致は ``tests/perception/facts/test_percept_schema.py`` が見る。
EventRef = tuple[int, int]

#: 見えた物の種類。``poi``=店・施設(id は POI の番号)/ ``landmark``=目印と駅の出入口(名だけ=id は -1)/
#: ``signage``=看板(注視のゲートを通った看板の POI)。
OBJECT_KINDS: Final[tuple[str, ...]] = ("poi", "landmark", "signage")
#: 音の種類(今は街の騒音の段だけ。会話の傍受は ``heard_speech`` の欄=値は空間の段)。
SOUND_KINDS: Final[tuple[str, ...]] = ("noise",)
#: 〔第 3 期 3-5〕周りの変化 ``Percept.nearby_change`` の種類。``loud_sound``=大きな音に注意が向く(③ 群の System 1 の反応・
#: 器だけ=値は空・空間の段 3 で入る・``engine.body.system1``)。顔ぶれの変化(入った人・出た人)の種類は空間の段で足す。
NEARBY_CHANGE_KINDS: Final[tuple[str, ...]] = ("loud_sound",)

#: 欄だけ用意して値は空(None)で始める欄(回答 10-13b §4-2・計画 1-2)。
EMPTY_FIELDS: Final[tuple[str, ...]] = (
    "eye_dir", "mind_dir", "belongings", "tool_state",
    "watched_by", "heard_speech", "nearby_change", "acquaintance_seen", "prediction", "heard_referents",
)


@dataclass(frozen=True, slots=True)
class SeenObject:
    """見えた物 1 つ(id・種類・距離・向き)。今はセルの代表点から見える物=距離と向きは空間の段で入る(None)。"""

    id: int
    kind: str
    distance_m: float | None = None
    direction: int | None = None
    #: 表示の名(描き方の材料。店の名・目印の名)。
    name: str = ""


@dataclass(frozen=True, slots=True)
class SeenPerson:
    """見えた人 1 人(id・向き・行為)。並びは描画の近接行と同じ(焦点が先頭・ほかは距離の順か id の順)。"""

    id: int
    #: 相手の向き(空間の段で入る=今は None)。
    direction: int | None
    #: 相手の今の行為(``agents.state.Activity`` のコード)。
    action: int
    #: 距離[m](下限 0.1=描画の単一ランキングの視角に使う値と同じ)。
    distance_m: float
    #: 知人か(関係の記憶か構築時の知人の表)。
    acquainted: bool


@dataclass(frozen=True, slots=True)
class Sound:
    """聞こえる音 1 つ(段)。"""

    kind: str
    #: 段(``noise``=騒音の段=``templates.NOISE_STAGE_VOCAB`` の索引)。
    stage: int


@dataclass(frozen=True, slots=True)
class TimeView:
    """時刻の見方(同じ刻みの全員で同じ)。

    ``tod_s``=その日の中の秒(世界内日時の時・分・秒から)・``day_kind``=暦の日の種類(``engine.calendar.SimCalendar.day_kind``=
    ``weekday``/``saturday``/``sunday``・祝日は日曜の行。暦の口が無い描画は None)。``hour``・``minute``=5 分に切り捨てた時刻
    (B3 の表記)。``weather``・``daylight``・``heat``=天候・日照・暑さの語(W13 の行か環境の過程と同じ規則)。
    """

    tod_s: int
    day_kind: str | None
    band5: int
    hour: int
    minute: int
    weather: str
    daylight: str
    heat: str


@dataclass(frozen=True, slots=True)
class BodyView:
    """体の段(空腹・疲れ・暑さ)。``hunger``・``fatigue``・``thermal`` は内受容の値(0〜10)、``*_stage`` は閾値
    ``renderer.INTERO_UP_EDGES`` を何本越えたか(0〜3)。"""

    hunger: int
    fatigue: int
    thermal: int
    hunger_stage: int
    fatigue_stage: int
    thermal_stage: int


@dataclass(frozen=True, slots=True)
class SelfView:
    """自分の状態(種別・所持金・手がふさがっているか・今の行為)。持ち物の中身は ``Percept.belongings``(空=1-7)。"""

    kind: int
    money: int
    hands_full: bool
    activity: int


@dataclass(frozen=True, slots=True)
class IntentView:
    """いまの意図(行為のコード・対象の種類=``agents.state.IntentKind``・対象の番号)。"""

    action: int
    target_kind: int
    target: int


@dataclass(frozen=True, slots=True)
class WakeView:
    """起きた理由と直前の結果(B6 の材料)。

    ``reason``=起床の条件(``WakeCondition`` の値か文言)・``inviter``=話しかけた人(無ければ None)・``result``=直前の
    結果のコード・``result_known``=直前の結果があるか・``last_action``=直前に試みた行動の語(None=今の行為で代用)。
    観測値(失敗のときだけ意味を持つ): ``cheapest_price``=いるセルで最も安い品・``next_open_hour``=次の開店の時・
    ``closed_note``=名指しの店の閉店の 1 句(Q25・名指しで歩かずに失敗した直後だけ)。
    """

    reason: int | str
    inviter: int | None
    result: int
    result_known: bool
    last_action: str | None
    cheapest_price: int = 0
    next_open_hour: int | None = None
    closed_note: str = ""


@dataclass(frozen=True, slots=True)
class SceneView:
    """その場(セルと刻みで決まる事実=同じセルの全員で同じ・刻みごとに 1 回作る)。

    ``objects``=セルの代表点から見える店・目印(看板は体ごとの注視なので ``Percept.seen_objects`` の側)・``signage_poi``=
    そのセルの看板の POI(無ければ -1)・``crowd_stage``=密度の段(LOS の索引)・``flow``=流れの段・``sounds``=音の段・
    ``salient``=顕著な出来事(世界過程が作る文の材料)・``near_items``=近景の項目(待ち行列の文の材料)・``field_hash``=
    B4 の欄の指紋(起床条件 (i) と描画のキャッシュの鍵)・``with_signage``=見える物+看板。
    """

    cell: int
    in_area: bool
    objects: tuple[SeenObject, ...]
    signage_poi: int
    crowd_stage: int
    flow: int
    sounds: tuple[Sound, ...]
    salient: tuple[str, ...]
    near_items: tuple[str, ...]
    field_hash: int
    #: ``objects`` に看板(``signage``)を足した物(看板の注視のゲートを通った体の ``Percept.seen_objects``・看板の無い
    #: セルでは ``objects`` と同じ)。セルと刻みで 1 回だけ作る。
    with_signage: tuple[SeenObject, ...] = ()


@dataclass(frozen=True, slots=True)
class Percept:
    """1 体・1 刻みの知覚の事実(構造のある事実。文は ``Renderer.render_percept`` が描く)。

    事実の欄: ``seen_objects``(見えた物)・``seen_people``(見えた人)・``sounds``(音の段)・``time_view``(時刻の見方)・
    ``body``(体の段)・``self_view``(自分の状態)・``intent``(意図)・``wake``(起きた理由と直前の結果)・``memories``
    (想起した記憶の行=記憶の層の行・想起の口が無いランは None)・``signage_shown``(看板の注視のゲートを通ったか=看板の無い
    セルでは真)・``watched_n``(被注視の人数=構築の時に渡す配列の値・ランでは渡さない=0)・``scene``(その場)。
    欄だけ(値は None): ``EMPTY_FIELDS``。
    """

    agent_id: int
    #: 通しの刻みの番号(T)。
    step: int
    #: 通しの時刻[ns](世界内日時と時計の原点の差=``core.types.SimTime``)。
    t_ns: int
    cell: int
    self_view: SelfView
    seen_objects: tuple[SeenObject, ...]
    seen_people: tuple[SeenPerson, ...]
    sounds: tuple[Sound, ...]
    time_view: TimeView
    body: BodyView
    wake: WakeView
    intent: IntentView | None
    memories: tuple[Any, ...] | None
    signage_shown: bool
    watched_n: int
    scene: SceneView
    # ---- 欄だけ(値は空=None・EMPTY_FIELDS) ----
    #: 目の向き(CT2・16 方位の索引の予定)。
    eye_dir: int | None = None
    #: 心の向き(CT2・何に注意を向けているか)。
    mind_dir: Any = None
    #: 持ち物(1-7 の道具の台帳)。
    belongings: tuple[Any, ...] | None = None
    #: 道具の状態(1-7)。
    tool_state: Any = None
    #: 誰が見ているか(人の id の列=空間の段の視線)。
    watched_by: tuple[int, ...] | None = None
    #: 聞こえる会話(1-8b の ``Utterance`` の出来事の目印=``EventRef`` の列)。
    heard_speech: tuple[EventRef, ...] | None = None
    #: 周りの顔ぶれの変化(入った人・出た人)と周りの変化(種類 ``NEARBY_CHANGE_KINDS``=〔3-5〕大きな音 ``loud_sound``)。
    nearby_change: Any = None
    #: 知人の出現(人の id の列)。
    acquaintance_seen: tuple[int, ...] | None = None
    #: 本人の予想(1-8 で埋める=「今の観測」と並べて判断の入力に載せる)。
    prediction: Any = None
    #: 〔第 6 期 6-5・MR6 の 2〕聞こえた発話が指した相手の ID(見えない欄=描画しない・聞き手の記憶を引く手がかり)。
    #: ``(発話の出来事の目印, 指した相手の id の組)`` の列。値を作る口(話し手の発話の形)は会話の段(6-4 C1)と空間の段の後。
    heard_referents: tuple[tuple[EventRef, tuple[int, ...]], ...] | None = None


@runtime_checkable
class PerceptCarrier(Protocol):
    """1-8 の ``DecisionPort.choose(ctx, candidates)`` の ``ctx`` が満たす形(知覚の事実を持つ)。

    今の観測は ``ctx.percept``・本人の予想は ``ctx.percept.prediction``(並べて載せる=回答 10-13b §4-2 の 3)。驚くか・
    何をするか・よく考えるかは判断の側が決める(エンジンは並べて載せるだけ=10-03 §7)。
    """

    @property
    def percept(self) -> Percept: ...


@runtime_checkable
class PerceptDrawing(Protocol):
    """知覚の事実の描き方(文章はその 1 つ=``perception.renderer.Renderer``)。"""

    def draw(self, percept: Percept) -> str: ...


def with_prediction(p: Percept, prediction: Any) -> Percept:
    """本人の予想を並べた ``Percept`` の写し(1-8 の口が使う)。"""
    return dataclasses.replace(p, prediction=prediction)


def percept_fields() -> tuple[str, ...]:
    """``Percept`` の欄の名(宣言順)。"""
    return tuple(f.name for f in dataclasses.fields(Percept))


def percept_manifest() -> dict[str, Any]:
    """manifest の ``percept``(計器): 形の版・欄の数と名・空の欄の一覧。"""
    names = percept_fields()
    return {
        "schema": PERCEPT_SCHEMA,
        "n_fields": len(names),
        "fields": list(names),
        "empty_fields": list(EMPTY_FIELDS),
        "n_empty_fields": len(EMPTY_FIELDS),
    }
