# 2-0b 不応期を外した腕の計測: 独立検収

- 検収役: 実装を見ていない検収役(Opus 5.5)。対象は作業木(枝 `2-0b/refractory-arm`・土台 `f2405e3`)の未 commit の記録・道具・試験。発注の後の追記(活動層 off の A/B・2 万体の A/B・表の外の門 6 件・69 行・`rerun_same_after_tool_update.json`)も含む。
- 読んだもの: [README.md](README.md)・[refractory_calls.json](refractory_calls.json)・[refractory_calls.md](refractory_calls.md)・[rerun_same.json](rerun_same.json)・[rerun_same_after_tool_update.json](rerun_same_after_tool_update.json)・[tools/measure_refractory.py](tools/measure_refractory.py)・`tests/bench/test_refr20b_tool.py`・src の該当箇所(読むだけ)・作業場所 `_bc` のログ。
- 回したもの: CLI のラン 3 本(5,000 体)・小さな探りのラン 1 本(1,000 体)・試験 2 組。作業場所は作業木の根の `_bc_review`(終わりに消した)。`tests/c7` は回していない。封印した層は読んでいない。

## 判定: 条件つき受入

数値・道具・試験・決定論は受入。条件は記録の文言の直し(中 1 件=M1、低 L1・L2)。ランのやり直しは要らない。

## 1〜8 の確かめ

### 1. エンジン不変 ✓

- `git diff --stat -- src` は空。`git status --porcelain -- src` も空(変わったのは未追跡の `_bc/`・`refr20b/`・`tests/bench/` だけ)。
- 道具と試験に `monkeypatch`・`setattr`・モジュールの属性への代入は無い(grep 0 件)。道具は `cli.run`・`cli.parse_refractory_scale`・`resolve.refractory_ticks` を呼び、`arbiter.L4_*` を読むだけ。試験はアービタの純関数 `arbitrate` を直に呼ぶ。
- 69 行とも `shibuya_from_given_src` が真。`provenance.src_dirty_files` は 0。

### 2. 腕の作り方 ✓

- コードの根拠:
  - `cli.parse_refractory_scale` は `float(val)` を通し、条件名を `R.wake_condition_index` で引く。0 を拒む分岐は無い。
  - `resolve.refractory_ticks` が拒むのは `f < 0` と非有限だけ(docstring に「倍率 0 は床なし」)。`np.floor(分 × 0 + 0.5)` で 0 になる。
  - `systems/build.py` の `refractory_table = R.refractory_ticks(refractory_scale)` が、`systems/decide.py` の `R.set_refractory(..., refractory_table)` を通って `resolve.set_refractory` の `until = tick + tab[c]`(`np.maximum.at`)に届く。アービタの ① は `ru[agent, cond] > tick` で抑止するので、0 分なら偽になる。
  - `refractory_until` に書くのは `set_refractory` と `clear_refractory`(0 に戻す)だけ(grep)。
- 記録の値: 腕 B の 7 行(5,000 体の 6 群と 2 万体)は、どれも `suppressed`=0 で、`arbiter.suppressed` も 4 クラスとも 0。腕 A は 19,522〜89,604(どれも 0 より大きい)。69 行の `refractory_scale`(manifest)と `effective_minutes` は腕の定義どおり(B=11 条件とも 0.0・Ck=k 番目だけ 0・A=空)。
- CLI の実ランでも、11 個の旗が受け付けられ、診断の `suppressed` が 0 になった(3 の腕 B)。

### 3. 独立の再現 ✓

道具を使わず、作業木の根で `PYTHONPATH=src` にして `python -m shibuya.cli --agents 5000 --seed 1 --vocab-version v3 --activity on --policy mock [--refractory-scale …]` を 3 本並べて回した(`w6_v3_default`={語彙 v3・活動層 on})。

| 腕 | 呼数(CLI) | 記録 | final(CLI) | 記録 | 不応期の抑止 | 就寝抑止 | 会話セッション | 時ごとの呼 |
|---|---|---|---|---|---|---|---|---|
| A | 65,597 | 65,597 | `5f7ae9ff24005314` | 同じ | 19,731 | 10,971 | 226 | 24 時とも記録と同じ |
| B(11 個とも =0) | 82,919 | 82,919 | `5ef1bf66b413058f` | 同じ | 0 | 11,268 | 287 | 同じ |
| 内受容だけ 0 | 79,447(+13,850) | C6 79,447(+13,850) | `b55e3e49801bc1c9` | 同じ | 6,904 | 11,857 | 266 | 同じ |

