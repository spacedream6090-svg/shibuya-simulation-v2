# 第 1 期 1-7 道具の台帳 C0(CT0・CT5・CT9・CT10)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-7/tools-c0`(HEAD `e0865b3`=T0・1-3・1-4・1-6・1-9・1-2・1-5 を取り込んだ後)。commit は親。
- 正: [口の約束 1-7](../../../../design/v2-foundation-contracts-2026-10-13.md)(口・約束 3 つ・受入の試験・〔決定(回答 10-13b §3)〕店の番号の場所の表は OSM の `phone` タグから作る)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) 第 1 期 1-7・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-4 CT0・CT5・CT9・CT10・§1-13・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(仮採用)・§1 1-5(将来の音声・表情にも同じ口)・[道具の草案](../../../../design/v2-communication-tools-design-round-draft.md) の〔答え〕。先例は [R-113](../../../../research/v2-r113-e1-foundations-existing-implementations.md) §8(AgentSociety 2 の `@tool(readonly, kind)`+`EnvMeta` の登録表と全呼び出しの記録=Apache-2.0・形だけ借りた・コードは写していない)。手段の材料は [R-85](../../../../research/v2-r85-communication-tools.md) §1・§2-6・§5-1。
- 数は実測。生の出力(テープ・side の JSON)は git の外の作業用の置き場(作業木の `_bc/`)に置いた。比べた結果と道具だけをこのフォルダに置く。
- 道具(`tools/`・使い方は各ファイルの冒頭・絶対パスなし): `add_bridges_c0.py`(つなぎの台帳に 1-7 の行を足す・`--check`)・`count_osm_phone.py`(OSM の `phone` タグを持つ要素の数と W6 の POI との番号の結び)・`manifest_check_c0.py`(10f の manifest の 2 つの側を比べる・r15 の道具の写し)・`signboard_volume_c0.py`(看板を読んだ出来事の腕を入れたときの行数)。byte-check は既存の道具(`10e/byte_check_10e.py`)。

## 0. 結論

