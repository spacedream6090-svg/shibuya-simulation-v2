# 知覚遅延 δ_perc の導入判断(R3-8 未決D)— Webリサーチ答申

<!-- hdr:v1 -->
- **分野**: 知覚心理学・精神物理学 #5 | **重要度**: P0(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 109 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 作成: 2026-09-04 / 調査者: Opus 5(サブ) / 対象: docs/design/v2-perception-contract.md §6「未決D」
> 規律: 実読した出典の数値のみを本文に置く。二次情報・未読は §5 に隔離。子サブは起動していない。リポ書き込みなし。

---

## ① 結論(冒頭10行)

1. **導入を推奨する(強)。** 現行 δ_min=0.2 秒は Woods 2015 の**単純反応時間の床(213 ms・完全予期・中心視・n=1,469)**であって、街路の突発事象への反応値ではない。予期の有無で反応時間は**約2倍**動く(Green 2000 抄録: 予期あり0.70-0.75 s / 予期なし約1.25 s / 驚愕約1.5 s)ため、0.2 秒固定は「全員が驚愕事象に0.2秒で反応する集団」を作る。
2. **δ_perc は「起床キューのタイムスタンプ・オフセット」として実装せよ。** 新規データ構造ゼロ・逐次ループゼロ・予算影響ゼロ。§6 の pull-on-wake と完全整合。
3. **推奨パラメータ: 反応時間の床を Woods の 0.213 秒に固定し、予期クラスごとの無次元ペナルティ k を掛ける**(値でなく比を流用する。下表 ④-1)。分布は**対数正規・σ_ln=0.20**(Woods の個人内CV 17.1% と Hooper&McGee 表2成分和の 50th→99th 比から独立に一致)。
4. **予期クラスはエンジンが起床条件IDから決定論的に決める**(LLMに問わない=§1不変条件1と整合)。(iii)計画境界→即時、(ii)B5社会変化→0.35 s、(i)B4段階変化→1.05 s、顕著行為/イベント音→1.30 s。
5. **感覚運動スケール(0.2-1.5秒)と熟慮スケール(30-75秒)は別レーンにせよ。** 避難開始・介入判断は Forssberg 2019(n=2,486・40実験)で平均30.0-74.9秒・対数正規/対数ロジスティック。同じ δ_perc に混ぜてはいけない。
6. **傍観者効果は「潜時」でなく「行為確率と熟慮潜時」に効く**(Darley&Latané 1968: 52→93→166秒、通報率85→62→31%)。感覚運動 δ_perc に群衆密度倍率を掛けるのは誤り。
7. **p_notice(未決A)は「一発Bernoulli@発生tick」で正しい。** Wood&Simons 2019: 提示時間を1.5→5秒に伸ばしても気づき率は41→49.4%しか動かない=「気づくなら直後、でなければ永遠に気づかない」。毎tickハザード累積の実装は現実と食い違い、かつ計算も無駄。
8. **副次効果が大きい: δ_perc は同期的なthundering herdを対数正規の到着過程に散らす。** 顕著行為1件で数百体が同一tickに起床する事故を構造的に防ぎ、P7「64 in-flight/GPU」の膝を守る。未決E(繰り延べ)の原理的な先行実装でもある。
9. **δ_think(α×tokens)には上限を課せ。** 上限がないとトークン予算が人間の反応時間を暗黙に決める=「設計者の指紋」。先行研究 RRARA(2025)は推論実測時間をそのままシム時間に写像しており(GPT-3.5=2.54 s, Claude-3.7-Sonnet=13.05 s)、結果がGPU/モデル選択で動く。**我々の α×tokens 方式のほうが再現性で優る**——この優位は明文化する価値がある。
10. **合成の整合が良い**: δ_perc(C3=1.05)+δ_think(床0.2)=1.25 s = Green の「予期なし」。δ_perc(C4=1.30)+0.2 = 1.50 s = Green の「驚愕」。独立2系統(運転者研究の総反応時間 / 実験室成分の積み上げ)が同じ値に落ちる。

---

## ② ユーザーがまず読む大枠(5分版)

**何が問題だったか。** 契約書 §6 は「起床したら δ=max(0.2s, α×tokens) 後に行動」としている。この 0.2 秒は Woods et al. 2015 の単純反応時間 213 ms から来ているが、あの数値は**「今から光る」と分かっている被験者が中心視の刺激にボタンを押す**条件の値だ。街路で背後から悲鳴が上がったときの反応ではない。今のままだと、渋谷の全員が驚愕事象に0.2秒で反応する。

**現実はどうか。** 反応時間は単一の値ではなく、**予期の関数**である。これは交通人間工学の中心的知見で、Green (2000) の分類がそのまま使える:

| 状態 | 総反応時間 |
|---|---|
| 予期あり(いつどこで信号が来るか完全に分かっている) | 0.70-0.75 秒 |
| 予期なしだが日常的(前車のブレーキランプ) | 約 1.25 秒 |
| 驚愕(物体が突然進路に入る) | 約 1.5 秒 |

そして Hooper & McGee (1983) は同じものを**成分に分解**している。この分解が我々の設計とほぼ1対1で対応するのが決め手だった:

| 成分 | 50%タイル | 99%タイル | v2でどこに対応するか |
|---|---|---|---|
| 潜時(周辺視→眼球運動開始) | 0.24 s | 0.45 s | **δ_perc** |
| 眼球運動 | 0.09 s | 0.09 s | **δ_perc** |
| 固視(焦点合わせ) | 0.20 s | 0.20 s | **δ_perc** |
| 認識(何であるか分かる) | 0.40 s | 0.65 s | **δ_perc** |
| **知覚小計(当方計算)** | **0.93 s** | **1.39 s** | **δ_perc の実体** |
| 決定 | 0.50 s | 1.00 s | **δ_think(α×tokens)** |
| 制動反応(運転固有・歩行者には不適用) | 0.85 s | 2.16 s | (不採用) |

つまり **δ_perc = 知覚小計、δ_think = 決定**という素直な対応がつく。しかも知覚小計 0.93 s に δ_think の床 0.2 s を足すと 1.13 s、Green の「予期なし 1.25 s」とほぼ一致する。独立2系統が合う。

**もうひとつの発見: 時間スケールが2つある。** 感覚運動の反応(0.2-1.5秒)と、社会的・熟慮的な反応(30-75秒)は別物である。火災避難の pre-movement time は事務所で平均64.4秒、映画館で30.0-44.0秒、ナイトクラブで46.6-65.4秒(Forssberg et al. 2019・実験40件・n=2,486)。社会的緊急事態への通報潜時は52-166秒で、しかも**居合わせた人数で1.8-3.2倍に伸びる**(Darley & Latané 1968)。避難開始や「倒れた人を助けるか」はこちらのレーンで、δ_perc に混ぜてはいけない。

**実装は安い。** δ_perc は起床キューに入れる時刻を後ろにずらすだけ。新しいメモリも逐次ループもいらない。むしろ**得をする**: 顕著行為が1件起きると周囲の数百体が同じtickに起床してGPUの in-flight 上限(64)を叩き割る問題が、δ_perc の分散によって自動的に時間方向へ散る。未決E(繰り延べ思想)の原理的な先行実装になっている。

**設計上の判断が1つ必要。** δ_perc 秒後に起床したとき、その個体が見る世界は「事象が起きた瞬間の世界」か「起床した瞬間の世界」か。前者は現実的(人は古い情報で動く)だが、契約書 §2 不変条件3「観測は有界な完全現在形」と衝突し、バイト一致の維持も難しくなる。**推奨は後者(起床時点の現在形)**——δ_perc は純粋にスケジューリングの遅延として扱い、観測は常に現在形を保つ。この割り切りは expedient として台帳に登録し、ablation を予約する。

---

## ③ 問い1-6の証拠

### 問1. 一次資料の確認

#### 1-a. Woods et al. 2015 の再確認 ★実読(PMC全文)

