# Myllymäki & Mrkvička 2024 — GET: Global Envelopes in R(原理は Myllymäki et al. 2017 JRSS-B)

- リンク: https://arxiv.org/abs/1911.06583 | 分野: 統計学・因果推論 #23 / 検証と V&V #22 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが curl → システム python の pymupdf で全 40 頁抽出。§2.1 定義(式 2)・IGI 定義 2.1・§2.2 型の選び方・付録 C を逐語照合)。**親未確認**。*J Stat Softw* 111(3):1–40・doi:10.18637/jss.v111.i03(arXiv:1911.06583 v1 2019-11-15 → v4 2023-12-23)。**原理の原典** Myllymäki, Mrkvička, Grabarnik, Seijo & Hahn (2017) *JRSS-B* 79(2):381–404・doi:10.1111/rssb.12172(arXiv:1307.0239)は**抄録のみ**。

## 主張(claim)

曲線(関数)を帰無の曲線群と比べるとき、**各点ごとに α を守る「点ごとの帯」では、曲線全体としての第 1 種の誤りが守られない**。全点に同時の被覆を与える帯(大域包絡)を使えば、**検定と図示が同時にでき、「どこで外れたか」まで読める**。

逐語(≤125 字):
- 式(2): "**A 100(1−α)% global envelope is a set (T^(α)_low, T^(α)_upp) of envelope vectors … such that the probability that Ti falls outside this envelope in any of the d points is equal to α**"
- "**global means that the envelope is given with the prescribed coverage 100(1−α)% simultaneously for all the elements of the multivariate or functional statistic**"

## 機構(mechanism)

1. **s 本のベクトル** T1,…,Ts を用意(用途 (ii) では T1 = 実測、T2…Ts = 帰無の下で生成したもの)。
2. 極値度の**測度 M_i** を選ぶ('rank' / 'erl' / 'cont' / 'area' / 'qdir' / 'st' / 'unscaled')。
3. **Monte Carlo p 値**: "p = Σ_{i=1}^{s} 1(M_i ≤ M_1) / s"
4. **IGI(内在的図的解釈)**(定義 2.1): 帯の外に出るのは M_i < M(α) のときに限る ⇔ 帯の中に完全に収まるのは M_i ≥ M(α) のときに限る。→ **「帯の外に出た点」がそのまま棄却理由**: "inspecting for which k = 1,…,d the data vector T1 is outside the global envelope"
5. **前提**: "**In order to obtain an exact Monte Carlo test … the exchangeability of the test vectors Ti is required.**"
6. 合成帰無(母数を推定する場合)は "the classical Monte Carlo test can be liberal or conservative" → 付録 C の 2 段階補正が要る。

## 効く箇所(seam)

- **事前登録 v1.2 の「(ii) 実測が 3 本の幅の中にあるか」の正典形がこれ**。いま我々が「幅」と呼んでいるものは、**測度を決めていない・α を宣言していない・p を計算していない**状態。
- **d = 120(5 エリア × 24 時間)の全点に同時の被覆**を与えるので、**H1〜H5 を Bonferroni で締める代わりに、曲線 1 本の大域検定に畳める**(§1-1 の多重比較問題の別解)。
- **交換可能性の要求が ECMWF の fair score の前提と同じ**。空間統計と気象アンサンブルが独立に同じ条件へ収束している = 我々が seed の交換可能性を検査すべき理由が 2 系譜で立つ。
- **合成帰無の警告**が効く: 我々の「帯」はモデルの母数を較正した後の seed 群なので、素朴な Monte Carlo 検定は保守的にも寛容にもなりうる。

## 「結論でなく機構として」の入れ方

- **借りない**: R パッケージ・空間点過程の作例・7 種の測度の細部。
- **借りる**: (1) **式(2) の定義文をそのまま事前登録に書く**(「どの点でも外れない確率が 1−α」)。(2) **p = #{M_i ≤ M_1}/s** と、そこから出る **p の下限 1/s**。(3) **IGI**=「外れた点が理由」という報告様式(受入表に「どの時刻・どのエリアで外れたか」を書く)。(4) **交換可能性の検査**を前提条件として明記。

## 数値(そのまま使う値)

- **p の下限は 1/s**(定義から直ちに)。→ **seed 3 本 + 実測 1 本 = s=4 では p ≥ 0.25。α=0.05 の判定は原理的に不可能**。
- α=0.05 を主張するには **s ≥ 20**(= 帰無側 **19 本**)。
- 論文中の作例が使う本数: **nsim = 199 / 999 / 1999 / 2999**。著者の推奨(逐語): "**for testing, if just possible, we recommend to use a large number of simulations**"。
- 測度の選び方: 少数しか回せないときは 'erl' と 'area' が積分型の極値に強く、'cont'・'qdir' が最大値型に強い。"If the type of extremeness is unknown, then the 'area' measure can be preferred."

## コスト/スケール含意

| 判定 | 必要 seed | 39 万体(9.17 h) | 5,000 体(0.5 h) |
|---|---|---|---|
| 記述の帯(検定でない) | 3 | 27.5 h | 1.5 h |
| 大域包絡 α=0.05(s ≥ 20) | **19** | **174 h = 7.3 日** | **9.5 h** |
| 著者推奨水準(199) | 199 | 1,825 h = 76 日 | 100 h = 4.2 日 |

→ **α 付きの曲線判定は 5,000 体の階層でしか回らない**。39 万体は記述用。

## 批判・限界

- **大域検定はラン数を食う**——点ごとの帯より本質的に高い。これが我々にとっての主な制約。
- 交換可能性が崩れると厳密性が失われる(著者が明記)。合成帰無では付録 C の 2 段階手続きが要る(**本メモでは手続きの逐語を取っていない**)。
- **JSD のような 1 スカラーに畳んだ指標には使えない**(曲線として扱う必要がある)。H1 を JSD ではなく 120 点の曲線として扱い直す設計変更が要る。
- 原典 Myllymäki et al. (2017) JRSS-B の本文は**未読**(抄録のみ)。必要シミュレーション数の指針は Myllymäki & Mrkvička (2020) の別論文にあると本文が言及しているが **未読**。

## 関連

[[stats__currie-cheng2016_output-analysis]](Bonferroni の側)・[[ensemble__ecmwf_ensemble-size]](交換可能性・fair score)・[[validation__sargent2016_interval-test]]・`../v2-statistics-causal-research.md` §1-4・事前登録 v1.3 の S1-d
