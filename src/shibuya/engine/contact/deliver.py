"""engine.contact.deliver — 届く(エンジン)=メッセージ・電話・既読(第 6 期 6-4 C1・決定 10-12 §4-4 CT3・CT9・§4-2 TM1)。

正: CT3「届くのはエンジンです。通知は周りの出来事の 1 つとして System 1 へ入ります」「返す・書くは CT2 です。エンジンは時刻も
回数も決めません」・TM1「メッセージは、届くのはエンジン、気づく・読む・返すは本人の判断と状態」「電話は窓の境目で届け、出るかは
本人が決めます」・CT2「既読は道具の性質として扱います」・CT9(記録に道具の欄と届いた/読んだ時刻・範囲の外から来た情報に出どころの
印)・3-2 の窓の待ち行列の「境目で配達する種類」(``engine.batching.BOUNDARY``)。

持ち主 :class:`Mailbox`(状態台帳の腕の行 ``CT1I``=軸 1 behavior・軸 2 required・道筋 ``contact.mail``):

- ``_inbox``: 体 → 届いたメッセージの行 ``[番号, 送った人, グループ(−1), 道具, 送った時刻, 届いた時刻, 読んだ時刻(−1), モーラ数, 本文]``。
  届いた出来事の記録の id は行に持たない(〔1-3 の (1) の直し〕層の診断の表 ``ContactLayer._ct_event_of``=記録 on/off で行が同じ)。
- ``_unseen``: 体 → ``[まだ System 1 に入れていない届いた数, 最初に届いた時刻]``(通知の刺激の素=その刻みに 1 回の刺激)。
- ``_sent``: メッセージの番号 → ``[送った人, 道具, 送った時刻, 届け先の数, 読んだ数]``(既読の印=道具の性質)。
- ``_held``: 電源の切れた体 → 網が預かっているメッセージ(電源が入ったら届く=本段は充電が無い=預かったまま)。
- ``_pending``: 予約の鍵 → 窓の境目で届ける事象(送信=打ち終わり・着信)の行 ``[種類, 頼んだ時刻, 境目の時刻, …]``。進行役の待ち行列は捨ててよい(状態台帳の行 BW)=予約の
  中身はここに持ち、再開では組み立ての後の結び(``ContactLayer.bind_queue``)が待ち行列に入れ直す。
- ``_ringing``: 着信中の体 → ``[かけた人, 鳴った時刻, かけた時刻]``・``_calling``: かけた体 → ``[相手, かけた時刻, 段 0=予約/1=鳴っている]``。
- ``_next``: ``[次のメッセージの番号, 次の予約の鍵]``。

届け方(エンジンの規則=物理と道具の性質だけ):

- メッセージ: 送った時刻に、電源が入り電波の届く相手の道具へ届く(``deliver_message``)。届いた行・出来事 ``連絡:届いた``(原因=
  過程 ``contact``=網)・相手の ``_unseen`` に積む。電源の切れた相手は網が預かる(``_held``)。
- 送信(打ち終わり)と着信は窓の境目(待ち行列の種類 ``contact.send``・``contact.ring``=届け方 ``BOUNDARY``=処理中の窓の中なら
  次の窓の頭)。どちらも世界の事象(持ち主 −1)で、同じ時刻の刻みの事象(順位 0)より前(順位 −2・−1)=その刻みの知覚に入る。
  打ち終わりの境目は「打つ時間」の代わり(T2 の細かい時計の口が来るまで=宣言・つなぎの台帳 ``DOC-ct-c1-chat-clock``)。
- 既読: 読んだとき(本人の判断の時刻)に送った人の道具へ印が届く(``_sent`` の読んだ数・出来事 ``連絡:既読``=原因 過程 ``contact``)。
  気づくかは送った人が画面を見たとき(知覚の事実の道具の状態)=驚き(予想とのずれ)は判断の側。

**未リサーチ(expedient)**: 待ち行列の種類の番号 40・41 と順位 −1・−2(刻みの事象の前)・読んだメッセージを持つ長さ 1 日
(``MAIL_KEEP_S``=日の頭で古い既読を落とす=有界)・網が預かるのは電源が切れている間だけ(電波は全域で届く)。

逐次ループ宣言: :meth:`Mailbox.deliver` は届け先の数ぶん(1 対 1 は 1・グループは成員の数)。:meth:`Mailbox.read_all` は
その体の未読の数ぶん。:meth:`Mailbox.prune` は届いた行の数ぶん(日に 1 回)。
"""

