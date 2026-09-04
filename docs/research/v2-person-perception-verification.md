# 人物知覚4段階案の敵対的検証（R3-2 材料）

作成: 2026-09-02 / 検証者: サブ(Opus 5) / 依頼: 親Claude
対象: 「人物情報を観測スキーマの第1級とし、①密度・流れ ②構造物(行列・人だかり・グループ) ③顕著な行為 ④知人の認識 の4段階で有界化する」案
規律: リポジトリ書き込みなし・ダウンロードなし・支持と反証の両方を探索

---

## ① 結論

**判定: 要修正（骨格は支持・棄却しない。ただし修正5件は「あると良い」ではなく「無いと台帳の強5本のうち A1・C1・U18 が成立しない」レベル）。**

支持の強さ: 4段階の「集約→構造→逸脱→個体」という階層は、人間の群衆知覚の実証構造（アンサンブル知覚／視覚crowding／注意容量3-4）と**独立に一致**する。先行実装（Generative Agents・AgentSociety・OASIS・Project Sid）はどれもこの階層を持たず、いずれも本案より粗いか、社会シムでない。**この点では本案は先行実装より良い。**

反証の強さ: 本案は**「視覚のみ・観測者を主体としてのみ扱う・全員に決定論的に届く」**の3点で現実と乖離する。とくに聴覚欠落は、最も近い先行実装のablationで**最強チャネル**と測定されており（後述）、単なる不足ではなく順位の誤りである。

### 修正案（優先順）

| # | 修正 | 理由の一行 | コスト |
|---|---|---|---|
| **M1** | **聴覚チャネルを新設**（モダリティ軸。段の追加ではない） | 最近接の先行実装のablationで、パニック伝播への寄与は voice 0.48 > gesture 0.31 > face/motion 0.16（全体0.60）。視覚だけの設計は最強チャネルを落とす | 低（無指向・距離減衰・遮蔽なし＝視覚より安い。セル＋隣接セルのイベント配送で足りる） |
| **M2** | **段④を「知人」から「近接他者上位k(k=3-4)」へ拡張**（④′） | ④の現形（関係リスト∩セル在圏者）では**見知らぬ人を一人も個別化できない**。A1(会話グループ形成の相手選択)・U18(加害者の被害者選択＝歩容による選別が実証済み)・接客・道を尋ねる、が全て成立しない | 中（上位k=3-4はMOT容量の実証値。O(セル人数)ソート1回、個体固有ブロック） |
| **M3** | **第5段「被注視性/exposure」を新設** | 「自分が見られている」は①-④のどれとも計算方向が逆（自分を客体として数える）。規範遵守・向社会行動・U18犯罪の抑止（natural surveillance）の直接の機構。**決定論的可視性事前計算の副産物としてほぼ無料** | 極小（isovistの逆引き＝「自分が可視な人数」。既に計算済みの行列の転置） |
| **M4** | **①を連続量でなく順序尺度に量子化**（Fruin LOS型 5-6段） | (a)人間は2 vs 3人/m²を区別できない・クラスタで系統的に過小評価する (b)バイト列が階級変化時のみ変わる＝prefixキャッシュのヒット率が桁で変わる。**現実忠実度とキャッシュ経済が同じ方向を指す稀な例** | 極小 |
| **M5** | **③の「イベント駆動で全員に配送」を「配送は全員・注意到達は確率的」に分離** | 携帯を見て歩く歩行者は一輪車の道化を見落とす（inattentional blindness実測）。全員が必ず気づく設計はC1カスケードの分母を壊し、「気づかれなさ」由来の現象（見て見ぬふり・目撃証言の欠落）が原理的に出ない | 低（配送済みブロックに注意ゲート1個。ただし**トークンは払う**ので予算宣言が必要——下記L3参照） |

### さらに、実装経済の主張に対する重大な指摘（3件・②で平易に説明）

- **L1: セル共有ブロックが512トークン未満なら、prefixキャッシュは無言でかからない**（Claude Opus 5の最小キャッシュ可能プレフィックスは512トークン。それ未満は `cache_creation_input_tokens: 0` でエラーも出ない）。①②のセル観測だけでは届かない可能性が高い。**場所の静的言語化とセル観測を1ブロックに束ねて512超を保証する**規約が要る。
- **L2: 同一セルの全員を同時に投げると、キャッシュ読みは1件も発生しない**。キャッシュ実体は「最初の応答がストリーム開始した後」に読めるようになる。N本の同時fan-outは全員がwrite(1.25×)でread 0。**1本先行→最初のトークン到着→残りN-1本発射**、が必須の実装規約。実測1.6-2.0xがこの規約下で測られたものかを確認すべき。
- **L3: 「セル共有ブロック」と「個体ブロック」はprefix順序で排他**。レンダリング順は tools→system→messages で、前方が1バイト変わると後方は全部無効。
  - 順序A `[静的][セル共有(毎step変化)][個体]` → セル共有はstep内で体間共有できるが、**個体のペルソナ/記憶は毎step全額**。
  - 順序B `[静的][個体(体ごとに不変)][セル共有]` → 個体は0.1×で読めるが、**セル共有は体間で1度も共有されない**。
  - どちらが得かは「個体ブロックのトークン数 vs セル共有ブロックのトークン数」で決まる。ただし順序Bには5分TTLの壁がある（40万体で同一個体の次の呼び出しまで5分以上空くなら失効。1h TTLはwrite 2×）。**この交換関係は予算宣言表(R1)に未記載。宣言＋Phase 2で実測すべき。**

---

## ② ユーザーがまず読む大枠（平易・10行）

