# PENDING — 未実装・実装中・ユーザー判断待ち

> 本ファイルは **まだ終わっていないもの**だけを持つ。完了済みは → **[IMPLEMENTED.md](IMPLEMENTED.md)**(決定の履歴も同所の年表と git log が正典)。
> 索引と最終更新は → **[STATUS.md](STATUS.md)**。
> 最終更新: **2026-08-21**(第145後の全面更新: 8/14以来の棚卸し。①実装中=FACT-D/INV-A/B/C(サブ走行中)+CRWD/PRICE-B(次)②物理P1/P3/P4=消化(夕方step対策・累計-81%ベンチ)③判断待ちを「8/22統合判定ラウンド」に集約④日程を現行(開始目標8/22深夜〜8/23・最終線8/23夜)へ)。

---

## 1. 運用中・未着手レーン

| レーン | 内容 | 状態 |
|---|---|---|
| **RW-U1 運用** | タスクスケジューラ稼働中(`shibuya-rw-fetch-daily` 毎日12:00)。残=①規約再確認(R3)②本選中は `--report` の欠け監視を時々目視③本選後の解除 `Unregister-ScheduledTask` | 稼働中 |
| 物理ベンチ較正レーン(旧称P4・※第145の格子有界化P4とは別物) | D(J/w 水準)の原因切り分け・高密度の壁貫通脱出(接触項 or v_max クリップ再設計) | 未着手(任意) |

## 2. 計画済み(実装の残りがあるもの)

