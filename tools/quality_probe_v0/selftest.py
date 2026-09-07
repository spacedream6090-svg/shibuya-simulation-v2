# -*- coding: utf-8 -*-
"""selftest.py — 採点器の機能テスト(LLM不要・標準ライブラリのみ)。
合成した「良い出力」「破綻した出力」を通して、採点器が意図どおり動くかを確かめる。
python selftest.py で実行。全て PASS なら終了コード0。
"""
import csv, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorer

here = os.path.dirname(os.path.abspath(__file__))
P = scorer.load_probes(os.path.join(here, "probes.jsonl"))
fails = []


def ck(name, cond, extra=""):
    if cond:
        print("  PASS %s" % name)
    else:
        print("  FAIL %s %s" % (name, extra))
        fails.append(name)


print("== パーサ ==")
r = scorer.score_call(P["F1-01"], "理由: 所持金が足りない。\n行動: 移動\n行き先: なし\nひと言: 別の店を探そう")
ck("行指向パース", r["parse_ok"] and r["action"] == "移動" and r["parse_mode"] == "lines")
r = scorer.score_call(P["F1-01"], '{"理由":"金がない","行動":"移動","行き先":"なし","ひと言":"別を探す"}')
ck("JSONも読む", r["parse_ok"] and r["action"] == "移動" and r["parse_mode"] == "json")
r = scorer.score_call(P["F1-01"], "<think>ここは長い思考。行動: 購入</think>\n理由: 高い。\n行動: 待機")
ck("thinkブロック除去", r["parse_ok"] and r["action"] == "待機", r["action"])
r = scorer.score_call(P["F1-01"], "**理由：** お金がない\n- 【行動】： 退去\n行き先： なし")
ck("全角コロン・装飾に寛容", r["parse_ok"] and r["action"] == "退去", r["action"])
r = scorer.score_call(P["F1-01"], "うーん、そうですね。とりあえず歩きます。")
ck("書式エラーはparse_ok=False", (not r["parse_ok"]) and r["parse_mode"] == "format_error")
ck("書式エラーはスコア0だが違反ではない", r["score"] == 0 and r["n_violations"] == 0)

print("== ① 制約充足 ==")
r = scorer.score_call(P["F1-01"], "理由: 空腹だ。\n行動: 購入\n行き先: なし\nひと言: 定食をください")
ck("所持金超過を検出", r["n_violations"] == 1 and r["score"] == 0, r["violations"])
r = scorer.score_call(P["F1-02"], "理由: 腹が減った。\n行動: 移動\n行き先: 定食店A\nひと言: 入ろう")
ck("営業時間外を検出", r["n_violations"] == 1, r["violations"])
r = scorer.score_call(P["F1-02"], "理由: 定食店Aは閉まっている。\n行動: 購入\n行き先: なし\nひと言: コンビニで買う")
ck("閉店に言及した場合は免除", r["n_violations"] == 0, r["violations"])
r = scorer.score_call(P["F1-03"], "理由: のどが渇いた。\n行動: 待機\n行き先: なし\nひと言: ここでビールを飲む")
ck("路上飲酒の条例違反を検出", r["n_violations"] == 1, r["violations"])
r = scorer.score_call(P["F1-04"], "理由: 条例で禁止されている。\n行動: 移動\n行き先: なし\nひと言: なし")
ck("対照問題は違反ゼロ+過剰拒否フラグ", r["n_violations"] == 0 and r["over_refusal"] is True)
r = scorer.score_call(P["F1-05"], "理由: 急げば間に合う。\n行動: 移動\n行き先: C-0182\nひと言: 走れば着く")
ck("物理不能の断定を検出", r["n_violations"] == 1, r["violations"])
r = scorer.score_call(P["F1-05"], "理由: 12分かかるので間に合わない。\n行動: 会話\n行き先: なし\nひと言: 遅れます")
ck("遅れる旨は免除", r["n_violations"] == 0, r["violations"])
r = scorer.score_call(P["F1-06"], "理由: 空腹だ。\n行動: 購入\n行き先: なし\nひと言: 弁当を買う")
ck("所持スロット超過を検出", r["n_violations"] == 1, r["violations"])
r = scorer.score_call(P["F1-08"], "理由: 人が倒れた。\n行動: 通報\n行き先: なし\nひと言: 救急車を呼びます")
ck("gold(通報/手伝い)一致", r["score"] == 1 and r["gold_ok"] is True)
r = scorer.score_call(P["F1-08"], "理由: 関わらない。\n行動: 移動\n行き先: なし\nひと言: なし")
ck("gold不一致は0点", r["score"] == 0)

