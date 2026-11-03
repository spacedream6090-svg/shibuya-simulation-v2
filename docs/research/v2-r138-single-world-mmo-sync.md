<!-- hdr:v1 | 等級: (親検収の前) | 作成: 2026-11-03 | 範囲: 11-03 §7-4 -->
# R-138 単一の世界の MMO の同期(世界を遅らせる形と、計算を割っても結果を 1 つに保つ形)

- **分野**: 計算機科学(並列・決定論) #28 / ゲームエンジン工学・CG #30 / ABM方法論 #21 | **重要度**: P1([指示書 11-03 返事その 3](../design/prompt-2026-11-03-reply3.md) §7-4・§4)
- **一次確認**: (親検収の前)。筆者の実読=出典 32 本(◎ 20・○ 11・△ 1。S23 の FFF 4 本を 1 本ずつ数えた)・読めなかったもの 9 件は §10
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-11-03・リサーチ役(Opus 5.5)。子サブは起動していない。Web は読むだけ。途中で WebFetch と WebSearch が利用の上限で止まったため、一部の頁は `curl` の出力を標準出力のまま Python で文字だけにして読んだ(ファイルには保存していない・ブラウザを装う設定は使っていない)。リポにも data/ にも何も保存していない。コード・台帳・設計書・INDEX は 1 バイトも変えていない。試験も回していない。SpatialOS の GDK(MIT)の設定ファイルは読んだだけで写していない。封印の層(holdout・test の層)には触れていない。
> 土台: `build/spatial-d102-prep` の HEAD `a800790`(発注の 33193c3 の次の commit=第343 §1 の答申の訂正。src は同じ)。場所は `path:行`(src/shibuya からの相対は `engine/...` と略す)。出典は §9 の [S*]・読んだ日はすべて 2026-11-03。
> 既存答申との関係: PDES の保守的同期・lookahead・透かし・背圧は ※既存答申 [R-128](v2-r128-backpressure-design-pdes-watermarks.md) §2〜§4(等級 B)に、AI Metropolis の依存の規則と区域ごとの時計の案は ※既存答申 [R-73](v2-r73-time-model-des.md) §2・§7-1(等級 B+)に、Age of Empires と Factorio の「入力だけを記録して再生しチェックサムで同期外れを見つける」型は ※既存答申 [R-72](v2-r72-event-log-formats.md) §4(等級 A−)に、乱数の鍵(blake3 で鍵を作るカウンタ型の Philox)は ※既存答申 [R-55](v2-r55-own-code-state-checkpoint-rng-resume.md)(等級 A)に、v3 の列と透かしは ※既存答申 [R-133](v2-r133-event-driven-core-design-options.md) §1・§6・§8(等級 B)にある。本書はそれらを繰り返さずに引き、MMO の実例(EVE・Star Citizen・SpatialOS・関心の範囲・ロックステップ)だけを足す。ゲーム技術の輸入の旧答申([v2-game-tech-import-research](v2-game-tech-import-research.md))は等級 D(出典 URL なし)なので、根拠には使っていない。
> 等級: ◎=開発者の公式の文書・特許・ソースを本文まで読んだ/○=公式の文の写し(ファンの wiki の転載)・二次の記事・要旨だけ/△=検索の抜粋だけ。筆者の見立ては【見立て】、根拠のない置き方は【推測】と書く。推薦は書かない。決めるのはユーザー(壁打ち)。

## §0 要旨

1. EVE Online の Time Dilation(TiDi)は、サーバーの待ち行列(tasklet の列)がほぼ空に保たれるまで、ノードの中の世界の時計を細かく遅らせる仕組みである [S1◎]。下限は 10% [S2○][S3○]。遅らせる単位は星系ではなくノード(1 本の単一スレッドの過程)で、同じノードの星系はそろって遅れる [S2○][S5◎]。
2. TiDi は世界の時計を 1 つにしない。遅れたノードと遅れないノードが並び、産業・技能の習得・構造物の強化の時計は壁時計のまま進む [S2○]。CCP は「時計を見て終わる時刻を確かめるものは遅らせない」と書いた [S1◎]。
3. EVE の分割は静的である。星系はダウンタイムにノードへ割り当てられ、大きな戦いは前日のダウンタイムまでに届け出て専用のノードへ移す [S7◎][S8◎]。CCP は届け出ても性能は保証できないと書く [S8◎]。
4. Star Citizen の server meshing は、状態を持つ replication layer と、計算する game server を分けた [S9○][S11○]。1 つの entity には書き込める server(authority)が 1 つだけあり、streaming の範囲を出ると次の server へ移る [S9○]。2024-12 の 4.0 で静的な mesh が出た [S12○]。2026-08 の時点では、負荷で server を増減するのはインスタンスだけ(QDSM)で、区域の細分はまだである [S13○]。
5. SpatialOS も同じ骨格を持つ。1 つの entity の component に authority を持つ worker は 1 つで、interest は空間の問い合わせと更新の頻度で書く [S16◎][S21△]。移譲には猶予の時間があり、猶予の間の命令は溜め、遅れて届いた更新は捨てて数える [S15◎]。決定論を約束する記述は、読んだ範囲には無かった。
6. MMO の「割っても 1 つ」は、実行中に書き手を 1 人にして矛盾しない歴史を 1 本保つという意味であり、同じ seed から同じ歴史を出す(再現)とは別の性質である【見立て】。再現まで求める先例は、全員が同じ入力で同じ計算をするロックステップ(AoE・Factorio)[S22◎][S24◎] と PDES(※R-128 §2)の側にある。
7. ロックステップは (A) の形でもある。AoE は「いちばん遅い機械に合わせて」通信の turn の長さを変えた [S22◎]。Factorio は遅い計算機があると他の全員が待つと書き、遅い参加者を外す選択肢を挙げた [S23◎]。本プロジェクトの完全な透かしで待つ形(※R-133 §6-2 の W1)は、この系譜に当たる【見立て】。
8. 関心の範囲(AOI)の先例は帯域を減らすための近似であり、格子のセル・常に届く一覧・休眠・問い合わせごとの頻度が道具になる [S27◎][S16◎]。本プロジェクトで AOI を「誰が何に気づくか」に使うなら、それは近似ではなく世界の規則(知覚)になる。計算を割るための関心は、規則の上に立つ漏れのない上位集合でなければ結果が変わる【見立て】。
9. 本プロジェクトで (B) を後で開ける条件を 6 つ挙げた(§7)。鍵と乱数が区域と処理の順に依らないこと、全体に効く量(刻みあたりの呼の予算・アービタの順)を決まった鍵で合流すること、越境を世界の時刻の境目で渡すこと、持ち主の割り当てを決まった時刻にだけ変えること、浮動小数の集計の順を固定すること、分け方を変えた 2 ランの byte 比較を試験に入れること。
10. 決めるべき題を 10 個並べた(§8)。(A) の形、遅れの計器、割る単位、割り当てを変える時刻、越境の渡し方、全体の量の合流、浮動小数、一致の検査、艦隊の遅れの閉じ込め、時計に載せないものの宣言である。推薦は書かない。

