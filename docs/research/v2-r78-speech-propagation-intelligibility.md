# R-78 答申: 声の伝わり方と聞き取り(声の大きさ・距離の減衰・建物の陰・背景の騒がしさ・明瞭度・ロンバード効果・屋内・計算の費用・先行例)

<!-- hdr:v1 -->
- **分野**: 環境音響学 #6 / 知覚心理学・精神物理学 #5 / ゲーム・VR 産業(常設レーン) | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §4-1「会話の距離は空間の段 3 で音の伝わり方から出す」・§11 第 2 群「音の伝わり方と明瞭度」)
- **一次確認**: **B**(サブ実読。原典本文 11・一部推測 10・抄録/二次 11・未読 3・空欄は §11)・既存答申との 2 段照合を実施(§0-1)・親検収 済(第317・2026-10-03: 導いた式 SNR = 32.5 − 0.5 L_N − 20 lg r を Rindel の式 1(55 + 0.5(L_N − 45))と逆二乗から再導出し、表 6 の隅 2 欄(53 dB・0.35 m → 15、71 dB・1 m → −3)を再計算で一致。ISO 9921・Pearsons 1977 の段の値は既知の値と一致。○ 10 本(要約モデル経由・図読み)の逐語は親未確認。等級 B+)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は WebFetch が保存したものをローカルの pymupdf で文字抽出。走査画像の 1 本は画面に描いて図から読んだ)・コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: 密度と話し声の騒がしさ(Meng & Kang 2015・Leembruggen 2021 の Rindel 式の閉形式・発話率の負帰還・街の谷の反射 +6〜8 dB)は [密度と可聴半径の検証](v2-density-hearing-verification.md)(等級 B・2026-09-04)にある。本書は**その答申の錨のうち会話の判定に効くものを原典へ再照合**し(§0-1)、足りない部分(声の大きさの規格の値・距離と地面と空気・建物の陰・明瞭度の閾値・日本語の了解度・屋内・駅の放送・計算の費用・ゲームの先行例)を足す。視線の遮蔽は W8([w8_visibility.py](../../src/shibuya/build/vis/w8_visibility.py)・建物頂部の 2.5 m 格子)、道路の騒音は W10([構築仕様 W10](../design/v2-world-data-build-spec.md)・ASJ RTN-Model 2018)、視野は [R-62](v2-r62-field-of-view-anchors.md)。

## 結論(5 行)

1. **声の大きさの基準値は 3 系統あり、数 dB ずれる**。1 m 先の A 特性で、ISO 9921 は普通 60・少し大きい 66・大声 72・とても大きい 78 dB とする(6 dB 刻み)。ANSI S3.5 の標準スペクトルを A 特性にすると 59.5・66.5・73.7・82.3 dB で、叫び声まである。Pearsons 1977 の無響室の実測は男性で普通 58・大声 76・叫び声 89 dB で、雑談は普通より約 5 dB 弱い。どの系統を使うかは宣言が要る。日本語話者の値は見つからなかった(空欄)。
2. **会話の判定は「1 m の声 − 20 lg(距離) − 背景 ≥ 閾値」の式で足りる**。ロンバード効果(背景が 45 dB を超えると、1 dB あたり声が約 0.5 dB 上がる)を入れると SNR = 32.5 − 0.5·背景 − 20 lg(距離) になる。この式は推測で導いたもので、Rindel 2019 の表 6 の全 42 欄と丸めの範囲で一致した。閾値には Lazarus の段階を使える(−3 dB 以上で「足りる」、0 dB 以上で「満足」)。普通の声が届く距離は、背景 45 dB で 3.2〜4.5 m、背景 75 dB で 0.6〜0.8 m になる(推測)。指示書の「静かな路地なら 3〜4 m」と合う。
3. **建物の角を回ると下がる量は周波数で大きく違う**。Kurze–Anderson の式で角の手前 2 m・先 2 m の配置を計算すると、250 Hz で 15 dB、2 kHz で 24 dB 下がる(推測)。ISO 9613-2 は 1 回の回折を 20 dB で頭打ちにする。実際の路地では壁の反射が影を埋める。角を曲がると 10〜20 dB 下がり、その量は壁の吸音で変わる(Davies)。A 特性 1 本で計算する場合、EU の文書は 500 Hz の値を使うよう勧める。ただし明瞭度に効く高い音ほど深く落ちるので、その扱いは宣言が要る。
4. **地面と空気は会話の距離ではほぼ効かない**。ISO 9613-2 の簡便式では、地面の減衰は短い距離で 0 になる。硬い地面の反射は逆に音を足し、3 m で +1.8 dB、30 m で +3.0 dB に近づく(推測)。空気の吸収は 4 kHz でも 10 m で 0.3 dB にとどまる(推測)。屋内は Rindel の式で背景と SNR が閉じた形で出る。入力は人数・部屋の容積・残響時間・1 人あたりの吸音(0.2〜0.5 m²)・話す人 1 人あたりの人数(3.5)である。仮想空間の既定値は、この式の係数として宣言できる。
5. **ゲームの音響は、直接音を遮る obstruction と部屋ごと隔てる occlusion を分ける**。どちらも音量と高音の削りで表す。物理の値は表引き(Triton は焼き込んだ波動計算を 1 回約 100 μs で引く)か光線の判定(Steam Audio)で作る。避難のエージェント模型には、日本語の了解度実験を錨にして声の伝達を入れた例がある(Aranha ほか 2017)。ただし建物の陰は入れていない。計算の費用は「話し手 × 近くの聞き手 k 人」の対の数で決まる。視線の判定は W8 の 2.5 m 格子と同じ処理を使い回せる(推測)。

---

> 〔親注記 第317・訂正の伝播〕ロンバード効果の傾き 0.5 dB/dB(Rindel の式 1)に対し、R-79 が引く Miles ほか 2023 の実測は 0.32 dB/dB。本書の式は 0.5 を係数 c として宣言し、感度の腕で 0.32 を回す(R-79 §末尾)。

## §0 出典の表