from __future__ import annotations

from typing import Any, Final, Iterable, Sequence

from shibuya.core.time_consts import SECONDS_PER_DAY
from shibuya.engine.batching import BOUNDARY
from shibuya.engine.contact.arm import LEDGER_ARM

__all__ = [
    "VIA_MESSAGE", "VIA_GROUP", "VIA_CALL", "VIAS", "KIND_RING", "KIND_SEND", "RANK_RING", "RANK_SEND",
    "RING_DELIVERY", "SEND_DELIVERY", "MAIL_KEEP_S", "P_SEND", "P_RING", "Mailbox", "OUTSIDE_ORIGIN", "senders_of",
]

VIA_MESSAGE: Final[str] = "メッセージ"
VIA_GROUP: Final[str] = "グループ"
VIA_CALL: Final[str] = "通話"
#: 道具のコード(行の欄)→ 語(1-3 の ``Event.via`` の語)。
VIAS: Final[tuple[str, ...]] = (VIA_MESSAGE, VIA_GROUP, VIA_CALL)

#: 進行役の待ち行列の種類(着信・送信=打ち終わり)と順位(同じ時刻の刻みの事象=順位 0 より前)。
KIND_RING: Final[int] = 40
KIND_SEND: Final[int] = 41
RANK_RING: Final[int] = -1
RANK_SEND: Final[int] = -2
#: 届け方(TM1=窓の境目)。試験の負の対照だけが ``IN_WINDOW`` に差し替える。
RING_DELIVERY: str = BOUNDARY
SEND_DELIVERY: str = BOUNDARY
#: 読んだメッセージを持つ長さ[秒](日の頭で、これより前に読んだ行を落とす)。
MAIL_KEEP_S: Final[int] = SECONDS_PER_DAY
#: 予約の種類(``_pending`` の行の 0 番目)。
P_SEND: Final[int] = 0
P_RING: Final[int] = 1
#: 範囲の外にいる体が送ったメッセージの出どころの印(CT9)。
OUTSIDE_ORIGIN: Final[str] = "contact:outside"

# 届いた行の欄の位置
_MSG, _SENDER, _GROUP, _VIA, _TSEND, _RECV, _READ, _MORA, _TEXT = range(9)


