# 移す段 1・段 2(コードの区分の移動の下ごしらえ・返事その 7 §4-2)

> 整理の段(既定の結果を 1 バイトも変えない段)。ファイルはまだ動かしていない(動かすのは段 4)。
> 発注: [返事その 7](../../../design/prompt-2026-11-09-reply7.md) §4-2 の 3・4。計画: [最終の表と移す段の計画](../../../reference/package-map-final-2026-11-09.md)
> §7-0〜§7-3 と[全ファイルの表](../../../reference/package-map-final-2026-11-09-files.md)。照らし合わせ: [照らし合わせ](../../../reference/package-map-reconcile-2026-11-05.md) §2-1 の末尾。
> 土台 `3d88da1`(枝 `stage/move12`)。実装役 Opus 5.5。commit とタグは親。

## 0. 要点

- **段 1 固定の表**: `src/shibuya/engine/class_ids.py` を足した。src(`build/` を除く)のクラス 481(168 本)のうち **480** は
  表(「モジュール.クラス名」→ 凍結の名・段 1 では鍵と値が同じ)、残る 1 つ(CP12 の実験の条件の型)は表に名を書けないので、
  名を書いてよい置き場 `engine/events/log.py` でクラスの属性 `CLASS_ID` に凍結の名を宣言し、`class_id` が表の次に読む(§6 M1)。
  表にも宣言にも無い `shibuya` の型は `class_id` が止める(§6 M2)。ハッシュ・状態のファイル・設定の指紋・系ごとの指紋に名を流す
  4 ファイルの 5 つの関数を、表を引く形にした。byte-check 19 構成 37 欄 **19/19 同じ(終了コード 0)**。
- **段 2**: 2-1 名前を変えてはいけない文字列の凍結(乱数の領域の名 41・道の形 8+接尾 2・版の ID 69・見出し 9・ほかの名 3)、
  2-2 根の道を `core/paths.py` の 1 か所に、2-3 書きの許可の一覧の形、2-4 乱数の検査の道、2-5 世界カタログの包みの名。
  byte-check 19 構成 37 欄 **19/19 同じ(終了コード 0)**。凍結には、6 つの短いランの manifest・run_meta・テープの見出し・
  ハッシュから拾った道の形の文字列 74 種も足した(§6 M4)。
- **別の検収役の指摘の直し(§6)**: M 6 件・L 4 件を直した(L5 は親の作業)。直した後の byte-check も **19/19 同じ(終了コード 0)**。
- **しなかったこと**: 2-6(封印の語の AST の検査と `sealed_only` の試験)。封印の語の一覧が 2 つある件(最終の表の聞きたいこと 5)が
  ユーザーの判断待ちのため(発注どおり)。
- 計画の数との違い: 表のクラスは計画の 480 と同じ数だが中身が違う(関数の中のクラス `engine.experiment.branch._recorder.<locals>._Recorder`
  を足し、CP12 の実験の条件の型 `engine.events.log` の `Experiment` は表でなく置き場の宣言にした)・
  乱数の領域の名は 42 → **41**(第346 で `conversation.invite` を消した)・道と同じ形のほかの名は 2 → **3**(この役が見つけた塩の語
  `\x1fengine` を足した=§2-1)。

## 1. 段 1 固定の表(計画 §7-1)

### 1-1 変えたもの

| ファイル | 関数 | 前 | 後 |
|---|---|---|---|
| `engine/class_ids.py`(新) | `class_id`・`class_path` | — | 表 `CLASS_IDS`(480 行・`MappingProxyType`)と逆引き `_PATH_OF`。表 → クラスの宣言 `CLASS_ID` の順に引き、どちらにも無い `shibuya` の型(構築の段 `shibuya.build` を除く)は `TypeError`。`shibuya` の外の型と構築の段の型は今の名をそのまま返す |
| `engine/events/log.py` | `Experiment` | — | クラスの属性 `CLASS_ID = "shibuya.engine.events.log.Experiment"`(凍結の名の宣言=§6 M1。dataclass の欄にはならない `ClassVar`) |
| `engine/state_hashes.py` | `_qual` | `f"{t.__module__}.{t.__qualname__}"` | `class_id(type(obj))` |
| `engine/state_codec.py` | `qualname` | 同じ形 | `class_id(t)` |
| `engine/state_codec.py` | `allowed_class` | 名を `rpartition` して import | `class_path(name)` を import し、`qualname(obj) == name`(=凍結の名)を確かめる |
| `engine/resume.py` | `_canon` の最後の行 | `f"<{type(v).__module__}.{type(v).__qualname__}>"` | `f"<{class_id(type(v))}>"` |
| `engine/systems/probe.py` | `plain` の最後の行 | `("obj", type(v).__module__ + "." + type(v).__qualname__)` | `("obj", class_id(type(v)))` |

変えないもの(計画どおり): `ALLOWED_CLASSES`(17)・`CLASS_FIELDS`(2)・`VALUE_CLASSES`(4)の鍵は凍結の名のまま(注を 1 行ずつ
足しただけ)。`engine/events/log.py` の `cls.__module__ != __name__`・`systems/static_check.py` の `__module__` の比べ
(段 2-3 で名の作り方だけ直した=§2-3)。

`engine/removed_switches.py`(第346 で足された)はクラスを持たない(表に行は無い)。[全ファイルの表](../../../reference/package-map-final-2026-11-09-files.md)
に行 224a を足した: 置き場の案 `foundation/arms/removed.py`(標準ライブラリだけを読み、読み手が世界の法則・経済の規則の口・
runtime・CLI にまたがる=全部より下の foundation。切替口 4 本と同じ `foundation/arms/`)。置き場は段 4 の前に親が確かめる。
あわせて、移す段で足したファイルの行 143a `engine/class_ids.py`(→ `runtime/state/class_ids.py`=計画 §7-1)と 91a `core/paths.py`(→ `foundation/paths.py`=計画 §7-3)も足した(行は 327 本。本文 §2 の包みごとの数には入れていない)。

### 1-2 表の作り方

道具 [tools/gen_class_ids.py](tools/gen_class_ids.py)(冪等・標準ライブラリだけ):

