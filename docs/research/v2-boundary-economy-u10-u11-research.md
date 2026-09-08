# レーンU 答申: 境界(U10・来街の決定)と経済SFC(U11) — R4リサーチ

> **親検収(Fable・2026-09-06)**: 出典を親が一次確認した。✔=親が実読して数値一致。
> - ✔ TF Resource(実読): 「There are no applicable criteria guidelines for checks of external travel models.」逐語一致。同ページの±10%(0.90-1.10)は域内の発生集中バランスの目安であって外部交通ではない→**コードン照合の許容誤差はv2の自前宣言(expedient)**。既存台帳の「±10%が典型的合格条件」は要修正。
> - ✔ Caiani et al. 2016 JEDC(PDF実読): 「the sum of the net worth of all the agents in the economy (including government and central bank) is exactly equal to the values of real assets in every simulation round」逐語一致・主体数=家計8,000/消費財企業100/資本財企業20/銀行10/公務員1,360(パラメータ表)・「stocks seem to appear ex-nihilo rather than be realized through a transfer of resources」(倒産後の参入に関する不整合の警告)逐語一致。
> - ✔ 家計調査2025年平均(総務省統計局PDF実読): 二人以上世帯314,001円/月・単身173,042円/月・総世帯259,880円/月・勤労者世帯(二人以上)の平均消費性向65.0%・黒字186,111円(黒字率35.0%)・預貯金純増177,061円。
> - ✔ 東京観光財団 令和5年度渋谷マーケティング調査(PDF実読): 滞在中の消費額 平均7.1万円(宿泊者10.4/非宿泊者5.6)・令和元年3.3万円・非宿泊者滞在4.9時間(元年4.5)・有効回収2,628・8地点・実査19日(11-12月土日中心・12-20時)。**注意**: 「滞在中」の範囲(渋谷滞在中か訪日滞在中か)は本文で明示されない=持込金アンカーとしては上限側の目安。
> - ✔ GATSim(arXiv 2506.23306v2実読): 「A synthetic population of 70 individuals is generated using GPT-4o」・大規模実験なし・呼数/トークンの記載なし。
> - 呼数試算(来街判断≈8.1万呼/日=予算の2%)は答申の推測(パラメータ仮)。expedient 8件(E-a〜E-h)は答申自身が宣言。**用語訂正**: MER=EVE Onlineの月次経済レポート(Robuxではない)。
> - 正典化: docs/research/v2-boundary-economy-u10-u11-research.md(U10境界・U11経済SFCの根拠)。


作成: 2026-09-06 / 担当: リサーチサブ(Opus 5) / 検収: 親(Fable) / 決定: ユーザー
規律遵守: 子サブ未起動・出典は実読ページのみ引用・未読は「空欄(未確認)」・ダウンロード実行なし(WebFetchのPDF読解のみ)・リポジトリ非書込

---

## 要約(10行)

1. **交通実務には「域外を集約ノードで持つ」正典がある**: external station(cordon station)にI-X/X-I/X-X の3類型を割り当てる。ただしTF Resourceは**「外部交通モデルの検査には適用可能な基準ガイドラインは存在しない」と明記**——既存台帳の「コードン±10%が典型的合格条件」は**要再検証(反証寄りの証拠)**。
2. **LLM都市モビリティ実装の到達点はまだ極小**: GATSimの実験人口は**70人**。40万体でLLMに日次来街判断をさせる先行例は**空欄(未確認=見当たらない)**。
3. GATSimは**再計画の起点を4種に限定**(日の開始/待ち時間/反省周期/活動終了)——v2のT0習慣+差分LLMの直接の先行根拠。
4. **U10推奨=案A「外界1ノード+活動スケジュール(T0習慣)+差分時のみLLM」**。重力モデル日次抽選(v1型)は「エージェントが決める」を満たさず**主案不可・ablation対照としてのみ保持**。
5. KDDI滞在人口曲線は**状態同化に使わない**(事後検証専用)。較正はセンサス/PT側、KDDIは形状照合(相関・ピーク時刻・平日休日差)に限定。
6. **U11のSFC正典はCaiani et al.(JEDC 2016)**——実読で確認: 家計8,000/消費財企業100/資本財企業20/銀行10。検算は**(a)行和列和=0(四重記入)**と**(b)全主体の純資産合計=実物資産価額**の2本立て。後者が**v2の月次センサスの主検算式**として最適。
7. 保存則の実装形=**transfer(payer,payee,amount)単一API+残高直接代入の静的禁止**(既決)に、Caianiの検算2本と「退出・参入時のex-nihilo禁止」を追加。
8. **初期所持金の実数アンカー(2025年家計調査・実読)**: 二人以上世帯 消費支出314,001円/月、単身173,042円/月、勤労者世帯の平均消費性向65.0%・黒字率35.0%・預貯金純増177,061円/月。→ sink(消費)とfaucet(給与)と退蔵(貯蓄)の比率が公的数値で固定できる。
9. **来街者の持込金**: 訪日外国人の渋谷滞在中消費額 **平均7.1万円**(令和5年度・非宿泊者5.6万円・非宿泊者滞在4.9時間・n=2,628)。日本人来街者の1回あたり消費額は**空欄(未確認)**。
10. **PT調査の目的別構成比の数値は公開概要では図のみ**(数表未取得)=**空欄(未確認)**。取得経路はe-Stat「目的種類別代表交通手段別OD表」(stat_infid=000032066127)を指定済み。

---

## 1. U10 境界(来街の決定): 標準手法と先行例

### 1-1. 交通実務の標準形 = external station + I-X/X-I/X-X

米国の旅行需要モデル検証の実務規範(TF Resource, TRB系コミュニティwiki)を実読。

> "Comparing total modeled base year vehicle trips (including resident I-X, nonresident X-I, and X-X) trips to the base year traffic count for each external station."
> — TF Resource, *Model Validation and Reasonableness Checking / Amount Of Travel*（実読✔）

3類型の定義(同ページ・要約):
- **I-X** = 域内居住者の域外行き / **X-I** = 域外居住者の域内行き / **X-X** = 通過(両端が域外)

