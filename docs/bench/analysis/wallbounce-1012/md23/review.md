# 第 2 期 2-3 複数日の mock(10g)の独立検収

- 検収役 Opus 5.5(実装は見ていない)。対象は作業木の枝 `2-3/multiday-mock` の未 commit の差分(26 ファイル変更+新規 `engine/events/body.py`・`tests/engine/multiday/`・記録 `md23/`)。土台 `fea27d2`・本体 HEAD `21cd044`。
- 正: 発注文(親の scratch)・決定 10-03 §4-3・§6 ⑧ 8-1・§3-8・A1-3・10-12 K9・CA10・計画の 2-3 の行・1-6 の記録 [m0](../m0/README.md)・10e の記録・実装役の記録 [README.md](README.md)。
- 自分の生の出力は作業木の `_bc_review/`(検収の後に消した)。ここには結果だけを書く(絶対パスなし)。封印の層は 1 バイトも読んでいない(W9 の資産の確かめは W19 を走らせずに行った=§8 (c))。

## 判定

**条件つき受入**(高 0・中 3・低 7)。結果不変・口の守り・同値・W9 の窓・7 日の再計算・再開=通しは、自分の手で全部確かめて合った。中の 3 件はどれも実装の誤りではない。発注文と決定の食い違いと、既定にする前に決めることで、親の判断が要る。

## 1. 結果不変 ✓

| 確かめ | やり方 | 結果 |
|---|---|---|
| 実装役の byte-check([byte_check_md23.json](byte_check_md23.json)) | 19 構成 × 25 欄を読んだ。side の JSON で head 側は `src_is_worktree` 偽・md23 側は真。腕の環境変数は渡していない(既定=`mem`・`cell`・`off`) | 19/19 構成で 25 欄とも同じ・呼数の差 0 |
| 自分の byte-check 4 構成 | `10e/byte_check_10e.py`。head=本体 HEAD `21cd044` の `git archive`(src と錨 3 本と予算の宣言と w6 の置き場・祝日の CSV)・md23=作業木の src(`PYTHONPATH`)。5,000 体・seed 1・1 日・テープつき | **4/4 構成で 25 欄とも同じ**。final: w6_v3_default `5f7ae9ff24005314`(65,597 呼)・w6_v3_activity_off `e0054a837c6ec4c1`(50,301)・w6_v1_default `24375ee3dab349e8`(51,835)・v3_mem_rel `73a78288ab5e1498`(69,111) |
| 出来事の記録と manifest(既定の腕・自分の道具) | v3_mem_rel・5,000 体・1 日を HEAD の写しと作業木で回し、`EventLog` の全部の欄(生きている行)の sha256 と manifest(壁時計を除く)を比べた | 記録 `df80fb49d43b01cc`・32,050 行で**同じ**。manifest で違ったのは環境の欄(`git_commit`・`env_id`・`git_dirty`=写しに .git が無い)と、写しに台帳のファイルが無いことによる `bridges_*`・`rules_version` だけ(エンジンの値ではない)。日次の `events` の欄も同じ |
| 体の出来事の口の計器(既定の腕) | 作業木の src で `BodyEventLink.__init__`・`write`・`conversation_end`・`MemoryStore._check_logged`・`judge._with_calls` と `_body_events_on` が真を返した回数を包んで数えた | **全部 0** |

## 2. 口と約束 ✓(△ 1)

口の型と関数名・欄は記録 §1・§2 のとおり。

