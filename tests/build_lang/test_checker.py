"""検査器の回帰テスト(**第1回生成 2026-09-09 の全件分析が根拠**)。

親の分析: W14 不合格 307/2,337(0.131)・W15 147/520(0.283)。rep 間バイト一致は 1.0 で、
不合格の中身は**検査器の偽陽性**(N1 47・N7 113・N2 11)と**プロンプトの欠陥**
(N4 78=「毎日終日」に数字が無くモデルが 10-22 時を捏造・too_long 72・W15 の「など」106)
だった。ここは前者(検査器)の陽性/陰性を釘付けする。

- 偽陽性だったもの = **通らなければならない**(通さないと世界が合成文へ落ちる)。
- 真陽性だったもの = **落ちなければならない**(通すと捏造が世界に入る)。
"""

from __future__ import annotations

import pytest

from shibuya.build.lang import common as L

#: W14 の入力(user プロンプト)の典型形。
ALLOWED_W14 = (
    "店名: Skechers\n業種: 物販店\n価格帯: 中程度\n"
    "営業時間: 平日は11時から21時\n定休日: なし\nこの店の店頭表示を1行で書く。"
)
ALLOWED_KONBINI = (
    "店名: ファミリーマート\n業種: コンビニエンスストア\n価格帯: 低め\n"
    "営業時間: 24時間営業(毎日)\n定休日: なし\nこの店の店頭表示を1行で書く。"
)


def rules(text: str, allowed: str, *, kanji_strict: bool = True) -> set[str]:
    """その文が踏んだ規則 id の集合(固有名詞+禁止語+個体語+省略記法)。"""
    v = L.scan_proper_nouns(text, allowed, kanji_strict=kanji_strict)
    v += L.check_banned_words(text)
    v += L.check_individual_words(text, allowed)
    v += L.check_abbreviation(text, allowed)
    return {x.rule for x in v}


# ---------------------------------------------------------------- N1 ラテン(偽陽性)
@pytest.mark.parametrize(
    "text",
    [
        "Skechersは物販店。平日は11時から21時。",          # 第1回: 'Skechers 11' で落ちた
        "Skechers 11時から21時まで営業。",                  # 空白+数字が続く形
        "Skechersは物販店で、11時から21時まで営業。",
    ],
)
def test_latin_name_followed_by_digits_passes(text: str):
    """英字店名に空白・数字が連結しても偽陽性にしない(第1回 47 件の原因)。"""
    assert "N1_latin" not in rules(text, ALLOWED_W14)


def test_latin_word_is_matched_case_insensitively():
    allowed = "店名: Zarigzu cafe\n業種: 飲食店\n営業時間: 毎日17時から23時\n"
    assert "N1_latin" not in rules("ZARIGZU CAFEは飲食店。毎日17時から23時。", allowed)


@pytest.mark.parametrize("text", ["Skechersのほか Adidas も扱う。", "H&M と併設。"])
def test_latin_word_not_in_input_is_still_caught(text: str):
    """語単位に割っても**入力に無い英字語**は捕まる(捏造の検出は落とさない)。"""
    assert "N1_latin" in rules(text, ALLOWED_W14)


# ---------------------------------------------------------------- N7 漢字(偽陽性)
@pytest.mark.parametrize(
    "word", ["開館", "開校", "参拝", "診療", "利用", "軽食", "紹介", "用品", "受付"]
)
def test_two_character_common_kanji_words_pass(word: str):
    """2 文字の一般漢語は N7 の対象外(第1回 113 件のほぼ全部がこれ)。"""
    assert "N7_kanji" not in rules(f"Skechersは物販店。平日は11時から21時。{word}あり。", ALLOWED_W14)


def test_kanji_compound_of_input_and_generic_passes():
    """「歯科診療」= 入力語(歯科)+ 一般語(診療)は分解して通す。"""
    allowed = "店名: 渋谷歯科\n業種: サービス店\n営業時間: 平日は9時から18時\n"
    assert "N7_kanji" not in rules("渋谷歯科は平日9時から18時に歯科診療をしています。", allowed)


def test_run_on_kanji_containing_an_input_substring_passes():
    """「分日曜」のような連結は、入力に「日曜」があれば文字単位で消えて通る。"""
    allowed = "店名: 風月\n業種: 飲食店\n営業時間: 月曜から日曜は11時30分から22時\n"
    assert "N7_kanji" not in rules("風月は月曜から日曜11時30分日曜22時まで営業。", allowed)


def test_fabricated_kanji_is_still_caught():
    """入力にも一般語表にも無い 3 文字以上の漢字列は落とす(真陽性)。"""
    assert "N7_kanji" in rules("Skechersは物販店。歌庯場を併設。", ALLOWED_W14)


