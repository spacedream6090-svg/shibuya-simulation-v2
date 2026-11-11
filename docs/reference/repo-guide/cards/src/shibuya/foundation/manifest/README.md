# src/shibuya/foundation/manifest

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/foundation/manifest/__init__.py)

(冒頭の説明なし)

## [canonical.py](../../../../../../../../src/shibuya/foundation/manifest/canonical.py)

manifest.canonical: run manifest の正規化・自己ハッシュ(run_id)・YAML入出力。

- 公開の関数とクラス
  - `canonical_bytes`(関数): 正規化本文(run_id を除いた決定論的 JSON バイト列)を返す。
  - `compute_run_id`(関数): run_id = blake3(正規化本文) の16進文字列(64桁)。
  - `dump_yaml`(関数): ``normalized_yaml`` の内容を UTF-8 で書き出し、書いたパスを返す。
  - `load_yaml`(関数): YAML ファイルを読んで検証済み ``RunManifest`` を返す。
  - `normalized_yaml`(関数): 決定論的な YAML 文字列(キー昇順・UTF-8そのまま・ブロック形式)。
  - `verify_run_id`(関数): T1: 記録された run_id が正規化本文のハッシュと一致するか。
  - `with_run_id`(関数): ``identity.run_id`` を自己ハッシュで埋めた**新しい** manifest を返す。
- import している内部モジュール: `shibuya.foundation.manifest.schema`
- 読む試験: `tests/test_manifest_roundtrip.py`

## [schema.py](../../../../../../../../src/shibuya/foundation/manifest/schema.py)

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
- 呼び手: `shibuya.engine.run`・`shibuya.foundation.manifest.canonical`・`shibuya.foundation.queues.scheduler`・`shibuya.llm.fleet`・`tools/c6/c6lib.py`
- 読む試験: `tests/c6/test_l4_l6_budget.py`・`tests/c6/test_t9_diagnostics.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_scheduler.py`・`tests/engine/test_tape_deferred.py`・`tests/llm/test_fleet.py`・`tests/llm/test_fleet_contract.py`・`tests/test_manifest_roundtrip.py`・`tests/test_manifest_rules_extra.py`

## [sections.py](../../../../../../../../src/shibuya/foundation/manifest/sections.py)

ラン manifest(``RunResult.run_manifest_fields``)の欄を「設定」「観測」「環境」に分ける表(10f・K22 (a))。

- 公開の関数とクラス
  - `config_paths`(関数): 表の設定の節の道筋(昇順)。golden で固定する(10f 検収 N3 の 3)。
  - `leaf_paths`(関数): 入れ子の辞書の葉の道筋(辞書でない値・空の辞書が葉。list は 1 つの葉)。
  - `section_of`(関数): 道筋(``a.b.c``)の節。最も長く一致する表の道筋の節。どれにも当たらなければ ``None``。
  - `sections_table`(関数): manifest に置く表(``manifest_sections``)。
  - `split`(関数): manifest の一番上の欄を節ごとに分けた写し(入れ子の中は分けない=読み手の便利のため)。表に無い欄は ``unlisted``。
  - `unlisted_in_mixed`(関数): 混ざった辞書の下の葉のうち、表の道筋が混ざった辞書そのものにしか当たらないもの(=節の決まっていない鍵)。
- 呼び手: `shibuya.engine.run`・`shibuya.experiments.drive.branch`
- 読む試験: `tests/engine/batching/test_window_queue.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_manifest_events.py`・`tests/engine/experiment/test_cf33b_manifest.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/time/test_t0_tm9_fields.py`
- 決定の ID: 10-13b/§7・11-01・11-02r/§1・11-02r/§1 #7・11-03/§3・第 330
