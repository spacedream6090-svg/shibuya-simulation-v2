# 段 4 の下ごしらえ: 試験の側(コードの区分の移動・返事その 7 §4-2)

> 段 4(ファイルを移す段)の前に、**ファイルを移すと落ちる試験を、移す前でも移した後でも通る形に直した**。src は 1 バイトも
> 変えていない(`git diff --stat -- src` は空)。本体の木のファイルは 1 本も動かしていない(移したのは git の外の写しの木だけ)。
> 発注: 親の発注文(試験の役)・親の決定(段 4 の下ごしらえ・2026-11-11)の 3・4・5・10・検収の途中の指摘への親の裁定
> (11-11 01:25)の L-7。計画: [最終の表と移す段の計画](../../../reference/package-map-final-2026-11-09.md) §7-4・§7-5。
> 段 1・段 2 の記録 [move-346](../move-346/README.md)、段 3 の記録 [pkgmove-346](../pkgmove-346/README.md)(§5-4 の 80 本と類 A〜E)。
> 土台 `f5426de`(枝 `stage/prep4`)。実装役 Opus 5.5。commit とタグは親。

## 0. 要点

- **直したもの**: 試験と試験の補助 46 本・表を作る道具 `gen_class_ids.py`・新しい試験の補助 2 本(`tests/_head_copy_pin.py`・
  `tests/_places.py`)・新しい試験 1 本(`tests/test_places_guard.py`)。§1-0。
- **検収(条件つき受入・H 0・M 2・L 3)の後の直し**: M-1 固定の写しを字面・文の順・意味の 3 つで固定(§1-1・§6-1)、M-2 対応表を
  読む所で表を確かめる(§1-7)、L-1 解けない `shibuya.` の名を層の試験の違反に(§1-7)、L-2・L-3・前からの穴 M63 の記録(§8)。
- **移す前**(作業木): 範囲の試験は **2 failed・6,720 passed**。落ちたのは発注の 2 本だけ(前からの 1 本と `allow --check`)(§3)。
  検収の後の直しの後は、変えた試験のファイル 44 本を回して 941 passed。
- **移した後**(foundation だけを当てた写しの木): 予行で落ちた 81 本(80 本+前からの 1 本)のうち **68 本が通る**。落ちたのは
  類 B 12 本(つなぎの台帳=道具の役)と前からの 1 本だけ(検収の後の直しの後に、写しを作り直して回し直しても同じ)。範囲の試験は
  20 failed・6,690 passed。落ちた 20 本は類 B 12・前からの 1・道具の試験 `test_pkgmove.py` 7(移す前の git の木が前提)(§4)。
- **全段を当てた写しの木**(先回りの確かめ): 道具の役の src の直しが 2 つ要る(M-1 の循環・決定 3 の `cli.py`)。その代わりを写しの木
  だけに当てると、直した試験のファイル 50 本は、つなぎの台帳 15・前からの 1・道具 repo_guide の道 2 のほかは通る(§5・§7)。
- **突然変異**(1 本ずつ順に): 移す前の木で 39 件中 38 件が期待どおり(残る 1 件は同値の変異で、替えた 2 件は落ちる)・全段の木で
  35 件中 35 件が期待どおり(§6)。検収の後の確かめは、固定の写しの形 16 件が 3 つの木でどれも期待どおり・対応表と解けない名の
  変異 7 件がどれも落ちる(§6-1)。
- 包みの名とディレクトリを字面で持つ試験は、**元の置き場**(対応表 `tools/pkgmove/map.toml` で引く・移す前の木では今の置き場と同じ)で
  範囲を決める形にした(`tests/_places.py`=親の裁定 L-7)。移す前の木では、15 の包みでファイルの集合とモジュールの名の集合が
  前の字面と同じことを確かめた(§2-2)。
- **第 2 回**(§10・取り込みの作業木): 再検収 M-3(表に無い `.py` で範囲の試験の全体が収集で止まる)を直し、全段の木で落ちる試験の
  残り(類 I・E・D・B・H=`tools/c8`)を直した。範囲の試験は、移す前の木で 2 failed(前からの 1・道具の試験 1=§10-7)・6,750 passed、
  foundation・world・runtime・全段を当てた木で、どれも前からの 1 本だけが落ちる。ほかの段の木では落ちた試験のファイル 44 本が全部
  通る。突然変異 46 件(期待を決めた 44 件は全部期待どおり)。
- **第 3 回**(§11): 再検収 M-4(移した後に keep の行で足したファイルが範囲から黙って外れる)を、old と new が同じ行の集合の固定と
  「新しいファイルの行は move の形」の決まりで閉じ、写しの 2 か所が同じ答えを返すことを試験で固定し、宣言の道の引き方(L-6)と
  元の道の重なり(L-7)を直した。変えた試験は作業木と全段の木でどちらも 231 passed・突然変異 22 件とも期待どおり。

## 1. 直した試験

### 1-0 変えたファイル

追跡ファイル 47 本(試験と試験の補助 46=うち補助は `scenes.py`・`head_copies.py`・`rights_writers.py`・道具 1=`gen_class_ids.py`)と
新しいファイル 4 本(`tests/_head_copy_pin.py`・`tests/_places.py`・`tests/test_places_guard.py`・本書)。触ってよい道の外(src・tools・ほかの docs・
カード・`tests/tools/test_pkgmove.py`・`tests/engine/bridging/**`)は変えていない。

### 1-1 類 A(古い commit の写しを sha で固定した材料・53 本)=親の決定 10

〔検収 M-1 の後に改めた形・親の裁定の M-1〕最初の版(import の文の行を取り除いた残りの sha256+置く名の並び)は、import の行の注・
文の順と位置・別名の入れ替え・別名はそのままで読む名だけ替える形・名を別の文へ移す形を止めなかった。今の形は次の 3 つ。

| ファイル | 直し方 | 保たれていること |
|---|---|---|
| 新 `tests/_head_copy_pin.py` | **字面** `text_sha256`: AST で見つけた `shibuya` を読む import の文(関数の中も・相対の import は除く)を取り除かず、その位置に印の行を残す。隣り合う文(間に空行か注だけ)は束にまとめ、束ごとに「字下げ・空行の数・置く名を並べた一覧・束の中の注(行末・括弧の中・文の間の注の行)を並べた一覧」を 1 行に書く。その全体の sha256。文の行に別の文が同居していれば止める。**文の順** `statement_names`・`order_problems`: 束の中で、元の文ごとの置く名の組が元の順に並ぶ(1 本の文が 2 本以上に分かれてよく、分けた文どうしの順は問わない)。**意味** `refs`・`ref_problems`(写しを読み込んだ後): 置いた名ごとに、指す物の元の置き場(`tests/_places.py` の対応で今 → 元)。モジュールは元のモジュールの名、関数とクラスは(元のモジュールの名, `__qualname__`)、ほかの値は(文が読むモジュールが包みの頭でなければその元の名, 値の `repr` の sha256 の頭 16 字。集合は要素の `repr` を並べて書く)。固定の表の名は `shibuya.` を外して書く(移す道具に書き換えさせない) | 字面: 束の外の全部のバイト(行の並び・改行を含む)と、束の位置・字下げ・空行・置く名・注。文の順: 元の文の順と、名がどの文に属したか。意味: 置いた名が指す物(元の置き場で)。**覆わないもの**(〔再検収 L-4〕で書き足した): 読むモジュールの道・1 本の文を分けたときの分け方と分けた文どうしの順(段 4・段 5 で移す道具が書き換える所)のほかに、束の中の注の置き場(どの行・どの名に付くか。注の中身の一覧は覆う)・束の中の空白だけの行の空白(空行の数は覆う)・文の改行と括弧の付け方・文の形(`from P import m as x` と `import P.m as x` のように、置く名と指す物が同じになる書き方の違い)。限界は §8-1 の 6 |
| `tests/perception/facts/scenes.py` | `HEAD_RENDERER_SHA256`(全体)→ `HEAD_RENDERER_TEXT_SHA256`・`HEAD_RENDERER_ORDER`(1 束 10 文)・`HEAD_RENDERER_REFS`(29 の名)。`head_module()` は読む前に字面と文の順、読んだ後に意味を確かめる。元の全体の sha256 は注に残した | 同上。写しのファイルは 1 バイトも変えていない |
| `tests/economy/cp2/head_copies.py` | `BLOBS`(git の blob の名)→ `PINS`(改行を LF に揃えてから、字面・文の順・意味)・`pin_problems()`。元の blob の名と全体の sha256 は注 | 同上(LF に揃えるのは前の blob の名と同じ) |
| `tests/economy/cp2/test_cp2_nine_ops_equivalence.py` | `test_the_copies_are_the_head_blobs` が写し 2 本を読み込み、`pin_problems` が空(写しの名の集合も固定) | 写し 2 本が HEAD 136fdbb のバイトのまま(上の「覆わないもの」を除く) |
| `tests/perception/facts/test_render_from_percept_bytes.py` | docstring の注だけ | — |

写しの 3 本(`head_renderer_136fdbb.py`・`head_goods_136fdbb.py`・`head_ledger_136fdbb.py`)は書き換えていない(import の文は段 4 で道具が
書き換える)。foundation を当てた写しの木で、写しの import の文が書き換わっても固定は同じ値(§4)。

### 1-2 類 C(凍結の名を今の置き場として使う・4 本)

| ファイル | 直し方 | 保たれていること |
|---|---|---|
| `tests/engine/state/test_class_ids.py` | CP12 の型の今の置き場 `EXP_PATH` を型の `__module__` から作り、凍結の名 `EXP_ID` と分けた(網羅・凍結の JSON の確かめは `EXP_PATH` で src の AST の名と突き合わせる)。値の入れ替えの試験・`allowed_class` の M6 の試験・動かしたふりの試験は、凍結の名から `class_path()` で今の置き場を引く | 宣言するクラスは CP12 の型 1 つだけ・凍結の JSON=表の値と宣言の値の写像・別のクラスを指す道で止まる(M6)。凍結の名の字面(`EXP_ID`・状態のファイルに入る名)はそのまま |
| `tests/engine/test_state_format_10f.py::test_u3_value_class_fields_match_the_class` | 凍結の名 → `class_path()` → モジュールの `__file__` のファイルを読む(前は凍結の名から src の道を作った) | 値のクラスの欄の一覧=クラスの AST の属性 |

### 1-3 類 D(道具が触らない形の道・名・8 本)と親の決定 4

