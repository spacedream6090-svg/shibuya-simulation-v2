# Rozanov & Rei 2024/2025 — StateAct: Enhancing LLM Base Agents via Self-prompting and State-tracking

- リンク: https://arxiv.org/abs/2410.02810 | 分野: 自然言語処理 #27 / ABM 方法論 #21 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-16・サブが WebFetch で abs + `arxiv.org/html/2410.02810v3` 本文を取得)。**親未確認**。v1 2024-09-21 / v2 2025-02-15 / v3 2025-04-08。Comments 欄は「9 pages, 5 pages appendix, 7 figures, 5 tables」のみ=**会議名の記載は無い**(REALM@ACL 2025 という記載は abs ページに見当たらない=[時系列の種](../v2-llm-social-sim-timeline-seed.md) #6 の「REALM@ACL 2025」は**出所不明**)。著者 Nikolai Rozanov, Marek Rei。

## 主張(claim)

追加学習も検索も使わず、**プロンプトの形だけ**で ReAct を上回る。2 部品=(1) **self-prompting**(毎手番で目標を書き直させる)(2) **chain-of-states**(状態を毎手番の出力の中に書かせる)。

## 機構(mechanism)— 出力の形がすべて

1 手番の出力が固定の行指向ブロック(§3.3・Alfworld の例):

```
>Goal: Put a clean tomato in fridge
Current Location: countertop 2
Current Inventory: None
Locations Visited: table 1, countertop 1
Thought: I find the tomato, now I need to take it.
Action: take tomato 1
```

- 付録 J.1 の実プロンプトは小文字で `>goal:` `current location:` `current inventory:` `thought:` `action:`(Locations Visited は無い)。Webshop(J.2)は `Current Selection:` に差し替え=**状態欄はドメインごとに決める**。手数のカウンタ欄は無い。
- 形式化(付録 K): 文脈ベクトル **c_t = (g_0, s_t, r_t, a_t)**= 固定目標・状態・推論・行動。

## 数値(出所つき)

- **Table 1**(Alfworld・gpt-3.5-1106・134 タスク): Act 0.41 / ReAct **0.64** / StateAct **0.77**。
- **Table 3**(逐語 ≤125 字): ReAct は「**63.7, 68.15 and 72.59, while StateAct achieves 77.04 (+13.3), 71.85(+3.7) and 83.70(+11.2)**」(gpt-3.5-1106 / gpt-4o-mini / Mixtral-8x22B)。
- **Table 2**(開放モデル 5 種の平均): Alfworld ReAct 0.58 → StateAct **0.66** / Webshop 0.26 → **0.28** / Textcraft 0.23 → **0.31**。15 セル中 ReAct が勝つのは 2 セルだけ。
- **Table 6 の部品分解**(3 開放モデル平均・Alfworld/Webshop/Textcraft):
  - ReAct 0.58 / 0.26 / 0.23
  - State+Act 0.51 / **0.31** / 0.22 ← **状態だけ入れると Webshop が最良**
  - Goal+Act **0.63** / 0.24 / 0.26 ← 目標(self-prompt)は Alfworld に効く
  - State+Thought+Act 0.58 / 0.18 / **0.34** ← Textcraft は thought が効く。**Webshop では thought が害**(0.18)
  - 全部入り 0.66 / 0.28 / 0.31
- **Table 5**(平均手数・Alfworld・gpt-3.5): ReAct **31.49** → StateAct **19.11**。状態を抜くと 22.50・目標を抜くと 20.09・thought を抜くと 23.76。
- **Table 7**(書式を JSON にすると): ReAct 63.70→62.96(ほぼ不変)だが **StateAct 77.04→58.52(−18.5)**。**書式の選び方そのものが変数**。
- **Fig. 6**: LLM が書いた状態が発見的な正解状態と一致する率 **88%**。
- 費用(逐語 ≤125 字・脚注 6): 「**Despite StateAct using a twice-longer prompt, our cost remains similar to ReAct, at around $8 for the full Alfworld run**」。few-shot 例は ReAct 590〜935 tok に対し StateAct 807〜1458 tok(約 2 倍)だが**手数が減るので総額は同じ**。

## 効く箇所(seam)

- `v2-perception-contract.md` §2.5 の**出力書式**(1 行目「理由: 」2 行目「行動: 対象: ひと言: 」)。この repo は既に**理由を先に書かせる**=thought に相当する部分は入っている。**入っていないのは「状態を書き戻させる」欄**(現在地・所持・既訪)。
- `v2-open-intent-arm-spec.md` の `OUTPUT_SPEC_OPEN`。状態欄を足す腕は**まだ無い**。

## 「結論でなく機構として」の入れ方

- **借りない**: ReAct/StateAct の実装そのもの、タスク成功率。
- **借りる**: (1) **状態欄は 3〜4 個・ドメイン語で・出力の先頭**という形、(2) **部品分解の ablation**(目標 / 状態 / 推論 の 2^3 を測る)、(3) **書式を JSON にすると崩れる**という警告=この repo が JSON を課さず行指向にしたのと同じ向き(§2.5「厳密 JSON は課さず」)の**外部裏づけ**、(4) **手数が減ればトークン 2 倍でも総額は同じ**という費用の見方。
- **重要な区別**: 本論文の「状態」は **LLM が自分で書いて自分で読む**もの。この repo の状態はエンジンが持つ。**層が違うので競合しない**。競合するのは「観測ブロック B5 に書いてやる」か「出力で書き戻させる」かの二択で、後者は**未測定**。

## コスト/スケール含意

出力トークンが増える(状態欄の分)。この repo は **o64 既定**(`v2-perception-contract.md` §2.2)なので、状態 3 欄で 20〜30 tok を食うと理由+行動が入らない可能性がある。**腕にするなら o96 以上が要る**=呼数でなく出力長の予算に当たる。

## 批判・限界

- GPT-4 級の結果が無い(gpt-4o-mini のみ・しかも +3.7 と最小)。**大きいモデルほど効かない**傾向が見える。
- 単一貪欲実行(1 回)の数字が Table 3。seed 分散の報告が無い。
- タスクは全部**単体エージェントの道具使い**。社会シミュではない。
- 状態欄は人が設計している(Alfworld/Webshop で別)=**設計者の指紋**がそのまま入る。

## 関連

[[agents__goodyear2025_state-representation]] ・ [[memory__lu2026_procedural-graphs]] ・ `../../design/v2-perception-contract.md` §2.5
