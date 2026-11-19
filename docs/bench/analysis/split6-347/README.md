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

## 5. S6-G0 の試験と tools の別名の分け(土台 `c8bfcde`・2026-11-19)

割る道具の厳しい当て(`--apply` の道)は、手で直す一覧が 1 つでも残ると当てない。いちばん大きな部分は、1 つの別名(`from shibuya.engine import resolve as R`)から割り先の違う名を 2 つ以上読む import。5a・5b と同じ作法で、割る前の今のうちに、試験(`tests/`。c7 を除く)と tools の別名を割り先ごとに分けた(分けた別名は、今は全部 `shibuya.engine.resolve` を指す=挙動は同じ。属性の読みのまま。名の import にしない)。src の別名(8 本)は S6-G1(byte-check の commit)で直す。src・`tools/pkgmove/`・`tools/bytecheck/`・`tests/tools/test_pkgmove.py`・表・`map.toml`・`contracts.toml`・`pyproject.toml`・`test_two_phase.py` の `_loop_scan_paths` は変えていない。

### 5-1. 別名の名と割り先(リポの全体で同じ割り先には同じ名)

| 別名 | 割り先 | 別名 | 割り先 |
|---|---|---|---|
| `R_APPLY` | `act/apply.py` | `R_PLAN` | `act/ops/plan_writes.py` |
| `R_GATE` | `act/gate.py` | `R_RAIL` | `act/ops/rail.py` |
| `R_BODY` | `act/ops/body_writes.py` | `R_SHOP` | `act/ops/shop.py` |
| `R_DETECT` | `act/ops/detect_writes.py` | `R_TALK` | `act/ops/talk.py` |
| `R_FOCUS` | `act/ops/focus.py` | `R_MIND` | `mind/ops.py` |
| `R_INIT` | `act/ops/init_writes.py` | `R_RESTORE` | `runtime/state/restore.py` |
| `R_INTENT` | `act/ops/intent_writes.py` | `R_GUARD` | `foundation/write_guard.py` |
| `R_LAW` | `act/ops/law_writes.py` | `R_ACT_CODES` | `foundation/vocab/act_codes.py` |
| `R_MOVE` | `act/ops/move.py` | `R_AGENT_CODES` | `foundation/vocab/agent_codes.py` |

- 元の別名 `R` は、そのファイルでいちばん多く読む割り先に残した(同じ数なら割り先の道の字の順で先)。名 → 割り先は、親の scratch の名 → 割り先の表(全ファイルの表 §4-14 から作った表に、裁定 Q2 の 2 名・S6-A の 2 名・`_ACTION_ORDER_BY_VOCAB` を当てたもの)。表に無い名(resolve が import で結んで再輸出する名=`ACT_BUY`・`ACT_EAT`)は、道具の再輸出の割り先(主な割り先が先=`act/apply.py`)。
- import の文は、その有効範囲(頂上か関数の中)で読む割り先の別名だけを置いた(読まない別名は足さない)。文の上に注 1 行(長ければ「・」で折り返し)。

### 5-2. 直したファイル(32 本・別名の数・読みの数)

| ファイル | 別名の数 | 別名=割り先(読みの数) | 読みの数 |
|---|---:|---|---:|
| `tests/engine/body/test_body_same_values.py` | 2 | `R`=act/apply(1)・`R_SHOP`=act/ops/shop(1) | 2 |
| `tests/engine/clock/test_tm3_step_scope.py` | 2 | `R`=act/ops/detect_writes(5)・`R_MIND`=mind/ops(5) | 10 |
| `tests/engine/processes/test_civic.py` | 2 | `R`=act/apply(1)・`R_RAIL`=act/ops/rail(1) | 2 |
| `tests/engine/processes/test_crowd.py` | 3 | `R`=act/apply(14)・`R_RAIL`=act/ops/rail(7)・`R_SHOP`=act/ops/shop(5) | 26 |
| `tests/engine/processes/test_opening.py` | 2 | `R`=act/ops/rail(2)・`R_LAW`=act/ops/law_writes(1) | 3 |
| `tests/engine/processes/test_rail.py` | 2 | `R`=act/apply(13)・`R_RAIL`=act/ops/rail(2) | 15 |
| `tests/engine/processes/test_rail_board_intent.py` | 3 | `R`=act/apply(24)・`R_RAIL`=act/ops/rail(4)・`R_TALK`=act/ops/talk(1) | 29 |
| `tests/engine/processes/test_rail_return.py` | 2 | `R`=act/ops/rail(6)・`R_APPLY`=act/apply(1) | 7 |
| `tests/engine/proximity/test_rule.py` | 2 | `R`=act/ops/talk(6)・`R_ACT_CODES`=foundation/vocab/act_codes(3) | 9 |
| `tests/engine/rights/test_rights_events.py` | 2 | `R`=act/ops/law_writes(1)・`R_RAIL`=act/ops/rail(1) | 2 |
| `tests/engine/rights/test_staff_of_poi_equivalence.py` | 2 | `R`=act/ops/init_writes(1)・`R_RAIL`=act/ops/rail(1) | 2 |
| `tests/engine/systems/test_stage_a_guard.py` | 2 | `R`=foundation/write_guard(2)・`R_MIND`=mind/ops(2) | 4 |
| `tests/engine/test_ablation23_switches.py` | 2 | `R`=mind/ops(17)・`R_INIT`=act/ops/init_writes(1) | 18 |
| `tests/engine/test_add_at_guard.py` | 2 | `R`=foundation/write_guard(3)・`R_MIND`=mind/ops(1) | 4 |
| `tests/engine/test_c9b_targets_attention.py` | 5 | `R`=act/ops/focus(14)・`R_ACT_CODES`=foundation/vocab/act_codes(8)・`R_APPLY`=act/apply(13)・`R_GATE`=act/gate(3)・`R_TALK`=act/ops/talk(3) | 41 |
| `tests/engine/test_conversation_invite.py` | 2 | `R`=act/ops/init_writes(3)・`R_TALK`=act/ops/talk(3) | 6(渡す別名は素の使い方=§5-4) |
| `tests/engine/test_defect_fixes_1103.py` | 4 | `R`=act/apply(6)・`R_RAIL`=act/ops/rail(4)・`R_SHOP`=act/ops/shop(3)・`R_TALK`=act/ops/talk(3) | 16(渡す別名は素の使い方=§5-4) |
| `tests/engine/test_detection_writes_split.py` | 2 | `R`=act/ops/detect_writes(4)・`R_MIND`=mind/ops(4) | 8 |
| `tests/engine/test_familiarity.py` | 2 | `R`=act/gate(2)・`R_SHOP`=act/ops/shop(2) | 4 |
| `tests/engine/test_geometry_c9.py` | 2 | `R`=act/gate(2)・`R_APPLY`=act/apply(1) | 3 |
| `tests/engine/test_intent_chooser.py` | 3 | `R`=act/apply(12)・`R_GATE`=act/gate(1)・`R_SHOP`=act/ops/shop(3) | 16 |
| `tests/engine/test_intent_hold.py` | 6 | `R`=act/ops/intent_writes(3)・`R_APPLY`=act/apply(2)・`R_GATE`=act/gate(1)・`R_INIT`=act/ops/init_writes(1)・`R_RAIL`=act/ops/rail(1)・`R_SHOP`=act/ops/shop(1) | 9 |
| `tests/engine/test_ledger_wiring.py` | 3 | `R`=act/ops/law_writes(4)・`R_APPLY`=act/apply(1)・`R_INIT`=act/ops/init_writes(1) | 6 |
| `tests/engine/test_move_destination.py` | 2 | `R`=act/gate(1)・`R_MOVE`=act/ops/move(1) | 2 |
| `tests/engine/test_plan_sleep_d62.py` | 3 | `R`=act/ops/plan_writes(6)・`R_APPLY`=act/apply(2)・`R_INIT`=act/ops/init_writes(2) | 10 |
| `tests/engine/test_presence_exit_walk.py` | 5 | `R`=act/gate(4)・`R_ACT_CODES`=foundation/vocab/act_codes(3)・`R_RAIL`=act/ops/rail(1)・`R_SHOP`=act/ops/shop(1)・`R_TALK`=act/ops/talk(1) | 10 |
| `tests/engine/test_resolve.py` | 5 | `R`=act/apply(7)・`R_BODY`=act/ops/body_writes(2)・`R_DETECT`=act/ops/detect_writes(1)・`R_INIT`=act/ops/init_writes(1)・`R_MIND`=mind/ops(3) | 14 |
| `tests/engine/test_resume_10d.py` | 2 | `R`=act/ops/body_writes(3)・`R_INIT`=act/ops/init_writes(2) | 5 |
| `tests/engine/test_sim_time_T.py` | 2 | `R`=act/ops/body_writes(2)・`R_MIND`=mind/ops(2) | 4 |
| `tests/engine/test_stage3_small_fixes.py` | 2 | `R`=act/gate(1)・`R_SHOP`=act/ops/shop(1) | 2 |
| `tests/engine/test_two_layer_activity.py` | 7 | `R`=act/ops/init_writes(5)・`R_APPLY`=act/apply(1)・`R_BODY`=act/ops/body_writes(3)・`R_GATE`=act/gate(2)・`R_MIND`=mind/ops(1)・`R_MOVE`=act/ops/move(1)・`R_SHOP`=act/ops/shop(1) | 14 |
| `tests/engine/test_vocab_v2_eat.py` | 3 | `R`=act/apply(11)・`R_INIT`=act/ops/init_writes(1)・`R_SHOP`=act/ops/shop(4) | 16 |

- `test_intent_chooser.py` の `R`(`act/apply.py`)の読み 12 は、再輸出の名 `ACT_BUY`・`ACT_EAT`(上の表の数に入っていない)。
- `test_resume_10d.py` は関数の中の import 2 つ: 1 つ目の関数は `initialize` だけを読むので別名を `R_INIT` だけにした・2 つ目は `R`(`advance_body`)のまま。

### 5-3. 差し替えの向け先(取り直し §7 の 17 か所のうち試験と tools の物)

