# fix4-1103 棚卸し B の欠陥 4 件の直し(小さな版上げ)と宣言の食い違いの直し

根拠: [指示書 11-03 §3](../../../design/prompt-2026-11-03-reply3.md)=検証で見つけた欠陥の修正(CLAUDE.md §2-6・試験つき・事後報告)。
欠陥の出どころは棚卸し B([behavior-audit-B-resolve-world-2026-11-02.md](../../../reference/behavior-audit-B-resolve-world-2026-11-02.md))の
M10・M11・M28・M16。宣言の食い違いは棚卸し A([behavior-audit-A-perception-decision-2026-11-02.md](../../../reference/behavior-audit-A-perception-decision-2026-11-02.md))
§4-1・§4-2 と棚卸し B §4-1・§4-2。作業の枝 `stage/fix4`(土台 HEAD `a800790`)。実装役 Opus 5.5。commit は親。

| 置き場 | 中身 |
|---|---|
| 本書 | §1 4 件の直し・§2 切替口・§3 宣言の直し 31 件・§4 試験・§5 台帳と指紋・§6 byte-check・§7 性能・§8 できなかったこと |
| [bytecheck/](bytecheck/) | byte-check の side 3 本(土台 `base_a800790`・既定 on `fix4`・旧道 `fix4_legacy`)と compare 2 本 |

## §1 4 件の直し

既定の腕 `on` で直し、旧道 `legacy` は版上げの前の挙動のまま(§2)。

| 名 | 所 | 前(legacy) | 後(既定 on) | 計器 |
|---|---|---|---|---|
| M10 | `engine/systems/talk.py` の会話の終わりの解放と、`_revert` に積まれた招待側の戻し(対象の決まらない会話の失敗・招待が流れた=不応期・`invite` の却下・返事待ちに積めなかった・期限切れの返事待ち)・`engine/run.py` の `_settle_pending_invites` の末尾の招待側の戻し・`engine/resolve.py` の新しい書き手 `end_conversation` | 3 か所とも対象の体を全員 `IDLE` にする(今の活動を見ない)。`_revert` は CONVERSING の確かめより前に「対象の決まらない会話」(`invitee < 0`=resolve が失敗させた体=活動は変わっていない)からも呼ばれるので、寝ている・歩いている・在店の体まで IDLE にしていた(対象のある会話の失敗は戻していない) | 活動が `CONVERSING` の体だけ `IDLE` に戻す。ほかは活動を変えない(=対象のある失敗と揃う)。`talk_partner` は全員 −1。戻す対象は会話中(`is_busy`)でない体だけ=積むとき(今と同じ)と、腕 on では書く直前にもう一度(同じ刻み・同じ呼び出しのうちにセッションに入った体を引き剥がさない=検収 低-2) | `n_conversation_end_kept_activity`(会話の終わり)・`n_invite_revert_kept_activity`(招待側の戻し=原因 `no_target`・`invite_failed`・`expired`・`settle` ごと × 活動の名ごと)=どちらも戻さなかった数 |
| M11 | `engine/resolve.py` の `_apply_move`(歩き出した体)・`_apply_board`(ホームへ歩き出した体)・`_serve_poi_queue`(捌く前の居場所の確かめ) | 列の印 `queue_poi` は移動・乗車で消えない。席が空けば店のセルの外で購入・食事が成立して在店になる | 移動で MOVING になった体・乗車で board_line を立てて歩く体は列を離れる(`queue_poi`・`queue_since` を −1・失敗は書かない)。捌く前に店のセルに居ない体を列から外す(活動と直前の結果は書かない) | `n_queue_left_by_move`・`n_queue_left_by_board`・`n_queue_dropped_away`(本来 0) |
| M28 | `engine/resolve.py` の `_serve_poi_queue` | 列から席へ入る前の支払いの確かめが現金だけ(`money >= price`) | 新しい行の購入・食事と同じ `_payable`(経済の段階 2 の支払いの部品では現金か口座) | `n_queue_payable_not_cash`(現金だけなら外れたが口座で払えて残った数) |
| M16 | `engine/run.py` の `_settle_pending_invites`(引数 `drop_unreachable`)・`engine/conversation.py` の新しい `ConversationManager.drop_pending` | 返事が「会話」で招待者宛て(か名指しなし)でも、届かなければ断り(`n_declined`・拒否の記憶 60 刻み) | 届かないときは不成立(`drop_pending`=返事待ちを外し `_remember_refusal` を呼ばない・起点の計数は `unreachable`)。招待側は今と同じく戻す。本人の行は intent に残す(B6 は今のまま) | `n_pending_unreachable` |

`conv.step` に `in_conversation` を渡す配線(会話の番で別の行為を選んだ体をセッションから外す)は**していない**(本人の判断の口の設計に関わる=仕分けへ・§8)。

### 1-1 頻度(5,000 体・seed 1・mock・1 日・byte-check の `w6_v3_default` と同じ引数=`vocab_version=v3`・`activity=True`)

親の計測(土台=旧道の挙動の中で数えた・final `73aa01d9afb206d0`・呼 61,066=土台と同一。親の便りの値をそのまま写す。M10 は呼び出し元ごとに数え直した値):

