"""act.intake.from_words — 割る段で ``engine/commit.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/commit.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Sequence
import numpy as np
from shibuya.foundation.hashing import wake_tiebreak_array
from shibuya.foundation.vocab.actions import UNDEFINED_ACTION
from shibuya.act.intake.parser import parse_two_line
from shibuya.foundation.vocab.act_codes import (
    ACTION_CODES,
    ACT_BUY,
    ACT_EAT,
    ACT_MOVE,
    ACT_NONE,
    ACT_QUEUE,
    ACT_SLEEP,
    ACT_TALK,
    ACT_WAIT,
    ENGINE_STEP,
    TARGET_HINT_APPROACH,
    TARGET_HINT_CODES,
    TARGET_HINT_HOME,
    TARGET_HINT_LOOK,
    TARGET_HINT_NONE,
    TARGET_HINT_SCHOOL,
    TARGET_HINT_WORK,
)
from shibuya.act.commit import IntentBatch, ResourceSpace, delta_perc_ns, tick_start_ns

__all__ = [
    "parse_action", "target_hint_code", "focus_codes", "pair_partners", "talk_partners", "engine_continuations",
    "intents_from_responses", "undefined_fallback_code",
]


def undefined_fallback_code(vocab_version: str = "v1") -> int:
    """未定義行動の落ち先コード(v1/v2=待機・**v3=なし**=アジェンダ §1-1)。"""
    return ACT_NONE if str(vocab_version) == "v3" else ACT_WAIT


def target_hint_code(hint: str) -> int:
    """対象ヒントの語 → 索引(未知の語は ``TARGET_HINT_NONE``)。"""
    return int(TARGET_HINT_CODES.get(str(hint or ""), TARGET_HINT_NONE))


def focus_codes(target_hint, target_person, target_poi, n_agents: int) -> np.ndarray:
    """(ヒント, 名指しの個体, 解決した POI) → ``agents.focus_target`` の符号化。

    「近づく」「見る」のときだけ焦点を立てる(``agents.state.focus_code_for_*`` と同じ符号)。
    人が優先(人と POI の両方が取れることは無いが、順序を決めておく)。

    Returns:
        ``(k,)`` int64。``-1``=焦点を立てない / ``≥0``=個体 id / ``≤-2``=``-2-poi_id``。

    逐次ループ宣言(P4): なし。
    """
    h = np.asarray(target_hint, dtype=np.int64).ravel()
    p = np.asarray(target_person, dtype=np.int64).ravel()
    q = np.asarray(target_poi, dtype=np.int64).ravel()
    want = (h == TARGET_HINT_APPROACH) | (h == TARGET_HINT_LOOK)
    ok_p = want & (p >= 0) & (p < int(n_agents))
    ok_q = want & (~ok_p) & (q >= 0)
    return np.where(ok_p, p, np.where(ok_q, -2 - q, -1)).astype(np.int64)


# ------------------------------------------------------------------ Phase A(intent 収集)
#: パーサが行動語を取れなかったときのコード(行動契約書 §7 段1「未定義行動レコード」)。
#: **正典は ``llm.contract.UNDEFINED_ACTION``**(値 −2)を import している。


def parse_action(text: str, vocab_version: str) -> int:
    """2行形から行動語を取り出してコードにする(**正典パーサへの薄い委譲**)。

    Args:
        text: 応答の本文。
        vocab_version: ランの語彙の版(〔第348〕``parse_two_line`` へそのまま渡す。前は渡さず、パーサの既定 v1 で読んでいた)。

    Returns:
        ``ACTION_CODES`` の値(12 語)。取れない/12 語の外(役割語を含む)なら
        ``UNDEFINED_ACTION``。

    Note:
        C2 ではここに最小写像を置いていたが、C3 で正典のパーサ
        (``llm.parser.parse_two_line``・ラベル基準の寛容行指向・知覚契約書 §2.5)が入ったので
        **委譲に置き換えた**(パーサを2つ持たない)。§2.2 の役割語は ``_APPLY`` に対応分岐が
        無い(効果先は C4)ため、ここでは 12 語だけをコード化し、他は未定義扱い=``resolve`` が
        「待機」に落とす(§2 共通必須事項③の安全弁)。
    """
    if not text:
        return UNDEFINED_ACTION
    word = parse_two_line(text, vocab_version).action
    if word is None:
        return UNDEFINED_ACTION
    return int(ACTION_CODES.get(word, UNDEFINED_ACTION))


def talk_partners(
    agent_id: np.ndarray,
    cell: np.ndarray,
    named: np.ndarray | None,
    partner_cell: np.ndarray | None,
    n_agents: int,
    order_key: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """会話の相手を決める(**LLM の「対象」欄を第一**・C6 の設計準拠化 09-09)。

    正典
    - 行動契約書 §1-2: 2 行形の「対象: <セルID|物カテゴリ|**個体ID**>」= 対象スロット。
      会話の相手は**モデルが名指しする**(C3 の「エンジンが文脈から導く」は expedient だった)。
    - 知覚契約書 §3.7 聴覚: 雑談の可聴距離 1-2.5 m → **同一セル**で代理する(C3 と同じ)。

    規則(適用順)
      1. ``named`` が個体 ID(``P-nnn`` → ``Target.person_id``)で、範囲内・自分でない・
         **同一セル**なら、その個体を相手にする(``source=0``)。
      2. さもなければ ``pair_partners``(同じ適用バッチの同セル最小 id)へ**フォールバック**
         (``source=1``・**expedient のまま**・計数する)。
      3. フォールバックでも相手が居なければ ``-1``(``source=2``=不成立)。

    Args:
        agent_id: 呼んだ個体。
        cell: その個体のセル。
        named: LLM が名指しした個体 id(``-1``=名指しなし)。``None`` なら全件 ``-1``。
        partner_cell: 全個体のセル配列(``agents.registry.cell``)。``None`` なら名指しは使えない。
        n_agents: 個体数(範囲検査)。
        order_key: フォールバックのセル内の並び順(``pair_partners`` へ素通し)。
            **ID 順バイアス(T5)を避けるため blake3 撹拌鍵を渡す**。

    Returns:
        ``(partner, source)``。``source`` は 0=名指し / 1=フォールバック / 2=相手なし。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    c = np.asarray(cell, dtype=np.int64)
    fallback = pair_partners(a, c, order_key)
    if named is None or partner_cell is None or a.size == 0:
        source = np.where(fallback >= 0, 1, 2).astype(np.int8)
        return fallback, source
    nm = np.asarray(named, dtype=np.int64)
    pc = np.asarray(partner_cell, dtype=np.int64)
    ok = (nm >= 0) & (nm < int(n_agents)) & (nm != a) & (c >= 0)
    if ok.any():
        ok = ok & (pc[np.clip(nm, 0, max(0, int(n_agents) - 1))] == c)
    partner = np.where(ok, nm, fallback)
    source = np.where(ok, 0, np.where(fallback >= 0, 1, 2)).astype(np.int8)
    return partner, source