| 名 | 差し替え | 差し替える先(取り直し §7) | 今の別名と、その割り先 |
|---|---|---|---|
| `advance_body` | `tests/engine/test_resume_10d.py:623・633`・`test_sim_time_T.py:221` | body_writes | `R`=body_writes(両方のファイル) |
| `advance_body` | `discard_probe.py:180`・`test_state_checks_10f.py:439`・`test_state_ledger_10b.py:682`・`test_removed_switches_346.py:120`(コードの文字列) | body_writes | 別名が 1 つの割り先だけを読む=道具が機械で直す(この節では触っていない) |
| `initialize` | `test_resume_10d.py:308` | init_writes | `R_INIT`=init_writes |
| `energy_out_of_area_meal` | `test_meal_bundle_2b.py:488・492` | body_writes | 機械で直る(同上) |
| `discard_to_bin`・`request_open_close`・`set_conversing`・`join_conversation`・`write_relations` | 取り直し §7 の各 1 か所 | law_writes・law_writes・talk・talk・mind/ops | 機械で直る(同上) |
| `apply` | `tools/c7/attr_arms.py:281`・`occupancy_series.py:182` | act/apply | 直していない(§5-4) |

書かない実行の E5-b(差し替えの届く先の守り)で、差し替え 17 か所のうち 15 か所(13 項)が「確かめた」=定義の割り先へ届く。前は 10 項(手で直す一覧の別名の 5 項が「見られなかった」)。残る「見られなかった」は tools/c7 の 2 か所だけ。

### 5-4. 関数へ渡す形・返す形・tools/c7 の 2 本(素の使い方。返す形は検収の後に直した・残る 4 本は道具の側の宣言で通す=§5-7)

道具は、別名を素で使う(関数へ渡す・返す・属性に入れる)別名を、読む名の割り先が 1 つでも手で直す一覧に出す。割る前の今、別名を分けても素の使い方は残るので、次の 5 本は一覧に残った(見立ての割り先には向けた)。うち `test_meal_gate_per_hour` は、検収の後に形を直して一覧から外した(§5-7 の直し 1)。

- `tests/engine/test_conversation_invite.py:310`・`test_defect_fixes_1103.py:335・355・447・493・526`: 別名を `runtime/run.py::_settle_pending_invites(…, R, …)` へ渡す。中で読むのは talk の 4 名(`end_conversation`・`revert_conversation`・`set_conversing`・`talk_within_reach`=今の木で確かめた)=取り直し §6 の見立てどおり、渡す別名を `R_TALK` にした(そのファイルの talk の読みも `R_TALK`)。
- `tests/engine/test_meal_gate_per_hour.py:189`: 関数 `_energy_policy` が別名を返す。呼び手が返った別名で読むのは全部 body_writes の名=別名 `R` は body_writes だけを読む(別名を分ける直しは要らなかった)。割る前に直せない形と見ていたが、検収の後に直せた(§5-7 の直し 1=助けは別名を返さず、呼び手が自分で別名を持つ)。
- `tools/c7/attr_arms.py:264`・`tools/c7/occupancy_series.py:172`: `module.apply` を包む(読む名は `apply` だけ=act/apply)。手で直す一覧に出るわけは、別名を属性に入れる(`self._module = module`)・引数で受ける(`occupancy_series.attach(module=None)`)素の使い方。割る前に直す形は、割った後の置き場(`shibuya.act.apply`)を先に書くか、取り付けと取り外しの形を作り替えることになる=直していない。
- この 5 本は、割る道具が素の使い方の別名を書き換えないので、S6-G1 で手で直す物(または道具の側の口)。親に聞いた結果、`_energy_policy` は割る前に直し、残る 4 本は道具の側の宣言で通す(§5-7)。

### 5-5. 一緒に入れた小さな直し(再検収の低-1)

`tests/engine/state/test_move_prep_stage2.py`: 「一覧のどのファイルも索引の関数を 1 つ以上定義する」の確かめに渡す関数の集合から、凍結の表で除く関数(`_require_thawed`=`RI.EXCLUDED`)を引いた(`AL.index().funcs - RI.EXCLUDED`)。割った後に、その関数だけを持つファイルが一覧にまぎれても気づく。負の対照に 1 つ足した: 除く関数だけを索引の関数として持つファイル(今の置き場を対応表から引く)は、引く形では「索引の関数を定義しない」に挙がり、引かない形では挙がらない。

### 5-6. 確かめ

| 何を | 結果 |
|---|---|
| 手で直す一覧(書かない実行=親の scratch の台本。割る道具を、段 6 の形にした表でメモリの中に当てる。道具の実装役の台本を写して、木を作業の木に替えた) | 前 49 項(45 ファイル)=src の import 8・tests の import 36(33 本)・tools/c7 の import 2・文字列 3 → 後 16 項(15 ファイル)=src の import 8(S6-G1)・tests の import 3(素の使い方=§5-4)・tools/c7 の import 2(§5-4)・文字列 3(`test_cp2_write_window` の偽の道 2・`guide_permits.py::RESOLVE_FILE`=裁定 T4 と道具の検収の低-6 の振り分け=表と順の発注の側)。守りは前も後も全部「同じ」(契約は「宣言どおり 4」)・止めた理由 0 |
| E5-b(差し替えの届く先) | 前 確かめた 10 項・見られなかった 5 → 後 確かめた 13 項(差し替え 15 か所)・見られなかった 2(tools/c7 の 2=§5-4)・止めた 0 |
| AST の確かめ(足した別名を元の `R` へ戻し、同じ有効範囲で重なった `from shibuya.engine import resolve as …` を 1 つにする) | 32 本とも土台 `c8bfcde` の版と AST が同じ |
| 直したファイル(32 本と `test_move_prep_stage2`)の同じノード(`-n 2`・`-rA`) | 前 668 passed → 後 668 passed・skipped と failed は 0(ファイルごとに同じ数) |
| 束(`tests/engine` の直下の試験と `body`・`clock`・`processes`・`proximity`・`rights`・`systems`・`state`・`-m "not gpu and not slow"`・`-n 2`・合図を取って) | 2,157 passed・0 skipped・0 failed |
| `git status --porcelain -- src` | 空 |
| カード | 作り直した(`data.md` は単独で戻した・`--check` 最新) |
| 秘密の走査 | CLEAN |

- 見立てと違った所: 無い(関数へ渡す形は talk の 4 名・返す形は body_writes だけ=取り直し §6 のとおり)。違ったのは数だけ: 取り直しの tests の手で直す 42 文のうち、前の commit(割る前の試験の直し)で範囲の手がかり 5 本・`test_move_prep_stage2`・`LAYER_SRC`(裁定 R2)が外れて 36 文(33 本)。
- この節の台本(親の scratch に置いた。リポには入れていない): 別名を割り先ごとに分ける台本・足した別名を元の `R` へ戻して土台の版と AST を比べる台本・下調べ(別名ごとの読みと素の使い方を挙げる)の台本・道具の再輸出の割り先を引く台本・書かない実行の台本(道具の実装役の台本の写し。G1 の手直しの模擬は既定で回さない)。

### 5-7. 検収の後の直し(検収=受入の低 3・再検収=受入の低 2・親の裁定)

- 直し 1(低-1 の前半・親の裁定): `tests/engine/test_meal_gate_per_hour.py` の助け `_energy_policy` は別名を返さない形にした(返すのは `pol`・`lay` だけ)。呼び手 `test_a_meal_resets_the_hazard_but_a_snack_does_not` が、関数の中で自分の別名 `R` を import する。確かめる中身と、読む名(body_writes の 4 名=`_energy_snack`・`energy_home_meal`・`energy_out_of_area_meal`・`_energy_meal`)は変えていない。同じノード: 前 8 passed → 後 8 passed。
- 直し 2(表と順の検収の見立て・親の裁定。負の対照 2 は再検収の後に直し A で選び直した): `tests/economy/cp2/test_cp2_write_window.py` の負の対照 2 本の名札を、割る行の resolve の道から替えた。名札は合成のコード片に付けるだけで、`ALLOWED`(`economy/ops.py` の `transfer`)と `DECLARED`(凍結の表の (置き場, 関数))との照合に使う。ファイルは読まない。負の対照 1(窓)は `NEG_LABEL_WINDOW = "synthetic/negative_control.py"`: `ALLOWED` との照合だけなので、どの名札でも意味は「transfer の外」で変わらない。この字面は、全ファイルの表の道の字面・`map.toml` の文字列(old・new・split_to・names ほか)・段 6 の名 → 割り先の表のどれとも重ならず、木に無い。頭の包み `synthetic/` も表と木に無い(元の字面で同じ確かめをすると全部に当たる=正の対照)。負の対照 2(書き)の名札は次の直し A。同じノード: 前 5 passed → 後 5 passed。
- 直し A(再検収の低-1・親の裁定): 負の対照 2 も初めは `synthetic/…` にした。正しい実装での結果は名札によらないが、元の名札(凍結の表に書き手を持つ置き場)が持っていた「書き手の置き場の中でも、宣言に無い関数の書きは違反」の確かめが、この試験から落ちた。そこで負の対照 2 の名札を `NEG_LABEL_WRITER = "economy/ledger.py"`(`map.toml` の行 107=keep=割る道具も移す道具も書き換えない・凍結の表に書き手 4 関数)にして戻した。期待の一覧は同じ。負の対照: メモリの中で `MW.violations` を (ア) 宣言に書き手を持つ置き場なら関数を問わず通す・(イ) 置き場の宣言の列の和で見る、の 2 通りに壊すと、今の版の負の対照 2 は 2 つとも FAIL(`synthetic/…` の名札では 2 つとも気づかなかった。関数の名だけで見る壊れには、どの名札でも気づかない)。同じノード: 5 passed → 5 passed。書かない実行は 13 項のままで、この字面は手で直す一覧に出ない。
- 残った 4 本(`test_conversation_invite`・`test_defect_fixes_1103` が `R_TALK` を `_settle_pending_invites` へ渡す形・`tools/c7` の 2 本が `module` をしまう形と引数で受ける形): 形は直さない。割る道具の別名の割り先の宣言に「素で使ってよい別名」の印を足して通す(道具の側の次の commit)。こちらの側は今のまま。
- 低-2・低-3: §5-3 の行の番号を、別名を分けた後の木の番号に引き直した(`test_resume_10d.py` 623・633・308・`test_sim_time_T.py` 221。`test_state_ledger_10b.py` は土台でも 682=前の版の 681 は写しの誤り)。§5 で scratch の台本の置き場を名指ししていた所は、何をする台本かを書く形に替えた。
- 書かない実行の回し直し: 手で直す一覧 16 項(15 ファイル)→ 13 項(13 ファイル)=src の import 8(S6-G1)・tests の import 2(`test_conversation_invite`・`test_defect_fixes_1103`)・tools/c7 の import 2・文字列 1(`guide_permits.py::RESOLVE_FILE`=道具の側で書き換えから外す)。消えたのは直し 1・2 の 3 項だけ。E5-b は前と同じ(確かめた 13 項・見られなかった 2=tools/c7)・守りは全部「同じ」(契約は「宣言どおり 4」)・止めた理由 0。カードは作り直した(engine のカードの「読む試験(道筋で)」から `test_cp2_write_window` が外れた=字面の resolve の道を消した結果。`--check` は最新)。
- 検収役の見立て:
  - `_energy_policy`: 呼び手 1 本が body_writes の 4 名だけを読む。呼び手が自分で別名を持てば、割った後の置き場を書かずに素の使い方が消える。
  - `test_cp2_write_window` の名札(表と順の検収): 関数の名 `f`・`helper`・`leak` はどの道でも許可に無いので、名札を替えても結果は変わらない。再検収: 正しい実装での結果は同じだが、負の対照 2 の「置き場だけで見る形の壊れ」への感度は名札で変わる(束では `test_cp2_transfer_only_writer` の負の対照が気づく)=直し A。
  - `test_conversation_invite`・`test_defect_fixes_1103`: 渡した先で読むのは talk の 4 名だけ。関数の約束がモジュールを受け取る形なので渡さない形にはできない=宣言が筋。
  - `tools/c7/attr_arms.py`: 読む名は `apply` だけ。`detach` で import し直せば形も直せるが、`tests/c7` が `_module` を読むかは確かめていない(裁定は、c7 の試験を手元で回せないので形を変えずに宣言で通す)。
  - `tools/c7/occupancy_series.py`: 読む名は `apply` だけ。引数 `module` が外との約束(差し込み口)なので素の使い方は消せない=宣言が筋。