| ファイル | 直し方 | 保たれていること |
|---|---|---|
| `tests/engine/time/test_t0_time_consts.py` | `shibuya.` の無い点の名の文字列で `import_module` していたのを import の文に(道具が書き換える)。`scheduler` は包みの頭が同じ名の関数を再輸出しているので `HORIZON_TICKS` を直に読む | 10 のモジュールの定数が同じ値 |
| `tests/engine/test_salt_seed_split_10f.py` | `_rng_aliases` の名の部品(`rng`・`core`・`core.rng`)を `RNG.__name__` から作る | 別名の import と名前つきの用途名を拾う走査 |
| `tests/engine/memory/test_m0_store_schema.py` | 読んでよい層・いけない層を `_places` の元の置き場で決める(前は包みの名の表 `("engine", …, "core")` と `("shibuya.economy", …)`)。読むモジュールは「`from P import 子のモジュール` は子」。器のファイルはモジュールの `__file__`。「表のモジュールと同じ名のディレクトリが無い」もモジュールから | 器が engine・perception・llm・agents・world・core の層だけを読み、economy・census・build を読まない |
| `tests/engine/decision/test_j0_port_schema.py` | 読むファイルを `P.__file__`・`PS.__file__` から(前はディレクトリの道の結合) | 提示の文に数字の例が無い・実装に `choose` の上書きが無い |
| `tests/engine/experiment/test_x33_form.py` | 実験のコードのファイルを `_places` の元の置き場(実験の包みの直下)で引く。主なモジュール 6 本(`gate` を含む)が範囲に入ることを確かめる | 実験のコードに地名と業種名が無い(範囲は移す前と同じファイル) |
| `test_md23_w9_window.py`・`test_md23_tool.py`・`test_version_bump_10e.py` | **試験の側は直さない**(親の決定 7)。記録の道具の import の文を道具が書き換える形を写しの木で模すと(§4・§5)、3 本とも通る=試験の側に直す所は残らない | — |

### 1-4 類 E(試験の中で作った木・差し込むコード・3 本)

| ファイル | 直し方 | 保たれていること |
|---|---|---|
| `tests/tools/test_bytecheck.py::test_root_scanner_counts_the_paths_helpers` | 作る木の根の道のモジュールの置き場と import の文を `PATHS.__name__` から組み立てる(親ディレクトリを作ってから書く) | 根の道の手伝いで根を読む読み手を数える(突然変異の試験) |
| `tests/engine/experiment/test_x33_apply.py` | `GATE` を `GT.__name__` から・包みと包みの中の名も分けて作る。差し込むコードを f 文字列で組み立てる。負の対照を 1 つ足した(別の包みの同じ名は数えない)。`pytestmark` の警告の型を型から作る | 口の外の `admit` と表の書き口を見つける・別の物の `admit` を数えない |
| `tests/engine/systems/test_fix_guards.py` | write_permit と guard の包み・名を `__name__` から。差し込むコード(L2・L11・R1)を組み立てる。`test_systems_modules_do_not_bypass_the_box_setattr` の範囲を元の置き場で | 許可を外す口・大域の書き換え・`_WP` の再輸出を見つける |

### 1-5 親の決定 3(頭の再輸出に頼らない)

| ファイル | 直し方 |
|---|---|
| `tests/engine/body/test_body_manifest.py`・`test_body_reserve.py` | `from shibuya.engine import body as B` → 腕の口は `schedule`、`BodyModel` は `model` を直に読む |
| `tests/engine/state/test_move_prep_stage2.py` | `from shibuya.engine import systems as SYSTEMS` をやめ、系の包みの名を定義したモジュール `allow` の包みから作る |

### 1-6 親の決定 5(表を作る道具)

`docs/bench/analysis/move-346/tools/gen_class_ids.py`: 書く先 `OUT_PY` の決め打ちをやめ、`find_out_py()` が `src/shibuya` の下の
`class_ids.py` を探して 1 本だけなら使う(0 本か 2 本以上なら止める)。`--check` は作業木で「同じ」(import で確かめた 480・関数の中の
クラス 1・新しい鍵 0・落とした鍵 0)。

### 1-7 親の裁定 L-7(包みの名とディレクトリの字面)と同じ形の先回り

新 `tests/_places.py`: 範囲を「移す前に包み X にあったモジュール」(元の置き場)で決め、今の名と今のファイルを対応表で引く。包みは、
その包みにある(あった)モジュールを 1 つ import して渡す(包みの名を字面で持たない)。移す前の木では元の置き場=今の置き場。

- 〔検収 M-2〕表を読む所 `origins_from` が、形の名(`shibuya.tools/pkgmove/map/1`)・行が空でない・どの行にも `old` と `kind`
  (`move` は `new` も)があること、**今の木の `src/shibuya/**/*.py` が表の `old` か `move` の `new` に必ず在ること**を確かめ、外れたら
  `PlacesMapError`(試験が落ちる)。どちらにも無くてよいのは 0 バイトの `__init__.py`(段 4 で足す空の頭)だけ。負の対照の試験
  `tests/test_places_guard.py`(空の表・形の名が違う表・読めない表・行の鍵の名が違う表・1 行欠けた表・作った木で表に無いファイルと
  中身のある頭は止まり、0 バイトの頭と move の行は通る)。
- 〔検収 L-1〕`Names.hits(name)`=`has(name)` か、`shibuya.` で始まるのに木のどのモジュールにも包みにも解けない名(`unknown`)。
  層の試験(下の表の `test_cp2_event_links`・`test_single_write_path`・`test_m0_store_schema`・`test_mr65_guards`・`test_runner`・
  `test_nav1_units`・`test_fleet_contract`)の「読んではいけない」は `hits` で見る(前の字面の前方一致が拾っていた、無いモジュールの名
  `shibuya.economy.zz_future` も違反)。

| ファイル | 前の字面 | 直し方 |
|---|---|---|
| `tests/engine/state/test_move_prep_stage2.py:151`・`:191` | `startswith("shibuya.engine")`・`"shibuya.manifest"` | engine の元の置き場のモジュールの今の名(`names_from(RV)`)・`WC.__name__` の包み |
| `tests/engine/systems/test_fix_guards.py:72` ほか | `"shibuya.engine.systems"`+`"guard"` | §1-4 |
| `tests/engine/events/test_e_cause_three_kinds.py` | `LOG_MODULE`・`"shibuya.engine.events"`・差し込むコード 12 形・`ALLOWED` の道 | `EV.__name__` から包みと名・`ALLOWED` はモジュールの `__file__` |
| `tests/engine/rights/rights_writers.py` | `startswith("shibuya.engine.rights")` | 台帳のモジュールの包み |
| `tests/engine/space/test_nav1_units.py` | 包みの名 2 つとモジュールの名 4 つ・`SRC.parents[1] / "calendar2" / "layer.py"` | 元の置き場(llm・engine/decision)+モジュールの `__name__`・calendar2 の層は `__file__` |
| `tests/llm/test_fleet_contract.py` | 包みの名 7 つ | 元の置き場 6 つ+census だけ字面(頭 1 本の包みで段 4 の delete の段で消える) |
| `tests/economy/cp2/test_cp2_event_links.py` | ディレクトリ economy の直下・包みの名 2 つ | 元の置き場(economy の直下・engine/events・llm) |
| `tests/economy/test_single_write_path.py` | ディレクトリ engine の走査・`"shibuya.economy"` | 元の置き場(engine・economy) |
| `tests/engine/body/test_body_guard.py` | `"engine/body/model.py"`・`"engine/body/"` | モジュールの `__file__` |
| `tests/engine/memory/test_mr65_guards.py` | f 文字列の道 `engine/{m}.py`・包みの名 3 つ | モジュールを import・元の置き場 |
| `tests/engine/processes/test_runner.py` | ディレクトリ `src/shibuya/engine/processes`・包みの名 2 つ | 元の置き場 |
| `tests/engine/test_add_at_guard.py` | 対象外 `("economy/", "build/")` の道の中の字面・engine/systems の直下 | 元の置き場(字面の表は残し、元の置き場と同じことを確かめる) |
| `tests/engine/test_state_ledger_10b.py:239` | `startswith("engine/")` | engine の元の置き場のファイルの集合 |
| `tests/c6/test_t3_parallel_invariance.py` | ディレクトリ engine の走査 | 元の置き場 |
| `tests/engine/time/test_t0_no_tick_word.py` | ディレクトリ core と engine/systems | 元の置き場 |
| `tests/engine/systems/test_stage_a_guard.py` | ディレクトリ engine/systems | 元の置き場 |
| `tests/tools/test_repo_guide.py::test_real_public_names_match_import` | `startswith(("src/shibuya/core/", "src/shibuya/engine/systems/"))` | 元の置き場 |
| `tests/tools/test_repo_guide.py` の見本の木(`repo`)と `test_missing_ledger_is_reported` | 本物の道と同じ字面の見本の木(移す道具が一部だけを書き換えた) | 道具 repo_guide が道で読む 5 本は `guide.P` の定数から・ほかは同じ根の下に f 文字列(§8-1 の 5) |
| `tests/engine/test_two_phase.py` | `_HOT_PATHS` の engine/systems の直下 | 元の置き場。0 バイトの頭は宣言の対象の外(§8-1 の 4) |
| `tests/build_rail/test_w12_arrivals_2_3c.py` | `"processes.rail_events"`・ディレクトリ 2 つの有無 | `ERE.__name__`・過程と系のモジュールの `__file__` |
| `tests/engine/calendar2/test_ca2_runs.py`・`calendar3/test_ca3_runs.py`・`duties/test_du_units.py` | ディレクトリ+`"layer.py"` | 層のモジュールの `__file__` |
| `tests/engine/contact/test_c1_fixes.py`・`test_c2_habit.py` | ディレクトリ+ファイルの名の一覧 | モジュールの一覧(保留の 4 本を含む=段 4 で連絡の包みの一部だけが動く) |
| `tests/engine/rules/test_rules_table_schema.py` | `"shibuya.engine.rules"`・`"engine/rules/"`・差し込むコード 6 形 | 表のモジュールの `__name__`・`__file__` から・差し込むコードを組み立てる |
| `tests/engine/test_state_checks_10f.py::test_t4_axis1…` | 偽のファイルの置き場 `engine/processes/fake_behavior.py` | 過程のモジュールのディレクトリ |
| `parse_two_line` を `shibuya.llm` の頭から読む 5 本(`test_j0_mock_equivalence`・`test_wom_from_utterance_roundtrip`・`test_classical_policy`・`test_b6_invite`・`test_speech_on_reaches_addressee`) | 頭の再輸出 | 定義したモジュール `shibuya.llm.parser` から(§5 の M-1 の循環に備える) |

`imported()`(読むモジュール): `import a.b` は `a.b`、`from P import c` は `P.c` が木のモジュールなら `P.c`、そうでなければ `P`。段 4 の
`from <新しい包み> import <移したモジュール>` の形で、新しい空の頭でなく読む子のモジュールで元の置き場を引くため。移す前の木では前の
「`node.module` の前方一致」と同じ範囲か、それより広い(`from shibuya import X` の `X` も見る)。

## 2. 移す前と同じことの確かめ(弱めていないこと)

### 2-1 字面からモジュールで作った名と道

