# A48(第347)天気の語の最頻値の補いを消した(weather-a48-347)

> 小さな版上げ。発注: [返事その 8](../../../design/prompt-2026-11-16-reply8.md) §3 の A48 の行・§8 の 5、壁打ちの記録 2-55
> (決定の正は原文)、親の裁定(計画 `plan_bumps` §1-3 の A48-1〜A48-6)、検収の直しの発注(検収 `review_a48`=高 0・中 1・低 8)。
> 作業の枝 `work/weather-a48-347`(親が本体の頭 `dcd25a6c` の上へ載せ直した)。実装役 Opus 5.5。byte-check・範囲の全体の試験・
> commit・タグ(`stable-v2-before-weather-a48`)・版上げの履歴への写しは親。`bytecheck/` の記録は親が置く(実装役は触らない)。

## 0. 要点

- **補いを消した。** 住民に見せる天気の語を作る口(`PerceptionAssets.weather`)は、W13 の時の表に `(日付, 時)` の行が無ければ、
  日付と時を書いて止める(`ValueError`=黙って埋めない)。365 日のその時の最頻値の表(`weather_by_hour`)は作らない。
- **本筋にそろえた。** 世界過程の無いラン(`processes=False`・`--no-processes` の下限対照)で実データの描画なら、天気の日を引いて
  B3 の語を出すだけの環境の過程を立てる(本筋と同じ規則・同じ環境の seed・日の頭に引き直す・manifest の `weather.days`・一番上の
  `replay_date`・`frozen_sources` の W13 の 2 表に残る)。体感温度は書かない(下限対照の「体は動かさない」は変えない)。
  注入の描画(アダプタでない)にも同じ口を挿す。
- **前もって止める。** 実データの描画は、組み立てで「引きうる再生日の全部(W13 の日の表)× 24 時」の行がそろうかを確かめ、
  日の頭でも引いた再生日を確かめる。**資産の片方だけはどちらの向きでも組み立てで止める**(描画に時の表があり環境の過程に日の表が
  無い/〔検収 中-1〕描画の資産が合成なのに世界が実データか環境の過程に日の表がある)。
- **合成の世界は宣言した。** 試験用の合成の世界は、A48 の前と同じ値の決まった天気を宣言として持ち、manifest の
  `weather.declared` に出す。宣言の表にその時が無ければ止める(宣言していない定数で埋めない)。体の側の体感(5 の固定)との
  1 段のずれは直していない(宣言の文に書いた)。
- **19 構成は 37 欄すべて同じの見込み**(§5)。直しの前の親の byte-check(基準 231d9fd)は 19 構成・37 欄すべて同じだった。

## 1. 裁定(計画 §1-3)と、検収の後の親の答え

| 細部 | 裁定 | したこと |
|---|---|---|
| A48-1 過程なしのランのそろえ方 | (a) 天気だけの環境の過程 | 組み立て(天気の結線の所)で `EnvironmentProcess` を立てる。過程の資産は計画実行層が読んだ物を使い回し、無ければ読む。影の面は渡さない(体感温度にしか使わない=影のファイルを開かない)。刻みの更新は呼ばない |
| A48-2 合成の天気の値 | (a) 今の表のまま | `PerceptionAssets.synthetic` の表(晴・日照は時から・やや暑い)を `declared_weather_by_hour` に置いた |
| A48-3 宣言の置き場 | (a) docstring の項を同じ位置で書き換え+manifest の欄 | 描画の docstring の見出し「expedient(本モジュール分)」の項(最頻値の項)を同じ位置で書き換え(項の数 8 のまま)。manifest の `weather.declared`(合成のランだけ)。台帳に行は足していない |
| A48-4 止める所 | (b) 日の頭+描画の口 | 日の頭(`state_io.relay_weather`)で引いた再生日の 24 時を確かめる。さらに組み立てで引きうる再生日の全部を確かめる(§2 の 4)。描画の口でも止める。**親の答え 1: この形でよい** |
| A48-5 旧道の腕 | 残さない | 腕は作っていない。旧値は安定版のタグ |
| A48-6 文字列を束ねるか | 束ねない | つなぎの台帳・世界の台帳の文・nav1 の宣言には触れていない |

過程なしのランでは、見せる暑さと体の体感の食い違いは前からあり、今回は直していない(体感は初期値のまま。B3 の暑さは前は
W13 の行、今は本筋と同じ規則の暑さ段)。