**★最重要の反証**: 同ページは外部交通モデルの検査基準について次のように述べる。

> "There are no applicable criteria guidelines for checks of external travel models."
> — 同上（実読✔）

→ 既存の `v2-boundary-deep-research.md` 面1にある「コードン横断総量が実測**±10%以内**が典型的合格条件」は、少なくともTF Resourceでは支持されない。**親の一次確認リスト#1**に載せる。v2としては「±X%は自前で宣言する数値」であり、**外部権威に依拠できない**と扱うのが安全。

ActivitySim系の「auxiliary demand(補助需要)」の位置づけ(検索要約・原文の該当箇所は**未読=要確認**): 貨物・訪問者・I-X/X-I/X-X・特別発生源は**活動ベースモデルの本体には含めず、補助モデルで別建てする**のが標準。→ v2に翻訳すると「来街者を本体エージェントとして持つ」のは**実務標準からの逸脱=新規性の所在**でもある。

### 1-2. 重力モデル / 離散選択 / 活動ベース

| 手法 | 域外の扱い | v2適合 |
|---|---|---|
| 重力モデル(集計) | 外部ゾーンを1ゾーンとして引力式に組込み | 個体が決めない=**U10の第一候補と不整合** |
| 目的地選択の離散選択(MNL/Nested) | 外部ゾーンを選択肢集合に追加 | **選択肢集合として使える**(T0習慣の生成側) |
| 活動ベース(MATSim/ActivitySim) | external stationの外生行列 or 補助モデル | **日次計画=活動チェーン**の形がv2に直結 |
| LLM生成エージェント(GATSim等) | 前例なし(閉鎖名簿) | 規模が桁違いに小さい |

MATSimでの外部交通の扱いについて、ETH系一次文献の該当記述は**空欄(未確認)**。検索では「コードン課金シナリオ(Zurich/Barcelona/NYC/SF)」の応用例が多数出るが、外部ゾーン設計そのものを規定した節を実読できていない。

### 1-3. LLM都市エージェントの先行例と規模

- **GATSim (Liu, Li, Ma, arXiv:2506.23306 / Transportation Research Part C)** — HTML版実読✔。
  > "A synthetic population of 70 individuals is generated using GPT-4o with carefully designed demographic constraints to ensure realistic population structure."

  → **70体**。LLMモビリティシムの実験規模はv2(40万体)の**約1/5,700**。
- **AgentSociety (arXiv:2502.08691)** — 検索要約では「10k超のエージェント、500万インタラクション」。**原文未読=要確認**。
- UrbanLLM / CityBench — 本ラウンドでは**空欄(未確認)**。
- 既存台帳(`v2-boundary-deep-research.md` 面3)の結論「LLM社会シムで開放系境界を実装した先行例はゼロ」は、本ラウンドでも**反証は見つからなかった**(補強)。

### 1-4. KDDI型滞在人口曲線の使い方 = 事後検証専用

**設計原則(答申)**:
- **状態同化(data assimilation)には使わない**。理由は既存台帳の面1で確定済み(較正データとholdoutの3階層管理・「境界流量とPOI人気度を両方較正に使うと検証対象が枯渇」)。
- **較正に使う系**: 国勢調査(昼夜間人口・従業地通学地)/PT調査(目的別・時間帯別)/大都市交通センサス(乗換・定期券)。
- **holdout(照合)に使う系**: KDDI 5エリア×24h×属性の滞在人口曲線。照合する統計量は**水準ではなく形状**を主に:
  1. 24hカーブのピーク時刻(エリア別・±30分)
  2. ピーク/谷比(dynamic range)
  3. 平日/休日のカーブ形状差
  4. エリア間の位相差(例: 道玄坂の夜ピークとオフィス街の朝ピーク)
  5. 属性別シェア(年代・性別)の時間帯変動
- **水準(絶対人数)は較正側の国勢調査で既に拘束されるため、KDDIの水準一致は「独立な検証」にならない**——形状指標のほうが情報量が高い。【推測】だが、面1の「境界感度は集計量でなく構造に出る」(疫学ハイブリッドの教訓)と整合。

### 1-5. 来街目的の構成(東京圏)の数値

**取得できた実数**:

| 項目 | 値 | 出典(実読✔) |
|---|---|---|
| 渋谷来訪 訪日外国人の訪問理由 | 「カルチャーを体感したかった」48%/「行きたい商業施設があった」39%/「行きたい施設があった」31%/「家族・友人から訪問を薦められた」21%/「行きたい飲食店があった」20% | TCVB 令和5年度 渋谷マーケティング実態調査(n=2,628) |
| 区部住民が「ふだん最も頻繁に利用する繁華街」 | 新宿20.3% / 池袋16.4% / 銀座11.0% / **渋谷9.9%**(区部住民4,077票) | 東京都 繁華街利用実態調査(平成13年3月公表・調査は平成12年9〜10月) |
| 同・都内全体プール | 新宿19.3% / 池袋11.8% / 銀座7.7% / **渋谷7.5%** | 同上 |
| 繁華街へのアクセス手段 | 「電車」全体53.8%、新宿・銀座・渋谷・池袋は**軒並み70%超**(新宿80.3%)、乗用車は**5%前後** | 同上 |
| 渋谷センター街入口 12時間(10-22時)通行量 | 平日**113,568人**・休日11万2千人 | 同上 |
| 首都圏 定期券発売枚数 | 平成27年890万枚 → 令和3年**638万枚(72%)** | 第13回大都市交通センサス(令和5年3月28日公表) |
| 東京都区部の在圏人数(交通ICカード集計) | **529万人** | 同上 |

