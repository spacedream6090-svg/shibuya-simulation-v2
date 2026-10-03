# R-68 答申: 記憶の作り直しの錨 — 出来事ログ+ポインタ・4 種類の忘却・固定・習慣・個人差・手がかり再生
<!-- hdr:v1 -->
- **分野**: 認知科学(記憶・習慣) #12 / 会話分析・語用論 #15 / 自然言語処理・機械学習 #27(LLM エージェントの記憶の器) | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **未検収**(サブ実読: 本文 11・抄録 14・二次/要約 6・コード 2 系統・空欄=§10)。親の一次確認は §9 の「親が確認すべき上位 5 件」から。
- **索引**: [INDEX.md](INDEX.md)

> 用途: [指示書 09-30 §3-2](../design/v2-wallbounce-decisions-2026-09-30.md) の記憶の作り直し(A 器・B 4 種類・C 固定・D 習慣・E 個人差・G 説明の記録・H 候補)に錨を付ける。設計の決定はしない。
> 規律: 子サブ未起動・Web は読むだけ(PDF は OS の一時ディレクトリへ取得して pymupdf で抽出・リポに置かない)・データ取得なし・コミットなし・台帳/設計書/src 未編集。本書の数値は、本サブが開いて読んだ本文・抄録からだけ書いた。読めなかったものは空欄。

## 結論(5 行)

1. **Lally 2010 の原典本文はこのサブも読めなかった**(Wiley は Cloudflare で 403・UCL の登録は本文なし)。抄録(OpenAlex 経由の逐語)で確かめられたのは「96 人・82 人を解析・漸近曲線の当てはめ 62 人・良い当てはまり 39 人・95% 到達 18〜254 日・1 回抜かしても実質影響なし」まで。**「66 日」は抄録に無く**、後続の二次資料では「中央値」(Singh 2024 メタ分析)と「平均」(著者本人の Gardner, Lally & Wardle 2012)で食い違う。曲線の形は A(t)=a−b·e^(−ct)(Buyalskaya 2023 が「Lally に従い」と明記)。
2. **Wagenaar 1986 の抄録は「思い出せない出来事は約 20% まで増えるが、実は完全に忘れられたものは無いという証拠が幾つかある」**であり、指示書の「思い出せない 2 割も手がかりで戻る」は抄録より強い言い方(戻した手がかりの種類・割合は本文でしか分からず空欄)。「快い出来事ほどよく思い出す」は抄録にある。ただし Walker ら 1997 では差は「わずか」で、はっきりした偏りは**記憶そのものでなく感情の強さ**が不快側で速く薄れる形(fading affect bias)で出る。
3. **記憶の種類ごとの保持は形そのものが違う**: 意味記憶(学校のスペイン語)は最初の 3〜6 年だけ指数的に落ちてその後 30 年まで横ばい(Bahrick 1984)/技能は使わないと効果量 d −0.01(直後)→ −1.4(365 日超)で、身体・自然・速さの課題は落ちにくい(Arthur 1998)/潜在(知覚のプライミング)は 17 年後も残り、エピソード記憶と切り離れている(Mitchell 2006)。**種類ごとのべき指数を同じ尺度で並べた研究は見つからなかった**=4 種類の忘却の速さは宣言+感度腕になる。
4. **個人差と年齢**: ACT-R 型の忘却率(既定 0.3 の母数)は同年齢の学生 126 人で平均 .296・SD .046・範囲 .186〜.442(Sense 2018)=変動係数 約 15%。健康な成人では**年齢は覚える量を下げるが 1 週間の忘却の速さは変えない**(Studer 2024・236 人・18〜77 歳)という結果と、7 日で高齢群が多く忘れた小標本(Mary 2013・16+16 人)がある。→ 年齢は「忘れる速さ」より「覚え込みの強さ/想起の閾値」側に置くのが錨に沿う(未リサーチの読み)。
5. **会話は 5 分後でも約 10% しか思い出せず、1 か月で 4%**(Stafford & Daly 1984・Stafford ら 1987)。逐語は 80〜160 音節で消え要旨は残る(Sachs 1967)。→ A の「自分が知覚した部分」の印と、M1 の「要旨 40 字」の形は錨に沿う。LLM エージェントの先行(Generative Agents・Concordia)は**会話の全文を各自の記憶へ複写**しており、共有ログ+ポインタの器の直接の先行は読んだ範囲に無い(提供者と私的/共有の 2 層を持つ Collaborative Memory 2025 が最も近い)。v2 のテープには既に `recalled_rows`(B5 記憶行の行番号)がある=G は一部実装済み。

---

## §0 既存答申との重複(引くだけ)と循環参照の検査

