# レーンA答申: 知覚契約書§3「人物③ 顕著な行為」の到達確率 p_notice の関数形

> **親検収(Fable・2026-09-06)**: 出典を親が一次確認した。✔=親が実読して数値一致。
> - ✔ Fotios, Yang & Uttley 2015(White Rose PDFをpymupdfで実読): 全体中央値10.3 m(IQR 8.3-12.3)・昼13.0 m/夜8.9 m・注視480 ms(IQR 400-640)・177人観察・提案15 m/500 ms。
> - ✔ Sandia SAND2015-6368(osti.gov PDF実読): 式(2)(3) P∞=(N/N50)^E/(1+(N/N50)^E), E=2.7+0.7(N/N50)・「動く標的のN50は静止の2/3」・「低クラッタN50=0.5→高クラッタ2.5」を逐語確認。**P1表(d50=40 m)は親が再計算し全値一致**(10 m 0.9995・40 m 0.500・60 m 0.217・80 m 0.108・100 m 0.061・200 m 0.010・215 m 0.0085)。
> - ✔ Hill型フィット m=0.92・T=1.2・k=1.05(Jorjafki, Sagarin & Butail 2018, J R Soc Interface 15:20180335・PMC実読。関数形の提案はGallup et al. 2012に帰属)。**Milgram 1969の42%/86%は親が原典未確認**(PNAS/APAは403・リダイレクト)。ただしフィット値から再現するとP(1)=0.42・P(15)=0.86で整合する。
> - ✔ Hyman et al. 2010の携帯通話者25%(WWU公式ニュース実読)。群別内訳・nは空欄のまま。
> - 案B(2段Hill)の d50=40 m・m_density・打ち切り80 m・叫び声の到達4-13 mは**答申の導出=expedient**(答申自身が宣言)。
> - 正典化: docs/research/v2-p-notice-research.md(R3-8 §3-1の根拠)。


作成: 2026-09-06 / リサーチサブ(Opus 5) / 検収=親(Fable)・決定=ユーザー

---

## 要約(10行)

1. **最重要の実測**: 歩行者が他の歩行者を実際に注視する距離の中央値は **10.3 m**(IQR 8.3–12.3 m)、注視時間の中央値は **480 ms**(Fotios, Yang & Uttley 2015・実路上アイトラッキング)。**100 m セルは「対人観察の作用半径」より一桁大きい**。「同一セル=一律 p_notice」は物理的に誤り。距離項は必須。
2. 昼夜比は同研究で **昼 13.0 m / 夜 8.9 m**(比 0.68)。照明係数の一次エビデンスがここにある。
3. 距離→検出確率の関数形は、軍用目標捕捉の **TTPF**(Sandia SAND2015-6368 式2-3)が最も枯れている: `P = s^E/(1+s^E), E = 2.7+0.7s`(s = 解像サイクル比 ∝ 1/距離)。**ロジスティックではなく Hill 型**。
4. 群衆密度は**二方向**に効く。下げる側=クラッタ(低クラッタ N50=0.5 → 高クラッタ 2.5、必要解像度5倍)と遮蔽。上げる側=社会的手がかり。
5. 上げる側の一次データは Milgram, Bickman & Berkowitz 1969: 見上げる人1人で通行人の **42% が見上げ・4% が停止**、15人で **86% が見上げ・40% が停止**(N=1,424、50フィート歩道、30試行)。
6. その Milgram データに **同型の Hill 関数**がフィット済み: `P(N) = 0.92·N^1.05/(1.2^1.05 + N^1.05)`(Royal Society Interface 2018)。**距離項と社会項が同じ関数族**で書けるのは大きい。
7. 偏心は視力式 `f_a = f·E2/(E+E2)`(achromatic E2 ≈ 6.22°)。「背後=一次視覚ゼロ、聴覚と社会的手がかりのみ」は**近似として妥当**(ただし注視方向は 480 ms で移る=expedient)。
8. 課題従事は Hyman et al. 2010: 携帯通話者で一輪車ピエロに気づいた割合 **25%**、非携帯群は 50% 超(群別の内訳は一次未確認=空欄)。
9. ゲームAI(CryENGINE TTPS / Alien: Isolation / The Last of Us / Splinter Cell: Blacklist)は**全て段階錐+レイキャスト+時間エンベロープ**。16体の総当りで 136 レイキャスト→購読フィルタで 16 に削減、という計算量の実話が輸入価値。**40万体でレイキャストは不可**。
10. **推奨=案B「2段Hill」**: 一次検出(TTPF距離×乗法係数)+ 二次検出(Milgram Hill の社会伝播)。パラメータ7個・レイキャストなし・イベントあたり O(近傍セル在席者)。親案の「距離3段×密度2段の固定表」は案Bの離散化(LUT)として保持可=ablation A1 の位置づけ。

---

## 問い1. 距離依存

### 1-1. 直接の実証(最重要・一次確認済)

