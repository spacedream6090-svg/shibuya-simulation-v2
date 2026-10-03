# 10d 日境界の再開と複数日の通しラン(D-102 Q3・Q5・A10・A11)

> 実行役(Opus 5.5)の記録。親と別のサブの検収の前。commit していない。基準: HEAD `8486f9c`(ブランチ `build/spatial-d102-prep`)。
> 指示: [アジェンダ §4・A10・A11](../../../../design/v2-d102-foundation-implementation-agenda.md)・[指示書 10-03 §3-6・§3-7](../../../../design/v2-wallbounce-decisions-2026-10-03.md)・[設計書](../../../../design/v2-resume-determinism-draft.md)。
> パスは `src/shibuya/` を省略。行番号は 10d の作業木。絶対パスは書かない。
> 後片付け: 作業用の写しと一時ファイル(短いパスの作業用ディレクトリ `w10d`=HEAD の写し・テープ・状態のファイル・scratch)は**検収の後に親が消す**。

## 0. 結論(親の答え 7 件を反映した後の値・§10)

1. **既定の結果は動いていない**。HEAD `8486f9c` の `git archive` の写しと作業木で、初版で 19 構成が 19/19 一致([byte_check.json](byte_check.json))、反映の後に既定 v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439・relations-on `40409ebed834126b`/72,930 の 3 本が final・呼数・blocks・calls の 14 列で 3/3 一致([byte_check_after_answers.json](byte_check_after_answers.json))。classical 1,500 体の golden `4f78f3c0`/25,808 は既存のテストで一致。
2. **複数日の通しラン**を世界資産・台帳・艦隊のランに広げた。日ごとに締め(1 日 1 回)、締めの後の 2 つのハッシュを日ごとに記録する。2 日目からは日の頭の初期化を**走らせず**(A11)、時刻表・計画実行層・計画境界(K9 のつなぎ)・天気の実日・出勤率・**営業時間の曜日の行(W7)・世界過程の日ごとの乱数の表**を「その日の分」に張り直す(§2・§10-5)。
3. **状態の書き出しと読み込み**(`run_day(state_out=…, stop_at_tick=…, resume_from=…)`・CLI `--sim-days`・`--resume-from`・`--state-out`)。保存するのは**状態台帳(10d 版・191 行)の範囲だけ**(SoA の required/derivable/unknown の列と外の状態の `full_items`)。1 ファイル・一時ファイル → 名前の付け替え・先頭の行(版・ラン ID・sha256)と見出しの写しで「自分が書いたものだけを読む」・`finished` で拒否・`parent_run` と `resumed_at_T`・艦隊の未着の呼を同じ call_id で出し直す。再開では日の頭の初期化を**呼ばず**、SoA から作る表だけを `rebuild_derived` で作り直し、戻した直後に full-hash を検算する。
4. **`resume == straight`(mock 5,000 体・世界資産・2 日・毎 tick)**: 既定 v3 は止める時刻 5 点(日中の 7:00・12:30・22:00、日の境目、2 日目の 7:00)、記憶+関係は 12:30 と日の境目、counter ×1000 は 22:00 で、残りの tick の全点の final・behavior-hash・full-hash・tick ごとの呼数・締めの後の 2 つのハッシュと日次センサスの行・テープの prompt_hash が**すべて一致**(§10-8)。
5. 初版で見つけた**保存し忘れ 14 項目**は状態台帳の行と軸を直して吸収した(§10-1)。見つけて直した欠陥: 描画の B3 のキャッシュと classical の c_t の覚え書きの鍵に日が無かった(日を足した・1 日のランは同じバイト)。
6. 残る問い: §10-7 の `--state-out` の追加(実行役の追加)の確認と、§9 の初版の問いのうち答えで閉じなかったもの(7 (b)〜(d) の記録だけ)。

> **§1〜§9 は初版(親の答えの前)の記録**。親の答え(7 件)を反映した変更は §10。食い違うところは §10 と §0 が正。§3 の表は反映後の値に直した。

## 1. 入れたもの

| 場所 | 中身 |
|---|---|
| `engine/run.py` | `run_day` の口 `state_out`・`stop_at_tick`・`resume_from`・`run_id`・`checkpoint_detail`。複数日の制限を「再生だけ止める」に。日の頭の張り直し `_relay_tables`(:3238)と日の頭の書き換え `_start_day`(:3278)、途中の日の締め `_close_day_midrun`(:3334)・台帳の締め `_ledger_close`(:3288・最後の日の締めも同じ関数)、書き出し `_save_state`(:3348)、再開(:3395〜)。艦隊の未着の呼の控え `fleet_inflight`。`RunResult.daily`・`day_heads`・`resume`・`checkpoint_details`。manifest の `resume`・`finished`・`parent_run`・`daily`・`day_heads`(列の追加だけ) |
| `engine/resume.py`(新) | 状態のまとまりの形・書き出し(一時ファイル → `os.replace`・見出しの写しの `.json`)・読み込み(形式の版と台帳の版の検査)・設定の指紋・ラン ID・`EXTRA_ITEMS`(既定は空)と `PROPOSED_EXTRA_ITEMS`(問い 1 の候補 14 項目と理由) |
| `engine/resolve.py` | 戻す書き手 `restore_soa`(:3175)・`restore_items`(:3280)(単一書き手の規律=戻すのも resolve) |
| `engine/state_hashes.py` | `component_digests`(列ごと・外の状態の道筋ごとの digest=食い違いの場所を探す道具の材料) |
| `engine/processes/rail.py` | その日の便を T の座標で末尾に足す `append_day`(:397)・帰無腕の域外居住者の到着便の割り当て直し `_assign_external`(:437)・帰りの便の「日の中の分 → T」の換算(:604) |
| `engine/presence.py` | その日の表の張り直し `relay_day`(:838)・日の頭の書き換え `start_day`(:868)・イベントの表を日の中の分で引く換算(`_run_tick` :1291・`_rearm_after_leaving` :1696・到着便の割り当て) |
| `engine/processes/environment.py` | その日の実日を引き直す `pick_day`(:231) |
| `engine/processes/runner.py` | `end_of_day(…, flush_rail=False)`(途中の日の締めでは最後の便を流さない) |
| `perception/renderer.py` | B3 のキャッシュの鍵に日付(:1673)。**検収後**: B3 の天候はその日の再生の実日で引く(§11 D1) |
| `engine/state_ledger.py` | 除外の一覧に新しい属性(計画実行層の `_kind`・`_agent_key`=定数、`day_index`・`_t0`・`_day_trains`=日の頭で張り直すキャッシュ、鉄道の `_day_starts`・`_t0`=同)。初版では行と軸の判定を変えていなかった。**反映後**(§10-1・§11)は版を `state-ledger/10d` に上げ、行を 187 → 192 に(O90〜O94)・O37・O85・O88 の軸を直した |
| `cli.py` | `build_ledger_bundle(endow=…)`(再開では参入資本を入れない)・`cli.run` は `resume_from` のとき `endow=False` |
| tests | `tests/engine/test_resume_10d.py`(新・§6-1)・`tests/engine/test_sim_time_T.py`(世界資産の複数日を止める行を外した) |
| 記録 `10d/` | 本書・[first_diff.py](first_diff.py)(食い違いの場所を探す道具)・[resume_check_10d.py](resume_check_10d.py)(5,000 体の記録)・記録の JSON(§6・§8) |

## 2. 複数日の通しラン

### 2-1 日の流れ(1 日のランは今のまま)

```
for T in range(始め, 終わり):
    T が日の頭(T % 1 日の tick 数 == 0・T > 0)→ 表の張り直し(_relay_tables)→ 日の頭の書き換え(_start_day)
    …今までの 1 tick(変えていない)…
    checkpoint(既定は 360 tick ごと)
    T がその日の最後の tick で、ランの最後の tick でない → 途中の日の締め(_close_day_midrun)→ state_out があれば書く
ランの最後: 今までの終端の処理(艦隊の吸い切り・runner.end_of_day・台帳の締め・締めの後のハッシュ)→ state_out があれば書く(finished: true)
```

- **日次の締め**(1 日 1 回): `runner.end_of_day`(ActualLog の畳み込み)・台帳の締め(`ledger.end_of_day`)・日次センサス・月次 T3・センサスの書き出し(複数日では `census_out/day-NNNN/`)・締めの後の behavior-hash と full-hash。記録は `RunResult.daily`(日ごと)。
- **途中の日の締めでは鉄道の最後の便を流さない**(`runner.end_of_day(flush_rail=False)`)。今の 1 日のランは締めで `rail.step(T+1)` を呼んで最後の発車(発車 tick 1,439 の便)を流すが、複数日では次の日の頭の tick の `rail.step(1,440)` が同じ便を流す。両方で流すと同じ発車を 2 度処理する。ランの最後の日だけ今までどおり流す。
- **再開ではランの最後の処理をしない**: 止めたランは艦隊を吸い切らず(未着の呼は状態に書く)、日の途中で止めたら締めない。

### 2-2 日の頭の張り直し(`_relay_tables`)

