# Kretz 2015 — The Social Force Model and its Relation to the Kladek Formula

- リンク: https://arxiv.org/abs/1512.01426 | 分野: 歩行者動力学(群衆物理)#18 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが `ar5iv.arxiv.org/html/1512.01426` の §2「Introduction Part II: the Kladek Formula」を読み、式 (1)・(7)(8)(9)(10) と参照 [10][11] を確認)。**親未確認**。

## 主張(claim)

社会力モデル(SFM)の 1 次元マクロ極限は、歩行者の速度−密度関係に実測される変曲点を再現しない。SFM を少し拡張すると変曲点が出る。その動機づけとして **Kladek 式(都市の自動車交通のために提案され、歩行者で広く使われている速度−密度式)との関係**を論じる。

## 機構(mechanism)— Kladek 式と Weidmann のパラメータ化

- 式 (1)(§2): **v̄m = v̄f (1 − e^{−γ(1/ρ − 1/ρmax)})**(v̄m = average momentary speed、ρ = density)。
- §2「Weidmann applied the Kladek formula to describe the speed-density relation of uni-directional pedestrian flow [10, 11].」
- §2「Weidmann's parametrization of the Kladek formula to describe uni-directional, two-dimensional pedestrian dynamics is」→
  - 式 (7) **v_f = 1.34 m/s**
  - 式 (8) **γ = 1.913 1/sqm**
  - 式 (9) **ρ_max = 5.4 1/sqm**
  - 式 (10) **a = γ/ρmax ≈ 0.354**(無次元化)
- 参照 [10] = U. Weidmann, *Transporttechnik der Fussgänger*(ETH Zürich, IVT, 1993)/ [11] = Buchmüller & Weidmann (2006)。
- §2 は「Kladek 式は Kladek (1966) が自動車交通のために提案したが、実際には主として歩行者で使われてきた」とも述べる。

## 数値(出所つき)

- **v(ρ) = 1.34 · [1 − exp(−1.913 · (1/ρ − 1/5.4))]**(式 1 + 式 7-9)。
- **[再計算]** この式の値: ρ=0.238 → 1.339 m/s / 0.431 → 1.317 / 0.718 → 1.207 / 1.076 → **1.017**(サブ記載の 1.015 は誤り・親と実装テストの再計算=1.0173・第213 訂正)/ 2.15 → 0.556 / 3.33 → 0.265 / 5.0 → 0.037 m/s。

## 効く箇所(seam)

[C9 決定アジェンダ](../../design/v2-c9-geometry-agenda.md) **G2**(「密度で減速」の式)と [群衆物理設計書](../../design/v2-crowd-physics.md) §4 の空欄「Weidmann 原典」。

## 「結論でなく機構として」の入れ方

1. **借りる**: **式の形とパラメータ 3 つだけ**。v2 は 1 tick = 60 s の巡航速度を出すだけなので、CFSM を入れる前でも **辺上の平均速度としてそのまま使える**。
2. **これで R-7 の空欄が 1 行埋まる**: 群衆物理答申 :17 は「**γ=1.913 と Kladek 式の形は二次資料(検索要約)のみ・原典未読=空欄**」と書いていた。**本メモで arXiv 一次・式番号つきに昇格**(ただし原典 [10] そのものではなく、原典を引用した論文の記述である点は明示する)。
3. **借りない**: 本論文の主題である SFM の拡張(v2 は CFSM 第 1 候補で SFM は対照群)。

## コスト/スケール含意

指数 1 回・除算 2 回。39 万体で毎 tick 評価しても NumPy のベクトル演算 1 本。**逐次ループの新設にならない**(P4 宣言は不要の見込み・親判断)。

## 批判・限界

- **一次資料そのものではない**。Weidmann 1993 の原典は本調査で取得できなかった(ETH Research Collection の bitstream が HTTP 500)。**「Weidmann がそう書いた」ことの保証は Kretz の引用に依存する**。
- **単方向流・二次元**のパラメータ化。渋谷の多方向流・交差流には適用の保証がない(U15-5 が expedient 宣言している通り)。
- ρ→0 で v→v_f、ρ→ρmax で v→0 と振る舞いは良いが、**ρ > 5.4 は定義できない**(負になる)。実装では clip が要る。

## 関連

[[crowd__bosina-weidmann2018_fd-generic-model]] ・ [[crowd__morita2004_kobe-luminarie]] ・ [C9 答申](../v2-c9-position-attention-research.md) §1.3
