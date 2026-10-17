# 第 6 期 6-3 時計の段 T2・T3・T4 の記録(会話の時計・何かあった体だけ・場所ごとの時計)

- 実装役 Opus 5.5。作業木の枝 `6-3/tm-t2-t4`(作った時の土台 `4f186fb`=6-5 記憶の腕の後 → 検収の後に本体 `32fb262` へ早送り=§13)。commit は親。§0〜§12 の数は直しの前の値で、直しの後に変わったもの・回し直したものは §13。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-2(TM1 時計の 3 つ・TM2 考えた時間・TM3 会話・TM4 既定の幅と指標・TM5・TM6 の T2〜T4・TM7・TM9・TM10)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) の 6-3 の行と回答 2-1(第 6 期のコードは GPU の前に腕で)・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(仮採用)・[3-2 の記録](../tm32/README.md)・[3-5 の記録](../bd35/README.md)・答申 [R-111](../../../../research/v2-r111-time-perception-decision-time-speech-rate.md) §3 C4・§2 B8・[R-73](../../../../research/v2-r73-time-model-des.md) §4-2・§6・§7・[時間のモデルの草案](../../../../design/v2-time-model-design-round-draft.md)(TM3〜TM5・TM10 の材料)。
- 数は実測(Windows 11・論理 CPU 20・並行して別の作業木のランが動いていた)。生の出力(テープ・side の JSON・道具)は作業木の `_bc/`(git の外)。本書には比べた結果だけを置く。絶対パス・ホスト名は書かない。

## 0. 結論

- **3 つの腕を作った(既定は今のまま)**。T2 会話の時計 `--talk-clock {table,mora}`(既定 table)・T3 何かあった体だけ `--step-scope {all,changed}`(既定 all)・T4 場所ごとの時計 `--clock {global,regional,mixed}`(既定 global・mixed は口だけ)。環境変数は `SHIBUYA_TALK_CLOCK`・`SHIBUYA_STEP_SCOPE`・`SHIBUYA_CLOCK`。
- **byte-check(10e の道具・19 構成・5,000 体・1 日・テープつき)**: 既定・腕 changed・腕 regional・腕 mora のどれも **19/19 構成で 25 欄とも HEAD(`4f186fb` の写し)と同じ**。3 つの腕を全部立てたランも 19/19 で final が HEAD と同じ(§6)。2 日のラン(final `b346bb6e3ecc60af`・138,946 呼)と、日の境目・2 日目の途中からの再開も、どの腕でも通しと同じ(テープの中身の sha も同じ)。〔検収 M6〕この 19 構成は直しの前のsrc の値。直しの後に本体 `32fb262` の写しと回し直した値は §13-3(既定・changed・regional は 19 構成・mora は 4 構成)。
- **T2**: 発言の長さ = モーラ数 × 人ごとのモーラの長さ × 発言ごとの揺れ × 相手の項。値は R-111 §3 と R-73 §4-2 の錨(平均 0.151 秒=6.62 モーラ/秒・話者 18 人の範囲 0.124〜0.198 秒・揺れ CV 0.42・親しい相手 +8.3〜10.9%・間 7 ms)。考える時間は足さない(TM2 の側)。会話ごとの時計の発言を窓の待ち行列の事象(種類 talk)として時刻順に処理し、同じ会話を同じ束に入れたら止め(負の対照)、違う会話は同じ束にする。会話の番は今も刻みに 1 回=時計は会話の中の時刻を数える計器(世界は変えない)。5,000 体 1 日(既定 v1): 会話 117・発言 384・**会話の長さは会話の時計で平均 3.0 秒、今の表(1 番=刻み 1 つ)で平均 246 秒**・人ごとの速さ 平均 6.64 モーラ/秒(5.14〜8.05)。
- **T3**: 体の反映は TM5 の予約(3-5 の reserve)、検出器の内受容の段の跨ぎは変化の印の体だけ(`ChangeDetector.detect(scope=)`)。**19/19 構成で 25 欄とも既定と同じ**(一致しない構成は無かった=腕を守る環境変数は要らなかった)。処理した体の割合(内受容の判定)は 2.4〜4.5%、体の反映(体の刻み)は 2.7〜6.9%。**刻みあたりの時間は速くならない**(5,000 体でも 39 万体でも=写しの比べと写しの更新が残る・§4-3)。腕の意味は「何かあった体だけ」の形の確認(版上げの前の器)。
- **T4**: セルの重心の 500 m の格子=29 区域+舞台の外。区域ごとに窓を進め、区域をまたぐ事象(発言を別の区域で聞く・処理し終えた区域への予約)は窓の終わりに届ける。**19/19 構成で 25 欄とも既定と同じ**。〔検収 M4〕ただしこの一致は**構造上の一致**: 区域の時計は今は計器だけで世界を書かない(区域の事象は会話の時計の発言だけ・系は全員の配列を 1 回で処理する)=区域ごとの処理の正しさの試験ではない。意味のある一致の確認は T2 の版上げ(会話の番を窓の中で回す)と C1(メッセージ・電話)の後(つなぎの台帳 `DOC-tm234-t4-structural-identity`)。TM6 の「T4 は一致が条件」の受入は条件つき(構造上)。メッセージの遅れの計器(聞く人の区域またぎ)は幅 W と同じだけ遅れる(W=60 → 60 秒・W=10 → 10 秒・W=1 → 1 秒)=TM4 の目標「10 秒以下」は W ≤ 10 で満たす(§5-3)。遅刻の計器を入れ(既定 v3 で予定の到着 6,388 のうち 283 が遅い)、TM4 の道具の遅刻と待ち合わせの列を埋めた(待ち合わせは約束の仕組みが無い=欄だけ)。
- TM9: manifest と日次の記録の `clock_kind` は腕 regional のランだけ `regional`(既定は今の `steps`)。TM10 の表は §8。

## 1. 作ったもの・変えたもの

| 項 | ファイル | 中身 |
|---|---|---|
| T2 会話の時計 | `src/shibuya/engine/speech_clock.py`(新規) | 腕(`arm`・`set_arm`・`is_default`・`make`)・錨の表 `ANCHORS` と導いた値(`SIGMA_BETWEEN`・`SIGMA_WITHIN`・`FAMILIAR_DELTA`・`GAP_NS`)・`language_of`・`person_mora_len_s`・`utterance_jitter`・`SpeechTiming`(話す)・`ChatTiming`(打つ=C1 の口・値は空欄)・`QueueRouter`(全体の窓の待ち行列に置く口)・持ち主 `TalkClock`(`on_turn`・`on_dispatch`・`on_close`・計器)・manifest の `talk_clock` |
| T3 何かあった体だけ | `src/shibuya/engine/step_scope.py`(新規) | 腕・持ち主 `StepScope`(`marks`=変化の印・`detect`・`after_detection`・計器)・manifest の `step_scope` |
| T3 の口 | `src/shibuya/engine/change_detect.py` | `ChangeDetector.detect(…, scope=None)`(None=今の道)・`_interoception_scoped`(同じ判定を印の体だけに) |
| T4 場所ごとの時計 | `src/shibuya/engine/regional_clock.py`(新規) | 腕(mixed は口だけ=止める)・`region_of_cells`・`clock_kind`・持ち主 `RegionalClock`(`schedule`・`now_ns`・`window_end_ns`・`hear_delay_ns`・`run_windows`=境目の移動・遅刻・区域の事象)・manifest の `clock` |
| 窓の待ち行列の読み口 | `src/shibuya/engine/batching.py` | `WindowQueue.now_ns`(処理中の時刻か次の窓の頭=予約の下限・読むだけ) |
| 結線 | `engine/systems/{build,conductor,llm_io,talk,perceive,run_end,state_io,boxes,table}.py`・`engine/run.py`・`engine/manifest_sections.py`・`engine/state_ledger.py`・`engine/state_ledger_ast.py`・`engine/rng_audit.py`・`cli.py` | §11 |
| 道具 | `tools/instruments/batch_width_gauge.py` | 指標 `lateness`=`clock.late_arrivals`・`meeting`=`clock.meeting`(欄だけ)・子プロセスが manifest の `clock` を拾い、`message_delay_max_s` に区域またぎの聞こえの遅れを含める |
| つなぎの台帳 | `docs/design/bridging-ledger.json` | 文書の行 14(§9-3)・3-2 の 4 行の why に注(status は不変) |
| 試験 | `tests/engine/clock/`(新規 3 本)・凍結の表 5 本 | §10 |

## 2. 口の表

| 腕 | CLI / 環境変数 | 既定 | 持ち主(`Layers` の名) | 設定の指紋 | manifest の節 | 状態台帳の腕の行 | ランの種類 |
|---|---|---|---|---|---|---|---|
| T2 会話の時計 | `--talk-clock {table,mora}` / `SHIBUYA_TALK_CLOCK` | table(持ち主なし) | `talk_clock`=`TalkClock`(組み立てが作る) | mora のときだけ `talk_clock: "mora"` | `talk_clock`(腕のランだけ) | `TCR`・`TCC`(腕 talk-clock) | arm |
| T3 何かあった体だけ | `--step-scope {all,changed}` / `SHIBUYA_STEP_SCOPE` | all(持ち主なし) | `step_scope`=`StepScope`(組み立て)・体の層は reserve で作る | changed のときだけ `step_scope: "changed"` | `step_scope`(腕のランだけ) | `T3M`(腕 step-scope) | arm |
| T4 場所ごとの時計 | `--clock {global,regional,mixed}` / `SHIBUYA_CLOCK` | global(持ち主なし) | `clock`=`RegionalClock`(進行役が窓のループの前に作る) | regional のときだけ `clock: "regional"` | `clock`(腕のランだけ)・`clock_kind=regional` | `T4W`(腕 clock-regional) | arm |