| 値 | 既存の置き場所 | 一次確認の等級 | 本書での扱い |
|---|---|---|---|
| 基底活性 A=ln Σ(Δt+1)^−d・d=0.5 | 認知設計 §4(既決)・[cognition-detail](v2-cognition-detail-research.md) §4 | **出典欄は「△ 検索」**(Springer 書誌のみ・Taatgen ら PDF 未読=本文の一次は無い) | 引くだけ。**循環参照の検査**: d=0.5 を根拠にした後発(c10-initial-relations・R-49・R-51・記憶アジェンダ)は全部この 1 行に戻る。原典(Anderson & Schooler 1991 等)の本文一次はリポに無い。本書も読んでいない(空欄)。関連する一次の手がかりとして、Sense ら 2018 の本文は「ACT-R の宣言的記憶の式に基づく学習システムで忘却率の母数は既定 0.3 から始める」と書く(§4-1)=**d=0.5 とは別の母数化**(減衰の切片 α)であり、同じ数として比べない。 |
| 〔親注記 第319・訂正の伝播〕d=0.5 の出どころは ACT-R のマニュアルの推奨値(:bll .5)で、Anderson & Schooler 1991 の本文には d=0.5 は無い(環境の指数は .73・.77・.83・当てはめの d₁ は .125・1.0・1.5=R-87 §1)。設計書の「(Anderson & Schooler 1991)」の括弧は ACT-R マニュアルに直す候補 | | | |
| Petrov 2006 の近似 | [親しみの表アジェンダ](../design/v2-familiarity-counters-implementation-agenda.md) §1-2 | 親一次確認(第290) | 引くだけ |
| Murre & Dros 2015(24 時間の跳ね) | cognition-detail §4-2 | 本文実読 ✔ | 引くだけ(C の固定の話で参照) |
| GA 0.995/時・反省 150 | [r23 batch1](v2-r23-primary-check-batch1.md) #14・#15 | 一致 | 引くだけ |
| Lally 2010「66 日・18〜254 日」 | r23 batch1 #18(条件つき一致・原典 403)・[persona-dynamics](v2-persona-dynamics-research.md) §3-1(△二次) | 抄録のみ | §1 で抄録の逐語と後続の二次を並べ直した(原典本文は依然 403) |
| 単純接触・潜在の持続(Seamon 1983 ほか) | [R-51](v2-r51-mere-exposure-incidental-ads-research.md) §4-2 | 親検収 5 数値一致 | 引くだけ(§3 の潜在の行) |
| 忘却の減衰の散らばり(5.8 日〜23 日〜d=0.5) | [R-49](v2-r49-wom-memory-store-choice-research.md) §4 | 親検収 | 引くだけ |
| 会話の頻度(Mehl & Pennebaker 2003 覚醒の 27.9%) | [thought-frequency-anchors-note](v2-thought-frequency-anchors-note.md) | A | 引くだけ(R-69 側でも参照) |
| GA/AI Town/Humanoid・Concordia/AgentSociety/OASIS のコード | [R-43](v2-r43-code-reading-ga-aitown-humanoid.md)・[R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md) | B | 行動の表現と効果の解決が主題で、**記憶の器(共有/個別・ポインタ)は読んでいない**=§7 で重複しない範囲を読んだ |

---

## §1 Lally ら 2010(習慣の形成)— 決定 D の錨

### 1-1 原典(抄録の逐語・OpenAlex の抄録索引から復元・原典本文は 403)
Lally P., van Jaarsveld C.H.M., Potts H.W.W., Wardle J. (2010). How are habits formed: Modelling habit formation in the real world. *European Journal of Social Psychology* 40(6):998–1009. https://doi.org/10.1002/ejsp.674

> "96 volunteers chose an eating, drinking or activity behaviour to carry out daily in the same context (for example 'after breakfast') for 12 weeks. They completed the self‐report habit index (SRHI) each day and recorded whether they carried out the behaviour. The majority (82) of participants provided sufficient data for analysis, and increases in automaticity (calculated with a sub‐set of SRHI items) were examined over the study period. Nonlinear regressions fitted an asymptotic curve to each individual's automaticity scores over the 84 days. The model fitted for 62 individuals, of whom 39 showed a good fit. Performing the behaviour more consistently was associated with better model fit. The time it took participants to reach 95% of their asymptote of automaticity ranged from 18 to 254 days; indicating considerable variation … Missing one opportunity to perform the behaviour did not materially affect the habit formation process. With repetition of a behaviour in a consistent context, automaticity increases following an asymptotic curve which can be modelled at the individual level."

- 標本: 96 人(解析 82・当てはまり 62・良い当てはまり 39)。行動の種類: 飲食・運動の自選 1 行動を毎日同じ文脈で。尺度: SRHI の自動性の部分項目(どの項目かは本文=空欄)。観察期間 84 日=**254 日は観察期間外への外挿**。
- **「66 日」は抄録に無い**。後続の記述:
  - Singh ら 2024(*Healthcare* 12:2488・PMC11641623・本文実読)§3.3:「Lally et al. [5] examined the formation of healthy eating, water consumption or exercise habits and reported that the median time to reach 95% automaticity was 66 days (range: 18 to 254 days).」=**二次**。
  - Gardner, Lally & Wardle 2012(*Br J Gen Pract*・PMC3505409・WebFetch 要約経由=要約のみ):「automaticity plateaued on average around 66 days」「simpler actions become habitual more quickly」(水を飲む vs 腹筋 50 回)「automaticity gains soon resumed after one missed performance」=**著者本人だが「平均」と書く**。
  - → **中央値か平均かは原典本文でしか決まらない(空欄)**。batch1 #18 の注(「母集団は良い当てはまりの 39 人」)と合わせ、66 は「当てはまった一部の人の代表値」として扱う。
- 行動の種類による違い: 「単純な行動ほど速い」(著者 2012・要約のみ)。数値は本文=空欄。
- 1 回抜かしの影響: 「実質影響なし」(抄録 ◎)。