## 2. 変えた中身

| ファイル | 中身 |
|---|---|
| `src/shibuya/perception/renderer.py` | docstring の項を同じ位置で書き換え(§1)。`SYNTHETIC_WEATHER_NOTE`(宣言の文)。`PerceptionAssets` の欄 `weather_by_hour` → `declared_weather_by_hour`(合成の世界だけ・実データでは空)。`is_synthetic`・`weather`(行が無ければ合成は宣言の表・ほかは止める。〔検収 低-6〕宣言の表にその時が無ければ合成でも止める)・`missing_weather_hours`・`require_weather_days`・`declared_weather_manifest`。`load` は最頻値の表を作らない。`Renderer.weather_env`(参照だけ・既定 None) |
| `src/shibuya/runtime/systems/assemble.py` | 天気の結線の所: 描画の選び方(アダプタ/注入の描画)・天気だけの環境の過程・口を挿す(`state_io.wire_weather`)・組み立ての確かめ(両向きの片方だけ=〔検収 中-1〕)。〔検収 低-4〕頭の docstring の古い文(`_b3_words` は `state_io` へ移した)と、使われなくなった `from datetime import datetime` の 1 行 |
| `src/shibuya/runtime/systems/state_io.py` | `weather_source`・`relay_weather`(日の頭)・`wire_weather`(10d D1 と 10e B6 の結線の中身をそのまま 1 か所に)。`relay_tables` から `relay_weather` を呼ぶ |
| `src/shibuya/runtime/systems/table.py` | 日の頭の系の読みの宣言に `layers.renderer`(`relay_weather` が読む) |
| `src/shibuya/runtime/systems/report.py` | manifest の `weather` の源(世界過程の無いランは天気だけの環境の過程)と、合成の世界の `weather.declared`。〔検収 低-1〕世界過程の無いランの `frozen_sources` に、天気だけの環境の過程が読んだ W13 の 2 表(`process:w13_weather_days.parquet`・`process:w13_weather_hourly.parquet`)と、一番上の `replay_date`(最後の日の再生日=世界過程のあるランと同じ形) |
| `src/shibuya/runtime/state/ledger.py` | 除外の一覧に `renderer.weather_env`(参照・状態は資産・暦・日番号・環境の seed から作り直せる) |

1. 識別子に open/tick を新しく作っていない。新しいクラスは無い(止めるのは `ValueError`=クラスの名の固定の表を動かさない)。
2. 新しい文字列に道の形の部分(モジュールの道・ファイルの道)を入れていない(名の凍結の試験と、合成のランの manifest の道の形)。
3. manifest の節の表は直していない(`weather`・`frozen_sources`・`replay_date` はどれも設定の節で混ざった辞書でない)。
4. A48-4 の (b) の実現: 再生日は W13 の日の表の中からしか引かない(`environment.py` の `_pick_day_calendar`・`set_replay_date`)
   ので、組み立てで日の表の全部を確かめれば、どの日の頭でも止まらない。日の頭の確かめは、資産がランの途中で変わったとき
   だけ当たる。注入の描画で世界過程の無いランは、ランの日の暦の日付を組み立てで確かめる。
5. 段 7 で `perception/renderer.py` を割るときは、今回足した名(`SYNTHETIC_WEATHER_NOTE`・`PerceptionAssets.is_synthetic`・
   `missing_weather_hours`・`require_weather_days`・`declared_weather_manifest`・`Renderer.weather_env`)の割り先が要る
   (割る段の表 `package-map-final-2026-11-09-files.md` §4-23 に無い。定数と `PerceptionAssets` の 4 つは `PerceptionAssets` と同じ
   割り先=世界の側に置く。心の側に落とすと世界から心への import になる=検収 低-8)。

## 3. 止まる道(直した後)

