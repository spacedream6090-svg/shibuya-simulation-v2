# 第 6 期 6-6 ② 第 1 部「店の仕事を働く人の体へ」(開閉店・補充・廃棄・腕 `--duties arm`)の記録

- 実装役 Opus 5.5。作業木の枝 `6-6/store-duties-arm`(土台 `6115860`=カレンダー 3 の取り込みの後の本体・本体の世界は W21)。commit は親。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §1-5(② 他の人の仕事をエンジンが代わりにしている=働く人の
  エージェントへ)・§1-4(人の手続きはコードに書かない=住人の知識から出す)・§1-1 CP6 と §2 の 2(まだ人の行動で作れない変化は
  エンジン規則でつなぐ=conf 宣言つき・カバー率を台帳へ)・§4-1 CA1・§4-4 CT1 C3・[計画](../../../../design/v2-implementation-plan-2026-10-12.md)
  6-6・回答 2-1(GPU の前に仮のモデルで)・[口の約束](../../../../design/v2-foundation-contracts-2026-10-13.md) 1-3・1-8 J0・10-13b §0-3。
  先行の記録 [ca3](../ca3/README.md)・[ca1b](../ca1b/README.md)・[pop43](../pop43/README.md)・[rules42](../rules42/README.md)。
- **全部 腕**(既定 off=層を作らない=今のまま)。検証の錨・封印した層は読んでいない。数は実測。生の出力は作業木の `_bc/`(git の外)。
  このフォルダには比べた結果と道具だけ(絶対パスなし)。道具 [tools/](tools/)。測った機械: Windows 11・x86-64(別の実装役 2 人と
  検収役・親の全体試験が並走=壁時計は参考)。
- **本段で触らないもの(第 2 部以降=宣言)**: 納品のドライバー・清掃・収集・宅配・道路工事・バスと鉄道(運転士・車掌・指令)・出動・
  報道・催し・ホテル・車の流れ・値段。閉店の後の片付け。

## 0. 結論

> 〔検収の直し〕独立検収([review.md](review.md)=条件つき受入 中 4・低 8)を親の判断どおり 1 回で直した。**§13 が正**(§0〜§12 の
> 数と形は直す前の記録。候補を出す体=その店の雇用の行を持つ体なら誰でも・カバー率は雇用の行の出どころ別と店の決まりの出どころ別・
> バックヤードが空なら補充の候補なし・補充の「居る」は開閉と同じ・ほか)。

- 腕 `--duties {off,arm}`(環境変数 `SHIBUYA_DUTIES`・既定 off)を足した。arm は世界過程の開閉店(`OpeningProcess`)・補充
  (`ShelfRestockProcess`)・売れ残りの廃棄(`WasteCollectionProcess`)に持ち主 `DutiesLayer` を挿し、**担当が店のセルに居て起きている店は
  エンジンが代わりにしない**。担当(開閉の過程の担当の表=雇用の行の店ごとの最初の体)が本人の判断(J0・仮のモデル=一様)で開ける/閉める・
  棚に補充する・閉めた店の売れ残りを捨てる。担当が居ない店・担当が店で寝ている店は今の conf 宣言つきのつなぎのまま(カバー率を計器と台帳へ)。
- **店の決まり=住人の知識**: W7 の営業時間の表のその日の行を、その店の雇用の行(体 → 店)の体だけが店の決まりの口
  `ShopRules`(カレンダー 3 の `StoreRules` の子=問い合わせの口)で引ける。開閉の候補を出す条件はこの口の答えだけ(時刻の直書き 0=AST)。
  常識の文に 1 行(「店の決まり: 営業 9:00〜21:00。」)。