出典: Woods DL, Wyma JM, Yund EW, Herron TJ, Reed B. **Factors influencing the latency of simple reaction time.** *Frontiers in Human Neuroscience* 9:131 (2015). https://pmc.ncbi.nlm.nih.gov/articles/PMC4374455/

| 項目 | 実験1 | 実験2 |
|---|---|---|
| n / 年齢 | 1,469 / 18-65歳 | 189 / 18-82歳 |
| 平均SRT(生値) | 231 ms | 237.8 ms |
| 平均SRT(ハードウェア遅延補正後) | **213 ms**(補正量 17.8 ms) | — |
| 被験者間SD | 27 ms | 28 ms |
| **個人内SD / 変動係数** | **40.0 ms / 17.14%** | 52.7 ms / 21.9% |
| 加齢効果 | **+0.55 ms/年**(r=0.24) | +0.45 ms/年(r=0.35) |
| **刺激検出時間 SDT** | **131.2 ms**・年齢非依存(r=−0.02) | 138.3 ms(r=−0.05) |
| SOA(予告→刺激の間隔)効果 | 最短SOAで**約15%延長**(28 ms程度)・ω²=0.49 | 同 ω²=0.40 |
| ヒット率 | 97.1% | 97.2% |

**含意3点**:
- 213 ms は**予期・中心視・単一刺激・ボタン押し**の床。街路の反応値ではない。契約書§6の現行記述(「予期ありの反応時間の下限」)は正確である。
- SRT は **SDT(検出 131 ms)+ 残り(≈82 ms の運動/決定)**に分解でき、**加齢はSDTでなく運動側に乗る**。つまり「検出遅延」と「運動遅延」は独立に扱ってよい実証がある。
- **個人内CV 17.1%** が、δ_perc の分散パラメータの直接の実測アンカーになる(→④-2)。
- SOA を変えるだけで15%動く=**「予期の程度」は連続量**であり、離散クラス分けは近似(expedient)である。

#### 1-b. Green (2000) ★抄録のみ実読・本文未読

出典(書誌): Green M. **"How Long Does It Take to Stop?" Methodological Analysis of Driver Perception-Brake Times.** *Transportation Human Factors* 2(3):195-216 (2000). DOI 10.1207/STHF0203_1 — https://www.tandfonline.com/doi/abs/10.1207/STHF0203_1 (本文403・取得不可)

抄録の文言(検索経由で tandfonline / scispace の抄録レンダリングを2独立系統から確認):

- 最重要変数は**運転者の予期(expectation)であり、反応時間を2倍動かす**。
- **予期あり**(信号の時刻と位置を完全に把握): 検出+アクセル→ブレーキの足の移動で **約0.70〜0.75秒**。
- **予期なしだが日常的な信号**(前車のブレーキランプ): **約1.25秒**。
- **驚愕事象**(物体が突然進路に入る): **およそ1.5秒**。
- これらは**年齢・性別・認知負荷・切迫度**によって多少変調される。

参照: https://scispace.com/papers/how-long-does-it-take-to-stop-methodological-analysis-of-3s6qwritrf

**分解値は Green 本人のサイトの記述**(論文本文では未確認・二次扱い): https://www.visualexpert.com/Resources/reactiontime.html
- 予期あり 0.7 秒 = 知覚 0.5 + 運動 0.2
- 予期なし 約1.25 秒 = 知覚 >1.0 + 運動 0.2
- 驚愕 1.5 秒(側方からの侵入)= 知覚 1.2 + 運動 0.3。正面の障害物は「数10ミリ秒〜0.数秒速い」
- ステアリング反応は制動より 0.15〜0.3 秒速い
- 認知負荷による遅延は 0.3〜1秒以上
- 照度を1/10にすると 20〜25 ms 遅くなる
- 同サイトの別頁 https://www.visualexpert.com/Resources/realprt.html: Olson & Sivak (1986) は中央値1.1秒・5%タイル0.8秒・95%タイル1.6秒。車線侵入研究の平均PRTは約1.5秒でその95%タイルは約2.4秒=AASHTOの2.5秒に近い。

**評価**: 抄録の3値(0.70-0.75 / 1.25 / 1.5)は本答申の中核として使ってよい。**分解値(0.5+0.2 等)は著者本人の記述だが査読論文本文で未確認**であり、二次扱いのまま設計に使う場合は expedient タグを付けること。

#### 1-c. 歩行者の知覚反応時間(PRT)と AASHTO 2.5 秒 ★TRB論文は実読

出典: Hooper KG, McGee HW. **Driver Perception-Reaction Time: Are Revisions to Current Specification Values in Order?** *Transportation Research Record* 904:21-30 (1983). https://onlinepubs.trb.org/Onlinepubs/trr/1983/904/904-004.pdf(PDF取得→pymupdf抽出・実読)

**AASHTO 2.5 秒の内訳(本文からの直接引用)**:
> "The current AASHTO specification for this driver characteristic is 2.5 s. As specified in the AASHO Policy on Geometric Design of Rural Highways, this value was determined from an assumed perception time of 1.5 s and a brake-reaction time of 1.0 s. The values do not relate to any specific percentile of drivers."

→ **2.5 秒は「知覚1.5秒+制動反応1.0秒」の仮定値であり、特定パーセンタイルに対応しない。**(設計値であって観測値ではない、と原典が明言している。台帳にはこの注記込みで載せること。)

**表2: 成分別・パーセンタイル別の推定値(秒)** — 本答申の中心証拠:

| 成分 | 50th | 75th | 85th | 90th | 95th | 99th |
|---|---|---|---|---|---|---|
| 潜時 (Latency) | 0.24 | 0.27 | 0.31 | 0.33 | 0.35 | 0.45 |
| 眼球運動 (Eye movement) | 0.09 | 0.09 | 0.09 | 0.09 | 0.09 | 0.09 |
| 固視 (Fixation) | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 |
| 認識 (Recognition) | 0.40 | 0.45 | 0.50 | 0.55 | 0.60 | 0.65 |
| 決定 (Decision) | 0.50 | 0.75 | 0.85 | 0.90 | 0.95 | 1.00 |
| 制動反応 (Brake reaction) | 0.85 | 1.11 | 1.24 | 1.42 | 1.63 | 2.16 |
| **合計(原典)** | **2.3** | **2.9** | **3.2** | **3.5** | **3.8** | **4.6** |
| *知覚4成分の和(当方計算)* | *0.93* | *1.01* | *1.10* | *1.17* | *1.24* | *1.39* |

原典の注釈も重要:
> "These values should not be considered a statistically reliable distribution of the driving population. They are based on estimates, assumptions, and data from experimental procedures not truly indicative of actual conditions."
> "a human is capable of time-sharing sensory information processing and psychomotor tasks"(=成分の単純加算は過大評価になりうる)

**「知覚4成分の和」は当方が行の和を取ったもので、原典が公表している数値ではない**(原典が公表するのは決定+制動反応を含む合計)。設計に使う際は「当方計算」と明記のこと。

**副次的に得た一次値**(同論文中):
- 眼球運動潜時(視軸から20°の刺激): 50th 0.24 / 85th 0.31 / 99th 0.45 秒(Bartlett et al.・ただし**被験者3名**と原典が注記)
- 眼球運動時間: 約0.09 秒(White et al.)
- 固視時間: 0.1-0.3 秒(Matson, Smith & Hurd)、開放路走行中の平均固視時間 0.27 秒(Mourant et al.)
- 標識の検出後の認識反応時間: 平均 0.42-0.48 秒(Ells et al., n=12)、別研究で約 0.6-0.7 秒(Ells & Dewar)
- 決定時間(Lunenfeld・85%タイル)— **情報量ビット数と予期の交互作用が読める**:

  | 情報量 | 予期あり | 予期なし |
  |---|---|---|
  | 0 bit | 0 | 0 |
  | 1 bit | 0.7 s | 1.0 s |
  | 2 bit | 1.3 s | 1.6 s |
  | 3 bit | 2.0 s | 2.6 s |

  → **決定時間は情報量にほぼ線形**。これは δ_think = α×tokens という現行の定式化の現実側の裏付けになる(トークン数≒情報量の代理)。予期なしは一律 +0.3〜0.6 秒。