- 事象の種類: 会話の時計の発言=種類 1 `talk`(順位 1=同じ時刻では刻みの事象 0 の後・届け方 in_window)。腕 regional のときは全体の待ち行列に置かず、区域ごとの時計に置く。
- 試験の差の測り(段 B): 窓の境目 `WINDOW_MARK` は行 `BW:`・`TCC:`・`T4W:` の鍵だけを通す(`conductor.WINDOW_MARK_KEYS`)。系の宣言: decide と llm_receive に `TCR:talk_clock.*`・`TCC:talk_clock.*`、conversation に `TCC:talk_clock.*`、detect に `T3M:step_scope.*`。読みの宣言に `layers.talk_clock`・`layers.step_scope`・`layers.clock`(close_final は 3 つ・day_close は clock)。腕を立てたランの段 B は宣言の外の書き 0(試験)。
- C1(チャットの会話の状態)が刺す口: `speech_clock.MODALITIES=("対面","チャット")`・`ChatTiming.typing_ns`・`read_gap_ns`(空欄=None)・`TalkClock.on_turn(…, modality=…)`(チャットは `chat_blank` に数えて時計に載せない)。

## 3. T2 会話の時計

### 3-1. 値の出どころ(写し検査の形)

| 量 | コードの名 | 値 | 原典(答申の場所) |
|---|---|---|---|
| 日本語の日常会話のモーラの長さの平均 | `MORA_LEN_MEAN_S` | 0.151 秒(=6.62 モーラ/秒) | 石本 2024 表 1(CEJC・研究協力者 18 人・途中に間のある発話を除く)。R-111 §3-1・§3-2 の表・#38 ○/R-73 §4-2 #32 ◎ |
| 最速の話者 | `MORA_LEN_FAST_S` | 0.124 秒(8.06 モーラ/秒) | 同(65〜69 歳男性)。R-111 §3-1 |
| 最遅の話者 | `MORA_LEN_SLOW_S` | 0.198 秒(5.05 モーラ/秒) | 同(50〜54 歳女性)。R-111 §3-1 |
| 話者の数 | `N_SPEAKERS` | 18 | R-111 §3-1 |
| 話者の中の揺れ(句ごと) | `WITHIN_CV` | CV 0.42(句の長さの項なし) | Quené 2005 表 1(オランダ語 58 人・20,886 句)。R-111 §3-1・§3-2・#42 ○ |
| 同(句の長さで説明した後) | `WITHIN_CV_PHRASE` | 0.28(記録だけ・未使用) | 同 |
| 親しい相手に速い割合 | `FAMILIAR_FASTER` | 英語 +10.9%(214/193 語/分)・中国語 +8.3%(247/228 字/分) | Yuan ほか 2006 表 2。R-111 §3-1・#44 ○(日本語は z 値だけ=空欄・§3-4) |
| 応答の開始の間(日本語) | `GAP_MEAN_MS`・`GAP_MEDIAN_MS` | 平均 +7 ms・中央値 0 ms | Stivers ほか 2009。R-73 §4-2 #30 ◎ |
| 範囲 → SD の換算 | `D2_N18` | 3.640(正規の標本 18 の範囲の期待値=管理図の係数 d2) | 仮採用(試験で 4 万回の模擬 3.639 を確かめた) |

導いた値(式はコードの docstring と同じ・試験が再計算する):

| 値 | 式 | 結果 |
|---|---|---|
| 人ごとのモーラの長さの対数の幅 `SIGMA_BETWEEN` | ln(0.198/0.124) ÷ 3.640 | 0.12857 |
| 発言ごとの揺れの対数の幅 `SIGMA_WITHIN` | √ln(1+0.42²) | 0.40306 |
| 知らない相手の倍率 −1 `FAMILIAR_DELTA` | (0.109+0.083)/2 | 0.096 |
| 間 `GAP_NS` | 7 ms | 7,000,000 ns |

- 〔検収 L1〕中心 ln 0.151 は中央値で、範囲 [0.124, 0.198] を非対称に切る(下 −1.53σ・上 +2.11σ)。母集団の平均のモーラの長さは 0.15357 秒(錨の 0.151 より 1.7% 長い)・話す速さの母集団の平均は 6.586 モーラ/秒・切らない分布の 8.0% を範囲の外として切る(18 人の範囲を母集団の上下限にする扱い)。切り方は直していない(記録と台帳の行 `DOC-tm234-rate-distribution` に書いた=平均を 0.151 に合わせる形にするかは主張の前の感度試験で)。R-73 §4-2 は話者を「18 人前後」と書く(R-111 §3-1 は 18 人)=d2 の n が ±1 人で σ が約 1.4% 動く。

### 3-2. 時計の規則と試験

| 規則 | 中身 | 試験(`tests/engine/clock/test_tm2_talk_clock.py`) |
|---|---|---|
| モーラ数 | 本文から `engine.speech.port.mora_count`(1-8b の読みの規則=仮名 1 字 1 拍・拗音と小書きは 0・促音と撥音と長音は 1・漢字 1 字 2 拍)。仮名も漢字も無い本文(英語など)=欄だけ(長さは今の表=刻み 1 つ・`lang_other`)。本文の無い番(空・「なし」)は発言にしない(`silent`) | 本当の数と規則の出力が合う例 9 本(こんにちは 5・きょう 2・がっこう 4・コーヒー 4・東京 4・それじゃ、また。 5 ほか)・〔検収 L3〕漢字 2 拍の近似が外れる例 4 本を規則の出力と本当の数に分けて固定(混んでいるな 7/6・今日 4/2・一緒に行こう 9/7・渋谷駅 6/5)・言語の判定 |
| 人ごとの速さ | 対数正規(中心 ln 0.151)を [0.124, 0.198] 秒で切った形・乱数は母集団の seed と体の番号(Philox・一様 1 語の逆関数・状態を持たない) | 2 万体で全部が 5.05〜8.06 モーラ/秒・平均 6.45〜6.85・同じ鍵で同じ値・seed で変わる・d2(18) の模擬 |
| 発言ごとの揺れ | 平均 1 の対数正規・CV 0.42・鍵=話し手・作った時刻[ns]・会話の番号(TM7 (d)) | 3 万回で平均 1.00±0.01・CV 0.42±0.02・時刻と会話で値が変わる |
| 相手の項 | 関係の層で話し手から相手へ生きている辺(A ≥ τ)=親しい(倍率 1)・無ければ知らない相手(× 1.096)・関係の層の無いランは欄だけ(倍率 1・`familiar_unknown`) | 倍率・関係の層の口(`acquaintances`)を読む |
| 間と考える時間 | 次の発言の始まり=前の発言の終わり+7 ms。考える時間(TM2=今の表 L4 0.2 秒)は足さない | 差がちょうど 7 ms・`llm_bridge` を import しない(AST)・〔検収 L2〕**負の対照**=間に L4(0.2 秒)を足す欠陥を植えると間の検査が落ちる |
| 時刻順・持ち越し | 最初の発言は作った時刻に始まる。発言の事象は「始まり」と「今処理している時刻」の遅い方に置く=始まりが今より前=持ち越し(`carried`・`lag_ns`) | 窓の待ち行列で次の番を処理の中で作る形(版上げの形): 2 本の会話 × 6 発言が時刻順・同じ会話は前の発言の後・幅 60 秒と 1 秒で同じ順/会話の番が刻みに 1 回(今の形)=2 番目からは持ち越し・会話の時計は 3 発言で数秒 |
| 1 つの会話の中はまとめない | 〔検収 M3〕(1) 会話の番を作るとき、同じ会話の前の番と同じ時刻に作った番を止める(=1 回の LLM に同じ会話の番を 2 つ書かせない・会話の遅れ=持ち越しの有無によらない)(2) 同じ会話の発言が同じ束(同じ時刻・同じ種類の続き)に入ったら止める。どちらも `RuntimeError` | **負の対照**: 同じ会話の番を 1 回で 2 つ作る(=1 回の LLM に会話をまとめて書かせる形)と止まる |
| 違う会話どうしはバッチ | 同じ時刻の違う会話の発言は 1 つの束(`batch_max`) | 3 本の会話の最初の発言=1 つの束(体の番号の順) |
| 上限(安全装置) | 1 つの会話が 1 つの窓で処理する発言 2^10(当たったら次の窓の頭へ・`cap_hits`・止めない) | 上限 3 で当たって数え、全部いつかは処理される |
| C1 の口 | `ChatTiming`(打つ時間・読む間=空欄)・チャットの発言は `chat_blank` | 形・空欄・知らない道具は `ValueError` |

### 3-3. 会話の長さの分布(既定の表 vs 会話の時計・5,000 体・seed 1・1 日)

