# src/shibuya/runtime/state

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/runtime/state/__init__.py)

(冒頭の説明なし)

## [class_ids.py](../../../../../../../../src/shibuya/runtime/state/class_ids.py)

engine.class_ids — クラスの名の固定の表(移す段 1・返事その 7 §4-2 の 3)。

- 公開の関数とクラス
  - `class_id`(関数): 型の凍結の名。表 → クラスの宣言(:data:`DECLARED_ATTR`)の順に引く。どちらにも無い ``shibuya`` の型は止める。
  - `class_path`(関数): 凍結の名 → 今の「モジュール.クラス名」(状態のファイルを読むときに import する先。表に無い名はそのまま)。
- 呼び手: `shibuya.runtime.state.codec`・`shibuya.runtime.state.hashes`・`shibuya.runtime.state.resume`・`shibuya.runtime.systems.probe`
- 読む試験: `tests/engine/state/test_class_ids.py`・`tests/engine/test_state_format_10f.py`

## [codec.py](../../../../../../../../src/shibuya/runtime/state/codec.py)

状態のファイルの直列化 npz+json(10f・K23 (a))。読むだけでコードが動く経路を持たない。

- 公開の関数とクラス
  - `Decoder`(クラス): (JSON の木, 配列の読み口) → 値の木。許可の表の外は ``StateFormatError``。
  - `Encoder`(クラス): 値の木 → (JSON にできる木, 配列の辞書)。
  - `StateFormatError`(クラス): 状態のファイルの中身が形式・許可の表・台帳の宣言に合わない(読まない)。
  - `allowed_class`(関数): 許可の表の名前 → クラス(表に無ければ ``StateFormatError``)。import するのは表に書いたモジュールだけ。
  - `declared_fields`(関数): 許可したクラス(``object`` の形)の欄の集合。dataclass は ``fields``・ほかは ``CLASS_FIELDS``。
  - `dumps`(関数): 値の木 → npz のバイト列(圧縮)。
  - `loads`(関数): npz のバイト列 → 値の木。``np.load(allow_pickle=False)`` と許可したクラスの表だけで組み立てる。
  - `qualname`(関数): 型の凍結の名(〔移す段 1〕``engine.class_ids`` の固定の表から引く)。
- import している内部モジュール: `shibuya.runtime.state.class_ids`
- 呼び手: `shibuya.runtime.state.resume`
- 読む試験: `tests/engine/state/test_class_ids.py`・`tests/engine/test_state_format_10f.py`

## [growth_decl.py](../../../../../../../../src/shibuya/runtime/state/growth_decl.py)

engine.growth_decl — エンジン側の**状態成長宣言**(D-R2-6 の YAML 5 欄・データ非依存の定数)。

- 公開の関数とクラス
  - `activity_declaration`(関数): **二層の段 2** の活動の文(``engine.activity.ActivityLayer``)の成長宣言。
  - `declarations`(関数): エンジン側 5 構造体の成長宣言(名前 → 宣言)。
  - `to_yaml`(関数): D-R2-6 の YAML 5 欄を文字列で返す(manifest / 検収パックへ貼る用)。
- import している内部モジュール: `shibuya.foundation.growth`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.run`・`shibuya.runtime.systems.report`
- 読む試験: `tests/engine/test_mock_day_w2.py`・`tests/engine/time/test_t0_time_consts.py`

## [hashes.py](../../../../../../../../src/shibuya/runtime/state/hashes.py)

behavior-hash と full-hash(10b・A2・A3)。表は ``engine.state_ledger`` だけから読む。

- 公開の関数とクラス
  - `behavior_hash`(関数): behavior-hash。
  - `component_digests`(関数): 列ごと(``置き場.列名``)と外の状態の道筋ごと(``行の鍵:道筋``)の digest(16 進 32 字)。読むだけ。
  - `external_digest`(関数): 外の状態の digest と、行ごとの直列化のバイト数(``items`` の既定=full に入る行)。
  - `full_hash`(関数): full-hash と、外の状態の行ごとのバイト数(``sizes``・記録用)。
  - `item_digest`(関数): 属性 1 本の digest(32 B)と直列化のバイト数(「無い」は印 1 B)。行の ``ordered`` の印を見る。
  - `resolve_item`(関数): ``"runner.salient.rng"`` → 値。途中の持ち主が ``None`` なら ``_ABSENT``。
  - `to_state`(関数): 値を決定論のバイト列にする(外の状態の直列化の書き手)。``ordered`` は辞書の挿入順を保つ。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.runtime.state.class_ids`・`shibuya.runtime.state.ledger`
