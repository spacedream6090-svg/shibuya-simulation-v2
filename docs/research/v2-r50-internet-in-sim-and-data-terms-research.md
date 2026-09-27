# R-50 答申: シミュレーション内のインターネット(検索・口コミ・SNS)の設計論点と、実データ初期値の利用規約
<!-- hdr:v1 -->
- **分野**: 研究倫理・情報法 #31 / 小売科学・商業立地論 #17 / 行動経済学・マーケティング科学 #16 / 知覚心理学 #5 / 社会ネットワーク科学 #14 / 計算社会科学 #25 / 自然言語処理・機械学習 #27 | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(出典 45〔原典 43・うち規約・公式文書 21・抄録のみ 7/二次 2(#3・#44)〕・空欄 21 = §9)・**親検収 済(第278・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: 設計者の要件(シミュレーション内のネット=エージェントが店を検索し・口コミを読み書きし・SNS を見る)について、(1) 実データ(食べログ・Google マップ等)を初期値にできるかを**規約の逐語**で判定し、(2) 先行実装・日本の店選び経路・歩きスマホ・検索と距離・ネット広告の計測の錨を原典で並べる。現行案「見えている順の満足化・距離項なし」([草案 §2-2/L3](../design/v2-hunger-choice-attention-draft.md))との衝突点を整理する。**設計の決定はしない**(§8 は選択肢。サブの自前構成は「expedient」と明示)。
> 規律: 子サブ未起動・Web は読むだけ(登録・API 呼び出し・ダウンロードなし)・コミットなし・台帳未編集・本書の新規作成のみ。**法的助言ではない**(規約の文言の整理。事業化前に弁護士確認)。

---

> **親検収(第278・2026-09-27・親=Fable 5.1)**:
> - 規約の逐語(§1)の照合(親が同じ URL を curl → 標準出力 → 文字列照合・保存なし・登録なし): ✓ Google Maps Platform ToS 3.2.3「(iii) copy and save business names, addresses, or user reviews」「to train, test, validate or fine-tune the models」(Previous versions の欄に「Last modified August 26, 2026」)/ ✓ 食べログ 9.(1)[1]「…複写、若しくはその他の方法により再生、複製、送付、譲渡、頒布、配布、転売、又はこれらの目的で使用するために保管すること」・6.(1)[1]「営業活動その他の営利を目的とした行為」/ ✓ Yelp Dataset Terms 3.「Non-commercial use means use of the Data by registered nonprofits, government, educational institutions, and think tanks」「you must submit your findings to Yelp for review and approval」。
> - 判定表(§2)の判定の妥当性: 逐語と整合(評価点の保存・初期値化は各規約で不可・FSQ OS Places は評価列なし・OSM は自家評価の別属性で非発火)。**法的助言ではない**の注記を設計書にも保つ。Google 3.2.3(c)(vii) の「test, validate」は台帳候補 L6 の現実側に Google 評価を使う道を塞ぐ=親も同意(PENDING に注記)。
> - 数値の写し検査(§4〜§7): ✓ Argin ら 2020「35.9% gazed on and through the smartphone screen」「only 7.8% of the observed pedestrians were using a smartphone」/ ✓ Thompson ら 2013(PubMed E-utilities の抄録)「text messaging (7.3%)」/ ✓ リクルート 2024 の 26.4/22.2/14.7/11.1・n=6,487 は R-49 の検収で同じ PDF を照合済み。Hyman 2010 の 25.0/51.3/60.7/71.4% は第278 に親が原典 PDF 表 2 で確認 ✓(§5 の「△ 親未確認」と §9-14 は解消)。
> - 循環参照検査: 法務答申(D 等級)を根拠にせず ODbL・OSMF を原文で取り直している=可。広告答申の等級 C の箇所は「等級 C」と明示して引いている=可。
> - 訂正の伝播: なし(訂正は無い)。設計への写し先は [記憶・口コミ・ネットの草案](../design/v2-memory-wom-internet-draft.md) §2(D-121)。

## §0 等級と調べ方

- 等級: **◎** 原典の本文に逐語があり親も同じ URL で文字列照合できる / **○** 原典を実読(図の画像・抄録のみ・JS 埋め込み等で照合がやや手間)/ **△** 二次経由(検索要約・ブログ)/ **×** 未確認。
- 取得: HTML/PDF を curl で標準出力に流し、HTML はタグ除去、PDF は pymupdf でテキスト化して**生テキストへの文字列一致**で逐語を確認した。長い規約は中間テキストをセッションのスクラッチに置いた(リポ・data/ には置いていない)。arXiv は API の抄録と HTML/PDF 本文。WebFetch は 1 回(ぐるなび API ページ=403 で失敗)。登録・API キーを要するものには触れていない。
- 既存答申で済んでいるものは引用のみ: OASIS/AgentSociety のコード([R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md) §2〜§3)・Hyman 2010 の 4 群([R-47](v2-r47-classical-choice-attention-research.md) §5・**親未確認 △**)・CoPB/ハフの定義(R-47 §2-6・§3)・広告効果の実測帯と attribution の壁([広告答申](v2-ad-information-research.md) §4・**等級 C**)・ホットペッパー 2018 のリピート 77.5%([選好ベクトル答申](v2-preference-vector-research.md)・親 ✓)・CitySim の Google 評価とブランド偏り([lit](lit/leisure__bougie2025_citysim-shibuya-poi.md)・親未確認)。法務答申([v2-legal-licensing-deep-research.md](v2-legal-licensing-deep-research.md))は **D 等級(URL なし)** なので根拠にせず、ODbL は本書 §1-5 で原文を取り直した。