```
python docs/bench/analysis/move-346/tools/gen_class_ids.py           # 書く(class_ids.py と凍結の JSON)
python docs/bench/analysis/move-346/tools/gen_class_ids.py --check   # 今のファイルが作り直しと同じか
```

- src(`build/` を除く)の全部の `.py` を AST で読み、全部の `ClassDef` を `__qualname__` と同じ形(入れ子は `外.内`・関数の中は
  `関数.<locals>.クラス`)で集める。鍵は「モジュール.クラス名」(`__init__.py` はパッケージの名)。
- 値は足すだけで変えない: 今の `class_ids.py` に載る鍵は今の値を引き継ぎ、新しい鍵は値=鍵で足す。消えたクラスの行は落とす。
- **置き場で宣言するクラス(表に載せない)**: `engine/events/log.py` の実験の条件の型 `Experiment` の 1 つ。CP12 の試験
  (`tests/engine/events/test_e_cause_three_kinds.py::test_no_module_outside_the_gate_names_the_experiment_type`)が、
  `engine/events/log.py` と `engine/experiment/gate.py` の外の src に、名を文字列で書くこと(`'….Experiment'`)を落とすため、
  表には書けない。最初の版は全部のクラスを載せて範囲の試験でこの 1 本が落ち(§4)、次の版は表から外して「値はハッシュにも状態の
  ファイルにも入らない」と書いたが、**これは不正確だった**: 系ごとの指紋(probe)の外の状態の digest は全部の行で
  `state_hashes.item_digest` を呼び、行 E の `events._cz_experiments`(`Experiment` の list)で dataclass の名が入る(別の検収役の
  M1)。そこで、名を書いてよい `log.py` の側でクラスの属性 `CLASS_ID` に凍結の名を宣言し、`class_id` が表の次に読む形にした
  (CP12 の門と、門の許す置き場は変えていない・`class_ids.py` は何も import しない=輪は無い)。道具は AST でクラスの本体の
  `CLASS_ID = "…"` を見つけ、宣言のあるクラスを表から外す。
- 関数の中でないクラス 480 個は import して `__module__`・`__qualname__` が鍵と同じか(宣言のあるクラスは宣言の値が AST と同じか)を
  確かめた(違えば止まる)。関数の中の 1 個は AST の名だけ。
- 凍結の JSON `tests/engine/state/class_ids_frozen.json` は「凍結の名 → `__qualname__`」の写像(481 行・宣言の分を含む)。道具は、
  どの行も凍結の名の末尾が鍵のクラスの `__qualname__` であることを確かめる(§6 M3)。
- 動的に作るクラス(`namedtuple(...)`・`Enum(...)`・`type(..., ..., ...)`・`make_dataclass`)は src に無い(`core/types.py` の
  `NewType` 3 つは型でなく値が int)。

### 1-3 試験(`tests/engine/state/test_class_ids.py`・12 本)

1. 網羅: src の全部のクラス(試験の中の別の AST の実装)= 表の鍵 ∪ 置き場で宣言するクラス(CP12 の型だけ)。
2. 凍結: 凍結の JSON(凍結の名 → `__qualname__`)= 表の値と宣言の値から作った写像。どの行も値の末尾が鍵のクラスの `__qualname__`。
   値どうしの入れ替え(`ActivityKind` と `AgentKind`)が名の集合では通り、写像では落ちることも確かめる(§6 M3)。
3. 1 対 1: 値が重ならない・`class_path(値)` が鍵に戻る・許可の表と値のクラスと欄の一覧の型(21 個)が今の名に戻る。表にも宣言にも
   無い `shibuya` の型(`type()` で後から作った型・名前つきの組)は止まり、`shibuya` の外の型・試験の中の型・構築の段の型は今の名の
   まま・宣言は自分の文字列だけを読む(継いだ宣言は読まない)(§6 M2)。
4. 入口: 4 ファイルに `__module__` と `__qualname__` を 1 つの式で連ねる所が無い・5 つの関数が `class_id`・`class_path` を呼ぶ・
   連ねるのは `class_ids.py` の 1 か所だけ。
   入口の確かめの振る舞いの負の対照: `_PATH_OF` を別のクラスへ向けると `allowed_class` と状態のファイルの読みが
   `StateFormatError` で止まる(§6 M6)。
5. 動かしたふり(3 本): 試験の中で 3 つの型(dataclass `WakeCandidates`・Enum `EventClass`・値のクラス `DeferralQueue`)の
   `__module__` を別の置き場に書き換え、表の鍵をそれに合わせる。(a) 値の直列化(ハッシュ)・状態のファイルの中身と読み戻し・
   設定の指紋・系ごとの指紋が書き換える前と同じ。(b) 30 体・2 日の mock で 750 で止めて状態を書き、再開する短いランの全
   checkpoint(final=behavior-hash・full-hash・combined)・状態のファイルの中身(ランの ID を除く)・見出しの指紋・再開の final が
   同じ(3 つの型が状態のファイルに流れていることも確かめる)。負の対照: 表を合わせない `shibuya` の置き場では止まる(ランも)。
   `shibuya` の外へ動かしたふりでは名が変わり、ハッシュと指紋、全 checkpoint の behavior-hash と full-hash が動く。(c) CP12 の型:
   系ごとの指紋の `probe.snapshot` の行 E の `events._cz_experiments`(と、その下の `item_digest`)が、置き場を動かしたふりでも
   同じ(代わりの digest に落ちていないことも確かめる)。宣言を外すと `shibuya` の置き場では止まり(probe は代わりの digest に
   落ちる)、`shibuya` の外では digest が動く(§6 M1)。
6. 往復: 許可の表の 17 の名が全部 `allowed_class` で組み立てられ、凍結の名に戻る。
7. 表に無い型が 0 件: 止める口(`class_ids._unknown`)を数える口に替えて、既定のラン(止めて再開)と系ごとの指紋(probe)つきの
   ランを回す=表にも宣言にも無い `shibuya` の型は 0 件(§6 M2)。

### 1-4 byte-check(段 1)

`python tools/bytecheck/cli.py run --base 3d88da1 --work C:\bcm1 --out-dir <スクラッチ> --set all19 --jobs 6`