def _reach_rows(agents, a: np.ndarray, named: np.ndarray, rows: np.ndarray, rule) -> np.ndarray:
    """〔第 2 期 2-2〕``rows`` の行の名指しの相手に届くか(ほかの行は偽)。逐次ループ宣言: なし。"""
    out = np.zeros(a.shape, dtype=bool)
    sel = np.flatnonzero(rows)
    if sel.size:
        out[sel] = rule.reach(agents, a[sel], np.asarray(named, dtype=np.int64)[sel])
    return out


def _talk_partners_reach(agents, a: np.ndarray, is_talk: np.ndarray, named: np.ndarray | None,
                         order_key: np.ndarray | None, rule) -> tuple[np.ndarray, np.ndarray]:
    """〔第 2 期 2-2 段 11a〕``talk_partners`` の腕 ``--proximity distance`` の版(会話の行だけ決める)。

    1. 名指しの個体が範囲内・自分でない・自分が舞台の中で、**届く**(``rule.reach``)ならその個体(``source=0``)。
    2. さもなければ、届く同じ束の体のうち並びの鍵が最小の体(``engine.proximity.batch_partners``・``source=1``)。
    3. どちらも居なければ −1(``source=2``)。会話でない行は −1・``source=2``(使わない)。
    逐次ループ宣言: なし。
    """
    from shibuya.world.model.proximity import batch_partners

    n = a.size
    partner = np.full(n, -1, dtype=np.int64)
    rows = np.flatnonzero(is_talk)
    if rows.size == 0:
        return partner, np.full(n, 2, dtype=np.int8)
    fb = np.full(n, -1, dtype=np.int64)
    fb[rows] = batch_partners(agents, rule, a, rows, order_key)
    cell = np.asarray(agents.registry.cell, dtype=np.int64)[a]
    nm = np.full(n, -1, dtype=np.int64) if named is None else np.asarray(named, dtype=np.int64)
    valid = is_talk & (nm >= 0) & (nm < int(agents.n)) & (nm != a) & (cell >= 0)
    ok = _reach_rows(agents, a, nm, valid, rule)
    partner = np.where(ok, nm, fb)
    source = np.where(ok, 0, np.where(fb >= 0, 1, 2)).astype(np.int8)
    return partner, source


