# 工程 C0(骨格)受入報告(2026-09-08・ブランチ build/c0-c4)

> 根拠: 実装計画書 §9.1 C0 行・§9.5(証拠は親自身の実行出力のみ)・§9.6 層2。作業=親(Fable)+サブ2本(Opus: manifest / 予算表+世界カタログ)。サブの報告は証拠にせず、以下はすべて親が実行した出力。

## 1. 成果物(§9.1 C0 の内容との対応)

| §9.1 の項目 | 成果物 | 状態 |
|---|---|---|
| リポ構造(manifest/build/core/world/agents/perception/llm/engine/economy/census) | `src/shibuya/<10 packages>/__init__.py`(層の役割を docstring に記載)・`pyproject.toml`(src レイアウト・部品表 §2 の依存) | 済 |
| import-linter 層契約 | `pyproject.toml [tool.importlinter]` 契約5本(層順・core は何にも依存しない・llm は world/agents を import しない・build は実行時に import されない・economy は transfer API 経由のみ) | 済(5 kept / 0 broken) |
| pytest/hypothesis 骨格 | `tests/`(5ファイル・57テスト=層2指摘の追加4本を含む)・`[tool.pytest.ini_options]`(markers gpu/slow) | 済 |
| CI(GitHub Actions) | `.github/workflows/ci.yml`(pip install → 秘密スキャン → lint-imports → pytest(not gpu/slow) → data/ 未追跡検査) | 済(定義・初回実行はプッシュ後) |
| 秘密スキャン pre-commit | `.githooks/pre-commit`(ステージ済みファイルを scan_secrets へ・data/ のステージ拒否)・`git config core.hooksPath .githooks` | 済(ローカル設定) |
| 予算宣言の機械読取(P/M/S/L 行) | `src/shibuya/core/budget.py`(`load_budget_table`・34行=W3/P7/M12/L7/S4+I1・`parse_limit` best-effort) | 済 |
| 世界カタログ分母ファイル(SHA 34f9fa9d) | `src/shibuya/build/catalog_freeze.py`(凍結規則を復元)→`src/shibuya/manifest/frozen/world_catalog_v0_2.json`(57クラス)・`src/shibuya/manifest/world_catalog.py`(`verify_frozen`) | 済(SHA 再現) |
| manifest 正規化(pydantic) | `src/shibuya/manifest/schema.py`(13節・機械化規則 a–e)・`canonical.py`(正規化本文・run_id=blake3 自己ハッシュ・YAML往復) | 済 |
| (追加)RNG ドメイン分離 | `src/shibuya/core/rng.py`(Philox4x64・鍵=blake3(seed‖domain)・カウンタ=個体/tick)+hypothesis 性質テスト(T4 規模不変性) | 済 |

## 2. 受入(§9.1 検収列: CI緑・層契約違反0・manifest往復一致)= 親の実行出力

```
$ .venv/Scripts/python.exe -m pytest -p no:cacheprovider -o addopts="" -q
.....................................................                    [100%]
53 passed in 0.94s   (層2指摘の修正後に再実行: 57 passed in 0.93s / exit=0)
pytest exit=0

$ .venv/Scripts/lint-imports.exe
Analyzed 17 files, 3 dependencies.
layers: census > economy > engine > (perception | llm) > (world | agents) > core > manifest KEPT
core は何にも依存しない(manifest も import しない) KEPT
llm は world/agents を import しない(mock LLM が成立する) KEPT
build は実行時に import されない KEPT
economy は engine の transfer 単一API経由のみ(world/agents 直接書き込み禁止) KEPT
Contracts: 5 kept, 0 broken.
lint exit=0

$ python tools/scan_secrets.py <tracked+untracked 190 files>
CLEAN
scan exit=0

$ git ls-files data | wc -l
0
$ git branch --show-current
build/c0-c4

$ .venv/Scripts/python.exe -m shibuya.build.catalog_freeze   (再実行で md5 不変)
version=v0.2 sha16=34f9fa9d316587be n_classes=57
```