- 表1(各研究の制動反応時間・抽出時に列が一部崩れたため参考): Greenshields (1936) n=1,461 平均0.496・SD 0.0913 / Johansson & Rumar (1971) n=321 平均0.75 / Sivak et al. (1981) n=311 平均1.23・SD 0.62 / Mortimer (1970) n=80 平均1.30。

**歩行者PRT 0.48秒 は依然未読**(→§5)。

---

### 問2. 知覚遅延の分解(検出/認知/運動)と注意状態の効果

#### 2-a. 分解の実証

- **実験室レベル(Woods 2015・実読)**: SRT 213 ms のうち **SDT(刺激検出時間)131.2 ms**。残り約82 ms が運動+決定。**SDTは年齢非依存**(r=−0.02)、SRT全体は +0.55 ms/年 → **加齢は検出でなく運動/決定に乗る**。
- **応用レベル(Hooper & McGee 1983・実読)**: 上表のとおり 潜時 / 眼球運動 / 固視 / 認識 / 決定 / 運動 の6成分。**検出側(潜時+眼球運動+固視)=0.53〜0.74秒、認識=0.40〜0.65秒、決定=0.50〜1.00秒、運動=0.85〜2.16秒(車両操作)**。
- **原典の警告**: 成分の単純加算は「人間は感覚情報処理と運動課題を時分割できる」ため過大になりうる。**→ 我々が δ_perc + δ_think を直列に足すのは上限側の近似であることを台帳に明記すべき。**
- **歩行の運動側(Moussaïd et al. 2009・実読)**: 廊下での歩行開始について、**反応時間 0.35 秒の後**に加速が始まり、力学的緩和時間 **τ = 0.54 ± 0.05 秒**、自由歩行速度 1.29 ± 0.19 m/s。→ 歩行文脈での「気づいてから動き出すまで」の実測値。

  出典: Moussaïd M, Helbing D, Garnier S, Johansson A, Combe M, Theraulaz G. **Experimental study of the behavioural mechanisms underlying self-organization in human crowds.** *Proc. R. Soc. B* 276:2755 (2009). https://arxiv.org/pdf/0908.3131
  > "The desired velocities v⁰ are normally distributed with an average value of 1.29±0.19m/s (mean±sd), and the relaxation time amounts to τ = 0.54 ± 0.05 seconds"
  > "The parameters were estimated as τ=0.54±0.05s and v0=1.29±0.19m/s **after a reaction time of 0.35s**."

#### 2-b. 注意状態による変化

- **予期の程度は連続量**(Woods 2015・実読): SOA(予告からの間隔)を最短にするだけで SRT が約15%延長。予期は on/off ではない。
- **予期あり/なしの倍率**(Green 2000 抄録・Lunenfeld 表): 総反応時間で**約2倍**、決定時間で **+0.3〜0.6 秒**。
- **スマホ注視・二重課題**: 決定的な実測秒数は取れなかった(→§5)。ただしモデル側の扱いは明確:

  出典: Echeverría-Huarte I, Roge A, Simonin O, Nicolas A. **Near-future projections in continuous agent-based models for crowd dynamics: mathematical structures in use and their implications.** arXiv:2309.12798 (2025-03-13). https://arxiv.org/pdf/2309.12798(PDF→pymupdf抽出・実読)
  > "The first timescale is the cognitive reaction time τψ. It encompasses both how often the agents refresh their perceptions of the environment (gazing activity) and the short delay before they adjust their motion in response to their observations. ... Obviously, this time is expected to soar if the person is engaged in a discussion or playing with their smartphones (texting or web-browsing, in particular)"
  > "a delayed reaction (larger τψ) implies that the agents persist longer on their initial, collisional paths (especially when **τψ increases from 1 s to 2 s**), but then swerve more abruptly and more markedly."
  > "since τψ cannot be obtained from a quantity measured in the experiments ... we cannot provide a more quantitative comparison."

  → **先行研究も τψ の実測値を持っていない。1秒→2秒という探索レンジを提示しているだけ**。我々が m_att(スマホ)を expedient で置くのは先端と同水準であり、恥じる必要はない。ただし ablation は必須。

- **注意逸れの実測(行動側・秒でなく空間)**: Murakami H, Tomaru T, Feliciani C, Nishiyama Y. **Spontaneous behavioral coordination between avoiding pedestrians requires mutual anticipation rather than mutual gaze.** *iScience* 25 (2022). https://pmc.ncbi.nlm.nih.gov/articles/PMC9684055/(実読)
  - 条件: BASE(通常)/ NMA(**片方が携帯で1桁加算課題をしながら歩行**)/ NMG(片面ミラーサングラスで**視線情報のみ遮断**)。男性学生20名・各条件120試行。
  - 結果: 携帯使用条件で行動協調が低下。**視線情報の遮断だけでは歩行は変わらなかった**。→ 協調は「視線」でなく「相互予期」に依存する。
  - 携帯条件ですれ違い時の距離が BASE より大きい(数値は図中で本文に記載なし)。
  - 上記 arXiv:2309.12798 は同実験を引き、**「注意逸れ側の回避開始が遅く・より急峻になり、すれ違い距離が平均5〜10cm大きい」**と要約している(当方は iScience 本文で当該cm値を確認できていない=二次)。

  **設計含意**: 「見られている/見ている」は δ_perc の入力ではなく**相互予期の有無**が効く。契約書 §3 の人物⑤(被注視性)は δ_perc とは別軸として維持してよい。

---

### 問3. 社会的事象への反応潜時

#### 3-a. 傍観者効果の潜時 ★一次実読

出典: Darley JM, Latané B. **Bystander Intervention in Emergencies: Diffusion of Responsibility.** *Journal of Personality and Social Psychology* 8(4):377-383 (1968). https://www.ucdenver.edu/docs/librariesprovider102/default-document-library/bystander-intervention-john-darley-and-bibb-latane.pdf(PDF→pymupdf抽出・実読)

表1(発作を通報するまで):

| 群サイズ | n | 発作終了までに通報した割合 | **通報までの時間(秒)** | 速度スコア |
|---|---|---|---|---|
| 2(被験者と被害者) | 13 | 85% | **52** | .87 |
| 3(+他1名) | 26 | 62% | **93** | .72 |
| 6(+他4名) | 13 | 31% | **166** | .51 |

分布の形について本文から直接:
> "Ninety-five percent of all the subjects who ever responded did so within the first half of the time available to them. **No subject who had not reported within 3 minutes after the fit ever did so.**"

同一被験者群での構成効果(3人群・男性被害者): 女性S+男性他者 94秒 / 女性S+女性他者 92秒 / 女性S+医療系他者 60秒 / 男性S+女性他者 110秒 → **他者の属性は潜時にほぼ効かない**。

**設計含意**:
- 群衆密度の効果は**「気づき」ではなく「行為するか/いつ行為するか」に乗る**。倍率は 93/52 = **1.79**(3人)、166/52 = **3.19**(6人)。
- 分布は**強い頭重+打ち切り**。指数分布ではない。「3分で打ち切り」は実装上ありがたい(ハザードを永久に回し続けなくてよい)。
- 注意: これは実験室の intercom 状況であり、渋谷の路上への流用は expedient。

#### 3-b. 気づきそのものの潜時 ★一次実読(PMC全文)

出典: Wood K, Simons DJ. **Now or never: noticing occurs early in sustained inattentional blindness.** *Royal Society Open Science* 6(11):191333 (2019). https://pmc.ncbi.nlm.nih.gov/articles/PMC6894580/