## 6. S6-G0 の試験と tools の別名の分けの、親の確かめと検収(第347・2026-11-19)

### 6-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 3)→ 続きの直し(§5-7)→ 再検収 **受入**(高 0・中 0・低 2)→ 低の直し(§5-7 の直し A・B)。検収役はファイルを 1 本も変えていない。
- 挙動: 検収役が自分の台本で、足した別名を有効範囲つきで元へ戻し、重なった import を 1 つにすると、32 本とも土台 `c8bfcde` の版と AST が同じ(関数の中の import も同じ)。
- 別名ごとの割り先: 直した 32 本と、resolve を import する試験と tools の 71 本で、1 つの束縛が 2 つ以上の割り先を読む所は 0・表に無い名を読む所も 0。別名の名はリポの全体でそろっている。
- 差し替え: 洗い出した差し替えは取り直しの 17 か所と同じ顔ぶれで、どれも定義の割り先の別名へ向いている(9 つの名とも、resolve の中に素の名で読む関数は無い)。
- 別名を渡す形・返す形: `_settle_pending_invites` が読むのは talk の 4 名だけ・`_energy_policy` の返り値を読む呼び手は 1 本で body_writes の 4 名だけ。

### 6-2. 検収の低と、親の裁定

- 残った素の使い方(別名を渡す・返す・しまう): `test_meal_gate_per_hour` は割る前に形を直した(§5-7 の直し 1)。`test_conversation_invite`・`test_defect_fixes_1103`(`R_TALK` を `_settle_pending_invites` へ渡す)と `tools/c7` の 2 本(`apply` を包む)は、**割る道具の宣言で通す**(別名の割り先の宣言に、素で使ってよい別名の印を足す=次の道具の commit)。`tools/c7` の形は直さない(その試験を手元で回せないため)。
- `test_cp2_write_window` の負の対照の名札: 木に無い名札へ替えると、負の対照 2 が「書き手の置き場の中でも、宣言に無い関数の書きは違反」をこの 1 本では確かめなくなる(再検収の低-1。検収役が、確かめる関数をメモリの中で 2 通りに壊して見つけた)。**負の対照 2 の名札を、割る行でも移す行でもなく、凍結の表に書き手を持つ置き場 `economy/ledger.py` にした**(§5-7 の直し A。壊した 2 通りで今の版が落ちる)。負の対照 1(窓)の名札は木に無い字面のまま。
- 別名の付け方(`R` を、そのファイルでいちばん多く読む割り先に残す・同数なら道の字の順): 受け入れる(正しさの面で困る所は無い。読みやすさのコストは段 8 の掃除の候補)。
- `tools/pkgmove/allow_tests_tools.toml` の古い行(名札を替えて要らなくなった許可): 残す(割る道具は読まない=今の動きに影響しない)。段 8 で消す。

### 6-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`・別名の分けの木・§5-7 の直しの前に集めた回) | 7,043 passed・2 failed・22 skipped・1 xfailed・39 分 36 秒。落ちた 2 本= 前からの 1 本(linked の作業木でだけ落ちる)と、`test_env_and_sections_10f.py::test_platform_id_ignores_commit_threads_and_dependency_versions`。後者は、実行環境の指紋(作業木の差分の sha を含む)が試験の始めと終わりで同じことを見る試験で、**親が範囲の試験の最中に、同じ作業木で §5-7 の直しを進めさせた**ために落ちた(木の差分が途中で変わった)。木が動かない状態で回し直すと通る(下の行)。前の回(7,005 passed・1 failed)から、道具の拡張の試験 38・前の commit の検収の後に足した負の対照 1 で +39(うち 1 本が上の落ちなので、passed は +38 の 7,043) |
| 木が動かない状態での回し直し(§5-7 の直しの後・`-n 2`): 直した試験のファイル 35 本/`test_env_and_sections_10f.py` | 681 passed/20 passed・落ちた試験 0 |
| 本体の頭(表と順の commit の後)へ載せ直した後の回し直し(直した試験のファイル 35 本と `test_two_phase.py`・`test_env_and_sections_10f.py`) | 715 passed・落ちた試験 0(35 本で 681・`test_two_phase.py` 14・`test_env_and_sections_10f.py` 20) |
| 載せ直した木で、本物の表での書かない実行(`split --through engine/resolve.py`) | 守りは全部「同じ」(決まりは宣言どおり 4)・手で直す一覧は 13(src の import 8・tests の import 2・`tools/c7` 2・名の無い点の道 1)・差し替えの届く先は確かめた 13・見られなかった 2(`tools/c7`) |
| `git status --porcelain -- src` | 空(src は変えていない=byte-check は要らない) |

## 7. S6-G1 の下ごしらえ: src の別名の分け(土台 `e543f3b`・2026-11-19)

写す段(S6-G1)を 2 つの commit に分けた 1 つ目。割る道具の厳しい当て(`--apply` の道)は、手で直す一覧が 1 つでも残ると当てない。本物の表での書かない実行の手で直す一覧 13 のうち、src の 8 本(1 つの別名から割り先の違う名を 2 つ以上読む頂上の import)を、割る前の今のうちに手で分けた。分けた別名は、今は全部 `shibuya.engine.resolve` を指す(挙動は同じ・属性の読みのまま・名の import にしない)。残りの 5(試験 2・`tools/c7` 2・`guide_permits.py` の 1)は道具の側の受け持ち(別の commit)。変えたのは src の 8 本とこの記録だけ(カードは作り直して変わらなかった)。試験・`tools/pkgmove/`・`tools/bytecheck/`・`tools/c7`・全ファイルの表・`map.toml`・`contracts.toml`・`pyproject.toml` は変えていない。

### 7-1. 決まり(試験の側の §5 との違い)

- 別名の名は、試験の側の表(§5-1)と同じ(`R_APPLY`=act/apply・`R_BODY`=act/ops/body_writes・`R_TALK`=act/ops/talk・`R_MIND`=mind/ops ほか 18 の割り先に 1 つずつ)。
- **src では元の別名 `R` を残さない**: 読みの全部を割り先の名の別名にした(試験の側は、いちばん多く読む割り先に `R` を残した。src では `R` の意味がファイルごとに違う形を作らない)。8 本とも元の別名は `R`(下線つきの名は無かった)・足した名とぶつかる名は 0。
- 名 → 割り先は本物の表(`map.toml` の `engine/resolve.py` の行の `names`=131 名・`names_complete`)。表に無い名は、道具の再輸出の割り先(主な割り先が先)。8 本で読む名は全部が表に在った(再輸出の名を読む所は 0)。
- import の文の置き場は変えない(8 本とも頂上の 1 文を、別名の数だけの文に置き換えた)。上に注 1 行(長い 2 本は「・」で 2 行に折った)。5b の G1 の `calendar_self.py` の注(`_CS`・`_CR`)と同じ形。

### 7-2. 直した 8 本(別名・割り先・読みの数)

