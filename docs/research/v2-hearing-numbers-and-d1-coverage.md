# 一次確認: ①会話可能距離の公開数表(R3-7)/②D1′前提=5エリアbbox被覆

作成 2026-09-04 / サブエージェント(Opus 5) / リポ書き込みなし・scratchpadのみ

凡例: **[F]**=当該URLを実際に開いて直読した事実 / **[S]**=二次・要約経由 / **[推測]**=本サブの推論 / **[未確認]**

---

# ① 結論

## タスク1(会話可能距離)

### 1. ISO 9921 原典 — 定義は取れた/数表は取れなかった

**ISO 9921:2003 の無償プレビュー(12ページ)を直読できた。しかし数表(Annex A の Table A.1 = 発声努力別の1m音圧、Annex E = SIL)はプレビューに含まれず、通話可能距離の数表は ISO 原典からは取得できていない [F/未確認]。**

ただしプレビューから **ISO 9921:2003 における SIL の定義そのもの**が直読できた。これは R3-7 の「SNR基準」設計に直接効く:

> 3.11 **speech interference level SIL** — difference between A-weighted speech level and the arithmetic average of sound-pressure levels of ambient noise in four octave bands with central frequencies of 500 Hz, 1 000 Hz, 2 000 Hz and 4 000 Hz [F]

つまり **ISO 9921:2003 の SIL は「暗騒音レベル」ではなく「A特性発話レベル − 4帯域平均暗騒音」= 実質SNR量**。古典的SIL(=4帯域平均そのもの)とは定義が違う。R3-7がSNRで書いているのは ISO 9921:2003 の語法と整合する [F+推測]。

併せて直読できた ISO の数値:

> 3.14 **vocal effort** — quantified objectively by the A-weighted speech level at **1 m** distance in front of the mouth [F]
>
> 5.1 People with a slight hearing disorder (in general the elderly) or non-native listeners require a higher signal-to-noise ratio (**approximately 3 dB**) [F]
>
> 5.2 This criterion represents a mean value for listeners with a normal hearing (**50 % coverage**). For **96 % coverage** of the population, an improvement is required that can be expressed by an **increase of the signal-to-noise ratio by 3 dB** [F]
>
> Table 1(直読・全行): 用途別の最低性能 — Alert/warning(簡単な文の理解)=Poor/Loud、Alert/warning(重要語の理解)=Fair/Loud、対人(critical)=Fair/Loud、対人(長時間の通常会話)=**Good/Normal**、公共空間の放送=Fair/Normal、パーソナル通信=Fair/Normal [F]

ISO 9921:2003 は **ISO 9921-1:1996 を取消・置換**した(Foreword 直読)[F]。9921-1 の副題が「SIL and communication distances …(SIL method)」であり、通話可能距離表は 1996年版の主題だったが、**1996年版本文は未読**[未確認]。

### 2. 代替として実読できた SIL/PSIL 通話可能距離の数表 2本

両者は 5 dB ずれるが、構造(距離2倍=−6 dB、発声努力1段=+6 dB)は一致。

**表A: TU Delft 建築物理 Knowledge Base A-11(2013年8月) Table 4 [F]**
「良好な音声明瞭度を得るための暗騒音の最大許容SIL値 [dB]」(SIL=500/1k/2k/4k の4帯域算術平均)

| 話者-聴者距離 [m] | normal | raised | loud | very loud |
|---|---|---|---|---|
| 0.3 | 65 | 71 | 77 | 83 |
| 0.9 | 55 | 61 | 67 | 73 |
| 1.5 | 51 | 57 | 63 | 69 |
| 1.8 | 49 | 55 | 61 | 67 |
| 3.7 | 43 | 49 | 55 | 61 |

> 注(直読): "In general, in case of a female speaker, these SIL values can be **reduced with 5 dB**." [F]

**表B: Engineering ToolBox "Required Voice Level at Distance" [F]**
(PSIL = 500/1k/2k の3帯域算術平均)

| 距離 (ft) | (m) | Normal | Raised | Very Loud | Shouting |
|---|---|---|---|---|---|
| 1 | 0.3 | 70 | 76 | 82 | 88 |
| 3 | 0.9 | 60 | 66 | 72 | 78 |
| 6 | 1.8 | 54 | 60 | 66 | 72 |
| 12 | 3.7 | 48 | 54 | 60 | 66 |
| 24 | 7.3 | 42 | 48 | 54 | 60 |