| 名 | 親の計測(土台) |
|---|---|
| M10 会話の終わり(base の `talk.py:217`) | 139 回・314 体・会話中でない 168(MOVING 71・SHOPPING 57・WAITING 39・IDLE 1)=実装役の探りと同じ |
| M10 招待側の戻し(base の `talk.py:193`=`_revert` に積まれた全部=対象の決まらない会話の失敗を含む) | 940 回・2,283 体・会話中でない 2,157(IDLE 1,536・WAITING 284・MOVING 208・SHOPPING 124・SLEEPING 5)。実装役の探りの内訳(原因ごと・呼び出しは原因ごとに数えた): 対象の決まらない会話 928 回・2,159 体・会話中でない 2,157(上の全部)/招待が流れた 113 回・124 体・会話中でない 0/期限切れ 0 回 |
| M10 招待側の戻し(base の `run.py:1906`=`_settle_pending_invites` の末尾) | 655 回・2,043 体・会話中でない 24(IDLE 10・MOVING 7・SHOPPING 5・WAITING 2) |
| M11 | 列から席へ入った購入 120 件のうち店と違うセルで成立 4 件(4 件とも歩行中)。列に残ったまま店のセルの外に居た行×刻み 29・歩行中 32 |
| M28 | 列の判定の行 1,508・現金不足 0・現金不足だが口座で払える 0(段階 2 の payment は on)=このランでは 0 件 |
| M16 | 返事 2,202 のうち「会話・招待者宛てだが届かない」で断りとして記録 28(承諾の成立 158) |

実装役の計測(同じ条件・テープなし。計器は manifest の `defect_fixes_1103.counts`):

| 計器 | 既定 on のラン | legacy のラン |
|---|---:|---:|
| final / 呼数 | `c8d68704b7b0760d` / 60,939 | `73aa01d9afb206d0` / 61,066(土台と同一) |
| M10 `n_conversation_end_kept_activity` | MOVING 80・SHOPPING 66・WAITING 45(計 191) | 0(旧道は数えない) |
| M10 `n_invite_revert_kept_activity` | `no_target` IDLE 1,488・WAITING 306・MOVING 208・SHOPPING 121・SLEEPING 7(計 2,130)/`settle` IDLE 10・MOVING 10・SHOPPING 7・WAITING 4(計 31)/`invite_failed`・`expired` 0。IDLE の 1,498 は戻しても戻さなくても同じ=実際に活動が残ったのは 663(うち 642 が対象の決まらない会話の失敗) | 0 |
| M11 `n_queue_left_by_move` / `n_queue_left_by_board` / `n_queue_dropped_away` | 4 / 5 / 0 | 0 / 0 / 0 |
| M28 `n_queue_payable_not_cash` | 0 | 0 |
| M16 `n_pending_unreachable` | 32 | 0 |
| (参考)列から席へ入った数 / 満席で並んだ数 / 食事 | 117 / 166 / 4,164 | 120 / 180 / 4,124 |

- M10 の範囲は会話の終わりと招待側の戻し 2 か所(親の依頼の続き)。招待側の戻しで戻さなかった非 IDLE の体は、ほとんどが「対象の決まらない会話」を選んで resolve に失敗させられた体(既定のランで 642/663=残りは返事の解決 21)。期限切れの返事待ちから来た体は 0(期限切れそのものが既定のランで 1 件)。【訂正】前の版の本書は「返事待ちの間に別の行為を選んだ招待側」が主と書いたが誤り(検収 中-2)。
- 旧道は対象の決まらない会話を選んで失敗した**寝ている体**まで `IDLE` にして起こしていた(既定のランで 7 体)。対象のある会話の失敗(相手が会話中・届かない等)は旧道でも活動を戻していない=直した道はそれと揃う。合成の小さな世界で全員が「会話 対象: P-1」と答える試験(`tests/engine/test_fleet_wiring.py`)では、この起こしが昼の会話の成立を支えていた(§4 の 7)。
- 既定の final は検収の直し(中-1・低-2)の前後で同じ(`c8d68704b7b0760d` / 60,939)=書く直前の会話中の除外はこの条件では 1 体も当たらなかった。
- 招待の帳尻(検収 中-1): 腕 on では `counters()` に `conv_pending_unreachable` を足した(既定のランで 32)。招待 2,218 = 成立 155 + 断り 2,029 + 期限切れ 1 + 未決 0 + 不成立 32 + 1。残りの 1 は `resolve_pending` で承諾が門(会話中)で落ちた分(`gate_rejected` に入り帳尻の項に無い)で、旧道でも同じ形で 1 件ずれる(土台: 招待 2,203 = 157 + 2,044 + 0 + 1 + 1)=本段の前からの穴(§8)。
- M11 は既定のランで 9 体が列を離れた(移動 4・乗車 5)。`n_queue_dropped_away` は 0(移動と乗車の外で動いて列に残った体は無かった)。
- M28 はこの条件では 0(親の計測と同じ=結果を動かさない)。
- M16 は 32(土台の親の計測 28 と同じ桁。既定のランは途中から別の軌跡になるので一致はしない)。

## §2 切替口

`src/shibuya/engine/defect_fixes_1103.py`(`engine/absent_processes.py` を写して作った)。