腕 mora は世界を変えないので、同じランの中で「今の表」(会話の番 1 つ=刻み 1 つ=60 秒・行動契約書 §3 の 1 呼=1 発話ブロック)と「会話の時計」(発言の長さ+間の和=最初の発言の始まりから最後の発言の終わり)を並べて数えた。会話の世界の上の長さ(開いた刻みから閉じた刻み)も並べる。語彙 v3 は既定ではひと言が無い(会話の番は全部 silent)ので、v3 は発話の口(`--speech-port on`=ひと言が戻る=世界は変わる)を立てて測った。mock の本文は v1 が 4 種(5〜7 モーラ)・v3+発話の口が「こんにちは」(5 モーラ)。

| 構成 | 会話 | 発言 | 会話の番(セッションの外=招待への返事) | 発言の長さ 平均[秒](最大) | 話す速さ(人ごと) 平均 [最小, 最大] | **会話の時計 平均[秒]** | **今の表 平均[秒]** | 世界の上の長さ 平均[秒] | 持ち越し |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|
| `w6_v1_default`(v1) | 117 | 384 | 2,045(1,565) | 0.887(3.41) | 6.64 [5.14, 8.05](203 人) | **3.01** | **246.2** | 267.7 | 270 |
| `w6_v3_default`+発話の口 | 175 | 698 | 2,905(2,207) | 0.760(2.25) | 6.56 [5.08, 8.02](316 人) | **3.07** | **239.3** | 261.3 | 524 |
| `v3_mem_rel`+発話の口 | 195 | 742 | 3,117(2,375) | 0.760(2.61) | 6.60 [5.09, 8.06](358 人) | **2.91** | **226.8** | 248.9 | 547 |

区切りごとの数(`w6_v1_default`・区切りは左閉じ):

| 会話の長さ[秒] | 0〜1 | 1〜2 | 2〜5 | 5〜10 | 10〜20 | 20〜60 | 60〜120 | 120〜300 | 300〜 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 会話の時計 | 17 | 17 | 72 | 11 | 0 | 0 | 0 | 0 | 0 |
| 今の表(会話の番 × 60 秒) | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 56 | 51 |
| 世界の上の長さ | 0 | 0 | 0 | 0 | 0 | 0 | 10 | 41 | 66 |

- 発言の長さ(v1): 0〜0.25 秒 1・0.25〜0.5 秒 62・0.5〜1 秒 199・1〜1.5 秒 89・1.5〜2 秒 27・2〜3 秒 3・3〜4 秒 3。人ごとの速さ(v1・203 人): 5.0〜5.5 が 7・5.5〜6 が 32・6〜6.5 が 50・6.5〜7 が 51・7〜7.5 が 35・7.5〜8 が 26・8〜9 が 2。
- 会話の時計の 0〜1 秒の 17 本のうち 3 本は発言の無い会話(`conv_silent`=全部の番が「なし」)。
- 相手の項: 関係の層のある `v3_mem_rel` では 742 発言が全部「親しい」(会話の相手は生きている辺のある相手だった=C10 8b の誘い方)。知らない相手の倍率はこれらの構成では効いていない。関係の層の無い構成は欄だけ。
- 会話の番の 7 割強はセッションの外(返事待ちの招待への返事)=会話の時計に入れていない(仮採用 6)。
- 差の読み: 会話の時計は「8 往復の会話にシミュ内で 16 分かかる」(指示書 10-03 §7-6)の向きを数で示す(今の表の 1/80 前後)。会話の番を窓の中で続けて回す版上げをすると、会話は 1 つの窓の中で終わる。

### 3-4. 世界との関係

- 会話の番(LLM の呼び出し)は今も刻みに 1 回(系 decide・llm_receive)。会話の時計は発言の時刻を数え、窓の待ち行列で時刻順に処理するが、処理は計器だけ=世界の状態・テープ・final は変えない(19/19 構成)。会話の番を窓の中で時刻順に続けて回す(違う会話どうしを 1 回の LLM にまとめ、同じ会話の次の番は前の番が返ってから)のは T2 の版上げ(GPU の後・つなぎの台帳 `DOC-tm234-talk-clock-meter-only`)。試験は版上げの形(発言の事象の処理の中で次の番を作る)で、時刻順・持ち越し・束の規則を確かめた(`on_turn(made_ns=…)` の口)。
- 発話の口(1-8b)の発言の時刻(`Utterance.t_ns`)は今のまま(刻みの頭)。会話の時計の時刻と結ぶのは版上げで。

## 4. T3 何かあった体だけ

### 4-1. 絞る処理・絞らない処理

| 処理(時間のモデルの草案 TM5 の「全員に毎回かけている 4 つ」) | 腕 changed | 体の数の走査 |
|---|---|---|
| 反映(体の自然な変化=空腹・疲れ・体感温度) | **絞る**: TM5 の予約(3-5 の reserve=予約の境目の体と入力の変わった体だけを規則に通す) | 予約の列+入力の写しの比べ 7 本(3-5 のまま) |
| 変化の検出(内受容の段の跨ぎ) | **絞る**: 変化の印の体だけ(`ChangeDetector.detect(scope=)`) | 印=写しの比べ 6 本(内受容の値 3 つと段 3 つ)+前に跨いだ体 |
| 変化の検出(セルの描画欄の変化の起床) | 絞らない(変化したセルの事象から体を numba の 1 本で拾う) | 1 本 |
| スケジューラ(計画の境目)・活動の満了・顕著行為・知人の出現 | 前から事象の数ぶんの配列(日の表の区間・候補の配列) | なし |
| 知覚の前計算 | セルごと(体の数に比例しない) | なし |
| 計器(空腹の語の段の時間の延べ・observe) | 絞らない(全員の和) | 2〜3 本 |

- 変化の印: 前の検出の後に内受容の値か段が変わった体 ∪ 前の検出で段を跨いだ体(段は 1 回に 1 段=値が 2 段ぶん動いた体は次の検出でもう 1 段跨ぐ)。最初の検出(組み立ての後・再開の後)は写しが無い=全員。印は「判定の結果が変わりうる体」の上界(値も段も前と同じで前に跨いでいない体は、判定の入力が前と同じ=前と同じく跨がない)。
- 事象(到着・退出・会話・購入・予約の境目・知らせ・判断の予定)と印: 内受容の値を動かすもの(食事・休み・就寝・移動の消費・体感温度)は値の変化として印に現れる。書き手が resolve の 11 の関数に散っていて 1 つの知らせの口が無いので、印は写しとの比べで付ける(3-5 の `BR-BODY-RESERVE-DETECT` と同じ形・つなぎの台帳 `DOC-tm234-t3-mark-by-copy`=驚き駆動の版上げで書き手の知らせの口に替える)。
- 試験: 印の体だけの判定=全員の判定(乱数の状態 3 通り・印=全員/跨ぐ体+500 体/跨ぐ体だけ)・**負の対照**(跨ぐ体を 1 つ抜くと違う・前に跨いだ体を印に残さないと 40 回の検出で全員を見る版と食い違う)・印の中身(値と段を変えた体+跨いだ体だけ)。

### 4-2. 一致の表(19 構成)と処理した体の割合

byte-check(19 構成・25 欄)は §6。下の表は 3 つの腕を全部立てたランの計器(final は 19/19 で HEAD と同じ)。内受容の判定の割合=印の体の延べ ÷(5,000 × 1,440)・体の反映の割合=規則に通した体の延べ ÷ 7,200,000(3-5 と同じ値)・体感温度=規則に通した体の延べ ÷(5,000 × 288 窓)。

