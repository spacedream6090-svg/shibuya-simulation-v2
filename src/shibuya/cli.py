"""shibuya.cli — ``python -m shibuya.cli`` の入口(外との約束)。中身は ``shibuya.interfaces.cli.main``(割る段 5b)。"""

if __name__ == "__main__":
    from shibuya.interfaces.cli.main import main

    raise SystemExit(main())
