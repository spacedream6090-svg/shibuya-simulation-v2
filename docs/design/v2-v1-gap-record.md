# v1 との差分の記録(穴の一覧)

- 作成: 2026-10-03(実行役 Opus 5.5・親の検収前)
- 元: 指示書 [v2-wallbounce-decisions-2026-10-03.md](v2-wallbounce-decisions-2026-10-03.md) の付録 A。指示書は「記録の文書にするときは、コードでもう一度確かめてください」と言っているので、各行を v1 リポ(隣のディレクトリ・読むだけ)と v2 リポのコードで確かめ直した。
- 書き方: v1 の場所は `v1:パス:行`、v2 の場所は `v2:パス:行`(どちらもリポ相対)。

## 0. 位置づけ

10-01 に v1 と v2 を 4 つの領域に分けて突き合わせた結果が付録 A。そのときの規模は「v1 約 9.7 万行・v2 約 7.4 万行」。今回 `git ls-files` で追跡中の .py を数え直した。

| 数え方 | v1(最終コミット 2026-09-01) | v2(本ブランチ) |
|---|---|---|
| `src/` の .py の行数 | **96,563 行** | **73,745 行** |
| リポ全体の .py の行数(tests・scripts・tools を含む) | 329,456 行(694 ファイル) | 158,660 行(469 ファイル) |

指示書の「9.7 万・7.4 万」は `src/` の .py の行数と一致する。リポ全体で数えると桁が変わるので、引くときは「src の行数」と添える。

## 1. v2 の今の判定の方法

- 「無い / 一部ある / ある」は、v2 の `src/`(.py・.json・.yaml。`__pycache__` を除く)と `docs/`(.md)を、Python の正規表現(大文字小文字を区別しない)で検索した結果で決めた。表の「検索語」の欄がその正規表現、「src 行」は当たった行の数、「docs」は当たったファイルの数。
- docs の当たりの大半は、指示書そのもの・v1 の写し(`docs/reference/v1/`)・計画の文。docs に当たっても、src に実装が無ければ「無い」とした。
- src の当たりが別の意味の語だった場合(例: 「地位」が「従業上の地位」)は、備考に書いて判定から外した。

## 2. 扱いが決まったもの(13 行)

