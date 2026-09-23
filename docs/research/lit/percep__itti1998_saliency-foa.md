# Itti, Koch & Niebur 1998 — A Model of Saliency-Based Visual Attention for Rapid Scene Analysis

- リンク: https://doi.org/10.1109/34.730558 | 分野: 知覚心理学・精神物理学 #5 / 認知科学(記憶・習慣)#12 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが著者最終稿 PDF 6 頁を `pymupdf` で抽出。§1・§2.1・§2.2・§2.3 を確認)。**出版社版(IEEE)は未取得**・**親未確認**。IEEE Trans. Pattern Analysis and Machine Intelligence 20(11):1254-1259, Nov. 1998。

## 主張(claim)

霊長類の初期視覚系に倣い、**複数の特徴マップを 1 枚の顕著性マップに束ね、動的神経回路が顕著な順に「注意される位置」を選ぶ**。場面理解という複雑な問題を、注目すべき少数の場所へ落として解く。

## 機構(mechanism)— 注意の焦点(FOA)は 1 個の状態

- §1「Intermediate and higher visual processes appear to select a subset of the available sensory information before further processing」/「This selection appears to be implemented in the form of a spatially circumscribed region of the visual field, the so-called "**focus of attention**," which scans the scene」。
- §2.1: 42 枚の特徴マップ → 正規化演算子 N(.) → 3 枚の conspicuity map(intensity / color / orientation) → 1 枚の saliency map(SM)。**N(.) は「globally promotes maps in which a small number of strong peaks of activity (conspicuous locations) is present, while globally suppressing maps which contain numerous comparable peak responses」**。
- §2.2 勝者総取り(WTA)が発火すると **3 つが同時に起きる**:
  1. 「The FOA is shifted to the location of the winner neuron;」
  2. WTA の全ニューロンをリセット
  3. 「local inhibition is transiently activated in the SM, in an area with the size and new location of the FOA」——「but it also prevents the FOA from immediately returning to a previously-attended location.」
- §2.2「Such an "**inhibition of return**" has been demonstrated in human visual psychophysics」。
- §2.2「a small excitation is transiently activated in the SM, in a near surround of the FOA ("**proximity preference**" rule of Koch and Ullman)」= **近い場所へ移りやすいバイアス**。

## 数値(出所つき)

- §2.2: 「the FOA jumps from one salient location to the next in approximately **30–70 ms** (simulated time), and that an attended area is **inhibited for approximately 500–900 ms**」(心理物理の観測に合わせてパラメータを選んだと明記)。
- §2.2: 「The difference in the relative magnitude of these delays proved sufficient to ensure thorough scanning of the image and prevented cycling through only a limited number of locations.」= **2 つの時定数の比が走査の網羅性を決める**。

## 効く箇所(seam)

[C9 決定アジェンダ](../../design/v2-c9-geometry-agenda.md) **G4**(「見る」= `待機` × 対象 = 注意の焦点・SoA 1 欄)と [知覚契約](../../design/v2-perception-contract.md) §4(注意ゲート 段2 の顕著性順位)・§6(不応期の表)。

## 「結論でなく機構として」の入れ方

1. **借りる**: **注意の焦点は 1 個の状態**という粒度。G4 案(4 B/体)は本論文と同じ粒度。
2. **★ 借りる**: **「注意したら、そこへはすぐには戻らない」(IOR)** という形。**G4 案には「外れる条件」が書かれていない**。IOR は v2 の「焦点の寿命」欄の原型になる。
3. **借りる**: **proximity preference**(次の焦点は近い側に寄る)。v2 の近接上位 k と同じ向き。
4. **借りない**: **ms の値そのもの**。Itti の IOR は 500–900 ms、v2 の起床不応期は分単位で **4 桁違う**。v2 の tick は 60 s なので、IOR を tick に写すと常に 1 tick 未満 = 表現できない。**借りるのは形だけ**。
5. **注記(親要確認)**: 知覚契約 §4 の「**Itti & Koch が否定したのは線形和**」という記述に対応する逐語は、**本論文(1998 年 TPAMI 版)には無い**。あるのは正規化演算子 N(.) の議論(上記)。Itti & Koch 2001(Nature Rev Neurosci)側の記述かもしれない → 親が確認。

## コスト/スケール含意

本論文の実装は画像処理(42 特徴マップ)で、v2 は使わない。**v2 が借りるのは「焦点 1 個 + 抑制」という状態機械**だけなので **O(1)/体**。焦点 4 B + 寿命 1 B = 5 B/体、390,067 体で **1.95 MB**[再計算]。

## 批判・限界

- **純ボトムアップ**。§2.2「Since we do not model any top-down attentional component…」= **課題や意図で注意が変わる部分は本論文の範囲外**。v2 は LLM が意図を出すので、**トップダウン側は本論文に根拠が無い**。
- 静止画のみ。**動く群衆・自分も動く状況は扱っていない**。
- 30–70 ms / 500–900 ms は **「心理物理の観測に合うように選んだ」**値であって、本論文が測った値ではない([16] が出所)。

## 関連

[[gameeng__unreal_ai-perception]] ・ [知覚契約](../../design/v2-perception-contract.md) §4 ・ [C9 答申](../v2-c9-position-attention-research.md) §1.4
