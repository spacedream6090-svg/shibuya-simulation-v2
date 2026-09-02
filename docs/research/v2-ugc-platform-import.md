# UGCプラットフォーム/大規模オンラインゲーム基盤の輸入 リサーチ答申(2026-09-02・Opusサブエージェント・全出典URL付き)

> 位置づけ: CLAUDE.md §3「ゲームは作らない・技術知見を輸入する」の常設レーン。
> 対象: 中心仮説「UGCプラットフォーム=信頼できない創作者に世界を拡張させつつ不変条件を守る機械≅本プロジェクトのエンジン/LLM線引き(LLM=創作者・エンジン=ランタイム)」の検証と深掘り。
> 輸入先の主目標: R2詳細(世界過程レジストリ/resolve並行制御)・16行表 行5/13/16・プロンプト規約(prefix設計)・Phase 2骨格・層3GM(原則6)。

---

## ① 要旨(10行)

1. **中心仮説は条件つきで成立**。3つの共通機構が独立に確認できた——(a) deny-by-default の能力集合+入れ子で単調減少、(b) 失敗前提のトランザクション/ロールバック、(c) 裁定→自動化のフィードバックループ。
2. ただし**同型なのは「LLMが規則を書く」層だけ**。UGCの創作者コードは*事前公開・審査・版管理・失効可能な成果物*で、審査コストを長期償却できる。LLMの毎ステップ出力は*流量*で償却できない。→ サンドボックス機構は補助原則8(Voyager)・行13(立法)・行16(未定義行動)にのみ適用し、通常の意思決定にはサンドボックスでなく**スキーマ+resolve**を使う——これが本答申の主要結論。
3. 脅威モデルも違う。UGCの敵は*意図を持ち報酬に反応する*(バックドア・RMT・回避)。LLMの誤りは*無意図*。→ escrow/holding period 等の敵対的機構は一部過剰。
4. 不変条件の性質も違う。UGCのそれは商業・安全(金・児童保護・IP)。**物理・会計の保存則という点では EVE/UO の方が同型度が高い**。
5. 最大の単一輸入候補は **Verse の効果型(`<decides>`+`<transacts>`)**。原則1・2(resolve分離)を*コンパイル時に強制できる形*で書き直せる。
6. 次点は **Replication Graph のノード分類**。知覚契約(U17)をそのまま node 分類として設計でき、かつ「セル可視リストの共有」が prefix 共有仮説の物理的根拠になる。
7. **Roblox の動的プライスフロア+逸脱に比例する手数料**は、行5(価格提案=LLMスカラー)の運用形の完成品。逸脱を*禁じず課金する*。
8. **EVE TiDi** は δ思考時間の先行実装。統制信号が「実行待ちキュー長」という*測れる量*で、かつ**どの時計が伸びてどれが伸びないかを明示的に分けている**(reinforcement timerは伸びない/shield rechargeは伸びる)。
9. **警告的古典**: UO の生態系は「プレイヤーが壊した」のではない。AIは*性能*(半径探索+経路探索)で切られ、生態系は*閉じた資源プールへの退蔵*で枯れた(Koster一次証言)。**閉じた保存則は退蔵項を数えないと必ず枯渇する**。
10. 設計上の緊張として報告: 長期運用に成功した2つの仮想経済(UO後期・EVE)は**いずれも厳密保存則を捨て、faucet-drain+公開計測を選んだ**。「保存則を紙上で閉じる」ドクトリンの運用形を再考する材料。

---

## ② 本柱ごとの知見

### 柱1 — Roblox Luau のサンドボックス/API面