資産・暦・日番号だけから決まる(再開のときも同じ表を作れる)。体の状態は書かない。

1. **鉄道の時刻表**: その日の平日/土休のダイヤ(暦の口)の便を、発車 tick + 日 × 1 日の tick 数(T の座標)で**末尾に足す**。前の日の便の索引は動かさない(乗車中の体の `transit_ref`・帰りの便の予約・待ち行列が便の索引を持つため)。日ごとの便の範囲は `rail.day_range(日)`。帰無腕(計画実行層なし)では域外居住者の到着便をその日の便へ割り当て直す。帰りの便(D-61)の週次表は日の中の分で引いて T に戻す。
2. **計画実行層**: 出勤率の欠席(10a の日番号つきの鍵)・在圏ブロック(W17 の曜日の行)・到着便(その日の便)・イベントの表を作り直す。表は日の中の分で持ち、`_t0`(その日の頭の T)で換算する。
3. **計画境界の表**: W17 は **K9 (a) のつなぎ**(W17 v2 は月曜の行しか無いので、行の無い曜日は月曜の行=宣言)。置き換えた日は manifest の `resume.w17_weekday_substituted_days`。mock 日課は暦の土休。表が前の日と同じなら何もしない。違う日(休日の mock 日課など)で活動層・classical・想起優先の候補合成が立っているランは止める(問い 6)。
4. **天気の実日**: `environment.pick_day(日)`(10a の日番号つきの鍵)。日の出・日の入り・影の面もその日の実日。プロンプトの日付は暦の T から(10a #1)。**注(検収で指摘)**: 既定の世界では再生の実日が影のある 1 日(2026-07-28)に絞られるので、張り直しても**値は変わらない**(毎日 07-28)。
5. (欠陥の修正)描画の B3 のキャッシュの鍵に日付を足した(上の 4 で天気の実日が変わっても、B3 は 0 日目の行を使い回していた。2 日目のプロンプトの天候が 0 日目のままだった)。1 日のランは日付が 1 つなので同じバイト(byte-check)。 **注(検収 D1)**: この直しの後、2 日目のプロンプトの天候は暦の日付(07-29)の行・体の暑さは再生の実日(07-28)の行になり、別の日になっていた。§11 で B3 の天候を再生の実日で引くように直した。

**張り直さないもの(0 日目の表を毎日繰り返す=宣言)**(再確認 N3 で今の実装に合わせて直した。初版はここに営業時間の表と世界過程の日ごとの乱数の表も並べていたが、§10-5 の後はこの 2 つは日ごとに張り直す): 範囲外の食事と自宅の食事の予定(起動時の `table_weekday(0)` の行=既定の暦では月曜の行を毎日=K9 のつなぎ)・計画境界の表の曜日の差(W17 は K9 のつなぎで平日は月曜の行=前の日と同じ表。表が違う日=休日の mock 日課で活動層・classical・想起優先の候補合成が立つランは止める)・古典の事前分布の曜日の種別・関係の初期の辺の曜日(起動時だけ)・エネルギーの計数(累計)。表は §10-5。

### 2-3 日の頭の書き換え(`_start_day`・通しのランだけ)

- 日の頭の初期化(`initialize`・初期の活動・域外の配置・空腹の初期値・初期の財布・参入資本・帳簿の作り直し)は**走らせない**(A11)。位置・活動・在圏・所持金・棚・関係・記憶はすべて持ち越す。
- 計画実行層の「今日の計画」の写しだけを置く: `plan_flags` の「今日の計画がある」ビットと `plan_activity`(0:00 の活動)、日ごとの印 `_pulled_in_today`(今日 civic に引き込まれた)を落とす。位置は動かさない。
- 日の頭のお金と体の数を `RunResult.day_heads` に記録する(試験 v)。

## 3. 日の頭の初期化に頼っていたもの 26 件の振り分け(A11)

元の一覧は [wage-prep §2](../wage-prep.md)(お金 3・物 3・体 7・位置と在圏 4・関係と記憶 4・世界の過程 5)。10d から、複数日の通しランでも再開でも、日の頭の初期化(下の「初期化の場所」)は **0 日目の頭の 1 回だけ**走り、1 日目からは走らない。振り分けは指示の 3 つ:

- **補われる** = 現実の過程で補われる(賃金・在庫の補充・開店など。過程がもうある)
- **宣言** = 補う過程がまだ無いので宣言しておく(複数日では減り続ける・0 日目の表を繰り返す など)
- **張り直し** = 毎日の張り直し(時刻表・計画境界・天気。日の頭で「その日の分」を作る)

パスは `src/shibuya/` を省略。行番号は 10d の作業木。

| # | もの | 初期化の場所 | 10d の扱い(2 日目の頭) | 振り分け | 補う過程/張り直しの場所 |
|---|---|---|---|---|---|
| M1 | 世帯の財布(外界→世帯の入れ直し) | `engine/resolve.py:519-524`・`cli.py:207-257` | 入れ直さない(持ち越す)。再開でも入れない(日の頭の初期化を呼ばない・§10-2) | **宣言**(賃金が未接続=所持金は減る一方。§6-2 の既定 v3・5,000 体では 2 日目に世帯の合計が 131,529,808 → 125,672,948 円=1 体 約 −1,171 円/日(反映後の値)。賃金の段で直す。来街者の持ち込みも未実装) | なし |
| M2 | 店舗の参入資本 | `cli.py:293-295` | 開業時(0 日目の頭)だけ。再開は `build_ledger_bundle(endow=False)` | **補われる**(売上) | `engine/resolve.py` の購入の金の脚 |
| M3 | 帳簿(残高・取引・日の番号) | `cli.py:284-292` | 作り直さない(持ち越す・日ごとに締める) | **補われる**(取引の記録そのもの) | 日の締め `engine/run.py` の `_ledger_close` |
| G1 | 棚の在庫 | `world/state.py:157`・`cli.py:290` | 持ち越す | **補われる**(店員の補充・納品) | `engine/processes/goods_flow.py:216-221`(補充・日の 0 分に「今日の補充済み」を戻す) |
| G2 | 納品の枠(1 店 1 日 1 便) | `engine/processes/goods_flow.py:338` | 納品の時刻と遅れをその日の日の鍵で引き直す(§10) | **補われる**(納品)・**張り直し**(日の鍵の乱数) | `goods_flow.py`(`DeliveryInboundProcess.relay_day`) |
| G3 | 廃棄ビン・世帯の持ち物 | `economy/goods.py`(台帳の新規作成) | 持ち越す | **補われる**(収集・消費) | `goods_flow.py:438-447` |
| B1 | 空腹・疲れ・暑さの値と段 | `engine/resolve.py:526-539` | 持ち越す | **補われる**(食事・睡眠中の疲労の回復・気象の 5 分ごとの更新) | `engine/resolve.py` の `advance_body`・`engine/processes/environment.py` の `step` |
| B2 | エネルギー収支(体重・必要量の抽選) | `engine/resolve.py:1161`(`initialize_energy`) | 持ち越す(体重と必要量は体の定数) | **補われる**(食事) | `engine/resolve.py` の食事の摂取 |
| B3 | 活動(0 時の活動) | `engine/resolve.py:526`・`engine/run.py:2810`(`set_initial_activity`) | 持ち越す | **補われる**(計画境界の起床・就寝) | 計画境界(下の張り直し) |
| B4 | 不応期 | SoA の初期値 | 持ち越す(T で比べる・10a) | **補われる**(時間の経過) | `engine/resolve.py:793` |
| B5 | 会話の状態 | `engine/run.py:2511` | 持ち越す(日の境目の会話も続く) | **補われる**(会話の終了の規則) | `engine/conversation.py` |
| B6 | 種別・年齢・性別 | `engine/resolve.py:513-518` | 体の定数(書き直しではない) | (定数) | なし |
| B7 | 所持品の消費(1 日 1 回) | `goods_flow.py:444` | 日の中の分で毎日 1 回 | **宣言**(1 日 1 回の規則=expedient のまま) | `goods_flow.py:471-492` |
| P1 | 位置(全員を自宅へ) | `engine/resolve.py:506-511` | 持ち越す(自宅へ置き直さない) | **補われる**(計画の帰宅・就寝) | 計画境界・計画実行層 |
| P2 | 在圏(域外の配置・戻る時刻) | `engine/presence.py:1207`(`initialize`) | 置き直さない。戻る時刻(`_extra`・`_skip_depart_at`・帰りの便の予約)は持ち越す | **張り直し**(その日の在圏ブロックとイベント・出勤率の欠席) | `engine/presence.py:838`(`relay_day`)・`:868`(`start_day`) |
| P3 | セルの密度・開いている店の数 | `engine/resolve.py:540` | 状態から毎 tick 計算 | (導出) | `engine/resolve.py:1488` |
| P4 | 列車の在線と乗車率 | `engine/processes/rail.py`(起動時) | 前の日の便は残し、その日の便を T の座標で足す | **張り直し**(時刻表) | `engine/processes/rail.py:397`(`append_day`) |
| R1 | 関係の初期の辺 | `engine/run.py:2952`(`seed_initial`) | 作り直さない(持ち越す) | **補われる**(会話・手伝い・同席の書き手) | `engine/relations.py` |
| R2 | 記憶・店の記憶・なじみ | `engine/run.py:2534`(SoA の確保) | 持ち越す | **補われる**(記憶の書き手) | `engine/memory.py` |
| R3 | 口コミの抽出器 | `engine/run.py:2998`(`WomExtractor.from_world`) | 持ち越す(辞書は定数・計数は累計) | (定数と計数) | なし |
| R4 | 規範の計器などの診断の累計 | 各計器の新規作成 | 累計のまま(日ごとに 0 に戻さない) | **宣言**(診断・日ごとの値が要るなら差で取る) | なし |
| W1 | 営業中の上書き・営業時間の表 | `world/state.py:162`・`engine/processes/opening.py:130` | その日の曜日の行(W7・`table_weekday(日)`)で開閉の表を作り直す(§10) | **補われる**(開店・閉店の過程)・**張り直し**(曜日の行) | `opening.py`(`OpeningProcess.relay_day`) |
| W2 | 道路工事の占有 | `engine/processes/logistics.py:293` | その日の日の鍵で工事の辺を引き直す(塞いでいる辺はその夜の終わりまで)(§10) | **補われる**(夜に始まり朝に終わる過程)・**張り直し** | `logistics.py`(`RoadWorksProcess.relay_day`) |
| W3 | 顕著行為・公共サービスの乱数 | `engine/processes/salient.py:171`・`civic.py:134` | stateful はその日の日の鍵の流れに引き直す・counter は鍵の時刻が日ごとに違うので何もしない(§10) | **張り直し**(日ごとの乱数) | `salient.py`・`civic.py` の `relay_day` |
| W4 | 世界過程の束 | `engine/run.py:2604` | 持ち越す(各過程の状態) | **補われる**(各過程) | `engine/processes/runner.py` |
| W5 | 気象の再生日 | `engine/processes/environment.py`(起動時の `_pick_day(0)`) | その日の実日を日番号つきの鍵で引き直す(既定の世界では影のある 1 日に絞るので値は変わらない・B3 の天候もこの実日で引く=§11 D1) | **張り直し**(天気) | `environment.py:231`(`pick_day`) |

張り直しの全部(`engine/run.py:3242` の `_relay_tables` と `engine/processes/runner.py:394` の `relay_day`): 鉄道の時刻表(P4)・計画実行層(P2)・**計画境界の表**(W17 は K9 (a) のつなぎ=曜日 0 の行で火〜金を引く・mock 日課は暦の土休)・天気の実日(W5)・営業時間の曜日の行(W1)・日ごとの乱数の表(G2・W2・W3・大きな催し)・宅配の配達済み(§10-5)。出勤率の欠席は P2 の中で日番号つきの鍵(10a ◐ #19)で引き直す。

## 4. 書き出しと読み込み

### 4-1 保存の形(`engine/resume.py`)

1 ファイル(`state_out/state-T<次に回す T>.pkl`)に 1 回の `pickle.dump`(プロトコル 5)で次を書く。同じディレクトリの一時ファイルに書いて `fsync` してから `os.replace`(途中で落ちても壊れたファイルを読まない)。見出しの写しを同じ名前の `.json` に置く(人が読む用)。

| 部分 | 中身 |
|---|---|
| `header` | 形式の版 `shibuya.engine.resume/state/v1`・台帳の版・ラン ID・親のラン(`parent_run`)・`finished`・進捗の印(`next_T`・日・日の中の tick・締めた日の数・日の境目で締めた後か・`sim_days`)・設定の指紋・足して保存した道筋(`extra_items`)・環境の欄(Python・numpy・OS・スレッド数)・書いた時点の behavior-hash と full-hash・数(列・道筋・未着の呼・保留の応答) |
| `soa` | agents・cells・pois・知覚の SoA の列のうち、状態台帳の軸 2 が `discardable` でない列(`required`・`derivable`・`unknown`=full-hash と同じ範囲) |
| `items` | 外の状態: 台帳の `full_items`(軸 2 が `required`・`derivable`・`unknown` の行の属性・宣言順)の道筋 → 値。保留の応答(O43・13 要素の組・call_id つき)・艦隊の繰り延べと再生の到着待ち(O44)を含む。腕が立っていない持ち主は「無い」の印 |
| `inflight` | 艦隊へ**出したが返っていない呼**(`LLMCall`=プロンプト・ブロック・call_id) |

- **書く時**: `stop_at_tick` で止めたとき(日の境目なら締めの後・日の途中なら締めずに)・複数日のランの途中の日の締めの後(各日)・ランの最後(`finished: true`)。
- **pickle の注意**: 自分で書いたファイルだけを読む前提(外から来たファイルを読むと任意のコードが動く)。値どうしの同一性(会話の `sessions` と `_of_agent` が同じ `Session` を指す など)を 1 回の dump で保つために選んだ(**未リサーチ(expedient)**)。

### 4-2 読み込み(`run_day(resume_from=…)`)

1. 見出しの検査: 形式の版・台帳の版が今と同じ、`finished: true` でない、設定の指紋(`run_day` の引数のうち挙動に効くもの・観測と出力先と日数と状態の口は除く)が親と同じ、再開の T がこのランの範囲の内側。違えば止める。
2. 起動時の組み立ては通しのランと同じ。**日の頭の初期化の値は一度置くが、ループの前に保存した状態で全部上書きする**(下の注)。お金は台帳を通さない(`initialize(ledger=None)`・`build_ledger_bundle(endow=False)`=財布と参入資本を外界から入れない・台帳の取引にも生ログにも何も書かない)。台帳に取引が 1 件でもあれば止める(参入資本を入れた台帳を渡した呼び手)。
3. 再開の時刻より前に頭が来た日の表を張り直す(便の索引を通しと同じにする)。
4. SoA の列を戻す(`restore_soa`)→ 外の状態を戻す(`restore_items`)。配列・辞書・リスト・集合は**中身を入れ替える**(同じ物を別の持ち主も指している: 金の台帳の世帯の現金の行=`agents.money`・`run_day` の局所のリスト)。辞書は保存の順に入れ直す(挿入順が挙動を決める行 O8・O39)。
5. **戻した直後の full-hash を計算し、保存したときの値と比べる**(違えば止める=戻し忘れ・戻し違いの検出)。
6. 艦隊の未着の呼を同じ `LLMCall`(同じ call_id=艦隊の seed は call_id とランの seed から決まる)で出し直す。

注(実行役の判断・問い 2): 「日の頭の初期化を走らせない」を文字どおり(呼ばない)にすると、起動時に SoA の初期値から作る表が通しのランと違ってしまう。見つけた例: 方策 classical の `employed`(起動時の `bind` が SoA の `kind` を読む。`kind` は `initialize` が入れる)。呼ばない形では classical の 2 日のランで再開が 8 tick 目から食い違った。そこで初期化と同じ値を一度置き、表を作った後で保存した状態で全部上書きする形にした(置いた値は残らない=手順 5 の検査が通る・お金は台帳を通さない)。

### 4-3 ラン ID と親

- ラン ID は `run_day(run_id=…)`、空なら設定の指紋・始めの T・親のラン ID から作る(`run-` + 16 桁)。
- manifest: `resume`(ラン ID・`parent_run`=親のラン ID と再開の T と状態のファイルの名前と full-hash・始めと終わりの T・`finished`・締めた日の数・書いた状態のファイル・K9 で置き換えた日・終わりの未着の呼の数・読み込みと戻すのにかかった秒)、`finished`、`parent_run`。

## 5. 保存の大きさと時間

5,000 体・世界資産・2 日の記録(§6-2)の状態のファイル(1 本・pickle・圧縮なし)。

| 構成 | 止めた T | ファイル | うち SoA の列 | うち外の状態 |
|---|---|---|---|---|
| 既定 v3(`w6_v3_default`) | 420〜1860 | 4.04〜4.38 MB(日の境目 1440 で 4,302,839 B(反映後・先頭の 1 行を含む)=**861 B/体**) | 0.87 MB(174 B/体・61 列) | 3.43 MB(685 B/体・168 道筋) |
| 記憶+関係(`v3_mem_rel`) | 750・1440 | 21.7〜21.9 MB(4.4 KB/体) | 記憶・関係の表が大半 | なし |
| counter・率 ×1000 | 1320 | 4.32 MB | なし | なし |

- 外の状態で大きいもの(既定 v3・1440): 活動層の計画境界の表 `_bt_tick`・`_bt_agent`(各 0.35 MB)・金の台帳の残高 `_lines`(0.27 MB)・計画実行層のイベントの表 `ev_tick`・`ev_arg`・`ev_agent`(各 0.22 MB)・テープの共有ブロックの印 `_interned`(0.19 MB)・在圏ブロック(0.14 MB)。導出できる表(軸 2 が derivable)が外の状態の半分ほどを占める(台帳どおり=full-hash と同じ範囲を書いた)。
- **時間**(この機械・壁時計): 書き出し 0.01 s(書き直しの実測)・読み込み 0.02 s・戻す(表の張り直し+SoA と外の状態+full-hash の検算)0.01〜0.06 s。日に 1 回なので費用は無視できる。
- **39 万体への外挿(推測・線形)**: 既定 v3 は 861 B/体 × 390,067 ≈ **336 MB**、記憶+関係は 4.4 KB/体 ≈ **1.7 GB**。アジェンダ §7 の宣言(既定 137 B/体=53 MB・全腕 5,373 B/体=2.1 GB)のうち既定は**超える**: 宣言は SoA の列だけを数えていて、外の状態(とくに導出できる表)を入れていなかった。導出できる表を保存しないで再開時に作り直せば外の状態は小さくなる(導出できる行の扱いは台帳の軸 2 の約束どおり「保存する」にした=問い 1 と一緒に決めたい)。

## 6. 試験

### 6-1 新しいテスト(`tests/engine/test_resume_10d.py`)

14 関数・パラメータ込み **27 件・全部合格**(この機械で約 9 分。全体のテストは親が回す)。小さいランで回す(合成世界 100 体・世界資産 300 体)。一致の試験は fixture `extra`(問い 1 の 14 項目を足して保存)で回す。

| 試験 | 中身 |
|---|---|
| (i)(ii) `test_synthetic_all_arms_resume_equals_straight_at_every_tick` ×5 | 合成世界・全腕(語彙 v3・記憶・関係・同席・店の記憶・親しみ・エネルギー)・2 日・止める T=420・750・1320・1440・1860。再開の時刻から後の**毎 tick** の final・behavior・full、tick ごとの呼数、日の締めの後の 2 つのハッシュとセンサスの行と体の数、テープの (tick・体・級・prompt_hash)、呼数の合計、`parent_run` |
| (i)(ii) `test_world_resume_equals_straight_at_every_tick` ×5 | 世界資産 300 体・既定 v3・2 日・同じ 5 点・毎 tick・同じ比べ方 |
| `test_world_arms_resume_equals_straight` ×6 | 世界資産で全腕(750)・classical+記憶+関係(1320・2 日目 1860)・帰無腕(750)・v2+edge(1320)・歩いて乗る退出(1080) |
| 問い 1 の固定 ×2 | 台帳どおりの保存(`EXTRA_ITEMS` が空)では、日の境目の再開で 2 日目のセンサスが落ち締めの後の full-hash が違う / 記憶の腕の日中の再開で呼数が違う(台帳を直したら「一致する」に書き換える) |
| (iii) `test_resume_in_a_fresh_process_with_empty_caches` | 再開を別のプロセスで(numba のキャッシュの置き場も空)。毎 tick の 3 つのハッシュが通しと一致 |
| (iv) `test_daily_close_runs_once_per_day` | 合成 3 日: `runner.end_of_day` が 3 回(途中の 2 回は鉄道を流さない・最後だけ流す)・`daily` が 0・1・2 日・`day_heads` が 1・2 日 |
| (iv) `test_two_day_world_run_closes_money_goods_and_bodies_each_day` | 世界資産 2 日: 台帳の締め 2 回・毎日のセンサスの関門(`gate_ok`・`flow_ok`・`ex_nihilo_ok`・`residual_ok`・`goods_balanced`)が合格・体の数(在圏+乗車中+域外=全体・ほかの値 0)・鉄道の便は 2 日目の分が T の座標で末尾に足され発車は便の数と同じ(2 度流さない)・K9 の置き換えが 1 日目・2 日目にも計画実行層の到着と呼がある |
| (v) `test_no_money_is_added_at_the_head_of_day_two_or_on_resume` | 2 日の通しで財布の入れ直し・参入資本・`initialize` が各 1 回だけ(0 日目)。1 日目の終わりのお金=2 日目の頭のお金。再開では財布も参入資本も入れない・再開の始めのお金=止めたランの締めの後・2 日目の終わりのお金が通しと同じ |
| (vi) `test_resume_refuses_finished_mismatched_and_wrong_stops` | `finished: true` への再開・設定の違う再開(seed)・範囲の外の再開(2 日目の状態を 1 日のランで)・`state_out` の無い `stop_at_tick`・範囲の外の `stop_at_tick`・再生との組み合わせ・台帳の版の違うファイルを止める。再開の manifest に親のラン ID と再開の T・`finished` |
| (vi) `test_resume_refuses_a_ledger_that_was_already_endowed` | 参入資本を入れた台帳を再開に渡すと止める(お金の自動補充の禁止) |
| (vii) `test_counter_rng_resume_draws_once` | `--rng-scheme counter`・顕著行為の率 ×1000・合成世界。再開が通しと一致し、顕著行為の事象と出動の数が「止めたラン+再開のラン」=通し(二重に引かない) |
| 艦隊 `test_fleet_inflight_calls_are_reissued_with_the_same_call_id` | 偽 vLLM・24 tick・T=12 で止める。状態に未着の呼が入り(T=11 に発射した呼)、再開で出し直した呼のテープ行は T=11 の call_id のまま。再開の後の毎 tick のハッシュとテープと呼数が通しと一致 |
| `test_state_file_is_one_atomic_bundle` | 1 ファイル+見出しの `.json`・一時ファイルが残らない・見出しの欄・道筋と列の集合が台帳(+足した道筋)と同じ・バイト数と full-hash が記録と同じ |

既存のテストで直したもの: `tests/engine/test_sim_time_T.py::test_multi_day_mouth_refuses_what_needs_the_day_head` の「世界資産の複数日を止める」行を外した(10d で通すようにしたため)。回帰の組(`test_sim_time_T`・`test_10a_review_fixes`・`test_rng_scheme_10c`・`test_calendar_sites`・`test_response_delay`・`test_state_ledger_10b`(網羅と AST の検査を含む)・`test_classical_social`(classical 1,500 体の golden)・`test_cli`・`test_manifest_roundtrip`・`test_census_out`・`test_ledger_wiring`・`test_presence_executor`・`test_presence_exit_walk`・`test_fleet_wiring`・`test_tape_deferred`・`test_tape_wiring`・`test_determinism_t1_t2_t4`・`tests/economy`・`tests/engine/processes`・`tests/perception`・`test_renderer_wiring`・`test_two_phase`・`test_memory_record`・`test_relations_8b`・`test_meal_bundle_2b`・`test_two_layer_activity`)は合格。`test_state_ledger_10b.py::test_t2_call_id_on_the_fleet_and_replay_paths` は、5,000 体のランを 3 本並べて CPU が詰まっていたときに 1 回だけ落ち(呼び手の行の判定が「?」)、単独で回し直すと合格した(偽 vLLM の到着の時刻に依る試験=負荷で揺れる・10d の変更とは別。記録だけ)。

### 6-2 5,000 体の記録([resume_check_10d.py](resume_check_10d.py))

mock 5,000 体・seed 1・世界資産(`data/world/v2`)・2 日・`cli.run`。通しのランと、止める時刻ごとの「止めたラン → 状態のファイル → 再開のラン」を**別々のプロセス**で回し、`first_diff.compare` で再開の時刻から後を比べた。checkpoint は **毎 tick**(`checkpoint_every=1`)=「残りの tick の全点」。足して保存する 14 項目(問い 1)は on(`--extra`)。

| 構成 | 止めた T | 比べた checkpoint(=残りの tick) | 食い違い | tick ごとの呼数 | 締めの後の 2 つのハッシュとセンサスの行 | テープの呼(prompt_hash) | 呼数の合計(通し / 止め+再開) |
|---|---|---|---|---|---|---|---|
| 既定 v3 | 420(7:00) | 2,460 | **0** | 一致 | 0・1 日目 一致 | 140,643 行 一致 | 142,578 / 142,578 |
| 既定 v3 | 750(12:30)・別プロセス+空の numba キャッシュ | 2,130 | **0** | 一致 | 0・1 日目 一致 | 111,670 行 一致 | 同上 |
| 既定 v3 | 1320(22:00) | 1,560 | **0** | 一致 | 0・1 日目 一致 | 75,999 行 一致 | 同上 |
| 既定 v3 | 1440(日の境目)・別プロセス+空の numba キャッシュ | 1,440 | **0** | 一致 | 1 日目 一致 | 72,600 行 一致 | 同上 |
| 既定 v3 | 1860(2 日目 7:00) | 1,020 | **0** | 一致 | 1 日目 一致 | 66,511 行 一致 | 同上 |
| 記憶+関係 | 750 | 2,130 | **0** | 一致 | 一致 | 116,217 行 一致 | 148,455 / 148,455 |
| 記憶+関係 | 1440 | 1,440 | **0** | 一致 | 一致 | 75,525 行 一致 | 同上 |
| counter・率 ×1000 | 1320 | 1,560 | **0** | 一致 | 一致 | 103,423 行 一致 | 196,956 / 196,956 |

記録: 初版の JSON(足して保存した値)は反映の後の記録(§10-8 の 3 本)で置き換えた。

**台帳どおりの保存(`--extra` なし)の対照**(初版の記録・JSON は置いていない・checkpoint は 60 tick ごと+列ごとの digest): 記憶+関係は 750 で止めると T=764 から呼数が食い違い(呼数の合計 148,909 ≠ 148,455)、1440 で止めると 1 日目のセンサスが落ちる(`census_pass` 通し True → 再開 False・`flow_ok`)。道具が出す最初の食い違いの列は記憶の表(`mem_*`)と活動の列で、**根(`conv.n_opened`・金の台帳の `_snap`)は台帳の範囲の外なので digest に出ない**(食い違いの場所を探す道具の限界=台帳に載っていない状態は「結果の列」しか指せない)。

そのほかの構成(世界資産 300 体・2 日・止める T=420・750・1320・1440・1860・60 tick ごと): 既定 v1・既定 v3・全腕・classical+記憶+関係・帰無腕(計画実行層なし=鉄道の域外居住者の便の割り当て直しの道)・v1+edge・v2+edge(注意)・counter ×1000・歩いて乗る退出の 9 構成 × 5 点が全部一致(`--extra` あり・実行役の scratch での確認=記録の JSON は置いていない。テストに同じ形の 11 件を入れた)。

**通しの 2 日の値**(既定 v3・5,000 体): 締めは 0・1 日目の 2 回・センサスの関門は 2 日とも合格。体の数は 1 日目の終わり 在圏 977+乗車中 6+域外 4,017=5,000、2 日目の終わり 938+0+4,062=5,000。2 日目の頭のお金=1 日目の終わり(世帯 131,529,808 円・貨幣供給量 425,192,358 円)。

## 7. 食い違いの場所を探す道具([first_diff.py](first_diff.py))

- `dump(res, path, tape=…)` で `run_day`/`cli.run` の結果を JSON に落とし、`python first_diff.py compare --straight S.json --segments A.json B.json` で通しと「止めたラン+再開のラン」を比べる。
- 出すもの: 比べた checkpoint の数・食い違った数・**最初に食い違う tick** と、その tick で値の違う SoA の列と外の状態の道筋(状態台帳の行の鍵・名前・軸 1・軸 2 つき。`run_day(checkpoint_detail=True)` のとき)・tick ごとの呼数の最初の食い違い・足りない tick・日の締めの後の 2 つのハッシュと日次センサスの行の違う欄・テープの呼ごとの prompt_hash の違う数と最初の呼。
- 5,000 体の記録は `resume_check_10d.py run`(内部でこの道具を使う)。使用例は §6-2 と各スクリプトの冒頭。

## 8. byte-check

- 手順は 10c と同じ: HEAD `8486f9c` を `git archive HEAD src docs/bench/anchors docs/design/v2-budget-declaration.md docs/bench/analysis/w6-regen-2026-09-28` で短いパスの作業用ディレクトリへ展開した写しと、**最終のコード**の作業木で、19 構成を mock/classical 5,000 体・seed 1・1 シミュ日・テープつきで回し(`10c/byte_check_10c.py side`)、`10b/byte_check_10b.py compare` で比べた。
- 結果: **19/19 一致**(final・呼数・blocks・calls の 14 列)・`src_checks` ok([byte_check.json](byte_check.json))。

| 構成 | final | 呼数 |
|---|---|---|
| w6_v3_default(golden v3) | 993276d5e5bb5cbe | 69,978 |
| w6_golden_null_arm(帰無) | 72cb9cd52982da74 | 100,439 |
| v3_mem_rel(関係 on) | 40409ebed834126b | 72,930 |
| v3_classical | 3390e3ec02d392a9 | 97,563 |
| ほか 15 構成 | [byte_check.json](byte_check.json) | |

- classical 1,500 体の golden(`4f78f3c0`/25,808)は既存のテスト `tests/engine/test_classical_social.py` で一致。
- 10b の状態台帳の網羅の検査(AST と実行時)と AST の読み手の検査は合格(`tests/engine/test_state_ledger_10b.py` 全件)。新しい属性は除外の一覧に理由つきで足した(§1)。

```
D=docs/bench/analysis/wallbounce-1003
python $D/10c/byte_check_10c.py side --src <写しの src> --label head --scratch <作業用> --out <作業用>/head.json --jobs 4
python $D/10c/byte_check_10c.py side --label work --scratch <作業用> --out <作業用>/work.json --jobs 4
python $D/10b/byte_check_10b.py compare --head <作業用>/head.json --work <作業用>/work.json --head-label 8486f9c --out $D/10d/byte_check.json
```

## 9. 見つけた問い(止めたもの)

1. **保存の範囲(状態台帳の軸 2 の判定)**。指示どおり「SoA の required/derivable(+unknown)の列と外の状態の `full_items`」だけを保存すると、日中の 3 点の試験と日の境目の再開で通しと食い違う。保存し忘れていたのは台帳の軸 2 が `discardable` の次の項目(`engine/resume.py` の `PROPOSED_EXTRA_ITEMS` に理由つきで並べた・**台帳には足していない**)。
   - (a) 金の台帳の `_snap`(O58): 次の日の締めの `d_cash`(締め `_last_close`=O77 required・日次センサスの検算①)の基準。無いと**日の境目で再開した日のセンサスが落ちる**(`census_pass` 通し True → 再開 False)・締めの後の full-hash が違う。
   - (b) 生ログと配達ログの位置(金 `_raw_pos`・`_raw_head`・`_day_marks`・`n_raw_dropped`、物 `_dl_pos`・`_dl_head`・`_dl_marks`・`n_delivery_dropped`=O58・O60): 締めの `raw_rows_kept`・`delivery_rows_kept` が `_last_close`(required)に入る。**位置は全部か何も無しかで戻す**(一部だけ戻すと成長の検査が「実測が負」で止まった)。リングの中身は戻していない(K16 の既定案のまま)。
   - (c) `conv.n_opened`(O41・diag の計数・discardable): **記憶の層が「開いた会話の数」として読む**(`engine/memory.py:713` の `_next_session` との比較)=挙動に効く。無いと記憶の腕の日中の再開で呼数が食い違う(5,000 体の記録 §6-2・テスト)。正しくは軸 1 も behavior。
   - (d) `presence._pulled_in_today`(O37・behavior・discardable): 日の途中で止めると、その日の残りの behavior-hash が違う(10b §11-4 の親の答え「behavior-hash に入れたまま・full に入らない」の帰結)。読み手は計数の内訳だけ(`presence.py` の `_do_arrive`)なので軸 1 の判定(behavior)の方が誤りかもしれない。
   - (e) `ledger.money.n_transfers`(O78): 日次センサスの行の `n_transfers`(累計)が再開で 0 から数え直しになる(診断だけ)。`_flow_daily`(O58): 2 日では一致に要らなかったが、月次 T3 と `cumulative_close` が読む日次の履歴。
   - (f) `classical._ipf_cache`(O22「キャッシュ」): 15 分帯ごとの c_t を**最初に引いたときの状態**から作って使い回す覚え書き(作り直すと別の値)。既定の乗数(全部 1)では使わないので食い違いは観測していない。
   - 選択肢: (A) 台帳を直す(上の項目の軸 2 を required に・`n_opened` は軸 1 も behavior に・版を上げる。full-hash の値は全構成で変わる。`n_opened` を behavior に入れると behavior-hash も全構成で変わり、10b で記録した 10e 用の値と一致しなくなる)/(B) 台帳はそのまま、再開の時だけ足して保存する一覧として持つ(今の `EXTRA_ITEMS` の口を既定で on にする)/(C) (a)(b)(e) は K16(リングの保存)と一緒に決め、(c)(d)(f) だけ先に直す。実行役の案は (A)(再開の判定の full-hash と保存の範囲が一致するのは A だけ)。
2. **再開の初期化の扱い**(実行役の判断・§4-2 の注): 「日の頭の初期化を走らせない」を「初期化と同じ値を一度置き、起動時の表を作った後、保存した状態で全部上書きする(お金は台帳を通さない)」と読んだ。文字どおり呼ばない形では classical の `employed`(起動時に SoA の `kind` を読む)などが通しと違う表になった。置いた値が残らないことは、戻した直後の full-hash の検算で毎回確かめている。この読みでよいか。
3. **テープの共有ブロックの印 `bridge._interned`(O85・unknown)**: full-hash に入るので、通しのランと再開のランでテープを書く/書かないがそろっていないと full-hash が違う(テストで実際に踏んだ)。再開のランは印を親から引き継ぐので、**再開のテープには親が書いたブロックの行が無い**(親のテープと合わせて初めてプロンプトが組み直せる)。再生(replay)は 10d の範囲の外にした。テープを鎖で読む形にするか、再開のテープに必要なブロックを書き直すか、O85 を full-hash から外すか。
4. **日の鍵の無いキャッシュ**: B3(時刻・天候)のキャッシュの鍵が 5 分帯だけで、複数日のランで 0 日目の天候を 2 日目も使っていた。これは §2-6 の「検証で見つけた欠陥の修正」として直した(鍵に日付・1 日のランは同じバイト・byte-check で確認)。同じ形の `classical._ipf_cache`(帯ごとの c_t を日をまたいで使い回す)は**直していない**(既定の乗数では使われない・直すと乗数を変えた classical の複数日の結果が動く)。日ごとに作り直すか。
5. **張り直さない日ごとの表**(0 日目の表を毎日繰り返す=宣言): 営業時間の表(W7 の曜日の行)・世界過程の日ごとの乱数の表(入荷の時刻・工事・配達・大きな催し=`day_key(0)`)・範囲外と自宅の食事の予定・古典の事前分布の曜日の種別・エネルギーの計数(O28 の「日の締めで 0 に戻す」は入れていない=累計のまま)。指示の張り直しの一覧(時刻表・計画境界・天気・出勤率)の外なので入れなかった。日ごとに引き直すか(引き直すと 2 日目の結果が動く・1 日のランは動かない)。
6. **曜日で計画境界の表が変わる日**(休日の mock 日課・W17 の別の曜日の行): 活動層・classical・想起優先の候補合成は起動時に表を写して持つので、表が前の日と違う日が来たら止める(`NotImplementedError`)。K9 のつなぎ(平日は月曜の行)と既定の暦(day_index 0 から平日)では起きない。張り直しの口を足すか。
7. **そのほか(記録だけ)**: (a) 状態の口の CLI の切替口(`--state-out`・`--resume-from`・`--stop-at-tick`・`--sim-days`)は足していない(指示は `run_day` の口)。(b) 複数日の `census_out` は `day-NNNN/` に日ごとに書く。(c) manifest に足した `daily`・`resume` は seed で値が変わる欄なので、seed の交換可能性の道具(`tools/c7`)では「未説明」に出る(10a の `replay_date` と同じ扱い=10f)。(d) 状態のファイルは pickle(自分で書いたファイルだけを読む)。

## 10. 親の答えの反映(7 件)

### 10-1 答え 1: 保存の範囲=台帳を直す

再開の時だけ足す一覧(初版の `EXTRA_ITEMS`・`PROPOSED_EXTRA_ITEMS`)は消し、14 項目を状態台帳に吸収した。台帳の版は `state-ledger/10d`(行 187 → **191**・外の状態 89 → 93)。full-hash は全構成で値が変わる(新しい道筋が入る)。behavior-hash も全構成で変わる(`conv.n_opened`・`classical._ipf_cache` を軸 1 behavior の行に入れたため)。final(今の `combined`)は変わらない。

| 道筋 | 前(行・軸 1・軸 2) | 後(行・軸 1・軸 2) | 理由 |
|---|---|---|---|
| `presence._pulled_in_today` | O37・behavior・discardable | O37・behavior・**required** | 日の頭で落とす日ごとの印。日の途中の再開で要る |
| `classical._ipf_cache` | O22・no・discardable | **O90**・**behavior**・**required** | 帯ごとに最初に引いた時の状態から作る覚え書き(作り直すと別の値)。鍵に日を足した(10-4) |
| `conv.n_opened` | O41・diag・discardable | **O91**・**behavior**・**required** | 記憶の層が `_next_session` と比べて読む(`engine/memory.py:713`)=挙動に効く |
| `ledger.money._snap`・`_flow_daily`・`_raw_pos`・`_raw_head`・`_day_marks`・`n_raw_dropped` | O58・no・discardable | **O92**・diag・**required** | `_snap`=次の日の締めの `d_cash`(センサスの検算①)の基準、`_flow_daily`=月次 T3 の日ごとの履歴、位置=締めの `raw_rows_kept` |
| `ledger.money.n_transfers` | O78・diag・discardable | **O92**・diag・**required** | 日次センサスの行の累計 |
| `ledger.goods._dl_pos`・`_dl_head`・`_dl_marks`・`n_delivery_dropped` | O60・no・discardable | **O93**・diag・**required** | 締めの `delivery_rows_kept` |
| `bridge._interned`・`fleet_bridge._interned` | O85・O88・no・unknown | O85・O88・no・**required** | 答え 3 |

- **K16 の既定案の修正**: 「リング(金の生ログ・配達ログ)は状態に含めない」を「**中身**は含めない(O58・O60 は discardable のまま)が、**位置**(`_raw_pos`・`_raw_head`・`_day_marks`・`n_raw_dropped`・`_dl_*` の位置)は要る」に直した。位置は全部まとめて戻す(初版の切り分けで、一部だけ戻すと成長の検査で「実測が負」になって止まった)。再開したランの生ログは再開の後の取引から始まる(位置の数え方は通しと同じ)。
- **AST の検査の穴**: 10b の AST の検査は **SoA の列の読み手だけ**を見る。外の状態の属性(`conv.n_opened` を `getattr(conv, "n_opened", 0)` で読む記憶の層など)の読み手は検出しない。軸 1 を behavior に直したが、AST の検査は「読み手あり」とは言わない(言う仕組みが無い)。外の状態の軸 1 は手の判定のまま=検査の穴として記録する。 検収で見つけたもう 1 つの具体例: `poi_resolver.named_closed`(名指しの店の即時閉店の控え。描画の B6 がプロンプトに 1 句足す=挙動に効くのに O26 の計数・discardable だった=§11 L2 で O94 に)。

### 10-2 答え 2: 再開の初期化を呼ばない・導出の表を作り直す

- 再開では日の頭の初期化(`R.initialize`・`R.initialize_energy`・`R.set_initial_activity`・`presence.initialize`(域外の配置)・世界過程の起動時の域外の配置・関係の初期の辺・財布・参入資本)を**呼ばない**(`engine/run.py:2564` ほか)。
- 起動時に **SoA の値から**作る表は、戻した SoA から決定的に作り直す口 `_rebuild_derived`(`engine/run.py:3388`)で作り直す: 方策 classical の `employed`(`ClassicalPolicy.rebuild_derived`・`engine/classical.py:398`=体の種別から)と、開閉の過程の担当従業者 `staff_of_poi`(`OpeningProcess.rebuild_derived`・`engine/processes/opening.py:172`=補充の過程が同じ配列を持つので中身を書き換える)。どちらも台帳の除外の一覧のキャッシュ(導出)に「SoA の kind から作る=再開では rebuild_derived で作り直す」と理由を書いた(行ではなく除外の一覧に載っている表=保存しない)。計画実行層の配置の数の控えは `PlanExecutor.initialize_caches`(体を動かさない)。
- 起動時に SoA から作る表は grep で探した(起動時に `kind` を読むのはこの 2 つ。ほかの過程は step の中で読む)。漏れは再開の試験で見る(§10-8 で 0 件)。
- 戻した直後の full-hash の検算は残した(保存したときの値と違えば止める)。
- 順: 再開の時刻より前に頭が来た日の表の張り直し → SoA を戻す → `_rebuild_derived` → 外の状態を戻す → full-hash の検算 → 艦隊の未着の呼の出し直し。

### 10-3 答え 3: テープの共有ブロックの印

- `bridge._interned`(O85)・`fleet_bridge._interned`(O88)は軸 1 no・軸 2 required(記録の継続に要る)。
- **再開したランのテープは新しい block だけを持つ**(親のテープに書いた block の行は書かない)。manifest の `parent_run`(親のラン ID・再開の T・状態のファイル)が親を指すので、読み手は親のテープと連結して読む(鎖の先頭までたどる)。再生(replay)は 10d の範囲の外のまま。
- 試験の前提: O85 が full-hash に入るので、比べる 2 本は「両方ともテープを書く」か「両方とも書かない」でそろえる(テストの冒頭と `resume_check_10d.py` の冒頭に書いた。5,000 体の記録は全部のランがテープを書く)。

### 10-4 答え 4: `classical._ipf_cache` の鍵

鍵は 15 分帯だけだった(日が入っていない)。B3 のキャッシュと同じ直しで鍵を `(日, 帯)` にした(`engine/classical.py:526`・日=T ÷ 1 日の tick 数)。1 日のランは日 0 だけ=同じ値(byte-check の classical の腕と classical 1,500 体の golden で確認)。テスト: 乗数を 1 でなくした classical の 2 日のランで、覚え書きの鍵の日が 0 と 1 の両方になる。

### 10-5 答え 5: 日ごとの表

日の頭の張り直しを `WorldProcessRunner.relay_day`(`engine/processes/runner.py:394`)にまとめた。日の鍵は暦の口の `day_key(日)`(`day_index` モードでは day_index+日・`real` では日番号)、曜日の行は `table_weekday(日)`(`real` では実曜日)。

| 表 | 2 日目からの扱い | 場所 |
|---|---|---|
| 鉄道の時刻表 | **張り直す**(その日の平日/土休のダイヤを T の座標で末尾に足す) | `rail.py` `append_day` |
| 天気の実日 | **張り直す**(日番号つきの鍵)。ただし既定の世界では影のある 1 日に絞るので値は変わらない(検収) | `environment.py` `pick_day` |
| 営業時間(W7 の曜日の行) | **張り直す**(`table_weekday(日)`) | `opening.py` `relay_day` |
| 納品の時刻と遅れ | **張り直す**(`day_key(日)` の乱数) | `goods_flow.py` `relay_day` |
| 道路工事の辺 | **張り直す**(`day_key(日)`・塞いでいる辺はその夜の終わりまで) | `logistics.py` `RoadWorksProcess.relay_day` |
| 大きな催しの会場 | **張り直す**(`day_key(日)`・会場に居る体はそのまま) | `civic.py` `LargeEventProcess.relay_day` |
| 顕著行為と出動の乱数 | **張り直す**(stateful はその日の `day_key(日)` の流れ。counter は鍵の時刻が日ごとに違う値なので何もしない) | `salient.py`・`civic.py` の `relay_day` |
| 宅配の配達済み | **張り直す**(日の頭で 0。予定個数は乱数を使わない「その日の予定」) | `logistics.py` `LastMileProcess.relay_day` |
| 計画実行層(在圏ブロック・イベント・出勤率) | **張り直す**(W17 は K9 のつなぎ=月曜の行・出勤率は日番号つきの鍵) | `presence.py` `relay_day` |
| 計画境界の表 | K9 のつなぎ(平日は月曜の行=宣言)。表が前の日と同じなら何もしない | `run.py` `_relay_tables` |
| 範囲外の食事と自宅の食事の予定 | **張り直さない**(K9 のつなぎ=月曜の行を毎日=宣言) | `energy.py`(日の中の tick で引く) |
| 古典の事前分布の曜日の種別・関係の初期の辺の曜日 | **張り直さない**(0 日目の値=宣言。指示の一覧の外) | `classical.py`・`relations.py` |
| エネルギーの計数(O28) | 日ごとに 0 に戻さない(累計=宣言・診断だけ) | `energy.py` |

1 日のランは張り直しを通らない(日の頭は 1 日目から)=不変。2 日のランの 2 日目の値は動いた(例: 既定 v3・5,000 体の 2 日の通しの呼数 142,578 → 142,043・final `b90c7a3a…` → `47e0a85b…`。10d の初版との比べ=予定どおりの変化)。

### 10-6 答え 6

`NotImplementedError` の文言を「張り直しは K9 の解消まで入れていない(K9 のつなぎ=平日は月曜の行の間は通らない)」にした。

### 10-7 答え 7: CLI・manifest・読み口の検査

- 切替口 `--sim-days N`・`--resume-from <path>` を `engine.run.add_calendar_args`(`engine.run` と `shibuya.cli` の両方が使う 1 か所)に足した。**実行役の追加(親の確認がほしい)**: `--resume-from` に渡す状態のファイルを CLI で作れるよう、書き出し先 `--state-out <dir>` も同じ所に足した(無いと CLI からは状態を作れない)。既定のときは `run_day` の引数に何も足さない(既定の引数は今のまま)。
- manifest に `resumed_at_T`(再開の T・再開でなければ null)を足した。`sim_days`・`parent_run` は前から出る。
- **読み口の検査**(`engine/resume.py` の `read_state`): ファイルの先頭の 1 行に印 `SHIBUYA-STATE`・形式の版・ラン ID・中身の sha256・中身のバイト数を書き、pickle を開く**前**に (1) 印と版 (2) 中身のバイト数と sha256 (3) 見出しの写し(`.json`)があり、そのラン ID が先頭の行と同じ、を確かめる。開いた後に見出しのラン ID と full-hash が写しと同じか・台帳の版が同じかを確かめる。どれか違えば止める。再開したランの `parent_run` はこのラン ID になる。
- **10f の項**: 状態のファイルの形式の見直し(pickle → npz+json。値どうしの同一性の保ち方を含む)。
- **10e の予算の再宣言の材料**: §5 の数値(既定 v3 で 861 B/体・39 万体で約 336 MB=宣言の 53 MB を超える・記憶+関係で約 1.7 GB)をそのまま残す。

### 10-8 反映後の試験と記録

- **テスト**: `tests/engine/test_resume_10d.py` は 19 関数・パラメータ込み **32 件**(初版の 27 件から、台帳どおりの保存で食い違うことを固定した 2 件を「台帳を直した後は一致する」2 件に書き換え、5 件を足した: 台帳の行の移し替え・自分が書いたものだけを読む・CLI の切替口と manifest・日ごとの表の張り直し・`_ipf_cache` の鍵の日)。`tests/engine/test_state_ledger_10b.py` の行の数の試験を 191 行に直した。結果は §10-9。
- **5,000 体の記録**(反映後のコード・毎 tick・別々のプロセス・全部のランがテープを書く): 既定 v3 は止める T=420・750(キャッシュ空の別プロセス)・1320・1440(日の境目・キャッシュ空)・1860 の 5 点すべて、記憶+関係は 750・1440、counter ×1000 は 1320 で、残りの tick の全点の final・behavior・full・tick ごとの呼数・締めの後の 2 つのハッシュとセンサスの行・テープの prompt_hash が通しと**一致**([resume_check_v3_default_5000.json](resume_check_v3_default_5000.json)・[resume_check_v3_mem_rel_5000.json](resume_check_v3_mem_rel_5000.json)・[resume_check_v3_counter_x1000_5000.json](resume_check_v3_counter_x1000_5000.json))。§6-2 の表は初版(足して保存した)の値で、置き換わった(呼数の合計: 既定 v3 142,043・記憶+関係 148,347・counter 197,659。止め+再開も同じ)。状態のファイルは既定 v3 で 4.04〜4.38 MB(先頭の 1 行が増えただけ)。
- **byte-check**(反映後のコード・既定 v3・帰無・relations-on): `993276d5e5bb5cbe`/69,978・`72cb9cd52982da74`/100,439・`40409ebed834126b`/72,930 で 14 列が **3/3 一致**([byte_check_after_answers.json](byte_check_after_answers.json))。

### 10-9 反映後のテストの結果

反映後のコードで `tests/engine/test_resume_10d.py`(32 件)・`tests/engine/test_state_ledger_10b.py`(70 件・台帳の網羅の検査と AST の検査を含む)・`test_sim_time_T`・`tests/engine/processes`・`test_calendar_sites`・`test_classical_social`(classical 1,500 体の golden)・`test_classical_policy`・`test_10a_review_fixes`・`test_presence_executor`・`test_ledger_wiring`・`test_census_out` を回し、**全部合格**(約 400 件・終了コード 0)。全体のテストは親が回す。

## 11. 検収後の直し([review-10d.md](../review-10d.md)・親の答え Q1〜Q4)

検収の結果: resume == straight は検収役の独立のランでも 2,880 点で一致・結果を動かす欠陥 1・潜在 6・記録の誤り 5・テストの欠け 5・問い 4。全部を次のように直した。

| # | 指摘 | 直し | テスト(`tests/engine/test_resume_10d.py`) |
|---|---|---|---|
| D1 | 2 日目から B3 の天候(暦の日付の W13 の行)と環境の過程の天候・暑さ(再生の実日の行)が別の日 | 親の答え (a): B3 の天候を「その日の再生の実日」(`environment.replay_date`=体の暑さと同じ源)で引く。描画に口 `weather_date_fn` を足し(`perception/renderer.py`)、`engine.run` が世界過程の再生の実日を差し込む。日付と曜日の語は暦のまま(**日付は暦・天候は実日=K7 のつなぎ**として宣言)。キャッシュの鍵は (天候の日, 5 分帯)。合成世界(実日なし)は今までどおり暦の日付。1 日のランは再生の実日=暦の開始日なので不変(byte-check)。`--start-date` で開始日を実日と違う日にしたランでは、B3 の天候も実日の行になる(今までは暦の日付の行) | `test_b3_weather_and_the_environment_read_the_same_day_on_day_two`(2 日目の 12 時台の B3 の天候の語が再生の実日の 12 時の W13 の行・環境の過程の行も同じ実日) |
| L1 | 再開の最初の tick の診断の行の `conversations_opened` が累計 | 差分の基準(`prev_sessions`・`prev_tape_misses`)を戻した状態(`conv.n_opened`・`bridge.n_tape_misses`)から置く(`engine/run.py:3433`)。診断の行に累計の列は無い | 一致の試験はすべて診断の行の**全列**を比べる(`_diag`)。`first_diff.py` も全列(`diag_by_tick`・`first_diag_mismatch`) |
| L2 | `poi_resolver.named_closed`(名指しの店の即時閉店の控え)を保存しない(B6 のプロンプトに効く) | O26 から外して **O94**(behavior・required)にした | `test_named_closed_memo_survives_a_resume`(控えを入れてから T=600 で止めて戻す。保存に控えがあり、再開の後の全 tick の 3 つのハッシュとテープが通しと同じ) |
| L3 | 指紋にパスの文字列(`world_dir`・世界の `source`・`holiday_csv`)が入る(置き場所・OS で再開を拒む・見出しにユーザー名) | 指紋はパスの文字列を入れず中身で同定: ファイル=sha256、ディレクトリ=`build_manifest.json` の sha256(無ければ直下のファイルの名前と大きさの一覧の sha256)。世界の同定はセル数と POI 数+`world_dir` の中身(`engine/resume.py` の `path_identity`)。見出しに絶対パスが入らない | `test_fingerprint_and_header_have_no_paths_and_run_ids_are_unique`(相対と絶対で同じ指紋・見出しの写しに作業ディレクトリとホームのパスが無い・相対で書いた状態を絶対パスの設定で再開できる) |
| L4 | `staff_of_poi` の作り直しを外しても捕まるテストが無い | 合成世界で比べるテストを足した(W16 の母集団には種別「従業者」が居ないので、世界資産のランでは表が全部 −1=比べても意味が無い) | `test_resume_rebuilds_the_staff_table_shared_with_restocking`(再開の後の表が通しと同じ・補充の過程と同じ配列) |
| L5 | O37 `_pulled_in_today` の軸 1 が behavior(読み手は計数だけ) | 親の答え: 軸 1 を **diag** に。behavior-hash は全構成で値が変わる(下) | `test_ledger_rows_moved_by_10d` |
| L6 | ラン ID が実行ごとに一意でない | ラン ID に実行の時刻とプロセス番号の印を混ぜた(`run_id_of`)。**再開の鎖は `parent_run` の (親のラン ID・再開の T・保存の full-hash) の組で引く**。状態の口を使わないランではラン ID を作らない(空)=manifest は決定論のまま(同じ設定の 2 回のランの manifest が一致する既存の約束・`tests/engine/test_census_out.py`) | 上の L3 の試験(同じ設定の 2 回でラン ID が違う・親の組が manifest に出る) |
| T5 | 日の境目で艦隊の未着の呼がある形の試験が無い | 足した(偽 vLLM・合成 2 日・体 0〜4 に 23:59 の計画境界を足して T=1439 に呼を出し、T=1440 で止める) | `test_fleet_inflight_calls_at_the_day_boundary`(状態に未着の呼・日の締めの後・再開の後の 3 つのハッシュとテープと呼数が通しと同じ・出し直した呼は T=1439 の call_id) |

記録の誤り 5 件(review §5)は直した: §2-2 の 4・§3 の W5・§10-5 の「天気の実日を張り直す」に「既定の世界では値が変わらない」を足し、§2-2 の 5 に D1 の注を足した / §3 の M1 を反映後の文言と値(131,529,808 → 125,672,948 円=1 体 約 −1,171 円/日)に / §5 のバイト数を反映後の 4,302,839 B に(検収後は先頭の行が長くなり 4,302,954 B) / §1 の表の `state_ledger.py` の行を反映後に / §10-1 の AST の検査の穴の具体例に `named_closed` を足した。

問いへの答え: Q1=D1 の (a)。Q2=L5 の diag。Q3=L3・L6。Q4=pickle は「自分が書いたものだけを読む」運用の約束のまま(10f の npz+json で解消・§10-7 に記録済み)。

### 11-1 台帳(`state-ledger/10d`・192 行)

10d の反映で 191 行 → 検収後 **192 行**(O94 を足した)。O37 の軸 1 を behavior → diag。full-hash と behavior-hash は全構成で値が変わる(final は不変)。

**新しい behavior-hash**(1 日・mock 5,000 体・seed 1・最後の checkpoint・先頭 16 桁。[byte_check_after_review.json](byte_check_after_review.json) の作業木の値): 既定 v3 `b3ccfa6797f2c418`・帰無 `aa2a2b3818f33362`・relations-on `2817c8ed4bc17c88`。full-hash は既定 v3 `fa168793db2b6433`・帰無 `c38b7abc37211bd6`・relations-on `165666b6c42034f3`。10e で比べるのはこの値(10b §11-5 の値は置き換わった)。

### 11-2 byte-check と resume == straight(検収後のコード)

- **byte-check**: 既定 v3 `993276d5e5bb5cbe`/69,978・帰無 `72cb9cd52982da74`/100,439・relations-on `40409ebed834126b`/72,930 で final・呼数・blocks・calls の 14 列が **3/3 一致**([byte_check_after_review.json](byte_check_after_review.json))。
- **resume == straight**(mock 5,000 体・世界資産・2 日・既定 v3・毎 tick・別々のプロセス・全部のランがテープを書く): 止める T=420(7:00)・750(12:30・キャッシュ空の別プロセス)・1320(22:00)・1440(日の境目・キャッシュ空)・1860(2 日目 7:00)の 5 点すべてで、残りの tick の全点の final・behavior・full・**診断の行の全列**・締めの後の 2 つのハッシュとセンサスの行・テープの prompt_hash が一致([resume_check_v3_default_5000.json](resume_check_v3_default_5000.json) を検収後の値に置き換えた)。2 日の通しの final `47e0a85b02797e23`・呼数 142,043 は検収の前と同じ(D1 はプロンプトだけを動かし、mock の行動には効かない。テープの B3 の行は 2 日目から変わる)。記憶+関係と counter ×1000 の 5,000 体の記録(§10-8)は検収の前の値のまま(この 2 本は回し直していない)。

### 11-3 テスト

`tests/engine/test_resume_10d.py` は 24 関数・パラメータ込み **37 件**(検収で 5 件を足した: D1・L2・L3/L6・L4・T5。全部の一致の試験に診断の行の全列の比べを足した)。`test_state_ledger_10b.py` の行の数の試験を 192 行に直した。
回した組: `test_resume_10d`・`test_state_ledger_10b`(台帳の網羅と AST の検査)・`test_census_out`・`tests/test_cli.py`・`tests/test_manifest_roundtrip.py` の 145 件が全部合格。その前の回(検収の直しの途中のコード)で `test_sim_time_T`・`tests/engine/processes`・`test_calendar_sites`・`test_classical_social`(classical 1,500 体の golden)・`test_classical_policy`・`test_10a_review_fixes`・`test_presence_executor`・`test_ledger_wiring`・`test_stage3_small_fixes`・`test_renderer_wiring`・`tests/perception`・`test_fleet_wiring`・`test_tape_deferred`・`test_response_delay` も合格(落ちたのは `test_census_out::test_the_checkpoint_does_not_move` の 1 件=ラン ID を実行ごとに一意にしたら manifest が回ごとに違った。状態の口を使わないランではラン ID を作らない形に直して合格)。全体のテストは親が回す。

## 12. 再確認の後の直し(review-10d.md §再確認・N1〜N3・src は触らない)

| # | 指摘 | 直し | 壊した写しで落ちるか(作業用ディレクトリに src を写して 1 か所ずつ壊し、`-o pythonpath=<写しの src>` で回した) |
|---|---|---|---|
| N1 | `_b3` の鍵から日を外しても 37 件が全部合格する(既定の世界は再生の実日が毎日同じ・合成世界は天候が日付に依らない) | 描画の単体の試験 `test_b3_weather_follows_the_replay_date_of_each_day` を足した: 描画に 2 日分の違う W13 の行(07-28 は曇・07-29 は雨)を持たせ、`weather_date_fn` が日ごとに別の実日を返す形で `Renderer._b3` を直接呼ぶ。2 日目(同じ 5 分帯・暦の日付は実日と別)の B3 の天候と暑さが 2 日目の実日の行 | 鍵を `(0, 5 分帯)` にした写しで**落ちる**(2 日目も「曇」=0 日目の行を使い回す) |
| N2 | `test_named_closed_memo_survives_a_resume` は控えが戻るところまでしか見ていない(体の `last_result_tick` が控えの tick と違い、B6 の 1 句が出ない) | 書き直した: T=599 の頭で、直前の結果が「閉店」の体ぜんぶに、その結果の tick を持つ控えを入れる(1 句が出る条件を満たす)。再開のランの解決器の控えが保存と同じ・再開の直後の描画で 1 句(「…は閉店中」)が実際に出て、通しの同じ tick・同じ体と同じ文・その呼の prompt_hash も同じ・全 tick の 3 つのハッシュとテープも同じ | (a) 台帳の O94 を discardable に戻した写し: 保存に控えが無く**落ちる** (b) 戻した直後に控えを捨てる写し: 戻した後の full-hash の検算で**止まる** (c) 検算の後で控えを捨てる写し(描画にだけ効く形): 控えの比べで**落ちる** |
| N3 | §2-2 の末尾の「張り直さないもの」が初版の文言 | 今の実装に合わせて直した(張り直さないのは食事の予定・計画境界の曜日の差(K9)・古典の事前分布の曜日・関係の初期の辺の曜日・エネルギーの計数) | なし |

テスト: `tests/engine/test_resume_10d.py` は 25 関数・パラメータ込み **38 件**(N1 で 1 件を足し、N2 で 1 件を書き直した)。回した組は下。

回した組(src はこの節の前のまま): `tests/engine/test_resume_10d.py`(38 件)・`tests/engine/test_state_ledger_10b.py`(台帳の網羅と AST の検査)・`tests/perception` の約 400 件が全部合格(終了コード 0)。壊した写しは作業用ディレクトリの `mut1`〜`mut4`(検収の後に親が消す)。