多重物体追跡課題中に予期しない十字が出現。**提示時間を変えても気づき率がほとんど動かない**:

| 実験 | 提示時間別の気づき率 |
|---|---|
| 実験1 | 2.67秒 38.5% → 5秒 44.0%(差 +5.5pt) |
| 実験2 | 1.5秒 41% → 2.67秒 43.4% → **5秒 49.4%** |
| 実験3 | 1.5秒 61.5% → 5秒 64.9%(差 −3.4pt) |

> "subjects who noticed the unexpected object did so soon after it onset"

**設計含意(未決A=p_notice にも直結)**:
- **p_notice は「事象発生tickでの一発Bernoulli」で実装するのが現実に忠実**。毎tickハザードで累積させると、5秒露出で気づき率が上がりすぎて現実と食い違う。
- **かつ計算が安い**(1事象1判定)。契約書 §4 段1 の実装形をこれで確定できる。
- 気づいた個体の δ_perc は短い(「直後」)。→ δ_perc の分散は小さくてよい(σ_ln=0.2 の裏付け)。

#### 3-c. 避難開始時間(pre-movement time)の分布 ★出版社プレビュー経由で実読

出典: Forssberg M, Kjellström J, Frantzich H, Mossberg A, Nilsson D. **The Variation of Pre-movement Time in Building Evacuation.** *Fire Technology* 55(6):2491-2513 (2019). DOI 10.1007/s10694-019-00881-1
- 書誌確認: https://lup.lub.lu.se/search/publication/2d4e39fa-71da-4ea4-a79d-9723c48333a5
- 数表取得元: https://www.springerprofessional.de/en/the-variation-of-pre-movement-time-in-building-evacuation/16926104(**出版社プレビュー頁からの読取。論文PDF本体は未読**)

規模: **予告なし避難実験40件・6用途・2,486データ点**(うち映画館は30実験・1,954点)。

| 用途 | n | 平均(秒) | SD | 範囲 | 適合分布 |
|---|---|---|---|---|---|
| 事務所 | 45 | **64.4** | 45.6 | 12-201 | 対数ロジスティック (γ=0; β=52.5; α=3.0) |
| 映画館(音声警報) | 900 | **44.0** | 18.0 | 17-138 | 対数ロジスティック (γ=0; β=40.5; α=5.8) |
| 映画館(サイレン) | 163 | **30.0** | 28.1 | 14-179 | 対数正規 (μ=25.0; σ=6.2) |
| 映画館(ベル) | 886 | **32.5** | 17.2 | 11-224 | 対数ロジスティック (γ=0; β=29.5; α=5.0) |
| 百貨店 | 229 | **35.9** | 17.7 | 5-111 | 対数正規 (μ=35.9; σ=18.3) |
| 飲食店/カフェ | 27 | **52.5** | 15.7 | 20-86 | ワイブル (α=3.8; β=58.1) |
| 学校 | 72 | **74.9** | 42.3 | 13-170 | ガンマ (α=3.0; β=24.5) |
| ナイトクラブ(積極的スタッフ) | 62 | **46.6** | 18.7 | 11-87 | ワイブル (α=2.7; β=52.5) |
| ナイトクラブ(消極的スタッフ) | 84 | **65.4** | 64.0 | 5-417 | 対数ロジスティック (γ=0; β=50.6; α=2.3) |

内訳(事務所): 認知時間(recognition)平均 40.6秒(SD 27.4)+ 反応時間(response)平均 23.2秒(SD 25.2)= 64.4秒。映画館(音声警報): 認知 29.7秒 + 反応 14.4秒。

→ **社会的事象への反応も「認知」と「反応」に分解されている**。我々の δ_perc / δ_think の分割と構造が同じ。

**注意すべき2点**:
1. n の合計が 1,949+519 = 2,468 で、論文の 2,486 と18点ずれる。プレビュー経由の読取の限界。
2. 分布パラメータの表記規約(μ/σ が対数空間か秒か)が確認できていない。特に「対数正規 (μ=35.9; σ=18.3)」は平均/SDそのままの値で、対数空間パラメータではない可能性が高い。**再現に使う前に論文PDFで要確認**。

**設計含意**: 「スタッフが積極的か消極的か」だけで 46.6 → 65.4 秒(+40%)動く。**制度・役割が潜時を支配する**——v2の「世界の変化はエージェント行動の結果」ドクトリンと整合的で、指令エージェント(D-R2-1-2)の効果が潜時に現れる場所である。

---

### 問4. シミュレーションでの実装先行

#### 4-a. 群衆シム(SFM / ORCA / ANDA)

**Social Force Model 系**: 「反応時間」に相当する独立パラメータを持たない。SFM の τ は**力学的緩和時間**であって認知遅延ではない。arXiv:2309.12798(実読)が正面から批判している:

> "in conventional force-based models, pseudo-forces are additively inserted into Eq. 8 ... Conceptually, this is not satisfactory, because it puts these cognition-mediated effects on the same footing as mechanical forces, in particular subjecting them to the same relaxation time scale τ_mech."
> "It so happens that for walking the cognitive reaction time τψ is of the same order of magnitude as τ_mech and that both processes take place within the confines of the same physical entity; the pedestrian. **This helps explain the widespread conflation of mechanical and decisional processes.**"

同論文は認知反応時間 τψ を**「知覚の更新頻度(gazing activity)+観測後に運動を調整するまでの短い遅延」**と定義し、ANDA モデルでは「決定層が desired velocity を更新する間隔」に対応させている。図7で **τψ を 1秒→2秒** に振って効果を示している。

> "It is worth adding a note on the numerical integration time dt in continuous models. Typically much shorter than both τψ and τ_mech, this time step is a computational artifact"

**→ v2への直接の含意**: **δ_perc(認知)と行動の物理的継続時間(力学)は別パラメータとして分離せよ**。これは先端の群衆力学が明示的に要求していることで、我々の「エンジン=状態と集約 / LLM=意思決定と発話」の分業とも一致する。

**ORCA/RVO2**: 反応遅延パラメータは一次で確認できず(→§5)。上記 arXiv:2309.12798 の批判の射程(「純粋反応型モデル」)からして、**毎ステップ即時再計画=遅延ゼロ**が既定と考えるのが妥当。

#### 4-b. 避難ABM

- pre-movement time は「秒で直接指定」または「一様/正規/対数正規/確率密度/累積分布」から選べるのが商用実装の標準(Pathfinder 等)。→ **我々が δ_perc を分布で持つのは業界標準の実装形**であり、新奇な設計ではない(=導入の政治的コストは低い)。
- 実データ側の分布は 3-c のとおり対数正規/対数ロジスティックが中心。

#### 4-c. ゲームAI(Unreal Engine)

出典: https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine(実読)および https://zomgmoz.tv/unreal/AI-Perception/AISense-Sight(実読)

- **視覚センスは time-sliced** され、「a lot of controllers using it」の場合に性能影響を下げる。ただし:
  > "This can add latency to sight perception events, **but only if you hit the time slice limits**"
- 既定値は `DefaultGame.ini` / `AISense_Sight.h` で設定可能(**具体的な既定値は未確認**)。
- 関連パラメータ: `AutoSuccessRangeFromLastSeenLocation`(既視の対象はこの範囲内なら常に見える)、`Max Age`(知覚のタイムアウト)、`Forget Stale Actors`。

**→ 含意**: 商用エンジンの知覚遅延は**性能都合の副作用**であって、意図的な人間らしさのモデルではない。我々が δ_perc を**明示的な現実整合パラメータ**として置くなら、それはゲーム産業からの輸入ではなく交通人間工学からの輸入である。**「ゲームは作らない・知見だけ輸入する」の線引きに照らして、UE から輸入すべきは「時間分割による負荷平準化」の実装技法のみ**で、遅延の値ではない。ただしこの技法は δ_perc の分散と同じ効果(バースト平準化)を持つ点が示唆的。