**空欄(未確認)**:
- 東京都市圏PT調査 第6回の**目的別トリップ構成比の数表**。相模原市によるPT解説資料(19p・実読)を確認したが、目的構成・外出率・原単位は**すべて図(グラフ)提示で数値が本文に無い**。同資料で確認できた定性事実のみ: 「市外との移動における目的に着目すると、東京区部や川崎市は通勤目的が多い一方、町田市や県央地域は私事目的の移動が多くなっています。」(実読✔)/ 1人あたりトリップ数のグラフ軸は2.0〜3.5の範囲。
- 大都市交通センサスの目的別(通勤/通学/私事)構成比。第13回公表資料(12p・実読)は定期券発売実績とICカード在圏人数が中心で、目的別構成比の表は含まれない。
- **取得経路(確定)**: e-Stat「東京都市圏パーソントリップ調査/分布関連/目的種類別代表交通手段別OD表」(toukei=00600550, tstat=000001151670, stat_infid=000032066127)。ここから渋谷区着トリップの目的別を直接引ける見込み。次ラウンドの必須タスク。

---

## 2. U10 の計算形: 40万体の日次「来るか来ないか」をLLMなしで回す

### 2-1. 先行の設計(GATSim・実読✔)

GATSimは**再計画の機会を明示的に限定**している:

> "Plan revision opportunities occur at strategically selected moments including: 1) simulation day initiation; 2) waiting periods at network nodes such as traffic intersections or transit stops; 3) periodic intervals during ongoing activities based on reflection frequencies; and 4) natural transition points when activities conclude."

日次計画の表現形:
> "a chronologically ordered sequence of activities the agent intends to perform throughout the day, with each activity represented through a structured tuple."

→ **v2への直接の移植**: 「1日の活動列 = 構造化タプルの時系列」+「再計画は列挙された少数の起点でのみ」。GATSim自体は70体なのでこの限定でもLLM呼が残るが、v2は**T0習慣を既定路線にして再計画起点をさらに絞る**。

### 2-2. 推奨する計算形(3段の階層)

```
T0(習慣・LLM呼ゼロ)      : 各persistent_idが持つ週次活動スケジュール表(曜日×時刻×活動×場所)
                            → 「来街するか」は表の参照だけ。1体あたり数十バイトの固定長。
T1(確率的差分・LLM呼ゼロ) : 天候/イベント/曜日/前日疲労などの少数スカラーで
                            (a)実行/不実行 (b)時刻シフト (c)場所差替 を確率的に決める。
                            エンジン内の閉じた式。Bernoulli/カテゴリカルの抽選のみ。
T2(再計画・LLM呼あり)     : 「T1の抽選が既定路線から逸脱した」「新規イベントに遭遇した」
                            「関係者から誘われた」「計画が破綻した」ときだけLLMを呼ぶ。
```

**設計上の要点(v1の矛盾の根治)**: 抽選するのは**「来街するか否か」ではなく「習慣からの逸脱が起きたか」**。来街の是非は本人のスケジュール表(=過去にLLMが作った/更新した本人の産物)が決める。これで「エージェントが来街を決定する」を満たしつつ、日次のLLM呼を消せる。

**スケジュール表の生成**:
- 初回のみLLMで生成(ペルソナ→週次スケジュール)。40万体 × 1回 = **40万呼(初期化コスト・1回限り)**。
- 以降は**更新イベント時のみ**(転職・引越・進学・関係変化)。年率で数%オーダー。

### 2-3. 呼数への含意(予算400万呼/シミュ日に対して)

【推測を含む試算・パラメータはすべて仮】

| 層 | 母数 | 1体あたり日次呼 | 日次合計呼 |
|---|---|---|---|
| 在場40万体のうち住民・常連(仮に15万) | 150,000 | T2発火率5% × 1呼 | 7,500 |
| 在場のうち通勤通学(仮に18万) | 180,000 | T2発火率2% × 1呼 | 3,600 |
| 一度きり来街者(仮に7万) | 70,000 | 入場時1呼(目的地選択) | 70,000 |
| **来街判断だけの小計** | | | **約8.1万呼/日** |

→ **来街判断は400万呼予算の約2%で収まる**。残る398万呼を会話・購買・仕事・内省に回せる。**逆に、来街判断を毎日LLMで回すと40万呼/日=予算の10%を1機能で消費**し、しかもT0習慣がないので日々の一貫性(常連関係)が壊れる。**T0習慣型の採用は呼数だけでなく再訪同一性の観点からも必須**。

**expedient宣言が要る箇所**: T1の確率式(天候→来街確率の弾力性など)は現時点で出典なし。**expedient**とタグ付けし、感度試験で「結果を駆動していない」ことを示すか、PT調査の天候別データで裏を取る。

---

## 3. U11 経済SFC: 先行例と最小設計

### 3-1. SFC-ABM の正典 (Caiani, Godin, Caverzasi, Gallegati, Kinsella, Stiglitz 2016, JEDC 69:375-408) — 全文PDF実読✔

**規模(Table 3 Parameters)**:
| 主体 | 数 |
|---|---|
| 家計 (sizeΦH) | 8,000 |
| 消費財企業 (sizeΦC) | 100 |
| 資本財企業 (sizeΦK) | 20 |
| 銀行 (sizeΦB) | 10 |
| 公務員 (Ngt) | 1,360(定数) |
| 消費財企業の初期労働者 (Nc0) | 4,000 |
| 資本財企業の初期労働者 (Nk0) | 1,000 |
| 初期失業率 (u0) | 0.08 |

→ **SFC-ABMの実装規模は1万体オーダー**。40万体SFCは**前例なし**(既存台帳の「区レベルSFCは前例なき粒度」を規模面でも補強)。

**検算法(2本立て・原文引用)**:

> "We then propose two complementary methods to avoid misspecifications, based on the accounting matrices traditionally employed in the aggregate SFC literature: 1. The first method consists in deriving the Transaction Flow Matrix and Full Integration Matrix (Godley and Lavoie, 2007) of the model. Compliance with Copeland's quadruple entry principle requires that **every row and column of the matrices sum up to zero in every single moment of the simulation**."

> "2. ... The method consists in checking that **the sum of the net worth of all the agents in the economy (including government and central bank) is exactly equal to the values of real assets in every simulation round**. This can be easily explained by the fact that real stocks are the only assets in the economy which do not have a liability counterpart."

