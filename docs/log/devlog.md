# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **3 / 10**
> 第1〜第110(2026-09-01〜09-08)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 2026-09-08 第111 【工程出口】C4(世界過程第1陣+経済+物)完了・層2合格(修正1点反映)・コミット=C0〜C4 の /goal 達成
- 実施(親検収=再実行): サブH-2a(runner・環境・鉄道 4,089 本/日・営業時間 PlanSpec・混雑/屋内占有・断面交通)・サブH-2b(補充/納品/廃棄・前倒し 9 過程・顕著行為+p_notice 結線・センサス結線・L4 上限修正 56,488→50,000 呼)・親の shibuya.cli(台帳つき入口・店舗参入資本 200,000 円=expedient)・core.types.max_tick 境界修正。層2レビュー=不合格(修正1点: センサスが畳んだ後の空行列を評価)→C4-fix で DayClose 経由に修正(+潜在バグ: attach_household_cash の期首取り直し)・O(t) ログの成長実測・乗り残し率・注記訂正・便数照合両方向。最終: 1,125 passed・lint 5 kept・scan CLEAN・実データ 5,000 体×1 日 12.8 s・保存則(金/物/乗客)一致・センサス残差 0 PASS・憲法5 OK・T2 一致。
- ユーザー判断待ち(PENDING 冒頭): W10 道路名(Overpass)・W9 影容量宣言・セル数表記・B3 チャネル行・S3 参照・科目表 delta 5・語彙上限 24・B0 予算・§2.6 実効容量・B5 気づき行/在庫置場/補充フォールバック行/バス停座標/§6(i) B4b/廃棄 band 方式・成長宣言 delta(ActualLog)・W16 の町丁目境界・R16(GPU 艦隊)。
- 次: ユーザーの判断→C5(W16 母集団合成=境界データ後・W17=艦隊)→C6(実 LLM スモーク)→C7(40 万体)。

## 2026-09-08 第112 【運用】ユーザー回答6件+添付サーベイ所見(出典一次確認)+PENDING 全面整理(番号制)・R16 仮決定・§9.1/§9.6 delta
- 依頼: 1 サーバー解決? 2 e-Stat 手順を詳しく 3 R16=推奨で仮承認(今後変更あり) 4 クレジット=止まったら仕方ない 5 PC OK 6 PENDING 見にくい→整理・**実装はまだ**・添付(LLM 社会シミュ動向サーベイ・文字化けで到着→復元)の意見。
- 実施: SSH 疎通 OK(18:48・up 24 days・7×A5000 空き=前回のタイムアウトは一過性)。e-Stat 統計GIS は動的ページで文言を機械確認できず→東京都一覧への直リンク(statmap-search?…serveyId=A002005212020&prefCode=13&coordsys=1&format=shape&datum=2011)と手順を PENDING U-1 に記載(zip 取得はユーザー・§7 例外の範囲外のため)。決定台帳に R16 行(仮)・実装計画書 §9.6 追記(クレジット不使用・PC・疎通・合図待ち)・§9.1 実績 delta(C0〜C4≈8 h・律速=外部前提)。**PENDING.md を U/D/§3/F 番号制の 5 節へ全面整理**(完了項削除・判断 15 件に推奨と既定を併記・ユーザー作業 7 件・工程地図 C5〜C8)。Unawareness 監査: templates/llm/bridge のプロンプト面に「シミュレーション/実験/エージェント」語なし。
- 添付サーベイの一次確認(親・arXiv/J-STAGE 実読=要旨レベル): 森ら=**森隆太郎**(理研)+原田憲旺(東大)ほか計 10 名・人工知能学会論文誌 41(4)・2026-07-01 公開・「再現」「理解」二軸=真(報告の「陽太郎」は誤記)/Mou et al. 2412.03563=三階層(個人・シナリオ・社会)=真(ACM CSUR 掲載は要旨に無し=未確認)/PIMMUR 2509.18052=実在・v3(2026-04)は 39 本・違反 89.7%・実験推測 50.8%・過剰制御 61.0%・「often vanish or reverse」(報告の 52.9%・「frequently fail to emerge」は旧版の可能性=版差)/SimBench 2510.17516=20 データセット・40.80/100・対数線形=真(45 モデル・Claude-3.7 は要旨に無し・ICLR 2026 採択=真)/OpenLife 2606.31046=真(6 体・約 12 週・ALIFE 2026)/Emergence World 2606.08367=真(5 世界×15 日・安定〜人口崩壊)/Larooij & Törnberg=arXiv 2504.03274 実在・「exacerbate rather than resolve」(35 本は要旨に無し・Springer 版は認証壁で未読)/「分散 20〜300 倍」=2604.01520 の考察節にあり(検索ツール経由・親の本文実読は未)。
- 所見(ユーザーへ): 報告の主軸(検証第一・average persona・永続世界)は v2 の骨格(アンカー台帳+holdout 封印・指標 B・ペルソナ 3 層+ドリフト予算・保存則・エンジン決定論)と同方向。差分提案 4 件を PENDING F-8 に**未決**で登録(PIMMUR 準拠表・Unawareness 診断行・連続稼働ドリフト観察・行動分散アンカー)。Concordia の GM=LLM 語り部に対し v2 は決定論エンジン=意図的差分。Park et al. のインタビュー駆動ペルソナは 40 万体では不可→PT/社会生活基本調査(行動自己申告の集計)で代替し「歪む場所」として宣言。
- 次: ユーザー=U-1 境界データ配置・U-2 返却延長・D-1〜D-15 への回答(「推奨どおり」可)。親=合図後に C5-a から(実装は再開しない)。

