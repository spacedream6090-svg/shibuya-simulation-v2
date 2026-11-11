"""world.processes.circularity — 循環(同じ値の系で動かして採点する)の機械検査(第340 段 2 の 2・回答 11-01 §3)。

正典: 回答 11-01 §3「つなぎの台帳と WorldProcess に ``drives_from``(何の系の値で動くか)の欄、パターン台帳の各行に
『採点する系』、較正に使った錨に ``burned``。CI で突き合わせ、重なれば落とす(W19・read_guard と同じ型)」。

突き合わせの規則(本モジュールの読み)
    主体 S(世界過程・PlanSpec・つなぎの台帳の行)の ``drives_from`` に系 X があり、S の ``contributes`` に入る
    パターン行 R が X を採点する(R の ID が X か、R の「採点する系」が X)とき、**重なり**とする。重なりの例外は
    2 つ: (1) R の ``burned`` が ``burned``/``外す`` で始まる(較正に使った・一時的に検証から外した)、(2) S に
    「無いと宣言」(``Absence`` の no_actor/no_port)があり、**エンジンがもう動かしていない**(``engine_stopped=True``)うえ、
    R がその宣言の錨(``keeps_anchor`` と結ぶ過程の ``contributes``)に入る(〔検収 中-3・低-2〕)。宣言があっても
    ``engine_stopped=False`` なら例外にせず、「宣言と実装が食い違う」と出して落とす。``要確認`` の印は例外にしない。
    ``drives_from`` の ``none`` と未記入は突き合わせない。系は行の ID と「採点する系」の欄の語(``data:<id>`` を含む)の
    どれでも重なりを見る(〔検収 中-1〕)。

    代打の条件 ⑤(代打の出力が、その過程の検証に使う錨の系に入らない)は ``stand_in_overlap`` で別に見る
    (疑いの行の記録用。⑤ の重なりは系の名 ``stand_in`` の :class:`Overlap` にして、下の 2 段で同じに扱う)。

CI の 2 段(11-02r/§1 #6「宣言の無い重なり=落とす/宣言つき(既知の循環・外す段つき)=警告」)
    例外(``burned``/``外す``/止めた「無い」の宣言)の付かない重なりを :func:`classify` で 2 つに分ける。
    :data:`KNOWN_CIRCULARITIES`(パターン行・系・主体・理由・**外す段**・決定の ID)に載る重なりは**警告**(CI のログに
    出す)、載らない重なりは**落とす**。宣言は外す段が空なら作れない(:class:`KnownCircularity` が止める)。どの重なりにも
    当たらない宣言(古くなった宣言)は :func:`stale_declarations` で見つけて落とす(宣言だけが残るのを防ぐ)。
    パターン台帳の ``burned`` の欄が「既知の循環」で始まる行(:attr:`PatternScoring.known`)は、その行の宣言が
    :data:`KNOWN_CIRCULARITIES` にあることを試験で突き合わせる(台帳の文と宣言の表の 2 か所)。

読む物: パターン台帳(Markdown・列の名で引く)・つなぎの台帳の JSON(行の欄 ``drives_from`` ほか)・世界の台帳
(``first_batch.build_registry``)。層契約により engine の台帳の読み口は使わない(JSON を直に読む)。

逐次ループ宣言: なし(試験と道具が 1 回呼ぶだけ・ランの中では呼ばない)。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Mapping

from shibuya.world.ledger import absent as _AB
from shibuya.world.ledger.constitution import (
    ENV_PATTERN_MD,
    PATTERN_LEDGER_RELPATH,
    _doc_path,
    _repo_root,
    _split_row,
)
from shibuya.world.ledger.records import DRIVES_NONE

__all__ = [
    "COL_SCORING",
    "COL_BURNED",
    "BRIDGE_LEDGER_RELPATH",
    "PatternScoring",
    "Subject",
    "Overlap",
    "parse_pattern_scoring",
    "load_ledger_rows",
    "subjects_from_registry",
    "subjects_from_ledger",
    "find_overlaps",
    "stand_in_overlap",
    "COL_CATEGORY",
    "STAND_IN",
    "KnownCircularity",
    "KNOWN_CIRCULARITIES",
    "classify",
    "stale_declarations",
    "warning_lines",
]

COL_SCORING: Final[str] = "採点する系"
COL_BURNED: Final[str] = "burned"
COL_CATEGORY: Final[str] = "区分"
BRIDGE_LEDGER_RELPATH: Final[str] = "docs/design/bridging-ledger.json"
MISMATCH: Final[str] = "無いと宣言したが規則がまだ動く=宣言と実装が食い違う"
#: ``burned`` の欄のうち突き合わせの例外にする頭の語。
_EXEMPT_HEADS: Final[tuple[str, ...]] = ("burned", "外す")
#: ``burned`` の欄のうち「既知の循環」(宣言つき=警告)の頭の語(11-02r/§1 #6)。例外にはしない(警告で残す)。
_KNOWN_HEAD: Final[str] = "既知の循環"
#: 代打の条件 ⑤ の重なりの系の名(``drives_from`` の系ではなく、代打の出力が錨に入ること)。
STAND_IN: Final[str] = "stand_in"


@dataclass(frozen=True)
class PatternScoring:
    """パターン台帳の 1 行の「採点する系」と ``burned``。"""

    id: str
    scoring: str
    burned: str
    #: 「区分」の欄(列の無い表は空)。検証か較正か初期化かの読みに使う(11-02r §1 #6 の D5′・E5 の試験)。
    category: str = ""

    @property
    def exempt(self) -> bool:
        """突き合わせの例外か(``burned``/``外す`` で始まる)。"""
        return self.burned.startswith(_EXEMPT_HEADS)

    @property
    def known(self) -> bool:
        """「既知の循環」と宣言した行か(例外にはしない=警告。宣言は :data:`KNOWN_CIRCULARITIES`)。"""
        return self.burned.startswith(_KNOWN_HEAD)

    @property
    def systems(self) -> frozenset[str]:
        """この行が採点する系の id(行の ID と「採点する系」の欄の・区切りの語)。"""
        parts = {p.strip() for p in self.scoring.replace("、", "・").split("・") if p.strip()}
        return frozenset({self.id, *parts})


@dataclass(frozen=True)
class Subject:
    """突き合わせの主体(世界過程・PlanSpec・つなぎの台帳の行)。"""

    kind: str
    id: str
    drives_from: tuple[str, ...]
    contributes: tuple[str, ...]
    absent_id: str = ""
    absent_stopped: bool = False
    absent_anchors: tuple[str, ...] = ()
    calibration_declined: tuple[str, ...] = ()
    world_process: str = ""
    note: str = ""

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.id}"


@dataclass(frozen=True)
class Overlap:
    """重なり 1 件。``exempt`` が空なら CI で落とす候補。"""

    subject: str
    system: str
    pattern_id: str
    exempt: str = ""
    detail: str = field(default="", compare=False)

    def as_dict(self) -> dict[str, str]:
        return {"subject": self.subject, "system": self.system, "pattern_id": self.pattern_id,
                "exempt": self.exempt, "detail": self.detail}


def parse_pattern_scoring(path: str | Path | None = None) -> dict[str, PatternScoring]:
    """パターン台帳の §1・§9 の表(先頭の列 ``ID``/``行``・§2 の封印表を除く)から 2 列を列の名で読む。

    Raises:
        ValueError: 2 列のある表が 1 つも無い(列を足す前の台帳)。
    """
    md = _doc_path(PATTERN_LEDGER_RELPATH, ENV_PATTERN_MD, path)
    out: dict[str, PatternScoring] = {}
    cols: tuple[int, int, int] | None = None
    sealed = False
    for raw in md.read_text(encoding="utf-8").split("\n"):
        line = raw.strip()
        if line.startswith("## "):
            sealed = line.startswith("## 2.")
        cells = _split_row(raw)
        if not cells:
            cols = None
            continue
        if cells[0] in ("ID", "行") and not sealed:
            cols = ((cells.index(COL_SCORING), cells.index(COL_BURNED),
                     cells.index(COL_CATEGORY) if COL_CATEGORY in cells else -1) if COL_SCORING in cells else None)
            continue
        if cols is None or set(line) <= set("|-: "):
            continue
        rid = cells[0]
        if not rid or rid.startswith("~~"):
            continue
        out[rid] = PatternScoring(rid, cells[cols[0]], cells[cols[1]], cells[cols[2]] if cols[2] >= 0 else "")
    if not out:
        raise ValueError(f"{md}: 「{COL_SCORING}」と「{COL_BURNED}」の列のある表が無い")
    return out


def load_ledger_rows(path: str | Path | None = None) -> list[dict[str, Any]]:
    """つなぎの台帳の行(JSON の辞書のまま)。"""
    p = Path(path) if path is not None else _repo_root(BRIDGE_LEDGER_RELPATH) / BRIDGE_LEDGER_RELPATH
    return list(json.loads(p.read_text(encoding="utf-8"))["bridges"])


def _absence_info(a: Any, contributes: Iterable[str]) -> tuple[str, bool, tuple[str, ...]]:
    if a is None or a.kind not in ("no_actor", "no_port"):
        return "", False, ()
    anchors = tuple(dict.fromkeys([*a.keeps_anchor, *contributes]))
    return a.id, bool(a.engine_stopped), anchors


def subjects_from_registry(registry: Any) -> list[Subject]:
    """世界の台帳の過程と PlanSpec(``drives_from`` を書いたものだけ)。"""
    out: list[Subject] = []
    for kind, items in (("world_process", registry.processes), ("plan_spec", registry.plan_specs)):
        for p in items:
            if not p.drives_from:
                continue
            ab, stopped, anchors = _absence_info(p.absence, p.contributes)
            out.append(Subject(kind, p.id, tuple(p.drives_from), tuple(p.contributes), ab, stopped, anchors))
    return out


def subjects_from_ledger(rows: Iterable[Mapping[str, Any]], registry: Any) -> list[Subject]:
    """つなぎの台帳の active の行のうち ``drives_from`` を書いた行。``contributes`` は行の欄と、結んだ世界過程
    (``world_process``)の ``contributes`` の合併。無いの宣言は結んだ世界過程か routing の行から引く。"""
    procs = {p.id: p for p in (*registry.processes, *registry.plan_specs)}
    by_row = _AB.by_routing_row()
    out: list[Subject] = []
    for r in rows:
        if r.get("status") != "active" or not r.get("drives_from"):
            continue
        wp = str(r.get("world_process", ""))
        contrib = list(r.get("contributes", ()))
        absence = None
        if wp:
            p = procs.get(wp)
            if p is None:
                raise ValueError(f"{r['id']}: world_process {wp!r} が世界の台帳に無い")
            contrib += [c for c in p.contributes if c not in contrib]
            absence = p.absence
        n = r.get("routing_row", 0)
        if (absence is None or absence.kind not in ("no_actor", "no_port")) and n in by_row:
            absence = by_row[n]
        ab, stopped, anchors = _absence_info(absence, contrib)
        out.append(Subject("bridge", r["id"], tuple(r["drives_from"]), tuple(contrib), ab, stopped, anchors,
                           tuple(r.get("calibration_declined", ())), wp, str(r.get("drives_note", ""))))
    return out


def find_overlaps(subjects: Iterable[Subject], scoring: Mapping[str, PatternScoring]) -> list[Overlap]:
    """``drives_from`` と「採点する系」の重なり(例外の印つき)。"""
    out: list[Overlap] = []
    for s in subjects:
        for x in s.drives_from:
            if x == DRIVES_NONE:
                continue
            for pid in s.contributes:
                ps = scoring.get(pid)
                systems = ps.systems if ps is not None else frozenset({pid})
                if x not in systems:
                    continue
                note = ""
                if ps is not None and ps.exempt:
                    ex = "burned"
                elif s.absent_id and s.absent_stopped and pid in s.absent_anchors:
                    ex = "absent"
                else:
                    ex = ""
                    if s.absent_id and not s.absent_stopped:
                        note = f"・{MISMATCH}"
                out.append(Overlap(s.key, x, pid, ex,
                                   f"burned={ps.burned if ps else '(台帳に行なし)'}・absent={s.absent_id or '—'}{note}"))
    return out


def stand_in_overlap(subject_contributes: Iterable[str], anchors: Iterable[str]) -> tuple[str, ...]:
    """代打の条件 ⑤ の見方: 代打の出力が入る錨(``contributes``)と、疑いの錨の重なり。"""
    c = set(subject_contributes)
    return tuple(a for a in anchors if a in c)


# ================================================================== 11-02r/§1 #6: CI の 2 段(宣言つき=警告・宣言の無い=落とす)
_DEC_6 = "11-02r/§1 #6"


@dataclass(frozen=True)
class KnownCircularity:
    """既知の循環の宣言 1 件(11-02r/§1 #6)。``remove_at`` が空の宣言は作れない(外す段つきだけが宣言)。

    Attributes:
        pattern_id: 採点する行(パターン台帳の ID)。
        system: 重なった系(``drives_from`` の値・``data:<id>``)か :data:`STAND_IN`(代打の出力が錨に入る=条件 ⑤)。
        subjects: 重なった主体(:attr:`Subject.key` の形=``world_process:<id>``・``bridge:<id>``)。
        reason: なぜ循環か(1 文)。
        remove_at: 外す段(この段で循環が解ける・空は不可)。
        decided: 決定の ID(中身は写さない=CLAUDE.md §6)。
        basis: ``decided``=外す段がユーザーの決定に書いてある/``inferred``=それ以外(実装役が台帳の行から当てた・親の案=
            親が確かめる。〔検収 中-2〕循環そのものはユーザーの決定でも、外す段が決定に無ければ inferred)。
    """

    pattern_id: str
    system: str
    subjects: tuple[str, ...]
    reason: str
    remove_at: str
    decided: str = _DEC_6
    basis: str = "inferred"

    def __post_init__(self) -> None:
        if not self.remove_at.strip():
            raise ValueError(f"{self.pattern_id}/{self.system}: 既知の循環の宣言は外す段が要る(11-02r §1 #6)")
        if not self.subjects:
            raise ValueError(f"{self.pattern_id}/{self.system}: 主体が空")
        if self.basis not in ("decided", "inferred"):
            raise ValueError(f"{self.pattern_id}/{self.system}: basis は decided か inferred")

    def covers(self, o: Overlap) -> bool:
        """重なり ``o`` がこの宣言に当たるか(行・系・主体の 3 つが同じ)。"""
        return o.pattern_id == self.pattern_id and o.system == self.system and o.subject in self.subjects


_CAR = ("world_process:vehicle_cross_section", "bridge:DEC-109-driveCars")
_W17 = ("bridge:DEC-63-weeklyPlan", "bridge:DEC-69-sleepOnPlan", "bridge:DEC-71-wakeUp")
_W17_STAGE = ("6-2(W17 を初期の予定に格下げし、照合は構築に使っていない表で行う=パターン台帳 §10-2 の社会生活基本調査の行・"
              "DEC-63/69/71 の外す段)")

#: 既知の循環の宣言(11-02r/§1 #6)。第340(#133)で「警告のまま」にした重なり(車→D5・騒音→D12′・W17→A5〜A7・席 30 分→D8・
#: 補充→W1/E5・家で使う→W1)と、E5 の納品。車→D5′ は D5′ を burned にしたので例外の側(ここに無い)。
KNOWN_CIRCULARITIES: Final[tuple[KnownCircularity, ...]] = (
    KnownCircularity("D5", "data:road_census_r3", _CAR,
                     "車の断面の台数を道路交通センサス R3 の同じ行から作り、D5(交通流の日内二峰性)も同じ調査で採点する",
                     "通過交通を境界の外の入力にし、断面の区間を範囲の外側(入力)と内側(検証)に分ける段(DEC-109 の外す段=7・"
                     "回答 11-01 §10-1・パターン台帳 §10-2 の自動車の行)"),
    KnownCircularity("D12′", "data:tokyo_noise_r5", ("world_process:static_noise_field",),
                     "W10 の静的な騒音場の残差を都環境局 R5 の 7 点で照合し、D12′ も同じ点で採点する",
                     "7(騒音の照合を較正に使っていない測定点に分ける段=パターン台帳 §10-1 の騒音の行・計画に段が無い)"),
    *(KnownCircularity(a, "data:ssb", subs,
                       "W17 の週の表の元が社会生活基本調査で、A5〜A7 も同じ調査で採点する", _W17_STAGE)
      for a, subs in (("A5", _W17), ("A6", _W17), ("A7", ("bridge:DEC-63-weeklyPlan",)))),
    KnownCircularity("D8", STAND_IN, ("bridge:DEC-31-leaveSeat",),
                     "席を 30 分で一律に解く代打の出力が、商業滞在時間 D8 の分布の上端を決める",
                     "11-01p-3(席を立つ口=活動の「まで」と「続けるか」の口ができる段・DEC-31 の外す段)"),
    KnownCircularity("W1", STAND_IN, ("bridge:DEC-98-restock",),
                     "10 時の補充の代打が棚を満たし、売れ残りと消費を経て廃棄 sink(W1 の欄)に入る",
                     "11-01p-3(補充の口=店員の判断の口ができる段・DEC-98 の外す段)"),
    KnownCircularity("E5", STAND_IN, ("bridge:DEC-98-restock", "bridge:DEC-102-inboundDelivery"),
                     "補充の代打と納品の入力の出力が、消費支出の錨 E5 の系に入る(contributes=E5)。11-02r §1 #6=E5 は検証・既知の循環(ユーザー決定)。外す段は親の案(第342)=PENDING §2 の 3 の delivery_inbound と同じ段",
                     "配送の入荷が店の発注と配達員の行動になる段"),
    KnownCircularity("W1", STAND_IN, ("bridge:DEC-41-homeUse",),
                     "19 時に持ち物のある全員が 1 個を使う規則の出力が、廃棄 sink(W1 の欄)を直に作る",
                     "語彙に「家で使う」が入る段(11-02r §1 #8・DEC-41 の外す段=11-01p-3)", decided="11-02r/§1 #8"),
)


def classify(overlaps: Iterable[Overlap], known: Iterable[KnownCircularity] = KNOWN_CIRCULARITIES
             ) -> tuple[list[Overlap], list[tuple[Overlap, KnownCircularity]]]:
    """例外の付かない重なりを (落とす=宣言の無い重なり, 警告=宣言つきの重なりと宣言) に分ける(11-02r/§1 #6)。

    ``exempt`` の付いた重なり(``burned``/``外す``/止めた「無い」)はどちらにも入れない(今のまま通す)。
    """
    ks = tuple(known)
    fail: list[Overlap] = []
    warn: list[tuple[Overlap, KnownCircularity]] = []
    for o in overlaps:
        if o.exempt:
            continue
        hit = next((k for k in ks if k.covers(o)), None)
        if hit is None:
            fail.append(o)
        else:
            warn.append((o, hit))
    return fail, warn


def stale_declarations(overlaps: Iterable[Overlap], known: Iterable[KnownCircularity] = KNOWN_CIRCULARITIES
                       ) -> list[tuple[KnownCircularity, str]]:
    """どの重なりにも当たらない宣言の主体(宣言だけが残った=循環が解けたか主体の名が変わった)。

    例外の付いた重なりは当たりに数えない(例外で通るなら宣言は要らない)。
    """
    live = [o for o in overlaps if not o.exempt]
    out: list[tuple[KnownCircularity, str]] = []
    for k in known:
        for subj in k.subjects:
            if not any(o.pattern_id == k.pattern_id and o.system == k.system and o.subject == subj for o in live):
                out.append((k, subj))
    return out


def warning_lines(warn: Iterable[tuple[Overlap, KnownCircularity]]) -> list[str]:
    """警告の文(CI のログに出す 1 行ずつ=主体・系・行・外す段・決定)。"""
    return [f"既知の循環(警告・{k.decided}): {o.subject} の {o.system} → {o.pattern_id}。外す段: {k.remove_at}"
            f"〔{k.basis}〕" for o, k in warn]