| 項目 | 残り |
|---|---|
| **★INV/FACT-D/CRWD/PRICE(第145計画・全承認済み)** | [inventory-two-tier-plan.md](docs/plans/inventory-two-tier-plan.md)。conf一式(E1混雑プロキシ廃止/PRICE-C価格固定/PRICE-A卸値較正/P1)=**適用済み(81bcd7a)**。**実装中(サブ走行)**=FACT-D(fact重複抑制・truth_ledger)+INV-A/B/C(2層在庫+店員shelf_restock行動+店主発注行動+棚知覚)。**次**=CRWD(混雑不満・閾値つき飽和・nightlife U字)+PRICE-B(時間帯価格+閉店前見切り=店員行動)。検証=劣化ckpt-72 resumeプローブ→フル1日リハ |
| **★物理 夕方step対策(triage計画§0)** | [afternoon-slowdown-triage-plan.md](docs/plans/afternoon-slowdown-triage-plan.md)。P1(update_every30)/P3(_box3同値高速化)=**コミット済み**・P4(格子有界化clip_margin_m:10)=**実装・検収済み(コミット待ち=次バッチ同梱)**。ベンチ累計=physics.phase 48.5→9.4s/step(-81%)。残=25k夕方帯の実測(ckptプローブ)と250k縦煙での確認 |
| **WIT witness再設計** | **WIT-1+2=実装完了(第143/144)・世界不変性の25k証明済み(98/100種一致)・witness CPU除去は火炎図で確認(truth_ledger圏外)**。残=較正アンカー照合(Philpot 16.3人/件・認知率が100%から離れること)を1日リハで |
| **犯罪×LLM検証** | V0=mock実装完了(第109)。**V1/V2実LLM実測=本選後送り(ユーザー宣言2026-08-19・第140補2)** |
| **所有権レイヤー** | [ownership-layer-plan.md](docs/plans/ownership-layer-plan.md)。O1登記簿+O3相続=第109・**O4家賃=第114**(lease権利行・受け手=own行の家主・org/個人着金)。残=**O2家財L-agg・O5流通内生(売買代金)・敷金/住宅ローン(O4完全版)=本選後**。「持ち家なのにrent_shareを引かれる」件はO4完全版の持ち物 |
| **存在内生化POP** | **転出/転入(案A)/出生=実装完了(第114・35テスト)**。finals=出生ON。残=**転出/転入の8/15リハーサル**(1〜2日ラン+`summary.population.per_day`を現実レート7.8/8.4件日と照合→conf 2行ON)・案B(転入を新規個体で・初期関係値の設計が前提)=本選後 |
| **本選信頼性(STAB)** | [finals-reliability-plan.md](docs/plans/finals-reliability-plan.md)+第140補2(無停止化=デバッグ期間は置かずテスト+リハの型で代替・開始後不介入原則)。装備済み8項。**残=STAB残4項**: 信頼性リハ7本実走・vLLM自動復旧・RSS/ディスク閾値アラート・E4ドライラン+閾値/世代数の本選値化。★運用注意: `--resume`は落ちたラン専用/走行中run-dirへのrobocopy直がけ禁止/走行中run dirのrm厳禁/pgrepはブラケット記法 |
| **在場内生化PRES** | **A1+A2+B+C=実装完了(第111)**。残=**A2 emergent のON判断のみ**(8/15 RSS/R_eff実測後・finals confの1行) |
| **メタバース射影** | [metaverse-projection-plan.md](docs/plans/metaverse-projection-plan.md)。**GTロガーG1-G7=全部実装済み(第113・承認済み)**。残=射影フィルタF0-F4・復元実験3案=**本選後**。運用の掟=**checkpoint/dormant剪定禁止(G2)**・backup_run は `--ckpt-generations 999` で回す(既定2のままだと18世代が手元に残らない) |
| **AGE/DPH/RFX/v2の残り** | AGE-A〜F=**実装完了(第116)**・DPH-O/C/B=**完了(第115)**・RFX-A=**完了(第116)**。残=**①v2プール切替判断**(conf 1行・tier_quota再計算と縦煙が前提・待機ブロックに手順)②DPH-A(起床→就寝地平)=本選後 ③sleep_task_rewrite(就寝前テンプレ言い換え)=実LLM検収待ちOFF ④PPv2-G(workplace_scope/at_homeのengine接続)=判断待ち ⑤build_friend_graph O(N²)=30,000人で起動25分(Chung-Lu案が処方箋・本選後) |
| **Discord進捗報告** | **最小構成=実装完了(第116・--dry-run検収済み)**。残=**webhook URLの環境変数設定(ユーザー作業・ops/finals-compute-checklist.md §E2手順)**→初回--dry-run→本番投稿・GPU機のdiscord.com:443疎通確認(8/15環境確認項目) |
| **アクターモデル移行** | **GTFS実発車=第114で完了**(1,810本・朝+18%)。残(本選後): SoA配線(乱数キー判断が前提)・店主行為化(1-2週規模)・PoA観測(片肺実装は誤読を生むため一括)。OPEN: PoA/§4.5 |
| **身体と事件レイヤー** | chance.py の**コード削除**=本選後(運用退役は finals conf で済み)。設計上の残は §4「身体と事件の残」 |
| DP-U2/DP-U3/S-quick/DTスナップショット | 8/15-16 診断ランでの実測待ち(vLLM同居・R_eff/RSS・σ再実測)・S-quick は承認待ちのまま |

## 3. ユーザー判断待ち

### ★8/22 統合判定ラウンド(数字が揃い次第・一括提示予定)