- 活動層の場所起床の抑止も、A 211,925・B 253,778 で記録と同じだった。壁時計は 1 本 83〜95 秒(3 本並列)。
- 発注にある「C5(内受容だけ 0)」は、道具の番号では **C6** にあたる(`WakeCondition.INTEROCEPTION`=5 なので C6)。C5 は計画境界の移動・待機(`PLAN_TRANSIT`・増分 −12)。回したのは内受容で、+13,850 はこの腕の値。記録は `WakeCondition` の値+1 で番号を振っていて、一貫している。

### 4. 表と外挿の検算 ✓

道具を読み込まずに、`refractory_calls.json` の 69 行と、10e の `sides/ret.json`・`budget_10e.json` から計算し直した。

- 倍率 B/A(7 群)は md の表と一致した: 1.2641・1.2786・1.2707・1.2431(2 万体)・1.2793・8.4384・7.8923。
- 69 行とも `calls` が Σ`calls_by_condition` とも Σ`calls_by_hour` とも等しい。
- C1〜C11 の順位(増分の降順・同点は番号順)は、5 群とも道具の表と md の行に一致した。上位 3 つ:
  - v3 の seed 1〜3: 内受容 > 場所の変化 > 一般活動(seed 1 は +13,850・+3,322・+796)
  - 関係 on: 同じ並び(+15,071・+3,710・+1,350)
  - v1: 場所の変化 +310,492 > 内受容 +5,985 > 一般活動 +1,872
  - 足し算で表せない分(−615・+1,017・−833・−2,316・+67,525)も一致した。
- 既知の答え: 4 構成の腕 A の呼数と final は 10e の `ret.json` と同じ(65,597/`5f7ae9ff…`・69,111/`73a78288…`・51,835/`24375ee3…`・50,301/`e0054a83…`)。`n_full` は 390,067。
- 外挿: 39 万体の既定の呼数/日は 65,597 × 390,067 / 5,000 = 5,117,445。腕 B はそれに 1.264067 を掛けて 6,468,793/日、7 日で 45,281,552。仮の割りでは判断モデル 6,133,804・LLM 334,990(会話ターンの割合 4,294/82,919)。L4 の線の 1.617 倍。seed の幅は 6,468,793〜6,543,291。関係 on は 6,897,399、v1 は 34,123,529、活動層 off は 30,970,618(L4 の 7.74 倍)。どれも JSON・md・README と一致した。
- 2 万体: 倍率 1.2431(5,000 体の 1.2641 との差 −0.0210・相対 −1.66%)。呼/体/日は A 13.31(+1.5%)・B 16.55(−0.2%)。条件ごとの体あたりの増えも README §11-2 と一致した。
- 「仮」の明記: README の §0・§5・§6-6・§7-1、md の表の見出し「仮の割り」、道具の docstring に書いてある。manifest の `calls_by_model` は判断モデル 0・LLM=全呼のままで、道具は変えていない。

### 5. 負の対照の読み ✓(記録の書き方は正しい。発注の言い方が一部ずれている)

- C8〜C10: 起床候補を作る場所は次のとおりで、`PROXIMITY_SWAP`・`BEING_WATCHED`・`OVERHEARD` を出す場所は無い。src の grep でも、この 3 つは `engine/commit.py` のクラスの写像にしか出てこない。`change_detect.py` の docstring にも「知人出現・近接入替・被注視・傍受は C2 では検出しない」とある。C10 の資料の D-49 ③ と同じ事実で、不応期を 0 にしても候補が無いから A と同じになる。
  - 計画境界(`systems/body.py`): PLAN_*
  - 検出(`change_detect.candidates`): INTEROCEPTION と CELL_BLOCK だけ
  - 会話(`conversation.wake_candidates`): CONVERSATION_TURN
  - 顕著行為(`processes/salient.py`): CELL_BLOCK
  - 活動の満了: ACTIVITY_EXPIRY
  - 関係(`relations.acquaintance_candidates`): ACQUAINTANCE
  - 艦隊の再投入: 呼んだときの条件の写し
- C1・C2 は理由が違う。記録はそれぞれ正しく書いている。
  - C1: 会話ターンの不応期はもともと 0 分なので、倍率 0 を掛けても変わらない。
  - C2: 候補が無いのではない。就寝境界の候補は D-62 (a) でエンジンが実行し、アービタの前に落とす(`systems/body.py` の `to_bed`・`plan_sleep` は既定 on)。だから発射は 0 で、タイマーも張られない。
  - 発注の「C1・C2・C8〜C10 は起床の候補を出す処理が無い=D-49 と同じ」が当てはまるのは C8〜C10 だけ。
