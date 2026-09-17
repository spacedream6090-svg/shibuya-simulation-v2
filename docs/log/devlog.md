# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **6 / 10**
> 第1〜第210(2026-09-01〜09-17)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第211 R-4 ミクロ観察の先行例 帰還・親確認 3 件・D-80 新設(2026-09-17 夕)

- **R-4**([答申](../research/v2-micro-observation-research.md)・lit 6): GA=replay は「状態 1 JSON+アバタ全開示」・評価は「無作為の 1 体の一生の再生」・幻覚 453 中 1.3%(n=6)/ Concordia=entity×step×component のログ・replay の語なし / AgentSociety だけ個体と集計を分離・AgentTorch は 840 万体で個体検査を放棄 / ODD 2020 S1=Observation を design concept として持ち「個体を選んで trace」「中心傾向だけか分布も見たか」/ POM「1 パターンは誤った理由でも合う」/ MATSim Via=events 1 本から agent plan と facility の到着・出発・滞在 / de Montjoye=4 点で 95% 一意・1/10 乗則。**親確認 3 件**(ODD S1 逐語・GA §7.1・de Montjoye)。**非対称**: 個体×tick 全記録は 4.6 GB=S1 の 92%(不可)・場所カルテ 24 MB(全数可)→ 抽出規則が M1 の本体・**再生で事後に作れば追加ラン 0**。指紋は N=1,000 と店名伏せの 2 点。→ **D-80**(O1〜O20・親推奨=場所カルテ→個体生成器→CLI→HTML・規律先行)。
- devlog 第201〜210 を圧縮(第210b)。C9a 実装・R-3 実行中・seed 3 17:35。

## 第212 R-3 個体の同質性 残 10 件 帰還・親確認 3 件・D-81 新設(2026-09-17 夕)

- **R-3**([答申](../research/v2-d68-remaining-research.md)・lit 8・公的 xlsx 1 本 45 MB): 始業時刻の分布表は**存在しない**→代理=時間帯編 第15-4表(仕事率の階差・東京都 p10/p50/p90 7:15/8:45/10:00)/ 片道通勤時間は令和3年に無い→住宅・土地統計 表58-2-1(東京都 p50 43.7 分・渋谷区 33.0・自宅 5.07%)/ Schneider Fig.3 数値なし(追試 11〜17 型・83〜90%)/ Schlich & Axhausen 有料・「8.6/36」の出所不明 / **REAL Sampling(ベースの次トークン・App.J 9M トークン・90.2%)と 2605.09995(instruct の意味的多様性・「Larger base models are not less diverse, but larger post-trained models are」)は別の層**=8B 据置の根拠は後者 / 2604.01520「20–300 倍」は本文に裏づけ表なし / Lu 2013 Π_max 0.88・MC(1) 0.91 / 交替制の 0:00 仕事率=固定の 4.8 倍(全国)・14 倍(東京都)/ 日本 PT へのモチーフ適用=Pseudo-PFLOW / TrajLLM に定量評価なし。**親確認 3 件**(15-4 表を openpyxl で再計算=8.82/1.83・8.25/0.59 一致・REAL App.J・2605.09995 本文)。→ **D-81**(K-1〜K-5・親推奨=採用・K-5 は C9 の速度と同時に入れると二重に効くので順序を宣言)。
- 本日の高優先リサーチ 6 レーン(L-R8・L-C9・R-25・R-23 第2批・R-3・R-4)は全部帰還・親確認済み。C9a 実装中・seed 3 17:35。

## 第213 C9a 帰還・親検収・コミット(2026-09-17 夕)

