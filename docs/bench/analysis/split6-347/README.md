# 割る段 6(`engine/resolve.py` を 18 の割り先へ)の記録(第347)

段 6 は 3 つの commit に分ける: **S6-A**(src を手で変える小さな下ごしらえ・挙動は 1 バイト不変)→ S6-G0(src 不変・道具と表と試験)→ S6-G1(道具で写す)。計画・取り直し・親の裁定は親の scratch に在る(計画 §3-2・§5-2・§5-3・§6-2・取り直し §3・§12・裁定 Q1・Q3・Q9・決め事 2・7)。

## 1. S6-A(土台 `bde381e`・安定版のタグ `stable-v2-before-split6-A` = `a6469a2`・2026-11-19)

返事その 8 §1-6 の 2「`apply_detection` は段 6 で 2 つの関数に割る」を、`engine/resolve.py` の中で先に当てた(名は裁定 Q3)。道具(`tools/pkgmove/`)・全ファイルの表・`contracts.toml`・`pyproject.toml`・`tools/bytecheck/` は変えていない。

### 1-1. 変えたファイルと行

| ファイル | 足した・消した行 | 中身 |
|---|---:|---|
| `src/shibuya/engine/resolve.py` | +10・−4 | `__all__` の `"apply_detection"`(147)を `"write_b4_hash"`・`"write_intero_stages"`(147-148)に。関数(815-824)を同じ場所で 2 つの頂上の関数に(816-829) |
| `src/shibuya/runtime/systems/perceive.py` | +2・−1 | 77 の `R.apply_detection(agents, world, det)` を `R.write_b4_hash(world, det)`・`R.write_intero_stages(agents, det)` の 2 行に(この順・`_count_intero_crossings` の後・`step_scope.after_detection` の前=同じ位置) |
| `src/shibuya/runtime/systems/table.py` | +1・−1 | 226 の系 `detect` の `resolve_ops` を `"write_b4_hash write_intero_stages"`(空白で区切った名の並び=その欄の今の型) |
| `src/shibuya/runtime/systems/allow.py` | +2・−2 | `ALIAS_WRITES` の鍵 `apply_detection` → `write_intero_stages`(52・続きの行の字下げをそろえた)。`RESOLVE_FILES` は 1 本のまま |
| `src/shibuya/validation/static/system_static_check.py` | +12・−10 | `from shibuya.engine import resolve as _RESOLVE` と `RESOLVE_MODULE`・`_RESOLVE_PARENT`・`_RESOLVE_LEAF` をやめ、`allow.RESOLVE_FILES` から作る名の集合 `RESOLVE_MODULES`(`frozenset`・45-46)に。`_resolve_names` の比べ 5 か所(82・84・89・91・95)を「集合に入るか」に。根の包みの名は系の包みのモジュールの名から取る(act の側は import しない) |
| `src/shibuya/foundation/decl/ledger_paths.py` | +15・−3 | 前向きだけの表 `LEDGER_PATHS_SPLIT`(空・239)と、`ledger_path()` がそれも引く形(`LEDGER_PATHS` → `LEDGER_PATHS_SPLIT` → そのまま)。`__all__` に名。モジュールの docstring に 2 行。`current_path()` は 1 字も変えていない |
| docstring の言及 3 か所 | 各 1〜2 行 | `runtime/clocks/step_scope.py:166-167`・`mind/system1/change_detect.py:20`・`runtime/run.py:250` の `apply_detection` を新しい 2 つの名に |

### 1-2. 2 つの関数の字面

```python
def write_b4_hash(world: World, result: DetectResult) -> None:
    """``change_detect`` が返した新しい B4 ハッシュを書き込む(世界の欄 ``cells.b4_hash``)。"""
    with world.writable():
        if result.changed_cells.size:
            world.cells.b4_hash[result.changed_cells] = result.changed_b4_hash


def write_intero_stages(agents: AgentState, result: DetectResult) -> None:
    """``change_detect`` が返した内受容段を書き込む(心の欄 ``fatigue_stage``・``hunger_stage``・``thermal_stage``)。"""
    with agents.writable():
        for crossing in result.crossings:
            if crossing.agent_id.size:
                agents.registry.field(crossing.stage_field)[crossing.agent_id] = (
                    crossing.new_stage.astype(np.int8)
                )
```

- `with` の中の文は、前の `with agents.writable(), world.writable():` の中の 2 つの文と AST が同じ(字下げのほかは変えていない=試験 ② で確かめる)。上の節の注(`# ---- 変化検出の書き戻し`)はそのまま。
- `writable()` を読んで確かめたこと: `World.writable`(`world/model/state.py`)と `AgentState.writable`(`world/model/agent_table.py`)は、凍結していれば `thaw()`(列ごとに書き込みの旗を系の許可 `write_permit.allows` で立てる)→ 中身 → `freeze()`(旗を全部下ろす)だけ。凍結していなければ何もしない。数・記録・乱数・計数に触らない。`write_permit.allows` は今の許可の集合を読むだけ(純)。2 つの文は別々の配列(`world.cells.b4_hash` と `agents.registry.<x>_stage`)を、同じ読むだけの `result` から書き、間で互いを読まない=分けても同じ結果。終わりの凍結の旗は前も後も「両方凍結」。

### 1-3. 呼び手の一覧(前と後)

| 所 | 前 | 後 |
|---|---|---|
| 呼び手(src) | `runtime/systems/perceive.py:77` の 1 行 | 同じ所の 2 行(77-78) |
| 系の宣言 | `table.py:226` `resolve_ops="apply_detection"` | `resolve_ops="write_b4_hash write_intero_stages"` |
| 手の別名の表 | `allow.py` の `ALIAS_WRITES["apply_detection"]` | `ALIAS_WRITES["write_intero_stages"]`(別名の書きを持つのは心の側の関数) |
| 試験の呼び出し | `test_tm3_step_scope.py:111・118・145・249・266`・`test_resolve.py:355` | どれも 2 行(b4 → 段) |
| 試験が名で引く | `test_stage_a_guard.py:315`・`test_guard_runs.py:58`・`test_body_guard.py:172`・`test_cp2_transfer_only_writer.py:105`・`test_move_prep_stage2.py:106` | `write_intero_stages` に(下の §1-5) |
| 心の読みの表 | `mind_world_reads_frozen.json` の `scope.split` の `act/ops/detect_writes.py` の記号 `apply_detection` | `write_b4_hash` は `act/ops/detect_writes.py`・`write_intero_stages` は `mind/ops.py` の行へ(裁定 Q3 の割り先) |
| docstring の言及 | 3 か所 | 新しい 2 つの名に(§1-6) |

- `apply_detection` の字が残る所(src・tests〔c7 を除く〕・tools・docs の記録の道具を洗った): `tools/pkgmove/map.toml:2337`(名の表の行=S6-G0 で親の裁定どおりに直す)・`tools/pkgmove/README.md`(道具の文)・`tests/tools/test_pkgmove.py:183`(注の文=直さなくてよい)・`docs/bench/analysis/wallbounce-1012/run-day-decomp/build_allow.py`(古い記録の台本・記録の道具の一覧の外)・足した試験の中の前の形の写し。`tests/c7` は字の Grep の数だけを見た=0。

### 1-4. 足した試験(決め事 2 の ①②・段 6 の後も残す)

`tests/engine/test_detection_writes_split.py`(32 本):

- ① 割る前の形の関数を試験の中に写した(`_apply_detection_bde381e`・注に土台 `bde381e`)。同じ作りの世界と体(`test_tm3_step_scope` と同じ作り=値と合わない段を混ぜる)の 2 つの写しに、前の形と新しい 2 つ(b4 → 段)を別々に当て、`world.state_hash()`・`agents.state_hash()`・凍結の旗(`frozen` と配列ごとの書き込みの旗)を比べる。場合= 跨ぎが多い(最初の検出=跨ぎ 500 を超える・変わったセルあり)・跨ぎ 0 件・変わったセル 0 件・両方 0 件 × 種 3 × 系 `detect` の書きの許可の中かどうか(24 本)・凍結していない写し(1 本)・検出と書き戻しを 30 回繰り返す(値を乱数で少し動かす・終わりの 5 回は動かさない=跨ぎ 0 件の回を含む)を、印の体だけの版 `step_scope` ありとなしで(2 本)。
- 負の対照: 2 つのうち片方だけを当てると前の形と違う(`write_b4_hash` だけ=体のハッシュが違う・`write_intero_stages` だけ=世界のハッシュが違う・2 本)。
- ② AST の比べ: 新しい 2 つの関数の `with` の中の文の `ast.dump` の並び=前の形の `with` の中の 2 つの文。`with` の項は前の 2 つを 1 つずつ。引数の名と並び。関数の今の字面は `inspect.getsource` で読む(割る段で置き場が変わっても同じことを確かめる)。
- 場合が空回りしないことの確かめ 1 本・系 `detect` の書きの集合が 4 列のまま 1 本。
- ③ `writes_soa_frozen.json` は変えていない。既存の `test_d2_writes_soa_matches_the_frozen_table` が通る(系 `detect` の書きは `cells.b4_hash`・`agents.fatigue_stage`・`agents.hunger_stage`・`agents.thermal_stage` の 4 列のまま)。

