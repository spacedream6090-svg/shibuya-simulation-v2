# 第 2 期 2-0 較正側の錨の計器: 検収の記録

- 検収役: Opus 5.5(2026-10-14)。実装は見ていない。作業木と本体は読むだけで、書いたのは本書 1 本だけ。commit・子サブ・ネットワーク・taskkill は使っていない。
- 対象: 作業木(枝 `2-0/instrument`・HEAD `2bc7a4b`)の未 commit の 8 ファイル。計器 `tools/instruments/anchor_gauge.py`・`read_guard.py`、試験 `tests/tools/test_anchor_gauge.py`、記録 `gauge20/README.md`、`docs/bench/instruments/anchor_gauge/` の `calib_anchors_v0.json`・`preregistration_v1_4_draft.md`・`2026-10-14_2bc7a4b/anchor_gauge.{json,md}`。
- 正: 発注文、R-115 §2〜§5、回答 10-13b §1 1-1・§0-3。

## 判定

**条件つき受入**。欠陥は高 0・中 1・低 10。

- エンジン不変と封印の守りは確かめられた。
- 4 つの量のうち 3-2 と 3-4 を計器のコードを使わずに再計算し、記録の値と一致した(3-1 のピークも一致)。
- 受入の条件は 3 つ。中 1(記録の宣言の抜け)と、ユーザーに見せる草案と記録の数の誤り 2 件(低 1・低 2)を直すこと。ほかの低は任意。

## 1. エンジン不変 ✓

- `git diff --stat -- src` は空。`git status --porcelain --untracked-files=all -- src` も 0 行。
- 包みの関数を読んだ(`anchor_gauge.py` :337-361、`tools/c7/attr_arms.py` :263-287)。
  - `_init` は元の `__init__` を呼んでから参照を控えるだけで、戻り値は None のまま。
  - `_pop` は元の `_resolve_population` の戻り値をそのまま返す。
  - `AgentCellRecorder` の包みは元の `apply` の戻り値を返し、cell・transit_state・kind を copy で控えるだけ。
  - 3 つとも `finally` で元に戻す。
- 自分で回したラン(5,000 体・seed 1・1 日):

| ラン | src | final | 呼数 |
|---|---|---|---|
| 計器の `record --arm mock`(記録器あり) | 作業木(`src_is_worktree` 真) | `5f7ae9ff24005314` | 65,597 |
| 計器の `record --arm mock --no-recorder` | 作業木 | `5f7ae9ff24005314` | 65,597 |
| 本体 HEAD の `cli.run`(包みなし・守りなし・vocab v3) | 本体 | `5f7ae9ff24005314` | 65,597 |
| j0 の既定 v3(`j0/arm_pair_j0.json`) | — | `5f7ae9ff24005314` | 65,597 |
| 計器の `record --arm classical`(記録器あり) | 作業木 | `202a05a22c5bd8e1` | 93,460 |
| 本体 HEAD の `cli.run`(classical・包みなし) | 本体 | `202a05a22c5bd8e1` | 93,460 |

- 本体 HEAD は `b6f674b` で、`2bc7a4b` との差は文書だけ(src と tools の差は 0)。
- 自分の 2 本の journal で gauge の段を回し直した。記録の json と全部の値が一致し、違いは journal のバイト数と md5 だけだった(低 10)。

## 2. 封印の守り ✓(抜け道の宣言を足す)

**(a) 計器が実際に開いたファイル**

自前の監査フックを足して gauge の段を回し、Python の open を全部控えた。

- data・docs・tools の下で開いたのは、記録の md5 の表にある 34 本(W16・W16_chome・W2_cells・W12 の 2 本・area_axes・time_dist_12・commute_r3・ssb_8_1・calib_anchors・pool 22 本・journal 2 本)と、書き出しの 2 本だけだった。
- pyarrow の読みは監査に出ない。ただし計器が md5 を取るときに Python の open で開くので、parquet の 5 本も控えに出た。
- 34 本はどれも R-115 §2 の〔写〕〔部〕〔非〕に当たる構築側である。

