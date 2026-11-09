# -*- coding: utf-8 -*-
"""bytecheck — 決定論の確かめ(byte-check)の道具。基準の commit と比べる側の src で同じ構成を回し、25 欄を比べる。

発注: ``docs/design/prompt-2026-11-09-reply7.md`` §2 の 4(byte-check を ``tools/`` に置き、版上げの手順から 1 行で呼ぶ。
CI では回せない=作者の機械で回す)。前の道具 ``docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py`` の働きを
引き継いだ(記録の再現のため前の道具は消さない)。使い方は ``tools/bytecheck/README.md``。

モジュール
    - ``configs``: 19 構成の表・構成の組(all19・parent4・arms)・比べる 25 欄・記録に残す切替口の環境変数。
    - ``tree``: 写す追跡ファイルの一覧と src の走査(取りこぼしの検査)・git archive の写し・data へのつなぎを置いて外す。
    - ``check``: ``one``・``side``・``compare``・``run``。
    - ``cli``: 入口(``python tools/bytecheck/cli.py …``)。
"""