### 1-5. 直した試験(名と呼び出し・確かめは弱めていない)

| 試験 | 直し | 数の前後 |
|---|---|---|
| `tests/engine/clock/test_tm3_step_scope.py` | 呼び出し 5 か所を 2 行ずつ | 試験の数は同じ |
| `tests/engine/test_resolve.py` | 呼び出しを 2 行に・試験の名を `test_write_b4_hash_and_write_intero_stages_write_hashes_and_stages` に | 同じ(1 本) |
| `tests/engine/systems/test_stage_a_guard.py:315` | `ALIAS_WRITES` の鍵 | 同じ(3 列) |
| `tests/engine/systems/test_guard_runs.py:58` | 落ちる関数の名(部分一致)を `write_intero_stages` に | 同じ(10 組) |
| `tests/engine/body/test_body_guard.py` の `HEAD_WRITERS` | 鍵を `write_intero_stages` に(鍵の昇順に合わせて表の終わりへ移した) | 11 鍵 → 11 鍵(`write_b4_hash` は体の列を書かないので載らない) |
| `tests/economy/cp2/test_cp2_transfer_only_writer.py:105` | `ALIAS_WRITES` の鍵の集合 | 1 → 1 |
| `tests/engine/state/test_move_prep_stage2.py:106` | ファイルをまたぐ名の重なりの試験の偽の名を `write_intero_stages`(resolve に在る名) | 同じ |
| `tests/engine/state/test_move_prep_stage2.py` の `test_static_check_names_come_from_the_modules` | `RESOLVE_MODULE` の 1 つの名の比べを、`RESOLVE_MODULES` が `allow.RESOLVE_FILES` から作る集合で、割る前は `{resolve の名}` の 1 つ=前と同じ範囲、に。前は名の親と葉の字面(`_RESOLVE_PARENT`・`_RESOLVE_LEAF`)を比べていたので、代わりに `_resolve_names` を動かして、resolve を読む 3 つの形(親の包みから葉・別名の import・口の素の import)と頂上の別名と口を拾い、ほかのモジュールを拾わないことを確かめる形にした(確かめは強まる側) | 同じ(1 本) |
| `tests/engine/state/mind_world_reads_frozen.json` | `scope.split` の記号(§1-3) | 合計 83 か所・72 鍵のまま。記号の数は `detect_writes` の行 1 → 1・`mind/ops.py` の行 9 → 10(1 つの名が 2 つになった分) |
| `tests/engine/bridging/test_bridging_ledger.py` | 前向きの表の試験 3 本を足した(§1-7) | +3 |

### 1-6. docstring の言及 3 か所(裁定 Q3)

- つなぎの台帳の宣言(見出しのハッシュ)に入るかを先に確かめた: 変えた src の 9 本のファイルごとに、宣言の走査(`validation/static/bridging_scan.scan_source`)の結果(同定の文字列・形・項の数)が土台と作業の木で同じ(`engine/resolve.py` 4・`mind/system1/change_detect.py` 1・`runtime/run.py` 1・ほか 0)。3 か所とも宣言の段落・見出しの外=直した。
- `runtime/clocks/step_scope.py:166-167`: 「``resolve.write_b4_hash``・``resolve.write_intero_stages`` の後: …」(2 行の折り返しを直した)。`mind/system1/change_detect.py:20`: 「``resolve.write_b4_hash``・``resolve.write_intero_stages`` が書き込む。」。`runtime/run.py:250`: 「``write_b4_hash``・``write_intero_stages`` の**前**に呼ぶ」。

### 1-7. `RESOLVE_MODULES` と前向きの表

- `RESOLVE_MODULES` は、割る前は `{"shibuya.engine.resolve"}` の 1 つ=前の `RESOLVE_MODULE` と同じ範囲(試験で確かめる)。`system_static_check` は resolve を import しなくなった。この辺(`validation.static.system_static_check → engine.resolve`)は import の決まりの例外に載っていない(先に `pyproject.toml` と `contracts.toml` で確かめた)=例外の効きは変わらない。
- 前向きだけの表 `LEDGER_PATHS_SPLIT`(裁定 Q1 の (ii)・決め事 7・親の追記で名と形を確定): 型と字面は `LEDGER_PATHS` と同じ形(空の間は `MappingProxyType({` の後で改行し、次の行が `})`)。表の意味=割る段で 2 つ目以降の割り先になったファイルの今の道 → 台帳の道(値は `LEDGER_PATHS` の値と重なってよい=N 対 1・手で書かない)。`ledger_path(path)` は `LEDGER_PATHS` → `LEDGER_PATHS_SPLIT` → そのまま。`current_path()` は前向きの表を引かない(1 字も変えていない)。台帳の JSON は変えていない。モジュールの docstring は宣言に入らない(§1-6 の走査で 0)ので 2 行足した。
- 足した試験(`test_bridging_ledger.py`): 前向きの表が空の間、`ledger_path()` は全部の道(表の今の道と台帳の道・src の `.py` の全部・台帳のコードの行の道)で前(`LEDGER_PATHS.get(道, 道)`)と同じ/前向きの表に行を一時に 1 つ足すと、その道が台帳の道へ引け(値は主な表の値と重なる=N 対 1)、`current_path()` は全部の道で変わらない/同じ今の道が 2 つの表の両方に在ってはならない(負の対照: 一時に足すと見つかる)。往復の試験と 1 対 1 の試験は今のまま通る。
- 裁定 Q1 の条件 ③ の「前向きの表に載った道に宣言が 1 つも無ければ落ちる試験」は、表に行を書く道具の拡張と一緒に S6-G0 で足す見込み(今回は足していない)。

### 1-8. 確かめ

| 何を | 結果 |
|---|---|
| 狙いの試験の束(足した試験・`test_resolve`・`tests/engine/systems`・`state`・`bridging`・`clock`・`body`・`tests/economy/cp2`・`tests/tools`・`-m "not gpu and not slow"`・`-n 2`) | 1,315 本=1,294 passed・21 skipped・0 failed(飛ぶ 21 本は `tests/tools/test_pkgmove.py` の前からの分=段 4 と割る段の済んだ木) |
| 足した試験 `tests/engine/test_detection_writes_split.py` | 32 passed |
| 台帳の試験 `tests/engine/bridging/test_bridging_ledger.py` | 43 passed(足した 3 本を含む) |
| `test_d2_writes_soa_matches_the_frozen_table`(`writes_soa_frozen.json` は変えていない) | passed(上の束の中) |
| `lint-imports`(作業の木の src) | 11 kept・0 broken |
| `map --check`・`split --next` | 同じ・「割る段は全部当たっている」 |
| `contracts --stage delete --tree . --check --probe` | 同じ(契約 2+9・例外 20 辺・延べ 26 行=全部効く・効かない 0・壊れた 0) |
| byte-check 19 構成(基準 `bde381e`・記録 [bytecheck_A/](bytecheck_A/)) | 37 欄すべて同じ 19・動いた 0・誤り 0・441 秒。既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939(基準と同じ) |
| つなぎの台帳の宣言の走査(変えた src の 9 本) | 土台と同じ(§1-6) |
| カード | 作り直した(`data.md` だけ単独で戻した・`--check` 最新) |
| 秘密の走査(変えたファイルを引数で) | CLEAN |

### 1-9. 計画・取り直しの数と違った所・親に聞くこと・確かめていないこと

- 計画・取り直しとの違い: `_resolve_names` の比べは発注の「4 か所(80・82・87-89・93)」のとおりの所で、数えると 5 つ(87-89 に 2 つ)。`HEAD_WRITERS` の鍵は名を替え、鍵の昇順に合わせて表の終わりへ移した(数は 11 のまま)。`test_static_check_names_come_from_the_modules` は、消した名(`_RESOLVE_PARENT`・`_RESOLVE_LEAF`)の字面の比べを、`_resolve_names` を動かす確かめに替えた(§1-5)。
- **親に見てほしい所**: `mind_world_reads_frozen.json` の `scope.split` で、`write_intero_stages` を `mind/ops.py` の行に置いた(裁定 Q3 の割り先。発注は「記号の名」)。表の数(83 か所・72 鍵)は変わらない。全ファイルの表 §4 と `map.toml` は今も `apply_detection`(`map.toml` の割り先は `mind/ops.py`)のまま=S6-G0 で表を直すときに、この置き方と合わせる。違う置き方なら直す。
- 確かめていないこと: 範囲の全体の試験(親が回す)・slow の試験・CI。裁定 Q1 の条件 ③(前向きの表に載った道に宣言が 1 つも無ければ落ちる試験)は S6-G0 に送る。

