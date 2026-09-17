# Bosina & Weidmann 2018 — Creating a generic model of the pedestrian fundamental diagram

- リンク: https://www.strc.ch/2018/Bosina_Weidmann.pdf | 分野: 歩行者動力学(群衆物理)#18 / 人間移動科学 #3 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが PDF 全 33 頁を `pymupdf` で抽出。Table 2・Table 3・§3.3.1・p.10 を確認)。**親未確認**。18th Swiss Transport Research Conference, May 16-18, 2018。著者 Ernst Bosina / Ulrich Weidmann(ETH Zürich)。

## 主張(claim)

歩行者の基本図(速度−密度関係)は状況ごとに違う。**歩行者個人の特性(希望速度・体幅・反応時間など)の分布を入力にして、状況別の基本図を生成する**汎用モデルを作る。

## 機構(mechanism)— 個人の特性の幅から基本図が出る

- モデル A〜E を段階的に作り、各段で **1,000 人・時間刻み 0.1 s・持続 10,000 s**(Table 3)で走らせて速度−密度を測る。
- 歩行者の特性は **最小値と最大値の幅**として与え、`minimum / maximum / average / uniform` の 4 通りの母集団合成で基本図の帯を出す(§3.3.1)。
- 参照曲線として **Weidmann (1993) の基本図**を毎図に重ねる。p.10「The fundamental diagram for walkways presented by Weidmann (1993) is well within this range.」

## 数値(出所つき)— **Table 2(p.5)がこのメモの核**

Table 2 表題: 「Range of values for the pedestrian characteristics used for modelling the fundamental diagram.」

| Variable | Minimum | Maximum | Source(本文表記) |
|---|---:|---:|---|
| **Desired walking speed vd [m/s]** | **1.00** | **1.60** | **Bosina and Weidmann (2017)** |
| Body width wB [m] | 0.49 | 0.33 | DIN (2013), Pheasant (2006) |
| Sway width wS [m] | 0.06 | 0.04 | Murray et al. (1964), Simoneau (2010) |
| Body depth dB [m] | 0.29 | 0.17 | DIN (2013), Still (2000) |
| **Intimate distance dI [m]** | **0.20** | **0.15** | **Hall (1966)** |
| Reaction time tr [s] | 0.80 | 0.40 | Degond et al. (2015), Ma et al. (2010), Moussaïd et al. (2009) |
| Deceleration time td [s] | 1.02 | 0.49 | Hediyeh et al. (2015) |

Table 3(Simulation parameter): Number of pedestrians 1'000 / Simulation time interval **0.1 s** / Simulation duration 10'000 s / Random noise 10 % / Step formula Cavagna / Maximum acceleration **0.6 m/s²** / Reaction delay 0.2 – 0.4 s / Number of lanes 10。

## 効く箇所(seam)

[群衆物理設計書](../../design/v2-crowd-physics.md) U15-5 段階2 と [C9 決定アジェンダ](../../design/v2-c9-geometry-agenda.md) **G2**。

## 「結論でなく機構として」の入れ方

1. **★ 最重要の訂正**: **「1.00〜1.60」は年齢係数ではなく、希望歩行速度そのものの m/s の幅**。C9 アジェンダ G2 の「Weidmann 1.34 m/s × 年齢係数(1.00〜1.60)」は **掛け算にすると 1.34〜2.14 m/s = 4.8〜7.7 km/h** になり走行域に入る。repo の設計書・群衆物理答申は元から m/s と書いている。
2. **借りる**: 「個人の特性を**幅**で持ち、母集団合成の仕方(min/max/avg/uniform)を**感度の腕**にする」構え。v2 の感度試験にそのまま翻訳できる。
3. **借りる**: **Hall (1966) を 0.15〜0.20 m の 1 つの数に落として使う**という作法。v2 の d_talk・傍受 r も同じで、帯ではなく数を決める。
4. **借りない**: モデル A〜E の運動則そのもの(v2 は CFSM を第 1 候補に決めている)。

## コスト/スケール含意

1,000 人・0.1 s 刻み・10,000 s は **単方向の一次元流**の設定。v2 の 39 万体・60 s tick とは 3 桁違う。**基本図の較正にだけ使う**(実行時の刻みにしない)。

## 批判・限界

- **希望速度の幅 1.00〜1.60 の中身は本文に無い**(Bosina & Weidmann 2017 = Physica A 468:1-29, [doi:10.1016/j.physa.2016.09.044](https://doi.org/10.1016/j.physa.2016.09.044) が出所で、**有料のため未読**)。何本の研究の何パーセンタイルか、年齢別の内訳があるかは **空欄**。
- **単方向流のみ**。渋谷のスクランブルのような多方向流は本論文の範囲外(p.22「a direct comparison … has to be made with caution」)。
- Weidmann (1993) 曲線は**参照として重ねているだけ**で、式そのもの(パラメータ)は本文に書かれていない → [[crowd__kretz2015_kladek-formula]] で補う。

## 関連

[[crowd__kretz2015_kladek-formula]] ・ [[crowd__morita2004_kobe-luminarie]] ・ [[psych__sorokowska2017_interpersonal-distance]] ・ [C9 答申](../v2-c9-position-attention-research.md) §1.2