等級: **◎** 原典本文で数値まで逐語確認 / **○** 一部推測を含む(要約モデル経由の逐語・図からの読み取り・二次実装の表) / **△** 抄録・二次 / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Olsen W.O. 1998「Average Speech Levels and Spectra in Various Speaking/Listening Conditions: A Summary of the Pearson, Bennett, & Fidell (1977) Report」American Journal of Audiology 7(2) | https://doi.org/10.1044/1059-0889(1998/012) (読んだ写し: CEQA の公開添付) | ◎ | PDF 全文・表 1〜5 |
| 2 | Pearsons K.S., Bennett R.L., Fidell S. 1977「Speech levels in various noise environments」EPA-600/1-77-025 | https://cfpub.epa.gov/si/si_public_record_Report.cfm?Lab=ORD&dirEntryID=45786 | × | 書誌のみ(本文は #1 経由) |
| 3 | ANSI/ASA S3.5-1997「Methods for Calculation of the Speech Intelligibility Index」 | (有料) | △ | 本文未読。値は #4・#5・#6 経由 |
| 4 | R パッケージ SII(Warnes)vignette の `overall.spl` 表 | https://cran.r-project.org/web/packages/SII/vignettes/SII.pdf | ○ | PDF 抽出・表(規格の二次実装) |
| 5 | SII の MATLAB 実装 SII.m(ANSI S3.5 の 1/3 オクターブ法) | https://github.com/jtkim-kaist/Speech-enhancement/blob/master/SE/lib/sub_lib/MATLAB_code/objective_measures/intelligibility/SII.m | ○ | 要約モデル経由で該当行(式 12〜14) |
| 6 | Odeon「Application note: Calculation of Speech Transmission Index in rooms」 | https://odeon.dk/pdf/Application_Note_SpeechTransmissionIndex.pdf | ◎ | PDF 全文・表 1/2/6/7/8 |
| 7 | ISO 9921:2003 Ergonomics: Assessment of speech communication | (有料) | △ | 本文未読。値は #6・#8 経由 |
| 8 | Rindel J.H. 2019「Restaurant acoustics: Verbal communication in eating establishments」Acoustics in Practice 7(1) | https://euracoustics.org/documents/8/01_Restaurant_acoustics.pdf | ◎ | PDF 全文・式 1〜7・表 2〜7 |
| 9 | ISO 9613-2:1996 Acoustics: Attenuation of sound during propagation outdoors, Part 2 | (有料。公的記録の走査写しは文字なし) | △ | 式は #10・#11・#12 経由 |
| 10 | Parzych D. 2004「Handling of Barriers in ISO 9613-2」NOISE-CON 2004 | https://www.poweracoustics.com/tech%20papers%20pdf/noisecon_2004_paper.pdf | ◎ | PDF 抽出・式 1〜10 |
| 11 | EMD「The International rule DIN ISO 9613-2」windPRO 4.1 Appendix A DECIBEL | https://help.emd.dk/knowledgebase/content/windPRO4.1/Appendix_A_DECIBEL.pdf | ◎ | PDF 抽出・式 2〜9(ISO の式の写しとしては ○) |
| 12 | Wölfel ほか 2002 AR-INTERIM-CM WP 3.4.1「Description of the calculation method ISO 9613-2」 | https://loja.schiu.com/utilidades/artigos/GTEuropeu-DescricaoISO9613-2.pdf | ◎ | PDF 全文 |
| 13 | Maekawa Z. 1968「Noise reduction by screens」Applied Acoustics 1:157-173 | https://doi.org/10.1016/0003-682X(68)90020-0 | × | 未読(#10 の記述のみ) |
| 14 | Kurze U.J., Anderson G.S. 1971「Sound attenuation by barriers」Applied Acoustics 4(1):35-53 | - | △ | #10 の式 9・10 による二次 |
| 15 | Davies H.G.「Noise propagation in urban and industrial areas」(NASA NTRS 19770003379・年は本文から読めず=空欄) | https://ntrs.nasa.gov/api/citations/19770003379/downloads/19770003379.pdf | ◎ | PDF 抽出・角の節 |
| 16 | Brungart D.S. ほか 2020「Objective Assessment of Speech Intelligibility in Crowded Public Spaces」Ear & Hearing | https://pmc.ncbi.nlm.nih.gov/articles/PMC7676620/ | ○ | 全文 HTML を要約モデル経由で逐語 |
| 17 | Bottalico P. ほか 2017「Evaluation of the starting point of the Lombard Effect」Acta Acustica united with Acustica | https://pmc.ncbi.nlm.nih.gov/articles/PMC5612409/ | ○ | 同上 |
| 18 | Bottalico P., Piper R.N., Legner B. 2022「Lombard effect, intelligibility, ambient noise, and willingness to spend time and money in a restaurant amongst older adults」Scientific Reports 12:6549 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9023576/ | ○ | 同上 |
| 19 | Hodgson M., Steininger G., Razavi Z. 2007「Measurement and prediction of speech and noise levels and the Lombard effect in eating establishments」JASA 121(4):2023-2033 | https://doi.org/10.1121/1.2535571 | △ | Europe PMC の抄録・勾配 0.69 は #8 の記述 |
| 20 | Lane H., Tranel B. 1971「The Lombard sign and the role of hearing in speech」JSHR 14:677-709 | https://doi.org/10.1044/jshr.1404.677 | △ | 検索の要約と #8 の記述のみ |
| 21 | Plomp R. 1986「A signal-to-noise ratio model for the speech-reception threshold of the hearing impaired」JSHR 29(2):146-154 | https://doi.org/10.1044/jshr.2902.146 | △ | Europe PMC の抄録 |
| 22 | Schädler M.R. 2021「Thoughts on the potential to compensate a hearing loss in noise」F1000Research 10:311 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8524304/ | ○ | 全文 HTML を要約モデル経由 |
| 23 | 近藤和弘・泉良・藤森雅也・加賀類・中川清司 2007「二者択一型日本語音声了解度試験方法の検討」日本音響学会誌 63(4):196-205 | https://doi.org/10.20697/jasj.63.4_196 | ○ | 走査 PDF の図 8〜12 を目で読んだ(値は読み取りの近似) |
| 24 | 星野康・森本政之・佐藤逸人・佐藤洋 2012「単語了解度によるスピーチプライバシーの評価」神戸大学大学院工学研究科・システム情報学研究科紀要 4:1-6 | https://hdl.handle.net/20.500.14094/81004234 | ◎ | PDF 全文 |
| 25 | 李孝珍・坂本慎一・菅原彬子・池田佳樹 2019「駅コンコースにおける音環境評価のための実測調査および聴感評価実験」日本建築学会環境系論文集 84(765):983-991 | https://doi.org/10.3130/aije.84.983 | △ | J-STAGE の抄録 |
| 26 | 岡田駿太郎・森地茂・家田仁 2019「鉄道駅ホームにおける音環境の分析」土木計画学研究・講演集 60 | http://library.jsce.or.jp/jsce/open/00039/201912_no60/60-25-08.pdf | × | 接続できず(検索の要約のみ) |
| 27 | Wenmaekers R.H.C., Hak C.C.J.M.「Spatial decay rate of speech in open plan offices: the use of D2,S and Lp,A,S,4m as building requirements」(akutek 掲載) | https://www.akutek.info/Papers/RW_speech_spatial_decay.pdf | ◎ | PDF 抽出(本文の数値) |
| 28 | ISO 3382-3 Open-plan offices | (有料) | △ | 検索の要約のみ |
| 29 | Wikipedia「Critical distance」「Reverberation」 | https://en.wikipedia.org/wiki/Critical_distance ・ https://en.wikipedia.org/wiki/Reverberation | ○ | 要約モデル経由(百科の二次) |
| 30 | Valve「Steam Audio Source」Unity 版の説明書 | https://valvesoftware.github.io/steam-audio/doc/unity/source.html | ○ | 要約モデル経由で逐語 |
| 31 | Audiokinetic Wwise の obstruction/occlusion の説明(Unity 版・Q&A) | https://www.audiokinetic.com/qa/155/occlusion-and-obstruction | △ | 検索の要約のみ(説明書の頁は 403) |
| 32 | Raghuvanshi N. ほか「Project Triton: Pre-computed Environmental Wave Acoustics」(Gears of War の講演資料) | https://cdn.gearsofwar.com/thecoalition/publications/Raghuvanshi_Nikunj_Gears_Of_War.pdf | ◎ | PDF 抽出(スライド 2〜65) |
| 33 | Aranha C., Matsushima H., Kanoh H. 2017「Information Exchange Model for Multi-Agent Earthquake/Tsunami Evacuation Simulation」Journal of Natural Disaster Science 38(2):179-200 | https://doi.org/10.2328/jnds.38.179 | ◎ | PDF 抽出(§3.5・式 1 は一部欠落=空欄) |
| 34 | Gover B.N., Bradley J.S.「ASTM metrics for rating speech privacy of closed rooms and open plan spaces」Canadian Acoustics | https://jcaa.caa-aca.ca/index.php/jcaa/article/download/2405/2154/0 | ○ | PDF 抽出(表は画像で読めず・本文のみ) |
| 35 | ASTM E1130 Objective Measurement of Speech Privacy in Open Plan Spaces Using Articulation Index | https://store.astm.org/e1130-16r21.html | △ | 検索の要約のみ |
| 36 | (既存)[密度と可聴半径の検証](v2-density-hearing-verification.md) | リポ内 | 等級 B | 錨の再照合に使用(§0-1) |

