# 走査の道具の自己更新の規則の直し(第347)

> [返事その 8](../../../design/prompt-2026-11-16-reply8.md) §1-6 の 4 の答え「直してください。心の読みの一覧を試験で固定する前に、別の commit で行い、検査の結果がどう変わったか(strict に入る行)を報告してください。ランの値が変わらないことは byte-check で確かめてください」の記録。
> 問いの元: [コードの区分の表](../../../reference/package-map-final-2026-11-09.md) §8-1 の 4・[心の読みの数え直し](../../../reference/mind-world-reads-2026-11-09.md) §4-1。
> 実装は実行役(Opus 5.5)。byte-check と範囲の試験の欄(§5)は親が埋める。

## 1. 直したこと

`src/shibuya/runtime/state/ledger_ast.py` の `_is_self_update`(`scan` が属性の読みを数えるときに、自己更新=書き直しの右辺の読みを外す規則)。

- 前: 比べるのは**列の名前だけ**で、受け手(手前の式)を見ていなかった。左辺の中の属性の名前を全部集めて比べていた。そのため次の 2 つの読みが外れていた。
  - 穴 A: 右辺の読みで、左辺は同じ名前の列を別の受け手に書く。例: `self.price = np.asarray(world.pois.price, ...)`(店の値段)。
  - 穴 B: 左辺の添字の中の読みで、左辺は別の物を書く。例: `a[r.fam_thing[ids] == FAMILIARITY_EMPTY] = ...`。関数の docstring は「左辺の中(添字)の読みは、その左辺が同じ列を書くときだけ自己更新」と書いていたが、実装は読みの節そのものが左辺に入るので常に真だった。
- 後: 右辺の読みも左辺の添字の中の読みも、**左辺(組なら対の要素)が同じ受け手の同じ列を書くときだけ**自己更新と見なす。受け手は手前の式の文字列(`ast.unparse`)で比べる。別名(`r` と `agents.registry`)は別の受け手と見る=読みに数える側に倒す。外の状態の検査が使う `_self_update_stmt` と同じ比べ方。
- 足した関数: `_written_attrs`(左辺が書く属性。添字の中の属性は入れない)・`_writes_same`。消した関数: `_attr_names`(直しで呼び手が 0)。`_target_names` は前から呼び手が無いが残した(削除は別の段)。
- 許可の表(`EXT_AST_ALLOW`・`DIAG_EXITS`・`UNRESOLVED_ALLOW`・状態台帳の行の `ast_allow`)は変えていない。

## 2. 数え方

道具を読むだけで回した(ランはしない)。同じ木で、直す前(頭 `ff28372d`)と直した後の `src/shibuya` を走査した。

```python
from pathlib import Path
from shibuya.runtime.state import ledger_ast as A
res = A.scan(Path("src/shibuya"))   # files・names は渡さない(build/ を除く全部・宣言の全部の列)
A.check(res)                        # 空なら合格
```

心の読みの数は[心の読みの数え直し](../../../reference/mind-world-reads-2026-11-09.md) §1 と同じ数え方(strict の読みのうち、心の区分のファイルが、持ち主が心でない列を読む所。割るファイルは[全ファイルの表](../../../reference/package-map-final-2026-11-09-files.md) §4 の割り先で関数ごとに分ける)。

## 3. 結果

| | 直す前 | 直した後 |
|---|---:|---:|
| 走査したファイル | 277 | 277 |
| strict の読み | 841 | 844(+3) |
| loose の読み | 1,154 | 1,175(+21) |
| 解決できない動的な読み | 7(全部許可に載る) | 7 |
| `check` | 空(合格) | 空(合格) |
| 心の読み(別紙の鍵=移した後の道筋・割るファイルだけ記号・列) | 82 か所・48 組 | 83 か所・49 組 |
| 心の読み(鍵=移した後の道筋・`クラス.メソッド` か関数名・列) | 82 か所・71 組 | 83 か所・72 組 |

直す前の 82 か所・48 組は、別紙の json の `key_counts` と組ごとに全部同じだった。

### 3-1 strict に入った行(3)

| ファイル:行 | 関数 | 列(置き場・持ち主) | 文 | 穴 | 心の読みの一覧 |
|---|---|---|---|---|---|
| `mind/judge/store_choice.py:94` | `StoreChoice.__init__` | `price`(pois・world) | `self.price = np.asarray(world.pois.price, dtype=np.int64)` | A | 入る(+1) |
| `mind/memory/familiarity.py:186` | `FamiliarityLayer._activation_rows` | `fam_thing`(agents・mind) | `a[r.fam_thing[ids] == FAMILIARITY_EMPTY] = ACTIVATION_ABSENT` | B | 入らない(心の自分の列) |
| `mind/memory/memory.py:450` | `MemoryLayer.scores` | `mem_kind`(agents・mind) | `s[r.mem_kind[a] == _EMPTY] = -np.inf` | B | 入らない(心の自分の列) |

### 3-2 loose だけに入った行(18)

手前の式が SoA らしくない(結果の物の同じ名前の欄・同じ名前のメソッドの呼び出し・想起した記憶の行)。どれも軸 1 が behavior の列なので `check` の検査 2(no/diag の列は loose の読み手 0)に掛からない。