**(b) 負の対照**

- 試験にあるもの: `kddi_la`(check・read_bytes・一覧の組み立て)、`shibuya_jinryu`(組み立て・監査の open)、`presence_anchors`・`diversity_anchors`・`hunger_energy_anchors`・`boundary_counts.json`・`pt6_c-2.csv`(check)。
- 試験に無いもの: `data/realworld_live/`。
- 自分でも、作業用の場所に偽の写し(中身は `{}`)を置いて 51 本の負の対照を回した。**51/51 が落ちた**。
  - 計器の一覧で check・read_json・open × 7 種の名(`kddi_la`・`presence_anchors_v0.json`・`shibuya_jinryu`・`boundary_counts.json`・`realworld_live`・`pt6_c-2.csv`・`diversity_anchors_v0.json`)。
  - 役割の差し替え(time_dist_12・commute_r3・calib_anchors の道筋に 4 種の封印の名)。
  - journal・`--compare` のフォルダ・pool・世界の置き場に封印の名。
  - ランの段の守り(`sealed_only`)で open × 5 種。
- `sealed_only` は `presence_anchors` を落とさない。エンジンのランを計器の一覧で縛らない設計どおりである。

**(c) 監査フックの抜け道**(偽のファイルで確かめた)

- 落ちる(open の監査イベントが出る): `builtins.open`・`os.open`・`io.FileIO`・`io.open_code`・`Path.read_bytes`/`read_text`・`json.load(open(...))`・`gzip.open`・`numpy.load`・`numpy.fromfile`・`numpy.loadtxt`・`shutil.copyfile`。8.3 の短い名(`SHIBUY~1` のように語が消える名でも、実体の名で判定する)と junction 越しも落ちる。
- 落ちない(抜け道):
  - pyarrow(`parquet.read_table`・`pyarrow.fs`)。pandas は venv に無いが、`pandas.read_parquet` も pyarrow 経由なので同じ。
  - `sqlite3`。
  - `subprocess`(外のコマンドで読む)。
  - `os.listdir`・`os.scandir`(名だけ)。
  - hard link(一覧にある名で、実体が別のファイル)。
- 計器の gauge の段がこのうち使うのは pyarrow だけで、読み口の検査(`read_parquet`)と md5 の open の両方で縛られている。sqlite3 は使っていない。subprocess は record と run の段の git と子プロセスだけ。README §6-10 の宣言は pyarrow だけなので、ほかを足す(低 7)。

**(d) 落とす語**

- 封印の語(ランの段でも落とす): `kddi`・`jinryu`・`boundary_counts`・`realworld_live`・`/holdout/`・`holdout_compare`・`calib/pt2018`・`pt6_c-2`・`pt6_b-4`・`pt6_c-3`・`pt6_c-4`。
- 計器の段で足す語: `diversity_anchors`・`presence_anchors`・`hunger_energy_anchors`・`calib/hunger`・`000032224420`(第 30 表)・`research_cache/r99`(第 14・15 表)・`line_capacity_12`・`transfer_12`・`station_od13_13`・`station_flow_12`。
- `pt_area` は入っていない。ただし `pt_area_daytime_peak` はファイルの中の鍵の名で、計器はファイル `presence_anchors_v0.json` を丸ごと落とすので要らない。`boundary` は `boundary_counts` の形で入っている。
- 守る根(data・docs・世界資産・プール)の下は、一覧の外を開けない。語は二重目の守りである。

## 3. 4 つの量の式 ✓(違いの一覧)

**R-115 §3・§4 と計器の違い**