#### 4-d. LLMエージェント系での知覚遅延の扱い ★2本とも実読

**(1) 推論遅延をシム時間に写像した例**
出典: Zheng Y, Mao S, Zhang D, Cai W. **Reflex First, Reflect Later: Latency-Aware Embodied LLM Agents for Dynamic Response.** arXiv:2506.07223v2. https://arxiv.org/html/2506.07223v2(HTML実読)

- **Time Conversion Mechanism (TCM)**: `F_inf = ⌈t_inf × FPS⌉` — **実測の推論壁時計時間を、そのままシミュレーション frame に換算する**。実験は全て 30 FPS。
- 評価指標: **Response Latency (RL)** = 実行を開始/継続できるまでのブロッキング遅延、**LAR** = `t_inf/(t_inf+t_action)`。
- 実測値(表2):

  | エージェント | RL | LAR |
  |---|---|---|
  | ルールベース | 0.00 s | — |
  | GPT-3.5 | **2.54 s** | 52% |
  | Claude-3.7-Sonnet | **13.05 s** | 89% |
  | RRARA-v1 | 0.00 s | 0% |
  | RRARA-v2 | 0.38 s | 17% |

**→ 我々への含意(重要)**: この方式だと **シミュレーション結果がGPU速度とモデル選択で変わる**(同じ世界がGPT-3.5なら2.54秒、Claude-3.7なら13.05秒で反応する)。**我々の δ=max(0.2s, α×tokens) はトークン数という決定論的量に基づくため、再現性で優る。**この優位は設計書に明記しておく価値がある(「なぜ実測レイテンシを使わないか」への答え)。同時に、この論文は**「reflex(即応)と reflect(熟慮)を非同期に分ける」**という構造を提案しており、我々の**感覚運動レーン(δ_perc)と熟慮レーン(C5)の二層化**の先行例として引ける。

**(2) 「いつ行動するか」を「何をするか」から切り離した例**
出典: Zhang A, Tan Y, Tang Y, Tang H, Ye Q, Gonzalez MC, Li Y. **Toward Temporal Realism in City-Scale Crisis Response Simulation using LLM Agents.** arXiv:2606.19904v1 (2026-06-19). https://arxiv.org/abs/2606.19904(抄録実読)

抄録から:
> "Human collective participation is rarely steady in time: it is bursty, with short episodes of intense activity separated by long quiet intervals. ... Such settings are increasingly modeled with LLM-based social simulators, yet these simulators are validated on whether each action is individually plausible, **not on whether actions are timed as in reality**. Their temporal realism ... thus remains untested."
- 手法: **「いつ行動するか」(明示的な自己励起・危機活性化機構)と「何をするか」(LLM)を分離**。
- 数値: LLM単体ベースラインは**バースト性を全く生まない(中央値 B = −0.14)**。提案手法は **中央値 B ≈ 0.37**。

**→ 我々への含意(最も重要な外部証拠)**: **同期的なターン制スケジューリングは、時間構造を平坦化して現実と食い違う**——これが2026年時点でLLM社会シミュレーションの査読可能な欠陥として指摘されている。δ_perc の導入は「反応が遅くなる」以上に、**「起床のタイミングを世界側の決定論で分散させる」ことで時間的リアリズムを回復する装置**である。契約書 §6 の起床条件と δ_perc の組合せは、この論文の「when/what 分離」をエンジン側で実現したものになる。

---

### 問5. δ_perc と δ_think の合成

#### 5-a. 合成の意味論

現行: `δ = max(0.2s, α×tokens)` は**決定(思考)時間**。
提案: **総反応時間 = δ_perc(世界→気づき) + δ_think(気づき→決定) [+ δ_act(決定→可視の行動)]**

対応関係(Hooper & McGee の成分に厳密に写像できる):

| v2の量 | Hooper&McGee の成分 | 50%タイル |
|---|---|---|
| δ_perc | 潜時 + 眼球運動 + 固視 + 認識 | 0.93 s(予期なし視覚事象) |
| δ_think | 決定 | 0.50 s(予期あり)〜 |
| δ_act | 制動反応(=運動) | 車両固有・歩行者は Moussaïd の 0.35 s + τ 0.54 s |

**δ_act は新設せず、行動の継続時間(action duration)に吸収することを推奨**(新規パラメータを増やさない)。

#### 5-b. 現実の反応時間分布との整合検証

3系統が独立に同じ場所へ落ちる:

| 予期クラス | δ_perc(提案) | + δ_think床 0.2 | Green 2000 の総反応時間 | 一致 |
|---|---|---|---|---|
| 予期あり(外部信号) | 0.20 s | 0.40 s(+運動0.2〜0.3 = 0.60-0.70) | 0.70-0.75 s | ○ |
| 予期なし・日常 | 1.05 s | **1.25 s** | **約1.25 s** | ◎ |
| 驚愕 | 1.30 s | **1.50 s** | **約1.5 s** | ◎ |

かつ Hooper & McGee の知覚成分和(0.93〜1.39秒)が「予期なし・日常」の δ_perc = 1.05 秒を独立に支持する。

**→ 「Green の総反応時間から δ_think の床 0.2 秒を引いた残り」を δ_perc の中央値とする**という単純な定義で、2つの独立した一次系統が整合する。これが本答申の中心的推奨根拠。

#### 5-c. 予期あり/なしをエンジンでどう決めるか

**原則: 予期クラスは起床条件のIDから決定論的に決まる。LLMには問わない。**(§1不変条件1「知覚=世界状態の決定論的射影」と整合。LLMに「驚きましたか」と聞くのは知覚の生成にあたり禁止事項。)

契約書 §6 の起床条件 (i)-(v) からの写像:

| 起床条件 | 予期クラス | δ_perc 中央値 |
|---|---|---|
| (iii) 計画境界(現行行動の終了)= 自発 | **C0 自発** | **0 s** |
| (iv) 会話ターン | **C1 予期あり** | 0.20 s |
| (ii) B5: 知人出現・近接上位kの入替・被注視・傍受ヒット | **C2 注意内の社会変化** | 0.35 s |
| (ii) B5: 内受容の閾値割れ | C2(データなし・expedient) | 0.35 s |
| (i) B4: 密度段階の跨ぎ・騒音段階・構造物(行列/人だかり) | **C3 予期なし・日常** | 1.05 s |
| (i) B4: 顕著行為の到達(倒れる・叫び・警察)・聴覚イベント | **C4 突発** | 1.30 s |
| (大事件・避難・介入判断) | **C5 熟慮** | 対数正規・中央値 ≈35 s |

**判定の実装**: 起床イベントに `expectation_class` を1バイトで持たせるだけ。分岐は起床条件の生成側にあり、追加の計算はゼロ。

**注意状態による修飾** m_att(乗算・expedient):
- スマホ注視中・会話中: ×2.0(arXiv:2309.12798 が τψ を 1→2秒 で探索していることに合わせる。実測値は世界に存在しない)
- 睡眠/dormant: そもそも起床条件から除外(既存の仕組みで足りる)

**傍観者効果は δ_perc に掛けない。** Darley&Latané の 1.79/3.19 倍は「通報という**行為**の潜時」であり、C5 熟慮レーンにのみ適用する(または介入確率へ)。感覚運動レーンに掛けるのは誤りである。

#### 5-d. δ_think 側への3つの要求

1. **上限を課す**: `δ_think ≤ δ_think_max(class)`。C0-C4 は 1.0 秒(Hooper&McGee の決定時間99%タイル)。C5 は無制限。これがないと**トークン予算が人間の反応時間を暗黙に決めてしまう**(憲法「設計者の指紋の最小化」に反する)。
2. **床 0.2 秒の意味を再定義**: 現在は「反応時間の下限」だが、δ_perc 導入後は**「決定の下限」**になる。Hooper&McGee の決定時間 50%タイル 0.50 秒からすると 0.2 秒はむしろ低めで、床としては安全側。文言だけ改める。
3. **α の較正アンカー**: Lunenfeld の決定時間表(1bit=0.7s / 2bit=1.3s / 3bit=2.0s・85%タイル)は**情報量に対しほぼ線形で約0.65 s/bit**。トークン数をビット数の代理と見なす α×tokens の定式化に現実側の裏付けがある。ただし bit → token の換算は未確立(expedient)。