### 1-2 曲線の式(一次の本文にある形)
Buyalskaya, Ho, Milkman, Li, Duckworth, Camerer 2023, *PNAS* 120(17):e2216115120(PMC10151500・本文実読):「Following (5), for each individual i, we attempt to identify A(t), an exponential function of form a − b e^(−c t) describing daily-level habit strength as a function of time. Likewise, following (5), we define the inferred time to habit formation as the time it takes for A(t) to reach 95% of its asymptote.」((5)=Lally 2010)

**回数の関数として書く(未リサーチ=本書の導出)**: 同じ状況で 1 日 1 回なら t=回数 n。A(0)≈0(b≈a)と置くと 95% 到達は n95 = ln 20 / c ≈ 3.00 / c。
- n95=66 → c ≈ 0.0454/回・半飽和 n50 = ln2/c ≈ 15.3 回(persona-dynamics の「15〜66 回」と一致=同じ導出)
- n95=18 → c ≈ 0.166/回 / n95=254 → c ≈ 0.0118/回
- 「b≈a」は仮定(Lally の当てはめの切片は本文=空欄)。

### 1-3 後続・メタ分析
- **Singh ら 2024 メタ分析**(20 研究・2,601 人・本文実読): 「Four studies reported the median or mean times to reach habit formation, ranging from 59–66 days (median) and 106–154 days (means), with substantial individual variability (4–335 days).」Keller ら 2021(健康な食事): 中央値 59 日(4〜335 日)・閾値に届いたのは 23%。習慣得点の前後差 SMD 0.69(95% CI 0.49–0.88)。
- **Buyalskaya ら 2023**(ジム 30,110 人・中央値 1,525 日の観察/病院の手洗い 3,124 人・約 4,000 万点): 「it typically takes months to form the habit of going to the gym but weeks to develop the habit of handwashing in the hospital」。予測子で最も重いのは前回からの間隔:「for 76% of gym goers in our sample, the longer it has been since they last visited the gym, the less likely they are to go on a given day.」(具体の月数は図のみ=空欄)。
- 含意(未リサーチの読み): 習慣の強さは「同じ状況での回数」と「前回からの間隔」の両方で決まる=**基底活性 A(回数と経過時間)と同じ入力**で書ける。領域で速さが 1 桁違う(週 vs 月)。

---

## §2 Wagenaar 1986(自伝的記憶の 6 年)— 決定 H の錨

Wagenaar W.A. (1986). My memory: A study of autobiographical memory over six years. *Cognitive Psychology* 18(2):225–252. https://doi.org/10.1016/0010-0285(86)90013-7 — 原典は ScienceDirect 403・OA なし。**抄録の逐語**(TNO リポジトリの書誌ページ https://resolver.tno.nl/uuid:421db624-3c69-44c8-a9fc-cf67a3a6943d を curl で取得):

> "This paper describes a study on the recall of 2400 events from the author's daily life, recorded during a period of 6 years. One feature of the study is that all events were recorded by means of four aspects, viz., what the event was, who was involved, and where and when it happened. All events were scaled for saliency, emotional involvement, and pleasantness. Recall was cued by different combinations of the recorded aspects. … Pleasant events were better recalled than unpleasant events. An analysis of the effectiveness of cue combinations showed that, in the organization of autobiographical memory, temporal information functions in a different manner than information about what, who, and where. Although the number of irretrievable events can rise to about 20%, there is some evidence that in fact none of these events was completely forgotten."

- 手がかりの数と想起率・保持期間ごとの想起率・快/不快の差の大きさ: **本文の図表=空欄**。
- 「何が」が最も効く手がかり(Storms 2024 の要約=二次)/「いつ」は効かない(抄録の「時間情報は別の働き」と整合)。
- 指示書の「思い出せない 2 割も手がかりで戻る」は抄録の **"can rise to about 20%" と "some evidence that … none … completely forgotten"** を強めた言い方。「どんな証拠か」(他人に聞いた手がかりで戻したか等)は本文=**空欄・記憶で埋めない**。
- 関連の一次(本文実読): Storms 2024 *Journal of Cognition* 7(1):16(日記 2,691 件・24 年)抄録:「I remembered less than two thirds of the recorded events and the retention curve showed a curvilinear shape. … Regression analyses showed that event rehearsal was the best predictor of retention and dating」。快さ・顕著さ・感情の関与・語り直し・自己関連と有意に相関(親密さは無相関)。
- 楽しい出来事の偏り:
  - Walker, Vogl & Thompson 1997 *Appl Cogn Psychol* 11:399–413 抄録(OpenAlex 逐語):「judgments of pleasantness or unpleasantness of an event became less extreme as retention interval increased. This effect was larger for unpleasant events … showed a modest effect of pleasantness with pleasant events remembered slightly better than unpleasant events.」保持期間 3 か月・1 年・4.5 年。
  - Walker & Skowronski 2009 *Appl Cogn Psychol* 23:1122–1136(総説・本文実読):「participants remembered the positive and negative events with almost equal clarity. Thus, while the emotions associated with positive and negative events faded differentially, the memory for the events themselves did not.」Ritchie ら 2009 の内訳(W&S 2009 経由=二次): 1 年後に快の出来事は Fixed 49%・Fading 37%/不快は Fading 51%・Fixed 38%。
  - Ritchie ら 2015 *Memory* 23(2):278–290: 10 文化・562 人・2,400 件超で FAB(抄録・検索要約経由=要約のみ)。
