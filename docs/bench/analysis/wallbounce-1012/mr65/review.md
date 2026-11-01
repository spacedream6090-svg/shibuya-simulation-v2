# 第 6 期 6-5 記憶 M1〜M5 の腕と器 — 検収の記録(実装を見ていない検収役)

- 検収役 Opus 5.5。対象=作業木の枝 `6-5/memory-m1-m5-arms`(土台 `0239a3b`・未 commit)。本体の HEAD は `35aa748`(3-1 の取り込みの後)。
- 読んだもの: 決定 10-12 §4-6・回答 10-12 の 6-2・実装役への発注文・実装役の記録 [README.md](README.md) と結果の JSON・作業木の差分(src 9 本・試験 6 本の変更と新しいファイル 13 本)。
- 書いたのはこの記録 1 本だけ。作業用の置き場は作業木の `_bc_review/`(git の外・終わりに消した)。封印した層と人の記憶のデータの値は読んでいない(下の §9 に 1 件の注)。GPU・ネットワーク・重みの取得は使っていない。

## 0. 判定

**条件つき受入**(既定は不変=自分の byte-check 7 構成で確かめた。腕の中身は発注の大半を満たす。中 4 件は腕の既定化の前に直すか宣言する。高は無し)。

## 1. 結果不変 ✓

| 確かめ | やり方 | 結果 |
|---|---|---|
| 実装役の 19 構成 | `byte_check_mr65.json` を読んだ | 19/19 構成で 25 欄とも同じ・両側の `env` は空=腕は既定の道 ✓ |
| 実装役の最後の 6 構成 | `byte_check_mr65_final_6cfg.json` は要約の形だけ=生の side(`_bc/head.json`・`_bc/mr65_final.json`)を 10e の `compare` にかけ直した | 6/6 構成で 25 欄とも同じ ✓ |
| **自分の 4 構成** | 本体 HEAD **`35aa748`** の `git archive`(src・錨 3 本・`HEAD_TREE_FILES` の追跡ファイル・`w6-regen`)+本体の data へのつなぎ/作業木の src。本体の最新の `10e/byte_check_10e.py` の `side --only w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`・5,000 体・seed 1・1 日・両側とも本体の v2 の資産 | **4/4 構成で 25 欄とも同じ**(`tree_missing` 空・両側 `env` 空・`src_is_worktree` 偽=両側とも `--src` の木で回った)。final は `b8eadcb51e8705e7`・`c88ba9104f45f897`・`e1288e092ddaca86`・`768b2262e3b0999e`=実装役の値と同じ ✓ |
| **自分の 3 構成(器の道)** | 19 構成はどれも `SHIBUYA_MEMORY_STORE` を立てない=器の既定の道(6-5 の腕の分岐が入った `remember`・`recall`・`_write`)を通らない。両側に `SHIBUYA_MEMORY_STORE=events` を立てて `v3_mem_rel,v3_mem_store,v3_classical_mem_rel` | **3/3 構成で 25 欄とも同じ**(テープの列 `recalled_event_ids` の sha と `full_last`=行 M0L を含む)✓。M2 の「既定=ID の一致の想起が M0 と同じ」の 5,000 体での負の対照にもなる |
| 2 日・再開 | `two_days_head_vs_mr65.json`・`resume_default_5000.json`・`resume_m1_5000.json` を読んだ | 2 日 final `31c9b19409e18b2f`・呼数 145,675 が同じ・日の境目の再開=通し(既定と腕 m1)✓ |

HEAD を `35aa748` で比べた=3-1 の取り込みの後の本体とも既定の結果が同じ(3-1 も既定は不変のはず=それとも矛盾しない)。

## 2. 口と約束 ✓(違い 3 つ)