- `engine/events/body.py`: `BodyEventLink(log, *, signboard_reads=False)`(`EventLog` 以外は `TypeError`)。入口は `write(who, kind, partner, obj, result, cell, src, call_ids=None) -> (t_ns, seq)` と `conversation_end(sessions, cell) -> int` の 2 つで、組み立ては `_event` の 1 つ。どちらも `EventLog.append` を通る。表 `KIND_ACT_WORD`・`_WHAT_OF_KIND` は `MappingProxyType`、`SOURCES` は組、`ACT_FAMILY_WORDS` は frozenset。
- `MemoryStore.remember(agent, LoggedEvent(t_ns, seq, kind, partner, obj, result, cell), strength, None)`: 口の無い器では `ValueError`(legacy だけ)。型が違えば `TypeError`。seq < 0・記録に無い id・who が体と違う・what が種類と合わないときは `ValueError`(`_check_logged`)。`attach_events` は 1 回だけ(2 回目は `RuntimeError`)。
- 語彙: 末尾に `行為:会話の始まり`=60・`行為:会話の終わり`=61・`知覚:気づき`=62(族 `知覚` は `FAMILIES` の末尾)。前の 60 語のコードは動いていない。過程の名 `resolve`・`conversation` は `CAUSE_PROCESS_NAMES` の末尾。版は `events-vocab/2-3`。
- `DOC-memory-store-legacy` は removed(`remove_at` 2-3 のまま)。
- △ manifest: 発注文は「腕 a の記憶の目印の内訳(legacy/記録)を memory の観測に 2 欄(末尾)」。実装役は、内訳は M0 からある `origins`(`log`・`legacy`)にあるとして、末尾の 2 欄を `targets_log_live`・`targets_log_gone`(目印の先がいまの記録にある行と無い行)にした。理由は記録 §8 にあり、筋は通る。発注文の字面とは違うので親が受けるかを決める(低 L3)。

約束の各項と試験の対応(無いものだけ書く):

- 実行(ラン)の水準で「腕 `events`+`--events off`=器だけの道は legacy のまま HEAD と同じ」を確かめる試験が無い。1-6 の同値の試験 `test_m0_recall_equivalence.py` は腕 a(記録の目印)の形に書き換わり、legacy の道のランの試験が無くなった(低 L1)。自分で確かめた結果は §6 で合っていた。
- `知覚:気づき`(顕著行為への気づき)は単体の試験だけで、ランの水準では語の数を確かめていない(合成の世界には顕著行為が少ない)。5,000 体の再計算では 396 行あった(§6)。
- LlmCall の call_id がテープにあることは試験が見ていない(形と体と刻みだけ)。5,000 体の再計算では全部あった(§6)。

〔決定〕の反映: 10-03 §4-3 の暫定の印 3 行(§8 (e))・§6 ⑧ 8-1(腕 c・d は 2-1 の `--economy-stage2`)・§3-8(11a・11c の後)・K9(曜日の比較はしないと宣言)・10-13b §0-3(既定 off の腕)は反映されている。A1-3・CA10 は発注文と食い違う(中 M1)。

## 3. 発注文の各項

| 番号 | 判定 | 根拠 |
|---|---|---|
| 1 体の出来事を記録へ・目印を記録の出来事へ | ✓ | §2・§6。既定は 1 バイトも変わらない(§1)。腕 a の想起の候補は HEAD の legacy の形と同じ(§6) |
| 2 W9 の影を 7 日に | ✓ | `SHADOW_DATES`=07-28+07-13〜07-19。資産 `data/world/v2_stage_2-3/` を自分の W9 で組み直すと W9 の出力 9 本とヘッダがバイト一致し、build_hash もヘッダから組み直して `f241eb4fe5a176d3` で一致(§8 (c))。台帳の 2 行は remove_at 2-4・active・why に「窓の外の日だけ」 |
| 3 7 日の mock | △ | 5 構成 × 7 日 × 発注の量は全部ある。既定の 7 日は自分で回して全部一致した(§8 (d))。△ の理由は次の 4 つ。(i) 土台が「既定 v3」でなく `v3_mem_rel`(記憶と関係を測るため=記録 §13-3 で宣言)。(ii) 月〜日はエンジンの A1-3 が止めるので、道具だけが検査を外して `test_only` の印を付けた(中 M1)。(iii) 土日は W17 の土休の行が無く月曜の予定(K9・宣言)。(iv) 窓に給料日が無く賃金は 0 で、引き出しだけの緩みしか測れていない(記録 §13-4)。7 日のランは本体の v2 で回したので、07-18・07-19 は近い日の影を読んだ(記録 §3 で宣言) |
| 4 暫定の印 | ✓ | `DOC-md23-provisional-tau-rel`・`-copresence-weight`・`-days-to-full`(remove_at 5-2・active)。7 日では満杯にならない(1.40% → 1.80%)。容量の追記は不要とした。外挿 1,234 日は推測と明記 |
| 5 manifest | △ | 複数日の欄は 10d のまま。memory の観測の末尾の 2 欄は中身が発注文と違う(§2 の △) |

