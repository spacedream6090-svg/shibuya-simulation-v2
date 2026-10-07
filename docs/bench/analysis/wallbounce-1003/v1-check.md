# v1 の確認 2 件とビューアの一覧(2026-10-03)

- 実行: 実行役 Opus 5.5(親の検収前)。手元のファイルの調査だけ(Web 取得なし・v1 リポは読むだけ)。
- 元: 指示書 [v2-wallbounce-decisions-2026-10-03.md](../../../design/v2-wallbounce-decisions-2026-10-03.md) §7-3 4-3・§6 ②・§10-3。
- パスはリポ相対。v1 リポ(隣のディレクトリ)は `v1:` を付ける。

## 1. v1 の 100 万人分の backstory の写し(§7-3 4-3)

**結論: 見つからない。**

### v1 の記録が言う置き場

- `v1:docs/plans/v1-inventory.md:45`: 「backstory | data/persona_backstory_v2/(サーバー側)| 99.98万人分」。
- `v1:docs/log/devlog.md:1563`〜`1580`(2026-08-24): 生成はサーバーで走った(mass 段 L2+L4+L5=933,310 人・core 段 L1+L3=66,690 人)。finals の設定で `backstory_dir=data/persona_backstory_v2`。
- 読み口は `v1:src/society/world/backstory.py:49`(BackstoryStore)。1 行の形は同ファイル冒頭の説明で `{"pid": …, "backstory": …}`(層別 JSONL、gz 可)。

### 探した場所と結果

| 場所 | 探し方 | 結果 |
|---|---|---|
| v1 の `data/`・`runs/`・`experiments/`・`ref/`・`reference/` | ファイル名に backstory・persona・bio・profile・`agents_*` | backstory は 0 件。persona の当たりは下の母集団と `personas_*.json`(40〜300 人の手作り名簿)だけ。`runs/` は分析の persona_consistency と `_profile` だけ |
| v1 リポ全体(`.git` の中も) | ファイル名に backstory | 生成スクリプト・読み口・テストの .py だけ(`scripts/build_persona_backstory.py`・`src/society/world/backstory.py`・`tests/test_backstory_build.py`・`tests/test_persona_backstory.py`) |
| v2 の `data/`・`runs/` | 同じ名前の条件 | `runs/` は無い。`data/persona_pool_v2/` だけ当たる |
| 母集団のファイル(v1 の `data/persona_pool/`・`data/persona_pool_v2/`・`data/persona_pool_v2_smoke/`、v2 の `data/persona_pool_v2/`) | 中身を `backstory` で grep | 0 件 |
| v1 リポの隣にあるバックアップのディレクトリ(リポ外・参考) | ファイル名に backstory | v1 の写し(mirror)の .py だけ。データは無い |

### 手元にある近いもの(backstory ではない)

- v2 `data/persona_pool_v2/`: 24 ファイル。meta の `total_generated` は 1,000,000(L1 30,000・L2 138,759・L3 36,690・L4 793,259・L5 1,292)。v1 の同名ディレクトリとサイズが一致する。
- 1 行のキー: age・bedtime_min・birth_year・commute・commute_mode・drive_threshold・employment・fire_weight・gender・has_bicycle・has_car・household_id・household_role・household_type・id・industry_key・industry_major・layer・name・occupation・occupation_major・persona・presence・rank・role・school_stage・sleep_steps・traits(internal_locus・nfc・risk_tolerance)・visitor・workplace_scope。
- `persona` 欄は短い 1 文(L1 の先頭 2,000 行で中央値 61 字・最大 75 字)。事前生成の backstory(過去情報)ではない。
- したがって、指示書 §7-3 4-3 の「無ければ構造化された属性だけで始める」の場合に当たる。

## 2. AB7 のテープの場所(§6 ②)

**結論: 見つかった。** v2 の `data/tape/`(gitignore 下)に、AB7 系の 5 ラン・12 腕のテープがある。書かれた日時は 2026-09-16〜09-18(サーバー返却 09-22 の前)。v1 リポには無い(`ab7`・`open_intent`・`free_intent` をファイル名で検索して、`.git/objects` の名前の偶然の一致 2 件だけ)。

### `tools/vocab/registry_from_tape.py` が期待する入力