- 含意(未リサーチの読み): H の「楽しい出来事ほど覚えている偏り」は、**出来事の想起率の差(小さい)**と**評価の感情の強さの差(不快が速く薄れる)**の 2 つに分けて腕にするのが錨に沿う。後者は B の「意味(評価)」の減衰を符号で変える形になる。

---

## §3 記憶の種類ごとの忘却 — 決定 B の錨

| 種類(指示書 B) | 錨 | 数値・逐語 | 条件・標本 | 等級 |
|---|---|---|---|---|
| エピソード(実験室の無意味綴り) | Murre & Dros 2015 | 既存(cognition-detail §4-2) | — | 本文(既存) |
| エピソード(自伝) | Storms 2024 / Wagenaar 1986 / Stafford ら 1987(§6) | 24 年で 2/3 未満を想起・曲線は曲がる/想起不能は約 20% まで | 単一被験者の日記 | 本文/抄録 |
| 関数の形の総覧 | Rubin & Wenzel 1996 *Psych Rev* 103:734–760 | 210 データ集合 × 105 種の 2 母数関数:「The best fits were to the logarithmic function, the power function, the exponential in the square root of time, and the hyperbola in the square root of time. … the same set of 4 functions fit most data sets, with autobiographical memory being the exception.」 | 種類ごとの母数の表は本文(Duke の PDF はボット検査で読めず=空欄) | 抄録(OpenAlex) |
| 意味(知識) | Bahrick 1984 *JEP:General* 113:1–29(PMID 6242406) | 「memory curves which decline exponentially for the first 3-6 years of the retention interval. After that retention remains unchanged for periods of up to 30 years before showing a final decline. … one portion of the response distribution has life spans of 0-6 years, the other portion, life spans in excess of 25 years」 | 733 人・学校で習ったスペイン語・50 年 | 抄録(Europe PMC) |
| 手続き(技能) | Arthur, Bennett, Stanush & McNelly 1998 *Human Performance* 11(1):57–101 | 「the amount of skill loss ranging from an effect size (d) of -0.01 immediately after training to a d of -1.4 after more than 365 days of nonuse. … Physical, natural, and speed-based tasks were less susceptible to skill loss than cognitive, artificial, and accuracy-based tasks.」 | 53 論文・189 点のメタ分析 | 抄録(OpenAlex) |
| 潜在(知覚のプライミング) | Mitchell 2006 *Psych Sci* 17:925(PMID 17176420) | 「tested 17 years later by mail. Identification rates were significantly higher for fragments from these previously exposed targets … Priming … was stable over the years (r= .51). Priming was dissociated from episodic memory, in that it was present even in subjects who reported no conscious recollection」 | 絵を 1〜3 秒・17 年後 | 抄録 |
| 潜在(単純接触) | Seamon 1983 ほか | 既存 R-51 §4-2(好み 1 週で落ちない) | — | 既存 |
| 材料による違い(同じ人) | Sense, Behrens, Meijer & van Rijn 2016 *Top Cogn Sci* 8:305–321 | 題名どおり「個人の忘却率は時間を通して安定・材料で違う」(単語・国旗・地図) | 本文は RUG の PDF が 403=**要約のみ** | 要約のみ |

- **習慣(指示書の「手続き」)と技能は別物**: Arthur 1998 は「訓練した技能を使わないと落ちる」。習慣(状況 → 行動の結びつき)の非使用時の減衰の直接の一次は読んだ範囲に無い(空欄)。Buyalskaya の「前回からの間隔」が最も近い。
- **種類ごとのべき指数の比較**: 見つからなかった(空欄)。→ B は「エピソード d=0.5(既決)/意味=2 成分(速く落ちる部分と残る部分・Bahrick の形)/習慣=回数で飽和・間隔で弱まる(§1)/親しみ=長く残る(Mitchell)」を**形の宣言**として置き、母数は感度腕(未リサーチの提案)。

---

## §4 年齢と個人差 — 決定 E の錨

### 4-1 同じ年齢の中の個人差(忘却の速さ)
Sense, Meijer & van Rijn 2018 *Frontiers in Education* 3:112(本文実読):「When a new item is introduced, the parameter starts with the default value of 0.3 … The parameter captures the decay of the memory trace … lower values indicate slower decay.」「The mean rate of forgetting was .296 with a standard deviation of 0.046 [range = (0.186; 0.442)].」標本 126 人(オランダの大学 1 年・年齢中央値 20・18〜26)・スワヒリ語の単語。一般知能・作業記憶との相関は弱い(本文の図 2)。
→ 変動係数 約 15.5%・範囲は平均の 0.63〜1.49 倍。**若い学生・単語学習**の値で、街の出来事への転用は未リサーチ。

