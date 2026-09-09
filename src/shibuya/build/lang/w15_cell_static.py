"""W15 B2 セル静的文(§1 W15・D-W18)。

入力: W2 ``w2_cells.parquet``(セル・街区・面積)+ W8 ``w8_t1_cell``/``w8_targets``
      (セル代表点から見える目標物)+ W6 ``w6_poi.parquet``(セル内 POI の種別構成・名称)
      + W11 ``w11_station_exits.parquet``(出口名)。
出力: ``w15_prompts.jsonl`` → [外で fleet_gen] → ``w15_responses.jsonl``
      → ``w15_cell_static.parquet``(place_id・text・text_sha256)+``w15_gates.json``。

ゲート(§1 W15 行 + D-W18)
- 同セル **2 体でバイト差分ゼロ**: 文はセル ID だけの関数(個体語を含まない)。
  検査は ①凍結文が place_id で一意 ②個体依存語の不在(§2.4 ⑧・``normalize`` の検査器)
  ③レンダラ側で同セル 2 体の B2 バイト一致(``tests/build_lang/test_wiring.py``)。
- 同一プロンプト 2 回生成でバイト一致(温度0)。
- 150 tok 上限(§1 W15 行)。**トークン推定法**= ``perception.channels.estimate_tokens``
  (UTF-8 文字数 ÷ 2)= 知覚側の予算判定と同じ関数。
- 固有名詞は入力由来のみ(``common.scan_proper_nouns``・漢字厳格モードは**使わない**)。

**結線枠の宣言(重要・登録簿)**
知覚契約書 §2.2 の B2 予算は 150 tok、群予算(B2+B4+B4b)は **250 tok** で、実資産の実測は
B2 121 / セル群 173 tok(残り 77 tok)。凍結文を B2 に**足す**と群予算を超える。したがって
凍結文は B2 の既存行を**置き換える**形で結線する:

  ``[B2 可視] 見えるもの: <凍結文>。``  ← §3.2 の ``B2.visible`` 枠を占める

[B2 場所](セル ID・対象スロットに要る)・[B2 路面](§3.2 で唯一の等級 A 行)・[B2 看板]
(W14)・[B2 地物]は**そのまま残す**。凍結文の実効上限は **45 tok(=90 字)**
(= B2 予算 150 − 実資産での他行最大 105)で、仕様の 150 tok は「B2 ブロック全体の予算」と
読む。150 tok の生成文をそのまま載せるには B2/群予算の delta が要る=**親判断待ち**
(緩和の選択肢: ① [B2 地物] 行を凍結文に畳む → 70 tok ② 群予算の delta → 150 tok)。

expedient(本段階ぶん・登録簿へ)
- プロンプト文面(``SYSTEM_PROMPT``/``USER_TEMPLATE``)は自前。
- 可視物の**順序**= ``renderer.PerceptionAssets.load`` と同じ(可視視点数の降順 →
  target_id 昇順)。**二重定義**(build は perception の資産ローダを呼べない)。
  **件数**はプロンプト側だけ 2/2 に絞る(レンダラ側の合成フォールバックは 8/4 のまま)。
- ``max_tokens=128``・``CHAR_LIMIT=45``(指示)・``PROMPT_REGEX`` の 88 字(硬い上限)・
  ``TOKEN_CAP=45``(上記の結線枠)。
- 末尾の句点は落とす(テンプレ ``B2.visible`` が「。」を持つため)。
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Final

import numpy as np
import pyarrow as pa

from ..geo import common as C
from . import common as L
from .w14_signage import business_word

STAGE = "W15"
STAGE_VERSION = "1.0.0"

#: 実測のセル数(C1 実装・W2)。仕様の「≈600」は推定値。
EXPECTED_CELL_ROWS: Final[int] = 520

#: 生成上限トークン。
MAX_TOKENS: Final[int] = 128
#: 構造化出力の正規表現(``fleet_gen`` → vLLM ``structured_outputs``・xgrammar)。
#: **改行なし・10〜88 文字**。88 字 = ``estimate_tokens`` で 44 tok ≤ ``TOKEN_CAP`` 45 =
#: 「枠を超える文が物理的に出てこない」構造的保証(第2回生成では too_long が 181/188 =
#: 不合格の 96%だった)。禁止語(「など」等)は正規表現では書けないので指示+検査器で見る。
#: 文字数の数え方は xgrammar の Unicode 文字単位を前提=**パイロットで確認する**。
REGEX_MIN_CHARS: Final[int] = 10
REGEX_MAX_CHARS: Final[int] = 88
PROMPT_REGEX: Final[str] = rf"[^\n]{{{REGEX_MIN_CHARS},{REGEX_MAX_CHARS}}}"
#: 凍結文の長さ上限[推定トークン]=**結線枠**。
#: 導出: B2 ブロック予算 150 − 実資産(520 セル)での「他の B2 行」の最大合計 105
#: (= [B2 場所]+[B2 路面]+[B2 看板]+[B2 地物]・2026-09-09 実測)= 45。
#: §3.2 の ``B2.visible`` 枠は 60 だが、それを使うと最悪セルで B2=165 tok(>150)になる。
#: ``tests/build_lang/test_wiring.py`` が実資産でこの導出を再測して守る。
TOKEN_CAP: Final[int] = 45
#: 仕様 §1 W15 行の上限[推定トークン](報告用・B2 ブロック全体の予算として見る)。
SPEC_TOKEN_CAP: Final[int] = 150
#: プロンプトに書く字数上限(**指示値**・親指示 2026-09-09 第3回)。硬い上限は
#: ``REGEX_MAX_CHARS``(88 字 = 44 tok)で、45 字は「そこを狙わせる」ための指示。
CHAR_LIMIT: Final[int] = 45

#: 1 セルあたりに**プロンプトへ載せる**可視 POI / 目印の上限。
#: 第2回生成では 8/4 件を渡したうえで「「など」を使わず名前を並べる」と指示したため、
#: モデルが全部を列挙して 45 tok の枠を超えた(too_long 181/188)。**上位 2 件だけ**渡し、
#: 「名前は最大 2 つ」と指示することで、長さ・個数の数字・「など」を同時に潰す。
#: 選び方は決定論: ``renderer.PerceptionAssets.load`` と同じ順序(可視視点数の降順 →
#: target_id 昇順)の先頭から。
MAX_VISIBLE_POI: Final[int] = 2
MAX_VISIBLE_LANDMARK: Final[int] = 2
#: 本文に書いてよい名前の数(system の指示値)。
MAX_NAMES_IN_TEXT: Final[int] = 2

#: 入力ファイル。
INPUT_FILES: Final[tuple[str, ...]] = (
    "w2_cells.parquet",
    "w6_poi.parquet",
    "w8_targets.parquet",
    "w8_t1_cell.parquet",
    "w11_station_exits.parquet",
)

#: バンド → 層語(``perception.templates.BAND_WORDS`` と同値・層契約により二重定義)。
BAND_WORDS: Final[dict[str, str]] = {"UG": "地下", "GL": "地上", "DECK": "デッキ"}
#: 目印として扱う POI カテゴリ(renderer と同値)。
LANDMARK_CATS: Final[frozenset[str]] = frozenset({"landmark", "attraction"})

#: system プロンプト(**凍結対象**)。
SYSTEM_PROMPT: Final[str] = "\n".join(
    (
        "あなたは街の一区画を**三人称の客観描写**で書き起こす記録係です。"
        "「私」「僕」「我々」「あなた」など人を指す語は絶対に使いません。"
        "与えられた事実だけを使って、その区画の静的な説明を書きます。",
        "書き方:",
        f"1. 全体で{CHAR_LIMIT}字以内の**1文**。長さが最優先の制約です。",
        "2. まず**区画の性格**を書く。すなわち、層(地上・地下・デッキ)、"
        "街区があるかどうか、多い店の種別を1語。",
        f"3. そのあとに、見えるものの**名前を最大{MAX_NAMES_IN_TEXT}つまで**書く。"
        "与えられた名前をそのまま使う。それ以外の名前は書かない。",
        "4. 与えられた事実に無い固有名詞(店名・地名・駅名・企業名・商品名・ブランド名)を"
        "書かない。与えられていない事実を推測で足さない。",
        "5. **「など」「等」「ほか」「その他」を使わない**。書ききれないものは"
        "**数えず、触れない**。",
        "6. **数を書かない**。「2軒」「3つ」のような個数を書かない。漢数字も使わない。",
        "7. 評価語(人気・おすすめ・話題・にぎやかのような主観語)を書かない。"
        "来店や移動を誘う表現・命令文を書かない。",
        "8. 特定の人物・その場にいる人・時刻・天候・混雑には触れない。"
        "いつ来ても変わらない事実だけを書く。",
        "9. **区画IDと区画の広さは書かない**(どの区画でも同じなので書く価値がない)。",
        "10. 記号・箇条書き・改行・引用符・絵文字を使わない。句読点は「、」と「。」だけを使う。",
        "11. 「見えるもの:」に続けて読まれる文として書く。出力は本文の1行だけ。"
        "前置き・説明・見出しを書かない。",
    )
)

#: user プロンプト(**凍結対象**)。
USER_TEMPLATE: Final[str] = "\n".join(
    (
        "区画ID: {place_id}",
        "層: {band}",
        "広さ: 一辺100メートルの区画",
        "街区: {blocks}",
        "この区画に多い店の種別: {main_kind}",
        "この区画から見える店舗と施設(可視の多い順・上位2件): {visible}",
        "この区画から見える目印(上位2件): {landmarks}",
        f"この区画の静的な説明を1行で書く。{CHAR_LIMIT}字以内。区画IDと広さは書かない。"
        f"名前は最大{MAX_NAMES_IN_TEXT}つまで。数を書かない。",
    )
)


# --------------------------------------------------------------- 可視物の集約
def _visible_by_cell(world_dir: Path) -> tuple[list[list[str]], list[list[str]]]:
    """W8 T1 → セルごとの (可視 POI の表示語, 可視の目印).

    順序は ``renderer.PerceptionAssets.load`` と同じ(可視視点数の降順 → target_id 昇順)。

    Note:
        逐次ループ宣言(P4): セル数(520)ぶんの 1 本。索引付けは NumPy。
    """
    p = Path(world_dir)
    cells = C.read_parquet_columns(p / "w2_cells.parquet", ["place_id"])
    n = len(cells["place_id"])

    poi = C.read_parquet_columns(p / "w6_poi.parquet", ["poi_id", "name", "cat", "subcat"])
    poi_row = {str(pid): i for i, pid in enumerate(poi["poi_id"])}

    ex = C.read_parquet_columns(
        p / "w11_station_exits.parquet", ["exit_id", "exit_name", "station_title"]
    )
    exit_label = {
        str(e): f"{str(st)}{str(nm)}"
        for e, nm, st in zip(ex["exit_id"], ex["exit_name"], ex["station_title"])
    }

    tgt = C.read_parquet_columns(p / "w8_targets.parquet", ["target_id", "kind", "ref_id"])
    tgt_kind = [str(k) for k in tgt["kind"]]
    tgt_ref = [str(r) for r in tgt["ref_id"]]

    t1 = C.read_parquet_columns(
        p / "w8_t1_cell.parquet", ["place_idx", "target_id", "n_viewpoints"]
    )
    pidx = np.asarray(t1["place_idx"], dtype=np.int64)
    tid = np.asarray(t1["target_id"], dtype=np.int64)
    nvp = np.asarray(t1["n_viewpoints"], dtype=np.int64)
    order = np.lexsort((tid, -nvp, pidx))
    pidx, tid = pidx[order], tid[order]
    starts = np.searchsorted(pidx, np.arange(n), side="left")
    ends = np.searchsorted(pidx, np.arange(n), side="right")

    vis: list[list[str]] = []
    lands: list[list[str]] = []
    for c in range(n):  # 逐次: セル数ぶん
        v: list[str] = []
        ld: list[str] = []
        for t in tid[starts[c]: ends[c]]:
            kind = tgt_kind[int(t)]
            ref = tgt_ref[int(t)]
            if kind == "poi":
                j = poi_row.get(ref)
                if j is None:
                    continue
                cat = str(poi["cat"][j])
                if cat in LANDMARK_CATS:
                    if len(ld) < MAX_VISIBLE_LANDMARK:
                        ld.append(str(poi["name"][j]))
                elif len(v) < MAX_VISIBLE_POI:
                    word = business_word(cat, poi["subcat"][j])
                    v.append(f"{word}({str(poi['name'][j])})")
            elif kind == "exit":
                if len(ld) < MAX_VISIBLE_LANDMARK:
                    ld.append(exit_label.get(ref, "駅出入口"))
            if len(v) >= MAX_VISIBLE_POI and len(ld) >= MAX_VISIBLE_LANDMARK:
                break
        vis.append(v)
        lands.append(ld)
    return vis, lands


def _main_kind_by_cell(world_dir: Path, place_ids: list[str]) -> list[str]:
    """W6 → セル内で**最も多い店の種別 1 語**(同数は業種語の昇順・無ければ「なし」)。

    第2回生成までは「飲食店8、サービス店3、…」と件数つきの構成を渡していたが、
    それが唯一の数字源になってモデルの個数記述(N4 50 件)を誘発した。第3回は
    **1 語だけ**にして、プロンプトから件数の数字を消す(親指示 2026-09-09)。
    """
    poi = C.read_parquet_columns(
        Path(world_dir) / "w6_poi.parquet", ["place_id", "cat", "subcat"]
    )
    counters: dict[str, Counter] = {pid: Counter() for pid in place_ids}
    for pid, cat, sub in zip(poi["place_id"], poi["cat"], poi["subcat"]):
        c = counters.get(str(pid))
        if c is not None:
            c[business_word(str(cat), sub)] += 1
    out: list[str] = []
    for pid in place_ids:
        c = counters[pid]
        out.append(sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if c else "なし")
    return out


# --------------------------------------------------------------- プロンプト生成
def build_prompts(world_dir: Path) -> list[L.Prompt]:
    """W2/W6/W8/W11 → セルごとのプロンプト(決定論・行順は w2_cells の行順)。"""
    p = Path(world_dir)
    cells = C.read_parquet_columns(p / "w2_cells.parquet", ["place_id", "band", "block_ids"])
    place_ids = [str(s) for s in cells["place_id"]]
    vis, lands = _visible_by_cell(p)
    main_kind = _main_kind_by_cell(p, place_ids)

    prompts: list[L.Prompt] = []
    for i, pid in enumerate(place_ids):  # 逐次: セル数ぶん
        user = USER_TEMPLATE.format(
            place_id=pid,
            band=BAND_WORDS.get(str(cells["band"][i]), "地上"),
            blocks="あり" if cells["block_ids"][i] else "なし",
            main_kind=main_kind[i],
            visible="、".join(vis[i]) if vis[i] else "なし",
            landmarks="、".join(lands[i]) if lands[i] else "なし",
        )
        prompts.append(
            L.Prompt(
                id=pid,
                system=SYSTEM_PROMPT,
                user=user,
                max_tokens=MAX_TOKENS,
                allowed=user,
                regex=PROMPT_REGEX,
            )
        )
    return prompts


# --------------------------------------------------------------- 応答の取り込み
def ingest(
    world_dir: Path,
    responses_path: Path,
    prompts: list[L.Prompt] | None = None,
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
    for it in items:  # 逐次: セル数ぶん
        reps = [r for r in (got.get((it.id, k)) for k in range(L.REPEAT)) if r is not None]
        report.verdicts.append(
            L.verify_one(
                it.id,
                reps,
                it.allowed,
                token_cap=TOKEN_CAP,
                kanji_strict=False,
                strip_trailing_kuten=True,
            )
        )
    return report


def _write_frozen(out_dir: Path, report: L.IngestReport) -> dict[str, Any]:
    rows = report.frozen
    schema = pa.schema(
        [
            ("place_id", pa.string()),
            ("text", pa.string()),
            ("text_sha256", pa.string()),
            ("n_tokens_est", pa.int32()),
            ("n_chars", pa.int32()),
        ]
    )
    return C.write_parquet(
        out_dir,
        "w15_cell_static.parquet",
        {
            "place_id": [v.id for v in rows],
            "text": [v.text for v in rows],
            "text_sha256": [C.sha256_bytes(v.text.encode("utf-8")) for v in rows],
            "n_tokens_est": [int(v.tokens) for v in rows],
            "n_chars": [int(v.chars) for v in rows],
        },
        schema=schema,
    )


# --------------------------------------------------------------- 段階本体
def run(ctx: C.Ctx) -> C.StageResult:
    """W15: プロンプトを書き、応答があれば凍結する(純関数)。"""
    out = ctx.out
    prompts = build_prompts(out)
    psha = L.prompts_sha256(prompts)
    outputs = [L.write_prompts(out, "w15_prompts.jsonl", prompts)]

    inputs = [out / f for f in INPUT_FILES]
    resp = out / "w15_responses.jsonl"
    gates: list[C.Gate] = [
        C.Gate("cell_rows", len(prompts), EXPECTED_CELL_ROWS),
        C.Gate(
            "place_id_unique",
            len({p.id for p in prompts}),
            len(prompts),
        ),
        C.Gate("prompts_sha256", psha),
        C.Gate("system_sha256", C.sha256_bytes(SYSTEM_PROMPT.encode("utf-8"))),
        C.Gate("max_tokens", MAX_TOKENS, MAX_TOKENS),
        C.Gate("prompt_regex", PROMPT_REGEX, PROMPT_REGEX),
        C.Gate(
            "all_prompts_carry_regex",
            sum(1 for p in prompts if p.regex == PROMPT_REGEX),
            len(prompts),
        ),
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
        "token_cap_wiring": TOKEN_CAP,
        "token_cap_spec": SPEC_TOKEN_CAP,
        "wiring": "凍結文は B2.visible 行(見えるもの:)を置き換える。場所/路面/看板/地物は残す。",
        "structured_outputs": {
            "regex": PROMPT_REGEX,
            "why": (
                "改行なし・10-88 文字を文法で強制する(88 字 = 44 tok ≤ TOKEN_CAP 45)。"
                "第2回生成は too_long が不合格の 96%(181/188)だったので、長さは指示ではなく"
                "構造で保証する。禁止語は正規表現に書けないので指示+検査器で見る。"
            ),
            "char_unit_caveat": "xgrammar の文字数は Unicode 文字単位を前提=パイロットで要確認",
        },
        "fallback": "凍結行の無いセルは renderer の合成可視物リストを使う",
    }

    if resp.exists():
        report = ingest(out, resp, prompts)
        outputs.append(_write_frozen(out, report))
        outputs.append(C.write_json(out, "w15_gates.json", report.to_json(), rows=len(prompts)))
        gates += L.gate_rows(report, L.W15_MAX_FAIL_RATE)
        # 合否は**凍結行**の個体語ゼロ(§2.4 ⑧ の pin)。全応答での件数は報告値
        # (不合格の行は fail_rate 側で数えており、ここで二重に落とさない=親決定 09-09)。
        gates.append(
            C.Gate(
                "frozen_individual_word_violations",
                report.violation_count("I", frozen_only=True),
                0,
            )
        )
        gates.append(
            C.Gate("individual_word_violations_all", report.violation_count("I"))
        )
        gates.append(
            C.Gate(
                "frozen_place_id_unique",
                len({v.id for v in report.frozen}),
                len(report.frozen),
            )
        )
        gates.append(
            C.Gate(
                "tokens_max_within_spec",
                report.to_json()["tokens_max"],
                f"<= {SPEC_TOKEN_CAP}",
                passed=report.to_json()["tokens_max"] <= SPEC_TOKEN_CAP,
            )
        )
        inputs.append(resp)
        notes["ingest"] = report.to_json()
    else:
        gates.append(C.Gate("responses_present", False, None, passed=True))
        notes["responses_missing"] = (
            "w15_responses.jsonl が無い。tools/gen/fleet_gen.py で生成してから再実行すると"
            "凍結する(段階は落とさない)。"
        )

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
                "spec_token_cap": SPEC_TOKEN_CAP,
                "char_limit": CHAR_LIMIT,
                "temperature": L.TEMPERATURE,
                "seed": L.SEED,
                "repeat": L.REPEAT,
                "max_visible_poi": MAX_VISIBLE_POI,
                "max_visible_landmark": MAX_VISIBLE_LANDMARK,
                "max_names_in_text": MAX_NAMES_IN_TEXT,
                "prompt_regex": PROMPT_REGEX,
                "band_words": BAND_WORDS,
                "max_fail_rate": L.W15_MAX_FAIL_RATE,
            }
        ),
        params={
            "max_tokens": MAX_TOKENS,
            "token_cap": TOKEN_CAP,
            "spec_token_cap": SPEC_TOKEN_CAP,
            "char_limit": CHAR_LIMIT,
            "temperature": L.TEMPERATURE,
            "seed": L.SEED,
            "repeat": L.REPEAT,
            "max_fail_rate": L.W15_MAX_FAIL_RATE,
            "prompts_sha256": psha,
        },
        outputs=outputs,
        gates=gates,
        catalog_classes=[],
        expedients=[
            "プロンプト文面(system/user)は自前=先行研究なし・版は system_sha256/prompts_sha256",
            f"max_tokens={MAX_TOKENS}・char_limit={CHAR_LIMIT}",
            f"結線枠 {TOKEN_CAP} tok = B2 予算 150 − 実資産での他行最大 105"
            "(仕様の 150 tok は B2 ブロック全体の予算と読む)",
            f"プロンプトへ載せる可視物は上位 {MAX_VISIBLE_POI} 件・目印 {MAX_VISIBLE_LANDMARK} 件"
            f"(順序は renderer と同じ・本文に書ける名前は {MAX_NAMES_IN_TEXT} つまで)",
            "セル内 POI の構成は**最も多い種別 1 語**だけ渡す(件数の数字をプロンプトから消す)",
            "街区は数でなく あり/なし",
            f"構造化出力 regex={PROMPT_REGEX}(改行なし・{REGEX_MIN_CHARS}-{REGEX_MAX_CHARS} 字)",
            "可視物の順序・上限(8/4)は renderer.PerceptionAssets.load の二重定義",
            "末尾の句点は落とす(テンプレ B2.visible が句点を持つ)",
            f"不合格率の閾値 {L.W15_MAX_FAIL_RATE}",
        ],
        notes=notes,
    )
