# 概観 — operational validity と LLM を人間 proxy にすることの妥当性

- リンク: 原典は v1 メモに記載(Larooij & Törnberg AI Rev 2025 / operational validation replication arXiv 2508.21740 / Argyle et al. 2023 Political Analysis / Aher et al. 2023 Turing Experiments / Nature Comp Sci 2025 大規模再現)| 分野: 検証とV&V・UQ #22 / 科学哲学 #26 | 重要度: **P0**
- **一次確認**: **二次(v1 の読解メモを経由)**。2026-09-15 に親が v1 `docs/lit/measurement__validation-overview.md` を実読した。**原典は未読**(Web 取得が使用上限で停止)。Larooij & Törnberg は [RESEARCH-STATE.md](../RESEARCH-STATE.md) §2-B の B-6 で PMC 全文を読む

## なぜこのメモを v2 に起こすか

**第一目標が「世界そのものがプロダクト=再現」なのに、「妥当」「再現」が何を言うことかの整理が v2 に無い**(科学哲学 #26 は答申 2 本だけ・分野地図 §3 で「**なし**。第一目標の言葉そのもの」と書かれていた分野)。v1 はその実務側を押さえていた。

## 中核

### validation の標準と落とし穴

- **operational validity = 「表層でなく機構を捉える」**。ABM の実務は **多 seed の Monte Carlo で「正しい理由で正しいパターン」を micro/meso/macro の分布・構造で確認する**。個体やテキストの一致ではなく**マクロパターンの再現**。
- **LLM-as-judge の circularity**: LLM に自分の出力を評価させると自己 favoring・較正不良。守り方 = **別モデルを judge に / 人手検証サブセット / 行動(非自己申告)指標 / 評価者間信頼性(κ)**。
- **face validity(それっぽさ)の限界**: 機構とは緩くしか結びつかない。

### LLM を人間 proxy とすることの妥当性

- **Argyle 2023 の algorithmic fidelity**: 人口統計で条件づけると人間の**回答分布**は再現される(集団・相関・少数派も)。
- ★ **tail の過小表現**: silicon sampling は**多数派に overfit し、極端・少数派を過小表現する**。
- **効果量の水増しと sensitive topic の盲点**(Nature CS 2025): 主効果は 73-81% 再現するが**効果量は人間より大きく出る**。race / gender / ethics では再現が低い。

### 較正 = 新規の結果を信じる前に既知の結果を再現する

Turing Experiments(Aher 2023: Ultimatum / Milgram / Wisdom of Crowds の再現)の発想。**既知の社会的結果を再現できるかを sanity check にしてから、新規の主張を出す。**

## 効く箇所(seam)

1. **「多 seed のマクロパターン」は v2 の受入表と同型だが、v2 はまだ 1 本ずつしか回していない**。G-8 のアンサンブルが立つまで operational validity は主張できない。→ [[stats__lorscheid2012_replication-doe]] と同じ結論に別ルートで着く。
2. **効果量の水増し**は、この repo が既に踏んでいる可能性がある。c7-day-2 で**通報が現実の 28 倍**、c7-day-3 で 2.7 倍まで下げた経緯がある。広告の過剰反応(D-56 系)も同じ形かもしれない。**「LLM は効果量を大きく出す」は系統誤差として登録する価値がある**(未検証・親の見立て)。
3. **既知結果の再現を sanity check にする**発想は、v2 の「アンカー台帳 → holdout」と同型だが、**v2 のアンカーは全部「人流・経済の実測」で、社会心理の既知結果が 1 つも無い**。第2陣の主題が人間関係になるなら、ここに 1 本要る。
4. **LLM-judge の circularity**: v2 は W17 の多様性判定などで LLM を使っていない(物差しはエンジン側の集計)。この点は**既に守れている**。

## 「結論でなく機構として」の入れ方

数値は借りない。借りるのは **(a) 妥当性は多 seed のマクロ分布で見る (b) 新規の主張の前に既知を再現する (c) 効果量は大きく出る前提で読む** の 3 つの作法。

## 批判・限界

- **原典を 1 本も読んでいない**。効果量の数値(73-81%)も v1 メモ経由。
- v1 メモの文脈は「世界改変者は tail にいる → LLM が tail を潰すと観たい現象が消える」という v1 固有の問題設定。**v2 の第一目標は再現なので、tail の扱いは別の意味を持つ**(再現したい分布に tail が含まれるか、という問いになる)。
- なお **v2 の D-68 答申は Argyle 2023 を DOI つきで正しく押さえている**(「these 'silicon samples' would not emulate exact human responses at an individual level」を引用済み)。親は当初「v2 に silicon sampling の言及が無い」と見立てたが、**grep して誤りと分かった**。重複ではなく、v2 側の方が一次に近い。

## 関連

[[stats__lorscheid2012_replication-doe]] ・ [[network__complex-contagion-overview]] ・ [[compute__matsim2020_hermes]] ・ v1 `docs/lit/measurement__validation-overview.md`(出所)・v2 [d68 答申](../v2-d68-behavioral-diversity-research.md) §3
