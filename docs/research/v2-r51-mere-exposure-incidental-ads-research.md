# R-51 答申: 単純接触効果と広告への偶発的な接触 — 思い出せなくても選択肢に入るか(M17「潜在的な親しみ」の乗数の錨)
<!-- hdr:v1 -->
- **分野**: 認知科学(記憶・習慣) #12 / 行動経済学・マーケティング科学 #16 / 知覚心理学 #5 / 人間移動科学 #3 / 小売科学・商業立地論 #17 | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(原典本文 13・業界ページ 1・抄録 18・二次/要約 7・空欄 = §7)・**親検収 済(第283・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: [記憶アジェンダ M17](../design/v2-memory-agenda.md)「潜在的な親しみ」(体×もの=店・場所・人・道ごとに ACT-R の基底活性 A=ln Σ(Δt+1)^−0.5 を持ち、τ を超えたものは文章化して LLM へ=意識、数値のまま System 1/1.5 へ=潜在)の**乗数の錨**を並べる。最初の接続先は店選び(看板の p_see 通過と訪問 → 満足化の走査順を前へ=案 α / 候補に入りやすく=案 β、[草案 v1 §2-2](../design/v2-hunger-choice-attention-draft.md) の L8)。設計の決定はしない(§6 は候補と区分だけ)。
> 規律: 子サブ未起動・Web は読むだけ(PDF は curl → 標準出力 → pymupdf・保存なし)・ダウンロードなし・コミットなし・台帳未編集・本書の新規作成のみ。

---

> **親検収(第283・2026-09-28・親=Fable 5.1)**
> - 一次照合した引用(親が同じ URL を curl → 標準出力 → 文字列照合・保存なし): ✓ Zajonc & Rajecki 1969「affective ratings increase with the logarithm of frequency of exposure」「F = 15.61」/ ✓ Ferraro ら 2009「17.1% of the participants selected Dasani, as compared to 21.6% in the four-exposure and 40.0% in the 12-exposure」/ ✓ Seamon ら 1983 表 1「Immediate 60.5 55.5」「1 Week 65.0 50.8」「undiminished over a delay of 1 week」/ ✓ Schooler & Hertwig 2005「doubles as a decision criterion for recognition」「Records are searched in order of their activation」/ ✓ Barbosa ら 2015「κ ≈64.3±1.3」「≈23.6±0.2」「both mechanisms must be present」。
> - 訂正: なし。Ferraro の加速形(4 回で効かず 12 回で効く)は小標本=形の錨にしない(§8-5 に同意)。
> - 写し検査・訂正の伝播検査・循環参照検査・フロア併記検査: 設計への写し先=[記憶アジェンダ v1 M17](../design/v2-memory-agenda.md)(形の比較)。**循環参照の発見(§8-1)は正しい**: 広告答申 4-C (ii)「ε は台帳(AD4)で較正」は 4-F の AD4=holdout と矛盾 → 親が広告答申の末尾に訂正の伝播を追記(AD4 は照合専用・ε/β は宣言+感度腕)。人の親しみの定数は台帳 B1(holdout)に合わせない(§8-2 に同意)。フロア併記=実験室の効果量(Bornstein r≈.26 △・Ferraro OR 3.23)は野外の上限に使えない、を §1 の読みで併記済み。
> - 規律上の判定(取得経路など): 子サブなし・保存なし=規律内。

## 要約