1. **「人が最重要」というユーザー仮説は、心理学の実証で強く裏づけられます。** 人間は群衆を一人ずつ見ておらず、100ミリ秒程度で「平均の表情」「男女比」「平均の見た目」といった**要約統計**を取り出しています。①②の集約は当て推量ではなく、脳がやっていることそのものです。
2. **ただし4段階は「目だけ」の設計です。** いま最も近い先行研究（2026年・LLMで群衆の感情伝播を再現した実験）が要素ごとの寄与を測ったところ、パニックを広げた最大の要因は**声**（叫び声）で、表情や動きはずっと小さい寄与でした。渋谷は音の街です。**耳を足すべきです。**
3. **④「知人を見かける」だけでは足りません。** 現実の社会生活の大半は**見知らぬ人**が相手です。道を尋ねる相手を選ぶ、話しかける相手を選ぶ、犯罪者が被害者を選ぶ（歩き方で選ぶことが実証済み）——全部「見知らぬ人を1人だけよく見る」動作です。**「一番近い3-4人だけ個別に見る」**を足すべきです（人間が同時に追える人数の実験値が3-4人です）。
4. **「自分が見られている」感覚が抜けています。** これは規範や犯罪に直結し（見られていると人は行儀よくなる、という実験が多数）、しかも**あなたの設計ではタダで手に入ります**——可視性を事前計算した表をひっくり返すだけです。
5. **混雑度は「1.8人/m²」でなく「やや混雑」で持つべきです。** 人間はそもそも2人と3人の密度を区別できませんし、粗い段階で持つほうがLLMのキャッシュも効きます。忠実度と速度が珍しく同じ方向を向いています。
6. **キャッシュ節約の見積もりに3つの落とし穴があります**（短すぎるとキャッシュされない／同時に一斉送信すると節約ゼロ／個体情報とセル情報のどちらか片方しか節約できない）。実装前に実測してください。
7. **「ぶつからないのはエンジン、社会はLLM」という線引きには反例が複数あります**（視線の向きで人はよける方向を変える、仲間だと物理的に近づく、集団はV字で歩き流量を落とす）。線引き自体は維持でよいですが、**社会→物理へ細い一方通行の管**（パーソナルスペース半径・回避の左右の偏り・集団の結合強度）を1本通す必要があります。

---

## ③ 問い1: 現実整合の証拠

### 1-A. ①②はアンサンブル知覚と対応する（**支持・強い**）

- 群衆から要約統計（平均表情・男女比・平均のアイデンティティ／家族的類似）を、**一瞥（100ms以下）で**抽出できる。低次特徴（向き・色）から高次の社会的特徴まで階層的に成立する。Whitney & Yamanashi Leib, *Annual Review of Psychology* 2018. https://www.annualreviews.org/doi/10.1146/annurev-psych-010416-044232
- 群衆の平均表情（ensemble coding of crowd facial emotion）は空間配置でも時系列でも成立する。https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11201231/ ／ 平均表情が個別表情の印象を変える https://pubmed.ncbi.nlm.nih.gov/28557491/
- 男女比・crowd perceptionの個人差（女性の方が異質群の平均アイデンティティ推定が正確）。https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4557101/
- **機構的裏づけ**: 周辺視では visual crowding により**個体の同定は原理的に不可能**だが、「crowdingされた対象も特徴をアンサンブル／テクスチャに寄与させる」。つまり「個体は分からないが平均は分かる」という①②の設計は、視覚系の実際の制約そのもの。Whitney & Levi, *Trends in Cognitive Sciences* 2011. https://www.cell.com/trends/cognitive-sciences/abstract/S1364-6613(11)00032-5 ／ Bouma則の50人再現 https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10408772/

**反証側（設計に効く）:**
- **サブサンプリング説**: アンサンブルは全項目の並列平均ではなく「注意が数個だけ抽出して平均している」だけで同等の成績が再現できる（Myczek & Simons 2008のシミュレーション）。中間説（容量制限つき大域機構）も有力。→ **実装含意: ①をセル全員の厳密集約で計算する必要はない。k個サンプルの平均で心理的に等価**。O(セル人数)をO(k)に落としても忠実度は落ちない、と宣言できる。https://link.springer.com/article/10.3758/s13414-018-1560-5 ／ 容量制限の証拠 https://www.sciencedirect.com/science/article/abs/pii/S002839322200149X
- **数の知覚は系統的に歪む**: クラスタ化されるほど過小評価される（crowdingが原因ではない）。*Cognition* 2020. https://www.sciencedirect.com/science/article/abs/pii/S0010027720300147
- 群衆密度の観察者は 2 / 3 / 4 人/m² をほぼ区別できない（実務側の知見）。https://theconversation.com/how-do-scientists-estimate-crowd-sizes-at-public-events-and-why-are-they-often-disputed-262695
- **→ M4（順序尺度化）の根拠**。Fruinの歩行者LOS A-F（1971 HRR 355）が既存の6段順序尺度。https://onlinepubs.trb.org/Onlinepubs/hrr/1971/355/355-001.pdf ／ 実務まとめ https://www.gkstill.com/Support/crowd-flow/fruin/Fruin1.html

### 1-B. ②「グループ・行列・人だかり」は知覚的に第1級か（**支持・強い**）

- **facing dyad（向かい合う2体）は単体の顔・身体と同様に「1つのユニット」として構成的に処理される**（two-body inversion effect）。倒立で選択的に成績が落ちる＝配置に特化した表現がある。視覚探索でも facing dyad は検出されやすい。Papeo, Stein & Soto-Faraco, *Psychological Science* 2017. https://journals.sagepub.com/doi/abs/10.1177/0956797616685769 ／ 因果証拠（left EBAへのTMSで効果消失）*Current Biology* 2023. https://www.cell.com/current-biology/fulltext/S0960-9822(23)01664-0
- **現実の頻度**: 群衆の**最大70%が集団（友人・カップル・家族）として歩いている**。低密度では横並び、高密度ではV字に折れ、V字は「非空力的」で流量を下げる。Moussaïd et al., *PLoS ONE* 2010. https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0010047
- → ②は「便宜的なまとめ上げ」ではなく、**知覚単位としても現実頻度としても第1級**。A1（会話グループサイズ2人53.9%・95%が4人以下）の照合対象そのものであり、この段が無いとA1が観測できない。

### 1-C. ③「顕著な行為への注意捕捉」（**部分支持・ただし通説より弱い**）

