<!-- hdr:v1 | 等級: B(第346 親の一次確認=末尾の表) | 作成: 2026-11-09 | 範囲: 返事その 7(11-09)§6-2 の R-137 の追補・記録 2-41 -->
# R-137 の追補: 読めなかった原典(飽き・限界値定理・連れの効果・Gollwitzer 1999)をどこまで読めたか

- **分野**: 認知科学(記憶・習慣) #12 / 時間利用研究 #4 / 交通工学(活動ベース需要予測) #2 / ABM方法論 #21 | **重要度**: 発注文に記載なし([返事その 7(11-09)](../design/prompt-2026-11-09-reply7.md) §6-2。記録 [2-41](../reference/wallbounce-record-2026-11-02_05.md) の「研究の題に足す」)
- **一次確認**: B(第346・親=末尾の表)。筆者がこの回に読んだ出典は 21 本(◎ 2・○ 9・△ 10)。既存答申からの引用は 5 本(R-137・R-102・R-103・R-45・R-124)。読めなかったものは §5 に挙げた。
- **索引**: [INDEX.md](INDEX.md)(索引の行の追加は親が行う) ・ **元の答申**: [R-137](v2-r137-human-daily-planning-forms.md)(本書は元の答申を 1 バイトも変えていない)

> 作成 2026-11-09・リサーチ役(Opus 5.5)。子サブは起動していない。Web は WebFetch と WebSearch で読むだけで、**上限には当たっていない**(ただし OpenAlex の応答に「認証なしの問い合わせは IP ごとの共有の 1 日 $0.10 の枠を使う」との注が出た。その後の 1 回も応答した)。curl は使っていない。リポにも data/ にも何も保存していない(e-Stat の表も取得していない)。封印の層には触れていない。コード・台帳・設計書・INDEX・元の答申は変えていない。commit も git add もしていない。発注文が開かないと定めた文書(IMPLEMENTED.md・build-report-C7*/C8*・G1 のバックテストの計画・パターン台帳・data/ の下)は開いていない。
> **取り方の注**: 読む前に robots.txt を読んだのは cambridge.org・arxiv.org・escholarship.org・scholar.utc.edu・annualreviews.org(いずれも該当の道を禁じていない)。sciencedirect.com は robots.txt そのものが 403、link.springer.com は robots.txt で `ClaudeBot`・`anthropic-ai`・`Claude-Web` を `Disallow: /` にしている。BMC(jeatdisord.biomedcentral.com)の robots.txt は Springer の robots.txt へ転送された。pmc.ncbi.nlm.nih.gov はブラウザの確かめの頁だけを返した。これらはどれも、名乗り・経路・ミラー・キャッシュを変えて取りに行っていない(§5)。要旨は公開の索引(OpenAlex・Crossref)で読んだ(CLAUDE.md §7 の 11-04c §2 ①・返事その 7 §1-4 の線の内側)。
> 等級: ◎=原典の本文を読んだ/○=要旨・該当行だけ読んだ/△=検索の抜粋か書誌だけ。筆者の組み立ては【見立て】、根拠の無い置き方は【推測】と書く。**推薦は書かない**。記録 2-41 の決定((E3)・飽きの曲線は設計者が置かない)は変えず、本書の値は比べる錨の候補として並べる。

## §0 要旨