- **道具の台帳**(`engine/tools/registry.py`): `Tool`(口の約束の 6 欄+将来の音声・表情 `modality`・中身の出どころ `content_origin`・使う口の段 `stage`・つなぎの行 `bridge`・凍結)と `ToolRegistry`(**書く口は `register` の 1 つ**=足すだけ・表は `MappingProxyType`・中身は名を変えた slot・属性の付け替えと消去は `AttributeError`)。最初の中身は 7 行(看板・掲示・電話・連絡先・グループ・乗換案内・地図=§2)。今の世界で使っているのは看板と掲示、残りの 5 つは登録だけ(使う口は 6-4=C1〜)。
- **個人の連絡先(CT5)**: 関係の記憶の層に `contact_flags`(体 × k・手段 4 つのビット)を足した。既存の `rel_*` の列と書き方は変えていない(印を書く口を止めたランと値まで同じ)。家族(世帯の辺)と職場(職場の辺)は初めから印あり。書く口は `_write_contacts` 1 つ(AST と負の対照)。C0 では誰も読まない(印を乱しても final が同じ)。状態台帳の行 `CT5`(軸 1 diag=読み手は持ち主の数えの口 `contact_tally`(manifest)だけ・軸 2 derivable・hash_skip)。
- **グループの一覧(CT10)**: 家族=W16 の世帯・職場=W16 の事業所(W6 の組織)。**全母集団で 27,404+9,872=37,276 行=世帯の数+事業所の数**(検算・§3)。
- **店の番号の場所の表**: 空の表 `PhoneTable` と読み口 `phone_of`。空欄は `BR-PHONE-TABLE-BLANK`(外す段 2-4)。OSM の `phone` タグを持つ要素は **575/3,516**(2026-09-28 の取り直し)。W6 の POI は OSM の番号で結べ、`phone` を持つのは 477 行(§5)。
- **記録の欄(CT9)と看板の作り物の印**: 1-3 の `via`・`received_ns`/`read_ns`・`origin` を使い、看板を読んだ出来事(`道具:看板`)に `origin="signboard:synthetic"` を付ける口を作った。**腕(既定 off)**。on と off で描画の全部のバイトが同じ(§6・§8)。
- **結果不変**: byte-check **19/19 構成で 25 欄とも HEAD と同じ**。manifest の 7 本は既存の欄が全部同じ(動いたのは `bridges_count` 282 → 284 と `bridges_version` だけ=つなぎの台帳に 2 行を足したため)(§7)。
- manifest の末尾に `tools`(道具の数・グループの数・連絡先の印の数・店の番号の表・看板の印=観測の節)。
- 試験: 新しい試験 7 ファイル・70 本(§11 の直しと §12 の結線の後)。全体は 4,563 passed・既知の落ち 1 件(§8)。仮採用は §10 の 12 件。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/tools/__init__.py`(新規) | 包みの説明だけ(下のモジュールを import しない=`engine.relations` が `contacts` を読むので循環を作らない) |
| `src/shibuya/engine/tools/registry.py`(新規) | `Tool`(凍結・slots・欄は口の約束の 6 つ `name`・`known_by`・`requires`・`affects`・`owner`・`content_writer` と `modality`・`content_origin`・`stage`・`bridge`)・`KnownBy`(全員・誰も・番号の集合=既定は全員 `EVERYONE`)・`ToolRegistry`(読み口 `get`・`known`・`rows`(MappingProxyType)・`names`・`in_use`・`registered_only`。**書く口は `register` の 1 つ**=足すだけ・同じ名は `ValueError`。中身は名を変えた slot 1 つ・`__setattr__`/`__delattr__` の守り)・最初の中身 `DEFAULT_TOOLS`(§2)・`default_registry()` |
| `src/shibuya/engine/tools/contacts.py`(新規) | 連絡先の手段の印(`MEANS`=通話・メッセージ・メール・職場の連絡=ビット 1・2・4・8)・初めの印(`INITIAL_FLAGS_BY_KIND`)・`flags_from_kinds`(辺の種別 → 印)・`tally`(manifest の数え)。種別の番号は `engine.relations.REL_KINDS` の写し(一致は試験) |
| `src/shibuya/engine/tools/groups.py`(新規) | `GroupList`(家族=W16 の世帯・職場=W16 の事業所=W6 の組織・CSR・書く口なし=`from_population` で作る・読み取り専用の配列)・`tally` |
| `src/shibuya/engine/tools/places.py`(新規) | `PhoneTable`(店の番号の場所の表・C0 は空・読み口 `phone_of(poi_id)`・作った後は書けない)・`osm_phone_of`(OSM の `phone`→`contact:phone` の規則=数えの道具と試験が同じ関数) |
| `src/shibuya/engine/tools/record.py`(新規) | 看板を読んだ出来事の口 `SignboardReadLink`(作り物の印 `signboard:synthetic`・腕 `SHIBUYA_TOOL_EVENTS`=既定 off)・`ToolsFixture`(台帳・グループ・店の番号の表・看板の口)・`build_fixture`・`manifest_fields`(manifest の `tools`) |
| `src/shibuya/engine/relations.py` | 関係の記憶に `contact_flags`(体 × k の uint8=欄の位置は `rel_*` と同じ・`rel_*` の列と書き方は変えない)。書く口 `_write_contacts` 1 つ(呼ぶのは `seed_initial`=初めの辺・`_reset_slots`=欄の相手が替わった・`rebuild_contacts`=再開)・数えの口 `contact_tally`(manifest が読む=持ち主の外で欄を読まない)。docstring |
| `src/shibuya/engine/state_ledger.py` | 行 `CT5`(`rel_layer._contact_flags`=§11 の L1 の後の名・軸 1 diag・軸 2 derivable・中身は hash_skip=1-6 の M0 と同じ形)・docstring の行の数 192 → 193 |
| `src/shibuya/engine/systems/table.py` | decide: `writes.paths` に `E:events.*`(看板を読んだ出来事=腕のときだけ書く)・`reads` に `fx.tools`/memory: `writes.paths` に `CT5:rel_layer._contact_flags`(§11 の L1 の後の名)(新しい相手の欄の印を消す)/report: `reads` に `fx.tools`/docstring の 1 段落 |
| `src/shibuya/engine/systems/decide.py` | 系の終わりに、腕のランだけ描いた知覚の事実から看板を読んだ出来事を書く(3 行)・docstring |
| `src/shibuya/engine/systems/boxes.py` | `Fixtures.tools`(既定 `None`) |
| `src/shibuya/engine/systems/build.py` | 出来事の記録を作った後に道具の一式を作り、`Fixtures(tools=…)` へ |
| `src/shibuya/engine/systems/state_io.py` | `rebuild_derived`(再開だけ)で連絡先の印を戻した辺の種別から作り直す |
| `src/shibuya/engine/systems/report.py` | `result.tools = manifest_fields(…)` |
| `src/shibuya/engine/run.py`・`manifest_sections.py` | `RunResult.tools`・manifest の末尾に `tools`(観測の節) |
| `src/shibuya/engine/events/vocab.py` | 族 `道具`(族の並びの末尾)・語 `道具:看板`(表の末尾=57 語・1-5 までの 56 語のコードは動かない)・原因の名 `perception`(`PERCEPTION_PROCESSES`)・版 `events-vocab/1-7` |
| `docs/design/bridging-ledger.json` | 2 行を足した(§4)。既存の行は変えていない |
| `tests/engine/tools/`(新規) | §8 |
| 凍結の表(増えた分だけ) | `tests/engine/time/manifest_keys_frozen.json`(末尾に `tools`=115 鍵)・`tests/engine/events/writes_paths_events.json`(decide) |
| **発注の編集してよい一覧の外**(数と並びの固定を直しただけ) | `tests/engine/events/test_e_vocab_is_closed.py`(56 → 57 語・版)・`tests/engine/bridging/test_bridging_ledger.py`(見出し 76 → 77・ファイル 73 → 74・項 342 → 345・`HD-` の行 76 → 77)・`tests/engine/test_state_ledger_10b.py`(外の状態 101 → 102・全体 192 → 193・行 CT5)・manifest の末尾の並び(`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/perception/facts/test_percept_schema.py`・`tests/engine/rights/test_rights_manifest.py`)・`tests/engine/rights/test_rights_events.py`(1-5 の語の位置 `VOCAB[-1]` → `VOCAB[55]`)。発注が「語彙に足す」「新しい宣言は台帳に行を足す」「状態台帳に行を足す」「manifest に欄」を決めているので、直さないと落ちる(1-3〜1-5 と同じ扱い) |

## 2. 道具の一覧(最初の中身・`DEFAULT_TOOLS`)

| 名 | 知っている | 要るもの | 体と知覚への影響 | 誰が持つか | 中身を書くのは | 中身の出どころ | 使う口の段 | つなぎの行 |
|---|---|---|---|---|---|---|---|---|
| 看板 | 全員 | ― | 空 | 店 | 他人(店) | **作り物**(W14 で LLM が書いた文) | 今(描画の B2 の看板の行) | `BR-SIGNAGE-FICTION`(1-4) |
| 掲示(店の営業時間) | 全員 | ― | 空 | 店 | 他人(店) | 実データ(W7=OSM の `opening_hours` 565 件+チェーンの伝播・残りはカテゴリの既定値) | 今(開いているかの判定・失敗の直後の次の開店の時刻) | `W7#1`(カテゴリの既定値) |
| 電話(店の番号) | 全員 | 持ち物:携帯電話・契約:電話の契約・回線:電話の網 | 空 | 本人 | 本人 | 無し(店の番号の表は空) | 6-4(C1) | `BR-PHONE-TABLE-BLANK`(1-7) |
| 連絡先(関係の記憶の印) | 全員 | ― | 空 | 本人 | 本人 | 実データ(W16 の世帯と事業所から初めの印) | 6-4(C1) | ― |
| グループ(家族・職場) | 全員 | 持ち物:スマートフォン・契約:メッセージのアカウント・回線:データ通信 | 空 | 成員 | 本人 | 実データ(W16) | 6-4(C1) | ― |
| 乗換案内 | 全員 | 持ち物:スマートフォン・回線:データ通信 | 空 | 本人 | 機械 | 無し(登録だけ) | 6-4(C1〜) | ― |
| 地図 | 全員 | 持ち物:スマートフォン・回線:データ通信 | 空 | 本人 | 機械 | 無し(登録だけ) | 6-4(C1〜) | ― |

- `modality`(将来の音声・表情)はどの行も空(`None`)。`affects` も空(目の向き・心の向きは CT2 の段)。
- 値は実装役が決定 10-12 §4-4 と R-85 §1 の道具の一覧から当てた(未リサーチ=expedient・C0 では誰も読まない)。
- 中身が作り物の道具はつなぎの台帳の行を持つ(`Tool` の検査)。各行の `bridge` は台帳の active の行(試験)。

## 3. グループの一覧の行数の検算

