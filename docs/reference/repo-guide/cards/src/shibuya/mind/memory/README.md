# src/shibuya/mind/memory

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 11 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/mind/memory/__init__.py)

(冒頭の説明なし)

## [familiarity.py](../../../../../../../../src/shibuya/mind/memory/familiarity.py)

engine.familiarity — **親しみの表**(4 段目・記憶の先行部品=M13 訪問カウンタ+M17 露出カウンタ・第290)。

- 公開の関数とクラス
  - `FamiliarityLayer`(クラス): 親しみの表の値を決める層(書き手は ``resolve.write_familiarity``)。
  - `activation_approx`(関数): 最適化学習の近似 ``A = ln(n/(1−d)) − d·ln(L+1)``(n ≤ 0 は :data:`ACTIVATION_ABSENT`)。
  - `activation_exact`(関数): 厳密式 ``ln Σ_j (Δt_j + 1)^(−d)``(Δt_j=各接触からの経過分・比較と記録のためだけ)。
  - `person_thing`(関数): 体 → 人の ``thing_id``(``1<<30 | id``・本段では書かない)。
  - `place_thing`(関数): セル → 場所の ``thing_id``(``−(cell+2)``=空行 −1 と衝突しない・cell ≥ 0)。
  - `thing_kind`(関数): ``thing_id`` → 種類(``"empty"`` / ``"poi"`` / ``"place"`` / ``"person"``)の文字列配列。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.perception.attention`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_store`
- 読む試験: `tests/engine/test_familiarity.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_store_memory.py`・`tests/perception/test_p_see_activity.py`
- 状態台帳の行
  - 持ち主 `fam_layer`(`FamiliarityLayer`)
    - `O7` FamiliarityLayer prev_cell(挙動 behavior・復元 required) 道筋 `fam_layer.prev_cell` 書ける系: familiarity
    - `O67` FamiliarityLayer stats(挙動 diag・復元 discardable) 道筋 `fam_layer.stats` 書ける系: familiarity
- 決定の ID: D-95・D-119・第 290

## [memory.py](../../../../../../../../src/shibuya/mind/memory/memory.py)

engine.memory — 記憶 第 1 段の **記録**(6 段目 6a・D-95・記憶アジェンダ v1 M1〜M4・M13・M16・修正 1・第294)。