1. R-137 §9 の K-5(飽き・限界値定理・連れと一緒の滞在時間)と K-6(Gollwitzer 1999)のうち、本文まで読めたのは飽きの 1 本(Galak ほか 2011)と、限界値定理を述べる人の実験の 1 本(Simonelli ほか 2025)だけだった。ほかは要旨か書誌か検索の抜粋にとどまる(§1 の表)。
2. 飽きについて、Galak・Kruger・Loewenstein 2011 は、続けて消費すると繰り返しより変化が好まれ、間を空けると逆になると示した(好きな曲 9 回・間 1 分・106 人・交互作用 F(1,102)=47.29)[S1]。人は消費の速さが好みに効くことを低く見積もり、間を空ける条件で前もって選ぶと変化を選びすぎた [S1]。
3. 飽き(hedonic decline)の先行要因は「体からの帰還・知覚の変化・自己の振り返り」の 3 類に分けられる(総説の要旨)[S2]。飽きの時間の形には人ごとに「平ら・着実に下がる・急に下がる」の 3 型があり、刺激と時をまたいで人の中で比較的安定する(要旨)[S3]。
4. 限界値定理(Charnov 1976)の原典は書誌しか読めていない。索引に要旨が無く、発行元の ScienceDirect は robots.txt そのものが 403 だったので読んでいない [S6]。定理の文は Simonelli ほか 2025 の引用で読んだ。「今の区画の報酬が環境の平均の報酬率を下回ったら離れる」、移動の時間が長いほど区画に長く居る [S7]。
5. 人は定理の最適より長く居すぎる(overharvesting)と報告されている(Constantino & Daw 2015 ほか・二次)[S7]。Simonelli ほか(34 人・宝箱の課題・40 試行)では、時間の余裕が長い条件で取り残しが多く(underharvest)、貧しい区画では居すぎた。学習で最適に近づいたが届かなかった [S7]。
6. 連れの効果について、Sommer ほか 1992 は、連れのいる買い物客は 1 人の客より長く居て多く買い、量の差は滞在の長さを揃えても残った、と要旨に書く。要旨に数値は無い [S13]。喫茶店 3 店でも連れのいる客が長く居た [S14]。モールの出口の観察(1,269 人)では、買った率は 1 人 約 54%・連れ 41% で向きが逆だった(滞在の長さは測っていない)[S17]。
7. 食事の長さと人数(Bell & Pliner 2003)の数値は検索の抜粋だけで読んだ(△)。抜粋ではファストフードで 1 人 10.7 分(SD 3.3・22 組)・5 人以上 21.9 分(SD 5.8・18 組)、中価格の店で 27.6 分(SD 6.7・8 組)・58.5 分(SD 13.1・21 組)。抜粋の出どころは発行元でない写しで、本書はその写しを開いていない [S15]。
8. 国内の材料として、社会生活基本調査の調査票 A は 15 分ごとに「一緒にいた人」(平成 13 年は 一人で・家族・学校・職場の人・その他の人)を聞く。行動の種類 × 一緒にいた人の平均時間の表が e-Stat にある(抜粋)。値は取得していない [S20]。
9. Gollwitzer 1999 は要旨を公開の索引で読んだ。実行意図は「状況 x が来たら、目標に向けた反応 y を始める」形で、反応の制御を前もって決めた状況の手がかりに渡し、手がかりに出会うと反応が自動で起きる [S21]。R-137 §4-2 の記述(△)は要旨と合う。本文は読んでいない(大学の保管庫の写しは開いていない・理由は §5)。
10. 断られたものは ScienceDirect(robots.txt から 403)・Annual Reviews の PDF(403)・Springer と BMC(robots で ClaudeBot を禁止)・PMC(ブラウザの確かめの頁)の 4 か所である。どれも経路を変えて取りに行っていない(§5)。

## §1 R-137 §9 の項ごとの結果

| R-137 §9 | 対象 | 本書で読めたもの(等級) | 読めなかったもの |
|---|---|---|---|
| K-5 飽き | Galak・Redden など | Galak ほか 2011 の本文(◎ S1)。Galak & Redden 2018 の総説・Galak ほか 2022・Epstein ほか 2009 の要旨(○ S2〜S4)。Galak ほか 2013 は抜粋(△ S5) | 総説の本文(Annual Reviews の PDF が 403)・2022 の本文(ScienceDirect が 403)・Epstein の本文(PMC が確かめの頁)・Redden 2008 の分類の水準の論文(探していない) |
| K-5 限界値定理 | Charnov 1976 | 原典は書誌だけ(△ S6)。定理の文は S7 の引用(◎) | 原典の要旨と本文(索引に要旨なし・発行元は Elsevier) |
| K-5 限界値定理(人) | (R-137 は挙げていない) | Simonelli ほか 2025 の本文(◎ S7)。Constantino & Daw 2015・Hutchinson ほか 2008・Pirolli & Card 1999・Schlender ほか 2025・Seiler & Pinna 2017 は書誌か抜粋(△ S8〜S12) | Constantino & Daw の本文(Springer が ClaudeBot を禁止)・Hutchinson の本文 |
| K-5 連れ | 連れと一緒の買い物の滞在時間 | Sommer ほか 1992・Sommer & Sommer 1989・Lee & Martin 2001・Kapur & Bhat 2007 の要旨(○ S13・S14・S17・S18)。Bell & Pliner 2003・Herman 2017・Srinivasan & Bhat 2008 は抜粋か書誌(△ S15・S16・S19)。社会生活基本調査の用語(○ S20) | どの研究も分単位の滞在の値を本文で読めていない |
| K-6 | Gollwitzer 1999 の原典の文 | 要旨(○ S21) | 本文(§5 の U6) |