| 母集団 | 行(=世帯+事業所) | 家族(世帯) | 職場(事業所) | 成員(家族/職場) | 一番大きい行(家族/職場) |
|---|---|---|---|---|---|
| 全母集団(390,067 体) | **37,276** | 27,404(=`w16_households.parquet` の行) | 9,872(=`w6_org.parquet` の行=W16 の `org_id` の種類) | 43,588/222,849 | 3/1,756 |
| 5,000 体・seed 1(既定のラン) | 1,854 | 474 | 1,380 | 475/2,421 | 2/18 |
| 5,000 体・seed 2 | 1,838 | 475 | 1,363 | 475/2,421 | ― |

- 全母集団では W16 の世帯 27,404 行と W6 の組織 9,872 行のどれにも成員がいる(体の番号の無い世帯・組織は 0)=**行の数=世帯の数+事業所の数**(試験 `test_rows_equal_households_plus_establishments_on_the_full_population`=parquet の行の数と値まで)。成員の数は `household_id`・`org_id` を持つ体の数と同じ。作る時間 0.027 秒・2.8 MB(目安)。
- ランの一覧はランの体に成員のいる世帯・事業所だけ(5,000 体の抽出では世帯の成員は 1〜2 人=定員先取り層が先に入るため・職場の成員 2,421=1-5 の雇用の行と同じ数)。

## 4. つなぎの台帳に足した行(282 → 284 行)

| id | 外す段 | 根拠 | 中身 |
|---|---|---|---|
| `HD-engine.tools.contacts-1af925f4` | 6-4 | inferred | `contacts.py` の見出し「expedient(本モジュール分)」の項 3 個(手段の印の 4 つ・初めの印の値・学校ほかの辺は印なし) |
| `BR-PHONE-TABLE-BLANK` | 2-4 | inferred(発注「版上げ 2 回目で OSM の phone から埋める」) | 店の番号の場所の表は空(`code_at`=`engine/tools/places.py`) |

- 看板の作り物の印は 1-4 の `BR-SIGNAGE-FICTION` に結んだ(行は足していない=`engine.tools.registry.SIGNAGE_BRIDGE`)。掲示はカテゴリの既定値の `W7#1` に結んだ。
- 1 対 1(コードの宣言 ↔ 台帳の行)は 6 形とも欠け 0・余り 0。数: 見出し 76 → 77(ファイル 73 → 74・項 342 → 345)・`HD-` の行 76 → 77。

## 5. 店の番号の場所の表と OSM の `phone` タグの数

- `PhoneTable` は空(行 0)。読み口 `phone_of(poi_id)` は全部 `None`。空欄はつなぎの台帳 `BR-PHONE-TABLE-BLANK`(外す段 2-4)。
- 数えた規則: `engine.tools.places.osm_phone_of`(`phone` を先に・無ければ `contact:phone`・空は無し)。記録 [osm_phone_count.json](osm_phone_count.json)(道具 `count_osm_phone.py`・ネットは使わない=手元の取得物だけ)。

| 手元の OSM の取得物(ODbL・ライセンス台帳にある) | 要素 | `phone` タグを持つ | 内訳 |
|---|---|---|---|
| `poi_tags_overpass_20260928.json`(amenity・shop・leisure・tourism・office・craft・healthcare) | 3,516 | **575(16.4%)** | `phone` 476・`contact:phone` 100(1 件は両方)/ amenity 366・shop 157・office 30・tourism 12・leisure 6・craft 3・healthcare 1 |
| `poi_opening_hours_overpass_20260907.json`(W7 の営業時間の取得) | 2,164 | 457(21.1%) | `phone` 377・`contact:phone` 81 |
| `shibuya_osm_wide_v8.json` の `pois`(W6 の POI の元) | 2,337 | 0 | タグを持たない(欄は id・名・種類・位置だけ) |

- **2-4 の材料(見つけたこと)**: `w6_poi.parquet` には OSM の番号の列が無いが、**元の JSON の行の並びで OSM の番号に結べる見込み(2,259 行・`phone` 477 行)=2-4 で確かめる**。W6 の POI の行 i は `shibuya_osm_wide_v8.json` の `pois[i]`(名が 2,337 行とも同じ)で、その `id` は OSM の要素の番号(`p_n<node>`・`p_w<way>`)を持つ。OSM の番号を持つ 2,327 行のうち 2,259 行が 2026-09-28 の取り直しの要素と番号で結べ、そのうち 477 行が `phone` タグを持つ(残りの 10 行は手で足した POI=番号なし)。W6 の構築の段に OSM の番号の欄を足す形が考えられる。結べない 68 行(2025-04-01 の時点の要素で 2026-09-28 に無い・番号が変わった)の扱いは 2-4 で決める。`places.py` の docstring とつなぎの台帳の行 `BR-PHONE-TABLE-BLANK` も同じ書き方にそろえた(検収 L3)。

## 6. 記録の欄(CT9)と看板の作り物の印

- 1-3 の `Event.via`・`received_ns`/`read_ns`・`origin` を使った(新しい欄は足していない)。
- **看板を読んだ出来事**(`engine.tools.record.SignboardReadLink`): 判断の系(decide)の終わりに、その刻みに描いた知覚の事実(`Percept`)のうち見えた物に看板(`seen_objects` の種類 `signage`=注視のゲートを通って B2 に看板の行が載った物)がある体ごとに 1 行。`who`=体・`what`=`道具:看板`・`where`=(`poi`, 看板の POI)・`via`=`無し`・`received_ns`=`read_ns`=その刻みの頭・`origin`=`signboard:synthetic`・`cause`=`Process("perception")`。描画の後に事実を読むだけ=描画・判断・テープは変わらない(試験 `test_c0_signboard_mark_invariance.py`=腕の on/off で全部の描画の本文・ブロック・指紋が同じ・合成の世界と世界資産)。
- **腕(既定 off)**: `SHIBUYA_TOOL_EVENTS=on`(か `record.set_enabled(True)`)。組み立ての時に読む。出来事の記録が off(`SHIBUYA_EVENTS=off`)なら口を作らない。`run_day` の引数・CLI にはしていない(設定の指紋に入れない=出来事の記録の切替口と同じ扱い)。
- **腕を入れたときの量**(記録 [signboard_volume_c0.json](signboard_volume_c0.json)・道具 `signboard_volume_c0.py`・5,000 体・seed 1・1 日・既定 v3): 看板を読んだ出来事 **65,002 行/日**(呼 65,597 の 99.1%=ほぼ全部の描画に看板が載る)。出来事の記録の行は 32,158 → 97,160 行/日・2.3 → 7.0 MB/日。final と呼数は同じ(`5f7ae9ff24005314`・65,597)。壁時計は 48.2 秒 → 47.7 秒(目安=差は見えない)。全母集団に比例で当てると約 500 万行/日・約 365 MB/日(保持窓 7 日で約 2.5 GB・推計)。
- 既定を off にした理由: 既定で書くと manifest の日次の記録 `events` の既存の欄(`rows`・`bytes`・`by_what`・`live_rows`・`live_bytes`)の値が動く(発注「manifest の既存の欄は不変」)。上の量も判断の材料(§10 の 1)。