| # | 出典 | 種別 | 等級 |
|---|---|---|---|
| 1 | 食べログ利用規約(最終改正 2026-02-17)https://tabelog.com/help/rules/ | 規約 | ◎ |
| 2 | 食べログ robots.txt https://tabelog.com/robots.txt | 公式 | ◎ |
| 3 | 食べログ API 提供終了(2014-06-30)の告知の引用 https://attrip.jp/129520/ ほか | 二次 | △ |
| 4 | カカクコム ニュース 2026-04-21(月間利用者数)https://corporate.kakaku.com/news/20260421 | IR 公表 | ◎ |
| 5 | Google Maps Platform Terms of Service(Last modified August 26, 2026)https://cloud.google.com/maps-platform/terms | 規約 | ◎ |
| 6 | Google Maps Platform Service Specific Terms(Last modified June 10, 2026)https://cloud.google.com/maps-platform/terms/maps-service-terms | 規約 | ◎ |
| 7 | Places Aggregate API overview https://developers.google.com/maps/documentation/places-aggregate/overview | 公式文書 | ◎ |
| 8 | Yelp Open Dataset https://business.yelp.com/data/resources/open-dataset/ | 公式 | ◎ |
| 9 | Yelp Dataset Terms of Use(Last Updated February 21, 2020)https://s3-media0.fl.yelpcdn.com/assets/srv0/engineering_pages/bea5c1e92bf3/assets/vendor/yelp-dataset-agreement.pdf | 規約 | ○(配布物同梱の版は未確認) |
| 10 | Foursquare「Foursquare Open Source Places」2024-11-19 https://foursquare.com/resources/blog/products/foursquare-open-source-places-a-new-foundational-dataset-for-the-geospatial-community/ | 公式 | ◎ |
| 11 | FSQ OS Places スキーマ https://docs.foursquare.com/data-products/docs/places-os-data-schema / 取得 https://docs.foursquare.com/data-products/docs/access-fsq-os-places | 公式文書 | ◎ |
| 12 | FSQ Places Pro/Premium スキーマ https://docs.foursquare.com/data-products/docs/places-pro-and-premium | 公式文書 | ◎ |
| 13 | ODbL 1.0 https://opendatacommons.org/licenses/odbl/1-0/ | ライセンス | ◎ |
| 14 | OSMF Collective Database Guideline https://osmfoundation.org/wiki/Licence/Community_Guidelines/Collective_Database_Guideline_Guideline | ガイドライン | ◎ |
| 15 | リクルートWEBサービス 利用規約 https://cdn.p.recruit.co.jp/terms/rws-t-1001/index.html | 規約 | ◎ |
| 16 | ホットペッパーグルメ API リファレンス https://webservice.recruit.co.jp/doc/hotpepper/reference.html | 公式文書 | ○ |
| 17 | ぐるなびサイト利用規約(改定 2024-01-15)https://corporate.gnavi.co.jp/agreement/ ・お問い合わせ https://corporate.gnavi.co.jp/contact/ | 規約・公式 | ◎ |
| 18 | Retty 利用規約(2023-06-26 改定)https://retty.me/announce/tos/ | 規約 | ◎ |
| 19 | e-Stat 検索「口コミ」(データベース 37 件)https://www.e-stat.go.jp/stat-search/database?page=1&query=口コミ&layout=dataset | 公式 | ○ |
| 20 | NII 情報学研究データリポジトリ 一覧 https://www.nii.ac.jp/dsc/idr/datalist.html | 公式 | ○ |
| 21 | Yang ら OASIS, arXiv:2411.11581 | 原典 | ◎ |
| 22 | Piao ら AgentSociety, arXiv:2502.08691 | 原典 | ◎ |
| 23 | Wang ら RecAgent, arXiv:2306.02552 | 原典 | ◎ |
| 24 | Zhang ら Agent4Rec, arXiv:2310.10108 / Gao ら S3, arXiv:2307.14984 | 抄録 | ○ |
| 25 | Rossetti ら Y Social, arXiv:2408.00818 | 原典 | ◎ |
| 26 | Park ら Social Simulacra(SimReddit), arXiv:2208.04024 | 原典 | ◎ |
| 27 | AgentSociety 2, arXiv:2607.11895 / UGI, arXiv:2312.11813 | 部分・抄録 | ○/△ |
| 28 | Muchnik, Aral & Taylor 2013, Science 341(6146):647–651, doi:10.1126/science.1240466 | 抄録(PubMed) | ◎ |
| 29 | リクルート「飲食店への期待と満足度、リピート意向についての調査」2024-05-28 https://www.recruit.co.jp/newsroom/pressrelease/assets/20240528_gourmet_01.pdf | 業界公表 | ◎ |
| 30 | Thompson ら 2013, Inj. Prev. 19(4):232–237, doi:10.1136/injuryprev-2012-040601 | 抄録(PubMed) | ◎ |
| 31 | Argin, Pak & Turkoglu 2020, ISPRS IJGI 9(12):700, doi:10.3390/ijgi9120700(arXiv:2103.01217) | 原典 | ◎ |
| 32 | 澁谷・中村 2015「デジタルサイネージにおける注目度の規定要因」東京都市大学 情報メディアジャーナル 16 https://www.comm.tcu.ac.jp/cisj/16/assets/16_04.pdf | 原典 | ○(図 5〜9 は画像) |
| 33 | 小塚 2016「歩行中・自転車運転中の“ながらスマホ”時の視線計測と危険性」IEICE Fundamentals Review 10(2):129 https://www.jstage.jst.go.jp/article/essfr/10/2/10_129/_pdf | 原典 | ○ |
| 34 | NTT ドコモ モバイル社会研究所 2023-09-06 https://www.moba-ken.jp/project/lifestyle/20230906.html | 業界公表 | ◎ |
| 35 | 東京消防庁「歩きスマホ等に係る事故に注意！」(2026-03-03 更新)https://www.tfd.metro.tokyo.lg.jp/lfe/nichijo/mobile.html | 公的 | ◎ |
| 36 | Ursu 2018, Marketing Science 37(4):530–552, doi:10.1287/mksc.2017.1072 | 抄録(Crossref) | ◎ |
| 37 | Noulas ら「A tale of many cities」arXiv:1108.5355 | 抄録 | ○ |
| 38 | Athey ら 2018, arXiv:1801.07826 | 抄録 | ○ |
| 39 | Wang ら 2023, iScience 26(6):106811, doi:10.1016/j.isci.2023.106811 | 原典(PMC) | ◎ |
| 40 | Luca「Reviews, Reputation, and Revenue: The Case of Yelp.com」HBS WP 12-016 https://www.hbs.edu/ris/Publication%20Files/12-016_a7e4a5a2-03f9-490d-b093-8f951238dba2.pdf | 原典 | ◎ |
| 41 | Zheng ら arXiv:2309.03882 / Liu ら「Lost in the Middle」arXiv:2307.03172 | 抄録 | ○ |
| 42 | MRC Viewable Ad Impression Measurement Guidelines https://www.iab.com/wp-content/uploads/2015/06/MRC-Viewable-Ad-Impression-Measurement-Guideline.pdf | 業界標準 | ◎ |
| 43 | IAB/MRC Intrinsic In-Game Advertising Measurement Guidelines 2.0(2022-08)https://mediaratingcouncil.org/sites/default/files/Standards/In-Game%20Advertising%20Measurement%20Guidelines%2008-31-22.pdf | 業界標準 | ◎ |
| 44 | ぐるなび無料 API 終了(2021-06-30)の記述 http://boccitabi.com/gurunaviwaebservice-use/ | 二次 | △ |
| 45 | 消費者庁 消費者意識基本調査 報告書「Ⅱ 調査結果の概要」(2024-06-14 掲載 PDF・調査年度は本文抜粋に無く未確認)https://www.caa.go.jp/policies/policy/consumer_research/research_report/survey_002/assets/consumer_research_cms201_240614_15.pdf | 公的 | ◎ |