1. 3-1 錨 1: R-115 は「正時 h にブロックの中にいる体の数」(正時の標本)と書く。計器はランと同じ v1.4 の数え方(1 日の合計 30 分と、時間帯に θ 分)を計画のセルに当てた。計画の正時の列は無く、README §2 :61 もこの違いを書いていない(低 3)。
2. 3-1 錨 1: 自宅の行も home_cell で補う(R-115 は職場と学校だけ)。宣言あり。
3. 3-1 錨 2: R は P′ の居住者(kind 2・3)、I と O は全年齢・全種別の流量。宣言あり(I と O に年齢の軸が無い)。
4. 重み: R-115 §3-0 の w_k は割合の比、計器の ω_k = N_k/n_k はそれに N/n(=78.0)を掛けた拡大係数。比とピーク時刻は変わらず、水準だけが W16 の規模になる。宣言あり。
5. 母集団: P′ を本則、P と全員を腕にした。発注どおりで、10-13b 1-1 の文言(kind 7)とのずれは README §6-1 に宣言がある。
6. 30 分の数え方は合計が本則・連続が腕、θ は 1 刻みが既定・30 分が腕で、どちらも R-115 §4 どおり。ただし `presence_hourly`(:569-574)は θ を刻みの数としてそのまま比べる。`daily_qualified` は秒から刻みへ直している。刻みが 60 秒の今は結果が同じ(低 4)。
7. 24〜28 時は `HOUR_IDX = h % 24` で同じ日の 0〜4 時に代える。試験もある。KDDI の 24 区分も R-115 どおり。
8. 3-3: 到着は transit_state が 1(乗車中)か 2(域外)から 0 に変わった刻み。舞台の中で乗って舞台の中で降りる体が居れば、それも到着に数える。量は小さい見込みだが、未確認。
9. 3-4: 対象に P′ と `work_cell ≠ home_cell` を足した。宣言あり。錨 3 の立ち上がりは「最大の 50% 以上」で、R-115 の「超える」と違う。今の値では「超える」でも同じ 8:30。

**草案 `preregistration_v1_4_draft.md` と計器**

- 母集団・属性・滞在・時間帯・時刻・ピークの順・比の定義は、計器の関数と同じだった。
- §1 :17 の「P と P′ の差は 5,315 体」は誤り。P と P′ はどちらも 20 歳以上なので、差は 5,268 体である。5,315 は全年齢の数で、うち 47 体が 20 歳未満(低 2)。
- §7 の「ピークの順=ピーク時刻の昇順」は計器と同じ。ただし記録の md と README §4 :126 は `>` でつなぐので、「大きい順」に読める(低 5)。

## 4. 独立の再計算(3-2・3-4) ✓

**方法**

- 計器のコードは使わずに書き直した。共有したのは入力と、セル → 5 エリアの写像(`c7lib.build_area_map`=計器の外の既存の道具)だけ。
- 入力は自分の journal(1 で記録と全部の値が一致)と W16 の parquet。
- 3-2: 体 × エリアの合計の分を bincount で数え、30 分以上 × P′ × area の属性(自宅が先・次に職場と学校)× ω_k で和を取った。
- 3-4: 対象(kind 0・2・P′・work_cell ≥ 0 かつ ≠ home_cell)ごとに、職場のセルに居る刻みの連続(run-length)を取った。0 刻み目から始まらない最初の 30 分以上の区間の始まりを取り、ω で重みを付けた平均と、下側の重みつき中央値を出した。

**結果**

| 量 | mock 再計算 | mock 記録 | classical 再計算 | classical 記録 |
|---|---|---|---|---|
| 3-2 5 エリアの和 V/Res | 34.944 | 34.94 | 30.000 | 30.0 |
| 3-2 5 エリアの和 W/Res | 9.700 | 9.70 | 16.050 | 16.05 |
| 3-2 エリアごとの件数 n(W・Res・V) | 一致 | — | 一致 | — |
| 3-2 W・Res・V の差の最大 | 0.044 | (記録は小数 1 桁) | 0.044 | (同) |
| 3-4 対象・始まりが取れた体 | 2,346・852 | 2,346・852 | 2,346・2,252 | 2,346・2,252 |
| 3-4 平均 | 783.21 分(13:03) | 783.21 | 604.96 分(10:05) | 604.96 |
| 3-4 p50 | 726 分(12:06) | 726 | 569 分(9:29) | 569 |
| 3-4 :00/:30 の率 | 0.0446 | 0.0446 | 0.0315 | 0.0315 |
| 3-4 最頻の 15 分 | 9:30 | 9:30 | 8:45 | 8:45 |