| # | 穴の名前 | v1 にあった形 | v2 の今(検索語 → 結果) | 10-03 の扱い | 備考 |
|---|---|---|---|---|---|
| 1 | 日次の現実データ取得 | `v1:scripts/rw_fetch/cli.py:230`(main)・`v1:scripts/rw_fetch/ledger.py:66`(取得台帳への追記) | **無い**(src に)。`rw_fetch\|realworld_fetch\|_ledger\.jsonl` → src 0 行・docs 5。`tools/realworld_fetch/` は調査の初めには無かったが、調査の途中で別の作業が未追跡のまま作った(v1 の rw_fetch と同じ名前のファイル 10 本。§10-1 の写しと思われるが中身は未確認) | §10-1 | v2 は取得済みのファイルを読むだけ(`v2:src/shibuya/build/field/w13_weather.py:39` がアメダスの置き場を指す)。取得台帳 `data/realworld/_ledger.jsonl` は v1 が 440 行、v2 の写しが 463 行(gitignore 下・中身の差は未確認) |
| 2 | 信念・誤情報の伝播の計測、原因つきのイベントログ | `v1:src/society/truth_ledger.py:1266`(真偽台帳の phase)・`v1:src/society/observer/causality.py:664`(cause_of)。噂は `v1:src/society/rumors.py:471` | **無い**。`truth_ledger\|真偽台帳\|因果台帳\|causality\|cause_type\|原因つき` → src 0 行・docs 7 | 事後に抽出する(§10-2)。出来事の記録(§6 ①) | §10-2 は v1 の真偽台帳と原因台帳を移植しないと決めた。v1 の 3 つはいずれも既定 OFF |
| 3 | 世界を変える道具(出店・集会・チラシ・団体) | `v1:src/society/tools.py:534`(class Tools)・`v1:src/society/tools.py:773`(_post_flyer)。同ファイル冒頭に open_venture / host_event / post_flyer / found_group | **無い**。`post_flyer\|open_venture\|found_group\|チラシ\|出店` → src 1 行(`v2:src/shibuya/engine/wom.py:110` の店の語の一覧で、道具ではない)・docs 5 | 専用の道具は作らず、部品と裁定で(§6 ② ⑦) | |
| 4 | 個体差の源(backstory、ペルソナ) | `v1:src/society/world/backstory.py:49`(BackstoryStore)・`v1:scripts/build_persona_backstory.py`(100 万人分の事前生成) | **一部ある**。`backstory` → src 0 行・docs 3。`persona_pool\|ペルソナ` → src 10 行(`v2:src/shibuya/build/pop/pool.py:7`・`v2:src/shibuya/build/pop/w16_population.py:72`)。構造化された属性の母集団(100 万人)は読んでいる | §7-3 4-3 | 母集団の行には短い `persona` 欄(中央値 61 字)があるが、`"persona"` を名前で読む src の行は 0。backstory の写しは手元に見つからない(報告 `docs/bench/analysis/wallbounce-1003/v1-check.md` §1) |
| 5 | 電車の車内の空間(混雑、着席、毎朝同じ人) | `v1:src/society/transit_interior.py:1152`(phase・既定 OFF)。顔見知りの他人は `v1:src/society/net/contact_formation.py:15` 付近 | **無い**。`transit_interior\|車内\|顔見知り` → src 3 行。乗ると位置がセルを持たなくなる(`v2:src/shibuya/engine/resolve.py:2110` `r.node[riders] = -1`)=車内は空間になっていない | §8 3-8-3 | |
| 6 | 反実仮想の入口(v1 の worldmod) | `v1:src/society/world/worldmod.py:128`(class WorldMod・構築時に 1 回だけ適用する静的な改変 4 種) | **無い**。`worldmod\|world\.mod` → src 0 行・docs 4 | 保留(§12) | v2 の `src/shibuya/manifest/frozen/world_catalog_v0_2.json:506` に v1 の状態として「実装(edges_closed=反実仮想)」の記載がある |
| 7 | Chronicle | `v1:scripts/build_chronicle.py:6357`(main・6,617 行)。出力 `v1:viz/chronicle/chronicle.html` は生成物で git 管理外 | **無い**。`chronicle` → src 0 行・docs 16 | ビューアをゼロから作り直す(§6 ⑭) | |
| 8 | 共通乱数と並べ替え検定 | `v1:scripts/compare_runs.py:2`(同じ seed の対の比較と CRN の健全性検査)・`v1:scripts/panel_stats.py:216`(perm_test_paired) | **無い**。`置換検定\|並べ替え検定\|permutation test\|共通乱数\|common random\|\bCRN\b` → src 0 行・docs 24(計画と答申)。`tools/` も同じ語で検索して実装は 0(当たりは答申索引の説明文 1 行だけ) | §6 ⑮ | |
| 9 | 可搬性 | **v1 にも無い**(要件の文だけ: `v1:docs/plans/v2-requirements.md:64`)。近いものとして LLM サーバーの起動 `v1:ops/launch-vllm-finals.ps1`・退避 `v1:scripts/backup_run.py` がある | **無い**。`可搬\|portab\|lockfile\|コンテナ` → src 0 行・docs 20。両リポとも根に lock ファイル・Dockerfile・requirements は無い(ディレクトリ一覧で確認) | §6 ⑯ | v1 の `envpack.py` は「別の街へ移す」ための設定の分離で、§6 ⑯ の可搬性(環境の固定)とは別物 |
| 10 | 発言の本文が相手に届いていない | `v1:src/society/engine/scheduler.py:3211`(話し手と発言を次の呼へ渡す `_reply_to`)・`v1:src/society/engine/scheduler.py:3996`(DM の本文を受け手へ) | **一部ある**。`ひと言\|utterance\|発言の本文` → src 113 行。会話の器はある(`v2:src/shibuya/engine/conversation.py:84` `MAX_TURNS = 3`)が、相手に渡るのは定型文 `v2:src/shibuya/perception/templates.py:722`「会話の相手が話し終えたため、応じる必要があります。」だけ | Q57 (d)(既定の予定)。§6 ⑤ | 語彙 v3 にひと言の欄が無い(`v2:src/shibuya/engine/wom.py` 冒頭の説明) |
| 11 | 賃金がランにつながっていない | `v1:src/society/economy.py:262`(wage_amount)・`v1:src/society/engine/scheduler.py:4714`(_gov_payroll) | **一部ある**。`賃金\|wage\|payroll` → src 32 行。月給の送金の関数 `v2:src/shibuya/economy/anchors.py:217`(monthly_wages)はあるが、`monthly_wages` を呼ぶのは `tests/economy/test_anchors.py:75` だけ(src・tools・tests を検索) | §6 ⑧ 8-1 | 科目は `v2:src/shibuya/economy/accounts.py:117`(WAGE) |
| 12 | 日次の内省が本番で 1 回も呼ばれていない | `v1:src/society/cognition/reflection.py:393`(maybe_reflect)・`v1:src/society/engine/scheduler.py:6787`(呼び出し) | **一部ある**。`日次内省\|reflection\|T2` → src 81 行(T2 は決定論の受入の名前にも使われていて当たりが混ざる)。就寝で「発火を記録するだけ」(`v2:src/shibuya/engine/resolve.py:42`・`:2602`)。LLM の内省の呼は無い | §7-3(遅い思考は日中も) | 本番 0 回/日の記録: `docs/design/v2-architecture-overview-detailed.md:386` |
| 13 | ビューア | `v1:viz/make_viewer.py`(4,942 行)・`v1:viz/make_viewer3d.py`(2,716 行)。一覧は報告 §3 | **無い**。`viewer\|ビューア` → src 0 行・docs 16 | §10-3 | |