- 公開の関数とクラス
  - `MemoryLayer`(クラス): 記憶の表の書き手と読み口(記録だけ・本段では誰も読まない)。
  - `RecallItem`(クラス): 想起した 1 行(描画の材料=``perception.renderer`` が文にする)。
  - `activation_rows`(関数): A = ln(n/(1−d)) − d·ln(L+1)(L=(tick − first)×分/tick・#56 と同じ近似)。n=0 の行は −inf。
  - `importance_of`(関数): 事象 → importance(固定表・配列演算)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.relations`・`shibuya.engine.resolve`・`shibuya.foundation.types`・`shibuya.mind.memory.familiarity`・`shibuya.mind.memory.memory_embed`・`shibuya.mind.memory.memory_m1`・`shibuya.mind.memory.memory_shops`・`shibuya.mind.memory.memory_store`・`shibuya.mind.memory.store_memory`・`shibuya.mind.relations.people`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.mind.judge.decision.sources`・`shibuya.mind.memory.memory_store`・`shibuya.mind.memory.store_memory`・`shibuya.mind.plan.head_recall`
- 読む試験: `tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m1_strength.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/test_wom.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/perception/facts/test_render_from_percept_bytes.py`
- 状態台帳の行
  - 持ち主 `mem_layer`(`MemoryLayer`)
    - `O8` MemoryLayer gist・_gist_order(挙動 behavior・復元 required) 道筋 `mem_layer._gist_order`・`mem_layer.gist` 書ける系: decide・llm_receive・memory
    - `O9` MemoryLayer _session_key・_gist_done(挙動 behavior・復元 required) 道筋 `mem_layer._gist_done`・`mem_layer._session_key` 書ける系: decide・llm_receive・memory
    - `O10` MemoryLayer _next_session・_next_join(挙動 behavior・復元 required) 道筋 `mem_layer._next_join`・`mem_layer._next_session` 書ける系: decide・llm_receive・memory
    - `O11` MemoryLayer _target・stats・recall_stats(挙動 diag・復元 discardable) 道筋 `mem_layer._target`・`mem_layer.recall_stats`・`mem_layer.stats` 書ける系: decide・llm_receive・memory
- 決定の ID: D-93・D-95・D-120・第 294・第 295・第 298

## [memory_embed.py](../../../../../../../../src/shibuya/mind/memory/memory_embed.py)

engine.memory_embed — 記憶 MR2 の意味の手がかり(埋め込み)の口(第 6 期 6-5・腕 ``--memory-cue embed``)。

- 公開の関数とクラス
  - `CueState`(クラス): 意味の手がかりの状態(記憶の器の子の持ち主 ``mem_layer.memory_store.cue``・状態台帳の腕の行 ``M0C``)。
  - `EmbedUnavailable`(クラス): 埋め込みのモデルが使えない(重みが置き場に無い・torch/transformers が無い)。
  - `Embedder`(クラス): 埋め込みの口(``encode`` は L2 で正規化した ``(件, dim)`` の float32)。
  - `NgramEmbedder`(クラス): 試験用の代わり ``ngram-test``(文字の 1〜3-gram を crc32 で ``dim`` 次元に足して正規化・意味の手がかりではない)。
  - `RuriEmbedder`(クラス): Ruri-v3(``cl-nagoya/ruri-v3-30m``・``130m``)を CPU で(重みは :data:`MODEL_ROOT` の版の置き場から読む)。
  - `RuriPin`(クラス): Ruri-v3 の版の固定(huggingface のリポ・commit・重みの sha256=X-Linked-ETag・大きさ・ライセンス)。
  - `make_embedder`(関数): 腕のモデルの名 → 埋め込みの口(``ngram-test`` は試験用の代わり・Ruri は重みが無ければ :class:`EmbedUnavailable`)。
  - `model_identity`(関数): 〔検収 L1〕埋め込みのモデルの名 → 版の同定(設定の指紋と manifest の設定の節に入れる=再開で取り違えを止める)。
- 呼び手: `shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_m1`・`shibuya.mind.memory.memory_store`
- 読む試験: `tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`
- 状態台帳の行
  - 持ち主 `mem_layer.memory_store.cue`(`CueState`)
    - `M0C` CueState(意味の手がかり=手がかりの文と行の埋め込み・第 6 期 6-5)(挙動 behavior・復元 required・腕 memory-cue) 道筋 `mem_layer.memory_store.cue._heard`・`mem_layer.memory_store.cue._own`・`mem_layer.memory_store.cue._qcache`・`mem_layer.memory_store.cue._vec` 書ける系: decide・llm_receive・memory
    - `M0X` M1State・CueState の計数(第 6 期 6-5)(挙動 diag・復元 discardable) 道筋 `mem_layer.memory_store.cue._cue_stats` 書ける系: decide・llm_receive・memory
- 決定の ID: 10-12/§4-6・R-87

## [memory_impression.py](../../../../../../../../src/shibuya/mind/memory/memory_impression.py)

engine.memory_impression — 記憶 M3 の器(印象の履歴と、本人が寝たときの書き直し・第 6 期 6-5)。

- 公開の関数とクラス
  - `ImpressionBook`(クラス): 印象の履歴と意味の記憶の器(M3)。書く口は :meth:`after_conversation`・:meth:`on_sleep`・:meth:`add_conclusion`。
  - `ImpressionEntry`(クラス): 履歴の 1 件(足すだけ)。``cause`` は LLM の呼び(原因つき)。
- import している内部モジュール: `shibuya.foundation.journal.log`
- 読む試験: `tests/engine/memory/test_m3_impression_and_trace.py`・`tests/engine/memory/test_mr65_guards.py`
- 決定の ID: 10-12・10-12/§4-6

## [memory_m1.py](../../../../../../../../src/shibuya/mind/memory/memory_m1.py)

engine.memory_m1 — 記憶 MR 第 6 期 6-5 の GPU の前に作る分(強さの式 M1・個人差・思い浮かぶ/見覚え・腕の切替口)。

- 公開の関数とクラス
  - `KindSpec`(クラス): 種類ごとの忘れる速さと足す項(MR1 (d)・MR12 (a))。``additive``: ``importance``・``none``。
  - `M1State`(クラス): M1 の強さの状態(記憶の器の子の持ち主 ``mem_layer.memory_store.m1``・状態台帳の腕の行 ``M0M``=腕 memory-model)。
  - `MemoryArms`(クラス): 6-5 の腕のいまの値(組み立てが 1 回読む)。
  - `arms`(関数): いまの腕(既定は ``m0``・``id``・``table``・``ruri-v3-30m``・``each``)。
  - `arms_on`(関数): 既定と違う腕が 1 つでもあるか(``cli.run`` のランの種類=結果を変える腕は「腕」に数える)。
  - `base_level`(関数): 行の配列 → 基底の強さ B(ACT-R の折衷形・秒)。``n == 0`` の行は −inf。
  - `check_arms`(関数): 組み立ての前の検査(器の無いランで既定と違う腕・people=memory で model=m0)→ いまの腕。違えば ``ValueError``。
  - `clarity_words`(関数): 強さ → 言葉(MR-0): ``A ≥ τ + margin`` は「はっきり」・``A ≥ τ`` は「うろ覚え」・それ以外は空文字。
  - `config_of`(関数): 〔検収 L1〕腕の値 → 設定の節と設定の指紋に入れる値(既定の腕なら空=既定のランの指紋と manifest の欄は前のまま)。
  - `exact_base_level`(関数): 正確な式 ``ln Σ t_j^(−d)``(試験の参照=全部の回の時刻)。
  - `forget_mask`(関数): 忘れる(消す)=手がかりがあっても見覚えに ``margin`` だけ届かない(上限なしの腕だけが使う)。
  - `forgetting_scale`(関数): 体の鍵の配列 → 忘れる速さの倍率 ``1 + cv·z``(z は標準正規=Philox の 2 語から Box-Muller・±``clip_sigma`` で切る)。
  - `recall_mask`(関数): 思い浮かぶ=``A ≥ τ``。
  - `recognize_mask`(関数): 見覚え=親しみの強さに目の前の手がかりを足すと ``τ`` を超える(手がかりの無い行は偽)。
  - `set_arm`(関数): 腕を選ぶ(CLI・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
  - `tau_from_m0`(関数): M1 の境目 τ の仮の値(expedient・人のデータで較正しない=検証側)。
  - `touch_times`(関数): ``recent_ns[rows]`` の直近の時刻に ``t_ns`` を足す(新しい順に 1 つずらす・空きは :data:`NO_TIME`)。その場で書く。
- import している内部モジュール: `shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.memory_embed`
- 呼び手: `shibuya.cli`・`shibuya.engine.systems.build`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_store`・`shibuya.mind.memory.memory_trace`・`shibuya.mind.plan.head_recall`・`shibuya.mind.relations.people`
- 読む試験: `tests/engine/memory/_mr65.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m1_strength.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`
- 状態台帳の行
  - 持ち主 `mem_layer.memory_store.m1`(`M1State`)
    - `M0M` M1State(記憶の強さ M1 の直近の時刻と人ごとの忘れる速さの倍率・第 6 期 6-5)(挙動 behavior・復元 required・腕 memory-model) 道筋 `mem_layer.memory_store.m1._scale`・`mem_layer.memory_store.m1._t_ns` 書ける系: decide・llm_receive・memory
    - `M0X` M1State・CueState の計数(第 6 期 6-5)(挙動 diag・復元 discardable) 道筋 `mem_layer.memory_store.m1._m1_stats` 書ける系: decide・llm_receive・memory
- 環境変数: `SHIBUYA_MEMORY_CUE`・`SHIBUYA_MEMORY_EMBED_MODEL`・`SHIBUYA_MEMORY_GRAIN`・`SHIBUYA_MEMORY_MODEL`・`SHIBUYA_MEMORY_PEOPLE`・名前を読めない所 1 か所
- 決定の ID: 10-12・10-12/§4-6・R-68・R-87

## [memory_shops.py](../../../../../../../../src/shibuya/mind/memory/memory_shops.py)

engine.memory_shops — 人も記憶の一つの腕の店の評価の行(第 6 期 6-5・検収 M4・腕 ``--memory-people memory``)。

- 公開の関数とクラス
  - `ShopTable`(クラス): 店の評価の行の表(記憶の器の子の持ち主 ``mem_layer.memory_store.shops``・状態台帳の腕の行 ``M0S``)。
  - `UncappedStoreMemory`(クラス): 人も記憶の一つの腕の店の評価の記憶(``StoreMemory`` の子=行の口だけ差し替える・行は :class:`ShopTable`)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.mind.memory.memory_store`・`shibuya.mind.memory.store_memory`
- 呼び手: `shibuya.mind.memory.memory`
- 読む試験: `tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_guards.py`
- 状態台帳の行
  - 持ち主 `mem_layer.memory_store.shops`(`ShopTable`)
    - `M0S` ShopTable(人も記憶の一つの腕の店の評価の行・第 6 期 6-5 検収 M4)(挙動 behavior・復元 required・腕 memory-people) 道筋 `mem_layer.memory_store.shops._first`・`mem_layer.memory_store.shops._last`・`mem_layer.memory_store.shops._n`・`mem_layer.memory_store.shops._poi`・`mem_layer.memory_store.shops._precision`・`mem_layer.memory_store.shops._source`・`mem_layer.memory_store.shops._valence` 書ける系: decide・llm_receive・memory
    - `M0X` M1State・CueState の計数(第 6 期 6-5)(挙動 diag・復元 discardable) 道筋 `mem_layer.memory_store.shops._shop_stats` 書ける系: decide・llm_receive・memory
  - 持ち主 `mem_layer.store` の別のクラス `UncappedStoreMemory`(行は `shibuya.mind.memory.store_memory` のカードを見る)
- 決定の ID: 10-12・10-12/§4-6

## [memory_store.py](../../../../../../../../src/shibuya/mind/memory/memory_store.py)

engine.memory_store — 記憶の器 M0(第 1 期 1-6・MR-0・MR11 (b)・MR16)。

- 公開の関数とクラス
  - `Cue`(クラス): 想起の手がかり(System 1 が体の状態から作る=今の 6b の q・ID の一致)。負/0 は「無し」。
  - `LegacyEvent`(クラス): 出来事の記録に無い出来事(仮の行の中身)。配列か整数。``t_ns`` はその回の時刻。
  - `LoggedEvent`(クラス): 〔第 2 期 2-3〕出来事の記録にある出来事への目印(``(t_ns, seq)``)と中身の写し。配列か整数。
  - `MemoryStore`(クラス): 記憶の器 M0(体ごとの行の範囲・SoA の列)。書く口は :meth:`remember` と :meth:`mark_shown`。
  - `MemoryView`(クラス): LLM に見せる形(MR-0): 言葉(``clarity``)と中身の粗さ(``grain``)と中身の ID。**強さの数は持たない**。
  - `RecallReport`(クラス): 1 回の想起の計数(``MemoryLayer`` が manifest の ``memory_summary.recall.counts`` に足す)。
  - `ShopPool`(クラス): ほかの表の候補(M0 は 7c の店の評価の行=今の ``sm_*``)。器の行と同じ score の順で競わせる。
  - `arm`(関数): いまの腕(``mem``=既定・``events``=記憶の器)。組み立てのときに読む。
  - `clarity_of`(関数): 強さ A → 言葉(MR-0)。A ≥ τ=はっきり・それ以外=うろ覚え(境目は expedient)。
  - `event_id_text`(関数): 目印 → テープの列の文字列 ``"t_ns:seq"``(無ければ空文字)。
  - `render_memories`(関数): ``MemoryView`` の組 → B5「記憶」の 1 行(今の描き方=``perception.renderer`` の項と行の組み立て・テンプレ v1.3)。
  - `row_caps`(関数): いまの種類ごとの行の上限(写し)。
  - `rows0`(関数)
  - `set_arm`(関数): 腕を選ぶ(CLI ``--memory-store``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
  - `set_row_caps`(関数): 上限なしの腕の種類ごとの行の上限(``episode``・``person``・``shop``・``None``=既定の値に戻す)。試験と感度の腕の口
  - `set_rows0`(関数): 上限なしの腕の最初の行の幅(``None``=記憶の表と同じ)。試験と測りの切替口(組み立ての時に読む)。
  - `to_item`(関数): ``MemoryView`` → 今の描き方が読む ``RecallItem``(刻みの番号に戻す=今の表と同じ値)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.events.body`・`shibuya.foundation.journal.log`・`shibuya.foundation.text.normalize`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.foundation.write_guard`・`shibuya.mind.memory.familiarity`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_embed`・`shibuya.mind.memory.memory_m1`・`shibuya.perception.renderer`
- 呼び手: `shibuya.cli`・`shibuya.engine.systems.build`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_shops`
- 読む試験: `tests/engine/memory/_m0.py`・`tests/engine/memory/_mr65.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/multiday/_md.py`・`tests/engine/multiday/test_md23_body_events.py`
- 読む試験(道筋で): `tests/engine/memory/test_mr65_guards.py`
- 状態台帳の行
  - 持ち主 `mem_layer.memory_store`(`MemoryStore`)
    - `M0` MemoryStore(記憶の器 M0・第 1 期 1-6)の行・仮の出来事の表・注釈(挙動 no・復元 derivable) 道筋 `mem_layer.memory_store._lg_cell`・`mem_layer.memory_store._lg_kind`・`mem_layer.memory_store._lg_object`・`mem_layer.memory_store._lg_partner`・`mem_layer.memory_store._lg_result`・`mem_layer.memory_store._ms_ev_seq`・`mem_layer.memory_store._ms_ev_t_ns`・`mem_layer.memory_store._ms_first_ns`・`mem_layer.memory_store._ms_imp`・`mem_layer.memory_store._ms_n`・`mem_layer.memory_store._ms_note`・`mem_layer.memory_store._ms_note_order`・`mem_layer.memory_store._ms_origin` 書ける系: decide・llm_receive・memory
    - `M0L` MemoryStore の記録の目印の seq(第 2 期 2-3)(挙動 no・復元 required・腕 memory-store) 道筋 `mem_layer.memory_store._ms_log_seq` 書ける系: decide・llm_receive・memory
    - `M0R` MemoryStore の録画(見せた時刻)・テープの列への控え・計数(第 1 期 1-6)(挙動 diag・復元 discardable) 道筋 `mem_layer.memory_store._ms_last`・`mem_layer.memory_store._ms_shown_ns`・`mem_layer.memory_store._ms_stats`・`mem_layer.memory_store._ms_tape` 書ける系: decide・drain・llm_receive・memory
- 環境変数: `SHIBUYA_MEMORY_STORE`
- 決定の ID: 10-12/§4-6・10-13b/§3・R-113

## [memory_trace.py](../../../../../../../../src/shibuya/mind/memory/memory_trace.py)

engine.memory_trace — 注意を向けずに見ていた人の浅い痕跡(第 6 期 6-5・MR6 の後段「注意を向けずに見ていた人が話題に出たとき」)。

- 公開の関数とクラス
  - `TraceView`(クラス): 浅い痕跡(保存しない=手がかりが来たときに組み立てる)。``places`` は ``(場所の種類, id, 回数)`` の組。
  - `played_along_share`(関数): 「LLM が覚えていないのに話を合わせた割合」=聞き手の記憶に指された相手が無い行のうち、話を合わせた行の割合
  - `shallow_trace`(関数): 出来事の記録から ``viewer`` が ``target`` を同じ場所の近い時刻で見ていた回を組み立てる(読むだけ)。
  - `trace_word`(関数): 聞き手に見せる言葉: 注意を向けた記憶=空文字(普通に描く)・浅い痕跡だけ=「見たような気もする」・何も無い=空文字。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.mind.memory.memory_m1`
- 読む試験: `tests/engine/memory/test_m3_impression_and_trace.py`・`tests/engine/memory/test_mr65_guards.py`
- 決定の ID: 10-12・10-12/§4-6

## [store_memory.py](../../../../../../../../src/shibuya/mind/memory/store_memory.py)

engine.store_memory — **店の評価の記憶**(D-120 7a・N1 (a)・N2 (i)(iii)・N4 (a)・N5 (a)・第296)。

- 公開の関数とクラス
  - `StoreColumns`(クラス): 〔第 6 期 6-5・検収 M4〕店の評価の行の列(``(体, 幅)``)。既定=体の表の ``sm_*`` そのもの(読む口=書かない)。
  - `StoreMemory`(クラス): 店の評価の記憶の書き手と読み口(``MemoryLayer`` が持つ・``--store-memory on`` のランだけ)。
  - `StoreRows`(クラス): 1 体の店の評価の行(空でない行だけ・行番号の順)。本段では誰も読まない(7c の読み口)。
  - `check_store_decay`(関数): 減衰の形を検査して返す(:data:`STORE_DECAY_MODES` のどれか)。
  - `check_store_sigma`(関数): 出どころ別の σ の表を検査して、全部の鍵を持つ辞書で返す(欠けた鍵は既定値)。
  - `valence_of_result`(関数): 結果コード → 向き(``OK`` +1・:data:`STORE_VALENCE_NEGATIVE` −1・それ以外 0)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.foundation.time_consts`・`shibuya.mind.memory.memory`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.mind.judge.store_choice`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.memory_shops`・`shibuya.mind.memory.wom`
- 読む試験: `tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_wom.py`
- 状態台帳の行
  - 持ち主 `mem_layer.store`(`StoreMemory`)
    - `O12` StoreMemory stats(挙動 diag・復元 discardable) 道筋 `mem_layer.store.stats` 書ける系: decide・llm_receive・memory
- 決定の ID: R-49・D-120・D-121・第 296

## [wom.py](../../../../../../../../src/shibuya/mind/memory/wom.py)

engine.wom — **会話からの店の抽出**(D-120 7b・N3 (a)・口コミ=伝聞の書き手・第297)。

- 公開の関数とクラス
  - `WomExtraction`(クラス): 1 発話の抽出結果。
  - `WomExtractor`(クラス): 店名の辞書と評価語の辞書(1 ランに 1 つ・世界は読むだけ)。
  - `check_wom_source`(関数): ``--wom-source`` の値を検める。
  - `hear`(関数): 抽出した店を聞き手(宛先)の店の行へ(出どころ=伝聞・精度 +重み × 1/σ²)→ 書いた行の数。
  - `normalize_v0`(関数): 正規化 v0: NFKC(全角/半角)・英字は小文字・空白を全部消す。
- import している内部モジュール: `shibuya.engine.poi_target`・`shibuya.mind.memory.store_memory`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.llm_io`・`shibuya.society.speech.layer`
- 読む試験: `tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_wom.py`
- 状態台帳の行
  - 持ち主 `wom`(`WomExtractor`)
    - `O15` WomExtractor stats・top・unmatched_words(挙動 diag・復元 discardable) 道筋 `wom.stats`・`wom.top`・`wom.unmatched_words` 書ける系: decide・llm_receive・memory
- 決定の ID: D-120・第 297・第 298・第 312