- 3-1 のピーク(ランと計画 × 7 列 × 2 腕)も同じ書き直しで数え、全部一致した。

## 5. 錨の値の写し検査 ✓

構築側の原典から読み直した。検証側のファイルは開いていない。

| 錨 | 原典 | 読み直した値 | 記録 |
|---|---|---|---|
| 3-2 錨 1 W16 kind の写像 P′ | `w16_population.parquet` | W 210,402・Res 37,836・V 83,072・V/Res 2.1956・W/Res 5.5609 | 同じ |
| 同 P | 同 | V 88,340・V/Res 2.3348・W/Res 5.5609(R-115 の 2.33・5.56) | 同じ |
| 同 全員 | 同 | W 217,054・Res 43,622・V 129,391・V/Res 2.9662 | 同じ |
| 3-2 錨 1 area の写像 W/Res(P′) | 同+`w2_cells`+`area_axes_v0.json` | 18.62・20.69・11.28・28.34・10.82・計 16.40(Res 11,027・W 180,812) | 同じ |
| 3-2 錨 3 中核 9 | `calib_anchors_v0.json` | 130,167 ÷ 8,810 = 14.775 → 14.8(d66 :278 と R-115 §2 の値とも同じ) | 14.8 |
| 同 W16 の夜 | `w16_population`+`w16_chome` | 8,524 | 8,524 |
| 3-3 錨 1 線の割合 | `w12_external_nodes.parquet` | 10 ノードの割合の差の最大 0 | — |
| 3-3 錨 2 時刻の形のピーク | `w12_generation_weights.parquet` | 鉄道 8 線 8 時・徒歩 10 時・道路 8 時 | 同じ |
| 3-1 錨 2 R・I・O とピーク | W16・W12・`time_dist_12.json`(帰宅・乗車) | 37,836・1,521,476・1,483,785・13 時 | 同じ |
| 3-4 錨 3 第 8-1 表 | `ssb2021_activity_prior_v0.json`(平日・03・有業の男女・年齢総数・05) | 立ち上がり 8:30(最大 69.0%) | 8:30 |
| 3-4 錨 2 W17 v2 の勤務の行 | `w17_schedule.parquet`(d0・勤務・start > 0 の最小) | n 2,336・平均 554.96(9:15)・p50 520(8:40)・0.0463 | 同じ |
| 3-4 錨 1 第 31 表+arrival_lead | `w17v2/w17v2_stage2_prompts.jsonl` の「勤務: 場所 曜日 HHMM-HHMM」(月か毎日) | n 1,939・平均 543.71(9:04)・p50 517(8:37)・0.0289。窓の始まりは対象 2,332 体の全員で一致 | 同じ |
| 3-1 錨 1 計画上のセル | `w17_schedule.parquet`(行 → セルの補い) | ブロックの中の 3,215,684 刻みのうち、W17 の行がある刻みは全部一致。食い違いの 1,320 刻みは、3 体の W17 の行の切れ目(行が無い分を計器は「舞台の中・セル不明」とする=設計どおり) | — |

## 6. 試験 ✓

- `tests/tools/test_anchor_gauge.py`(`-m "not slow"`): **18 passed**(2.3 秒)。
- `tests/tools tests/c7`(`-m "not slow"`): **215 passed**(4.1 秒)。
- data の無い写し(作業木の HEAD の src・tools・tests に新しい 4 ファイルを足し、data は置かない)で、`test_anchor_gauge.py` を slow も含めて回した: **17 passed・2 skipped**(`requires_data: world_v2 が無い`)。CI-1(`-m "not gpu and not slow"`)では 17 本が回り、1 本が飛ぶ。
- `requires_data` の仕組みは環境変数ではなく、`tests/_data_ids.py` の登録表で置き場のファイルがあるかを見る。印は正しく効いた。ただし実データの 2 本(:463・:490)は `data/realworld/transport_census/time_dist_12.json` も読むのに、印は `world_v2`(と `persona_pool`)だけ(低 6)。
- slow の 1 本は回していない。同じ中身(記録器の有無で final と呼数が同じ)は 1 で手で確かめた。

