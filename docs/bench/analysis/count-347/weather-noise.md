# 数える役 A(weather-noise): 天気の補い(A48)・騒音の段の切り替え(A49)・ランの記録(2-56)

- 発注: 返事その 8 §6-1 の 1・2・6(記録 2-55・2-58・2-56)。ランは変えていない。
- 木: linked の作業木・HEAD `38b0142f`(src は第346 段 4-9 の `1a1b5849` と同じ)。行の番号はこの木のもの。
- 数え方: `weather-noise/count_run.py` が 5 つの関数を包み(元の関数をそのまま呼んで、戻り値は変えない)、`shibuya.cli.run` を
  byte-check と同じ形で回す(19 構成・5,000 体・seed 1・1 日・mock・`PYTHONHASHSEED=0`・`SHIBUYA_` の変数なし)。1 本ずつ順に回した。
  包んだ関数: `PerceptionAssets.weather`・`Renderer._time_view`(`perception/renderer.py`)・`ChangeDetector.detect`
  (`engine/change_detect.py`)・`WorldProcessRunner.salient_wake_candidates`(`world/laws/runner.py`)・`Arbiter.step`(`engine/arbiter.py`)。
- 包みがランを変えていない確かめ: 19 構成すべてで final(16 桁)と呼数が byte-check の記録
  `docs/bench/analysis/move4-346/validation/bytecheck/all19_work.json` と一致した(`weather-noise/summary.json` の `final_matches_bytecheck`)。
- 出力: `weather-noise/runs/<構成>.json`(19 本)・`probes/*.json`(6 本)・`w13_rows.json`・`summary.json`(`summarize.py` が作る)。
  テープは木の外の作業場に出し、リポには入れていない。

## 1. A48 天気の最頻値の補い

補いの場所: `perception/renderer.py:673-681`(`PerceptionAssets.weather`。`(日付, 時)` の行が表に無いと `weather_by_hour` に落ちる)。
最頻値の表は `:856-859` で作る(365 日のその時の最頻値。同数なら文字列の大きい方)。合成の世界は同じ枝で
`:709-717` の決まった表(晴れ・日照は時から・暑さは段 1)に落ちる。これは 365 日の最頻値とは別のもの。

天気の語を引く口は 3 つある(`renderer.py:1599-1633`)。
- words_fn: 環境の過程の再生日で引く。`runtime/systems/assemble.py:1131-1149` で結線され、条件は「`runner` がある」かつ
  「`runner.replay_date` が空でない」かつ「`assets.has_weather`」。
- date_fn: 再生日で引く(`:1608-1621`)。`replay_date` が空でないのは W13 があるときだけ(`world/laws/environment.py:300-314`)なので、
  words_fn と必ず一緒に結線される。単独で使われる組み合わせは無い。
- 暦の日付: 上の口が結線されないとき(`:1622-1623`)。

### 1-1 byte-check の 19 構成(1 日のラン・実測)

| 構成 | 天気の語を引いた回数 | 補いに落ちた回数 | 口 | 再生日 |
|---|---|---|---|---|
| w6_v3_default ほか 19 構成すべて | 270〜287 | **0** | すべて words_fn | 2026-07-13(how=actual) |

構成ごとの回数は `summary.json` の `configs[].a48`。コードから見ても 19 構成で補いは通らない。どの構成も `processes` を渡していない
(`tools/bytecheck/configs.py:19-47`)ので、既定の `processes=True`(`engine/run.py:2055`)で `runner` が立つ(`assemble.py:806-835`)。
環境の過程は有効・無効の切り替えに関わらず必ず作られ(`world/laws/runner.py:238-243`)、再生日は W13 の日から選ばれる(`environment.py:303-312`)。
W13 には 365 日 × 24 時の行がすべてある(1-3)。

### 1-2 環境の過程が無い走らせ方ほか(小さなラン・200 体・1 日・`probe_paths.py`)

| 走らせ方 | 口 | 引いた回数 | 補いに落ちた回数 | 場所 |
|---|---|---|---|---|
| 世界の資産あり・`processes=False`(`--no-processes`・`engine/run.py:2619`)・既定の開始日 2026-07-13 | 暦の日付 | 228 | 0(暦の日付の行が W13 にある) | assemble.py:807 |
| 同上・開始日が W13 の窓の外(2026-09-14) | 暦の日付 | 228 | **228(全部が最頻値)** | 同上 |
| 世界の資産あり・過程あり・開始日が窓の外(2026-09-14) | words_fn | 230 | 0(再生日 2025-11-10 を引いた) | environment.py:306-308 |
| 世界の資産あり・過程あり・`--weather-perturb` | words_fn | 229 | 0(再生日 2026-07-30) | environment.py:303 |
| 合成の世界(`world_dir=None`)・過程あり | 暦の日付 | 228 | 228(合成の決まった表) | renderer.py:742-748・709-717 |
| 合成の世界・`processes=False` | 暦の日付 | 228 | 228(合成の決まった表) | 同上 |