## 7. 結果不変

| 検査 | 方法 | 結果 |
|---|---|---|
| byte-check 19 構成([byte_check_c0.json](byte_check_c0.json)) | `10e/byte_check_10e.py`・5,000 体・seed 1・1 日・テープつき。HEAD の側は本体の `e0865b3` の `git archive` の写し(src・anchors・予算の表・w6 の道具・`rules-table.json`・`bridging-ledger.json`+祝日の CSV・`src_is_worktree` 偽)、c0 の側は作業木の src(`--src`・`src_is_worktree` 真) | **19/19 構成で 25 欄とも同じ**(final・呼数・テープの列と sha・行動の件数・behavior/full-hash・締めの後・暦ほか)。既定 v3 の final `5f7ae9ff24005314`(1-5 の記録と同じ値) |
| manifest の 7 本([manifest_check_c0.json](manifest_check_c0.json)) | 10f の `manifest_check_10f.py side`(両側 `PYTHONHASHSEED=0`)→ `tools/manifest_check_c0.py` | **all_ok**。既存の欄 1,766〜2,282 個が全部同じ(日次の記録の `events` も同じ=腕は既定 off)。足したのは `tools` の中の欄と節の表の 1 行(関係の無い構成 25・関係のある構成 37)。動いたのは `bridges_count`(一番上と日次の行=282 → 284)と `bridges_version`(`3b7e73ad707bf9b1` → `9520069a801b8065`)だけ。final は 7 本とも同じ |
| 腕の on/off(試験・道具) | `test_c0_signboard_mark_invariance.py`(合成の世界 60 体と世界資産 2,000 体)・`signboard_volume_c0.py`(5,000 体・既定 v3) | final・呼数・全部の描画の本文・ブロック・指紋・看板の物が同じ。日次の記録の差は `道具:看板` の行だけ |
| 印を書く口を止めたラン・印を乱したラン(試験) | `test_c0_contacts_in_relations.py`(合成の世界 80 体 720 刻み・世界資産 2,000 体 300 刻み) | final・呼数・`rel_*` の 6 列が値と型まで同じ |
| 再開(試験) | 世界資産 2,000 体を 150 刻みで止めて再開 | final が通しと同じ・連絡先の印も通しと同じ(作り直し) |
| 2 日のラン([two_day_c0.json](two_day_c0.json)・§8 の直しの前の src) | `10e/two_day_check_act.py one`(5,000 体・seed 1・sim_days=2・既定 v3・テープつき)を HEAD の写しと作業木で | **16 欄のうち名札・`src_is_worktree`・壁時計の外は全部同じ**(final `912446bd2b42b6ab`・140,913 呼・テープの calls `cb330e76b4b8a573`・blocks `7f09f3dc78d84ac4`・暦 07-13 → 07-14・天気の日ごとの記録) |
| 系ごとの指紋([probe_c0_head_ledger.json](probe_c0_head_ledger.json)・最後の src) | `tools/probe_c0.py`(1-0 の probe・全部の刻み・`PYTHONHASHSEED=0`)。3 構成(合成 80 体 720 刻み 記憶+関係+同席+店・世界資産 300 体の既定 v3・記憶+関係)。作業木の側だけ 1-7 で足した道筋(`CT5:rel_layer.contact_flags`=L1 の前の名・`RunResult.tools`)を外し、**つなぎの台帳を HEAD のものに読み替えた** | **3 構成とも全部の系(19〜21)の指紋と全部の刻みの差の並び(6,664・15,598・17,710 件)が同じ**・final と呼数も同じ。台帳を読み替えない比べ([probe_c0.json](probe_c0.json)・§8 の直しの前の src)では、最後の 2 つの境目(`close_final`・`report`)だけが違う=日次の記録とランの結果の `bridges_count`(282 → 284)と `bridges_version`(manifest の比べと同じ差) |

## 8. 試験

- 新規 `tests/engine/tools/`(5 ファイル・61 本・4 並列で約 2 分半・slow の印なし):
  - `test_c0_tool_registry.py`(28): 欄の名と順(口の約束の 6 欄が先頭)・凍結と slots・`affects` は読み取り専用・不正な行 15 形・`KnownBy`・最初の中身 7 行(使っている 2・登録だけ 5=段 6-4)・各行の `bridge` がつなぎの台帳の active の行・`register` は足すだけ(同じ名・型の違いは落ちる・前に渡した表は変わらない)・付け替えと消去と名の無い属性と `vars()` は止まる・`known`・**書く口は `register` だけ(AST: 名を変えた slot を置くのは `__init__` と `register`・置き場の外は slot に触らない)と負の対照**・語彙の族 `道具` との結び(1-5 までのコードは動かない)。
  - `test_c0_groups_from_w16.py`(5): 合成の母集団の CSR と並び・空と片側・読み取り専用・**全母集団で行=世帯の数+事業所の数(parquet の行と値まで)**・5,000 体の抽出と先頭を切る形。
  - `test_c0_contacts_in_relations.py`(14): 写しの番号・状態台帳の行 CT5 と系の宣言(書く系は memory だけ)・`flags_from_kinds` と数え・初めの辺(世帯・職場・学校)・新しい相手と同じ相手・押し出された欄・作り直し・**印を書く口を止めた層と `rel_*` が値と型まで同じ**・**ランで印を止めても乱しても final・呼数・`rel_*` が同じ**・段 B(新しい相手の欄の印を消す差は memory に出て宣言の中/宣言を外すと memory に違反=全部の刻み・120 刻み)・世界資産 2,000 体(印=種別の写像・manifest の数・印を書く口を止めても同じ)・再開・**書く口は 1 つ(AST: 書き 10 形・差し替え 4 形・名の分からない setattr・書く口の呼び手)と負の対照 16 形**。
  - `test_c0_signboard_mark_invariance.py`(8): 口の単体(欄の値)・印とつなぎの台帳と語彙の結び(新しい欄・`via` の語は無い)・**腕の on/off で描画の全部が同じ(合成の世界 60 体と世界資産 2,000 体)・記録の行=看板の見えた描画の数・日次の記録の差は `道具:看板` だけ**・既定は書かない・出来事の記録が off なら口を作らない・decide の宣言を外すと書いた所で `PermissionError`・切替口の値の読み方。
  - `test_c0_phone_table_empty_and_declared.py`(6): 空の表と読み口・作った後は書けない・つなぎの台帳の行(2-4・`code_at`)・`osm_phone_of` の規則・記録した数を同じ規則で再現(data)・manifest の `phone_table`。