> 同ページ直読の補助数値 [F]:
> - 0.3 m において normal ≈ **70 dB**, raised ≈ **76**, very loud ≈ **82**, shouting ≈ **88** SPL(=発声努力の絶対レベル)
> - **PSIL = L_p(dBA) − 7**(dBAからの換算式)
> - "In social settings people often talk with normal voice levels at distances ranging **1 to 4 metre**. In such cases background noise levels should not exceed **55 to 60 dBA**."
> - "In outdoor play and recreational areas people often communicate with raised or very loud voices at distances **5 to 10 metre** and the background noise should not exceed **45 to 55 dBA**."

### 3. 導出: 「暗騒音 X dBA での通話可能距離」

換算は 距離2倍=−6 dB(逆二乗)。基準点は 0.9 m 行。PSIL=dBA−7 は表B直読 [F]、SIL(4帯域)≈dBA−8 は本サブの近似 [推測]。

| 暗騒音 | 表B(PSIL)基準 normal / raised / very loud / shouting | 表A(SIL 4帯域)基準 normal / raised / loud / very loud |
|---|---|---|
| 60 dBA | 2.0 / 4.0 / 8.0 / 16.0 m | 1.3 / 2.5 / 5.1 / 10.1 m |
| 65 dBA | 1.1 / 2.3 / 4.5 / 9.0 m | 0.71 / 1.4 / 2.9 / 5.7 m |
| **70 dBA** | **0.64 / 1.3 / 2.5 / 5.1 m** | **0.40 / 0.80 / 1.6 / 3.2 m** |
| 75 dBA | 0.36 / 0.71 / 1.4 / 2.9 m | 0.23 / 0.45 / 0.90 / 1.8 m |
| 80 dBA | 0.20 / 0.40 / 0.80 / 1.6 m | 0.13 / 0.25 / 0.51 / 1.0 m |
| 85 dBA | 0.11 / 0.23 / 0.45 / 0.90 m | 0.07 / 0.14 / 0.28 / 0.57 m |

→ **依頼形式の回答: 暗騒音 70 dBA では、通常声の会話可能距離は約 0.4–0.6 m、張り上げた声で約 0.8–1.3 m、非常に大きな声で 1.6–2.5 m、叫び(shouting)で 3.2–5.1 m。**

既存 factsheet の渋谷実測(街頭ベースライン 65–72 dBA・ピーク 80–85 dBA・繁華街街路 ≒70 dBA)に当てると、**スクランブル周辺の平常時で通常声 0.4–1.1 m / 叫び 3–9 m、ピーク時(80–85 dBA)は通常声 0.07–0.2 m・叫び 0.6–1.6 m**。

### 4. R3-7 の暫定値との突合 [推測]

表Bを SNR に読み替えると、0.3 m で normal(発話70 dB SPL)の閾値 PSIL=70 → 暗騒音 ≈77 dBA → 発話70 vs 騒音77 = **SNR ≈ −7 dB**。表Aで同様に計算すると **SNR ≈ −3 dB**。

→ **R3-7 の「内容理解=SNR≈0 dB」は、公開数表から逆算した −7〜−3 dB より 3〜7 dB 厳しい(保守的)。** 「存在検知≈−10 dB」は数表の射程外だが、理解閾値より 10 dB 低い設定は上記の理解閾値(−3〜−7)との差が 3〜7 dB しかなく、**検知と理解の分離が薄い可能性がある**。ISO 9921:2003 の「非母語話者/軽度難聴で+3 dB」「50%→96%カバレッジで+3 dB」は、この幅と同じオーダー [F]。

### 5. Brungart et al. 2020 = 一次確認できた [F]

**書誌**: Brungart DS, Barrett ME, Cohen JI, Fodor C, Yancey CM, Gordon-Salant S. **"Objective Assessment of Speech Intelligibility in Crowded Public Spaces."** *Ear and Hearing* **41**(Suppl 1): **68S–78S**, 2020. **doi:10.1097/AUD.0000000000000943**, **PMID 33105261**。(Ear Hear 2020 Oct 26 付。PMC全文 PMC7676620)

**該当記述(PMC全文からの直引用)**:
> "the SNR decreased by **0.44 dB for every 1 dB increase in ambient noise level above 60 dB**"
>
> "The average distance between participants, measured at the location of the heads, was **approximately 1 m**."

