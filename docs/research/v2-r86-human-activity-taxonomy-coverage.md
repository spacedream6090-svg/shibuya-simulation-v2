# R-86 答申: 人の行動の分類と v2 の語彙の突き合わせ(足りない行動の洗い出し)

<!-- hdr:v1 -->
- **分野**: 時間利用研究 #4 / 計算社会科学 #25 / ABM 方法論 #21 | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §6 ②・§6 7-2・§11 第 3 群「人の行動の分類との突き合わせ」・付録 A の未決の穴)
- **一次確認**: **B**(サブ実読。原典本文・原表 15・リポ内の記録と既存答申 3・抄録 1・未読 1。空欄 9 件は §7)・数値は原表から再計算(§8 の手順)・親検収 済(第319・2026-10-03: 役割語が待機に落ちる箇所 `engine/llm_bridge.py:683-686` を実読・AB7 の 300 件の JSON(n=300・段0 281)と被覆の JSON の出典(e-Stat 第 1-7 表)を確認・社会生活基本調査の合計 1,439 分は原表の値。手で付けた 300 件の分類の妥当性は親未確認(抜き取り 10 件を今後)。等級 A−)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(取得は e-Stat の xlsx 1 件だけ=`data/research_cache/r86/MANIFEST.md`)・コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: 社会生活基本調査の 20 種と 6/22/90・ATUS の 17/110/465 は [D-71 の答申](v2-d71-vocab-growth-research.md) §1.5(親確認 第204)。本書は 90 小分類それぞれの**平日の時間**を原表から取り、v2 の語彙と 1 行ずつ突き合わせる。段0 辞書の意味損失の宣言は [語彙政策 v0](../design/v2-synonym-policy-v0.md)。v1 との差分の 9 件は [v2-v1-gap-record.md](../design/v2-v1-gap-record.md) §3。
> 集計スクリプトと JSON: `docs/bench/analysis/wallbounce-1003/r86/`(§8)。

## 結論(5 行)

1. **縦軸 12 の分類と、横軸 26 語(v1/v2/v3 の行動語の和)と affordance を突き合わせた**。社会生活基本調査 R3 の小分類 90(平日・10 歳以上・全国の総平均時間。原表の合計 1,439 分)は、「ある」19・「近い」27・「無い」42・対象外 2 に分かれる。時間で見ると「ある」695 分・「近い」562 分・「無い」175 分になる。
2. **時間の重みが一番大きい穴は「無い」ではなく「近い」に入る**。主な仕事(241 分)は役割語の形で語彙にあるが、LLM の経路では役割語が待機に落ちて状態が変わらない(`engine/llm_bridge.py:683〜686`)。「無い」の中で重み(時間 × 範囲 × 影響・自前の式=推測)の上位 5 は、身の回りの用事(トイレ・身支度)・子どもと家族の世話と同伴・スポーツと運動・受診と療養・自宅の家事。
3. **時間の調査に出にくいが、他人や世界を変える行動の穴**が、Gehl 系の公共空間の観察項目・先行の LLM 社会シミュレーション・v1・付録 A から出た。遠隔の連絡(電話・メッセージ・SNS)・観察と接近・物の受け渡し・路上の生業・喫煙・迷惑行為・遺失物・評判と噂の 8 群がそれに当たる。統合した「無い」の一覧は 26 項目(§3-4)。
4. **AB7 の自由文 300 件を辞書を通さずに読み直した**。段0 で写された 281 行のうち、別の行為に畳まれた行(意味の損失)は 76 行=**27.0%**(95% 区間 22.2〜32.5%)、行為の一部だけが残る行(軽微)を足すと 105 行=**37.4%**(31.9〜43.2%)で、既存の約 37% と合う。300 件のうち 265 件(88%)は目的が食事で、自由文の表層は 91 種類しかなく、上位 2 語(行く・食べる)が 89.8% を占める。AB7 は足りない行動の**幅**を測る材料としては狭い。
5. **② の部品で表せないものは 4 つの型に分かれる**。複数の体の位置をつなぐ同伴、場の状態を変える喫煙や騒音、他人の体を変える迷惑行為や事故、エンジンの過程として起きる火災と遅延である。語彙に足す候補は「連絡する・見る・渡す/拾う・連れて行く」。affordance に足す候補はトイレ・受診・対人サービス・座る場所・雨よけ・喫煙所。GPU の後のメニュー無しの腕では、本書の符号表で原文を 2 人で分類し、一致率と「どの分類にも入らない行」の割合を測る(§6)。

## §0 出典の表

等級: **◎** 原典本文・原表で数値や名前まで確認 / **○** 一部推測を含む・リポ内の既存の記録経由 / **△** 抄録・二次 / **×** 未読(空欄)

