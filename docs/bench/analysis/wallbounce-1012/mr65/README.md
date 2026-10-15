# 第 6 期 6-5 記憶 MR の GPU の前に作る分(M1・M2・M4 のコードと M3・M5 の器)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `6-5/memory-m1-m5-arms`(土台 HEAD `0239a3b` → 検収の直しの後に本体の最新 `ed7155c` → さらに `54ba3db`(=`86fcff3`+文書だけ)
  =`76d3899`+文書だけの 1 本へ rebase=§16)。commit は親。
- 独立検収の記録は [review.md](review.md)(条件つき受入・中 M1〜M4・低 L1〜L8)。直しは §16(親の判断=中は全部直してから取り込む)。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-6(MR-0・MR1・MR2・MR3・MR4・人も記憶の一つ・MR6・MR8・MR10・MR11・MR12・MR13・MR16)・[回答 10-12](../../../../design/v2-plan-answers-2026-10-12.md) の 6-2(段 M0〜M5)と 6-4(第 6 期のコードを GPU の前に=腕で)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) の 6-5 の行・[記憶の草案](../../../../design/v2-memory-rework-design-round-draft.md) の〔答え〕・[R-87](../../../../research/v2-r87-recall-relationship-decay-copresence.md)(ACT-R の式と :bll・Ruri の表)・[R-68](../../../../research/v2-r68-memory-rework-anchors.md)(Sense 2018 の 15%)。土台の記録は [m0](../m0/README.md)・[md23](../md23/README.md)。
- **全部 腕**(既定=今のまま)。MR10=各段をまず腕で入れて 1 つずつ測り、まとめて 1 回で既定にする。
- 数は実測。生の出力(テープ・状態のファイル)は作業木の `_bc/`(直しの前)と `_bc2/`(直しの後=回し終えて中身を消した)に置いた(git の外)。このフォルダには比べた結果と道具だけを置く(絶対パスなし)。道具は [tools/](tools/)。

## 0. 結論