- **反証: 「怒り顔は群衆からpop outする」（anger superiority / Öhman・Hansen & Hansen 1988）は再現性が争われている。** 低次視覚交絡を除去した7実験で「怒り顔はpop outせず、効率的にすら検出されない」、むしろ**happy優位**の探索非対称が出た。https://www.researchgate.net/publication/51482489_The_Face_in_the_Crowd_Effect_Unconfounded_Happy_Faces_Not_Angry_Faces_Are_More_Efficiently_Detected_in_Single-_and_Multiple-Target_Visual_Search_Tasks （反対側の再現主張もある: https://www.academia.edu/78516383/The_face_in_the_crowd_effect_Anger_superiority_when_using_real_faces_and_multiple_identities ）
  → **含意: 「顔の情動」を③の駆動にしてはいけない。③は「身体全体の逸脱行為・音・大きな運動」で駆動すべき。** これはM1（聴覚）とも整合する。
- **反証: 見落としは大きい。** 携帯で通話中の歩行者は経路上の一輪車の道化を有意に見落とす。Hyman et al., *Applied Cognitive Psychology* 2010. https://onlinelibrary.wiley.com/doi/abs/10.1002/acp.1638 ／ 台北の実地観察でも同様 https://pmc.ncbi.nlm.nih.gov/articles/PMC6311895/ ／ 群衆シミュ側の実装前例「Modelling distracted agents in crowd simulations」*The Visual Computer* 2020 https://link.springer.com/article/10.1007/s00371-020-01969-4
- **支持（ただし方向は逆に注意）: 実際の緊急時、傍観者は介入する。** CCTV映像の国際比較で**公共空間の対立の10件中9件で少なくとも1人が介入**し、傍観者数が多いほど介入確率が上がる（古典的傍観者効果は危険場面では成立しない）。Philpot et al. 2020 系。https://journals.sagepub.com/doi/10.1177/19485506211042683 ／ https://onlinelibrary.wiley.com/doi/full/10.1002/ab.21853
  → **含意: ③の「配送」は正しい（多くの人に届く）。誤りは「注意到達＝100%」の側**。M5の分離が正解で、しかも介入率の実測値（9/10）が較正アンカーになりうる。

### 1-D. ④「既知の顔の検出」（**支持だが、案の前提より弱い**）

- **知人の顔はpop outしない。** 自分の子どもの顔でさえ、集合写真からの探索は**注意を要する直列探索**で、妨害顔数に依存する。*Scientific Reports* 2024. https://www.nature.com/articles/s41598-024-66964-4 ／ 「人はpop outするか」 https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4595219/
- **ただし個人的に馴染みのある顔は、少ない注意資源で・意識に上らずとも検出でき、180msでの検出報告もある**（部分ベース処理が効くため倒立にも頑健）。https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5459439/ ／ 群衆内の既知/未知顔 https://psycnet.apa.org/record/2014-39120-015
- → **含意: ④の「関係リスト∩セル在圏者の交差のみ・全走査禁止」という計算形は、心理学的にはむしろ正しい**（全走査＝pop out仮説に相当し、それが否定されている）。ただし**検出率を1.0にしてはいけない**（直列探索＝混雑と注意状態に依存）。混雑度（①）と注意状態を条件にした確率で良い。

### 1-E. 欠けている段の候補（依頼で名指しされた4件＋2件）

| 候補 | 実証の有無 | 4段階のどこに入るか | 判定 |
|---|---|---|---|
| **群衆の構成（デモグラフィック的雰囲気）** | **あり**。男女比・平均アイデンティティ/家族的類似はアンサンブルとして抽出される（Whitney & Yamanashi Leib 2018; https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4557101/ ）。声のアンサンブルでも性比が脅威・帰属感の判断を変える（*Sci Rep* 2024 https://www.nature.com/articles/s41598-024-65535-x ） | **①のスキーマ拡張で足りる**（新段不要）。ただし現案の①は「密度・流れ」だけ＝**フィールドが足りない**。年齢帯・性比・服装カテゴリ（スーツ/制服/観光客）の分布を①に追加 | **要修正（段は不要・スキーマ追加）** |
| **被注視感（自分が見られている）** | **あり・強い**。直接注視は覚醒早期から注意を捕捉し、自己参照処理を起動する（stare-in-the-crowd effect: https://www.nature.com/articles/s41598-019-39342-8 ／ 測定パラダイム https://link.springer.com/article/10.3758/s13428-014-0514-7 ／ 幾何図形でも生じる https://journals.sagepub.com/doi/10.1177/0301006620934320 ）。watching-eyes効果＝自己意識・記憶・向社会行動・他者評価の4系統（Conty et al., *Consciousness and Cognition* 2016 https://www.sciencedirect.com/science/article/pii/S1053810016302501 ／ https://www.sciencedirect.com/science/article/abs/pii/S1053810019301242 ） | **①-④のどれにも入らない**（自分を客体として数える＝計算方向が逆） | **第5段が必要（M3）**。実装は可視性行列の転置＝ほぼ無料。U18・規範・「eyes on the street」に直結 |
| **群衆の情動（パニック・熱気）の伝播** | **あり**。感情伝播は二者を超えて第三者へ無自覚に伝わる（*PLoS ONE* 2013 https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0067371 ）。ABM側の系統的レビュー: *AAMAS* 2022 https://link.springer.com/article/10.1007/s10458-022-09589-z ／ 恐怖伝播モデルの経験的評価 https://link.springer.com/article/10.1007/s10458-013-9220-6 | **①（平均情動＝アンサンブル）＋③（伝播イベント）に分解可能**。ただし主チャネルは**声**（下記M1） | **段は不要・M1が本体** |
| **視線方向の追従（gaze following）** | **あり・定量的**。実地: 歩行者3,325人を追跡、Oxfordの商店街で2,822人の視線追従を計測（Gallup et al., *PNAS* 2012 https://www.pnas.org/doi/10.1073/pnas.1116141109 ）。Milgram 1969の刺激群サイズ効果は5人以上で飽和。VR再現では**最近接の3体以上が上を向くとほぼ100%が追従**（1体で約50%、伝播モデル当てはめで T=0.7 は実世界の T=1.2-7 より低い＝仮想の方が伝播しやすい）*J. R. Soc. Interface* 2018 https://pmc.ncbi.nlm.nih.gov/articles/PMC6127183/ (DOI: 10.1098/rsif.2018.0335) ／ 相反手がかり下の合意的追従 https://link.springer.com/article/10.3758/s13414-017-1303-z | **②に統合すべき**（「人だかり」の構造＝多数の視線が向く方向）。ただし**独立フィールドとして明示が必要** | **要修正（②にフィールド追加）**。**C1（カスケードの99%が1世代で終了・中央値1.3）の直接の観測装置**になる——現案の②では視線がないのでC1が街頭で観測できない |
| **【追加発見】聴覚** | **あり・最強**。下記M1 | **どこにも無い（モダリティ軸の欠落）** | **新設必須（M1）** |
| **【追加発見】近接他者の個別化（見知らぬ人）** | **あり**。100ms提示で信頼性・有能さ・攻撃性の特性判断が成立し、提示時間を延ばしても相関は上がらない（Willis & Todorov, *Psychological Science* 2006 https://journals.sagepub.com/doi/10.1111/j.1467-9280.2006.01750.x ）。犯罪側: 服役中の暴力犯が路上動画から被害者を選別し、**歩容の5カテゴリが被害者/非被害者を分けた**（Grayson & Stein, *Journal of Communication* 1981 https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1460-2466.1981.tb01206.x ／ https://eric.ed.gov/?id=EJ238367 ）。規範側: 都市の既定は**civil inattention**＝約2.4-3mで一瞬視線を合わせて外す。実証操作化（Arminen & Heino）では**「有標」な外見（日傘・アバヤ+ニカブ）への civil inattention 違反は無標条件の10倍**。https://www.frontiersin.org/journals/sociology/articles/10.3389/fsoc.2023.1212090/full ／ https://bpspsychub.onlinelibrary.wiley.com/doi/10.1111/bjso.12828 | **④が知人限定なので入らない** | **④′として拡張必須（M2）**。上位k=3-4（MOT容量: 通常3-4個 https://jov.arvojournals.org/article.aspx?articleid=2121950 ／ https://www.jneurosci.org/content/28/16/4183 ） |