- 引数はテープのディレクトリ 1 つ(例 `data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open`)と `--out`。中に `calls.parquet` と `blocks.parquet` が要る(`src/shibuya/engine/tape.py` の Tape で読む)。
- `calls.parquet` の列(版 2 = `shibuya.tape/2`): call_id・agent_id・tick・wake_class・prompt_hash・block_ids・params_hash・**response**・tokens_in・tokens_out・deferred・deferred_reason・observed_tick。
- 使う列: `deferred`(1 の行は分母から外す)、`response`(`parse_two_line` で読み、語彙に当たらない行だけ台帳へ)、`agent_id`・`tick`・`prompt_hash`、`block_ids`(セルの復元)。
- `blocks.parquet` の列: block_id・text・tokens。[B2 場所] の文面から正規表現 `現在地はセル(…)` でセル ID を取る。
- 出力は未定義行動台帳の JSON(`shibuya.cli.undefined_registry_payload` と同じ形)。既にある出力: `data/vocab/ab7_open_s1.json`(走査 36,868 行・語彙一致 1,991・台帳へ 34,877・保持 603 行・26 語)、`data/vocab/ab7_open_s2.json`(36,707 行・2,043・34,664・672 行・30 語)。

### 見つかったテープ

自由文の原文が入っている列は、どれも **`response`**(2 行の形: 1 行目「理由」・2 行目「行動」。AB7 の自由意図の腕では 2 行目が自由文)。繰り延べ行(deferred=1)は AB7 seed 1 の open 腕で 0 行。

| パス(リポ相対) | ファイル | サイズ(バイト) | 行数 | md5 |
|---|---|---|---|---|
| `data/tape/c8_ab7_s1/AB7-OPEN-INTENT__open/` | calls.parquet | 2,506,930 | 36,868 | 4d5b343cabafc06533e9c064677b50e2 |
| 同上 | blocks.parquet | 54,001 | 849 | 583eee6c35f26fd3d6aa4dfd63d42f10 |
| `data/tape/c8_ab7_s1/AB7-OPEN-INTENT__vocab/` | calls.parquet | 2,640,555 | 36,906 | 82df2c207a2ad268f4a544c2b83ba2e4 |
| 同上 | blocks.parquet | 54,268 | 852 | 7819b64b1e98b5bceb99a403f20fc270 |
| `data/tape/c8_ab7_s2/AB7-OPEN-INTENT__open/` | calls.parquet | 2,499,483 | 36,707 | 41c0dc2a4b8d5ac9fd7d43591a974779 |
| 同上 | blocks.parquet | 54,166 | 854 | 74339aaf3cb15a06f20d5bf40ec88efd |
| `data/tape/c8_ab7_s2/AB7-OPEN-INTENT__vocab/` | calls.parquet | 2,637,150 | 36,889 | 2876d60407cd187b6e5d70771dd10a04 |
| 同上 | blocks.parquet | 54,049 | 848 | 909c4328d60ee3524748c955247e80aa |
| `data/tape/c8_ab7b_s1/AB7b-HINT-INTENT__hint/` | calls.parquet | 2,508,242 | 36,855 | d0979f8f5fb8522459dd449a5d14d371 |
| 同上 | blocks.parquet | 54,564 | 862 | 75f358c88652c6d3305f5f1bc7103fe6 |
| `data/tape/c8_ab7b_s1/AB7b-HINT-INTENT__vocab/` | calls.parquet | 2,642,913 | 36,906 | 146d007d44a26e15b8fa8a8f596e10bc |
| 同上 | blocks.parquet | 54,268 | 852 | 7819b64b1e98b5bceb99a403f20fc270 |
| `data/tape/c8_ab7c_s1/AB7c-VOCAB-V2__open_v2/` | calls.parquet | 2,555,504 | 37,100 | b78dbeb9e5907cb18e273dffc19da2f4 |
| 同上 | blocks.parquet | 54,583 | 869 | db1a885dc3cb11217d9850806beb3e13 |
| `data/tape/c8_ab7c_s1/AB7c-VOCAB-V2__vocab_v1/` | calls.parquet | 2,644,215 | 36,906 | a4dd738bb5e012098cc6943eda1d7f30 |
| 同上 | blocks.parquet | 54,268 | 852 | 7819b64b1e98b5bceb99a403f20fc270 |
| `data/tape/c8_ab7c_s1/AB7c-VOCAB-V2__vocab_v2/` | calls.parquet | 2,467,679 | 37,165 | 0b7b045b5c6d0a7cbd418d8eff96b3d8 |
| 同上 | blocks.parquet | 55,534 | 898 | 40f5acf0dd23a92aa236d6c1896ffbc3 |
| `data/tape/c8_ab7c_s2/AB7c-VOCAB-V2__open_v2/` | calls.parquet | 2,549,307 | 37,125 | da9d72a9153f0c09c7a54b12cabe1455 |
| 同上 | blocks.parquet | 54,590 | 871 | 1767dc4a89ded77a031f766bc89300c9 |
| `data/tape/c8_ab7c_s2/AB7c-VOCAB-V2__vocab_v1/` | calls.parquet | 2,624,307 | 36,889 | a73e55be4182874d96ba1efa69bb2ab8 |
| 同上 | blocks.parquet | 54,049 | 848 | 909c4328d60ee3524748c955247e80aa |
| `data/tape/c8_ab7c_s2/AB7c-VOCAB-V2__vocab_v2/` | calls.parquet | 2,491,412 | 37,371 | 9ce0aa79fc0ad4a610a06ef0dbd9448e |
| 同上 | blocks.parquet | 55,130 | 883 | 36ce6a0756010deb198b44b379873b45 |