| ファイル(元の import の行) | 別名の数 | 別名=割り先(読みの数: 読む名) | 読みの数 |
|---|---:|---|---:|
| `src/shibuya/interim_bundles/calendar_self.py:89` | 4 | `R_ACT_CODES`=foundation/vocab/act_codes(3: `EXIT_WALK_FLAG` 3)<br>`R_PLAN`=act/ops/plan_writes(6: `begin_exit_walk`・`begin_walk_to`・`set_plan_state` 4)<br>`R_RAIL`=act/ops/rail(2: `rail_arrive`・`rail_depart`)<br>`R_SHOP`=act/ops/shop(2: `balk_queue`・`release_indoor`) | 13 |
| `src/shibuya/mind/relations/layer.py:83` | 2 | `R_ACT_CODES`=foundation/vocab/act_codes(1: `TALK_OPEN_METERS`)<br>`R_MIND`=mind/ops(3: `write_relations` 3) | 4 |
| `src/shibuya/runtime/systems/assemble.py:38` | 5 | `R_BODY`=act/ops/body_writes(1: `initialize_energy`)<br>`R_INIT`=act/ops/init_writes(2: `initialize`・`set_initial_activity`)<br>`R_MIND`=mind/ops(2: `normalized_refractory_scale`・`refractory_ticks`)<br>`R_MOVE`=act/ops/move(1: `nav_place`)<br>`R_RESTORE`=runtime/state/restore(2: `restore_items`・`restore_soa`) | 8 |
| `src/shibuya/runtime/systems/body.py:20` | 2 | `R_BODY`=act/ops/body_writes(4: `advance_body`・`energy_home_meal`・`energy_out_of_area_meal` 2)<br>`R_PLAN`=act/ops/plan_writes(2: `begin_planned_sleep`・`wake_from_plan`) | 6 |
| `src/shibuya/runtime/systems/judge.py:27` | 2 | `R_MIND`=mind/ops(1: `clear_refractory`)<br>`R_TALK`=act/ops/talk(属性の読み 0・素の使い方 1=`_settle_pending_invites` へ渡す) | 1 + 素 1 |
| `src/shibuya/runtime/systems/perceive.py:18` | 2 | `R_DETECT`=act/ops/detect_writes(1: `write_b4_hash`)<br>`R_MIND`=mind/ops(1: `write_intero_stages`) | 2 |
| `src/shibuya/runtime/systems/talk.py:27` | 2 | `R_ACT_CODES`=foundation/vocab/act_codes(1: `TALK_LEAVE_METERS`)<br>`R_TALK`=act/ops/talk(6: `end_conversation` 2・`join_conversation`・`set_conversing`・`talk_within_reach` 2) | 7 |
| `src/shibuya/world/laws/presence.py:99` | 4 | `R_ACT_CODES`=foundation/vocab/act_codes(3: `EXIT_WALK_FLAG` 3)<br>`R_PLAN`=act/ops/plan_writes(16: `begin_exit_walk`・`begin_planned_sleep`・`clear_board_intent`・`set_plan_state` 12・`wake_from_plan`)<br>`R_RAIL`=act/ops/rail(7: `place_at_external` 2・`rail_arrive` 2・`rail_depart` 3)<br>`R_SHOP`=act/ops/shop(2: `balk_queue`・`release_indoor`) | 28 |

- 計: 別名 23・属性の読み 69・素の使い方 1(`judge.py`)。
- 足した行で 120 字を超えるのは無い。名を替えた行で 120 字を超えたのが 1 行(`calendar_self.py` の `R_PLAN.begin_exit_walk(…)`=122 字)。src には前から 120 字を超える行が 263 行あり、字数を見る検査は無いので、折らずに残した(名を替えるだけの差にとどめた)。

### 7-3. 差し替えが届く形(試験が差し替える名を、定義の割り先の別名の属性で読む)

| 名(定義の割り先) | 試験の差し替え | 読む src の行(直した後) | 別名 |
|---|---|---|---|
| `advance_body`(act/ops/body_writes) | 7 か所(`discard_probe.py:180` ほか=§5-3) | `runtime/systems/body.py:38` | `R_BODY` |
| `energy_out_of_area_meal`(act/ops/body_writes) | `test_meal_bundle_2b.py:488・492` | `runtime/systems/body.py:46・52` | `R_BODY` |
| `initialize`(act/ops/init_writes) | `test_resume_10d.py:308` | `runtime/systems/assemble.py:780` | `R_INIT` |
| `set_conversing`(act/ops/talk) | `proximity/test_runs.py` | `runtime/systems/talk.py:179`(`runtime/run.py` の読みは 1 つの割り先だけ=道具が機械で直す) | `R_TALK` |〔検収の低-1・親が正した〕`runtime/run.py` の `R.set_conversing` は、頂上の別名でなく、`_settle_pending_invites` の引数 `R` を通る読み(頂上の別名 `R` が読むのは `_UNADDRESSABLE` と `talk_within_reach` だけ)。割った後に試験の差し替えがこの読みへ届くかは、`judge.py` の `R_TALK` を talk へ向ける宣言で決まる(届く先が talk であることは同じ)。
| `join_conversation`(act/ops/talk) | `proximity/test_runs.py` | `runtime/systems/talk.py:141` | `R_TALK` |
| `write_relations`(mind/ops) | `memory/test_m4_m5_people.py` | `mind/relations/layer.py:258・331・644` | `R_MIND` |

- `discard_to_bin`(`world/laws/goods_flow.py`)・`request_open_close`(`interim_bundles/duties/layer.py`・`world/laws/opening.py`)・`apply`(`runtime/systems/act.py`)を読む src は、1 つの割り先だけを読む=この 8 本の外で、道具が機械で直す(変えていない)。
- 書かない実行の差し替えの届く先の守り(E5-b)は、直す前も後も、確かめた 13・見られなかった 2(`tools/c7` の 2=道具の側の宣言の分)・読み込みの時だけの読み 0 で同じ。src の 8 本で、差し替える名を名の import で持つ所・読み込みの時に読む所は 0。

### 7-4. 素の使い方・関数の中の import など

- `runtime/systems/judge.py:163`: 別名を `runtime/run.py` の `_settle_pending_invites(…, R_TALK, np, …)` へ渡す。渡した先で別名の属性として読むのは talk の 4 名(`end_conversation`・`revert_conversation`・`set_conversing`・`talk_within_reach`=今の木の AST で確かめた。別名をほかへ渡す所は無い)=talk の別名 `R_TALK` を渡した。この 1 つは、別名を分けても手で直す一覧に残る(素の使い方)。道具の側の宣言(「素で使ってよい別名」の印・親の裁定 T5)で通す。
- ほかの素の使い方(返す・しまう・既定の引数・デコレータ)は、8 本で 0。
- 関数の中の import・`TYPE_CHECKING` の中の import・注釈だけで使う別名は、8 本で 0(8 本とも頂上の import 1 つ・読みは全部が関数の中の属性の読み・頂上やクラスの本体で読み込みの時に読む所も 0)。
- docstring と注の中の `R.名` の言及は、8 本で 0(直す注は無かった)。

### 7-5. 確かめ

| 何を | 結果 |
|---|---|
| AST(足した別名を元の `R` へ戻し、重なった `from shibuya.engine import resolve as R` を 1 つにする) | 8 本とも土台 `e543f3b` の版と AST が同じ。8 本で `R` の名を読む所は 0 |
| 書かない実行(本物の表・`split --through engine/resolve.py`) | 手で直す一覧 13 → **6**(src は `runtime/systems/judge.py:29` の `R_TALK` の 1 つだけ=素の使い方・試験 2・`tools/c7` 2・`guide_permits.py::RESOLVE_FILE` 1)。守りは前も後も全部「同じ」(決まりは宣言どおり 4)・止めた理由 0。道具が書く 22 の別名の import は、どれも狙いの割り先のモジュール(例 `from shibuya.act.ops import plan_writes as R_PLAN`) |
| E5-b(差し替えの届く先) | 前 確かめた 13・見られなかった 2 → 後 13・2(同じ) |
| 狙いの試験の束(`tests/engine` の直下と `systems`・`state`・`body`・`clock`・`proximity`・`rights`・`processes`・`memory`・`tests/economy`・`tests/tools`・`-m "not gpu and not slow"`・`-n 2`・合図を取って) | 前 3,471 passed・22 skipped・0 failed → 後 3,471 passed・22 skipped・0 failed(passed のノードの一覧も、飛んだ理由の行も前と同じ。飛ぶ 22 本は `tests/tools/test_pkgmove.py` ほかの前からの分=段 4 と割る段の済んだ木) |
| `lint-imports`(作業木の src) | 前も後も 11 kept・0 broken(出力が同じ) |
| `cli.py map --check` | 前も後も「同じ」 |
| `cli.py contracts --stage delete --tree . --check --probe` | 前も後も「同じ」・例外 20 辺・延べ 26 行・効かない例外 0(報告の JSON が前と同じ) |
| byte-check 19 構成(基準 `e543f3b`・記録 [bytecheck_G1a/](bytecheck_G1a/)・合図を取って) | 37 欄すべて同じ 19・動いた 0・誤り 0・final が同じ 19・434 秒(基準の側 222 秒・比べる側 211 秒)。既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939 |
| カード | 作り直して変わらない(`data.md` は単独で戻した・`--check` 最新) |
| 秘密の走査 | CLEAN(直した src の 8 本と、この記録) |

- この節の台本(親の scratch に置いた・リポには入れていない): 頂上の別名を割り先ごとに分ける台本(名 → 割り先は本物の表から引く・素の使い方は割り先を名指しする)・足した別名を元へ戻して土台の版と AST を比べる台本。

### 7-6. 見立てと違った所・確かめていないこと

- 見立てと違った所: 無い。8 本・素の使い方 1(`judge.py`)・書かない実行の 13 → 6 は発注の見込みのとおり。計画 §7-1 の割り先の数(`presence.py` 4・`calendar_self.py` 4・`assemble.py` 5・`body.py` 2・`perceive.py` 2・`talk.py` 2・`layer.py` 2・`judge.py` は mind/ops+渡す talk)とも同じ。
- 確かめていないこと: 範囲の全体の試験(親が回す)。割った後の振る舞い(2 つ目の commit=道具で写す)と、差し替えを外すと落ちる確かめ(親の決め事 4=割った後に 1 つずつ)。`tests/c7`(開いていない)。

## 8. S6-G1 の下ごしらえ(src の別名の分け)の、親の確かめと検収(第347・2026-11-19)