## 7. `--compare` ✓

- 記録のフォルダの写しを 2 つ作り、`compare --prev A --cur B` を回した: 要約の値 156 件のうち、変わったのは 0 件。
- 自分の journal で `gauge --compare <記録の写し>` を回した: 156 件のうち 0 件。差の表(`compare_vs_*.md`)は出る。差が 0 のときは見出しだけの空の表になる(見た目だけの話)。

## 8. 記録 ✓(中 1 を除く)

- 新しい 8 ファイルに、絶対パス・ホスト名・個人名は無い。grep の当たりは `calib_anchors_v0.json` の出典の https の URL だけ。`tools/scan_secrets.py` は CLEAN、CR は 0。
- json の道筋は全部相対。作業用の場所の journal は名だけで、out はリポからの相対。
- 「読んだファイルの一覧」は、2 (a) の監査の控え(gauge の段)と一致した。
- ただし record の段(エンジンのラン)が開くファイルは、記録のどこにも書いていない。自分で控えると、Python の open で 20 本(世界資産・暦・OSM・規則表・つなぎの台帳など)を開き、その中に `docs/bench/anchors/hunger_energy_anchors_v0.json` がある。計器の gauge の段は、このファイルを「第 4-1・7-1・18-1 表の検証の行が混ざる」として落とす語に入れている(中 1)。

## 欠陥

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `gauge20/README.md` §3・`anchor_gauge.md` :3(`anchor_gauge.py` :1357) | record の段では、エンジンが `hunger_energy_anchors_v0.json`(〔検〕の行が混ざるファイル)を開く。md の冒頭の「検証側と〔灰〕は許可の一覧で縛って読んでいない」が当たるのは gauge の段だけ。エンジンが前から読んでいるファイルで、計器が足した露出ではない | README §3 と md の冒頭に「ランの段はエンジンが既存の入力を読む(`hunger_energy_anchors_v0.json` を含む・計器はその値を使わない)」と書く。できれば record の meta に、ランの間に開いたファイルの一覧(道筋だけ)を残す |
| L1 | 低 | `gauge20/README.md` :136 | 「P 2.34」は 2.3348 を 2 回丸めた値で、正しくは 2.33 | 2.33 に直す |
| L2 | 低 | `preregistration_v1_4_draft.md` :17 | 「P と P′ の差は 5,315 体」は全年齢の数。20 歳以上では 5,268 体 | 「5,268 体(全年齢では 5,315)」に直す |
| L3 | 低 | `gauge20/README.md` :61・`anchor_gauge.py` `gauge_arm` | 計画の在圏を v1.4 の数え方で出しており、R-115 の「正時の標本」と違う。記録に書いていない | 違いを記録に書く。計画の正時の列(`plan/on_hour`)を足せば R-115 の形とも比べられる |
| L4 | 低 | `anchor_gauge.py` :569-574 | θ を刻みの数としてそのまま比べる。刻みが 60 秒でないと θ の分がずれる | θ を `ceil(θ·60/tick_seconds)` の刻みに直して比べる |
| L5 | 低 | `anchor_gauge.py` :1408・`gauge20/README.md` :126 | ピークの順を `>` でつなぐが、中身は早い順 | 「早い順」と書くか `→` でつなぐ |
| L6 | 低 | `test_anchor_gauge.py` :463・:490 | `time_dist_12.json` を読むのに、`requires_data` の印に無い | 印に `"realworld:transport_census/time_dist_12.json"` を足す |
| L7 | 低 | `gauge20/README.md` §6 :186 | 監査フックの抜け道の宣言が pyarrow だけ | sqlite3・subprocess・ほかの C 拡張の読み・hard link を足す(gauge の段は使っていない) |
| L8 | 低 | `read_guard.py` :93-100・`test_anchor_gauge.py` :374-380 | `deny_hit` は語を照らす前に必ず realpath を取る。試験が本物の `boundary_counts.json`・`presence_anchors_v0.json`・`pt6_c-2.csv` などの道筋に check をかけるので、realpath がそのファイルに属性だけの handle を開く(中身は読まない) | 生の道筋で語が当たったら realpath を取らずに落とす。試験は tmp_path の偽物で行う |
| L9 | 低 | `anchor_gauge.py` `make_guard`(out・prev のフォルダ) | out と `--compare` のフォルダは、どこを渡してもその下を全部許す。守る根を渡すと根の下が開けてしまう(誤用の場合) | out と prev は、守る根の外か `docs/bench/instruments/anchor_gauge/` の下に限る |
| L10 | 低 | 記録の journal の md5 | meta に壁時計が入るので、同じランでも md5 が変わる(今回は 3〜4 バイトの差)。同じファイルかの印にはなるが、再現の確かめには使えない | 配列だけの hash を別の欄に残す |

