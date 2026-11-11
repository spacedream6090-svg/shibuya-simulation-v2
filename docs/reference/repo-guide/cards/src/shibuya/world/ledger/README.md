# src/shibuya/world/ledger

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 10 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [frozen](frozen/README.md)

## [__init__.py](../../../../../../../../src/shibuya/world/ledger/__init__.py)

(冒頭の説明なし)

## [absent.py](../../../../../../../../src/shibuya/world/ledger/absent.py)

world.processes.absent — 「無いと宣言」する過程と判断の一覧(第340 段 2 の 6・回答 11-01 §2・§10-3)。

- 公開の関数とクラス
  - `by_id`(関数)
  - `by_routing_row`(関数): routing §1 の行の番号 → 宣言(「無い」の宣言=no_actor と no_port だけ)。
  - `by_world_process`(関数): ``world_process_id`` → 宣言(``kind`` が no_actor のものだけ=「無い」の過程)。
- import している内部モジュール: `shibuya.world.ledger.records`
- 呼び手: `shibuya.world.ledger.first_batch`・`shibuya.world.processes.circularity`・`tools/instruments/absent_declarations.py`
- 読む試験: `tests/bridging/test_drives_from_vs_scoring.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/world/processes/test_declarations_1101.py`
- 決定の ID: 11-01/§2・11-01/§3・11-01/§10-1・11-01/§10-2・11-01/§10-3・11-02r/§1・11-02r/§1 #7・第 340

## [actual_log.py](../../../../../../../../src/shibuya/world/ledger/actual_log.py)

world.processes.actual_log — **追記専用 ActualLog**(固定幅 numpy レコード+保持窓+増分索引)。

- 公開の関数とクラス
  - `ActualLog`(クラス): 追記専用の実績ログ(固定幅 numpy + 保持窓 + 増分索引)。
  - `ComplianceRate`(クラス): PlanSpec の「遵守率の観測欄」の実測値。
  - `plan_compliance`(関数): PlanSpec の遵守率(``realizes`` 関係で結ばれた世界過程の記録から計算)。
- import している内部モジュール: `shibuya.foundation.growth`・`shibuya.foundation.time_consts`・`shibuya.world.ledger.records`・`shibuya.world.ledger.relations`
- 呼び手: `shibuya.world.laws.runner`
- 読む試験: `tests/engine/events/test_e_log_links_actual.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/time/test_t0_time_consts.py`・`tests/world/processes/test_actual_log.py`
- 状態台帳の行
  - 持ち主 `runner.log`(`ActualLog`)
    - `O61` WorldProcessRunner log(ActualLog)(挙動 no・復元 discardable) 道筋 `runner.log` 書ける系: close_final・day_close・day_head・duties・world

## [constitution.py](../../../../../../../../src/shibuya/world/ledger/constitution.py)

world.processes.constitution — **憲法5 の機械検査**(D-R2-4・決定2026-09-07)。

- 公開の関数とクラス
  - `ConstitutionReport`(クラス): ``check_constitution5`` の報告(CI ゲート用)。
  - `DeletionCandidate`(クラス): 「宣言した届き先が消えた細部は、削除候補として台帳に自動的に載る」(§5 確定文)。
  - `LedgerIds`(クラス): パターン台帳から読んだ行 id の3分類。
  - `Violation`(クラス): 憲法5 検査の違反1件。
  - `check_constitution5`(関数): D-R2-4 のビルド時検査を台帳全体に適用する。
  - `check_declaration`(関数): 1件ぶんの (a)/(b) 検査。
  - `parse_pattern_ledger_ids`(関数): パターン台帳の表(先頭列見出しが ``ID`` または ``行``)から行 id を読む。
  - `parse_perception_channel_ids`(関数): 知覚契約書 §3 チャネル仕様表の**チャネル列**を出現順で返す。
- import している内部モジュール: `shibuya.foundation.paths`・`shibuya.world.ledger.records`
- 呼び手: `shibuya.world.ledger.first_batch`・`shibuya.world.ledger.registry`・`shibuya.world.processes.circularity`・`shibuya.world.processes.deletion_candidates`
- 読む試験: `tests/bridging/test_drives_from_vs_scoring.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/world/processes/test_constitution.py`・`tests/world/processes/test_deletion_candidates.py`・`tests/world/processes/test_first_batch.py`
- 環境変数: `SHIBUYA_PATTERN_LEDGER_MD`・`SHIBUYA_PERCEPTION_MD`・名前を読めない所 1 か所

