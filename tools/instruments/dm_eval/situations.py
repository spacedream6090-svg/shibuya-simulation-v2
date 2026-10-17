# -*- coding: utf-8 -*-
"""dm_eval.situations — 状況の読み口(DM4)と候補の口(DM-0)(第 6 期 6-1 の器・読むだけ)。

状況の読み口
    1-10 の評価セット(``data/evalset/evalset-1-10/situations.jsonl``・340 件・md5 は下の定数)を読み、1 件ごとに
    描画のブロック(B0=``summary.json`` の ``b0_texts``・B1〜B4b=``input_text`` を行の頭の ``[Bx …]`` で分けた物)を持つ。
    DM4 の短い版(判断モデル)と長い版(LLM)は **``engine.decision.port.compose`` 1 つ**で作る(共通部分 B0〜B4b を前・
    人ごとの部分 → 提示 → 長い版だけ指示)。B5・B6 は 1-10 の材料に無い(1-10 の限界 §5 の 1)=空欄の宣言(``missing``)。
    1-10 の材料では人ごとの部分が無いので、短い版と長い版の差は長い版の末尾の指示の 1 行だけになる。

    長さの腕(DM4「300 と 1,000 を腕で比べる」): ``t300`` と ``t1000``。目安は文字数で宣言する(``CHARS_PER_TOKEN``)。
    tokenizer は使わない=トークン数は後で測る欄(``Rendered.tokens`` は空)。
    - ``t1000``=DM4 (b)「ブロックをそのまま流用する」: 手元のブロックを全部(B0〜B4b)。
    - ``t300``=DM4 (a) の代わり: 全員に同じ前置き B0(憲法・役割知識・出力規約)を外す。DM4 (a) の「人ごとの短い
      特徴量」の描画は材料にも engine にも無い(報告の「engine の口の不足」)ので、ここでは文を作り足さず、削るのも
      ブロック単位だけにする(どの事実を残すかを器が選ばない)。目安を超えた件は ``over_budget`` に数える。

    言語の欄(§4-8): ``lang`` は材料の言語(今は全件 ``ja``)。住人の第一言語 ``first_language`` は空欄の宣言
    (材料に無い=6-1 の空欄として引き継ぐ・1-10 の親の注 §9)。

    DM4「数字はお金と時刻だけ」の計器: 状況の部分(提示の番号を除く)の数字の並びのうち、時刻(時・分・時間・:)と
    お金(円・万円・¥)に続かない物の数(``numbers_outside_money_time``)。描画を直すのは engine の側(器は数えるだけ)。

候補の口(DM-0 の 5 つの源を**記録から**付ける)
    ``engine.decision.sources.build_candidates`` に 1-10 の状況から作った ``DecisionContext`` を渡す(1 つの仕組み)。
    1. 続ける(``continue``): その版の安全弁の語(語彙 v1 の「待機」)。
    2. 近い予定(``plan``): **空欄**(B6 の起床の理由と予定が材料に無い)。
    3. 本人の経験(``experience``): 記憶(B5)が材料に無いので、**テープの記録**=同じテープの同じ体の、この状況より前の
       呼(刻みが小さい・繰り延べでない)の応答の行為の語を新しい順に最大 ``EXPERIENCE_K`` 呼(本人の経験の代わり)。
    4. 周りが示すできること(``affordance``): 1-10 の事実(``facts``)から engine の規則
       (``engine.decision.layer.DecisionLayer.affordance_words``)の形で: 移動=いつでも・乗車=駅の手がかり・購入=店の
       手がかり。会話(B5 の近くの人)・就寝(自宅のセル)・断る(B6 の招待)は**空欄**(材料に無い)。
    5. よく考える(``deliberate``): 1 つ。
    どの源も出さなかった語彙 v1 の残りは J0 と同じ印 ``vocab``(つなぎ=台帳 ``DOC-j0-candidates-vocab``)。候補は毎回
    12 語+よく考える=13。並びは ``engine.decision.port.present``(乱数の鍵=種と状況の id)で入れ替えて記録する
    (R-108 の対策 1)。並べ替え試験の N 通りは ``present`` の並びの巡回(``orders``)。

expedient(器の宣言・未リサーチ)
    - ``CHARS_PER_TOKEN`` = 1.0(長さの腕の目安の文字数=トークン数 × 1.0。tokenizer で後で測る)。
    - 長さの腕 ``t300`` は B0 を外すだけ(上の説明)。
    - 本人の経験の代わり=同じテープの同じ体の前の呼の行為の語・最大 3 呼(engine の想起の行の上限 3 に合わせた)。
    - 周りが示すできることの手がかり=1-10 の ``facts`` の ``station_word_or_band``(乗車)と ``shop_word``(購入)。
      営業中かは材料から読めない(看板の文を解釈しない)。
    - 巡回の位置=``k × n // N``(k=0〜N−1・n=候補の数・N=並びの数)。
逐次ループ宣言: 状況の数(340)× 並びの数(既定 4)× 候補の数(13)。テープは状況のあるテープ(32 本)ごとに 1 回、
    65,536 行ずつ読む(体で絞る=pyarrow の配列演算)。
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from typing import Any, Final, Iterable, Mapping, Sequence

import dm_eval  # noqa: F401  (src と tools/instruments を sys.path に足す)
from read_guard import GAUGE_DENY_TOKENS, SealedPathError, deny_hit
from shibuya.core.rng import stream
from shibuya.core.time_consts import MINUTES_PER_HOUR, NS_PER_SECOND, SECONDS_PER_MINUTE
from shibuya.engine.decision.port import LENGTHS, Candidate, DecisionContext, compose, present
from shibuya.engine.decision.sources import build_candidates
from shibuya.llm.contract import cross_action_words, safe_action_word
from shibuya.llm.parser import parse_two_line

REPO: Final[Path] = dm_eval.REPO
EVALSET_DIR: Final[Path] = REPO / "data" / "evalset" / "evalset-1-10"
SITUATIONS_NAME: Final[str] = "situations.jsonl"
SUMMARY_NAME: Final[str] = "summary.json"
#: 1-10 の記録 §0・§4 の md5(親の注 §9 で data/ の下へ移した 2 本)。
SITUATIONS_MD5: Final[str] = "d4d0cf61e64a2fd0a400d84f625b3335"
SUMMARY_MD5: Final[str] = "46e8d0e955e6b05faf7ad29f8d507794"
N_SITUATIONS: Final[int] = 340

#: 材料の語彙の版(1-10 の母集団は B0 が語彙 v1 のテープだけ=仮採用 1)。
VOCAB_VERSION: Final[str] = "v1"
VOCAB: Final[tuple[str, ...]] = cross_action_words(VOCAB_VERSION)
CONTINUE_WORD: Final[str] = safe_action_word(VOCAB_VERSION)
_CODE_OF: Final[Mapping[str, int]] = MappingProxyType({w: i for i, w in enumerate(VOCAB)})
_WORD_OF: Final[Mapping[int, str]] = MappingProxyType({i: w for i, w in enumerate(VOCAB)})

#: 描画のブロックの並び(共通 B0〜B4b → 人ごと B5・B6=``port.compose`` と同じ並び)。
BLOCK_ORDER: Final[tuple[str, ...]] = ("B0", "B1", "B2", "B3", "B4", "B4b", "B5", "B6")
COMMON_BLOCKS: Final[tuple[str, ...]] = BLOCK_ORDER[:6]
#: 人ごとの部分(短い版=B6・長い版=B5+B6=``port.compose`` と同じ分け方)。
INDIVIDUAL_BLOCKS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({"short": ("B6",), "long": ("B5", "B6")})
_BLOCK_HEAD: Final[re.Pattern[str]] = re.compile(r"^\[(B\d+b?)[ \]]")

#: 長さの腕(DM4)→ 目標のトークン数。
LENGTH_ARMS: Final[Mapping[str, int]] = MappingProxyType({"t300": 300, "t1000": 1000})
#: 長さの腕 → 外すブロック(上の説明・expedient)。
ARM_DROP_BLOCKS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({"t300": ("B0",), "t1000": ()})
#: 目安の文字数 = トークン数 × これ(expedient・未計測=tokenizer で後で測る)。
CHARS_PER_TOKEN: Final[float] = 1.0

#: 本人の経験の代わりに取る前の呼の数(expedient)。
EXPERIENCE_K: Final[int] = 3
#: 並べ替えの乱数の用途名(エンジンの ``decision.present`` とは別の名)。
PRESENT_DOMAIN: Final[str] = "dm_eval.present"
#: 既定の種と並びの数(R-108 §1-4 の巡回 × 4・1-10 の記録 §2-5)。
DEFAULT_SEED: Final[str] = "dm61"
DEFAULT_N_ORDERS: Final[int] = 4

#: 空欄の宣言(材料に無い源と欄)。
BLANK_SOURCES: Final[Mapping[str, str]] = MappingProxyType({
    "plan": "近い予定=B6(起床の理由と予定)が材料に無い",
    "affordance:会話": "近くの人=B5 の近接行が材料に無い",
    "affordance:就寝": "自宅のセル=材料は全件セルの路上(1-10 §5 の 2)",
    "affordance:断る": "招待=B6 が材料に無い",
    "experience:memory": "記憶(B5)が材料に無い=テープの前の呼で代える",
})

_TAPE_COLUMNS: Final[tuple[str, ...]] = ("agent_id", "tick", "deferred", "response")
_BATCH_ROWS: Final[int] = 1 << 16


class EvalsetMissing(FileNotFoundError):
    """評価セットのファイルが無い(data/ は gitignore の下)。"""


def _guarded(path: Path) -> Path:
    """封印・検証側・〔灰〕の語のある道筋は開く前に落とす(``read_guard.deny_hit``)。"""
    hit = deny_hit(path, GAUGE_DENY_TOKENS)
    if hit:
        raise SealedPathError(f"dm_eval は {hit!r} を含む道筋を読まない")
    return path


def _read_bytes(path: Path) -> bytes:
    p = _guarded(Path(path))
    if not p.is_file():
        raise EvalsetMissing(f"評価セットのファイルが無い: {p.name}")
    return p.read_bytes()


def md5_of(raw: bytes) -> str:
    return hashlib.md5(raw).hexdigest()


# ---------------------------------------------------------------------------------------------- 状況
@dataclass(frozen=True)
class Situation:
    """評価セットの 1 件(読むだけ)。``tape_output`` はテープの応答の本文(記録に写さない・テープの当て口だけが読む)。"""

    sid: str
    blocks: Mapping[str, str]
    lang: str = "ja"
    #: 住人の第一言語(§4-8)。材料に無い=空欄の宣言。
    first_language: str | None = None
    missing: tuple[str, ...] = ("B5", "B6")
    facts: Mapping[str, Any] = field(default_factory=dict)
    strata: Mapping[str, Any] = field(default_factory=dict)
    agent_id: int = -1
    #: テープの刻み(呼の時刻)。
    step: int = -1
    wake_class: int = -1
    call_id: str = ""
    tape: str = ""
    tape_output: str = field(default="", repr=False)

    def __post_init__(self) -> None:
        bad = [b for b in self.blocks if b not in BLOCK_ORDER]
        if bad:
            raise ValueError(f"知らないブロック {bad}(並び {BLOCK_ORDER})")
        object.__setattr__(self, "blocks", MappingProxyType(dict(self.blocks)))
        object.__setattr__(self, "facts", MappingProxyType(dict(self.facts)))
        object.__setattr__(self, "strata", MappingProxyType(dict(self.strata)))


def split_blocks(input_text: str) -> dict[str, str]:
    """``input_text``(B1〜B4b を改行で連結)→ ブロックごとの文(行の頭の ``[Bx …]`` で分ける)。

    頭の無い行は直前のブロックの続き。ブロックは連続して並び、``BLOCK_ORDER`` の順であること(違えば ``ValueError``)。
    ブロックの文を ``BLOCK_ORDER`` の順に改行で連結すると ``input_text`` に戻る。
    """
    out: dict[str, list[str]] = {}
    cur: str | None = None
    for line in str(input_text).split("\n"):
        m = _BLOCK_HEAD.match(line)
        if m:
            b = m.group(1)
            if b != cur:
                if b in out:
                    raise ValueError(f"ブロック {b} が離れて 2 回出る")
                if b not in BLOCK_ORDER:
                    raise ValueError(f"知らないブロック {b}")
                out[b] = []
                cur = b
        elif cur is None:
            raise ValueError("最初の行にブロックの頭が無い")
        out[cur].append(line)
    order = [b for b in out]
    if order != [b for b in BLOCK_ORDER if b in out]:
        raise ValueError(f"ブロックの並びが違う: {order}")
    return {b: "\n".join(lines) for b, lines in out.items()}


def situation_from_row(row: Mapping[str, Any], b0_texts: Mapping[str, str]) -> Situation:
    """``situations.jsonl`` の 1 行と B0 の本文の表 → ``Situation``。"""
    blocks = split_blocks(str(row["input_text"]))
    b0 = b0_texts.get(str(row.get("b0_id", "")))
    if b0 is not None:
        blocks = {"B0": str(b0), **blocks}
    return Situation(
        sid=str(row["sid"]), blocks=blocks, lang=str(row.get("lang", "ja")), first_language=None,
        missing=tuple(str(x) for x in row.get("input_missing", ("B5", "B6"))),
        facts=dict(row.get("facts") or {}), strata=dict(row.get("strata") or {}),
        agent_id=int(row.get("agent_id", -1)), step=int(row.get("tick", -1)),
        wake_class=int(row.get("wake_class", -1)), call_id=str(row.get("call_id", "")),
        tape=str(row.get("tape", "")), tape_output=str(row.get("output", "")),
    )


def load_situations(directory: Path | None = None, *, verify_md5: bool = True) -> list[Situation]:
    """1-10 の 340 件を読む(並びはファイルの並び=鍵の昇順)。md5 が記録と違えば ``ValueError``。"""
    d = Path(directory) if directory is not None else EVALSET_DIR
    raw = _read_bytes(d / SITUATIONS_NAME)
    sraw = _read_bytes(d / SUMMARY_NAME)
    if verify_md5 and (md5_of(raw) != SITUATIONS_MD5 or md5_of(sraw) != SUMMARY_MD5):
        raise ValueError("評価セットの md5 が 1-10 の記録と違う")
    b0_texts = json.loads(sraw.decode("utf-8"))["b0_texts"]
    rows = [json.loads(line) for line in raw.decode("utf-8").split("\n") if line.strip()]
    return [situation_from_row(r, b0_texts) for r in rows]


def file_md5(path: Path, *, chunk: int = 1 << 24) -> str:
    """ファイルの md5(16 MiB ずつ読む・封印の道筋は開く前に落とす)。"""
    p = _guarded(Path(path))
    h = hashlib.md5()
    with io.FileIO(str(p), "r") as fh:
        while True:
            b = fh.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def verify_tape_md5(situations: Sequence[Situation], *, root: Path | None = None,
                    directory: Path | None = None) -> dict[str, Any]:
    """状況のあるテープの ``calls.parquet`` の md5 を 1-10 の ``summary.json`` の表(``md5_calls``)と照らす。"""
    base = Path(root) if root is not None else REPO
    d = Path(directory) if directory is not None else EVALSET_DIR
    table = {str(t["tape"]): str(t.get("md5_calls", "")) for t in
             json.loads(_read_bytes(d / SUMMARY_NAME).decode("utf-8"))["tapes"]}
    tapes = sorted({s.tape for s in situations})
    mismatch = []
    for t in tapes:  # 逐次ループ宣言: テープの数(32)
        path = base / t / "calls.parquet"
        if t not in table or not path.is_file() or file_md5(path) != table[t]:
            mismatch.append(t)
    return {"n": len(tapes), "ok": not mismatch, "mismatch": mismatch, "basis": "1-10 summary.json の tapes[].md5_calls"}


# ---------------------------------------------------------------------------------------------- 描画(DM4)
_NUM: Final[re.Pattern[str]] = re.compile(r"[0-9０-９]+(?:[.,][0-9０-９]+)?")
_TIME_AFTER: Final[tuple[str, ...]] = ("時", "分", ":", "：")
_MONEY_AFTER: Final[tuple[str, ...]] = ("円", "万円", "千円")
_MONEY_BEFORE: Final[tuple[str, ...]] = ("¥", "￥")
#: 描画のブロックの印(``[B4b 近景]`` など=文の形の印で、状況の中身ではない)。数字の計器の前に外す。
_BLOCK_TAG: Final[re.Pattern[str]] = re.compile(r"\[B\d+b?(?: [^\]\n]*)?\]")


def numbers_outside_money_time(text: str) -> int:
    """数字の並びのうち、時刻(時・分・時間・:)とお金(円・万円・千円・¥)に続かない物の数(DM4 の計器)。

    ブロックの印 ``[Bx …]`` の数字は数えない(文の形の印)。
    """
    text = _BLOCK_TAG.sub("", str(text))
    n = 0
    for m in _NUM.finditer(text):
        after = text[m.end():m.end() + 2]
        before = text[max(0, m.start() - 1):m.start()]
        if after.startswith(_TIME_AFTER) or after.startswith(_MONEY_AFTER) or before in _MONEY_BEFORE:
            continue
        n += 1
    return n


@dataclass(frozen=True)
class Rendered:
    """DM4 の 1 つの文と長さの欄(``tokens`` は後で測る欄=空)。"""

    text: str
    length: str
    arm: str
    chars: int
    common_chars: int
    target_tokens: int
    budget_chars: int
    over_budget: bool
    numbers_outside_money_time: int
    tokens: int | None = None


def arm_blocks(situation: Situation, arm: str) -> dict[str, str]:
    """長さの腕で使うブロック(``ARM_DROP_BLOCKS`` を外す・並びは ``BLOCK_ORDER``)。"""
    if arm not in LENGTH_ARMS:
        raise ValueError(f"arm は {tuple(LENGTH_ARMS)} のどれか(いま {arm!r})")
    drop = set(ARM_DROP_BLOCKS[arm])
    return {b: situation.blocks[b] for b in BLOCK_ORDER if b in situation.blocks and b not in drop}


def common_text(blocks: Mapping[str, str]) -> str:
    """共通部分(B0〜B4b のうち手元にある物)の文。短い版と長い版の頭はこの文で始まる。"""
    return "\n".join(blocks[b] for b in COMMON_BLOCKS if b in blocks)


def render(situation: Situation, presented: Sequence[Candidate], *, length: str, arm: str) -> Rendered:
    """DM4 の短い版(``length="short"``=判断モデル)か長い版(``"long"``=LLM)を ``port.compose`` で作る。"""
    if length not in LENGTHS:
        raise ValueError(f"length は {LENGTHS} のどれか(いま {length!r})")
    blocks = arm_blocks(situation, arm)
    text = compose(blocks, presented, length=length)
    target = int(LENGTH_ARMS[arm])
    budget = int(round(target * CHARS_PER_TOKEN))
    return Rendered(text=text, length=length, arm=arm, chars=len(text), common_chars=len(common_text(blocks)),
                    target_tokens=target, budget_chars=budget, over_budget=len(text) > budget,
                    numbers_outside_money_time=numbers_outside_money_time(situation_text(blocks, length)))


def situation_text(blocks: Mapping[str, str], length: str) -> str:
    """状況の部分(共通 → 人ごと)の文=``compose`` の文から提示と指示を除いた頭(数字の計器はここだけを数える=
    提示の番号は C-2 の「番号で返す」の形なので数えない)。"""
    used = COMMON_BLOCKS + INDIVIDUAL_BLOCKS[length]
    return "\n".join(blocks[b] for b in BLOCK_ORDER if b in blocks and b in used)


# ---------------------------------------------------------------------------------------------- 候補(DM-0)
def affordance_from_facts(facts: Mapping[str, Any]) -> tuple[str, ...]:
    """1-10 の事実から「周りが示すできること」の語(語彙の順・engine の規則の形・expedient)。"""
    ok = {
        "移動": True,
        "乗車": bool(facts.get("station_word_or_band", False)),
        "購入": bool(facts.get("shop_word", False)),
    }
    return tuple(w for w in VOCAB if ok.get(w, False))


def word_of_output(text: str) -> str | None:
    """テープの応答(2 行形)の行為の語(語彙 v1 の横断語だけ・それ以外は None)。"""
    w = parse_two_line(text, VOCAB_VERSION).action
    return w if w in _CODE_OF else None


def _t_ns_of(facts: Mapping[str, Any]) -> int:
    minutes = int(facts.get("hour", 0)) * MINUTES_PER_HOUR + int(facts.get("minute", 0))
    return minutes * SECONDS_PER_MINUTE * NS_PER_SECOND


def context_of(situation: Situation, experience: Sequence[str] = ()) -> DecisionContext:
    """1-10 の状況 → ``DecisionContext``(予定は空・記憶はテープの前の呼の語=``origin="tape"``)。口は値を解釈しない。"""
    memories = tuple(SimpleNamespace(kind=_CODE_OF[w], event_id=None, origin="tape")
                     for w in experience if w in _CODE_OF)
    percept = SimpleNamespace(intent=None, memories=memories)
    return DecisionContext(agent_id=int(situation.agent_id), step=int(situation.step),
                           t_ns=_t_ns_of(situation.facts), wake_class=int(situation.wake_class), condition=-1,
                           cell=-1, call_id=situation.call_id or situation.sid, percept=percept)


def candidates_for(situation: Situation, experience: Sequence[str] = ()) -> tuple[Candidate, ...]:
    """DM-0 の 5 つの源(+語彙の残り)の候補を ``engine.decision.sources.build_candidates`` で作る(番号なし)。"""
    ctx = context_of(situation, experience)
    return build_candidates(ctx, vocab=VOCAB, continue_word=CONTINUE_WORD, word_of_code=_WORD_OF,
                            kind_words=_WORD_OF,
                            affordance_words=lambda c, v: affordance_from_facts(situation.facts))


def _present_rng(seed: str | int, sid: str) -> Any:
    return stream(seed, f"{PRESENT_DOMAIN}|{sid}")


def rotation_offsets(n: int, n_orders: int) -> tuple[int, ...]:
    """巡回の位置 ``k × n // N``(k=0〜N−1)。N は 1〜n。"""
    if n < 1:
        return (0,)
    if not 1 <= int(n_orders) <= n:
        raise ValueError(f"並びの数は 1〜{n}(いま {n_orders})")
    return tuple(k * n // int(n_orders) for k in range(int(n_orders)))


def orders(candidates: Sequence[Candidate], sid: str, *, n_orders: int = DEFAULT_N_ORDERS,
           seed: str | int = DEFAULT_SEED) -> tuple[tuple[Candidate, ...], ...]:
    """並べ替え試験の N 通りの提示: ``present``(種と状況の id の鍵)の並びを巡回させ、番号を 1 から振り直す。

    0 番目は ``present`` の並びそのもの(R-108 の対策 1=順のシャッフルの記録)。
    """
    base = present(candidates, _present_rng(seed, sid))
    n = len(base)
    out = []
    for r in rotation_offsets(n, n_orders):
        rot = base[r:] + base[:r]
        out.append(tuple(dataclasses.replace(c, number=i + 1) for i, c in enumerate(rot)))
    return tuple(out)


# ---------------------------------------------------------------------------------------------- テープの記録
def tape_experience(situations: Sequence[Situation], *, root: Path | None = None,
                    k: int = EXPERIENCE_K) -> dict[str, tuple[str, ...]]:
    """本人の経験の代わり: 同じテープの同じ体の、状況より前の呼(刻みが小さい・繰り延べでない)の行為の語を新しい順に k 呼。

    読むのは状況のあるテープの ``calls.parquet`` の 4 列(体・刻み・繰り延べ・応答)だけ。応答の本文は語にしてすぐ捨てる。
    """
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    base = Path(root) if root is not None else REPO
    by_tape: dict[str, list[Situation]] = {}
    for s in situations:
        by_tape.setdefault(s.tape, []).append(s)
    out: dict[str, tuple[str, ...]] = {}
    for tape, sits in sorted(by_tape.items()):
        path = _guarded(base / tape / "calls.parquet")
        if not path.is_file():
            raise EvalsetMissing(f"テープが無い: {tape}")
        agents = sorted({int(s.agent_id) for s in sits})
        aset = pa.array(agents, pa.int32())
        rows: dict[int, list[tuple[int, int, str]]] = {a: [] for a in agents}
        pos = 0
        pf = pq.ParquetFile(str(path))
        names = set(pf.schema_arrow.names)
        cols = [c for c in _TAPE_COLUMNS if c in names]  # 版 1 のテープには繰り延べの列が無い(全行が応答あり)
        for batch in pf.iter_batches(batch_size=_BATCH_ROWS, columns=cols):
            m = pc.is_in(batch.column("agent_id"), value_set=aset)
            idx = pc.indices_nonzero(m).to_pylist()
            if idx:
                sub = batch.take(pa.array(idx, pa.int64()))
                ag = sub.column("agent_id").to_pylist()
                st = sub.column(_TAPE_COLUMNS[1]).to_pylist()
                de = sub.column("deferred").to_pylist() if "deferred" in cols else [0] * len(idx)
                rs = sub.column("response").to_pylist()
                for j in range(len(idx)):  # 逐次ループ宣言: 対象の体の行だけ
                    if int(de[j]) != 0 or not rs[j]:
                        continue
                    w = word_of_output(rs[j])
                    if w is not None:
                        rows[int(ag[j])].append((int(st[j]), pos + int(idx[j]), w))
            pos += batch.num_rows
        for s in sits:
            prior = sorted((r for r in rows[int(s.agent_id)] if r[0] < int(s.step)), reverse=True)
            out[s.sid] = tuple(r[2] for r in prior[:int(k)])
    return out


def describe_candidates(cands_by_sid: Mapping[str, Sequence[Candidate]]) -> dict[str, Any]:
    """候補の集計(源ごとの提示の数・候補の数の分布)。中身の文は写さない。"""
    by_source: dict[str, int] = {}
    sizes: dict[str, int] = {}
    kinds_by_source: dict[str, dict[str, int]] = {}
    for cands in cands_by_sid.values():
        sizes[str(len(cands))] = sizes.get(str(len(cands)), 0) + 1
        for c in cands:
            by_source[c.source] = by_source.get(c.source, 0) + 1
            ks = kinds_by_source.setdefault(c.source, {})
            ks[c.kind] = ks.get(c.kind, 0) + 1
    return {"n_situations": len(cands_by_sid), "presented_by_source": dict(sorted(by_source.items())),
            "kinds_by_source": {s: dict(sorted(v.items())) for s, v in sorted(kinds_by_source.items())},
            "n_candidates": dict(sorted(sizes.items())), "blank_sources": dict(BLANK_SOURCES)}


def iter_lengths(situations: Iterable[Situation], presented_by_sid: Mapping[str, Sequence[Candidate]]
                 ) -> dict[str, dict[str, Any]]:
    """腕 × 長さごとの文字数の集計(最小・中央・最大・目安を超えた件数・数字の計器)。トークン数は空。"""
    import numpy as np

    acc: dict[tuple[str, str], list[Rendered]] = {}
    for s in situations:
        pres = presented_by_sid[s.sid]
        for arm in LENGTH_ARMS:
            for length in LENGTHS:
                acc.setdefault((arm, length), []).append(render(s, pres, length=length, arm=arm))
    out: dict[str, dict[str, Any]] = {}
    for (arm, length), rs in acc.items():
        ch = np.asarray([r.chars for r in rs], dtype=np.int64)
        cc = np.asarray([r.common_chars for r in rs], dtype=np.int64)
        nums = np.asarray([r.numbers_outside_money_time for r in rs], dtype=np.int64)
        out[f"{arm}/{length}"] = {
            "n": int(ch.size), "chars_min": int(ch.min()), "chars_median": float(np.median(ch)),
            "chars_max": int(ch.max()), "common_chars_median": float(np.median(cc)),
            "target_tokens": int(LENGTH_ARMS[arm]), "budget_chars": int(rs[0].budget_chars),
            "over_budget": int(sum(r.over_budget for r in rs)),
            "numbers_outside_money_time_median": float(np.median(nums)),
            "numbers_outside_money_time_max": int(nums.max()),
            "tokens": None,
        }
    return out