- 書く口の AST の道具 `tests/engine/tools/contacts_writers.py`(1-5 の `rights_writers.py`・1-9 の `money_writers.py` と同じ広さ=欄が 1 つなので名の表は小さい)。
- 全体(`-m "not gpu and not slow" -n 4 --dist loadfile`・data あり・作業木): **1 回目は 4,557 passed・7 failed・1 xfailed(25 分 4 秒)**。直したもの(5 件・原因 3 つ): (1) `tests/engine/rights/test_rights_schema.py::test_nothing_outside_touches_the_ledger`=1-5 の書く口の AST が、`groups.py` の slot の名 `__st` とクラスの名 `_Store`(権利台帳の中の名と同じ)を「台帳の外から触る」と数えた → slot を `__grp`・クラスを `_GroupStore` に替えた。(2) `tests/engine/test_state_checks_10f.py` の 3 本=10f の軸 1 の AST が、`record.py` の manifest の数えで `rel_layer.contact_flags`(軸 1 no)を持ち主の外で読むのを落とした → 数えを持ち主の口 `RelationLayer.contact_tally` に移し、行 CT5 の軸 1 を **diag**(読み手は manifest の数えだけ=本当の読み手に合わせた)にした。(3) `tests/engine/rights/test_rights_events.py::test_the_word_and_the_cause_name` の `V.VOCAB[-1]`(1-5 の語が末尾)→ `V.VOCAB[55]`(数と並びの固定の直し)。残り 2 件: 既知の落ち(§13)と、`tests/test_child_imports_this_tree.py`(実装役の作業の事故=`PYTHONPATH=src` を相対で渡したので子プロセスが本体の src を読んだ。印なしで回し直すと通る)。直しの後の範囲(`tests/engine/tools`・`rights`・`bridging`・`events`・`systems`・`test_state_checks_10f.py`・`test_state_ledger_10b.py`・関係の 2 本・`test_child_imports_this_tree.py`): 566 passed(8 分 27 秒)。**2 回目(最後の src・`PYTHONPATH` なし): 4,563 passed・1 failed(既知の落ち=§13)・1 xfailed(19 分 41 秒)**。
- byte-check・manifest の 7 本・系ごとの指紋(台帳を読み替えた比べ)は直しの後の最後の src で回し直した(§7)。2 日のランと読み替えない指紋の比べは直しの前の src(違いは名の替えと、軸 1 の宣言と、manifest の数えの置き場だけ=挙動とハッシュに入らない)。
- `lint-imports` は 5 契約とも守られている(208 ファイル)。秘密の走査(`tools/scan_secrets.py`・変えたファイルと新しいファイル)は CLEAN。

## 9. 共有のファイルの一覧(取り込みの rebase 用)

`engine/systems/table.py`(decide の `writes.paths` に `E:events.*`・`reads` に `fx.tools`/memory の `writes.paths` に `CT5:rel_layer._contact_flags`/report の `reads` に `fx.tools`/docstring 1 段落)・`engine/systems/decide.py`(系の終わりの 3 行と docstring)・`engine/systems/build.py`(出来事の記録の後の 4 行・`Fixtures(tools=…)`)・`engine/systems/boxes.py`(`Fixtures.tools`)・`engine/systems/state_io.py`(`rebuild_derived` の 2 行)・`engine/systems/report.py`(3 行)・`engine/run.py`(`RunResult.tools`・manifest の末尾 1 欄・docstring)・`engine/manifest_sections.py`(1 行)・`engine/state_ledger.py`(行 CT5・docstring)・`engine/relations.py`(欄・書く口・作り直し・数えの口・docstring)・`engine/events/vocab.py`(族・語・原因の名・版)・`docs/design/bridging-ledger.json`(末尾に 2 行)。凍結の表: `tests/engine/time/manifest_keys_frozen.json`・`tests/engine/events/writes_paths_events.json`。数と並びの固定: §1 の表の最後の行の 9 ファイル。`cli.py` は触っていない。

- **他の作業木とぶつかりそうな所**: manifest の末尾の並び(… → `rights` → `tools`・1-8/1-8b が欄を足すと並びの試験 5 本と凍結の鍵)・出来事の語彙の末尾と版(1-8b が語を足すと `VOCAB` の末尾の順と `events-vocab/1-x`)・decide の系の宣言(1-8 が decide を変える)と凍結の表 `writes_paths_events.json`・状態台帳の外の状態の行の末尾(`… P, CT5`)と行の数の試験。

## 10. 仮採用(回答 10-13b §0-3)

