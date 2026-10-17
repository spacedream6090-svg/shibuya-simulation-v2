# R-95 答申: 声の大きさの段階と分布(ANSI S3.5 の値の出どころ・人ごとの差・距離・ささやき声・日本語の話者・連続値の形)

<!-- hdr:v1 -->
- **分野**: 環境音響学 #6 / 知覚心理学・精神物理学 #5 / 会話分析・語用論 #15 | **重要度**: P1(指示書 10-06 §7 の 6・§2 SR8 の材料)
- **一次確認**: **B**(サブ実読。本文を自分で抽出した原典 5・取得ツール経由の本文と二次実装の表 5・抄録または二次 6・未読 2・空欄は §空欄)・親検収 済(第323・2026-10-06: Odeon 表 1 の普通の声の帯域値(250 Hz 57.2・500 Hz 59.8・1 kHz 53.5・2 kHz 48.8・4 kHz 43.8・8 kHz 38.6)から A 特性の合計を親が再計算して 59.49 dB=指示書の 59.5 と一致(重み付けなしは 62.58≈ANSI の 62.35)。指示書の 4 値は「ANSI S3.5 の帯域スペクトルの A 特性の合計(Odeon の計算)」と読むのが正しい。ほかの段と白石・神田 2010・加納 1985 の値は親は未再計算))
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-06・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は標準出力か作業用の一時の写しを pymupdf で抽出し、写しは読んだ後に消した)。取得物なし(`data/research_cache/r95/` は作っていない)。コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: 声の段の 3 系統の表・距離の減衰・ロンバードの式・閾値 = [R-78](v2-r78-speech-propagation-intelligibility.md) §1・§6 / ロンバードの腕 0.32(Miles ほか 2023)と会話の距離 = [R-79](v2-r79-noticing-factors-conversation-distance.md) / 視野と見分けの距離 = [R-62](v2-r62-field-of-view-anchors.md) / 会話の量 = [R-84](v2-r84-conversation-volume-anchors.md)(声の大きさの値は無し)。本書は R-78 の表を再掲せず番号で引き、足りない値だけを足す。
> 対象: [指示書 10-06](../design/v2-wallbounce-decisions-2026-10-06.md) §2 SR8・[空間の設計ラウンドの草案](../design/v2-spatial-design-round-draft.md) SR8。

## 結論(5 行)

1. **指示書の 59.5・66.5・73.7・82.3 dB は ANSI S3.5-1997 の表の値ではなく、ANSI のオクターブ帯域の標準スペクトル(口の正面 1 m・自由音場)を A 特性で足し合わせた値**で、計算したのは Odeon の技術資料の表 1 です。表の帯域値から自分で足し直すと 59.49・66.48・73.69・82.32 dB になり一致しました。ANSI 自身の合計値(重み付けなし)は 62.35・68.34・74.85・82.30 dB です。Pearsons 1977 の値(男性の普通 58・女性 55 dBA)とは別系統で、ANSI の「普通」は実測の普通の声より 2〜5 dB 大きい側にあります。
2. **人ごとの差は標準偏差 3〜4 dB**。Pearsons 1977 の無響室では普通の声の SD が 4 dB(男女とも)、大声と叫び声では 6〜7 dB に広がります。日本語の話者(九大生 20 人の 7 分間の朗読)は 1 m の LAeq が男性 56.3・女性 51.7 dB(算術平均)で、SD は個人値から再計算して男性 3.9・女性 4.2 dB、最大と最小の差は 16.3 dB でした。男女差は 3〜5.5 dB(Pearsons 3・白石 4.6・Hunter 5.5)。
3. **相手が遠いと声は上がるが、逆二乗(倍で 6 dB)の補償には届かない**。13 人の男性が 1.5〜12 m の相手に話した実験で、距離が倍になるごとに 1.3〜2.2 dB 上がりました(Pelegrín-García ほか 2011・抄録)。「相手の位置で同じ大きさにせよ」と明示した課題では、ほぼ完全に補償できます(Zahorik & Kelly 2007・母音)。自然な会話の既定値は前者が近い。
4. **ささやき声と小声の 1 m の値は、多人数の実測が見つからなかった**。規格の段では Lazarus が 36(ささやき)・42 dB(小声)とし(R-78)、二次資料は 30〜40 dB を挙げます。Cushing 2011 の「hushed」(ささやきより少し大きい有声の最小)は 44〜45 dB 前後(二次の表・重み付け不明)です。普通の声との差は約 20 dB という記述があります。
5. **日本語の話者のロンバードの傾きは平均 0.49 dB/dB**(加納 1985・14 人・30 cm・背景 50〜90 dBA)で、Rindel の 0.5 とほぼ同じです。ただし帯域ごとの値 0.27〜0.74 と本文の言葉(「高騒音ほど小さい」)が原典の中で食い違っています。段階・人ごとのオフセット・ロンバード・距離を dB で足し合わせる形は先行例(Pelegrín-García 2011・Bouserhal 2017)と同じで、新しい組み立てではありません。