## §2 読めた中身

### 2-1 飽き(satiation・hedonic decline)

| 研究 | 課題と人数 | 結果(条件つき) | 出典 |
|---|---|---|---|
| Galak・Kruger・Loewenstein 2011 実験 1 | 好きな 1 曲を 9 回 対 好きな 3 曲の並び。続けて/1 分の間(読み込みの棒か並べ替えの課題)。106 人(ネットの登録者) | 続けて聞くと変化の方が楽しい(F(1,102)=25.52)。間を空けると繰り返しの方が楽しい(F(1,102)=22.65)。交互作用 F(1,102)=47.29・ηp²=.32。繰り返しの条件の楽しさの傾きは、続けて −3.00、間を空けて −.58(有意でない)。楽しさは 1〜9 と 101 点の滑り棒。セルの平均は図にあり本文に無い | [S1] ◎ |
| 同 実験 2 | クラシックの 10 曲を 9 曲の候補から選ぶ。続けて/2 分の間。70 人(学部生) | 前もって選ぶと平均 7.24 曲、その場で選ぶと 6.67 曲(主効果 F(1,65)=4.34)。多様化の偏りは間を空けたときにだけ現れ(F(1,65)=15.26)、続けてでは消えた(F<1)。前もって選んだ人は、間を空けたときにだけ楽しさが低い | [S1] ◎ |
| 同 実験 3 | 浜の写真 16 枚を 12 枚の候補から。間 0・30・60・90 秒。150 人のうち 138 人を分析 | 楽しさ(−4〜+4)は間が長いほど下がった(平均 1.67・.79・.28・−.19、F(3,130)=5.90)。その場で選んだ人(平均 1.34)は前もって選んだ人(−.06)より楽しく、差は間が長いほど広がった(線形の対比 F(1,59)=18.79)。著者は「前もって選ぶと、間を空けた消費の得を勘定に入れない」と読む。その場で選んだ人は間が長いほど変化を選ばなくなった | [S1] ◎ |
| Galak & Redden 2018(総説) | — | 飽きは、繰り返しの接触で快の反応が下がる傾き。典型の時間の経過と実験の型を述べ、先行要因を「physiological feedback, perceptual changes, and self-reflection」の 3 類に分ける。自己の振り返りの研究が増えている | [S2] ○ |
| Galak・Kim・Redden 2022 | — | 人ごとの時間の形は「flat, steady decline, and rapid onset decline」。刺激と時をまたいで人の中で比較的安定し、1 つの刺激で測った型が別の刺激や後の型を当てる。認知欲求(Need for Cognition)が一部を説明。再び消費するかと、その時機に効く | [S3] ○ |
| Epstein ほか 2009 | 食べ物の手がかりの繰り返し | 動物でも人でも、食べ物の手がかりの繰り返しで行動と体の反応が慣れ、慣れは食べる量と食べ終わる時機に結びつく。慣れは「エネルギーの補充で量を減らす」のとは別の仕組みとして説明される | [S4] ○ |
| Galak ほか 2013「Slow Down!」 | — | 自分で消費の速さを選んだ人は、遅い速さを与えられた人より楽しさが少なかった(抜粋) | [S5] △ |

- 【見立て】記録 2-41 の「飽きた(心)」は、見回しのときに System 1.5 が続けるかを決める形で、飽きの曲線を設計者が置かない。上の研究は駆動に入れず、住民の振る舞いと比べる錨の候補になる。比べられそうな形は (i) 間を空けると繰り返しへの飽きが弱まる、(ii) 人ごとに 3 つの時間の形がありそれぞれ安定している、の 2 つ。(ii) は記録 2-39 の均質化の計器(振る舞いのばらつき)と同じ側の量になる。
- 【見立て】食べ物の慣れ(S4)は、2-41 の「満たされた(体)=満腹は体の状態」とは別の仕組み(体の補充でない)として書かれている。2-41 の決定は体と心の 2 つに分けたので、慣れがどちらに入るかは決まっていない。

### 2-2 限界値定理と、人が区画を離れる時機