#### 5-e. 観測スナップショットの時点(要判断・契約書との衝突)

δ_perc 秒後に起床したとき、渡す観測は:
- **案A(推奨)**: **起床時点(t_event + δ_perc)の現在形**。§2不変条件3「観測は有界な完全現在形」を維持。B0-B4 のバイト一致も維持。実装は起床キューのタイムスタンプ・オフセットのみ。**リアリズムの代償: 個体が古い情報で動くことはない。**
- 案B: 事象発生時点(t_event)の世界を渡す=真の知覚遅延。現実的だが、個体ごとに異なる時点のスナップショットを保持する必要があり、**セル共有のバイト一致が壊れる**(実測−38%の再来)。

**推奨は案A。** 案Bを採る理由が出てきたら、B4のみ1tick前のハッシュを保持する限定版で対応可能だが、Phase 2では不要。この割り切りは **expedient(観測時点の現在形化)** として台帳に登録し、ablation を予約する。

---

### 問6. 台帳アンカー候補(実数値)

**強(一次実読・そのまま載せられる)**

| # | アンカー | 値 | 出典 |
|---|---|---|---|
| RT-1 | 単純反応時間(予期あり・中心視) | 213 ms(HW補正)/ 231 ms(生)・被験者間SD 27 ms・n=1,469(18-65歳) | Woods 2015 |
| RT-2 | 反応時間の個人内変動 | 個人内SD 40.0 ms・**CV 17.14%** | Woods 2015 |
| RT-3 | 刺激検出時間(SDT) | 131.2 ms・**年齢非依存**(r=−0.02) | Woods 2015 |
| RT-4 | 反応時間の加齢勾配 | **+0.55 ms/年**(検出でなく運動/決定側に乗る) | Woods 2015 |
| RT-5 | 予期の程度は連続量 | 最短SOAで SRT が約15%延長 | Woods 2015 |
| RT-6 | 知覚成分和(予期なし・路上物体) | 50th **0.93 s** / 85th 1.10 / 99th **1.39 s**(当方=行の和) | Hooper&McGee 1983 表2 |
| RT-7 | 決定時間 | 50th 0.50 s / 85th 0.85 / 99th 1.00 s | Hooper&McGee 1983 表2 |
| RT-8 | 決定時間の情報量依存(85%タイル) | 1bit 0.7/1.0 s・2bit 1.3/1.6 s・3bit 2.0/2.6 s(予期あり/なし)≈ **0.65 s/bit** | Lunenfeld(Hooper&McGee 経由) |
| RT-9 | AASHTO 2.5秒の内訳 | 知覚1.5 s + 制動反応1.0 s の**仮定値・特定パーセンタイルに非対応**(原典明言) | Hooper&McGee 1983 |
| RT-10 | 認識時間(標識) | 平均 0.42-0.48 s(n=12) | Ells et al.(同上経由) |
| RT-11 | 開放路走行中の平均固視時間 | 0.27 s | Mourant et al.(同上経由) |
| PD-1 | **歩行開始の反応時間** | **0.35 s** | Moussaïd 2009 |
| PD-2 | 歩行の力学的緩和時間 | τ = **0.54 ± 0.05 s** | Moussaïd 2009 |
| PD-3 | 自由歩行の希望速度 | 1.29 ± 0.19 m/s | Moussaïd 2009 |
| SO-1 | 社会的緊急事態の通報潜時 | 2人 **52 s** / 3人 **93 s** / 6人 **166 s** | Darley&Latané 1968 |
| SO-2 | 同・通報率 | 85% / 62% / 31% | Darley&Latané 1968 |
| SO-3 | 同・分布形 | 応答者の95%は利用可能時間の前半・**3分後の新規応答ゼロ** | Darley&Latané 1968 |
| SO-4 | 傍観者倍率 | ×1.79(3人)/ ×3.19(6人) — **行為潜時にのみ適用** | 当方計算(SO-1より) |
| IB-1 | 気づきは提示時間にほぼ非依存 | 1.5s 41% / 2.67s 43.4% / 5s 49.4% | Wood&Simons 2019 |
| EV-1 | 避難前時間(平均秒・SD) | 事務所 64.4(45.6)/映画館 音声44.0(18.0)・サイレン30.0(28.1)・ベル32.5(17.2)/百貨店35.9(17.7)/飲食52.5(15.7)/学校74.9(42.3)/NC積極46.6(18.7)・消極65.4(64.0) | Forssberg 2019 |
| EV-2 | 同・規模と分布 | 実験40件・6用途・**n=2,486**・対数正規/対数ロジスティックが中心 | Forssberg 2019 |
| EV-3 | 同・認知/反応の分解(事務所) | 認知 40.6 s(27.4)+ 反応 23.2 s(25.2) | Forssberg 2019 |
| EV-4 | **役割による潜時支配** | ナイトクラブでスタッフ積極46.6 → 消極65.4 s(**+40%**) | Forssberg 2019 |

**中(抄録のみ・分解は著者サイト)**

| # | アンカー | 値 | 出典 |
|---|---|---|---|
| GR-1 | 制動反応時間: 予期あり | **0.70-0.75 s** | Green 2000 抄録 |
| GR-2 | 制動反応時間: 予期なし・日常 | **約1.25 s** | Green 2000 抄録 |
| GR-3 | 制動反応時間: 驚愕 | **約1.5 s** | Green 2000 抄録 |
| GR-4 | 予期の効果量 | **約2倍** | Green 2000 抄録 |

**参考(我々の設計判断の対照として)**

| # | アンカー | 値 | 出典 |
|---|---|---|---|
| LL-1 | LLM推論の実測レイテンシ | GPT-3.5 2.54 s / Claude-3.7-Sonnet 13.05 s / RRARA-v2 0.38 s | Zheng 2025 |
| LL-2 | 推論時間→シム時間の写像式 | `F_inf = ⌈t_inf × FPS⌉`(30 FPS) | Zheng 2025 |
| LL-3 | 同期ターン制はバースト性を生まない | LLM単体 中央値 B = −0.14 / 提案手法 B ≈ 0.37 | Zhang 2026 |
| CM-1 | 群衆モデルの認知反応時間 τψ の探索レンジ | 1 s → 2 s(**実測値ではないと原典が明言**) | Echeverría-Huarte 2025 |

---

## ④ 設計含意(契約書 §6 未決D への具体的提案)

### ④-1. δ_perc の定義と推奨パラメータ

**定義**: `δ_perc = RT_floor × k(class) × m_att`、`RT_floor = 0.213 s`(Woods 2015 の HW補正済 SRT)

**値でなく比を流用する。** 絶対秒は運転者研究由来で歩行者への流用に不確かさが残るが、「予期ペナルティの倍率」のほうが転移可能性が高い。

| クラス | 起床条件 | k | δ_perc 中央値 | 根拠 | タグ |
|---|---|---|---|---|---|
| **C0 自発** | (iii) 計画境界 | 0 | **0 s** | 外部信号なし | mechanism |
| **C1 予期あり** | (iv) 会話ターン・予告済み事象 | 1.0 | **0.21 s** | Woods 213 ms | mechanism |
| **C2 注意内の社会変化** | (ii) 知人出現・近接入替・被注視・傍受・内受容 | 1.6 | **0.35 s** | Moussaïd 0.35 s | mechanism(内受容のみ expedient) |
| **C3 予期なし・日常** | (i) 密度/騒音段階・構造物・看板 | 4.9 | **1.05 s** | Green 1.25 − 0.2。H&M 知覚和 0.93-1.10 が独立支持 | **expedient(運転者研究からの流用)** |
| **C4 突発** | (i) 顕著行為の到達・イベント音・大事件 | 6.1 | **1.30 s** | Green 1.5 − 0.2 | **expedient(同上)** |
| **C5 熟慮** | 避難開始・介入判断・群衆同調 | — | **対数正規 中央値 ≈35 s** | Forssberg 用途別(渋谷路上は未計測=百貨店35.9 sを暫定) | **expedient(用途流用)** |