- **既定 off で結果不変**: 既定の 5,000 体 1 日の final `bb86f898…`(=本体の既定 v3 の値)・byte-check 19 構成 × 25 欄=§4。
- **腕 arm(mock 5,000 体・W21・2026-07-13 月曜始まり)**: 1 日=本人が開けた 11/閉めた 11/補充した 4/捨てた 5。エンジンのつなぎは
  開閉 4,189・補充 43・廃棄 1,544 行=**担当の行動の割合は開閉 0.5%・補充 8.5%・廃棄 0.3%**(担当の表は 2,337 店とも埋まっているが、
  〔検収 L4〕最初の雇用の行の出どころは W21c 68 店/丸振り 2,269 店=1 人の担当が何十の店を受け持つ=担当がその店のセルに居ることが
  少ない=§9 の 1)。監査 0・
  記録 on/off で final と checkpoint が同じ・2 日の T=1440 の再開=通し。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/duties/__init__.py`(新) | 包みの説明 |
| `src/shibuya/engine/duties/arm.py`(新) | 腕の切替口・設定の指紋の組・状態台帳の腕の名 `duties`・manifest の鍵 `duties` |
| `src/shibuya/engine/duties/port.py`(新) | 判断の口 `DutiesPort`(`DecisionPort` の子・用途名 `duties.mock`/`duties.present`)・判断の種類 3・候補の語の閉じた表(役割語 開閉店・補充・接客+なし+廃棄)・呼びの id(通し番号は 2^22 から=ほかの口とぶつからない) |
| `src/shibuya/engine/duties/knowledge.py`(新) | 店の決まりの口 `ShopRules`(`knows`・`at`・`edge`・`hours`)・常識の文 `rules_line` |
| `src/shibuya/engine/duties/layer.py`(新) | 持ち主 `DutiesLayer`・系 `sys_duties`・manifest の `duties`・監査 `audit_causes` |
| 共有のファイル | §11 |
| `tests/engine/duties/`(新) | §10 |
| 記録 | 本書・[du1_5000.json](du1_5000.json)・[byte_check_du1.json](byte_check_du1.json)・道具 [tools/run_du1.py](tools/run_du1.py)・[tools/add_bridges_du1.py](tools/add_bridges_du1.py) |

## 2. 口の表(誰が)

| 口 | 置き場 | 中身 | 誰が |
|---|---|---|---|
| 店の決まり(営業時間) | `ShopRules.at/edge/hours`・`rules_line` | その日の W7 の行(曜日・祝日の行・申込書 L1 の差し替えを含む)=担当(雇用の行 体 → 店)だけが引ける | 組織の口(読むだけ) |
| 店に居るか・起きているか | `DutiesLayer.run_step`(配列演算)・`DutiesLayer.awake` | 担当のセル=店のセル・寝ていない・その刻みに主の判断の呼びが無い | エンジン(物理=居場所だけ) |
| 開閉の気づき | `_shop_offers` | 店の決まりで 15 分後に営業なのに閉まっている/15 分後に休みなのに開いている | System 1(本人の知識の答えだけ) |
| 棚の気づき | `run_step`(補充の評価の刻みごと) | 棚の残りが補充点の下・営業中=店の中の気づき | System 1 |
| 閉店の作業の気づき | `run_step` | 自分が閉めた店に売れ残りがある(前の 05:00 から 1 回) | System 1 |
| 選ぶ | `_shop`・`_restock`・`_discard`(`DutiesPort`) | 開ける/閉める/まだ・補充する/接客する/待つ・捨てる/まだ | 担当(判断の口=仮のモデル) |
| 開け閉め | `_set_shop` → `resolve.request_open_close`+ActualLog `SCHEDULED` | 権利は台帳に聞く(無くても止めない=CP3) | 担当の体 |
| 補充 | `ShelfRestockProcess.restock_by_staff` | 今の役割行動と同じ量・代金(原因=過程 shelf)・`SCHEDULED`/`SKIPPED` | 担当の体 |
| 廃棄 | `WasteCollectionProcess.bin_by_staff` | 05:00 のつなぎと同じ式で棚 → ビン | 担当の体 |
| 主の判断の役割語 | `LLMBridge.role_sink` → `note_role_word` → `_role_word` | 「補充」「開閉店」を同じ刻みに本人の行動として(店に居るときだけ) | 主の判断(実 LLM の段) |
| つなぎ | `OpeningProcess.step`・`ShelfRestockProcess.step`・`WasteCollectionProcess._sell_leftovers_to_bin` | 担当が居ない/寝ている店だけ(REPLACEMENT conf 0.5・10:00・05:00) | エンジン |
| 労働時間・店の決まりの外 | `_labor`・`_set_shop` | 1 日 8 時間(human の行)・決まりで休みの時刻に開けた/営業の時刻に閉めた=数えるだけ | 計器(止めない) |
| 計器 | manifest の `duties` | §5 | — |
| 監査 | `audit_causes`・`issued_keys`・`role_call_ids`(行 DUQ) | 仕事の族の語の原因=この層の判断の呼び(源と番号つき)か役割語の道の主の判断の call_id | — |

## 3. 流れ(知る → 気づく → 選ぶ → 変わる)

系 `duties` は刻みの中・カレンダー 2 の系の後・記憶の系の前(その刻みの主の判断が決まった後)。世界の系(開閉・補充・廃棄の過程)は
刻みの頭の方で先に回る。

1. **知る**: 担当は自分の店の決まり(営業時間)を店の決まりの口で引く。担当でない体は知らない。
2. **気づく**: 担当が自分の店のセルに居て、起きていて、主の判断が無い刻みに、(a) 決まりと店の状態が 15 分先で食い違う・(b) 棚が
   補充点の下(5 分ごと)・(c) 自分が閉めた店に売れ残り。
3. **選ぶ**: J0 の候補(仮のモデル=語と id の順に並べて乱数の余り=一様)。
4. **変わる**: 選んだら本人の行動の口(開閉=`request_open_close`・補充=`restock_by_staff`・廃棄=`bin_by_staff`)。出来事は族 `仕事`
   (開けた・閉めた・補充した・捨てた)・原因=判断の呼び。ActualLog は `SCHEDULED`(担当の行動)。
5. **つなぎ**: 担当が居ない/寝ている店は世界の系が今のまま代わりにする。開始の刻みの最初の設定(`open_now` が負の店)もエンジン。
   担当が捨てた店は次の 05:00 のつなぎが捨てない(担当が閉めた/捨てた印は 05:00 のつなぎの後に空に)。

## 4. 既定 off の結果不変

- 既定の 5,000 体 1 日(本書の道具 `run_du1.py one --arm off`): final `bb86f89855172717…`=本体の既定 v3 の値(K19 の定数と同じ)。
- byte-check 19 構成(mock/classical 5,000 体・seed 1・1 シミュ日・テープつき)× 25 欄: 土台 `6115860` の写し(`git archive`+
  `HEAD_TREE_FILES`+data へのつなぎ=回した後に `cmd /c rmdir` で外した)と作業木の src=§4-1(`byte_check_du1.json`)。
  5,000 体のランは 1 本ずつ(`--jobs 1`)。`SWITCH_ENV` に `SHIBUYA_DUTIES` を足した(両側とも未設定)。
- 既定のランで動く欄(どれも 25 欄の外): `manifest_sections`(節の表=`duties` と子)・`bridges_count`(つなぎの台帳 616 → 626)・
  `bridges_version`・日次の記録の `bridges_count`・出来事の記録の語彙の版(`events-vocab/6-6-w1`)。
- 腕 off のランでは層・系・世界過程の `duties`(None)・`LLMBridge.role_sink`(None)のどれも動かない(試験 `test_default_off_builds_nothing`)。

### 4-1. byte-check の結果

[byte_check_du1.json](byte_check_du1.json): 19 構成 × 25 欄が**全部同じ(19/19)**・呼数の合計 1,106,861(両側)・両側の `env` 空・
`tree_missing` 空・作業木の側は `src_is_worktree` 真。既定 v3 の final `bb86f898…`・活動層 off `3cdf9dbf…`・v1 `8fca095b…`・
`v3_mem_rel` `94becde2…`(カレンダー 3 の記録の 4 構成と同じ値)。

## 5. 計器(腕 arm・mock 5,000 体・世界 v2(W21)・seed 1・2026-07-13 月曜始まり・合否なし)

[du1_5000.json](du1_5000.json)(道具 [tools/run_du1.py](tools/run_du1.py))。

| 計器 | arm 1 日 | off 1 日 | arm 2 日 | off 2 日 |
|---|---|---|---|---|
| final(頭 16) | `0643442c88a7dbe9` | `bb86f89855172717` | `209ae071523d6084` | `38d5d5674b90f993` |
| 壁時計・1 刻み・最大の作業メモリ | 39.4 秒・27.4 ms・505 MB | 37.6 秒・26.1 ms・511 MB | 79.9 秒・27.7 ms・509 MB | 84.4 秒・29.3 ms・501 MB |
| 判断の呼び(店の仕事)・LLM の呼び | 95・63,515 | 0・63,572 | 678・139,371 | 0・138,821 |
| 判断の内訳(開閉/補充/廃棄) | 48/35/12 | — | 103/553/22 | — |
| 本人 開けた/閉めた/補充した/捨てた | 11/11/4/5 | — | 26/21/16/12 | — |
| 開閉の過程の役割行動(担当が居る店をエンジンが担当として)・つなぎ | 0・6,526 | 22・6,524 | 0・10,769 | 38・10,772 |
| エンジンのつなぎ 開けた/閉めた(担当の表のある店) | 2,110/2,079 | — | 4,230/4,202 | — |
| 補充 つなぎ(10:00)・本人・本人の失敗(バックヤード空) | 43・4・9 | 43・(役割行動 3) | 198・16・164 | 194・(役割行動 12) |
| 廃棄 つなぎの行・本人の行(個数) | 1,544・5(9) | 1,544・— | 2,932・12(21) | 2,937・— |
| 棚の減った店 × 分(全店・世界過程の後に数えた) | 101,976 | 102,485 | 341,943 | 337,051 |
| 棚の空の店 × 分 | 11,600 | 11,538 | 46,702 | 46,340 |
| 担当が店に居た店 × 刻み(寝ていた・主の判断が先) | 12,996(2,367・211) | — | 27,411(4,212・508) | — |
| 労働時間の行を超えた体 × 日・決まりの外の開け閉め(開けた/閉めた) | 10・10/10 | — | 19・25/20 | — |
| 監査の食い違い・仕事の族の出来事 | 0・31 | —・0 | 0・75 | —・0 |

カバー率(本人/(本人+エンジン)):

| 項目 | arm 1 日 | arm 2 日 |
|---|---|---|
| 開閉 | 22/4,211=0.5% | 47/8,479=0.6% |
| 補充 | 4/47=8.5% | 16/214=7.5% |
| 廃棄(行) | 5/1,549=0.3% | 12/2,944=0.4% |
| 担当の表のある店の割合 | 2,337/2,337=100%(〔検収 L4〕W21c 68 店+丸振り 2,269 店) | 同じ |

開店の遅れ(店の決まりの区切りとの差[分]・負=早め・仮のモデルは 1 刻みごとに半分の確率で開ける=偏る): 1 日=開けた −15(3)・−14・
−13・−12(2)・−10・−3・−2・0/閉めた −15(4)・−14(4)・−4(2)・+3。2 日=開けた 26 件は全部 −15〜0・閉めた 21 件のうち 20 件が −15〜−1
(+3 が 1 件)。

- **数の読み方の注**: 仮のモデルは候補から一様に選ぶ=数は振る舞いのモデルではない。担当が店に居る機会が少ないのは担当の表の形
  (丸振りの 1 人が多くの店を受け持つ・その店のセルに居ることが少ない)のせい=本段の判断の形ではない(§9 問い 1)。
- 棚の新旧: 減った店 × 分は 1 日で −0.5%・2 日で +1.5%、空の店 × 分は +0.5%・+0.8%(どちらも担当の居る店がわずかなので差は小さい・
  2 日の本人の補充の失敗 164 はバックヤードが空の店=仮のモデルが毎回選び直す)。
- 労働時間の行を超えた体は「担当が自分の店のセルに居た分」が 8 時間を超えた体(1 日 8 時間の行=human=数えるだけ)。

## 6. 負の対照

| 確かめ | 対照 | 試験 |
|---|---|---|
| 判断なし=開かない | 仮のモデルがいつも「まだ」=担当の居る店は正午まで閉じたまま・担当の居ない店はつなぎが開けた・担当の店の ActualLog の行 0 | `test_without_the_decision_the_staffed_store_stays_closed` |
| 補充しない=エンジンも補充しない | いつも「接客する」=担当の居る店の補充の行 0(10:00 のつなぎも無い) | `test_without_the_decision_the_shelf_is_not_restocked_by_the_engine_at_a_staffed_store` |
| 寝ている担当の店はつなぎ | `awake` を偽に=担当の居る店の開閉は REPLACEMENT | `test_a_sleeping_staff_is_bridged_like_an_absent_one` |
| 候補の条件は店の決まりの行から | 店の決まりを 9:00 → 13:00 にすると最初に開けた刻みが 12:45 より後へ動く・常識の文も動く | `test_the_offer_moves_with_the_store_rules` |
| 時刻の直書き 0(AST) | `_shop_offers`・`run_step` の比較と算術に 0・1 のほかの数が無い・`_shop_offers` は開閉の行列を直に読まない。植えた 4 件を全部見つける | `test_ast_offer_conditions_have_no_time_literals`・`test_ast_negative_control_catches_time_literals` |
| 本人の語の原因は判断の呼びだけ(AST) | `_log` の原因は名前 `cause` だけ・`cause` は `self._decide` の答えか `_role_word` の `LlmCall` だけ。植えた 3 件を見つける | `test_ast_person_events_come_only_from_decisions`・`test_ast_negative_control_catches_planted_causes` |
| 監査 | 過程が原因・層に無い呼び・体の違い・種類の違い・時刻の違い=5 件とも数える | `test_audit_catches_forged_causes` |
| 段 B | duties の宣言から `DU*:duties.*` を外すと `AssertionError`(宣言の外) | `test_stage_b_negative_control_without_the_declaration_fails` |
| 既定は何も作らない | 層なし・manifest の節なし・状態のファイルの `duties.*` なし・指紋の鍵なし・仕事の族 0・世界過程の `duties` は None | `test_default_off_builds_nothing` |
| 取り違えの再開は止まる | arm で書いた状態を off で再開=設定の指紋の `duties` で止まる | `test_resuming_with_the_arm_off_stops` |

## 7. 2 日と再開・記録 on/off

| ラン | 通し | 再開/off | 同じか |
|---|---|---|---|
| 5,000 体 2 日・T=1440 で止めて再開 | `209ae071…` | `209ae071…` | final・T≥1440 の checkpoint 24 個の behavior/full・manifest の `duties` 10 欄が同じ |
| 5,000 体 1 日 記録 on/off | `0643442c…` | `0643442c…` | final と checkpoint 4 個の behavior-hash が同じ(off の記録 0 行) |

- 合成(80 体・1 セル・2 日)の再開=通し(`test_two_days_and_resume_is_the_straight_run`)・記録 on/off(`test_event_log_on_off_does_not_change_the_arm_run`)。
- 世界過程の計数(状態台帳 O73=discardable=再開で 0 から)は増えだけを読む(覚えの値 `_du_base` も組み立てで 0 から)=再開でも
  カバー率の分母が通しと同じ。

## 8. manifest の節・設定の指紋・状態台帳の行・つなぎの台帳・語彙

- manifest の一番上の鍵 `duties`(腕 arm のランだけ)。設定の子 7(`schema`・`arm`・`port`・`rules`・`arbitration`・`bridges`・
  `provisional`)・観測の子 11(`meter`・`decisions`・`shop`・`shelf`・`waste`・`coverage`・`delay_minutes`・`labor_over`・`role_words`・
  `common_knowledge`・`calls`)。設定の道筋 `CONFIG_PATHS_SHA256` `94fe399f…99682dea` → `91c11fdf…01bd1f085e`(この 7 本を外すと前の値)。
  `calls_by_model` に内訳 `duties`(manifest と日次の記録)。
- 設定の指紋に `duties`(腕 arm のときだけ=`{"arm": "arm"}`)。世界過程の無いラン(`processes=False`)の arm は組み立てで止める。
- 状態台帳の腕の行(腕の名 `duties`・持ち主の居るランだけ 2 つのハッシュと状態のファイルに入る=既定は不変):

| 行 | 道筋 | 軸 1 / 軸 2 |
|---|---|---|
| DUS | `duties._closed_by_me`・`_binned`・`_days` | behavior / required |
| DUG | `duties._role_asks`(判断の系が積み同じ刻みの系 duties が読む) | behavior / required |
| DUM | `duties._du_meter`・`_du_hist`・`_du_prev`・`_du_minutes`・`_du_over` | diag / required |
| DUQ | `duties._du_issued`・`_du_issued_n`・`_du_role_ids` | diag / required |

- 外の状態 149 → 153 行・全体 240 → 244 行。除外: `duties` の設定・参照・`_codes`・`_du_base`(CACHE)・世界過程 3 つの `duties`(REF)・
  `bridge.role_sink`(REF)。診断の出口 `DutiesLayer._engine_meter`(世界過程の計数の増えを読むだけ)。
- 出来事の記録の語彙: 族 `仕事` と 4 語(開けた・閉めた・補充した・捨てた=表の末尾=カレンダー 3 までの 101 語のコードは不変・101〜104)・
  版 `events-vocab/6-6-w1`(並行の段と取り込みで親が合わせる)。道具の名は足していない。
- つなぎの台帳 10 行(`DOC-du1-port-candidates`・`-shop-window`・`-store-rules`・`-shelf-notice`・`-unstaffed-bridge`・
  `-one-staff-per-store`・`-no-cleanup`・`-labor-record-only`・`-role-word-path`・`-not-default`=616 → 626 行・active 602)。
  `PR-store_opening`・`FB-store_opening`・`PR-shelf_stock_restock`・`PR-waste_collection` の `why` の末尾に「腕 arm では担当の居る店で本人の
  行動に置き換わる(割合)・既定 off では今のまま」を足した(`what`・外す段・状態は変えない)。道具 [tools/add_bridges_du1.py](tools/add_bridges_du1.py)
  は同じ id の行を置き換え・追記は 1 回だけ(2 回回して同じ)。
- 乱数: 用途名 `duties.mock`・`duties.present`(動きの側=`MOTION_RNG_DOMAINS` の末尾)・`SAFE_SITES` 24 → 25・決まらない呼び手 16 → 17。
  系の表: 刻みの系 29 → 30(`calendar_2` → `duties` → `memory`)。

## 9. 限界と仮採用(〔検収の直し〕親の判断に合わせて直した)

1. **担当の表の形とカバー率**(親の判断=M1): 候補はその店の雇用の行を持つ体なら誰でも(店のセルに居て起きていて主の判断が無い・
   1 店 1 刻み 1 人=雇用の行の順で最初)。エンジンの代打を止める「居る」も同じ判定(`staffed_now`)。カバー率は行動した体の雇用の行の
   出どころ(W21c/丸振り)で分ける(つなぎは店の担当の表の体の出どころ)。実測(5,000 体): 雇用の行 2,435 行・290 体・最初の行の
   出どころは W21c 68 店/丸振り 2,269 店・2 行以上の店 29(〔検収 L4〕)。丸振りの偏り(1 人が多くの店)は母集団の側の行
   `DOC-pop43-store-round-robin-kept` に残す=宣言(`DOC-du1-employment-candidates`)。
2. **候補を出す幅 15 分**(仮採用・`DOC-du1-shop-window`): 区切りの 15 分前から食い違う間ずっと。〔検収 L6〕先読みが夜中をまたぐと
   今日の行列を巻き戻して読む(つなぎも同じ=食い違いなし)を宣言に足した。
3. **棚の知覚の形**(親の判断=M2): 店の中の気づき(Percept の外)は受入・バックヤードが空なら候補を出さない(本人は在庫を知って
   いる)・出さなかった数を計器 `shelf.no_notice_empty_backroom` に。
4. **W7 の既定の行**(親の判断=M3): 答えるが出どころの印を付ける(W7 の列 src を `world/assets.py` で読む=`plan_src_names`・
   `plan_poi_src`)。記録の `origin`=`store_rules:<出どころ>`・常識の文に「(出どころ category_default=作り物の印)」・計器(カバー率・
   遅れ)を出どころで分ける。
5. **寝ている担当の店**: 雇用の行の体が店のセルで寝ているだけの店はつなぎ(エンジン)(試験 `test_a_sleeping_staff_is_bridged_like_an_absent_one`)。
6. **開始の刻みの最初の設定**はエンジン(`open_now` が負の店=世界の最初の状態)。
7. **主の判断の役割語の道**(`DOC-du1-role-word-path`): 「補充」「開閉店」を同じ刻みに実行・体の行為の語は安全弁(なし)のまま・
   開閉店=今の状態の逆。仮のモデルの主の判断は役割語を出さない=5,000 体では 0 件(合成の試験だけ)。
8. **カレンダー 3 と結んでいない**: 担当の勤務の枠(カレンダー 3 の勤務の行)と開閉店の整合は「担当が店に居ないとつなぎ」の数
   (エンジンのつなぎの開閉=開けられなかった店)で見るだけ。勤務の行の時刻から店に行くのは 1b の既定化と第 2 部。
9. 労働時間=雇用の行の店のセルに起きて居た分(〔検収 L3〕寝ている刻みは数えない・休憩・ほかの勤め先は数えない)・閉店の後の片付けは
   無い・補充の代金の原因は過程 shelf のまま。
10. 艦隊の経路(実 LLM)は通していない(mock だけ)。

## 10. 試験

新しい試験 `tests/engine/duties/`(共通 `_du.py`=腕の切替・1 セルの合成の世界(店 2=店 1 に担当・店 0 は担当なし)・店の決まり 9:00〜21:00・
物の台帳・判断の差し替え):

- `test_du_units.py`(10): 店の決まりの口(担当だけが知る・日で巻き戻す・区切り・常識の文・休業日の枠は空・表の行に従う・表が無ければ
  知らない)・仮のモデル(一様・決定論・閉じた語)・呼びの id がぶつからない・腕の切替口・AST の 2 つと負の対照 2 つ。
- `test_du_runs.py`(22): 既定 off・担当の居る店は本人・居ない店はつなぎ・manifest の節と `calls_by_model`・判断なし=開かない・寝ている
  担当はつなぎ・候補の条件は店の決まりから・補充は本人(つなぎなし)・補充しない対照・廃棄は閉店の作業(05:00 のつなぎが捨てない)・
  労働時間は記録だけ・2 日と再開・取り違えの再開・記録 on/off・段 B と負の対照・役割語の道・LLMBridge の口・監査の負の対照・語彙・
  腕の行と系の宣言・CLI とランの種類・世界過程の無い arm は止まる。
- `test_du_world.py`(1・slow・data): 5,000 体 1 日(本人とつなぎ・役割行動 0・監査 0)。

結果: §12。

## 11. 触った共有ファイル(どれも末尾に足す形・腕のランだけ通る)

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/processes/opening.py` | 属性 `duties`(既定 None)・`step` の腕のときだけの分岐(担当が店に居て起きている最初の設定の済んだ店を外す・寝ている担当は居ないのと同じ)・docstring の段落 |
| `src/shibuya/engine/processes/goods_flow.py` | 補充: 属性 `duties`・`step` の腕のときだけの分岐(役割行動の代打をしない・寝ている担当は 10:00 のつなぎ)・新しい口 `restock_by_staff`。廃棄: 属性 `duties`・`_sell_leftovers_to_bin` の腕のときだけの分岐(担当が捨てた店を除く)・新しい口 `leftovers_of`・`bin_by_staff` |
| `src/shibuya/engine/llm_bridge.py` | 属性 `role_sink`(既定 None)・役割語の分岐の中で口があれば渡す(行為の語は今のまま) |
| `src/shibuya/engine/events/vocab.py` | 族 `仕事`(`FAMILIES` の末尾)・4 語(表の末尾)・版・docstring |
| `src/shibuya/engine/systems/table.py` | import 1 行・`calendar_2` と `memory` の間に系 `duties`・decide と llm_receive の `paths` の末尾に `DUG:duties._role_asks`・close_final の reads の末尾・docstring の段落 |
| `src/shibuya/engine/systems/conductor.py` | `WHEN` の末尾に `duties` |
| `src/shibuya/engine/systems/boxes.py` | `OWNER_NAMES` の末尾・`Layers` の末尾の欄 `duties` |
| `src/shibuya/engine/systems/state_io.py` | `hash_owners` の末尾と docstring・日次の記録の `calls_by_model` の内訳 `duties` |
| `src/shibuya/engine/systems/run_end.py` | `calendar3_layer` の直後に `duties_layer` |
| `src/shibuya/engine/systems/build.py` | 設定の指紋(カレンダー 3 の直後・世界過程が無ければ止める)・組み立て(カレンダー 3 の層の後=世界過程 3 つと LLMBridge に口を挿す)・`Layers(duties=…)` |
| `src/shibuya/engine/run.py` | `_calls_by_model` に `duties`・`before_du`・manifest の末尾(`calendar_3` の後)・補助 `_duties_field`・乱数の用途名の表の末尾 2 つ |
| `src/shibuya/engine/rng_audit.py` | `SAFE_SITES` の末尾 1 行・`UNDETERMINED_SITES` の末尾 1 行 |
| `src/shibuya/engine/manifest_sections.py` | `PATHS` の末尾(`calendar_3` の後) |
| `src/shibuya/engine/state_ledger.py` | `_EXT` の末尾(CA3Q の後)に 4 行・`OWNER_CLASSES` の末尾 1 項・`EXCLUDED` の末尾 9 項 |
| `src/shibuya/engine/state_ledger_ast.py` | `DIAG_EXITS` の末尾 1 行(`DutiesLayer._engine_meter`) |
| `src/shibuya/cli.py` | `run` のランの種類の腕の数え方の末尾・引数 `--duties`(`--experiment` の前)・切替口 |
| `docs/design/bridging-ledger.json` | 末尾に 10 行・店の仕事の 4 行の `why` の末尾 |
| `docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py` | `SWITCH_ENV` の末尾に `SHIBUYA_DUTIES` |
| 凍結の表の試験 | `tests/engine/systems/test_systems_table.py`(並び・刻みの系 30)・`writes_soa_frozen.json`(`duties`)・`tests/engine/events/writes_paths_events.json`(`calendar_2` の後に `duties`)・`test_e_vocab_is_closed.py`(105 語)・`tests/engine/test_state_ledger_10b.py`(153・244・腕の行の並び)・`test_state_checks_10f.py`(`SAFE_SITES` 25・決まらない呼び手 17)・`test_env_and_sections_10f.py`(`CONFIG_PATHS_SHA256`)・語彙の版と族の並びを固定していた 5 本(`tests/engine/speech/test_speech_port_schema.py`=腕の行の並びも・`tests/engine/tools/test_c0_tool_registry.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/engine/multiday/test_md23_body_events.py`) |