| # | 事項 | 判断材料の状態 |
|---|---|---|
| J1 | **cap最終値=平均step時間の設計**: 1,440step×平均6分=6日で完走(8/23開始でも間に合う)/平均10分=実時間10日=完走が提出8/30を超過→「完走必達なら6-7分」か「提出時点7-9日分で提出」か | 期限算術は提示済み。1日リハの実測平均で最終判定 |
| J2 | ATT層AのON値(hear×0.029の25k実データあり・k_i≈4±2)・層Bの採否 | 実データあり |
| J3 | S7 `memory.relations_max`(500-2,000帯)・S15 聴衆上限 | conf 1行ずつ・即決可 |
| J4 | REL採否・OVL-1(朝計画×物理重ね)実装の要否・OVL-2採否(設計§4.6準備済み) | OVL-1は物理-81%で利得縮小=要再試算 |
| J5 | TRIM表(実測に基づくOFF候補の取捨) | 1日リハ実測後 |
| J6 | 250k init問題の白黒+finals ON範囲の最終値表(INV/CRWD/PRICE/carry_grid含む) | 250k縦煙(8/22)で |
| J7 | cognition.fire を開けるか(affects_k=True・呼数実測とセット) | 第113からの持ち越し |
| J8 | seed 2本目+GPU尾部(8/26-30)の使途配分(seed分散が無いと量的主張が落ちる) | 第113からの持ち越し・本選前 |
| J9 | Δt梯子(並行1-2万体×Δt=1)の採否 | 計画提示済み(8/12)・fire判断と連動 |
| J10 | policy_cache 保存判断(resume呼数差の実測とセット) | リハで実測可 |
| J11 | ~~エージェント発注裁量~~ **決定済み(8/22未明)=見送り・V2送り**(ユーザー決定「入れない方向性でいく」)。コード・conf無変更=追加検証ラン不要 | V2で経営エージェント(発注・価格・シフト・仕入先)へ拡張予定 |

### 単発の判断待ち