- 「近接入替=最大の暴発源」(知覚契約書 §6 の表の行)を今のエンジンで確かめられない理由(候補を出す処理が無い)は正しい。10-13b §4-2 の 1(知覚の事実として扱う)への繋ぎも原文どおり。

### 6. 表の外の門の一覧 ✓(6 件とも実在する。ただし網羅ではない=L2)

| 名 | 出典の記号 | コードの門 |
|---|---|---|
| 活動層の候補の落とし | `engine/activity.py` `suppress_cell_block` | `activity_until > tick` の体の CELL_BLOCK を落とす。`systems/perceive.py` が検出の後に呼ぶ |
| 就寝抑止 D-56 | `engine/arbiter.py` `sleep_suppressed_total` | `arbitrate` の「⓪ 就寝抑止」(⓪-a の注で ⓪-b と呼ばれている) |
| 域外抑止 D-66 | 同 `outside_suppressed_total` | `arbitrate` の「⓪-a 域外抑止」 |
| アービタの合流 | 同 `merged_total` | `arbitrate` の「③ 同一体の合流」 |
| 会話の招待の間隔 | `engine/conversation.py` `PAIR_INVITE_REFRACTORY_TICKS`(60)・`SPEAKER_INVITE_REFRACTORY_TICKS`(30) | `stamp_invite_refractory` と抑止の理由 `pair_refractory`/`speaker_refractory`。腕 A の行で `conv_invite_refractory_blocked` 95 件 |
| 知人出現の同一相手 | `engine/relations.py` `REL_ACQ_PAIR_REFRACTORY_MIN`(60) | `enable_acquaintance_wake` の `_acq_pair_ticks` を使い、`acquaintance_candidates` で落とす(`stats["acq_pair_refractory"]`) |

- 出典に行番号は無い。試験 `test_gates_outside_table_symbols_are_defined_in_their_files` は、記号の定義があるかを正規表現で照らす(負の対照 3 つつき)。
- 載っていない門が 2 つある(L2)。

### 7. 試験 ✓

- `tests/bench tests/tools`(`-n 2 --dist loadfile -m "not slow"`): 63 passed(3.8 秒。bench 12 本+tools 51 本)。
- 既存の ablation の試験 2 本(`tests/engine/test_ablation23_switches.py` 39 本・`tests/c8/test_ablations_table.py` 24 本): 63 passed(20.6 秒)。
- 新しい試験は data を使わない(読むのは git に入っている 10e の `ret.json`・`budget_10e.json` と src)。CI の `-m "not gpu and not slow"` の組に入る。

### 8. 記録 ✓

- 新しい 8 ファイルに、絶対パス・ホスト名・個人名は無い(grep 0 件)。どれも LF で BOM なし。`tools/scan_secrets.py` は CLEAN。
- `rerun_same.json` の 65/65 は、本当に独立した 2 回のランの比べ。`run` は在る行を飛ばす作りなので、ログで確かめた。
  - 1 回目(`rows_run1`): 63 本を回した。A・B の 2 本は直前の試しのラン(`first_AB.log`)の行で、これも実際に回したもの。
  - 2 回目(`rows_run2`): ログでは 65 本とも「済」(「在る」は 0)。
  - 3 回目(`rows`): これも 65 本とも「済」。
  - `same` は 2 つのディレクトリの行を (構成・腕・seed・体数) で突き合わせ、`SAME_KEYS` の 11 欄を比べる。
- 検収役が、2 回目と 3 回目を `SAME_KEYS` の外の欄(`activity_counters`・`conversation_counters`・`calls_by_model`・`l4`)まで比べても 65/65 同じだった。記録の JSON の 69 行は `_bc/rows` の 69 ファイルと中身が同じ。

## 欠陥

### 中

**M1. 活動層 off の結果を「門だけ」の重みとして書いている**(README §0・§5・§11-1 の見出し)。