「できなかったこと」の申告(記録 §13)と実態は合っている。申告のとおり、凍結の数の試験 12 本(語彙の数と末尾 5・状態台帳の行の数 2・M0 の legacy の期待 4・`_data_ids.py`)は発注の「編集してよい」一覧の外を直した。どれも数を足す直しか、外すつなぎ(legacy 100%)の期待の付け替えで、中身の規則は変えていない。

## 4. 守り ✓(低 2)

- **書く口は 1 つ**: 新しい 3 語と体の出来事を書く所を src 全体から grep した。`body.py` の `_event` → `EventLog.append` だけだった。`append` は実行時に系の宣言(`E:events.*`)を確かめる。
- **負の対照(自分で植えた・一時の写し)**: (1) `memory` の `writes.paths` から `E:events.*` を外した写しで、合成の世界の腕 a のランは `PermissionError: 系 memory は出来事の記録(E:events.*)を書く宣言を持たない` で止まった。既定の腕は通った。静的な凍結の表(`writes_paths_events.json`)との照合も、系の並びが違って落ちる形になった。(2) `MemoryStore._check_logged` を何もしない形にした写しでは、記録に無い id(seq+99)が通った=試験 `test_remember_takes_only_ids_in_the_log` の負の対照は効く。
- **付け替え**: `MemoryStore.__setattr__` が `_ms_log_seq`・`body_events` の付け替えを落とす(口は `attach_events` の 1 回)。`_KIND_OF_CODE` は書けない配列。
- 低 L4: `BodyEventLink` は `__slots__` だけで `__setattr__` の守りが無く、`log`・`signboard_reads` を実行時に付け替えられる(1-3 の検収の教訓「実行時の守り=`__setattr__`」)。
- 低(参考・前からの形): 器の列 `_ms_log_seq` は numpy の配列で、中身は外から書ける(M0 のほかの列と同じ「口の中だけ」の約束)。試験 `test_rebuild_keeps_the_log_pointer_from_the_saved_seq` も `ms2._ms_log_seq[:] = saved` と直接書く。

## 5. 宣言と凍結 ✓

- `writes.paths`: memory と conversation に `E:events.*`。decide・llm_receive は前から宣言済み。`reads` に apply_responses と conversation の `layers.mem_layer`。`writes.soa` は変わっていない。
- 状態台帳: 行 `M0L`(外の状態の末尾・軸 1 no・軸 2 required・腕 `memory-store`・道筋 `mem_layer.memory_store._ms_log_seq`)。外の状態 111 → 112・全体 202 → 203。除外に 2 項(`body_events`=REF・`LEDGER_ARM`=CONST)。`LEDGER_VERSION` は上げていない(腕の行=既定のハッシュは不変=1-8b の前例と同じ)。`arm_owner` は「根」から「道筋の最後の属性の前まで」に変わったが、S8・S8M の値は `speech` のまま(試験あり)。
- 凍結の表: 動いたのは `tests/engine/events/writes_paths_events.json`(conversation・memory の 2 系を足しただけ)。`writes_soa_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`・`manifest_keys_frozen.json`・`CONFIG_PATHS_SHA256` は変わっていない(`git diff` に無い)。
- manifest の既存の欄: 既定の腕で値が同じ(§1)。腕 a では `memory_summary.memory_store.counts` の鍵が `legacy_events` → `log_events` に変わる。腕の中の観測なので可。
- T0: 足した行に `tick` の新しい識別子と docstring は無い(既存の `after_tick`・引数 `tick` だけ)。src に時間の直書きは無い。試験 `test_md23_resume.py`・`test_md23_tool.py` に `1440` があり、T0 の検査の範囲(src)の外なので通る(低 L6)。
- 参考(既知で宣言済み): 腕 a は full-hash を動かす(行 M0L が required)。1-6 の「腕 on/off で full-hash も同じ」は成り立たなくなった。1-6 の腕 on で作った古い状態のファイルからは再開できない(道筋の集合が違って止まる)。behavior-hash と final は同じ。

## 6. 同値 ✓

実装役の試験を読んだ: `test_recall_candidates_are_the_same_as_the_legacy_form`(合成の世界・テープの 21 列を腕 on/off で突き合わせる)・`test_m0_recall_equivalence.py`(腕 a=記録の目印に書き換え)・`test_manifest_differs_only_by_the_store_instrument`(動いてよい葉を events・full に広げた)。