| 構成 | final(HEAD=all=changed) | 内受容の判定 | 1 刻みの印の平均 | 跨いだ体の延べ | 体の反映 | 体感温度 | (T4)境目の移動 | (T4)遅い到着/予定 | (T4)区域またぎの聞こえ/聞こえ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `w6_v3_default` | b8eadcb51e8705e7 | 4.25% | 212 | 91,055 | 5.8% | 5.2% | 28,647 | 283/6,388 | 0/0 |
| `w6_v3_activity_off` | c88ba9104f45f897 | 2.39% | 119 | 62,275 | 2.7% | 3.8% | 20,344 | 283/6,388 | 0/0 |
| `w6_v1_default` | e1288e092ddaca86 | 2.59% | 129 | 65,050 | 2.8% | 3.9% | 20,807 | 283/6,388 | 1/384 |
| `w6_v1_derive_v2_1` | cfbba0d504a27aa7 | 2.60% | 130 | 67,475 | 2.8% | 3.7% | 19,920 | 280/6,383 | 3/328 |
| `w6_v2` | c186b380ae65cb86 | 2.63% | 132 | 67,756 | 2.8% | 3.8% | 19,997 | 283/6,388 | 1/230 |
| `w6_v1_edge` | d1c56f85847c21db | 2.51% | 126 | 64,227 | 2.8% | 3.2% | 21,565 | 283/6,388 | 6/442 |
| `w6_v2_edge` | 948b975a2ab74231 | 2.56% | 128 | 66,693 | 2.8% | 3.1% | 20,687 | 283/6,388 | 2/274 |
| `w6_v1_edge_plateau` | ff8fc6b562622640 | 2.54% | 127 | 64,720 | 2.8% | 3.3% | 21,947 | 283/6,388 | 7/386 |
| `w6_old_v1_default` | 78b6fec6036b2438 | 2.59% | 129 | 65,050 | 2.8% | 3.9% | 20,807 | 283/6,388 | 1/384 |
| `w6_old_v1_derive_v2_1` | f647f0483ef3d7ca | 2.60% | 130 | 67,475 | 2.8% | 3.7% | 19,920 | 280/6,383 | 3/328 |
| `w6_old_v2` | 9d8a34ee545f484a | 2.63% | 132 | 67,756 | 2.8% | 3.8% | 19,997 | 283/6,388 | 1/230 |
| `w6_old_v1_edge` | 245b2fdb8aa229ef | 2.51% | 126 | 64,227 | 2.8% | 3.2% | 21,565 | 283/6,388 | 6/442 |
| `w6_old_v2_edge` | 2fb54c9ad562faca | 2.56% | 128 | 66,693 | 2.8% | 3.1% | 20,687 | 283/6,388 | 2/274 |
| `w6_old_v1_edge_plateau` | dd66261d71c4d6ae | 2.54% | 127 | 64,720 | 2.8% | 3.3% | 21,947 | 283/6,388 | 7/386 |
| `w6_golden_null_arm` | 19ee17b1b1caf44c | 2.59% | 130 | 46,278 | 2.9% | 4.6% | 17,937 | 0/0 | 5/648 |
| `v3_mem_store` | a9f6f9f0adb3f9a4 | 4.25% | 212 | 91,055 | 5.8% | 5.2% | 28,647 | 283/6,388 | 0/0 |
| `v3_mem_rel` | 768b2262e3b0999e | 4.25% | 213 | 90,780 | 5.9% | 5.3% | 28,435 | 283/6,388 | 0/0 |
| `v3_classical` | ca25874a5e4acb79 | 4.42% | 221 | 99,253 | 6.7% | 6.4% | 31,483 | 283/6,388 | 0/0 |
| `v3_classical_mem_rel` | 9dd9d5684891b57c | 4.47% | 223 | 99,626 | 6.9% | 6.7% | 32,738 | 283/6,388 | 0/0 |

- 一致しない構成は無かった=「どの系が何を見落としたか」の行は無い。腕を「一致した構成だけで有効」にする環境変数の守りは置いていない(要らなかった)。
- 語彙 v3 の構成の聞こえ 0 は、ひと言が無い(発話の口 off=会話の番は全部 silent)ため。`w6_golden_null_arm` は計画実行層が無い(到着の予定が無い)。

### 4-3. 刻みあたりの時間(P4)

5,000 体・1 日(`w6_v3_default`・テープなし・子プロセスで 1 本ずつ)を腕 all と changed で交互に 3 回ずつ回し、進行役の `run_system` を包んで系ごとの壁時計を数えた(刻みあたり ms の中央値・並行して別の作業木のランが動いていた)。final は 6 本とも `b8eadcb51e8705e7`。

| 系 | 腕 all | 腕 changed |
|---|---:|---:|
| detect(検出の系の全体=セルの描画欄の変化・内受容・段の書き戻し・候補) | 0.341 | 0.351 |
| body(体の自然な変化) | 0.193 | 0.398 |
| world | 0.715 | 0.701 |
| 刻みの系の和 | 27.83 | 27.39 |
| ランの壁時計[秒] | 41.9 | 41.2 |

- 5,000 体では速くならない: 内受容の判定は検出の系の一部(腕 changed の検出器の呼び出しは 0.21 ms/刻み=manifest の `detect_seconds_nondeterministic` 0.305 秒/日)で、印を付ける写しの比べ(体の数の配列 6 本)と判定の差が小さい。体の反映(TM5 の予約)は 2.1 倍遅い(3-5 の記録の 2.6 倍と同じ向き=全員のエネルギーの積み上げと入力の写しの比べが残る)。ランの壁時計の差は揺れの中。
- 39 万体(合成の体・内受容の判定だけ・30 回の中央値・値を一部の体だけ動かして写しの比べの手間を含む):

〔検収 M5〕写しの更新(`after_detection`=印の体の 6 列の写しを書き直し、跨いだ体を集める=腕 changed だけにかかる手間)を含めて
測り直した(30 回の中央値・直しの後の src):

| 印の割合(実測) | 全員を見る版[ms] | 印の体だけ[ms](うち写しの比べ) | 写しの更新[ms] | **腕 changed の合計[ms]** |
|---:|---:|---:|---:|---:|
| 0.39% | 0.738 | 0.309(0.221) | 0.072 | **0.381** |
| 1.57% | 0.876 | 0.477(0.318) | 0.187 | **0.661** |
| 3.91% | 0.964 | 0.686(0.468) | 0.337 | **1.030** |

  **5,000 体の実測の印の割合(2.4〜4.5%)の帯では、39 万体でも内受容の判定は速くならない**(3.91% で 0.964 → 1.030 ms)。速く
  なるのは印が 2% 前後より少ないときだけ。写しの比べ(体の数の配列 6 本)と写しの更新が全員の判定と同じ桁で残るため。縮めるのは書き手の
  知らせの口(驚き駆動の版上げ=計画 6-2)。腕 changed の意味は「何かあった体だけ」の形と全員を見る版との一致の確認(版上げの前の器)。

  予算の宣言に写す形(親が写す): 「T3 腕 changed(既定 off)=刻みあたり 5,000 体 detect 0.341 → 0.351 ms・body 0.193 → 0.398 ms・
  系の和 27.8 → 27.4 ms(揺れの中)/39 万体の内受容の判定 0.964 → 1.030 ms(印 3.91%・写しの更新を含む)・処理した体の割合 内受容 2.4〜4.5%・体の反映
  2.7〜6.9%・新しい逐次ループなし(区域ごとの時計の区域の数 30 × 区域の窓の中の時刻の数は宣言)」。
- 逐次ループ: 新しく体の数に比例する Python のループは無い(印は配列の比べ・判定は 3 変数 × 段の境目 3 つの定数回)。区域ごとの時計は区域の数(30)× 区域の窓の中の時刻の数の小さなループ(宣言は `engine/regional_clock.py`)・境目の移動の数え(体の数の配列 1 本)は刻みの事象のある窓だけ。

## 5. T4 場所ごとの時計

### 5-1. 区域と境目

| 規則 | 中身 |
|---|---|
| 区域 | セルの重心を 500 m の格子で塊にしたもの(格子の (x, y) の昇順に番号)+舞台の外(セル < 0)の区域 1 つ。世界資産 520 セル → 29 区域+外=30。重心の無い世界はセルの番号 ÷ 25(どちらの世界も重心を持つ=使われない) |
| 区域ごとの窓 | 区域ごとに窓の頭を持つ。全体の窓 [t, t+W) の刻みの事象(世界の 1 回の系の並び=全員の配列)を処理した後に、区域の事象を区域の番号の昇順に区域ごと・区域の中は時刻 → 体 → 予約の番号の順に処理し、全部の区域の頭を t+W にする(障壁=先読み幅は窓の幅・R-73 §2-2 の同期型)。区域どうしは窓の中で互いを待たない |
| 区域の事象 | 会話の時計の発言(腕 mora)。話し手の今のセルの区域に置く。違う区域の会話は別の束になる(束の数が増え、最大の束が小さい=試験) |
| 境目で届ける | (a) 発言を別の区域で聞く=窓の終わりに届く(遅れ=窓の終わり − 発言の時刻・`hear_*`)(b) 処理し終えた区域へ同じ窓の時刻で予約した事象=窓の終わりへ(`cross_events`)(c) 移動=窓の境目で体の区域を前の境目の写しと比べて数える(移動は刻みの事象の中=次に読まれるのは次の刻み=全体で 1 つの時計との遅れ 0・`cross_move_delay_ns_max=0`)(d) メッセージ・電話は今の世界に無い(C1 の後)=欄だけ |
| 遅刻 | 計画実行層の日の表(ブロックごとの到着の刻みと始め)から、窓に入った刻みの予定の到着のうち到着が始めより遅い数と分(計器だけ・本人の出入りではない) |
| 待ち合わせ | 約束の仕組みが無い(C10 8d の後)=欄だけ(`meeting=null`) |
| 混合 | `--clock mixed` は口だけ(〔検収 L7〕組み立て=build の段で `NotImplementedError`=宣言・試験は止まった場所を見る) |

- 試験(`tests/engine/clock/test_tm4_regional_clock.py`): 区域の作り方・世界資産の 29 区域・区域ごとの処理の順と束・聞こえの遅れ(同じ区域 0・別の区域=窓の終わり − 時刻)・処理し終えた区域への予約は窓の終わりへ・過去への予約の拒否・境目の移動と遅れ 0・遅刻の数と分・混合は止める・既定 global との一致(合成の世界・世界資産 1,000 体+会話の時計)・2 日と再開・段 B・CLI・TM4 の道具の遅刻の列。

### 5-2. 一致の表