| 研究 | 中身 | 出典 |
|---|---|---|
| Charnov 1976「Optimal foraging, the marginal value theorem」Theoretical Population Biology 9(2):129-136 | 書誌だけ(索引の要旨は空・閉じた版)。索引の語は最適採餌・区画の滞在時間 | [S6] △ |
| 定理の文(Simonelli ほか 2025 の引用) | 「the most profitable moment to leave a patch」は「when the reward in the current patch is less than the average reward rate of the environment」(Constantino & Daw 2015 を引く)。「longer travel times lead to longer patch residence times」(Bustamante ほか 2023 を引く)。定理は無限の時間で率を最大にする場面を考えるので、時間の予算が決まった自分たちの課題には直接は当てられない、と書く | [S7] ◎ |
| 居すぎ(二次) | Constantino & Daw 2015 は「a tendency to harvest a patch longer than it would be needed for reward maximization」を見た(Hutchinson ほか 2008 も)。説明の候補はばらつきの費用を減らす策・学習と適応の結果・時間の認知の結果 | [S7] ◎(二次)・[S8][S9] △ |
| Simonelli ほか 2025 | 34 人(19〜50 歳)・4 つの区域の宝箱・40 試行・豊かな区画は 8→4 枚、貧しい区画は 5→1 枚。箱から箱 3.41±0.53 秒、区域を変えて取る 6.10±0.72 秒(約 2 倍)。電池が長いと最初の区域で多く開け(係数 0.600)、豊かな環境でも多く開けた(0.318)。最適のエージェントと比べ、長い電池では取り残し、貧しい最初の区域では開けすぎた(居すぎ)。著者は埋没費用の効果が一部を動かすかもしれないと書く。最後の 10 試行でも最適に届かなかった(p=0.005) | [S7] ◎ |
| Hutchinson ほか 2008 | 計算機のゲーム。直前の区画で成功が多いと滞在が短くなり、実験の後ろ 3 分の 2 で早く離れるよう学んだ(抜粋) | [S9] △ |
| Schlender ほか 2025 | ドイツのスーパーで 190 人に移動の時間・滞在・得を見積もらせ、指数の得の曲線を当てた。本人の見積もりでは精度が足りなかったかもしれない、と著者が書く(抜粋) | [S11] △ |
| Seiler & Pinna 2017 | 買い物かごの RFID で棚の前の時間を測り、最適な止め時での探索の得を平均 1 分あたり $2.10 と推定(限界値定理ではなく最適停止・抜粋) | [S12] △ |
| Pirolli & Card 1999「Information foraging」 | 書誌だけ(要旨が索引に無い) | [S10] △ |

- 【見立て】記録 2-41 の「続けた場合と知っている他の過ごし方を比べる=10-25 の機会費用」は、限界値定理の「今の率と環境の平均の率を比べる」の形に近い。ただし 2-41 は比べるのを System 1.5 の判断に置き、式を置かない。定理と人の実験は、住民の切り上げを測る物差しの候補になる(移動の時間が長いほど長く居るか・居すぎるか)。

### 2-3 連れの効果