## 2. S6-A の親の確かめと検収(第347・2026-11-19)

### 2-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 4)。検収役はファイルを 1 本も変えていない。
- 2 つの関数: 前の形の写し(試験の中)は土台 `bde381e` の関数と字面が同じ。`with` の中の文の AST も同じ。`World.writable`・`AgentState.writable` は対象ごとに独立で、例外の時も同じ結果になる。検収役がメモリの中で関数を書き換えて試した: `with` を外す・旗を取り違える・跨ぎを 1 つだけ書く・凍結を戻し忘れる、はどれも足した試験で落ちる。呼ぶ順を逆にしても結果は同じ(2 つの書きは独立)。
- 呼び手: `runtime/systems/perceive.py` の 2 行は同じ位置・b4 → 段の順。ほかに呼ぶ所は無い(古い記録の台本は記録の道具の一覧の外で、試験も読まない)。
- 書きの許可: `allow.index` を前後で比べ、36 系の書きは全部同じ・系 `detect` は 4 列のまま・関数の数は 101 → 102。
- `system_static_check`: `RESOLVE_MODULES` は `{"shibuya.engine.resolve"}` の 1 つ=割る前の範囲は同じ。拾う形(モジュールの別名・素の名の関数・関数の中の import・`import … as`)は前と同じ。`contracts --check --probe` は前と同じで、消えた辺(`system_static_check → engine.resolve`)はどの例外にも載っていない。
- 試験: 名を替えた試験は弱まっていない(`HEAD_WRITERS` は 11 → 11)。足した試験は空回りしない(負の対照が効く・AST の比べは今の src を読む)。
- 心の読みの表 `mind_world_reads_frozen.json` の `scope.split`: 置き方(`write_b4_hash` → `act/ops/detect_writes.py` の行・`write_intero_stages` → `mind/ops.py` の行)は、表の意味(割り先が心の置き場の下なら、その関数の読みを数える)と裁定 Q3 に合う。走査の範囲は広がる側(厳しくなる側)に変わった(`write_intero_stages` の本体が新しく走査に入る)。合計 83 か所・72 鍵が変わらないのは、2 つの関数に世界を読む文が無いから。
- 前向きの表: 親の確定した形どおり。空の間 `ledger_path()` は全部の道で前と同じ。台帳の JSON は差 0・宣言の走査は変えた src の 9 本で同じ(`bridges_version` は動かない)。このモジュールはランの中で読まれない。割る道具は表を名の完全一致で探すので、2 つ目の表に影響されない。
- docstring の言及 3 か所と、`resolve.py`・`ledger_paths.py` の docstring は、どれもつなぎの台帳の宣言の外。
- 変えないはずの物(`tools/pkgmove/`・`tools/bytecheck/`・全ファイルの表・`contracts.toml`・`pyproject.toml`)は差 0。

### 2-2. 検収の低 4 件と、親の了承 1 件

- 低-1(`apply_detection` の字が `tools/pkgmove/map.toml`・全ファイルの表の 3 行・凍結の JSON の `md_source` に残る。もとの表どうしも食い違う=`map.toml` は関数ごと `mind/ops.py` へ、全ファイルの表と JSON は detect_writes へ): S6-G0 の表の直しで、裁定 Q3 の割り先に 2 つの名を書き分ける(1 つの名の置き換えでは足りない)。
- 低-2(足した試験 `test_detection_writes_split.py` が、1 つの別名から割り先の違う 2 つの名を読む読み手を 1 本増やした): S6-G1 の手で直す一覧に入る(取り直しの「tests 59 本・64 文」は 60 本・65 文の見込み)。
- 低-3(「跨ぎが多い」場合が空でないことを確かめるのは種 1 だけ。種 2・3 も実際には空でない): S6-G0 の試験の直しと一緒に、3 つの種の全部で確かめる形に直す。
- 低-4(記録の置き場 `bytecheck_A_parent/` が途中の状態だった): 親の byte-check が終わって 3 本そろった(下)。
- 親の了承: 裁定 Q1 の条件 ③(前向きの表に載った道に宣言が 1 つも無ければ落ちる試験)は、表が空の S6-A では空回りになるので、S6-G0 で足す(割る道具が行を書く S6-G1 の前に在ればよい)。時期を変えたことを了承した。
- 実装役が確かめを求めた 1 点(`scope.split` の置き方): 上のとおり受け入れる。

