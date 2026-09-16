# 「自由意図」腕(open-intent arm)の仕様 — ブランチ build/open-intent(2026-09-16・第199)

<!-- hdr:v1 -->
- **分野**: 計算社会科学 #25 / 自然言語処理 #27 / ABM方法論 #21 | **重要度**: P0 | **状態**: **ユーザー承認済(09-16「1. 回して欲しい」「2. 見せないを先に」)・実装は Opus 5 サブ・検収は親**
- **一次確認**: 本書の数値(35 分/本・6.94 呼/体/日・0.7%)は C8 受入報告・c7-day-4 受入表・D-68 答申の実測。設計上の判断は親(Fable)。
- **索引**: [INDEX.md](../research/INDEX.md) ・ **計画**: [v2-schedule-and-research-plan-2026-09.md](v2-schedule-and-research-plan-2026-09.md) ・ **行動契約書**: [v2-action-contract.md](v2-action-contract.md) §7

> **問い**: LLM に 24 語のホワイトリストを見せるのをやめ、自由文の意図を出させてエンジン側で接地(§7 段0〜1)すると、何が起きるか。**測るまで分からないので腕として回す。**
> **不変の線**: 既定(`intent_mode="vocab"`)の**バイト・ハッシュ・呼数・テストは一切変えない**。腕は切替口の裏にだけ存在する。効果(effects)・前提(preconditions)・保存則はエンジンが持ち続ける=**「入口は自由、効果は閉じる」**。

---

## 1. 何を測るか(5 数・両腕とも同一条件で)

| # | 数 | 定義 | 出所 |
|---|---|---|---|
| M1 | **接地率** | 応答のうち `行動` 欄が **24 語に直接一致**した割合 + **段0 辞書(`undefined.SYNONYMS`)で写せた**割合(2 段で報告) | parse → `ParseResult.action` / `dictionary_candidate` |
| M2 | **未定義率** | 24 語にも段0 でも写せず `UNDEFINED_ACTION`(→待機)へ落ちた割合 | `UndefinedActionRegistry.counters()` |
| M3 | **上位未定義語** | 正規化後の語 × 出現数 × **distinct agents**(§7 段2 の閾値 N=10 に届いた語を印) | `registry.top_words(k=30)`・`distinct_agents(word)` |
| M4 | **行動エントロピー** | 解決後の行動コード分布のシャノンエントロピー[bits]+**24 語のうち出現した種類数** | 既存の行動語分布(ablation_runner の JSD 計算と同じ元) |
| M5 | **費用** | 呼数・呼/体/日・壁時計・tokens_out の平均・書式エラー率(実効/厳密) | 受入表 L4 と同じ集計・calls.parquet |

**判定の書き方**: 合否は出さない(探索的な腕)。ただし事前に書く予想: 接地率(直接)は vocab 腕 ≈1.0 → open 腕で**下がる**。open 腕の M3 上位語に「待ち合わせ/会う/探す/見る/帰る」系が出れば §7 段2 の**最初の起草材料**。M4 は open 腕で上がると予想(D-68 の 0.7% 問題の動詞側)。M5 の tokens_out は open 腕で微増と予想。

## 2. 切替口

| 層 | 変更 | 既定値 |
|---|---|---|
| `engine/run.py` | 設定 dataclass と `run_day(...)` に **`intent_mode: str = "vocab"`**(`"vocab"` \| `"open"`)。`signage`・`budget_mode`・`derive_rule` と同じ配管 | `"vocab"` |
| `cli.py` | `--intent-mode {vocab,open}`(既定 vocab)。`--no-signage` と同じ場所・同じ渡し方 | vocab |
| `perception/templates.py` | **`OUTPUT_SPEC` は触らない**(B0 凍結・SHA 固定)。新たに `OUTPUT_SPEC_OPEN` を追加: `行動:` の指示を `<いま自分がしたいことを 10 字以内の動詞句で>` に置き換え、**それ以外の行(理由・対象・ひと言・2 行形・JSON 禁止)は同文**。`B0_SYSTEM_OPEN` を組み、レンダラが `intent_mode` で選ぶ | B0_SYSTEM |
| `engine/llm_bridge.py` | **変更なし**(第199 訂正)。親が `tests/engine/test_undefined_action.py` と `undefined.py` を読んで確認: **段0 辞書写像(`SYNONYMS` 100 語・`map_synonym`)は既に bridge の `undefined.observe` で主経路に結線済み**(`undefined_stage==0`・`n_undefined_mapped`)。段1(記録+失敗フィードバック+待機)も結線済み。**段2 `adjudicate` は実装済みだが本番では `adjudicator=None` のため発火しない**(run.py/cli.py に注入口なし)。段4 `adopt` は親の手動。→ 本腕はプロンプトの差だけで測れる | 現行 |
| `llm/undefined.py` | 変更なし。段2 は `adjudicator=None` のため本番で発火しない(=この腕では記録と計数のみ)。閾値 N=10 到達語は M3 で印を付ける | — |
| `tools/c8/ablations_v1.json` | 腕 **`AB7-OPEN-INTENT`** を追加: `runs=[{tag:"vocab", kwargs:{intent_mode:"vocab"}, is_baseline:true},{tag:"open", kwargs:{intent_mode:"open"}}]`・`switch.kind="implemented_flag"`・`mock_effective:false`(MockLLM はプロンプトを読まない=腕の差は実 LLM でしか出ない・AB1 と同じ注記) | — |
| `tools/c8/ablation_runner.py` | 集計に M1〜M3 を追加(`registry.counters()`・`top_words`・parse 段階の 2 段接地率)。**既存腕の出力 JSON は列追加のみ・値不変** | — |