| 研究 | 場面 | 結果(条件つき) | 出典 |
|---|---|---|---|
| Sommer・Wynes・Brinkley 1992 | 買い物。目立たない観察 | 連れのいる客は 1 人の客より長く居て多く買った。量の差は滞在の長さを揃えても残った。女性と年長の客も長く居て多く買った。要旨に数値なし | [S13] ○ |
| Sommer & Sommer 1989 | 喫茶店 3 店 | 連れのいる客は 1 人より長く居て、後から加わった組が最も長く居た。自然の場面の社会心理の研究では「長さ」が大事な従属変数、と書く | [S14] ○ |
| Granbois 1968(Sommer ほか 1992 の引用として抜粋に出た) | 薬局 | 連れのいる客は長く居て衝動買いが多い(二次) | 抜粋 △ |
| Lee & Martin 2001 | ジョージア州のモールの出口・1,269 人 | 包みを持つ率は 1 人 約 54%・連れ 41%(差は p<.05)。滞在は測っていない。著者は「社会的促進の効果は場所に依るかもしれない」と書く | [S17] ○ |
| Bell & Pliner 2003 | 職場の食堂・ファストフード・中価格の店 | 人数と食事の長さに正の相関があり、効き方は場所で違い、ファストフードで最も小さい(抜粋)。分の値は §0 の 7 のとおり(抜粋・食堂の行は抜粋に無い) | [S15] △ |
| Herman 2017(総説) | — | 人数と長さを別々に操作した研究(Pliner ほか)では、食べる量を当てたのは長さで人数ではない。現実では、少なくとも友人どうしでは人数と長さが強く絡む(抜粋) | [S16] △ |
| Kapur & Bhat 2007 | 2004 年の米国時間利用調査・週末・15 歳以上 | 「誰と」を含めて維持と裁量の活動の時間配分を MDCEV で模した。要旨に連れの有無ごとの長さの数値は無い | [S18] ○ |
| Srinivasan & Bhat 2008 | 米国時間利用調査の共同の活動 | 書誌だけ(要旨が索引に無い・発行元は Springer) | [S19] △ |
| 社会生活基本調査(平成 13 年の用語の解説) | 調査票 A | 「一緒にいた」は「普通に会話ができる程度の距離にいる場合」。近くに知っている人が誰もいないときと睡眠中は「一人で」。時間帯(15 分単位)別に 4 区分(一人で・家族・学校・職場の人・その他の人)。行動は 20 種類。頁は文字化けしており、道具が復元した文である | [S20] ○ |
| 同(抜粋) | e-Stat の表 | 平成 23 年の調査票 A に「行動の種類,一緒にいた人別総平均時間」(表 2-1)ほか。令和 8 年の調査票の見本は区分を 家族・地域の人・友人・知人・その他の人・一人で・学校・職場の人 に分ける | [S20] △ |

- 【見立て】R-137 §5 の表で、今の「まで」の型の「相手」は上限 60 分である。△ の値では、中価格の店で 4 人の組の平均が 52.3 分(SD 8.5)、5 人以上が 58.5 分(SD 13.1)だった。錨として使うなら、発行元の本文で値を確かめる必要がある(§4 の P4-b)。
- 【見立て】連れの効果は、買い物の長さ・食事の長さ・喫茶店の滞在では同じ向き(連れで長く)で、モールの購入の率では逆の向きだった。量(長さ・買う量・買った率)と場所で向きが変わりうる。

### 2-4 Gollwitzer 1999

- 書誌: Gollwitzer P.M. 1999「Implementation intentions: Strong effects of simple plans」American Psychologist 54(7):493-503 [S21]。
- 要旨(索引の逆引きから復元した文の言い換え): 目標を行動に移すのに苦労するとき(始められない・気が散る・悪い癖に戻る)、人は自動の過程を意図して使える。実行意図は予想した決定的な状況と目標に向けた反応を結ぶ計画で、「Whenever situation x arises, I will initiate the goal-directed response y!」の形をとる。反応の制御を前もって決めた状況の手がかりに渡し、手がかりに実際に出会うと反応が自動で起きる。研究の計画は、実行意図が目標の達成を進めることを示し、仕組みを明らかにする [S21]。
- 索引の逆引きには本文の冒頭(Oscar Wilde の引用・計画的行動の理論の研究では強い意図ほど実現する、の段落)も混ざって入っていた。本書は要旨の部分だけを使う。
- R-137 §4-2 の記述(「状況 x が来たら、目標に向けた反応 y を始める」・反応の制御を手がかりに委ねる)は要旨と合う。効果量(d=.65)は R-103 §2-4 のまま(Gollwitzer & Sheeran 2006 の値)で、本書では確かめていない。

## §3 既存の実装・模型の比較表(推薦なし)

