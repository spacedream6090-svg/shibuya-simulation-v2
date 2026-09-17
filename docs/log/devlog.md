# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **2 / 10**
> 第1〜第210(2026-09-01〜09-17)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第211 R-4 ミクロ観察の先行例 帰還・親確認 3 件・D-80 新設(2026-09-17 夕)

- **R-4**([答申](../research/v2-micro-observation-research.md)・lit 6): GA=replay は「状態 1 JSON+アバタ全開示」・評価は「無作為の 1 体の一生の再生」・幻覚 453 中 1.3%(n=6)/ Concordia=entity×step×component のログ・replay の語なし / AgentSociety だけ個体と集計を分離・AgentTorch は 840 万体で個体検査を放棄 / ODD 2020 S1=Observation を design concept として持ち「個体を選んで trace」「中心傾向だけか分布も見たか」/ POM「1 パターンは誤った理由でも合う」/ MATSim Via=events 1 本から agent plan と facility の到着・出発・滞在 / de Montjoye=4 点で 95% 一意・1/10 乗則。**親確認 3 件**(ODD S1 逐語・GA §7.1・de Montjoye)。**非対称**: 個体×tick 全記録は 4.6 GB=S1 の 92%(不可)・場所カルテ 24 MB(全数可)→ 抽出規則が M1 の本体・**再生で事後に作れば追加ラン 0**。指紋は N=1,000 と店名伏せの 2 点。→ **D-80**(O1〜O20・親推奨=場所カルテ→個体生成器→CLI→HTML・規律先行)。
- devlog 第201〜210 を圧縮(第210b)。C9a 実装・R-3 実行中・seed 3 17:35。

## 第212 R-3 個体の同質性 残 10 件 帰還・親確認 3 件・D-81 新設(2026-09-17 夕)

- **R-3**([答申](../research/v2-d68-remaining-research.md)・lit 8・公的 xlsx 1 本 45 MB): 始業時刻の分布表は**存在しない**→代理=時間帯編 第15-4表(仕事率の階差・東京都 p10/p50/p90 7:15/8:45/10:00)/ 片道通勤時間は令和3年に無い→住宅・土地統計 表58-2-1(東京都 p50 43.7 分・渋谷区 33.0・自宅 5.07%)/ Schneider Fig.3 数値なし(追試 11〜17 型・83〜90%)/ Schlich & Axhausen 有料・「8.6/36」の出所不明 / **REAL Sampling(ベースの次トークン・App.J 9M トークン・90.2%)と 2605.09995(instruct の意味的多様性・「Larger base models are not less diverse, but larger post-trained models are」)は別の層**=8B 据置の根拠は後者 / 2604.01520「20–300 倍」は本文に裏づけ表なし / Lu 2013 Π_max 0.88・MC(1) 0.91 / 交替制の 0:00 仕事率=固定の 4.8 倍(全国)・14 倍(東京都)/ 日本 PT へのモチーフ適用=Pseudo-PFLOW / TrajLLM に定量評価なし。**親確認 3 件**(15-4 表を openpyxl で再計算=8.82/1.83・8.25/0.59 一致・REAL App.J・2605.09995 本文)。→ **D-81**(K-1〜K-5・親推奨=採用・K-5 は C9 の速度と同時に入れると二重に効くので順序を宣言)。
- 本日の高優先リサーチ 6 レーン(L-R8・L-C9・R-25・R-23 第2批・R-3・R-4)は全部帰還・親確認済み。C9a 実装中・seed 3 17:35。
