<!-- hdr:v1 | 等級: B(第347 親の一次確認=末尾の表) | 作成: 2026-11-16 | 範囲: 返事その 8(11-16)§3 A48・M10 の根拠の一次確認 -->
# R-155 版上げ A48・M10 の ① の根拠の一次確認と、M10 の ① の決まっていない細部の材料(記録 2-55・2-59 が引く 5 本・会話の後に誰が考え直すか・何を覚えているか・どのくらい覚えているか)

- **分野**: 認知科学(記憶・習慣) #12 / 人間工学・HCI / 交通工学(活動ベース) #2 / 会話分析 | **重要度**: 発注文に記載なし(親が付ける)。材料にする所は [返事その 8(11-16)](../design/prompt-2026-11-16-reply8.md) §3 の A48・M10 の行と、[壁打ちの記録](../reference/wallbounce-record-2026-11-02_05.md) 2-55・2-59
- **一次確認**: B(第347 親の一次確認=末尾の表)。筆者がこの回に読んだ出典は 29 本(◎ 1・○ 20・△ 8)。既存答申からの引用は R-136・R-41・R-89・R-103(番号と節で引き、読み直していない)。読めなかったものは §5。
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-11-16・リサーチ役(Opus 5.5)。子サブは起動していない。作ったのは本書 1 本だけで、コード・台帳・設計書・INDEX は 1 バイトも変えていない。commit も git add もしていない。封印の層(holdout・test の層)には触れていない。発注文が開かないと定めた文書(IMPLEMENTED.md・build-report-C7*/C8*・G1 のバックテストの計画・パターン台帳)は開いていない。重み・データセットの取得はしていない。
> **取り方の注**: 頁は WebSearch と WebFetch で読んだ。WebFetch は頁を小さなモデルに通して答えを返すので、引用は写しの段を 1 つ経ている(短い逐語の断片だけを頼み、長い文は要約として扱った)。要旨の多くは公開の索引(OpenAlex の `abstract_inverted_index`・Europe PMC の REST の `abstractText`・Crossref)で読んだ。PDF は 1 本だけ([S6]・発行元=CogSci の予稿を置く eScholarship)で、WebFetch がリポの外の道具の結果の置き場に自動で残した写しを、システムの Python の pymupdf で文字にして該当の節を読んだ(R-136・R-149 と同じ形。リポにも data/ にも保存していない)。curl と gh は使っていない。コードは HEAD `73c2f5fb` の `src/shibuya/world/laws/environment.py` を読んだだけ(試験は回していない)。**Web の道具は最後まで上限に当たらなかった。**
> **断られた頁**(§5 に詳細): Taylor & Francis の規約の頁 403・Wiley の規約の頁 403・ScienceDirect の robots.txt 403・De Gruyter Brill の robots.txt 405・ACM DL の本文の頁 403・EMCA wiki 403・cell.com と link.springer.com の robots が ClaudeBot を `Disallow: /`。どれも別の名乗り・経路・ミラー・キャッシュ・著者の頁・第三者の写しで取りに行っていない。**1 件だけ取り方で迷った所がある**(§5-2 の 1=Kurby & Zacks の PMC の著者稿を、発行元の robots を確かめる前に読んだ。本文の中身は本書に入れず、要旨だけで突き合わせた)。
> 等級: ◎=原典の本文の頁を読んだ/○=要旨だけ読んだ(索引の要旨を含む)/△=検索の抜粋だけ。筆者の組み立ては【見立て】、根拠の無い置き方は【推測】と書く。**推薦は書かない**。決めるのはユーザー。
> 既存答申との関係(重ねない): 中断の費用と再開の遅れ・手がかりの 8 秒・職場で同じ日に戻る 77.2% は [R-136](v2-r136-interruption-and-attention.md) §2(**B**)、何でも考え直す形と盲目的に続ける形の比べは [R-41](v2-r41-cognitive-architecture-precedents.md) §2-1(**B**)、展望記憶の多過程理論と 5 秒の遅れの値は [R-89](v2-r89-prospective-memory-punctuality.md) §1-1(**B+**)、やらなかった予定の理由と「やることの考え」の内側のきっかけ 61% は [R-103](v2-r103-surprise-prospective-memory-future-thinking.md) §2-3・§3-2(**B**)を正とする。本書は値を再掲せず番号で引き、足りない分だけを足す。

## §0 要旨