- **19 構成・37 欄すべて同じ 19・一部を比べていない 0・動いた 0・誤り 0・final が同じ 19 → 終了コード 0**。
  基準の側 209 秒・比べる側 200 秒・全体 410 秒。final `w6_v3_default` = `c8d68704b7b0760d`(60,939 呼)。
- compare の JSON: [bytecheck/stage1_compare_base_3d88da1_vs_work.json](bytecheck/stage1_compare_base_3d88da1_vs_work.json)。
- 作業の置き場はつなぎが残っていないこと(`dir /AL /S` で 0 件)を確かめてから消した。

## 2. 段 2(計画 §7-2・§7-3)

### 2-1 名前を変えてはいけない文字列の凍結

道具 [tools/gen_frozen_names.py](tools/gen_frozen_names.py) で `tests/engine/state/names_frozen.json` に凍結した(形は
`tests/engine/time/manifest_keys_frozen.json` と同じ `schema`・`note`・中身。道と行の番号は鍵にしない)。試験
`tests/engine/state/test_names_frozen.py`(13 本)は src の AST を別の実装で集めて比べ、短いランから拾う分(下の表の最後の行)は
`tests/engine/state/shaped_names.py` で子のプロセスを回して比べる。docstring の中の文字列は数えない。

| 種類 | 数 | 集め方 | 試験 |
|---|---:|---|---|
| 乱数の領域の名(3 つの表の鍵) | 41(母集団 15・環境 3・動き 23) | `POPULATION_RNG_DOMAINS`・`ENVIRONMENT_RNG_DOMAINS`・`MOTION_RNG_DOMAINS` の頂上の代入を名で探す(build の外) | 鍵の集合が凍結と同じ |
| そのうち今のモジュールの道と同じ形 | 8 | `shibuya.` を頭に足すと 2 部品以上の頭が src のモジュールか包みになる鍵(`engine.chooser`・`engine.processes.environment`・`engine.processes.rail`・`llm.mock`・`llm.mock.move_target`・`llm.mock.out_of_cell_target`・`perception.attention.p_see`・`perception.p_notice`) | 表の鍵にあり、ランの側の src の定数に出てくる数が凍結と同じ(3・3・5・3・1・1・4・3=§6 L1) |
| 接尾 | 2 | `llm.mock` の `_MOVE_TARGET_DOMAIN_SUFFIX`・`_SHOP_TARGET_DOMAIN_SUFFIX` の値(`.move_target`・`.out_of_cell_target`) | 出てくる数が凍結と同じ(各 1) |
| 版の ID | 69(文字列 61・バイト列 8・値は 67 種) | src の全部(build を含む)の文字列とバイト列の定数のうち `shibuya.<点の名>/` で始まるもの(多重集合) | 多重集合が凍結と同じ |
| ハッシュと指紋の見出し(バイト列) | 9 | src の全部のバイト列の定数のうち `shibuya.` で始まるもの(多重集合。版の ID の 8 と `engine/tape.py` の `b"shibuya.tape.schema"`) | 多重集合が凍結と同じ |
| 道と同じ形のほかの名 | 3 | 計画の 2(manifest の節の名 `economy.stage2`・`shibuya.cache_salt`)と、この役が見つけた `\x1fengine` | ランの側の src の定数に出てくる数が凍結と同じ(`\x1fengine` は 2・ほかは 1=§6 L1) |
| ランから拾った道の形 | 74 種(6 構成) | 6 つの短いランの manifest・run_meta・テープの見出し・ハッシュに入る文字列の中の、点の道と斜線の道の部分(§6 M4) | 構成ごと・拾う所ごとの集合が凍結と同じ |

- 計画の「版の ID 70 か所」との差 1 は docstring の中の 1 か所(`build/sched/trial.py` の `shibuya.build.sched/W17/v2/depart:`)。
  docstring は記録なので凍結に入れていない。
- `\x1fengine` は `engine/run.py` の `run_salt_for`(`blake3(seed‖0x1f‖"engine")`)と `perception/renderer.py` の近接の同点の塩の
  f 文字列の定数の部分。包みの名 `engine` と同じ語がハッシュに入るので、段 4 で包みの名を書き換える道具が触らないように足した
  (計画の表に無い=親の確認を待つ)。
- 乱数の領域の名の 3 つの表のほか、`run.py` の `MOTION_SALTS` の鍵(`run_salt`・`fleet.call_seed`・`calendar_1b`)は記録の
  文字列で、`core.rng` の用途名でないので凍結していない。

### 2-2 根の道を 1 か所に(`core/paths.py`)

`src/shibuya/core/paths.py` を足した(段 4 で `foundation/paths.py` へ)。`PACKAGE_ROOT`(`src/shibuya`)・`REPO_ROOT`・
`resolve_repo_path`(`engine/calendar.py` から移した)・`find_upward(relpath, start)`・`module_dir(__name__)`。ランの側
(`build/` の外)で `__file__` を使うのは `core/paths.py` だけになった(試験)。

| ファイル | 前 | 後 |
|---|---|---|
| `core/budget.py` `_repo_root` | `Path(__file__)` から上へ辿る | `find_upward(BUDGET_MD_RELPATH, module_dir(__name__))`(辿る順は同じ=ファイルのディレクトリから。見つからないときの文はディレクトリの名になる) |
| `world/processes/constitution.py` `_repo_root` | 同じ形 | `find_upward(relpath, module_dir(__name__))` |
| `engine/bridging/ledger.py` `default_path` | `parents[4]` | `REPO_ROOT / LEDGER_RELPATH` |
| `engine/rules/table.py` `default_path` | `parents[4]` | `REPO_ROOT / TABLE_RELPATH` |
| `engine/classical.py` `ACTIVITY_PRIOR_PATH` | `parents[3]` | `REPO_ROOT / …` |
| `engine/energy.py` `_ANCHORS_DIR` | `parents[3]` | `REPO_ROOT / …` |
| `engine/resume.py` `_repo_root` | `parents[3]` | `REPO_ROOT`(試験が差し替える口なので関数のまま) |
| `engine/bridging/scan.py` `scan_package` | `parents[2]`(包みの根) | `PACKAGE_ROOT` |
| `engine/systems/allow.py` `src_root` | `parents[2]`(包みの根) | `PACKAGE_ROOT` |
| `engine/systems/static_check.py` `source_root` | `parent` | `module_dir(__name__)`(呼び手は無い) |
| `engine/calendar.py` | `REPO_ROOT` と `resolve_repo_path` の定義 | 定義を消し、`core.paths` の `resolve_repo_path` を使う(`__all__` から外した=再輸出の口は残さない) |
| `economy/wages.py`・`engine/economy_stage2.py`(2 か所)・`engine/resume.py` | `engine.calendar` の `resolve_repo_path` | `core.paths` の `resolve_repo_path`(economy から暦への辺と、再開の口から暦への辺が消えた) |
| `tests/engine/test_10a_review_fixes.py` | `engine.calendar` から import | `core.paths` から import |