## 3. まだ決まっていないもの(9 行)

10-03 の扱いはすべて「未決。PENDING §5 に残す。行動の分類の突き合わせ(§11)の対象」。実装は先に聞く。v1 の機構はいずれも既定 OFF のモジュールだった。

| # | 穴の名前 | v1 にあった形 | v2 の今(検索語 → 結果) | 備考 | PENDING §5 の 1 行の文案 |
|---|---|---|---|---|---|
| 1 | 評判・ゴシップ・地位(第三者の評価が広まる仕組み) | `v1:src/society/gossip.py:329`(悪評の伝播の phase)・`v1:src/society/status.py:248`(合成地位の日次計算)・`v1:src/society/rumors.py:471`(情報オブジェクトの伝播) | **一部ある**。`評判\|reputation` → src 4 行(口コミ `v2:src/shibuya/engine/wom.py:118` ほか)。`噂\|rumou?r\|デマ` → src 1 行・`ゴシップ\|gossip` → src 1 行(どちらも world_catalog の v1 欄)。`地位\|prestige` → src 6 行(すべて「従業上の地位」で無関係) | 今の口コミは店名と評価語だけを運び、出来事・噂・デマは運べない | 評判・ゴシップ・地位: 第三者についての評価が広まる仕組み(v1 は gossip / status / rumors)。v2 の口コミは店名と評価語だけ。§11 の対象・実装は先に聞く([記録](docs/design/v2-v1-gap-record.md) §3-1) |
| 2 | 路上の生業(客引き、ティッシュ配り、路上音楽) | `v1:src/society/street_life.py:1009`(phase・客引きと条例パトロールを含む) | **一部ある**(役割の名前と知識の文だけ)。`客引き\|ティッシュ\|路上音楽\|street_life\|busk` → src 4 行。統計層の役割名 `v2:src/shibuya/agents/population.py:15`、客引き防止地区の役割知識 `v2:src/shibuya/perception/templates.py:301`。行動の機構は無い | | 路上の生業: 客引き・ティッシュ配り・路上音楽(v1 は street_life)。v2 は役割名だけ。§11 の対象・実装は先に聞く(記録 §3-2) |
| 3 | 火災と歩行者の事故 | `v1:src/society/incidents_env.py:1290`(phase・火災 / 交通 / 群集の 3 族) | **無い**。`火災\|fire_incident\|incidents_env` → src 0 行・`歩行者の事故\|交通事故\|accident` → src 0 行 | | 火災と歩行者の事故(v1 は incidents_env)。v2 には無い。§11 の対象・実装は先に聞く(記録 §3-3) |
| 4 | 遺失物のループ | `v1:src/society/lost_property.py:1024`(phase・落とす→拾う→届ける/着服) | **無い**。`遺失\|lost_property` → src 0 行・docs 7 | | 遺失物のループ(v1 は lost_property)。v2 には無い。§11 の対象・実装は先に聞く(記録 §3-4) |
| 5 | 混雑が停車時間を延ばして遅延になる閉ループ | `v1:src/society/transit_staff.py:445`(_dwell・ホームの負荷→停車時間→遅延)・`v1:src/society/engine/scheduler.py:6836` | **一部ある**。`停車時間\|dwell` → src 43 行(食事の滞在時間なども混ざる)。停車時間は線別の静的表で混雑を見ない(`v2:src/shibuya/engine/processes/rail.py:66`〜`67`) | ODPT の運行情報が答え合わせになる(§10-1 で検証専用) | 混雑→停車時間→遅延の閉ループ(v1 は transit_staff)。v2 の停車時間は線別の静的表。§11 の対象・実装は先に聞く(記録 §3-5) |
| 6 | 重症化・入院・死亡 | `v1:src/society/health.py:29`(S0〜S4 と回復/死亡の状態機械の説明)・`v1:src/society/medical.py:582`(搬送・入院の phase) | **無い**。`入院\|重症\|hospitali[sz]` → src 0 行・`死亡\|death` → src 0 行。病院は場所の種類としてだけある(`v2:src/shibuya/engine/poi_target.py:156`) | | 重症化・入院・死亡(v1 は health / medical)。v2 は病院が場所の種類としてあるだけ。§11 の対象・実装は先に聞く(記録 §3-6) |
| 7 | 人口の出入り、転居、加齢 | `v1:src/society/population.py:537`(転出)・`:682`(転入)・`:852`(出生)、転居 `v1:src/society/engine/simulation.py:636`、加齢 `v1:src/society/aging.py:91` | **無い**。`転居\|転出\|転入\|migrat` → src 0 行・`加齢\|aging\|誕生日` → src 0 行 | | 人口の出入り・転居・加齢(v1 は population / aging)。v2 には無い。§11 の対象・実装は先に聞く(記録 §3-7) |
| 8 | 対人サービス(美容室、医院、塾、ジム) | `v1:src/society/services.py:424`(apply_effect・滞在して効果を受ける) | **一部ある**(場所の種類と営業時間だけ)。`美容室\|理美容\|医院\|clinic` → src 7 行・`学習塾\|ジム\|\bgym\b` → src 10 行。POI の分類 `v2:src/shibuya/build/geo/poi_class.py:101`、営業時間 `v2:src/shibuya/build/field/w7_planspec.py:246` | | 対人サービス: 美容室・医院・塾・ジム(v1 は services)。v2 は場所の種類と営業時間だけ。§11 の対象・実装は先に聞く(記録 §3-8) |
| 9 | 監督と自動復旧(watchdog) | `v1:scripts/watchdog.py:290`(class Watchdog)・`v1:scripts/watchdog_llm.py` | **無い**。`watchdog\|自動復旧` → src 0 行・docs 8(`docs/ops/v2-server-lessons.md` ほか) | §6 ⑯ の可搬性(一発起動・退避)と近い | 監督と自動復旧(v1 は scripts/watchdog)。v2 には無い。§6 ⑯ と合わせて検討・実装は先に聞く(記録 §3-9) |