→ **方法2がv2の月次経済センサスの主検算式**として最適。行列を毎ステップ組むより安く、実物資産(在庫・什器)の扱い(既存台帳「実物資産の行は0にならない」)と整合する。

**参入・退出のex-nihilo禁止(原文の警告)**:

> "An example of inconsistency is represented by the exit-entry process of firms, where it is usually assumed that new firms enter the market to replace defaulted ones with a given stock of capital and liquid assets. The question then arises of where does this additional capital come from and whom is providing this additional liquidity. Since these stocks seem to appear ex-nihilo ..."

→ v2は「倒産→退出→**新規参入**のフルサイクル」を新規性候補に置いている(既存台帳)。そのフルサイクルは**まさにCaianiが名指しした不整合の巣**。**参入時の初期資本は必ずどこかの主体からのtransferで来ること**を型で強制する規則(R4)を追加すべき。

- 実装ツール: JMAB (Java Macro Agent Based)。「to ensure and check the model stock-flow consistency at the **macro, meso and micro levels**」(原文)。→ v2も**3層(全体/部門/個体)で検算**する。

### 3-2. ゲーム経済のセンサス型運用

**用語の訂正(親への注意)**: 依頼文にある「**MER(Roblox経済レポート)**」は用語の取り違えの可能性が高い。**MER = Monthly Economic Report は EVE Online(CCP Games)** の月次経済レポートの名称で、ISK faucets / sinks / money supply を毎月公開する運用。Roblox は経済レポートを "Annual Economic Impact Report" 等の名で出す別系統。

- **EVE Online MER**(faucet/sink運用): faucet=ISKが経済に入る経路、sink=出る経路を科目別に月次公開。「money supplyが直近4.5年で約2倍」「11月の前年比+7.5%、ISK支出は+15%で1 quadrillion ISK超」等の指標を継続追跡。
  **出典状況: 二次情報(ブログ)のみ。CCP公式MERページは未読=要確認**。v2に移植するのは「**faucet科目・sink科目・貨幣供給量を毎月同じ表形式で出し続ける**」という運用形そのもの。
- **Roblox Annual Economic Impact Report (2025-09)** — 実読✔:
  > "From March 2024 to March 2025, Roblox creators earned over $1 billion globally, a year-over-year increase of more than 31%"
  > "The median creator participating in the DevEx Program receiving $1,575 USD during the 12 months ended December 31, 2024"
  上位1,000開発者は2024年平均$820,000、上位10は平均$3,390万、DevEx参加は24,500超。
  **ただし同レポートは creator payout 中心で、Robuxの流入/流出(faucet/sink)の内訳は載っていない**(実読で確認)。→ **v2が移植すべきはEVE型(科目別faucet/sink)であってRoblox型(payout開示)ではない**。
- **UOの退蔵(hoarding)教訓**: 本ラウンドでは一次情報を確認できず**空欄(未確認)**。

### 3-3. 最小の勘定科目セット(5部門)

依頼の5部門(世帯・店舗・雇用主・外界・政府)に、Caiani/G&Lの標準に合わせ**銀行**を加えるか否かが分岐点。既存台帳U-B面1は「銀行1部門+ローン行+預金行の3行追加」を推奨済み(現金のみ経済は賃金原資を説明できない)。本答申はそれを支持する。

**バランスシート行列(BS)最小形** (+=資産, −=負債, Σ行=0 が原則・実物資産行のみΣ≠0):

| | 世帯 | 店舗 | 雇用主 | 銀行 | 政府 | 外界RoW | Σ |
|---|---|---|---|---|---|---|---|
| 現金 | +HC | +SC | +EC | −CASH | (発行) | +RC | 0 |
| 預金 | +HD | +SD | +ED | −D | | +RD | 0 |
| 貸出 | | −SL | −EL | +L | | | 0 |
| 在庫(実物) | | +INV | | | | | **≠0** |
| 什器・設備(実物) | | +K_S | +K_E | | | | **≠0** |
| 純資産 | −V_H | −V_S | −V_E | −V_B | −V_G | −V_R | **−(実物計)** |
| Σ | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**取引フロー行列(TFM)の最小科目**(列=部門、企業系は経常/資本の2列に分割):

| フロー科目 | 源(+) | 使途(−) | faucet/sink分類 |
|---|---|---|---|
| 賃金 | 世帯 | 雇用主・店舗 | 域内は内部移転 / **域外雇用主→域内世帯 = faucet** |
| 域外給与の持込 | 世帯(通勤者) | RoW | **faucet(境界)** |
| 来街者の持込金 | RoW | — | **faucet(境界)** ※入場イベントで計上 |
| 財・サービス購入 | 店舗 | 世帯・来街者 | 域内は内部移転 |
| 域外での購入(持ち出し) | RoW | 世帯 | **sink(境界)** |
| 仕入(域外サプライヤ) | RoW | 店舗 | **sink(境界)** |
| 税 | 政府 | 世帯・店舗・雇用主 | **sink** |
| 移転・給付 | 世帯 | 政府 | **faucet** |
| 利子 | 銀行/預金者 | 借入者/銀行 | 内部 |
| 貸出実行/返済 | (貨幣の創造/消滅) | | **faucet/sink(制度)** |
| 貯蓄(預金純増) | — | — | **退蔵項(sinkではない・ストックに残る)** |
| 残差科目 | — | — | **説明不能分の受け皿・毎月ゼロでない値を報告** |

**faucet/sink全登録をエンジンで検査する仕組み(答申)**:

1. `transfer(payer, payee, amount, account_code)` の**単一API**。残高への直接代入は型で不可能にし、静的検査(AST走査)でCIゲート。
2. **account_codeは列挙型**。列挙にない科目でのtransferはコンパイル/起動時に落ちる。→「登録漏れのfaucet」が原理的に作れない。
3. **RoWは無限の財布ではなく残高を持つ1部門**(既存台帳U-B R2)。来街者の持込金はRoW残高の同額減として記帳される。
4. **境界通過イベント(boundary_cross)と金銭移動を同一トランザクションで**。入場=持込金faucet、退場=持ち出しsink。境界イベントの件数と金額が突き合わない場合は即fail。
5. **参入時の初期資本はtransfer由来のみ**(新規則R4・Caianiの警告への対応)。
6. **通貨は整数円・ε=0でassert**(既存台帳U-B T2)。