- byte-check の道具の一覧 `tools/bytecheck/tree.py` の `ROOT_READERS` に `shibuya/core/paths.py` の行を足し、
  `engine/calendar.py` の行の文を「`resolve_repo_path` の呼び(定義は `core/paths.py`)」に直した。道具の試験
  (`test_root_reader_files_are_declared`=`scan_root_anchors` と一覧が同じ)が要るため。道具は別の役の持ち物(計画 §7-5 の最後の行は
  「段 2-2 と段 4 でその役と一緒に直す」)なので、親の確認を待つ。写すファイル(`TRACKED_READS`)は変わらない。
- 記録の古い道具 `docs/bench/analysis/wallbounce-1012/ec21/tools/split_l2_l3.py` は `engine.calendar` から `resolve_repo_path` を
  import する。`calendar` が import した名として残るので今は動く(暗黙の再輸出・記録は直していない)。段 4 で壊れる(§5)。
- `module_dir(__name__)` は `__name__` が `__main__`(モジュールを直に `python …/x.py` で回したとき)なら包みの根を返す。
  使っている `core/budget.py`・`world/processes/constitution.py`・`engine/systems/static_check.py` は直に回すモジュールでない
  (検収 L3=書くだけ)。

### 2-3 書きの許可の一覧の形

- `engine/systems/allow.py`: `RESOLVE_FILES = ("engine/resolve.py",)` を足し、`index` はこの一覧のファイルを全部読む形にした
  (段 2 では 1 本=前と同じ木・同じ順)。関数の名がファイルをまたいで重なれば `ValueError`(1 本のファイルの中の重なりは前と同じ
  扱い)。段 6 で割り先の書き手のファイルを全部載せる。
- `engine/systems/static_check.py`: `RESOLVE_MODULE` は `engine.resolve` の `__name__`、系の包みの頭 `shibuya.engine.systems.`
  は `engine.systems` の `__name__` から作る。`from shibuya.engine import resolve` の形の照合(前の `"shibuya.engine"` と
  `"resolve"`)も `RESOLVE_MODULE` を割って作る。import の文は段 3 の道具が直すので、段 4・段 6 で文字列を直さなくてよい。
- 書きの許可の集合が段の前と同じことは、既存の `tests/engine/systems/`(`writes_soa_frozen.json` との突き合わせ)が通ることで
  確かめた。

### 2-4 乱数の検査の道(`engine/rng_audit.py`)

`core.rng` の名を `core.rng.__name__` から作る: `RNG_MODULE`(`shibuya.core.rng`)・頭の包みを除いた `_RNG_TAIL`(`core.rng`)・
その親 `_RNG_PARENT_TAIL`(`core`)・葉 `_RNG_LEAF`(`rng`)。直したのは計画の 3 か所(:80 の `endswith("core.rng")`・:406・:409 の
`"shibuya.core.rng"`)と、同じ働きの 3 か所(:70 の `== "rng"`・:74 の `endswith("core")`・:76 の `== "rng"`)。:74 は直さないと、
段 4 で `foundation` へ動かした後に `from shibuya.foundation import rng as R` の呼び手を見落とす(計画の数え「`core.rng` の名 3」に
入っていなかった)。道の表 44 行(`SAFE_SITES`・`UNDETERMINED_SITES` ほか)は段 4 の道具で直す(触っていない)。

### 2-5 世界カタログの包みの名(`manifest/world_catalog.py`)

`importlib.resources.files` に渡す包みの名を `_RESOURCE_PACKAGE = __package__ or __name__.rpartition(".")[0]` にした。
JSON(`manifest/frozen/world_catalog_v0_2.json`)と pyproject の `package-data` は段 4 で一緒に動かす(触っていない)。

### 2-6 試験(`tests/engine/state/test_move_prep_stage2.py`・12 本)

`__file__` を使うのは `core/paths.py` だけ・根の道が前と同じ(パッケージの `__file__` から求めた値と比べる)・読み手が求める
ファイルが前と同じ(つなぎの台帳・規則の表・活動の事前分布・錨・宣言表・知覚の契約書・宣言の走査の道筋)・`find_upward` の辿り方・
`RESOLVE_FILES` が resolve のファイルを指し関数の集合が同じ・関数の名の重なりで止まる・`static_check` と `rng_audit` と
`world_catalog` に道の文字列が残っていない・`rng_audit` の 3 つの import の形を、名を `shibuya.foundation.rng` に替えたふりでも
見つける・頂上の表の名がファイルをまたいで重なれば止まり、重ならなければ 2 本を 1 つの閉包にする(§6 L2)。

### 2-7 byte-check(段 2)

`python tools/bytecheck/cli.py run --base 3d88da1 --work <短い作業の置き場> --out-dir <スクラッチ> --set all19 --jobs 6`(段 1 と段 2 の累積を
基準 `3d88da1` と比べた)

- **19 構成・37 欄すべて同じ 19・一部を比べていない 0・動いた 0・誤り 0・final が同じ 19 → 終了コード 0**。
  基準の側 207 秒・比べる側 200 秒・全体 407 秒。
