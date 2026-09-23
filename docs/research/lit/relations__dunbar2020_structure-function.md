# Dunbar 2020 — Structure and function in human and primate social networks: implications for diffusion, network stability and health

- リンク: https://doi.org/10.1098/rspa.2020.0446 (全文 PDF: https://ora.ox.ac.uk/objects/uuid:f56e97cb-c481-449c-b792-a76156550d9e/) | 分野: 社会ネットワーク科学 #14 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-17・リサーチサブが ORA 版 PDF を WebFetch → pymupdf で本文抽出。**親未確認**)。*Proc. R. Soc. A* 476:20200446、受理 2020-07-10、**CC BY 4.0**。査読つき総説。

## 主張(claim)

人間の自我中心網は**フラクタルな層構造**を持ち、層は **接触頻度**で定義される。累積の層サイズは **1.5 / 5 / 15 / 50 / 150 / 500 / 1500 / 5000** で、**隣接層の比は約 3**。社会的努力の **40% が最内層 5 人・20% が次の 10 人・合わせて 60% が 15 人**に向かう。構造は認知制約と**時間制約**の産物。

## 機構(mechanism)

接触頻度の分布は単純な冪則ではなく**段(plateau)**を持ち、クラスタ解析で 4 層が出る。層を維持するには時間投資が要り、時間は非弾性なので層サイズに上限がかかる。信頼(trust)が層構造を支える認知機構で、信頼を損なう内外の脅威は網の断片化と再編を招く。

## 数値(出所つき)

- 逐語(層と頻度): "This gives the network a layered structure, where individual alters in a given layer are **contacted with more or less similar frequency** and there is a sharp drop-off in contact frequencies to the next layer."
- 逐語(倍率): "when counted cumulatively, they have a very distinct scaling ratio: **each layer is approximately three times the size of the layer immediately inside it** (figure 2)."
- 逐語(頻度が層を決める): "**Each layer seems to correspond to a very specific frequency of interaction** (figure 3), and these frequencies are remarkably consistent across media [66]"
- 図 2 の層(本文の並び): `EGO 1.5 intimates / 5 best friends / 15 good friends / 50 friends / 150 acquaintances / 500 known names / 1500 / 5000 = known faces`。最外層 5000 は顔認識の実験由来。
- 図 3(逐語): "Frequency per day with which people contacted individual members of each layer in their social network. Sample: **complete social networks of 251 UK and Belgian women**." 縦軸 0〜0.4/日、**最内層 5 が ≈0.4 回/日**で以降単調減。
- **努力配分(逐語・本 repo の行動契約 §5 の出所)**: "Approximately **40% of all social effort** (whether indexed as the frequency or duration of interaction) is directed to the **five individuals in the closest layer**, with another **20% devoted to the remaining 10 members of the second layer**. Thus, **60% of social time is devoted to just 15 people**." + "Comparable results have been reported from large-scale surveys in the UK [8] and in China [10]."
- **減衰(逐語)**: "a reduction in time devoted to a tie results in an inexorable decline in the emotional strength of a tie, **at least for friendships** (figure 6). Note, however, that **family ties appear to be quite robust** in the face of lack of opportunity to interact. Figure 6 suggests that this effect happens **within a matter of a few months**"
- **決裂率(逐語)**: "A similar effect will occur when there is a terminal breakdown in a relationship. These seem to occur with a frequency of **about 1% of relationships per year**"
- **激変時の入替(逐語・二次要約)**: "Saramäki et al. [145] reported a turnover of **approximately 40%** in the network membership of young adults over an 18-month period after they had moved away from their home town, **most of which occurred in the first nine months**."
- **ABM での層の稀少さ(逐語)**: 3,000 回超のラン・適応度関数の重みを系統的に振った結果 — "**multilevel social structures of the kind found in many primates, and especially those with the specific layer sizes of human social networks, were extremely rare (accounting for less than 1% of runs)**. They occurred only under a very limited set of circumstances, namely when a capacity for high investment in social time ... preferential social interaction strategies, high mortality risk and steep reproductive differentials between individuals coincided."

## 効く箇所(seam)

- 行動契約 §5 の「層容量 5/15/50/150」「会話相手選択の重み 内側 5 人 40%・次の 10 人 20%・残り 40%」の**出所**。
- **図 3(層別の 1 日あたり接触率)は registry.yaml の新しい現実アンカー候補**。関係・会話のアンカーが 1 本も無い穴(C10 材料 §6-2)を埋める。
- C10 のウォームアップ設計: **「相互作用に任せれば層が出る」とは期待できない**(<1% の run)。

## 「結論でなく機構として」の入れ方

「5/15/50/150 を層容量として上から与える」のは**結論の輸入**。機構として入れるなら **「時間が有限で、接触頻度が辺の強さを決める」** の 2 行だけを入れ、**層が出るかどうかを測る**。出なかったら「歪む場所」として宣言する(それが正しい使い方)。

## コスト/スケール含意

- 40%/20%/60% は**相手選択の確率分布**なので、辺の強さ順の上位 5/次 10 でサンプリングすれば実装費用ゼロ。
- 図 3 の「最内層 0.4 回/日」を満たすには、1 体あたり **5×0.4 + 10×0.13 + … ≈ 3〜4 会話/日**が要る。本 repo の c7-day-4 実測は **0.0021 会話/体/日** = **3 桁足りない**。

## 批判・限界

- **総説**であり一次データの論文ではない。図 3 の標本は **251 名の英・ベルギー女性**(男性・非欧州・都市の雑談は含まない)。
- **写しズレ注意**: 「1%/年」は**関係の決裂**の率であって「入替率」ではない。パターン台帳 B3 の「内層の年間入替 1〜4%/年」(Roy 2022)とは別の量。
- **フロア併記注意**: 「18 か月で 40% 入替」は Dunbar の要約。原典 Saramäki 2014 は **Jaccard 0.22±0.09(全網)/ 0.36±0.13(上位 20)**=もっと大きな入替。**要約でなく原典を引くこと**。
- Lindenfors et al. 2021 は「脳サイズからの 150 の導出」をベイズで否定している(v1 資産の記録・本メモでは未確認)。層サイズそのものの実証は独立に強いが、**導出の理屈は争われている**。

## 関連

[[relations__saramaki2014_social-signatures]] ・ [[relations__robertsdunbar2015_relationship-decay]] ・ [[relations__zhao2012_actr-dunbar-network]] ・ `../../design/v2-action-contract.md` §5 ・ `../v2-c10-initial-relations-research.md` §1-4