**独立の再計算 1(HEAD の写しとの比較・方法を変えた)**: 腕 `events` を環境変数で立て、HEAD の写し(1-6=目印は 100% legacy)と作業木(目印は記録の出来事)を、byte-check の道具で v3_mem_rel・5,000 体・1 日・テープつきで回して比べた。

- 25 欄のうち 22 欄が同じ。final `73a78288ab5e1498`・呼数 69,111・blocks・行動の件数・behavior-hash は同じ。
- テープの列で動いたのは **`recalled_event_ids` だけ**(`recalled_rows`・`recalled_kind`・`recalled_object`・`b5_text`・`prompt_hash` ほかは全部の呼び出しで同じ)。
- 動いた残りは full-hash(最後と締めの後)と `full_external_bytes`(行 M0L)。
- =想起の候補は legacy の形と同じで、目印の値だけが記録の id に替わった。

**独立の再計算 2(legacy の道・試験の抜け L1 の代わり)**: 腕 `events` に `SHIBUYA_EVENTS=off` を足して同じく比べた。25 欄のうち 23 欄が同じで、テープは `recalled_event_ids` まで全部同じだった。動いたのは full-hash だけ(行 M0L が全部 −1 で入る)。

**独立の再計算 3(腕 a の体の出来事・5,000 体・1 日・器と記録の外から数え直し)**:

- 体の出来事 72,822 行。語ごとの数は記録 §2-2 の 1 日目と全部一致した(看板 15,550・移動 8,823・乗車 8,655・購入 6,017・並ぶ 6,004・手伝い 5,822・食事 5,812・通報 5,687・就寝 5,588・会話 3,532・会話の始まり 468・会話の終わり 468・気づき 396)。
- 原因: LlmCall 44,038 と、Process の perception 15,946・resolve 11,910・conversation 928 だけ。LlmCall の call_id は **44,038 件すべてテープにあり**、テープの行の体は出来事の who と全部同じ。呼の刻みは出来事の刻み以下で、差は 1 刻みが 42,943・0 刻みが 1,095(mock は呼んだ次の刻みに適用する=「この刻みに適用した判断の呼」と合う)。
- 器: 55,465 行全部が出どころ None。目印を記録の出来事の表から 1 行ずつ引くと、無い行 0・who の違い 0・種類の違い 0。
- 器の `remember` 72,354 回+会話の終わり 468=72,822=体の出来事の行数。

## 7. 試験 ✓

- 作業木で `tests/engine/multiday tests/engine/memory tests/engine/events tests/engine/systems tests/engine/time tests/engine/bridging tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/build_vis tests/tools`(`-n 2 --dist loadfile -m "not slow"`・pytest の `pythonpath` で作業木の src): **602 passed・1 warning(11 分 42 秒)**。data が無くて飛ばした試験は 0 件。warning は窓の外 07-20 の近い日の影の警告で、試験が期待するもの。同時に 5,000 体のランを 3〜4 本並べたので時間は参考。
- `lint-imports`(作業木の src・223 ファイル=本体より `body.py` の 1 本多い): 5 契約とも守られている。
- `tests/c7` は回していない。全体は親が回す。

## 8. 抜け道と記録

- **(a) 既定の不変** ✓: byte-check 4 構成(§1)。記録の全欄と manifest も同じ(§1)。体の出来事の口の計器は 0(§1)。
- **(b) 腕 a** ✓: 原因は LlmCall か Process(resolve・conversation・perception)だけ(§6 の 3)。`remember(origin=None)` は記録にある id だけを受け、無い id は `ValueError`(試験+自分の負の対照 §4)。想起の候補は legacy の形と同じ(§6 の 1)。`DOC-memory-store-legacy` は removed。語彙は末尾に 3 語・版 `events-vocab/2-3`。
- **(c) W9 の影** ✓: `SHADOW_DATES` は 07-28・07-13〜07-19。build_hash は次の 2 通りで確かめた。**W19 は走らせていない**。W19 は封印の層のファイル(`kddi_la`・`shibuya_jinryu`・`boundary_counts.json`)の sha256 を取るので、中身のバイトを読むことになる。
  - (1) 本体の v2 の直下のファイル 97 本(W17 の jsonl を除く)を作業用の置き場に写し、作業木の src で `--stage W9` だけを組んだ。`W9.header.json` と W9 の出力 9 本(影 8 日+面の表)が `v2_stage_2-3` とバイト一致した。param_hash `ad4a3ee8630ec2a1`。07-13〜07-17 と 07-28 は本体の v2 とも一致した。
  - (2) `v2_stage_2-3` の全段のヘッダから、W 番号順に出力の sha256 をつないで build_hash を組み直し、`f241eb4fe5a176d3` で manifest と一致した。
  - 窓の中で `BR-SHADOW-NEAREST-DAY` が呼ばれない(計器 0)・07-20 では呼ばれることは、試験 `test_stage_asset_has_the_window_and_the_fallback_is_used_only_outside`(data あり・not slow=§7 の実行に入る)で通った。台帳の 2 行は remove_at 2-4・active。