- byte-check 19 構成・25 欄=19/19 同じ(§6・直しの後は §13-3)。区域ごとの計器は §4-2 の表の右 3 列(3 つの腕を全部立てたラン)。
- 〔検収 M4〕**この一致は構造上いつも成り立つ**: 腕 regional を単独で立てたランは区域の事象が 0 件(`events=0`)・会話の時計を載せても区域の事象は計器だけで、どちらも世界を書かない。区域ごとの時計の誤り(区域の事象の処理の順・境目の届け方)が世界を変える形はまだ無い=TM1 の「誤りの検出」としての一致の試験は、世界を書く区域の事象が入る段(T2 の版上げ・C1)の後(`DOC-tm234-t4-structural-identity`=remove_at 6-4)。
- 世界資産 1,000 体(v1・記憶+関係)で会話の時計を載せた全体の時計と区域ごとの時計: final・呼数・checkpoint が同じ・会話の計器は区域またぎの聞こえ(遅れ)と束の分け方(束の数・最大の束)のほかは全部同じ(試験)。

### 5-3. メッセージの遅れの計器と遅刻(TM4 の道具)

道具 `tools/instruments/batch_width_gauge.py`(本段で遅刻と待ち合わせの列を埋めた)を、腕 regional+mora・世界資産 1,000 体・v1・記憶+関係・母集団の seed 1・salt 1〜6・幅 60・30・10・5・1 秒で回した(正解=いちばん細かい 1 秒)。

| 幅 W[秒] | salt の数 | final が同じ | 呼数 差 / salt の幅 / (g) | 行動の件数 差 / salt の幅 / (g) | メッセージの遅れの最大[秒] 差 / salt の幅 / (g) | 遅刻 差 / salt の幅 / (g) | 待ち合わせ |
|---|---|---|---|---|---|---|---|
| 60 | 6 | 1 | 0 / 164.8 / 中 | 0 / 1100 / 中 | 29.5 / 0.5748 / 外 | 0 / 0 / 中 | — |
| 30 | 6 | 1 | 0 / 164.8 / 中 | 0 / 1100 / 中 | 14.5 / 0.5748 / 外 | 0 / 0 / 中 | — |
| 10 | 6 | 1 | 0 / 164.8 / 中 | 0 / 1100 / 中 | 4.5 / 0.5748 / 外 | 0 / 0 / 中 | — |
| 5 | 6 | 1 | 0 / 164.8 / 中 | 0 / 1100 / 中 | 2 / 0.5748 / 外 | 0 / 0 / 中 | — |
| 1(正解) | 6 | 1 | 0 / 164.8 / 中 | 0 / 1100 / 中 | 0 / 0.5748 / 中 | 0 / 0 / 中 | — |

- (f) 単調: 呼数・行動・メッセージの遅れ・遅刻とも「はい」。既定の幅の候補(記述)は 1 秒(メッセージの遅れの (g) を満たすのは正解の幅だけ=遅れは構造で W に比例する)。
- メッセージの遅れの中身: 6 salt のうち 3 salt で区域またぎの聞こえが 1〜2 回あり、その遅れの最大がちょうど W(会話の番は刻みの頭で作られ、発言の事象は持ち越しで刻みの頭に置かれる=窓の終わりまで W)。TM4 の目標「メッセージの遅れ 10 秒以下」は W ≤ 10 で満たす。世界の結果(final・呼数・行動)はどの幅でも同じ(世界の事象の粒度は 60 秒のまま)。
- 〔検収 L5〕遅刻: どの幅・salt でも遅い到着 24(1,000 体)。数えるのは計画実行層の日の表(到着の刻みとブロックの始め)=窓の幅で動かない構造=TM4 の指標の列は埋まったが差は測れない(本人の到着の遅れは 6-2 の 1b の後)。待ち合わせは欄だけ。
- (g) の salt の幅は 3-2 と同じ読み(正解の腕の salt 間の幅・expedient)。

## 6. byte-check と 2 日・再開

| 確かめ | 範囲 | 結果 |
|---|---|---|
| byte-check 既定 | 10e の道具(本体の道具・`side --src`)・19 構成・5,000 体・seed 1・1 日・テープつき。HEAD 側=`4f186fb` の写し(`HEAD_TREE_FILES`+本体の data へのつなぎ=.NET で外す)・作業木側=作業木の src | **19/19 構成で 25 欄とも同じ** |
| byte-check 腕 changed | 同じ・作業木側だけ `SHIBUYA_STEP_SCOPE=changed` | **19/19・25 欄とも HEAD と同じ** |
| byte-check 腕 regional | 同じ・`SHIBUYA_CLOCK=regional` | **19/19・25 欄とも HEAD と同じ** |
| byte-check 腕 mora | 同じ・`SHIBUYA_TALK_CLOCK=mora` | **19/19・25 欄とも HEAD と同じ** |
| 3 つの腕を全部 | 19 構成(計器を集める道具・テープなし)・3 つの環境変数を全部 | 19/19 で final が HEAD と同じ(§4-2 の表) |
| 2 日のラン | 5,000 体・seed 1・世界資産・既定 v3・activity・テープつき。HEAD の写し・既定・changed・regional・mora の通し | 5 本とも final `b346bb6e3ecc60af`・138,946 呼・8 つの checkpoint の behavior-hash・テープの calls と blocks の中身の sha(`7b2ba202…`・`2293072f…`)が同じ |
| 再開 | changed・regional・mora のそれぞれで、刻み 1,440(日の境目)と刻み 2,211(2 日目の途中)で止めて再開 | 6 本とも final `b346bb6e3ecc60af`・呼数の和 138,946・再開の後の checkpoint は通しの末尾と同じ・止めたランと再開のランのテープの sha は腕によらず同じ(日の境目 `d764f256…`/`3dca122c…`・途中 `1c7a2e27…`/`4db846c1…`)。再開の後の最初の検出は全員(`full_steps=1`)・区域の窓は再開の刻みから |

- HEAD の 19 構成の final は 3-2・3-5 の記録と同じ(w6_v3_default `b8eadcb51e8705e7` ほか)。
- つなぎの台帳の active の行は 456 → 470(本段の 14 行)。manifest と日次の記録の `bridges_count` はこの分だけ動く(byte-check の 25 欄の外=3-2 と同じ)。
- 腕は設定の指紋に入る(既定と違うときだけ=3-2 の幅と同じ形)。腕の違う再開は「設定が親と違う」で止まる(試験)。

## 7. TM9 の欄

- GPU 無しの欄(判断モデルと LLM を分けた呼び出し数 `calls_by_model`・時計の種類 `clock_kind`・刻みの幅 `step_seconds`・つなぎの台帳の数 `bridges_count`)は第 1 期 1-1 T0 で manifest と日次の記録に入っている(10f と一体)。本段で変えたのは `clock_kind` の値だけ: 腕 regional のランは `regional`(manifest と日次の記録の両方)・既定は今の `steps`(`core.time_consts.CLOCK_KIND`)。T2・T3 の腕は時計の種類を変えない(会話の時計と変化の印は manifest の節 `talk_clock`・`step_scope` に出る)。
- 判断モデルの呼び出し数は 0 のまま(判断モデルは 6-1 の後)。

## 8. TM10 の表(指示書の値と R-73 の幅)

指示書 10-03 §7-5・§7-6 の推測値と、R-73 §6 の検算の幅を並べる。決定 10-12 §4-2 TM10 (b) のとおり、今回の決定で上にずれ得る点を書き添える。K3(GPU の調達)の材料には R-73 の幅を使う。どれも推測(R-73 の印のまま)。

| 量 | 指示書の値(10-03 §7-5・§7-6) | R-73 の幅(§6) | 今回の決定(10-12 §4-2)で上にずれ得る点 |
|---|---|---|---|
| LLM の呼び出し | 約 700 万回/日(会話 1 人 2 回 × 8 往復+高度な判断 2 回) | 7,021,206 回/日(同じ前提の再現) | TM3: 会話の番は発言 1 つ=1 呼(1 回の LLM に会話全部を書かせない)。会話の回数と往復は R-b で置き換え |
| 判断モデル | 約 2,000 万件/日(1 人 50 件) | 19,503,350 件/日 | TM2: 考えた時間を本人の出力から(迷い・トークン数)=出力が長くなる腕がある |
| 同時に進む会話 | 約 540 件(昼のピーク約 1,100) | 平均 541.8 件 | TM3: 違う会話どうしはバッチ・同じ会話は順番=窓の中の会話の連鎖の長さで 1 窓の実時間が決まる |
| H100×8 の 1 シム日 | 約 4.7〜9.6 時間 | LLM 約 7.5〜17.8 時間+判断モデル約 4.3〜33.9 時間=合計約 11.7〜51.7 時間 | 判断モデルの入力の長さが最大の変数(R-73 §6-3)。TM2 の考えた時間の腕・TM3 の会話の時計の入力(聞こえた範囲の相手の発言)で入力が伸びる |
| 資源が無限・全体の窓で同期の下限 | 約 1〜2.5 時間 | 1.9〜11.5 時間(1 発話の生成 L=0.2〜0.9 秒・発言の長さ+間 d=1.88 秒=英語の値) | TM3 の d は日本語の話す速さで決まる: 本段の会話の時計では mock の文(5〜7 モーラ)で d≈0.76〜0.89 秒+7 ms=英語の 1.88 秒より短い → 下限は上へ(実 LLM の発言の長さで置き換える)。TM4 の目標(遅れ 10 秒以下)で窓が細かくなる |
| 資源が無限・別々の時計の下限 | 約 10〜20 分 | 空欄(依存の構造が無い)・AI Metropolis の実測は全体同期の 1.3〜4.15 倍速い | T4 の区域ごとの時計は今は系を区域に割らない(区域の事象は会話の時計だけ)=速さの差はまだ測れない |