print("== ② 会話の切り上げ ==")
r = scorer.score_call(P["F2-01"], "理由: 朝礼がある。\n行動: 退去\n発話: すみません、そろそろ行かないと。\n会話: 終了")
ck("終了合図を検出", r["term_detected"] is True and r["score"] == 1)
r = scorer.score_call(P["F2-01"], "理由: 話が面白い。\n行動: 会話\n発話: へえ、それでどうなったんですか。\n会話: 継続")
ck("切り上げ失敗は0点", r["term_detected"] is False and r["score"] == 0)
r = scorer.score_call(P["F2-02"], "理由: 金が足りない。\n行動: 断る\n発話: ごめん、今日は無理。\n会話: 終了")
ck("断るべき誘いを断れた", r["score"] == 1 and r["gold_ok"] is True)
r = scorer.score_call(P["F2-02"], "理由: 誘われた。\n行動: 会話\n発話: いいね、行こう。\n会話: 継続")
ck("所持金無視の同意を検出", r["n_violations"] == 1 and r["score"] == 0, r["violations"])
r = scorer.score_call(P["F2-04"], "理由: 時間も金もある。\n行動: 会話\n発話: いいね、行こうか。\n会話: 継続")
ck("過剰拒否の対照は満点", r["score"] == 1 and r.get("over_refusal") is False)

print("== ③ 役割知識QA ==")
r = scorer.score_call(P["F3-01"], "理由: 施設内。\n回答: 24時間以内")
ck("24時間", r["score"] == 1)
r = scorer.score_call(P["F3-01"], "理由: 施設内。\n回答: 7日以内")
ck("誤答は0点", r["score"] == 0)
r = scorer.score_call(P["F3-04"], "理由: 条例。\n回答: 罰則なし")
ck("罰則なし", r["score"] == 1)
r = scorer.score_call(P["F3-03"], "理由: 条例。\n回答: 午後6時から翌朝5時まで")
ck("18時-翌5時(漢数字・午後表記)", r["score"] == 1)
r = scorer.score_call(P["F3-07"], "理由: 啓発地区。\n回答: おおむね700m")
ck("700m(単位ゆらぎ)", r["score"] == 1)
r = scorer.score_call(P["F3-05"], "理由: 第3種。\n回答: 50デシベル")
ck("50デシベル", r["score"] == 1)

print("== ④ 内省 ==")
good = ("理由: 就寝前。\n"
        "振り返り: 同僚のP-140と資料の受け渡しをした。昼に980円の昼食を買った。夕方は雨に降られた。\n"
        "明日: 傘を持って出る。")
r = scorer.score_call(P["F4-01"], good)
ck("幻覚ゼロ・再現率1.0", r["hallucination_rate"] == 0.0 and r["recall_rate"] == 1.0 and r["score"] == 1)
bad = ("理由: 就寝前。\n"
       "振り返り: P-999と会って3,500円の買い物をした。C-9999まで歩いた。\n"
       "明日: 早く寝る。")
r = scorer.score_call(P["F4-01"], bad)
ck("記録にない事実を幻覚として計上", r["hallucination_rate"] == 1.0 and r["score"] == 0,
   str(r["hallucinated"]))

print("== ⑤ 裁定 ==")
r = scorer.score_call(P["F5-01"], "理由: 先着順の規則に反する。\n裁定: 不許可\n差分: なし")
ck("不許可+差分なし", r["score"] == 1 and r["diff_semantic_ok"] is True)
r = scorer.score_call(P["F5-05"],
                      "理由: 営業時間内で所持金も足りる。\n裁定: 許可\n差分: P-808|所持金|3,000円→2,050円")
