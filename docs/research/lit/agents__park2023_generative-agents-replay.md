# Park et al. 2023 — Generative Agents: Interactive Simulacra of Human Behavior(replay/inspect と逸話の扱い)

- リンク: https://arxiv.org/abs/2304.03442 | 分野: 検証と V&V #22 / 計算社会科学 #25 | 重要度: **P1**
- **一次確認**: **サブ実読**(2026-09-17・ar5iv 版 <https://ar5iv.labs.arxiv.org/html/2304.03442> の本文を 2 回に分けて取得し、§3.1.1・§5・§6.1・§6.3・§7.1.1・§7.1.2・§7.2・§8.2 を逐語採取)。**親未確認**。**arXiv の原典 PDF は未取得**=数値は原典で再確認が要る。UIST 2023 の会議版との異同も未確認。
- **既存メモとの関係**: 本メモは**観察の道具と逸話の扱い**に絞る。アーキテクチャ(記憶・内省・計画)側は本 repo の既存答申が扱っており、ここでは触れない。

## 主張(claim)

25 体 × 2 ゲーム日のサンドボックスで、**評価は「無作為に選んだ 1 体の replay + 記憶ストリームの全開示」を単位に行い**、創発の主張(情報伝播・関係形成・協調)は**逸話のままにせず全体への聞き取りと記憶の裏取りで数値に降ろす**。逸話が出てくるのは「失敗の 3 型」の側だけ。

## 機構(mechanism)— 観察の道具

| 層 | 実体 | 逐語 |
|---|---|---|
| 状態 | サーバ側の 1 個の JSON | "**The server maintains a JSON data structure that contains information about each agent in the sandbox world**"(§5)/ "The agent's output action then updates the JSON, and the process loops for the next time step."(§5) |
| inspect | アバタのクリック | "**The complete natural language description of the action can be accessed by clicking on the agent's avatar.**"(§3.1.1) |
| replay | 評価者が 1 体の生活を見る | "**watching a replay of a randomly chosen agent's life in Smallville**"(§6.1)・"**Participants had access to all information stored in the agent's memory stream.**"(§6.1) |

**「巻き戻し可能なデバッガ」は存在しない**。あるのは (1) 状態が 1 個の JSON (2) クリックで全文 (3) 記憶ストリームの全開示 の 3 つで、replay はその再描画。

## 「逸話を結論にしない」の実行形(§7.1・これが本メモの本体)

物語 → 数 → 裏取り の 3 段:

1. **物語**: Isabella がバレンタインのパーティを企画する / Sam が市長選に出る。
2. **数**: "we measure the spread of two specific pieces of information over two days in the game world"(§7.1.1)。**2 ゲーム日の終わりに 25 体全員へ聞き取り**("we conduct interviews at the end of the two game days with each of the 25 agents")。
3. **裏取り**: "**we verified that the agents did not hallucinate their responses by locating the specific dialogue in their memory stream.**"(§7.1.1)

結果(§7.1.2):

| 指標 | 値 |
|---|---|
| 市長選の認知 | 1 体(4%)→ **8 体(32%)** |
| パーティの認知 | 1 体(4%)→ **13 体(52%)** |
| 関係網の密度 | **0.167 → 0.74** |
| 幻覚 | **453 応答中 1.3%(n=6)** |
| パーティ出席 | 招待 12 体中 **5 体**(欠席 7 = 予定衝突 3 / 関心はあるが計画せず 4) |

## 逸話が出てくる唯一の場所(§7.2 Boundaries and Errors)

"identifying **three common modes of erratic behavior** that future research could address and improve upon"(§7.2)。

- 型1: 場所を覚えるほど不自然な場所を選ぶ。"some agents chose less typical locations for their actions, potentially making their behavior less believable over time"(昼食にバー)
- 型2: "erratic behaviors caused by **misclassification of what is considered proper behavior**"(一人用トイレへの入室・17 時以降の店舗)
- 型3: "we observed possible effects of **instruction tuning**"。過度に礼儀正しく協調的で、Isabella は "**rarely said no**"

**成功の証拠に逸話は使われていない。** 逸話は失敗の型に名前をつけるためだけに使われる。

## 評価設計(§6)

- 100 名(Prolific)・within-subjects・所要 ≈30 分・5 条件(全構成 + ablation 3 + 人間クラウドワーカ)の**順位づけ**。
- 体は "sampled from the end of a two game day simulation with the full architecture"(§6.1)。
- §6.4 は第一著者による帰納的分析(inductive analysis)で条件間の質的差を見る。

## 効く箇所(seam)

- **M1(個体カルテ)の直接の先行**。「クリック 1 回で 1 体の全文」を、v2 では UI なしのファイルで満たせる。
- **抽出は無作為**("randomly chosen agent")。v2 の抽出規則(答申 §2 O5)の根拠。
- **裏取りの可能性が観察の価値を決める**: カルテがなければ「幻覚率 1.3%」は計算できなかった。**M1 の存在理由そのもの**。

## 「結論でなく機構として」の入れ方

- **借りない**: サンドボックス UI・絵文字表示・Prolific 評価。
- **借りる**: (1) **無作為抽出 + 全開示**という評価の単位。(2) **物語 → 全体への問い直し → 記録での裏取り**の 3 段。(3) **逸話は失敗の命名にだけ使う**という線。

## 批判・限界(著者自身の留保)

- §8.2 評価は "**limited to a relatively short timescale and a baseline human crowdworker condition**"。クラウドワーカ基準線は "did not represent the maximal human performance"。
- "the robustness of generative agents is still largely unknown"(prompt hacking・memory hacking・幻覚)。
- 費用: 25 体 2 日で "costing thousands of dollars in token credits and taking multiple days to complete"。
- **本メモの数値はすべて ar5iv 経由**。原典 PDF での再確認が済んでいない。

## 関連

[[abm__grimm2020_odd-observation]](観察の ODD 上の位置)・[[abm__grimm-railsback2012_pom-multiscope]](1 パターンでは結論にならない)・[[validation__larooij2025_generative-abm-validation]]・`../v2-micro-observation-research.md` §1-1