## 9. manifest の節・状態台帳の行・つなぎの台帳

### 9-1. manifest(末尾・腕のランだけ出る=既定のランの manifest の鍵は今のまま)

| 節 | 設定の子 | 観測の子 |
|---|---|---|
| `talk_clock` | schema・arm・anchors(出典の表)・sigma_between・sigma_within・familiar_delta・gap_ns・think_time・mora_rule・modalities・cap_per_window・kind・rank・bins | turns・utterances・silent・no_session・lang_other・chat_blank・familiar・unfamiliar・familiar_unknown・persons・carried・lag_ns_sum・lag_ns_max・ahead・cap_hits・dispatches・batch_max・batch_sum・mora_sum・speech_ns_sum・utterance_ns_max・gap_ns_sum・heard・cross_heard・hear_delay_ns_sum・hear_delay_ns_max・conversations・conv_silent・conv_open_at_end・conv_tm3_ns_sum・conv_table_s_sum・conv_span_s_sum・pending_at_end・mean_*・person_rate_*・hist |
| `step_scope` | schema・arm・narrowed・not_narrowed・mark_columns・body_schedule | steps・full_steps・marked・marked_max・crossed・full_equiv・detect_seconds_nondeterministic・marked_mean・marked_share |
| `clock` | schema・arm・clock_kind・region_size_m・regions_from・n_regions・outside_region・width_s・messages・meeting_note・mixed | windows・region_windows・events・dispatches・cross_events・cross_delay_ns_sum・cross_delay_ns_max・boundaries・cross_moves・cross_move_delay_ns_max・hear・hear_cross・hear_delay_ns_sum・hear_delay_ns_max・planned_arrivals・late_arrivals・late_minutes_sum・late_minutes_max・message_delay_ns_max・pending_at_end・meeting |

- 節の表(`engine/manifest_sections.py`)に混ざった辞書 3 つを足した=設定の子 31 本=`CONFIG_PATHS_SHA256` を `b48498e8…0edcaa` から `f44871a3…c0ab7a0` に(この 31 本を外すと前の値に戻る)。既定のランの manifest の一番上の鍵と並び(凍結の表)は変わらない。

### 9-2. 状態台帳(腕の行 4 つ・どれも軸 1 diag・軸 2 discardable=どちらのハッシュにも状態のファイルにも入らない)

| 行 | 持ち主 | 道筋 | 腕 |
|---|---|---|---|
| `TCR` 話す速さの控え | `talk_clock`(TalkClock) | `_tc_rate` | talk-clock |
| `TCC` 会話の時計の持ち越し・予約・計器 | 同 | `_tc_line`・`_tc_pending`・`_tc_meter` | talk-clock |
| `T3M` 変化の印 | `step_scope`(StepScope) | `_ss_copy`・`_ss_crossed`・`_ss_meter` | step-scope |
| `T4W` 区域の窓 | `clock`(RegionalClock) | `_rc_head`・`_rc_events`・`_rc_seq`・`_rc_snap`・`_rc_late`・`_rc_meter` | clock-regional |

- 外の状態 120 → 124 行・全体 211 → 215 行(版は上げない=3-3 の X・3-2 の BW と同じ理由)。持ち主のクラス 3 つを `OWNER_CLASSES` に・設定と参照と窓の中の作業の値を `EXCLUDED` に足した。遅刻の計器が計画実行層の日の表(行 O38=軸 1 no)を読むので、診断の出口 `DIAG_EXITS` に `RegionalClock._lateness` を足した。乱数の呼び手 2 つ(`person_mora_len_s`・`utterance_jitter`=k19 の並べ方・一様 1 語)を `rng_audit.SAFE_SITES` に足した(16 → 18)。

### 9-3. つなぎの台帳(文書の行 15・`declared_in` は本書)

| id | 中身 | remove_at(basis) |
|---|---|---|
| `DOC-tm234-talk-clock-meter-only` | 会話の時計は計器だけ・会話の番は刻みに 1 回 | T2(plan=版上げ) |
| `DOC-tm234-mora-rule` | モーラ数=1-8b の仮名の近似・他の言語は欄だけ | T2(inferred) |
| `DOC-tm234-rate-distribution` | 人ごとの速さの分布の形(切った対数正規・範囲 ÷ d2) | 7(inferred) |
| `DOC-tm234-within-cv` | 揺れ CV 0.42(句の長さの項なし) | 7(inferred) |
| `DOC-tm234-familiar-partner` | 相手の項(英中の平均 9.6%・基準=親しい相手) | 7(inferred) |
| `DOC-tm234-gap-constant` | 間=平均 7 ms の定数・考える時間は足さない | 7(inferred) |
| `DOC-tm234-talk-anchor-carry` | 最初の発言の置き方・持ち越しの読み・締め/あいづち/重なりは入れない | T2(inferred) |
| `DOC-tm234-talk-cap` | 会話ごとの 1 窓の上限 2^10 | T2(inferred) |
| `DOC-tm234-chat-blank` | C1 の口の値は空欄 | 6-4(plan) |
| `DOC-tm234-t3-mark-by-copy` | 変化の印=写しとの比べ | 6-2(plan=1b+T3 の版上げ) |
| `DOC-tm234-t3-not-narrowed` | 絞らない走査(セルの起床・計器) | 6-2(inferred) |
| `DOC-tm234-t4-region` | 区域=500 m の格子 | 7(inferred) |
| `DOC-tm234-t4-messages-meeting` | メッセージ・電話・待ち合わせは欄だけ・遅刻は計画の表から | 6-4(plan) |
| `DOC-tm234-t4-mixed-port` | 混合の時計は口だけ | 7(inferred) |
| `DOC-tm234-t4-structural-identity` | 〔検収 M4〕T4 の一致は構造上の一致(区域の事象は世界を書かない) | 6-4(inferred) |

- 3-2 の 4 行(remove_at T2・status は不変)の why の末尾に注: `DOC-tm32-event-time-60s`(腕 mora では発言の事象がナノ秒の時刻で入る=前半は腕のランで外れる・世界の系の並びは刻みごとのまま)・`DOC-tm32-same-time-body-order`(発言の事象も同じ順=宣言のまま)・`DOC-tm32-conversation-not-batched`(腕 mora では同じ会話を同じ束に入れたら止める検査を足した=「検査が無い」は腕のランで外れる)・`DOC-tm32-window-cap`(発言の事象もこの上限に入る・会話ごとの上限は別の行)。

## 10. 試験