| # | 出典 | URL・場所 | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | 総務省統計局「令和3年社会生活基本調査 調査票B 生活時間編」第1-7表 曜日,男女,ふだんの健康状態,年齢,行動の種類別総平均時間(主行動)(10歳以上)全国(statInfId 000032261363) | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032261363&fileKind=0 | ◎ | xlsx 全表。平日・男女総数・健康状態総数・年齢総数の行を抽出(大 6・中 22+再掲 1・小 90 を見出しから数えた) |
| 2 | 同 調査票B の表一覧(生活時間編) | https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00200533&tstat=000001158160&cycle=0&tclass1=000001158188&tclass2=000001158189&tclass3=000001158191&tclass4val=0 | ◎ | 表番号と statInfId の対応 |
| 3 | BLS「ATUS Activity Lexicons」 | https://www.bls.gov/tus/lexicons.htm | ◎ | 「3-tiered classification system with 17 first-tier categories」 |
| 4 | BLS「ATUS Activity Coding Lexicon 2025」PDF | https://www.bls.gov/tus/lexicons/lexiconnoex2025.pdf | ◎ | PDF のしおり(第 1 層 01〜16・18・50 の名前) |
| 5 | UNSD「ICATUS 2016」 | https://unstats.un.org/unsd/demographic-social/time-use/icatus-2016/ | ◎ | 大分類 1〜6 の名前・3 層の構造 |
| 6 | UNSD Classification Detail(ICATUS 2016) | https://unstats.un.org/unsd/classifications/Family/Detail/2083 | ◎ | 「nine major divisions」・構造表 9 / 56 / 165 |
| 7 | UNSD「Time-use statistics」研修資料(チュニス 2023) | https://unstats.un.org/unsd/demographic-social/meetings/2023/tus-wk-tunisia-2023/2.%20UNSD.pdf | ◎ | 大分類 7〜9 の名前(pymupdf で抽出) |
| 8 | NHK 放送文化研究所「国民生活時間調査 行動分類について」 | https://www.nhk.or.jp/bunken/yoron-jikan/data/yoron-jikan_bunrui.pdf | ◎ | 全文(大分類・中分類・小分類 29・具体例・同時行動の扱い) |
| 9 | 第6回東京都市圏 PT 調査(2018)目的種類別代表交通手段別 OD 表の集計(計画基本ゾーン 0241 着) | `docs/bench/pt_shibuya/pt6_summary_core0241.json`(元は e-Stat の d-1 CSV。[D-66 答申](v2-d66-outside-residents-research.md) §3-C) | ○ | リポ内の集計 JSON を読んだ(CSV は再集計していない) |
| 10 | Seattle DOT「Public Life Data - Metadata」(Gehl Institute の Public Life Data Protocol に準拠) | https://www.seattle.gov/documents/Departments/SDOT/UrbanDesignProgram/public_life_metadata.pdf | ◎ | 全文(姿勢 11 欄・活動 18 欄の名前と定義) |
| 11 | Gehl Institute「Public Life Data Protocol(beta)」 | https://gehlinstitute.org/wp-content/uploads/2017/09/PLDP_BETA-20170927-Final.pdf | × | 未読(#10 のリンク先として確認しただけ) |
| 12 | Park J.S. ほか 2023「Generative Agents」 | https://arxiv.org/abs/2304.03442 | △ | 抄録(固定の行動の一覧は無く、自然文で行動する) |
| 13 | google-deepmind/concordia README | https://github.com/google-deepmind/concordia | ◎ | 「Entities describe their intended actions in natural language, and the GM translates these」 |
| 14 | camel-ai/oasis `oasis/social_platform/typing.py` | https://github.com/camel-ai/oasis/blob/main/oasis/social_platform/typing.py | ◎ | `class ActionType(Enum)` の 32 値と既定の組 |
| 15 | tsinghua-fib-lab/AgentSociety `cityagent/blocks/*.py` | https://github.com/tsinghua-fib-lab/AgentSociety/tree/main/packages/agentsociety/agentsociety/cityagent/blocks | ◎ | mobility / economy / social / other / plan の各 Block の name・description・行動 |
| 16 | v1 リポ `src/society/cognition/deliberate.py`・`src/society/actions/registry.py`・`src/society/tools.py` | 隣のディレクトリ(読むだけ) | ◎ | 出力形の行動の一覧と道具 |
| 17 | v2 リポの語彙と affordance の定義(§2) | `src/shibuya/...`(§2 に `path:line`) | ◎ | 定義と適用関数 |
| 18 | AB7 seed 1/2 自由意図の腕のテープ | `data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open/calls.parquet` ほか | ◎ | 全行の表層と無作為 300 行の原文 |
| 19 | 趣味の affordance 対応表 | [v2-hobby-affordance-map.md](../design/v2-hobby-affordance-map.md) | ○ | POI の subcat と社会生活基本調査の種目の対応 |
| 20 | 語彙政策 v0・行動契約書 | [v2-synonym-policy-v0.md](../design/v2-synonym-policy-v0.md)・[v2-action-contract.md](../design/v2-action-contract.md) | ○ | 段0 辞書の分類・契約表 |

