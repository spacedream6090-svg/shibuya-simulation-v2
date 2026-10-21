"""engine.calendar2.book — 本人の予定の器(第 6 期 6-2 カレンダー 2・CA3・CA4・CA6・CA7)。

正: 決定 10-12 §4-1 CA3「各自が自分の理解を持つ(共有の 1 行にしない)・変えられるのは自分の行だけ・変更は最新値と、出来事の
記録への 1 行・欄に置き場所・確かさ(確定/仮)・元の会話・置き場所は性質で書き(知らせ・持ち歩き・見える範囲・忘れやすさ)、種類は
増やせる・頭の中だけの予定もエンジンは保管する」・CA4 (d)「壊れた予定だけ拒む・地名帳に無い場所は言葉のまま持つ」・CA6 (b)
(範囲外の過ごし方=本人の計画・置き場所=頭の中)・CA7 (a)(c)(アラームと時刻の実行意図は同じ種類・上限なし・出来事がきっかけの
ものは計画の記憶)・5-1「カレンダーに入るもの=スマホに入れるような予定は全部」。

- 行(``dict``・状態のファイルの値の木): 番号 ``id``・持ち主 ``owner``(行を変えられるのはこの体だけ)・種類 ``kind``(:data:`KINDS`)・
  始まり ``start_ns``・終わり ``end_ns``(−1=決めていない)・場所 ``cell``(地名帳のセル=−1 は地名帳に無い)と言葉 ``place``・
  誰と ``with``・何を ``what``・置き場所 ``placement``(:data:`PLACEMENTS`)・確かさ ``certain``(:data:`CERTAINTY`)・元の会話
  ``origin``(``[道具, 会話の鍵, 会話の番の id]`` か ``None``)・元の誘い ``offer``・状態 ``state``(:data:`STATES`)・知らせの時刻
  ``notify_ns``・結びつく行 ``link``・出来事の実行意図のきっかけ ``trigger``(会ったら思い出す相手)。ほかは本人の行でない観測の欄
  (``OBSERVED_FIELDS``=書いた時刻・見た回数・出発・到着・始まりの居場所・締め・頭の中の記憶の痕跡)。書いた出来事の id は
  層の診断の表に持つ(〔検収 M3〕記録の有無で行が変わらない)。
- 書く口: :meth:`PromiseBook.write`(本人が自分の行を書く=壊れた予定は ``ValueError``)・:meth:`PromiseBook.edit`(本人が自分の
  行の欄を変える=**ほかの体の行は** ``PermissionError``)・:meth:`PromiseBook.observe`(層が観測の欄だけを書く)・
  :meth:`PromiseBook.drop`(締めた行を日の締めで落とす)。
- :func:`broken`(CA4 (d)): 壊れた予定=始まりが無い・終わりが始まりより前・場所が空(セルも言葉も無い)。重なり・間に合わない・
  閉店中は壊れた予定ではない(層が記録だけする)。

**未リサーチ(expedient)**(つなぎの台帳 ``DOC-ca2-placement-kinds``): 置き場所の種類の初期の一覧 4 つ(アプリ・アラーム・手帳・
頭の中)と性質の値(1b の ``PLACEMENT_TRAITS`` と同じ 4 つの種類・頭の中の思い出し方だけ「記憶で思い出せたとき」)・行の種類 5 つ。

逐次ループ宣言: :meth:`PromiseBook.own_rows` は持ち主の行の数ぶん(体の数に比例しない)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from shibuya.engine.calendar2.arm import LEDGER_ARM

__all__ = [
    "PLACEMENTS", "PL_APP", "PL_ALARM", "PL_PLANNER", "PL_HEAD", "PLACEMENT_TRAITS", "KINDS", "K_PROMISE", "K_OWN",
    "K_PLAN", "K_ALARM", "K_INTENT", "STATES", "ST_LIVE", "ST_CANCELLED", "ST_NOT_GOING", "ST_DONE", "CERTAINTY",
    "PERSON_FIELDS", "OBSERVED_FIELDS", "EDITABLE_FIELDS", "broken", "PromiseBook",
]

#: 置き場所の種類(CA3: 性質で書く・種類は増やせる)。番号は行の ``placement`` の値。
PLACEMENTS: Final[tuple[str, ...]] = ("アプリ", "アラーム", "手帳", "頭の中")
PL_APP, PL_ALARM, PL_PLANNER, PL_HEAD = range(4)
#: 置き場所の性質(CA3=知らせ・持ち歩き・見える範囲・忘れやすさ)と思い出し方(AT1)。
PLACEMENT_TRAITS: Final[Mapping[str, Mapping[str, Any]]] = MappingProxyType({
    "アプリ": MappingProxyType({"知らせ": "本人が決めた時刻に通知", "持ち歩き": True, "見える範囲": "画面",
                                "忘れやすさ": "低い", "思い出し方": "通知・画面を見たとき", "重なりの警告": True}),
    "アラーム": MappingProxyType({"知らせ": "本人が決めた時刻に鳴る", "持ち歩き": True, "見える範囲": "音",
                                  "忘れやすさ": "低い", "思い出し方": "鳴る", "重なりの警告": False}),
    "手帳": MappingProxyType({"知らせ": "無し", "持ち歩き": True, "見える範囲": "開いたとき", "忘れやすさ": "中",
                              "思い出し方": "見たとき", "重なりの警告": False}),
    "頭の中": MappingProxyType({"知らせ": "無し", "持ち歩き": True, "見える範囲": "本人だけ", "忘れやすさ": "高い",
                                "思い出し方": "記憶で思い出せたとき", "重なりの警告": False}),
})
#: 行の種類(5-1: スマホに入れるような予定は全部・CA6 の本人の計画・CA7 のアラームと実行意図)。
KINDS: Final[tuple[str, ...]] = ("二人の約束", "本人の予定", "本人の計画", "アラーム", "出来事の実行意図")
K_PROMISE, K_OWN, K_PLAN, K_ALARM, K_INTENT = range(5)
#: 行の状態。
STATES: Final[tuple[str, ...]] = ("有効", "取り消し", "行かない", "済み")
ST_LIVE, ST_CANCELLED, ST_NOT_GOING, ST_DONE = range(4)
#: 確かさ(CA3)。番号は行の ``certain`` の値(0=仮・1=確定)。
CERTAINTY: Final[tuple[str, ...]] = ("仮", "確定")

#: 本人が書く欄(行を書くときに渡す)。
PERSON_FIELDS: Final[tuple[str, ...]] = (
    "kind", "start_ns", "end_ns", "cell", "place", "with", "what", "placement", "certain", "origin", "offer", "state",
    "notify_ns", "link", "trigger")
#: 本人が後から変えられる欄(:meth:`PromiseBook.edit`)。
#: 〔検収 M1〕``notify_ns`` は予定の時刻を変えたときにアプリが知らせを同じだけずらす(道具の性質)=持ち主の口で変える。
EDITABLE_FIELDS: Final[frozenset[str]] = frozenset({"start_ns", "end_ns", "cell", "place", "certain", "state",
                                                   "notify_ns"})
#: 層が観測して書く欄(本人の行の中身ではない=見た回数・出発・到着・始まりの居場所・締め・頭の中の記憶の痕跡)。
#: 〔検収 M3〕書いた出来事の id は行に持たない(記録の有無で行が変わらない=口の約束 1-3 の (1))=層の診断の表
#: ``Calendar2Layer._c2_event_of``(行の番号 → 出来事の id)。
OBSERVED_FIELDS: Final[tuple[str, ...]] = (
    "written_ns", "seen", "departed_ns", "arrived_ns", "at_start", "closed", "outcome", "trace")


def broken(fields: Mapping[str, Any]) -> str | None:
    """壊れた予定(CA4 (d))なら理由・そうでなければ ``None``。

    壊れた予定=始まりが無い(負)・終わりが始まりより前(終わりを決めた行だけ)・場所が空(地名帳のセルも言葉も無い)。
    """
    start = int(fields.get("start_ns", -1))
    end = int(fields.get("end_ns", -1))
    if start < 0:
        return "始まりが無い"
    if end >= 0 and end < start:
        return "終わりが始まりより前"
    if int(fields.get("cell", -1)) < 0 and not str(fields.get("place", "") or "").strip():
        return "場所が空"
    return None


class PromiseBook:
    """本人の予定の器(状態台帳の腕の行 ``CA2B``)。行は持ち主ごと=二人の約束も各自が自分の行を持つ。"""

    LEDGER_ARM: Final[str] = LEDGER_ARM

    def __init__(self) -> None:
        #: 行の番号 → 行(挿入順=書いた順)。
        self.rows: dict[int, dict[str, Any]] = {}
        #: 持ち主 → 行の番号の列(書いた順)。
        self.by_owner: dict[int, list[int]] = {}
        #: 次の行の番号。
        self.next_id: list[int] = [0]

    # ------------------------------------------------------------------ 書く口
    def write(self, owner: int, fields: Mapping[str, Any], *, written_ns: int) -> int:
        """本人 ``owner`` が自分の行を 1 つ書く → 行の番号。壊れた予定は ``ValueError``(呼び手が先に :func:`broken` を見る)。"""
        why = broken(fields)
        if why is not None:
            raise ValueError(f"壊れた予定は書けない({why})")
        unknown = set(fields) - set(PERSON_FIELDS)
        if unknown:
            raise KeyError(f"本人が書く欄の外: {sorted(unknown)}")
        rid = int(self.next_id[0])
        self.next_id[0] = rid + 1
        row: dict[str, Any] = {"id": rid, "owner": int(owner)}
        for k in PERSON_FIELDS:
            row[k] = _DEFAULTS[k] if k not in fields else _plain(fields[k])
        row.update({"written_ns": int(written_ns), "seen": 0, "departed_ns": -1, "arrived_ns": -1,
                    "at_start": -1, "closed": 0, "outcome": "", "trace": None})
        self.rows[rid] = row
        self.by_owner.setdefault(int(owner), []).append(rid)
        return rid

    def edit(self, requester: int, row_id: int, key: str, value: Any) -> Any:
        """本人 ``requester`` が自分の行の欄を変える → 前の値。**ほかの体の行は変えられない**(``PermissionError``)。"""
        row = self.rows[int(row_id)]
        if int(row["owner"]) != int(requester):
            raise PermissionError(f"体 {requester} は体 {row['owner']} の行 {row_id} を変えられない(変えられるのは自分の行だけ)")
        if key not in EDITABLE_FIELDS:
            raise KeyError(f"本人が変えられる欄の外: {key!r}")
        old = row[key]
        row[key] = _plain(value)
        return old

    def observe(self, row_id: int, key: str, value: Any) -> None:
        """層が観測の欄を書く(本人の行の中身は書かない)。"""
        if key not in OBSERVED_FIELDS:
            raise KeyError(f"観測の欄の外: {key!r}(本人の欄は edit)")
        self.rows[int(row_id)][key] = _plain(value)

    def drop(self, row_id: int) -> None:
        """締めた行を落とす(日の締め=有界化)。"""
        row = self.rows.pop(int(row_id))
        lst = self.by_owner.get(int(row["owner"]), [])
        if int(row_id) in lst:
            lst.remove(int(row_id))
        if not lst:
            self.by_owner.pop(int(row["owner"]), None)

    # ------------------------------------------------------------------ 読む口
    def own_rows(self, owner: int) -> list[dict[str, Any]]:
        """持ち主の行(書いた順)。"""
        return [self.rows[r] for r in self.by_owner.get(int(owner), ())]

    def __len__(self) -> int:
        return len(self.rows)


_DEFAULTS: Final[Mapping[str, Any]] = MappingProxyType({
    "kind": K_OWN, "start_ns": -1, "end_ns": -1, "cell": -1, "place": "", "with": [], "what": "", "placement": PL_HEAD,
    "certain": 1, "origin": None, "offer": -1, "state": ST_LIVE, "notify_ns": -1, "link": -1, "trigger": -1,
})


def _plain(v: Any) -> Any:
    """状態のファイルの値の木に入る形(タプルは list・numpy の数は Python の数)。"""
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if hasattr(v, "item") and not isinstance(v, (str, bytes)):
        return v.item()
    return v