## §1 問い

- 前提([指示書 11-03](../design/prompt-2026-11-03-reply3.md) §4・仮決定): 世界は 1 つの時計で動く。区域ごとの列(Q4)は採らない。鍵と乱数は区域や処理の順に依存させない。将来、結果を変えずに計算を割る道は残す。世界の時刻はナノ秒で持ち、1 秒の格子で束ねる(G2)。列は体ごとの次の時刻の欄+世界と体をまたぐ事象の列(Q3)。同時刻の鍵は時刻 → 種類の順位 → ハッシュ(事象の時刻・体・ラン seed)で、挿入の順は入れない。
- 問い (A): 計算が追いつかないとき、世界を遅らせる形。MMO ではどう測り、どの単位で遅らせ、観測者(遊ぶ人)にどう伝え、何を遅らせないか。
- 問い (B): 計算を割っても結果を 1 つに保つ形。何を単位に割り、境目をまたぐ作用をどう扱い、書き手をどう決め、結果の一意性と再現性をどこまで保つか。
- 本プロジェクトとの違い(【見立て】): 観測者は遊ぶ人ではなく、後で結果を読む人である。壁時計で待たせても誰も困らない。困るのは、壁時計(GPU の遅れ)が世界の結果に漏れることだけである(10-25 §2-7・※R-128 §0-1)。

## §2 EVE Online(Time Dilation・星系ごとのノード・1 つの宇宙)

### 2-1 仕組みの表

| 項目 | 事実 | 出典 |
|---|---|---|
| 問題 | サーバーは協調型の round-robin で tasklet を回す。負荷が高いと、譲った後に次の番が回るまで「5 秒以上」かかる。船の破壊は DB との往復が多く「何分にも」伸びる。module を回す tasklet は 100 ms 実行すると譲る | [S1◎] |
| 狙い | 過負荷のとき「待っている tasklet の列を最小に、理想は 0 に」保つように劣化させる | [S1◎] |
| 仕組み | 大きな戦いの負荷の多くは時計に結びつく(module・物理・移動・ワープ)。そこで、待ちの列がごく小さく保たれるまでゲームの時計を遅らせ、負荷が引けば戻す。「動的に、ごく細かい刻みで」。少しの過負荷なら 98% でもよい | [S1◎] |
| 退けた案 | 物理(Destiny)の刻みを延ばす(物理は負荷の 5〜10% だけ)・module の周期を延ばす(ゲームの設計が変わる) | [S1◎] |
| 下限 | 2011-04 の時点では「どこまで遅らせるかに硬い上限を置く」「0.1% で回しても意味がない」とだけあり、値は未定 | [S1◎] |
| 下限(後の値) | 最大の遅れは 10%(ゲームの 1 秒=壁時計の 10 秒)。2013-01 の Asakai の戦い(2,700〜2,750 人)では「設定の上限の 10% まで押し下げられた」 | [S2○][S3○] |
| 例(2011 の想定) | 約 1,600 人。ワープで来た直後は 5% 程度・戦いが組み合うと約 30%(何でも 3 倍かかる)・1,200 人ほどで約 60%・一斉の離脱で約 10%・終われば 100% | [S1◎] |
| 遅らせないもの | 強化の時計(reinforcement timer)は遅らせられない(遅らせると満了の時刻を動かせてしまう)。シールドの回復は遅らせる。「時計を見て終わる時刻を確かめるものは、たぶん遅らせるべきではない」 | [S1◎] |
| 遅らせないもの(今) | EVE のサーバー時刻と、それに結びつくもの(産業の仕事・技能の習得・Upwell 構造物の修理の時計)は通常のまま | [S2○] |
| 単位 | 遅れはノード単位。ノードの負荷が閾値を越えると、そのノードの全星系に TiDi の印が出る | [S2○] |
| 伝え方 | HUD の動きと宇宙の爆発がゆっくりになる [S1◎]。円の印にマウスを当てると今の率が出る・緑(少し)/黄(半分)/赤(遅い)[S2○]。運用側には、ノードが過負荷になると大きな赤い数字が出る状態の頁がある [S3○] | |
| 効果(運用後) | 大きな戦い 2 件で module の反応を大半の時間 1 秒未満に保った。以前は 20・40・600 秒が出ていた(2012-02 の Veritas のブログの紹介) | [S4○] |
| 限界 | 「TiDi はすべてを解決しない」。時間の長さに結びつかない負荷があるので、際限のない大きさの戦いは扱えない。上限を越えると以前のように応答しなくなる | [S1◎] |
| 導入 | 2011-04 に構想(「ごく仮」)・2012-01 に既定で有効(Crucible) | [S1◎]・[S4○] |

### 2-2 1 つの宇宙の構造

| 項目 | 事実 | 出典 |
|---|---|---|
| 層 | Proxy(接続とセッション)・SOL(星系の模擬)・DB の 3 層。ノード=EVE のサーバーの 1 過程で、クラスタの最小の粒度 | [S5◎][S6◎] |
| 単一スレッド | Stackless Python の作りのため、各ノードの Python の部分は 1 本のスレッドで、CPU の 1 コアしか使えない | [S5◎] |
| 規模 | 2008: SOL の機械 90〜100 台 × 2 ノード。2023(Tranquility Tech IV): 星系の模擬の一般用に 170 ノード・rank-and-file の機械 18 台 × 13 ノード(195 稼働+39 予備) | [S5◎][S6◎] |
| 専用ノード | Jita は 1 ノードに単独、The Forge の市場も別のノードに単独。2008 年には Jita・Motsu・Saila が専用の機械にあった | [S5◎][S6◎] |
| 割り当ての時刻 | 星系はダウンタイムにノードへ割り当てる。戦いの当日のダウンタイムを過ぎると、別のノードへ移せないことがある | [S7◎][S8◎] |
| 強化の届け出 | 会社の CEO か director だけが Fleet Fight Notification を出せる。2018-01 から「予定の戦いの前のダウンタイムの 1 時間前まで」(以前は 24 時間前で、論理の誤りがあった)。長期の予約は受けない。強化しても大きな戦いの性能は保証できない | [S7◎][S8◎] |
| 生の移動 | 2008 年にノードが落ちた後、その星系を専用の機械へ「再割り当て」した例が 1 件ある | [S5◎] |
| 運用の手当て | Asakai では、戦いに関わらない人を他のノードへ移し、残りは時計を遅らせてしのいだ(記事の要約) | [S3○] |

### 2-3 読み(【見立て】)