- **(d) 7 日の mock** ✓: 既定の 7 日の 1 本を自分で回した(道具の `run`・作業木の src・5,000 体・07-13 → 07-19・seed 1)。
  - final `6c709bfc84f12a17`・呼数 535,487 で記録と同じ。日ごとの呼数(69,111・79,728・79,733・81,120・71,610・73,455・80,730)も同じ。
  - 日次の記録(呼数・金・出来事)・日の終わりの読み(会話・関係辺・記憶・財布)・2-0 の計器(在圏のピーク・到着)は、壁時計を除いて全部の日で同じ。
  - 状態のファイルの大きさは 4 日で 1 B 違った。原因は npz の `meta`(run_id・env_id)で、10d の前からの形=記録の表は参考値。
  - 壁時計は 7 日で 311.3 秒(日ごとに 41.7〜47.9 秒・ほかのラン 3〜4 本と並べた)。記録は 290.6 秒。
  - 開始日の検査は `start_check_waived`(土休を含む)・`test_only` 真。07-18・07-19 は近い日 07-17 の影。
  - 日の境目の保存 → 再開=通し(5,000 体・2 日・道具の `resume`): 既定は final `3995d83df61363f1` が同じ・境目の後の checkpoint 4 点(behavior/full)が同じ・呼数 148,839。腕 d(a+b+c)も final `0c6487db123033e5` が同じ・checkpoint 4 点が同じ・呼数 146,325。どちらも記録 [resume_5000.json](resume_5000.json) と同じ値。
- **(e) 暫定の印** ✓: τ_rel・共在の長さの重み・満杯までの日数の 3 行(remove_at 5-2)。曜日の比較はしていない(K9・土日は月曜の予定と宣言)。ただし記録 §5 の「金曜と土曜が少ない(71,610・73,455)」は曜日の名で比べて見える書き方(低 L5)。
- **(f) 土台** ✓: 本体 HEAD `21cd044` は土台 `fea27d2` の子で、差は `IMPLEMENTED.md`・`PENDING.md`・`STATUS.md`・`docs/design/v2-budget-declaration.md` の 4 本だけ(src は同じ)。作業木の変更と重ならない=rebase は衝突なし。2-1・2-2・1-8b は土台に入っている。
- 記録に絶対パス・ホスト名・個人名は無い(grep。出てくるのは相対の `_bc/` だけ)。触った共有ファイルの一覧(記録 §12・§1)は `git diff --stat` の 26 本と合う。