### 4-2 年齢
| 研究 | 標本 | 結果(逐語) | 等級 |
|---|---|---|---|
| Studer, Heinemann, Gutbrod & Henke 2024 *Sci Rep* 14:31176 | 236 人・18〜77 歳・15 語・30 分と 1 週 | 「no significant interaction between time × age group (F(3.05, 352.69) = 1.27, p = .28). Hence, old age was not associated with a disproportionate memory loss over one week」/抄録「learned fewer words, but they exhibited no disproportionate forgetting over days」 | 本文 |
| Mary, Schreiner & Peigneux 2013 *Front Psychol* 4:750 | 若年 16・高齢 16(65〜75 歳) | 「recall was significantly decreased 7 days later, with an increased forgetting in older participants」・睡眠中の覚醒の多さと 7 日後の想起が負の相関 | 本文(抄録部) |
| Rivera-Lares, Della Sala, Baddeley & Logie 2023 *QJEP* | 若年・高齢・30 秒〜24 時間 | 「initial acquisition is influenced by age … rate of forgetting proved to be independent from initial degree of learning」 | 検索要約のみ |
| Wilschut ら 2026 *Commun Med*(PMC13562709) | 964 人・22〜86 歳・8 分の対連合学習から忘却の速さを推定した SGMA 得点 | 表 2「Age −0.69 (SE 0.04) t −18.45」(得点/歳・教育 +2.34) | 本文(**得点の尺度と α の対応は本文で見つけられず=空欄**) |

- **フロア(実データ同士のばらつき)**: 年齢の忘却差は「無い」(Studer・n 236)と「7 日で有る」(Mary・n 32)が並ぶ。同年齢内の SD .046(平均の 15%)。
- 含意(未リサーチの読み): E は **(i) 忘却の速さ=体ごとに平均 0.3 相当±15% を振る(年齢に依らない)(ii) 年齢は覚え込みの強さ(初回の活性)か想起の閾値 τ に掛ける** とすると、Studer・Rivera-Lares・Wilschut の 3 本と矛盾しない。v2 の d=0.5 と Sense の 0.3 は母数化が違うので、CV だけを移す。

---

## §5 睡眠による固定 — 決定 C の錨

| 研究 | 逐語・数値 | 条件 | 等級 |
|---|---|---|---|
| Berres & Erdfelder 2021 *Psych Bull*(PMID 35404637) | 「analyzing 823 effect sizes from 271 independent samples … a moderate overall sleep benefit in episodic memory (g = 0.44) … When accounting for selective reporting bias, the overall effect … is reduced but still significant (g = 0.28)」。何度も学んだ材料で大きい・自由再生>手がかり再生>再認 | 1967〜2019 の 177 論文 | 抄録 |
| Wilhelm ら 2011 *J Neurosci*(PMC6623736) | 「Postlearning sleep compared with wakefulness produced a strong improvement at delayed retrieval only if the subjects had been informed about the retrieval test after the learning period. If they had not been informed, retrieval after retention sleep did not differ from that after the wake retention interval.」手続き(指のタッピング)にも及ぶ | 単語対・位置・運動 | 抄録 |
| Sugita 2023(PsyArXiv・学部卒論) | 期待の操作で差なし(睡眠の利得そのものはあり) | 12 時間 | 抄録(査読なし) |
| Cordi & Rasch 2021 *Curr Opin Neurobiol* | 「several key findings … could not be replicated or occurred only under certain conditions, suggesting that effects of sleep on memory are smaller, more task-dependent, less SWS-related, less robust and less long-lasting than previously assumed」 | 総説 | 抄録 |
| Stickgold & Walker 2013 *Nat Neurosci*(PMC5826623) | 「memory triage」=選んで残す仮説 | 総説 | 抄録 |

- 含意(未リサーチの読み): 「就寝直後に 1 呼で固定」は中程度の効果(g 0.28〜0.44)に錨がある。「重要なもの(将来使うもの)が優先」は Wilhelm の一次があるが再現が揺れている=**優先の強さは宣言+感度腕**。v2 の Murre & Dros の 24 時間の跳ね(既存)と同じ向き。

---

## §6 会話の一部しか覚えていない — 決定 A の「知覚した部分」の錨

| 研究 | 逐語・数値 | 条件 | 等級 |
|---|---|---|---|
| Stafford & Daly 1984 *Hum Commun Res* 10(3):379–402 | 「even after only five minutes people are able to recollect only about 10% of what was said in a social exchange. … Subjects also remembered more of their partner's comments in the interaction than their own.」 | 自然会話・書面/口頭の想起 | 抄録(OpenAlex) |
| Stafford, Burggraf & Sharkey 1987 *Hum Commun Res* 14(2):203–229 | 「Participants could recall only about 10% of their conversations immediately after the conversations. One month later this figure had dropped to 4%. … participants recalled less content and reported more descriptive statements, made more inferences, and were less accurate」 | 2 段階・1 か月 | 抄録 |
| McKinley, Brown-Schmidt & Benjamin 2017 *Mem Cogn*(PMID 28685249) | 「content that was spoken was remembered better than content that was heard」 | 課題つき会話(共通基盤) | 抄録 |
| Samp & Humphreys 2007 *Commun Monogr* 74(4) | 友人より見知らぬ人との会話の想起が不正確 | 144 人の女性 | 抄録 |
| Sachs 1967 *Percept Psychophys* 2:437(Springer 抄録) | 「after 80–160 syllables, recognition for syntactic changes had dropped to near chance levels while remaining high for semantic changes. … the original form of the sentence is stored only for the short time necessary for comprehension」 | 96 人・24 の録音文章 | 抄録 |

