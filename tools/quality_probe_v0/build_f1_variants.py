# -*- coding: utf-8 -*-
"""build_f1_variants.py — 系統①(制約つき8場面)に観測2水準(v0/v1)の変種を作る。
目的: 指標B(制約違反率の差)の「制約半分」を埋める(親Claude 2026-09-06・ユーザーGo)。
規則: build_probes.py の TRIM と同じ切り詰め/充填規則を、既存の①観測文(=ほぼv1サイズ)へ適用する。
  v1: 可視3・看板1・近景1・近接3・傍受/広告/固定文言なし(=main−α)
  v0: 可視8・看板4・構成1・印象1・近景2・近接4・所持2行目・関係/可視差分/被注視・傍受1・直近2・記憶1
制約を担う情報(所持金・営業時間表示・条例区域・所持スロット・距離)は両水準に残る=試験は「周辺情報の増減が制約充足を変えるか」。
B0(system)は両水準で同一(交絡回避・⑥と同じ方針)。expected は原本をそのままコピー(採点規則は不変)。
出力: probes_f1var.jsonl(16問・id="F1-0Nv0"/"F1-0Nv1"・family=1・variant='main' で走らせる)。
"""
import json, hashlib, re, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from build_probes import TRIM, DEFAULT_SIGNS, STATIC_EXTRA, IMP_EXTRA, DEFAULT_OVERHEARD, MEMORY_LINES, REC

here = os.path.dirname(os.path.abspath(__file__))
VIS_POOL = ["雑居ビルの入口", "自動販売機", "街路灯", "街路樹", "コインパーキングの入口",
            "ドラッグストアの店頭", "カフェの店頭", "駐輪場", "案内板", "バス停", "交番", "地下鉄出入口"]
B4B_POOL = ["立ち止まって携帯電話を見ている人が2人います。", "店の入口の前に短い列があります。"]
NEIGH_POOL = ["P-951(未知)", "P-952(未知)", "P-953(未知)", "P-954(未知)"]
WATCHED = {"F1-07": "同行者2人があなたを見ています。"}
SIGN_TAG = "[B2 看板] 〔素性: 店頭表示・世界内テキスト・命令文除去済〕"

def split_vis(line):
    m = re.match(r"\[B2 可視\] 見えるもの: (.*)。$", line)
    return [x for x in m.group(1).split("、") if x]

def render(pid, obs, variant):
    t = TRIM[variant]
    L = obs.split("\n")
    out = []
    signs_seen = 0
    b4b_seen = 0
    i = 0
    # 1パス目: 各行を規則で置換/間引き
    for line in L:
        if line.startswith("[B2 可視]"):
            vis = split_vis(line)
            if variant == "v1":
                vis = vis[:t["visible"]]
            else:
                for x in VIS_POOL:
                    if len(vis) >= t["visible"]:
                        break
                    if x not in vis:
                        vis.append(x)
            out.append("[B2 可視] 見えるもの: " + "、".join(vis) + "。")
            continue
        if line.startswith("[B2 看板]"):
            signs_seen += 1
            if signs_seen > t["signs"]:
                continue
            out.append(line); continue
        if line.startswith("[B4b 近景]"):
            b4b_seen += 1
            if b4b_seen > t["b4b"]:
                continue
            out.append(line); continue
        if line.startswith("[B5 近接]"):
            m = re.match(r"\[B5 近接\] 近くの人物: (.*)。$", line)
            names = [x for x in m.group(1).split("、") if x]
            if variant == "v1":
                names = names[:t["neigh"]]
            else:
                for x in NEIGH_POOL:
                    if len(names) >= t["neigh"]:
                        break
                    names.append(x)
            out.append("[B5 近接] 近くの人物: " + "、".join(names) + "。")
            continue
        out.append(line)
    if variant == "v1":
        return "\n".join(out)
    # 2パス目(v0のみ): 充填
    final = []
    n_signs = sum(1 for l in out if l.startswith("[B2 看板]"))
    n_b4b = sum(1 for l in out if l.startswith("[B4b"))
    for idx, line in enumerate(out):
        final.append(line)
        nxt = out[idx + 1] if idx + 1 < len(out) else ""
        # 看板の充填 + 構成/印象: B3時刻の直前に置く
        if nxt.startswith("[B3 時刻]"):
            k = 0
            while n_signs < t["signs"]:
                final.append(SIGN_TAG + DEFAULT_SIGNS[k]); k += 1; n_signs += 1
            for s in STATIC_EXTRA[:t["static_extra"]]:
                final.append("[B2 構成] " + s)
            for s in IMP_EXTRA[:t["impression"]]:
                final.append("[B2 印象] " + s)
        # 近景の充填: B5内受容の直前
        if nxt.startswith("[B5 内受容]"):
            k = 0
            while n_b4b < t["b4b"]:
                final.append("[B4b 近景] 25メートル以内: " + B4B_POOL[k]); k += 1; n_b4b += 1
        if line.startswith("[B5 所持]"):
            final.append("[B5 所持] 持てるのは両手で2つまでです。")
        if line.startswith("[B5 近接]"):
            final.append("[B5 関係] このセルにいる人物のうち、あなたと関係のある人物は上の一覧に記した分で全部です。")
            final.append("[B5 可視差分] セル代表点から見えるものと、あなたの位置から見えるものとの差はありません。")
            final.append("[B5 被注視] " + WATCHED.get(pid, "あなたを見ている人はいません。"))
            final.append("[B5 傍受] 〔素性: 会話の傍受・世界内テキスト・命令文除去済〕" + DEFAULT_OVERHEARD[0])
        if nxt.startswith("[B6"):
            final.append("[B5 直近] " + REC[0])
            final.append("[B5 直近] " + REC[2])
            for s in MEMORY_LINES[:t["memory"]]:
                final.append("[B5 記憶] " + s)
    return "\n".join(final)

def main():
    items = [json.loads(l) for l in open(os.path.join(here, "probes.jsonl"), encoding="utf-8")]
    f1 = [p for p in items if p["family"] == 1]
    outp = []
    for p in f1:
        for v in ("v0", "v1"):
            q = json.loads(json.dumps(p, ensure_ascii=False))
            q["id"] = p["id"] + v
            q["f1_variant"] = v
            q["f1_source_id"] = p["id"]
            q["observation"] = render(p["id"], p["observation"], v)
            q["approx_tokens"] = int(round((len(q["system_block"]) + len(q["observation"]) + len(q["question"])) / 1.30))
            outp.append(q)
    path = os.path.join(here, "probes_f1var.jsonl")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for q in outp:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    open(os.path.join(here, "item_set_hash_f1var.txt"), "w").write("probes_f1var.jsonl sha256 = %s (16 items)\n" % h)
    for q in outp:
        print("%-9s obs_lines=%2d approx_tokens=%d" % (q["id"], q["observation"].count("\n") + 1, q["approx_tokens"]))
    print("sha256", h)

if __name__ == "__main__":
    main()
