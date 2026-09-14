# v2×世界モデル関係性リサーチ答申(2026-08-31・Opusサブエージェント・全出典URL付き)

<!-- hdr:v1 -->
- **分野**: 計算社会科学 #25 | **重要度**: P2(親判断・2026-09-15 第191)
- **一次確認**: **D** = **出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る — 出典痕跡 10 件・URL 0 件。09-02 以降の中央値 62 に対して桁が違う
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> ユーザー仮説「世界モデルのトレンドとこのシミュレーションは異なる文脈」の検証。判定=**条件付き支持**。

## 判定

系譜・会議・目的関数・評価軸のいずれで見ても両者は分離した文脈——[事実] 2025-26の世界モデル系主要
ワークショップ(ICLR World Models・NeurIPS Physical AI・ICML Assessing World Models)のscopeに
社会シミュレーションは1語も現れない。ただし「完全に無関係」の強い形は棄却——2024年末以降、世界モデル側から
社会領域へ語を拡張する動き(清華FIB研のCSURサーベイ=social simulacraを4応用領域の一つに)が実在する。

## 1. 「world model」の語の五系譜(目的関数と評価軸)

| 系譜 | 起源 | 目的関数 | 評価軸 |
|---|---|---|---|
| (a) RL/モデルベース制御 | Schmidhuber 1990→Ha&Schmidhuber 2018→DreamerV3(Nature 2025) | **方策の改善**(想像した軌跡でactor-critic訓練) | タスク報酬・単一エージェント |
| (b) 生成的世界モデル | Genie/Cosmos/World Labs。Fei-Fei Li定義=「世界を理解・推論・生成・相互作用する生成モデル」 | 生成品質。Cosmosの中心用途=**合成データ生成** | 視覚忠実度・物理整合・下流ロボット性能 |
| (c) LeCun/JEPA・AMI | エネルギーベース+潜在変数の表現空間予測 | 表現の予測可能性 | 下流転移 |
| (d) LLM内部世界モデル論争 | Othello-GPT(肯定)vs Vafa+(否定)・Gupta&Pruthi=「比喩自体が機構を覆い隠す」批判 | — | プローブ精度・因果介入 |
| (e) 認知科学の原義 | **Craik 1943**「頭の中の小規模モデル」・forward model・能動的推論(予測誤差を知覚更新か行動で最小化) | — | 行動・神経データ適合 |

[事実] 語の分裂は当事者も自認(2026サーベイ「解釈により比較不能」・2604.22748)。

## 2. コミュニティの系譜的関係(事実)

- **世界モデル側→社会側の引用はほぼ無い**: 主要WS 3つのscopeに社会シム無し・Quantaの系譜記事も触れず・
  世界モデル論文がSchelling/Sugarscape等ABM古典を引く例は確認できず。
- **社会側→世界モデル側もほぼ無い**: ISTI-CNRの社会シムサーベイ(2607.13693)は"world model"を一度も使わない・
  Concordiaは「generative social simulation/GABM」を自称・Park+は"believable simulacra"。
  **DeepMindがGenieもConcordiaも作りながら別々の語を当てている=分離の好例**[推測]。
- **例外=橋渡しの単一研究室**: 清華FIB研(AgentSocietyの作者)のCSURサーベイがsocial simulacraを世界モデルの
  応用領域に位置づけ・Agentic World Modelingサーベイ(2604.22748)も社会世界の法則を含める。
- **語の借用例**: SocioVerse「A World Model for Social Simulation」は本文でworld modelを未定義
  =可視性目的のラベル借用[推測]。

## 3. 分離の証拠と実在する交差点

**分離3軸**: 目的関数(制御/生成品質 vs 機構理解・反実仮想)・対象(単一エージェントの環境予測 vs 多主体の
社会過程)・評価(画素/物理整合/報酬 vs 分布整合・統計則照合)。