## 2026-09-08 第113 【データ】U-1 町丁目境界データ受領・親検収(80 町丁目・人口合計 243,883=E1 一致)+ライセンス台帳行+U-3/U-7 の解説
- 依頼: 「data/realworld/estat に置いた。U-7・U-3 の解説を詳しく」。
- 実施: zip(A002005212020DDSWC13113-JGD2011.zip・57,768 B・sha256 88e8f889…)を data/realworld/estat/r2ka13113/ へ展開。標準ライブラリで shp ヘッダ/dbf を解析(geopandas・pyshp は部品表外=未導入): Polygon 80・KEY_CODE 80 一意・HCODE 8101・JGD2011 緯度経度・JINKO 合計 243,883=e-Stat API の夜間人口(E1)と完全一致・SETAI 149,967・AREA 15.12 km²(区面積 15.11)。ライセンス台帳に行追加(政府標準利用規約2.0)。PENDING U-1 を削除・§0/§5 更新。
- U-7(PLATEAU 渋谷区 2023 年度)の一次確認: G空間情報センター plateau-13113-shibuya-ku-2023=CityGML v4 zip 636 MB(udx: bldg/brid/dem/fld/frn/lsld/luse/tran/ubld/urf/veg・製品仕様書 4.1 版・2025-04-18 v4 公開・最終更新 2026-04-03)・関連データ 42 kB(GeoJSON: station/railway/border 等)・ライセンス=PLATEAU サイトポリシー §3(PDL1.0)。目録に tran の属性記述なし→交通量属性(uro:TrafficVolumeAttribute=センサス区間 ID)の有無は開くまで不明。仕様書 PDF は 10 MB 超で親未読。
- U-3(main マージ)の状況: main=第105b・build/c0-c4 は 7 コミット先行・fast-forward 可・origin には main のみ(ブランチ未 push)。CI(ci.yml)=push(main・build/**)と PR で起動: 秘密スキャン全追跡ファイル・lint-imports・pytest(not gpu/slow・data 依存テストは skipif)・data/ 非追跡検査。
- 次: ユーザー=U-2(返却延長)・U-3 の方式選択(ブランチ push→PR か ff マージ)・U-7 取得の要否・D-1〜D-15。実装は合図待ち。
