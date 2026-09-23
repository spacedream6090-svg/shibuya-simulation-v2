# 世界過程 行5 価格形成 — LLM店主の値付けの実証(再リサーチ答申・正典化)

<!-- hdr:v1 -->
- **分野**: 小売科学・商業立地論 #17 / 行動経済学・マーケティング科学 #16 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 36 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(Fable・2026-09-08)**: サブ(Opus 5・子サブなし・リポ書込なし・ハーネスがファイル書込を遮断=テキスト返答を親が保存)の最重要5件を親が原典で確認した。✔=一致。
> - ✔ **Fish, Gonczarowski & Shorrer, "Algorithmic Collusion by Large Language Models"(arXiv 2404.00806 v6・2026-08-31・PDF 83p親抽出)**: プロンプト雛形は "My chosen price: <just the number, nothing else>"=**絶対価格を数値で書かせる**。脚注18 "The price ceiling is reported as the number 2.34 · pM, where the number 2.34 was drawn from Unif[1.5, 2.5]"(1回抽選=サブが疑った内部矛盾は無し)・本文 "text designed to deter the LLM from pricing above a certain ceiling"。Online Appendix B: GPT-4 0613・**温度1**・"our agents use string parsing to extract the price"・"If the LLM fails to produce output in the correct format, the query is retried up to 10 times. In case of 10 consecutive failures, the experimental run is stopped. Such stopping only occurred for monopoly experiments (see Appendix C) using Clau[de]…"。市場履歴は "rounded to the second decimal digit"。
> - ✔ **Higo & Saita (2007) BOJ "Price-setting in Japan: Evidence from CPI Micro Data"(PDF p.37の図を親が座標復元)**: Average Frequency of Price Changes (CY1999-2003, %/month) = **Total 21.4 / Goods 31.1 / Services 4.5 / Public services 3.9 / General services 4.7**(サブの割当は正しい)。一般サービス内訳: **Eating out 5.0**・Domestic duties 2.6・Medical care & welfare 5.8・Education 6.2・Reading & recreation 6.0。公共サービス内訳: Domestic duties 8.8・Medical 1.8・Transportation & communication 0.3・Education 5.5・Reading 1.4。脚注13 "the average frequency of price changes for food product is 29.9% while its standard deviation is 19.5%"。
> - ✔ **金融庁『業種別支援の着眼点』2023(令和5)年3月「4 飲食業」(PDF 11p親抽出)**: 「FL比率＝FLコスト(FOOD:材料費+LABOR:人件費)÷売上高」「60％が適正値の一つの目安」・図「FLコスト:60％/その他経費:30％/営業利益:10％」・「営業利益ベースで売上比10％程度の確保は目指したい」・「原価率20％・30％・35％という目安を押さえる」・図ラベル「ドル箱商材 20%(ビール)/平均的飲食業 30%(ラーメン)/高級・こだわり 35%」「30％弱〜30％強に収めたい」・「中小飲食業の場合『原価≒材料費』と考えて捉える場合が多く…様々なメニューの組み合わせで粗利益を確保」。**訂正**: 作成主体はサブ記載の「日本能率協会」ではなく**公益財団法人 日本生産性本部**(令和4年度 金融庁委託調査)。
> - ✔ **EconAgent(arXiv 2310.10436v3)**: "P ← P(1+φP), φP ~ sign(φ̄)U(0, αP|φ̄|)"・αP=0.10・LLM出力は "'work' (a value between 0 and 1 with intervals of 0.02…) and 'consumption' (…)" をJSONで。
> - **未取得(空欄)**: Ueda (2024, Japanese Economic Review, DOI 10.1007/s42973-024-00161-w)本文(Springerは認証リダイレクト・CARF F570はタイムアウト)=抄録(Semantic Scholar経由)のみ: "The average frequency of price changes approximates 20% on a monthly basis"・外食の改定頻度上昇(2022-23)・店舗間価格分散の数値=**未取得**。Jia & Yuan 2024・Struski et al. 2026・Keppo et al. 2026・Lou & Sun 2024(AI 0.45)は要約経由/サブ実読=親未確認。日本政策金融公庫の原価率(36.9%等)は二次情報のみ=不採用。
> - 適用先: 世界過程設計書 行5 追補(提案H-1〜H-5)。

> 作成: 2026-09-08 / 実行=Opus 5 リサーチサブ(約20分)。

## 要約(5行)
1. Fish et al.(v6・GPT-5.2まで頑健性確認)は絶対価格を数値で書かせ、価格上限テキスト(2.34·p^M)をプロンプトに入れている=絶対価格出力の暴走を著者側が実装で抑えた痕跡。温度1・文字列パース・最大10回再試行。
2. LLMの絶対価格出力は市場均衡に収束しないという反証系が2本(Jia & Yuan 2024/Struski et al. 2026: 価格分散が人間3.5に対しLLM 11.7-28.1・要約経由)。共謀と非収束は矛盾せず「絶対価格を書かせると分布が暴れる」方向。
3. 「比率で答えさせる」直接実証は見つからず(空欄)。EconAgentは価格を方程式で更新しLLMは[0,1]・0.02刻みの傾向を出す(統制比較ではない)。
4. 「月次≈20%」はHigo–Saita(Total 21.4%/月・親確認)とUeda 2024抄録で裏取り。ただし**財31.1%対サービス4.5%で桁が違い、外食は5.0%/月**(親確認)=飲食のCalvo頻度20%は約4倍速すぎる。
5. 原価/FLは金融庁委託文書で確定: FL60/その他30/営業利益10、原価率20/30/35(ドル箱/平均/高級)、原価≒材料費でメニュー間に原価率を散らす実務。

