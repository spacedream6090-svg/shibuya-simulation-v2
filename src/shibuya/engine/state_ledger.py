"""状態台帳の宣言(10b・A3「挙動」と「復元」の 2 軸・機械可読の 1 ファイル)。

**読み口は 1 つ**: ``LEDGER``(207 行の組=〔第 3 期 3-1〕暦 1a の影の行 ``CAL``・〔第 2 期 2-3〕記憶の器の記録の目印の腕の行 ``M0L``・〔第 3 期 3-3〕申込書の控えの行 ``X``・〔第 2 期 2-1〕経済の段階 2 の行 ``EC``・``ATM``・``CR``・``EM``・〔第 1 期 1-8〕候補の口の行 ``J0``・〔第 1 期 1-3〕出来事の記録の行 ``E``・〔1-6〕記憶の器の行 ``M0``・``M0R``・〔1-9〕金と物の目印と計器の行 ``A`` ・〔第 1 期 1-2〕知覚の事実の行 ``P``・〔第 1 期 1-7〕連絡先の印の行 ``CT5``・〔第 1 期 1-8b〕発話の口の腕の行 ``S8``・``S8M``・〔第 2 期 2-2〕近接の層の行 ``PX``・近傍の索引の行 ``PX0``・〔第 3 期 3-2〕計算のまとめの窓の行 ``BW`` を足した)・``OWNER_CLASSES``・``EXCLUDED`` と、その上の小さな関数(``rows``・
``soa_rows``・``external_rows``・``behavior_excluded``・``full_excluded``・``full_items``・``behavior_items``・〔1-8b〕``arm_rows``・``arm_items``)。表・AST の検査(``engine.state_ledger_ast``)・
2 つのハッシュ(``engine.state_hashes``)・揺らし試験はどれもこの表から作る。

〔第 1 期 1-8b〕**腕の行**(``LedgerRow.arm``): 腕が立ったランだけ持ち主がある状態で、軸 1 が behavior か軸 2 が full に入るもの
(発話の口の未読の列 ``S8``)。``behavior_items``・``full_items`` の表には入れず、根の持ち主が居るランだけ ``arm_items`` が
2 つのハッシュと状態のファイルの末尾に足す(持ち主が None のランでは「無い」の印も入れない=既定の final・full-hash・状態の
ファイルは腕の行を足す前と同じバイト)。腕を取り違えた再開は、道筋の集合の食い違いで止まる(``resolve.restore_items``)。
〔第 2 期 2-3〕腕の行の持ち主は道筋の最後の属性の前まで(``LedgerRow.arm_owner``=``speech.inbox`` → ``speech``・
``mem_layer.memory_store._ms_log_seq`` → ``mem_layer.memory_store``)。根の持ち主から属性をたどり、途中が None なら「居ない」。

行の中身(材料 ``docs/bench/analysis/wallbounce-1003/10b-prep.md`` §1 の表を写した。根拠の ``path:line`` は
材料の値=a08109a の行番号。パスは ``src/shibuya/`` を省略):

- **SoA の列 98 行**(agents 79・cells 5・pois 9・知覚 5): ``place`` は ``agents``・``cells``・``pois``・``perception``。
  〔10e(E1)〕死蔵の 5 列(agents の ``plan_cursor``・``invocation_distance``・``wake_pending_class``=Q9、
  知覚の ``last_b2_hash``・``last_b4_hash``=A4)を SoA から消したので **93 行**(agents 76・cells 5・pois 9・知覚 3)。
  死蔵の行は知覚の ``invocation_distance``(単体ベンチの逃げ道・既定では確保しない)の 1 行だけが残る。
  〔10e(E1・検収 R1)〕外の状態に O96(O44 から ``run_day.replay_inbox`` を分けた行・軸 1 no)を足して **96 行**・全体 189 行。
  〔第330・RET〕K15 の 2 列(agents の ``fail_streak``・``plan_activity``)を消して SoA **91 行**(agents 74)・全体 **187 行**。
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
金・物・ActualLog のリング 3 行は ``discardable``(K16 の既定案)。〔第330・RET〕K15 の ``fail_streak``・``plan_activity``
(``no`` かつ復元 ``unknown``・書くだけで誰も読まない)は列ごと消した(台帳の 2 行も消した)。

10b-2(親の答え): 外の状態の持ち主のクラス(``OWNER_CLASSES``)の属性は、どれかの行の ``items`` か、明示の除外の
一覧 ``EXCLUDED``((ii) キャッシュ・導出 / (iii) 定数・設定 / (iv) 参照・理由つき)のどちらかに必ず載る
(``engine.state_ledger_ast.coverage`` とテストが突き合わせる)。判断のつかない行は軸 2 を ``unknown`` にして
full-hash に入れる。``hunger`` は構成で軸 2 が変わる印(``restore_by_config``)を持つ。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable, Mapping

#: 表の版(列や行の判定を変えたら上げる。manifest の ``state_hashes.ledger_version`` に出る)。
#: 10e(E1): 死蔵の 5 列(Q9 の 3 列+A4 の 2 列)を消して 193 → 188 行・O44 から replay_inbox を O96 に分けて 189 行。
#: 〔第330・RET〕K15 の 2 列(``fail_streak``・``plan_activity``)を消して 187 行=版を上げた(前 ``state-ledger/10e``)。
#: 〔第 1 期 1-3〕出来事の記録の行 ``E``(軸 1 diag・軸 2 discardable)を足したが版は上げない(仮採用): この行は
#: behavior-hash・full-hash・状態のファイル(``full_items``)のどれにも入らず、上げると manifest の
#: ``state_hashes.ledger_version`` の値が動き、前の版で書いた状態のファイルから再開できなくなる(どちらも中身は同じ)。
#: 〔第 1 期 1-6〕記憶の器の行 ``M0``(軸 1 no・軸 2 derivable・中身は全部 hash_skip)と ``M0R``(diag・discardable)を
#: 足したが版は上げない(1-3 と同じ仮採用): どちらのハッシュにも状態のファイルにも入らない(190 行)。
#: 〔第 1 期 1-2〕知覚の事実の行 ``P``(軸 1 no・軸 2 discardable・道筋なし)も同じ理由で版は上げない(仮採用)。
#: 〔第 1 期 1-8 J0〕候補の口の行 ``J0``(軸 1 diag・軸 2 discardable)も同じ理由で版は上げない(仮採用)。
#: 〔第 1 期 1-7〕連絡先の印の行 ``CT5``(軸 1 diag・軸 2 derivable・中身は全部 hash_skip=1-6 の ``M0`` と同じ形)も同じ理由で
#: 版は上げない(仮採用)。
#: 〔第 1 期 1-8b〕発話の口の腕の行 ``S8``(behavior・required)・``S8M``(diag・discardable)も版は上げない(仮採用): 腕の行は
#: 腕 on のランだけハッシュと状態のファイルに入る=既定 off のランの状態のファイルは前の版と同じ中身。
#: 〔第 2 期 2-2 段 11a〕近接の層の行 ``PX``(diag・discardable)と近傍の索引の行 ``PX0``(no・discardable)も同じ理由で上げない。
#: 〔第 3 期 3-3〕申込書の控えの行 ``X``(diag・discardable)も版は上げない(仮採用): どちらのハッシュにも状態のファイルにも入らない。
#: 〔第 3 期 3-2〕計算のまとめの窓の行 ``BW``(diag・discardable)も版は上げない(仮採用): どちらのハッシュにも状態のファイルにも入らない。
#: 〔第 3 期 3-5〕本人の体の層の行 ``BD``(diag・discardable)も同じ理由で版は上げない(仮採用)。
#: 〔第 3 期 3-1〕暦 1a の影の行 ``CAL``(diag・derivable・中身は全部 hash_skip=CT5 と同じ形)も同じ理由で版は上げない(仮採用)。
#: 〔第 6 期 6-4 C1〕連絡の道具の腕の行 ``CT1D``・``CT1A``・``CT1AS``・``CT1I``・``CT1IS``・``CT1C``・``CT1K``・``CT1S``・``CT1M``
#: も版は上げない(仮採用): 腕の行は腕 c1 のランだけハッシュと状態のファイルに入る=既定のランの状態のファイルは前の版と同じ中身。
LEDGER_VERSION: Final[str] = "state-ledger/10e-ret"

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
    #: 10e(E1・検収 R1 の続き): 並びが状態でない list の道筋(``items`` の部分集合)。ハッシュは要素の多重集合で取る
    #: (直列化の昇順)。再開の保存は並びのまま(戻すときの値は変えない)。
    multiset: tuple[str, ...] = ()
    #: 〔第 1 期 1-8b〕**腕の行**の印(腕の名・空=どの構成でも入る行)。腕の行は ``behavior_items``・``full_items`` の
    #: 表に入れず、根の持ち主が居るラン(腕が立っているラン)だけ ``arm_items`` で 2 つのハッシュと状態のファイルに入る
    #: (持ち主が None のランでは「無い」の印も入れない=腕の状態を足しても既定の final・full-hash・状態のファイルは不変)。
    #: 道筋の根(``items`` の先頭の ``.`` の前)は行の中で 1 つ。
    arm: str = ""

    @property
    def is_soa(self) -> bool:
        return self.place in SOA_PLACES

    @property
    def arm_owner(self) -> str:
        """腕の行の持ち主の道筋(腕の行でなければ ``""``)。〔第 2 期 2-3〕道筋の最後の属性の前まで(``speech.inbox`` →
        ``speech``・``mem_layer.memory_store._ms_log_seq`` → ``mem_layer.memory_store``)。"""
        return self.items[0].rpartition(".")[0] if (self.arm and self.items) else ""

    @property
    def in_behavior(self) -> bool:
        return self.behavior == BEHAVIOR

    @property
    def in_full(self) -> bool:
        return self.restore in FULL_RESTORE


# ---------------------------------------------------------------- SoA の列(98 行 → 10e で 93 行)
def _s(place: str, name: str, dtype: str, nbytes: str, alloc: str, behavior: str, restore: str,
       basis: str, *, dead: bool = False, allow: tuple[AstAllow, ...] = (), note: str = "",
       by_config: tuple[tuple[str, str], ...] = ()) -> LedgerRow:
    return LedgerRow(key=f"{place}.{name}", name=name, place=place, dtype=dtype, nbytes=nbytes,
                     alloc=alloc, behavior=behavior, restore=restore, dead=dead, basis=basis,
                     ast_allow=allow, note=note, restore_by_config=by_config)


B, N_, D_ = BEHAVIOR, NO, DIAG
R_, V_, X_, U_ = REQUIRED, DERIVABLE, DISCARDABLE, UNKNOWN

_ALLOW_BAND = (AstAllow("world/assets.py", 'cells["band"]',
                        "資産の表(W2 の parquet)の列 band を読む行。SoA の agents.band ではない(材料 §2-4 の誤検出 1)"),
               # 〔第 2 期 2-2 段 11a〕腕 --proximity distance の読み手。〔改訂(第 2 期 2-4 V2)〕近接の既定が distance に
               # なったので、組み立ての規則(rule_from)は体の層を behavior の列 agents.cell から導く(cell_band[cell]=値は同じ)
               # =この列を読むのは cell_band を持たない規則(試験の合成の規則)の道だけ。描画(B5 の近接行の自分の層)の読みは
               # セルから導く形に替えて消した(軸 1 no のまま)
               AstAllow("engine/proximity.py", "return np.asarray(r.band)",
                        "第 2 期 2-2: cell_band を持たない規則(試験の合成の規則)だけの読み(組み立ての規則はセルから導く=2-4 V2)"))
_ALLOW_B4 = (AstAllow("world/state.py", "return self.cells.b4_hash",
                      "プロパティ World.b4_hash の中の読み。プロパティの呼び手は 0(材料 §2-4 の誤検出 2)"),)
_ALLOW_REVENUE = (AstAllow("engine/systems/report.py", "result.revenue_end =",
                           "保存則の検査とラン要約の値(RunResult.revenue_end)だけ=診断"),
                  AstAllow("engine/resolve.py", "_require_thawed(world, world.pois.revenue)",
                           "1-0 段 A: ufunc.at の前の配列単位の書き込みの旗の検査(値を見ない=読みではない)"))
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
    _s("agents", "talk_partner", "i4", "4", "既定", B, R_, "agents/state.py:576・memory.py:355・run.py:2639",
       note="A2 (b): 記憶の腕・店の記憶の腕のときだけ読む"),
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
    _s("agents", "last_action", "i1", "1", "既定", B, R_, "agents/state.py:708・intent.py:394"),
    _s("agents", "last_result", "i1", "1", "既定", B, R_, "agents/state.py:711・activity.py:297"),
    _s("agents", "last_result_tick", "i4", "4", "既定", B, R_, "agents/state.py:713・activity.py:296・renderer.py:2504"),

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
    # ---- 知覚 SoA(5 列 → 10e で 3 列・perception/state.py:98-108・runner.salient.pstate) ----
    _s("perception", "heading", "u1", "1", "既定(知覚 SoA)", N_, V_, "perception/state.py:98・salient.py:205-214,400-414",
       allow=_ALLOW_HEADING, note="親の宣言: 事象の直前に毎回貼り直す派生の値なので behavior-hash に入れない"),
    _s("perception", "task_flag", "u1", "1", "既定(知覚 SoA)", N_, V_, "perception/state.py:100・salient.py:205-214",
       allow=_ALLOW_TASK, note="親の宣言: heading と同じ"),
    _s("perception", "invocation_distance", "u2", "2", "単体ベンチの条件付き", N_, X_, "perception/state.py:108・宣言のみ",
       dead=True),
)


# ---------------------------------------------------------------- 外の状態(65 行)
def _o(n: int, name: str, where: str, dtype: str, behavior: str, restore: str, items: Iterable[str], *,
       skip: Iterable[str] = (), note: str = "", ordered: bool = False,
       multiset: Iterable[str] = ()) -> LedgerRow:
    return LedgerRow(key=f"O{n}", name=name, place=EXTERNAL, dtype=dtype, nbytes="", alloc="",
                     behavior=behavior, restore=restore, dead=False, basis=where,
                     items=tuple(items), hash_skip=tuple(skip), note=note, ordered=ordered,
                     multiset=tuple(multiset))


#: 〔第 1 期 1-6〕記憶の器 M0 の行 M0 の道筋(記憶の行の列・仮の出来事の表・注釈)。
_M0_ITEMS: Final[tuple[str, ...]] = tuple(f"mem_layer.memory_store.{a}" for a in (
    "_ms_ev_t_ns", "_ms_ev_seq", "_ms_n", "_ms_imp", "_ms_first_ns", "_ms_origin",
    "_lg_kind", "_lg_partner", "_lg_object", "_lg_result", "_lg_cell", "_ms_note", "_ms_note_order"))

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
        "energy.stage_ticks", "energy.stage_ticks_awake_by_hour", "energy.ate_default"),
       note="日の締めで読み終わってから 0 に戻す宣言(日の途中の再開なら要るに変わる)。〔小さな版上げ・meal_w17〕"
            "ate_default=既定の時刻の食事を食べた体の印(計器 meal_default_use)。〔検収 L5〕日の締めで 0 に戻さず状態のファイルにも"
            "入れない(この行の他の配列と同じ)=複数日は「どこかの日に食べた体」・日の途中の再開の後は再開の後の分だけ(宣言)"),
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
            "起床の順になる(conversation.py:617,627)=順を保つ。10e(E2): 期限つきの辞書 3 つ(_refusal_until・"
            "_pair_invite_until・_speaker_invite_until)は tick ごとに期限の切れた項を落とす(purge_expired)="
            "日数に比例して増えない。挙動は不変(期限切れは「無い」と同じ)・中身が変わるので 2 つのハッシュは動く"),
    _o(40, "ConversationManager join_events", "conversation.py:280-313", "list", B, R_, ("conv.join_events",),
       note="A2 (b)・記憶の腕が _next_join で読む"),
    _o(41, "ConversationManager origin_counts ほかの計数", "conversation.py:280-313", "計数", D_, X_,
       ("conv.origin_counts", "conv.n_ignored_invites", "conv.n_gate_rejected", "conv.n_invites",
        "conv.n_accepted", "conv.n_declined", "conv.n_pending_expired", "conv.n_invite_refractory_blocked",
        "conv.n_blocks", "conv.n_backchannels", "conv.n_interrupts", "conv.closed_by_reason", "conv.ignored_events",
        "conv.size_hist", "conv.n_expired_purged")),
    _o(42, "Arbiter _pending・_pool・queue・_last_tick", "arbiter.py:535-543", "配列・float・辞書", B, R_,
       ("arbiter._pending", "arbiter._pool", "arbiter.queue", "arbiter._last_tick")),
    _o(43, "run_day の局所 pending(適用待ちの応答)", "run.py:2696", "list[13 要素の組]", B, R_, ("run_day.pending",),
       multiset=("run_day.pending",),
       note="10b で組に発射の tick と call_id を足した(13 要素)。直列化の書き手=to_state。10e(E1・検収 R1 の続き): "
            "並びは艦隊の到着の順(録画)とテープの行の順(再生)で違うが、適用は (t_apply, 級, 撹拌鍵, 体) の lexsort の"
            "順=並びに依らない=並びは状態でない。ハッシュは多重集合で取る(multiset の印)"),
    _o(44, "run_day の局所 fleet_deferred・fleet_waiting", "run.py:2393-2402", "list・set", B, R_,
       ("run_day.fleet_deferred", "run_day.fleet_waiting"), multiset=("run_day.fleet_deferred",),
       note="A2 (b)・艦隊のランだけ。10e(E1・検収 R1): replay_inbox は O96 に分けた。fleet_deferred(繰り延べた呼の"
            "(体, 条件, 級, 起床の起点) の list)の並びは、録画では艦隊が返した順・再生ではテープの行の順で違うが、"
            "翌 tick の再投入は配列にして候補へ混ぜるだけで並びに依らない(録画と再生で呼数・legacy の final が一致)"
            "=並びは状態でない。ハッシュは多重集合で取る(multiset の印)"),
    _o(45, "ChangeDetector _prev_raw", "change_detect.py:274,299", "i4 セル×4", B, R_, ("detector._prev_raw",),
       note="None だと日の頭に全セル起床"),
    _o(46, "SalientProcess rng・event_seen_tick・budget", "salient.py:153-176", "Generator・i4 体数", B, R_,
       ("runner.salient.rng", "runner.salient.event_seen_tick", "runner.salient.budget"),
       note="10c: rng は counter では None(保存するものが無い)。〔第330・RET〕stateful を消したので常に None。道筋は behavior-hash の"
            "定義の一部(「無い」の印)なので行と道筋は残す(消すと final が動く)"),
    _o(47, "PublicServiceDispatchProcess rng・pending", "civic.py:116-117", "Generator・list", B, R_,
       ("runner.dispatch.rng", "runner.dispatch.pending"),
       note="10c: rng は counter では None(保存するものが無い)。〔第330・RET〕stateful を消したので常に None。道筋は behavior-hash の"
            "定義の一部(「無い」の印)なので行と道筋は残す(消すと final が動く)"),
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
        "renderer.named_closed_lookup", "renderer.signage_exposures"),
       note="10e(E2・10f の残り O64 の答え=親案): signage_exposures は描画が集めた看板の露出を同じ tick の 6 段目で"
            "記憶と親しみの層が読んで空にする**挙動の読み**だが、tick の中だけの口で checkpoint と日の境目の保存の"
            "時点では常に空。behavior にしてもハッシュの値は変わらず、全構成の behavior-hash を動かす理由が無いので"
            "軸 1 no・軸 2 discardable のまま。持ち主の外の読みは state_ledger_ast.EXT_AST_ALLOW に理由つきで許す"
            "(場所・当たる数・関数の名前を固定)。空であることは試験で確かめる"),
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
        "runner.opening.n_unauthorized",  # 第 1 期 1-5: 権利の無い体の開閉(止めずに記録した行)
        "runner.environment.n_updates", "runner.environment.shadow_missing", "runner.n_steps",
        "runner.phase_seconds"),
       note="phase_seconds は壁時計(非決定)"),
    _o(74, "RailProcess arrival_train・external_line(帰りの便の予約印・域外居住者の路線)", "processes/rail.py:293-294,405-406,459,502",
       "i8 体数", B, R_, ("runner.rail.arrival_train", "runner.rail.external_line"),
       note="初期化で域外居住者に割り当て、乗車と帰着で書き換える"),
    _o(75, "CrowdProcess occupancy・queue_len・flow", "processes/crowd.py:165-180,252-293",
       "i8/u1 POI・セル数", B, U_,
       ("runner.crowd.occupancy", "runner.crowd.queue_len", "runner.crowd.flow"),
       note="毎 tick の step で SoA から作り直すが、作り直す前(次の tick の入店の判定)に読む口があるかは未確認=不明。"
            "10f: flow_dir8・coherence は O95 へ(読み手 0=diag)"),
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
           # 第 1 期 1-8b: B6 に足した発話の行の数・個体群の予算で外した描画の数(腕 on のランだけ増える)
           "speech_lines", "speech_lines_over_budget",
           # 〔第 6 期 6-4 C1〕B6 に足した連絡の行の数・予算で外した描画の数・割り込めなかった出来事のあった描画の数(腕 c1 だけ)
           "contact_lines", "contact_lines_over_budget", "contact_unnoticed_renders"))),
    _o(85, "LLMBridge _interned(テープへ書いた共有ブロック)", "engine/llm_bridge.py:554,771-774", "set", N_, R_,
       ("bridge._interned",), note="テープの block 行を 1 回だけ書く印。10d: 記録の継続に要る=required(再開のテープは"
                                   "新しい block だけを持ち、親のテープと連結して読む)"),
    _o(86, "LLMBridge の計数", "engine/llm_bridge.py", "計数", D_, X_,
       tuple(f"bridge.{a}" for a in (
           "n_calls", "n_parse_errors", "n_parse_errors_strict", "n_label_alias", "n_positional",
           "n_dictionary_mapped", "n_unknown_action", "n_undefined_mapped", "n_role_actions", "n_tape_misses",
           "n_deferred", "n_tape_rows",
           # 第 1 期 1-5: 役割語のうち権利台帳で許可の無かった数・判定しなかった数(decide の持ち物=検収 L10)
           "n_role_unauthorized", "n_role_unjudged"))),
    _o(87, "TapeWriter の書き出し待ちの行と計数", "engine/tape.py", "list・計数", N_, X_,
       ("bridge.tape._rows", "bridge.tape._blocks", "bridge.tape._n_written", "bridge.tape._n_deferred",
        "bridge.tape._arm_values"),
       note="テープはファイルに出る(O65)。〔第 1 期 1-6 M0〕_arm_values=腕の列の書き出し待ちの値(_rows と同じ並び)"),
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
    _o(95, "CrowdProcess flow_dir8・coherence(8 方位と向きのそろい)", "processes/crowd.py:166-167,269-297",
       "u1/f8 セル数", D_, U_, ("runner.crowd.flow_dir8", "runner.crowd.coherence"),
       note="10f: 元 O75(behavior)。src に読み手が無い(grep `flow_dir8`・`coherence` は crowd.py の書き込みと"
            "tests/engine/processes/test_crowd.py だけ・getattr の文字列も無い・10f の材料 §3-3 の AST でも 0)。"
            "crowd.py の docstring どおり「診断・将来用」=軸 1 を diag に。描画が使う 3 値の flow は O75 に残る"
            "(coherence は flow を作る途中の局所変数 coh として使われ、属性は読まれない)。軸 2 は O75 と同じ unknown"),
    _o(96, "run_day の局所 replay_inbox(再生の到着待ち)", "run.py:2393-2402", "dict", N_, R_,
       ("run_day.replay_inbox",),
       note="10e(E1・検収 R1): 元 O44(behavior)。再生の到着待ちは、テープの observed_tick から導ける「応答がいつ届くか」の"
            "表し方で、世界の挙動ではない(録画の側では同じ応答は艦隊の中=O65 にあり checkpoint の時点で知り得ない)。"
            "behavior に入れると、艦隊で録ったランとその再生で behavior-hash(=既定の final)が食い違う(在途の呼があれば"
            "途中の checkpoint は必ず・最後の tick に在途の呼があれば final も)。軸 1 は no にして behavior-hash から外す。"
            "再開には要る=軸 2 は required のまま(full-hash と状態のファイルには入る)"),
    # ---- 第 1 期 1-3(出来事の記録・CP12): 足す前に軸を決めた行(口の約束 1-3 の約束 (1)) ----
    LedgerRow(
        key="E", name="EventLog(出来事の記録・第 1 期 1-3)", place=EXTERNAL,
        dtype="列(SoA 風・1 行 72 B)・名の表・原因の表の列(1 行 39 B+入力の id 12 B/個=1-8 J0)",
        nbytes="", alloc="", behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/events/log.py(EventLog)・engine/systems/state_io.py(day_record の計器)",
        items=tuple(f"events.{a}" for a in (
            "_ev_t_ns", "_ev_seq", "_ev_who", "_ev_what", "_ev_whom", "_ev_where_kind", "_ev_where_id",
            "_ev_how_much", "_ev_via", "_ev_received_ns", "_ev_read_ns", "_ev_origin", "_ev_cause", "_ev_n",
            "_ev_names", "_ev_name_codes", "_ev_now_ns", "_ev_seq_next",
            "_ev_day_mark", "_ev_n_appended", "_ev_n_evicted",
            # 〔第 1 期 1-8 J0・1-3 の検収 M2〕原因の表の列(前は Python の物の list と dict=_ev_causes・_ev_cause_codes)
            "_cz_kind", "_cz_ref", "_cz_call_t", "_cz_call_agent", "_cz_call_cls", "_cz_in_start", "_cz_in_len",
            "_cz_src", "_cz_num", "_ci_t", "_ci_seq", "_cz_n", "_ci_n", "_cz_proc_rows", "_cz_exp_rows",
            "_cz_experiments", "_cz_texts", "_cz_last_llm")),
        note="1-3: 軸 1 diag(読み手は日次の記録の計器=state_io.day_record と試験だけ。挙動は読まない)・軸 2 discardable"
             "(再開のランは空から書く=どちらのハッシュにも状態のファイルにも入らない=記録の有無で final・behavior-hash は"
             "不変)。id は (t_ns, seq) なので刻みの境目からの再開でも通しのランと同じ id。行の鍵は O の通し番号でなく "
             "E(系の宣言は E:events.*)。書く系は world・phase_c(1-9)・checkpoint・day_close・close_final・decide(1-8 J0 の"
             "腕 --decision-port port の判断の出来事 1 行)(凍結の表 writes_paths_events.json と同じ。1-5 の役割語は出来事を"
             "書かない)。1-8 J0 で原因の表を列にした(道筋の名だけが替わった)"),
    # ---- 第 1 期 1-6(記憶の器 M0・MR11 (b)・MR16・腕 --memory-store events): 足す前に軸を決めた行 ----
    LedgerRow(
        key="M0", name="MemoryStore(記憶の器 M0・第 1 期 1-6)の行・仮の出来事の表・注釈", place=EXTERNAL,
        dtype="列(SoA 風・行 32 B+仮の出来事 14 B)・注釈の dict", nbytes="", alloc="", behavior=NO,
        restore=DERIVABLE, dead=False,
        basis="engine/memory_store.py(MemoryStore)・engine/memory.py(_write・_recall_from_store・rebuild_memory_store)",
        items=_M0_ITEMS, hash_skip=_M0_ITEMS,
        note="1-6: 腕のランだけ確保(既定は持ち主が None)。M0 の器は記憶の表 mem_*(behavior・required)と要旨 O8 の"
             "写し(同じ出来事を同じ行に書く=_write が行の食い違いを落とす・行は全部が出どころ legacy)=軸 1 no(派生と"
             "宣言=想起の中身は mem_* と O8 と同じ値で既に behavior-hash に入っている)・軸 2 derivable(再開では"
             "rebuild_memory_store が戻した mem_* と O8 から作り直す)・中身は hash_skip(作り直せる表=キャッシュと同じ扱い"
             "=どちらのハッシュにも状態のファイルにも入らない=腕を足しても既定の final は不変)。M1 で器を既定の記憶に"
             "する(mem_* を消す)ときに behavior・required へ移す(版上げ)。書く系は decide・llm_receive・memory・drain"
             "(宣言 M0*:mem_layer.memory_store.*)。〔第 6 期 6-5・検収 M3〕腕 --memory-model m1 と --memory-people memory では"
             "器の行が挙動を決める(m1=想起の候補と順を器の行の強さで・memory=器は表の写しでなく、人の行が会話の相手選びを・"
             "出来事の行が想起を決める)のに、この行の軸は既定の器のまま(軸 1 no・hash_skip・軸 2 derivable)=behavior-hash は"
             "器の人の行と出来事の行を見ない(入るのは腕の行 M0M の時刻と M0S の店の行だけ)。腕 memory と粒度 day は再開を止める"
             "ので軸 2 の害は無い。既定化(MR10=まとめて 1 回の版上げ)のときに軸を改める(behavior-hash に入れる・required)"),
    LedgerRow(
        key="M0R", name="MemoryStore の録画(見せた時刻)・テープの列への控え・計数(第 1 期 1-6)", place=EXTERNAL,
        dtype="列(8 B/行)・dict・Counter", nbytes="", alloc="", behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/memory_store.py(mark_shown・take_shown・recall の計数・summary)",
        items=tuple(f"mem_layer.memory_store.{a}" for a in ("_ms_shown_ns", "_ms_tape", "_ms_stats", "_ms_last")),
        note="1-6: 録画(MR16)は診断=読み手はテープの列 recalled_event_ids と manifest の計器だけ(挙動は読まない)・"
             "再開のランは空から(捨ててよい)"),
    # ---- 第 1 期 1-9(お金の基本操作・CP2 の段階 1): 足す前に軸を決めた行 ----
    LedgerRow(
        key="A", name="金と物の台帳の行の目印の列・transfer の計器(第 1 期 1-9)", place=EXTERNAL,
        dtype="列(生ログ・納品ログの輪と同じ長さ・12 B/行)・計器の dataclass",
        nbytes="", alloc="", behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="economy/ops.py(transfer・TransferMeter)・economy/ledger.py・economy/goods.py・"
              "engine/systems/state_io.py(day_record の計器)・engine/run.py(manifest の economy)",
        items=("ledger.money._raw_event_t_ns", "ledger.money._raw_event_seq", "ledger.money.meter",
               "ledger.goods._dl_event_t_ns", "ledger.goods._dl_event_seq"),
        note="1-9: 生ログ(O58)と納品ログ(O60)の行ごとの出来事の id((t_ns, seq)・無い行は -1)と、基本操作 transfer の"
             "計器(行・額・原因の無い行・出来事の行・輪の溢れ=K17・日の締めの流れの表の検算)。軸 1 diag(読み手は manifest の"
             " economy と日次の記録の計器と試験だけ)・軸 2 discardable(輪の中身 O58・O60 と同じく再開で空から=どちらの"
             "ハッシュにも状態のファイルにも入らない)。行の鍵は O の通し番号でなく A(CP1 の A=湧かないもの=お金。1-5 の権利=CP1 の C と取り違えないため・検収 L3)。系の宣言は A:ledger.*。"
             "書く系は phase_c・world・day_close・close_final"),
    # ---- 第 1 期 1-2(知覚の分離・§1-13): 足す前に軸を決めた行(口の約束 1-2 の約束 (3)) ----
    LedgerRow(
        key="P", name="TickScratch.percepts(知覚の事実 Percept・第 1 期 1-2)", place=EXTERNAL,
        dtype="体 → perception.facts.Percept(凍結の dataclass)", nbytes="", alloc="", behavior=NO,
        restore=DISCARDABLE, dead=False,
        basis="perception/facts.py(Percept)・perception/renderer.py(perceive・render_percept)・"
              "engine/systems/decide.py(書く)・engine/systems/boxes.py(SCRATCH_FIELDS)",
        items=(),
        note="1-2: 軸 1 no(描画は Percept から文を描くが、Percept は刻みの中で個体 SoA・世界・刻みの前計算から作り直す派生の値="
             "知覚 SoA の heading・task_flag と同じ扱い。scratch の欄を読む系は今は無い=1-8 の判断の口が読む)・軸 2 discardable"
             "(刻みの頭で空になる=どちらのハッシュにも状態のファイルにも入らない)。持ち主の物ではなく TickScratch の欄なので"
             "道筋(items)は持たない。書く系は decide だけ(writes.scratch=段 C の守り)。行の鍵は O の通し番号でなく P"),
    # ---- 第 1 期 1-8(候補の口 J0・DM-0・C-2): 足す前に軸を決めた行(口の約束 1-8 の約束 (1)=腕の裏) ----
    LedgerRow(
        key="J0", name="DecisionLayer(候補の口 J0 の計器・刻みごとの営業中の店の控え・第 1 期 1-8)", place=EXTERNAL,
        dtype="計器の dict(数と分布)・セル数の bool 3 本と刻みの番号", nbytes="", alloc="--decision-port port",
        behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/decision/layer.py(DecisionLayer.decide_one・affordance_words)・engine/systems/decide.py(書く)・"
              "engine/run.py(manifest の decision_port)",
        items=("decision.meter", "decision._aff_step", "decision._aff_any", "decision._aff_eatery",
               "decision._aff_shop", "decision._s2_hints"),
        note="1-8 J0: 腕 --decision-port port のランだけ層を作る(既定は持ち主が None)。計器(判断の数・候補の源の分布・"
             "「その他」・選んだ番号・今の道との食い違い・判断の出来事の行)は診断=読み手は manifest の decision_port と試験だけ"
             "(軸 1 diag)。営業中の店の控えは刻みの頭の世界から作り直す(候補の源 affordance を作るだけ=行為は口の実装が"
             "選ぶ・mock と古典は候補の源を読まない)。軸 2 discardable(再開のランは空から=どちらのハッシュにも状態のファイルにも"
             "入らない)。書く系は decide だけ(宣言 J0:decision.*)。行の鍵は O の通し番号でなく J0。〔第 2 期 2-1・検収 A1〕"
             "_s2_hints=口の答えの段階 2 の印の控え(decide_one が書き、判断の系が同じ呼の中で take_stage2_hint で取り出す="
             "刻みの境目ではいつも空・印は保留の組の末尾に移って行為へ運ばれる)"),
    # ---- 第 1 期 1-7(道具の台帳 C0・CT5 個人の連絡先): 足す前に軸を決めた行 ----
    LedgerRow(
        key="CT5", name="RelationLayer contact_flags(個人の連絡先の手段ごとの印・第 1 期 1-7)", place=EXTERNAL,
        dtype="u1 体×k(関係辺の欄と同じ位置)・k B/体", nbytes="", alloc="", behavior=DIAG, restore=DERIVABLE,
        dead=False,
        basis="engine/relations.py(_write_contacts・seed_initial・_reset_slots・rebuild_contacts)・"
              "engine/tools/contacts.py(印の作り方と数え方)・engine/systems/state_io.py(rebuild_derived)",
        items=("rel_layer._contact_flags",), hash_skip=("rel_layer._contact_flags",),
        note="1-7: 関係の記憶(--relations on のランだけ)に足した連絡先の手段ごとの印(決定 10-12 §4-4 CT5 (c))。軸 1 diag"
             "(読み手は持ち主の数えの口 contact_tally=manifest の tools.contact_flags と試験だけ=C0 では挙動が読まない・"
             "値は C1 で使う)・軸 2 derivable"
             "(C0 では印は辺の種別の写像そのもの=家族と職場は初めから・新しい相手は 0。再開では rebuild_derived が戻した"
             " rel_kind・rel_partner から作り直す)・中身は hash_skip(作り直せる表=キャッシュと同じ扱い=どちらのハッシュ"
             "にも状態のファイルにも入らない=既定の final・full-hash は不変。1-6 の M0 と同じ形)。C1 で本人が連絡先を"
             "交換し始めたら種別から作れない=behavior・required へ移す(版上げ)。書く系は memory(新しい相手の欄を消す="
             "宣言 CT5:rel_layer._contact_flags)と組み立て(初めの辺)。中身は _contact_flags(公開の contact_flags は"
             "読み取り専用の view の property=検収 L1)。行の鍵は O の通し番号でなく CT5"),
    # ---- 第 1 期 1-8b(発話の口・Q57 (d)): 足す前に軸を決めた行(口の約束 1-8b の約束 (1)=腕の裏・腕の行 arm) ----
    LedgerRow(
        key="S8", name="SpeechPort.inbox(届け先 → 未読の発話の列・第 1 期 1-8b)", place=EXTERNAL,
        dtype="dict(体 → [(目印 (t_ns, seq), 話し手, 本文, 話した時刻 ns)]・届け先ごとに 3 件まで)", nbytes="",
        alloc="--speech-port on", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/speech/port.py(SpeechPort.say・take_heard)・perception/renderer.py(perceive・_b6)・"
              "engine/systems/llm_io.py(utter)",
        items=("speech.inbox",), arm="speech-port",
        note="1-8b: 腕 --speech-port on のランだけ口を作る(既定は持ち主が None)。未読の発話は相手の次の入力(B6 の末尾)に"
             "載る=軸 1 behavior・刻みをまたぐ=軸 2 required。腕の行(arm)=持ち主の居るランだけ behavior-hash・full-hash・"
             "状態のファイルの末尾に入る(arm_items・既定 off のランは「無い」の印も入らない=final・full-hash・状態のファイルは"
             "腕の行を足す前と同じ)。書く系は decide(届ける=描画の perceive が take_heard・話す=会話の番の発話)と "
             "llm_receive(艦隊と再生の到着の発話)(宣言 S8:speech.*)。行の鍵は O の通し番号でなく S8"),
    LedgerRow(
        key="S8M", name="SpeechPort の計器・直近の入力の目印・渡した発話の記録の id の控え(第 1 期 1-8b)", place=EXTERNAL,
        dtype="計数の dict・体 → 目印の組の dict・体 → dict(口の目印 → 記録の id)", nbytes="", alloc="--speech-port on",
        behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/speech/port.py(meter・take_heard・report_shown・event_ids・take_input_ids)・engine/run.py(manifest の "
              "speech_port)",
        items=("speech.meter", "speech._last_input", "speech._own_last", "speech._heard_taken"), arm="speech-port",
        note="1-8b: 計器(会話の番・発話・届いた数・口コミに渡った数ほか)は診断=読み手は manifest の speech_port と試験だけ。"
             "直近の入力の目印は次の発話の出来事の原因の入力(出来事ログ=診断)=軸 1 diag・軸 2 discardable(再開のランは空から)。"
             "〔1-3 の (1) の直し〕take_heard で渡した発話の記録の id の控え _heard_taken は同じ刻みの report_shown・event_ids が"
             "引く(刻みの中の一時=次の take_heard で置き換わる)=diag・discardable。口の通し番号の控え _own_last は未読の列の"
             "目印を決めるが刻みの中でだけ効く(同じ時刻の 2 つ目の発話に 1 を振る・再開は刻みの境目=次の発話は新しい時刻=0 から"
             "=通しと同じ)=discardable のまま(口の欄は付け替えられない=戻す口が無い)。"
             "書く系は decide・llm_receive(宣言 S8M:speech.*)"),
    LedgerRow(
        key="S8E", name="SpeechPort の口の目印 → 出来事の記録の id の診断の表(第 1 期 1-8b・1-3 の (1) の直し)",
        place=EXTERNAL, dtype="dict((t_ns, 通し番号) → (t_ns, seq))",
        nbytes="未読の列にある発話ごとに 1 組(届け先ごとに 3 件まで)", alloc="--speech-port on", behavior=DIAG,
        restore=REQUIRED, dead=False,
        basis="engine/speech/port.py(say・_next_mark・_forget_mark・take_heard)",
        items=("speech._mark_event_of",), arm="speech-port",
        note="1-3 の (1) の直し: 未読の列(行 S8=behavior)の目印は記録に依らない口の通し番号だけにし、記録に書いた出来事の id は"
             "ここに持つ=読み手は次の発話の原因の入力(出来事ログ=診断)だけ=軸 1 diag(記録 on/off で behavior-hash と final が"
             "同じ)。未読が刻みをまたぐ=再開したランの原因の入力が通しと同じ=軸 2 required(C1 の CT1Q・カレンダー 2 の CA2M と"
             "同じ形)。書く系は decide・llm_receive(宣言 S8E:speech.*)"),
    # ---- 第 2 期 2-2 段 11a(近接の判定の切替口): 足す前に軸を決めた行(腕の裏=既定の腕 cell では持ち主が None) ----
    LedgerRow(
        key="PX", name="ProximityLayer(近接の層の計器・第 2 期 2-2 段 11a)", place=EXTERNAL,
        dtype="計器の dict(数と分布)", nbytes="", alloc="SHIBUYA_PROXIMITY=distance", behavior=DIAG,
        restore=DISCARDABLE, dead=False,
        basis="engine/proximity.py(ProximityLayer.build_index・observed)・engine/systems/perceive.py(書く)・"
              "engine/run.py(manifest の proximity)",
        items=("proximity._meter",),
        note="2-2 段 11a: 腕 --proximity distance のランだけ層を作る(〔2-4 V2〕既定。切替口 cell は持ち主が None)。計器(索引を作った回数・"
             "索引の体の数の最大・B5 の単位の在室人数の最大と分布)は診断=読み手は manifest の proximity と試験だけ(軸 1 diag)。"
             "判定の規則(rule)は設定・気づいた印の読み口(_marks=関係の層)は参照(除外の一覧)。軸 2 discardable(再開のランは 0 から=どちらのハッシュにも状態のファイルにも"
             "入らない)。書く系は perceive_prepare だけ(宣言 PX:proximity.*)。行の鍵は O の通し番号でなく PX"),
    LedgerRow(
        key="PX0", name="TickScratch.near_index(近傍の索引 SpatialIndex・第 2 期 2-2 段 11a)", place=EXTERNAL,
        dtype="engine.proximity.SpatialIndex(体の id・座標・層・B5 の単位・格子の鍵の配列)", nbytes="",
        alloc="SHIBUYA_PROXIMITY=distance", behavior=NO, restore=DISCARDABLE, dead=False,
        basis="engine/proximity.py(SpatialIndex)・engine/systems/perceive.py(書く)・engine/systems/boxes.py(SCRATCH_FIELDS)・"
              "perception/renderer.py(B5 の近接行=描画の前計算 _tickc.near)",
        items=(),
        note="2-2 段 11a: 軸 1 no(刻みの頭の SoA の xy・band・poi_ref・cell から作り直す派生の値=行 P と同じ扱い)・軸 2 "
             "discardable(刻みの頭で空になる=どちらのハッシュにも状態のファイルにも入らない)。持ち主の物ではなく TickScratch の"
             "欄なので道筋(items)は持たない。書く系は perceive_prepare だけ(writes.scratch=段 C の守り)。既定の腕 cell では None"),
    # ---- 第 2 期 2-1(経済の段階 2・腕 --economy-stage2 on): 足す前に軸を決めた行(腕の無いランは持ち主の属性が None) ----
    LedgerRow(
        key="EC", name="経済の段階 2 の中身(MoneyStage2=部品・体の種別・1 日の消費・労働時間・組み立ての物・計器)",
        place=EXTERNAL, dtype="物(体の数の配列 6 本=種別・1 日の消費・来街者・労働時間・呼の控え 2 本+〔賃金の小さな版上げ〕"
        "賃金の腕 occupation で 3 本=月の賃金・出どころ・月の時間の目安+組み立ての物の賃金の入力 5 本・dict の計器)", nbytes="",
        alloc="--economy-stage2 on",
        behavior=BEHAVIOR, restore=DERIVABLE, dead=False,
        basis="economy/stage2.py(MoneyStage2)・economy/ledger.py(attach_stage2・purchase_many・endow_households・"
              "on_day_end)・engine/economy_stage2.py(Stage2Plan・attach)・engine/resolve.py(_payable・_stage2_withdraw)",
        items=("ledger.money.stage2",), hash_skip=("ledger.money.stage2",),
        note="2-1: 腕のランだけ挿す(既定は None)。部品と規則(引き出し・支払いの方法・給料日・税)が分岐を決める=軸 1 "
             "behavior。中身は組み立てで作り直す(種別・母集団・W17・暦・規則の表から)=軸 2 derivable・中身は hash_skip"
             "(どちらのハッシュにも状態のファイルにも入らない=腕を足しても既定の final は不変)。残高は帳簿の O57 に入る"
             "(預金も)。計器 s2_meter は診断(manifest の economy.stage2 と日次の記録だけが読む)で再開では 0 から。"
             "書く系は phase_c(引き出し・支払い・税)・day_close と close_final(賃金・日の欄)・build(挿す)"
             "(宣言 EC:ledger.*)。〔検収 A1〕呼の控え(last_call・pay_answer=体ごとの最後の金に触れる行為の呼の id と"
             "支払いの方法の答え)も中身(再開で空から=つなぎの台帳 DOC-ec21-call-memo-not-saved・J0 の 3 つの実装は"
             "支払いを答えない=挙動は不変)。書く系は phase_c(resolve.apply が意図の呼の id を渡す)"),
    LedgerRow(
        key="ATM", name="ATM の表(Fixtures.atms と同じ物・第 2 期 2-1)", place=EXTERNAL,
        dtype="配列(セル i8・種類 i1・営業の区間 i2 × 7 × 2 × 2・出どころ i1)× 点の数(55)", nbytes="",
        alloc="--economy-stage2 on", behavior=BEHAVIOR, restore=DERIVABLE, dead=False,
        basis="engine/economy_stage2.py(AtmTable・build_atm_table・atm_open_cells)・engine/systems/build.py(Fixtures)",
        items=("ledger.money.stage2.atms",), hash_skip=("ledger.money.stage2.atms",),
        note="2-1: OSM の amenity=atm・atm=yes・amenity=bank(検収 L3)の 55 点をセルに写し営業時間を曜日 × 分の区間に"
             "(組み立てで 1 回)。引き出しの"
             "場所と時刻を決める=軸 1 behavior。取得物から作り直す=軸 2 derivable・中身は hash_skip(取得物の md5 を manifest の"
             "economy.stage2.atms に出す)。ランの間は書かない(凍結の dataclass・配列は読み取り専用=検収 L1)。2-4 で W6 の POI に"
             "ATM の行を足して外す"
             "(つなぎの台帳 DOC-ec21-atm-fixture)"),
    LedgerRow(
        key="CR", name="信用の器(CreditBook・第 2 期 2-1・器だけ=行は 0)", place=EXTERNAL,
        dtype="列(種類 i1・借り手・限度・残高・返済日・返済額・延滞)", nbytes="", alloc="--economy-stage2 on",
        behavior=DIAG, restore=DERIVABLE, dead=False,
        basis="economy/credit.py(CreditBook・repay_due=呼び手なし)・economy/ledger.py(attach_stage2)",
        items=("ledger.money.credit",), hash_skip=("ledger.money.credit",),
        note="2-1: 決定 10-12 §4-11 の信用 C1〜C3 の器。ランの中で行を足す口も返済の呼び手も無い=読み手は manifest の"
             "economy.stage2.credit(持ち主の Ledger.economy_record)だけ(軸 1 diag)・いつも空で作り直せる(軸 2 derivable・"
             "hash_skip)。審査と総量規制は 4-2 の規則の表の後。行が動く段で behavior・required へ"
             "(版上げ)"),
    LedgerRow(
        key="EM", name="金の生ログの支払いの方法の列(_raw_method・第 2 期 2-1)", place=EXTERNAL,
        dtype="列(i1・輪と同じ長さ)", nbytes="1 B/行(輪の 1 行 24 B の切り上げの空きに入る)", alloc="", behavior=DIAG,
        restore=DISCARDABLE, dead=False,
        basis="economy/ops.py(transfer の method)・economy/ledger.py(raw_methods)",
        items=("ledger.money._raw_method",),
        note="2-1: 生ログの行ごとの支払いの方法(0=現金・1=口座)。読み手は記録と試験だけ(軸 1 diag)・輪の中身 O58 と同じく"
             "再開で空から(軸 2 discardable)。腕の無いランは全部 0。書く系は生ログを書く系と同じ(world・phase_c・day_close・"
             "close_final=宣言 EM:ledger.*)"),
    # ---- 第 3 期 3-3(反実仮想の申込書・CP5・CP12): 足す前に軸を決めた行 ----
    LedgerRow(
        key="X", name="ExperimentLayer(申込書の改変の控え・4 つの確認の結果・第 3 期 3-3)", place=EXTERNAL,
        dtype="WorldHandle(口が触る世界の物の束と控え rec=効かせた/効かせていない行の list・計数の dict・決定の番号の集合)・"
              "4 つの確認の結果の読み取り専用の dict",
        nbytes="", alloc="申込書を渡したラン(cli.run の experiment・--experiment)", behavior=DIAG, restore=DISCARDABLE,
        dead=False,
        basis="engine/experiment/apply.py(ApplyRecord・WorldHandle・apply)・engine/experiment/layer.py(ExperimentLayer・"
              "manifest・record_checks)・engine/experiment/branch.py(run_branch が record_checks を呼ぶ)",
        items=("experiment.handle", "experiment.xchecks"),
        note="3-3: 申込書を渡したランだけ持ち主を作る(既定は持ち主が None)。handle は口 apply が触る世界の物の束(参照)と"
             "改変の控え handle.rec(効かせた・効かせていない行・計数・決定の番号の集合)。控えの行と計数と 4 つの確認の結果"
             "(xchecks)は診断=読み手は manifest の experiment(持ち主のメソッド manifest)と分岐の報告と試験だけ(軸 1 diag)。"
             "控えの中の決定の番号の集合(記録した・効いている・日ごとに当てた・終わった)は口 apply の当て直しの印だが、申込書と"
             "時刻と世界の資産から決まる派生(世界に入った結果=店の開閉の旗・天気の再生日 O56・暦は世界の側の状態とテープにある)。"
             "軸 2 discardable(再開のランは申込書と時刻と親の状態の見出しの申込書の指紋から作り直す=どちらのハッシュにも状態の"
             "ファイルにも入らない=申込書つきの A/A の枝の final は基準のランと同じ)。書く系は experiment だけ(宣言 "
             "X:experiment.*)。xchecks はランの後に分岐の道具 branch.run_branch が持ち主の口 record_checks で 1 回だけ書く(系の外="
             "ランの間は書かない)。持ち主の欄は 1 回だけ置ける(__setattr__・__delattr__ の守り=検収 M4)。行の鍵は O の通し番号で"
             "なく X"),
    # ---- 第 2 期 2-3(体の出来事を記録へ・器の目印=記録の出来事): 足す前に軸を決めた行(腕の行=腕 --memory-store events) ----
    LedgerRow(
        key="M0L", name="MemoryStore の記録の目印の seq(第 2 期 2-3)", place=EXTERNAL,
        dtype="列(i4・行の数=体 × n_rows・−1=仮の行か空の行)", nbytes="4 B/行(5,000 体で 2.56 MB)",
        alloc="--memory-store events", behavior=NO, restore=REQUIRED, dead=False,
        basis="engine/memory_store.py(remember・rebuild・check_against_table)・engine/events/body.py(BodyEventLink)",
        items=("mem_layer.memory_store._ms_log_seq",), arm="memory-store",
        note="2-3: 腕のランで記憶の器の目印が出来事の記録(1-3)の出来事になった(出どころ None)。目印の seq は記録が付ける"
             "(同じ時刻の行の通し)ので記憶の表 mem_* からは作り直せない=軸 2 required(腕の行=器の居るランだけ full-hash と"
             "状態のファイルの末尾に入る=既定の final・full-hash・状態のファイルは不変)。軸 1 no(想起の中身は mem_* と O8 で"
             "既に behavior-hash に入る=目印は録画とテープの列だけが読む)。再開では rebuild がこの列から目印と出どころを戻す"
             "(前の日の出来事は再開のランの記録に無い=記録は discardable のまま=目印は残る・記録 md23/README.md)。書く系は"
             "decide・llm_receive・memory(宣言 M0*:mem_layer.memory_store.*)。行の鍵は O の通し番号でなく M0L"),
    # ---- 第 3 期 3-2(計算のまとめの窓・時計の段 T1): 足す前に軸を決めた行 ----
    LedgerRow(
        key="BW", name="WindowQueue(計算のまとめの窓の待ち行列と計器・第 3 期 3-2)", place=EXTERNAL,
        dtype="Scheduler(幅 W のバケットの輪+遠未来の heapq)・持ち越しの行(int64 × 4 列)・次の窓の頭(int・ns)・"
              "計器の dict(int)",
        nbytes="", alloc="既定(進行役が窓のループの前に置く)", behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/batching.py(WindowQueue・manifest_fields)・engine/systems/conductor.py(conduct が置いて窓ごとに回す)",
        items=("batching._bw_sched", "batching._bw_carry", "batching._bw_head", "batching._bw_meter"),
        note="3-2: 進行役が窓のループの前に持ち主を作る(組み立ての間は None)。T1 の待ち行列に入るのは次の刻みの事象だけ"
             "(世界の 1 回の系の並び=刻みの番号から決まる派生)。持ち越しは上限に当たった窓の残りだけ(既定のランでは空)。"
             "計器(窓の数・事象の数・持ち越し・上限に当たった数)の読み手は manifest の batching(持ち主のメソッド "
             "manifest_fields)と試験だけ(軸 1 diag)。再開のランは進行役がランの始めの刻みから作り直す(軸 2 discardable="
             "どちらのハッシュにも状態のファイルにも入らない=既定の final・full-hash・状態のファイルは不変)。書くのは進行役"
             "(系の外=窓の境目 WINDOW_MARK に帰属)と刻みの事象の頭の次の予約と、〔6-4 C1 検収 H1〕腕 c1 の系 contact(送信と着信の予約=宣言 BW:batching.*・予約の控えは連絡の持ち主の行 CT1I)だけ(〔6-3 検収 M1〕腕 --talk-clock mora のランは"
             "会話の番の発言の予約=系 decide・llm_receive も書く=宣言 BW:batching.*)。T2 で刻みの外の事象(会話の番・届く"
             "メッセージ・体の変化の予約)が入ったら軸 1 behavior・軸 2 required へ見直す(版上げ・つなぎの台帳 DOC-tm32-*)。"
             "行の鍵は O の通し番号でなく BW"),
    # ---- 第 3 期 3-5(本人の体の層・③ 群・TM5 の予約の口): 足す前に軸を決めた行 ----
    LedgerRow(
        key="BD", name="BodyModel(本人の体の層の段の境目の計器と TM5 の予約の列・第 3 期 3-5)", place=EXTERNAL,
        dtype="計器の dict(数・種類ごとの境目の数・境目の列の鎖のハッシュ)・BodySchedule(予約の列 Scheduler 2 本・体ごとの"
              "生きている予約の通し番号と刻み/窓・引き直しの写し・その日の体感温度の表と次に変わる窓の表)",
        nbytes="腕 sweep: 計器だけ/腕 reserve: 体あたり約 56 B(通し番号と刻み/窓と列 8 B × 5・写し 16 B)+予約 1 件 32 B"
               "+日の表 288 × (セル+1) × (1+4) B",
        alloc="常に(予約の列の中身は腕 --body-schedule reserve のランだけ)", behavior=DIAG, restore=DISCARDABLE,
        dead=False,
        basis="engine/body/model.py(BodyModel.step・initial・observed)・engine/body/schedule.py(BodySchedule)・"
              "engine/resolve.py(advance_body・initialize・initialize_energy が呼ぶ)・engine/processes/environment.py"
              "(step が呼ぶ)・engine/run.py(manifest の body)",
        items=("body._body_meter", "body._reservations"),
        note="3-5: 組み立てがどの腕でも持ち主を作る(段の境目の計器と manifest の body のため)。計器(体の刻みの回数・規則に"
             "通した体の延べ・予約・引き直し・種類ごとの境目の数と列の鎖のハッシュ)は診断=読み手は manifest の body と試験だけ。"
             "予約の列は腕 reserve で「どの体を規則に通すか」を決めるが、受入の条件が「全員を毎回見る版(sweep)と結果が同じ」"
             "(byte-check 19 構成・境目の列が同じ)=結果を変えない控え=軸 1 diag(親の発注の宣言)。軸 2 discardable(再開では"
             "状態から引き直す=最初の体の刻みで全員を規則に通す・下界の予約なので引き直した列は通しの列と違ってよい=結果は同じ="
             "どちらのハッシュにも状態のファイルにも入らない)。腕 sweep では予約の列は空のまま。書く系は body(体の刻み)と "
             "world(5 分の窓の体感温度=環境の過程が口を呼ぶ)だけ(宣言 BD:body.*)。持ち主の欄は 1 回だけ置ける(__setattr__・"
             "__delattr__ の守り)・中身を書く口は step と initial だけ(試験 tests/engine/body/test_body_guard.py)。〔検収 M1〕体ごと"
             "の配列は腕 reserve だけ確保する(腕 sweep は長さ 0=計器だけ)・〔検収 L6〕段の境目の計器は環境変数 "
             "SHIBUYA_BODY_BOUNDARY_GAUGE=1 のときだけ数える。行の鍵は O の通し番号でなく BD"),
    # ---- 第 3 期 3-1(暦 1a の影・CA2 (a)・腕 --calendar-shadow 1a): 足す前に軸を決めた行(腕の無いランは持ち主が None) ----
    LedgerRow(
        key="CAL", name="CalendarShadow(暦 1a の影=その日の勤務と授業の約束と日ごとの計器・第 3 期 3-1)", place=EXTERNAL,
        dtype="その日の影の dict(体 × 欄の配列 10 本と日・週・曜日)・日番号 → 計器の記録の dict", nbytes="",
        alloc="--calendar-shadow 1a", behavior=DIAG, restore=DERIVABLE, dead=False,
        basis="engine/calendar_shadow.py(CalendarShadow.relay_day・manifest)・engine/systems/state_io.py(relay_tables)・"
              "engine/systems/build.py(組み立てで 0 日目)・engine/run.py(manifest の calendar_shadow)",
        items=("calendar_shadow.today", "calendar_shadow.shadow_day_log"),
        hash_skip=("calendar_shadow.today", "calendar_shadow.shadow_day_log"),
        note="3-1: 腕 1a で母集団のあるランだけ持ち主を作る(既定 w17 は None)。影は計器だけ=出入り・退出・就寝は計画実行層が"
             "W17 で動かす(CA2 (a))=読み手は manifest の calendar_shadow と試験だけ(軸 1 diag)。その日の影と日ごとの記録は"
             "W20 の週の表・暦・日番号だけから決まる=軸 2 derivable(再開では組み立てが 0 日目を・表の張り直しが再開の日までを"
             "作り直す=通しと同じ記録)・中身は hash_skip(どちらのハッシュにも状態のファイルにも入らない=腕 1a のランの final は"
             "既定と同じ)。書く系は day_head(宣言 CAL:calendar_shadow.*)と組み立て。行の鍵は O の通し番号でなく CAL"),
    # ---- 第 6 期 6-5(記憶 MR の GPU の前の分・全部 腕): 足す前に軸を決めた行(腕の行=腕のランだけ持ち主がある) ----
    LedgerRow(
        key="M0M", name="M1State(記憶の強さ M1 の直近の時刻と人ごとの忘れる速さの倍率・第 6 期 6-5)", place=EXTERNAL,
        dtype="列(i8 × k=3・行の数=体 × 器の行の幅)・f8(体の数)",
        nbytes="24 B/行+8 B/体(5,000 体・128 行で 15.4 MB)", alloc="--memory-model m1", behavior=BEHAVIOR,
        restore=REQUIRED, dead=False,
        basis="engine/memory_m1.py(M1State・base_level)・engine/memory_store.py(remember・recall・seed_people・"
              "people_rows・_resize)",
        items=("mem_layer.memory_store.m1._t_ns", "mem_layer.memory_store.m1._scale"), arm="memory-model",
        note="6-5: 腕 m1 のランだけ持ち主を作る(既定は持ち主が None=既定の 2 つのハッシュと状態のファイルは不変)。器の行ごとの"
             "直近 k 回の時刻(秒の時刻=t_ns)は記憶の表 mem_* に無い(表は最初と最後と回数だけ)=作り直せない=軸 2 required・"
             "想起の候補と順(強さ A=ACT-R の折衷形)を決める=軸 1 behavior。人ごとの倍率は母集団の seed(〔検収 M1〕組み立てが"
             "enable_memory_store にランごとに渡す)と体の番号から引ける値だが、直近の時刻と同じ持ち主にあるので一緒に保存する"
             "(required)。書く系は memory・decide・llm_receive(宣言 "
             "M0*:mem_layer.memory_store.*=器の書く口 remember の中から)。行の鍵は O の通し番号でなく M0M"),
    LedgerRow(
        key="M0C", name="CueState(意味の手がかり=手がかりの文と行の埋め込み・第 6 期 6-5)", place=EXTERNAL,
        dtype="dict(体 → 文)× 2・dict(番地 → f2 の埋め込み)・OrderedDict(文 → 埋め込みの控え)", nbytes="",
        alloc="--memory-cue embed", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/memory_embed.py(CueState)・engine/memory_store.py(note_cue・remember・recall・rebuild)・"
              "engine/memory.py(note_utterance・_recall_from_store)",
        items=("mem_layer.memory_store.cue._heard", "mem_layer.memory_store.cue._own", "mem_layer.memory_store.cue._vec",
               "mem_layer.memory_store.cue._qcache"),
        hash_skip=("mem_layer.memory_store.cue._vec", "mem_layer.memory_store.cue._qcache"), arm="memory-cue",
        note="6-5: 腕 embed のランだけ持ち主を作る。手がかりの文(会話の相手の直前の発言・本人の直前の理由)は想起の一致と順を"
             "決める=軸 1 behavior・会話の番からしか来ない=軸 2 required。行の埋め込みと手がかりの文の埋め込みの控えは注釈(要旨)と"
             "文から作り直せる=hash_skip(再開では rebuild が要旨から作り直す)。書く系は decide・llm_receive・memory(宣言 "
             "M0*:mem_layer.memory_store.*)。行の鍵は O の通し番号でなく M0C"),
    LedgerRow(
        key="M0X", name="M1State・CueState の計数(第 6 期 6-5)", place=EXTERNAL, dtype="dict(int)", nbytes="",
        alloc="腕 --memory-model m1・--memory-cue embed", behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/memory_m1.py(M1State.summary)・engine/memory_embed.py(CueState.summary)",
        items=("mem_layer.memory_store.m1._m1_stats", "mem_layer.memory_store.cue._cue_stats",
               "mem_layer.memory_store.shops._shop_stats"),
        note="6-5: 計数=読み手は manifest の memory_summary.memory_store.mr65 と試験だけ(軸 1 diag)・再開は空から(軸 2 "
             "discardable)。宣言 M0*:mem_layer.memory_store.*。〔検収 M4〕店の行の表の計数(幅を倍にした回・上限で上書きした数)も"
             "ここ。行の鍵は O の通し番号でなく M0X"),
    LedgerRow(
        key="M0S", name="ShopTable(人も記憶の一つの腕の店の評価の行・第 6 期 6-5 検収 M4)", place=EXTERNAL,
        dtype="列(体 × 幅=32 から倍にして上限 256・i4/f4/f4/i4/i4/u2/u1=体の表の sm_* と同じ型)",
        nbytes="23 B/行(上限 256 行で 5,888 B/体)", alloc="--memory-people memory(と --store-memory on)",
        behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/memory_shops.py(ShopTable・UncappedStoreMemory)・engine/store_memory.py(columns・_evict_slots・"
              "_put)・engine/memory.py(enable_store)",
        items=tuple(f"mem_layer.memory_store.shops.{a}" for a in (
            "_poi", "_valence", "_precision", "_first", "_last", "_n", "_source")), arm="memory-people",
        note="6-5(検収 M4): 腕 memory で店の記憶のあるランだけ持ち主を作る(既定は None=既定の 2 つのハッシュと状態のファイルは"
             "不変)。体の表の sm_*(上限 32 の固定の表=behavior・required)の代わり=店の選び(7c)と想起(B5)と伝聞の書き手が"
             "この表を読み書きする=軸 1 behavior・表から作れない=軸 2 required(腕 memory は再開を止める=器の側)。この腕では"
             "体の表の sm_* は書かない(空のまま)。書く系は memory・decide・llm_receive(宣言 M0*:mem_layer.memory_store.*=器の"
             "店の行の書く口 put・grow)。行の鍵は O の通し番号でなく M0S"),
    # ---- 第 6 期 6-2(カレンダー 1b=出入りを本人へ・腕 --calendar 1b): 足す前に軸を決めた行(腕の行=腕のランだけ持ち主がある) ----
    LedgerRow(
        key="C1B", name="CalendarSelf.cal_store(本人の予定の器=その日の約束・置き場所・見積り・機会・行き来の時刻・第 6 期 6-2)",
        place=EXTERNAL, dtype="体ごとの配列の dict(i1/i2/i4/i8/f4/bool・見積りの直近 K=5 は (体, 5) の f4)",
        nbytes="約 140 B/体(5,000 体で約 0.7 MB)", alloc="--calendar 1b", behavior=BEHAVIOR, restore=REQUIRED,
        dead=False,
        basis="engine/calendar_self.py(CalendarSelf.relay_day・step・_opportunities・_finish_go)・"
              "engine/systems/state_io.py(relay_tables)・engine/systems/body.py(sys_presence)",
        items=("calendar_self.cal_store",), arm="calendar",
        note="6-2: 腕 1b で母集団と計画実行層のあるランだけ持ち主を作る(既定 w17 は None=既定の 2 つのハッシュと状態のファイルは"
             "不変)。約束・置き場所・見積り(直近の実感の値)・次の機会と置いた記録・行き来の時刻・域外からの到着の予約・歩きの"
             "途中の印は、本人の出入りの判断と実行(いつ出るか・どの便で着くか・どこへ歩くか)を決める=軸 1 behavior・見積りと"
             "予約と歩きの途中は表から作れない=軸 2 required(再開=通し)。書く系は day_head(日の頭に約束と機会を張る)と "
             "presence(刻みごとの出入り)(宣言 C1B*:calendar_self.*)。行の鍵は O の通し番号でなく C1B"),
    LedgerRow(
        key="C1BM", name="CalendarSelf.cal_meter(判断の記録と計器=日ごとの記録・エンジンがしないこと 3 つの検査・第 6 期 6-2)",
        place=EXTERNAL, dtype="計数と記録の dict(日ごとの記録・出発と帰る判断の行の列・検査の数)", nbytes="",
        alloc="--calendar 1b", behavior=DIAG, restore=REQUIRED, dead=False,
        basis="engine/calendar_self.py(_summary・manifest・_check_continuity・_opportunities)・engine/run.py(manifest の "
              "calendar_1b)",
        items=("calendar_self.cal_meter",), arm="calendar",
        note="6-2: 読み手は manifest の calendar_1b と試験だけ=軸 1 diag(記録の id の通し番号は機会の参照=器の next_ref に写す"
             "値で、挙動は器の側で数える)。日をまたぐ記録(閉じた日の記録・判断の行・検査の数)は再開で作り直せない=軸 2 required"
             "(再開でも日ごとの記録が通しと同じ)。書く系は day_head と presence(宣言 C1B*:calendar_self.*)。行の鍵は C1BM"),
    # ---- 第 6 期 6-3(時計の段 T2〜T4・全部 腕): 足す前に軸を決めた行(腕の行=腕のランだけ持ち主がある・既定は空) ----
    LedgerRow(
        key="TCR", name="TalkClock の話す速さの控え(体 → モーラの長さ・第 6 期 6-3 T2)", place=EXTERNAL,
        dtype="dict(int → float)", nbytes="話した体あたり約 100 B(辞書の項)", alloc="--talk-clock mora", behavior=DIAG,
        restore=DISCARDABLE, dead=False,
        basis="engine/speech_clock.py(TalkClock.mora_len_s・person_mora_len_s)・engine/systems/llm_io.py(utter が on_turn を呼ぶ)",
        items=("talk_clock._tc_rate",), arm="talk-clock",
        note="6-3 T2: 腕 mora のランだけ組み立てが持ち主を作る(既定 table は None=既定の 2 つのハッシュと状態のファイルは不変)。"
             "人ごとのモーラの長さは母集団の seed と体の番号から引ける値の控え(最初に話したときに引く)。会話の時計は世界の状態を"
             "書かない(発言の長さと時刻を数えるだけ=記録 tm234/README.md §T2)=読み手は時計の計器と manifest の talk_clock だけ"
             "(軸 1 diag)・再開では空から引き直す(同じ値=軸 2 discardable)。書く系は decide・llm_receive(会話の番=宣言 "
             "TCR:talk_clock.*)。行の鍵は O の通し番号でなく TCR"),
    LedgerRow(
        key="TCC", name="TalkClock の会話の時計・予約した発言・計器(第 6 期 6-3 T2)", place=EXTERNAL,
        dtype="dict(会話の番号 → int の組 8=〔検収 M3〕前の番を作った時刻を含む)・dict(予約の番号 → 組)・計器の dict(int・区切りの数の組)・どれも読み取り専用の写し", nbytes="",
        alloc="--talk-clock mora", behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/speech_clock.py(TalkClock.on_turn・on_dispatch・on_close・observed)・engine/systems/conductor.py"
              "(発言の事象の種類 talk を窓の待ち行列か区域ごとの時計に置く)・engine/systems/talk.py(終わった会話)",
        items=("talk_clock._tc_line", "talk_clock._tc_pending", "talk_clock._tc_meter"), arm="talk-clock",
        note="6-3 T2: 会話ごとの時計(最初の発言の始まり・次の発言の始まり・最後の発言の終わり・発言の数・話した長さ・窓と窓の"
             "中の数)・予約した発言(窓の待ち行列の事象の番号 → 会話・話し手・始まり・長さ・モーラ数・聞く人・作った時刻)・計器"
             "(持ち越し・上限・束の大きさ・区切りごとの数)。世界の状態を書かない=軸 1 diag(会話の番は今も刻みに 1 回=つなぎの"
             "台帳 DOC-tm234-talk-clock-meter-only)。再開のランは空から(話し中の会話は再開の後の最初の発言から時計を始め直す="
             "軸 2 discardable)。書く系は decide・llm_receive(予約)・conversation(終わった会話)・窓の境目 WINDOW_MARK(発言の"
             "事象の処理)。行の鍵は O の通し番号でなく TCC"),
    LedgerRow(
        key="T3M", name="StepScope の変化の印(内受容の値と段の写し・前に跨いだ体・計器・第 6 期 6-3 T3)", place=EXTERNAL,
        dtype="dict(列の名 → u1 の配列 × 6)・i8 の配列・計器の dict", nbytes="6 B/体+跨いだ体 8 B",
        alloc="--step-scope changed", behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/step_scope.py(StepScope.marks・detect・after_detection)・engine/change_detect.py(detect の scope=)・"
              "engine/systems/perceive.py(sys_detect)",
        items=("step_scope._ss_copy", "step_scope._ss_crossed", "step_scope._ss_meter"), arm="step-scope",
        note="6-3 T3: 腕 changed のランだけ持ち主を作る。写しは「内受容の判定の結果が変わりうる体」を選ぶだけで、判定の結果は"
             "全員を見る版と同じ(受入=byte-check 19 構成)=結果を変えない控え=軸 1 diag(3-5 の BD と同じ扱い)。再開では写しを"
             "捨てる(再開の後の最初の検出は全員=軸 2 discardable)。書く系は detect(宣言 T3M:step_scope.*)。行の鍵は T3M"),
    LedgerRow(
        key="T4W", name="RegionalClock の区域ごとの窓・区域の事象・体の区域の写し・遅刻の日の表・計器(第 6 期 6-3 T4)",
        place=EXTERNAL,
        dtype="i8 の配列(区域の数)・dict(区域 → 事象の組の list)・int・i8 の配列(体)・組(日・i8 × 3・f8)・計器の dict",
        nbytes="8 B/体(区域の写し)+区域 30 × 8 B+日の表 1,440 × 32 B", alloc="--clock regional", behavior=DIAG,
        restore=DISCARDABLE, dead=False,
        basis="engine/regional_clock.py(RegionalClock.schedule・run_windows・hear_delay_ns・observed)・"
              "engine/systems/conductor.py(窓のループの後に区域ごとの窓)",
        items=("clock._rc_head", "clock._rc_events", "clock._rc_seq", "clock._rc_snap", "clock._rc_late",
               "clock._rc_meter"), arm="clock-regional",
        note="6-3 T4: 腕 regional のランだけ進行役が持ち主を作る(既定 global は None)。区域ごとの窓の頭と区域の事象(会話の"
             "時計の発言の事象)・境目の移動を数える体の区域の写し・遅刻の日の表・計器(区域の窓・区域をまたぐ事象と遅れ・聞く人の"
             "区域またぎの遅れ・遅刻)。世界の状態を書かない(系は全員の配列を 1 回で処理する=全体で 1 つの時計と同じ結果=受入の"
             "条件=構造上いつも成り立つ一致=〔検収 M4〕)=軸 1 diag・再開では進行役が作り直す=軸 2 discardable。書くのは進行役"
             "(窓の境目 WINDOW_MARK に帰属)と会話の番の発言の予約(〔検収 M1〕系 decide・llm_receive=宣言 T4W:clock.*)。"
             "行の鍵は O の通し番号でなく T4W"),
    # ---- 第 6 期 6-4 C1(連絡の道具・腕 --contact c1): 足す前に軸を決めた行(腕の行=腕 c1 のランだけ持ち主がある=既定の
    # 2 つのハッシュと状態のファイルは不変) ----
    LedgerRow(
        key="CT1D", name="Devices(道具の状態=電源・電池・マナーモード・置き場・イヤホン・第 6 期 6-4 C1)", place=EXTERNAL,
        dtype="列(体ごと bool・float32・bool・i1・i1・bool)", nbytes="9 B/体", alloc="--contact c1", behavior=BEHAVIOR,
        restore=REQUIRED, dead=False,
        basis="engine/contact/device.py(Devices.stimulus・drain・take_out・put_back)・engine/contact/layer.py(run_step・"
              "percept_hook)",
        items=tuple(f"contact.dev.{a}" for a in ("_on", "_battery", "_manner", "_home", "_place", "_ear")),
        arm="contact-c1",
        note="6-4 C1: 道具の状態(CT0 の共通の決まり 2・3)は通知の刺激の段・電源(届くか)・知覚の事実の道具の状態を決める=軸 1 "
             "behavior。電池と置き場は本人の行動と物理で動く=作り直せない=軸 2 required(最初の状態は母集団の側の乱数=作り直せる"
             "が同じ持ち主にあるので一緒に保存する)。書く系は contact だけ(宣言 CT1*:contact.*)。行の鍵は O の通し番号でなく CT1D"),
    LedgerRow(
        key="CT1A", name="Attention(目と心の向き=視線の先・関心の的・前の刻みの活動・最後に気づいた通知・第 6 期 6-4 C1)",
        place=EXTERNAL, dtype="列(体ごと i1 × 3)・dict(体 → [時刻, 種類, 段, チャネル])", nbytes="3 B/体+気づいた体ごとに約 100 B",
        alloc="--contact c1", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/contact/attention.py(Attention・coarsen・gate_salient)・engine/contact/layer.py(run_step・percept_hook)",
        items=tuple(f"contact.attn.{a}" for a in ("_gaze", "_focus", "_prev_act", "_notice")),
        arm="contact-c1",
        note="6-4 C1: 視線の先と関心の的は知覚の事実の形(周辺視・割り込めなかった出来事)と気づきの門と判断の候補を決める=軸 1 "
             "behavior。前の刻みの活動(暇になった境目)と最後に気づいた通知(次の刻みの知覚の事実と着信の判断)も同じ=刻みをまたぐ="
             "軸 2 required。書く系は contact だけ(宣言 CT1*:contact.*)。行の鍵は CT1A"),
    LedgerRow(
        key="CT1AS", name="Attention._gaze_since(今の視線になった時刻=画面を見ていた長さの計器の素・第 6 期 6-4 C1)",
        place=EXTERNAL, dtype="列(体ごと i8)", nbytes="8 B/体", alloc="--contact c1", behavior=DIAG, restore=REQUIRED,
        dead=False, basis="engine/contact/attention.py(look_at_screen・look_up)・engine/contact/layer.py(計器)",
        items=("contact.attn._gaze_since",), arm="contact-c1",
        note="6-4 C1: 読み手は画面を見ていた長さの計器だけ=軸 1 diag。画面を見ている途中の再開で長さが通しと同じになる=軸 2 "
             "required(O37 と同じ形)。書く系は contact だけ"),
    LedgerRow(
        key="CT1I", name="Mailbox(届いた箱・新しく届いた数・網が預かる分・窓の境目の予約・着信と呼び出し・番号・第 6 期 6-4 C1)",
        place=EXTERNAL,
        dtype="dict(体 → 届いた行の list)・dict(体 → [数, 時刻])・dict(体 → 行の list)・dict(鍵 → 予約の行)・dict × 2・list[int]",
        nbytes="届いた行 1 つ約 150 B(本文を含む)・既読は 1 日で落とす", alloc="--contact c1", behavior=BEHAVIOR,
        restore=REQUIRED, dead=False,
        basis="engine/contact/deliver.py(Mailbox)・engine/contact/layer.py(_send_now・_ring_now・_read・_system1・bind_queue)",
        items=tuple(f"contact.mail.{a}" for a in ("_inbox", "_unseen", "_held", "_pending", "_ringing", "_calling",
                                                 "_next")),
        arm="contact-c1",
        note="6-4 C1: 届いた・未読・予約・着信は通知の刺激と判断の候補(読む・出る)と知覚の事実(未読の数)を決める=軸 1 behavior。"
             "刻みと日をまたぐ=軸 2 required。進行役の待ち行列(行 BW=捨ててよい)に入れた送信と着信は予約の表 _pending に持ち、"
             "再開では組み立ての後の結び(ContactLayer.bind_queue)が境目の時刻で入れ直す=通しと同じ。書く系は contact と窓の境目の"
             "処理(進行役の WINDOW_MARK=宣言 conductor.WINDOW_PATHS)。行の鍵は CT1I。〔1-3 の (1) の直し〕届いた行は出来事の"
             "記録の id を持たない(診断の表 contact._ct_event_of=行 CT1Q)=記録 on/off で行が同じ"),
    LedgerRow(
        key="CT1IS", name="Mailbox._sent(送ったメッセージの既読の数=道具の性質・第 6 期 6-4 C1)", place=EXTERNAL,
        dtype="dict(番号 → [送り手, 道具, 時刻, 届け先の数, 読んだ数])", nbytes="1 通 約 80 B(読み終わるか 1 日で落とす)",
        alloc="--contact c1", behavior=DIAG, restore=REQUIRED, dead=False,
        basis="engine/contact/deliver.py(read_all・prune・counts)",
        items=("contact.mail._sent",), arm="contact-c1",
        note="6-4 C1: 既読の印(送った側の道具の性質)。本段では送った側の判断の候補にまだ載せない(読み手は計器と掃除だけ)=軸 1 "
             "diag。日をまたぐ=軸 2 required。送った側の予想とのずれ(驚き)を判断に載せる段で behavior へ"),
    LedgerRow(
        key="CT1C", name="ChatBook(チャットの会話の状態=対面の会話の器 ConversationManager の子・第 6 期 6-4 C1)", place=EXTERNAL,
        dtype="dataclass・辞書(O39・O40・O91 と同じ形)・dict(鍵 → 番号)", nbytes="", alloc="--contact c1", behavior=BEHAVIOR,
        restore=REQUIRED, dead=False, ordered=True,
        basis="engine/conversation.py(ConversationManager.step・_close・_terminate・purge_terminal)・"
              "engine/contact/chat_state.py(ChatBook.on_message・step・partners_of)・engine/contact/layer.py(percept_hook)",
        items=tuple(f"contact.chats.{a}" for a in (
            "sessions", "_of_agent", "_refusal_until", "_next_id", "pending_invites", "_pair_invite_until",
            "_speaker_invite_until", "join_events", "n_opened", "_of_key")),
        arm="contact-c1",
        note="6-4 C1: 続いているチャットの相手は知覚の事実(画面の道具の状態)に載る・沈黙で締める=軸 1 behavior・刻みをまたぐ="
             "軸 2 required。表の挿入順が相手の並び=順を保つ(ordered)。書く系は contact と窓の境目の処理(送った時)"),
    LedgerRow(
        key="CT1K", name="CallManager(電話の会話=ConversationManager のセッションと表・第 6 期 6-4 C1)", place=EXTERNAL,
        dtype="dataclass・辞書(O39・O40・O91 と同じ形)", nbytes="", alloc="--contact c1", behavior=BEHAVIOR,
        restore=REQUIRED, dead=False, ordered=True,
        basis="engine/conversation.py(ConversationManager)・engine/contact/calls.py(CallManager)・engine/contact/layer.py"
              "(_calls_turns・_ring_decisions・run_step)",
        items=tuple(f"contact.calls.{a}" for a in (
            "sessions", "_of_agent", "_refusal_until", "_next_id", "pending_invites", "_pair_invite_until",
            "_speaker_invite_until", "join_events", "n_opened")),
        arm="contact-c1",
        note="6-4 C1: 対面の会話と同じ器(行 O39・O40・O91 と同じ属性)=通話の番の話者・終わり・話し中を決める=軸 1 behavior・"
             "軸 2 required。sessions の走査の順が番の処理の順=順を保つ(ordered)。書く系は contact だけ"),
    LedgerRow(
        key="CT1S", name="CallSpeechPort.inbox(通話の相手の次の番に載る発話・第 6 期 6-4 C1)", place=EXTERNAL,
        dtype="dict(体 → 未読の発話の列)", nbytes="", alloc="--contact c1", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/speech/port.py(SpeechPort.say・take_heard)・engine/contact/layer.py(_calls_turns)",
        items=("contact.speech.inbox",), arm="contact-c1",
        note="6-4 C1: 通話の発話(1-8b の口そのまま・道具=通話)。相手の次の番の判断の入力(原因の入力の出来事)=軸 1 behavior・"
             "軸 2 required(行 S8 と同じ形)。書く系は contact だけ。〔1-3 の (1) の直し〕未読の列の目印は記録に依らない口の通し番号"
             "(t_ns, 通し番号)だけ=出来事の id は診断の表 contact.speech._mark_event_of(行 CT1Q・発話の口の行 S8E と同じ形)"),
    LedgerRow(
        key="CT1M", name="連絡の道具の計器(層・チャット・通話・通話の発話の口の計数と分布・通話の切った判断の控え・第 6 期 6-4 C1)",
        place=EXTERNAL, dtype="計数の dict・分布の dict・dict(通話 → call_id)・list(前の刻みの気づき)", nbytes="",
        alloc="--contact c1", behavior=DIAG, restore=DISCARDABLE, dead=False,
        basis="engine/contact/layer.py(_bump・_hist_add・manifest)・engine/contact/chat_state.py(counts)・"
              "engine/conversation.py(counters)・engine/speech/port.py(observed)",
        items=("contact._meter", "contact._ct_hist", "contact._hangup", "contact._exposed_prev",
               "contact.chats._chat_meter",
               *(f"contact.chats.{a}" for a in (
                   "n_ignored_invites", "n_gate_rejected", "n_invites", "n_accepted", "n_declined", "n_pending_expired",
                   "n_invite_refractory_blocked", "n_blocks", "n_backchannels", "n_interrupts", "closed_by_reason",
                   "ignored_events", "size_hist", "n_expired_purged", "origin_counts")),
               *(f"contact.calls.{a}" for a in (
                   "n_ignored_invites", "n_gate_rejected", "n_invites", "n_accepted", "n_declined", "n_pending_expired",
                   "n_invite_refractory_blocked", "n_blocks", "n_backchannels", "n_interrupts", "closed_by_reason",
                   "ignored_events", "size_hist", "n_expired_purged", "origin_counts")),
               "contact.speech.meter", "contact.speech._last_input", "contact.speech._own_last",
               "contact.speech._heard_taken"),
        arm="contact-c1",
        note="6-4 C1: 計器=読み手は manifest の contact_c1 と試験だけ(軸 1 diag)・再開は空から(軸 2 discardable)。通話の切った判断の"
             "控え(通話の終わりの出来事の原因)と前の刻みの気づき(記憶に残ったかの数え)も診断。書く系は contact と窓の境目の処理"),
    LedgerRow(
        key="CT1G", name="連絡の層が系の間に渡す値(顕著行為の門を通った気づいた体・仲裁で回した判断・主の判断が選んだ「スマホを見る」・"
                         "第 6 期 6-4 C1 検収 M1・M5)",
        place=EXTERNAL, dtype="list[配列]・list[int]・dict(体 → 種類)・dict(体 → [call_id, 番号])", nbytes="",
        alloc="--contact c1", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/contact/layer.py(_salient_gate・salient_view・_person_decisions・take_main・_take_main_looks)・"
              "engine/systems/remember.py(_salient_for_memory)・engine/decision/layer.py(decide_one)",
        items=tuple(f"contact.{a}" for a in ("_sal_noticed", "_sal_step", "_defer", "_look_main")),
        arm="contact-c1",
        note="6-4 C1 検収 M1: 顕著行為の門の結果(気づいた体)は連絡の持ち主の側に持ち、記憶の系が salient_view で読む(記憶の書き手の "
             "(c) 気づき=軸 1 behavior・顕著行為の過程のキャッシュは書き換えない)。M5: 仲裁で次の刻みに回した通知と暇の判断・主の判断"
             "(判断の系)が選んだ「スマホを見る」(同じ刻みの系 contact が読む=刻みの境目では空)も行動を決める=behavior。刻みをまたぐ"
             "のは _defer だけだが、同じ持ち主の 4 つを一緒に保存する=軸 2 required。書く系は contact と判断の系(_look_main=宣言 "
             "CT1G:contact._look_main)。行の鍵は CT1G"),
    LedgerRow(
        key="CT1Q", name="発行した連絡の判断の呼びの控えと呼び数・出来事の id の診断の表(監査の突き合わせ・calls_by_model・原因の入力・"
                         "第 6 期 6-4 C1 検収 M2・M5・1-3 の (1) の直し)",
        place=EXTERNAL, dtype="i8 の配列(刻み・体・通し番号を詰めた整数)・list[int](控えの数・判断の呼び・文の口の呼び)・"
                              "dict(体 → [[番号, t_ns, seq]])・dict((t_ns, 通し番号) → (t_ns, seq))",
        nbytes="1 回 8 B(5,000 体 1 日 約 22 万回=約 1.8 MB)・未読の届いた行と未読の通話の発話ごとに目印 1 つ", alloc="--contact c1",
        behavior=DIAG, restore=REQUIRED, dead=False,
        basis="engine/contact/layer.py(_issue・issued_keys・model_calls・audit_causes・_send_now・_unread_basis・_drop_read_marks・"
              "_calls_turns)・engine/speech/port.py(SpeechPort.say・event_ids)・engine/run.py(_calls_by_model)・"
              "engine/systems/state_io.py(日次の記録の calls_by_model)",
        items=("contact._issued", "contact._issued_n", "contact._ct_event_of", "contact.speech._mark_event_of"),
        arm="contact-c1",
        note="6-4 C1 検収 M2: 読み手は監査(試験と記録の道具)と manifest・日次の記録の calls_by_model だけ=軸 1 diag。再開した"
             "ランの監査と呼び数が通しと同じになる=軸 2 required。既定化の前に日ごとの監査で捨てる形に改める(量=記録 §5-2)。"
             "〔1-3 の (1) の直し〕出来事の記録の id(届いた行の目印 _ct_event_of・通話の発話の目印 speech._mark_event_of=行 S8E と同じ形)"
             "もここ=読み手は"
             "読む判断と通話の番の判断の原因の入力(原因の表)だけ=軸 1 diag(記録 on/off で behavior の行 CT1I・CT1S が変わらない)。"
             "再開したランの原因の入力が通しと同じ=軸 2 required(カレンダー 2 の CA2M と同じ形)"),
    # ---- 〔第 6 期 6-2 カレンダー 2〕会話から生まれる予定(腕 --calendar-2 arm): 足す前に軸を決めた行(腕の行=腕 arm のランだけ
    # 持ち主がある=既定のランの 2 つのハッシュと状態のファイルは不変) ----
    LedgerRow(
        key="CA2B", name="PromiseBook(本人の予定の器=各自が自分の理解の行・第 6 期 6-2 カレンダー 2)", place=EXTERNAL,
        dtype="dict(行の番号 → 行の dict)・dict(持ち主 → 行の番号の列)・list[int]", nbytes="行 1 つ約 400 B",
        alloc="--calendar-2 arm", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/calendar2/book.py(PromiseBook.write・edit・observe・drop・own_rows)・engine/calendar2/layer.py",
        items=("calendar2.book.rows", "calendar2.book.by_owner", "calendar2.book.next_id"), arm="calendar-2",
        note="6-2 カレンダー 2: 本人の行(いつ・どこ・誰と・何を・置き場所・確かさ・元の会話)が見える予定と出発の判断を決める="
             "軸 1 behavior・表から作れない=軸 2 required。書く系は calendar_2 だけ(宣言 CA2*:calendar2.*)。行の鍵は CA2B"),
    LedgerRow(
        key="CA2O", name="Calendar2Layer の誘い・帳面・歩いている行・知らせ・手帳・範囲の外の印(第 6 期 6-2 カレンダー 2)",
        place=EXTERNAL, dtype="dict(誘い)・list[int]・dict(刻み → [[種類, 行]])・list[int]・dict・dict・bool の配列(体ごと)・dict",
        nbytes="範囲の外の印 1 B/体", alloc="--calendar-2 arm", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/calendar2/layer.py(_propose・_respond・_hear・_settle_offers・_schedule_row・_opportunities・_look・"
              "_depart・_track・_outside・run_step)",
        items=tuple(f"calendar2.{a}" for a in ("_offers", "_offer_next", "_agenda", "_watch", "_noticed",
                                               "_planner_day", "_was_out", "_out_row", "_days")),
        arm="calendar-2",
        note="6-2 カレンダー 2: 返事待ちの誘い・本人が選んだ知らせの時刻と行の始まりと終わりの帳面・知らせで次に見える行・手帳を"
             "開いた日・範囲の外に出た/戻った印は、どれも次の判断と記録を決める=軸 1 behavior・作り直せない=軸 2 required。"
             "書く系は calendar_2 だけ。行の鍵は CA2O"),
    LedgerRow(
        key="CA2G", name="Calendar2Layer が系の間と刻みの間に渡す値(会話の番の控え・仲裁で回した考えた体・第 6 期 6-2 カレンダー 2)",
        place=EXTERNAL, dtype="list[[会話の鍵, 体, 刻み, 番の id, [相手]]]・dict(体 → 刻み)", nbytes="",
        alloc="--calendar-2 arm", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/calendar2/layer.py(note_turn・run_step・_opportunities)・engine/systems/llm_io.py(utter)・"
              "engine/contact/layer.py(_calls_turns・_queue_send)",
        items=("calendar2._turns", "calendar2._think"), arm="calendar-2",
        note="6-2 カレンダー 2: 会話の番の控えは対面の会話の番(判断の系と到着の系=宣言 CA2G:calendar2._turns)・通話の番とメッセージを"
             "送る判断(連絡の系)が積み、同じ刻みの系 calendar_2 が読む(刻みの境目では空)。仲裁で次の刻みに回した考えた体は刻みを"
             "またぐ。どちらも判断を決める=behavior・一緒に保存する=軸 2 required。行の鍵は CA2G"),
    LedgerRow(
        key="CA2M", name="カレンダー 2 の計器(計数・分布・体ごとの約束の数・第 6 期 6-2)", place=EXTERNAL,
        dtype="計数の dict・分布の dict・dict(体 → 数)", nbytes="", alloc="--calendar-2 arm", behavior=DIAG,
        restore=REQUIRED, dead=False, basis="engine/calendar2/layer.py(_bump・_hist_add・manifest)",
        items=("calendar2._c2_meter", "calendar2._c2_hist", "calendar2._c2_per_agent", "calendar2._c2_event_of",
               "calendar2._c2_offer_event"), arm="calendar-2",
        note="6-2 カレンダー 2: 読み手は manifest の calendar_2 と試験だけ=軸 1 diag。再開した後も 1 週間あたりの約束の数・忘れた割合が"
             "通しと同じ=軸 2 required(1b の C1BM と同じ形)。〔検収 M3〕書いた出来事と誘った出来事の id(行と誘いの目印=返事の"
             "判断の入力の目印として原因の表だけが読む)もここ=記録の有無で behavior の行が変わらない(口の約束 1-3 の (1))"),
    LedgerRow(
        key="CA2Q", name="発行したカレンダー 2 の判断の呼びの控えと呼び数(監査の突き合わせ・第 6 期 6-2)", place=EXTERNAL,
        dtype="i8 の配列(刻み・体・通し番号を詰めた整数)・list[int](控えの数・判断の呼び・文の口の呼び)",
        nbytes="1 回 8 B", alloc="--calendar-2 arm", behavior=DIAG, restore=REQUIRED, dead=False,
        basis="engine/calendar2/layer.py(_issue・issued_keys・model_calls・audit_causes)",
        items=("calendar2._c2_issued", "calendar2._c2_issued_n"), arm="calendar-2",
        note="6-2 カレンダー 2: 読み手は監査(試験と記録の道具)と manifest だけ=軸 1 diag。再開したランの監査が通しと同じ=軸 2 "
             "required(C1 の CT1Q と同じ形)"),
    # ---- 〔第 4 期 4-2〕店の預かり消費税(Q1・腕 SHIBUYA_RULES_42=on のランで税の部品が動くときだけ持ち主がある=腕 off の
    # ランの 2 つのハッシュと状態のファイルは不変) ----
    LedgerRow(
        key="TXD", name="TaxDeposit(店の預かり消費税=課税期間の年 → 店ごとの預かり額・累計・第 4 期 4-2)", place=EXTERNAL,
        dtype="dict(年 → i8 の配列=店の数)・計数の dict", nbytes="課税期間 1 つあたり 8 B/店(2,337 店で 18.7 KB)",
        alloc="SHIBUYA_RULES_42=on(既定)", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="economy/tax_deposit.py(TaxDeposit.collect・remit_due)・economy/stage2.py(purchase・before_close)",
        items=("ledger.money.stage2.tax_deposit.held", "ledger.money.stage2.tax_deposit.totals"), arm="rules-42",
        note="4-2(Q1): レジの税を店の預かり金に積み、申告の期限の日の締めに店 → 政府へ移す。預かり額が期限の納付の額を決める="
             "軸 1 behavior・積んだ額は作り直せない=軸 2 required。書く系は phase_c(レジ)・day_close と close_final(期限の"
             "納付)=宣言 TXD:ledger.*。累計(積んだ・移した・移せなかった)は保存則の検算(economy.checks.tax_deposit_check)の"
             "材料=再開の後も通しと同じ。行の鍵は TXD"),
    # ---- 〔第 6 期 6-2 カレンダー 3〕雇い主・祝日(C3 職場の連絡と束ねる・腕 --calendar-3 arm): 足す前に軸を決めた行(腕の行=
    # 腕 arm のランだけ持ち主がある=既定のランの 2 つのハッシュと状態のファイルは不変) ----
    LedgerRow(
        key="CA3S", name="Calendar3Layer の雇い主の記録(組んだ週・組んだシフト・第 6 期 6-2 カレンダー 3)", place=EXTERNAL,
        dtype="dict(単位 → 週の最初の日)・dict(単位 → {働く人: [[日, 枠の番号]]})・dict(シフトを組む人 → 週の最初の日)",
        nbytes="働く人 1 人 1 週 7 組", alloc="--calendar-3 arm", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/calendar3/layer.py(_begin_compose・_compose・_answer・_due_units・_act)",
        items=("calendar3._composed", "calendar3._plan", "calendar3._compose_due"), arm="calendar-3",
        note="6-2 カレンダー 3: 雇い主が組んだシフト(自分の記録)と組んだ週が、次に組むかと休みの申し出の返事の後の記録を決める="
             "軸 1 behavior・作り直せない=軸 2 required。書く系は calendar_3 だけ(宣言 CA3*:calendar3.*)。行の鍵は CA3S"),
    LedgerRow(
        key="CA3P", name="Calendar3Layer の C3 の連絡の控え・帳面・勤務の行の表・知らせの印・通し番号(第 6 期 6-2 カレンダー 3)",
        place=EXTERNAL, dtype="dict(call_id → 中身)・dict(メッセージの番号 → 中身)・dict(体 → 中身)・dict(体 → 中身の列)・"
                              "dict(刻み → [[種類, 行]])・dict(行 → [働く人, 単位, 雇い主, 日])・dict(体 → 行の列)・list[int]",
        nbytes="中身 1 つ約 200 B", alloc="--calendar-3 arm", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/calendar3/layer.py(note_sent・_send・_poll_calls・_deliver・_write_rows・_schedule_row・_agenda_step・"
              "_act・_prune・run_step)",
        items=tuple(f"calendar3.{a}" for a in ("_out", "_msg", "_calls", "_wait", "_agenda", "_work_rows", "_noticed", "_next",
                                               "_days")),
        arm="calendar-3",
        note="6-2 カレンダー 3: 送った/送れなかった/電話の C3 の連絡の中身・本人が選んだ知らせの時刻と行の終わりの帳面・勤務の行の"
             "雇い主と単位・知らせが鳴った行は、どれも次の判断と記録を決める=軸 1 behavior・作り直せない=軸 2 required。送った判断の "
             "call_id → メッセージの番号は網の打ち終わり(窓の境目=C1 の _send_now の口 sent_sink)が移す。書く系は calendar_3。"
             "行の鍵は CA3P"),
    LedgerRow(
        key="CA3G", name="Calendar3Layer が系の間と刻みの間に渡す値(読んだ C3 の連絡の控え・仲裁で回した考えた体・第 6 期 6-2)",
        place=EXTERNAL, dtype="list[[体, メッセージの番号, 送った人, グループ, 道具]]・dict(体 → 刻み)", nbytes="",
        alloc="--calendar-3 arm", behavior=BEHAVIOR, restore=REQUIRED, dead=False,
        basis="engine/calendar3/layer.py(note_read・run_step・_opportunities)・engine/contact/layer.py(_read)",
        items=("calendar3._reads", "calendar3._think"), arm="calendar-3",
        note="6-2 カレンダー 3: 読んだ C3 の連絡の控えは連絡の系の読む判断(宣言 CA3G:calendar3._reads)が積み、同じ刻みの系 "
             "calendar_3 が読む(刻みの境目では空)。仲裁で次の刻みに回した考えた体は刻みをまたぐ。どちらも判断を決める=behavior・"
             "一緒に保存する=軸 2 required。行の鍵は CA3G"),
    LedgerRow(
        key="CA3M", name="カレンダー 3 の計器(計数・分布・休みの申し出の出来事の id・第 6 期 6-2)", place=EXTERNAL,
        dtype="計数の dict・分布の dict・dict(申し出の番号 → 出来事の id)", nbytes="", alloc="--calendar-3 arm",
        behavior=DIAG, restore=REQUIRED, dead=False, basis="engine/calendar3/layer.py(_bump・_hist_add・_ask_rest・manifest)",
        items=("calendar3._c3_meter", "calendar3._c3_hist", "calendar3._c3_event_of"), arm="calendar-3",
        note="6-2 カレンダー 3: 読み手は manifest の calendar_3 と試験だけ=軸 1 diag。再開した後も計器が通しと同じ=軸 2 required"
             "(カレンダー 2 の CA2M と同じ形)。休みの申し出の出来事の id(返事の判断の入力の目印=原因の表だけが読む)もここ=記録の"
             "有無で behavior の行が変わらない(口の約束 1-3 の (1))"),
    LedgerRow(
        key="CA3Q", name="発行したカレンダー 3 の判断の呼びの控えと呼び数(監査の突き合わせ・第 6 期 6-2)", place=EXTERNAL,
        dtype="i8 の配列(刻み・体・通し番号を詰めた整数)・list[int](控えの数・判断の呼び・文の口の呼び)",
        nbytes="1 回 8 B", alloc="--calendar-3 arm", behavior=DIAG, restore=REQUIRED, dead=False,
        basis="engine/calendar3/layer.py(_issue・issued_keys・model_calls・audit_causes)",
        items=("calendar3._c3_issued", "calendar3._c3_issued_n"), arm="calendar-3",
        note="6-2 カレンダー 3: 読み手は監査(試験と記録の道具)と manifest・calls_by_model だけ=軸 1 diag。再開したランの監査が"
             "通しと同じ=軸 2 required(CA2Q と同じ形)"),
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
    """full-hash に入れる外の状態の ``(行の鍵, 属性の道筋)``(台帳の宣言順)。〔1-8b〕腕の行は入れない(``arm_items``)。"""
    out: list[tuple[str, str]] = []
    for r in external_rows():
        if not r.in_full or r.arm:
            continue
        skip = set(r.hash_skip)
        out.extend((r.key, it) for it in r.items if it not in skip)
    return tuple(out)


def arm_rows() -> tuple[LedgerRow, ...]:
    """〔第 1 期 1-8b〕腕の行(``LedgerRow.arm`` のある外の状態の行・宣言順)。"""
    return tuple(r for r in external_rows() if r.arm)


def arm_items(owners: Mapping[str, object], *, behavior: bool) -> tuple[tuple[str, str], ...]:
    """〔第 1 期 1-8b〕腕の行のうち根の持ち主が居る(腕が立っている)行の ``(行の鍵, 属性の道筋)``(宣言順・``hash_skip`` を除く)。

    ``behavior=True`` は軸 1 が behavior の行(behavior-hash の末尾に足す)・``False`` は軸 2 が full に入る行(full-hash と
    状態のファイルの末尾に足す)。持ち主が None か ``owners`` に無いランは何も返さない=既定の 2 つのハッシュと状態のファイルは
    腕の行を足す前と同じバイト。〔1-8b 検収 低7〕持ち主が居るときは持ち主の腕の名(クラスの定数 ``LEDGER_ARM``)を行の
    ``arm`` と照合する(違えば配線の誤り=``ValueError``=別の腕の持ち主を同じ根の名に挿しても黙って入れない)。
    """
    out: list[tuple[str, str]] = []
    for r in arm_rows():
        if (r.behavior != BEHAVIOR) if behavior else (not r.in_full):
            continue
        owner = _owner_at(owners, r.arm_owner)
        if owner is None:
            continue
        got = getattr(type(owner), "LEDGER_ARM", None)
        if got != r.arm:
            raise ValueError(f"状態台帳の腕の行 {r.key} の腕 {r.arm!r} と持ち主 {r.arm_owner} の腕 {got!r} が違う(配線の誤り)")
        skip = set(r.hash_skip)
        out.extend((r.key, it) for it in r.items if it not in skip)
    return tuple(out)


def _owner_at(owners: Mapping[str, object], path: str) -> object | None:
    """〔第 2 期 2-3〕持ち主の道筋(根の鍵から ``.`` でたどる)→ 物(途中が無いか None なら ``None``)。"""
    root, *rest = path.split(".")
    cur = owners.get(root)
    for a in rest:  # 逐次ループ宣言: 道筋の段の数(≤ 2)
        if cur is None:
            return None
        cur = getattr(cur, a, None)
    return cur


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
    # 第 1 期 1-6: 記憶の器 M0(状態台帳の行 M0・M0R・腕 --memory-store events のランだけ)
    "mem_layer.memory_store": ("engine/memory_store.py", "MemoryStore"),
    # 〔第 6 期 6-5〕器の子の持ち主(腕 --memory-model m1 の M1 の状態・腕 --memory-cue embed の意味の手がかり)
    "mem_layer.memory_store.m1": ("engine/memory_m1.py", "M1State"),
    "mem_layer.memory_store.cue": ("engine/memory_embed.py", "CueState"),
    # 〔第 6 期 6-5・検収 M4〕人も記憶の一つの腕の店の評価の行(腕 --memory-people memory で店の記憶のあるラン)
    "mem_layer.memory_store.shops": ("engine/memory_shops.py", "ShopTable"),
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
    # 第 1 期 1-3: 出来事の記録(状態台帳の行 E)
    "events": ("engine/events/log.py", "EventLog"),
    # 第 1 期 1-8 J0: 候補の口の層(状態台帳の行 J0・腕 --decision-port port のランだけ)
    "decision": ("engine/decision/layer.py", "DecisionLayer"),
    # 第 1 期 1-8b: 発話の口(状態台帳の腕の行 S8・S8M・腕 --speech-port on のランだけ)
    "speech": ("engine/speech/port.py", "SpeechPort"),
    # 第 2 期 2-2 段 11a: 近接の層(状態台帳の行 PX・腕 --proximity distance のランだけ)
    "proximity": ("engine/proximity.py", "ProximityLayer"),
    # 第 3 期 3-3: 申込書の持ち主(状態台帳の行 X・申込書を渡したランだけ)
    "experiment": ("engine/experiment/layer.py", "ExperimentLayer"),
    # 第 3 期 3-2: 計算のまとめの窓(状態台帳の行 BW・進行役が置く)
    "batching": ("engine/batching.py", "WindowQueue"),
    # 第 3 期 3-5: 本人の体の層(状態台帳の行 BD・どの腕でも置く)
    "body": ("engine/body/model.py", "BodyModel"),
    # 第 3 期 3-1: 暦 1a の影(状態台帳の行 CAL・腕 --calendar-shadow 1a のランだけ)
    "calendar_shadow": ("engine/calendar_shadow.py", "CalendarShadow"),
    # 第 6 期 6-2: カレンダー 1b(状態台帳の腕の行 C1B・C1BM・腕 --calendar 1b のランだけ)
    "calendar_self": ("engine/calendar_self.py", "CalendarSelf"),
    # 第 6 期 6-3: 時計の段 T2〜T4 の腕の持ち主(状態台帳の腕の行 TCR・TCC・T3M・T4W・腕のランだけ)
    "talk_clock": ("engine/speech_clock.py", "TalkClock"),
    "step_scope": ("engine/step_scope.py", "StepScope"),
    "clock": ("engine/regional_clock.py", "RegionalClock"),
    # 〔第 6 期 6-4 C1〕連絡の道具(状態台帳の腕の行 CT1*・腕 --contact c1 のランだけ)と子の持ち主
    "contact": ("engine/contact/layer.py", "ContactLayer"),
    "contact.dev": ("engine/contact/device.py", "Devices"),
    "contact.attn": ("engine/contact/attention.py", "Attention"),
    "contact.mail": ("engine/contact/deliver.py", "Mailbox"),
    "contact.chats": ("engine/conversation.py", "ConversationManager"),
    "contact.calls": ("engine/conversation.py", "ConversationManager"),
    "contact.speech": ("engine/speech/port.py", "SpeechPort"),
    # 〔第 6 期 6-2 カレンダー 2〕会話から生まれる予定(状態台帳の腕の行 CA2*・腕 --calendar-2 arm のランだけ)と子の持ち主
    "calendar2": ("engine/calendar2/layer.py", "Calendar2Layer"),
    "calendar2.book": ("engine/calendar2/book.py", "PromiseBook"),
    # 〔第 4 期 4-2〕店の預かり消費税(状態台帳の腕の行 TXD・腕 SHIBUYA_RULES_42=on のランだけ)
    "ledger.money.stage2.tax_deposit": ("economy/tax_deposit.py", "TaxDeposit"),
    # 〔第 6 期 6-2 カレンダー 3〕雇い主・祝日(状態台帳の腕の行 CA3*・腕 --calendar-3 arm のランだけ)
    "calendar3": ("engine/calendar3/layer.py", "Calendar3Layer"),
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
    # 〔第 6 期 6-5〕人も記憶の一つの腕(--memory-people memory)の関係の読み口=RelationLayer の子クラス
    "rel_layer": (("engine/relations_people.py", "PeopleRelationLayer"),),
    # 〔第 6 期 6-5・検収 M4〕人も記憶の一つの腕の店の評価の記憶=StoreMemory の子クラス(行の口だけ差し替える)
    "mem_layer.store": (("engine/memory_shops.py", "UncappedStoreMemory"),),
    # 〔第 6 期 6-4 C1〕電話の会話と通話の発話の口=対面の会話と発話の口の子クラス(腕の名だけ足す)
    "contact.calls": (("engine/contact/calls.py", "CallManager"),),
    "contact.chats": (("engine/contact/chat_state.py", "ChatBook"),),
    "contact.speech": (("engine/contact/calls.py", "CallSpeechPort"),),
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
    _x("act_layer", CONST, _CFG, "n", "salt", "minutes_per_tick", "_tpd"),
    _x("act_layer", CACHE, "ぶらつきの近傍の表(資産から作る)", "_nbr_start", "_nbr_cells"),
    _x("intent_layer", CONST, _CFG, "n", "max_ticks"),
    _x("intent_layer", REF, _REFR, "world"),
    _x("intent_layer", CACHE, _TAB, "_poi_cell"),
    _x("fam_layer", CONST, _CFG, "n", "k", "minutes_per_tick", "d", "p_see", "seed"),
    _x("fam_layer", CACHE, _TAB, "signage_poi_by_cell"),
    _x("fam_layer", REF, "描画の側の関数(配線・〔第 1 期 1-2〕乗数つきの p_see_fn は消した)", "kind_fn"),
    _x("mem_layer", CONST, _CFG, "n", "n_rows", "minutes_per_tick", "d", "w_r", "w_i", "tau",
       "store_recall_scope"),
    _x("mem_layer", REF, "関係辺の層(rel_layer の側で数える)", "relations"),
    _x("mem_layer.store", CONST, _CFG, "n", "n_rows", "minutes_per_tick", "d", "sigma", "decay", "weight",
       "signage"),
    _x("mem_layer.store", CACHE, _TAB, "poi_cell"),
    # 第 1 期 1-6: 記憶の器 M0 の設定(今の表と同じ定数・テープに列を足すランかの印=組み立てが 1 回だけ置く)
    _x("mem_layer.memory_store", CONST, _CFG, "n", "n_rows", "ns_per_step", "minutes_per_step", "d", "w_r", "w_i",
       "tau", "tape_on"),
    # 第 2 期 2-3: 体の出来事の口(出来事の記録への参照=記録は行 E の側で数える)と腕の行の腕の名
    _x("mem_layer.memory_store", REF, "体の出来事の口(engine.events.body.BodyEventLink=記録 E の側で数える・組み立てが 1 回だけ置く)",
       "body_events"),
    _x("mem_layer.memory_store", CONST, _FIELD + "(腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
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
    _x("energy.out_of_area", CONST, _CFG, "sleep_defer", "_tpd", "meal_default"),
    # 〔小さな版上げ・meal_w17〕既定の食事時刻の分布・体ごとに引いた既定の時刻・前夜の夕食・計器の表(初期化で作る)
    _x("energy.out_of_area", CACHE, _TAB + "(既定の食事時刻の分布と体ごとの引き=母集団の seed と W17 から作り直せる)",
       "distribution", "default_min", "prev_dinner_min", "_default_slots", "_no_plan"),
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
       "constitution_report", "constitution_ok", "registry_hash", "enabled"),
    _x("runner.salient", REF, _REFR + "(知覚 SoA は台帳の perception の 5 行で数える)", "world", "agents", "dispatch",
       "press", "environment", "pstate"),
    _x("runner.salient", CONST, _CFG + "・クラスの定数", "tick_seconds", "master_seed", "day_index", "ablation",
       "d50_scale", "params", "d50_by_kind", "rate", "process_ids", "ablation_id"),
    _x("runner.salient", CACHE, "step の頭で空に戻すその tick の事象・行・気づいた体と、セルの索引",
       "events", "cell_lines", "noticed_agents", "_neighbours", "_cell_index_tick", "_order", "_start"),
    _x("runner.dispatch", REF, _REFR, "world", "log"),
    _x("runner.dispatch", CONST, _FIELD + "・" + _CFG, "tick_seconds", "process_ids", "ablation_id", "master_seed",
       "day_index"),
    _x("runner.dispatch", CACHE, "10c の counter の k の数え(同じ T の中だけ。T が変わると空に戻す=tick の境目で再開すれば"
       "空から数え直して同じ値)", "_k_tick", "_k_next"),
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
    # 第 1 期 1-5: 権利台帳(SoA の kind・W16 の org_id・POI の数から作る導出=再開では rebuild_derived で作り直す。
    # ラン中に権利を変える行動は無い=2-1 で状態の行にする)・その材料
    _x("runner.opening", CACHE, "権利台帳(1-5・SoA の kind と W16 の org_id と POI の数から作る導出・再開では作り直す)",
       "rights"),
    _x("runner.opening", CONST, _CFG + "(1-5: 権利台帳の雇用の行の材料=W16 の org_id)", "org_of_agent"),
    _x("runner.opening", CONST, _CFG + "(〔第 4 期 4-3 段 10〕差し替えの世界の権利台帳の初期の行=店の担当と住まい・読むだけ)",
       "initial_rights"),
    _x("runner.environment", REF, _REFR, "calendar", "world", "agents", "assets"),
    _x("runner.environment", CONST, _FIELD + "・" + _CFG, "master_seed", "day_index",
       "tick_seconds", "process_ids"),
    _x("runner.environment", CACHE, "日の出・日の入り・セルの点・日陰の面(資産と日付から作る)と日陰のキャッシュの印",
       "_planes", "_sunrise", "_sunset", "_cell_point", "_shade_cache_frame"),
    # 第330(10e E3・B6): 天気と暦の規則・天気を揺らすか(初期化で渡す設定)
    _x("runner.environment", CONST, _CFG, "weather_scheme", "perturbed"),
    _x("runner.environment", CACHE, "10e B6: 暦の規則の時ごとの WBGT・暑さ段・日の出と日の入り(資産・暦の日付・再生日から作る)"
       "と日ごとの天気の記録・警告(manifest の記録だけ)", "_cal_wbgt", "_cal_stage", "_sun_exact", "weather_days",
       "weather_warnings"),
    # 第330(10e B0): 開いた影のファイルの sha256(manifest の frozen_sources の記録だけ・資産と日付から作り直せる)
    _x("runner.environment", CACHE, "10e B0: 開いた影のファイルの sha256(manifest の記録だけ)", "shadow_sources"),
    _x("ledger.money", CONST, _CFG + "(他所の現金の扱いの印は初期化で 1 回だけ立てる)", "sizes", "_foreign_cash",
       "retention_days", "raw_capacity"),
    _x("ledger.money", CACHE, "書き込み窓の入れ子の深さ(checkpoint では 0)", "_depth"),
    # 第 1 期 1-9: 出来事の記録への参照(状態台帳の行 E の側で数える)・刻みの幅と K17 の容量の係数(初期化の設定)
    _x("ledger.money", REF, _REFR + "(1-3 の出来事の記録の口 MoneyEventLink・build が挿す)", "_events"),
    _x("ledger.money", CONST, _CFG + "(1-9: 刻みの幅[ns]・作ったときの K17 の容量の係数)", "_step_ns",
       "raw_rows_per_agent_day"),
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
    _x("renderer", REF, "10e B6: B3 の天候・日照・暑さの語とキャッシュの鍵を返す口(天気の規則 calendar で engine.run が"
       "差し込む・関数)", "weather_words_fn", "weather_words_key_fn"),
    _x("renderer", REF, "第 1 期 1-2: 暦の日の種類を返す口(組み立てが暦の SimCalendar.day_kind を渡す・関数・"
       "Percept.time_view の材料・描画の文は読まない)", "day_kind_fn"),
    _x("renderer", REF, "第 1 期 1-8b: 届いた発話を受け取る口と B6 に載せた発話を報告する口(組み立てが腕 on のランだけ "
       "SpeechPort.take_heard・report_shown を差し込む・関数・状態は口の側=状態台帳の行 S8・S8M)", "heard_fn",
       "heard_seen_fn"),
    _x("renderer", CONST, _CFG + "(第 1 期 1-8b: 会話の番の B6 に出力の欄の指示を足すか=腕 on・語彙 v3)",
       "speech_field"),
    _x("renderer", CONST, _CFG + "(知人の初期表・被注視数は初期化で渡す値)", "seed", "acquaintances", "watched_by",
       "budget_mode", "strict_group_budget", "signage_enabled", "signage_p_see", "intent_mode", "vocab_version",
       "role_words", "near_tiebreak", "near_order", "_near_salt64", "_b0", "_b4b", "_hunger_words", "hunger_words",
       "_hunger_min_stage"),
    _x("bridge", CONST, _CFG, "mode", "vocab_version", "landmarks", "_engine_codes", "params", "lane", "tick_seconds"),
    _x("bridge", REF, _REFR + "(未定義行動の台帳・再生・応答の口)", "renderer", "undefined", "replay", "client"),
    # 第 1 期 1-5: 役割語の権利の確かめの口(開閉の過程の権利台帳を読むだけ・状態を持たない。数えは bridge の O86)
    _x("bridge", REF, _REFR + "(1-5: 役割語の権利の確かめの口=読むだけ)", "role_rights"),
    _x("bridge.tape", CONST, _CFG, "path", "flush_rows", "run_meta"),
    _x("bridge.tape", REF, "parquet の書き手(ファイル)", "_writer"),
    _x("bridge.tape", REF, "〔第 1 期 1-6 M0〕腕の列の値を作る口(関数・組み立てが置く)", "arm_columns"),
    _x("fleet_bridge", REF, _REFR + "(艦隊・テープ・未定義行動の台帳・デバッグのファイル)", "client", "tape",
       "tape_row_factory", "undefined", "_debug_fp"),
    _x("fleet_bridge", CONST, _CFG, "vocab_version", "landmarks", "_engine_codes", "params", "source",
       "_params_hash", "debug_dir", "debug_max_rows"),
    # 第 1 期 1-3: 出来事の記録の設定(記録するか=切替口・保持窓の日数)
    _x("events", CONST, _CFG, "enabled", "retention_days"),
    # 第 1 期 1-8 J0: 候補の口の層の設定(腕の名・語彙・続ける語・語の表)・参照(口の実装・出来事の記録・世界)・資産の表
    _x("decision", CONST, _CFG, "arm", "vocab", "continue_word", "word_of_code", "kind_words", "event_words",
       "n_cells"),
    _x("decision", REF, _REFR + "(口の実装=口の後ろの今の道の bridge と方策を指す・出来事の記録・世界・〔1-7〕道具の台帳"
       "=組み立ての Fixtures.tools と同じ物)",
       "port", "events", "world", "tools"),
    _x("decision", CACHE, _TAB, "_poi_cell", "_eatery", "_station", "_home_cell"),
    # 第 1 期 1-8b: 発話の口の設定(刻みの幅のナノ秒・未読の時間の窓・届け先ごとの上限)と参照(出来事の記録・口コミの抽出の口)
    _x("speech", CONST, _CFG, "step_ns", "ttl_steps", "max_per_addressee"),
    _x("speech", CONST, _FIELD + "(実装の名=manifest の speech_port.port・腕の行の腕の名 LEDGER_ARM)", "name",
       "LEDGER_ARM"),
    _x("speech", REF, _REFR + "(出来事の記録・口コミの抽出の口・セッションが開いているかの口=組み立てが置く関数)",
       "events", "wom_fn", "session_active"),
    # 第 2 期 2-2 段 11a: 近接の層の判定の規則(凍結=腕の名・d・B5 の半径・気づく抽選の塩と時刻の鍵の材料)
    _x("proximity", CONST, _CFG + "(2-2: 判定の規則=凍結の dataclass)", "rule"),
    _x("proximity", REF, _REFR + "(2-2 検収 L1: 関係の層=気づいた印の読み口 aware_of を描画へ渡すだけ・読むだけ)", "_marks"),
    # 第 2 期 2-2(検収 M2): 腕 distance の体 × k の辺の見え方(同じ刻みの同席と知人出現で共有する控え=その刻みの中で使い切る)
    _x("rel_layer", CACHE, "2-2: 刻みの中だけの控え(腕 distance の辺の見え方=同席と知人出現で共有)", "_ev", "_ev_step"),
    # 第 2 期 2-1: 経済の段階 2 の組み立ての物への参照(状態台帳の行 EC の側で数える)・段階 2 の組を許す印(組み立てで 1 回)
    _x("decision", REF, _REFR + "(2-1: 経済の段階 2 の組み立ての物=ATM の表と部品を読むだけ)", "money_stage2"),
    _x("decision", REF, _REFR + "(6-4 C1 検収 M5: 連絡の道具の層=候補を足す口と選んだ体を渡す口・状態は連絡の側の行 CT1G)",
       "contact_offer"),
    # 第 3 期 3-3: 申込書の持ち主の設定(申込書=凍結・T0 とランの範囲の刻み・メンバーと半分)と参照(T0 で切り替える LLM の口)
    _x("experiment", CONST, _CFG + "(申込書は凍結の ExperimentForm・刻みはランの範囲・アンサンブルのメンバーと半分=入口で"
       "決まる)", "form", "t0_step", "begin_step", "end_step", "total_steps", "member", "half"),
    _x("experiment", REF, _REFR + "(T0 で切り替える LLM の口=分岐の指定の make_client が作る口=3-3 の BranchClient か 3-3b の"
       " ReplaySwitch・計器は manifest の experiment.replay)", "branch"),
    # 第 3 期 3-2: 計算のまとめの窓の設定(幅・上限・刻みの幅)・事象の種類の表(名・処理の関数・届け方と順位)・窓の中だけの
    # 作業の値(処理中の時刻・窓の終わり・処理の中で予約した窓の中の行=窓を閉じるときに空)
    _x("batching", CONST, _CFG + "(3-2: 幅と上限と刻みの幅=進行役がランの始めに決める)", "width_s", "width_ns", "cap",
       "step_s"),
    _x("batching", REF, _REFR + "(3-2: 事象の種類の表=名・処理の関数・届け方と順位の表=ランの始めに置く)", "_bw_kinds",
       "_bw_rank"),
    _x("batching", CACHE, "3-2: 窓の中だけの作業の値(処理中の時刻・窓の終わり・処理の中で予約した窓の中の行=窓を閉じると空)",
       "_bw_now", "_bw_end", "_bw_new"),
    # 第 3 期 3-5: 本人の体の層の設定(腕・体の数・刻みの幅=組み立てで決まる)
    _x("body", CONST, _CFG + "(3-5: TM5 の腕 sweep/reserve・体の数・刻みの幅・段の境目の計器を数えるか)", "arm", "n",
       "step_seconds", "gauge"),
    # 第 3 期 3-5: 環境の過程が体感温度を体の層の口で書くための参照と、腕 reserve のその日の体感温度の表(資産と日付と再生日から作る)
    _x("runner.environment", REF, _REFR + "(3-5: 本人の体の層=組み立てが attach_body で挿す)", "body"),
    _x("runner.environment", CACHE, "3-5: その日の窓 × セルの体感温度の表(腕 reserve だけ・暑さ段と日陰の面から作る・日の頭と"
       "天気の日付の差し替えで捨てる)", "_felt_table"),
    # 第 3 期 3-1: 暦 1a の影の表(W20 の週の表をランの体の並びに引き直した物=資産から作る)・設定・参照(暦と W17 の週次表)
    _x("calendar_shadow", CACHE, _TAB + "(3-1: W20 の週の表をランの体の並びに引き直した物)", "table"),
    _x("calendar_shadow", CONST, _CFG + "(3-1: 体の数・源の名 1a)", "n", "source"),
    _x("calendar_shadow", REF, _REFR + "(3-1: 暦の口と W17 の週次表=参考の差を数えるだけ・読むだけ)", "calendar", "weekly"),
    # 第 6 期 6-5: 記憶の器の腕の設定(組み立てが enable_arms で 1 回だけ置く)・子の持ち主の設定と参照
    _x("mem_layer.memory_store", CONST, _CFG + "(6-5: 上限なしの腕か・体の出来事の粒度=組み立てが 1 回だけ置く)",
       "uncapped", "grain"),
    _x("mem_layer.memory_store.m1", CONST, _CFG + "(6-5: 体の数・直近の回数 k・M1 の境目 τ・最短の符号化時間・倍率の seed)",
       "n", "k", "tau", "t_min_s", "seed"),
    _x("mem_layer.memory_store.cue", REF, _REFR + "(6-5: 埋め込みの口=モデル)", "embedder"),
    _x("mem_layer.memory_store.cue", CONST, _CFG + "(6-5: モデルの名と次元)", "model", "dim"),
    _x("mem_layer.memory_store.m1", CONST, _FIELD + "(6-5: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("mem_layer.memory_store.cue", CONST, _FIELD + "(6-5: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("rel_layer", REF, _REFR + "(6-5: 人も記憶の一つの腕の記憶の器=状態は器の側で数える)", "_ms"),
    # 〔第 6 期 6-5 検収 M2・M4・L1〕器の行の上限と腕の設定の値(組み立てが 1 回だけ置く)・店の行の表の設定・店の記憶の子の参照
    _x("mem_layer.memory_store", CONST, _CFG + "(6-5 検収 M2・L1: 種類ごとの行の上限・腕の設定の値=組み立てが 1 回だけ置く)",
       "caps", "arms_cfg"),
    _x("mem_layer.memory_store.shops", CONST, _CFG + "(6-5 検収 M4: 体の数・店の行の上限)", "n", "cap"),
    _x("mem_layer.memory_store.shops", CONST, _FIELD + "(6-5 検収 M4: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("mem_layer.store", REF, _REFR + "(6-5 検収 M4: 腕 memory の店の行の表=状態は器の子の持ち主 shops の側で数える)",
       "_tab"),
    # 第 6 期 6-2: カレンダー 1b の層の設定・参照・表と、計画実行層の口(腕 1b のランだけ組み立てが挿す)
    _x("calendar_self", REF, _REFR + "(6-2: W20 の表・暦・状態・世界・計画実行層・鉄道・判断の口・出来事の記録・道具の台帳)",
       "table", "calendar", "agents", "world", "presence", "rail", "port", "events", "tools"),
    _x("calendar_self", CONST, _CFG + "(6-2: 割り振りの種・刻みの幅・1 日の刻みの数・体の数・腕の名)", "seed",
       "step_seconds", "tpd", "n", "source"),
    _x("calendar_self", CONST, _FIELD + "(6-2: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("calendar_self", CACHE, _TAB + "(6-2: 路線ごとの便の表と便の間隔=鉄道の便から日の頭に作り直す)", "_line_tab",
       "_headway"),
    _x("calendar_self", CACHE, "6-2: この刻みに歩き始めた体(刻みの中で使い切る)", "walk_started_now"),
    _x("presence", REF, _REFR + "(6-2: カレンダー 1b の層=腕 1b のランだけ組み立てが挿す口・状態は層の側で数える)",
       "io_hook"),
    # 第 6 期 6-3: 時計の段 T2〜T4 の腕の持ち主の設定・参照・作業の値
    _x("talk_clock", CONST, _CFG + "(6-3 T2: 話す速さと揺れの乱数の seed・刻みの幅・1 窓の上限)", "rate_seed", "jitter_seed",
       "step_ns", "cap"),
    _x("talk_clock", REF, _REFR + "(6-3 T2: 関係の層=親しい相手の判定を読むだけ・事象を置く口=進行役が挿す)", "rel_layer",
       "_tc_router"),
    _x("talk_clock", CONST, _FIELD + "(6-3 T2: 持ち主の名・腕の行の腕の名 LEDGER_ARM)", "name", "LEDGER_ARM"),
    _x("step_scope", CONST, _CFG + "(6-3 T3: 体の数)", "n"),
    _x("step_scope", CACHE, "6-3 T3: 検出の間だけの作業の値(今の検出で見た体=after_detection で空に戻す)", "_ss_idx"),
    _x("step_scope", CONST, _FIELD + "(6-3 T3: 持ち主の名・腕の行の腕の名 LEDGER_ARM)", "name", "LEDGER_ARM"),
    _x("clock", CONST, _CFG + "(6-3 T4: 区域の数・舞台の外の区域・窓と刻みの幅・ランの始め・区域の作り方の名)", "n_regions",
       "outside", "width_ns", "step_ns", "start_ns", "regions_from"),
    _x("clock", CACHE, _TAB + "(6-3 T4: セル → 区域の表=世界資産のセルの重心から作る)", "region_of_cell"),
    _x("clock", REF, _REFR + "(6-3 T4: 体の状態=区域を引くセルを読むだけ・区域の事象の種類の表=名と処理の関数)", "agents",
       "_rc_kinds"),
    _x("clock", CACHE, "6-3 T4: 区域の窓の中だけの作業の値(処理中の時刻・窓の終わり・処理し終えた区域=窓を閉じると空)",
       "_rc_now", "_rc_end", "_rc_done"),
    _x("clock", CONST, _FIELD + "(6-3 T4: 持ち主の名・腕の行の腕の名 LEDGER_ARM)", "name", "LEDGER_ARM"),
    # 〔第 6 期 6-4 C1〕連絡の道具の持ち主と子の持ち主の設定・参照・作業の値
    _x("contact", CONST, _CFG + "(6-4 C1: 体の数・刻みの幅・下の腕・記憶に残ったかを数えるか=組み立てが 1 回だけ置く)", "n",
       "step_seconds", "step_ns", "unnoticed_arm", "send_arm", "remember_link"),
    _x("contact", CONST, _FIELD + "(6-4 C1: 腕の行の腕の名 LEDGER_ARM・主の判断の候補に足す語 MAIN_LOOK_WORD)", "LEDGER_ARM",
       "MAIN_LOOK_WORD"),
    _x("contact", CONST, _CFG + "(6-4 C1 検収 M5: 判断の口の腕のランか=組み立てが 1 回だけ置く)", "main_offer"),
    _x("contact", CONST, _CFG + "(〔つなぎ BR-CT1-CHARGE-AT-HOME〕体 → 住まいのセル=母集団の予定表の写し・組み立てが 1 回だけ置く)",
       "home_cell"),
    _x("contact", REF, _REFR + "(6-4 C1: 出来事の記録・体・世界・対面の会話・判断の口・文の口・宛先の読み口・進行役の待ち行列・"
       "描画=連絡の行の計数を manifest に写すだけ)", "events", "agents", "world", "conv", "port", "text", "book", "_queue",
       "renderer"),
    _x("contact", CACHE, "6-4 C1: 待ち行列の予約の番号 → 予約の鍵(ランの始めの結びで作り直す)・その刻みの体ごとの判断の通し番号"
       "(刻みの頭で空)", "_seq_key", "_codes"),
    _x("contact.dev", CONST, _CFG + "(6-4 C1: 体の数)", "n"),
    _x("contact.dev", CONST, _FIELD + "(6-4 C1: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("contact.attn", CONST, _CFG + "(6-4 C1: 体の数)", "n"),
    _x("contact.attn", CONST, _FIELD + "(6-4 C1: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("contact.mail", CONST, _FIELD + "(6-4 C1: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("contact.chats", CONST, _FIELD + "(6-4 C1: 腕の行の腕の名 LEDGER_ARM=子クラス ChatBook)", "LEDGER_ARM"),
    _x("contact.chats", CONST, _CFG + "(6-4 C1 検収 L1: 会話の器の設定=チャットの沈黙の閾値・使わない段の長さ)", "master_seed",
       "domain", "max_turns", "extra_turns_for_important", "max_participants", "accept_probability",
       "refusal_memory_ticks", "silence_ticks", "max_session_ticks", "walk_over_ticks", "topics_per_session",
       "important", "origin_names"),
    _x("contact.calls", CONST, _CFG + "(6-4 C1: 対面の会話と同じ設定=重要度上位の体の集合を含む)", "master_seed", "domain",
       "max_turns", "extra_turns_for_important", "max_participants", "accept_probability", "refusal_memory_ticks",
       "silence_ticks", "max_session_ticks", "walk_over_ticks", "topics_per_session", "important", "origin_names"),
    _x("contact.calls", CONST, _FIELD + "(6-4 C1: 腕の行の腕の名 LEDGER_ARM=子クラス CallManager)", "LEDGER_ARM"),
    _x("contact.speech", CONST, _CFG, "step_ns", "ttl_steps", "max_per_addressee"),
    _x("contact.speech", CONST, _FIELD + "(6-4 C1: 実装の名・腕の行の腕の名 LEDGER_ARM=子クラス CallSpeechPort)", "name",
       "LEDGER_ARM"),
    _x("contact.speech", REF, _REFR + "(6-4 C1: 出来事の記録・口コミの抽出の口(無し)・通話が開いているかの口)", "events",
       "wom_fn", "session_active"),
    _x("renderer", REF, "〔第 6 期 6-4 C1〕連絡の道具の口(組み立てが腕 c1 のランだけ ContactLayer.percept_hook を差し込む・関数・"
       "状態は連絡の持ち主の側=状態台帳の行 CT1*)", "contact_fn"),
    # 〔第 6 期 6-2 カレンダー 2〕会話から生まれる予定の持ち主と子の持ち主の設定・参照・作業の値
    _x("contact", REF, "〔第 6 期 6-2 カレンダー 2〕会話の番の控えの口(組み立てが腕 --calendar-2 arm のランだけ "
       "Calendar2Layer.note_turn を差し込む・関数・状態はカレンダー 2 の持ち主の側=状態台帳の行 CA2G)", "turn_sink"),
    _x("calendar2", CONST, _CFG + "(6-2 カレンダー 2: 体の数・刻みの幅・1 日の刻みの数=組み立てが 1 回だけ置く)", "n",
       "step_seconds", "step_ns", "steps_per_day", "day_ns"),
    _x("calendar2", CONST, _FIELD + "(6-2 カレンダー 2: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("calendar2", REF, _REFR + "(6-2 カレンダー 2: 出来事の記録・体・世界・暦・対面の会話・連絡の道具・世界過程=読むだけ・"
       "判断の口・頭の中の予定の思い出しの口(人ごとの忘れる速さの倍率=母集団の seed と体の番号から作り直せる))", "events",
       "agents", "world", "calendar", "conv", "contact", "runner", "port", "recall"),
    _x("calendar2", CACHE, "6-2 カレンダー 2: その刻みの体ごとの判断の通し番号(刻みの頭で空)", "_codes"),
    _x("calendar2.book", CONST, _FIELD + "(6-2 カレンダー 2: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    # 〔第 6 期 6-2 カレンダー 3〕雇い主・祝日の持ち主の設定・参照・作業の値と、連絡の道具に挿す控えの口
    _x("contact", REF, "〔第 6 期 6-2 カレンダー 3〕送った/読んだメッセージの控えの口(組み立てが腕 --calendar-3 arm のランだけ "
       "Calendar3Layer.note_sent・note_read を差し込む・関数・状態はカレンダー 3 の持ち主の側=状態台帳の行 CA3P・CA3G)",
       "sent_sink", "read_sink"),
    _x("calendar3", CONST, _CFG + "(6-2 カレンダー 3: 体の数・刻みの幅・1 日の刻みの数=組み立てが 1 回だけ置く)", "n",
       "step_seconds", "step_ns", "steps_per_day", "day_ns"),
    _x("calendar3", CONST, _FIELD + "(6-2 カレンダー 3: 腕の行の腕の名 LEDGER_ARM)", "LEDGER_ARM"),
    _x("calendar3", CONST, _CFG + "(6-2 カレンダー 3: 労働時間の行の値(規則の表の human の行を読んだ写し)・試験用の印=組み立てが"
       "1 回だけ置く)", "labor", "trial"),
    _x("calendar3", REF, _REFR + "(6-2 カレンダー 3: 出来事の記録・体・世界・暦・連絡の道具・カレンダー 2(本人の予定の器)・世界過程"
       "=読むだけ・雇い主の口の表を作る口・判断の口・暦の常識の口・店の決まりの口)",
       "events", "agents", "world", "calendar", "contact", "calendar2", "runner", "roster_fn", "port", "cc", "rules"),
    _x("calendar3", CACHE, "〔6-2 カレンダー 3 検収 H1〕雇い主の口の表とシフトを組む人 → 受け持つ単位(権利台帳の雇用の行・W20・役割の"
       "語から作る導出=組み立てでは作らず最初の刻みの頭に作る=再開では状態を戻して権利台帳を作り直した rebuild_derived の後に"
       "作り直す=通しと同じ台帳・同じ並びの単位)", "roster", "sched_units"),
    _x("calendar3", CACHE, "6-2 カレンダー 3: その刻みの体ごとの判断の通し番号(刻みの頭で空)", "_codes"),
    _x("ledger.money.stage2.tax_deposit", CONST, _CFG + "(4-2: 店の数)・" + _FIELD + "(4-2: 腕の行の腕の名 LEDGER_ARM)",
       "n", "LEDGER_ARM"),
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
    """behavior-hash に入れる外の状態の ``(行の鍵, 属性の道筋)``(軸 1 が behavior の行・``hash_skip`` を除く)。
    〔1-8b〕腕の行は入れない(``arm_items(owners, behavior=True)``)。"""
    out: list[tuple[str, str]] = []
    for r in external_rows():
        if r.behavior != BEHAVIOR or r.arm:
            continue
        skip = set(r.hash_skip)
        out.extend((r.key, it) for it in r.items if it not in skip)
    return tuple(out)