**分布**: 全クラスで**対数正規**、`σ_ln = 0.20`(C0-C4)。
- 根拠1: Woods の個人内 CV = 17.14%
- 根拠2: Hooper&McGee 知覚成分和の 50th=0.93 → 99th=1.39 から `σ_ln = ln(1.39/0.93)/2.326 = 0.173`(当方計算)。85%タイル予測 1.11 s vs 実表 1.10 s で一致。
- 2つの独立系統が σ_ln ≈ 0.17 に収束するため、**0.20 は安全側の丸め**。これは mechanism タグでよい。
- C5 は Forssberg の用途別パラメータをそのまま使う(σ が大きい: 事務所は平均64.4/SD45.6 = CV 71%)。

**注意状態修飾** `m_att`(乗算・**全て expedient・ablation 必須**):
- スマホ注視/会話中: ×2.0(Echeverría-Huarte の探索レンジ 1→2秒に整合)
- 既定: ×1.0

**傍観者/群衆密度**: **δ_perc に掛けない。** C5 の潜時と「介入行為の確率」にのみ、×1.79(近傍3名)/×3.19(近傍6名以上)を適用(expedient)。

### ④-2. 実装(コスト実質ゼロ)

```
起床イベント生成時:
    e.class      = expectation_class(wake_condition_id)      # 分岐のみ
    e.t_wake     = t_event + lognormal(median=δ_perc[e.class]·m_att, σ_ln=0.20)
    arbiter_queue.push(e)                                     # 既存のキューに入れるだけ
起床時:
    観測は t_wake 時点の現在形で描画(§2不変条件3を維持)
```

- **新規メモリ: ゼロ**(イベントに1バイトの class と既存の時刻フィールドのみ)
- **新規逐次ループ: ゼロ**(§4 の「逐次ループの新設は宣言必須」に抵触しない)
- **P6(変化検出)・M10/M11 への影響: なし**
- **L4(起床数)への影響: 減る方向**。δ_perc 窓内に複数の起床条件が重なれば1回に合体できる(coalescing)。

### ④-3. 副次的な性能上の利得(導入の第2の理由)

契約書 §7 は「起床キュー=64 in-flight/GPU(ベンチ第3段の膝)」を予算としている。**顕著行為1件で同一セルの数百体が同一tickに起床する**構造が現状ある(§6起床条件(i))。δ_perc の対数正規分散(中央値1.30 s・σ_ln 0.20 → おおむね 0.9-1.9 秒に散る)は、このバーストを自動的に時間方向へ均す。

- **これは未決E(繰り延べアービタ)の原理的な先行実装**である。破棄でなく繰り延べ、しかも繰り延べ量が**現実の反応時間で決まる**ため恣意的でない。
- Zhang 2026(LL-3)が示すとおり、**同期ターン制はバースト性を消して時間的リアリズムを壊す**。δ_perc はこれを構造的に回避する。
- **UE の time-slicing と同じ効果**(負荷平準化)を、性能都合ではなく現実整合の側から得ている。これは「ゲームの技法を輸入するが、値は現実から取る」というプロジェクトの姿勢の良い実例になる。

### ④-4. 未決A(p_notice)への波及 — 同時決着を推奨

Wood&Simons 2019(IB-1)は **「気づくなら直後、でなければ気づかない」** を示す(提示時間 1.5→5秒で気づき率 41→49.4%)。したがって:

- **p_notice は事象発生tickでの一発Bernoulli**として実装する(毎tickハザードの累積は現実と食い違い、計算も無駄)。
- 気づいた個体だけが δ_perc 後に起床する。気づかなかった個体はその事象では二度と起床しない。
- 初期値は契約書の (i) 案(非注意性盲目 46% 見落とし → p_notice = 0.54)を採り、ablation を予約。Wood&Simons の実測気づき率(41-64.9%・課題負荷依存)がこの水準と整合的である点は追加の支持になる。

### ④-5. タグ・予算・検証装置への追記案

**mechanism|expedient**:
- δ_perc の存在・対数正規・σ_ln=0.20・C0/C1/C2 の値: **mechanism**
- C3/C4 の値(運転者研究からの流用): **expedient(流用)** → 感度試験で「結果を駆動していない」証明が必要
- C5 の値(建物用途からの流用): **expedient(流用)**
- m_att(スマホ×2.0): **expedient** — 先行研究にも実測値がない
- 傍観者倍率(C5のみ): **expedient**
- 観測を t_wake の現在形にする割り切り: **expedient(観測時点の現在形化)**

**ablation 予約(L2枠に追加)**:
1. δ_perc = 0(全クラス即時)vs 採用 — δ_perc が結果を駆動しているか
2. クラス別値の一律化(全クラス 1.0 秒) — クラス分けが効いているか
3. m_att = 1.0 固定 — スマホ修飾が効いているか
4. σ_ln = 0(決定論的遅延) — 分散が効いているか(バースト平準化の効果測定を兼ねる)

**台帳の弱い行(holdout 用・確度中)**:
- 「予期なし事象への行動変化の中央値は約1.2秒」
- 「傍観者数が増えると介入潜時は 1.8-3.2 倍になる」
- 「群衆内で顕著事象が起きたとき、周囲の反応開始は同時でなく約1秒中心の対数正規で散る」
- 直接観測は困難なので、代替の検証量として「顕著行為の発生から周囲個体の進路変化までの時間分布」を実映像で測る案(Phase 3以降・要データ)

**予算宣言**:
- 新規予算項目は不要。**L4(起床数)の上限に対して δ_perc は緩和側に働く**ことを診断行に常設(coalescing で減った呼数)。

### ④-6. 契約書 §6 の書き換え案(該当行のみ)

現行:
> **δ_perc(知覚遅延)**: δ_min=0.2秒は予期ありの反応時間の下限(単純反応時間213-231ms・n=1,469・実読)。予期なしは約1.25秒・驚愕は約1.5秒(二次資料・原典未読)。**未決D: δ_percを導入するか**(推奨=導入・二次値は暫定)。

案:
> **δ_perc(知覚遅延)= 導入(R3-8で決定)**。総反応時間 = δ_perc + δ_think(+行動継続時間)。δ_perc = 0.213 s × k(予期クラス) × m_att、対数正規 σ_ln=0.20。予期クラスは起床条件IDからエンジンが決定論的に決める(LLMには問わない)。k: C0自発=0 / C1予期あり=1.0 / C2注意内の社会変化=1.6 / C3予期なし日常=4.9 / C4突発=6.1。C5熟慮(避難・介入)は別レーンで対数正規・中央値約35秒。根拠: 単純反応時間213 ms(Woods 2015・n=1,469)を床とし、Green 2000の予期倍率(予期あり0.70-0.75 s / 予期なし1.25 s / 驚愕1.5 s)と Hooper&McGee 1983 表2の知覚成分和(50th 0.93 s / 99th 1.39 s)が独立に一致。C3/C4は運転者研究からの流用=**expedient・ablation予約**。実装は起床キューのタイムスタンプ・オフセットのみで新規予算なし。副次効果として顕著行為による同時起床バーストを対数正規に散らし、64 in-flight の膝を守る(未決Eの原理的先行実装)。

---

## ⑤ 未発見・未確認の正直な列挙

### 取得できなかった一次資料