- 腕の切替口(`memory_m1.arms`・`set_arm`・`arms_on`・`check_arms`・`bind_rate_seed`)・CLI の 5 引数・環境変数 5 つ・`engine/memory_embed.py`(新規・名は発注どおり)・`LlmCall` の原因・`Percept` の欄・manifest `memory_summary.memory_store.mr65`・状態台帳の行 M0M・M0C・M0X・つなぎの台帳 15 行。
- 違い: (1) 腕の名は manifest の**観測**の節(`memory_summary.memory_store.mr65`)にだけ出て、設定の節にも設定の指紋にも無い(下 L1)。(2) `manifest_sections.py` は触っていない(`memory_summary.memory_store` が丸ごと観測なので要らなかった=妥当)。(3) 段の名: 発注の M4/M5 と回答 10-12 の 6-2 の表の M4(個人差 15%)/M5(同席と浅い痕跡)が違う=記録 §14 の対応表は 6-2 の表(自分で読んだ)と合う。台帳の id は混ざっている(`DOC-mr65-m4-recognition`=発注の M4・`DOC-mr65-m4-rate-variation`=6-2 の M4)=低。
- 約束ごとの試験: M1 の式・単位・最短の符号化時間・倍率・τ・M0 との上位 k(負の対照)・M2 の経路と既定で計算しないこと・M4/M5 の単体と AST と書かない負の対照・幅を倍・5,000 体 1 日(slow)・M3 の器・浅い痕跡・見えない欄・粒度 day・CLI・守り。**無いもの**: 腕 embed の再開(宣言済み)・腕 m1+embed の組み合わせのラン・母集団の seed の分けの実行時の検査(下 M1)・上限なしの腕の複数日(下 M2)。

## 3. 発注の各項

| 番号 | 判定 | 根拠 |
|---|---|---|
| 1 M1 強さの式 | △ | 式・秒・+1 なし・最短の符号化時間・種類の表・τ の仮の値・15%・腕は ✓(§6 の独立の再計算で一致)。言葉の描き方の口 `render_memories(words=True)` は描画に結線していない(宣言=テンプレの版が動く=親の判断)。人ごとの倍率の seed が組み立てに届かない(下 M1) |
| 2 M2 手がかり | △ | 既定=ID の一致は不変(§1 の器の 3 構成)。腕 embed の口・cos ≥ 0.5・+1.0·cos・要旨の埋め込み・控え ✓。**Ruri の重みは取得していない=正しく止めた**(転送先 `us.aws.cdn.hf.co` が CLAUDE.md §7 の一覧の外)。版と sha の固定の記録あり。`data/models/` は本体にも無い・venv に torch・transformers・huggingface_hub・safetensors・tokenizers が無い・site-packages の最新の変更は 10-13(pip を使っていない)✓。手がかりの文は会話の番からだけ(判断の理由と予定は未結線=宣言)=手がかりの文のある想起は 3〜5% |
| 3 M4 思い浮かぶ/見覚え | ✓ | `recall_mask`・`recognize_mask`・`forget_mask`・`PeopleRelationLayer.recognized`。親しさの数値は LLM に出ない(manifest だけ) |
| 4 M5 人も記憶(器) | △ | 同じ器・同じ式・関係の表を読まない書かない(§6 の AST と負の対照 2 本)・出来事 128 行の上限を外す・忘れる=消す・最初の関係はデータから(W16/W17 の辺=4-1 段 4 までのつなぎ)✓。**店 32 件の上限を外す道は作っていない**(記録 §4 は「本段の外」と書くが、発注 4 の範囲の中=下 M4) |
| 5 M3 の器 | ✓ | `ImpressionBook`(足すだけ・寝たときに書き直しを足す・原因 `LlmCall` だけ・長さを切らない)・mock の試験 |
| 6 浅い痕跡 | ✓ | `shallow_trace`(保存しない・読むだけ)・`trace_word`・`played_along_share`(null)・`Percept.heard_referents`(空・描画しない=src に描き手の参照なし) |
| 7 保持窓と粒度 | ✓ | 腕 `--memory-grain day`・見積り(§8 で再計算一致) |
| 8 manifest・状態台帳・凍結・台帳 | △ | 行と台帳 15 行は ✓。腕 memory での行 M0 の軸(下 M3)・腕の名が設定の節に無い(下 L1) |