- 腕を 5 つ足した: `--memory-model {m0,m1}`・`--memory-cue {id,embed}`(+`--memory-embed-model {ruri-v3-30m,ruri-v3-130m,ngram-test}`)・`--memory-people {table,memory}`・`--memory-grain {each,day}`。どれも記憶の器のラン(`--memory on`+`--memory-store events`)でだけ効く。既定は全部今のまま。
- **既定の腕で結果不変**: byte-check 19 構成で 25 欄とも本体 HEAD と同じ(19/19・[byte_check_mr65.json](byte_check_mr65.json))。5,000 体・2 日の通しも HEAD と全部の欄が同じ([two_days_head_vs_mr65.json](two_days_head_vs_mr65.json))。2 日の日の境目の再開=通し(既定と腕 m1 の両方・5,000 体)。
- **M1**(強さの式): ACT-R の折衷形(直近 3 回は本当の時刻・古い分は近似=Petrov 2006 の式 (3)=親が原典で一次確認 ○)・時刻は秒・+1 なし・最短の符号化時間 1 秒・d=0.5(ACT-R マニュアルの :bll の推奨値)・忘れる速さの人ごとのばらつき 15%(Sense 2018・Philox・seed=ランの母集団の seed を組み立てが渡す=§16 M1)・種類ごとの d と足す項・境目 τ は仮の値 −3.738(M0 の τ と「n=1・初めての成功の行」が同じ時刻に越える値=人のデータで較正していない)。5,000 体で M0 の上位 k と順まで同じ想起は 52〜73%(両方とも空を除くと 51.5・72.9・66.0%=§10)。
- **M2**(手がかり): 既定は ID の一致のまま(1-6 の同値の試験が通る)。腕 embed は意味の手がかりだけ(一致=cos ≥ 0.5・score に 1.0 × cos)。手がかりの文は会話中=相手の直前の発言・ほか=本人の直前の理由。**Ruri-v3 の重みは取得していない**: `model.safetensors` は huggingface.co から `us.aws.cdn.hf.co` へ転送される=許可の一覧の外(CLAUDE.md §7)。版(commit と重みの sha256)だけ固定し、Ruri の道は未試験。経路の試験は試験用の代わり `ngram-test`(文字の n-gram=意味ではない)。pip も使っていない(torch が要るのは重みの後)。
- **M4/M5**(思い浮かぶ/見覚え・人も記憶の一つ=器): 思い浮かぶ=A ≥ τ・見覚え=親しみの種類(d=0.35)に目の前の手がかり 1.0 を足すと超える・忘れる=見覚えにも 1.0 届かない行を消す。腕 memory は人を同じ器・同じ式で持ち、関係の表(`rel_*`)を読まない・書かない(AST と負の対照)。出来事 128 行と店 32 件の固定の上限を外した: 満杯の体は忘れた行を消し、足りなければ全員の幅を倍に(5,000 体・1 日で幅 8 → 64 でも呼数は同じ)。〔検収 M2・M4〕倍にするのは種類ごとの上限(出来事・人・店の各 256 行/体=expedient)まで・その種類が上限に届いた体は思い浮かぶ強さ A の一番低い行を消す・店の行は器の店の行の表(§4・§16)。5,000 体・7 日の通しで器の幅 128 → 256(7 日目)・体あたりの出来事の行の最大 135・人 18・店 45・消えた行 0(§7)。
- **M3**(印象と寝たときの書き直し)と**浅い痕跡**は器と口だけ(ランに結線していない・mock の試験)。`Percept` に見えない欄 `heard_referents` を足した(版 /2・値は空・描画は不変)。
- **粒度の案**(腕 `--memory-grain day`=同じ記憶の行は日に 1 行): 体の出来事は 14.58 → 10.93 行/体/日(−25%)。39 万体・保持窓 7 日の見積りは 3.59 → 2.65 GiB=1-3 の宣言 256 MB はまだ大きく超える(§7)。
- 試験: 新しい試験 52 本(`tests/engine/memory/` の 7 ファイル・slow 1・重みが無くて skip 1)+検収の直しの試験(§16)。範囲の試験(`tests/c8`・`tests/economy/cp2` を含む)は §12。`lint-imports` 5 契約とも守られている。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/memory_m1.py`(新) | 腕の切替口(`arms`・`set_arm`・`arms_on`・`check_arms`・〔検収 L1〕`config_of`・`FP_KEY`=〔検収 M1〕`bind_rate_seed` は消した)・M1 の式(`base_level`=折衷形・`exact_base_level`=参照)・`touch_times`・`forgetting_scale`(Philox・15%)・`tau_from_m0`・思い浮かぶ/見覚え/忘れる/言葉(`recall_mask`・`recognize_mask`・`forget_mask`・`clarity_words`)・種類の表 `KIND_SPECS`・器の子の持ち主 `M1State`(直近の時刻・人ごとの倍率) |
| `src/shibuya/engine/memory_embed.py`(新) | 埋め込みの口 `Embedder`・`RuriEmbedder`(版の固定 `RURI_PINS`・重みが無ければ `EmbedUnavailable`)・試験用の代わり `NgramEmbedder`・器の子の持ち主 `CueState`(手がかりの文・行の埋め込み・控え) |
| `src/shibuya/engine/relations_people.py`(新) | `PeopleRelationLayer`(`RelationLayer` の子=器の人の行から関係の読み口を作る・関係の表を読まない) |
| `src/shibuya/engine/memory_impression.py`(新) | M3 の器 `ImpressionBook`(会話の直後の追記・寝たときの書き直し・昼の結論・原因は `LlmCall`) |
| `src/shibuya/engine/memory_trace.py`(新) | 浅い痕跡 `shallow_trace`(出来事の記録から組み立てる・保存しない)・`trace_word`・計器 `played_along_share` |
| `src/shibuya/engine/memory_shops.py`(新・検収 M4) | 店の評価の行の表 `ShopTable`(器の子の持ち主 `shops`・状態台帳の腕の行 `M0S`)・`UncappedStoreMemory`(`StoreMemory` の子=行の口 `columns`・`_evict_slots`・`_put` だけ差し替え) |
| `src/shibuya/engine/store_memory.py`(検収 M4) | 行の読み書きを口 `columns`(既定=体の表の `sm_*` そのもの)・`_evict_slots`(既定=score の最小)・`_put`(既定=`resolve.write_store_memory`)に通した=既定のランは同じ配列・同じ計算 |
| `src/shibuya/engine/store_choice.py`(検収 M4) | 7c の想起の読み口を `store.columns(agents)` に(既定=同じ配列) |
| `src/shibuya/engine/systems/build.py`(検収 M1・L1・L6) | 器に母集団の seed を渡す・腕の設定を設定の指紋 `memory_mr65` に(既定と違う腕のときだけ)・記憶 off のランで腕を立てたら止める |
| `src/shibuya/engine/manifest_sections.py`(検収 L1) | `memory_summary` の設定の子に `mr65_arms` |
| `src/shibuya/engine/memory_store.py` | 腕の子の持ち主と設定(`m1`・`cue`・`uncapped`・`grain`・`enable_arms`=組み立てで 1 回)・`remember`(人の行の鍵・`keep_pointer`=粒度 day・上限なしの空き作り・M1 の時刻・要旨の埋め込み)・`recall`(M1 の強さと τ と言葉・意味の手がかり・人の行を出来事の想起に出さない・M1 で店の行の尺度をそろえる)・`seed_people`・`people_rows`・`pointer_same_day`・`note_cue`・上限なしの `_resize`・`_delete_rows`・`_forgettable`・`_make_room`・`check_against_table(kept=)`・`rebuild`(上限なしと粒度 day は止める・埋め込みの作り直し)・manifest `mr65`・`render_memories(words=True)` |
| `src/shibuya/engine/memory.py` | `__init__` の腕の検査・`_enable_mr65`・`enable_relations`(腕 memory は `PeopleRelationLayer`)・`_recall_from_store`(手がかりの文・店の行の番号の底・粒度 day の描く時刻)・`_write`(粒度 day=日の 2 回目からは記録に書かない・上限なしは表と比べない・人の行に触れる)・`_touch_people`・`note_attended`(MR6 の口)・`note_utterance`(手がかりの文) |
| `src/shibuya/engine/relations.py` | 読み口 `_partner_rows` を 1 つ足し、`choose_talk_partners` の相手の配列と幅をそこから取る(既定は `rel_partner` の写し・幅=k=挙動は同じ) |
| `src/shibuya/perception/facts.py` | `Percept.heard_referents`(空の欄・`EMPTY_FIELDS` の末尾)・`PERCEPT_SCHEMA` /1 → /2 |
| `src/shibuya/cli.py` | 腕の引数 5 つ・`cli.run` のランの種類に 6-5 の腕を数える(〔検収 M1〕人ごとの倍率の seed を置く 3 行は消した=組み立てが渡す) |
| `src/shibuya/engine/state_ledger.py` | 行 `M0M`・`M0C`・`M0X`・〔検収 M4〕`M0S`(外の状態の末尾)・持ち主 3 つ・子クラス 2 つ・除外 11 項・〔検収 M3〕行 M0 の注 |
| `src/shibuya/engine/run.py` | 乱数の用途名の表 `POPULATION_RNG_DOMAINS` に `memory.forgetting_rate` を 1 行 |
| `src/shibuya/engine/rng_audit.py` | 静的に安全な呼び手の表 `SAFE_SITES` に `forgetting_scale` を 1 行 |
| `docs/design/bridging-ledger.json` | 末尾に 17 行(`DOC-mr65-*`・§8=検収の直しで 2 行足し、id の段の名を 6-2 の表に合わせた) |
| `tests/engine/memory/`(新 7 ファイル+共通 `_mr65.py`) | §12 |
| 凍結の数の試験(増えた分だけ) | `test_state_ledger_10b.py`(行の数=rebase の後の本体 116・207 → 120・211・鍵の列と腕の行)・`test_speech_port_schema.py`(腕の行)・`test_state_checks_10f.py`(SAFE_SITES 15→16)・`test_percept_schema.py` と `tests/engine/body/test_system1_placeholders.py`(Percept の欄と版)・`test_m0_store_schema.py`(器の slots に子の持ち主 3 つ)・`test_env_and_sections_10f.py`(〔検収 L1〕`CONFIG_PATHS_SHA256`=設定の道筋 1 本) |

## 2. M1 強さの式と parameter

```
B = ln( Σ_{j ≤ k_i} t_j^(−d) + [n > k_i]·(n − k_i)·(t_n^(1−d) − t_k^(1−d)) / ((1 − d)(t_n − t_k)) )   (t は秒・t ≥ T_MIN_S)
A = B + β_種類                       思い浮かぶ: A ≥ τ
A_fam = B(d = D_FAMILIAR × 倍率) + β   見覚え: A_fam + W_CUE ≥ τ(目の前の手がかりのある人)
忘れる(消す): A_fam + W_CUE < τ − FORGET_MARGIN(上限なしの腕で満杯の体に空きを作るとき)
```

| 値 | 中身 | 出典/印 |
|---|---|---|
| d=0.5 | 忘れる速さ(出来事・人・印象) | ACT-R 7 参照マニュアルの :bll の推奨値(R-87 §1-1・Anderson & Schooler 1991 の値ではない) |
| 折衷形 | 直近 k 回は本当の時刻・古い回は寿命から近似(k=0 なら式 (2) `ln(n·t_n^(−d)/(1−d))`) | Petrov 2006 の式 (3)(R-87 §1-1)=**親が一次確認 ○(第336)**(原典=ACT-R users の添付 PDF・式 (3)=ln[Σ_{i≤k} t_i^{−d}+(n−k)(t_n^{1−d}−t_k^{1−d})/((1−d)(t_n−t_k))]・k=0 で式 (2)・d=0.5 で式 (4)) |
| k=3 | 直近の回数 | expedient(R-87 §1-3 の例)・`DOC-mr65-m1-k-recent` |
| T_MIN_S=1 秒 | 最短の符号化時間(t=0 を避ける) | expedient・`DOC-mr65-m1-t-min` |
| 倍率 1+0.15·z | 忘れる速さの人ごとのばらつき(z=Philox の標準正規・±3σ で切る・鍵=体の番号・seed=ランの母集団の seed=〔検収 M1〕組み立てが `enable_memory_store(population_seed=…)` で渡す) | Sense, Meijer & van Rijn 2018(.296±.046=15.5%・R-68 §4-1)=錨・切りと鍵は expedient・`DOC-mr65-m4-rate-variation`(6-2 の M4=個人差) |
| β | 出来事=0.5 × 重要度(M0 の score の w_i)・人と印象=0 | MR1 (d) の形・値は expedient・`DOC-mr65-m1-kind-table` |
| τ=−3.738 | 境目(全員同じ) | 仮の値=`tau_from_m0(−2.0)`(M0 の n=1 の行が τ を下回る 217 分と、M1 の「n=1・重要度 2」の行が下回る時刻を同じにする)・人のデータで較正しない(検証側)・`DOC-mr65-m1-tau-provisional` |
| D_FAMILIAR=0.35・W_CUE=1.0・FORGET_MARGIN=1.0 | 見覚えと忘れる | expedient=1 回だけ会った人(倍率 1)は思い浮かぶ約 29 分・見覚え約 9 日・消えるまで約 5 か月・`DOC-mr65-m1-recognition`(〔検収 L7〕旧 id `-m4-recognition`) |
| CLEAR_MARGIN=1.0 | 「はっきり」=A ≥ τ+1・「うろ覚え」=τ ≤ A < τ+1 | expedient |

- 単位: 正確な式も折衷形も、時刻の単位を c 倍にすると全部の強さが −d·ln c だけ同じにずれる(試験 `test_units_shift_all_strengths_by_the_same_amount`・負の対照=M0 の式はずれ方が経過で違う)。
- 器の行ごとの直近の時刻は `M1State._t_ns`(i8 × 3)。M0 の器は記憶の表の写しのままで、追い出しは表と同じ M0 の score(器と表の行をそろえるため=仮採用)。M1 が変えるのは想起の候補・順・言葉。
- 1 回の行の残る時間(倍率 1): M0 は重要度によらず 3.6 時間。M1 は初めての成功 3.6 時間(τ の決め方のとおり)・初めての会話 約 10 時間・初めての失敗 約 27 時間(重要度の項が境目の側に入る)。
- 言葉(MR-0): 器の `MemoryView.clarity` に「はっきり/うろ覚え」。描き方の口 `render_memories(words=True)` は「(うろ覚え)」「(要旨だけ)」を項の頭に付ける。**今の描画(`perception/renderer.py`)には結線していない**(LLM に見せるのは描画の 1 か所=テンプレの版が動く=親の判断)。
- 店の評価の行(今の `sm_*` と今の式=腕 memory では器の店の行の表=§4)は、M1 の腕では score を境目の差(τ_M1 − τ_M0)だけずらして出来事と同じ順に並べる(仮採用・`DOC-mr65-m1-shop-scale`)。店の行の強さを M1 の式にするのは本段の外(店の記憶の式のまま)。

## 3. M2 手がかりと埋め込み

- 既定(`id`): その場の手がかり(相手・対象・セル・直前の結果=今の 6b の q)。腕を作らない=埋め込みを計算しない(試験 `test_default_cue_computes_no_embedding`=埋め込みの口を落とす口に替えても既定のランは通る)。
- 腕 `embed`: 意味の手がかりだけ(ID の一致は使わない=MR6 の後段の「ID で引く単純化 ↔ 意味の手がかりだけの腕」の比べ)。一致=`cos(手がかりの文, 行の要旨) ≥ COS_MATCH`(0.5)・score に `W_CTX × cos`(1.0)。行の埋め込みは要旨(会話の 40 字)を置いたときに 1 回のバッチ(印象は M3 の器の口)。手がかりの文の埋め込みは控え(LRU 4,096)。float16 に丸めて持つ(決定論の手当て)。
- 手がかりの文(MR2 問い 4): 会話の番の口(`note_utterance`)から、聞き手には話し手のひと言・話し手には理由。語彙 v3 はひと言が無いので、会話中も本人の理由に戻る。**判断の呼の理由と予定の文は口へ結線していない**(系 `llm_io`・`judge` は範囲の外)=5,000 体の腕 embed で手がかりの文のある想起は 3〜5%(§10)。
- Ruri-v3(2026-10-15 に huggingface.co の API と HEAD で確かめた・**重みは取得していない**):

| 名 | リポ | commit | model.safetensors の sha256(X-Linked-ETag)・大きさ | 次元 | ライセンス | base |
|---|---|---|---|---|---|---|
| ruri-v3-30m | cl-nagoya/ruri-v3-30m | `24899e5de370b56d179604a007c0d727bf144504` | `e94155e342cbfc33280c345c6e2912905fb5de6e1a3adeb938f395aafd2f8832`・146,828,152 B | 256 | Apache-2.0 | cl-nagoya/ruri-v3-pt-30m |
| ruri-v3-130m | cl-nagoya/ruri-v3-130m | `e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6` | `1c342581efc23d0b50b92fb11ac1eeb02719691bcc59bdc0dc0b09a36b4fc6d1`・528,573,472 B | 512 | Apache-2.0 | cl-nagoya/ruri-v3-pt-130m |

  - 取得しなかった理由: `…/resolve/<commit>/model.safetensors` は `302` で `https://us.aws.cdn.hf.co/xet-bridge-us/…` へ転送される(HEAD で確かめた)。CLAUDE.md §7「一覧の外(転送先や保管先が別ドメインの場合を含む)なら取得せず先に聞く」=止めた。`config.json`・`tokenizer.json` は huggingface.co の中(`/api/resolve-cache/…`)で返るが、重みが無いと使えないので取っていない。
  - 置き場の予定: `data/models/ruri/<名>@<commit>/`(gitignore の下)。読み方(未試験): transformers の `AutoModel`・平均の pooling(`1_Pooling/config.json` で確かめる)・接頭辞「検索クエリ: 」「検索文書: 」(モデルカードで確かめる前の仮)・CPU・スレッド 1・決定論のアルゴリズム。依存(torch・transformers)は本体の venv に入れていない(pip は使っていない)。
  - 試験 `test_ruri_close_sentence_ranks_first` は重みがあるときだけ走る(今は skip)。

