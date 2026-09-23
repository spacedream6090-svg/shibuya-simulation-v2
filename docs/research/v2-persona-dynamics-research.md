# レーンPD: ペルソナの動態 — 「ペルソナはシミュを回す中で変化させる必要があるか」(R4リサーチ答申)

<!-- hdr:v1 -->
- **分野**: 人格心理学 #13 | **重要度**: P0(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 162 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(Fable・2026-09-07)**: 出典を親が一次確認した。✔=親が実読して一致。
> - ✔ Roberts & DelVecchio 2000 Psychological Bulletin(PDF実読): 「trait consistency increased from .31 in childhood to .54 during the college years, to .64 at age 30, and then reached a plateau around .74 between ages 50 and 70 when time interval was held constant at 6.7 years」・Crook(1941)「trait consistency averaged above .80 over several weeks and dropped to around .50 after 6½ years」。**「1年未満の研究を除外」の逐語は親の抽出で見つからず**(要旨レベルの主張は一致)。
> - ✔ arXiv 2605.06307(抄録実読): 「Scripted interactions with explicit task prompts eliminate this drift entirely」(非台本対話ではドリフト発生)。✔ arXiv 2402.10962(抄録実読): LLaMA2-chat-70B/GPT-3.5で「a significant instruction drift within eight rounds of conversations」。
> - ✔ JILPT(実読): 「2023年の入職率は16.4%(前年比1.2ポイントの上昇)、離職率は15.4%(同0.4ポイントの上昇)」。✔ 総務省統計局 住民基本台帳人口移動報告2024(実読): 市区町村間移動者520万7746人(前年比+1.1%)・都道府県間252万3249人。年率4.2%は親未再計算(分母=人口推計)。
> - **Lally et al. 2010(66日・18-254日・n=96)はWiley 403で親も未確認=二次のまま**→T1→T0のn(15-66・既定40)は**expedient**(答申の申告どおり)。Hill 2013・Sethuraman 2011・Verplanken 2008も二次。
> - 正典化: docs/research/v2-persona-dynamics-research.md(ペルソナ動態の根拠)。

作成: 2026-09-07 / 担当: リサーチサブ(Opus 5) / 検収: 親(Fable) → 決定: ユーザー
規律: 子サブ不使用・出典は**実読ページのみ**引用・未読/未取得は「空欄(未確認)」・リポは読み取りのみ・ファイルDLなし

**凡例**: ✔実読=当該ページ本文を取得して引用した / △二次=検索エンジンが返した要旨断片のみ(本文未取得)=**親の一次確認対象** / 空欄(未確認)=取得できず。【推測】=一次根拠のない私の推論。

---

## 要約(10行)

1. **性格特性(Big Five)は週〜月では固定してよい。** Roberts & DelVecchio 2000は**1年未満の研究を除外**した上で1年間隔の平均一致 r≈.55、同論文が引くCrook 1941は「数週間で **>.80**」「低下は最初の数か月で速く約1年で安定」。週〜月尺度では特性の**ランクオーダーは実質不変**。✔実読
2. 平均水準変化は**若年成人期(20-40歳)に協調性以外が上昇**する程度で、年〜十年の尺度。30日のシミュで動く量ではない(d値は本文未取得=空欄)。✔実読(方向のみ)
3. **態度・信念は逆に速い。** 説得効果は「小さく・速く減衰」が支配的所見(Coppock et al. 2020 Sci Adv=59実験34,000人で「small average effects」✔実読)。sleeper effectは条件付きで **d≈0.25**、遅延測定の平均は **18日/24日**(Kumkale & Albarracín 2004 ✔実読)。
4. 既決の**効果キャップ 10⁻⁴〜10⁻³/接触**(リポ内・親検収済)は、説得文献の「平均効果は小さい」所見と**桁で整合**【推測: 直接比較できるpp値は未取得】。
5. **習慣は「速変数」ではなく「緩変数」。** Lally 2010の中央値66日/範囲18-254日(△二次)を素直に読むと、**T1→T0の n は 15(半飽和)〜66(95%飽和)回**。週〜月のシミュでは**新規習慣化はほぼ起きない**=習慣表は**初期化で与える**もの。
6. **生活構造の年間変化率(日本・公式統計)**: 離職率 **15.4%**/入職率 **16.4%**(2023・✔実読)、市区町村間移動者 **5,207,746人**(2024・✔実読)=人口比 **約4.2%/年**(親再計算・分母要確認)。合計で**約20%/体/年**。
7. → 週次スケジュール表の改訂は **0.2回/体/年 = 40万体で約219件/日 = 予算の0.005%**。既決U10 §1.2「更新イベントは年率数%」は**低すぎ**(実測は10-20%台)だが、呼数はどちらでも無視可能。
8. **LLM側の「persona drift」は人格変化ではなく実装欠陥。** LLaMA2-70B/GPT-3.5は**8ターンで指示ドリフト**(arXiv 2402.10962 ✔実読)、9ターンの非定型対話でドリフトが出るが「**明示タスク指示つきの台本化対話では完全に消える**」(arXiv 2605.06307 ✔実読)。v2の**1呼=1発話ブロック・max_turns 3・文面凍結**はこの回避条件そのもの。
9. **Generative Agentsは人格文を書き換えない。** 変化は memory stream と reflection(高次記憶)に載る(arXiv 2304.03442 ✔実読)。**「persona文は不変・変化は内省gistで表す」はGA同型**であり、v2の文面凍結・ハッシュ・prefixキャッシュと衝突しない。
10. **推奨**: 親の3層仮説を**採用**。ただし**習慣表を緩変数へ**移す(第3層ではなく第2層)。persona文は不変・変化はgist追記。ドリフト予算を宣言(traitsのΔ=0をpytestゲート)+ ablation「凍結 vs 変化」を第2陣。