**Fotios S, Yang B, Uttley J (2015) "Observing other pedestrians: Investigating the typical distance and duration of fixation", Lighting Research & Technology 47(5): 548–564. doi:10.1177/1477153514529299**
(White Rose 版: https://eprints.whiterose.ac.uk/89559/ — 本文読了)

モバイルアイトラッカーで実路上を歩く被験者 n=40、昼と夜、2ルート。他の歩行者への**注視が発生した距離**の実測。

> "Overall, the median fixation distance was 10.3 m (inter-quartile range 8.3–12.3 m)."

> "Median fixation distances were shorter after dark (8.9 m) than during daytime (13.0 m)."

Table 2(ルート別・抜粋):

| ルート | 昼 中央値 | 昼 IQR | 夜 中央値 | 夜 IQR |
|---|---|---|---|---|
| Difficult | 11.6 m | 8.6–13.7 | 8.9 m | 7.4–10.2 |
| Unfamiliar | 19.1 m | 14.1–27.4 | (抽出テキストが途切れ・空欄) | — |

上四分位:

> "In the current data, the upper quartiles were 15.3 m for daytime trials and 10.3 m for after dark trials."

注視時間:

> "The overall median duration of observation was 480 ms (inter-quartile range 400–640 ms)."

結論(要旨):

> "We propose that further work on interpersonal judgements should examine the effects of lighting at a distance of 15 m with an observation duration of 500 ms."

独立研究(Davoudian & Raynham、夜間・n=15・55人の遭遇)の再解析も同論文が引用:

> "Distances at which fixations occurred ranged from 10 m to over 50 m, with a median of 20 m"

**設計含意(最重要)**: 「顕著な行為への気づき」の作用半径は **10–20 m オーダー**。100 m セルの端(≈70–140 m)は事実上ゼロ。**セル内一律は棄却される**。

### 1-2. 工学的正典: Johnson 基準と TTPF(一次確認済)

**Sjaardema TA, Smith CS, Birch GC (2015) "History and Evolution of the Johnson Criteria", SAND2015-6368, Sandia National Laboratories.** https://www.osti.gov/servlets/purl/1222446 (PDF本文読了)

> "P(t) = P∞[1−e^(−t/τ_FOV)]  (1)
> P∞ = (N/(N50)_D)^E / (1 + (N/(N50)_D)^E)  (2)
> E = 2.7 + 0.7(N/(N50)_D)  (3)"

変数(同 Table 2): N = 標的上の解像サイクル数、(N50)_D = 50% 検出に要するサイクル数、τ_FOV = 標的発見までの平均時間。

N は標的の角サイズに比例 ∝ 1/距離。よって **s ≡ N/N50 = d50/d** と置けば、式(2)(3) はそのまま**距離の関数**になる。**式(1)の時間項は本件では不要**(§3 は発生tickでの一発ベルヌーイが既決)。

Johnson 原典のサイクル数(サーチ結果・原典は一次未確認): 検出 1.0 ± 0.25 / 認識 4.0 ± 0.8 / 識別 6.4 ± 1.5 サイクル。ACQUIRE 版の検出 = 0.75 サイクル(SAND 本文 Table 4 で確認)。

**動く標的の補正(一次確認済)**:

> "Traditionally, however, for moving targets, the N50 is 2/3 the value for an equivalent static target."

→ 「倒れる・暴れる・走る」は静止対象より **1.5 倍の距離**で検出可能。event_class 係数の根拠。

**含意**: 「誰が何をしているか判る距離(recognition, 4 cycles)」と「何かが起きたと判る距離(detection, 1 cycle)」の比は **4:1**。Fotios の 15 m は前者(対人判断のための注視)なので、**顕著な行為の検出距離 d50 は 15 m の 1〜4 倍のレンジ**にあると導出できる(問い6で使用)。

### 1-3. CCTV 監視(参考・二次)

IEC/EN 62676-4 の DORI 画素密度基準: Detection 25 px/m、Observation 62、Recognition 125、Identification 250(サーチ結果・**規格本文は一次未確認**)。人間観察者の課題難度の**序列**が Johnson と一致することの傍証にとどまる。

### 1-4. 空欄(未確認)

- **「人が倒れる/叫ぶ」への気づき率を距離を系統的に振って測った実験は発見できず**。Hyman 2010 のピエロも距離を操作していない。bystander 研究(Latané & Darley 系、Levine の CCTV 実暴力研究)は**介入率**の研究であり**検出率**を測っていない。
- → **距離依存の直接エビデンスは存在しない。距離項は「視覚系の一般法則(TTPF)+ 実測された対人注視距離(Fotios)」からの外挿であり、expedient である**。

---

## 問い2. 密度依存

### 2-1. 下げる側

**(a) クラッタが必要解像度を上げる(一次確認済・SAND2015-6368)**

> "For scenes with low clutter, for 50% probability of detection, N50 was 0.5 and for high clutter it was raised to 2.5."
(Schmieder & Weathersby 1983 の実験結果として引用)

Detect05 モデルのクラッタ係数:

> "For low, medium-low, medium, and high amounts of clutter, C is 1, 1.5, 2.0, and 2.7 respectively. N50 = 0.75C[(C/ΔT_RSS)^2 + 1]"

→ **高クラッタは N50 を 5 倍(= d50 を 1/5)にする**。群衆密度をクラッタに写像するのは自然だが、写像自体に根拠はない(expedient)。

**(b) 遮蔽**: 群衆映像の遮蔽度分類は Fully-Visible (0–15%) / Partially-Occluded (15–50%) / Largely-Occluded (50–85%) / Fully-Occluded (85–100%) の4段が使われ、"High-density sequences exhibit severe occlusions, while low/medium-density situations do not"(サーチ結果・**一次未確認**)。

**(c) 視覚探索のセットサイズ効果**: 特徴で分離できない探索は **20–40 ms/item**(target-present)、spatial configuration 探索は **25–50 ms/item**(Wolfe 系。サーチ結果・**一次未確認**)。注視時間が 480 ms しかない(Fotios)ことと合わせると、**1回の注視で走査できる人数は10人前後が上限**という粗い上界が引ける(480/40 ≈ 12)。【推測】この解釈は本答申の独自導出であり、文献の主張ではない。

### 2-2. 上げる側(社会的手がかり)— 一次確認済・最強のエビデンス

**Milgram S, Bickman L, Berkowitz L (1969) "Note on the drawing power of crowds of different size", Journal of Personality and Social Psychology 13(2): 79–82.**(PDF全文読了。DOI は **空欄(未確認)**)

方法(verbatim):

> "The subjects were 1,424 pedestrians on a busy New York City street who passed along a 50-foot length of sidewalk during thirty 1-minute trials."

> "The stimulus crowds were composed of 1, 2, 3, S[=5], 10, and 15 persons."

結果(verbatim):

> "While 4% of the passersby stopped alongside a single individual looking up, 40% of the passersby stopped alongside a stimulus crowd of IS[=15]."

> "While one person induced 42 % of the passersby to look up (whether or not they also stopped), the stimulus crowd of IS[=15], all looking in the same direction, caused 86% of the passersby to orient themselves in the same direction"

トレンド解析(verbatim):

> "There is a significant linear trend (F = 101.7, p < .01) and a nonsignificant quadratic trend (F = .42) for the passersby who stopped. However, for the passersby who looked up, there are both significant linear (F = 57.2, p < .01) and quadratic (F = 11.6, p < .01) components."

**設計上決定的な数値: 刺激群衆が1人でも 42% が視線を追従する。** これは単独で「観測が届く/届かない」を決めるほど強い。

著者自身が挙げる注意点(2件・verbatim):

> "the size of the stimulus crowd increased as soon as persons joined it. Thus, the effect of a stimulus crowd of constant size was not studied."

> "passersby were oriented by the gaze of the crowd to a scene that had no special holding power. ... If, instead, an acrobat were performing on the building ledge, the interest of the scene would likely hold crowd members for a longer period"

→ **上限バイアス(群衆が成長するので大サイズの効果が過大)と下限バイアス(退屈な刺激なので「倒れた人」ならもっと強い)が同時にある**。差し引きは不明。

なお観測区間は **50 フィート(≈15 m)の歩道**であり、問い1の「対人観察の作用半径 10–20 m」とよく一致する。**社会項は「同一セル」ではなく「半径15m程度」の局所量として実装すべき**ことの傍証。

### 2-3. 関数形の既存フィット(Hill 型・確認済)

**"Drawing power of virtual crowds", J. R. Soc. Interface 15(145): 20180335 (2018). doi:10.1098/rsif.2018.0335**(著者名は **空欄(未確認)**。royalsocietypublishing.org は 403、https://pmc.ncbi.nlm.nih.gov/articles/PMC6127183/ 経由で取得)

> "the proportion of crowd looking up as a function of the stimulus size N is P(N) = mN^k/(T^k + N^k)"

- VR 実験のフィット: **m = 1, T = 0.7, k = 1.7**
  > "Fitting this model to our data by minimizing the sum of square error between values predicted by this model and those obtained in the experiment, we get a values of m = 1, T = 0.7 and k = 1.7"
- **Milgram 1969 実データへの同モデルのフィット: m = 0.92, T = 1.2, k = 1.05**
  > "By contrast, when the authors in [7] fitted the same model to data from Milgram et al. [6], the values were m = 0.92, T = 1.2 and k = 1.05"
- VR 側が急峻な理由として近接性と HMD の視野(110°)を挙げている。

**→ そのまま実装可能な社会伝播項が既に存在する。** k = 1.05 ≈ 1 なので実質 Michaelis–Menten 型: `P2(N) ≈ 0.92·N/(1.2+N)`。N=1 で 0.42、N=15 で 0.85 → **Milgram の実測 42%/86% を再現する**。

### 2-4. 結論(密度)

密度は**単一の係数にしてはならない**。
- 一次検出(自力での気づき)には**負**に効く(クラッタ・遮蔽)。
- 二次検出(他人の反応を見て気づく)には**強く正**に効く。
- ネット効果は密度の非単調関数になる可能性が高い。**符号を決め打ちせず、創発の観察対象として残す**(自然界模倣ドクトリンに適合)。

---

## 問い3. 向き・偏心

### 3-1. 偏心と解像の代表式(確認済)

**Haun AM (2021) "What is visible across the visual field?", Neuroscience of Consciousness 2021(1): niab006. doi:10.1093/nc/niab006**(https://pmc.ncbi.nlm.nih.gov/articles/PMC8167368/ 経由)

> "f_a = f * E2/(E + E2)"

E2 定数: **achromatic E2 = 6.22°**、Blue/Yellow 6.22°、Red/Green 1.82°。
コントラスト感度について:

> "Contrast sensitivity for a target of any spatial frequency declines exponentially with eccentricity, with a steeper exponent for higher spatial frequencies"

→ 偏心角 E での実効解像は中心の **E2/(E+E2)** 倍。E2 = 6.22° として:

| 偏心角 E | 0° | 10° | 20° | 30° | 60° | 90° |
|---|---|---|---|---|---|---|
| m_ecc | 1.00 | 0.38 | 0.24 | 0.17 | 0.094 | 0.065 |

TTPF の s に掛ければ偏心係数がそのまま得られる(`s_eff = s · m_ecc`)。**パラメータ1個(E2)で偏心が入る**のは実装上きわめて安い。

### 3-2. 周辺視の運動検出(二次・一次未確認)

角速度の運動検出閾値: 偏心 54.3° で約 0.5 °/s、72.6° で 1.2–1.5 °/s、90° で 2.1 °/s(Motion Detection in the Far Peripheral Visual Field, govinfo GOVPUB-D101-PURL-gpo84675。**サーチスニペットのみ・一次未確認**)。

→ 周辺視は**解像は落ちるが運動には残存感度がある**。「倒れる」「走り出す」のような大きな運動は周辺視でも拾いうる。E2 だけで減衰させると周辺視の運動検出を過小評価する。**event_class ごとに E2 を変える(運動事象は E2 を大きく=減衰を緩く)のが妥当**だが、この補正の数値的裏付けはない = **expedient**。

### 3-3. クラウディング(Bouma 則・二次)

臨界間隔 `d = b·E + w`(b = Bouma 定数、E = 偏心角、w = y切片)。2パラメータ Bouma 則で被験者間分散の 82%、拡張版で 94% を説明(Rosen/Chakravarthi/Pelli 系。サーチ結果・**一次未確認**)。

→ **偏心と密度は独立ではない**。周辺視 + 高密度は乗算的に悪化する。推奨案では `m_ecc × m_density` の単純積で近似 = **expedient**。

### 3-4. 「背後の事象は音でしか届かない」の妥当性判定

**判定: 一次視覚チャネルの近似としては妥当。ただし補正が2つ要る。**

妥当な理由:
- 人間の水平視野は物理的に前方 ~200°(両眼)止まりで真後ろは不可視。E2 式でも E > 90° は 0.065 以下でほぼ無視できる。
- ゲームAI の実務も同じ結論に達している(問い5: 全社が視錐+背後死角)。

**補正1(条件付きで必要)**: **注視方向は 480 ms で移る**(Fotios)。tick 長が 480 ms より十分長いなら「向き」は tick 内で平均化され、背後係数を厳密に 0 にするのは過剰。→ **推奨: 背後(|E| > 110°)の一次視覚係数 = 0、ただし tick 長 > 1 s なら「向き」自体を tick ごとに確率的に再抽選する**(進行方向を平均とする分布から)。

**補正2(必須)**: **背後でも社会的手がかりで届く**。Milgram の 42%(1人でも)には、前を歩く人の反応を見て振り返る経路が含まれる。→ **背後の事象は「聴覚 + 二次検出 P2」で届く**設計にすれば、背後の一次視覚をゼロにしても情報は正しく伝播する。これで「背後=音のみ」の粗さが実害にならない。

**聴覚チャネルの物理(参考・本答申の導出=【推測】)**: ANSI S3.5-1997 の発声努力レベルは normal 62.4 / raised 68.3 / loud 74.9 / **shout 82.3 dB SPL @ 1 m**(R の SII パッケージ文書由来。**規格本文は一次未確認**)。球面拡散なら距離2倍で −6 dB。渋谷の街路暗騒音を 70 dB(A) と置くと、叫び声が暗騒音を上回るのは 82.3 − 70 = 12.3 dB 相当 → **約 4 m**。暗騒音 60 dB なら約 13 m。
→ **「叫び声はセル全域に届く」は誤り。聴覚半径も視覚と同オーダー(数 m〜十数 m)**。この計算は本答申の導出であり、要検証。

---

## 問い4. 課題従事・照明

### 4-1. 携帯電話(Hyman 2010)

**Hyman IE Jr, Boss SM, Wise BM, McKenzie KE, Caggiano JM (2010) "Did you see the unicycling clown? Inattentional blindness while walking and talking on a cell phone", Applied Cognitive Psychology 24(5): 597–607. doi:10.1002/acp.1638**

Wiley 本文は **HTTP 403 で読めず(一次未確認)**。著者所属大学の公式発表より:

> "Cell phone use causes people to be oblivious to their surroundings while engaged in even a simple task such as walking."
(Western Washington University: https://news.wwu.edu/would-talking-on-your-cell-phone-cause-you-to-have-missed-this-clown-one-professor-thinks-so)

確認できた数値:
- **携帯通話者で一輪車ピエロに気づいた割合 = 25%**
- 単独歩行・二人組・音楽プレーヤー利用者は **いずれも「半数超」**
- 誘導なしの自由報告では携帯利用者の **8%** のみが言及(二次情報)

**空欄(未確認)**: 単独歩行・二人組・音楽の**個別の %**、各群の n、実験1(ピエロ)と実験2(Red Square 375 feet 横断)の対応。→ **親の一次確認対象**。

**設計上の使い方**: 25/54 ≈ **0.46** を `m_load`(スマホ)として、距離ではなく**確率の乗数**に掛ける(Hyman は距離も密度も統制していないため、d50 の乗数にするのは根拠が弱い)。

### 4-2. 非注意性盲目のベースライン(既決値の確認)

Simons DJ & Chabris CF (1999) "Gorillas in our midst", Perception 28: 1059–1074. doi:10.1068/p281059。全 192 名中 **54% が気づき・46% が見落とし**(サーチ結果。親側で既決済)。Easy 64% / Hard 45% の内訳は**今回一次未確認 = 空欄**。

### 4-3. 照明(一次確認済・Fotios 2015)

- 注視距離 中央値: **昼 13.0 m / 夜 8.9 m** → 比 **0.68**
- 上四分位: **昼 15.3 m / 夜 10.3 m** → 比 **0.67**

著者自身が因果を確定していない点(verbatim):

> "This may reflect a desire to fixate upon others at shorter distances after dark, or alternatively it may be that this is because the lower light level after dark, and hence lower visibility of a pedestrian's features, does not make fixation at greater distances worthwhile. It is also possible that after dark pedestrians at distances above 11.0 m were not sufficiently visible, either for detection with peripheral vision or inspection with foveal vision."

→ **m_light(夜) = 0.68 を「距離スケール d50 の乗数」として使うのが最も素直**(確率の乗数ではない)。ただし「望んで近づけている」可能性が排除されていないので **expedient タグ必須**。

**渋谷固有の注意**: 上記は英国住宅街の道路照明での実測。渋谷スクランブル交差点周辺は**大型ビジョン・看板照明で夜間鉛直面照度がきわめて高い**。夜係数を街区一律に掛けるのは誤り。**照明レイヤ(鉛直面照度)をセル属性として持ち、m_light をセル別に決める**べき(照明データの取得可否は別途 OPEN)。

### 4-4. 夜間の検認距離(二次・一次未確認)

- 反射ベスト着用の歩行者は 200 m 超で気づかれるが、白・灰・通常衣類ははるかに短距離
- 黒/灰のダミー歩行者・黒衣の実歩行者の recognition distance は **50 m 以下**

(いずれもサーチスニペットのみ。**運転者視点**であり歩行者同士ではない → 渋谷の歩行者への転用は要注意)

---

## 問い5. 工学的先行例(輸入候補)

| 実装 | 関数形 | 数値・仕様 | 計算量の扱い | 確認 |
|---|---|---|---|---|
| **CryENGINE 3 TTPS**(Crysis 2 由来) | stim(離散イベント)→ ADSR エンベロープ(連続値)→ Target Track。距離減衰ではなく **主FOV/副FOV の2段 + エンベロープの attack 時間差** | peak 値: 足音 25 / 銃声 50 / 主FOV視覚 100 | 3段フィルタ: ①イベント型の購読、②agent 視程 vs stim 半径、③視錐内判定(安価)→ 通過分のみ**非同期**レイキャスト。16体総当りで 136 レイキャスト → 敵対のみ登録で **16 に削減** | ✔ 全文読了 |
| **Alien: Isolation** | **4つの視錐**(normal / focused / peripheral / close) | 角度・距離値は非公開 | 段階錐 = 距離減衰の離散近似 | ✔(Panwar 2022 経由) |
| **The Last of Us** | **視野角が距離に反比例**(単一規則) | 数値非公開 | 錐1つで近接死角を解消 | ✔(Panwar 2022 経由) |
| **Splinter Cell: Blacklist** | 視錐でなく **「棺桶型」**(正面遠方は細く近傍は広い)。露出度は**骨8点へのレイキャスト本数**で連続量化 | 難易度ごとに形状を調整 | 聴覚は直線距離でなく**チョークポイント経由の音響距離**(10 m の音源が経路長 50 m として届く) | ✔ フェッチ |
| **HiDAC / Pelechano** | FOV 120–180°、**方向ベクトルとの内積 > 0** で視野内判定 | — | O(1)/対、レイキャストなし | △ 二次 |

### 引用(CryENGINE TTPS・verbatim)

> "Stims need to contain the following information in order to describe an event: The type of stimulus being generated, the entity ID of the source, the position or direction from which the stimulus originated, and a radius within which that stimulus can be perceived."

> "in our games we try to limit the number of active AI agents to 16. This means that every agent can potentially see 15 other AI characters. In the worst case scenario, this could mean 120 raycasts being requested to check visibility between all the AI agents, even before the player is considered!"

> "After the optimization of having agents only register interest in hostile targets, only 16 raycasts would be required"

> "A lot of unnecessary raycasts can be avoided by doing these much cheaper tests to see if potential visual targets are even within an agent's view cone before requesting a raycast."

> "in our current stim configuration, footsteps peak at a perception value of 25, weapon sounds peak at 50, and primary FOV visual stimuli peak at 100."

> "If an observable is within this secondary range of vision but not the primary (and still receives a clear raycast), then a secondary visual stim is sent ... This stim has both a lower peak perception value ... than the primary stim and a longer attack time."

出典: Welsh R, "Crytek's Target Tracks Perception System", Game AI Pro, Ch.31, pp.403–412. https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter31_Crytek's_Target_Tracks_Perception_System.pdf

### 引用(The Last of Us / Alien: Isolation・verbatim)

> "It uses 4 different view cones namely - normal, focused, peripheral and close"

> "The developers of The Last of Us came up with an even better and complex form of Vision cone with a simple rule that the angle of view is inversely proportional to the distance between the NPC and the player"

出典: Panwar H (2022) "The NPC AI of The Last of Us: A case study", arXiv:2207.00682. https://arxiv.org/pdf/2207.00682

### 引用(Splinter Cell: Blacklist・要約)

視錐は「棺桶型(coffin)」で、正面遠方は細く手前は広い。NPC は Fisher の骨格8点へレイキャストを打ち、遮蔽されていない骨の数が多いほど露出が高い。音は環境トポロジー経由の距離で評価するため「音源まで実距離 10 m でも経路長 50 m」になりうる。数値パラメータは非公開。
出典: https://www.gamedeveloper.com/design/bringing-balance-to-stealth-ai-in-splinter-cell-blacklist

### 輸入すべき教訓(3点)

1. **レイキャストは 16 体規模でも爆発する**。40万体では絶対に不可。**遮蔽は解析式(密度→遮蔽係数)で近似するしかない**。
2. **段階錐(2〜4段)が業界の実装解**。親案の「距離3段」は業界標準と整合しており、案Bの LUT 実装として温存できる。
3. **時間エンベロープ(ADSR)は本件では採らない**。§3 は「発生tickで一発ベルヌーイ」が既決(Wood & Simons 2019)。将来「気づきの遅れ」を入れる段階で、主FOV/副FOV の attack 時間差が既製解として使える。

---

## 問い6. 推奨(3案比較)

### 案の定義

**案A: 固定段階表(親の自前案)**
距離3段(近/中/遠)× 密度2段(疎/密)の 6 セル表 + 負荷/照明で表を切り替え。

**案B: 2段Hill(推奨)**

一次検出:
```
s        = d50_eff / d
E        = 2.7 + 0.7 * s
P1       = s^E / (1 + s^E)                    # TTPF そのまま
d50_eff  = d50(event_class) * m_light * m_ecc * m_density
m_ecc    = E2 / (E_ang + E2)                  # E2 = 6.22 deg、|E_ang| > 110 deg なら 0
m_light  = 1.0 (昼) / 0.68 (夜)               # Fotios: 8.9/13.0
m_density= 1.0 (疎) / 0.5 (中) / 0.2 (密)     # Schmieder の N50 0.5→2.5 から
P1'      = P1 * m_load                        # スマホ 0.46 (=25/54)、会話 1.0、手空き 1.0
```
二次検出(社会伝播):
```
P2 = 0.92 * N^1.05 / (1.2^1.05 + N^1.05)      # Milgram 実データのフィット
                                              # N = 半径 ~15 m 内で当該 tick に既に気づいた人数
```
合成:
```
p_notice = 1 - (1 - P1') * (1 - P2)
```

**案C: 幾何レイキャスト + ADSR(ゲームAI 完全移植)**
主/副視錐 + 遮蔽レイキャスト + 時間エンベロープ。

### 比較表

| 観点 | 案A 固定段階表 | **案B 2段Hill(推奨)** | 案C 幾何+ADSR |
|---|---|---|---|
| **根拠の強さ** | ✕ 文献裏付けなし(親も自認) | ◎ 距離=TTPF(60年の枯れた工学)、社会項=Milgram実データの既存フィット、照明=Fotios実測、負荷=Hyman。**恣意なのは d50 の値だけ** | △ ゲームの体験設計であって人間の実測ではない |
| **パラメータ数** | 6(表)× 負荷2 × 照明2 = 最大 **24** | **7**(d50, E2, m_light, m_density 3段, m_load)。社会項の m,T,k は文献固定なので実質 0 | 10+(錐2つの角度・距離、遮蔽閾値、ADSR 4値 × stim型) |
| **計算量**(イベント時のみ) | O(n) 表引き。最速 | O(n)。算術 ~20 flop + RNG 1。**距離→P1 を 256 bin LUT 化すれば表引きと同コスト** | ✕ レイキャストが O(n)。Crytek が 16 体で音を上げた規模の 1000 倍 |
| **セル境界** | ✕ セル内一律 → 100 m セル端で不連続。**Fotios の 10–20 m 実測と矛盾** | ◎ 連続。打ち切り半径は性能予算で選択(推奨 2·d50 = 80 m) | ◎ 連続だが高コスト |
| **密度の非単調性** | ✕ 表では表現不能 | ◎ P1↓ と P2↑ の合成で自然に出る(創発の観察対象になる) | △ 社会伝播は別途実装が要る |
| **紙上での監査** | ○ | ◎ 全項が閉形式。保存則系と同様に紙で検証可 | △ |
| **ablation 容易性** | △ 表を差し替える | ◎ 項ごとに 0/1 で外せる | ✕ |
| **expedient 量** | 大(ほぼ全部) | 中(下表に列挙) | 大 |

### 推奨: 案B

理由:
1. **距離項が必須であることが実測で確定した**(Fotios 中央値 10.3 m vs 100 m セル)。案A はセル内一律の粗さを距離3段で緩和するが、段の切り方に根拠がない。
2. **距離項と社会項が同じ Hill 関数族**で書け、**両方に既存フィット値がある**ので設計者の指紋が最小(ドクトリン §3「造語・制度を注入しない」に対応する形式版)。
3. パラメータ数が案Aより少ない。
4. レイキャストゼロで 40万体に載る。

**案Aは捨てず、案Bの LUT 実装 = ablation A1 として保持する**(同一コードで両立)。

### d50 の較正(導出と expedient 宣言)

- **下限アンカー**: Fotios 15 m(対人判断のための注視距離・昼の上四分位)。これは Johnson の "recognition"(4 cycles)相当。
- **上限アンカー**: Johnson の detection : recognition = 1.0 : 4.0 cycles → 検出距離は認識距離の **4 倍** → 60 m。
- **運動補正**: 動く標的は N50 が静止の 2/3 → さらに ×1.5 側に効く。
- **推奨初期値: d50(顕著な行為) = 40 m**。**この 40 m は文献値ではない = expedient。ablation で 20 / 40 / 80 m を振ること。**

d50 = 40 m のときの P1(前方・手空き・昼・低密度・社会項なし):

| 距離 | 5 m | 10 m | 20 m | 40 m | 60 m | 80 m | 100 m | 150 m | 200 m |
|---|---|---|---|---|---|---|---|---|---|
| P1 | 1.000 | 0.9995 | 0.945 | 0.500 | 0.217 | 0.108 | 0.061 | 0.022 | 0.010 |

(`s = d50/d`, `E = 2.7+0.7s`, `P = s^E/(1+s^E)`。**本答申が式から計算したもの。親は再計算で検証すること**)

裾が思ったより厚い点に注意: **P < 0.01 になるのは約 215 m(≈ 5.4·d50)**。100 m セルで打ち切り半径を素直に取ると ±2 リング(25セル)必要になる。→ 打ち切りは**性能予算との明示的トレードオフとして宣言する**(下記)。

社会項を足すと、近傍に気づいた人が 1 人いるだけで下限が 0.42 に持ち上がる → **100 m 先でも「周りが騒いだら気づく」が自然に出る**。これが Milgram の再現。

### expedient として明示する項(感度試験で「結果を駆動していない」証明が必要)

| 項 | 値 | expedient である理由 |
|---|---|---|
| `d50 = 40 m` | 40 | Fotios の注視距離を Johnson のサイクル比で外挿。直接測定なし |
| `m_density` 3段 (1.0/0.5/0.2) | クラッタ N50 比から | 群衆密度 → IR クラッタの写像に根拠なし |
| `m_ecc` の event_class 別調整 | 運動事象で E2 拡大 | 周辺視の運動残存感度は定性的にしか確認できていない |
| 背後 = 一次視覚 0 | 0 | 注視方向は 480 ms で移る。tick 長次第で過剰 |
| `m_load`(スマホ 0.46) | 25/54 | Hyman は距離も密度も統制していない。他要因が混入している |
| 聴覚半径(叫び ≈ 4–13 m) | 本答申の SPL 計算 | 一次文献なし・完全な導出 |
| 社会項の適用半径 15 m | 15 | Milgram の観測区間 50 feet から。設計者の選択 |
| 打ち切り半径 80 m | 2·d50 | 性能予算のための切り捨て。P1 ≤ 0.11 の裾を捨てている |

### ablation 設計

| 段 | 構成 | 外している項 |
|---|---|---|
| A0 | `p_notice = 0.54`(定数 = Simons & Chabris の全体値) | 全部 |
| A1 | + 距離(TTPF, d50 固定)※案A相当 | 偏心・密度・負荷・照明・社会 |
| A2 | + 負荷 `m_load` ・照明 `m_light` | 偏心・密度・社会 |
| A3 | + 偏心 `m_ecc` ・密度 `m_density` | 社会 |
| A4 | + 社会伝播 `P2`(= 案B完成形) | — |

**判定指標(全てエンジン側の集約。LLM を呼ばない)**
1. イベントあたり目撃者数の分布(中央値・裾)
2. 群衆形成の最大サイズと成長曲線(Milgram の「刺激群衆が成長する」が定性再現できるか)
3. 情報到達半径の中央値(何セル先まで噂が届くか)
4. 事象発生 → 最初の通報/介入行動までの tick 数

**expedient 卒業条件**
- A3→A4 で指標2 が定性的に変わる(群衆が成長するようになる)→ 社会項は **mechanism** と認定。
- `m_ecc` を ±50% 振って指標1–4 が較正誤差内に収まる → **expedient として封印可**(結果を駆動していない証明)。
- `d50` を 0.5× / 2× 振って指標3 が桁で変わる → **d50 は結果を駆動している = 較正データが必要**(何を較正データにするかは別途 OPEN。候補: 渋谷の実イベント時の SNS 投稿の空間分布)。

### 性能予算の宣言(案B)

- **逐次ループの新設: なし**(イベント発生時のベクトル演算1回)
- 在席密度の仮定: 40万体 / 139セル ≒ **2,878体/セル**(均一・ピーク想定。実際は交差点集中で不均一 → 最悪セルで数倍を見込むこと)

| 打ち切り | 半径 | セル数 | 対象体数 | 切り捨てる P1 | 1イベントの演算 |
|---|---|---|---|---|---|
| 保守 | 215 m (5.4·d50) | 25 (±2リング) | ~72,000 | < 0.01 | 0.72 MOPS |
| **推奨** | **80 m (2·d50)** | **9 (±1リング)** | **~26,000** | **< 0.11** | **0.26 MOPS** |
| 最小 | 40 m (d50) | 1〜9 | ~2,900 | < 0.50 | 0.03 MOPS |

- 演算: 距離2乗(3)→ LUT 引き(1)→ 乗数4回(4)→ RNG(1) ≈ **10 ops/体**
- **推奨は 80 m 打ち切り**。切り捨てる裾(P1 ≤ 0.11)の寄与は、**社会伝播 P2 が同じ情報をより遠くへ運ぶ**ので実質的に補償される(遠方の agent は「直接見た」のではなく「騒ぎを見た」経路で届くのが自然)。**この打ち切りは expedient。ablation で 215 m 版と比較し、指標3(情報到達半径)が変わらないことを確認すること。**
- tick あたりの顕著イベント数の上限を宣言値として置く(**初期 200/tick を提案**)→ **52 MOPS/tick**。numpy ベクトル化でミリ秒台【推測・実測でゲートすること】
- **バイト予算**: 追加の永続状態は エージェントあたり **2 byte**(向きの量子化 1 byte + 課題従事フラグ 1 byte)× 40万 = **800 KB**
- LUT: 256 bin × float32 × event_class 数。無視できる

---

## 問い7. 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 確認すべき引用文 | 確認すべき数値 |
|---|---|---|---|---|
| 1 | 歩行者が他の歩行者を注視する距離の中央値は 10.3 m、昼 13.0 m / 夜 8.9 m、注視 480 ms | https://eprints.whiterose.ac.uk/89559/ (doi:10.1177/1477153514529299) | "Overall, the median fixation distance was 10.3 m (inter-quartile range 8.3–12.3 m)." / "Median fixation distances were shorter after dark (8.9 m) than during daytime (13.0 m)." / "The overall median duration of observation was 480 ms (inter-quartile range 400–640 ms)." | 10.3 / 8.3–12.3 / 13.0 / 8.9 / 上四分位 15.3・10.3 / 480 ms / n=40 / Table 2 の Unfamiliar 夜の値(本答申では空欄) |
| 2 | 刺激群衆1人で 42% が見上げ・4% が停止、15人で 86% ・40% | J. Personality & Social Psychology 13(2):79–82 (1969)。**DOI は本答申では空欄**。本文PDFは communicationcache のミラーで読了(非正規ドメイン → 出版社版で再確認すること) | "While 4% of the passersby stopped alongside a single individual looking up, 40% of the passersby stopped alongside a stimulus crowd of [15]." / "While one person induced 42 % of the passersby to look up ... caused 86% of the passersby to orient themselves in the same direction" | 42 / 86 / 4 / 40 / N=1,424 / 30試行 / 50 feet / 刺激群衆 1,2,3,5,10,15 |
| 3 | TTPF の関数形と指数、動標的補正、クラッタ補正 | https://www.osti.gov/servlets/purl/1222446 (SAND2015-6368) | "P∞ = (N/(N50)_D)^E / (1 + (N/(N50)_D)^E)  (2)" / "E = 2.7 + 0.7(N/(N50)_D)  (3)" / "for moving targets, the N50 is 2/3 the value for an equivalent static target" / "For scenes with low clutter, for 50% probability of detection, N50 was 0.5 and for high clutter it was raised to 2.5." | 2.7 / 0.7 / 2/3 / 0.5→2.5 / ACQUIRE 検出 0.75 cycles / Detect05 C = 1, 1.5, 2.0, 2.7 |
| 4 | Milgram データに Hill 関数 P(N)=mN^k/(T^k+N^k) がフィット済み、実データ側 m=0.92, T=1.2, k=1.05 | doi:10.1098/rsif.2018.0335 / https://pmc.ncbi.nlm.nih.gov/articles/PMC6127183/ (本体サイトは 403) | "the proportion of crowd looking up as a function of the stimulus size N is P(N) = mN^k/(T^k + N^k)" / "when the authors in [7] fitted the same model to data from Milgram et al. [6], the values were m = 0.92, T = 1.2 and k = 1.05" | m=0.92 / T=1.2 / k=1.05(実世界)、m=1 / T=0.7 / k=1.7(VR)。**この論文の著者名(本答申では空欄)と、参照[7](元フィットの出典)の特定** |
| 5 | 携帯通話者で一輪車ピエロに気づいた割合 25%、非携帯は半数超 | doi:10.1002/acp.1638(**Wiley 本文は 403 で未読**)/ 大学発表 https://news.wwu.edu/would-talking-on-your-cell-phone-cause-you-to-have-missed-this-clown-one-professor-thinks-so | (原著の該当文は未取得 = **空欄**) | **25% を原著で確認**。**単独歩行/二人組/音楽の個別 % と各群 n は本答申では空欄**。実験1と実験2のどちらの数値かも要確認 |

### 補足: 親が追加で潰すべき「空欄(未確認)」

- Simons & Chabris 1999 の Easy 64% / Hard 45% の内訳(既決値の裏取り)— doi:10.1068/p281059
- Haun 2021 の E2 = 6.22°(achromatic)— doi:10.1093/nc/niab006。**Strasburger et al. 2011 の孫引きの可能性があるので原典(JOV 11(5):13, doi:10.1167/11.5.13)を当たること**
- 周辺視の運動検出閾値(54.3° → 0.5 °/s 等)— govinfo GOVPUB-D101-PURL-gpo84675。**サーチスニペットのみ**
- Bouma 定数 b ≈ 0.5 と `d = bE + w` — Rosen, Chakravarthi & Pelli (2014) JOV。**サーチスニペットのみ**
- 視覚探索スロープ 25–50 ms/item — Wolfe 系。**サーチスニペットのみ**
- Johnson 原典のサイクル数(検出 1.0±0.25 / 認識 4.0±0.8 / 識別 6.4±1.5)— **原典未確認**(SAND 本文では ACQUIRE 版 0.75 のみ確認)
- ANSI S3.5-1997 の発声努力 SPL(shout 82.3 dB @1 m)— **規格本文未確認・R パッケージ文書由来**
- IEC/EN 62676-4 の DORI 画素密度(25/62/125/250 px/m)— **規格本文未確認**
- 夜間の歩行者 recognition distance(黒衣 50 m 以下 / 反射ベスト 200 m 超)— **サーチスニペットのみ・運転者視点**
- 群衆遮蔽度の4段分類(0-15/15-50/50-85/85-100%)— **サーチスニペットのみ**

---

## 参照一覧

| # | 著者・年 | 題 | URL / DOI | 確認状況 |
|---|---|---|---|---|
| R1 | Fotios S, Yang B, Uttley J (2015) | Observing other pedestrians: Investigating the typical distance and duration of fixation. *Lighting Res. Technol.* 47(5):548–564 | doi:10.1177/1477153514529299 / https://eprints.whiterose.ac.uk/89559/ | ✔ 本文読了(Table 2・要旨・考察を verbatim 引用) |
| R2 | Milgram S, Bickman L, Berkowitz L (1969) | Note on the drawing power of crowds of different size. *JPSP* 13(2):79–82 | DOI **空欄(未確認)**。本文PDF: communicationcache ミラー(非正規ドメイン) | ✔ 全文読了(結果・ANOVA・限界の記述を verbatim 引用)。**出版社版で再確認要** |
| R3 | Sjaardema TA, Smith CS, Birch GC (2015) | History and Evolution of the Johnson Criteria. SAND2015-6368, Sandia National Laboratories | https://www.osti.gov/servlets/purl/1222446 | ✔ 全文読了(式1–3・動標的・クラッタ・ACQUIRE表) |
| R4 | (著者名 **空欄**, 2018) | Drawing power of virtual crowds. *J. R. Soc. Interface* 15(145):20180335 | doi:10.1098/rsif.2018.0335 / https://pmc.ncbi.nlm.nih.gov/articles/PMC6127183/ | ✔ PMC 経由でフェッチ・Hill 式と両フィット値を取得。**著者名と参照[7]は未特定** |
| R5 | Welsh R (Game AI Pro Ch.31) | Crytek's Target Tracks Perception System, pp.403–412 | https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter31_Crytek's_Target_Tracks_Perception_System.pdf | ✔ 全文読了(stim構造・ADSR・peak値・レイキャスト削減) |
| R6 | Panwar H (2022) | The NPC AI of The Last of Us: A case study | arXiv:2207.00682 / https://arxiv.org/pdf/2207.00682 | ✔ 全文読了(4視錐・視野角∝1/距離) |
| R7 | Haun AM (2021) | What is visible across the visual field? *Neurosci. Conscious.* 2021(1):niab006 | doi:10.1093/nc/niab006 / https://pmc.ncbi.nlm.nih.gov/articles/PMC8167368/ | ✔ フェッチ(E2 式・E2=6.22° 取得)。原典 Strasburger 2011 は未確認 |
| R8 | Hyman IE Jr et al. (2010) | Did you see the unicycling clown? *Appl. Cogn. Psychol.* 24(5):597–607 | doi:10.1002/acp.1638 | **△ Wiley 本文 403 で未読**。25% は大学公式発表で確認。群別内訳は空欄 |
| R9 | Western Washington University (2009) | Would talking on your cell phone cause you to have missed this clown? | https://news.wwu.edu/would-talking-on-your-cell-phone-cause-you-to-have-missed-this-clown-one-professor-thinks-so | ✔ フェッチ(25% と「半数超」を確認) |
| R10 | (Splinter Cell: Blacklist 解説記事) | Bringing Balance to Stealth AI in Splinter Cell: Blacklist | https://www.gamedeveloper.com/design/bringing-balance-to-stealth-ai-in-splinter-cell-blacklist | ✔ フェッチ(棺桶型視錐・8ボーン露出・音響距離) |
| R11 | Simons DJ, Chabris CF (1999) | Gorillas in our midst: Sustained inattentional blindness for dynamic events. *Perception* 28:1059–1074 | doi:10.1068/p281059 | **△ サーチのみ**(46%/54%)。Easy/Hard 内訳は空欄 |
| R12 | Pelechano N, Allbeck JM, Badler NI (2007) | Controlling individual agents in high-density crowd simulation (HiDAC). SCA '07 | https://dl.acm.org/doi/10.5555/1272690.1272705 | **△ サーチのみ**(FOV 120–180°・内積判定) |
| R13 | (米国政府刊行物) | Motion Detection in the Far Peripheral Visual Field | https://www.govinfo.gov/content/pkg/GOVPUB-D101-PURL-gpo84675/pdf/GOVPUB-D101-PURL-gpo84675.pdf | **△ サーチスニペットのみ**(0.5 / 1.2–1.5 / 2.1 °/s) |
| R14 | Rosen S, Chakravarthi R, Pelli DG (2014) | The Bouma law of crowding, revised. *Journal of Vision* | https://jov.arvojournals.org/article.aspx?articleid=2212997 | **△ サーチスニペットのみ**(d = bE + w、説明分散 82% / 94%) |
| R15 | (ANSI S3.5-1997 / SII 定数表) | Constants Tables for ANSI S3.5-1997 Speech Intelligibility | https://rdrr.io/cran/SII/man/critical.html | **△ 規格本文未確認**(normal 62.4 / raised 68.3 / loud 74.9 / shout 82.3 dB SPL @1 m) |
| R16 | Axis (ホワイトペーパー) | Pixel density based on IEC 62676-4:2014 | https://whitepapers.axis.com/en-us/pixel-density-based-on-iec-62676-4-2014 | **△ 規格本文未確認**(DORI 25 / 62 / 125 / 250 px/m) |
| R17 | Wood G, Simons DJ (2019) | (既決の根拠。本答申では未検証) | — | **本答申の調査範囲外**(親側で既決) |

---

## 規律の申告

- **子サブエージェントは起動していない。**
- **リポジトリへの書き込み・コミットは行っていない。**
- **Web からのファイルダウンロードは実行していない。** 本答申中の PDF は WebFetch がツール側で一時キャッシュに保存したものをローカルで文字抽出して読んだのみ(pymupdf)。R1 の本文テキストは本セッションの一時キャッシュに既に存在したもの(別レーンのフェッチ結果)から抽出しており、SAGE 掲載版のページ体裁("Lighting Res. Technol. 2015; 47: 548–564")を含む。**親は上記 White Rose の URL で独立に確認すること。**
- **記憶で埋めた数値はない。** 一次確認できなかった項目は本文中で「サーチスニペットのみ」「一次未確認」「空欄」と明示した。本答申が式から計算した値(P1 の表、聴覚半径、480/40 の走査上界)は【推測】または「本答申の導出」と明示した。