- 新しい試験 59 本(`tests/engine/clock/`): `test_tm2_talk_clock.py` 32(data 要 2・うち slow 1=5,000 体 1 日)・`test_tm3_step_scope.py` 11(data 要 1)・`test_tm4_regional_clock.py` 16(data 要 2)。全部 passed。
- 凍結の表と数の試験の更新(増えた分だけ): 状態台帳の行の数と並び・腕の行の並び(10b・1-8b)・`CONFIG_PATHS_SHA256`(10f)・`rng_audit.SAFE_SITES` の数 16 → 18(10f)・乱数の用途名の表(`engine/run.py` の `POPULATION_RNG_DOMAINS` に `talk.rate`・`MOTION_RNG_DOMAINS` に `talk.jitter`=試験 `test_salt_seed_split_10f.py`)・TM4 の道具の遅刻の列の注。
- 範囲(`tests/engine/clock`・`batching`・`speech`・`body`・`decision`・`events`・`bridging`・`time`・`systems`・会話の 2 本・P6・状態台帳 10b・10f の 3 本・再開 10d・道具・子プロセスの import・8 並列・slow を含む): **916 passed**(12 分 51 秒・最後の直しの後)。`tests/economy/cp2`: **109 passed**。
- 全体(`-m "not gpu and not slow" -n 8 --dist loadfile --ignore=tests/c7`・直しの前の 1 回): 5,416 passed・4 failed・1 skipped・1 xfailed。落ちた 4 本のうち 2 本(腕の行の並び・乱数の用途名の表)は本段の凍結の表の漏れ=直して上の範囲で通った。1 本(`test_child_imports_this_tree.py`)は `PYTHONPATH` を相対の `src` で渡した回し方のせい(絶対の道筋で通る)。残りの 1 本は既知の `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(作業木の `data` が本体へのつなぎ=3-2・T0 の記録と同じ)。`tests/c7` は回していない。
- `lint-imports`: 5 契約とも守られている(264 ファイル・作業木の src)。
- 最後の直し(getattr の読み・写しの形・乱数の用途名の表)の後に byte-check 4 構成(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel・テープつき)を既定と 3 つの腕を全部立てたランで回し直した: どちらも **4/4 で 25 欄とも HEAD と同じ**。

## 11. 触った共有ファイル(並行の作業木との突き合わせ用)

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/systems/boxes.py` | `OWNER_NAMES` の末尾に `talk_clock`・`step_scope`・`clock`・`Layers` の末尾に同じ名の 3 欄 |
| `src/shibuya/engine/systems/state_io.py` | `hash_owners` の末尾に 3 つ・日次の記録の `clock_kind`(1 行)・import 1 行 |
| `src/shibuya/engine/systems/build.py` | 設定の指紋(3 つの腕・6-5 の暦の影の後)・体の層の腕(changed のとき reserve)・会話の時計と変化の印を作る 2 行(発話の口の後)・`Layers(...)` の末尾に 2 つ |
| `src/shibuya/engine/systems/conductor.py` | `WINDOW_MARK_KEYS`・`declared_check` の窓の境目・区域ごとの時計と会話の時計の口を挿す 15 行(窓の待ち行列の後)・窓のループに 4 行 |
| `src/shibuya/engine/systems/llm_io.py` | `utter` に会話の時計の 4 行(`conv.utterance` の後) |
| `src/shibuya/engine/systems/talk.py` | `sys_conversation` に終わった会話の 4 行(体の出来事の口の前) |
| `src/shibuya/engine/systems/perceive.py` | `sys_detect` の検出の呼び出しを腕で分ける 7 行 |
| `src/shibuya/engine/systems/run_end.py` | `close_final` に結果へ渡す 3 行(暦の影の後) |
| `src/shibuya/engine/systems/table.py` | llm_receive・decide の `paths` と `reads`・conversation の `paths` と `reads`・detect の `paths` と `reads`・day_close と close_final の `reads`(末尾に足しただけ) |
| `src/shibuya/engine/state_ledger.py` | `_EXT` の末尾(6-5 の M0S の後)に 4 行・`OWNER_CLASSES` の末尾 3 つ・`EXCLUDED` の末尾 11 行 |
| `src/shibuya/engine/state_ledger_ast.py` | `DIAG_EXITS` の末尾 1 行 |
| `src/shibuya/engine/rng_audit.py` | `SAFE_SITES` の末尾 2 行 |
| `src/shibuya/engine/run.py` | import 3 行・`_tm234_sections`(関数 1 つ)・manifest の末尾(3-1 の calendar_shadow の後)・`clock_kind` の 1 行・乱数の用途名の表 2 行(`talk.rate`・`talk.jitter`) |
| `src/shibuya/engine/manifest_sections.py` | `PATHS` の末尾に混ざった辞書 3 つ |
| `src/shibuya/engine/batching.py` | `WindowQueue.now_ns`(読み口 1 つ) |
| `src/shibuya/engine/change_detect.py` | `detect` の引数 `scope` と `_interoception_scoped`(既定の道は今のまま) |
| `src/shibuya/cli.py` | `--talk-clock`・`--step-scope`・`--clock`(`--calendar-shadow` の前)・`main` の腕の置き方 3 つ・`cli.run` のランの種類に 1 条件 |
| `docs/design/bridging-ledger.json` | 末尾に 14 行・3-2 の 4 行の why の末尾 |
| `tools/instruments/batch_width_gauge.py` | `DEFAULT_METRICS` の 2 行・子プロセスの出力・docstring(発注の「空欄を埋める」・編集してよい一覧の外=§12) |
| 凍結の表と数の試験 | `tests/engine/test_state_ledger_10b.py`(行の数と並び)・`tests/engine/test_env_and_sections_10f.py`(`CONFIG_PATHS_SHA256`)・`tests/engine/test_state_checks_10f.py`(`SAFE_SITES` の数)・`tests/engine/speech/test_speech_port_schema.py`(腕の行の並び)・`tests/tools/test_batch_width_gauge.py`(遅刻の列の注) |

## 12. 仮採用・限界・親に確かめてほしいこと

### 12-1. 仮採用(10-13b §0-3=既存の決定と原文から一つに決まらない所・戻せる形)

1. モーラ数は 1-8b の仮名の近似(漢字 2 拍)。読みの辞書は使わない(R-111 §3-5 の道具の調査がまだ)。英語などは欄だけ(今の表でつなぐ)。
2. 人ごとの速さの分布は切った対数正規・幅は範囲 ÷ d2(18)。属性(年齢・性別)の項は入れない。
3. 揺れは CV 0.42(句の長さの項を入れない値)。
4. 相手の項は英語と中国語の平均 9.6%・基準(倍率 1)を親しい相手と読んだ(CEJC の日常会話)。
5. 間は平均 7 ms の定数(中央値 0・ばらつきの値が原典に無い)。考える時間(TM2)は足さない。
6. 会話の時計に入れないもの: 返事待ちの招待への返事(セッションの外=会話の番の 7 割強)・締めの定型 1 発話・あいづち・重なり。最初の発言は作った時刻に始まり、始まりが今より前の発言は持ち越しに数える。
7. 会話ごとの 1 窓の上限 2^10(安全装置)。
8. 発言の乱数: 人ごとの速さは母集団の seed、揺れは動きの seed(話し手・作った時刻・会話の番号)。どちらも一様 1 語の逆関数(静的な乱数の検査で安全な形)。
9. T3 の変化の印は写しとの比べ(体の数の配列の比べ 6 本)。腕 changed は体の反映を reserve にする(体の腕を別に指定しても reserve)。
10. T4 の区域は 500 m の格子(建物・駅は使わない)・区域の事象は会話の時計の発言だけ・系は区域に割らない。移動の遅れは「次に読まれる刻み」との差で数える(=0)。
11. 3 つの腕は既定と違うときだけ設定の指紋に入れる(3-2 の幅と同じ形)。manifest の節は腕のランだけ出す。

### 12-2. 限界

- T2 は計器: 会話の番は刻みに 1 回のまま。会話の時計の時刻は世界の行動に効かない(版上げで会話の番を窓の中で回すまで)。発話の口の発言の時刻(`Utterance.t_ns`)も刻みの頭のまま。
- 会話の時計の分布は mock の決まった文(5〜7 モーラ)の値。実 LLM の発言の長さでは平均が上へ動く(TM10 の d)。関係の層のある構成では相手は全部「親しい」で、知らない相手の項は効いていない。
- T3 の印は体の数の配列の比べ(O(体の数))で、書き手ごとの知らせではない。絞らない走査が残る(§4-1)。5,000 体では刻みあたりの時間は縮まない(§4-3)。
- T4 は系を区域に割らない(速さの差は無い)。区域の事象は会話の時計だけ・メッセージと電話は無い・遅刻は計画の表から(本人の出入りではない)・待ち合わせは欄だけ。
- T3・T4 の一致は「世界の状態が変わらない」こと(既定の結果と同じ)で、区域ごとの処理の正しさの一部(区域の事象が世界を書く形)はまだ試していない(その事象が無い)。

### 12-3. 親に確かめてほしいこと

1. `tools/instruments/batch_width_gauge.py` を直した(発注の「batch_width_gauge.py の空欄を埋める」・編集してよい一覧には無い)。指標の道筋 2 行と子プロセスの出力だけ。
2. 〔直しの後〕回し直した compare の JSON は本書のフォルダに置いた(§13-3)。直しの前の side と道具は `_bc/`・直しの後の side は `_bc2/` に置いた(「記録 1 本」に合わせて記録のフォルダには置いていない)。記録のフォルダに入れるかは親の判断。`_bc/` は取り込みに載せない(3-2 の L9 と同じ)。
3. 本体の 10e の道具の `SWITCH_ENV` に `SHIBUYA_STEP_SCOPE`・`SHIBUYA_CLOCK`・`SHIBUYA_TALK_CLOCK` が無い(side の JSON の `env` に腕が残らない=3-2 の L3 と同じ・本体の道具なので触っていない)。
4. 会話の時計がセッションの外の返事(招待への返事)を数えない読み(仮採用 6)。招待の段階を会話の時計の最初に入れるかは版上げで。
5. TM4 の既定の幅: 世界の結果はどの幅でも同じで、メッセージの遅れ(区域またぎの聞こえ)は W と同じ=「差が salt のばらつきに入る一番大きい幅」は今は正解の幅(1 秒)になる。会話の番を窓の中で回す版上げの後に測り直す。

## 13. 検収の後の直し(検収役=条件つき受入・中 6・低 7)と rebase

### 13-1. 直しの表

