"""engine.experiment.form — 反実仮想の申込書 ``ExperimentForm``(第 3 期 3-3・決定 10-12 §4-5 CP5-4・探索と確認・CP14)。

申込書の欄(CP5-4 の 8 欄に、アンサンブルと事前登録の 2 欄と形式の版を足した)。**知らない欄は ``ValueError``**(入れ子の欄も
同じ)。読み口は ``from_json``・``from_dict``・``load``、書き口は ``to_json``(鍵の昇順・区切りの空白なし=決定的な並び)。

| 欄 | 中身 |
|---|---|
| ``schema`` | 形式の版(``FORM_SCHEMA``・省略可) |
| ``kind`` | ``explore``(探索)か ``confirm``(確認)。日本語の ``探索``・``確認`` も受ける |
| ``subject`` | 対象=``level``(改変の種類 L0〜L4)・``ids``(対象の番号の列=L1 は POI の番号)・``category``(POI の種別の名=申込書の値で受ける) |
| ``content`` | 改変の中身=決定の列(``{"decision": 名, …}``)。名と欄は ``DECISIONS`` の表。空の列=A/A の枝 |
| ``start`` | 始まり T0=通しの時刻のナノ秒(``core.time_consts`` の ``NS_PER_SECOND`` で数える・0=最初から) |
| ``end`` | 終わり(ナノ秒・``None``=ランの終わりまで) |
| ``notice`` | 告知=誰に(``to``=体の番号か ``staff``=対象の店の担当)・いつ(``at``・``None``=始まり)・どの道具で(``via``=1-3 の ``VIA_WORDS`` の語)。CP6 の段取りは本段では「届いた情報」の出来事まで |
| ``question`` | 問い(空でない文) |
| ``metrics`` | 比べる指標=``primary``(主 1 つ)・``secondary``(副の列)。各指標は ``id``・``path``(checkpoints の JSON の道筋)・``direction``(``greater``/``less``/``None``)・``description`` |
| ``ensemble`` | 初期状態 × モデル × 偶然の本数(``initial``・``model``=モデルの札の列・``chance``)・A/A の枝の有無(``aa``)・種の起点(``seed0``) |
| ``preregistration`` | 確認のランだけ=封印の指紋(``seal_sha256``)と申込書の登録の指紋(``registration_sha256``=``registration_digest``)。探索では ``None`` |
| ``aa_of`` | 〔検収 L4〕A/A の枝の印=元の申込書の登録の指紋(``aa()`` が置く・ふつうの申込書は ``None``)。置いた申込書は改変と告知が空。確認の A/A の枝は事前登録を引き継ぎ、``aa_of`` が事前登録の ``registration_sha256`` と同じでなければエラー(改変の中身の照合は元の申込書がする) |

コードに地名や業種名を書かない(対象は番号か申込書の値の種別名で受ける=試験 ``tests/engine/experiment`` が日本語の固有名詞の
一覧と突き合わせる)。

決定の表(``DECISIONS``): 種類ごとの水準と欄。本段で実装したのは L0(天気の日付の差し替え・祝日)と L1(営業時間・休業・催しの
告知)だけ。L2〜L4 は欄だけ(``implemented=False``=効かせる口が「宣言して未実装」として記録して続ける)。

逐次ループ宣言: なし(申込書の検査は欄の数ぶん・ランの外で 1 回)。
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from shibuya.core.time_consts import NS_PER_SECOND
from shibuya.engine.events import vocab as _V

__all__ = [
    "FORM_SCHEMA", "KINDS", "EXPLORE", "CONFIRM", "LEVELS", "DECISIONS", "DecisionSpec", "FORM_FIELDS",
    "ExperimentForm", "canonical_json", "sha256_hex", "NOTICE_STAFF",
]

FORM_SCHEMA: Final[str] = "shibuya.engine.experiment/form/1"
EXPLORE: Final[str] = "explore"
CONFIRM: Final[str] = "confirm"
KINDS: Final[tuple[str, ...]] = (EXPLORE, CONFIRM)
_KIND_ALIASES: Final[Mapping[str, str]] = MappingProxyType({"探索": EXPLORE, "確認": CONFIRM})
LEVELS: Final[tuple[str, ...]] = ("L0", "L1", "L2", "L3", "L4")
#: 告知の宛先の印「対象の店の担当」(体の番号の代わりに書ける唯一の語)。
NOTICE_STAFF: Final[str] = "staff"

FORM_FIELDS: Final[tuple[str, ...]] = (
    "schema", "kind", "subject", "content", "start", "end", "notice", "question", "metrics", "ensemble",
    "preregistration", "aa_of",
)
_SUBJECT_FIELDS: Final[tuple[str, ...]] = ("level", "ids", "category")
_NOTICE_FIELDS: Final[tuple[str, ...]] = ("to", "at", "via")
_METRICS_FIELDS: Final[tuple[str, ...]] = ("primary", "secondary")
_METRIC_FIELDS: Final[tuple[str, ...]] = ("id", "path", "direction", "description")
_DIRECTIONS: Final[tuple[Any, ...]] = (None, "greater", "less")
_ENSEMBLE_FIELDS: Final[tuple[str, ...]] = ("initial", "model", "chance", "aa", "seed0")
_PREREG_FIELDS: Final[tuple[str, ...]] = ("seal_sha256", "registration_sha256")
_HEX64_LEN: Final[int] = 64


@dataclass(frozen=True)
class DecisionSpec:
    """決定の種類 1 つ(水準・欄の名と型の検査・実装したか)。``params`` は欄の名 → (検査の名, 必須か, 既定)。"""

    level: str
    params: Mapping[str, tuple[str, bool, Any]]
    implemented: bool
    note: str


def _spec(level: str, implemented: bool, note: str, **params: tuple[str, bool, Any]) -> DecisionSpec:
    return DecisionSpec(level=level, params=MappingProxyType(dict(params)), implemented=implemented, note=note)


#: 決定の種類の表(名 → 水準・欄)。本段の実装は L0 と L1 だけ(残りは欄だけ=宣言して未実装)。
DECISIONS: Final[Mapping[str, DecisionSpec]] = MappingProxyType({
    # ---- L0 環境(天気・日付・祝日)。天気は自然(決めた人はいない)・祝日は社会の決まり(暦) ----
    "weather_date": _spec("L0", True, "その日の天気を W13 の別の日(再生日)の天気に差し替える",
                          replay_date=("date", True, None)),
    "holiday": _spec("L0", True, "暦の日付を祝日にする(on=True)か祝日から外す(on=False)",
                     date=("date", True, None), on=("bool", False, True), name=("str", False, "休日")),
    # ---- L1 制度と運営(実行は世界の中の人=CP6) ----
    "opening_hours": _spec("L1", True, "対象の店の営業時間の表を変える(開閉は担当の従業者が行う)",
                           hours=("hours", True, None)),
    "closure": _spec("L1", True, "対象の店を休業にする(営業時間の表を空にする)"),
    "event": _spec("L1", True, "催しの決定(本段では告知の「届いた情報」の出来事まで)",
                   at=("ns", False, None), until=("ns", False, None)),
    # ---- L2〜L4(欄だけ・宣言して未実装) ----
    "passage": _spec("L2", False, "入口や通路の開閉(空間の段 1〜2 の後)", open=("bool", False, False)),
    "barrier": _spec("L2", False, "仮の柵・家具の配置・行列の場所(空間の段 1〜2 の後)"),
    "construction": _spec("L3", False, "大きな物理(開始前に作り込むか、工事を作業員の仕事にする=§1-1)"),
    "fare": _spec("L4", False, "運賃(経済の段の後)", amount_yen=("int", True, None)),
    "service_suspension": _spec("L4", False, "運休(交通の段の後)"),
    "new_store": _spec("L4", False, "新しい店(権利台帳の段の後)"),
    "visitors": _spec("L4", False, "来る人の構成(人口の段の後)", scale=("float", True, None)),
})


# ================================================================ 正準の形と指紋
def _thaw(v: Any) -> Any:
    if isinstance(v, Mapping):
        return {str(k): _thaw(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_thaw(x) for x in v]
    return v


def _freeze(v: Any) -> Any:
    if isinstance(v, Mapping):
        return MappingProxyType({str(k): _freeze(x) for k, x in v.items()})
    if isinstance(v, (list, tuple)):
        return tuple(_freeze(x) for x in v)
    return v


def canonical_json(v: Any) -> str:
    """決定的な JSON(鍵の昇順・区切りの空白なし・ASCII の外もそのまま)。"""
    return json.dumps(_thaw(v), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_hex(v: Any) -> str:
    """``canonical_json`` の UTF-8 の sha256(16 進 64 字)。"""
    return hashlib.sha256(canonical_json(v).encode("utf-8")).hexdigest()


# ================================================================ 欄の検査
def _unknown(where: str, d: Mapping[str, Any], allowed: tuple[str, ...]) -> None:
    extra = sorted(set(d) - set(allowed))
    if extra:
        raise ValueError(f"申込書の {where} に知らない欄 {extra}(欄は {list(allowed)})")


def _mapping(where: str, v: Any) -> Mapping[str, Any]:
    if not isinstance(v, Mapping):
        raise ValueError(f"申込書の {where} は辞書(いま {type(v).__name__})")
    return v


def _int(where: str, v: Any, *, lo: int | None = 0) -> int:
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"申込書の {where} は整数(いま {v!r})")
    if lo is not None and v < lo:
        raise ValueError(f"申込書の {where} は {lo} 以上(いま {v})")
    return int(v)


def _str(where: str, v: Any) -> str:
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"申込書の {where} は空でない文字列(いま {v!r})")
    return v


def _date(where: str, v: Any) -> str:
    s = _str(where, v)
    try:
        d = _dt.date.fromisoformat(s)
    except ValueError:
        raise ValueError(f"申込書の {where} は YYYY-MM-DD の日付(いま {v!r})") from None
    return d.isoformat()


def _hours(where: str, v: Any) -> tuple[tuple[int, int], ...]:
    """営業時間の区間の列 ``[[開く分, 閉じる分], …]``(日の 0 時からの分・閉じる分は翌日の分まで=W7 の書き方と同じ)。"""
    from shibuya.core.time_consts import MINUTES_PER_DAY

    if not isinstance(v, (list, tuple)):
        raise ValueError(f"申込書の {where} は [[開く分, 閉じる分], …] の列")
    out = []
    for k, iv in enumerate(v):
        if not isinstance(iv, (list, tuple)) or len(iv) != 2:
            raise ValueError(f"申込書の {where}[{k}] は [開く分, 閉じる分]")
        s, e = _int(f"{where}[{k}][0]", iv[0]), _int(f"{where}[{k}][1]", iv[1])
        if not (s < e <= 2 * MINUTES_PER_DAY) or s >= MINUTES_PER_DAY:
            raise ValueError(f"申込書の {where}[{k}] は 0 ≤ 開く < 1 日の分・開く < 閉じる ≤ 2 日の分(いま {iv!r})")
        out.append((s, e))
    return tuple(out)


def _check_param(where: str, kind: str, v: Any) -> Any:
    if kind == "date":
        return _date(where, v)
    if kind == "bool":
        if not isinstance(v, bool):
            raise ValueError(f"申込書の {where} は真偽(いま {v!r})")
        return v
    if kind == "str":
        return _str(where, v)
    if kind == "int":
        return _int(where, v, lo=None)
    if kind == "ns":
        return _int(where, v)
    if kind == "float":
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            raise ValueError(f"申込書の {where} は有限の数(いま {v!r})")
        return float(v)
    if kind == "hours":
        return [list(x) for x in _hours(where, v)]
    raise AssertionError(kind)


def _decision(k: int, v: Any, level: str) -> dict[str, Any]:
    d = _mapping(f"content[{k}]", v)
    name = d.get("decision")
    if name not in DECISIONS:
        raise ValueError(f"申込書の content[{k}].decision は {sorted(DECISIONS)} のどれか(いま {name!r})")
    spec = DECISIONS[name]
    _unknown(f"content[{k}]", d, ("decision",) + tuple(spec.params))
    if spec.level != level:
        raise ValueError(f"申込書の content[{k}].decision={name!r} は {spec.level}(subject.level は {level})")
    out: dict[str, Any] = {"decision": name}
    for p, (pk, required, default) in spec.params.items():
        if p in d and d[p] is not None:
            out[p] = _check_param(f"content[{k}].{p}", pk, d[p])
        elif required:
            raise ValueError(f"申込書の content[{k}].{p} は必須({name})")
        else:
            out[p] = default
    if name == "event" and out.get("at") is not None and out.get("until") is not None and out["until"] <= out["at"]:
        raise ValueError(f"申込書の content[{k}] の until は at より後")
    return out


def _subject(v: Any) -> dict[str, Any]:
    d = _mapping("subject", v)
    _unknown("subject", d, _SUBJECT_FIELDS)
    level = d.get("level")
    if level not in LEVELS:
        raise ValueError(f"申込書の subject.level は {LEVELS} のどれか(いま {level!r})")
    ids_raw = d.get("ids", ())
    if not isinstance(ids_raw, (list, tuple)):
        raise ValueError("申込書の subject.ids は番号の列")
    ids = sorted({_int(f"subject.ids[{k}]", x) for k, x in enumerate(ids_raw)})
    cat = d.get("category")
    if cat is not None:
        cat = _str("subject.category", cat)
    if level == "L0" and (ids or cat is not None):
        raise ValueError("申込書の subject: L0(環境)は対象の番号と種別を持たない")
    return {"level": level, "ids": ids, "category": cat}


def _notice(v: Any, start: int, end: int | None) -> dict[str, Any] | None:
    if v is None:
        return None
    d = _mapping("notice", v)
    _unknown("notice", d, _NOTICE_FIELDS)
    to_raw = d.get("to")
    if not isinstance(to_raw, (list, tuple)) or not to_raw:
        raise ValueError("申込書の notice.to は宛先の列(体の番号か 'staff')で空でない")
    to: list[Any] = []
    for k, x in enumerate(to_raw):
        if x == NOTICE_STAFF:
            to.append(NOTICE_STAFF)
        else:
            to.append(_int(f"notice.to[{k}]", x))
    ints = sorted({x for x in to if isinstance(x, int)})
    to_c: list[Any] = ([NOTICE_STAFF] if NOTICE_STAFF in to else []) + ints
    at = d.get("at")
    if at is not None:
        at = _int("notice.at", at)
        if at < start:
            raise ValueError("申込書の notice.at は start より後(決定の前に告知できない)")
        if end is not None and at >= end:
            raise ValueError("申込書の notice.at は end より前")
    via = d.get("via", "メッセージ")
    if via not in _V.VIA_WORDS or via == _V.VIA_NONE:
        raise ValueError(f"申込書の notice.via は {[w for w in _V.VIA_WORDS if w != _V.VIA_NONE]} のどれか(いま {via!r})")
    return {"to": to_c, "at": at, "via": via}


def _metric(where: str, v: Any) -> dict[str, Any]:
    d = _mapping(where, v)
    _unknown(where, d, _METRIC_FIELDS)
    direction = d.get("direction")
    if direction not in _DIRECTIONS:
        raise ValueError(f"申込書の {where}.direction は {list(_DIRECTIONS)} のどれか(いま {direction!r})")
    desc = d.get("description")
    return {"id": _str(f"{where}.id", d.get("id")), "path": _str(f"{where}.path", d.get("path")),
            "direction": direction, "description": None if desc is None else _str(f"{where}.description", desc)}


def _metrics(v: Any) -> dict[str, Any]:
    d = _mapping("metrics", v)
    _unknown("metrics", d, _METRICS_FIELDS)
    if "primary" not in d:
        raise ValueError("申込書の metrics.primary(主の指標 1 つ)は必須")
    sec_raw = d.get("secondary", ())
    if not isinstance(sec_raw, (list, tuple)):
        raise ValueError("申込書の metrics.secondary は列")
    prim = _metric("metrics.primary", d["primary"])
    sec = [_metric(f"metrics.secondary[{k}]", x) for k, x in enumerate(sec_raw)]
    ids = [prim["id"]] + [m["id"] for m in sec]
    if len(set(ids)) != len(ids):
        raise ValueError(f"申込書の metrics の id が重なる: {ids}")
    return {"primary": prim, "secondary": sec}


def _ensemble(v: Any) -> dict[str, Any]:
    d = _mapping("ensemble", v)
    _unknown("ensemble", d, _ENSEMBLE_FIELDS)
    model = d.get("model", ("mock",))
    if not isinstance(model, (list, tuple)) or not model:
        raise ValueError("申込書の ensemble.model はモデルの札の列で空でない")
    models = [_str(f"ensemble.model[{k}]", x) for k, x in enumerate(model)]
    if len(set(models)) != len(models):
        raise ValueError("申込書の ensemble.model の札が重なる")
    aa = d.get("aa", True)
    if not isinstance(aa, bool):
        raise ValueError("申込書の ensemble.aa は真偽")
    return {"initial": _int("ensemble.initial", d.get("initial", 1), lo=1), "model": models,
            "chance": _int("ensemble.chance", d.get("chance", 1), lo=1), "aa": aa,
            "seed0": _int("ensemble.seed0", d.get("seed0", 1), lo=None)}


def _prereg(v: Any) -> dict[str, Any] | None:
    if v is None:
        return None
    d = _mapping("preregistration", v)
    _unknown("preregistration", d, _PREREG_FIELDS)
    out = {}
    for k in _PREREG_FIELDS:
        s = _str(f"preregistration.{k}", d.get(k))
        if len(s) != _HEX64_LEN or any(c not in "0123456789abcdef" for c in s):
            raise ValueError(f"申込書の preregistration.{k} は 16 進 64 字(sha256)")
        out[k] = s
    return out


# ================================================================ 申込書
def _normalize(d: Any) -> dict[str, Any]:
    """辞書 → 正準の辞書(全部の欄の検査・既定を埋める)。知らない欄・型の誤り・矛盾は ``ValueError``。"""
    d = _mapping("(全体)", d)
    _unknown("(全体)", d, FORM_FIELDS)
    schema = d.get("schema", FORM_SCHEMA)
    if schema != FORM_SCHEMA:
        raise ValueError(f"申込書の schema は {FORM_SCHEMA!r}(いま {schema!r})")
    kind_raw = d.get("kind")
    kind = _KIND_ALIASES.get(kind_raw, kind_raw) if isinstance(kind_raw, str) else kind_raw
    if kind not in KINDS:
        raise ValueError(f"申込書の kind は {KINDS}(探索/確認)のどれか(いま {kind_raw!r})")
    subject = _subject(d.get("subject"))
    content_raw = d.get("content", ())
    if not isinstance(content_raw, (list, tuple)):
        raise ValueError("申込書の content は決定の列(空の列=A/A の枝)")
    content = [_decision(k, x, subject["level"]) for k, x in enumerate(content_raw)]
    start = _int("start", d.get("start", 0))
    end = d.get("end")
    if end is not None:
        end = _int("end", end)
        if end <= start:
            raise ValueError("申込書の end は start より後")
    notice = _notice(d.get("notice"), start, end)
    if notice is not None and NOTICE_STAFF in notice["to"] and subject["level"] == "L0":
        raise ValueError("申込書の notice.to の 'staff' は対象の店のある水準(L1 以上)だけ")
    aa_of = d.get("aa_of")
    if aa_of is not None:
        aa_of = _str("aa_of", aa_of)
        if len(aa_of) != _HEX64_LEN or any(c not in "0123456789abcdef" for c in aa_of):
            raise ValueError("申込書の aa_of は 16 進 64 字(元の申込書の登録の指紋)")
        if content or notice is not None:
            raise ValueError("申込書の aa_of(A/A の枝の印)を置いた申込書は改変と告知が空")
    out = {
        "schema": FORM_SCHEMA, "kind": kind, "subject": subject, "content": content, "start": start, "end": end,
        "notice": notice, "question": _str("question", d.get("question")), "metrics": _metrics(d.get("metrics")),
        "ensemble": _ensemble(d.get("ensemble", {})), "preregistration": _prereg(d.get("preregistration")),
        "aa_of": aa_of,
    }
    prereg = out["preregistration"]
    if kind == EXPLORE and prereg is not None:
        raise ValueError("申込書: 事前登録は確認のランだけ(探索は事前登録なしで傾向を見る)")
    if kind == CONFIRM:
        if prereg is None:
            raise ValueError("申込書: 確認のランは事前登録(preregistration)が要る")
        if aa_of is not None:
            if prereg["registration_sha256"] != aa_of:
                raise ValueError("申込書: 確認の A/A の枝の aa_of が事前登録の指紋と違う")
        elif prereg["registration_sha256"] != _registration_of(out):
            raise ValueError("申込書: 事前登録の指紋(registration_sha256)が申込書と指標の定義に合わない")
    return out


def _registration_of(n: Mapping[str, Any]) -> str:
    """正準の辞書の登録の指紋(事前登録の欄を除く)。"""
    d = dict(n)
    d.pop("preregistration", None)
    return sha256_hex(d)


@dataclass(frozen=True)
class ExperimentForm:
    """反実仮想の申込書(凍結・入れ子も読み取り専用)。作るのは ``from_dict``・``from_json``・``load``。

    〔検収 L3〕直に作っても ``__post_init__`` が同じ検査を通す(正準の形でない・矛盾は ``ValueError``)。
    """

    kind: str
    subject: Mapping[str, Any]
    content: tuple[Mapping[str, Any], ...]
    start: int
    end: int | None
    notice: Mapping[str, Any] | None
    question: str
    metrics: Mapping[str, Any]
    ensemble: Mapping[str, Any]
    preregistration: Mapping[str, Any] | None
    aa_of: str | None = None

    def __post_init__(self) -> None:
        mine = self.to_dict()
        if canonical_json(_normalize(mine)) != canonical_json(mine):
            raise ValueError("申込書の欄が正準の形でない(from_dict で作る)")

    # ------------------------------------------------------------------ 読み口
    @classmethod
    def from_dict(cls, d: Any) -> "ExperimentForm":
        """辞書 → 申込書(知らない欄・型の誤り・矛盾は ``ValueError``)。"""
        n = _normalize(d)
        return cls(kind=n["kind"], subject=_freeze(n["subject"]), content=_freeze(n["content"]), start=n["start"],
                   end=n["end"], notice=_freeze(n["notice"]), question=n["question"], metrics=_freeze(n["metrics"]),
                   ensemble=_freeze(n["ensemble"]), preregistration=_freeze(n["preregistration"]), aa_of=n["aa_of"])

    @classmethod
    def from_json(cls, text: str) -> "ExperimentForm":
        try:
            d = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"申込書の JSON が読めない: {e}") from None
        return cls.from_dict(d)

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentForm":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))

    # ------------------------------------------------------------------ 書き口
    def to_dict(self) -> dict[str, Any]:
        """正準の辞書(全部の欄・既定を埋めた形=同じ申込書は同じ辞書)。"""
        return {
            "schema": FORM_SCHEMA, "kind": self.kind, "subject": _thaw(self.subject),
            "content": _thaw(self.content), "start": int(self.start), "end": self.end,
            "notice": _thaw(self.notice), "question": self.question, "metrics": _thaw(self.metrics),
            "ensemble": _thaw(self.ensemble), "preregistration": _thaw(self.preregistration), "aa_of": self.aa_of,
        }

    def to_json(self) -> str:
        """決定的な JSON(``canonical_json``)。``from_json(to_json())`` は同じ申込書。"""
        return canonical_json(self.to_dict())

    def sha256(self) -> str:
        """申込書の指紋(``to_json`` の sha256)。manifest の ``experiment.form_sha256``。"""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def registration_digest(self) -> str:
        """CP14 の登録の指紋=申込書から事前登録の欄を除いた正準の形(問い・指標の定義を含む)の sha256。"""
        return _registration_of(self.to_dict())

    # ------------------------------------------------------------------ 読む便利
    @property
    def level(self) -> str:
        return str(self.subject["level"])

    @property
    def is_aa(self) -> bool:
        """改変が空(A/A の枝)。"""
        return len(self.content) == 0

    def aa(self) -> "ExperimentForm":
        """同じ申込書で改変だけを空にした A/A の枝(告知も外す=何も世界に入れない)。〔検収 L4〕元の申込書の登録の指紋を
        ``aa_of`` に残す(確認の申込書は事前登録を引き継ぐ=JSON の往復で通る)。A/A の枝の A/A は自分のまま。"""
        if self.aa_of is not None:
            return self
        return replace(self, content=(), notice=None, aa_of=self.registration_digest())

    def start_step(self, step_seconds: int) -> int:
        """始まり T0 の刻みの番号(T0 の時刻以後の最初の刻み=切り上げ)。"""
        w = int(step_seconds) * NS_PER_SECOND
        return -(-int(self.start) // w)

    def end_step(self, step_seconds: int) -> int | None:
        if self.end is None:
            return None
        w = int(step_seconds) * NS_PER_SECOND
        return -(-int(self.end) // w)