**交差点の仕分け**:
- **(i) エージェントの内部モデル(最も実質的)**: LAW枠組み(2312.05230)=信念・予期・目標を推論の抽象に。
  [推測] **v2のT1発火条件(予測誤差)は能動的推論の定式と概念的に同型**——ただしv2の誤差は明示的な記号量で
  あり学習生成モデルの尤度ではない=同型は**説明の語彙どまり**(実装上の系譜接続ではない)。
- (ii) 環境生成器としての外注: 幾何・映像の層であり、保存則+台帳整合を要するv2環境層とは責務が異なる。
- (iii) シミュ→世界モデルの訓練データ: Cosmosは合成データエンジンとして実運用。社会側の同型=合成回答者
  市場だが、AAPOR 2026タスクフォースが妥当性・開示の重大リスクを警告。
- (iv) Earth-2型物理ツイン: 社会側の対応物は"social digital twin"という**別系譜**。

## 4. 用語戦略

- **リスク**: 語は3-5義に分裂・レビュアーは既定で「学習された環境ダイナミクス予測器」を期待・
  「世界モデルを持つ」主張自体が批判の的・digital twinと同じ「定義の弛緩→マーケ語化」の轍(Pinto論)。
  便益は検索性と資金アクセスのみ[推測]。
- **推奨自己呼称**: (主)**large-scale generative agent-based social simulation**(GABM系譜=DeepMind/
  Ghaffarzadegan 2024と語が一致)(副)empirically grounded social simulation・partial social digital twin。
- **関係を述べる推奨定式(3行)**:
  > 本研究は世界モデル(学習された環境ダイナミクス予測器)ではない。明示的な保存則エンジンと実測データで
  > 構成した渋谷の再現環境の上で40万のLLMエージェントを走らせる、大規模生成的エージェントベース社会
  > シミュレーションである。世界モデルとの接点は各エージェントの内部予測(forward model)と予測誤差による
  > 行動発火に限られ、世界そのものは学習されていない。

## 5. 資本・言説(事実)

2026年の世界モデル系VC投資30億ドル超(World Labs $1B調達/評価$5.4B・AMI Labs €シード最大$1.03B)。
**社会シミュレーション研究への直接波及は確認できず**。隣接の合成回答者市場には$1.5B超(Aaru $1B評価)。
[推測] 資金の波及経路は「世界モデル」でなく「LLMエージェント+合成データ」側=便乗すべき語も後者。

## 6. 仕分け(結論)

- **利用しうる**: forward model/予測誤差/能動的推論の**語彙**をT1発火の説明に借りる(認知科学の原義に接続・
  査読上安全)/v2出力の合成行動データ提供(AAPOR級の妥当性表示が前提)。
- **利用すべきでない**: 生成世界モデルを環境エンジンに据える(保存則・台帳の検証可能性を失う)/
  自己呼称としての"world model"(誤解コスト>便益)/Earth-2型物理ツインとの同一視(検証体系が別物)。

## 主要出典

Wikipedia world model系譜・DreamerV3(2301.04104/Nature 2025)・Fei-Fei Li "From Words to Worlds"・
NVIDIA Cosmos(2501.03575)・LeCun(2306.02572)・Othello-GPT(2210.13382)/Nanda・NeurIPS 2024(2406.03689)・
Vafa+(2507.06952)・Gupta&Pruthi(2511.12239)・Craik 1943書評・能動的推論(S0301051123002612)・
語の分裂サーベイ(2604.22748)・ICLR/NeurIPS/ICML各WS CFP・Quanta 2025-09-02・ISTI-CNRサーベイ(2607.13693)・
Concordia(GitHub/2411.07038)・GABM(Ghaffarzadegan・SDR 2024)・清華CSUR(2411.14499/ACM)・
AgentSociety(2502.08691)・SocioVerse(2504.10157)・LAW(2312.05230)・RAP/WebDreamer(2411.06559)・
検証基準(2506.19806)・AAPOR合成回答者2026・Earth-2・social digital twin(Smart Cities 2025)・
Pinto(Bricks To Bytes)・Forbes 2026-06-30・Crunchbase(AMI)・TechCrunch(Aaru)。(URLはリサーチ実行ログに完全版)