## 4. M4 思い浮かぶ/見覚え・M5 人も記憶の一つ(器=腕 `--memory-people memory`)

- 人の行: 器の行の種類 `PERSON_KIND`(13)・鍵は (種類, 相手)・対象の欄=関係の種類(世帯 1・職場 2・学校 3・常連 4・知人 5=重ねても前の値)・重要度 0・目印は仮の行(legacy)。触れる回=会話の番ごと・手伝い(MR6=注意が向いた 1 回=会話は自然に強く残る)。注意の口 `MemoryLayer.note_attended`(MR6 の同席=人の記憶だけ・店と予定と出来事は書かない)は**口だけ**(知覚の注意から呼ぶ結線は目の向きと空間の段の後)。
- 最初の関係はデータから(開始前の経験): `seed_people` が今の関係の層の機械的初期化(W16 の世帯・W17 の共在)の辺を人の行に入れる(n・最初・最後の時刻=負の時刻)。4-1 段 4 の `w21_relations_initial` は本体に無い=口は同じ(`DOC-mr65-people-initial`・外す段 4-1)。
- 関係の読み口 `PeopleRelationLayer`: `activation`・`edges`・`acquaintances`・`partners_in_cell`・`_partner_rows`(会話の相手選び)・`recognized`(見覚え)・`summary`(今の層と同じ鍵)を器の人の行から作る。親の `RelationLayer` で関係の表を読むメソッドは全部上書き(試験の AST)。知人出現の起床(既定 on)と同席の腕は作らない=要求は計器 `relations.counts.acq_wake_requested_unavailable` に出す(`acq_wake_on` は偽=系は起床を作らない)。連絡先の印は人の行の関係の種類から数えるだけ。好意の符号は持たない(0)。
- 上限なし: 出来事 128 行の上限を外した(体あたりの行の幅は全員同じで、満杯の体が出たら忘れた行を消し、それでも足りなければ幅を倍に=`_resize`)。
  - 〔検収 M2〕幅を倍にするのは種類ごとの上限(`memory_store.ROW_CAPS_DEFAULT`=出来事 256・人 256・店 256 行/体=expedient・感度の腕の口 `set_row_caps`)の和(器の行の幅は出来事+人で共有=512)まで。新しい行の種類(出来事/人)の行がその体で上限に届いていたら、**思い浮かぶ強さ A(M1・手がかり無し)が一番低いその種類の行を消して**入れる(同点は最後に触れた時刻=目印の時刻の古い順・次に行の番号=決定的・τ を下回る行が先に来る)。「忘れた=見覚えも無い」(`forget_mask`)で消す規則は前のまま(意味は変えない=満杯の体の空き作りの最初の段)。最初の関係(`seed_people`)も人の上限の中(超えれば止める)。計数: `m1_stats` の `grown`(幅を倍にした回・最初の幅の置き直しを含む)・`forgotten`・`evicted_by_a`・器の計数 `rows_resized`・`forgotten`・`evicted_by_a`(`:episode`・`:person`)・manifest の `mr65.capacity`。
  - 〔検収 M4〕**店 32 件の固定の上限を外す道**: 腕 memory で店の記憶のあるランは、店の評価の行を器の子の持ち主 `shops`(`engine/memory_shops.py` の `ShopTable`=状態台帳の腕の行 `M0S`=behavior・required)に書く。同じ作り=幅 32(`STORE_MEMORY_N`)から満杯の体が出たら全員の幅を倍に・上限 256 で**思い浮かぶ強さ A(店の記憶の式・手がかり無し)の一番低い行を上書き**(同点は最後の時刻の古い順・行の番号。親の既定の追い出しは score=A+0.5×min(4, 精度) の最小)。店の記憶の書き手・σ・減衰・読み口(7c の選び手・B5 の想起・伝聞)は前の式のまま=`StoreMemory` の行の口(`columns`・`_evict_slots`・`_put`)だけを子 `UncappedStoreMemory` が差し替える(既定のランは体の表の `sm_*` そのもの=同じ配列)。この腕では体の表の `sm_*` は書かない(空のまま・確保は今の組み立てのまま)。`DOC-mr65-m1-shop-uncapped`。
- 5,000 体・1 日(`v3_mem_rel` の腕・最初の幅 8): 幅 8 → 64(広げた回 3+最初の 1)・器の行 62,764・人の行 9,215(体あたり平均 1.84・最大 16)・最初の関係 8,861 本(世帯 2・職場 5,732・学校 3,127)・思い浮かぶ人 4,996 本(今の層の生きている辺 8,981 本)・呼数 64,689(最初の幅 128 のランと同じ=幅は挙動を変えない・final は行 M0M の配列の形が違うので違う)。試験 `test_world_5000_one_day_uncapped_grows_and_reads_people`(slow)。
- 再開は止める(器が記憶の表の写しでない=表から作り直せない=本段の限界・`DOC-mr65-m1-people-limits`)。
- 5,000 体・1 日(`v3_mem_rel` の腕 people・最初の幅 128)の final は直しの前と同じ `16434de8b0643c7c`(§16=上限に届かない・店の記憶 off の構成)。店の記憶 on の構成(`v3_mem_store` など)は店の行が体の表 `sm_*`(behavior-hash に入る)から器の店の行の表(腕の行 M0S)へ移るので final は変わる(§16)。

## 5. M3 の器(印象と寝たときの整理)

- `ImpressionBook`: 会話の直後に短く足す(`after_conversation`=原因はその会話の番の `LlmCall`)・本人が寝たときに、前の書き直しの後に追記のあった相手だけ書き直しの口(`rewrite`=LLM の呼び)を呼び、書き直しを**足す**(古い要約も残る)・今の印象=最後の書き直し・昼の結論は意味の記憶へ(`add_conclusion`・MR13 (c))。原因が `LlmCall` でなければ `TypeError`(同席だけ・エンジンの規則では書かない=MR3)。文の長さは切らない(MR13=128 の上限をやめる)。印象の埋め込みの口(MR2 問い 3)。
- **ランに結線していない**(GPU が要る段=回答 10-12 の 6-2)。試験は mock の書き直しの口(`test_impressions_are_appended_and_rewritten_on_sleep`)。

## 6. 注意を向けずに見ていた人(浅い痕跡)

- `shallow_trace(log, viewer, target, t0, t1)`: 出来事の記録から、2 人の行を時刻の窓で引き、同じ場所(`where`)に 1 刻み以内で居た回を組み立てる(回数・最初と最後・場所)。保存しない。記録に居場所が載るのは体の出来事の腕(2-3 の腕 a)のランだけ。視野(目の向き)は空間の段の後=今は「同じ場所に近い時刻」で近似(`DOC-mr65-trace-window`)。
- 見せる言葉 `trace_word`: 注意を向けた記憶=空文字(普通に描く)・浅い痕跡だけ=「見たような気もする」・何も無い=空文字。
- 話し手の指した相手の見えない欄: `Percept.heard_referents`(`(発話の出来事の目印, 指した相手の id の組)` の列・空の欄・描画しない)。値を作る口(話し手の発話の形)は会話(6-4 C1)と空間の段の後。`PERCEPT_SCHEMA` を /2 に上げた(manifest の `percept` の欄の数と名が 1 つ増える=設定の節の値が既定のランでも変わる=byte-check の 25 欄の外・final とハッシュとテープは不変・〔検収 L5〕親の承認待ちの宣言=仮採用 9)。
- 計器「LLM が覚えていないのに話を合わせた割合」: `played_along_share`(値は実 LLM の後)・manifest の `memory_summary.memory_store.mr65.played_along_share`(今は null)。

## 7. 保持窓と粒度の案と見積り(2-3 の 14.6 行/体/日)

腕 `--memory-grain day`: 同じ記憶の行(同じ鍵)は日に 1 行だけ記録へ書く。2 回目からは目印を日の最初の回のまま(`keep_pointer`)・回数と M1 の時刻は進める・描く時刻は記憶の表の最後の回(B5 の文は変わらない)。保持窓の外の行は 2-3 の「要旨だけ」のまま。再開は止める(目印の時刻が表から作れない=本段の限界)。

5,000 体・seed 1・`v3_mem_rel`・2 日(連続する平日)([grain_side.json](grain_side.json)・[grain_estimate.json](grain_estimate.json)=器の無い既定のランの行を引いた体の出来事だけ):

| 腕 | 体の出来事(1 日目・2 日目) | 行/体/日 | LLM の原因の行の割合 | B/体/日 | 39 万体・7 日(推測=線形の外挿) |
|---|---|---|---|---|---|
| each(今の腕 a) | 72,048・73,761 | 14.58 | 63.9% | 1,413 | 3.59 GiB |
| day | 55,497・53,785 | 10.93 | 60.0% | 1,042 | 2.65 GiB |

- 1 日の比べ(4 構成・[arms_moved.json](arms_moved.json)): 記録の全部の行は `v3_mem_store` 122,892 → 107,344・`v3_mem_rel` 125,991 → 109,440・`v3_classical_mem_rel` 113,564 → 104,284(減った行=目印を前のままにした回=`pointer_kept`)。final・呼数・テープの既存の列は同じ(動いたのは full-hash=行 M0L の seq と、目印の列 `recalled_event_ids` だけ)。
- **粒度 day だけでは 1-3 の宣言(256 MB)に届かない**。256 MB を 39 万体・7 日で割ると体あたり約 98 B/日=約 1 行/体/日。親の判断の材料: (a) 体ごと・日ごとの要旨の 1 行(その日の記憶の行の目印の束)に縮める・(b) 保持窓を短くし、窓の外は器の要旨だけ(2-3 の M3)・(c) 宣言(S1)の割り当てを増やす。どれも未リサーチ。
- 逐次ループ: 記録への 1 行ずつの `append` は 1-3 の口のまま(粒度 day は呼ぶ回数が減る)。