触っていない: カレンダー 3 の層(`calendar3/*` は `StoreRules` と `labor_params` を読むだけ)・判断の口の土台(`decision/port.py`・`ports.py`=
本段は自分の口 `DutiesPort` を持つ=主の判断の mock の語彙は変えない)・権利台帳・規則の表・W7 の表・`manifest_keys_frozen.json`・
`tick_word_allow.json`・`time_literal_allow.json`・用語集(足す語の候補: 店の決まり・店の中の気づき・閉店の作業・担当の行動の割合)。

## 12. 結果(試験・byte-check)

作業木の src・本体の .venv・`-p no:cacheprovider -o addopts=""`:

- 範囲(`tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`・
  `tests/c7` は回さない): **4,221 passed・1 skipped・2 failed・0 errors**(59 分 47 秒)。落ちた 2 本は直して単独で通した:
  `tests/economy/cp2/test_cp2_writes_declared.py::test_declaring_systems`(`A:ledger.*` を宣言する系に `duties` が入った=凍結の並びを
  張り替えた)・`tests/engine/bridging/test_manifest_rules_bridges.py::test_values_match_the_ledger_and_the_table`(範囲の試験の途中で
  つなぎの台帳の割合の文を書き足した=試験の頭のランと後の読みで台帳の sha が違った=src は同じ)→ 直した後
  `tests/economy/cp2/test_cp2_writes_declared.py tests/engine/bridging`=**53 passed・0 failed**。