- compare の JSON: [bytecheck/stage2_compare_base_3d88da1_vs_work.json](bytecheck/stage2_compare_base_3d88da1_vs_work.json)。
- 作業の置き場はつなぎが残っていないことを確かめてから消した。
- **最後の版でもう 1 回**: 範囲の試験で CP12 の試験が落ちたので、表から実験の条件の型を外した(§1-2)。src が変わったので、最後の
  src で同じ形の byte-check を回し直した: **19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・final が同じ 19 → 終了コード 0**
  (基準の側 220 秒・比べる側 201 秒・全体 421 秒)。compare の JSON:
  [bytecheck/stage2_final_compare_base_3d88da1_vs_work.json](bytecheck/stage2_final_compare_base_3d88da1_vs_work.json)。

## 3. byte-check の結果(まとめ)

| 段 | 比べたもの | 構成 | 37 欄すべて同じ | 動いた | 誤り | final が同じ | 終了コード |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | 基準 `3d88da1` ⇔ 段 1 の作業木 | 19 | 19 | 0 | 0 | 19 | 0 |
| 2 | 基準 `3d88da1` ⇔ 段 1+段 2 の作業木 | 19 | 19 | 0 | 0 | 19 | 0 |
| 2(最後) | 基準 `3d88da1` ⇔ 表から CP12 の型を外した作業木 | 19 | 19 | 0 | 0 | 19 | 0 |
| 検収の直し | 基準 `3d88da1` ⇔ §6 の直しの後の作業木 | 19 | 19 | 0 | 0 | 19 | 0 |

37 欄=前の道具の 25 欄(final・呼数・テープの 2 表の行と列のハッシュ・25 欄の計器)と第346 で足した 12 欄(テープの置き場の全ファイルの
名と sha256・2 表のスキーマ・manifest と `run_meta.json` の全欄・全 checkpoint)。比べない欄は道具の README の一覧どおり
(git の commit を含む `env_id`・`environment.code` と、壁時計の欄)。両側の条件の確かめ(読んだ src の digest・写しの木の読み・
`PYTHONHASHSEED=0`)はどちらの段も誤り 0。

## 4. 範囲の試験・lint-imports・カード

- 範囲の試験 `pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`(作業木の src・venv は本体):
  - 1 回目(表に全部のクラス 481 を載せた版): 2 failed・6,687 passed・1 skipped・1 xfailed・errors 0(収集の誤り 0)。
    落ちたのは前からの 1 本と、`tests/engine/events/test_e_cause_three_kinds.py::test_no_module_outside_the_gate_names_the_experiment_type`
    (`engine/class_ids.py` に実験の条件の型の名の文字列=CP12 の門)。表からその型を外して直した(§1-2)。
  - 2 回目(表から CP12 の型を外した版): 1 failed・6,689 passed・1 skipped・1 xfailed・errors 0(収集の誤り 0)・34 分 14 秒。
  - **3 回目(検収の直しの後=最後の版): 1 failed・6,702 passed・1 skipped・1 xfailed・errors 0(収集の誤り 0)・34 分 11 秒**
    (足した試験 13 本の分だけ増えた)。
  - 落ちた 1 本は前からの `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`
    (作業木の data が本体の data へのつなぎのため、テープの置き場の相対の道筋が `data/tape/` で始まらない=この段の変更と関係しない)。
  - 飛ばした 1 本は `tests/engine/memory/test_m2_cue.py`(Ruri の重みが無い=前から)。
- 足した試験: `tests/engine/state/` の 3 本(`test_class_ids.py` 12・`test_names_frozen.py` 13・`test_move_prep_stage2.py` 12=37 本)と
  `tests/tools/test_bytecheck.py` の 1 本。拾いの口 `tests/engine/state/shaped_names.py`(試験の本体ではない)。
  張り替えた試験: `tests/engine/test_10a_review_fixes.py`(`resolve_repo_path` の import 元だけ)。
- `lint-imports`: 5 つの決まり全部 KEPT(326 ファイル・1,270 の依存)。
- 道具の確かめ: `gen_class_ids.py --check` と `gen_frozen_names.py --check` はどちらも「同じ」(終了コード 0)。
- カード: `python tools/repo_guide/build.py` で作り直した(カード 122 本)。`--check` は終了コード 0(最新)。全体の作り直しなので、
  `data.md`(data の大きさの揺れ=検収 L5・親が作り直す)・`docs.md`(この記録の置き場)・入口の `README.md` も書き換わった。

## 5. しなかったこと・親に確かめてほしいこと・段 4 で気をつけること

- **2-6 封印の守り(封印の語の AST の検査と `sealed_only` の試験)はしていない**。封印の語の一覧が 2 つある件
  (`build/audit/w19_freeze.HOLDOUT_TOKENS` と `tools/instruments/read_guard.SEALED_TOKENS`=最終の表 §8-1 の 5)が
  ユーザーの判断待ち。
- ファイルは動かしていない(段 4)。commit・タグ・版上げの記録(安定版のタグ・戻す手順・性能)は親。
- 親の確認を待つもの: (1) `tools/bytecheck/tree.py` の `ROOT_READERS` の 4 行と文の直し・`scan_root_anchors` の数えの広げ
  (§2-2・§6 M5)。(2) 凍結に足した `\x1fengine`(§2-1)とランから拾った 74 種(§6 M4)。(3) 全ファイルの表の行 224a の置き場の案と、
  足した行 91a・143a(§1-1)。(4) 表の道具と凍結の道具を記録の下に置いた(段 3 の `tools/pkgmove/` に寄せるかは段 3 で決める)。
  (5) CP12 の実験の条件の型を `log.py` のクラスの属性 `CLASS_ID` で宣言する形(§6 M1)。
- **段 4 で壊れるもの・動くもの(検収 L4 と、拾いで見つけたもの)**:
  - 記録の古い道具 `docs/bench/analysis/wallbounce-1012/ec21/tools/split_l2_l3.py:30` は `engine.calendar` が import した
    `resolve_repo_path` を通って動いている(暗黙の再輸出)。段 4 で `engine/calendar.py` を動かすと壊れる。古い記録の道具は書き換えない。
  - つなぎの台帳 `docs/design/bridging-ledger.json`(byte-check が写す追跡ファイル)の行は、宣言の置き場を `declared_in` に
    `src/shibuya/…` の道筋で持つ(398 行)。行の ID `HD-engine.energy-cc73b60c` の形(約 92 か所)は ID で変えないが、`declared_in` は
    ファイルを動かすと `engine/bridging/scan.py` の走査の結果と食い違う(台帳の試験が落ちる)。台帳を直すと manifest の
    `bridges_version` が動く(byte-check の「動いた」)。段 4 の前に、台帳の道筋を直すか・走査が今の道筋の対応表を引くかを決める。