テスト内訳: manifest 17(往復一致・T1自己ハッシュ・キー順/空白不変・欄変更で run_id 変化・規則 a/b/c/d/e の拒否と偽陽性ガード)・RNG 6(同入力同列・ドメイン分離・T4 規模不変・型取り違え・入力検査・既知解)・予算表 ≈15(34行・33行の固定集合・カテゴリ・M8→(24,GB)・S1)・世界カタログ ≈15(SHA 再現・57行・列名・凍結 JSON の再生成が byte 一致・CR 不在)。

CI「緑」は GitHub 上での初回実行を待つ(ローカルで同じコマンド列が通っていることを上で示した)。

## 3. 停止句の判定

- (a) 台帳・予算・ライセンス・憲法・設計書の決定項に触れる分岐: **なし**(設計書の変更は §8 expedient 登録簿への追記のみ)。
- (b) 世界カタログ分母 SHA: 第92の凍結スクリプトから規則を復元し **34f9fa9d316587be を再現**=該当せず。
- (c) 外部データ取得: なし。

## 4. expedient(登録済み: 実装計画書 §8 C0 節)

rng 鍵導出形式/正規化のリスト順序保持と run_id 除去/診断列・保存則検算の命名/IPv4 判定の安全側/予算行 I1 の包含と parse_limit の規則/カタログ凍結規則の復元と `frozen/` 命名/pre-commit の実装形。

## 5. 次工程への持ち越し

- C1∥C2 を並列に開始(§9.3)。C1 は取得レーン §3 のデータが data/ に揃っていることが前提(PT・OSM・センサス・騒音・気象は取得済み)。
- CI の初回実行(プッシュ)は main へのマージ時=ユーザー。
- `warp-lang` の sm_120 対応は未確認のまま(C2 の GPU テストはセルフホスト段)。

## 6. 層2 独立検収(別インスタンスの Fable・docs/ops/layer2-review-checklist.md)

**判定: 合格(条件付き懸念3件)**。レビュー役が自分で実行: pytest 53 passed / lint-imports 5 kept 0 broken / 秘密スキャン CLEAN(追跡+未追跡29) / SHA 独立再計算 34f9fa9d316587be / `git diff --stat main -- docs/design/` = 実装計画書 §8 への +8 行のみ / data 未追跡 / ブランチ build/c0-c4。敵対的検査として層契約に違反 import を5種注入し全件 BROKEN を確認。

指摘と処置(コミット前に親が反映):
| 指摘 | 処置 |
|---|---|
| `core.autocrlf=true` で md が CRLF 化すると凍結 SHA テストが落ちる | `.gitattributes`(`* text=auto eol=lf`・バイナリ指定)を追加 |
| `test_known_answer_is_stable` が固定値を比較していない(空検査) | 既知解 4 件を固定(鍵2組・整数列2組) |
| rng.py docstring の鍵入力形式が実装と不一致 | docstring を実装(`i:`/`s:` 接頭辞)に合わせて修正 |
| 規則(c)に `VLLM_MARLIN_USE_ATOMIC_ADD=0` の検証がない / `phases` が未固定 | schema に定数と検証を追加+テスト4本(tests/test_manifest_rules_extra.py) |
| pre-commit の `$files` 非引用 | NUL 区切り(`-z`/`xargs -0`)に書き換え |
| expedient 未登録(正規化の符号化・http 拒否・run_id None・budget 環境変数・凍結 JSON 書式・pyproject 設定) | 実装計画書 §8 C0 節へ追記 |

持ち越し(C2/C3/C4 で対処): 層契約は現状ほぼ空(依存3本)=C2 で `shibuya.engine.transfer` を独立モジュール化し economy→engine.* 他を forbidden に追加+書き込み口の実行時テスト/ pre-commit フックの実行はコミット時に確認/ 第92の凍結スクリプト自体は tools/ に無い(規則は復元・再現済み)。