- 腕 `--defect-fixes-1103 {on,legacy}`・環境変数 `SHIBUYA_DEFECT_FIXES_1103`・既定 `on`。`legacy`=版上げの前の値の再現だけ(次の版上げで消す=台帳 `DOC-fix4-defect-legacy-switch`・next-bump)。
- 組み立てで 1 回読む(`run_day` の引数にしない=設定の指紋に入れない)。組み立ての箱 `Config.defect_fixes_1103`(`systems/boxes.py`)→ 行為の解決 `R.apply(..., defect_fixes=...)`(`systems/act.py`・M11・M28)・会話の系(`systems/talk.py`・M10)・返事の解決 `_settle_pending_invites(..., drop_unreachable=..., keep_activity=...)`(`systems/judge.py`・M16 と M10 の招待側の戻し)。`resolve.apply` と `_settle_pending_invites` の関数の既定は `False`=旧道(直に呼ぶ試験の互換=`seat_release_walk` と同じ形)。
- manifest の節 `defect_fixes_1103`(`manifest_sections.py`=設定 `schema`・`mode`・`fixes`・`fixed`/観測 `counts`)を末尾(`absent_processes` の後)に足した。
- 状態のファイルの見出し `defect_fixes_1103`(on のランだけ `{"mode": "on"}`=legacy は版上げの前の見出しのまま・`systems/state_io.py`)。再開で見出しの腕(無ければ legacy)と今の腕が違えば止める(`systems/build.py`)。
- 既定と違う腕(legacy)はランの種類 arm(`cli.py` の `run_kind`)。
- 系の表 `systems/table.py`: `cfg.defect_fixes_1103` を読む系(apply_responses・phase_c・conversation と、`cfg.absent_processes` を読む 4 つの系)に足し、conversation と apply_responses(返事の解決=`_settle_pending_invites` が呼ぶ・検収 低-1)の `resolve_ops` に `end_conversation` を足した。
- 会話マネージャの設定 `count_unreachable`(組み立てが腕 on で True を渡す=腕は組み立てで 1 回読んだ値を Config と共用): True のときだけ `counters()` に `conv_pending_unreachable` を出し、起点の計数に `unreachable` の鍵を最初から置く(旧道の出力は 1 字も変えない=検収 中-1・低-4)。電話・チャットの器(子クラス)は既定 False。
- 計器の積算: 列の 4 本は `leave_counts`(`systems/build.py` の初期の鍵に足した・`systems/act.py` が積む)、会話の 3 本は会話マネージャの診断の欄(`n_pending_unreachable`・`n_end_kept_activity`・`n_revert_kept_activity`=積むのは `note_end_kept`・`note_revert_kept`、読むのは `defect_fix_counters` のメソッドだけ)。会話マネージャの 3 欄は状態台帳 `engine/state_ledger.py` の行 O41(diag・discardable)と行 CT1M(電話・チャットの会話の器=同じクラス)に足した=どちらのハッシュにも状態のファイルにも入らない。

## §3 宣言の直し(31 件・値は変えない)

直したのは docstring・コメント・つなぎの台帳の行・tick-constants-inventory(tci)と decision-inventory の行番号の注だけ。プロンプトに出る文字列と定数の値は変えていない。「値の側」=値を直すべきもの。宣言の側に「実装はこう・宣言はこう・仕分け待ち(11-03 §2)」の注を足しただけ。