**保存則テストの形(pytest)**:

```
test_row_col_zero        : 各期のTFM 行和=0 かつ 列和=0 (実物資産行を除く)  [毎ステップ・小規模ラン]
test_networth_eq_real    : Σ全主体の純資産 == Σ実物資産価額               [毎日・全規模ラン] ★主検算
test_no_direct_balance   : 残高への直接代入がコード中に存在しない          [静的・CI]
test_account_coverage    : 実行中に出た全transferのaccount_codeが台帳に登録済み [ラン後]
test_boundary_money      : boundary_crossイベント件数 × 金額 == RoW残高変化 [毎日]
test_redundant_equation  : 冗長方程式(実装しない1本)が毎期0                [毎ステップ]
test_hoarding_reported   : 退蔵(預金・現金の非取引残高)が月次センサスに項として出る [月次]
test_residual_bounded    : 残差科目の絶対値が総フローのX%未満(Xは事前宣言)  [月次]
```

**日次/月次センサスの出力表**(EVE MER型):
- 日次: faucet科目別金額 / sink科目別金額 / 貨幣供給量(現金+預金) / 残差 / 退蔵残高
- 月次: 上記の月次集計 + 部門別BS + TFM + 純資産=実物資産の検算値 + 客単価・客数の分離(既存E10)

---

## 4. 初期所持金と持込金の根拠

### 4-1. 家計側(総務省統計局 家計調査 2025年平均・PDF実読✔)

| 指標 | 値 | 備考 |
|---|---|---|
| 二人以上世帯 消費支出 | **314,001円/月** | 平均世帯人員2.87人・世帯主平均年齢60.7歳・名目+4.6%・実質+0.9% |
| 単身世帯 消費支出 | **173,042円/月** | 平均年齢58.6歳・名目+2.1%・実質−1.5% |
| 総世帯 消費支出 | **259,880円/月** | 平均世帯人員2.15人 |
| 総世帯のうち勤労者世帯 実収入 | **559,173円/月** | 平均世帯人員2.42人・有業1.52人・世帯主48.3歳 |
| 単身勤労者世帯 実収入 | **386,791円/月** | 平均年齢43.3歳 |
| 二人以上勤労者世帯 平均消費性向 | **65.0%** | 前年比+2.8pt |
| 同 黒字 / 黒字率 | **186,111円 / 35.0%** | |
| 同 金融資産純増 | **194,870円** | うち預貯金純増**177,061円**・有価証券純購入5,059円・保険純増12,751円 |
| 同 土地家屋借金純減 | 30,173円 | |

**v2への換算**(【推測】= 単純割り算):
- 二人以上世帯: 314,001 ÷ 30.4日 ≈ **10,300円/世帯・日** ÷ 2.87人 ≈ **3,600円/人・日**
- 単身世帯: 173,042 ÷ 30.4 ≈ **5,700円/人・日**
- → **住民エージェントの1日あたり消費sink = 3,600〜5,700円** を初期アンカーに。渋谷区は単身率が高いため上側寄り。
- **貯蓄(退蔵)率 = 35.0%** をそのまま「可処分所得のうち退蔵項に回る割合」の初期値に使える。**faucet(給与)とsink(消費)と退蔵の比率が公的数値で閉じる**のがこの表の価値。

**東京補正**: 既存台帳(面3)の「東京の消費支出341,594円/月・全国比約1.09」を較正係数として併用。

### 4-2. 来街者の持込金

| 対象 | 値 | 出典(実読✔) |
|---|---|---|
| 渋谷来訪 訪日外国人 滞在中消費額(令和5年度) | **平均7.1万円**(宿泊者10.4万円・非宿泊者5.6万円) | TCVB 渋谷マーケティング実態調査(2024年4月・n=2,628) |
| 同(令和元年度) | 平均3.3万円 | 同上 |
| 非宿泊者の滞在時間 | 令和5年度**4.9時間**(令和元年度4.5時間) | 同上 |
| 宿泊率 / 平均宿泊日数 | 30% / 8.3泊(令和元年度は15% / 6.8泊) | 同上 |
| 補足 | 「渋谷非宿泊者のうち滞在時間が6〜9時間の観光客では平均7万円台」 | 同上 |

**注意**: 「滞在中の消費額」は**渋谷での消費額か訪日旅行全体の消費額か、概要版の文言だけでは断定できない**。宿泊者10.4万円という水準からは旅行全体寄りに見える。**親の一次確認リスト#4**。

**日本人来街者の1回あたり消費額**: **空欄(未確認)**。東京都「繁華街利用実態調査」(平成13年公表)は商圏・アクセス・通行量が中心で、金額は概要版に無い(実読で確認)。かつ同ページに「本調査以降、同様の調査は行っていません。」と明記されており**後継調査は存在しない**。
→ 代替の取得経路候補: 渋谷区の商業統計/経済センサス販売額 ÷ 推計来街者数(逆算)、または渋谷区観光協会/渋谷未来デザインの調査(未探索)。

### 4-3. 現金保有(財布の中の現金)

**空欄(未確認・一次情報なし)**。検索で出たのはau PAY/東証マネ部などのメディア調査(キャッシュレス派は「5,000円〜1万円未満」32.7%が最多、現金派は「1万円〜3万円未満」が最多)で、**一次出典に到達していない**。日本銀行「決済システムレポート別冊 キャッシュレス決済の現状」「決済動向」が候補だが本ラウンドでは未読。
→ **初期所持金の分布は当面 expedient** とし、家計調査の預貯金純増(177,061円/月)から「口座残高」を、財布現金は仮置き(例: 対数正規, 中央値1万円)で**expedientタグ+感度試験**にかけるのが安全。

