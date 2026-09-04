# U17「五感/VLA知覚の導入」リサーチ答申(R3 知覚契約ラウンド事前)

作成: 2026-09-02 / 調査担当: Opus 5 サブ(リサーチ実行役)
表記規約: **[事実]** = 出典の記述そのもの(URL付き) / **[推測]** = 本答申による外挿・計算 / **[未発見]** = 探したが見つからなかった

---

## 0. サマリと推奨

### 0.1 五行結論

1. **視覚情報は社会的意思決定の忠実度を上げる。しかし「生画像をVLMに食わせる」形は最良ではない。**「画像→言語化→テキストLLM」が「画像→VLM直結」を上回る測定結果がある(AgentViSS: 対話調整タスクで **31.21 → 49.60、+18.39ポイント**)[事実]。
2. **高レベルの社会的/計画的意思決定に視覚を足しても効果はほぼゼロ、低レベルの空間ナビゲーションには決定的**(EmbodiedBench: 家事計画 EB-ALFRED は視覚あり 56.3% / 視覚なし 58.0% で**差なし**、ナビ EB-Navigation は 57.7% → **17.4%** に崩壊)[事実]。v2のLLM担当領域は前者に近い。
3. **(c) VLA直結は型が合わない。** VLAの行動空間はモータ制御(関節角/EEF/キーボード・マウス)であり、v2の行動空間(社会的・経済的意思決定と発話)と一致しない。社会シムへの適用例は **CrowdVLA 1件のみ**で、規模は1シーン9体・論文自身が「数千体は compute-bound」と明記[事実]。
4. **PLATEAU LOD2 からの画像は「世界の状態」を測らない。** LOD2 には**窓もドアもなく(開口部はLOD3から)、屋内もなく(地下街LOD4.1のみ)、人も車も一切含まれず**、テクスチャは国交省自身が「航空写真由来で解像度が低く・影が含まれ・視認性に課題がある」と書いている。さらに**渋谷は単位面積あたりテクスチャ量が最悪クラス**で、国交省の技術調査では Cesium 12パターン中5パターンが**メモリ超過で描画失敗**している[すべて事実]。
5. **視覚は「レンダリング」ではなく「可視性計算」で買うのが 2〜4桁安い。** 渋谷 LOD2 の 1.39 km² を 2.5m グリッドで割ると約22万セルで、GPU加速VGA の最大構成(236,000セル / **137秒**)とほぼ同じ[事実+推測]。**全地点間の相互可視性を一度きり2〜3分で前計算できる**。

### 0.2 推奨(R3知覚契約への提案)

**採用: (a) を知覚契約の正典。ただし「テキスト」ではなく「構造化観測レコード + 決定論的可視性計算」に格上げする。**

```
知覚 = エンジンが決定論的に計算した「可視集合 + 感覚スティミュラス集合」
       → 構造化レコード → (必要な層だけ)自然言語化 → LLM
```

- v1「テキストのみ」の弱点は**テキストであること**ではなく、**可視性が計算されていなかったこと**。Generative Agents ですら可視性は「preset visual range」という**半径パラメータ1個**である[事実]。ここを isovist / Visibility Graph Analysis (VGA) で埋めるのが最もコスト効率が高い。GPU化VGAは **236,000セル・48億エッジを137秒**で処理し、depthmapX比 **239倍**高速[事実](§4.9)。**渋谷 LOD2 の 1.39 km² は 2.5m グリッドで約22万セル**[推測]なので、全域の相互可視性を一度きり2〜3分で前計算できる。
- 動的物体(人・車)の遮蔽だけは、**RGBを作らず低解像度のセグメンテーション/IDバッファか短距離レイキャスト**で毎ステップ取る((a0))。これなら PLATEAU のテクスチャ品質問題(§4.1)も VRAM 常駐問題(§4.2)も**両方消える**。
- これは憲法5「知覚されない細部は作らない」の**実装形そのもの**になる。可視集合を先に決めれば、その外側の細部生成を正当に省略できる(=カバー率が台帳に書ける)。

**限定採用: (b) VLMは「オフライン言語化器」と「現実整合アンカーの検証器」として、40万体×日次のループの外側に置く。**

3用途に限定(いずれも償却されるか、極少数):
1. **場所の静的言語化**(償却型): 街区/交差点/店舗前など**場所数 × 1回**だけ視点画像を作りVLMで記述 → 台帳に静的な「その場所の見え方」として格納。40万体×日次ではないので桁が3〜4つ落ちる。**ただし PLATEAU 由来の画像ではなく実ストリートビュー画像を使うほうが妥当な可能性が高い**(§4.1)。
2. **現実整合アンカーの検証**(SAGAI式): 実ストリートビュー画像とシム描画画像を**同一ルーブリック**でVLM採点し乖離を測る。これは「歪む場所の宣言」に直結する測定手段になる。SAGAIは LLaVA-1.6-Mistral-7B 4bit・**無料Colab枠で 1,200–1,300 images/hour**、7,000–8,000枚を2.5時間で処理[事実]。**この測定は「(b)を採らない」という決定を根拠づけるためにも価値がある。**
3. **T2昇格時のon-demand視覚**(極少数): 認知LODのT2に昇格した極少数のエージェント・極少数の場面のみ。実都市3Dの最先端(Virtual Community, 800m四方)ですら **A100 1枚で RGB は 1 Hz**[事実]という事実に照らして頻度を決める。

**不採用: (c) VLA直結。** ただし「歩行の局所回避」だけを切り出す将来の選択肢としては残す(CrowdVLAが唯一の先行例)。

**五感の残り**: 音・匂い等は「**発生源が自己申告するスティミュラス**」型で統一する(商用ゲームAIの標準設計。Unreal Engine の AI Perception は視覚=半径+登録済みスティミュラス源、聴覚=Report Noise Event という**明示的に宣言された刺激**であり、レンダリングでも音場計算でもない[事実])。知覚契約のフィールドをモダリティで拡張可能にしておけば、後から足せる。

**そして視覚より先に内受容感覚を入れるべき。** §5.3 の通り、空腹・疲労・体温は (i) LLM呼び出しを1回も増やさず、(ii) 効果検証が存在し(Humanoid Agents: health を0にすると健康関連活動が **+156%**)、(iii) **渋谷に直結する実測アンカーがある**(熱環境下の歩行者は日陰の距離を係数 **0.86** で割り引く — Scientific Reports 2022)[すべて事実]。**(a)/(b)/(c) のどれよりも安く、どれよりも検証がある。**

### 0.3 なぜこの結論か(5つの決定的な数字)

| 論点 | 数字 | 含意 |
|---|---|---|
| 高レベル意思決定に視覚は効かない | EB-ALFRED 56.3%(視覚あり) vs 58.0%(視覚なし)[事実] | v2のLLM担当=高レベル。視覚投資の回収先がない |
| 言語化 > 生画像 | AgentViSS 対話調整 49.60(言語化視覚) vs 31.21(直接視覚)[事実] | 生画像を渡すこと自体が損。「言語化」に投資すべき |
| 規模の壁(LLM側) | OASIS(**テキストのみ**)で100万体 = **27×A100 で1タイムステップ18時間**[事実] | 7×A5000で40万体に視覚を足す余地は、LOD前提でしか存在しない |
| 規模の壁(描画側) | Virtual Community(実都市3D、**800m四方・建物53棟**)は **A100 1枚で RGB を 1 Hz、depth を 100 Hz**[事実] | 実都市3Dの最先端が「RGBは秒1枚」。40万体×毎ステップとは2〜3桁の差 |
| 素材の壁 | 渋谷 LOD2 の4メッシュで**テクスチャ画像 4,264枚 / 501MB**、Cesium検証で**12パターン中5パターンが描画失敗**[事実] | 都市規模の制約は三角形数ではなく**テクスチャのVRAM常駐** |

---

## 1. 課題1: VLA/VLMの現状(2025–2026)

### 1.1 アーキテクチャの分類(何が「VLA」と呼ばれているか)

[事実] サーベイ *Vision-Language-Action Models for Robotics: A Review Towards Real-World Applications* は、VLAを7系統に分類する:

| 系統 | 代表モデル |
|---|---|
| Transformer + 離散アクショントークン | VIMA, Gato, RT-1 |
| Transformer + 拡散アクションヘッド | Octo, NoMAD |
| Diffusion Transformer | RDT-1B, LBMs |
| VLM + 離散アクショントークン | RT-2, OpenVLA, GR-1 |
| VLM + 拡散アクションヘッド | Diffusion-VLA, ChatVLA |
| VLM + Flow Matching ヘッド | π0, π0.5 |
| VLM + Diffusion Transformer | GR00T N1 |

出典: https://arxiv.org/html/2510.07077

**[重要]** どの系統も**出力は連続的なモータ指令**(関節角/エンドエフェクタ位置/速度)である。「行動」の意味がv2と異なる。

### 1.2 実測性能(パラメータ数・レイテンシ・制御周波数)

[事実] *A Survey on Efficient Vision-Language-Action Models* の Table I:

| モデル | パラメータ | 推論レイテンシ | 制御周波数 |
|---|---|---|---|
| RT-2-PaLI-X (large) | 55B | 330–1000 ms | 1–3 Hz |
| RT-2-PaLI-X (small) | 5B | 200 ms | 5 Hz |
| OpenVLA | 7B | 166 ms | 6 Hz |
| π0 | 3.3B | 73 ms | 20/50 Hz |

出典: https://arxiv.org/html/2510.24795v1

[事実] GR00T N1: 公開版 GR00T-N1-2B は総パラメータ 2.2B(うちVLM 1.34B)。16アクションチャンクのサンプリングは **L40 GPU / bf16 で 63.9 ms**。System 1(拡散制御ポリシー)は 120Hz で閉ループ動作。
出典: https://arxiv.org/html/2503.14734v1

[事実] 学習コストの桁: OpenVLA の事前学習は **21,500 A100-GPU時間(64GPUクラスタ)**、π0 は **10,000時間のロボット軌跡データ**。
出典: https://arxiv.org/html/2510.24795v1

**[推測] v2への含意**: 7B級VLAで 166ms/推論・6Hz は「1体のロボット」の数字。40万体には**7桁足りない**。効率化技術(SmolVLAの視覚トークン64/frame、BitVLAの3.36×メモリ圧縮、RLRCの90%スパース化[事実、同出典])を全部積んでも桁が埋まらない。

### 1.3 何ができて何ができないか