「できなかったこと」の申告(Ruri の重み・M3 と浅い痕跡の結線・腕 memory と粒度 day の再開・腕 embed の再開・Petrov の式 (3) の一次確認)は実態と合う。**申告に無い**もの: 店 32 件(M4)・倍率の seed の大域の残り(M1)・上限なしの腕の複数日の太り方(M2)。

## 4. 守り ✓

- 子の持ち主(`M1State`・`CueState`)の書く口を呼ぶのは `engine/memory_store.py` だけ(AST の試験+植えた外の呼びで落ちる負の対照あり)。子の列(`_t_ns`・`_scale`・`_heard`・`_own`・`_vec`・`_qcache`)への代入は 2 つのモジュールの外に無い。自分の grep でも外からの読み書きは状態台帳の道筋の文字列だけ。
- `__setattr__`・`__delattr__` の守り(`M1State`・`ImpressionBook`・`MemoryStore` の新しい欄)と読み取り専用の view(`scale`・`recent_ns`)は試験あり。`CueState` の守りは試験が無い=自分で確かめた(`_heard`・`embedder`・`model` の付け替え・`_vec` の消去・新しい欄の追加はどれも `AttributeError`)=試験を 1 本足すとよい(低)。表は `MappingProxyType`(`KIND_SPECS`・`PARAMS`・`_ENV`・`RURI_PINS`・`WORD_PREFIX`)。ただし `PARAMS["kinds"]` の中は普通の dict(下 L4)。
- 書きの宣言: `remember` が M1 の時刻を書く前に `M0M` を、手がかりの文と埋め込みは `M0C` を確かめる。宣言を外すと落ちる負の対照あり。系の宣言は既存の `M0*:mem_layer.memory_store.*` の中に入る(新しい鍵が M0 で始まる)=宣言の表は変えていない。
- 腕の取り違えの再開(自分で試験・合成の世界 80 体・2 日・日の境目): 保存 m0 → 再開 m1・保存 m1 → 再開 m0・保存 id → 再開 embed の 3 本とも `ValueError`(保存した外の状態の道筋が今の台帳と違う)=腕の行の道筋の差で止まる ✓。埋め込みのモデル名の取り違えは止まらない(下 L1)。

## 5. 宣言と凍結 ✓(注 2 つ)

- 状態台帳: M0M(behavior・required・腕 memory-model)・M0C(behavior・required・腕 memory-cue・`_vec`・`_qcache` は hash_skip)・M0X(diag・discardable)・持ち主 2 つ・子クラス 1 つ(`rel_layer` → `PeopleRelationLayer`)・除外 7 項。腕のランの実行時の網羅は 4 つの腕で漏れ 0(試験)。外の状態 115 → 118・全体 206 → 209。
- 凍結の数の試験は増えた分だけ(行の数・腕の行の列・`SAFE_SITES` 15 → 16・Percept の欄と版・器の slots)。`writes_soa_frozen.json`・`manifest_keys_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`・`writes_paths_events.json`・`CONFIG_PATHS_SHA256` は触っていない。
- manifest の既存の欄: 鍵は不変。値は `percept`(設定の節)が既定のランでも /1 → /2・欄 1 つ増(宣言済み=下 L5)と、つなぎの台帳の件数と sha(行を足した分)だけが動く。
- 注: 腕 memory の器の行が挙動を決めるのに行 M0 の軸が既定のまま(下 M3)。

## 6. 同値と独立の再計算

