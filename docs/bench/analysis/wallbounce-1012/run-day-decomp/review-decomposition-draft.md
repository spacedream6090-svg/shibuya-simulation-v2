# 検収: run_day の分解の口の案(草案 v2-run-day-decomposition-draft.md・第330)

- 検収役 Opus 5.5(起草した調査役とは別)。親 Fable 5.1 が最終判断する。コードと追跡ファイルは触っていない。
- 対象: [草案](../../../../design/v2-run-day-decomposition-draft.md)(411 行)と本フォルダの道具と表。正: [回答 10-12b](../../../../design/v2-answers-2026-10-12b.md) §6・[実装の計画](../../../../design/v2-implementation-plan-2026-10-12.md) 第 1 期・状態台帳(`engine/state_ledger.py`・`state_ledger_ast.py`・`state_hashes.py`)。
- コードの版: 作業木の HEAD は `4bb8d55` だが、`0389689..4bb8d55` の差は `tests/tools/test_commit_check.py` だけ(`git diff --stat 0389689 HEAD -- src/ tests/`)。草案の行番号はそのまま使える。
- 印: 「推測」=確かめていない読み。

## 判定: 条件つき受入

地図(§1)と方針(実行順の区間で切る・宣言の表・状態台帳の語彙・既存の `freeze`/`writable` を使う)は妥当で、数の大半は再現した。道具の再実行で final と呼数は報告と全部一致し、負の対照 4 本も報告どおり落ちた。

ただし、ユーザーの指示の中心である「宣言の外を書いたら試験で落ちる」を、段 A(SoA の実行時の検査)は保証していない。`np.<ufunc>.at` で書く列は、宣言から外しても落ちない(下の K1・実測で 2 本)。条件 1〜6 を満たしてから切りに入る。

### 受入の条件

1. **K1 を直す**: ufunc.at で書く列にも段 A が効くようにする(案: `resolve._require_thawed` を、状態の物の `frozen` ではなく書く配列の `flags.writeable` を見る形にする。`economy/ledger.py:_apply_cash` が既にこの形)。直したら、ufunc.at で書く列ごとに負の対照を足す(下の T1)。
2. **K2・K3 の抜け道を段 D に入れる**: `flags.writeable = True`・`setflags(write=...)` の直書きと、SoA の配列の切り出しやビューを層に持たせることを、状態のモジュールと resolve の外では禁じる静的な検査を足す。台帳(`Ledger`・`GoodsLedger`)の書き込み窓も、系ごとに解く形にするかを決める。
3. **K4: 宣言の作り方**: 動的な測り(6 構成・窓の tick)を正にせず、静的な閉包(系 → 層のメソッド → resolve の口、差し込んだ関数も含む)を正にする。動的な測りは、閉包の漏れを見つける側に回す。宣言を固める前に、byte-check の 19 構成と艦隊・再生・`response_delay=2`・再開の試験で段 A を回す。
4. **K5: 系ごとの指紋の基準値**: 区間の境目を、系の境目に合わせて細かくする(7 系は今の区間の一部か和。下の K5)。指紋に `RunStats` と scratch も入れる。
5. **R1: `focus_request` を `TickScratch` の毎 tick の空にする対象から外す**(または「空」の定義を、今と同じ「FOCUS_NONE で埋める」にする)。
6. **§0-1 の問いを言い換える**(§5)。ユーザーに聞くのは 1 件にまとめ、残り 4 件は親の判断として後でまとめて報告する。

## 1. 事実の検査(HEAD のコードを自分で読んだ)