---

## ③ 問い2: 実装の最良性 — 先行実装との比較

### 2-A. LLM社会シム系の人物知覚の実際

| 実装 | 規模 | 人物知覚の形 | 本案との差 |
|---|---|---|---|
| **Generative Agents (Stanford, UIST 2023)** https://dl.acm.org/doi/10.1145/3586183.3606763 | 25体 | Perceiveモジュールが**周囲のゲームオブジェクトを感知**し、自然言語の観測文をmemory streamへ全記録。半径内の全イベント | **段階なし・上位kなし・集約なし**。40万体に外挿すると爆発（v1のrunB二乗爆発と同型の構造） |
| **AgentSociety (Tsinghua, ACL 2025)** https://arxiv.org/abs/2502.08691 | 10k体・500万相互作用 | 都市空間はOSM由来のAOI/POI。**専用の知覚モジュールは論文中に明示されない**。「空間近接によるオフライン相互作用」と社会ネットワーク参照 | 都市規模で最も近いが、**人物知覚のスキーマが無い**。本案の方が細かい |
| **OASIS (CAMEL-AI, 2024)** https://arxiv.org/abs/2411.11581 | **100万体** | **推薦システムによるtop-kフィード**（in-network=いいね数順、out-of-network=TwHIN-BERT興味マッチ+新しさ+フォロワー数）。**空間的な人物知覚は存在しない**（SNSシム） | 100万体の唯一の前例だが対象が違う。**コスト実測値は貴重: 1M体で18.0時間/1タイムステップ・A100×27。100k体で3.0時間・A100×5** |
| **Project Sid / PIANO (Altera, 2024)** https://arxiv.org/abs/2411.00114 | 10-1000+体 | 並列モジュールが複数入力ストリームを同時処理（Minecraft内） | 人物知覚の有界化は主題でない |
| **Concordia (DeepMind, 2023)** https://arxiv.org/pdf/2312.03664 | 小規模 | **Game Masterがエージェントに観測を与える**（TRPG型）。誰が何を見るかはGMの裁量 | 本案の「知覚契約」に近いが、有界化の定量規約が無い |
| **【最重要】Affect propagation in LLM crowds (2026)** https://arxiv.org/html/2607.25140v1 | **10-26体** | **視覚（8m・200°FOV・壁と身体で遮蔽）＋聴覚（無指向: 叫び20m・雑談10m）＋触覚（群集圧＝希望速度と実速度の差）**。自然言語化して投入。「可視群衆の要約」＋**最近接3体の詳細な表出状態** | **本案に最も近い先行実装。しかも本案に無いものを3つ持っている（聴覚・触覚・最近接3体の個別化）** |

**この最後の1本が検証全体で最も重い。** そのablation（Standing Line・各20ラン）:

| 条件 | パニック割合 |
|---|---|
| 全モダリティ | 0.60 |
| 全消音（対照） | 0.09 |
| **声のみ** | **0.48**（曝露率53%） |
| 身振りのみ | 0.31（曝露時の条件付き発生80%） |
| 表情/動きのみ | 約0.16 |

さらに: 警戒の伝播は**約0.96 m/sの進行波**、SISモデル的に**約22%で非ゼロプラトー**。プロンプト成分のablationでは**パーソナリティ・ブロックを外すと効果が全部消える**（|ΔV|,|ΔA| < 0.01）。バックエンド依存も大（gpt-4o-miniではパーソナリティ差がほぼ消滅）。