# ---------------------------------------------------------------- A1 曜日略記
@pytest.mark.parametrize("text", ["Skechersは月金11時から21時。", "Skechersは金土のみ営業。"])
def test_weekday_abbreviation_is_caught_by_a1_not_n7(text: str):
    """**曜を伴わない**曜日字の連なりだけが略記。⑥(A1)で扱い N7 では扱わない。"""
    got = rules(text, ALLOWED_W14)
    assert "A1_weekday_abbr" in got
    assert "N7_kanji" not in got


@pytest.mark.parametrize(
    "text",
    [
        "Skechersは土曜日曜11時から21時。",     # 第2回生成の 56 件(入力「土日」の展開)
        "Skechersは土曜日曜日11時から21時。",
        "Skechersは火曜金曜のみ営業。",
        "Skechersは月曜から金曜11時から21時。",
    ],
)
def test_full_weekday_names_side_by_side_are_not_abbreviations(text: str):
    """**完全な曜日名を並べただけ**は略記でない(親指示 2026-09-09 第3回)。

    第2回生成の W14 は不合格 94 件中 56 件がこの形(入力の「土日は…」をモデルが
    「土曜日曜」へ展開したもの)で、凍結率を無駄に下げていた。
    """
    got = rules(text, ALLOWED_W14)
    assert "A1_weekday_abbr" not in got, got
    assert "N7_kanji" not in got, got


def test_weekday_pair_present_in_the_input_passes():
    """入力に「土日」と書いた場合、その表現は略記ではない。"""
    allowed = "店名: Skechers\n業種: 物販店\n営業時間: 平日は11時から21時、土日は10時から20時\n"
    assert "A1_weekday_abbr" not in rules("Skechersは平日11時から21時、土日10時から20時。", allowed)


# ---------------------------------------------------------------- N2 カタカナ
@pytest.mark.parametrize(
    "word",
    ["スイーツ", "パチンコ", "クリニック", "イタリアン", "デザート", "サンドイッチ",
     "グッズ", "カレーハウス", "アイスクリーム", "ヘアケア", "ファストフード",
     "ブランド", "トラック", "ヘアーアクセサリー"],
)
def test_generic_katakana_words_pass(word: str):
    assert "N2_katakana" not in rules(f"Skechersは物販店。{word}を扱う。", ALLOWED_W14)


@pytest.mark.parametrize("word", ["ホミヤ", "ハリス", "マレーシア"])
def test_proper_katakana_not_in_input_is_caught(word: str):
    """固有名詞らしいカタカナは残す(真陽性)。"""
    assert "N2_katakana" in rules(f"Skechersは物販店。{word}を扱う。", ALLOWED_W14)


# ---------------------------------------------------------------- N4 数字
def test_fabricated_hours_against_24h_input_is_caught():
    """入力が「24時間営業(毎日)」なのに 10-22 時と書いたら落とす(第1回 74 件の真陽性)。"""
    got = rules("ファミリーマートは10時から22時まで営業。", ALLOWED_KONBINI)
    assert "N4_digit" in got


def test_24h_wording_from_the_input_passes():
    """新しい入力表現「24時間営業(毎日)」はそのまま書ける。"""
    assert not rules("ファミリーマートはコンビニエンスストアで24時間営業。", ALLOWED_KONBINI)


def test_fullwidth_digits_in_the_input_are_normalized_before_comparison():
    """入力側に全角数字があっても偽陽性にしない(NFKC で寄せる)。"""
    allowed = "店名: １１番地ベーカリー\n業種: 飲食店\n営業時間: 毎日７時から１９時\n"
    assert "N4_digit" not in rules("11番地ベーカリーは毎日7時から19時。", allowed)


# ---------------------------------------------------------------- W15(kanji_strict なし)
ALLOWED_W15 = (
    "区画ID: g0_0_GL\n層: 地上\n広さ: 一辺100メートルの区画\n"
    "この区画に含まれる街区の数: 1\n"
    "この区画から見える店舗と施設: 飲食店(pioppino)、飲食店(いちのや)\n"
    "この区画から見える目印: なし\nこの区画の中にある店舗の構成: なし\n"
)


@pytest.mark.parametrize("text", ["飲食店や娯楽施設などが並ぶ", "飲食店、物販店等が並ぶ"])
def test_w15_abbreviation_is_caught(text: str):
    """第1回 W15 の最大要因(106/147)。system で禁止したうえで検査でも落とす。"""
    assert "A1_abbreviation" in rules(text, ALLOWED_W15, kanji_strict=False)


def test_w15_counting_with_digits_is_caught():
    """個数を数字で書く(「2軒」)のは入力に無い数字=真陽性(第1回 50 件)。"""
    assert "N4_digit" in rules("飲食店が2軒並ぶ通り", ALLOWED_W15, kanji_strict=False)


def test_w15_first_person_is_caught():
    assert "I1_individual" in rules("私の目の前に飲食店が並ぶ", ALLOWED_W15, kanji_strict=False)


