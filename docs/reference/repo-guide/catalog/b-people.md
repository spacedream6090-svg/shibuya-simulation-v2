# 機能のカタログ B 人の中身(把握の資料 段 2)

> 発注は [返事その 6](../../../design/prompt-2026-11-05-reply6.md) §3-1 の 3 です。今のコードの現状を書きます。あるべき姿は [仕様書](../../../design/spec/) の担当なので、ここには書きません。
> 正はコードです。HEAD `15b6bbd` のコードを読み、既定の値は `shibuya.cli.main` の引数の定義(引数なしの `parse_args` の結果)と各腕のモジュールの `arm()` を、`SHIBUYA_*` の環境変数なしで Python で読み出して確かめました。ランは回していません。`data/` は開いていません。
> 実測の数値は記録からの写しです。出どころの #番号(IMPLEMENTED)の日付より後の版上げで、値が変わっている場合があります。

## 読み方

- 区分の 既定・腕・器・無い は [段 1](../day-flow.md) §0-3 と同じです。「既定のラン」は段 1 §0-2 のとおり、`python -m shibuya.cli` を引数なし・`SHIBUYA_*` の環境変数なしで起動したランです。「旧道」は旧値の再現のためだけに残る切替口で、腕に数えません(段 1 §10-2)。
- 語は [用語集](../../../design/v2-glossary.md) と段 1 §0-4 の語で書きます。
- 元の決定は [索引](../../../design/decision-id-index.md) の ID の形です。`#N` は [IMPLEMENTED](../../../../IMPLEMENTED.md) の番号、`routing #N` は [判断の行き先の表](../../decision-routing-2026-11-01.md) の番号です。索引に行の無い番号(D-118 など)は「索引に行なし」と書き、#N で辿れるようにしました。
- 状態の表の「腕の中」は、上の腕を立てたランでだけ効く下の切替口です。「感度の値」は値を振るだけの引数で、段 1 §10-2 と同じく腕に数えません。
- 指紋は [仕分けの表 11-04](../../behavior-audit-triage-2026-11-04.md) の行 ID と区分 V/K/D/E です。表の行番号は HEAD `90258ef` のもので、今の行とはずれています。
- 棚卸しの範囲は [A](../../behavior-audit-A-perception-decision-2026-11-02.md)(知覚と判断)と [B](../../behavior-audit-B-resolve-world-2026-11-02.md)(解決と世界)です。「表の path の欄に出てきません」は指紋が無いという意味ではなく、棚卸しの範囲の外という意味です。path の欄を機械で引いて確かめました。
- 「コードの読み」は、コードを読んで確かめたがランの件数は数えていないという印です。
- 別のグループとの境は次のとおりです。席と列の本体・歩行は A 群、経済と台帳・権利・判断の口・知覚・起床は C 群の担当で、ここでは接する所だけ書きます。
- 〔11-09〕[段 2 の突き合わせ](../../stage2-crosscheck-2026-11-05.md)の食い違いと書き漏れを、HEAD `14b151a` のコードで確かめて直しました。直した所の一覧は末尾の「11-09 の直し」です。#番号の実測の値と、決定の原文との差の「決定の側」は、突き合わせでもコードでは確かめていません(記録の値・原文は開いていない)。

### 考える担い手(全部の節に共通)