→ **含意3つ**: (i) M1（聴覚）は必須。(ii) M2（最近接k体の個別化）は先行実装が既に採用している。(iii) **「LLMの人物知覚実験は、モデルとプロンプト構成に対して脆い」**——`AI Agents Alone Are Not (Yet) Sufficient for Social Simulation` https://arxiv.org/html/2603.00113v2 が「情報の存在と主体の気づきを同一視する設計は決定過程を歪める」「小さなプロンプト差で結論が動く」と警告し、**環境（曝露機構・スケジューリング）を監査可能にせよ**と勧告している。**これは本案の「知覚契約を宣言可能・機械検査可能にする」（憲法5精密化）と完全に同じ方向で、本案の強い支持材料。**

### 2-B. synthetic vision 系をLLMに渡さない判断（**妥当・支持**）

- Ondřej, Pettré, Olivier & Donikian, *SIGGRAPH 2010* 「A synthetic-vision based steering approach for crowd simulation」: エージェントに合成視覚を与え、そこから衝突回避を導くと**自己組織化パターンが創発**する。 https://dl.acm.org/doi/10.1145/1833349.1778860 ／ 著者PDF https://people.rennes.inria.fr/Julien.Pettre/pdf/SIGGRAPH2010.pdf
  → これは**下層（操舵）の話であり、LLMに渡す層ではない**。本案の分業は文献の分業と一致する。
- **反証候補（2026年・最新）**: CrowdVLA https://arxiv.org/html/2604.05525v1 は Qwen3-VL-2B + LoRA で三人称エゴ視点画像を入力し、20フレーム刻みで64個の動作スキルを選ぶ。「知覚駆動・帰結を意識した意思決定」として群衆シミュを再定義する主張。
  **ただし敵対的に読むと弱い**: (a) **数千体は依然compute-boundと自認**、スループット数値なし。(b) 比較対象が視覚ベース2手法のみで、**ORCA/社会力モデルとの比較が無い**。(c) **視覚 vs 記号/構造化観測のablationが無い**——つまり「画像である必要があった」ことを示していない。
  → **R3-1のVLA不採用（U17答申: 視覚は高レベル判断に効かず56.3 vs 58.0・言語化>生画像 +18.4pt）を覆す証拠にはならない。判断は維持でよい。**

### 2-C. MMO/ゲームの関心管理（**本案の配送層は業界標準そのもの・支持**）

- Unreal **Replication Graph**: Grid Spatialization 2D ノード（世界をグリッドに分割し、セルごとに可視アクタのリストを保持＝クライアントは距離判定をせずセルのリストを引くだけ）／Always Relevant ノード（空間に関係なく全員に関連）／**Dormancy**（休眠アクタは別リストで静的扱い、起きると動的扱い）。 https://dev.epicgames.com/documentation/unreal-engine/replication-graph-in-unreal-engine ／ https://www.unrealengine.com/en-US/tech-blog/replication-graph-overview-and-proper-replication-methods ／ https://dev.epicgames.com/documentation/unreal-engine/actor-network-dormancy-in-unreal-engine
- 学術側の総説: Liu & Theodoropoulos, "Interest management for distributed virtual environments: A survey", *ACM Computing Surveys* 46(4), 2014. https://dl.acm.org/doi/10.1145/2535417 ／ アルゴリズム比較 https://dl.acm.org/doi/abs/10.1145/1230040.1230069
- → **本案の5ノード（場所セル共有/常時関連/個体固有/dormant/attachment）はReplication Graphの直訳で、産業標準と一致。ここは反証なし。**
- ABM側の定石（空間ハッシュ/グリッドでO(N²)回避）は自明で、明確な比較論文は見つからなかった（→⑤で正直に記載）。U7（チャンクSoA+空間グリッド）で既に決定済みなので追加検討は不要。

### 2-D. 代替案比較表

評価軸: 現実忠実度 / 計算量 / 台帳適合（A1会話グループ・C1カスケード・D1滞在・D4′人流・U18犯罪）/ prefix共有経済

| 方式 | 現実忠実度 | 計算量 | A1 | C1 | D1 | D4′ | U18 | prefix経済 | 代表 |
|---|---|---|---|---|---|---|---|---|---|
| **(a) 半径内全イベント** | 中（集約が無く「一人ずつ見る」＝crowdingの実証に反する） | **O(半径内人数)/体 → 40万体で破綻**（runB同型） | △ 相手選択はできる | △ 伝播は追えるが分母が爆発 | ○ | ○ | △ | ×（体ごとに全部違う） | Generative Agents |
| **(b) synthetic vision をLLMへ** | 高（下層）/ 不明（上層。U17実測では効かない） | **×**（VLM推論が毎step。CrowdVLAが数千体でcompute-bound自認） | × | × | △ | △ | △ | ×（画像はキャッシュ共有困難） | Ondřej 2010 / CrowdVLA 2026 |
| **(c) 本4段階案（現形）** | 中〜高（①②は強く裏づけ。③④に過大仮定・視覚のみ） | **○ O(セル数)+O(k)** | **△（見知らぬ人を個別化できず相手選択が不能）** | **△（視線フィールドが無くカスケードの機構が観測できない）** | ○ | ○ | **×（被害者選択・被注視性が無い）** | △（L1-L3の未検証） | 本案 |
| **(c′) 本案＋M1-M5** | **高** | ○（増分は聴覚イベント配送＋上位kソート＋転置1回＝いずれもO(セル人数)以下） | **○** | **○** | ○ | ○ | **○** | **○（M4で量子化・L1-L3を規約化）** | 提案 |
| **(d) 関心管理＋優先度上位k（AOI/Replication Graph）** | — （配送層であり知覚モデルではない） | ◎ | — | — | — | — | — | ◎ | UE / MMO |
| **(e) 推薦システム型 top-kフィード** | 低（空間が無い） | ◎（100万体実証） | × | ○（SNS側のC1には最適） | × | × | × | ○ | OASIS |
| **(f) モダリティ別チャネル＋近接3体詳細** | **高（唯一ablationで検証済み）** | 中（8m/200°FOV+遮蔽の可視性計算が毎step。ただし本案は事前計算済みなので安い） | ○ | ○ | ○ | ○ | ○ | 未検討 | arXiv 2607.25140 |
| **(g) 集約LOD（連続体/群として扱い、必要時のみ個体化）** | 中（密群衆では妥当） | ◎ | × | × | ○ | ◎ | × | ◎ | Aggregate Dynamics for Dense Crowd Simulation ほか |