## 4. v1 から空間に使えるもの(4 行)

v1 リポで実物を開いて数えた。数値は指示書と実測を並べる(どちらが正しいかは決めない)。

| # | もの | v1 の実物 | 実測 | 指示書の値 | v2 の今 | 備考 |
|---|---|---|---|---|---|---|
| 1 | 建物の外形の多角形 | `v1:data/shibuya_osm_wide_v8.json` の `buildings`(欄: id・name・levels・kind・footprint・entrance・area・cx・cy) | 7,210 棟。footprint が頂点 3 つ以上の多角形のものも 7,210。`v1:data/shibuya_osm_wide_v7.json`・`v1:data/shibuya_osm_wide_20250401.json` も 7,210 | 7,210 棟 | **一部ある**。同じファイルの写しが `data/realworld/osm/shibuya_osm_wide_v8.json`(md5 一致)。使い方は入口の射影に重心だけ(`v2:src/shibuya/build/geo/w5_entrances.py:17`)、視界の遮蔽に 2.5 m のラスタ(`v2:src/shibuya/build/vis/w8_visibility.py:15`) | 一致。ただし v1 の既定の地図 `v1:data/shibuya_osm.json` は 1,181 棟で別物(v1 の記録 `v1:docs/log/devlog-block7to9-fulltext.md:260` にも同じ注意) |
| 2 | フロアの構成 `floor_layouts.json` | `v1:data/floor_layouts.json`(meta + buildings。階ごとに用途・区画数) | 21 棟・197 階。階の範囲は B3〜47F | 21 棟・197 階 | **無い**。`floor_layouts` → src 0 行。v2 の `data/` にも無い(ファイル名で検索) | 一致。meta の注記は「幾何区画配置は非公開のため収録せず、手続き生成への制約に限定」。v1 の屋内の間取りは layout の bbox から格子を作る(`v1:src/society/world/indoor_flow.py:270`〜`273`)・「簡略間取り」(同 `:187`)。使うなら仮の値として宣言する(指示書どおり) |
| 3 | `floorguide` | `v1:data/floorguide_shibuya.json`(meta + buildings。各施設に floors と connections) | 10 施設・99 階。階の範囲は全体で **B5〜47F**。B5〜3F なのは「渋谷駅」の行(-5〜3)。最上は渋谷スクランブルスクエアの 47 | 10 施設・地下 B5〜3F | **一部ある**。写しが `data/realworld/osm/floorguide_shibuya.json`(md5 一致)。使っているのは直結 22 本だけ(`v2:src/shibuya/build/geo/w11_station_exits.py:3`・`:43`) | **合わない**: 施設数は一致、階の範囲は指示書 B5〜3F・実測 B5〜47F |
| 4 | 店と建物・階の対応 | `v1:data/shibuya_osm_wide_v8.json` の `pois`(欄 building・floor) | POI 2,337 件のうち building・floor の欄を持つもの 1,607 件。floor が 0 以外のもの **215 件**(food 79・shop 65・nightlife 30・office 23・service 9・hall 5・school / cinema / attraction / leisure 各 1)。店に近い 4 種(food・shop・nightlife・service)に限ると 183 件。v7 の地図では 215 ではなく 190 件 | 地上以外の階の店 215 件 | **一部ある**。W6 が POI の floor を列として運ぶ(`v2:src/shibuya/build/geo/w6_poi_org.py:212`) | 件数は一致(floor≠0 の POI 全体として)。ただし office・hall・school などを含むので「店」と呼ぶなら 183。floor の値が建物の階数を超えるものがある(`v1:src/society/world/floors.py:14` に v1 の既定地図で 20 件の記載) |
| 5 | 面の中かどうかの判定と入口の列挙(`zones.py`) | `v1:src/society/world/zones.py:298`(point_in・ray casting・境界上は内側)・`v1:src/society/world/zones.py:800`(gates_of・面の外にあって面の中のノードに隣接するグラフのノードを列挙) | 実在を確認(879 行) | `zones.py` | **無い**。`zones\.py\|gates_of` → src 0 行。`point_in\|point_in_polygon\|内外判定` → src 5 行(すべて W8 の「多角形内外判定をラスタで代用した」という説明) | 一致。v1 の「面」は歩行者の物理のゾーン(class Zone `v1:src/society/world/zones.py:221`)で、建物の外形ではない。入口はグラフのノードで、建物の入口の欄(`entrance`)とは別 |

表の行数は指示書の「4 行」に合わせ、2 行目(floor_layouts と floorguide)を 2 と 3 に分けたので 5 行になった。

## 5. 指示書の数値と実測が合わなかったもの

- 1 件: floorguide の階の範囲(指示書「地下 B5〜3F」・実測「B5〜47F」。B5〜3F は渋谷駅の行だけの範囲)。
- 数は一致したが中身に注意が要るもの 2 件: 店と建物・階の 215 件(店以外の POI を含む。店に近い 4 種で 183)、建物 7,210 棟(広域の地図の数。v1 の既定の地図は 1,181)。
- 規模の 9.7 万・7.4 万は `src/` の .py の行数として一致。