| 先例 | 終わりの決め方 | 飽き | 機会費用 | 連れ | ライセンス | 出典 |
|---|---|---|---|---|---|---|
| Nijland ほか 2012 | 欲求が日数に比例して増え、閾値を越えたら行う。行えばその欲求は全部満たされる(日の単位) | 日の単位の欲求 | — | — | 論文はオープンアクセス(R-137 S1)。コードは本書で未確認 | ※R-137 §0 の 9 |
| The Sims | 物の広告が欲求をどれだけ満たすか | 欲求の値 | 広告の比べ合い | — | 商用 | ※R-45・※R-124 |
| MATSim | 終了時刻か最長の所要時間。採点に典型の所要時間 | — | 採点で間接 | — | GPL(読むだけ・写さない) | ※R-137 S8〜S11 |
| Lyfe | 反復の検出(新しさの枯渇) | 反復 | — | — | 本書で未確認 | ※R-45(R-137 §5 の引用) |
| 区画の採餌の課題(Constantino & Daw 2015) | 今の率と環境の平均の率 | — | 時間の機会費用を学ぶ(索引の語に TD 学習・平均の報酬) | — | コードは本書で未確認 | [S8] △ |
| Simonelli ほか 2025 | 最適のエージェント(時間の予算つき)と比べる | — | — | — | 論文 CC BY-NC-ND 4.0。コードは本書で未確認 | [S7] ◎ |
| MDCEV(Kapur & Bhat 2007) | 1 日の時間を活動 × 誰と に配る | — | 効用の比べ合い | 誰と別の配分 | 本書で未確認 | [S18] ○ |
| 回答 10-25 §4-3 と記録 2-41(本プロジェクト) | 見回しで System 1.5 が続けるかを決める。既定 60 分・上限 480 分は宣言したつなぎ | 曲線を置かない | 続けた場合と知っている他の過ごし方を比べる | 「相手」の型 | — | 記録 2-41 |

## §4 決めるべき題(選択肢と根拠・推薦は書かない)

| # | 題 | 選択肢 | 根拠 |
|---|---|---|---|
| P4-a | どれを錨として住民と比べるか | 間を空けた消費の効果/飽きの 3 つの型/居すぎ・取り残し/連れによる長さの伸び/比べない | §2-1〜§2-3。2-41 の決定は変えない |
| P4-b | △ の値の扱い | 錨に使う前に親が発行元の本文を確かめる/△ のまま「未確認」と書いて使う/使わない | §0 の 7。ScienceDirect は 403 |
| P4-c | Gollwitzer 1999 の大学の保管庫(KOPS)の写しを読んでよいか | 読む/読まない(要旨のまま) | §5 の U6。著者の頁の同じ文書が R-137 で 403 だった |
| P4-d | 社会生活基本調査の「一緒にいた人」の表を取得するか | 取得する(e-Stat・許可の一覧の内側・ライセンス台帳に行)/しない。取るなら記録 2-44 のデータの 2 つの組のどちらに置くか(2-44 は社会生活基本調査の 15 分ごとの割合を「学びの候補」に挙げる) | §2-3。2-44 |
| P4-e | 飽きの計器 | 活動の長さの分布/繰り返しの間隔と切り上げの関係/人ごとの時間の形/出さない | §2-1・2-39 の均質化の計器 |
| P4-f | 切り上げの計器 | 移動の時間と滞在の長さの関係/居すぎの率/出さない | §2-2 |

## §5 読めなかったもの・確かめていないもの

| # | 対象 | 理由 | 取り方の注 |
|---|---|---|---|
| U1 | Galak・Kim・Redden 2022 の本文(ScienceDirect)と Bell & Pliner 2003 の発行元の頁 | sciencedirect.com は robots.txt そのものが **403** | そこで止めた。別の名乗り・経路で取りに行っていない |
| U2 | Galak & Redden 2018 の総説の PDF(annualreviews.org) | robots.txt は `/doi/` を禁じていないが、PDF が **403** | そこで止めた |
| U3 | Constantino & Daw 2015・Schlender ほか 2025・Srinivasan & Bhat 2008(link.springer.com)と Herman 2017(BMC) | Springer の robots.txt が `ClaudeBot`・`anthropic-ai`・`Claude-Web` を `Disallow: /`。BMC の robots.txt は Springer へ転送 | 読んでいない。PMC の写しも開いていない |
| U4 | Epstein ほか 2009 の本文(pmc.ncbi.nlm.nih.gov) | ブラウザの確かめの頁だけが返った | 断られたものとして扱い、取り直していない。要旨は OpenAlex |
| U5 | Bell & Pliner 2003 の写し(Zenodo) | 検索の抜粋は Zenodo の PDF を出どころに挙げたが、発行元(Elsevier)の頁が読めず、写しの出どころが確かめられない | 開いていない(ミラーにあたる恐れ)。§0 の 7 の値は抜粋のまま △ |
| U6 | Gollwitzer 1999 の本文 | R-137 で著者の頁の PDF が 403。OpenAlex は大学の保管庫(KOPS)の投稿版を開いた版として挙げる | 同じ文書を別の場所で読むことが「経路を変える」に当たる恐れがあるので開いていない。親の判断を求める(P4-c) |
| U7 | Hutchinson ほか 2008 の本文 | 発行元は Elsevier。抜粋に出た著者の頁の PDF は開いていない(U5 と同じ理由) | — |
| U8 | eScholarship の居すぎの論文(qt84j3j2hp) | robots.txt は許すが、PDF が道具の上限 10 MB を超え、品目の頁は中身が空で返った | 別の経路で取りに行っていない |
| U9 | Charnov 1976・Pirolli & Card 1999 の要旨 | 索引に要旨が無い(どちらも閉じた版) | 書誌だけ |
| U10 | Redden 2008(分類の水準と飽き)・McAlister の属性の飽きの模型 | 探していない | — |
| U11 | 分単位の連れの効果の本文の値 | 上の U1・U3 のため | §2-3 の値は要旨か抜粋 |
| U12 | 社会生活基本調査の「一緒にいた人」の表の値 | 取得していない(P4-d) | — |
| U13 | Simonelli ほか 2025 の HTML の末尾 8,026 字 | 読んでいない | 本文の結果の節は読んだ |