- **頂上の表の名の重なり(検収 L2)は直した**(§6 L2)。段 6 で resolve を割るときは、表(`_APPLY` など)を割り先のどれか 1 本に置く。

## 6. 別の検収役の指摘と直し(条件つき受入・H 0・M 6・L 5)

検収役の写し(作業木の外)には触っていない。親の byte-check(本体の道具・`--base 3d88da1 --src <作業木の src> --set all19`)は
直す前に 19/19 同じ・終了コード 0。以下は直した形と確かめ方(どれも既定の結果を変えない=最後の byte-check §6-1)。

| # | 指摘 | 直した形 | 確かめ方 |
|---|---|---|---|
| M1 | CP12 の型 `Experiment` は probe の外の状態の digest(行 E の `events._cz_experiments`)で `_qual` に届き、今の名が入る。docstring と §1-2 の「ハッシュにも状態のファイルにも入らない」は probe の分が不正確 | 名を書いてよい `engine/events/log.py` で、クラスの属性 `CLASS_ID: ClassVar[str] = "shibuya.engine.events.log.Experiment"`(dataclass の欄にならない)に凍結の名を宣言し、`class_id` が表の次に読む。`class_ids.py` は何も import しない(輪は無い)。CP12 の門と門の許す置き場は変えていない。道具は AST で宣言を見つけて表から外し、凍結の JSON に入れる。docstring と §1-2 を直した | `test_cp12_type_keeps_its_frozen_name_on_the_probe_path`: `probe.snapshot` の行 E の値と `item_digest` が置き場を動かしたふりでも同じ・代わりの digest(`X:`)に落ちていない・名がバイトに入る。負の対照=宣言を外すと `shibuya` の置き場では止まり(probe は `X:` に落ちる)、`shibuya` の外では digest が動く。CP12 の門の試験は通る |
| M2 | 表に無い `shibuya.*` のクラスでも `class_id` が止まらない(`namedtuple`・`Enum(…)`・`type()`・`make_dataclass` で後から足すと網羅の試験を素通りする) | `class_id` は表 → 宣言の順に引き、どちらにも無い `shibuya` の型を `TypeError` で止める(止める口 `_unknown`)。`shibuya` の外の型・試験の中の型・構築の段 `shibuya.build` の型(表に載せない・動かさない)は今の名のまま | `test_unknown_shibuya_types_stop_and_others_keep_their_names`(`type()` の型・名前つきの組が止まる・numpy・試験の中・構築の段は今の名)。`test_default_run_resume_and_probe_meet_no_unknown_shibuya_type`: 止める口を数える口に替え、30 体・2 日・750 で止めて再開のランと、probe つきの 60 体のランを回す=0 件。範囲の試験(§4)も通る |
| M3 | 凍結の JSON が名の集合なので、値どうしの入れ替え(`ActivityKind` と `AgentKind`)が通る | 凍結の JSON を「凍結の名 → `__qualname__`」の写像にした(481 行)。道具は全行で値の末尾が鍵のクラスの `__qualname__` かを確かめる | `test_frozen_json_maps_each_value_to_the_qualname_of_its_class`(全行で末尾が `__qualname__`・写像が同じ)・`test_swapping_two_values_is_caught`(入れ替えは名の集合では通り、写像と末尾の確かめで落ちる) |
| M4 | 2-1 の凍結は手で選んだ一覧で、manifest に入る道の形の名が漏れていた(`HD-engine.energy-cc73b60c`・`core.rng.philox_array(seed, …`・`engine/energy.py の見出しの項`) | 6 つの短いラン(合成 2・世界資産 4=既定・古典+記憶+関係・v1 の辺と PLATEAU の旧・腕 7 変数)を子のプロセスで回し、manifest・run_meta・テープの Parquet の見出し・ハッシュに入る文字列(`state_hashes._str` に渡る名と値・外の状態の行の `鍵:道筋`)から、点の道と斜線の道の部分を拾う(`tests/engine/state/shaped_names.py`。頭の部品は今の包み 11 と移した後の包みの名=固定の一覧・日本語の文に埋まっていても ASCII の名の境で拾う)。構成ごと・拾う所ごとに凍結(74 種=§6-2) | `test_run_outputs_contain_exactly_the_frozen_path_shaped_names`(6 構成・世界資産の 4 つは data が要る)・`test_shaped_pattern_finds_both_forms_inside_japanese_text`。突然変異: 写しの木で `HD-engine.energy-` を `HD-world.body.energy-` に書き換えると、合成の既定の構成で「新しい `world.body.energy`・消えた `engine.energy`」で落ちた(スクラッチで確かめて消した) |
| M5 | `tools/bytecheck/tree.py` の `scan_root_anchors` が `find_upward`・`PACKAGE_ROOT`・`module_dir` を数えない | 呼び出しの名 `ROOT_CALLS` に `find_upward`・`module_dir` を、名 `ROOT_NAMES` に `PACKAGE_ROOT` を足し、属性の形(`P.REPO_ROOT`)と `for … in (start, *start.parents)` の形も数える。`ROOT_READERS` に 3 行(`engine/bridging/scan.py`・`engine/systems/allow.py`・`engine/systems/static_check.py`=どれも src の中を読むだけ)を足した | `tests/tools/test_bytecheck.py::test_root_scanner_counts_the_paths_helpers`: 突然変異(`find_upward` と `module_dir` で読む関数・`PACKAGE_ROOT.parent.parent` で読む関数・`P.REPO_ROOT`・`(start, *start.parents)` の for)を足した木で全部見つかる(前の数え方では 4 本とも見落とす)。`test_root_reader_files_are_declared` も通る |
| M6 | `state_codec.allowed_class` の `qualname(obj) != name` に振る舞いの試験が無い | 試験を足した(コードは変えない) | `test_allowed_class_refuses_a_path_that_points_to_another_class`: `_PATH_OF` を別のクラスへ向けると `allowed_class` と状態のファイルの読みが `StateFormatError` |
| L1 | 道の形の名と塩の凍結は「値が src のどこかにあるか」だけ(`\x1fengine` は 2 か所で、片方だけ書き換えても通る) | 道の形の乱数の領域の名・接尾・ほかの名は、ランの側の src の定数に出てくる数を凍結(`\x1fengine` 2・`engine.processes.rail` 5 ほか) | `test_path_shaped_rng_domains_are_kept_by_value_and_count`・`test_other_path_shaped_names_are_kept_by_value_and_count` |
| L2 | `allow.index` の重なりの検査は頂上の関数の名だけ | 頂上の表の名(関数を指す代入)もファイルをまたいで重なれば止める(1 本のファイルの中は前と同じ) | `test_index_refuses_a_table_name_split_across_files_and_merges_distinct_ones`(`_APPLY` の重なりで止まる・別の名なら 2 本を 1 つの閉包にして `_APPLY` は前と同じ) |
| L3 | `module_dir` は `__main__` のとき包みの根を返す | §2-2 に書いた | — |
| L4 | 古い記録の道具が暦の暗黙の再輸出で動いている | 書き換えない。§5 に「段 4 で壊れるもの」として書いた | — |
| L5 | カード `data.md` の揺れ | 何もしない(親がカードを作り直す) | — |