---

## 5. 店舗側の初期条件

### 5-1. 取得済み(既存台帳 `v2-economy-sfc-deep-research.md` 面3 より継承・本ラウンドで再取得はせず)

- 渋谷区 飲食店 3,970(2021)・小売店4,876・従業者503,767人
- 渋谷区 小売業年間販売額 1兆5,904億円(全国8位・都内1位)
- 小売卸売販売額 6兆5,926億円 / 1人当たり小売687万円
- 飲食店の5年純減 −7.5%(2016→2021)
- JFA 客単価104.3% × 客数102.9%

### 5-2. 本ラウンドで確定した取得経路(e-Stat・未取得)

売上規模・客単価・営業時間の**渋谷区レベルの数値**は、以下のe-Statデータベースから直接引ける(表IDを確認済み・実データ未取得=**空欄(未確認)**):

| 目的 | e-Stat 表 |
|---|---|
| 産業別 事業所数・売上金額(市区町村) | 令和3年経済センサス‐活動調査 事業所に関する集計 産業横断的集計「売上(収入)金額等」(toukei=00200553, tstat=000001145590) |
| 産業小分類別 事業所数・従業者数(市区町村) | statdisp_id=**0004005689**(産業(小分類)、経営組織(5区分)別全事業所数、男女別従業者数及び常用雇用者数—全国、都道府県、市区町村) |
| 飲食店 細分類別 売上・8時間換算雇用者数 | statdisp_id=**0003094894**(全国・都道府県まで。**市区町村は無い**) |
| サービス関連産業 小分類別 | statdisp_id=0004003270(全国・都道府県まで) |

**構造的制約(重要)**: 経済センサスの**細分類レベルは都道府県止まり**で、市区町村は小分類までしか出ない。したがって「渋谷区のカフェの客単価」のような粒度は**公的統計からは直接取れない**。
→ **設計への含意**: 店舗の売上・客単価は「渋谷区の小分類別売上 ÷ 事業所数 = 1店あたり年商」でトップダウンに配分し、**客単価は東京都/全国の細分類値を移入する**。この移入は **expedient** とタグ付けし、月次センサスの客単価×客数分解(E10 holdout)で事後検証する。

**営業時間の公的統計**: **空欄(未確認)**。経済センサスに営業時間項目は無い。実務上の代替はOSM `opening_hours` タグ / Google Places / 食べログ等。既決の D-R2-1(営業時間)台帳と接続すべき。ライセンス台帳(`data-license-ledger.md`)の確認が必須。

**1店あたり年商の粗い目安**【推測・単純割り算】: 小売業年間販売額1兆5,904億円 ÷ 小売店4,876店 ≈ **3.26億円/店・年** ≈ 89万円/日。これは大型店(渋谷スクランブルスクエア・ヒカリエ等)に強く引っ張られた平均であり、**中央値ははるかに低い**。→ **平均でなく分布(べき則/対数正規)で持つこと**を設計要件に。

---

## 6. 推奨

### 6-a. U10 の設計案

**案A(推奨・主案): 外界1ノード + T0活動スケジュール + 差分時のみLLM**

- 域外は**RoW 1ノード**(経済のRoWと同一実体)。域外の地理は持たない。域外の内訳は「出発地コホート(世田谷・神奈川・埼玉…)」の属性で表現。
- 各persistent_idは**週次活動スケジュール表**を持つ。来街は表の参照。
- 日次はT1(確率的差分)のみ。LLMはT2(逸脱・イベント・破綻)でのみ発火。
- **較正**: 国勢調査(昼夜間人口・従業地通学地の町丁目別)でスケジュール表の生成分布を決める。PT調査の目的別時間帯カーブで時刻分布を決める。大都市交通センサスの乗換人員で通過層を決める。
- **照合(holdout)**: KDDI 5エリア×24h×属性の**形状指標5本**(§1-4)。スクランブル50万人/日。訪日訪問率60.3%・滞在5時間。
- **感度ゲート**: 「代替の境界仮定(案B・案C)でも結論が反証されないこと」(Galán+ 2009)を主張の条件に。境界妥当性テスト(実験がコードン流量を有意に変えたら領域が狭すぎる)を自動化。

**案B(不採用・ablation対照): 重力モデルによる日次抽選(v1型)**

- 不採用理由(3点):
  1. **U10の第一候補「エージェントが来街を決定する」を構造的に満たさない**——抽選は世界側の外生入力。
  2. ODD 2020の分類で「外生」=一方向。エージェントの経験(前日の失望・友人からの誘い)が来街確率に返らない。**適応と創発が消える**。
  3. **holdout汚染**: 重力モデルのパラメータを滞在人口に合わせて較正すると、KDDI曲線が検証に使えなくなる。
- **ただし ablation の下限対照として1本は必ず走らせる**(既存台帳面1の「閉鎖系は主案不可だが対照として必須」と同型)。「案Aが案Bより良い」を示す唯一の方法。

**案C(ハイブリッド・第2候補): 案A + 低解像度外界の段階導入**

- 常連層・通勤通学層は案A(永続ID・スケジュール表)。一度きり層は**入場時に決定論的シード生成**(既存台帳 面3(a) と同じ)。
- 域外を1ノードでなく**数ノード(方面別: 東急沿線/京王/JR埼京/メトロ)**に分け、鉄道の運行(D-R2-1)と接続。
- 導入は段階的(Ajelli+ 2010 の粗い外界→細かい内界の先行)。**Phase 2以降**。

**較正・照合手順(3階層・TAG式)**:
1. **生成に使用**(独立でない): 国勢調査の町丁目別従業地通学地 → スケジュール表の空間分布
2. **較正に使用**: PT調査目的別時間帯カーブ、大都市交通センサス乗換人員、定期券枚数
3. **検証専用(触らない)**: KDDI滞在人口(形状5指標)、スクランブル通行量、訪日訪問率・滞在時間、繁華街利用実態調査の商圏シェア(渋谷9.9%・電車70%超)
4. **事前宣言**: 較正がスケジュール表の生成分布を変えてよい上限(例: 各コホート人数の±5%)を数値で宣言。超えたら「より低い検証水準」として報告(TAG M3.1準拠)。

