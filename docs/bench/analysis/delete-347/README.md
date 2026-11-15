# 第347 削除の段 その 1(S50 の待ち時間の関数・使われていない効き目の上限の定数・pricing の結線しない関数)

> 整理の段(既定のランの結果を 1 バイトも変えない段)。発注: [返事その 8](../../../design/prompt-2026-11-16-reply8.md)
> §1-3 の 2・§3 の表の A72 と S50 の行・§6-3。決定の正: [壁打ちの記録](../../../reference/wallbounce-record-2026-11-02_05.md)
> 2-60(S50)・2-66(C2=世界の側の効き目の上限は採らない)。棚卸し: [表 A #3](../../../reference/inventory-vessels-research-heads-2026-11-09.md)。
> 前の削除の段: [delete-346](../delete-346/README.md)。byte-check の基準 `6d454c50`(枝 `del/347`)。実装役 Opus 5.5・検収と commit は親。

## 0. 要点

- 3 件とも、ランの道(src)から呼ぶ所・読む所が 0 であることを grep で確かめてから消した。消した関数・定数だけを試す試験も
  一緒に消した。
- 消さずに止めたものが 2 つある: `economy.pricing` の型 `PriceSector`・`PriceProposal`。どちらもクラスの名の固定の表
  (`runtime/state/class_ids.py`・`tests/engine/state/class_ids_frozen.json`)に行があり、型を消すと表の網羅の試験が落ちる。
  発注どおり表は変えず、型は残した(§3)。
- つなぎの台帳の行は変えていない。docstring の見出し「expedient(本モジュール分)」の下の項の数(pricing 4・crowd 6)は台帳の
  `what` と試験が見るので、消した物の項は「〔第347 で消した〕…」の注に書き換えて数を保った(§3)。
- 表を 1 つだけ直した: 「tick」を含む識別子の allow の表から `mean_wait_ticks` の 1 行を消した(表の決まり=名が無くなったら
  消す。残すと `test_allow_table_has_reasons_and_no_stale_names` が落ちる)。

## 1. 消したもの

| # | 名前 | 置き場(今) | 行の数 | 呼ぶ所の確かめ |
|---|---|---|---|---|
| 1 | `CrowdProcess.mean_wait_ticks`(M/M/c の平均待ち時間の近似・観測の欄だけ) | `src/shibuya/world/laws/crowd.py`(移す前 `engine/processes/crowd.py:300-307`) | 9 行(関数 8+空行 1)。docstring の項 1 行を注に書き換えた | `mean_wait` で src・tools・tests・docs の `*.py`・`*.toml`・`*.json` を grep=src は定義だけ・tests は `test_crowd.py` の 1 本・`tick_word_allow.json` の 1 行。`getattr` の文字列も無い |
| 2 | `EFFECT_CAP_PER_EXPOSURE`(行動効果キャップ 10⁻⁴〜10⁻³/曝露) | `src/shibuya/perception/attention.py`(段 4 の後も同じ置き場。全ファイルの表の割り先は `foundation/text/salience.py`) | 3 行(`__all__` 1・注 1・定義 1)。docstring の正典の写しの下に注を 1 行足した | `EFFECT_CAP` で同じ範囲を grep=src は定義と `__all__` だけ・tests は値を確かめる 1 行だけ |
| 3 | `economy.pricing` の Calvo の改定・r の適用・逸脱比例コスト・`propose_price` と、それらだけが使う定数: `CALVO_MONTHLY`・`DAYS_PER_MONTH`・`calvo_daily_probability`・`calvo_draw`・`R_MIN`・`R_MAX`・`apply_r`・`DEVIATION_BETA`・`deviation_cost`・`book_deviation_cost`・`propose_price`(11 個) | `src/shibuya/economy/pricing.py` | 154 行を消し 12 行を足した(足したのは docstring の注と型の docstring) | 各名で同じ範囲を grep=src は `pricing.py` の中だけ。`pricing` を import するのは `economy/goods.py` だけで、読むのは `K_VOLUME`・`K_AVERAGE`・`K_PREMIUM`(`CATEGORY_K`)だけ(試験 `test_calvo_is_not_wired_into_the_engine` も同じことを AST で見ている) |

### 一緒に消した試験

- `tests/engine/processes/test_crowd.py::test_mean_wait_is_finite_and_zero_without_a_queue`
- `tests/perception/test_attention.py`: `assert A.EFFECT_CAP_PER_EXPOSURE == (1e-4, 1e-3)` の 1 行。試験の名を
  `test_effect_and_memory_caps_are_declared` → `test_memory_caps_are_declared` に直した(残る 2 行は記憶側上界の値)。
- `tests/economy/test_pricing.py`: `test_calvo_monthly_probabilities_are_by_sector`・`test_calvo_draw_is_deterministic_and_frequencies_match`・
  `test_r_is_clipped_to_the_declared_range`・`test_parse_failure_keeps_the_previous_r_and_is_counted`・
  `test_deviation_cost_is_proportional_to_the_gap_below_the_floor`・`test_deviation_cost_is_booked_as_a_sink_to_the_government`・
  `test_propose_price_is_the_single_entry_point_for_the_llm_scalar`(7 本)と、使わなくなった import(`pytest`・`stream`)。
  係数の試験 `test_floor_k_has_the_three_values_from_h2` とクリアリングの試験は残した。

### 消した後の grep(`*.py`・`*.toml`・`*.json`)

消した 13 の名(`mean_wait_ticks`・`EFFECT_CAP_PER_EXPOSURE`・pricing の 11 個)で src・tests・tools・docs を grep した残り:

| 置き場 | 中身 | 扱い |
|---|---|---|
| `src/shibuya/economy/pricing.py` | docstring の注に `propose_price` の名(2 か所)・型 `PriceProposal` の欄の名 `deviation_cost` | 関数ではない(注と欄の名) |
| `src/shibuya/economy/accounts.py:373` | 名前のある流れの登録 `RegisteredFlow("逸脱比例コスト", …, "pricing.deviation_cost")` の出どころの文字列 | 呼んでいない(ラベル)。表は manifest の流れの表と保存則の検算の登録に入るので触っていない(§3・親への問い) |
| `tests/engine/processes/test_rate_rules_1101.py:230-289` | Calvo を結線しないことを見る AST の試験の名の集合 `_CALVO_NAMES` と負の対照の植えた文 | 呼んでいない(見張り)。名が無くなっても試験の意味は残る(親への問い) |

docs の記録の文(`*.md`)に残る言及の数は §4 に書いた。

## 2. 効き目の上限の定数の一覧(発注 2 の調べ)

src の大文字の定数で `CAP`・`MAX`・`LIMIT`・`CEIL` を含むもの全部(約 120)と、「効果・効き目・影響・反応」+「上限・上界・キャップ」の
注、`exposure`・`曝露`、看板・広告・呼びかけの名(`SIGNAGE`・`AD`・`BROADCAST`・`NOTICE`・`WOM`・`NORM` ほか)+`CAP`・`MAX`・
`WEIGHT`・`EFFECT`・`PROB` の名を grep した。「看板・広告・呼びかけが行動に与える効き目に上限を掛ける」役の定数は
`EFFECT_CAP_PER_EXPOSURE` の 1 つだけだった。

| 定数 | 置き場 | 役 | 読む所 | 扱い |
|---|---|---|---|---|
| `EFFECT_CAP_PER_EXPOSURE` | `perception/attention.py` | 行動効果の上限[/曝露] | 無い(値の試験だけ) | **消した** |
| `MEMORY_CAP_RECOGNITION`・`MEMORY_CAP_RECALL` | `perception/attention.py` | 記憶側上界(1 曝露の再認 0.40・再生 0.08) | src に無い(定義と `__all__` だけ)・試験 `test_attention.py::test_memory_caps_are_declared` が値を見るだけ | 残した(発注どおり・役が違う) |
| `BUDGET_ADS`・`BUDGET_SALIENT`・`BUDGET_OVERHEARD` | `perception/attention.py` | 知覚の注意予算(1 刻みに載る件数) | `BUDGET_SALIENT` は `world/laws/salient.py:403`。`BUDGET_ADS`・`BUDGET_OVERHEARD` は src に無い(試験だけ) | 残した(効き目の上限ではない=知覚の件数) |
| `CONTENT_CAP_*`・`GAZE_SECONDS_DEFAULT` | `perception/attention.py` | 一目で読める字数の上限(段 3) | `content_cap_chars`・`tag_world_text` | 残した(記録 2-66 の A2 の器) |
| `STORE_SCORE_P_CAP` | `mind/memory/store_memory.py` | 店の記憶の行の順位(精度の頭打ち) | `store_memory.py:392`・`memory.py:490-498` | 残した(役が違う) |
| `WOM_WEIGHT` | `mind/memory/wom.py` | 口コミの記憶の重み | 同ファイル | 残した(上限ではない) |

`MEMORY_CAP_*` の使われ方: 読む所は src に無い。記録 [R-48](../../../research/v2-r48-own-code-memory-range-return.md) の
「これを使う記憶の実装は見つからなかった」と同じ。

## 3. 残したものと理由

| もの | 理由 |
|---|---|
| `K_PREMIUM`・`K_AVERAGE`・`K_VOLUME` | 発注どおり。`goods.CATEGORY_K` が使い、既定のランの補充の代金と参入資本に効く |
| `StoreKind`・`K_BY_KIND`・`floor_price` | 係数の側(H-2 の内生フロア)。src からの呼び手は消した `propose_price` だけだったが、係数の試験が `K_BY_KIND`・`floor_price` を使う。`StoreKind` はクラスの名の固定の表に行がある。消すかは親(§7) |
| `clearing` | 発注の 3 つ(Calvo・逸脱比例コスト・`propose_price`)のどれでもなく、それらからも呼ばれていない。src からの呼び手は無い。消すかは親(§7) |
| `PriceSector`・`PriceProposal`(型) | クラスの名の固定の表に行がある(`class_ids.py:79-80`・`class_ids_frozen.json:60-61`)。型を消すと `tests/engine/state/test_class_ids.py` の網羅と凍結の 2 本が落ち、表を作り直す道具 `docs/bench/analysis/move-346/tools/gen_class_ids.py` が 2 行を落とす。発注の「表は勝手に変えない」に従い、型は残して docstring に注を書いた |
| docstring の見出し「expedient(本モジュール分)」の下の項の数 | つなぎの台帳の行 `HD-economy.pricing-1af925f4`(項 4 個)・`HD-engine.processes.crowd-1af925f4`(項 6 個)の `what` と、項の合計の試験(`tests/engine/bridging/test_bridging_ledger.py`)が見る。台帳を直すと manifest の `bridges_version` が動くので、消した物の項は「〔第347 で消した〕…」の注に書き換えて数を保った(pricing は β と Calvo の薄め方の 2 項・crowd は M/M/c の 1 項) |
| 正典の写し(`crowd.py` の「M/M/c 近似」・`attention.py` の「効果キャップ=行動効果10⁻⁴〜10⁻³/曝露」・`pricing.py` の H-1・H-3・H-5) | 設計書と契約書の逐語の写しなので変えず、`attention.py` と `pricing.py` には写しの下に〔第347 注〕を足した |
| `accounts.DEVIATION_COST`・`FLOW_REGISTRY` の「逸脱比例コスト」の行・`world/ledger/absent.py` の「pricing.py の改定はエンジンに結線されていない」の行・`world/laws/switch_rate.py` の規則 `calvo`(計数 `calvo_draws`) | manifest と保存則の検算の表に入る文字列。消した関数を呼んではいないので触っていない |

## 4. 名の凍結・表・台帳に当たったもの

| 表 | 当たった名 | 扱い |
|---|---|---|
| クラスの名の固定の表(`runtime/state/class_ids.py`・`tests/engine/state/class_ids_frozen.json`) | `shibuya.economy.pricing.PriceProposal`・`PriceSector`・`StoreKind` | 表は変えていない。型は 3 つとも残した(§3) |
| 名の凍結(`tests/engine/state/names_frozen.json`) | 無い | — |
| つなぎの台帳(`docs/design/bridging-ledger.json`) | `HD-economy.pricing-1af925f4`(項 4)・`HD-engine.processes.crowd-1af925f4`(項 6)・`HD-perception.attention-1af925f4`(項 4・消した定数は項に無い)・pricing を文で言う行 1 つ(`pricing.py` の改定は結線されていない) | 台帳は変えていない。項の数は保った(§3) |
| 状態の台帳(`runtime/state/ledger.py`)と AST の許可(`ledger_ast.py`) | crowd の行(`crowd.py:184`・`:231`・`:242` などの行の番号の注) | 消したのは 297 行より後ろで、docstring の行の数も同じ=前の行の番号は動いていない。pricing・attention の行は無い |
| 乱数の検査(`validation/static/rng_audit.py`) | `perception/attention.py` の `gate_stage1`(消していない) | — |
| `__all__` | `pricing` から 11 個・`attention` から 1 個を外した | 再輸出する頭は無い(grep) |
| 「tick」の語の allow の表(`tests/engine/time/tick_word_allow.json`) | `mean_wait_ticks` | 1 行消した(表の決まり=古い行を残すと落ちる) |
| 時間の直書きの allow の表(`time_literal_allow.json`) | 無い | — |

docs の記録の文(`*.md`)に残る言及(カードの作り直しの後・消した 13 の名): 本書を除いて 12 本・17 か所。内訳は記録と設計の文
11 本・16 か所(返事その 8 が 3・`repo-guide/catalog/a-body-and-town.md` が 3・棚卸しの表が 2・ほか 8 本が 1 ずつ)と、
カード `cards/src/shibuya/economy/README.md` の 1 か所(pricing の docstring の注をそのまま写したもの)。記録の文は直していない。

## 5. 確かめ(実装役が回したもの)

作業木 `del/347`(頭 `6d454c50`)・venv は本体・`PYTHONPATH` は作業木の src・`-n` なし。

| 確かめ | 結果 |
|---|---|
| 関わる試験(`-m "not gpu and not slow"`) | `tests/perception/test_attention.py` 26・`tests/economy/test_pricing.py` 2・`tests/engine/processes/test_crowd.py` 15・`tests/test_places_guard.py` 16・`tests/engine/time/test_t0_no_tick_word.py` 6・`tests/engine/time/test_t0_literal_count.py` 4・`tests/economy/test_accounts.py` 13・`tests/engine/bridging/test_bridging_ledger.py` 40・`tests/engine/state/test_class_ids.py` 12 = 134 passed |
| 状態の台帳の試験 | `tests/engine/test_state_ledger_10b.py` 73 passed(4 分 36 秒) |
| Calvo を結線しない見張り | `tests/engine/processes/test_rate_rules_1101.py -k calvo` 2 passed |
| 読み手の側 | `tests/economy/test_goods.py` 21・`tests/economy/test_entry_capital.py` 20・`tests/engine/test_area_source_c9c.py` 14・`tests/perception/test_signage_p_see_gate.py` 31 passed |
| `lint-imports --no-cache` | 10 kept・0 broken |
| `tools/bytecheck/astsame.py --base HEAD` | 変わった src 3 本とも structure(`economy/pricing.py`・`perception/attention.py`・`world/laws/crowd.py`)・終了コード 2(消したので想定どおり) |
| カード `tools/repo_guide/build.py` → `--check` | 作り直した(150 本)→「最新」。本段と関係の無い差も入った: `cards/README.md`・`cards/docs.md` は HEAD の前の commit で足された記録(`astsame-347`・`sealed-tokens-347`・tests/tools と tools/bytecheck と tools/instruments の数)と本書の置き場を拾った。`foundation/README.md` は `foundation.rng` を読む試験から `test_pricing.py` が外れた分 |
| 秘密の走査(変えた・足したファイル 17 本) | CLEAN |
| `tests/c7` | 回していない(発注どおり) |

## 6. byte-check と範囲の試験(親が回した)

| 確かめ | 結果 |
|---|---|
| byte-check 19 構成(`tools/bytecheck/cli.py run --base 6d454c50 --src <作業木の src> --set all19 --jobs 6`) | **19 構成・37 欄すべて同じ(動いた 0・誤り 0・final が同じ 19)・終了コード 0**。既定の final は `c8d68704b7b0760d`・呼数 60,939 のまま。全体の壁時計 426 秒(6 本並列。裏でほかの役のランが回っていた=参考値)。記録 [bytecheck/](bytecheck/) |
| 範囲の試験(`pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`・linked の作業木) | 6,797 passed・4 skipped・1 xfailed・**1 failed**。落ちたのは前からの 1 本(`tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`=linked の作業木でだけ落ちる)。「git が無い」「commit が無い」で飛んだ試験は 0 |
| 基準の commit と取り込みの commit の間 | byte-check の基準は `6d454c50`。取り込みの前に本体は `0716cc53` まで進んだが、その間の commit は src を 1 本も変えていない(`git diff 6d454c50 0716cc53 -- src` が空)。だから byte-check の結果はそのまま取り込みの木に当てはまる |

## 7. 親への問いと、親の扱い(第347)

親の扱い: 1〜6 とも、今回は実装役の形のまま取り込んだ(残したものは残したまま・表と台帳は変えない)。型 2 つと、呼び手の無い `StoreKind`・`K_BY_KIND`・`floor_price`・`clearing`・`BUDGET_ADS`・`BUDGET_OVERHEARD`・`MEMORY_CAP_*` は、返事その 8 が名指しした消すものの外なので、第 347 の報告でユーザーに上げる。manifest に出る文字列(問い 3・4)は、直すと `bridges_version` などが動くので、次の版上げで扱う。

実装役が挙げた問い:


1. 型 `PriceSector`・`PriceProposal` を消すか。消すなら、型 2 つを消して `docs/bench/analysis/move-346/tools/gen_class_ids.py` で
   表と凍結の JSON の 2 行を落とす(ハッシュに入る名は、どちらも作られる所が無いので動かない見込み)。
2. 係数の側の `StoreKind`・`K_BY_KIND`・`floor_price` と、`clearing` を残してよいか(どれも src からの呼び手は無い)。
3. docstring の見出しの下に「〔第347 で消した〕…」の項を残して項の数を保った形でよいか。項を消すなら、つなぎの台帳の 2 行の
   `what`(pricing 4 → 2・crowd 6 → 5)と項の合計の試験を直し、manifest の `bridges_version` が動く。
4. `accounts.FLOW_REGISTRY` の「逸脱比例コスト」の行の出どころの文字列 `pricing.deviation_cost` は、消した関数を指したまま。
   科目 `DEVIATION_COST` と流れの登録をどうするか(登録の表は保存則の検算と流れの表に入る)。
5. 見張りの試験 `test_calvo_is_not_wired_into_the_engine` の名の集合 `_CALVO_NAMES` に消した名が残る(試験は通る)。そのままでよいか。
6. `BUDGET_ADS`・`BUDGET_OVERHEARD`(知覚の件数の予算)も src から読まれていない。効き目の上限ではないので消していない。