本数: ◎ 11(#1・6・8・10・11・12・15・24・27・32・33)/ ○ 10(#4・5・16・17・18・22・23・29・30・34)/ △ 11(#3・7・9・14・19・20・21・25・28・31・35)/ × 3(#2・13・26)。#36 は既存答申。

### §0-1 既存答申の錨の再照合(答申 → 原典)

| 既存答申の記述 | 既存の等級 | 本書での原典照合 | 判定 |
|---|---|---|---|
| ANSI S3.5 の声 Normal 60 / Raised 67 / Loud 74 / Shout 82 dBA(Sensors 2025 経由) | 要約読 | #6 表 1 の A 特性合計 59.5 / 66.5 / 73.7 / 82.3 dB(1 m・口の正面) | 丸めた値として整合 ✓。ただし既存の「60」は ISO 9921 の普通 60 とも同じ数で、系統の区別が要る |
| Lombard 開始 45 dBA・話し声 55 dBA(Rindel) | 実読(Leembruggen 経由) | #8 本文「The Lombard effect starts at a noise level around 45 dB and a speech level of 55 dB」と式 (1) | ✓ |
| Rindel 統計法 L_NA = 93 + 20 lg(Ns/A) | 実読(Leembruggen 経由) | #8 式 (2)「L_N,A = 93 − 20 lg(A/N_S)」 | ✓(同じ式の書き換え) |
| Hodgson 0.69 dB/dB | 実読(Leembruggen の表) | #8 本文「the Lombard slope was on average 0.69, and the group size was around 3」 | ✓(ただし Hodgson 本文は未読=△) |
| Bottalico 2017 変化点 43.3 dB(A)・勾配 0.24 / 0.65 | 要約読 | #17 で同じ値と 95% 区間 41.0〜45.6 | ✓ |
| Brungart 2020 の SNR 低下 0.44 dB/dB・会話間隔 約 1 m | 要約読 | #16 で同じ値。間隔は「着席したまま」の指示による(騒音で変わらない設計) | ✓・**注記を追加**: 間隔 1 m は実験の条件で、自由に近づける場面の値ではない |
| 「ISO 9921 の距離表は読めていない」 | 空欄 | 本書でも読めず(有料・走査写しのみ) | 空欄のまま |
| 会話の SNR 閾値 0 dB・検知 −10 dB(既存答申の自前の設定) | 自前 | #8 表 3(Lazarus): −3 dB 以上で「足りる」、0〜3 dB「満足」 | 0 dB は錨のある段に乗る。−10 dB の検知は錨なし(expedient のまま) |

---

## §1 声の大きさ(1 m での A 特性音圧レベル)

### 1-1 規格と実測の値

| 段 | ISO 9921 附属書 A(男性・#6 表 2)/ Lazarus(#8 表 2) | ANSI S3.5 の標準スペクトル(A 特性合計・#6 表 1) | ANSI S3.5 の合計(無補正・#4) | Pearsons 1977 無響室(#1 表 5・女性/男性/子ども) |
|---|---|---|---|---|
| ささやき・小声 | 36・42(Lazarus) | - | - | - |
| ゆったり(relaxed)・雑談(casual) | 54(Lazarus は 48 を relaxed、54 を relaxed/normal とする) | - | - | 50 / 52 / 53 |
| ふつう | 60 | 59.5 | 62.35 | 55 / 58 / 58 |
| 少し大きい(raised) | 66 | 66.5 | 68.34 | 63 / 65 / 65 |
| 大声(loud) | 72 | 73.7 | 74.85 | 71 / 76 / 74 |
| とても大きい(very loud) | 78 | - | - | - |
| 叫び声(shout) | 84(Lazarus) | 82.3 | 82.30 | 82 / 89 / 82 |
| 最大の叫び | 90(個人では 96)(Lazarus) | - | - | - |

- #6: 「Vocal effort ... quantified objectively by the A-weighted speech level at 1 m distance in front of the mouth」。ANSI の元データは「sound pressure levels (SPL) at a distance of 1 m in front of the speaker's lips in the free field」。同じ表に**音響パワー**も載る(ふつう 68.4・少し大きい 75.5・大声 82.6・叫び声 91.0 dB)。群衆の背景の計算には音響パワーの方を使う(#6)。
- #1: 「Casual speech during conversation was approximately 5 dB weaker than normal vocal effort」。「Raised speech was approximately 7 dB more intense than normal speech, and loud speech was elevated by another 11 dB by the males and 8 dB to 9 dB by the females and children. Shouted speech increased by an additional 8 dB to 13 dB」。
- #8: 「Vocal effort is ranged and labelled in steps of 6 dB」「By shouting, the SPL can reach 84 dB to 90 dB, and in private communication (whispering or soft speech) typical levels are 35 dB to 50 dB」。
- **叫び声は聞き取りにくくなる**: ISO 9921 附属書 A は、1 m の声が 75 dB を超えるとき、STI の計算で声を ΔL = 0.4 (L_S,A,1m − 75) dB だけ下げると定める(#6。叫び声 82.3 dB なら 2.9 dB 下げる例が載る)。
- **日本語話者の努力段ごとの 1 m の値: 空欄**(J-STAGE の検索で見つからず)。

### 1-2 実際の場面で人が使う声(Pearsons の現場の測定・#1)

| 場面 | 背景(dBA) | 声(1 m に換算・dBA) | 会話の距離 | 聞き手の位置の SNR |
|---|---|---|---|---|
| 郊外の家(屋内/屋外) | 41 / 48 | 55 / 55 | 約 1 m(自分で選んだ「ふつうの距離」) | +14 / +8 dB |
| 都市の家(屋内/屋外) | 48 / 61 | 57 / 65 | 約 1 m | +9 / +5 dB |
| 病院(病室/詰所) | 45 / 52 | 56 / 56 | - | +10 / +5 dB |
| 百貨店 | 54 | 58 | 1 m より近い | 約 +7 dB |
| 電車 / 飛行機 | 74 / 79 | 66 / 68 | 0.4 m(方法の節では約 0.5 m) | −1 / −2 dB |

- #1 のまとめ: 「In most settings, speech levels were between 55 and 66 dBA at conversation distances ... S/N ratios on the order of 5 to 15 dB were maintained」。電車と飛行機では近づいても SNR が負のまま会話している。
- 教室の教員は背景 45〜55 dBA の範囲で「approximately 1 dB for each dB increase in noise level」声を上げた(#1)。

## §2 距離による減衰・地面・空気

### 2-1 点音源の逆二乗

- ISO 9613-2 の幾何発散: **A_div = 20 lg(d/d₀) + 11 dB**(d₀ = 1 m。#11 の式 6。11 は音響パワーから 1 m の音圧への換算)。1 m の声の値 L₁ から始めるなら **L(r) = L₁ − 20 lg(r/1 m)**(距離が倍で −6 dB)。
- #8 も同じ前提で「Reducing the distance from 1 m to 0.7 m means a 3 dB better SNR, and coming as close as 0.5 m yields another 3 dB improvement」。
- **向き**: 口の正面の値。#8 は話し手の指向係数 Q = 2(正面)を置く。後ろ側の値の錨: 空欄(#6 は Chu & Warnock 2002 を挙げ「directivity is not significantly affected by vocal effort, gender, or language」と書くが、数値は本書で未読)。

### 2-2 地面の影響(ISO 9613-2 の簡便式)

- 地面の減衰(A 特性の簡便式・#11 式 8): **A_gr = 4.8 − (2 h_m / d)[17 + (300 / d)] ≥ 0 dB**(h_m = 音の通り道の平均の高さ)。負になれば 0。
- 硬い地面で音源が地面に近いときの見かけの増し分(#11 式 3): **D_Ω = 10 lg{1 + [d_p² + (h_s − h_r)²] / [d_p² + (h_s + h_r)²]}**。
- 当てはめ(推測): 口と耳の高さ 1.5 m・距離 3 m では A_gr の式は −112 dB で 0 になる。30 m でも +2.1 dB にとどまる。D_Ω は距離 1 m で 0.4・3 m で 1.8・10 m で 2.8・30 m で 3.0 dB。**会話の距離では地面は「+0〜3 dB の増し」として効き、減衰としては効かない**。
- 街の谷(両側のビル)の反射の増し分 +6〜8 dB は既存答申にある(Sensors 2025・要約読)。本書では原典を読み直していない。

### 2-3 空気の吸収

- **A_atm = α d / 1000**(#11 式 7)。10 °C・湿度 70% の α は 500 Hz で 1.9、1 kHz で 3.7、2 kHz で 9.7、4 kHz で 32.8 dB/km(#11 の表。#11 は「this table was included in earlier versions of the ISO 9613-2 standard」と書く)。
- 当てはめ(推測): 4 kHz でも 10 m で 0.33 dB、50 m で 1.6 dB。**会話と傍受の距離(数十 m まで)では無視してよい**。

## §3 建物の陰(回折)

### 3-1 式

- フレネル数 **N = 2δ/λ**(δ = 回り道の長さ − 直線の長さ)。Maekawa 1968 は遮音壁の測定から N と減衰の関係を図にした(#13・未読)。
- **Kurze–Anderson の近似**(#10 式 9・10): **D = 5 + 20 lg[√(2πN) / tanh √(2πN)] dB**。N = 0(ちょうど視線をかすめる)で 5 dB。#10 は「The above formulations are Kurze curve fits to Maekawa's data」と書く。簡単な形 10 lg(3 + 20N) もある(検索の二次。N > 1 で上とほぼ同じ)。
- **ISO 9613-2 の遮蔽**(#10 式 3〜8): **D_z = 10 lg(3 + (C₂/λ) C₃ z K_met)**。C₂ = 20(地面の反射を含む場合)・C₃ = 1(1 回の回折)・z = 回り道の差・K_met は気象の補正(縦の縁を回る横の回折では 1)。上の縁を越えるときは **A_bar = D_z − A_gr**、横の縁を回るときは **A_bar = D_z**。#10: 「For single screens, ISO 9613-2 suggests limiting the maximum attenuation calculated to 20 dB while for multiple screens it suggests 25 dB」。
- EU の写し(#12)の注: 回り道の差が −λ/20(500 Hz で −0.034 m)より小さければ回折の計算は要らない。A 特性しか無いときは 500 Hz の減衰を使う(ISO の注 1 を「may」から「should」に直す提案)。式 12 の「> 0」の条件は誤りで外すべき、とも書く。
- 2024 年の第 2 版で D_z の形と K_met が書き換えられた(検索の二次・△。本文未読)。

### 3-2 会話の声に当てはめた試算(推測)

| 配置 | δ | 250 Hz | 500 Hz | 1 kHz | 2 kHz | 4 kHz |
|---|---|---|---|---|---|---|
| 角の手前 2 m・先 2 m(直角) | 1.17 m | 15.3 | 18.3 | 21.3 | 24.3 | 27.3 |
| 角の手前 5 m・先 5 m | 2.93 m | 19.3 | 22.3 | 25.3 | 28.3 | 31.3 |
| 視線をかすめた直後 | 0.05 m | 6.2 | 7.2 | 8.8 | 11.0 | 13.7 |

(Kurze–Anderson・音速 343 m/s。ISO の頭打ちを入れると 20 dB を超える欄は 20 dB)

### 3-3 当てはめるときの注意

- **周波数**: 明瞭度に効く帯域(2 kHz 付近)は 500 Hz より 6 dB ほど深く落ちる(上の表・推測)。A 特性 1 本で 500 Hz の値を使うと、**音量の下がりは合っても聞き取りの下がりを小さく見積もる**(推測)。帯域ごとに計算するか、聞き取り用に高い帯域の値を使うかを宣言する必要がある。
- **反射が影を埋める**: Davies(#15)「the nomogram of Lee and Davies predicts a drop of between 10 and 20 dB as the receiver "turns" a corner away from a source. This is consistent with measured values. However, the amount of the drop depends very much on the absorption coefficient; high absorption coefficients give large drops」。渋谷の路地のように壁の硬い谷では、回折だけの計算(上の表)は下がりを大きく見積もるおそれがある(推測)。
- **屋根越し**: ISO の式は屋根を越える道と横を回る道を両方考える。渋谷の建物は人の背より十分高いので、屋根越しの道は 20 dB の頭打ちに張り付き、効くのは横の縁(建物の角)を回る道になる(推測)。
- 建物の高さと平面形: W8 は W4 の建物を 2.5 m 格子に塗った「建物頂部の高さ場」を持ち、視線の遮蔽を numba で判定している(視線 1 本を 2.5 m 刻みで標本化)。角の位置そのものは格子に無いので、回り道の差 δ を出すには建物の多角形の頂点が要る(推測)。

## §4 背景の騒がしさ

### 4-1 道路(W10)

- W10 の出力は街路の 2.5 m 格子の**昼と夜の等価騒音レベル L_Aeq**(ASJ RTN-Model 2018 の非定常式・車線ごとの線音源・昼 12 時間 7〜18 時と夜の一様配分)。uint8 の dB で ±0.5 dB の量子化(w10_ruler.py の注)。
- 意味の注意: L_Aeq は時間平均で、車が通る瞬間の大きさ(L_A,max)とは違う。会話の 1 発話のあいだの背景としては平均の値を使うのが ISO 9921・Rindel の流儀(どちらも A 特性の背景レベルで SNR を定義・#8)。通過の瞬間の妨害は扱わない(推測)。
- W10 の宣言済みの近似: ΔL = 0(遮音壁・反射・地面の効果なし)・較正点の残差 渋谷区 3 点 ±1.4 dB ほか(構築仕様 §C1)。

### 4-2 周りの人の話し声(群衆)

- **屋内(拡散音場)**: Rindel(#8 式 2・3): **L_N,A = 93 − 20 lg(A/N_S) = 93 − 20 lg(A g / N)**、**A = 0.16 V/T + A_p N**。N_S = 同時に話す人の数、g = N/N_S(話す人 1 人あたりの人数・飲食店で 3.5 を推奨・3〜4 が典型)、A_p = 1 人あたりの吸音(0.2〜0.5 m²)。「the ambient noise level increases by 6 dB for each doubling of number of individuals present」。精度は「the prediction method may have an uncertainty of ± 3 dB」、「it may not apply to small rooms with a capacity less than, say 30 persons」。検証: 食堂 1,235 m³・T 0.47 s で g = 3.5 が最良、宴会場 3 室で実測との差 1 dB 以下(#8 §5)。
- この式は Lombard 勾配 0.5 を入れた後の閉じた形(#8「the Lombard slope had to be 0.5; this was the only value that made a reasonable good fit」)。勾配を変えた閉形式は既存答申の Leembruggen 式 5・7 にある。
- **屋外の歩行者の街路**: 密度からの式(Meng & Kang 2015 の実測回帰・エネルギー和・発話率の負帰還)は既存答申にある。本書では足さない。
- **音楽などの別の背景**: Rindel 式 6 は、音楽のエネルギー E_M と話し声だけの背景 E_N から、Lombard を含めた合計 L_N,Total = 10 lg[E_M + 0.5 E_N (1 + √(1 + 4E_M/E_N))] を出す。背景音楽の推奨上限は 60〜65 dB(#8 §6.3)。
- **カクテルパーティー効果**: Rindel は Cherry 1953 を挙げ、人は 1 つの声に注意を向けて他を背景として抑えられると書く(#8 §3)。ただし Rindel の SNR の計算は他の声を背景のエネルギーとして全部数える。抑えの量(dB)の錨: 空欄。

### 4-3 駅の放送

- 首都圏 8 駅のコンコース 30 点(#25・抄録): 背景は大半の点で 65〜70 dB、最大 72.4 dB。利用者の少ない駅は 54.7〜60.6 dB と 64.4〜66.1 dB。**放送は背景より高いが、差は大半の点で 10 dB 以内**。同じ点でも内容で放送の大きさが変わり、差は 11 点で平均 5 dB 超・最大 13.1 dB。うるささは放送 74 dB で「少し」、82 dB で「ある程度」、90 dB で「とても」。放送と背景の差 +10 dB でも、女性の放送で約 29%、男性で 50% が「聞き取りにくい」と答えた。
- ホームの朝の放送が 90 dB を超える例(#26): 未読(空欄)。
- 渋谷駅の放送の実測: 空欄。

## §5 聞き取れるか(明瞭度)

### 5-1 指標の概要

- **SII(ANSI S3.5-1997)**: 帯域ごとに「声 − 背景」を 0〜1 に写し、帯域の重要度で重み付けして足す。MATLAB 実装(#5): **K = (E − D + 15)/30**、0〜1 に切る、**A = L·K**、**SII = Σ I·A**(E = 声のスペクトルレベル、D = 背景と自己マスキングの大きい方、I = 帯域の重要度、L = 声が大きすぎるときのひずみの係数)。つまり帯域の SNR が −15 dB で 0、+15 dB で 1 になる。
- **STI(IEC 60268-16)**: 0〜1。評価の段(#6 表 6・ISO 9921 から): 優 > 0.75(意味のある PB 単語の正答 > 98%)・良 0.60〜0.75(93〜98%)・可 0.45〜0.60(80〜93%)・劣 0.30〜0.45(60〜80%)・不可 < 0.30(< 60%)。人と人の会話の最低の推奨(#6 表 8): 長いふつうの会話で「良」・ふつうの声、大事な会話で「可」・大声。
- 日本語では、残響と騒音が同時にあると STI が了解度を反映しない、という報告がある(日本建築学会の論文・検索の要約のみで未読。数値は空欄)。

### 5-2 SNR と聞き取りの目安

| 錨 | 内容 | 出典・等級 |
|---|---|---|
| 会話の質の段(Lazarus) | とても悪い < −9・不足 −9〜−3・足りる −3〜0・満足 0〜3・良い 3〜9・とても良い > 9 dB。「focus on the border between sufficient and insufficient, i.e. SNR = −3 dB」 | #8 表 3 ◎(Lazarus 原典は未読) |
| 高齢者・母語でない人 | 「require a higher signal-to-noise ratio (approximately 3 dB)」(ISO 9921 §5.1 の引用) | #8 ◎(ISO は △) |
| 混んだ公共の場の実測(MRT・英語) | 60 dBA 未満は約 95% 正答。60 dBA 超では SNR −5 dB で約 82%、+10 dB で約 95%。背景 85 dBA 超で平均 80% 未満。背景 75 dBA 付近で SNR が 0 を下回る | #16 ○ |
| 文の聞き取り閾値(50%・ドイツ語の文・定常雑音) | 健聴者の SRT は約 −7 dB | #22 ○ |
| Plomp の SRT の模型 | 健聴の SRT を「静かなときの閾値」と「高い騒音での SNR」の 2 つで表す模型。式の本文と −5 dB 前後という値は未確認 | #21 △(式は空欄) |
| 日本語 DRT(2 択・語頭子音)| 平均の正答(偶然を補正)を図 8 から読むと、白色雑音で SNR −15/−10/0/+10 dB に約 20/37/69/89%、擬似音声雑音で約 26/48/85/96%、多人数の話し声の雑音で約 37/61/89/97% | #23 ○(図の読み取り) |
| 日本語の単語(親密度の高い 4 モーラ・書き取り) | SNR −20 と −15 dB で了解度は 0% 近く、±0 dB で 100% 近く、−10 と −5 dB はその間。SNR は声の最大値(Slow)と背景の中央値の差で定義 | #24 ◎ |
| 会話の内容が漏れない(スピーチプライバシー) | ASTM E1130: AI ≤ 0.05 で「confidential」、0.05〜0.20 で「normal」。PI = (1 − AI)×100 で、「Confidential Speech Privacy (PI = 95%)」 | #34 ○・#35 △ |

- 注意: 錨ごとに SNR の定義が違う(帯域ごとか A 特性の合計か、声の平均か最大か、2 択か書き取りか)。#24 の SNR は声の最大値を使うので、平均の声で定義した SNR より数 dB 大きく出るはず(推測。差の量は空欄)。

### 5-3 「会話の距離」との突き合わせ(Rindel 表 6 の再計算)

- Rindel の式 1(Lombard)と直接音の逆二乗を合わせると、**SNR = 32.5 − 0.5 L_N − 20 lg(r/1 m)**(L_N > 45 dB のとき)になる(推測で導出)。表 6 の 4 隅(53 dB・0.35 m で 15、71 dB・1 m で −3、89 dB・0.35 m で −3、53 dB・2 m で 0)と、確かめた欄はすべて一致した。
- #8 の例: 「In the distance r = 1.0 m the corresponding ambient noise level is 71 dB」(−3 dB の境)。10 人の丸テーブルで向かい側(2 m)と話すには背景 59 dB 以下が要る。背景 77 dB では隣(0.5 m)としか話せない。
- #16: 先行研究は背景 75 dBA を超えると人が 0.5 m まで近づくと予測する、と書く。

## §6 ロンバード効果(うるさいと声が大きくなる)

| 錨 | 値 | 出典・等級 |
|---|---|---|
| 式 | L_S,A,1m = 55 + c (L_N,A − 45)(背景 45 dB 超) | #8 式 1 ◎ |
| 勾配 0.5 | Webster & Klumpp 1962、Gardner 1971(食堂と懇親会)、Bronkhorst が Lane & Tranel を引いて 0.5 を確認 | #8 ◎(各原典は未読) |
| Lazarus の総説 | 0.5〜0.7(#8)/「0.3–0.6 dB per noise level rise of 1 dB for all disturbing noise exceeding 40–50 dB(A)」(#17 の引用) | #8 ◎・#17 ○(Lazarus 原典は未読) |
| Hodgson 2007(飲食店 10 軒の最適当てはめ) | 平均 0.69・話す人 1 人あたり約 3 人・1 人あたり吸音 0.1〜1 m² | #8 ◎・#19 △ |
| Bottalico 2017(若い成人 20 人・ピンク雑音) | 変化点 43.3 dB(A)(95% 区間 41.0〜45.6)・下 0.24・上 0.65 dB/dB | #17 ○ |
| Bottalico 2018・2022 | 大学生: 変化点 57.3・下 0.31・上 0.54。60 歳超 31 人: 変化点 58.3(53.4〜63.3)・下 0.27・上 0.51。難聴の有無で差なし | #18 ○ |
| 混んだ公共の場の実測 | SNR が背景 1 dB あたり 0.44 dB 下がる(60 dBA 超)。声の上昇に直すと約 0.56 dB/dB(推測) | #16 ○ |
| Pearsons の教室 | 背景 45〜55 dBA で約 1 dB/dB | #1 ◎ |
| Lane & Tranel 1971 | 総説。勾配は動機(伝わることをどれだけ重んじるか)で変わると論じる、と二次の記述。数値の原典確認は空欄 | #20 △ |
| 頭打ち | 叫び 84〜90 dB・最大の叫び 90 dB(個人で 96)。75 dB を超えると聞き取りにくくなる(ISO の ΔL = 0.4 (L − 75)) | #8 ◎・#6 ◎ |

- 含意: **Lombard 勾配 c が 1 未満なので、背景が上がるほど SNR は下がる**。c = 0.5 なら背景 +10 dB で SNR −5 dB、届く距離は 0.56 倍(推測)。勾配の候補は 0.44〜0.69 の幅があり、感度の腕にできる。
- 変化点は 43〜58 dB(A) と研究で幅がある。Rindel の 45 dB はその下の端。

## §7 屋内

### 7-1 式

- **Sabine**: T = 0.161 V / (S ā)(#29)。等価吸音面積に直すと **A = 0.16 V/T**(#8 式 3。在室者の分 A_p N を足す)。
- **直接音と残響音**: Hopkins–Stryker の形 L_p = L_W + 10 lg(Q/(4πr²) + 4/R)(R = 室定数)。式の写しは検索の二次(△)で原典は未読。
- **臨界距離**(直接音と残響音が等しい距離): **d_c = (1/4)√(γA/π) ≈ 0.057 √(γV/T)**(#29)。
- **Rindel の会話の SNR**(#8 式 4): **SNR = 10 lg(Q A g / (16π r² N))**(Q = 2)。「This formula applies to A-weighted ambient noise levels between 45 dB and 85 dB ... The corresponding SNR range is from – 10 dB to +10 dB」。全員が同じ Lombard で声を上げるので、SNR は Lombard の影響を受けない(#8)。
- **音響容量**(#8 式 5): 1 m で SNR −3 dB(背景 71 dB)を保てる最大人数 **N_max ≈ V/(20T)**(g = 3.5・A_p = 0.35 m²)。「When a restaurant is fully occupied, it is typical that the acoustic capacity is exceeded by a factor of 2 or more」。

### 7-2 既定値の候補(錨のある係数)

| 係数 | 値 | 出典 |
|---|---|---|
| 1 人あたり吸音 A_p | 0.2〜0.5 m²(服装による)。音響容量の式では 0.35 | #8 ◎ |
| 話す人 1 人あたりの人数 g | 3.5(飲食店の推奨)。食事の初めは 4、後半は 3 に合う | #8 ◎ |
| 飲食店の残響時間の等級(T ÷ 1 人あたり容積) | A 0.025・B 0.040・C 0.063・D 0.100 s/m³。満席で 1 m の SNR は A 0・B −2・C −4・D −6 dB | #8 表 7 ◎ |
| 実例の残響時間 | 食堂 1,235 m³ で 0.47 s。宴会場 2.5 s・0.8 s・1.0 s。8,265 m³ のホールで 3.9 s | #8 ◎ |
| 必要な吸音の目安 | 1 人あたり 3.5 m² 以上(De Ruiter) | #8 ◎(原典未読) |
| オープンオフィスの距離減衰 D₂,S | 実測 4.2〜5.6 dB(自由音場の 6 dB より小さい)。良い条件の例 ≥ 7 dB・悪い条件の例 < 5 dB | #27 ◎・#28 △ |
| オフィス・飲食店の日本の典型的な残響時間 | 空欄 | - |

- 当てはめの注意: Rindel の統計法は「30 人未満の小さな部屋には合わないかもしれない」(#8)。小さな店の席ごとの会話は直接音の式(§5-3)で足りる(推測)。

## §8 計算の費用(すべて推測)

- **対の数**: 1 窓に話している人 S 人 × 聞き取りの候補の範囲にいる人 k 人。範囲の上限は「叫び声が静かな場所で −15 dB まで落ちる距離」で決まる(§10-3 の R_max)。例として S = 1 万・k = 30 なら 30 万対/窓。
- **1 対の計算**: 距離・log10・背景の格子の読み(W10 と群衆の背景の表)・閾値の比較で数十 ns。視線の遮蔽の判定を W8 と同じ方法(2.5 m 刻みの標本で建物頂部の高さ場を読む)で行うと、距離 20 m で 8 標本。numba で 1 対 50〜200 ns とすると 30 万対で 15〜60 ms/窓。
- **回折**: 視線が切れた対だけ、近くの建物の角(多角形の頂点)を探して δ を出す。候補の頂点が数十なら 1 対あたり上の 10〜100 倍。切れる対の割合が 1〜2 割なら、全体で 2〜20 倍になる。安く済ませる案は「視線が切れたら一律 10〜20 dB 下げる」(Davies の幅)で、これは expedient として宣言が要る。
- **事前計算(G13 と共用)**: W8 の T2(セル → セル・約 140 MB)は「見えるか」の表なので、音にはそのまま使えない(回り込みがある)。セル対ごとの「回折込みの減衰」の表を前計算すると、ランの中は表引きになる。ただし容量は T2 と同じ桁になる。
- **背景の計算**: 群衆の話し声の背景は既存答申の 1 次元表(LUT)で 1 回の補間。2.5 m 格子・渋谷区全域で GPU 0.04 ms・CPU 1 コア 82 ms/更新(既存答申の試算)。

## §9 先行例(ゲーム・VR と社会シミュレーション)

- **obstruction と occlusion**: Triton の講演(#32): 「Obstruction ~ initial (direct) sound energy / Occlusion ~ initial (direct) + reflected (indirect)」。CryEngine の Wwise 連携の説明(検索の要約・△)では obstruction は乾いた音だけに、occlusion は残響へ送る前の音に掛かる。Wwise はこれを**音量の減衰と低域通過フィルタの曲線**で表す。値の計算(光線など)はゲーム側の仕事で、Wwise 自体は幾何を見ない(#31・△)。
- **Steam Audio**(#30): 距離の減衰の「Physics Based」は「This is an inverse distance falloff」。遮蔽は「Raycast」(1 本の光線で遮られたか)と「Volumetric」(音源の周りの球へ複数の光線を飛ばし、遮られた割合を出す)。透過は遮られた部分だけに掛ける。空気の吸収は「an exponential falloff」で高い音ほど速く落ちる。Pathing は音源から聞き手への最短の道を計算する。
- **Triton(焼き込み型)**(#32): 静的な地形で波動計算を前もって行い、ランの中は表引きと補間。「Efficient CPU: ~100μs for acoustic lookup」「RAM: ~100MB for Campaign」。焼き込みは「100 machines ~4 hours」。物理の 100 dB の幅をゲームの 25 dB の幅に詰め直して使った。**v2 の G13(物理は事前計算・ランは表引き)と同じ考え方**である。
- **避難のエージェント模型**(#33): 声のやりとりを模型に入れた例。式 1 は「a_ij^m = Asound_m − 20 log10 d_ij」(点音源・反射も回折もなし)を使い、群衆の密度 c_j と組み合わせて伝わる確率を出す。錨は近藤ほか 2007 の日本語了解度(#23)と繁華街の平均の騒音。声の大きさは避難者 85・誘導員 105・拡声車 115 dB。「buildings and obstructions do not affect sound transmission directly」。確率の式の全体は抽出で欠けた(空欄)。
- 群衆の音のミドルウェア(CRI の Crowd System)が密度 3 段の素材を混ぜるだけで物理の則を持たない点は既存答申にある。

## §10 v2 への当てはめ(リサーチ役の自前構成・expedient・親とユーザーが決める)

### 10-1 「聞き取れる」の最小の式(案)

```
声     L_S = clamp( L_eff(段) + c · max(0, L_N,話し手 − L_0), 上限 L_max )      [1 m・A 特性]
届く   L_R = L_S − 20 lg(r / 1 m) − A_bar(回折) + D_Ω(地面 0〜3) − A_atm(≈0)
背景   L_N,聞き手 = 10 lg( 10^(L_W10/10) + 10^(L_群衆/10) + 10^(L_放送/10) + … )
判定   SNR = L_R − L_N,聞き手  ≥ θ
```

- 屋内は背景を Rindel 式 2・3 で出し、SNR を式 4(直接音 ÷ 残響音)か上の式で出す。
- 閾値 θ を確率にするなら、SNR に対するロジスティック曲線を日本語の錨(#23・#24)か英語の実測(#16)に当てる案がある(B4 の「区切りでなく連続の確率」と同じ形)。

### 10-2 本人が選べる行動との接続(案)

- エンジンは本人に「聞き取りやすい / 聞き取りにくい / 聞こえない」を知覚として渡す。数値は渡さない。
- 本人(決定モデル)が選ぶ: **近づく**(r を半分で SNR +6 dB)・**声を張る**(段を 1 つ上げて +6 dB。叫び声は ISO の ΔL で効きが下がる)・**静かな場所へ移る**(L_N が下がる)・**やめる**。
- Lombard の分は本人が選ばない自動の分(c)として入れる。選ぶ分(段)と分ける。

### 10-3 傍受(案)

- 会話の各発話について、話し手から R_max の範囲にいる周りの人に同じ式を当てる。SNR ≥ θ_内容 なら内容を知覚し、θ_存在 ≤ SNR < θ_内容 なら「誰かが話している」だけを知覚する。
- θ_内容 の錨: 会話の閾値と同じ(−3 または 0 dB)。θ_存在 の錨: 日本語の単語は −15 dB 以下で 0% 近く(#24)。「話していると分かる」閾値そのものの錨は空欄。
- 傍受の距離の試算(推測・ふつうの声・Lombard 0.5): SNR −10 dB まで内容が漏れるとすると、背景 45 dB で 10 m、65 dB で 3.2 m、75 dB で 1.8 m。

### 10-4 届く距離の試算表(推測・直接音のみ・地面と反射なし)

L_eff = 55 dB(Rindel の基準)・c = 0.5・L_0 = 45 dB。数値は SNR ≥ 0 / ≥ −3 dB で届く距離 [m]。

| 背景 L_N | ふつう | +6 dB(少し大きい) | +12 dB(大声) | +24 dB(叫び声相当) |
|---|---|---|---|---|
| 40 dB | 5.6 / 7.9 | 11 / 16 | 22 / 32 | 89 / 126 |
| 45 dB | 3.2 / 4.5 | 6.3 / 8.9 | 13 / 18 | 50 / 71 |
| 55 dB | 1.8 / 2.5 | 3.5 / 5.0 | 7.1 / 10 | 28 / 40 |
| 65 dB | 1.0 / 1.4 | 2.0 / 2.8 | 4.0 / 5.6 | 16 / 22 |
| 75 dB | 0.56 / 0.79 | 1.1 / 1.6 | 2.2 / 3.2 | 8.9 / 13 |
| 85 dB | 0.32 / 0.45 | 0.63 / 0.89 | 1.3 / 1.8 | 5.0 / 7.1 |

- 叫び声の欄は上限(90 dB)と ISO の ΔL を入れていない。入れると短くなる。
- 街の谷の反射(+6〜8 dB・既存答申)を声だけに足すと距離は 2〜2.5 倍に延びる。ただし背景の道路と群衆も同じだけ増えるので、SNR への効き方は配置しだい(推測)。

### 10-5 宣言する係数の一覧(案)

| 係数 | 既定の候補 | 感度の腕の候補 | 錨 |
|---|---|---|---|
| 声の段の値 L_eff | ISO 9921 の 6 dB 刻み(ふつう 60)か Rindel の 55 | 55・60 と Pearsons の性別ごとの値 | §1 |
| 性別・年齢の差 | なし | Pearsons の男女差(大声で男性 +5 dB) | #1 |
| Lombard 勾配 c | 0.5 | 0.44・0.56・0.69 | §6 |
| Lombard の開始 L_0 | 45 dB | 43.3・57 dB | §6 |
| 声の上限 L_max | 90 dB | 84・96 | #8 |
| 叫び声の明瞭度の補正 | ΔL = 0.4 (L − 75) | なし | #6 |
| 話し手の指向 | 正面のみ(Q = 2) | 後ろ向きで下げる(値は空欄) | #8 |
| 地面 D_Ω | 硬い地面の式 | 0 | #11 |
| 空気 A_atm | 0 | - | §2-3 |
| 回折の式 | Kurze–Anderson・20 dB で頭打ち | 一律 10・20 dB(Davies) | §3 |
| 回折の帯域 | 500 Hz | 2 kHz | §3-3 |
| 街の谷の反射 | 0 | +6・+8 dB | 既存答申 |
| 会話の閾値 θ | −3 dB(足りる) | 0・+3 dB | #8 表 3 |
| 高齢者などの上乗せ | +3 dB | 0 | #8(ISO 9921 §5.1) |
| 傍受の内容の閾値 | 会話と同じ | −5・−10 dB | §5-2 |
| 存在だけ分かる閾値 | −15 dB | −10・−20 dB | #24(錨は弱い) |
| 屋内 A_p・g | 0.35 m²・3.5 | 0.2〜0.5・3〜4 | #8 |
| 屋内の残響時間 | Rindel 表 7 の等級 C(0.063 s/m³) | A〜D | #8 |
| 放送の大きさ | 背景 + 5〜10 dB | +13 dB | #25 |

## §11 空欄(見つからない・読めないもの)

1. 日本語話者の努力段ごとの 1 m の声の大きさ(§1-1)。
2. Pearsons 1977 の原報の本文(Lombard 0.6 dB/dB とする二次の記述の確認を含む)。
3. ISO 9921 の SIL 法と通話できる距離の表(有料・走査写しは文字なし)。
4. Plomp の SRT の式の本文と健聴者の −5 dB 前後という値(抄録のみ)。
5. Lane & Tranel 1971 の勾配の数値の原典確認。
6. ホームの放送 90 dB 超の原典(土木学会の講演集・接続できず)と渋谷駅の放送の実測。
7. Davies の文書の発行年。
8. Aranha ほか 2017 の伝達確率の式 1 の全体(抽出で欠落)。
9. 日本語の了解度と STI の対応の数値。
10. 日本の事務所・飲食店の典型的な残響時間。
11. SII でのスピーチプライバシーの閾値(SII ≤ 0.1・0.2 とする二次の記述の原典確認)。
12. 星野ほか 2012 の SNR(声の最大値)と平均の声で定義した SNR の差の量。
13. 話し手の向き(後ろ向き)による減衰の数値・カクテルパーティー効果の抑えの量(dB)・「話していると分かる」閾値の錨。

空欄の数: 13 項(13 は 3 点をまとめた)。