- `tests/engine/duties`(slow を除く): 32 passed(範囲の中)。slow の 5,000 体 `test_du_world.py`(1 本だけで): **1 passed**。
- lint-imports: 5 kept・0 broken。
- 範囲の後に新しい識別子の「open」を外した(持ち主の参照 `opening` → `shops`・定数 `_SHOP_PROCESS_ID`・試験の名前=挙動は同じ)。
  その後 `tests/engine/duties tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/systems
  tests/engine/time tests/engine/bridging`(not slow)=**361 passed・0 failed**・slow の `test_du_world.py`=1 passed。
- byte-check 19/19(§4-1)・5,000 体の再開=通し・記録 on/off 同じ(§7)・監査 0(§5)。

## 13. 独立検収の直し(条件つき受入=中 4・低 8 → 全部直した・rebase はまだ)

検収の記録は [review.md](review.md)。この節の数が正(§0〜§12 は直す前の記録)。親の判断(M1〜M4・L1〜L8)のとおりに直した。

### 13-1. 直しの表

| 欠陥 | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| M1 担当が店ごとに 1 人・カバー率を出どころで分けていない | `duties/layer.py`(`ensure_staff`・`_here`・`staffed_now`・`first_per_store`・`run_step`・`_coverage`)・`processes/opening.py`・`goods_flow.py`(腕の分岐) | 候補=その店の雇用の行(体 → 店)を持つ体なら誰でも(店のセルに居て起きていて主の判断が無い・1 店 1 刻み 1 人=雇用の行の順で最初)。開閉と補充の過程の腕の分岐は同じ判定 `staffed_now` で代打を止める。最初の設定を含むほかの店はつなぎ(REPLACEMENT=担当の役割行動として代打しない)。カバー率は行動した体の雇用の行の出どころ(W21c=初期の行の表の `store_staff`/丸振り)で分ける(つなぎは店の担当の表の体の出どころ・補充と廃棄のつなぎは過程の口 `note_bridge` で店ごとに数える) | `test_a_second_employee_acts_and_coverage_is_split_by_origin`・`test_first_per_store_takes_the_first_eligible_row`・`test_staffed_store_is_unlocked_by_the_person_and_the_other_by_the_bridge`(出どころの分け) |
| M2 バックヤードが空でも補充の候補 | `duties/layer.py`(`run_step`) | `notice &= backroom > 0`(本人は在庫を知っている)・出さなかった数 `shelf.no_notice_empty_backroom` | `test_no_restock_offer_when_the_backroom_is_empty` |
| M3 店の決まりに出どころの印が無い | `world/assets.py`(`plan_src_names`・`plan_poi_src`=W7 の列 src を読むだけ)・`duties/knowledge.py`(`ShopRules.source`・`rules_line`・`origin_mark`)・`layer.py` | 記録の `origin`=`store_rules:<出どころ>`・常識の文に「(出どころ category_default=作り物の印)」(実データの osm には付けない・列の無い資産は「出どころ不明」)・カバー率と遅れの分布を出どころで分ける。読み足しで既定は動かない(4 構成 off=13-3) | `test_store_rules_carry_the_source_mark`・`test_store_rules_source_mark` |
| M4 補充の「居る」が開閉と食い違う(通勤者の担当) | `goods_flow.py`(`ShelfRestockProcess.step` の腕の分岐) | 腕の分岐の `present` を `staffed_now`(店のセルに居て起きている=種別を見ない)に。二重の補充の防ぎ(`_acted_today`)は残す | `test_restock_presence_ignores_the_agent_kind` |
| L1 系 duties の `writes.paths` が宣言しすぎ | `systems/table.py` | `DU*`・`E`・`O5[23]`・`O61`・`O73`・金と物の台帳の行・`A`・`EM` だけに絞った。世界の系に `DUM:duties._du_meter`(つなぎの店を数える口) | 段 B `test_stage_b_has_no_undeclared_writes`(0)・負の対照 `test_stage_b_negative_control_without_the_declaration_fails` |
| L2 決まりの外の計器が幅の中の早めを数える・鍵に open | `layer.py`(`_set_shop`) | `unlock_early_in_window`/`unlock_outside_rule_hours`・`lock_early_in_window`/`locked_during_rule_hours` に分けた | `test_staffed_store_is_unlocked_…`(鍵に open なし) |
| L3 労働時間が店で寝ている刻みを数える | `layer.py`(`run_step`→`_labor`) | 起きている雇用の行の体だけ数える | `test_labor_rows_are_recorded_and_do_not_stop` |
| L4 記録の数が pop43 の写し | 本書 §0・§5・§9 | 実測 W21c 68 店/丸振り 2,269 店・雇用の行 2,435 行・290 体・2 行以上の店 29 | — |
| L5 `_days` が DUS(behavior) | `state_ledger.py` | DUM(diag)へ | `test_arm_rows_and_system_declarations` |
| L6 夜中をまたぐ先読みが今日の行 | `knowledge.py` の docstring・台帳 `DOC-du1-shop-window` | 宣言を足した | — |
| L7 役割語の補充が条件を見ない | `layer.py`(`_role_word`) | 営業中・棚が補充点の下のときだけ(ほかは `role_words.restock_not_needed`) | `test_role_words_from_the_main_decision_take_effect_at_the_store` |
| L8 台帳の道具が率なしで「未計測」に戻る | `tools/add_bridges_du1.py` | 率を渡さなければ今の文を保つ(冪等=2 回回して同じ)・使い方に再現の引数を書いた | — |