Web の道具の上限には当たらなかった。

## §6 出典(読んだ日はすべて 2026-11-09)

| # | 出典 | URL | 読んだ範囲 | 等級 |
|---|---|---|---|---|
| S1 | Galak J., Kruger J., Loewenstein G. 2011「Is variety the spice of life? It all depends on the rate of consumption」Judgment and Decision Making 6(3):230-238(CC BY 3.0) | https://doi.org/10.1017/S1930297500001431 | Cambridge Core の本文(実験 1〜3 の方法と結果) | ◎ |
| S2 | Galak J., Redden J.P. 2018「The Properties and Antecedents of Hedonic Decline」Annual Review of Psychology 69:1-25 | https://doi.org/10.1146/annurev-psych-122216-011542 | OpenAlex の要旨 | ○ |
| S3 | Galak J., Kim J., Redden J.P. 2022「Identifying the temporal profiles of hedonic decline」OBHDP 169:104128 | https://doi.org/10.1016/j.obhdp.2022.104128 | OpenAlex の要旨 | ○ |
| S4 | Epstein L.H., Temple J.L., Roemmich J.N., Bouton M.E. 2009「Habituation as a determinant of human food intake」Psychological Review 116(2):384-407 | https://doi.org/10.1037/a0015074 | OpenAlex の要旨 | ○ |
| S5 | Galak J., Kruger J., Loewenstein G. 2013「Slow Down! Insensitivity to Rate of Consumption Leads to Avoidable Satiation」JCR 39(5):993-1009 | (検索の結果の econbiz と RePEc の頁) | 検索の抜粋 | △ |
| S6 | Charnov E.L. 1976「Optimal foraging, the marginal value theorem」Theoretical Population Biology 9(2):129-136 | https://doi.org/10.1016/0040-5809(76)90040-x | OpenAlex の書誌(要旨なし) | △ |
| S7 | Simonelli V., Nuzzi D., Lancia G.L., Pezzulo G.「Human foraging strategies flexibly adapt to resource distribution and time constraints」arXiv 2408.01350(v4 は 2025-05-12・CC BY-NC-ND 4.0) | https://arxiv.org/abs/2408.01350 | 要旨と HTML v3 の前半 10 万字 | ◎ |
| S8 | Constantino S.M., Daw N.D. 2015「Learning the opportunity cost of time in a patch-foraging task」CABN 15(4):837-853 | https://doi.org/10.3758/s13415-015-0350-y | OpenAlex と Crossref の書誌(要旨なし)・S7 の二次 | △ |
| S9 | Hutchinson J.M.C., Wilke A., Todd P.M. 2008「Patch leaving in humans: can a generalist adapt its rules to dispersal of items across patches?」Animal Behaviour 75:1331-1349 | (検索の結果) | 検索の抜粋 | △ |
| S10 | Pirolli P., Card S. 1999「Information foraging」Psychological Review 106(4):643-675 | https://doi.org/10.1037/0033-295x.106.4.643 | OpenAlex の書誌(要旨なし) | △ |
| S11 | Schlender ほか 2025「Grocery Shopping Under Simplified Marginal Value Theorem Predictions」Human Nature | https://doi.org/10.1007/s12110-024-09485-3 | 検索の抜粋 | △ |
| S12 | Seiler S., Pinna F. 2017「Estimating Search Benefits from Path-Tracking Data」Marketing Science 36(4):565-589 | https://doi.org/10.1287/mksc.2017.1026 | 検索の抜粋 | △ |
| S13 | Sommer R., Wynes M., Brinkley G. 1992「Social Facilitation Effects in Shopping Behavior」Environment and Behavior 24(3):285-297 | https://doi.org/10.1177/0013916592243001 | Crossref の要旨 | ○ |
| S14 | Sommer R., Sommer B.A. 1989「Social Facilitation Effects in Coffeehouses」Environment and Behavior 21(6):651-666 | https://doi.org/10.1177/0013916589216001 | Crossref の要旨 | ○ |
| S15 | Bell R., Pliner P.L. 2003「Time to eat: the relationship between the number of people eating and meal duration in three lunch settings」Appetite 41(2):215-218 | https://doi.org/10.1016/s0195-6663(03)00109-0 | OpenAlex と Crossref の書誌(要旨なし)・検索の抜粋 | △ |
| S16 | Herman C.P. 2017(社会的促進の総説)Journal of Eating Disorders 5:16 | (検索の結果) | 検索の抜粋 | △ |
| S17 | Lee L.J., Martin A.L. 2001「Influence of social facilitation and gender differences on purchasing behavior of consumers in a mall」Modern Psychological Studies 8(1) | https://scholar.utc.edu/mps/vol8/iss1/6/ | 雑誌の保管庫の頁の要旨 | ○ |
| S18 | Kapur A., Bhat C.R. 2007「Modeling Adults' Weekend Day-Time Use by Activity Purpose and Accompaniment Arrangement」TRR 2021:18-27 | https://doi.org/10.3141/2021-03 | Crossref の要旨 | ○ |
| S19 | Srinivasan S., Bhat C.R. 2008「An exploratory analysis of joint-activity participation characteristics using the American time use survey」Transportation 35(3):301-327 | https://doi.org/10.1007/s11116-007-9155-3 | Crossref の書誌(要旨なし) | △ |
| S20 | 総務省統計局「平成13年社会生活基本調査 用語の解説 3. 1日の生活時間に関する事項(調査票A)」と、e-Stat の表の題・令和 8 年の調査票の見本(抜粋) | https://www.stat.go.jp/data/shakai/2001/yogo3.html | 頁(文字化けを道具が復元)・検索の抜粋 | ○ |
| S21 | Gollwitzer P.M. 1999「Implementation intentions: Strong effects of simple plans」American Psychologist 54(7):493-503 | https://doi.org/10.1037/0003-066X.54.7.493 | OpenAlex の要旨(逆引きの索引から復元) | ○ |

