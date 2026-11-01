# R-87 答申: 想起の形・関係の減衰と保管・同席の相互作用の強さ

<!-- hdr:v1 -->
- **分野**: 認知科学(記憶) #12 / 社会ネットワーク科学 #14 / 社会心理学(対人魅力) #13 / 自然言語処理・機械学習 #27(埋め込み) | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §5-4 C6・§5-1 C1・§11 第 3 群「想起」「関係の減衰と保管」「同席の相互作用の強さ」・§12 の 7)
- **一次確認**: **A−**(サブ実読: 原典本文 13・本文を読み取り器経由 4・抄録/二次 7・未読 2・空欄は §6)・親検収 済(第319・2026-10-03: ACT-R の :bll 推奨値 .5・GA の 0.995/時と α=1・Roberts & Dunbar の −0.62/+0.27 は既知の値と一致。4.6 GB/年の検算と 7.25→6.9 時間を再計算。Anderson & Schooler 1991 に d=0.5 が無いという指摘は R-68 に伝播。Festinger 1950 は台帳 B1 の holdout として未開封(正しい))
- **索引**: [INDEX.md](INDEX.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は OS の一時ディレクトリで pymupdf 抽出・リポに置かない)・モデルの重みは取得していない(huggingface.co は公開 API とモデルカードの文面を読んだだけ)・コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: 記憶の作り直しの錨 = [R-68](v2-r68-memory-rework-anchors.md)(Lally・Wagenaar・忘却の種類)/箱の中の社会 = [R-69](v2-r69-indoor-society-anchors.md)/部署の大きさと Allen の曲線 = [R-80](v2-r80-department-size-anchors.md)/単純接触 = [R-51](v2-r51-mere-exposure-incidental-ads-research.md)/GA の 0.995 と反省 150 = [r23 batch1](v2-r23-primary-check-batch1.md) #14・#15/関係の文献メモ = `lit/relations__*`。本書はこれらを引くだけにし、足りない錨(ACT-R の原典の値・埋め込みの比較・関係の減衰・保管の条件・同席の量)を足す。設計の決定はしない(§4 は親への案)。

## 結論(5 行)

1. **想起の式は ACT-R の原典で確かめた**。活性 A = B + Σ W·S、基底の活性 B = ln Σ t^−d。マニュアルは d=0.5 を「数少ない強い推奨値」と書く。ただし **Anderson & Schooler 1991 の本文に d=0.5 は無い**。環境の必要確率の指数は .73・.77・.83 で、記憶モデルを当てはめた d₁ は .125・1.0・1.5 だった。v2 の辺の式は ACT-R の近似式(:ol)と同じで、L は「最初に会ってから」の時間をとる。このため式の中に「最後に会ってからの時間」が入っていない。GA の想起は、最後に**想起**されてからのゲーム内の時間に 0.995 の減衰をかけた recency と、重要度(1〜10)・関連度(コサイン)を min-max で正規化して α=1 で足す形である(原典で確認)。
2. **日本語の埋め込み**(JMTEB の表・2025-10 の版): Sarashina-v2-1b 76.38(非商用の許諾)・Ruri-v3-310m 75.85・Ruri-v3-130m 75.52・PLaMo-1b 74.85・Ruri-v3-30m 72.95(37M・256 次元・Apache-2.0)・mE5-large 70.67。モデルカードの平均(30m で 74.51)は表の値と一致しない(評価の版の違いと読める・推測)。CPU の処理量の実測は見つからず空欄。
3. **関係の減衰の暦の上の速さを示す数値は原典に無い**。Roberts & Dunbar(2015 の再解析)は 25 人を 18 か月追い、友人の親しさは下がり(b=−0.62)、家族は上がる(+0.27)と報告した。下がり方は前半の 9 か月が大きい。Dunbar 2020 は「数か月のうちに」「3 か月を超えると弱まる」と書く。Levin ほか 2011 は 3 年以上連絡の無い関係を眠っている関係と定義し、再接続しても価値があると報告した。今の「1 回話した相手が閾値を下回るまで」は τ=−2.346 で 7.25 時間、今の既定 τ=−2.322 では 6.9 時間になる(式からの計算)。
4. **保管の容量 4.6 GB/年は検算が合う**: 2 人/日 × 365 × 390,067 体 × 16 B = 4.56×10⁹ B(4.24 GiB)。前提は 1 件 16 B(今の辺の行と同じ大きさ)。1 日に何人の新しい知り合いができるかの錨は見つからず空欄。保管に入る条件の錨: Hall は「顔見知りから気軽な友人まで 40〜60 時間」(大学の発表)、Reis ほか 2011 は 1 回目から 2 回目の会話で「相手を知っている感覚」の伸びが最も大きいと報告した。
5. **同席の強さの錨**: 机を隣にした無作為の割り当て(5 か月・2,996 人)で、相互の友人になる確率は 15.3% から 22.3% に上がった(+7.0 ポイント)。会話をしない 15 回の同席でも好意は上がった(Moreland & Beach・抄録)。Hall は「一緒に働いた時間はあまり数えない」と書く。1 回の同席が辺の強さをどれだけ動かすかを直接示す値は無い。仮の値を宣言して感度試験に回すことになる(§4-4)。Festinger 1950 は台帳 B1(holdout)なので較正に使わない。

---

## §0 出典の表