## §0 出典の表

等級: **◎** 原典本文を自分で抽出して数値まで確認 / **○** 取得ツール経由の本文・二次実装の表 / **△** 抄録・二次・検索の要約 / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 使った箇所 |
|---|---|---|---|---|
| 1 | Odeon「Application note: Calculation of Speech Transmission Index in rooms」 | https://odeon.dk/pdf/Application_Note_SpeechTransmissionIndex.pdf | ◎ | 4 頁 表 1(画像を目で読み、A 特性で再計算)・表 2 |
| 2 | SII の MATLAB 実装 SII.m(ANSI S3.5 の表 3 の 1/3 オクターブの標準スペクトル) | https://github.com/jtkim-kaist/Speech-enhancement/blob/master/SE/lib/sub_lib/MATLAB_code/objective_measures/intelligibility/SII.m | ○ | `SpV` の表(18 帯域 × 4 段)を読み、合計と A 特性を再計算 |
| 3 | R パッケージ SII(Warnes)vignette の `overall.spl` | https://cran.r-project.org/web/packages/SII/vignettes/SII.pdf | ○ | PDF 抽出(ANSI の表の二次実装) |
| 4 | ANSI/ASA S3.5-1997 (R2017/R2024)「Methods for Calculation of the Speech Intelligibility Index」 | (有料) | × | 本文未読。値は #1〜#3 経由 |
| 5 | Olsen W.O. 1998「Average Speech Levels and Spectra in Various Speaking/Listening Conditions」Am J Audiol 7(2) | https://doi.org/10.1044/1059-0889(1998/012) (読んだ写し: CEQA の公開添付) | ◎ | 表 2〜5(SD を含む)・方法 |
| 6 | Hopkins C., Graetzer S., Seiffert G. 2025「On-axis sound pressure levels and sound power of normal speech ...」Forum Acusticum 2025 | https://dael.euracoustics.org/confs/fa2025/data/articles/000654.pdf | ◎ | Pearsons と Cushing の人数・ANSI と ISO 3382-3 の関係・文献表 |
| 7 | Acta Acustica 2026「Sound power of speech between 63 Hz and 20 kHz at a normal vocal effort level」 | https://acta-acustica.edpsciences.org/articles/aacus/full_html/2026/01/aacus260033/aacus260033.html | △ | 403 で本文は読めず。検索の要約で Pearsons と Cushing の平均と SD |
| 8 | Cushing I.R., Li F.F., Cox T.J., Worrall K., Jackson T. 2011「Vocal effort levels in anechoic conditions」Applied Acoustics 72(9):695-701 | https://doi.org/10.1016/j.apacoust.2011.02.011 | △ | 抄録と検索の要約(50 人・平均 30 歳・hushed の定義) |
| 9 | Hunter E.J., Berardi M.L., van Mersbergen M. 2021「Relationship Between Tasked Vocal Effort Levels and Measures of Vocal Intensity」JSLHR 64(6):1829-1840 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8740752/ | ○ | 表 2・3、男女差、個人内の再現性 |
| 10 | Pelegrín-García D., Smits B., Brunskog J., Jeong C.-H. 2011「Vocal effort with changing talker-to-listener distance in different acoustic environments」JASA 129(4):1981-1990 | https://doi.org/10.1121/1.3552881 | △ | DTU の抄録・検索の要約(距離 1.5/3/6/12 m・4 室) |
| 11 | Zahorik P., Kelly J.W. 2007「Accurate vocal compensation for sound intensity loss with increasing distance in natural environments」JASA 122(5):EL143-EL150 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3412342 | ○ | 方法・結果・先行研究の値 |
| 12 | Traunmüller H., Eriksson A. 2000「Acoustic effects of variation in vocal effort by men, women, and children」JASA 107:3438-3451 | https://doi.org/10.1121/1.429414 | △ | 抄録と検索の要約(0.3〜187.5 m・ささやき声を含む) |
| 13 | 白石君男・神田幸彦 2010「日本語における会話音声の音圧レベル測定」Audiology Japan 53(3):199-207 | https://doi.org/10.4295/audiology.53.199 | ◎ | 方法・表 1・表 2(個人値) |
| 14 | 加納有二 1985「騒音下の発声音レベルの研究」日本耳鼻咽喉科学会会報 88(2):138-147 | https://doi.org/10.3950/jibiinkoka.88.138 | ◎ | 方法・結果 1)・考察(段の差 6 dB) |
| 15 | Bouserhal R.E. ほか 2017「Modeling Speech Level as a Function of Background Noise Level and Talker-to-Listener Distance for Talkers Wearing Hearing Protection Devices」JSLHR | https://doi.org/10.1044/2017_JSLHR-S-17-0052 | △ | Europe PMC の抄録 |
| 16 | Šrámková H. ほか 2015「The softest sound levels of the human voice in normal subjects」JASA 137(1):407-418 | https://pubs.aip.org/asa/jasa/article/137/1/407/911468/The-softest-sound-levels-of-the-human-voice-in | △ | #17 経由の値のみ |
| 17 | Galster J.「Revisiting expectations for average and soft speech levels」Phonak Audiology Blog(2024-05 以前) | https://audiologyblog.phonakpro.com/revisiting-expectations-for-average-and-soft-speech-levels/ | ○ | 本文 |
| 18 | Sato H., Morimoto M., Ota R. 2011「Acceptable range of speech level in noisy sound fields for young adults and elderly persons」JASA 130(3):1411-1419 | (URL 未確認・書誌は #17 の文献表) | × | #17 の文献表のみ(聞き手の許容の値で、話し手の値ではない) |
| 19 | (既存)R-78 の #6(Odeon)・#8(Rindel 2019)・Lazarus の表 | リポ内 | B+ | 段の値の既存の表 |
| 20 | (既存)R-79 の Miles ほか 2023(ロンバード 0.32・2.0 cm/dB) | リポ内 | B+ | 腕の値 |

本数: ◎ 5(#1・5・6・13・14)/ ○ 5(#2・3・9・11・17)/ △ 6(#7・8・10・12・15・16)/ × 2(#4・18)。#19・#20 は既存答申。

---

## §1 指示書の値 59.5/66.5/73.7/82.3 dB の出どころ(調べること 1)

時点: ANSI S3.5-1997(再確認 2017・2024)。世界の基準の日付(未決・候補 W13 の週 = 2026-07-28)とは無関係の規格値。

### 1-1 3 つの表の関係

| 段 | ANSI の合計(重み付けなし・#3 `overall.spl`) | 1/3 オクターブ表(#2)から再計算: 合計 / A 特性 | Odeon 表 1 のオクターブ帯域(#1)から再計算: A 特性 | Odeon 表 1 の「A-weighted」欄 |
|---|---|---|---|---|
| normal(普通) | 62.35 | 62.35 / 59.22 | 59.49 | 59.5 |
| raised(少し大きい) | 68.34 | 68.28 / 66.36 | 66.48 | 66.5 |
| loud(大声) | 74.85 | 74.86 / 73.85 | 73.69 | 73.7 |
| shout(叫び声) | 82.30 | 82.36 / 82.21 | 82.32 | 82.3 |

- #1 の表 1 の題: 「Speech spectra in octave bands for different vocal effort. SPL at 1 m in front of the mouth from ANSI 3.5 [4] and the calculated corresponding sound power levels」。帯域値(普通): 250 Hz 57.2・500 Hz 59.8・1 kHz 53.5・2 kHz 48.8・4 kHz 43.8・8 kHz 38.6 dB。本文: 「The original data for speech level are given as sound pressure levels (SPL) at a distance of 1 m in front of the speaker's lips in the free field」「The data at the 125 Hz octave band are not available from ANSI 3.5」。
- 再計算の方法: 帯域値に標準の A 特性の補正(250 Hz −8.6・500 Hz −3.2・1 kHz 0・2 kHz +1.2・4 kHz +1.0・8 kHz −1.1 dB)を足し、エネルギーで合計した [再計算]。1/3 オクターブ表は「スペクトルレベル(dB/Hz)」なので、帯域幅(中心周波数 × 0.2316)の 10 lg を足して帯域レベルにした [再計算]。重み付けなしの合計が #3 の値と 0.06 dB 以内で合ったので、表の読み方は正しいと判断した。
- 1/3 オクターブ表からの A 特性(59.2・66.4・73.9・82.2)とオクターブ表からの値(59.5・66.5・73.7・82.3)は 0.3 dB 以内で一致する。オクターブの表を 1/3 オクターブから組み直すと帯域ごとに 1 dB 以内で合った [再計算]。
- **判定**: 指示書の 4 値は「ANSI S3.5 の標準スペクトル(口の正面 1 m・自由音場)を A 特性にした合計」で、R-78 §1-1 の記述(「ANSI S3.5 の標準スペクトル(A 特性合計・#6 表 1)」)と同じ。ANSI の規格書そのものに A 特性の合計の欄があるかは確かめられなかった(本文未読=空欄 1)。**Pearsons 1977 の値ではない**(Pearsons の普通は女性 55・男性 58 dBA=#5 表 5)。
- 測定の条件(#1・#6): 口の正面 1 m・自由音場(無響)・長時間平均。帯域は 250 Hz〜8 kHz(ANSI の「standard」スペクトルは 250 Hz〜8 kHz のオクターブ。ISO 3382-3 のスペクトルと 250 Hz〜8 kHz で同じ=#6 逐語「The ANSI S3.5 'standard' spectrum is the same as the ISO 3382-3 spectrum between 250Hz and 8kHz」)。
- ANSI の標準スペクトルの元のデータ: 検索の要約では「Pavlovic 1987 がまとめた複数の研究から作った」とされる(△・Morales & Leembruggen の資料の要約。本文未読=空欄 2)。Pearsons 1977 は材料の 1 つの可能性があるが、確かめていない。

### 1-2 含意(サブの読み)

- ANSI の「普通 59.5」は、実測の普通の声(Pearsons 55/58・白石 51.7/56.3=§2)より 2〜8 dB 大きい。ANSI の段は「規格上の段の代表値」で、平均的な話し手の普通の声とは位置がずれている。R-78 §1-1 で並べた ISO 9921(普通 60)とも 0.5 dB の差しかないので、SII と ISO 9921 の両方とそろう利点は残る。
- 普通の声の基準を 59.5 にするか、実測寄りの 55 にするかで、普通の声が届く距離は約 1.7 倍変わる(4.5 dB の差 → 10^(4.5/20)=1.68 [再計算])。R-78 §9 の腕「55・60」と同じ論点。

## §2 人ごとの声の大きさの分布(調べること 2)

### 2-1 無響室での段ごとの平均と SD(Pearsons 1977=#5 表 5・逐語)

時点: 測定は 1970 年代前半(EPA の委託研究・報告は 1977)。

| 段 | 女性 dBA(SD) | 男性 dBA(SD) | 子ども dBA(SD) |
|---|---|---|---|
| casual(雑談) | 50 (4) | 52 (4) | 53 (5) |
| normal | 55 (4) | 58 (4) | 58 (5) |
| raised | 63 (4) | 65 (5) | 65 (7) |
| loud | 71 (6) | 76 (6) | 74 (9) |
| shouted | 82 (7) | 89 (7) | 82 (9) |

- 条件(#5 逐語): 「Speech levels were measured in an anechoic chamber for 100 individuals ... at a distance of 1 m」。女性と男性は「aged 13 to 60 years」、子どもは「under age 13」。人数は男性 42・女性 35(#6)。読んだ文は 1 文(「Joe took father's shoe bench out ...」)。
- SD は話し手の間の差。普通の声で 4 dB、大声と叫び声で 6〜7 dB に広がる。
- Cushing 2011(英国の 50 人・平均 30 歳): 普通の声で男性 58(SD 3)・女性 56(SD 3)dBA(#7 の検索の要約・△)。著者の要旨では Pearsons と 1〜2 dB(A) の差(#8)。

### 2-2 日本語の話者(白石・神田 2010=#13・◎)

時点: 論文受付 2010-03(測定は 2009〜2010 と推測)。

- 対象と条件(逐語): 「九州大学の男子学生１０名（平均２３．６±０．８歳）と女子学生１０名（平均２２．８±１．５歳）の計２０名」。無響室で「通常話す音声の大きさと速さ」で 7 分間の朗読を 4 回。マイクは唇から 1 m 前方。
- 1 m 前方の LAeq(逐語): 男性「算術平均 56．3 dB エネルギー平均 57．8 dB」、女性「算術平均51．7dB エネルギー平均53．6 dB」、全体「算術平均54．0 dB エネルギー平均56．2 dB」。最大 62.3(男性)・最小 46.0(女性)・差 16.3 dB。
- 個人値(表 2)からの再計算 [再計算]: SD は男性 3.94・女性 4.19 dB、20 人まとめて 4.60 dB。男女差 4.56 dB。重み付けなしの LZeq は男性 61.1(SD 3.30)・女性 56.5(SD 3.15)dB。
- 注意: 朗読で、会話ではない。若い学生だけ。Pearsons の普通の声(男性 58・女性 55)より約 2〜3 dB 小さい。

### 2-3 段を指示したときの重なり(Hunter ほか 2021=#9・○)

時点: 2021 年の論文。

- 20 人(女性 10・男性 10・平均 20.4 歳)に、努力の段(Borg CR100 の 2・13・25・50)を指示した。1 m 換算の声: 2 → 58.26(SD 6.16)・13 → 62.98(SD 6.58)・25 → 66.59(SD 6.98)・50 → 73.24(SD 7.24)dB。
- 隣の段の効果量は d = 0.74・0.53・0.93 で、人と文をまとめた分布は大きく重なる(最小〜最大の幅が隣の段と重なる)。
- 「the biological females produced 5.46 dB less (from the medians) than the males」。段と性別の交互作用はなし(p = .541)。
- 同じ人の中では、9 種の文の間の相関が平均 r = .90。**人ごとの大きさは安定した性質**として扱える(サブの読み)。

### 2-4 年齢

- Pearsons は 13〜60 歳をまとめており、年代別の値はない。高齢者の話し声の大きさの差の一次は見つからなかった(空欄 3)。

## §3 相手との距離による声の変化(調べること 3)

| 出典 | 課題 | 距離 | 距離が倍になるごとの増分 | 等級 |
|---|---|---|---|---|
| Pelegrín-García ほか 2011(#10) | 13 人の男性が聞き手に話す。4 室(無響室・講義室・廊下・残響室) | 1.5・3・6・12 m | 1.3〜2.2 dB(要約によっては 1.5〜2.0) | △ |
| Zahorik & Kelly 2007(#11) | 「聞き手の位置で同じ大きさになるように」と明示。母音 /a/ を 3 秒 | 1・2・4・8 m | 部屋の減衰(−1.8〜−6.4 dB/倍)をほぼ打ち消した。聞き手の位置での傾きの中央値 −0.9 dB/倍 | ○ |
| Warren 1968(#11 経由) | - | - | 6 dB | △ |
| Michael ほか 1995(#11 経由) | - | - | 減衰が約 2 dB/倍の場で、補償も約 2 dB/倍 | △ |
| 先行研究のまとめ(#11 逐語) | - | - | 「ranging from 5 to less than 1 dB/doubling」 | ○ |
| Traunmüller & Eriksson 2000(#12) | 屋外の野原で相手に話す | 0.3〜187.5 m | 生成側の傾きは本文未読(空欄 4)。聞き手が「倍の距離」と感じるのに要る増分は 4.6 dB(同じ著者の知覚研究の要約) | △ |

- Zahorik & Kelly の注意(#11 逐語): 「adjust their vocal output level such that the level reaching the experimenter (distal level) remained constant」。自然な会話ではなく、明示した課題で、母音だけ。
- 含意(サブの読み): 自然に相手に話すときの既定は「倍ごとに約 1.5〜2 dB」。逆二乗で 6 dB 落ちるので、相手が遠いほど聞き手の位置の声は小さくなる。距離 1 m → 2 m → 4 m での増分は、Pelegrín-García の傾きを 1 m まで延ばすと +1.3〜2.2・+2.6〜4.4 dB [再計算・1.5 m より近い側への外挿は推測]。
- Pearsons の現場(R-78 §1-2)では、話し手は自分で約 1 m を選び、電車と飛行機では 0.4 m まで近づいた。距離と声の両方を動かしている。

## §4 ささやき声と小声(調べること 4)

| 段 | 値(1 m・dBA) | 出典 | 等級 |
|---|---|---|---|
| ささやき | 36 | Lazarus(R-78 #8 の表 2) | R-78 で ◎ |
| 小声(soft) | 42 | 同上 | 同上 |
| ささやき・小声の典型 | 35〜50 | Rindel 2019(R-78 #8 逐語「whispering or soft speech ... 35 dB to 50 dB」) | 同上 |
| ささやき | 30〜40 | 一般の二次資料(検索の要約) | △ |
| hushed(有声の最小。「just louder than whispering」) | 男性 44.3・女性 45.3(帯域の合計。A 特性かは不明) | Cushing 2011 を引く二次の表(検索の要約。原典の PDF は 404) | △ |
| 最も小さい有声の声 | 42〜47 dBA(30 cm) | Šrámková 2015(#17 経由)。1 m への換算は逆二乗で約 −10 dB=32〜37 dBA [再計算・推測] | △ |
| ささやき声と普通の声の差 | 約 20 dB | 検索の要約(出典の特定はできず) | △ |

- 多人数を 1 m の無響条件で測ったささやき声の平均と SD は見つからなかった(空欄 5)。Traunmüller & Eriksson 2000 は近い距離でささやき声も録っているが、値は本文未読。

## §5 日本語の話者の値(調べること 5)

- 普通の声: §2-2(白石 2010)。英語の Pearsons より約 2〜3 dB 小さいが、朗読と 1 文の繰り返しの違いがある。
- 騒音の中の声(加納 1985=#14・◎): 時点は 1985 年。正常聴力 14 人。背景 40(暗騒音)・50・60・70・80・90 dB(A)。対面で 0.3 m の相手に日本語の単音節を話す。測定は「口唇より30cm点」。
  - 逐語: 「発声音レベルの上昇の程度は,騒音レベル1dB当たりの変化量に換算して,0.27dB/dB (50～60dB(A)の騒音レベル間)から0.74dB/dB (80～90dB(A)の騒音レベル間)まで,平均0.49dB/dBであった」。
  - 同じ段落に「騒音レベルの上昇に対応した発声音レベルの上昇の程度は,高騒音レベルになるにつれて小さくなった」とあり、数値の並び(高い側ほど大きい)と食い違う〔原典内の食い違い・図 2 は画像で未確認〕。
  - 「騒音下の発声音レベルは,騒音の周波数分布にかかわらず,騒音のA-特性レベル(感覚レベル)にしたがって変化した」。
  - 段の差(考察・逐語): 「普通の話声の大きさより,やや大声,非常に大声,呼び声まで,発声努力により,約6dBずつ,最大で約18dBの差がある」(Beranek の値の引用)。
- 日本の騒音環境での実際の声の大きさ(駅や繁華街での会話の音圧の実測)は見つからなかった(空欄 6)。R-78 の #25(駅のコンコースの音環境)は背景の値。

## §6 連続値にする形の先行例(調べること 6)

- **Pelegrín-García ほか 2011(#10・△)**: 声の大きさ = 基準 + 距離の項(倍ごとに 1.3〜2.2 dB)+ 部屋の項(room gain 1 dB あたり −3.6 dB)。抄録の逐語「raised their vocal intensity by between 1.3 and 2.2 dB per double distance to the listener and lowered it as a linear function of the quantity 'room gain' at a rate of 3.6 dB/dB」。
- **Bouserhal ほか 2017(#15・△)**: 背景の騒音と距離の両方を入れた式で、Pelegrín-García の式を広げた。最も予測区間が良いのは「talker-dependent model that requires the users' unoccluded speech level at 10 m as a reference」=**人ごとの基準値を持つ形**。
- **Rindel 2019(R-78 §6・◎)**: 1 m の声 = 55 + 0.5 (背景 − 45)(背景 45 dB 超)。ロンバードを足し算で入れる形。
- **ISO 9921(R-78 §1-1)**: 段を 6 dB 刻みの連続した物差しの上に置く。75 dB を超える声は明瞭度の計算で 0.4 (L − 75) dB 下げる。
- 段階 → dB の対応 + 人ごとのオフセット + ロンバード + 距離を 1 本の dB の式で足す形は、上の 3 つを合わせたもの。足し合わせたときに交互作用があるか(例: 騒音が大きいと距離の傾きが変わるか)を測った一次は見つからなかった(空欄 7)。

## §空欄

1. ANSI S3.5-1997 の本文(A 特性の合計の欄の有無・表の番号・注)。有料で未読。
2. ANSI の標準スペクトルの元データ(Pavlovic 1987 のまとめか)の確認。
3. 年代別(とくに高齢者)の話し声の大きさ。
4. Traunmüller & Eriksson 2000 の生成側の距離の傾きと、ささやき声の値。
5. 多人数を 1 m の無響条件で測ったささやき声と小声の平均と SD(Cushing 2011 の本文の表を含む)。
6. 日本の街頭や駅での会話の声の実測。
7. 段・ロンバード・距離を足し合わせたときの交互作用の実測。
8. 加納 1985 の 0.27〜0.74 dB/dB と本文の言葉の食い違い(図 2 の確認)。
9. **ユーザーの判断が要る点**: 本人が段を選ぶとき、LLM はすでに周りのうるささを見て「大声」を選ぶかもしれない。そこへエンジンがロンバードを足すと、騒音の効果を 2 回数える。ロンバードを「段の中の自動の分」として足すか、段の選び方に任せるかは設計の判断(R-78 §9「Lombard の分は本人が選ばない自動の分」と整合させる必要)。

## §v2 への当てはめ(案・未決。親が判断する材料)

1 m・口の正面・A 特性の声の値を、次の和で出す案(形は §6 の先行例の組み合わせ):

```
L_1m = L_段 + o_人 + c × max(0, 背景 − 45) + k × max(0, log2(相手との距離 / 1 m))
       上限: 叫び声の個人上限(Lazarus 90・個人で 96=R-78)   下限: 宣言(案 30)
```

| 項 | 既定の案 | 腕 | 根拠 | 印 |
|---|---|---|---|---|
| L_段 ささやく | 36 | 30・42 | Lazarus(R-78)・二次の 30〜40 | 錨は弱い(多人数の実測なし) |
| L_段 小声 | 42 | 48 | Lazarus・Šrámkováの換算 32〜37 と Pearsons の雑談 50〜53 の間 | expedient 寄り |
| L_段 普通 | 59.5(ANSI) | 55(Pearsons/Rindel)・54(白石の日本語の全体の算術平均) | §1・§2 | 系統の宣言が要る |
| L_段 少し大きく | 66.5 | 63〜65(Pearsons) | 同上 | 同上 |
| L_段 大声 | 73.7 | 71〜76(Pearsons) | 同上 | 同上 |
| L_段 叫ぶ | 82.3 | 82〜89(Pearsons) | 同上 | 同上 |
| o_人(人ごとの性質) | 平均 0・SD 4 dB の正規分布(生成時に 1 回だけ引く) | SD 3・SD 4.6(白石の男女まとめ) | Pearsons・Cushing・白石・Hunter の再現性 r = .90 | 錨あり |
| 男女差 | なし(o_人に含める) | 男性 +2.3・女性 −2.3(差 4.6=白石)。Pearsons の差 3 | 指示書 SR8「男女の差を腕」 | 錨あり |
| 段の中の幅(段ごとに SD が広がる) | なし | 大声と叫ぶだけ SD 6〜7 | Pearsons 表 5 | 錨あり |
| c(ロンバード) | 0.5 dB/dB・開始 45 dB | 0.32(Miles 2023)・0.49(加納 1985 の平均=日本語)・0.69(Hodgson) | R-78 §6・§5 | 錨あり |
| k(距離) | 1.5 dB/倍 | 0(距離で変えない)・2.2・6(明示の課題) | Pelegrín-García 2011・Zahorik & Kelly 2007 | 錨あり(1.5 m 未満は推測) |
| 1 m より近い相手 | 声を下げない(0) | 倍ごとに −1.5 dB | 1.5 m より近い側の実測なし | 推測 |

- 普通の段の基準は ANSI(59.5)と実測(55)の 2 系統を腕にすると、届く距離が 1.7 倍変わる(§1-2)。結果を動かしそうな expedient なので、5,000 体のスクリーニングの対象の候補。
- ささやく・小声の 2 段は値の錨が弱い。この 2 段は「傍受されにくさ」に直に効くので、腕を回す候補。
- §空欄 9(ロンバードの二重計上)は設計の判断。案: 段は「相手と内容に対する努力」を選ぶ言葉とし、騒音への自動の上げ分はエンジンが c で足す。LLM の観察文には「周りがうるさい」を書くが、段の選択肢の説明は騒音に触れない形にする(推測・未検証)。