## 親に確かめてほしいこと

1. **検収の手順 6 の `tests/c7` は `presence_anchors_v0.json` を読み込む**。`tests/c7/test_presence_yardstick.py` の fixture(:21・:39-40)が `presence_yardstick.load_anchors()` を呼ぶためである。指示どおり回したので、試験のプロセスの中でこのファイルが開かれた。値は出力に出ておらず、私は値を見ていない。実装役も同じ試験を回している(README §7 の 215 passed)。今後の検収の指示から外すか、その試験を `--deselect` にするかを決めてほしい。
2. 中核 9 の値の写しを確かめるため、`docs/research` と `docs/design` の md を `130,167` で grep した。そのとき `docs/research/v2-d66-outside-residents-research.md` :292 の 1 行が出力に出て、PT 由来の滞留の数(〔灰〕の `pt_area_daytime_peak` と同じ種類の量)が目に入った。どの確かめにも使っていない。R-115 §5 主張 3 と同じ「目に触れた」の宣言として残す。
3. M1 で挙げた、エンジンが `hunger_energy_anchors_v0.json` を読むことは、計器の外の既存の挙動(K6 (i))である。計器の記録でどう宣言するかを決めてほしい。
4. P′ を本則にする仮採用(10-13b 1-1 の文言は kind 7)のユーザー確認(README §6-1 のとおり)。
5. R-115 §2 は `time_dist_12` を〔部〕とする。一方、封印 `boundary_counts` の `n_by_source` には time_dist 228 行(同じ元)がある。W12 の構築は乗車と降車の両方の行を使う(`w12_external_nodes.py` :380-381)ので、計器が 3-1 錨 2 の β に乗車の行を使っても〔写〕〔部〕の扱いと矛盾しないと読んだ。親の区分で確かめてほしい。

## 読んだもの・読んでいないもの

- 自分では開いていない: `data/realworld/kddi_la/`・`shibuya_jinryu`・`boundary_counts.json`・`data/realworld_live/`・`data/calib/pt2018/`・`presence_anchors_v0.json`(親に確かめてほしいことの 1 の試験のプロセスを除く)・`diversity_anchors_v0.json`・`hunger_energy_anchors_v0.json`(エンジンのランが開く=M1)・第 30・14・15 表。
- 読んだ構築側: `data/world/v2` の W2・W12 の 2 本・W16・W16_chome・`w17_schedule.parquet`・`W17.header.json`・`w17v2/w17v2_stage2_prompts.jsonl`(対象の体の行の user 欄)・`data/persona_pool_v2`(計器の中で)・`time_dist_12.json`・`commute_time_dist_r3.json`・`ssb2021_activity_prior_v0.json`・`calib_anchors_v0.json`・`tools/c7/area_axes_v0.json`・`j0/arm_pair_j0.json`。
- 負の対照と抜け道の確かめには、作業用の場所に作った偽のファイル(`{}` など)だけを使った。
- 作業用の場所に置いたもの: journal 3 本・確かめの Python 10 本・偽のファイル・data の無い写し。作業木と本体に書いたのは本書だけ(git status と find で確かめた。gitignore の `__pycache__` は除く)。
