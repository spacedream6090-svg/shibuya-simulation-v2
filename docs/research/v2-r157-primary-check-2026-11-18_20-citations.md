<!-- hdr:v1 | 等級: B−(第348 親の一次確認=末尾の表。主な数値の一部を原典で確かめた。残りは未確認) | 作成: 2026-11-21 | 範囲: 返事その 9(11-20)§5-7 R-157 11-18〜11-20 の文献の一次確認 -->
# R-157 11-18〜11-20 の壁打ちが根拠に挙げた文献の一次確認と、日本語の自由連想の基準データ(記録 2-77・2-78・2-80・2-81)

- **分野**: 認知科学(記憶・思考) #12 / 機械学習(潜在の推論・連想記憶) / 強化学習・エージェント / 都市モデル(住み替え) / 心理言語学(連想基準) | **重要度**: 発注文に記載なし(親が付ける)。材料にする所は [返事その 9(11-20)](../design/prompt-2026-11-20-reply9.md) §5-7 と、[壁打ちの記録](../reference/wallbounce-record-2026-11-02_05.md) 2-77・2-78・2-80・2-81
- **一次確認**: B−(第348 親の一次確認=末尾の表。主な数値の一部を原典で確かめた。残りは未確認)。筆者がこの回に読んだ出典は 32 本(◎ 11・○ 11・△ 10)。既存答申からの引用は R-41・R-45・R-88・R-103・R-135・R-140・R-146 と思考の頻度の錨のメモ(番号と節で引き、読み直していない)。読めなかったものは §5。
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-11-21・リサーチ役(Opus 5.5)。子サブは起動していない。作ったのは本書 1 本だけで、コード・台帳・設計書・INDEX は 1 バイトも変えていない。commit も git add もしていない。封印の層(holdout・test の層)には触れていない。発注文が開かないと定めた文書(IMPLEMENTED.md・build-report-C7*/C8*・G1 のバックテストの計画・パターン台帳)は開いていない。重み・データセットのファイルは取得していない(連想の基準データも、頁を読んだだけ)。作業の途中で利用の上限に 2 回当たり、親の指示で再開した。再開の後は、書いた分を節ごとに保存しながら進めた。
> **取り方の注**: 頁は WebSearch と WebFetch で読んだ。WebFetch は頁を小さなモデルに通して答えを返すので、引用は写しの段を 1 つ経ている(短い逐語の断片だけを頼み、長い文は要約として扱った)。要旨の多くは公開の索引(OpenAlex の `abstract_inverted_index`・Europe PMC の REST の `abstractText`)で読んだ。PDF は 2 本([S16]・[S26])で、WebFetch がリポの外の道具の結果の置き場に自動で残した写しを、システムの Python の pymupdf(`-I` で起動)で文字にして読んだ。写しも文字もリポの外にあり、リポにも data/ にも保存していない。curl と gh は使っていない。**発行元が断った論文を別の場所で読んだもの**(2-87 の決まりの 1 行ずつ):
> - Howard & Kahana 2002 [S16]: 発行元 Elsevier(ScienceDirect の robots.txt は 403=R-155 §5-1 U3)/読んだ場所=著者(Howard)の大学の個人の頁 `people.bu.edu/marc777/docs/`/robots.txt は 404(置いていない=制限なし)。サイトの利用規約の頁は見つけられず読んでいない/読んだ版=出版版の組版(「Copyright © 2001 by Academic Press」・31 頁)。
> - LWOW(Abramski ら)[S5]: 発行元 nature.com(Scientific Data)は robots で ClaudeBot を禁止(R-149 §12 U2・本書では開いていない)/読んだ場所=arXiv/robots.txt は `/html` を許す(Claude 向けの行は無い。冒頭の注は「無差別な自動の取得は不可」)。arXiv の利用規約の頁は別に読んでいない/読んだ版=arXiv v1(2024-12-02)。雑誌の版(2025)とは数字が違うことがある。
> - Coconut [S1]・Ramsauer [S2] は arXiv が最初の公開の場で、断った発行元は無い(Coconut は COLM 2025 採録と comments 欄にある)。
> **取り方の順の誤り 1 件**: Frontiers の JALEX の頁 [S32] を、robots.txt を読む前に読んだ。直後に robots.txt を読み、`User-agent: *` に `Allow: /` で Claude 向けの行が無いことを確かめた。以後の Frontiers の頁 [S14] は robots を読んだ後に読んだ。
> 等級: ◎=原典(または名のある二次の文献)の本文の頁を読んだ/○=要旨だけ読んだ(索引の要旨を含む)/△=検索の抜粋だけ。筆者の組み立ては【見立て】、根拠の無い置き方は【推測】と書く。**推薦は書かない**。決めるのはユーザー。
> 既存答申との関係(重ねない): Kinny & Georgeff 1991 は [R-41](v2-r41-cognitive-architecture-precedents.md) §2-1(原典・親確認)、Sutton, Precup & Singh 1999 は [R-45](v2-r45-action-activity-granularity-research.md) §1-1(著者公開の PDF・親確認)、Soar の chunking は [R-135](v2-r135-mind-modules-precedents.md) §2 b-2(◎)、SimMobility は [R-140](v2-r140-population-lod-simulation.md) §3-4(○)、McClelland ら 1995 は [R-146](v2-r146-sleep-consolidation-person-vector.md) §2-2(○)、Killingsworth & Gilbert 2010 は [R-88](v2-r88-llm-humanlikeness-deliberation-vision.md) の表 #22・B5 と [思考の頻度の錨のメモ](v2-thought-frequency-anchors-note.md) H4 を正とする。本書は値を再掲せず番号で引き、記録の文と合うかだけを足す。

## §0 要旨

1. 16 行のうち、記録の文と原典が合うのは Coconut・Baird ら・Daw ら・Memorizing Transformers・Sutton ら・LWOW の 6 本。数値まで原典の本文で確かめられたのは Coconut と LWOW(どちらも arXiv の版)。
2. Coconut の GSM8k は CoT 42.9% → Coconut 34.1%(表 1・arXiv v4)で、記録のとおり下がっている。全部の実験が学習済みの GPT-2 を多段の課程で学ばせ直したもの。ProntoQA と ProsQA では、連続の思考を使わず課程だけで学ばせた腕も 99.9%・95.5% に届く(表 1)【見立て: 伸びの多くは課程から来ている】。
3. 不随意の記憶の値は 2 本の論文を混ぜている。「1 日 2 回より多い・最も多い見積もり 5〜6 回・幅 3〜20」は Berntsen 1996 の日記の研究(14 人)の自己見積もりで、Krans ら 2015 の本文で確かめた。「意図した想起の 3 倍」と「ぼんやり・退屈・注意が散るとき」は Rasmussen & Berntsen 2011(デンマークの学部生 48 人・1 日・数取り器)。スマートフォンで記録した 2015 年の研究では差が出なかった(△)。
4. 「不満が溜まると住み替えを探す」形の出どころは ILUTE ではない。Wolpert 1965 と Brown & Moore 1970 の地理学の stress-threshold 模型(△)が出どころで、ILUTE の住宅市場の部品 HoMES(Rosenfield ら 2013)がこの「住まいの stress」の考えを使っている(本文は △・書誌と要旨は ○)。
5. LWOW は SWOW の 11,545 の刺激語を 3 つの LLM に 100 回ずつ答えさせた。異なる答えの数は人 116,640 に対し Llama3 105,367・Mistral 41,369・Haiku 15,275 だった。人の網の辺のうち LLM と共有するのは 13〜23%(表 1・表 3)。一方、意味のプライミングを模擬した効果量は 4 つとも 0.86〜0.87 でそろった。
6. 一部だけ合うもの・確かめられないもの(表 §2-0): Christoff ら 2016 は、要旨に「制約」の語が無い。強さの並びは検索の抜粋だけ(△)。Alderson-Day & Fernyhough 2015 は、「ストレスのとき展開する」の言い方が別の総説(Fernyhough & Borghi)にあり、2015 年の論文の中では確かめられない(△)。Ramsauer ら 2020 では、β は平均する型の数を決めるとあるが、「大きいと 1 つ・小さいと混ざる」の言い方は読めた範囲に無い。ほかに Howard & Kahana 2002(隣接効果を初めて詳しく示したのは Kahana 1996 で、大きさは図だけ)・Kinny & Georgeff(計画の費用 p の条件を落としている)・SimMobility と Director(「下が結果を返す」は読めた範囲に無い)・McClelland ら(「睡眠中」は R-146 の読みに無い)。
7. Bower 1981 の「証拠が混在する」は、気分状態依存については合う(1985 年の追試で出なかった・Ucros 1989 は条件で効果量が変わるとした)。ただし記録の E(今の気分が地形を傾ける)が当たるのは気分一致の方で、気分一致について後の総説の結論は読めていない。
8. 日本語の自由連想の基準で、自由に入手でき、利用の条件まで分かるものは見つからなかった。候補は 4 つある。梅本 1969(大学生 1,000 人・210 語・本)/JWAD-V1(2,099 項目・104,800 反応・1 項目に最大 50 人)/連想概念辞書(反応の種類を指定する課題で、厳密な自由連想ではない)/SWOW-JP(2020 秋開始。反応 16.5 万超・4,000 人超は △。公開と条件は確かめられない。smallworldofwords.org は robots で ClaudeBot を禁止)。
9. Killingsworth & Gilbert の 46.9% は R-88 #22(○)と錨のメモ H4(二次)にある。ただし R-88 が本文を読んだのは Fermat's Library の注釈版(第三者のサイト)で、2-87 の決まりでは第三者の写しに当たるおそれがある(§5-2 の 2)。
10. 親に確かめてほしい数値は §6 の末尾。