---

## Q1. 性格特性の安定性 — 週〜月で固定してよいか

### 1-1. ランクオーダー安定性(Roberts & DelVecchio 2000)✔実読

> "From 152 longitudinal studies, 3,217 test-retest correlation coefficients were compiled. Meta-analytic estimates of mean population test-retest correlation coefficients showed that trait consistency increased from .31 in childhood to .54 during the college years, to .64 at age 30, and then reached a plateau around .74 between ages 50 and 70 when time interval was held constant at 6.7 years."
> — Roberts & DelVecchio (2000), *Psychological Bulletin* 126(1), 3-25. DOI [10.1037/0033-2909.126.1.3](https://doi.org/10.1037/0033-2909.126.1.3) 【✔実読(本文PDF全文を抽出)】

年齢帯別の母集団推定(Table 3・実読値):

| 年齢帯 | ρ | K | N |
|---|---|---|---|
| 6-11.9 | .45 | 29 | 4,053 |
| 12-17.9 | .47 | 32 | 10,951 |
| 18-21.9 | .51 | 45 | 11,340 |
| 22-29 | .57 | 10 | 3,394 |
| 30-39 | .62 | 8 | 1,055 |
| 40-49 | .59 | 11 | 2,711 |
| 50-59 | .75 | 4 | 948 |
| 60-73 | .72 | 6 | 1,385 |

**時間間隔の効果**(v2にとって決定的な部分):

> "Consistent with previous research, the relation between time interval and consistency was negative and of modest size (r = -.20, p < .05)."
> "For example, the average trait consistency over a 1-year period would be .55; at 5 years, it would be .52; at 10 years, it would be .49; at 20 years, it would be .41; and at 40 years, it would be .25." 【✔実読】

**重大な限定条件**(親が必ず押さえるべき点):

> "Second, to emphasize the longitudinal consistency of traits and to diminish potential carry-over effects that could inflate estimates, we included studies with test-retest intervals greater than 1 year." 【✔実読】

→ **このメタ分析には「週〜月」の推定値が存在しない**。1年の .55 が**短期の下限**として使える、というのが正しい読み方。短期の直接値は同論文が引用するCrookのみ:

> "Crook estimated that trait consistency averaged above .80 over several weeks and dropped to around .50 after 6 1/2 years. He also concluded that the drop was negatively accelerated, that is, the drop is fast over the initial months and then stabilizes after approximately 1 year." 【✔実読(Roberts & DelVecchio 内の引用として)】
> ※原典 Crook (1941) は未読=空欄(未確認)。

### 1-2. 平均水準変化(Roberts, Walton & Viechtbauer 2006)✔実読(要旨のみ)

> "People increase in measures of social dominance (a facet of extraversion), conscientiousness, and emotional stability, especially in young adulthood (age 20 to 40)."
> — Roberts, Walton & Viechtbauer (2006), *Psychological Bulletin* 132(1), 1-25. DOI [10.1037/0033-2909.132.1.1](https://doi.org/10.1037/0033-2909.132.1.1)。要旨は University of Illinois 公式ポータル([experts.illinois.edu](https://experts.illinois.edu/en/publications/patterns-of-mean-level-change-in-personality-traits-across-the-li/))で実読。
> 同要旨に**d値の記載はない**(「The abstract does not report specific effect sizes」)→ **累積d値は空欄(未確認)**。92サンプル・「longer studies and studies based on younger cohorts showed greater change」は△二次。

**【推測】**: 20-40歳の20年間で d≈0.2-0.5 級(教科書的な値)としても、線形按分すれば**30日あたり d≈0.001-0.002**。v2の較正精度(TVD 0.078・SRMSE 0.003-0.128級)を**3桁下回る**ため観測不能。ただしこの按分自体に一次根拠はない=**【推測】**。d値の一次取得を親の確認リストに載せる。

### 1-3. 判定

**「週〜月のシミュ期間で性格特性は固定してよい」は可**。根拠の強さは:
- 強(mechanism): 1年で r≈.55 が**下限**、かつ低下は最初の数か月で速く1年で安定 → 週〜月なら r>.80 相当(Crook経由)。
- 中: 平均水準変化は年〜十年尺度で、30日の変化量は測定限界以下【推測】。
- **v2への含意**: `traits[internal_locus/nfc/risk_tolerance]` と `persona文` は**不変核**に置き、シミュ中の書き込みを**静的に禁止**する(経済のtransfer単一APIと同型の「代入禁止」)。これは近似ではなく**文献整合の設計**=`mechanism` タグでよい。

---

## Q2. 態度・信念・選好の変化 — 効果量と持続時間

### 2-1. 単回接触の効果は「小さい」(一次で確認)

> "Evidence across social science indicates that average effects of persuasive messages are small. One commonly offered explanation for these small effects is heterogeneity: Persuasion may only work well in specific circumstances."
> …49広告・59実験・34,000人で "small average effects on candidate favorability and vote"
> — Coppock, Hill & Vavreck (2020), *Science Advances* 6(36): eabc4046. DOI [10.1126/sciadv.abc4046](https://doi.org/10.1126/sciadv.abc4046)。著者公式サイトの要旨ページで実読(science.org本体は403)。
> **具体的なpp値は当該ページに記載がなく取得できず=空欄(未確認)**。

### 2-2. 持続時間(減衰)

- Hill, Lo, Vavreck & Zaller (2013) "How Quickly We Forget: The Duration of Persuasion Effects From Mass Communication", *Political Communication* 30(4). DOI [10.1080/10584609.2013.828143](https://doi.org/10.1080/10584609.2013.828143)。
  **△二次**: 検索要旨が返した「効果の大半は**2週間**で減衰、大統領選では**6週間**まで残存」は本文未取得(tandfonline 403 / escholarship 本文空)。**親の一次確認対象**。

### 2-3. sleeper effect(逆方向の変化)✔実読

> "A meta-analysis of the available judgment and memory data on the sleeper effect in persuasion is presented. According to this effect, when people receive a communication associated with a discounting cue, such as a noncredible source, they are less persuaded immediately after exposure than they are later in time. Findings from this meta-analysis indicate that recipients of discounting cues were more persuaded over time when the message arguments and the cue had a strong initial impact."
> — Kumkale & Albarracín (2004), *Psychological Bulletin* 130(1), 143-172。PMC全文 [PMC3100161](https://pmc.ncbi.nlm.nih.gov/articles/PMC3100161/) で実読。

同ページから取得した数値(**要旨外・親の再確認推奨**): 割引手がかりが**メッセージの後**に来て処理動機が高い条件で **d = 0.25**。遅延測定の平均間隔は **1回目 18日(SD=16)・2回目 24日**。

→ **v2への含意**: 「時間とともに効果が上がる」経路が実在する。ただし条件が細かく(信頼できない出典+高処理動機+手がかりが後置)、**v2の第1陣には入れない**のが妥当。入れるなら `expedient` として素性タグ(知覚契約§1条6)と結合させる。

### 2-4. 広告弾力性・摩耗

- Sethuraman, Tellis & Briesch (2011) "How Well Does Advertising Work? Generalizations from Meta-Analysis of Brand Advertising Elasticities", *JMR* 48(3), 457-471. DOI [10.1509/jmkr.48.3.457](https://doi.org/10.1509/jmkr.48.3.457)。
  **△二次**: 「短期弾力性の平均 **.12**(先行メタ分析の .22 より大幅に低い)・短期751件/長期402件・56研究」は検索要旨のみ。**長期弾力性の値は取得できず=空欄(未確認)**。SAGE本体403。
- **摩耗(wearout)の一次データは取得できず=空欄(未確認)**。

### 2-5. 既存答申(リポ内・親検収済)との整合

`docs/research/v2-ad-information-research.md` の正典値:
- 「1接触あたりの行動変化確率は **10⁻⁴〜10⁻³** のオーダー」(3経路からの独立推定の一致・直接測定ではないと明記済み)
- Shapiro et al. 長期弾力性 中央値 **0.014**
- LLMは人間の **3〜10倍**ナッジに反応(人間9.9pp vs エージェント10〜60pp・17モデル)

**整合判定**: 本レーンで一次確認できた「説得の平均効果は小さい」「効果は2-6週で減衰(△)」は、10⁻⁴〜10⁻³キャップと**方向・桁で矛盾しない**。ただし **pp値の直接照合はできていない**(空欄)ので「整合を確認した」とは書けない。**【推測】: 桁は整合。**

### 2-6. 反復接触の累積則(提案・expedient)

一次根拠のある累積則は**取得できず=空欄(未確認)**。以下は設計提案:

```
belief_i(t+1) = belief_i(t) + κ_i · cap · f(n_exposures_recent)   # cap = 10⁻⁴〜10⁻³(既決)
f(n) = 1 - exp(-λn)        # 逓減(Lallyの漸近曲線と同形・広告の凹型反応と同形)
decay: belief_i → prior_i with half-life τ = 14日   # Hill et al. 2013 の「2週間」由来(△二次)
κ_i = ペルソナtraitsからの決定論的導出(行動契約§4-5と同じ写像規律)
```
**タグ: 全項 expedient**。λ・τ・κ写像は感度試験±50%で「結果を駆動していない」ことを示す。

---

## Q3. 習慣形成と消失 — T1→T0 の n の根拠

### 3-1. Lally et al. 2010(**△二次・親の一次確認必須**)

- Lally, van Jaarsveld, Potts & Wardle (2010) "How are habits formed: Modelling habit formation in the real world", *European Journal of Social Psychology* 40(6), 998-1009. DOI [10.1002/ejsp.674](https://doi.org/10.1002/ejsp.674)
- **本文・要旨ページは取得できず**(Wiley 403 / ScienceOpen 403 / BPS 403 / Semantic Scholar 空)。以下は検索エンジンが返したWiley要旨の断片:
  - 96名が食事・飲料・活動のいずれかの行動を**同一文脈**(例「朝食後」)で12週間毎日実施、SRHIを毎日記入。
  - 「The time it took participants to reach 95% of their asymptote of automaticity ranged from **18 to 254 days**」
  - 中央値 **66日**、自動性は**漸近曲線**に従って増加、**1日抜かしても曲線は壊れない**。
  - 82名が解析可能データ、モデル適合は62名・良好適合39名。
- → **これらの数値は本答申では「未検証」扱い**。親がWiley/UCL Discovery等で一次確認するまで台帳に正典化しないこと。

### 3-2. n の導出(漸近曲線からの再計算・親再計算可能)

Lallyの漸近モデル A(t) = A_max(1 − e^(−kt)) を採ると、95%到達 t=66日 から
- k = ln(20)/66 = **0.0454 /回**
- 半飽和(50%)到達 = ln2/k = **15.3回**
- 80%到達 = ln5/k = **35.4回**
- 範囲18-254日 → k = 0.166 / 0.0118 → 半飽和 **4.2回 〜 58.7回**

→ **T1→T0の n は「閾値をどこに置くか」で 15〜66 回**(個体差は 4〜59 回)。v2は「同一(文脈,行動)対が n 回**連続**一致」なので、**日次行動なら n = 日数と一致**、週次行動なら n=15 でも15週=105日かかる。

### 3-3. v2設計への含意(重要)

- **週〜月のシミュ期間では、新規のT1→T0習慣化はほぼ発生しない。** n=15でも日次行動で15日、n=66なら2か月超。30日ランで生まれる新習慣は日次行動に限られ、かつ数はごく少ない。
- → **習慣表(T0の(文脈,行動)対)は「シミュ中に育つもの」ではなく「初期化で与えるもの」**。母集団合成の週次スケジュール表(U10既決・初回LLM生成)と**同じ層**に属する = **緩変数**。
- → 親の3層仮説のうち「習慣は速変数」という配置は**修正が必要**(§Q6で表を提示)。
- **T1→T0機構自体は残す価値がある**: 30日ランでは「ほとんど発火しない」ことが**正しい挙動**であり、長期ラン(数か月〜年)でだけ効く。**n は expedient のまま、ablation {15, 40, 66} で「主要指標が動かない」ことを示す**のが筋。

### 3-4. 習慣の消失(接触断絶後の減衰)

- **減衰速度の一次データは取得できず=空欄(未確認)。**
- 文脈変化による習慣の断絶は「habit discontinuity hypothesis」として確立: Verplanken, Walker, Davis & Jurasek (2008) "Context change and travel mode choice: Combining the habit discontinuity and self-activation hypotheses", *Journal of Environmental Psychology* 28(2), 121-127. DOI [10.1016/j.jenvp.2007.10.005](https://doi.org/10.1016/j.jenvp.2007.10.005)。
  **△二次**(ScienceDirect/ORCAとも403): 「文脈変化が習慣を乱すと、行動が熟慮的に検討されやすくなる窓が開く」「最近転居した環境配慮的な大学職員は、同程度に配慮的だが転居していない職員より持続可能な通勤をしていた」。
- **v2への接続**: 行動契約§5の「転居後18か月で関係の≈40%入替(Dunbar 2020・mechanism)」と**同じイベントが習慣表もリセットする**、という規則が自然。実装形:
  `ライフイベント(転居/転職/進学) → 影響を受ける(文脈,行動)対をT0からT1へ降格 → 再習慣化はn回`
  降格率は **expedient**(一次根拠なし)。

---

## Q4. 役割・生活構造の変化率(日本の公的統計)

### 4-1. 就業(✔実読)

> 「2023年の入職率は**16.4％**(前年比1.2ポイントの上昇)、離職率は**15.4％**(同0.4ポイントの上昇)」
> 一般労働者: 入職率 **12.1％** / 離職率 **12.1％**、パートタイム労働者: 入職率 **27.5％** / 離職率 **23.8％**
> — 労働政策研究・研修機構(JILPT)『ビジネス・レーバー・トレンド』2024年11月号「入職率、離職率」 https://www.jil.go.jp/kokunai/blt/backnumber/2024/11/c_01.html 【✔実読】(原統計=厚生労働省「雇用動向調査」)

- **転職入職率**: 当該ページに記載なし。検索要旨は「2024年1〜6月の転職入職率は **5.5%**」(△二次)。**空欄(未確認)**。
- 就業構造基本調査(5年周期)の転職者数・転職希望者数は**未取得=空欄(未確認)**。

### 4-2. 転居(✔実読)

> 「市区町村間移動者数」**520万7746人**(2024年)、「都道府県間移動者数」**252万3249人**(2024年)
> — 総務省統計局「住民基本台帳人口移動報告 2024年(令和6年)結果」 https://www.stat.go.jp/data/idou/2024np/jissu/youyaku/index.htm 【✔実読】
> ※前年比の**符号**(1.1%減 vs 増)は取得内容が食い違ったため**空欄(未確認)**。絶対数のみ採用。

**親再計算**: 分母を日本の総人口 約1億2,380万人(2024年10月1日・人口推計)とすると
- 市区町村間移動率 = 5,207,746 / 123,800,000 = **4.21 %/年**
- 都道府県間移動率 = 2,523,249 / 123,800,000 = **2.04 %/年**
→ **分母は本レーンで一次確認していない**(人口推計ページ未読)。分母確定は親の確認リストへ。

### 4-3. 婚姻・離婚

**空欄(未確認)**。検索要旨は「令和6年 婚姻件数 **48万5,063組**・婚姻率(人口千対)**4.0**、離婚件数 **18万5,895組**・離婚率 **1.55**」(△二次)。厚生労働省「令和6年(2024)人口動態統計(確定数)の概況」https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/kakutei24/index.html は**文字化けで本文取得不能**。親がe-Stat(人口動態調査)で一次取得すること。

### 4-4. 週次スケジュール表の改訂頻度(合成)

| イベント | 年率 | 出典の強さ |
|---|---|---|
| 離職(=職場・通勤経路の変化) | **15.4 %/年** | ✔実読(JILPT/雇用動向調査 2023) |
| 転居(市区町村間) | **4.2 %/年** | ✔実読の実数から親再計算(分母未確認) |
| 婚姻 | 0.4 %/年 | △二次(未確認) |
| 進学・卒業 | コホート依存・3月末に集中 | 空欄(未確認) |
| **合計(重複を無視した上限)** | **約 20 %/体/年** | — |

**呼数への含意**:
- 40万体 × 0.20 = **8万件/年 = 219件/日**。1件1呼なら **219呼/日 = 400万呼予算の 0.005%**。**完全に無視できる**。
- 既決 U10 §1.2「更新イベント(転職・引越・進学・関係変化)は**年率数%**」は**過小**(実測は10-20%台)。**訂正提案**: 「年率約20%(離職15.4%+転居4.2%+その他)」。呼数結論は変わらない。
- **設計上の含意**: 週次表の改訂は**年に0.2回/体**=平均**5年に1回**。30日ランでは 40万体中 約6,600体(1.6%)が改訂を経験する。これは「シミュ中に構造が動く」ことの**観測可能な最小量**であり、ゼロではない。第1陣で機構を入れる価値はある。

---

## Q5. LLMエージェントシムの先行例

### 5-1. Generative Agents(Park et al. 2023)✔実読

> "…store a complete record of the agent's experiences using natural language, synthesize those memories over time into higher-level reflections, and retrieve them dynamically to plan behavior."
> — arXiv [2304.03442](https://arxiv.org/abs/2304.03442) 要旨。25体・observation/planning/reflection の各成分がablationで寄与を示す。

**要点**: GAは**エージェントの識別記述(seed memory)を書き換えない**。変化は memory stream への追記と reflection(高次記憶)として表現される。**「人格文は不変・変化は内省で表す」はGAの設計そのもの**。
※「内省が人格(seed memory)を書き換えるか」を明示的に否定した文は要旨に無い=**厳密には空欄(未確認)**。ただしアーキテクチャ記述に「persona書き換え」成分は現れない。

### 5-2. Generative Agent Simulations of 1,000 People(Park et al. 2024)△二次

- arXiv [2411.10109](https://arxiv.org/abs/2411.10109)。**△二次**: 1,052名の実在人物のインタビューからエージェントを作り、「GSSの回答を、**本人が2週間後に自分の回答を再現する精度の85%**で再現」。
- **v2にとって最重要の含意**: 「**人間自身の2週間後の一致率が上限**」= 態度・意見の**短期不一致は人間側にも大量にある**。ペルソナを変化させなくても、**測定ノイズ相当の揺らぎ**が現実側に存在する。**較正の上限**として使える。**親の一次確認対象**。

### 5-3. AgentSociety(2025)△二次

- arXiv [2502.08691](https://arxiv.org/abs/2502.08691)。10k超のエージェント・500万インタラクション。エージェントは「emotions, needs, motivations, and cognitive abilities」を持つ。
- → **速変数(感情・欲求)は持つが、性格特性を変化させる記述は確認できず=空欄(未確認)**。
- リポ内既決(母集団合成答申・親検収済): AgentSocietyの空間再現は **CPC=0.088**(Paris)= 移動はエンジンで拘束すべき、という判断の根拠。

### 5-4. persona drift(長期対話での人格漂流)— **実装欠陥であって人格変化ではない**

> "significant instruction drift within eight rounds of conversations" / models: "LLaMA2-chat-70B and GPT-3.5" / cause: "the transformer attention mechanism plays a role, due to attention decay over long exchanges" / fix: "a lightweight method called split-softmax"
> — Li, Chen et al., "Measuring and Controlling Instruction (In)Stability in Language Model Dialogs", arXiv [2402.10962](https://arxiv.org/abs/2402.10962) 【✔実読】

> "within-conversation drift occurs in unscripted dialog for high and moderate ADHD personas"(9ターン・N=3,952)/ "**Scripted interactions with explicit task prompts eliminate this drift entirely.**" / "Self-reported characteristics remain stable for high intensities"(between-conversation N=4,968・5 LLM・3プロンプト設計)
> — "LLM-Based Educational Simulation: Evaluating Temporal Student Persona Stability Across ADHD Profiles", arXiv [2605.06307](https://arxiv.org/abs/2605.06307) 【✔実読】

**v2への含意(強い)**:
1. ドリフトは **8-9ターン**で顕在化する。v2は**1呼=1発話ブロック・max_turns=3呼/体(往復6呼)**(行動契約§3)なので**構造的に閾値の内側**。
2. ドリフトを**完全に消す条件が「明示タスク指示つきの台本化対話」**= v2の**文面凍結(知覚契約§1条5)+決定論テンプレ+2行形の出力規約**そのもの。**既決の設計がドリフト対策として一次根拠を持つ**ことになる。これは台帳に書ける新事実。
3. 逆に言えば、**ペルソナ文を「変化させる」設計はドリフトと区別がつかなくなる**。意図した変化と実装欠陥の切り分けができない = 検証不能。

### 5-5. ペルソナ文を書き換える設計(evolving persona)△二次

- PersonaAgent(arXiv [2506.06254](https://arxiv.org/abs/2506.06254)): 「persona serving as a unique system prompt for each user that continuously evolves by integrating user-data-driven memory」。episodic memory + semantic memory。
- EconAI(arXiv [2605.13762](https://arxiv.org/abs/2605.13762)): 「Dynamic Persona Evolution and Memory-Aware Agents in Evolving Economic Environments」。
- いずれも**要旨のみ(△二次)**。**個人化(personalization)が目的**であり、**社会シミュレーションの妥当性検証**の文脈ではない。

**コスト面の否定材料**(v2固有):
- persona文が**system prompt に載る**設計では、個体ごとに文面が変わる = **共有静的prefix(B0/B1)を壊す**。BN-2C実測(知覚契約§2.2)では **個体末尾300→800tokで −8.1%/100tok**、逆に**個体→共有へ200tok移すと +23.8%**。persona文を可変にして個体ブロックへ押し込むと、**スループットが直接削られる**。
- 文面凍結(§1条5)は「ペルソナ文面の中立化だけで毒性が46.7%動く」実測を根拠にしている。**可変persona文はこの実測が示す感度をランごとに再現不能にする**。
- ハッシュ版管理(B2/B4のバイト列ハッシュ=prefixキャッシュキー=変化検出器=dormant再送抑止の三役)と衝突する。

---

## Q6. 推奨

### (a) 3層設計 — **採用。ただし習慣表を第2層(緩変数)へ移す**

| 層 | 中身 | 更新規則 | 時間尺度 | 30日ランでの期待変化 | 追加呼数 | タグ |
|---|---|---|---|---|---|---|
| **L0 不変核** | persistent_id・出生コホート・性別・国籍・`traits[internal_locus/nfc/risk_tolerance]`・**persona文**・§4-5の個体係数(記憶転写重み・関係辺Δ・半減期) | **書き込み静的禁止**(代入禁止API)。年齢のみ誕生日で+1 | シミュ全期間 | **0(ゲートで強制)** | 0 | **mechanism**(Roberts&DelVecchio: 1年で r≈.55 が下限・週〜月は>.80相当) |
| **L1 緩変数** | 役割・住所・職場・通学先・**週次活動スケジュール表**・関係辺の集合(層配置)・**習慣表(T0の(文脈,行動)対)** | **ライフイベント駆動のみ**(離散・イベント時に1呼で改訂)。習慣はT1→T0の n 回一致で追加、ライフイベントでT1へ降格 | 月〜年 | 約1.6%の個体が週次表改訂(=6,600体)。新規T0は日次行動に限りごく少数 | **219呼/日 = 予算の0.005%** | mechanism(公的統計: 離職15.4%/年・転居4.2%/年)/ n と降格率は expedient |
| **L2 速変数** | 内受容3変数・エピソード記憶・日次内省gist・**信念/態度**・**選好**・関係辺の**強度**・直前の結果 | 日次内省(就寝同期・既決)+ 事象駆動の増分。減衰は半減期で | 日 | 記憶12本の入替・gist最大3/晩・態度は10⁻⁴〜10⁻³/接触の累積 | **0(既決の内省呼に相乗り)** | mechanism(枠=ACT-Rべき減衰・既決)/ 効果量は expedient |

**この配置の要点**:
- 親の仮説からの唯一の変更は **習慣表を L2 → L1** に移すこと。根拠は Lally の 15-66回(§Q3-2)。**週〜月のシミュでは習慣は動かない**ので、速変数として扱うと「動くはずのものが動かない」という誤った期待を設計に埋め込む。
- 「関係」も分割する: **辺の集合(誰と繋がっているか)= L1**、**辺の強度 = L2**。行動契約§5の「平時入替1%/年(mechanism)」は L1 の年率、「発話ブロックごとに+Δ・非接触で半減期90日」は L2 の日次。**既決がすでにこの分割になっている**ので追加決定は不要。

### (b) persona文は**不変**・変化は**内省gistの追記**で表す — 推奨

**採用理由(4点)**:
1. **Generative Agents 同型**(§5-1 ✔実読)。変化は memory stream + reflection に載る。
2. **drift と区別がつく**。persona文を凍結すれば、観測される行動変化は「記憶・状態の変化」に一意に帰属する。可変にすると arXiv 2402.10962 のドリフトと切り分け不能(§5-4)。
3. **文面凍結宣言(知覚契約§1条5)と整合**。ハッシュ版管理・prefixキャッシュ・dormant再送抑止の三役が保たれる。
4. **コスト**。個体ブロックの増加は −8.1%/100tok(BN-2C実測)。可変persona文は個体ブロックを膨らませる方向にしか効かない。

**実装形**:
```
persona文(不変・L0)          … B0/B1側の役割テンプレに載る固定文字列。ハッシュで版管理。
自己記述gist(可変・L2)        … 日次内省の最大3 gistのうち、自己言及型を「近況」枠に最大2本・各1-2文で保持。
                                観測プレフィクスB5(220tok)の内数に収める(予算増ゼロ)。
                                古い自己記述gistはACT-R A(m)で自然に落ちる(既決の d=0.25 ブースト対象)。
```
→ **「ペルソナが変化した」ように見える現象は、persona文の書き換えではなく "近況gist 2本 + 関係辺 + 習慣表 + 選好ベクトル" の変化として表現される**。

### (c) ドリフト予算(状態成長宣言との接続)+ ablation

**ドリフト予算の宣言(性能予算・バイト予算と同じ様式で、機能追加前に宣言しテストでゲート)**:

| 量 | 30シミュ日あたりの上限 | 検査 | 違反時 |
|---|---|---|---|
| `traits` ベクトルの変化 | **L∞ = 0(厳密不変)** | pytest: 全体のtraitsハッシュがrun前後で一致 | ゲート失敗(赤) |
| persona文 | **バイト一致(ハッシュ不変)** | pytest: persona文ハッシュ一致 | ゲート失敗(赤) |
| 選好ベクトル(店・経路・商品カテゴリ) | **L1 ≤ 0.10**(全体の10%以内) | 月次センサスに列追加・分布の分位点で監視 | 警告→キャップ発火回数を記録 |
| 態度/信念スカラー | 1接触 ≤ **10⁻³**(既決キャップ)・30日累積 ≤ **0.05** | 接触ログから累積を集計 | 警告 |
| 習慣表の項目入替 | **≤ 1件/体/30日** | T0昇格・降格の計数 | 警告 |
| 関係辺の集合の入替 | 平時 **≤ 1%/年**、ライフイベント後18か月で **≤ 40%**(既決・Dunbar) | 既決の監視に相乗り | 警告 |
| **バイト予算への影響** | 近況gist 2本 = 既決6.1KB/体の**内数**(12本×260Bの枠内) | 既存のバイト予算テスト | 増加なら赤 |

**ablation「凍結ペルソナ vs 変化ペルソナ」**(第2陣・第1陣は凍結のみ):
- **A(既定)**: L0凍結 + L1イベント駆動 + L2日次(推奨案)
- **B(全凍結)**: L2の信念・選好も凍結(記憶だけ蓄積)→ **下限対照**
- **C(persona可変)**: 日次内省でpersona文自体を書き換える(30日で最大30回改版)→ **上限対照**
- 判定指標: 既決の3本(**移動分布・経済フロー・情報伝播**)+ holdoutの形状5指標(KDDI相関・ピーク時刻・平日休日比・エリア構成・属性構成)。
- **合格条件**: A と B の差が holdout 指標で**有意かつ現実側の方向**に出ること(=変化させる意味がある証明)。A と C の差が**出ない**なら、Cは**コストだけ払って何も買っていない**=不採用。
- **付随計測(必須)**: Cではスループット低下(個体トークン増)とprefixキャッシュヒット率低下を必ず記録する。

### (d) expedient 登録簿(本レーン分)

| 項目 | 値/内容 | なぜ expedient か | 検証 |
|---|---|---|---|
| T1→T0 の n | 15〜66回(既定 **40**) | Lallyの漸近曲線からの再導出であって、v2の(文脈,行動)対に対する直接測定ではない。かつLally自体が **△二次(未一次確認)** | ablation {15, 40, 66}・主要3指標が動かないこと |
| 態度の反復則 f(n)=1−e^(−λn) | λ 未定 | 累積則の一次根拠なし(空欄) | 感度試験 ±50% |
| 態度の減衰半減期 τ | 14日 | Hill et al. 2013 の「2週間」由来だが**本文未確認** | 一次確認後に mechanism 昇格候補 |
| ライフイベント→習慣降格率 | 未定(初期 30%) | 先例なし | 感度試験 |
| 選好ベクトルのドリフト上限 L1≤0.10 | 自前宣言 | 文献値なし(コードン±10%と同じ性質) | 感度試験・宣言として記録 |
| 近況gist 2本 | 自前宣言 | GAは本数を規定していない | バイト予算テスト |
| sleeper effect(不採用) | 第1陣は入れない | 条件が細かく較正不能 | — |
| 週次表改訂率 約20%/年 | 離職15.4%+転居4.2%の単純和 | **重複(転職と転居の同時発生)を無視した上限** | 就業構造基本調査で照合 |

**mechanism と主張してよい項**: L0凍結の妥当性(Roberts & DelVecchio ✔実読)、L1の年率(雇用動向調査・住民基本台帳人口移動報告 ✔実読)、persona文凍結がドリフト対策になること(arXiv 2605.06307 の「scripted → drift消滅」✔実読)。

---

## Q7. 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 引用(本レーンが得た文字列) | 親が確認すべき数値 | 現状 |
|---|---|---|---|---|---|
| 1 | 性格特性は1年間隔で r≈.55、週〜月では >.80 相当 | https://doi.org/10.1037/0033-2909.126.1.3 (本文PDF: http://jenni.uchicago.edu/Spencer_Conference/Representative%20Papers/Roberts%20&%20DelVecchio,%202000.pdf) | 「trait consistency increased from .31 in childhood to .54 during the college years, to .64 at age 30, and then reached a plateau around .74 between ages 50 and 70 when time interval was held constant at 6.7 years」/「we included studies with test-retest intervals greater than 1 year」/「Crook estimated that trait consistency averaged above .80 over several weeks」 | ①1年=.55 / 5年=.52 / 10年=.49 の記述 ②**1年未満を除外した**という限定条件 ③Crook 1941 は孫引きであること | **✔本レーンで実読済**(親は追認のみでよい) |
| 2 | 新習慣の自動化は中央値66日・範囲18-254日 → n=15〜66 | https://doi.org/10.1002/ejsp.674 | (Wiley要旨の断片・**本文未取得**)「ranged from 18 to 254 days」「median 66 days」「missing a single day did not break the curve」 | ①中央値66日が**95%漸近到達**の中央値であること ②96名/解析82名/良好適合39名 ③1日欠落の頑健性 | **△二次・要一次確認**(Wiley 403。UCL Discovery か図書館経由) |
| 3 | 説得効果は2週間で大半が減衰・6週間まで一部残存 | https://doi.org/10.1080/10584609.2013.828143 | (検索要旨のみ・**本文未取得**)「effects mostly decay over a period of 2 weeks」「some effect in the presidential campaign endures for at least 6 weeks」 | ①減衰の関数形と半減期の数値 ②「2週間」が半減期なのか消失なのか | **△二次・要一次確認**(tandfonline 403 / escholarship 本文空) |
| 4 | 台本化された明示タスク対話ではペルソナドリフトが消える(=v2の文面凍結の一次根拠) | https://arxiv.org/abs/2605.06307 / https://arxiv.org/abs/2402.10962 | 「Scripted interactions with explicit task prompts eliminate this drift entirely」(2605.06307)/「significant instruction drift within eight rounds of conversations」(2402.10962) | ①「8ターン」の測定条件(モデル・指標) ②2605.06307のN(4,968/3,952)と9ターンという設定 ③v2のmax_turns=3(往復6呼)が本当に閾値の内側か | **✔要旨実読済**(親は本文で条件を確認) |
| 5 | 日本の生活構造の年間変化率(週次表改訂の根拠) | https://www.jil.go.jp/kokunai/blt/backnumber/2024/11/c_01.html / https://www.stat.go.jp/data/idou/2024np/jissu/youyaku/index.htm | 「2023年の入職率は16.4％…離職率は15.4％」/「市区町村間移動者数 520万7746人」「都道府県間移動者数 252万3249人」 | ①**転職入職率**(離職率≠転職率)の正しい値 ②移動率の**分母**(人口推計の総人口)を確定し 4.2%/年 を再計算 ③**婚姻件数48万5,063組・婚姻率4.0**(本レーン未確認)をe-Statで取得 | **✔2件実読・婚姻と転職入職率は空欄(未確認)** |

**追加の未取得項目(空欄・優先度中)**:
- Roberts et al. 2006 の**累積d値**(要旨に記載なし。本文 Table が必要)→ 「30日でd≈0.001」の【推測】を裏づける/否定する
- Sethuraman et al. 2011 の**長期弾力性**(短期 .12 は△二次、長期は空欄)
- 広告の**摩耗(wearout)**の一次データ(空欄)
- 習慣の**消失速度**の一次データ(空欄。habit discontinuity は「窓が開く」だけで減衰率を与えない)
- Park et al. 2024 の「本人の2週間後の再現性の85%」の**一次確認**(較正上限として使うなら必須)

---

## 参照一覧

**✔実読(本文または要旨ページを取得して引用)**
1. Roberts, B. W., & DelVecchio, W. F. (2000). The rank-order consistency of personality traits from childhood to old age. *Psychological Bulletin*, 126(1), 3-25. DOI [10.1037/0033-2909.126.1.3](https://doi.org/10.1037/0033-2909.126.1.3)
2. Roberts, B. W., Walton, K. E., & Viechtbauer, W. (2006). Patterns of mean-level change in personality traits across the life course. *Psychological Bulletin*, 132(1), 1-25. DOI [10.1037/0033-2909.132.1.1](https://doi.org/10.1037/0033-2909.132.1.1) — 要旨のみ(University of Illinois 公式ポータル)
3. Kumkale, G. T., & Albarracín, D. (2004). The sleeper effect in persuasion: A meta-analytic review. *Psychological Bulletin*, 130(1), 143-172. [PMC3100161](https://pmc.ncbi.nlm.nih.gov/articles/PMC3100161/)
4. Coppock, A., Hill, S. J., & Vavreck, L. (2020). The small effects of political advertising are small regardless of context, message, sender, or receiver. *Science Advances*, 6(36), eabc4046. DOI [10.1126/sciadv.abc4046](https://doi.org/10.1126/sciadv.abc4046) — 著者公式サイトの要旨で実読
5. Park, J. S., et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. arXiv [2304.03442](https://arxiv.org/abs/2304.03442)
6. Measuring and Controlling Instruction (In)Stability in Language Model Dialogs. arXiv [2402.10962](https://arxiv.org/abs/2402.10962)
7. LLM-Based Educational Simulation: Evaluating Temporal Student Persona Stability Across ADHD Profiles. arXiv [2605.06307](https://arxiv.org/abs/2605.06307)
8. 労働政策研究・研修機構(JILPT)「入職率、離職率」*ビジネス・レーバー・トレンド* 2024年11月号 https://www.jil.go.jp/kokunai/blt/backnumber/2024/11/c_01.html (原統計=厚生労働省「雇用動向調査」)
9. 総務省統計局「住民基本台帳人口移動報告 2024年(令和6年)結果」 https://www.stat.go.jp/data/idou/2024np/jissu/youyaku/index.htm

**△二次(要旨断片のみ・本文未取得=親の一次確認対象)**
10. Lally, P., van Jaarsveld, C. H. M., Potts, H. W. W., & Wardle, J. (2010). *European Journal of Social Psychology*, 40(6), 998-1009. DOI [10.1002/ejsp.674](https://doi.org/10.1002/ejsp.674)
11. Hill, S. J., Lo, J., Vavreck, L., & Zaller, J. (2013). *Political Communication*, 30(4). DOI [10.1080/10584609.2013.828143](https://doi.org/10.1080/10584609.2013.828143)
12. Sethuraman, R., Tellis, G. J., & Briesch, R. A. (2011). *Journal of Marketing Research*, 48(3), 457-471. DOI [10.1509/jmkr.48.3.457](https://doi.org/10.1509/jmkr.48.3.457)
13. Verplanken, B., Walker, I., Davis, A., & Jurasek, M. (2008). *Journal of Environmental Psychology*, 28(2), 121-127. DOI [10.1016/j.jenvp.2007.10.005](https://doi.org/10.1016/j.jenvp.2007.10.005)
14. Park, J. S., et al. (2024). Generative Agent Simulations of 1,000 People. arXiv [2411.10109](https://arxiv.org/abs/2411.10109)
15. Piao, J., et al. (2025). AgentSociety. arXiv [2502.08691](https://arxiv.org/abs/2502.08691)
16. PersonaAgent: Bridging Memory and Action for Personalized LLM Agents. arXiv [2506.06254](https://arxiv.org/abs/2506.06254)
17. EconAI: Dynamic Persona Evolution and Memory-Aware Agents. arXiv [2605.13762](https://arxiv.org/abs/2605.13762)
18. 厚生労働省「令和6年(2024)人口動態統計(確定数)の概況」 https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/kakutei24/index.html (文字化けで本文取得不能)

**リポ内の既決・既検収(参照のみ・再検証していない)**
- `docs/research/v2-ad-information-research.md`(10⁻⁴〜10⁻³/接触・Shapiro長期弾力性0.014・LLMのナッジ3-10倍増幅)
- `docs/design/v2-cognition-design.md` §3-4(T1→T0のn・ACT-R記憶・日次内省)
- `docs/design/v2-action-contract.md` §4-5(個体可変パラメータ・Dunbar 2020の1%/年・18か月40%)
- `docs/design/v2-perception-contract.md` §1条5・§2.2(文面凍結・BN-2C実測の個体/共有トークン感度)
- `docs/design/v2-boundary-economy-design.md` §1(週次活動スケジュール表・更新イベント年率)
- `docs/research/v2-population-synthesis-research.md`(traits・a_i・±10-15%の弱い変調)

**未取得(空欄)**: Crook (1941) 原典 / Roberts et al. 2006 の d値 / Sethuraman 長期弾力性 / 広告wearoutの一次データ / 習慣消失速度の一次データ / 転職入職率 / 婚姻件数・婚姻率の一次確認 / 就業構造基本調査 / 人口推計の総人口(移動率の分母)