### 8-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 1・知らせ 1)。検収役はファイルを 1 本も変えていない。
- 挙動: 足した別名を元の `R` に畳むと、8 本とも土台 `e543f3b` と AST が同じ。import は土台の頂上の 1 文と同じ位置に続けて並ぶ(関数の中・`TYPE_CHECKING` の中の import は 0)。足した文は全部同じモジュールを読むので、最初の 1 文で読み込みが済み、副作用の順は変わらない。docstring とつなぎの台帳の宣言も前後で同じ。
- 別名ごとの割り先: 本物の表(`map.toml`・131 名)で見て、23 の別名のどれも 1 つの割り先だけを読む。2 つ以上の割り先・表に無い名・再輸出の名の読みは 0・元の `R` も残っていない。別名の名は試験の側の表(§5-1)と同じ。src の全部で resolve の別名を持つ 28 本で見ても、2 つ以上の割り先を読む別名は 0。
- 差し替えが届く形: 試験が差し替える 9 つの名とも、src が読む別名の割り先・名の定義の割り先・試験が差し替える別名の割り先の 3 つがそろう(`advance_body`・`energy_out_of_area_meal` → `R_BODY`・`initialize` → `R_INIT`・`set_conversing`・`join_conversation` → `R_TALK`・`write_relations` → `R_MIND`。`discard_to_bin`・`request_open_close`・`apply` は、8 本の外の 1 つの割り先だけを読む別名=道具が属性の読みのまま正しい割り先へ書き換える)。
- 素の使い方: `judge.py` の `R_TALK` の 1 つだけ。`_settle_pending_invites` の中で読むのは talk の 4 名だけで、ほかへ渡す所は無い。
- 書かない実行(検収役がメモリの中で 1 回): 守りは全部「同じ」(決まりは宣言どおり 4)・手で直す一覧は 6(src は `judge.py` の 1 つ・試験 2・`tools/c7` 2・`guide_permits` 1)・22 の別名は狙いの割り先のモジュールへ書き換わる。`contracts --check --probe` は前と同じ(例外 20 辺・延べ 26 行)。

### 8-2. 検収の低と知らせ・親の答え

- 低-1(§7-3 の `set_conversing` の行の読み方の誤り): 親が §7-3 の行に注を足して正した。`judge.py` の宣言の「渡した先で読む名」には、`set_conversing` を含む 4 名を書く(道具の側の次の commit)。
- 知らせ(割った後の `runtime/systems/talk.py` は、`act_codes` を 2 つの別名で持つ=挙動は同じ): 段 8 の掃除の候補。
- 実装役の問い(名を替えた行の 1 つが 122 字になった): 折らない(名を替えるだけの差にとどめる。src には前から 120 字を超える行が在り、字数を見る検査は無い)。
- 検収役の手順の注: 差分の写しを 1 回、リポの外の一時の置き場に書き、すぐ消した。