| 走らせ方 | 前 | 後 |
|---|---|---|
| 実データ・世界過程あり(19 構成ほか) | 再生日の行(補い 0 回) | 同じ。組み立てで 365 日 × 24 時、日の頭で引いた日を確かめる(止まらない) |
| 実データ・世界過程なし・窓の中の日 | 暦の日付の行(日照と暑さも W13 の行) | 本筋と同じ規則で引いた再生日(窓の中=その日)。日照と暑さも本筋と同じ |
| 実データ・世界過程なし・窓の外の日(複数日で窓を越える日を含む) | 228/228 が最頻値 | 本筋と同じ層から引いた実日。止まらない |
| 部分的なデータ(描画に時の表・環境の過程に日の表が無い) | 暦の日付・窓の外は最頻値 | **組み立てで止まる**(「天気の資産の片方だけ: 描画に W13 の時の表があるのに、環境の過程の W13 の日の表が無い」) |
| 〔検収 中-1〕逆向き(描画の資産が合成=描画のファイルのどれかが無いか世界の道が無い・世界が実データか環境の過程に日の表がある) | 止まらず宣言の「晴」・宣言の文が「合成の世界」 | **組み立てで止まる**(「描画の資産が合成(わけ)なのに、世界が実データ・環境の過程に W13 の日の表がある(当たった方)。直し方: …」。〔再検収 低-A〕わけと直し方は当たった形ごと=注入の描画の資産が合成/世界が合成なので描画の資産も合成(ファイルの有無は見ない)/world_dir が無い/world_dir に無い描画のファイルの名。`counts/stop_paths.json` の文は低-A の前の文) |
| 注入の描画(アダプタでない・`weather_words_fn` を持つ)・世界過程あり | 口が挿さらず暦の日付 | 本筋の口が挿さる。過程に日の表が無ければ組み立てで止まる。**`weather.declared` は出ない**(report は アダプタの描画しか見ない) |
| 注入の描画・世界過程なし | 暦の日付・窓の外は最頻値 | 暦の日付で引く(**本筋にはそろわない=`weather_perturb` も使わない・manifest の `perturbed` は偽**)。ランの日の 24 時がそろわなければ組み立てで止まる |
| 注入の描画で `weather_date_fn` だけを持ち `weather_words_fn` を持たない物 | 暦の日付 | **選ばれず組み立ての確かめに入らない**(行が無ければ描画の口で止まる) |
| 合成の世界(世界過程あり・なし・描画も過程も合成) | 決まった表(宣言なし) | 同じ値を宣言(`weather.declared`) |
| スタブの描画 | B3 なし | 同じ(確かめない) |

注入の描画(アダプタでない)の呼び手は src と tools に無い(試験の偽物だけ)。

**置き場ごとの確かめ**(`stop_paths_a48.py` → `counts/stop_paths.json`=10 体・2 刻みのランを世界過程のあり・なしで回した。
段の途中の置き場は、天気の結線より前の移動の確かめ(切替口 ③a の後=nav1 の資産が無い本番の形の世界は止まる)に当たるので、
試験と同じ口 `nav1._LEGACY_FOR_TESTS` で旧のセルの移動にして回し直した):

| 置き場(`data/world/*/` の 20) | 描画のファイル | W13 の 2 表 | 世界過程あり | 世界過程なし |
|---|---|---|---|---|
| `v2`・`v2_stage_5-1` | あり | あり | 止まらない・宣言なし・再生日 2026-07-13 | 同じ |
| `v2_pre20260928`・`v2_pre_4-3`・`v2_stage_*`(2-3〜4-3 の 9)=11 | あり | あり | 止まらない(旧のセルの移動で)・宣言なし・再生日 2026-07-13(`v2_pre20260928` は窓の外=2026-08-31) | 同じ |
| `v2_10e_steps`・`v2_pre1c_20260928`・`v2_pre_2-4`・`v2_steps_*`(3)=6 | なし | なし | 止まらない(合成の世界・宣言あり) | 同じ |
| `v2_pre_10e_2026-10-12` | なし | **あり** | **止まる**(逆向きの片方だけ=環境の過程に日の表がある) | 止まらない(合成の世界・宣言あり) |

- `v2_pre_10e_2026-10-12` は 10e より前の W13 の退避(世界と描画のファイルが無い)。旧資産の切替口は第330 で消え、src と試験に
  これを世界の置き場として使う所は無い(`tests/engine/test_assets_10e_b0_b1.py` は消した旗が止まることだけを見る)。決定の
  「合成の世界だけが宣言の天気」に照らすと止まるのが正しい(§9 の問い)。検収の数えの「両方そろう 14・両方無い 6」は、この置き場を
  「両方そろう」に入れていた(描画のファイルは無い)。
- W13 の 2 表がそろう 14 置き場は、どれも日の表の全部の日に 24 時の行がそろう(`w13_days_hours.py` → `w13_days_hours.json`=
  欠けた日時 0)。