| # | 元の行(棚卸し) | 直した所 | 値の側に残したもの |
|---|---|---|---|
| A1-1 | A §4-1 decision-inventory #34 の帯「0.14〜0.79」 | `perception/attention.py` の p_see の定数の上にコメント(実装は 2 帯・0.79 は無い) | 棚卸しの写しの値(decision-inventory は行番号の注だけ触れる約束=値は直していない) |
| A1-2 | A §4-1 台帳 W15#4「上位 2 件・目印 2 件」 | 台帳 W15#4 の why に注・`perception/channels.py` の B2.visible の上にコメント | 件数(凍結文 2 件・合成文 3 件)=仕分け待ち |
| A1-3 | A §4-1 B5.near_person の max_items=3 | `perception/channels.py` の B5.near_person の上にコメント | 描画の `max_items=len(near)` と宣言 3=仕分け待ち |
| A1-4 | A §4-1 役割語の行「権限があるときだけ成立」 | `perception/templates.py` の `ROLE_WORDS_LINE` の上にコメント | プロンプトの文(値の側=変えると結果が動く)=仕分け待ち |
| A1-5 | A §4-1 `RESULT_OPTIONS` の注「待機を必ず含む」 | `perception/renderer.py` の注を「語彙 v1/v2 の表」と書き、v3 は `RESULT_OPTIONS_V3` が待機を「なし」に畳むと足した | なし |
| A1-6 | A §4-1 `DEFAULT_VOCAB_VERSION` v1・`role_words=False` | `perception/templates.py` の `DEFAULT_VOCAB_VERSION` の上にコメント(単体の描画の既定とランの既定が別) | 既定を 1 つにするか=仕分け待ち |
| A1-7 | A §4-1 `agents/state.py:316`・BR-REFRACTORY-OVERHEARD「同一話者 30 分は C2 未実装」 | `agents/state.py` の傍受の行のコメントに注・台帳 BR-REFRACTORY-OVERHEARD の why に注 | 会話の招待の間隔 30 と同じものか=不明=仕分け待ち |
| A2-1 | A §4-2 `change_detect.py:40-41`「知人出現・近接入替・被注視・傍受は C2 では検出しない」 | docstring の expedient の項 4 を書き直し(知人出現は関係の層・決定は BR-WAKE-CONDITION-CLASS・項の数 4 のまま) | なし |
| A2-2 | A §4-2 crowd の `queue_rows` の注「配線していない」 | `engine/processes/crowd.py` の Note を「配線済み(`systems/perceive.py`)」に | なし |
| A2-3 | A §4-2 tci の行番号(p_notice・agents/state・llm_bridge・renderer・llm/contract) | tci の #1・#24・#34・#41・renderer の行に「11-03 行番号の注」 | なし |
| A2-4 | A §4-2 decision-inventory #35・#90・#96 の行 | decision-inventory の 3 行に「11-03 行番号の注」 | なし |
| A2-5 | A §4-2 `llm_bridge.py:14-16`「待機へ落とす」 | 正典の項を「安全弁の語(v1/v2 は待機・v3 は「なし」)」に | なし |
| A2-6 | A §4-2 `templates.py` の `KIND_WORDS` の注 | コメントに注(W16 の 4 種は来街者の語で描かれる・台帳に行が無い) | 4 種別の語=仕分け待ち |
| A2-7 | A §4-2 `renderer.py:47-51`「150 tok は B2 全体の予算と読む(親判断待ち)」 | docstring に「未決のまま=仕分け待ち」 | 判断待ちのまま |
| A2-8 | A §4-2 `templates.py:9` の B0 300 | docstring に「正典の写し・実効のゲートは群の予算」(値の主張は足していない) | なし |
| B1-1 | B §4-1 `EAT_DWELL_MINUTES` 20 が使われない | `engine/resolve.py` の定数の上にコメント | 食事の所要時間=仕分け待ち |
| B1-2 | B §4-1 `D_TALK_METERS` ≈1 m と 2.0 m の 2 本の定数 | `engine/conversation.py` の定数のコメントと docstring の d_talk の項 | 1 本にまとめるか・値=仕分け待ち |
| B1-3 | B §4-1 参加上限 3(契約)と 2 | `engine/conversation.py` の `MAX_PARTICIPANTS` のコメント | 既定=仕分け待ち |
| B1-4 | B §4-1 `_BOARD_KEEP_ACTIONS` と実装(B5) | `engine/resolve.py` の定数のコメント | どちらに合わせるか=仕分け待ち |
| B1-5 | B §4-1 Q20 と `sleep_pending`(B5) | `engine/resolve.py` の `_SLEEP_KEEP_ACTIONS` のコメント | 就寝の意図に広げるか=仕分け待ち |
| B1-6 | B §4-1 `_payable` と列の現金だけの判定 | M28 として直した(§1・既定 on) | legacy は旧値 |
| B1-7 | B §4-1 応答率 0.8 の抽選(`conversation.py:423` の `_accepts`) | `engine/conversation.py` の docstring の項と定数のコメントに「死んでいる道」・台帳 `DOC-fix4-dead-accept-probability`(消していない) | 次の版上げで消す |
| B1-8 | B §4-1 重要度上位 +2 呼 | `engine/conversation.py` の定数のコメント・台帳 `DOC-fix4-dead-important-extra-turns`(消していない) | 次の版上げで消す |
| B1-9 | B §4-1 合成 POI の受け入れ数 4 を本番でも使う | `world/assets.py` の `SYNTHETIC_POI_CAPACITY` のコメント | 本番の値=仕分け待ち |
| B2-1 | B §4-2 HD-engine.resolve-1af925f4 の 6 項が古い | `engine/resolve.py` の docstring の 6 項を書き直し(移動の幾何の腕 node・edge・nav1・鉄道の過程を渡したランの乗車と降車・会話は招待の成否と活動の欄だけ・日次内省は数えるだけ・断るの「C2 では」を外した)。項の数 6 のまま・台帳の why に注 | なし |
| B2-2 | B §4-2 commit の σ_ln=0.20・m_att「C3 で入れる」 | `engine/commit.py` の項を「入っていない(δ_perc は予期クラスの定数のまま)」に | なし |
| B2-3 | B §4-2 conversation の「d_talk の代理=同一セル ∧ 双方 idle」 | docstring の項を書き直し(届くかは呼び手が渡す・相手の idle は見ない)・台帳の why に注 | なし |
| B2-4 | B §4-2 `call_budget_per_tick`「L4 の制御目標」 | `engine/arbiter.py` の docstring を監査線の書き方に(CLI の既定は上限なし・按分が上限になる場合) | なし |
| B2-5 | B §4-2 crowd の `queue_rows`(A2-2 と同じ) | A2-2 で直した | なし |
| B2-6 | B §4-2 tci #18〜#20・#22・#25・#26 | tci の 6 行に注(resolve の定数の行・`engine/body/rules.py` へ移った 2 つ・既定の空間の腕は nav1) | なし |
| B2-7 | B §4-2 棚卸し 10-31 の行は今の HEAD でもほぼ合う | 変えていない | なし |

行番号の注は作業木の今の版の行(本段の編集の後)で書いた。

## §4 試験