「引いた回数」は描画の天気のキャッシュの鍵(日付 × 5 分の帯)が外れた回数で、1 日に約 228〜287 回。

コードを読んで挙げた、実測していない道:
- 複数日のランで `processes=False` のまま暦の日付が 2026-08-31 を越える日。2 行目と同じで、その日は全部が最頻値になる見込み。
- `run_day(renderer=<Renderer>)` で `PerceptionRendererAdapter` でないものを渡したとき(`assemble.py:944-951`)。`perception` が None になり
  口が結線されないので、暦の日付で引く。窓の外の日は最頻値。試験では `tests/engine/test_renderer_wiring.py:166-167,287` が Renderer を直に作る。
- `renderer="stub"`: 天気を引かない。
- 過程の資産に W13 の日の表(`w13_weather_days.parquet`)が無く、知覚の資産に時の表がある部分的なデータ。暦の日付で引き、窓の外は最頻値になる。
- 古い道: 天気の規則 legacy は第330 で消えており、残っていない(`environment.py:35-37`)。
- CI: data が無いので合成の世界。合成の決まった表に落ちる。
- 試験: `processes=False` で回す試験は約 30 本あり、ほとんどは合成の世界(`world_dir=None` か既定)。

### 1-3 W13 で「引いた日のその時の行」が欠けるか(`w13_rows.py`・ランと同じ読み口)

| 量 | 値 |
|---|---|
| 再生日の候補(`w13_weather_days`)の日数 | 365(2025-09-01〜2026-08-31) |
| 知覚の時の表の行 | 8,760(365 日 × 24) |
| 候補の日 × 0〜23 時のうち行が無いもの | **0** |
| 時の表にあって日の表に無い日 | 0 |
| 過程の側の WBGT の NaN | 0 |
| (参考)最頻値がその日その時の実際の値と違う数 | 3 つ組 4,499 / 8,760(語ごと: 天候 2,583・日照 639・暑さ 2,541) |

### 1-4 補いを消したとき標準のランが 1 バイト不変か

19 構成で通った回数が 0 なので、不変の見込みがある。描画の資産 `PerceptionAssets` の欄は状態のハッシュに入っていない。
状態の台帳(`runtime/state/ledger.py:554-560`・`657-666`)に入るのはレンダラのキャッシュと計数だけで、`renderer.assets` は無い。
manifest に入るのはファイルの sha256(`renderer.py:842-843`)だけで、表の中身は入らない。
ただし、「本筋にそろえる」直しで `processes=False` の道や合成の世界の表を変えれば、19 構成の外のランと試験の値は動く(1-2)。

## 2. A49 6 時と 22 時の騒音の段の切り替え

- 段の出どころ: `world/model/state.py:404-424`(`World.noise_stage_for_tick`。刻みから時を出す)→ `world/assets.py:313-322`(6〜22 時は昼の表、それ以外は夜の表)。
  描画は `runtime/systems/perceive.py:40` で同じ値を受け取る。`cells.noise_stage` を書く所は src に無いので、変わるのは 6 時と 22 時だけ
  (実測でも騒音の欄が変わった刻みは 360 と 1320 の 2 つだけ)。
- 静的な表(520 マス): 昼と夜で段が違うマスは **96**。夜の方が高いマスが 93、低いマスが 3。

### 2-1 「起こす理由」の記録のされ方(コード)

1. 検出: B4 の 4 欄(密度の段・騒音の段・流れ・顕著行為)のどれかが前の刻みと違うマスの全員を CELL_BLOCK(10)の候補にする
   (`engine/change_detect.py:299-313・428-436`)。どの欄が変わったかは候補に残らない。顕著行為の到達も同じ CELL_BLOCK になる(`runtime/systems/judge.py:270-277`・注 `:320-321`)。