### 7-2. 粒度の次の手の見積り(〔検収・親の判断 5〕既定化の前に決める=並べるだけ)

256 MiB(1-3 の宣言)を 39 万体・7 日で割ると 98.3 B/体/日=記録の行(72 B)で約 1 行。行のバイト=記録の行 72 B+LLM の原因の行 39 B × 原因のある行の割合。全部 推測(線形の外挿)・未リサーチ。

| 案 | 行/体/日 | B/体/日 | 保持窓 | 39 万体 | 256 MiB との比 |
|---|---|---|---|---|---|
| 今(each=2-3 の腕 a) | 14.58 | 1,413 | 7 日 | 3.59 GiB | 14.4 倍 |
| 粒度 day | 10.93 | 1,042 | 7 日 | 2.65 GiB | 10.6 倍 |
| (b) 保持窓だけ(each) | 14.58 | 1,413 | 0.49 日で 256 MiB | — | 1 |
| (b) 保持窓だけ(day) | 10.93 | 1,042 | **0.66 日**で 256 MiB(検収役の値と同じ) | — | 1 |
| (a) 体ごと・日ごとの要旨の 1 行(原因の行なし) | 1 | 72 | 7 日 | 187.5 MiB | 0.73 |
| (a) 同(原因の行つき) | 1 | 111 | 7 日 | 289.0 MiB | 1.13(境目) |
| (a)+(b) 窓 3 日 | 1 | 72〜111 | 3 日 | 80.4〜123.9 MiB | 0.31〜0.48 |
| (a)+(b) 窓 1 日 | 1 | 72〜111 | 1 日 | 26.8〜41.3 MiB | 0.10〜0.16 |

- (b) 単独で桁を合わせるには窓を 1 日より短くする必要がある(day で 0.66 日・each で 0.49 日)=1 日の中の想起の目印が窓の外に出る。単独で桁を合わせられるのは (a) だけ(原因の行を足すと境目)。(a)+(b) なら窓 3 日でも宣言の半分以下。決めるのは親(既定化の前)。

### 7-3. 〔検収 M2〕上限なしの腕のバイト予算(親が予算の宣言の文書に写す)

器の行のバイト=器の行 32 B(目印 12・回数 2・重要度 1・最初の時刻 8・出どころ 1・録画 8)+仮の出来事の中身 14 B+記録の目印の seq 4 B+M1 の直近の時刻 24 B(i8 × 3)=**74 B/行**(検収役の「約 82 B」は録画 8 B を 2 回数えた)。店の行=体の表の `sm_*` と同じ 23 B/行(宣言 24 B)。器の行の幅は全員同じ(出来事と人で共有=上限は出来事+人の和)。

| 種類 | 最大の幅(行/体・expedient) | 行のバイト | 39 万体(390,067)× 最大の幅 × 行のバイト |
|---|---|---|---|
| 出来事(器の行) | 256 | 74 B | 7,389,429,248 B(6.88 GiB) |
| 人(器の行) | 256 | 74 B | 7,389,429,248 B(6.88 GiB) |
| 店(器の店の行の表) | 256 | 23 B | 2,296,714,496 B(2.14 GiB) |
| 器の幅の上限(出来事+人=512) | 512 | 74 B | 14,778,858,496 B(13.76 GiB) |
| 人ごとの倍率(M1) | — | 8 B/体 | 3,120,536 B |

- 含まないもの: 注釈(会話の要旨=体あたり 16 件までの dict)・埋め込み(腕 embed)・Python の入れ物の重さ(推測)。
- 既定化の条件(親の判断)=下の 7 日の測りと 39 万体の見積りが予算の中。**今は満たしていない**(器の幅 256 で 6.88 GiB)=上限の値・体ごとの可変の幅か CSR・出来事の行の忘れ方(MR12=種類ごと)の決め直しが既定化の前に要る(`DOC-mr65-m1-row-caps`)。

### 7-4. 〔検収 M2〕5,000 体・7 日の通し(mock・腕 memory+m1)

道具 [tools/capacity_mr65.py](tools/capacity_mr65.py)・[capacity_7d.json](capacity_7d.json)。構成=`v3_mem_rel`+店の記憶 on(店の行の表も測る)・seed 1。7 日は土日を含む=開始日の検査の規則の違反(連続する平日に収まらない)を止めずに記録に写して回した(2-3 の `--allow-rest-days` と同じ包み方=test_only)。final `91d5a09dcec3a6c5`・呼数 501,379。日の締めごとの値(最大の作業集合はプロセス全体=決定論でない):

| 日 | 器の幅 | 器の行 | 出来事の行 | 人の行 | 体あたり出来事 最大/p99 | 人 最大 | 店 幅/行/体の最大 | 消えた行 | 最大の作業集合 | 壁時計(通し) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 128 | 62,764 | 53,549 | 9,215 | 57/26 | 16 | 32/20,179/14 | 0 | 470 MiB | 75 秒 |
| 2 | 128 | 104,734 | 95,191 | 9,543 | 88/41 | 16 | 32/33,928/21 | 0 | 470 MiB | 162 秒 |
| 3 | 128 | 139,628 | 129,745 | 9,883 | 97/55 | 17 | 32/45,092/30 | 0 | 470 MiB | 252 秒 |
| 4 | 128 | 171,302 | 161,078 | 10,224 | 102/67 | 17 | 64/55,240/35 | 0 | 470 MiB | 342 秒 |
| 5 | 128 | 196,089 | 185,547 | 10,542 | 106/77 | 17 | 64/63,374/40 | 0 | 503 MiB | 424 秒 |
| 6(土) | 128 | 219,899 | 209,003 | 10,896 | 115/84 | 17 | 64/71,097/42 | 0 | 517 MiB | 509 秒 |
| 7(日) | **256** | 244,299 | 233,046 | 11,253 | 135/93 | 18 | 64/78,970/45 | 0 | 576 MiB(ランの終わり 694 MiB) | 599 秒 |

- 器の行は 1 日に 2.4〜4.2 万行(体あたり 5〜8 行)増え、7 日目に最大の体が 128 行を超えて全員の幅が 256 に(器の列 47.4 → 94.7 MB)。店の行の表は 4 日目に 32 → 64。消えた行 0(忘れた=見覚えにも届かない行も、上限 256 に届く体も無い)。3 日目までの値は検収役の 3 日の通し(器の行 139,628・体あたり最大 99=出来事+人)と同じ。
- 39 万体へ(推測=幅 × 行のバイト × 体の数): 器 幅 256 → 6.88 GiB・店 幅 64 → 0.53 GiB。7 日目より後も幅は上限 512(13.76 GiB)まで倍になりうる(出来事の行は消えないので体あたりの最大は単調に増える)。

## 8. 状態台帳・manifest・つなぎの台帳・CLI

- 状態台帳(外の状態の末尾に 4 行=3 行+〔検収 M4〕M0S・版は上げない=既定のランのハッシュと状態のファイルは不変・rebase の後は本体の行 CAL の後):
  - `M0M`(腕の行・腕 memory-model): `mem_layer.memory_store.m1._t_ns`・`._scale`=軸 1 behavior(想起の候補と順を決める)・軸 2 required(表から作れない)。
  - `M0C`(腕の行・腕 memory-cue): `mem_layer.memory_store.cue._heard`・`._own`(behavior・required)・`._vec`・`._qcache`(hash_skip=要旨から作り直す)。
  - `M0X`(diag・discardable): 子の持ち主の計数(〔検収 M4〕店の行の表の計数を含む)。
  - 〔検収 M4〕`M0S`(腕の行・腕 memory-people): `mem_layer.memory_store.shops._poi`・`_valence`・`_precision`・`_first`・`_last`・`_n`・`_source`=軸 1 behavior(店の選びと想起と伝聞が読む=体の表 `sm_*` の代わり)・軸 2 required(腕 memory は再開を止める=器の側)。
  - 持ち主 `mem_layer.memory_store.m1`(`M1State`)・`mem_layer.memory_store.cue`(`CueState`)・〔検収 M4〕`mem_layer.memory_store.shops`(`ShopTable`)・子クラス `rel_layer` → `PeopleRelationLayer`・〔検収 M4〕`mem_layer.store` → `UncappedStoreMemory`・除外(設定・参照・`LEDGER_ARM`・〔検収〕`caps`・`arms_cfg`・`_tab`)。腕のランの実行時の網羅は 4 つの腕で漏れ 0(試験)。
  - 〔検収 M3〕行 M0 の注: 腕 m1 と memory では器の行が挙動を決める(m1=想起の候補と順・memory=器が表の写しでなく人の行が会話の相手選び・出来事の行が想起を決める)のに、行 M0 の軸は既定の器のまま(軸 1 no・hash_skip・軸 2 derivable)=behavior-hash は器の人の行と出来事の行を見ない(入るのは M0M の時刻と M0S の店の行)。腕 memory と粒度 day は再開を止めるので軸 2 の害は無い。**既定化(まとめて 1 回の版上げ)のときに軸を改める**(behavior-hash に入れる・required)。軸そのものは今は変えない(既定は不変)。
  - 系の宣言は変えていない(書く口は全部 `M0*:mem_layer.memory_store.*` の中=M0M・M0C・M0X は鍵が M0 で始まる)。
