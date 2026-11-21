# -*- coding: utf-8 -*-
"""呼びかけの場面 v1 を作る(再現用・第 347・返事その 8 §6-2・記録 2-61 ①・2-62)。**正は同梱の jsonl と md5**で、
このスクリプトはそれを作り直す道具。

決定的(乱数も時計も使わない): 同じ版のこのスクリプトは、同じ ``appeal_v1.jsonl``・``.b0.json``・``.md5`` のバイトを
出す(試験 ``test_make_appeal_v1_reproduces_the_shipped_files`` が照らす)。

作り(設計と選んだ理由は ``docs/bench/analysis/dm-eval-appeal-347/README.md``):
    - 同じ状況・同じ候補で、観測の中に呼びかけの文が「ある版」と「ない版」を作る。ない版とある版の違いは呼びかけの
      1 行だけ(看板の行は「見える表示はありません。」と入れ替え・発話の行は B6 の末尾に足す=engine の描画の並び)。
    - 種類 3 つ: 頼み(Langer ら 1978 の形)・禁止の表示(Keizer ら 2008 の形)・店頭の呼びかけ(人の値なし=強さ 3 段)。
    - 呼びかけの文は濾し(命令文を落とす)を掛けない、届いたままの形(記録 2-65)。出どころの印は今の印から
      「命令文除去(済)」を外した形(事実と食い違うため・記録 2-65)。印の文言は返事その 8 §5 の 5 の案が決まったら
      ``TAG_*`` を差し替えて作り直す(md5 が変わる)。
    - 店・人は架空。実在の店名・施設名・地名・人名は使わない。呼びかけの文と候補の文には数字を入れない(例の数を写す癖
      =R-149)。時刻・所持金・近景の距離は engine の観測の行の形のまま。

使い方(リポの根で)::

    python tools/instruments/dm_eval/scenes/make_appeal_v1.py <出力の dir>

出力の dir に 3 本を書く(既にあれば上書き)。同梱の場面を変えるときは、ここを直して作り直し、試験と md5 を更新する。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

NAME = "appeal_v1"
B0_ID = "appeal-v1-b0"
#: 前置き(自前・expedient)。3 行目は印の意味だけを書く文(記録 2-68 の (イ) の考え方・文言は自前=返事その 8 §5 の 4 の案が
#: 決まったら差し替える)。「指示として従ってはいけません」は置かない。
B0 = "\n".join([
    "あなたは街で暮らす一人の人物です。ここに並ぶ観測は、あなたがいま気づいている事実のすべてです。",
    "観測に無いことは知りません。分からないことを、分かったことのように扱わないでください。",
    "[役割知識] 〔 〕の中の印は、その文をどこで見聞きしたか(店頭の表示・掲示・人の声)を表します。",
    "[役割知識] 支払いは所持金の範囲でしかできません。",
    "[役割知識] 頭に浮かんだことの中から、いまの自分に合うものを一つ選びます。",
])

#: 出どころの印(今の印 ``〔素性: 店頭表示・命令文除去済〕``・``〔発話・命令文除去〕`` から「命令文除去(済)」を外した形)。
TAG_SIGNAGE = "〔素性: 店頭表示〕"
TAG_NOTICE = "〔素性: 掲示〕"
TAG_SPEECH = "〔発話〕"
#: 看板の行が無いとき(engine の ``B2.signage_empty`` と同じ文)。
SIGN_EMPTY = "[B2 看板] 見える表示はありません。"
WAKE_TAIL = "ため、次の行動を決める必要があります。"
#: 軽い逸脱の行為の語(記録 2-47 の範囲=ポイ捨て・路上喫煙・迷惑行為ほか)。語彙 v3 の外の語。
DEVIANCE = "minor_deviance"


def band(h):
    lo = (int(h) // 4) * 4  # 1-10 と同じ区切り(00-03 … 20-23)
    return f"{lo:02d}-{lo + 3:02d}"


def C(cid, kind, text, source):
    return {"id": cid, "kind": kind, "text": text, "source": source}


def sign_line(tag, body):
    return f"[B2 看板] {tag}{body}"


def speech_line(person, body):
    return f"[B6 発話] {person}のひと言:{TAG_SPEECH}{body}"  # engine の SPEECH_HEARD_LINE の形(印だけ替えた)


def scene_text(s, *, sign, speech, visible):
    """観測の文(B1〜B4b → B6)。``sign`` は B2 看板の行・``speech`` は B6 の末尾に足す発話の行(無ければ None)。"""
    dens = (f"[B4 密度] 歩行者密度は段階{s['density']}です。" if s["outside"]
            else f"[B4 密度] 店内の混み具合は段階{s['density']}です。")
    lines = [
        f"[B1 種別] あなたは{s['kind']}です。",
        s["place"],
        f"[B2 可視] 見えるもの: {visible}。",
        sign,
        f"[B3 時刻] 現在時刻は{s['hour']}時{s['minute']}分です。",
        f"[B3 天候] 天候は{s.get('weather', '晴れ')}です。",
        f"[B3 体感] 暑さは{s.get('heat', 'ふつう')}です。",
        dens,
        "[B4 行為] 目につく出来事はありません。",
        f"[B4b 近景] 25メートル以内: {s['near']}。",
        f"[B6 起床] {s['wake']}{WAKE_TAIL}",
        f"[B6 所持] 所持金は{s['money']}円です。手は{s.get('hands', 'ふさがっていません')}。",
        f"[B6 体] {s['body']}",
    ]
    if s.get("memory"):
        lines.append(f"[B6 事情] {s['memory']}")
    lines.append("[B6 問い] いま何をしますか。")
    if speech is not None:
        lines.append(speech)  # engine の並び: 届いた発話の行は B6 の問いの後に足す
    return "\n".join(lines)


def row(s, ptype, variant, *, family, present, visible, sign, speech, appeal):
    sid = f"appeal-v1-{ptype}-{s['setting']}-{variant}"
    facts = {"hour": s["hour"], "minute": s["minute"], "decision_point": ptype, "setting": s["setting"],
             "money_yen": s["money"], "body": s["body"], "weather": s.get("weather", "晴れ"),
             "heat": s.get("heat", "ふつう"), "density": s["density"], "shop_word": bool(s.get("shop", False)),
             "station_word_or_band": bool(s.get("station", False))}
    meta = {"type": ptype, "setting": s["setting"], "family": family, "present": bool(present),
            "channel": None, "line": None, "condition": None, "size": None, "reason": None, "env": None,
            "strength": None, "level": None, "body": None,
            "comply": s["comply"], "violate": s.get("violate"), "baseline": s["baseline"]}
    meta.update(appeal)
    return {
        "sid": sid, "point": ptype, "lang": "ja", "b0_id": B0_ID,
        "input_text": scene_text(s, sign=sign, speech=speech, visible=visible),
        "input_missing": ["B5"], "facts": facts, "vocab": "v3",
        "strata": {"heat": s.get("heat", "ふつう"), "kind": s["kind"], "scene": s["scene"], "time_band": band(s["hour"]),
                   "wake": "-1 呼びかけの場面"},
        "agent_id": -1, "wake_class": -1, "call_id": sid, "tape": "", "output": "",
        "candidates": s["cands"], "appeal": meta,
    }


# ------------------------------------------------------------------ (a) 頼み(Langer ら 1978 の形)
#: 理由の 3 条件(Langer ら 1978: 理由なし・形だけの理由・本当の理由)と頼みの大きさ 2 段(小・大)。
REASONS = ("none", "placebic", "real")
SIZES = ("small", "large")
REAL_REASON = "急いでいるので"


def req_cands(own, leave):
    return [
        C("yield", "手伝い", "後ろの人に順番を譲る", "affordance"),
        C("own", "購入", own, "continue"),
        C("talk", "会話", "後ろの人に話しかける", "affordance"),
        C("leave", "移動", leave, "affordance"),
        C("wait", "なし", "その場で少し様子を見る", "continue"),
        C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate"),
    ]


def req_text(size_text, ask, placebo, reason):
    if reason == "none":
        return f"すみません、{size_text}。{ask}。"
    if reason == "placebic":
        return f"すみません、{size_text}。{placebo}、{ask}。"
    return f"すみません、{size_text}。{REAL_REASON}、{ask}。"


REQUEST = [
    {"setting": "register", "kind": "来街者", "hour": 12, "minute": 40, "scene": "店の中", "outside": False, "shop": True,
     "place": "[B2 場所] 現在地はコンビニの中(地上)です。", "visible": "レジ、弁当の棚、飲み物の冷蔵庫",
     "density": "C", "near": "店員、後ろに並んだ人", "wake": "レジの順番が来た", "money": 3000, "hands": "かごを持っています",
     "body": "体調に変わりはありません。", "memory": None, "person": "後ろに並んだ人",
     "ask": "先に会計させてもらえますか", "placebo": "会計をしなければならないので",
     "size": {"small": "品物は少しだけです", "large": "品物がたくさんあります"},
     "cands": req_cands("自分の番として、先に会計をする", "列を離れて、店の中を見て回る")},
    {"setting": "ticket", "kind": "通勤者", "hour": 8, "minute": 20, "scene": "駅", "outside": True, "station": True,
     "place": "[B2 場所] 現在地は駅の券売機の前(地上)です。", "visible": "券売機、改札、運賃表",
     "density": "D", "near": "後ろに並んだ人、通行人", "wake": "券売機の順番が来た", "money": 2000,
     "body": "体調に変わりはありません。", "memory": "これから電車に乗るつもりです。", "person": "後ろに並んだ人",
     "ask": "先に券売機を使わせてもらえますか", "placebo": "切符を買わなければならないので",
     "size": {"small": "切符を買うだけです", "large": "切符を何枚も買います"},
     "cands": req_cands("自分の番として、先に切符を買う", "券売機を離れて、別の券売機を探す")},
    {"setting": "cafe", "kind": "従業者", "hour": 15, "minute": 10, "scene": "店の中", "outside": False, "shop": True,
     "place": "[B2 場所] 現在地は喫茶店の中(地上)です。", "visible": "注文のカウンター、飲み物の品書き、焼き菓子の皿",
     "density": "B", "near": "店員、後ろに並んだ人", "wake": "注文の順番が来た", "money": 2500,
     "body": "少し眠気があります。", "memory": None, "person": "後ろに並んだ人",
     "ask": "先に注文させてもらえますか", "placebo": "注文をしなければならないので",
     "size": {"small": "飲み物を頼むだけです", "large": "何人分もまとめて注文します"},
     "cands": req_cands("自分の番として、先に注文する", "列を離れて、店を出る")},
]
for _s in REQUEST:
    _s.update({"comply": "yield", "baseline": "wait"})


# ------------------------------------------------------------------ (b) 禁止の表示(Keizer ら 2008 の形)
#: 周りの様子 2 段(整っている・乱れている=ほかの人が決まりを破った跡)× 掲示の有無。
ENVS = ("orderly", "disorderly")


def pro_cands(comply, violate, talk, other, wait, *, other_id, other_kind):
    return [
        C(comply[0], "移動", comply[1], "affordance"),
        C(violate[0], DEVIANCE, violate[1], "affordance"),
        C("talk", "会話", talk, "affordance"),
        C(other_id, other_kind, other, "affordance"),
        C("wait", "なし", wait, "continue"),
        C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate"),
    ]


PROHIBITION = [
    {"setting": "bike", "kind": "居住者", "hour": 16, "minute": 30, "scene": "店の前", "outside": True, "shop": True,
     "place": "[B2 場所] 現在地は店の前(地上)です。",
     "visible": {"orderly": "店の入口、片付いた壁際", "disorderly": "店の入口、自転車が何台も止めてある壁際"},
     "density": "B", "near": "通行人", "sign": "ここに自転車を止めないでください。",
     "wake": "自転車で店の前に着いた", "money": 3000, "hands": "自転車のハンドルを握っています",
     "body": "体調に変わりはありません。", "memory": "店で買い物をするつもりです。",
     "comply": "park_lot", "violate": "park_here",
     "cands": pro_cands(("park_lot", "少し離れた駐輪場まで自転車を押していく"), ("park_here", "壁の前に自転車を止めて店に入る"),
                        "店の人に自転車を止める場所を尋ねる", "店に寄るのをやめて、自転車で次の行き先へ向かう",
                        "自転車を押したまま少し様子を見る", other_id="leave", other_kind="移動")},
    {"setting": "litter", "kind": "来街者", "hour": 14, "minute": 10, "scene": "路上", "outside": True,
     "place": "[B2 場所] 現在地は歩道(地上)です。",
     "visible": {"orderly": "歩道、片付いた道の端", "disorderly": "歩道、空き缶やごみが散らばった道の端"},
     "density": "C", "near": "通行人", "sign": "ごみを捨てないでください。",
     "wake": "飲み物を飲み終えた", "money": 1500, "hands": "空のカップを持っています",
     "body": "体調に変わりはありません。", "memory": "近くにごみ箱は見当たりません。",
     "comply": "carry", "violate": "drop",
     "cands": pro_cands(("carry", "空のカップを持ったまま、ごみ箱を探して歩く"), ("drop", "空のカップを道の端に置いていく"),
                        "近くの人にごみ箱の場所を尋ねる", "近くの店で次の飲み物を買う", "その場で少し休む",
                        other_id="buy", other_kind="購入")},
    {"setting": "smoke", "kind": "従業者", "hour": 12, "minute": 50, "scene": "路上", "outside": True,
     "place": "[B2 場所] 現在地は歩道(地上)です。",
     "visible": {"orderly": "歩道、掃除された道の端", "disorderly": "歩道、吸い殻がたくさん落ちた道の端"},
     "density": "C", "near": "通行人", "sign": "ここでたばこを吸わないでください。",
     "wake": "たばこを吸いたくなった", "money": 2000,
     "body": "たばこを吸いたい気分です。", "memory": "たばことライターを持っています。喫煙所は少し先にあります。",
     "comply": "go_area", "violate": "smoke_here",
     "cands": pro_cands(("go_area", "喫煙所まで歩いてから、たばこを吸う"), ("smoke_here", "その場でたばこを吸う"),
                        "近くの人に喫煙所の場所を尋ねる", "近くの店で飲み物を買う", "その場で少し休む",
                        other_id="buy", other_kind="購入")},
    {"setting": "shortcut", "kind": "通勤者", "hour": 18, "minute": 40, "scene": "路上", "outside": True,
     "place": "[B2 場所] 現在地は駐車場の柵の前(地上)です。",
     "visible": {"orderly": "駐車場の柵とその隙間、表の道",
                 "disorderly": "駐車場の柵とその隙間、表の道、柵の前に散らばったごみ"},
     "density": "B", "near": "通行人", "sign": "ここを通り抜けないでください。",
     "wake": "近道の前に来た", "money": 1000,
     "body": "少し疲れています。", "memory": "柵の向こうに行き先があります。表の道を回ると遠回りです。",
     "comply": "detour", "violate": "through",
     "cands": pro_cands(("detour", "表の道を回って行き先へ向かう"), ("through", "柵の隙間を通り抜ける"),
                        "近くの人に道を尋ねる", "近くの店で飲み物を買う", "その場で少し休む",
                        other_id="buy", other_kind="購入")},
]
for _s in PROHIBITION:
    _s["baseline"] = "wait"


# ------------------------------------------------------------------ (c) 店頭の呼びかけ(人の値なし=強さ 3 段)
#: 強さ 3 段(記録 2-62: お願い・命令・今すぐ)。今すぐ=命令に「今すぐ」を足した形(自前)。
STRENGTHS = ("please", "command", "now")
STRENGTH_WORDS = {"please": "お願い", "command": "命令", "now": "今すぐ"}

SHOP_CALL = [
    {"setting": "cake", "kind": "居住者", "hour": 15, "minute": 30, "scene": "店の中", "outside": False, "shop": True,
     "place": "[B2 場所] 現在地はケーキの店の中(地上)です。", "visible": "季節のケーキと定番のケーキの並んだケース、レジ",
     "density": "B", "near": "店員、ほかの客", "channel": "signage",
     "texts": {"please": "季節のケーキを、よろしければお試しください。", "command": "季節のケーキを買っていけ。",
               "now": "今すぐ季節のケーキを買っていけ。"},
     "wake": "ケーキのケースの前に来た", "money": 3000,
     "body": "体調に変わりはありません。", "memory": "季節のケーキと定番のケーキは同じ値段です。",
     "comply": "seasonal", "baseline": "look",
     "cands": [C("seasonal", "購入", "季節のケーキを買う", "affordance"),
               C("classic", "購入", "定番のケーキを買う", "affordance"),
               C("leave", "移動", "何も買わずに店を出る", "affordance"),
               C("ask", "会話", "店員にケーキのことを尋ねる", "affordance"),
               C("look", "なし", "もう少しケースを見ながら迷う", "continue"),
               C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate")]},
    {"setting": "tout", "kind": "来街者", "hour": 19, "minute": 20, "scene": "路上", "outside": True, "shop": True,
     "place": "[B2 場所] 現在地は飲食店の並ぶ通り(地上)です。", "visible": "居酒屋の並ぶ通り、コンビニ",
     "density": "D", "near": "客引き、通行人", "channel": "speech", "person": "客引き",
     "texts": {"please": "よろしければ、うちの店に寄っていってください。", "command": "うちの店に寄っていけ。",
               "now": "今すぐうちの店に寄っていけ。"},
     "wake": "飲食店の並ぶ通りに来た", "money": 5000,
     "body": "お腹がすいています。", "memory": "この先の店で食事をするつもりです。",
     "comply": "follow", "baseline": "wait",
     "cands": [C("follow", "食事", "客引きについて行き、その店で食事をする", "affordance"),
               C("go_on", "移動", "決めていた店に向かって歩き続ける", "continue"),
               C("ask", "会話", "客引きに店のことを尋ねる", "affordance"),
               C("snack", "購入", "近くのコンビニで軽食を買う", "affordance"),
               C("wait", "なし", "その場で少し様子を見る", "continue"),
               C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate")]},
    {"setting": "sample", "kind": "来街者", "hour": 13, "minute": 40, "scene": "店の前", "outside": True, "shop": True,
     "place": "[B2 場所] 現在地は総菜の店の前(地上)です。", "visible": "総菜の並ぶケース、試食の皿",
     "density": "C", "near": "試食の皿を持った店員、通行人", "channel": "speech", "person": "店員",
     "texts": {"please": "よろしければ、試食をどうぞ召し上がってください。", "command": "試食を食べていけ。",
               "now": "今すぐ試食を食べていけ。"},
     "wake": "店の前を通りかかった", "money": 2000,
     "body": "少しお腹がすいています。", "memory": None,
     "comply": "taste", "baseline": "wait",
     "cands": [C("taste", "食事", "試食を受け取って食べる", "affordance"),
               C("pass", "移動", "そのまま通り過ぎる", "continue"),
               C("buy", "購入", "店で総菜を買う", "affordance"),
               C("ask", "会話", "店員に品のことを尋ねる", "affordance"),
               C("wait", "なし", "その場で少し様子を見る", "continue"),
               C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate")]},
    {"setting": "clothes", "kind": "来街者", "hour": 16, "minute": 50, "scene": "店の前", "outside": True, "shop": True,
     "place": "[B2 場所] 現在地は衣料品店の前(地上)です。", "visible": "衣料品店の入口、飾り窓",
     "density": "C", "near": "店の前に立つ店員、通行人", "channel": "signage",
     "texts": {"please": "よろしければ、店内もご覧ください。", "command": "店内を見ていけ。", "now": "今すぐ店内を見ていけ。"},
     "wake": "店の前を通りかかった", "money": 8000,
     "body": "体調に変わりはありません。", "memory": "次の行き先へ向かう途中です。",
     "comply": "enter", "baseline": "window",
     "cands": [C("enter", "移動", "店に入って中を見る", "affordance"),
               C("pass", "移動", "次の行き先へ歩き続ける", "continue"),
               C("drink", "購入", "近くの店で飲み物を買う", "affordance"),
               C("ask", "会話", "店の前の店員に品のことを尋ねる", "affordance"),
               C("window", "なし", "店の前で足を止めて飾り窓を眺める", "continue"),
               C("deliberate", "よく考える", "立ち止まってよく考える", "deliberate")]},
]


def build_rows() -> list[dict]:
    """場面の行(並びは 種類 → 場面 → ない版が先)。"""
    rows: list[dict] = []
    for s in REQUEST:
        fam = s["setting"]
        rows.append(row(s, "request", "nocall", family=fam, present=False, visible=s["visible"], sign=SIGN_EMPTY,
                        speech=None, appeal={}))
        for size in SIZES:
            for reason in REASONS:
                body = req_text(s["size"][size], s["ask"], s["placebo"], reason)
                rows.append(row(s, "request", f"{size}-{reason}", family=fam, present=True, visible=s["visible"],
                                sign=SIGN_EMPTY, speech=speech_line(s["person"], body),
                                appeal={"channel": "speech", "line": "B6 発話", "condition": f"{size}/{reason}",
                                        "size": size, "reason": reason, "body": body}))
    for s in PROHIBITION:
        for env in ENVS:
            fam = f"{s['setting']}-{env}"
            rows.append(row(s, "prohibition", f"{env}-nosign", family=fam, present=False, visible=s["visible"][env],
                            sign=SIGN_EMPTY, speech=None, appeal={"env": env}))
            rows.append(row(s, "prohibition", f"{env}-sign", family=fam, present=True, visible=s["visible"][env],
                            sign=sign_line(TAG_NOTICE, s["sign"]), speech=None,
                            appeal={"channel": "notice", "line": "B2 看板", "condition": env, "env": env,
                                    "body": s["sign"]}))
    for s in SHOP_CALL:
        fam = s["setting"]
        rows.append(row(s, "shop_call", "nocall", family=fam, present=False, visible=s["visible"], sign=SIGN_EMPTY,
                        speech=None, appeal={}))
        for level, strength in enumerate(STRENGTHS, 1):
            body = s["texts"][strength]
            if s["channel"] == "signage":
                sign, speech, line = sign_line(TAG_SIGNAGE, body), None, "B2 看板"
            else:
                sign, speech, line = SIGN_EMPTY, speech_line(s["person"], body), "B6 発話"
            rows.append(row(s, "shop_call", strength, family=fam, present=True, visible=s["visible"], sign=sign,
                            speech=speech, appeal={"channel": s["channel"], "line": line, "condition": strength,
                                                   "strength": strength, "level": level, "body": body}))
    return rows


def render_files() -> dict[str, bytes]:
    """書き出す 3 本の名 → バイト(LF・UTF-8・鍵の順は固定)。"""
    rows = build_rows()
    jl = ("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n").encode("utf-8")
    b0 = (json.dumps({"b0_texts": {B0_ID: B0}, "name": NAME, "note": "呼びかけの場面 v1 の前置き(自前・架空)"},
                     ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")
    md5 = (f"{hashlib.md5(jl).hexdigest()}  {NAME}.jsonl\n"
           f"{hashlib.md5(b0).hexdigest()}  {NAME}.b0.json\n").encode("utf-8")
    return {f"{NAME}.jsonl": jl, f"{NAME}.b0.json": b0, f"{NAME}.md5": md5}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    if len(args) != 1:
        print("使い方: make_appeal_v1.py <出力の dir>")
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