## 1. LLMに価格を決めさせた実証(2023-2026)
| 主張 | 出典 | 逐語 | 別 |
|---|---|---|---|
| 寡占でLLM価格エージェントが超競争価格へ | https://arxiv.org/abs/2404.00806 | "LLM-based pricing agents quickly and autonomously reach supracompetitive prices and profits" | 要約経由 |
| 出力=絶対価格・上限テキスト・温度1・再試行10回 | 同PDF v6 | (親検収欄参照) | 親実読 |
| P1/P2の文言差で超競争度が変わる | 同 | P1 "…you should not take actions which undermine profitability." / P2 "…including possibly risky or aggressive options for data-gathering purposes…" | 要約経由 |
| LLMは市場均衡に到達できない | https://arxiv.org/abs/2409.08357 (Jia & Yuan 2024) | "LLMs lacked the capacity to achieve market equilibrium" | 要約経由 |
| ダブルオークションで非収束・価格分散が人間の3-8倍 | https://arxiv.org/html/2609.02580v1 (Struski et al. 2026) | "In none of the three experiments do we observe full convergence to the competitive equilibrium" / α: GPT Small 11.7・GPT Large 15.6・Gemini Large 28.1・Human 3.5 | 要約経由(α定義未確認) |
| 共謀は異質性で減衰(22%→10%→7%)・モデルサイズ非対称は共謀を安定化 | https://arxiv.org/abs/2603.20281 (Keppo et al. 2026) | 「Patience heterogeneity reduced price elevation from 22% to 10% above competitive levels」「Asymmetric data access brought it down to 7%」 | 要約経由 |
| EconAgent: 価格は方程式・αP=0.10・LLMは比率 | https://arxiv.org/html/2310.10436v3 | (親検収欄) | 親確認 |
LLM出力価格の分布統計(桁外れ率・粘着性)を正面から報告した論文は未発見(空欄)。

## 2. 比率・離散選択で縛る設計の実証
- 比率 vs 絶対値の統制比較=空欄(発見できず)。rスカラー化はexpedient登録が必要。
- Lou & Sun (arXiv 2412.06593v2・サブ実読・著者所属はNational Day School Beijing・査読版JCSS未読): GPT-4のAnchoring Index≈0.45(人間0.61)・CoT等の単純緩和は不十分・強いモデルほど出力分散が小さい・数値回答を拒否することがあり "educated guess" を求める運用。

## 3. 価格改定頻度(日本)
- Higo & Saita 2007(親確認): Total 21.4/Goods 31.1/Services 4.5/Public 3.9/General 4.7、**Eating out 5.0 %/月**。都市間ばらつき大(食品29.9%±19.5)。
- Ueda 2024 JER(抄録のみ): 月次約20%・改定頻度は米国より異質・改定サイズと店舗間分散に正の相関・大都市ほど頻度高く分散小・2022-23年に外食の改定頻度が顕著に上昇。

## 4. 価格分散の実測
- Ueda 2024が唯一の有力候補(店舗間分散の指標定義と数値=未取得→E7アンカー登録は保留)。渋谷区単独の店舗間分散は公表値から読めるか未確認。

## 5. 原価・FLコスト
- 金融庁『業種別支援の着眼点』飲食業編(親確認): FL60/その他30/営業利益10・原価率20(ドル箱)/30(平均)/35(高級・こだわり)・原価≒材料費・メニュー組合せで粗利確保。公庫『小企業の経営指標』は原典未到達=不採用。

## 行5 A案への含意(サブ案・親が設計書追補で採否を整理)
維持: rスカラー化(方向は支持・直接実証なし=expedient・r vs 絶対価格ablation必須)/エンジン側クリアリング+方程式更新/共謀は創発しうるが異質性で減衰。
修正案: (H-1)Calvo改定頻度を業種別に(小売20-30%/月・飲食5-10%/月=Higo–Saita外食5.0%を下限・Ueda(6)で上方修正)/(H-2)内生フロアkをFL基準で解釈(FL60+その他30+利益10が閉じる水準)・業態別3値 k≈2.9(35%)/3.3(30%)/5.0(20%)・店舗レベルでFL制約、メニュー内の原価率分散はr側/(H-3)rのクリップ(例 r∈[0.7,1.5])+拒否・パース失敗時は前期r維持+計数/(H-4)逸脱比例コストの較正に店舗間分散(Ueda・大都市ほど小)=数値未取得のため保留/(H-5)Fish型の「価格上限テキスト」は不要(rスカラーが構造的上限)。

## 参照一覧
親実読: arxiv.org/pdf/2404.00806v6・ier.hit-u.ac.jp/~ifd/doc/IFD-conference/higosaita.pdf・fsa.go.jp/policy/chuukai/0330gyosyubetu_04.pdf・arxiv.org/html/2310.10436v3。要約経由: arxiv 2404.00806(abs/html)・2409.08357・2609.02580v1・2603.20281・boj.or.jp wp07e20・api.semanticscholar.org(Ueda)。サブ実読: arxiv.org/pdf/2412.06593。未取得: carf.e.u-tokyo.ac.jp F570(タイムアウト)・link.springer.com s42973-024-00161-w(認証リダイレクト)・日本政策金融公庫原典。