- **C9a**(サブ Opus 5・9 ファイル): `engine/geometry.py` 新設(前計算表+解析式・Kladek・希望速度 Uniform(1.00,1.60)・MAX_HOPS 32)・SoA +8 B/体(edge のみ)・LOS 段階(人/m²)・resolve の edge 分岐・`--geometry`・`TARGET_GONE`・P2 ≤300 ms@40 万体宣言。**親検収**: 2,446 passed・既定 3 種 checkpoint 不変・**edge 9a9049f5 を親が 2 回再現(決定論)**・lint 5 kept・Kladek の lit メモの誤値 1 件(ρ=1.076→1.015)を 1.017 に訂正。サブ実測: P2 175 ms/tick(40 万体・全員移動中の重い条件)・在圏 昼 −2.6%・朝の到着中央値 13 分早い・1 移動 31.4→10.5 tick(2.3→4.7 km/h)・保存則 OK・詰まり 0。expedient 5 件+床の判断=**D-82**(親推奨=床なし・`geometry_jammed` を計器に)。
- **次**: C9b(対象ヒント辞書 v4・目印 68 の対象解決・注意の焦点+寿命+喪失距離・近づく=移動の対象・見る=待機の対象・会話距離 2 m 成立/離脱)を起動。seed 3(テープ 77%)→ v1.3 確定 → 開封。

## 第214 ユーザー「古典 vs LLM 社会シミュレーションのリサーチ」「リサーチの反映度を全分野で検証」→ 3 レーン帰還+C9b 帰還・親検収(2026-09-17 夕)

- **L-CLS**([答申](../research/v2-classical-vs-llm-simulation-research.md)・lit 13): 古典の要求 6 語(目的を言え/単純さの理由/生成は候補/パターンは複数/再現は独立に/識別問題)× LLM の新規性(役割知識を重みから)と壊れたもの 7(決定論・漏洩・同質性・書式・検証不能感・費用・看破 65.2%)→ 対照表 8 行・**判定基準 10 項(古典由来 6・LLM 由来 1・両方 3)**。Axtell 2016 は 1.2 億体を 1 台・半日=規模は新規性でない。「観測的同値」は Haavelmo 1944→Windrum 2007。**親確認 3**: PIMMUR v4(350 論文/576 実験・65.2%・50.6%=既存答申の 39/89.7% は旧版)・**Anthis 2025 §4.5.2「we encourage, preregistration」=事前登録の外部根拠+1**・Sid 25+3+1 体/20 priests。Squazzoni 2012 JASSS は存在せず(Boero & Squazzoni 2005 で代替)。
- **反映監査 A(P0 35 本・240 項)+B(P1 40+P2 9 本・244 項)= 484 項**: 実装済 214(44.2%)・部分 104(21.5%)・設計済未実装 82(16.9%)・未採用 22(4.5%)・未判定 62(12.8%)。分野: 知覚 100%・SFC 86%・人流/音響/行動経済/小売/科学哲学 80% ↔ **認知科学 0%**・倫理 25%・事業 29%・法学 33%。**方法論の穴**: 感度試験 19 行中結論 1・**AB2〜AB5 未実施のまま 40 万体 4 本**・台帳ゲートは世界過程のみ・定数タグが機械可読でない・P5 未実効。逆引き表 42 行(名指しの P0 は 16 本)。**親再確認 5**(T2 内省の実呼なし ✓・感度台帳 done 6/todo 13 ✓・実施腕 AB1/6/7/7b ✓・B の「D4 修正3 未訂正」は誤り・T3 未実装 ✓)。→ **D-83**(優先順の判断・親推奨 ①開封前に統計を計器へ ②AB2/AB3 有償 GPU ④根拠答申列)。
- **C9b**(サブ・19 ファイル・+1,007 行・49 テスト): 辞書 v4・目印解決・近づく・注意の焦点・会話距離。**親検収 2,495 passed・1 xfailed(354 s)+FleetBridge 回帰 1・既定 4 種不変・edge+v2 6d6b1cda 2 回一致・lint 5 kept**。**mock では G3〜G6 が動かない**(実 LLM でしか測れない)。**親の欠陥修正**: `run.py` の `FleetBridge(...)` に `vocab_version` 未渡し→修正+回帰テスト。判断 3 点=**D-84**(積のまま・実 LLM スモーク・C9c へ)。
- 誤配 1 件: 監査 A への追加指示を L-CLS に送ってしまった(L-CLS は誤配と判断して続行・監査 A は分野別集計を自発的に出していた)。
- **次**: seed 3(テープ 132 MB)→ v1.3 確定 → 開封 / D-83 ①(統計を計器へ)/ C9c / 未踏。