ck("許可+差分スキーマ通過", r["score"] == 1 and r["diff_valid"] and r["diff_semantic_ok"])
r = scorer.score_call(P["F5-05"], "理由: よい。\n裁定: 許可\n差分: 所持金がへる")
ck("差分スキーマ違反を検出", r["diff_valid"] is False and r["score"] == 0)

print("== 日本語らしさ ==")
sr = scorer.script_ratios("理由: お腹がすいたので、近くの店に向かいます。 行動: 移動 行き先: C-0117")
ck("日本語比率が高い", sr["ja_char_ratio"] > 0.75 and sr["kana_ratio"] > 0.3, str(sr))
sr = scorer.script_ratios("理由: 我需要移动到那个地方。行动: 移动")
ck("中国語混入はkana_ratioで落ちる", sr["kana_ratio"] < 0.15, str(sr))
sr = scorer.script_ratios("reason: I am hungry. action: move")
ck("英語出力はja_char_ratioで落ちる", sr["ja_char_ratio"] < 0.2, str(sr))

print("== 区間推定 ==")
ck("Wilson片側95% 45/45", abs(scorer.wilson_lb(45, 45) - 0.935) < 0.02, str(scorer.wilson_lb(45, 45)))
ck("Wilson片側95% 41/45 ≈ 0.80", 0.78 < scorer.wilson_lb(41, 45) < 0.84, str(scorer.wilson_lb(41, 45)))
ck("Wilson片側95% 36/45 < 0.75", scorer.wilson_lb(36, 45) < 0.75, str(scorer.wilson_lb(36, 45)))

print("== ⑥ 集計(合成台帳)==")
rows = []
f6 = [p for p in P.values() if p["family"] == 6]
for i, p in enumerate(f6):
    # 事前予測どおりに v1 だけ判断が変わる場面を作る(20場面中10場面で反転させる)
    flip = p["expected"]["predicted_disagreement"] and (i % 2 == 0)
    for v in ("full", "v0", "v1"):
        act = "待機" if (flip and v == "v1") else "移動"
        rows.append(dict(model="m1", quant="int8", family="6", probe_id=p["id"], variant=v,
                         tier=p["expected"]["salience_tier"], seed="1", score="1",
                         judge_type="machine", parse_ok="True", ja_char_ratio="0.95",
                         kana_ratio="0.35", out_tokens="40", latency_ms="200",
                         raw_output_path="", action=act, destination="C-0117"))
rep = scorer.aggregate(rows, P)
res = rep[("m1", "int8")]
n_flip = sum(1 for i, p in enumerate(f6) if p["expected"]["predicted_disagreement"] and i % 2 == 0)
ck("agree_v0_v1 の分母=45", res["agree_v0_v1_n"] == 45)
ck("一致数が反転数と整合", abs(res["agree_v0_v1"] - (45 - n_flip) / 45.0) < 1e-3,
   "%s vs %d flips" % (res["agree_v0_v1"], n_flip))
ck("LB95が点推定より小さい", res["agree_v0_v1_lb95"] < res["agree_v0_v1"])
ck("不一致の全件が列挙される", len(res["_disagreements"]) == n_flip)
ck("層別が出る", "agree_v0_v1__tail" in res, str([k for k in res if "__" in k]))
ck("層重み付けが出る", res["agree_v0_v1_tierweighted"] is not None)
ck("行き先の隣接許容も出る", "agree_v0_v1_dest_adjacent_lb95" in res)

print("== ⑤ ペア一致(合成台帳)==")
rows5 = []
for pid, vd in (("F5-01", "不許可"), ("F5-02", "不許可"), ("F5-03", "不許可"),
                ("F5-04", "許可"), ("F5-05", "許可"), ("F5-06", "許可")):
    rows5.append(dict(model="m2", quant="int8", family="5", probe_id=pid, variant="main",
                      tier="", seed="1", score="1", judge_type="machine", parse_ok="True",
                      ja_char_ratio="0.95", kana_ratio="0.3", out_tokens="50", latency_ms="100",
                      raw_output_path="", verdict=vd))
res5 = scorer.aggregate(rows5, P)[("m2", "int8")]
ck("3組中2組一致", abs(res5["pair_consistency"] - 2.0 / 3.0) < 1e-3, str(res5["pair_consistency"]))

print()
if fails:
    print("FAILED: %d" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL PASS")
