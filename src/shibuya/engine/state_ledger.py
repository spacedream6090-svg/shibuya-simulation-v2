"""状態台帳の宣言(10b・A3「挙動」と「復元」の 2 軸・機械可読の 1 ファイル)。

**読み口は 1 つ**: ``LEDGER``(187 行の組)・``OWNER_CLASSES``・``EXCLUDED`` と、その上の小さな関数(``rows``・
``soa_rows``・``external_rows``・``behavior_excluded``・``full_excluded``・``full_items``・``behavior_items``)。表・AST の検査(``engine.state_ledger_ast``)・
2 つのハッシュ(``engine.state_hashes``)・揺らし試験はどれもこの表から作る。

行の中身(材料 ``docs/bench/analysis/wallbounce-1003/10b-prep.md`` §1 の表を写した。根拠の ``path:line`` は
材料の値=a08109a の行番号。パスは ``src/shibuya/`` を省略):

- **SoA の列 98 行**(agents 79・cells 5・pois 9・知覚 5): ``place`` は ``agents``・``cells``・``pois``・``perception``。
- **SoA の外の状態 94 行**(O1〜O65=材料・O66〜O89=10b-2 で持ち主のクラスの属性を棚卸しして足した行・
  O90〜O94=10d の再開の試験と検収で見つけた保存し忘れを元の行から移した行):
  ``place`` は ``external``。``items`` はその行が指す属性の道筋
  (``run_day`` の中で組む ``owners`` の鍵から ``.`` でたどる。例 ``runner.salient.rng``)。

軸 1「挙動」(``behavior``。A2 (b)=どれかの腕・どれかの構成で分岐・計算・描画に使う読み手があれば入れる):

- ``behavior`` = behavior-hash に入れる。
- ``no`` = 読まれない(または派生として入れないと宣言した)。
- ``diag`` = 診断・要約・保存則の検査・日次センサスだけが読む。

軸 2「復元」(``restore``。日境界の再開で保存するか):

- ``required`` = 要る / ``derivable`` = 資産・母集団・予定の表・ほかの列から作り直せる /
  ``discardable`` = 捨ててよい(死蔵・tick の中だけ・キャッシュ・日ごとに 0 に戻す計数)/
  ``unknown`` = 不明(K15 の答えで直す欄。安全側として full-hash には入れる)。

full-hash に入れるのは軸 2 が ``required``・``derivable``・``unknown`` の行(``discardable`` を入れると
再開で 0 から始まる行が混ざり ``resume == straight`` が成り立たない=アジェンダ §2-3)。外の状態の行のうち
``hash_skip`` に挙げた属性(キャッシュと計数)は、行が ``derivable`` でも中身を入れない(作り直しで空になる)。

親の宣言(expedient・アジェンダ §3 の下の段落と指示): 知覚 SoA の ``heading``・``task_flag`` は事象の直前に
貼り直す派生の値なので ``no``。``OutOfAreaMeals.d_armed`` は ``required``(日をまたぐ印として持ち越す)。
金・物・ActualLog のリング 3 行は ``discardable``(K16 の既定案)。``fail_streak``・``plan_activity`` は
``no`` かつ復元 ``unknown``(K15)。

10b-2(親の答え): 外の状態の持ち主のクラス(``OWNER_CLASSES``)の属性は、どれかの行の ``items`` か、明示の除外の
一覧 ``EXCLUDED``((ii) キャッシュ・導出 / (iii) 定数・設定 / (iv) 参照・理由つき)のどちらかに必ず載る
(``engine.state_ledger_ast.coverage`` とテストが突き合わせる)。判断のつかない行は軸 2 を ``unknown`` にして
full-hash に入れる。``hunger`` は構成で軸 2 が変わる印(``restore_by_config``)を持つ。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable

#: 表の版(列や行の判定を変えたら上げる。manifest の ``state_hashes.ledger_version`` に出る)。
LEDGER_VERSION: Final[str] = "state-ledger/10d"

BEHAVIOR: Final[str] = "behavior"
NO: Final[str] = "no"
DIAG: Final[str] = "diag"
AXIS1_VALUES: Final[tuple[str, ...]] = (BEHAVIOR, NO, DIAG)

REQUIRED: Final[str] = "required"
DERIVABLE: Final[str] = "derivable"
DISCARDABLE: Final[str] = "discardable"
UNKNOWN: Final[str] = "unknown"
AXIS2_VALUES: Final[tuple[str, ...]] = (REQUIRED, DERIVABLE, DISCARDABLE, UNKNOWN)
#: full-hash に入れる軸 2 の値。
FULL_RESTORE: Final[frozenset[str]] = frozenset({REQUIRED, DERIVABLE, UNKNOWN})

SOA_PLACES: Final[tuple[str, ...]] = ("agents", "cells", "pois", "perception")
EXTERNAL: Final[str] = "external"


@dataclass(frozen=True)
class AstAllow:
    """AST の検査で「読み手」として数えても許す場所(``path`` と、その行に含まれる文字列で引く)。

    行番号はずれるので使わない。``reason`` は除外の根拠(記録にそのまま出る)。
    """

    path: str
    contains: str
    reason: str


@dataclass(frozen=True)
class LedgerRow:
    """状態台帳の 1 行。"""

    #: 一意の鍵。SoA は ``"<place>.<name>"``、外の状態は ``"O<n>"``。
    key: str
    #: 列名(SoA)/オブジェクトと属性の見出し(外の状態)。
    name: str
    #: ``agents``・``cells``・``pois``・``perception``・``external``。
    place: str
    #: 型(SoA は numpy の型の略記 ``i4`` など・形があれば ``i4x11``)/外の状態は材料の型の欄。
    dtype: str
    #: 体(セル・POI)あたりのバイト(SoA)/外の状態は材料の大きさの欄(文字)。
    nbytes: str
    #: 確保の条件(``既定`` か腕の名)。外の状態は空。
    alloc: str
    behavior: str
    restore: str
    #: 死蔵(書き手も読み手も無い・または初期値だけ)。
    dead: bool
    #: 根拠(宣言の場所・読み手の ``path:line``=材料の表から写した値)。
    basis: str
    #: 外の状態: ``owners`` からたどる属性の道筋。
    items: tuple[str, ...] = ()
    #: 外の状態: full-hash に入れない属性(キャッシュ・計数)。``items`` の部分集合。
    hash_skip: tuple[str, ...] = ()
    #: AST の検査で許す読み手(``no``/``diag`` の列だけ)。
    ast_allow: tuple[AstAllow, ...] = ()
    note: str = ""
    #: 構成で軸 2 が変わる列の印(``(構成, 軸 2 の値)`` の組)。``restore`` は既定の構成の値。
    #: full-hash には ``restore`` で決める(安全側=どの構成でも入れる)。
    restore_by_config: tuple[tuple[str, str], ...] = ()
    #: 辞書の**挿入順**が挙動を決める行(走査の順が処理の順・``popitem`` で古い順に落とす など)。
    #: 印のある行の辞書は挿入順のまま直列化する(印の無い行の辞書は鍵の昇順=順に依らない)。
    #: ``collections.OrderedDict`` は印が無くても挿入順のまま流す(型が順序を持つ約束)。
    ordered: bool = False

    @property
    def is_soa(self) -> bool:
        return self.place in SOA_PLACES

    @property
    def in_behavior(self) -> bool:
        return self.behavior == BEHAVIOR

    @property
    def in_full(self) -> bool:
        return self.restore in FULL_RESTORE


# ---------------------------------------------------------------- SoA の列(98 行)
def _s(place: str, name: str, dtype: str, nbytes: str, alloc: str, behavior: str, restore: str,
       basis: str, *, dead: bool = False, allow: tuple[AstAllow, ...] = (), note: str = "",
       by_config: tuple[tuple[str, str], ...] = ()) -> LedgerRow:
    return LedgerRow(key=f"{place}.{name}", name=name, place=place, dtype=dtype, nbytes=nbytes,
                     alloc=alloc, behavior=behavior, restore=restore, dead=dead, basis=basis,
                     ast_allow=allow, note=note, restore_by_config=by_config)


B, N_, D_ = BEHAVIOR, NO, DIAG
R_, V_, X_, U_ = REQUIRED, DERIVABLE, DISCARDABLE, UNKNOWN

_ALLOW_BAND = (AstAllow("world/assets.py", 'cells["band"]',
                        "資産の表(W2 の parquet)の列 band を読む行。SoA の agents.band ではない(材料 §2-4 の誤検出 1)"),)
_ALLOW_B4 = (AstAllow("world/state.py", "return self.cells.b4_hash",
                      "プロパティ World.b4_hash の中の読み。プロパティの呼び手は 0(材料 §2-4 の誤検出 2)"),)
_ALLOW_REVENUE = (AstAllow("engine/run.py", "result.revenue_end =",
                           "保存則の検査とラン要約の値(RunResult.revenue_end)だけ=診断"),)
_ALLOW_ENERGY_BALANCE = (AstAllow("engine/energy.py", "bal = np.asarray(r.energy_balance",
                                  "EnergyLayer.summary(日次センサスと要約)だけ=診断"),)
_ALLOW_HEADING = (AstAllow("engine/processes/salient.py", "heading = np.asarray(self.pstate.heading)",
                           "顕著行為の p_notice が読む。値は事象の直前に毎回貼り直す派生の値なので状態としては入れない(親の宣言)"),)
_ALLOW_TASK = (AstAllow("engine/processes/salient.py", "task = np.asarray(self.pstate.task_flag)",
                        "同上(heading と同じ扱い・親の宣言)"),)

_SOA: tuple[LedgerRow, ...] = (
    # ---- agents(79 列・agents/state.py:505-716) ----
    _s("agents", "cell", "i4", "4", "既定", B, R_, "agents/state.py:505・resolve.py:1432 ほか"),
    _s("agents", "node", "i4", "4", "既定", B, R_, "agents/state.py:507・resolve.py:1432,1479"),
    _s("agents", "band", "i1", "1", "既定", N_, V_, "agents/state.py:509・resolve.py:1483(cell_band[cell] から導出)",
       allow=_ALLOW_BAND),
    _s("agents", "xy", "f4x2", "8", "既定", B, R_, "agents/state.py:511・salient.py:215・renderer.py:1252"),
    _s("agents", "path_next_node", "i4", "4", "既定", B, R_, "agents/state.py:513・resolve.py:1429"),
    _s("agents", "target_node", "i4", "4", "既定", B, R_, "agents/state.py:515・commit.py:554"),
    _s("agents", "kind", "i1", "1", "既定", B, V_, "agents/state.py:535・resolve.py:512・classical.py:350(母集団・ラン中不変)"),
    _s("agents", "age", "u1", "1", "既定", B, V_, "agents/state.py:538・resolve.py:1171,1182・classical.py:508",
       note="A2 (b): energy の空腹(CLI 既定)と classical のときだけ読む"),
    _s("agents", "sex", "i1", "1", "既定", B, V_, "agents/state.py:540・resolve.py:1171・classical.py:508",
       note="A2 (b): age と同じ"),
    _s("agents", "hunger", "u1", "1", "既定", B, R_, "agents/state.py:542・change_detect.py:305・renderer.py:1796",
       by_config=(("hunger_model=energy", DERIVABLE),),
       note="構成で軸 2 が変わる: v1 の空腹では要る・energy の空腹(CLI 既定)では毎 tick advance_body が "
            "since_meal_kcal から作り直す=導出できる(親の答え 6・full-hash には入れる)"),
    _s("agents", "fatigue", "u1", "1", "既定", B, R_, "agents/state.py:544・change_detect.py:77-81,305(名前の表 INTERO_VARS)"),
    _s("agents", "thermal", "u1", "1", "既定", B, R_, "agents/state.py:546・change_detect.py:305・renderer.py:2374"),
    _s("agents", "hunger_stage", "i1", "1", "既定", B, R_, "agents/state.py:550・change_detect.py:305(段の前回値)"),
    _s("agents", "fatigue_stage", "i1", "1", "既定", B, R_, "agents/state.py:552・change_detect.py:305"),
    _s("agents", "thermal_stage", "i1", "1", "既定", B, R_, "agents/state.py:554・change_detect.py:305"),
    _s("agents", "money", "i4", "4", "既定", B, R_, "agents/state.py:567・run.py:2208・resolve.py:2170"),
    _s("agents", "holdings", "u1", "1", "既定", B, R_, "agents/state.py:569・goods_flow.py:473・renderer.py:1815"),
    _s("agents", "activity", "i1", "1", "既定", B, R_, "agents/state.py:572・activity.py:432 ほか"),
    _s("agents", "plan_cursor", "i2", "2", "既定", N_, X_, "agents/state.py:574・宣言 1 件のみ(Q9 で消す)", dead=True),
    _s("agents", "talk_partner", "i4", "4", "既定", B, R_, "agents/state.py:576・memory.py:355・run.py:2639",
       note="A2 (b): 記憶の腕・店の記憶の腕のときだけ読む"),
    _s("agents", "invocation_distance", "u2", "2", "既定", N_, X_, "agents/state.py:578・宣言のみ(Q9 で消す)", dead=True),
    _s("agents", "transit_state", "i1", "1", "既定", B, R_, "agents/state.py:581・activity.py:433 ほか"),
    _s("agents", "transit_ref", "i4", "4", "既定", B, R_, "agents/state.py:584・rail.py:650・civic.py:496"),
    _s("agents", "board_line", "i1", "1", "既定", B, R_, "agents/state.py:588・presence.py:1422"),
    _s("agents", "board_since", "i4", "4", "既定", B, R_, "agents/state.py:591・resolve.py:2003"),
    _s("agents", "sleep_pending", "i1", "1", "既定", B, R_, "agents/state.py:595・commit.py:868"),
    _s("agents", "intent_action", "i1", "1", "既定", B, R_, "agents/state.py:599・intent.py:178"),
    _s("agents", "intent_target", "i4", "4", "既定", B, R_, "agents/state.py:603・intent.py:194・memory.py:358"),
    _s("agents", "intent_kind", "i1", "1", "既定", B, R_, "agents/state.py:605・intent.py:193"),
    _s("agents", "intent_since", "i4", "4", "既定", B, R_, "agents/state.py:607・intent.py:263,438"),
    _s("agents", "poi_ref", "i4", "4", "既定", B, R_, "agents/state.py:610・crowd.py:231・classical.py:416"),
    _s("agents", "poi_since", "i4", "4", "既定", B, R_, "agents/state.py:612・crowd.py:231"),
    _s("agents", "queue_poi", "i4", "4", "既定", B, R_, "agents/state.py:614・memory.py:366・presence.py:1321"),
    _s("agents", "queue_since", "i4", "4", "既定", B, R_, "agents/state.py:616・crowd.py:242"),
    _s("agents", "refractory_until", "i4x11", "44", "既定", B, R_, "agents/state.py:702・run.py:3108,3160"),
    _s("agents", "wake_pending_class", "i1", "1", "既定", N_, X_, "agents/state.py:705・agents/state.py:724(初期値 -1 だけ・Q9 で消す)",
       dead=True),
    _s("agents", "last_action", "i1", "1", "既定", B, R_, "agents/state.py:708・intent.py:394"),
    _s("agents", "last_result", "i1", "1", "既定", B, R_, "agents/state.py:711・activity.py:297"),
    _s("agents", "last_result_tick", "i4", "4", "既定", B, R_, "agents/state.py:713・activity.py:296・renderer.py:2504"),
    _s("agents", "fail_streak", "u1", "1", "既定", N_, U_,
       "agents/state.py:715・resolve.py:1074,1465,1526,1538,3054,3099(自分に 1 を足すか 0 に戻すだけ・読み 0)",
       note="K15 の答えで直す欄(今は behavior-hash から外し full-hash には入れる=安全側)"),
    _s("agents", "edge_id", "i4", "4", "腕 edge", B, R_, "agents/state.py:519・resolve.py:1432"),
    _s("agents", "edge_s", "f4", "4", "腕 edge", B, R_, "agents/state.py:522・resolve.py:1432"),
    _s("agents", "focus_target", "i4", "4", "腕 attention", B, R_, "agents/state.py:527・resolve.py:1622・renderer.py:1130"),
    _s("agents", "focus_ttl", "u1", "1", "腕 attention", B, R_, "agents/state.py:531・resolve.py:1805"),
    _s("agents", "weight_kg", "f4", "4", "腕 energy", B, V_, "agents/state.py:558・resolve.py:1182・energy.py:983",
       note="A2 (b): energy の腕の初期化(bmr を作る)だけで読む。ランの途中では読まれない"),
    _s("agents", "eer_kcal", "f4", "4", "腕 energy", B, V_, "agents/state.py:560・resolve.py:1153"),
    _s("agents", "since_meal_kcal", "f4", "4", "腕 energy", B, R_, "agents/state.py:562・resolve.py:1156"),
    _s("agents", "energy_balance", "f4", "4", "腕 energy", D_, R_, "agents/state.py:564・energy.py:903(日次センサスと要約だけ)",
       allow=_ALLOW_ENERGY_BALANCE, note="センサスの項(日をまたいで足していく値)"),
    _s("agents", "plan_activity", "i1", "1", "腕 plan", N_, U_, "agents/state.py:620・AST: 読み 0",
       note="K15 の答えで直す欄(今は behavior-hash から外し full-hash には入れる=安全側)"),
    _s("agents", "plan_flags", "i1", "1", "腕 plan", B, R_, "agents/state.py:623・presence.py:1560"),
    _s("agents", "activity_until", "i4", "4", "腕 activity", B, R_, "agents/state.py:628・activity.py:350"),
    _s("agents", "activity_kind", "i1", "1", "腕 activity", B, R_, "agents/state.py:631・resolve.py:1133・renderer.py:1572"),
    _s("agents", "fam_thing", "i4x64", "256", "腕 familiarity", B, R_, "agents/state.py:636・familiarity.py:199"),
    _s("agents", "fam_first", "i4x64", "256", "腕 familiarity", B, R_, "agents/state.py:638・familiarity.py:187"),
    _s("agents", "fam_last", "i4x64", "256", "腕 familiarity", N_, R_, "agents/state.py:640・AST: 読み 0(表の行の一部・将来の読み手)"),
    _s("agents", "fam_visits", "u2x64", "128", "腕 familiarity", B, R_, "agents/state.py:642・familiarity.py:186"),
    _s("agents", "fam_exposures", "u2x64", "128", "腕 familiarity", B, R_, "agents/state.py:644・familiarity.py:186"),
    _s("agents", "mem_kind", "u1x128", "128", "腕 memory", B, R_, "agents/state.py:649・memory.py:333"),
    _s("agents", "mem_tick", "i4x128", "512", "腕 memory", B, R_, "agents/state.py:651・memory.py:309"),
    _s("agents", "mem_last", "i4x128", "512", "腕 memory", B, R_, "agents/state.py:653・memory.py:403,485",
       note="A2 (b): 記憶の腕の描画だけ(B5 の時刻)"),
    _s("agents", "mem_cell", "i4x128", "512", "腕 memory", B, R_, "agents/state.py:655・memory.py:376"),
    _s("agents", "mem_partner", "i4x128", "512", "腕 memory", B, R_, "agents/state.py:657・memory.py:372"),
    _s("agents", "mem_object", "i4x128", "512", "腕 memory", B, R_, "agents/state.py:659・memory.py:369"),
    _s("agents", "mem_result", "u1x128", "128", "腕 memory", B, R_, "agents/state.py:661・memory.py:378"),
    _s("agents", "mem_importance", "u1x128", "128", "腕 memory", B, R_, "agents/state.py:663・memory.py:310"),
    _s("agents", "mem_n", "u2x128", "256", "腕 memory", B, R_, "agents/state.py:665・memory.py:309"),
    _s("agents", "sm_poi", "i4x32", "128", "腕 store_memory", B, R_, "agents/state.py:670・store_choice.py:141"),
    _s("agents", "sm_valence", "f4x32", "128", "腕 store_memory", B, R_, "agents/state.py:672・store_memory.py:303"),
    _s("agents", "sm_precision", "f4x32", "128", "腕 store_memory", B, R_, "agents/state.py:674・store_choice.py:148"),
    _s("agents", "sm_first", "i4x32", "128", "腕 store_memory", B, R_, "agents/state.py:676・store_memory.py:306"),
    _s("agents", "sm_last", "i4x32", "128", "腕 store_memory", B, R_, "agents/state.py:678・store_memory.py:330,346・memory.py:486",
       note="A2 (b): 減衰 ga/citysim の腕と B5 の描画だけ"),
    _s("agents", "sm_n", "u2x32", "64", "腕 store_memory", B, R_, "agents/state.py:680・store_memory.py:305"),
    _s("agents", "sm_source", "u1x32", "32", "腕 store_memory", B, R_, "agents/state.py:682・store_choice.py:149"),
    _s("agents", "rel_partner", "i4x15", "60", "腕 relations", B, R_, "agents/state.py:689・relations.py:709"),
    _s("agents", "rel_kind", "u1x15", "15", "腕 relations", B, R_, "agents/state.py:691・relations.py:733"),
    _s("agents", "rel_sign", "i1x15", "15", "腕 relations", B, R_, "agents/state.py:693・relations.py:736"),
    _s("agents", "rel_first", "i4x15", "60", "腕 relations", B, R_, "agents/state.py:695・relations.py:737"),
    _s("agents", "rel_last", "i4x15", "60", "腕 relations", N_, R_, "agents/state.py:697・AST: 読み 0(表の行の一部・将来の読み手)"),
    _s("agents", "rel_n", "u2x15", "30", "腕 relations", B, R_, "agents/state.py:699・relations.py:738"),
    # ---- cells(5 列・world/state.py:121-130) ----
    _s("cells", "density", "i4", "4", "既定", B, V_, "world/state.py:121・resolve.py:1487,1511(agents.cell から毎 tick 再計算)"),
    _s("cells", "density_stage", "u1", "1", "既定", B, V_, "world/state.py:123・salient.py:484・presence.py:1715"),
    _s("cells", "noise_stage", "u1", "1", "既定", B, V_, "world/state.py:125・world/state.py:418・renderer.py:1219"),
    _s("cells", "open_count", "i4", "4", "既定", N_, V_, "world/state.py:128・AST: 読み 0(open_count_per_cell(tick) から導出)"),
    _s("cells", "b4_hash", "u8", "8", "既定", N_, V_, "world/state.py:130・world/state.py:221(プロパティの呼び手 0)",
       allow=_ALLOW_B4),
    # ---- pois(9 列・world/state.py:134-150) ----
    _s("pois", "cell", "i4", "4", "既定", B, V_, "world/state.py:134・資産"),
    _s("pois", "node", "i4", "4", "既定", B, V_, "world/state.py:136・資産"),
    _s("pois", "stock", "i4", "4", "既定", B, R_, "world/state.py:138・resolve.py:2167"),
    _s("pois", "price", "i4", "4", "既定", B, V_, "world/state.py:140・resolve.py:2166(資産・ラン中不変)"),
    _s("pois", "revenue", "i8", "8", "既定", D_, R_, "world/state.py:142・run.py:1118,3993(保存則の検査とラン要約だけ)",
       allow=_ALLOW_REVENUE, note="保存則の項(再開で 0 に戻すと保存則が壊れる)"),
    _s("pois", "capacity", "i4", "4", "既定", B, V_, "world/state.py:144・run.py:3316 → commit.py:413"),
    _s("pois", "open_from", "i2", "2", "既定", B, V_, "world/state.py:146・world/state.py:393・renderer.py:1546"),
    _s("pois", "open_to", "i2", "2", "既定", B, V_, "world/state.py:148・world/state.py:393"),
    _s("pois", "open_now", "i1", "1", "既定", B, R_, "world/state.py:150・opening.py:181・world/state.py:389"),
    # ---- 知覚 SoA(5 列・perception/state.py:98-108・runner.salient.pstate) ----
    _s("perception", "heading", "u1", "1", "既定(知覚 SoA)", N_, V_, "perception/state.py:98・salient.py:205-214,400-414",
       allow=_ALLOW_HEADING, note="親の宣言: 事象の直前に毎回貼り直す派生の値なので behavior-hash に入れない"),
    _s("perception", "task_flag", "u1", "1", "既定(知覚 SoA)", N_, V_, "perception/state.py:100・salient.py:205-214",
       allow=_ALLOW_TASK, note="親の宣言: heading と同じ"),
    _s("perception", "last_b2_hash", "u8", "8", "既定(知覚 SoA)", N_, X_, "perception/state.py:103・宣言のみ(A4 で消す)", dead=True),
    _s("perception", "last_b4_hash", "u8", "8", "既定(知覚 SoA)", N_, X_, "perception/state.py:105・宣言のみ(A4 で消す)", dead=True),
    _s("perception", "invocation_distance", "u2", "2", "単体ベンチの条件付き", N_, X_, "perception/state.py:108・宣言のみ",
       dead=True),
)


# ---------------------------------------------------------------- 外の状態(65 行)
def _o(n: int, name: str, where: str, dtype: str, behavior: str, restore: str, items: Iterable[str], *,
       skip: Iterable[str] = (), note: str = "", ordered: bool = False) -> LedgerRow:
    return LedgerRow(key=f"O{n}", name=name, place=EXTERNAL, dtype=dtype, nbytes="", alloc="",
                     behavior=behavior, restore=restore, dead=False, basis=where,
                     items=tuple(items), hash_skip=tuple(skip), note=note, ordered=ordered)


_EXT: tuple[LedgerRow, ...] = (
    _o(1, "ActivityLayer text・until_kind", "activity.py:178-179", "list[str]・配列(体数)", B, R_,
       ("act_layer.text", "act_layer.until_kind"), note="今の activity_hash に入る"),
    _o(2, "ActivityLayer text_id・_texts・_text_ids・_digest_cache", "activity.py:181-184", "intern 表", N_, V_,
       ("act_layer.text_id", "act_layer._texts", "act_layer._text_ids", "act_layer._digest_cache"),
       skip=("act_layer._digest_cache",), note="_digest_cache はキャッシュ=中身は full に入れない"),
    _o(3, "ActivityLayer _bt_agent・_bt_tick・_bt_start", "activity.py:189-191", "予定の表", N_, V_,
       ("act_layer._bt_agent", "act_layer._bt_tick", "act_layer._bt_start")),
    _o(4, "IntentLayer _payload", "intent.py:139", "dict", B, R_, ("intent_layer._payload",),
       note="今の activity_hash に入る(intent.py:471-482)"),
    _o(5, "IntentLayer _proposals・_executing・_kept_walk", "intent.py:135-141", "tick の中だけ", N_, X_,
       ("intent_layer._proposals", "intent_layer._executing", "intent_layer._kept_walk")),
    _o(6, "IntentLayer stats・ticks_sum・ticks_n", "intent.py:142-144", "計数", D_, X_,
       ("intent_layer.stats", "intent_layer.ticks_sum", "intent_layer.ticks_n")),
    _o(7, "FamiliarityLayer prev_cell", "familiarity.py:168,253", "i8・8 B/体", B, R_, ("fam_layer.prev_cell",),
       note="無いと tick 0 に全員が「入った」扱い"),
    _o(8, "MemoryLayer gist・_gist_order", "memory.py:242-243", "dict(40 字)", B, R_,
       ("mem_layer.gist", "mem_layer._gist_order"), ordered=True,
       note="A2 (b)・描画 B5。_gist_order は OrderedDict で popitem(last=False)=古い順に落とす(memory.py:585-590)=順を保つ"),
    _o(9, "MemoryLayer _session_key・_gist_done", "memory.py:245-246", "dict・set", B, R_,
       ("mem_layer._session_key", "mem_layer._gist_done")),
    _o(10, "MemoryLayer _next_session・_next_join", "memory.py:247,257", "整数", B, R_,
       ("mem_layer._next_session", "mem_layer._next_join")),
    _o(11, "MemoryLayer _target・stats・recall_stats", "memory.py:240,248,252", "tick の中・計数", D_, X_,
       ("mem_layer._target", "mem_layer.stats", "mem_layer.recall_stats")),
    _o(12, "StoreMemory stats", "store_memory.py:207", "計数", D_, X_, ("mem_layer.store.stats",)),
    _o(13, "StoreChoice choice_poi・choice_reason・stats・by_hour", "store_choice.py:105-110", "配列・計数", D_, X_,
       ("poi_resolver.store_choice.choice_poi", "poi_resolver.store_choice.choice_reason",
        "poi_resolver.store_choice.stats", "poi_resolver.store_choice.by_hour")),
    _o(14, "StoreChoice _b_tick・_b_off", "store_choice.py:97-99", "予定の表", N_, V_,
       ("poi_resolver.store_choice._b_tick", "poi_resolver.store_choice._b_off")),
    _o(15, "WomExtractor stats・top・unmatched_words", "wom.py:244-246", "Counter", D_, X_,
       ("wom.stats", "wom.top", "wom.unmatched_words")),
    _o(16, "RelationLayer _prev_cell", "relations.py:646,1003", "i4・4 B/体", B, R_, ("rel_layer._prev_cell",)),
    _o(17, "RelationLayer _acq_until", "relations.py:644,986", "i4 体×k・60 B/体", B, R_, ("rel_layer._acq_until",)),
    _o(18, "RelationLayer _co_since・_co_day・_co_active", "relations.py:635-637,938-939", "i4/i2 体×k・90 B/体+可変", B, R_,
       ("rel_layer._co_since", "rel_layer._co_day", "rel_layer._co_active")),
    _o(19, "RelationLayer _invite_salt・chosen_count・origin_of・stats ほか", "relations.py:628-633,826,884-895",
       "設定・計数・tick の中", D_, X_,
       ("rel_layer._invite_salt", "rel_layer.chosen_count", "rel_layer.origin_of", "rel_layer.stats",
        "rel_layer.init_audit", "rel_layer.wall"),
       note="10b-2: init_audit(初期化の控え・秒は非決定)・wall(壁時計)を「ほか」に足した"),
    _o(20, "ClassicalPolicy _prev", "classical.py:371", "i8・8 B/体", B, R_, ("classical._prev",),
       note="A2 (b): 乗数 m_prev が 1 でないときだけ読む"),
    _o(21, "ClassicalPolicy _gate_hazard(EnergyLayer meal_reset と同じ配列)", "classical.py:390・energy.py:804",
       "f4・4 B/体", B, R_, ("classical._gate_hazard",)),
    _o(22, "ClassicalPolicy _condition・_tick・_eating_tick・_eating_cells", "classical.py:372-378",
       "tick の中・キャッシュ", N_, X_,
       ("classical._condition", "classical._tick", "classical._eating_tick", "classical._eating_cells"),
       note="10d: _ipf_cache は O90 へ(最初に引いた時の状態から作る覚え書き=作り直せない)"),
    _o(23, "ClassicalPolicy _b_tick・_b_off・counts・by_hour", "classical.py:357", "予定の表・計数", N_, V_,
       ("classical._b_tick", "classical._b_off", "classical.counts", "classical.by_hour"),
       skip=("classical.counts", "classical.by_hour"),
       note="材料は「導出できる(表)・捨ててよい(計数)」。計数は full に入れない"),
    _o(24, "ClassicalPolicy home_cell・acq_fn", "classical.py:344,385", "設定・関数", N_, V_,
       ("classical.home_cell", "classical.acq_fn"), skip=("classical.acq_fn",),
       note="acq_fn は関数(配線)=中身は full に入れない"),
    _o(25, "ClassicalChooser last_habit・stats", "chooser.py:180,189", "控え・計数", D_, X_,
       ("poi_resolver.chooser.last_habit", "poi_resolver.chooser.stats")),
    _o(26, "TargetResolver _cat_mask_cache・stats・entropy_sum・named_closed・move_stats",
       "poi_target.py:270,373,472,536,763", "キャッシュ・計数", D_, X_,
       ("poi_resolver._cat_mask_cache", "poi_resolver.stats", "poi_resolver.entropy_sum",
        "poi_resolver.move_stats"),
       note="材料は「導出できる・捨ててよい」。キャッシュは作り直しで空・計数は捨てる=捨ててよいに寄せた(実行役の判断)"),
    _o(27, "EnergyLayer bmr", "energy.py:806・resolve.py:1182", "配列(体数)", B, V_, ("energy.bmr",),
       note="weight_kg から導出"),
    _o(28, "EnergyLayer meal_bits・n_meals・n_snacks・counts・intake_kcal・meal_start_*・stage_ticks*",
       "energy.py:810-831", "配列・計数", D_, X_,
       ("energy.meal_bits", "energy.n_meals", "energy.n_snacks", "energy.counts", "energy.intake_kcal",
        "energy.meal_start_home", "energy.meal_start_in", "energy.meal_start_out", "energy.snack_start",
        "energy.stage_ticks", "energy.stage_ticks_awake_by_hour"),
       note="日の締めで読み終わってから 0 に戻す宣言(日の途中の再開なら要るに変わる)"),
    _o(29, "OutOfAreaMeals の予定 tick・agent・slot・from_row・_start", "energy.py:610-616", "予定の表", N_, V_,
       ("energy.out_of_area.tick", "energy.out_of_area.agent", "energy.out_of_area.slot",
        "energy.out_of_area.from_row", "energy.out_of_area._start")),
    _o(30, "OutOfAreaMeals の遅らせの表 d_agent・d_slot・d_arm_tick・d_eat_tick・d_wake_min", "energy.py:626-630",
       "予定の表", N_, V_,
       ("energy.out_of_area.d_agent", "energy.out_of_area.d_slot", "energy.out_of_area.d_arm_tick",
        "energy.out_of_area.d_eat_tick", "energy.out_of_area.d_wake_min")),
    _o(31, "OutOfAreaMeals d_armed(就寝中の食事を起床時に回す印)", "energy.py:631,681-688", "bool(行数)", B, R_,
       ("energy.out_of_area.d_armed",), note="親の宣言: 日をまたぐ印として持ち越す(10d の状態に含める)"),
    _o(32, "HomeMeals の予定 tick・agent・slot・_start・home_cell", "energy.py:738-758", "予定の表", N_, V_,
       ("energy.home_meals.tick", "energy.home_meals.agent", "energy.home_meals.slot",
        "energy.home_meals._start", "energy.home_meals.home_cell")),
    _o(33, "HomeMeals n_not_home・n_asleep・OutOfAreaMeals の計数 n_armed ほか", "energy.py:633-639,760", "計数", D_, X_,
       ("energy.home_meals.n_not_home", "energy.home_meals.n_asleep", "energy.out_of_area.n_armed",
        "energy.out_of_area.n_skipped_past_window", "energy.out_of_area.n_deferred_not_out")),
    _o(34, "GroupNormMeter _prev_xy・_pair_keys・_pair_len・計数", "norm_meter.py:111-131", "配列", N_, X_,
       ("norm_meter._prev_xy", "norm_meter._pair_keys", "norm_meter._pair_len", "norm_meter._ctx",
        "norm_meter.n_actions_counted", "norm_meter.n_actions_off_stage", "norm_meter._role_rows",
        "norm_meter.role_result", "norm_meter.role_by_kind", "norm_meter.no_permission_total",
        "norm_meter.cowalk_episodes", "norm_meter._cowalk_pairs_seen", "norm_meter.cowalk_agent_minutes",
        "norm_meter.moving_agent_minutes", "norm_meter.cowalk_ticks_skipped", "norm_meter.cowalk_pairs_max_tick",
        "norm_meter.group_size_minutes", "norm_meter.seconds", "norm_meter.inst_walker_minutes",
        "norm_meter.inst_grouped_minutes", "norm_meter.inst_size_minutes", "norm_meter.inst_group_count",
        "norm_meter.inst_pairs_max_tick", "norm_meter.inst_ticks_skipped", "norm_meter.tick_ms_max",
        "norm_meter.n_ticks"),
       note="計器(読むだけ)。捨ててよい=計器の連続性だけ"),
    _o(35, "PlanExecutor 退出の歩行 _walk_since・_walk_line・_plan_rider・_rewalked・_rewalk_*", "presence.py:715-730",
       "i4 ほか(体数)", B, R_,
       ("presence._walk_since", "presence._walk_line", "presence._plan_rider", "presence._rewalked",
        "presence._rewalk_ids", "presence._rewalk_line", "presence._rewalk_deadline")),
    _o(36, "PlanExecutor _defer_ids・_defer_deadline・_defer_line・_defer_walk・_extra・_skip_depart_at",
       "presence.py:707-711,752-755", "配列・辞書", B, R_,
       ("presence._defer_ids", "presence._defer_deadline", "presence._defer_line", "presence._defer_walk",
        "presence._extra", "presence._skip_depart_at")),
    _o(37, "PlanExecutor _pulled_in_today", "presence.py:756", "bool(体数)", D_, R_, ("presence._pulled_in_today",),
       note="10d: 日の頭で落とす日ごとの印(presence.start_day)。日の途中の再開で要る=required。10d 検収 L5: 読み手は"
            "到着の飛ばしの内訳の計数(O70)だけ=軸 1 を diag に"),
    _o(38, "PlanExecutor ev_*・arrival_*・absent・blocks", "presence.py:661-666,990-1108", "予定の表", N_, V_,
       ("presence.ev_tick", "presence.ev_agent", "presence.ev_type", "presence.ev_arg", "presence.ev_act",
        "presence.ev_place", "presence.arrival_train_e1", "presence.arrival_tick", "presence.arrival_cell",
        "presence.arrival_train", "presence.absent", "presence.blocks")),
    _o(39, "ConversationManager sessions・_of_agent・_refusal_until・_next_id・pending_invites・_pair_invite_until・"
           "_speaker_invite_until", "conversation.py:280-313", "dataclass・辞書", B, R_,
       ("conv.sessions", "conv._of_agent", "conv._refusal_until", "conv._next_id", "conv.pending_invites",
        "conv._pair_invite_until", "conv._speaker_invite_until"),
       ordered=True,
       note="直列化の書き手=engine.state_hashes.to_state。sessions・pending_invites の走査の順が話し手と被招待の"
            "起床の順になる(conversation.py:617,627)=順を保つ"),
    _o(40, "ConversationManager join_events", "conversation.py:280-313", "list", B, R_, ("conv.join_events",),
       note="A2 (b)・記憶の腕が _next_join で読む"),
    _o(41, "ConversationManager origin_counts ほかの計数", "conversation.py:280-313", "計数", D_, X_,
       ("conv.origin_counts", "conv.n_ignored_invites", "conv.n_gate_rejected", "conv.n_invites",
        "conv.n_accepted", "conv.n_declined", "conv.n_pending_expired", "conv.n_invite_refractory_blocked",
        "conv.n_blocks", "conv.n_backchannels", "conv.n_interrupts", "conv.closed_by_reason", "conv.ignored_events",
        "conv.size_hist")),
    _o(42, "Arbiter _pending・_pool・queue・_last_tick", "arbiter.py:535-543", "配列・float・辞書", B, R_,
       ("arbiter._pending", "arbiter._pool", "arbiter.queue", "arbiter._last_tick")),
    _o(43, "run_day の局所 pending(適用待ちの応答)", "run.py:2696", "list[13 要素の組]", B, R_, ("run_day.pending",),
       note="10b で組に発射の tick と call_id を足した(13 要素)。直列化の書き手=to_state"),
    _o(44, "run_day の局所 fleet_deferred・fleet_waiting・replay_inbox", "run.py:2393-2402", "list・set・dict", B, R_,
       ("run_day.fleet_deferred", "run_day.fleet_waiting", "run_day.replay_inbox"), note="A2 (b)・艦隊と再生のランだけ"),
    _o(45, "ChangeDetector _prev_raw", "change_detect.py:274,299", "i4 セル×4", B, R_, ("detector._prev_raw",),
       note="None だと日の頭に全セル起床"),
    _o(46, "SalientProcess rng・event_seen_tick・budget", "salient.py:153-176", "Generator・i4 体数", B, R_,
       ("runner.salient.rng", "runner.salient.event_seen_tick", "runner.salient.budget"),
       note="10c: rng は --rng-scheme stateful(既定)だけ Generator。counter では None(保存するものが無い)"),
    _o(47, "PublicServiceDispatchProcess rng・pending", "civic.py:116-117", "Generator・list", B, R_,
       ("runner.dispatch.rng", "runner.dispatch.pending"),
       note="10c: rng は --rng-scheme stateful(既定)だけ Generator。counter では None(保存するものが無い)"),
    _o(48, "HotelProcess rooms_occupied・bed_cell", "civic.py:271,278", "配列", B, R_,
       ("runner.hotel.rooms_occupied", "runner.hotel.bed_cell")),
    _o(49, "LargeEventProcess _inside", "civic.py:449", "配列", B, R_, ("runner.large_event._inside",)),
    _o(50, "RailProcess occupancy・peak_ratio・_return_queue・_inbound・_inbound_ready", "rail.py:283-298", "配列・辞書", B, R_,
       ("runner.rail.occupancy", "runner.rail.peak_ratio", "runner.rail._return_queue", "runner.rail._inbound",
        "runner.rail._inbound_ready")),
    _o(51, "CrowdProcess queue_action", "crowd.py:184", "i1 体数", B, R_, ("runner.crowd.queue_action",)),
    _o(52, "ShelfRestockProcess backroom・_acted_today", "goods_flow.py:171,182", "配列", B, R_,
       ("runner.shelf.backroom", "runner.shelf._acted_today")),
    _o(53, "WasteCollection _cursor・waste_g_collected/StreetCleaning litter_g・swept_g", "goods_flow.py:426-432,565-568",
       "配列・float", N_, R_,
       ("runner.waste._cursor", "runner.waste.waste_g_collected", "runner.street_cleaning.litter_g",
        "runner.street_cleaning.swept_g", "runner.street_cleaning._cursor"),
       note="物の流れの続き・保存則の項(10b-2: 清掃の巡回の位置 _cursor を足した)"),
    _o(54, "RoadWorks blocked_cells・occupied_edges", "logistics.py:285-286", "配列", N_, R_,
       ("runner.road_works.blocked_cells", "runner.road_works.occupied_edges"), note="工事の続き"),
    _o(55, "LastMile delivered・_cum/BusTaxi・Traffic(cell_hourly・cell_vehicles)・Infra(power_kwh)・Press・Opening・"
           "DeliveryInbound の計数", "logistics.py:121-124,211・traffic.py:100-103・civic.py:200,382・opening.py:127-129・"
       "goods_flow.py:346-349", "計数・日ごとの場", N_, V_,
       ("runner.last_mile.delivered", "runner.last_mile._cum", "runner.traffic.cell_hourly",
        "runner.traffic.cell_vehicles", "runner.infra.power_kwh", "runner.delivery_inbound.delay_minute"),
       skip=("runner.last_mile.delivered", "runner.traffic.cell_vehicles", "runner.infra.power_kwh"),
       note="材料は「捨ててよい(計数)・導出できる(日ごとの場と遅れの表)」。計数は full に入れない(実行役の判断)"),
    _o(56, "EnvironmentProcess replay_date・stratum・_row・_shade", "environment.py:144-157", "値", B, V_,
       ("runner.environment.replay_date", "runner.environment.stratum", "runner.environment._row",
        "runner.environment._shade"), note="seed と日番号から選ぶ(10a で日ごとに進める)"),
    _o(57, "MoneyLedger _lines・_day", "economy/ledger.py:222-269", "5 科目 × 6 部門の配列", B, R_,
       ("ledger.money._lines", "ledger.money._day"), note="世帯の現金は agents.money と同じ配列"),
    _o(58, "MoneyLedger 生ログのリング(中身)", "economy/ledger.py:222-269・:662-690",
       "24 B/行・容量 N 比例(下限 16,384)", N_, X_,
       ("ledger.money._raw_tick", "ledger.money._raw_ps",
        "ledger.money._raw_pi", "ledger.money._raw_qs", "ledger.money._raw_qi", "ledger.money._raw_amt",
        "ledger.money._raw_code"),
       note="K16 の既定案(① の記録でファイルに出す前提)。10d: 位置・_snap・_flow_daily は O92 へ(位置だけは要る)"),
    _o(59, "GoodsLedger _shelf・_bin・_sold_today・_day", "economy/goods.py:330-406", "配列", B, R_,
       ("ledger.goods._shelf", "ledger.goods._bin", "ledger.goods._sold_today", "ledger.goods._day")),
    _o(60, "GoodsLedger 配達ログのリング", "economy/goods.py:936-958", "16 B/行", N_, X_,
       ("ledger.goods._dl_tick", "ledger.goods._dl_poi", "ledger.goods._dl_slot", "ledger.goods._dl_qty",
        "ledger.goods._dl_code"),
       note="K16 の既定案。10d: 位置は O93 へ(位置だけは要る)"),
    _o(61, "WorldProcessRunner log(ActualLog)", "world/processes/actual_log.py:162-166", "31 B/行(見積り)", N_, X_,
       ("runner.log",), note="K16 の既定案"),
    _o(62, "UndefinedActionRegistry log・counts・precedents", "llm/undefined.py:697-705", "辞書", N_, X_,
       ("undefined.log", "undefined.counts", "undefined.precedents"), note="run_day は裁定器なし=効かない"),
    _o(63, "PerceptionRenderer のキャッシュ _b1_cache〜_b4_cache・_rank_cell_cache・_acq_cache・_tickc",
       "perception/renderer.py:1115,1146-1152", "キャッシュ", N_, V_,
       ("renderer._b1_cache", "renderer._b2_cache", "renderer._b3_cache", "renderer._b4_cache",
        "renderer._rank_cell_cache", "renderer._acq_cache", "renderer._tickc"),
       skip=("renderer._b1_cache", "renderer._b2_cache", "renderer._b3_cache", "renderer._b4_cache",
             "renderer._rank_cell_cache", "renderer._acq_cache", "renderer._tickc"),
       note="描画の派生のキャッシュ=中身は full に入れない(作り直しで空になる)"),
    _o(64, "PerceptionRenderer の口 acquaintance_fn・memory_recall・session_partner_fn・named_closed_lookup・"
           "signage_exposures", "perception/renderer.py:1171 ほか・run.py の配線", "関数・tick の中", N_, X_,
       ("renderer.acquaintance_fn", "renderer.memory_recall", "renderer.session_partner_fn",
        "renderer.named_closed_lookup", "renderer.signage_exposures")),
    _o(65, "LLMBridge・TapeWriter・FleetBridge の計数・行・処理中の呼", "llm_bridge.py:537-554・tape.py:242-278・llm/fleet.py",
       "計数・ファイル", N_, X_, (), note="テープはファイルに出る・処理中の呼は O44 と同じ扱い"),
    # ---- 10b-2(親の答え 1): 持ち主のクラスの属性の棚卸しで見つけた状態(tick をまたいで残る値) ----
    _o(66, "ActivityLayer の計数", "activity.py", "計数", D_, X_,
       ("act_layer.n_set", "act_layer.n_expiry_candidates", "act_layer.n_cell_suppressed",
        "act_layer.n_arrival_expired", "act_layer.n_partner_expired", "act_layer.n_fail_immediate",
        "act_layer.n_leave_expired", "act_layer.n_wander_steps", "act_layer.n_wander_bad",
        "act_layer.n_intent_moves", "act_layer.kind_counts")),
    _o(67, "FamiliarityLayer stats", "familiarity.py", "Counter", D_, X_, ("fam_layer.stats",)),
    _o(68, "StoreChoice first_by_reason・visits_by_reason", "store_choice.py", "計数", D_, X_,
       ("poi_resolver.store_choice.first_by_reason", "poi_resolver.store_choice.visits_by_reason")),
    _o(69, "ClassicalPolicy n_calls", "classical.py", "計数", D_, X_, ("classical.n_calls",)),
    _o(70, "PlanExecutor の計数と時別の控え", "presence.py", "計数・list", D_, X_,
       tuple(f"presence.{a}" for a in (
           "n_arrivals", "n_departures", "n_arrive_skipped", "n_arrive_skipped_in_area", "n_arrive_skipped_pulled",
           "n_returned_to_block", "n_depart_skipped", "n_exit_deferred", "n_exit_forced", "n_shopping_interrupted",
           "n_queue_balked", "n_pulled_in", "n_pushed_out", "n_departed_by_llm", "n_depart_dropped", "n_rearmed",
           "n_placed_at_start", "n_gate_arrivals", "n_spread_moved", "n_spread_overflow", "sleep_counts",
           "sample_hours", "sample_in_area", "match_in_num", "match_in_den", "match_out_num", "match_out_den",
           "in_area_by_hour", "wake_in_area_by_hour", "n_home_out_slept_inside", "n_exit_walk_started",
           "n_exit_walk_waiting_at_start", "n_exit_walk_boarded", "n_exit_walk_departed", "n_exit_walk_gone",
           "n_exit_walk_restarted", "n_exit_rewalk_queued", "n_exit_rewalk_started", "n_exit_rewalk_forced",
           "n_exit_rewalk_gone", "n_exit_lost_final", "n_exit_too_far", "n_exit_lost", "n_exit_lost_deferred",
           "n_exit_gate_immediate", "n_exit_no_platform", "n_walk_wakes_suppressed", "n_walk_calls",
           "walk_minutes", "lost_why", "fallback_minutes", "exit_cell_by_hour", "platform_cell_by_hour",
           "exit_stage_max_by_hour"))),
    _o(71, "Arbiter の計数", "arbiter.py", "計数", D_, X_,
       ("arbiter.budget_unused", "arbiter._diag_total", "arbiter._outside_total", "arbiter._merged_total",
        "arbiter._sleep_total", "arbiter.n_calls_total")),
    _o(72, "SalientProcess の計数", "processes/salient.py", "計数", D_, X_,
       ("runner.salient.n_events", "runner.salient.n_noticed", "runner.salient.n_collapse",
        "runner.salient.n_over_cap", "runner.salient.n_broadcast_lines")),
    _o(73, "世界の過程と実行器の計数", "processes/*.py・processes/runner.py", "計数", D_, X_,
       ("runner.dispatch.n_dispatched", "runner.dispatch.n_arrived", "runner.dispatch.delay_minutes_total",
        "runner.hotel.n_checkin", "runner.hotel.n_no_bed", "runner.hotel.n_checkout",
        "runner.large_event.n_in", "runner.large_event.n_out", "runner.press.n_releases", "runner.infra.water_m3",
        *(f"runner.rail.{a}" for a in (
            "n_departures", "n_arrivals", "n_departed_riders", "n_fare_rejected", "n_left_behind",
            "n_board_applicants", "n_board_intent", "n_board_walking", "n_board_unreachable", "n_board_waiting",
            "n_board_timeout", "n_board_dropped", "n_boarded_from_queue", "n_boarded_plan_exit",
            "n_board_waiting_plan_exit", "n_return_scheduled", "n_return_arrived", "n_no_return",
            "n_return_no_train")),
        "runner.crowd.n_released", "runner.crowd.n_balked", "runner.crowd.peak_queue", "runner.crowd.peak_occupancy",
        "runner.shelf.n_role_actions", "runner.shelf.n_fallback", "runner.shelf.n_no_backroom", "runner.shelf.n_rejected",
        "runner.shelf.units_restocked", "runner.shelf.yen_paid", "runner.delivery_inbound.n_runs",
        "runner.delivery_inbound.n_delayed", "runner.delivery_inbound.units_delivered", "runner.waste.n_stops",
        "runner.waste.n_bin_rows", "runner.waste.n_consumed", "runner.waste.consumed_g",
        "runner.street_cleaning.n_swept_cells", "runner.last_mile.n_batches", "runner.bus_taxi.n_arrivals",
        "runner.road_works.n_started", "runner.road_works.n_finished", "runner.traffic.daily_vehicle_km",
        "runner.opening.n_role_actions", "runner.opening.n_fallback", "runner.opening.n_events",
        "runner.environment.n_updates", "runner.environment.shadow_missing", "runner.n_steps",
        "runner.phase_seconds"),
       note="phase_seconds は壁時計(非決定)"),
    _o(74, "RailProcess arrival_train・external_line(帰りの便の予約印・域外居住者の路線)", "processes/rail.py:293-294,405-406,459,502",
       "i8 体数", B, R_, ("runner.rail.arrival_train", "runner.rail.external_line"),
       note="初期化で域外居住者に割り当て、乗車と帰着で書き換える"),
    _o(75, "CrowdProcess occupancy・queue_len・flow・flow_dir8・coherence", "processes/crowd.py:165-180,252-293",
       "i8/u1/f8 POI・セル数", B, U_,
       ("runner.crowd.occupancy", "runner.crowd.queue_len", "runner.crowd.flow", "runner.crowd.flow_dir8",
        "runner.crowd.coherence"),
       note="毎 tick の step で SoA から作り直すが、作り直す前(次の tick の入店の判定)に読む口があるかは未確認=不明"),
    _o(76, "EnvironmentProcess daylight・heat_stage・wbgt", "processes/environment.py:158-160,267-278", "値", B, V_,
       ("runner.environment.daylight", "runner.environment.heat_stage", "runner.environment.wbgt"),
       note="5 分刻みの更新で気象の行と時刻から作り直す(更新の間も読まれる)"),
    _o(77, "MoneyLedger _flow・_last_change_day・_snap0・_last_close(センサスと保存則の項)", "economy/ledger.py:231-244,657-740",
       "配列・DayClose", D_, R_,
       ("ledger.money._flow", "ledger.money._last_change_day", "ledger.money._snap0", "ledger.money._last_close"),
       note="_last_change_day は economy/checks.py だけが読む"),
    _o(78, "MoneyLedger rejections", "economy/ledger.py", "計数", D_, X_,
       ("ledger.money.rejections",), note="10d: n_transfers は O92 へ(日次センサスの行が読む累計)"),
    _o(79, "GoodsLedger _shelf_age・_household_sku", "economy/goods.py:367-371,550,832-886", "配列", B, R_,
       ("ledger.goods._shelf_age", "ledger.goods._household_sku"),
       note="棚の古さ=廃棄の判定・世帯の在庫=消費の可否(goods.py:550)"),
    _o(80, "GoodsLedger の保存則の項(_row_sku・_waste_sku・_inflow・_outflow・_residual・_open_stock・廃棄の g)",
       "economy/goods.py:365-381", "配列・float・list", D_, R_,
       ("ledger.goods._row_sku", "ledger.goods._waste_sku", "ledger.goods._inflow", "ledger.goods._outflow",
        "ledger.goods._residual", "ledger.goods._open_stock", "ledger.goods.store_waste_g_total",
        "ledger.goods._day_waste_g", "ledger.goods._waste_g_daily", "ledger.goods._last_close")),
    _o(81, "GoodsLedger n_moves・rejections", "economy/goods.py", "計数", D_, X_,
       ("ledger.goods.n_moves", "ledger.goods.rejections")),
    _o(82, "UndefinedActionRegistry proposals・vocabulary_extension・_agents", "llm/undefined.py:699-704,729-765",
       "辞書", N_, U_, ("undefined.proposals", "undefined.vocabulary_extension", "undefined._agents"),
       note="run_day は裁定器なし=提案も語彙の拡張も起きない見込み。拡張が立てば解析に効く=不明"),
    _o(83, "UndefinedActionRegistry の計数", "llm/undefined.py", "計数", D_, X_,
       ("undefined.n_dropped_records", "undefined.n_adjudication_calls", "undefined.n_dictionary_mapped")),
    _o(84, "PerceptionRenderer の計数", "perception/renderer.py", "計数", D_, X_,
       tuple(f"renderer.{a}" for a in (
           "memory_lines", "memory_items", "memory_line_tokens", "memory_items_dropped_for_budget",
           "memory_items_dropped_for_channel", "memory_lines_over_budget", "near_order_ties", "near_tie_breaks",
           "near_tie_candidates", "cache_hits", "cache_misses", "renders", "truncation_count", "intent_lines",
           "intent_lines_over_budget", "named_closed_notes", "signage_gate_draws", "signage_gate_shown",
           "signage_by_kind", "signage_effective_p"))),
    _o(85, "LLMBridge _interned(テープへ書いた共有ブロック)", "engine/llm_bridge.py:554,771-774", "set", N_, R_,
       ("bridge._interned",), note="テープの block 行を 1 回だけ書く印。10d: 記録の継続に要る=required(再開のテープは"
                                   "新しい block だけを持ち、親のテープと連結して読む)"),
    _o(86, "LLMBridge の計数", "engine/llm_bridge.py", "計数", D_, X_,
       tuple(f"bridge.{a}" for a in (
           "n_calls", "n_parse_errors", "n_parse_errors_strict", "n_label_alias", "n_positional",
           "n_dictionary_mapped", "n_unknown_action", "n_undefined_mapped", "n_role_actions", "n_tape_misses",
           "n_deferred", "n_tape_rows"))),
    _o(87, "TapeWriter の書き出し待ちの行と計数", "engine/tape.py", "list・計数", N_, X_,
       ("bridge.tape._rows", "bridge.tape._blocks", "bridge.tape._n_written", "bridge.tape._n_deferred"),
       note="テープはファイルに出る(O65)"),
    _o(88, "FleetBridge _interned", "llm/fleet.py", "set", N_, R_, ("fleet_bridge._interned",),
       note="LLMBridge._interned と同じ(10d: required)"),
    _o(89, "FleetBridge の計数", "llm/fleet.py", "計数", D_, X_,
       tuple(f"fleet_bridge.{a}" for a in (
           "n_debug_rows", "n_debug_skipped", "n_calls", "n_parse_errors", "n_parse_errors_strict", "n_label_alias",
           "n_positional", "n_dictionary_mapped", "n_unknown_action", "n_undefined_mapped", "n_role_actions",
           "n_deferred", "n_deferred_rows", "n_tape_rows"))),
    # ---- 10d(親の答え 1): 日中の再開と日の境目の再開の試験で見つけた保存し忘れ(元の行から移した) ----
    _o(90, "ClassicalPolicy _ipf_cache(15 分帯ごとの c_t の覚え書き)", "classical.py:379,523-544", "dict", B, R_,
       ("classical._ipf_cache",),
       note="10d: 元 O22(キャッシュ)。帯ごとに最初に引いた時の状態(起きて範囲内の体)から作り、その日の中は使い回す"
            "=作り直すと別の値。鍵に日を足した(日ごとに作る)"),
    _o(91, "ConversationManager n_opened(開いたセッションの数)", "conversation.py・memory.py:713", "整数", B, R_,
       ("conv.n_opened",),
       note="10d: 元 O41(計数)。記憶の層が「どこまで見たか」(_next_session)と比べて読む=挙動に効く。"
            "AST の検査は SoA の列だけを見るので、外の状態の属性の読み手は検出しない(検査の穴=README)"),
    _o(92, "MoneyLedger 締めの基準と生ログの位置(_snap・_flow_daily・_raw_pos・_raw_head・_day_marks・n_raw_dropped・"
           "n_transfers)", "economy/ledger.py:222-269・:713-741・economy/census.py:253", "配列・list・整数", D_, R_,
       ("ledger.money._snap", "ledger.money._flow_daily", "ledger.money._raw_pos", "ledger.money._raw_head",
        "ledger.money._day_marks", "ledger.money.n_raw_dropped", "ledger.money.n_transfers"),
       note="10d: 元 O58・O78。_snap は次の日の締めの d_cash(センサスの検算①)の基準・位置は締めの raw_rows_kept"
            "(_last_close)・n_transfers はセンサスの行。K16 の既定案「リングは含めない」を「中身は含めないが位置は要る」"
            "に直した。位置は全部まとめて戻す(一部だけだと成長の検査で実測が負になる)"),
    _o(93, "GoodsLedger 配達ログの位置(_dl_pos・_dl_head・_dl_marks・n_delivery_dropped)", "economy/goods.py:895-901",
       "整数・list", D_, R_,
       ("ledger.goods._dl_pos", "ledger.goods._dl_head", "ledger.goods._dl_marks", "ledger.goods.n_delivery_dropped"),
       note="10d: 元 O60。締めの delivery_rows_kept(_last_close)に入る"),
    _o(94, "TargetResolver named_closed(名指しの店の即時閉店の控え)", "poi_target.py:472・run.py:_named_closed_lookup・"
           "perception/renderer.py の B6", "dict", B, R_, ("poi_resolver.named_closed",),
       note="10d 検収 L2: 元 O26(計数・discardable)。描画の B6 が失敗の直後の起床でプロンプトに「(店名は閉店中・"
            "開店の時刻)」を足す=挙動に効く。AST の検査は外の状態の属性の読み手を見ないので捕まらなかった"),
)

#: 状態台帳(163 行)。**読み口はこれと下の関数だけ**。
LEDGER: Final[tuple[LedgerRow, ...]] = _SOA + _EXT


def rows(place: str | None = None) -> tuple[LedgerRow, ...]:
    """台帳の行(``place`` を渡せばその置き場だけ)。"""
    return tuple(r for r in LEDGER if place is None or r.place == place)


def soa_rows(place: str) -> tuple[LedgerRow, ...]:
    if place not in SOA_PLACES:
        raise ValueError(f"place は {SOA_PLACES} のどれか(いま {place!r})")
    return rows(place)


def external_rows() -> tuple[LedgerRow, ...]:
    return rows(EXTERNAL)


def row(key: str) -> LedgerRow:
    for r in LEDGER:
        if r.key == key:
            return r
    raise KeyError(key)


def behavior_excluded(place: str) -> frozenset[str]:
    """behavior-hash で ``state_hash(exclude=…)`` に渡す列名(軸 1 が ``no``/``diag`` の列)。"""
    return frozenset(r.name for r in soa_rows(place) if not r.in_behavior)


def behavior_columns(place: str) -> frozenset[str]:
    return frozenset(r.name for r in soa_rows(place) if r.in_behavior)


def full_excluded(place: str) -> frozenset[str]:
    """full-hash で除く列名(軸 2 が ``discardable`` の列)。"""
    return frozenset(r.name for r in soa_rows(place) if not r.in_full)


def full_items() -> tuple[tuple[str, str], ...]:
    """full-hash に入れる外の状態の ``(行の鍵, 属性の道筋)``(台帳の宣言順)。"""
    out: list[tuple[str, str]] = []
    for r in external_rows():
        if not r.in_full:
            continue
        skip = set(r.hash_skip)
        out.extend((r.key, it) for it in r.items if it not in skip)
    return tuple(out)


def counts() -> dict[str, int]:
    """行の数(記録と試験が読む)。"""
    out = {p: len(rows(p)) for p in SOA_PLACES + (EXTERNAL,)}
    out["soa"] = sum(out[p] for p in SOA_PLACES)
    out["total"] = len(LEDGER)
    return out


# ---------------------------------------------------------------- 持ち主のクラスと除外の一覧(10b-2・親の答え 1)
#: 外の状態の行の持ち主(``run_day`` の ``owners`` からの道筋)→ (``src/shibuya`` からのファイル, クラス名)。
#: ここに載るクラスの属性(``self.x = …`` と dataclass の欄)は、**どれかの行の ``items`` か ``EXCLUDED`` に
#: 必ず載る**(``tests/engine/test_state_ledger_10b.py`` が AST で突き合わせる=新しい状態を足したら宣言する)。
OWNER_CLASSES: Final[dict[str, tuple[str, str]]] = {
    "act_layer": ("engine/activity.py", "ActivityLayer"),
    "intent_layer": ("engine/intent.py", "IntentLayer"),
    "fam_layer": ("engine/familiarity.py", "FamiliarityLayer"),
    "mem_layer": ("engine/memory.py", "MemoryLayer"),
    "mem_layer.store": ("engine/store_memory.py", "StoreMemory"),
    "poi_resolver": ("engine/poi_target.py", "TargetResolver"),
    "poi_resolver.store_choice": ("engine/store_choice.py", "StoreChoice"),
    "poi_resolver.chooser": ("engine/chooser.py", "ClassicalChooser"),
    "wom": ("engine/wom.py", "WomExtractor"),
    "rel_layer": ("engine/relations.py", "RelationLayer"),
    "classical": ("engine/classical.py", "ClassicalPolicy"),
    "energy": ("engine/energy.py", "EnergyLayer"),
    "energy.out_of_area": ("engine/energy.py", "OutOfAreaMeals"),
    "energy.home_meals": ("engine/energy.py", "HomeMeals"),
    "norm_meter": ("engine/norm_meter.py", "GroupNormMeter"),
    "presence": ("engine/presence.py", "PlanExecutor"),
    "conv": ("engine/conversation.py", "ConversationManager"),
    "arbiter": ("engine/arbiter.py", "Arbiter"),
    "detector": ("engine/change_detect.py", "ChangeDetector"),
    "runner": ("engine/processes/runner.py", "WorldProcessRunner"),
    "runner.salient": ("engine/processes/salient.py", "SalientProcess"),
    "runner.dispatch": ("engine/processes/civic.py", "PublicServiceDispatchProcess"),
    "runner.hotel": ("engine/processes/civic.py", "HotelProcess"),
    "runner.large_event": ("engine/processes/civic.py", "LargeEventProcess"),
    "runner.press": ("engine/processes/civic.py", "PressProcess"),
    "runner.infra": ("engine/processes/civic.py", "InfraLoadProcess"),
    "runner.rail": ("engine/processes/rail.py", "RailProcess"),
    "runner.crowd": ("engine/processes/crowd.py", "CrowdProcess"),
    "runner.shelf": ("engine/processes/goods_flow.py", "ShelfRestockProcess"),
    "runner.delivery_inbound": ("engine/processes/goods_flow.py", "DeliveryInboundProcess"),
    "runner.waste": ("engine/processes/goods_flow.py", "WasteCollectionProcess"),
    "runner.street_cleaning": ("engine/processes/goods_flow.py", "StreetCleaningProcess"),
    "runner.last_mile": ("engine/processes/logistics.py", "LastMileProcess"),
    "runner.bus_taxi": ("engine/processes/logistics.py", "BusTaxiProcess"),
    "runner.road_works": ("engine/processes/logistics.py", "RoadWorksProcess"),
    "runner.traffic": ("engine/processes/traffic.py", "TrafficProcess"),
    "runner.opening": ("engine/processes/opening.py", "OpeningProcess"),
    "runner.environment": ("engine/processes/environment.py", "EnvironmentProcess"),
    "runner.log": ("world/processes/actual_log.py", "ActualLog"),
    "ledger.money": ("economy/ledger.py", "Ledger"),
    "ledger.goods": ("economy/goods.py", "GoodsLedger"),
    "undefined": ("llm/undefined.py", "UndefinedActionRegistry"),
    "renderer": ("perception/renderer.py", "Renderer"),
    "bridge": ("engine/llm_bridge.py", "LLMBridge"),
    "bridge.tape": ("engine/tape.py", "TapeWriter"),
    "fleet_bridge": ("llm/fleet.py", "FleetBridge"),
}

#: (ii) キャッシュ・導出。中身は 3 通り: (a) 毎 tick(か事象のある tick)作り直す作業の値・印
#: (b) 中身で引く覚え書き(ラン中残るが、空から始めても同じ鍵で同じ値を作り直す=出力は同じ)
#: (c) 資産・母集団・予定の表から初期化で作る表(ランの間に変わらない)。
#: 構成で同じ道筋に入る別のクラス・子クラス(AST の網羅はこれらの属性も合わせて見る)。
#: 実行時の網羅(``tests/engine/test_state_ledger_10b.py``)はインスタンスの ``vars()`` で見るので、
#: ここに無いクラスが入っても落ちる。
OWNER_ALT_CLASSES: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    "poi_resolver.chooser": (("engine/chooser.py", "NearestChooser"),),
    "ledger.money": (("cli.py", "_HouseholdWalletLedger"),),
}

CACHE: Final[str] = "cache"
CONST: Final[str] = "const"   # (iii) 定数・設定(ランの間に変わらない)
REF: Final[str] = "ref"       # (iv) 参照(他のオブジェクトへの参照・配列のビュー・関数)
EXCLUDE_KINDS: Final[tuple[str, ...]] = (CACHE, CONST, REF)


@dataclass(frozen=True)
class Excluded:
    """台帳の行に入れない属性(``owner`` の ``attrs``・分類 ``kind``・理由)。"""

    owner: str
    attrs: tuple[str, ...]
    kind: str
    reason: str


def _x(owner: str, kind: str, reason: str, *attrs: str) -> Excluded:
    return Excluded(owner, tuple(attrs), kind, reason)


_CFG = "初期化で渡す設定・定数(ランの間に変わらない)"
_REFR = "他のオブジェクトへの参照(その持ち主の側で数える)"
_TAB = "資産・母集団・予定の表から初期化で作る表(ランの間に変わらない=作り直せる)"
_FIELD = "クラスの定数(process_ids・ablation_id など)"
_DAY = "10d: 日の頭で暦の口の日から張り直す値(曜日の行・日の鍵)=再開でも同じ値"

#: 明示の除外の一覧(親の答え 1 の (ii)〜(iv))。
EXCLUDED: Final[tuple[Excluded, ...]] = (
    _x("act_layer", CONST, _CFG, "n", "salt", "minutes_per_tick", "_tpd", "leave_effect"),
    _x("act_layer", CACHE, "ぶらつきの近傍の表(資産から作る)", "_nbr_start", "_nbr_cells"),
    _x("intent_layer", CONST, _CFG, "n", "max_ticks"),
    _x("intent_layer", REF, _REFR, "world"),
    _x("intent_layer", CACHE, _TAB, "_poi_cell"),
    _x("fam_layer", CONST, _CFG, "n", "k", "minutes_per_tick", "d", "p_see", "seed"),
    _x("fam_layer", CACHE, _TAB, "signage_poi_by_cell"),
    _x("fam_layer", REF, "描画の側の関数(配線)", "p_see_fn", "kind_fn"),
    _x("mem_layer", CONST, _CFG, "n", "n_rows", "minutes_per_tick", "d", "w_r", "w_i", "tau",
       "store_recall_scope"),
    _x("mem_layer", REF, "関係辺の層(rel_layer の側で数える)", "relations"),
    _x("mem_layer.store", CONST, _CFG, "n", "n_rows", "minutes_per_tick", "d", "sigma", "decay", "weight",
       "signage"),
    _x("mem_layer.store", CACHE, _TAB, "poi_cell"),
    _x("mem_layer.store", REF, "店の選び手の口(関数)", "visit_hook"),
    _x("poi_resolver", CACHE, _TAB, "_cat", "_sub", "_names", "_names_by_len", "_cat_words", "_cat_exact",
       "_buyable", "_by_cell", "_off", "_skip", "_cell_of_place", "_landmark"),
    _x("poi_resolver", CONST, _CFG, "_rich", "seed", "move_search_radius"),
    _x("poi_resolver", REF, _REFR, "world"),
    _x("poi_resolver.store_choice", REF, _REFR, "memory", "store", "world"),
    _x("poi_resolver.store_choice", CONST, _CFG, "n", "seed", "minutes_per_tick", "ticks_per_hour", "_tpd",
       "intent_max_ticks", "recall_first", "_src_order"),
    _x("poi_resolver.store_choice", CACHE, _TAB, "poi_cell", "price", "walk"),
    _x("poi_resolver.chooser", CONST, _CFG, "p_h", "tau", "name"),
    _x("wom", CONST, _CFG, "source", "n_poi"),
    _x("wom", CACHE, "店名と評価語の辞書(世界と辞書 v0 から作る)", "poi_cell", "cell_dist", "keys", "_by_first",
       "_generic", "_generic_tails", "_cat_tails", "_val_words", "_neg"),
    _x("rel_layer", CONST, _CFG + "(enable_* で 1 回だけ置く値を含む)", "n", "k", "minutes_per_tick", "d", "tau", "s",
       "_co_minutes", "_co_meters", "_acq_pair_ticks"),
    _x("rel_layer", CACHE, "tick の中だけの控え(同セルの辺の集め・知人出現の候補=その tick の中で使い切る)",
       "_hits", "_hits_tick", "_acq_pending"),
    _x("classical", REF, _REFR + "・交際の口(関数)", "agents", "world", "partner_fn"),
    _x("classical", CONST, _CFG, "minutes_per_tick", "_tpd", "_identity", "seed", "prior", "prior_md5",
       "m_place", "m_next", "m_prev", "source", "social", "meal_gate"),
    _x("classical", CACHE, _TAB, "work_cell", "school_cell", "has_work", "_station", "_eatery",
       "_cell_has_eatery"),
    _x("classical", CACHE, "SoA の kind から作る表(導出・10d: 再開では rebuild_derived で戻した SoA から作り直す)",
       "employed"),
    _x("energy", CONST, _CFG, "model", "n_agents"),
    _x("energy", REF, "ClassicalPolicy._gate_hazard と同じ配列(O21 で数える)", "meal_reset"),
    _x("energy", CACHE, _TAB, "poi_intake"),
    _x("energy.out_of_area", CONST, _CFG, "sleep_defer", "_tpd"),
    _x("energy.out_of_area", CACHE, _TAB + "(予定の行の数と並べ替えの索引)", "n_rows", "n_defaults",
       "n_asleep_defaults", "n_deferrable", "_arm_order", "_eat_order", "_arm_start", "_eat_start"),
    _x("energy.home_meals", CONST, _CFG, "_tpd"),
    _x("energy.home_meals", CACHE, _TAB, "n_rows", "n_agents_with_rows"),
    _x("norm_meter", REF, _REFR, "agents"),
    _x("norm_meter", CONST, _CFG, "tick_seconds", "n_station_cells", "role_codes", "_role_word_by_code",
       "_code_words"),
    _x("norm_meter", CACHE, _TAB, "_station_cell"),
    _x("presence", REF, _REFR, "world", "agents", "weekly", "rail", "assets"),
    _x("presence", CONST, _CFG + "・クラスの定数", "seed", "ticks", "exit_mode", "attendance_rate",
       "mode", "derive_rule", "n", "walk_max_ticks", "ablation_id", "process_ids", "_PRESENCE_TYPES",
       "_BOUNDARY_TYPES"),
    _x("presence", CONST, _CFG + "(10d: 出勤率を日ごとに引き直す種別と鍵)", "_kind", "_agent_key"),
    _x("presence", CACHE, "10d: 日の頭で張り直す表の座標(W17 の曜日の行・その日の頭の T・その日の便の範囲)。"
       "暦と日番号から作る=再開でも同じ値", "day_index", "_t0", "_day_trains"),
    _x("presence", CACHE, _TAB + "(管理する体・自宅・方向・路線・開始時の在圏・事象の索引)", "managed", "home_cell",
       "home_out", "_home_shim", "direction_node", "line_of_agent", "in_area_at_start", "_ev_start",
       "n_all_day_outside"),
    _x("presence", CACHE, "この tick に歩き始めた体(tick の中で使い切る)", "walk_started_now"),
    _x("conv", CONST, _CFG + "(重要度上位の体の集合を含む)", "master_seed", "domain", "max_turns",
       "extra_turns_for_important", "max_participants", "accept_probability", "refusal_memory_ticks",
       "silence_ticks", "max_session_ticks", "walk_over_ticks", "topics_per_session", "important", "origin_names"),
    _x("arbiter", CONST, _CFG, "n_agents", "run_salt", "budget", "classes", "_pool_cap"),
    _x("detector", CONST, _CFG, "n_agents", "n_cells"),
    _x("detector", CACHE, "歩行可能面積(資産)と毎 tick 使い回す作業の配列", "walkable_area_m2", "_b1", "_b2", "_b3", "_up",
       "_dn", "_hit", "_any", "_cell_mask", "_wake_buf"),
    _x("runner", REF, _REFR + "(過程の辞書 _procs を含む)", "registry", "world", "agents", "assets", "clock",
       "calendar", "ledger", "presence", "_procs"),
    _x("runner", CONST, _CFG + "・世界側台帳の検査の結果", "master_seed", "day_index", "tick_seconds", "plan_executor",
       "constitution_report", "constitution_ok", "registry_hash", "enabled", "rng_scheme"),
    _x("runner.salient", REF, _REFR + "(知覚 SoA は台帳の perception の 5 行で数える)", "world", "agents", "dispatch",
       "press", "environment", "pstate"),
    _x("runner.salient", CONST, _CFG + "・クラスの定数", "tick_seconds", "master_seed", "day_index", "ablation",
       "d50_scale", "params", "d50_by_kind", "rate", "process_ids", "ablation_id", "rng_scheme"),
    _x("runner.salient", CACHE, "step の頭で空に戻すその tick の事象・行・気づいた体と、セルの索引",
       "events", "cell_lines", "noticed_agents", "_neighbours", "_cell_index_tick", "_order", "_start"),
    _x("runner.dispatch", REF, _REFR, "world", "log"),
    _x("runner.dispatch", CONST, _FIELD + "・" + _CFG, "tick_seconds", "process_ids", "ablation_id", "master_seed",
       "day_index", "rng_scheme"),
    _x("runner.dispatch", CACHE, "10c の counter の k の数え(同じ T の中だけ。T が変わると空に戻す=tick の境目で再開すれば"
       "空から数え直して同じ値。stateful では使わない)", "_k_tick", "_k_next"),
    _x("runner.hotel", REF, _REFR, "world", "agents", "log"),
    _x("runner.hotel", CONST, _FIELD + "・" + _CFG, "tick_seconds", "process_ids", "ablation_id"),
    _x("runner.hotel", CACHE, _TAB, "hotel_poi", "hotel_cell", "rooms_total", "hotel_of_cell", "external_home"),
    _x("runner.large_event", REF, _REFR, "world", "agents", "rail", "presence", "log"),
    _x("runner.large_event", CONST, _FIELD + "・" + _CFG, "tick_seconds", "visitor_delta", "process_ids",
       "ablation_id", "master_seed"),
    _x("runner.large_event", CACHE, _TAB, "venue_cells"),
    _x("runner.press", REF, _REFR, "world", "log"),
    _x("runner.press", CONST, _FIELD + "・" + _CFG + "(発表の文)", "tick_seconds", "line", "strip", "process_ids",
       "ablation_id"),
    _x("runner.infra", REF, _REFR, "world", "agents"),
    _x("runner.infra", CONST, _FIELD + "・" + _CFG, "tick_seconds", "process_ids", "ablation_id"),
    _x("runner.rail", REF, _REFR, "world", "agents", "assets", "calendar", "schedule", "log", "presence", "_weekly"),
    _x("runner.rail", CONST, _FIELD + "・" + _CFG, "master_seed", "day_index", "fare_yen", "plan_executor",
       "process_ids", "ablation_id"),
    _x("runner.rail", CACHE, "時刻表と列車の表(資産と暦から作る)", "lines", "lines_present", "line_cell", "dep_tick",
       "dwell", "train_line", "train_dir", "platform_cell", "capacity100", "cap_pct", "_arr_order", "_arr_start",
       "enter_tick", "_enter_order", "_enter_sorted"),
    _x("runner.rail", CACHE, "10d: 日ごとの便の索引の範囲といまの日の頭の T(日の頭で張り直す=暦と日番号から作る)",
       "_day_starts", "_t0"),
    _x("runner.crowd", REF, _REFR, "world", "agents"),
    _x("runner.crowd", CONST, _FIELD + "・" + _CFG, "tick_seconds", "seat_area_m2", "default_seat_area_m2",
       "process_ids", "ablation_id"),
    _x("runner.crowd", CACHE, "席数の表(資産)と、その tick の入店数(tick の頭で 0 に戻す)", "seats",
       "admitted_this_tick"),
    _x("runner.shelf", REF, _REFR, "world", "agents", "ledger", "log"),
    _x("runner.shelf", CONST, _FIELD + "・" + _CFG, "tick_seconds", "fill_ratio", "process_ids", "ablation_id"),
    _x("runner.shelf", CACHE, _TAB + "(初期の在庫からの容量・発注点・店員)", "capacity", "reorder_point",
       "staff_of_poi"),
    _x("runner.delivery_inbound", REF, _REFR, "world", "ledger", "shelf", "log"),
    _x("runner.delivery_inbound", CONST, _FIELD + "・" + _CFG, "tick_seconds", "master_seed", "process_ids",
       "ablation_id", "plan_spec_id"),
    _x("runner.delivery_inbound", CACHE, _DAY, "day_index"),
    _x("runner.delivery_inbound", CACHE, _TAB, "plan_minute"),
    _x("runner.waste", REF, _REFR, "world", "agents", "ledger", "log"),
    _x("runner.waste", CONST, _FIELD + "・" + _CFG, "tick_seconds", "master_seed", "process_ids", "ablation_id"),
    _x("runner.waste", CACHE, _TAB, "route"),
    _x("runner.street_cleaning", REF, _REFR, "world", "agents"),
    _x("runner.street_cleaning", CONST, _FIELD + "・" + _CFG, "tick_seconds", "process_ids", "ablation_id"),
    _x("runner.last_mile", REF, _REFR, "world", "log"),
    _x("runner.last_mile", CONST, _FIELD + "・" + _CFG, "tick_seconds", "process_ids", "ablation_id"),
    _x("runner.last_mile", CACHE, _TAB, "bbox_share", "parcels_today", "parcels_per_cell", "_hours"),
    _x("runner.bus_taxi", REF, _REFR, "world", "assets", "log"),
    _x("runner.bus_taxi", CONST, _FIELD + "・" + _CFG, "tick_seconds", "headway", "process_ids", "ablation_id",
       "plan_spec_id"),
    _x("runner.bus_taxi", CACHE, _TAB, "stop_cell", "phase", "n_departures_planned"),
    _x("runner.road_works", REF, _REFR, "world", "assets", "log"),
    _x("runner.road_works", CONST, _FIELD + "・" + _CFG, "tick_seconds", "process_ids", "ablation_id",
       "plan_spec_id", "master_seed", "n_works"),
    _x("runner.road_works", CACHE, _TAB, "planned_edges", "edge_cell"),
    _x("runner.traffic", REF, _REFR, "world", "assets"),
    _x("runner.traffic", CONST, _FIELD + "・" + _CFG, "tick_seconds", "through_ratio", "process_ids", "ablation_id"),
    _x("runner.traffic", CACHE, _TAB + "・場を作り直した時の印(-1 に戻せば同じ時の場を作り直す)", "edge_hourly", "q24",
       "hour"),
    _x("runner.opening", REF, _REFR, "world", "agents", "assets", "log"),
    _x("runner.opening", CONST, _FIELD + "・" + _CFG, "tick_seconds", "process_ids", "ablation_id",
       "plan_spec_id"),
    _x("runner.opening", CACHE, _DAY, "day_index"),
    _x("runner.opening", CACHE, _TAB, "open_matrix"),
    _x("runner.opening", CACHE, "SoA の kind から作る担当従業者の表(導出・10d: 再開では rebuild_derived で作り直す)",
       "staff_of_poi"),
    _x("runner.environment", REF, _REFR, "calendar", "world", "agents", "assets"),
    _x("runner.environment", CONST, _FIELD + "・" + _CFG, "prefer_shadow_days", "master_seed", "day_index",
       "tick_seconds", "process_ids"),
    _x("runner.environment", CACHE, "日の出・日の入り・セルの点・日陰の面(資産と日付から作る)と日陰のキャッシュの印",
       "_planes", "_sunrise", "_sunset", "_cell_point", "_shade_cache_frame"),
    _x("ledger.money", CONST, _CFG + "(他所の現金の扱いの印は初期化で 1 回だけ立てる)", "sizes", "_foreign_cash",
       "retention_days", "raw_capacity"),
    _x("ledger.money", CACHE, "書き込み窓の入れ子の深さ(checkpoint では 0)", "_depth"),
    _x("ledger.money", CONST, "初期の財布(cli._HouseholdWalletLedger・母集団の財布=初期化で渡す定数)", "wallets"),
    _x("ledger.goods", CONST, _CFG + "・クラスの定数", "sku", "n_poi", "slots", "cat", "poi_sku", "_n_slots_used",
       "static_store_waste_g", "unit_cost", "n_agents", "retention_days", "STORE_WASTE_BAND_NOTE"),
    _x("ledger.goods", CACHE, "書き込み窓の入れ子の深さ(checkpoint では 0)", "_depth"),
    _x("undefined", CONST, _CFG, "vocab_version", "threshold_agents", "log_limit", "params", "review_keywords"),
    _x("undefined", REF, "裁定器(run_day では None)", "adjudicator"),
    _x("renderer", REF, _REFR + "・時計の関数・焦点の列(agents.focus_target のビュー)", "world", "agents", "assets",
       "clock_fn", "_focus_target"),
    _x("renderer", REF, "10d 検収 D1: B3 の天候の日を返す口(engine.run が世界過程の再生の実日を差し込む・関数)",
       "weather_date_fn"),
    _x("renderer", CONST, _CFG + "(知人の初期表・被注視数は初期化で渡す値)", "seed", "acquaintances", "watched_by",
       "budget_mode", "strict_group_budget", "signage_enabled", "signage_p_see", "p_see_activity", "_p_see_mult",
       "_p_see_identity", "intent_mode", "vocab_version", "role_words", "near_tiebreak", "near_order",
       "_near_salt64", "_b0", "_b4b", "_hunger_words", "hunger_words", "_hunger_min_stage"),
    _x("bridge", CONST, _CFG, "mode", "vocab_version", "landmarks", "_engine_codes", "params", "lane", "tick_seconds"),
    _x("bridge", REF, _REFR + "(未定義行動の台帳・再生・応答の口)", "renderer", "undefined", "replay", "client"),
    _x("bridge.tape", CONST, _CFG, "path", "flush_rows", "run_meta"),
    _x("bridge.tape", REF, "parquet の書き手(ファイル)", "_writer"),
    _x("fleet_bridge", REF, _REFR + "(艦隊・テープ・未定義行動の台帳・デバッグのファイル)", "client", "tape",
       "tape_row_factory", "undefined", "_debug_fp"),
    _x("fleet_bridge", CONST, _CFG, "vocab_version", "landmarks", "_engine_codes", "params", "source",
       "_params_hash", "debug_dir", "debug_max_rows"),
)


def excluded_attrs() -> dict[str, dict[str, Excluded]]:
    """持ち主 → 属性 → 除外の項。"""
    out: dict[str, dict[str, Excluded]] = {}
    for e in EXCLUDED:
        for a in e.attrs:
            out.setdefault(e.owner, {})[a] = e
    return out


def item_attrs() -> dict[str, set[str]]:
    """持ち主 → 台帳の行の ``items`` に載る属性(持ち主そのものが ``items`` に載る行は ``"*"``)。"""
    out: dict[str, set[str]] = {}
    for r in external_rows():
        for it in r.items:
            if it in OWNER_CLASSES:
                out.setdefault(it, set()).add("*")
                continue
            owner, attr = it.rsplit(".", 1)
            out.setdefault(owner, set()).add(attr)
    return out


def behavior_items() -> tuple[tuple[str, str], ...]:
    """behavior-hash に入れる外の状態の ``(行の鍵, 属性の道筋)``(軸 1 が behavior の行・``hash_skip`` を除く)。"""
    out: list[tuple[str, str]] = []
    for r in external_rows():
        if r.behavior != BEHAVIOR:
            continue
        skip = set(r.hash_skip)
        out.extend((r.key, it) for it in r.items if it not in skip)
    return tuple(out)