- 新しい試験 `tests/engine/test_defect_fixes_1103.py`(39 本): 切替口(既定の腕と名の検査・見出しと再開の突き合わせ・`run_day` の引数に無い)・M10(`end_conversation` と `revert_conversation` の対・会話の系を小さな箱で回す on/legacy の対)・M11(並んだ体の移動・別のセルへ置かれた体・乗車でホームへ歩く体=on/legacy の対)・M28(偽の口座の台帳で on/legacy の対)・M16(届かない承諾=名指しあり・なし × on/legacy・会話でない返事は今のまま断り・`drop_pending` の起点の計数)・M10 の招待側の戻し(返事待ちの間に MOVING になった招待側が期限切れで既定は MOVING のまま・legacy は IDLE/CONVERSING のまま待っていた招待側はどちらの腕でも IDLE/断られた SHOPPING の招待側が既定では残る=`_settle_pending_invites` の末尾・各 on/legacy の対)・検収の直し(中-2 対象の決まらない会話を選んだ寝ている体は既定で寝たまま=計器の原因 no_target・低-2 同じ呼び出しのうちにセッションに入った体を戻さない・中-1 招待の後に被招待が別のセルへ動いてから承諾=帳尻が両方の腕で合う・低-4 起点の計数の鍵 unreachable は腕 on のランだけ最初から置く・原因の名の検査)・ランの全体(manifest の節・再開の拒否 2 方向・CLI の名の検査)。
- 既存の試験の直し(期待値の更新は、どれも legacy の側で前の値が出ることを確かめてから=下の「legacy で確かめた」):
  1. manifest の末尾の鍵の並び(節 `defect_fixes_1103` を末尾に足した=腕に依らず出る): `tests/engine/body/test_body_manifest.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/time/test_t0_tm9_fields.py` と凍結の一覧 `tests/engine/time/manifest_keys_frozen.json`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/perception/facts/test_percept_schema.py`・`tests/engine/test_env_and_sections_10f.py`(`DF13_KEYS`)。
  2. 設定の節の道筋の指紋 `CONFIG_PATHS_SHA256`(`tests/engine/test_env_and_sections_10f.py`): `defect_fixes_1103.fixed`・`fixes`・`mode`・`schema` の 4 本を足した(前 `0e6dfaaa…81f9ec69`=この 4 本を外すと前の値)。
  3. 状態台帳の持ち主の欄の網羅(`tests/engine/test_state_ledger_10b.py` の 4 本・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py` の 4 本): 会話マネージャの新しい 3 欄を行 O41・CT1M に登録して通った(試験は直していない)。
  4. 既定の結果の golden(既定 on で動いた=legacy で前の値が出ることを確かめてから張り替えた・注に前の値と戻し方): `test_state_ledger_10b.py` の `CUR_SYN` v1・v3・v2_edge_attention・all_arms・`T7_V3_FINAL`・`test_presence_executor.py` の差し替えの世界の行 6 値・`test_nav1_world.py` の 3 値・`test_relations_tenure.py`・`test_state_checks_10f.py` の `K19_V3_FINAL_COUNTER`・`tests/perception/test_near_tiebreak.py` の古典 1,500 体・`test_env_and_sections_10f.py` の写しの 3 値。`test_t7_legacy_switch_reproduces_the_pre_bump_final` は張り替えず、旧道の切替口を 3 つ(率の規則・「無い」の過程・本段)とも legacy にした(版上げの前の値 `7bfe215641b792ac`/62,176 のまま)。
  5. つなぎの台帳の土台の行の指紋(`tests/bridging/test_decision_rows_1101.py`・§5)。
  6. `tests/engine/proximity/test_runs.py` の `HEAD_GOLDEN`(300 体・腕 cell): legacy で前の値 `2b342b34…a8ea90a6`/2,422 が出ることを確かめてから `a50ab61a…21ef9611`/2,416 に。
  7. `tests/engine/test_fleet_wiring.py::test_conversations_need_awake_partners_so_night_only_runs_barely_open_any`: 全員が「会話 対象: P-1」と答える合成の 200 体のランで、昼の側の窓 600 刻み(`CONV_TICKS`)の成立が 1 → 0 になり `d_open > n_open` が落ちた。原因(検収 中-2 で訂正): 旧道は「対象の決まらない会話」を選んで失敗した寝ている体も招待側の戻しで `IDLE` にして起こしていた(この 600 刻みで直した道が戻さなかった体=原因 `no_target` の SLEEPING 126・IDLE 151)。直した道では寝た体は寝たまま。試験の意図(真夜中の窓では開かない・朝を含めば開く)を保つため、昼の側を 1 日(`STEPS_PER_DAY`)に延ばした(既定で成立 6・旧道 600 刻みでも試験は通る=確かめた)。
  8. 招待の帳尻の恒等式(`tests/engine/test_conversation_invite.py` の 2 か所・`tests/engine/test_fleet_wiring.py` の 1 か所): `c.get("conv_pending_unreachable", 0)` の項を足した(腕 on のランだけ出る鍵=検収 中-1)。

legacy で確かめた値(5,000 体・seed 1・1 日・mock・`SHIBUYA_DEFECT_FIXES_1103=legacy` で回して前の golden と一致 → 既定 on の新しい値):

| 構成(試験) | legacy(=前の golden) | 既定 on |
|---|---|---|
| v3(T7・K19・presence v3・nav1 既定) | `73aa01d9afb206d0` / 61,066 | `c8d68704b7b0760d` / 60,939 |
| 帰無腕(presence null) | `2767525651ddb7ce` / 101,035 | `2875768fc19e02e8` / 95,645 |
| 帰無腕 hunger v1 | `37fe9e3db225e9a8` / 97,047 | `0d7100b43a0d591c` / 93,187 |
| 帰無腕 l4x1 | `9df2be95f55a809a` / 40,835 | `5b6024762b1431d6` / 40,875 |
| v3 hunger v1 | `09ff5fd88bb4bc09` / 60,375 | `41f2cfaa2f750081` / 60,341 |
| v3 l4x1 | `335f80ac58b648e0` / 36,350 | `b57ce0f65ffd628f` / 36,441 |
| nav1 密度 cell | `7b976b2272ef57e4` / 62,600 | `ab503d82e499ccfe` / 62,543 |
| nav1 密度 unscaled | `7a27bf218610714c` / 60,191 | `2d1c84ef289fb54d` / 60,211 |
| 関係 on(v3・記憶 on) | `8db3f95a61228c92` / 63,710 | `477e22fcaed2590a` / 63,519(検収の直しの前は `ebe0ce39b70fc2c0`=低-2 の書く直前の会話中の除外が返事の解決で 2 体に当たった・呼数は同じ) |
| 古典 1,500 体(near_tiebreak) | `fa919b1a…dfc48f1b` / 24,734 | `12a1b549…aef7945f` / 24,686 |
| 合成の世界 `CUR_SYN`(state_ledger_10b の T1) | v1 `a36995c487c3f214`・v3 `92290af2f272b811`・v2_edge_attention `863d35e1bfdb55f9`・all_arms `246c6478620d4cce`(legacy の環境変数で回して試験が通った) | v1 `ea16e1af840583d4`・v3 `7c9db9611874691c`・v2_edge_attention `1b9ce45df4c8dd92`・all_arms `2406ca74eed3422d`(classical は不変 `22d8c5ba98bfaca0`) |
| 近接 300 体 腕 cell(proximity の HEAD_GOLDEN) | `2b342b34…a8ea90a6` / 2,422 | `a50ab61a…21ef9611` / 2,416 |