作業木で、新しく作った名と道が前の字面と同じ(24/24。`j0` の 2 本・層のファイル 4 本・連絡のモジュールの一覧 3 つ・記憶の 6 本・実験の
ファイルの一覧・`GATE`・write_permit と guard・乱数の名の部品・根の道の置き場・規則の表の包みと道・偽のファイルの置き場・`ere_tail`・系の
包み・`EXP_PATH`・固定の表が恒等・`class_path` が恒等)。

### 2-2 元の置き場の範囲(`tests/_places.py`)

作業木で、15 の包み(engine・perception・llm・agents・world・core・economy・economy の直下・build・engine/events・engine/decision・
engine/processes・engine/experiment の直下・engine/systems・engine/body)について、`rels_from` のファイルの集合が前の字面のディレクトリの
走査と同じ・`names_from` で当たるモジュールの名の集合が前の字面の前方一致と同じ(15/15)。ファイルの数: engine 174・perception 11・llm 6・
agents 5・world 17・core 12・economy 15・build 79・engine/events 5・engine/decision 6・engine/processes 12・engine/experiment の直下 10・
engine/systems 25・engine/body 5。

## 3. 移す前の試験(作業木)

`pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`(作業木の src・venv は本体):
**2 failed・6,720 passed・1 skipped・1 xfailed**(33 分)。合計 6,724 本は段 3 の記録 §9 と同じ数(試験は足していない。負の対照は
既存の試験の中に足した)。

