"""W14 看板(a)文面(§1 W14・D-W18)。

入力: W6 ``w6_poi.parquet``(POI 名・カテゴリ)+ W7 ``w7_plan_spec.parquet``(営業時間・価格帯)。
出力: ``w14_prompts.jsonl``(段階が書く)→ [外で fleet_gen] → ``w14_responses.jsonl``
      → ``w14_signage.parquet``(poi_id・text・text_sha256・n_tokens_est)+``w14_gates.json``。

ゲート(§1 W14 行 + D-W18)
- 同店 **2 回生成でバイト一致**(温度0)。
- 文面 SHA(プロンプト・凍結文の両方をヘッダへ)。
- **固有名詞は入力(POI 名)由来のみ**(入力にない固有名詞を含む文は不合格)= ``common.scan_proper_nouns``。
- 正規化規約 9 項(``perception.normalize`` を通した結果と一致=通したものを凍結)。
- 長さ上限= 知覚契約書 §3.2「看板・広告面1件 25 tok」= ``estimate_tokens`` で 25(≒50 字)。

**不合格の店は凍結しない**。レンダラは ``w14_signage.parquet`` に行が無い POI について
従来の合成文(``renderer._signage`` の「<店名>の表示。営業は<h>時から<h>時。」)を使う。

expedient(本段階ぶん・登録簿へ)
- プロンプト文面(``SYSTEM_PROMPT``・``USER_TEMPLATE``)は自前(先行研究なし)。版は
  ``system_sha256``/``prompts_sha256`` で管理する。
- ``max_tokens=64``: 内容キャップ 25 tok(§3.2)= ``estimate_tokens`` で 50 字 → 日本語は
  Qwen 系で概ね 1 字 1 トークン前後なので 50 + 余裕 14。生成が上限に当たった応答は
  途中で切れる可能性があるが、長さゲート(25 tok)で落ちるので凍結には入らない。
- カテゴリ → 業種語の表(``CAT_WORDS``/``SUBCAT_WORDS``)。**プロンプトに載せた語だけ**が
  固有名詞検査の許容語彙になる(=モデルが勝手な業種語を作ると不合格になる)。
- 価格帯語(``PRICE_WORDS``)。``free`` は「表示なし」に写す(landmark/office 等の非商業 POI が
  ``free`` に入っているため「無料」と書かせない)。
- 営業時間の日本語化と**圧縮**(曜日のまとめ方・「24時間」「翌N時」の表記・多くて 2 帯・
  24 字を超えたら代表日 1 帯へ = ``format_opening_hours`` の docstring)。第1回生成
  (2026-09-09)では曜日別の内訳をそのまま渡したため 72 件が長さ超過、「毎日終日」には
  数字が無いためモデルが 10-22 時を捏造して 74 件が N4 で落ちた。
- 漢字厳格モード(``kanji_strict=True``)。W14 の出力語彙は強く制約されるので、入力に無い
  **3 文字以上**の漢字列を捏造とみなす(2 文字漢語は一般名詞になりやすいので対象外=
  第1回生成の偽陽性 113 件の反映)。W15 では使わない。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import pyarrow as pa

from ..geo import common as C
from . import common as L

STAGE = "W14"
STAGE_VERSION = "1.0.0"

#: 仕様書 §1 W6/W14 の POI 数(=呼数)。変わったら気づけるように定数で置く。
EXPECTED_POI_ROWS: Final[int] = 2337

#: 生成上限トークン(上の expedient を参照)。
MAX_TOKENS: Final[int] = 64
#: 凍結文の長さ上限[推定トークン]= 知覚契約書 §3.2 の ``B2.signage`` 25 tok。
TOKEN_CAP: Final[int] = 25
#: プロンプトに書く字数上限(``TOKEN_CAP`` × 2 字 − 余裕 5)。
CHAR_LIMIT: Final[int] = 45

#: 入力ファイル(``ctx.out`` にある前段の出力)。
INPUT_FILES: Final[tuple[str, ...]] = ("w6_poi.parquet", "w7_plan_spec.parquet")

#: cat → 業種語(D-W7 の 3 層規則②「店舗 POI は業種・サブカテゴリ・価格帯・営業時間まで実データ」)。
CAT_WORDS: Final[dict[str, str]] = {
    "food": "飲食店",
    "shop": "物販店",
    "nightlife": "夜間営業の飲食店",
    "office": "事務所",
    "service": "サービス店",
    "hotel": "宿泊施設",
    "school": "学校",
    "landmark": "目印になる施設",
    "leisure": "娯楽施設",
    "hall": "集会施設",
    "attraction": "観光施設",
    "cinema": "映画館",
    "education": "教育施設",
}
#: subcat → 業種語(cat より優先)。
SUBCAT_WORDS: Final[dict[str, str]] = {
    "convenience": "コンビニエンスストア",
    "love_hotel": "宿泊施設",
    "worship": "宗教施設",
    "karaoke": "カラオケ店",
    "club": "ナイトクラブ",
    "childcare": "保育施設",
    "pachinko": "ぱちんこ店",
    "hospital": "病院",
    "arcade": "ゲームセンター",
    "sauna": "サウナ",
    "net_cafe": "インターネットカフェ",
}
#: price_tier → 価格帯語。
PRICE_WORDS: Final[dict[str, str]] = {
    "low": "低め",
    "mid": "中程度",
    "high": "高め",
    "free": "表示なし",
}
#: 曜日語(W7 の content は 0=月曜)。
DAY_WORDS: Final[tuple[str, ...]] = ("月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "日曜")

#: system プロンプト(**凍結対象**・版は ``system_sha256`` で管理)。
SYSTEM_PROMPT: Final[str] = "\n".join(
    (
        "あなたは店舗の店頭表示を書き起こす記録係です。与えられた事実だけを使って、"
        "その店の店頭に出ている表示の文面を書きます。",
        "規則:",
        "1. 与えられた事実に無い固有名詞(店名・地名・駅名・企業名・商品名・ブランド名)を"
        "書かない。与えられていない事実を推測で足さない。",
        "2. 評価語(人気・おすすめ・絶品・話題・限定・名物・こだわりのような語)を書かない。",
        "3. 来店を誘う表現(ぜひ・どうぞ・ください・いかが・お立ち寄り・今すぐのような語)を"
        "書かない。命令文を書かない。",
        "4. 数字は与えられた営業時間の数字だけを使う。漢数字は使わない。"
        "与えられていない時刻を書かない。",
        "5. **営業時間は与えられた表現をそのまま使う**。曜日ごとの内訳を作らない。"
        "曜日を「月金」「火曜金曜」のように略さない。",
        "6. 記号・箇条書き・改行・引用符・絵文字を使わない。句読点は「、」と「。」だけを使う。",
        "7. 時刻は「10時から22時」の形で書く。分があるときだけ「10時30分」の形にする。",
        f"8. 全体で{CHAR_LIMIT}字以内の**1文**。事実を述べる平叙文だけを書く。"
        f"{CHAR_LIMIT}字に収まらないときは、価格帯、次に業種の順で省く。"
        "店名と営業時間は必ず残す。",
        "9. 出力は本文の1行だけ。前置き・説明・見出しを書かない。",
    )
)

#: user プロンプト(**凍結対象**)。
USER_TEMPLATE: Final[str] = "\n".join(
    (
        "店名: {name}",
        "業種: {cat}",
        "価格帯: {price}",
        "営業時間: {hours}",
        "定休日: {closed}",
        "この店の店頭表示を1行で書く。",
    )
)


# --------------------------------------------------------------- 入力の日本語化
def _fmt_hm(minute: int) -> str:
    """分(0時からの通算)→「10時」/「10時30分」。24 時以降は「翌2時」。"""
    m = int(minute)
    day_over = m >= 1440
    m = m % 1440
    h, mi = divmod(m, 60)
    body = f"{h}時" if mi == 0 else f"{h}時{mi}分"
    return ("翌" + body) if day_over else body


def _fmt_first_interval(intervals: list[list[int]]) -> str:
    """1 日ぶんの区間列 → **最初の区間 1 つ**の表記。空なら空文字(定休)。

    ``[0,1440]`` は「24時間」(第1回生成では「毎日終日」と渡したため、モデルが
    「10時から22時」という**入力に無い数字**を捏造して 74 件が N4 で落ちた。
    「24」を入力に含めることでコンビニ等の 24 時間営業を数字つきで書ける)。
    """
    if not intervals:
        return ""
    a, b = int(intervals[0][0]), int(intervals[0][1])
    if a == 0 and b >= 1440:
        return "24時間"
    return f"{_fmt_hm(a)}から{_fmt_hm(b)}"


#: 曜日の並び → 群(平日 = 月-金・土日 = 土日)。
_WEEKDAY_IDX: Final[tuple[int, ...]] = (0, 1, 2, 3, 4)
_WEEKEND_IDX: Final[tuple[int, ...]] = (5, 6)
#: プロンプトに載せる営業時間表現の字数上限(超えたら代表日 1 帯へ畳む・expedient)。
#: 45 字の本文に店名と業種を入れる余地を残すための値。
MAX_HOURS_CHARS: Final[int] = 24


def format_opening_hours(content: str) -> tuple[str, str]:
    """W7 ``content``(7 日 × 区間の JSON)→ (営業時間の文, 定休日の文)。

    **圧縮規則(45 字ゲートのための前処理・expedient・2026-09-09 改訂)**。第1回生成では
    曜日別の内訳をそのまま渡したため、モデルが全曜日を書き写して 72 件が長さ超過で落ちた。
    渡す表現は**多くて 2 帯**に畳む:

    1. 全曜日が同一区間 → 「毎日<帯>」(全曜日 24 時間なら「24時間営業(毎日)」)。
    2. 平日群(月-金)の営業日が一定、かつ土日群の営業日が一定 → 「平日は<A>、土日は<B>」
       (片方が全休なら在る側だけを書く。定休日欄に休みの曜日が出る)。
    3. それ以外(群の中で日ごとに違う) → **代表日**(営業分数が最大の日・同点は曜日番号が
       小さい方)の最初の区間 +「(曜日で異なる)」。
    どの場合も 1 日に複数区間があれば**最初の区間だけ**を渡し「(時間帯で異なる)」を足す。
    2 帯にしても ``MAX_HOURS_CHARS``(24 字)を超えるときは 3. へ落とす。

    Example:
        >>> format_opening_hours("[[[600,1320]],[[600,1320]],[[600,1320]],"
        ...                      "[[600,1320]],[[600,1320]],[],[]]")
        ('平日は10時から22時', '土曜、日曜')
    """
    days: list[list[list[int]]] = json.loads(content)
    if len(days) != 7:
        raise ValueError(f"W7 content の日数が 7 でない: {len(days)}")
    texts = [_fmt_first_interval(d) for d in days]
    closed = [DAY_WORDS[i] for i, t in enumerate(texts) if not t]
    closed_text = "、".join(closed) if closed else "なし"
    multi = any(len(d) > 1 for d in days)
    note = "(時間帯で異なる)" if multi else ""

    open_texts = [t for t in texts if t]
    if not open_texts:
        return ("営業時間の表示なし", closed_text)

    # 1. 全曜日同一
    if all(t == texts[0] for t in texts):
        if texts[0] == "24時間":
            return ("24時間営業(毎日)" + note, closed_text)
        return (f"毎日{texts[0]}{note}", closed_text)

    # 2. 平日群・土日群でそれぞれ一定
    wd_open = [i for i in _WEEKDAY_IDX if texts[i]]
    we_open = [i for i in _WEEKEND_IDX if texts[i]]
    if (
        len({texts[i] for i in wd_open}) <= 1
        and len({texts[i] for i in we_open}) <= 1
        and (wd_open or we_open)
    ):
        parts = []
        if wd_open:
            parts.append(f"{_group_phrase(wd_open, _WEEKDAY_IDX, '平日')}は{texts[wd_open[0]]}")
        if we_open:
            parts.append(f"{_group_phrase(we_open, _WEEKEND_IDX, '土日')}は{texts[we_open[0]]}")
        hours = "、".join(parts) + note
        if len(hours) <= MAX_HOURS_CHARS:
            return (hours, closed_text)

    # 3. 代表日(営業分数が最大の日・同点は曜日番号が小さい方)+ 「異なる」の但し書き
    minutes = [sum(int(b) - int(a) for a, b in d) for d in days]
    rep = max(range(7), key=lambda i: (minutes[i], -i))
    tail = "(曜日と時間帯で異なる)" if multi else "(曜日で異なる)"
    return (f"{texts[rep]}{tail}", closed_text)


def _group_phrase(idxs: list[int], group: tuple[int, ...], label: str) -> str:
    """群の中で営業している曜日の並び → 短い曜日表現(決定論)。"""
    if len(idxs) == len(group):
        return label
    if len(idxs) == 1:
        return DAY_WORDS[idxs[0]]
    if idxs == list(range(idxs[0], idxs[-1] + 1)):
        return f"{DAY_WORDS[idxs[0]]}から{DAY_WORDS[idxs[-1]]}"
    return "、".join(DAY_WORDS[i] for i in idxs)


def business_word(cat: str, subcat: str | None) -> str:
    """(cat, subcat) → 業種語。subcat が表にあればそちらを採る。"""
    if subcat and str(subcat) in SUBCAT_WORDS:
        return SUBCAT_WORDS[str(subcat)]
    return CAT_WORDS.get(str(cat), "店舗")


# --------------------------------------------------------------- プロンプト生成
def build_prompts(world_dir: Path) -> list[L.Prompt]:
    """W6/W7 → POI ごとのプロンプト(決定論・行順は w6_poi の行順)。

    Note:
        逐次ループ宣言(P4): POI 数(2,337)ぶんの 1 本。構築時 1 回。
    """
    p = Path(world_dir)
    poi = C.read_parquet_columns(p / "w6_poi.parquet", ["poi_id", "name", "cat", "subcat"])
    plan = C.read_parquet_columns(p / "w7_plan_spec.parquet", ["poi_id", "content", "price_tier"])
    by_poi = {
        str(pid): (str(cnt), str(tier))
        for pid, cnt, tier in zip(plan["poi_id"], plan["content"], plan["price_tier"])
    }

    prompts: list[L.Prompt] = []
    for pid, name, cat, subcat in zip(poi["poi_id"], poi["name"], poi["cat"], poi["subcat"]):
        pid = str(pid)
        content, tier = by_poi.get(pid, ("[[],[],[],[],[],[],[]]", "free"))
        hours, closed = format_opening_hours(content)
        user = USER_TEMPLATE.format(
            name=str(name),
            cat=business_word(str(cat), subcat),
            price=PRICE_WORDS.get(str(tier), "表示なし"),
            hours=hours,
            closed=closed,
        )
        prompts.append(
            L.Prompt(id=pid, system=SYSTEM_PROMPT, user=user, max_tokens=MAX_TOKENS, allowed=user)
        )
    return prompts


# --------------------------------------------------------------- 応答の取り込み
def ingest(
    world_dir: Path,
    responses_path: Path,
    prompts: list[L.Prompt] | None = None,
    *,
    kanji_strict: bool = True,
) -> L.IngestReport:
    """応答 jsonl を読み、ゲートを掛けて凍結対象を決める(ファイルは書かない)。"""
    p = Path(world_dir)
    items = prompts if prompts is not None else build_prompts(p)
    got = L.read_responses(Path(responses_path))
    report = L.IngestReport(
        n_prompts=len(items),
        responses_sha256=C.sha256_file(Path(responses_path)),
        responses_path=Path(responses_path).name,
    )
    for it in items:  # 逐次: プロンプト件数ぶん(構築時 1 回)
        reps = [r for r in (got.get((it.id, k)) for k in range(L.REPEAT)) if r is not None]
        report.verdicts.append(
            L.verify_one(
                it.id,
                reps,
                it.allowed,
                token_cap=TOKEN_CAP,
                kanji_strict=kanji_strict,
            )
        )
    return report


def _write_frozen(out_dir: Path, report: L.IngestReport) -> dict[str, Any]:
    """合格文 → ``w14_signage.parquet``(poi_id 昇順ではなく**プロンプト順**=w6 行順)。"""
    rows = report.frozen
    schema = pa.schema(
        [
            ("poi_id", pa.string()),
            ("text", pa.string()),
            ("text_sha256", pa.string()),
            ("n_tokens_est", pa.int32()),
            ("n_chars", pa.int32()),
        ]
    )
    return C.write_parquet(
        out_dir,
        "w14_signage.parquet",
        {
            "poi_id": [v.id for v in rows],
            "text": [v.text for v in rows],
            "text_sha256": [C.sha256_bytes(v.text.encode("utf-8")) for v in rows],
            "n_tokens_est": [int(v.tokens) for v in rows],
            "n_chars": [int(v.chars) for v in rows],
        },
        schema=schema,
    )


# --------------------------------------------------------------- 段階本体
def run(ctx: C.Ctx, *, kanji_strict: bool = True) -> C.StageResult:
    """W14: プロンプトを書き、応答があれば凍結する(純関数)。"""
    out = ctx.out
    prompts = build_prompts(out)
    psha = L.prompts_sha256(prompts)
    outputs = [L.write_prompts(out, "w14_prompts.jsonl", prompts)]

    inputs = [out / f for f in INPUT_FILES]
    resp = out / "w14_responses.jsonl"
    gates: list[C.Gate] = [
        C.Gate("poi_rows", len(prompts), EXPECTED_POI_ROWS),
        C.Gate("prompts_sha256", psha),
        C.Gate("system_sha256", C.sha256_bytes(SYSTEM_PROMPT.encode("utf-8"))),
        C.Gate("max_tokens", MAX_TOKENS, MAX_TOKENS),
    ]
    notes: dict[str, Any] = {
        "llm": {
            "model_hint": L.MODEL_HINT,
            "temperature": L.TEMPERATURE,
            "seed": L.SEED,
            "repeat": L.REPEAT,
            "n_calls": len(prompts) * L.REPEAT,
        },
        "token_estimator": "perception.channels.estimate_tokens(UTF-8 文字数 ÷ 2)",
        "token_cap": TOKEN_CAP,
        "fallback": "凍結行の無い POI は renderer の合成文(店名+営業時間)を使う",
    }

    if resp.exists():
        report = ingest(out, resp, prompts, kanji_strict=kanji_strict)
        outputs.append(_write_frozen(out, report))
        outputs.append(C.write_json(out, "w14_gates.json", report.to_json(), rows=len(prompts)))
        gates += L.gate_rows(report, L.W14_MAX_FAIL_RATE)
        inputs.append(resp)
        notes["ingest"] = report.to_json()
    else:
        gates.append(C.Gate("responses_present", False, None, passed=True))
        notes["responses_missing"] = (
            "w14_responses.jsonl が無い。tools/gen/fleet_gen.py で生成してから再実行すると"
            "凍結する(段階は落とさない)。"
        )

    catalog: list[str] = []
    if resp.exists() and notes.get("ingest", {}).get("n_frozen", 0) > 0:
        catalog = ["看板・広告文言"]

    return C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash(inputs),
        param_hash=C.param_hash(
            {
                "system_sha256": C.sha256_bytes(SYSTEM_PROMPT.encode("utf-8")),
                "user_template": USER_TEMPLATE,
                "max_tokens": MAX_TOKENS,
                "token_cap": TOKEN_CAP,
                "char_limit": CHAR_LIMIT,
                "temperature": L.TEMPERATURE,
                "seed": L.SEED,
                "repeat": L.REPEAT,
                "kanji_strict": kanji_strict,
                "cat_words": CAT_WORDS,
                "subcat_words": SUBCAT_WORDS,
                "price_words": PRICE_WORDS,
                "max_fail_rate": L.W14_MAX_FAIL_RATE,
            }
        ),
        params={
            "max_tokens": MAX_TOKENS,
            "token_cap": TOKEN_CAP,
            "char_limit": CHAR_LIMIT,
            "temperature": L.TEMPERATURE,
            "seed": L.SEED,
            "repeat": L.REPEAT,
            "kanji_strict": kanji_strict,
            "max_fail_rate": L.W14_MAX_FAIL_RATE,
            "prompts_sha256": psha,
        },
        outputs=outputs,
        gates=gates,
        catalog_classes=catalog,
        expedients=[
            "プロンプト文面(system/user)は自前=先行研究なし・版は system_sha256/prompts_sha256",
            f"max_tokens={MAX_TOKENS}(内容キャップ 25 tok=50 字 + 余裕)",
            "cat/subcat → 業種語の表・price_tier → 価格帯語(free=表示なし)",
            "営業時間の日本語化(曜日のまとめ方・終日・翌N時)",
            "固有名詞検査 N1-N7(字種+接尾辞+既知語・裸の地名は既知語リスト依存=残余リスク)",
            f"漢字厳格モード kanji_strict={kanji_strict}",
            f"不合格率の閾値 {L.W14_MAX_FAIL_RATE}",
        ],
        notes=notes,
    )
