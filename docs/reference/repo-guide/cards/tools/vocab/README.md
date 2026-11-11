# tools/vocab

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 1 本(このディレクトリの直下)

その他のファイル: `synonym_policy_v0.json`

## [adjudicate.py](../../../../../../tools/vocab/adjudicate.py)

adjudicate — 未定義行動台帳 → 契約行の草案(段2)+静的検査(段3)。**ラン後オフライン**。

- 公開の関数とクラス
  - `FleetAdjudicator`(クラス): 実 vLLM 艦隊に 1 語 1 呼・**温度 0**(決定 K)。
  - `MockAdjudicator`(クラス): **決定論の定型草案**を返す mock(テストと配線確認用・LLM を呼ばない)。
  - `Verdict`(クラス): 段3(静的)の判定語。**今日はどれも自動採用ではない**(動的検査が未実施)。
  - `build_prompt`(関数): 1 語ぶんの起草プロンプト(温度 0・1 語 1 呼)。
  - `coverage`(関数): 被覆(決定 A (c)): ``体数 × max(1, セル数) × max(1, 時間帯数)``。
  - `load_policy`(関数): 語彙政策 v0(写し)を読む。
  - `load_registry`(関数): ``shibuya.cli.undefined_registry_payload`` が書いた JSON を読む(形を検査)。
  - `main`(関数)
  - `merge_registries`(関数): 複数ラン(seed 1/2 など)の台帳を合算して語ごとの行を作る(**全件保持**)。
  - `nearest_existing`(関数): 既存語との距離(決定 I (b)・``difflib.SequenceMatcher.ratio``)。
  - `render_report`(関数): 親検収用の Markdown(上位 k 語の表・不採用理由・要動的検査)。**相対パスのみ**。
  - `run_batch`(関数): 段2 起草 + 段3 静的検査を 1 バッチぶん回す(**純関数**・I/O は呼び出し側)。
  - `static_checks`(関数): 段3 の**静的**検査 (s1)〜(s6) → ``(checks, verdict, reasons)``。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.economy.accounts`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.fleet`・`shibuya.llm.undefined`
- 読む試験: `tests/vocab/conftest.py`
- CLI の引数
  - `--budget`: 1 バッチの件数予算(決定 A)
  - `--endpoints`: カンマ区切り http://host:port
  - `--llm`: 裁定 LLM の経路
  - `--model`: served-model-name
  - `--out`: 出力ディレクトリ(drafts.json / report.md)
  - `--threshold-agents`: 被覆の下限 N(体数・既定 10)。未満は保持のみ
  - `--top-k`: 報告に載せる上位語数
  - `registry`: 未定義台帳 JSON(複数可・合算する)
- 決定の ID: D-71

## [registry_from_tape.py](../../../../../../tools/vocab/registry_from_tape.py)

registry_from_tape — 録画テープ(``calls.parquet``)→ 未定義行動台帳 JSON(D-71 段2 の入力)。

- 公開の関数とクラス
  - `cell_by_block`(関数): ``block_id`` → セル ID(取れたブロックだけ)。
  - `main`(関数)
  - `payload_from_tape`(関数): ``shibuya.cli.undefined_registry_payload`` と**同じ形**の dict を作る。
  - `registry_from_tape`(関数): テープ → (台帳, ``(agent_id, tick) → セル``, 走査の計数)。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.tape`・`shibuya.llm`
- 読む試験: `tests/vocab/conftest.py`
- CLI の引数
  - `--out`: 出力 JSON
  - `--tag`: 由来の印(既定=テープのディレクトリ名)
  - `--threshold-agents`: 段2 の閾値 N(既定=台帳の 10)。段2 は起こさない(印のみ)
  - `tape_dir`: calls.parquet のあるディレクトリ
- 決定の ID: D-58・D-71