- manifest: `memory_summary.memory_store.mr65`(観測の節の下)=腕の名・M1 の値と倍率の分布と直近の時刻の数・意味の手がかりの計数・人の行の数・〔検収 M2〕`capacity`(器の幅・上限・消えた行・行のバイト)・〔検収 M4〕`shops`(店の行の表の幅・行・計数)・計器 `played_along_share`(null)。腕の立っていない器のランには出ない(1-6 の葉のまま)。
- 〔検収 L1〕**腕の名と埋め込みのモデルの名と版は設定の節と設定の指紋に入る**: manifest の設定の節 `memory_summary.mr65_arms`(`manifest_sections` の `memory_summary` の設定の子に 1 本=`CONFIG_PATHS_SHA256` を改訂=2 回目の rebase の後は本体 3-3b の `63a87f2f…` → `b48498e8…`・この 1 本を外すと本体の値)と設定の指紋の鍵 `memory_mr65`(`engine/systems/build.py`=まとめの幅の腕と同じ置き方)。中身=`memory_m1.config_of`: `model`・`cue`・`people`・`grain`、腕 embed では `embed_model` と `embed_identity`(Ruri=`<repo>@<commit>:sha256=<重みの sha256>`・`ngram-test`=作りの名と次元)、腕 memory では `row_caps`。既定の腕のランには欄も指紋の鍵も出ない(既定の指紋と manifest の欄は前のまま=値が動くのは `manifest_sections` の表の値だけ)。再開で腕の取り違え(前は状態台帳の腕の行の道筋の差で止まった)に加えて**埋め込みのモデルの取り違え**も止まる(`_vec` は hash_skip=前は今のモデルで作り直して黙って通った)。
- つなぎの台帳(末尾に 17 行・`declared_in`=本記録・2 回目の rebase の後は本体の 450 行の後=467 行): `DOC-mr65-m1-k-recent`・`-m1-t-min`・`-m1-tau-provisional`・`-m1-kind-table`・`-m1-recognition`・`-m4-rate-variation`・`-m2-embed`・`-m2-cue-text`・`-m1-people-initial`(外す段 4-1)・`-m1-people-limits`・`-grain-day`・`-render-words`・`-m5-trace-window`(外す段 5-2)・`-m1-shop-scale`・〔検収 M2〕`-m1-row-caps`・〔検収 M4〕`-m1-shop-uncapped`・`-m3-impression-form`。ほかは外す段 6-5(MR10=測ってからまとめて既定に)。〔検収 L7〕id の段の名は回答 10-12 の 6-2 の表の名(§14 の対応表)・発注の名は why に。道具 [tools/add_bridges_mr65.py](tools/add_bridges_mr65.py)(同じ id は足さない・`--replace` で本段の行を置き換える)。
- CLI: `--memory-model`・`--memory-cue`・`--memory-embed-model`・`--memory-people`・`--memory-grain`(指定したとき環境変数より強い・試験は子のプロセス)。`cli.run` は 6-5 の腕を「腕」に数える(ランの種類)。〔検収 L6〕記憶 off のランで腕を立てると組み立てで止める(`check_arms` と同じ形の `ValueError`=ランの種類が「腕」になる抜け道を塞いだ)。〔検収 M1〕人ごとの倍率の seed=ランの母集団の seed(組み立て `engine/systems/build.py` が `enable_memory_store(population_seed=pop_seed)` で渡す=`cli.run` の大域の置き方はやめた=`run_day` を直に呼んでも前のランの値が残らない)。
- 乱数: 用途名 `memory.forgetting_rate`(母集団の側の表に 1 行)・静的に安全な呼び手の表に 1 行。

## 9. 結果不変

| 確かめ | やり方 | 結果 |
|---|---|---|
| byte-check([byte_check_mr65.json](byte_check_mr65.json)) | `10e/byte_check_10e.py`・19 構成・5,000 体・seed 1・1 日・テープつき。head=本体 HEAD `0239a3b` の src の写し(git archive+data のつなぎ)・mr65=作業木の src(腕は全部既定) | **19/19 構成で 25 欄とも同じ**(既定 v3 の final `b8eadcb51e8705e7`・v3_mem_rel `768b2262e3b0999e`・古典+記憶+関係 `9dd9d5684891b57c`) |
| 最後の src の 6 構成([byte_check_mr65_final_6cfg.json](byte_check_mr65_final_6cfg.json)) | 上の 19 構成の後に店の行の尺度(腕 m1 だけの道)と注を直した=作業木の src で 6 構成(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel・v3_mem_store・v3_classical_mem_rel)を回し、上の head の側と比べた | **6/6 構成で 25 欄とも同じ** |
| 2 日([two_days_head_vs_mr65.json](two_days_head_vs_mr65.json)) | 道具 `arms_mr65.py one --days 2`・`v3_mem_rel`・5,000 体・head の写しと作業木 | final `31c9b19409e18b2f`・呼数 145,675・テープの全部の列・行動・ハッシュが同じ |
| 再開=通し(既定・[resume_default_5000.json](resume_default_5000.json)) | 道具 `resume`・5,000 体・2 日・日の境目で保存 → 再開 | final `31c9b19409e18b2f` が同じ・境目の後の checkpoint 4 点が同じ・呼数が同じ |
| 再開=通し(腕 m1・[resume_m1_5000.json](resume_m1_5000.json)) | 同じ・`SHIBUYA_MEMORY_STORE=events`・`SHIBUYA_MEMORY_MODEL=m1` | final `268779d84297ce5b` が同じ・checkpoint 4 点が同じ(行 M0M が状態のファイルから戻る) |
| 合成の世界の再開(試験) | 腕 m1・2 日・80 体 | final・checkpoint・テープの `recalled_rows` が通しと同じ |
| 〔検収の直し・rebase の後〕byte-check 1 構成([byte_check_mr65_fix_1cfg.json](byte_check_mr65_fix_1cfg.json)) | 10e の `byte_check_10e.py side/compare`・`w6_v3_default`・5,000 体・seed 1・1 日・head=本体 `54ba3db`(2 回目の rebase の後・src は `86fcff3` と同じ)の src の写し(git archive+`HEAD_TREE_FILES`+data へのつなぎ=回した後に外した)・wt=作業木の src | **25 欄とも同じ**(final `b8eadcb51e8705e7`・両側の `env` 空)。4 構成は親 |
| 〔検収の直し・rebase の後〕腕 4 本([arms_after_fix_vs_pre.json](arms_after_fix_vs_pre.json)) | 道具 `arms_mr65.py side`・`v3_mem_rel`・5,000 体・seed 1・1 日を直しの前の [arms_side.json](arms_side.json) と比べた | m1 `7eaf88e41a5a3335`・embed `cc2ac53d24ae28e8`・people `16434de8b0643c7c`(呼数 64,689)・grain `768b2262e3b0999e`=**4 本とも直しの前と同じ final**・テープの列も全部同じ。people の `v3_classical_mem_rel` も同じ(`2353ea23fb37472b`) |
| 〔検収 M4〕腕 people の店の記憶 on の構成 | 同じ道具・`v3_mem_store` | final `fc10773ef8ec1a4c` → `f41038f9a769597c`(店の行が behavior-hash に入る体の表 `sm_*` から腕の行 M0S へ移った=ハッシュの中身の差)。**呼数 64,528・テープの全部の列・行動の件数・食事・気づきは同じ**(店の行の表の体あたりの最大 14 < 32=上限の差が出ない=同じ挙動) |

## 10. 腕ごとの動いた量(4 構成・5,000 体・1 日・[arms_side.json](arms_side.json)・[arms_moved.json](arms_moved.json))

比べの基準=器だけの腕(`base`=`--memory-store events`・6-5 の腕は既定)。`default`=器なし。`w6_v3_default` は記憶 off=どの腕も何も変えない(1-6 と同じ)。

| 腕 | 動いた欄(3 つの記憶の構成で同じ) | 呼数の差 | テープで動いた列 |
|---|---|---|---|
| default(器なし) | `calls_column_names`・`full_last` | 0 | 列 `recalled_event_ids` が無い(器の腕だけの列) |
| m1 | final・behavior/full の最後 | 0 | `b5_text`・`prompt_hash`・`recalled_rows`・`recalled_kind`・`recalled_object`・`recalled_first_tick`・`tokens_in`・目印の列 |
| embed(ngram-test) | final・behavior/full の最後 | 0 | 同上 |
| people(m1+人も記憶) | `v3_mem_store`(関係 off)は m1 と同じ欄・`v3_mem_rel`・`v3_classical_mem_rel` は呼数と行動も | −3,105・−11,891 | ほぼ全部(知人出現の起床が無い=§4) |
| grain(day) | `full_last` だけ | 0 | 目印の列だけ |

- final と behavior の最後が動くのは、腕の行(M0M・M0C)が腕のランだけ behavior-hash に入るためでもある。挙動が動いたかはテープの列(B5 の本文・プロンプト)で見る: m1 と embed は呼数・行動の件数・食事・気づきは同じで、B5 の記憶の行の中身が変わった(mock の行為は B5 の記憶の行に鈍い=1-6 の記録と同じ)。
- **M1 と M0 の上位 k**(負の対照=同じである必要はない・腕 m1 の全部の想起で、同じ器の行を M0 の式でも並べた):

| 構成 | 想起 | 順まで同じ(両方とも空を含む/除く) | 集合が同じ(含む/除く) | 両方とも空 | M1 が少ない | M1 が多い | 項の重なり(M0 の項に対して) |
|---|---|---|---|---|---|---|---|
| v3_mem_store | 59,693 | 51.6% / 51.5% | 57.0% / 56.8% | 169 | 945 | 2,415 | 76.2% |
| v3_mem_rel | 62,959 | 72.9% / 72.9% | 77.0% / 76.9% | 212 | 4,238 | 2,595 | 88.5% |
| v3_classical_mem_rel | 100,513 | 66.6% / 66.0% | 69.1% / 68.5% | 1,965 | 16,730 | 5,362 | 80.8% |

  〔検収 L2〕「両方とも空」の想起を「同じ」に数えた率と除いた率の両方(計器の出力 [arms_moved.json](arms_moved.json) の `topk_shares`=道具 `compare` が両方を出す・同じ side の JSON から作り直した=ほかの欄は前と同じ)。

  違いの主な源: M1 は重要度の項を境目の側に入れる(§2 の「1 回の行の残る時間」)・直近の時刻が効く(最後に触れてからの時間)・人ごとの倍率。