# ---------------------------------------------------------------- I1 と入力由来の「私」
# 第3回の ingest で 10 件(W14 7・W15 3)がすべて偽陽性だった: POI 名の「私立…」「陳家私菜」。
# I1 は **allowed に現れる語を除いた残り**に掛ける(親承認 2026-09-09)。
_ALLOWED_SCHOOL = "店名: 私立青山学院中等部\n業種: 学校\n営業時間: 平日は8時から17時\n"


@pytest.mark.parametrize(
    "text,allowed",
    [
        ("私立青山学院中等部は平日8時から17時。", _ALLOWED_SCHOOL),
        (
            "学校(私立青山学院中等部)がある地上の区画である",
            "この区画から見える店舗と施設(可視の多い順・上位2件): 学校(私立青山学院中等部)\n",
        ),
        (
            "陳家私菜は毎日11時から23時まで営業しています。",
            "店名: 陳家私菜\n業種: 飲食店\n営業時間: 毎日11時から23時\n",
        ),
        (
            "私立実践女子学園中学校は平日8時から17時。",
            "店名: 私立実践女子学園中学校\n業種: 学校\n営業時間: 平日は8時から17時\n",
        ),
    ],
)
def test_input_derived_watashi_passes(text: str, allowed: str):
    """**陽性(通る)**: 入力(POI 名)由来の「私」は個体語ではない。"""
    assert "I1_individual" not in rules(text, allowed, kanji_strict=False)


@pytest.mark.parametrize(
    "text",
    [
        "私は物販店の前に立っている",
        "私の正面に飲食店が並ぶ",
        "僕の右手に物販店がある",
        "我々の前に街区が広がる",
        "あなたの正面に飲食店がある",
    ],
)
def test_real_first_person_is_still_caught(text: str):
    """**陰性(落ちる)**: 人称としての語は、入力に「私立…」があっても残る。"""
    assert "I1_individual" in rules(text, _ALLOWED_SCHOOL, kanji_strict=False)


def test_person_id_is_caught_even_if_the_input_mentions_it():
    """I2(人ID・所持金・内受容)は**本文そのもの**に掛ける(入力で免罪しない)。"""
    got = L.check_individual_words("P-12 が立っている区画", allowed="P-12")
    assert any(x.rule == "I2_agent_dependent" for x in got)


def test_w15_names_from_the_input_pass():
    got = rules("飲食店のpioppinoといちのやが並ぶ通り", ALLOWED_W15, kanji_strict=False)
    assert not got, got


# ---------------------------------------------------------------- 先頭の見出し語
# 第3回のパイロット(親・2026-09-09)で 3 件中 2 件が system の指示文の見出しを本文へ
# 書き写した(「見えるもの: 地上に街区があり…」)。レンダラのテンプレ ``B2.visible`` が
# 既に「見えるもの: 」を持つので、そのまま凍結すると見出しが二重になる。
@pytest.mark.parametrize(
    "raw,want",
    [
        ("見えるもの: 地上に街区があり、サービス店が多い。", "地上に街区があり、サービス店が多い。"),
        ("見えるもの：地上に街区があり、サービス店が多い。", "地上に街区があり、サービス店が多い。"),
        ("見えるもの:  地上に街区があり、サービス店が多い。", "地上に街区があり、サービス店が多い。"),
        ("説明: 地下の通路に面した区画。", "地下の通路に面した区画。"),
        ("区画の説明: 地上の区画。", "地上の区画。"),
        ("店頭表示: ローソンは24時間営業。", "ローソンは24時間営業。"),
        # 引用符でくるまれていても、外したあとの見出しを落とす
        ("「見えるもの: 地上の区画」", "地上の区画"),
        # 見出しが 2 段でも全部落とす(=冪等の担保)
        ("見えるもの: 説明: 地上の区画", "地上の区画"),
    ],
)
def test_leading_heading_is_stripped(raw: str, want: str):
    text, why = L.normalize_generated(raw)
    assert why == "" and text == want


@pytest.mark.parametrize(
    "raw",
    [
        "地上の区画で、見えるもの: は書かない",  # **文中**の見出し語は本文の一部
        "見えるものは特にない",                  # コロンが無ければ見出しではない
        "見えるもの科の店が並ぶ",
        "地上に街区があり、サービス店が多い。",
    ],
)
def test_non_leading_heading_words_are_kept(raw: str):
    text, why = L.normalize_generated(raw)
    assert why == "" and text == raw


def test_normalize_generated_is_idempotent():
    """凍結するのは「通したもの」= もう一度通しても動かない(``verify_one`` の検査)。"""
    for raw in (
        "見えるもの: 説明: 地上の区画",
        "  「Ｊournal Standardの表示。 物販店。」 ",
        "地上の区画で、コンビニエンスストアが見える",
    ):
        once, why = L.normalize_generated(raw)
        assert why == ""
        twice, why2 = L.normalize_generated(once)
        assert why2 == "" and twice == once


def test_heading_only_output_is_empty_not_frozen():
    assert L.normalize_generated("見えるもの:") == ("", "empty")