## 4. 試験

| 試験(`tests/perception/test_weather_a48.py` ほか) | 足した/直した | 何を確かめるか |
|---|---|---|
| `test_real_shaped_assets_stop_on_a_missing_row_and_the_synthetic_world_uses_the_declared_weather` | 足した ①(直しで 1 項足した) | 実データの形の資産は行が無ければ日付と時を書いて止まる。合成の世界は表に無い日付でも宣言の天気。〔低-6〕宣言の表にその時が無い合成の資産も止まる |
| `test_the_renderer_port_stops_too` | 足した ① | 描画の口(B3)でも行が無ければ止まる |
| `test_synthetic_runs_declare_the_fixed_weather_in_the_manifest[True/False]` | 足した ②(直しで比べ方を直した) | 合成のランは世界過程のあり・なしとも `weather.declared` に宣言。表は語で書き下した値と比べる(同じ関数どうしの比べをやめた=低-3)。過程なしは一番上の `replay_date` も空 |
| `test_a_run_without_processes_draws_the_same_replay_day_as_the_main_path` | 足した ③(`requires_data`・直しで足した) | 世界過程の無い実データのランが本筋と同じ再生日・層を引き、B3 の語が同じ。体感の更新 0 回・影を開かない。〔低-3〕実データのランは過程あり・なしとも宣言が出ない(負の対照)。〔低-1〕一番上の `replay_date` と `frozen_sources` の W13 の 2 表が過程ありのランと同じ |
| `test_a_run_without_processes_builds_the_weather_only_environment_without_data` | **足した**(data 不要=CI で回る・低-3/低-1) | 試験の中で作る資産(合成の形の描画の資産・W13 の 2 日分の過程の資産)で、世界過程の無い 2 日のランが天気だけの環境の過程を立て、日の頭に 2 日目を引き直し、B3 の語がその日の行から出る。日ごとの記録(影は空)・一番上の `replay_date`・`frozen_sources` の W13 の 2 表(W13 でない表は写さない)・宣言なし・体感の更新 0 回 |
| `test_a_run_without_processes_draws_from_the_stratum_like_the_main_path_without_data` | **足した**(再検収 低-B・data 不要) | W13 の 3 日分(夏の平日・天候型 3 つ)の過程の資産で、開始日を窓の外(2026-07-27)に置くと、世界過程の無いランの天気だけの環境の過程が層から引き(`how` が sampled・`sample_calendar_day` を環境の seed で呼んだ値と同じ)、世界過程のあるランと再生日・層・B3 の語が同じ。天候の語は引いた日の行 |
| `test_assets_on_one_side_only_stop_at_assembly[True/False]` | 足した ④ | 描画に時の表・過程に日の表が無いと組み立てで止まる(世界過程のあり・なし) |
| `test_the_reverse_one_side_stops_too` | **足した**(中-1・data 不要) | 描画の資産が合成で過程に日の表があると組み立てで止まり、文に「環境の過程に W13 の日の表がある」 |
| `test_a_real_world_with_synthetic_perception_assets_stops` | **足した**(中-1・data 不要) | 世界が実データ(世界の資産の出どころを実データの印に替えた合成の世界)なのに描画の資産が合成だと、世界過程の無いランでも組み立てで止まり、文に「世界が実データ」 |
| `test_an_injected_renderer_is_checked_at_assembly` | 足した ⑤ | 注入の描画も組み立ての確かめに入る(片方だけで止まる・暦の日付の 24 時で止まる/回る) |
| `test_an_injected_renderer_gets_the_main_path_hooks_in_a_run` | **足した**(低-3・data 不要) | 世界過程のあるランで注入の描画に本筋の口が実際に挿さる(天気の日=再生日・語=その日の行・鍵=(再生日, 暦の日付)) |
| `test_wire_weather_puts_the_main_path_hooks_on_any_renderer` | 足した ⑤ | `wire_weather` は描画に本筋と同じ口(日・語・鍵)を挿す |
| `test_wire_weather_puts_only_the_day_hook_when_the_environment_has_no_weather_days` | **足した**(低-3) | 環境の過程に日の表が無い(`has_weather` が偽)と日の口だけを挿し、語と鍵の口は挿さない |
| `test_relay_weather_picks_the_day_without_processes_and_checks_the_rows` | 足した ⑥ | 日の頭は世界過程の無いランだけ引き直し、引いた日の 24 時を確かめる |
| `tests/perception/test_renderer_golden.py::test_j2_real_assets_carry_names_noise_and_weather` | 直した | 「表に無い日付でも決定論的に落ちる」→「表に無い日付は止まる(日付と時が文に出る)・実データでは宣言の表は空」 |
| `tests/engine/test_resume_10d.py::test_b3_weather_follows_the_replay_date_of_each_day` | 注だけ直した | (確かめることは同じ)合成の世界で表に無い時は宣言の天気になる、と注に書いた |