- 腕 m1 の器: 直近の時刻を 1 回だけ持つ行 43,042・2 回 7,068・3 回 3,202(`v3_mem_store`)・倍率の平均 1.000・SD 0.149・範囲 0.55〜1.45。
- 腕 embed: 要旨の埋め込み 256〜379 行・手がかりの文のある想起 2,590〜3,251(全体の 3〜5%)・聞き手の手がかり 0(語彙 v3 にひと言が無い)。

## 11. 性能(刻みあたり=P4・5,000 体・1 日・`v3_mem_rel`・参考)

道具 `arms_mr65.py side --jobs 1`(1 本ずつ順に・上位 k の比べは無し・[perf_side.json](perf_side.json))。同じ機械で他の作業木のランが動いていた=ばらつきは測っていない(参考)。

| 腕 | 壁時計(1 日) | 刻みあたり | 器だけ(base)との差 | 呼数 |
|---|---|---|---|---|
| default(器なし) | 61.6 秒 | 42.8 ms | −4.1% | 67,794 |
| base(器 M0+体の出来事) | 64.2 秒 | 44.6 ms | 0 | 67,794 |
| m1 | 70.7 秒 | 49.1 ms | +10.1% | 67,794 |
| embed(ngram-test) | 63.6 秒 | 44.2 ms | −1.0% | 67,794 |
| people(m1+人も記憶) | 73.0 秒 | 50.7 ms | +13.8% | 64,689 |
| grain(day) | 64.1 秒 | 44.5 ms | −0.1% | 67,794 |

- M1 の増え(約 +4.5 ms/刻み・1 日 約 6.5 秒)は想起ごとの強さの計算(体の行の配列 × 直近 3 回・約 6 万回/日=1 回 約 0.1 ms)。人も記憶の腕は人の行の読み口(関係の読み口の呼びごとに体の行の幅の配列)が足される。39 万体への外挿は呼数に比例(推測)。
- 〔検収 L3〕人も記憶の腕の会話の相手選びは、相手だけ要る読み口(`_partner_rows`)で強さを計算せず、A だけ要る読み口(`activation`・`edges`・`acquaintances`・`partners_in_cell`・計器)で見覚えの強さを計算しない(`people_rows(strength=, familiar=)`)=相手選び 1 回の強さの計算は 4 回 → 1 回。結果は前の作りと同じ(試験 `test_people_readers_compute_each_strength_once`・5,000 体 1 日の final も同じ=§16)。上の表の +13.8% は直しの前の値(測り直していない)。
- 既定の腕は前と同じ道(器を作らない・6-5 の腕の検査は記憶の層を作る時の 1 回)。byte-check の 19 構成の壁時計(5 本並列・参考)は作業木/HEAD の比の中央値 1.03(記憶 off の構成は変えた道を通らない=同じ機械の他のランによるばらつきの範囲・記憶 on の 4 構成は 0.98〜0.99)。
- 逐次ループの新設: 無い(体ごとの for は無い)。宣言した逐次は、上限なしの腕の幅を倍にする回(log2)と、注釈・埋め込みの行の数ぶん(会話の要旨=刻みに数件)と、浅い痕跡の 2 人の行(手がかりの時だけ)。

## 12. 試験

新しい試験 `tests/engine/memory/`(52 本=slow 1・Ruri の重みが無くて skip 1・data が要るのは slow の 1 本だけ):

- `test_m1_strength.py`(10): 既知の値(+1 なし)・折衷形=正確な式(n ≤ k)と等間隔の近さ・式 (2) の近似・単位で全部が同じだけずれる(負の対照=M0 の式)・最短の符号化時間・人ごとの倍率(決定的・15%・切り・カウンタの鍵)・τ の仮の値が M0 の越える時刻と同じ・直近の時刻のずらし・思い浮かぶ/見覚え/忘れる/言葉・M1 の状態の守り(付け替え・消去・読み取り専用の view・幅を広げる)・腕の切替口と検査。
- `test_m1_runs.py`(8): 既定の腕は何も作らず manifest の葉も増えない・器の単体(直近の時刻・M1 の τ と言葉)・言葉の描き方の口・**M1 と M0 の上位 k(負の対照=全部同じなら落とす)**・腕 m1 の 2 日の再開=通し・宣言(M0M)を外すと書いた所で落ちる・腕は系の外で 1 回だけ・器の無いランの腕は止める。
- `test_m2_cue.py`(8): n-gram の代わりの決定論・近い要旨が上に来る(一致は cos ≥ 0.5)・要旨を落とすと埋め込みも落ちる・手がかりの文の選び(会話中/外)・Ruri の版の固定と重みが無いときの `EmbedUnavailable`・(skip)Ruri で近い文が上・既定は埋め込みを計算しない・腕 embed のランが決定的。
- `test_m4_m5_people.py`(8): 人の行の鍵・重要度・関係の種類・思い浮かぶ/見覚え/忘れる(消す・負の対照=見覚えのある人は消さず幅を広げる)・幅を倍に・最初の関係(`seed_people`)・**関係の表を読まない(AST=親の読み手は全部上書き)**・**腕 table は `write_relations` を呼び腕 memory は呼ばない(負の対照)**+幅 4 から広がる・再開は止める・(slow)5,000 体・1 日・幅 8 から。
- `test_m3_impression_and_trace.py`(5): 印象の追記と寝たときの書き直し(古い要約も残る・長さを切らない・埋め込みの口)・原因は LLM の呼びだけ・浅い痕跡(同じ場所の近い時刻・窓の外・言葉)・計器・見えない欄と版。
- `test_mr65_grain_and_cli.py`(4): 粒度 day(記録の行が減る=目印を前のままにした回だけ・final と既存のテープの列は同じ・目印は記録にある)・再開は止める・CLI の腕が環境変数より強い(子のプロセス・seed は母集団の seed)・`cli.run` のランの種類が「腕」。
- `test_mr65_guards.py`(9): 子の持ち主の書く口は器からだけ(AST・負の対照)・子の持ち主の列は持ち主の中でだけ書く・状態台帳の行の軸・腕のランの実行時の網羅(4 つの腕)・新しいモジュールの層の契約。

〔検収の直しで足した試験〕関数 18・項目 20(§16 の表の試験の名): `test_mr65_review_fixes.py`(新・7=L1 の 2・L3・L4・`CueState` の守り・M3・L7)・`test_m1_runs.py`(+3 関数・項目 +5=M1 の 2・L6 の媒介変数 3)・`test_m4_m5_people.py`(+7=M2 の 4・M4 の 3。slow の 5,000 体 1 日に M2・M4 の確かめを足した)・`test_mr65_guards.py`(+1=M4 の書く口の守り・負の対照)。変えた試験: `test_mr65_grain_and_cli.py`(大域の seed の確かめを外した)・`test_m0_store_schema.py`(子の持ち主 3 つ)・状態台帳の数(§16)・`CONFIG_PATHS_SHA256`。

結果(作業木・data あり):

| 範囲 | 結果 |
|---|---|
| 全体 `-m "not slow and not gpu" -n 6 --dist loadfile --ignore=tests/c7` | **5,170 passed・1 failed・1 skipped・1 xfailed(16 分 29 秒)**。落ちた 1 件は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(テープの道筋が `data/tape/` で始まらない=作業木の `data` が本体へのつなぎで起きる既知の落ち=1-0・T0・1-3・1-6・2-3 の記録と同じ)。skip 1 件は Ruri の重み。この中に `tests/c8`・`tests/economy/cp2`・`tests/engine/memory`・`tests/engine/test_relations*.py`・`tests/engine/events`・`tests/engine/systems`・`tests/engine/multiday`・`tests/engine/test_resume_10d.py`・状態台帳・10f・`tests/perception`・`tests/tools`・`tests/engine/bridging` を含む |
| `slow`(`tests/engine/memory`・`tests/engine/multiday`) | **4 passed**(6 分 39 秒=1-6 の 5,000 体の想起の突き合わせ 2 本・人も記憶の 5,000 体 1 本・2-3 の 5 日 1 本) |
| `tests/c8`・`tests/economy/cp2`・`tests/engine/bridging`(先に別に) | 322 passed(47 秒) |
| `lint-imports` | 5 契約とも守られている(250 ファイル・926 の依存) |
| 秘密の走査(`tools/scan_secrets.py`・変えたファイルと新しいファイル) | CLEAN |

〔検収の直し・rebase の後〕(作業木・本体 `ed7155c` の上・data あり。発注の範囲の行だけ 2 回目の rebase の後=`54ba3db` の上):