- TiDi の測る量は「待ちの列の長さ」で、遅らせる量は「時計に結びついた負荷」である。列を小さく保つ制御なので、遅れの率は負荷の関数になる。遊ぶ人から見て公平かどうかは、同じノードの中では全員が同じ率で遅れる点で保たれる。
- EVE の時計はノードの数だけある。星系の境(門のジャンプ)をまたぐとき、遅れの率の違う時計の間を移ることになる。その扱いの一次の記述は見つけていない(§10)。
- 「時計を見るものは遅らせない」は、時計を 2 種類に分ける規則である。ゲームの時計(遅らせる)と壁時計(遅らせない)の 2 本で、本プロジェクトの世界の時刻と壁時計の分け方(10-25 §2-7)と同じ切り口になる。ただし EVE は壁時計の側に世界の規則(強化の満了)を置いている。本プロジェクトでは世界の規則はすべて世界の時刻に載る。壁時計に載るのは固まりの上限(※R-133 §6-2 W1)のような運用の量だけである。

## §3 Star Citizen(server meshing)

| 項目 | 事実 | 出典 |
|---|---|---|
| 骨格 | entity はもう 1 台の game server の持ち物ではない。1 つの server node が制御し(authority)、他の node は client の見え方を持つ。authority は node の間で移せる必要がある。2020 年の前半に entity authority と authority transfer に開発の時間を割いた(当時の移譲は client と 1 台の server の間だけ) | [S9○] |
| replication layer | streaming と replication の論理を game server の外へ出した。shard の全 entity の今の状態を持つ、伸び縮みする記憶上のキャッシュ。Replicant はゲームの論理を回さない(動きも物理もなく、網の符号だけ)。Gateway は client と Replicant の間で包みを振り分ける | [S9○] |
| EntityGraph と持続 | 網で複製される全 entity の状態をグラフ DB に書く(Persistent Streaming)。2021 年は replication layer と EntityGraph に充てた | [S9○] |
| 時計 | replication layer は「traditional な game server のような tick rate ではなく事象駆動」。余分の 1 段は 1 ms 未満の見込み。遅れの要因は server の tick rate・client の ping・entity の生成・持続のサービスの遅れで、tick rate が最も大きく、server が模擬する場所の数に関係する | [S9○] |
| 順 | server は生成の列を 1 本持ち、順に処理しなければならない(並列の列で緩める予定)。server で生成が終わるまで client へは複製しない | [S9○] |
| 権威の偏り | ゲームの符号の一部はまだ client が権威を持つ。弾は client 側で生成する | [S9○] |
| 静的と動的 | 静的な mesh では、shard あたりの server の数と、どの server がどの場所を模擬するかを前もって決める。全員が同じ場所へ行けば同じ server に集まる。動的な mesh は模擬の配り方を絶えず見直し、過負荷も遊びもない点を探す。そのために entity の authority を移し、server を立ち上げて畳む | [S9○] |
| 越境 | shard をまたぐ作用は無い。shard の中では、ミサイルは複数の server を渡れるが、authority を持つのは 1 台だけ | [S9○] |
| 落ちたとき | Replicant が落ちると、client は shard につながったまま模擬の一部か全部が止まり、EntityGraph の持続から戻す(1 分未満を見込む・entity が飛ぶことがある)。初期の Hybrid(1 台)が落ちると全員が最初の画面へ戻される | [S9○] |
| 歩み | 2023-10: replication layer を game server から外し、単独のサービスにする。game server は宇宙全体ではなく特定の区域の authority になれる [S11○]。2024-03: replication layer に server 2 台をつないだ shard で同時 350 人 [S10○]。2024-12: Alpha 4.0 の build 情報に「Server Meshing: 5:5:500 Player Shards」(数の意味は書かれていない)[S12○] | |
| 2026-08 の今 | shard ごとに決まった数の server があり、それぞれが別の区域(内部の呼び名は territory)を受け持つ。静的な形では、混んだ区域を割る server を立てられない。4.10 のインスタンスで、負荷の比が上限に達したら server を足す形を初めて入れた(QDSM)。永続の宇宙の区域はまだ細分していない | [S13○] |

- 決定論・同じ seed からの再現・時刻の同期の記述は、読んだ範囲には無かった。
- 読み(【見立て】): Star Citizen が保つ「1 つ」は、書き手が 1 人であることと、状態の正本が replication layer に 1 つあることである。負荷への答えは server を足すこと(B)で、世界の時計を遅らせる仕組み(A)は宣言されていない。過負荷のときは server の tick rate が下がり、それが遅れとして見える [S9○]。tick rate が下がったとき世界の時間の進みがどうなるか(遅れるのか、刻みが粗くなるのか)の一次の記述は見つけていない(§10)。

## §4 SpatialOS(Improbable)

| 項目 | 事実 | 出典 |
|---|---|---|
| 模型 | すべてが entity で、entity は component からなり、component のデータは schema で書く。worker はクラウドで並べられ、authority を持つ entity-component を模擬する。1 つの entity-component に authority を持つ worker は同時に高々 1 つ。worker は authority を持つ entity のまわりに interest を持つ | [S21△] |
| HLA との比べ | authority は HLA の所有の管理に似るが「交渉ではなく指図」。interest の問い合わせは HLA の DDM に似るが、worker ではなく Runtime が初めから提供する | [S21△] |
| Runtime と bridge | 各 bridge が worker に最新の世界の見え方を渡し、worker が一部の entity を変えられるようにする。2 つの見え方を一致させるのは bridge の役 | [S16◎] |
| 問い合わせによる interest(QBI) | entity の interest component が、entity DB への問い合わせの購読と更新の頻度を持つ。頻度は問い合わせごとに変えられる(近い球は高く・遠い球は低く)。component の値での一致(例: 同じチーム)や、他の entity のまわりへの interest も書ける。時間に敏感でない component なら、更新を少なく受けて帯域を空けられる | [S16◎] |
| 負荷の分け方(特許) | chunk の module が chunk の領域の entity を見張り、負荷の均しの規則で entity を別の chunk へ移す。移すときは、状態を送り、行き先が変化の通知を受け始め、元が受けるのを止める。候補の計算機ごとに負荷の重心の距離と移す点数を出し、瞬間の負荷が高い候補は外す | [S17◎] |
| 負荷の分け方(設定) | GDK for Unity の配布の設定に `chunkEdgeLengthMeters: 5`・世界 500 m × 500 m・層 `UnityGameLogic` に `rectangle_grid` 2 列 × 1 行 | [S18◎] |
| ヒステリシス | 権威の帯を重ねて、権威の行き来(thrashing)を防げる(空間のヒステリシス)。1 つの区域に 1 つの worker だけにしたいなら重ねない | [S16◎] |
| 移譲の手順(特許) | 移譲の引き金は、entity が別の worker の区域に入る・worker が落ちて別の worker が引き継ぐ・新しい worker が世界の一部を受け持つ・負荷の高い worker が遠い区域を手放す。Runtime は「失いそう」(AUTHORITY_LOSS_IMMINENT)と知らせ、猶予の時間(例 1,000 ms=在庫の取引を外の DB へ書き終える時間)の後に移す。猶予の間に来た命令は溜め、新しい worker が受け持ってから渡す。旧い worker が応えなくても、猶予が過ぎれば移す | [S15◎] |
| 遅れた更新(特許) | worker が「失いそう」と思って更新を送っても、Runtime から見ればもう権威を失っていることがある。その更新は捨て、計器を 1 つ増やす。計器は移譲の数・時間・時間切れ・捨てた更新・捨てた命令 | [S15◎] |
| 後の扱い | GDK for Unity は「失いそう」の状態をやめ、`HasAuthority` の真偽だけにした(SpatialOS 側で廃止) | [S19◎] |
| 終わり | GDK for Unity と GDK for Unreal の公開リポは 2022-01 に archive(MIT)。Unreal の GDK は旧基盤向けに凍結され、zeuz 上の SpatialOS への移行を案内している。公開の文書の頁(documentation.improbable.io)は今は応答しない | [S18◎][S20◎] |