class Mailbox:
    """届いた・送った・予約のメッセージと着信(書く口はこのクラスのメソッドだけ)。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

    def __init__(self) -> None:
        self._inbox: dict[int, list[list[Any]]] = {}
        self._unseen: dict[int, list[int]] = {}
        self._sent: dict[int, list[int]] = {}
        self._held: dict[int, list[list[Any]]] = {}
        self._pending: dict[int, list[Any]] = {}
        self._ringing: dict[int, list[int]] = {}
        self._calling: dict[int, list[int]] = {}
        self._next: list[int] = [0, 0]

    # ------------------------------------------------------------------ 予約(窓の境目)
    def new_message_id(self) -> int:
        m = int(self._next[0])
        self._next[0] = m + 1
        return m

    def reserve(self, row: list[Any]) -> int:
        """窓の境目で届ける事象を予約の表に置き、鍵を返す(待ち行列への予約は持ち主の結びが行う)。"""
        k = int(self._next[1])
        self._next[1] = k + 1
        self._pending[k] = list(row)
        return k

    def take_pending(self, key: int) -> list[Any] | None:
        return self._pending.pop(int(key), None)

    def pending_items(self) -> list[tuple[int, list[Any]]]:
        """予約の表(鍵の昇順=予約した順)。"""
        return sorted(self._pending.items())

    # ------------------------------------------------------------------ メッセージ
    def deliver(self, msg: int, sender: int, recipients: Sequence[int], group: int, via: int, t_send: int,
                mora: int, text: str, on: Any) -> tuple[list[int], list[int]]:
        """送った時刻に届ける。``on(体)`` が偽(電源が切れた)の体は網が預かる。→(届いた体・預かった体)。"""
        got: list[int] = []
        held: list[int] = []
        self._sent[int(msg)] = [int(sender), int(via), int(t_send), len(recipients), 0]
        for r in recipients:  # 逐次ループ宣言: 届け先の数ぶん
            row = [int(msg), int(sender), int(group), int(via), int(t_send), int(t_send), -1, int(mora), str(text)]
            if bool(on(int(r))):
                self._inbox.setdefault(int(r), []).append(row)
                u = self._unseen.setdefault(int(r), [0, int(t_send)])
                u[0] += 1
                got.append(int(r))
            else:
                self._held.setdefault(int(r), []).append(row)
                held.append(int(r))
        return got, held

    def take_unseen(self) -> list[tuple[int, int, int]]:
        """System 1 に入れる「新しく届いた」体 ``(体, 数, 最初に届いた時刻)``(体の番号の昇順)。取ったら空にする。"""
        out = sorted((int(a), int(v[0]), int(v[1])) for a, v in self._unseen.items())
        self._unseen.clear()
        return out

    def unread(self, agent: int) -> list[list[Any]]:
        return [r for r in self._inbox.get(int(agent), ()) if int(r[_READ]) < 0]

    def unread_count(self, agent: int) -> int:
        return sum(1 for r in self._inbox.get(int(agent), ()) if int(r[_READ]) < 0)

    def read_all(self, agent: int, t_ns: int) -> list[list[Any]]:
        """体の未読を全部読む(本人の判断の時刻 ``t_ns``)→ 読んだ行(写し)。送った人の既読の数を進める。"""
        out: list[list[Any]] = []
        for r in self._inbox.get(int(agent), ()):  # 逐次ループ宣言: その体の届いた行の数ぶん
            if int(r[_READ]) >= 0:
                continue
            r[_READ] = int(t_ns)
            s = self._sent.get(int(r[_MSG]))
            if s is not None:
                s[4] += 1
            out.append(list(r))
        return out

    def prune(self, now_ns: int, keep_ns: int) -> int:
        """古い既読の行(読んだ時刻が ``now − keep`` より前)と、全部の届け先が読んだか古い送った行を落とす。落とした数。"""
        cut = int(now_ns) - int(keep_ns)
        n = 0
        for a in list(self._inbox):
            rows = self._inbox[a]
            keep = [r for r in rows if not (0 <= int(r[_READ]) < cut)]
            n += len(rows) - len(keep)
            if keep:
                rows[:] = keep
            else:
                del self._inbox[a]
        for m in [m for m, s in self._sent.items() if s[4] >= s[3] or int(s[2]) < cut]:
            del self._sent[m]
        return n

    # ------------------------------------------------------------------ 電話
    def ringing_of(self, callee: int) -> list[int] | None:
        return self._ringing.get(int(callee))

    def calling_of(self, caller: int) -> list[int] | None:
        return self._calling.get(int(caller))

    def start_calling(self, caller: int, callee: int, t_call: int) -> None:
        self._calling[int(caller)] = [int(callee), int(t_call), 0]

    def ring(self, caller: int, callee: int, t_ring: int, t_call: int) -> None:
        self._ringing[int(callee)] = [int(caller), int(t_ring), int(t_call)]
        c = self._calling.get(int(caller))
        if c is not None:
            c[2] = 1

    def stop_ringing(self, caller: int, callee: int) -> None:
        """着信と呼び出しを終える(出た・出ない・切った・不通)。"""
        if self._ringing.get(int(callee), [-1])[0] == int(caller):
            del self._ringing[int(callee)]
        if self._calling.get(int(caller), [-1])[0] == int(callee):
            del self._calling[int(caller)]

    def ringing_items(self) -> list[tuple[int, list[int]]]:
        return sorted(self._ringing.items())

    def calling_items(self) -> list[tuple[int, list[int]]]:
        return sorted(self._calling.items())

    # ------------------------------------------------------------------ 計器
    def mail_counts(self) -> dict[str, int]:
        return {
            "inbox_rows": int(sum(len(v) for v in self._inbox.values())),
            "unread": int(sum(1 for v in self._inbox.values() for r in v if int(r[_READ]) < 0)),
            "held": int(sum(len(v) for v in self._held.values())),
            "pending": len(self._pending), "ringing": len(self._ringing), "calling": len(self._calling),
            "sent_open": len(self._sent),
        }


def senders_of(rows: Iterable[list[Any]]) -> list[tuple[str, int, int]]:
    """読んだ行 → 会話ごとの束 ``(鍵の種類 p/g, 相手かグループ, 最後の行の番号)``(出た順・重ねない)。"""
    out: list[tuple[str, int, int]] = []
    seen: set[tuple[str, int]] = set()
    for r in rows:
        k = ("g", int(r[_GROUP])) if int(r[_GROUP]) >= 0 else ("p", int(r[_SENDER]))
        if k not in seen:
            seen.add(k)
            out.append((k[0], k[1], int(r[_MSG])))
    return out