- 構成 `w6_v3_activity_off` は活動層を丸ごと外す。外れるのは門だけでなく、活動の満了の起床・活動の設定・あたり歩行・B4b の行も一緒(CLI の `--activity` の説明)。だから腕 A も 65,597 から 50,301 に変わる。src には門だけを外す口が無い(`suppress_cell_block` は `perceive.py` から条件なしで呼ばれる)。
- §5 の「活動層の門だけでも、外すと既定 v3 の倍率は 1.26 倍から 7.89 倍に上がった(39 万体で約 3,097 万呼/日)」は、測った量と違う。T3 で層を残して門だけを外すなら、A の土台(満了の起床 19,055 を含む)が違うので、倍率も 3,097 万も変わる。
- §0 の「約 6.6 倍ぶん抑えています」は倍率の差(7.89 − 1.26 = 6.63)のことで、比(6.24 倍)ではない。読み違えやすい。
- 直し方: 「活動層ごと off(門・満了の入口などを一緒に外す)で 7.89 倍。門だけの腕は src を変えないと作れないので測っていない。増えの 95% が場所の変化なので、主に効いているのは門と読める(推測)」と書く。§0 は「倍率の差 +6.63」と書く。ランのやり直しは要らない。

### 低

- **L1.** README §4-1 の「就業・移動の 1 種ずつの腕は ±0.5% 以内」が数値と合わない。v3 seed 3 の移動が +420(+0.65%)、関係 on の就業が +852(+1.23%)、v1 の移動が −262(−0.51%)。直し方: 実際の範囲(−0.5%〜+1.2%)で書くか、v3 の seed 1・2 に限ると書く。
- **L2.** 表の外の門の一覧(`gates_outside_table`・README §5・§6-4・§11-3)が網羅になっていない。腕 B でも残る「いつ考えるか」の門のうち、既定 v3 で働いているのに載っていないものが 2 つある。
  - (a) 意図の保持(`engine/intent.py` `IntentLayer.suppress_wakes`): 意図を持つ体の CELL_BLOCK と ACTIVITY_EXPIRY を落とす。検収役の小さなラン(1,000 体・1 日・既定 v3)で `cell_block_suppressed` 283・`expiry_suppressed` 17。
  - (b) 就寝境界をエンジンが実行する D-62 (a)(`systems/body.py` の `to_bed`): 判断を呼ばない。C2 が 0 になる理由でもある。
  - ほかに、既定では効かない門として 9a の歩行退出(`presence.suppress_walker_wakes`)と L4 の繰り延べがある。
  - 直し方: 2 行足すか、「主なもの・網羅ではない」と書く。§0 の「上限になるのは…門が残る場合に限ります」も同じ。量は小さい見込み(意図の保持の落としは、5,000 体に比例させると活動層の門の約 0.7%=推測)で、結論の数値は動かない。
- **L3.** README §11-1 の「活動層 off の腕 A が少ないのは、活動の満了の起床が無いため」は、分解の一部しか見ていない。A の差 15,296 は、満了 +19,055・内受容 +8,716・場所の変化 −13,125・会話ターン +1,161・計画境界 −511 の和。「主に」や「推測」を付けるか、分解を書く。
- **L4.** README §10 の再現の手順に、2 回目を回す前に 1 回目の rows を別の名へ移すことが書いていない。`run` は在る行を飛ばすので、書いてあるとおりに回すと 2 回目は全部「在る」になり、`same` が同じ行どうしを比べてしまう。直し方: 「1 回目の `_bc/rows` を `rows_run1` へ移してから回す」を 1 行足す。
- **L5.** `same` の比べる欄(`SAME_KEYS`)に `activity_counters`・`conversation_counters`・`calls_by_model`・`l4` が無い(検収役が足して比べた結果は同じ)。任意の直し: 足す。
- **L6.** 作業場所 `_bc/` は gitignore されていないので、git status に出る(中に旧版の道具 `measure_refractory_v1.py.bak` とログがある)。commit のときに明示したパスだけをステージすれば足りる(親の段取りの注意)。

## 親に確かめてほしいこと

1. 発注の「C5(内受容だけ 0)」は、道具の番号では C6(C5 は PLAN_TRANSIT)。記録の側は一貫している。親の要約や台帳に「C5=内受容」と書いていないか。
2. M1: 活動層 off の 7.89 倍・3,097 万呼/日を PENDING や計画に写すなら、「門の重み」ではなく「層ごと off」の量として写す。
3. L2: 表の外の門の一覧を T3 の設計の入力に使うなら、意図の保持(段 2c)と D-62 の就寝の実行も並べる。
4. 範囲外の気づき: `agents/state.py` の `REFRACTORY_MINUTES` の注「知人出現(…同一相手 60 分は C2 未実装)」は、`relations.py` の `REL_ACQ_PAIR_REFRACTORY_MIN`(関係 on で働く)と食い違う古い注。本段では src を触らないので、記録だけ。