**結論: (c′) = 本案 + M1-M5 が最良。** (c)単体では (f) に負ける（(f)は同じ構造を持ちながら聴覚・触覚・近接個別化を追加し、しかもablationで検証済み）。(c′)は(f)の要素を全部含み、かつ(f)が持たない有界化（セル集約・事前計算可視性・上位k・Replication Graph配送）を持つので、40万体で唯一成立しうる。

---

## ③ 問い3: 「衝突回避＝エンジン / 社会的知覚＝LLM」の反例

**反例は複数あり、かつ実測を伴う。線引きは維持できるが、無修正では維持できない。**

| # | 反例 | 出典 | 影響の向き |
|---|---|---|---|
| R1 | **視線方向が回避方向を決める**。他者の視線は移動方向の手がかりとして使われ、通行人は**視線と反対側へよける** | Nummenmaa, Hyönä & Hietanen, *Psychological Science* 20:1454-1458 (2009)。後続の実証: 相互視線の衝突回避への効果 https://www.researchgate.net/publication/324029801_Effect_of_mutual_gaze_on_collision_avoidance_behavior_during_human_walking ／ 仮想人物の視線行動 https://people.rennes.inria.fr/Julien.Pettre/pdf/18VRLYNCH.pdf ／ 仮想群衆の通り抜けは注視で予測できる https://www.sciencedirect.com/science/article/abs/pii/S0001691817305632 | 社会情報 → 下層運動（**左右の偏り**） |
| R2 | **社会的アイデンティティが対人距離を変える**。内集団成員（見知らぬ人でも）には物理的に近づき、群衆の混んだ部分へ寄る。2集団がすれ違うとき、各人は自集団側へ寄る（空間に余裕があっても） | Templeton, Drury & Philippides, "Walking together: behavioural signatures of psychological crowds", *Royal Society Open Science* 5:180172 (2018) https://royalsocietypublishing.org/rsos/article/5/7/180172/94580 ／ https://pubmed.ncbi.nlm.nih.gov/30109073/ ／ ESIM https://www.sussex.ac.uk/research/labs/crowds-and-identities/publications/ | 社会情報 → 下層運動（**パーソナルスペース半径・凝集**） |
| R3 | **集団構造が流量を変える**。70%が集団で歩き、高密度でV字化し、V字は流量を落とす | Moussaïd et al., *PLoS ONE* 5:e10047 (2010) https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0010047 ／ 双方向流への影響 https://arxiv.org/pdf/1910.04337 ／ 群のproxemicsと透過性 https://arxiv.org/pdf/2510.26571 ／ 2人組と個人の衝突回避の社会的側面 https://arxiv.org/pdf/2305.18343 | 社会構造 → **マクロ流量（D4′に直結）** |
| R4 | **見た目が視線行動を変える**。有標な外見への civil inattention 違反は10倍 | Arminen & Heino ほか。総説 https://www.frontiersin.org/journals/sociology/articles/10.3389/fsoc.2023.1212090/full | 社会情報 → 視線（→R1経由で運動へ） |
| R5 | **情動表出が移動を支配する**。エージェントの外向的表出が「群衆内での動き方を支配する」設計が既に採られ、伝播波0.96 m/sを再現 | https://arxiv.org/html/2607.25140v1 | 情動 → 下層運動 |
| R6 | 群衆シミュ側は既に「社会規則＋視線」を操舵に統合し始めている | "Social Crowd Simulation: Improving Realism with Social Rules and Gaze Behavior", *ACM SIGGRAPH MIG* 2024 https://dl.acm.org/doi/10.1145/3677388.3696337 ／ 群単位の注視行動＋性格 https://onlinelibrary.wiley.com/doi/abs/10.1002/cav.1806 ／ 群衆の注視モデル Grillon & Thalmann, *CAVW* 20(2):111-119 (2009) https://onlinelibrary.wiley.com/doi/abs/10.1002/cav.293 | 産業/学術の趨勢 |

**修正案（線引きを壊さない形）:**

> **社会→物理の一方向・低次元・低頻度チャネルを1本だけ通す（"変調ベクトル"）。**
> LLM/認知層は毎stepではなくT0習慣・状態変化時にのみ、以下のスカラーを物理層へ書き出す:
> `{personal_space_r, group_cohesion, avoid_side_bias, desired_speed, attention_load}`
> 物理層（ORCA/SFM）はこれをパラメータとして読むだけ。逆方向（物理→社会）は既存の観測経路のみ。

これは決定済みの原則4「量はスカラー、質は自由文」および原則2「LLMの出力は意図まで・結果はエンジン」と矛盾しない。**むしろ、この管が無いと D4′（3街路の日内プロファイル分化）と A1（会話グループ）が物理層に反映されず、「集団で歩く」という現実の70%が再現できない。**

---

## ④ 未発見・不確実の正直な列挙

