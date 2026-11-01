# -*- coding: utf-8 -*-
"""leak_check.sets — 問いの集合(型 ①・②・④)を作る。``python -m leak_check.sets --write`` で ``question_sets/`` に書く。

型 ①「時点を切る」(Ludwig ら §3.3・Anthis ら §4.5.2 の型)
    (a) ``type1_dates.jsonl``: 日付を指定して「その日に渋谷で起きた出来事を挙げよ」。世界の時点 2026-07-13 より前の
        日付 10 件と後の日付 10 件。答えの形は「1 行目に『分からない』か『ある』・2 行目から出来事を 1 行に 1 つ」。
    (b) ``type1_events.jsonl``: 架空の出来事 10 件(時点の前 5・後 5)。実在の出来事は**入れない**(親が後で
        ``data/leak_check/real_events.jsonl`` に置く=gitignore の下・md5 で照らす)。走らせるときに架空と実在を種の
        鍵で混ぜ、「知っているか」を問う(1 行目に「はい」「いいえ」「分からない」・2 行目に 1 文)。
        架空の出来事は、起きていないと分かる形(街の形・制度を大きく変える出来事)にし、実在した出来事の形(像や
        ホームの移設など)は借りない(検収 L5 で f02・f04 を差し替えた)。ただし時点の後の 5 件は
        Claude の知識の締め切り(2026-06)の後の日付なので、起きていないことを親が確かめる(報告の問い)。

型 ②「名前を伏せる」(Glasserman & Lin 2023・指示書 10-03 §9-1 の店名の架空名の比較の腕を施設と出来事へ)
    ``type2_names.jsonl``: 判断の場面(dm_eval の 1-10 の行と同じ形=``input_text`` は行の頭の ``[Bx …]`` で分かれる
    ブロック・``facts``・``strata``・``input_missing``・``lang``)に候補 3〜6 を付け、実名版と架空名版の 2 行を作る。
    2 行の違いは名だけ(``{名}`` の差し込み)。候補の並びと中身は同じ。対象は 4 つ: 施設 2(渋谷スクランブルスクエア・
    MIYASHITA PARK)・出来事 1(渋谷のハロウィン)・店名(6 店・1 店に 1 場面)。対象ごとに 5 場面以上。
    人物は架空(役割だけで名は付けない)。数字はお金と時刻だけ(DM4 の形・近景の「25 メートル」は 1-10 の材料の形)。
    出来事の場面は、名のほかに出来事を言い当てる手がかり(仮装・日付)を書かない(名を伏せた効果を薄めないため)。人の多さ・警察官・時刻などの手がかりは
    残るが、実名版と架空名版で同じなので交絡ではない(検収 L4)。

型 ④「記憶の誘い出し」(Golchin & Surdeanu ICLR 2024 の guided instruction と general instruction)
    ``type4_recall.jsonl``: 指示の型 2 つ(guided=データ名と冒頭を与える・general=冒頭だけを与える)。参照の文
    (データ名・冒頭・続き)は親が後で ``data/leak_check/recall_refs.jsonl`` に置く。問いの集合には参照の文も
    検証側の値も 1 つも入れない。

expedient(器の宣言・未リサーチ)
    - 型 ① の日付の選び方(前 10・後 10・同じ月日の対=10-31 を前後に置く)と架空の出来事の文。
    - 型 ② の架空名(実名の構造の語を残し、ブランドの語だけを片仮名 3 音の無意味語に)。実在しないことは親が確かめる
      (検収 M3・N3・Q5)。
    - 型 ② の場面の文と候補(Claude の作文)。候補の並びは実名版と架空名版で同じに固定する(位置の偏りは対の差で消える)。
    - 型 ④ の冒頭の長さ(既定 64 文字)と続きの長さ(既定 128 文字)は ``run`` の側の既定。
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from leak_check import SETS_DIR, WORLD_DATE

TYPE1_DATES_NAME: Final[str] = "type1_dates.jsonl"
TYPE1_EVENTS_NAME: Final[str] = "type1_events.jsonl"
TYPE2_NAME: Final[str] = "type2_names.jsonl"
TYPE4_NAME: Final[str] = "type4_recall.jsonl"
SET_NAMES: Final[tuple[str, ...]] = (TYPE1_DATES_NAME, TYPE1_EVENTS_NAME, TYPE2_NAME, TYPE4_NAME)

NAME_SLOT: Final[str] = "{名}"
SIDE_PRE: Final[str] = "pre"
SIDE_POST: Final[str] = "post"

# ---------------------------------------------------------------------------------------------- 型 ①
#: 時点より前の日付(10)。施設の開業日(a1-research §4-3)とハロウィンの夜を含む。
DATES_PRE: Final[tuple[str, ...]] = (
    "2019-11-01", "2020-07-28", "2022-10-31", "2023-10-31", "2024-10-31",
    "2025-07-13", "2025-10-31", "2026-01-01", "2026-05-05", "2026-07-01",
)
#: 時点より後の日付(10)。2026-10-31 は前の 10-31 と対になる。
DATES_POST: Final[tuple[str, ...]] = (
    "2026-07-14", "2026-07-25", "2026-08-08", "2026-08-22", "2026-09-05",
    "2026-09-19", "2026-10-03", "2026-10-12", "2026-10-24", "2026-10-31",
)

DATE_PROMPT: Final[str] = (
    "{date}に東京の渋谷で起きた出来事を挙げてください。\n"
    "知らない、または分からない場合は、1 行目に「分からない」とだけ書いてください。\n"
    "知っている場合は、1 行目に「ある」と書き、2 行目から出来事を 1 行に 1 つずつ、最大 5 つ書いてください。"
)

#: 架空の出来事(起きていないと分かる形)。(id・年月・文)。
FICTIONAL_EVENTS: Final[tuple[tuple[str, str, str], ...]] = (
    ("f01", "2021-03", "渋谷スクランブル交差点の中央に、高い時計塔が建てられた。"),
    ("f02", "2022-09", "道玄坂の坂が削られて平らな道になった。"),
    ("f03", "2023-06", "渋谷区が区内のすべての歩道を動く歩道に置き換える工事を始めた。"),
    ("f04", "2024-11", "センター街の全体が水路に作り替えられ、小舟で行き来するようになった。"),
    ("f05", "2025-05", "渋谷川に大型の遊覧船の定期便が就航した。"),
    ("f06", "2026-07", "渋谷スクランブル交差点の上に、歩行者用のガラスの橋が開通した。"),
    ("f07", "2026-08", "渋谷駅のすべての改札が廃止され、乗車券が要らなくなった。"),
    ("f08", "2026-09", "渋谷区が区内で傘を差すことを禁じる条例を施行した。"),
    ("f09", "2026-10", "宮益坂の全体が屋根で覆われた。"),
    ("f10", "2026-10", "渋谷のハロウィンの夜に、スクランブル交差点が氷のスケートリンクになった。"),
)

EVENT_PROMPT: Final[str] = (
    "次の出来事を知っていますか。\n"
    "出来事: {when}、{text}\n"
    "1 行目に「はい」「いいえ」「分からない」のどれか 1 つだけを書き、2 行目に知っていることを 1 文で書いてください。"
)


def _ja_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.year}年{d.month}月{d.day}日"


def ja_month(ym: str) -> str:
    """``YYYY-MM`` → ``YYYY年M月``。"""
    y, m = ym.split("-")[:2]
    return f"{int(y)}年{int(m)}月"


def side_of(day_or_month: str) -> str:
    """世界の時点との前後(年月だけのときは、時点の月を「後」に数える=時点の月の出来事は時点の後でありうる)。"""
    w = dt.date.fromisoformat(WORLD_DATE)
    parts = day_or_month.split("-")
    if len(parts) == 2:
        y, m = int(parts[0]), int(parts[1])
        return SIDE_PRE if (y, m) < (w.year, w.month) else SIDE_POST
    d = dt.date.fromisoformat(day_or_month)
    if d == w:
        raise ValueError("世界の時点の当日は前後に分けない")
    return SIDE_PRE if d < w else SIDE_POST


def event_prompt(when_ym: str, text: str) -> str:
    return EVENT_PROMPT.format(when=ja_month(when_ym), text=text)


def build_type1_dates() -> list[dict[str, Any]]:
    w = dt.date.fromisoformat(WORLD_DATE)
    rows = []
    for i, iso in enumerate(DATES_PRE + DATES_POST):
        side = side_of(iso)
        rows.append({
            "qid": f"t1a-{i + 1:02d}", "type": 1, "part": "a", "date": iso, "side": side,
            "days_from_world": (dt.date.fromisoformat(iso) - w).days, "lang": "ja",
            "prompt": DATE_PROMPT.format(date=_ja_date(iso)),
        })
    return rows


def build_type1_events() -> list[dict[str, Any]]:
    rows = []
    for eid, ym, text in FICTIONAL_EVENTS:
        rows.append({
            "qid": f"t1b-{eid}", "type": 1, "part": "b", "kind": "fictional", "when": ym, "side": side_of(ym),
            "lang": "ja", "prompt": event_prompt(ym, text),
        })
    return rows


# ---------------------------------------------------------------------------------------------- 型 ②
#: 対象 → (区分・実名・ブランドの語の置き換え)。架空名は、実名の構造の語(渋谷・の・店・本店・スクエア・PARK)を
#: 残し、ブランドの語だけを片仮名 3 音の無意味語に置き換えて作る(検収 M3 → N3・親の判断)。業態・展望・既存の店の
#: 連想を足さない。実在しないことは親が確かめる。伏せ字の腕は足さない(拡張=判断待ち)。
BRAND_SWAPS: Final[Mapping[str, tuple[str, str, tuple[tuple[str, str], ...]]]] = {
    "scramble_square": ("facility", "渋谷スクランブルスクエア", (("スクランブル", "ヨスリ"),)),
    "miyashita_park": ("facility", "MIYASHITA PARK", (("MIYASHITA", "ルモテ"),)),
    "halloween": ("event", "渋谷のハロウィン", (("ハロウィン", "タロナ"),)),
    "shop_109": ("shop", "SHIBUYA109渋谷店", (("SHIBUYA109", "ベミカ"),)),
    "shop_parco": ("shop", "渋谷PARCO", (("PARCO", "ソミラ"),)),
    "shop_loft": ("shop", "渋谷ロフト", (("ロフト", "ヌキソ"),)),
    "shop_donki": ("shop", "MEGAドン・キホーテ渋谷本店", (("MEGAドン・キホーテ", "ネカリ"),)),
    "shop_hands": ("shop", "ハンズ渋谷店", (("ハンズ", "ポナセ"),)),
    "shop_shinqs": ("shop", "渋谷ヒカリエ ShinQs", (("ヒカリエ", "ケトミ"), ("ShinQs", "ハユナ"))),
}


def fictional_name(real: str, swaps: Sequence[tuple[str, str]]) -> str:
    """実名のブランドの語だけを無意味語に置き換える(どの語も実名にちょうど 1 回出ること)。"""
    out = real
    for brand, word in swaps:
        if real.count(brand) != 1:
            raise ValueError(f"ブランドの語 {brand!r} が実名 {real!r} にちょうど 1 回でない")
        out = out.replace(brand, word)
    return out


#: 対象 → (区分・実名・架空名)。
TARGETS: Final[Mapping[str, tuple[str, str, str]]] = {
    k: (kind, real, fictional_name(real, swaps)) for k, (kind, real, swaps) in BRAND_SWAPS.items()}
#: 対象の群(採点の内訳の単位)。店名は 6 店で 1 群。
TARGET_GROUP: Final[Mapping[str, str]] = {
    "scramble_square": "scramble_square", "miyashita_park": "miyashita_park", "halloween": "halloween",
    "shop_109": "shop", "shop_parco": "shop", "shop_loft": "shop", "shop_donki": "shop", "shop_hands": "shop",
    "shop_shinqs": "shop",
}

CHOICE_INSTRUCTION: Final[str] = "上の状況で、あなたが次にすることを候補から 1 つ選び、番号だけを半角数字で答えてください。"


def _scene(target: str, n: int, *, kind: str, place: str, visible: str, hour: int, minute: int, weather: str,
           density: str, near: str, extra: Sequence[str], candidates: Sequence[str]) -> dict[str, Any]:
    """1 場面の型(``{名}`` を含む)。ブロックは dm_eval の 1-10 の行と同じ頭(``[B1 種別]`` ほか)。"""
    lines = [f"[B1 種別] あなたは{kind}です。", f"[B2 場所] 現在地は{place}です。", f"[B2 可視] 見えるもの: {visible}。",
             f"[B3 時刻] 現在時刻は{hour}時{minute:02d}分です。", f"[B3 天候] 天候は{weather}です。"]
    lines += list(extra)
    lines += [f"[B4 密度] 歩行者密度は段階{density}です。", f"[B4b 近景] 25メートル以内: {near}。"]
    return {"target": target, "n": n, "kind": kind, "hour": hour, "minute": minute, "density": density,
            "template": "\n".join(lines), "candidates": tuple(candidates)}


SCENES: Final[tuple[dict[str, Any], ...]] = (
    # ---- 渋谷スクランブルスクエア(施設)
    _scene("scramble_square", 1, kind="渋谷の会社に勤める会社員", place="渋谷駅の東口の前(地上)",
           visible="{名}、バスの乗り場、歩道橋", hour=12, minute=10, weather="晴、日照は日中", density="B",
           near="同僚がひとり", extra=("[B3 予定] 昼休みが始まりました。昼食はまだです。",),
           candidates=("{名}の飲食店の階で昼食をとる", "駅の反対側の定食屋まで歩く", "コンビニで買って会社に戻る",
                       "同僚に行き先を任せる")),
    _scene("scramble_square", 2, kind="地方から来た観光客", place="渋谷駅の東口の前(地上)",
           visible="{名}、スクランブル交差点の方角、ハチ公の方角", hour=18, minute=40, weather="晴、日照は夕方",
           density="C", near="なし", extra=("[B3 予定] 今夜の予定は決めていません。街の夜景を見たいと思っています。",),
           candidates=("{名}の上の階の展望の施設に上がる", "スクランブル交差点を渡って写真を撮る", "ホテルに戻って休む",
                       "近くの居酒屋に入る")),
    _scene("scramble_square", 3, kind="大学生", place="渋谷駅の東口の前(地上)", visible="{名}、駅の地下への階段、タクシー乗り場",
           hour=16, minute=20, weather="雨、日照は日中", density="B", near="なし",
           extra=("[B3 体感] 傘を持っていません。服が少し濡れています。",),
           candidates=("{名}に入って雨がやむのを待つ", "駅の地下通路で待つ", "コンビニで傘を買って歩く",
                       "雨の中を走って帰る")),
    _scene("scramble_square", 4, kind="友人への贈り物を探している人", place="渋谷駅の東口の前(地上)",
           visible="{名}、銀座線の高架、宮益坂の入口", hour=14, minute=5, weather="曇、日照は日中", density="B",
           near="なし", extra=("[B3 予定] 贈り物の予算は5,000円ほどです。",),
           candidates=("{名}の店を見て回る", "宮益坂を上って小さな雑貨店を探す", "通販で買うことにして帰る")),
    _scene("scramble_square", 5, kind="友人と会う約束をした人", place="渋谷駅の改札の前(地上)",
           visible="{名}への通路、ハチ公の方角、改札", hour=19, minute=0, weather="晴、日照は夜", density="C",
           near="知らない人が大勢", extra=("[B3 予定] 友人に待ち合わせの場所を伝える必要があります。",),
           candidates=("{名}の入口を待ち合わせの場所にする", "ハチ公の前を待ち合わせの場所にする",
                       "この改札の前で待つ", "近くの喫茶店に入って待つ")),
    # ---- MIYASHITA PARK(施設)
    _scene("miyashita_park", 1, kind="小さな子どもを連れた親", place="明治通りの歩道(地上)",
           visible="{名}、宮下公園交差点、ビルの並び", hour=13, minute=30, weather="晴、日照は日中", density="B",
           near="自分の子どもがひとり", extra=("[B3 予定] 休日です。子どもが外で遊びたがっています。",),
           candidates=("{名}の屋上の公園で遊ばせる", "代々木公園まで歩く", "家に帰る", "喫茶店に入って休む")),
    _scene("miyashita_park", 2, kind="仕事を終えた会社員", place="明治通りの歩道(地上)",
           visible="{名}、渋谷駅の方角、居酒屋の看板", hour=19, minute=15, weather="曇、日照は夜", density="B",
           near="なし", extra=("[B3 予定] 少し飲んでから帰りたいと思っています。",),
           candidates=("{名}の飲食店の並ぶ通りに入る", "駅前の居酒屋に入る", "まっすぐ家に帰る",
                       "コンビニで飲み物を買って帰る")),
    _scene("miyashita_park", 3, kind="体を動かしたい大学生", place="明治通りの歩道(地上)",
           visible="{名}、歩道橋、自転車の駐輪場", hour=10, minute=40, weather="晴、日照は日中", density="A",
           near="なし", extra=("[B3 予定] 午後の授業まで時間があります。",),
           candidates=("{名}の運動の施設を使う", "代々木公園を走る", "大学の体育館へ行く", "家に帰る")),
    _scene("miyashita_park", 4, kind="原宿へ向かう観光客", place="渋谷駅の北側の歩道(地上)",
           visible="{名}、明治通り、山手線の高架", hour=11, minute=0, weather="晴、日照は日中", density="B",
           near="連れがひとり", extra=("[B3 予定] 原宿で昼食をとる予定です。",),
           candidates=("{名}の中を通り抜けて歩く", "明治通りの歩道を歩く", "山手線に一駅だけ乗る", "バスに乗る")),
    _scene("miyashita_park", 5, kind="出張で来た会社員", place="明治通りの歩道(地上)",
           visible="{名}、ホテルの案内、渋谷駅の方角", hour=21, minute=50, weather="小雨、日照は夜", density="A",
           near="なし", extra=("[B3 予定] 今夜泊まる場所をまだ決めていません。",),
           candidates=("{名}のホテルに空きがあるか聞く", "駅前のビジネスホテルを探す", "新宿まで移動して探す",
                       "終電で家に帰る")),
    # ---- 渋谷のハロウィン(出来事)
    _scene("halloween", 1, kind="渋谷の近くに住む若者", place="自宅の近くの路上(地上)",
           visible="大勢の人、渋谷駅の方角、コンビニ", hour=20, minute=30, weather="晴、日照は夜", density="C",
           near="友人がふたり", extra=("[B4 行為] 目につく出来事: 今夜は{名}の夜です。友人が一緒に行こうと誘っています。",),
           candidates=("交差点まで出かけて{名}に加わる", "誘いを断って家にいる", "友人の家に集まって過ごす",
                       "遠くから少し見て帰る")),
    _scene("halloween", 2, kind="センター街の飲食店の店長", place="店の前の路上(地上)",
           visible="店の入口、センター街、大勢の人", hour=17, minute=0, weather="曇、日照は夕方", density="C",
           near="店の従業員がふたり", extra=("[B4 行為] 目につく出来事: 今夜は{名}の夜です。",),
           candidates=("いつもどおり営業する", "{名}に合わせて早く店を閉める", "店の前に従業員を立てて営業する")),
    _scene("halloween", 3, kind="帰宅途中の会社員", place="渋谷駅の近くの歩道(地上)",
           visible="渋谷駅の入口、人の列、警察官", hour=21, minute=10, weather="晴、日照は夜", density="D",
           near="知らない人が大勢", extra=("[B4 行為] 目につく出来事: {名}で駅の周りが混んでいます。",),
           candidates=("このまま渋谷駅から帰る", "隣の駅まで歩いて帰る", "混雑が引くまで会社に戻って待つ",
                       "タクシーで帰る")),
    _scene("halloween", 4, kind="海外から来た観光客", place="ホテルのロビー(地上)",
           visible="フロント、ロビーの出口、案内の掲示", hour=19, minute=45, weather="晴、日照は夜", density="A",
           near="フロントの係員がひとり", extra=("[B4 行為] 目につく出来事: 今夜は{名}の夜だと聞きました。",),
           candidates=("{名}を見に出かける", "ホテルで過ごす", "別の街へ出かける")),
    _scene("halloween", 5, kind="宇田川町に住む人", place="自宅の玄関の前(地上)",
           visible="住宅の並び、センター街の方角、大勢の人", hour=22, minute=0, weather="晴、日照は夜", density="C",
           near="なし", extra=("[B3 予定] 明日の朝食の牛乳が切れています。", "[B4 行為] 目につく出来事: 今夜は{名}の夜です。"),
           candidates=("いまコンビニへ出かける", "明日の朝まで待つ", "{名}の人混みを避けて遠回りの道で出かける",
                       "家族に買い物を頼む")),
    # ---- 店名(6 店・1 店に 1 場面)
    _scene("shop_109", 1, kind="服を見たい高校生", place="道玄坂の下の歩道(地上)",
           visible="{名}、スクランブル交差点、道玄坂", hour=16, minute=30, weather="晴、日照は日中", density="C",
           near="同級生がひとり", extra=("[B3 予定] 使えるお金は3,000円です。",),
           candidates=("{名}に入って服を見る", "原宿まで歩いて店を探す", "駅ビルの店を見る", "通販で探すことにして帰る")),
    _scene("shop_parco", 1, kind="休日の会社員", place="公園通りの歩道(地上)",
           visible="{名}、映画館の看板、喫茶店", hour=15, minute=0, weather="曇、日照は日中", density="B",
           near="なし", extra=("[B3 予定] 美術とゲームが好きで、午後は空いています。",),
           candidates=("{名}の展示の階を見に行く", "映画館に入る", "喫茶店で本を読む", "家に帰る")),
    _scene("shop_loft", 1, kind="文房具を買いたい大学生", place="井の頭通りの歩道(地上)",
           visible="{名}、百円ショップ、宇田川町の通り", hour=17, minute=20, weather="晴、日照は夕方", density="B",
           near="なし", extra=("[B3 予定] 明日の発表に使うペンとノートが要ります。",),
           candidates=("{名}に入って選ぶ", "百円ショップで揃える", "大学の購買で明日買う", "通販で注文する")),
    _scene("shop_donki", 1, kind="ホテルに泊まっている観光客", place="井の頭通りの歩道(地上)",
           visible="{名}、コンビニ、ホテルの方角", hour=23, minute=40, weather="晴、日照は夜", density="B",
           near="なし", extra=("[B3 予定] 歯ブラシと充電の線を買い忘れました。",),
           candidates=("{名}に入る", "コンビニに入る", "ホテルの売店で聞く", "明日の朝に買う")),
    _scene("shop_hands", 1, kind="棚を手作りしたい会社員", place="井の頭通りの歩道(地上)",
           visible="{名}、宇田川町の通り、バスの停留所", hour=13, minute=0, weather="晴、日照は日中", density="B",
           near="なし", extra=("[B3 予定] 木材とねじと工具が要ります。",),
           candidates=("{名}で材料を揃える", "郊外のホームセンターまで行く", "通販で注文する", "知人に工具を借りる")),
    _scene("shop_shinqs", 1, kind="手土産を探している人", place="渋谷駅の東口の前(地上)",
           visible="{名}、駅の売店、宮益坂の入口", hour=11, minute=30, weather="晴、日照は日中", density="B",
           near="なし", extra=("[B3 予定] 午後に取引先を訪ねます。手土産の予算は3,000円ほどです。",),
           candidates=("{名}の食品の売り場で選ぶ", "駅の売店で選ぶ", "宮益坂の和菓子店で選ぶ", "手土産なしで訪ねる")),
)


BLOCK_ORDER: Final[tuple[str, ...]] = ("B0", "B1", "B2", "B3", "B4", "B4b", "B5", "B6")
_BLOCK_HEAD: Final[re.Pattern[str]] = re.compile(r"^\[(B\d+b?)[ \]]")


def block_sequence(input_text: str) -> list[str]:
    """``input_text`` のブロックの並び(dm_eval ``split_blocks`` と同じ規則=行の頭の ``[Bx …]``・続けて並び・
    ``BLOCK_ORDER`` の順)。規則に合わなければ ``ValueError``(dm_eval に依存しないための写し)。"""
    seq: list[str] = []
    for line in str(input_text).split("\n"):
        m = _BLOCK_HEAD.match(line)
        if m is None:
            if not seq:
                raise ValueError("最初の行にブロックの頭が無い")
            continue
        b = m.group(1)
        if b not in BLOCK_ORDER:
            raise ValueError(f"知らないブロック {b}")
        if seq and seq[-1] == b:
            continue
        if b in seq:
            raise ValueError(f"ブロック {b} が離れて 2 回出る")
        seq.append(b)
    if seq != [b for b in BLOCK_ORDER if b in seq]:
        raise ValueError(f"ブロックの並びが違う: {seq}")
    return seq


def choice_prompt(input_text: str, candidates: Sequence[Mapping[str, Any]]) -> str:
    """場面の文(ブロック)+候補(番号つき)+指示。番号は候補の並びの順に 1 から。"""
    lines = [str(input_text), "[候補]"]
    lines += [f"{i + 1}. {c['text']}" for i, c in enumerate(candidates)]
    lines.append(CHOICE_INSTRUCTION)
    return "\n".join(lines)


def build_type2() -> list[dict[str, Any]]:
    rows = []
    for sc in SCENES:
        target = sc["target"]
        group, real, fake = TARGETS[target]
        if not 3 <= len(sc["candidates"]) <= 6:
            raise ValueError(f"候補は 3〜6({target} {sc['n']})")
        pair_id = f"t2-{target}-{sc['n']:02d}"
        for variant, name in (("real", real), ("fictional", fake)):
            cands = [{"id": f"c{i + 1}", "text": str(t).replace(NAME_SLOT, name), "mentions_name": NAME_SLOT in t}
                     for i, t in enumerate(sc["candidates"])]
            text = str(sc["template"]).replace(NAME_SLOT, name)
            block_sequence(text)
            rows.append({
                "sid": f"{pair_id}-{variant}", "pair_id": pair_id, "variant": variant, "target": target,
                "target_group": TARGET_GROUP[target], "target_kind": group, "name": name, "lang": "ja",
                "judgment_kind": "候補から 1 つ選ぶ(番号)", "input_text": text, "input_missing": ["B5", "B6"],
                "facts": {"hour": sc["hour"], "minute": sc["minute"], "density": sc["density"]},
                "strata": {"kind": sc["kind"]}, "candidates": cands, "prompt": choice_prompt(text, cands),
            })
    return rows


# ---------------------------------------------------------------------------------------------- 型 ④
RECALL_TEMPLATES: Final[tuple[tuple[str, str], ...]] = (
    ("guided", "次の文章は『{name}』の冒頭の一部です。元の文章のとおりに、この続きを書いてください。"
               "説明は付けず、続きの文だけを書いてください。\n冒頭: {prefix}"),
    ("general", "次の文章の冒頭に続く文を書いてください。説明は付けず、続きの文だけを書いてください。\n冒頭: {prefix}"),
)


def build_type4() -> list[dict[str, Any]]:
    return [{"template_id": tid, "type": 4, "lang": "ja", "template": t,
             "basis": "Golchin & Surdeanu ICLR 2024(arXiv 2308.08493)の guided / general instruction"}
            for tid, t in RECALL_TEMPLATES]


# ---------------------------------------------------------------------------------------------- 書き出しと読み
BUILDERS: Final[Mapping[str, Any]] = {
    TYPE1_DATES_NAME: build_type1_dates, TYPE1_EVENTS_NAME: build_type1_events, TYPE2_NAME: build_type2,
    TYPE4_NAME: build_type4,
}


def to_jsonl(rows: Sequence[Mapping[str, Any]]) -> bytes:
    """行の並びのまま 1 行 1 件(utf-8・LF・鍵は書いた順)。"""
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")


def lf_md5(raw: bytes) -> str:
    """改行を LF にそろえた md5(作業木の改行の変換に左右されない)。"""
    return hashlib.md5(raw.replace(b"\r\n", b"\n")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    return [json.loads(line) for line in raw.split("\n") if line.strip()]


def load_set(name: str, directory: Path | None = None) -> tuple[list[dict[str, Any]], str]:
    """問いの集合を読む(行と LF の md5)。"""
    if name not in BUILDERS:
        raise ValueError(f"知らない問いの集合 {name!r}")
    p = Path(directory or SETS_DIR) / name
    raw = p.read_bytes()
    return read_jsonl(p), lf_md5(raw)


def write_sets(directory: Path | None = None) -> dict[str, int]:
    d = Path(directory or SETS_DIR)
    d.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, fn in BUILDERS.items():
        rows = fn()
        (d / name).write_bytes(to_jsonl(rows))
        out[name] = len(rows)
    return out


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="leak_check の問いの集合を作る")
    ap.add_argument("--write", action="store_true", help="question_sets/ に書く(無ければ件数だけ出す)")
    a = ap.parse_args(argv)
    if a.write:
        counts = write_sets()
    else:
        counts = {name: len(fn()) for name, fn in BUILDERS.items()}
    for name, n in counts.items():
        print(f"{name}\t{n}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