会場は大学図書館・カフェテリア・ランチ時のカジュアルレストラン・ハッピーアワーの混雑バー、被験者 174名 [S: 検索結果要約]。各会場の実測 dBA・実測発話レベルの個別値は WebFetch 要約が言い換えており、**逐語では未確認**[未確認]。

**含意 [推測]**: 人は騒音が上がっても**距離を詰めない(≈1 m 固定)**。声だけを 1 dB あたり 0.56 dB 上げる(=Lombard の不完全補償)。→ v2 で「うるさいと近づく」を実装するのは**現実と逆**。R3-7 の半径を騒音依存で縮める設計は、この論文と整合する(距離固定+SNR悪化=聞こえなくなる)。

### 6. 渋谷区「音のめやす」の測定距離 = 出典連鎖のどこにも書かれていない [F]

- **渋谷区ページ(noiseeffect.html)直読**: 表は全20項目(エアコン41-59 / 換気扇42-58 / 洗濯機64-72 / 掃除機60-76 / ピアノ80-90 / エレクトーン77-86 / ステレオ70-86 / テレビ57-72 / 犬の鳴き声90-100 / 子供のかけ足50-66 / 車のアイドリング63-75 / **人の話し声(日常)約50〜61 dB** / **人の話し声(大声)約88〜99 dB** ほか)。**測定距離・測定条件の記載なし**。注記は「このデータは『生活騒音の現状と今後の課題』(環境省)による」のみ [F]
- **東京都環境局「生活騒音」ページも同一表・同一出典表記・距離記載なし** [F]
- **一次出典を実読した**: 環境庁 大気保全局特殊公害課『生活騒音の現状と今後の課題』**昭和58年(1983)9月**(env.go.jp の PDF、全30ページ、スキャン画像・テキスト層なし → ページ画像を描画して判読) [F]
  - **表1「生活騒音の騒音レベル」には「測定条件」列が実在する**(直読):
    ピアノ 正面1m点(自由曲)82〜92 / ピアノ 正面1m点(バイエル104番)80〜90 / 電子オルガン 普通の演奏状態(正面1m点)79〜87 / ステレオ 昼間の聴取状態(正面1m)71〜88・夜間61〜78 / テレビ 昼間58〜74・夜間52〜65 / ボイラー 定常運転(ボイラー室の出入口から1m点)47〜50 / エアコン室内ユニット 正面1m点(強)45〜58・(弱)39〜52 / エアコン(室外)クーラー始動時42〜65 / 温風ヒーター 標準状態46〜52 / 洗濯機 正面1m(洗濯時)53〜66・(脱水時)51〜69 / 掃除機 真上1m点58〜70・横1m点59〜72 / 電動工具 横1m(負荷時)80〜97・(無負荷時)78〜94 / 換気扇 1m点(最多使用条件)44〜62 / バス 給水音(浴室の出入口)58〜76 / トイレ洗浄音(正面1m点)62〜71 / **アイドリング 横2m点(暖気)57〜62・(安定)51〜57、マフラー45°方向(50cm)(暖気)63〜77・(安定)60〜71** / **犬の鳴き声 正面5m 88〜100** / 子供の足音(上階からの足音を階下居室で測定)50〜67 / タイヤの落下音 JIS A 1418 59〜71 / **物売り(拡声機)車の後方5m 81〜93** [F]
  - **★ 重大な発見: 表1に「人の話し声」の行は存在しない。** 表2「生活騒音の特徴」は◯印の定性表でdB値なし [F]。さらに、渋谷区/都の表の値は表1と**一致しない**(掃除機 60-76 vs 58-70/59-72、洗濯機 64-72 vs 53-66/51-69、テレビ 57-72 vs 58-74/52-65、犬 90-100 vs 88-100)。
- **環境省『生活騒音パンフレット』(env.go.jp/air/seikatsu.pdf・全8ページ)** にも「騒音の目安」図はあるが **参考: 全国環境研協議会 騒音調査小委員会** であって、**88〜99 dB の話し声の値も距離記載も無い** [F]

**判定**: 渋谷区「音のめやす」の 大声 88-99 dB / 通常会話 50-61 dB は、掲示された出典(環境省1983)まで遡っても該当行が存在せず、**測定距離の定義は追跡不能**。R3-7 のアンカーとしては「距離未定義の孤立値」として扱うべき。表1の同種項目の測定条件が **「正面1m点」で統一されている**ことから 1 m が最も蓋然性が高いが、これは[推測]であって出典の記載ではない。

---