### 6-b. U11 の最小SFC設計

- **6部門**(世帯・店舗・雇用主・**銀行**・政府・外界RoW)。依頼の5部門に銀行を追加する理由=現金のみ経済は賃金原資を説明できない(既存台帳U-B面1)。
- **科目**: §3-3のBS 6行 + TFM 12科目 + 残差科目 + 退蔵項。
- **faucet/sink表**: §3-3の表を台帳ファイル化。account_codeの列挙型と1対1対応させ、**列挙にない科目は実行不能**にする。
- **検算**: Caianiの2本(行列の行和列和=0 / 純資産合計=実物資産)。**主検算は後者**(全規模ランで安い)。
- **日次/月次センサス**: EVE MER型の固定表形式。faucet科目別・sink科目別・貨幣供給量・残差・退蔵残高。
- **テスト形**: §3-3のpytest 8本。
- **新規則R4**: 参入時の初期資本はtransfer由来のみ(ex-nihilo禁止)。Caianiの名指しした不整合への対応。

### 6-c. expedient として明示すべき箇所(根拠なし・感度試験必須)

| # | 箇所 | 理由 |
|---|---|---|
| E-a | T1の確率式(天候・曜日→来街確率の弾力性) | 出典なし |
| E-b | 財布現金の初期分布 | 一次出典未取得(§4-3) |
| E-c | 店舗の客単価(細分類値の都道府県→区への移入) | 経済センサスは市区町村×細分類を出さない(§5-2) |
| E-d | 1店あたり年商の分布形(べき則/対数正規の選択) | 平均のみ公表・分布は非公表 |
| E-e | 営業時間 | 公的統計なし・外部データ依存 |
| E-f | 来街目的の構成比 | PT数表が未取得(§1-5) — **取得できれば mechanism に昇格可能** |
| E-g | 日本人来街者の1回あたり持込金 | 一次出典なし(後継調査が存在しない) |
| E-h | コードン照合の許容誤差(±X%) | TF Resourceは「基準ガイドラインは存在しない」と明記(§1-1) → **v2の自前宣言事項** |

---

## 7. 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 引用文 | 確認すべき数値・論点 |
|---|---|---|---|---|
| 1 | 外部交通モデルの検査に基準ガイドラインは存在しない(既存台帳の「±10%が典型的合格条件」と衝突) | https://tfresource.org/topics/Model_Validation_and_Reasonableness_Checking_Amount_Of_Travel.html | "There are no applicable criteria guidelines for checks of external travel models." | ①この文が本当にexternal travelの節にあるか ②既存台帳のTN guidelines(±10%)の一次出典を再確認し、どちらを採るか決める |
| 2 | SFC-ABMの検算は2本立て・主検算は「純資産合計=実物資産」 | https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ABMSFCMacroModelBenchmark.CainiEtAl2016.pdf (JEDC 69:375-408, doi経由でも可) | "the sum of the net worth of all the agents in the economy (including government and central bank) is exactly equal to the values of real assets in every simulation round" | ①Table 3の主体数(家計8,000/C企業100/K企業20/銀行10/公務員1,360) ②ex-nihilo参入の警告文の所在(第2節) ③この検算がv2の月次センサスに移植可能か |
| 3 | 家計調査2025年平均の消費・貯蓄比率 | https://www.stat.go.jp/data/kakei/sokuhou/tsuki/pdf/fies_gaikyo2025.pdf | 「消費支出は、１世帯当たり１か月平均314,001円」「平均消費性向は、65.0％」「黒字は186,111円、黒字率は35.0％」「預貯金純増は177,061円」 | ①314,001/173,042/259,880の3値 ②消費性向65.0%と黒字率35.0%が同一表か ③1日あたりへの割り戻し(30.4日)の妥当性 |
| 4 | 渋谷来訪 訪日外国人の消費額7.1万円 | https://www.tcvb.or.jp/jp/project/chiiki_r5markeshibuya_form.pdf | 「① 滞在中の消費額 … 平均7.1万円（宿泊者10.4万円。非宿泊者5.6万円）」「③ 非宿泊者滞在時間 … 平均4.9時間」 | **①「滞在中」が渋谷での消費か訪日旅行全体かの定義**(持込金アンカーとして使えるかの分岐) ②n=2,628・調査地点8・調査期間19日の代表性 ③令和元年3.3万円→令和5年7.1万円の2.15倍が円安の影響か実質増か |
| 5 | LLMモビリティシムの実験規模は70体 / 再計画起点は4種に限定 | https://arxiv.org/abs/2506.23306 (HTML: https://arxiv.org/html/2506.23306v2) | "A synthetic population of 70 individuals is generated using GPT-4o" / "Plan revision opportunities occur at strategically selected moments including: 1) simulation day initiation; 2) waiting periods …" | ①70体が主実験の規模か(スケール実験が別にないか) ②LLM呼数/トークン数の記載の有無 ③この4起点をv2のT2発火条件にそのまま使えるか |

---

## 参照一覧