[事実] *10 Open Challenges Steering the Future of Vision-Language-Action Models* が挙げる10課題(https://arxiv.org/html/2511.05936):

1. **Multimodal Sensing and Perception** — RGB依存、深度知覚が弱く、反射・レンズフレア等の環境ノイズに弱い
2. **Robust Reasoning** — pick-and-place のような単純タスクでも不完全、長期タスクで劣化
3. **Quality Training Data** — Open-X-Embodiment の100万エピソード超で学習してもOOD環境に脆い
4. **Evaluation of VLA Models** — 評価が WidowX / Franka の数種の実機ベンチに偏る
5. **Cross-Robot Action Generalization** — 行動空間/自由度が違う機体へ汎化しない
6. **Resource Efficiency** — 小型化すると性能が大きく落ちる(容量-効率トレードオフ)
7. **Whole-Body Coordination** — 移動と操作の同時協調が未解決
8. **Safety Assurances** — 有害行動を防ぐガードレールがない
9. **VLA Models in Agentic Frameworks** — **マルチエージェントVLAは未開拓**
10. **Human-Robot Coordination** — 双方向の対話・確認要求が未発達

**課題9が本件に直撃**: 「マルチエージェントVLAは未開拓」= 40万体の社会シムに使う先行例が業界的に存在しない、というサーベイ自身の宣言。

### 1.4 空間推論の弱さ(定量)

[事実] **ViewSpatial-Bench**: 10のベースラインモデル(InternVL2.5 2B/8B, LLaVA-NeXT-Video, LLaVA-OneVision, Llama-3.2-Vision, Kimi-VL, Qwen2.5-VL 7B, GPT-4o, Gemini-2.0-Flash)の全体精度は **27.49%〜43.24%**、**ランダムベースラインは 26.33%**。カメラ視点(自己中心)からの空間定位精度は平均 33.2% で、人間視点(他者中心)の 35.7% を**下回る**という反直感的パターン。
出典: https://arxiv.org/html/2505.21500v2

[事実] **Spatial-DISE**: 28のSOTA VLMを評価し「current VLMs have a large and consistent gap to human competence, especially on multi-step multi-view spatial reasoning」。
出典: https://arxiv.org/abs/2510.13394

[事実] **街路画像に限った評価**: GPT-4V/GPT-4o/Gemini は歩行者・車両の正確な計数に失敗、道路幅は「実際の1〜2倍高い」推定、建物階数は遮蔽・透視効果で不能、建築年代は最大10年ずれる。GPT-4V は車が多いと回答拒否する。
出典: https://arxiv.org/html/2408.12821v1

**[推測] v2への含意**: 渋谷の「人が何人いるか」「どれだけ混んでいるか」をVLMに画像から読ませるのは、**エンジンが既に正確に知っている値を、精度を落として再取得する行為**になる。パターン台帳ゲートを通らない。

### 1.5 シミュレーション内エージェントへの適用例

**存在する2件**:

**(1) CrowdVLA — 群衆シミュレーションへのVLA適用**(本件に最も近い先行例)
[事実]
- 基盤: **Qwen3-VL-2B-Instruct + LoRA**
- 行動空間: **64個の離散モーションプリミティブ**(各20フレーム区間)
- 知覚: 「各エージェントのやや後方に置いた三人称カメラ」による agent-centric な観測(Unityで再構成した環境から生成)。解像度の明記なし。加えてグループメンバの相対位置・目的地座標・残時間を条件付け信号として与える
- 推論頻度: 毎フレームではなく **20フレームのモーションスキル周期**(シミュレーションは25fps)
- 規模: 比較図で「1シーンに9体が交差」。論文自身が「**VLM-based policies face scalability challenges as agent count grows**」「**thousands of agents remain compute-bound**」と明記
- 学習: **8× NVIDIA A100**
- 限界(論文明記): モーションスキル離散化が細かい制御を制約、規範遵守はシーン固有の意味定義に依存、活動やグループ形成といった長距離の意図は部分的にしかモデル化されていない

出典: https://arxiv.org/html/2604.05525v1

**(2) SIMA / SIMA 2 — 3D仮想世界の汎用エージェント**
[事実] SIMA は「プレイヤーが見るものを見て、自然言語指示を理解し、通常のキーボード・マウス操作で行動する。APIやソースコードへのアクセスを必要としない」。
出典: https://deepmind.google/blog/sima-generalist-ai-agent-for-3d-virtual-environments/ , https://arxiv.org/abs/2404.10179

[事実] SIMA 2:
- 基盤: **Gemini Flash-Lite**(レイテンシ制約でProではなくFlash-Liteを選択と明記)
- 知覚: **720p の RGB 動画フレームのみ**。「The agent does not receive any privileged information from the environment, such as an underlying state.」= 特権的状態を一切受け取らない
- 行動空間: 96個の標準キーボードキー + マウスクリック + 離散化したマウス相対移動を、構造化テキストとして出力
- 限界(論文明記): 「very long-horizon, complex tasks」が苦手、「a relatively short memory of its interactions—it must use a limited context window to achieve low-latency interaction」
- 計算コスト・同時実行エージェント数の記載: **なし**

出典: https://arxiv.org/html/2512.04797v1

**[推測] 読み方**: SIMA系は「1体のエージェントが人間と同じ入出力で遊ぶ」ことを目的にしており、**多数体の社会を回すことは目的ではない**。CrowdVLAは多数体を目指しているが、著者自身が数千体でcompute-boundと認めている。**40万体×VLA の先行例は未発見**。

---

## 2. 課題2: LLM社会シム/ゲームAIでの視覚知覚グラウンディング先行例

### 2.1 Generative Agents 系 — 「木構造の世界 → 自然言語」

[事実] Generative Agents (Park et al.):
- 「we represent the sandbox environment—areas and objects—as a tree data structure, with an edge in the tree indicating a containment relationship in the sandbox world.」
- 「We convert this tree into natural language to pass to the generative agents. For instance, 'stove' being a child of 'kitchen' is rendered into 'there is a stove in the kitchen.'」
- 「Agents build individual tree representations of the environment as they navigate it — subgraphs of the overall sandbox environment tree.」= **エージェントごとの部分グラフ**(=既知/可視の管理)
- 「The sandbox server is also responsible for sending all agents and objects that are within a **preset visual range** for each agent to that agent's memory.」= **可視範囲は半径パラメータ1個**
- オブジェクト状態: エージェントが物に作用したとき「we prompt the language model to ask what happens to the state of the object」(コーヒーメーカー "off" → "brewing coffee")

出典: https://ar5iv.labs.arxiv.org/html/2304.03442

**[推測] v2への含意**: v1「テキストのみ」の直系。**可視性が「半径」1個**なのが最大の粗さ。ここを isovist/VGA に置き換えるだけで、レンダリングなしに大幅な忠実度向上が得られる余地がある。

### 2.2 Minecraft 系 — 視覚を「持たない」ことを明言している

[事実] **Voyager**:
- 「Voyager does not currently support visual perception, because the available version of GPT-4 API is text-only at the time of this writing.」
- 「Our work's focus is on pushing the limits of GPT-4 for lifelong embodied agent learning, rather than solving the 3D perception or sensorimotor control problems... we rely on the high-level Mineflayer API to control the agent.」
- 観測形式: インベントリ、近傍ブロック・エンティティ、バイオーム、座標、体力・空腹度(すべて構造化テキスト)
- 「Voyager has the potential to be augmented by multimodal perception models to achieve more impressive tasks.」(将来課題として明記)

出典: https://arxiv.org/html/2305.16291

[事実] **Project Sid**(1000体超のエージェント社会):
- 限界(§7): 「**The primary challenge lies in agents' lack of vision and spatial reasoning, limiting their basic Minecraft skills, particularly in spatial navigation and collaborative skills, such as building structures.**」
- 規模: 文化伝達実験で500体。「We have also simulated societies with over 1000 agents, but these runs **exceeded the computational constraints of our Minecraft server environment**, causing agents to be sporadically unresponsive.」(=LLMではなく**サーバ側**の制約)
- APIコスト・トークン使用量・ハードウェア要件の記載: なし

出典: https://arxiv.org/abs/2411.00114 , https://arxiv.org/html/2411.00114v1

**[推測] 読み方**: 「視覚がないことが限界だった」と当事者が言っている。ただしその限界は **建築と空間ナビゲーション**という**低レベル空間タスク**に集中しており、社会的振る舞い(専門分化・課税制度・宗教の発生)は視覚なしで創発している。これは EmbodiedBench の測定(§2.5)と完全に整合する。

### 2.3 SimWorld — 都市規模UE5シミュレータ + LLM/VLMエージェント(最も近い設計先行例)

[事実]
- 基盤: **Unreal Engine 5**
- 知覚(2系統を**併存**させている):
  - 視覚: 一人称視点のカメラ入力3種 —「(1) color images capturing the raw visual appearance of the environment, (2) depth maps encoding geometric distance from the agent's viewpoint, and (3) semantic segmentation masks」
  - 構造化: 「high-level spatial and semantic representations, including a **semantic scene graph** and GPS-like localization information」
- 規模: 「20 agents controlled by the same language model」、競争シナリオで24体
- コスト: 各シミュレーションステップで「**around 7000 tokens per request**」、評価ランは 5000 steps。**レンダリングのfpsやレイテンシは非開示**

出典: https://arxiv.org/html/2512.01078

**[推測] 重要**: 最先端の「都市 + VLMエージェント」シミュレータが **20体規模**。40万体との差は4桁。かつ SimWorld も**生画像だけにせず、シーングラフを併存**させている。

### 2.4 NPCへの視覚付与の実装形 — 「描画 → タグ化 → テキスト → LLM」

[事実] *Empowering NPC Dialogue with Environmental Context Using LLMs and Panoramic Images*:
- 「We put a camera at eye-level of the non-playable character which takes a **panoramic image composed of four images, each covering 90° of its view** (front, left, right, and behind).」
- パイプライン: パノラマ4枚 → **Recognize Anything Model (RAM)** で方向別(left/front/right/behind)のオブジェクトタグをJSON生成 → 並行してバウンディングスフィアが方向ベクトル付きオブジェクト名を返す(例: `Simple_Shelf2, VEC:X=-0.940 Y=-0.340 Z=0.000`)→ 両者を統合したテキストプロンプトを **GPT-4** に送る
- **画像はLLMに届く前にテキストへ変換される**
- 実装: Unreal Engine 5 + GPT-4 API
- レイテンシ・トークン数・コストの記載: **なし**

出典: https://arxiv.org/html/2604.19192v1

**[推測] v2への含意**: これは**(a)と(b)の中間形**であり、実務的に最も現実味がある。かつ v2 の場合は**RAMを使う必要すらない**——エンジンが既にオブジェクトIDを持っているので、「描画→認識」を経ずに「可視判定→オブジェクトID→方向ベクトル」を直接出せる。つまり**この論文のパイプラインの前半(描画+RAM)を丸ごと省略できる**。

### 2.5 視覚の有無を直接測ったアブレーション(最重要の証拠)

#### EmbodiedBench(2502.09560)

[事実]
- **EB-ALFRED(高レベル家事プランニング)**: GPT-4o は視覚あり **56.3%** / 視覚なし **58.0%** — ほぼ同一(むしろ視覚なしが上)
- **EB-Navigation(低レベルナビゲーション)**: 「disabling vision causes GPT-4o's EB-Navigation performance to **drop sharply from 57.7% to 17.4%**, with long-horizon planning **completely collapsing to 0%**」
- **EB-Manipulation**: GPT-4o は平均 **28.9%**(そもそも困難)
- 長期タスクの劣化: Claude-3.5-Sonnet は EB-Habitat の基本タスク96% → 長期タスク58%
- 失敗要因: 操作タスクの失敗の **33%が知覚エラー**、うち誤認識が22%

出典: https://arxiv.org/html/2502.09560v2

#### StarDojo(2507.07445) — Stardew Valley での生活シミュレーション

[事実]
- 3条件比較: Image+Text(既定) / Image Only / Text Only(7×7の局所グリッド情報のみ)
- 「removing textual input (**Image Only**) **significantly affects agents' performance across all tasks**」
- 「eliminating visual input (**Text Only**) substantially reduces success **in tasks that require navigation**」
- リアルタイム条件: pause機能を切ると「remarkably affects performance across tasks demanding timely reactions or prolonged action sequences」。虫討伐タスクでは「the target (bug) continues moving during model inference, which can take **over 10 seconds per request**」
- 結論: 両モダリティが必要。視覚は空間推論と移動、テキストは詳細な行動決定を担う

出典: https://arxiv.org/html/2507.07445v1

#### AgentViSS(2606.15152) — 視覚的社会的知性(最も v2 に近いタスク)

[事実]
- 7つのマルチモーダルLLM(Claude-Sonnet-4.6, GPT-5.4, Qwen 9B/27B/122B, GLM-4.6V, InternVL3.5-241B-A28B)を評価
- **役割演技タスクは飽和**: 全モデル平均86超、全体平均 94.37
- **相互作用管理タスクは困難**: 全体平均 57.39(Claude-Sonnet-4.6 が 71.32 で最高、InternVL が 43.87 で最低)
- **決定的な数字**: 相互作用調整(interaction regulation)で「The score increases from **31.21 under DV [direct-vision] to 49.60 under VV [verbalized-vision]**, yielding an **18.39-point gain**.」
- 「Both VV and DV consistently outperform **Text-only** across models, showing that visual evidence provides social information beyond dialogue.」
- ボトルネックの所在: 直接画像アクセスが言語化記述に劣る = モデルは「視覚認識」ではなく「**知覚から意思決定への統合**」で詰まっている

出典: https://arxiv.org/html/2606.15152

**[推測] これが答申の背骨**:
1. 視覚情報そのものは社会的判断に効く(VV/DV > Text-only)
2. **しかし届け方は「言語化」が最良**(VV > DV, +18.39)
3. かつ**高レベル判断では視覚の寄与がほぼ消える**(EmbodiedBench EB-ALFRED)
→ v2が取るべきは「**エンジンが持つ真値から、視覚的に妥当な言語化を生成する**」形。生画像を経由する必要はなく、経由すると精度が落ちる。

### 2.6 Habitat / AI2-THOR 等 embodied AI の抽象化

[事実] レンダリングスループット:
- **Habitat-Sim**: 単一スレッドで数千fps、Matterport3D シーンを単一GPU・マルチプロセスで **10,000 fps 超**
  出典: https://arxiv.org/abs/1904.01201v2
- **Habitat 2.0**: 物理有効で **25,000 simulation steps/秒 超**
  出典: https://ar5iv.labs.arxiv.org/html/2106.14405
- **AI2-THOR**: 数十fps(idle/interact で 60/30 SPS)
- **Madrona batch renderer**: 128×128 の独立画像を大量バッチ描画するとき、単純シーンで **>100,000 fps/GPU**、HSSDデータセットの幾何的に複雑なシーンでも **>10,000 fps/GPU**(GPU型番の明記なし=条件不明)
  出典: https://madrona-engine.github.io/renderer.html
  ※ 一部の二次情報にある「RTX4090/H100 で 300K/30K FPS」「HSSD 平均700万三角形」という数値は**公式ページで確認できず**、SIGGRAPH Asia 2024 の原論文(DOI: 10.1145/3680528.3687629)は ACM DL が 403 で本文取得不可。本答申では**採用しない**。

**[推測]**: 「室内スケールならレンダリングそのものは安い」。ただし**都市規模では話が変わる**(§4)。ボトルネックはレンダリングのFPSではなく **テクスチャのVRAM常駐** と **VLM推論**。

### 2.7 3Dシーングラフ — 「生画像でも生テキストでもない」第三の抽象化

[事実]
- **3DGraphLLM**: 「the first method to create a learnable 3D scene graph representation for LLMs」。3Dシーングラフは「a compact scene model, storing information about the objects and the semantic relationships between them」
  出典: https://arxiv.org/abs/2412.18450
- **GraphEQA**: リアルタイム3D metric-semantic シーングラフ + タスク関連画像をマルチモーダル記憶としてVLMのグラウンディングに使う
  出典: https://arxiv.org/html/2412.14480v2
- **GraphPad**: 「recasting perception as an interactive, language-mediated process rather than a static preprocessing step」= 知覚を**問い合わせ可能なインタフェース**として設計
  出典: https://arxiv.org/html/2506.01174v1
- サーベイ: 3DSGは「a compact, interpretable, and **queryable** abstraction of 3D environments」
  出典: https://arxiv.org/html/2606.19383

**[推測] v2への含意**: **GraphPad の「知覚 = 静的な前処理ではなく、言語で仲介される対話的プロセス」という定式化は、認知LOD on-demand昇格と同型**。「見えるものリストを全部渡す」のではなく「エージェントが問い合わせたものを返す」設計にすれば、コンテキスト量を注意(saliency)で自然に絞れる。

### 2.8 商用ゲームAIの知覚モデル

[事実] **Unreal Engine AI Perception System**:
- 「The AI Perception System is a tool within the AI framework that provides sensory data for AI, enabling Pawns to receive data from the environment such as where noises are coming from, if the AI was damaged by something, or if the AI sees something.」
- **Sight**: 「The AI Sight config enables you to define parameters that allow an AI character to 'see' things on your Level. When an Actor enters the **Sight Radius**, the AI Perception System signals an update and passes through the Actor that was seen.」= **半径 + 登録済みアクター**
- **Hearing**: 「The AI Hearing sense can be used to detect sounds generated by a **Report Noise Event**」= **音源が明示的にイベントを発行**
- **AI Perception Stimuli Source Component**: 「gives the owning Actor a way to **automatically register itself as a stimuli source** for the designated Sense(s)」= **オブジェクト側が「私はこう知覚される」を自己申告する**

出典: https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine , https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/AIModule/Perception/UAISense_Hearing

**[推測] v2への含意**: **ゲーム産業が数十年かけて到達した知覚設計は「レンダリングしない」である**。生の感覚データではなく、スティミュラス源の自己申告 + 幾何判定。これは v2 の「世界の変化はエージェント行動の結果」ドクトリン(棚が減る=店員の補充行動)とも整合する——オブジェクトが「私は今こう見える」を持つ。

### 2.9 都市 × VLM(現実側の先行例) — 検証器としての価値

[事実] **SAGAI**(Streetscape Analysis with Generative AI):
- 入力: OpenStreetMap のジオメトリ + Google Street View(1サンプル点あたり東西南北4方向) + **LLaVA v1.6 / Mistral-7B バックボーン(4bit量子化)**
- 規模: 2ケーススタディで約 **7,000–8,000枚**を処理
- 実行時間: 画像ダウンロード約80分、**LLaVA推論 約9,000秒(2.5時間)**、スループット **1,200–1,300 images/hour**
- ハードウェア: 「deployable in **free-tier Google Colab** environments」「without task-specific training or proprietary software dependencies」
- 出力する構造化指標: (1)二値分類(都市/農村)、(2)物体計数(見える店舗数)、(3)寸法推定(歩道幅[m])。点・街路セグメント単位で集計しテーマ図に

出典: https://arxiv.org/html/2504.16538v1

**[推測] v2への含意**: **これは「現実整合アンカー台帳」の測定装置になる**。同じルーブリックを (i) 実ストリートビュー画像 と (ii) シムからレンダリングした同地点画像 に適用すれば、「その場所の見え方がどれだけ一致しているか」を数値化できる。**これが (b) を採用する最も強い理由**であり、かつ **40万体×日次ではなく地点数×1回**で済む。

その他の都市×VLM研究(参考): 都市安全知覚のMLLM採点 https://arxiv.org/html/2407.19719v1 、街路評価フレームワーク MSEF(VisualGLM-6B + GPT-4、ハルビンの15,000枚超の注釈画像、客観特徴 F1=0.84、住民知覚との一致率89.3%) https://arxiv.org/abs/2506.05087 、信頼性を考慮したベンチマーク論 https://arxiv.org/html/2606.00871

---

## 3. 課題3: コスト構造

### 3.1 視覚トークンの基本定数 —「1トークン ≒ 28×28ピクセル」

これは**ベンダ横断でほぼ一致する**:

[事実] **Anthropic (Claude)**: 「Claude views images in patches instead of pixels. Each patch is a **28×28-pixel block** of the image, referred to as a visual token. An image, therefore, costs `⌈width / 28⌉ × ⌈height / 28⌉` visual tokens.」
出典: https://platform.claude.com/docs/en/build-with-claude/vision

[事実] **Qwen2.5-VL(オープンウェイト)**: パッチ 14×14、隣接4パッチをMLPマージャで統合 → 視覚トークン数 = (H/14)×(W/14)÷4 = **H×W / 784**(= 28×28 = 784)。動的解像度でアスペクト比を保つ。
出典: https://arxiv.org/html/2502.13923v1

[事実] **LLaVA-1.5**: CLIP ViT-L で 24×24 パッチ → **576 視覚トークン/画像**(標準解像度)。LLaVA-NeXT の AnyRes は高解像度画像を分割し **2,880 (5×576) トークン**。
出典: https://arxiv.org/html/2411.03312v1

#### 解像度→視覚トークン数(⌈w/28⌉×⌈h/28⌉ で計算)[推測: 上記式による計算]

| 解像度 | 視覚トークン |
|---|---|
| 224×224 | **64** |
| 256×256 | 100 |
| 336×336 | **144** |
| 448×448 | **256** |
| 512×512 | 361 |
| 640×360 | 299 |
| 1280×720 (720p) | 1,196 |

[事実] Anthropic の上限(参考): 標準ティアは長辺1568px / 視覚トークン1568上限、高解像度ティア(4.7以降)は長辺2576px / 4784上限。1000×1000 = 1296トークン、1920×1080 は標準ティアで1456×819に縮小され1560トークン。
出典: https://platform.claude.com/docs/en/build-with-claude/vision

### 3.2 「視覚トークンは既存プロンプトに比べれば安い」という反直感的事実

[推測: 上記トークン数による計算] SimWorld が報告する「1リクエスト約7,000トークン」[事実, https://arxiv.org/html/2512.01078]を基準に、画像1枚を追加したときのプレフィル増分:

| テキスト文脈 | +224² (64) | +336² (144) | +448² (256) | +512² (361) |
|---|---|---|---|---|
| 2,000 tok | +3.2% | +7.2% | +12.8% | +18.1% |
| **7,000 tok** | **+0.9%** | **+2.1%** | **+3.7%** | **+5.2%** |
| 16,000 tok | +0.4% | +0.9% | +1.6% | +2.3% |

4方向パノラマ(NPC論文式)でも: 4×224² = 256トークン = 7,000トークン文脈に対し **+3.7%**、4×336² = 576トークン = **+8.2%**。

**[推測] 含意**: **「画像を足すこと」自体のトークンコストは、既に投げている長大なテキストプロンプトに比べれば誤差レベル**。したがって (b) を否定する理由は「トークンが高いから」ではない。否定理由は以下3点:
1. **モデルを変えねばならない**(テキストLLM → VLM)。7×A5000(各24GB)ではVLMのサイズが 7B級に制約される。そのサイズ帯のVLMは空間推論が弱い(§1.4)
2. **プロンプトキャッシュを壊す**。Anthropicの推奨は「images come before text」[事実, 上記vision doc]だが、毎ステップ変わる画像を先頭に置けば安定プレフィックスのキャッシュが毎回無効化される。長い共通システムプロンプトを持つ設計ほど損害が大きい
3. **レンダリングと画像パイプラインの実装・運用コスト**が別途乗る(§4)

### 3.3 視覚トークン数 vs モデルサイズ:スケーリング則(設計上重要)

[事実] *Inference Optimal VLMs Need Fewer Visual Tokens and More Parameters*:
- 「For visual reasoning tasks, the inference-optimal behavior in VLMs is achieved by using the **largest LLM that fits within the inference budget while minimizing visual token count — often to a single token**.」
- フィットしたスケーリング則: 品質パラメータ **α=0.077(LLMパラメータ) vs β=0.015(視覚トークン数)** → 「VLM error increases significantly faster when reducing the LLM parameters compared to reducing the number of visual tokens」= **誤差はLLMサイズに対してトークン数の約5倍速く反応する**
- 計算最適な圧縮率は **1〜4トークン**(88.9%〜99.8%圧縮、元の3%未満)
- **重要な反転**: OCR/文書タスクではα=0.029, β=0.048 と逆転し、トークン数が支配的になる

出典: https://arxiv.org/html/2411.03312v2

**[推測] v2への含意**: 「視覚推論タスク」= シーンの大まかな理解、では **画像を極端に圧縮して大きなLLMに渡す**のが最適。これは「画像を言語化して大きなテキストLLMに渡す」= AgentViSS の VV 条件 と方向が一致する。逆に**看板の文字を読ませる(OCR的)用途だけは高解像度が必要**——渋谷の看板・広告を扱うなら、そこだけ別扱いにする必要がある[要判断]。

### 3.4 7×A5000 での試算

[事実] NVIDIA RTX A5000 データシート: Tensor Performance **222.2 TFLOPS**、単精度 27.8 TFLOPS、RT Core 54.2 TFLOPS、メモリ 24GB、帯域 768 GB/s、8,192 CUDAコア / 256 Tensorコア / 64 RTコア、TBP 230W。
出典: https://www.nvidia.com/content/dam/en-zz/Solutions/products/workstations/nvidia-rtx-a5000-datasheet.pdf

**[推測] 注意**: NVIDIAの「Tensor Performance」表記は慣例的に **2:4スパース込み**。密行列 FP16 はその半分 ≈ **111 TFLOPS/GPU** と見るのが安全。

**[推測] プレフィル計算(視覚トークン分のみ、FLOPs ≈ 2·N·T、MFU=0.35 と仮定)**:

| VLMサイズ | 解像度 | 視覚トークン | TFLOPs/枚 | ms/枚/GPU | 7GPU・24h上限 |
|---|---|---|---|---|---|
| 2B | 224² | 64 | 0.26 | 6.6 | 91.9 M枚/日 |
| 2B | 448² | 256 | 1.02 | 26.3 | 23.0 M枚/日 |
| 7B | 224² | 64 | 0.90 | 23.0 | 26.3 M枚/日 |
| 7B | 448² | 256 | 3.58 | 92.2 | **6.6 M枚/日** |
| 7B | 512² | 361 | 5.05 | 130.0 | 4.7 M枚/日 |

対する需要: 40万体 × 1枚/日 = **0.4 M枚/日**、×3枚 = 1.2 M、×10枚 = 4.0 M。

**[推測] 素朴には「7B・448²・1枚/日なら理論上限の約6%」で収まるように見える。だがこれは楽観的**:
- 上の計算は**視覚トークンのプレフィルのみ**。テキスト文脈(7,000トークン)のプレフィルと、出力トークンのデコード(メモリ帯域律速)が別途乗る。**実務では生成が支配的**
- 実測の裏付け: SAGAI は無料Colab枠(単一の弱いGPU)で **1,200–1,300 images/hour ≒ 0.34 img/s**[事実]。これは4bit量子化7B VLMで**記述文生成込み**の end-to-end 値
- **[推測]** これを7×A5000・バッチ推論で 20〜60倍と見積もれば **7〜20 img/s ≒ 0.6M〜1.7M 枚/日**。40万枚/日は「入るが、GPU予算のかなりの割合を食う」水準。**しかもそのGPUは意思決定LLMと取り合いになる**

### 3.5 規模の現実:先行研究のコスト実測

[事実] **OASIS**(100万体のソーシャルメディアシミュレーション、**テキストのみ**):
- 「using five A100 GPUs, we can simulate the interactions of **100,000 users over 10 time steps within two days**」
- フルスケールでは **27 A100 GPU、1タイムステップあたり18時間**(1ステップで新規投稿 約48,500件・コメント 約97,100件)
- vLLM を使用、GPUリソースマネージャがリクエストを分散
- **全エージェントが毎ステップLLMを呼ぶわけではない**: 実ユーザ行動から導いた「24次元の時間帯別活動確率ベクトル」でゲート

出典: https://arxiv.org/html/2411.11581v3

[事実] **Affordable Generative Agents (AGA)** — トークン実測:
- Stanford Town の元研究は「the entire study incurring **costs of thousands of dollars**」、embodied agents は「simulations of **2 to 3 agents costing several dollars per hour**」
- 25人町: ベースライン **25.41M ± 0.96M トークン** → AGA適用 10.86M(42.7%)
- 3人町: 4.548M ± 0.36M → 1.417M(31.1%)
- VirtualHome 単一エージェント1日: 34,327 ± 4,210 → 1,189 ± 313(**3.4%**)

出典: https://arxiv.org/pdf/2402.02053 (HTML v1: https://arxiv.org/html/2402.02053v1)

[事実] **GenWorld**(東広島市、**196,608体**の合成住民):
- 「LLM-agent simulation faces a joint grounding and scaling problem: agents should act in environments that reflect real urban constraints, yet **direct online LLM calls for city-scale populations are computationally prohibitive**.」
- 解法: 「**offline compilation of LLM-derived decision signals into lookup policies** for scalable rollout」= LLMの意思決定信号をオフラインでルックアップ方策にコンパイル
- グラウンディング: 国勢調査 + 地理空間データ、YJMob100K 携帯電話データを通勤距離の診断に使用

出典: https://arxiv.org/abs/2606.27650

[事実] **AgentTorch / Large Population Models**:
- **LLMアーキタイプ**: 「queries the LLM to inform behavior over each unique set of agents' characteristics—for instance, if behavior is informed by age and sex, there is one LLM query per different combination of age and sex」
- シミュレーション600倍・較正3000倍・分析5000倍の高速化を主張、NYC 840万体のCOVID研究
出典: https://arxiv.org/html/2507.09901v1

**[推測] 40万体×日次で成立する形は存在するか → 「全員に視覚」では存在しない。「LODで昇格した少数に視覚」なら存在する。**

先行研究がとった規模の壁の破り方は3種で、v2の認知3層LODと同型:
| 手法 | 先行例 | v2の対応 |
|---|---|---|
| 活動確率でゲート | OASIS(24次元時間帯ベクトル) | T0/T1/T2 の昇格条件 |
| オフラインでコンパイル | GenWorld(lookup policies) | T0 習慣 |
| アーキタイプで集約 | AgentTorch(属性の組合せ単位で1クエリ) | ペルソナ集約 |

### 3.6 認知LODと視覚の組み合わせ設計材料

[事実] **能動的知覚(active perception)の研究群**が「必要なときだけ見る」を定式化している:
- 「Active perception is the process of **selective acquisition of sensory information** to achieve specific goals, and has proven essential for efficient information gathering and decision making in complex environments.」(Active-O3: https://arxiv.org/html/2505.21457v1)
- Q-Zoom: 「Globally scaling entire images floods the LLM's quadratic self-attention mechanism with **thousands of visually useless background tokens**」→ クエリ依存で適応的に解像度を割り当てる(https://arxiv.org/html/2604.06912)
- GraphPad: 知覚を「静的な前処理」ではなく「対話的・言語仲介的プロセス」として再定式化(https://arxiv.org/html/2506.01174v1)

**[推測] v2への設計提案(門前条件つき)**:

```
知覚LOD-0(全員・常時): 可視集合ID + 距離 + 方向 + 密度スカラー(エンジン計算・LLM呼び出しなし)
知覚LOD-1(T1昇格時):   可視集合を自然言語テンプレートで言語化(LLM呼び出しなし・決定論的)
知覚LOD-2(T2昇格時):   「見る」を明示的なツールとして提供。エージェントが問い合わせたときだけ
                        場所の静的VLM記述(事前計算済み)を返す
知覚LOD-3(例外のみ):   その場でレンダリング+VLM。門前条件を書けた場合のみ許可
```

昇格条件の候補(要ユーザー判断): 初訪問の場所 / 予測との不一致が閾値超 / 会話相手の非言語手がかりが必要な場面 / 検証ランのサンプリング対象。

---

## 4. 課題4: レンダリングコスト(PLATEAU LOD2 からのエージェント視点画像)

### 4.0 この節の一行結論

**レンダリングのFPSは問題ではない。問題は3つ — (1) PLATEAU LOD2 が「窓もドアも人も車も屋内もない、航空写真由来の低解像度・影焼き込みテクスチャ」であること、(2) 渋谷のテクスチャ量が国交省自身の技術調査で「描画失敗」を起こしていること、(3) 実都市3Dでの唯一の先行事例が RGB を 1 Hz に落としていること。**

### 4.1 PLATEAU LOD2 に何が入っていて、何が入っていないか

[事実] **LOD定義(建築物)**: LOD2 は「面が壁/屋根/床などの役割を区別できる」レベル(`WallSurface`/`RoofSurface`/`GroundSurface` 等)。テクスチャは `app:ParameterizedTexture` で画像URIとUV座標を与える。
出典: https://www.mlit.go.jp/plateau/learning/tpc03-3/

[事実] **開口部は LOD3 から**: 「建築物モデル(LOD3)では、建築物モデル(LOD2)に含むべき地物に加え、**開口部(窓及び扉)が追加される**」「また、建築物の側面が詳細化される」。**LOD2 には窓もドアもない。** 同ページに室内(インテリア)の記載もない。
出典: https://www.mlit.go.jp/plateaudocument/toc4/toc4_02/toc4_02_01/toc4_02_01_04/_da554178-d7ce-cbf3-bd20-7834e9359422/

[事実] **テクスチャの品質について国交省自身の記述**: 「現在の3D都市モデルに使われているテクスチャは**航空写真をもとに作っているため、解像度が低かったり、撮影時の太陽高度の影響による影**が含まれていたりがあり、**視認性に課題がある**」。
出典: https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_tech_doc_0062_ver01.pdf (PLATEAU Technical Report No.62, 2024年3月)

[事実] **渋谷区(2023年度)の提供LOD**:

| 地物 | LOD | 形式 |
|---|---|---|
| 建築物 | 0, 1, **2.0, 2.2**(LOD3 なし) | CityGML, 3D Tiles |
| 道路(交通) | 1, 2, 3.0 | CityGML, MVT, 3D Tiles |
| 都市設備 | 1, 3.0 | CityGML, 3D Tiles |
| 植生 | 1, 3 | CityGML, 3D Tiles |
| 橋梁 | 2.1 | CityGML, 3D Tiles |
| 地下街 | 1, **4.1**(唯一の屋内) | CityGML, 3D Tiles |
| 地形 / 土地利用 / 都市計画決定 / 洪水浸水 / 土砂災害 | 1 | CityGML, MVT, 3D Tiles |

FBX/OBJ は直接提供されず、PLATEAU SDK で変換する。商用利用含め無償。
出典: https://www.geospatial.jp/ckan/dataset/plateau-13113-shibuya-ku-2023

[事実] **渋谷の LOD2 整備面積は 1.39 km²**(東京23区FY2022時点の地区別内訳。新宿2.57、丸の内・有楽町・日比谷1.22、東京都心部12.55、合計35.02 km²)。東京23区(2022年度)の 3D Tiles + MVT の ZIP は約 **8.8 GB**。
出典: https://www.geospatial.jp/ckan/dataset/plateau-tokyo23ku-2022

[事実] **動的地物は一切含まれない**。提供地物はすべて静的地物であり、車両・歩行者・信号現示・営業状態などは存在しない。PLATEAU は人流等の動的情報を「3D都市モデルに重ね合わせる外部データ」として位置づけている。
出典: https://www.mlit.go.jp/plateau/learning/tpc01-2/

[事実] **変換ツールは揃っている**: PLATEAU SDK for Unity(MIT、CityGMLインポート・テクスチャ結合の自動化・地物フィルタ・C# API、**エクスポートは FBX/OBJ/glTF**)、PLATEAU SDK for Unreal(UE5向け、Blueprint API)、PLATEAU GIS Converter(Rust、CityGML → 3D Tiles/MVT/glTF/OBJ/Minecraft 等)。3D Tiles のストリーミング配信APIもあり、`{area}-{type}-{lod}[-interior][-{texture}]-{year}` 形式で LOD とテクスチャ有無を指定できる。
出典: https://github.com/Project-PLATEAU/PLATEAU-SDK-for-Unity , https://project-plateau.github.io/PLATEAU-SDK-for-Unity/manual/ExportCityModels.html , https://github.com/Project-PLATEAU/PLATEAU-GIS-Converter , https://docs.plateauview.mlit.go.jp/datasets/3d-tiles/

[未発見] PLATEAU LOD2 の公式なポリゴン数/三角形数統計。渋谷区 CityGML の ZIP 実サイズ。

> **[推測] 決定的な含意**: PLATEAU LOD2 からレンダリングした画像に写るのは「**窓もドアもない、航空写真テクスチャを貼った箱の集合**」であり、**人も車も看板の点灯も商品棚もない**。動的なものは全部こちら側で用意しなければならない。つまり:
>
> **レンダリング画像をVLMに食わせると、「世界の状態」ではなく「我々が何をシーンに置いたか」を測ることになる。** VLMが読み取れる情報の大半は、エンジンが既に真値として持っているもの(誰がどこにいるか)か、そもそも存在しないもの(窓の様子、店の中)のどちらかになる。**パターン台帳ゲートを通す門前条件が書きにくい。**

### 4.2 渋谷は「テクスチャ量が最悪クラス」であることが測定済み

[事実] 国交省 技術調査レポート No.62 の性能検証。**環境**: Intel Xeon W-2123 @3.60GHz / RAM 32.0GB / Windows 10 Pro(GPU型番の記載なし=条件不明)。汎用WebブラウザでCesiumにより 3D Tiles を表示。

**表3-11(抜粋)**。「ー」= **メモリ上限を超過して 3D Tiles の描画に失敗**:

| # | 最大タイル数 | 再アトラス化 | FMEアトラス化 | 都市 | FPS最小 | メモリ(MB) |
|---|---|---|---|---|---|---|
| 1 | 10,000 | 有 | 無 | **渋谷** | **ー(失敗)** | ー |
| 2 | 30,000 | 有 | 無 | **渋谷** | **ー(失敗)** | ー |
| 3 | 50,000 | 有 | 無 | 渋谷 | 3 | 1,320.3 |
| 4–6 | 10/30/50,000 | 有 | 有 | 渋谷 | 1 | 1,058–1,227 |
| **7–9** | 10/30/50,000 | 無 | 無 | **渋谷** | **ー(全て失敗)** | ー |
| 10–12 | 10/30/50,000 | 無 | 有 | 渋谷 | 3 | 1,079–1,727 |
| 13–24 | — | — | — | 加賀 | 15–48 | 85–580 |

**12パターン中5パターンが描画失敗**(#1, #2, #7, #8, #9)。原文の結論: 「加賀市のような範囲当たりのテクスチャ量が多くない場合には、再アトラス化による効果がみられるが、画像をまとめることでメモリ使用量は増加するため、**渋谷のような範囲当たりのテクスチャの量が多い場合には、画像のまとめ方での描画性能の向上では限度がみられた**」。

[事実] **再アトラス化の副作用**(表3-9、渋谷4メッシュ): 画像ファイル数 4,264 → 1,811(約58%削減)だが、**総容量は 501MB → 967MB(約2倍に増加)**。理由は「1枚の画像に異なる大きさや形状の画像を詰め込むことで余白が生じる」。処理時間は約25分。

出典: https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_tech_doc_0062_ver01.pdf

**[推測]**: 都市規模シーンの制約は「三角形数」ではなく**テクスチャの総バイト数と、それをVRAMに常駐させられるか**である。渋谷は日本のPLATEAUデータの中でも単位面積あたりテクスチャ量が最悪クラスで、ブラウザ+Cesiumという比較的軽い経路ですら上限に当たっている。

### 4.3 バッチレンダリングの公表値(条件つき)

| システム | 数値 | 条件 | 出典 |
|---|---|---|---|
| **Madrona batch renderer** | **>100,000 FPS**(単純)/ **>10,000 FPS**(HSSD) | 「per GPU」のみ、**GPU型番なし**。**128×128** | https://madrona-engine.github.io/renderer.html |
| **Madrona MJX**(第三者測定) | 403k FPS(64×64)/ 19k FPS(512×512) | **RTX 4090**、CartPoleBalance(**幾何は極めて単純**) | https://arxiv.org/html/2601.01288v1 |
| **PyBatchRender**(2026-01) | **1.6M FPS**(64×64)/ **61k FPS**(512×512)、Madrona MJX比 3.97×/3.2× | **RTX 4090**、CartPoleBalance | https://arxiv.org/html/2601.01288v1 |
| **bps3D 原論文** | >19,000 f/s(1GPU)/ 72,000 f/s(8GPU) | GPU型番・解像度・シーン**すべて条件不明** | https://arxiv.org/abs/2103.07013 |
| **Habitat-Sim** | 単一スレッド数千FPS / 単一GPU multi-process >10,000 FPS、**640×480 で 311.7 FPS** | GPU型番なし。室内スケール | https://github.com/facebookresearch/habitat-sim |
| **Habitat 3.0** | 単一環境 **140–250 FPS** / 16並列環境1GPU で **1,100–2,290 FPS** | **V100 ×1**、HSSD室内(68–846 m²) | https://arxiv.org/pdf/2310.13724 (付録F.1 表4) |
| **ManiSkill3 / SAPIEN** | 最大30,000+ FPS、ReplicaCAD部屋規模でレンダ込み2,000+ FPS(RoboCasaは約25 FPS)、VRAM **3.5 GB**(Isaac Labは14.1 GB) | **RTX 4090**、**128×128**、128並列 | https://arxiv.org/html/2410.00425v2 |
| **Genesis BatchRenderer** | 数値なし。推奨「**256×256 で 128–256 環境**」 | Linux+CUDA必須。バックエンドはMadrona | https://genesis-world.readthedocs.io/en/v0.3.14/user_guide/getting_started/batch_renderer.html |

**[重要な留保]** 上表の高FPS値は**すべて室内スケールないし極端に単純な幾何**が前提。**都市規模シーンでのバッチレンダリング公表FPSは未発見**。

[事実] Madrona 本体の制約: 研究用コードベース(API破壊的変更あり)、**GPUバックエンドは Linux 必須**(Windows の CUDA は必要な unified memory 機能を欠く)、**使用する archetype を事前に全宣言する必要があり動的な追加/削除は非対応**、Volta以降のNVIDIA GPU必須。
出典: https://github.com/shacklettbp/madrona

### 4.4 Isaac Sim / Isaac Lab

[事実] **Isaac Sim 4.5.0 公式ベンチマーク**(リファレンス機: i9-14900k + DDR5 32GB):
- 合成データ生成(SDG)、**RTX 4080、720pカメラ、オブジェクト500個**: シンプル(RGBDのみ)**81.3 メガピクセル/秒**、コンプレックス(全アノテータ)**3.7 メガピクセル/秒**
- Full Warehouse シーン(RTX 4080, Windows): ロード88.7秒、**113.6 FPS**
- 起動: シェーダキャッシュ有 async 5.73秒、無 33.7秒 / 非async 278秒

出典: https://docs.isaacsim.omniverse.nvidia.com/4.5.0/reference_material/benchmarks.html

**[推測]** 81.3 MP/s を画像枚数換算すると **720pなら約88枚/秒、128×128相当なら約4,960枚/秒**(単純按分)。全アノテータ付きだと720pで約4枚/秒。

[事実] **Isaac Lab の推奨**: 「RTX 4090 相当のGPUでは、シーン内に **512カメラ**で動かすことを推奨」。タイルドカメラの効率の源は同期が**1回のデバイス同期で済む**こと。
出典: https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/sensors/camera.html

[事実] **Isaac Lab 論文**(L40 48GB / RTX Pro 6000 96GB / GeForce 5090 32GB で測定): **USD-Camera は RGB/depth とも48並列カメラを超えるとメモリ律速**。Tiled-Camera と RayCaster は**数千環境までスケール**。
出典: https://arxiv.org/html/2511.04831v1

[事実] **マルチGPUスケーリング**: 2GPU×2カメラ(720p)で72–89%高速化、4GPU×4カメラで213–233%、4GPU×8カメラで271–281%。**GPU物理は1GPUしか使わない**。テクスチャストリーミング予算は既定で **GPUメモリ容量の60%**。
出典: https://docs.isaacsim.omniverse.nvidia.com/6.0.0/reference_material/sim_performance_optimization_handbook.html

### 4.5 Unreal / Pixel Streaming — 案(b)(c)には不適

[事実] Azure リファレンスアーキテクチャ: 「性能最適化(30fps・720p)を適用すれば、**1台のGPU VMに 2〜4本のアプリを載せられる可能性がある**」。H.264 ハードウェアエンコーダはコンシューマGPUで**エンコードセッション上限が8**、Pixel Streaming 2 では9本目以降は自動でソフトウェアエンコーダに切り替わる。
出典: https://learn.microsoft.com/en-us/gaming/azure/reference-architectures/unreal-pixel-streaming-in-azure , https://dev.epicgames.com/documentation/en-us/unreal-engine/hosting-and-networking-guide-for-pixel-streaming-in-unreal-engine

**[推測]** Pixel Streaming は設計目標が「人間の視聴者に低遅延で映像を届ける」ことで、**1GPU = 2〜4エージェント**。40万体には10万GPUオーダーが必要で桁が3〜4つ合わない。NVENCエンコードが完全に無駄。

[事実] **Unreal City Sample**(The Matrix Awakens と同一アセット): Big City は「およそ **4km × 4km(約16 km²)**」「数万オブジェクトから成る**数十億ポリゴン**」。必要環境: **RTX-2080 / Radeon 6000 以上、VRAM 8GB以上、12コア 3.4GHz CPU、システムRAM 64GB、SSD**。フレームタイム例: ネイティブ4Kで **57.50 ms**、TSRで1080pからアップスケールすると **33.37 ms**(GPU型番の記載なし)。
出典: https://dev.epicgames.com/documentation/en-us/unreal-engine/city-sample-project-unreal-engine-demonstration

[事実・要注意] Cesium公式コミュニティフォーラムの**一ユーザーの測定**(公式ベンチマークではない): UE5.3 + Cesium for Unreal v2.8.0 + **RTX 2070** で東京を表示 — Japan 3D Building Data(PLATEAU由来)**20–29 fps(不安定)**、Google Photorealistic 3D Tiles 36–38 fps(安定)、港区LOD2 36–45 fps。
出典: https://community.cesium.com/t/i-want-to-improve-the-performance-of-japan-3d-building-data-in-vr/35241

[事実] **Blender EEVEE は headless(ディスプレイなし)システムを現時点でサポートしていない**。
出典: https://developer.blender.org/T58921

[事実] **nvdiffrast** は「より低レベルなライブラリ」で、**カメラモデル・ライティング/マテリアル・シェーディングモデル・加速構造を一切含まない**。公式ドキュメントにスループット数値の掲載なし。
出典: https://nvlabs.github.io/nvdiffrast/

[未発見] Unreal ヘッドレス(`-RenderOffScreen`)の1画像あたりコストの公表実測値。Omniverse の都市規模デジタルツインの VRAM/FPS 公表値。Open3D / PyRender の公表スループット。

### 4.6 最も近い先行事例: Virtual Community(2025年8月)— この節で最も重要

[事実] 実都市の3DデータでLLM/ロボットエージェント社会をシミュレートした直近の事例。
- **世界の作り方**: **Google 3D Tiles + OpenStreetMap**。指定範囲の3D Tilesを取得、ECEF→ENU座標変換。OSMから道路・地面アノテーションと建物メタデータ。テクスチャは Google StreetView と Mapillary のストリートビューを再投影
- **シーン規模**: 屋外シーンは **800m × 800m(64万 m²)**。世界17カ国35都市の35シーン。1シーンあたり**平均53棟の建物、約133のアメニティ物体、357の自然物**
- **エンジン**: **Genesis** 物理エンジン
- **性能(決定的)**: **NVIDIA A100 ×1、シングルプロセス**。**RGB設定ではアバター観測を 1 Hz で供給しつつ物理を 100 FPS で回す。Depth設定では depth を物理ステップ毎(100 Hz)にレンダリング**
- **LLMエージェントへの入力**: 各ステップで「RGB-D画像 + カメラ行列 + セグメンテーション + 現在姿勢 + タスク情報」
- タスク成績(Human Following Rate)はベースライン平均 42–60%

出典: https://arxiv.org/abs/2508.14893 , https://arxiv.org/html/2508.14893v1

**[推測] この設計が示す実務的な答え**: 800m四方・建物53棟という「渋谷の交差点周辺だけ」程度の規模ですら、A100 1枚で **RGB は 1 Hz が実用上限**とされている。そして **RGB と depth の周波数を100倍違えている**のは、著者らが RGB のコストを depth の100倍と見積もっていることの強い状況証拠。40万エージェントに毎ステップRGBを配る構成は、この事例から2〜3桁の飛躍が必要。

### 4.7 40万体への外挿 [すべて推測]

コスト感の桁を掴むための外挿(実測ではない):

| 方式 | 1ステップあたりのGPU時間(40万視点) | 根拠 |
|---|---|---|
| Madrona級バッチ、128×128 RGB、**室内スケール幾何** | 約 **40 GPU秒** | 400,000 ÷ 10,000 FPS |
| 同、**都市規模幾何**(テクスチャ常駐が効く) | **不明。1桁以上悪化しうる** | HSSD(部屋)と渋谷(街区)の差。実測データなし |
| Isaac Sim SDG、720p RGBD、RTX 4080 | 約 **4,500 GPU秒(1.25時間)** | 81.3 MP/s、400,000×0.9216MP |
| Unreal Pixel Streaming | **10万GPU 必要** | 1 GPU VM あたり 2–4 ストリーム |
| **低解像度セグメンテーション/IDバッファのみ** | **数 GPU秒オーダー** | ピクセル按分 + シェーディング省略 |
| **レイキャストのみ**(1体64レイ = 2,560万レイ) | **1 GPU秒未満と推定** | BVHの一般的スループットからの推定。絶対値の出典は未発見 |

**[推測] そしてVLM推論が全部を飲み込む**。40万枚を毎ステップVLMに通す構成は、極めて楽観的に「1GPUあたり1,000画像/秒」と置いても **400 GPU秒/ステップ** で、Madrona級レンダリングの10倍。**レンダリングを最適化しても解決しない。** 案(b)(c) が成立するとしたら「全エージェントが毎ステップ画像を見る」ではなく「**ごく一部のエージェントが、ごく稀に画像を見る**」構成に限られる。Virtual Community が RGB を 1 Hz、depth を 100 Hz に分けたのは、まさにこの非対称性への回答と読める。

### 4.8 画像を作らずに幾何情報だけ得る(1): レイキャスト・IDバッファ

[事実] **Isaac Lab RayCaster**: 「各レイについて経路上に線を辿り、指定メッシュとの**最初の衝突位置**を返す」。レイは**跳ね返らず、マテリアルや不透明度の影響を受けない**。NVIDIA Warp で直接計算。戻り値は `[N, B, 3]`。**重大な制約: 「デフォルトのUSDファイル仕様から変化しない静的メッシュにのみ対応」= 動的物体は検出できない**(将来解除予定と明記)。
出典: https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/sensors/ray_caster.html

[事実] **RayCaster vs TiledCamera**: 「**低解像度では RayCasterCamera がより効率的、高解像度では Tiled-Camera が優位**」。スケーリング特性: アセット数増加に対し**劣線形**の性能劣化、解像度が上がるほどレイ/秒が強く増加、**メッシュ複雑度 20k–200k 面の範囲では影響は最小**。「**メッシュ簡略化よりレイ密度のチューニングの方が、精度と効率のバランスを取る有効なレバー**」。
出典: https://arxiv.org/html/2511.04831v1

[事実] **Genesis BatchRenderer は RGB / depth / セグメンテーション / 法線マップをレンダリング可能で、セグメンテーションは entity / link / geometry の各レベル**で出力できる。
出典: https://genesis-world.readthedocs.io/en/v0.3.14/user_guide/getting_started/batch_renderer.html

**[推測] 案(b)(c) の最も現実的な着地点**: 「そのエージェントから何が見えるか」の**オブジェクトIDリスト**が欲しいだけなら、RGBを作らず**低解像度(32×32 や 64×64)のセグメンテーション/IDバッファだけを描く**のが最短。シェーディング・テクスチャフェッチ・アンチエイリアス・エンコードが全部不要になるので、**§4.2 の最大のボトルネックであるテクスチャVRAM常駐が消える**(ジオメトリとIDだけ載せればよい)。しかも§4.1の問題(PLATEAUのテクスチャが低品質)も同時に消える——**IDバッファはテクスチャ品質と無関係**だから。

[事実] **GPUオクルージョンカリング**(GPU Gems 2 Ch.6, NVIDIA): 都市ウォークスルー事例で「本章のアルゴリズムは、**視錐台カリング単独と比べて約4倍**、階層的 stop-and-wait 法と比べて 2.6倍の高速化」。シーン記述は定性的で三角形数は非公開。
出典: https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-6-hardware-occlusion-queries-made-useful

[未発見] Warp / RayCaster の rays/sec 絶対値。オクルージョンクエリのマイクロ秒単位コスト。

### 4.9 画像を作らずに幾何情報だけ得る(2): 可視性グラフの事前計算【本答申の推奨経路】

[事実] **GPU加速VGA**(City-Scale Visibility Graph Analysis via GPU-Accelerated HyperBall)のアブストラクト実測値:
- 「our tool achieves a **239x end-to-end speedup at 42,705 cells** and scales to **236,000 cells (4.8 billion edges) in 137 seconds** -- problem sizes far beyond depthmapX's practical limit」
- delta圧縮CSR + LEB128 varint で **約4倍圧縮**、RAMを超えるグラフをmmap可能に
- HyperBall(HyperLogLogベースの確率的距離推定)で BFS 計算量を O(N|E|) → O(D|E|2^p) に
- 精度: 「At p=10, Visual Mean Depth achieves **Pearson r=0.999 with 1.7% median relative error** across 20 matched configurations」

出典: https://arxiv.org/abs/2604.08374 (PDF: https://arxiv.org/pdf/2604.08374)

[事実] **理論的背景(空間統語論 / Space Syntax)**:
- isovist = ある地点から見えるすべての点の集合(Benedikt)。Turner et al. が Visibility Graph Analysis (VGA) として定式化: 研究領域に格子点を置き、建物内部の点を除去し、半径r以内で見通しが通る2点を辺で結ぶ
- 「There is evidence from the field of Space Syntax and natural movement theories that attributes **pedestrian spatial cognition to visibility**.」
- Turner & Penn (2002) は「見える距離の確率に導かれたランダムウォーク」でエージェントベース歩行者モデルを構成
- 「The **angle is more critical than the depth** for the emergence of path patterns, indicating that our path choices are affected by the **width of our field of view**, rather than the distance.」

出典: https://doi.org/10.1068/B2684 (Turner et al. 2001, *From Isovists to Visibility Graphs*) , https://journals.sagepub.com/doi/10.1177/23998083251324065 , https://doi.org/10.1177/23998083231184884

[事実] **3D isovist への拡張**も存在する(A 3D Isovist World Model — Revealing a City's Unseen Geometry and Its Emergent Cross-City Signature): https://arxiv.org/pdf/2606.03609 。ただしPDF本文からスケール・計算コストの具体数値は抽出できず [未発見]。

[事実] **可視性 → 商業の実証的裏付け**(パターン照合の門前条件になる):
- 「Stores located in segments with **high visibility of through traffic** benefit from increased retail success」— 小売のミクロ立地における可視性の役割: https://doi.org/10.1177/23998083221138570
- 小売店の可視性解析(書店でのパイロット研究): https://journals.sagepub.com/doi/10.1068/b130016p
- POI と視覚的知覚による都市計画・設計: https://journals.sagepub.com/doi/10.1177/23998083231191338

#### 渋谷への当てはめ [推測]

**渋谷の LOD2 整備面積 1.39 km²(=1,390,000 m²)を 2.5m グリッドで割ると約 222,000 セル。** これは上記論文の最大構成(236,000セル / 137秒)と**ほぼ同じスケール**。つまり:

> **渋谷全域の「どの地点からどの地点が見えるか」を、GPU で 2〜3分の一度きりの前計算で得られる。**

静的建物に対する可視性は毎ステップ計算する必要がない。動的物体(人・車)だけを毎ステップの短距離レイキャストで扱えばよい(§4.8)。**これが §4.7 の外挿表で「1 GPU秒未満」と見積もった経路**であり、レンダリング(40 GPU秒〜1.25時間)とVLM(400 GPU秒)より 2〜4 桁安い。

**[推測] 最重要の設計上の主張**: 渋谷の社会シムで「視覚」が効くパターンの大半——**店の視認性 → 立ち寄り、見通し → 経路選択、看板の到達、初訪問者の迷い**——は、**isovist/VGAという「レンダリングもVLMも不要な決定論的幾何計算」で照合可能**である。生画像が本当に必要なのは「見た目の印象(綺麗/怖い/賑わい)が行動を変える」パターンだけで、それは§2.9のSAGAI式に**場所ごとの静的スコアとして事前計算**できる。

### 4.10 §4 の結論(PLATEAU 留保の解消)

答申前半で「要検証」としていた留保は、**事実として確認された**:

| 留保 | 検証結果 |
|---|---|
| 屋内なし | **確認**(LOD4.1 は地下街のみ)[事実] |
| 窓・ドアなし | **確認**(開口部は LOD3 から。渋谷は LOD2.0/2.2 まで)[事実] |
| 人物・車両なし | **確認**(動的地物は一切含まれない)[事実] |
| 看板の可読テクスチャなし | **確認**(航空写真由来で「解像度が低い・影が含まれる・視認性に課題」と国交省自身が明記)[事実] |
| 都市規模のVRAM負荷 | **確認**(渋谷は12パターン中5パターンで描画失敗)[事実] |

→ **したがって「PLATEAU LOD2 から作った画像をVLMに渡す」構成は、世界の状態ではなくシーン構築の中身を測る。** 案(b)を採るなら、(i) 動的オブジェクト(人・車・看板・商品)を全部自前で用意し、(ii) テクスチャVRAM問題を解き、(iii) その上で VLM が読み取る情報がエンジンの真値より価値があることを示す、という3段の証明が必要になる。**§0.2 の推奨(オフライン言語化 + 現実整合検証に限定)は、この3段を回避する設計**である。

---

## 5. 課題5: 「五感」の残り(聴覚・嗅覚・内受容感覚)

### 5.0 この節の一行結論

**4つの独立した分野(embodied AI音響 / 都市騒音マップ / ロボット嗅覚 / ゲーム産業)が同一の設計パターンに収束していた: 「オフラインで場(field)をベイクし、実行時はエージェントが O(1) でサンプリングするだけ」。** そして 40万体規模では前3者すらオーバーキルで、**ゲームAI流の「半径 + 音源イベント」+ 事前ベイク済み実測騒音グリッド**が唯一現実的。

### 5.1 聴覚 — 研究側は「高忠実度」、産業側は「半径1個」

#### 事前計算 vs 実行時計算の決定的な差(実測値)

[事実] **SoundSpaces**(ECCV 2020): Matterport3D / Replica に対する幾何音響シミュレーションによる**事前計算済みRIR(室内インパルス応答)データセット**。直接音・初期反射・残響・HRTF による空間音響。事前計算は「0.5m グリッド上の全音源・受音点ペアについて、固定の100環境」に対して実施。**事前計算データそのものは TB オーダー**。
出典: https://arxiv.org/abs/1912.11474

[事実] **SoundSpaces 2.0**(NeurIPS 2022): 実行時にジオメトリから音響をレンダリング(Habitat-sim 内の**双方向パストレーシング**、Intel Embree でレイトレース加速)。**実測FPS(Table 2)**:

| モード | 1スレッド | 5スレッド |
|---|---|---|
| high-quality | **0.9 ± 0.0 FPS** | 4.0 ± 0.1 FPS |
| high-speed | 7.7 ± 0.2 FPS | **33.5 ± 0.4 FPS** |

high-speed は high-quality に対し1スレッドで8倍・5スレッドで33倍効率改善(精度は RT60 で 9.5% 劣化)。対比として「**TDW は 60 FPS、SoundSpaces(1.0)は 500+ FPS で動作(ボトルネックはI/O)**。ただし簡略化された部屋モデルか、設定不可であることの代償として」。学習コスト参考: ナビゲーション課題で **32 GPU × 46時間**、8000万ステップ。
出典: https://arxiv.org/abs/2206.08312 , https://ar5iv.labs.arxiv.org/html/2206.08312

**[推測] 事前計算 500+ FPS vs 実行時 0.9〜33.5 FPS = 15〜500倍の差**。40万体規模では実行時音響レンダリングは論外。

[事実] **Steam Audio**(Valve 公式): 実行時反射のパラメータがすべて「CPU使用量が増加する代償を伴う」と明記されている(Real Time Rays / Bounces / Duration / Ambisonic Order)。Real Time Max Sources で実行時に反射を計算する音源数に**上限を設ける**設計。Embree 使用で実行時シミュレーションとベイクが4〜6倍高速化。
出典: https://valvesoftware.github.io/steam-audio/doc/unity/settings.html

[事実] **Microsoft Project Acoustics**: 「**静的ライティングと似た哲学: 詳細な物理をオフラインでベイクし、表現力ある設計コントロールを持つ軽量ランタイムを使う**」「CPU集約的なレイトレーシングを必要とせず、オクルージョン・オブストラクション・ポータリング・リバーブを低CPU・低RAMで実行時レンダリング」。3.0 でクラウド並列ベイクにより ~1000プローブのシーンでプリベイク5倍高速化。
出典: https://developer.microsoft.com/en-us/games/articles/2022/08/project-acoustics-30-is-now-available/

[未発見] NVIDIA VRWorks Audio の現行公式ドキュメント上のコスト特性。

#### ゲームAIの聴覚は「半径1個 + 音源イベント」であることの公式確認

[事実] **Unreal Engine AI Perception**: 感覚は Sight / Hearing / Damage / Touch / Team / Prediction の6種。Hearing のパラメータは **Hearing Range**(「AI Perception システムがこの感覚を知覚できる距離」)、LoS Hearing Range、Detection by Affiliation(Enemies/Neutrals/Friendlies フィルタ)、Max Age、Starts Enabled のみ。「The AI Hearing sense can be used to detect sounds generated by a **Report Noise Event**」。**音響伝播・反射・壁の減衰の計算は一切なし。距離パラメータ1個とイベント登録のみ。**
出典: https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine , https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception?application_version=4.27

[事実] **Unity**: 公式のビルトインAI知覚(聴覚)システムは **未発見**。Asset Store のサードパーティ製のみで、その実装も「音を球でモデル化し、中心を音源、中心から離れるほど大きさが減衰する」という半径+減衰の近似。

**[推測]**: 商用ゲームの聴覚は距離しきい値+イベントであり、それで20年以上「それらしい」効果が出ている。v2の聴覚は `hear_radius` 1個 + 音源側が `noise_event(loudness, tag)` を発行、で十分。**expedient タグ**を付け、感度試験で「聴覚半径を±50%振っても集計結果が動かない」ことを示す設計にできる。

#### 都市騒音 — 渋谷では「計算する」必要すらない

[事実] **CNOSSOS-EU**: EU の法定共通騒音評価法(2018/12/31 以降、EU戦略騒音マッピングで義務)。計算コストが公然の課題で「膨大な数の地域グリッドが多大な計算時間を消費し、騒音マップの更新効率を著しく制約する」。CNOSSOS-EU 自体が明示的な近似レバー(車線を1本に集約 / 音源高さの本数を減らす / デジタル地図の空間解像度を下げる)を規定している。
出典: https://publications.jrc.ec.europa.eu/repository/handle/JRC72550

[事実] **NoiseModelling**(Université Gustave Eiffel、GPLv3): CNOSSOS-EU を実装した Java ライブラリ。H2GIS/PostGIS 連携。最も計算量の大きいパスファインディングに R-Tree、反射のイメージソース法の指数爆発を避けるため**受音点ベースのビューコーン戦略**を採用。
出典: https://github.com/Universite-Gustave-Eiffel/NoiseModelling

[事実] **日本の実測データ(渋谷に直接使える)**: 環境省「自動車騒音常時監視」。令和5年度は全国847自治体・延長69,463km の道路、約951万9,200戸を対象に評価。GIS形式で公開(国立環境研究所 環境GIS)。東京都環境局も年度別の自動車交通騒音調査結果を公開。
出典: https://www.env.go.jp/air/car/noise/index.html , https://tenbou.nies.go.jp/gis/explain/traffic/index.html , https://www.kankyo.metro.tokyo.lg.jp/vehicle/noise/result

**[推測] これは大きい**: 渋谷なら**音場を自前で計算する必要がない**。環境省/東京都の実測騒音データを街区メッシュの dB フィールドに焼くだけで、**現実整合アンカー台帳に直接載る実測アンカー**になる(mechanism でも expedient でもなく「実データ」)。

[未発見] LLM社会シム主要系(Generative Agents / AgentSociety / Concordia / Project Sid)で**聴覚モダリティを明示的に持つもの**。「聞こえた会話/騒音」を扱う先行例は見つからなかった。避難ABMでは「警報音を聞く」が避難開始トリガとして登場するが、音響伝播・可聴性・壁減衰の定量モデルは未発見(バイナリの「鳴った/鳴っていない」扱いが主流と見られる)。

### 5.2 嗅覚 — ロボティクスと都市データには存在、社会シムには存在しない

[事実] **GADEN**(Sensors 2017, DOI: 10.3390/s17071479): 3Dガス拡散シミュレータ。2段構成 —
1. **オフライン**: OpenFOAM による CFD 風速場の事前計算(障害物・流入出を考慮)
2. **実行時**: フィラメント拡散モデル。ガス放出を「パフの列。各パフは n 本のフィラメント、各フィラメントは分子の3D正規分布」としてモデル化

コスト: フィラメントシミュレータは「オフライン実行前提」で各タイムステップのガス濃度3Dマップをファイル記録。再生する Player パッケージは「**基本的に計算負荷なし**」でオンライン動作可能。
出典: https://pmc.ncbi.nlm.nih.gov/articles/PMC5539624/

[事実] 乱流プルーム追跡を深層RLで学習した研究(創発挙動が飛翔昆虫に類似、「生物は現在の風向ではなく局所的なプルーム形状に従う」): https://arxiv.org/abs/2109.12434 。CFDを回さずにプルームの「体験」を統計的に生成する COSMOS: https://arxiv.org/abs/2505.22436

[事実] **Smelly Maps: The Digital Life of Urban Smellscapes**(ICWSM 2015): スメルウォークで嗅覚語彙の辞書を作り、**Flickr/Instagram のタグと位置情報付きツイート**から都市の匂い地図を構築(バルセロナ・ロンドン)。匂い語は10カテゴリに分類され、一部カテゴリ(industry, transport, cleaning)は**政府の大気質指標と相関**。
出典: https://arxiv.org/abs/1505.06851

**[未発見] 社会シミュレーション/ABM での嗅覚の実装例(「飲食店の匂いが客を引く」型)は該当文献ゼロ。** 都市スメルスケープ研究(記述的・GIS的)と ABM 消費者行動研究(嗅覚なし)は**それぞれ独立に存在するが、両者を接続した文献は見つかっていない**。

**[推測]**: これは「先行例がないから避けるべき」ではなく v2 の差別化余地でもある。だが**較正データ(匂いが実際に来店を動かした証拠)が存在しない**ため、**mechanism ではなく expedient としてしか正当化できず、パターン台帳ゲートを通らない可能性が高い**。優先度は最低に置くのが妥当。実装するなら GADEN 型の「オフライン濃度フィールド + 実行時サンプリング」一択(実行時CFDは論外)。

### 5.3 内受容感覚(空腹・疲労・体温)— 最も安く、最も先行例が濃く、最も効果検証がある

#### Humanoid Agents(EMNLP 2023 Demo)— この論点の中核先行例

[事実]
- **needs の定義**: fullness(満腹), fun, health, social, energy の**5種、0〜10スケール**。初期値は中間の5
- **更新則**: 「エージェントが活動に従事した後、その活動が感情を変化させ、いずれかの基本欲求を満たしたかを**エージェント自身が評価**し、該当すれば対応する欲求ステータスを1増やす。そうでなければ、各基本欲求は時間経過とともに一定の確率で1減少する」
- **減衰率**(5時間あたり): fullness −1, health −1, social −4, fun −4, energy −5
- **プロンプトへの投入条件(コスト設計上の要点)**: 「感情が中立でない、または**いずれかの基本欲求が未充足(10点中3以下)である場合にのみ**、内的状態を自然言語にフォーマットし…計画を変更すべきか判断させる」= **常時注入せず、閾値割れ時のみ注入**
- **効果検証(Table 2)**: health を0にすると健康関連活動の時間が **+156%**、energy で **+56%**、fullness で **+35%**。social は **+12%** で効果薄
- **人手評価(Table 1)**: fullness / energy / emotion の分類は **F1 ≥ 0.84**、fun / social / health は F1 0.66〜0.74(過剰予測)
- 規模: 3ワールド(2〜4エージェント)、平日2日を15分刻み(1エージェント42ステップ)。**コスト非開示**

出典: https://arxiv.org/abs/2310.05418 , https://ar5iv.labs.arxiv.org/html/2310.05418

[事実] **AgentSociety**(1万体超): **マズローの欲求階層**を採用。「Needs はエージェントの行動を導く根底的な動機づけ因子として機能し、基本的な生存要求から個人的成長・自己実現といった高次の願望までを含む」。欲求階層は「エージェントの能動的行動、制御不能ないし受動的な外的事象、現在の心理状態」の3要因で継続更新。**Need → Plan → Behavioral Sequence** の連鎖(計画的行動理論)。1日1エージェントあたり平均500インタラクション・計500万インタラクション。トークン/コスト数値は非開示。
出典: https://arxiv.org/html/2502.08691v1

[事実] **Concordia**(Google DeepMind): 「**エージェントの生理状態をモデル化したければ、渇きと空腹、健康、ストレスのレベルを記述するコンポーネントを追加する**」。コンポーネントは**通常のコード**(空腹レベルのような具体的変数の追跡)でも LLM 呼び出しでも実装できる。
出典: https://arxiv.org/html/2312.03664v2

[事実] 対照: **Generative Agents には内的身体状態は一切ない**(音・匂い・空腹その他の非視覚モダリティの議論を含まない)。**Project Sid / PIANO** のモジュール10種にも空腹・体力・内的生理状態の明示的モジュールはない。**Voyager** の観測には「health and hunger bars」が含まれる[https://arxiv.org/html/2305.16291]。

#### 理論的背景

[事実] **Homeostatic RL**(eLife 2014, Keramati & Gutkin): 内部状態に基づく報酬関数を RL の枠組みで定義し、**動因低減理論と強化学習を接続**。「行動の結果が内部状態に与える影響を予測でき、その予測された影響が**内部状態とその理想値との差を縮める**と信じられるとき、その行動を報酬的と感じる」。
出典: https://elifesciences.org/articles/04811 / 連続時間版: https://arxiv.org/abs/2109.06580

[事実] **Life-inspired Interoceptive AI**: 内受容 =「内部環境を一定範囲内に保つための監視プロセス」。要件は (1) **内部状態変数を外部環境変数から分離(factorize)**すること、(2) 生体の内部安定維持を反映する数学的性質を採ること。
出典: https://arxiv.org/abs/2309.05999 / レビュー: https://arxiv.org/abs/2604.24527

#### 都市スケールで「身体状態→行動選択」が検証された唯一の系: 熱・日陰(渋谷に直結)

[事実] **Behavioural thermal regulation explains pedestrian path choices in hot urban environments**(Scientific Reports 12, 2022): 熱帯都市での被験者実験 + 計算手法。**日陰を歩いた距離は日向を歩いた距離に対して係数 0.86 で割り引かれる**(=日陰なら14%長く歩いてもよいと感じる)。建物の影は樹木の影より強い効果。
出典: https://doi.org/10.1038/s41598-022-06383-5

[事実] **Seeking shade: an agent-based model to study shadow-focused pedestrian movement (Berlin, 2026)**: **NetLogo で約25,000体**、Lidar 由来の影マップ + 詳細な街路データ(歩道・自転車道・車寄せ・路上駐車・中央分離帯)。日陰を優先するコスト関数のみ。結果: 最も晴れた日に**日陰歩行が +12%、総所要時間の増加はわずか +2%**。
出典: https://www.sciencedirect.com/science/article/pii/S2590198226000485

**[推測] これが「五感」で最も費用対効果が高い**: 内受容は LLM 呼び出しを増やさず、効果検証があり(+35〜156%)、かつ**日陰係数 0.86 は現実整合アンカーとして台帳に載せられる実数値**で、渋谷の夏の回遊行動に mechanism として直接使える。憲法3「身体感覚はプロンプトへ」の最も安い実装形。

### 5.4 マルチモーダル観測のシリアライズ — 「全モダリティを1本の自然言語文字列に落とす」が事実上の標準

[事実] **Concordia** が最も明快: **Game Master (GM)** が世界状態から各エージェントの観測を生成する。
- 「**観測・行動・イベント文はすべて英語の文字列である**」
- 「**GM がそのプレイヤーはその事象を観測しなかったと判断した場合、観測は一切発行されない**」
- = **「何が知覚されるか」の判定をGMに集約**し、感覚モダリティ別のパイプラインを持たない

出典: https://arxiv.org/html/2312.03664v2

[事実] **PIANO の Cognitive Controller ボトルネック**(Project Sid): 「Cognitive Controller は Agent State 全体の情報を**ボトルネックを通して**統合する。このボトルネックは CC に提示される情報量を削減し、2つの目的を果たす: **CC が関連情報に推論を集中できるようにすること**、および**システム設計者に情報フローの明示的な制御を与えること**」。CC の決定は下流へブロードキャストされ、発話モジュールとの一貫性を高める。
出典: https://arxiv.org/html/2411.00114v1

[事実] **観測マスキング ≒ LLM要約**: *The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for Agent Context Management* — **単純な観測マスキングがLLM要約と同等に効率的**。追加のLLM呼び出しをかけずにトークンを削れる。
出典: https://arxiv.org/abs/2508.21433

[未発見] **感覚モダリティ別の saliency フィルタ**(「この匂いは弱いので観測に含めない」等)を明示的に設計した社会シムは見つからなかった。トークン削減側の研究は多いが、それは文脈管理であって感覚顕著性ではない。

**[推測] v2への含意**: 「5感を別チャネルで持つ」設計の先行例はゼロ。**Concordia 型に倣い、エンジン側(GM相当)が全モダリティを1本の自然言語観測に統合し、閾値を割った感覚だけを文字列に混ぜる**のが最安。§0.2 の Observation スキーマは内部表現であり、LLMへの提示は1本の文字列に畳む。

### 5.5 ゲーム産業の「オブジェクト側が『私はこう知覚される』を宣言する」設計 — 20年以上の標準

[事実] **Unreal Engine — AI Perception Stimuli Source Component**: アクタが「**指定した感覚に対する刺激源(stimuli source)として自分自身を自動登録する**」。プロパティは **Auto Register as Source**、**Register as Source for Senses**(感覚の配列)。この分離設計により、知覚する側の関与なしに任意のアクタが刺激になれる(ピックアップ等の非AIアクタも被知覚対象になれる)。
出典: https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine

[事実] **Smart Object の学術的原典** — Kallmann & Thalmann, *Modeling Objects for Interaction Tasks*(Computer Animation and Simulation '98, DOI: 10.1007/978-3-7091-6375-7_6): 「オブジェクトの記述の中に、**どうやってそれと相互作用するかを記述するために必要な全情報を含める**」。可動部・機能命令・相互作用位置を特徴モデリングで指定。「Smart Objects は、ユーザがどう相互作用できるかを**自分自身で知っている**オブジェクトである」。
出典: https://link.springer.com/chapter/10.1007/978-3-7091-6375-7_6 / 続編 ACM VRST '99: DOI 10.1145/323663.323683

[事実] **F.E.A.R.**(Jeff Orkin, GDC 2006): 有限状態機械はわずか**3状態 — Goto / Animate / UseSmartObject**。行動列も経路も A* で計画(GOAP)。「巨大なFSMを作る代わりに、AIにゴールと**環境をどう操作するかのモデル**を与え、達成方法はAIに考えさせる」。**UseSmartObject が3つの基本状態の1つ**であることが、この設計の一般性を示す最も強い証拠。
出典: https://gdcvault.com/play/1013282/Three-States-and-a-Plan

[事実] **Halo 2**(GDC 2005, Damian Isla): 逆に限界の証言。知覚情報の保管庫 "props" は「**単なるオブジェクト参照のフラットなリスト**であり、空間関係(is-next-to / is-on-top-of)も構造関係の情報も持たない」と著者自身が認めている。ただし「アクタは壁越しに見えるべきではない」ことは保証し、**AIの信念状態が世界の実状態から乖離できる**ようにしている(それがAIを騙す・驚かせる余地を生む)。
出典: https://www.gamedeveloper.com/programming/gdc-2005-proceeding-handling-complexity-in-the-i-halo-2-i-ai

[事実・要注意] **The Sims の "advertisement" 機構**(オブジェクトが「私を使えば energy +10」を放送し、Sim が自分の現在のモチーブレベルで重み付けしてスコアリング)については、**Maxis 公式の一次出典は未発見**。確認できたのは二次資料のみ。学術的裏付けは Kallmann & Thalmann と Game AI Pro のユーティリティ理論章(David "Rez" Graham, *An Introduction to Utility Theory*, Game AI Pro Ch.9, http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter09_An_Introduction_to_Utility_Theory.pdf )で代替するのが妥当。

**[推測] v2への含意(重要)**: 「生の感覚データではなくオブジェクト側が宣言する」は**業界標準であり、v2の既存ドクトリンと完全に整合**する:
- 「状態と集約はエンジン、意思決定と発話だけLLM」← 知覚もエンジン側
- 「世界の変化はエージェント行動の結果として実装」(棚が減る=店員の補充行動)← これを**知覚側にも対称に適用**すると「この棚は『補充が必要に見える』と宣言する」になる
- Generative Agents のオブジェクト状態自然言語化とも同型

### 5.6 感覚別の実装推奨(コスト順)

| 感覚 | 最安の近似 | 実行時コスト/体 | 先行例の強度 | mechanism/expedient |
|---|---|---|---|---|
| **体温・熱** | 事前ベイクした日陰/WBGTグリッドをサンプル、距離コストに係数 **0.86** | O(1) グリッド参照 | **強**(被験者実験検証あり・DOI付き) | **mechanism 候補** |
| **空腹・疲労等** | 0〜10スカラー数本、減衰は定数、**閾値割れ時のみ**プロンプト注入 | **LLM呼び出し増ゼロ** | **強**(効果検証 +35〜156%) | **mechanism 候補** |
| **騒音** | 環境省/東京都の実測騒音を街区メッシュにベイク、`hear_radius` 1個 | O(1) | 中(ゲーム標準 + 実測データあり) | expedient(要感度試験)/ 実測アンカー |
| **会話の傍受** | 半径 + Concordia型GM判定で観測文字列に混ぜる | O(近傍数) | **弱**(LLM社会シムに先行例なし) | expedient |
| **嗅覚** | GADEN型 オフライン濃度フィールド + サンプリング | O(1) | **なし**(社会シムでは未発見) | expedient のみ |

**[推測] 実装順の推奨: 内受容(体温含む) → 騒音 → 会話傍受 → 嗅覚。** そして **この順序の先頭2つは、視覚(a)/(b)/(c)のどれよりも安く、どれよりも効果検証がある**。R3で視覚の議論に時間を使う前に、内受容を知覚契約に入れる決定を先に取るべき、というのが本節の実務的な提案。

---

## 6. 課題6: (a)/(b)/(c) の比較表

### 6.1 各案の定義(本答申での明確化)

3案を、調査で見えた実装形に合わせて**5案に分解**する:

- **(a) 構造化された視覚記述テキスト**: エンジンが可視集合を決定論的に計算し(半径だけでなく **isovist/VGA を前計算**)、構造化レコード → 自然言語テンプレートで言語化。**LLM呼び出しも描画もゼロ**。
- **(a0) IDバッファ/レイキャスト併用**: 動的物体(人・車)の可視判定だけ、低解像度(32×32〜64×64)のセグメンテーション/IDバッファか短距離レイキャストで毎ステップ取る。**RGBを一切作らない**ので、PLATEAUのテクスチャ品質問題もVRAM常駐問題も消える。
- **(a+) (a)(a0) + オフラインVLM言語化**(**本答申の推奨**): 場所ごとに1回だけレンダリング+VLM記述を作り台帳化。ランタイムはテキスト参照のみ。
- **(b) VLMスナップショット理解**: 毎ステップ(または昇格時)にエージェント視点をレンダリングし、VLMに直接投入。
- **(c) VLA直結**: 視覚から行動を直接生成。

### 6.2 比較表

| 観点 | (a) 構造化記述 | (a0) IDバッファ/レイキャスト | (a+) +オフラインVLM言語化【推奨】 | (b) VLMスナップショット | (c) VLA直結 |
|---|---|---|---|---|---|
| **得られる忠実度** | 静的可視性・距離・方向は**真値**。見た目の質感はゼロ | + 動的物体の遮蔽まで**真値**(「人だかりの向こうは見えない」) | + 場所ごとの「雰囲気」記述。社会的判断への寄与は VV 条件相当(AgentViSS 49.60)[事実] | 動的な見た目を毎回取れる。ただしDV条件はVVに18.39pt劣る[事実]。かつ**PLATEAUには人も車も窓もない**[事実] | 知覚と行動の一貫性。ただし行動空間がモータ制御に限定 |
| **失うもの** | 動的遮蔽。「そこにあるが記述されていない」ものは存在しない(=憲法5と整合、だが記述設計が全て) | 色・材質・表情 | ランタイムの動的変化は静的記述に反映されない | プロンプトキャッシュ、モデル選択の自由度(VLM必須)、**レンダラ品質・シーン構築品質への全面依存** | テキストLLMの推論能力・説明可能性・v2の行動空間との整合。学習データも存在しない |
| **コスト(40万体・1ステップ)** | **ゼロ**(可視性は一度きりの前計算: 236k cells / **137秒**[事実]。渋谷2.5mグリッド≒22万セル[推測]) | **[推測] 1 GPU秒未満〜数GPU秒** | 場所数×1回のVLM。渋谷の地点を1万点とすれば SAGAI 実測 1,300枚/時[事実]で**8時間程度の一度きり** | **[推測]** Madrona級・室内幾何なら40 GPU秒/ステップだが**都市幾何の実測は未発見**。Isaac Sim 720p なら **4,500 GPU秒**。VLM推論が **400 GPU秒** 上乗せ | **[推測]** 成立しない。OpenVLA 7Bで166ms/6Hz[事実]、CrowdVLAが「数千体で compute-bound」と明記[事実] |
| **どのパターン照合に効くか** | 店の視認性→立ち寄り、見通し→経路選択、看板到達、初訪問者の迷い(可視性→小売成功の実証あり[事実]) | + 混雑による視界遮蔽→迂回、人だかりへの引き寄せ | + 「印象(綺麗/怖い/賑わい)→滞留・回避」。SAGAI式で実SV画像と同一ルーブリック採点でき、**現実整合アンカーの測定装置になる** | 動的な視覚事象。ただしVLMは歩行者計数に失敗する[事実]ので**エンジンの真値のほうが正確** | 局所的な歩行回避のみ。それ以外は該当なし |
| **門前条件を書けるか** | **書ける**。「可視性が歩行者の立ち寄り率に効く」は空間統語論の実証パターン | **書ける**。「見通しの悪さが経路変更を生む」 | **書ける**。「街路の印象スコアが滞留時間に効く」+ 実SV画像との乖離測定 | **部分的**。「行列の視認が並ぶ判断を変える」は書けるが、行列の有無はエンジンが知っている(=視覚不要) | **書けない**(現時点)。「VLAでしか照合できない渋谷の現実パターン」を1行で書けない |
| **mechanism / expedient** | mechanism(幾何は現実と同じ機構) | mechanism | mechanism(場所の見えは実際に静的)+ 記述の粒度は expedient | **expedient になりやすい**(レンダラ品質とシーン構築が結果を駆動するリスク) | — |
| **憲法整合** | 5「知覚されない細部は作らない」の**実装形そのもの** | 同左 | 同左 + 3「心と世界は相互に見える」を強化 | **5と衝突しうる**(描画のためにLOD2にない細部を作り込む圧力が生じる) | 3を満たすが「意思決定と発話だけLLM」の背骨と衝突 |
| **性能予算への影響** | step時間・RSSともに増分ほぼゼロ(前計算テーブルのバイト予算のみ) | 逐次ループ1本の新設(宣言必須)。GPU物理と共存 | 同左 + 台帳のバイト予算 | **逐次ループの新設が必要**(描画→VLM→LLM)+ **テクスチャVRAM常駐**(渋谷は Cesium で描画失敗の実績[事実]) | 同左 + 学習パイプライン |
| **可逆性** | 高い | 高い | 高い(台帳を捨てればよい) | 中(パイプライン投資が発生) | 低い |

### 6.3 段階的導入の提案(R3知覚契約で決めるべきこと)

**Phase 0(視覚より先に決めるべきこと)**: **内受容感覚を知覚契約に入れる**。0〜10のスカラー数本 + **閾値割れ時のみプロンプト注入**(Humanoid Agents 方式)。LLM呼び出しは1回も増えない。熱・日陰は事前ベイクグリッド + 係数0.86。**(a)(b)(c) のどれよりも安く、効果検証がある**(§5.3)。

**Phase A(即時・低リスク)**: 知覚契約のスキーマを「モダリティ汎用のスティミュラスレコード」として定義する。
```
Observation := {
  visual:  [{entity_id, distance, bearing, angular_size, occlusion, salience}]
  auditory:[{source_id, distance, loudness, kind, occlusion}]
  olfactory: [...]   # スキーマだけ切っておく(実装は後)
  interoceptive: {hunger, fatigue, thermal, crowding_stress}   # ← Phase 0 で先に埋まる
  place_descriptor: <台帳から引く静的記述>  # (a+)の差し込み口
}
# LLMへの提示は Concordia 型に1本の自然言語文字列へ畳む。
# 閾値を割ったフィールドだけを文字列に混ぜる(常時全部は入れない)。
```
- 「見える」の定義を**半径から isovist/VGA に格上げ**する(先行研究の半径1個[事実: Generative Agents]からの最大の差分)。渋谷全域の前計算は GPU で 2〜3分[推測]
- **オブジェクト側が「私はこう知覚される」を自己申告する**設計(UE AI Perception 型 / Smart Object 型)[事実]。v2の「棚が減る=店員の補充行動」原則の知覚側への対称適用

**Phase B(安価な動的可視性)**: (a0) を追加。低解像度IDバッファか短距離レイキャストで動的物体の遮蔽を取る。**RGBを作らないのでPLATEAUのテクスチャ問題とVRAM問題を完全に回避する**。性能予算に逐次ループ1本を宣言。

**Phase C(検証つき・(b)の投資判断の根拠)**: SAGAI式の現実整合測定を1地点セットで試す。実ストリートビュー画像とシム描画画像を同一ルーブリックでVLM採点し、乖離を測る。**§4.1/§4.2 の事実に照らせば乖離は大きく出る可能性が高い**(人も車も窓もない箱の集合を撮ることになる)。乖離が大きければ「シム画像はシーン構築の中身を測っているだけ」が実証され、**(b) を根拠を持って棄却できる**。これは棄却のための測定として価値がある。

**Phase D(条件つき)**: Phase C が合格した場合のみ、場所ごとの静的VLM記述を台帳化(a+)。

**Phase E(将来)**: 認知LOD T2 昇格時の on-demand 視覚を「ツール」として提供(GraphPad 型の「問い合わせ可能な知覚」)。門前条件が書けた場面のみ。

### 6.4 ユーザー判断を仰ぐべき分岐

1. **Phase 0 を先に取るか**: 視覚の議論より先に内受容感覚を決める、という順序変更の可否。**本答申の最も強い実務提案**。
2. **看板・広告テキストの扱い**: OCR的タスクは視覚トークン数が支配的になり[事実: α/β反転]、スケーリング則の結論が逆転する。かつ **PLATEAU LOD2 の航空写真テクスチャでは看板は読めない**[事実]ので、扱うなら別データソース(実ストリートビュー / OSM の店舗属性)が要る。渋谷の屋外広告を扱うか否かで設計が変わる。
3. **嗅覚を入れるか**: 先行例が未発見・較正データもない。「自然界を模した仕組み志向」に照らせば入れる価値はあるが、パターン台帳ゲートを通せるかは要判断。
4. **可視性計算の解像度とバイト予算**: 渋谷の格子点数をいくつに取るか(2.5mグリッドで約22万セル・137秒[推測+事実])。前計算テーブルのサイズがバイト予算に直結。
5. **Phase C の測定を実施するか**(コスト: [推測] 実SV画像取得 + VLM推論で数時間規模)。**(b)を採らない決定をするためにも、この測定はやる価値がある**。
6. **騒音を実測データで入れるか**: 環境省/東京都の自動車騒音常時監視データを街区メッシュに焼く[事実: データは公開済み]。これは較正データつきの数少ない感覚。

---

## 7. 未発見・不確実性の明示

| 項目 | 状態 |
|---|---|
| **40万体規模でVLA/VLMを使った社会シミュレーションの先行例** | **未発見**。最大は SimWorld の 20–24体[事実]、CrowdVLA の1シーン9体[事実]、Virtual Community の800m四方[事実] |
| **嗅覚を実装した社会シム/ABM**(「飲食店の匂いが客を引く」型) | **未発見**(該当文献ゼロ)。都市スメルスケープ研究と ABM 消費者行動研究は独立に存在するが接続されていない |
| **LLM社会シムにおける聴覚モダリティの明示実装** | **未発見**(Generative Agents / AgentSociety / Concordia / Project Sid いずれにもない) |
| **感覚モダリティ別の saliency フィルタ**を設計した社会シム | **未発見** |
| **都市規模シーンでのバッチレンダリング公表FPS** | **未発見**(公表値は全て室内スケールか極端に単純な幾何) |
| Madrona SIGGRAPH Asia 2024 原論文本文 | ACM DL が **HTTP 403** で取得不可。「RTX4090/H100 で 300K/30K FPS」「HSSD 平均700万三角形」は**採用せず** |
| Warp / Isaac Lab RayCaster の rays/sec 絶対値 | **未発見**(論文は相対傾向のみ) |
| Unreal ヘッドレス(`-RenderOffScreen`)の1画像あたりコスト | **未発見** |
| Omniverse の都市規模シーンの VRAM/FPS 公表実測値 | **未発見**(技術要件ページは最低要件のみ) |
| Open3D / PyRender の公表スループット | **未発見** |
| GPUオクルージョンクエリのマイクロ秒単位コスト | **未発見** |
| PLATEAU LOD2 の公式ポリゴン数/三角形数統計、渋谷区 CityGML の ZIP 実サイズ | **未発見** |
| NVIDIA VRWorks Audio の現行公式コスト特性 | **未発見**(公式ドキュメントに到達できず) |
| The Sims の advertisement 機構の一次(Maxis公式)出典 | **未発見**(二次資料のみ)。Kallmann & Thalmann と Game AI Pro のユーティリティ理論章で代替 |
| 避難ABMにおける音響伝播・可聴性の定量モデル | **未発見**(バイナリの「鳴った/鳴っていない」扱いが主流と見られる) |
| SIMA 2 の推論レイテンシ・モデルサイズ・同時実行数 | 論文に記載なし[事実: 「does not specify」] |
| Project Sid の API コスト・トークン使用量 | 論文に記載なし[事実] |
| CrowdVLA の推論画像解像度・実行時レイテンシ | 本文になし(補足資料に委譲)[事実] |
| AgentSociety / Humanoid Agents のトークン・コスト数値 | いずれも非開示[事実] |
| 3D isovist world model (2606.03609) のスケール・計算コスト | PDF本文から抽出できず [未発見] |
| Spatial-DISE の具体的な精度数値と人間ベースライン | アブストラクトには数値なし。本文未確認 [未発見] |
| Game AI Pro の PDF 本文(Splinter Cell Blacklist の知覚章等) | URL存在確認のみ、本文未取得 |

**方法論上の注意**:
1. 本答申の数値のうち §3.1 のトークン表、§3.2 の増分率、§3.4 の TFLOPs/レイテンシ試算、§4.7 の外挿表、§4.9 の渋谷グリッド数は、いずれも**出典の公式・実測値から本答申が計算した [推測]** である。実測ではない。実装前に count_tokens 相当の実測とマイクロベンチで検証すべき。
2. §4 の表で「GPU型番の記載なし=条件不明」と注記した数値(Madrona, bps3D, Habitat-Sim, VGA論文, City Sample のフレームタイム)は、**条件が揃わないので相互比較してはいけない**。
3. Cesium コミュニティフォーラムの東京表示FPS(20–45 fps)は**一ユーザーの測定**であり Cesium 公式ベンチマークではない。

---

## 8. 出典一覧

### VLA / VLM
- Vision-Language-Action Models for Robotics: A Review Towards Real-World Applications — https://arxiv.org/html/2510.07077
- A Survey on Efficient Vision-Language-Action Models — https://arxiv.org/html/2510.24795v1
- 10 Open Challenges Steering the Future of Vision-Language-Action Models — https://arxiv.org/html/2511.05936
- GR00T N1: An Open Foundation Model for Generalist Humanoid Robots — https://arxiv.org/html/2503.14734v1
- Vision-Language-Action (VLA) Models: Concepts, Progress, Applications and Challenges — https://arxiv.org/abs/2505.04769
- RADAR: Benchmarking VLA Generalization — https://arxiv.org/html/2602.10980v1
- ViewSpatial-Bench — https://arxiv.org/html/2505.21500v2
- Spatial-DISE — https://arxiv.org/abs/2510.13394
- Inference Optimal VLMs Need Fewer Visual Tokens and More Parameters — https://arxiv.org/html/2411.03312v2
- Qwen2.5-VL Technical Report — https://arxiv.org/html/2502.13923v1
- Anthropic Vision docs(視覚トークン公式) — https://platform.claude.com/docs/en/build-with-claude/vision

### シミュレーション内エージェント
- CrowdVLA: Embodied Vision-Language-Action Agents for Context-Aware Crowd Simulation — https://arxiv.org/html/2604.05525v1
- SIMA 2: A Generalist Embodied Agent for Virtual Worlds — https://arxiv.org/html/2512.04797v1
- Scaling Instructable Agents Across Many Simulated Worlds (SIMA) — https://arxiv.org/abs/2404.10179
- SIMA blog — https://deepmind.google/blog/sima-generalist-ai-agent-for-3d-virtual-environments/
- SimWorld — https://arxiv.org/html/2512.01078
- Emergent Crowds Dynamics from Language-Driven Multi-Agent Interactions — https://arxiv.org/html/2508.15047

### LLM社会シム
- Generative Agents: Interactive Simulacra of Human Behavior — https://ar5iv.labs.arxiv.org/html/2304.03442
- Voyager: An Open-Ended Embodied Agent with Large Language Models — https://arxiv.org/html/2305.16291
- Project Sid: Many-agent simulations toward AI civilization — https://arxiv.org/html/2411.00114v1
- OASIS: Open Agent Social Interaction Simulations with One Million Agents — https://arxiv.org/html/2411.11581v3
- AgentSociety — https://arxiv.org/abs/2502.08691
- GenWorld: Empirically Grounded Urban Simulation Infrastructure — https://arxiv.org/abs/2606.27650
- Affordable Generative Agents — https://arxiv.org/pdf/2402.02053
- Large Population Models (AgentTorch) — https://arxiv.org/html/2507.09901v1

### 視覚の有無のアブレーション
- EmbodiedBench — https://arxiv.org/html/2502.09560v2
- StarDojo — https://arxiv.org/html/2507.07445v1
- Can Agents Read the Room? (AgentViSS) — https://arxiv.org/html/2606.15152

### シーングラフ / 能動的知覚
- 3DGraphLLM — https://arxiv.org/abs/2412.18450
- GraphEQA — https://arxiv.org/html/2412.14480v2
- GraphPad — https://arxiv.org/html/2506.01174v1
- 3D Scene Graphs: Open Challenges and Future Directions — https://arxiv.org/html/2606.19383
- Active-O3 — https://arxiv.org/html/2505.21457v1
- Q-Zoom — https://arxiv.org/html/2604.06912

### PLATEAU / 都市3Dデータ
- PLATEAU LOD定義(建築物) — https://www.mlit.go.jp/plateau/learning/tpc03-3/
- PLATEAU 3D都市モデルの概要(動的情報の位置づけ) — https://www.mlit.go.jp/plateau/learning/tpc01-2/
- 建築物モデル LOD3 仕様(開口部の追加) — https://www.mlit.go.jp/plateaudocument/toc4/toc4_02/toc4_02_01/toc4_02_01_04/_da554178-d7ce-cbf3-bd20-7834e9359422/
- **PLATEAU Technical Report No.62(渋谷の描画性能実測・テクスチャ実測)** — https://www.mlit.go.jp/plateau/file/libraries/doc/plateau_tech_doc_0062_ver01.pdf
- 渋谷区(2023年度)データセット — https://www.geospatial.jp/ckan/dataset/plateau-13113-shibuya-ku-2023
- 東京23区(2022年度)データセット — https://www.geospatial.jp/ckan/dataset/plateau-tokyo23ku-2022
- PLATEAU SDK for Unity — https://github.com/Project-PLATEAU/PLATEAU-SDK-for-Unity / エクスポート仕様 https://project-plateau.github.io/PLATEAU-SDK-for-Unity/manual/ExportCityModels.html
- PLATEAU SDK for Unreal — https://github.com/Project-PLATEAU/PLATEAU-SDK-for-Unreal
- PLATEAU GIS Converter — https://github.com/Project-PLATEAU/PLATEAU-GIS-Converter
- PLATEAU 3D Tiles 配信仕様 — https://docs.plateauview.mlit.go.jp/datasets/3d-tiles/
- Cesium ion Japan 3D Buildings — https://cesium.com/platform/cesium-ion/content/japan-3d-buildings/

### レンダリング / 可視性
- Madrona: High-Throughput Batch Rendering for Embodied AI — https://madrona-engine.github.io/renderer.html
- Madrona Engine(制約・要件) — https://github.com/shacklettbp/madrona
- PyBatchRender(RTX 4090 実測、Madrona MJX との比較) — https://arxiv.org/html/2601.01288v1
- Large Batch Simulation for DRL (bps3D) — https://arxiv.org/abs/2103.07013
- Habitat: A Platform for Embodied AI Research — https://arxiv.org/abs/1904.01201v2
- Habitat-Sim(README のベンチ値) — https://github.com/facebookresearch/habitat-sim
- Habitat 2.0 — https://ar5iv.labs.arxiv.org/html/2106.14405
- Habitat 3.0(V100 実測、付録F.1) — https://arxiv.org/pdf/2310.13724
- ManiSkill3 — https://arxiv.org/html/2410.00425v2
- Genesis BatchRenderer — https://genesis-world.readthedocs.io/en/v0.3.14/user_guide/getting_started/batch_renderer.html
- GPUDrive — https://arxiv.org/html/2408.01584v1
- **Virtual Community(実都市3D + LLMエージェント、RGB 1Hz / depth 100Hz)** — https://arxiv.org/abs/2508.14893 , https://arxiv.org/html/2508.14893v1
- Isaac Sim 4.5.0 ベンチマーク — https://docs.isaacsim.omniverse.nvidia.com/4.5.0/reference_material/benchmarks.html
- Isaac Sim 性能最適化ハンドブック(マルチGPU) — https://docs.isaacsim.omniverse.nvidia.com/6.0.0/reference_material/sim_performance_optimization_handbook.html
- Isaac Lab Camera(512カメラ推奨) — https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/sensors/camera.html
- Isaac Lab RayCaster(静的メッシュのみの制約) — https://isaac-sim.github.io/IsaacLab/main/source/overview/core-concepts/sensors/ray_caster.html
- Isaac Lab 論文(Tiled vs RayCaster スケーリング) — https://arxiv.org/html/2511.04831v1
- NVIDIA Warp CHANGELOG(BVH 改善) — https://github.com/NVIDIA/warp/blob/main/CHANGELOG.md
- nvdiffrast(低レベルライブラリであることの明記) — https://nvlabs.github.io/nvdiffrast/
- GPU Gems 2 Ch.6 Hardware Occlusion Queries Made Useful — https://developer.nvidia.com/gpugems/gpugems2/part-i-geometric-complexity/chapter-6-hardware-occlusion-queries-made-useful
- Unreal City Sample(4km×4km・必要環境) — https://dev.epicgames.com/documentation/en-us/unreal-engine/city-sample-project-unreal-engine-demonstration
- Unreal Pixel Streaming ホスティング(エンコーダ上限8) — https://dev.epicgames.com/documentation/en-us/unreal-engine/hosting-and-networking-guide-for-pixel-streaming-in-unreal-engine
- Azure Unreal Pixel Streaming リファレンスアーキテクチャ(1GPU VM = 2–4ストリーム) — https://learn.microsoft.com/en-us/gaming/azure/reference-architectures/unreal-pixel-streaming-in-azure
- Cesium コミュニティ(東京表示の一ユーザー測定) — https://community.cesium.com/t/i-want-to-improve-the-performance-of-japan-3d-building-data-in-vr/35241
- Blender EEVEE headless 非対応 — https://developer.blender.org/T58921
- **City-Scale Visibility Graph Analysis via GPU-Accelerated HyperBall** — https://arxiv.org/abs/2604.08374
- Turner et al., From Isovists to Visibility Graphs — https://doi.org/10.1068/B2684
- Simulation to forecast crime patterns: space syntax vs ABM — https://journals.sagepub.com/doi/10.1177/23998083251324065
- Simple agents – complex emergent path systems — https://doi.org/10.1177/23998083231184884
- A 3D Isovist World Model — https://arxiv.org/pdf/2606.03609

### 都市 × VLM / 現実整合
- SAGAI: Streetscape Analysis with Generative AI — https://arxiv.org/html/2504.16538v1
- Examining the Commitments and Difficulties Inherent in Multimodal Foundation Models for Street View Imagery — https://arxiv.org/html/2408.12821v1
- Revolutionizing Urban Safety Perception Assessments — https://arxiv.org/html/2407.19719v1
- Interpretable Multimodal Framework for Human-Centered Street Assessment (MSEF) — https://arxiv.org/abs/2506.05087
- Benchmarks for VLMs in Urban Perception Should Be Reliability-Aware — https://arxiv.org/html/2606.00871
- Exploring the role of accessibility in shaping retail location (space syntax) — https://doi.org/10.1177/23998083221138570
- Developing Visibility Analysis for a Retail Store — https://journals.sagepub.com/doi/10.1068/b130016p
- Urban planning and design with points of interest and visual perception — https://journals.sagepub.com/doi/10.1177/23998083231191338

### 音響 / 騒音
- SoundSpaces: Audio-Visual Navigation in 3D Environments — https://arxiv.org/abs/1912.11474
- SoundSpaces 2.0(FPS実測 Table 2) — https://arxiv.org/abs/2206.08312 , https://ar5iv.labs.arxiv.org/html/2206.08312
- ThreeDWorld (TDW) — https://arxiv.org/abs/2007.04954
- Steam Audio 設定(実行時反射のCPUコスト) — https://valvesoftware.github.io/steam-audio/doc/unity/settings.html
- Project Acoustics 3.0(オフラインベイク哲学) — https://developer.microsoft.com/en-us/games/articles/2022/08/project-acoustics-30-is-now-available/
- CNOSSOS-EU (JRC) — https://publications.jrc.ec.europa.eu/repository/handle/JRC72550
- NoiseModelling — https://github.com/Universite-Gustave-Eiffel/NoiseModelling
- **環境省 自動車騒音常時監視** — https://www.env.go.jp/air/car/noise/index.html
- 国立環境研究所 環境GIS(自動車交通騒音) — https://tenbou.nies.go.jp/gis/explain/traffic/index.html
- 東京都環境局 自動車交通騒音調査結果 — https://www.kankyo.metro.tokyo.lg.jp/vehicle/noise/result

### 嗅覚
- GADEN: 3Dガス拡散シミュレータ — https://pmc.ncbi.nlm.nih.gov/articles/PMC5539624/
- 乱流プルーム追跡の創発挙動 — https://arxiv.org/abs/2109.12434
- COSMOS(データ駆動の嗅覚シミュレータ) — https://arxiv.org/abs/2505.22436
- Smelly Maps: The Digital Life of Urban Smellscapes — https://arxiv.org/abs/1505.06851

### 内受容感覚 / 身体状態
- **Humanoid Agents**(5needs・閾値注入・効果検証) — https://arxiv.org/abs/2310.05418 , https://ar5iv.labs.arxiv.org/html/2310.05418
- Concordia(生理状態コンポーネント・観測は全て文字列) — https://arxiv.org/abs/2312.03664 , https://arxiv.org/html/2312.03664v2
- Homeostatic reinforcement learning (eLife 2014) — https://elifesciences.org/articles/04811
- Continuous Homeostatic RL — https://arxiv.org/abs/2109.06580
- Life-inspired Interoceptive AI — https://arxiv.org/abs/2309.05999
- Interoceptive machine framework(レビュー) — https://arxiv.org/abs/2604.24527
- **Behavioural thermal regulation explains pedestrian path choices**(日陰係数0.86) — https://doi.org/10.1038/s41598-022-06383-5
- Seeking shade: shadow-focused pedestrian ABM (Berlin, 25,000体) — https://www.sciencedirect.com/science/article/pii/S2590198226000485
- The Complexity Trap: Simple Observation Masking ≒ LLM Summarization — https://arxiv.org/abs/2508.21433

### ゲームAI知覚 / Smart Object
- Unreal Engine AI Perception(Stimuli Source Component 含む) — https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine
- Unreal Engine 4.27 AI Perception — https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception?application_version=4.27
- UAISense_Hearing — https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/AIModule/Perception/UAISense_Hearing
- Kallmann & Thalmann, Modeling Objects for Interaction Tasks(Smart Object 原典) — https://link.springer.com/chapter/10.1007/978-3-7091-6375-7_6
- F.E.A.R. — Three States and a Plan (GDC 2006, Jeff Orkin) — https://gdcvault.com/play/1013282/Three-States-and-a-Plan
- Halo 2 AI (GDC 2005, Damian Isla) — https://www.gamedeveloper.com/programming/gdc-2005-proceeding-handling-complexity-in-the-i-halo-2-i-ai
- Game AI Pro — An Introduction to Utility Theory — http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter09_An_Introduction_to_Utility_Theory.pdf
- Empowering NPC Dialogue with Environmental Context Using LLMs and Panoramic Images — https://arxiv.org/html/2604.19192v1

### ハードウェア
- NVIDIA RTX A5000 データシート — https://www.nvidia.com/content/dam/en-zz/Solutions/products/workstations/nvidia-rtx-a5000-datasheet.pdf