**言語VM層(Luau)**([luau.org/sandbox](https://luau.org/sandbox)・[luau.org/why](https://luau.org/why))

- 脅威モデルを明示: 「untrusted and actively malicious code」を前提。**信頼するのは自前コンパイラが出したバイトコードのみ**——`load` / `string.dump` / `loadfile` / `dofile` を削除し、バイトコードの外部注入経路を塞ぐ。
- 削除ライブラリ: `io`(ファイル・プロセス)・`package`(ネイティブモジュール)・`debug`(メモリ安全違反・隔離破り)。`os` は `clock/date/difftime/time` のみ。`collectgarbage` は `count` のみ。
- **組み込みライブラリと string メタテーブルを VM レベルで readonly 化**(`rawset`/`setmetatable` でも破れない)。スクリプトごとのグローバル表は `__index` リダイレクトで隔離。
- `__gc` メタメソッドを全廃し、ホスト制御のタグ付きデストラクタに置換(GC中に任意コードが走らない)。
- **割り込みハンドラ**: ホストが関数呼び出し・ループ反復の地点で暴走スクリプトを停止できる。Roblox 実装は Studio で10秒ウォッチドッグ。
- `getfenv`/`setfenv` は隔離リスクと認めつつ互換性のため残置(=**残った穴を隠さず文書化する**態度)。

**プラットフォーム層(Script Capabilities)**([create.roblox.com/docs/scripting/capabilities](https://create.roblox.com/docs/scripting/capabilities) / [.md](https://create.roblox.com/docs/en-us/scripting/capabilities.md)・[third-party-vulnerabilities](https://create.roblox.com/docs/scripting/security/third-party-vulnerabilities)・[Roblox公式アナウンス 2026-05-13](https://devforum.roblox.com/t/protect-your-games-with-script-capabilities-sandboxing/4634642))

- 任意の Instance(Model/Folder/Script)に `Sandboxed=true` を立て、`Capabilities` 集合を明示付与する**ホワイトリスト**方式。
- **能力の分類**: 実行制御2(`RunClientScript`/`RunServerScript`)・インスタンスアクセス1(`AccessOutsideWrite`)・スクリプト機能4(`CreateInstances`/`LoadString`/`LoadUnownedAsset`/`ScriptGlobals`)・エンジンAPI面 約40(`Network`/`DataStore`/`Physics`/`Chat`/`Players`/`Teleport`/`Monetization`/`Consequences`(BAN/Kick)/`CapabilityControl` ほか)。
- **入れ子は交差(intersection)**。内側コンテナの実効能力 = 自身の宣言 ∩ 親の能力。共通部分が空なら実質何もできない。→ **能力は入れ子で単調減少しかしない**。
- **`CapabilityControl` 自体が1つの能力**(=`Sandboxed`/`Capabilities` プロパティを変更する権限)。メタ規則を能力体系の内側に閉じ込めている。
- エスカレーション防止が3方向で塞がれている: ①外部 ModuleScript は自身の能力集合が要求側の**部分集合以下**でないと `require` 不可 ②インスタンスの再parentは同等以下の能力コンテナへのみ ③ Bindable{Event,Function} のコールバックは**登録側の能力文脈**で実行(呼び出し側の能力を借りられない)。
- **失敗メッセージが機械可読**: 「The current thread cannot modify 'Workspace' (lacking capability AccessOutsideWrite)」——*何を*/*どこで*/*最初に欠けた能力名*を返す。
- Creator Store から挿入した資産は既定でサンドボックス化され、`LoadUnownedAsset`/`LoadString`/`CapabilityControl`/`getfenv`/`setfenv` が既定禁止(2026-05-13 稼働・著名資産のみ祖父条項)。

### 柱2 — UEFN Verse の言語設計(トランザクショナル意味論)

**効果型**([transacts 公式](https://dev.epicgames.com/documentation/en-us/fortnite/transacts)・[decides 公式](https://dev.epicgames.com/documentation/en-us/fortnite/decides))

- 効果指定子は関数シグネチャの `<...>`。**排他的効果**(`computes` / `varies` / `transacts`)と**加算的効果**(`suspends` / `decides`)に分かれる。
- 公式定義(引用): `transacts` の関数は「the function can read and write data, but those actions can be rolled back if the function also has the `decides` effect」。**排他的効果を何も指定しない関数は「読み書きできるがロールバックできない」**。
- つまり**書けること**と**巻き戻せること**が独立に型に現れる。ロールバック可能性は `transacts`+`decides` の合成でしか得られない。
- 失敗は例外でなく**式の失敗**: `decides` 関数は角括弧で呼び、失敗可能文脈でしか呼べない。コンパイラが効果違反を**コンパイルエラー**にする(実行時サプライズにしない)。

**投機実行のランタイム(AutoRTFM)**([Epic tech blog "Bringing Verse Transactional Memory Semantics to C++" 2024-03-15](https://www.unrealengine.com/en-US/tech-blog/bringing-verse-transactional-memory-semantics-to-c) ※本文はWebFetch 403・検索結果経由の断片のみ / [ICFP/SPLASH 2025 REBASE 講演 Saam Barati (Epic)](https://conf.researchr.org/details/icfp-splash-2025/rebase-2025-papers/4/On-creating-a-virtual-machine-for-Verse-a-language-for-programming-in-a-shared-real-) / [UE API: autortfm_memory_validation_level](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/AutoRTFM/autortfm_memory_validation_level))

- Clang フォーク+専用ランタイムで **C++ にソフトウェアトランザクショナルメモリを付与**。Fortnite 28.10 以降、一部サーバー実行ファイルがこのコンパイラでビルドされている。
- `AutoRTFM::Transact(lambda)` がトランザクションオブジェクト(undoログ)を張る。中断すると*C++側の副作用も*巻き戻る。
- **重要な限界(そのまま我々の制約になる)**: 「open-code」(トランザクション外のコード)がトランザクション中に書かれたメモリを書き換えると、undo が open-code の書き込みを上書きしてメモリを壊す。ゆえに **memory validation** で検出する。→ *ロールバック可能領域は明示的に囲われた範囲に限られ、境界は自動では守られない*。
- REBASE 2025 講演: 「Verse is designed to support multiple paradigms: functional, logic, object oriented, imperative, and transactional」。新VMは旧VMより Verse コードが 5倍速。

**構造化並行性**([Book of Verse 14 Concurrency](https://verselang.github.io/book/14_concurrency/) ※後述の公式性注意 / [structured concurrency 用語](https://dev.epicgames.com/documentation/fortnite/structured-concurrency?lang=en-US))

- 即時式(1シミュレーション更新内で完了)と **async 式**(複数更新にまたがり suspend/resume)を型で分離。`<suspends>` 効果が呼び出し連鎖を伝播。
- 構造化: `sync`(全部起動し全部待つ・結果は宣言順のタプル)/ `race`(最初の完了で他を即キャンセル)/ `rush`(最初の完了で返るが他は走り続ける)/ `branch`(発火して即続行・**囲みスコープ終了で自動キャンセル**)。非構造化は `spawn` のみ(スコープを超えて生き残る・`task(t)` ハンドルを返す)。
- **`rush` と `branch` は loop/for の本体に直接書けない**——*無限にタスクが積み上がるのを言語仕様で禁じている*。
- キャンセルは**協調的**で、シグナルの検査点は「suspension point」(タイミング操作・suspend関数呼び出し・構造化並行式)に限られる。検査点の間はコードが中断されない=「予測可能なタイミング」。
- 同一トランザクション内では `GetSecondsSinceEpoch()` が同じ値を返す(トランザクション内の時刻は凍結)。

### 柱3 — Replication Graph / AOI(interest management)

([Epic tech blog: Replication Graph Overview](https://www.unrealengine.com/tech-blog/replication-graph-overview-and-proper-replication-methods) ※本文403・検索結果経由 / [UE公式ドキュメント Replication Graph](https://dev.epicgames.com/documentation/unreal-engine/replication-graph-in-unreal-engine?lang=en-US) / [Liu & Theodoropoulos, "Interest Management for Distributed Virtual Environments: A Survey", ACM Computing Surveys 46(4)](https://dl.acm.org/doi/10.1145/2535417))

- 解く問題: 標準レプリケーションは**アクタ×接続の総当たり関連性評価**でサーバーCPUがボトルネックになる。UE公式が挙げる規模は **Fortnite Battle Royale = 接続100・レプリケート対象アクタ約50,000**。
- 解: 永続的な **Replication Graph Node** 群が「クライアントごとに送るアクタのリストをオンデマンドで組み立てる」。決定的な性質は2つ——**フレームをまたいでデータを保持できる**ことと、**接続間でデータを共有できる**こと。
- ノードの役割分担(公式ドキュメントの記述):
  - 空間/位置ノード(Epic tech blog の "Grid Spatialization 2D"): 世界をグリッドセルに分割し、**セルごとに「そこから見えるアクタのリスト」を保持**。クライアントは自分のセルを引くだけで距離判定が消える。
  - Always-Relevant ノード: 全クライアント共通の特別アクタ。
  - 接続固有ノード: 特定プレイヤー/チームに常に関連・常に無関連なアクタ。
  - Dormant リスト: 事前配置され状態がほぼ変わらない静的アクタを分離。
  - Attachment ノード: 装備・所持物を所有者にまとめる。
- 「型と状態でアクタをノードに割り当てるだけで莫大なCPU時間を節約でき、従来のレプリケーションでは成立しないゲームが作れる」(UE公式)。
- 学術的裏づけ: interest management は DVE のスケーラビリティ要件に対する標準パラダイムとして体系化済み(Liu & Theodoropoulos の taxonomy)。

**LLM側の接続(prefix局所性仮説の検証材料)**

- 現行の LLM サービング基盤は共有プレフィクスの再利用を一級機能として持つ: SGLang の **RadixAttention**(KV活性をradix木にキャッシュし、先頭一致する要求間で再利用)、vLLM の **automatic prefix caching**(PagedAttention のページ共有)。TTFT 短縮効果はプレフィクス重複率に単調で、同時実行数が増えるほど木のノード共有が増えて効果が複利的に効く。
  - 参考(二次): [SGLang vs vLLM prefix caching 比較](https://medium.com/byte-sized-ai/prefix-caching-sglang-vs-vllm-token-level-radix-tree-vs-block-level-hashing-b99ece9977a1)
- **したがって仮説の機構的根拠は成立する**: Replication Graph が「セル可視リストを1回作って多接続で共有」するのと、「セル世界状態記述を1回トークン化して多エージェントで共有」するのは*同一の共有構造*。
- ただし成立条件が厳しい(下記③-7で規約化): ①共有部が**バイト一致**であること ②共有部が**先頭**に来ること(prefix であってsuffixではない) ③共有ブロック内にエージェント固有の一語も混ぜないこと。→ プロンプト配置は [静的system/役割] → [場所セル世界状態] → [個体private] → [問い] の順序に固定される。

### 柱4 — Robux 経済の運用

([Marketplace fees and commissions 公式](https://create.roblox.com/docs/marketplace/marketplace-fees-and-commissions) / [.md](https://create.roblox.com/docs/en-us/marketplace/marketplace-fees-and-commissions.md) / [Developer Exchange 公式](https://create.roblox.com/docs/production/monetization/developer-exchange) / [Earned Robux & DevEx Rates 公式サポート](https://en.help.roblox.com/hc/en-us/articles/27984458742676-Earned-Robux-Earned-Robux-Balance-and-DevEx-Rates) / [18+ DevEx rate (creator-docs)](https://github.com/Roblox/creator-docs/blob/main/content/en-us/production/monetization/18-plus-devex-rate.md))

- **手数料**: Marketplace 購入で創作者取り分 30%。ゲーム内購入は 創作者30% / 体験オーナー40% / Roblox 30%。
- **累進レベニューシェア(Marketplace)**: 創作者の取り分が**プライスフロアからの上乗せ倍率**で増える——1×フロア=30%、2×=50%、6×以上=70%(上限)。
- **プライスフロア**: 資産種別ごとに設定。Limited については 2024-02-22 に**動的プライスフロア**を導入し、市場状況に応じ通常日次で変動(算出式は非公開)。
- **摩擦の意図的な設計**:
  - アップロード手数料 80 Robux/提出(本人確認後)。
  - **返金可能な publishing advance**(公開時前払い・種別により 10〜20,000 Robux)。= *スパム出品には費用がかかるが、真面目な出品では戻る*デポジット。
  - 個別売上のコミッションに **30日エスクロー**。
  - 転売は Limited / Limited Unique のみ、購入後 **30日の保有義務**(即時フリップの禁止)。
  - Limited の取引参加自体が有料サブスクリプション(Premium)ゲート。
  - UGC Limited 転売の分配: 転売者50% / 原作者10% / 販売仲介10% / Roblox 30%。
- **出口(DevEx)は一方向の計測された弁**: 標準レートは 1 Earned Robux = **US$0.0038**(30,000 Robux = $114)。2026-06-08 以降、米国の年齢確認済み18歳以上プレイヤーの適格支出由来分は **$0.0054**。買値と売値が非対称で、KYCと適格性の門がある。

**行5への含意(見解)**: Roblox は多数の自律的値付け主体を「自由放任」でも「方程式固定」でもなく、**(a) プラットフォームが市場から内生的にフロアを再計算し、(b) フロアからの逸脱幅の関数として取り分を変える**という形で捌いている。逸脱を*禁止せず課金する*。これは 16行表 行5(価格提案=店主LLMのスカラー・成立=エンジン)の運用形そのもの。

### 柱5 — モデレーション判例化パイプライン

**Roblox**([How Roblox Uses AI to Moderate Content on a Massive Scale (2025-07)](https://about.roblox.com/newsroom/2025/07/roblox-ai-moderation-massive-scale) / [Scaling Safety and Civility on Roblox (2024-04)](https://about.roblox.com/newsroom/2024/04/scaling-safety-civility-roblox) / [ROOST へのオープンソース安全モデル提供 (2026-08)](https://about.roblox.com/newsroom/2026/08/roblox-open-source-safety-models-roost) / [Voice Safety Classifier v3 (2026-06)](https://about.roblox.com/newsroom/2026/06/upgrading-voice-safety-classifier-22-languages-sharper-detection-capabilities))

- **規模**: テキストチャット 61億メッセージ/日・28言語。音声 110万時間/日・8言語。資産アップロード 数百万/日。**違反率は 0.01%**。
- **スループット**: テキストフィルタ ピーク 750,000 RPS、PII分類器 370,000 RPS、音声安全分類器 8,300 RPS。音声は15秒以内に分類。違法コンテンツ通知からアクションまでの中央値 10分。
- **政策→モデルの変換パイプライン**(=判例化の実装形):
  1. **golden set**: 政策専門家が手作業で curate した基準例。
  2. サンプリング: uncertainty sampling で境界例を、adversarial red team で弱点を狙う。
  3. **整合テスト**: 同じ例を複数の人間にラベルさせ、**一致率 80% を「政策が執行可能か」の閾値**とする。
  4. 合成データ: LLM に実例を模した人工例とラベルを作らせる。
  5. **フィードバック**: 異議申立てで覆った判定が自動的に学習データになる。ユーザ通報(視覚的注釈つきが適格通報の約15%)も入る。「通報からAI駆動のルールを自動生成する」ことを検討中と明言。
  6. 段階的制裁: 警告 → タイムアウト → 停止 → 音声チャット剥奪。停止の効果は最大3週間持続し再犯率を下げる、との社内研究に言及。
- 分類器は**オープンソース化**され外部で再利用されている(voice safety classifier は2024年公開後72,000回超ダウンロード、v3は機械ラベル25万時間+人手ラベル2.9万時間で学習)。
- **独立評価(批判側の一次)**: Kaushik, Brown, Hasan, Rahaman, "An Evaluation of Chat Safety Moderations in Roblox", [arXiv:2605.04491](https://arxiv.org/abs/2605.04491)。4ゲーム約200万メッセージ(9.98万件を人手ラベル)。グルーミング・未成年の性的対象化・いじめ・暴力・自傷・機微情報共有が**すり抜けた事例**を確認し、フラグ済みユーザーの回避技法も観測。→ *自動判例化は再現率を保証しない*ことの一次証拠。

**Epic / Fortnite**([Island Moderation Tips and FAQs](https://dev.epicgames.com/documentation/en-us/fortnite/island-moderation-tips-and-faqs-in-fortnite-creative) / [IARC Overview and FAQs](https://dev.epicgames.com/documentation/en-us/fortnite/iarc-overview-and-faqs-in-fortnite-creative) / [Introducing IARC Ratings in Fortnite](https://www.epicgames.com/site/en-US/news/introducing-iarc-ratings-in-fortnite-paving-the-way-for-a-multi-game-ecosystem) / [Fortnite Developer Rules](https://legal.epicgames.com/fortnite/developer-rules))

- 公開時に **2段階審査**: 第1段階は**メタデータと資産**(島名・説明・サムネイル・ロード画面文言・ロビー背景・宣伝スクショ・トレーラー)、第2段階でゲームプレイ本体。安い検査を先に置いて高い検査に回す件数を削る構造。
- 公開前に創作者が **IARC 質問票**に自己申告で回答→年齢レーティングが自動算出、各地域のレーティング機関(ESRB/PEGI/ACB/USK/ClassInd 等)が公開後に独自審査で上書きしうる。= **創作者の構造化自己申告 + 事後監査**。

### 柱6 — EVE Online 単一シャード運用 + UO の警告

**アーキテクチャ**([CCP dev blog "My node was equipped with the following..."](https://www.eveonline.com/news/view/my-node-was-equipped-with-the-following...) / [CCP dev blog "CarbonIO and BlueNet"](https://www.eveonline.com/news/view/carbonio-and-bluenet-next-level-network-technology-1) / [Stackless Python Applications wiki](https://github.com/stackless-dev/stackless/wiki/Applications) / [GDC Vault: Multitasking with Coroutines](https://www.gdcvault.com/play/1020578/Multitasking-with))

- **node = 1つの EVE サーバープロセス**で、クラスタの最小粒度。Stackless Python 製、**1コアに束縛**。90〜100枚の SOL ブレードが各2ノードを走らせる。
- 太陽系がシミュレーション単位。多くは共有ブレード上だが、高負荷系(Jita/Motsu/Saila)は**専用ブレード**に載せ、2つ目のノードは遊ばせる。DBクラスタはピーク時 2,000+ トランザクション/秒(38,000 IOPS)。
- 並行性は **tasklet**(OSスレッドでない・軽量・プリエンプションなし)+ channel。CCP は「コンパイル言語では作れなかった」と明言。
- **StacklessIO → CarbonIO → BlueNet**: I/O を GIL の外へ出す一連の改修。CarbonIO はマルチスレッド通信エンジンを GIL 外で走らせ「データはGILを一度も譲らずにキューから取り出される」。BlueNet は 8〜10バイトのルーティングヘッダで C++ 側がパケットを転送し「Python は一度も呼ばれない」。ピーク約1600人のプロキシで CPU が劇的に低下、Sol ノード側は 8〜10% 改善(=**ゲーム論理側のボトルネックはI/Oではない**ことの実測)。

**Time Dilation (TiDi)**([CCP 公式告知 "Introducing Time Dilation (TiDi)"](https://www.eveonline.com/news/view/introducing-time-dilation-tidi) / 補助: [EVE University Wiki: Time dilation](https://wiki.eveuniversity.org/Time_dilation) / [PC Gamer 解説](https://www.pcgamer.com/eve-onlines-mad-time-dilation-tech-beats-lag/))

- 問題定義: 過負荷時「一度yieldしてから次の順番が回るまで5秒以上かかることがある」。
- **統制信号は測れる量**: 「実行待ちの tasklet キューが最小化される——理想的にはゼロ」ことを目標に、ゲーム内クロックを負荷に比例して遅くする。モジュール・物理・移動など時間依存系の処理需要が同率で減る。
- 導入時の例示: 大規模会戦のワープイン時に**実時間の5%**まで、戦闘中は30%前後、撤退時10%程度。「どこまで伸ばすかのハード上限は運用後に決める」と明言。
- **公平性は下層のラウンドロビンスケジューラで担保**。
- **時計の分割が明示的**: 「reinforcement timer は dilate できない」(制度的・戦略的タイマーは実時間に固定)一方「shield recharge は dilate されなければならない」(戦闘内の物理量)。
- 体験としては、無応答や desync ではなく**スローモーション**として観測される(HUDも爆発も一緒に遅くなる)=**劣化が透過的**。
- 補足(二次情報): Tranquility の tick は通常 1Hz、TiDi 全開で 0.1Hz まで落ちる。TiDi はノード単位で作用する。
- 運用: 大規模会戦の予告に対し、CCP が次のダウンタイムで当該太陽系を**より強力なマシンへ再割当て(reinforced node)**する——*人手の運用判断*。

**経済の実運用**([Monthly Economic Report – June 2026](https://www.eveonline.com/news/view/monthly-economic-report-june-2026) / [March 2026](https://www.eveonline.com/news/view/monthly-economic-report-march-2026) / [May 2026](https://www.eveonline.com/news/view/monthly-economic-report-may-2026) / [CCP: EVE Online Appoints In-World Economist](https://community.eveonline.com/news/news-channels/press-releases/eve-online-appoints-in-world-economist-1/) / [CCP: 中央銀行エコノミスト Stefán Þórarinsson 招聘 (2025)](https://www.ccpgames.com/news/2025/ccp-games-appoints-central-bank-economist-stefan-thorarinsson-to-advance) / [Game Developer: CCP Economist on EVE's "pure capitalist" market](https://www.gamedeveloper.com/game-platforms/ccp-economist-on-i-eve-online-i-s-pure-capitalist-market))

- CCP は 2007年に MMO で初めて**専属の実務経済学者**(Dr. Eyjólfur Guðmundsson、元アークレイリ大学経営・理学部長)を雇用。本人は自らの仕事を「中央銀行の研究員のようなもの」と表現。2025年には中央銀行エコノミストを追加招聘。
- **月次経済レポート(MER)** を公開。公開系列: ISK faucets / sinks の科目別内訳・money supply・velocity・production / mining(高セク・低セク・WHのガス採掘量など)・destruction・**地域別統計**・価格指数群(consumer / mineral / primary producer / secondary producer)・top commodity faucets・services 内訳・2018年基準の指数。
- **生データを zip で全公開**(例: `EVEOnline_MER_202606.zip`)。
- 会計を閉じるための専用科目 **Active ISK Delta**: RMT捜査による没収と、プレイヤーの離脱/復帰(90日無活動でその ISK は経済からいったん外れる)を吸収する残差項。**「説明できない差分」を専用科目に押し込んで明示する**という手口。
- 実際の運用値の例: 2026-03 は faucets +17%、2026-05 は +26%(bounty prizes と commodities が主因)、2026-06 は Active ISK Delta がプラス転(拡張後に休眠プレイヤーが戻る典型)。

**警告的古典 — Ultima Online の生態系崩壊**([Raph Koster: "Did players destroy the UO ecology?"](https://www.raphkoster.com/games/snippets/did-players-destroy-the-uo-ecology/) / [Koster: "UO's resource system"](https://www.raphkoster.com/2006/06/03/uos-resource-system/) / [同 part 3](https://www.raphkoster.com/2006/06/05/uos-resource-system/) / [Zachary Booth Simpson, "The In-Game Economics of Ultima Online", GDC 1999-04-07](https://www.semanticscholar.org/paper/The-In-game-Economics-of-Ultima-Online-Simpson-Galbraith/5aeef27d5ed62007c8550997855014f4603d2fb0))

- 設計: 生物は資源値の束(肉・皮・羽…)。オブジェクトは METAL/WOOD/CLOTH/MAGIC/PLAYER といった**抽象資源タグ**を持ち、AI は資源に対して4種の関わり方(PRODUCTION / FOOD / SHELTER / DESIRES)を持つ。優先順位は Maslow 的階層(FOOD→SHELTER→DESIRES)。
- **通説の否定(Koster一次証言)**: AI が切られたのは「**半径探索に続く経路探索のコスト**」のためであり、生態系崩壊の理由とは**無関係**。
- **実際の崩壊原因**: 「最初は閉じた経済ループで、すべてが固定資源プールから spawn されていた。それが**プレイヤーの退蔵(hoarding)の犠牲になった**」。具体的には——羊を殺して羊毛を得て、クラフト熟練度を上げるためにシャツを大量生産し、それを退蔵するか極めてゆっくり売った。結果「**中央銀行の羊毛が尽き、羊を新たに spawn できなくなった**」。
- 資源値そのものは今もクラフト・採取系で使われ続けている(=設計が全損したわけではない)。
- Koster は Simpson の "The In-Game Economics of Ultima Online" を「faucet-drain economy という語をゲーム設計に広めた極めて影響力の大きい論考」と評価。GDC 1999 で発表。

---

## ③ v2への輸入提案リスト

| # | 提案 | 行き先 | 根拠(柱) |
|---|---|---|---|
| 1 | **能力集合(capability set)をレジストリの必須フィールドに**。世界過程・LLM生成規則・行動ハンドラは、触れてよい状態面を宣言した集合を持つ。既定は deny。 | R2詳細(レジストリのD-R2-2フィールド構成) | 1 |
| 2 | **入れ子は交差**。サブ規則・呼び出し先の実効能力は親との∩で単調減少しかしない。加えて「能力を変更する能力」自体を1能力として体系内に置く(=LLM生成規則が自分の権限を広げられない)。 | R2詳細+補助原則8 | 1 |
| 3 | **コールバックは登録側の能力文脈で走る**。resolve が呼び戻すハンドラが呼び出し元の権限を借りない。 | R2 原則5(書き込み口1本)の実装細目 | 1 |
| 4 | **バイトコード信頼境界**: LLMが書いた規則は*テキストのまま実行しない*。自前の制限DSL→自前コンパイラ→自前VMの一本道のみ。`eval`相当の受理口を作らない。`load`/`dump` 相当を最初から実装しない。 | 補助原則8(Voyager方式)・行13(立法)・行16(未定義行動) | 1 |
| 5 | **割り込み/ウォッチドッグ**: LLM生成規則の実行に step 予算を課し、関数呼び出し・ループ反復の地点で決定論的に中断。中断は失敗として resolve に返す。 | 予算宣言表R1・R2 実装原則3 | 1 |
| 6 | **失敗メッセージの機械可読化**: 「何を・どこで・最初に欠けた能力/資源は何か」を構造化して返す。原則1「不足時は無効化+**本人通知**」の通知フォーマットをこれに合わせる。 | 16行表 行1-6の共通resolve契約 | 1 |
| 7 | **効果型を resolve の契約にする(最重要)**。各行動ハンドラ/世界過程が `pure` / `reads` / `writes` / `writes+rollbackable` / `suspends` を宣言し、テストで静的にゲートする。原則2(意図まで/結果はエンジン)を*規約*から*検査可能な型*へ格上げする。 | R2詳細 D-R2-2 + D-R2-6(状態成長宣言と同じ書式に載せる) | 2 |
| 8 | **エージェント意図 = 失敗しうるトランザクション**。resolve は意図列を決定的順序でトランザクションとして適用し、失敗は部分書き込みなしで巻き戻す。`decides`+`transacts` の分離をそのまま採る——「書ける」と「巻き戻せる」を別々に宣言させる。 | R2 原則1・2・5の実装形 / Phase 2骨格 | 2 |
| 9 | **ロールバック領域を明示的に囲う**。トランザクションログの対象は宣言された SoA 状態面のみ。ログ・LLM呼び出し済み・RNGストリーム・ファイルは「open code」であり *巻き戻らない*。境界越えの書き込みを検査するテスト(AutoRTFM の memory validation 相当)を置く。 | R2詳細(resolve並行制御) | 2 |
| 10 | **構造化並行性の規律**: エージェントの複数ステップ行動はタスク木にし、スコープ終了で自動キャンセル。孤児タスクを作れるのは1構文だけに限る。**「ループ本体に非構造タスク生成を書けない」を静的規則にする**(=runB の二乗爆発を並行性の層でも構造的に禁止)。 | R2 実装原則(3への追加条項) | 2 |
| 11 | **中断点の限定**: エージェント思考中に世界状態が変わらないことを保証する。suspension point を「LLM呼び出し」と「明示的yield」だけに限り、その間の状態面を凍結(トランザクション内で時刻が凍るのと同型)。 | R2 原則5 + 三時計の整合 | 2 |
| 12 | **知覚契約を Replication Graph のノード分類で設計する**: ①場所セルノード(セル→可視エンティティ/世界状態リスト、**フレーム跨ぎ保持・エージェント間共有**)②常時関連ノード(天候・時刻・大事件)③個体固有ノード(所持・関係・債務)④ dormant ノード(建物・看板=一度届けたら再送しない)⑤ attachment ノード(所持品を所有者にまとめる)。 | U17(知覚契約+可視性事前計算)/ 憲法5の「届き先」宣言 | 3 |
| 13 | **prefix局所性仮説は「機構的に成立・実測未確認」として採択し、プロンプト規約に落とす**。規約: プロンプトは [静的system/役割テンプレ] → [場所セル世界状態(セル共有・バイト一致)] → [個体private] → [問い] の順に固定。共有ブロックにエージェント固有の一語も入れない。数値の丸め・列挙順・空白を正規化してバイト一致を保証。**受け入れゲート = prefix cache ヒット率の実測**(ablation対象)。 | プロンプト規約(prefix設計)+ v2-bench-plan | 3 |
| 14 | **行5の運用形 = 「内生フロア + 逸脱に比例するコスト」**。エンジンが原価・センサスからフロアを再計算(日次=制度時計)、店主LLMのスカラー提案はフロアからの倍率として受理し、逸脱幅の関数で成立確率/取り分/売れ残りが効く。**逸脱を禁止せず課金する**。E7(価格分散)が保存され、暴走もしない。 | 16行表 行5の再リサーチ素材(D-R2-3)/ 行6賃金も同型 | 4 |
| 15 | **摩擦の意図的設計3点セット**: ①返金可能デポジット(出品・価格改定にコストを課し、成約すれば戻る)②最低保有/最低改定間隔(高頻度フリップ・価格振動の抑制)③決済のエスクロー遅延。いずれも `expedient` でなく **mechanism** として正当化可能(現実の商慣行に対応物がある)ことを門前条件で示す。 | 16行表 行4-5 / 経済SFC答申との突合 | 4 |
| 16 | **判例化パイプラインの5段構成をそのまま層3GMに**: 政策文 → golden set(手 curate 基準例)→ 決定論ルール/分類器 → 自動執行 → 異議申立てで覆った判定を golden set に還流。 | 原則6(裁定は判例化してエンジンへ降ろす)/ 層3GM設計(R8) | 5 |
| 17 | **「執行可能性の閾値」を導入**: *同じ事例を独立に複数回裁定させ、一致率が閾値(Robloxは80%)を超えたものだけを決定論ルールへ降ろす*。一致しない事案は判例化せず、毎回LLM裁定に残す。——原則6の「2回目は決定論参照」に**降ろしてよいかの門**を追加する提案。 | 原則6の精密化 / R8 | 5 |
| 18 | **2段階審査の経済学**: 未定義行動(行16)の受理は、まず**安い構造化自己申告の検査**(どの状態面に触るか・どの能力が要るか・保存則を破るか)で落とし、通ったものだけ高価なLLM裁定に回す。IARC 質問票+事後監査と同型。 | 16行表 行16 / 行13 | 5 |
| 19 | **δ思考時間 = TiDi 型の制御器にする**。統制入力は主観的な負荷感でなく**測れるキュー長**(未処理の意思決定数 / step予算超過分)。出力は世界時計の伸長率。**ハード下限を宣言する**(CCPも「上限は運用後に決める」と明言している=最初から数値を決め打たない)。 | 三時計 / 予算宣言表R1 / R2 D-R2-5 | 6 |
| 20 | **時計ごとに dilate 可否を宣言する**。世界過程レジストリに `dilatable: yes/no` フィールドを追加。物理時計に載る過程は伸びる、制度時計に載る過程(営業日・締切・ダイヤの制度上の時刻)は伸びない。CCPの reinforcement timer / shield recharge の分割と同型。 | R2詳細 D-R2-2(レジストリ) + D-R2-4 | 6 |
| 21 | **劣化を透過的にする**: 打ち切り(イベント落とし)より減速を優先。落としたときは「落とした」ことが観測出力に出る。 | 憲法1(打ち切りでなくLOD)の補強 / 観測射影 | 6 |
| 22 | **経済センサスを MER 形式で定期出力**: faucets/sinks の科目別内訳・money supply・velocity・生産/消費/破壊・**地域別(=丁目/駅勢圏別)**・価格指数群(消費者/素材/一次生産者/二次生産者)を毎「月」出力し、**生データも同梱**。パターン台帳E群の実運用装置になる。 | パターン台帳(E1経済センサス)/ 観測射影 / v2-bench-plan | 6 |
| 23 | **残差科目を必ず1つ置く**(Active ISK Delta 相当)。保存則が閉じない差分をゼロと言い張らず、専用科目に押し込んで**大きさを毎回公表**する。差分が膨らんだら機構の欠陥として台帳に上がる。 | 「保存則は実装前に紙上で収支を閉じる」の運用形 / 経済SFC | 6 |
| 24 | **退蔵(stock)項を保存則の紙上収支に必ず含める**。UOの死因は流量でなく在庫。エージェント保有在庫を台帳の計測対象に含め、「中央プールが枯れる」状態を検知するテストを置く。 | 経済SFC / パターン台帳 / Phase 2骨格 | 6 |
| 25 | **近傍クエリ設計を最優先の性能課題として明示**。UOのAIは「半径探索+経路探索」で消えた。#12の空間セルが同時にこの対策になっていることをレジストリの門前条件に書く(=一石二鳥を宣言して二重実装を防ぐ)。 | R2 実装原則2(状態成長宣言)の姉妹条項 | 6 |
| 26 | **設計上の緊張の明示的な決着を求める(親への論点提起)**: 長期運用に耐えた2つの仮想経済(UO後期・EVE)は**厳密保存則を捨て faucet-drain + 公開計測を選んだ**。v2ドクトリン「保存則系は実装前に紙上で収支を閉じる」を、①厳密保存を貫く ②faucet-drain を認めた上で全 faucet/sink を台帳登録し月次計測する、のどちらで運用するかを D-R2-3 で決定すべき。**推奨は②**(現実の渋谷経済は開放系であり、bbox境界に必ず流出入がある)。 | 決定台帳 / 16行表 行4-6 / 経済SFC答申 | 6 |

---

## ④ 移入禁止リスト(エンゲージメント最適化=設計者の指紋が増えるもの)

| 禁止対象 | 一次情報 | 禁止理由 |
|---|---|---|
| **エンゲージメントプール型報酬式**(「島のエンゲージメント ÷ プラットフォーム総エンゲージメント × プール」)。Roblox の旧 Engagement-Based Payouts(Premium Playtime Score・2025-07-24 廃止)/ 現 Creator Rewards、Epic の Engagement Payout。 | [Roblox: Engagement-based payouts](https://create.roblox.com/docs/production/monetization/engagement-based-payouts)・[Epic: Engagement Payout in Fortnite Creative](https://dev.epicgames.com/documentation/fortnite/engagement-payout-in-fortnite-creative?lang=en-US)・[Epic: Creator Economy 2.0](https://www.fortnite.com/news/introducing-the-creator-economy-2-0) | 「注目の総量の取り合い」を目的関数として世界に注入する装置。エージェントの効用に滞在時間・再訪率・注目シェアを入れた瞬間、観測される社会は**その目的関数の像**になる。設計者の指紋の最大の増加源。 |
| **リテンション重み・課金近傍プレイタイム重み**(Epicの現行式は active playtime / island retention / item shop 支出周辺の playtime / 新規・復帰ユーザー獲得の5指標を重み付け)。 | 同上 | 上に同じ。特に「支出の周辺時間」を重みにする設計は、経済行動を注目指標へ従属させる。 |
| **参加権の課金ゲート**(Limited の売買・トレードが Premium サブスクリプション必須)。 | [Roblox marketplace fees](https://create.roblox.com/docs/marketplace/marketplace-fees-and-commissions) | 市場参加者の選別基準がプラットフォームの収益設計に由来する。現実の渋谷の市場参加条件に対応物がなく、`expedient` としてすら正当化できない。 |
| **人為的希少性の注入**(Limited / UGC Limited の供給を運営が絞ることで価格を作る)。 | 同上 | E7(価格分散)を「創発させる」のでなく「作る」ことになる。分散が出ないなら機構の欠陥として台帳に上げるべきで、希少性で埋めてはならない。 |
| **外部換金レート(DevEx 型の一方向弁)**。 | [Roblox DevEx](https://create.roblox.com/docs/production/monetization/developer-exchange) | 世界の閉性を壊す。ただし「出口は設計され計測された弁である」という*思想*は #23(残差科目)として輸入済み。 |
| **ガチャ/ルートボックス型の確率設計、段階的制裁の行動改変目的での使用**(Robloxは停止処分が最大3週間再犯率を下げると社内研究に言及)。 | [Roblox AI moderation at scale](https://about.roblox.com/newsroom/2025/07/roblox-ai-moderation-massive-scale) | 記録と裁定は輸入してよいが、**再犯率を下げるための介入設計**は観測対象を先に矯正する。層3GMは裁く装置であって矯正装置ではない。 |
| **IARC 年齢レーティング質問票を世界内機構として持ち込むこと**。 | [IARC Overview](https://dev.epicgames.com/documentation/en-us/fortnite/iarc-overview-and-faqs-in-fortnite-creative) | 商用配信の法的要件であって世界の性質ではない。ただし *2段階審査の経済学*(#18)と *構造化自己申告+事後監査* の形式だけは輸入する。出力物公開側の要件は publication-ethics 答申の管轄。 |
| **人手で特定の場所に計算資源を優遇する運用**(EVE の reinforced node をプレイヤー要請で割り当てる)。 | [EVE architecture / reinforced node](https://highscalability.com/eve-online-architecture/)(二次) | 再現性を壊す。負荷に応じた資源再配置は**自動かつ宣言的なポリシー**としてのみ入れる。「どの場所が重要か」を人間が都度決めた瞬間、ラン間比較が成り立たなくなる。 |
| **「違反率0.01%」型のKPIを世界の健全性指標に流用すること**。 | 同上 | プラットフォーム安全のKPIであって世界の忠実度の指標ではない。パターン台帳の照合指標と混ぜない。 |

---

## ⑤ 未発見・不確実項目(見つからなかったものは見つからなかったと書く)

**取得できなかった一次資料**
1. Epic の AutoRTFM 技術ブログ本文(`unrealengine.com/en-US/tech-blog/bringing-verse-transactional-memory-semantics-to-c`)は **HTTP 403** で取得不能。記載内容は検索結果経由の断片と UE API リファレンス(`autortfm_memory_validation_level`)からの再構成。**トランザクションのオーバーヘッド実測値・競合時の解決順序(どちらが勝つか)・ネスト深度制限は未確認**。
2. Epic の Replication Graph 技術ブログ本文も **403**。ノード名 "Grid Spatialization 2D" は検索結果経由。UE公式ドキュメントページ本体からは**ノードのクラス名の完全な列挙が取れていない**。
3. `dev.epicgames.com` の Verse 概念ページ群(effects-in-verse / concurrency-overview-in-verse)は本文がJSレンダリングで、WebFetch では目次しか取れなかった。用語ページ(`transacts` / `decides`)のみ本文取得に成功。並行性の記述は **Book of Verse(`verselang.github.io/book`)に依拠**。
4. Simpson "The In-Game Economics of Ultima Online" の**一次配布元が未確認**。検索で出た PDF は非公式ミラー(dergigi.com / nelderim.pl)のみで、DL禁止規律により中身は未検証。Semantic Scholar の書誌のみ確認。Koster の引用による評価に依拠している。
5. EVE MER の **raw data zip の中身は未確認**(ダウンロード実行禁止のため)。科目定義(何を faucet とし何を sink と数えるか)の**方法論ドキュメントは記事本文中に見つけられなかった**。

**公開されていない/確認できなかった事実**
6. **Roblox の動的プライスフロアの算出式は非公開**。判明したのは「2024-02-22 導入」「市場状況に依存」「通常日次で変動」のみ。#14 の提案は式ではなく*構造*の輸入である。
7. Roblox の script capabilities の**完全性**: ドキュメントから約49件(実行制御2+アクセス1+機能4+エンジンAPI約42)を取得したが、「42」という数はページ整形の産物である可能性がある。各能力が**どの実行地点で検査されるか**の内部仕様は非公開。
8. Roblox の**人間モデレーターの実数は非公開**("thousands of human experts around the world" のみ)。自動/人手の処理件数の内訳、異議申立ての受理率・覆り率も非公開。
9. **TiDi の現行ハード下限は未確認**。導入告知(2011年頃)は「5%まで」「10%まで」を*例示*しており、CCP自身が「上限は運用後に決める」と述べている。現行の制限値の公式一次資料は見つからなかった。通常 1Hz / TiDi時 0.1Hz という記述は二次(EVE University Wiki・PC Gamer)。
10. Fortnite の Replication Graph 導入による **CPU 削減率の具体数値は公式には見つからなかった**。確認できたのは「接続100・レプリケート対象約50,000アクタ」という規模のみ。
11. Tranquility の**現行**ハードウェア構成は未確認。取得できた CCP dev blog(SOLブレード90-100枚×2ノード、Opteron/Woodcrest、RamSans)は**明らかに旧世代**の記述。近年クラウドネイティブ化を進めた旨の報道(Nutanix系)はあるが一次資料未取得。
12. **Robux の総発行量・沈没量の公開統計は見つからなかった**。Roblox は EVE の MER に相当する経済公開を**していない**(手数料率とレートは公開だが、フローの科目別統計は非公開)。→ 柱4は「価格制度の設計」としては豊富だが「**保存則の全域計測の先行例としては EVE の方が圧倒的に上**」。

**矛盾する一次証言(未解決)**
13. UO 生態系について、**Koster と Garriott の説明が食い違う**。Koster は「プレイヤーが壊したのではない。AIは性能で切られ、崩壊は閉じた資源プール+退蔵が原因」と明言している一方、Garriott は「プレイヤーが動物を殺し尽くして壊した」と語ったと報じられている([Massively OP: Richard Garriott on how players 'destroyed' UO's ecology](https://massivelyop.com/2018/01/06/richard-garriott-talks-about-how-players-destroyed-ultima-onlines-ecology/)、Ars Technica War Stories)。両者とも一次証言。**本答申は Koster の記述(自身のブログ・より技術的に具体的)を採ったが、この食い違いは未解決**。教訓としては両説とも「ボトムアップ生態系は運用で死ぬ」に収束するので、輸入する結論(#24 退蔵項・#25 近傍クエリ)は説の選択に依存しない。

**検証されていない仮説**
14. **「空間セル = プロンプト prefix 局所性」の実測先行研究は見つからなかった**。prefix caching(RadixAttention / vLLM APC)自体は確立した技術で、共有プレフィクスによる TTFT 短縮も広く報告されているが、**AOIセル粒度でプロンプトを設計した社会シミュレーションのベンチマークは発見できなかった**。よって #13 は「機構的に妥当・効果量は自前で測るべき未検証仮説」として扱うのが正しい。v2-bench-plan の測定項目候補。
15. **Book of Verse(`verselang.github.io/book` / GitHub `verselang/book`)の公式性は断定できない**。README は「open source documentation for the Verse programming language」でライセンスは CC0-1.0。Epic の名を冠しているが、Epic 公式ドキュメントであるとは確認できなかった。並行性の記述(#10・#11 の根拠)はこの不確実性を負っている——**採択前に `dev.epicgames.com` 本体で裏取りすべき**。
16. 中心仮説の「同型」判定は**私の見解**であり、外部の先行研究に基づくものではない。特に「UGCのサンドボックスは*成果物*に効き、LLMの*流量*には効かない(償却の非対称)」という論点は本答申の独自主張で、反証可能な形にすると「LLM生成規則の審査コストを、その規則の再利用回数で割った値が、毎ステップのスキーマ検証コストを下回るか」という測定問題になる。Phase 2 で測れる。

---

## 参考: 中心仮説の判定(見解)

| 観点 | 同型度 | 根拠 |
|---|---|---|
| 権限の与え方(deny-by-default・交差・権限昇格の封じ) | **高** | Roblox capabilities が補助原則8にほぼそのまま移植可能 |
| 失敗の扱い(トランザクション・部分書き込みなし・失敗は式の値) | **高** | Verse `decides`+`transacts` が原則1・2の型付き版 |
| 裁定→自動化のループ | **高** | Roblox の golden set→分類器→異議申立て還流が原則6の実装形 |
| 適用のタイミング | **低** | UGC=事前審査つき成果物(償却可)/ LLM=毎ステップの流量(償却不可) |
| 脅威モデル | **低** | UGC=意図的・報酬反応的 / LLM=無意図・分布外 |
| 守るべき不変条件の性質 | **低**(UGC)/ **高**(EVE・UO) | UGC=商業・安全 / v2=物理・会計の保存則 → 保存則側の先行例は EVE と UO |

**結論(見解)**: 仮説は「不変条件を守る機械」という部分で正しく、3つの具体機構を輸入できる。ただし**「LLM=創作者」の対応は、LLMが*規則を書く*ときにだけ成り立つ**。毎ステップの意思決定に対しては、サンドボックスではなく低次元スキーマ+resolve が正しい形であり、これはむしろ答申原則4「量はスカラー、質は自由文」がすでに与えている解である。保存則の全域運用については EVE の MER と UO の失敗の方が同型度が高く、そちらを主教材にすべき。