- 既定のランで答えるのは mock(決まった乱数で答える代役)です。判断モデルの**中身**は src にありません。腕(連絡 `--contact c1`・カレンダー 1b・2・3・店の仕事 `--duties arm`)には判断モデルを**呼ぶ口**があり、仮のモデル(mock)が候補から一様に選びます。manifest と日次の記録の `calls_by_model.judge_model` はその呼数で、既定のランでは 0 です(`engine/run.py` の `_calls_by_model`)。
- 腕の層の判断の口と文の口は、コードで仮のモデルに固定されています(`contact/layer.py` の `ContactPort`・`MockTextPort`、`duties/layer.py` の `DutiesPort`、`calendar2/layer.py` の `Calendar2Port`、`calendar3/layer.py` の `Calendar3Port`、`calendar_self.py` の `CommuteMockPort`=古典の方策のランだけ `CommuteClassicalPort`)。**`--llm fleet` を選んでも、連絡・店の仕事・カレンダーの判断と文は艦隊へ行きません。** 艦隊へ行くのは主の判断の呼び(会話の番を含む)だけです。
- 「よく考えるかを決める段」は無いと宣言されています(`absent.deliberate`・routing 95。宣言の文の「L2」は判断の行き先の層の語で、思考時間の段の既定は L1=段 1 §11 の #14)。
- 判断の口の腕 `--decision-port {legacy,port}`(既定 `legacy`・環境変数 `SHIBUYA_DECISION_PORT`)。`port` のとき mock の代わりに `MockPort`(同じ乱数の鍵で同じ番号)・`ClassicalPort`・`LlmPort` を口に通します(`engine/decision/layer.py`・`decision/ports.py`)。本体は C 群 C11 です。

## 0. 一覧

足した印は、発注のリストに無く、近い機能として足したものです。

| # | 機能 | 状態 | 主なファイル |
|---:|---|---|---|
| 1 | 購入 | 既定。無い=品と数を選ぶ・値段を見て見送る | `engine/resolve.py`・`engine/commit.py` |
| 2 | 店選び(足した) | 既定=今のセルの候補の絞り込みと最寄りの選び手(候補の距離は全部同じなので、実際は可視の降順 → 番号で決まる)。腕=`--chooser classical`・想起優先 | `engine/poi_target.py`・`engine/chooser.py`・`engine/store_choice.py` |
| 3 | 食事と空腹 | 既定=店の食事・舞台の外の自動の食事・エネルギー収支。腕=`--home-meal plan` ほか 5 本。無い=家で食べる | `engine/resolve.py`・`engine/energy.py`・`engine/body/rules.py` |
| 4 | 会話 | 既定=招待とセッション(言葉なし)。腕=`--conv-max-participants 3`。器=応答率 0.8 ほか。無い=3 人目 | `engine/conversation.py`・`engine/systems/talk.py`・`engine/run.py` |
| 5 | 近接の判定(足した) | 既定=`--proximity distance`。感度の値=`--proximity-d` | `engine/proximity.py`・`engine/spatial_index.py` |
| 6 | 発話の口(足した) | 腕=`--speech-port on`。無い=ひと言(既定) | `engine/speech/` |
| 7 | 会話の時計(足した) | 腕=`--talk-clock mora`(計器だけ) | `engine/speech_clock.py` |
| 8 | 記憶 | 腕=`--memory on` と下の腕 5 本。器=印象・浅い痕跡。無い=1 日の振り返り | `engine/memory.py`・`engine/memory_store.py`・`engine/memory_m1.py` |
| 9 | 店の評価の記憶と口コミ(足した) | 腕=`--store-memory on`。器=ネットの枠 | `engine/store_memory.py`・`engine/wom.py` |
| 10 | 親しみ | 腕=`--familiarity on` | `engine/familiarity.py` |
| 11 | 関係 | 腕=`--relations on`・`--memory-people memory` | `engine/relations.py`・`engine/relations_people.py` |
| 12 | カレンダーと予定 | 既定=暦の口・日課表 W17。腕=`--calendar-shadow 1a`・`--calendar 1b`・`--calendar-2 arm`・`--calendar-3 arm`。無い=予定を考え直す | `engine/calendar.py`・`engine/calendar_shadow.py`・`engine/calendar_self.py`・`engine/calendar2/`・`engine/calendar3/` |
| 13 | 連絡 | 腕=`--contact c1`。器=道具の台帳と店の番号の表 | `engine/contact/`・`engine/tools/` |
| 14 | 店の仕事 | 既定=開閉・補充・納品をコードが動かす。腕=`--duties arm`。無い=売れ残りの廃棄・接客・値段を変える | `engine/processes/opening.py`・`engine/processes/goods_flow.py`・`engine/duties/` |
| 15 | 意図の保持と活動層(足した) | 既定 | `engine/intent.py`・`engine/activity.py` |
| 16 | 手伝い・断る・通報(足した) | 語は既定で受けるが効果が無い。手伝いと断るの効果は無いと宣言 | `engine/resolve.py` |
| 17 | 人物の文(足した) | 器 | `engine/decision/persona.py` |

パスの頭の `src/shibuya/` は表の中では省きました。

## 1. 購入

### 何をしているか

答えが「購入」か、対象が飲食店でない「並ぶ」のとき、対象の店で 1 個買います。対象の決め方は 2 節です。`resolve._apply_buy` は、対象がある → 営業中 → 棚に在庫がある → 払える → 席がある、の順に確かめます。失敗の結果は順に BAD_TARGET・CLOSED・OUT_OF_STOCK・MONEY_SHORT です。

満席は失敗にしません。列に入り、活動は WAITING、直前の結果は OK になります。席が空くと、並んだ順に席へ入り、並んだときの行為を完了します(`resolve._serve_poi_queue`)。

完了(`resolve._complete_buy`)で動くものは次のとおりです。金の台帳(`purchase_many`)・物の台帳の棚(`sell_many`)・`world.pois.stock`(棚の合計の写し)・店の売上の写し(税抜き)・本人の持ち物の数 `holdings` +1・活動 SHOPPING・在席の登録です。飲食系の店で買うと空腹が少し戻ります(3 節)。買った物の中身は体に持たせず、個数だけを持ちます。持ち物のある体は 19 時に 1 個使います(過程 `waste` の `_household_consumption`)。

同じ刻みに同じ店へ来た買い手は、取り合いの決着で `min(1 刻みの受け入れ数, 棚の在庫)` に絞られ、超えた分は LOST_ARBITRATION です(`commit.ResourceSpace.capacity`・`arbitrate_resources`)。受け入れ数は合成の世界も本番の世界も 4 です(`world/assets.py` の `SYNTHETIC_POI_CAPACITY`)。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 確かめと完了(1 回 1 個) | 既定 | 語彙 v3 の語。切替口なし |
| 満席で列に入る・席が空いたら入る | 既定 | `--queue-service` 既定 on。off は第267 以前の挙動(誰も捌かない) |
| 支払いの方法・レジの税 | 既定 | `--economy-stage2` 既定 on(`economy_stage2.DEFAULT_ARM`)。中身は C 群 |
| 19 時に持ち物を 1 個使う | 既定 | 切替口なし |
| 品と数を選ぶ | 無い | `absent.item_qty` |
| 値段を見て見送る | 無い | `absent.price_balk` |
| 購入で空腹 −4 | 旧道 | `--hunger-model v1` のときだけ(既定 energy) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `_apply_buy`・`_complete_buy`・`_apply_queue`・`_serve_poi_queue`・`_payable`・`consume` |
| [src/shibuya/engine/commit.py](../../../../src/shibuya/engine/commit.py) | 答えから対象と資源を決める `intents_from_responses`・取り合いの決着 `arbitrate_resources` |
| [src/shibuya/engine/systems/act.py](../../../../src/shibuya/engine/systems/act.py) | 系 `phase_a`・`phase_b`・`phase_c` |
| [src/shibuya/engine/processes/crowd.py](../../../../src/shibuya/engine/processes/crowd.py) | 席数・`can_admit`・列の目的 `queue_action`(本体は A 群) |
| [src/shibuya/engine/processes/goods_flow.py](../../../../src/shibuya/engine/processes/goods_flow.py) | `WasteCollectionProcess._household_consumption`(19 時の 1 個) |
| [src/shibuya/world/assets.py](../../../../src/shibuya/world/assets.py) | `SYNTHETIC_POI_CAPACITY`・価格と初期在庫の読み口 |
| [src/shibuya/world/processes/absent.py](../../../../src/shibuya/world/processes/absent.py) | 「無い」の宣言 |

### 元の決定

`09-24d/D-114`・`09-25/D-114`(候補を絞るのはエンジン、選ぶのは本人)・`09-24d/D-113`・`09-25/D-113`(列を捌く=#43)・`11-03/M11`・`11-03/M28`・`11-03/§3`(#138)・`11-01/§10-3`(無いと宣言・routing #37・#38)。段の実装は #52・#54。

### 棚卸しで見つかった指紋

- V: B1(受け入れ=min(4, 在庫)・影響 大)・M8(同じ刻みの席と最後の 1 個を行の順で決める)・S11(棚を超える買い手を行の順で OUT_OF_STOCK)・A18(着いた意図の順位の鍵)
- K: M2(満席なら自動で列へ)・S7(「並ぶ」の対象が飲食店なら食事へ)・F2(列を捌く処理が新しい行為より先)・F4(列の印が消えない道)
- D: A36(失敗の観測値がセルの全 POI の最安の値と最も早い開店の時)
- E: S12(保存則・払い出しを最大 8 回スロットを回す。〔11-09〕今のコードでは起きない=既知の穴)・S13(保存則・持ち物 255 で頭打ち)・M11(物理・列の印)・M28(制度の手順・列から席へ入る前の支払いの確かめ)

### 既知の穴

- `absent.py` の 2 件の宣言(品と数・値段)。値段は買えなかった後にしか見えません。
- 仕分けの表が直す対象と書く行が 2 つあります。S12 は 9 スロット以上の店の偽の品切れ、S13 は 256 個目で物が消える件です。〔11-09〕S12 は今のコードでは起きません。`GoodsLedger.sell_many` が 1 回の呼びで全スロットをまたいで払い出します(2026-09-08 の直し)。12 スロットの店で確かめました(C 群 C1 の既知の穴)。既定の SKU の登録簿はスロットが最大 3 です。
- F2 と F4 は [fix4 の記録](../../../bench/analysis/fix4-1103/README.md) §8 の残りです。列を離れた体は既定のランで 9 体でした(同 §1-1)。
- 19 時に全員が 1 個使う規則は、外すかが問いのまま残っています(routing #41・[PENDING](../../../../PENDING.md) §1-1)。
- 実績は 5,000 体・seed 1・mock・1 日で、満席で並んだ 166 回、列から席へ入った 117 回です(fix4 §1-1)。

### 文書とコードの差

- `resolve._apply_buy` の docstring は「売上+同額」と書いています。コードは税を引いた額を `world.pois.revenue` へ足します(`net = paid - tax`・#101 V4)。

## 2. 店選び(足した)

### 何をしているか

購入・食事・並ぶの答えから、どの店にするかを決めます。mock の対象はこれらの語では「なし」なので(`mock._render_v3`・描画は候補を渡しません)、既定のランはこの節の「なし」の道を通ります。

`TargetResolver.classify` が対象の欄を読みます。読み順は、総称語(店・店舗・ショップ・お店)→ なし、全体がカテゴリ語 → カテゴリ、合成名 `food1954` の形 → 名指し、POI 名 → 名指し、カテゴリ語を含む → カテゴリ、それ以外 → なし、です。カテゴリ語の対応表は 59 語です(`CATEGORY_WORDS`)。

候補は今のセルの POI のうち、意図に合い(食事=飲食店・購入と並ぶ=`BUYABLE_CATS` の 7 種)、カテゴリが合い、営業中で、購入と並ぶは棚の在庫があるものです。ただし購入と並ぶでも、飲食店の POI は棚の在庫を見ずに候補に残ります(`poi_target.py` の `stock_ok[is_open] | eatery[is_open]`=「並ぶ」が食事へ回る道のため)。在庫が 0 の飲食店が購入の候補に残ると、後で `_apply_buy` の OUT_OF_STOCK か取り合いの決着で落ちます(コードの読み・件数は未確認)。候補が無ければ理由を分けて対象を置き、`resolve` の既存の判定が結果を付けます(`NO_CANDIDATE_REASONS`)。名指しの店が見えているとき、カテゴリの店が近くにあるときは、歩く意図に変えます(15 節)。

選び手は分布を返し、`draw_index` が 1 つ引きます。既定の `NearestChooser` の規則は、距離の昇順 → 可視(視点数)の降順 → POI の番号、の先頭 1 件に確率 1.0 です(`chooser.py`)。ただし既定の道の候補は今のセルの POI だけで(`poi_target.py` の `cand_all = base`=`pois_in_cell`)、選び手に渡す距離は `cell_dist[今のセル, 店のセル]`=全候補で同じ値です。このため既定のランの店選びは、実際には**可視の降順 → 番号**で決まります(今のセルの中で最も見える店)。距離が効くのは、ほかのセルの店を見る `_pick` の道(見えている名指しの店・近くのカテゴリの店へ歩く意図を作るとき)だけです。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 対象の欄の読み・候補の絞り込み | 既定 | 切替口なし(組み立てが毎回 `TargetResolver` を作る) |
| 最寄りの選び手 | 既定 | `--chooser` 既定 `nearest` |
| 古典の選び手(習慣と満足化) | 腕 | `--chooser classical`・`--classical-habit-p` 既定 0.5・`--classical-tau` 既定 1.0。習慣の項は `--familiarity on` のときだけ |
| 想起優先の候補合成 | 腕 | `--memory on`・`--store-memory on`・`--chooser classical` の 3 つがそろったときだけ |
| カテゴリ語の近傍の探索の幅 | 感度の値 | `--move-search-radius` 既定 5 セル |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/poi_target.py](../../../../src/shibuya/engine/poi_target.py) | `TargetResolver`(読み・候補・移動の行き先 `resolve_move`・計数)・`CATEGORY_WORDS`・`BUYABLE_CATS` |
| [src/shibuya/engine/chooser.py](../../../../src/shibuya/engine/chooser.py) | 選択器の口 `Chooser.probs`・`NearestChooser`・`ClassicalChooser`・`draw_index` |
| [src/shibuya/engine/store_choice.py](../../../../src/shibuya/engine/store_choice.py) | 想起優先 `StoreChoice`・決め手の記録・`walk_m_per_tick` |

### 元の決定

`09-24d/D-114`・`09-25/D-114`・`09-25/D-112`・D-119(索引に行なし・#58)・D-120(索引に行なし・#64)・`11-01/§10`(routing #25〜#27)。段の実装は #52・#53・#58・#64。

### 棚卸しで見つかった指紋

- K: A01(距離 → 可視 → 索引の先頭 1 件・影響 大)・A19(全部閉店なら代表 1 件で即時に失敗)・A20(見えない名指しは失敗)・A21(カテゴリ語の近いセル 5 個)・A22(対応表 59 語)・A23(読み順)・A37(〔腕〕届く店の式)・A38(〔腕〕習慣 0.5・揺らぎ 1.0)
- V: A54(店の抽選の鍵が刻みの番号を含む)・A69(`store_choice` の引数の既定 60 秒)
- D: S10(選び手が無いときの最小の番号=旧道の形)

### 既知の穴

- 既定の最寄りは `chooser.py` が「憲法⑥の宣言つき暫定」と書いています。本来は本人の選び手の仕事です。
- 既定の道の店選びでは距離が効きません。既定のランの「最寄り」は、今のセルの中で最も見える店です(上の何をしているか)。
- 名指しの店が今のセルから見えなければ失敗します(A20)。記憶から店を思い出して歩くのは腕の想起優先だけです。
- `09-30/M17` の「親しみを候補へ入れる」接続は未実装です(10 節)。

### 文書とコードの差

- `poi_target.py` の docstring の手順 2 は「現在セルに無い名指しは段 2c=いまは失敗」と書いています。既定のランは意図の層が立つので(`IntentLayer` は語彙 v3・`--activity on` で作る)、見えている名指しの店へは歩きます。docstring の段 2c の段落が今の挙動です。
- CLI の `--chooser` の help は nearest の並びを「可視の降順 → POI 索引」と書き、選び手の docstring とコードの「距離 → 可視 → 索引」と違っていました。11-09 に help を「規則は距離 → 可視 → 索引。候補が今のセルだけなので実際は可視 → 索引」の形に直しました(help は `--help` の表示だけで、ランの出力に入らない)。

## 3. 食事と空腹

### 何をしているか

店の食事は `resolve._apply_eat` です。対象が飲食店 → 営業中 → 払える → 席がある、の順に確かめ、失敗は NOT_IN_EATERY・CLOSED・MONEY_SHORT です。満席は購入と同じく列に入ります。完了(`_complete_eat`)で金は購入と同じ道を動き、棚と持ち物は動きません。

空腹はエネルギー収支です(`engine/energy.py`)。

- 消費は毎刻み EER/1440 × METs/1.379 です。`hunger` の段はこの結果の写しです。
- 語は 食後の消費 ÷(EER/3)が 0.25・0.75・1.5 を越えるごとに 満腹・ふつう・空腹・とても空腹 で、`hunger` の写しは 1・5・8・10 です。
- 食事の摂取は時間帯の比 × EER で、食後の消費を 0 に戻します。飲食系の店の購入は軽食か飲料として食後の消費を減らします(`poi_intake_kind`=cat `food`・subcat `convenience` は軽食、subcat `drink`・`vending` は飲料)。比は種類で違います。軽食は性と年齢の階級ごとの間食の比(`EnergyModel.snack_share_of`=国民健康・栄養調査の第 13 表の錨 `nhns_t13_meal_kcal` の `snack_of_four`)× EER、飲料だけが一律の比 0.03(`DRINK_SHARE`・expedient)× EER です(`resolve._energy_snack`)。飲料の subcat はコードの注に「実資産の W6 には 0 件=口だけ」とあり、本番の世界では 0.03 の道は通らないはずです(data は開いていない)。
- プロンプトの B5 に描くのは空腹以上だけです(`--hunger-words` 既定 `hungry`)。
- 段を跨ぐと呼び出しの候補になります(`change_detect`・C 群)。

舞台の外に居る体は自動で食べます(`OutOfAreaMeals`)。W17 の食事の行の開始にそのとき舞台の外なら食べ、行の無い時間帯は既定の時刻に食べます。既定の時刻は W17 の食事の行の開始の分布から体ごとに引きます。金と物は動きません。初期の空腹は前夜の夕食からの経過で決まります。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 店の食事 | 既定 | 語彙 v3 の語 |
| エネルギー収支 | 既定 | `--hunger-model` 既定 `energy`(`cli.CLI_DEFAULT_HUNGER_MODEL`)。ライブラリの `run_day` の既定は `v1` |
| 舞台の外の自動の食事 | 既定 | 切替口なし |
| 消費の式 BMR | 腕 | `--energy-rate bmr`(既定 `eer`) |
| 就寝中の既定の食事を起床の時刻へ | 腕 | `--meal-sleep-defer on`(既定 off) |
| 域内の家の食事の行を予定として実行 | 腕 | `--home-meal plan`(既定 off)。系 `home_meal` が立つ |
| B5 に満腹・ふつうも描く | 腕 | `--hunger-words all`(既定 `hungry`) |
| 飲食店の集合を広げる | 腕 | `--eatery place_food`(既定 `food`) |
| 古典の方策の食事の門 | 腕 | `--policy classical`(既定 mock)・`--meal-gate` 既定 `per_wake`。方策の本体は C 群 |
| 旧い空腹のモデル | 旧道 | `--hunger-model v1` |
| 域内の家で食べる | 無い | `absent.eat_home`(`--home-meal off` の既定で) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `_apply_eat`・`_complete_eat`・`_energy_meal`・`_energy_snack`・`energy_out_of_area_meal`・`energy_home_meal`・`advance_body`・`initialize_energy` |
| [src/shibuya/engine/energy.py](../../../../src/shibuya/engine/energy.py) | 値を決める層 `EnergyModel`・`OutOfAreaMeals`・`HomeMeals`・`EnergyLayer`・`MealStartDistribution` |
| [src/shibuya/engine/body/rules.py](../../../../src/shibuya/engine/body/rules.py) | 体の自然変動の値 `interoception`・`initial_energy_values` |
| [src/shibuya/engine/systems/body.py](../../../../src/shibuya/engine/systems/body.py) | 系 `body`・`home_meal`・`energy_after` |
| [src/shibuya/engine/classical.py](../../../../src/shibuya/engine/classical.py) | 古典の方策の食事の門と事前分布 |
| [src/shibuya/world/state.py](../../../../src/shibuya/world/state.py) | `eatery_mask`・`EATERY_MODES` |
| [src/shibuya/perception/renderer.py](../../../../src/shibuya/perception/renderer.py) | B5 の空腹の語・`HUNGER_WORDS_MODES` |

### 元の決定

D-118(索引に行なし・#57)・D-119(索引に行なし・#58)・`09-30/§4`・`09-30/Q34`・`09-30/Q35`・`09-30/Q31`・`09-30/Q48`・`09-30/§8-2`(食事の束は切替口で作り、既定は版上げで束ねる=#78 ④・#79)・`10-13b/§7`(既定の食事時刻=#117)・`09-24d/D-96`(飲食店の集合=#50)・`11-01/§10-3`(routing #80)・`10-25/§2-5`((ii) `--hunger-model v1` を消す・未着手)。

### 棚卸しで見つかった指紋

- V: A13(空腹の語は段 2 以上だけ描く)・A14(段 4/7/9 の跨ぎで呼び出し候補)・B1(受け入れの式は食事にも効く)
- K: M2(満席なら自動で列へ)・S7(「並ぶ」の委譲)
- D: S1(食事の所要時間 20 分は宣言だけ)・S15(空腹 v1 の −4)

### 既知の穴

- `absent.eat_home`。`--home-meal plan` の腕もほとんど効きません。5,000 体の域内の家の体 509 体のうち月曜の家の食事の行は 103 本で、欠食率は 83.1 → 82.3% です(#79。W17 の中身にかかる記録の値で、data を開いていないのでコードでは確かめていない)。
- 食事は棚を動かさないので、売上に対応する原価が立ちません(`_apply_eat` の docstring)。
- 棚の在庫が 0 の飲食店は、食事でも取り合いの決着で落選します。食事の資源も `space.poi` で、受け入れ数が `min(4, 在庫)` だからです(コードの読み・件数は未確認)。
- 量と時間帯を本人が選ぶ形はありません。摂取は時間帯の比で決まり、既定の時刻は窓(`MEAL_WINDOWS_MIN`)の中です。`10-03/§9-6` の方針はコードに入っていません。
- 既定の食事時刻はつなぎです(台帳 `BR-MEAL-DEFAULT-W17`・外す段 6-6)。
- #79 が直さずに残した点があります。同じ時間帯に 2 回食べることを防がない(mock 8・classical 14)・夕食の既定の時刻から日の終わりまで眠っている 387 体は夕食を失う・W17 の連続する行の 2.73% が重なる(全母集団 3,071,887 組のうち 83,801)。#117 と #118 の前の数値です。

### 文書とコードの差

- `09-30/Q31` は「満腹・ふつうも描くを既定に」と決めています。コードの既定は `hungry` で、`09-30/§8-2` の束ねる版上げがまだ来ていません。`09-30/Q34`・`Q35`・`Q48` も同じで、腕のままです。
- `_apply_eat` の docstring の効果は「空腹−`EAT_HUNGER_RELIEF`」と「売上+同額」です。既定の energy では `_energy_meal` が空腹を決め、売上は税抜きです。

## 4. 会話

### 何をしているか

答えが「会話」の体の相手を決め、招待し、話者が交替するセッションを進めて、エンジンが終わらせます。既定のランに言葉はありません。語彙 v3 に「ひと言」の欄が無く、発話の口も off なので、残るのはセッションと回数です(段 1 §7)。

流れは次のとおりです。

1. 相手を決めます(`commit.intents_from_responses`)。名指しが届くならその人、届かなければ同じ束の中で届く体のうち並びの鍵が最小の体です(`_talk_partners_reach`)。名指しの相手が届かず別のセルなら歩く意図にします(15 節)。
2. 行為を適用します(`resolve._apply_talk`)。相手が居ない BAD_TARGET・届かない PARTNER_GONE・相手が会話中か就寝中 PARTNER_BUSY です。通れば話しかけた体が CONVERSING になります。
3. 系 `conversation` が招待を扱います(`sys_conversation`)。相手も同じ刻みにこちらを名指ししていればその場で成立します。そうでなければ返事待ちに積み(`register_pending`)、相手は次の刻みに会話の番で呼ばれます。
4. 返事を解決します(`run._settle_pending_invites`)。「会話」で招待者宛てか名指しなし、かつ届くなら成立です。届かなければ不成立(`drop_pending`)で、ほかの答えは断りです。断りは組を 60 刻み記憶します。返事の期限は 3 刻みです。
5. セッションでは話者が交替で呼ばれ、1 呼び出しが 1 発話ブロックです。1 体 3 回まで、話題は 1 往復で 1 本減って 3 本です。
6. 終わりは 6 種です。全員が上限(`hard`)・話題が尽きる(`soft_topics`)・沈黙 5 刻み超(`soft_silence`)・退去・離脱(`left_cell`)・寿命 60 刻み(`timeout`)。閉じると CONVERSING の参加者だけを IDLE に戻します(`resolve.end_conversation`)。
7. 招待の間隔は、同じ組 60 刻み・同じ話し手 30 刻みです。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 招待・セッション・終わり | 既定 | `run_day` の `conversations` 既定 True。CLI に切替口なし |
| 終わりと招待側の戻し(M10)・届かない承諾(M16) | 既定 | `--defect-fixes-1103` 既定 on(`legacy` は旧道) |
| 3 人会話 | 腕 | `--conv-max-participants 3`(既定 2)。既定では `absent.third_joiner` |
| 応答率 0.8 の抽選 | 器 | 呼び手は全部 `answered=True`(`talk.py`・`contact/calls.py` の docstring)。台帳 `DOC-fix4-dead-accept-probability`・次の版上げで消す |
| 重要度上位の +2 呼 | 器 | 組み立ては `important` を渡さない(`build.py` の `ConversationManager(...)`)。台帳 `DOC-fix4-dead-important-extra-turns` |
| 相槌と締めの文 | 器 | `backchannel_for`・`closing_utterance` の呼び手が src に無い(grep) |
| 割り込みの要求・断るの拒否の記憶 | 器 | `request_interrupt`・`record_refusal` の呼び手が src に無い(grep) |
| 歩いて近づく段 | 器 | `walk_over_ticks` 既定 0 |
| 古典の方策の交際の相手 | 腕の中 | `--classical-social {acquaintance,near_first}`(既定 `acquaintance`)。`--policy classical` のときだけ効き、会話の相手の選び方を変える(`build.py` の `classical_policy.acq_fn`・`partner_fn`) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/conversation.py](../../../../src/shibuya/engine/conversation.py) | セッションの状態機械 `ConversationManager`・`Session`・定数 |
| [src/shibuya/engine/systems/talk.py](../../../../src/shibuya/engine/systems/talk.py) | 系 `relations_wake`・`conversation` |
| [src/shibuya/engine/systems/judge.py](../../../../src/shibuya/engine/systems/judge.py) | 系 `apply_responses`(返事の解決を呼ぶ)・`wake_sources`(`conv.wake_candidates`) |
| [src/shibuya/engine/systems/llm_io.py](../../../../src/shibuya/engine/systems/llm_io.py) | 会話の番の発話 `utter` |
| [src/shibuya/engine/run.py](../../../../src/shibuya/engine/run.py) | `_settle_pending_invites` |
| [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `_apply_talk`・`talk_within_reach`・`set_conversing`・`end_conversation`・`revert_conversation`・`join_conversation` |
| [src/shibuya/engine/commit.py](../../../../src/shibuya/engine/commit.py) | `talk_partners`・`_talk_partners_reach`・`pair_partners` |
| [src/shibuya/engine/defect_fixes_1103.py](../../../../src/shibuya/engine/defect_fixes_1103.py) | `--defect-fixes-1103` の切替口 |

### 元の決定

行動契約書 §3(docstring の正典・索引に行なし)・`10-03/§4`・`10-03/§5-1`・`10-03/§7-6`・`11-03/§3`・`11-03/M10`・`11-03/M16`(#138)・`11-01/§10-3`(routing #53)・`11-05/§3-2`(死んだ道を消す・未着手)。C10 の 3 人会話は #65。

### 棚卸しで見つかった指紋

- V: B6(1 刻み 1 発話・3 呼・3 本・5 刻み・60 刻み・影響 大)・S34(返事待ち 3 刻み)・S35(返事待ちは先着 1 件)・S36(セル離脱の判定)・A10(近くの人 3/2/1 人)・A51(近くの人の同点)
- K: B8(名指しが届かなければ束の先頭・影響 大)・M10(会話の後の活動・割れる)・M14(招待の間隔 60/60/30)・M15(上限 2)・M29(相手が会話中か就寝中なら失敗)・S32(話す番)・S33(相槌と締め)・F1(番で別の行為を選んでもセッションに残る)・F3(招待の帳尻の 1 件)
- D: S37(応答率 0.8)・A30(招待の起床理由の固定文)・A65(ひと言 20 字ほか)
- E: M16(物理・届かなければ成立しない)・S4(物理・成立 2 m と離脱 3 m)

### 既知の穴

- 既定のランに言葉が無く、終わった後に誰も覚えていません(段 1 §7)。
- F1 は `talk.py` の docstring にあります。`conv.step` に `in_conversation` を渡していません。
- 招待の帳尻は 招待 2,218=成立 155+断り 2,029+期限切れ 1+未決 0+不成立 32+1 で、最後の 1 は F3 です(fix4 §1-1)。
- 既定の mock は 12 語から一様に引くので、承諾は計算で約 1/12 です(段 1 §7)。
- `D_TALK_METERS`(1 m)はどこからも距離として読まれません。成立の距離は `proximity.D_DEFAULT` と `resolve.TALK_OPEN_METERS` の 2 本が別々に持ちます(`conversation.py` の注)。
- 実 LLM の道で、返事待ちの体にもう 1 本送る穴があります(台帳 `DOC-fleet-resend-while-waiting`・`10-25/§2-7`)。

### 文書とコードの差

- 仕分けの表の S36(「2 人で一緒に歩くと終わる」)は `_left_cell` の話です。既定の近接 distance では `near_fn` が先に効き(`step` の分岐)、`_left_cell` は `--proximity cell` のときだけ通ります。
- 仕分けの表の S33 は相槌と締めの文を K の行にしていますが、コードでは呼び手が無く、死んだ道です。`_close` の「締めの 1 発話」は `s.blocks` を 1 足すだけで文を作りません。
- `gate`・`register_pending` の引数名 `same_cell` は、既定の近接 distance では「届く」の意味です(呼び手が `talk_within_reach` の結果を渡します)。

## 5. 近接の判定(足した)

### 何をしているか

会話が届くか、近くの人として見えるかを実距離で決めます。`ProximityRule.reach` は「舞台の中・同じ層・距離 ≤ d」か「同じ B5 の単位(同じ店に在席し、その店のセルの中)」で真です。離脱は d+1 m です(`stay`)。使う所は、会話の開始・返事待ち・3 人会話・離脱・招待の相手の候補・偶然の出会い・知人に気づく起床・同席・B5 の近接行です。B5 の近接行の半径は 10.3 m、知人に気づく確率は 2 点(R-62)を通るロジスティックで、100 m で打ち切ります。索引は 2.5 m の格子で、刻みごとに作って捨てます。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 実距離の判定 | 既定 | `--proximity` 既定 `distance`(`proximity.DEFAULT_MODE`) |
| 距離 d | 感度の値 | `--proximity-d {1.0,2.0,2.5}` 既定 2.0 |
| 同じセルの判定 | 旧道 | `--proximity cell` |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/proximity.py](../../../../src/shibuya/engine/proximity.py) | `ProximityRule`・`ProximityLayer`・`batch_partners`・`marks_for` |
| [src/shibuya/engine/spatial_index.py](../../../../src/shibuya/engine/spatial_index.py) | 近傍の索引 |

### 元の決定

`10-03/§4`・`10-03/§4-1`・`10-03/§4-2`・#97・#101(V2)。

### 棚卸しで見つかった指紋

E: S4(物理)・M16(物理)。V: A10・A51。`proximity.py` の本体は棚卸し B の「読んでいない先」です(棚卸し B §5)。

### 既知の穴

- 位置の出どころは暫定です。今の既定の nav1 では、建物の中の体は入口の点に居て、仮想の距離を測れません(`marks_for`)。nav1 が立つのは、本番の世界の置き場に `nav1_*` の資産があるときだけです。合成の世界と、資産も `build_hash` も無い置き場は legacy で回ります(`build.py`・A 群 §3 の状態の「条件」)。`--geometry` の既定は `node` です。
- 2 m は決め打ちで、音の伝わり方の計算は空間の段 3 の仕事です(`proximity.py` の expedient)。

### 文書とコードの差

- `proximity.py` の docstring の「暫定」の段は「位置の出どころは node の座標」と書いています。既定の nav1 のランで manifest に出る印は `marks_for("nav1")` の「入口の点」です。
- `ProximityLayer` の docstring は「既定の腕 cell では作らない」と書いていました。既定は distance で、組み立てが層を作ります(cell は旧道)。11-09 に docstring を直しました。

## 6. 発話の口(足した)

### 何をしているか

会話の番の答えの「ひと言」を出来事の記録に 1 回書き、相手の次の入力の B6 に載せ、口コミの抽出へ渡します(`SpeechPort.say`)。on のランでは、会話の番の呼び出しだけ B6 の末尾に欄の指示が足されます。届いた発話は素性の札と命令文の除去つきで描きます。届く範囲は当面セッションの参加者です。ひと言の上限は 20 字です(`contract.COMMENT_MAX_CHARS`)。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 発話の口 | 腕 | `--speech-port on`(既定 off・環境変数 `SHIBUYA_SPEECH_PORT`)。on は設定の指紋に入る |
| ひと言(既定のラン) | 無い | `absent.utterance` |
| 音声と表情の欄 `modality` | 器 | 値は空 |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/speech/port.py](../../../../src/shibuya/engine/speech/port.py) | `Utterance`・`SpeechPort`・`mora_count` |
| [src/shibuya/engine/speech/layer.py](../../../../src/shibuya/engine/speech/layer.py) | 切替口・`make_port`・`speak_turn` |
| [src/shibuya/llm/mock.py](../../../../src/shibuya/llm/mock.py) | mock の決まった文 `MOCK_UTTERANCE`(「こんにちは」) |
| [src/shibuya/perception/renderer.py](../../../../src/shibuya/perception/renderer.py) | `SPEECH_HEARD_LINE`・`SPEECH_IMPERATIVE_PATTERNS`・`heard_fn` |

### 元の決定

`09-30/Q57`・`10-13b/§1-5`・`10-12/TM3`・`10-12/MR11`・`11-01/§10-3`(routing #49)・#96。

### 棚卸しで見つかった指紋

D: A65(ひと言 20 字)。K: A42(要旨の源)。V: A45(個体の枠の超過で発話の行を落とす)。

### 既知の穴

- 既定にするのは GPU の後の版上げです(`speech/layer.py`)。
- 届く範囲はつなぎです(台帳 `DOC-s8b-reach-session`・`DOC-s8b-reach-hearing`・外す段 5-3)。

### 文書とコードの差

- `09-30/Q57` は「40 字程度」と書いています。コードと欄の指示は 20 字です(`SPEECH_FIELD_LINE`)。要旨の 40 字(`memory.GIST_CHARS`)は別のものです。
- 段 1 §0-1 と §4-4 の「mock はプロンプトを読まない」には、腕の例外が 1 つあります。mock は `SPEECH_FIELD_LINE` がプロンプトにあるかを見ます(`mock.py`)。

## 7. 会話の時計(足した)

### 何をしているか

発言の長さをモーラ数 × 人ごとの話す速さで計算し、会話の中の時計を数えます。世界の状態は書きません。会話の番は今も刻みに 1 回で、これは計器です(`speech_clock.py`・台帳 `DOC-tm234-talk-clock-meter-only`)。

### 状態

腕です。`--talk-clock mora`(既定 `table`・環境変数 `SHIBUYA_TALK_CLOCK`)。`table` は持ち主を作りません。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/speech_clock.py](../../../../src/shibuya/engine/speech_clock.py) | `TalkClock`・`make`・`ChatTiming`(値は空欄) |

### 元の決定

`10-12/TM3`・`10-12/TM6`・`10-12/TM7`・#114。

### 棚卸しで見つかった指紋

行はありません。B6(V)の 1 刻み 1 発話が、この腕で変わらない部分です。

### 既知の穴

会話の番を窓の中で時刻順に回すのは T2 の版上げです(#114 の残り)。5,000 体 1 日の会話の時計は平均 3.0 秒で、今の表は 246 秒でした(#114)。

## 8. 記憶

### 何をしているか

腕のランで、体ごとに出来事を覚え、呼ばれたときに思い出した行を B5 に載せます。既定では系 `memory` は立ちますが、層が無いので何もしません。

- 記憶の表(`engine/memory.py`)は体ごとに 128 行です。書くのは行動の成否・会話・気づき・強い看板(初見)です。同じ鍵の行は `mem_n` を増やして統合します。重要度は固定表(失敗 3・会話 2・成功 1・気づき 1・看板 1・初回 +1・上限 4)です。
- 強さは A=ln(n/(1−d))−d·ln(L+1)(d=0.5・L は分)、score=A+0.5×重要度です。満杯なら score 最小の行を落とします。
- 想起(`recall`)は手がかり(セル・相手・対象・直前の結果)の一致と A ≥ τ(−2.0)で絞り、会話は 3 件、それ以外は 2 件です。足りなければ A ≥ τ の残りで補います。
- 会話の要旨は体あたり 16 件・40 字です。源はひと言で、空なら理由の先頭 40 字です。

下の腕はどれも記憶の器のランで効きます。

- 記憶の器 M0: 出来事の記録への目印・強さ・注釈・出どころ・録画の行を持ち、想起を器から引きます。結果は変えません。
- M1 の強さ: ACT-R の折衷形(秒・直近 3 回は本当の時刻)・人ごとの忘れる速さに約 15% のばらつき・τ は仮の −3.738(`tau_from_m0(-2.0)`)。
- 意味の手がかり: `cos` の一致(0.5 以上)で引きます。
- 人も記憶の一つ: 11 節です。
- 粒度: 同じ行は日に 1 行だけ記録へ書きます。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 記憶の表と想起 | 腕 | `--memory on`(既定 off)・`--memory-n` 既定 128・`--memory-tau` 既定 −2.0 |
| 記憶の器 M0 | 腕 | `--memory-store events`(既定 `mem`・環境変数 `SHIBUYA_MEMORY_STORE`)。`--memory on` のランでだけ器を作る |
| M1 の強さ | 腕 | `--memory-model m1`(既定 `m0`・`SHIBUYA_MEMORY_MODEL`) |
| 意味の手がかり | 腕 | `--memory-cue embed`(既定 `id`・`SHIBUYA_MEMORY_CUE`)・`--memory-embed-model` 既定 `ruri-v3-30m` |
| 粒度 | 腕 | `--memory-grain day`(既定 `each`・`SHIBUYA_MEMORY_GRAIN`) |
| 印象の履歴と書き直し | 器 | `memory_impression.py`。呼び手が src に無い(grep) |
| 浅い痕跡 | 器 | `memory_trace.py`。呼び手が src に無い(grep)。`Percept.heard_referents` は空の欄 |
| 注意の口 `note_attended` | 器 | 呼び手が src に無い(grep) |
| 1 日の振り返り | 無い | `absent.reflect_day` |
| 予想と違って直す | 無い | `absent.plan_fix_surprise` |

組み立ての検査は次のとおりです。器の無いランで model・cue・people・grain を既定から変えると止まります。people=memory は model=m1 が前提です(`memory_m1.check_arms`)。`--store-memory on` と `--relations on` は `--memory on` が前提です(`build.py`)。

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/memory.py](../../../../src/shibuya/engine/memory.py) | `MemoryLayer`(記録 `after_tick`・想起 `recall`・要旨 `note_utterance`) |
| [src/shibuya/engine/memory_store.py](../../../../src/shibuya/engine/memory_store.py) | 記憶の器 `MemoryStore`・`MemoryView` |
| [src/shibuya/engine/memory_m1.py](../../../../src/shibuya/engine/memory_m1.py) | M1 の式・人ごとの倍率・腕の切替口 `check_arms` |
| [src/shibuya/engine/memory_embed.py](../../../../src/shibuya/engine/memory_embed.py) | 埋め込みの口・`CueState`・`RURI_PINS` |
| [src/shibuya/engine/memory_impression.py](../../../../src/shibuya/engine/memory_impression.py) | 印象の器 `ImpressionBook` |
| [src/shibuya/engine/memory_trace.py](../../../../src/shibuya/engine/memory_trace.py) | 浅い痕跡 `shallow_trace`・`played_along_share` |
| [src/shibuya/engine/systems/remember.py](../../../../src/shibuya/engine/systems/remember.py) | 系 `memory`・`familiarity` |
| [src/shibuya/engine/events/body.py](../../../../src/shibuya/engine/events/body.py) | 体の出来事を記録に書く口(器のランだけ) |
| [src/shibuya/agents/state.py](../../../../src/shibuya/agents/state.py) | 列 `mem_*`(`memory_columns` のランだけ確保) |

### 元の決定

`09-24d/§3`・`09-24d/M1`〜`M6`・`09-24d/M16`(記憶 第 1 段=#60・#61)・`09-30/§3-2`・`10-12/§4-6`(`10-12/MR-0`・`MR1`・`MR2`・`MR3`・`MR4`・`MR6`・`MR8`・`MR10`・`MR11`・`MR12`・`MR13`・`MR16`)・`10-12p/§6-2`(段 M0〜M5)・`11-01/§10-3`(routing #94・#96)。器は #91・#100、腕は #110。`11-05/§2` の「M1 を既定にする方向」は時期が未定で、コードの既定は `m0` です。

### 棚卸しで見つかった指紋

K: A42(要旨の源と口コミの聞き手)。V: A45(個体の枠 300 tok で意図 → 記憶 → 発話 → 連絡の順に落とす)。`memory*.py` は表の path の欄に出てきません。

### 既知の穴

- 語彙 v3 にひと言が無いので、要旨は理由の先頭 40 字です(`09-30/Q57` の暫定)。
- Ruri の重みは未取得です。転送先のドメインが許可の一覧の外だからです(`memory_embed.py` の docstring)。`ngram-test` は意味の手がかりではなく、試験用です。
- 人も記憶の腕の 39 万体の見積りは出来事 6.88 GiB・人 6.88 GiB・店 2.14 GiB で、予算の外です。粒度 day でも 39 万体 7 日 2.65 GiB で、256 MB の宣言を超えます(#110)。
- 判定は複数日と実 LLM の後です。mock は描画を読まないので、記憶 on でも行動は変わりません(#61)。

### 文書とコードの差

- `memory.py` の docstring は τ の感度を −1.5/−2.5、定数の注は −0.5/−2.0/−2.5 と書いています。
- `memory_store.py` の docstring の「M0 は今の式」は腕 m0 の話で、腕 m1 では器の子の持ち主 `M1State` が強さを決めます(同じ docstring の〔第 6 期 6-5〕の段)。

## 9. 店の評価の記憶と口コミ(足した)

### 何をしているか

腕のランで、体ごとに店の行を最大 32 行持ちます。向きと確からしさを精度の加重で足します(σ 自分 1・伝聞 2・看板 4・ネット 2)。書くのは自分の訪問(結果コードから向き)・看板の初見(向き 0)・伝聞です。読むのは B5 の想起の店の項と、選び手 classical のときの想起優先です(2 節)。

口コミは、会話の発話の欄から店名と評価語を辞書で拾い、宛先の店の行へ伝聞として書きます(`WomExtractor`)。呼数は 0 です。今の語彙 v3 はひと言の欄が無いので、発話の口が off のランは抽出が 0 件です。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 店の評価の行 | 腕 | `--store-memory on`(既定 off)・`--store-memory-n` 既定 32・`--store-decay` 既定 `actr`・`--store-sigma` 既定は表の値 |
| 看板の初見から書く | 腕の中 | `--store-signage` 既定 on |
| 口コミの転写 | 腕の中 | `--store-wom` 既定 on・`--wom-source` 既定 `utterance`(旧 `reason-target`) |
| B5 の想起の入口 | 腕の中 | `--store-recall-scope` 既定 `all` |
| 上限を外す道 | 腕 | `--memory-people memory` で `memory_shops.UncappedStoreMemory`(幅 32 から 256 まで) |
| ネットの出どころ | 器 | ビット 8 と σ の枠だけ |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/store_memory.py](../../../../src/shibuya/engine/store_memory.py) | `StoreMemory`・`STORE_SIGMA`・列の口 |
| [src/shibuya/engine/store_choice.py](../../../../src/shibuya/engine/store_choice.py) | 想起優先と決め手 |
| [src/shibuya/engine/wom.py](../../../../src/shibuya/engine/wom.py) | 店名と評価語の抽出 `WomExtractor`・`hear` |
| [src/shibuya/engine/memory_shops.py](../../../../src/shibuya/engine/memory_shops.py) | 上限なしの腕の店の行 `ShopTable`・`UncappedStoreMemory` |
| [src/shibuya/engine/systems/llm_io.py](../../../../src/shibuya/engine/systems/llm_io.py) | `utter` が抽出と転写を呼ぶ |

### 元の決定

D-120(索引に行なし・#62・#63・#64)・`09-30/Q57`(#78 ①=内心の漏れの修正)・`10-12/§4-6`(固定の上限をなくす腕=#110)。

### 棚卸しで見つかった指紋

K: A37(〔腕〕届く店の式)・A42(口コミの聞き手)。V: A54(抽選の鍵)・A69。

### 既知の穴

- 口コミは今 0 件で、off/on の差も 0 です(#64・#78)。
- 非宛先と傍受の重みは未実装で、宛先だけです(`wom.py`)。別名表 v0 は空です。
- 初回率と店頭の割合は 1 日のランでは照合量として読めません(#64)。

### 文書とコードの差

- `store_memory.py` の docstring の「本段では誰も読まない」は段 7a の話で、今は `store_choice.py` と `memory.py` が読みます。
- `wom.py` の docstring は抽出の場所を `engine.run` の `_utter` と書いています。実体は `engine/systems/llm_io.py` の `utter` です。

## 10. 親しみ

### 何をしているか

腕のランで、体ごとに 64 行の表に、店・場所への接触を数えます(訪問数と露出数)。訪問は購入と食事の成立、露出は描画で看板が載った回とセルに入った回です。人と道は書きません。A=ln(n/(1−d))−d·ln(L+1) の読み口があります。読むのは選び手 classical の習慣の項だけで、`fam_visits` を読みます(`poi_target._rich_fields`)。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 親しみの表 | 腕 | `--familiarity on`(既定 off)・`--familiarity-k` 既定 64。系 `familiarity` が立つ |
| 習慣の入力 | 腕 | `--chooser classical` と一緒のときだけ読まれる |
| 露出数 `fam_exposures` | 器 | 書く口と計器だけ。判断の読み手は src に無い(grep) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/familiarity.py](../../../../src/shibuya/engine/familiarity.py) | `FamiliarityLayer`・`place_thing`・`activation_approx` |
| [src/shibuya/engine/systems/remember.py](../../../../src/shibuya/engine/systems/remember.py) | 系 `familiarity` |
| [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | 書き手 `write_familiarity` |
| [src/shibuya/engine/poi_target.py](../../../../src/shibuya/engine/poi_target.py) | 読み手 `_rich_fields` |

### 元の決定

`09-24d/M13`・`09-30/M17`・`09-30/Q53`・#56。

### 棚卸しで見つかった指紋

K: A38(〔腕〕習慣 0.5)。`familiarity.py` は表の path の欄に出てきません。

### 既知の穴

- `09-30/M17`(親しみを店の候補へ入れる)はコードにありません。`familiarity.py` と `store_choice.py` の docstring が「含めない」と書いています。
- A の近似は最近に偏った接触で低めに出ます(`familiarity.py` の docstring)。

### 文書とコードの差

- `familiarity.py` の docstring は「誰も読まない」と書いています。`poi_target.py` が `fam_visits` を読みます(#58 で結線)。

## 11. 関係

### 何をしているか

腕のランで、体ごとに 15 辺の表を持ちます。種別は 世帯・職場・学校・常連・知人です。初期の辺は W16 と W17 の共在から機械的に作ります(`initial_edges`)。ラン中は記憶の会話と手伝いの行から辺を更新します。符号は結果コードから決め、LLM は書きません。A ≥ τ(−2.322)の辺だけが読み口に出ます。

`--relations on` で動くものは次のとおりです。

- B5 の「(知人)」の印と、近接行の人数の外への掲載です。
- 名指しの無い会話の相手を、辺の重み(内側 5 人 40%・次の 10 人 20%・残り 40%)で引きます(`--rel-invite`)。
- 知人が同じセルに現れた刻みの呼び出し候補(同じ相手 60 分)を作ります(`--rel-acq-wake`・系 `relations_wake`)。
- 同席を 1 日 1 本数える腕があります(`--rel-copresent`)。

人も記憶の一つの腕は、関係の表 `rel_*` を読み書きせず、記憶の器の人の行から読み口を作ります(`PeopleRelationLayer`)。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 関係辺 | 腕 | `--relations on`(既定 off・`--memory on` が前提)・`--rel-k` 既定 15・`--rel-tau` 既定 −2.322・`--rel-d` 既定 0.5・`--rel-init-density` 既定 1.0・`--rel-tenure-weeks` 既定 13 |
| 会話の相手の重み | 腕の中 | `--rel-invite` 既定 on |
| 知人が現れる呼び出し | 腕の中 | `--rel-acq-wake` 既定 on |
| 同席 | 腕の中 | `--rel-copresent` 既定 off |
| 人も記憶の一つ | 腕 | `--memory-people memory`(既定 `table`)。`--memory-store events` と `--memory-model m1` が前提 |
| 連絡先の印 `contact_flags` | 器 | 既定の読み手なし。`--contact c1` のランで読まれる(13 節) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/relations.py](../../../../src/shibuya/engine/relations.py) | `RelationLayer`・`initial_edges`・`choose_talk_partners`・`acquaintance_candidates`・`copresent_step` |
| [src/shibuya/engine/relations_people.py](../../../../src/shibuya/engine/relations_people.py) | `PeopleRelationLayer` |
| [src/shibuya/engine/systems/talk.py](../../../../src/shibuya/engine/systems/talk.py) | 系 `relations_wake` |
| [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | 書き手 `write_relations` |
| [src/shibuya/engine/memory.py](../../../../src/shibuya/engine/memory.py) | `enable_relations`・人の行に触れる `_touch_people` |

### 元の決定

`09-24d/§3`(D-93)・`09-24d/M12`・`09-30/Q91`・`09-30/Q111` → `10-03/§5-4` → `10-12/§4-6`(関係の表をやめる方向・腕まで)・`09-30/Q42`(古典の交際の相手=#78 ③)・#65・#66・#67・#78 ②・#110。

### 棚卸しで見つかった指紋

V: S17(辺の符号 ±127)・A10(知人は人数の外)。K: B8・M14(相手を選ぶ道)。`relations*.py` は表の path の欄に出てきません。

### 既知の穴

- 8c(語彙 v3.1)・8d(約束)・ウォームアップの強制ペアは含めません(`relations.py`)。約束はカレンダー 2 が別に持ちます。
- 初期網は来街者が全員空でした(全母集団 390,067 体のとき 96,006 体・#65。今の母集団 345,858 体での値は未確認)。
- 最初の関係のつなぎは台帳 `DOC-mr65-people-initial` です。人も記憶の腕では同席と知人出現の起床を作りません(`relations_people.py`)。
- 人も記憶の腕は 39 万体の予算の外です(#110)。

### 文書とコードの差

- #65 の「on でも挙動不変」は段 8a の値です。今の既定は `--rel-invite on`・`--rel-acq-wake on` なので、`--relations on` は呼数を変えます(#66)。
- `09-30/Q111` の「容量 50」は `10-12/§4-6` で上書きされ、コードの既定は 15 のままです。50 は `--rel-k` の感度の値です。

## 12. カレンダーと予定

### 何をしているか

6 つの部分があります。

1. 暦の口(`SimCalendar`): 日付・曜日・祝日・季節・営業日を 1 つの口で引きます。開始日の既定は 2026-07-13 です。給料日は経済の層が 25 日の暦を作って使います(`economy_stage2.py`)。
2. 日課表 W17: 初期の予定です。コードが実行するのは舞台への出入り・就寝・起床と舞台の外の食事だけで、勤務の行を実行する処理はありません(段 1 §0-1)。実行部 `presence.py` は A 群の担当です。
3. 暦 1a の影(`--calendar-shadow 1a`): 勤務と授業の表 W20 を日の頭に引いて、計器だけを出します。挙動は変えません。
4. カレンダー 1b(`--calendar 1b`): W20 の時刻つきの勤務の約束を持つ体の、出発と帰宅を本人の判断へ渡します。本人の予定の器・置き場所ごとの思い出し方(アプリ・アラーム・手帳・頭の中)・時間の見積りを持ちます。エンジンは逆算して起こさず、間に合う便を選ばず、時刻で退出させません(検査 3 つ)。判断は仮のモデルです(`CommuteMockPort`・`CommuteClassicalPort`)。就寝・起床・来街者の来訪は W17 のままです。
5. カレンダー 2(`--calendar-2 arm`): 会話の番とメッセージから約束が生まれます。各自が自分の行を持ち、変えられるのは自分の行だけです(`PromiseBook`)。頭の中の予定は記憶 M1 の式で思い出せたときだけ見えます。出発は本人が考えた刻みか本人が選んだ知らせの時刻です。範囲外の過ごし方も本人の計画に書けます。
6. カレンダー 3(`--calendar-3 arm`): シフトを組む人が金曜の頭以降の最初の機会に翌週 7 日の枠を選び、連絡の口で知らせ、働く人が勤務の行を書きます。休みの申し出と遅れの連絡もあります。祝日は全員が知る常識の口です。

判断はどれも候補の口の形で、仮のモデルは候補から一様に選びます。判断モデルの中身は無く、カレンダー 1b・2・3 の口は `--llm fleet` でも仮のモデルに固定です(冒頭の「考える担い手」)。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 暦の口 | 既定 | 切替口なし(`--start-date` ほかは `add_calendar_args`) |
| 日課表 W17 | 既定 | `--calendar` 既定 `w17`・`--derive-rule` 既定 `v2`(A 群) |
| 暦 1a の影 | 腕 | `--calendar-shadow 1a`(既定 `w17`・`SHIBUYA_CALENDAR_SHADOW`) |
| カレンダー 1b | 腕 | `--calendar 1b`(既定 `w17`・`SHIBUYA_CALENDAR`)。母集団・実行部・W20 の表が無いと止まる。W20 の表は世界の置き場の `w20_calendar_1a.parquet` か、環境変数 `SHIBUYA_CALENDAR_W20` で渡す(`calendar_shadow.resolve_path`) |
| カレンダー 2 | 腕 | `--calendar-2 arm`(既定 off・`SHIBUYA_CALENDAR_2`) |
| カレンダー 3 | 腕 | `--calendar-3 arm`(既定 off・`SHIBUYA_CALENDAR_3`)。`--contact c1` と `--calendar-2 arm` が無いと止まる |
| 試験用の印 | 腕の中 | `SHIBUYA_CALENDAR_3_TRIAL` 既定 off |
| 店の休業日の口 `StoreRules` | 器 | 枠だけ(`calendar3/knowledge.py`) |
| 学校の長期休みの表 | 器 | 渡す形だけで中身は空(`calendar.py`) |
| 予定を考え直す | 無い | `absent.replan`(1b に plan・continue・deliberate があるだけ) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/calendar.py](../../../../src/shibuya/engine/calendar.py) | 暦の口 `SimCalendar`・祝日の表・開始日の検査 |
| [src/shibuya/agents/weekly.py](../../../../src/shibuya/agents/weekly.py) | W17 の読み口 |
| [src/shibuya/engine/calendar_shadow.py](../../../../src/shibuya/engine/calendar_shadow.py) | 1a の影・W20 の読み口 `load_table` |
| [src/shibuya/engine/calendar_self.py](../../../../src/shibuya/engine/calendar_self.py) | 1b の層 `CalendarSelf`・見積り・実感・検査 |
| [src/shibuya/engine/calendar2/book.py](../../../../src/shibuya/engine/calendar2/book.py) | 本人の予定の器 `PromiseBook` |
| [src/shibuya/engine/calendar2/layer.py](../../../../src/shibuya/engine/calendar2/layer.py) | 持ち主 `Calendar2Layer`・系 `calendar_2` |
| [src/shibuya/engine/calendar2/port.py](../../../../src/shibuya/engine/calendar2/port.py) | 候補と仮のモデル `Calendar2Port` |
| [src/shibuya/engine/calendar2/recall.py](../../../../src/shibuya/engine/calendar2/recall.py) | 頭の中の予定の思い出し `HeadRecall` |
| [src/shibuya/engine/calendar2/arm.py](../../../../src/shibuya/engine/calendar2/arm.py) | 切替口 |
| [src/shibuya/engine/calendar3/layer.py](../../../../src/shibuya/engine/calendar3/layer.py) | 持ち主 `Calendar3Layer`・系 `calendar_3` |
| [src/shibuya/engine/calendar3/roster.py](../../../../src/shibuya/engine/calendar3/roster.py) | 雇い主の口 `Roster`(つなぎ) |
| [src/shibuya/engine/calendar3/port.py](../../../../src/shibuya/engine/calendar3/port.py) | 候補と仮のモデル `Calendar3Port` |
| [src/shibuya/engine/calendar3/knowledge.py](../../../../src/shibuya/engine/calendar3/knowledge.py) | 暦の常識の口 `CommonCalendar`・`StoreRules` |
| [src/shibuya/engine/calendar3/arm.py](../../../../src/shibuya/engine/calendar3/arm.py) | 切替口と試験用の印 |

### 元の決定

`10-03/§3-1`(暦の口)・`10-03/§7-2`・`10-12/§4-1`(CA1 は索引に行なし)・`10-12/CA2`〜`CA11`・`10-12/AT1`〜`AT3`・`10-12/K9`・`10-12p/§6-6`・`10-12p/§2-1`(GPU の前に腕で)・`11-01/§10-3`(routing #64)。実装は #80・#88(暦)・#106(1a)・#112(1b)・#119(2)・#121(3)。

### 棚卸しで見つかった指紋

- 日課の実行に関わる行は K: M26(計画の切れ目で寝ている体を起こす)・S19(計画の就寝で会話中ほかは寝かせない)・F4(本人の予定とカレンダー 2 の歩き出しで列の印が消えない)、V: A73(活動の満了を計画の級にする)です。
- 暦 1a・1b・2・3 のファイルは表の path の欄に出てきません(F4 が `calendar2/layer.py` を挙げるだけです)。

### 既知の穴

- `absent.replan`。
- W17 v2 は月曜の行しか無く、火〜金も月曜の予定を使います(`10-12/K9`・台帳 `BR-K9-MONDAY`。data の中身にかかるので、台帳の文の値で、data では確かめていない)。
- カレンダー 2 は C1 と束ねると、5,000 体 1 日で約束の行 37,774・判断 37 万回/日・出来事の記録 約 26 MB/日です。既定にしません(#119・台帳 `DOC-ca2-not-default`)。
- カレンダー 2 の初めの予定は空で始めます(台帳 `DOC-ca2-initial-empty`)。
- カレンダー 1b の残りは、既定化(実 LLM の後)・アラームを System 1 へ・驚き駆動・通学です(#112)。mock の 1b では遅刻 697(0.257)で、82% は mock の行為の抽選で歩きが途切れたものです(#112)。
- カレンダー 3 のシフトを組む人の選び方と枠はつなぎです(台帳 `DOC-ca3-scheduler-pick`・`DOC-ca3-frame-form`)。
- カレンダー 1b・2・3 の判断の口は、コードで仮のモデルに固定されています(`calendar_self.py` の `CommuteMockPort`=古典の方策のランだけ `CommuteClassicalPort`・`calendar2/layer.py` の `Calendar2Port`・`calendar3/layer.py` の `Calendar3Port`)。実の LLM で回すときも、この判断は艦隊へ行きません。

### 文書とコードの差

- `calendar.py` の docstring は給料日を「今は誰も読まない」「既定は給料日なし」と書いています。既定の経済の段階 2 は `dataclasses.replace(calendar, payday_day_of_month=...)` で 25 日の暦を別に作ります(`economy_stage2.py`)。
- `calendar2/book.py` の docstring は行の種類を 5 つと書いています。`KINDS` は `勤務` を足して 6 つです。
- `cli.py` の `add_calendar_args(ap)` の注は `--calendar-weekday` を挙げています。この切替口は第330 で消えました(`calendar.py` の docstring・`run.add_calendar_args` に定義なし)。
- 索引の見出しは引き方の例に `10-12/CA1` を挙げていますが、索引の表に `CA1` の行はありません。原文は `10-12/§4-1` の「約束(勤務と授業)の作り方(CA1)」です。

## 13. 連絡

### 何をしているか

腕のランで、スマホの連絡を体の行動として動かします。届くのはエンジン、読む・返す・かける・出るは本人の判断です。

- 道具の状態(電源・電池・マナーモード・置き場・イヤホン)から通知の刺激を計算します。
- 目の向きと関心の的を状態に持ちます。画面を見ている間は、周りは周辺視 2.0 m の人数だけです。
- メッセージ・グループ・電話(`CallManager`=会話の器の子)・チャットの状態(`ChatBook`)があります。
- C2 として、充電は本人の判断(電池の知らせ 20%・10%・満充電)・連絡先の交換・グループを作る・ビデオ通話・既読の印があります。
- 習慣は下の腕で、舞台の外に居る体だけです(閾値 5・ときどき 0.1)。

判断は仮のモデル(`ContactPort`)が候補から一様に選び、文は定型です(`MockTextPort`)。どちらも `contact/layer.py` で固定で、`--llm fleet` でも艦隊へ行きません。主の判断が先で、連絡の判断は次の刻みへ回します(`ARBITRATION`)。

既定のランは道具の台帳(1-7 C0)を作りますが、結果に効きません。台帳の行は看板・掲示・電話・連絡先・グループ・乗換案内・地図・時計・天気予報の 9 行です。c1 のランはメッセージ・ビデオ通話・充電器・店の番号を調べる・郵便・置き手紙の 6 行を足します。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| C1・C2 の連絡 | 腕 | `--contact c1`(既定 off・`SHIBUYA_CONTACT`)。系 `contact` が立つ |
| 割り込めなかった出来事の載せ方 | 腕の中 | `SHIBUYA_CONTACT_UNNOTICED` 既定 `i` |
| 送る文 | 腕の中 | `SHIBUYA_CONTACT_SEND` 既定 `b` |
| 連絡の習慣 | 腕の中 | `SHIBUYA_CONTACT_HABIT` 既定 off |
| 道具の台帳・グループの一覧 | 器 | `tools.record.build_fixture` が既定でも作る。manifest の `tools` に出るだけ |
| 看板を読んだ出来事 | 腕 | `SHIBUYA_TOOL_EVENTS` 既定 off |
| 店の番号の表 | 器 | `PhoneTable()` は空(`build_fixture`)。台帳 `BR-PHONE-TABLE-BLANK`(外す段 7) |
| 道具を使う行為の語 | 器 | `TOOL_ACTION_WORDS` は空 |
| 郵便・置き手紙 | 器 | 台帳の行だけ(`contact/tools.py`) |
| 体の反射で顔を上げる | 器 | `body/system1.py` の値は空 |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/contact/layer.py](../../../../src/shibuya/engine/contact/layer.py) | 持ち主 `ContactLayer`・系 `contact`・`workplace_send`・監査 |
| [src/shibuya/engine/contact/arm.py](../../../../src/shibuya/engine/contact/arm.py) | 切替口と下の腕 |
| [src/shibuya/engine/contact/device.py](../../../../src/shibuya/engine/contact/device.py) | 道具の状態と刺激 `Devices` |
| [src/shibuya/engine/contact/attention.py](../../../../src/shibuya/engine/contact/attention.py) | 目と心の向き `Attention` |
| [src/shibuya/engine/contact/deliver.py](../../../../src/shibuya/engine/contact/deliver.py) | 届く `Mailbox` |
| [src/shibuya/engine/contact/chat_state.py](../../../../src/shibuya/engine/contact/chat_state.py) | チャットの状態 `ChatBook` |
| [src/shibuya/engine/contact/calls.py](../../../../src/shibuya/engine/contact/calls.py) | 電話 `CallManager`・`CallSpeechPort` |
| [src/shibuya/engine/contact/book.py](../../../../src/shibuya/engine/contact/book.py) | 宛先 `ContactBook` |
| [src/shibuya/engine/contact/port.py](../../../../src/shibuya/engine/contact/port.py) | 候補と仮のモデル `ContactPort`・文の口 |
| [src/shibuya/engine/contact/habit.py](../../../../src/shibuya/engine/contact/habit.py) | 習慣 `HabitBook` |
| [src/shibuya/engine/contact/tools.py](../../../../src/shibuya/engine/contact/tools.py) | 道具の台帳に足す 6 行 |
| [src/shibuya/perception/contact_view.py](../../../../src/shibuya/perception/contact_view.py) | 知覚の事実の値と描き方の行 |
| [src/shibuya/engine/tools/registry.py](../../../../src/shibuya/engine/tools/registry.py) | 道具の台帳 `ToolRegistry` |
| [src/shibuya/engine/tools/contacts.py](../../../../src/shibuya/engine/tools/contacts.py) | 連絡先の手段の印 |
| [src/shibuya/engine/tools/groups.py](../../../../src/shibuya/engine/tools/groups.py) | グループの一覧 `GroupList` |
| [src/shibuya/engine/tools/places.py](../../../../src/shibuya/engine/tools/places.py) | 店の番号の表 `PhoneTable` |
| [src/shibuya/engine/tools/record.py](../../../../src/shibuya/engine/tools/record.py) | 道具の一式 `build_fixture`・看板の記録 |

### 元の決定

`10-03/§7-7`・`10-12/§4-4`・`10-12/CT0`〜`CT5`・`10-12/CT9`・`10-12/CT10`・`10-12/TM1`・`10-13b/§1-7`(店の番号の表)・`10-12p/§2-1`。実装は #92(C0)・#116(C1)・#125(C2 ほか)。

### 棚卸しで見つかった指紋

V: A45(個体の枠の超過で連絡の行を落とす)。`engine/contact/` と `engine/tools/` は表の path の欄に出てきません。棚卸し A §3 は `contact_view.py` を読まなかったと書いています。

### 既知の穴

- 既定にできません。畳んだ後も 5,000 体 1 日で 155,148 行・27.9 MB/日、39 万体で約 2.17 GB/日で、記録の宣言 256 MB を超えます(#116・台帳 `DOC-ct-c1-not-default`)。
- 連絡の呼びは 5,000 体 1 日で、数え口 `judge_model` が 240,128・`llm` が 32,482 で、主の判断 64,528 の 3.7 倍です(#116 の記録の写し・今の HEAD の値は確かめていない)。**判断モデルも LLM も動いた数ではありません。** 判断モデルの中身は無く、`judge_model` は仮のモデル `ContactPort` の呼数、`llm` の連絡の分は定型の文の口 `MockTextPort` の呼数です(`contact/layer.py` の `model_calls`・`run._calls_by_model`)。既定のランでは `judge_model` は 0 です。
- C4(SNS・検索・口コミ)と C5(掲示・サイネージ)はありません(#125)。体の無い遠くの人は入れません(`contact/book.py`・`10-12/CT4`)。
- 打つ時間と読む間は窓の境目で代えています(台帳 `DOC-ct-c1-chat-clock`)。
- 関係の層の無いランの連絡先は家族だけです(`contact/book.py`)。

### 文書とコードの差

- `tools/places.py` の docstring は「版上げ 2 回目に OSM の `phone` タグから埋める」と書いています。今の `build_fixture` は空の `PhoneTable()` で、台帳の外す段は 7 です。
- `tools/contacts.py`・`tools/groups.py`・`tools/registry.py` の「C0 では誰も読まない」は C0 当時の文です。c1 のランでは `contact/book.py` が読み、1b は時計の行を読みます(`build.py` の `tools=`)。`tools/__init__.py` の文は「C0 は器だけ(既定の final・behavior-hash・テープ・描画は動かない)」で、既定のランについては今も合っています。

## 14. 店の仕事

### 何をしているか

既定では、店の開閉と補充をコードが動かします。

- 開閉(過程 `opening`): 5 分ごとに営業時間の表 W7 と店の状態を比べ、違う店を開け閉めします。担当がその店のセルに居れば `request_open_close` で本人の役割行動として記録し(ActualLog SCHEDULED)、居なければ代打です(`set_open_flags`・REPLACEMENT)。LLM は呼びません。
- 補充(過程 `shelf`): 5 分ごとに、営業中で棚が容量の 95% を割った店を見ます。担当が居る店を補充し、10 時に今日まだ補充していない店を代打します。代金は棚入れの瞬間に払います。
- 納品(過程 `delivery_inbound`): 5〜8 時に未陳列の枠が積まれます。物は動きません。

腕 `--duties arm` では、その店の雇用の行を持つ体が店のセルに居て起きている店を、コードが代わりにしなくなります。本人が店の決まり(W7 の行・担当だけが引ける)と店の中の気づきから、開ける/閉める/まだ、補充する/接客する/待つ、捨てる/まだ、を選びます。判断の担い手は仮のモデル(`duties/layer.py` の `DutiesPort`=固定・`--llm fleet` でも艦隊へ行かない)で、1 店 1 刻みに 1 人です。主の判断の役割語「補充」「開閉店」も、担当が店に居れば本人の行動になります(`role_sink`)。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 開閉 | 既定 | 切替口なし(`--duties` off のとき)。担当か代打 |
| 補充 | 既定 | `REORDER_FILL_RATIO`=0.95。担当か代打 |
| 納品 | 既定(入力の宣言) | `absent.inbound_delivery`(`engine_stopped=False`) |
| 発注 | 無い(初期の予定) | `absent.ordering` |
| 店の仕事を働く人の判断へ | 腕 | `--duties arm`(既定 off・`SHIBUYA_DUTIES`)。系 `duties` が立つ |
| 売れ残りの廃棄 | 無い | `absent.discard_unsold`。旧道 `--rate-rules legacy`。腕 duties の本人の分は残る |
| 接客 | 無い | `absent.serve_customer`。腕 duties の「接客する」は数えるだけ(`shelf:serve`) |
| 値段を変える | 無い | `absent.change_price`。`economy/pricing.py` は結線しない |
| 採用と解雇 | 無い | `absent.hiring_firing` |
| ごみ収集・街路の清掃 | 無い | `absent.waste_collection`・`absent.street_cleaning`。旧道 `--absent-processes legacy`(世界過程は A 群) |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/processes/opening.py](../../../../src/shibuya/engine/processes/opening.py) | `OpeningProcess`(開閉と代打)・担当の表 |
| [src/shibuya/engine/processes/goods_flow.py](../../../../src/shibuya/engine/processes/goods_flow.py) | `ShelfRestockProcess`・`DeliveryInboundProcess`・`WasteCollectionProcess`・`restock_by_staff`・`bin_by_staff` |
| [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `request_open_close`・`set_open_flags`・`restock`・`discard_to_bin` |
| [src/shibuya/engine/rights/initial.py](../../../../src/shibuya/engine/rights/initial.py) | 担当の雇用の行(W21c と丸振り)。権利の本体は C 群 |
| [src/shibuya/engine/duties/layer.py](../../../../src/shibuya/engine/duties/layer.py) | 持ち主 `DutiesLayer`・系 `duties`・`staffed_now`・監査 |
| [src/shibuya/engine/duties/knowledge.py](../../../../src/shibuya/engine/duties/knowledge.py) | 店の決まり `ShopRules` |
| [src/shibuya/engine/duties/port.py](../../../../src/shibuya/engine/duties/port.py) | 候補と仮のモデル `DutiesPort` |
| [src/shibuya/engine/duties/arm.py](../../../../src/shibuya/engine/duties/arm.py) | 切替口 |

### 元の決定

`10-12/§1-1`・`10-12/CP6`・`10-12/§1-4`・`10-12/§1-5`(②)・`10-12/CP3`・`10-12p/§2-1`・`10-25/§2-6`(丸振りの廃止=版上げ 5 回目・未着手)・`11-01/§2`・`11-01/§10-3`(routing #99〜#103)・`11-02r/§1`(#7)。実装は #123(腕)・#132・#136(既定から止めた分)。

### 棚卸しで見つかった指紋

E: S26(物理的に止める仕組み・権利の無い開閉店も止めない)。D: A27(役割語は安全弁の語「なし」へ落とす)。`processes/opening.py`・`processes/goods_flow.py`・`engine/duties/` は表の path の欄に出てきません(棚卸し B §5 は過程のファイルを読んでいないと書いています)。

### 既知の穴

- 抽出のランでは担当が店に居ることが少なく、腕 duties の本人の割合は 開けた 23/4,211(0.5%)・補充 5/47(10.6%)・捨てた 5/1,549(0.3%)でした(#123・#132 の前)。主因は丸振りの体がその店に居ないことです。組み直しは `10-25/§2-6` です。
- 既定の開閉の「担当が居る」はセルだけを見て、寝ているかを見ません(`OpeningProcess.step`)。補充の `has_permission` も種別とセルだけです(コードの読み)。腕 duties の `staffed_now` は起きていることまで見ます。
- 第 2 部以降(納品のドライバー・清掃・収集・運輸・出動・報道・催し・ホテル・値段)は未着手です(#123)。
- 代金は棚入れの瞬間です。在庫置場の節点と単独の域外仕入の口がありません(`goods_flow.py` の docstring)。

### 文書とコードの差

- `duties/layer.py` の docstring は担当の居ない店のつなぎを「売れ残りは 05:00」と書いています。`WasteCollectionProcess.step` の 05:00 の廃棄は `--rate-rules legacy` のときだけで、既定では本人の分しか捨てません。
- `goods_flow.py`・`opening.py` の `executor=llm_agent` は台帳の語で、既定の役割行動は LLM を呼びません(コードが条件を見て実行します)。
- `goods_flow.py` の docstring の補充点 80% は定数 0.95 と違います(段 1 §11 の 11)。
- `--role-words` の help は「役割語 12 語」と書いています。語彙 v3 の役割語は 11 語です(`contract.ROLE_ACTION_WORDS_V3`・「並ぶ」は行為の語へ移りました)。

## 15. 意図の保持と活動層(足した)

### 何をしているか

活動層は語彙 v3 の「活動」と「まで」を持ちます。エンジンが活動に持つのは、体の位置(「あたり」=近くを歩き回る)・持続(満了で呼び出し候補)・B4b の 1 行の 3 つです(`ActivityLayer`)。

意図の保持は、購入・食事・並ぶ・会話・就寝の対象が今のセルに無く解決できるとき、行為を意図として持って歩きます。着いたら LLM を呼ばずに実行します(`IntentLayer`)。歩いている間は場所の変化で呼びません。60 刻み歩いても着かなければ TOO_FAR です。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 活動層 | 既定 | `--activity` 既定 on(語彙 v3 のときだけ立つ) |
| 意図の保持 | 既定 | 活動層と候補の解決があるランで作る(`build.py`)・`--intent-max-ticks` 既定 60 |

### 実装しているファイル

| ファイル | 役割 |
|---|---|
| [src/shibuya/engine/intent.py](../../../../src/shibuya/engine/intent.py) | `IntentLayer` |
| [src/shibuya/engine/activity.py](../../../../src/shibuya/engine/activity.py) | `ActivityLayer`・`ActivityPayload` |
| [src/shibuya/engine/commit.py](../../../../src/shibuya/engine/commit.py) | セル外の対象を移動に変える `intent_hold` の道 |
| [src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) | `set_intent`・`clear_intent`・`fail_intent`・`set_activity` |

### 元の決定

`09-25/D-112`・`09-25/D-114`・D-116(索引に行なし・#46〜#48)・#54。

### 棚卸しで見つかった指紋

- K: A16(意図を持って歩く体の呼び出しを落とす)・A17(60 刻みで TOO_FAR)・A40・A41(既定 60 分)・B5(途中の「なし」で就寝の意図が消える・影響 大)・S22・S25(意図が黙って変わる種類)
- V: A18(着いた意図の順位の鍵)・A46(同じセルの活動の行)・A73

### 既知の穴

- 乗車の意図は別の道のままです(`intent.py` の Q19)。
- 列の印が消えない道が残ります(F4)。

### 文書とコードの差

- `intent.py` の docstring は「`engine.run` の結線」と書いています。実体は 1-0 で `engine/systems/` へ移っています。

## 16. 手伝い・断る・通報(足した)

### 何をしているか

語彙 v3 の語としてどれも受けます。mock は 12 語から一様に引くので、既定のランでも選ばれます。手伝いは必ず BAD_TARGET です(`_apply_help`)。断るは状態を変えず OK です(`_apply_record_only`)。通報は、自分のセルの顕著行為を 5 刻み以内に知覚していれば OK、なければ BAD_TARGET で、成立しても状態は変えません(`_apply_report`)。

### 状態

| 部分 | 区分 | 切替口と既定 |
|---|---|---|
| 語を受ける・結果を返す | 既定 | 切替口なし |
| 通報の前提の検査 | 既定 | `--report-precondition` 既定 on |
| 手伝いと断るの効果 | 無い | `absent.help_refuse_effect` |

### 実装しているファイル

[src/shibuya/engine/resolve.py](../../../../src/shibuya/engine/resolve.py) の `_apply_help`・`_apply_record_only`・`_apply_report`。

### 元の決定

`09-24d/D-113`(②)・#42・`11-01/§10-3`(routing #54・#55)。

### 棚卸しで見つかった指紋

D: M24(手伝いはいつも失敗)・S6(断ると通報は記録だけ)。V: S5(通報の窓 5 刻み)。

### 既知の穴

通報の受け手が居ません(`absent.public_service_dispatch`)。

## 17. 人物の文(足した)

### 何をしているか

差し替えの母集団の体ごとの短い版と長い版の文を読み、判断の入力の頭に置くための器です。今のランのプロンプトには入りません。段 1 §4-5 のとおり、人物像はプロンプトに載りません。

### 状態

器です。`load_persona`・`persona_blocks` の呼び手は src に無く(grep)、切替口もありません。

### 実装しているファイル

[src/shibuya/engine/decision/persona.py](../../../../src/shibuya/engine/decision/persona.py)。構築側の文は `src/shibuya/build/pop/w21_persona.py` です(このグループでは読んでいません)。

### 元の決定

`10-12/§4-10`・`10-12/DM4`・#111(文の材料)・#118(差し替え)。

### 棚卸しで見つかった指紋

V: A07(種別 5〜8 を「来街者」と書く・割れる)。文そのものの行はありません。

### 既知の穴

判断モデルの段で読む予定です(`persona.py`)。

## 読んでいないファイル

全部は読まず、次の範囲に留めました。

- docstring と定数だけを読んだファイル: `engine/contact/` の各ファイル(`layer.py` は頭 120 行)・`engine/calendar2/layer.py`・`engine/calendar3/layer.py`・`calendar3/roster.py`・`engine/duties/knowledge.py`・`duties/port.py`・`engine/calendar_self.py`(頭と `build`)・`engine/memory_store.py`・`engine/memory_m1.py`・`engine/memory_embed.py`・`engine/memory_shops.py`・`engine/store_memory.py`・`engine/wom.py`・`engine/relations.py`・`engine/relations_people.py`・`engine/familiarity.py`・`engine/speech/port.py`・`engine/speech_clock.py`・`engine/classical.py`・`engine/tools/` の各ファイル。
- 一部だけ読んだファイル: `engine/resolve.py`(購入・食事・会話・列・空腹の関数)・`engine/commit.py`・`engine/poi_target.py`(頭と `_rich_fields` と想起優先の分岐)・`engine/energy.py`(頭と `OutOfAreaMeals`・`HomeMeals` の頭)・`engine/memory.py`(頭 700 行ほど)・`engine/duties/layer.py`(頭と `run_step`)・`engine/processes/goods_flow.py`・`engine/processes/opening.py`・`engine/systems/build.py`(腕の組み立ての区間)・`perception/renderer.py`(grep だけ)。
- 読んでいないファイル: `engine/decision/layer.py`・`decision/port.py`・`decision/ports.py`・`decision/sources.py`(判断の口=C 群)・`economy/` の全部(C 群)・`engine/rights/ledger.py`・`rights/record.py`・`engine/events/` の本文・`engine/presence.py`(A 群)・`agents/weekly.py`・`agents/population.py` の本文・`build/` の全部・`tests/` と `tools/` の全部(カードの名前だけ)・`docs/design/spec/`(混ぜないため)・答申の本文。
- 読んだ記録は [fix4 §1-1](../../../bench/analysis/fix4-1103/README.md) と IMPLEMENTED の該当の項だけです。各段の記録(`docs/bench/analysis/wallbounce-1012/*`)は開いていません。

## 未確認

- 腕のランを回していないので、腕の数値は全部 #番号の記録からの写しです。今の HEAD の値は確かめていません。特に #123 は #132・#136 の前、#79 は #117・#118 の前の値です。
- 実 LLM での挙動は、どの機能も確かめていません。
- 棚の在庫が 0 の飲食店の食事の落選(3 節)の頻度は数えていません。店の初期の在庫の値は `data/` にあるので見ていません。
- 既定のランで通報がどれだけ成立するかは数えていません。段 1 §9 のとおり顕著行為の抽選が起きないので、ほとんど BAD_TARGET のはずですが、これは推測です。
- W20 の表 `w20_calendar_1a.parquet` が今の `data/world/v2` にあるかは確かめていません(`data/` を開かないため)。無ければ `--calendar 1b` と `--calendar-3 arm` は止まります。`calendar_shadow.STAGE_DIR` は `data/world/v2_stage_3-1` を指します。
- 今の母集団 345,858 体での関係の初期網の値は確かめていません。
- 連絡・カレンダー 2・カレンダー 3 の層の本文は docstring どおりに書きました。docstring と本文の突き合わせは、この節の外ではしていません。
- 決定の ID のうち、索引に行の無い D-93・D-95・D-116・D-118・D-119・D-120 と CA1 の原文は開いていません。D 番号の決定は [旧 PENDING の凍結](../../../log/pending-archive-2026-09-28.md) にあるはずですが、未確認です。
- 棚卸しの行の割り当ては、行の path と一言の文字列を機械で引いて選びました。ほかの機能に数えられる行を見落としている可能性があります。

## 11-09 の直し(段 2 の突き合わせ)

[段 2 の突き合わせ](../../stage2-crosscheck-2026-11-05.md) §4-b の番号です。どれも HEAD `14b151a` のコードで確かめてから直しました。11-09 の直しのために読んだのは poi_target.py の 395〜530 行・chooser.py の 105〜145 行・energy.py の 270〜295 行と 465〜490 行と 600〜641 行・resolve.py の 1233〜1255 行・contact/layer.py の 255〜270 行と 440〜485 行・run.py の 517〜545 行・duties/layer.py・calendar2/layer.py・calendar3/layer.py・calendar_self.py の口を作る行・calendar_shadow.py の 96〜100 行・build.py の 470〜495 行・tools/__init__.py の冒頭です。

| 突き合わせ | 直した所 |
|---|---|
| 食い違い 1(既定の店選びで距離が効かない) | 2 節の何をしているか・既知の穴・0 節の 2 行目 |
| 食い違い 2(空腹の比 0.03 は飲料だけ) | 3 節の何をしているか |
| 食い違い 3(在庫 0 の飲食店が購入の候補に残る) | 2 節の何をしているか |
| 食い違い 4(nav1 が立つ条件) | 5 節の既知の穴 |
| 食い違い 5(`tools/__init__.py` の文) | 13 節の文書とコードの差 |
| 食い違い 6(「判断モデル 240,128」) | 13 節の既知の穴・冒頭の「考える担い手」 |
| 食い違い 7(`SHIBUYA_CALENDAR_W20`) | 12 節の状態 |
| 食い違い 8(#番号の実測の値) | 確かめられない。読み方に「記録の値・コードでは確かめていない」の注を足した |
| 食い違い 9(W17 の中身) | 確かめられない。3 節と 12 節の既知の穴に「data では確かめていない」の注を足した |
| 食い違い 10(決定の原文との差) | 確かめられない。読み方に「決定の側は原文を開いていない」の注を足した |
| 書き漏れ 1(腕の層の口は仮のモデルに固定) | 冒頭の「考える担い手」・12 節・13 節・14 節 |
| 書き漏れ 2(`absent.deliberate`) | 冒頭の「考える担い手」 |
| 書き漏れ 3(`--decision-port`) | 冒頭の「考える担い手」 |
| 書き漏れ 4(`--classical-social`) | 4 節の状態 |
| 書き漏れ 5(`--chooser` の help) | 2 節の文書とコードの差。cli.py の help も直した |
| 書き漏れ 6(`ProximityLayer` の docstring) | 5 節の文書とコードの差。proximity.py の docstring も直した |
| 書き漏れ 7(既定の道で距離が効かない) | 2 節の既知の穴 |
| S12(払い出しは最大 8 スロット) | 1 節の既知の穴(C 群 C1 で確かめた) |