## 5. 37 欄不変の見込み(計画 §1-4 の条件 (i)〜(iv))

byte-check(19 構成・37 欄)は親が回す。直しの前の親の byte-check(基準 231d9fd)は 19 構成・37 欄すべて同じだった。直しの後も
見込みが変わらない理由:

- **(i) docstring の見出しの項の数 8 を保つ**: 描画の見出しは前と同じ `…renderer.py#heading:1af925f4`・項 8 個(今回の直しで
  docstring の見出しの項は触っていない)。`tests/engine/bridging/test_bridging_ledger.py` は通った(§7)。
- **(ii) 台帳の行を足さない**: `docs/design/bridging-ledger.json` は変えていない。
- **(iii) 文字列を束ねない**: つなぎの台帳・世界の台帳の文・nav1 の宣言には触れていない。
- **(iv) 過程ありの道**: 19 構成は描画の資産も過程の資産も実データ=今回足した逆向きの確かめ(描画の資産が合成のときだけ)の枝に
  入らない。`report.py` の足した 2 つ(`frozen_sources` の W13 の 2 表・一番上の `replay_date`)は世界過程が無いときだけ
  (世界過程のあるランの枝は前のまま)。合成の宣言の表の補いをやめた所は、宣言の表が 24 時そろうので当たらない(19 構成は合成の
  資産を使わない)。`assemble.py` の import の 1 行と docstring はランに効かない。数え(§6)で `w6_v3_default` の final と呼数は前と同じ。
- そのほか動かさないもの: manifest の一番上の鍵(足していない)・設定の指紋(`run_day` の引数は変えていない)・`template_sha256`・
  クラスの名の固定の表(新しいクラスは無い)・名の凍結(`tests/engine/state/test_names_frozen.py` は合成のランの manifest を含めて
  通った)・manifest の節の表(`tests/engine/test_env_and_sections_10f.py` は通った)。

## 6. 数え直し(直した後)

台本 [count_weather_a48.py](count_weather_a48.py)(関数を包んで数えるだけ・ランは変えない)。結果は `counts/` の JSON(直しの前の
実装で数えた。今回の直しは過程ありの道の値を変えない=§5)。

| ラン | 天気の行を引いた回数(内訳) | 口 | 組み立ての確かめ | final・呼数・再生日 |
|---|---|---|---|---|
| `w6_v3_default`(5,000 体・1 日) | 280(実データの行 280・行が無い 0) | 環境の過程の口 60,939 | 1 回・365 日 | `c8d68704b7b0760d`・60,939(②a の byte-check の記録と同じ) |
| 世界過程なし・実データ・開始日 2026-09-14(窓の外・200 体) | 228(実データの行 228・行が無い 0)。前は 228 回すべて最頻値 | 環境の過程の口 1,754 | 1 回・365 日 | 再生日 2025-11-10(層から引いた=count-347 の世界過程ありの窓の外と同じ日)・影は開かない |
| 世界過程なし・実データ・既定の開始日 2026-07-13(200 体) | 228(実データの行 228) | 環境の過程の口 1,754 | 1 回・365 日 | 再生日 2026-07-13(その日の実際の天気) |
| 合成の世界・世界過程あり(200 体) | 228(宣言した天気 228) | 暦の日付 2,678 | 0 回(合成は確かめない) | `weather.declared` あり |

- 「引いた回数」は描画の天気のキャッシュの鍵(日付 × 5 分の帯)が外れた回数。世界過程の無い 2 本は final と呼数が同じ(mock は
  文を読まない・天気と開始日は体の値に効かない)。
- 前の数えの道具 `../count-347/weather-noise/count_run.py`(:57)と `../count-347/weather-noise/w13_rows.py`(:37)は、消した欄
  `weather_by_hour` を読むので、回し直すと止まる。記録の道具は直していない(346 の前例)。過去の文書で旧の挙動を書いた所
  (`../count-347/weather-noise.md`・`../wallbounce-1012/10e-build-side-prep.md`)も過去の記録のまま。