等級: **◎** 原典本文で数値まで逐語確認 / **○** 本文を読み取り器(WebFetch)経由で確認、または公式の発表文 / **△** 抄録・二次・検索要約のみ / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | ACT-R 7.x Reference Manual(Bothell) | http://act-r.psy.cmu.edu/actr7.x/reference-manual.pdf | ◎ | 宣言的記憶の活性の式・:bll・:ol・:mas・Sji の節(pymupdf 抽出) |
| 2 | Anderson J.R. & Schooler L.J. 1991「Reflections of the environment in memory」Psychological Science 2(6):396-408 | https://doi.org/10.1111/j.1467-9280.1991.tb00174.x (本文: https://users.cs.northwestern.edu/~paritosh/papers/KIP/AndersonSchooler1991ReflectionsOfEnvironmentOnMemory.pdf) | ◎ | 全文(走査 PDF の文字層) |
| 3 | Whitehill J. 2013「Understanding ACT-R - an Outsider's Perspective」 | https://arxiv.org/abs/1306.0125 | ○ | 本文 §4.3〜4.4(二次の解説) |
| 4 | Park J.S. ほか 2023「Generative Agents」UIST '23 | https://arxiv.org/abs/2304.03442 | ◎ | 本文 §4.1 想起・§4.2 反省・§4.3 反応の文脈 |
| 5 | Yu Y. ほか 2024「Affordable Generative Agents」TMLR | https://arxiv.org/abs/2402.02053 | ◎ | 本文の Social Impression Memory・付録 B.2 |
| 6 | Piao J. ほか 2025「AgentSociety」 | https://arxiv.org/abs/2502.08691 | ◎ | 本文の社会の節(関係の強さ 0〜100) |
| 7 | JMTEB の leaderboard.md(GitHub・commit 9b1e683・2025-10-02) | https://github.com/sbintuitions/JMTEB/blob/9b1e683bc6a2cd2b6b3e170bd94c29041038c4bb/leaderboard.md | ◎ | 要約表・検索・STS・分類の表 |
| 8 | Hugging Face の公開 API とモデルカード(Ruri-v3・Sarashina・PLaMo・GLuCoSE・mE5・bge-m3・EmbeddingGemma) | https://huggingface.co/cl-nagoya/ruri-v3-30m ほか | ◎ | 許諾の札・パラメータ数・次元・最大長(文面を読んだだけ・重みは取得していない) |
| 9 | Jiang H. ほか 2026「SYNAPSE」 | https://arxiv.org/abs/2601.02744 | △ | 抄録(読み取り器) |
| 10 | Hou Y., Tamoto H., Miyashita H. 2024(CHI LBW) | https://arxiv.org/abs/2404.00573 | △ | 抄録(読み取り器) |
| 11 | Roberts S.G.B. & Dunbar R.I.M. 2011「The costs of family and friends: an 18-month longitudinal study of relationship maintenance and decay」Evol. Hum. Behav. 32(3):186-197 | https://doi.org/10.1016/j.evolhumbehav.2010.08.005 | △ | 抄録の要旨(検索要約・出版社 403) |
| 12 | Roberts & Dunbar 2015「Managing relationship decay」Human Nature 26(4):426-450(#11 と同じデータの再解析) | https://pmc.ncbi.nlm.nih.gov/articles/PMC4626528/ | ○ | 本文(読み取り器・既存 lit メモと数値が一致) |
| 13 | Roberts & Dunbar 2011「Communication in social networks」Personal Relationships 18(3):439-452 | https://doi.org/10.1111/j.1475-6811.2010.01310.x | △ | 抄録の要旨(検索要約) |
| 14 | Dunbar R.I.M. 2020「Structure and function in human and primate social networks」Proc. R. Soc. A 476:20200446 | https://doi.org/10.1098/rspa.2020.0446 (Europe PMC PMC7482201) | ◎ | 全文 XML(Europe PMC REST)から文字列照合 |
| 15 | Burt R.S. 2000「Decay functions」Social Networks 22:1-28 | https://doi.org/10.1016/S0378-8733(99)00015-5 | △ | 抄録の要旨(検索要約)・#17 の紹介 |
| 16 | Burt R.S. 2001「Attachment, decay, and social network」J. Organizational Behavior 22(6):619-643 | https://www.ronaldsburt.com/research/files/ADSN.pdf | ◎ | 抄録・decay の節 |
| 17 | Raeder T. ほか 2011「Predictors of short-term decay of cell phone contacts」Social Networks | https://arxiv.org/abs/1102.1753 | ◎ | 本文 §2(Burt の紹介)・方法 |
| 18 | Levin D.Z., Walter J., Murnighan J.K. 2011「Dormant ties: The value of reconnecting」Organization Science 22(4):923-939 | https://doi.org/10.1287/orsc.1100.0576 (本文: https://business.gwu.edu/sites/g/files/zaxdzs5326/files/15_FP.SP_Walter.J_15levin_2011a.pdf) | ◎ | 全文 |
| 19 | Hall J.A. 2019「How many hours does it take to make a friend?」JSPR 36(4):1278-1296 | https://doi.org/10.1177/0265407518761225 ・ https://news.ku.edu/news/article/2018/03/06/study-reveals-number-hours-it-takes-make-friend | ○ | 抄録(OpenAlex)・大学の発表文(読み取り器)。本文は 403 |
| 20 | Reis H.T. ほか 2011「Familiarity does indeed promote attraction in live interaction」JPSP 101(3):557-570 | https://doi.org/10.1037/a0022885 (本文: https://www.sas.rochester.edu/psy/people/faculty/reis_harry/assets/pdf/ReisManiaciCaprarielloEastwickFinkel_2011.pdf) | ◎ | 全文(研究 1・研究 2) |
| 21 | Rohrer J.M., Keller T., Elwert F. 2021「Proximity can induce diverse friendships」PLOS ONE 16(8):e0255097 | https://doi.org/10.1371/journal.pone.0255097 | ○ | 本文(読み取り器) |
| 22 | Back M.D., Schmukle S.C., Egloff B. 2008「Becoming friends by chance」Psychological Science 19:439-440 | https://doi.org/10.1111/j.1467-9280.2008.02106.x | △ | 検索要約(本文は有料・著者の配布は申込み制) |
| 23 | Moreland R.L. & Beach S.R. 1992「Exposure effects in the classroom」JESP 28:255-276 | https://doi.org/10.1016/0022-1031(92)90055-O | △ | 抄録の要旨(検索要約) |
| 24 | Paulos E. & Goodman E. 2004「The familiar stranger」CHI '04(Milgram 1972 の再現) | https://doi.org/10.1145/985692.985721 (本文: http://www.paulos.net/papers/2004/Familiar%20Stranger%20(CHI%202004).pdf) | ◎ | 本文の調査の節(Milgram の数値はこの論文の引用=二次) |
| 25 | Festinger L., Schachter S., Back K. 1950 | - | × | 読んでいない(台帳 B1 = holdout。較正に使わないため意図して開かない) |
| 26 | Allen T.J. 1977(距離と交流の曲線) | - | × | 未読(R-80 #19 の空欄のまま) |

本数: ◎ 13・○ 4・△ 7・× 2(既存 lit メモの Saramäki 2014 は引くだけで数えない)。

### §0-1 既存答申との重複と循環参照の検査

| 値 | 既存の置き場所 | 本書での扱い |
|---|---|---|
| d=0.5 の根拠 | R-68 §0 が「原典の本文一次はリポに無い・Anderson & Schooler 1991 は未読」と記録 | **本書で両方を読んだ**。d=0.5 の出どころは ACT-R マニュアルの推奨値(#1 ◎)。Anderson & Schooler 1991 は d=0.5 を書いていない(#2 ◎)。→ 「d=0.5(Anderson & Schooler 1991)」と書いた箇所は「d=0.5(ACT-R マニュアルの推奨値・環境の分析は Anderson & Schooler 1991)」に直すのが正確(訂正の伝播の候補・§7) |
| GA 0.995・α=1・反省 150 | r23 batch1 #14・#15(一致) | 再確認して一致。補足: recency は「最後に**想起された**時から」の時間(最後の出来事からではない) |
| Ruri-small 71.53 vs mE5-large 71.65 | [memory-retrieval](v2-memory-retrieval-research.md) 第203 訂正 | 2025-10 の表では Ruri-small 69.34・mE5-large 70.67(評価の版の更新で値が動いた)。**どの版の表かを必ず併記する**(§1-6) |
| Dunbar の層の呼び名 | `lit/relations__dunbar2020_structure-function.md` は「150 acquaintances / 500 known names」 | Dunbar 2020 の本文(#14 ◎)は「the 500 (acquaintances) layer」と書く。1500 の層の呼び名は本文に無い。図 2 の画像の文字は読めていない。**食い違い**(§7) |
| Roberts & Dunbar の係数 | `lit/relations__robertsdunbar2015_relationship-decay.md`(読み取り器経由) | 別の読み取りでも同じ値が返った(b=−0.71・−0.62・+0.27・28.41/69.31/128.78 日)。ただしどちらも読み取り器なので ○ のまま |
| Festinger 1950 | 台帳 B1(holdout) | 較正の錨にしない。本書は開いていない |

---

## §1 A. 想起

### 1-1 ACT-R の活性(#1 ◎)

- 活性 A_i = B_i + S_i + P_i + ε。S_i が活性の広がり、P_i が部分一致、ε が雑音。
- 基底の活性(:ol nil): **B_i = ln(Σ_{j=1..n} t_j^−d) + β_i**。t_j は j 回目の提示からの時間、d は :bll の値。
- 近似(:ol t): **B_i = ln(n/(1−d)) − d·ln(L) + β_i**。L は「chunk の寿命(作られてからの時間)」。逐語: "L: The lifetime of chunk i (the time since its creation)"。
- 折衷(:ol を数にする): 直近の k 回だけ本当の時刻を持ち、それより古い分を近似で足す。
- **:bll の推奨値**(逐語): "The recommended value for :bll is .5, and it is one of the few parameters which have a strong recommended value."
- 活性の広がり: **S_i = Σ_k Σ_j W_kj · S_ji**。W_kj はバッファ k の源 j からの量で、既定ではバッファの源の活性を源の数で割った値。**S_ji = S − ln(fan_ji)**(j が i の欄にあるとき・それ以外は 0)。S は :mas。:mas の既定は nil(活性の広がりは切ってある)。S_ji が負になると既定では警告を出して 0 にする。
- 「S はおよそ 2」という言い方は検索要約(チュートリアル経由)だけで、原典の数値は確認していない(空欄 #14)。マニュアルの例には `(sgp :esc t :bll .5 :mas 2 :mp 1)` の行がある(例であって推奨値ではない)。

### 1-2 Anderson & Schooler 1991(#2 ◎)= d=0.5 の原典ではない

- 主張: 記憶の想起しやすさ(頻度・最近さ・間隔)の関係は、環境で「その項目が必要になる確率」の関係と同じ形をしている。
- 環境の保持曲線(必要の見込み対 経過時間)の冪の指数: ニューヨーク・タイムズ **.73**・子どもへの発話 **.77**・電子メール **.83**。どれも指数関数には合わない。
- 記憶のモデル(本文の式 9〜11): 提示ごとの強さが足し合わさる・各提示は冪で減る・各提示の減衰の指数は前の提示からの間隔で決まる(d_i = max[d₁, b(t_i − t_{i−1})^−d₁])。当てはめで **b = .61** を固定し、d₁ は **.125**(Glenberg の間隔効果)・**1.000**・**1.5**(保持と練習の加法性)を使った。
- **d=0.5 という数は本文に出てこない**。0.5 は ACT-R の後の版で推奨値として置かれたもの(#1)。#3 も「d の定義は文献ごとに違う」と整理している。

### 1-3 v2 の今の辺の式との対応(src を読んだだけ・変えていない)

- `engine/relations.py` の A = ln(n/(1−d)) − d·ln(L+1)・d=0.5・L は (tick − rel_first) の分。**これは ACT-R の :ol t の近似と同じ形**(+1 は t=0 で発散しないための足し算)。
- 近似式の L は「最初に会ってから」なので、**「最後に会ってからの時間」は式に入っていない**。n 回の出会いが一様に散っているときの近似で、最後の出会いの時刻は効かない。ユーザー案の「会った回数と最後に会ってからの時間」に合わせるなら、折衷の形(直近 k 回の時刻を持つ)が要る。体あたりの辺 50 × k 回 × 4 B が増える(推測: k=3 で 600 B/体・39 万体で約 234 MB)。
- 1 回だけ話した相手(n=1)が τ を下回るまでの時間(式からの計算・推測ではなく算術): L+1 = exp((ln 2 − τ)/0.5)。τ=−2.346(REL_TAU_V1)で 435 分 = **7.25 時間**、τ=−2.322(今の既定 REL_TAU_V2)で 415 分 = **6.9 時間**。指示書の「約 7.3 時間」は V1 の τ の値。
- 同じ式で n を変えると(L の単位は分・算術): n=2 で約 1.15 日、n=5 で約 7.2 日、n=65(週 5 日 × 13 週)で約 1,220 日。

### 1-4 Generative Agents の想起(#4 ◎)

- recency(逐語): "we treat recency as an exponential decay function over the number of sandbox game hours since the memory was last retrieved. Our decay factor is 0.995."
- importance: LLM に 1〜10 の整数で答えさせる(「部屋の片付け」が 2・「好きな人をデートに誘う」が 8)。記憶を作った時に一度だけ付ける。
- relevance(逐語): "we calculate relevance as the cosine similarity between the memory's embedding vector and the query memory's embedding vector."
- 合成: 3 つを **min-max で [0,1] に正規化**して重み付きで足す。"In our implementation, all αs are set to 1."
- 反省: 直近の出来事の重要度の和が **150** を超えたら作る。"our agents reflected roughly two or three times a day"。
- 相手への印象に当たるもの: 反応を決める前に「What is [observer]'s relationship with the [observed entity]?」と「[Observed entity] is [action status]」の 2 つの問いで記憶を引き、要約を合わせる。印象を保存した欄は持たず、毎回引き直して要約する。

### 1-5 印象の記憶の更新の先行例

- **AGA(#5 ◎)**: 体ごとに相手ごとの「Social Impression Memory」(Relationship・Feeling・Summary Events)を持つ。初対面は Unknown/Unknown/None。**会話の後に LLM が更新する**(逐語: "After the agent's dialogues, AGA updates the relationship and feeling between the participants. This update is based on the agent's personal information, the original relationship between the participants, the agent's impression of the other participant, and the content of the conversation itself.")。
- **AgentSociety(#6 ◎)**: 関係の種類は家族・友人・同僚の 3 つ。"Each relationship has a strength value ranging from 0 to 100 representing social closeness"。強さの高い相手ほど頻繁に連絡し、相手とのやりとりの履歴(内容と時刻)を持つ。**強さを更新する規則は読んだ範囲に無い**(空欄 #8)。
- **GA(#4)**: 印象の欄を持たない。反省(上の 150)が相手についての高い水準の記憶を作り、想起のたびに要約し直す。
- ACT-R の基底の活性と埋め込みの関連度を合わせた LLM エージェントの先行: SYNAPSE(#9 △・時間の減衰と活性の広がりを埋め込みと融合・抄録のみ)、Hou ほか 2024(#10 △・文脈の関連・経過時間・想起の回数から固定の度合いを計算・抄録のみ)。式の細部は未読。

### 1-6 日本語の埋め込みモデル(#7 ◎・#8 ◎)

JMTEB の表(2025-10-02 の commit 9b1e683。2025-12 に表は MTEB の公式の表へ移った)。数値は 100 倍の値。

| モデル | 平均 | 検索 | STS | パラメータ数(HF API) | 次元 | 許諾 |
|---|---|---|---|---|---|---|
| sbintuitions/sarashina-embedding-v2-1b | 76.38 | 76.48 | 84.22 | 1,224M | - | 非商用(sarahina-non-commercial-license の札) |
| cl-nagoya/ruri-v3-310m | 75.85 | 76.03 | 81.59 | 315M | 768 | Apache-2.0 |
| cl-nagoya/ruri-v3-130m | 75.52 | 76.45 | 81.05 | 132M | 512 | Apache-2.0 |
| sbintuitions/sarashina-embedding-v1-1b | 74.87 | 74.53 | 81.71 | 1,224M | - | 非商用 |
| pfnet/plamo-embedding-1b | 74.85 | 73.25 | 83.15 | 1,051M | - | Apache-2.0 |
| cl-nagoya/ruri-v3-70m | 73.95 | 74.23 | 80.96 | 70M | 384 | Apache-2.0 |
| cl-nagoya/ruri-v3-30m | 72.95 | 72.84 | 81.78 | 37M | 256 | Apache-2.0 |
| BAAI/bge-m3 | 72.46 | 72.15 | 79.74 | - | - | MIT |
| pkshatech/GLuCoSE-base-ja-v2 | 71.11 | 68.45 | 82.95 | 133M | - | Apache-2.0 |
| intfloat/multilingual-e5-large | 70.67 | 67.65 | 80.86 | 560M | - | MIT |
| google/embeddinggemma-300m | 70.59 | 65.91 | 82.74 | 303M | - | gemma の許諾 |
| intfloat/multilingual-e5-small | 67.38 | 63.91 | 80.46 | 118M | - | MIT |

- Ruri-v3 のモデルカード(#8): ModernBERT・最大 8,192 トークン・30m は埋め込みの層を除くと 10M・10 層。入力に「検索クエリ: 」「検索文書: 」「トピック: 」などの接頭辞を付ける 1+3 の方式。**カードの平均は 30m で 74.51・310m で 77.24**で、上の表の値と違う。評価の版(データの組)が違うためと読める(推測)。比べるときは同じ表の中だけで比べる(フロアの併記: 同じ表の上位 5 本の平均の差は 1.5 ポイント以内)。
- Hugging Face の作者ごとの一覧(2026-10-03 に API で確認): cl-nagoya の埋め込みで最も新しいのは 2025-04 の Ruri-v3、sbintuitions は 2025-08 の Sarashina-v2、pfnet は 2025-08 の PLaMo-1b。これより新しい版は見当たらなかった。MTEB の公式の表(huggingface.co/spaces)は動的な画面で、文面を読めていない(空欄 #10)。
- 取得: huggingface.co は §7 の取得の例外に無い(記憶アジェンダの食い違い #9 と同じ)。重みの取得はユーザー判断。

### 1-7 CPU で回す費用の桁(全部推測)

- 1 回の埋め込み: Ruri-v3-30m の埋め込み層を除く 10M パラメータ × 2 FLOP × 40 トークン(40 字の要旨を想定)で約 0.8 GFLOP。CPU の実効 100〜500 GFLOP/s と置くと、1 コアの塊で毎秒 100〜600 件の桁(推測・実測なし)。
- 書く側: 印象の更新を「LLM の会話の後だけ」にすると、件数は会話の回数で決まる。39 万体 × 1 日 5 回と置くと 1 日 195 万件、上の速さで 1〜5 時間の CPU 時間(推測)。
- 引く側: 問い(今の思考や会話)の埋め込みは決定の呼び出し 1 回に 1 件。候補との類似度は 50 辺 × 256 次元の内積で、埋め込みの計算に比べて小さい。
- 置き場所: 50 辺 × 256 次元 × 39 万体で、float16 なら約 10 GB、int8 なら約 5 GB(算術)。保管の関係にまで印象を持たせると年に数十 GB の桁になる(推測)。**印象の埋め込みは表の 50 辺だけに持たせ、保管には持たせない**形が置き場所の面では素直。

---

## §2 B. 関係の減衰と保管

### 2-1 Roberts & Dunbar(#11 △・#12 ○・#13 △)

- 2011 EHB(#11・抄録の要旨): 25 人の学生を高校から大学への移行の 18 か月追った。友人の情緒的な親しさは家族より、接触の頻度の低下と一緒にする活動の減少に敏感だった。結論は「友人の維持の費用は家族よりずっと高い」。本文の係数は読めていない(空欄 #1)。
- 2015 Human Nature(#12・同じデータの再解析・読み取り器): 30 人を集め 25 人が完了・網の相手 1,291 人・時点は 1 か月(T1)・9 か月(T2)・18 か月(T3)。
  - 友人の親しさの変化 b=**−0.62**(t₇₈₆.₅₇=−15.23)・家族 b=**+0.27**(t₅₄₂.₁₀=7.28)。尺度は 1〜10。
  - 友人の T1→T2 が **−0.82**、T2→T3 が **−0.31**(前半が大きい)。
  - 接触の頻度の変化(最後の接触からの日数・Z 化)→親しさの変化 b=**−0.71**(SE 0.17)。性別との交互作用 0.51(女性で強い)。
  - 友人の最後の接触からの日数の平均: **28.41(中央値 1)→ 69.31(中央値 22.5)→ 128.78(中央値 27)**。
  - 内側の層に残った割合: 家族 70.3%・友人 48.6%。
  - **「1 か月あたり何点下がる」という暦の上の速さは本文に無い**(読み取り器の答え: 時点ごとの係数だけ)。空欄 #2。
- 2011 Personal Relationships(#13・抄録の要旨): 女性 251 人。親族の網が大きい人ほど最後の接触までの時間が長い。親しさが高いほど最後の接触までの時間が短く、その効果は親族で大きい。

### 2-2 Dunbar 2020(#14 ◎)

- 層の大きさ: 5・15・50・150・500・1500・5000。"each layer is approximately three times the size of the layer immediately inside it"。
- 500 の層の呼び名(逐語): "slip over the threshold into the 500 (acquaintances) layer"。5000 は顔の認識の実験から("the number of faces that can be recognized as known by sight")。1500 の呼び名は本文に無い(図 2 の画像は未読)。
- 減衰の時間(逐語): "Figure 6 suggests that this effect happens within a matter of a few months"。"if lockdown continues for more than about three months, we may expect to see a weakening of existing friendships"。家族は接触が無くても強い。
- "Each layer seems to correspond to a very specific frequency of interaction"(層ごとの頻度の値は図 3 の画像にあり未読)。

### 2-3 Burt(#15 △・#16 ◎・#17 ◎)

- Burt 2000(抄録の要旨・#17 の紹介): 金融機関の銀行員の網を 4 年、年に 1 回「頻繁で実質的な仕事の接触」の相手を挙げさせた。以前の関係が強い・同じ部門・地位が高い・共通の第三者が多いほど減衰が遅い。**減衰は時間の冪関数で、関係が古いほど・人が古株ほど減衰の確率が下がる**(新しさの不利)。本文の指数は未読(空欄 #3)。
- Burt 2001(◎): 卒業生の母校への愛着は、卒業後 20 年で直線的に約半分まで下がる(逐語: "linearly for the first twenty years to about half its initial level")。卒業後の出来事は説明できる分散の 2% だけ。これは個人の辺ではなく組織への愛着の話で、辺の減衰の錨としては弱い。
- 形の含意: 「新しい辺ほど速く消え、古い辺ほど残る」は ACT-R の基底の活性(冪の減衰と回数の和)と同じ向き。

### 2-4 眠っている関係(#18 ◎)

- 定義(逐語): "We asked respondents to choose two people with whom they had not communicated for at least three years"。3 年は恣意的と著者自身が書き、3 年と、それより長い眠りで効果の差は見られなかった。
- 母数: "Although adults accumulate thousands of ties, they actively maintain no more than one or two hundred (e.g., Killworth et al. 1990); this means that most ties are dormant."
- 結果: 再接続した眠っている関係は、今の関係と比べて遜色のない知識をもたらした。かつて強かった眠っている関係は、弱い関係の利点(効率・目新しさ)と強い関係の利点(信頼・共有された見方)の 4 つを全部もたらした。目新しさの係数: 眠っている強い関係 0.67(p<.0001)。対象は EMBA の幹部(分析は回答者 129 人)。
- v2 への含意: 保管は「消えた関係」ではなく「再び引ける関係」として持つのが錨に沿う。再会で履歴ごと表に戻す、という指示書の形と合う。

### 2-5 社会的な署名(既存 lit メモ・引くだけ)

- Saramäki ほか 2014: 18 か月で相手の入れ替わりは大きい(区間の Jaccard 0.22・0.27)が、順位ごとの配分の形は個人ごとに保たれる(d_self < d_ref が 82%±12%)。表を「今よく思い浮かぶ相手」とし、配分の形を照合の相手にする設計と相性がよい。

### 2-6 保管に入る条件と「知人」の錨

- Hall(#19 ○): 大学の発表文(逐語): "it takes roughly 50 hours of time together to move from mere acquaintance to casual friend"・"90 hours to go from that stage to simple 'friend' status"・"more than 200 hours"。2 つの研究を合わせると「40〜60 時間で気軽な友人・80〜100 時間で友人・200 時間超で親しい友人」。"Hours spent working together just don't count as much"。本文にあるとされる 94・164・219 時間(ロジスティック回帰の 50% の点)は検索要約だけで未確認(空欄 #9)。
- Reis ほか 2011(#20 ◎): 研究 2 は約 15 分のオンラインの会話を 1・2・4・6・8 回。相手を知っている感覚は線形に増え、**1 回から 2 回への伸びが他より大きい**(逐語: "this result stemmed from the larger increase from one-chat to two-chat relative to the other condition differences")。
- Milgram と Paulos & Goodman(#24 ◎・Milgram の値は二次): 「見慣れた他人」= 繰り返し見るが話さない相手。Milgram の調査で 89% が 1 人以上を見分け、平均 4.0 人。2004 年の再現では 77.8%・平均 3.1 人・中央値 2。その場にいる時間の中央値が 15 分の昼の人は平均 3.9 人、5 分のバス停の人は 2.3 人。
- 1 日に何人の新しい知り合いができるか(流れの量)の錨は見つからなかった(空欄 #4)。手元にあるのは在庫の量(Dunbar の 500・Levin の「数千」)だけ。

### 2-7 保管の容量の検算(算術)

- 指示書の前提: 1 日 2 人 × 365 日 × 390,067 体 = 年 2.85 億件。1 件 16 B なら **4.556×10⁹ B = 4.6 GB(10 進)= 4.24 GiB**。16 B は今の辺の行(相手 4・種別 1・符号 1・最初 4・最後 4・回数 2)と同じ大きさで、指示書の数字はこの前提で合う。
- 保管に必要な欄が「誰か 4・最初 4・回数 2・最後 4」だけなら 14 B で、年 3.99 GB。
- 2 人/日が続くと 1 体あたり年 730 件になり、2 年で Dunbar の 1500 の層を超える。保管に入る条件を付けないと、Levin の「数千」を数年で超える(推測)。

---

## §3 C. 同席の相互作用の強さ

### 3-1 錨の一覧

| 錨 | 条件 | 量 | 等級 |
|---|---|---|---|
| Rohrer ほか 2021(#21) | ハンガリーの小中学校 40 校・182 学級・2,996 人。2 人机への無作為の割り当て・2017-09〜2018-01(約 5 か月)・算数・ハンガリー語の文学・文法の 3 科目 | 相互の「親友」の指名の確率 **15.3% → 22.3%(+7.0 ポイント・95% CI 4.6〜9.4)**。最も保守的な補完で 14.6% → 18.7%(+4.0)。男女の組 +2.3・女子同士 +9.3・男子同士 +13.1 | ○ |
| Back ほか 2008(#22) | 新入生 54 人・初回の 1 回だけの説明会で座席を無作為に割り当て | 1 年後、隣の席だった相手・同じ列の相手との友情の強さが高い。効果の大きさは未読(空欄 #5) | △ |
| Moreland & Beach 1992(#23) | 100 人超の講義に女性 4 人が 0・5・10・15 回出席し、誰とも話さない。学期末に学生 130 人が評定 | 見慣れの効果は弱く、好意と似ているという感覚への効果は強い。条件ごとの平均は未読(空欄 #6) | △ |
| Reis ほか 2011 研究 1(#20) | 初対面の同性 2 人が 2 問(平均 129 秒)か 6 問(平均 394 秒)話す | 魅力 3.55 → 4.17・d=0.91 | ◎ |
| Reis ほか 2011 研究 2(#20) | 約 15 分のオンラインの会話を 1・2・4・6・8 回 | 魅力に線形の傾向(F(1,101)=5.15・p=.03)。知っている感覚は 1→2 回の伸びが最大 | ◎ |
| Hall(#19) | 新しい知り合いとの時間 | 気軽な友人まで 40〜60 時間。一緒に働いた時間は「あまり数えない」 | ○ |
| 単純接触(R-51・引くだけ) | 実験室 | 好意は接触の回数の対数で増える(Zajonc & Rajecki 1969 ◎)。回数が多いと逆 U | 既存 |
| 見慣れた他人(#24) | 駅・バス停・昼の広場 | 話さなくても 3〜4 人を見分ける。滞在が長いほど多い | ◎ |
| Festinger 1950 | 寮の近さと友人 | **台帳 B1 = holdout。較正に使わない** | × |
| Allen 1977 | 職場の距離と交流 | R-80 の空欄のまま | × |

### 3-2 読み

- 「定型のやりとりや同席だけで、関係は少しだが確かに育つ」は錨が複数ある(Rohrer の無作為化・Back・Moreland & Beach)。
- 「1 回の同席で何点」を示す錨は無い。Rohrer の +7.0 ポイントは約 5 か月分の机の隣の累積で、1 回あたりへ割るには授業の回数と時間の前提が要る(推測になる)。
- Hall の「一緒に働いた時間はあまり数えない」と、Reis の「会話の長さと回数で魅力が増える」を合わせると、**同席 1 回の重みは会話 1 回より小さい**、という順序だけは錨から言える。比の値は無い。
- Moreland & Beach は「見慣れより好意が先に動く」と報告している。v2 の辺の強さ(想起のしやすさ)と好意(符号)を分けるなら、同席は強さにも符号にも少しずつ効く形が錨に近い。ただし v2 の今の同席の腕は符号 +0 で、強さだけを動かす(指示書 C1 の「関係辺(顔なじみ)だけを少し強める」と同じ)。

---

## §4 D. v2 への当てはめ(親への案・未決定・全部 expedient の印つきの候補)

### 4-1 想起の式の候補

| 候補 | 式 | 長所 | 短所 |
|---|---|---|---|
| (a) ACT-R 型(加算) | 想起の強さ = B_i + w_ctx · cos(e_印象_i, e_問い) | 単位が log-odds で、τ と同じ尺度で閾値を引ける。候補の集合に依存しない。B は今の辺の式をそのまま使える | w_ctx の値に錨が無い(ACT-R の W·S の対応は形だけ) |
| (b) GA 型(min-max 正規化の和) | α_r·recency + α_i·importance + α_v·relevance(各 [0,1]) | 原典の既定(α=1・0.995/時)がある | 正規化が候補の集合に依存し、同じ記憶の点数が周りの記憶で変わる。閾値で「思い浮かばない」を表しにくい |

- 案: (a) が辺の表(閾値で入る・出る)と同じ尺度で書けるので扱いやすい。w_ctx は expedient として宣言し、感度の腕を {0, 0.5, 1, 2} で置く(推測)。記憶アジェンダ M6 (a)(第 1 段は埋め込み無し = w_ctx=0)とそのままつながる。
- B の形: 「最後に会ってからの時間」を入れるなら ACT-R の折衷(直近 k 回の時刻)。k=3 なら 600 B/体の追加(§1-3・推測)。
- d=0.5 の出典の書き方は「ACT-R マニュアルの強い推奨値」。Anderson & Schooler 1991 の環境の指数(.73〜.83)は d₁ とは別物で、同じ数として比べない。

### 4-2 関係の減衰の式(記憶と分ける形)

- 今の「6.9〜7.25 時間で消える」は、L を**分**で数えていることから来る(冪の +1 があるので、時間の単位を変えると閾値を越える時刻が変わる)。算術: n=1・τ=−2.322 で L+1 = 415.8 単位。単位が分なら 6.9 時間、時なら約 17 日、日なら約 1.14 年。
- 候補(どれも expedient):
  - (i) 想起のしやすさ(表に入るか)は今の式のまま、親しさ(保管と符号の重み)を別の遅い量にする。
  - (ii) 関係だけ d を小さくする(d_rel)。
  - (iii) 関係だけ L の単位を日にする。
- 較正の相手: Roberts & Dunbar の「友人の最後の接触からの日数」28/69/129 日(中央値 1/22.5/27)と、前半が大きい落ち方(−0.82 と −0.31)。Dunbar 2020 の「数か月」「3 か月超」。Levin の「3 年以上でも再接続の価値がある」(保管から戻せることの錨)。どれも英国の学生か米国の幹部で、日本の都市の一般の人ではない(フロア: 同じデータで性別により効果が有意でなくなる・交互作用 0.51)。
- 家族は接触が無くても下がらない(+0.27)。v2 では世帯の辺は毎日の同居で回数が積まれるので、種別ごとの定数を置かなくても差が出る(既存 lit メモと同じ読み)。

### 4-3 保管の形と条件

- 欄: 相手 int32・最初 int32・回数 u16・最後 int32(14 B)。種別と符号を残すなら 16 B。印象の埋め込みは持たない(§1-7)。
- 入る条件の候補:
  - (α) 条件なし(指示書の今の形)。年 4.6 GB。
  - (β) 回数 n ≥ 2(Reis の 1→2 回の伸びが錨の候補・店員と 1 回だけ話した相手は入らない)。
  - (γ) 会話の合計の分数 ≥ X(Hall の時間の物差しに近いが、X の錨は無い)。
  - (δ) 名前を知った(v2 にまだ名前の交換の概念が無い。将来)。
- 監視: 体あたりの保管の件数の分布と、Dunbar の 500・1500 の層との比(超えたら条件を見直す合図)。

### 4-4 同席の強化量の仮の値と感度試験

- 形の候補: 同席 1 本を、ACT-R の提示の「端数の 1 回」として n に w_c を足す(会話 1 回 = 1)。
- 仮の値: w_c ∈ {0, 0.1, 0.25, 0.5}。案の既定は 0.25(推測・錨は「会話より小さい」という順序だけ)。
- 感度試験の設計(推測):
  - 見るもの: 表の入れ替わり(区間の Jaccard を Saramäki の 0.22〜0.27 と並べる)・職場の辺の割合・1 日の会話の相手の選ばれ方(Dunbar の 40%/20%)・保管の増え方。
  - 判定: w_c を 0 から 0.5 まで動かしても、会話の相手の選び方の分布が変わらなければ「結果を駆動していない」。変わるなら錨探しを優先。
  - 照合の相手(較正ではない): Rohrer の +7.0 ポイントは「5 か月の机の隣」での相互の指名の差なので、学校の体で 5 か月を回せる日まで照合に使えない(当分は測れない)。
- 決定モデルが状況に応じて量を変える形(指示書 C1 の候補)は、錨が無く、決定モデルの導入(R-a)の後の問い。

### 4-5 印象の記憶を誰がいつ書き換えるか(先行例の整理)

| 候補 | 先行例 | 費用 |
|---|---|---|
| (a) LLM の会話の後に、本人の LLM が 40 字程度で書き換える | AGA(#5) | 会話 1 回に呼び出し 1 回の追加、または会話の最後の発話に同梱 |
| (b) 反省のときにまとめて書く | GA(#4・150 の閾値で 1 日 2〜3 回) | 反省の呼び出しに相乗り |
| (c) 印象の欄を持たず、毎回エピソードから引き直す | GA の反応の文脈 | 埋め込みの検索が毎回要る |
| (d) エンジンが書く | 先行例なし | 「意思決定と発話だけ LLM」の背骨とぶつかる |

### 4-6 埋め込みモデルの候補(設計者の恣意として宣言する前提)

- Ruri-v3-30m(37M・256 次元・Apache-2.0・表 72.95): CPU で回しやすい。腕の既定の候補。
- Ruri-v3-130m(132M・512 次元・表 75.52): 質の腕。
- Sarashina は非商用の許諾なので、収益化の領域(広告・情報伝播)を考えると候補から外す理由になる。
- PLaMo-1b は Apache-2.0 で STS と検索の一部が強いが、1B で CPU には重い。

### 4-7 H7(記憶の作り直しの壁打ち)の問いの案

1. 想起の式は ACT-R 型(活性 + w·コサイン・閾値つき)と GA 型(正規化した 3 項の和)のどちらにするか。
2. 「最後に会ってからの時間」を式に入れるために、直近 k 回の時刻を持つか(k=3 で約 234 MB/39 万体)。持たないなら今の近似(最初に会ってからの時間)のまま。
3. 関係の減衰を記憶と分ける形は (i) 別の遅い親しさの量・(ii) 関係だけの d・(iii) 関係だけ L を日で数える、のどれにするか。較正の相手は Roberts & Dunbar の 28/69/129 日でよいか。
4. 保管に入る条件は「条件なし」「2 回以上会った」「会話の合計 X 分以上」のどれから始めるか。
5. 同席の強化量 w_c の既定と感度の幅(0・0.1・0.25・0.5)でよいか。符号は動かさない(+0)ままでよいか。
6. 印象の記憶は誰がいつ書くか((a) 会話の後に本人の LLM・(b) 反省のとき・(c) 欄を持たない)。
7. 埋め込みは Ruri-v3-30m を既定の腕にするか。重みの取得(huggingface.co は許可の一覧の外)をどうするか。
8. 印象の埋め込みは表の 50 辺だけに持たせ、保管には持たせない、でよいか。

---

## §5 本サブの読みと注意

- 錨の強さ: A(想起の式)は原典で確定できた。B(関係の減衰)は「下がる・前半が速い・家族は下がらない・3 年後でも戻せる」という形の錨はあるが、暦の上の速さの数値は無い。C(同席)は「会話より小さいが確かに育つ」という順序と、5 か月の累積(+7.0 ポイント)だけがある。
- 循環参照の注意: d=0.5 を Anderson & Schooler 1991 に帰す書き方は、原典の本文と合わない(§0-1)。
- フロアの併記: Roberts & Dunbar の効果は性別で有意かどうかが分かれる(交互作用 0.51)。Rohrer の +7.0 は補完の仕方で +4.0 まで下がる。埋め込みの表の上位はモデルカードと表で 1.5 ポイント前後ずれる。

## §6 空欄

1. Roberts & Dunbar 2011 EHB の本文の係数(出版社 403)。
2. 親しさが 1 か月あたりどれだけ下がるかの暦の上の値(2015 の再解析の本文に無い)。
3. Burt 2000 の本文の減衰の関数の指数(出版社・抄録の取得不可)。
4. 1 日に新しくできる知り合いの人数(流れの量)の錨。
5. Back ほか 2008 の効果の大きさ。
6. Moreland & Beach 1992 の条件ごとの平均。
7. 日本語の埋め込みモデルの CPU の処理量の実測。
8. AgentSociety の関係の強さを更新する規則。
9. Hall の本文の 94・164・219 時間(検索要約のみ)。
10. MTEB の公式の表(動的な画面で文面を読めず)の最新の日本語の順位。
11. Dunbar 2020 の 1500 の層の呼び名と、図 3 の層ごとの接触の頻度の値(画像)。
12. ACT-R で S を「およそ 2」とする原典の値(チュートリアル未読)。
13. Allen の距離と交流の曲線の原典の数値(R-80 から引き継ぎ)。
14. 日本の「顔見知り」の形成の量的な研究(探したが見つからず)。

## §7 親が確認すべき上位

1. ACT-R マニュアルの :bll の推奨値の一文(#1)と、Anderson & Schooler 1991 に d=0.5 が無いこと(#2)。リポの「d=0.5(Anderson & Schooler 1991)」の書き方を grep し、訂正の伝播が要るか。
2. GA の recency が「最後に想起されてから」であること(#4 §4.1)。v2 の記憶の式で「最後の出来事から」と書いた箇所が無いか。
3. Rohrer ほか 2021 の 15.3% → 22.3%(+7.0)と保守的な +4.0(#21・読み取り器経由なので本文の表で)。
4. Dunbar 2020 の「500 (acquaintances)」と、lit メモの「150 acquaintances / 500 known names」の食い違い(#14)。
5. JMTEB の表の値(commit 9b1e683)とモデルカードの値が違うこと、Sarashina の非商用の札(#7・#8)。