1. **看板を読んだ出来事は腕(既定 off・`SHIBUYA_TOOL_EVENTS`)**。既定で書くと manifest の日次の記録 `events` の既存の欄が動き、出来事の記録は 3 倍(5,000 体で 32,158 → 97,160 行/日)になるため。代案: 既定 on(CT の共通の決まり 5「使用は全部、出来事の記録へ」に合う)=版上げのときに親が決める(§6 の量)。
2. **出来事の形**: `what`=`道具:看板`(新しい族 `道具`=語は道具の台帳の名の写し・表の末尾)・原因=`Process("perception")`(新しい原因の名=知覚・`過程:` の語ではない)・`via`=`無し`(CT9 の 5 つの道具の外=`看板` を `via` の語に足すのは決定 CT9 (b) の拡張なので足していない)・`received_ns`=`read_ns`=その刻みの頭・1 体 1 刻み 1 行(同じ看板を続けて読んでも描画ごとに 1 行)。
3. **作り物の印の文字列** `signboard:synthetic`(発注の値)。W14 の行の無い店の合成の文(描画の「<店名>の表示。営業は…」)も作り物なので同じ印。
4. **連絡先の印の置き場=関係の記憶の層(`RelationLayer`)の SoA の外の配列**(体 × k・欄の位置は `rel_*` と同じ)。個体 SoA の列にすると `Registry` の behavior/full-hash・状態のファイル・体あたりのバイトの宣言が動くため。状態台帳の行 `CT5`=軸 1 diag(読み手は持ち主の数えの口 `contact_tally`=manifest だけ。持ち主の外で欄を読まない=10f の軸 1 の AST)・軸 2 derivable・中身は hash_skip(1-6 の M0 と同じ形)。C1 で本人が交換し始めたら behavior・required の行へ(版上げ)。
5. **手段の印の 4 つと初めの値**: 通話・メッセージ・メール・職場の連絡(R-85 §5-1 案 (a))。世帯の辺=通話・メッセージ・メール/職場の辺=それに職場の連絡/学校・常連・知人=0(決定は「家族と職場」)。手段ごとに「知っている」の錨は空欄(`HD-engine.tools.contacts-1af925f4`・外す段 6-4)。
6. **連絡先の印は関係の記憶のあるラン(`--relations on`)だけ**。既定のラン(関係なし)の manifest の `tools.contact_flags` は `null`。5,000 体の抽出では世帯の辺がほとんど無い(定員先取り層が先に入り、世帯の成員は 1〜2 人)ので、印のある辺のほぼ全部が職場(v3_mem_rel seed 1 で 5,732 本のうち職場 5,730)。
7. **グループの一覧=ランの体に成員のいる世帯と事業所だけ**(範囲の外の家族・体の無い成員は入らない=決定 CT4 の宣言)。職場=W16 の `org_id`(W6 の組織)。学校のグループは作っていない(決定は「家族と職場」)。
8. **道具の台帳の欄に足した 4 つ**(`modality`・`content_origin`・`stage`・`bridge`)と最初の中身の各欄の値(§2・未リサーチ)。掲示はカテゴリの既定の営業時間のつなぎ `W7#1` に結んだ。
9. **道具の一式の置き場=箱 `Fixtures.tools`**(組み立てで作り読むだけ=状態台帳の対象外)。manifest の `tools` は観測の節(設定の節の道筋の golden を動かさない)。
10. **状態台帳の版は上げない**(行 CT5 はハッシュにも状態のファイルにも入らない=1-3・1-6・1-9・1-2 と同じ仮採用)。
11. **外す段**: `BR-PHONE-TABLE-BLANK`=2-4(発注)・`HD-engine.tools.contacts`=6-4(C1)。どちらも `inferred`。
12. **切替口は環境変数と `set_enabled`**(`run_day` の引数・CLI にしない=設定の指紋と 1-0 の引数の数を変えない)。

## 11. 独立検収(review.md)の後の直しと取り込み(L4)

検収役の判定は条件つき受入(記録 [review.md](review.md))。親の判断で M1 と低 L1〜L3 を直し、L4 は取り込み(本体の枝への rebase)で解く。

| 項 | 直し |
|---|---|
| **M1** 書く口の AST の広さ | 書く形を見る道具を 1-5 の `rights_writers._LedgerScanner` と同じ広さにして、置き場を共通にした: `tests/engine/ast_writers.py`(`WriterScanner`=列の判定・差し替えを数える名・呼び手を数える口の名を引数で渡す)。`tests/engine/tools/contacts_writers.py` はこれを使う。広げた形: 別名を 2 回集める(別名の鎖)・`for`/内包/`with` の別名・的の `Tuple`/`List`/`Starred`(タプルの代入)・`enumerate`/`zip`/`iter`/`reversed` を通す別名・`getattr(x, 式)` は「?」・名だけで呼ぶ `copyto` など・`out=(…,)`。負の対照に検収の 7 形を足した(合わせて 23 形)。`rights_writers.py` はそのまま(取り込みの後に共通の道具へ寄せる候補) |
| **L1** 実行時の守り | 中身を `RelationLayer._contact_flags` に置き、公開の `contact_flags` は読み取り専用の view を返す property にした(口の外の `layer.contact_flags[0, 0] = 9` は `ValueError`・`layer.contact_flags = …` は `AttributeError`)。`_contact_flags` の付け替えと消去も `__setattr__`/`__delattr__` で止める(`object.__setattr__` で名を知って触る形は止まらない=1-5 と同じ Python の限界・src の中は AST が止める)。`ufunc.at` は読み取り専用を見ないので AST で見る。書くのは `_write_contacts` の中だけ。状態台帳の行 `CT5` の道筋と memory の宣言は `rel_layer._contact_flags` に替えた。試験の `noisy`・`_prefill` は書く口を通す形に直した。負の対照の試験 `test_runtime_guard_stops_writes_outside_the_writer` |
| **L2** `__init__` の呼び直し | `ToolRegistry`・`GroupList`・`PhoneTable` は、名を変えた slot が置かれた後の `__init__` を `RuntimeError` で止める。試験 `test_c0_init_recall.py`。1-5 の `Rights` は同じ形だが本段では触っていない(親の判断) |
| **L3** 店の番号の表の説明 | `places.py` の docstring・つなぎの台帳の行 `BR-PHONE-TABLE-BLANK` の `what`/`why`(道具 `add_bridges_c0.py` も)・この記録 §5 と §13 を「`w6_poi.parquet` には番号の列が無いが、元の JSON の行の並びで OSM の番号に結べる見込み(2,259 行・`phone` 477 行)=2-4 で確かめる」にそろえた |
| **L4** 取り込み | 本体の枝(1-8 の候補の口 J0 を取り込み済み)へ rebase する。予告された 14 ファイルの衝突の解き方: (a) decide の `writes.paths` の `E:events.*` と凍結の表 `writes_paths_events.json` の `decide` は 1-8 と 1-7 の両方が足した=1 つにまとめる (b) manifest の末尾の並びは … → `rights` → `decision_port` → `tools`(凍結の鍵は 1-8 の 115 に `tools` を足す・並びの試験 5 本) (c) 状態台帳の外の行は末尾(1-8 の `J0` の後に `CT5`) (d) つなぎの台帳は行を足すだけ・語彙の表は末尾に足す。(e) HEAD の行 `HD-engine.decision.layer-2d3672ba`(外す段 1-7)の扱いは、取り込みの後の結線(§12)で決める |

- **直しの後の試験**(作業木・`-m "not slow" -n 4 --dist loadfile`): `tests/engine/tools`・`tests/engine/rights`・関係の 3 本(`test_relations.py`・`_8b`・`_tenure`)・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`tests/engine/systems` で 1 回目 431 passed・3 failed(状態台帳の道筋の名を `_contact_flags` に替えた後の試験 3 本の名の直し漏れ)→ 直して 16 passed(落ちた 3 本を含むファイル)。新しい試験は 63 本(L1 の負の対照 1・L2 の 1 を足した)。`lint-imports` は 5 契約とも守られている。
- **直しの後は byte-check を回していない**(L1 は持ち主の中の名の替えと実行時の守り・L2 は組み立ての後の呼び直しの守り・L3 は文だけ=挙動とハッシュに入らない)。rebase の後に親の指示の byte-check(既定 4 構成と腕 port 2 構成)で確かめる(§12)。§7 の表の値は直しの前の src。