### 6-1 直した後の byte-check

`python tools/bytecheck/cli.py run --base 3d88da1 --work <短い作業の置き場> --out-dir docs/bench/analysis/move-346/bytecheck/review_fix --set all19 --jobs 6`

- **19 構成・37 欄すべて同じ 19・一部を比べていない 0・動いた 0・誤り 0・final が同じ 19 → 終了コード 0**
  (基準の側 210 秒・比べる側 202 秒・全体 413 秒)。
- 出力 3 本: [bytecheck/review_fix/](bytecheck/review_fix/)(compare と両側の side。道筋は道具の決まりどおり `<home>` などに伏せてある)。
- 作業の置き場はつなぎが残っていないこと(`dir /AL /S` で 0 件)を確かめてから消した。

### 6-2 ランから拾った道の形の文字列(凍結 `run_path_shaped`・74 種)

拾う所ごと。「一部」は一部の構成だけに出るもの(括弧の中が出る構成)。元の文の例は代表の 1 つ。

| 拾う所 | 道の形 | 出る構成 | 元の文の例・どこから |
|---|---|---|---|
| manifest | `engine.energy` | 全部 | `HD-engine.energy-cc73b60c`(`engine/body/rules.py` の体の規則の表=つなぎの台帳の行の ID) |
| manifest | `engine/energy.py` | 全部 | 「…(`engine/energy.py` の見出しの項)」(同じ表の根拠の文) |
| manifest | `core.rng.philox_array` | 全部 | 「`core.rng.philox_array(seed, 'proximity.notice', …)`」(`engine/proximity.py` の f 文字列) |
| manifest | `engine/systems/talk.py` | 全部 | 欠陥 4 件の切替口の文(会話の終わり) |
| manifest | `agents.poi_ref`・`world.pois.cell` | 全部 | 在席の印の文「`agents.poi_ref`(在席中の POI の区画 id)∧ 体のセル == その POI のセル(`world.pois.cell`)」 |
| manifest | `world.cells.density_stage` | 全部 | nav1 の密度の段の文 |
| manifest | `economy.stage2` と `economy.stage2.*` 23 個(`arm`・`atms`・`calls`・`credit`・`deposit`・`deposit_mean`・`endow`・`expedients`・`external_sales`・`faucet_sink_by_cell`・`faucet_sink_registry`・`hours_source`・`parts`・`payday_day_of_month`・`payment`・`plan`・`rules`・`tax`・`wages`・`wallet`・`wallet_mean`・`wallet_zero`・`withdraw`) | 全部 | manifest の欄を節に分ける表 `manifest_sections`(欄の道筋) |
| manifest | `economy.raw_*` 6 個・`economy.transfer_events`・`economy.transfers_amount`・`economy.transfers_total`・`economy.transfers_uncaused` | 全部 | 同じ表 |
| manifest | `shibuya.*` の版の ID の頭 19 個(`shibuya.absent_processes`・`shibuya.calendar_shadow`・`shibuya.defect_fixes_1103`・`shibuya.engine`・`shibuya.engine.batching`・`shibuya.engine.body`・`shibuya.engine.decision`・`shibuya.engine.resume`・`shibuya.engine.speech`・`shibuya.engine.tools`・`shibuya.perception`・`shibuya.proximity`・`shibuya.rate_rules`・`shibuya.space.nav1`(世界資産の 4 構成)・`shibuya.calendar_self`・`shibuya.engine.calendar2`・`shibuya.engine.calendar3`・`shibuya.engine.contact`・`shibuya.engine.duties`(腕 7 変数の構成だけ)) | 全部か一部 | 版の ID(`…/1` など。§2-1 の `version_ids` にも入っている) |
| manifest | `engine.rights.initial` | 一部(合成 2) | 権利台帳の初期の行の出どころ |
| manifest | `agents.weekly.WEEKLY_FILE` | 一部(合成の全腕と古典) | 週次表の読み口の定数の名の文 |
| run_meta | `shibuya.engine.resume` | 全部 | 環境の欄の版 `shibuya.engine.resume/environment/v1` |
| tape_meta | `shibuya.tape`・`shibuya.tape.schema` | 全部 | テープのスキーマの版と metadata の鍵 |
| hash | `shibuya.core.types.EventClass`・`shibuya.engine.arbiter.WakeCandidates`・`shibuya.engine.scheduler.DeferralQueue`・`shibuya.perception.p_notice.Counters`・`shibuya.perception.p_notice.EventBudget` | 全部 | クラスの凍結の名(段 1 の表) |
| hash | `shibuya.economy.ledger.DayClose`・`shibuya.engine.presence.PlanBlocks`・`shibuya.llm.contract.Target`・`shibuya.llm.contract.TargetKind`(世界資産の 4 構成)・`shibuya.engine.activity.ActivityPayload`(v1 の旧の構成を除く世界資産の 3 構成) | 一部 | 同じ |

