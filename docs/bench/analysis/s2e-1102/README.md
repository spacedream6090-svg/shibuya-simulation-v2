# 11-02r §1 #7・#6 「無い」の過程 5 件を止める小さな版上げと、循環の CI を 2 段に(s2e-1102)

> 実行役(Opus 5.5)の記録。作業木の枝 `stage/s2e-absent-ci-1102`(土台 `b593b57`=`build/spatial-d102-prep`)。commit は親。
> 正: [指示書 11-02 返事その 2](../../../design/prompt-2026-11-02-reply2.md) §1 #6・#7・§2-2(時間の方針)・[回答 11-01](../../../design/v2-answers-2026-11-01.md) §2・§3・§10-3・[回答 10-13b](../../../design/v2-answers-2026-10-13b.md) §0-6・§0-7。手順の見本は [s2-rates-1101](../s2-rates-1101/README.md)(率の規則の小さな版上げ)と [s2-ledger-1101](../s2-ledger-1101/README.md)(台帳の欄と循環の検査)。
> 測った機械: Windows 11・x86-64・論理 CPU 20。比べたランは mock・5,000 体・seed 1・1 シミュ日・CLI の既定(`--llm mock` だけ)。絶対パス・ホスト名・個人名は書かない。

## 0. 結論

- 「無い」と宣言していながらエンジンがまだ動かしていた世界過程 5 件(ごみ収集・街路の清掃・道路工事・救急と警察の出動・電気と水の負荷)を、**既定で止めた**。旧道は切替口 `--absent-processes {stopped,legacy}`(環境変数 `SHIBUYA_ABSENT_PROCESSES`・既定 `stopped`)で 1 版だけ残した。形は `--rate-rules` と同じにした(腕は組み立てで 1 回読む・設定の指紋に入れない・manifest の節と状態の見出しに出す・再開で腕が違えば止める・既定と違えばランの種類は arm)。
- 計器 `tools/instruments/absent_declarations.py` で、5 件が「止めた」側へ移ったことを確かめた(止めた 20・まだ動く 6 → 止めた 25・まだ動く 1=納品だけ)。
- **5,000 体 × 1 日の final と呼数は、土台・stopped・legacy の 3 本とも同じ**(`73aa01d9afb206d0`・61,066)。止めた 5 件の出力は、既定の腕では behavior-hash の材料にも起床の材料にも入っていなかった(ごみもポイ捨ても倒れる人も既定では無い・工事の占用は「記録のみ」・電気と水は報告だけ)。変わったのは過程の件数・ActualLog の行(25,276 → 25,264=工事の 12 行)・manifest の節。**golden は 1 本も動かなかった**(§5)。
- **legacy は前の版と 1 バイトも変わらない**: final・呼数・過程の件数・廃棄の射影が土台と一致した。率の規則も旧道にした組み合わせも、土台の `--rate-rules legacy` と一致した(final `7bfe215641b792ac`・呼数 62,176)。
- 正しい不合格(11-02r #7)は、率の規則を旧道にした組み合わせで数として見える。街路に残るごみは 59,747 g → 141,743 g(掃いた量 0)、倒れた 5 人のうち運ばれた人は 5 → 0、店のビンの収集は 910,750 g → 0(§3-2)。この組み合わせでは final が動く(`c090385d84cbcf4d`・呼数 61,997=警察の到着の顕著行為 5 件が無くなった)。
- 循環の CI を 2 段にした(11-02r #6): **宣言の無い重なり=落とす/宣言つき(既知の循環・外す段つき)=警告**。宣言の表は `src/shibuya/world/processes/circularity.py` の `KNOWN_CIRCULARITIES`(9 件=主体 15)。D5′ は検証へ移して `burned`(今は入力と重なるので採点できない)と宣言した。E5 は検証へ移して既知の循環と宣言した(ユーザー決定)。外す段「配送の入荷が店の発注と配達員の行動になる段」は親の案(第342)=`basis=inferred`(〔検収 中-2〕)。

## §1 変えたファイルと行

| ファイル | 変えたところ(行は作業木の今の版) |
|---|---|
| `src/shibuya/engine/absent_processes.py`(新) | 切替口の本体。`MODES`・`DEFAULT_MODE=stopped`・`PROCESSES`(5 件)・`STOPPED_PROCESSES`(実行器の名・台帳の id・absent の id・止めたもの・止めないもの・検証に残す錨)・`arm`/`set_arm`/`resolve`/`is_legacy`・`stopped_flags`・`manifest_fields`・`header_fields`・`check_resume` |
| `src/shibuya/engine/processes/goods_flow.py` | import `:54`・docstring の expedient の項 2 つに注(`:35-36`・`:42-43`=項の数は不変)・`WasteCollectionProcess` の引数 `:495`・属性 `:507`・**止める所 `:535-536`**・計器 `:671-672`・`StreetCleaningProcess` の引数 `:697`・属性 `:704`・**止める所 `:723-724`**・計器 `:743-744` |
| `src/shibuya/engine/processes/logistics.py` | import `:31`・docstring の項に注 `:20-21`・`RoadWorksProcess` の引数 `:301`・属性 `:307-309`・**止める所 `:346-347`**・計器 `:375-376` |
| `src/shibuya/engine/processes/civic.py` | import `:38`・docstring の項に注 `:20-21`・`:24-25`・`PublicServiceDispatchProcess` の引数 `:129`・属性 `:136-137`・`request` の docstring と**止める所 `:155-163`**・計器 `:227-228`・`InfraLoadProcess` の引数 `:427-428`・属性 `:432-433`・**止める所 `:442-443`**・計器 `:454-457`(山の時は止めた腕で −1)・要約 `:461-462` |
| `src/shibuya/engine/processes/runner.py` | import `:34`・docstring `:139-140`・引数 `:182`・属性 `:207-209`・5 過程へ渡す `:274`・`:277`・`:301`・`:308`・`:318` |
| `src/shibuya/engine/systems/boxes.py` | `RunConfig.absent_processes`(既定 "stopped")`:188-190` |
| `src/shibuya/engine/systems/build.py` | 再開の突き合わせ `:430-433`・組み立てで腕を読む `:793-795`・実行器へ `:824`・`RunConfig` へ `:1573` |
| `src/shibuya/engine/systems/report.py` | manifest の節 `:404-406` |
| `src/shibuya/engine/systems/state_io.py` | 状態の見出し(stopped のランだけ書く)`:428-433` |
| `src/shibuya/engine/systems/table.py` | 系の `reads` に `cfg.absent_processes`(`:478`・`:495`・`:517`・`:542`) |
| `src/shibuya/engine/run.py` | `RunResult.absent_processes` `:822-823`・manifest の末尾の鍵 `:1469-1472` |
| `src/shibuya/engine/manifest_sections.py` | `absent_processes` の節(設定=schema・mode・processes・stopped/観測=counts)`:222-223` |
| `src/shibuya/engine/state_ledger.py` | 属性 `absent_processes` を設定(CONST)に分類(runner・dispatch・infra・waste・street_cleaning・road_works=`:1791`・`:1800`・`:1814`・`:1839`・`:1843`・`:1853`) |
| `src/shibuya/cli.py` | ランの種類の判定 `:486`・`:507`・旗 `--absent-processes` `:978-986`・腕を選ぶ `:1622-1625` |
| `src/shibuya/world/processes/absent.py` | 5 件の `engine_stopped=True`・`engine_now` を `_ABSENT_OFF` の文に・ごみ収集と電気と水の `stage` を `next-bump`(DEC の行と同じ)・docstring・使わなくなった `_ENGINE_RULE_STILL` を消した |
| `src/shibuya/world/processes/circularity.py` | CI の 2 段(§7): `PatternScoring.category`(「区分」の列)・`PatternScoring.known`・`STAND_IN`・`KnownCircularity`・`KNOWN_CIRCULARITIES`(9 件)・`classify`・`stale_declarations`・`warning_lines`・docstring |
| `tools/ledger/add_decision_rows_1101.py` | `NEXT_BUMP_ROWS` に #43・#103・`DECIDED` に 11-02r/§1 #7(#43 は 11-01 の ID と併記)・5 行の `drives_note` に止めた注(`ABSENT_STOPPED_ROWS`) |
| `tools/ledger/add_pattern_columns_1101.py` | `BURNED` の D5′・E5 の値を今の台帳の文にそろえた(列を足す前の表にだけ効く道具=今の台帳には触らない) |
| `tools/ledger/fix_pattern_rows_1102.py`(新) | パターン台帳の D5′・E5 の行を直す冪等の道具(§7-2) |
| `docs/design/bridging-ledger.json` | DEC の 5 行(`DEC-43-powerWater`・`DEC-103-wastePickup`・`DEC-104-streetSweep`・`DEC-106-roadWorks`・`DEC-110-dispatch`)=`remove_at` next-bump(#43 は 7 から・#103 は 6-6 から)・`decided`・`drives_note`。PR の 6 行に注(`PR-waste_collection`・`PR-street_cleaning`・`PR-road_works_occupancy`・`PR-plan.road_works`・`PR-public_service_dispatch`・`PR-infra_daily_load`)。足した行 `DOC-s2e-absent-legacy-switch`(next-bump・最初の DEC の行の前)。790 → 791 行 |
| `docs/design/v2-pattern-ledger.md` | D5′(§9)の用途・区分・burned/E5(§1 階層 E)の split案・区分・burned/§5 集計の「較正に使ってよいのは … E5 …」の行に注(数値は不変) |
| `docs/bench/analysis/s2e-1102/` | 本書・計器の出力 [absent_declarations.md](absent_declarations.md)・道具 [tools/run_s2e.py](tools/run_s2e.py)(比べと性能)・[tools/add_bridges_s2e.py](tools/add_bridges_s2e.py)(つなぎの台帳の行) |
| 試験 | §4 |

つなぎの台帳の道具は 2 つとも冪等(`add_bridges_s2e.py` を 2 回・その後 `add_decision_rows_1101.py` を回して md5 が同じ=`08b0f186…`)。土台の DEC 以外の行の指紋は `tests/bridging/test_decision_rows_1101.py` の `BASE_ROWS`=679・`BASE_ROWS_SHA`=`91fbecef…286b16aa` に改めた(前=678 行 `7130eb39…f5e81a7`。変えた行は上の PR の 6 行と足した 1 行)。

## §2 5 件の止め方と切替口

| 名(`engine.absent_processes`) | 過程(実行器・台帳の id) | 止め方(既定 stopped) | 止めないもの | 宣言 |
|---|---|---|---|---|
| `waste_collection` | `waste`・`waste_collection` | `step` の 06〜10 時の収集の前で返す(`goods_flow.py:535-536`)=ビンは集めない | 05:00 の売れ残り(率の規則の腕)・19:00 の世帯の消費(#41=11-02r #8 で残す)・腕 duties の担当の体の廃棄 | `absent.waste_collection` |
| `street_cleaning` | `street_cleaning` | ポイ捨て(率の規則の腕)の後、掃除の巡回の前で返す(`goods_flow.py:723-724`) | ポイ捨て(`--rate-rules legacy` だけ) | `absent.street_cleaning` |
| `road_works` | `road_works`・`road_works_occupancy`(PlanSpec `plan.road_works`) | `step` の頭で返す(`logistics.py:346-347`)=辺を占用しない・ActualLog に書かない | その日の工事の辺の抽選(日の鍵の counter=ほかの流れを動かさない) | `absent.road_works` |
| `dispatch` | `dispatch`・`public_service_dispatch` | `request` が -1 を返す(`civic.py:162-163`)=乱数を引かない・記録しない・到着も無い | 倒れる事象そのもの(率の規則の `collapse`=既定は無い) | `absent.public_service_dispatch` |
| `infra` | `infra`・`infra_daily_load` | `step` の頭で返す(`civic.py:442-443`)=負荷を数えない | — | `absent.power_water` |

- 切替口: CLI `--absent-processes {stopped,legacy}`(既定は指定なし=環境変数 `SHIBUYA_ABSENT_PROCESSES`、その既定 `stopped`)。指定は環境変数より強い。名の誤りは止める(CLI は argparse の SystemExit・環境変数と `set_arm` は ValueError)。
- 腕は組み立てで 1 回読み(`build.py:793-795`)、`WorldProcessRunner` と 5 過程は引数 `absent_processes`(`None`=今の腕)で受ける。`run_day` の引数にしない=設定の指紋に入れない(`rate_rules`・`seat_release` と同じ)。
- manifest の一番上の鍵の末尾(`rate_rules` の後)に `absent_processes`=設定 `schema`(`shibuya.absent_processes/1`)・`mode`・`processes`・`stopped`(過程ごとの `absent_<名>_stopped`)/観測 `counts`(旧道の件数=収集の回と量・掃いたセル・街路に残るごみ・工事の着手・出動・倒れた数・電気と水)。過程の `counters()` にも `absent_<名>_stopped` の印(`process_counters` は manifest に入らない)。
- 状態のファイルの見出し: 既定 stopped のランだけ `absent_processes: {"mode": "stopped"}` を書く(無い=legacy=版上げの前のラン)。再開のとき腕が違えば止める(`check_resume`)。
- 腕が既定と違えば `cli.run` のランの種類は `arm`(`cli.py:507`)。
- つなぎの台帳: `DOC-s2e-absent-legacy-switch`(next-bump=次の版上げで切替口を消すときに書き直す試験の一覧つき)。DEC の 5 行は next-bump(`remove_basis` は道具の約束どおり inferred)。

## §3 計器の前後

### 3-1 「無いと宣言」の一覧(`tools/instruments/absent_declarations.py`)

前=土台の出力(= [s2-ledger-1101/absent_declarations.md](../s2-ledger-1101/absent_declarations.md))・後=[absent_declarations.md](absent_declarations.md)。

| 宣言(§1 主体が居ない過程) | id | 前 | 後 |
|---|---|---|---|
| ごみ収集 | `absent.waste_collection` | まだ動く | **止めた** |
| 街路の清掃 | `absent.street_cleaning` | まだ動く | **止めた** |
| 宅配 | `absent.parcel_delivery` | 止めた | 止めた |
| 道路工事 | `absent.road_works` | まだ動く | **止めた** |
| 救急と警察の出動 | `absent.public_service_dispatch` | まだ動く | **止めた** |
| 催しの人の注入 | `absent.event_injection` | 止めた | 止めた |
| 採用と解雇 | `absent.hiring_firing` | 止めた | 止めた |
| 電気と水の負荷 | `absent.power_water` | まだ動く | **止めた** |
| (§2)納品 | `absent.inbound_delivery` | まだ動く | まだ動く(外さない=E5 と気象の文と一緒に次の版上げ) |

| §5 件数 | 前 | 後 |
|---|---|---|
| 宣言 | 26 | 26 |
| 止めた(循環の検査の例外になる) | 20 | **25** |
| まだ動く | 6 | **1**(納品) |
| 指紋 | `81215f34d47a28fe` | `3bddeaccdebf814d` |

### 3-2 5,000 体 × 1 日の比べ([tools/run_s2e.py](tools/run_s2e.py))

「土台」は `b593b57` の src・「stopped」は本段の既定・「legacy」は本段の `--absent-processes legacy`。右の 3 列は率の規則を旧道にした組み合わせ(`--rate-rules legacy`=倒れる人・ポイ捨て・売れ残りの廃棄がある世界=正しい不合格が数で見える)。

| 量 | 土台 | stopped | legacy | 土台+率 legacy | stopped+率 legacy | legacy+率 legacy |
|---|---:|---:|---:|---:|---:|---:|
| final(先頭 16) | `73aa01d9afb206d0` | `73aa01d9afb206d0` | `73aa01d9afb206d0` | `7bfe215641b792ac` | `c090385d84cbcf4d` | `7bfe215641b792ac` |
| 呼数 | 61,066 | 61,066 | 61,066 | 62,176 | 61,997 | 62,176 |
| 収集の停車/搬出[g] | 0 / 0 | 0 / 0 | 0 / 0 | 234 / 910,750 | **0 / 0** | 234 / 910,750 |
| 売れ残りのビンの行 | 0 | 0 | 0 | 1,544 | 1,544 | 1,544 |
| 世帯の消費[個]/[g] | 1,131 / 395,850 | 1,131 / 395,850 | 1,131 / 395,850 | 1,136 / 397,650 | 1,136 / 397,650 | 1,136 / 397,650 |
| 当日の廃棄 sink[g] | 395,850 | 395,850 | 395,850 | 1,308,400 | **397,650** | 1,308,400 |
| 廃棄の射影[t/日] | 0.396 | 0.396 | 0.396 | 1.390 | **0.398** | 1.390 |
| 掃いたセル延べ/掃いた量[g] | 1,920 / 0 | **0 / 0** | 1,920 / 0 | 1,920 / 81,911 | **0 / 0** | 1,920 / 81,911 |
| 街路ごみの発生/残り[g] | 0 / 0 | 0 / 0 | 0 / 0 | 141,658 / 59,747 | 141,743 / **141,743** | 141,658 / 59,747 |
| 工事の着手/撤去/塞いだセル | 12 / 6 / 6 | **0 / 0 / 0** | 12 / 6 / 6 | 12 / 6 / 6 | **0 / 0 / 0** | 12 / 6 / 6 |
| 倒れた/出動/到着 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 5 / 5 / 5 | 5 / **0 / 0** | 5 / 5 / 5 |
| 顕著行為の事象 | 0 | 0 | 0 | 10 | 5 | 10 |
| 電気[kWh/日]/水[m³/日] | 16,458 / 564 | **0 / 0** | 16,458 / 564 | 16,527 / 567 | **0 / 0** | 16,527 / 567 |
| ActualLog の行 | 25,276 | 25,264 | 25,276 | 27,886 | 27,642 | 27,886 |
| manifest の末尾 | `space`・`rate_rules` | `rate_rules`・`absent_processes` | 同左 | — | 同左 | 同左 |

- **正しい不合格**(11-02r #7)の数: 率の規則を旧道にした世界で、止めた腕は街路に残るごみが 59,747 g → 141,743 g(掃いた量 81,911 g → 0)、倒れた 5 人の出動と到着が 5 → 0(倒れた事象は同じ 5 件=乱数は counter)、店のビンの収集が 910,750 g → 0(ビンに溜まる一方=廃棄 sink に入らない=射影が 1.390 → 0.398 t/日)。W1・W3 の錨を照合すると外れる側へ動く(W1 は収集ができるまで比べられない・W3 は体の式ができるまで検証から外す=宣言どおり)。
- 既定の腕(率の規則 off)では、止めた 5 件の出力は世界を変えていなかった。ごみ・ポイ捨て・倒れる人が無いので収集・掃除・出動は空回りで、工事は記録のみ、電気と水は報告だけ。だから既定の final は動かない。
- 「stopped+率 legacy」の final が動いたのは、出動の到着が「警察」の顕著行為(B4 の目につく出来事)を出し、それに気づいた体が起きていたため(顕著行為の事象 10 → 5・呼数 62,176 → 61,997)。
- 「stopped+率 legacy」で倒れた事象の数が同じでも街路ごみの発生量がわずかに違う(141,658 → 141,743 g)のは、起床の数が変わって在圏の密度の時系列が変わったため(推測・内訳は測っていない)。

## §4 試験

範囲 `tests/engine tests/economy tests/c8 tests/bridging tests/tools tests/perception tests/build_pop`(作業木の src・`-n 8`・`-p no:cacheprovider -o addopts=""`)。

| 回 | passed | failed | errors | skipped | 時間 |
|---|---:|---:|---:|---:|---|
| 1 回目(直しの途中の版) | 4,834 | 4 | 0 | 1 | 32 分 51 秒 |
| 最終(§4-3) | 4,836 | 2(土台から落ちている 2 本) | 0 | 1 | 32 分 21 秒 |

1 回目に落ちた 4 本:

| 試験 | 理由 | 直し |
|---|---|---|
| `tests/engine/test_state_ledger_10b.py::test_t7_legacy_switch_reproduces_the_pre_bump_final` | 率の規則だけ旧道にした 5,000 体のラン=止めた出動が警察の到着を消して final が動いた(`c090385d…`・61,997) | 「無い」の過程も旧道に(版上げの前の値=2 つの切替口とも legacy) |
| `tests/engine/test_resume_10d.py::test_counter_rng_resume_draws_once` | 出動の数を見る(`dispatches > 0`) | 旧道を明示 |
| `tests/engine/bridging/test_bridging_ledger.py::test_the_counts_by_form`・`::test_heading_rows_carry_the_heading_and_the_item_count` | **土台 `b593b57` で同じく落ちる**(本段と無関係)。`95c4ced`(#134・presence.py の docstring の書き直し)で `engine/presence.py` の expedient の見出しの項が 9 → 11 個になり、台帳の行 `HD-engine.presence-b560bcbc` の「項 9 個」と項の総数 366 が古いまま(数えると 368) | 直していない(§9 問い 1) |

### 4-1 新しい試験

- `tests/engine/processes/test_absent_processes_1102.py`(19 本): 切替口(既定 stopped・名の検査・印・宣言 absent.py と 1 対 1)/見出しと再開/過程ごとの正と負の対照=ごみ収集(stopped はビンに溜まる・世帯の消費は両方の腕で起きる)・街路の清掃(ポイ捨ての旧道でごみを生じさせ、stopped は残る=正しい不合格)・道路工事(stopped は占用 0・ActualLog 0・辺の抽選は両方の腕で同じ)・出動(stopped は -1・記録 0・到着 0)・倒れる事象は両方の腕で同じ数で、stopped は出動も到着も 0(正しい不合格)・電気と水/実行器が 5 過程へ腕を渡す(stopped・legacy・None=今の腕)/合成世界の run_day の manifest(末尾の鍵・stopped の件数は全部 0・legacy は電気と水を数える)/CLI の名の誤り。
- `tests/bridging/test_drives_from_vs_scoring.py`(§7): `test_d5p_and_e5_are_on_the_validation_side`・`test_known_rows_in_the_pattern_ledger_have_a_declaration`・`test_two_tiers_on_a_synthetic_example`(宣言の無い重なりで落ちる・宣言つきで警告だけ・主体が違えば落ちる・古い宣言を見つける・外す段の無い宣言は作れない)・`test_no_undeclared_circularity`・`test_no_stale_declaration`・`test_stand_in_overlaps_are_declared`。

### 4-2 直した既存の試験(機械的=鍵の並び・旧道の過程の挙動を見る試験に legacy を明示)

| 試験 | 理由 | 直し方 |
|---|---|---|
| `tests/engine/time/manifest_keys_frozen.json`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/perception/facts/test_percept_schema.py`・`tests/engine/test_env_and_sections_10f.py`(`AP12_KEYS`) | manifest の一番上の鍵の末尾に `absent_processes` | 凍結の一覧と末尾の並びに足した(凍結の JSON の注に理由)。**一番上の鍵の凍結の更新は親が確かめてほしい** |
| `tests/engine/test_env_and_sections_10f.py::test_config_paths_are_frozen` | 設定の節の道筋に `absent_processes.mode/processes/schema/stopped` の 4 本 | `CONFIG_PATHS_SHA256` を `fc5174c7…3308fca73` → `0e6dfaaa…b81f9ec69`(土台との差はこの 4 本だけ=一覧の diff で確かめた) |
| `tests/engine/processes/test_civic.py`(出動 2 本・電気と水 1 本)・`test_goods_flow.py`(収集 2 本・掃除 1 本)・`test_logistics.py`(工事 1 本) | 旧道の過程の挙動そのものを見る | 過程に `absent_processes="legacy"` |
| `tests/engine/processes/test_salient.py`・`test_rng_scheme_10c.py`(モジュールの autouse の fixture) | 出動の経路を見る(倒れる率の口と同じく旧道) | fixture に `absent_processes` の旧道も足した |
| `tests/engine/processes/test_rate_rules_1101.py::test_run_manifest_counts_rise_in_legacy_and_are_zero_off` | 末尾の鍵 | `list(m)[-2:] == ["rate_rules", "absent_processes"]` |
| `tests/engine/test_processes_run.py::test_c4_second_half_on_the_real_world` | 工事の ActualLog の行・`road_works.n_started > 0`・電気 > 0 | 既定では行が立たない・着手 0(辺の抽選は残る)・電気 0 を見る形に(負の対照) |
| `tests/engine/test_state_ledger_10b.py::test_t7_legacy_switch_reproduces_the_pre_bump_final`・`tests/engine/test_resume_10d.py::test_counter_rng_resume_draws_once` | §4 の 1 回目 | 旧道を明示 |
| `tests/bridging/test_decision_rows_1101.py` | 土台の行の指紋(§1) | `BASE_ROWS`・`BASE_ROWS_SHA` と注 |
| `tests/bridging/test_drives_from_vs_scoring.py::test_engine_stopped_flags`・`::test_next_bump_rows`・`::test_pattern_ledger_has_scoring_and_burned_for_every_row`・`::test_suspect_rows_contributes` | 5 件の True・DEC の next-bump に #43・#103・D5′ の burned・E5 の既知の循環・車→D5′ の重なりが例外の側へ・納品→E5 の行を足した | 期待値を今の宣言に |
| `tests/tools/test_absent_declarations.py` | 件数(20・6 → 25・1)と記録のファイル | 記録を本段の [absent_declarations.md](absent_declarations.md) に(前の版の出力は s2-ledger-1101 に残す)・5 件の行が「止めた」 |

### 4-3 最終の全体試験

同じ範囲・`-n 8`: **2 failed・4,836 passed・0 errors・1 skipped**(32 分 21 秒)。落ちた 2 本は土台で落ちる `test_bridging_ledger.py` の 2 本(§4・§9 問い 1)。範囲ごとの集めた本数(`--co`): tests/engine 3,134(failed 2=上の 2 本)・tests/economy 446・tests/c8 186・tests/bridging 29・tests/tools 445・tests/perception 386・tests/build_pop 213=合計 4,839(=passed+failed+skipped)。engine 以外の範囲は failed 0・errors 0。skipped の 1 本の場所は数えていない(前の記録の「前からの 1 本」と同じと推測)。`lint-imports` は 5 kept・0 broken。秘密スキャン(変えたファイルと新しいファイル)は CLEAN。

## §5 golden の更新と理由

**更新した golden は 0 本。** 既定(stopped)の 5,000 体 × 1 日は final `73aa01d9afb206d0`・呼数 61,066 で、土台と同じ(T7・K19・nav1・帰無腕・空腹 v1・l4×1・古典・関係・近接の golden は全範囲の試験で通った=§4)。理由は §3-2 の注: 既定の腕(率の規則 off)では、止めた 5 件の出力が behavior-hash と起床に入っていない。動いた欄は過程の件数・ActualLog の行(工事の 12 行)・manifest の節で、これらを固定する試験は §4-2 で直した。

旧道に固定した 1 本: `test_t7_legacy_switch_reproduces_the_pre_bump_final` は 2 つの切替口とも legacy で final `7bfe215641b792ac`/62,176(前の版の旧道と同じ)。次の版上げで 2 つの切替口と一緒に消す。

## §6 性能の記録(10-13b §0-7)

5,000 体 × 1 日・mock・seed 1・CLI の既定・1 本ずつ単独で順に回した(土台 → stopped → legacy を 2 巡)。刻みあたりは壁時計 ÷ 実際に進めた刻みの数(実行器の `n_steps`=1,440=1 日 ÷ 幅 60 秒と一致)。最大メモリは Windows の最大の作業集合(`GetProcessMemoryInfo` の `PeakWorkingSetSize`・10^6 B を MB とした)。判断モデルの呼数は 0(mock)。

| 版 | 壁時計[秒] 1 巡/2 巡 | 刻みあたり[ms] | 最大メモリ[MB] | 呼数(LLM) | final |
|---|---|---|---|---:|---|
| 土台(`b593b57`) | 51.2 / 49.6 | 35.6 / 34.4 | 517.9 / 528.7 | 61,066 | `73aa01d9afb206d0` |
| 本段の既定(stopped) | 52.4 / 50.6 | 36.4 / 35.1 | 535.1 / 540.9 | 61,066 | `73aa01d9afb206d0` |
| 本段の legacy | 51.9 / 50.7 | 36.1 / 35.2 | 533.1 / 529.0 | 61,066 | `73aa01d9afb206d0` |
| (参考)STATUS の前の版の表(率の規則の段の記録・別の日) | 41.8 | 29.1 | 534 | 61,066 | `73aa01d9afb206d0` |

- 同じ日・同じ測り方の中では、既定(stopped)は土台より壁時計 +1.0〜1.2 秒(+2%)・最大メモリ +12〜17 MB。止めた側は仕事が減るだけなので、差は並べ順(いつも土台の次に回した)と機械の揺れと見る(推測・順を入れ替えた測りはしていない)。悪化の判定は親に任せる(§9 問い 7)。
- STATUS の表の 41.8 秒より今日の土台が 8〜10 秒遅い。同じコード(final 同じ)なので、機械の状態の違いと見る(推測)。3 本の差は同じ日の測りの中で比べる。
- 1 巡目の 2 本目以降は、記録の文を書く作業(軽い)と並べて回した。比べのラン(§3-2)は性能の値に使っていない。

## §7 CI の 2 段と D5′・E5 の宣言

### 7-1 仕様(`world/processes/circularity.py`・`tests/bridging/test_drives_from_vs_scoring.py`)

- 重なりの見つけ方と例外の形は前のまま(`find_overlaps`=`drives_from` × 採点する系・例外は `burned`/`外す` の行と、止めた「無い」の宣言の錨)。
- 例外の付かない重なりを `classify` で 2 つに分ける。`KNOWN_CIRCULARITIES` の宣言(行・系・主体の 3 つが同じ)に当たれば**警告**、当たらなければ**落とす**。
  - 警告は `warnings.warn(UserWarning)` で出す(pytest の warnings summary=CI のログに 1 行ずつ「既知の循環(警告・決定の ID): 主体 の 系 → 行。外す段: …〔decided/inferred〕」)。
  - 落とすのは `AssertionError`(「宣言の無い重なり … =落とす」と重なりの一覧)。
  - 宣言は外す段が空なら作れない(`KnownCircularity.__post_init__` が ValueError)。
  - どの重なりにも当たらない宣言(古くなった宣言)は `stale_declarations` で見つけて落とす(宣言だけが残るのを防ぐ)。例外の行に宣言を置くことも落とす(例外で通るなら宣言は要らない)。
- 代打の条件 ⑤(代打の出力が錨に入る)も同じ 2 段で見る。疑いの行(routing §6-B の 5 行+納品→E5)の ⑤ の重なりを系 `stand_in` の重なりにし、同じ `classify` にかける。
- パターン台帳の `burned` の欄が「既知の循環」で始まる行(`PatternScoring.known`)は、宣言の表に同じ行があることを試験で突き合わせる。
- `PatternScoring` に「区分」の列(`category`)を足した(検証か較正かの試験に使う・列の無い表は空)。

### 7-2 宣言の表(9 件=主体 15=警告の 15 対)

| 行 | 系 | 主体 | 外す段 | 根拠 |
|---|---|---|---|---|
| D5 | `data:road_census_r3` | `vehicle_cross_section`・`DEC-109-driveCars` | 通過交通を境界の外の入力にし、断面の区間を範囲の外側(入力)と内側(検証)に分ける段(DEC-109=7・回答 11-01 §10-1・台帳 §10-2 の自動車の行) | inferred |
| D12′ | `data:tokyo_noise_r5` | `static_noise_field` | 7(騒音の照合を較正に使っていない測定点に分ける段=台帳 §10-1 の騒音の行・計画に段が無い) | inferred |
| A5・A6 | `data:ssb` | `DEC-63`・`DEC-69`・`DEC-71` | 6-2(W17 を初期の予定に格下げ・照合は構築に使っていない表=台帳 §10-2 の社会生活基本調査の行・DEC の外す段) | inferred |
| A7 | `data:ssb` | `DEC-63` | 同上 | inferred |
| D8 | `stand_in` | `DEC-31-leaveSeat` | 11-01p-3(席を立つ口・DEC-31 の外す段) | inferred |
| W1 | `stand_in` | `DEC-98-restock` | 11-01p-3(補充の口・DEC-98 の外す段) | inferred |
| **E5** | `stand_in` | `DEC-98-restock`・`DEC-102-inboundDelivery` | **配送の入荷が店の発注と配達員の行動になる段** | inferred(循環=11-02r §1 #6 のユーザー決定・外す段=親の案(第342)=PENDING §2 の 3 の `delivery_inbound` と同じ段) |
| W1 | `stand_in` | `DEC-41-homeUse` | 語彙に「家で使う」が入る段(11-02r §1 #8・DEC-41=11-01p-3) | inferred(決定 11-02r/§1 #8) |

外す段は 9 件とも `basis=inferred`。E5 を除く 8 件は実装役が台帳の行(DEC の `remove_at`・パターン台帳 §10)から当てた値、E5 は親の案(§9 問い 2)。`decided` の定義は「ユーザーの決定に外す段が書いてある」のまま(〔検収 中-2・親の判断〕)。

台帳と宣言の突き合わせは**台帳 → 宣言の向きだけ**(台帳の「既知の循環」の行には宣言がある)。逆向き(宣言のある行の台帳の欄が「既知の循環」か)は次の段=D5・D12′・A5〜A7・D8・W1 の台帳の欄は未記入(〔検収 低-3・親の判断〕)。

### 7-3 D5′ と E5 の行(`tools/ledger/fix_pattern_rows_1102.py`=冪等・2 回回して 2 回目は 0)

| 行 | 列 | 前 | 後 |
|---|---|---|---|
| D5′(§9) | 用途 | 断面交通の較正 | 断面交通の検証(今は入力と重なるので採点できない=burned・11-02r §1 #6) |
| D5′ | 区分 | 錨(較正→検証へ) | 錨(検証・今は burned=11-02r §1 #6) |
| D5′ | burned | —(較正→検証へ=回答 11-01 §8・§10-1) | burned(今は入力と重なるので採点できない=駆動の値と照合の値が同じ道路交通センサス R3 の行・11-02r §1 #6・回答 11-01 §8・§10-1。断面の区間を分けたら内側の区間で採点する=§10-2 の自動車の行) |
| E5(§1 階層 E) | split案 | **較正** | holdout(検証へ=11-02r §1 #6) |
| E5 | 区分 | 錨(要確認・較正に使用) | 錨(検証・既知の循環=11-02r §1 #6) |
| E5 | burned | 要確認(較正に使用=split 欄・回答 11-01 §3 の疑い) | 既知の循環(補充の代打と納品の入力の出力が E5 に入る=contributes。11-02r §1 #6=E5 は検証・既知の循環(ユーザー決定)。外す段: 配送の入荷が店の発注と配達員の行動になる段=親の案(第342)=PENDING §2 の 3 の delivery_inbound と同じ段) |
| §5 集計 | 「較正に使ってよいのは A5(NHK側)・E1・E5・F1-3 のみ」 | (そのまま) | 末尾に「〔11-02r §1 #6〕E5 は検証へ移した(較正には使わない・今は既知の循環として宣言=§1 階層 E の E5 の行)」(訂正の伝播) |

この結果、車→D5′ の重なり 2 件(`vehicle_cross_section`・`DEC-109`)は警告から例外(burned)の側へ移った。E5 は例外にしない(警告で残す)。数値の列は触っていない。

## §8 時間の方針(11-02r §2-2)への適合

本段で新しく書いた行は、刻みの番号に依存しない。

- `engine/absent_processes.py`: 時刻を持たない(腕の名だけ)。
- 5 過程の止める所: 腕を見て返すだけで、時刻の判定を新しく足していない(旧道の窓の判定は前のコード=書き換えていない)。
- `tests/engine/processes/test_absent_processes_1102.py`: 時刻は世界の時刻(秒)で書き、過程へ渡す刻みの番号は幅 `STEP_S` から `_k(秒)` で都度求める(過程も同じ幅で組む・run_day の `ticks` も `_k(2 時間)`)。
- `tools/run_s2e.py`: 刻みあたりの値は実際に進めた刻みの数(実行器の `n_steps`)で割り、世界の日数は刻みの数 × 幅で求めて突き合わせる(1,440 を決め打ちしない)。
- 既存の試験の直し(§4-2)は、既存の刻みの番号の書き方のまま(引数を足しただけ)。既存のコードの過程の `step(tick)` の口と、出動の `request(tick, …)` の口は前のまま(書き換えは要らない=方針どおり)。

## §9 問い

1. **土台で落ちている試験 2 本**(§4): `test_bridging_ledger.py` の `test_the_counts_by_form`(項の総数 366 → 368)と `test_heading_rows_carry_the_heading_and_the_item_count`(`HD-engine.presence-b560bcbc` の「項 9 個」→ 11 個)。原因は `95c4ced`(#134 の presence.py の docstring)で、本段とは無関係。台帳の行の文と試験の数を直すのは本段の範囲の外なので触っていない。親が直すか、別の段に回すか。
2. **既知の循環の外す段は 9 件とも inferred**(§7-2)。E5 を除く 8 件は実装役の当て、E5 は親の案(第342)。車→D5 は D5′ と同じく「区間を分けたら」なので、D5 も D5′ と同じ扱い(burned)にするかは問い。
3. **DEC-43・DEC-103 の外す段を next-bump に改めた**(電気と水=7・ごみ収集=6-6 から)。「外す段」の意味を「切替口を消して宣言を閉じる版上げ」と読んだ(率の規則の行と同じ)。収集員の体を置く段(6-6)は宣言の文の「外す段」に残る。読みが違えば戻す。
4. **E5 の split を「holdout(検証へ)」にした**。§5 集計の「較正に使ってよいのは … E5 …」の文は消さず注を足した。誓約の文そのものを書き換えるかは親(台帳の §0 の運用規則に触る)。
5. **納品→E5 の行を疑いの表に足した**(`DEC-102-inboundDelivery`・`contributes=E5`)。E5 の宣言の主体に補充と納品の 2 つを入れたのは、発注の文の外す段が「配送の入荷」を名指しするため(読み)。
6. **既定の final が動かなかった**ので、指示書の「既定側は動く」は final ではなく、過程の件数・ActualLog・manifest で動く(§3-2)。親の 4 構成 byte-check で「既定側が動く」を final で見る場合は、率の規則を旧道にした組み合わせ(final `c090385d…`)が動く側になる。
7. **性能**: 既定は土台より +2% の壁時計(§6)。仕事は減るので変更が原因とは考えにくいが、並べ順を入れ替えた測りはしていない。要るなら親の機械で測り直してほしい。

## §10 検収の直し(別の検収役=条件つき受入・高 0・中 2・低 4)と本体への rebase

| # | 重さ | 直したこと | 場所 |
|---|---|---|---|
| 1 | 中 | 宣言の数を **9 件(主体 15)**・外す段の当てを **8 件(E5 を除く)** に直した | 本書 §0・§1・§7-2・§9 問い 2 |
| 2 | 中 | 〔親の判断〕`decided` の定義は「ユーザーの決定に外す段が書いてある」のまま。E5 は `basis="inferred"` に戻し、出典を分けた(循環=11-02r §1 #6 のユーザー決定・外す段=親の案(第342)=PENDING §2 の 3 の `delivery_inbound` と同じ段) | `circularity.py` の `KnownCircularity` の docstring と E5 の宣言の `reason`・パターン台帳 E5 の burned・`tools/ledger/fix_pattern_rows_1102.py`(前の版の文は `SUPERSEDED` に置いて冪等のまま書き換える)・`add_pattern_columns_1101.py` の `BURNED`・試験 `test_d5p_and_e5_are_on_the_validation_side`(9 件とも inferred) |
| 3 | 低 | 〔親の判断〕突き合わせは台帳 → 宣言の向きだけ(試験は変えない)と §7-2 に 1 行 | 本書 §7-2 |
| 4 | 低 | `_counts` の docstring を「正しい不合格の 2 欄(`street_litter_now_g`・`collapse_events`)を除き 0」に | `engine/absent_processes.py` |
| 5 | 低 | 止めた腕の電気と水の山の時 `peak_hour` を −1(`civic.py:454-455`)・要約の文も「止めた」(`civic.py:461-462`)。試験 `test_infra_peak_hour_is_minus_one_when_stopped`(stopped で −1・legacy で 0〜23) | `engine/processes/civic.py`・新しい試験 |
| 6 | 低 | `run_day` を通す再開の試験 `test_resume_through_run_day_checks_the_arm`(300 体・合成世界・12 時で止めて再開=同じ腕なら通しのランと final 一致・違う腕なら ValueError) | `tests/engine/processes/test_absent_processes_1102.py` |

### 10-1 rebase(本体 `1c137c6` の上へ)

手順: 変えたファイル 46 本を控え → 土台(b593b57)に戻す → `git merge --ff-only build/spatial-d102-prep`(早送り=`1c137c6`)→ 本体の側でも変わった 3 本だけ 3 方向 `git merge-file`(base=b593b57・ours=控え・theirs=新しい HEAD)・ほかは控えをそのまま写した。

| ファイル | 結果 | 解き方 |
|---|---|---|
| `docs/design/bridging-ledger.json` | 衝突なし | 本体の `HD-engine.presence-b560bcbc`(項 11 個)をそのまま取り、本段の 12 行(DEC 5・PR 6・DOC 1)をその上に。道具 2 本を回し直して変化なし(冪等・md5 `cc4faeb6…`) |
| `src/shibuya/cli.py` | 衝突なし | `--memory-model` の `%%` の行は本体の版のまま(本段の差分に `%%` の行は無い) |
| `tests/bridging/test_decision_rows_1101.py` | 衝突(`BASE_ROWS`・`BASE_ROWS_SHA`) | 本体の注を残し、「第342 の 1c137c6 の後に s2e の 1 行(DOC-s2e-absent-legacy-switch)を足した」の注を足した。再計算=**679 行・`eaf4d8e7efa2f130cf3dc74cf6c169d11b6566aa73c124d1ad83acd117c44bdb`**(検収役の見立てと一致) |

本体で直った `test_bridging_ledger.py` の 2 本(§4・§9 問い 1)は、rebase の後は通る(下の試験に含む)。

### 10-2 直しと rebase の後の確かめ

- 試験 `tests/engine/bridging tests/bridging tests/world/processes tests/engine/processes tests/tools tests/llm tests/test_cli_help.py tests/test_cli.py`(`-n 8`): **1,221 passed・0 failed・0 errors**(6 分 23 秒)。
- 5,000 体 × 1 日 mock・既定: final **`73aa01d9afb206d0`**・呼数 **61,066**(前と同じ・壁時計 50.0 秒・34.7 ms/刻み・最大メモリ 510.9 MB)。

### 10-3 残る問い

- D5 を D5′ と同じく burned にするか(親がユーザーに聞く)。
- D12′ の外す段「7(較正に使っていない測定点に分ける段)」には計画の段の根拠が無い(台帳 §10-1 の騒音の行から当てただけ)。