**取り込み(rebase)の記録(L4)**: この枝は commit を持たず、1-7 の変更は全部が作業木の未 commit の変更だった(親が commit する前)。`git rebase` は未 commit の変更があると動かないので、(1) 変えた 23 ファイルの写しと `git diff` を作業用の置き場へ控え(写しと作業木が全部同じことを確かめた)、(2) その 23 ファイルを土台の版に戻し、(3) `git rebase build/spatial-d102-prep`(commit が無いので早送り=新しい土台は `4995147`。発注の `b6f674b` の後に文書の commit が 2 つ)、(4) 控えの 23 ファイルを 3 方向で併合した(ours=控え・base=`e0865b3`・theirs=新しい HEAD・`git merge-file`)。stash も index も使っていない(`git add` はしていない)。新しいファイル(`engine/tools/` ほか)は追跡の外なのでそのまま。9 ファイルは衝突なしで併合され、14 ファイルが衝突した(予告どおり):

| ファイル | 解き方 |
|---|---|
| `src/shibuya/engine/run.py` | manifest の末尾=… → `rights` → `decision_port`(1-8)→ `tools`(1-7) |
| `src/shibuya/engine/systems/decide.py` | docstring に 1-8 J0 の段落の後ろに 1-7 の段落 |
| `src/shibuya/engine/systems/table.py` | decide の `writes.paths` の `E:events.*` は 1 つ(1-8 の ` J0:decision.* E:events.*` のまま・注に 1-7 も同じ宣言と書いた)。docstring の 1-7 の段落にも「1 つにまとめた」 |
| `src/shibuya/engine/state_ledger.py` | 行の並び=… `P` → `J0`(1-8)→ `CT5`(1-7)・docstring の行の数 194 |
| `docs/design/bridging-ledger.json` | 新しい HEAD の 286 行の後ろに 1-7 の 2 行=**288 行**(HEAD の行は 1 字も変えていない=読み直して書いた形が HEAD のファイルとバイトで同じことを確かめた) |
| `tests/engine/events/writes_paths_events.json` | `decide` は 1 回(1-8 が足した所)・注に 1-7 も同じ宣言と書いた |
| `tests/engine/time/manifest_keys_frozen.json` | 1-8 の 115 鍵の末尾に `tools`=**116 鍵**・注に 1 文 |
| manifest の並びの試験 5 本(`test_manifest_rules_bridges.py`・`test_t0_tm9_fields.py`・`test_env_and_sections_10f.py`・`test_percept_schema.py`・`test_rights_manifest.py`) | 末尾の並び … `rights` → `decision_port` → `tools`(`test_manifest_rules_bridges.py` は 1-4 の 3 欄が末尾の 5 つ前までの続き) |
| `tests/engine/bridging/test_bridging_ledger.py` | 見出し 79 → 80・ファイル 76 → 77・項 348 → 351・`HD-` の行 79 → 80 |
| `tests/engine/test_state_ledger_10b.py` | 外の状態 103 行・全体 194 行・並びの末尾 `J0`・`CT5`・両方の行の軸の検査 |

- 衝突の無かった 9 ファイル(`vocab.py`・`manifest_sections.py`・`relations.py`・`boxes.py`・`build.py`・`report.py`・`state_io.py`・`test_e_vocab_is_closed.py`・`test_rights_events.py`)も中身を読んだ(build は 1-8 の候補の口の腕の段落の前に 1-7 の道具の一式・語彙は 1-8 で変わっていない=57 語のまま・`log.py` の原因の列は `CAUSE_PROCESS_NAMES` から作るので末尾の `perception` も通る)。
- 併合の後の試験(範囲・`-m "not slow" -n 4 --dist loadfile`): `tests/engine/bridging`・`test_state_ledger_10b.py`・`test_e_writes_declared.py`・`test_e_vocab_is_closed.py`・`test_systems_table.py`・`tests/engine/tools`・manifest の並びの試験 5 本・`test_state_checks_10f.py` で **351 passed**(8 分 46 秒)。全体の試験・byte-check は §12 の後。
- HEAD の行 `HD-engine.decision.layer-2d3672ba`(外す段 1-7)は §12 の結線で removed にした。

## 12. rebase と 1-8 への結線(候補の源「周りが示すできること」を道具の台帳に結ぶ)

rebase の手順と衝突の解き方は §11 の後半(土台 `4995147`=本体 `f2405e3` と src は同じ)。ここは結線(親の指示 C)。

**結線**: 1-8 の `DecisionLayer.affordance_words`(候補の源 affordance)が、(i) 場所の種類と営業時間と知覚の読み(今のまま=世界の状態の読み=つなぎではない)に加えて、(ii) 道具の台帳から「この体が知っていて(`known_by`)・要るもの(`requires`)が満たされ・今の世界で使う段(`stage` が `None`)」の道具を、道具 → 判断の語彙の語の凍結の表 `engine.tools.registry.TOOL_ACTION_WORDS`(`MappingProxyType`・**今は空**)で語に写して足す。表が空なので候補の列は変わらない。要るものは本人の持ち物・契約・回線(`Percept.belongings`)に全部あれば満たされる=持ち物の台帳はまだ無い(空)ので、要るもののある道具は使えない扱い。台帳は組み立てが `Fixtures.tools` と同じ物(`ToolsFixture.registry`)を層に渡す(`run_day` の引数・CLI は増やしていない)。既定の腕(legacy)は層を作らないので触らない。

| ファイル | 変えた所 |
|---|---|
| `src/shibuya/engine/tools/registry.py` | `ToolRegistry.usable(agent, have)`・凍結の表 `TOOL_ACTION_WORDS`(空)・`affordance_words(registry, agent, have)`(表が空なら空の組)・docstring |
| `src/shibuya/engine/decision/layer.py` | `DecisionLayer(tools=…)`・`affordance_words` が道具の語を足す(表を呼ぶたびに読む)・docstring(場所の読みの説明を本文へ移し、expedient の見出しを書き直した) |
| `src/shibuya/engine/decision/sources.py` | docstring の源 4 の説明だけ |
| `src/shibuya/engine/systems/build.py` | 層を作るときに `tools=_tools_fx.registry`(1 行) |
| `src/shibuya/engine/state_ledger.py` | 除外の一覧の `decision` の参照に `tools`(道具の台帳=組み立ての物と同じ・状態ではない) |
| `docs/design/bridging-ledger.json` | 下の 2 行の出し入れ(道具 `tools/wire_bridges_c0.py`・`--check`) |
| `tests/engine/bridging/test_bridging_ledger.py` | `HD-` の行 80 → 81(removed を含む)・active の `HD-` は 80・旧い行が removed の検査 |
| `tests/engine/tools/test_c0_affordance_from_registry.py`(新規・8 本) | 表は空で凍結・**表が空なら層の語と候補の列が結線の前と同じ**(台帳を渡さない層と比べる単体・12 通りの文脈)・**負の対照=表に 1 語(看板 → 通報)を仮に入れると、その語の源が vocab → affordance になり affordance の候補が 1 つ増える**(語彙の外の語は足されない)・知らない体には出ない・要るものが満たされない道具は出ない(持ち物が空/半分/全部)・登録だけの段の道具は出ない・組み立てが `Fixtures.tools` と同じ台帳を渡し、台帳を渡さない層のランと番号の分布・源の分布・final・呼数が同じ(腕 port の小さなラン) |