- 帰無腕(語彙 v1)は呼が 101,035 → 95,645(−5,390)と大きく減った。【推測】v1 の帰無腕は招待が流れる件数が多く、旧道では招待側の戻しで起こされた・止められた体の再起床が呼を足していた。

範囲の試験(`tests/engine tests/llm tests/world tests/bridging tests/core tests/perception`・tests/c7 は除く・`-n 6`): §4-1 の結果の行を見る。

### 4-1 範囲の試験の結果

- 最後の src(検収の直しの後)で `tests/engine tests/llm tests/world tests/bridging tests/core tests/perception`(`-n 6`・byte-check と並べて回した): **4,116 passed・1 skipped・2 failed**(48 分 11 秒)。
  - `tests/engine/test_change_detect_p6.py::test_p6_change_detection_under_2ms_at_400k_agents`: 壁時計の門(2.546 ms > 2 ms)。byte-check と並べた負荷の揺れ=単独で回して 11 passed(コードは直していない)。
  - `tests/engine/test_relations_tenure.py::test_relations_on_arm_golden_old_and_new`: 関係 on の golden が `ebe0ce39…` → `477e22fc…`(呼数 63,519 は同じ)。原因は検収 低-2 の書く直前の会話中の除外(探りで返事の解決の 2 体に当たった・会話の系は 0)。legacy で前の値 `8db3f95a61228c92`/63,710 が出ることを確かめてから、この試験と `test_env_and_sections_10f.py` の写しを張り替え、2 ファイルを回し直して 27 passed。
  - 直したのは試験の値だけ(src は変えていない)=範囲の全体の回し直しはしていない(合わせて 4,118 passed・1 skipped・0 failed の見込み)。
- 前の回までの経緯: M10 の招待側の戻しの前の回は 4,102 passed・3 failed(軸 1 の AST の検査=計器の欄を持ち主の外で読み書き→メソッドに直した)。招待側の戻しを足した回は 4,109 passed・2 failed(近接の HEAD_GOLDEN と会話の成立の試験=§4 の 6・7)。
- 本段の新しい試験 39 本。範囲の外で回したもの: なし(tests/c7 は除いた)。

## §5 台帳の行と指紋の更新

- つなぎの台帳 `docs/design/bridging-ledger.json`(791 → 794 行): DEC の行の前に 3 行を足した=`DOC-fix4-defect-legacy-switch`(切替口 legacy・next-bump・plan)・`DOC-fix4-dead-accept-probability`(応答率 0.8 の抽選=死んでいる道・next-bump・inferred)・`DOC-fix4-dead-important-extra-turns`(+2 呼=死んでいる道・next-bump・inferred)。4 行の why に注=`W15#4`・`BR-REFRACTORY-OVERHEARD`・`HD-engine.resolve-1af925f4`・`HD-engine.conversation-1af925f4`。
- 見出しの行(HD-*)の項の数は変えていない(resolve 6・conversation 7・change_detect 4=docstring の項の文だけ書き直した)。`tests/engine/bridging/test_bridging_ledger.py` の見出しの合計 368 と形ごとの数はそのまま通った。docstring の `expedient:` の段落(第 3 形)は触っていない。
- 土台の DEC 以外の行の指紋 `tests/bridging/test_decision_rows_1101.py`: `BASE_ROWS` 679 → 682・`BASE_ROWS_SHA` `eaf4d8e7…bdb` → `c5e005b5fb1929da4e8efc7078f026379f5e4c4b8cdcb29b009a1852eeee82c3`(変えた行=上の 3 行と注の 4 行)。台帳の書き方は前と同じ(`json.dumps(indent=1, ensure_ascii=False)`+改行=手の編集の前に往復で一致を確かめた)。
- 状態台帳 `engine/state_ledger.py`: 行 O41 に `conv.n_pending_unreachable`・`conv.n_end_kept_activity`・`conv.n_revert_kept_activity`、行 CT1M の `contact.chats.*`・`contact.calls.*` に同じ 3 欄(診断=ハッシュに入らない)。設定 `count_unreachable` は conv・contact.chats・contact.calls の設定の除外(CONST)に足した。CT1M の注を「診断 3 欄」に直した(検収 低-5)。`LEDGER_VERSION` は上げていない(状態のファイルの中身が変わらない=前例と同じ扱い)。
- tci と decision-inventory: 行番号の注だけ(§3 の A2-3・A2-4・B2-6)。

## §6 byte-check

