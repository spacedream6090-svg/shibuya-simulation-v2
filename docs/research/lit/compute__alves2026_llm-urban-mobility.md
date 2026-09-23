# Alves et al. 2026 — Evaluating LLMs for Decision-Making in Agent-Based Urban Mobility Simulations

- リンク: https://arxiv.org/abs/2607.02716 | 分野: 計算機科学(並列)#28 / 交通工学 #2 / 計算社会科学 #25 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-16・サブが WebFetch で abs + `arxiv.org/html/2607.02716v1` 本文を取得)。**親確認(第202)**: Table 3 の 10 行を親が WebFetch で再読(500 体: 21.92 / 79.40 / 98.50 / 102.30 / 111.50 s・1000 体: 58.40 / 152.50 / 219.25 / 184.80 / 239.67 s)・倍率 3.62〜5.09 / 2.61〜4.10 を親が再計算・一致。倍率の文が本文に無いことも一致。。v1 のみ(2026-07-02)。**Comments 欄が無い=会議・誌名の記載なし**。著者 Bruno Cascaes Alves, Míriam Blank Born, Ulisses Gilioli Francescatto Júnior, Felipe Moura Goulart, Letícia Brandão Caldas, Marilton Sanchotene de Aguiar。

## 主張(claim)

GAMA(ABM プラットフォーム)に LLM を **API 経由の判断層**として足す。LLM は経路計算を置き換えず、「**再計画するかどうか**」だけを決める。記憶を持たせると一貫性が上がるが構成によって効き方が違う。

## 数値(出所つき)— **Table 3 が本件の目的**

Table 3 の説明(逐語 ≤125 字): 「**Computational cost and robustness analysis of the evaluated approaches,**」+「**reporting average simulation time and error rate across simulations.**」
列 = Agents | Model | Memory | Simulation Time (s) | Error Rate (%)。時間は 10 seed の平均 ± 標準偏差。Error Rate は「不正な JSON 出力を含む」処理不能応答の割合。

| 体数 | モデル | 記憶 | 実行時間 (s) | 誤り率 (%) | 規則ベース比(サブ計算) |
|---|---|---|---|---|---|
| 500 | Rule-Based | — | **21.92 ± 5.78** | — | 1.00 |
| 500 | Gemini-Assisted | No | 79.40 ± 16.04 | 0.58 | **3.62×** |
| 500 | Gemini-Assisted | Yes | 98.50 ± 10.61 | 1.17 | **4.49×** |
| 500 | OpenAI-Assisted | No | 102.30 ± 24.27 | 0.00 | **4.67×** |
| 500 | OpenAI-Assisted | Yes | 111.50 ± 12.62 | 0.00 | **5.09×** |
| 1000 | Rule-Based | — | **58.40 ± 7.79** | — | 1.00 |
| 1000 | Gemini-Assisted | No | 152.50 ± 24.62 | 0.49 | **2.61×** |
| 1000 | Gemini-Assisted | Yes | 219.25 ± 34.28 | 1.25 | **3.75×** |
| 1000 | OpenAI-Assisted | No | 184.80 ± 22.60 | 0.00 | **3.16×** |
| 1000 | OpenAI-Assisted | Yes | 239.67 ± 28.50 | 0.00 | **4.10×** |

→ **有志のまとめの「計算 3〜5 倍」は Table 3 で裏づけられる**(500 体で 3.62〜5.09 倍・1000 体で 2.61〜4.10 倍)。ただし**本文に「N 倍」という文は無い**(逐語は「**results in a substantial increase in computational cost compared to the rule-based baseline**」「**This increase is consistent across both population scales.**」のみ)。**倍率はサブが表から割った値**=親は割り算を再計算すること。

- 設定: 2 シナリオ(Localized / Extended)・**500 体と 1000 体**・1 ラン **540 サイクル(1 サイクル = 10 秒)**・**10 seed**。属性は学生 20%・就労者 60%・退職者 20%。
- モデル: 「**Google's Gemini 2.5 Flash-Lite**」と「**OpenAI's GPT-4o Mini**」・温度 1.0。**どちらも API 越し**(Agno + FastAPI + 非同期 HTTP)=ローカル推論ではない。
- Table 3 が Localized / Extended のどちらか(あるいは合算か)は**表にも本文にも書いていない**。

## 効く箇所(seam)

D-70(計算費の比較表)の **4 例目**。ただし**比較の軸が違う**:
- 本論文の倍率 = 「同じ ABM を規則ベースで回すか LLM 判断を足すか」の**相対値**。この repo に規則ベースの対照が無いので、そのままは並べられない。
- 並べられるのは**体あたり秒**: 1000 体 × 540 サイクル = 540,000 体サイクルが 152.5〜239.7 秒 = **2,250〜3,540 体サイクル/秒**。この repo は 390,067 体 × 1 シミュ日 を 9.167 h で回している。**LLM 呼の頻度が違う**(本論文は「再計画するか」の 1 判断・この repo は 6.94 呼/体/日)ので、**呼あたりで正規化しない限り比較は成立しない**。

## 「結論でなく機構として」の入れ方

- **借りない**: GAMA・Agno・API 越し推論(この repo は自前艦隊)。
- **借りる**: (1) **「LLM は再計画するかどうかだけを決め、経路はエンジンが解く」**という分業 = この repo の憲法(意思決定と発話だけ LLM)と同型。**外部の独立収束の 5 例目**。(2) **記憶を足すと時間が 1.2〜1.4 倍になる**という実測 = 第2陣の記憶設計の費用の当たり。(3) **誤り率を計算費と同じ表に並べる**という報告の形(この repo の受入表 L4 に書式エラー率がある=同じ形)。

## コスト/スケール含意

- **記憶の値段**: Gemini 1000 体で 152.50 → 219.25 s = **+43.8%**。OpenAI で 184.80 → 239.67 s = **+29.7%**。第2陣で記憶を入れるときの**下限の見積もり**(本論文の記憶は会話履歴の持ち越し程度)。
- **誤り率と記憶は相関している**(Gemini: 記憶なし 0.58/0.49 → 記憶あり 1.17/1.25 = **約 2 倍**)。文脈が長くなると書式が崩れる=この repo の書式エラー率(実効/厳密)の監視が第2陣でより重要になる。

## 批判・限界

- **API 越しの壁時計**なので、測っているものの大半がネットワーク待ちの可能性がある。GPU 時間でも呼数でもない=**この repo の艦隊(ローカル vLLM)とは値段の構造が違う**。
- 500 体・1000 体のみ。スケール則は 2 点では引けない。
- Table 3 がどのシナリオの数字か不明。
- 査読の記載なし。

## 関連

[[compute__matsim2020_hermes]] ・ [[compute__agentsociety2025_parallel_framework]] ・ [[mas__yang2024_oasis]] ・ `../v2-llm-social-sim-timeline-seed.md` #10
