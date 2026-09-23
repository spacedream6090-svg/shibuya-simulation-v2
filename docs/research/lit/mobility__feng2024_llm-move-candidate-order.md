# Feng, Lyu, Chen & Ong 2024 — Where to Move Next: Zero-shot Generalization of LLMs for Next POI Recommendation(LLM-Move)

- リンク: <https://arxiv.org/abs/2404.01855> / 本文 <https://arxiv.org/html/2404.01855v2> | 分野: 人間移動科学 #3 / 自然言語処理・機械学習 #27 | 重要度: **P1**
- **一次確認**: **実読(サブ・2026-09-17・arXiv HTML v2)・親未確認**。v1 2024-04-02 / v2 2024-04-22・cs.IR。査読会議の記載は abs に無い。
- **なぜ引くか**: **「候補を作って LLM に選ばせる」設計の細部が、1 本の論文の中に全部書いてある唯一の先行**(候補の作り方・並べ方・見せる属性・順序 ablation・規則ベースとの比較)。R-37 の親案 H の直接の型紙であり、同時に**順序バイアスの最強の反証データ**でもある。

## 主張(claim)

零ショットの LLM は、候補 POI 集合と地理距離と逐次遷移を与えれば、学習済みの次 POI 推薦器を上回る。ただし **(i) LLM は地理文脈を正確に理解できない**(座標から距離を計算させると失敗する)**(ii) 候補の提示順に強く依存する**。

## 機構(mechanism)

1. **候補集合**(逐語): 「the candidate set comprises the ground truth POI and **100 randomly sampled POIs**」= 推薦評価の慣行(He ほか NCF)。POI は `⟨Id, Cat, Lat, Lon⟩`。
2. **距離はエンジンが前計算して入力にする**(逐語): 「For each POI in the candidate set, we calculate its **geographical distance**」「from the user's current position (indicated by the last check-in)」/ 脚注 1 で ChatGPT に座標から距離を出させる試みが「cannot obtain accurate results」で失敗したと明記し、「Hence, we **calculate the distances and utilize them as input**.」
3. **並べ方は距離昇順**(逐語): 「As an empirical choice, we adopt the **Dist-asc** ordering to present POI candidates in our work.」
4. 出力は上位 10 件のランキング。

## 数値(表番号まで)

**Table II(主表・Acc@1 / Acc@5 / Acc@10 / MRR)**

| 手法 | NYC Acc@1 / @5 / @10 / MRR | TKY Acc@1 / @5 / @10 / MRR |
|---|---|---|
| Popu(人気順) | .0500 / .2200 / .2750 / .1168 | .2300 / .4000 / .5050 / .3148 |
| **Dist(最近傍)** | **.3702** / .5700 / .6195 / .4452 | **.2700** / .4850 / .5450 / .3682 |
| CZSR | .1600 / .2400 / .2800 / .1903 | .1300 / .1700 / .1800 / .1461 |
| LLMRank | .0400 / .1150 / .1750 / .0738 | .0100 / .0850 / .1600 / .0469 |
| ListRank | .1100 / .1700 / .2050 / .1347 | .1250 / .1500 / .1750 / .1357 |
| LLMMob | .3600 / .5450 / .6050 / .4384 | .3350 / .4800 / .5150 / .3873 |
| LLMMob(+Geo) | .3850 / .5850 / .6550 / .4703 | .3200 / .5500 / .6100 / .4091 |
| **LLMmove(本手法)** | **.5200** / .6100 / .6650 / .5585 | **.4200** / .5800 / .6250 / .4847 |

→ **最近傍という 1 行の規則(.3702 / .2700)が、先行の LLM 零ショット推薦(LLMRank .04 / ListRank .11 / CZSR .16)を全部上回る。** 候補+距離+選好を全部見せた LLM だけがその規則を超える。

**Table III(距離を消す ablation・NYC)**: 距離なしで .4800 / .5750 / .6250 / .5201。著者(逐語)「**LLMmove-Geo exhibits the lowest performance, underscoring the essential role of geographical distance**」。

**Table IV(順序の ablation・NYC・Acc@1 / @5 / @10 / MRR)**

| 並べ方 | Acc@1 | Acc@5 | Acc@10 | MRR |
|---|---|---|---|---|
| **Dist 昇順(採用)** | **.5200** | .6100 | .6650 | .5585 |
| **Dist 降順** | **.2000** | .3000 | .3250 | .2398 |
| 無作為 | .3250 | .4500 | .5150 | .3854 |
| Freq 昇順 | .3600 | .4450 | .4950 | .4060 |
| Freq 降順 | .4400 | .5400 | .6400 | .4900 |

→ **並べ替えだけで Acc@1 が .52 → .20(2.6 倍)動く。** 著者(逐語)「the **order of the candidate set significantly affects** the recommendation performance」。著者の説明は「the LLM's limited capability to handle a large number of candidates」。

- モデル: **gpt-3.5-turbo のみ**。
- 抄録の 2 つの自己申告(逐語): 「LLMs **cannot accurately comprehend geographical context information**」「**sensitive to the order of presentation of candidate POIs**」。

## 効く箇所(seam)

- **R-37 §5-1「並べ方」**: 体ごとの順序撹拌を**対照ではなく必須の機構**にする根拠。repo 内の先例は `engine/commit.py:702-710` の会話相手の blake3 撹拌(v1 C-8 の ID 順バイアス対策)。
- **R-37 §5-2「見せる情報」**: **距離は数値でなくエンジンが計算した語で渡す**。座標を渡して LLM に計算させない。
- **A2/A3 腕の設計**(R-37 §4-3)。

## 「結論でなく機構として」の入れ方

- **借りる**: (1) 距離をエンジンが前計算して渡す形 (2) 候補の並びが結果を動かすので並びを設計変数として宣言する形 (3) 「最近傍だけの規則」を**必ず対照に置く**形。
- **借りない**: Acc@1 .52 という値そのもの(**予測タスクであり、正解が候補集合に必ず入っている**。v2 には正解が無い)。

## コスト/スケール含意

呼数は 1 候補集合 1 呼。候補 101 件をプロンプトに載せるので入力は長い。**v2 の k=4 とは 25 倍の差**があり、著者の「大量の候補を扱えない」という説明は **v2 が k を小さく保つ根拠**になる。

## 批判・限界

1. **予測タスク**(正解が候補に必ず入っている・履歴がある)。生成/シミュレーションではない。
2. 候補が**無作為 100 件**=現実の到達可能性ではない。
3. **gpt-3.5-turbo 1 モデルのみ**。**8B 級での値は無い**(= v2 の A2 腕が最初の測定になる)。
4. Table IV は NYC だけ。TKY の順序 ablation は未取得(空欄)。

## 関連

[[mobility__santos2026_unconstrained-poi]] ・ [[mobility__li2026_trajgenagent-candidates]] ・ [[nlp__zheng2023_selection-bias]] ・ 答申 `../v2-destination-choice-llm-research.md` §1-2・§3-1
