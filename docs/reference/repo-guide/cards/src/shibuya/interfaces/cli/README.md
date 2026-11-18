# src/shibuya/interfaces/cli

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/interfaces/cli/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_pkgmove.py`

## [run_args.py](../../../../../../../../src/shibuya/interfaces/cli/run_args.py)

interfaces.cli.run_args — 割る段で ``engine/run.py`` を割った割り先(全ファイルの表 §4・名の表は``tools/pkgmove/map.toml`` の割る行)。

- 公開の関数とクラス
  - `add_calendar_args`(関数): 暦の口の引数(10a・A1-1・A1-2。``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。
  - `add_fleet_args`(関数): 実艦隊の共通引数(``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。
  - `calendar_kwargs_from_args`(関数): ``add_calendar_args``(10d の ``--sim-days``・``--resume-from``・``--state-out``・10e の ``--weather-perturb`` を含む)の
  - `fleet_from_args`(関数): ``add_fleet_args`` の結果 → ``FleetClient``(``--llm mock`` なら ``None``)。
  - `main`(関数): ``python -m shibuya.engine.run --agents 5000 --seed 1 --world data/world/v2``。
- import している内部モジュール: `shibuya.foundation.manifest.schema`・`shibuya.foundation.ports.inference`・`shibuya.foundation.types`・`shibuya.runtime.inference.fleet`・`shibuya.runtime.run`・`shibuya.runtime.state.growth_decl`・`shibuya.world.facts.calendar`・`shibuya.world.laws.presence`・`shibuya.world.laws.presence_plan`・`shibuya.world.model.assets`・`shibuya.world.model.geometry`・`shibuya.world.model.space.nav1`・`shibuya.world.model.state`
- 呼び手: `shibuya.cli`
- 読む試験: `tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_mock_day_w2.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_version_bump_10e.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- CLI の引数
  - `--ablate`: 止める過程(過程 id か AB-* の感度試験 id・複数可)
  - `--agents`
  - `--area-source`: 歩行可能面積の出所(C9c-1 G8 (b))。legacy=街路点×6.25 m²(既定・バイト不変)/ plateau=c9c_walkable_area.parquet(PLATEAU 歩道部+OSM×道路構造令の実測)
  - `--cells`: 合成世界のセル数
  - `--checkpoint-every`
  - `--day`: 曜日(0=月曜)
  - `--derive-rule`: 在圏ブロックの読み口(v2=§2 追補・v1=原則のまま)
  - `--endpoints`: カンマ区切り http://host:port(既定艦隊は 7 本=xxhash(call_id) mod 7)
  - `--environment-seed`: 10f 環境の seed(気象・大きな催し・道路工事。省略=--seed と同じ)
  - `--exit-mode`: 退出の実行形(immediate のみ実装・他は予約)
  - `--fleet-debug-dir`: 書式の原因分析用 jsonl の置き場(既定 off・診断のみ)。初回パースが落ちた呼の プロンプト/初回の生応答/再生成の生応答/実効・厳密の判定/理由 を 1 行 1 呼で書く
  - `--fleet-queue-capacity`: 艦隊の受理待ち+実行中の合計上限(既定 0=FleetConfig の既定 max_in_flight×4)。C7 本番(D-55/D-58): 計画呼数 2,709/tick に対し既定 1,792 だと 33.8%% が queue full で繰り延べ→テープに残らず再生不能。計画呼数以上(例 4096)にすると繰り延べ ≈0
  - `--fleet-wait-s`: ④′ で未応答が残るとき tick ごとに最大この秒数だけ艦隊を待つ(既定 0=純非ブロッキング・本番の運用は 120)
  - `--geometry`: 位置幾何(C9 G1/G2)。node=1 tick 1 ノード(既定・バイト不変)/edge=辺上の連続位置+希望速度 1.00〜1.60 m/s+Kladek 減速
  - `--group-norms`: 群・規範の計器(D-107 (a)・読むだけ)を回すか(第309 Q150・既定 on)
  - `--growth-yaml`: 状態成長宣言 YAML を出力して終了
  - `--holiday-csv`: 内閣府の祝日 CSV(cp932)。読めなければ開始日の検査で止める(既定 data/calendar/syukujitsu.csv)
  - `--llm`: LLM 経路(fleet=実 vLLM 艦隊・--endpoints 必須)
  - `--max-tokens`: T1 の max_tokens(既定 96=2 行形の最大 ≒70 tok に余裕・expedient)
  - `--mode`: 実行モード(cache_salt の勘定分離・record/replay とは別物)
  - `--model`: served-model-name(空なら /v1/models の先頭)
  - `--no-outside-suppression`: D-66 域外抑止を切る(=D-66 前の挙動・帰無腕)
  - `--no-plan-executor`: D-66 計画実行層(engine.presence)を切る(=現行挙動・帰無腕)
  - `--no-plan-sleep`: D-62「就寝は計画の実行」を切る(=D-62 前の挙動・帰無腕。就寝境界も LLM に判断させ・tick 0 は全員 SLEEPING)
  - `--no-population`: W16 母集団を使わず合成個体で回す(下限対照)
  - `--no-processes`: 世界過程(C4 第1陣)を止める(ablation の下限対照)
  - `--no-sleep-suppression`: D-56 就寝抑止を切る(=D-56 前の挙動・帰無腕)
  - `--population-seed`: 10f(K21 (a))母集団の seed(省略=--seed と同じ)。--seed は動きの seed(salt)
  - `--resume-from`: 再開する状態のファイル(10d・state-T<T>.npz)。設定は親と同じにする(違えば止める)
  - `--run-id`: manifest の run_id(cache_salt の第2要素)
  - `--school-holidays`: 学校の長期休みの区間 YYYY-MM-DD:YYYY-MM-DD をカンマ区切り(開始日の検査・既定は空)
  - `--seed`
  - `--sim-days`: 通しで回す日数(10d)。2 以上では各日の終わりに締め・日の頭の初期化は走らせない(既定 1)
  - `--start-date`: 開始日 YYYY-MM-DD(A1-1・manifest の start_sim_datetime)。空=2026-07-13(月)+ --day-index 日
  - `--state-out`: 状態の書き出し先のディレクトリ(10d)。各日の締めの後とランの最後に state-T<T>.npz を書く
  - `--tape`: 録画テープの出力先ディレクトリ
  - `--temperature`: T1 の温度(既定 0.7=知覚契約書 §2.5/卒業条件表・運用設計書 §1.3 の本番値。運用設計書 §1.2 の設定節は欄形だけで数値を持たない)
  - `--ticks`
  - `--weather-perturb`: 天気を揺らす(10e B6・アンサンブル)。窓の中でも同じ季節 × 平日/土休の層から天候型を日数の割合で引く(鍵は --environment-seed)。既定は付けない=その日の実際の天気
  - `--world`: 世界資産ディレクトリ(無ければ合成小世界へ落ちる)
- 決定の ID: D-55・D-56・D-58・D-62・D-66・D-107・第 309
