# T0 の同値の道具(検収 L4=再現のためリポに置く)

- `ast_equiv.py`: HEAD と作業木の各ファイルを AST に直して比べる(docstring を落とし、`time_consts` から import した名はその値に戻す)。
- `build_probe.py`: 置き換えた build の純粋な関数 16 個を同じ入力で HEAD の写しと作業木の両方から呼び、出力の sha を比べる。
- `manifest_check_t0.py`: 7 つのランの manifest の既存の欄が同じで、増えたのが TM9 の葉だけであることを見る。

使い方は各ファイルの冒頭。入力の置き場(HEAD の写しと作業木)は引数で渡す(絶対パスは書かない)。