1. **形は「回数の対数」**: 古典の定式は「affective ratings increase with the logarithm of frequency of exposure」(Zajonc & Rajecki 1969 ◎・新聞広告の野外実験でも同じ)。ACT-R の A は等間隔の接触なら ln n にほぼ比例して増える(傾き ≈0.5 [サブ計算] §4-4)ので、**A を線形に乗数へ写すことは対数則と同じ形**。ただし回数が多いと**逆 U**(Montoya ら 2017 ○: 268 曲線・81 論文で正の傾き+負の二次項)、広告反復のメタ分析では態度の頂点が**約 10 回**(Schmidt & Eisend 2015 ○)。
2. **効果量**: Bornstein 1989 の全体 r≈.26 は二次のみ(△)。意識下の提示ほど効果が大きい(Bornstein & D'Agostino 1992 ○: 5 ms > 500 ms)。**実験室の効果量は街の看板に移せない**(既存 [広告答申](v2-ad-information-research.md) 2-5: 1 接触あたり 10⁻⁴〜10⁻³・スイス DiD 相対 3%)。
3. **「思い出せないが選ぶ」の直接証拠**: Ferraro ら 2009 ◎(ブランドに気づかなかった 108 人で、写真 0/4/12 枚の接触 → 選択 **17.1/21.6/40.0%**)。Seamon ら 1983 ◎(再認はチャンス水準のまま、好みで選ぶと **60.5〜65.0%**・1 週間後も減らない)。Shapiro ら 1997 ○・Yoo 2008 ○(明示記憶なしで**考慮集合に入る**)。
4. **効く段は「候補に入る」**: Coates ら 2004 ○「increase the likelihood that they will enter the consumers' consideration set. However, the advantage does not appear to extend to choice itself」。Lee 2002 ○: stimulus-based の選択は知覚的な潜在記憶、memory-based の選択は概念的な潜在記憶で有利。→ 形の上では M17 の**案 α(走査順・候補入り)側**に錨が多い。
5. **意識と潜在の境界の先行がある**: Schooler & Hertwig 2005 ◎ が ACT-R で「検索閾値 τ と再認の判定基準を分ける」形を書いている(再認されない項目も「differ in gradation of strength」)。= **1 本の A に 2 つの閾値**。同論文は「Records are searched in order of their activation」=**活性順の走査**も書く。
6. **活性→選択確率の写像**: ACT-R の想起確率 P(i)=e^{A_i/s}/(e^{τ/s}+Σ_k e^{A_k/s})・s≈0.25(Taatgen ら ◎)/IBL の softmax 温度 τ=σ√2・既定 σ=0.25・d=0.5(SpeedyIBL ◎)/推薦系で ACT-R 基底活性(d=0.5)→二次式(逆 U)→シグモイド(Ex2Vec ◎)。
7. **潜在は意識より長持ち**: Seamon ◎(1 週間で好みは不変・再認は 55.5→50.8%)/Tunney & Bezzina ○(14 日で recollection が落ち familiarity が残る)/Shapiro & Krishnan △。飽き(satiation)は 1 週間の空白で消える(Stang 1975 ◎)。広告の反復効果は時間とともに減る(Schmidt & Eisend ○)。
8. **看板と来店**: 位置情報で接触者と来店を結ぶ業界計測はある(jeki: 接触日数が増えるほど訪問率が上がる・数値なし ○[業界])が、**記憶を測らない**。**「看板を見た記憶が無いのに来店が増えた」を同じ人で切り分けた実証は学術・業界とも見つからなかった(空欄)**。
9. **人・場所・道**: 人=Moreland & Beach 1992 ○(話さずに同席 0/5/10/15 回で好意と類似感が上がり、familiarity の自覚は弱い)。場所=preferential return Π_i ∝ f_i(**訪問回数に線形**)と新近性の**両方**が要る(Barbosa ら 2015 ◎)。道=親しい経路を選ぶ(Tong & Bode 2022 ◎・定性)が、歩行者の効果量の一次は空欄。
10. **K の目安**: 活動空間の容量 ≈25(既存 [d68](v2-d68-behavioral-diversity-research.md) §1-4)。戻り先の頻度順位分布の打ち切り κ=**23.6**(携帯基地局)/**64.3**(Brightkite の場所チェックイン)(Barbosa ◎)。K=64 は後者と同じ桁。**看板で知っているだけの店の数の錨は無い**(宣言)。

## §0 等級と調べ方・出典表

- 等級: **◎** = 原典(本文または公式抄録)を生テキストで文字列照合し、親も同じ URL で再取得できる / **○** = 原典実読だが抄録のみ・第三者掲載 / **△** = 二次経由(他論文の記述・検索要約) / **×** = 未確認。**[要約]** = WebFetch の要約モデル経由(生テキスト照合なし)。[業界] = 査読なし。[サブ計算] = 本書での算術。
- 取り方: 抄録は PubMed E-utilities・Crossref API・EconPapers・Europe PMC の生テキスト。PDF は Springer/arXiv/著者サイト/J-STAGE/MPG.PuRe を curl → 標準出力 → pymupdf(保存なし)。OUP・APA・T&F・SSRN・ScienceDirect は 403 が多く、そこは抄録止まり。
- 既存答申で扱ったものは再確認せず参照: ACT-R d=0.5・Anderson & Schooler 1991・Nedungadi・Lynch & Srull([R-49](v2-r49-wom-memory-store-choice-research.md) §4・§5)/Stoller DiD・Lumen VAC・1 接触 10⁻⁴〜10⁻³・注意ゲート・4-C (ii)「親近性スカラー +ε」([広告答申](v2-ad-information-research.md))/Hyman・Janiszewski 1998・Pieters & Wedel [要約]([R-47](v2-r47-classical-choice-attention-research.md) §5)/Alessandretti 容量 ≈25([d68](v2-d68-behavioral-diversity-research.md) §1-4)/Festinger(台帳 B1=holdout)。

| # | 書誌 | URL | 等級 | 取れた範囲 |
|---|---|---|---|---|
| 1 | Zajonc 1968, JPSP 9(2, Pt.2):1–27 | https://doi.org/10.1037/h0025848 | △ | 原典未読(#2 の記述経由) |
| 2 | Zajonc & Rajecki 1969, Psychon Sci 17(4):216–217 | https://doi.org/10.3758/BF03329178 | ◎ | Springer PDF 全文 |
| 3 | Kunst-Wilson & Zajonc 1980, Science 207:557–558 | https://doi.org/10.1126/science.7352271 | ○ | PubMed 抄録 |
| 4 | Bornstein 1989, Psych Bull 106(2):265–289 | https://doi.org/10.1037/0033-2909.106.2.265 | △ | 原典 403・#5/#6 と検索要約経由 |
| 5 | Bornstein & D'Agostino 1992, JPSP 63(4):545–552 | https://doi.org/10.1037/0022-3514.63.4.545 | ○ | PubMed 抄録 |
| 6 | Grybinas, Kantner & Dobbins 2019, Mem Cogn 47(7):1314–1327 | https://doi.org/10.3758/s13421-019-00935-3 | ◎ | 本文(Bornstein の二次記述) |
| 7 | Montoya, Horton, Vevea, Citkowicz & Lauber 2017, Psych Bull 143(5):459–498 | https://doi.org/10.1037/bul0000085 | ○ | PubMed 抄録(係数は △=ブログ) |
| 8 | Seamon, Brody & Kauff 1983, Bull Psychon Soc 21(3):187–189 | https://doi.org/10.3758/BF03334682 | ◎ | Springer PDF 全文(表 1) |
| 9 | Stang 1975, Bull Psychon Soc 6(3):273–275 | https://doi.org/10.3758/BF03336659 | ◎ | Springer PDF 全文 |
| 10 | Reber, Winkielman & Schwarz 1998, Psych Sci 9(1):45–48 | https://doi.org/10.1111/1467-9280.00008 | ○ | Crossref 抄録 |
| 11 | Reber, Schwarz & Winkielman 2004, PSPR 8(4):364–382 | https://doi.org/10.1207/s15327957pspr0804_3 | ○ | Crossref 抄録 |
| 12 | Schmidt & Eisend 2015, J Advertising 44(4):415–428 | https://doi.org/10.1080/00913367.2015.1018460 | ○ | ウィーン大ポータルの抄録(37 研究は △) |
| 13 | Shapiro, MacInnis & Heckler 1997, JCR 24(1):94–104 | https://doi.org/10.1086/209496 | ○ | EconPapers 抄録(本文の USC 版は 404) |
| 14 | Shapiro 1999, JCR 26(1):16–36 | https://doi.org/10.1086/209548 | △ | OUP 抄録 [要約] |
| 15 | Janiszewski 1993, JCR 20(3):376–392 | https://doi.org/10.1086/209356 | △ | OUP 抄録 [要約] |
| 16 | Lee 2002, JMR 39(4):440–454 | https://doi.org/10.1509/jmkr.39.4.440.19119 | ○ | Crossref 抄録 |
| 17 | Yoo 2008, J Interactive Mktg 22(2):2–18 | https://doi.org/10.1002/dir.20110 | ○ | Crossref 抄録 |
| 18 | Fang, Singh & Ahluwalia 2007, JCR 34(1):97–103 | https://doi.org/10.1086/513050 | ○ | EconPapers 抄録 |
| 19 | Ferraro, Bettman & Chartrand 2009, JCR 35(5):729–741 | https://people.duke.edu/~jrb12/bio/Jim/ferraro%20bettman%20chartrand.pdf | ◎ | 著者サイト PDF 全文(研究 1) |
| 20 | Coates, Butler & Berry 2004, Appl Cogn Psychol 18(9):1195–1211 | https://doi.org/10.1002/acp.1044 | ○ | Crossref 抄録 |
| 21 | Oeusoonthornwattana & Shanks 2010, JDM 5(4):310–325 | https://doi.org/10.1017/S1930297500003545 | ○ | Crossref 抄録 |
| 22 | Shapiro & Krishnan 2001, J Advertising 30(3):1–13 | https://doi.org/10.1080/00913367.2001.10673641 | △ | 検索要約 |
| 23 | Singh, Rothschild & Churchill 1988, JMR 25(1):72–80 | https://doi.org/10.1177/002224378802500107 | ○ | Crossref 抄録 |
| 24 | Northup & Mulligan 2013, Appl Cogn Psychol 27(1):127–136 | https://doi.org/10.1002/acp.2892 | ○ | Crossref 抄録 |
| 25 | Wedel & Pieters 2000, Mktg Sci 19(4):297–312 | https://doi.org/10.1287/mksc.19.4.297.11794 | ○ | Crossref 抄録(全文) |
| 26 | 安藤・吉原 1997「交通広告効果指標の考察」消費者行動研究 5(1):125–137 | https://www.jstage.jst.go.jp/article/acs1993/5/1/5_1_125/_pdf/-char/ja | ◎ | J-STAGE PDF 全文 |
| 27 | jeki「Universal OOH Plus」コラム 0042 | https://universal-ooh.jeki.co.jp/column/0042/ | ○[業界] | ページ本文 |
| 28 | Donthu, Cherian & Bhargava 1993, JAR 33(3):64–72 | https://doi.org/10.1080/00218499.1993.12466894 | △ | 検索要約 |
| 29 | Lee, Bart & Pauwels(SSRN 5728803・2026 版) | https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5728803 | △ | 403・検索要約 |
| 30 | Taatgen, Lebiere & Anderson「Modeling paradigms in ACT-R」(Sun 編 2006 所収・書誌は二次) | https://www.ai.rug.nl/~niels/publications/taatgenLebiereAnderson.pdf | ◎ | 著者版 PDF |
| 31 | Nguyen, Phan & Gonzalez「SpeedyIBL」arXiv:2111.10268 | https://arxiv.org/abs/2111.10268 | ◎ | arXiv PDF |
| 32 | Schooler & Hertwig 2005, Psych Rev 112(3):610–628 | https://doi.org/10.1037/0033-295X.112.3.610 | ◎ | MPG.PuRe PDF 全文(pure.mpg.de) |
| 33 | Hertwig, Herzog, Schooler & Reimer 2008, JEP:LMC 34(5):1191–1206 | https://doi.org/10.1037/a0013025 | ○ | PubMed 抄録 |
| 34 | Sguerra, Tran & Hennequin 2023「Ex2Vec」RecSys '23, arXiv:2311.10635 | https://arxiv.org/abs/2311.10635 | ◎ | arXiv PDF |
| 35 | Tunney & Bezzina 2007, Acta Psychol 125(1):37–50 | https://doi.org/10.1016/j.actpsy.2006.06.002 | ○ | PubMed 抄録(Yonelinas 2002 は同抄録経由=△) |
| 36 | Moreland & Beach 1992, JESP 28(3):255–276 | https://doi.org/10.1016/0022-1031(92)90055-O | ○ | 第三者掲載の抄録(数値は △) |
| 37 | Barbosa, de Lima-Neto, Evsukoff & Menezes 2015, EPJ Data Sci 4:21 | https://doi.org/10.1140/epjds/s13688-015-0059-8 | ◎ | 本文(オープンアクセス) |
| 38 | Tong & Bode 2022, J R Soc Interface 19:20220061 | https://doi.org/10.1098/rsif.2022.0061 | ◎ | Europe PMC 全文(PMC8984324) |
| 39 | Zhu & Levinson 2015, PLoS ONE 10(8):e0134322 | https://doi.org/10.1371/journal.pone.0134322 | ◎ | Europe PMC 全文 |

## §1 Q1 単純接触効果 — 効果量と条件

| 出典 | 設計 | 効果(逐語・数値) | 条件・注意 | 等級 |
|---|---|---|---|---|
| Zajonc 1968(#1) | トルコ語風の語・漢字風の図形・男性の顔写真を 0/1/2/5/10/25 回 | 「affective ratings increase with the logarithm of frequency of exposure」(#2 の要約) | 実験室・全提示後に評定 | △ |
| Zajonc & Rajecki 1969(#2) | 大学新聞 2 紙に 25 日間、トルコ語 5 語を 1/2/5/10/25 回掲載・1,141 人 | 見たと答えた人(N=292)で頻度の効果 F=15.61(p<.001)・見た人 3.35 vs 見ていない人 3.06(7 段階・F=35.75)・「fairly consistent logarithmic relationship」(OCR で Iogarithmic) | **野外の広告**。頻度の効果は「見たと答えた人」で出したもの=意識下の証拠ではない | ◎ |
| Kunst-Wilson & Zajonc 1980(#3) | 劣化させた提示 | 「these preferences can develop even when the exposures are so degraded that recognition is precluded」 | 数値は抄録に無い | ○ |
| Bornstein 1989(#4・#6) | 134 研究・208 対比(#6 ◎) | 全体 r≈.26 [△]・「the average effect size (across studies) for subliminally presented stimuli was larger than the average effect size in the meta-analysis as a whole」(#6 ◎)・10〜20 回で頭打ち [△]・再認あり 45/55・なし 25/75(BESD・ブログ △) | 刺激の種類・複雑さ・提示時間・再認・年齢・遅延・最大提示回数が効く(抄録の検索要約 △) | △ |
| Bornstein & D'Agostino 1992(#5) | 5 ms vs 500 ms・1〜20 回 | 「5-ms stimuli produced significantly larger mere exposure effects than did 500-ms stimuli」 | 追試の失敗あり(Fox & Burns 1993=検索要約 △) | ○ |
| Montoya ら 2017(#7) | 268 曲線・81 論文 | 「positive slope and negative quadratic effect consistent with an inverted-U shaped curve」・好意の平均曲線 y=.66131+.00191x−.000026x²(頂点 36.7 回 [サブ計算]・ブログは 35.73 回=食い違い) | 逆 U は「(a) all visual, but not auditory stimuli; (b) exposure durations shorter than 10 s and longer than 1 min; … (d) ratings that were taken after all stimuli were presented」 | ○(係数 △) |
| Reber ら 1998(#10)・2004(#11) | 流暢性を反復以外で操作(プライム一致・図地コントラスト・提示時間) | 「perceptual fluency increases liking」/美的快は処理の流暢さの関数 | 機構の説明(反復→流暢→好意の 2 段) | ○ |
| Schmidt & Eisend 2015(#12) | 広告反復のメタ分析(37 研究=態度 19・再生 18 は △) | 「maximum attitude is reached at approximately ten exposures, while recall increases linearly and does not level off before the eighth exposure」 | 「Low involvement and spaced exposures enhance repetition effects on attitude」「Repetition effects decay over time for both attitude toward the brand and recall」 | ○ |
| Stang 1975(#9) | 女性 10 人・香辛料 15 種を 10 回ずつ、1 週間後に 4 回 | 快さは試行とともに下がり、1 週間の空白で回復(試行 1 と 11 に差なし)・「some satiation effects dissipate with time while others are cumulative」 | 味覚・集中接触=**飽き**の側 | ◎ |

→ **読み**: 形は「対数で上がり、多いと頭打ち/下がる」。頂点の回数は約 10(広告の態度)〜約 36(実験刺激の好意・△)と散る。意識下・短時間・遅延後の評定で効果が大きい。**効果量は研究間で大きく散る**(Bornstein の BESD 45/55〜25/75 は △)=フロア併記: 実験室の効果を野外の上限に使うこと自体が不可。

## §2 Q2 偶発的な接触は考慮集合・選択を動かすか(思い出せないが選ぶ)

| 出典 | 課題 | 結果(逐語・数値) | 明示記憶 | 効いた段 | 等級 |
|---|---|---|---|---|---|
| Shapiro, MacInnis & Heckler 1997(#13) | 注意を別課題に向けたまま広告に接触 | 「the incidental exposure effect is fairly robust, occurring across a variety of factors (when the consideration set formation context was memory or stimulus based, when the buying situation was familiar or unfamiliar, and across two different product classes)」 | 「despite subjects' lack of explicit memory for the ads」 | 考慮集合 | ○(率は本文未取得) |
| Shapiro 1999(#14) | 同上・4 研究 | 概念的/知覚的流暢性で stimulus-based の考慮集合に入りやすい・「even when subjects were explicitly trying to avoid choosing products that were depicted in the ads」 | 無意識 | 考慮集合 | △[要約] |
| Janiszewski 1993(#15) | 意図的処理のない接触 | 態度が上がる・「preattentive processes」。再認率 14.3〜53.3%(#19 本文の引用) | 想起できなくても | 態度 | △[要約] |
| Lee 2002(#16) | 潜在記憶 vs 明示記憶 | 「memory-based choice benefits from advertising that enhances conceptually driven implicit memory whereas stimulus-based choice benefits from advertising that enhances perceptually driven implicit memory」・「implicit memory measures may be more useful indicators of advertising effectiveness than explicit memory measures」 | 潜在と明示は別構成概念 | 選択 | ○(効果量は本文未取得) |
| Yoo 2008(#17) | Web 広告・注意あり/なし | 「those who unconsciously processed Web ads did not remember seeing the ad explicitly, but they were more likely to include the advertised brand in the consideration set than those who had no exposure」 | なし | 考慮集合・態度 | ○ |
| Fang ら 2007(#18) | バナー広告・偶発接触 | 「the classical mere exposure effect is replicated in the context of banner advertising」・PF/M を否定し、流暢性→自発的な感情が仲立ち | — | 評価 | ○ |
| **Ferraro ら 2009**(#19) | 126 人・20 枚の写真のうち 0/4/12 枚に Dasani・「focus on the facial expressions」と教示・4 銘柄から 1 本もらう | 気づかなかった 108 人(36/37/35)で選択 **17.1/21.6/40.0%**・線形傾向 χ²(1)=5.03, p=.02・好意は差なし(5.7/5.1/6.2)・好意と選択の相関 r=.40/.57/.75。[サブ計算] オッズ比 4 回 1.34・12 回 3.23 | 再生で気づいた人 12 回 27.1%・4 回 11.9%(再認では 27.1/7.1%)を除外 | **選択** | ◎ |
| Coates ら 2004(#20) | 既知ブランド名のプライミング・3 実験(実際に品物を受け取る条件あり) | 「priming had an influence on brand consideration but not on final or preferred choice」 | — | 考慮のみ | ○ |
| Oeusoonthornwattana & Shanks 2010(#21) | 自然な消費者選択 | 「although recognition was a powerful driver of preferences, it was used in a compensatory rather than a non-compensatory way」 | 再認あり | 選好(補償型) | ○ |
| **Seamon ら 1983**(#8) | 64 人・10 図形を 5 ms×5 回・直後/1 日/1 週(20/20/24 人)・強制選択 | 好みで選ぶ **60.5/60.0/65.0%**・再認で選ぶ 55.5/52.5/50.8%(チャンス 50%・好みは全群 p<.01・再認は全群 p>.05)・「undiminished over a delay of 1 week」 | 再認できない | 好み | ◎ |
| Northup & Mulligan 2013(#24) | 概念的潜在テスト | 「aware participants did show significantly more priming than those who were unaware」 | 気づきの混入 | — | ○ |

→ **読み**: (i) 明示記憶なしで**考慮集合に入る**は複数で頑健(Shapiro 1997・Yoo・Coates)。(ii) **選ぶ**まで効いた直接証拠は Ferraro(12 回で 17→40%)。ただし 4 回ではほぼ効かず 12 回で効く**加速形**で、対数則(凹)と向きが逆(各群 35〜37 人の小標本)。(iii) Coates は「選択には及ばない」=効く段は**候補入り**。(iv) 全部が実験室(数分〜1 週間・強制選択)で、街頭の来店の効果量ではない。

## §3 Q3 屋外広告・看板の露出と記憶・選択

- **既存(広告答申・等級 C)**: 採用はスイス DiD(**AD1=holdout**)と OOH 計測構造だけ。Lumen/AM4DOOH の VAC 14〜79% が p_see の先験分布(expedient)。1 接触の行動変化 10⁻⁴〜10⁻³。OAAA の想起率(88%・79%)は自己申告で不採用。**4-C (ii)「その店に対する親近性スカラー +ε」は M17 の潜在経路そのもの**(ただし §8-1 の矛盾あり)。
- **Wedel & Pieters 2000(#25 ○)**: 88 人・雑誌 65 広告の視線計測。「It is assumed that the number of fixations, not their duration, is related to the amount of information」「The accumulation of information across multiple fixations … is assumed to be additive」「Accurate memory is assumed to occur when the accumulated information exceeds a threshold that varies randomly across ads and consumers in a binary probit-type of model component」。ブランドと絵の注視は記憶を上げ文字は上げない・後に見た広告ほど再認がよい(新近性)。→ **接触を回数で加算し、確率的な閾値で記憶になる**形の直接の先行(ただし印刷広告・間接記憶課題)。
- **jeki 1997(#26 ◎)**: 「テレビCMはGRPと認知率との間[OCR は「問」]に、一般的に図1のような指数関数関係があると考えられている。交通広告(車内ポスター)においても図2のような関係があると思われるが、明確な関係式等は今後研究を進めなければならない」=**飽和形は業界の前提だが交通広告の関係式は無い**。
- **jeki Universal OOH(#27 ○[業界])**: 位置情報で接触者/非接触者を分けて来店を計測。「接触日数が、１日、２日、３日…と増えるに連れて「訪問率がアップ」」(**数値なし**)。ブランドリフト 認知 +9.0pt・興味 +8.9pt・利用意向 +9.4pt、10 週以上の出稿で認知 +12.0pt(5 週の他社の「4倍」)。**非無作為(接触者=その路線の利用者)・記憶を測らない**。
- **Donthu ら 1993(#28 △)**: 高速道路の 10 枚の看板・通勤者 142 人。位置・色・語数・関与・広告への態度が再生を左右(再生率の数値は未取得)。
- **Lee, Bart & Pauwels(#29 △)**: DOOH の表示ローテーションを準実験に使い、接触がウェブ訪問の確率を上げ時期を早める・閾値を超えると限界効果が逓減(数値未取得)。
- **空欄**: 「看板を見た記憶が無くても来店が増える」を、**同じ人で記憶(再生/再認)と来店を測って**切り分けた実証は見つからなかった。業界の来店計測は記憶を測らず、実験室の研究は来店を測らない。

## §4 Q4 減衰と累積の形・活性から選択確率への写像

### 4-1 累積の形

| 形 | 先行 | 値 | 等級 |
|---|---|---|---|
| 回数の対数 | Zajonc & Rajecki(#2) | 野外と実験室で同じ | ◎ |
| 逆 U(二次) | Montoya(#7)・Ex2Vec(#34: I=α d+β d²+γ+b → シグモイド) | 頂点 ≈36 回 [△] | ○/◎ |
| 頭打ち(広告) | Schmidt & Eisend(#12) | 態度 ≈10 回・再生は 8 回まで直線 | ○ |
| 指数関数的な飽和(GRP→認知率) | jeki 1997(#26) | TV の前提・交通は未確定 | ◎ |
| べき減衰の和(ACT-R) | Taatgen ら(#30)「Activation represents the probability (actually, the log odds) that a chunk is needed」 | d=0.5「has emerged as the default value」 | ◎ |
| 加算+確率的な閾値 | Wedel & Pieters(#25) | 注視回数の加算・probit | ○ |
| 訪問回数に線形(場所) | Barbosa(#37)が引く Song の preferential return「Π_i ∝ f_i」 | — | ◎ |

### 4-2 持続(既存 R-49 §4 の減衰表=GA 0.995/時・CitySim λ 0.03/日・ACT-R d=0.5・Trusov 21 日・Leone 6〜9 か月 は再掲しない)

- **潜在は長持ち**: Seamon(#8 ◎)=好みの選択は直後 60.5%→1 週 65.0%(差は有意でない)・再認は 55.5%→50.8%。Tunney & Bezzina(#35 ○)=「recollection contributed to recognition decisions but declined over the 14-day period leaving familiarity as the only basis for recognition」(人工文法)。Shapiro & Krishnan(#22 △)=遅延と注意分割で明示記憶は落ち、潜在記憶は保たれる。
- **明示の再認も減る**: Singh ら(#23 ○)「recognition scores are not indiscriminately high … and … they do decline with time」「more sensitive and more discriminating than, and covary with, unaided recall scores」。
- **飽きは戻る**: Stang(#9 ◎)=1 週間の空白で快さが初回の水準に戻る。Schmidt & Eisend(#12)=分散接触のほうが態度への反復効果が大きい。
- → 1 本の A を 2 つの閾値で読むと、**A が下がるにつれ先に τ_high(意識)を割り、τ_low(潜在)はまだ超えている期間ができる**=「明示が先に消え潜在が残る」がそのまま出る [推測]。

### 4-3 活性 → 選択確率(先行の式)

- **ACT-R 想起確率(#30 ◎)**: 「P(i) = e^{A_i/s} / (e^{τ/s} + Σ_k e^{A_k/s})」(抽出は崩れ字・式の形は本文)。「s controls the noise in the activation levels and is typically set at about 0.25」。τ は外側の選択肢(想起失敗)として分母に入る。
- **IBL(#31 ◎)**: 「τ = σ √ 2」の Boltzmann/softmax・「we used the decay d = 0.5 and noise σ = 0.25」。選択肢の価値は「the sum of all past experienced outcomes weighted by their probability of retrieval」(blending)。
- **Schooler & Hertwig(#32 ◎)**: 「Records are searched in order of their activation until either a record is found that satisfies the current condition or the activation of the next record to be considered is so low that it is not worth considering」=**活性順の走査+打ち切り**(満足化と同型)。閾値の二役:「the retrieval criterion, τ, doubles as a decision criterion for recognition」「if the retrieval criterion is assumed to be lower than the recognition decision criterion, then the fluency rule will apply to comparisons in which both objects exceed the modest retrieval criterion but remain unrecognized」。環境の錨: 新聞の言及回数と人口 .82・言及回数と再認率 .66。Δt は**日**単位(Seattle: ln(710^−.5+430^−.5+219^−.5)=−1.87)・当てはめた τ=1.44。
- **Hertwig ら 2008(#33 ○)**: 「retrieval fluency can be a proxy for real-world quantities」=想起の速さ(活性)で選ぶ流暢性ヒューリスティック。
- **Ex2Vec(#34 ◎)**: 基底活性「B_i(t) = ln Σ_j 1_{t>t_j} (t − t_j)^−d」・「Following ACT-R's community we set d = 0.5」・学習では (t − t_j + c)^−d(**v2 の (Δt+1) と同じ形**)で距離を変調 → 二次式 → シグモイドで再生確率。**ACT-R の A を選択確率に写した実装の直接の先行**(音楽の再聴・Deezer)。
- **LLM 社会シミュ**: [R-49](v2-r49-wom-memory-store-choice-research.md) §6 の 6 系(GA・Lyfe・RecAgent・Agent4Rec・CitySim・AgentSociety)に「LLM に見せない数値の親しみを選択器に掛ける」形は読んだ範囲で無い(CitySim は会話後に相手への familiarity を数値で持つが用途は未確認)。

### 4-4 v2 の A の目安 [サブ計算](Δt=分・d=0.5)

- 1 回だけ: 1 時間前 −2.06 / 1 日前 −3.64 / 7 日前 −4.61 / 30 日前 −5.34。
- 毎日 1 回を n 日(最後から 1 日後に評価): n=1 −3.64・2 −3.10・5 −2.46・10 −2.02・25 −1.48・60 −0.99。n が 6 倍で ΔA≈1.0=**傾き ≈0.5×ln n**(Zajonc の対数則と同じ形)。
- **単位の注意**: Δt を分で測ると日で測るより A が 0.5×ln 1440 ≈ **3.64 低い**。文献の τ(Schooler & Hertwig の日単位 1.44・AMBR 章の −1.0 [△])は**そのまま移せない**。

## §5 Q5 人・場所・道への一般化

- **人**: Moreland & Beach 1992(#36 ○): 見た目の似た女性 4 人が講義に 0/5/10/15 回出席し誰とも話さない・学期末に 130 人がスライドで評定。「Mere exposure had weak effects on familiarity, but strong effects on attraction and similarity」「the effects of exposure on familiarity and similarity were mediated by its effects on atrraction」(掲載ページの綴りのまま)。魅力 3.62(0 回)→4.38(15 回)は △。→ **同席だけで効き、しかも「見覚え」の自覚は弱い**=潜在経路の人版。Zajonc 1968 の顔写真(#2 の記述)。**台帳 B1(Festinger 隣室 41%)は holdout**=人の親しみの定数を B1 に合わせない。
- **場所**: Barbosa ら 2015(#37 ◎): preferential return「Π_i ∝ f_i」(Song)・新近性の戻り「p(i) ∝ K_s(l_i)^−η」・混合 α で「when α = 0, the heavy tail of the visitation frequency disappears while for α = 1 the power law of the recency distribution vanishes. It suggests that both mechanisms must be present」。実データ: 頻度順位の戻り確率 指数 1.560・打ち切り κ **23.6**(D1: ブラジルの携帯 3 万人 6 か月・基地局)/1.521・κ **64.3**(D2: Brightkite 51,406 人・772,966 地点・実際の場所)。新近順位 1.644・κ 40.9/1.699・κ 206.6。EPR γ 0.73/0.50・ρ 0.83/0.75。1 日の訪問地点 ⟨N⟩≈3(同論文が先行を引く=○)。→ ACT-R の Σ(Δt+1)^−d は頻度と新近性を 1 本で持つので「両方要る」と同じ方向 [推測]。
- **道**: Tong & Bode 2022(#38 ◎): 「The preference of pedestrians for familiar places has been identified as an essential factor affecting pedestrian route choice」・避難では「This preference for familiar routes can persist even when other available exits are closer」・不慣れな人は群衆に従う。Zhu & Levinson 2015(#39 ◎): ミネアポリス・8〜13 週の GPS・「Most people did not choose the shortest path」・既存の経路集合生成は実際の経路の多くを出せない。**歩行者の経路選択で親しみの係数・効果量を推定した一次は見つからなかった(空欄)**。

## §6 v2 への写し方(候補と区分・推奨ではない)

区分: **エンジン**=エンジンで実行可能 / **GM**=GM 裁定行き / **なし**=実行手段なし。

| # | 候補 | 区分 | 定数 | 錨 or 宣言 | 根拠 |
|---|---|---|---|---|---|
| F1a | 案 α の線形: rank′=rank−β·A(A は ln n 的なので対数則と同形) | エンジン | β | **形は錨**(Zajonc 対数 ◎・活性順の走査 ◎)・β は宣言+感度腕 | #2・#32 |
| F1b | 候補入り確率=ACT-R 想起確率 1/(1+e^{−(A−τ_low)/s})(看板で知っているだけの店を候補に足す) | エンジン | τ_low・s | 形は錨(#30)・候補入りの段は錨(#13・#17・#20)・値は宣言(時間の単位を変えると A は定数だけずれる=τ_low は単位で動くが s は動かない [サブ計算]・s の文献値 0.25 は実験課題の当てはめで店選びの較正値ではない) | #30・#20 |
| F1c | 効用に足す softmax P∝exp((u+A)/s)(IBL 型=補償型) | エンジン | s | 形は錨(#31)・**案 β に近い**・Coates は「選択には及ばない」 | #21・#31・#20 |
| F1d | 飽和・逆 U(A に上限 A_max/二次式) | エンジン | A_max | 頂点の回数が 10〜36 と散る=宣言+感度腕 | #7・#12・#34 |
| F2 | 意識と潜在の境界: 1 本の A に τ_high(文章化して B5 へ)と τ_low(潜在の下限)。境界を確率にするなら ACT-R の s | エンジン | τ_high・τ_low | **2 閾値の分離は錨**(#32)・潜在が長持ち(#8・#35)・値は宣言(単位 §4-4) | #32・#25 |
| F3 | 測り方: 決定ごとに経路(意識/潜在/両方/なし)を記録・腕 2×2(意識経路 off/on × 潜在経路 off/on)× seed | エンジン(manifest) | seed 数 | 人の実験の型(#19 の再生+再認で気づいた人を除く・#8 の好み vs 再認の強制選択)は体の内部状態から直接取れる | #19・#8・#23 |
| F4 | K(体あたり保持件数) | エンジン | K | 訪問の場所は錨の桁(容量 ≈25・κ 23.6/64.3)・**看板で知っているだけの店・人・道を足した上限は錨なし=宣言** | d68・#37 |
| F5 | 効果の大きさの上限の確認 | エンジン(判定のみ) | — | 実験室の値(#19 OR 3.23・#8 +10〜15 pp)は較正値ではない。**AD1・AD4 は holdout=照合専用** | 広告答申 |
| F6 | 接触の数え方: 看板=p_see 通過(注視は時間でなく回数=#25)・場所=そのセルにいた・人=B4b 同席(話さなくても効く=#36)・道=通った辺(錨なし) | エンジン | — | 看板と人は形の錨・道は宣言 | #25・#36 |
| F7 | LLM との分担: 潜在経路は数値のまま LLM を通らない | エンジン | — | 広告答申 4-C (ii) と一致・LLM の過剰反応(3〜10 倍)を迂回。意識経路(τ 超)は文章化されるので 4-C (i) の注入上限が要る | 広告答申 |
| F8 | 飽き(同じ店・看板への集中接触) | エンジン | — | 1 週で回復(#9)・分散接触で態度↑(#12)。店選びの飽き(料理の飽き)と重なる=宣言 | #9・#12 |

## §7 未確認一覧

1. Bornstein 1989 原典(全体 r=.26・再認あり/なしの r・10〜20 回の頭打ち・遅延の効果量)=二次のみ(APA 403)。
2. Zajonc 1968 原典の本文・図(#2 の記述経由)。Kunst-Wilson & Zajonc 1980 の選好率・再認率(抄録に数値なし)。
3. Montoya 2017 の係数と頂点(ブログ経由・再計算 36.7 回と表記 35.73 回が食い違う)。
4. Shapiro 1997 の考慮集合への包含率・Lee 2002/Yoo 2008 の効果量(本文未取得)。Shapiro 1999・Janiszewski 1993 の逐語([要約])。
5. Shapiro & Krishnan 2001 の 1 週間遅延の結果(検索要約)。Schmidt & Eisend の 37 研究の内訳(検索要約)。
6. Moreland & Beach の 3.62→4.38(二次)。
7. Donthu ら 1993 の再生率・Lee, Bart & Pauwels の効果量(SSRN 403)。
8. **看板の記憶と来店を同じ人で測った実証**(空欄)。
9. **歩行者の経路選択の親しみの効果量**(Kinateder ら 2018 の出口の親しみ・Harms ら 2021 の系統的レビューは本文未取得=×)。
10. ACT-R τ=−1.0(AMBR 章)は検索要約のみ。Jacoby 1991 の過程分離法・Yonelinas 2002 は本文未取得。
11. 看板で知っているだけの店の数(awareness set の大きさ)の一次(空欄)。
12. 日本の OOH の接触回数×認知率の関係式(jeki 1997 自身が「今後」)・jeki の来店リフトの数値(非公表)。

## §8 親への確認依頼

1. **既存答申の矛盾(循環参照検査の対象)**: [広告答申](v2-ad-information-research.md) 4-C (ii) は「ε は台帳(AD4)で較正」と書くが、同 4-F の AD4 は split=**holdout**。M17 の β を AD4 に合わせると較正が holdout に触れる。M17 では AD1/AD4 は照合専用とし、広告答申の該当句の訂正要否を判断してほしい。
2. **人の親しみと台帳 B1**: B1(Festinger 隣室 41%)は holdout。人への M17 の定数を B1 に合わせない運用でよいか。
3. **案 α と案 β**: 候補入り(#13・#17・#20)と活性順の走査(#32)は α 側、補償型(#21)と IBL 型(#31)は β 側。どちらも錨は「形」までで、β の値の錨は無い。
4. **τ の単位**: v2 の Δt は分(1 tick=1 分)。文献の τ は日単位や当てはめ値で移せない。τ_high/τ_low を B5 の行数(M4 の k)と記憶チャネル 60 tok から逆算する宣言にするか。
5. **Ferraro の加速形**(4 回 OR 1.34・12 回 3.23)と対数則(凹)は向きが逆。小標本なので形の錨にしない扱いでよいか。
6. **親が一次確認すべき数値 5 件**: (1) #2「logarithm of frequency of exposure」と F=15.61・3.35/3.06 (2) #19「17.1% of the participants selected Dasani, as compared to 21.6% in the four-exposure and 40.0% in the 12-exposure」(3) #8 表 1「60.5 55.5」「65.0 50.8」(4) #32「doubles as a decision criterion for recognition」「Records are searched in order of their activation」(5) #37 の頻度順位の打ち切り κ「64.3」「23.6」(HTML は LaTeX 表記 `\approx64.3\pm1.3`・`\approx23.6\pm0.2`)。