1. **M1 の式**(`tools` を見ずに自分で書いた: ACT-R の正確な式 `ln Σ t_j^(−d)` と Petrov 2006 の折衷形 `ln(Σ_{j≤k} t_j^(−d) + (n−k)(t_n^(1−d) − t_k^(1−d))/((1−d)(t_n − t_k)))`・k=0 は `ln(n/(1−d)) − d·ln L`): 9 例(n=1・2・3・50・91 の最初の関係の形・d=0.35・d=0.725=倍率の上の端・k=0)で `memory_m1.base_level` との差の最大 **1.1e−16**。等間隔 50 回で正確な式 −1.5486・折衷形 −1.5323。単位を秒 → 分にすると 6 例とも全部が `d·ln 60 = 2.047172281111` だけ同じにずれる。τ=`−3.738024749`(M0 の n=1 の行が −2.0 を下回る 217.39 分から)=作業木の値と同じ。残る時間(倍率 1): 初めての成功 3.62 時間・会話 9.85 時間・失敗 26.77 時間・1 回だけ会った人の思い浮かぶ 29.4 分・見覚え 8.76 日・消える 152.6 日=記録 §2 の値と合う。39 万体の倍率: 平均 1.0003・SD 0.1499・範囲 0.55〜1.45・±3σ で切った体 1,057(0.27%)・決定的。Petrov の式は自分の記憶との一致=原典の一次確認は親の候補のまま(ネットワークは使っていない)。
2. **M0 との上位 k**(`arms_side.json` の生の計数から再計算): 順まで同じ 51.6%・72.9%・66.6%(記録と同じ)。ただし「両方とも空」の想起(169・212・1,965 回)を「同じ」に数えている=除くと 51.5%・72.9%・66.0%(下 L2)。
3. **人も記憶の腕の呼数の減り**(実装役のテープ `_bc/s7` の `wake_class` を数えた): 器だけ 67,794 → 腕 people 64,689(−3,105)。起床の種類 2 が 22,460 → 19,758(**−2,702**)=既定のランの知人出現の起床 2,700(`calls_by_condition` の ACQUAINTANCE)とほぼ同じ。残りは会話の番 −183・種類 1 −316・種類 3 +96。記録の理由(知人出現の起床を作らない)は数で支えられる。
4. **関係の表を読まない**(自分の AST・試験とは別の書き方=ファイルを読んで `RelationLayer` の全メソッドから `rel_partner/kind/sign/first/last/n`・`write_relations`・同じ名の文字列を拾う): 親の読み手 16 個は全部子が上書き・子の中の参照 0。負の対照: 子に `agents.registry.rel_sign` を読む行を植えると見つかる・子の `edges` の上書きを消すと「上書きされていない親の読み手 edges」が出る。src 全体の grep でも `rel_*` を触るのは `relations.py` と `resolve.write_relations` だけ。
5. **粒度の見積り**: §8。

## 7. 試験

- 範囲の試験(作業木・`-m "not slow"`・`-n 2 --dist loadfile`・`PYTHONPATH` に作業木の src): `tests/engine/memory`・`tests/engine/test_relations*.py`(3 本=`tests/engine/relations` は無い)・`tests/engine/events`・`systems`・`multiday`・`test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/perception`・`tests/tools`・`tests/economy/cp2`・`tests/c8`・`tests/engine/body`・`tests/engine/time` → **1,359 passed・1 skipped(Ruri の重み)・failed 0**(22 分 30 秒=同じ機械で他の作業木のランが動いていた)。`tests/c7` は回していない。slow は回していない(実装役の 4 passed を記録で読んだだけ)。
- `lint-imports`(作業木の src=`shibuya.__file__` が作業木を指すことを確かめた): 5 契約とも守られている・250 ファイル・926 の依存。
- 新しい試験は 7 ファイル・関数 49・項目 52(媒介変数 4)=記録の数と同じ。

## 8. 本段に固有の確認(発注の 8 (a)〜(h))