**プロンプトの差は `行動:` の 1 行だけ**。`対象` 欄の制約(セルID / 物のカテゴリ / 人ID / なし)は**残す**——エンジンが対象の型を要るのは効果を閉じるためで、ここは「入口の自由」の範囲外。

## 3. 実行(親)

```
python tools/c8/ablation_runner.py --arm AB7-OPEN-INTENT --run-id ab7_s1 --seed 1 \
  --world data/world/v2 --agents 5000 --ticks 1440 --out docs/bench/c8 \
  --temperature 0.7 --max-tokens 96 --fleet-wait-s 120
```
- 2 腕 × 5,000 体 × 1,440 tick・実 LLM(7×Qwen3-8B INT8)。C8 実績 **35 分/腕**。seed 2 も回す(再現性・帰無 0.0035 bits の参照は T7)。
- 出力: `docs/bench/c8/ablation_AB7-OPEN-INTENT*.{json,md}`・テープ `c8_tapes/AB7-OPEN-INTENT__{vocab,open}`。記録のパスは `<repo>/`・`~/` にマスク(第175 の教訓)。
- 親の検収: (1) 既定経路の**バイト不変**=`mock 実資産 5,000 体×1 日`(`python -m shibuya.cli --agents 5000 --seed 1 --world data/world/v2`)の checkpoint が現行 HEAD(1e20cd3 以降 src 変更なし)の値と一致: **v2 既定 `ba01bd0beed19666…`・`--derive-rule v2.1` `4fb0f2ec42ee57ab…`**(第200 親実測・両方一致。第199 版に書いた `d5d79337…` は C6-C8 当時の古い値=訂正)。リダイレクト時は `PYTHONUTF8=1` が要る(summary の「≤」が cp932 で落ちる) (2) `pytest tests/perception tests/engine tests/llm tests/c8 tests/test_cli*` 緑 (3) `lint-imports` 層契約 (4) 腕 JSON の M1〜M5 を親が calls.parquet から再計算して一致。

## 4. 受入(サブ → 親)

サブは「テスト名と結果表」で報告(自己申告の完了は不採用・§9.2)。必須で緑:
`tests/perception/test_templates.py`(B0 SHA 不変)・`tests/perception/test_renderer_golden.py`・`tests/engine/test_undefined_action.py`(既定経路の固定点)・`tests/c8/*`(105 本+腕定義表の検証)・`tests/test_cli*`。**新規テスト**: (a) `intent_mode="open"` で `OUTPUT_SPEC_OPEN` が選ばれ B0 の SHA が変わる(=切替が効く) (b) 既定で B0 の SHA が現行値のまま (c) 既定・open の両方で段0 写像が同じに効く(例「探索」→「移動」・既存テストで担保)(d) ablations_v1.json に AB7 が増えて既存腕の定義がバイト不変。

## 5. 決めないこと(この腕の範囲外・S2 へ)

段2 の発火(裁定 LLM)・語彙への採用・対象欄の自由化・W17 台本の緩和(②)。**この腕は「入口を開けたら何が見えるか」だけを測る。**

## 6. expedient 登録(本書分)

| 項目 | 値 | 検証 |
|---|---|---|
| 自由意図の指示文(10 字以内の動詞句) | 親の自前文 | 本腕(語数上限 6/10/20 の副腕は結果次第) |
| 段0 辞書 `SYNONYMS`(v2) | 既存 | M1 の 2 段目で効き目を測る |