- **食い違い(フロア)**: 自分の発言と相手の発言のどちらを覚えるかが、自然会話(相手>自分・Stafford)と課題会話(話した>聞いた・McKinley)で逆。
- 含意(未リサーチの読み): 聞き手の記憶は「発話行へのポインタ+要旨」、逐語は持たない(Sachs)。想起できる割合は idea unit の約 10%(直後)→ 4%(1 か月)。これは「会話の行を持つか持たないか」でなく「要旨の何割が思い出せるか」の錨なので、**知覚した部分の印(聞こえた範囲)と、想起の閾値(思い出せる範囲)を別の欄**にすると両方に錨が付く。

---

## §7 出来事ログ+一人ずつのポインタの器の先行(R-43/R-44 と重複しない範囲)

### 7-1 Generative Agents(コード読み・commit fe05a71d…・R-43 と同じ版)
- `reverie/backend_server/persona/memory_structures/associative_memory.py`: 記憶は**体ごと**の `ConceptNode` の列(`id_to_node`)。欄に `filling` があり、`add_thought` は `filling` に**根拠のノード ID の列**を受け取る(:199–210「if filling: depth += max([self.id_to_node[i].depth for i in filling])」)。
- `cognitive_modules/reflect.py:121–132`: 内省は `generate_insights_and_evidence` が返す根拠のノード ID を `add_thought(…, thought_embedding_pair, evidence)` で `filling` に書く=**体の中の記憶どうしのポインタ**の先行。
- `cognitive_modules/perceive.py:167–171`: 会話は `add_chat(…, persona.scratch.chat)`=**会話の全文を各自の記憶へ複写**(共有ログへのポインタではない・知覚した部分の印もない)。
- `cognitive_modules/retrieve.py:266–267`: 想起したノードの `last_accessed` を更新するだけ。**判断ごとに引いた記憶を記録する口は無い**。
- 知覚の制限は `vision_r`・`att_bandwidth`・`retention`(perceive.py:31–33)=見える範囲と注意の本数で事象を絞る。

### 7-2 Concordia(コード読み・main @ 02a5faccdc2a233c51093721060a8f5f10198d67・2026-09-29)
- `concordia/components/game_master/make_observation.py:41–82` `ObservationQueue`「A shared queue for observations that can be used across multiple GMs」: `add(entity_name, event, player_names)` が**同じ文字列を各プレイヤーの列へ複写**する。
- 同 :205–219: 列が空なら GM の LLM が「What does {active_entity_name} observe now? Never repeat information that was already provided …」で**その人の観測を書く**=主観の濾過を GM の LLM が担う(エンジンの印ではない)。`log_entry['queue']` に列の状態を残す。
- `concordia/associative_memory/basic_associative_memory.py:52`: 記憶は体ごとの `pd.DataFrame(columns=['text', 'embedding'])`=文字列と埋め込みだけ・ポインタなし。

### 7-3 論文(抄録)
- Rezazadeh ら 2025「Collaborative Memory: Multi-User Memory Sharing in LLM Agents with Dynamic Access Control」arXiv:2505.18279(abs を WebFetch=要約のみ): 私的な断片(originating user のみ可視)と共有の断片の 2 層・各断片に「immutable provenance attributes (contributing agents, accessed resources, and timestamps)」・「full auditability of memory operations」。**用途は権限管理**で、主観の注釈や「知覚した部分」の印は無い。
- MemGPT・AgentSociety の記憶の器: 本書では読んでいない(空欄)。

### 7-4 v2 自身(コード読み)
- `src/shibuya/engine/tape.py:37–38, 125`: テープに `recalled_rows`(list<int32>)「その呼の B5「記憶」行に載せた記憶の行番号」がある=**G(引いた記憶の行 ID をテープに残す)は B5 記憶行の範囲で既にある**。店の評価・親しみ・関係辺を判断に使った場合の記録の有無は本書で確かめていない(親が確認)。

**まとめ**: 「共有の出来事ログを 1 回だけ書き、各自はポインタ+主観の注釈+知覚した範囲の印を持つ」器の、LLM 社会シミュでの直接の先行は読んだ範囲に無い。近い要素は GA の `filling`(体内のポインタ)・Concordia の共有列(ただし複写)・Collaborative Memory の出所つき 2 層。

---

## §8 まとめ: 決定 A〜H × 錨

