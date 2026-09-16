# Wang, Gandhi, Neubig & Fried 2025 — Inducing Programmatic Skills for Agentic Tasks (ASI)

- リンク: https://arxiv.org/abs/2504.06821 | 分野: 自然言語処理 #27 / ソフトウェア工学 #29 / ABM 方法論 #21 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが `arxiv.org/html/2504.06821v1` 本文 §2.2/§2.3/§3.2/§3.3/Table 3/§5 を取得)。**親未確認**。v1 2025-04-09。著者 Zora Zhiruo Wang, Apurva Gandhi, Graham Neubig, Daniel Fried。後続論文は COLM 2025 掲載と記載(**本書では未確認**)。

## 主張(claim)

技能を**テキストでなくプログラム**で表すと、**採用前に実行して正しさを確かめられる**。この「検証の保証」が性能差の主因。

## 機構(mechanism)— v2 の「自動検査」に直結する 3 検査

- **誘導のタイミング**(§2.2): 1 エピソードごと。ただし LM 評価器で正解と判定されたものだけ——「we employ an LM-based evaluator」して「perform skill induction only on」その集合に対して。「I is instructed to take in one filtered episode e and output one or more pieces of desired skills」。**回数の閾値は無い**。
- **検証は再実行**(§2.3): 「we can readily verify their correctness by executing them and checking if tasks can be solved successfully」。元の軌跡を新技能呼び出しで書き直し、最後の技能呼以降の素行動を切り落とし(「removing any trailing primitive actions after the last call to a skill program」)、前置部分を環境で再生してから続きを解かせる。
- **3 検査**(§2.3・逐語):
  1. 「Correctness: if executing τf successfully solves the task q」
  2. 「Skill Usage: if the trajectory contains at least one call to at least one new skill」
  3. 「Skill Validity: if all skill-calling actions cause environment changes」
- **採用**: 「we add the skills being called in the trajectory τf to the agent skill library」=**呼ばれたものだけ**入る。**重複排除・統合の記述は無い**(§5 に「新サイトで既存技能を更新してもよい」とあるのみ)。

## 数値(出所つき)

- 抄録: WebArena で静的ベースラインと**テキスト技能版**をそれぞれ **+23.5% / +11.3%**(成功率)上回る。「mainly thanks to the programmatic verification guarantee」。手数は **−10.7〜15.3%**。
- §3.3(逐語 ≤125 字): 「**ASI produced programs pass verification for only 15.6% of the turns, whereas AWM adds new skills for 31.4% of the time**」=**検証を入れると採用率は半分以下**。
- §3.3 Table 3(shopping・ablation): 検証済みプログラムを**記憶に置くだけ**で **32.6 → 36.4(+4.2 pt)**。検証済みプログラムをテキスト化して記憶に置くと 39.0、**行動空間として使う完全版が 40.1**。著者は利得の大半を検証に、残りを行動空間の形に帰属。
- §3.3: 誘導に使えた正解エピソードは「70 and 58 examples for AWM and ASI」程度。

## 効く箇所(seam)

[行動契約書 §7](../../design/v2-action-contract.md) 段3(自動テスト)。D-71 答申 §2-C の 4 検査は、この 3 検査を v2 の語に翻訳したもの(**正しさ / 使用 / 妥当性** + SkillCAT 由来の **非退化**)。

## 「結論でなく機構として」の入れ方

- **借りない**: プログラム表現そのもの、WebArena の数値、オンライン誘導。
- **借りる**: (1) **3 検査の形**——特に「**Skill Validity: 技能呼が環境を変えるか**」。v2 では「採用した契約行が世界状態を実際に変えるか(空振りでないか)」=**待機に畳まれる語を弾く検査**になる。(2)「**Skill Usage: 新技能が実際に呼ばれたか**」→ v2 では「未定義台帳の該当行が実測で減るか」。(3) **採用率 15.6% という期待値**——起草の大半は落ちるという前提で、裁定バッチの件数予算を組む。(4) **検証の有無で +4.2 pt** = 検証の段は飾りでない。

## コスト/スケール含意

検証は**環境での再実行**を要する。v2 でこれに対応するのはモック 5,000 体のスモークで、**実 LLM を使わない**(語彙が増えても LLM 費用は増えない)。ASI の「再生の前置を作る」手続きは、v2 のテープ再生と同型=**既に持っている装置で実装できる**。

## 批判・限界

- Web 環境のみ。**保存則・現実整合の検査は無い**(v2 が足す必要がある部分)。
- 正解判定は LM 評価器(§2.2)で、真値ではない。
- **重複排除・剪定は無い**。
- 「検証を通った 15.6%」は**プログラムが書ける領域**だから測れた数字で、v2 の契約行(表)にそのまま移せる保証はない。

## 関連

[[agents__wang2024_workflow-memory]] ・ [[agents__wang2023_voyager]] ・ [[agents__zhao2024_learnact]] ・ [D-71 答申](../v2-d71-vocab-growth-research.md) §1.1・§2-C