その他: 前の版の台帳の行 `DOC-du1-one-staff-per-store` は `DOC-du1-employment-candidates` に置き換えた(未 commit=消した・台帳 626 行・
active 602 のまま)。`DiagExit` の `DutiesLayer._engine_meter` は消した(つなぎの数は過程の口で数える=計数の増えを読まない)。
manifest の形の版 `shibuya.engine.duties/2`(`coverage` は `total`・`by_employment_origin`・`by_rule_source` の 3 つ・`shop` に雇用の
行の数)。設定の道筋は前と同じ(`CONFIG_PATHS_SHA256` は変わらない)。

台帳の 4 行の割合の文(記録の値の再現の引数):
`"0.5%(本人 23/つなぎ 4,188・W21c 5.8%/丸振り 0.4%)" "10.6%(本人 5/つなぎ 42・W21c 2/3/丸振り 6.8%)" "0.3%(本人 5 行/つなぎ 1,544 行・W21c 4.8%/丸振り 0.1%)"`。

### 13-2. 計器の新旧(腕 arm・mock 5,000 体・W21・2026-07-13 月曜始まり・[du1_5000.json](du1_5000.json) を上書き)

| 計器 | 直す前 1 日 | 直した後 1 日 | 直した後 2 日 |
|---|---|---|---|
| final(頭 16) | `0643442c88a7dbe9` | `4cbe146311ffd25b` | `b2bdfaa2d0de0d4b` |
| 壁時計・1 刻み・最大の作業メモリ | 39.4 秒・27.4 ms・505 MB | 39.5 秒・27.5 ms・498 MB | 81.6 秒・28.3 ms・506 MB |
| 判断の呼び(開閉/補充/廃棄) | 95(48/35/12) | 78(50/16/12) | 185(112/51/22) |
| 本人 開けた/閉めた/補充した/捨てた | 11/11/4/5 | 12/11/5/5 | 30/21/20/12 |
| 補充の本人の失敗・空なので候補を出さなかった | 9・— | 0・132 | 0・697 |
| 2 人目以降が判断した店 × 刻み | — | 933 | 2,083 |
| 監査の食い違い | 0 | 0 | 0 |

