# Atil et al. 2024/2025 — Non-Determinism of "Deterministic" LLM Settings

- リンク: https://arxiv.org/abs/2408.04667 | 分野: 計算機科学(並列・決定論)#28 / 自然言語処理 #27 | 重要度: **P0**
- **一次確認**: **抄録のみ**(2026-09-17・サブが abs ページを取得。**本文は未読**=TAR の実数値は空欄)。**親未確認**。v1 2024-08-06 / v5 2025-04-02。著者 Berk Atil, Sarp Aykent, Alexa Chittams, Lisheng Fu, Rebecca J. Passonneau, Evan Radcliffe, Guru Rajan Rajagopal, Adam Sloan, Tomasz Tudrej, Ferhan Ture, Zhe Wu, Lixinyu Xu, Breck Baldwin。

## 主張(claim)

**「決定論的」に設定した LLM でも、同じ入力に同じ出力は返らない。**

- 抄録: 「outputs can vary for the same inputs under settings expected to be deterministic」
- 抄録: 「**none of the LLMs consistently delivers repeatable accuracy across all tasks, much less identical output strings**」

## 機構(mechanism)

- 実験: **5 モデル × 8 タスク × 10 回**、zero-shot と few-shot の両方。
- 原因の推測(抄録): 「non-determinism perhaps essential to the efficient use of compute resources via **co-mingled data in input buffers**」——**バッチ内で他の要求と混ざることが原因**とされ、構造的で当面消えないと著者は書いている。
- **指標 2 つ**: **TARr@N**(N 回の生出力の全一致率)/ **TARa@N**(解析後の答えの一致率)。
  - **注**: 抄録は「temperature 0」「greedy decoding」の語を使っていない。「決定論的とされる設定」という一般的な言い方。

## 数値(出所つき)

- 「We see **accuracy variations up to 15%** across naturally occurring runs」
- 「**gap of best possible performance to worst possible performance up to 70%**」
- **TAR の具体値は抄録に無い**(本文・リポジトリ側=空欄)。

## 効く箇所(seam)

[行動契約書 §7](../../design/v2-action-contract.md) **段4「採用後は語彙に加わり 2 回目以降は決定論参照(判例化)」**。この 1 行の実現方法が本論文で決まる。

## 「結論でなく機構として」の入れ方

- **借りない**: 数値、モデル比較。
- **借りる**:
  1. **「温度 0 で呼び直す」では段4 の決定論は作れない**。**採用済みの契約行を表として引く**(辞書・契約表・manifest に版で固定)形でしか同一性は保証されない。→ **ユーザー決定(ラン内に裁定 LLM を入れない)は、指紋の最小化だけでなく決定論の要請からも正しい**。
  2. キャッシュを使う場合、**完全一致キー**(未定義語の正規化文字列 + 語彙版)に限る。**意味キャッシュ(近似一致)は不可**——近い語が同じ裁定に吸われるのは、段0 辞書の「意味の損失」を再生産する事故。
  3. **TARr@N / TARa@N をそのまま計測器として採る**。v2 は既にテープ再生で決定論を確認しているが、**LLM 層の同一性**は別の指標が要る。AB7 の seed 間比較(JSD 0.00007)は分布の一致であって**文字列の一致ではない**——TARr@N なら後者が測れる。

## コスト/スケール含意

同一入力で 10 回回す形の計測。v2 なら未定義語の裁定プロンプト 30 本 × 10 回 = 300 呼で、**ランの外・数分**。ゲートに入れるなら「裁定の TARa@10 = 1.0 でなければ採用しない」という形もありうる(**未検討・指紋になる**)。

## 批判・限界

- **本文未読**。TAR の実数値・どのモデルがどれだけ揺れたかは本メモでは空欄。
- API 越しの観測で、**ローカル艦隊(この repo の構成)にそのまま当てはまるかは別問題**——バッチ混在が原因なら、バッチサイズを固定した自前サービングでは事情が違いうる。ここは v2 側で測れる。
- 精度の揺れ(15%)と文字列の同一性は別の話で、抄録は両方を混ぜて述べている。

## 関連

[[causal__shah2026_agent-replay]] ・ [[nlp__choi2025_identity-drift]] ・ [D-71 答申](../v2-d71-vocab-growth-research.md) §1.4・§2-H