- 拾いの限界: 拾うのは 6 構成の 1 日以内の短いランに出る文字列だけ(19 構成の残り・ほかの腕・2 日以上・艦隊の道は見ていない)。
  検収役が src の走査で見つけた「日本語を含み manifest に入るか確かめられていない 43 本」のうち、この 6 構成の manifest に出たのは
  上の表の文(`engine/energy.py の見出しの項` など)で、出なかったものはこの拾いでは守れない(段 3 の道具の除外の一覧には、src の
  文字列の定数のうち道の形を含むものを全部入れる案=段 3 で決める)。
- ハッシュに入る文字列のうち `state_hashes` を通らないもの(SoA の `state_hash` の列の名・`blake3_hex` に直に渡す塩)は拾っていない。
  塩の語は §2-1 の `\x1fengine`(数つき)で守る。

## 7. 再検収と親の検収(親が書いた)

### 7-1 同じ検収役の再検収(条件つき受入・H 0)

- 閉じた: M1・M2・M3・M5・M6・L1・L2(L3・L4 は本書に記録、L5 は何もしない)。直す前の版で通っていた突然変異 6 件(値の入れ替え・
  読み込みの型の確かめを効かなくする・塩の片方だけの書き換え・新しい手伝いの関数で根を読む 2 件・乱数の用途名の呼ぶ側だけの書き換え)は、
  直した後の版で全部落ちた。前から落ちていた 8 件と新しく足した 6 件(宣言を消す・宣言の値を 1 文字変える・つなぎの台帳の ID の書き換え・
  proximity の f 文字列の書き換えほか)も全部落ちた(20 件)。
- 新しく壊したものは無い: 止める口(M2)を数える口に替えて tests/c7 と tests/engine/state を除く全体を回し(艦隊の道を mock と偽の vLLM で通る
  範囲を含む)、表に無い型は 0 件。`dataclasses.fields(Experiment)` は前と同じ `cond_id` だけで、実験の記録の状態の digest も基準の src と同じ。
- **閉じていない M4 の残り**: 6 構成の外の腕 `SHIBUYA_TALK_CLOCK=mora` の manifest に、凍結に無い道の形の名 `engine.speech.port.mora_count`
  (`engine/speech_clock.py` の `mora_rule` の文)が出る。この腕は byte-check の 19 構成にも入っていない。ランの側の src の文字列の定数のうち
  道の形を含み凍結に無いものは 472 本(うち 378 本は段 3 の道具がわざと直す道の表 3 本=state_ledger・state_ledger_ast・rng_audit)。
  → **親の決定**: 段 3 の道具は、許可の一覧(import の文・§7-5 で「段 3 の道具で直す」とした道の表・固定の表の鍵)だけを書き換え、
  それ以外の文字列の定数は書き換えない。これで残りは段 3 で閉じる(段 3 の試験で、許可の一覧の外の定数が 1 つも変わらないことを確かめる)。
- 残る L: L-a 同じ `__qualname__` を持つクラスが 4 組ある(`Arbiter`・`GoodsLedger`・`Renderer`・`Scheduler`)。組の中で値を入れ替えると
  写像の試験も末尾の確かめも通る → 段 3 の道具が鍵を書き換えるとき、新しい鍵が対応表で古い鍵に戻り、その値が古い鍵の凍結の名と同じことを
  確かめる。L-b `from shibuya.core.paths import REPO_ROOT as R`・別名の import・`getattr` の形は `scan_root_anchors` が数えない
  (docs と data の道は `scan_path_refs` が別に拾う)=限界として記す。L-c probe の外の状態の digest では、表に無い型の `TypeError` を
  受け口が拾い代わりの digest に落ちる(behavior-hash・full-hash・状態のファイルでは止まる・今は 0 件)=限界として記す。
- 確かめていない(空欄): slow と gpu の試験を止める口つきで回すこと・段 4 の後に版をまたいで probe を比べること・472 本のうち mora の
  1 本のほかが出力に届くか・記憶の m1 と暦 1b の腕の拾い。

### 7-2 親の検収

- byte-check(本体の道具・`--base 3d88da1 --src <作業木の src> --set all19 --jobs 6`): 直す前も直した後も
  **19 構成・37 欄すべて同じ・動いた 0・誤り 0・final 同じ 19・終了コード 0**。
- 範囲の試験で作業木だけで落ちる `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` は、
  本体では通る。作業木では data が本体へのつなぎなので、テープの置き場の道がリポの根の相対にならず、道の相対化の 1 行だけが落ちる
  (数の確かめは全部通る)=移す段の変更と関係しない。
- commit は 3 つ+本書: 段 1(段 1 の新しいファイルは CP12 の型を外した版で入れた=途中の commit で CP12 の門の試験が落ちないように。
  段 2 はクラスを足していないので段 1 の時点でも表の試験は通る)・段 2・検収の直し。各 commit の木は、直す前の写しと直した後の作業木に
  1 バイトも違わない(カードを除く)。
- 実装役の確認待ち 5 点への親の判断: (1) `tools/bytecheck/tree.py` の直しは受け入れる(検収の指摘への直し)。(2) `\x1fengine` と
  74 種の凍結は受け入れる。(3) 全ファイルの表の行 91a・143a は受け入れる。行 224a(`engine/removed_switches.py` の置き場)は段 4 の前に
  決める問いに入れる(段 3 の道具は保留の行として動かさない)。(4) 表と凍結の道具は記録の下に置いたままにする(段 3 で `tools/pkgmove/` に
  寄せるかは段 3 の役が決めて書く)。(5) `CLASS_ID` の形は受け入れる。
- **段 4 の前に決めること(追加)**: つなぎの台帳の `declared_in`(398 行)の扱い。(a) 台帳の道筋を直す(manifest の `bridges_version` が動く
  =1 バイト不変の段の中の既知の例外として記録) (b) 台帳は今の道筋のまま残し、台帳の試験と走査が対応表を引く(manifest は動かない)。
  親案は (b)(返事その 7 の「すべて 1 バイト不変」を守る)。ユーザーの判断に出す。
