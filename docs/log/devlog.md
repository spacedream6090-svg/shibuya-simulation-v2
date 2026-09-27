# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **2 / 10**
> 第1〜第270(2026-09-01〜09-26)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第271 ユーザーの答え 3 件+パーサ「セル」接頭辞の修正(2026-09-26)

- **依頼**(ユーザー): 「1. A / 2. 全部入れてもいいと思うが、現時点での思考の頻度では行動の粒度が小さすぎる気がする。そもそもなぜエンジンで行動を規定しないといけないの? 待つなどであれば不要じゃない? / 3. 修正を入れていいよ」
- **実施**: ③ `contract.parse_target` に `_CELL_PREFIX_RE`(「セル」「セルID:」「セルID_」を剥がした残りがセル ID の形のときだけ CELL)。テスト +1・parametrize +7(llm 173 passed・広い回帰 全緑・exit 0 を確認)。計測: テープ 28 本の対象欄で 14,872 呼が CELL に(移動 10,913=2.3%・待機 1,017・食事 921・乗車 645・購入 391)。エンジンは既定で対象欄を行き先に使わないので挙動不変・mock 5,000 checkpoint 2f3969cf 不変。IMPLEMENTED #45。① D-114 は案 A=§9-5 と §9-6 を束ねる(PENDING D-114/D-112)。
- **親の答え(②)**: エンジンが行動を「規定」する理由は 1 つだけ=**世界に触れる**(保存則・占有・位置・前提の検査・他者の観測に出る)から。購入・食事・乗車・移動・会話・通報・役割語はそれ。待つ・見る・散歩・休む は世界を変えない「次に考えるまでの時間の使い方」で、契約行も裁定も要らない。いまの語彙はこの 2 種を 1 つの欄に混ぜていて、後者を 1 tick の行為として作るから粒度が思考の頻度(7〜15 呼/体/日)と合わない(待機 40,755 呼は何も起こさず次の起床まで放置・エンジン継続 87.6% は歩行の 1 歩)。筋は**二層**: (a) 世界に触れる行為=小さな契約集合(要るときだけ書く)・(b) 活動=自由文 10 字+持続(到着まで/相手が来るまで/N 分/次の予定まで)。エンジンは (b) に対して位置と持続と観測への表示だけを持ち、語彙の成長は (a) のオブジェクト由来(affordance)だけになる。→ v3 の新語 2 語(見る・散歩)は撤回し、二層の出力形を設計ラウンド(§9-10・認知+カレンダーと同じ回)の草案に含める。降車削除・上限撤廃・文面 v3・対象欄の許容値・パーサ・VOCAB_COMPAT は v3 に残す。
- **次**: ユーザーが二層の方向を認めれば、設計ラウンドの草案(出力形・持続の決め方・観測への表示・KPI の数え方)を書いてから実装。それまで Overpass 再取得(生応答+md5)→ W6 再生成 → D-112 ①+D-114 案 A+選択器の口 を進める。

## 第272 行為と活動の二層=先行の実装読み 2 本+文献 1 本 → 設計ラウンドの草案(2026-09-27)

- **依頼**(ユーザー): 「一旦他のシミュレーションでどのような実装となっているのかコードを観察してまとめる、あとは文献や論文をリサーチしてどのような実装にすれば良いのか調べてもらってから草案を書いて欲しい」。
- **分担**: サブ Opus 5.5 ×3 並列(`model:"opus"`)= R-43 コード読み(Generative Agents / AI Town / Humanoid Agents・46 ファイル)・R-44 コード読み(Concordia / AgentSociety / OASIS・57 ファイル)・R-45 文献(24 出典・原典 21)。3 本とも WebFetch でなく **curl を標準出力に流して読んだ**(要約モデルを挟まず行番号と逐語を保つため。保存・clone・実行なし=「Web は読むだけ」の範囲内と親が判定)。子サブ未起動・コミットなし・台帳未編集。
- **親検収**: 固定コミットの raw(AI Town @8e05997・GA @fe05a71・Humanoid @9718c67・Concordia @eaea22e・AgentSociety @8cc5bb9・OASIS @ca8caa5)と arXiv HTML / 著者公開 PDF(pymupdf を標準入力で)を同じ方法で読み、**結論を変える逐語 25 か所を照合=全一致・訂正なし**。訂正の伝播 1(既存答申の AI Town「7 入力」は ARCHITECTURE.md の列挙・コードでは `inputHandler` 13=版差の追記)。R-45 §11 の 9 件は答申の注記どおり(Lyfe の 10-100/30-100 の不一致は実在・Wang の 59.9% は本文の上限値)。INDEX・backlog に 3 行。
- **事実**: 6 実装のうち **AI Town(入力口 13 vs activity `{description, emoji, until}`)・AgentSociety v1(移動/購入=コード vs 仕事/睡眠/その他=LLM 見積もりの分数で記憶だけ)・Concordia interrupt 駆動 GM(自由文+`{mask, timer}`・裁定なし・逐語注入)の 3 つが二層**。持続を LLM に書かせる実装 3(GA=分・Humanoid=時刻・AgentSociety=分)。保存則つきの行為をコードで解くのは AgentSociety の購入と OASIS だけ。「待つ」に専用語は OASIS の `DO_NOTHING` だけ。文献: options の timeout(Sutton 1999)・HTN「cannot easily be expressed as a single goal task」・Lyfe「termination condition … checked by fast, non-LLM methods」(0.5 USD/体/時)・AgentSociety「sleeping are directly handled by LLMs」・Wang 2024「does not exceed 59.9%」・Project Sid「imaginary pickaxe」・Sims Medieval「only attempt to make a decision when their interaction queue was empty」。
- **成果**: [二層の草案](../design/v2-action-activity-two-layer-draft.md)(183 行): §1 事実(待機 40,755・休憩 59,148 呼が 1 tick で切れて放置・移動の 57% 対象なし)/ §2 実装 6 本の横断表 / §3 文献 / §4 案=出力に「活動:」「まで:」を足す・契約語は世界に触れる語だけ(待機・休憩・降車を外し 並ぶ を横断語へ・「行動: なし」が安全弁)・エンジンは活動に位置/持続(上限・割込み可)/表示の 3 つだけ・満了は System 1.5 が先に受ける・「まで: 次の予定」はカレンダーから・語彙の成長は行為のオブジェクト由来だけ・第270 の候補 14 群を再配置(新語なし)/ §5 決定アジェンダ A〜I(**D-116 新設**・親推奨つき)/ §6 空欄(呼数の増減・8B の書式率は未測定)。PENDING D-92/D-112/D-114 に追記・STATUS・devlog 2/10。
- **次**: ユーザーの答え(A〜I・番号で)→ 語彙 v3+文面 v3+パーサ+エンジン(`activity_until`・起床入口 5・`--activity`)を 1 ラウンドで実装(mock で起床内訳と呼数を先に計測)。並行して Overpass 再取得 → W6 再生成 → D-112 ①+D-114 案 A。