### 2-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| byte-check 19 構成(本体の道具・基準 `bde381e`・S6-A の木) | 37 欄すべて同じ 19・動いた 0・誤り 0・438 秒・既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。記録 [bytecheck_A_parent/](bytecheck_A_parent/)(実装役の記録は [bytecheck_A/](bytecheck_A/)=441 秒) |
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`) | 6,996 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・22 skipped・1 xfailed・40 分 03 秒。前の回(5b の G3 の直しの前)の 6,960 passed・23 skipped から、S6-A で足した試験 35 本(32+3)で +35・G3 の直しで飛ぶ試験 1 本が passed に戻って +1(飛ぶ試験は 23 → 22) |
| src の差分を読んだ | 2 つの関数は元の文を字面のまま(字下げのほか)・`perceive.py` は同じ位置で 2 行・`table.py` の `resolve_ops` は空白区切りで 2 つの名・`ALIAS_WRITES` の鍵は `write_intero_stages`・`_resolve_names` の比べ 5 か所は集合の形 |

## 3. S6-G0 の割る前の試験の直し(土台 `8997e2d`=S6-A の台帳の commit・2026-11-19)

S6-G0 は 2 つに分けた: 道具の拡張(別の実装役・別の木)と、この節の「割る前の試験の直し」。`engine/resolve.py` を割ると黙って空回りする・範囲が縮む・落ちる試験を、割る前の今のうちに、割っても同じ事を確かめる形に直した。src・`tools/pkgmove/`・`tools/bytecheck/`・`tests/tools/test_pkgmove.py`・全ファイルの表・`map.toml`・`contracts.toml`・`pyproject.toml` は変えていない(`git status --porcelain -- src` は空=byte-check は要らない)。

### 3-1. 範囲の作り方(親の裁定 R1)

- **ループを探す範囲**(毎刻みの関数・ホットパス)は `_PL.split_files("engine/resolve.py", 名)`=名を定義する今のファイル(割る前は元のファイル・割った後は名の割り先)。第 1 引数は字面で書く(割る道具は表の鍵を書き換えない)。
- **書き手の範囲**(`writable()` の呼び手・`ufunc.at`・D ⑥ の除外・D ⑦・帳簿の口の呼び手)は `allow.RESOLVE_FILES`(割る前は `engine/resolve.py` の 1 本・割った後は書き手の 15 本=裁定 Q4)。
- どちらも割る前は今と同じ範囲。「名が全部見つかる」「空でない」「陽性の対照」を足して、空回りを音にした。

### 3-2. 直した試験(割った後に起きるはずだった事・直し・範囲・数)

数は、直す前と後で同じノード(`-m "not gpu and not slow"`・`-n 2`・`-rA`)を回した数。直した 16 本と `tests/tools/test_repo_guide.py`: 前 368 passed → 後 377 passed(直したファイルごとに同じ数。増えた 9 は §3-5 の足した試験)。skipped・failed は前も後も 0。

| 試験 | 割った後に起きるはずだった事 | 直し | 数(前 → 後) |
|---|---|---|---|
| `test_energy_balance.py::test_per_tick_paths_have_no_python_loops`(`_PER_TICK`) | 字面の `"engine/resolve.py"` が主な割り先へ書き換わり、3 つの関数が無い=何も調べずに通る(**黙って空回り**) | resolve の 3 つの名(`advance_body`・`_energy_meal`・`energy_out_of_area_meal`)は `_PL.split_files("engine/resolve.py", 名)` で定義のファイルを引く(`_per_tick_paths`)。**名が全部見つかること**を足した | 28 → 28 |
| `test_two_phase.py::test_only_resolve_writes_to_the_world` | `writable()` の呼び手が書き手の割り先の数になり、1 本との比べが落ちる(音) | 呼び手 ⊆ `{RESOLVE_FILES のファイル}`・空でない | 14 → 14(ファイル全体) |
| `test_two_phase.py::_hot_paths` | 字面が主な割り先 `act/apply.py` だけになり、ほかの割り先が外れる(**黙って縮む**) | `_PL.split_files("engine/resolve.py", ("apply",))`=元の docstring(逐次ループ宣言)を持つ主な割り先(割る前は同じ 1 本)。**ループを探す範囲(`_loop_scan_paths`)を割り先の全部へ広げる直しは、まだ入れていない**(§3-9) | 同上 |
| `test_add_at_guard.py` の 3 本(`…lives_only_in_resolve`・`…actually_uses_ufunc_at_on_state`・`…preceded_by_the_frozen_check`) | 1 本との比べが落ちる/陽性の対照が 0 件で落ちる/**apply.py に `ufunc.at` が無く黙って通る** | 書き手の範囲 `_writer_files()`(`RESOLVE_FILES` の全部・在ること)。呼び手 ⊆ 書き手・空でない/陽性の対照は全部で 3 以上/直前の確かめは全部で見て、見た数が 3 以上 | 9 → 9 |
| `test_stage_a_guard.py::test_every_state_ufunc_at_in_resolve_checks_the_written_array`(D ⑦) | 0 件で `checked >= 5` が落ちる(音) | `RESOLVE_FILES` の全部の関数で見る(関数が空でない) | 17 → 17(ファイル全体) |
| `test_stage_a_guard.py`・`test_fix_guards.py` の `_EXEMPT_D6` | 書き手の割り先 14 本が D ⑥ の走査に入って落ちる(音) | 字面の `"engine/resolve.py"` を外し `\| set(AL.RESOLVE_FILES)` | 同上・16 → 16 |
| `test_stage2_writers.py::_callers_in_resolve` | 1 本のファイルだけを見て、帳簿の口の呼び手が割り先に移ると落ちる(音) | `RESOLVE_FILES` の全部の関数で見る(空でない) | 4 → 4 |
| `test_body_guard.py::test_only_the_ports_write_the_body_layer` | `"engine/resolve.py:advance_body:step"` ほかの字面が割り先の道と合わず落ちる(音) | 道が書き手のどれか(`RESOLVE_WRITERS`)なら `resolve` に正規化して比べる(`_as_resolve`) | 8 → 8 |
| `test_body_guard.py::test_callers_of_the_body_write_ports_are_not_more_than_head` | 受け手の名 `R`・`resolve` の字面(割り先の別名に替わると見落とす) | 受け手は、そのファイルの import(頂上と関数の中)が書き手のモジュールに結ぶ名(`_resolve_aliases`・AST)。割る前は同じ `R`。〔検収の後の直し〕見る形が変わった(広げただけではない)ので、前の字面の名 `R`・`resolve` も足した(§3-10 の直し 2) | 同上 |
| `test_move_prep_stage2.py` の 2-3 の 4 本 | `RESOLVE_FILES == ("engine/resolve.py",)` の字面・`RV.__file__`・偽の木の `engine/resolve.py`・`PL.names_from(RV)` が落ちる(音) | 一覧の全部のファイルが在り・重ならず、索引の関数=一覧の全部のファイルの頂上の関数(`apply` を含む)/偽の木は一覧の全部を同じ道で写す(`_fake_writers`・試験が一覧を差し替える前の値 `_REAL_WRITERS` で)・偽の名は一覧の関数から引く/static_check の試験は、resolve のモジュールの名を `apply` を定義するモジュールとして集合から引き、範囲の手がかりを `shibuya.act.intent` に(§3-3)。モジュールの頂上の `from shibuya.engine import resolve as RV` は使わなくなったので外した | 12 → 12 |

### 3-3. 範囲の手がかりの付け替え(裁定 Q10)

`from shibuya.engine import resolve as ENGINE` を `from shibuya.act import intent as ENGINE`(元の置き場が `engine/intent.py` の、割らずに移したモジュール)へ。付け替えの前と後で、手がかりから作る範囲(ファイル・名の集合)が同じことを 1 本ずつ確かめた(どちらも元の置き場のディレクトリは `engine/`)。

| 試験 | 範囲の作り方 | 前と後 |
|---|---|---|
| `tests/c6/test_t3_parallel_invariance.py` | `PL.files_from(ENGINE)` | 同じ(185 本) |
| `tests/economy/test_single_write_path.py` | `PL.files_from(ENGINE)` | 同じ(185 本) |
| `tests/engine/memory/test_m0_store_schema.py` | `PL.names_from(ENGINE, PERCEPTION, LLM, AGENTS, WORLD, CORE)` | 同じ(頭 25・葉 218) |
| `tests/engine/test_state_ledger_10b.py` | `PL.rels_from(ENGINE)` | 同じ(185 本) |
| `tests/llm/test_fleet_contract.py` | `PL.names_from(ENGINE, PERCEPTION, WORLD, AGENTS, ECONOMY, BUILD)` | 同じ(頭 34・葉 284) |
| `tests/engine/state/test_move_prep_stage2.py`(static_check の試験) | `PL.names_from(ENGINE)`(前は `names_from(RV)`) | 同じ(頭 17・葉 168) |

### 3-4. 再輸出 4 名(裁定 Q7)

- `tests/engine/body/test_body_same_values.py::test_moved_names_point_to_the_same_values`: resolve の再輸出(`BODY_TICK_PERIOD`・`SLEEP_FATIGUE_RELIEF`・`ACTIVITY_REST_PERIOD_TICKS`・`ACTIVITY_REST_FATIGUE_RELIEF`)は割る段で消える(10-13b §0-6=再輸出の口は残さない)ので、resolve の側の確かめ 2 つ(4 つの値が体の層と同じ・resolve の `__all__` に 4 名が在る)を外した。体の層 `world.body.rules` の値 `(30, 2, 10, 1)` は残した。`environment`・`salient` の写しの確かめと、resolve に残る行為の効果(`REST_FATIGUE_RELIEF`・`BUY_HUNGER_RELIEF`)の確かめは変えていない。〔検収の後の直し〕確かめる物が減ったのは、この 1 か所(裁定 Q7)のほかに、`test_move_prep_stage2` で書き手の一覧の字面の固定 3 つ(`RESOLVE_FILES == ("engine/resolve.py",)`・`RV.__file__` との一致・`RESOLVE_MODULES == {RV.__name__}`)を形の確かめに替えた所も(=頂上の関数を持たないファイルが一覧にまぎれても落ちなくなっていた・検収の中-1)。後者は §3-10 の直し 1 で埋めた。試験の数は 24 → 24(同じ関数の中の確かめが 2 つ減った)。src の `__all__` は変えていない(消えるのは G1)。
- `tests/engine/test_resolve.py::test_advance_body_only_moves_on_its_period`: `R.BODY_TICK_PERIOD` を `world.body.rules` の `BR.BODY_TICK_PERIOD` から読む(確かめは同じ)。35 → 35。

### 3-5. 足した試験と負の対照

- `tests/engine/systems/test_resolve_index_frozen.py`(6 本)と `resolve_index_frozen.json`(S6-A の後の木で作った): `allow.index()` を正規化(関数の集合 101・関数ごとの直接の書き 73 行・辺 42 行=115 本・頂上の表 4・帳簿の口の (関数, 口) 5・別名の書きの (関数, 別名) 2。行の番号なし・ファイルの本数に依らない)して表と比べる。裁定 Q4 のため `_require_thawed` を関数の集合と辺から外す(外すのは `EXCLUDED` の 1 つだけと試験で固定。今は 17 本の関数がこの関数を呼ぶ辺を持ち、そのうち 12 本はこの辺だけ=外すと空になる「辺の無い関数」の行 12 行が正規化で落ちる)。外す関数が書かない・どの表にも載らないこと、外しても 36 系の書きの閉包(`writes_for_ops`)が同じことも確かめる。負の対照 3: 関数を 1 つ消す・書きを 1 つ足す・辺を 1 つ消すと表との違いに出る。今の正規化は `python -m tests.engine.systems.test_resolve_index_frozen` で出る。
- `tests/engine/bridging/test_bridging_ledger.py::test_forward_rows_point_to_files_with_declarations`(裁定 Q1 の条件 ③): 前向きの表 `LEDGER_PATHS_SPLIT` に載った道のファイルには、つなぎの台帳の宣言が 1 つ以上在る(台帳の道で走査)。今は表が空なので、試験の中で一時に行を足して両方を確かめる: 宣言の在るファイル(AST の形の宣言を持ち、主な表に無いファイル)=通る・宣言の無いファイル=落ちる(その道が挙がる)。
- S6-A の検収の低-3: `tests/engine/test_detection_writes_split.py::test_the_first_detection_has_changed_cells_and_many_crossings` を種 1・2・3 の全部で(1 本 → 3 本)。ほかは変えていない。(知らせ)この試験は 1 つの別名 `R` から割り先の違う 2 つの名を読むので、S6-G1 で手で直す一覧に入る。

### 3-6. カードの道具(決め事 3)

- `tools/repo_guide/guide_permits.py`: 書きの閉包を、`allow.py` の `RESOLVE_FILES` を AST で読んで、その全部のファイルから作る形に(`_resolve_files`・関数ごとに置いたファイル `Permits.func_files`)。`allow.py` に `RESOLVE_FILES` が無い木(見本の木)は前のとおり 1 本(`RESOLVE_FILE`)で読む。名が在るのに読めなければ問題に書く。`guide_render.py`: resolve の関数の行は、その関数を置いたファイルの節へ(割る前は全部 resolve.py=前と同じ)。
- 直す前と後でカードが同じこと: 古い道具(土台の `tools/repo_guide/*.py`)と新しい道具で、同じ木の書きの許可の節(`permit_lines_by_file`・関数ごとの直接の書き・問題)を出して比べ、1 バイトも同じ(20 ファイル・228 行・問題 0)。カードを作り直した差分は、試験の直しと足した試験の分だけ(試験の docstring・「読む試験」と import の一覧・ファイルの数。16 枚)で、書きの許可の節(直接の書き・口・閉包)の行は 1 行も変わらない。`tests/tools/test_repo_guide.py`(変えていない)は 39 passed。

### 3-7. 字面の `"engine/resolve.py"` を消した所と残した所

- 消した(範囲を作る所): `test_energy_balance` の `_PER_TICK`・`test_two_phase`(呼び手の比べ・`_hot_paths`)・`test_add_at_guard`(3 本)・`test_stage_a_guard`(D ⑦・`_EXEMPT_D6`)・`test_fix_guards`(`_EXEMPT_D6`)・`test_stage2_writers`・`test_body_guard`(2 本)・`test_move_prep_stage2`(2-3 の 4 本)。範囲の手がかり 5 本の import。
- 残した(わざと・ほかの段で直す): `_PL.split_files("engine/resolve.py", …)` の第 1 引数(表の鍵=割る道具は書き換えない)・`tests/economy/cp2/test_cp2_write_window.py:127・142`(偽の道=負の対照)・`test_stage_a_guard.py::FLAG_WRITERS` の `("engine/resolve.py", "_restore_array_into")`(割る道具が restore へ機械で書き換える=計画 §7-2)・`test_fix_guards.py:394-401` のコードの文字列の import(道具が機械で書き換える)・`tests/economy/cp2/money_writers_frozen.json:9-12` と `mind_world_reads_frozen.json:110`(G1 で手で直す)・`tests/test_places_guard.py::NON_MOVE_ROWS`(除外の一覧)・`tests/tools/test_pkgmove.py`・`tests/tools/test_repo_guide.py`(別の役の側・裁定 R2)・docstring と注の文(`test_body_guard.py:6`・`test_add_at_guard.py:11` の docstring の字面もここ=検収の低-3 の知らせ)。

### 3-8. 確かめ

| 何を | 結果 |
|---|---|
| 直した 16 本と `tests/tools/test_repo_guide.py`(直す前と後で同じノード・`-n 2`・`-rA`) | 前 368 passed → 後 377 passed・skipped 0・failed 0(直したファイルごとに同じ数・増えた 9 は足した試験) |
| 束(`tests/engine/systems`・`state`・`body`・`bridging`・`tests/economy`・`tests/c6`・`tests/llm`・`tests/tools`・直したファイルのほかの置き場の 7 本・`-m "not gpu and not slow"`・`-n 2`) | 2,168 本=2,147 passed・21 skipped(`tests/tools/test_pkgmove.py` の前からの分=段 4 と割る段の済んだ木)・0 failed。data が要って飛んだ試験 0 |
| `git status --porcelain -- src` | 空(src を変えていない=byte-check は要らない) |
| `lint-imports`(作業の木の src) | 11 kept・0 broken |
| `map --check`・`contracts --stage delete --tree . --check --probe` | 同じ・同じ(例外 20 辺・延べ 26 行=全部効く・出力は S6-A の後と同じ) |
| カード | 作り直した(差分は §3-6 のとおり足した試験の分だけ・`data.md` は単独で戻した・`--check` 最新) |
| 秘密の走査(変えたファイルを引数で) | CLEAN |
| 束の pytest を回す間 | 合図のファイルを取った(前の数・後の数と束。終わったら単独で消した)。もう 1 人の実装役が合図を持つ間は待った |

### 3-9. 計画と違った所・親に聞くこと・確かめていないこと

- **まだ入れていない直し(親に聞く)**: `test_two_phase.py::_loop_scan_paths` に resolve の割り先の全部(`_PL.split_files("engine/resolve.py")`=名の全部)を足す直し。今の対応表(`tools/pkgmove/map.toml`)の resolve の名の表は S6-A の前の `apply_detection` のままで、`split_files` は名の全部を引くと `PlacesMapError`(「名 apply_detection を定義するファイルが元にも割り先にも無い」)で止まる。名の表を直すのは道具の側(全ファイルの表 §4-14 と `map.toml`=この発注では変えない)。割る前の範囲は今のままで同じ(`_hot_paths` の主な割り先が `engine/resolve.py`)だが、割った後は主な割り先 `act/apply.py` だけを走査する=表が直るまでに足す必要がある。案: (a) 道具の側で表が直った後に `extra` へ `*_PL.split_files("engine/resolve.py")` を足す(1 行・割る前も後も割り先の全部)/(b) 名を手で並べる(名の表と二重になるので推さない)。
- 計画との違い: `test_move_prep_stage2.py` の偽の木の試験は、一覧を差し替えた後に偽の木を作るので、一覧の本物の値を先に取っておく形(`_REAL_WRITERS`)にした(初めの直しで偽の道を本物の src から写そうとして落ちたのを直した)。`test_body_guard.py` の受け手は、書き手のモジュールを指す別名を AST の import から引く形(計画のとおり)。
- 確かめていないこと: 範囲の全体の試験・slow の試験・CI(親が回す)。割った後の木での振る舞い(G1 で確かめる)。カードの道具が割った後の 15 本を読む形は、見本の木の試験(変えない)では確かめていない(本物の木の一覧が 1 本の今は、古い道具と同じ出力)。

### 3-10. 検収の後の直し(検収=条件つき受入の中 1・低 4 と、道具の検収の低 1・親の裁定)

検収は「割る前の範囲は直した全部の試験で直す前と同じ・空の集合で通る形は無い・付け替えの 6 本は同じ範囲」。直したのは次の 5 つと記録。src・`tools/pkgmove/`・`tests/tools/test_pkgmove.py` は変えていない。直したファイル 5 本(`test_move_prep_stage2`・`test_body_guard`・`test_resolve_index_frozen`・`test_bridging_ledger`・`test_repo_guide`)を直す前と後で回した: 前 109 passed → 後 110 passed(`test_move_prep_stage2` に負の対照 1 本を足した分・ほかは同じ数)・skipped と failed は 0。

- **直し 1(検収の中-1・書き手の一覧の中身)**: 前の版は一覧を字面で固定していた(3 つ)。今の形は「在る・重ならない・索引の関数=一覧の頂上の関数」だけで、頂上の関数を持たないファイルが一覧にまぎれても落ちなかった(まぎれると D ⑥ の除外・`writable()`・`ufunc.at` を書いてよい側が広がる)。`test_resolve_files_list_reads_the_resolve_module` に「一覧のどのファイルも、索引の関数を 1 つ以上頂上で定義する」を足した(本数に依らない=割った後もそのまま効く)。凍結した関数の集合(`resolve_index_frozen.json` の 101)と合わせて、一覧は「凍結した関数を定義するファイル」に固定される: 関数を持たないファイルはこの確かめで、索引に無い関数を持つファイルは索引の関数が増えて凍結の表で、足りないファイルは索引の関数が減って凍結の表で、同じ関数を 2 本が持てば索引が止めて、それぞれ落ちる。負の対照 `test_negative_a_stray_file_in_the_writer_list_is_seen`(メモリの中で一覧を差し替えて): `economy/tax_deposit.py`(クラスだけ)をまぎれさせる=この確かめが落ちる・`foundation/write_guard.py`(索引に無い関数 2 つ)をまぎれさせる=凍結の表との比べが落ちる。
  - 割る前の間だけ「一覧は 1 本(`engine/resolve.py`)」を確かめる形は**入れていない**。わけ: 上の 2 つ(どのファイルも索引の関数を定義する+凍結した関数の集合)で一覧は本数に依らず決まり、割る前の今は凍結の表の 101 の関数が全部 `engine/resolve.py` に在る=一覧は 1 本と同じことを言う。条件つきの確かめ(割る行が当たったら外れる)は、割る段の状態に結んだ字面を試験に増やすだけになる。
- **直し 2(検収の低-1・体の口の呼び手の数え方)**: `test_body_guard.py::test_callers_of_the_body_write_ports_are_not_more_than_head` の受け手を「書き手のモジュールに結ぶ import の名」と前の字面の名 `R`・`resolve` の和に(`_PREV_RECEIVERS`)。前の形が拾っていた「引数で受けたモジュール」と相対の import の呼び手を含む=前の版が拾う呼び手 ⊆ 今の版が拾う呼び手。4 つの口の名で絞るので拾いすぎない。今の木で数えた: 前の形 5・import の名だけの形 5・今の形 5(3 つとも同じ・`HEAD_CALLERS` と同じ)。
- **直し 3(検収の低-2・外す関数の「書かない」)**: `test_resolve_index_frozen.py::test_only_require_thawed_is_excluded_and_it_writes_nothing` に、外す関数を定義する今のファイルを対応表から引き(`_PL.split_files("engine/resolve.py", ("_require_thawed",))`・見つからなければ止まる)、そのファイルだけを一時の書き手の一覧にした索引で、関数が在り書きと辺が無いことを確かめる形を足した(索引に在るかどうかに依らない=割った後に `foundation/write_guard.py` へ行っても効く)。割る前は `engine/resolve.py` の索引=前と同じ確かめ。
- **直し 4(検収の低-4・カードの道具)**: `tools/repo_guide/guide_permits.py` は、頂上の表の名がファイルをまたいで重なれば問題の一覧に書く(関数の名の重なりと同じ扱い・`allow.index` と同じく関数と表の名を 1 つの持ち主の表で見る)。今の木(1 本)では、カードの書きの許可の節が土台の道具の出力と 1 バイトも同じ(問題 0)。見本の 2 本(書き捨ての台本)で、表の名が重なると 1 件・重ならないと 0 件を確かめた。`tests/tools/test_repo_guide.py` は変えていない(39 passed)。
- **直し 5(道具の検収の低-2・前向きの表が空に頼る試験)**: `test_bridging_ledger.py` の S6-A で足した試験は `LEDGER_PATHS_SPLIT == {}` に頼っていた(段 6 で表に 2 行入ると落ちる)。表の中身が何行でも成り立つ形 `_check_both_directions` にした: 前向きの表に載っていない道は `ledger_path()` が前と同じ値・載っている道は前向きの表の値・`current_path()` は前向きの表を引かない(主な表の逆向きと同じ)。比べる道に前向きの表の道も入れた。試験の名を `test_ledger_path_follows_the_main_table_then_the_forward_table` に替えた(1 本のまま)。表が空の今は、全部の道で前と同じ=前の確かめと同じ強さ。行を一時に 1 つ足す試験(`test_a_forward_row_…`)でも同じ確かめを通す(行が在っても成り立つ)。
- 入れなかった 1 行(`test_two_phase.py::_loop_scan_paths` に resolve の割り先の全部)は、親の裁定で次の「表と順」の commit で足す。そのとき名の表は、古い名 `apply_detection` を消すだけでなく `write_b4_hash`(→ `act/ops/detect_writes.py`)・`write_intero_stages`(→ `mind/ops.py`)を足す(足さないと `split_files` が `detect_writes.py` を返さず、1 行を足しても走査から外れる=検収役の注)。
- 確かめ: 直したファイル 5 本(上の数)・カードを作り直した(差分は試験の docstring・関数の一覧・数・`data.md` は単独で戻した・`--check` 最新)・`git status --porcelain -- src` は空・秘密の走査 CLEAN。

## 4. S6-G0 の割る前の試験の直しの、親の確かめと検収(第347・2026-11-19)

### 4-1. 別の役の検収(実装を見ていない、新しい検収役)

- 判定: **条件つき受入**(高 0・中 2・低 4)→ 直し(§3-10)→ 直しの差分の再検収 **受入**(高 0・中 0・低 2)。検収役はファイルを 1 本も変えていない。
- 割る前の範囲: 土台の版の助けの関数をメモリの中で呼び、今の版と並べた。違いは 0(`_PER_TICK`・`_hot_paths`・`_loop_scan_paths`・呼び手・違反・D ⑦ の関数・`_EXEMPT_D6` 2 本・`_callers_in_resolve`・体の呼び手)。
- 弱まり・空回り: 空の集合で通る形は無い(どこにも「空でない」か陽性の対照が在る)。欠陥をメモリの中で入れた試しでは、前に見つけた物を今も全部見つけ、今だけが見つける物も在る(`ufunc.at` が 0 件のとき・割った後の形の `_PER_TICK`)。`| set(RESOLVE_FILES)` は今 1 本で、前と同じ集合。
- 割った後の見立て: `resolve.py` をメモリの中で表のとおりに分けた木でも、凍結の表との差は空・36 系の書きの閉包は全部同じ・割り先ごとの別名も拾う。
- 範囲の手がかりの付け替え(6 本): 前と後で同じ範囲(`files_from`・`rels_from` は 185 本・`names_from` は 17/168・25/218・34/284)。
- 外した確かめ: 裁定 Q7 の 2 つだけ(値 `(30, 2, 10, 1)` は今も守られている)。
- 足した試験: `resolve_index_frozen.json` は今の索引と一致(関数 101・直接の書き 73 行・42 行/115 辺・表 4・帳簿の口 5・別名の書き 2)。負の対照は試験の 3 つと、検収役が足した 4 つが全部差に出る。前向きの表の条件 ③ と 3 つの種の確かめは空回りしない。
- カードの道具: 土台の道具と今の道具は、書きの許可の節(20 ファイル・228 行・問題 0)が同じ。

### 4-2. 検収の中 2 件・低 4 件と、再検収の低 2 件の扱い

- 中-1(書き手の一覧 `RESOLVE_FILES` の中身を、どの試験も固定していない=字面の固定 3 つを形の確かめに替えて弱まっていた): **直した**(§3-10 の直し 1)。再検収: 関数を持たないファイル・頭だけの `__init__.py`・`async def` だけのファイルを足すと新しい確かめが落ち、索引に無い関数を持つファイルを足すと凍結の表が落ち、関数を写した別のファイルを足すと索引が止まる。割る前の一覧は `("engine/resolve.py",)` 以外になりえない。
- 中-2(`_loop_scan_paths` を割り先の全部へ広げる 1 行を入れていない): **表と順の commit で足す**(今は、割る道具の表に S6-A の前の名が残っていて `split_files("engine/resolve.py")` が落ちる=検収役がメモリの中で呼んで確かめた)。名の表は、古い名を消すだけでなく `write_b4_hash`・`write_intero_stages` を足す(足さないと `detect_writes.py` が走査から外れる)。S6-G1 の前に必ず入れる。
- 低-1(体の口の呼び手の見方が前の形を含まない)・低-2(割った後に空回りする「書かない」の確かめ)・低-3(記録)・低-4(カードの道具が表の名の重なりを問題に書かない): 直した(§3-10 の直し 2・3・6・4)。道具の拡張の検収の低-2(「前向きの表は空」の比べ)も直した(直し 5)。
- 再検収の低-1(割った後に、`_require_thawed` だけを持つファイルが一覧にまぎれても気づかない。計画の割り先では起きない): 次の試験の側の commit(別名の分け)で、確かめに渡す集合から除く関数を引く 1 行を足す。
- 再検収の低-2(直し 5 の試験は、1 本だけで見ると「前向きの表が空」の固定を手放した): §3-10 の「前の確かめと同じ強さ」は、束で見たときの話。宣言のあるファイルを別の台帳の道へ向ける行は宣言と台帳の比べが落とし、宣言の無いファイルを指す行は条件 ③ の試験が落とす(通るのは答えを変えない行だけ)。
- 検収役の手順の注(2 つ・どちらも中身は開いていない): 検索を 1 回、作業木の根で回したため、開かない約束の文書の当たり 2 行が出力に出た/更新の時刻を比べる走査が `tests` の下の全部に入った(名前も中身も表示していない)。以後の発注には「検索と走査は根と `tests` の全体で回さない」と書く。

### 4-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`・§3-10 の直しの前に集めた回) | 7,005 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・22 skipped・1 xfailed・40 分 00 秒。前の回(S6-A)の 6,996 から、足した試験 9 本(凍結の索引 6・前向きの表の条件 ③ 1・場合が空でない確かめの種 2)で +9 |
| §3-10 の直しの後に、直した 5 本を回し直した(`-n 2`) | 直した 5 本と `test_detection_writes_split.py` で 144 passed・落ちた試験 0(5 本は 109 → 110=直し 1 の負の対照で +1。範囲の全体は直しの後に回し直していない) |
| `git status --porcelain -- src` | 空(src は変えていない=byte-check は要らない) |

## S6-G0 の表と順(土台 `c8bfcde`=割る前の試験の直しの commit・2026-11-19)

`engine/resolve.py` を、割る道具の本物の表と順に入れた(23 本目の割る行)。src は変えていない。本物の木には書いていない(書かない実行だけ)。

### 表と順-1. 変えたファイルと行(`git diff --numstat`・足した/消した)

| ファイル | 行 | 何を |
|---|---|---|
| `docs/reference/package-map-final-2026-11-09-files.md` | 27 / 8 | §3 に 14 行(225a〜225n)・225 の行に注・§4-14 の直しと注 4 つ |
| `tools/pkgmove/map.toml` | 121 / 6 | `cli.py map` で作り直した(手で書いていない) |
| `tools/pkgmove/contracts.toml` | 47 / 0 | `[[ignore_split]]` 4 本(割 5〜8)と `[[split_weakens]]` 1 つ |
| `tools/pkgmove/split.py` | 9 / 4 | `SPLIT_PATH_DESTS` に 2 行(裁定 Q8) |
| `tools/pkgmove/table.py` | 4 / 1 | `SPLIT_ORDER` の 23 本目と `SPLIT_GROUPS["6"]`(裁定 Q9) |
| `tests/tools/test_pkgmove.py` | 34 / 16 | 表と順の数を直した(試験は足していない) |
| `tests/engine/test_two_phase.py` | 4 / 3 | `_loop_scan_paths` の 1 行(裁定 R1・§4-2 の中-2) |
| `tests/engine/state/mind_world_reads_frozen.json` | 5 / 5 | `_cell_of_node` の行と `md_source` の sha256(検収の低-1) |

### 表と順-2. 表の直し(§3・§4-14)

| 所 | 前 | 後 | 裁定 |
|---|---|---|---|
| §3 225a〜225n(14 行・新) | 無し | 2 つ目以降の割り先の move の形の行(`engine/<名>.py` → 割り先。`mind/ops.py` は包み mind・`runtime/state/restore.py` は包み runtime・ほかは act)。割る前は old も new も無い | Q5(仮採用・5a の Q1 の作法) |
| §3 225 の何故の欄 | — | 注: S6-A の 2 つの名と 14 行 | Q3 |
| §4-14 `act/apply.py` の定数 | `_UNADDRESSABLE` あり・「ほか 1 個」 | `_UNADDRESSABLE` を外した・`_ACTION_ORDER_BY_VOCAB` を開いた | Q2・5a の Q9/5b の Q3 の見方 |
| §4-14 `act/ops/talk.py` の定数 | なし | `_UNADDRESSABLE` | Q2 |
| §4-14 `act/ops/move.py` → `act/ops/rail.py` | `_cell_of_node` は move | rail | Q2 |
| §4-14 `mind/ops.py` | `apply_detection` の心の欄を書く半分(〔〕の外の字) | `write_intero_stages` | Q3 |
| §4-14 `act/ops/detect_writes.py` | `apply_detection` | `write_b4_hash` | Q3 |
| §4-14 `foundation/vocab/agent_codes.py` | `_REFRACTORY_TICKS` が 2 回 | 1 回 | 重なりの直し(5a の Q9 の見方) |

- 行数の欄は元の見積りのまま(道具は行数の欄を読まない。5b の G0 と同じ扱いで、注に書いた)。
- `map.toml`: 358 行(keep 94・delete 2・move 235・split 25・empty 2)。前は 344 行・move 221。resolve の行は `split_order = 23`・名が揃った(131 名)。前の表との名の違いは上の 5 つの名だけ。

### 表と順-3. 順・群・宣言・決まりの表

- `SPLIT_ORDER` は 23 本(末尾に `engine/resolve.py`)・`SPLIT_GROUPS["6"] = {"G1": (23, 23)}`。
- `SPLIT_PATH_DESTS`(E8): `runtime/state/ledger.py::_ALLOW_REVENUE` → `act/ops/shop.py`(収入の書きの許可の字面が在るのは `_complete_buy`・`_complete_eat`)・`runtime/state/ledger_ast.py::ext_reason` → `runtime/state/restore.py`(`restore` で始まる関数=再開の復元)。
- `contracts.toml` の割る段の例外 4 本(どれも `appears_with = "engine/resolve.py"`・`gone_at = "注釈だけ"`)。割った後の木(メモリの中)を AST で読んで、4 本とも読みは注釈だけだった(`from __future__ import annotations` あり・実行の時の読み 0・文字列の注釈 0)。

| 割 | 辺 | 決まり | import の行と名 |
|---|---|---|---|
| 5 | `act.ops.detect_writes` → `mind.system1.change_detect` | 1 | 行 10 `DetectResult` |
| 6 | `mind.ops` → `world.model.agent_table` | 3 | 行 13 `AgentState` |
| 7 | `runtime.state.restore` → `world.model.agent_table` | 10 | 行 13 `AgentState` |
| 8 | `runtime.state.restore` → `world.model.state` | 10 | 行 16 `World` |

- `[[split_weakens]]`(resolve): 消える古い決まり 1 つ(`layers: census > economy > engine > …`=包み engine が消える)・言えなくなる新しい決まり 0。

### 表と順-4. 試験(前 → 後)

| 何を | 前(c8bfcde) | 後 |
|---|---|---|
| `test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 150 passed・21 skipped | 150 passed・21 skipped(飛ぶ顔ぶれは同じ。次の割る行の書かない実行の試験は、今は resolve の行を通る) |
| slow: 5a・5b の順の当て(23 本目まで) | — | passed 22 秒(決まりは古い 1・新しい 10・決まり 2 と 4 は言える) |
| slow: 履歴の当て直し(E5-b) | — | passed 57 秒 |
| `test_two_phase.py`(1 行を足す前と後) | 14 passed | 14 passed(同じノード。割る前の走査の範囲は前も後も 36 本で同じ=resolve は `engine/resolve.py` の 1 本) |
| `tests/tools` の残り・`tests/test_places_guard.py`・`tests/engine/state`・`bridging`・`systems`・`test_energy_balance.py`(`-n 2`) | — | 929 passed・落ち 0・飛び 0 |
| `map --check`・`contracts --stage delete --tree . --check --probe`・`lint-imports` | — | 同じ・同じ(古い 2+新しい 9・例外 26 行/20 辺・割 5〜8 は「割る行がまだ当たっていない」で載らない)・11 kept |

- `split_files("engine/resolve.py", …)` の呼び手 3 か所(`test_resolve_index_frozen.py`・`test_energy_balance.py`・`test_two_phase.py`)は、表を直した後に落ちる所も縮む所も無い。
- 凍結の JSON: `apply_detection` は S6-A で消えていた。残っていた古い形は `_cell_of_node` の置き場だけ(move → rail に移した)。`md_source` を今の表の sha256 に直し、注を足した。心の割り先は変わらないので数(`key_counts` と合計)は同じ。値の意味は変えていない。

### 表と順-5. 本物の木の書かない実行(`cli.py split --through engine/resolve.py`)

- 守り: 全部「同じ」(13 項・④ は前向きの表で)・決まりは「宣言どおり 4」・止めた守り 0。割り先 18。`deleted` は `engine/resolve.py` と `engine/__init__.py`(包み engine が消える)・作った頭は `act/ops/__init__.py`。
- 前向きの表: 2 行(`act/ops/plan_writes.py`・`mind/ops.py` → `engine/resolve.py`)。台帳の道は 1 行を足す。E8 の宣言 2 つは各 1 か所で使われた。
- 決まり: 前 古い 2・新しい 9・例外 26 行/20 辺 → 後 古い 1・新しい 10・例外 18 行/16 辺。消える例外 8 本(28 本の表の #1〜#4・#13・#14・#16・#21)・載る 4 本(割 5〜8)。宣言した弱まり 4・宣言の無い弱まり 0。取り直し §4・§5 の見込みと同じ。
- E5-b: 確かめた 10 群・11 か所(`discard_probe`・`test_du_runs`・`test_m4_m5_people`・`proximity/test_runs` 2 名・`test_no_permission_count`・`test_meal_bundle_2b` 2 か所・`test_removed_switches_346` のコードの文字列・`test_state_checks_10f`・`test_state_ledger_10b`)。見られなかった 5 群・6 か所(`test_resume_10d` の `advance_body`・`initialize`・`test_sim_time_T` の `advance_body`・`tools/c7/attr_arms.py`・`tools/c7/occupancy_series.py` の `apply`)は、どれも手で直す一覧の別名を通る差し替え(別名を分ければ確かめられる)。読み込みの時だけの読み 0。

### 表と順-6. 手で直す一覧(49 文・45 ファイル。前の 74 文から減った)の 4 つの分け(分けただけ・決めていない)

- **(i) 別名を割り先ごとに分ければ消える import(46)**: `from shibuya.engine import resolve` の別名の読みの割り先が 1 つに決まらないもの。
  - src 8(S6-G1 で直す): `interim_bundles/calendar_self.py:89`・`mind/relations/layer.py:83`・`runtime/systems/assemble.py:38`・`body.py:20`・`judge.py:27`・`perceive.py:18`・`talk.py:27`・`world/laws/presence.py:99`。
  - tests 36: `engine/body/test_body_same_values.py:16`・`engine/clock/test_tm3_step_scope.py:99・145・249`・`engine/processes/` の `test_civic:11`・`test_crowd:14`・`test_opening:12`・`test_rail:14`・`test_rail_board_intent:26`・`test_rail_return:26`・`engine/proximity/test_rule.py:24`・`engine/rights/` の `test_rights_events:20`・`test_staff_of_poi_equivalence:18`・`engine/systems/test_stage_a_guard.py:18`・`engine/` 直下の `test_ablation23_switches:33`・`test_add_at_guard:26`・`test_c9b_targets_attention:42`・`test_conversation_invite:24`・`test_defect_fixes_1103:24`・`test_detection_writes_split:24`(S6-A で足した試験)・`test_familiarity:24`・`test_geometry_c9:32`・`test_intent_chooser:17`・`test_intent_hold:35`・`test_ledger_wiring:39`・`test_meal_gate_per_hour:189`・`test_move_destination:20`・`test_plan_sleep_d62:30`・`test_presence_exit_walk:20`・`test_resolve:16`・`test_resume_10d:288・593`・`test_sim_time_T:28`・`test_stage3_small_fixes:14`・`test_two_layer_activity:38`・`test_vocab_v2_eat:23`。
  - tools 2: `tools/c7/attr_arms.py:264`・`tools/c7/occupancy_series.py:172`(別名 `module`。E5-b の見られなかった 2 群もここ)。
- **(ii) E8 の宣言で向けられる道の文字列: 0**。src の 2 つ(`ledger.py`・`ledger_ast.py`)は上の宣言で向いた。ほかに名の手がかりの無い道は残っていない。
- **(iii) 書き換えから外す候補(3)**:
  - `tests/economy/cp2/test_cp2_write_window.py` の `test_negative_window_and_balance_write`・`test_negative_setattr_and_named_writes`: `"engine/resolve.py"` は、コードの断片に付ける「窓の外のファイル」の名札(`window_refs(code, path)`・`MW.scan_source(code, path)`)。負の対照の偽の道で、ファイルが在るかどうかは結果を変えない。案: `STRING_EXCLUDE` に 2 行(わけ=負の対照の名札)、または手で今在る道に替える。
  - `tools/repo_guide/guide_permits.py::RESOLVE_FILE`(`shibuya.engine.resolve`): `allow.py` に `RESOLVE_FILES` が無い木(カードの試験の見本の木。`tests/tools/test_repo_guide.py` が見本の木のこの道に resolve の材料を置く)で読む 1 本(決め事 3)。本物の木は `RESOLVE_FILES` の全部を読む。案: 見本の木の材料として外す。ただし `guide_render.py` が、置き場の分からない関数のカードの既定にもこの道を使うので、(iv) と見るなら案は「既定を主な割り先 `act/apply.py` にする」(`tools/repo_guide` は今回の範囲の外)。
- **(iv) そのほか: 0**(上の `RESOLVE_FILE` の読み方しだい)。

### 表と順-7. 計画や取り直しと違った所

- 手で直す一覧: 道具の拡張の時の今の木の書かない実行は 74 文 → 割る前の試験の直し(`c8bfcde`)と表の直しの後は 49 文。中身は、import の別名 52 → 46(tests 42 → 36。src 8・tools 2 は同じ)・道の文字列 21 → 2・名の無い点の道 1 → 1。減ったのは、割る前の試験の直しで消えた試験の字面の `"engine/resolve.py"` と別名の import。
- 凍結の JSON の古い名は `apply_detection` ではなく `_cell_of_node` の置き場だった(裁定 Q2 で表を直したため)。
- 表の行数の欄は直していない(上のとおり)。数の見込み(358/235・23 本・古い 1+新しい 10・消える 8/載る 4・18 行/16 辺・前向きの表 2 行)は全部、見込みどおり。
- 範囲の全体の試験・byte-check・ランは回していない(src は変えていない)。`tests/c7` は開いていない・検索の範囲にも入れていない。カードは作り直していない。

## S6-G0 の表と順: 親の確かめと検収(第347・2026-11-19)

### 表と順(親)-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 2)。検収役はファイルを 1 本も変えていない。
- 表の名と割り先: 今の `resolve.py` の頂上の名 131 と、`map.toml` の resolve の行の名 131 がちょうど一致する。前の表から変わった名は 6 つだけ(`_UNADDRESSABLE` → talk・`_cell_of_node` → rail・`apply_detection` → `write_b4_hash`/`write_intero_stages`・`_ACTION_ORDER_BY_VOCAB` → apply)で、裁定に無い名は動いていない。割り先は 18。足した 14 行は、新しい 2 つ目以降の割り先とちょうど同じ(既に在る 3 本には行が無い)。
- 循環: 割った後の割り先どうしに、互いに読む組は 0(守り `import_cycles` は「同じ」)。
- 決まりの例外 4 本(割 5〜8): 割った後の字面を AST で読むと、4 本とも注釈だけの辺(`from __future__ import annotations` あり・実行の時の読み 0・`TYPE_CHECKING` 0・文字列の注釈 0)。今の木では載らない(「割る行がまだ当たっていない」)。検収役が決まりを自分で評価し(関数の中の import と間接の鎖まで)、割る前も割った後も破りは 0・4 本を 1 本ずつ外すとそれぞれ破りが出る=4 本とも効き、ほかに要る例外は無い。`[[split_weakens]]` は宣言どおり 4・宣言の外 0。契約は古い 2+新しい 9 → 古い 1+新しい 10・例外は 26 行/20 辺 → 18 行/16 辺・消える 8 本は #1〜#4・#13・#14・#16・#21。
- 道の文字列の宣言 2 行: `act/ops/shop.py` には `_require_thawed(world, world.pois.revenue)` を持つ `_complete_buy`・`_complete_eat` が、`runtime/state/restore.py` には `restore_soa`・`restore_items` が在る(ほかの割り先に当たる関数は無い)。
- 書かない実行(検収役がメモリの中で 1 回): 守り 13 項はどれも「同じ」・消えるのは `engine/resolve.py` と `engine/__init__.py`・作る頭は `act/ops/__init__.py`・前向きの表 2 行・手で直す一覧 49 文は実装役の一覧とファイル・行まで一致(分け漏れなし)。
- `_loop_scan_paths`: 割る前は resolve の 1 本(範囲 36 本は同じ)・割った後は 18 本(`detect_writes` と既に在る 3 本を含む)。
- `test_pkgmove` の数の直しは表と合う(358 行・move 235・2 つ目以降の行 30・順 23・群)。確かめを弱めた所は無い。凍結の JSON は `_cell_of_node` を act の行の間で移したのと sha の直しだけ(心の数は同じ)。

### 表と順(親)-2. 検収の低 2 件と、書き換えから外す候補 3 件の裁定

- 低-1(S6-G1 の手直しは、道具の「手で直す一覧」の外にも在る=`allow.py` の `RESOLVE_FILES` を 15 本へ・`money_writers_frozen.json` の 4 行の道・`mind_world_reads_frozen.json` の `scope.split` の resolve の項): S6-G1 の発注に入れる。
- 低-2(カードの道具 `guide_render` は、置き場の分からない口の名を `RESOLVE_FILE` へ黙って置く。割った後の本物の木では使われない): そのまま(範囲の外)。
- `tests/economy/cp2/test_cp2_write_window.py` の負の対照 2 本の `"engine/resolve.py"`(合成のコード片に付けた名札で、ファイルは読まない): **割る前に、どの割る段にも当たらない名札の字面へ手で直す**(検収役の見立てを採る。同じノードの前後を記録)。次の commit で。
- `tools/repo_guide/guide_permits.py` の `RESOLVE_FILE`(`RESOLVE_FILES` の無い見本の木のための 1 本。`test_repo_guide` の見本の木がこの道に resolve の材料を置く): **道具の書き換えから外す**(`split.STRING_EXCLUDE`)。書き換えると `test_repo_guide` が落ちる。次の commit で。
- 別名を「渡す・返す・しまう」形で使う所(試験 3 本・`tools/c7` の 2 本・src の `judge.py`)は、別名を分けても手で直す一覧に残る。扱いは次の commit で決める(別名の割り先の宣言に、素で使ってよい別名の印を足す案)。

### 表と順(親)-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 150 passed・21 skipped・落ちた試験 0(数は前と同じ・飛ぶ 21 本も同じ) |
| `tests/tools/test_pkgmove.py` の slow | 2 passed(本物の表と木で順に当てる試験は 23 本目まで・履歴の当て直し) |
| `tests/tools` の残り・`tests/engine/test_two_phase.py`・`tests/engine/state`・`tests/test_places_guard.py`(`-n 2`) | 745 passed・落ちた試験 0(`test_pkgmove.py` を除く・`tests/engine/test_energy_balance.py` を含む) |
| 本物の木の `map --check`・`contracts --check --probe` | 同じ・同じ(今の木では例外 20 辺・延べ 26 行のまま。割 5〜8 は割る行を当てた後に載る) |
| `git status --porcelain -- src` | 空(src は変えていない=byte-check は要らない) |