| # | 事項 | 状態 |
|---|---|---|
| **U-10** | 事前登録の閾値承認+10日ラン解釈方針([stationarity-preregistration.md](docs/plans/stationarity-preregistration.md)) | **本番直前に決定**(freeze時に承認依頼) |
| ~~OBS-U1/U3~~ | **決着(2026-08-14承認)**: finals ONセット承認・g_update ON・認知棚卸し再実行済み(第113=搬送漏れ4族追加)。残る fire 判断は上の独立行 | 済 |
| **Δt梯子の承認** | [dt-reduction-plan.md](docs/plans/dt-reduction-plan.md) 提示済み(2026-08-12): 本線25万×Δt=10+**並行1〜2万体×Δt=1**(驚き発火の解放=科学的動機・30秒は見送り推奨)。承認でDT-1〜3(呼数不変の機械固定・Δt=1プロファイル・運用)を実装。+並行ラン規模(1万or2万)と開始時期 | 承認待ち |
| **存在内生化POP** | [population-endogenization-plan.md](docs/plans/population-endogenization-plan.md) 提示済み(2026-08-12): 転入=案A(L4定着昇格)推奨/案B・実装=**本選後推奨**(10日ランでは0.03%)・出生=POP-3で含める推奨 | 承認待ち(3点) |
| **★cognition.fire を開けるか** | 第113発見: OBS承認で g_update ON にしたが **fire OFF では g_update は1行も出ない no-op**(plasticity は fire 前提)。fire は LLM呼の発生点が変わる **affects_k=True** の別項目のため未開放。開ける場合=呼数増の実測(8/15診断)とセットが筋。Δt5案の「思考層の利得ゼロ」も同根(fire ON なら Δt の科学的価値が復活する関係) | **新規(第113)・8/15判断推奨** |
| **★ラン計画: seed 2本目+GPU尾部(8/26-30)** | ユニークデータJ5/J6: 事前登録が「条件間差>seed間差」を要求するのに seed分散の入力ランが無い=**量的主張がほぼ全部落ちる**。`analyze_seed_variance.py` は実装済みで入力待ち。選択肢=(a)本線と並行で小規模seed違い (b)本線後の尾部でseed2本目 (c)尾部は反実仮想U15(分岐再走)に使う——**尾部の使途配分の判断** | **新規(第113)・本選前** |
| ~~**J1 共在ペア記録上限**~~ | `transit_interior.copresence.max_pairs_per_day: 8→24`(conf 1行・L1 +2〜3GB)。U13完全接触ネットワークの分母。**着地済み**(第114 レーン1c で本選 conf のみ 24 へ・理由コメント同梱)。動力学不変の機械検収 = `tests/test_transit_interior.py::test_daily_cap_only_changes_the_copresence_rows` / `test_daily_cap_is_binding_and_conserves_the_pair_total` / `test_finals_conf_raises_the_daily_cap`(第121 レーンB3 β3 で再走・緑) | **消化**(第114 実装 / 第117 再確認) |
| **home_awake の ON**(縦煙ゲートのみ) | **ユーザー決定済み(2026-08-16)**: ①lead=個体分布(per_agent・現実gap264分へ較正=mock実測257.3分/MAPE2.5%)②夜会話=開ける(evening_talk)→**第122で実装完了**。残=v2縦煙で(13b)ブロック解凍(★L1−27%/呼数−26%=夜の街が空くためpresence較正の不変確認が必須) | **縦煙後(機械ゲート)** |
| ~~同居人どうしの夜の自宅会話~~ | **決着(2026-08-16ユーザー決定=開ける)**: `evening_talk` として第122実装(同一世帯×両者在宅覚醒ペア限定・social/replyのみ+12.7%@60体mock)。home_awake ONとセット解凍 | **消化**(第122) |
| 賃金の残り2点 | ①最低賃金の床に27,740人(12.4%)が完全同一額で張り付く(現実にも最賃集積はあるが単一値スパイク)②家賃は実引落日(27日/末日)が10日窓に入らないため引落ゼロ=**savings_rate 0.555の帯超過は窓アーティファクトと記録済み**(機構は触らない判断=Fable)。異論あれば再検討 | 新規(第112)・小 |
| visit_purpose構成比のPT較正・曜日/雨弾性の水準較正 | PRES-A1の設計値を実測(PT調査・jinryu曲線)へ較正し直す別レバー(1レバーずつの規律) | 小・任意 |
| **policy_cache 保存判断** | checkpoint 未保存=resume で呼数と行動が変わりうる。推奨=8/15-16 診断で resume 前後の呼数差を実測してから | 本選前 |
| **回転搭載の判断待ち・残1件** | `implicit_self`+`behav_ema`(EMA の窓が回転を跨ぐべきかの意味論)。※`wv_expect` は第112乙B8で搬送済み=消化 | 第109・小 |
| beliefs の `--bin-steps` 既定24 | 唯一残った Δt 直書き(CLI 上書きで回避可)。直すなら 8/15 ハッシュ凍結前 | 小・任意 |
| NEW-5 | F/N/P 初期値条件の本選配分 | パイロット後に提案 |
| DT-U2 | UE5 デモ動画 | 保留(本選中判断) |
| ~~v2プール2系統分岐~~ | **ユーザー決定(2026-08-16)=「本番を回す直前に現HEADから再生成」した物がそのまま正典**(分岐原因の追跡より再生成で機械的に確定)。手順=別dir煙→meta照合→conf表/tier_quota引き直し→切替。既存2系統は再生成後に破棄可 | **決定済み・本番直前に実施** |
| ~~v2に配達員が不在~~ | **ユーザー決定(2026-08-16)=再生成に3職業(配達員/バンドマン/写真家)を追加**。生成器修正+再発防止テスト(confが名指しする職業の語彙検査)を実装レーンで進行中 | **決定済み・実装中** |
| ~~物理ゾーン痩身の方式~~ | **全消化(第135=A・第136=B+C・finals ON)**。A=セル法8kで95倍(ビット一致)・B=認知的近傍(密度上界・★硬い視野円錐は壁貫通=fov360が正)・C=密度場far(93-324倍・RMSE改善)。残メモ=ORCA LP純Python化(ビット同値不能で別判断)・密度場の壁無視(地下通路型で過大評価の可能性)・front_spacing(v_of_s=finals OFF) | **消化(第135/136)** |
| **本番開始の条件(凍結の扱い)** | **ユーザー方針(2026-08-16)**: 日付固定の凍結に執着しない。「現存の実装+今後本番に必要と判断される実装」を終えたら**できる限り早く**本番ランを開始する。→開始ゲート=①物理痩身(再提案→承認→実装+検証)②v2再生成③cap/fire確定④RAM線GO⑤U-10承認⑥launch手順E4 | **方針決定・ゲート消化中** |
| ~~**stock_threshold=6 の較正**~~ | **決着(2026-08-20ユーザー決定=E1廃止・第145でfinals適用)**: 混雑プロキシ廃止・品切れは実在庫へ一本化・混雑の不満はCRWD(文献準拠・行動は止めない)が後継 | **消化(第145)** |