## §1 実データの利用規約(逐語)

**1-1 食べログ(#1〜#4)**: 目的=「他の食べログ閲覧者が飲食店を選ぶ際の参考として活用していただくことを主な目的」(1.)。
- 6.(1)[1]「お客様は、当社が提供する食べログについて、その全部あるいは一部を問わず、営業活動その他の営利を目的とした行為又はそれに準ずる行為やそのための準備行為を目的として、利用又はアクセスしてはならないものとします。」
- 6.(1)[2]「食べログへ投稿された口コミを無断転載・無断利用することは禁止します。」/ 6.(1)[3] 営利目的の口コミ利用に「1件の口コミ（画像の場合には1枚の画像）につき1万円」の請求権。
- 8.(3)「…法令により権利者からの許諾なく利用若しくは使用することを許容されている場合を除き、食べログ及び食べログの内容について複製､編集､改変､掲載､転載､公衆送信､配布､販売､提供､翻訳・翻案その他あらゆる利用又は使用を行ってはなりません｡」
- 9.(1)[1]「法令上又は本規約若しくはガイドライン上特に認められている場合を除き、食べログの提供する情報を当社の事前の同意なく、複写、若しくはその他の方法により再生、複製、送付、譲渡、頒布、配布、転売、又はこれらの目的で使用するために保管すること」。
- 規約本文に「スクレイピング」「クローリング」の語は**無い**(文字列検索で 0 件)。機械的取得は 9.(1)[1] の複製・保管で塞がれる形。robots.txt は一部パスの Disallow のみ(#2)。**研究利用の例外条項は無い**。公式 API は 2014-06-30 終了(#3・△=一次の告知ページは取れず)。学術向けの公式データ提供は見つからず、NII IDR の一覧にも飲食店口コミのデータセットは無い(#20・楽天は市場/トラベル/GORA/レシピのみ)。
- 規模(#4): 「月間利用者数 1億175万人、月間総PV24億6,234万PV（2025年12月実績）」「スマートフォン：8,336万人 パソコン：1,839万人」。注記「サイトを訪れた人をブラウザベースで数えた利用者数」=**人数ではなくブラウザ数**(日本の人口を超える)。

**1-2 Google Maps Platform(#5〜#7)**: ToS 3.2.3 Restrictions Against Misusing the Services —
- (a) No Scraping「Customer will not export, extract, or otherwise scrape Google Maps Content for use outside the Services. For example, Customer will not: (i) pre-fetch, index, store, reshare, or rehost Google Maps Content outside the services; … (iii) copy and save business names, addresses, or user reviews」。
- (b) No Caching「Customer will not cache Google Maps Content except as expressly permitted under the Maps Service Specific Terms.」
- (c) No Creating Content From Google Maps Content「… (vii) use Google Maps Content to improve machine learning and artificial intelligence models, including to train, test, validate or fine-tune the models.」
- (e) No Use With Non-Google Maps「… Customer will not (i) display or use Places content on a non-Google Map」(SST 14.2 も「must not use Google Maps Content from the Places API in conjunction with a non-Google map」)。
- 例外: SST 3「Customer may cache (a) place_id from Places API …」、SST 14.3 緯度経度のみ「up to 30 consecutive calendar days」。Places Aggregate API(#7)は「user ratings」で絞った**件数**か place ID(「only if the count is 100 or lower」)を返し、SST 13.1 は件数から作る「Customer Value」を「cannot be used as a substitute for POI Counts」等の条件つきで許し、13.2 は件数の保持を「30 consecutive calendar days solely for the purpose of calculating the Customer Value」に限る。
- 含意: 評価点・店名・口コミの保存は (a)(iii)(b) で不可。**評価を LLM シミュレーションの照合(test/validate)に使うことは (c)(vii) の文言に当たりうる**(解釈 △)。v2 の地図は OSM/PLATEAU なので (e) にも当たる。

**1-3 Yelp Open Dataset(#8・#9)**: 規模「6,990,280 Reviews」「150,346 Businesses」「11 Metropolitan areas」・「intended for educational use」(#8)。規約(2020 版): 3. License「…to use, access, and create derivative works of the Data in electronic form for solely for non-commercial use.. Non-commercial use means use of the Data by registered nonprofits, government, educational institutions, and think tanks …」「Prior to any public presentation or publication of the academic results … you must submit your findings to Yelp for review and approval」。4.B「use the Data in connection with any commercial purpose」を禁止、4.E 集計値の開示も同意なしは禁止(学術出版は除外)。地理範囲は米国(+カナダ)の都市で**東京は含まれない**(△=公式に都市一覧が無く、利用論文の記述経由)。

**1-4 Foursquare OS Places(#10〜#12)**: 「This base layer of 100mm+ global places of interest (“POI”) includes 22 core attributes … available for commercial use under the Apache 2.0 license framework.」(2024-11-19)。スキーマ(OS)は fsq_place_id・name・latitude/longitude・address・…・fsq_category_ids・date_closed・unresolved_flags 等で、**rating/popularity/tips の列は無い**。評価は有償の Premium 層にある:「rating … The rating of a POI (0-10) based on user votes as well as an internal score aggregated by likes /dislikes, tips, and visit traffic」「popularity … Measure of a POI's popularity by foot traffic」。配布は現在 Places Portal(登録とトークン)経由。東京・渋谷の件数は公表値が無く空欄(数えるには取得が要る)。

**1-5 OpenStreetMap ODbL(#13・#14)**: 4.4 a「Any Derivative Database that You Publicly Use must be only under the terms of: i. This License …」/ 4.5 c「Use of a Derivative Database internally within an organisation is not to the public and therefore does not fall under the requirements of Section 4.4.」/ 4.6 公開時は派生 DB 全体か差分ファイルの提供義務。OSMF の水平層ガイドライン:「a non-OSM database replaces or adds a property of a primary feature, and uses either all OSM data or no OSM data for that property … within the same regional cut」なら Collective Database=share-alike 非発火。**シミュレーションが生成した評価を OSM 由来 POI の別属性(全部が非 OSM)として足すのはこの条項に入る**(公開時も評価の層は ODbL にならない。POI 層は従来どおり)。

**1-6 ぐるなび・ホットペッパー・Retty(#15〜#18・#44)**:
- リクルートWEBサービス(ホットペッパー): 「更新の義務」「個別に定める規定がない場合はキャッシュの更新頻度を24時間以内と定めます。」/「禁止行為」「本APIを通して取得した情報を、第三者のデーターベースに複製保存し、またはダイレクト・マーケティングその他本規約において具体的に許諾されている用途以外の用途のためにコンパイルまたは利用することはできません。」/「権利関係の帰属」「…販売、編集、加工、翻案その他の変更、再配信、サブライセンスまたは譲渡することはできません。」(条番号なし・見出しで引用)。API の応答項目に**評価点の欄は見当たらない**(#16・予算・営業時間・席数等)。
- ぐるなび: 第7条(12)「ぐるなびに無断でぐるなびサイトを営利目的に利用する行為」・(13)「…ぐるなびコンテンツ（第９条に定義します。）の全部または一部を、ぐるなびに無断で転載、蓄積、販売、再許諾、自己が利用する範囲を超えて複製、複写する行為」/ 第9条2「お客様は、私的利用の範囲に限って、ぐるなびコンテンツをダウンロードや印刷をしてご利用することができます。」。API は「「ぐるなびWebサービス」としてAPIを無料公開しておりましたがサービスを終了させて頂くことになりました。」「法人としてAPIの利用をご希望の方は以下よりお問い合わせください。」(#17)=法人・有償(終了日 2021-06-30 は △)。
- Retty: 第13条2「…利用者は、本サービスに関するコンテンツを無断で複製、編集、改編、掲載、転載、公衆送信、上映、展示、提供、販売、譲渡、貸与、翻訳、翻案、二次利用等することはできません。」/ 第14条(15)「本サービスと競合するサービスに利用することを目的とした行為（情報収集等を目的とした行為を含む）」・(19)「通常利用の範囲を超えてサーバーに負担をかける行為」。**「スクレイピング禁止が明記」という二次記述は本文と一致しない**(語は無い。塞いでいるのは第13条2・第14条)。
- 公的データ(#19): e-Stat の「口コミ」37 件はホームレスの実態に関する全国調査・情報化社会と青少年に関する調査・訪日外国人消費動向調査の**設問項目**(情報源としての口コミ)で、店ごとの評価ではない。「レビュー」は 0 件。**公的な店別評価データは無い**(○)。

## §2 規約判定表(「店の評価点をシミュレーションの初期値として取り込む」)

| データ源 | 判定の根拠(逐語は §1) | 初期値利用 | 研究のみなら | 等級(文言/判定) |
|---|---|---|---|---|
| 食べログ | 9.(1)[1] 事前同意なき複製・保管の禁止・8.(3)・6.(1)[1] 営利目的のアクセス禁止・API なし | **不可** | 事前の書面同意が要る(規約に研究例外なし) | ◎/○ |
| Google Maps Platform | 3.2.3(a)(iii) 店名・住所・口コミの保存禁止・(b) キャッシュ禁止・(c)(vii) AI の test/validate 禁止・(e) 非 Google 地図 | **不可**(place_id のみ保存可) | 同じ(規約に研究例外なし) | ◎/○ |
| 同 Places Aggregate | SST 13.1–13.2(評価帯で絞った件数から作る派生値のみ・件数は 30 日) | グレー(要法務) | 同左 | ◎/△ |
| Yelp Open Dataset | 3. 非商用のみ(登録非営利・政府・教育機関・シンクタンク)・公表前審査・4.B・渋谷は範囲外 | **不可**(範囲外) | 分布の形の参照なら可能性(公表前審査つき) | ○/○ |
| Foursquare OS Places | Apache 2.0・商用可・**評価列なし** | POI の存在・カテゴリ・閉店日は**可**/評価は無い | 可 | ◎/◎ |
| Foursquare Premium | rating 0–10・popularity(有償・契約) | 契約次第(本答申範囲外) | — | ◎/× |
| OSM | ODbL・評価は無い・シム生成の評価を別属性で足すのは水平層で非発火 | 評価は無い/自家評価の追加は**可** | 可 | ◎/○ |
| ホットペッパー API | 第三者 DB への複製保存禁止・キャッシュ 24 時間・評価欄なし | **不可** | 同じ | ◎/○ |
| ぐるなび | 第7条(12)(13)・第9条2(私的利用のみ)・API は法人有償 | **不可** | 同じ | ◎/○ |
| Retty | 第13条2・第14条(15)(19)・公開 API なし | **不可** | 同じ | ◎/○ |
| e-Stat 等公的 | 店別評価は存在しない | 該当なし | — | ○/○ |

- 結論(判定・○): **店ごとの評価点を保存して初期値にできる実データ源は、読んだ範囲に無い**。保存・再利用できるのは (i) POI の存在・カテゴリ(OSM=既存・FSQ OS=Apache 2.0)と (ii) 公表された**集計値**(調査の割合・論文の効果量)だけ。著作権法 30 条の4(情報解析)が食べログ 8.(3)/9.(1)[1] の「法令により…許容」に当たるかは本答申の範囲外(逐語未取得・弁護士判断・§9)。

## §3 他シミュレーションのネット実装

- **OASIS(#21・R-44 §3)**: 推薦系が見える投稿を決める —「the RecSys … suggests posts to agents based on their social connections, interests, or hot score of posts」。X 型は「in-network (users followed by the agent) and out-of-network」、後者は「interest matching using TwHIN-BERT」+新しさ+投稿者のフォロワー数、Reddit 型は hot score。群集効果の再現で Muchnik 2013 に倣い「one initial dislike / … one initial like」を付け、「the agents began to exhibit explicit herd effect」は 100→10,000 体で出た。行動は瞬間・持続なし(R-44)。
- **Muchnik ら 2013(#28)**: 「positive social influence increased the likelihood of positive ratings by 32% and created accumulating positive herding that increased final ratings by 25% on average」、負の操作は「inspired users to correct manipulated ratings」=**非対称**。シム内の口コミが照合できる現実パターン。
- **AgentSociety(#22)**: 都市・社会・経済の 3 空間を同じ run に持つ。社会空間は「Our current framework primarily models online social interactions through messaging on online social network」「supervisor, which monitors social media content, filters messages」=**友人への私信+監督者**で、公開の口コミ・検索は無い。場所選びは種類→半径→「Apply the Gravity model for spatial optimization」(半径内の同種 POI を全部知っている=検索相当+重力)。
- **RecAgent(#23)**: 推薦サイト内の行動に「(1) Searching behaviors: by these behaviors, the agents can actively search the items of interests. (2) Browsing behaviors: by these behaviors, the agents can receive recommendations from the system in a passive manner」を分け、社会行動は one-to-one chatting と友人への一斉発信。**検索(能動)と推薦(受動)を別の行為にした先行**。
- **Agent4Rec(#24)**: MovieLens 等で初期化した生成エージェントが「interacts with personalized recommender models in a page-by-page manner」(協調フィルタ)。**S3(#24)**: X 型の感情・態度・拡散。
- **Y Social(#25)**: 実ニュースを「RSS (Really Simple Syndication) feed parser module」で注入(「more than 600 validated RSS feeds」)・推薦戦略はエージェントごとに選択=**外部の実データを流し込む口を持つ先行**。**SimReddit(#26)**: Social Simulacra の試作ツール(Reddit の投稿・返信を生成)。
- **「物理世界と同時にネット」**: 読んだ範囲では **AgentSociety だけ**(ただし私信のみ)。UGI(#27・同研究室)は online/offline の社会網を記述(△)。AgentSociety 2(#27)は環境を「flexibly composed across research contexts」とし、事例は「meso-level dynamics in social media, and macro-level urban scenarios」と**別々に**並ぶ(同じ run で都市と SNS を回した例は未確認)。**歩き回る体が公開の口コミを読み書きし検索する先行は見つからなかった(空欄)**。

## §4 人が外食店を決める経路(日本)

- **リクルート 2024(#29)**: 首都圏・関西圏・東海圏 20〜69 歳・有効 9,606・2024-04-01〜11・マクロミル モニター。対象は「一番最近で夕方以降に初めて利用した飲食店」(モーニング・ランチ・テイクアウト・デリバリーを除く)。「事前の期待を醸成した情報源トップ3 は、1 位「グルメサイト、口コミサイト」（26.4％）、2 位「店構えや店先のメニューなど」（22.2％）、3 位「家族・友人・知人等からの口コミ」（14.7％）」、4 位 SNS 11.1%(n=6,487・複数回答。SNS の 3 圏域計は本文に無く、表の列順と 20 代男性 26.2% の一致から読んだ)。性年代: 「20・30 代男性と20 代女性で「SNS」（20 代男性26.2％、30 代男性16.8％、20 代女性28.1％）」「50・60 代女性で「店構えや店先のメニューなど」（50 代女性27.8％、60 代女性29.0％）」。店選びの経緯: 「主に自分がお店を選んだ」n=3,928・「自分もお店選びに関わった」2,043・「主に他の人がお店を選んだ」1,986。
- **フロア**: 首都圏 26.6/23.2/14.2%・関西圏 27.6/21.8/14.6%・東海圏 22.9/19.3/17.0%(同表)=圏域差 ±2〜5pt。
- 読み方: これは**初訪問**の、しかも「期待を醸成した情報源」(複数回答)で、「通りがかりで入った割合」そのものではない。外食全体では**リピート 77.5%**(ホットペッパー 2018・既存答申 ✓)なので、ネット経由が効くのは主に残り 22.5% の初訪問側。
- 規模: 食べログ 月間 1 億 175 万ブラウザ(§1-1)。
- **読む人と書く人(#45・公的)**: ネット利用者 4,439 人に「SNS や口コミサイト、動画サイト等で、商品やサービスに関して」した反応を聞き、「「お気に入り」や「いいね」や「高評価/低評価」をつけたことがある」42.8%・「投稿やコメントをしたことがある」21.1%・いずれか 47.9%。読む側は「インターネット上の口コミや評価が高い商品を選ぶ」70.1%・「評価の点数が高くても、否定的な口コミを見て購入をためらうことがある」63.9%・「レビュー（購入者の評価）の件数が多い商品を選ぶ」50.6%。**これは「したことがあるか」で、来店 1 回あたりの投稿率ではない**(投稿率の直接の錨は空欄・§9)。飲食店に限った数字でもない。
- **渋谷の来街者に絞った店選び経路の調査は見つからなかった(空欄)**。少数標本の民間調査(Instagram・Google マップの利用率等)は検索要約のみで採らない。

## §5 歩きスマホ(「スマホ操作中」活動の錨)

| 量 | 値 | 出典・等級 |
|---|---|---|
| 瞬間の割合(観察・横断中) | 「Nearly one-third (29.8%) of all pedestrians performed a distracting activity while crossing. Distractions included listening to music (11.2%), text messaging (7.3%) and using a handheld phone (6.2%).」n=1,102・シアトル 20 交差点・2012 | #30 ◎ |
| 瞬間の割合(観察・広場) | 「only 7.8% of the observed pedestrians were using a smartphone」(ヘント Korenmarkt・7 日) | #31 ◎ |
| 使う人の視線の配分 | 「64.1% of smartphone users’ gaze was on the environment (Gaze 1), while 35.9% gazed on and through the smartphone screen」・静止中は「58.6%」・「74.3% of smartphone users walked without stopping」(n=350) | #31 ◎ |
| 「するか」(自己申告) | 「全体の4割超が歩きスマホを行っている」「男女とも10代～20代の6割超」・特別区/政令市の 10〜30 代「約7割」(n=6,423・2023-01) | #34 ◎ |
| 速さ | 約 23 m の横断歩道で「通常歩行に比べて約20 ～30％遅くなる」/ texting で「1.87 additional seconds (18.0%)」 | #33 ○ / #30 ◎ |
| 看板への注目(渋谷) | スマホ所持の有無で「渋谷交差点を除く全ての地点で，スマートフォンを持っていない人のほうが明らかに注目率が高い」・停止者の注目 交差点 42.3% vs ハチ公広場 30.9%(χ²=27.96)。**スマホ別の数値は図 5〜9 の画像で取れず** | #32 ○ |
| 気づき(副課題) | 道化を見た率 通話 25.0%・単独 51.3%・音楽 60.7%・二人 71.4% | R-47 §5(△ 親未確認) |
| 事故 | 令和3〜7年で「171人が救急搬送」・令和7年 43 人(速報)・「ころぶ」71 人 | #35 ◎ |

- **フロア**: 観察の瞬間割合 7.3〜7.8%(画面操作系)と自己申告「するか」40%超は**定義が違う**(瞬間の割合 vs 経験の有無)ので混ぜない。観察同士でも交差点(シアトル)と広場(ヘント)で場所が違う。
- 渋谷の知見(#32)は、信号待ちではスマホを持っていても顔を上げる(交差点だけスマホ有無の差が出ない)=**「スマホ操作中」の減衰は場所(信号待ち)で打ち消される**ことを示す。
- 「視野が 1/20」は小塚 2016 本文に無く一次を確認できなかった(§9)。

## §6 検索と候補集合・距離(L3 との衝突)

- **位置効果(#36)**: Expedia の順位を無作為化した実験で「I identify the causal effect of rankings and show that they affect what consumers search, but conditional on search, do not affect purchases」「average position effect of $1.92, which is lower than literature estimates obtained without experimental variation」=**順位は「何を見に行くか」を変え、見た後の選択は変えない**。
- **距離減衰は検索時代も残る(#39)**: Yelp の店属性+SafeGraph の来店 6 億件超で「the number of restaurant visitations decreases as the inverse square of their travel distances」(後期パンデミックで弱まる=フロアは時期差)。Athey ら(#38)は昼食の店選びで評価と移動時間の好みを体ごとに推定(MNL/NL より良い)。
- **距離でなく順位(#37)**: Foursquare で「a universal law for human mobility is identified, which isolates as a key component the rank-distance, factoring in the number of places between origin and destination, rather than pure physical distance」=**介在機会(間にある店の数)**が効く。
- **評価の効果(#40)**: 「a one-star increase in Yelp rating leads to a 5-9 percent increase in revenue」「this effect is driven by independent restaurants; ratings do not affect restaurants with chain affiliation」。
- **LLM に一覧を渡す危険(#41)**: 選択肢の並びへの「selection bias」(Zheng)・中ほどの情報を落とす(Liu)。LLM に検索結果を並べて選ばせると、**人の位置効果(#36)ではなくモデルの位置偏りが混ざる**。CitySim のブランド偏り(既存 lit)も同じ系統。
- **「検索で選んだ店は通りがかりより遠い」を直接比べた実証は見つからなかった(空欄)**。
- 衝突の整理: 現行 L3 は B2 の可視順で満足化し距離項を持たない。検索は B2 の外の店を候補に入れるので、(i) 並べ方(プラットフォームの順位か近い順か)と (ii) 半径で切るか、が新たな決定になる。AgentSociety は半径+重力、CoPB は重力(R-47)=**先行はどちらもハフ型側**。

## §7 ネット広告をこのネットに載せる形

- 表示の数え方の標準: MRC「Pixel Requirement: Greater than or equal to 50% of the pixels in the advertisement were on an in-focus browser tab on the viewable space of the browser page」「Time Requirement: The time the pixel requirement is met was greater than or equal to one continuous second, post ad render」(動画は 2 秒・970×250 相当以上の大型は 30%)(#42)。3D 空間の広告は IIG 2.0 —「The ad must be a minimum of 1.5% of screen coverage to be considered viewable」「an ad angle no greater than 55 degrees for any one coordinate (on an absolute basis) relative to the game screen is recommended」+同じ 1 秒(#43)。
- v2 との対応: IIG 2.0 の「画面占有・角度・画素・持続」は既存の看板ゲート(段0 幾何 → 段1 p_see → 段2 注視時間 g → 段3 p_act・広告答申 §4)と**同じ形**。ネット広告は「検索結果・フィードの広告枠に出た」+「その体が画面注視(§5)している持続 ≥1 秒」を表示と数えれば、看板(IIG 準拠)とネット(MRC 準拠)を**同じ台帳の同じ列**(表示 → 店ページを開く → 来店 → 購入)に並べられる(expedient の対応づけ)。
- 効果の測り方: 業界は CTR と attribution(観測)で、因果(incrementality)とずれる=既存の広告答申(Gordon ら 2019・Blake ら 2015 の検索連動広告・等級 C)。シミュレーションは広告ゼロ腕(AB6-AD-ZERO)と同じ反実仮想で incrementality を直接出せる。段3 の p_act 上限と C1(カスケード)の合否ゲートはネット広告にもそのまま掛かる。
- メタバース広告の先行は IIG 2.0 の 1 本(ゲーム内広告の業界標準)に留めた。

## §8 v2 への写し方(選択肢・推奨ではない)

**A. 「シミュレーション内ネット」と「実データ初期値」**

| 観点 | シム内ネット(体が書き・エンジンが集約) | 実データ初期値 |
|---|---|---|
| 費用 | エンジン表(POI×評価の集計・順位)+口コミを書く短い LLM 呼。検索そのものはエンジン(呼ばない) | §2 のとおり保存できる源が無い。有償契約(FSQ Premium・ぐるなび法人)か事前同意の交渉 |
| 規約 | 自家生成=問題なし。OSM POI に別属性で足すのは水平層で share-alike 非発火(§1-5) | 評価点の保存は各規約で不可。Google は照合(test/validate)にも使えない |
| 指紋 | 順位の規則・冷スタート(初期評価)・書く確率=宣言+感度腕。Muchnik の群集化があるので**初期値が結果を動かしうる**(感度腕必須) | プラットフォームの偏り(ブランド・観光客)を輸入。LLM が店名から実評価を知っている事前知識と二重 |
| 照合 | パターン照合: Muchnik の非対称(+32%/+25%)・Luca の独立店だけの段差・§4 の情報源割合・Ursu の位置効果 | 店ごとに合うのは初期値の写し(循環)。holdout と較正が混ざる |
| 世界観 | 「世界の変化はエージェント行動の結果」(CLAUDE.md §3)に合う | 外生注入=conf 宣言つきフォールバック扱い |

- 混合案(既存資産で可能): POI の存在は OSM(+FSQ OS Places=Apache 2.0 で閉店日・カテゴリを補う案)、評価はシム内で生成、実データは**公表された集計値を照合パターンにだけ**使う。店名を LLM に見せる腕と隠す腕の対照(既存 lit の CitySim 教訓)は、実データを使わなくても LLM の事前知識経由で実評価が漏れるので必要。

**B. 検索と L3(満足化・距離項なし)**(すべて expedient・§6 の先行は B3/B4 側)
- B1 検索なし(L3 のまま): 初訪問の情報源の約 4 割(26.4+11.1%・複数回答)をモデル外に置く宣言が要る。
- B2 検索は候補を増やすだけ・並びは近い順・満足化: 連続の距離項なしで「近い順に最初に条件を満たす店」=介在機会型の距離減衰が出る(#37 と同型というのは本答申の推論・未検証)。
- B3 並び=プラットフォームの順位(評価・件数)+半径で切る: 位置効果(#36)を再現できるが、半径は段差の距離項=**L3「距離項なし」に触れる**。
- B4 検索結果の中で重力(AgentSociety・CoPB 型): **ユーザー決定「ハフ型は入れない」に正面から触れる**。
- 共通: 一覧の並べ替えと満足化はエンジン(System 1.5)、LLM に渡すのは最終候補 1〜3 件だけにすれば LLM の位置偏り(#41)を避けられる(expedient)。

**C. 「スマホ操作中」**(D-116 の活動の種別に触る)
- C1 活動の種別に 1 語追加(排他)/ C2 移動・その場に直交する旗「画面注視」(#31 の「使う人でも画面は 36%」には旗+割合の方が近い)。いずれも p_see に乗数(下向きの錨=Hyman の通話 25.0/51.3・渋谷は信号待ちで打ち消し #32)、歩く速さ −18〜30%(#30・#33)。
- C3 検索・閲覧・投稿の行為がこの旗を立てる=**ネットを使うこと自体が看板を見落とす物理コスト**になり、ネット広告と看板の注意の奪い合いが機構で出る。照合: 観察の瞬間割合 7〜8%(#30・#31)。

**D. パターン台帳ゲート(1 行)の候補**: 口コミ=Muchnik の非対称な群集化(書く人の経験率 21.1%・評価をつける 42.8% は #45 で上限の目安)/ 検索=初訪問の情報源割合(#29)と位置効果(#36)/ スマホ=瞬間割合 7〜8%(#30・#31)/ ネット広告=MRC・IIG の表示定義で看板と同じ列。

## §9 未確認・空欄

1. 食べログ API 終了(2014-06-30)の一次告知(二次のみ・Wayback も取れず)。2. ぐるなび無料 API 終了日 2021-06-30(二次のみ・api.gnavi.co.jp は 403)。3. Yelp 配布物に同梱の規約の現行版(2020 版の PDF のみ)。4. Yelp の 11 都市の一覧と東京非収録の公式記述。5. FSQ OS Places の東京・渋谷の件数。6. 著作権法 30 条の4 の逐語(e-Gov が JS 描画で取れず)と、食べログ規約の「法令上…認められている場合」との関係(弁護士判断)。7. 評価点(数値)の著作物性・不正競争防止法の限定提供データの論点(未調査)。8. 渋谷来街者に絞った店選び経路の調査。9. 「通りがかりで入った」割合の直接指標(リクルートは情報源・複数回答で代理)。10. カカクコム自身の利用者調査(店選び経路)。11. 総務省 通信利用動向調査の飲食店検索の率(未調査)。12. 澁谷・中村 2015 の図 5〜9 のスマホ有無別注目率。13. 「検索で選んだ店までの距離 > 通りがかり」の直接比較。14. Hyman 2010(R-47 で親未確認のまま)。15. 「歩きスマホで視野 1/20」の一次。16. 公開の口コミ・検索を物理世界と同時に持つ LLM シミュレーション。17. AgentSociety 2 が都市と SNS を同じ run で合成した例。18. Places Aggregate の派生値(Customer Value)で評価帯別件数を使う道の適法性。19. 南京の横断歩道観察(32.7%)は検索要約のみで不採用。20. 飲食店の来店 1 回あたりの口コミ投稿率(#45 は経験率・全商品)。21. #45 の調査年度(掲載 PDF が抜粋で表紙なし)。

## §10 親への確認依頼

1. **規約判定は文言の整理で法的助言ではない**。事業化・公開の前に弁護士確認を(特に §9-6・7・18)。
2. **Google 3.2.3(c)(vii)** は「AI の test/validate」を禁じる。台帳候補 L6(POI 人気の順位相関)で CitySim が使った Google 評価を現実側に使う道はこれで塞がれる可能性がある=L6 の現実側から外すかの判断。
3. **B2〜B4 はユーザー判断**(B3 の半径は「距離項なし」、B4 は「ハフ型は入れない」に触れる)。B2 の「満足化×近い順=介在機会型」は本答申の推論で未検証。
4. **C1/C2 は D-116 の契約語に触る**=先に聞く案件。C3 の「ネット利用が看板を見落とす」は設計者の指紋になる挙動の追加に当たるので同じく先に聞く。
5. シム内ネットの**冷スタート(初期評価)**は Muchnik の群集化で結果を動かしうる=初期値を感度腕に。
6. 渋谷の店選び経路を現実に取る手段(有償の会員アンケート等)は現実データへの接触=先に聞く(本答申では調べていない)。
