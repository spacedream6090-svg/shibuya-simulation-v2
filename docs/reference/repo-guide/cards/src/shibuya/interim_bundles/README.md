# src/shibuya/interim_bundles

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [calendar2](calendar2/README.md)・[calendar3](calendar3/README.md)・[contact](contact/README.md)・[duties](duties/README.md)

## [__init__.py](../../../../../../../src/shibuya/interim_bundles/__init__.py)

(冒頭の説明なし)

## [calendar_self.py](../../../../../../../src/shibuya/interim_bundles/calendar_self.py)

engine.calendar_self — カレンダー 1b「勤務の出入りを本人へ」(第 6 期 6-2・腕 ``--calendar 1b``)。

- 公開の関数とクラス
  - `CalendarSelf`(クラス): カレンダー 1b の層(状態台帳の腕の行 ``C1B``・``C1BM``・腕 ``--calendar 1b`` のランだけ)。
  - `CommuteClassicalPort`(クラス): 仮のモデル(古典=見積りの幅の真ん中を使う)。ほかは mock と同じ規則(判断モデルまでのつなぎ)。
  - `CommuteMockPort`(クラス): 仮のモデル(mock・判断モデルまでのつなぎ=CA5 問い 2「モックはそのまま寄り」)。
  - `Estimate`(クラス): 見積りの幅[分]\(``lo``〜``hi``)。
  - `Observation`(クラス): 今の観測(本人が見たもの)。``time_min``=本人が読んだその日の時刻[分]\(おおよそなら丸めた値)。
  - `Prediction`(クラス): 本人が知っている予想(約束の時刻と場所の言葉・見積りの幅・余裕・時計を見る間隔)。時刻はその日の分。
  - `arm`(関数): いまの腕(``w17``=既定・``1b``=出入りを本人へ)。組み立てのときに読む。
  - `build`(関数): 組み立ての口: 腕 1b のランの層を作り、0 日目を張り、計画実行層に口を挿す(腕 w17 は ``None``)。
  - `commute_candidates`(関数): 出入りの候補(J0 の候補の形・番号は口が振る)。行き=出発する/まだ出ない/よく考える・帰り=帰る/まだ残る/よく考える。
  - `duration_words`(関数): 本人に渡す長さの言葉(``ROUND_MIN`` 分に丸める・最小は「5 分ほど」)。
  - `felt_minutes`(関数): 経過時間の実感[分]\(R-111 §1 の形): 待ちは 1.9+0.72×実際(出典の範囲 3〜15 分の中だけ=外は比 1)・待ち以外は比 1
  - `first_entering_train`(関数): 検査の口(実装の ``CalendarSelf.first_train`` と別に鉄道の表を直に引く): 路線 ``line`` で ``ready_T`` 以降に最初に
  - `hop_walk_steps`(関数): 節の数 → 歩く刻み(〔第 5 期 空間の段 1・検収 M5〕)。``hop_steps`` が None なら 1 刻み 1 節(legacy の見積り=B8)・
  - `is_on`(関数)
  - `manifest_fields`(関数): manifest の末尾に足す欄(腕 1b のランだけ ``{"calendar_1b": …}``・既定は空=manifest は今のまま)。
  - `observe_time`(関数): 本人が読む時刻(TM8): 時計やスマホを見れば分単位・見なければ ``APPROX_ROUND_MIN`` 分に丸めた「ごろ」。
  - `route_steps`(関数): 歩行グラフ(W3 の next-hop)で src → dst の節の数(着かなければ −1)。体はベクトル・ループは道のりの節の数ぶん。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--calendar``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
  - `update_estimate`(関数): 直近の実感の値の平均で見積りを作り直す(記憶の仕組みまでのつなぎ)。幅=直近の最小と最大(2 回より少なければ最初の幅)。
  - `validate_commitments`(関数): 1 人の約束の列を確かめる(CA4 (d))。返り値=(壊れた行の印, 重なりの組の一覧)。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.hashing`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.agent_codes`・`shibuya.foundation.vocab.events`・`shibuya.mind.judge.decision.sources`・`shibuya.society.calendar_shadow`・`shibuya.society.tools.registry`・`shibuya.world.facts.w20_calendar_reader`・`shibuya.world.laws.presence`・`shibuya.world.laws.presence_plan`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.interim_bundles.calendar2.layer`・`shibuya.interim_bundles.calendar3.layer`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/space/test_nav1_units.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`
- 状態台帳の行
  - 持ち主 `calendar_self`(`CalendarSelf`)
    - `C1B` CalendarSelf.cal_store(本人の予定の器=その日の約束・置き場所・見積り・機会・行き来の時刻・第 6 期 6-2)(挙動 behavior・復元 required・腕 calendar) 道筋 `calendar_self.cal_store` 書ける系: close_final・day_close・day_head・presence・world
    - `C1BM` CalendarSelf.cal_meter(判断の記録と計器=日ごとの記録・エンジンがしないこと 3 つの検査・第 6 期 6-2)(挙動 diag・復元 required・腕 calendar) 道筋 `calendar_self.cal_meter` 書ける系: day_head・presence
- 環境変数: `SHIBUYA_CALENDAR`
- 決定の ID: 10-12/§1-3・10-12/§2-1・10-12/§4-1・10-13b/§0-3・11-01・R-111・R-111 §1-1 #1・R-111 §1-2 #1・第 340