## 第215 ユーザー決定 D-80〜D-84(全部推奨)・seed アンサンブル計器・D-83 ① 着手(2026-09-17 夕)

- **決定**: D-80 M1 採用(場所カルテ→個体生成器→CLI→HTML・規律先行)/ D-81 K-1〜K-5 採用(C9・C10 の後・K-5 は順序宣言)/ D-82 床なし+`geometry_jammed` / D-83 ①②④ 今週・③⑤ S2・⑥ 第2陣・⑦ 進めてよい範囲 / D-84 積のまま・実 LLM スモーク 1 本・次は C9c。C9 アジェンダ §6・C10 アジェンダ §5(着手条件+指紋 3 つの親案)に記録。
- **実装(親)**: `tools/c7/seed_ensemble.py`(N seed 帰無参照・家族 95%・fair CRPS 係数・seed 1/2 で第204 を再現・テスト 7)=IMPLEMENTED #29。seed 3 の取得スクリプトと 5 分おきの見張りを用意。
- **着手**: D-83 ① `holdout_compare.py` の v1.3(複数 occupancy・家族 95% 区間・同値判定 pass/fail/undecided・H3 記述格下げ・GET 包絡・fair CRPS・既定 v1.2 不変)を実装サブ(Opus)へ。
- ユーザーの問い「第二陣はいつ始められるか」「実装のみ/判断のみのものは」に回答(C9c は今すぐ・C10 は指紋 3 つの確認後・記憶は材料集めの後)。
- **次**: seed 3 → 3 seed 帰無参照 → v1.3 確定 → 「開けてよい」。C9c 実装サブ。

## 第216 D-83 ① 帰還・親検収(事前登録 v1.3 の計器)(2026-09-17 夕)

- **サブ(Opus 5)**: `tools/c7/prereg_v13.py` 689 行+`holdout_compare.py` +100/−8+テスト 39(合成のみ・`--open-seal` 不使用)。判定統計量は `five_metrics` の pass 式から機械的に取り、線は `res[H*]["limit"]`(prereg 側と鍵名が食い違う H1 の写し事故を回避)。expedient 11 件を docstring に明記(tau 未定義は fail・Bonferroni 分母 5・fail 優先 AND・H1 昼窓は観測を再正規化・α は 0.01 のみ・N は 3..10・v1.2 に複数 occupancy はエラー・v1.3 の exit code はアンサンブル判定・開封記録の欄追加・CRPS raw は c8 流用)。
- **親検収**: tests/c7 124 passed in 0.75s・tests/c8+cli 265 passed・lint 5 kept・既定不変は golden(report 文面・compare の dict)で固定されているのを確認。**親修正 2 件**: (i) v1.3 のトップレベル判定をアンサンブルに(`apply_ensemble_verdict`・`c7_accept.py` の HOLD 行が読むため・seed 1 点判定は `seed1_v12` に保存)(ii) CRPS の係数名を 2 つに分離((1+1/M)=raw の期待膨張 / M/(M−1)=fair の広がり項)。両方とも正しい量で、名前の混同だけが問題だった。
- prereg §7 に計器注記(確定は seed 3 の後)。
- **次**: seed 3 → `seed_ensemble.py`(3 seed)→ §7 確定 → 「開けてよい」→ `holdout_compare.py --prereg-version v1.3 --open-seal`。C9c-1 帰還待ち。