### 8-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| byte-check 19 構成(本体の道具・基準 `e543f3b`・src の別名の分けの木) | 37 欄すべて同じ 19・動いた 0・誤り 0・440 秒・既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。記録 [bytecheck_G1a_parent/](bytecheck_G1a_parent/)(実装役の記録は [bytecheck_G1a/](bytecheck_G1a/)=434 秒) |
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`。回している間、この作業木は誰にも編集させていない) | 7,044 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・22 skipped・1 xfailed・40 分 06 秒。前の回(別名の分け・7,043 passed・2 failed)から、親の段取りで落ちていた 1 本が通って +1(試験は足していない) |
| src の差分を読んだ(3 本) | 別名は割り先ごとに 1 つ・属性の読みのまま・`judge.py` は talk の別名を渡す・`perceive.py` は `R_DETECT.write_b4_hash`・`R_MIND.write_intero_stages` |

## 9. S6-G1 の写し(23 本目 `engine/resolve.py` を 18 の割り先へ・土台 `4a5bd30`・安定版のタグ `stable-v2-before-split6-G1`・2026-11-19)

道具(`tools/pkgmove/cli.py split --next --apply --tree .`)で `engine/resolve.py` を 18 の割り先へ写し、読み手の import を書き換えた。包み `engine` は木から消えた。手で直したのは道具の一覧の外の 3 つ(裁定 Q4・取り直し §12)と、割った結果として落ちた試験 2 本(親の裁定)だけ。`tools/pkgmove/`・`tools/bytecheck/`・全ファイルの表・`map.toml`・`contracts.toml` は変えていない(`pyproject.toml` は `contracts --apply` が書いた)。

### 9-1. 本の数

| 本 | 割る行 | 書き換えた import の文(src・tests・tools・docs) | 分けた文 | 鍵 | 台帳の道 | 前向きの表 | 道の文字列 | 書き換えなかった鍵 | 手で直した読み | 別名の割り先の宣言 | 写さなかった | 守り | byte-check | 契約 | 例外 載せた・効いている(辺/行) |
|---:|---|---|---:|---:|---:|---:|---|---:|---|---:|---|---|---|---|---|
| 23 | `engine/resolve.py` | 166(43・119・3・1)=ファイル 88(28・56・3・1) | 0 | 1 | 1 | 2 行 | src の表 2(E8 の宣言)・コードの文字列 7・斜線の道 1 | 11 | 0(src の 8 本は §7・試験と tools は §5) | 印のある宣言 5(`judge.py`・試験 2・`tools/c7` 2) | 再輸出 4 名(裁定 Q7)・import 1 文と注 8 行(下) | 13 個「同じ」(決まりは宣言どおり 4) | 19/19 同じ(434 秒) | 1+10 | 16/18・16/18 |

- 割り先と名の数(道具の数え): `act/apply.py` 18・`act/ops/shop.py` 20・`act/ops/rail.py` 13・`act/ops/move.py` 10・`act/ops/plan_writes.py` 6・`mind/ops.py` 10・`act/ops/law_writes.py` 8・`act/ops/body_writes.py` 7・`act/gate.py` 3・`act/ops/talk.py` 8・`runtime/state/restore.py` 4・`act/ops/intent_writes.py` 9・`act/ops/focus.py` 7・`act/ops/init_writes.py` 2・`foundation/write_guard.py` 1・`act/ops/detect_writes.py` 1・`foundation/vocab/act_codes.py` 3・`foundation/vocab/agent_codes.py` 2(表の名は `_REFRACTORY_TICKS` の 1 つ。道具の数えは、旗の代入の文の束縛も数えて 2)。新しく作った割り先 15・在るファイルへ足した割り先 3(write_guard と語彙の 2 本)・作った頭 `act/ops/__init__.py`・消したファイル `engine/resolve.py`・`engine/__init__.py`。道具が書いたファイル 112・消したファイル 2。
- 当てる前の書かない実行(`split --next`)は、親と検収役が確かめた姿と全部同じだった: 手で直す一覧 0・見られなかった差し替え 0・差し替えの届く先は確かめた 13・宣言で確かめた 2(`tools/c7` の 2 本の `apply`)・使われた宣言は印のある別名の宣言 5 と道の文字列の宣言 2(`ledger.py::_ALLOW_REVENUE` → shop・`ledger_ast.py::ext_reason` → restore)・前向きの表に 2 行(`act/ops/plan_writes.py`・`mind/ops.py` → `engine/resolve.py`)。
- 写さなかった物(道具の `unwritten`): 体の層へ移した値の import 1 文(`world.body.rules` の 4 名=再輸出・裁定 Q7)とその中の注 1 行、`__all__` の中の区切りの注 7 行(`__all__` は割り先ごとに作り直した)。割り先の docstring と注に残る古い名(`engine.resolve` など)は直していない(段 8 の文の掃除)。
- 契約(`contracts --stage delete --tree . --apply`・`pyproject.toml` +19・−21 行): 古い層の決まり(`layers: census > economy > engine > …`)が消え、決まり 4 の契約(`act.apply`・`act.ops` を読めるのは act・world.laws・interim_bundles・runtime・interfaces だけ)が入った=古い 2+新しい 9 → 古い 1+新しい 10。例外は 12 行(8 辺)が消え、4 行(割 5〜8=`act.ops.detect_writes → mind.system1.change_detect`・`mind.ops → world.model.agent_table`・`runtime.state.restore → world.model.agent_table`・`runtime.state.restore → world.model.state`)が載った=26 行・20 辺 → 18 行・16 辺。効かない例外 0。計画に無い契約と例外は要らなかった。

### 9-2. 当てた直後の import の確かめで止まった(発注の手順の順の誤り)と、回し直し

- 当てた直後の道具の import の確かめ: モジュール 386 のうち 2 つが落ちた(終了コード 3)=`shibuya.runtime.systems.table` と `shibuya.validation.static.system_overrides`(`table` を import する)。どちらも `FileNotFoundError`(`engine/resolve.py` が無い)。`table.py` が import の時に系の表を作り(`spec.make` → `allow.writes_for_ops` → `allow.index()`)、`allow.py` の `RESOLVE_FILES` が割る前のファイル `engine/resolve.py` を指したままだった。`python -m shibuya.cli --help`・`python -m shibuya.interfaces.cli.run_args --help` は終了コード 0。
- 取り直し §5 が「`RESOLVE_FILES` は道具が書き換えない・書き換えないと `allow.index` が無いファイルを読んで落ちる」と見込んでいたのに、発注の手順が import の確かめ(手順 2)を手直し(手順 3)の前に置いていた=親の書き誤り(親の裁定)。木は土台に戻さず、書いたままの木で手直し 1(§9-3)を先に当て、道具の同じ確かめ(`cli.py importcheck --tree .`)を回し直した: モジュール 386・落ちた 0・`--help` 2 つとも終了コード 0。2 つの確かめの出力は [importcheck_G1/](importcheck_G1/)(作業の木の絶対の道は伏せた)。

### 9-3. 手で直した所と、直した試験

道具の一覧の外の 3 つ(取り直し §12・表と順の検収の低-1):

| 所 | 直し | 確かめ |
|---|---|---|
| `src/shibuya/runtime/systems/allow.py` の `RESOLVE_FILES` | 書き手の 15 本(字の順)。すぐ上の注を合わせた | 割り先 18 のうち、resolve から来た関数を頂上に持つのは 16 本=15 本と `foundation/write_guard.py`(来た関数は `_require_thawed` だけ=裁定 Q4 で除く 1 つ)。語彙の 2 本は resolve から来た関数 0。15 本は「18 から write_guard と語彙の 2 本を引いた物」とちょうど同じ |
| `tests/economy/cp2/money_writers_frozen.json` の 4 行 | `path` だけ: `initialize` → `act/ops/init_writes.py`・`_board_riders` → `act/ops/rail.py`・`_complete_buy`・`_complete_eat` → `act/ops/shop.py` | ほかの欄(関数・列・種類・わけ)は 1 字も変えていない(読んで比べた) |
| `tests/engine/state/mind_world_reads_frozen.json` の `scope.split` | resolve の項を外した(`perception/renderer.py` の項は残る) | ファイルは `json.dumps(indent=1)` の形のまま。`key_counts` は 83・`totals` は 83・72 のまま |

割った結果として落ちた試験(親の裁定で直した・直す前と後で、そのファイルの同じノードが、この 1 本のほかは同じ):

| 試験 | 行 | 前 | 後 | わけ | 元の数・中身を残した形 |
|---|---|---|---|---|---|
| `tests/engine/bridging/test_bridging_ledger.py::test_the_counts_by_form` | 169 | 見出しの宣言を持つ今のファイル 81 | 83 | resolve の見出しの宣言 4 つが 3 つの割り先へ分かれた(`act/apply.py` 6 項・`mind/ops.py` 0 項と 1 項・`act/ops/plan_writes.py` 2 項)。宣言の数(見出し 84)・項の数(367)・台帳は同じ | **台帳の道で数えた数 == 81** を足して固定した(助け `_heading_ledger_paths`=`ledger_path()` に通した道の集合)。負の対照の試験を 1 本足した(`test_negative_a_dropped_forward_row_changes_the_heading_ledger_count`=前向きの表のどちらの行を一時に落としても 82 になる)。ファイル: 43 passed・1 failed → 45 passed |
| `tests/engine/test_state_checks_10f.py::test_t4_axis1_collision_needs_the_owner_receiver` | 119 | 写しの木の `engine/fake_collision.py` に偽のファイルを書く | `act/fake_collision.py` | 包み `engine` が木から消えて `FileNotFoundError`(数の固定ではない・道具は `/` の結合の `"engine"` を移すファイルの道とみなさないので一覧に出なかった) | 置き場の字面だけを替えた(注 1 行)。2 つの確かめ(衝突 1 件で `n_calls_total`・限界の行 `fake_collision.py:3`)は同じ。置き場を `act`・`act/ops`・`runtime`・`mind` にした写しの台本でも通る。ファイル: 23 passed・1 failed → 24 passed |

- 同じ形の洗い(写した木や一時の木の中の `engine` の置き場に、ファイルを書く・読む・在ることを前提にする試験): `tests`(`c7` を除くディレクトリを名指し)と `tools`(`c7` を除く)を AST で洗った(`/` の連鎖の `"engine"`・`os.path.join`/`Path`/`joinpath` の `"engine"`・`engine/` を含む文字列)。641 ファイル・416 か所。ファイルを書く・読む形は 16 か所(6 ファイル)で、どれも一時の置き場に自分で `engine` を作ってから書く(`test_mr65_guards`・`test_rate_rules_1101`・`test_move_prep_stage2` の偽の木・`test_state_ledger_10b`・`test_bytecheck` の 2 か所)=束で通っている。束の外の当たりは、docstring・注・合成の場所の名札・元の道を鍵に使う表(`PL.split_files("engine/run.py", …)`・`tools/c8/c8lib.py` の元の置き場の引き)だけで、`engine` の置き場を前提にファイルを書く・読む所は 0。
- 残した古い名(名札・ファイルを書かない): `tests/engine/test_state_checks_10f.py` の 348 行 `"engine/fake.py"`(合成の場所の名札)。

### 9-4. 凍結の表と書きの許可の比べ

| もの | 結果 |
|---|---|
| `tests/engine/systems/test_resolve_index_frozen.py`(書きの許可の索引の凍結) | passed。`resolve_index_frozen.json` は 1 字も変えていない(関数の集合・直接の書き・辺・表・帳簿の口・別名の書きが割る前と同じ) |
| `writes_soa_frozen.json`(36 系の書きの集合・`test_systems_table`・`test_fix_guards`・`test_e_writes_declared`・`test_detection_writes_split`) | passed・JSON は 1 字も変えていない |
| `tests/engine/state/test_move_prep_stage2.py`(書き手の一覧の固定) | passed |
| `tests/engine/bridging/test_bridging_ledger.py`(前向きの表の 2 行・載った道のファイルに宣言が在る・台帳の JSON は 1 字も変わらない) | §9-3 の 1 本を直して 45 passed(足した負の対照 1 を含む) |
| クラスの名の固定の表(`test_class_ids`)・名の凍結(`test_names_frozen`)・心の読みの表(`test_mind_world_reads`)・`tests/economy/cp2` | passed(クラスの名の鍵 1=`ResolveOutcome` → `act.gate`・値は凍結の名のまま) |

### 9-5. 差し替えの「外すと落ちる」(親の決め事 4・5b の G3 と同じ)

確かめに使った書き換えは、1 か所ずつ一時に書き換えて試験を回し、同じ台本の中でバイトを戻した(sha256 で確かめた)。毎回、別のコマンドで `git diff` と `git status --porcelain` の指紋が確かめの前と同じことを見た。書き換える前に、狙いの試験のノードを書き換えずに回して通ることを確かめた(落ちたのは前からの 1 本だけ=§9-10)。

| # | 差し替え(当てた後の行・別名の割り先) | 外したとき(行を `pass` に) | 結果 |
|---:|---|---|---|
| 1 | `discard_probe.py:180` `advance_body`(body_writes) | `test_state_checks_10f::test_t4_axis2_required_made_discardable_fails` | **落ちる** |
| 2 | `test_resume_10d.py:308` `initialize`(`R_INIT`=init_writes) | 同じ名の試験 | **落ちる**(`initialize` の数え 0 ≠ 1) |
| 3 | `test_resume_10d.py:623` `advance_body`(body_writes) | `test_named_closed_memo_survives_a_resume` | **落ちる**(控え 0) |
| 4 | `test_resume_10d.py:633` `advance_body` を元へ戻す行 | 同じ | 落ちない=**元へ戻す行**(差し替えではなく後片付け。再開のランは 600 から=控えを入れる tick 599 を通らない。外しても落ちないのが正しい) |
| 5 | `test_sim_time_T.py:221` `advance_body` | `test_no_negative_elapsed_time_in_any_tick_column_every_tick` | **落ちる** |
| 6 | `test_state_checks_10f.py:439` `advance_body` | `test_t5_runtime_fifth_word_caller_fails` | **落ちる**(`KeyError`) |
| 7 | `test_state_ledger_10b.py:682` `advance_body`(`RES`) | `test_t5_weight_kg_is_read_only_at_initialization`・`test_t5_perturbing_no_columns_changes_nothing` の 2 形 | **落ちる**(3 本とも) |
| 8 | `test_removed_switches_346.py:120` コードの文字列の `R.advance_body = _stop` | `test_the_frame_check_catches_a_stop_inside_the_ticks` | **落ちる**(123 行の assert) |
| 9 | `test_meal_bundle_2b.py:488` `energy_out_of_area_meal = spy`(属性への代入) | `test_run_wiring_defaults_are_old_and_switches_reach_the_run` | **落ちる** |
| 10 | `test_meal_bundle_2b.py:492` 元へ戻す行(`finally`) | 同じ | 落ちない=**元へ戻す行**(後片付け。外しても落ちないのが正しい) |
| 11 | `duties/test_du_runs.py:275` `discard_to_bin`(law_writes) | `test_discard_is_a_closing_task_and_the_morning_bridge_skips_it` | **落ちる** |
| 12 | `rights/test_no_permission_count.py:86` `request_open_close`(law_writes) | `test_live_count_is_zero_or_marked` | 落ちない(下) |
| 13 | `proximity/test_runs.py:126` `set_conversing`(talk) | `test_sensitivity_arms_keep_every_conversation_within_their_d`(slow・2 形) | **落ちる**(`open` 0) |
| 14 | `proximity/test_runs.py:127` `join_conversation`(talk) | 同じ | 落ちない(下) |
| 15 | `memory/test_m4_m5_people.py:149` `write_relations`(mind/ops) | `test_people_arm_run_never_writes_the_relation_table` | **落ちる** |
| 16 | 宣言で通した素の使い方: `src/shibuya/runtime/systems/judge.py:163` の渡す別名 `R_TALK` を `R_MIND` に | `tests/engine/test_conversation_invite.py`(not slow) | **落ちる**(`runtime/run.py:605` で `mind.ops` に `talk_within_reach` が無い) |
| 17 | 同: `test_conversation_invite.py:310` の `R_TALK` を `R`(init_writes)に | 同じファイル | **落ちる**(5 本) |
| 18 | 同: `test_defect_fixes_1103.py:335` の `R_TALK` を `R`(act/apply)に(同じ形 5 か所の 1 つ) | 同じファイル | **落ちる**(4 形) |

- **割る前からの試験の弱さ**(割る段の違いではない・直していない): 12 と 14 は、試験が差し替えた物の呼ばれた数を合否に使っていない。12 の `roc` は数えて印(▲ の警告)を出すだけ・200 体の既定の構成では開閉の口を通らない(差し替えを `None` にしても落ちない)。14 の `join` は `join_bad == []` だけを見る・本物のランで一度も呼ばれない(`_recorded_run` の 1,500 体で join 0・5,000 体 d=2.5 で join 0)。土台 `4a5bd30` との差はどちらのファイルも import の 1 行だけで、数を見る行は割る前から無い=土台でも同じ行を外して落ちない【見立て=字面の比べ。world の data が要る試験なので土台の写しでは回していない】。
- 届く先: 道具の守り(差し替えの届く先)が字面で、12 は law_writes・14 は talk と確かめた。12 は、店の仕事の腕 on の合成のラン(`test_du_runs` の day_run と同じ組み立て)で `act.ops.law_writes.request_open_close` を数える包みに差し替えると src から 2 回呼ばれ、置かない回は 0。14 は、同じ別名 `R_TALK` の属性で読む `set_conversing` の包みが通る(35 回・172 回)。
- `tools/c7` の 2 本(`apply` を包む・宣言で確かめた 2): 手元では確かめられない(`tests/c7` は開かない・回さない=CI で回る)。

### 9-6. 読み込みの閉包(5b の G2・G3 と同じ見方)

- 割る前の `resolve.py` の頂上で読み込みの時に走る文: `assert` 5 と書き込みの旗の代入 1。割った後、`assert` 4 は `act/apply.py`(510・515・535・557 行)、`assert` 1 と旗の代入は `foundation/vocab/agent_codes.py`(305・306 行)の頂上に同じ文で在る。環境変数の読み・`stop_if_set`・登録は無い。
- 閉包(環境変数なしで別のプロセスで import した後の `sys.modules` の shibuya の分):

| 割り先 | 閉包 | 土台の `import shibuya.engine.resolve`(47)から読み込まれなくなる | そのうち頂上に作用のある文を持つ |
|---|---:|---:|---|
| `act/apply`・`act/ops/shop`・`act/ops/talk` | 49〜54 | 2 | — |
| `act/ops/rail`・`move`・`plan_writes` | 42〜44 | 6 | `world.body.energy`(環境変数を読んで raise) |
| `mind/ops`・`act/gate`・`act/ops/detect_writes` | 38〜39 | 8〜9 | `foundation.vocab.actions`(assert)・`world.body.energy` |
| `act/ops/law_writes`・`intent_writes`・`runtime/state/restore` | 22〜25 | 23〜26 | `foundation.text.templates`(assert)・`world.body.energy`(・`foundation.vocab.actions`) |
| `act/ops/body_writes`・`init_writes` | 20〜27 | 20〜27 | `foundation.text.templates`・`foundation.vocab.actions` |
| `act/ops/focus`・`foundation/write_guard`・語彙 2 本 | 4〜9 | 38〜42 | `templates`・`actions`・`agent_codes`(assert)・`foundation.write_permit`(環境変数を読む)・`energy` |

- 18 の割り先の閉包の和は、土台の閉包を全部含む(抜けるモジュール 0)。入口とランの組み立て: `interfaces.cli.main`(162 → 173)・`runtime.systems.assemble`(151 → 162)・`runtime.run`(138 → 149)・`interfaces.cli.run_args`(145 → 156)とも、名の付け替え(`engine`・`engine.resolve` → 新しい割り先 15 と `act.ops`)のほかは同じ集合。合成の世界の小さなラン 1 本が読み込むモジュールも、名の付け替えのほか同じ(土台 236 → 250・新しい 16 本を全部読む)。
- 環境変数を置いた前後の比べ(`SHIBUYA_MEAL_DEFAULT=zz_invalid`=消した切替口。止める文は `world/body/energy.py` の頂上にだけ在り、ランの組み立ての `check_environment` の一覧には無い。終了コード 1=止まる):

| 読むもの | 土台 | 後 |
|---|---|---|
| `import shibuya.engine.resolve`(土台)/ 割り先 `act/apply`・`act/ops/shop`・`act/ops/talk`・`act/ops/body_writes`・`act/ops/init_writes` を 1 本だけ import | 止まる | 止まる |
| 割り先 `act/ops/rail`・`move`・`plan_writes`・`law_writes`・`intent_writes`・`focus`・`detect_writes`・`act/gate`・`mind/ops`・`runtime/state/restore`・`foundation/write_guard`・`foundation/vocab/act_codes`・`agent_codes` を 1 本だけ import(13 形) | (土台の `import …resolve` は止まる) | **止まらない** |
| `python -m shibuya.cli --help` | 止まる | 止まる |
| `import shibuya.runtime.systems.assemble` | 止まる | 止まる |

- **止まらなくなる 13 形**(親の仮採用でそのまま=5b の G2・G3 と同じ扱い): 割り先を 1 本だけ import する形。入口(`-m shibuya.cli`)とランの組み立て(`assemble`)は前後とも止まり、ランは必ず `world.body.energy` を読み込む=正しい環境のランと byte-check には効かない。語彙の 2 本と write_guard は割る前から resolve を読まないファイル(1 本だけ読む読み手は前から止まらない)。`foundation.write_permit` の環境変数(`SHIBUYA_WRITE_GUARD`)の読みは、focus・語彙 2 本のどれかだけを読む形では後ろへずれる(読む時刻が変わるだけ・値は同じ)。

### 9-7. 試験・決まり・byte-check

| 何を | 結果 |
|---|---|
| 狙いの試験の束(`tests/engine` の直下と `systems`・`state`・`bridging`・`body`・`clock`・`proximity`・`rights`・`processes`・`memory`・`tests/economy`・`tests/tools`・`tests/test_places_guard.py`・道具が書き換えた試験でほかの置き場の 3 本=`tests/bench/test_refr20b_tool.py`・`tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/duties/test_du_runs.py`・`-m "not gpu and not slow"`・`-n 2`・合図を取って) | 3,621 passed・22 skipped・1 failed(§9-3 の `test_state_checks_10f` の 1 本=直した後にファイルを回し直して 24 passed)。飛んだ試験の行は割る前の束(§7)と同じ 22(data が要って飛んだ 0) |
| `tests/tools/test_pkgmove.py`(上の束の中) | 174 passed・21 skipped。飛ぶ試験は増えなかった(割る行が残り 0 の木でも書かない実行の試験が回る形=5b の §17-10 の直し 2) |
| `lint-imports`(作業木の src) | 11 kept・0 broken(古い 1+新しい 10) |
| `cli.py map --check` | 同じ |
| `cli.py contracts --stage delete --tree . --check --probe` | 同じ・例外 18 行・16 辺・効かない例外 0 |
| `cli.py split --next` | 「割る段は全部当たっている」(置き場にファイル 0) |
| **byte-check 19 構成**(基準 `4a5bd30`・記録 [bytecheck_G1/](bytecheck_G1/)・合図を取って) | **37 欄すべて同じ 19・動いた 0・誤り 0・434 秒**(基準の側 220 秒・比べる側 213 秒)。既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939(基準と同じ)。byte-check の後に直したのは試験 1 本だけ(src と道具は変えていない=`git status` で確かめた) |
| カード | 作り直した(`engine` のカードが消え `act/ops` のカードが増えた・`tests/c7` のカード 1 枚は道具が c7 の import を 1 行書き換えた結果=中身は見ていない)。`data.md` は単独で戻した・`--check` 最新 |

### 9-8. `tests/c7`

道具が書き換えたのは `tests/c7/test_attr_arms.py` の import の 1 行(+1・−1)だけ。道具は c7 の中で手で直す所を挙げなかった。中身は開いていない・回していない(CI で回る)。

### 9-9. 宣言する書きの例外(裁定 Q11)

- 再開の復元(`runtime/state/restore.py`=resolve から来た 4 名。`restore_soa`・`restore_items` ほか)は世界の欄を書く。CLAUDE.md §3 の「世界の欄を書く関数は行為の区分(act)だけが持つ」の例外として、ここに宣言する(書きの許可の一覧 `RESOLVE_FILES` には載る)。**宣言の正式な置き場(最終の表の例外の表か、要件の文書か)はユーザーの判断待ち**。

### 9-10. 計画・取り直しと違った所・前からの欠陥・親に聞くこと・確かめていないこと

- 計画・取り直しとの違い: 発注の手順の順(import の確かめ → 手直し)で import の確かめが 2 つ落ちた(§9-2=親の書き誤り・順を入れ替えて回し直した)。割った結果として落ちた試験が 2 本(§9-3=数の固定 1・偽のファイルの置き場 1)。道具の名の数えは agent_codes が 2(表は 1)。ほかは取り直し §4・§5・§7・§10 の見込みどおり(消える例外 8・載る例外 4・契約 1+10・包み `engine` が消える・差し替え 17 か所)。
- 前からの欠陥(割る段とは別・直していない・原因は追っていない): `tests/engine/test_conversation_invite.py::test_named_target_drives_invites_end_to_end`(slow)が `assert c["conv_fallback_same_batch"] > 0` で落ちる。土台 `4a5bd30` の src と試験(と、試験が読む `docs` の 2 つと祝日の fixture)を作業の外の置き場へ書き出し、土台の src で回しても同じ assert で落ちた。
- 確かめていないこと: 範囲の全体の試験(親が回す)・`tests/c7`・12 と 14 を土台で外して落ちないこと(見立て)。

## 10. S6-G1 の写しの、親の確かめと検収(第347・2026-11-19)

### 10-1. 別の役の検収(2 人に分けた=道具の出力と決まりの側・意味の側)

どちらの検収役も、ファイルを 1 本も変えていない。

- **道具の出力と決まりの側: 受入**(高 0・中 0・低 2=どちらも知らせ)。
  - 当て直しと一致: 土台 `4a5bd30` をメモリに読み、今の道具と表で 23 本目を厳しい当てで当て直した。守り 13 項は全部「同じ」・手で直す 0・見られなかった差し替え 0。できた木と作業木で違う `.py` は 3 本だけ(`allow.py` の `RESOLVE_FILES`・`test_bridging_ledger.py`・`test_state_checks_10f.py`)で、どれも発注と親の裁定の中身どおり。`.py` の外で変わったのは、凍結の JSON 2 本・`pyproject.toml`・記録・カード・`tests/c7` の道 1 本だけ。割る道具・byte-check の道具・全ファイルの表・`map.toml`・`contracts.toml`・つなぎの台帳の JSON は差 0。
  - 写しの字面: 元の頂上の文 137(import・docstring・`__all__` を除く)は、どれも 18 の割り先のどれか 1 つの頂上に、AST が同じ文でちょうど 1 回在る。頂上の名 131 は全部、表の割り先で定義される。既に在った割り先 3 本は足した行だけ(消した行 0)。
  - `engine` の包み: 置き場は消えた。`shibuya.engine` を import する文・実行の時に名で読む文字列(`import_module`・差し替えの的・`-m` の引数)は 0。
  - import の決まり: `contracts --check --probe` を検収役が回して「同じ」(古い 1+新しい 10・例外 18 行・16 辺・効かない 0)。消えた例外は 8 本・載ったのは割 5〜8 の 4 本。`pyproject.toml` の差分はこの結果と合う。
  - 台帳と凍結の値: `LEDGER_PATHS` に 1 行・`LEDGER_PATHS_SPLIT` に 2 行。宣言の走査の同定の集合は割る前と同じ。凍結の JSON 4 本は差 0・クラスの名の鍵は 1 つだけ変わり値は同じ。
  - byte-check の記録(実装役の分と親の分): 比べる側は `engine/resolve.py` を読まず、割り先 16 本を読んで走った。記録の src の sha 276 本は、今の木と同じ。
- **意味の側: 受入**(高 0・中 0・低 2・手順の知らせ 1)。
  - 差し替え: 試験と tools の差し替えを全部洗った。割り先のモジュールを差し替えるのは 17 か所で、どれも、差し替えるモジュールが、src がその名を呼ぶ時に引くモジュールと同じ(空振り 0)。素で渡す `R_TALK` は talk で、渡した先が読む 4 名は talk に全部在る。検収役も 2 か所(`write_relations`・`advance_body`)、差し替えの行をメモリの中で外して回し、元は通り、外すと落ちることを確かめた。
  - 落ちない 4 か所(§9-5): 2 つは元へ戻す後片付けの行。残る 2 つ(`request_open_close`・`join_conversation`)は、試験のコードに、差し替えた包みの数えを合否に使う assert が無い(警告と `join_bad == []` だけ)。土台との差は import の 1 行だけなので、割る前から落ちない(字面で言える)。
  - 読み込みの時に走る文と閉包: `assert` 5 と旗の代入は、割り先の頂上に同じ字面で在る。入口とランの組み立て 6 つの読み込みの集合は、`engine`・`engine.resolve` が割り先に替わったほかは同じ(抜け 0・増え 0)。消した切替口の環境変数を置くと、入口 4 つは前後とも同じ誤りで止まる。割り先を 1 本だけ読む形が止まらなくなることは、§9-6 の表と合う。
  - 書きの許可の索引: 凍結の索引の試験 6 本は通り、JSON は変わっていない。`RESOLVE_FILES` の 15 本は、resolve の関数を持つ割り先 16 本から `write_guard` を除いた物とちょうど同じ。静的な検査の `RESOLVE_MODULES` は 15 で、36 系とも割る前と同じ(呼び出し・`resolve_ops`・`writes.soa`)。
  - 試験の範囲: 割る前に直した試験の助けを、両方の木で呼んで比べた。毎刻みの関数 13・ループの走査の関数の集合 273・`ufunc.at` の当たり 5・帳簿の口の呼び手 2・体の口の呼び手 5 は同じ。空の集合で通る所・名が見つからずに飛ぶ所は 0=黙って縮んだ所は 0。
  - 心の読みの表とお金の書き手の表: 手直しのほかは土台と 1 字も同じ。`mind/ops.py` は `mind/` の下なので走査に入り続ける。
  - 決まり: act の外の書き手は `mind/ops`(心の欄だけ)と `restore`(§9-9 の宣言)で、どちらも割る前から在った書き。新しい書きは無い。
  - 数の固定の直し(83 と 81): 検収役が自分で数えても合い、負の対照(82)も通る=確かめは弱まっていない。

### 10-2. 検収の低と知らせ・親の答え

- 道具の側の低-1(`RESOLVE_FILES` の 15 本のうち `runtime/state/restore.py` は、`allow.index` で数えると直接の書きを持つ関数が 0=復元は静的な読みの外の形で書く): 載せたままにする(裁定 Q4・Q11。外すと凍結の索引の関数の集合が割る前と変わる)。§9-3 の言い方(resolve から来た関数を頂上に持つ 16 本から `write_guard.py` を除いた 15 本)が正しい数え方。
- 道具の側の低-2(`shibuya.engine` の字面が、docstring・注・schema の札・凍結の名・台帳の道の値に残る。使い方の案内として古いのは `interfaces/cli/run_args.py` の docstring の 1 か所): 段 8 の文の掃除で直す。実行の時に読む形は 0 なので、今は直さない。
- 意味の側の低-1(割り先どうしが名の import で呼び合う): §10-3 に一覧を足した。今は何も起きない。
- 意味の側の低-2(割る道具の `judge.py` の宣言の「わけ」が「差し替えは無い」と言うが、`proximity/test_runs.py` が `set_conversing` を差し替え、その読みは `judge.py` が渡す別名を通る): 届く先は talk で正しく、外すと落ちる(§9-5 の 13)。宣言の文は、割る道具の次の commit で正す(この commit では道具を変えない)。
- 手順の知らせ(実装役): 合図のファイルを、指紋の確かめと同じ行で消したことが 1 回あった(消すコマンドは単独で、の決まりに当たる)。走査の一覧の写しを 1 回、リポの外の一時の置き場に書いた(中身は道の一覧だけ)。どちらも報告に載せ、次の発注文に 1 行足す。

### 10-3. 割り先をまたぐ名の import(これから差し替えを足すときは、読む側のモジュールの属性を差し替える)

割る前は、resolve の中の関数どうしが素の名で呼び合っていたので、`resolve.X` を差し替えれば、中の呼び手にも効いた。割った後は、割り先が相手の関数を名の import で持つので、定義の割り先を差し替えても、ほかの割り先の呼び手には届かない(呼び手のモジュールが持つ名を差し替える)。今の試験と tools が差し替える resolve 由来の名は 9 つで、どれも割る前に resolve の中で素の名で読む関数が無い(検収役が土台の AST で確かめた)=今は何も起きない。挙動は変わらない(byte-check)。

| 読む側の割り先 | 定義の割り先 → 名の import で持つ関数 |
|---|---|
| `act/apply.py` | `act/gate.py` → `ResolveOutcome`・`_ok`・`_fail`/`act/ops/shop.py` → `_apply_buy`・`_apply_eat`・`_apply_queue`・`_apply_wait`・`_serve_poi_queue`・`_stage2_note_calls`・`_stage2_withdraw`/`act/ops/move.py` → `_apply_engine_step`・`_apply_move`・`_is_nav`・`_nav_positions`・`_nav_stop`/`act/ops/rail.py` → `_apply_alight`・`_apply_board`・`_serve_board_queue`/`act/ops/talk.py` → `_apply_leave`・`_apply_talk`/`act/ops/intent_writes.py` → `_clear_intent_fields`・`intent_kept_by`/`act/ops/focus.py` → `_advance_focus` |
| `act/ops/move.py` | `act/gate.py` → `ResolveOutcome`・`_ok`・`_fail`/`act/ops/focus.py` → `_clear_focus`・`_focus_xy`・`_set_focus`/`act/ops/rail.py` → `_enter_board_queue` |
| `act/ops/shop.py` | `act/gate.py` → `ResolveOutcome`・`_ok`・`_fail`/`act/ops/body_writes.py` → `_energy_meal`・`_energy_snack`/`act/ops/focus.py` → `_set_focus`/`foundation/write_guard.py` → `_require_thawed` |
| `act/ops/talk.py` | `act/gate.py` → `_ok`・`_fail`/`act/ops/shop.py` → `balk_queue`・`release_indoor`/`foundation/write_guard.py` → `_require_thawed` |
| `act/ops/rail.py` | `act/gate.py` → `ResolveOutcome`・`_ok`・`_fail` |
| `act/ops/plan_writes.py` | `act/ops/rail.py` → `_cell_of_node`・`_platform_table` |
| `act/ops/intent_writes.py`・`act/ops/law_writes.py`・`mind/ops.py` | `foundation/write_guard.py` → `_require_thawed` |

- 数え(親が割った後の木の AST で数えた): 割り先どうしの名の import のうち、resolve から来た関数とクラスは延べ 50。このほかに、語彙の 2 本(`act_codes`・`agent_codes`)の値と列挙を名で持つ import が在る(値と列挙は差し替えの的にならない)。

### 10-4. 親が回した確かめ

| 何を | 結果 |
|---|---|
| byte-check 19 構成(本体の道具・基準 `4a5bd30`・割った後の木) | 37 欄すべて同じ 19・動いた 0・誤り 0・438 秒・既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。記録 [bytecheck_G1_parent/](bytecheck_G1_parent/)(実装役の記録は [bytecheck_G1/](bytecheck_G1/)=434 秒)。記録の「読み込んだ src」は、基準 262 本・比べる側 276 本。基準にだけ在るのは `engine/__init__.py`・`engine/resolve.py`。比べる側にだけ在るのは 新しい 16 本。sha が変わったのは 35 本 |
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`。回している間、この作業木は誰にも編集させていない) | 7,069 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・22 skipped・1 xfailed・40 分 24 秒。前の回(下ごしらえ・7,044 passed)から +25=道具の宣言の試験 24 と、足した負の対照 1 |
| 差分を読んだ(手直し 3 つ・試験 2 本) | `RESOLVE_FILES` は 15 本・お金の書き手の表は 4 行の道だけ・心の読みの表は resolve の項だけを外した・数の固定は 83 と 81 の 2 つと負の対照・偽のファイルの置き場は `act` |
| 守る物に差が無いこと(`git status`) | `tools/pkgmove`・`tools/bytecheck`・`map.toml`・`contracts.toml`・つなぎの台帳の JSON・凍結の索引 2 本は変わっていない。`src/shibuya/engine` の置き場は無い |