| 範囲 | 結果 |
|---|---|
| 全体 `-m "not slow and not gpu" -n 6 --dist loadfile --ignore=tests/c7` | **5,267 passed・1 failed・1 skipped・1 xfailed(16 分 48 秒)**。落ちた 1 件は上と同じ既知の `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(作業木の data が本体へのつなぎ=テープの道筋が `data/tape/` で始まらない)。skip 1 件は Ruri の重み。`tests/c8`(読みのグラフの作り直しは要らなかった)・`tests/economy/cp2`・`tests/engine/memory`・状態台帳・10f・`tests/perception`・`tests/engine/test_store_memory.py`・`test_store_choice.py`・`test_wom.py` を含む |
| 発注の範囲(`tests/engine/memory`・`body`・`speech`・`tests/perception`・状態台帳・10f の 2 本・`bridging`・`cp2`・`tests/c8`・`test_relations*.py` 3 本・店の記憶と選び手と伝聞の 3 本・`-n 2 --dist loadfile -m "not slow"`) | `ed7155c` の上: **1,197 passed・1 skipped(Ruri の重み)・failed 0(14 分 57 秒)**。2 回目の rebase の後(`tests/engine/experiment` を足した): **1,320 passed・1 skipped・failed 0(18 分 1 秒)**・`tests/c8` は読みのグラフの作り直し無しで通る |
| `slow`(`tests/engine/memory`・`tests/engine/multiday`) | **4 passed**(4 分 40 秒) |
| `tests/c8`・`tests/economy/cp2`・`tests/engine/bridging` | 322 passed(61 秒) |
| `lint-imports` | 5 契約とも守られている(253 ファイル・944 の依存) |
| 秘密の走査(変えたファイルと新しいファイル) | CLEAN |

## 13. 触った共有ファイル(親が取り込み順に rebase するときの一覧)

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/state_ledger.py` | `_EXT` の末尾(行 BD の後)に M0M・M0C・M0X・`OWNER_CLASSES` の `mem_layer.memory_store` の直後に 2 項・`OWNER_ALT_CLASSES` の末尾に 1 項・`EXCLUDED` の末尾に 7 項 |
| `src/shibuya/engine/run.py` | `POPULATION_RNG_DOMAINS` の末尾に 1 行(`memory.forgetting_rate`) |
| `src/shibuya/engine/rng_audit.py` | `SAFE_SITES` の末尾に 1 行・注の数 |
| `src/shibuya/cli.py` | `--decision-port` の前に引数 5 つ・`run_kind` の式の末尾に 1 項と import 1 行・`pop_seed` の直後に seed を置く 3 行・`--memory-store` の切替口の直後に腕の切替口 |
| `src/shibuya/perception/facts.py` | 版 /2・`EMPTY_FIELDS` の末尾・`Percept` の末尾の欄・冒頭の注 |
| `src/shibuya/engine/relations.py` | 読み口 `_partner_rows` を足し、`choose_talk_partners` の 3 行 |
| `docs/design/bridging-ledger.json` | 末尾に 17 行(本体の 450 行の後=467 行) |
| `src/shibuya/engine/systems/build.py`(検収 M1・L1・L6) | 指紋の組み立ての 3 か所目(まとめの幅の直後)に記憶の腕の鍵・記憶の表を作った直後に記憶 off の腕の検査・`enable_memory_store` に母集団の seed |
| `src/shibuya/engine/store_memory.py`(検収 M4) | 行の口 3 つ(`columns`・`_evict_slots`・`_put`)と `StoreColumns`・読み口の `agents.registry.sm_*` を口に(既定=同じ配列) |
| `src/shibuya/engine/store_choice.py`(検収 M4) | 7c の想起の読み口を `store.columns(agents)` に(5 行) |
| `src/shibuya/engine/manifest_sections.py`(検収 L1) | `memory_summary` の設定の子に `mr65_arms` |
| `tests/engine/test_env_and_sections_10f.py`(検収 L1) | `CONFIG_PATHS_SHA256` の改訂と注 |
| 凍結の数の試験 | §1 の表の最後の行(行の数・腕の行・SAFE_SITES の数・Percept の欄と版・器の slots) |

系の宣言の表(`systems/table.py`)・進行役(`systems/conductor.py`)・体の層・実験の層・凍結の表(`writes_soa_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`・`manifest_keys_frozen.json`・`writes_paths_events.json`)・描画(`perception/renderer.py`)は触っていない。〔検収の直し〕組み立て(`systems/build.py`)・manifest の節の表(`manifest_sections.py`)・`CONFIG_PATHS_SHA256`・店の記憶(`store_memory.py`・`store_choice.py`)は親の判断(M1・L1・M4)で触った(上の表)。店の行の表の書く口は既存の系の宣言 `M0*:mem_layer.memory_store.*`(memory・decide・llm_receive)に入る=系の宣言の表は変えていない。

## 14. 限界・仮採用(10-13b §0-3)・親に確かめてほしいこと

**発注の段の名と回答 10-12 の 6-2 の表の名が違う**: 発注は「M4=思い浮かぶ/見覚え・M5=人も記憶」、6-2 の表は「M1=想起の式と統合(人も記憶の一つ・上限と保管をなくす)・M4=個人差 15%・M5=同席と浅い痕跡」。本段は中身で作った(全部の中身が入っている)。記録の節の名は発注に合わせ、〔検収 L7〕**つなぎの台帳の id は 6-2 の表の名にそろえた**(発注の名は各行の why に書いた)。対応表:

| 本記録(発注の名) | 6-2 の表の段 | つなぎの台帳の id |
|---|---|---|
| M1 強さの式(§2) | M1 想起の式と統合 | `DOC-mr65-m1-k-recent`・`-m1-t-min`・`-m1-tau-provisional`・`-m1-kind-table`・`-m1-shop-scale` |
| M1 の倍率 15%(§2) | M4 個人差 | `DOC-mr65-m4-rate-variation` |
| M2 手がかり(§3) | M2 手がかり | `DOC-mr65-m2-embed`・`-m2-cue-text` |
| M4 思い浮かぶ/見覚え(§4) | M1 | `DOC-mr65-m1-recognition`(旧 `-m4-recognition`) |
| M5 人も記憶=器・上限なし・最初の関係・限界・種類ごとの上限・店の行(§4) | M1 | `DOC-mr65-m1-people-initial`(旧 `-m5-`)・`-m1-people-limits`(旧 `-m5-`)・`-m1-row-caps`・`-m1-shop-uncapped` |
| M3 の器(§5) | M3 印象と寝たときの整理 | `DOC-mr65-m3-impression-form` |
| 浅い痕跡・見えない欄・注意の口(§6) | M5 同席と浅い痕跡 | `DOC-mr65-m5-trace-window`(旧 `-trace-window`) |
| 粒度 day(§7)・言葉の描き方(§2) | 段の外(2-3 の決め直し・MR-0) | `DOC-mr65-grain-day`・`-render-words` |

**仮採用**

1. M1 の腕は器を記憶の表の写しのままにし、追い出しは表と同じ M0 の score(器と表の行をそろえる)。上限を外すのは人も記憶の腕だけ(〔検収 M2〕種類ごとの上限 256 まで)。
2. 境目 τ は M0 の τ から導いた仮の値(人のデータで較正しない)。重要度の項を境目の側(A)に入れた(ACT-R の基底の定数と同じ置き方)。
3. 見覚えの d=0.35 と忘れるの幅(1 回だけ会った人は見覚え約 9 日・消えるまで約 5 か月)。倍率の小さい人(d が小さい)は int64 の時刻の範囲で忘れないことがある。
4. 腕 embed は意味の手がかりだけ(ID の一致を使わない)。店の行の一致は ID のまま(店の行に文が無い)。
5. 腕 memory の知人出現の起床と同席は作らない(要求は計器)=呼数が減る(§10)。人の行の目印は仮の行。好意の符号は 0。
6. 人ごとの倍率の鍵は体の番号(母集団の元 id は器に届かない)。〔検収 M1・直した〕seed=ランの母集団の seed(組み立てが `enable_memory_store(population_seed=…)` で渡す・無ければ止める=0 で黙って引かない)。
7. 〔検収 L1・直した〕6-5 の腕は既定と違うときだけ設定の指紋(`memory_mr65`)と manifest の設定の節(`memory_summary.mr65_arms`)に入る(まとめの幅の腕と同じ置き方)。`run_day` の引数ではない(切替口)。
8. 〔検収 L6・直した〕記憶 off のランで腕を立てると組み立てで止める(前は何もしなかった)。記憶 on で器の腕が mem のまま 6-5 の腕を立てても止める。
9. `Percept` の版を /2 に上げた(manifest の `percept` の値が既定のランでも変わる=欄が 1 つ増える・byte-check の 25 欄の外=〔検収 L5〕親の承認待ちの宣言)。
10. 言葉の描き方の口は描画に結線していない(テンプレの版が動く=親の判断)。
11. 店の行の尺度を M1 にそろえるのは境目の差のずらしだけ(店の行の強さは店の記憶の式のまま=腕 memory の器の店の行の表も同じ式)。
12. 〔検収 M2〕種類ごとの上限 256 行/体(出来事・人・店)と、上限に届いた種類は思い浮かぶ強さ A(手がかり無し)の一番低い行を消す規則(expedient・感度の腕の口 `set_row_caps`・外す条件=既定化の前の 7 日の測りと予算=§7-3)。
13. 〔検収 M4〕腕 memory では体の表の `sm_*` を書かない(確保は今のまま・空)=店の行は器の店の行の表だけ(腕の行 M0S)。

**限界**

- Ruri の重みは未取得(§3)=Ruri の道(`RuriEmbedder.encode`)は未試験。取得の許可(`us.aws.cdn.hf.co` などの転送先)が出たら、版の置き場に置き、`test_ruri_close_sentence_ranks_first` と腕 embed のランを回す(torch と transformers の版の固定と venv への導入も)。
- 腕 memory と粒度 day は再開に対応しない(止める)。腕 embed の再開は合成の世界の日の途中の再開で通しと同じ final(〔検収 L1〕の試験の負の対照)・5,000 体では測っていない。
- 〔検収 M2〕腕 memory の器は 5,000 体・7 日で幅 256 に届き、39 万体の見積り(6.88 GiB・上限まで倍なら 13.76 GiB)は予算の中に無い=既定化の条件を満たしていない(§7-3・7-4)。
- M3 の器と浅い痕跡と注意の口はランに結線していない。腕 embed の手がかりの文は会話の番からしか来ない(判断の呼の理由の結線が無い)。
- Petrov 2006 の式 (3) は親が原典(ACT-R users の添付 PDF)で一次確認 ○(第336)。
- 用語集との照合はしていない(新しい語「人の行」「見覚えの強さ」「粒度」「浅い痕跡」)。

**親に確かめてほしいこと**