## §1 問いと前提

### 1-1 問い(発注文)

1. 仕事 1: 記録 2-77・2-78・2-80・2-81 が引く文献 16 行について、記録の中での使われ方と原典を突き合わせる。§2。
2. 仕事 2: 日本語の自由連想の基準データの有無と、利用の条件。§3。
3. 範囲の外: 記録の決定(思考の流れ・連想の再現の形)の良し悪し・推薦・ここに挙げていない節の文献。

### 1-2 記録の中での使われ方(引用)

- **2-77**: 「Christoff ら 2016(Nature Reviews Neuroscience)思考は常に流れ、違いは意図的な制約と自動的な制約の強さ(夢で最も弱く・ぼんやりで少し強く・目的の思考で最も強い。強い自動の制約は反芻)=古典・本文は再読していない/Alderson-Day & Fernyhough 2015(Psychological Bulletin)内なる言葉はふだん凝縮され、ストレスや問題にとらわれると話し言葉に近い形へ=同/Killingsworth & Gilbert 2010 の 46.9%(リポで確認済み)/Coconut(Hao ら 2024)=ProntoQA で CoT 98.8%・92.5 トークンに対し 99.8%・9.0 トークン、ProsQA で 77.5%→97.0%。ただし GSM8k では 42.9%→34.1% に下がり、GPT-2 を学ばせ直した結果(重みの加工=2-46 の了承が要る)。」
- **2-78**: 「根拠=ぼんやり考える思考は未来に向かいやすく、役割の 1 つが自分にとって大事な将来の目標の計画(Baird, Smallwood & Schooler 2011)」「(参考=不満が溜まったときの住み替えを扱う都市モデル。ILUTE 系としたが出典の確かめは未)」「時間の速さで層を分けて上が文脈・下が結果を返す(SimMobility・Hafner 2022 Director)/下の単位は始まり・中身・終わりの条件を持つまとまり(Sutton, Precup & Singh 1999 options=予定帳の項)/習慣と熟考は不確かさで切り替わる(Daw, Niv & Dayan 2005=2-29)/熟考の結果は習慣に写る(Soar の chunking=2-30 (c)・第 2 世代の蒸留)/長い意図の見直しやすさは環境の変わりやすさで変わる(Kinny & Georgeff 1991)。どれも古典で、本文は再読していない。」
- **2-80**: 「C=現代ホップフィールドネットワーク(Ramsauer ら 2020)… β が大きいと 1 つの記憶へ、小さいと混ざった準安定の状態。更新の規則は注意と同じ/D=相補的学習系(McClelland, McNaughton & O'Reilly 1995)。昼は速い記憶(A)、睡眠中の再生で遅い記憶(本人のベクトル)と地形を少しずつ書き換える/E=気分を記憶と一緒に記録し、今の気分が地形を傾ける(Bower 1981)。証拠が混在するので効きは 0 を含む腕で/B=経験を LLM の内部表現(key/value)のまま保存し注意で引く(Memorizing Transformers・Wu ら 2022)」「錨(11-20 の確かめ):不随意の自伝的記憶=日記の研究で参加者の見積もりは 1 日に 2 回より多く、最も多い見積もりは 5〜6 回(幅 3〜20)。数取り器で 1 日数えた研究では不随意の記憶は意図した想起の 3 倍で、ぼんやりしているとき・退屈なとき・注意が散っているときに多い(Rasmussen & Berntsen 2011)/想起の隣接効果(Howard & Kahana 2002)/ぼんやり考えている割合 46.9%」
- **2-81**: 「意味の連想(言葉のつながり。人の自由連想の基準 SWOW と比べた研究に LWOW=Abramski ら 2025)・入力の中の連想(注意の計算そのものが連想記憶=Ramsauer ら 2020)」「検証の候補=住民に連想語を出させ人の基準データと比べる(日本語の基準の有無は未調査・研究の題の候補)」

## §2 仕事 1: 一次確認

### 2-0 まとめの表

| # | 文献 | 記録の節 | 読めた範囲と等級(読んだ版) | 合うか | 記録が原典より強く言っている所・違い |
|---|---|---|---|---|---|
| 1 | Christoff ら 2016 | 2-77 | Europe PMC の要旨 ○ [S8]・大学の発表 ◎(二次)[S9]・並びは △ [S10] | 一部 | 「思考は常に流れる」は読めた範囲に無い。強さの並びは △ だけ。記録は並びから「創造的な思考」を落としている |
| 2 | Alderson-Day & Fernyhough 2015 | 2-77 | OpenAlex の要旨 ○ [S11]・別の総説の抜粋 △ [S12] | 確かめられない(2015 の論文の中では) | 「ストレスや問題で話し言葉に近い形へ」の言い方は Fernyhough & Borghi の総説の抜粋にある(△) |
| 3 | Coconut(Hao ら) | 2-77 | arXiv v4 の HTML ◎ [S1] | 合う | 数値は全部合う。課程だけの腕(連続の思考なし)も ProntoQA・ProsQA で高い(記録に無い) |
| 4 | Rasmussen & Berntsen 2011 ほか | 2-80 | 2011 の要旨 ○ [S13]・Krans ら 2015 の本文 ◎ [S14]・△ [S15] | 一部(値の出どころが 2 本) | 日記の見積もりは Berntsen 1996。3 倍は記録の方法で変わる(2015 で差なし・△) |
| 5 | Howard & Kahana 2002 | 2-80 | 著者の頁の出版版の PDF ◎ [S16] | 一部 | 隣接効果を初めて詳しく示したのは Kahana 1996。2002 は模型。大きさは図だけ |
| 6 | Ramsauer ら 2020 | 2-80・2-81 | arXiv v3 の HTML §1〜§4 ◎ [S2](付録は未読) | 一部 | 更新の規則=注意は合う。「β が大きいと 1 つ・小さいと混ざる」の言い方は読めた範囲に無い(β は平均する型の数を決める) |
| 7 | McClelland ら 1995 | 2-80 | R-146 §2-2(○・読み直していない) | 一部(R-146 の読みの範囲) | 「睡眠中の」は R-146 の要旨の読みに出てこない |
| 8 | Bower 1981 と後の見直し | 2-80 | 要旨 ○ [S17]・△ [S18] | 一部 | 「証拠が混在」は気分状態依存について合う。記録の E は気分一致に当たり、その後の結論は読めていない |
| 9 | Baird ら 2011 | 2-78 | Europe PMC の要旨 ○ [S19] | 合う | 未来向きの割合の値は要旨に無い |
| 10 | Sutton, Precup & Singh 1999 | 2-78 | R-45 §1-1(親確認) | 合う | — |
| 11 | Daw, Niv & Dayan 2005 | 2-78 | Europe PMC の要旨 ○ [S20] | 合う | 要旨は「習慣」の語でなく線条体と前頭前野の 2 つの系の競合 |
| 12 | Kinny & Georgeff 1991 | 2-78 | R-41 §2-1(原典・親確認) | 一部 | 計画の費用 p の条件と、「見直しを賢く反応させると、どこでも最適」の結論を落としている |
| 13 | ILUTE 系の住み替え | 2-78 | HoMES の書誌と要旨 ○ [S21]・本文と古典は △ [S22][S23] | 合わない(出典の帰属) | 閾値の形の出どころは Wolpert 1965・Brown & Moore 1970 |
| 14 | LWOW と SWOW | 2-81 | LWOW arXiv v1 ◎ [S5]・SWOW の要旨 ○ [S6] | 合う | — |
| 15 | Killingsworth & Gilbert 2010 | 2-77・2-80 | 既存答申を引くだけ | 既存のとおり | R-88 の読み方の経路(§5-2 の 2) |
| 16 | Memorizing Transformers・Director・Soar・SimMobility | 2-78・2-80 | arXiv の要旨 ○ [S3][S4]・R-135・R-140 | Memorizing は合う/他は一部 | 「上が文脈・下が結果を返す」は読めた範囲に無い |

### 2-1 Christoff ら 2016

- **書誌**: Christoff K., Irving Z.C., Fox K.C.R., Spreng R.N., Andrews-Hanna J.R.「Mind-wandering as spontaneous thought: a dynamic framework」Nature Reviews Neuroscience 17(11): 718–731(2016)。DOI 10.1038/nrn.2016.113。PMID 27654862。閉じた出版(OpenAlex の is_oa=false・保管庫の写しなし)。
- **読めた範囲**: Europe PMC の要旨(○)[S8]。OpenAlex には要旨が無い。発行元(nature.com)は robots で ClaudeBot を禁止(R-149 §12 U2)。同じ著者らの章を置く PhilArchive も robots で ClaudeBot を禁止。検索に出た第三者のサイトの PDF の写しは開いていない(§5-1)。大学(UBC)の発表の頁(2016-10-31)を読んだ(◎・二次)[S9]。
- **原典の言っていること**: 要旨(○)「We propose that mind-wandering is best understood as a member of a family of spontaneous-thought phenomena」「that also includes creative thought and dreaming.」要旨に「rumination」「automatic」「deliberate」「constraints」の語は無い(Europe PMC の要旨。雑誌の頁の要旨とは違うことがある)。大学の発表(◎)「two types of constraints—one automatic and the other deliberate—can curtail this spontaneous movement of thoughts」「thoughts flow freely when the mind is in its default state—mind-wandering」。
- **強さの並び(△)[S10]**: 検索の抜粋に「deliberate constraints are minimal during dreaming, tend to increase somewhat during mind-wandering, increase further during creative thinking and are strongest during goal-directed thought」と「Rumination and obsessive thought … are characterized by strong automatic constraints」がある(雑誌の頁の要点の欄と、別の総説の記述の抜粋)。本文の図 1 は読んでいない。
- **合うか**: 一部。2 種類の制約で思考の動きを分ける骨組みは大学の発表で合う。並び(夢<ぼんやり<創造<目的)と反芻の位置は △ の範囲で合う。
- **記録が強く言っている所**: 「思考は常に流れ」は、読めた範囲の文(「既定の状態では思考が自由に流れる」)より強い。記録は並びから「創造的な思考」を落としている。

### 2-2 Alderson-Day & Fernyhough 2015

- **書誌**: Alderson-Day B., Fernyhough C.「Inner speech: Development, cognitive functions, phenomenology, and neurobiology」Psychological Bulletin 141(5): 931–965(2015)。DOI 10.1037/bul0000021。PMCID PMC4538954。出版版は CC BY(OpenAlex)。
- **読めた範囲**: OpenAlex の要旨(○)[S11]。PMC の頁は、別の論文で確認の画面だけが返ったので読んでいない(§5-1 U4)。Durham の大学の保管庫と APA(psycnet)は robots で ClaudeBot を禁止。
- **原典の言っていること(要旨・○)**: 内なる言葉の発達・認知の働き・現象・神経の総説で、「approaches to the scientific study of inner speech have remained diffuse and largely unintegrated」。最後に、発達と認知と心理言語学に基づく多成分の模型を出す。要旨に「condensed」「stress」の語は無い。
- **別の出典(△)[S12]**: 検索の抜粋では、Fernyhough & Borghi の TiCS の総説「Inner speech as language process and cognitive tool」(年と巻は確かめていない・Durham の保管庫で読めない)が「IS can transition flexibly between condensed and expanded forms and, under conditions of stress and cognitive challenge, be re-externalized as overt self-talk」と書く。「expanded」「condensed」の語を Alderson-Day & Fernyhough 2015 が持ち込んだとする Frontiers 2020 の記述の抜粋もある(△)。
- **合うか**: 2015 の論文の中では確かめられない。記録の中身は、同じ著者の系統の別の総説の抜粋とは合う。

### 2-3 Coconut(Hao ら)

- **書誌**: Hao S., Sukhbaatar S., Su D., Li X., Hu Z., Weston J., Tian Y.「Training Large Language Models to Reason in a Continuous Latent Space」arXiv 2412.06769(v1 2024-12-09・v2 2024-12-11・v3 2025-11-03・v4 2026-08-23)。comments 欄「Accepted to COLM 2025」。
- **読めた範囲**: arXiv の HTML(v4)の本文(◎)[S1]。v1〜v3 の数値とは比べていない。
- **表 1(v4)**: 正答率%(トークン数)。

| 方法 | GSM8k | ProntoQA | ProsQA |
|---|---|---|---|
| CoT | 42.9 ± 0.2(25.0) | 98.8 ± 0.8(92.5) | 77.5 ± 1.9(49.4) |
| No-CoT | 16.5 ± 0.5(2.2) | 93.8 ± 0.7(3.0) | 76.7 ± 1.0(8.2) |
| iCoT | 30.0*(2.2) | 99.8 ± 0.3(3.0) | 98.2 ± 0.3(8.2) |
| Pause Token | 16.4 ± 1.8(2.2) | 77.7 ± 21.0(3.0) | 75.9 ± 0.7(8.2) |
| Coconut | 34.1 ± 1.5(8.2) | 99.8 ± 0.2(9.0) | 97.0 ± 0.3(14.2) |
| 課程なし | 14.4 ± 0.8(8.2) | 52.4 ± 0.4(9.0) | 76.1 ± 0.2(14.2) |
| 思考なし(課程だけ) | 21.6 ± 0.5(2.3) | 99.9 ± 0.1(3.0) | 95.5 ± 1.1(8.2) |
| 休止の記号を思考に | 24.1 ± 0.7(2.2) | 100.0 ± 0.1(3.0) | 96.6 ± 0.8(8.2) |

  *iCoT の GSM8k は Deng ら 2024 の値(著者は回し直していない)。
- **学ばせ方**: 「We use a pre-trained GPT-2 model as the base model for all experiments.」言葉の CoT のデータで、段 k で最初の k 歩を k×c の連続の思考に置き換える多段の課程(GSM8k は c=2、ProntoQA・ProsQA は c=1)。付録 C.2 で Llama 3.2-3B(No-CoT 26.0 → Coconut 31.7)と Llama 3-8B(42.2 → 43.6)も試し、伸びは GPT-2 より小さかった(CoT の値は報告なし)。§5.3「Although Coconut does not surpass CoT on GSM8k, it offers a superior trade-off between reasoning efficiency and accuracy」。
- **合うか**: 合う(98.8%・92.5/99.8%・9.0/77.5%→97.0%/42.9%→34.1%/GPT-2 の学ばせ直し)。
- **記録に無い点**: 連続の思考を使わず課程だけで学ばせた腕も ProntoQA 99.9%・ProsQA 95.5% に届く。休止の記号を思考の代わりにした腕も 100.0%・96.6%。【見立て】この 2 つの課題では、伸びの多くが「連続の思考」より課程から来ている。GSM8k では、Coconut 34.1% と課程だけの腕 21.6% の差が大きい。

### 2-4 不随意の自伝的記憶の頻度(Rasmussen & Berntsen 2011 ほか)

値ごとの出どころを分ける。

| 記録の値 | 出どころ | 読めた範囲 | 中身 |
|---|---|---|---|
| 1 日に 2 回より多い・最も多い見積もり 5〜6 回・幅 3〜20 | **Berntsen 1996**(日記の研究。原典は未読) | Krans, de Bree & Moulds 2015 の序論の本文 ◎ [S14] | 「Berntsen (8) asked 14 participants to record 50 involuntary memories with a maximum of 2 memories per day.」日記とは別に、ふつうの日の回数を見積もらせた=「more than two involuntary memories per day」「with five or six involuntary memories per day being the most typical estimate (range 3–20).」(自己の見積もりで、数えた値ではない) |
| 意図した想起の 3 倍 | **Rasmussen & Berntsen 2011** | OpenAlex の要旨 ○ [S13] | 「48 Danish undergraduates recorded their involuntary versus voluntary autobiographical memories during a day using a mechanical counter.」「Involuntary memories were reported three times as frequently as voluntary memories.」 |
| ぼんやり・退屈・注意が散るとき | **Rasmussen & Berntsen 2011** | 同上 ○ | 意図した想起に比べ「associated less with problem solving and social sharing and more with day dreaming, periods of boredom, no reasons for remembering and predominantly came to mind during unfocused attention.」 |
| (記録に無い・幅) | Rasmussen ら 2015・Rubin & Berntsen 2009 | 検索の抜粋 △ [S15] | スマートフォンで記録した 2015 年の研究では、不随意と意図した想起の頻度に差が無かった。Rubin & Berntsen 2009(Memory & Cognition 37(5): 679–688)は評定の調査で、頻度は同じくらい。後の論文は「at least as frequent」とまとめ、記録の手間で頻度の測り方が変わると書く(△) |

- **書誌**: Rasmussen A.S., Berntsen D.「The unpredictable past: Spontaneous autobiographical memories outnumber autobiographical memories retrieved strategically」Consciousness and Cognition 20(4): 1842–1846(2011)。DOI 10.1016/j.concog.2011.07.010。Krans J., de Bree J., Moulds M.L.「Involuntary Cognitions in Everyday Life: Exploration of Type, Quality, Content, and Function」Frontiers in Psychiatry 6(2015)・DOI 10.3389/fpsyt.2015.00007。Berntsen 1996 の書誌は Krans らの文献欄 (8) の部分が読めた範囲で切れており、確かめていない。
- **合うか**: 一部。値そのものは出どころの文と合う。ただし記録は 2 本(Berntsen 1996 の見積もりと Rasmussen & Berntsen 2011 の数え)を 1 つの括弧にまとめている。BPS の Psychologist の記事は Berntsen 1996 を「3〜5 回」と言い換えている(△)。
- **記録が強く言っている所**: 「3 倍」は 48 人・1 日・数取り器での値で、記録の方法を変えた 2015 年の研究では差が出なかった(△)。錨にするなら、測り方で値が動く幅を一緒に持つ必要がある【見立て】。

### 2-5 Howard & Kahana 2002

- **書誌**: Howard M.W., Kahana M.J.「A Distributed Representation of Temporal Context」Journal of Mathematical Psychology 46(3): 269–299(2002)。DOI 10.1006/jmps.2001.1388。
- **読めた範囲**: 著者の頁の PDF(出版版の組版・31 頁)の §1 を pymupdf で文字にして読んだ(◎)[S16]。
- **原典の言っていること**: 要旨「The principles of recency and contiguity are two cornerstones of the theoretical and empirical analysis of human memory.」「TCM uses retrieval of prior contextual states to drive contextual drift. In TCM, retrieved context is an inherently asymmetric retrieval cue.」「TCM can simultaneously explain recency and contiguity effects across time scales.」§1.1「This tendency, which we refer to as the lag-recency effect, illustrates the principle of contiguity.」「the lag-recency effect was first detailed by Kahana (1996)」。CRP は「peaked in the middle around lag zero」「asymmetric, with a greater probability of making recalls in the forward, rather than backward direction (see Fig. 1)」。§1.2: 項目の間に 16 秒の難しい計算の妨害を挟んでも隣接効果は出る(Howard & Kahana 1999)。CRP の形は項目の間を大きく離しても目に見えては変わらない(ほぼ尺度に依らない)。
- **主な数値**: 本文に CRP の値は無い。大きさは図 1(Murdock 1962 の LL=20・30・40 の条件・Murdock & Okada 1970・Murdock & Metcalfe 1978 の CRP の曲線。Kahana 1996 からの再掲)にしかない。
- **合うか**: 一部。隣接効果の中身(近い位置の項目が続けて思い出される・前向きが多い・時間の尺度に依らない)は合う。効果を初めて詳しく示したのは Kahana 1996 で、2002 は説明の模型(時間文脈模型 TCM)である。
- **記録が強く言っている所**: 無い。錨に使う大きさの値は、この論文の本文からは取れない(図か Kahana 1996 が要る)。

### 2-6 Ramsauer ら 2020

- **書誌**: Ramsauer H. ほか 16 名「Hopfield Networks is All You Need」arXiv 2008.02217(v1 2020-07-16・v2 2020-12-22・v3 2021-04-28)。arXiv の頁に雑誌・会議の欄は無い(ICLR 2021 は確かめていない)。
- **読めた範囲**: arXiv の HTML(v3)の §1〜§4(◎)[S2]。付録(A.1〜A.6)と文献欄は頁が切れて読んでいない。
- **原典の言っていること**: 式(3)「ξnew = X p = X softmax(β Xᵀ ξ)」。β=1/√dk で transformer の注意と同じ(式 10)。要旨「The new update rule is equivalent to the attention mechanism used in transformers.」固定点は 3 種=全部の型の平均の 1 つの固定点・一部の型の平均の準安定の状態・1 つの型の固定点(要旨・§2・§4)。§2 では、どれになるかを型どうしの離れ方 Δ で書く(よく離れた型は 1 つの型の固定点、離れていない型は全体の平均、似た型の部分集合は準安定)。§3「The variable β controls over how many patterns is averaged.」「variable β to determine the kind of fixed points such as the size of metastable states.」多くの場合 1 回の更新で取り出す(要旨・定理 4)。
- **合うか**: 一部。「更新の規則は注意と同じ」は合う。「β が大きいと 1 つ・小さいと混ざった準安定」の言い方は §1〜§4 に無い(「large β」「small β」の語も無い)。原典は、固定点の種類を型の離れ方 Δ と β の両方で書く。【見立て】softmax の形から、β を大きくすると平均する型が減る向きは読み取れる。2-81 の「注意の計算そのものが連想記憶」は要旨と合う。

### 2-7 McClelland, McNaughton & O'Reilly 1995

- **書誌**: Psychological Review 102(3): 419–457。DOI 10.1037/0033-295X.102.3.419(R-146 [S30])。
- **読めた範囲**: 本書では読んでいない。R-146 §2-2 の要旨の読み(○)を引く: 新しい記憶はまず海馬の系で符号化され、海馬が新皮質で再現し、新皮質のシナプスは再現ごとに少しだけ変わる。新しい記憶を古い記憶と交互に学ぶときだけ共通の構造を取り出せる。
- **合うか**: 一部(R-146 の読みの範囲)。「速い記憶と遅い記憶・再生で少しずつ書き換える」は合う。記録の「睡眠中の」再生は、R-146 §2-2 の要旨の読みには出てこない(確かめられない)。

### 2-8 Bower 1981 と後の見直し

- **書誌と読めた範囲**: Bower G.H.「Mood and memory」American Psychologist 36(2): 129–148(1981)・DOI 10.1037/0003-066X.36.2.129/Blaney P.H.「Affect and memory: A review」Psychological Bulletin 99(2): 229–246(1986)・DOI 10.1037/0033-2909.99.2.229/Ucros C.G.「Mood state-dependent memory: A meta-analysis」Cognition & Emotion 3(2): 139–169(1989)・DOI 10.1080/02699938908408077。どれも OpenAlex の要旨(○)[S17]。Blaney の要旨は索引の中で途中で切れていた。
- **Bower 1981(○)**: 催眠で誘った楽しい・悲しい気分で、「mood-state-dependent memory in recall of word lists, personal experiences recorded in a daily diary」と、気分一致「people recalled a greater percentage of those experiences that were affectively congruent with the mood they were in」を報告。「an emotion serves as a memory unit that can enter into associations with coincident events」と連想の網で説明。
- **Blaney 1986(○・途中まで)**: 「Two classes of effects—state dependence and mood congruence—are examined.」結論の文は読めていない。
- **Ucros 1989(○)**: 1975〜1985 の気分状態依存の研究のメタ分析。統合した効果量の値は要旨に無い。「Effect sizes are shown to vary systematically as a function of several variables.」肯定の気分で多く出る。実生活の出来事を材料にした研究で最も強い。説明の軸は「実験の現実らしさ」と「要求への感度」が競う。
- **△ [S18]**: Bower & Mayer 1985(Bulletin of the Psychonomic Society 23: 39–42)は Bower ら 1978 の実験 3 の追試で気分依存が出ず、「unreliable phenomenon in the laboratory」とした。Bower & Mayer 1989(Journal of Social Behavior and Personality 4: 121–156)は「impasse」「muddled scene」と書いたとされる。ただしその引用の頁を 165–166 とする抜粋があり、雑誌の頁 121–156 と合わない(確かめられない)。Eich 1995(Psychological Science 6(2): 67–75)は、状態依存が出る条件(内から作った出来事か・気分が強く本物か・快と覚醒の 2 次元)を論じる。
- **合うか**: 一部。「証拠が混在する」は、気分状態依存(覚えた時と思い出す時の気分が同じだと思い出しやすい)については、原典の範囲で合う。記録 2-80 の E(今の気分が地形を傾ける)が当たるのは気分一致(今の気分に合う中身を思い出しやすい)の方で、Bower 1981 の要旨にはある。気分一致について後の総説が何と言うかは読めていない(Blaney の結論の文・Matt ら 1992 のメタ分析は未読)。

### 2-9 Baird, Smallwood & Schooler 2011

- **書誌**: 「Back to the future: Autobiographical planning and the functionality of mind-wandering」Consciousness and Cognition 20(4): 1604–1611(2011)。DOI 10.1016/j.concog.2011.08.007。PMID 21917482。
- **読めた範囲**: Europe PMC の要旨(○)[S19]。R-103 #26 は △ だった。
- **原典の言っていること**: 「one potential function of spontaneous thought is to plan and anticipate personally relevant future goals, a process referred to as autobiographical planning」「The results confirm that the content of mind-wandering is predominantly future-focused」「individuals with high working memory capacity are more likely to engage in prospective mind-wandering」「prospective mind-wandering frequently involves autobiographical planning」。
- **主な数値**: 要旨には「as much as half of human thought arises in a stimulus independent fashion」だけ。未来向きの割合と標本の数は無い。
- **合うか**: 合う(「役割の 1 つ」は原典の「one potential function」と同じ強さ)。

### 2-10 Sutton, Precup & Singh 1999

R-45 §1-1(著者公開の PDF・親確認)を引く: option は「a policy π」「a termination condition β」「an initiation set I」の 3 つから成る。記録の「始まり・中身・終わりの条件を持つまとまり」は合う。R-45 は、価値が下がれば割り込む方が終わりまで走らせるより悪くならない(定理 2)とも書いている。

### 2-11 Daw, Niv & Dayan 2005

- **書誌**: 「Uncertainty-based competition between prefrontal and dorsolateral striatal systems for behavioral control」Nature Neuroscience 8(12): 1704–1711(2005)。DOI 10.1038/nn1560。PMID 16286932。
- **読めた範囲**: Europe PMC の要旨(○)[S20]。R-103 #8 は △ だった。
- **原典の言っていること**: 「We identify a key trade-off pitting computational simplicity against the flexible and statistically efficient use of experience.」「The trade-off is realized in a competition between the dorsolateral striatal and prefrontal systems.」「We suggest a Bayesian principle of arbitration between them according to uncertainty, so each controller is deployed when it should be most accurate.」要旨に数値は無い。
- **合うか**: 合う。要旨は「習慣」の語を使わず、背外側線条体の系(計算が単純)と前頭前野の系(経験を柔軟に使う)の競合として書く。

### 2-12 Kinny & Georgeff 1991

R-41 §2-1(原典・親確認)を引く: 何歩ごとに計画を見直すかを変え(bold=見直さない・cautious=毎歩)、世界の変化の速さ γ と計画の費用 p で効き目を比べた。p=4 では bold が cautious より上。p を下げると、変化の速い世界で normal が bold を上回る。目標の消滅に反応する形に変えると、bold が「everywhere superior」になり、「the combination of commitment with intelligent reactive replanning was observed to result in optimal behaviour」。数値は図だけ。

- **合うか**: 一部。「見直しやすさの良し悪しは環境の変わりやすさで変わる」は合う。ただし原典では計画の費用 p も同じくらい効き、結論は「見直しの頻度」より「何に反応して見直すか」に置かれている。

### 2-13 ILUTE 系の「不満が溜まったときの住み替え」(出典の確かめ)

- **ILUTE の側**: ILUTE の住宅市場の部品 HoMES は Rosenfield A., Chingcuanco F., Miller E.J.「Agent-based Housing Market Microsimulation for Integrated Land Use, Transportation, Environment Model System」Procedia Computer Science 19: 841–846(2013)・DOI 10.1016/j.procs.2013.06.112。MIT の保管庫の書誌と要旨(○・出版版・CC BY-NC-ND 3.0)[S21] には「stress」の語が無い(要旨は、動くかの選択・場所の選択・住宅の評価・供給・価格を挙げる)。PDF は保管庫が 429(Retry-After 900 秒)を返したので、再試行していない(§5-1)。検索の抜粋(△)[S22] では、本文は住み替えを「residential stressors」で解釈し、今の住まいと他の候補の満足の差を stress と定義し、stress が時間とともに変わって押す力・引く力になる、と書く。結婚・出産・離婚が住み替えの見込みを上げ、Habib の mixed logit が要因の効きを量る、とも書く。Habib & Miller 2008 が ILUTE に入れる住み替えと探索の概念の手順を出した(△・Transportation 2010 の論文の引用の抜粋)。
- **閾値の形の出どころ(△)[S23]**: Wolpert J. 1965「Behavioral Aspects of the Decision to Migrate」Papers of the Regional Science Association 15: 159–169(場所の効用 place utility と、満足の基準 threshold reference point)と、Brown L.A., Moore E.G. 1970「The intraurban migration process: a perspective」Geografiska Annaler Series B 52: 1–13(動く以外の対応=改修なども並べる)。抜粋の文「The stress-threshold model (Wolpert, 1965; Brown and Moore, 1970) assumes that people do not consider moving unless they experience residential stress」「When residential stress exceeds a certain stress threshold, the household decides to seek a new residence.」後の実証に Speare 1974(Demography 11: 173–188・満足を間に置く変数)・Clark & Cadwallader 1973(Environment and Behavior 5: 29–41)がある(△)。
- **合うか**: 合わない(出典の帰属)。「溜まった不満で探し始める」形の出どころは、ILUTE ではなく 1960〜70 年代の地理学の stress-threshold 模型である。ILUTE(HoMES)はこの「住まいの stress」の考えを使う系統の 1 つ(△)。HoMES が閾値を数式で置いているかは読めていない。
- **記録との関係**: 記録の「数式の閾値ではなく本人の言葉の記録と判断で」は、記録自身の設計の言葉で、出典の中身ではない。

### 2-14 LWOW(Abramski ら 2025)と SWOW

- **書誌**: Abramski K., Improta R., Rossetti G., Stella M.「The "LLM World of Words" English free association norms generated by large language models」Scientific Data 12: 803(2025)・DOI 10.1038/s41597-025-05156-9(雑誌の版は検索の抜粋で書誌だけ)。arXiv 2412.01330(v1 2024-12-02)。前身は HHAI 2024 の「LLM-Generated Word Association Norms」(Mistral 7B instruct 0.1・△)。SWOW 英語は De Deyne S., Navarro D.J., Perfors A., Brysbaert M., Storms G.「The "Small World of Words" English word association norms for over 12,000 cue words」Behavior Research Methods 51(3): 987–1006・DOI 10.3758/s13428-018-1115-7(OpenAlex の要旨 ○)[S6]。
- **読めた範囲**: LWOW は arXiv v1 の HTML(◎)[S5]。雑誌の版(PMC)は確認の画面だけ返り、読めていない。
- **作り方(v1)**: 3 つの LLM(Mistral・Llama3・Haiku。版・温度は本文に無い)に、SWOW の刺激語 12,282(前処理の後 11,545)を、1 語に 3 つの答えで 100 回ずつ。指示文は SWOW の人への指示を真似た(本文は画像)。答えの総数は Mistral 3,268,206・Llama3 3,348,049・Haiku 3,403,644(表 1)。人のデータ(SWOW-EN.R100)は 3,148,578 の答え・欠け 9.1%。
- **主な結果(v1)**:
  - 異なる答えの数(表 1): 人 116,640・Llama3 105,367・Mistral 41,369・Haiku 15,275。
  - 網(表 2・WordNet で濾し、重み 1 の辺を除き、最大の連結成分): 人 24,308 結び目・317,344 辺・平均次数 26.1/Mistral 20,339・199,103・19.6/Llama3 38,987・546,866・28.1/Haiku 15,596・64,599・8.3。
  - 人との重なり(表 3): 人の結び目のうち共有=Mistral 59%・Llama3 48%・Haiku 57%。人の辺のうち共有=23%・13%・15%。LLM だけの辺=51%・81%・24%。
  - 意味のプライミングの模擬(Semantic Priming Project の語彙判断の 50 組・spreadr): 関連と無関連の活性の差の効果量=人 0.870・Mistral 0.859・Llama3 0.869・Haiku 0.866。活性と反応時間の Spearman=−0.626・−0.615・−0.614・−0.662(すべて p<0.001)。実験の反応時間の効果量は −0.87(図 2)。(表の番号は道具の答えで 5 と 7 が混ざっていたので、親が確かめる)
  - 性の固定観念(女性 5・男性 5 の語 × 形容詞 50): 女性の語の効果量=人 0.686・Mistral 0.323・Llama3 0.153・Haiku 0.669。男性の語=−0.695・−0.200・−0.722・−0.412。
- **許諾**: SWOW の加工済みの人のデータは、SWOW の許諾が「prohibits the distribution of modified material」なので配らない(脚注 1)。LWOW のデータとコードは GitHub(`LLMWorldOfWords/LWOW`)。データの許諾の文は本文に無い。smallworldofwords.org の robots.txt の注は、データの許諾を CC BY-NC-ND 3.0 とし、学習の用途は不可と書く(◎・robots の注だけ)[S7]。
- **合うか**: 合う(LLM の自由連想を SWOW と同じ刺激語で集めて比べた研究)。
- **【見立て】記録 2-81 にとっての含意**: 答えの種類の広さは LLM で大きく違い(人の 13%〜90%)、人の辺との重なりは 13〜23% と小さい。それでも網の上でのプライミングの模擬は 4 つともほぼ同じ値になった。比べる物差しを何にするかで、「人に似ている」の結論が変わる。

### 2-15 Killingsworth & Gilbert 2010 の 46.9%

本書では読み直していない。値は [R-88](v2-r88-llm-humanlikeness-deliberation-vision.md) の表 #22(○)・§1 の B5(2,250 人・標本の 46.9%)と、親検収(第 319「既知の値と一致」)、[思考の頻度の錨のメモ](v2-thought-frequency-anchors-note.md) H4(二次=Harvard Gazette と著者の発表。原文は 403 で未読)にある。測り方で 10〜60%(Seli 2018)・人で 2〜97%(Kane 2017)の幅は R-88 §2-1 と R-103 の表にある。**注意**: R-88 #22 が本文を読んだ経路は「Fermat's Library の注釈版本文(取得ツールの引用)。出版社ページは 403」と書かれている。2-87 の決まり(第三者の写しは不可・中身は答申から外す)に当たるかは親の判断(§5-2 の 2)。

### 2-16 余力の分(Memorizing Transformers・Director・Soar の chunking・SimMobility)

| 文献 | 読めた範囲 | 記録の文 | 合うか |
|---|---|---|---|
| Wu Y., Rabe M.N., Hutchins D., Szegedy C.「Memorizing Transformers」arXiv 2203.08913(v1 のみ・ICLR 2022 spotlight) | 要旨 ○ [S3] | 「経験を LLM の内部表現(key/value)のまま保存し注意で引く」 | 合う。「an approximate kNN lookup into a non-differentiable memory of recent (key, value) pairs improves language modeling」「the performance steadily improves when we increase the size of memory up to 262K tokens」。「大きさ・モデルを替えると使えない」は記録の推論で、要旨には無い |
| Hafner D., Lee K.-H., Fischer I., Abbeel P.「Deep Hierarchical Planning from Pixels」arXiv 2206.04114(v1 のみ。頁に会議の欄は無い) | 要旨 ○ [S4] | 「時間の速さで層を分けて上が文脈・下が結果を返す」 | 一部。「The high-level policy maximizes task and exploration rewards by selecting latent goals」「the low-level policy learns to achieve the goals」。上が何刻みごとに選ぶかと、「下が結果を返す」は要旨に無い |
| Soar の chunking | R-135 §2 b-2(◎) | 「熟考の結果は習慣に写る」 | 一部。chunking は substate の結果から規則を作り「converts deliberate, sequential reasoning into parallel rule firings」(R-135)。「習慣」は記録の言い換え。R-135 は「chunking requires that substate decisions be deterministic」も引いている |
| SimMobility(Adnan ら 2016) | R-140 §3-4(○) | 「時間の速さで層を分けて上が文脈・下が結果を返す」 | 一部。長期・中期・短期の 3 段で、段の間をデータが流れる(R-140)。どの向きに何が流れるかは R-140 で「中身はこの回は読めていない」 |

## §3 仕事 2: 日本語の自由連想の基準データ

### 3-1 日本語の自由連想の基準(見つかったもの)

**結論**: 自由に入手でき、利用の条件(ライセンス・研究利用・再配布)まで確かめられる日本語の自由連想の基準は、見つからなかった。下の 4 つは、どれも公開の形か条件が確かめられない。

| 名前 | 作った所と年 | 刺激語の数 | 答えた人の数と属性 | 公開の形と利用の条件 | 入手の場所(頁を読んだだけ) | 等級 |
|---|---|---|---|---|---|---|
| 梅本「連想基準表—大学生 1000 人の自由連想による」 | 梅本堯夫・東京大学出版会・1969(321 頁) | 210 語(Joyce & Srdanović 2008)。漢字 2 字の語とする記述あり(△) | 大学生 1,000 人 | 本(紙)。国立国会図書館の書誌にデジタルの形もあるとされる(△)が、利用の範囲は確かめていない。データの許諾の文は無い(本の著作物) | 国立国会図書館の書誌(検索の抜粋) | ◎(Joyce 2008 の記述)・△(書誌) |
| JWAD(Japanese Word Association Database)V1 | Joyce T.・多摩大学・2005〜(科研費の課題) | 目標 5,000 語。V1 は 2,099 項目 | 1 項目に最大 50 人(気付く は 100 人)。紙の質問紙。V1 の反応は 104,800 | 論文は「currently available JWAD Version 1」と書くが、配布の頁・条件は見つからなかった(確かめられない) | Joyce & Srdanović 2008 の 3.2 節 [S26] | ◎ |
| 連想概念辞書(Associative Concept Dictionary) | 岡本潤・石崎俊・慶應義塾大学 SFC・2001 | 1,656 名詞(Joyce 2008)。約 840 名詞とする記述もある(△) | 10 人・33,018 反応(Joyce 2008)。1 語に 50 人とする記述もある(△) | 反応の種類(上位・下位・部分・属性・類義・動作・環境の 7 つ)を指定する課題=厳密な自由連想ではない(Joyce 2008)。配布の頁・条件は見つからなかった | Joyce & Srdanović 2008 [S26]・言語処理学会の予稿の抜粋 [S27] | ◎(Joyce)・△ |
| SWOW-JP(Small World of Words 日本語版) | 東京大学 東京カレッジ(Telegina M.)・共同=Joyce T.(多摩大学)・De Deyne S.(メルボルン大学)。2020 秋に開始 | 見つからなかった | 反応 165,000 超・4,000 人超・平均 37 歳(SD 15)・全都道府県(東京 17%・神奈川 10%・愛知 5%)(△・バージニア大学の DH の要旨の抜粋。robots が 403 で頁は読めない)。属性は性・年齢・地域で分ける研究とある | 公開の有無と条件は確かめられない。東大の頁 3 つは公開に触れない。プロジェクトの頁(smallworldofwords.org/jp)は robots で ClaudeBot を禁止=読んでいない。SWOW 全体の robots の注はデータの許諾を CC BY-NC-ND 3.0・学習の用途は不可と書く | 東大の頁(英・日)[S24]・数値は抜粋 [S25]・robots の注 [S7] | ◎(東大の頁・数値なし)・△(数値) |

- 比べるための英語の基準: SWOW 英語は 12,000 を超える刺激語・1 語に複数の答え(要旨 ○)。参加者 9 万人超・1 語に最大 3 つの答えとする記述がある(△)。
- 検索の抜粋(△)には、Miron & Wolfe 1964 の 12 言語の比べで日本語の連想が最も型どおり(答えの一致が最も高い)だった、という SWOW-JP の要旨の記述がある。

### 3-2 近いもの(自由連想ではない日本語の基準)

| 名前 | 作った所と年 | 中身 | 数 | 公開の形と条件 | 等級 |
|---|---|---|---|---|---|
| 幼児・児童の連想語彙表(国立国語研究所報告 69) | 国立国語研究所・1981(東京書籍)・DOI 10.15084/00001260 | 分類の連想(14 の分類=動物・乗り物ほか)と頭の音の連想(67 音)。語を刺激にした自由連想ではない。東京と鹿児島(甑島)で調査 | 子どもの人数は頁に無い | 国語研の保管庫で PDF が公開(2017-06-09)。許諾の欄は空 [S29] | ◎(書誌) |
| JWSAN(Japanese Word Similarity and Association Norm) | Inohara K.・Utsumi A.・Language Resources and Evaluation(2021)・DOI 10.1007/s10579-021-09543-7 | 語の組の「似ている」と「連想する」の評定 | 2,145 組・名詞・動詞・形容詞・日本語を母語とする 6,450 人(年齢と性をそろえた)(△) | 論文は著者の権利の表示(△)。データの配布の頁と条件は確かめられない(検索の道具が知識から挙げた頁は接続できなかった・§5-1) [S30] | △ |
| JWSD(日本語の単語の類似度のデータセット) | Sakaizawa Y.・Komachi M.・LREC 2018・arXiv 1703.05916 | 単語の組の類似度。いろいろな品詞と珍しい語を含む | 要旨に組の数・評定者の数は無い | arXiv の論文は CC BY-SA 4.0。データの置き場と許諾は要旨に無い(GitHub の置き場は △) [S31] | ○ |
| JALEX(日本語の語彙判断のデータベース) | Ota N.・Mochizuki M.・Frontiers in Language Sciences 3(2025-01-13 公開)・DOI 10.3389/flang.2024.1506509 | 語彙判断(語か語でないか)の反応時間 | 5,736 語・1,652 人(男 1,226・女 407・平均 51.07 歳)・1 語に約 43 人・2024-05-20〜21 に収集 | 論文は CC BY。データは OSF(osf.io/qr2sg)。データそのものの許諾の文は論文に無い [S32] | ◎ |

- 調べていないもの: 単語の親密度・心像性などの基準(NTT の「日本語の語彙特性」ほか)。この回は探していない(空欄)。

## §4 空欄(見つからなかったもの・確かめられなかったもの)

1. Christoff ら 2016 の本文(図 1 の 2 軸の置き方)。雑誌の頁と著者らの章の置き場が robots で禁止。
2. Alderson-Day & Fernyhough 2015 の本文で、「ストレスや問題のとき展開する」を書く箇所。
3. Berntsen 1996 の原典(書誌・見積もりの表)。値は Krans ら 2015 の記述だけ。
4. Howard & Kahana 2002・Kahana 1996 の CRP の数値(図だけ)。
5. Ramsauer ら 2020 の付録 A.6(β と固定点の種類の細部)。
6. Bower 1981 以後の、気分一致の効果についての総説・メタ分析の結論(Blaney 1986 の結論の文・Matt ら 1992)。
7. HoMES(Rosenfield ら 2013)の本文で stress を閾値で置くか。Habib & Miller 2008 の原典。
8. SWOW-JP の刺激語の数・公開の有無・利用の条件。JWAD と連想概念辞書の配布の条件。
9. LWOW の雑誌の版(2025)と arXiv v1 の数値の違い。

## §5 読めなかったもの

### 5-1 断られた頁・開かなかった頁

| # | 何が | 理由 | 本書への影響 |
|---|---|---|---|
| U1 | nature.com(Christoff 2016・Daw 2005・LWOW の雑誌の版) | robots が ClaudeBot を禁止(R-149 §12 U2 で確かめ済み)。開いていない | 要旨(○)と arXiv の版で代えた |
| U2 | PhilArchive(Christoff らの章「The Neuroscience of Spontaneous Thought」) | robots.txt が ClaudeBot・anthropic-ai・Claude-Web を `Disallow: /` | 読んでいない |
| U3 | 第三者のサイトの Christoff 2016 の PDF の写し(検索に出た個人のブログの置き場) | 第三者の写し(2-87 の (2))。開いていない | — |
| U4 | PMC(LWOW の PMC12084308) | ブラウザの確認の画面(reCAPTCHA)だけが返った。再試行せず、Europe PMC の本文・Pisa 大学の保管庫の写しにも回っていない。同じ理由で Alderson-Day 2015 の PMC の頁も開いていない | LWOW は arXiv v1、Alderson-Day は要旨 |
| U5 | Durham の大学の保管庫(Alderson-Day 2015・Fernyhough & Borghi) | robots.txt が ClaudeBot を `Disallow: /` | 要旨と抜粋(△) |
| U6 | psycnet.apa.org(APA) | robots.txt が ClaudeBot を `Disallow: /`(`User-agent: *` も `Disallow: /`) | 要旨だけ |
| U7 | smallworldofwords.org(SWOW と SWOW-JP の頁・データの条件) | robots.txt が ClaudeBot・anthropic-ai・Claude-Web を `Disallow: /`。robots.txt の注だけ読んだ | SWOW-JP の公開と条件は確かめられない |
| U8 | dh-abstracts.library.virginia.edu(SWOW-JP の DH の要旨) | robots.txt が 403 | 数値は検索の抜粋(△) |
| U9 | assets.cambridge.org(Berntsen 2009 の本の抜粋) | robots.txt が 403 | 読んでいない |
| U10 | pure.au.dk(Rasmussen & Berntsen 2011 の出版版の PDF) | robots.txt の要求が別のドメイン(medarbejdere.au.dk)へ転送された。転送先は追っていない | 要旨(○)だけ |
| U11 | dspace.mit.edu の PDF(Rosenfield ら 2013) | 429(Retry-After 900 秒)。再試行していない | 書誌と要旨(○)・本文は △ |
| U12 | memory.psych.upenn.edu(Kahana の研究室) | 接続拒否(ECONNREFUSED) | 著者(Howard)の頁で読んだ |
| U13 | utm.inf.uec.ac.jp(JWSAN の配布の頁とされる URL) | 接続拒否(ECONNREFUSED)。この URL は検索の道具が自分の知識から挙げたもので、正規の頁かも確かめていない | JWSAN の配布と条件は確かめられない |
| U14 | link.springer.com(JWSAN・Rubin & Berntsen 2009・Wolpert 1965 ほか) | robots が ClaudeBot を禁止(R-155 §5-1 U7)。開いていない | 抜粋(△) |
| U15 | www.u-tokyo.ac.jp の日本語の頁 | 1 回目は ECONNRESET(断りではない)。2 回目で読めた | — |

### 5-2 取り方で迷った所(親に判断してほしい)

1. **Frontiers の頁を robots を読む前に読んだ**(JALEX [S32])。読んだ直後に robots.txt を読み、許されていたことを確かめた。中身は本書に入れている。
2. **R-88 の Killingsworth & Gilbert の読みの経路**: R-88 の表 #22 は「Fermat's Library の注釈版本文」で読んだと書く。2-87 の決まりの (2)(第三者のサイトの写しは不可・中身は答申から外す)に当たるかは、親の判断。本書は R-88 を引くだけで、その頁は開いていない。46.9% は錨のメモ H4 の二次(Harvard Gazette)でも同じ値。
3. **著者の頁の規約**: Howard & Kahana [S16] の people.bu.edu は robots.txt を置いていない(404)。サイトの利用規約の頁は見つけられず読んでいない。2-87 の条件の「規約を先に読む」を満たしたかは、親の判断。
4. **検索の道具の知識による補い**: 検索の道具の要約が「Berntsen 1996 は 3〜5 回・ほかに 20 回超」「JWSAN の置き場の URL」を自分の知識として足した。前者は使っていない(本書の値は Krans ら 2015 の本文の文)。後者は接続できず使っていない。

## §6 出典の表

| # | 出典 | URL | 読んだ範囲 | 等級 |
|---|---|---|---|---|
| S1 | Hao ら「Training Large Language Models to Reason in a Continuous Latent Space」arXiv 2412.06769 v4 | https://arxiv.org/abs/2412.06769 | HTML の本文(表 1・§5.3・付録 C.2)と abs の頁 | ◎ |
| S2 | Ramsauer ら「Hopfield Networks is All You Need」arXiv 2008.02217 v3 | https://arxiv.org/abs/2008.02217 | HTML の §1〜§4(付録は切れて未読)と abs の頁 | ◎ |
| S3 | Wu ら「Memorizing Transformers」arXiv 2203.08913 v1 | https://arxiv.org/abs/2203.08913 | abs の頁の要旨 | ○ |
| S4 | Hafner ら「Deep Hierarchical Planning from Pixels」arXiv 2206.04114 v1 | https://arxiv.org/abs/2206.04114 | abs の頁の要旨 | ○ |
| S5 | Abramski ら「The "LLM World of Words" English free association norms generated by large language models」arXiv 2412.01330 v1 | https://arxiv.org/abs/2412.01330 | HTML の本文(表 1〜3・検証・使い方の注・データの記録) | ◎ |
| S6 | De Deyne ら「The "Small World of Words" English word association norms for over 12,000 cue words」BRM 51(3): 987–1006 | https://doi.org/10.3758/s13428-018-1115-7 | OpenAlex の要旨と書誌 | ○ |
| S7 | smallworldofwords.org の robots.txt | https://smallworldofwords.org/robots.txt | robots の行と注(データの許諾・学習の不可) | ◎(robots だけ) |
| S8 | Christoff ら 2016 Nat Rev Neurosci 17(11): 718–731 | https://doi.org/10.1038/nrn.2016.113 | Europe PMC の要旨(OpenAlex は書誌だけ) | ○ |
| S9 | UBC 心理学科の発表「Understanding mind-wandering could shed light on mental illness」(2016-10-31) | https://psych.ubc.ca/news/understanding-mind-wandering-could-shed-light-on-mental-illness-ubc-research/ | 全文 | ◎(二次) |
| S10 | Christoff ら 2016 の制約の並びと反芻(雑誌の頁の要点の欄・別の総説の記述) | (検索の抜粋) | 検索の抜粋 | △ |
| S11 | Alderson-Day & Fernyhough 2015 Psychol Bull 141(5): 931–965 | https://doi.org/10.1037/bul0000021 | OpenAlex の要旨と書誌・場所の一覧 | ○ |
| S12 | Fernyhough & Borghi の TiCS の総説(凝縮と展開・ストレスと認知の負荷)・Frontiers 2020 の記述 | (検索の抜粋) | 検索の抜粋 | △ |
| S13 | Rasmussen & Berntsen 2011 Conscious Cogn 20(4): 1842–1846 | https://doi.org/10.1016/j.concog.2011.07.010 | OpenAlex の要旨と書誌 | ○ |
| S14 | Krans, de Bree & Moulds 2015 Front Psychiatry 6 | https://doi.org/10.3389/fpsyt.2015.00007 | 本文の序論(先頭 10 万字) | ◎ |
| S15 | Rubin & Berntsen 2009・Rasmussen ら 2015・BPS の Psychologist の記事・後の論文の記述 | (検索の抜粋) | 検索の抜粋 | △ |
| S16 | Howard & Kahana 2002 J Math Psychol 46(3): 269–299 | https://doi.org/10.1006/jmps.2001.1388(読んだ場所 https://people.bu.edu/marc777/docs/HowardKahana02-JMP.pdf) | 出版版の PDF の要旨・§1(pymupdf) | ◎ |
| S17 | Bower 1981 Am Psychol 36(2)・Blaney 1986 Psychol Bull 99(2)・Ucros 1989 Cogn Emot 3(2) | https://doi.org/10.1037/0003-066X.36.2.129 ・ https://doi.org/10.1037/0033-2909.99.2.229 ・ https://doi.org/10.1080/02699938908408077 | OpenAlex の要旨(Blaney は途中まで) | ○ |
| S18 | Bower & Mayer 1985・1989・Eich 1995 の記述 | (検索の抜粋) | 検索の抜粋 | △ |
| S19 | Baird, Smallwood & Schooler 2011 Conscious Cogn 20(4): 1604–1611 | https://doi.org/10.1016/j.concog.2011.08.007 | Europe PMC の要旨 | ○ |
| S20 | Daw, Niv & Dayan 2005 Nat Neurosci 8(12): 1704–1711 | https://doi.org/10.1038/nn1560 | Europe PMC の要旨 | ○ |
| S21 | Rosenfield, Chingcuanco & Miller 2013 Procedia Computer Science 19: 841–846 | https://doi.org/10.1016/j.procs.2013.06.112(書誌は https://dspace.mit.edu/handle/1721.1/90434) | MIT の保管庫の書誌と要旨 | ○ |
| S22 | HoMES の本文の stress の記述・Habib & Miller 2008 の記述 | (検索の抜粋) | 検索の抜粋 | △ |
| S23 | Wolpert 1965・Brown & Moore 1970・Speare 1974・Clark & Cadwallader 1973 の記述 | (検索の抜粋) | 検索の抜粋 | △ |
| S24 | 東京大学の SWOW-JP の頁(東京カレッジ・UTokyo Compass の英語と日本語) | https://www.tc.u-tokyo.ac.jp/en/research/5609 ・ https://www.u-tokyo.ac.jp/adm/uci/en/projects/dp/project_00022.html ・ https://www.u-tokyo.ac.jp/adm/uci/ja/projects/dp/project_00023.html | 全文 | ◎ |
| S25 | SWOW-JP の DH の要旨の数値(反応 16.5 万超・4,000 人超・年齢・県) | (検索の抜粋) | 検索の抜粋 | △ |
| S26 | Joyce T., Srdanović I.「Comparing Lexical Relationships Observed within Japanese Collocation Data and Japanese Word Association Norms」COGALEX 2008(Coling 2008 の workshop): 1–8 | https://aclanthology.org/W08-1901.pdf | PDF の本文(pymupdf・§2・§3.2・§4.1) | ◎ |
| S27 | 連想概念辞書の記述(言語処理学会の予稿ほか) | (検索の抜粋) | 検索の抜粋 | △ |
| S28 | 梅本 1969 の書誌と記述(国立国会図書館・阪大の紀要・村上 1984) | (検索の抜粋) | 検索の抜粋 | △ |
| S29 | 国立国語研究所報告 69「幼児・児童の連想語彙表」 | https://repository.ninjal.ac.jp/records/1276 | 保管庫の書誌と要旨 | ◎ |
| S30 | Inohara & Utsumi 2021 JWSAN(LRE) | https://doi.org/10.1007/s10579-021-09543-7 | 検索の抜粋 | △ |
| S31 | Sakaizawa & Komachi「Construction of a Japanese Word Similarity Dataset」arXiv 1703.05916 v2 | https://arxiv.org/abs/1703.05916 | abs の頁の要旨 | ○ |
| S32 | Ota & Mochizuki「JALEX: Japanese version of lexical decision database」Front Lang Sci 3 | https://doi.org/10.3389/flang.2024.1506509 | 本文(方法・データの置き場・許諾) | ◎ |

- 等級の数: ◎ 11(S1・S2・S5・S7・S9・S14・S16・S24・S26・S29・S32)・○ 11(S3・S4・S6・S8・S11・S13・S17・S19・S20・S21・S31)・△ 10(S10・S12・S15・S18・S22・S23・S25・S27・S28・S30)。
- robots.txt を読んだ場所(本文の出典に数えていない): arxiv.org・pmc.ncbi.nlm.nih.gov(と PMC の著作権の頁)・u-tokyo.ac.jp・tc.u-tokyo.ac.jp・aclanthology.org(404)・frontiersin.org・philarchive.org・psych.ubc.ca・durham-repository.worktribe.com・psycnet.apa.org・dspace.mit.edu・repository.ninjal.ac.jp・people.bu.edu(404)。
- **親に確かめてほしい数値**: ① Coconut の表 1(v4)=GSM8k CoT 42.9・Coconut 34.1・課程だけ 21.6/ProntoQA 98.8(92.5 トークン)・99.8(9.0)・課程だけ 99.9/ProsQA 77.5・97.0・課程だけ 95.5(◎)② Berntsen 1996 の 14 人・「2 回より多い・5〜6 回・幅 3〜20」(Krans ら 2015 の序論・◎)③ Rasmussen & Berntsen 2011 の 48 人・1 日・数取り器・3 倍(○)④ LWOW の表 1 と表 3=異なる答え 116,640/105,367/41,369/15,275・人の辺の共有 23%/13%/15%(arXiv v1・◎)⑤ JWAD-V1 の 2,099 項目・104,800 反応・最大 50 人、梅本 210 語・1,000 人、連想概念辞書 1,656 名詞・10 人・33,018 反応(Joyce & Srdanović 2008・◎)。

## 親の一次確認(第348・2026-11-21)

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| Coconut(Hao ら・arXiv 2412.06769)の表 1 と、土台のモデル | 親が web の道具で arXiv の HTML(v4)を読んだ(2026-11-21) | 合う。CoT は GSM8k 42.9%・25.0 トークン、Coconut は 34.1%・8.2。ProntoQA は 98.8%・92.5 対 99.8%・9.0。ProsQA は 77.5%・49.4 対 97.0%・14.2。連続の思考を使わない腕(w/o thought)は 21.6・99.9・95.5。土台は学習済みの GPT-2 で、課程を踏んで学ばせ直している |
| 断られた頁・取り方 | 答申の冒頭の注と §5 を読んだ | 読めなかった頁 15(robots・403・429)は、別の経路で読んでいないと書かれている。取り方の順の誤り 1 件(Frontiers の頁を robots を読む前に読んだ。直後に許されていると確かめた)が申告されている。著者の頁(robots.txt は 404)で読んだ 1 本は、利用規約の頁を見つけられなかったと書かれている=記録 2-87 の条件「その場所の robots と規約を先に読む」を満たすかは、報告 348 で聞く |
| R-88 が Killingsworth & Gilbert の本文を読んだ経路(第三者のサイト) | 答申の §5-2 を読んだ。R-88 の該当の行は、親は開いていない | 未確認。記録 2-87 の決まりに当たるおそれがあるので、扱いを報告 348 で聞く |
| そのほか(Berntsen 1996・Rasmussen & Berntsen 2011・LWOW・JWAD-V1 ほか) | 確かめていない | 未確認 |