| 決定 | 錨の有無 | 値 | 条件 | 既定に入れてよいか(本サブの判断=未リサーチ) |
|---|---|---|---|---|
| A 器(共有ログ+ポインタ+知覚の印) | 形の先行は部分的(§7)・知覚の限界は錨あり(§6) | 会話の想起 約 10%(5 分)→ 4%(1 か月)・逐語は 80〜160 音節で消える | 自然会話・英語圏 | 器は設計判断(錨不要)。「知覚した部分」の印は入れてよい。想起の割合は腕で |
| B 4 種類・忘却を別に | 形の違いは錨あり(§3)・指数の比較は空欄 | 意味: 3〜6 年で落ちて以後横ばい/技能: d −1.4(>365 日)/潜在: 17 年残る | 各研究の材料に依存 | **形だけ既定**(意味=2 成分・親しみ=遅い減衰)・母数は感度腕 |
| C 就寝直後 1 呼の固定 | あり | 睡眠の利得 g 0.44(偏り補正 0.28)/将来の関連で選ぶ(Wilhelm)は再現が揺れる | 実験室の単語対ほか | 固定の呼は既定でよい(既決)。「重要なものを優先」の強さは腕 |
| C′ 信念は追記だけ | 直接の錨なし | — | — | 設計判断(説明可能性のため)=錨不要と明記 |
| D 習慣 | あり(抄録+二次) | A(t)=a−b·e^(−ct)・95% 到達 18〜254 日(66 は中央値/平均が未確定)・導出 c ≈ 0.045/回(n95=66)・1 回抜かし影響なし・前回からの間隔が最重要(76%) | 1 日 1 回の自選の健康行動・ジム/手洗い | 形は既定でよい。c の値は感度腕 {0.012, 0.045, 0.17} |
| E 個人差 | あり | 忘却率 SD/平均 ≈ 15%(126 人・20 歳)・年齢は忘却の速さより覚え込みに効く(Studer 236 人) | 単語学習・実験室 | 体ごとの忘却率の振り(CV 15%)は既定候補。年齢は覚え込み/閾値側へ(腕で比較) |
| G 引いた記憶の記録 | 先行は GA の `filling`(内省の根拠だけ) | v2 は `recalled_rows` が既にある | — | 既にある範囲を確認し、店の評価・親しみ・関係辺に広げるかは親判断 |
| H-1 手がかりで戻す | 抄録のみ | 想起不能は約 20% まで・完全に忘れたものは無い「証拠が幾つか」 | 単一被験者・6 年 | 候補のまま(本文で証拠の中身を確かめてから) |
| H-2 楽しい出来事の偏り | あり | 想起の差はわずか(Walker 1997)・感情の強さは不快が速く薄れる(FAB・1 年後 不快 Fading 51% vs 快 Fixed 49%) | 日記研究 | 「想起率」と「評価の感情の減衰」を分けた感度腕 |
| H-3 重要度を予測誤差へ | あり(実験室) | Rouhani ら 2018「recognition was better for items associated with larger absolute prediction errors」 | 報酬学習課題 | D-104 の方向を支持。候補のまま |

---

## §9 出典の表

| # | 出典 | URL | 読んだ範囲 | 等級 |
|---|---|---|---|---|
| 1 | Lally ら 2010 EJSP 40(6):998 | https://doi.org/10.1002/ejsp.674 | 抄録(OpenAlex の抄録索引)・本文 403 | 抄録 |
| 2 | Singh ら 2024 Healthcare 12:2488 | https://doi.org/10.3390/healthcare12232488 (PMC11641623) | 本文 | 本文 |
| 3 | Gardner, Lally & Wardle 2012 BJGP | https://pmc.ncbi.nlm.nih.gov/articles/PMC3505409/ | WebFetch 要約 | 要約のみ |
| 4 | Buyalskaya ら 2023 PNAS 120:e2216115120 | https://doi.org/10.1073/pnas.2216115120 (PMC10151500) | 本文 | 本文 |
| 5 | Wagenaar 1986 Cogn Psychol 18:225 | https://doi.org/10.1016/0010-0285(86)90013-7 | 抄録(TNO 書誌) | 抄録 |
| 6 | Storms 2024 J Cogn 7(1):16 | https://doi.org/10.5334/joc.334 | 本文 PDF | 本文 |
| 7 | Walker, Vogl & Thompson 1997 ACP 11:399 | https://doi.org/10.1002/(SICI)1099-0720(199710)11:5<399::AID-ACP462>3.0.CO;2-E | 抄録 | 抄録 |
| 8 | Walker & Skowronski 2009 ACP 23:1122 | https://www.niu.edu/jskowronski/publications/walkerskowronski2009.pdf | 本文 | 本文 |
| 9 | Rubin & Wenzel 1996 Psych Rev 103:734 | https://doi.org/10.1037/0033-295X.103.4.734 | 抄録 | 抄録 |
| 10 | Bahrick 1984 JEP:G 113:1 | https://pubmed.ncbi.nlm.nih.gov/6242406/ | 抄録 | 抄録 |
| 11 | Arthur ら 1998 Hum Perform 11:57 | https://doi.org/10.1207/s15327043hup1101_3 | 抄録 | 抄録 |
| 12 | Mitchell 2006 Psych Sci 17:925 | https://doi.org/10.1111/j.1467-9280.2006.01805.x | 抄録 | 抄録 |
| 13 | Sense, Meijer & van Rijn 2018 Front Educ 3:112 | https://doi.org/10.3389/feduc.2018.00112 | 本文 | 本文 |
| 14 | Sense ら 2016 Top Cogn Sci 8:305 | https://doi.org/10.1111/tops.12183 | 題名と検索要約 | 要約のみ |
| 15 | Studer ら 2024 Sci Rep 14:31176 | https://www.nature.com/articles/s41598-024-82570-w | 本文 | 本文 |
| 16 | Mary, Schreiner & Peigneux 2013 Front Psychol 4:750 | https://doi.org/10.3389/fpsyg.2013.00750 | 抄録部 | 抄録 |
| 17 | Rivera-Lares ら 2023 QJEP | https://doi.org/10.1177/17470218221128780 | 検索要約 | 要約のみ |
| 18 | Wilschut ら 2026 Commun Med | https://doi.org/10.1038/s43856-026-01663-x (PMC13562709) | 本文 | 本文 |
| 19 | Berres & Erdfelder 2021 Psych Bull | https://doi.org/10.1037/bul0000350 | 抄録 | 抄録 |
| 20 | Wilhelm ら 2011 J Neurosci | https://doi.org/10.1523/JNEUROSCI.3575-10.2011 | 抄録 | 抄録 |
| 21 | Cordi & Rasch 2021 Curr Opin Neurobiol | https://doi.org/10.1016/j.conb.2020.06.002 | 抄録 | 抄録 |
| 22 | Sugita 2023 PsyArXiv | https://doi.org/10.31234/osf.io/druf3 | 抄録 | 抄録(査読なし) |
| 23 | Stickgold & Walker 2013 Nat Neurosci | https://doi.org/10.1038/nn.3303 | 抄録 | 抄録 |
| 24 | Stafford & Daly 1984 HCR 10:379 | https://doi.org/10.1111/j.1468-2958.1984.tb00024.x | 抄録 | 抄録 |
| 25 | Stafford, Burggraf & Sharkey 1987 HCR 14:203 | https://doi.org/10.1111/j.1468-2958.1987.tb00127.x | 抄録 | 抄録 |
| 26 | McKinley ら 2017 Mem Cogn | https://doi.org/10.3758/s13421-017-0730-3 | 抄録 | 抄録 |
| 27 | Sachs 1967 Percept Psychophys 2:437 | https://doi.org/10.3758/BF03208784 | 抄録(Springer) | 抄録 |
| 28 | Samp & Humphreys 2007 Commun Monogr 74:561 | https://doi.org/10.1080/03637750701716610 | 抄録 | 抄録 |
| 29 | Rouhani, Norman & Niv 2018 JEP:LMC | https://doi.org/10.1037/xlm0000518 | 抄録 | 抄録 |
| 30 | Generative Agents(コード) | https://github.com/joonspk-research/generative_agents (fe05a71d…) | associative_memory.py・reflect.py・retrieve.py・perceive.py | コード |
| 31 | Concordia(コード) | https://github.com/google-deepmind/concordia (02a5facc…) | make_observation.py・basic_associative_memory.py | コード |
| 32 | Rezazadeh ら 2025 arXiv:2505.18279 | https://arxiv.org/abs/2505.18279 | abs(WebFetch 要約) | 要約のみ |
| 33 | Ritchie ら 2015 Memory 23:278 | https://doi.org/10.1080/09658211.2014.884138 | 検索要約 | 要約のみ |