# ② タスク2: D1′前提=5エリアポリゴンとbboxの被覆確認

## 結論: 照会したが、ポリゴンは公開されていない(存在しない)

**渋谷区オープンデータ(ArcGIS Hub)の KDDI Location Analyzer 6レイヤは、すべて `type: "Table"` であり、ジオメトリを一切持たない。したがって `returnGeometry=true&outSR=4326` での照会は原理的に不可能で、bbox・頂点数・面積は取得できない。v2 bbox(lat 35.6505-35.6685 / lon 139.6905-139.7115)との被覆関係は判定不能。** [F]

## 実照会の生結果 [F]

FeatureServer ホスト: `https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services/`

| サービス | `/FeatureServer/0?f=json` の応答 |
|---|---|
| 131130_taizaijinkou_seibetu | type=**Table**, geometryType=**null**, extent=**null**, fields=8 |
| 131130_taizaijinkou_zokuseibetu | type=**Table**, geometryType=**null**, extent=**null**, fields=7 |
| 131130_tsuukoujinkou_seibetu | type=**Table**, geometryType=**null**, extent=**null**, fields=8 |
| 131130_tsuukoujinkou_nendaibetu | type=**Table**, geometryType=**null**, extent=**null**, fields=7 |
| 131130_tsuukoujinkou_zokuseibetu | type=**Table**, geometryType=**null**, extent=**null**, fields=7 |
| Location_Analyzerによる滞在人口データ（年代別） | type=**Table**, geometryType=**null**, extent=**null**, fields=7 |

- FeatureServer ルート `.../131130_taizaijinkou_seibetu/FeatureServer?f=json` は **`"layers": []` / `"tables": [{"id":0,...}]` / `fullExtent: null` / `initialExtent: null`** を返す [F]。=フィーチャレイヤが1枚も無い純テーブルサービス。
- レイヤ0のフィールド全リスト(直読): `名称`(文字列) / `種別` / `年` / `月` / `時間帯` / `性別` / `人数_の合計`(整数) / `ObjectId`。**座標・メッシュコード・町丁目コード等の空間キーは1つも無い** [F]
- レコード実例(直読): `{"名称":"渋谷駅中心エリア","種別":"滞在人口","年":"2018年","月":"1月","時間帯":"10時","性別":"女性","人数_の合計":237000}` → **エリアは文字列名のみ** [F]
- ArcGIS アイテムメタデータ(`arcgis.com/sharing/rest/content/items/4ea66bd8bec444fab1e2afbeb72e52df?f=json`)直読: `extent: []`(空)、`spatialReference: null`、`typeKeywords` に **`"Table"`** を含む。description は「渋谷駅周辺等の滞在人口データです。性別ごとに集計しています。」のみで**エリア範囲の定義文は無い**。`licenseInfo: "<p>CC BY</p>"` [F]

## 同一ArcGIS組織の全サービス走査 [F]

`https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services?f=json` → **サービス総数152**。全名称を目視走査したが、**渋谷駅周辺5エリアの区域ポリゴンに相当するサービスは存在しない**。空間データは 131130_park / _bicycle_lane / _aed / _shopping_street / L_ハチ公バス路線 / L_渋谷周辺バス停 / 01_第9回避難場所 / 14歳以下人口分布 / S_H27国勢調査_昼間人口 等の別系統のみ。

## 代替ルート(依頼どおり提示)

1. **SHIBUYA CITY DASHBOARD 本体は ArcGIS ではなく Power BI**。区ページ(`shibuya_city_dashboard_peopleflow_KDDI.html`)の外部リンク先を抽出した結果、埋め込みは3本の `https://app.powerbi.com/view?r=...`(テナント `04a1b2c4-c1b0-440a-8e8d-1742fc18657b`)[F]。Power BI 埋め込みはセッショントークン付き POST でしかクエリできず、**WebFetch/REST では境界形状を取り出せない** [F/推測]。地図が図形マップならレポート内部に境界が入っている可能性はあるが、公開APIとしては露出していない。
2. **区ページの文言が唯一の公式定義**: 「滞在人口は以下の5エリアを対象としています。**渋谷駅中心エリア(スクランブル交差点含む)/渋谷駅北西エリア/渋谷駅北東エリア/渋谷駅南東エリア/渋谷駅南西エリア**」。通行人口は宮益坂・道玄坂・表参道の3ストリート [F]。→ **「中心エリアはスクランブル交差点を含む」以外に地理的手がかりは無い**。
3. **KDDI Location Analyzer 側の一般的仕様**: 「渋谷駅周辺を起点とする半径500mのエリア」といった記述がベンダーページにあるが、これは製品説明であって本データセットのエリア定義ではない [S・要注意]。
4. **確実な取得ルートは区への照会のみ**: グローバル拠点都市推進課 都市データ活用推進主査 03-3463-1529 / div-smartcity@shibuya.tokyo(区ページ直読)[F]。前回サブが平日/休日軸で挙げたのと同じ窓口。