## 7. 回した試験(直しの後・載せ直した木で)

- 載せ直しの直後: `tests/perception/test_weather_a48.py` と `test_renderer_golden.py -k "weather or j2"`(1 本): 11 passed。
- 直しの後: `tests/perception/test_weather_a48.py`(1 本・`-n` なし): 15 passed・飛ばした 0。
- 直しの後: `pytest -p no:cacheprovider -q -n 4`(1 本)で 28 ファイル(前の 26 に `state/test_mind_world_reads.py`・
  `space/test_nav1_world.py` を足した)→ 結果は §7-1。
- `lint-imports`(木で)→ §7-1。カード: `python tools/repo_guide/build.py` → `--check`(`cards/data.md` は戻した)。
- 回していないもの: byte-check・範囲の全体の試験(親が回す)。

### 7-1 結果

- `pytest -p no:cacheprovider -q -n 4`(1 本・28 ファイル): `tests/perception/test_weather_a48.py`・`test_renderer_golden.py`・
  `test_b6_invite.py`・`facts/test_render_from_percept_bytes.py`・`facts/test_percept_schema.py`・`tests/engine/test_resume_10d.py`・
  `test_weather_calendar_10e.py`・`test_renderer_wiring.py`・`test_activation_10e.py`・`test_assets_10e_b0_b1.py`・
  `test_processes_run.py`・`test_t3_manifest.py`・`test_version_bump_10e.py`・`test_census_out.py`・`body/test_system1_placeholders.py`・
  `bridging/test_manifest_rules_bridges.py`・`bridging/test_bridging_ledger.py`・`test_state_ledger_10b.py`・
  `systems/test_systems_table.py`・`systems/test_fix_guards.py`・`systems/test_guard_runs.py`・`state/test_names_frozen.py`・
  `state/test_class_ids.py`・`state/test_mind_world_reads.py`・`test_env_and_sections_10f.py`・`multiday/test_md23_w9_window.py`・
  `space/test_nav1_world.py`・`tests/tools/test_bytecheck.py` → **675 passed・失敗 0・飛ばした 0**(data のある機械)。
- `lint-imports`(木で): 12 kept・0 broken。
- 置き場ごとの確かめのラン(§3)は pytest と同時には回していない。

## 8. 性能(親が測った・10-13b §0-7)

測り方は [s2e-1102 §6](../s2e-1102/README.md) と同じ(壁時計=ランの前後・刻みあたり=壁時計 ÷ 実行器の刻みの数 1,440・最大メモリ=
Windows の最大の作業集合・10^6 B を MB・判断モデルの呼数は 0=mock)。5,000 体・1 日・seed 1。1 本ずつ単独で、土台 → 後 の順に
回した(既定のランは 2 巡)。土台=この版上げの直前の commit の src。道具と出力は [perf/](perf/)。

| ラン | 版 | 壁時計[秒] 1 巡/2 巡 | 刻みあたり[ms] | 最大メモリ[MB] | 呼数(LLM) | final |
|---|---|---|---|---|---:|---|
| 既定(CLI の既定・世界過程あり) | 土台 | 51.6 / 48.8 | 35.8 / 33.9 | 515.9 / 533.7 | 60,939 | `c8d68704b7b0760d` |
| 既定(同じ) | 後 | 50.3 / 49.1 | 34.9 / 34.1 | 550.6 / 519.9 | 60,939 | `c8d68704b7b0760d` |
| 世界過程の無いラン(ライブラリの既定) | 土台 | 16.9 | 11.8 | 500.0 | 23,501 | `29e4139c65fa9610` |
| 世界過程の無いラン(同じ) | 後 | 17.1 | 11.9 | 518.4 | 23,501 | `29e4139c65fa9610` |

- 既定のランは、壁時計の差が −1.3〜+0.3 秒・最大メモリは巡ごとに上下(土台の 2 巡の間でも 18 MB 揺れた)=揺れの中。悪化は見えない。
- 世界過程の無いランは、天気だけの環境の過程を立てる分で +0.2 秒・+18 MB(1 巡だけ=揺れと分けられない)。final と呼数は前と同じ
  (開始日 2026-07-13 は W13 の窓の中なので、前も後も同じ実日の行を引く)。manifest は、後だけが一番上の `replay_date` と
  `weather.days` を書く(前は空)。