1. Ruri の重みの取得の許可(転送先 `us.aws.cdn.hf.co`=CLAUDE.md §7 の一覧の外)と、torch・transformers を本体の venv に入れるか(別の venv にするか)=〔親の判断 2〕ユーザーの判断(親が PENDING §1-1 に書く・本段は取得も pip もしない)。
2. 共有ファイル `run.py`(乱数の用途名の表 1 行)と `rng_audit.py`(静的に安全な呼び手の表 1 行)を触った(発注の「編集してよい」一覧の外=Philox の鍵を使うと試験が表への登録を求める)。
3. `tests/engine/body/test_system1_placeholders.py`(体の層の試験)の Percept の欄の凍結を 1 つ増やした(発注の一覧の外=Percept に欄を足すと落ちる)。
4. 粒度の案の次の手(§7-2 の (a)・(a)+(b)=既定化の前に決める)。
5. 段の名の対応(§14 の最初の表=台帳の id は 6-2 の表の名にそろえた)。
6. 〔検収 M2〕バイト予算の表(§7-3)を予算の宣言の文書へ写すこと・上限の値と体ごとの可変の幅か CSR・出来事の行の忘れ方(MR12)の決め直し(既定化の前)。
7. 〔検収 M4〕店の行の表を器の子の持ち主に置き、`store_memory.py`・`store_choice.py` の読み書きを口に通した(既定は同じ配列=byte-check で不変)。腕 memory の店の記憶 on の構成は final が変わる(店の行が behavior-hash の `sm_*` から腕の行 M0S へ=§16)。
8. rebase の先は本体の最新 `ed7155c`(発注の `76d3899` の後の文書だけの 1 本=src は同じ)→ 2 回目は `54ba3db`(親の指示の `86fcff3` の後の文書だけの 1 本=src は同じ)。

## 15. ライセンス台帳に足す行の案(取得したときに親が足す)

| ディレクトリ | 内容 | 出典 | ライセンス | 商用 | 備考 |
|---|---|---|---|---|---|
| data/models/ruri/ruri-v3-30m@24899e5d…(未取得) | 文の埋め込みのモデル Ruri-v3-30m(37M・256 次元・model.safetensors 146,828,152 B・sha256 e94155e3…2f8832) | huggingface.co cl-nagoya/ruri-v3-30m(commit 24899e5de370b56d179604a007c0d727bf144504・base cl-nagoya/ruri-v3-pt-30m) | Apache-2.0(モデルカードの license) | ○ | 記憶 MR2 の腕 embed(6-5)。重みの本体は us.aws.cdn.hf.co へ転送=取得の前に許可。取得日・sha256 を取得の時に確かめて書く。再配布しない(gitignore) |
| data/models/ruri/ruri-v3-130m@e3114c6e…(未取得) | Ruri-v3-130m(132M・512 次元・528,573,472 B・sha256 1c342581…4fc6d1) | huggingface.co cl-nagoya/ruri-v3-130m(commit e3114c6ee10dbab8b4b235fbc6dcf9dd4d5ac1a6・base cl-nagoya/ruri-v3-pt-130m) | Apache-2.0 | ○ | 同上 |

## 16. 検収(review.md)の直し・rebase(親の判断=中は全部直してから取り込む)

| 欠陥 | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| M1 忘れる速さの seed が大域 | `memory_m1`(`_STATE["rate_seed"]`・`bind_rate_seed`・`rate_seed` を消した)・`memory.py`(`enable_memory_store(population_seed=)`→`_enable_mr65`)・`systems/build.py`(`pop_seed` を渡す)・`cli.py`(大域の bind の 3 行を消した) | ランごとに母集団の seed を組み立てが渡す(無ければ止める) | `test_m1_rate_seed_is_the_population_seed`(腕 m1 で 10f の `_check_split`・`cli.run(population_seed=7)` の後の `run_day(population_seed=9)` で 9=負の対照・省略=seed)・`test_m1_needs_the_population_seed_at_assembly`・2 日の再開の試験は `population_seed=5` |
| M2 上限なしの腕の器の太り | `memory_store.py`(`ROW_CAPS_DEFAULT`・`set_row_caps`・`max_width`・`_at_cap`・`_evict_by_a`・`_make_room`・`seed_people`)・`memory_m1.M1State`(計数)・計器 `mr65.capacity` | 幅の倍増は種類ごとの上限(256)の和まで・上限の種類は A の一番低い行を消す・忘れるの規則は前のまま・バイト予算の表(§7-3)・5,000 体 7 日の測り(§7-4) | `test_row_caps_bound_the_width_and_evict_the_lowest_a_row`・`test_cap_eviction_ties_go_to_the_lower_row`・`test_seed_people_over_the_person_cap_is_refused`・`test_rows0_over_the_width_cap_is_refused`・(slow)5,000 体 1 日 |
| M3 行 M0 の軸 | `state_ledger.py` の行 M0 の注 | 注を足した(軸は今は変えない=既定化で改める) | `test_ledger_m0_note_declares_the_arm_runs_and_keeps_the_axes` |
| M4 店 32 件の上限を外す道 | `memory_shops.py`(新)・`store_memory.py`(行の口 3 つ)・`store_choice.py`・`memory.py`(`enable_store`・読み口)・`memory_store.attach_shops`・状態台帳の行 M0S | 器の店の行の表=幅 32 から倍に上限 256・上限で A の一番低い行を上書き(§4) | `test_shop_table_grows_to_the_cap_then_overwrites_the_lowest_a`・`test_shop_table_ties_and_bounds`・`test_people_arm_run_keeps_shops_in_the_store_table`(小さな上限でも壊れない・体の表 `sm_*` は空)・(slow)5,000 体 1 日・守り `test_shop_table_ports_are_called_only_from_the_uncapped_store` |
| L1 腕の名とモデルの版 | `memory_m1.config_of`・`memory_embed.model_identity`・`build.py`(指紋)・`memory.py`(manifest)・`manifest_sections.py` | 設定の節 `memory_summary.mr65_arms` と指紋 `memory_mr65`(既定と違う腕だけ) | `test_arms_enter_the_config_section_and_the_fingerprint`・`test_resume_refuses_another_embed_model_or_another_arm`(負の対照=同じ腕は再開=通し) |
| L2 上位 k の一致 | 道具 `arms_mr65.py compare`(`topk_shares`)・[arms_moved.json](arms_moved.json) | 両方とも空を含む率と除いた率の両方(§10) | (道具) |
| L3 強さの 2 回計算 | `memory_store.people_rows(strength=, familiar=)`・`relations_people.py` | 相手だけ=計算しない・A だけ=見覚えを計算しない | `test_people_readers_compute_each_strength_once`(結果は前の作りと同じ) |
| L4 `PARAMS["kinds"]` | `memory_m1.PARAMS`・`_plain` | 中も `MappingProxyType`・manifest へは深い写し | `test_params_tables_are_read_only_and_the_summary_is_a_plain_copy` |
| L5 Percept /2 | 記録 §6・§14 の 9 | 既定のランでも manifest の `percept` の値が変わる(25 欄の外)と書いた | — |
| L6 記憶 off の腕 | `systems/build.py`(記憶の表が無いとき `check_arms(store_on=False)`) | 止める | `test_memory_off_with_memory_arms_is_refused`(3 つの腕 × `run_day`・`cli.run`・負の対照) |
| L7 台帳の id の段の名 | つなぎの台帳・道具 `add_bridges_mr65.py`(`--replace`) | 6-2 の表の名に・発注の名は why に(§14 の表) | `test_bridge_ids_use_the_stage_names_of_answer_6_2` |
| L8 `_bc/` | — | 触っていない(親が .NET でつなぎを外してから消す)・直しの scratch は `_bc2/`(つなぎは作って外した) | — |
| 低 `CueState` の守り | — | 試験を足した | `test_cue_state_guards` |

- rebase: 本体の最新 `ed7155c`(発注の `76d3899`+文書だけの 1 本)へ。控え(枝の版と土台 `0239a3b` の版)+`checkout`+`merge --ff-only`+`merge-file`。衝突 3 本: `cli.py`(暦の影の import と `run_kind` の式の末尾=本体の分 → 本段の分)・`state_ledger.py`(`_EXT` の末尾=CAL → M0M・M0C・M0X、`EXCLUDED` の末尾=暦の影 → 本段)・`test_state_ledger_10b.py`(数え直し: 外の状態 本体 116 → 119(rebase)→ 120(M0S)・全体 207 → 210 → 211・鍵の列 `… "BD", "CAL", "M0M", "M0C", "M0X", "M0S"`)。つなぎの台帳は本体の版の JSON に本段の行を末尾に足して書き直した(411+15=426 → 直しで 428=+`-m1-row-caps`・`-m1-shop-uncapped`)。
- 2 回目の rebase: 本体 `54ba3db`(親の指示の `86fcff3`=3-3b `e7261b7` と 4-1 段 4〜7 の後に文書だけの 1 本)へ同じ手順(控え=枝の版 20 本と `ed7155c` の版)。`cli.py`・`manifest_sections.py`・`state_ledger.py` は自動で合った(3-3b の分は別の hunk)。衝突は `test_env_and_sections_10f.py` の `CONFIG_PATHS_SHA256` だけ=本体 3-3b の 4 本(`63a87f2f…eab3ed`)に本段の 1 本を足して本体の計算の仕方(`config_paths()` の sha256)で計算し直した=`b48498e84f07bb9a1552fed87c5aca637805e31cdbc364f9536eeb96bf0edcaa`(本段の 1 本を外すと `63a87f2f…`=注に書いた)。つなぎの台帳=本体 450 行+本段 17 行=467 行(既存の行は変えない)。状態台帳の数は本体が変わらない(3-3b は行 experiment の説明文だけ)=外の状態 120・全体 211 のまま。既定の byte-check 1 構成(`54ba3db` の写し vs 作業木)25 欄とも同じ(final `b8eadcb51e8705e7`)・腕 4 本(`v3_mem_rel`)と腕 people の `v3_mem_store` の final は 1 回目の rebase の後と同じ([arms_after_fix_vs_pre.json](arms_after_fix_vs_pre.json))。
