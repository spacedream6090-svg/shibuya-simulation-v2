"""第 348(返事その 9 §1 の 19・§5-2 の 6): 低い層の既定 v1 に頼って読んでいた 8 か所に、ランの語彙を渡す。

記録 ``docs/bench/analysis/library-defaults-q13-347/README.md`` §4-8 の 8 か所のうち、パーサの 6 か所と行為の読みの 1 か所を
ここで確かめる(艦隊の書式の判定の 1 か所は ``test_fleet_run_vocab_348.py``)。

- パーサ ``_parse`` の 4 か所: 空の応答の結果(``_empty_result`` 2 か所)・対象の読み(``parse_target``)・役割語の判定
  (``is_role_action``)。
- 位置で読む ``_fill_positional`` の 2 か所(``find_action_word`` で行動語を探す 2 回)。
- 行為の読み ``parse_action``(``parse_two_line`` へ委ねる 1 か所)。

``_parse`` は ``parse_two_line`` が v1・v2 のときだけ呼ぶ(v3 は ``_parse_v3``)。そこで v3 の規則で読むことは ``_parse`` に
v3 を直に渡して確かめる(渡した語彙が中の呼び出しへ届くことの確かめ)。v1 と v2 では、``_empty_result``・``parse_target``・
``is_role_action`` は同じ規則なので、前と同じ値になる。``_fill_positional`` だけは v2 で読みが変わる応答がある
(「食事」が行動語として数えられる。下の ``test_v2_readings_that_change``)。
"""

from __future__ import annotations

import pytest

from shibuya.act.intake import parser as P
from shibuya.act.intake import from_words as FW
from shibuya.foundation.vocab.act_codes import ACTION_CODES
from shibuya.foundation.vocab.actions import DEFAULT_UNTIL, NO_TARGET, UNDEFINED_ACTION, is_role_action, parse_target

WANDER = "理由: 散歩したいから\n行動: 移動 対象: あたり ひと言: なし"
QUEUE = "理由: 列が見えたから\n行動: 並ぶ 対象: なし ひと言: なし"
#: 行動語が先頭の語に無い(v3 では「なし」が行動語)。1 回目の ``find_action_word``(欄の全体)が語彙を見るか。
GUARD_WHOLE = "理由: 疲れたから\n行動: ゆっくり なし 自宅"
#: 先頭の語が v3 だけの行動語(なし)で、後ろに v1 の行動語(移動)がある。2 回目(先頭の語)が語彙を見るか。
GUARD_FIRST = "理由: 迷ったから\n行動: なし 移動 自宅"


def _show(r: P.ParseResult) -> str:
    return (f"action={r.action!r} format_ok={r.format_ok} positional_used={r.positional_used} "
            f"is_role_action={r.is_role_action} wander={r.target.wander} activity={r.activity!r} "
            f"until={r.until!r}\nlabels={dict(r.labels)!r}\nerrors={r.errors!r}\n")


# ------------------------------------------------------------------ _parse の 4 か所
@pytest.mark.parametrize("text", [None, ""], ids=["none", "empty"])
def test_empty_result_reads_with_the_given_vocab(text):
    """``_empty_result`` の 2 か所(本文が None・空)。v3 なら活動=なし・まで=既定の形。"""
    r = P._parse(text, "v3")
    assert (r.activity, r.until) == (NO_TARGET, DEFAULT_UNTIL), "v3 の空の結果の形でない\n" + _show(r)
    for v in ("v1", "v2"):  # 前と同じ(欄なし)
        r = P._parse(text, v)
        assert (r.activity, r.until, r.errors) == ("", None, ("empty_output",)), f"{v} が前と違う\n" + _show(r)


def test_parse_target_reads_with_the_given_vocab():
    """``parse_target`` の 1 か所。v3 だけ「対象: あたり」が歩き回り(``wander``)。"""
    r = P._parse(WANDER, "v3")
    assert r.target.wander is True, "v3 で「あたり」が歩き回りにならない\n" + _show(r)
    for v in ("v1", "v2"):
        r = P._parse(WANDER, v)
        assert r.target.wander is False and r.target.category == "あたり", f"{v} が前と違う\n" + _show(r)


def test_is_role_action_reads_with_the_given_vocab():
    """``is_role_action`` の 1 か所。v3 では「並ぶ」は横断語(役割語でない)。"""
    r = P._parse(QUEUE, "v3")
    assert r.action == "並ぶ" and r.is_role_action is False, "v3 で「並ぶ」が役割語になった\n" + _show(r)
    for v in ("v1", "v2"):
        r = P._parse(QUEUE, v)
        assert r.action == "並ぶ" and r.is_role_action is True, f"{v} が前と違う\n" + _show(r)