### 決定済み(履歴の要点のみ・詳細は git log と IMPLEMENTED 年表)
2026-08-14(2回目): **GTロガー=全部実装**(→第113)/**OBS-U1/U3=承認**(g_update ON)/**b2b=Fable案**(部分納品+分散→第113)/**Δt=5案を計画・本番1本のみ**(並行ラン廃)/**POP=案Aで本線前試行**(イベント発生が主眼・厳しければ見送り可)/**所有権O2-O5・アクター残・判断不要小粒=できれば本線前**/新問い5題=計画まで/判断事項の選択肢+材料一覧化を要求。
2026-08-13/14: **痩せ=「くまなく検査して漏れがないよう修正」承認**(→第112甲/乙/丙で約40件根治)/**賃金多様性=実装承認**(月給/日給・振込タイミング・ボーナス・職種適合額→WAGE実装)/**メタバース観測データ検証=リサーチ+計画まで**(実装しない)。
2026-08-12: **org_id+bind_workplace=両方実装してON**(第109で実装完了)/**所有権3決定**(域内不動産org追加・相続承認・本線前実装)/**犯罪×LLM=Fable案採用**(検閲なし不使用・V0実装/V1V2は8/15)/**フリーズ=仮決定**(直前まで修正可能の認識)/**退避先=ローカルPC・外付けHDD**(クラウド/GPU機詳細は8/15)。
2026-08-11: 身体と事件4決定(死=現実量で実装・chance廃止・全部実装・保険RoW)。
2026-08-07: DP-U2=暫定案C/DP-U3=本線25万/SV-05=③/DP-U4=呼数/B3=換算しない/RW-U1=承認/凍結3本修正=承認(**8/15凍結の正ハッシュ `79a2e549486fe6ab5eea350334cbe37b4c712c12dbf75e41afea617939010d0f`**)/RW運用=スケジューラ。
2026-08-06 以前: IF-E2=案B/DP-U1=無償/SV残13=採用/PUB-U1/P2=ゾーン別ハイブリッド/NEW-1〜4・ID-U1〜U3 等(git 履歴参照)。

## 3.5 本番開始までの残工程(2026-08-21時点の実行順)

1. **実装の締め(今日8/21)**: FACT-D+INVサブ完了→検収→CRWD+PRICE-B実装→3レーン一括フルゲート→コミット(P4同梱)
2. **規模検証(今日夕方〜8/22)**: サーバーpull→劣化ckpt-72 resumeプローブ(夕方帯step前後比較・数十分)→フル1日リハ(25k×144step=平均step実測・欠品率8.3%帯/混雑不満分布の較正照合)→**250k縦煙**(init+夕方帯)
3. **STAB残4項**: 信頼性リハ7本実走・vLLM自動復旧・RSS/ディスク閾値アラート・E4ドライラン
4. **8/22判定ラウンド**(§3の表J1-J10)→**v2プール再生成**(3職業込み・正典化)→POPリハ→U-10承認→freeze_config
5. **本番開始**(目標8/22深夜〜8/23昼・最終線8/23夜): nohup起動→別ssh生存確認→Discord/監視配線→day-1チェック(新規フォロー/日/人・belief体積・RSS・step時間)
- 開始後(ブロッカーではない): 提出物=README+RESULTS骨格+プレゼン構成(8/25ごろ起草)・毎時モニタリング

## 4. 持ち越し小粒(未解決のみ)

- **新規(第159・ユーザー決定2026-08-25=本選後に実装)**: **来街判定のLLM化(マージン確認方式)**。現行=L4習慣カレンダー(統計較正の確率)。実現形=習慣カレンダーが期待の1.5-2倍の「行くかも」候補を出し、本人の記憶・関係・バックストーリー付きでLLMが行く/行かないを決める(10-15万呼/日・8B短呼・夜間窓)。**総量は統計クォータで守る**(8B宣言バイアス対策=SNCプローブでフォロー68%過剰の前科)・LLM故障時は習慣カレンダーへ宣言付きフォールバック。フルLLM化(79万呼/日)は艦隊容量超過で不可と結論済み。工数1.5-2日級。
- **新規(第158・ユーザー要望=本選後ロードマップ)**: **エンジン計算のGPU移行**(CuPy/torch)。対象=物理積分(SFM/ORCA・step時間の~51%)+知覚/カウント系(~27%)。下地は済み(第135セル法・第149ベクトル化=データ並列形)。前提=①vLLM常駐予約の縮小(gpu_memory_utilization)or専用GPU確保 ②CPU/GPU浮動小数点ビット不一致→物理ベンチ(基本図±20%・破綻統計)全面再検証 ③golden系テストの扱い設計。見積=移植+検証で最短2-4日級。B2(_apply speakのO(N)全走査)の索引化も同梱候補。
- **新規(第157補2)**: RT連鎖の**保存側**が無上限(post本文が「RT @A: RT @B: …」で日数とともに成長・現行対処はプロンプト側のfeed_item_max_chars=140截断のみ)→保存側を参照モデル化(原post_id参照+深さ上限)する検討=本選後。
- **新規(第155/155補の見送り小粒)**: ①physics_levers→physics:への畳み込み(conf整理のみ) ②G観測countの対数ビン化(観測値の意味が変わる=ユーザー判断) ③D(neighbor_cap7)導入に伴うP4基本図作業点+31%の再較正=本選後。

- **新規(第150・count_hearersサブの副発見)**: 第149 _hearers_boundedのベクトル化経路がnp.hypot==math.hypotを前提(docstring明記)だが実際は1 ULP差16%(第143で既知の罠)。ON経路のみ・実座標でmeasure-zero・同一ラン内は決定論なのでR1違反ではないが、count_hearersの±4 ULP帯裁定方式を本選後に移植してdocstring訂正。

- **新規(第146・FACT-Dサブの副発見)**: commerce の shop_state 開閉状態が checkpoint 未保存=境界が開店遷移 step にちょうど当たると resume が shop_state を 1 行落とす(第80 天気・第62 joint と同型・他の全行一致は実測済み)。修正=開閉状態の checkpoint 搬送 1 欄・本選前の小粒候補
- **新規(第145)**: ①IMPLEMENTED.mdバッチ年表が第137で停止(第138-145未転記=提出前に整理)②週次特売(小売価格変動の最大経路だが工程不釣合で見送り・PENDING)③待ち行列モデル+CRWD待ち成分(較正数値はリサーチ§9に記録済み・v2)④displacement創発の観測(混雑回避行動→「常連は寛容」統計の自然発生=論文観測ポイント候補)⑤PRICE-B配達員エージェント完全結合=本選後

- ~~第133ウェーブ2予定~~ → **第134で全消化**(A1 AgentRef/A2 vital台帳/watchdog/allow_dirty_outdir宣言/τ移植=analyze_structure+viewer両方)。**新規の残件**: ①**mem.relationsの削減**=AgentRef残サイズの75%(22.9KB/体)。読者2箇所のみ(gossip._seed_knowers/mobility._mutual_closeness)。案(a)=seed_contact_days以内+partner 1件だけ残す(読者の使用範囲と厳密一致・conf配管要) 案(b)=gossip/cohabit両OFF時のみ落とす(finalsは両ON=効かない)→**判断待ち** ②_vitalは設計どおり無制限増(1Mプールで~42MB・checkpoint毎にsidecar搬送=許容と記録)
- **A9残置: provenance transmissions list の無界性**(第133は counter併設+プロンプト参照差し替えのみ)。読者2(simulation.py:2356のsummary集計・test_rumorsのカスケード再構成)の付け替えとセットで別バッチ。25万×10日で~1億件=12GB級+checkpoint時間単調増
- **β7後方互換の残り窓**: 「COMPLETEマーカーが1つも無いdirは全候補許可」規則により、**最初の世代**の書き込み中クラッシュのみ未コミット本体が選ばれ得る(2世代目以降は第133で閉鎖)。塞ぐにはlegacy判定の作り直し
- **invariants実データ違反の残トリアージ**: pos_exit_without_enter 97件/287万(回転境界の既知クラスか要確認)。年齢系2種11件はv1プール起因=v2切替で解消見込み(v2の追加根拠)
- **RAM線への計上メモ(第133裏取りの規模再見積り)**: memory_daily日次バースト~8-9GB(60分内解放)・relations `_last` ~4-7GB単調増・SNS無界(posts_max=0)=follows/read_marks生涯46万キー。いずれも「在場でなく累計比例」族=10日は許容・延長ランでは要修正

- **第112の正直な限界5点**: ①truth_ledger.py:497,518 の幽霊解決は**凍結14本のため不触**(`_present()`が物理述語のため脱水個体を通す=`_fact_beliefs`が幽霊に書かれる・次のハッシュ変更に同梱)②途中入場者への友人グラフ適用は O(N²)で不可(dehydrate切り捨て問題のみ修復)③unbond は相手不在時保留(入場時整合で清算)④車両に rot_out 無し(退場者の車は「所有継続」と読む=O2耐久財寿命で再検討)⑤pool ONスモークの家計残差 rel 1.359e-06 は既存の丸め事象(旧挙動でも同値・|r|>0.5円の窓ゼロ)
- **σ_c の Δt 再測**(8/15-16 に統合)
- **finals プロファイル限定の未宣言トグル8件**(第109発見・既存の穴): `economy.bank.enabled`/`consumption`/`payment`/`vc`・`institution_routes.assembly.from_roster`/`.realism.enabled`・`memory.actr.enabled`・`prompts.dialog_history`=基底 conf に無いキーは registry 網羅テストが拾わない。機械的な宣言追加で塞がる
- **attach_record の本番コスト未実測**(第109): 台帳読み+25万回の dict 参照=8/15 の RSS/R_eff 実測に同梱
- **IF-E2 残**: ①窃盗の加害者への入金(挙動変化=独立トグル要・将来判断)②屋台の内税/床クリップギャップ(RoW が埋める)③b2b 買い手特定=一意率 4.5%(正直開示済み)
- **resume 整合の宣言済み限界**: `undefined_action_total` 等プロセス内カウンタ族=resume 後 0 から(checkpoint.py 明記)・`device_load` の時間内訳は resume 直後の1時間だけ過少(devices.py 明記・第109で1行差として実測確認)・凍結 `silence.py` docstring 6行は次のハッシュ変更に同梱
- **IF-C 残**: ①Item.transmissions 上限なし(25万ではホット噂 O(N)=別バッチ)②語り選択順(`max_per_talk=1`+古い順が律速)
- **P4 残**: J/w 未解明・壁貫通脱出・6変数同時最適化・ρ_meas 1.5 頭打ち
- **物理見積の残り**: 理論モード既定2つに根拠なし(実測外挿モードで迂回可)・混雑 dwell 未計上=下限側
- **3D 残り**: tracks.json は `--tracks-binary --no-tracks-json` が真の解・10日ラン実 RSS 未測
- **解析25万の残り**: ①`analyze_accounting` の events/flows は O(金額イベント数)(検査式に触れる別バッチ)②`row_group_rows` 既定 2^20 は本番前に実 L1 で再調整 ③W4-E 申告2点(ON=part 間スキーマ permissive 統一・indoor_tracks ON は +19GB)
- **Δt の残り**: L1 からの Δt 推定(pyarrow 依存で見送り)・旧ラン dt_min 無し=assumed 経路(仕様)・src 観測定数(凍結・8/15 以降)
- **W4-F の設計上の残**: `street` ブロックの帰属不能は仕様・`work_node` はスナップショット(受理集合の和で緩和済み)
- **身体と事件の残(第107・設計上の残のみ)**: 【H1】通報遅延分布は Δt=10 で同一 tick(payload 観測のみ)・死亡は発症時決定(治療→転帰の条件付けは別バッチ)・city_ops OFF では S3/S4 の物理表現なし【H2】医療機関 org 特定率=本番台帳で再測要・高額療養費/年齢別負担/病床数は未実装・H5 負傷者は搬送しない・S2 受診は移動を作らない【H3】落下ハザード=25万 ON 時は stride 化検討・resolve 1step 遅れ・落し物は知覚に出ない【H4】ペア確率=和近似・警察官を現場へ動かさない・detain_steps 既定0【H5】traffic 係数の本番規模再較正・延焼なし・群集は physics.zones ON のみ
- **`_dinner_logged` は予防的搭載で実測未達**(第109・帯の途中 resume の縮小再現は未取得)
- **D16 屋内 ON**・**D17 実験**・**4系統レーン2**(B-L1 以降)
- **竹-4 残**: ④span_m 実効速度差 ⑥サブステップ軌跡記録・`planning.py` 契約化

## 5. 設計制約と受領文書(背景・不変)

### 5.1 設計制約(R1 ドクトリン)
恒常制約: ①新機能は既定 OFF ②既定 OFF で golden L1 バイト一致 ③k 非依存 ④no-fingerprint ⑤用途別乱数 stream ⑥観測がシムを変えない。
観察ラン(本選10日)は再現性を厳密に求めず repro_tier=journal/none も投入可・検証ラン(verify)は strict のみ(第72で構造化済み)。

### 5.2 受領文書(原文は docs/plans/source/ に保存済み)
二重化指示書3本・認知/物理/DT定義3本・設計議論まとめ(2026-08-02)・サーベイ PDF(原本リポ外・読解=[llm-social-sim-survey.md](docs/research/llm-social-sim-survey.md))。
統合計画の正典: [dual-mode-observe-verify-plan.md](docs/plans/dual-mode-observe-verify-plan.md)・[cognition-physics-plan.md](docs/plans/cognition-physics-plan.md)・[dayplan-engaged-plan.md](docs/plans/dayplan-engaged-plan.md)・[highfidelity-3d-physics-plan.md](docs/plans/highfidelity-3d-physics-plan.md)・[if-sv-p4-plan.md](docs/plans/if-sv-p4-plan.md)。

### 5.3 日程(2026-08-21更新)
**提出 8/30 23:59**・**本番10日ラン開始=目標8/22深夜〜8/23昼・最終責任線8/23夜**(ユーザー方針2026-08-16: 日付固定の凍結に執着せず、必要な実装を終えたらできる限り早く開始)。**平均step時間の期限算術**: 平均6分=6日で完走(8/23開始可)/平均10分=10日=完走不能→§3 J1。ユーザー基準(2026-08-20)=「最悪、平均10分ならOK」+完走との整合はJ1で最終決定。GPU=A5000級×7(単一ノード・topology A)。旧記述(8/15開始・8/15-16診断ラン)は履歴。

### 5.4 本選後(レーン3)
所有権 O2/O4/O5・chance.py コード削除・場所二層知覚(IDEA⑥)・誤情報構造化フル版(ID-U2)・SUMO 反実仮想(P5)・USD/3D Tiles(DT-U4)・UE5(DT-U2)・org 会計主体化の拡張(倒産・信用線)・SoA 配線・詳細順位は [dt-integration-plan.md](docs/plans/dt-integration-plan.md) §3。