## 欠陥(重さ順)

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中(親の判断) | 発注文 ↔ 決定 10-03 A1-3 (a)・10-12 CA10 (c)。記録 §0・§13-1・道具 `run_collect` の `_check_start` | 月〜日の 7 日はエンジンの開始日の検査が止める。CA10 (c) は試験用(分析に使わない印)の週末のランも「カレンダー化の第 1 段の後すぐ」とし、第 1 段はまだ(K9 が active)。実装役は記録の道具だけで検査を外し `test_only` の印を付けた。エンジンは変えていない。発注文と決定の食い違いで、実装役の誤りではない | 親が選ぶ: (a) 試験用の記録として受け、台帳 `DOC-md23-weekend-run-test-only` で宣言する(今のまま)/(b) 決定に合わせ、分析の表を 5 日(月〜金・07-13〜07-17)に絞る。7 日の表は `test_only` の付録に下げる。検収役は (b) を勧める(CA10 の字面と合う・5 日分の数は今の JSON から作れる) |
| M2 | 中(既定にする前) | 記録 §7・`EventLog` の成長の宣言 | 腕 a の体の出来事は体あたり 14.6 行/日。39 万体・保持窓 7 日で約 4 GB(推測)となり、1-3 の宣言(256 MB)を大きく超える。追記案は記録 §7 にあるが、台帳にも予算の宣言にも行が無い | 親が予算の宣言かつなぎの台帳に「腕 a を既定にする前(M1)に、S1 の割り当てか記録の形・保持窓を決め直す」の行を足す |
| M3 | 中(親の判断) | 台帳 `DOC-md23-pointer-after-resume`(remove_at 7)・1-6 の記録 m0 §200 | m0 は「実の目印にする段で、記録の保持と再開(required にするか)を決め直す」とした。2-3 は目印の seq だけを M0L(required)に置き、記録は discardable・保持窓 7 日のまま残した。8 日目からと再開の後は、目印の先が記録に無くなる(計器 `targets_log_gone`)。いまの想起は器の中身の写しを引くので結果には出ないが、決め直しは「段の外(7)」に送られた | 親が決める: 7 で受けるか、M1(想起を記録から引く段)の前に決め直す段を置くか |
| L1 | 低 | `tests/engine/memory/test_m0_recall_equivalence.py` | ランの水準で legacy の道(腕 events+記録 off)を確かめる試験が無くなった(自分の再計算 2 では HEAD と同じだった) | 同値の試験を `SHIBUYA_EVENTS` on/off の 2 本にパラメータ化する |
| L2 | 低 | `tests/engine/multiday/test_md23_tool.py::test_world_seven_days_default` | `shadow_fallback` を `[False]*5+[True,True]` で固定している。2-4 の活性化で本体の v2 に 07-18・07-19 の影が入ると落ちる | 2-4 で書き換えると記録に書く(または資産に影があるかで期待を分ける) |
| L3 | 低 | `memory_store.MemoryStore._log_targets`・記録 §8 | manifest の 2 欄の中身が発注文(legacy/記録の内訳)と違う(§2 の △) | 親が受けるかを決める(受けるなら記録のまま) |
| L4 | 低 | `engine/events/body.py` の `BodyEventLink` | `__setattr__` の守りが無く、`log` を実行時に付け替えられる | `MemoryStore` と同じく、組み立ての 1 回のあとの付け替えを落とす |
| L5 | 低 | 記録 §5 の「呼数」の項 | 「金曜と土曜が少ない」は、K9 の期間に曜日の名で比べて見える書き方 | 曜日の名を外し、「日によって 7.2〜8.1 万呼(曜日の比較はしない)」の形に |
| L6 | 低 | `tests/engine/multiday/test_md23_resume.py`(`TPD = 1440`)・`test_md23_tool.py`(`1440 * (d + 1)`) | 試験の時間の直書き(T0 の検査は src だけなので通る) | `core.time_consts.STEPS_PER_DAY` を使う |
| L7 | 低 | 作業木の `_bc/` | gitignore の外の作業用の置き場(状態のファイル・テープ・byte-check の写しなど)。`git status` に出る | 親は明示のパスだけをステージし、取り込みの後に消す |

参考(本段の欠陥ではない・親に伝える):

- W9 の資産を組む手順(2-3b と同じ)は W19 を含む。W19 は封印の層のファイルの sha256 を取り、中身のバイトを読む。実装役の 2 回の構築はこれを通った。封印の規則で「ハッシュを取るための読み」をどう扱うかを親が確かめる。
- 記録 §13 の限界にある「通しにテープがあり、止めたラン(前半)にテープが無いと、日の境目の再開の後の full-hash が通しと違う(final と behavior-hash は同じ)」は、10d からの形(HEAD でも同じと実装役が確かめた)。台帳か PENDING に載っていなければ親が載せる。
- 1-6 の腕 on で作った状態のファイルは、2-3 の後は再開できない(行 M0L で道筋の集合が違う)。
- 7 日のランは本体の v2(07-18・07-19 は近い日の影)で回した。窓の中で近い日の影を使わないのは、資産 `v2_stage_2-3` のランでだけ成り立つ(活性化は 2-4)。