既存答申: ※R-137(親の一次確認 第343・B)§4・§5・§9・※R-102(B)§1-3・※R-103(B)§2-4・※R-45(B)・※R-124(B)。循環参照検査: 本書は D 等級の答申を根拠に使っていない。R-103 の d=.65 は R-103 のまま引き、本書では確かめていない。

### 親が一次確認すべき数値と主張

1. Galak ほか 2011 の実験 1 の F 値(25.52・22.65・47.29)と傾き(−3.00・−.58)、実験 3 の平均(1.67・.79・.28・−.19、1.34 対 −.06)[S1]。
2. Simonelli ほか 2025 の定理の文と、3.41±0.53 秒・6.10±0.72 秒・34 人 [S7]。
3. Lee & Martin 2001 の 1,269 人・約 54% 対 41% [S17]。
4. Bell & Pliner 2003 の分の値は △ のまま。錨に使うなら発行元の本文が要る(P4-b)。
5. 社会生活基本調査の「一緒にいた人」の定義の文(文字化けの復元)[S20]。

## 親の一次確認(第346・2026-11-09・親)

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| 値の確かめ | — | 親は値を原典で確かめていない(◎ は 2 本だけで、ほかは要旨・書誌・抜粋)。錨に使う前に写し検査が要る |
| 断られた頁: sciencedirect の robots.txt が 403・annualreviews の PDF が 403・link.springer.com の robots が ClaudeBot を Disallow・PMC は確かめの頁 | 取り方の注と §読めなかったもの | 別の経路の形跡なし・本文に無い |
| Gollwitzer 1999 の KOPS の写し | 報告 | 開いていない。著者の頁の同じ文書が 403 だったので、別の置き場の写しを読むかはユーザーの判断(第346 の報告)。11-09 §1-4 の線では、原典そのものが断ったら読まない |
