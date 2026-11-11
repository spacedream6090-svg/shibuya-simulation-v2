# src/shibuya/manifest

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [frozen](frozen/README.md)

## [__init__.py](../../../../../../../src/shibuya/manifest/__init__.py)

manifest: run manifest(U8・13節)の型・正規化・自己ハッシュ。誰にも依存しない・全員が読む。

- import している内部モジュール: `shibuya.manifest.canonical`・`shibuya.manifest.schema`
- 読む試験: `tests/test_manifest_roundtrip.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [canonical.py](../../../../../../../src/shibuya/manifest/canonical.py)

manifest.canonical: run manifest の正規化・自己ハッシュ(run_id)・YAML入出力。

- 公開の関数とクラス
  - `canonical_bytes`(関数): 正規化本文(run_id を除いた決定論的 JSON バイト列)を返す。
  - `compute_run_id`(関数): run_id = blake3(正規化本文) の16進文字列(64桁)。
  - `dump_yaml`(関数): ``normalized_yaml`` の内容を UTF-8 で書き出し、書いたパスを返す。
  - `load_yaml`(関数): YAML ファイルを読んで検証済み ``RunManifest`` を返す。
  - `normalized_yaml`(関数): 決定論的な YAML 文字列(キー昇順・UTF-8そのまま・ブロック形式)。
  - `verify_run_id`(関数): T1: 記録された run_id が正規化本文のハッシュと一致するか。
  - `with_run_id`(関数): ``identity.run_id`` を自己ハッシュで埋めた**新しい** manifest を返す。
- import している内部モジュール: `shibuya.manifest.schema`
- 呼び手: `shibuya.manifest`

## [schema.py](../../../../../../../src/shibuya/manifest/schema.py)

manifest.schema: U8 run manifest の型(13節)と機械化される規則。

- 公開の関数とクラス
  - `Arbiter`(クラス): 繰り延べアービタ(知覚契約書§6)。
  - `Budget`(クラス): 予算。``effective`` はラン時点のスナップショット(W1/L4/L6/M8/M11/P6…)。
  - `Code`(クラス): コード。``dirty=true`` は較正・holdout に使えない(CI拒否・規則(a))。
  - `Concurrency`(クラス): 並行意味論(U9)。二相コミット reserve→arbitrate→commit。
  - `Contracts`(クラス): 契約書2本(知覚・行動)。
  - `DataAsset`(クラス): データ資産1件。ライセンス台帳行と1対1(``license_row``)。
  - `Decoding`(クラス): デコード設定(T1=行動選択・T2=発話/静的言語化)。
  - `DecodingTier`(クラス): 1階層分のデコード設定。
  - `Diagnostics`(クラス): 診断行の列。T9=4列+保存則2検算(規則(e))。
  - `DocRef`(クラス): 文書参照(ODD・契約書)。manifest は本文でなくハッシュで参照する(§1.1)。
  - `Engine`(クラス): 推論エンジンの版(vLLM 系)。
  - `FidelityProfile`(クラス): 忠実度プロファイル。比較ランは同一プロファイル必須。
  - `Hardware`(クラス): ハードウェア。**サーバー名・IPは書かない**(規則(d))。
  - `HoldoutLayer`(クラス): 封印層1枚。``opened`` は mode≠holdout では false でなければならない(規則(b))。
  - `HoldoutSeal`(クラス): holdout封印。``seal_scheme`` = D(直接) / S(署名) / P(公開コミットメント)。
  - `Identity`(クラス): 同定。``run_id`` は manifest 正規化本文の自己ハッシュ(§1.1)。
  - `Lineage`(クラス): 系譜。``parent_run`` = resume 元の run_id。
  - `LlmApply`(クラス): LLM応答の適用(§2.4)。``overdue``=締切超過・``missing``=未着の扱い。
  - `LlmFleet`(クラス): LLM艦隊。既定 sha256(pickle) は版をまたいで非再現(vLLM公式)。
  - `Mode`(クラス): 実行モード(設計書§1.2 同定行・modeで勘定分離=L3)。
  - `Output`(クラス): 出力。接続情報(URL・IP)は書かない(規則(d))。
  - `Preregistration`(クラス): 事前登録。封印後の変更は新 run_id(HARKing防止)。
  - `PromptContract`(クラス): プロンプト契約(M11: 静的≤750・セル依存≤250・個体≤300)。
  - `Replica`(クラス): レプリカ1台(1 vLLM サーバプロセス)。
  - `Rng`(クラス): 乱数。個体/LLMシードは導出(別欄に持たない)=§2.5。
  - `Routing`(クラス): ルーティング。``cell_affinity`` は BN-4 で不採用=既定 false。
  - `RunManifest`(クラス): U8 run manifest(13節)。``identity.run_id`` は正規化本文の自己ハッシュ。
  - `Scheduler`(クラス): スケジューラの版(§2の規則の版)。
  - `Settings`(クラス): 設定。``normalized_blake3`` = 正規化済み設定本文のハッシュ。
  - `SourceRef`(クラス): 予算書の参照(パス+コミット+ハッシュ)。
- 呼び手: `shibuya.engine.run`・`shibuya.engine.scheduler`・`shibuya.llm.fleet`・`shibuya.manifest`・`shibuya.manifest.canonical`・`tools/c6/c6lib.py`
- 読む試験: `tests/c6/test_l4_l6_budget.py`・`tests/c6/test_t9_diagnostics.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_scheduler.py`・`tests/engine/test_tape_deferred.py`・`tests/llm/test_fleet.py`・`tests/llm/test_fleet_contract.py`・`tests/test_manifest_rules_extra.py`

## [world_catalog.py](../../../../../../../src/shibuya/manifest/world_catalog.py)

世界カタログ v0.2(世界被覆指標の**分母**)の実行時リーダ。

- 公開の関数とクラス
  - `WorldCatalog`(クラス): 凍結された世界カタログ。
  - `load_world_catalog`(関数): 同梱 JSON から凍結カタログを読む。
  - `verify_frozen`(関数): 凍結値との一致を検査する(分母が黙って動いていないことの門)。
- 呼び手: `shibuya.build.audit.w18_coverage`・`shibuya.world.processes.registry`
- 読む試験: `tests/build_audit/test_audit_pipeline.py`・`tests/build_audit/test_audit_units.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/test_world_catalog_sha.py`・`tests/world/processes/conftest.py`・`tests/world/processes/test_constitution.py`・`tests/world/processes/test_first_batch.py`・`tests/world/processes/test_registry.py`