## D1′への含意 [推測]

**前回サブが「★最重要の前提条件」とした bbox 整合の確認は、公開データだけでは永久に閉じない。** 選択肢は3つ:

- **(a)** 区へ照会してエリア境界を入手 → 入手できれば D1′ を予定どおり採用。
- **(b)** 境界不明のまま D1′ を採用し、**「5エリアの合計範囲 ≠ v2 bbox」を expedient タグ付きの既知の不整合として台帳に宣言**。D1′ は絶対人数ではなく**エリア内24時間シェアのJSD・ピーク時刻順序・深夜残存率順序**で判定する設計なので、境界のズレは「エリアの性格づけ」を歪めるが「形の比較」自体は成立しうる。
- **(c)** D1′ を降格し、境界が明示された別データ(MLIT人流OD等)へ差し替え。

現時点の証拠は (b) を許容する。ただし **「5エリア和が v2 bbox を覆う」とは書けない**——覆うとも覆わないとも言えない、が正しい記述。

---

# ③ 未確認・できなかったことの列挙(正直な申告)

## タスク1

- **ISO 9921:2003 Annex A(Table A.1: 発声努力 normal/raised/loud/very loud/shout の 1m A特性発話レベル)は未読**。無償プレビュー(iteh.ai サンプル)は本文 p.1–5 までで、Annex A(p.7-)・Annex E(p.18)・Annex F(Table F.1, p.19-)・Annex H は含まれない。
- **ISO 9921-1:1996(SIL法・通話可能距離の本体)は本文未読**。表題・置換関係のみ確認。
- ISO 全文を掲載していると見られるミラー(`www.mahuilab.top/images/5/52/ISO_9921-2003.pdf`)は **TLS証明書のホスト名不一致で接続失敗**。加えて著作権上、標準本体の全文取得は行っていない。
- ANSI S3.14 / ANSI S12.65 の原表は未読。Webster J.C. "Speech Interference by Noise" (Proc. Inter-Noise 74, INCE, p.558) は**書誌のみ**(SFU Sonic Studio 経由)で**本文未読**。
- 表A(TU Delft)・表B(Engineering ToolBox)はいずれも**二次教材**であり、出典標準を明記していない。**両者は 5 dB 系統差**があり、どちらが ISO 9921 準拠かは未確定。列見出しも異なる(表A: normal/raised/loud/very loud、表B: Normal/Raised/Very Loud/Shouting)。
- FAA AC 20-133・ScienceDirect Topics・CCOHS・PSU NoiseQuest・Wikipedia は 403 または該当表なしで取得できず。
- Brungart 2020 の**会場別 dBA・発話レベル・SNR の逐語値は未確認**(WebFetch要約が言い換え)。原文の当該段落は再読していない。
- 「音のめやす」の 88-99 dB(大声)の**測定距離は最終的に不明**。1983年報告の表1に該当行が無く、渋谷区/都の表の他項目の値も表1と一致しないため、**渋谷区表の真の出典が特定できていない**(1983年版以外の改訂版・別資料の可能性)。
- 環境省 1983 PDF はスキャン画像でテキスト層ゼロ。**表紙・目次・p.1・p.2(図2)・p.4(表1)・p.5(表2)のみ画像判読**し、p.3 および p.6–26 は未読。話し声の値が後半にある可能性は排除できていない。

## タスク2

- **5エリアのbbox・頂点数・面積は取得できなかった(データが存在しないため)**。「はみ出すか」「bboxのうち覆わない部分」も判定不能。
- Power BI レポート内部の図形データは未取得。
- 区への電話/メール照会は本タスクの範囲外(実施していない)。
- 152サービスは**名称のみ**の走査。各サービスの中身までは開いていない(KDDI6本を除く)。名称から判別できない形で5エリア境界を持つサービスが紛れている可能性は完全には排除していない。

## 手続き上の申告