- (a) 既定の不変: §1。腕の名が設定の指紋に入らない宣言は、再開の取り違えが状態台帳の腕の行で止まる(§4)ので実害は小さい。前例(結果を変える腕=`speech_port`・まとめの幅・暦 1a の影は on のときだけ指紋に入る)とは違う=既定化の版上げで指紋に入れる(記録 §14 の 7)で妥当。埋め込みのモデル名は残る(L1)。
- (b) M1 の式: §6 の 1。
- (c) M2: §1 の器の 3 構成・§3 の 2。
- (d) M5: §6 の 3・4。128 行の上限を外した道は 5,000 体 1 日で幅 8 → 64(実装役)。自分で 5,000 体・3 日の通し(`v3_mem_rel`・腕 m1+memory・最初の幅 128)を回した: 器の行 62,764(1 日目・実装役)→ **139,628**(3 日目)・体あたり最大 58 → **99** 行・人の行 9,883(体あたり平均 1.98・最大 17)・消した行 0・幅は 128 のまま(広げた回 0)・壁時計 228.6 秒。
- (e) M3 の器と浅い痕跡: mock の試験・描画のバイト不変(§1 の 7 構成でテープの `b5_text`・`prompt_hash` を含む列の sha が同じ)・`heard_referents` は src の描き手から参照されない。
- (f) 粒度 day の見積りを再計算: 体の出来事=記録の行 − 器の無いランの行(1 日目 125,988 − 53,940=72,048・2 日目 121,669 − 47,908=73,761)→ 14.581 行/体/日・LLM の原因 63.86% → (72 + 0.6386 × 39) × 14.581=1,413 B/体/日 × 390,067 体 × 7 日=3.858e9 B=**3.593 GiB**。day: 109,282/10,000=10.928 行 → 1,042.4 B → **2.651 GiB**。−25.05%。256 MiB ÷(39 万体 × 7 日)=98.3 B/体/日=約 1 行 ✓。次の手の案の妥当性: (a) 体ごと・日ごとの要旨の 1 行だけが単独で桁を合わせられる(それでも原因の行を足すとほぼ境目)。(b) 保持窓だけでは届かない(粒度 day で窓 0.66 日・each で 0.49 日が要る=自分の計算)。(c) 宣言の割り当ては 10 倍以上。=(a) か (a)+(b) を親の判断の材料に。再開を止める理由(器が表の写しでなくなる=目印の時刻が表から作れない)は妥当。
- (g) 性能: `perf_side.json` の値は記録と同じ(+10.1%・+13.8%)=参考値(ばらつき未測定・同じ機械で他の作業木が動いていた)のまま。腕 memory の増えの一部は L3。
- (h) 許可の外を触った 3 本: `run.py` の `POPULATION_RNG_DOMAINS` に 1 行(`test_every_rng_domain_in_src_is_classified` が新しい用途名の分類を求める=要る・母集団の側の分類は人の性質として妥当)・`rng_audit.py` の `SAFE_SITES` に 1 項(`k19_counter_array` で 0 語目を空け 1 語目に体の番号・2 語=静的に安全・凍結の数の試験が求める=要る・他の項は不変=監査を弱めていない)・`tests/engine/body/test_system1_placeholders.py`(Percept の空の欄の凍結に 1 つ足しただけ=完全一致の検査のまま)。ほかに `tests/engine/speech/test_speech_port_schema.py` の腕の行の列も足した(記録 §1 の表にある)。`relations.py` は読み口 `_partner_rows` 1 つと幅 `width`(既定は `rel_partner` の幅=挙動は同じ=§1 で確かめた)。`cli.py`・`perception/facts.py`・状態台帳の末尾・台帳 +15 行は記録 §13 と `git diff --stat` が合う。識別子に新しい `open`・`tick` は無い(`tick` は親の `RelationLayer` の引数名を上書きで受けるものと既存の名だけ)。記録に絶対パス・ホスト名・個人名は無い・LF。

**rebase の見込み**(本体 `0239a3b..35aa748` と作業木の変更の重なり 6 本): 衝突しそう=`state_ledger.py`(`_EXT` の末尾=CAL と M0M・M0C・M0X、`EXCLUDED` の末尾、冒頭の行数の注)・`tests/engine/test_state_ledger_10b.py`(外の状態 116+3=**119**・全体 207+3=**210**・鍵の列 `…"BD", "CAL", "M0M", "M0C", "M0X"`)・`cli.py`(`run_kind` の式の末尾=暦の影と記憶の腕の 2 項)・`docs/design/bridging-ledger.json`(末尾=W20cal の行と DOC-mr65-*)。自動で合う見込み=`run.py`(別の場所)・`tests/perception/facts/test_percept_schema.py`(別の hunk)。CAL は腕の行でない=`test_speech_port_schema` の腕の行の列は変わらない。