道具 `docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py`(5,000 体・seed 1・1 日・mock・テープつき)。`--only w6_v3_default,v3_mem_store,v3_classical,v3_classical_mem_rel --jobs 2`。土台は本体の src(`a800790`=label `base_a800790`)、作業木は `--src` に作業木の src。legacy の側は環境変数 `SHIBUYA_DEFECT_FIXES_1103=legacy` を side の環境に置いた(side は `os.environ` を写して `one` の子に渡す=子の組み立てが読む)。道具の `SWITCH_ENV` にこの変数が無いので、side の JSON の `env` 欄には出ない(道具は本段で触らない約束=compare の `note` に書いた)。最後の src(検収の直しの後)で回し直した値(前の回=招待側の戻しを足した後と 4 構成とも同じ値)。

| 構成 | legacy と土台(25 欄) | 既定 on と土台: 動いた欄 / final / 呼数 / 食事 / 行動の件数 |
|---|---|---|
| w6_v3_default | 25/25 同じ | 13 欄 / `73aa01d9afb206d0` → `c8d68704b7b0760d` / 61,066 → 60,939 / 4,124 → 4,164 / 183,192 → 184,009 |
| v3_mem_store | 25/25 同じ | 13 欄 / `0896589bae7ab302` → `2df5703f853f18d4` / 61,066 → 60,939 / 4,124 → 4,164 / 183,192 → 184,009 |
| v3_classical | 25/25 同じ | 0 欄(25/25 同じ・`5be0188ea16db82c`・89,941) |
| v3_classical_mem_rel | 25/25 同じ | 13 欄 / `c096c9472f755393` → `ea3047ab705ac9e2` / 101,076 → 100,942 / 9,326 → 9,382 / 341,411 → 340,722 |

- 既定 on で動いた 13 欄: final・calls・blocks_rows・blocks_sha・calls_rows・calls_columns_sha・action_usage_total・action_usage_sha・calls_by_condition・meals・behavior_last・full_last・end_of_day。動かなかった 12 欄: calls_column_names・salient_events・collapse・noticed・dispatches・arrived・mean_delay_min・start_sim_datetime・replay_date・calendar_weekday・rng_scheme・frozen_sources。
- v3_classical が動かないのは、この構成で会話と乗車と並ぶが 1 件も無い(土台の side の行動の件数=会話・乗車・並ぶの鍵が無い)ため=M10・M16・M11 の乗車の道が通らない。列(購入 1,484・食事 11,432)はあるが列を離れる体も口座払いも出なかった【推測: 古典は満席で並んだ後に歩き出す判断をしない】。
- compare の JSON: [compare_base_vs_fix4_legacy.json](bytecheck/compare_base_vs_fix4_legacy.json)・[compare_base_vs_fix4_on.json](bytecheck/compare_base_vs_fix4_on.json)。side の JSON 3 本も同じ置き場(絶対パスは無い=grep で確かめた)。

## §7 性能(10-13b §0-7)

5,000 体 × 1 日・mock・seed 1・CLI の既定(`cli.main(["--llm", "mock"])`・本段の腕だけ `--defect-fixes-1103 legacy` を足した)。測り方は [s2e-1102 §6](../s2e-1102/README.md) と同じ(壁時計=`cli.main` の前後・刻みあたり=壁時計 ÷ 実行器の `n_steps`=1,440・最大メモリ=Windows の最大の作業集合 `PeakWorkingSetSize`・10^6 B を MB とした・判断モデルの呼数は 0=mock)。1 本ずつ単独で、土台 → 既定 on → legacy の順を 2 巡(ほかの重いランを止めてから)。土台は本体の src(`a800790`)。道具は作業用の置き場の使い捨ての写し(リポには入れていない)。

| 版 | 壁時計[秒] 1 巡/2 巡 | 刻みあたり[ms] | 最大メモリ[MB] | 呼数(LLM) | final |
|---|---|---|---|---:|---|
| 土台(`a800790`) | 62.8 / 61.8 | 43.6 / 42.9 | 515.5 / 479.8 | 61,066 | `73aa01d9afb206d0` |
| 本段の既定(on) | 60.5 / 61.8 | 42.0 / 42.9 | 519.7 / 526.7 | 60,939 | `c8d68704b7b0760d` |
| 本段の legacy | 57.9 / 61.4 | 40.2 / 42.6 | 532.5 / 513.3 | 61,066 | `73aa01d9afb206d0` |

- 既定 on は同じ巡の土台と壁時計 −2.3〜0.0 秒・最大メモリは巡ごとに上下(+4〜+47 MB・土台の 2 巡の間でも 36 MB 揺れた)=揺れの中。悪化は見えない。
- 今回は 3 本とも前の回(M10 の招待側の戻しの前・土台 37.5/37.8 秒)より 1.6 倍ほど遅い。土台も同じだけ遅いので機械の状態の違いと見る(【推測】ほかの作業が機械を使っていた)。3 本の差は同じ回の中で比べる。前の回の値: 土台 37.5/37.8 秒・on 37.8/37.8 秒・legacy 37.4/37.7 秒(on は M10 の招待側の戻しの前の版)。
- CLI の既定のランの final と呼数は byte-check の `w6_v3_default`(テープつき)と同じ値。計器も §1-1 の表と同じ。

- 検収の直し(11-03 の 3 回目)の後は既定の final が変わらなかった(`c8d68704b7b0760d` / 60,939)ので、性能は測り直していない(親の指示=既定の final が変わったときだけ)。

## §8 できなかったこと・【推測】