本数: ◎ 15(#1〜8・#10・#13〜18)/ ○ 3(#9・#19・#20)/ △ 1(#12)/ × 1(#11)。

## §1 縦軸: 人の行動の分類

### 1-1 社会生活基本調査 R3 調査票B(大 6・中 22・小 90)

原表 #1 の平日・10 歳以上・全国の総平均時間(主行動・分/日)。小 90 の合計は 1,439 分(四捨五入の差で 1,440 にならない)。小分類 90 の 1 行ずつの時間・範囲・影響・v2 の語は `r86/coverage_ssb.json` の `rows`。下の表は中分類ごとのまとめ。

| 中分類(平日の分) | 分 | 小分類の数 | ある | 近い | 無い |
|---|---|---|---|---|---|
| 11 主な仕事関連 | 245 | 2 | 1 | 1 | 0 |
| 12 副業関連 | 1 | 2 | 1 | 1 | 0 |
| 13 通勤 | 32 | 1 | 1 | 0 | 0 |
| 14 その他の仕事関連 | 4 | 2 | 1 | 0 | 1 |
| 21 家事 | 105 | 14 | 0 | 0 | 14 |
| 22 育児 | 14 | 7 | 0 | 1 | 6 |
| 23 買い物・サービスの利用 | 19 | 3 | 1 | 1 | 1 |
| 24 家事関連に伴う移動 | 8 | 1 | 1 | 0 | 0 |
| 25 ボランティア活動関連 | 2 | 2 | 1 | 0 | 1 |
| 31 学業 | 61 | 5 | 2 | 3 | 0 |
| 32 学習・自己啓発・訓練(学業以外) | 4 | 1 | 0 | 1 | 0 |
| 41 睡眠関連 | 478 | 3 | 1 | 1 | 1 |
| 42 身体的ケア | 77 | 5 | 0 | 2 | 3 |
| 43 食事 | 109 | 5 | 5 | 0 | 0 |
| 51 社会参加・宗教活動 | 1 | 2 | 0 | 0 | 2 |
| 52 交際 | 11 | 6 | 1 | 1 | 4 |
| 53 教養・趣味・娯楽 | 50 | 13 | 0 | 7 | 6 |
| 54 スポーツ | 19 | 5 | 0 | 2 | 3 |
| 55 マスメディア利用 | 161 | 6 | 0 | 6 | 0 |
| 56 休養・くつろぎ | 22 | 1 | 1 | 0 | 0 |
| 61 移動 | 12 | 2 | 2 | 0 | 0 |
| 62 調査・その他 | 6 | 2 | 0 | 0 | 0(対象外 2) |

- 中分類の分は原表の中分類の列。小分類の和と 1 分ずれる行がある(原表の四捨五入)。
- 小分類の主な時間: 睡眠 475・主な仕事 241・テレビ 130・食事の管理 46・夕食 44・学校での授業 41・身の回りの用事(自分自身や家族等が行うもの)39・昼食 33・通勤 32・入浴 31・朝食 24・コンピュータの使用 23・休養・くつろぎ 22。
- 主行動の集計なので、電話・メッセージのように「ながら」で行うことの多い行動は小さく出る(電話による交際 1 分・電子メール等 2 分)。同時行動の表(第 1-10 表など)は取っていない(§7 空欄)。

### 1-2 ATUS(第 1 層 17)

#4 のしおり: 01 Personal Care / 02 Household Activities / 03 Caring For & Helping Household Members / 04 Caring For & Helping Nonhousehold Members / 05 Work & Work Related Activities / 06 Education / 07 Consumer Purchases / 08 Professional & Personal Care Services / 09 Household Services / 10 Government Services & Civic Obligations / 11 Eating and Drinking / 12 Socializing, Relaxing, and Leisure / 13 Sports, Exercise, and Recreation / 14 Religious and Spiritual Activities / 15 Volunteer Activities / 16 Telephone Calls / 18 Traveling(+ 50 Data Codes)。17 は 50 を除いた数(D-71 答申と同じ)。社会生活基本調査に無い独立の層は **08 対人サービス・09 家事サービス・10 行政サービス・16 電話**。

### 1-3 ICATUS 2016(大分類 9・中 56・小 165)

#5〜#7: 1 Employment and related activities / 2 Production of goods for own final use / 3 Unpaid domestic services for household and family members / 4 Unpaid caregiving services for household and family members / 5 Unpaid volunteer, trainee and other unpaid work / 6 Learning / 7 Socializing and communication, community participation and religious practice / 8 Culture, leisure, mass media and sports practices / 9 Self-care and maintenance。小 165 の一覧は読んでいない(§7)。

### 1-4 NHK 国民生活時間調査(小分類 29)

#8: 必需行動(睡眠・食事・身のまわりの用事・療養・静養)/ 拘束行動(仕事・仕事のつきあい・授業・学内の活動・学校外の学習・炊事・掃除・洗濯・買い物・子どもの世話・家庭雑事・通勤・通学・社会参加)/ 自由行動(会話・交際・スポーツ・行楽・散策・趣味・娯楽・教養(インターネット除く)・趣味・娯楽・教養のインターネット(動画除く)・インターネット動画・テレビ・録画番組・DVD・ラジオ・新聞・雑誌・マンガ・本・音楽・休息)/ その他。社会生活基本調査との違いで渋谷に効くものは 2 つ。**「行楽・散策」(行楽地・繁華街へ行く、街をぶらぶら歩く、散歩)** が独立の小分類であることと、**会話・交際に電話・電子メール・インターネットでのやりとりを含む**こと。時間の数値(2020 年)は取っていない(§7)。

### 1-5 PT 2018 の移動目的(渋谷駅周辺ゾーン 0241 着)

#9: 着トリップ 400,451(平日)。自宅-勤務 38.3%・私事 26.6%・自宅-私事 13.4%・勤務・業務 7.2%・自宅-通学 5.7%・帰宅 5.0%・自宅-業務 3.1%・不明 0.6%(不明 2,271 から再計算)。私事の内訳(買物・食事・社交・娯楽・通院など)は d-1 の表には無い(§7)。v2 は通勤・通学・業務を予定表の語(`build/sched/vocab.py:88` の 勤務・通学・用事)で持つが、「私事」の中身は行動語の側で受ける。

### 1-6 公共空間の観察(Gehl Institute の Public Life Data Protocol に準拠したシアトル市の項目)

#10 の「people staying」の欄。姿勢 11: standing / leaning / sitting_formal_all(public / public_fixed_bench / public_movable_seat / commercial / private)/ sitting_informal / lying / staying_mobility_assist。活動 18: commercial_selling / commercial_selling_informal / commercial_buying / commercial_observing / eating_drinking / talking_to_others / smoking / cultural / recreation_active / recreation_passive / waiting_transportation / working_civic / disruptive / disruptive_aggressive / disruptive_intoxicated / living_public / using_electronics / soliciting。#10 の背景の節は公共生活を「necessary (e.g., walking to work) or recreational (e.g., watching a street performer)」と書く。Gehl の 3 分類(必要・任意・社会的活動)の原典は読んでいない(§7)。

### 1-7 POI の種類ごとにできること

v2 の W6 の cat 13 種と subcat 31 語(`build/geo/poi_class.py:86`・`:125`)に、場所の種類から一般に起きる行為を当てた(実行役の判断=推測。外部の標準の分類表は §7 空欄)。

| cat(件数は `poi_target.py:211` の注記) | 起きる行為(推測) | v2 で使える行動 |
|---|---|---|
| food 823 | 食べる・飲む・座る・待つ・会う | 購入・食事・並ぶ・会話 |
| shop 721 | 買う・見て回る・試す・返品 | 購入・並ぶ |
| nightlife 259 | 飲酒・踊る・歌う(karaoke)・遊技(pachinko)・入浴(sauna)・夜を過ごす(net_cafe) | 購入・並ぶ(nightlife は食事の飲食店に入らない=語彙政策 v0 §6) |
| service 114 | 散髪・受診・手続き・預ける | 購入(対人サービスの効果は無い) |
| leisure 42 | 運動(gym)・遊ぶ(park・arcade)・休む | 購入・移動+あたり(park に購入の対象は無い) |
| cinema 7・attraction 12 | 観る・見学する・写真を撮る | 購入・撮影(役割語=効果なし) |
| hall | 観る(劇場・ライブ)・集まる(会議・展示) | 無い(購入の候補から除外 `poi_target.py:214`) |
| office | 働く・訪問する・会議 | 予定表の語「勤務」だけ |
| school・education | 授業・学ぶ・迎えに行く | 予定表の語「通学」だけ |
| hotel | 泊まる・休む | 就寝(寝床として使えるかは契約書の前提) |
| landmark 56 | 待ち合わせる・眺める・参拝(worship) | `can_meet` / `can_look`(`world/state.py:65`) |

### 1-8 先行の LLM 社会シミュレーションの行動

| 先行 | 行動の定義 | 一覧 |
|---|---|---|
| Generative Agents(#12) | 固定の一覧は無い。自然文で行動し、抄録の例は「wake up, cook breakfast, and head to work」 | 自然文 |
| Concordia(#13) | 固定の一覧は無い。体が意図を自然文で書き、Game Master が結果に直す | 自然文 |
| OASIS(#14) | `ActionType`(typing.py:17〜48)32 値 | exit・refresh・search_user・search_posts・create_post・like_post・unlike_post・dislike_post・undo_dislike_post・report_post・follow・unfollow・mute・unmute・trend・sign_up・repost・quote_post・update_rec_table・create_comment・like_comment・unlike_comment・dislike_comment・undo_dislike_comment・do_nothing・purchase_product・interview・join_group・leave_group・send_to_group・create_group・listen_from_group |
| AgentSociety(#15) | Block ごとの行動 8: mobility(place_selection・move)・economy(work・consume・economy_none)・social(find_person・message)・other(sleep・other)。欲求ごとの選択肢 `plan_block.py:139〜145` | hungry: Eat at home / Eat outside / Eat at current location、tired: Sleep at home、safe: Work / Shopping、social: Contact with friends、whatever: leisure and entertainment / other / stay at home。message の説明は「including online and offline, phone call, social post」 |

### 1-9 v1 の行動の一覧

`v1:src/society/cognition/deliberate.py:21〜56` の出力形: speak・coin_label・post・dm・wander・do(自由記述・切替口)・nothing(切替口)・verify(go / ask / net・切替口)。道具 `:81〜102`: propose・host_event・post_flyer・found_group・open_venture。`v1:src/society/actions/registry.py:18〜23`: move_to・continue・stay・speak・coin_label・reflect。ほかに plan・recall(`deliberate.py:760`・`:769`)・job_search(`v1:src/society/tools.py:972`)。路上の生業・遺失物・対人サービスなどは LLM の行動語ではなくエンジンの phase(付録 A)。

## §2 横軸: v2 の語彙と affordance

### 2-1 行動語(v1/v2/v3)

| 版 | 語 | 定義の場所 |
|---|---|---|
| v1(24 語) | 横断 12: 移動・乗車・降車・購入・待機・会話・退去・通報・手伝い・断る・休憩・就寝 / 役割 12: 接客・補充・開閉店・価格改定・発車・停車・放送・遅延報告・計画改訂・指示・並ぶ・撮影 | `src/shibuya/llm/contract.py:200〜517`(ActionSpec)・`:534`・`:537`・`src/shibuya/perception/templates.py:177`・`:475` |
| v2(25 語) | v1 + 食事 | `llm/contract.py:598`・`:603`・`:617`・`perception/templates.py:424` |
| v3(23 語) | 横断 12: 移動・乗車・購入・食事・会話・退去・通報・手伝い・断る・就寝・並ぶ・なし / 役割 11(並ぶを除く)。待機・休憩・降車は受理しない | `llm/contract.py:654`・`:680`・`:689`・`perception/templates.py:513` |
| v3 の活動欄 | 「世界を変えない過ごし方」の自由文 10 字以内+「まで」 | `perception/templates.py:538`・`engine/activity.py` 冒頭 |

三つの版の和は **26 語**(v1 の 24 + 食事 + なし)。

効果の有無(`engine/resolve.py`):
- **状態が変わる**: 移動 `:1641`・乗車 `:1883`・降車 `:2124`・購入 `:2154`・食事 `:2289`・並ぶ `:2384`・待機/なし `:2406`・会話 `:2491`・退去 `:2521`・休憩 `:2591`・就寝 `:2601`。
- **語はあるが状態が変わらない**: 断る(記録のみ `:2557`)・通報(前提の検査だけ。効果先は未実装 `:2562`)・手伝い(必ず失敗 `:2586`)。
- **役割語 11〜12 語**: LLM の経路では待機へ落ちる(`engine/llm_bridge.py:683〜686`)。開閉店にはエンジンの関数がある(`engine/resolve.py:3057` `request_open_close`・権限つき)が、LLM の応答からは呼ばれない。

### 2-2 affordance(店や場所の使い方)

| 何 | 中身 | 場所 |
|---|---|---|
| 購入・並ぶの候補の cat | food・shop・nightlife・service・leisure・cinema・attraction(office・hotel・school・landmark・hall・education は除く) | `engine/poi_target.py:214` |
| 食事の場所 | 飲食店マスク(cat が food。nightlife は入らない) | `world/state.py:333`・`engine/resolve.py:2289` |
| 目印の使い方 | `can_meet`・`can_look`(landmark・attraction の 68 件) | `world/state.py:65`・`:341` |
| subcat 31 語 | v1 から 11+趣味の受け皿 20(park・gym・theatre・museum・library ほか)。行動は付かず、場所の語と営業時間に効く | `build/geo/poi_class.py:86`・`:164` |
| 場所の種類 12・予定の活動語 12 | 自宅・職場・学校・駅・飲食店・物販店・公園・娯楽施設・宿泊施設・医療施設・路上・域外 / 就寝・支度・移動・乗車・勤務・通学・食事・買物・娯楽・用事・交流・休憩 | `build/sched/vocab.py:108`・`:88` |

予定表の活動語(勤務・通学・用事・娯楽・交流・支度)は W17 の日課の語で、LLM の行動語ではない。本書では「予定表の語だけ」を「近い」に数えた。

## §3 被覆の表

### 3-1 判定の語と重み

- **ある**: 行動語があり、適用関数が状態を変える。
- **近い**: 語はあるが効果が無い(記録のみ・必ず失敗・待機へ落ちる)、予定表の語か活動欄でしか表せない、または段0 辞書で別の語に写されて意味が落ちる。
- **無い**: 表す語が無い。活動欄に書けても、世界の側に受け皿(場所・相手・物)が無いものを含む。
- **重み** w = 平日の総平均時間 × 範囲 r × (1 + 影響 s)。r は 1(主に渋谷の街の中)/ 0.5(一部)/ 0.1(主に自宅か域外)、s は 1(他人や世界の状態を変える)/ 0。**式と r・s の値は実行役の判断(推測・expedient)**で、感度の確認はしていない。

### 3-2 社会生活基本調査の小分類 90 の集計

| 判定 | 小分類の数 | 平日の分 | 分 × r | w |
|---|---|---|---|---|
| ある | 19 | 695 | 210.9 | 298.3 |
| 近い | 27 | 562 | 209.7 | 340.1 |
| 無い | 42 | 175 | 48.3 | 65.7 |
| 対象外(調査に関連する行動・他に分類されない) | 2 | 7 | 0 | 0 |

「無い」の小分類は数が多いが、多くは自宅の家事と育児で、範囲の重みが小さい。範囲で重みを付けると、「ある」と「近い」がほぼ同じ大きさになる。

### 3-3 群にまとめた重み(`r86/group_weights.json`)

| 群 | 判定 | 平日の分 | w | 中身(小分類) |
|---|---|---|---|---|
| K01 仕事の中身(接客・補充・事務) | 近い | 242 | 242.0 | 111・121 |
| K03 メディアと画面(テレビ・PC・ゲーム・読書) | 近い | 205 | 43.3 | 551〜556・5302・5309〜5311・5313 |
| K02 学校と学習 | 近い | 56 | 27.4 | 311〜313・321 |
| **G01 身の回りの用事(トイレ・身支度)** | 無い | 39 | 19.5 | 423 |
| **G03 子どもと家族の世話と同伴** | 無い(送迎は近い) | 15 | 15.6 | 221〜227・2110〜2113 |
| **G05 スポーツと運動** | 無い・近い | 19 | 11.1 | 541〜545 |
| K04 対人サービスと観覧(美容室・塾・映画・劇場・浴場) | 近い | 35 | 11.1 | 233・424・5301・422 |
| **G02 受診と療養** | 無い | 8 | 10.4 | 421・413・425 |
| **G10 自宅の家事** | 無い | 101 | 10.1 | 2101〜2108・2114 |
| G04 遠隔の連絡(電話・メッセージ・手紙) | 無い | 3 | 6.0 | 524〜526 |
| G07 社会参加・ボランティア・会合 | 無い | 2 | 2.0 | 251・511・521 |
| K05 散歩・犬の散歩 | 近い | 2 | 2 | 5307 |
| K06 うたたね・家族との会話 | 近い | 5 | 1.3 | 412・523 |
| G06 公的サービスと手続き | 無い | 1 | 1.0 | 232・2109 |
| G09 求職 | 無い | 1 | 1.0 | 142 |
| G12 ドライブ | 無い | 1 | 1.0 | 5312 |
| G08 礼拝 | 無い | 1 | 0.5 | 512 |
| G11 趣味の制作・園芸・ペット | 無い | 1 | 0.5 | 5303〜5306・5308 |

太字は「無い」の重みの上位 5。

### 3-4 ほかの分類との突き合わせと、統合した「無い」の一覧

社会生活基本調査に出にくい(主行動の時間が小さい、または時間の調査の外にある)行動を、§1-2〜§1-9 と付録 A から足した。重みは時間が取れるものだけ w、取れないものは範囲と影響の印(◎ 主に街の中 / ○ 一部 / △ 主に外、影響は 有 / 無)。出所の略: S=社会生活基本調査、A=ATUS、I=ICATUS、N=NHK、P=PT、G=Gehl 系(#10)、O=OASIS、AS=AgentSociety、V1=v1、AB7=AB7 の表層、付A=付録 A。

| # | 足りない行動 | 出所 | w または 範囲・影響 | v2 の今 |
|---|---|---|---|---|
| 1 | 身の回りの用事(トイレ・身支度) | S423・A01・I9・N 身のまわりの用事 | 19.5 | 無い |
| 2 | 子どもと家族の世話と同伴(連れて歩く・付き添う・遊ばせる) | S22・A03/04・I4・N 子どもの世話・AS(Eat at home 系は家) | 15.6 | 無い(送迎の移動だけある) |
| 3 | スポーツと運動(球技・ジム・ジョギング) | S54・A13・N スポーツ・G recreation_active | 11.1 | 無い・近い(gym で購入・歩き回るは移動+あたり) |
| 4 | 受診と療養 | S421/413・A08・N 療養・静養・付A #6 | 10.4 | 無い(医療施設は場所の種類だけ) |
| 5 | 自宅の家事 | S21・A02・I3・N 炊事・掃除・洗濯 | 10.1(範囲は △) | 無い |
| 6 | 遠隔の連絡(電話・メッセージ・メール・SNS への投稿や返信) | S524/525・A16・N 会話・交際・G using_electronics・O 全般・AS message・V1 post / dm・AB7 電話 1 行 | 6.0(主行動の時間は小さい。同時行動は空欄) | 無い |
| 7 | 社会参加・集会・提案・団体・出店 | S251/511・I5/7・N 社会参加・O create_group / join_group・V1 propose / host_event / found_group / open_venture・付A 世界を変える道具 | 2.0 | 無い(§6 ② の部品と裁定で扱う決定済み) |
| 8 | 公的サービスと手続き(役所・銀行・郵便) | S232/2109・A09/10 | 1.0 | 無い |
| 9 | 求職・働き口を得る | S142・V1 job_search | 1.0 | 無い |
| 10 | 礼拝 | S512・A14・I7・N(社会参加に冠婚葬祭) | 0.5 | 無い(worship は can_look だけ) |
| 11 | 観察・見る・確かめに行く | G commercial_observing / recreation_passive・V1 verify・AB7 観察 80→待機・見る 33・調べる 2→待機 | ◎・無 | 近い(辞書で待機に写る=意味の損失) |
| 12 | 近づく・寄る(人や物に寄る) | AB7 近づく 49・近寄る 30(未定義) | ◎・無 | 無い |
| 13 | 雨宿り・避難 | AB7 避雨 8・避難 4(未定義) | ◎・無 | 無い |
| 14 | 物を持つ・取る・渡す・拾う | AB7 持つ 6・取る 9・取り出し 1(未定義)・② の部品「物を動かす」 | ◎・有 | 無い(購入の所持品の加算だけ) |
| 15 | 座る・立ち止まる・寝そべる(姿勢と場所の使い方) | G 姿勢 11 欄 | ◎・有(席を占める) | 近い(座る→休憩=軽微。席の容量は無い) |
| 16 | 路上の生業(客引き・ティッシュ配り・路上の物売り・路上音楽・募金や勧誘) | G commercial_selling_informal / soliciting / cultural・付A #2 | ◎・有 | 無い(役割名だけ) |
| 17 | 喫煙 | G smoking | ◎・有(場を変える) | 無い |
| 18 | 迷惑行為・酩酊・けんか | G disruptive / disruptive_aggressive / disruptive_intoxicated | ◎・有 | 無い(通報の相手としての事象だけ) |
| 19 | 路上で過ごす・野宿 | G living_public・契約書の就寝の失敗「路上就寝は U18」 | ◎・有 | 無い |
| 20 | 遺失物(落とす・拾う・届ける・着服) | 付A #4 | ◎・有 | 無い |
| 21 | 事故と火災に巻き込まれる | 付A #3 | ◎・有 | 無い(行動ではなく過程) |
| 22 | 評判・噂を広める(第三者についての話) | 付A #1・O repost / quote_post・V1 gossip | ◎・有 | 近い(口コミは店名と評価語だけ) |
| 23 | SNS 上の反応(いいね・フォロー・ミュート・通報) | O like_post / follow / mute / report_post | ○・有 | 無い |
| 24 | 待ち合わせ・約束(会う時刻と場所を決める) | S522・AS find_person・V1 dm | ◎・有 | 近い(can_meet の場所はあるが、約束の語は無い) |
| 25 | 名付け(新しい呼び名を作る) | V1 coin_label | ○・有 | 無い |
| 26 | 運転(車・自転車) | S5312・P 手段(自動車 4.3%・自転車 3.9%=#9 から再計算) | ○・有 | 無い(R-67 の担当) |

- **「無い」の数**: 上の 26 項目(社会生活基本調査の群 10・ほかの分類から 16)。「近い」に入れた 4 項目(#11・#15・#22・#24)を除くと 22。
- 対象外にしたもの: 内省・計画(v1 の reflect / plan / recall)は認知の層の話(指示書 §7-3)で行動語ではない。監督と自動復旧(付A #9)は運用で人の行動ではない。人口の出入り・加齢(付A #7)と混雑による遅延(付A #5)は世界の過程(§5)。
- ATUS・ICATUS・NHK の第 1 層は、社会生活基本調査の中分類と 1 対 1 か、より粗いので、新しい穴は出なかった(ATUS の 08・09・10・16 は #4・#8・#6 に入る)。

## §4 AB7 の自由文の読み直し

### 4-1 テープの場所と母集団

- テープはリポの `data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open/` と `data/tape/c8_ab7_s2/AB7-OPEN-INTENT__open/` にある(gitignore 下。指示書 §6 ② の「場所を確かめる」の答え)。
- seed 1: 36,868 行(繰り延べを除く)。行動欄の表層は **91 種類**。辞書を通らず語彙の語のまま書いた行 1,991、段0 で写された行 34,274、写されなかった行 603(既存の `data/vocab/ab7_open_s1.json` の計数と一致)。上位 2 語「行く」20,508・「食べる」12,594 で **89.8%**(`r86/ab7_surface_counts.json`)。
- seed 2: 36,707 行・表層 84 種類。上位 2 語で 89.4%(`r86/ab7_s2_surface_counts.json`)。

### 4-2 無作為 300 行の手の分類

- 抜き方: `random.Random(86)` で 300 行(`r86/ab7_sample.py`)。300 行の内訳は段0 で写された 281・語彙の語 15・未定義 4。
- 分類: 実行役が理由・行動・対象・ひと言を読み、目的(§1 の分類のどれか)と、段0 の写像で意味が落ちたかを 1 行ずつ付けた(`r86/ab7_labels.py`。符号の定義は同ファイル冒頭)。
- 目的の内訳(300 行): 食事 265・軽飲食と喫茶 15・買い物 5・休養 4・観察と確認 3・行き先の定まらない移動 2・雨宿り 2・判別できない 2・待つ 1・夜の娯楽 1。

| 写された 281 行の判定 | 行数 | 割合 |
|---|---|---|
| 意味は落ちていない(行く→移動で対象あり・買う→購入など) | 171 | 60.9% |
| 軽微(コンビニや食品店で「食べる」→購入=買うことは残る) | 29 | 10.3% |
| 対象の損失(探す・探索→移動で行き先なし) | 5 | 1.8% |
| 意味の損失(飲食店や対象なしで「食べる」→購入) | 76 | 27.0% |

- **意味の損失だけ: 76/281 = 27.0%(Wilson 95% 区間 22.2〜32.5%)**。軽微を足すと 105/281 = 37.4%(31.9〜43.2%)。対象の損失まで足すと 110/281 = 39.1%(33.6〜45.0%)。
- 同じ 281 行に語彙政策 v0 の分類(食べる・飲む・観察系=意味の損失)を機械的に当てると 106 行=37.7%。既存の「約 37%」は語の単位で「食べる」全体を意味の損失に数えた値で、行を読むと、そのうち約 3 割(29/106)は店で買う行為として読める。
- 例(原文の要約 3 件・店名と個人名は伏せた): (1)「食べる・対象なし・どこで食べようか考える」=意味の損失。(2)「食べる・対象=コンビニ・何か食べたい」=軽微。(3)「行く・対象=飲食店・おすすめは?」=意味は落ちていないが、目的の「食べる」は v1 の語彙に無い。
- 動詞では落ちていなくても**目的が v1 の語彙で表せない行**(目的が食事・観察・雨宿り)は 270/300 行。v2 で食事が入ったので、残るのは観察と雨宿り(5 行)。

### 4-3 含意

AB7 の自由文は食事に偏っていて、幅の材料としては狭い。300 件の無作為抽出では、珍しい語(見る・近づく・避雨・持つ・電話)は 0〜1 件しか入らない。次に読み直すときは、表層ごとの層別抽出(全表層から最大 N 件ずつ)にする(§6-4)。

## §5 付録 A の未決の穴 9 件

| # | 穴 | 縦軸のどれに当たるか | 重み | 行動か過程か |
|---|---|---|---|---|
| 1 | 評判・ゴシップ・地位 | S52 交際の中身・O repost / quote_post・N 会話・交際 | 時間は空欄(会話の時間の内数)・◎・有 | 行動(話の中身)。伝わり方は過程 |
| 2 | 路上の生業(客引き・ティッシュ配り・路上音楽) | G commercial_selling_informal / soliciting / cultural・S111 の一部(従業者の仕事) | ◎・有 | 行動(仕事の中身) |
| 3 | 火災と歩行者の事故 | G disruptive の一部。時間の分類には無い | ◎・有 | 過程(巻き込まれる・逃げる・通報は行動) |
| 4 | 遺失物のループ | 時間の分類には無い(落とすは無意図)。拾う・届けるは S511 社会参加に近い | ◎・有 | 過程(落とす)+行動(拾う・届ける・着服) |
| 5 | 混雑で停車時間が延びて遅延 | P の手段 鉄道 66.4%(#9)が受ける。人の行動は「乗る・降りる・駆け込む」 | ◎・有 | 過程 |
| 6 | 重症化・入院・死亡 | S421 受診・S413 療養(5+2 分)・A08・N 療養・静養 | w 10.4(G02)の一部 | 過程(状態)+行動(受診) |
| 7 | 人口の出入り・転居・加齢 | 時間の分類の外(年単位) | 範囲は域外・影響有 | 過程 |
| 8 | 対人サービス(美容室・医院・塾・ジム) | S424・S421・S313・S545・A08 | w 11.1(K04)+10.4(G02)の一部 | 行動(受ける側)+仕事(提供する側) |
| 9 | 監督と自動復旧 | 人の行動ではない | 対象外 | 運用 |

## §6 提案(実行役の案・親とユーザーの判断待ち。決定ではない)

### 6-1 足りない行動の優先順(重み順)

1. **K01 仕事の中身**(w 242・近い): 役割語の効果を LLM の経路につなぐ(新しい語は要らない。`llm_bridge.py:686` の「待機へ落とす」の扱いを変えるかどうか)。路上の生業(付A #2)はこの中に入る。
2. **G01 身の回りの用事(トイレ)**(w 19.5): 駅と商業施設の場所に affordance を足す形。
3. **G03 同伴**(w 15.6): 子連れ・家族連れ・友人連れで一緒に動く。② の部品だけでは表せない(6-2)。
4. **K04 + G02 対人サービスと受診**(w 21.5 を合わせる): 付A #6・#8 を一緒に扱える。
5. **#6 遠隔の連絡**(w 6.0。ただし主行動の時間は小さく出る): 指示書 §7-7 と R-85 の担当。付録 A の扱いが決まったもの「発言の本文が相手に届いていない」とつながる。
6. 以降は G05 運動、#11 観察、#14 物の受け渡し、#22 評判と噂、#16〜#19 の路上の行動の順。G10 自宅の家事は範囲の外なので最後にする。

### 6-2 ② の部品(状態を変える基本操作)で表せるもの・表せないもの

部品は指示書 §6 ② の 7 つ: お金を動かす・物を動かす・位置を変える・関係を変える・決まった記録や物を作る・本人の状態を変える・契約や所有や権利を移す。

| 足りない行動 | 部品の組み合わせ(案) | 判定 |
|---|---|---|
| トイレ・身支度 | 位置 + 本人の状態(+施設の列) | 表せる |
| 受診・対人サービス | 位置 + お金 + 本人の状態 + 提供者の時間(仕事) | 表せる(提供者の判断は提供者の呼で) |
| 遠隔の連絡・SNS 投稿 | 記録を作る(宛先つき)→相手の知覚に届く | 表せる(届き方は R-85) |
| 評判・噂 | 記録を作る(話の中身)→相手の知覚 | 表せる(本文が届く前提=Q57) |
| 観察・見る・近づく | 本人の状態(注意)・位置 | 表せる |
| 雨宿り | 位置 | 表せる |
| 物を持つ・渡す・拾う・遺失物 | 物を動かす + 所有の移転(着服は権限の検査で却下され、記録に残る) | 表せる |
| 求職・出店・団体 | 契約・所有・権利の移転 + お金 | 表せる(⑦ 7-2) |
| 運動・礼拝・社会参加 | 位置 + 本人の状態(+集まりの記録) | 表せる |
| 同伴(連れて歩く) | 複数の体の位置を同時につなぐ | **表せない**(部品は 1 体の位置。2 体の位置を拘束する部品が要る) |
| 喫煙・騒ぎ(場を変える) | 場の状態(煙・音)を変える | **表せない**(場の状態の部品が無い) |
| 迷惑行為・けんか・事故 | 他人の体の状態を変える | **表せない**(裁定の約束「他人の心は決めない」の外。体への作用をどう扱うかが未決) |
| 火災・遅延・人口の出入り | 行動ではない(エンジンの過程) | 部品の対象外 |

### 6-3 語彙に足す候補と affordance に足す候補

- **affordance に足す候補**(D-71 E「オブジェクトに affordance を足す」の形): トイレ(駅・商業施設)・受診(医療施設)・対人サービスを受ける(service の美容室・塾、leisure の gym)・観る(hall の劇場・ライブ。今は購入の候補から外れている)・座る場所(ベンチ・店の席。Gehl の姿勢の欄に当たる)・雨よけ(屋根・軒下・地下通路)・喫煙所・参拝(worship)。
- **語彙(動詞)に足す候補**(物に縛られない行為): 連絡する(相手=人・道具=電話やメッセージ)・見る(対象=物・人・場所。今は観察→待機で意味が落ちる)・渡す/拾う(対象=物)・連れて行く(対象=人)・約束する(相手・時刻・場所)。
- 足さない方がよいと考えるもの: 喫煙・迷惑行為は語にすると設計者の指紋になりやすい(促す形になる)。② のラン中の裁定の腕で、自由文に出てきたら記録する形が合う。

### 6-4 GPU の後のメニュー無しの腕での確認の形

1. System 2 が自由に計画する腕で、行動欄を辞書で写さず原文のまま記録する(指示書 §6 ②)。
2. 本書の符号表(社会生活基本調査の小分類 90 + §3-4 の 26 項目 + 判別できない)で、原文を 2 つの独立した分類者(LLM 2 つ、または人と LLM)が分類し、一致率(Cohen の κ)を出す。
3. 抜き方は表層ごとの層別抽出にする(無作為だけでは AB7 のように 1 つの目的に偏る)。全行の表層の数と上位 2 語の占める割合も毎回出す。
4. 測るもの: (a) どの分類にも入らない行の割合 (b) 「無い」の 26 項目それぞれの出現数 (c) 範囲内の小分類の構成比を、社会生活基本調査の平日の時間の構成比(範囲で重みを付けたもの)と比べる距離 (d) 語や affordance を足した後に、段0 の「意味の損失」(本書の 27.0% / 37.4%)が下がるか。
5. 同時に回す (c) の裁定の腕では、裁定の件数と却下の件数を 26 項目ごとに数え、6-2 の「表せない」型が実際にどれだけ来るかを確かめる。

## §7 空欄

1. 社会生活基本調査の**同時行動**を含む時間(第 1-10 表など)。電話・メッセージ・SNS は主行動では小さく出るので、遠隔の連絡の重みは過小の可能性がある。未取得。
2. NHK 国民生活時間調査 2020 の行動別の時間(分類表だけ読んだ)。
3. ICATUS 2016 の小分類 165 の一覧(大分類 9 の名前と件数だけ確認)。
4. PT 2018 の私事の内訳(買物・食事・社交・娯楽・通院など)。d-1 の表には無い。
5. Gehl Institute の Public Life Data Protocol の原典(#11)と、Gehl の必要・任意・社会的活動の原典。シアトル市の準拠版(#10)だけ読んだ。
6. POI の種類ごとの行為の外部の標準表(§1-7 は実行役の判断)。
7. AB7 seed 2 の 300 行の手の分類(seed 2 は表層の数だけ数えた)。
8. 重みの式 w の感度(r と s を変えたときに上位が入れ替わるか)。
9. Generative Agents の本文(抄録だけ)。

## §8 再現手順

リポの根から実行する(リポの `.venv` の Python。pyarrow を使う)。

1. `python docs/bench/analysis/wallbounce-1003/r86/ssb_b_weekday.py data/research_cache/r86/ssb2021_b_t1-7_000032261363.xlsx docs/bench/analysis/wallbounce-1003/r86/ssb_b_weekday.json`(xlsx は標準ライブラリだけで読む `xlsx_min.py`)
2. `python docs/bench/analysis/wallbounce-1003/r86/coverage_ssb.py docs/bench/analysis/wallbounce-1003/r86/ssb_b_weekday.json docs/bench/analysis/wallbounce-1003/r86/coverage_ssb.json`
3. `python docs/bench/analysis/wallbounce-1003/r86/group_weights.py docs/bench/analysis/wallbounce-1003/r86/coverage_ssb.json docs/bench/analysis/wallbounce-1003/r86/group_weights.json`
4. `python docs/bench/analysis/wallbounce-1003/r86/ab7_sample.py data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open docs/bench/analysis/wallbounce-1003/r86/ab7_sample300.json <リポの外の TSV>`(TSV は原文を含むのでリポに置かない)
5. `python docs/bench/analysis/wallbounce-1003/r86/ab7_meaning_loss.py docs/bench/analysis/wallbounce-1003/r86/ab7_sample300.json docs/bench/analysis/wallbounce-1003/r86/ab7_meaning_loss.json`
6. `python docs/bench/analysis/wallbounce-1003/r86/ab7_surface_counts.py data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open docs/bench/analysis/wallbounce-1003/r86/ab7_surface_counts.json`(seed 2 は出力名を `ab7_s2_surface_counts.json` に)