カバー率(本人/(本人+つなぎ))の新旧:

| 項目 | 直す前 1 日(全部) | 直した後 1 日 全部 | W21c(68 店) | 丸振り(2,269 店) | 直した後 2 日 全部 |
|---|---|---|---|---|---|
| 開閉 | 22/4,211=0.5% | 23/4,211=0.5% | 7/121=5.8% | 16/4,090=0.4% | 51/8,479=0.6% |
| 補充 | 4/47=8.5% | 5/47=10.6% | 2/3 | 3/44=6.8% | 20/214=9.3% |
| 廃棄(行) | 5/1,549=0.3% | 5/1,549=0.3% | 3/63=4.8% | 2/1,486=0.1% | 12/2,944=0.4% |

店の決まりの出どころ別(直した後 1 日・開けた): カテゴリ既定 8/1,668・OSM 4/445・チェーン既定 0/8。遅れの分布も出どころ別
(manifest の `delay_minutes` の鍵 `shop_begin:<出どころ>`)。常識の文の例「店の決まり: 営業 0:00〜24:00。(出どころ category_default=
作り物の印)」。

- 読み方: 雇用の行が 2 行以上の店は 29 しか無いので、全部のカバー率はほとんど動かない(検収の見込みどおり)。W21c の店(担当が
  その店の組織に所属)は丸振りの店より 10 倍ほど本人が多い=低さの主因は丸振り(母集団の側の行 `DOC-pop43-store-round-robin-kept`)。