| ファイル:行 | 列 | 文 | 穴 |
|---|---|---|---|
| `engine/resolve.py:574` | `hunger` | `agents.registry.hunger[:] = init.hunger` | A |
| `engine/resolve.py:575` | `fatigue` | `agents.registry.fatigue[:] = init.fatigue` | A |
| `engine/resolve.py:576` | `thermal` | `agents.registry.thermal[:] = init.thermal` | A |
| `engine/resolve.py:580` | `density_stage` | `world.cells.density_stage[:] = world.density_stage()` | A |
| `engine/resolve.py:1161` | `fatigue` | `r.fatigue[:] = upd.fatigue` | A |
| `engine/resolve.py:1163` | `fatigue` | `r.fatigue[upd.fatigue_ids] = upd.fatigue` | A |
| `engine/resolve.py:1166` | `hunger` | `r.hunger[:] = upd.hunger` | A |
| `engine/resolve.py:1168` | `hunger` | `r.hunger[upd.hunger_ids] = upd.hunger` | A |
| `engine/resolve.py:1194` | `hunger` | `r.hunger[:] = init.hunger` | A |
| `engine/resolve.py:1532` | `density_stage` | `world.cells.density_stage[:] = world.density_stage()` | A |
| `engine/resolve.py:1538` | `density_stage` | `world.cells.density_stage[:] = geometry.density_stage(geometry.surface_counts(r))` | A |
| `engine/resolve.py:1562` | `density_stage` | `world.cells.density_stage[:] = geometry.density_stage(world.cells.density)` | A |
| `engine/resolve.py:1702` | `density_stage` | `world.cells.density_stage[:] = nav.density_stage(nav.surface_counts(agents.registry))` | A |
| `mind/memory/memory.py:580` | `kind` | `rs["recalled_kind:" + ("store" if it_.kind == STORE_ITEM_KIND` | B |
| `mind/memory/memory.py:581`(2 つ) | `kind` | `else str(KIND_NAMES.get(it_.kind, it_.kind)))] += 1` | B |
| `mind/memory/memory.py:663`(2 つ) | `kind` | `rs["recalled_kind:" + str(KIND_NAMES.get(it_.kind, it_.kind))] += 1` | B |

loose の +21 は、上の 18 行(読み 18)と §3-1 の 3 行の和。ほかに `runtime/state/ledger_ast.py` の中の `e.kind` の読み 1 つが行の番号だけ動いた(504 → 528=このファイルに行を足したため・数は同じ)。

### 3-3 直しても外れたままの読み(本当の自己更新・19)

全部 `engine/resolve.py` の `r.c[x] = f(r.c[x])` の形(同じ受け手 `r` の同じ列): `since_meal_kcal`・`nav_t`・`nav_wait`・`focus_ttl`・`activity`(4)・`money`(3)・`holdings`・`hunger`(2)・`fatigue`・`plan_flags`(4)。

## 4. 試験

`tests/engine/test_state_ledger_10b.py` の 2 つの試験の引数の表に足した(試験の関数は増やしていない)。

- `test_p5_ast_blind_spots_are_caught`(読みとして捕まる・strict にも入る): 穴 A の 3 つ(`self.rel_last = np.asarray(world.pois.rel_last)`・`other.rel_last[a] = reg.rel_last[a] + 1`・`self.rel_last, self.cell = world.pois.rel_last, world.pois.cell`)、穴 B の 2 つ(`out[reg.rel_last[a]] = 1`・`self.n[reg.rel_last[a]] += 1`)、左辺が名前だけの 2 つ(`x: int = reg.rel_last[a]`・`x = y = reg.rel_last[a]`=前も後も読み)。
- `test_p5_true_self_updates_are_still_not_reads`(読みに数えない): `reg.rel_last[a][b] = reg.rel_last[a][b] + 1`・`reg.rel_last[a] += reg.rel_last[b]`・`reg.rel_last[:] = np.minimum(reg.rel_last, 3)`。
- 穴 A・B の 5 つは、直す前の規則では読み 0(loose も strict も)で、直した後は読み 1 になることを、関数を差し替えて確かめた。

## 5. ランの値が変わらないことの確かめ(親が回した)

- 直した関数(`_is_self_update`・`_written_attrs`・`_writes_same`)を呼ぶのは `scan` だけで、`scan` と `check` を呼ぶのは試験だけ。`ledger_ast` のモジュールはランの道で読み込まれる(`runtime/systems/table.py` の `make(...)` → `spec.make` → `allow.writes_for_ops` → `allow.index`)が、そこで使うのは `_parents`・`declared_columns`・`_is_write` だけで、どれも変えていない。
- byte-check(19 構成・37 欄): **すべて同じ(動いた 0・誤り 0・final が同じ 19)・終了コード 0**。基準は段 4-13 の commit `6064564`(`python tools/bytecheck/cli.py run --base 6064564 --src <作業木の src> --set all19 --jobs 6`)。既定の final は `c8d68704b7b0760d`・呼数 60,939 のまま。記録 [bytecheck/](bytecheck/)。段 4-10 の頭(`ff28372`)の上でも 1 回回し、同じ結果だった(その記録は、新しい頭での結果に置き換えた)。取り込みの土台(`07559de`)と `6064564` の間で、src は同じ。
- 範囲の試験(① と ② を合わせた木・`pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`): 6,818 passed・21 skipped・1 xfailed・**1 failed**。落ちたのは前からの 1 本(`tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`=linked の作業木でだけ落ちる)。