| # | 出典 | 著者・発行 | 年 | URL | 確認 |
|---|---|---|---|---|---|
| R1 | Agent based-stock flow consistent macroeconomics: Towards a benchmark model, JEDC 69:375-408 | Caiani, Godin, Caverzasi, Gallegati, Kinsella, Stiglitz | 2016 | https://faculty.sites.iastate.edu/tesfatsi/archive/tesfatsi/ABMSFCMacroModelBenchmark.CainiEtAl2016.pdf | ✔ 全34頁PDF実読(抄録・Table 3・検算2法・ex-nihilo警告) |
| R1b | 同 出版社ページ | Elsevier | 2016 | https://www.sciencedirect.com/science/article/abs/pii/S0165188915301020 | 未読(書誌のみ) |
| R2 | GATSim: Urban Mobility Simulation with Generative Agents | Liu, Li, Ma | 2025 | https://arxiv.org/abs/2506.23306 / https://arxiv.org/html/2506.23306v2 | ✔ HTML実読(70体・再計画4起点・計画のタプル表現) |
| R3 | Model Validation and Reasonableness Checking / Amount Of Travel | TF Resource (TRB系) | — | https://tfresource.org/topics/Model_Validation_and_Reasonableness_Checking_Amount_Of_Travel.html | ✔ 実読(I-X/X-I/X-X・基準ガイドライン不在) |
| R4 | 家計調査報告(家計収支編) 2025年(令和7年)平均結果の概要 | 総務省統計局 | 2026 | https://www.stat.go.jp/data/kakei/sokuhou/tsuki/pdf/fies_gaikyo2025.pdf | ✔ 24頁PDF実読(314,001 / 173,042 / 259,880 / 65.0% / 35.0% / 177,061) |
| R5 | 令和5年度 渋谷マーケティング実態調査及び事業計画策定支援業務委託 報告書概要版 | 東京観光財団(TCVB)・渋谷区観光協会 | 2024 | https://www.tcvb.or.jp/jp/project/chiiki_r5markeshibuya_form.pdf | ✔ 実読(7.1万円 / 4.9時間 / 宿泊率30% / 訪問理由5項目 / n=2,628) |
| R6 | 東京都における繁華街利用実態調査(平成13年3月) | 東京都(旧 労働経済局商工指導所) | 2001 | https://www.sangyo-rodo.metro.tokyo.lg.jp/toukei/pdf/monthly/chusho/hankagai.pdf | ✔ 実読(渋谷9.9%/7.5% / 電車53.8%・70%超 / センター街113,568人 / n=17,703) |
| R7 | 第13回 大都市交通センサス調査の公表について | 国土交通省 総合政策局 | 2023 | https://www.mlit.go.jp/sogoseisaku/transport/content/001717223.pdf | ✔ 12頁PDF実読(定期券890万→638万枚72% / 都区部在圏529万人)。**目的別構成比は非掲載** |
| R8 | 相模原市の人の動き 〜第6回(H30)東京都市圏パーソントリップ調査から〜 | 相模原市 | 2022 | https://www.city.sagamihara.kanagawa.jp/_res/projects/default_project/_page_/001/004/830/h30_pt.pdf | ✔ 19頁PDF実読。**目的構成・外出率・原単位はすべて図のみ=数値未取得** |
| R9 | 東京都市圏パーソントリップ調査(調査概要) | 東京都市圏交通計画協議会 | 2018/2023 | https://www.tokyo-pt.jp/person/01 | ✔ 実読(平成30年9〜11月・約63万世帯・268市区町村)。**構成比の数値なし** |
| R10 | 東京都市圏パーソントリップ調査 目的種類別代表交通手段別OD表 | e-Stat | 2018 | https://www.e-stat.go.jp/stat-search/files?layout=dataset&toukei=00600550&tstat=000001151670&stat_infid=000032066127 | **空欄(未取得)** — 次ラウンド必須 |
| R11 | Roblox Annual Economic Impact Report | Roblox Corporation | 2025-09 | https://about.roblox.com/newsroom/2025/09/roblox-annual-economic-impact-report | ✔ 実読($1B超・median $1,575・24,500超)。**faucet/sink内訳は非掲載** |
| R12 | EVE Online Monthly Economic Report(CCP公式) | CCP Games | — | 公式URL未特定 | **空欄(未確認)** — 二次(ブログ)経由の記述のみ。親の再取得推奨 |
| R13 | AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents | Piao et al. (Tsinghua) | 2025 | https://arxiv.org/abs/2502.08691 | **空欄(未読)** — 検索要約で「10k超・500万インタラクション」を得たのみ |
| R14 | 令和3年経済センサス‐活動調査 産業(小分類)別 事業所数・従業者数(市区町村) | 総務省・経済産業省 | 2021 | https://www.e-stat.go.jp/stat-search/database?statdisp_id=0004005689 | **空欄(未取得)** — 表IDのみ確認 |
| R15 | 令和3年経済センサス‐活動調査 飲食店等(細分類)別 売上金額(全国・都道府県) | 総務省・経済産業省 | 2021 | https://www.e-stat.go.jp/stat-search/database?statdisp_id=0003094894 | **空欄(未取得)** — 市区町村粒度は存在しないことを確認 |
| R16 | 令和3年度 全国都市交通特性調査 | 国土交通省 都市局 | 2023 | https://www.mlit.go.jp/toshi/city_plan/2021npt.html | ✔ ページ実読。**結果数値は別資料・未取得** |
| R17 | ActivitySim 技術説明(auxiliary demand / external) | CMAP | 2024頃 | https://cmap.illinois.gov/wp-content/uploads/dlm_uploads/CMAP_ActivitySim_ABM_Technical_Description.pdf | **空欄(未読)** — 検索要約のみ |
| R18 | 日本銀行 決済システムレポート別冊「キャッシュレス決済の現状」 | 日本銀行 | 2018 | https://www.boj.or.jp/research/brp/psr/psrb180928.htm | **空欄(未読)** — 財布現金の一次出典候補 |

### 本ラウンドの「空欄(未確認)」一覧(記憶で埋めていない項目)

1. 東京圏の来街目的の構成比(通勤/通学/業務/私事)の**数値** — R10で取得可能
2. MATSim/ActivitySim の外部ゾーン設計の**一次記述** — R17で取得可能
3. UrbanLLM / CityBench の規模と設計
4. AgentSociety の規模の原文確認 — R13
5. EVE MER の CCP公式ページと faucet/sink 科目一覧 — R12
6. UO(Ultima Online)の退蔵/インフレ事例の一次情報
7. 日本人来街者の1回あたり消費額(後継調査が存在しないことを確認済み)
8. 日本の財布内現金保有の一次統計 — R18が候補
9. 渋谷の店舗の営業時間の公的統計(存在しないと判断・要確認)
10. 渋谷区の飲食店・小売の**細分類別**売上(市区町村×細分類は公表されないことを確認)