- 決定論の記述は、読んだ範囲には無かった。
- 読み(【見立て】): SpatialOS は「どの worker がどの区域を持つか」を負荷で動かすことを前提にしている。移譲の結果(捨てた更新・溜めた命令の適用の時刻)は、壁時計の猶予と、どの worker がどれだけ速く応えたかに依る。だから同じ入力から同じ結果を出す設計ではない。決定論でない設計の帰結は、移譲の計器(捨てた更新の数)という形で特許に書かれている。

## §5 関心の範囲と決定論

### 5-1 関心の範囲(interest management)

| 先例 | 中身 | 出典 |
|---|---|---|
| 総説 | 大規模な分散の模擬と仮想環境(軍の模擬・MMO など)で、データの流れを絞る仕組みを interest management と呼び、規模の要件を満たす鍵になる。方式の分類と取り合いを総説する | [S28○] |
| AOI の比べ | MMO の interest management の算法の比べ(NetGames 2006) | [S29○ 書誌のみ] |
| Unreal の Replication Graph | Fortnite は 1 試合 100 人・約 5 万の複製される Actor で始まる。Actor ごとに全 client へ送るかを判定する標準の形は server の CPU で詰まる。位置で Actor を群に分け、格子のセル(または部屋・区域)ごとの一覧を持つ。動かない置き物を休眠の一覧へ分け、全員に常に届く一覧・特定の client にだけ届く一覧を別に持つ | [S27◎] |
| SpatialOS の QBI | 問い合わせ+頻度(§4) | [S16◎] |
| 推測航法(dead reckoning) | 100 ms ごとの更新の間、速さと向きを一定と見て手元で動かし、次の更新で直す。向きと速さが瞬時に変わる場面では使えない | [S26◎] |
| 実体の補間 | 他の人を 100 ms「過去」に描き、既知の 2 点の間を補う | [S26◎] |
| 遅延補償(lag compensation) | server は時刻つきの入力をすべて持つので、過去の任意の時刻の世界を組み立て直せる。撃った人の画面に映っていた位置で当たりを判定する。代わりに、物陰に隠れた後で撃たれることがある | [S26◎] |

- 読み(【見立て】): 上の先例はどれも、正本を持つ server が 1 台で、client へ何を送るかを絞る道具である。送らなかった分は client の見え方が粗くなるだけで、正本は変わらない。本プロジェクトの正本は 1 つの過程の中にあり、観測者(client)はいない。対応するのは「体が何に気づくか」(知覚)と「計算を割ったとき、どの部分が他の部分の何を読むか」の 2 つになる。前者は世界の規則で、近似ではない(※R-133 §3 の A2=セルの購読)。後者は割った部分の間の読みの範囲で、規則が読む範囲を漏れなく含まないと結果が変わる。

### 5-2 ロックステップと決定論