def pair_partners(
    agent_id: np.ndarray, cell: np.ndarray, order_key: np.ndarray | None = None
) -> np.ndarray:
    """同一セルに居る**起床中の**個体から会話相手を決める(決定論・ループなし)。

    規則(expedient): セル内で ``order_key`` 昇順の先頭を相手にする。先頭本人の相手は 2 番目。
    同じ相手を複数人が指名する=**会話招待の資源競合**が起きる(設計書 §2.2「会話招待=
    1件だけ通し」を Phase B で実際に効かせるための形)。

    Args:
        order_key: セル内の並び順(``None`` なら ``agent_id`` 昇順)。
            **``None`` は ID 順バイアスを作る**(運用設計書 §2.5・T5 |r|≤0.05)。C6 で
            被招待も起床するようになったため、呼び出し側は ``wake_tiebreak_array``
            (blake3 撹拌)を渡すこと。``None`` は単体テストと後方互換のためだけに残す。

    Returns:
        ``agent_id`` と同じ並びの相手 id(単独セルなら -1)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    c = np.asarray(cell, dtype=np.int64)
    out = np.full(a.shape, -1, dtype=np.int64)
    if a.size == 0:
        return out
    key = a if order_key is None else np.asarray(order_key).astype(np.uint64, copy=False)
    order = np.lexsort((a, key, c)) if order_key is not None else np.lexsort((a, c))
    sa, sc = a[order], c[order]
    starts = np.flatnonzero(np.concatenate(([True], sc[1:] != sc[:-1])))
    counts = np.diff(np.append(starts, sc.size))
    first = np.repeat(sa[starts], counts)
    second = np.repeat(np.where(counts > 1, sa[np.minimum(starts + 1, sc.size - 1)], -1), counts)
    partner = np.where(sa == first, second, first)
    partner = np.where(c[order] < 0, -1, partner)
    out[order] = partner
    return out


def engine_continuations(agents, space: ResourceSpace, tick: int) -> IntentBatch:
    """Phase A のエンジン内部分: 移動中の個体の「経路の1歩」。

    δ_perc は 0(**自発**=予期クラス C0)。資源競合なし。
    """
    from shibuya.foundation.vocab.agent_codes import Activity  # 局所 import(層は engine>agents で合法)

    moving = np.flatnonzero(
        (agents.registry.activity == int(Activity.MOVING)) & (agents.registry.target_node >= 0)
    ).astype(np.int64)
    n = moving.size
    return IntentBatch(
        agent_id=moving,
        action_code=np.full(n, ENGINE_STEP, dtype=np.int8),
        target_id=agents.registry.target_node[moving].astype(np.int32),
        resource_id=np.full(n, -1, dtype=np.int32),
        t_notice_ns=np.full(n, tick_start_ns(tick), dtype=np.int64),
    )


def _poi_in_cell(world, cell: np.ndarray, keep: np.ndarray | None) -> np.ndarray:
    """各体のセルにある POI の**最小 id**(無ければ -1)。``keep`` で候補を絞れる。

    C2 から購入の対象決定に使っていた走査をそのまま関数にしたもの(**値は 1 つも動かない**:
    ``keep=None`` のとき従来と同じ ``lexsort`` + ``searchsorted``)。語彙 v2 の「食事」は
    ``keep=world.eatery_mask`` で飲食店だけに絞って同じ走査を使う。

    逐次ループ宣言(P4): なし(NumPy の整列と二分探索だけ)。
    """
    c = np.asarray(cell, dtype=np.int64)
    poi_cell = world.pois.cell.astype(np.int64)
    idx = np.arange(poi_cell.size, dtype=np.int64)
    if keep is not None:
        k = np.asarray(keep, dtype=bool)
        poi_cell = np.where(k, poi_cell, -1)  # 候補外は「セル -1」へ退避(下で -1 は弾く)
    order = np.lexsort((idx, poi_cell))
    sorted_cells = poi_cell[order]
    pos = np.searchsorted(sorted_cells, c, side="left")
    pos_c = np.clip(pos, 0, max(0, sorted_cells.size - 1))
    found = (sorted_cells.size > 0) & (sorted_cells[pos_c] == c)
    # **場外(``cell == -1``)は必ず「見つからない」**。``keep`` で退避した候補外の POI も
    # セル -1 に寄せてあるので、これを弾かないと域外の体に候補外の POI が当たる
    # (``keep=None`` の購入では POI のセルに -1 が無いので、この条件は 1 件も変えない)。
    return np.where(found & (c >= 0), order[pos_c], -1)


def intents_from_responses(
    agents,
    world,
    space: ResourceSpace,
    tick: int,
    agent_id: np.ndarray,
    condition: np.ndarray,
    action_code: np.ndarray,
    *,
    home_cell: np.ndarray | None = None,
    work_cell: np.ndarray | None = None,
    school_cell: np.ndarray | None = None,
    target_person: np.ndarray | None = None,
    target_hint: np.ndarray | None = None,
    target_poi: np.ndarray | None = None,
    stats: dict[str, int] | None = None,
    run_salt: bytes = b"",
    vocab_version: str = "v1",
    move_dest: np.ndarray | None = None,
    targets: Sequence[object] | None = None,
    poi_resolver: object | None = None,
    intent_hold: object | None = None,
    talk_chooser: object | None = None,
    proximity: object | None = None,
) -> IntentBatch:
    """Phase A の LLM 由来分: 行動コード → 対象と資源を**エンジンが**決めて intent にする。

    行動契約書 §1 の「対象」欄は C3 のパーサが読む。C2 は行動語だけを LLM から受け取り、
    対象は文脈からエンジンが導く(**expedient**・そのぶん「対象を間違える」失敗は起きない)。

    Args:
        agents / world: 現在状態(**読むだけ**)。
        space: 資源名前空間。
        tick: 現在 tick。
        agent_id: 呼んだ個体(昇順でなくてよい)。
        condition: 起床条件(δ_perc の予期クラスに使う)。
        action_code: ``parse_action`` の結果(``UNDEFINED_ACTION`` を含む)。
        home_cell / work_cell: 移動・就寝の既定の行き先(mock スケジュール由来)。
        school_cell: **W16 の学校セル**(``-1``=学校なし)。対象ヒント ``school`` の解決先。
            ``None``(既定)なら ``school`` のヒントは**効かない**(=現行の行き先のまま)。
        target_person: **LLM が「対象」欄に書いた個体 id**(``-1``=名指しなし・C6 09-09)。
            会話の相手はここを第一に見る(``talk_partners``)。``None`` なら従来どおり
            同バッチ最小 id へのフォールバックだけになる。
        target_hint: **段0 辞書 v4 の対象ヒント**(``TARGET_HINT_*`` の索引・C9b G5)。
            ``None``(既定)では 1 バイトも挙動が変わらない。移動の行き先だけに効く:
            ``home``/``work``/``school``= 拠点セル / ``approach``= 対象(人/目印)のセル /
            ``category``・``look``= 行き先には効かない(``category`` は「対象」欄の物カテゴリを
            そのまま残すための印・``look`` は待機側)。
        target_poi: 「対象」欄が**目印 POI に解決できた**ときの POI 索引(``-1``=なし・
            C9b G6 a′)。``approach`` の行き先に使う。
        stats: 与えると会話の相手の由来を数える(``talk_named``/``talk_fallback``/
            ``talk_absent``)。診断行 ``conv_*`` の素材。
        run_salt: 会話フォールバックのセル内順序を撹拌する塩(運用設計書 §2.5)。
            **空だと ID 順**になり T5(順序バイアス |r|≤0.05)を割る。
        vocab_version: 語彙版。``"v3"`` で未定義行動の落ち先が **なし**(25)になり、
            **並ぶ**(22)の対象=現在セルの POI(購入と同じ走査)が立つ。既定 ``"v1"`` は不変。
        move_dest: **移動の行き先の上書き**(``(n,)``・``-1``=上書きなし・``≥0``=セル・
            ``WANDER_BAD_TARGET``=対象不正)。「対象: あたり」(二層の段 2)の行き先を
            ``engine.activity`` が決めて渡す口。``None``(既定)では 1 行も通らない。
        targets: 体ごとの「対象」欄(``llm.contract.Target`` か ``None``)。``poi_resolver`` と
            一緒に使う(段 2a)。
        poi_resolver: **段 2a の候補の絞り込み+選び手**(``engine.poi_target.TargetResolver``)。
            渡すと購入/食事/並ぶの対象を「現在セルの営業中・意図に合う POI の候補 → 選び手の
            分布」で決める。``None`` なら従来の「現在セルの最小 id」(``_poi_in_cell``)。
            **段 2b**: 渡すと移動の行き先も対象欄から決める(``TargetResolver.resolve_move``=
            セル ID → 名指し → カテゴリ語の近傍探索 → なし=従来の既定)。対象ヒント home/work/
            school/approach と「あたり」の行は従来どおり(そちらが優先)。
        intent_hold: **段 2c の意図の層**(``engine.intent.IntentLayer``)。``poi_resolver`` と
            一緒に渡すと、購入/食事/並ぶ/会話/就寝の対象が**現在セルに無く解決できる**行
            (名指しの店が見えている・カテゴリの店が近傍にある・会話の相手が別セル・寝床=自宅が
            別セル)を**目的地つき移動**に変え、元の行為を ``intent_hold.propose`` へ渡す
            (意図を立てるのは移動が始まった後=``IntentLayer.after_apply``)。``None``(既定)は
            段 2b と 1 バイトも変わらない。
        talk_chooser: **C10 8b の会話の相手の選び手**(``engine.relations.RelationLayer``・``--relations on``
            のランだけ)。名指しの無い会話の行(同セルの名指しでない・別セルの意図にしない行)の相手を関係辺の
            重み+seed つき乱択で引き(``choose_talk_partners``)、全部の会話の行に起点(招待/偶然/知人出現)を
            付ける。``None``(既定)は 1 バイトも変わらない。
        proximity: 〔第 2 期 2-2 段 11a〕腕 ``--proximity distance`` の判定の規則(``engine.proximity.ProximityRule``)。
            渡すと会話の相手を「同じセル」でなく「届く」(同じ層・距離 ≤ d、または同じ B5 の単位)で決める: 名指しは
            届くときだけ・フォールバックは届く束の体のうち並びの鍵が最小の体(``proximity.batch_partners``)・名指しの
            相手へ歩く意図にするのは「届かず別のセルに居る」相手。``None``(既定)は 1 バイトも変わらない。

    Returns:
        ``IntentBatch``(1 個体 1 件)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    n = a.size
    code = np.asarray(action_code, dtype=np.int64).copy()
    # 未定義行動は「待機」へ落とす(行動契約書 §7 段1・resolve が結果コードを付ける)
    # **語彙 v3 は「なし」へ**(アジェンダ §1-1・v1/v2 は ACT_WAIT のまま=バイト不変)
    code_out = np.where(
        code == UNDEFINED_ACTION, undefined_fallback_code(vocab_version), code
    ).astype(np.int8)
    target = np.full(n, -1, dtype=np.int64)
    resource = np.full(n, -1, dtype=np.int64)
    if n == 0:
        return IntentBatch.empty()

    cell = agents.registry.cell[a].astype(np.int64)

    # 移動: 行き先=職場/自宅のうち今いない方(mock)。無ければ現在セル。
    is_move = code_out == ACT_MOVE
    if np.any(is_move):
        if home_cell is not None and work_cell is not None:
            hc = np.asarray(home_cell, dtype=np.int64)[a]
            wc = np.asarray(work_cell, dtype=np.int64)[a]
            dest = np.where(cell == wc, hc, wc)
        else:
            hc = wc = None
            dest = cell
        # ---- 段 2b(D-112 ②): 対象欄が行き先を言っていれば従来の既定より優先する ----
        # 対象ヒント home/work/school/approach と「あたり」(move_dest)の行は下の既存の経路が決める。
        if poi_resolver is not None:
            skip = np.zeros(n, dtype=bool)
            if target_hint is not None:
                skip |= np.isin(
                    np.asarray(target_hint, dtype=np.int64),
                    (TARGET_HINT_HOME, TARGET_HINT_WORK, TARGET_HINT_SCHOOL, TARGET_HINT_APPROACH),
                )
            if move_dest is not None:
                skip |= np.asarray(move_dest, dtype=np.int64) != -1
            m_rows = is_move & ~skip
            if np.any(m_rows):
                m_dest = poi_resolver.resolve_move(  # type: ignore[attr-defined]
                    agents, int(tick), a, code_out, targets, m_rows
                )
                dest = np.where(m_rows & (m_dest != -1), m_dest, dest)
        # ---- C9b G5: 対象ヒントが在れば**LLM が言った行き先**を優先する ----
        # (「帰宅」と書いた体を職場へ歩かせない=段0 辞書が捨てていた対象を拾う。
        #  ``target_hint`` が ``None`` の既定では 1 行も通らない=バイト不変)
        if target_hint is not None:
            hint = np.asarray(target_hint, dtype=np.int64)
            if hc is not None:
                dest = np.where((hint == TARGET_HINT_HOME) & (hc >= 0), hc, dest)
            if wc is not None:
                dest = np.where((hint == TARGET_HINT_WORK) & (wc >= 0), wc, dest)
            if school_cell is not None:
                sc = np.asarray(school_cell, dtype=np.int64)[a]
                dest = np.where((hint == TARGET_HINT_SCHOOL) & (sc >= 0), sc, dest)
            # 「近づく」= 対象(人/目印)の**いまのセル**へ。セルが取れない対象は
            # ``-1`` のまま渡り ``resolve._apply_move`` が ``UNREACHABLE`` を返す。
            app = hint == TARGET_HINT_APPROACH
            if np.any(app):
                dest_app = np.full(n, -1, dtype=np.int64)
                if target_person is not None:
                    tp = np.asarray(target_person, dtype=np.int64)
                    ok_p = app & (tp >= 0) & (tp < int(agents.n))
                    if np.any(ok_p):
                        pc = np.asarray(agents.registry.cell, dtype=np.int64)[
                            np.clip(tp, 0, max(0, int(agents.n) - 1))
                        ]
                        dest_app = np.where(ok_p, pc, dest_app)
                if target_poi is not None:
                    tq = np.asarray(target_poi, dtype=np.int64)
                    ok_q = app & (dest_app < 0) & (tq >= 0) & (tq < int(world.n_poi))
                    if np.any(ok_q):
                        qc = np.asarray(world.assets.poi_cell, dtype=np.int64)[
                            np.clip(tq, 0, max(0, int(world.n_poi) - 1))
                        ]
                        dest_app = np.where(ok_q, qc, dest_app)
                dest = np.where(app, dest_app, dest)
        # ---- 二層の段 2: 「対象: あたり」の行き先(``engine.activity`` が決めた値)を優先 ----
        if move_dest is not None:
            md = np.asarray(move_dest, dtype=np.int64)
            dest = np.where(md != -1, md, dest)
        target = np.where(is_move, dest, target)

    # ---- 段 2c: 意図の層(``poi_resolver`` と一緒のときだけ)。行 → (対象, 種類) ----
    hold_on = intent_hold is not None and poi_resolver is not None
    shop_intents: dict[int, tuple[int, int]] = {}

    # ---- 段 2a(D-114 (a)): 購入/食事/並ぶの対象=候補(営業中・意図に合う)→ 選び手 ----
    is_buy = code_out == ACT_BUY
    is_queue = code_out == ACT_QUEUE
    is_eat = code_out == ACT_EAT
    if poi_resolver is not None:
        buy_like = is_buy | (is_queue & (str(vocab_version) == "v3"))
        if np.any(buy_like | is_eat):
            poi_t = poi_resolver.resolve(  # type: ignore[attr-defined]
                agents, int(tick), a, code_out, targets, is_eat=is_eat, is_buy_like=buy_like,
                **({"intent_out": shop_intents} if hold_on else {}),
            )
            sel = buy_like | is_eat
            target = np.where(sel, poi_t, target)
            resource = np.where(
                sel & (poi_t >= 0), space.poi(np.maximum(poi_t, 0)), resource
            )
        is_buy = is_queue = is_eat = np.zeros(n, dtype=bool)  # 従来の経路は通さない

    # 購入: 現在セルの POI(最小 id)。無ければ -1 → 失敗(在庫切れ扱いでなく対象不正)。
    if np.any(is_buy):
        poi = _poi_in_cell(world, cell, None)
        target = np.where(is_buy, poi, target)
        resource = np.where(is_buy & (poi >= 0), space.poi(np.maximum(poi, 0)), resource)

    # 並ぶ(語彙 v3・第275 親の決め #2): 対象=現在セルの POI(購入と同じ走査)。飲食店なら
    # ``resolve`` が食事へ、それ以外は購入へ委譲する(資源も購入/食事と同じ ``space.poi``)。
    if str(vocab_version) == "v3" and np.any(is_queue):
        q_poi = _poi_in_cell(world, cell, None)
        target = np.where(is_queue, q_poi, target)
        resource = np.where(
            is_queue & (q_poi >= 0), space.poi(np.maximum(q_poi, 0)), resource
        )

    # 食事(語彙 v2): 現在セルの**飲食店** POI(最小 id)。無ければ -1 → ``NOT_IN_EATERY``。
    # 購入と同じ「セル内の POI を探す」走査だが、候補を ``world.eatery_mask`` で絞る。
    # 資源も購入と同じ ``space.poi``(店の 1 tick 受け入れ数)= 同じ店の席を奪い合う。
    if np.any(is_eat):
        eat_poi = _poi_in_cell(world, cell, world.eatery_mask)
        target = np.where(is_eat, eat_poi, target)
        resource = np.where(
            is_eat & (eat_poi >= 0), space.poi(np.maximum(eat_poi, 0)), resource
        )

    # 会話: **LLM が名指しした個体**を第一・同セルでなければ同バッチ最小 id(資源=相手)。
    talk_intents: dict[int, tuple[int, int]] = {}
    is_talk = code_out == ACT_TALK
    if np.any(is_talk):
        # セル内の並びは blake3 撹拌(ID 順バイアス=v1 C-8 を断つ・T5 の監査点)。
        order_key = (
            wake_tiebreak_array(run_salt, int(tick), np.zeros(n, dtype=np.int64), a)
            if run_salt
            else None
        )
        prox = proximity if (proximity is not None and getattr(proximity, "is_distance", False)) else None
        if prox is None:
            partner, source = talk_partners(
                a, cell, target_person, agents.registry.cell, int(agents.n), order_key
            )
        else:  # 第 2 期 2-2: 届く相手(名指しは届くときだけ・フォールバックは届く束の体)
            partner, source = _talk_partners_reach(agents, a, is_talk, target_person, order_key, prox)
        if talk_chooser is not None:
            # C10 8b: 別セルの名指し(下の意図にする行)は選ばない=同じ判定を先に作る
            far0 = np.zeros(n, dtype=bool)
            if hold_on and target_person is not None:
                nm0 = np.asarray(target_person, dtype=np.int64)
                pc0 = np.asarray(agents.registry.cell, dtype=np.int64)
                ok0 = is_talk & (nm0 >= 0) & (nm0 < int(agents.n)) & (nm0 != a) & (cell >= 0)
                pcell0 = np.where(ok0, pc0[np.clip(nm0, 0, max(0, int(agents.n) - 1))], -1)
                far0 = ok0 & (pcell0 >= 0) & (pcell0 != cell)
                if prox is not None:  # 第 2 期 2-2: 届く名指しは別セルでも歩かない
                    far0 &= ~_reach_rows(agents, a, nm0, far0, prox)
            rows_t = np.flatnonzero(is_talk & ~far0)
            if rows_t.size:
                got, _origin = talk_chooser.choose_talk_partners(  # type: ignore[attr-defined]
                    agents, int(tick), a[rows_t], partner[rows_t], source[rows_t] == 0,
                    np.asarray(condition, dtype=np.int64)[rows_t],
                    **({} if prox is None else {"proximity": prox}),
                )
                partner = partner.copy()
                partner[rows_t] = got
                source = source.copy()
                source[rows_t] = np.where(source[rows_t] == 0, 0, np.where(got >= 0, 1, 2)).astype(np.int8)
        target = np.where(is_talk, partner, target)
        resource = np.where(
            is_talk & (partner >= 0), space.partner(np.maximum(partner, 0)), resource
        )
        talk_far = np.zeros(n, dtype=bool)
        if hold_on and target_person is not None:
            # 段 2c: 名指しの相手が**別セル**に居る → その人のセルへ歩いて(着いたら)話しかける
            nm = np.asarray(target_person, dtype=np.int64)
            pc_all = np.asarray(agents.registry.cell, dtype=np.int64)
            ok = is_talk & (nm >= 0) & (nm < int(agents.n)) & (nm != a) & (cell >= 0)
            pcell = np.where(ok, pc_all[np.clip(nm, 0, max(0, int(agents.n) - 1))], -1)
            talk_far = ok & (pcell >= 0) & (pcell != cell)
            if prox is not None:  # 第 2 期 2-2: 届く名指しは別セルでも歩かない
                talk_far &= ~_reach_rows(agents, a, nm, talk_far, prox)
            if np.any(talk_far):
                for k in np.flatnonzero(talk_far).tolist():
                    talk_intents[k] = (int(nm[k]), int(pcell[k]))
        if stats is not None:
            # 意図にした行(相手が別セル)は由来の計数から外す(manifest ``intent`` の person で数える)
            src = source[is_talk & ~talk_far]
            stats["talk_named"] = stats.get("talk_named", 0) + int(np.count_nonzero(src == 0))
            stats["talk_fallback"] = stats.get("talk_fallback", 0) + int(
                np.count_nonzero(src == 1)
            )
            stats["talk_absent"] = stats.get("talk_absent", 0) + int(np.count_nonzero(src == 2))

    # 就寝: 寝床=自宅セル(資源=そのセルの就寝スロット)。
    is_sleep = code_out == ACT_SLEEP
    bed_far = np.zeros(n, dtype=bool)
    if np.any(is_sleep):
        bed = np.asarray(home_cell, dtype=np.int64)[a] if home_cell is not None else cell
        target = np.where(is_sleep, bed, target)
        resource = np.where(is_sleep & (bed >= 0), space.sleep(np.maximum(bed, 0)), resource)
        if hold_on and home_cell is not None:
            # 段 2c: 寝床(自宅セル)が**別セル** → 自宅へ歩いて(着いたら)寝る
            bed_far = is_sleep & (bed >= 0) & (cell >= 0) & (bed != cell)
            # 親決定 Q22: 計画就寝の意図(``sleep_pending``)が立っている体には立てない(計画が優先)
            planned = bed_far & (np.asarray(agents.registry.sleep_pending, dtype=np.int64)[a] != 0)
            if np.any(planned):
                bed_far = bed_far & ~planned
                intent_hold.note(  # type: ignore[attr-defined]
                    "bed_skipped_sleep_pending", int(np.count_nonzero(planned))
                )

    # ---- 段 2c: セル外の対象を「意図+目的地つき移動」に変える ----
    if hold_on and (shop_intents or talk_intents or np.any(bed_far)):
        from shibuya.foundation.vocab.agent_codes import IntentKind  # 局所 import(層は engine>agents で合法)

        poi_cell = np.asarray(world.pois.cell, dtype=np.int64)
        rows: list[int] = []
        i_tgt: list[int] = []
        i_kind: list[int] = []
        i_dest: list[int] = []
        for k, (poi, kind) in sorted(shop_intents.items()):
            rows.append(k)
            i_tgt.append(int(poi))
            i_kind.append(int(kind))
            i_dest.append(int(poi_cell[int(poi)]))
        for k, (pid, pcell) in sorted(talk_intents.items()):
            rows.append(k)
            i_tgt.append(int(pid))
            i_kind.append(int(IntentKind.PERSON))
            i_dest.append(int(pcell))
        if np.any(bed_far):
            bed_arr = np.asarray(home_cell, dtype=np.int64)[a]
            for k in np.flatnonzero(bed_far).tolist():
                rows.append(k)
                i_tgt.append(int(bed_arr[k]))
                i_kind.append(int(IntentKind.BED))
                i_dest.append(int(bed_arr[k]))
        r_idx = np.asarray(rows, dtype=np.int64)
        dest_arr = np.asarray(i_dest, dtype=np.int64)
        intent_hold.propose(  # type: ignore[attr-defined]
            a[r_idx], code_out[r_idx].astype(np.int64), np.asarray(i_tgt, dtype=np.int64),
            np.asarray(i_kind, dtype=np.int64), dest_arr,
        )
        code_out = code_out.copy()
        code_out[r_idx] = np.int8(ACT_MOVE)
        target[r_idx] = dest_arr
        resource[r_idx] = -1

    t0 = tick_start_ns(tick)
    return IntentBatch(
        agent_id=a,
        action_code=code_out,
        target_id=target.astype(np.int32),
        resource_id=resource.astype(np.int32),
        t_notice_ns=(t0 + delta_perc_ns(condition)).astype(np.int64),
    )
