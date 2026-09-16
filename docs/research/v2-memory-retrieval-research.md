# v2記憶と想起リサーチ答申(2026-08-31・Opusサブエージェント・全出典URL付き)

<!-- hdr:v1 -->
- **分野**: 認知科学(記憶・習慣) #12 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **D** = **出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る — 出典痕跡 4 件・URL 0 件。09-02 以降の中央値 62 に対して桁が違う
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> D5下位項目①「記憶と想起」の意思決定材料。前提: 認知3層LOD(T0習慣/T1速い/T2遅い+夜間監査)・40万体・
> 状態バイト予算宣言の規律。

## 結論(推奨)

**案(c)ハイブリッド、ただし(a)構造化寄りの狭いレーンで。**
1. **T0/T1はembeddingを一切使わない**: 構造化スロット(v1の最近イベント+関係+信念cap継承)+語彙一致。
   AgentSocietyのEvent Flow/Perception Flow分離(起きたこと/態度を別スロット)を採用。
2. **T2夜間監査がconsolidationを兼ねる**: 生イベント→要約→スキーマ(Conwayの3層)へ昇格させ、
   **昇格したものだけ埋め込む**(1体8-16ベクタ上限・int8・384次元)→埋め込み生成は40万件/日=全員方式の1/20。
3. **索引は作らない**: per-agent 8-16件の全走査(µs級)。ベクタDB不要=運用の巨大削減。
4. **忘却=Ebbinghaus指数減衰+想起で減衰定数を緩める**(Jost/間隔効果)。「T2統合を通過した記憶は減衰が大幅に緩む」
   =睡眠の24時間ジャンプとも整合。
5. **バイト予算例**: 構造化3.0KB+統合ベクタ12×388B≈**7.7KB/体・40万体で3.1GB**。

(b)全員embeddingを推さない理由: 検索でなく**埋め込み生成がLLM推論とGPUを奪い合う**+**1万体超の先行例が皆無**。
(a)単独を推さない理由: 同一事象を各人が別語で記録する40万体の言語多様性に語彙一致では関係が張れず観測解像度が落ちる。

## 主要な事実

- **Generative Agents**(25体): memory stream全記録+recency(0.995指数減衰)/importance(LLM採点)/relevance(コサイン)。
  reflection=importance合計150超で発火(実測1日2-3回)。**25体×2日で数千ドル**≈$40/体日→40万体では原理的に不可。
- **1万体超でper-agent embedding検索を採用した公表例はゼロ**: AgentSociety(1万体)=構造化Stream Memory・
  OASIS(100万体)=リレーショナルDB・Project Sid=構造化WM/STM/LTM・AgentTorch(840万体)=per-agent記憶なし
  (アーキタイプ共有)。
- **GASim実測**: 1万体30ステップで記憶想起が316分=実行時間の支配項→グラフ構造化想起で16.4倍高速化。
- **検索自体は安い**(自分の記憶N=30-100の全走査=µs級・ベクタDB/ANN不要)。**真のコストは埋め込み生成側**
  (全員方式なら推定800万埋め込み/シミュ日=A100を数十分〜数時間占有)※算術は外挿・実測1本推奨。
- 日本語埋め込み: **(第203 訂正・出典 huggingface.co/cl-nagoya/ruri-small のベンチ表・親一次確認)** Ruri-small(68M・768次元)のJMTEB **71.53 は mE5-large 71.65 と同等(超えていない)**——正しい言い方は**「同等の平均スコアを1/8のパラメータで」**。mE5-small(384次元)=**69.52**。
  **旧記載「mE5-large(70.90)超」「mE5-small=67.71」はいずれも誤り**(答申 v2-r23-primary-check-batch1.md §2-5 #17)。埋め込みモデル選定の「優位」根拠は消える(U1 は判断待ちなので決定は未拘束)。
- 認知科学の錨: Murre&Dros 2015(忘却曲線再現・24h睡眠ジャンプ)・Cepeda+2006(間隔効果184論文)・
  Diekelmann&Born 2010(睡眠統合=エピソード→スキーマ変換)・Conway SMS(自伝的記憶3層・想起は構成的過程)。
- **夜間T2監査=consolidationは先行系譜あり**(SCM=Sleep-Consolidated Memory・Lyfe AgentsのSummarize-and-Forget)
  =独自でなく正当化しやすい設計。

## 3案比較(要約)

| | (a)構造化進化 | (b)全員embedding | (c)ハイブリッド |
|---|---|---|---|
| バイト/体 | 2-4KB | +11.6KB(int8)〜46KB(fp32) | +3KB |
| 実コスト | ゼロ | 埋め込み生成がGPU占有 | 1/10以下 |
| 失うもの | 別語同義の過去が繋がらない | ほぼ無し | 統合前の生イベントの意味検索のみ |
| 先行例 | OASIS 100万/AgentSociety 1万 | **無し** | 部分的(GASim/SCM) |

## 習慣の初期値(D5下位③への答え)

- Generative Agentsは**ゼロ開始ではない**(1段落のseed memoryを初期記憶に分割)。
- Lally+2010実測: 習慣の自動化は漸近95%まで**中央値66日**(18-254日)→数日のシミュ内時間でゼロからは育たない。
- **結論: T0習慣はペルソナから種を植えるのが妥当**。ただし`expedient`タグ+由来フラグ(persona由来/自書由来)を
  必ず立て、seed無しablationを回せる形に。初日以降はT2監査で本人が上書き=mechanism側へ移行する経路を確保。

## 主要出典

Park+2023(arXiv 2304.03442)・MemGPT(2310.08560)/Letta memory blocks・Memory in the Age of AI Agents
(2512.13564)・Rethinking Memory(2505.00675)・AgentSociety(2502.08691)・OASIS(2411.11581)・
Project Sid(2411.00114)・AgentTorch(2409.10568)・GASim(2605.07692)・ScaleSim(2601.21473)・
Lyfe Agents(2310.02172)・SCM(2604.20943)・Ruri/JMTEB(2409.07737)・mE5(2402.05672)・
Murre&Dros 2015(PLOS ONE)・Cepeda+2006・Klinzing+2019(Nat Neurosci)・Conway SMS・Lally+2010・
Qdrant量子化実務値。(URLはリサーチ実行ログに完全版)

> 推測と事実の切り分け: GB換算・埋め込み/日・GPU占有時間は外挿。採用前にRuri-small/mE5-smallの実機スループット計測1本を推奨。