## 9. 欠陥(重さ順)

**高**: 無し。

**中**

- **M1 人ごとの忘れる速さの seed がプロセスの大域の値**(`src/shibuya/engine/memory_m1.py` の `_STATE["rate_seed"]`・`bind_rate_seed`・`src/shibuya/cli.py` の `bind_rate_seed(pop_seed)`)。自分で実行時に確かめた(合成の世界・腕 m1・用途名 `memory.forgetting_rate` の鍵を作った seed): `run_day(population_seed=5)` を直に → **0**・`cli.run(population_seed=7)` → 7・その後の `run_day(population_seed=9)` → **7(前の値が残る)**。10f S1(母集団の側の乱数は母集団の seed から)が腕のランで崩れる。実行時の分けの検査(`tests/engine/test_salt_seed_split_10f.py` の `_check_split`)は腕を回さない。記録 §14 の 6 は「直に呼ぶランは 0」までしか書いていない(残りの方は申告に無い)。直し: 組み立て(`MemoryLayer._enable_mr65` に run_day の母集団の seed を渡す=`build.py` の 1 行は親)で置き、`cli.run` の大域の bind をやめる・腕 m1 で `_check_split` を回す試験を 1 本・台帳 `DOC-mr65-m4-rate-variation` の「seed=母集団の seed」を実態に合わせる。
- **M2 上限なしの腕(人も記憶)の器が複数日で太る・バイト予算の宣言が無い**(`memory_store.py` の `_make_room`・`_forgettable`・`_resize`)。満杯の体が 1 体でも出ると**全員の**幅を倍にする。「忘れる」の判定は出来事の行にも見覚えの式(d=0.35・重要度の β・W_CUE)を使う=自分の計算で、1 回きりの出来事の行が消えるまで重要度 1 で約 1.7 年・2 で約 7.2 年・4 で約 127 年=ランの長さの中では出来事の行はほぼ消えず、幅は単調に増える。自分の 5,000 体・3 日の通しで、器の行は 1 日あたり約 3.8 万行(体あたり約 7.7 行)ずつ増え、体あたりの最大は 58(1 日目)→ 99(3 日目)・消した行 0。この増え方なら 4〜5 日目に最大の体が 128 を超えて全員の幅が 256 になる(推測=線形の外挿)。器の行 46 B+目印の seq 4 B+録画 8 B+M1 の時刻 24 B=約 82 B/行 → 39 万体 × 幅 128 で約 4.1 GB・幅 256 で約 8.2 GB(推測)。腕 m1 だけでも行 M0M が 39 万体 × 128 行 × 24 B=約 1.2 GB 増える。直し: 既定化の前に 5,000 体・7 日の幅とバイトを測って予算(S1・P4)に宣言・出来事の行の忘れる判定を種類ごとに決める(MR12)・体ごとの可変の幅か CSR を候補に。
- **M3 腕 memory のランで器 M0 の行が挙動を決めるのに、行 M0 の軸が既定のまま**(`state_ledger.py` の行 M0=軸 1 NO・hash_skip・軸 2 derivable)。腕 memory では会話の相手選び(`PeopleRelationLayer`)と出来事の想起が表の写しでない器の行から決まる=behavior-hash は人の行と器の出来事の行を見ない(入るのは M0M の時刻だけ)。再開は止めているので軸 2 の害は無いが、軸 1 の宣言が腕のランで実態と違う。粒度 day も行 M0 の derivable が成り立たない(再開を止めているので害は無い)。直し: 腕 memory の器の行を腕の行(腕 memory-people・behavior・required)として宣言するか、少なくとも行 M0 の注と記録に書く。
- **M4 発注 4 の「店 32 件の固定の上限を外す道(腕)」を作っていない**(`sm_*` は器の外のまま)。記録 §4・§2 は「店を器に入れるのは本段の外」と書くが、発注の範囲の中=「できなかったこと」に入っていない。直し: できなかったことに移して親の判断へ(回答 10-12 の 6-2 の M1 も「人と店と出来事を同じ器に」)。

