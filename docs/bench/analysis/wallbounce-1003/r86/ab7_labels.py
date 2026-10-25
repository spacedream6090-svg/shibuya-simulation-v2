# -*- coding: utf-8 -*-
"""R-86: AB7 seed 1 の無作為 300 行(ab7_sample300.json)に、実行役(Opus 5.5)が原文を読んで付けた手の分類。

各行 = "目的コード 損失コード"。辞書を通さずに、理由・行動・対象・ひと言を読んで決めた。

目的コード(縦軸の分類への割り当て。社会生活基本調査 R3 調査票B の小分類コードを括弧に):
  E 食事(431〜434)/ D 軽飲食・喫茶(435)/ S 買い物(231)/ R 休養・くつろぎ(561)
  X 行き先の定まらない移動・街歩き(612 その他の移動。NHK「行楽・散策」)/ O 観察・確認(調査票Bに該当なし。Gehl 系の commercial_observing・recreation_passive)
  A 雨宿り・避難(該当なし)/ Q 待つ(店や施設が開くのを待つ。Gehl 系の waiting)/ N 夜の娯楽(5301 教養・娯楽)/ U 判別できない

損失コード(段0 辞書が写した語と、読んだ意味の比べ):
  n 意味は落ちていない(行く→移動 で対象が書かれている、買う→購入 など)
  k 軽微(写した語で行為の一部は残る。例: コンビニで「食べる」→購入=買うことはできるが食べることが落ちる)
  t 対象の損失(探す・探索→移動 で行き先が無い、行き先が理由にだけ書かれ対象欄が「なし」)
  m 意味の損失(別の行為に畳まれる。例: 飲食店で「食べる」→購入)
  v 語彙の語をそのまま書いた行(段0 を通らない=分母に入れない)
  u 辞書に無く写されなかった行(未定義=分母に入れない)
"""

LABELS = """
E m|E m|E n|X v|E n|E n|E n|E n|E n|E m|E n|D n|E v|E n|E n|D n|E v|D n|E n|E m|
S n|E n|E m|E n|E n|E n|E n|E m|E n|E m|E n|X n|E n|E n|E n|E m|E n|E n|E m|E n|
E n|E n|E n|E n|E n|E n|E n|E m|E n|E n|E m|E n|E m|E n|D n|S n|E m|E k|E n|E n|
O n|E n|E n|E n|E k|E k|E n|E n|E n|E n|E n|E n|D n|E m|E n|E n|E k|E n|E n|E m|
E n|E m|E n|E n|E v|E k|E n|E m|E m|E n|E m|E m|E n|E n|E n|E m|E n|E n|E n|E k|
E n|E n|E m|E m|E n|E k|E k|E k|E k|E m|E n|E m|E m|E n|E n|E n|E n|E m|E n|E k|
E n|E m|E m|E n|E n|S n|E m|E n|R v|D n|E m|E t|E n|E m|E n|E m|S v|E n|E t|E m|
E m|E n|E n|E n|E n|E v|E n|E n|E m|E m|U n|E m|A u|E k|E k|E m|E n|A n|E n|E n|
E n|E k|E m|E k|E m|E v|E m|E m|E m|E m|E n|E m|D n|E n|E k|D k|S n|E m|E n|E n|
D n|E n|E n|U n|E m|E k|R v|E n|R v|E n|E n|E m|E k|E m|E m|E m|E n|O u|E t|E n|
E m|E k|E k|E n|E n|E m|E k|E m|E n|E m|E m|E m|E n|D n|D t|E m|E k|E n|E n|E k|
E n|E n|E n|E n|E n|O u|E m|E m|E m|E n|E n|E n|E n|E m|E n|E n|E n|E n|E k|E n|
E k|E m|E n|E k|E n|E n|E m|E n|E t|E m|E n|E n|E n|E n|D n|E k|E n|E m|E n|E n|
E n|R v|E n|E n|E n|D v|E n|E m|E v|E n|E m|E n|E m|E u|E n|E v|E n|E n|E k|E m|
D n|E n|E n|E n|Q v|E m|E m|E n|E n|E n|E n|E n|E n|D n|E n|E m|E m|E m|N n|E n
"""


def labels() -> list[tuple[str, str]]:
    out = []
    for tok in LABELS.replace("\n", "").split("|"):
        tok = tok.strip()
        if tok:
            p, l = tok.split()
            out.append((p, l))
    assert len(out) == 300, len(out)
    return out