**つなぎの台帳の行の出し入れ**(288 行 → 289 行・active は 288 のまま):
- `HD-engine.decision.layer-2d3672ba`(1-8 J0 の見出し「expedient(周りが示すできること=1-7 の道具の台帳で外す)」・外す段 1-7)を **`status: removed`** にした(`why` の末尾に「2026-10-14・第 1 期 1-7 で外した=候補の源 affordance は道具の台帳から読む形に結んだ・場所の種類と営業時間と知覚の読みは世界の状態の読み=つなぎではない」)。
- 新しい見出し「expedient(道具を使う行為の語は判断の語彙に無い=道具 → 語の表は空・6-4 C1 で語を足す)」(項 1 個)の行 **`HD-engine.decision.layer-ce06b545`** を足した(外す段 6-4・expedient・inferred)。見出しの数・ファイルの数・項の数(80・77・351)は変わらない(見出しを 1 つ替えただけ・項は 1 個のまま)。宣言と行の 1 対 1 の AST の検査は通る。

**試験**: `tests/engine/tools`・`tests/engine/decision`・`tests/engine/bridging`・`tests/engine/events`・`tests/engine/systems`・`tests/engine/time`・`tests/engine/rights`・`test_state_ledger_10b.py`・`test_env_and_sections_10f.py`・`test_state_checks_10f.py`(`-m "not slow" -n 4 --dist loadfile`): **664 passed**(7 分 48 秒)。`tests/engine/tools` は 70 本。`lint-imports` は 5 契約とも守られている。

**byte-check**(HEAD=作業木の土台 `4995147` の `git archive` の写し=本体 `f2405e3` と src は同じ・作業木=結線の後の最後の src・5,000 体・seed 1・1 日・テープつき):

| 比べ | 結果 |
|---|---|
| 既定の腕(legacy)4 構成([byte_check_c0_rebased.json](byte_check_c0_rebased.json)): `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` | **4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`) |
| 腕 port 2 構成([byte_check_c0_port.json](byte_check_c0_port.json)): `w6_v3_default`・`v3_mem_rel`(`SHIBUYA_DECISION_PORT=port`) | **2/2 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`73a78288ab5e1498`)。**候補の番号列も同じ**(道具 `tools/port_pair_c0.py`): 判断ごとの候補の (id, 源) の列・提示の番号と選んだ id・適用したコードの並びの sha が結線の前後で同じ(既定 v3 65,597 判断・記憶+関係 69,111 判断)・manifest の `decision_port` の観測の子(判断の数・源の分布・番号の分布・候補の数の分布・`mismatch`・`other`)も同じ |

- §11 の検収の直し(L1〜L3)の後の src に対する byte-check は、この 2 つが最初(既定 4 構成と腕 port 2 構成=どちらも同じ)。
- 確かめてほしいこと: (a) 判断の入力 `DecisionContext.tools`(1-8 で欄だけ・空)には道具を入れていない(候補の源だけに結んだ=拡張になるので聞く)。(b) 道具を使う行為の語(看板を読む・電話をかける)を判断の語彙に足すのは 6-4 C1(つなぎの行 `HD-engine.decision.layer-ce06b545`)。

## 13. 限界と空欄・親に確かめてほしいこと

- **看板の出来事を既定にするか**(§10 の 1): 量は §6。既定にするなら manifest の日次の記録 `events` の値が動く(版上げ)。
- **1-8 との結線**: §12 で結んだ(道具 → 語の表は空=候補は変わらない・語を足すのは 6-4 C1)。
- **持ち物と道具の状態**: `Percept.belongings`・`tool_state` は欄だけのまま(値は空)。`Tool.requires` を確かめる持ち物の台帳が無い(C0 では誰も読まない)。
- **連絡先の印の初めの値と手段の数**(§10 の 5)・学校の辺に印を付けるか。
- **店の番号の表**: `w6_poi.parquet` には OSM の番号の列が無いが、元の JSON の行の並びで OSM の番号に結べる見込み(2,259 行・`phone` 477 行)=2-4 で確かめる(§5)。結べない 68 行の扱いも 2-4。
- **範囲の外の家族**(同じ世帯で体になっていない人)と友人のグループは入っていない(C1 以降・慣らし期間)。
- 既知の落ち `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` は作業木の `data` が本体への junction であることで起きる(1-3・1-4・1-5 の記録と同じ・本体では通る)。

## 13. 親の検収(第334・Fable 5.1・rebase の後)

- 本体 `f2405e3` へ rebase(衝突なし=2-0 は tools/docs だけ)。範囲の試験 1,050 passed(6 分 32 秒)。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・既定の腕)=final 同じ・25 欄とも差なし(`parent_head_vs_c0_rebased_4cfg.json`)。rebase の前にも 4 構成で同じ(`parent_head_vs_c0_4cfg.json`)。
- 腕 port の 2 構成(`SHIBUYA_DECISION_PORT=port` を環境に置いて head と c0 の両側を回し比較)=final 同じ・差なし(`parent_head_vs_c0_port_2cfg.json`)。final は既定の腕と同一(1-8 の口は番号列が同じ設計)。環境変数が byte_check の子プロセスへ伝わったことは親では確かめていない=実装役の `port_pair_c0.py`(候補の番号列の比較・65,597/69,111 判断)と検収役の確かめを根拠にする。
- 判断: 受入。`DecisionContext.tools` は欄だけ(空)のまま=1-8 の契約どおり・値を入れるのは 6-4。仮採用 12 件+検収役の問い(看板の出来事の既定・連絡先の手段と初めの値・学校の辺・2-4 の OSM の番号・`Event.origin` の用法)は PENDING §1-1b に 1 行で。