| # | 草案の主張 | 判定 | 確かめ方・正しい値 |
|---|---|---|---|
| F1 | `run_day` 1928〜4979(3,052 行)・引数 115 | 一致 | AST(`ast.parse` で FunctionDef の lineno/end_lineno・args+kwonlyargs=115・*args/**kw なし)。本体の最初の文(説明の次)は 2411 |
| F2 | 入れ子の関数 21(直下 17+内側 4) | 一致 | AST。直下 17 の名は草案と同じ。内側は `_classical_acq` 3145・`_classical_partner` 3160・`_session_partners` 3180・`_revert` 4260 |
| F3 | tick のループ 3631〜4531・最上位の文 112 | 一致 | AST(`for tick in ...` の lineno・end_lineno・len(body)) |
| F4 | SoA の静的な書き手は resolve.py の関数 63 本だけ(列名 91 のうち 87) | 一部不一致 | `soa_writers_ast.py` を再実行し、記録の json と同一(source 欄を除く)。属性の名の AST では 63 本・87 列で一致。ただし `economy/ledger.py:_apply_cash` が `agents.money`(世帯の現金として採用した同じ配列)を `np.add.at(cash_p, ...)` で書く。別名なので AST の数えには出ない。resolve の窓の中から呼ばれるが、「書き手は resolve.py だけ」は言い過ぎ |
| F5 | 静的な書き手の無い列 5(fatigue_stage・hunger_stage・thermal_stage・noise_stage・invocation_distance) | 不一致 | 道具の出力は **4 列**(`fatigue_stage`・`invocation_distance`・`noise_stage`・`thermal_stage`)。`hunger_stage` には resolve に静的な書き手がある。91−87=4 とも合う |
| F6 | resolve の口 49 種を 17 ファイルが呼ぶ | 一致 | `resolve_callers.json` の `external_files` が空でない口 49・ファイル 17 |
| F7 | `freeze()`(agents/state.py:786)・`writable()`(:802)・World と PerceptionState も同じ形 | 一致 | 該当行を読んだ。run.py:2776〜2777 で agents・world を凍結。知覚の状態は `processes/salient.py:164` で凍結 |
| F8 | ハッシュに `行の鍵:道筋` の文字列(state_hashes.py:327)と `module.qualname`(`_qual`・:94)が入る | 一致 | 327 行 `tag = f"{key}:{path}"`。`_qual` は 94 行で定義し、160・186・192・225 行で enum・dataclass・namedtuple・値のクラスの札として流す。`behavior_hash` は 267 行で `external_digest(owners, SL.behavior_items())` を足す |
| F9 | `pending` を 3702 で束縛し直す・`_receive_arrivals` と `_hash_owners` は遅れて名を引く | 一致 | 3702 `due, pending = _split_due(pending, tick)`。`_receive_arrivals` は `pending.append`、`_hash_owners`(3373)は `_RunDayLocals(pending, ...)` |
| F10 | `_relay_tables` の nonlocal = b_agent・b_cond・b_tick・b_cell・b_start・w17_substituted | 一部不一致 | 3439 の nonlocal は **5 つ**(b_agent・b_cond・b_tick・b_cell・b_start)。`w17_substituted` は束縛し直さず `append` で中身を変えるだけ(3445) |
| F11 | 描画は想起のときに記憶 3 列(mem_importance・mem_last・mem_n)を書く(§1-3・§3-3 の 6) | 不一致 | `MemoryLayer.recall`(memory.py:326〜)と `_recall_with_store` は SoA を**読むだけ**で、書くのは想起の計数(`rs`=外の状態)。L14 で記憶 3 列が変わった(v3 記憶+関係+店の dyn: mem_importance 6・mem_last 16・mem_n 16)のは、会話ターンの発話 `_utter` → `note_utterance` → `write_memory` の経路。負の対照 3 の追跡(memory.py:611 note_utterance)とも合う。結論の「`decide` の宣言に記憶を載せる」は、`_utter` があるので変わらない |
| F12 | 描画と方策へ差し込む無名関数 5 つ(3065・3074・3143・3184・3193) | 不一致 | lambda は **3 つ**(3074 天候の日・3143 知人・3193 想起)。3065 は工場関数 `_named_closed_lookup(...)` の戻り値、3184 は入れ子の def `_session_partners`。§3-3 の 6 の 3155・3169 は `classical_policy.acq_fn`・`partner_fn` への入れ子の def の代入 |
| F13 | 前の tick の束縛を読む 3 つ・中身を変える 24・読むだけ 82 | 一致(分類の名に注意) | static_map の `loop_vars_by_cat` と同じ数。ただし「読むだけ 82」には、メソッドや引数越しに中身が変わる物が入る(`talk_stats` は `intents_from_responses(stats=talk_stats)` で書かれる。agents・ledger・arbiter ほかの層も同じ)。箱の表(§2-3)に `talk_stats` が無い(K8) |
| F14 | 台帳 189 行のうち書き手が見えた行 134(SoA 69・外 65)・2 区間以上の列 28・行 27・activity 7 区間・O19 と O70 は 5 区間 | 一致 | `dyn_*.json` 6 本を自分で集計し直した。activity = E1・L2・L3・L6・L8・L17・L18。O70 = E1・L2・L3・L8・L22 |
| F15 | 試験の差し替え 9 ファイル 20 か所 | 一致 | `grep setattr tests` で `shibuya.engine.run` の名を差し替える行(`tests/engine/discard_probe.py` を含む 9 ファイル・20 行) |
| F16 | `state_ledger_ast.py` に `engine/run.py` が 19 か所・`state_ledger.py` に 1 か所 | 一致 | `grep -c` |
| F17 | 活動層・古典・想起優先の候補合成は起動時に表を写して持つ(3044・3024・3122) | 一致 | 3024・3044・3122 で `boundary_agent=b_agent` を渡す。3461〜3468 で止める |
| F18 | §1-7 の世界過程ごとの書き | 一致 | `proc_*.json` 3 本を集計し直した。rail は O36・O70(presence)と O74、large_event は O37・O70・O74、waste は台帳の O59・O60・O80・O81・O93 |
| F19 | 重さ +16〜29%(15.1〜15.7 秒 → 18.3〜19.5 秒) | 計算は一致・再計測はしていない | (18.3−15.7)/15.7=16.6%・(19.5−15.1)/15.1=29.1% |
| F20 | 「最初の試作(変わった列だけを許可)は 6 構成とも L17 で落ちた」 | 未確認 | 当時の許可の表が残っていないので再現できない |

## 2. 道具の再実行

親の venv(`.venv/Scripts/python.exe`)・`PYTHONPATH=src`。`import shibuya` が作業木の src を指すことを先に確かめた。1,000 体・seed 1・出力は scratch の外へ出していない(道具は標準出力に json を出すだけ)。

| 構成 | noprobe(final・呼数) | guard_poc(final・呼数) | 報告の値 | 判定 |
|---|---|---|---|---|
| v3 既定・1 日 | `a2edde01b409d6a1`・12,614 | `a2edde01b409d6a1`・12,614 | `a2edde01b409d6a1`・12,614 | 一致 |
| v3 既定・2 日 | `08013362b035909d`・25,814 | `08013362b035909d`・25,814 | `08013362b035909d`・25,814 | 一致 |
| v3 記憶+関係+店+同席 | `28a316167605d410`・12,698 | 同じ | 同じ | 一致 |
| v3 古典+記憶+関係 | `a7c16d0fd2d59a0a`・15,836 | 同じ | 同じ | 一致 |
| v1 edge | `9a7c5f0b66359886`・10,142 | 同じ | 同じ | 一致 |
| v2 edge | `5c881f69e0894b50`・9,942 | 同じ | 同じ | 一致 |
| golden の帰無腕 | `bee59e96a1849734`・19,144 | 同じ | 同じ | 一致 |

負の対照(草案の 4 本): 4 本とも落ち、落ちた場所も `guard_results.jsonl` と同じ。

| 外した列 | 結果 | 落ちた場所 |
|---|---|---|
| L2:agents.thermal | 落ちた | environment.py:299 → resolve.py:2742 set_thermal |
| L17:agents.money | 落ちた | resolve.py:2224 → ledger.py:640 `_apply_cash`(台帳**自前の**検査の ValueError。numpy ではない) |
| L14:agents.mem_last | 落ちた | memory.py:611 note_utterance → resolve.py:954 write_memory |
| L12:agents.rel_last | 落ちた | relations.py:976 copresent_step → resolve.py:1004 write_relations |

**追加の負の対照(検収役が足した・v3 既定 1 日)**:

| 外した列 | 区間で実際に変わった数(dyn_v3_default_2d) | 結果 |
|---|---|---|
| L14:agents.refractory_until | 129 | **落ちない**(ok・final `a2edde01b409d6a1`・12,614) |
| L17:pois.revenue | 81 | **落ちない**(ok・同じ final) |
| L17:pois.stock | — | 落ちた(resolve.py:2257 の添字の書き) |
| L17:agents.holdings | — | 落ちた(resolve.py:2265 の添字の書き) |

numpy 2.5.3 の単体の確かめ: `writeable=False` の配列に `np.add.at`・`np.maximum.at` は通り、値が変わる。`fill`・`out=`・`copyto`・`put`・`sort`・`+=`・添字の代入は止まる。凍結の前に作ったビューは、元の配列を凍結した後も書ける。

記録の小さな欠け: `guard_results.jsonl` に v3 既定 1 日の ok の行が無い(草案 §5 の表は「同じ」と書く)。今回の再実行で同じ値を確かめた。

## 3. 欠陥

### 3-1. 結果を動かす欠陥

- **R1 `focus_request` を毎 tick 空にする scratch に入れている**(§1-4 では「ループの外で作り中身を変える」側、§2-3 では `TickScratch`=tick の頭で空)。今は個体数ぶんの 1 本のバッファで、L6 のどの分岐も `FOCUS_NONE` で埋め直してから L17 の `resolve.apply(focus_request=...)` に渡す(3796〜3810・4210)。「空」が `None` になると、注視の腕(`attention_on`)で L6 の `if focus_request is not None` が飛び、L17 に `None` が渡って結果が動く(推測。今の 6 構成に注視の腕は無く、測りでは出ない)。条件 5。

### 3-2. 切り方の欠陥

- **K1 段 A は ufunc.at の書きを止めない**(§2-2 の実測)。`writable()` の解除を列ごとにしても、`np.<ufunc>.at` は numpy の書き込みの旗を見ない。コードは既にこれを知っていて(resolve.py:330 の `_require_thawed` の説明・ledger.py:631 の注)、状態の物の `frozen` を見る形で塞いでいる。しかし試作の差し替えは窓に入るとき `_frozen=False` にするので、列ごとの許可の外でもこの検査を通る。resolve で ufunc.at を使う列: `refractory_until`(820 `np.maximum.at`)・`pois.revenue`(2264・2362)・`pois.stock`(2262・物の台帳の無い経路)・`holdings`(2717・消費の経路)。草案 §2-6 の「宣言の外の列を書けば numpy が ValueError を投げ、書いた行で止まる」は、この 4 列では成り立たない。条件 1。
- **K2 thaw を通らない解除が 3 か所ある**: `economy/goods.py:446`(在庫の窓)・`economy/ledger.py:298`(台帳の窓)・`resolve.py:3224 _restore_array_into`(再開の復元)は `flags.writeable = True` を直接書く。段 D ④ は `writable()`・`thaw` の呼び出しだけを見ているので、ここは抜ける。段 D に「旗の直書きは決まったファイルだけ」を足す。台帳と在庫はもう自前の凍結の窓を持つので、系ごとに解く形に広げれば、金と物の台帳の行(外の状態)も段 B の標本ではなく実行時に止められる(案)。条件 2。
- **K3 ビューと別名の抜け道**(推測。実例は未発見): 凍結の前やまだ書ける間に作ったビュー(`arr[a:b]`・`reshape`)は、元の配列を凍結しても書ける(numpy 2.5.3 で確かめた)。今は層が持つのは同じ配列そのもの(例 `attach_household_cash` は `np.asarray` で同じ物)なので旗は効く。将来の層が切り出しを持つと段 A は効かない。段 D で禁じる。条件 2。
- **K4 宣言の素案が 6 構成の観測から作られている**: `allow.json` は「窓の tick で変わった列 ∪ 区間で呼ばれた resolve の口が静的に書く列」。呼ばれなかった口の列は入らない。6 構成で動かない腕(親しみの fam_* 5 列・注視の focus_*・行列の queue_*・hotel・dispatch・艦隊・再生・`response_delay=2`・再開・止めたラン)は、宣言から漏れる。外の状態の見えない 55 行の扱いは草案に無い。今のままだと、19 構成で段 A を入れた時点で落ちて宣言を足す、を繰り返す。宣言の正は静的な閉包にし、閉包には描画へ差し込んだ関数(3074・3143・3193・`_named_closed_lookup`・`_session_partners`・`acq_fn`・`partner_fn`)を通る経路も入れる。AST ではこの経路をたどれないので、閉包は手で書いた表と段 A の実行時の検査で突き合わせる。条件 3。
- **K5 系ごとの指紋**:
  - (a) 「区間=系なので区間の digest と突き合わせれば系ごとに確かめられる」(§2-7)は、7 系で成り立たない。`llm_receive`(L11 の前半)・`wake_filter`(L11 の後半+L12 の前半)・`relations_wake`(L12 の中)・`wake_assemble`(L12 の後半)・`memory`・`familiarity`・`energy_after`(L20 を 3 つに割る)。どれもループ本体の最上位の文で割れるので、`dyn_writers.py` の `BOUNDS` を系に合わせて細かくすれば足りる。
  - (b) 指紋は宣言した書く欄だけの digest。宣言の外の外の状態の書き(段 B が標本の tick だけなので見逃したもの)は、その系の指紋に出ず、後でそれを読む系の指紋に初めて出る。差の場所を誤って示す。
  - (c) 同じ指紋で中身が違う場合がある。(i) 台帳の `multiset` の行と順を持たない辞書・集合は、並べ替えてから digest を取る。並びの差は消える(台帳が正しければ挙動に効かない)。(ii) `RunStats` と `result` の積算 23 欄(呼数を含む)が指紋に入っていない(`Access.stats` はあるのに、§2-7 の digest は SoA・行・scratch だけ)。(iii) 台帳の外のキャッシュ(描画のキャッシュは除外の一覧)とテープ・艦隊は入らない。
  - 対策: 指紋に stats を入れる。段 1 では小さな人数で全部の tick を取る(今の基準値は 1 日 66 tick の窓だけ)。条件 4。
- **K6 「読む欄」の宣言を何も確かめない**: 段 D ③ は箱の属性の単位で、層のメソッドの中の読みは追わない。ユーザーの指示は「読む欄と書く欄を宣言」。落とす対象は書きだけでよいが、確かめない読みの宣言は古びる。読みは「文書(強制なし)」と明記するか、試験の中だけ箱の属性の読みを記録して宣言と突き合わせる。
- **K7 試作の守りはループの中(L0〜L24)だけ**: `guard_poc.py` は L 以外の区間で `cur=None`=全部を許す。drain(E0)・最後の締め(E1 は activity・transit_* を書く)・組み立て(S)の宣言は試されていない。`R2 drain` と `D2 day_close` の宣言は、試作では裏づけが無い。
- **K8 箱の表から漏れた局所**: `talk_stats`(会話の相手の由来の診断。引数越しに書かれる)が §2-3 のどの箱にも無い。static_map の「読むだけ」の分類は、引数やメソッド越しの書きを数えない。箱へ移すときは、局所を全部、箱のどれかに割り当てる表で漏れを 0 にする。
- **K9 外の状態の検査の粒度(§0-1 の 4)は台帳の行より細かくできる**: `item_digest(owners, key, path)` は道筋ごとに取れる(state_hashes.py:296)。宣言を `O55:runner.traffic.*` のような道筋の単位にすれば、行を割らず(ハッシュの札は変わらず)、O55 の 3 つの持ち主と O73(12 の過程の計数)の書き手を分けられる。「行を割るとハッシュが変わるので行の単位にする」は二択ではない。

### 3-3. 記録の誤り

1. §1-6: 静的な書き手の無い列に `hunger_stage` を入れている(正しくは 4 列。F5)。
2. §1-3: `_relay_tables` の nonlocal に `w17_substituted` を入れている(F10)。
3. §1-3 の末尾・§3-3 の 6: 無名関数の数と行(F12)。
4. §1-3 の末尾・§1-2 の L14・§3-3 の 6: 「描画は想起で記憶を書く」(F11)。書くのは `_utter`。
5. §0・§1-6: 「SoA の書き手は resolve.py だけ」に、`ledger._apply_cash` が別名で `agents.money` を書く例外の注が無い(F4)。
6. §2-6: 「宣言の外の列を書けば numpy が ValueError を投げる」(K1)。
7. §2-7: 「区間=系なので」(K5 (a))。
8. §2-8 の見出しは「土台 8 つ」だが、行は 1-1〜1-9 の 9 行(計画の書き方は「T0(1-1)+残りの土台 1-2〜1-9」)。
9. §5: `guard_results.jsonl` に v3 既定 1 日の ok の行が無い(表は「同じ」)。
10. §4 の小さな点: flecs の組み込みの phase に `OnStart` が抜けている。MATSim の QSim.java は `listenerManager.fireQueueSimulationBeforeSimStepEvent`/`AfterSimStepEvent` を呼ぶ形で、`MobsimBeforeSimStep` の名は直接は出ない。`MobsimEngine.java` に `doSimStep` は無く、`Steppable` から受け継ぐ。

### 3-4. 試験の欠け

- **T1** ufunc.at で書く列(refractory_until・pois.revenue・pois.stock・holdings ほか)の負の対照が無い。足していれば K1 は試作の時点で見つかった。
- **T2** 段 B(外の状態)・段 C(scratch)・段 D(静的)の負の対照が無い。どれも試作が無い。最低でも「宣言から外の状態の道筋を 1 本外すと落ちる」を 1 本ずつ。
- **T3** 系の外(drain・最後の締め・組み立て)の段 A の試作が無い(K7)。
- **T4** tick の中の古い束縛の検査が無い。条件つきでしか代入しない局所を後の文が読むと、今は前の tick の値を読む。`TickScratch` を空にすると挙動が変わる。今の主な受け渡し(`field_rows`・d/e/p/f の候補・`applied_now`・`focus_request`)は、どの分岐でも代入するのを読んで確かめた。全部の局所については確かめていない。試験では `reset()` の値を「読んだら落ちる番兵」にする。
- **T5** 試作は 6 構成・mock と古典だけ。段 A を 19 構成と、艦隊・再生・`response_delay=2`・再開の既存の試験(`test_fleet_wiring`・`test_tape_deferred`・`test_response_delay`・`resume_19x2`)の上で回す段が、§3-1 の段 1 に無い(段 2 に byte-check 19 構成はあるが、書きの検査を入れるとは書いていない)。

## 4. 切り方の検査のまとめ

- **実行順の区間で切ること**: 結果不変のためには妥当で、いちばん安全な選び方(28 列・27 行に書き手が 2 つ以上あり、順を 1 つも入れ替えられない)。十分条件ではない。区間を保ったうえで、次も保つ必要がある。(1) クロージャの遅い束縛(`pending`)と nonlocal(b_*)の意味。(2) 物の同一性(使い回すバッファ `focus_request`・差し込んだ関数が組み立ての時点で捕まえた `agents`・`rel_layer`・`mem_layer`・`conv`)。(3) ハッシュに入る名(F8)。(4) 状態に入る値のクラスの置き場。(5) 条件つきの代入の古い束縛(T4)。草案は (1)・(3)・(4) を §3-3 で押さえている。(2) は一部(6 番)、(5) は無い。
- **llm_receive を 2 つの位置に置く**: `response_delay` で位置を選ぶのは今のコード(3694・3916)と同じ。妥当。
- **土台の乗せ方(§2-8)**: 大筋は無理が無い。注意が 3 つ。
  - (a) 1-3 の出来事の記録の「追記」は、段 B の「変わった行 ⊆ 書く行」では検査できない(どの系も変える)。「前の分が変わらず、長さだけ増える」の検査を別に要る。
  - (b) 土台が足す状態(出来事のログ・規則の表・権利台帳・道具の台帳)は状態台帳の行になる。軸 1 を behavior にすると final が動くので、行の軸を先に決める。草案に書かれていない。
  - (c) 1-9 の「お金は口『移す』だけ」の静的な強制は、ledger の別名の書き(F4)を AST で見られない。実行時は ledger の自前の検査が頼り。
- **危ない所 16 件の抜け**: K1(ufunc.at)・K2(旗の直書き)・K3(ビュー)・K7(系の外)・R1(使い回すバッファ)・T4(古い束縛)・K8(漏れた局所)。ほかに推測が 1 件。進行役が系ごとに時間を測ると、`phase` の鍵の並び(今は `phase["llm"]` を L5・L11・L14 で足し込む)が変わる。manifest や診断の表の形に効くかは確かめていない。

## 5. 比較表の一次確認(§4)

WebFetch で出典の頁を開いた(読むだけ)。○=頁で確かめた・△=一部だけ・×=読めない。

| 先例 | 主張 | 判定 | 頁で読んだこと |
|---|---|---|---|
| UE5 | `ConfigureQueries` は依存の解き手が処理を見る前に呼ばれる | ○ | "called before the processor gets considered by Mass dependency solver" |
| UE5 | `AddRequirement<T>(EMassFragmentAccess, EMassFragmentPresence)` | ○ | テンプレートの版と UScriptStruct の版の 2 つ |
| UE5 | `ExecuteInGroup`・`ExecuteBefore`・`ExecuteAfter` | ○ | FMassProcessorExecutionOrder の 3 つの欄 |
| UE5 | `EMassProcessingPhase` の値・`BuildFlatProcessingGraph` | ×(草案も未確認と明記) | 概要の頁に phase・順・依存の図・多スレッドの記述は無い |
| UE5 | EULA | ×(草案どおり 403) | `unrealengine.com/eula/unreal` は 403 |
| Unity | 群 3 つ・`UpdateInGroup/Before/After`・`OrderFirst/Last` | ○ | systems-update-order(1.3) |
| Unity | 読み書きする component から依存を解析・システム単位なので要らない待ちが出る | ○ | scheduling-jobs-dependencies(1.4)の注 "can result in jobs waiting ... known issue" |
| Unity | `RefRO` | ○ | "stores a safe read-only reference" |
| Unity | Unity Companion License(Unity に依る作品だけ) | △ | 頁は "Unity Companion License for Unity-dependent projects" とだけ書く。条文は別の頁 |
| Bevy | `ambiguity_detection`・既定は無視 | ○ | "Defaults to LogLevel::Ignore"(bevy_ecs 0.20.0) |
| Bevy | `System::initialize` が `SystemAccess` を返す | ○ | `fn initialize(&mut self, _world: &mut World) -> SystemAccess` |
| Bevy | 同じ系の中の食い違う引数は初期化で panic | ○(出典は Query の頁) | "A system cannot contain two queries that break Rust's mutability rules, or else it will panic when initialized." System の頁には無い |
| Bevy | MIT または Apache-2.0 | ○(注あり) | README。外から来た一部のコードは BSD 風の別の条件(crate ごとに確かめる) |
| flecs | 組み込みの phase を DependsOn で位相ソート・phase の中は entity id 順(決定論) | ○(OnStart が抜け) | "orders systems by their entity id, to ensure deterministic order"(保証はしない注あり) |
| flecs | `[in]`/`[out]`・書きの宣言が同期点を決める・既定はフレームの終わりに混ぜる | ○ | "systems must be annotated with the components they write" |
| flecs | MIT | ○ | LICENSE(Meta の部分の著作権表示あり) |
| EnTT | const=読み取り専用・テンプレート引数で上書き・図を作るだけで実行しない | ○ | "The resulting tasks are not executed in any case."・`top_level`・`children` |
| EnTT | MIT | ○ | LICENSE |
| Mesa | Mesa 3 で scheduler を廃止し AgentSet の `do`/`shuffle_do` へ | ○ | "The whole Time module in Mesa is deprecated and will be removed in Mesa 3.1." |
| Mesa | Apache-2.0 | ○ | LICENSE |
| MATSim | 登録順のリストを毎 step 回す・前後の listener・`events.afterSimStep` | △ | QSim.java の 391〜397 行と 376・411・412 行で確かめた。listener の呼び名は `fireQueueSimulationBeforeSimStepEvent` 等 |
| MATSim | `MobsimEngine`(`doSimStep(now)`) | △ | MobsimEngine.java に doSimStep は無く、`Steppable` から受け継ぐ |
| MATSim | GPL-2.0 以降(読むだけ) | ○ | ヘッダ "version 2 of the License, or ... any later version" |
| Agents.jl | `agent_step!`・`model_step!`・既定の scheduler(最速)・`Randomly`・`ByProperty` | ○ | tutorial |
| Agents.jl | MIT | ○ | LICENSE.md |

まとめ: 比較表の主張に、結論を変える誤りは無い。未確認は草案自身が書いた 3 点(UE5 の phase の値・`BuildFlatProcessingGraph`・EULA)だけ。

## 6. §0-1 の 5 件はユーザーの判断か

回答 10-12b §6-6 の線引きは「戻せない判断と範囲を超える判断(新しい expedient の値を既定にする・検証専用のデータ・許可の外のドメイン・費用)だけ止めて聞く。戻せる判断は親案で進め、後でまとめて確認」。CLAUDE.md §2-6 は「指示された手段を変えるなら、実行前に代替案・根拠・トレードオフを示す」。

| # | 草案の問い | 判定 | 理由 |
|---|---|---|---|
| 1 | 系の切り方の軸(実行順で 25・話題は名札) | **ユーザー** | ユーザーは系の例として「移動・知覚・判断・会話・お金・鉄道」と話題で書いた。草案はこれと違う切り方を選ぶ=指示された手段の変更(§2-6)。切ってから戻すと口を作り直すので、戻しにくい |
| 2 | 書きの検査を本番でも常に入れるか | 親 | 結果を変えない・切替口で戻せる・費用は計算量だけ(計算量は案を外す理由にしない=CLAUDE.md §4)。親案で進めて後で報告 |
| 3 | Phase C を 1 つの系のまま置く | ユーザー(1 に入れる) | 単独では親の判断だが、「移動」と「お金」が独立の系にならない理由そのものなので、1 の説明に入れる |
| 4 | 外の状態の検査の粒度 | 親 | 技術の選択で戻せる。しかも道筋の単位にすればハッシュを変えずに細かくできる(K9)ので、二択の前提が崩れる |
| 5 | 世界過程の持ち主をまたぐ書き | 親(1-0 の中)・後でユーザー | 1-0 は結果不変なので、今の書きを宣言に載せて認めるしかない(親の判断)。「過程が他の層の状態を書いてよいか」は設計の決まり(世界の変化は人の行動の結果)に触るので、直す段でユーザーに聞く |

ユーザーへの問いの言い換え案(1 件):

> 系の切り方について 1 点だけ確かめさせてください。ご指示では系の例として「移動・知覚・判断・会話・お金・鉄道」を挙げていただきました。1-0 では、これを系そのものにせず、今の処理の順のまま 25 の系に切り、話題は系に付ける名札にしたいと考えています。理由は、同じ欄(たとえば「何をしているか」の欄)を 7 か所が順に書いていて、話題ごとにまとめ直すと順が変わり、結果が変わってしまうためです。このため「移動」と「お金」は、行為の解決(Phase C)という 1 つの系の中に残ります。話題ごとのまとめ直しは、事象の待ち行列(T1)の後の版上げで、結果が変わることを前提に行います。この進め方でよいでしょうか。

あわせてユーザーに伝える(問いではない): 「宣言の外を書いたら落ちる」の強さは、SoA(個体・セル・店の列)は実行のたびに書いた行で止まり、外の状態(層の中の表)は試験のときに系の前後を比べて落とす、の 2 段になる。後者は試験の人数と時刻の範囲でしか見えない。

## 7. 親に確かめてほしい点

1. K1 の直し方(`_require_thawed` を配列の旗で見る)は resolve の振る舞いを変えない想定だが、1-0 の前に入れるか、1-0 の段 A の中で入れるか。
2. 宣言の正を静的な閉包にする(K4)と、閉包の表を誰が書くか(手で書くか、道具で下書きして手で直すか)。
3. 系ごとの指紋に `RunStats` を入れると、呼数の差も系の単位で出る(K5 (c) (ii))。重さとの兼ね合い。
4. 草案の記録の誤り 1〜10 の訂正は、起草した調査役に戻すか、親が〔改訂〕の注で直すか。

## 8. 再現(リポの根で)

```
D=docs/bench/analysis/wallbounce-1012/run-day-decomp
PYTHONPATH=src .venv/Scripts/python.exe $D/noprobe.py v3_default 1000 1      # a2edde01b409d6a1・12614
PYTHONPATH=src .venv/Scripts/python.exe $D/noprobe.py v3_default 1000 2      # 08013362b035909d・25814
PYTHONPATH=src .venv/Scripts/python.exe $D/guard_poc.py v3_default 1000 1                                  # ok・同じ
PYTHONPATH=src .venv/Scripts/python.exe $D/guard_poc.py v3_default 1000 1 L14:agents.refractory_until      # ok(落ちない=K1)
PYTHONPATH=src .venv/Scripts/python.exe $D/guard_poc.py v3_default 1000 1 L17:pois.revenue                 # ok(落ちない=K1)
PYTHONPATH=src .venv/Scripts/python.exe $D/soa_writers_ast.py src/shibuya <scratch の出力>                 # 記録の json と同一
```

ほかの 5 構成の noprobe と guard_poc、草案の負の対照 4 本も同じ形で回した(§2 の表)。