## [first_batch.py](../../../../../../../../src/shibuya/world/ledger/first_batch.py)

world.processes.first_batch — **第1陣の宣言(データのみ・振る舞い無し)**。

- 公開の関数とクラス
  - `build_registry`(関数): 第1陣(+前倒し分)を積んだ ``WorldRegistry`` を作る。
  - `growth_declarations`(関数): 宣言済み世界過程の成長宣言(名前 → 宣言)。``core.growth.check_growth`` に渡す。
- import している内部モジュール: `shibuya.foundation.growth`・`shibuya.world.ledger.absent`・`shibuya.world.ledger.constitution`・`shibuya.world.ledger.inputs`・`shibuya.world.ledger.records`・`shibuya.world.ledger.registry`・`shibuya.world.ledger.relations`
- 呼び手: `shibuya.engine.bridging.scan`・`shibuya.world.laws.runner`
- 読む試験: `tests/bridging/test_drives_from_vs_scoring.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/processes/test_runner.py`・`tests/engine/test_processes_run.py`・`tests/world/processes/test_actual_log.py`・`tests/world/processes/test_declarations_1101.py`・`tests/world/processes/test_first_batch.py`
- 決定の ID: 第 340

## [inputs.py](../../../../../../../../src/shibuya/world/ledger/inputs.py)

world.processes.inputs — 入力の宣言の一覧(第340 段 2 の 7・回答 11-01 §1・§8)。

- 公開の関数とクラス
  - `by_id`(関数)
- import している内部モジュール: `shibuya.world.ledger.records`
- 呼び手: `shibuya.world.ledger.first_batch`・`tools/instruments/absent_declarations.py`
- 読む試験: `tests/world/processes/test_declarations_1101.py`
- 決定の ID: 10-12/§4-11・11-01・11-01/§1・11-01/§8・11-01/§10-1・第 340

## [records.py](../../../../../../../../src/shibuya/world/ledger/records.py)

world.processes.records — 世界側台帳の**レコード型3つ**(D-R2-2・決定2026-09-02)。

- 公開の関数とクラス
  - `Absence`(クラス): 無いと宣言する過程・判断(回答 11-01 §2・§10-3・routing §3)。
  - `ActualLogEntry`(クラス): §2 の ``ActualLog`` 1行(**追記専用・不変**)。
  - `AnnouncementScope`(クラス): 公示範囲(D-R2-4 の PlanSpec 必須欄)=「どの種別・セルの観測ブロックに載るか」。
  - `Clock`(クラス): §2 WorldProcess の「時計(物理=連続/制度=日次)」。
  - `DetailDeclaration`(クラス): 憲法5 確定文の「**全ての細部**・世界過程は…宣言できなければ実装しない」の細部側。
  - `DeviationVocab`(クラス): §2 ActualLog の逸脱語彙(GTFS-RT 式)。``DELAY`` は本モジュールの追加(expedient)。
  - `Executor`(クラス): ``realizes`` の属性 executor(§2)。「フォールバック」の正体はこの値の切り替え。
  - `InputDecl`(クラス): 入力の宣言(回答 11-01 §1 の型・A1-8 案 b)。境界の外から一方向に流れるもの。
  - `Modality`(クラス): 軸1 実行様態(§2 の表・第4値「物理アフォーダンス」は検証答申の追加)。
  - `NormKind`(クラス): 軸3 規範種別(§2・Searle / OperA / IG2.0 / SAI)。
  - `PlanSpec`(クラス): §2 の ``PlanSpec`` 行(旧「計画データ」の正式形)。
  - `ProcessKind`(クラス): §1 の3類 + フォールバック枠。**A は第1級**・B/C は §2 で「導出ラベルへ格下げ」。
  - `Validity`(クラス): 有効期間(valid time・§2 PlanSpec)。tick 単位。``valid_to=None`` = 無期限。
  - `Violability`(クラス): 軸4 違反可能性(§2・Grossi et al.)。
  - `WorldProcess`(クラス): §2 の ``WorldProcess`` 行。
