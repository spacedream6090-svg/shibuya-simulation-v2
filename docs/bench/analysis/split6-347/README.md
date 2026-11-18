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