**親が一次確認すべき上位 5 件**: ① Lally 2010 の原典本文(中央値か平均か・曲線の切片・行動の種類別の値)② Wagenaar 1986 の本文(手がかりの数と想起率・「完全に忘れたものは無い」の証拠の中身)③ Sense 2018 の .296/.046 と既定 0.3(本文 Results・Methods)④ Studer 2024 の交互作用の F 値と表 2 ⑤ Stafford & Daly 1984/Stafford 1987 の 10%・4%(抄録の逐語)。

## §10 未確認の一覧(空欄)

1. Lally 2010 本文(66 が中央値か平均か・SRHI の部分項目・切片・行動の種類別の値・抜かした回の影響の大きさ)。
2. Wagenaar 1986 本文(手がかり 1〜3 個での想起率・保持期間ごとの想起率・快/不快の差の大きさ・「完全に忘れたものは無い」の証拠の種類)。
3. 記憶の種類ごとのべき指数を同じ尺度で比べた研究(見つからず)。Rubin & Wenzel 1996 の種類別の母数表(Duke の PDF がボット検査)。
4. ACT-R の d=0.5 の原典本文(リポ全体で一次なし=循環参照)。
5. Sense 2016 本文(材料間の差の大きさ・安定性の相関)。Wilschut 2026 の SGMA 得点と α の対応。
6. 習慣を使わないときの減衰の一次(Arthur 1998 は技能の値)。
7. MemGPT・AgentSociety の記憶の器(本書では読んでいない)。
8. v2 のテープで、店の評価・親しみ・関係辺を判断に使ったときに行 ID が残るか(本書は `recalled_rows` の存在だけ確認)。
9. Gibbons ら 2011(FAB が 12 時間以内に始まり 3 か月続く)は検索要約でだけ見た=未記載。

## §11 INDEX に足す行の案

```
| 09-30 | [r68-memory-rework-anchors](v2-r68-memory-rework-anchors.md) | 約 260 | **未検収**(サブ実読 本文 11・抄録 14・要約 6・コード 2) | 認知科学(記憶・習慣) #12 / 会話分析・語用論 #15 / 自然言語処理・機械学習 #27 | R-68 記憶の作り直しの錨(第311 指示書 §3-2): Lally 2010 は原典本文 403 のまま・抄録に 66 は無く中央値(Singh 2024)と平均(著者 2012)で食い違う・曲線 a−b·e^(−ct)(Buyalskaya 2023)→ c≈0.045/回 / Wagenaar 1986 抄録「想起不能は約 20% まで・完全に忘れたものは無い証拠が幾つか」/ 種類ごとの形: 意味 3〜6 年で落ちて横ばい(Bahrick)・技能 d −1.4(Arthur)・潜在 17 年(Mitchell)・指数の比較は空欄 / 個人差 忘却率 .296±.046(Sense 2018)・年齢は忘却の速さを変えない(Studer 2024) / 睡眠 g 0.44→0.28 / 会話の想起 10%→4%(Stafford) / 共有ログ+ポインタの直接の先行なし・v2 は recalled_rows 既存 |
```