| 先例 | 中身 | 出典 |
|---|---|---|
| AoE の同時の模擬(Bettner・Terrano 2001) | 各機械で同じ模擬を回し、同じ命令だけを渡す。命令は 2 つ先の通信の turn に実行する(turn 1000 の命令は 1002 に)。turn はふつう 200 ms。乱数の種も同期した。模擬の中で乱数を呼ぶ回数をそろえる必要があった | [S22◎]・※R-72 §4 |
| AoE の速さの制御 | 全員が同じ入力を要るので、ゲームは「いちばん遅い機械」が通信を処理し turn を描き命令を出せる速さでしか進めない。各 client が保てる frame の速さと最も長い ping を「Turn Done」に載せ(2 バイト)、host が turn の長さと frame の速さを決める。turn の長さは遅れの変化には速く上げ、ゆっくり下げる。速さを変えるのは少しずつにした | [S22◎] |
| AoE の利用者の研究 | RTS では命令の遅れ 250 ms は気づかれず、250〜500 ms はよく遊べ、500 ms を越えると気づかれる。揺れる遅れ(80〜500 ms)より一定の 500 ms の方が遊べた | [S22◎] |
| AoE の同期外れ | 模擬が違えば「out of sync」として止める。世界・物体・経路・照準をチェックサムした。小さな差は時間とともに広がる(鹿の位置の差が数分後に村人の狩りの差になる) | [S22◎]・※R-72 §4 |
| AoE の局所の要因 | 模擬の中の符号は、局所の要因(空き時間・機械・設定)に依ってはならない。乱数を使うが模擬を変えてはいけないもの(地形の音)は、乱数の状態を控えて種を戻した | [S22◎] |
| Factorio の決定論 | 決定論のロックステップ。入力だけを送り、全員が毎刻みを同じに模擬する。網・遅れ・性能の問題は同期外れの原因にならない | [S24◎]・※R-72 §4 |
| Factorio の遅れ | 遅れの設定は全員で同じ。決定論のため、全員が全員の操作を同じ順に適用するので、自分の操作も他人の前の操作をすべて適用してからでないと出せない [S23◎ FFF#83]。手元の写し(latency state)を毎刻み正本から作り直し、未適用の自分の操作を載せて画面に出す。毎刻み作り直すので、ぶつかっても自ら直る(戦いと複雑な操作には使わない)[S23◎ FFF#83] | |
| Factorio の遅い参加者 | 計算機が地図を十分速く模擬できないと、他の全員が自分の模擬を遅くして待つ。それが重すぎる参加者を自動で外す選択肢を挙げた(2016)。入ってくる人は地図を受ける間の入力を溜め、早送りで追いつく(追いつけなければ他の人に迷惑をかけずに外れる) | [S23◎ FFF#147・#149] |
| 浮動小数の決定論(Fiedler 2014) | 決定論=同じ初期状態と同じ入力で「まったく同じ」結果。ODE は解法の中で乱数で拘束の順を混ぜるので、そのままでは決定論でない。同じ機械なら、内部の種を frame の番号に置けば一致した。異なる compiler・OS・命令の集合では保証できない。frame n の入力が無ければ、相手は frame n を進めず待つ | [S25◎] |

- 読み(【見立て】): ロックステップは「計算を割る」のではなく「同じ計算を全員でする」形だが、本プロジェクトに持ち込める部品が 3 つある。1 つ目は、入力が揃うまで待つ(A の形)。2 つ目は、局所の要因を模擬に入れない規則。3 つ目は、ずれをチェックサムで最初の場所まで追う検査である。Fiedler の「種を frame の番号に置く」は、11-03 §5 の v3-0a(刻みの番号を直接入れた鍵を世界の時刻から作る関数に通す)と同じ問題の 1 つ前の形にあたる。番号が処理の順や区域に依らない限り、どちらでも決定論は保てる。

## §6 比較の表

### 6-1 (A) 世界を遅らせる形

| 実例 | 何を単位に遅らせるか | 越境の扱い | 時計 | 決定論 | 結果の一意性 | 観測者への見え方 |
|---|---|---|---|---|---|---|
| EVE TiDi | ノード(同じノードの星系はそろう)[S2○] | 遅れの違う時計の間を門で移る(扱いの一次は空欄) | ノードの数だけのゲームの時計+遅らせない壁時計(強化・産業・技能)[S1◎][S2○] | 主張なし | 書き手は 1 ノード=1 本の歴史(実行中)。同じ戦いをもう一度回す概念は無い | HUD がゆっくり・円の印と率・色 [S1◎][S2○] |
| AoE の速さの制御 | 世界全体(全員が同じ turn)[S22◎] | 越境なし(全員が全部を計算) | 1 本(turn の長さを変える) | 決定論(種も同期) | 全員で同じ。違えば止める | 命令の遅れが 250〜500 ms・速さは少しずつ変える [S22◎] |
| Factorio | 世界全体(遅い参加者に全員が合わせる)[S23◎] | 越境なし | 1 本 | 決定論のロックステップ [S24◎] | 全員で同じ。違えば報告と再接続 [S24◎] | 手元の写しで遅れを隠す [S23◎] |
| Fiedler のロックステップ | 世界全体(入力が無い frame は進めない)[S25◎] | 越境なし | 1 本 | 同じ機械・同じ build では決定論 | 同上 | 揺れを隠すため遅れの緩衝を置く [S25◎] |
| 本プロジェクトの W1(※R-133 §6-2) | 世界全体(適用の時刻に返事が無ければ手前で待つ) | 越境なし(1 過程) | 世界の時刻 1 本+壁時計の固まりの上限 | seed で再現(返事の中身の決定論は別の条件=※R-128 ⑤) | 1 つ | 壁時計が延びるだけ(観測者は結果を後で読む) |

### 6-2 (B) 計算を割っても 1 つの結果に保つ形

| 実例 | 何を単位に割るか | 越境の扱い | 時計 | 決定論 | 結果の一意性 | 観測者への見え方 |
|---|---|---|---|---|---|---|
| EVE の星系とノード | 星系(ノードへ静的に割り当て・ダウンタイムに変える)[S7◎][S8◎] | 門のジャンプ=ノードの間のセッションの移り(一次は空欄) | ノードごと(TiDi) | 主張なし | ノードの中は書き手 1 人 | 混む星系は TiDi・強化は届け出 |
| Star Citizen の静的な mesh | 区域(territory)を server へ前もって割り当て [S9○][S13○] | entity の authority を streaming の範囲で次の server へ移す・ミサイルは複数の server を渡る [S9○] | server ごとの tick rate・replication layer は事象駆動 [S9○] | 主張なし(一部は client が権威)[S9○] | entity ごとに書き手 1 人・正本は replication layer [S9○] | 遅れは tick rate に出る・落ちれば一部が止まり持続から戻る [S9○] |
| Star Citizen の動的な mesh(QDSM まで) | 負荷の比で server を足す(今はインスタンスだけ)[S13○] | 同上 | 同上 | 主張なし | 同上 | 4.10 のインスタンス |
| SpatialOS | 空間(chunk・格子)を worker へ。負荷で entity を移す [S17◎][S18◎] | 猶予つきの移譲・猶予の間の命令は溜める・遅れた更新は捨てて数える [S15◎] | worker ごと(Runtime が見え方を合わせる)[S16◎] | 主張なし(移譲の結果は壁時計に依る=【見立て】) | entity-component ごとに書き手 1 人 [S21△] | 更新の頻度は問い合わせごと [S16◎] |
| PDES の保守的同期(※R-128 §2) | 論理過程(LP) | 時刻印つきの事象・lookahead・null message | LP ごと(局所の時刻の順) | 同時刻の順を固定すれば逐次と同じ結果 | 1 つ(逐次と同じ) | 該当なし |
| AI Metropolis(※R-73 §2) | 体(依存の規則で順序を外す) | 距離 ≤ 知覚の半径+速さ×時間の差なら待つ | 体ごとに先へ進む | 保守的(競合の訂正は要らない) | 全体同期と同じ結果を狙う | 該当なし |
| 本プロジェクトの T4(区域ごとの時計の腕・`engine/regional_clock.py:1-30`) | 500 m の格子の 29 区域+舞台の外。系は全員の配列を 1 回で処理(区域ごとに系を割らない) | 移動は窓の境目で数える・別の区域の発言は窓の終わりに届く・メッセージと電話は今は無い | 区域ごとの窓の頭・系の並びは全区域の窓の境目にそろう(障壁) | 既定と一致が条件(版上げなし) | 1 つ(全体で 1 つの時計と同じ) | 計器だけ |

- 読み(【見立て】): MMO の (B) は「実行中に矛盾しない 1 本の歴史」を保つ。本プロジェクトの (B) は「どう割っても同じ seed から同じ 1 本の歴史」を求める。後者は前者より強く、MMO の実例は満たしていない。満たしているのは PDES と、本プロジェクトの T4 の腕(区域の時計を置くが系は割らない)である。

## §7 本プロジェクトとの対応(【見立て】)

### 7-1 前提の確認(読むだけ・HEAD a800790)

| 所 | 事実 |
|---|---|
| `engine/scheduler.py:121-135` | 起床の順は `(offset_ns, class_rank, blake3 タイブレーク, agent_id)` の昇順。挿入の順は鍵に無い。11-03 §1-2 のとおり、既定のランでは呼ばれない |
| `engine/arbiter.py:438-456` | アービタの同順の鍵 `pk = wake_tiebreak_array(run_salt, int(tick), eff_class, agent)`。体ごとに決まり、区域にも処理の順にも依らない。ただし刻みの番号が入る(11-03 §5 v3-0a の対象) |
| `engine/arbiter.py:120-141` | 呼の予算は 1 日 400 万呼(40 万体の基準)から刻みあたりの予算を出す(`call_budget_per_tick`)。世界全体で 1 つの量 |
| `engine/regional_clock.py:1-30` | T4 の腕。区域の窓は互いを待たないが、系の並びは全区域の境目にそろう |
| ※R-55(等級 A) | 乱数は `derive_key(seed, domain)` の blake3 から Philox の鍵を作るカウンタ型で、呼ぶたびに新しい Generator を返す |

### 7-2 (A) 世界を遅らせる形が要求すること

| 要求 | 中身 | 先例との対応 |
|---|---|---|
| A-1 遅らせる単位は世界全体 | 1 つの時計(11-03 §4)なので、遅らせるのは世界全体になる。EVE 型(ノードごとの率)は区域ごとの時計の一種で、Q4 を採らない決定と合わない | AoE・Factorio・W1 は世界全体。EVE はノードごと |
| A-2 遅れは壁時計にだけ出す | 待つのは壁時計で、世界の時刻の進み(シミュ秒/事象)は変えない。TiDi の「時計に結びついた負荷を間引く」は、ここでは使えない。間引くと、どの体がいつ考えたかが GPU の速さに依る(※R-128 §0-4) | TiDi は世界の速さを変えても、遊ぶ人の体験(1 秒の重み)の問題だけで済んだ。本プロジェクトでは結果に効く |
| A-3 測る量は待ちの列 | TiDi の「待ちの tasklet の列」に当たるのは「適用の時刻が透かしに掛かっている未着の呼びの数」と「固まりの時間」。計器にはなるが、世界の判断には使わない | [S1◎]・※R-128 ⑥ |
| A-4 時計に載せないものの宣言 | TiDi の「時計を見るものは遅らせない」の逆で、本プロジェクトでは世界の規則はすべて世界の時刻に載る。壁時計に載るのは固まりの上限・送りの待ち・vLLM の priority など運用の量だけ、と宣言の表に書く | [S1◎][S2○] |
| A-5 速さの見え方 | 観測者は結果を後で読む人なので、TiDi の HUD に当たるのは manifest の計器(1 日の壁時計・世界の速さ=シミュ秒/壁秒・最長の固まり)。AoE の「速さは少しずつ変える」は遊ぶ人の体験のための規則で、ここでは要らない | [S22◎] |

### 7-3 (B) 割っても 1 つの結果を保つ形が要求すること

| 条件 | 中身 | 今の状態 | 先例 |
|---|---|---|---|
| B-1 鍵と乱数が区域と処理の順に依らない | 同時刻の鍵(時刻 → 種類の順位 → ハッシュ)と乱数の鍵が、体・事象の時刻・ラン seed だけで決まる。区域の番号・worker の番号・挿入の順を入れない | 11-03 §4 で決定。アービタの `pk` と R-55 の鍵は体ごとに決まる。刻みの番号を世界の時刻から作る形に替えるのが v3-0a | AoE の種の同期・Fiedler の種=frame 番号 [S22◎][S25◎]・MATSim の ID の順+乱数(※R-133 §1-2) |
| B-2 全体に効く量の合流 | 刻みあたりの呼の予算とアービタの全体の順は、世界全体で 1 回決まる。割った部分ごとの候補を B-1 の鍵で k 本の併合(k-way merge)すれば、割り方に依らない。合流は時刻の量子(1 秒の格子か窓)ごとの障壁になる | 今は 1 過程なので問題は表に出ない | PDES の LBTS(※R-128 §2)。MMO には相当する先例が無い(書き手を 1 人にするだけ) |
| B-3 越境は世界の時刻の境目で渡す | 境目をまたぐ作用(移動・声・視線・電話)を、割った部分の間の事象として時刻印つきで渡す。lookahead は歩く速さ×距離・声の届く距離・知覚の遅れから出る。電話とメッセージは距離に依らないので lookahead が縮む | T4 は窓の終わりに届ける形を計器で持つ。電話は今の世界に無い | PDES の lookahead(※R-128 §2)・※R-73 §2-4・AI Metropolis の依存の式 |
| B-4 持ち主の割り当ては決まった時刻にだけ変える | 割り当てを負荷で随時変えてよいのは、結果が割り当てに依らないと示せたときだけ。そうでなければ、割り当ては日の境目や checkpoint など決まった時刻に、予定で変える。SpatialOS の「猶予の後に移し、遅れた更新は捨てる」は壁時計に依るので持ち込めない | 割らないので未定 | EVE のダウンタイムの割り当てと強化の届け出 [S7◎][S8◎]・Star Citizen の静的 mesh [S9○]・SpatialOS の移譲 [S15◎] |
| B-5 浮動小数の集計の順を固定する | セルや全体の集計(人数・金額・混雑)を割った部分ごとに足して合わせると、足す順が変わり下の桁が変わる。整数か固定小数で持つか、体の id の順で足す | 1 過程の NumPy の集計は配列の並びに依る(【推測】=個々の集計の型は未確認) | Fiedler の浮動小数の注意 [S25◎]・AoE のチェックサム [S22◎] |
| B-6 割り方を変えた 2 ランの一致を試験にする | 割らない 1 過程・2 分割・29 区域などで回し、byte で比べる。ずれたら、部分ごとのチェックサムで最初にずれた時刻と欄を出す | T4 は既定と 19 構成一致が条件(記録 `docs/bench/analysis/wallbounce-1012/tm234/README.md`) | AoE・Factorio の同期外れの検査(※R-72 §4) |

### 7-4 艦隊(LLM)の遅れが支配する前提での読み

- 1 日の壁時計の大半が艦隊の待ちで、エンジンの計算は小さい(※R-73 の AI Metropolis では模擬の時間の約 95% が LLM の推論)。この前提では、エンジンを割って得る速さは小さい。割る意味が出るのは、(1) 35 万体のエンジンの 1 秒の格子の処理が艦隊の待ちを上回る時間帯(深夜の静かな時間など)と、(2) 艦隊を待たない部分(W2 の依存を見て進める範囲)を先に進めたいとき、の 2 つになる【見立て】。
- (2) は計算を割る話ではなく、透かしを依存の範囲で緩める話である(※R-133 §6-2 W2)。区域の時計を持たずに、1 つの時計のまま「この事象は未着の呼びの影響範囲の外」と判定して先に処理する形になる。B-1〜B-3 と同じ条件(鍵が区域に依らない・影響範囲の計算が漏れない)を要求する。
- 艦隊の遅れを世界に漏らさない条件(※R-128 §0-4)は、(A) と (B) のどちらでも同じである。GPU の空きで誰が考えるかを決めない。輸送の層の待ちは世界から見えない所に閉じる。

## §8 決めるべき題(選択肢と根拠・推薦なし)

| 題 | 選択肢 | 根拠(本書の節) |
|---|---|---|
| R1 (A) の形 | (a) 世界全体が適用の時刻で待つ(W1・AoE/Factorio 型)/(b) 依存の範囲の外を先に進める(W2・AI Metropolis 型)/(c) 区域ごとに遅らせる(EVE 型。Q4 を採らない決定と合わないので、比べる腕としてだけ残すか消すか) | §2・§5-2・§6-1・§7-2 A-1 |
| R2 遅れの計器 | (a) 世界の速さ(シミュ秒/壁秒)と未着の呼びの数と最長の固まりを manifest の計器にする/(b) (a) に加え、TiDi の率に当たる値を時刻ごとに記録する/(c) 計器は 1 日の壁時計だけ | §2-1 測り方・§7-2 A-3・A-5 |
| R3 割る単位(将来) | (a) 空間(セル・区域。EVE・Star Citizen・SpatialOS)/(b) 体の id のハッシュ(空間に依らない)/(c) 系(処理の種類)/(d) 割らずに 1 過程のまま透かしだけ緩める | §6-2・§7-4 |
| R4 割り当てを変える時刻 | (a) 固定(EVE の常時・Star Citizen の静的)/(b) 日の境目や checkpoint だけ(EVE のダウンタイム)/(c) 負荷で随時(SpatialOS・動的 mesh。結果が割り当てに依らないと試験で示すことが前提) | §2-2・§3・§4・§7-3 B-4 |
| R5 越境の渡し方 | (a) 時刻印つきの事象として境目で渡す(PDES・T4)/(b) 読み取り専用の写し(影)を隣に置く(Star Citizen の client view・SpatialOS の interest)/(c) 持ち主ごと移す(移譲)。副問: 電話とメッセージの lookahead | §3・§4・§7-3 B-3 |
| R6 全体に効く量 | (a) 刻みあたりの呼の予算とアービタの順を、時刻の量子ごとに決まった鍵で全体へ合流する/(b) 部分ごとに予算を配る(結果が変わる=版上げ)/(c) 全体の量を無くす(L4 は監査線のまま=今の宣言を確かめる) | §7-1・§7-3 B-2 |
| R7 浮動小数の集計 | (a) 整数か固定小数に/(b) 体の id の順で足す/(c) 許して分布で合格にする(10-13b §0-6 の「整理の段で無理なとき」の扱い) | §5-2・§7-3 B-5 |
| R8 一致の検査 | (a) 割り方を変えた 2 ランの byte 比較を試験に入れる(T4 と同じ形)/(b) (a) に加え、部分ごとのチェックサムで最初のずれを出す道具を作る(AoE・Factorio 型)/(c) 割る段が来るまで作らない | §5-2・§7-3 B-6 |
| R9 艦隊の遅れの閉じ込め | (a) 輸送の層の待ちだけに閉じる(※R-128 §4・①)/(b) (a) に加え vLLM の priority に適用の時刻を渡す(壁時計だけ短くなる)/(c) 遅れを世界に入れる腕(W3)を比べる腕として残す | §7-4 |
| R10 時計に載せないものの宣言 | (a) 壁時計に載る量の表(固まりの上限・送りの待ち・priority)を宣言の表に足す/(b) 用語集の「世界の中の思考時間と GPU の待ち時間」の行に注を足すだけ/(c) 足さない | §2-3・§7-2 A-4 |

- 遅延補償の問い(返事の前提を、撃った時刻の世界で確かめるか、適用の時刻の世界で確かめるか)は、※R-133 §4-4 の上書きの題(O1〜O3)と重なるので、ここでは題にしない。Gambetta の遅延補償 [S26◎] は「撃った人の見た過去」で判定する側の先例になる。

## §9 出典(読んだ日はすべて 2026-11-03)

| # | 出典 | URL | 等級・読めた範囲 |
|---|---|---|---|
| S1 | CCP Veritas, Introducing Time Dilation (TiDi), 2011-04-22 | https://www.eveonline.com/news/view/introducing-time-dilation-tidi | ◎ 本文 |
| S2 | EVE University Wiki, Time Dilation(最終編集 2024-02-11・CC BY-SA 4.0) | https://wiki.eveuniversity.org/Time_Dilation | ○ 二次(一次の forum の頁が読めないため) |
| S3 | Data Center Knowledge, Experiencing Heavy Server Load? Just Slow Down Time, 2013-01-31 | https://datacenterknowledge.com/servers/experiencing-heavy-server-load-just-slow-down-time | ○ 二次(Veritas の発言の引用) |
| S4 | Engadget, EVE Online's time dilation keeping game in sync, 2012-02-09 | https://www.engadget.com/2012-02-09-eve-onlines-time-dilation-keeping-game-in-sync.html | ○ 二次(Veritas のブログの紹介) |
| S5 | CCP Mindstar, My node was equipped with the following..., 2008-10-06 | https://eveonline.com/article/my-node-was-equipped-with-the-following... | ◎ 本文 |
| S6 | EVE Online Team, Tranquility Tech IV, 2023-03-08 | https://www.eveonline.com/news/view/tranquility-tech-iv | ◎ 本文 |
| S7 | CCP Falcon, Changes To The Fleet Fight Notification System, 2018-01-22 | https://www.eveonline.com/news/view/changes-to-the-fleet-fight-notification-system | ◎ 本文 |
| S8 | CCP Convict, Fleet Fight Notification Tool, 2020-07-10 | https://www.eveonline.com/news/view/fleet-fight-notification-tool | ◎ 本文 |
| S9 | CIG, Server Meshing and Persistent Streaming Q&A(Comm-Link 18397・CitizenCon 2951 の後) | 公式: https://robertsspaceindustries.com/comm-link/SCW/18397 ・写し: https://star-citizen.wiki/Comm-Link:18397/en | ○ 公式の頁は JS で本文が出ず、ファンの wiki の転載を読んだ(写しの日付の欄は誤り) |
| S10 | CIG, Letter From the Chairman(Comm-Link 19848・2024-03) | https://api.star-citizen.wiki/comm-links/19848 | ○ 転載 |
| S11 | CIG, Roadmap Roundup - October 4, 2023(Comm-Link 19505) | https://api.star-citizen.wiki/api/comm-links/19505 | ○ 転載(replication layer の節だけ) |
| S12 | CIG, Star Citizen Alpha 4.0 Preview patch notes, 2024-12-19(Comm-Link 20360) | https://api.star-citizen.wiki/comm-links/20360 | ○ 転載 |
| S13 | CIG, Letter From the Chairman, 2026-08-27(Comm-Link 21301) | https://starcitizen.tools/Comm-Link:Letter_from_the_Chairman_-_2026-08-27 | ○ 転載 |
| S14 | Star Citizen Wiki, Server meshing | https://starcitizen.tools/Server_meshing | ○ 二次(本文では数値を使っていない・一次の場所の索引として読んだ) |
| S15 | Improbable Worlds, US10878146B2 Handover techniques for simulation systems and methods(公開 2020-12-29・優先日 2016-08-24) | https://patents.google.com/patent/US10878146B2/en | ◎ 移譲・猶予・計器の節 |
| S16 | Improbable Worlds, US10579434B2 Simulation systems and methods using query-based interest(公開 2020-03-03) | https://patents.google.com/patent/US10579434B2/en | ◎ interest・頻度・ヒステリシスの節 |
| S17 | Improbable Worlds, US10303821B2 Load balancing systems and methods for spatially-optimized simulations | https://patents.google.com/patent/US10303821B2/en | ◎ chunk と移す手順の節 |
| S18 | spatialos/gdk-for-unity `cloud_launch.json`(MIT・2022-01 archive) | https://github.com/spatialos/gdk-for-unity/blob/master/cloud_launch.json | ◎ 全文 |
| S19 | spatialos/gdk-for-unity `UPGRADE_GUIDE.md` | https://github.com/spatialos/gdk-for-unity/blob/master/UPGRADE_GUIDE.md | ◎ 該当の節 |
| S20 | spatialos/UnrealGDK `README.md`(MIT・2022-01 archive) | https://github.com/spatialos/UnrealGDK | ◎ 全文 |
| S21 | Barker (Improbable), SpatialOS for Military Simulation and Training, NATO STO-MP-MSG-175, 2019-09-26 | https://www.sto.nato.int/publications/STO%20Meeting%20Proceedings/STO-MP-MSG-175/MP-MSG-175-01P.pdf | △ 本文は 404。検索の抜粋だけ |
| S22 | Bettner・Terrano, 1500 Archers on a 28.8: Network Programming in Age of Empires and Beyond, 2001-03-22 | https://www.gamedeveloper.com/programming/1500-archers-on-a-28-8-network-programming-in-age-of-empires-and-beyond | ◎ 本文(※R-72 #36 と同じ) |
| S23 | Wube, Factorio Friday Facts #76(2015-03-06)・#83(2015-04-24)・#147(2016-07-15)・#149(2016-07-29) | https://www.factorio.com/blog/post/fff-83 ほか同じ形の URL | ◎ 該当の節 |
| S24 | Factorio Wiki, Desynchronization | https://wiki.factorio.com/Desynchronization | ◎ 全文(※R-72 #37 と同じ) |
| S25 | Fiedler, Deterministic Lockstep, 2014-11-29 | https://gafferongames.com/post/deterministic_lockstep/ | ◎ 前半 |
| S26 | Gambetta, Fast-Paced Multiplayer Part III(Entity Interpolation)・Part IV(Lag Compensation) | https://www.gabrielgambetta.com/entity-interpolation.html ・ https://www.gabrielgambetta.com/lag-compensation.html | ◎ 本文 |
| S27 | Epic Games, Replication Graph(Unreal Engine の文書) | https://dev.epicgames.com/documentation/en-us/unreal-engine/replication-graph-in-unreal-engine | ◎ 冒頭と節の一覧 |
| S28 | Liu・Theodoropoulos, Interest management for distributed virtual environments: A survey, ACM CSUR 46(4):1-42, 2014 | https://doi.org/10.1145/2535417 | ○ 要旨(Crossref)。本文は 403 |
| S29 | Boulanger・Kienzle・Verbrugge, Comparing interest management algorithms for massively multiplayer games, NetGames '06 | https://doi.org/10.1145/1230040.1230069 | ○ 書誌だけ |

- 数え方: 表の 29 行のうち S23 は FFF 4 本なので 1 本ずつ数え、計 32 本。◎ 20(S1・S5〜S8・S15〜S20・S22・S23 の 4 本・S24〜S27)・○ 11(S2〜S4・S9〜S14・S28・S29)・△ 1(S21)。
- コードは写していない。GitHub の SpatialOS の 2 つのリポ(MIT)は読んだだけ。

## §10 読めなかったもの

1. EVE の forum の記録(forums-archive.eveonline.com の Time Dilation Video Demo の議論・2012-01 の「既定で有効」の告知)は 503 で読めなかった。10% の下限が自動の規則として決まった経緯(2011-10 の Veritas の発言)は、検索の抜粋でしか見ていない(△)。本文の 10% は [S2○][S3○] による。
2. 2012-02 の Veritas の TiDi の結果のブログ(グラフつき)の本文は見つけられなかった。「12 日で 12.87 時間ぶんの模擬の時間が遅れで消えた」という数値は、検索の抜粋(PC Gamer)に出たが、PC Gamer の頁は本文が取れず、本書では使っていない。
3. EVE で、遅れの率の違うノードの間を門で移るときの扱い(セッションの移り・時計の受け渡し)の一次の記述は見つけていない。
4. Star Citizen の CitizenCon の講演(2951・2953・2954・2955)の動画は読んでいない。講演の文字起こしの掲示(Frontier の forum)は 403。Massively OP の 2026-02 の CTO の配信の記事も 403。
5. Star Citizen で server の tick rate が下がったとき、世界の時間の進みがどうなるか(遅れるのか、刻みが粗くなるのか)の一次の記述は見つけていない。
6. SpatialOS の公開の文書(documentation.improbable.io・networking.docs.improbable.io)は応答しない。web.archive.org は取得の道具が受け付けなかった。authority・interest・負荷の分け方は特許と GDK の設定から読んだ。NATO の資料(S21)は 404。
7. Valve の Source Multiplayer Networking(遅延補償の原典の 1 つ)は 403。代わりに Gambetta を読んだ。
8. interest management の総説(S28)と比べの論文(S29)の本文は読めていない。AOI の分類(格子・aura・領域)の比べの数値は本書に書いていない。
9. Dual Universe(1 つの shard の連続した並列)・Hadean・Improbable の後継(Morpheus)は探していない。

## 親の一次確認(第343・2026-11-03・親)

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| EVE の TiDi は tasklet の待ちの列が小さく保たれるまで時計を細かく遅らせる(98% もありうる)[S1] | CCP の dev blog(2011)を curl で読んだ | **一致**(「maintain a very small queue of waiting tasklets」「run at 98% time」)。下限 10% は答申どおり二次 [S2][S3] の値で、一次は未確認 |
| 発注文の R-128 のファイル名 | docs/research を見た | **親の書き違い**=実在は `v2-r128-backpressure-design-pdes-watermarks.md`(答申はこちらを引いている) |
| 取り方 | 答申の冒頭の注 | 途中から curl の標準出力で読んだ(保存なし)。Valve の頁でブラウザの UA を付けた取得は自動の分類器に止められ、その後は試していない(ユーザーに報告する) |
| 形式 | 行数・改行・絶対パス・秘密 | 272 行・LF・絶対パスなし・CLEAN |

- 等級: **B**(主な数値を親が原典で 1〜2 点ずつ確かめた。ほかの出典は答申の ◎○△ のまま)。
- 共通の注: 作業の途中で、実装役・リサーチ役の WebFetch と WebSearch が利用の上限で止まった。後半は curl の標準出力を文字だけにして読んだ(ファイルの保存なし)。空欄は本文の「読めなかったもの」のとおりで、記憶では埋めていない。
