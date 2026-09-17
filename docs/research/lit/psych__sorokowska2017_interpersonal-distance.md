# Sorokowska ほか 2017 — Preferred Interpersonal Distances: A Global Comparison

- リンク: https://doi.org/10.1177/0022022117698039 | 分野: 人格心理学 #13 / 会話分析・語用論 #15 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-17・サブが著者最終稿 PDF 36 頁を大学リポジトリから取得し `pymupdf` で抽出。Classifying social distance 節・Materials and methods・Procedure・Table 2 を確認)。**出版社版(SAGE)は未取得**・**親未確認**。Journal of Cross-Cultural Psychology 48(4):577-592, 2017。著者 40 名超。

## 主張(claim)

対人距離の選好は文化間で大きく違う。**42 か国 8,943 人**で「見知らぬ人・知人・親しい人」への選好距離を同一手続きで測り、個人属性(性別・年齢)と文化属性(平均気温など)で説明する。

## 機構(mechanism)— Hall の 3 区分をそのまま測る

- 「Based on the classical Halls's theory (1966), we measured three separate categories of preferred interpersonal distances – distance to (1) a stranger, (2) an acquaintance and (3) a close person.」
- 「These measures reflected the previously defined categories of interpersonal distance: (1) **social distance**; (2) **personal distance**; and (3) **intimate distance** (Hall, 1966), respectively.」
- **測り方**: 「Answers were given on a distance (**0-220 cm**) scale anchored by two human-like figures, labelled A for the left one and B for the right one (Fig. 1).」= 言語非依存の図形課題。
- **Hall 1966 の再掲**(Classifying social distance 節。**本論文による二次の記述**):
  「(1) public distance (**above 210 cm**) … (2) social distance, maintained during more formal interactions (**122-210 cm**, this distance precludes all but visual and auditory stimuli); (3) personal distance, maintained during interactions with friends (about **46 to 122 cm**) … (4) intimate distance … (**from 0 to 46 cm**)」

## 数値(出所つき)

- **標本**: 「Our study was comprised of **8,943 participants** (4,013 men, 4,887 women and 43 unidentifieds) inhabiting **53 study sites in 42 countries**.」(Participants 節・Table 1)
- **平均距離**(Table 2 の多水準モデル切片):
  - **社会距離(見知らぬ人)= 135.14 cm**
  - **個体距離(知人)= 91.72 cm**
  - **親密距離(親しい人)= 31.85 cm**
- **日本は 42 か国に含まれない**。本文中「Japan」の出現は参考文献 1 件(Sawada の日本心理学研究)のみ[実読による確認]。
- 予測因子: 社会距離は性別と国の平均気温(女性・寒い国ほど遠い)、個体距離は年齢と性別、親密距離は年齢と気温。

## 効く箇所(seam)

[C9 決定アジェンダ](../../design/v2-c9-geometry-agenda.md) **G7**(会話・傍受が届く範囲・d_talk 2 m)と [会話実装](../../design/v2-perception-contract.md) §3(傍受 r ≈ 2 m)。

## 「結論でなく機構として」の入れ方

1. **★ 借りる(G7 の裏づけ)**: **見知らぬ人への選好距離が 1.35 m**。**d_talk = 2 m はそれより 0.65 m 広い**ので、会話している二人の実距離をほぼ全部覆う = **偽陰性が出にくい側**の設定。知人なら 0.92 m でさらに内側。
2. **借りる**: **相手との関係で距離が変わる**という形。v2 は知人/他人を既に区別している(近接上位 k + 知人常掲)ので、**会話成立距離を関係で変える余地がある**(ただし決定項なので推奨はしない)。
3. **借りない**: 国別の値・気温との回帰。**日本のデータが無い**。
4. **注意(親要確認)**: **本論文が再掲する Hall の帯(社会距離 122-210 cm・公衆距離 210 cm 超)は、一般に流布する Hall 原典の帯(社会距離 4-12 ft = 1.2-3.6 m)と切り方が違う**。本論文の回答尺度上限が 220 cm であることと関係している可能性がある。**Hall 1966 の原典は本調査では未取得**。

## コスト/スケール含意

なし(定数の根拠としてのみ使う)。

## 批判・限界

- **選好距離であって実測距離ではない**。図形課題で「どれくらい離れていたいか」を答えさせている。**実際の会話で取る距離は測っていない**。
- **屋外・群衆の状況ではない**。混雑で強制的に近づく場合は範囲外。
- **日本が入っていない**。渋谷に当てるときは文化差の補正ができない。
- 回答尺度が **0-220 cm で打ち切り**。2 m を超える距離は原理的に測れていない。
- Hall 1966 の帯は**本論文の要約**であって原典の逐語ではない。

## 関連

[[crowd__bosina-weidmann2018_fd-generic-model]](同じ Hall 1966 を親密距離 0.15-0.20 m として使う実例)・[C9 答申](../v2-c9-position-attention-research.md) §1.5・§2-G
