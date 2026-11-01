# -*- coding: utf-8 -*-
"""消費の場面 v1 を作る(再現用・〔11-01 段 1 の 3〕)。**正は同梱の jsonl と md5**で、このスクリプトはそれを作り直す道具。

決定的(乱数も時計も使わない): 同じ版のこのスクリプトは、同じ ``consumption_v1.jsonl``・``.b0.json``・``.md5`` の
バイトを出す(試験 ``test_make_consumption_v1_reproduces_the_shipped_files`` が照らす)。店・品・人は架空・値段は丸い
仮の値・語彙は v3・判断に要る事実は短い版に入る B6 に置く(設計は ``docs/bench/analysis/dm-eval-11-01/README.md`` §2)。

使い方(リポの根で)::

    python tools/instruments/dm_eval/scenes/make_consumption_v1.py <出力の dir>

出力の dir に 3 本を書く(既にあれば上書き)。同梱の場面を変えるときは、ここを直して作り直し、試験と md5 を更新する。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

NAME = "consumption_v1"
B0_ID = "cons-v1-b0"
B0 = "\n".join([
    "あなたは街で暮らす一人の人物です。ここに並ぶ観測は、あなたがいま気づいている事実のすべてです。",
    "観測に無いことは知りません。分からないことを、分かったことのように扱わないでください。",
    "[役割知識] 支払いは所持金の範囲でしかできません。",
    "[役割知識] 値札の値段は税込みです。",
    "[役割知識] 買わずに店を離れることも、別の店を探すこともできます。",
    "[役割知識] 頭に浮かんだことの中から、いまの自分に合うものを一つ選びます。",
])

def band(h):
    lo = (int(h) // 4) * 4  # 1-10 と同じ区切り(00-03 … 20-23)
    return f"{lo:02d}-{lo + 3:02d}"


def common(kind, shop, place_line, visible, tags, hour, minute, weather, heat, density, salient, outside=False):
    lines = [
        f"[B1 種別] あなたは{kind}です。",
        f"[B2 場所] 現在地は{shop}の中(地上)です。" if place_line is None else place_line,
        f"[B2 可視] 見えるもの: {visible}。",
    ]
    for t in tags:
        lines.append(f"[B2 値札] 〔素性: 店頭表示・命令文除去済〕{t}")
    lines += [
        f"[B3 時刻] 現在時刻は{hour}時{minute}分です。",
        f"[B3 天候] 天候は{weather}です。",
        f"[B3 体感] 暑さは{heat}です。",
        f"[B4 密度] 歩行者密度は段階{density}です。" if outside else f"[B4 密度] 店内の混み具合は段階{density}です。",
        f"[B4 行為] 目につく出来事: {salient}。" if salient else "[B4 行為] 目につく出来事はありません。",
        "[B4b 近景] 25メートル以内: 通行人。" if outside else "[B4b 近景] 25メートル以内: 店員、ほかの客。",
    ]
    return lines


def b6(reason, money, hunger, memory=None, result=None, hands="ふさがっていません"):
    # 判断に要る事実(所持金・体・事情・直前の結果)は短い版に入る B6 に置く(検収 高 1 (a))
    lines = [f"[B6 起床] {reason}", f"[B6 所持] 所持金は{money}円です。手は{hands}。", f"[B6 体] {hunger}"]
    if memory:
        lines.append(f"[B6 事情] {memory}")
    if result:
        lines.append(f"[B6 結果] {result}")
    lines.append("[B6 問い] いま何をしますか。")
    return lines


def add(rows, point, n, kind, hour, minute, shop, visible, tags, items, money, hunger, cands, *, weather="晴れ",
        heat="ふつう", density="B", salient=None, memory=None, reason, result=None, place_line=None, extra=None,
        outside=False):
    sid = f"cons-v1-{point}-{n:02d}"
    lines = common(kind, shop, place_line, visible, tags, hour, minute, weather, heat, density, salient, outside)
    lines += b6(reason, money, hunger, memory, result)
    facts = {"hour": hour, "minute": minute, "decision_point": point, "shop_kind": shop, "items": items,
             "money_yen": money, "hunger": hunger, "shop_word": True, "station_word_or_band": False,
             "weather": weather, "heat": heat, "density": density}
    if extra:
        facts.update(extra)
    rows.append({
        "sid": sid, "point": point, "lang": "ja", "b0_id": B0_ID, "input_text": "\n".join(lines),
        "input_missing": ["B5"], "facts": facts, "vocab": "v3",
        "strata": {"heat": heat, "kind": kind, "scene": "店の前" if outside else "店の中", "time_band": band(hour),
                   "wake": "-1 消費の契機"},
        "agent_id": -1, "wake_class": -1, "call_id": sid, "tape": "", "output": "",
        "candidates": cands,
    })


def C(cid, kind, text, source, **kw):
    d = {"id": cid, "kind": kind, "text": text, "source": source}
    d.update(kw)
    return d


# ------------------------------------------------------------------ 判断点 1 買うか見送るか
BUY_REASON = "棚の前で品を手に取ったため、次の行動を決める必要があります。"


def buy_cands(item, price):
    return [
        C("buy", "購入", f"{item}を買う", "affordance", item=item, qty=1, price_yen=price),
        C("skip", "buy_skip", "見送る(今回は買わずに棚に戻す)", "continue"),
        C("look", "なし", "もう少し店の中を見て回る", "continue"),
        C("leave", "移動", "店を出て別の店をのぞく", "affordance"),
        C("ask", "会話", "店員に品のことを尋ねる", "affordance"),
        C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate"),
    ]


P1 = [
    ("来街者", 12, 10, "コンビニ", "おにぎりの棚、飲み物の冷蔵庫", "おにぎり", 150, 3000, "お腹がすいています。", {}),
    ("通勤者", 7, 50, "パン屋", "焼きたてのパンの棚、レジ", "食パン", 300, 2000, "少しお腹がすいています。", {}),
    ("居住者", 19, 30, "八百屋", "野菜の箱、果物の台", "トマトの袋", 400, 5000, "体調に変わりはありません。", {}),
    ("来街者", 15, 0, "雑貨店", "食器の棚、文房具の棚", "マグカップ", 1500, 8000, "体調に変わりはありません。", {}),
    ("従業者", 21, 40, "ドラッグストア", "目薬の棚、日用品の棚", "目薬", 800, 1500, "少し疲れています。",
     {"salient": "レジに短い列"}),
    ("来街者", 14, 20, "書店", "文庫本の棚、雑誌の台", "文庫本", 900, 4000, "体調に変わりはありません。", {}),
    ("居住者", 10, 30, "花屋", "切り花の桶、鉢植えの棚", "小さな花束", 1200, 3000, "体調に変わりはありません。", {}),
    ("通勤者", 18, 50, "惣菜店", "弁当の棚、揚げ物のケース", "唐揚げ弁当", 600, 1000, "とてもお腹がすいています。",
     {"salient": "店員が値引きのシールを貼っている"}),
    ("来街者", 16, 40, "喫茶店の持ち帰りの窓口", "飲み物の品書き、焼き菓子の皿", "アイスコーヒー", 450, 2500,
     "のどが渇いています。", {"heat": "暑い"}),
    ("来街者", 13, 0, "衣料品店", "シャツの棚、試着室", "長袖のシャツ", 3000, 6000, "体調に変わりはありません。", {}),
    ("居住者", 20, 15, "菓子店", "焼き菓子の棚、ケーキのケース", "焼き菓子の詰め合わせ", 1000, 2000,
     "体調に変わりはありません。", {"density": "A"}),
]

# ------------------------------------------------------------------ 判断点 2 何をいくつ
QTY_REASON = "買う品の前に立ったため、次の行動を決める必要があります。"


def qty_cands(a, pa, qs, b, pb):
    out = [C(f"a{q}", "購入", f"{a}を{q}つ買う" if q < 10 else f"{a}を{q}個買う", "affordance",
             item=a, qty=q, price_yen=pa) for q in qs]
    out.append(C("b1", "購入", f"{b}を1つ買う", "affordance", item=b, qty=1, price_yen=pb))
    out.append(C("skip", "buy_skip", "見送る(今回は何も買わずに離れる)", "continue"))
    out.append(C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate"))
    return out


P2 = [
    ("来街者", 8, 20, "パン屋", "クロワッサン", 200, (1, 2, 3), "食パン", 300, 2000, "少しお腹がすいています。", None),
    ("通勤者", 12, 30, "コンビニ", "おにぎり", 150, (1, 2, 3), "サンドイッチ", 300, 1500, "お腹がすいています。", None),
    ("居住者", 17, 40, "八百屋", "りんご", 100, (1, 3, 5), "みかんの袋", 400, 3000, "体調に変わりはありません。",
     "家で家族と食べることが多い。"),
    ("来街者", 11, 0, "文具店", "ボールペン", 100, (1, 2, 5), "ノート", 200, 2500, "体調に変わりはありません。", None),
    ("従業者", 15, 10, "ドラッグストア", "水のペットボトル", 100, (1, 2, 6), "スポーツ飲料", 150, 1200,
     "のどが渇いています。", None),
    ("居住者", 16, 30, "菓子店", "シュークリーム", 250, (1, 2, 4), "ショートケーキ", 450, 3000,
     "体調に変わりはありません。", "週末に来客の予定がある。"),
    ("通勤者", 19, 0, "弁当店", "幕の内弁当", 600, (1, 2, 3), "おにぎり", 150, 2500, "お腹がすいています。",
     "家に待っている人がいる。"),
    ("居住者", 10, 50, "花屋", "切り花", 300, (1, 3, 5), "小さな鉢植え", 1000, 4000, "体調に変わりはありません。", None),
    ("来街者", 18, 20, "惣菜店", "コロッケ", 100, (1, 2, 4), "メンチカツ", 150, 1000, "お腹がすいています。", None),
    ("居住者", 13, 40, "雑貨店", "電池のパック", 200, (1, 2, 4), "延長コード", 1000, 5000, "体調に変わりはありません。",
     "家の時計と懐中電灯の電池が切れている。"),
    ("従業者", 9, 50, "喫茶店の持ち帰りの窓口", "ホットコーヒー", 400, (1, 2, 3), "クッキー", 200, 3000,
     "少し眠気があります。", "職場の同僚に頼まれることがある。"),
]

# ------------------------------------------------------------------ 判断点 3 値段を見て見送る
PRICE_REASON = "値札を見たため、次の行動を決める必要があります。"


def price_cands(a, pa, b, pb):
    return [
        C("buy", "購入", f"{a}を値段どおり買う", "affordance", item=a, qty=1, price_yen=pa),
        C("price_skip", "price_skip", "値段を見て見送る(買わずにやめる)", "continue"),
        C("cheaper", "購入", f"安いほうの{b}を買う", "affordance", item=b, qty=1, price_yen=pb),
        C("elsewhere", "移動", "別の店で探す", "affordance"),
        C("look", "なし", "もう少し棚を見ながら迷う", "continue"),
        C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate"),
    ]


P3 = [
    ("来街者", 17, 30, "コンビニ", "ビニール傘", 1000, "小さな折りたたみ傘", 800, 3000, "体調に変わりはありません。",
     "前に別の店でビニール傘を500円で買った。", {"weather": "雨"}),
    ("通勤者", 12, 40, "弁当店", "特製の弁当", 1200, "おにぎり", 150, 1500, "お腹がすいています。",
     "いつもの昼は500円ほどで済ませている。", {}),
    ("従業者", 22, 10, "ドラッグストア", "栄養ドリンク", 500, "お茶のペットボトル", 150, 2000, "疲れています。", None, {}),
    ("居住者", 18, 0, "果物店", "メロン", 3000, "バナナ", 200, 5000, "体調に変わりはありません。",
     "見舞いに行く予定がある。", {}),
    ("来街者", 14, 50, "書店", "新刊の単行本", 2000, "文庫本", 800, 2500, "体調に変わりはありません。",
     "読みたかった本の新刊が出ていた。", {}),
    ("居住者", 11, 20, "コーヒー豆の店", "コーヒー豆の袋", 1500, "ドリップのパック", 500, 4000,
     "体調に変わりはありません。", "いつもはスーパーで1000円の豆を買う。", {}),
    ("来街者", 13, 30, "ドラッグストア", "日焼け止め", 1800, "小さな日焼け止め", 900, 2000, "体調に変わりはありません。",
     None, {"heat": "暑い"}),
    ("来街者", 16, 0, "衣料品店", "Tシャツ", 4000, "無地のTシャツ", 1500, 5000, "体調に変わりはありません。", None, {}),
    ("従業者", 12, 15, "定食屋の入口", "日替わりの定食", 1500, "小盛りの定食", 800, 1800, "お腹がすいています。",
     "同じ通りの定食は1000円ほどだった。", {"place_line": "[B2 場所] 現在地は定食屋の入口(地上)です。"}),
    ("居住者", 19, 45, "菓子店", "ケーキ", 600, "焼き菓子", 200, 800, "体調に変わりはありません。", None, {}),
    ("通勤者", 8, 40, "家電の小売店", "充電ケーブル", 2500, "短い充電ケーブル", 1000, 3000, "体調に変わりはありません。",
     "スマートフォンの電池が残り少ない。", {}),
]

# ------------------------------------------------------------------ 判断点 4 満足して同じ店にまた行くか
REVISIT_REASON = "店を出たため、次の行動を決める必要があります。"


def revisit_cands():
    return [
        C("again", "revisit", "また行く(この店にまた来る)", "experience"),
        C("not_again", "no_revisit", "また行かない(次は別の店にする)", "experience"),
        C("tell", "会話", "店の人に感想を伝える", "affordance"),
        C("go_on", "移動", "ひとまず次の行き先へ向かう", "continue"),
        C("wait", "なし", "店の前で少し休む", "continue"),
        C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate"),
    ]


P4 = [
    ("来街者", 13, 10, "定食屋", "食事", "料理は温かく、待たずに座れました。値段は900円でした。", "満腹です。", 2000),
    ("通勤者", 20, 30, "ラーメン店", "食事", "味は好みでしたが、店の前で長く待ちました。値段は1000円でした。",
     "満腹です。", 3000),
    ("来街者", 15, 40, "喫茶店", "食事", "店は静かで、飲み物はぬるかったです。値段は500円でした。",
     "体調に変わりはありません。", 2500),
    ("居住者", 9, 20, "パン屋", "購入", "目当てのパンは売り切れで、別のパンを買いました。値段は300円でした。",
     "少しお腹がすいています。", 4000),
    ("来街者", 17, 0, "美容室", "利用", "仕上がりは希望どおりでした。値段は5000円でした。", "体調に変わりはありません。", 3000),
    ("来街者", 12, 50, "回転ずしの店", "食事", "皿の回りが遅く、店員の対応はていねいでした。値段は1500円でした。",
     "満腹です。", 1500),
    ("居住者", 14, 30, "古着屋", "購入", "欲しい品が見つからず、靴下だけ買いました。値段は500円でした。",
     "体調に変わりはありません。", 6000),
    ("従業者", 19, 10, "カレー店", "食事", "とてもおいしかったですが、値段は1800円で高めでした。", "満腹です。", 2000),
    ("通勤者", 12, 20, "そば店", "食事", "早く出てきましたが、店員の対応は冷たく感じました。値段は700円でした。",
     "満腹です。", 2500),
    ("居住者", 16, 10, "ケーキ店", "購入", "ケーキはおいしかったですが、家から遠い店です。値段は600円でした。",
     "体調に変わりはありません。", 3500),
    ("来街者", 21, 0, "焼き鳥の店", "食事", "席がせまく、煙が服についてしまいました。値段は2500円でした。",
     "満腹です。", 1000),
]

def build_rows() -> list[dict]:
    """場面の行(並びは判断点の順 → 番号の順)。"""
    rows: list[dict] = []
    for i, (kind, h, m, shop, vis, item, price, money, hunger, kw) in enumerate(P1, 1):
        add(rows, "buy_or_skip", i, kind, h, m, shop, vis, [f"{item} {price}円"],
            [{"name": item, "price_yen": price}], money, hunger, buy_cands(item, price), reason=BUY_REASON, **kw)
    for i, (kind, h, m, shop, a, pa, qs, b, pb, money, hunger, mem) in enumerate(P2, 1):
        vis = f"{a}の棚、{b}の棚、レジ"
        add(rows, "what_how_many", i, kind, h, m, shop, vis, [f"{a} 1つ{pa}円", f"{b} 1つ{pb}円"],
            [{"name": a, "price_yen": pa}, {"name": b, "price_yen": pb}], money, hunger, qty_cands(a, pa, qs, b, pb),
            memory=mem, reason=QTY_REASON, extra={"qty_options": list(qs)})
    for i, (kind, h, m, shop, a, pa, b, pb, money, hunger, mem, kw) in enumerate(P3, 1):
        vis = f"{a}の棚、{b}の棚"
        add(rows, "price_skip", i, kind, h, m, shop, vis, [f"{a} {pa}円", f"{b} {pb}円"],
            [{"name": a, "price_yen": pa}, {"name": b, "price_yen": pb}], money, hunger, price_cands(a, pa, b, pb),
            memory=mem, reason=PRICE_REASON, **kw)
    for i, (kind, h, m, shop, act, impression, hunger, money) in enumerate(P4, 1):
        add(rows, "revisit", i, kind, h, m, shop, "店の出口、通り", [], [], money, hunger, revisit_cands(),
            reason=REVISIT_REASON, result=f"直前の{act}は成功しました。{impression}",
            place_line=f"[B2 場所] 現在地は{shop}の前(地上)です。",
            extra={"impression": impression, "shop_word": True}, outside=True)
    return rows


def render_files() -> dict[str, bytes]:
    """書き出す 3 本の名 → バイト(LF・UTF-8・鍵の順は固定)。"""
    rows = build_rows()
    jl = ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n").encode("utf-8")
    b0 = (json.dumps({"b0_texts": {B0_ID: B0}, "name": NAME, "note": "消費の場面 v1 の前置き(自前・架空)"},
                     ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")
    md5 = (f"{hashlib.md5(jl).hexdigest()}  {NAME}.jsonl\n"
           f"{hashlib.md5(b0).hexdigest()}  {NAME}.b0.json\n").encode("utf-8")
    return {f"{NAME}.jsonl": jl, f"{NAME}.b0.json": b0, f"{NAME}.md5": md5}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    if len(args) != 1:
        print("使い方: make_consumption_v1.py <出力の dir>")
        return 2
    out = Path(args[0])
    out.mkdir(parents=True, exist_ok=True)
    files = render_files()
    for name, raw in files.items():
        (out / name).write_bytes(raw)
    print(files[f"{NAME}.md5"].decode("utf-8"), end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