- 呼び手: `shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.runtime.state.resume`・`shibuya.runtime.systems.probe`・`shibuya.runtime.systems.state_io`・`tools/bytecheck/check.py`
- 読む試験: `tests/engine/discard_probe.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/speech/test_speech_arm_rows_resume.py`・`tests/engine/state/shaped_names.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 決定の ID: 第 330

## [ledger.py](../../../../../../../../src/shibuya/runtime/state/ledger.py)

状態台帳の宣言(10b・A3「挙動」と「復元」の 2 軸・機械可読の 1 ファイル)。

- 公開の関数とクラス
  - `AstAllow`(クラス): AST の検査で「読み手」として数えても許す場所(``path`` と、その行に含まれる文字列で引く)。
  - `Excluded`(クラス): 台帳の行に入れない属性(``owner`` の ``attrs``・分類 ``kind``・理由)。
  - `LedgerRow`(クラス): 状態台帳の 1 行。
  - `arm_items`(関数): 〔第 1 期 1-8b〕腕の行のうち根の持ち主が居る(腕が立っている)行の ``(行の鍵, 属性の道筋)``(宣言順・``hash_skip`` を除く)。
  - `arm_rows`(関数): 〔第 1 期 1-8b〕腕の行(``LedgerRow.arm`` のある外の状態の行・宣言順)。
  - `behavior_columns`(関数)
  - `behavior_excluded`(関数): behavior-hash で ``state_hash(exclude=…)`` に渡す列名(軸 1 が ``no``/``diag`` の列)。
  - `behavior_items`(関数): behavior-hash に入れる外の状態の ``(行の鍵, 属性の道筋)``(軸 1 が behavior の行・``hash_skip`` を除く)。
  - `counts`(関数): 行の数(記録と試験が読む)。
  - `excluded_attrs`(関数): 持ち主 → 属性 → 除外の項。
  - `external_rows`(関数)
  - `full_excluded`(関数): full-hash で除く列名(軸 2 が ``discardable`` の列)。
  - `full_items`(関数): full-hash に入れる外の状態の ``(行の鍵, 属性の道筋)``(台帳の宣言順)。〔1-8b〕腕の行は入れない(``arm_items``)。
  - `item_attrs`(関数): 持ち主 → 台帳の行の ``items`` に載る属性(持ち主そのものが ``items`` に載る行は ``"*"``)。
  - `row`(関数)
  - `rows`(関数): 台帳の行(``place`` を渡せばその置き場だけ)。
  - `soa_rows`(関数)
- 呼び手: `shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.runtime.state.hashes`・`shibuya.runtime.state.ledger_ast`・`shibuya.runtime.state.resume`・`shibuya.runtime.systems.probe`・`shibuya.runtime.systems.state_io`・`tools/bytecheck/check.py`
- 読む試験: `tests/economy/cp2/test_cp2_writes_declared.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/discard_probe.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/speech/test_speech_arm_rows_resume.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/systems/test_systems_table.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/tools/test_repo_guide.py`
- 状態台帳の行
  - 持ち主を引けない行(道筋が `OWNER_CLASSES` に無い・道筋なし)
    - `O43` run_day の局所 pending(適用待ちの応答)(挙動 behavior・復元 required) 道筋 `run_day.pending` 書ける系: apply_responses・decide・drain・llm_receive
    - `O44` run_day の局所 fleet_deferred・fleet_waiting(挙動 behavior・復元 required) 道筋 `run_day.fleet_deferred`・`run_day.fleet_waiting` 書ける系: decide・drain・llm_receive・wake_filter
    - `O65` LLMBridge・TapeWriter・FleetBridge の計数・行・処理中の呼(挙動 no・復元 discardable) 書ける系: (宣言なし)
    - `O96` run_day の局所 replay_inbox(再生の到着待ち)(挙動 no・復元 required) 道筋 `run_day.replay_inbox` 書ける系: decide・drain・llm_receive
    - `P` TickScratch.percepts(知覚の事実 Percept・第 1 期 1-2)(挙動 no・復元 discardable) 書ける系: (宣言なし)
    - `PX0` TickScratch.near_index(近傍の索引 SpatialIndex・第 2 期 2-2 段 11a)(挙動 no・復元 discardable) 書ける系: (宣言なし)
- 決定の ID: 10-12/§4-4・10-12/§4-11・11-01・11-03・11-03/§3・第 330・第 346

## [ledger_ast.py](../../../../../../../../src/shibuya/runtime/state/ledger_ast.py)

追加 C の静的な検査: SoA の列ごとの読み手を AST で数え、状態台帳の軸 1 と食い違えば知らせる(10b)。

- 公開の関数とクラス
  - `DiagExit`(クラス): 診断の出口の関数(``qualname`` は ``クラス.メソッド`` か関数名。末尾の ``.*`` はそのクラスの全メソッド)。
  - `ExtAllow`(クラス): 外の状態の軸 1 の場所ごとの許可(属性の名前・当たる数・場所と理由・当たる行の関数の名前)。
  - `ExtScan`(クラス)
  - `ExtSite`(クラス): 持ち主の外の読みの場所(``func`` は ``クラス.メソッド`` か関数名・入れ子は ``.`` でつなぐ)。
  - `ScanResult`(クラス)
  - `Site`(クラス): 読みの場所(``path`` は ``src/shibuya`` からの相対・``text`` はその行の文字列)。
  - `check`(関数): 台帳の軸 1 と AST の読み手の食い違い(空なら合格)。
  - `check_external`(関数): 外の状態の軸 1 の検査(空なら合格)。場所ごとの許可は当たる数が宣言と同じであること(U5)。
  - `class_attrs`(関数): クラス ``cls`` の属性(メソッドの中の ``self.x = …``・``self.x += …``・``self.x[...] = …`` とクラスの欄)。
  - `class_defined_names`(関数): 属性の名前 → それを持つクラス(``path:Class``)。``self.x = …``(どのメソッドでも)・クラスの本体の代入と注釈・
  - `coverage`(関数): ``(持ち主 → 台帳にも除外にも無い属性, 食い違い)``。食い違い=除外と行の両方に載る・クラスに無い属性を載せた。
  - `declared_columns`(関数): ``declare("名前", ...)`` の列名(置き場 ``agents``・``cells``・``pois``・``perception`` → 宣言順)。
  - `ext_attr_rows`(関数): 外の状態の行が指す持ち主のクラスの属性の名前 → (持ち主, 行の鍵, 軸 1)。``run_day`` の局所の行は除く。
  - `ext_reason`(関数): 規則で許す理由の種類(``generic``・``exit``・``result``・``collision``)。``None`` なら規則では許さない。
  - `reader_counts`(関数): 台帳の SoA の行ごとの読み手の数(記録用)。
  - `runtime_uncovered`(関数): 実行時の網羅(検収 2-6): 各持ち主の**インスタンス**の ``vars()``(と ``__slots__``)を台帳+除外の一覧に
  - `scan`(関数): ``root``(= ``src/shibuya``)の下を走査する。``files``・``names`` を渡せばその範囲だけ(試験用)。
  - `scan_external`(関数): ``root``(= ``src/shibuya``)の下で、軸 1 が no/diag の外の状態の属性の「持ち主の外の読み」を集める。
  - `source_files`(関数): 走査の対象(``src/shibuya`` 全体・``build/`` を除く)。
- import している内部モジュール: `shibuya.runtime.state.ledger`
- 呼び手: `shibuya.runtime.systems.allow`
- 読む試験: `tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`
- 決定の ID: 第 304

## [resume.py](../../../../../../../../src/shibuya/runtime/state/resume.py)

日境界の再開と複数日の通しラン(10d・D-102 Q3・Q5・A10・A11)の状態の書き出しと読み込み。

- 公開の関数とクラス
  - `EnvironmentMismatchWarning`(クラス): 再開・再生の元(状態のファイル・テープ)を書いた環境の ``platform_id`` が今の環境と違う(10f・§8 の 6)。
  - `StateBundle`(クラス): 状態のまとまり 1 つ(見出し・SoA・外の状態・艦隊の未着の呼)。
  - `canonical_json`(関数): 正準の JSON(鍵を昇順・区切りを ``,`` ``:`` に固定・ASCII 以外もそのまま)。
  - `check_bundle`(関数): 読んだ中身を状態台帳の宣言と突き合わせる(壊れた値・取り違えた値で動き出さない)。
  - `check_item_kinds`(関数): 再開で戻す前に、保存の値と今の値の型を突き合わせる(10f・K23 (a))。違えば ``ValueError``。
  - `collect_items`(関数): 外の状態の値(台帳の ``full_items`` の道筋 → 値・宣言順)。持ち主が無い道筋は ``ABSENT_MARK``。
  - `collect_soa`(関数): SoA の列のうち軸 2 が ``discardable`` でない列の写し(置き場 → 列名 → 配列)。宣言順。
  - `declared_dtype`(関数): 台帳の SoA の行の型の略記(``i4``・``f4x2``・``u1x128``)→ (dtype, 2 次元目の長さ。1 次元なら ``None``)。
  - `environment_fields`(関数): 環境の欄(10f・K26 (a))。``platform``・``runtime`` はプロセスごとに 1 回だけ集める(``refresh=True`` で
  - `fingerprint`(関数): ``run_day`` の引数から設定の指紋を作る(再開で親と同じでなければ止める)。
  - `fingerprint_diff`(関数): 2 つの指紋で値の違う鍵(昇順)。
  - `path_identity`(関数): パス → 中身の同定(置き場所・書き方・OS に依らない)。ファイルは sha256、ディレクトリは
  - `platform_fields`(関数): 同じ環境かを見るための欄(決定論の方針: 同じ環境・同じ設定で同じ結果)。10f で ``environment_fields`` に広げた。
  - `read_state`(関数): 状態のまとまりを読む。npz+json だけ(外から来たファイルでもコードを動かさない)。
  - `run_id_of`(関数): ラン ID(実行ごとに一意・10d 検収 L6)。指紋・始めの T・親のラン ID に、実行の時刻とプロセス番号の印を混ぜる。
  - `state_path`(関数)
  - `warn_if_other_environment`(関数): 記録の環境の欄(``platform_id`` を持つ辞書)が今の環境と違えば警告を 1 行出す。返り値=警告したか。
  - `write_state`(関数): 状態のまとまりを 1 ファイル(npz+json・圧縮)に書く(一時ファイル → ``os.replace``)。返り値=ファイルのバイト数。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.paths`・`shibuya.runtime.state.class_ids`・`shibuya.runtime.state.codec`・`shibuya.runtime.state.hashes`・`shibuya.runtime.state.ledger`
- 呼び手: `shibuya.engine.resolve`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.state_io`
- 読む試験: `tests/economy/stage2/test_stage2_resume_arm.py`・`tests/economy/test_rules42_runs.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_arm_rows_resume.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_state_format_10f.py`・`tests/golden_env.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 環境変数: `NUMBA_NUM_THREADS`
- 決定の ID: D-102・第 330