# ------------------------------------------------------------------ _fill_positional の 2 か所
def test_fill_positional_whole_field_reads_with_the_given_vocab():
    """1 回目の ``find_action_word``(行動欄の全体)。v3 では「なし」が行動語=先頭の語に無いので位置で読まない。"""
    r = P._parse(GUARD_WHOLE, "v3")
    assert r.positional_used is False and "対象" not in r.labels, "v3 で位置読みした\n" + _show(r)
    for v in ("v1", "v2"):  # どちらも「なし」は行動語でない=前と同じに位置で読む
        r = P._parse(GUARD_WHOLE, v)
        assert r.positional_used is True and r.labels.get("対象") == "なし", f"{v} が前と違う\n" + _show(r)


def test_fill_positional_first_token_reads_with_the_given_vocab():
    """2 回目の ``find_action_word``(先頭の語)。v3 では先頭の「なし」が行動語=位置で読む(対象=移動)。"""
    r = P._parse(GUARD_FIRST, "v3")
    assert r.positional_used is True and r.labels.get("対象") == "移動", "v3 で位置読みしない\n" + _show(r)
    for v in ("v1", "v2"):  # 欄の全体の語は「移動」で先頭の語と違う=前と同じに位置で読まない
        r = P._parse(GUARD_FIRST, v)
        assert r.positional_used is False and r.action == "移動", f"{v} が前と違う\n" + _show(r)


@pytest.mark.parametrize(
    "text, before, after",
    [
        # 前: v1 の語で探し「食事」を見ない=位置で読み、対象=食事・行動語なし。後: 欄の全体の語は「食事」で先頭の語と違う=位置で読まない。
        ("理由: お腹がすいたから\n行動: ゆっくり 食事 ラーメン",
         {"positional_used": True, "action": None, "format_ok": False},
         {"positional_used": False, "action": "食事", "format_ok": False}),
        # 前: 欄の全体の語は「購入」で先頭の「食事」と違う=位置で読まない。後: 先頭の「食事」が行動語=位置で読む(対象=購入)。
        ("理由: お腹がすいたから\n行動: 食事 購入 なし",
         {"positional_used": False, "action": "食事", "format_ok": False},
         {"positional_used": True, "action": "食事", "format_ok": True}),
    ],
    ids=["eat_after_first_token", "eat_first_then_v1_word"],
)
def test_v2_readings_that_change(text, before, after):
    """〔第 348 で変わる読み〕語彙 v2 のランで、行動欄に「食事」があり、ラベルを省いた応答。``_fill_positional`` が v2 の語を見る
    ようになったので、位置で読むかが変わる(v1 の語だけで見ていた前の値は ``before``)。v1 のランは前と同じ。"""
    r = P.parse_two_line(text, "v2")
    got = {k: getattr(r, k) for k in after}
    assert got == after, f"v2 の新しい読みと違う(前の値は {before})\n" + _show(r)
    r1 = P.parse_two_line(text, "v1")
    assert r1.action != "食事", "v1 で「食事」が行動語になった\n" + _show(r1)


# ------------------------------------------------------------------ 行為の読み parse_action
V3_WAIT = "理由: 人を待つから\n行動: 待機 対象: なし 活動: 待つ まで: 10分"
GOOD = "理由: 予定の時間になったから\n行動: 移動 対象: C-0001 ひと言: なし"


def test_parse_action_reads_with_the_given_vocab():
    """``parse_action`` は語彙を受け取り ``parse_two_line`` へ渡す。v3 では「待機」は欠番=未定義。"""
    assert FW.parse_action(V3_WAIT, "v3") == UNDEFINED_ACTION
    for v in ("v1", "v2"):  # 前と同じ
        assert FW.parse_action(V3_WAIT, v) == ACTION_CODES["待機"], v
        assert FW.parse_action(GOOD, v) == ACTION_CODES["移動"], v
        assert FW.parse_action("", v) == UNDEFINED_ACTION, v


# ------------------------------------------------------------------ 低い層の既定を無くした(必ず渡す)
def _calls_without_vocab():
    from shibuya.runtime.inference import fleet as F

    return {
        "parse_two_line": lambda: P.parse_two_line(GOOD),
        "find_action_word": lambda: P.find_action_word("移動"),
        "_empty_result": lambda: P._empty_result(("empty_output",)),
        "_fill_positional": lambda: P._fill_positional({"行動": "移動 C-0001"}),
        "parse_target": lambda: parse_target("C-0001"),
        "is_role_action": lambda: is_role_action("並ぶ"),
        "parse_action": lambda: FW.parse_action(GOOD),
        "fleet._format_ok": lambda: F._format_ok(GOOD),
    }


@pytest.mark.parametrize("name", list(_calls_without_vocab()))
def test_low_level_functions_need_the_vocab(name):
    """8 か所が頼っていた低い層の既定は無い=語彙を渡さないと呼べない(``TypeError``)。"""
    call = _calls_without_vocab()[name]
    with pytest.raises(TypeError):
        call()