- 自由意図の腕は `__open`(AB7 seed 1・2)と `__open_v2`(AB7c seed 1・2)。`__hint`(AB7b)は「列挙から 1 語、無ければ 10 字以内の動詞句」の腕(`docs/bench/c8/ablation/ab7b_s1_parent_report.md:3`)。`__vocab*` は語彙から選ぶ対照。
- `blocks.parquet` の md5 が腕どうしで一致するもの(7819b6…・909c43…)がある。共有ブロックが内容アドレスなので、同じ条件の対照の腕なら同じになりうる。
- 各ランの親報告とランナーのログは `docs/bench/c8/ablation/`(`ab7_s1_parent_report.md` ほか)。

## 3. v1 の `viz/` の一覧(§10-3 の下準備・行数だけ)

v1 リポで `wc -l`。「管理」は git の追跡の有無。中身の分析はしていない。

| ファイル(v1 リポ相対) | 行数 | サイズ(バイト) | 管理 |
|---|---|---|---|
| `viz/make_viewer.py` | 4,942 | 299,328 | 追跡 |
| `viz/make_viewer3d.py` | 2,716 | 150,563 | 追跡 |
| `viz/make_hub.py` | 321 | 13,025 | 追跡 |
| `viz/notable_events.py` | 453 | 23,114 | 追跡 |
| `viz/feed_rank.py` | 377 | 18,482 | 追跡 |
| `viz/render_pov.py` | 166 | 7,234 | 追跡 |
| `viz/sfm.py` | 44 | 1,862 | 追跡 |
| `viz/blender_import.py` | 492 | 19,824 | 追跡 |
| `viz/unreal/import_shibuya_sim.py` | 301 | 13,604 | 追跡 |
| `viz/unreal/README_UE.md` | 228 | 13,429 | 追跡 |
| `viz/unreal/SimReplayActor_DESIGN.md` | 182 | 9,574 | 追跡 |
| `viz/vendor/three.min.js` | 6 | 603,445 | 追跡(外部ライブラリ) |
| `viz/vendor/OrbitControls.js` | 1,045 | 26,375 | 追跡(外部ライブラリ) |
| `viz/chronicle/chronicle.html` | 2,406 | 10,642,781 | 追跡外(生成物。`v1:.gitignore:35`〜`36`) |
| `viz/chronicle/data/` | 4 ファイル | 約 4.6 MB | 追跡外 |
| `viz/points_viewer.html` | 0(改行なし) | 12,977,837 | 追跡外 |
| `viz/viewer3d_runB/viewer3d.html` | 2,090 | 53,976,177 | 追跡外 |
| `viz/viewer3d_runB/tracks_bin/` | 32 ファイル | 約 285 MB | 追跡外 |

ビューアに関わる `viz/` の外のもの:

| ファイル(v1 リポ相対) | 行数 | サイズ(バイト) |
|---|---|---|
| `scripts/build_chronicle.py`(Chronicle の生成) | 6,617 | 330,890 |
| `scripts/export_3d.py` | 1,584 | 82,640 |
| `scripts/export_ue.py` | 274 | 12,323 |
| `scripts/live_viewer.py` | 1,326 | 69,351 |