1. **Green (2000) の本文**。tandfonline は 403、`safespeed.org.uk/reactions.pdf` は https↔http のリダイレクト・ループで取得不可、ResearchGate は 403。**確認できたのは抄録の文言のみ**(0.70-0.75 / 1.25 / 1.5 / 「予期は2倍動かす」)。抄録は tandfonline と scispace の2独立系統から同一文言を確認したが、**論文本文・図表・SD・パーセンタイルは未確認**。
2. **Green の分解値(予期あり 0.5+0.2 / 驚愕 1.2+0.3、ステアリングは0.15-0.3秒速い、認知負荷 0.3-1秒、照度1/10で+20-25ms)は著者本人のサイト visualexpert.com の記述**であり、査読論文で確認していない。**二次扱い。**
3. **歩行者PRT 0.48秒(Fugger et al. 2000, TRR 1705:20-25)は依然として未読**。同じ二次引用に「slowdown 0.58 s・start-up 0.39 s」が併記されているが、いずれも原典未確認。契約書 §10 の「未確認: PRT 0.48秒」は**解消していない**。
4. **Johansson & Rumar (1971, Human Factors 13(1):23-27) 原典未読**。二次では「n=321・予期あり平均 0.66 秒・予期なしで約1.0秒増・補正後中央値 0.9 秒」。一方 Hooper&McGee 表1 の抽出値は 0.75。**0.66 と 0.75 の食い違いは未解決**(表の列がPDF抽出時に崩れたため、0.75 が平均列かどうか確証がない)。設計にこの値は使っていない。
5. **Forssberg et al. (2019) の論文PDF未読**。数表は springerprofessional の**プレビュー頁からの読取**。(a) n の合計が 2,468 で論文記載の 2,486 と 18 点ずれる。(b) 分布パラメータの表記規約(μ/σ が対数空間か秒か)が不明——特に「対数正規 (μ=35.9; σ=18.3)」は平均/SDそのままの可能性が高い。**実装前に PDF で要確認。**
6. **AASHTO Green Book 原典未読**。2.5秒の内訳(知覚1.5+制動1.0・特定パーセンタイル非対応)は Hooper&McGee が AASHO Policy を引用した記述で読んだ(=一次論文内の引用)。
7. **UE の AI Perception の time-slice 既定値未確認**。`AISense_Sight.h` / `DefaultGame.ini` に設定があるとドキュメントが述べるのみで、具体値はエンジンソース参照が必要。
8. **ORCA/RVO2 に反応遅延パラメータがあるかは一次未確認**。gameaipro の該当章 PDF はテキスト抽出に失敗した。arXiv:2309.12798 の議論(純粋反応型モデルは即時再計画)から「遅延なし」と推定されるが、**推定である**。
9. **Murakami et al. (2022) の「すれ違い距離が5-10cm大きい」は arXiv:2309.12798 による要約**であり、iScience 本文で当該数値を確認していない。iScience 本文には**絶対秒数の潜時が報告されていない**(相対時間軸 0→1 で正規化されているため)。

### 数値が取れなかった項目

10. **歩きスマホの反応遅延の実測秒数は世界に見当たらない。** Huang et al. (2017, *Accident Analysis & Prevention*) はペイウォールで抄録に数値なし(「読むアプリ条件で検出が遅い」等の定性記述のみ)。**arXiv:2309.12798 の著者自身が「τψ は実験で測られた量から得られない」と明言している。**→ m_att = 2.0 は expedient にせざるを得ない。
11. **検索要約に現れた「聴覚・視覚の妨害で歩行者反応時間が67%・50%増」は、指示された出典(arXiv:2503.16443)本文に該当記述を確認できなかったため不採用。** 同論文で確認できたのはVR検証の「横断時間差 0.31 秒」など別の量のみ。**この67%/50%という数字は使わないこと。**
12. **会話のターン間ギャップ(約200ms・Stivers et al. 2009 PNAS とされる)は未調査・未読。** C1(会話ターン)の 0.21 秒は Woods の SRT から置いており、会話固有の証拠ではない。今後の確認候補。
13. **驚愕反射(startle reflex)の潜時は未調査。** Green の "surprise"(約1.5秒)は**驚愕反射(EMG で数10ms級)とは別概念**である。用語の混同に注意。契約書 §6 の「驚愕は約1.5秒」という表現は Green の surprise の訳であり、生理学的 startle ではないことを明記すべき。
14. **内受容(空腹・疲労・体感温度)の閾値到達から「気づく」までの潜時データは見つからなかった。** C2 に入れたのは便宜。
15. **日本・渋谷固有の反応時間データは見つからなかった。** 全て欧米の実験室・道路・建物由来。文化差の有無は未検証。
16. **Wood&Simons 2019 は「気づきは onset 直後に起きる」を示すが、秒単位の潜時は報告していない**(位置データが onset 位置に集中することからの推論)。δ_perc の分散が小さいという主張の裏付けとしては間接的。

### 調べていない領域(次のレーン候補)

17. 群衆密度そのものが**検出**に与える効果(視界遮蔽以外の注意資源の消費)。
18. 聴覚事象の反応時間が視覚より速い件(二次では聴覚 ~140-160ms vs 視覚 ~180-190ms)。**一次未読**。もし採るなら C4(イベント音)の k を視覚より小さくする根拠になりうる。
19. 夜間・低照度の δ_perc への効果(Green の「照度1/10で+20-25ms」は本人サイトのみ)。
20. 高齢者・子どもの δ_perc(Woods の +0.55 ms/年は 18-65 歳の SRT のみ。予期なし事象での加齢効果は未調査)。

---

## 付: 実読した出典URL一覧

| 出典 | URL | 読み方 |
|---|---|---|
| Woods et al. 2015, Front Hum Neurosci 9:131 | https://pmc.ncbi.nlm.nih.gov/articles/PMC4374455/ | 全文 |
| Hooper & McGee 1983, TRR 904:21-30 | https://onlinepubs.trb.org/Onlinepubs/trr/1983/904/904-004.pdf | PDF→pymupdf 全文 |
| Darley & Latané 1968, JPSP 8(4):377-383 | https://www.ucdenver.edu/docs/librariesprovider102/default-document-library/bystander-intervention-john-darley-and-bibb-latane.pdf | PDF→pymupdf 全文 |
| Wood & Simons 2019, R Soc Open Sci 6:191333 | https://pmc.ncbi.nlm.nih.gov/articles/PMC6894580/ | 全文 |
| Moussaïd et al. 2009, Proc R Soc B 276:2755 | https://arxiv.org/pdf/0908.3131 | PDF→pymupdf 全文 |
| Echeverría-Huarte et al. 2025, arXiv:2309.12798 | https://arxiv.org/pdf/2309.12798 | PDF→pymupdf 全文 |
| Zheng et al. 2025, arXiv:2506.07223v2 | https://arxiv.org/html/2506.07223v2 | HTML |
| Zhang et al. 2026, arXiv:2606.19904 | https://arxiv.org/abs/2606.19904 | 抄録 |
| Murakami et al. 2022, iScience 25 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9684055/ | 全文 |
| Forssberg et al. 2019, Fire Technology 55(6):2491-2513 | https://www.springerprofessional.de/en/the-variation-of-pre-movement-time-in-building-evacuation/16926104 / 書誌 https://lup.lub.lu.se/search/publication/2d4e39fa-71da-4ea4-a79d-9723c48333a5 | プレビュー数表のみ |
| Green 2000, Transportation Human Factors 2(3):195-216 | https://www.tandfonline.com/doi/abs/10.1207/STHF0203_1 (403) / https://scispace.com/papers/how-long-does-it-take-to-stop-methodological-analysis-of-3s6qwritrf | **抄録のみ** |
| Green(著者サイト・二次) | https://www.visualexpert.com/Resources/reactiontime.html / https://www.visualexpert.com/Resources/realprt.html | 全文(二次扱い) |
| Unreal Engine AI Perception | https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine / https://zomgmoz.tv/unreal/AI-Perception/AISense-Sight | ドキュメント |