- import している内部モジュール: `shibuya.foundation.growth`
- 呼び手: `shibuya.engine.duties.layer`・`shibuya.engine.experiment.branch`・`shibuya.world.laws.civic`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.logistics`・`shibuya.world.laws.opening`・`shibuya.world.laws.rail`・`shibuya.world.ledger.absent`・`shibuya.world.ledger.actual_log`・`shibuya.world.ledger.constitution`・`shibuya.world.ledger.first_batch`・`shibuya.world.ledger.inputs`・`shibuya.world.ledger.registry`・`shibuya.world.ledger.relations`・`shibuya.world.processes.circularity`
- 読む試験: `tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_log_links_actual.py`・`tests/world/processes/conftest.py`・`tests/world/processes/test_actual_log.py`・`tests/world/processes/test_constitution.py`・`tests/world/processes/test_declarations_1101.py`・`tests/world/processes/test_first_batch.py`・`tests/world/processes/test_records.py`・`tests/world/processes/test_registry.py`・`tests/world/processes/test_relations.py`
- 決定の ID: 11-01・11-01/§1・11-01/§2・第 340

## [registry.py](../../../../../../../../src/shibuya/world/ledger/registry.py)

world.processes.registry — 世界側台帳(**名前空間・ID体系は1つ**・D-R2-2)。

- 公開の関数とクラス
  - `CoverageReport`(クラス): executor 別の内訳と、世界カタログ(分母57)の被覆。
  - `WorldRegistry`(クラス): 世界過程・計画仕様・細部・関係を1つの名前空間で保持する台帳。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.world.ledger.constitution`・`shibuya.world.ledger.records`・`shibuya.world.ledger.relations`・`shibuya.world.ledger.world_catalog`
- 呼び手: `shibuya.engine.bridging.scan`・`shibuya.world.ledger.first_batch`
- 読む試験: `tests/world/processes/conftest.py`・`tests/world/processes/test_constitution.py`・`tests/world/processes/test_registry.py`

## [relations.py](../../../../../../../../src/shibuya/world/ledger/relations.py)

world.processes.relations — 世界側台帳の**関係(第1級)4本**(D-R2-2・§2)。

- 公開の関数とクラス
  - `CountsAs`(クラス): ``counts_as(物理的事実, 制度的事実, 文脈)`` — 構成的規則(Searle: X counts as Y in C)。
  - `FallbackRow`(クラス): conf宣言つきフォールバック台帳(§1 末尾)の1行。
  - `Realizes`(クラス): ``realizes(WorldProcess | AgentAction, PlanSpec)`` — **属性 executor が必須**。
  - `Records`(クラス): ``records(ActualLog, WorldProcess | AgentAction)``。
  - `RelationKind`(クラス): 関係4本の種別。
  - `Revises`(クラス): ``revises(Agent, PlanSpec)`` — 運転整理(指令)・値上げ(店主)・営業時間変更。
  - `SubjectType`(クラス): ``realizes`` / ``records`` の主体側(§2「WorldProcess | AgentAction」)。
  - `fallback_ledger`(関数): §1「conf宣言つきフォールバック台帳 = executor=engine_rule 行の一覧そのもの」。
  - `relation_key`(関数): 決定論ソート用の鍵(``to_json`` の並びを固定する)。
- import している内部モジュール: `shibuya.world.ledger.records`
- 呼び手: `shibuya.world.ledger.actual_log`・`shibuya.world.ledger.first_batch`・`shibuya.world.ledger.registry`
- 読む試験: `tests/engine/bridging/test_bridging_ledger.py`・`tests/world/processes/test_first_batch.py`・`tests/world/processes/test_registry.py`・`tests/world/processes/test_relations.py`

## [world_catalog.py](../../../../../../../../src/shibuya/world/ledger/world_catalog.py)

世界カタログ v0.2(世界被覆指標の**分母**)の実行時リーダ。

- 公開の関数とクラス
  - `WorldCatalog`(クラス): 凍結された世界カタログ。
  - `load_world_catalog`(関数): 同梱 JSON から凍結カタログを読む。
  - `verify_frozen`(関数): 凍結値との一致を検査する(分母が黙って動いていないことの門)。
- 呼び手: `shibuya.build.audit.w18_coverage`・`shibuya.world.ledger.registry`
- 読む試験: `tests/build_audit/test_audit_pipeline.py`・`tests/build_audit/test_audit_units.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/test_world_catalog_sha.py`・`tests/world/processes/conftest.py`・`tests/world/processes/test_constitution.py`・`tests/world/processes/test_first_batch.py`・`tests/world/processes/test_registry.py`