- 落ちた 2 本は発注の 2 本だけ: 前からの `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(data の
  つなぎ)と `tests/tools/test_pkgmove.py::test_allow_toml_is_current_and_src_tables_exist`(試験を直したので許可の一覧が古くなった)。
- 飛ばした 1 本は前からの Ruri の重み。
- 途中の確かめ: 直した 25 本+5 本(629 passed)・L-7 の 17 本(345 passed)・3 回目の 16 本(234 passed)。`gen_class_ids.py --check` は
  「同じ」。
- 範囲の試験の後に直した 2 本(`test_repo_guide.py` の見本の木・`test_two_phase.py` の空の頭=全段の木で見つけた)は、作業木で
  その 2 本のファイルを回して 53 passed。
- 検収の後の直し(M-1・M-2・L-1)の後: 変えた試験のファイル 44 本(新しい `test_places_guard.py` を含む)を作業木で回して
  **941 passed**(9 分)。範囲の試験の全部は回し直していない(`tests/_places.py` を読むのは変えた試験のファイルだけ)。

## 4. 移した後の試験(foundation だけを当てた写しの木)

置き方: 〔git の作業木の外の置き場〕の写しの木=作業木の追跡ファイル(`git archive HEAD`)に、作業木の変えたファイルと未追跡のファイルを上から写し、
data は本体へのつなぎ。`python tools/pkgmove/cli.py move --stage foundation --apply --tree <写し>`(作業木の道具。当てた行 39・移した 35・
守り 4 つとも「同じ」・書き換えたファイル 466)。親の決定 7 の代わりに、試験が読む記録の道具の import の文を道具の書き換え
(`pkgmove.imports.rewrite_file`)で写しの木だけ書き換えた(foundation の段では `rel8b_measure.py` 3 か所・`multiday_md23.py` 2 か所)。

- **予行で落ちた 81 本**(段 3 の記録 §5-4 の 80 本+前からの 1 本): **68 passed・13 failed**。落ちたのは類 B の
  `tests/engine/bridging/test_bridging_ledger.py` 12 本(道具の役)と前からの `test_ab7_seed1_open_matches_the_parent_report`(data の
  つなぎ)だけ。検収の後の直しの後に写しを作り直して回し直しても同じ(81 本と `test_places_guard.py` 8 本=13 failed・76 passed)。
- **範囲の試験** `pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`: **20 failed・6,690 passed・13 skipped・
  1 xfailed**(32 分)。
  - 落ちた 20 = 類 B 12・前からの 1・`tests/tools/test_pkgmove.py` 7。test_pkgmove の 7 本は、道具の試験が「移す前の git の木」を前提に
    している(foundation を当てた後の木では当てる行が 0・git の外なので `rev-parse` が失敗する)のと、`allow --check`(この役が試験を
    直したので許可の一覧が古くなった=取り込みのときに親が作り直す)。段 3 の予行の木には未追跡の道具が入っていなかったので、この 7 本は
    数えられていなかった。
  - 飛ばした 13 = git が無い 12(test_bytecheck 10・test_state_format_10f 1・test_percept_is_scratch 1)・Ruri の重み 1。段 3 の予行と同じ。

## 5. 全段を当てた写しの木(先回りの確かめ)

置き方: 〔git の作業木の外の別の置き場〕に §4 と同じ写しを作り `--stage all --apply`(当てた行 204・移した 179・守り 4 つとも「同じ」)。
記録の道具の import の文は §4 と同じ書き換え(`rel8b_measure.py` 16・`first_diff.py` 3・`byte_check_10e.py` 4・`multiday_md23.py` 8)。

全段の木は、そのままでは `import shibuya.cli` が落ちる(検収役の M-1=`llm/__init__.py` が `shibuya.act.intake.parser` の名を再輸出し、
移した parser が `shibuya.llm.undefined` を読んで llm の頭を走らせる循環)。さらに world の段で `engine/body/__init__.py` が空になり、
`cli.py:486`・`:1616` の `from shibuya.engine import body as _body` の後の `_body.arm()`・`_body.set_arm()` が落ちる(親の決定 3=道具の役の
src の直し)。この 2 つは道具の役の持ち物なので、**写しの木だけ**に代わりを当てた(`act/intake/parser.py` の `llm.undefined` の import を
関数の中へ・`cli.py` の `_body` を `world.body.schedule` から)。

直した試験のファイル・予行で落ちた試験のファイル・`test_rights_schema.py`(50 本のファイル)を回した結果(検収の後の直しの後に
写しを作り直して回した最後の回):

| 結果 | 数 | 中身 |
|---|---:|---|
| 落ちた・類 B | 15 | `test_bridging_ledger.py`(つなぎの台帳=道具の役。foundation の 12 本に、全段で落ちる 3 本が加わる) |
| 落ちた・前から | 1 | `test_ab7_seed1_open_matches_the_parent_report` |
| 落ちた・道具の側 | 2 | `test_repo_guide.py::test_real_ledger_rows_match_import`・`test_real_write_permits_match_import`=道具 `tools/repo_guide/guide_permits.py:27-31` が台帳と系の表を f 文字列の道(`f"{SRC}/engine/state_ledger.py"` ほか 5 本)で読む。移す道具は f 文字列を書き換えないので、runtime の段の後は本物の木の台帳と系の表を読めない(§7 の 4) |
| 通った | 1,048 | ほかの全部(md23 の 2 本と version_bump の 1 本と `test_places_guard.py` を含む) |

最初の 1 回目で見つけて直したもの(試験の側): nav1 の m5(`SRC.parents[1] / "calendar2" / "layer.py"`=nav1.py からの相対の道)・
`test_add_at_guard::test_systems_modules_have_no_state_ufunc_at`(engine/systems の直下)・`test_single_write_path`(`from shibuya.economy import
<engine 生まれの子>` を economy と見た=`_places.imported` を「読むモジュール」に直した)・`test_two_phase`(空にした頭に宣言が無い=§8-1 の 4)・
`test_repo_guide` の見本の木(移す道具が見本の木の道を一部だけ書き換え、道具 repo_guide の定数と食い違った=見本の木を道具の定数から作る)。

## 6. 突然変異(守りの試験を、わざと壊して落ちることを 1 本ずつ)

1 本ずつ順に(並べて回さない): 写しの木の 1 ファイルを書き換え → その変異を落とすはずの試験だけを `pytest -x` → ファイルを
バイトのまま戻す(戻ったことを確かめる)。道具は〔スクラッチの mutate.py〕。

**移す前の木**(作業木の写し): 39 件・**期待どおり 38**(落ちるはず 37 のうち 36 が落ち、通るはず 2 が通った。残る 1 件 E3 は
同値の変異=下の注)。

| 類 | 変異(落ちるはず) | 落とした試験 |
|---|---|---|
| A | 描画の写しの本文を 1 バイト(docstring の `—` を `-`)・`shibuya` の import の文に名を 1 つ足す/台帳の写しの本文を 1 バイト/物の写しの import の文を 1 本消す(置く名が減る) | `test_render_without_prepare…`・`test_the_copies_are_the_head_blobs` |
| C | 2 つ目のクラスが `CLASS_ID` を宣言・凍結の JSON の CP12 の型の `__qualname__`・`allowed_class` がクラスを確かめない・`CLASS_FIELDS` に欄を足す | `test_table_keys…`・`test_frozen_json…`・`test_allowed_class_refuses…`・`test_u3…` |
| D | `HORIZON_TICKS` を変える・`from shibuya.core import rng as R` で表に無い用途名・器が census を読む・提示の文に数字・`gate.py`(名指し)と `checks.py`(包みの走査)に地名 | `test_module_level_aliases…`・`test_every_rng_domain…`・`test_store_imports_only_allowed_layers`・`test_no_literal_example_numbers…`・`test_no_place_or_business_names…` |
| E | `from <包み> import gate as G` で `admit` を口の外で呼ぶ・write_permit を口の外で import して `set_enabled`・根の道の走査から `PACKAGE_ROOT` を外す/`find_upward` と `module_dir` を外す | `test_admit_and_the_table_writers…`・`test_permit_switches…`・`test_root_scanner_counts_the_paths_helpers` |
| 決定 3・L-7 | `_SYSTEMS_PREFIX` を変える・static_check に engine のモジュールの名の字面を足す | `test_static_check_names_come_from_the_modules` |
| 先回り | 過程が `import …rail_events as X`・規則の表の新しい読み手・記憶の新しいモジュールが perception を読む・`deliver` が `read_ns` を作る・nav1 が `llm.contract` を読む・fleet が engine を読む・`economy/ops.py` が `engine.events.log` を読む・過程が economy を読む・`engine/systems/table.py` が economy を読む・`engine/economy_stage2.py` で世界の状態に `np.add.at`・`engine/systems/table.py` に `prange`・`core/time_consts.py` の注に「tick」・過程が実験の型を `getattr` で読む・体の層の外で `_body_meter` を書く・体の包みの中で名が式の `setattr`(`BODY_DIR` の確かめ)・権利の台帳の内側の名を外から import | それぞれの試験(13 本) |

通るはず(import の文だけを変える): 描画の写しの `shibuya` の import の文を 2 本に分ける・台帳の写しの import の文のモジュールの名を
新しい置き場の名に書き換える → どちらも固定は同じ値で通った(= 固定は import の文の外の全部のバイトと置く名だけを見る)。

最初の版の E3(根の道の走査から `find_upward` だけを外す)は生き残った。試験の a.py が `find_upward` と `module_dir` の両方を使うので
同値の変異(直す前の試験でも生き残る形)。E3b・E3c に替えて、どちらも落ちることを確かめた。

**全段を当てた木**(§5 の写し): 35 件・**期待どおり 35**(落ちるはず 33 が全部落ち、通るはず 2 が通った)。移す前の木の変異を、
移した後の置き場に合わせて当てた(例: `foundation/queues/scheduler.py` の `HORIZON_TICKS`・`from shibuya.foundation import rng as R`・
`foundation/ports/experiment_gate.py` と `experiments/port/checks.py` に地名・`from shibuya.foundation.ports import experiment_gate as G` で
`admit`・`validation/static/system_static_check.py` に engine 生まれのモジュールの名の字面 `"shibuya.runtime.systems.table"`=親の裁定 L-7
の確かめ・nav1 が `foundation.vocab.actions`(llm 生まれ)を読む・fleet が `runtime.systems.table` を読む・`economy/ops.py` が
`foundation.journal.log` を読む・`economy/stage2_bind.py`(engine 生まれ)で世界の状態に `np.add.at`・`foundation/time_consts.py` の注に
「tick」・`world/body/rules.py` で名が式の `setattr`)。

通るはず(範囲が移す前と同じことの確かめ): 器が `economy.stage2_bind`(engine 生まれ=移す前は engine の読み=読んでよい層)を読む・
`experiments/port/run_kind.py`(engine 生まれ=移す前は実験の包みの外)に地名 → どちらも通った(元の置き場で範囲を決めているので、
移した後の包みの名に引きずられない)。

上の突然変異は検収の前の形で回したもの。検収の指摘(M-1・M-2・L-1)で直した所は、次の §6-1 で確かめ直した。

### 6-1 検収の後の確かめ(親の裁定 M-1・M-2・L-1)

**固定の写し(M-1)**: 写しを書き換えた別のファイルを作り、字面・文の順・読み込んだ後の意味の 3 つを固定と比べた(写しの木は
書き換えない。道具は〔スクラッチの pin_probe.py〕)。移す前の木・foundation を当てた木・全段を当てた木で、どれも **16/16 が期待どおり**。

| 形 | 期待 | 落とした固定 |
|---|---|---|
| M36 描画の写しの本文を 1 バイト・M37 台帳の写しの本文を 1 バイト | 落ちる | 字面 |
| M38 import の行の行末に注・M39 括弧の中の行に注 | 落ちる | 字面 |
| M40 隣り合う 2 本の import の文の入れ替え | 落ちる | 文の順 |
| import の文を末尾へ移す・関数の中へ移す | 落ちる | 字面・文の順(関数の中は意味も止める) |
| 2 本の文の別名の入れ替え(`hashes as H`・`normalize as N` → `normalize as H`・`hashes as N`) | 落ちる | 意味 |
| 別名はそのままで読む名だけ替える(`channels as ch` → `templates as ch`・`Retention` → `GrowthRow as Retention`) | 落ちる | 意味(前者は読み込みでも落ちる) |
| 名を別の文へ移す(`World` を world.state の文から world.assets の文へ) | 落ちる | 文の順(読み込みでも落ちる) |
| 束の中に空行を足す・import の文の字下げを変える | 落ちる | 字面 |
| **M41 読むモジュールの道だけを変える**(`blake3_hex` を同じ関数を読み込んでいる別のモジュールから読む) | **通る** | — |
| **1 本の文を 2 本に分ける**(同じ名・同じ位置・分けた文の順は入れ替え) | **通る** | — |
| 限界: 別名はそのままで同じ値の別の定数を読む(`MINUTES_PER_DAY as STEPS_PER_DAY`=どちらも 1440) | 通る | —(§8-1 の 6) |

固定の試験そのもの(`test_render_from_percept_bytes`・`test_speech_on_reaches_addressee`・`test_the_copies_are_the_head_blobs`)は、3 つの
木で同じ値で通った(§3・§4・§5 の回し直し)。

**対応表の確かめ(M-2)**: `tests/test_places_guard.py` の負の対照 6 本(空の表・形の名が違う表・読めない表・行の鍵の名が違う表・
`cli.py` の行が欠けた表・作った木で表に無いファイルと中身のある頭)が止まり、0 バイトの頭と move の行は通る。移す前の木と
foundation を当てた木と全段を当てた木で通った(本物の表は今の木を説明する=移す前の木は全部の `.py` が old、移した後の木で
old にも new にも無いのは 0 バイトの新しい頭だけ)。

**解けない名(L-1)**: `Names.hits` が `shibuya.` で始まる解けない名を違反にする(同じ試験の中の確かめ・作業木と 3 つの木で通る)。

突然変異(1 本ずつ・〔スクラッチの mutate.py〕): 7 件とも期待どおり落ちた。

| 木 | 変異 | 落とした試験(止めた所) |
|---|---|---|
| foundation | 対応表を行の無い表に(検収の P03) | `test_no_parallel_loop…`・`test_engine_does_not_import_economy`・`test_systems_modules_have_no_state_ufunc_at`(`PlacesMapError: 対応表に行が無い`。前は 17/19 が黙って通った) |
| foundation | 行の無い表+engine 生まれの `foundation/journal/log.py` に `prange`(P05) | `test_no_parallel_loop…`(`PlacesMapError`。前は範囲が 174 → 158 に縮んで通った) |
| foundation | 対照: 正しい表+同じ `prange`(P06) | `test_no_parallel_loop…`(engine に並列ループが増えた) |
| 移す前 | 器が `shibuya.economy.zz_future` を読む(M64) | `test_store_imports_only_allowed_layers` |
| 移す前 | engine の `presence.py` が `shibuya.economy.zz_future` を読む(M65) | `test_engine_does_not_import_economy`(前は拾わなかった) |
| 移す前 | nav1 が `import shibuya.llm.zz_future` | `test_engine_does_not_decide_for_the_person` |
| 移す前 | fleet が `from shibuya.zz_future import x` | `test_fleet_module_imports_no_forbidden_layer` |

## 7. 道具の役へ渡すこと

1. **M-1 の循環**: 全段を当てた木で `import shibuya.cli` が落ちる(§5)。この役の試験の側は、`parse_two_line` を `shibuya.llm` の頭から読む
   5 本を `shibuya.llm.parser` から読む形にした(頭から parser の名の再輸出を外す直しに備えた)。同じ形の読み手が試験の外に 3 つある:
   `tools/vocab/registry_from_tape.py:49`(`from shibuya.llm import UndefinedActionRegistry, parse_two_line`=試験
   `tests/vocab/test_registry_from_tape.py` が読む)・`docs/bench/analysis/wallbounce-1003/r86/ab7_sample.py:25`・`ab7_surface_counts.py:15`
   (試験は読まない)。
2. **親の決定 3 の src**: `cli.py:486`・`:1616` が world の段から落ちる(全段の木で 15 本・§5)。`engine/systems/static_check.py:32` の
   `from shibuya.engine import systems as _SYSTEMS` は `__name__` だけを読むので全段の木でも落ちない(新しい空の頭 `shibuya.runtime.systems`
   の名になる=`_SYSTEMS_PREFIX` が今の系の包みを指す)。
3. **親の決定 7 の一覧**: 試験が読む docs の記録の道具は 14 本(`rel8b_measure.py`・`wallbounce-1003/10d/first_diff.py`・
   `wallbounce-1012/10e/byte_check_10e.py`・`md23/tools/multiday_md23.py`・`pop41/tools/stage_pop41.py`・`pop41b/tools/stage_pop41b.py`・
   `pop43/tools/activate_pop43.py`・`refr20b/tools/measure_refractory.py`・`tt23c/tools/activate_tt23c.py`・`vb24/tools/activate_vb24.py`・
   `wave2-2026-09-30/wave2_bytecheck.py`・`move-346/tools/gen_class_ids.py`・`gen_frozen_names.py`・`s2-rules-1101/tools/add_bridges_s2rules.py`)。
   全段で import の文が書き換わるのは前の 4 本(31 か所)。書き換えると、それを読む試験に直す所は残らない(§4・§5)。
4. **許可の一覧 `allow_tests_tools.toml`**: この役の直しで古くなる(`allow --check` が「違う」)。取り込みのときに親が作り直す(発注どおり)。
   この役の直しで、試験の側の多くの道の字面が無くなったので、記号が減る見込み。
5. **道具 `tools/repo_guide` の道**: `guide_permits.py:27-31`(`LEDGER_FILE`・`LEDGER_AST_FILE`・`TABLE_FILE`・`ALLOW_FILE`・`RESOLVE_FILE`
   =f 文字列)と `guide_render.py` の説明の文。移す道具は f 文字列を書き換えないので、runtime の段の後は本物の木で台帳と系の表を
   読めない(全段の木で 2 本落ちる)。この役は見本の木を道具の定数から作る形にした(道具の定数を直せば見本の木も付いていく)。
   道具を直すのは道具の役か親(この役の触ってよい道の外)。
6. **包みの名を書き換えなくなる直し(L-7)の後**も、この役が直した試験は包みの名の字面に頼らない。残る包みの名の字面は §8-2。
7. **`engine/systems/static_check.py` の系の包み**: 全段の木で `_SYSTEMS_PREFIX` は `shibuya.runtime.systems.` になる。系の包みから
   `guard`(→ `foundation/write_guard.py`)・`overrides` と `static_check`(→ `validation/static/`)が出るので、静的の検査が系の関数から
   たどる補助の範囲が変わるかもしれない(確かめていない。この役の試験は `_SYSTEMS_PREFIX` が今の系の包みの名と同じことだけを見る)。

## 8. 先回りで直さなかったもの・判断が要る点

### 8-1 判断が要る点

1. **「economy の包み」「engine の外」などの範囲を元の置き場で決めた**: 段 4 では economy の包みに engine と core 生まれのファイル
   (`rules_bind.py`・`stage2_bind.py`・`wage_formula.py`)が入り、engine のファイルが 10 の包みへ分かれる。この役は、層の確かめの試験
   (`test_cp2_event_links`・`test_single_write_path`・`test_add_at_guard`・`test_m0_store_schema`・`test_fleet_contract` ほか)の範囲を
   **移す前と同じファイル**(元の置き場)に保った。新しい包みで範囲を決め直す(例: 新しい economy の包みは journal を読まない)のは、層の
   決まりそのものを変えることになるので、段 4 の終わりに pyproject の import の決まりを差し替えるときに親が決める。そのときは
   `tests/_places.py` を使う試験の範囲を新しい包みへ移す。
2. **`tests/_places.py` は対応表 `tools/pkgmove/map.toml` を読む**: 道具の持ち物を試験の補助が読む。段 4 が済んで古い置き場が無くなった
   後(段 8 で古い頭とディレクトリを消すまで)は対応表が要る。表の置き場か形が変わるなら、この補助も直す。表が空・古い・形が違う
   ときは、表を読む所が止める(検収 M-2・§1-7)。表に無い `.py` を src に足すと、`_places` を使う試験が `PlacesMapError` で落ちる
   (表を作り直す合図。ほかの試験は走る=〔再検収 M-3〕§10-1)。表に行を足す手順: 全ファイルの表
   `docs/reference/package-map-final-2026-11-09-files.md` に行を足し、`python tools/pkgmove/cli.py map` で `map.toml` を作り直す(手で
   書かない)。`tools/c8/` も同じ表を同じ規則で読む(§10-3-1)。2 か所が同じ答えを返すことは試験で固定した(§11-2)。
   〔再検収 M-4・親の裁定〕**段 4 の終わりに範囲を新しい包みへ移すまでは、新しいファイルの行は move の形で書く**: `old` に
   「移す前の置き場に在ったとしたらの道」(=どの範囲の守りを受けるかを決める道)、`new` に今の道。〔再検収 L-9〕`old` は範囲を
   決める道なので偽らない(そのファイルが受けるはずの範囲の外の置き場=例えば build を書かない。偽った `old` は試験では見分け
   られない)。道が変わらない行(〔再検収 L-8〕move でない行=keep・split・delete・empty と、`old` と `new` が同じ move の行)で
   載せると、元の置き場が今の道になり、元の置き場で決める範囲(層の守り・c8 の漏れの確かめ)から黙って外れる。道が変わらない
   行は、移す前から在って動かない置き場(build・economy の直下など)に足すときだけにし、`tests/test_places_guard.py` の固定の一覧
   `NON_MOVE_ROWS` にも足す(固定の一覧と違えば試験が落ちる=§11-1・§12)。
3. **census の包みの名だけは字面のまま**(`test_m0_store_schema.CENSUS`・`test_fleet_contract`)。census は頭 1 本だけの包みで、段 4 の
   delete の段で消える(残るモジュールが無い)ので、元の置き場から引く物が無い。消えた後は字面の確かめが空回りする(読むモジュールが
   無いので落ちない)。
4. **空にした頭と「逐次ループ宣言」**(`tests/engine/test_two_phase.py::test_every_hot_path_declares_its_sequential_loops`): 親の決定 9 で
   空にする頭(0 バイト)は docstring も消えるので、系の包みの頭(`engine/systems/__init__.py` → `runtime/systems/__init__.py`)が宣言を
   失う。この役は「0 バイトの頭は宣言の対象の外」とした(コードもループも無い。移す前の木の対象に空のファイルは無い=移す前の範囲は
   同じ)。頭の docstring を残す形(決定 9 を変える)を選ぶなら、この行は要らない。移す前の木でも、頭を 0 バイトにすると対象から
   外れる(直す前の試験では落ちた=検収の M62)。親の裁定(L-2): この判断は妥当で、直しは要らない。
5. **見本の木の道を道具の定数から作った**(`tests/tools/test_repo_guide.py`): 見本の木は本物の src の置き場ではなく道具 repo_guide が
   読む形。道具が道で読む 5 本は `guide.P` の定数から、ほかは同じ根の下に f 文字列で置いた(移す道具が書き換えない形)。カードの
   置き場の確かめ(`_card(repo, "src/shibuya/engine")` ほか)は見本の木の形のまま。道具の定数を新しい置き場に直すときは、見本の木の
   ほかのファイルとカードの確かめも一緒に直す(第 2 回で直した=§10)。
6. **意味の固定の限界**(`tests/_head_copy_pin.py`): 値(定数)は元の置き場と `repr` で見るので、同じモジュールの同じ値の別の定数に
   読み替えても(例 `MINUTES_PER_DAY as STEPS_PER_DAY`=どちらも 1440)固定は通る(振る舞いは同じ)。関数・クラス・モジュールは名で
   見るので、読み替えると落ちる。〔再検収 L-5〕潜在の限界がほかに 2 つ(今の写しには無い形): `import shibuya.x`(`as` なし)は置く名が
   `shibuya`(根)になり、意味の固定は根のモジュールを指すだけ(どの子を読んだかは字面の固定の束の中の置く名にも出ない)・包みの頭から
   値を読む文(`from shibuya.x import 値`=`x` が包み)は、値の置き場を「-」と書く(元のモジュールの名を固定しない。頭の再輸出は移す
   道具が定義したモジュールへ向け直すため)。

### 8-2 見つけたが直していないもの(どれも段 4 では落ちない見込み・静的に確かめた範囲)

- 自分で作った木と差し込むコードの中の包みの名(試験の中で閉じている): `tests/tools/test_repo_guide.py` の見本のソース(`LAYER_SRC`・
  `TABLE_SRC` の中の import の文)・`tests/engine/memory/test_mr65_guards.py:60`・`:101`・`tests/engine/processes/test_rate_rules_1101.py` の tmp の木・
  `tests/engine/test_state_ledger_10b.py` の tmp の `engine/fake.py`。
- 移さないファイルを指す字面: `engine/resolve.py`(保留)・`engine/run.py`(保留)・`engine/commit.py`・`engine/change_detect.py`・
  `engine/relations.py`・`engine/tools/registry.py`・`engine/calendar.py`・`engine/arbiter.py`(どれも割る行=段 4 では動かない)。
  `test_fix_guards.py::test_d1_sees_plain_imports_and_other_aliases` の差し込むコードの `shibuya.engine.resolve` も同じ。段 5〜7 で割る
  ときに見直す。
- 道具が書き換える形(許可の一覧の記号の中の道・コードとして読める文字列の import の文): `test_mr65_grain_and_cli.CODE`・
  `test_resume_10d._CHILD`・`test_salt_seed_split_10f` の差し込むコード。全段の木で通る(§5・§10-4)。`test_state_checks_10f::test_t5`
  の差し込むコードは、包みの名だけの `from shibuya.core import rng as R` を移す道具が書き換えない(親の裁定 L-7 の後の道具)ので、
  第 2 回で直した(§10-3)。
- `tests/perception/test_channels.py:52` の `importorskip("shibuya.llm")`(llm の頭は割る行で残る)・`test_w21_stage8_9` の差し込むコード
  (語 `llm` を含むかだけを見る)。
- `tests/c7/` は回していないし、中身も開いていない(発注どおり)。

### 8-3 前からの穴(この役は直していない・親が PENDING に載せる)

- `tests/engine/processes/test_runner.py::test_process_modules_do_not_import_build_or_economy` は `from … import` の形(ImportFrom)だけを
  見る。過程が `import shibuya.economy.ledger` の形で economy を読んでも落ちない(検収の M63=直す前の試験でも同じ)。

## 9. しなかったこと

- src・tools・ほかの docs(`gen_class_ids.py` と本書のほか)・カード・`tests/tools/test_pkgmove.py`・`tests/engine/bridging/**` は
  変えていない。写しの木の src の手直し(§5)は写しの木だけ。
- 試験を消す・skip にする・assert を外すことはしていない。移す前の木で範囲を狭めた試験は無い(§2 で同じ範囲を確かめた)。移した後の
  木で対象から外れるのは、空にした頭の「逐次ループ宣言」だけ(§8-1 の 4=判断が要る点)。
- 写しの木 3 つ(移す前・foundation を当てた・全段を当てた)と、その中の data のつなぎ 3 つは消していない(親が外して消す)。
- commit・git add・タグ・枝の作成・子のエージェントの起動・STATUS/PENDING/IMPLEMENTED/devlog/CLAUDE.md の書き換えはしていない。
- 封印の層・IMPLEMENTED.md ほか発注で開かないとしたものは開いていない。Web は使っていない。pip で何も入れていない。

## 10. 第 2 回(再検収 M-3・L-4・L-5・全段の木で落ちる試験の残り・`tools/c8`)

> 発注: 親の発注文(試験の役 第 2 回・11-11)。置き場は取り込みの作業木(枝 `stage/int`・土台 `54bbf64`。第 1 回の直しと道具の役の
> 最新を親が 1 つの木に合わせた物)。道具の役の一覧 [failing_tests_by_stage.md](../pkgmove-346/round2/failing_tests_by_stage.md)
> (第 1 回の直しを入れる前の木での結果・82 関数)と [pkgmove-346](../pkgmove-346/README.md) §10-6・§10-9 を読んで直した。

### 10-0 変えたファイル

第 2 回で変えたのは 18 本(試験 13・試験の補助 `tests/_places.py`・`tools/c8/` の 2 本・本書・許可の一覧は下)。足したファイルは無い。
触ってよい道の外(src・`tools/pkgmove/` の中身・`tools/repo_guide/`・カード・ほかの docs・`tests/tools/test_pkgmove.py`・
`tests/engine/bridging/**`)は変えていない。許可の一覧 `tools/pkgmove/allow_tests_tools.toml` は試験を直した後に `cli.py allow` で
作り直した(記号 98・ファイル 60。親が入れ替えた後の道具でも `--check` は「同じ」)。

### 10-1 再検収 M-3(表に無い `.py` を 1 本足すと、範囲の試験の全体が収集で止まる)

モジュールの読み込みの時点で `_places` を呼んでいた 3 か所を、試験の中で呼ぶ関数に移した。表の確かめ(`origins_from`)は変えていない
(厳しいまま)。

| ファイル | 直し方 | 保たれていること |
|---|---|---|
| `tests/engine/experiment/test_x33_form.py` | 定数 `EXP_FILES` → 関数 `_exp_files()`(試験の中で呼ぶ) | 実験のコードのファイルの集合と、地名と業種名が無いことの確かめ |
| `tests/engine/processes/test_runner.py` | 定数 `PROCESS_FILES` と頂上の assert → 関数 `_process_files()`(assert は関数の中) | 過程のファイルの集合・書き込み口と economy・build の読みの確かめ |
| `tests/engine/test_two_phase.py` | 定数 `_HOT_PATHS` と頂上の assert → 関数 `_hot_paths()`(`len > 25` は関数の中) | ホットパスの集合・個体数ぶんのループと宣言の確かめ |
| `tests/_places.py` | 表に無いファイルの `PlacesMapError` の文に、表に行を足す手順 `ADD_ROW_HELP`(全ファイルの表 `docs/reference/package-map-final-2026-11-09-files.md` に行を足し、`python tools/pkgmove/cli.py map` で `map.toml` を作り直す・手で書かない)を添えた。`PlacesMapError` の docstring に M-3 の注 | 表の確かめの規則は同じ |

確かめ:
- AST の走査(〔スクラッチの toplevel_places.py〕): 試験のファイルで `_places`・`_head_copy_pin` を関数の本体の外(頂上・クラスの
  本体・デコレータ・既定値)で呼ぶ所は **0**。第 2 回の前の写しでは 3(上の 3 か所)で、走査が拾うことも確かめた。
- 検収役の D01・M59〜M61 と b 版(§10-6)。表に行を足す手順は §8-1 の 2 にも書いた。

### 10-2 記録の書き方(再検収 L-4・L-5)

- L-4: §1-1 の `tests/_head_copy_pin.py` の行の「覆わないもの」に、束の中の注の置き場・束の中の空白だけの行の空白・文の改行と括弧の
  付け方・文の形(`from P import m as x` と `import P.m as x`)を足し、§8-1 の 6 を指した。
- L-5: §8-1 の番号を 1〜6 の順に直した(5 と 6 が入れ替わっていた)。§8-1 の 6 に `refs` の潜在の限界 2 つ(`import shibuya.x`〔`as`
  なし〕は置く名が `shibuya` になる・包みの頭から値を読む文は置き場が「-」)を足した。

### 10-3 全段の木で落ちる試験の残り(類ごと)

道具の役の一覧の 82 関数のうち、第 1 回の直し(§1)で直っていたものは、段を順に当てた木(§10-4)で通った。第 2 回で直したのは次の
とおり(類は一覧の類)。

| 類 | ファイル | 直し方 | 保たれていること |
|---|---|---|---|
| F | `tests/engine/experiment/test_x33_apply.py` | 第 1 回で直し済み(`pytestmark` の警告の型の印を、型の `__module__`・`__qualname__` から作る)。第 2 回は変えていない | 天気の警告だけを無視する |
| G | `tests/engine/body/test_body_manifest.py`・`test_body_reserve.py` | 第 1 回で直し済み(定義したモジュール `schedule`・`model` を直に読む=親の決定 3)。第 2 回は変えていない | 腕の口と体の模型の確かめ |
| I | `tests/build_pop/test_w21_stage8_9.py::test_persona_build_does_not_import_or_call_llm` | (親の裁定)`llm_loaded_by_engine` は True でも False でも通し、注に理由を書いた(段 4 で包みの頭の再輸出を除くと、engine を読んでも llm の頭が読まれなくなる=良い向き)。あわせて、llm の範囲(組み立ての後に読み込まれたかを見る名・呼ばれたかを見るファイル)を元の置き場で決めた。前は名の頭 `shibuya.llm` と道の `shibuya/llm` の字面で、段 4 で llm 生まれのモジュールが `act/intake/`・`foundation/` などへ移ると、黙って範囲から外れた | **組み立ての後に llm 生まれのモジュールが読み込まれていない(`after_build False`)・名の照合で llm 生まれのファイルの関数が呼ばれない(`llm_calls 0`)は変えずに見る**。移す前の木では、範囲は前の字面と同じモジュールとファイル |
| E | `tests/tools/test_repo_guide.py` の `test_ledger_rows_and_owner`・`test_write_permits_from_table`・`test_subdirs_are_sorted`・`test_missing_ledger_is_reported` | 期待の字面と節を、道具 `guide_permits` の定数(`guide.P` の `LEDGER_FILE`・`TABLE_FILE`・`RESOLVE_FILE`)から引く(`_guide_block`)。`test_subdirs_are_sorted` の期待は、見本の木の `src/shibuya` の下のディレクトリそのもの(並べて全部。前の 4 つを含むことも見る) | 台帳の行と持ち主・書きの許可の閉包・下のディレクトリの並び・台帳と系の表が無いときの知らせ。移す前の木では前の字面と同じ期待 |
| E | `tests/engine/state/test_names_frozen.py::test_shaped_pattern_finds_both_forms_inside_japanese_text` | 斜線の道 `engine/energy.py` を 1 つの定数に置き、入力の文(f 文字列=移す道具が触らない)と期待の両方で使う。前は、日本語の文の中の字面と期待の一覧の字面が、移した後に食い違った | 日本語の文の中の点の名と斜線の道を、両方拾う |
| E | `tests/engine/test_state_checks_10f.py::test_t5_static_fifth_word_caller_fails` | 植える 2 本の import を `RA.RNG_MODULE`(`rng` のモジュールの `__name__`)から組み立てる。前の `from shibuya.core import rng as R` は包みの名だけの文字列(親の裁定 L-7 で移す道具が書き換えない)なので、全段の木では植えた `R.stream` の呼び手を検査が拾わなくなっていた(§8-2 を直した) | 5 語目を引く呼び手・静的に決まらない呼び手・4 語以内の呼び手の判定 |
| D | `tests/world/processes/test_declarations_1101.py::test_inputs_existing_five_filled_and_new_seven_fields_only`・`tests/bench/test_refr20b_tool.py::test_gates_outside_table_symbols_are_defined_in_their_files` | src の宣言の文(入力の宣言の `source_rows`・記録の道具の門の出典)は元の道で書いてある(移す道具は記録の文を書き換えない)。src の `.py` の道は、新しい `_places.current_of`(元の道 → 今の道)で今の道へ引いてから、在ること・記号の定義を確かめる | 宣言が指すファイルが在る・門の記号がそのファイルに定義されている。移す前の木では同じ道 |
| D | `tests/engine/test_env_and_sections_10f.py::test_o75_split_flow_dir8_and_coherence_are_diag` | 走査から外すファイルを、ファイルの名(`crowd.py`・`state_ledger.py`。段 4 で台帳は名が変わる)から、群れの過程と状態台帳のモジュールの `__file__` に替えた | `flow_dir8`・`.coherence` を読むのは群れの過程と状態台帳だけ(どちらの名も src に 1 本だけなので、移す前の範囲は同じ) |
| B | `tests/engine/rights/test_rights_from_w16.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/engine/memory/test_mr65_review_fixes.py` | つなぎの台帳の `code_at` は台帳に書いてある道のまま(親の決定 1)。今の道へは `engine.bridging.ledger_paths.current_path` で引き、期待の今の道はモジュールのファイル(`_places.rel_of`)から作る。前は字面の道で、移す道具が書き換えた結果、台帳の道と食い違った | 権利の空欄 2 行が初期化のモジュールを指す・電話の表の空欄の行が表のモジュールを指す・seed の行が組み立ての系を指し、cli を指さない |
| H | `tools/c8/c8lib.py`・`tools/c8/sensitivity.py`(試験 `tests/c8/` の 7 本) | §10-3-1 | §10-3-1 |

試験の補助 `tests/_places.py` に `current_of(old)` を足した(元の道 → 今の道。`.py` だけ・移す前の木では同じ道・今の木に無い元の道は
`KeyError`)。

#### 10-3-1 類 H(`tools/c8/`)

| ファイル | 直し方 |
|---|---|
| `tools/c8/c8lib.py` | `src_origins()` を足した: 対応表 `tools/pkgmove/map.toml` を `tests/_places.origins_from` と同じ規則で確かめ(形の名・行が空でない・今の木の `.py` は `old` か `move` の `new` に在る・在らなくてよいのは 0 バイトの `__init__.py` だけ)、今の道 → 元の道を返す。外れたら `RuntimeError` と、表に行を足す手順(tools は tests を読まないので規則を写した)。`scan_engine_ablation_ids()` の既定の範囲を「元の置き場が `engine/processes` の直下のファイル」と「元の置き場が `engine/presence.py`」に、返すモジュールの名を元のファイルの名にした。`root` を渡したときは前と同じ(ディレクトリの走査) |
| `tools/c8/sensitivity.py` | `engine_read_graph()` の既定(`src_root` なし)で、読み口のファイルを元の道で書き、エンジン側か(`ENGINE_PACKAGES` の表)を元の道の頭の名で決める。`src_root` を渡したときは前と同じ |

保たれていること(発注の条件): **移す前の木で、走査するファイルの集合と出力が直す前と同じ**。直す前と後で、`scan_engine_ablation_ids()`
の 22 の id とモジュールの名と、`engine_read_graph()`(本物の build_manifest)の全部の段の読み口と判定を JSON に書き出し、バイトが
同じ(〔スクラッチの c8_snapshot.py〕)。**移した後の木でも同じ元のファイルを走査する**: runtime まで当てた木と全段を当てた木で書き出しても、
行番号まで同じバイト。台帳 `sensitivity_v1.json` の読み口は元の道のまま(書き換えない)。

### 10-4 範囲の試験(移す前・foundation・world・runtime・全段)

写しの木: 取り込みの作業木の写し(`git archive HEAD`+作業木の変更と未追跡・data は本体へのつなぎ)を〔git の作業木の外の置き場〕に
作り、foundation → world → economy → act → mind → society → runtime → experiments → validation → delete → interim_bundles の順に、
前の段の木の写しへ `cli.py move --stage <段> --apply`。どの段も終了コード 0・終わりの import の確かめで落ちたモジュール 0。**当てた道具は、
親が 11-11 07:18 に入れ替える前の道具**(段の木は 06 時台に作った)。移す前の木の範囲の試験も、入れ替えの前に終わっている(06:57)。

`pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`(木を cwd に・1 本ずつ順に):

| 木 | failed | passed | skipped | xfailed | 時間 | 落ちた試験 |
|---|---:|---:|---:|---:|---:|---|
| 移す前(取り込みの作業木) | 2 | 6,750 | 1 | 1 | 33 分 | 前からの 1・`tests/tools/test_pkgmove.py::test_every_rewritten_path_chain_points_to_a_file_in_the_applied_tree`(§10-7) |
| foundation | 1 | 6,738 | 14 | 1 | 31 分 | 前からの 1 |
| world | 1 | 6,738 | 14 | 1 | 30 分 | 前からの 1 |
| runtime(interim_bundles の前の最後) | 1 | 6,738 | 14 | 1 | 30 分 | 前からの 1 |
| 全段 | 1 | 6,723 | 29 | 1 | 30 分 | 前からの 1 |

- 数は進みの行から数えた(pyproject の `addopts` に `-q` があり、`-q` を足すと終わりの数の行が出ない。〔スクラッチの count_dots.py〕)。
  どの木も合計 6,754 本で、収集の id の数と同じ。木どうしの id の差は parametrize の id の名だけ(`test_body_rules_sources` 3・
  `test_rights_schema` 1・`test_rules_table_schema` 6・`test_fix_guards` 3。id にモジュールの名が入る)。今の取り込みの作業木は、
  入れ替えた後の `test_pkgmove.py` の 7 本ぶん多い 6,761 本を集める。
- 飛ばした試験の理由(`-rs` で回し直した): foundation の木=git が無い 10(`test_bytecheck`)・commit が無い 2
  (`test_state_format_10f`・`test_percept_is_scratch`)・Ruri の重み 1・`test_pkgmove` 1(foundation の段が当たった木=組の片方が
  動く段が無い)。全段の木=それに `test_pkgmove` 15(当てる段が無い木・動かすファイルが残っていない木・空にする頭の行が残って
  いない木)。どれも理由つき。

### 10-5 ほかの段の木(落ちた試験のファイルだけ)

economy・act・mind・society・experiments・validation・delete の 7 つの木で、道具の役の一覧の試験のファイル 41 本と
`test_runner.py`・`test_two_phase.py`・`test_places_guard.py`(44 本)を回した: **どの木も 0 failed・1,033 passed・11 skipped**
(git が無い 10・commit が無い 1)。

### 10-6 突然変異(1 本ずつ順に・〔スクラッチの mut2.py と specs_r2.py〕)

木は、移す前の写し(段の木の s00)と全段を当てた木。写しの木の 1 ファイルを書き換え(新しいファイルは書いて、終わったら消す)→
その試験だけを回す → バイトのまま戻す(戻ったことを sha256 で確かめる)。回したのは 46 件。**期待を決めた 44 件(落ちるはず 38・
通るはず 6)は、44 件とも期待どおり**。残る 2 件(D01)は合否ではなく、落ちた試験とその理由を見た。

| 変異 | 木 | 期待 | 結果(落とした試験・理由) |
|---|---|---|---|
| D01(検収役)表に行の無い無害な新しいファイル(`X = 1`) | 移す前・全段 | 見る | 4 本のファイルの 71 本のうち、範囲を使う 5 本(`test_runner` 2・`test_two_phase` 2・`test_x33_form` 1)だけが `PlacesMapError`(表に行を足す手順つきの文)で落ち、66 本は通った(`test_t0_time_consts` の全部と、範囲を使わない試験) |
| D02 同じファイルで、範囲の試験の全体の収集 | 移す前・全段 | 通る | 通った(収集が止まらない) |
| M59・M60・M61(検収役)表に行の無い新しいファイル(`object.__setattr__`・economy を読む・宣言なし) | 移す前・全段 | 落ちる | `PlacesMapError` で落ちた |
| M59b・M60b・M61b(検収役)同じ+表の行(全段の木では元の置き場 `engine/…` から新しい置き場へ移した行) | 移す前・全段 | 落ちる | 違反そのもので落ちた(箱を通さない書き換え・engine 生まれのファイルが economy を読む・逐次ループ宣言が無い) |
| C8a 過程の感度試験 id を変える | 移す前・全段 | 落ちる | `test_process_ablation_ids_match_source`・`test_scan_engine_ablation_ids` |
| C8b 新しい置き場に、元の置き場が `engine/processes` の過程を足す(id つき) | 全段 | 落ちる | `test_process_ablation_ids_match_source`(元の置き場で拾った) |
| C8c 対照: 同じファイルで、元の置き場が `world/laws` | 全段 | 通る | 通った(置き場の今の名に引きずられない) |
| W21a 組み立てが `shibuya.llm.contract` を import | 移す前 | 落ちる | `after_build True` |
| W21b 組み立てが llm 生まれの `shibuya.foundation.vocab.actions` を import | 全段 | 落ちる | `after_build True`(前の字面 `shibuya.llm` では拾えない形) |
| W21c 対照: 組み立てが core 生まれの `shibuya.foundation.rng` を import | 全段 | 通る | 通った |
| T5m 乱数の検査が `from <親> import rng as R` を見落とす | 移す前・全段 | 落ちる | `test_t5_static_fifth_word_caller_fails` |
| B1・B2・B3 つなぎの台帳の行の道を別のファイルに(権利の空欄・seed の行に cli を足す・電話の表の空欄) | 移す前・全段 | 落ちる | それぞれの試験(AssertionError) |
| G1・G2・G3 道具 repo_guide の下のディレクトリを逆順に・持ち主の無い行を系の口のカードへ・「が無い」の文を替える | 移す前・全段 | 落ちる | `test_subdirs_are_sorted`・`test_ledger_rows_and_owner`・`test_missing_ledger_is_reported` |
| D1 入力の宣言が無いファイルを指す | 移す前・全段 | 落ちる | `test_inputs_existing…`(`current_of` が `KeyError`) |
| R1 門の記号の定義の名を変える(活動層のファイル) | 移す前・全段 | 落ちる | `test_gates_outside_table_symbols…` |
| O1 ほかの src のファイルに `flow_dir8` | 移す前・全段 | 落ちる | `test_o75…` |
| O1b 対照: 群れの過程のファイルに `flow_dir8` | 移す前・全段 | 通る | 通った(外すのは群れの過程と台帳のファイルだけ) |
| N1 `shaped()` が斜線の道を拾わない | 移す前 | 落ちる | `test_shaped_pattern…` |

### 10-7 残った落ちる試験と持ち主

| 試験 | 木 | 原因 | 持ち主 |
|---|---|---|---|
| `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` | 全部 | 前から(data のつなぎ) | 前から(発注で除く 1 本) |
| `tests/tools/test_pkgmove.py::test_every_rewritten_path_chain_points_to_a_file_in_the_applied_tree` | 移す前の木だけ(段を当てた木では foundation の枝を通らない) | 道具の試験が、本物の試験のファイルの中の `/` の結合の道の書き換えを数え(foundation の段で 3 以上)、`tests/economy/cp2/test_cp2_event_links.py` に `src / "engine" / "ledger_api.py"` が在る前提で書いてある。この役の第 1 回の直し(§1-7=範囲を元の置き場で決める)で、その道が試験のファイルから無くなったので 2 本。親が入れ替えた後の `test_pkgmove.py`(840〜842 行)にも同じ前提がある(入れ替えた後の道具と試験で、移す前の木で `test_pkgmove.py` を回し直した=この 1 本だけが落ち、ほかの 46 本は通る) | 道具の役(この役は `test_pkgmove.py` を触れない。試験の前提を、見本の木か道具の側の材料に替える) |

### 10-8 道具の役へ渡すこと

1. 上の `test_every_rewritten_path_chain_points_to_a_file_in_the_applied_tree` の前提(§10-7)。
2. §7 の 1(M-1 の循環)・2(親の決定 3 の `cli.py`)・5(repo_guide の f 文字列の道)は、取り込みの作業木の道具の役の直しで済んで
   いる(全段の木で import の確かめ 0・`test_repo_guide` の本物の木の 3 本を含めて範囲の試験で落ちない)。この役の写しの木の手直し
   (§5)は第 2 回では要らなかった。

### 10-9 判断が要る点

1. **src の宣言の文の道は元の道のまま**(`world/processes/inputs.py` の `source_rows`・記録の道具の門の出典): 移す道具は記録の文を
   書き換えないので、試験は `_places.current_of` で今の道へ引く(つなぎの台帳と同じ扱い=親の決定 1)。段 4 の後に、誰かが**新しい
   置き場の道**で宣言を書くと、`current_of` は元の道として引けずに `KeyError` で落ちる。「今の木に在ればその道・無ければ元の道として
   引く」形にすれば両方を通せる(確かめは「宣言が指すファイルが在る」のまま)。どちらにするかは、宣言の文を新しい道へ書き換えるか
   (道具の役・段 5 以降)と合わせて決める。この役は変えていない。
2. **`tools/c8/` が対応表を読む**: `tests/_places.py` と同じ規則を `c8lib.src_origins()` に写した(tools は tests を読まない)。表の形か
   置き場が変わったら 2 か所を直す。感度試験の台帳 `sensitivity_v1.json` の読み口は元の道で書かれ、出力も元の道のまま(発注の条件=
   出力が変わらない)。段 4 の後に台帳の読み口を新しい道で書き直すなら、台帳のバイトが変わる(親の判断)。
3. §8-1 の 1〜6 は第 1 回のまま(5 は第 2 回で直した=§10-3 の E の行)。

### 10-10 作った写しの木とつなぎ(消していない・親が外して消す)

〔git の作業木の外の置き場〕の下に、第 2 回の段の木 12(s00〜s11=作業木の写しと 11 の段)と、第 2 回の探りの段の木 12(後の直しの
前に作った木)。第 1 回の写しの木 3(移す前・foundation・全段)も残っている。どの木にも data のつなぎが 1 つ(合わせて 27・全部
つなぎであることを確かめた)。

### 10-11 第 2 回でしなかったこと

- src・`tools/pkgmove/` の中身・`tools/repo_guide/`・カード・ほかの docs・`tests/tools/test_pkgmove.py`・`tests/engine/bridging/**` は
  変えていない。試験を消す・skip にする・assert を外すことはしていない(`llm_loaded_by_engine` を両方通すのは親の裁定)。
- 写しの木は段を当てた後に手で直していない(第 1 回の §5 の手直しは第 2 回では要らなかった)。
- commit・git add・タグ・枝の作成・子のエージェントの起動・STATUS/PENDING/IMPLEMENTED/devlog/CLAUDE.md の書き換えはしていない。
  封印の層・tests/c7 ほか発注で開かないとしたものは開いていない。Web は使っていない。pip で何も入れていない。

## 11. 第 3 回(再検収 M-4・写しの 2 か所・L-6・L-7)

> 発注: 親の発注文(試験の役 第 3 回・11-11)。第 2 回の再検収は条件つき受入(H 0・M 1・L 2)。置き場は取り込みの作業木(前と同じ)。

変えたファイル: 試験の補助 `tests/_places.py`・`tests/test_places_guard.py`・`tests/world/processes/test_declarations_1101.py`・
`tests/bench/test_refr20b_tool.py`・`tools/c8/c8lib.py`・本書。足したファイル: `tests/c8/test_places_rule_copies.py`。許可の一覧は
`cli.py allow` で作り直して変わらない(記号 98・ファイル 60・`--check` は「同じ」)。

### 11-1 再検収 M-4(移した後に作ったファイルが、範囲を使う試験から黙って外れる)

検収役の再現(A10〜A12): 全段の木で、表に `old = new = 今の道` の行(keep)を足して新しいファイルを作ると、元の置き場が今の道
(`runtime/systems/…`・`world/laws/…`)になり、`engine/systems` 生まれなどの範囲に入らない。層の守りと c8 の漏れの確かめを通り抜ける。

親の裁定に沿って直した:

| ファイル | 直し方 | 保たれていること |
|---|---|---|
| `tests/test_places_guard.py` | 固定の一覧 `SAME_PLACE_ROWS`(表の `old` と `new` が同じ行と kind が keep の行の道。今の表から数えて 96 行=keep 94〔build 79・economy の直下 14・根の頭 1〕・empty 2〔economy と world の頭〕)と、試験 `test_rows_that_keep_their_place_are_frozen`(表の集合が一覧と同じ。増えたら決まりの文つきで落ち、減ったら一覧からも消すよう求める)。負の対照 `test_a_keep_row_for_a_new_file_is_caught_and_a_move_row_is_not`(keep の行は一覧に当たり、move の形の行は当たらない・どちらの表も `origins_from` は受ける) | `origins_from` と `c8lib.src_origins` の規則は変えていない(表に無いファイルは今のとおり止まる) |
| `tests/_places.py`・`tools/c8/c8lib.py` | 表に行を足す手順の文(`ADD_ROW_HELP`・`PLACES_ADD_ROW_HELP`=同じ文)に、決まり(新しいファイルの行は move の形・keep の行は動かない置き場だけで固定の一覧にも足す)と期限(段 4 の終わりに範囲を新しい包みへ移すまで)を書いた。§8-1 の 2 にも書いた | — |

道具の側の表(`tests/tools/test_pkgmove.py::test_map_toml_is_made_from_the_table_and_is_current`)も行の数と kind ごとの数(keep 94)を
固定している。新しいファイルの行を足すときは、そちらの数も変わる(§11-6)。

### 11-2 規則の写しが 2 か所にある件(写しのまま・同じ答えを固定)

新 `tests/c8/test_places_rule_copies.py`(c8 を読める置き場): 今の木で 2 つの対応が完全に一致する(どちらも `PL.origins()` と同じ・
300 本を超える)・形の名と手順の文と表と包みの置き場が同じ・作った木と表(keep・move・移す前の置き場に在ったとしたらの道の move・
中身のある頭の keep・古い道にファイルが残る move)で同じ答え・同じ悪い表(空・形の名が違う・読めない・行の鍵が違う・move に new が
無い・1 行欠けた=古い)でどちらも止まる・表に無い中身のある頭でどちらも止まり、0 バイトの新しい頭はどちらも受ける。

そのために `c8lib.src_origins(map_path=None, pkg=None)` に表と木を渡せるようにした(既定は本物の表と `src/shibuya`)。あわせて、写しの
止まり方を `_places` に揃えた(読めない表・行が表でない・move に new が無い表を `RuntimeError` で止める。前は `TOMLDecodeError`・
`AttributeError`・`KeyError` で止まっていた=止まることは同じ)。既定の答えは変わらない: c8 の出力(22 の id・読み口の判定)は、直す前の
作業木の出力と、移す前の木でも全段を当てた木でもバイトが同じ。

### 11-3 L-6(宣言の道の引き方)

`tests/_places.py` に `declared_path_now(rel, org=None, pkg=None)`: **表の元の道として引ければ今の道へ・引けなければ、その道が今の木に
在るか**の順。どちらでもなければ `KeyError`。`current_of` は厳しいまま残した。`test_declarations_1101` と `test_refr20b_tool` の宣言の道は
これで引き、どちらの試験にも負の対照(元の道でも今の木の道でもない道は `KeyError`)を 1 行足した。補助の試験
`test_declared_path_now_reads_the_origin_first_then_the_tree`(移したファイルの古い道に別のファイルが在っても元のファイルを指す・表に
無い新しい道は木に在れば通る・無い道は止まる)。第 2 回の §10-9 の 1(段 4 の後に新しい道で書いた宣言が `KeyError` で落ちる)は
これで閉じた。

| ファイル | 保たれていること |
|---|---|
| `test_declarations_1101.py`・`test_refr20b_tool.py` | 宣言が指すファイルが在る・門の記号がそのファイルに定義されている。移す前の木では前と同じ道 |

### 11-4 L-7(`current_of` の重なり)

`current_index(org)`(元の道 → 今の道の索引)を分け、2 つの今のファイルが同じ元の道を持てば assert で止める。`current_of` と
`declared_path_now` はこれを使う。試験 `test_current_index_stops_when_two_files_share_one_origin`。

### 11-5 確かめ

- 取り込みの作業木(cwd): `tests/test_places_guard.py`・`tests/c8`・`test_declarations_1101.py`・`test_refr20b_tool.py` → **231 passed**
  (終了コード 0)。
- 全段の木(〔git の作業木の外の置き場〕に作業木の今の中身を写し、**入れ替えた後の道具**で `--stage all --apply` を 1 回=書いた
  ファイル 784・移した 180・古いディレクトリの消去 0・import の確かめ 356 モジュールで落ちた 0): 同じファイル → **231 passed**。
- 範囲の試験の全体は回していない(発注どおり=親が回す)。

突然変異(1 本ずつ順に・〔スクラッチの mut3.py と specs_r3.py〕): **22 件とも期待どおり**。移す前の木は第 2 回の段の木の s00 に
第 3 回の 6 本を重ねた写し。

| 変異 | 木 | 期待 | 結果 |
|---|---|---|---|
| A10k・A11k・A12k(検収役の A10〜A12 の形=keep の行で新しいファイル) | 全段 | 落ちる | 固定の試験が「old と new が同じ行が増えた」と決まりの文で落とした |
| A10k-r・A11k-r・A12k-r(同じ形で範囲の試験だけを回す) | 全段 | 通る | 通った(範囲は通り抜ける=固定が要る理由) |
| A10m・A11m・A12m(move の形の行=old `engine/systems/zz_new.py`・`engine/processes/zz_new.py`) | 全段 | 落ちる | `test_two_phase` の 2 本・c8 の `test_process_ablation_ids_match_source`・`test_fix_guards` の箱を通さない書き換えと `test_stage_a_guard` の thaw |
| A10m-f(move の形の行で固定の試験) | 全段 | 通る | 通った |
| E1(c8 の写しが中身のある頭を行なしで受ける)・E2(c8 の写しが古い道にファイルが残っても古い道を元にする) | 移す前・全段 | 落ちる | `test_places_rule_copies.py`(E2 の全段の木では今の木の一致の試験も落ちる) |
| L6a(引く順を逆に=木を先に)・L6b(無い道で止まらない) | 移す前・全段 | 落ちる | 補助の試験(L6b は宣言の 2 本の負の対照も) |
| L7(重なりの assert を外す) | 移す前・全段 | 落ちる | `test_current_index_stops…` |

### 11-6 道具の役へ渡すこと

1. 新しいファイルの行を move の形(`old` に移す前の置き場に在ったとしたらの道)で書く決まりは、道具の今の作りで受けられる(読んで
   確かめた範囲): 全ファイルの表の §3 の行の `old` は在るかを確かめずに読み(`table.parse_table`)、表の包みが build でなく `old` と
   `new` が違えば move になる。当てるとき(`move._row_state`)は、古い道が無く新しい道が在れば「当たっている」、移す前の木で古い道に
   ファイルを置いていれば「当てる」。直しは要らないと見ている(当てて確かめてはいない)。
2. ただし、全ファイルの表の書き方(§3 の `old` の列は「今の道」と読める)に、この決まり(移した後に作るファイルの `old` は在ったと
   したらの道)を書き足すかは、表の持ち主の判断。
3. 道具の試験 `test_map_toml_is_made_from_the_table_and_is_current` は行の数(328)と kind ごとの数を固定している。新しいファイルの行を
   足すたびに、その数とこの役の固定の一覧(keep のときだけ)の両方を直すことになる。
4. 第 2 回の §10-7 の 1 本(`test_every_rewritten_path_chain_points_to_a_file_in_the_applied_tree` の前提)はそのまま。

### 11-7 判断が要る点

1. **固定の一覧に empty の行(economy と world の頭)も入れた**: 発注の「keep の行(old と new が同じ)」を、kind でなく「old と new が
   同じ」で数えた(kind を move にして old と new を同じに書く抜け道も止まる)。kind が keep の行だけにするなら、2 行を外す。
2. **build に新しいファイルを足すと、固定の試験が落ちる**: build は動かない置き場なので keep の行が正しく、一覧に足せば通る(決まりの
   文にも書いた)。build の下を一覧から外して「build の下の keep は自由」にする形もあるが、裁定の「keep の行を黙って足せない」に
   合わせて、今は外していない。

### 11-8 作った写しの木とつなぎ

〔git の作業木の外の置き場〕に全段の木 1 つ(r3all)と、その報告の置き場。data のつなぎ 1 つ。第 2 回の段の木の s00 には第 3 回の
6 本を上書きした(突然変異の移す前の木)。どれも消していない(親が外して消す)。

## 12. 第 4 回(再検収 L-8・L-9・L-10)

> 発注: 親の指示(第 3 回の再検収=受入・H 0・M 0・L 3 の残り)。変えたファイル: `tests/test_places_guard.py`・`tests/_places.py`・
> `tools/c8/c8lib.py`・`tests/c8/test_places_rule_copies.py`・本書。許可の一覧は `allow --check` で「同じ」。

| 指摘 | 直し方 | 保たれていること |
|---|---|---|
| L-8 新しいファイルを split か delete の行(old=今の道)で載せると、固定の一覧をすり抜ける(検収の K03・K04) | 固定する集合を「**move でない行の old の全部+move で old と new が同じ行の old**」に広げた。名を `SAME_PLACE_ROWS` から `NON_MOVE_ROWS`、補助を `non_move_rows` に。今の表から数え直して 122 行(keep 94・split 24・delete 2・empty 2。move で old と new が同じ行は 0)。負の対照を kind ごと(keep・split・delete・empty・old と new が同じ move)の 5 本に | 表の規則(`origins_from`・`c8lib.src_origins`)は変えていない。move の形の行は一覧に当たらない |
| L-9 old を偽る(範囲の外の置き場を書く)と見分けられない(K05=決まりの外) | 決まりの文(`ADD_ROW_HELP`・`c8lib.PLACES_ADD_ROW_HELP`=同じ文)と §8-1 の 2 に「old は範囲を決める道なので偽らない(そのファイルが受けるはずの範囲の外の置き場=例えば build を書かない)」を足した。道が変わらない行の言い方も L-8 に合わせた | — |
| L-10 写しの試験の悪い表 `move_without_new` が、c8 の「move の行に new が無い」の止まり方を見ていない(K14) | 悪い表の例ごとに、止まった理由を両方の写しの文で見る(`match=`)。`move_without_new` は、作った木から新しい道のファイルを外して古い道のファイルだけを置く(new の無い move の行を読み飛ばしても、ほかの確かめでは止まらない木)。その木で正しい表なら両方が同じ答えを返すことも見る | 6 種の悪い表でどちらも止まる(理由まで) |

確かめ:
- 取り込みの作業木と全段の木(第 3 回の r3all に第 4 回の 4 本を重ねた。`c8lib.py` は道具が書き換えた import の 1 行を保って当てた):
  `tests/test_places_guard.py`・`tests/c8` → どちらも **212 passed**(終了コード 0)。
- 突然変異(1 本ずつ順に・〔スクラッチの mut4.py と specs_r4.py〕): **7 件とも期待どおり**。

| 変異 | 木 | 期待 | 結果 |
|---|---|---|---|
| K03(新しい系のファイルを split の行で載せる)・K04(delete の行で載せる) | 全段 | 落ちる | 固定の試験が「道が変わらない行が増えた」と決まりの文で落とした |
| K03-r・K04-r(同じ形で範囲の試験だけ) | 全段 | 通る | 通った(範囲は通り抜ける=固定が要る理由) |
| K14(c8 の写しが new の無い move の行を読み飛ばす) | 移す前・全段 | 落ちる | `test_both_copies_stop_on_the_same_bad_maps[move_without_new]`(DID NOT RAISE) |
| K15(c8 の写しが形の名を見ない) | 移す前 | 落ちる | `…[schema]` |

判断が要る点: 固定の一覧に split の 24 行が入ったので、段 5〜7 で割る行を move などに替えるたびに、この一覧も直すことになる(試験が
「減った」と知らせる)。
