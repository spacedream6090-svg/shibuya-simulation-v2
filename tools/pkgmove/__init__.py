# -*- coding: utf-8 -*-
"""pkgmove — コードの区分の移動の道具(移す段 3・返事その 7 §4-2・計画 docs/reference/package-map-final-2026-11-09.md §7-4)。

全ファイルの表から作る対応表(``map.toml``)に従って、ファイルを新しい置き場へ移し、次の 3 つだけを書き換える(許可の一覧):

    (a) src・tests・tools の Python の import の文(AST で見つけ、文の該当の部分だけ。再輸出の頭を通る import は元のモジュールへ)
    (b) 計画 §7-5 で「段 3 の道具で直す」とした道の文字列の表((ファイル, 記号) の一覧=``allow.py`` と ``allow_tests_tools.toml``)
    (c) 固定の表 ``class_ids.py`` の鍵だけ(値=凍結の名は変えない)
    (d) つなぎの台帳の道の対応の表 ``engine/bridging/ledger_paths.py`` に、移したファイルの「今の道 → 台帳の道」を足す

ほかの文字列の定数・docstring・注・docs は書き換えない。既定は書かずに差分と報告だけを出す(``--apply --tree`` のときだけ書く)。
書く前に凍結の値(names_frozen.json・class_ids_frozen.json・道の形の名 74 種)が残ることを確かめ、変わるなら書かずに止める。

モジュール
    - ``table``: 全ファイルの表を読む・対応表 TOML の書き手と読み手・保留の一覧(1 か所)・段の名。
    - ``model``: 木(ファイルの中身を手元に持つ)・モジュールの索引・頭の再輸出の引き先。
    - ``imports``: import の文の書き換え。
    - ``allow``: 許可の一覧(src の表と、tests と tools の (ファイル, 記号))・記号の決め方。
    - ``strings``: 道の文字列の書き換えと、触らなかった道の形の文字列の拾い。
    - ``classids``: 固定の表の鍵の書き換えと鍵の守り(同じ ``__qualname__`` の組の取り違えを止める)。
    - ``ledgerpaths``: (d) つなぎの台帳の道の対応の表の書き足しと守り(台帳の JSON は書き換えない)。
    - ``guard``: 凍結の値の守りと、許可の一覧の外が変わらないことの確かめ。
    - ``move``: 段を選んで計画を作る・報告・木へ書く。
    - ``cli``: 入口(``python tools/pkgmove/cli.py …``)。使い方は ``tools/pkgmove/README.md``。
"""