1. **会話の番で別の行為を選んだ体をセッションから外す配線**(`conv.step` に `in_conversation` を渡す)はしていない(発注どおり=本人の判断の口の設計に関わる=仕分けへ)。直した M10 は「終わったときに活動を巻き戻さない」だけで、歩き出した体がセッションに残ることは変わらない(セルを離れる・寿命で閉じるまで)。
2. **同じ刻みの列の捌きと新しい行為の順**: `apply` は列の捌き(`_serve_poi_queue`)を新しい意図の適用より前に回す。並んでいた体がこの刻みに「移動」を選んでも、その前に席が空けばまず席に入って払い、その後に歩き出す(歩き出しで在席の印は解ける=seat_release walk)。発注は「歩き出したときに列を離れる」なので、この順は変えていない。【推測】頻度は小さい(既定のランで列を離れた体は 9)。この刻みに移動・乗車を選んだ体を捌きから外すかは仕分けへ。
3. **M10 の頻度の数え方の食い違い**: 解消(親の計測の範囲の誤り=`revert_conversation` の 3 か所を全部数えていた。親が呼び出し元ごとに数え直して、会話の終わりは実装役の探りと一致=§1-1 の表)。親の判断で、招待側の戻し 2 か所も同じ切替口・同じ版上げに含めた。
4. **W16 の世界の golden の行**: `tests/engine/test_presence_executor.py` の W17 の表のうち W16 の世界の行(`3113e9ba7abb`)と、ほかの環境の行は張り替えていない(この機械の世界は差し替えの世界=`02114fb577f3` の行だけが試験で使われる)。本段の既定で動くはずの値だが、回す世界が手元に無い=空欄。
5. **byte-check の side の JSON の `env` 欄**: 道具の `SWITCH_ENV` に `SHIBUYA_DEFECT_FIXES_1103` が無いので legacy の side の JSON に腕が出ない(道具は本段の編集の範囲の外=触っていない)。legacy であることは compare の `note` と、final が土台と 4/4 一致することで示した。次に道具を触る段で 1 行足すとよい。
6. **状態台帳の版**: 会話マネージャの 3 欄を行 O41・CT1M(診断)に足したが `LEDGER_VERSION` は上げていない(どちらのハッシュにも状態のファイルにも入らない=前例の仮採用と同じ扱い)。上げるかは親の判断。
7. **値の側の 15 件**(§3 の「値の側に残したもの」)は注を足しただけで、値・プロンプトの文は変えていない=仕分け(11-03 §2)待ち。死んだ道 2 本(応答率 0.8・+2 呼)は台帳に印を付けただけで消していない(次の版上げ)。
8. 記録の文(本書)は yomiyasu の推敲をかけていない(親が出すときにかける前提)。
9. **列を離れない歩き出し(M11 の残る道・検収 低-3)**: 計画の就寝で就寝地へ歩き出す体(`resolve.begin_planned_sleep`)・本人の予定で歩き出す体(`resolve.begin_walk_to`)・カレンダー 2 の歩き出し(`engine/calendar2/layer.py` の歩く口)・乗車でホームに居た体(`_apply_board` の `on_plat`)は列の印を消さない。コードは足していない。安全網は給仕の前の居場所の確かめ(`n_queue_dropped_away`=店のセルに居なければ列から外す)で、既定のランでは 0 件。`engine/defect_fixes_1103.py` の M11 の行にも同じ宣言を書いた。
10. **招待の帳尻の残りの穴**: `resolve_pending` で承諾が門(会話中)で落ちた分は `gate_rejected` に入り、恒等式 招待 = 成立+断り+期限切れ+未決(+不成立)の項に無い(既定のランと土台でどちらも 1 件)。本段の前からの形。直すかは親の判断(試験の恒等式は小さな世界では当たっていない)。
11. **起点の計数の鍵(検収 低-4)**: `track_origins` は最初から全部の鍵(invites・accepted・declined・expired・rejected)を 0 で置く作りだった。腕 on のランでは `unreachable` も最初から置くように揃えた(旧道は鍵を足さない=出力は 1 字も変えない)。
12. **再開と診断の 3 欄(検収 低-6)**: 会話マネージャの 3 欄(`n_pending_unreachable`・`n_end_kept_activity`・`n_revert_kept_activity`)は状態台帳の診断(discardable)なので、状態のファイルに入らず、再開のランでは 0 から数え直す(通しのランの値とは一致しない)。記録だけ。

## §9 親の検収(第343)

- **別の検収役**(実装を見ていないサブ・Opus 5.5): 条件つき受入=中 2(招待の帳尻に不成立の項が無い・M10 の続きの原因の説明が実測と違う=大半は対象の決まらない会話の失敗)・低 6。中 2 と低 1・2・4・5 はコードで直し、低 3・6 は §8 に宣言した。旧版で保存した状態からの再開(legacy は通しのランと final 一致・on は腕の違いで止まる)と、文書だけの直しで値とプロンプトの文字列が変わっていないことは検収役が確かめた。
- **親の範囲の試験**(最後の src・単独・`-n 6`・tests/engine tests/llm tests/world tests/bridging tests/core tests/perception): 4,118 passed・1 skipped・0 failed。
- **親の byte-check**(4 構成・土台=本体の src・最後の src の on と legacy): legacy は 4 構成とも土台と 25/25 同じ。on は w6_v3_default・v3_mem_store・v3_classical_mem_rel で 13 欄が動き(final・呼数 −127/−127/−134・食事 +40/+40/+56)、v3_classical は 25/25 同じ。実装役の値と一致。比較の JSON は [bytecheck/parent_cmp_base_vs_legacy.json](bytecheck/parent_cmp_base_vs_legacy.json)・[bytecheck/parent_cmp_base_vs_on.json](bytecheck/parent_cmp_base_vs_on.json)。
- **状態台帳の版**(§8 の 6): 上げない(前例=6-4 の連絡の道具も診断の欄を足して上げなかった・検収役が再開で確かめた)。
