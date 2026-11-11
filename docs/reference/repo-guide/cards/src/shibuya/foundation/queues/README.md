# src/shibuya/foundation/queues

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/foundation/queues/__init__.py)

(冒頭の説明なし)

## [batching.py](../../../../../../../../src/shibuya/foundation/queues/batching.py)

engine.batching — 計算のまとめ(バッチ)の窓(第 3 期 3-2・時計の段 T1)。

- 公開の関数とクラス
  - `WindowQueue`(クラス): 計算のまとめの窓と事象の待ち行列(状態台帳の行 ``BW``・持ち主の名 ``batching``)。
  - `arm`(関数): いまの幅の腕[秒]\(既定 ``DEFAULT_WIDTH_S``)。進行役と組み立て(設定の指紋)が読む。
  - `config_keys`(関数): manifest の ``batching`` の設定の子の鍵(``engine.manifest_sections`` の表と試験が突き合わせる)。
  - `is_default`(関数): ``width_s``(省略=今の腕)が既定の幅か。
  - `manifest_fields`(関数): ``RunResult`` の manifest の ``batching``(進行役を通らない結果は ``None``)。
  - `observed_keys`(関数): manifest の ``batching`` の観測の子の鍵。
  - `parse_width`(関数): 幅の値(秒の整数・文字列も可)を検査して返す。``WIDTHS_S`` の外は ``ValueError``。
  - `set_arm`(関数): 幅の腕を選ぶ(CLI ``--batch-width-s``・試験の切替口)。ランの始めに読む(ランの途中で変えてもそのランは変わらない)。
- import している内部モジュール: `shibuya.foundation.queues.scheduler`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.layer`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.conductor`
- 読む試験: `tests/engine/batching/test_conductor_windows.py`・`tests/engine/batching/test_window_queue.py`・`tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/contact/_c1.py`・`tests/engine/contact/_c2.py`・`tests/engine/contact/test_c1_flow.py`
- 状態台帳の行
  - 持ち主 `batching`(`WindowQueue`)
    - `BW` WindowQueue(計算のまとめの窓の待ち行列と計器・第 3 期 3-2)(挙動 diag・復元 discardable) 道筋 `batching._bw_carry`・`batching._bw_head`・`batching._bw_meter`・`batching._bw_sched` 書ける系: calendar_3・contact・decide・llm_receive
- 環境変数: `SHIBUYA_BATCH_WIDTH_S`
- 決定の ID: 10-03/§7-5・10-12/§4-2

## [scheduler.py](../../../../../../../../src/shibuya/foundation/queues/scheduler.py)

engine.scheduler — 起床イベントの1分tickバケット配列+tick内秒オフセット順序+繰り延べ待ち行列。

- 公開の関数とクラス
  - `DeferralQueue`(クラス): 4クラス固定優先の繰り延べ待ち行列(知覚契約書 §6)。
  - `Scheduler`(クラス): 1分tick のバケット配列(リング)+遠未来 heapq の起床予約器。
  - `TickState`(クラス): 1 tick 分の起床イベント(純関数 ``scheduler`` の入力)。
  - `coalesce_agents`(関数): 順序を保ったまま同一個体の重複を1件に畳む(知覚契約書 §6 運用規定②「1呼に合流」)。
  - `order_indices`(関数): ``state.events`` を規約順に並べる**添字の置換**を返す(純関数)。
  - `ordered_events`(関数): 規約順に並べた ``(n, 4)`` イベント配列(純関数)。
  - `scheduler`(関数): 規約順に並べた **agent_id の配列**(int64)を返す純関数。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.manifest.schema`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`
- 呼び手: `shibuya.engine.arbiter`・`shibuya.engine.body.schedule`・`shibuya.engine.run`・`shibuya.engine.systems.observe`・`shibuya.foundation.queues.batching`
- 読む試験: `tests/engine/batching/test_window_queue.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/test_arbiter.py`・`tests/engine/test_mock_day_w2.py`・`tests/engine/test_scheduler.py`・`tests/engine/test_scheduler_p3.py`・`tests/engine/time/test_t0_time_consts.py`
- 読む試験(道筋で): `tests/engine/body/test_body_guard.py`