2. 検出の後で落とすもの: 意図を持つ体と活動中の体(`perceive.py:82-90`)、歩いて乗る体(`judge.py:330-334`)。
3. 裁定: 域外 → 就寝 → 不応期の順に落とす(`arbiter.py:340-425`。変化検出の行は就寝の例外にならない=`judge.py:393`)。
   同じ体に条件が複数あれば 1 呼に合流し、代表 1 つだけを残す(`arbiter.py:441-456`。実効クラスの昇順で選ぶので、CELL は最後になる)。
4. 記録: manifest の `calls_by_condition` は代表の条件の日計(`runtime/systems/decide.py:213-215`・`report.py:381-383`)。
   テープの `calls.parquet` の `wake_class` は実効クラス(`decide.py:165,185`)で、条件の列は無い。
   - 記録だけからは数えられない。足りないのは 2 つ。どの欄の変化で候補になったか(マス × 刻み)と、合流で落ちた条件の一覧。
     合流で落ちた条件は件数 `merged_per_class` しか残らない。
   - 今回は包みで数えた。騒音の欄だけが変わったマスにいて、同じ刻みにほかの起床の行(内受容・計画境界・満了・会話・保留・顕著行為)が
     無く、呼ばれた体を「騒音だけ」とした。ほかの欄も一緒に変わったマスの体と、ほかの行もあった体は「重なり」とした。

### 2-2 標準のラン(w6_v3_default・5,000 体・1 日)

| | 6:00(刻み 360) | 22:00(刻み 1320) | 1 日 |
|---|---|---|---|
| 騒音の段が変わったマス(騒音だけ/ほかの欄とも) | 96(95/1) | 96(92/4) | |
| 段が上がったマス/下がったマス | 3/93 | 93/3 | |
| そのマスにいた体(cell ≥ 0) | 183 | 314(騒音だけのマス 312・ほかの欄とものマス 2) | 497 |
| 検出の後の抑止で落ちた(意図・活動中・歩いて乗る) | 26 | 202 | |
| 就寝で落ちた | 149 | 28 | |
| 不応期で落ちた | 0 | 3 | |
| 域外で落ちた・繰り延べ | 0・0 | 0・0 | |
| **呼ばれた(起こされた)** | **8** | **81** | **89** |
| うち **騒音の段の変化だけ** | **4** | **41** | **45** |
| うち ほかの理由と重なった | 4 | 40 | 44 |
| 重なりの相手(条件の番号: 件数) | 2: 2・3+11: 1・4: 1 | 5: 16・3: 8・3+11: 7・3+5: 5・11: 3・4: 1 | |

その日の CELL_BLOCK の呼は 4,921、全部の呼は 60,939。「騒音だけ」の 45 は CELL_BLOCK の呼の約 0.9%。
騒音だけで呼ばれた体の代表の条件はすべて CELL_BLOCK だった(6 時 4・22 時 41)。

### 2-3 19 構成(参考・同じ数え方)

| 構成 | 6 時: マスの体 | 6 時: 呼ばれた | 6 時: 騒音だけ | 22 時: マスの体 | 22 時: 呼ばれた | 22 時: 騒音だけ | 1 日: 呼ばれた | 1 日: 騒音だけ | CELL_BLOCK の呼 |
|---|---|---|---|---|---|---|---|---|---|
| w6_v3_default・v3_mem_store | 183 | 8 | 4 | 314 | 81 | 41 | 89 | 45 | 4,921 |
| v3_mem_rel | 183 | 8 | 4 | 319 | 72 | 36 | 80 | 40 | 5,041 |
| w6_v3_activity_off | 187 | 35 | 31 | 295 | 266 | 236 | 301 | 267 | 15,601 |
| w6_v1_default・v1_edge・v1_edge_plateau・old の 3 つ | 184 | 34 | 28 | 317 | 296 | 254 | 330 | 282 | 15,824 |
| w6_v1_derive_v2_1・old | 177 | 27 | 25 | 290 | 272 | 236 | 299 | 261 | 14,669 |
| w6_v2・v2_edge・old の 2 つ | 190 | 38 | 34 | 326 | 303 | 254 | 341 | 288 | 16,400 |
| w6_golden_null_arm | 688 | 72 | 52 | 434 | 280 | 220 | 352 | 272 | 31,575 |
| v3_classical | 191 | 4 | 1 | 270 | 18 | 5 | 22 | 6 | 8,012 |
| v3_classical_mem_rel | 191 | 4 | 1 | 280 | 18 | 4 | 22 | 5 | 8,523 |