- **依頼の「ファイルのダウンロード・保存はしない」に対する例外**: WebFetch ツールがPDF応答を自動的にローカル(`.claude/projects/.../tool-results/`)へ保存する仕様のため、ISO 9921:2003プレビュー・klimapedia A-11・環境省1983報告・環境省パンフ・arXiv 2106.15916 の5本が意図せず保存された。**本サブが明示的にダウンロードコマンドを実行したものは無い。** テキスト抽出のため PyMuPDF で読み、環境省PDFのページ画像を scratchpad に `_moe1983_p*.png` として描画した(判読のため。scratchpad内)。
- ArcGIS REST は JSON応答を標準出力で読むのみ・ファイル保存なし [F]。
- リポジトリへの書き込み・コミットは一切していない。子サブエージェントは起動していない。

---

# ④ 実読URL一覧(証拠)

| # | URL | 何を直読したか |
|---|---|---|
| 1 | https://cdn.standards.iteh.ai/samples/33589/73fc1eef076a45b1a63d78733cd01a3e/ISO-9921-2003.pdf | ISO 9921:2003 無償プレビュー12p。3.11 SIL定義・3.14 vocal effort・5.1/5.2 の+3dB・Table 1・目次(Annex A/E/F の所在)・9921-1:1996置換 |
| 2 | https://klimapedia.nl/wp-content/uploads/2019/11/AE011-Speech-Intelligibility.pdf | TU Delft Knowledge Base Building Physics A-11 (2013-08)。**Table 4 = SIL最大許容値×距離×発声努力**、女性話者−5dB、STI/AI表 |
| 3 | https://www.engineeringtoolbox.com/voice-level-d_938.html | **Required Voice Level at Distance 表(PSIL)**、0.3m での発声努力別SPL、PSIL=dBA−7、社交場面1-4m/55-60dBA |
| 4 | https://www.engineeringtoolbox.com/speech-interference-levels-d_1138.html | SIL定義(3帯域)・図の説明(数表は画像のみで取得不可) |
| 5 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7676620/ | Brungart 2020 全文。0.44 dB/dB・平均距離≈1m・書誌/DOI/PMID |
| 6 | https://www.city.shibuya.tokyo.jp/kankyo/kankyo/soon/noiseeffect.html | 渋谷区「音のめやす」全20項目・距離記載なし・出典表記 |
| 7 | https://www.kankyo.metro.tokyo.lg.jp/noise/noise_vibration/daily_life_noises | 東京都「生活の中で発生する音の大きさの目安」同一表・距離記載なし |
| 8 | https://www.env.go.jp/air/ippan/kinrin/attach/1983_09.pdf | 環境庁『生活騒音の現状と今後の課題』昭58-9(30p・スキャン)。表紙/目次/p.1/図2/**表1(測定条件付き)**/表2 |
| 9 | https://www.env.go.jp/air/seikatsu.pdf | 環境省 生活騒音パンフ(8p)。騒音の目安は全国環境研協議会出典・話し声88-99なし |
| 10 | https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services?f=json | 渋谷区ArcGIS組織の全152サービス名 |
| 11 | https://services3.arcgis.com/UtdeFTavkHfI94t2/arcgis/rest/services/131130_taizaijinkou_seibetu/FeatureServer?f=json および `/0?f=json`, `/0/query?...` | layers=[] / tables=[0] / type=Table / geometryType=null / extent=null / 全8フィールド / レコード実例 |
| 12 | 同上を他5レイヤについて(131130_taizaijinkou_zokuseibetu, 131130_tsuukoujinkou_{seibetu,nendaibetu,zokuseibetu}, Location_Analyzerによる滞在人口データ（年代別）) | 6本すべて Table・geometryなし |
| 13 | https://www.arcgis.com/sharing/rest/content/items/4ea66bd8bec444fab1e2afbeb72e52df?f=json (および ed587c1134334e259c8cbcefaaf29b2a) | title/snippet/description/licenseInfo(CC BY)/extent=[] /typeKeywords に Table |
| 14 | (scratchpad実読) `_shibuya_city_dashboard_peopleflow_KDDI.txt` / `.html` | 5エリア名の公式表記・3ストリート・問合せ先・Power BI 埋め込みURL 3本 |
| 15 | https://cdn.standards.iteh.ai/samples/17805/fe19a3e1eded411886fcf28a29aad0e7/ISO-9921-1-1996.pdf | **未取得**(検索結果でURLは確認したが本文は開いていない) |