1. 記録が引く 5 本のうち、原典の本文を読めたものは無い。4 本は公開の索引の要旨(○)で確かめた。Altmann & Trafton 2002 は、同じ著者の 2004 年の予稿の本文(◎)が書く模型の要約でも確かめた。Schegloff & Sacks 1973 は、要旨に記録の言う中身が無く、確かめられない。
2. Böcker ら 2013 の要旨は「天気が移動、特に歩きと自転車にとって何を意味するかを知ることが重要になった」と書き、結論は「既存の研究の像は不完全で断片的」である [S1]。記録の「特に歩きと自転車に効く」は、同じ著者の博士論文の要旨の抜粋(△)とは向きが合う [S2]。ただし記録の文は、総説の結論の「不完全で断片的」を落としている=一部合う。
3. Rajagopalan & Lall 1999 は、6 つの気象の量をまとめた 1 日の組を過去の記録から引き直す。引くときは、前の日の組を特徴にした k 近傍に重みを付ける(1 次のマルコフ過程の代わり)[S3]。今の W13 の層の抽選は日の番号ごとに独立で、前の日の天気に条件を付けていない(コードで確認・§2-2)。「過去の実日をまるごと引き直す」は合うが、「W13 はこれに沿う」は一部だけ合う。「定番」という言い方は要旨に無い。
4. Kurby & Zacks 2008 の要旨は「出来事への切り分けは作業記憶の更新と関わる」と書く [S4]。区切りで見立てを更新する点は合う。ただし要旨が扱うのは見ている行動の切り分けで、「会話の終わり=区切り」は記録の当てはめである。
5. Altmann & Trafton の 2004 年の予稿は、「中断の間に元の課題の表象は薄れ、再開には手がかりが要る」と 2002 年の模型を要約する [S6]。ただし同じ予稿の実験が測ったのは、割り込みの後に元の課題で最初に操作するまでの秒数で、手がかりはそれを縮めただけ(中断の前の 8 秒で有意)である。再開しない率は測っていない。記録の「手がかりがあるときだけ再開される」は、実験の結果より強い。
6. 細部 (a) 誰が考え直すか。職場の割り込みの後に元の活動へ戻ったのは 55.2%、元の作業が割り込みの後も止まったのは 41% だった(O'Conaill & Frohlich 1995・△)[S16]。メタ分析は「中断した課題に戻る傾向は一般的」とする(○・率 約 67% は △)[S19][S20]。会話の最中に別のことを始めていた人と、話していただけの人を比べた実測は見つからなかった(空欄)。
7. 細部 (b) 何を覚えているか。まだ済んでいない意図と途中の意図は、中立の材料より速く思い出され、済んだ意図は遅くなる [S21]。中断で失われやすいのは「手順のどこまでやったか」で、「1 歩のやり方」は失われにくい [S27]。部屋を移ると物の記憶が落ちるという結果 [S22][S23] は、追試では作業記憶に負荷があるときにしか出なかった [S25]。行き先・作業・これからの予定を並べて比べた研究は見つからなかった。
8. 細部 (c) どのくらいの間覚えているか。5〜40 秒の遅れでも、負荷や割り込みがあると意図はすぐに忘れられた [S11]。McDaniel ら 2004 では、遅れの長さ(5・15・40 秒)と割り込みの長さ(10・20 秒)は効かず、割り込みがあるかどうかが効いた。外の手がかりで差は消えた [S12]。中断が長いほど、また割り込みが複雑なほど、目標を取り出す時間は延びる [S28]。分の単位の実測は職場の観察(R-136 の Mark 2005)だけで、会話の長さに合う実験は見つからなかった。
9. 【見立て】ここで引いた人の実測の多くは、再開を促す合図の無い条件で測っている。M10 の ① は「会話が終わった」を理由に本人を起こし、前の意図を見せる。人の研究でこれに近いのは、合図・外の手がかり・場面を戻す条件の方である [S12][S13][S10]。§3 の表は細部の案ごとに並べた。推薦は書かない。
10. 親に確かめてほしい数値は §6 の末尾。

## §1 問いと前提

### 1-1 問い(発注文)

1. 仕事 1: 記録 2-55・2-59 が引く 5 本について、記録の文と原典の言っていることが合うか。§2。
2. 仕事 2: M10 の ① の決まっていない細部 3 つについて、人の研究が何を言っているか。(a) 誰が考え直すか(細部 M10-1)・(b) 何を覚えているか(細部 M10-2)・(c) どのくらいの間覚えているか(細部 M10-5)。§3。
3. 範囲の外: 天気が歩行者の数に与える効き目の大きさ・LLM のエージェントの実装の比べ・既存の答申の書き直し。

### 1-2 前提(下調べの細部の案の記号)

下調べ(親の計画の写し。リポの外)の §3-3 の記号を使う。中身は下調べが正。

- **M10-1 起こす相手**: (a) 会話中のまま終わって IDLE に戻した体 (b) 参加者全員(会話の番で別の行為を選んだ体を含む) (c) (a) と、別の行為でもその場の活動の体。
- **M10-2 会話の前の意図の中身**: (a) 歩く意図だけ (b) (a)+活動の文 (c) (b)+乗車と就寝の意図 (d) (c)+日課の行。
- **M10-5 見せる長さ**: (a) 終わった後の最初の判断で 1 回 (b) 次の判断まで(繰り延べで遅れても) (c) 記憶の式で薄れるまで。

## §2 仕事 1: 記録が引く 5 本の一次確認

### 2-0 まとめの表

| # | 文献 | 記録の文(要点) | 読めた範囲と等級 | 合うか | 記録が原典より強く言っている所 |
|---|---|---|---|---|---|
| 1 | Böcker, Dijst & Prillwitz 2013 | 2-55「天気は日々の移動、特に歩きと自転車に効く」 | 索引の要旨 ○ [S1]・博士論文の要旨の抜粋 △ [S2] | 一部 | 要旨の結論「不完全で断片的」を落としている。効く向きは △ の出典にしか無い |
| 2 | Rajagopalan & Lall 1999 | 2-55「気象を作る定番は過去の実日をまるごと引き直す」「W13 の設計と本筋の道はこれに沿う」 | 索引の要旨 ○ [S3]・W13 の引き方はコード ◎ | 一部 | 「定番」は要旨に無い。前の日に条件を付ける点が W13 に無い |
| 3 | Kurby & Zacks 2008 | 2-59「会話の終わりは出来事の区切りで、区切りで見立てを更新する」 | 索引の要旨 ○ [S4](本文は §5-2 の 1) | 一部 | 「会話の終わり=区切り」は要旨に無い(記録の当てはめ) |
| 4 | Altmann & Trafton 2002 | 2-59「中断された目的は新しい目的に埋もれて薄れ、結び付いた手がかりがあるときだけ再開される」 | 索引の要旨 ○ [S5]・同じ著者の 2004 の予稿の本文 ◎ [S6] | 模型の要約としては合う | 「だけ再開される」は、2004 の実験(手がかりなしでも再開の遅れが測られた・手がかりは遅れを縮めただけ)より強い |
| 5 | Schegloff & Sacks 1973 | 2-59「会話の終わりは二人で作られ、先の取り決めを含むことが多い」 | 索引の要旨 ○ [S7]・二次の抜粋 △ [S8] | 確かめられない | 「多い」という頻度は、読めた範囲のどこにも無い |

### 2-1 Böcker, Dijst & Prillwitz 2013

- **書誌**: Böcker L., Dijst M., Prillwitz J.「Impact of Everyday Weather on Individual Daily Travel Behaviours in Perspective: A Literature Review」Transport Reviews 33(1): 71–91(2013。OpenAlex の公開日は 2012-12-05)。DOI 10.1080/01441647.2012.747114。閉じた出版(OpenAlex の is_oa=false)。
- **読めた範囲**: OpenAlex の要旨(○)[S1]。発行元の Taylor & Francis は robots.txt では `/doi/` の頁を禁じていないが、規約の頁が 403 で規約を読めなかったので、発行元の頁は開いていない(§5-1)。
- **原典の言っていること**: 要旨の最初の文は、気候への適応と緩和への関心の高まりの中で「weather conditions for travel behaviours—particularly walking and cycling—have become very important」と書く(天気が移動、特に歩きと自転車にとって持つ意味を知ることが重要になった)。目的は運輸・健康・生気象の研究をまとめること。主な結論は「an incomplete and fragmented picture of the impact of weather on travel behaviour」で、気候の変化への計画を難しくしている、とする [S1]。
- **効く向き**: 同じ著者の 2014 年の博士論文の要旨(検索の抜粋・△)は、雨・雪・曇り・風・寒さ・暑さが屋外の活動と歩きと自転車の利用を減らし、歩きと自転車の利用者が天気に最も敏感だと書く [S2]。総説そのものの本文でこれを確かめてはいない。
- **主な数値**: 要旨には数値が無い(OpenAlex の被引用 445)。
- **合うか**: 一部。歩きと自転車を重点に挙げる点は要旨と合う。「効く」は要旨の文ではなく、効く向きは △ の出典にしか無い。要旨の結論(像は不完全で断片的)は記録の文に無い。

### 2-2 Rajagopalan & Lall 1999

- **書誌**: Rajagopalan B., Lall U.「A k-nearest-neighbor simulator for daily precipitation and other weather variables」Water Resources Research 35(10): 3089–3101(1999)。DOI 10.1029/1999WR900028。
- **読めた範囲**: OpenAlex の要旨(○)[S3]。OpenAlex は発行元(Wiley)の PDF の頁を公開(bronze)と示すが、Wiley の規約の頁が 403 で規約を読めなかったので開いていない。CiteSeerX と著者の所属先の写しも開いていない(§5-1)。
- **原典の言っていること(要旨の逐語の断片)**: 1 日の気象の組を、過去の記録から「by conditioning on the vector of the same variables (feature vector) on the preceding day」引く。「The resampling is done from the k nearest neighbors in state space of the feature vector using a weight function」。組の中身は「solar radiation, maximum temperature, minimum temperature, average dew point temperature」と「average wind speed, and precipitation」の 6 つ。当てはめは「30 years of daily weather data at Salt Lake City, Utah」。結果は「a multivariate autoregressive model similar to that of Richardson [1981]」と比べた。要旨は、この方法を 1 次の多変量マルコフ過程のノンパラメトリックな代わりと位置づけ、同時分布の形を前もって仮定しなくてよいとする [S3]。
- **主な数値**: 6 変数・30 年・Salt Lake City(要旨)。被引用 436(OpenAlex)。
- **W13 の引き方(コードで確認)**: `src/shibuya/world/laws/environment.py:157-184` の `sample_calendar_day` は、季節 × 平日/土休 の候補日から天候型を日数の割合で引き、その型の日を一様に引く。乱数の鍵は「`calendar|季節|平日/土休|日番号`」で、**前の日に引いた日や天気を条件にしていない**。暦の日付が W13 の窓の中で揺らさないときは、その日の実際の天気をそのまま使う(`:303-305`=続いた実際の日の並びが残る)。
- **合うか**: 一部。「過去の実日をまるごと(1 日の量の組ごと)引き直す」は合う。違いは 2 つ。(i) 原典は前の日の状態に条件を付けて k 近傍で引くので、日から日への続き方(雨の続く日など)を残そうとする。W13 の層の抽選は日ごとに独立で、層(季節・平日/土休・天候型の割合)だけを合わせる。(ii) 原典は 1 地点の 30 年の記録で、W13 は 365 日の窓である。【見立て】複数日のランで窓の外の日を引くとき、天気の続き方は今の形では残らない。これが結果に効くかは測られていない。
- **記録が強く言っている所**: 「定番」は要旨に無い(被引用の多さからの言い方と読める)。「W13 の設計はこれに沿う」は、前の日への条件づけを除けば、という限りでの話である。

### 2-3 Kurby & Zacks 2008

- **書誌**: Kurby C.A., Zacks J.M.「Segmentation in the perception and memory of events」Trends in Cognitive Sciences 12(2): 72–79(2008)。DOI 10.1016/j.tics.2007.11.004。PMID 18178125・PMCID PMC2263140。
- **読めた範囲**: Europe PMC の要旨(○)[S4]。本文の扱いは §5-2 の 1(PMC の著者稿を読んだが、発行元 cell.com の robots が ClaudeBot を禁じていたので、本文の中身は本書に入れていない)。
- **原典の言っていること(要旨の逐語)**: 「People make sense of continuous streams of observed behavior in part by segmenting them into events.」「Event segmentation seems to be an ongoing component of everyday perception.」「Events are segmented simultaneously at multiple timescales, and are grouped hierarchically.」区切りで後部側頭・頭頂と外側前頭の活動が一時的に増える。「The parsing of ongoing activity into events is related to the updating of working memory, to the contents of long-term memory, and to the learning of new procedures.」「Event segmentation might arise as a side effect of an adaptive mechanism that integrates information over the recent past to improve predictions about the near future.」[S4]
- **主な数値**: 要旨に数値は無い。
- **合うか**: 一部。区切りと作業記憶の更新の結びつきは要旨にある。「会話の終わりは出来事の区切り」は要旨に無い。要旨の対象は見ている行動の流れで、自分で会話を終えることは扱っていない。
- **記録が強く言っている所**: 「会話の終わり=区切り」は記録の当てはめ(【見立て】の段)。なお既存の [知覚のタイミングの答申](v2-perception-timing-research.md) 262 行目は、Zacks ら 2007 の理論を総説経由(原著は未読)で引いている。
- **関わる注意**: 区切りの後は、前の出来事の情報が取り出しにくくなるという結果の系統がある(場所の移動の実験=§3-2 の [S22][S23]。追試の結果は分かれる=[S25])。M10-2 の「前の意図」は、会話の始めと終わりという 2 つの区切りをまたぐ情報にあたる【見立て】。

### 2-4 Altmann & Trafton 2002

- **書誌**: Altmann E.M., Trafton J.G.「Memory for goals: an activation-based model」Cognitive Science 26(1): 39–83(2002)。DOI 10.1207/s15516709cog2601_2(Wiley)。同じ論文に Elsevier の DOI 10.1016/S0364-0213(01)00058-1 もある(OpenAlex の別の場所)。
- **読めた範囲**: OpenAlex の要旨(○)[S5]。Wiley の規約の頁は 403、ScienceDirect の robots.txt も 403 で、どちらの発行元の頁も開いていない。DTIC と CiteSeerX の投稿版の写しも開いていない(§5-1)。既存の R-136 [S1] は △ だった。
- **原典の言っていること(2002 の要旨の逐語の断片)**: 目標で動く認知を「goal stack」のような専用の記憶の棚ではなく「in terms of the general memory constructs of activation and associative priming」で分析する。制約は 3 つ。「the interference level, which arises from residual memory for old goals」・「the strengthening constraint, which makes predictions about time to encode a new goal」・「the priming constraint, which makes predictions about the role of cues in retrieving pending goals」。ハノイの塔(「a means-ends puzzle that depends heavily on suspension and resumption of goals」)の時間と誤りで確かめ、「intention superiority, postcompletion error, and effects of task interruption」への含意を論じる [S5]。要旨に「decay(薄れる)」の語は無い。
- **同じ著者の 2004 の要約(◎・予稿 43 頁)**: 「during an interruption, the cognitive representations that support performance of the primary task will decay, in particular relative to the cognitive representations that support performance of the secondary task. Thus, when resuming the primary task, retrieval cues will be necessary to re-activate the relevant representations.」[S6]
- **2004 の実験で測ったもの(◎・R-136 §2-2 #1・#2 と同じ)**: 4 実験・各 24 人(計 96 人)。割り込みは 30〜45 秒続く 2 択の判断の課題で、割り込みの時機は機械が決める。測るのは、割り込みの課題が終わってから元の課題で最初に操作するまでの秒数(再開の遅れ)。再開しない率を測る作りにはなっていない【見立て: 方法の節の読み】。再開の遅れは 3.8 秒で、ふだんの操作の間隔 1.9 秒の 2 倍(全実験で p<.0001)。手がかり(中断の前の間に元の画面が見えるか)の効果は、中断の前の間が 2 秒と 4 秒で F<1、6 秒で F(1,22)=4.1・p=.056、8 秒で F(1,22)=5.7・p<.03(結果の節・図 6)[S6]。
- **合うか**: 模型の要約としては合う(薄れる・再開に手がかりが要る)。「新しい目的に埋もれて」は 2004 の「割り込みの課題の表象に比べて薄れる」に当たる。2002 の要旨が言う干渉は「古い目標の残り」からの干渉である。
- **記録が強く言っている所**: 「結び付いた手がかりがあるときだけ再開される」。2004 の実験では手がかりの無い条件でも再開の遅れが測られており(=元の課題に戻っている)、手がかりが変えたのは再開までの秒数である。再開しない率はこの実験では測っていない。手がかりが効いたのは中断の前の間が 8 秒のとき(6 秒は境目)である。

### 2-5 Schegloff & Sacks 1973

- **書誌**: Schegloff E.A., Sacks H.「Opening up Closings」Semiotica 8(4)(1973)。DOI 10.1515/semi.1973.8.4.289。頁は検索の抜粋で 289–327(△)[S8]。Crossref と OpenAlex には頁の欄が無い。1974 年に Turner 編の論集(Penguin)の 233–264 頁に再録とする抜粋もある(△)。
- **読めた範囲**: OpenAlex の要旨(○)[S7]。発行元の De Gruyter Brill の robots.txt が 405 を返し、規約も読めなかったので、発行元の頁は開いていない。EMCA wiki は 403(§5-1)。
- **原典の言っていること(要旨の逐語の断片)**: 「The paper presents some of the ways that have been developed for dealing with closings in conversation.」最初の問題を会話の最も基本的な性質から引き出し、「A partial solution is developed.」その解の難しさから 2 つ目の問題を立てる。最後に「an attempt to specify the domain for which the closing problems, as they have been posed seem apposite」[S7]。要旨は論文の組み立てだけを述べる。
- **二次の抜粋(△)[S8]**: 終わりの前置き(pre-closing)は相手が話を続けたいかを確かめる交渉の段で、話題は開き直すことも閉じることもできる。終わりの段には取り決め・次の会への結び付け・話題の開き直しなどが差し込まれることがある。「まだ言っていない言うべきこと(unmentioned mentionables)」は 303 頁、とする(Language and Psychoanalysis 2016 の論文の抜粋)。
- **合うか**: 確かめられない。要旨には「二人で作る」「取り決め」のどちらの語も無い。二次の抜粋は、終わりが相手との交渉で進むこと・取り決めが差し込まれうることを述べ、記録の向きとは合う。
- **記録が強く言っている所**: 「先の取り決めを含むことが**多い**」の頻度。会話分析の原典は規範の記述で比率を測らない、という指摘が既存の [R-23 の一次確認 その 2](v2-r23-primary-check-batch2.md) の 11 行目(Schegloff 1968 について)にある。本書の読めた範囲にも頻度は無い。記録自身も「原文は読めず=知っている範囲の要旨」と書いている。

## §3 仕事 2: M10 の ① の決まっていない細部の材料

列の「関わる案」は下調べの記号(§1-2)。どの案がよいかは書かない。「既存」は既存答申の等級のまま引いたもの。

### 3-1 (a) 誰が考え直すか(細部 M10-1)

| 研究 | 対象と場面(人数) | 測ったもの | 主な数値 | 等級 | 関わる案 |
|---|---|---|---|---|---|
| O'Conaill & Frohlich 1995 [S16] | 職場の観察。29 時間の映像から 125 件の自然な割り込み(対面・自分の席 79・対面・席の外 21・電話 25) | 割り込みの後に何をしたか | 元の活動に戻った 55.2%。元の作業が割り込みの長さを越えて止まった 41%(要旨の言い方では「just over 40%」)。受け手が得をした割り込み 64% | △(検索の抜粋。数値の出どころの頁は未確認) | M10-1 (a)(b)(c) 全部(戻らない人が 4 割いる) |
| Mark ら 2005(R-136 §2-2 #5) | 情報労働者 24 人の観察 | 中断された仕事の塊に戻るか・いつ | 同じ日に戻る 77.2%・戻るまで平均 25 分 26 秒・間に 2.26 件。中心の仕事 82.0%・周辺の仕事 43.8%。外からの中断 22 分 37 秒・自分からの中断 29 分 1 秒 | 既存 ◎(親確認) | M10-1 (a)(b)・M10-2 (d) |
| Ghibellini & Meier 2025 [S19][S20] | Zeigarnik と Ovsiankina の効果のメタ分析(課題の半分を中断する同じ型の実験) | 中断した課題の思い出しと、戻る率 | 要旨「We found no memory advantage for unfinished tasks but found a general tendency to resume tasks」。統合した戻る率 約 67%(50% が差なしの線)・思い出しの比 0.99(1.00=差なし。Zeigarnik の原典の 4 実験は 2.0 前後) | ○(要旨)・数値は △(ブログの二次) | M10-1 全部・M10-2 |
| Dodhia & Dismukes 2009 [S9] | 実験室の 2 実験(符号化の条件と取り出しの条件を変える) | 中断の後に元の課題へ戻り忘れること | 要旨: 中断は注意を急に奪い、戻る意図と計画を作る間を与えない。中断の後の新しい課題の求めが、戻る合図に気づく機会を減らす。中断から次の課題への移り目は、1 つの知覚の合図でなく概念で決まるので目立たない。前身の 2003 の発表では、合図があると戻り忘れが減った(F(1,62)=5.3・p=0.02)[S10] | ○(2003 の値は △) | M10-1 (b)(別の行為を始めた体)・M10-5 (a) |
| Iqbal & Horvitz 2007(UM)[S15] | Microsoft の 16 人の機械に 2 週間の記録の道具 | 会話(対面・電話を区別できない)の間の作業と、会話の後に作業へ戻る時機 | 会話の間にも機械の作業を続ける人がいることを報告。戻る時機の値は読めていない | △ | M10-1 (b)(c) |
| Iqbal & Horvitz 2007(CHI)[S14] | 職場の機械の操作とメッセージの知らせの記録 | 中断した作業へ戻るまでの時間と、戻るのを助ける要因 | 要旨に数値は無い。抜粋では、ほかの作業が開いていて新しい作業を始められることが、戻るのと競う | ○(要旨)・△ | M10-1 (b) |
| Katidioti ら 2016 [S18] | 実験室(メールに答える課題) | 自分からの中断と外からの中断 | 題「External interruptions are less disruptive than self-interruptions」。抜粋では、再開の遅れは差が無く、自分から中断を決めるのに約 1 秒かかった(瞳孔の広がり) | △(書誌と題だけ ○ 相当) | M10-1(会話を自分から始めたか誘われたか) |
| Czerwinski ら 2004 [S17] | 情報労働者の 1 週間の日記 | 課題の種類・割り込み・課題の間を移る難しさ | 要旨に数値は無い | ○ | M10-1 |
| Kinny & Georgeff 1991(R-41 §2-1) | エージェントの模擬(穴の出る世界) | 考え直す方針の比べ | 何にでも反応して考え直す形は、変化が速い世界を除き、盲目的に続ける形より悪い | 既存(原典・親確認) | M10-1 (a) と (b) の差 |
| 路上の立ち止まり [S29] | Seattle の 108 の街区面(2019)・Boston の 19 街区(Mehta 2013) | 歩道で立ち止まる人の行動 | 立ち止まった人のうち会話をしていた人 56%(Seattle)。立ち話の後に元の行き先へ戻る割合・時間は無い | △ | 空欄の確認だけ |

**ここから言えること【見立て】**

- 割り込みの後に元の活動へ戻らない人は、職場で 2〜4 割いる(41% [S16]・同じ日に戻らない 22.8%=R-136 の 77.2% からの再計算)。メタ分析は戻る傾向そのものは一般的とする [S19]。どれも路上の立ち話の値ではない。
- 会話の最中に別のことを始めていた人(M10-1 の (b) の 191 体に当たる人)を、話していただけの人と比べた実測は見つからなかった。近いのは、中断の後に新しい課題が来ると戻る合図に気づきにくい(Dodhia & Dismukes [S9])と、会話の間にも作業を続ける人がいる(Iqbal & Horvitz [S15]・値は未読)の 2 つである。
- 戻らないことの中身は「忘れた」だけではない。日常の予定でやらなかった理由のうち「忘れた」は約 13% で、約 58% は優先順位の付け替えだった(R-103 §2-3 の Marsh, Hicks & Landau 1998。本書の [S21] とは別の論文)。

### 3-2 (b) 何を覚えているか(細部 M10-2)

| 研究 | 対象と場面(人数) | 測ったもの | 主な数値 | 等級 | 関わる案 |
|---|---|---|---|---|---|
| Marsh, Hicks & Bink 1998 [S21] | 実験室・4 実験(語の判断と再認の速さ) | 済んでいない意図・途中の意図・済んだ意図に結び付いた語の思い出しやすさ | 済んでいない意図の語は中立の語より速い(実験 1・3)。済んだ意図の語は中立の語より遅い(実験 2〜4)。途中まで済んだ意図の語も速い(実験 4)。数値は要旨に無い | ○ | M10-2 (a)〜(d)(途中の意図=歩いている途中の行き先)・M10-5 (c) |
| Altmann, Trafton & Hambrick 2017 [S27] | 実験室・順番を保つ手順の課題 | 中断の長さと、誤りの種類 | 中断の長さは「手順のどこまでやったか」を失う誤りに効き、正しい 1 歩を誤って行う誤りには効かない。薄れと頭の中の繰り返しの模型で説明。数値は要旨に無い | ○ | M10-2 (b)(活動の文=どこまでやったか) |
| Altmann ら 2014(R-136 §2-2 #4) | 実験室・300 人 | 短い中断と順番の誤り | 約 2.8 秒で順番の誤り 2 倍・4.4 秒で 3 倍。順番に関係しない誤りは増えない | 既存 ○ | M10-2 (b) |
| Radvansky & Copeland 2006 [S22] | 仮想の部屋の中を物を持って移る | 物の思い出しやすさ(持っている物/置いた物・部屋を移る/移らない) | 置いた物は持っている物より思い出しにくい。部屋を移ると思い出しにくい。部屋の移動の効き目は、持っている物の方に大きい。数値は要旨に無い | ○ | M10-2(持ち物の手がかり)・M10-5 |
| Radvansky, Krawietz & Tamplin 2011 [S23] | 3 実験(小さな画面・本物の部屋・元の部屋に戻る) | 場所を移った後の記憶の落ち | 本物の部屋でも落ちた。元の部屋に戻っても記憶は戻らなかった | ○ | M10-2(場所の手がかり) |
| Lawrence & Peterson 2016 [S24] | 本物と仮想の場所を覚えた後、頭の中で歩く | 頭の中で戸口を通ると忘れるか | 戸口を通る道で忘れが多かった | ○ | M10-2 |
| McFadyen ら 2021 [S25] | 4 実験(没入の VR・負荷あり/なし・映像を見るだけ・本物の移動) | 同じ部屋/前の部屋の物の再認 | 戸口の効き目は有意でなかった。作業記憶に負荷があるときだけ、戸口の後に取り違えの誤りが増えた。著者は「これまでの報告と合わない」と書く | ○ | M10-2(場所の効き目の床。結果は割れている) |
| Cook ら 2014 [S13] | 実験室・3 実験(遅れて実行する展望記憶) | 割り込みと場面の結び付き | 割り込みで展望記憶が落ちた。割り込みの後に元の場面を戻すと落ちが和らいだ。実行する場面を前もって知らせても和らいだ | ○ | M10-2(場所・場面の手がかり)・M10-5 |
| Altmann & Trafton 2004(R-136 §2-2 #2・本書 [S6]) | 実験室・96 人 | 中断の前に元の画面が見えるか | 中断の前の間が 8 秒のとき手がかりが再開の遅れを縮めた(6 秒は境目) | ◎ | M10-2(直前の画面=直前の状態の手がかり) |
| Ghibellini & Meier 2025 [S19] | メタ分析 | 中断した課題の思い出し | 中断した課題がよく思い出されるという効果は一般には無い | ○ | M10-2 |
| Dodhia & Dismukes 2009 [S9] | 実験室 | 戻る意図の符号化 | 中断が急だと、戻る意図がはっきり符号化されない | ○ | M10-2(何を控えるか) |

**ここから言えること【見立て】**

- 研究が比べているのは「済んでいない意図か済んだ意図か」「手順の位置かやり方か」「持っている物か置いた物か」で、M10-2 の (a) 行き先・(b) していた作業・(c)(d) これからの予定を並べて比べたものは見つからなかった(空欄)。
- 向きとしては、済んでいない意図と途中の意図は思い出されやすく [S21]、手順の位置は失われやすい [S27]。行き先(歩いている途中の意図)は前者、活動の文(どこまでやったか)は後者に近いかもしれない【推測】。
- 場所の手がかりの効き目は割れている(落ちる [S22][S23][S24]/負荷のあるときだけ [S25]/元の場所に戻っても戻らない [S23]/場面を戻すと和らぐ [S13])。会話の前後で同じ場所にいる立ち話には、そのまま当てはまらない。

### 3-3 (c) どのくらいの間覚えているか(細部 M10-5)

| 研究 | 対象と場面(人数) | 測ったもの | 主な数値 | 等級 | 関わる案 |
|---|---|---|---|---|---|
| Einstein ら 2003 [S11] | 実験室・3 実験(遅れて実行する課題) | 課題の切り替わり(5・15・40 秒後)まで意図を保てるか。注意の分割と割り込み | 「Demanding conditions as well as interruptions revealed rapid forgetting of intentions」。頭の中の繰り返しも実行意図も、速い忘れを減らさなかった(実験 2・3)。率の値は要旨に無い | ○ | M10-5 (a)(b) |
| McDaniel ら 2004 [S12] | 実験室・2 実験 | 遅れの長さ(5・15・40 秒)・遅れの中の割り込み・割り込みの長さ(10・20 秒) | 遅れの長さは有意に効かない。割り込みは遅れだけより成績を下げた。割り込みの長さ(10 対 20 秒)は効かない。実験 2 で、簡単な外の覚え書きが差を消した | ○ | M10-5 (a)〜(c)・M10-2(外の手がかり) |
| R-89 §1-1(McDaniel & Einstein 2011) | 実験室の遅れて実行する課題 | 5 秒の遅れの後の実行 | すぐ実行できると高齢者 93%・5 秒の遅れで 45%。若年 97% → 90% | 既存 ○ | M10-5(人による差の床) |
| Hodgetts & Jones 2006 [S28] | 実験室(ロンドン塔の課題に予告なしの割り込み) | 目標を保留した長さと、割り込みの複雑さ | 中断された目標を取り出すのに時間がかかり、保留が長いほど延びた。割り込みが複雑なほど延びた。数値は要旨に無い | ○ | M10-5 (c)(会話の長さ・中身の難しさ) |
| Monk ら 2008(R-136 §2-2 #3) | 実験室・3 実験 | 割り込みの長さと負荷 | 長く重い割り込みほど再開が遅い。1 分までの形は忘却で説明でき、頭の中の繰り返しで減る。秒の値は未読 | 既存 ○ | M10-5 (c) |
| Altmann & Trafton 2007 [S26] | 実験室・13,000 回を超える割り込みを集めた | 割り込みの後の回復の時間の流れ | 反応の時間は、割り込みの後の最初の 10 回の反応(15 秒ほど)でなめらかに下がった。前の文脈を記憶から少しずつ取り戻す、と著者は解釈 | ○ | M10-5 (a) |
| Mark ら 2005(R-136 §2-2 #5) | 職場の観察 | 中断から戻るまで | 平均 25 分 26 秒(標準偏差 54 分 48 秒) | 既存 ◎ | M10-5 (b)(c)(分の単位) |
| Anderson & McDaniel 2019(R-103 §3-2) | 経験サンプリング(研究 2・122 人) | 日常で「やること」を考える割合ときっかけ | やることの考えは全体の 13〜15%。きっかけは内側 61%・外側 39% | 既存 ○ | M10-5 (c)(合図なしに浮かぶ) |
| Kurby & Zacks 2008 [S4] | 総説 | 区切りと記憶 | 区切りは作業記憶の更新と結びつく(要旨) | ○ | M10-5 (a) |

**ここから言えること【見立て】**

- 秒の単位の実験(5〜40 秒・10〜20 秒の割り込み)では、遅れの長さより「割り込みがあったか」が効いた [S11][S12]。分の単位(会話の長さに当たる)では、Mark 2005 の職場の観察だけが値を持つ。会話の長さと中身の難しさで薄れ方が変わるかを、分の単位で測った実験は見つからなかった(空欄)。
- 回復は 1 回で終わらず、最初の約 15 秒にわたって少しずつ進む [S26]。これは 1 刻み 60 秒の今の世界では 1 刻みより短い。
- 合図・外の覚え書き・場面を戻す条件では、忘れが減るか消えた [S12][S13][S10]。M10 の ① の「起こす+前の意図を見せる」は、人の研究のこの条件に近い。M10-5 の (a)〜(c) は、合図を何回・どれだけの間見せるかの違いにあたる。

## §4 空欄(見つからなかったもの)

1. 路上の立ち話の後に、元の行き先へ戻る割合と戻るまでの時間。路上の立ち止まりの観察 [S29] は、立ち話の長さも戻り方も報告していない(抜粋の範囲)。
2. 会話の最中に別のことを始めていた人と、話していただけの人の、会話の後の振る舞いの比べ(M10-1 の (a) 対 (b))。
3. 中断の前の「行き先」「していた作業」「これからの予定」を並べて、どれが思い出されやすいかを比べた研究(M10-2)。
4. 分の単位の会話の後の、意図の薄れ方の実験(M10-5)。秒の実験と職場の観察の間が空いている。
5. Iqbal & Horvitz 2007(CHI・UM)の戻るまでの時間の値。検索の道具の要約は「平均 10 分を超える・2 時間を超えるのが 27%」と書いたが、その要約自身が「一般の知識から」と断っていたので使っていない。
6. Rajagopalan & Lall 1999 の、前の日への条件づけを外したときの差の値(本文の比べの表)。

## §5 読めなかったもの

### 5-1 断られた頁・開かなかった頁

| # | 何が | 理由 | 本書への影響 |
|---|---|---|---|
| U1 | Böcker ら 2013 の発行元の頁(tandfonline.com) | robots.txt は `/doi/` を禁じていなかったが、規約の頁(`/terms-and-conditions`)が 403 で規約を読めなかった | 要旨だけ(○) |
| U2 | Rajagopalan & Lall 1999・Altmann & Trafton 2002・Dodhia & Dismukes 2009・McDaniel ら 2004・Cook ら 2014 の発行元の頁(Wiley) | robots.txt は `/doi/` を禁じていなかったが、規約の頁が 403 で規約を読めなかった | 要旨だけ(○)。著者の所属先・CiteSeerX・DTIC・interruptions.net の写しは開いていない |
| U3 | Altmann & Trafton 2002 の Elsevier の版(ScienceDirect) | robots.txt が 403 | 同上 |
| U4 | Schegloff & Sacks 1973 の発行元の頁(degruyter.com → degruyterbrill.com) | robots.txt が 405。degruyter.com は degruyterbrill.com への転送で、転送先も 405 | 要旨だけ(○)と二次の抜粋(△)。著者の頁の写しは開いていない |
| U5 | EMCA wiki の Schegloff 1973 の頁 | 403 | 抜粋に出た要旨の文は使っていない |
| U6 | Iqbal & Horvitz 2007(CHI)の ACM DL の本文の頁 | 403 | 要旨だけ(○)。著者の頁・Microsoft の頁の PDF は開いていない。同じ理由で O'Conaill & Frohlich 1995・Czerwinski ら 2004 も ACM の頁は開いていない(CHI '95 の ACM の静的な頁も開いていない) |
| U7 | Iqbal & Horvitz 2007(UM)・Radvansky & Copeland 2006・McFadyen ら 2021 の Springer の頁 | link.springer.com の robots.txt が ClaudeBot・Claude-Web・anthropic-ai を `Disallow: /` | UM の論文は抜粋だけ(△)。Radvansky と McFadyen は Europe PMC の要旨(○)。McFadyen は PMC に全文があるが、要旨だけ読んだ |
| U8 | Ghibellini & Meier 2025 の発行元の頁(nature.com) | R-149 §12 の U2 で、nature.com の robots が ClaudeBot を禁じていると確かめられているので、開かなかった。著者の所属先(ベルン大学)の PDF も開いていない | 要旨だけ(○)。統合した値(約 67%・0.99)はブログの二次(△) |
| U9 | Kurby & Zacks 2008 の発行元の頁(cell.com) | robots.txt が ClaudeBot と anthropic-ai を `Disallow: /` | §5-2 の 1 |
| U10 | Einstein ら 2003・Marsh ら 1998・Altmann ら 2017・Hodgetts & Jones 2006 の発行元(APA) | 開いていない(索引の要旨で足りた) | 要旨だけ(○) |

### 5-2 取り方で迷った所(親に判断してほしい)

1. **Kurby & Zacks 2008 の PMC の著者稿**: 最初に PMC(PMC2263140・NIH の公開の著者稿)の本文を WebFetch で読んだ。その後、発行元 cell.com の robots.txt が ClaudeBot を `Disallow: /` にしていると分かった。発注の決まり(断られた発行元の論文を第三者の写しで読まない)に当たるおそれがあるので、本文で読んだ中身は本書に入れず、§2-3 は Europe PMC の要旨(○)だけで突き合わせた。PMC は確認の画面を出さず、本文を返した。
2. **Dodhia & Dismukes の 2003 年の発表(NASA の頁)**: Wiley の 2009 の論文とは別の作品(学会の発表の資料)として、著者の所属先(NASA Ames)の頁の PDF を 2 回読みにいったが、道具が何も返さなかった(断られたのではない)。3 回目は試していない。本書の [S10] の F(1,62)=5.3 は検索の抜粋(△)で、その PDF の中身ではない。これを読みに行ったこと自体が決まりの線の外か内かは、親が判断してほしい。
3. **Altmann & Trafton 2004 の予稿の PDF**: 発行元(CogSci の予稿を置く eScholarship)の PDF を WebFetch が自動で残した写しを、pymupdf で文字にして読んだ(R-136・R-149 と同じ形)。写しと文字はリポの外の道具の置き場にあり、リポにも data/ にも保存していない。
4. **検索の道具の要約が記憶で数値を足した件**: Iqbal & Horvitz 2007 の「10 分を超える・27%」は、検索の道具の要約が「一般の知識から」と断って書いたもので、本書では使っていない(§4 の 5)。

## §6 出典の表

| # | 出典 | URL | 読んだ範囲 | 等級 |
|---|---|---|---|---|
| S1 | Böcker L., Dijst M., Prillwitz J.「Impact of Everyday Weather on Individual Daily Travel Behaviours in Perspective: A Literature Review」Transport Reviews 33(1): 71–91(2013) | https://doi.org/10.1080/01441647.2012.747114 | OpenAlex の要旨と書誌・Crossref の書誌 | ○ |
| S2 | Böcker L. 2014 の博士論文(ユトレヒト大学。気候・天気と日々の移動) | (検索の抜粋。正規の頁は開いていない) | 検索の抜粋(要旨の 2 文) | △ |
| S3 | Rajagopalan B., Lall U.「A k-nearest-neighbor simulator for daily precipitation and other weather variables」Water Resources Research 35(10): 3089–3101(1999) | https://doi.org/10.1029/1999WR900028 | OpenAlex の要旨と書誌 | ○ |
| S4 | Kurby C.A., Zacks J.M.「Segmentation in the perception and memory of events」Trends in Cognitive Sciences 12(2): 72–79(2008) | https://doi.org/10.1016/j.tics.2007.11.004 | Europe PMC の要旨(本文は §5-2 の 1) | ○ |
| S5 | Altmann E.M., Trafton J.G.「Memory for goals: an activation-based model」Cognitive Science 26(1): 39–83(2002) | https://doi.org/10.1207/s15516709cog2601_2 | OpenAlex の要旨と書誌 | ○ |
| S6 | Altmann E.M., Trafton J.G.「Task Interruption: Resumption Lag and the Role of Cues」Proceedings of the Annual Meeting of the Cognitive Science Society 26(2004) | https://escholarship.org/uc/item/18b4r661 | PDF の本文(pymupdf)の要旨・序論・方法・結果・考察。年は PDF の表紙で 2004 と確認(R-136 は「2004 と推定」) | ◎ |
| S7 | Schegloff E.A., Sacks H.「Opening up Closings」Semiotica 8(4)(1973) | https://doi.org/10.1515/semi.1973.8.4.289 | OpenAlex の要旨・Crossref の書誌 | ○ |
| S8 | Schegloff & Sacks 1973 の二次の記述(頁 289–327・Penguin の再録・終わりの前置き・取り決め・303 頁) | (検索の抜粋。Language and Psychoanalysis 2016 の論文ほか) | 検索の抜粋 | △ |
| S9 | Dodhia R.M., Dismukes R.K.「Interruptions create prospective memory tasks」Applied Cognitive Psychology 23(1): 73–89(2009) | https://doi.org/10.1002/acp.1441 | OpenAlex の要旨と書誌 | ○ |
| S10 | Dodhia & Dismukes 2003 の APS の発表(合図で戻り忘れが減った・F(1,62)=5.3) | (検索の抜粋。NASA の頁は道具が返さなかった) | 検索の抜粋 | △ |
| S11 | Einstein G.O., McDaniel M.A., Williford C.L., Pagan J.L., Dismukes R.K.「Forgetting of intentions in demanding situations is rapid」J. Exp. Psychol.: Applied 9(3): 147–162(2003) | https://doi.org/10.1037/1076-898X.9.3.147 | Europe PMC の要旨 | ○ |
| S12 | McDaniel M.A., Einstein G.O., Graham T., Rall E.「Delaying execution of intentions: overcoming the costs of interruptions」Applied Cognitive Psychology 18(5): 533–547(2004) | https://doi.org/10.1002/acp.1002 | OpenAlex の要旨と書誌 | ○ |
| S13 | Cook G.I., Meeks J.T., Clark-Foos A., Merritt P.S., Marsh R.L.「The Role of Interruptions and Contextual Associations in Delayed-Execute Prospective Memory」Applied Cognitive Psychology 28(1): 91–103(2014) | https://doi.org/10.1002/acp.2960 | OpenAlex の要旨と書誌 | ○ |
| S14 | Iqbal S.T., Horvitz E.「Disruption and recovery of computing tasks: field study, analysis, and directions」CHI 2007: 677–686 | https://doi.org/10.1145/1240624.1240730 | OpenAlex の要旨(数値なし)と検索の抜粋 | ○ |
| S15 | Iqbal S.T., Horvitz E.「Conversations Amidst Computing: A Study of Interruptions and Recovery of Task Activity」User Modeling 2007(LNCS 4511): 350–354 | https://doi.org/10.1007/978-3-540-73078-1_43 | 検索の抜粋(OpenAlex に要旨なし) | △ |
| S16 | O'Conaill B., Frohlich D.「Timespace in the workplace: dealing with interruptions」CHI '95 Conference Companion: 262–263(1995) | https://doi.org/10.1145/223355.223665 | OpenAlex の書誌(要旨なし)と検索の抜粋 | △ |
| S17 | Czerwinski M., Horvitz E., Wilhite S.「A diary study of task switching and interruptions」CHI 2004: 175–182 | https://doi.org/10.1145/985692.985715 | OpenAlex の要旨(数値なし) | ○ |
| S18 | Katidioti I., Borst J.P., van Vugt M.K., Taatgen N.A.「Interrupt me: External interruptions are less disruptive than self-interruptions」Computers in Human Behavior 63: 906–915(2016) | https://doi.org/10.1016/j.chb.2016.06.037 | Crossref の書誌(要旨なし)と検索の抜粋 | △ |
| S19 | Ghibellini R., Meier B.「Interruption, recall and resumption: a meta-analysis of the Zeigarnik and Ovsiankina effects」Humanities and Social Sciences Communications 12(2025) | https://doi.org/10.1057/s41599-025-05000-w | OpenAlex の要旨 | ○ |
| S20 | Ghibellini & Meier 2025 の統合値の二次の記述(戻る率 約 67%・思い出しの比 0.99・37 研究) | (検索の抜粋。ブログ) | 検索の抜粋 | △ |
| S21 | Marsh R.L., Hicks J.L., Bink M.L.「Activation of completed, uncompleted, and partially completed intentions」JEP: LMC 24(2): 350–361(1998) | https://doi.org/10.1037/0278-7393.24.2.350 | OpenAlex の要旨と書誌 | ○ |
| S22 | Radvansky G.A., Copeland D.E.「Walking through doorways causes forgetting」(副題は確かめていない)Memory & Cognition 34(5): 1150–1156(2006) | https://doi.org/10.3758/BF03193261 | Europe PMC の要旨 | ○ |
| S23 | Radvansky G.A., Krawietz S.A., Tamplin A.K.「Walking through doorways causes forgetting」(副題は確かめていない)QJEP 64(8): 1632–1645(2011) | https://doi.org/10.1080/17470218.2011.571267 | Europe PMC の要旨 | ○ |
| S24 | Lawrence Z., Peterson D.(題は確かめていない。DOI と Europe PMC の要旨で特定)Memory 24(1): 12–20(2016・オンライン 2014) | https://doi.org/10.1080/09658211.2014.980429 | Europe PMC の要旨 | ○ |
| S25 | McFadyen J., Nolan C., Pinocy E., Buteri D., Baumann O.「Doorways do not always cause forgetting」(副題は確かめていない)BMC Psychology 9(1): 41(2021) | https://doi.org/10.1186/s40359-021-00536-3 | Europe PMC の要旨 | ○ |
| S26 | Altmann E.M., Trafton J.G.「Timecourse of recovery from task interruption: data and a model」Psychonomic Bulletin & Review 14(6): 1079–1084(2007) | https://doi.org/10.3758/BF03193094 | Europe PMC の要旨 | ○ |
| S27 | Altmann E.M., Trafton J.G., Hambrick D.Z.「Effects of interruption length on procedural errors」J. Exp. Psychol.: Applied 23(2): 216–229(2017) | https://doi.org/10.1037/xap0000117 | Europe PMC の要旨 | ○ |
| S28 | Hodgetts H.M., Jones D.M.「Interruption of the Tower of London task: support for a goal-activation approach」J. Exp. Psychol.: General 135(1): 103–115(2006) | https://doi.org/10.1037/0096-3445.135.1.103 | Europe PMC の要旨 | ○ |
| S29 | 路上の立ち止まりの観察(Seattle 市の歩道の調査 2019・Mehta 2013「The Street」) | (検索の抜粋) | 検索の抜粋 | △ |

- 等級の数: ◎ 1(S6)・○ 20(S1・S3・S4・S5・S7・S9・S11・S12・S13・S14・S17・S19・S21〜S28)・△ 8(S2・S8・S10・S15・S16・S18・S20・S29)。
- S22〜S25 の題は、WebFetch の答えに出た範囲(主題)だけを書いた。副題は記憶で埋めていない。
- コードの読み: `src/shibuya/world/laws/environment.py:157-184`(`sample_calendar_day`)・`:289-314`(`_pick_day_calendar`)を HEAD `73c2f5fb` で読んだ(◎・出典の数に入れていない)。
- **親に確かめてほしい数値**: ① O'Conaill & Frohlich 1995 の 41%・55.2%・125 件(79/21/25)(△)② Ghibellini & Meier 2025 の戻る率 約 67%・思い出しの比 0.99・37 研究(△)③ McDaniel ら 2004 の遅れ 5/15/40 秒・割り込み 10 対 20 秒・「遅れの長さは効かない」(○)④ Altmann & Trafton 2007 の「最初の 10 回の反応(15 秒ほど)」と「13,000 回を超える割り込み」(○)⑤ Rajagopalan & Lall 1999 の 6 変数・30 年・Salt Lake City・前の日に条件を付けた k 近傍(○)。

## 親の一次確認(第347・2026-11-16・親)

確かめ方: 公開の索引の要旨(OpenAlex の `abstract_inverted_index`・Europe PMC の REST)を WebFetch で読んだ。WebFetch は頁を小さなモデルに通すので、短い逐語の断片と、問いへの答えで突き合わせた。発行元の頁・著者の頁・写しは開いていない。コードは本体の頭 `17ad6ebc` で読んだ。

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| Rajagopalan & Lall 1999: 6 変数・30 年・Salt Lake City・前の日の組に条件を付けた k 近傍・「定番」の語は要旨に無い(§2-2) | OpenAlex の要旨(DOI 10.1029/1999WR900028) | 合う。6 変数(日射・最高気温・最低気温・平均露点・平均風速・降水)・「30 years of daily weather data at Salt Lake City, Utah」・「by conditioning on the vector of the same variables (feature vector) on the preceding day」。「standard」の語は無い。巻号頁 35(10): 3089–3101 |
| W13 の層の抽選は前の日に条件を付けていない(§2-2) | `src/shibuya/world/laws/environment.py` の `sample_calendar_day` を読んだ | 合う。乱数の鍵は `calendar|季節|平日/土休|日番号` で、前の日に引いた日や天気を読まない |
| Böcker ら 2013: 要旨は歩きと自転車を重点に挙げ、結論は「不完全で断片的」(§2-1) | OpenAlex の要旨(DOI 10.1080/01441647.2012.747114) | 合う。「…travel behaviours—particularly walking and cycling—have become very important」「the existing studies present an incomplete and fragmented picture of the impact of weather on travel behaviour」 |
| McDaniel ら 2004: 遅れ 5・15・40 秒は効かない・割り込みは成績を下げる・割り込みの長さ 10 対 20 秒は効かない・実験 2 で外の覚え書きが差を消した(§3-3) | OpenAlex の要旨(DOI 10.1002/acp.1002) | 合う。「Delay length did not significantly affect performance」「The length of the interruptions (10 vs. 20 s) did not significantly affect performance」「these effects could be overcome with a simple external mnemonic」 |
| Altmann & Trafton 2007: 13,000 回を超える割り込み・最初の 10 回の反応(15 秒ほど)で反応の時間が下がる(§3-3) | Europe PMC の要旨(DOI 10.3758/BF03193094) | 合う。「over 13,000 interruptions」・最初の 10 回の反応・約 15 秒。14(6): 1079–1084 |
| Ghibellini & Meier 2025: 要旨は「思い出しの有利は無い・戻る傾向は一般的」。統合した値(約 67%・0.99・37 研究)は要旨に無い(§3-1) | OpenAlex の要旨(DOI 10.1057/s41599-025-05000-w) | 合う。「We found no memory advantage for unfinished tasks but found a general tendency to resume tasks.」数値は要旨に無い=67%・0.99・37 研究は △(ブログの二次)のまま。**この 3 つの値は決定の根拠に使わない** |
| O'Conaill & Frohlich 1995 の 41%・55.2%・125 件(§3-1) | 確かめていない(発行元 ACM の頁は 403・公開の索引に要旨が無い) | △ のまま。**決定の根拠に使わない**(戻らない人が居ることは R-136 の Mark ら 2005 ◎ で足りる) |
| Altmann & Trafton 2004 の再開の遅れ 3.8 秒・1.9 秒・8 秒の手がかり(§2-4) | R-136 の親の一次確認(済)を引く。読み直していない | R-136 のまま(◎) |
| Kurby & Zacks 2008・Altmann & Trafton 2002・Schegloff & Sacks 1973 の要旨の突き合わせ(§2-3〜§2-5) | 親は読み直していない(研究役の ○ のまま) | 研究役の読みのまま。Schegloff & Sacks 1973 の「取り決めを含むことが多い」は確かめられない |

**取り方の確かめ(CLAUDE.md §5・§7)**: 断られた頁(§5-1 の U1〜U10)を、別の名乗り・経路・ミラー・キャッシュ・著者の頁・第三者の写しで読んだ記述は無い。断られた頁の中身は本文に入っていない(§2 は索引の要旨と、発行元 eScholarship の予稿 [S6] だけで書かれている)。

- §5-2 の 1(Kurby & Zacks 2008 の PMC の著者稿を、発行元 cell.com の robots を確かめる前に読んだ): **11-21 の決定(記録 2-87)で可(公的な保管庫の著者稿)**(第348・11-20/§1 の 2)。本文で読んだ中身は、今回も答申に入れていない(§2-3 は Europe PMC の要旨の逐語だけ=親が確かめた)。読んだ版は PMC の著者稿(PMC2263140・NIH の公開の著者稿。雑誌の版と数字が違うことがある)。
- §5-2 の 2(Dodhia & Dismukes の 2003 年の発表を NASA の頁に読みにいき、道具が何も返さなかった): 断られたのではなく、発行元が断った論文の写しでもない(別の作品・著者の所属先の公的機関の頁)。線の内と判断する。3 回目を試さなかったのは決まりのとおり。値は △ のまま。

**記録の直しの候補(親から claude.ai へ)**: 記録 2-55 の「特に歩きと自転車に効く」(総説の結論は「不完全で断片的」)・「定番」(要旨に無い)・「W13 の設計はこれに沿う」(前の日への条件づけが無い)、記録 2-59 の「手がかりがあるときだけ再開される」(実験が測ったのは再開の遅れの秒数)・「先の取り決めを含むことが多い」(頻度は確かめられない)・「会話の終わり=出来事の区切り」(記録の当てはめ)。PENDING の「記録の直しの候補」の行に足す。

**等級**: B(5 本とも原典の本文は読めず、要旨まで。細部の材料は ○ 20・△ 8。空欄 6 つは §4)。