- 棚の減った店 × 分(全店): off 102,485 → arm 101,966(1 日)・off 337,051 → arm 342,157(2 日)。空の店 × 分: 11,538 → 11,600・
  46,340 → 46,772。
- 労働時間の行を超えた体 × 日: 9(1 日)・18(2 日)。決まりの幅の中で早めに開けた/閉めた: 11/10(1 日)・29/20(2 日)・幅の外は 0。

### 13-3. 既定 off・2 日と再開・記録 on/off

- 既定 off の 4 構成(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`): 本体 `091f1bc` の写し(`git archive`+
  `HEAD_TREE_FILES`+data へのつなぎ=回した後に `cmd /c rmdir` で外した)と作業木の src で **4/4 構成 × 25 欄 同じ**(final `bb86f898…`・
  `3cdf9dbf…`・`8fca095b…`・`94becde2…`・`tree_missing` 空・`env` 空・作業木の側は `src_is_worktree` 真)=
  [byte_check_du1_fix_4cfg.json](byte_check_du1_fix_4cfg.json)。W7 の列 src の読み足しで既定は動かない。既定 off の 5,000 体 1 日の
  final も `bb86f898…`・2 日 `38d5d567…`(直す前と同じ)。
- 5,000 体 2 日を T=1440 で止めて再開: final `b2bdfaa2…` が通しと同じ・T≥1440 の checkpoint 24 個の behavior/full が同じ・manifest の
  `duties` 10 欄が同じ。
- 記録 on/off(5,000 体 1 日): final `4cbe1463…` が同じ・checkpoint の behavior が同じ・off の仕事の出来事 0。
- 段 B(合成): 宣言の外 0・`DU*` を外すと止まる(範囲の試験の中)。

### 13-4. 試験(直した後)

- 範囲(`tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`・
  `tests/c7` は回さない): **4,229 passed・1 skipped・0 failed・0 errors**(58 分 6 秒)。その後に台帳の割合の文を書き足した=
  `tests/engine/bridging`=49 passed。
- `tests/engine/duties`(slow を除く): 39 passed(範囲の中・新しい試験 6 本=2 人目・バックヤード空・種別を見ない補充・出どころの印・
  `first_per_store`・出どころの印の単体)。slow の 5,000 体 `test_du_world.py`(1 本だけで・出どころ別のカバー率を足した): **1 passed**。
- lint-imports: 5 kept・0 broken。

### 13-5. 触った共有ファイル(直しで足した分)

`src/shibuya/world/assets.py`(`ProcessAssets` の欄 `plan_src_names`・`plan_poi_src` と W7 の読み=列 src があれば読むだけ)・
`processes/opening.py`・`goods_flow.py`(腕の分岐を `staffed_now` に・つなぎの口 `note_bridge`)・`systems/table.py`(duties の宣言を
絞った・world に `DUM:duties._du_meter`)・`state_ledger.py`(DUS/DUM の項・除外の CACHE)・`state_ledger_ast.py`(前に足した 1 行を消した=
本体と同じ)。
