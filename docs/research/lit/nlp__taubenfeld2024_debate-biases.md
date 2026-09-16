# Taubenfeld et al. 2024 — Systematic Biases in LLM Simulations of Debates

- リンク: https://arxiv.org/abs/2402.04049 | DOI: https://doi.org/10.18653/v1/2024.emnlp-main.16 | 分野: 計算社会科学 #25 / 自然言語処理 #27 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-16・サブが WebFetch で abs + `arxiv.org/html/2402.04049v3` 本文を取得)。**親未確認**。v1 2024-02-06 / v2 2024-09-28 / v3 2024-12-17。Comments 欄「Published as a conference paper at EMNLP 2024」。著者 Amir Taubenfeld, Yaniv Dover, Roi Reichart, Ariel Goldstein。

## 主張(claim)

政治的立場を指示しても、LLM エージェントは**基底モデル自身の社会的偏り**に寄る。自己微調整で基底の偏りを動かすと、エージェントの振る舞いも**そちらへ追随する**=偏りの出所はペルソナでなくモデル。

## 機構(mechanism)

- 話題の深刻度を **0〜10 で自己申告**させる。討論前と各ラウンド後に測る。温度 0。**アンケートの回答は会話履歴に入れない**(測定が会話に混ざらない設計)。
- 2〜3 体の討論(Republican / Democrat ± Default =「You are an American」)。**40 体の共和党ペルソナ・40 体の民主党ペルソナを LLM が生成**し、1 条件 **40 反復**(毎回ペアを変える)・平均と標準誤差を出す。
- 自己微調整: 10 個の種質問 → LLM が 100 問へ拡張 → 各 20 応答(温度 1.0)= **2,000 例**。QLoRA の次語予測 1 epoch(10 分未満)。その後 DPO(β=0.5)。3 seed 平均。

## 数値(出所つき)

- **Table 1**(話題=Racism・Default エージェント・最終ラウンド・Mistral 7B を共和党方向へ微調整): 素の Mistral 7B = **8.4** → r=16 NWP **5.1** → r=64 **4.3** → r=128 **2.5** → r=256 **1.9** → r=8 DPO **0.4**。同時に Hellaswag/MMLU が 83.6/59.0 → 73.8/48.6(r=256)まで落ちる(DPO 版は 81.4/57.0 で能力をほぼ保つ)。
- 基底の偏りの向き(逐語 ≤125 字): 「**In all the sub-figures except the 'illegal immigration', the default agent shows a bias toward the democrat perspective.**」
- 回帰の大きさ(逐語): 「**the agent with an initially opposing view tended to significantly compromise on its opinion**」「**the lines representing the partisan agents never intersect with the line of the Default agent**」「**agents tend to adopt more moderate positions, aligning more closely with the LLM's inherent bias.**」
- 収束の速さ: 変化の大半は**最初の巡回(iteration 3)**で起き、**iteration 9 以降はほとんど動かない**ので以後の実験は 9 iteration で打ち切っている。
- モデル: gpt-3.5-turbo-instruct(主結果)・Mistral 7B(微調整)・Solar 10.7B(付録)。開放モデルは 8bit 量子化・GPU 1 枚。

## **空欄**

**党派ペルソナの回帰の大きさ(何点動いたか)は本文の文字として存在しない。** 共和党/民主党ペルソナの初期値と最終値は **Fig. 3〜9・11〜12 の画像**の中だけで、HTML にも数表が無い。取れる数値は Table 1(Default エージェントの微調整応答 8.4→0.4)のみ。図の値を取るには PDF の図を人が読む必要がある。

## 効く箇所(seam)

- **D-56 系/D-59 の広告への過剰反応**と同根かの判定材料。ただし本論文が示すのは「指示した立場より基底の傾きが勝つ」であって「刺激に過剰反応する」ではない。**同根とは言えない**(効き方の方向が違う)=判定は保留が妥当。
- 「自由意図」腕(`v2-open-intent-arm-spec.md`)の M4 行動エントロピー。**指示語彙を外しても基底の傾きは残る**ことをこの論文が示している=AB7 seed 1 で「行く/食べる」に 90% 集中したのは語彙側でなく基底側の可能性がある、という読みの外部根拠。

## 「結論でなく機構として」の入れ方

借りるのは**測定の作法**: ①測定の設問を会話履歴から外す(この repo の受入表・物差しは既に別テープ) ②**40 反復・毎回ペアを変える** ③**帰無腕として「立場を指示しない Default」を必ず置く**。3 は AB7 の vocab/open 2 腕にはまだ無い形(どちらも指示がある)。

## コスト/スケール含意

40 体のペルソナ × 40 反復 × 9 iteration ≒ 討論 1 条件で数千呼。**自己微調整は 10 分未満・2,000 例**=基底の偏りを動かす実験は安い。ただし r=256 まで上げると MMLU が 59.0→48.6 と 10 pt 落ちる=**偏りを動かす代償が能力**。

## 批判・限界

- 主結果が **gpt-3.5-turbo-instruct** 1 モデル。2026 年の 8B 級で同じかは未検証。
- 「深刻度 0〜10 の自己申告」は態度の代理であって行動ではない。
- 効果量の記述が全部定性。**本論文から数値を引くなら Table 1 だけ**。

## 関連

[[nlp__choi2025_identity-drift]] ・ [[validation__ye2026_robustness-audits]] ・ `../v2-llm-social-sim-timeline-seed.md` #5
