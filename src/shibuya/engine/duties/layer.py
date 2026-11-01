"""engine.duties.layer — 店の仕事を働く人の体へ(開閉店・補充(品出し)・廃棄)の持ち主と系 ``duties``(第 6 期 6-6 ② 第 1 部・
腕 ``--duties arm``・既定 off)。

正: 決定 10-12 §1-5(② 他の人の仕事をエンジンが代わりにしている=働く人のエージェントへ・組織は開始時点の現実のデータ)・§1-4
(人の手続きはコードに書かない=住人の知識から出す)・§1-1 CP6 と §2 の 2(世界の変化は人の行動の結果・まだ人の行動で作れない
変化はエンジン規則でつなぐ=conf 宣言つき・カバー率を台帳へ)・§4-1 CA1(シフトは週ごと=カレンダー 3)・計画 6-6・回答 2-1
(GPU の前に仮のモデルで)。口の約束 1-3(出来事の記録)・1-5(権利台帳=読むだけ)・1-8(候補の口 J0)・10-13b §0-3(仮採用の形)。
記録 ``docs/bench/analysis/wallbounce-1012/duties1/README.md``(検収の直し=§13)。

持ち主 :class:`DutiesLayer`(道筋 ``duties``・状態台帳の腕の行 ``DU*``=腕 arm のランだけ持ち主がある=既定のランの 2 つの
ハッシュと状態のファイルは不変)。世界過程の 3 つ(開閉店 ``OpeningProcess``・補充 ``ShelfRestockProcess``・廃棄
``WasteCollectionProcess``)の ``duties`` に挿され、挿された過程は**その店の雇用の行を持つ体が店のセルに居て起きている店を
エンジンが代わりにしない**(:meth:`DutiesLayer.staffed_now`=開閉と補充で同じ判定=〔検収 M1・M4〕)。そうでない店は今の conf
宣言つきのつなぎ(開閉は REPLACEMENT conf 0.5・補充は 10:00・売れ残りは 05:00)。開始の刻みの最初の設定もエンジン。

流れ(系 ``duties``=刻みの中・カレンダー 2 の系の後・記憶の系の前。知る → 気づく → 選ぶ → 変わる):

1. **知る**: 店の決まり(営業時間)は、その店の雇用の行(権利台帳の 体 → 店)を持つ体だけが店の決まりの口
   (``engine.duties.knowledge.ShopRules``=W7 の営業時間の表のその日の行・申込書の決定を含む・出どころの印つき)で引ける。
   エンジンは表を読んで開け閉めしない。
2. **気づく**: 〔検収 M1〕その店の雇用の行を持つ体のうち、店のセルに居て、起きていて、その刻みに主の判断の呼びが無い体の雇用の
   行の順で最初の 1 人(1 店 1 刻みの判断は 1 人まで=仲裁)が、(a) 店の決まりで ``SHOP_LEAD_MINUTES`` 分後に営業なのに閉まって
   いる/``SHOP_LEAD_MINUTES`` 分後に休みなのに開いている(区切りの ``SHOP_LEAD_MINUTES`` 分前から、決まりと店の状態が食い違う間)、
   (b) 店の中の気づき=棚が減った(棚の残りが補充点の下・営業中・〔検収 M2〕バックヤードに在庫がある=本人は在庫を知っている・
   補充の評価の刻み ``RESTOCK_STEP_MINUTES`` ごと=System 1 の刺激)、(c) その店の雇用の行の体が閉めた店に売れ残りがある
   (閉店の作業)。
3. **選ぶ**(J0・仮のモデル): (a) 店を開ける/店を閉める/まだ・(b) 棚に補充する/接客する/待つ・(c) 売れ残りを捨てる/まだ。
4. **変わる**: 開け閉め=``resolve.request_open_close``(権利は台帳に聞き、無くても止めない=CP3)+ActualLog ``SCHEDULED``・
   補充=``ShelfRestockProcess.restock_by_staff``(今の役割行動と同じ量)・廃棄=``WasteCollectionProcess.bin_by_staff``(05:00 の
   つなぎと同じ式)。出来事は族 ``仕事`` の本人の語(原因=判断の呼び・``origin``=店の決まりの出どころの印)。
5. **主の判断の役割語**: 判断の口が役割語「補充」「開閉店」で答えたら(``LLMBridge.role_sink``)、その体が雇用の行を持つ店の
   セルに居れば同じ刻みに本人の行動として実行する(居なければ起きない=数える)。〔検収 L7〕補充は営業中で棚が補充点の下のとき
   だけ(気づきと同じ条件)。仮のモデルの主の判断は役割語を出さない(実 LLM の段で効く)。
6. **計器**(合否なし・manifest の ``duties``): 本人とエンジンのつなぎの開けた/閉めた/補充した/捨てた数(カバー率)を、
   〔検収 M1〕行動した体(つなぎは店の担当の表の体)の雇用の行の出どころ(W21c の担当/丸振り)と 〔検収 M3〕店の決まりの出どころ
   (W7 の src)で分ける・開店と閉店の遅れの分布(出どころ別)・棚の減った/空の店 × 分・労働時間の行と店の決まりの幅の外の開け閉め
   (読むだけで止めない=記録)。

記録(CT0 の 5): 族 ``仕事`` の語は全部本人の語(原因は判断の呼び ``LlmCall``=テープの形の call_id・選んだ候補の源と番号・役割語の
道は主の判断の call_id)。監査 :func:`audit_causes` は発行した判断の呼びの控え(腕の行 ``DUQ``)と突き合わせる。

仲裁(``ARBITRATION``=宣言): その刻みに主の判断の呼びのあった体・寝ている体には候補を出さない(次に条件がそろった刻みに出す)。

**未リサーチ(expedient)**(記録 §仮採用・つなぎの台帳 ``DOC-du1-*``): 候補を出す条件(店の決まりの区切りの
``SHOP_LEAD_MINUTES`` 分前から)・棚の気づきの形(補充点と評価の刻み=今の補充の過程の値)・閉店の後の片付けは無い・
雇用の行の体が居ない店はエンジン・仮のモデルは一様・1 店 1 刻みの判断は雇用の行の順で最初の 1 人・労働時間=雇用の行の店の
セルに起きて居た分。

逐次ループ宣言(新設・P4): 系 ``duties`` は (a) 雇用の行の体が居て候補がある店の数ぶん(1 店あたり判断 ≤ 2)・(b) その刻みの
主の判断の役割語の数ぶん。体の数に比例する Python のループは無い(雇用の行の体が店に居るかは配列演算)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Iterable, Mapping, Sequence

import numpy as np

from shibuya.agents.state import Activity
from shibuya.core.time_consts import MINUTES_PER_DAY, MINUTES_PER_HOUR, NS_PER_SECOND, SECONDS_PER_MINUTE
from shibuya.engine import resolve as R
from shibuya.engine.calendar3.layer import labor_params
from shibuya.engine.decision.port import Candidate, DecisionContext
from shibuya.engine.duties import arm as _ARM
from shibuya.engine.duties import port as _P
from shibuya.engine.duties.knowledge import UNKNOWN, ShopRules, origin_mark, rules_line
from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import Event, LlmCall
from shibuya.engine.processes.goods_flow import RESTOCK_STEP_MINUTES, WASTE_TO_BIN_MINUTE
from shibuya.world.processes.records import DEVIATION_CODES, DeviationVocab

__all__ = [
    "SCHEMA", "CONFIG_KEYS", "OBSERVED_KEYS", "ARBITRATION", "SHOP_LEAD_MINUTES", "W_UNLOCK", "W_LOCK", "W_RESTOCK",
    "W_DISCARD", "PERSON_WORDS", "WORD_PURPOSES", "ORIGINS", "DutiesLayer", "sys_duties", "manifest_fields",
    "audit_causes", "issued_key",
]

#: manifest の ``duties`` の形の版。
SCHEMA: Final[str] = "shibuya.engine.duties/2"

# ---- 出来事の記録の語(族 仕事=1-3 の語彙表の末尾に足した語・どれも本人の語) ----
W_UNLOCK = V.word(V.FAMILY_DUTY, "開けた")
W_LOCK = V.word(V.FAMILY_DUTY, "閉めた")
W_RESTOCK = V.word(V.FAMILY_DUTY, "補充した")
W_DISCARD = V.word(V.FAMILY_DUTY, "捨てた")
#: 本人の判断の語(原因は LlmCall でなければならない=負の対照の監査)。
PERSON_WORDS: Final[frozenset[str]] = frozenset({W_UNLOCK, W_LOCK, W_RESTOCK, W_DISCARD})
#: 本人の語 → 合う判断の種類(監査の突き合わせ)。
WORD_PURPOSES: Final[Mapping[str, frozenset[int]]] = MappingProxyType({
    W_UNLOCK: frozenset({_P.P_SHOP}), W_LOCK: frozenset({_P.P_SHOP}), W_RESTOCK: frozenset({_P.P_SHELF}),
    W_DISCARD: frozenset({_P.P_WASTE}),
})
#: 仲裁の規則(宣言=実装は :meth:`DutiesLayer.run_step`)。
ARBITRATION: Final = MappingProxyType({
    "main_first": "その刻みに主の判断の呼びのあった体には候補を出さない(次に条件がそろった刻みに出す)",
    "awake": "寝ている体には候補を出さない(雇用の行の体が店で寝ているだけの店はエンジンのつなぎ)",
    "one_per_store": "1 店 1 刻みの判断は 1 人まで=雇用の行の順で最初の、店に居て起きていて主の判断の無い体",
    "role_words": "主の判断の役割語(補充・開閉店)は同じ刻みに本人の行動として実行する(雇用の行の店に居るときだけ)",
})
#: 候補を出す条件の幅[分]=店の決まりの区切りの前(この分の後に営業/休みなのに逆の状態なら候補を出す=区切りのこの分前から、
#: 食い違う間ずっと)。
#: **未リサーチ(expedient)**(つなぎの台帳 ``DOC-du1-shop-window``)。
SHOP_LEAD_MINUTES: Final[int] = 15
#: 〔検収 M1〕雇用の行の出どころ(差し替えの世界の初期の行の表 W21c の店の担当/今の丸振り)・店に雇用の行が無い。
ORIGIN_W21C, ORIGIN_RR, ORIGIN_NONE = "w21c", "round_robin", "none"
ORIGINS: Final[tuple[str, ...]] = (ORIGIN_NONE, ORIGIN_W21C, ORIGIN_RR)

_CODE_SCHEDULED: Final[int] = DEVIATION_CODES[DeviationVocab.SCHEDULED]
_SHOP_PROCESS_ID: Final[str] = "store_opening"
#: カバー率の項目(本人/つなぎの計器の鍵の 2 つ目)。廃棄は行(店 × 棚)で数える。
_ITEMS: Final[tuple[str, ...]] = ("unlock", "lock", "restock", "discard_rows")

#: manifest の ``duties`` の設定の子と観測の子(``engine.manifest_sections`` の混ざった辞書)。
CONFIG_KEYS: Final[tuple[str, ...]] = (
    "schema", "arm", "port", "rules", "arbitration", "bridges", "provisional")
OBSERVED_KEYS: Final[tuple[str, ...]] = (
    "meter", "decisions", "shop", "shelf", "waste", "coverage", "delay_minutes", "labor_over", "role_words",
    "common_knowledge", "calls")

#: 発行した判断の呼びの控えの詰め方(刻み 22 ビット・体 20 ビット・通し番号−SERIAL_BASE 21 ビット)。
_ISS_T_SHIFT, _ISS_A_SHIFT = 41, 21
_ISS_MAX_T, _ISS_MAX_A, _ISS_MAX_S = 1 << 22, 1 << 20, 1 << 21


def issued_key(step: int, agent: int, serial: int) -> int:
    t, a, c = int(step), int(agent), int(serial) - _P.SERIAL_BASE
    if not (0 <= t < _ISS_MAX_T and 0 <= a < _ISS_MAX_A and 0 <= c < _ISS_MAX_S):
        raise ValueError(f"判断の呼びの控えの範囲の外: 刻み {t}・体 {a}・通し番号 {serial}")
    return (t << _ISS_T_SHIFT) | (a << _ISS_A_SHIFT) | c


def _signed_gap(minute: int, mark: int) -> int:
    """``minute`` − ``mark`` を 1 日の中で前後半日に巻き戻した差[分]。"""
    return (int(minute) - int(mark) + MINUTES_PER_DAY // 2) % MINUTES_PER_DAY - MINUTES_PER_DAY // 2


def first_per_store(stores: np.ndarray, agents: np.ndarray, eligible: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """〔検収 M1〕雇用の行(店の順・店の中は台帳の行の順)のうち ``eligible`` の行の、店ごとの最初の行。返り値は
    (店, 体, 行の番号)。"""
    idx = np.flatnonzero(np.asarray(eligible, dtype=bool))
    if idx.size == 0:
        z = np.zeros(0, dtype=np.int64)
        return z, z, z
    st = np.asarray(stores, dtype=np.int64)[idx]
    uniq, first = np.unique(st, return_index=True)
    rows = idx[first]
    return uniq.astype(np.int64), np.asarray(agents, dtype=np.int64)[rows], rows


class DutiesLayer:
    """店の仕事の持ち主(状態台帳の腕の行 ``DU*``)。"""

    LEDGER_ARM: Final[str] = _ARM.LEDGER_ARM

    def __init__(self, *, n_agents: int, seed: int | str, day_key0: int, step_seconds: int, steps_per_day: int,
                 events: Any, agents: Any, world: Any, calendar: Any, runner: Any) -> None:
        if runner is None:
            raise ValueError("腕 --duties arm は世界過程(開閉店・補充・廃棄)のあるランだけ")
        self.n = int(n_agents)
        self.n_poi = int(world.n_poi)
        self.step_seconds = int(step_seconds)
        self.step_ns = self.step_seconds * NS_PER_SECOND
        self.steps_per_day = int(steps_per_day)
        #: 1 刻みの分(労働時間の計器=雇用の行の店に居た分)。
        self.step_minutes = max(1, self.step_seconds // SECONDS_PER_MINUTE)
        # ---- 参照 ----
        self.events = events
        self.agents = agents
        self.world = world
        self.calendar = calendar
        self.runner = runner
        self.shops = runner.opening
        self.shelf = runner.shelf
        self.waste = runner.waste
        # ---- 口(参照・設定) ----
        self.port = _P.DutiesPort(seed=seed, day_key0=int(day_key0), step_seconds=self.step_seconds)
        self.rules = ShopRules(self.shops)
        self.labor = labor_params(calendar.date_of_day(0) if calendar is not None else None)
        # ---- 雇用の行の表(導出=権利台帳の 体 → 店 の行と差し替えの世界の初期の行の表から作る・組み立てでは作らず最初に
        # 使うときに作る=再開では状態を戻して権利台帳を作り直した後=通しと同じ台帳) ----
        self._emp_agent: np.ndarray | None = None
        self._emp_store: np.ndarray | None = None
        self._emp_w21c: np.ndarray | None = None
        #: 店 → 店の担当の表の体の雇用の行の出どころの番号(``ORIGINS``)。
        self._store_origin: np.ndarray | None = None
        # ---- 状態(腕の行 DUS=店ごとの閉店の作業の印・DUG=系の間) ----
        #: 雇用の行の体が閉めた店(前の売れ残りの時刻から=閉店の作業の機会)。
        self._closed_by_me: np.ndarray = np.zeros(self.n_poi, dtype=bool)
        #: 雇用の行の体が売れ残りを捨てた店(前の売れ残りの時刻から=05:00 のつなぎが捨てない店)。
        self._binned: np.ndarray = np.zeros(self.n_poi, dtype=bool)
        #: その刻みの主の判断の役割語 ``[[体, 刻み, 語, call_id], …]``(判断の系が積み・同じ刻みの系 duties が読む=刻みの境目で空)。
        self._role_asks: list[list[Any]] = []
        # ---- 計器(腕の行 DUM=診断・再開でも通しと同じ) ----
        self._du_meter: dict[str, int] = {}
        self._du_hist: dict[str, dict[str, int]] = {}
        #: 前の刻みの終わりの店の開閉(エンジンのつなぎが開け閉めした店を数える=計器だけ)。
        self._du_prev: np.ndarray = np.full(self.n_poi, -2, dtype=np.int8)
        #: その日に雇用の行の店に起きて居た分(体ごと)と、労働時間の行を超えたと数えた体(その日)。
        self._du_minutes: np.ndarray = np.zeros(self.n, dtype=np.int32)
        self._du_over: np.ndarray = np.zeros(self.n, dtype=bool)
        #: 〔検収 L5〕``[ランの中の日の数, 今の日]``(計器の日の頭を決めるだけ=diag)。
        self._days: list[int] = [0, -1]
        # ---- 発行した判断の呼びの控えと呼び数(腕の行 DUQ=監査) ----
        self._du_issued: np.ndarray = np.zeros(1024, dtype=np.int64)
        #: ``[控えの数, 判断の呼び(判断モデル), 文の口の呼び(LLM)]``。
        self._du_issued_n: list[int] = [0, 0, 0]
        #: 役割語の道で原因にした主の判断の call_id(監査の控え)。
        self._du_role_ids: list[str] = []
        # ---- 刻みの中の作業の値 ----
        self._codes: dict[int, int] = {}

    # ================================================================== 雇用の行の表(導出)
    def ensure_staff(self) -> None:
        """〔検収 M1〕雇用の行(体 → 店)の表を作る(まだなら)。店の順・店の中は台帳の行の順(最初の行=開閉の過程の担当の表)。
        出どころ=差し替えの世界の初期の行の表(``initial_rights`` の塊 ``store_staff``)にある組なら W21c・ほかは丸振り。"""
        if self._emp_agent is not None:
            return
        from shibuya.engine.rights.ledger import AGENT, EMPLOY, STORE

        h, o = self.shops.rights.pairs(EMPLOY, AGENT, STORE, 0)
        h, o = np.asarray(h, dtype=np.int64), np.asarray(o, dtype=np.int64)
        ok = (h >= 0) & (h < self.n) & (o >= 0) & (o < self.n_poi)
        h, o = h[ok], o[ok]
        order = np.argsort(o, kind="stable")
        h, o = h[order], o[order]
        w21c = np.zeros(h.size, dtype=bool)
        rows = getattr(self.shops, "initial_rights", None)
        if rows is not None and h.size:
            sel = np.asarray(rows.block) == "store_staff"
            keys = set(zip(np.asarray(rows.holder)[sel].tolist(), np.asarray(rows.object_id)[sel].tolist()))
            w21c = np.array([(int(a), int(p)) in keys for a, p in zip(h.tolist(), o.tolist())], dtype=bool)  # 逐次: 雇用の行の数(1 回)
        origin = np.zeros(self.n_poi, dtype=np.int8)
        if h.size:
            uniq, first = np.unique(o, return_index=True)
            origin[uniq] = np.where(w21c[first], ORIGINS.index(ORIGIN_W21C), ORIGINS.index(ORIGIN_RR))
        self._emp_agent, self._emp_store, self._emp_w21c, self._store_origin = h, o, w21c, origin

    def _here(self) -> tuple[np.ndarray, np.ndarray]:
        """雇用の行ごとに (体が店のセルに居るか, 起きているか)。"""
        self.ensure_staff()
        a, s = self._emp_agent, self._emp_store
        reg = self.agents.registry
        here = np.asarray(reg.cell, dtype=np.int64)[a] == np.asarray(self.world.pois.cell, dtype=np.int64)[s]
        awake = np.asarray(reg.activity, dtype=np.int64)[a] != int(Activity.SLEEPING)
        return here, awake

    def staffed_now(self, stores: Any) -> np.ndarray:
        """〔検収 M1・M4〕店ごとに、その店の雇用の行を持つ体が店のセルに居て起きているか(世界過程の開閉と補充が読むだけ=
        真の店はエンジンが代わりにしない・偽の店はつなぎ)。"""
        here, awake = self._here()
        mask = np.zeros(self.n_poi, dtype=bool)
        mask[self._emp_store[here & awake]] = True
        return mask[np.asarray(stores, dtype=np.int64)]

    def _origin_of_store(self, p: int) -> str:
        self.ensure_staff()
        return ORIGINS[int(self._store_origin[int(p)])]

    def _tag(self, origin: str, p: int) -> str:
        return f"{origin}:{self.rules.source(int(p))}"

    # ================================================================== 小さな口
    def _bump(self, key: str, n: int = 1) -> None:
        self._du_meter[key] = self._du_meter.get(key, 0) + int(n)

    def _hist_add(self, name: str, v: int) -> None:
        h = self._du_hist.setdefault(name, {})
        k = str(int(v))
        h[k] = h.get(k, 0) + 1

    def _log(self, t_ns: int, who: int, what: str, cause: Any, *, poi: int, how_much: int | None = None) -> None:
        """出来事の記録へ 1 行(記録が off のランは何もしない)。書く口はこれ 1 つ。出どころの印=店の決まりの出どころ。"""
        log = self.events
        if log is None or not bool(getattr(log, "enabled", False)):
            return
        eid = log.append(Event(t_ns=int(t_ns), who=int(who), what=what, where=("poi", int(poi)), how_much=how_much,
                               via=V.VIA_NONE, origin=origin_mark(self.rules.source(int(poi))), cause=cause))
        if eid is not None:
            self._bump(f"events:{what}")

    def _decide(self, T: int, t_ns: int, a: int, purpose: int, cands: Sequence[Candidate]) -> tuple[Candidate, LlmCall]:
        """本人の判断 1 回(候補の口 J0 の形・仮のモデル)。選んだ候補と原因(LlmCall)を返す。"""
        k = self._codes.get(a, 0) + 1
        self._codes[a] = k
        serial = _P.serial_of(purpose, k)
        cell = int(self.agents.registry.cell[a])
        ctx = DecisionContext(agent_id=int(a), step=int(T), t_ns=int(t_ns), wake_class=-1, condition=-1, cell=cell,
                              call_id=_P.call_id_of(T, a, serial))
        ch = self.port.choose(ctx, cands)
        self._issue(T, a, serial)
        self._du_issued_n[1] += 1
        c = next(x for x in cands if x.id == ch.candidate_id)
        basis = tuple(sorted({b for x in cands for b in x.basis}))
        self._bump(f"decisions:{_P.PURPOSES[purpose]}")
        self._bump(f"chosen:{c.kind}")
        return c, LlmCall(ctx.call_id, basis, source=c.source, number=int(ch.number))

    def _issue(self, T: int, a: int, serial: int) -> None:
        n = int(self._du_issued_n[0])
        if n >= self._du_issued.size:
            grown = np.zeros(self._du_issued.size * 2, dtype=np.int64)
            grown[:n] = self._du_issued[:n]
            self._du_issued = grown
        self._du_issued[n] = issued_key(T, a, serial)
        self._du_issued_n[0] = n + 1

    def issued_keys(self) -> np.ndarray:
        """発行した判断の呼びの控え(写し・監査の道具が読む)。"""
        return self._du_issued[: int(self._du_issued_n[0])].copy()

    def role_call_ids(self) -> tuple[str, ...]:
        """役割語の道で原因にした主の判断の call_id(写し・監査の道具が読む)。"""
        return tuple(self._du_role_ids)

    def model_calls(self) -> tuple[int, int]:
        """店の仕事の呼び数 ``(判断の呼び=判断モデル, 文の口=LLM)``(主の判断の役割語は主の判断の呼びに入る=数えない)。"""
        return int(self._du_issued_n[1]), int(self._du_issued_n[2])

    def binned_mask(self) -> np.ndarray:
        """前の売れ残りの時刻から雇用の行の体が売れ残りを捨てた店(廃棄の過程が読むだけ=05:00 のつなぎが捨てない店)。"""
        return self._binned

    # ================================================================== 口(世界過程のつなぎ・判断の口の役割語)
    def note_bridge(self, item: str, stores: Any) -> None:
        """〔検収 M1・M3〕エンジンのつなぎが代わりにした店(補充=10:00・廃棄=05:00 の行ごと=世界の系が呼ぶ・計器だけ)。店の担当の
        表の体の雇用の行の出どころと店の決まりの出どころで分けて数える。"""
        for p in np.asarray(stores, dtype=np.int64).tolist():  # 逐次: つなぎの店の数ぶん(日に 1 回の刻み)
            self._bump(f"bridge:{item}:{self._tag(self._origin_of_store(p), p)}")

    def note_role_word(self, agent: int, step: int, word: str, call_id: str) -> None:
        """主の判断の役割語を控える(``LLMBridge.role_sink``・判断の系の中=書くのは控えの列だけ)。効くのは本段の語(補充・開閉店)
        だけ(ほかの役割語は系 duties が数えるだけ)。"""
        self._role_asks.append([int(agent), int(step), str(word), str(call_id)])

    # ================================================================== 1 刻み(系 duties の本体)
    def run_step(self, T: int, t_ns: int, td: int, day: int, *, agents: Any, world: Any, decision: Any) -> None:
        self._codes.clear()
        self.ensure_staff()
        minute = (int(td) * self.step_seconds // SECONDS_PER_MINUTE) % MINUTES_PER_DAY
        if int(self._days[1]) != int(day):  # 日の頭(計器の日の数・労働時間の計器を空に)
            self._days[1] = int(day)
            self._days[0] += 1
            self._du_minutes[:] = 0
            self._du_over[:] = False
        now = np.asarray(world.pois.open_now, dtype=np.int8)
        # ---- 0. エンジンのつなぎが開け閉めした店(前の刻みの終わりからの変わり=世界の系が先に回った)・計器 ----
        ch = np.flatnonzero((now != self._du_prev) & (self._du_prev >= 0))
        for p in ch.tolist():  # 逐次: その刻みにつなぎが開け閉めした店の数ぶん
            item = "unlock" if int(now[p]) == 1 else "lock"
            self._bump(f"bridge:{item}:{self._tag(self._origin_of_store(p), p)}")
        # ---- 0b. 売れ残りのつなぎ(05:00)の後に閉店の作業の印を空に(廃棄の過程は同じ刻みの世界の系で読んだ) ----
        if minute == WASTE_TO_BIN_MINUTE:
            self._closed_by_me[:] = False
            self._binned[:] = False
        # ---- 0c. 棚の減った/空の店 × 分(計器) ----
        self._shelf_meter(T)
        sel = getattr(decision, "selected", None) if decision is not None else None
        main = np.zeros(self.n, dtype=bool)
        if sel is not None and len(sel):
            ids = np.asarray(sel.agent_id, dtype=np.int64)
            main[ids[(ids >= 0) & (ids < self.n)]] = True
        # ---- 1. 主の判断の役割語(同じ刻み) ----
        asks, self._role_asks = self._role_asks, []
        for a, st, word, cid in asks:  # 逐次ループ宣言 (b): その刻みの主の判断の役割語の数ぶん
            if str(word) not in _P.ROLE_KINDS:
                self._bump(f"role_words:other:{word}")
                continue
            self._role_word(T, t_ns, int(a), str(word), str(cid))
        # ---- 2. 雇用の行の体が店に居る店(配列演算・1 店 1 刻みの判断は雇用の行の順で最初の 1 人) ----
        here, awake = self._here()
        ea = self._emp_agent
        self._labor(np.unique(ea[here & awake]))  # 〔検収 L3〕店で寝ている刻みは数えない
        self._bump("present:store_steps", int(np.unique(self._emp_store[here]).size))
        self._bump("present:asleep_rows", int(np.count_nonzero(here & ~awake)))
        self._bump("present:main_first_rows", int(np.count_nonzero(here & awake & main[ea])))
        pois, s, rows = first_per_store(self._emp_store, ea, here & awake & ~main[ea])
        if pois.size == 0:
            np.copyto(self._du_prev, world.pois.open_now, casting="unsafe")
            return
        self._bump("present:second_or_later", int(np.count_nonzero(rows != np.searchsorted(self._emp_store, pois))))
        w21c = self._emp_w21c[rows]
        # ---- 3. 気づく(店の決まり・棚・閉店の作業) ----
        unlock, lock = self._shop_offers(s, pois, minute, t_ns, now)
        notice = np.zeros(pois.size, dtype=bool)
        if self.shelf.active and minute % RESTOCK_STEP_MINUTES == 0:
            stock = np.asarray(self.shelf.ledger.goods.aggregate_stock(), dtype=np.int64)[pois]
            low = (stock < np.asarray(self.shelf.reorder_point, dtype=np.int64)[pois]) & np.asarray(
                world.open_mask(T), dtype=bool)[pois]
            stocked = np.asarray(self.shelf.backroom, dtype=np.int64)[pois] > 0  # 〔検収 M2〕本人は在庫を知っている
            self._bump("shelf:no_notice_empty_backroom", int(np.count_nonzero(low & ~stocked)))
            notice = low & stocked
        bins = np.zeros(pois.size, dtype=bool)
        if self.waste.active:
            maybe = self._closed_by_me[pois] & ~self._binned[pois] & (now[pois] == 0)
            if maybe.any():
                bins[maybe] = self.waste.leftovers_of(pois[maybe]) > 0
        todo = np.flatnonzero(unlock | lock | notice | bins)
        # ---- 4. 選ぶ → 変わる ----
        for i in todo.tolist():  # 逐次ループ宣言 (a): 雇用の行の体が店に居て候補がある店の数ぶん(1 店あたり判断 ≤ 2)
            a, p = int(s[i]), int(pois[i])
            origin = ORIGIN_W21C if bool(w21c[i]) else ORIGIN_RR
            if unlock[i] or lock[i]:
                self._shop(T, t_ns, a, p, minute, bool(unlock[i]), origin)
            if notice[i] and int(world.pois.open_now[p]) > 0:
                self._restock(T, t_ns, a, p, origin)
            if bins[i]:
                self._discard(T, t_ns, a, p, origin)
        np.copyto(self._du_prev, world.pois.open_now, casting="unsafe")

    def _shop_offers(self, s: np.ndarray, pois: np.ndarray, minute: int, t_ns: int,
                     now: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """開閉の候補を出す店(店の決まりの口の答えだけから=時刻の直書きなし)。最初の設定の前の店(負)は出さない。"""
        if not self.shops.active:
            z = np.zeros(pois.size, dtype=bool)
            return z, z
        rsoon = self.rules.at(s, pois, minute + SHOP_LEAD_MINUTES, t_ns)
        cur = now[pois]
        unlock = (rsoon != UNKNOWN) & (cur == 0) & (rsoon == 1)
        lock = (rsoon != UNKNOWN) & (cur == 1) & (rsoon == 0)
        return unlock, lock

    def _shelf_meter(self, T: int) -> None:
        if not self.shelf.active:
            return
        stock = np.asarray(self.shelf.ledger.goods.aggregate_stock(), dtype=np.int64)
        lit = np.asarray(self.world.open_mask(T), dtype=bool)
        low = lit & (stock < np.asarray(self.shelf.reorder_point, dtype=np.int64))
        empty = lit & (stock <= 0)
        for name, m in (("low", low), ("empty", empty)):  # 逐次: 2 × 出どころ 3
            for k, origin in enumerate(ORIGINS):
                self._bump(f"shelf:{name}_store_minutes:{origin}",
                           int(np.count_nonzero(m & (self._store_origin == k))) * self.step_minutes)

    def _labor(self, here: np.ndarray) -> None:
        """労働時間の行(human)を読むだけで止めない=雇用の行の店に起きて居た分がその日の上限を超えた体を数える。"""
        if here.size == 0:
            return
        self._du_minutes[here] += self.step_minutes
        lp = self.labor
        if not lp:
            return
        over = here[(self._du_minutes[here] > int(lp["max_hours_per_day"]) * MINUTES_PER_HOUR) & ~self._du_over[here]]
        if over.size:
            self._du_over[over] = True
            self._bump("labor:over_day_hours", int(over.size))

    # ---------------------------------------------------------------- 選ぶ → 変わる
    def _shop(self, T: int, t_ns: int, a: int, p: int, minute: int, unlock: bool, origin: str) -> None:
        cands = [_P.cand(_P.K_SHOP, "店を開ける" if unlock else "店を閉める", id=_P.ID_UNLOCK if unlock else _P.ID_LOCK),
                 _P.cand(_P.K_WAIT, "まだ", id="wait")]
        c, cause = self._decide(T, t_ns, a, _P.P_SHOP, cands)
        if c.kind != _P.K_SHOP:
            self._bump("shop:not_yet")
            return
        self._set_shop(T, t_ns, a, p, unlock, cause, minute, origin)

    def _set_shop(self, T: int, t_ns: int, a: int, p: int, unlock: bool, cause: LlmCall, minute: int,
                  origin: str) -> None:
        """店を開ける/閉める(本人の行動=``resolve.request_open_close``・ActualLog ``SCHEDULED``・出来事 1 行)。"""
        op = self.shops
        from shibuya.engine.rights.ledger import AGENT, EMPLOY, STORE

        aa, pp = np.array([a], dtype=np.int64), np.array([p], dtype=np.int64)
        R.request_open_close(self.agents, self.world, aa, pp, np.array([unlock]), int(T),
                             permitted=op.rights.holds_each(aa, pp, kind=EMPLOY, holder_kind=AGENT, object_kind=STORE,
                                                            t_ns=int(t_ns)),
                             on_unauthorized=op._record_unauthorized)
        if op.log is not None:
            op.log.append_many(_SHOP_PROCESS_ID, pp, np.array([int(T)], dtype=np.int64),
                               np.array([_CODE_SCHEDULED], dtype=np.int8))
        mark = self.rules.edge(a, p, minute, t_ns, rising=bool(unlock))
        gap = None if mark is None else _signed_gap(minute, mark)
        self._log(t_ns, a, W_UNLOCK if unlock else W_LOCK, cause, poi=p, how_much=gap)
        tag = self._tag(origin, p)
        self._bump(f"person:{'unlock' if unlock else 'lock'}:{tag}")
        if gap is not None:
            self._hist_add(f"{'shop_begin' if unlock else 'shop_end'}:{self.rules.source(p)}", gap)
        # 〔検収 L2〕店の決まりとの関係(幅の中で早め/幅の外=決まりの外)を分けて数える
        rnow = int(self.rules.at([a], [p], minute, t_ns)[0])
        rsoon = int(self.rules.at([a], [p], minute + SHOP_LEAD_MINUTES, t_ns)[0])
        if unlock and rnow == 0:
            self._bump("hours:unlock_early_in_window" if rsoon == 1 else "hours:unlock_outside_rule_hours")
        if not unlock and rnow == 1:
            self._bump("hours:lock_early_in_window" if rsoon == 0 else "hours:locked_during_rule_hours")
        if not unlock:
            self._closed_by_me[p] = True

    def _restock(self, T: int, t_ns: int, a: int, p: int, origin: str) -> None:
        cands = [_P.cand(_P.K_RESTOCK, "棚に補充する", id="restock"), _P.cand(_P.K_SERVE, "接客する", id="serve"),
                 _P.cand(_P.K_WAIT, "待つ", id="wait")]
        c, cause = self._decide(T, t_ns, a, _P.P_SHELF, cands)
        if c.kind != _P.K_RESTOCK:
            self._bump("shelf:serve" if c.kind == _P.K_SERVE else "shelf:wait")
            return
        self._do_restock(T, t_ns, a, p, cause, origin)

    def _do_restock(self, T: int, t_ns: int, a: int, p: int, cause: LlmCall, origin: str) -> None:
        done, got = self.shelf.restock_by_staff([p], int(T))
        if not bool(done[0]):
            self._bump("shelf:person_failed")  # バックヤードが空・資金が足りない(物理と仕組みで止まる)
            return
        self._log(t_ns, a, W_RESTOCK, cause, poi=p, how_much=int(got[0]))
        self._bump(f"person:restock:{self._tag(origin, p)}")
        self._bump("shelf:person_units", int(got[0]))

    def _discard(self, T: int, t_ns: int, a: int, p: int, origin: str) -> None:
        cands = [_P.cand(_P.K_DISCARD, "売れ残りを捨てる", id="discard"), _P.cand(_P.K_WAIT, "まだ", id="wait")]
        c, cause = self._decide(T, t_ns, a, _P.P_WASTE, cands)
        if c.kind != _P.K_DISCARD:
            self._bump("waste:not_yet")
            return
        units, rows = self.waste.bin_by_staff([p], int(T))
        self._binned[p] = True
        self._log(t_ns, a, W_DISCARD, cause, poi=p, how_much=int(units[0]))
        self._bump("waste:person_bin")
        self._bump(f"person:discard_rows:{self._tag(origin, p)}", int(rows))
        self._bump("waste:person_units", int(units[0]))

    def _role_word(self, T: int, t_ns: int, a: int, word: str, cid: str) -> None:
        """主の判断の役割語を本人の行動として実行する(その体が雇用の行を持つ店のセルに居るときだけ=居なければ起きない)。"""
        self.ensure_staff()
        cell = int(self.agents.registry.cell[int(a)])
        pc = np.asarray(self.world.pois.cell, dtype=np.int64)
        mine = np.flatnonzero((self._emp_agent == int(a)) & (pc[self._emp_store] == cell))
        if mine.size == 0:
            self._bump(f"role_words:not_at_store:{word}")
            return
        row = int(mine[0])
        p = int(self._emp_store[row])
        origin = ORIGIN_W21C if bool(self._emp_w21c[row]) else ORIGIN_RR
        minute = (int(T) % self.steps_per_day) * self.step_seconds // SECONDS_PER_MINUTE
        if word == _P.K_RESTOCK:
            # 〔検収 L7〕気づきと同じ条件(営業中・棚が補充点の下)のときだけ
            lit = bool(np.asarray(self.world.open_mask(int(T)), dtype=bool)[p])
            low = (self.shelf.active and int(np.asarray(self.shelf.ledger.goods.aggregate_stock(), dtype=np.int64)[p])
                   < int(self.shelf.reorder_point[p]))
            if not (lit and low):
                self._bump("role_words:restock_not_needed")
                return
            cause = LlmCall(str(cid))
            self._du_role_ids.append(str(cid))
            self._bump("role_words:restock")
            self._do_restock(T, t_ns, int(a), p, cause, origin)
            return
        cur = int(self.world.pois.open_now[p])
        if cur < 0:
            self._bump("role_words:shop_before_first_setting")
            return
        cause = LlmCall(str(cid))
        self._du_role_ids.append(str(cid))
        self._bump("role_words:shop")
        self._set_shop(T, t_ns, int(a), p, cur == 0, cause, minute, origin)

    # ================================================================== 計器・manifest
    def _coverage(self, m: Mapping[str, int]) -> dict[str, Any]:
        """〔検収 M1・M3〕本人/つなぎの数とカバー率=項目 × (全部・雇用の行の出どころ別・店の決まりの出どころ別)。"""
        def share(p: int, e: int) -> float | None:
            return (p / (p + e)) if (p + e) else None

        def cell(person: int, bridge: int) -> dict[str, Any]:
            return {"person": person, "bridge": bridge, "person_share": share(person, bridge)}

        out: dict[str, Any] = {"total": {}, "by_employment_origin": {}, "by_rule_source": {}}
        for item in _ITEMS:  # 逐次: 項目 4 × 計器の鍵
            tot = [0, 0]
            by_o: dict[str, list[int]] = {}
            by_s: dict[str, list[int]] = {}
            for k, v in m.items():
                head, _sep, rest = k.partition(":")
                if head not in ("person", "bridge"):
                    continue
                it, _s2, tag = rest.partition(":")
                if it != item:
                    continue
                origin, _s3, src = tag.partition(":")
                j = 0 if head == "person" else 1
                tot[j] += int(v)
                by_o.setdefault(origin, [0, 0])[j] += int(v)
                by_s.setdefault(src, [0, 0])[j] += int(v)
            out["total"][item] = cell(*tot)
            out["by_employment_origin"][item] = {o: cell(*v) for o, v in sorted(by_o.items())}
            out["by_rule_source"][item] = {s: cell(*v) for s, v in sorted(by_s.items())}
        return out

    def manifest(self) -> dict[str, Any]:
        self.ensure_staff()
        m = dict(sorted(self._du_meter.items()))

        def pick(prefix: str) -> dict[str, int]:
            return {k[len(prefix):]: v for k, v in m.items() if k.startswith(prefix)}

        staff = np.asarray(self.shops.staff_of_poi, dtype=np.int64)
        counts = np.bincount(self._emp_store, minlength=self.n_poi) if self._emp_store.size else np.zeros(self.n_poi, int)
        example = ""
        for poi in np.flatnonzero(staff >= 0)[:1].tolist():  # 逐次: 1(例の 1 行)
            example = rules_line(self.rules, int(staff[poi]), int(poi), 0)
        srcs = getattr(getattr(self.shops, "assets", None), "plan_src_names", ())
        cfg = {
            "schema": SCHEMA, "arm": _ARM.ARM_ON, "port": self.port.name,
            "rules": {"source": "W7 の営業時間の表のその日の行(OpeningProcess.open_matrix)=雇用の行(体 → 店)の体だけが引ける・"
                                "出どころの印=W7 の列 src(osm_opening_hours=実データ・chain_default/category_default=作り物の印)",
                      "rule_sources": list(srcs),
                      "lead_minutes": int(SHOP_LEAD_MINUTES), "restock_notice_every_minutes": int(RESTOCK_STEP_MINUTES),
                      "notice": "棚の残りが補充点の下(ShelfRestockProcess.reorder_point)・営業中・バックヤードに在庫がある",
                      "waste": "雇用の行の体が閉めた店に売れ残りがある(閉店の作業)",
                      "staff": "その店の雇用の行を持つ体なら誰でも(店のセルに居て起きていて主の判断が無い)・1 店 1 刻みの判断は"
                               "雇用の行の順で最初の 1 人"},
            "arbitration": dict(ARBITRATION),
            "bridges": {"shop": "雇用の行の体が店に居て起きていない店=OpeningProcess の REPLACEMENT(conf 0.5)",
                        "shelf": "雇用の行の体が店に居て起きていない店=10:00 の engine_rule(conf 0.5)",
                        "waste": "雇用の行の体が捨てなかった店=05:00 の売れ残り → ビン",
                        "initial": "開始の刻みの最初の設定(open_now が負の店)はエンジン"},
            "provisional": list(_P.PROVISIONAL_VALUES),
        }
        obs = {
            "meter": m, "decisions": pick("decisions:"),
            "shop": {**pick("shop:"), "stores": int(self.n_poi),
                     "stores_with_employment": int(np.count_nonzero(counts > 0)),
                     "stores_with_2plus_employment": int(np.count_nonzero(counts >= 2)),
                     "employment_rows": int(self._emp_store.size),
                     "employment_agents": int(np.unique(self._emp_agent).size),
                     "stores_by_staff_origin": {o: int(np.count_nonzero(self._store_origin == k))
                                                for k, o in enumerate(ORIGINS)}},
            "shelf": pick("shelf:"),
            "waste": pick("waste:"),
            "coverage": self._coverage(m),
            "delay_minutes": {k: dict(sorted(v.items(), key=lambda kv: int(kv[0])))
                              for k, v in sorted(self._du_hist.items())},
            "labor_over": {**pick("labor:"), **pick("hours:"), "labor": dict(self.labor), "enforced": False},
            "role_words": pick("role_words:"),
            "common_knowledge": {"line": example},
            "calls": dict(zip(("judge_model", "llm"), self.model_calls())),
        }
        return {**cfg, **obs}


def manifest_fields(layer: DutiesLayer | None) -> dict[str, Any]:
    """manifest の ``duties``(腕 arm のランだけ・ほかは空=欄を出さない)。"""
    return {} if layer is None else {_ARM.MANIFEST_KEY: layer.manifest()}


def sys_duties(ctx: Any, b: Any) -> None:
    """系 duties(刻みの中・腕 arm のランだけ立つ)。"""
    b.layers.duties.run_step(ctx.T, int(ctx.t_ns), ctx.td, ctx.day, agents=b.soa.agents, world=b.soa.world,
                             decision=b.scratch.decision)


def audit_causes(events: Iterable[Any], *, step_ns: int, issued: Any = None,
                 role_ids: Iterable[str] = ()) -> dict[str, Any]:
    """負の対照の監査: 族 ``仕事`` の出来事の原因が判断の呼び(LlmCall)か。本段の判断の呼び(この層の形の call_id)は源と番号
    つき・時刻が判断の刻み・``issued``(:meth:`DutiesLayer.issued_keys`)にあり・体が同じ・判断の種類が語に合う
    (:data:`WORD_PURPOSES`)か。主の判断の役割語の道は ``role_ids``(:meth:`DutiesLayer.role_call_ids`)に call_id があるか。"""
    have = None if issued is None else set(int(x) for x in np.asarray(issued, dtype=np.int64).tolist())
    roles = set(str(x) for x in role_ids)
    bad: list[str] = []
    n = 0
    for ev in events:  # 逐次: 出来事の数ぶん(試験と記録の道具だけ)
        if not str(ev.what).startswith(f"{V.FAMILY_DUTY}:"):
            continue
        n += 1
        c = ev.cause
        if ev.what not in PERSON_WORDS or not isinstance(c, LlmCall):
            bad.append(f"{ev.what} の原因が本人の判断でない: {c!r}")
            continue
        got = _P.parse_call_id(c.call_id)
        if got is None:
            if str(c.call_id) not in roles:
                bad.append(f"{ev.what} の原因 {c.call_id} は層の判断の呼びでも主の判断の役割語でもない")
            elif ev.what not in (W_UNLOCK, W_LOCK, W_RESTOCK):
                bad.append(f"{ev.what} は役割語の道の語でない")
            continue
        if c.source is None or c.number is None:
            bad.append(f"{ev.what} の原因に候補の源と番号が無い: {c!r}")
            continue
        st, who, serial = got
        if int(who) != int(ev.who):
            bad.append(f"{ev.what} の体 {ev.who} と判断の呼びの体 {who} が違う")
        if have is not None:
            try:
                k = issued_key(st, who, serial)
            except ValueError:
                k = -1
            if k not in have:
                bad.append(f"{ev.what} の原因 {c.call_id} は層の発行した判断の呼びに無い")
        if _P.purpose_of_serial(serial) not in WORD_PURPOSES.get(ev.what, frozenset()):
            bad.append(f"{ev.what} の原因の判断の種類 {_P.purpose_of_serial(serial)} が語に合わない")
        if int(ev.t_ns) != int(st) * int(step_ns):
            bad.append(f"{ev.what} の時刻 {ev.t_ns} が判断の刻み {st} と違う")
    return {"events": n, "violations": len(bad), "examples": bad[:5]}