## 9. 版上げの履歴に書く 1 行の案(親が写す)と問い

```
| 小 | A48 天気の語の最頻値の補いを消した(住民に見せる天気の語は本筋と同じ「その日に引いた実日」から・W13 の行が欠けたら止める・資産の片方だけは両向きとも止める・世界過程の無いランも天気だけの環境の過程で本筋と同じ規則に・合成の世界は決まった天気を宣言)(#〇・第〇・返事その 8 §3・§8・記録 2-55)。既定の結果は不変=byte-check 19 構成 37 欄すべて同じ。性能の参考=w6_v3_default 5,000 体・seed 1・1 日・mock の壁時計 基準 〇 秒/後 〇 秒・呼数 60,939 で同じ | <commit> | `stable-v2-before-weather-a48`(<直前の commit>) | `git checkout stable-v2-before-weather-a48`(補いの旧値と、世界過程の無いランの暦の日付の天気の再現) |
```

親への問い(直しの後):

1. 置き場 `v2_pre_10e_2026-10-12`(10e より前の W13 の退避・世界と描画のファイルが無い)を世界の置き場に渡すと、世界過程のある
   ランは逆向きの片方だけで止まる(§3)。決定どおりと読んで止めたままにしたが、この置き場を世界として使う道が要るなら聞きたい。

## 10. 残した所(直さずに書くもの)

- **天気だけの環境の過程は状態のハッシュの外**(親の答え 2): 状態の台帳に行は足していない=世界過程の無いランの behavior と full の
  ハッシュを動かさない。再開では、資産・暦・日番号・環境の seed から作り直す(組み立てが 0 日目を引き、`relay_tables` が 1 日目から
  再開の日まで引き直す=世界過程の環境の過程の行 56 と同じ導き方)。検収役が、途中(2 日のランの 1 日目の途中)で止めて再開した
  ランの天気の日の記録・止めた後のテープの prompt_hash・final が通しと同じことを確かめた。ただし full のハッシュの検算はこの値を
  見ないので、作り直しが壊れても検算では捕まらない。
- **世界過程の無いランの `weather.days[].shadow_date` は空**(親の答え 3): 天気だけの環境の過程は影を開かない(世界過程のあるランは
  暦の日付の影)。影の警告も出ない。
- **注入の描画(アダプタでない)で世界過程の無いランは `weather_perturb` を使わない**(暦の日付で引く・§3 の表)。src と tools に
  呼び手が無い道。
- **注入の描画が合成の資産を持っていても `weather.declared` は出ない**(report はアダプタの描画しか見ない・§3 の表)。
- **過程なしの複数日と再開の `requires_data` の試験**は足していない(data 不要の 2 日の試験と、検収役の確かめで見た)。

## 11. 確かめていないこと

- byte-check(19 構成・37 欄)と範囲の全体の試験は回していない(親)。§6 で見たのは `w6_v3_default` の final と呼数だけ(直しの前の
  実装で)。
- 注入の描画(アダプタでない)を実データのランに渡した例(試験は偽物の描画と試験の中で作る資産で見た・検収役は実データで確かめた)。
- data の無い機械(CI)で試験のファイルが通るか(data のある機械で回した。data 不要の試験は data を読まない作りにした)。
- 性能(§8・親)。

## 12. 親の確かめ(第347)

- byte-check: 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・final が同じ 19(基準 `986773e`=この版上げの直前の src。既定
  `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。全体の壁時計 425 秒)。組は [bytecheck/](bytecheck/)。直しの前の実装
  (基準 `231d9fd`)と、検収の直しの後(基準 `dcd25a6`)でも回し、どちらも 19 構成すべて同じだった。
- 範囲の全体の試験(`tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`・linked の作業木): 6,884 passed・
  1 failed・21 skipped・1 xfailed(36 分 17 秒)。落ちた 1 本は前からの
  `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(linked の作業木でだけ落ちる)。
- 別の役の検収: 1 回目 条件つき(高 0・中 1=逆向きの資産の片方だけで止まらない・低 8)→ 直した → 2 回目 受入(高 0・中 0・低 3。
  低 2 件はその後に直した)。
- `tests/c7` は手元では回していない(CI で回る)。
- 性能は §8。例外(ignore)の本数は変わらない(割る段ではない)。`lint-imports` 12 kept。