騒音の段が変わったマスは、どの構成でも 6 時 96・22 時 96。活動の層が無い構成(v3_activity_off・v1・v2)では検出の後の抑止が効かないので、
22 時の数が大きい。

## 3. 2-56 ランの記録に引いた天気の実日が残っているか

| 記録 | 天気の実日 | 欄と形 | 場所 |
|---|---|---|---|
| manifest(`RunResult.run_manifest_fields()`) | **残る** | `weather.days[]` = 日ごとに `{day, calendar_date, replay_date, stratum(季節\|平日/土休\|天候型), how(actual/sampled/experiment), widened, shadow_date, shadow_fallback, sunrise_min, sunset_min}`。ほかに `weather.scheme`・`weather.perturbed`・`weather.warnings`・`weather.expedients`・`environment_seed`・`start_sim_datetime`・`calendar` | `environment.py:297-327・387-396`・`report.py:186-189`・`engine/run.py:1237-1242,1376,1381`。節は設定(`foundation/manifest/sections.py:59,65,68`)=`manifest_sha` に入る |
| manifest の一番上の `replay_date` | 最後の日だけ | 文字列 | `run_end.py:143` |
| manifest のファイル | `--checkpoints-out` のときだけ書く(`checkpoints_payload` の `manifest`) | | `cli.py:633,1766-1771` |
| テープの脇の `run_meta.json` | **残らない** | `weather_scheme` だけ | `assemble.py:665-672` |
| テープ `calls.parquet`・`blocks.parquet` | **残らない** | ブロックの文に天気の語はあるが、日付は無い | |
| byte-check の side の JSON | 残る | `weather`(manifest の写し・比べない欄。値は `manifest_sha` が見る) | `tools/bytecheck/check.py:325` |

- 天気を揺らすアンサンブルの口: `--weather-perturb`(`engine/run.py:2546`)と `environment_seed`。引いた結果は `weather.days[].replay_date`・`stratum`・
  `how="sampled"`・`widened` と `weather.perturbed=true` に残る。抽選の鍵は環境の seed と日番号(`environment.py:177-178`)。
  抽選の中間の値は残らないが、結果の日と層は残る。反実仮想の L0 で天気の日付を差し替えると、`how="experiment"` に書き換わる(`environment.py:348-350`)。
- 残らないもの:
  - 環境の過程が無いランは `weather.days=[]`(`report.py:186-189`)。実際に見せた天気(暦の日付の行か最頻値)は記録に無い。
  - 催し: 大きな催しの会場 3 マスは環境の seed で日ごとに引くが(`world/laws/civic.py:514-521`)、manifest に無い。
    `process_counters` の会場の数だけで、これは manifest に入らない。道路工事の辺(`world/laws/logistics.py:323-333`)も同じ。
  - 運行の乱れ: モデルに無い。第1陣は遅延を作らない(`world/laws/rail.py:839,923`)。記録するものも無い。
- 足すとしたらの見込み(未実装・未試験): 催しの会場と工事の辺を、`EnvironmentProcess.weather_days` と同じ形で各過程の `_plan` が日ごとに控える。
  `report.py` で manifest の新しい欄(または既存の欄の子)に出す。
  - 状態のハッシュ(behavior・full・final)と run_meta・テープのバイトは動かない見込み。乱数は今も引いていて、控えるだけのため。
  - `manifest_sha`・`manifest_fields_sha` は動く(欄が増える)。新しい一番上の欄なら `sections.PATHS` への追加が要る
    (`tests/engine/test_env_and_sections_10f.py` が全部の欄の節を確かめる)。
  - 環境の過程が無いランの天気の記録は、A48 の直しで本筋にそろえれば `weather.days` に入る。

## 確かめていないこと

- 2 日以上のラン・別の seed・別の体数(19 構成は 1 日・seed 1・5,000 体だけ)。
- 1-2 の実測していない道。複数日の `processes=False`・注入レンダラ・部分的なデータは、コードを読んだだけ。
- A49 の二次の影響。22 時に呼ばれた体は CELL_BLOCK の不応期に入るので、その後の密度の変化で起きる数が減る。この分は数えていない。
- A49 の「検出の後の抑止で落ちた」の内訳(意図の保持・活動中・歩いて乗るのどれか)は分けていない。
- 補いを消した版での 1 バイト一致は、見込みだけで byte-check していない。
- 催しの欄を足したときに `manifest_sha` 以外の比べる欄が動かないかは、見込みだけで試していない。
- センサスの時間帯別の表の有無は別の役が受け持つため、見ていない。