1. **「上位k件」のkの根拠は転用である。** MOTの3-4は「同一の動く物体を同時追跡できる数」であり、「群衆で同時に個別化できる人数」を直接測った研究は**見つけられなかった**。k=3はarXiv 2607.25140が採用した値だが、その論文もkの根拠を実証で示していない。**k=3を仮採用し、感度試験（k=1/3/5）をablation予約20%枠で行うべき。**
2. **「セル共有ブロックのバイト一致で実測1.6-2.0x」の元データを私は確認していない。** 上のL1-L3は仕様（プレフィックス一致・512トークン最小・同時fan-outの読み不可・レンダリング順 tools→system→messages・read 0.1×/write 1.25×or2×・breakpoint最大4）から導いた**論理的帰結**であり、本プロジェクトの実測条件を知らない。**実測がどの順序・どの並行度で行われたかの確認が先。**
3. **可視性事前計算（isovist）とセル共有ブロックの整合を検証していない。** 同一セル内でも個体ごとに見えるものが違うなら、「セル共有ブロックはバイト一致」と「決定論的可視性は個体ごと」は原理的に衝突する。**セル×可視性クラスで分割するか、セル共有ブロックを「セル代表の可視範囲」と定義し直すかの決着が必要**（この論点は本検証で新たに発見したもので、文献ではなく設計内部の矛盾）。
4. **ABMの近傍探索（空間ハッシュ vs kd-tree等）の定量比較論文を見つけられなかった。** 検索は当たらず、総説レベルの記述に留まった。U7で既に決定済みなので実害は無いと判断した。
5. **渋谷固有の実証（スクランブル交差点の知覚・日本語圏のcivil inattention規範）を探していない。** civil inattentionの実証（Arminen & Heino）はフィンランド。視線規範の文化差は大きい可能性があり、**D4′やA1の較正時に「文化差＝expedientタグ」として宣言が必要かもしれない**。
6. **アンサンブル知覚の「社会的高次特徴」は主に静止顔の実験室研究**である。歩行中・遮蔽あり・数百人規模の街頭で同じ精度が出る証拠は弱い。①②の忠実度主張は「機構の方向は正しい」までに留め、**精度の主張はしないほうが安全**。
7. **「顕著な行為」の検出率の実数を持っていない。** Philpotらの「10件中9件で介入」は介入率であって**知覚率ではない**。M5の確率パラメータの較正アンカーは未特定。
8. **聴覚の距離減衰パラメータ（叫び20m・雑談10m）は arXiv 2607.25140 の設定値であり、実測の出典が確認できていない。** 都市サウンドスケープ研究（例 https://pmc.ncbi.nlm.nih.gov/articles/PMC9957327/ ／ https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6123620/ ）は知覚構造は扱うが**到達距離の数値は与えない**。M1を採るなら、この数値には expedient タグと感度試験が必要。
9. **face-in-the-crowd（怒り顔優位）は学界で決着していない。** 私は「弱い/交絡疑い」側が強いと判断したが、実顔・多アイデンティティでの再現主張もある。③を顔情動で駆動しない、という私の勧告はこの判断に依存している。
10. **OASISの「18.0時間/1タイムステップ」が本プロジェクトの「≤24h/シミュ日」と比較可能かは不明**（タイムステップの定義が違う）。桁感の参考にとどめるべき。

---

## 付録: 支持と反証のどちらが強かったか（総括）

| 論点 | 支持 | 反証 | 判定 |
|---|---|---|---|
| ①②＝アンサンブル知覚 | **強**（Annual Review・crowding機構・複数実証） | 弱（サブサンプリング説は「もっと安く作れる」という**追い風**の反証） | **支持** |
| ②＝グループ検出が第1級 | **強**（two-body inversion + TMS因果 + 群れ70%） | 見つからず | **支持** |
| ③＝逸脱への注意捕捉 | 中（介入9/10・Milgram系） | **強**（anger superiorityの再現性・inattentional blindness） | **要修正（M5・顔情動で駆動しない）** |
| ④＝知人検出の交差計算 | **強**（pop outしない＝全走査禁止は正しい） | 中（検出率1.0は誤り） | **支持＋確率化** |
| 4段階で十分か | — | **強**（聴覚・近接他者・被注視性の3欠落。うち聴覚は最近接先行実装のablationで最大寄与） | **不十分（M1-M3）** |
| Replication Graph型配送 | **強**（産業標準・ACM CSUR総説） | 見つからず | **支持** |
| VLA/synthetic visionをLLMに渡さない | **強**（U17実測 + CrowdVLAの弱いablation） | 弱（CrowdVLAは比較設計が不十分） | **支持（維持）** |
| 2層分業（衝突回避＝エンジン） | 中 | **強**（R1-R6の6反例・うち3件は定量） | **要修正（変調ベクトル1本）** |
| prefix共有経済 | 未確認 | **中**（L1-L3の構造的制約） | **要実測** |

---

### 出典一覧（正規ドメインのみ）