**低**

- **L1** 腕の名が manifest の設定の節にも設定の指紋にも無い(観測の `mr65` だけ)。再開の取り違えは §4 のとおり止まるが、埋め込みのモデル名(30m/130m/ngram-test)の取り違えは止まらない(`_vec` は hash_skip=再開で今のモデルで作り直す)。反実仮想の入力の一致(3-3 `input_match`)も腕の差を設定の差として見ない(ランの種類の差で落ちる=保守的)。直し: 既定化の版上げで指紋に・モデル名を行 M0C か指紋に。
- **L2** M0 との上位 k の一致は「両方とも空」を「順まで同じ」に数えている(除くと 51.5%・72.9%・66.0%)。記録 §10 の表に注を。
- **L3** `relations_people.py` の `_partner_rows` は相手だけ要るのに `people_rows(…, 0)` で強さを 2 回計算する(`choose_talk_partners` は直後に `activation` でもう 1 回)。腕 memory の +14% の一部。直し: 強さを計算しない読み口を。
- **L4** `memory_m1.PARAMS` の `"kinds"` の中の dict は書き換えられ、`M1State.summary` の写しは同じ物を指す(計算は `KIND_SPECS` を使う=害は無い)。直し: 中も `MappingProxyType` か深い写し。
- **L5** `Percept` の版 /1 → /2 で既定のランの manifest の設定の節 `percept` の値が変わる(鍵は不変・宣言済み=仮採用 9)。親が承認を。
- **L6** 記憶 off のランで 6-5 の腕を立てても止まらない(記憶の層を作らない=検査が走らない)のに、`cli.run` のランの種類は「腕」になる。モジュールの注の「黙って効かないランを作らない」と食い違う(記録の仮採用 8 は宣言済み)。直し: `cli.run` か組み立てで記憶 off と腕の組み合わせを止める。
- **L7** 台帳の id の段の名が混ざる(`DOC-mr65-m4-recognition`=発注の M4・`DOC-mr65-m4-rate-variation`=6-2 の M4)。既定化の時に 6-2 の名へそろえる。
- **L8** 作業木の `_bc/` は git の外だが gitignore されていない(`??`)=写しの木の中に錨 3 本(検証側の空腹の錨の写しを含む)とテープがある。取り込みのときにステージしない・消す。

## 10. 親に確かめてほしいこと

1. 中 M1〜M4 の扱い(M1 は組み立ての 1 行=親の取り込みで直せる。M2 は 5,000 体・7 日の測りを既定化の前の条件に。M3 は台帳の宣言。M4 は発注の範囲の確認)。
2. Ruri の重みの転送先 `us.aws.cdn.hf.co` を許可の一覧に足すか(回答 10-12 の 2-1 は「埋め込みの Ruri は手元で動かしてよい」=CLAUDE.md §7 の転送先の規則との調整はユーザー)と、torch・transformers の置き場(本体の venv か別か)。
3. Petrov 2006 の式 (3) の一次確認(自分の記憶の式とは 1e−16 で一致=原典は読んでいない)。
4. rebase の衝突 4 本(§8 の末)と、合わせた後の数(外の状態 119・全体 210)。
5. 粒度の次の手は (a) か (a)+(b)(§8 (f)=保持窓だけでは届かない)。
6. 自分の確認で、本体の data の更新時刻の一覧(名だけ・深さ 4)を 1 回取ったときに `data/realworld_live/` の下の名が出た(中身は開いていない・本段の変更とは無関係の他の処理の更新)。