| 番号 | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| 中 M1 | `engine/systems/table.py`(decide・llm_receive の `paths`)・`engine/state_ledger.py`(行 BW・T4W の注) | 腕 mora の会話の番の発言の予約が書く `BW:batching.*`(全体の窓の待ち行列)と `T4W:clock.*`(区域ごとの時計)を 2 つの系の宣言に足し、行の注の「書くのは」に書いた | `test_tm4_regional_clock.py::test_stage_b_declared_writes_with_utterances[global/regional]`(合成の世界・語彙 v1・150 体・600 刻み=発言 8・宣言の外 0)・**負の対照** `test_negative_control_stage_b_catches_the_missing_declaration`(decide の宣言から BW を外すと段 B が捕まえる) |
| 中 M2 | `engine/owner_guard.py`(新規・共通の口)・`speech_clock.TalkClock`・`step_scope.StepScope`・`regional_clock.RegionalClock`・`ANCHORS` | 3-2 の `WindowQueue` と同じ形: `__setattr__`・`__delattr__` の守り(書く口の自分の文の間だけ書ける・区域の事象の処理の関数を呼ぶ間は閉じる)・中身の辞書は持ち主の中に置き、欄には `MappingProxyType` の写し・配列は書けない印つき(書く口が置き換えるか、持ち主の中の書ける写しのビュー)・事象の列と区切りごとの数は組・`ANCHORS` の値は組。`register` は最初の窓の後は止める | `test_m2_talk_clock_refuses_writes_from_outside`・`test_m2_step_scope_refuses_writes_from_outside`・`test_m2_regional_clock_refuses_writes_from_outside`・`test_m2_the_region_handler_runs_with_the_clock_closed`(外から書く・消す・中身を書くと `AttributeError`/`TypeError`/`ValueError`) |
| 中 M3 | `speech_clock.TalkClock.on_turn`・時計の行に `last_made_ns`(行の組 7 → 8)・つなぎの台帳 `DOC-tm32-conversation-not-batched` の注 | 同じ会話の前の番と同じ時刻に作った番を止める(遅れ=持ち越しの有無によらない)。束の検査(規則 7)も残す | `test_m3_two_turns_of_a_conversation_that_is_not_late_are_refused`(遅れていない会話の始まりの刻みに 2 番を植えると止まる・次の刻みは通る)・`test_negative_control_batching_inside_one_conversation_is_refused`(遅れている会話)・`test_the_dispatch_check_also_refuses_one_conversation_in_one_batch` |
| 中 M4 | 記録 §0・§5-2・つなぎの台帳 `DOC-tm234-t4-structural-identity`(新しい行=remove_at 6-4)・行 T4W の注 | T4 の一致は構造上の一致(区域の時計は計器だけで世界を書かない)と書き、意味のある一致の確認は T2 の版上げと C1 の後とした。TM6 の受入は条件つき(構造上) | — |
| 中 M5 | 記録 §0・§4-3 | 39 万体の見積りに写しの更新(`after_detection`)を入れて測り直し、「5,000 体でも 39 万体でも速くならない」と直した。予算の宣言に写す文を §4-3 に | 道具 `_bc2/perf_t3_390k.py`(30 回の中央値) |
| 中 M6 | 記録 §0・§6・§13-3 | 最後の直しの後に本体 `32fb262` の写しと 19 構成(既定・changed・regional)と 4 構成(mora)を回し直し、比べの JSON を本書のフォルダに置いた(時点を §13-3 に) | §13-3 |
| 低 L1 | 記録 §3-1・つなぎの台帳 `DOC-tm234-rate-distribution` | 切った分布の偏り(平均のモーラの長さ 0.15357 秒=+1.7%・速さの平均 6.586・8.0% を切る)と R-73 の「18 人前後」を書いた。**切り方は直していない**(記録と台帳に書いた方を選んだ) | — |
| 低 L2 | `test_tm2_talk_clock.py` | 考える時間の負の対照を独立に落ちる形に(間に L4 を足す欠陥を植えて検査が捕まえる) | `test_negative_control_adding_the_think_time_is_caught` |
| 低 L3 | `test_tm2_talk_clock.py`・記録 §3-2 | 既知の数を「本当の数と規則が合う例」(9 本)と「漢字 2 拍の近似が外れる例」(混んでいるな 7/6・今日 4/2・一緒に行こう 9/7・渋谷駅 6/5)に分けた。**規則は直していない**(読みの辞書に替えるまで仮採用 1 のまま=長音・拗音・促音は仮名の規則で数え、漢字の読みの長さを拾えないと宣言) | `test_mora_rule_known_counts`・`test_mora_rule_known_misses_of_the_kanji_two_mora_approximation` |
| 低 L4 | `test_tm2_talk_clock.py`・`test_tm4_regional_clock.py` | 腕 mora の 2 日と再開を会話の番のある構成(合成の世界・語彙 v1・150 体)に・段 B を発言のある構成に(M1 と同じ試験)。空振りでないことを試験の中で確かめる | `test_two_days_and_resume_with_mora_match_the_straight_default`・`test_stage_b_declared_writes_with_utterances` |
| 低 L5 | 記録 §5-3・台帳 `DOC-tm234-t4-messages-meeting`・`RegionalClock._lateness` の docstring | 計画の表の遅刻は窓の幅で動かない=TM4 の指標の列は埋まったが差は測れない、と書いた | — |
| 低 L6 | `_bc/` | 触っていない(親が消す)。直しの後の作業の置き場は `_bc2/` | — |
| 低 L7 | `engine/systems/build.py`・記録 §5-1 | 腕 mixed は組み立て(build)の段で止める(進行役の口の検査も残す) | `test_mixed_is_a_port_only`(止まった場所が build) |

- 直しで見つけた 1 つ: 写しの配列の印を持ち主の中で外す書き(`setflags(write=True)`)は既存の試験 `test_direct_flag_writes_live_only_in_known_places` が止める=持ち主の中の書ける写しと欄の読むだけのビューに分けた(`StepScope`)。

### 13-2. rebase

- `git merge --ff-only build/spatial-d102-prep`(本体 `32fb262`)=早送り・衝突 0(本体の土台の後の変更は記録と文書 12 本だけ・src の差は 0)。

### 13-3. 回し直し(最後の直しの後・本体 `32fb262` の写し)

| 確かめ | 結果 | 比べの JSON(本書のフォルダ) |
|---|---|---|
| byte-check 既定・19 構成 | **19/19 で 25 欄とも同じ** | `byte_check_head32fb262_vs_default.json` |
| byte-check 腕 changed・19 構成(`StepScope` の最後の直しの後に回し直した) | **19/19 で 25 欄とも同じ** | `byte_check_head32fb262_vs_changed2.json` |
| byte-check 腕 regional・19 構成 | **19/19 で 25 欄とも同じ** | `byte_check_head32fb262_vs_regional.json` |
| byte-check 腕 mora・4 構成(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel) | **4/4 で 25 欄とも同じ**(JSON の残り 15 構成は回していない=「動いた」に見える) | `byte_check_head32fb262_vs_mora.json` |
| 2 日・2 日目の途中(刻み 2,211)からの再開・5,000 体 | 腕 changed と腕 regional+mora: final `b346bb6e3ecc60af`・呼数の和 138,946・テープの sha は直しの前と同じ | `_bc2/td/` |
| 段 B(発言あり)・合成の世界 150 体・600 刻み・語彙 v1 | 腕 mora(全体の時計)・regional+mora: 宣言の外 0 | 試験 |

- 時点: 既定・regional・mora は M1〜M3・L7 の直しの後、`StepScope` の写しの持ち方の直しの前の src(この直しは腕 changed の中だけ=既定・regional・mora の道は通らない)。changed はすべての直しの後の src。
- 試験(直しの後): `tests/engine/clock` 71 本(T2 39・T3 12・T4 20)。発注の範囲(`tests/engine/clock`・`batching`・`speech`・`body`・`decision`・`events`・`bridging`・`tests/economy/cp2`・10b・10f の 2 本・`tests/engine/time`・`tests/engine/systems`・乱数の用途名・道具・`-n 2 --dist loadfile -m "not slow"`): 904 passed・1 failed(上の `test_direct_flag_writes_live_only_in_known_places`=直した)→ 直した後に落ちたファイルと範囲の関わる試験(`tests/engine/systems/test_stage_a_guard.py`・`test_fix_guards.py`・`tests/engine/clock/test_tm3_step_scope.py`・10b)118 passed。`lint-imports` 5 契約とも守られている。`tests/c7` は回していない。

### 13-4. 本体 `8169d4b` への rebase(4-1 段 8〜9・カレンダー 1b の取り込みの後)

- 手順: 本段の変更 24 本を控え(本段の版と土台 `32fb262` の版)→ 作業木の追跡ファイルを土台に戻して `merge --ff-only 8169d4b` →
  ファイルごとに `git merge-file`(本段・土台・本体)。衝突 13 本は、どれも末尾に両方が足した所=並びを「本体の分 → 本段の分」に
  解いた(`systems/{table,build,boxes,state_io,run_end}.py`・`run.py` の manifest の末尾=`calendar_1b` の後に本段の 3 節・
  `manifest_sections.py`・`state_ledger.py` の `_EXT`・`OWNER_CLASSES`・`EXCLUDED`=C1B・C1BM の後・`cli.py` のランの種類の条件)。
  つなぎの台帳は本体の 507 行に本段の 15 行を足して作り直した(522 行・active 511・3-2 の 4 行は本体が触っていない=本段の why の注を
  載せた)。
- 数の新旧: 状態台帳 外の状態 122 → 126・全体 213 → 217(本体の C1B・C1BM の後に TCR・TCC・T3M・T4W)。`CONFIG_PATHS_SHA256` は
  本体の `02f950ae…b0ee3a1b` に本段の設定の子 31 本を足して `ffbed6e3…d0f252`(31 本を外すと本体の値に戻る)。凍結の表の試験 3 本
  (10b の数・外の行と腕の行の並び・1-8b の腕の行の並び)を同じ並びに直した。
- byte-check(本体 `8169d4b` の写し vs 作業木・`w6_v3_default`・テープつき): 既定=25 欄とも同じ(final `b8eadcb51e8705e7`)。
  腕 changed・regional・mora も 1 構成ずつ 25 欄とも同じ(final は前と同じ `b8eadcb51e8705e7`)。