心理学・行動科学: [annualreviews.org/annurev-psych-010416-044232](https://www.annualreviews.org/doi/10.1146/annurev-psych-010416-044232) ／ [cell.com TiCS visual crowding](https://www.cell.com/trends/cognitive-sciences/abstract/S1364-6613(11)00032-5) ／ [PMC10408772 Bouma law](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10408772/) ／ [PMC4557101 gender differences in crowd perception](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4557101/) ／ [PMC11201231 ensemble cross-category expressions](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11201231/) ／ [pubmed 28557491 average crowd expression](https://pubmed.ncbi.nlm.nih.gov/28557491/) ／ [nature s41598-024-65535-x vocal sex ratio](https://www.nature.com/articles/s41598-024-65535-x) ／ [sciencedirect S0010027720300147 clustering underestimation](https://www.sciencedirect.com/science/article/abs/pii/S0010027720300147) ／ [springer 10.3758/s13414-018-1560-5 spatial grouping](https://link.springer.com/article/10.3758/s13414-018-1560-5) ／ [sciencedirect S002839322200149X ensemble size neural](https://www.sciencedirect.com/science/article/abs/pii/S002839322200149X) ／ [sagepub two-body inversion](https://journals.sagepub.com/doi/abs/10.1177/0956797616685769) ／ [cell.com Current Biology left EBA](https://www.cell.com/current-biology/fulltext/S0960-9822(23)01664-0) ／ [nature s41598-024-66964-4 searching for one's child](https://www.nature.com/articles/s41598-024-66964-4) ／ [PMC4595219 Do people pop out](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4595219/) ／ [PMC5459439 familiarity feature-based](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5459439/) ／ [psycnet 2014-39120-015 familiar/unfamiliar in a crowd](https://psycnet.apa.org/record/2014-39120-015) ／ [sagepub Willis & Todorov 100ms](https://journals.sagepub.com/doi/10.1111/j.1467-9280.2006.01750.x) ／ [nature s41598-019-39342-8 stare-in-the-crowd](https://www.nature.com/articles/s41598-019-39342-8) ／ [springer 10.3758/s13428-014-0514-7 SITC paradigm](https://link.springer.com/article/10.3758/s13428-014-0514-7) ／ [sagepub gazing without eyes](https://journals.sagepub.com/doi/10.1177/0301006620934320) ／ [sciencedirect S1053810016302501 watching eyes](https://www.sciencedirect.com/science/article/pii/S1053810016302501) ／ [sciencedirect S1053810019301242 being watched](https://www.sciencedirect.com/science/article/abs/pii/S1053810019301242) ／ [pnas 1116141109 visual attention in human crowds](https://www.pnas.org/doi/10.1073/pnas.1116141109) ／ [PMC6127183 drawing power of virtual crowds](https://pmc.ncbi.nlm.nih.gov/articles/PMC6127183/) ／ [springer 10.3758/s13414-017-1303-z perceiving crowd attention](https://link.springer.com/article/10.3758/s13414-017-1303-z) ／ [wiley acp.1638 unicycling clown](https://onlinelibrary.wiley.com/doi/abs/10.1002/acp.1638) ／ [PMC6311895 smartphone inattentional blindness Taipei](https://pmc.ncbi.nlm.nih.gov/articles/PMC6311895/) ／ [sagepub CCTV danger & intervention](https://journals.sagepub.com/doi/10.1177/19485506211042683) ／ [wiley ab.21853 social relations & bystander](https://onlinelibrary.wiley.com/doi/full/10.1002/ab.21853) ／ [wiley Grayson & Stein 1981](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1460-2466.1981.tb01206.x) ／ [eric EJ238367](https://eric.ed.gov/?id=EJ238367) ／ [frontiersin civil inattention](https://www.frontiersin.org/journals/sociology/articles/10.3389/fsoc.2023.1212090/full) ／ [bpspsychub bjso.12828 civil inattention needs](https://bpspsychub.onlinelibrary.wiley.com/doi/10.1111/bjso.12828) ／ [jov MOT capacity](https://jov.arvojournals.org/article.aspx?articleid=2121950) ／ [jneurosci 28/16/4183](https://www.jneurosci.org/content/28/16/4183) ／ [plos 0067371 contagion beyond dyads](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0067371)

群衆・都市: [plos 0010047 pedestrian social groups](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0010047) ／ [royalsociety rsos 180172 walking together](https://royalsocietypublishing.org/rsos/article/5/7/180172/94580) ／ [pubmed 30109073](https://pubmed.ncbi.nlm.nih.gov/30109073/) ／ [sussex crowds & identities](https://www.sussex.ac.uk/research/labs/crowds-and-identities/publications/) ／ [arxiv 1910.04337 social groups bidirectional flow](https://arxiv.org/pdf/1910.04337) ／ [arxiv 2510.26571 proxemics & permeability](https://arxiv.org/pdf/2510.26571) ／ [arxiv 2305.18343 social aspects of collision avoidance](https://arxiv.org/pdf/2305.18343) ／ [springer 10.1007/s10458-022-09589-z emotion contagion review](https://link.springer.com/article/10.1007/s10458-022-09589-z) ／ [springer 10.1007/s10458-013-9220-6 fear contagion evaluation](https://link.springer.com/article/10.1007/s10458-013-9220-6) ／ [springer 10.1007/s00371-020-01969-4 distracted agents](https://link.springer.com/article/10.1007/s00371-020-01969-4) ／ [trb Fruin 1971](https://onlinepubs.trb.org/Onlinepubs/hrr/1971/355/355-001.pdf)

実装・工学: [acm 3586183.3606763 Generative Agents](https://dl.acm.org/doi/10.1145/3586183.3606763) ／ [arxiv 2502.08691 AgentSociety](https://arxiv.org/abs/2502.08691) ／ [arxiv 2411.11581 OASIS](https://arxiv.org/abs/2411.11581) ／ [arxiv 2411.00114 Project Sid](https://arxiv.org/abs/2411.00114) ／ [arxiv 2312.03664 Concordia](https://arxiv.org/pdf/2312.03664) ／ [arxiv 2607.25140 affect propagation in LLM crowds](https://arxiv.org/html/2607.25140v1) ／ [arxiv 2603.00113 AI agents not yet sufficient](https://arxiv.org/html/2603.00113v2) ／ [arxiv 2604.05525 CrowdVLA](https://arxiv.org/html/2604.05525v1) ／ [arxiv 2402.02053 Affordable Generative Agents](https://arxiv.org/abs/2402.02053) ／ [acm 1833349.1778860 synthetic vision steering](https://dl.acm.org/doi/10.1145/1833349.1778860) ／ [inria SIGGRAPH2010 PDF](https://people.rennes.inria.fr/Julien.Pettre/pdf/SIGGRAPH2010.pdf) ／ [acm 2535417 interest management survey](https://dl.acm.org/doi/10.1145/2535417) ／ [acm 1230040.1230069 comparing IM algorithms](https://dl.acm.org/doi/abs/10.1145/1230040.1230069) ／ [epicgames replication graph](https://dev.epicgames.com/documentation/unreal-engine/replication-graph-in-unreal-engine) ／ [epicgames actor network dormancy](https://dev.epicgames.com/documentation/unreal-engine/actor-network-dormancy-in-unreal-engine) ／ [unrealengine tech-blog replication graph](https://www.unrealengine.com/en-US/tech-blog/replication-graph-overview-and-proper-replication-methods) ／ [acm 3677388.3696337 social crowd simulation gaze](https://dl.acm.org/doi/10.1145/3677388.3696337) ／ [wiley cav.293 Grillon & Thalmann](https://onlinelibrary.wiley.com/doi/abs/10.1002/cav.293) ／ [wiley cav.1806 group-based gaze](https://onlinelibrary.wiley.com/doi/abs/10.1002/cav.1806) ／ [inria 18VRLYNCH gaze in avoidance](https://people.rennes.inria.fr/Julien.Pettre/pdf/18VRLYNCH.pdf)
