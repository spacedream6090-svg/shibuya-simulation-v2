"""act.ops.shop — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Any, Final
import numpy as np
from shibuya.foundation.vocab.agent_codes import INTENT_NONE, Activity, ResultCode
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.foundation.vocab.act_codes import S2_MONEY_ACT, S2_PAY_ACCOUNT, S2_PAY_CASH, S2_WITHDRAW
from shibuya.act.commit import (
    IntentBatch,
)
from shibuya.foundation.vocab.act_codes import EXIT_WALK_FLAG
from shibuya.act.gate import ResolveOutcome, _fail, _ok
from shibuya.act.ops.body_writes import _energy_meal, _energy_snack
from shibuya.foundation.write_guard import _require_thawed
from shibuya.act.ops.focus import _set_focus

__all__ = [
    "BUY_HUNGER_RELIEF", "EAT_HUNGER_RELIEF", "release_indoor", "balk_queue",
]


BUY_HUNGER_RELIEF: Final[int] = 4

# ---- 語彙 v2「食事」(D-71 §3 E・2026-09-17 ユーザー決定) ----
#: 食事 1 回の空腹の回復量。**``BUY_HUNGER_RELIEF`` の再利用**(新しい数を作らない)。
#: 語彙 v1 では「食べる/飲む」を 購入 に写して同じ量だけ空腹が下がっていたので、
#: この値にすると **v1→v2 で身体の駆動が変わらず、変わるのは意味と会計だけ**になる。
#: 量そのものの較正はユーザー/親判断(D-71 §3 G の指紋として宣言する)。
EAT_HUNGER_RELIEF: Final[int] = BUY_HUNGER_RELIEF

#: 物の台帳の払い出しスロットを回す最大回数(``_apply_buy`` の注記・expedient)。
_SELL_SLOT_RETRIES: Final[int] = 8


def _stage2_money(out: ResolveOutcome) -> Any:
    """〔第 2 期 2-1〕経済の段階 2 の中身(``economy.stage2.MoneyStage2``・腕の無いランは ``None``)。"""
    led = out.ledger
    money = getattr(led, "money", None) if led is not None else None
    return getattr(money, "stage2", None) if money is not None else None


def _payable(agents: AgentState, out: ResolveOutcome, aid: np.ndarray, price: np.ndarray) -> np.ndarray:
    """払えるか。腕の無いラン=所持金 ≧ 価格(今のまま)/〔2-1〕支払い(payment)の部品=現金か口座のどちらかで足りる。"""
    s2 = _stage2_money(out)
    if s2 is not None and s2.part("payment"):
        return np.asarray(out.ledger.money.can_pay_many(aid, price), dtype=bool)
    return agents.registry.money[aid].astype(np.int64) >= price


def _stage2_note_calls(batch: IntentBatch, out: ResolveOutcome) -> None:
    """〔第 2 期 2-1・検収 A1〕意図の行のうち LLM の答えの行為が金に触れる行(購入・食事・並ぶ=``S2_MONEY_ACT``・遠い店へ
    歩く移動に変えた行も含む)の呼の id と支払いの方法の答え(``S2_PAY_*``)を台帳に控える(``Ledger.note_calls_many``)。
    購入・食事の金の行の原因 ``LlmCall(call_id)``(着いて実行する意図・列から席へ入った体も同じ呼)。腕の無いランは通らない。"""
    s2 = _stage2_money(out)
    if s2 is None or batch.call_id is None or batch.s2_flags is None or len(batch) == 0:
        return
    f = batch.s2_flags.astype(np.int64)
    has = np.fromiter((c is not None for c in batch.call_id), dtype=bool, count=len(batch))
    m = ((f & S2_MONEY_ACT) != 0) & has
    if not m.any():
        return
    pay = np.where((f & S2_PAY_CASH) != 0, 0, np.where((f & S2_PAY_ACCOUNT) != 0, 1, -1))
    out.ledger.money.note_calls_many(batch.agent_id[m].astype(np.int64), batch.call_id[m], pay[m])


def _stage2_withdraw(agents: AgentState, aid: np.ndarray, step: int, out: ResolveOutcome, *,
                     call_ids: np.ndarray | None = None, flags: np.ndarray | None = None) -> None:
    """〔第 2 期 2-1〕引き出し(withdraw の部品): この刻みに判断した体のうち、営業中の ATM・銀行の支店のセルに居る体を台帳に
    渡す。下ろすか・いくらかは本人の判断(``MoneyStage2.withdraw``=mock と古典の規則・expedient)。世帯の現金は基本操作
    ``economy.ops.transfer`` が書く(帳簿の口 ``withdraw_many``=口の名の表の外=``apply`` の閉包は ``agents.money`` を
    もう持つ=試験 ``tests/economy/stage2/test_stage2_writers.py``)。"""
    s2 = _stage2_money(out)
    if s2 is None or not s2.part("withdraw") or aid.size == 0:
        return
    from shibuya.economy import stage2_bind as _ES2

    open_cells = _ES2.atm_open_cells(s2.plan, int(step))
    if open_cells.size == 0:
        return
    cell = agents.registry.cell[aid].astype(np.int64)
    here = (cell >= 0) & (cell < open_cells.size)
    here[here] = open_cells[cell[here]]
    who = aid[here]
    if who.size:
        # 〔検収 A1〕口が「お金を下ろす」を選んだ行(``S2_WITHDRAW``)は規則を通さない・呼のある行の原因は LlmCall(call_id)
        wanted = None if flags is None else (np.asarray(flags, dtype=np.int64)[here] & S2_WITHDRAW) != 0
        cid = None if call_ids is None else np.asarray(call_ids, dtype=object)[here]
        out.ledger.money.withdraw_many(who, int(step), cause=s2.plan.cause("atm"), wanted=wanted, call_ids=cid)


def _apply_buy(agents, world, aid, tgt, tick, out, schedule) -> None:
    """購入: 営業中・在庫>0・所持金≧価格 → 在庫−1・所持金−価格・所持+1・**売上+同額**。

    台帳(``out.ledger``)があるときは金=``purchase_many``・物=``sell_many`` を通し、
    ``world.pois.stock`` は棚(真値)の写しとして書き戻す。
    """
    r = agents.registry
    led = out.ledger
    has_target = (tgt >= 0) & (tgt < world.n_poi)
    poi = np.clip(tgt, 0, max(0, world.n_poi - 1))
    open_mask = world.open_mask(tick)
    is_open = has_target & open_mask[poi]
    price = world.pois.price[poi].astype(np.int64)
    in_stock = is_open & (world.pois.stock[poi] > 0)
    if led is not None and led.goods is not None and in_stock.any():
        in_stock = in_stock & led.goods.can_sell(poi)  # 棚(SKU 別)が真値
    can_pay = in_stock & _payable(agents, out, aid, price)  # 〔2-1〕腕の無いランは所持金 ≧ 価格(今のまま)

    _fail(agents, aid[~has_target], ResultCode.BAD_TARGET, tick, out)
    _fail(agents, aid[has_target & ~is_open], ResultCode.CLOSED, tick, out)
    _fail(agents, aid[is_open & ~in_stock], ResultCode.OUT_OF_STOCK, tick, out)
    _fail(agents, aid[in_stock & ~can_pay], ResultCode.MONEY_SHORT, tick, out)

    # ---- 屋内占有(16行表 行2・容量 c の M/M/c 近似): 満席なら待ち行列へ ----
    if out.crowd is not None and can_pay.any():
        room = np.zeros(aid.size, dtype=bool)
        sel = np.flatnonzero(can_pay)
        room[sel] = np.asarray(out.crowd.can_admit(poi[sel]), dtype=bool)
        queued = aid[can_pay & ~room]
        if queued.size:
            # 契約書 §2.1「購入」のコスト欄「価格・**待ち時間**」= 満席時は並ぶ(失敗ではない)
            r.activity[queued] = int(Activity.WAITING)
            r.queue_poi[queued] = poi[can_pay & ~room].astype(np.int32)
            r.queue_since[queued] = int(tick)
            _remember_queue_action(out, queued, _QUEUE_FOR_BUY)
            out.n_queued += int(queued.size)
            _ok(agents, queued, tick, out)
        can_pay = can_pay & room

    win = np.flatnonzero(can_pay)
    if win.size == 0:
        return
    _complete_buy(agents, world, aid[win], poi[win], price[win], tick, out)


def _complete_buy(agents, world, buyers, bought, paid, tick, out) -> None:
    """購入の完了(席あり・支払い・棚・所持・空腹・在席の登録)。``_apply_buy`` の後半を
    D-113 ③ で関数に切り出した(列から席へ入れた体にも同じ完了を使う)。挙動は不変。"""
    r = agents.registry
    led = out.ledger
    if led is not None and led.goods is not None and buyers.size > 1:
        # 同じ店への買い手が**棚の合計**(``world.pois.stock``=台帳の写し)を超えたら、超えた分は
        # **支払いの前に** OUT_OF_STOCK(第288 で見つけた欠陥の修正: 満席の列の捌き
        # ``_serve_poi_queue`` が棚 1 個の店へ同じ tick に 2 人を入れ、台帳が 2 人から支払いを
        # 受けたのに品は 1 個しか出ず、1 人ぶんの代金が消えていた=保存則が破れた)。
        # 超えない限り 1 バイトも変わらない(並び=呼び出し側の順)。
        order = np.lexsort((np.arange(bought.size), bought))
        sb = bought[order]
        starts = np.flatnonzero(np.concatenate(([True], sb[1:] != sb[:-1])))
        rank = np.arange(sb.size) - np.repeat(starts, np.diff(np.append(starts, sb.size)))
        fits = np.empty(bought.size, dtype=bool)
        fits[order] = rank < np.maximum(0, world.pois.stock[sb].astype(np.int64))
        if not bool(fits.all()):
            _fail(agents, buyers[~fits], ResultCode.OUT_OF_STOCK, tick, out)
            out.n_buy_over_stock += int(np.count_nonzero(~fits))
            buyers, bought, paid = buyers[fits], bought[fits], paid[fits]
            if buyers.size == 0:
                return
    # 〔第 2 期 2-4 V4〕レジの税(段階 2 の税の部品が動くランだけ・ほかは 0)=店の売上の写しは税抜き
    tax = np.zeros(buyers.size, dtype=np.int64)
    if led is not None and led.money is not None:
        status = led.money.purchase_many(buyers, bought, paid, tick)
        tax = _purchase_tax(led.money, buyers.size)
        ok = np.asarray(status) == 0
        if not ok.all():
            _fail(agents, buyers[~ok], ResultCode.MONEY_SHORT, tick, out)
            out.n_ledger_rejected += int((~ok).sum())
            buyers, bought, paid, tax = buyers[ok], bought[ok], paid[ok], tax[ok]
            if buyers.size == 0:
                return
    else:
        r.money[buyers] = (r.money[buyers].astype(np.int64) - paid).astype(np.int32)
    if led is not None and led.goods is not None:
        # ``GoodsLedger.sell_many`` は 2026-09-08 の直しの後、店ごとの前置数を棚の累積和に当て、1 回の呼びで
        # **全スロットをまたいで払い出す**(``can_sell`` の棚の**合計**と粒度が合う=正しい払い出しは台帳の側で完結)。
        # 直しの前は「最初の非空スロット」(``_first_nonempty_slot``)からしか払い出さず、ここで失敗行だけを次の
        # スロットへ回して埋め合わせていた。下の再試行(≤8 回)はその**保険として残す**だけで、進まなければ抜ける
        # (9 スロット以上の店でも偽の品切れにならないことを 11-09 に 12 スロットの店で確かめた=段 2 の突き合わせ)。
        # 逐次ループ宣言(P4): **再試行の回数**ぶん(≤8)。購入行数には比例しない。
        sold = np.zeros(bought.size, dtype=bool)
        pending = np.arange(bought.size, dtype=np.int64)
        for _ in range(_SELL_SLOT_RETRIES):
            if pending.size == 0:
                break
            got = np.asarray(led.goods.sell_many(bought[pending], tick), dtype=bool)
            sold[pending[got]] = True
            pending = pending[~got]
            if not got.any():
                break  # 進捗なし = 本当に在庫切れ
        if not sold.all():
            _fail(agents, buyers[~sold], ResultCode.OUT_OF_STOCK, tick, out)
            out.n_ledger_rejected += int((~sold).sum())
            buyers, bought, paid, tax = buyers[sold], bought[sold], paid[sold], tax[sold]
            if buyers.size == 0:
                return
        world.pois.stock[bought] = led.goods.aggregate_stock(bought).astype(
            world.pois.stock.dtype
        )
    else:
        _require_thawed(world, world.pois.stock)
        np.add.at(world.pois.stock, bought, -1)
    _require_thawed(world, world.pois.revenue)
    net = paid - tax  # 〔第 2 期 2-4 V4〕税抜き(税の無いランは paid と同じ)
    np.add.at(world.pois.revenue, bought, net)
    r.holdings[buyers] = np.minimum(r.holdings[buyers].astype(np.int16) + 1, 255).astype(np.uint8)
    if out.energy is None:
        r.hunger[buyers] = np.maximum(
            r.hunger[buyers].astype(np.int16) - BUY_HUNGER_RELIEF, 0
        ).astype(np.uint8)
    else:
        # 5 段目 5a(K3 (a)・K7): 飲食系の購入だけが摂取(軽食/飲料)・他の購入は空腹を動かさない
        _energy_snack(r, buyers, bought, tick, out.energy)
    r.activity[buyers] = int(Activity.SHOPPING)
    if out.crowd is not None:
        # 在席の登録(屋内占有の集約=人物②「行列・人だかり」の素)
        r.poi_ref[buyers] = bought.astype(np.int32)
        r.poi_since[buyers] = int(tick)
        r.queue_poi[buyers] = -1
        out.crowd.on_admit(bought)
    # 購入の件数は**台帳が通した行だけ**(支払いを却下された行・棚から出なかった行は数えない=
    # 第288 #54 の残りの過大計数の修正。以前は台帳の前の人数を数えていた)。
    out.n_purchases += int(buyers.size)
    out.revenue_delta += int(net.sum())
    if out.track_visits:  # 4 段目(M13): 成立した行だけ(台帳が通した行)
        out.visit_agents.append(np.asarray(buyers, dtype=np.int64).copy())
        out.visit_pois.append(np.asarray(bought, dtype=np.int64).copy())
    _ok(agents, buyers, tick, out)


def _apply_eat(agents, world, aid, tgt, tick, out, schedule) -> None:
    """**語彙 v2「食事」**(D-71 §3 E: 飲食店オブジェクトの affordance ``eat``)。

    前提=飲食店(``world.eatery_mask``)のセルに居る・営業中・所持金 ≧ 価格 /
    効果=所持金−価格・**店の売上+同額**(科目は購入と同じ ``消費支出``=保存則を壊さない)・
    空腹−``EAT_HUNGER_RELIEF``・在店(``Activity.SHOPPING``+在席登録)。

    購入(``_apply_buy``)との違いは 2 つだけ:
      1. 対象が**飲食店に限られる**(対象決定は ``commit._poi_in_cell(..., eatery_mask)``)。
      2. **棚在庫も所持品も動かさない**——食事は物の受け渡しではない(摂食≠購買。
         語彙政策 v0 の★「意味の損失」を解く、というのがこの語の目的)。したがって
         ``led.goods`` は通さず、``world.pois.stock`` も減らさない。
         **売上に対応する原価が立たない**ことは親へ報告済み(残差科目・ゲートには触れない)。

    失敗: 飲食店にいない=``NOT_IN_EATERY`` / 営業時間外=``CLOSED`` / 所持金不足=``MONEY_SHORT``。
    満席(``out.crowd``)は**失敗ではなく待ち行列**(購入と同じ扱い・契約書 §2.1 の「待ち時間」)。
    """
    r = agents.registry
    led = out.ledger
    poi = np.clip(tgt, 0, max(0, world.n_poi - 1))
    # 前提「飲食店のセルに居る」= **対象が飲食店であること**まで見る。対象決定
    # (``commit.intents_from_responses``)は既に飲食店に絞っているが、``apply`` を直に
    # 呼ぶ経路でも前提が名前どおりに効くようにここでも確かめる(同じ検査を 2 回するだけ)。
    in_eatery = (tgt >= 0) & (tgt < world.n_poi)
    if world.n_poi:
        in_eatery = in_eatery & np.asarray(world.eatery_mask, dtype=bool)[poi]
    is_open = in_eatery & world.open_mask(tick)[poi]
    price = world.pois.price[poi].astype(np.int64)
    can_pay = is_open & _payable(agents, out, aid, price)  # 〔2-1〕腕の無いランは所持金 ≧ 価格(今のまま)

    _fail(agents, aid[~in_eatery], ResultCode.NOT_IN_EATERY, tick, out)
    _fail(agents, aid[in_eatery & ~is_open], ResultCode.CLOSED, tick, out)
    _fail(agents, aid[is_open & ~can_pay], ResultCode.MONEY_SHORT, tick, out)

    # ---- 屋内占有(購入と同じ 16行表 行2): 満席なら並ぶ ----
    if out.crowd is not None and can_pay.any():
        room = np.zeros(aid.size, dtype=bool)
        sel = np.flatnonzero(can_pay)
        room[sel] = np.asarray(out.crowd.can_admit(poi[sel]), dtype=bool)
        queued = aid[can_pay & ~room]
        if queued.size:
            r.activity[queued] = int(Activity.WAITING)
            r.queue_poi[queued] = poi[can_pay & ~room].astype(np.int32)
            r.queue_since[queued] = int(tick)
            _remember_queue_action(out, queued, _QUEUE_FOR_EAT)
            out.n_queued += int(queued.size)
            _ok(agents, queued, tick, out)
        can_pay = can_pay & room

    win = np.flatnonzero(can_pay)
    if win.size == 0:
        return
    _complete_eat(agents, world, aid[win], poi[win], price[win], tick, out)


def _purchase_tax(money: Any, n: int) -> np.ndarray:
    """〔第 2 期 2-4 V4〕直前の ``purchase_many`` の行ごとのレジの税(``Ledger.last_purchase_tax``)。口の無い金の台帳
    (試験の偽の台帳・段階 2 より前の形)は 0=売上の写しは支払いのまま。"""
    fn = getattr(money, "last_purchase_tax", None)
    if fn is None:
        return np.zeros(int(n), dtype=np.int64)
    return np.asarray(fn(int(n)), dtype=np.int64)


def _complete_eat(agents, world, eaters, shops, paid, tick, out) -> None:
    """食事の完了(支払い・空腹・在店の登録)。``_apply_eat`` の後半を D-113 ③ で関数に
    切り出した(列から席へ入れた体にも同じ完了を使う)。挙動は不変。"""
    r = agents.registry
    led = out.ledger
    tax = np.zeros(eaters.size, dtype=np.int64)  # 〔第 2 期 2-4 V4〕レジの税(税の部品が動くランだけ)
    if led is not None and led.money is not None:
        status = led.money.purchase_many(eaters, shops, paid, tick)
        tax = _purchase_tax(led.money, eaters.size)
        ok = np.asarray(status) == 0
        if not ok.all():
            _fail(agents, eaters[~ok], ResultCode.MONEY_SHORT, tick, out)
            out.n_ledger_rejected += int((~ok).sum())
            eaters, shops, paid, tax = eaters[ok], shops[ok], paid[ok], tax[ok]
            if eaters.size == 0:
                return
    else:
        r.money[eaters] = (r.money[eaters].astype(np.int64) - paid).astype(np.int32)
    _require_thawed(world, world.pois.revenue)
    net = paid - tax  # 〔第 2 期 2-4 V4〕税抜き(税の無いランは paid と同じ)
    np.add.at(world.pois.revenue, shops, net)
    if out.energy is None:
        r.hunger[eaters] = np.maximum(
            r.hunger[eaters].astype(np.int16) - EAT_HUNGER_RELIEF, 0
        ).astype(np.uint8)
    else:
        # 5 段目 5a(K7 (a)): 食事=時間帯の比 × EER・since_meal=0(範囲内の食事)
        _energy_meal(r, eaters, tick, out.energy, kind="meal_in")
    r.activity[eaters] = int(Activity.SHOPPING)  # 在店(その tick は移動しない)
    if out.crowd is not None:
        r.poi_ref[eaters] = shops.astype(np.int32)
        r.poi_since[eaters] = int(tick)
        r.queue_poi[eaters] = -1
        out.crowd.on_admit(shops)
    out.n_meals += int(eaters.size)
    if out.track_visits:  # 4 段目(M13): 成立した行だけ
        out.visit_agents.append(np.asarray(eaters, dtype=np.int64).copy())
        out.visit_pois.append(np.asarray(shops, dtype=np.int64).copy())
    out.meal_yen += int(paid.sum())
    out.revenue_delta += int(net.sum())
    _ok(agents, eaters, tick, out)


def _apply_queue(agents, world, aid, tgt, tick, out, schedule) -> None:
    """**語彙 v3「並ぶ」**(第275 親の決め #2・expedient)。

    対象 POI(現在セルの POI=``commit.intents_from_responses``)が**飲食店なら食事**
    (``_apply_eat``)、**それ以外なら購入**(``_apply_buy``)へ委譲する。満席なら既存の
    待ち行列に入る(D-113 ③ の機構がそのまま効く)・空席なら即時成立。対象なし/解決不能は
    ``BAD_TARGET``。``last_action`` は 並ぶ(22)のまま(``apply`` の分岐が書く)。
    """
    has = (tgt >= 0) & (tgt < world.n_poi)
    _fail(agents, aid[~has], ResultCode.BAD_TARGET, tick, out)
    if not bool(np.any(has)):
        return
    a, t = aid[has], tgt[has]
    eat = np.asarray(world.eatery_mask, dtype=bool)[t]
    out.n_queue_to_eat += int(np.count_nonzero(eat))
    out.n_queue_to_buy += int(np.count_nonzero(~eat))
    if bool(np.any(eat)):
        _apply_eat(agents, world, a[eat], t[eat], tick, out, schedule)
    if bool(np.any(~eat)):
        _apply_buy(agents, world, a[~eat], t[~eat], tick, out, schedule)


def _apply_wait(agents, world, aid, tgt, tick, out, schedule) -> None:
    """待機: **常に可能=安全弁**(失敗しない)。

    **C9b G4「見る」**: ``out.focus_request`` に対象が入っていて、取得距離
    ``FOCUS_ACQUIRE_M`` 以内なら**注意の焦点**にする(動詞は足さない=「待機の対象」)。
    遠すぎる対象は焦点にならないが、**待機そのものは成功する**(契約書 §2 共通必須事項③
    「失敗しない行動が常に1つ以上(待機)」を崩さない)。
    """
    r = agents.registry
    # 段 2c(親決定 Q20): 意図を持って**歩いている**体の なし/待機 は「新しい行為が無い」=歩みを止めない
    walking = (r.intent_action[aid] != INTENT_NONE) & (r.activity[aid] == int(Activity.MOVING))
    if "plan_flags" in r.arrays:  # 9a: 計画の退出でホームへ歩いている体も同じ(ビットは walk_to_platform のランだけ立つ)
        walking |= ((r.plan_flags[aid].astype(np.int64) & EXIT_WALK_FLAG) != 0) & (
            r.activity[aid] == int(Activity.MOVING))
    r.activity[aid[~walking]] = int(Activity.WAITING)
    _set_focus(agents, world, aid, tick, out, require_near=True)
    _ok(agents, aid, tick, out)


def release_indoor(agents: AgentState, agent_ids) -> None:
    """在席の解除(回転率=滞在上限・16行表 行2 の expedient)。"""
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    if a.size == 0:
        return
    with agents.writable():
        r = agents.registry
        r.poi_ref[a] = -1
        r.poi_since[a] = -1
        r.activity[a] = np.where(
            r.activity[a] == int(Activity.SHOPPING), int(Activity.IDLE), r.activity[a]
        ).astype(r.activity.dtype)


#: D-113 ③: 並んだ目的(``CrowdProcess.queue_action`` の値)。
_QUEUE_FOR_BUY: Final[int] = 0
_QUEUE_FOR_EAT: Final[int] = 1


def _remember_queue_action(out: ResolveOutcome, queued: np.ndarray, kind: int) -> None:
    """並んだ目的を混雑場に控える(過程が欄を持たない fake でも落ちない)。"""
    qa = getattr(out.crowd, "queue_action", None)
    if qa is not None and queued.size:
        qa[queued] = np.int8(kind)


def _serve_poi_queue(agents, world, tick: int, out: ResolveOutcome) -> None:
    """D-113 ③(第268): 満席で並んだ体を、席が空いた分だけ**並んだ順**に席へ入れる。

    - 順序: ``(queue_since, agent_id)`` 昇順=先に並んだ体から(同 tick は id 順・決定論)。
      ``CrowdProcess.can_admit`` は行順で席を詰めるので、この並びを渡せば FIFO になる。
    - 完了: 並んだときの行動(購入/食事・``queue_action``)を ``_complete_buy``/``_complete_eat``
      で完了させる(支払い・棚・空腹・在席)。待つ間に閉店した店の列は解散(``CLOSED``)、
      所持金が足りなくなった体は ``MONEY_SHORT``、棚が空なら ``OUT_OF_STOCK`` で列を離れる。
    - 15 tick の離脱閾値(``crowd.step``)はそのまま=席が空かなければ従来どおり ``INTERRUPTED``。
    - 切替口 ``out.queue_service``(False=第267 以前=誰も捌かない)。混雑場が無ければ何もしない。
    - 〔11-03 M11・M28〕``out.defect_fixes``(腕 on=既定)では、捌く前に店のセルに居ない体を列から外し(失敗は書かない)、
      払えるかを ``_payable``(現金か口座)で見る。旧道(False)は居場所を見ず、現金だけで見る。

    逐次ループ宣言(P4): なし(並んでいる体の配列に対するベクトル判定・``can_admit`` 1 回)。
    """
    crowd = out.crowd
    if crowd is None or not out.queue_service:
        return
    r = agents.registry
    q = r.queue_poi.astype(np.int64)
    waiting = np.flatnonzero((q >= 0) & (q < world.n_poi))
    if waiting.size == 0:
        return
    since = r.queue_since.astype(np.int64)[waiting]
    order = np.lexsort((waiting, since))
    w = waiting[order]
    poi = q[w]
    if out.defect_fixes:
        # 〔11-03 M11〕並んでいる体がその店のセルに居なければ列から外す(移動・乗車の外で動いた体=本来 0 のはず)。
        # 活動と直前の結果は書かない(本人は列を離れる行為を試みていない)。
        away = np.asarray(r.cell, dtype=np.int64)[w] != world.pois.cell.astype(np.int64)[poi]
        if away.any():
            gone = w[away]
            r.queue_poi[gone] = -1
            r.queue_since[gone] = -1
            out.n_queue_dropped_away += int(gone.size)
            w, poi = w[~away], poi[~away]
            if w.size == 0:
                return
    # 閉店した店の列は解散
    open_mask = np.asarray(world.open_mask(tick), dtype=bool)
    closed = ~open_mask[poi]
    if closed.any():
        gone = w[closed]
        r.queue_poi[gone] = -1
        r.queue_since[gone] = -1
        r.activity[gone] = int(Activity.IDLE)
        _fail(agents, gone, ResultCode.CLOSED, tick, out)
        out.n_queue_closed += int(gone.size)
        w, poi = w[~closed], poi[~closed]
        if w.size == 0:
            return
    # 待つ間に払えなくなった体・棚が空になった店の列は**席を取る前に**離れる(空いた席は
    # 同じ tick に次の体へ回る)。
    qa = getattr(crowd, "queue_action", None)
    kind = (
        np.full(w.size, _QUEUE_FOR_BUY, dtype=np.int64)
        if qa is None
        else np.asarray(qa, dtype=np.int64)[w]
    )
    price = world.pois.price[poi].astype(np.int64)
    can_pay = r.money[w].astype(np.int64) >= price
    if out.defect_fixes:
        # 〔11-03 M28〕新しい行の購入・食事と同じ確かめ(``_payable``=経済の段階 2 の支払いの部品では現金か口座)。
        # 旧道は現金だけ=口座で払える体が列の中でだけ MONEY_SHORT で外れていた。
        cash_only = can_pay
        can_pay = _payable(agents, out, w, price)
        out.n_queue_payable_not_cash += int(np.count_nonzero(can_pay & ~cash_only))
    is_buy = kind != _QUEUE_FOR_EAT
    in_stock = np.ones(w.size, dtype=bool)
    if is_buy.any():
        in_stock[is_buy] = world.pois.stock[poi[is_buy]] > 0
        led = out.ledger
        if led is not None and led.goods is not None and in_stock[is_buy].any():
            sel = np.flatnonzero(is_buy)
            in_stock[sel] = in_stock[sel] & np.asarray(led.goods.can_sell(poi[sel]), dtype=bool)
    leave = ~can_pay | ~in_stock
    if leave.any():
        gone = w[leave]
        r.queue_poi[gone] = -1
        r.queue_since[gone] = -1
        r.activity[gone] = int(Activity.IDLE)
        _fail(agents, w[~can_pay], ResultCode.MONEY_SHORT, tick, out)
        _fail(agents, w[can_pay & ~in_stock], ResultCode.OUT_OF_STOCK, tick, out)
        keep = ~leave
        w, poi, price, is_buy = w[keep], poi[keep], price[keep], is_buy[keep]
        if w.size == 0:
            return
    # 席が空いた分だけ、行順(=並んだ順)に入れる
    room = np.asarray(crowd.can_admit(poi), dtype=bool)
    if not room.any():
        return
    adm, adm_poi, adm_price, adm_buy = w[room], poi[room], price[room], is_buy[room]
    r.queue_since[adm] = -1
    if adm_buy.any():
        _complete_buy(agents, world, adm[adm_buy], adm_poi[adm_buy], adm_price[adm_buy], tick, out)
    if (~adm_buy).any():
        _complete_eat(agents, world, adm[~adm_buy], adm_poi[~adm_buy], adm_price[~adm_buy], tick, out)
    out.n_served_from_queue += int(adm.size)


def balk_queue(agents: AgentState, agent_ids, tick: int) -> None:
    """待ち行列からの離脱(離脱閾値・``INTERRUPTED``=「途中打ち切り(混雑・閉鎖)」)。"""
    a = np.asarray(agent_ids, dtype=np.int64).ravel()
    if a.size == 0:
        return
    with agents.writable():
        r = agents.registry
        r.queue_poi[a] = -1
        r.queue_since[a] = -1
        r.activity[a] = int(Activity.IDLE)
        r.last_result[a] = int(ResultCode.INTERRUPTED)
        r.last_result_tick[a] = int(tick)
