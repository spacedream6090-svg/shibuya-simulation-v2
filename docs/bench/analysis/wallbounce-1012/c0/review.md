# 第 1 期 1-7 道具の台帳 C0 の独立検収(review)

- 検収役 Opus 5.5(実装は見ていない)。対象は作業木の枝 `1-7/tools-c0`(土台 `e0865b3`)の未 commit の変更 23 ファイルと、新しい置き場 3 つ(`src/shibuya/engine/tools/`・`tests/engine/tools/`・この記録の置き場)。本体 HEAD `b6f674b`(1-8 を取り込んだ後)は読むだけにした。
- 正: 口の約束 `docs/design/v2-foundation-contracts-2026-10-13.md` の「1-7 道具の台帳 C0」と冒頭の共通の約束・計画 1-7 の行・決定 10-12 §4-4 CT0・CT5・CT9・CT10・実装役への発注文・実装役の記録 [README.md](README.md)。
- 検収の道具は検収役の scratch に置いた(作業木には置いていない)。生の出力は作業木の `_bc_review/` に置き、終わったら消した。

## 判定

**条件つき受入。** 結果不変は全部確かめた。自分の byte-check は 4/4 構成で 25 欄とも同じ(本体 HEAD `b6f674b` の写しと作業木)。2 日のランも最後の src で回し、記録の値と同じだった。腕 `SHIBUYA_TOOL_EVENTS` の on/off では、5,000 体の描画 65,597 回の本文・ブロック・指紋が同じ。再開の作り直しは 2,000 体・止める時刻 3 つで通しと同じ。連絡先の印をでたらめにしても 5,000 体の final が同じ。グループの行数と `phone` タグの数も数え直して一致した。

受入の条件は M1 だけ。連絡先の印の書く口を見る AST の道具が 1-5 の `rights_writers.py` の広さに届いておらず、記録の申告(「同じ広さ」)と違う。低 L1〜L4 は親の判断。

## 欠陥(重さの順)

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `tests/engine/tools/contacts_writers.py` 34 行(`VIEW_FUNCS`)・103〜116 行(別名と的)・135 行・139 行。記録 §8 の 122 行 | 記録と道具の冒頭は「1-5 の `rights_writers.py`・1-9 の `money_writers.py` と同じ広さ」と書く。実際は、`rights_writers.ledger_writes` が見つける次の 7 形を見つけない: (1) タプルの代入 `x.contact_flags[0], y = 1, 2` (2) `for i, row in enumerate(x.contact_flags)` (3) `for row, y in zip(x.contact_flags, ys)` (4) 別名の鎖 `c = x.contact_flags; d = c; d[0] = 1`(節を stack の後ろから読むので、書いた順でも外れる) (5) `getattr(x, nm)[0] = 1`(名が式) (6) `from numpy import copyto; copyto(x.contact_flags, 0)` (7) `out=(x.contact_flags,)`。同じ 7 形を列の名 `_r_holder` で `rights_writers` に通すと全部見つかる(検収役が文字列の写しで比べた)。今の src にこの形の書きは無い(src の `contact_flags` の参照を全部読んだ。書くのは `_write_contacts` だけ) | 1-5 の `_LedgerScanner` の形を写すか、列の判定を引数にして共通化する。写す点は、別名を 2 回集める・`for`/内包/`with`・的の `Tuple`/`List`/`Starred`・`VIEW_FUNCS` に `enumerate`/`zip`/`iter`/`reversed`・`getattr` の名が式なら「?」・名だけで呼ぶ `MUTATING_FUNCS`・`out=` のタプル。7 形を `NEG` に足す |
| L1 | 低 | `src/shibuya/engine/relations.py` 663 行(`self.contact_flags = np.zeros(...)`)・778 行(`_write_contacts`) | 実行時の守りが無い。口の外から書く `layer.contact_flags[0, 0] = 9` も、付け替える `layer.contact_flags = np.zeros(...)` も止まらない(検収役が実行して確かめた)。1-3 の検収の教訓(実行時の守り=`__setattr__`)と 1-6 の `MemoryStore`(付け替えは `__setattr__` で止まる)より弱い。今の守りは AST(M1)と、試験の中だけで動く段 B の probe だけ | 配列を読み取り専用(`flags.writeable = False`)で持ち、`_write_contacts` の中でだけ書けるようにする(`ufunc.at` は `writeable` を見ないので、そこは AST で見る)。または名を変えた slot に置き、読み取り専用の view を返す property にする。試験の `noisy`・`_prefill` は口の外で書いているので一緒に直す |
| L2 | 低(1-5 と同じ限界) | `src/shibuya/engine/tools/registry.py` 215 行・`groups.py` 73 行・`places.py` 51 行 | 作った後の物に `__init__` をもう一度呼ぶと、中身を入れ替えられる(`reg.__init__()` で 7 行が 0 行になる。検収役が実行した)。1-5 の `Rights.__init__` も同じ形 | `__init__` の頭で slot が既に置かれていれば止める(3 クラスと `Rights` を一緒に) |
| L3 | 低 | `src/shibuya/engine/tools/places.py` 7〜8 行の docstring・`docs/design/bridging-ledger.json` の `BR-PHONE-TABLE-BLANK`(3221 行)の `what`/`why` | どちらも「W6 の POI は OSM の要素の番号を持たず、名前と位置で突き合わせる規則が要る」と書く。一方で記録 §5 は「W6 の POI の行 i は `shibuya_osm_wide_v8.json` の `pois[i]` で、OSM の番号で結べる見込み(2,259 行・`phone` 477 行)」とする。検収役も 2,259 行・477 行を数え直した(`w6_poi.parquet` に OSM の番号の列は無いが、元の JSON の行の並びで結べる) | 3 か所の書き方をそろえる(例:「`w6_poi.parquet` には番号の列が無い。元の JSON の行の並びで OSM の番号に結べる見込み=2-4 で確かめる」) |
| L4 | 低(取り込みの時) | 共有の 14 ファイル | 本体 HEAD(1-8 を取り込み済み)との 3 方向の併合を `git merge-file` で試すと、14 ファイルが衝突する(`bridging-ledger.json`・`run.py`・`state_ledger.py`・`decide.py`・`table.py` と、試験・凍結の表 9 本)。衝突しない 4 本(`manifest_sections.py`・`boxes.py`・`build.py`・`state_io.py`)は中身を読んで問題なし。注意点: (a) decide の `writes.paths` の `E:events.*` を 1-8 と 1-7 の両方が足している。凍結の表 `writes_paths_events.json` も両方が `decide` を足している (b) manifest の末尾の並び(`rights` → `decision_port` → `tools` なら凍結の鍵は 116 個・並びの試験 5 本を直す) (c) 状態台帳の外の行の並び(… `P`・`J0`・`CT5`)と数(外 103・全体 194) (d) つなぎの台帳は 286+2=288 行・見出しの数 (e) HEAD の行 `HD-engine.decision.layer-2d3672ba`(外す段 1-7=「周りが示すできること」を 1-7 の道具の台帳で外す)は、1-7 が入っても active のまま(記録 §11 は、結線を 1-8 の取り込みの後に回している) | 取り込みで (a) を 1 つにまとめ、(b)〜(d) の並びと数を決める。(e) は、結線するか外す段を付け替えるかを親が決める |

## 1. 結果不変 ✓

- 実装役の byte-check([byte_check_c0.json](byte_check_c0.json)): 19/19 構成で 25 欄とも同じ(動いた欄 0・呼数の差 0)。腕の環境変数は未設定=既定 off。side の JSON(作業用の置き場)で、head の側は `src_is_worktree` 偽(`e0865b3` の写し)、c0 の側は真であることを確かめた。c0 の side の JSON より後に変わった src のファイルは無い。
- 自分の 4 構成(`w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`・5,000 体・seed 1・1 日・テープつき): 本体 HEAD `b6f674b` の `git archive` の写し(src・anchors・予算の表・w6 の道具・`rules-table.json`・`bridging-ledger.json`+祝日の CSV)と、作業木の src(`--src`)で `side` → `compare` を回した。**4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`。final の全桁・behavior/full の最後・締めの後の 2 本・テープの全列も同じ)。`src_is_worktree` は head が偽、c0 が真。HEAD は 1-8 を含む(1-8 は既定で結果不変)ので、最新の本体に対しても 1-7 の変更は結果を動かさない。
- manifest の既存の欄(自分で比べた): 土台 `e0865b3` の写しと作業木で、`v3_mem_rel` を 5,000 体・seed 1・1 日・`PYTHONHASHSEED=0` で回し、葉で比べた。比べた葉は 3,237 個。動いたのは `bridges_count`(一番上と日次の行・282 → 284)・`bridges_version`・環境の欄(`env_id`・`environment.code.*`=写しには git が無い)と、非決定の壁時計 2 欄だけ。足されたのは `tools` の 49 葉と節の表の 1 行(`manifest_sections.paths.tools`)だけ。鍵の並びは土台の並びが先頭にそのまま残り、末尾に `tools` が 1 つ増える。実装役の 7 本([manifest_check_c0.json](manifest_check_c0.json)・all_ok)とも合う。

## 2. 口と約束 ✓(違いは下)

- 型と名: `Tool` の欄は口の約束の 6 つ(`name`・`known_by`・`requires`・`affects`・`owner`・`content_writer`)が先頭にその順で並ぶ。後ろに `modality`(発注が求めた欄)と、実装役が足した `content_origin`・`stage`・`bridge`(記録 §10 の 8 で仮採用)。`ToolRegistry` は読み口 `get`・`known`、書く口 `register` 1 つ、表は `MappingProxyType`。
- 違い: 連絡先の印は、発注の「`rel_contact_flags` のような列」ではなく、関係の記憶の層の SoA の外の配列 `RelationLayer.contact_flags` に置いた(記録 §10 の 4。個体 SoA の列にすると behavior/full-hash と状態のファイルが動くため)。口の約束(「関係の記憶に手段ごとの印」)とは合う。
- 約束 → 試験: (1) 既定の final 不変=byte-check+`test_flags_are_not_read_by_the_run`・`test_world_run_family_and_work_flags_and_rel_columns_unchanged`。(2) 行の数=世帯の数+事業所の数=`test_rows_equal_households_plus_establishments_on_the_full_population`(parquet の行の数と、成員の値まで比べる)。(3) 看板の印は描画のバイトを変えない=`test_synthetic_run_arm_on_and_off_render_the_same_bytes`・`test_world_run_arm_on_and_off_render_the_same_bytes`。受入の試験 4 本の名は全部あり、発注の `test_c0_phone_table_empty_and_declared.py` もある。試験の無い約束は無い。
- 〔決定〕(店の番号の場所の表は OSM の `phone` タグから): 表の出どころ `osm:phone`・規則 `osm_phone_of`(`phone` を先に、無ければ `contact:phone`)・数の記録・つなぎの台帳の行(外す段 2-4)がそろう。表は発注どおり空。

## 3. 発注文の各項

| # | 判定 | 根拠 |
|---|---|---|
| 1 道具の台帳 | ✓ | 欄・凍結・slots・`KnownBy`(既定 `EVERYONE`)・`affects`/`modality` は空・`register` だけが書く・7 行(看板・掲示は今の世界で使う。残りの 5 つは段 6-4 で登録だけ) |
| 2 個人の連絡先(CT5) | ✓ | `contact_flags`(体 × k の u1)。既存の `rel_*` は値と型まで不変(試験と検収役の noise のラン)。家族と職場は初めから印あり。値は誰も読まない。置き場は仮採用(上の 2) |
| 3 店の番号の場所の表 | ✓ | 空の `PhoneTable`・`phone_of`・`BR-PHONE-TABLE-BLANK`(2-4)・数 575/3,516 を記録。説明の食い違いは L3 |
| 4 グループの一覧(CT10) | ✓ | `GroupList`(CSR・読み取り専用)。全母集団で 37,276 行=27,404+9,872 |
| 5 記録の欄(CT9)と作り物の印 | △ | 新しい欄は足していない(1-3 の `via`・`received_ns`/`read_ns`・`origin` を使う)。印を付ける口も作った。ただし腕 `SHIBUYA_TOOL_EVENTS` の既定は off で、既定のランの記録には看板の出来事も印も無い。発注の 6「manifest の既存の欄は不変」と両立させるための仮採用 1 で、記録 §6・§11 が親の判断を求めている。決定 10-12 §4-4 CT0 の共通の決まり 5「使用は全部、出来事の記録へ」は、既定では満たさない(掲示=営業時間の判定の使用も記録しない) |
| 6 manifest | ✓ | 末尾に `tools`(観測の節)。既存の欄は不変(上の 1) |
| 受入の試験・byte-check・記録 | ✓ | 5 ファイル・61 本(収集で数えた)。byte-check の JSON あり。記録の項目はそろう |

- 「できなかったこと」の申告(記録 §11): 1-8 との結線は後・`belongings`/`tool_state` は空・`Tool.requires` を確かめる持ち物の台帳は無い・連絡先の初めの値・2-4 の番号の結び・範囲の外の家族。実態と合う(`engine/decision/` はこの枝の土台に無い。`belongings`・`tool_state` が `None` のままなのは下の 8 (e) で確かめた)。

## 4. 守り △(M1・L1・L2)

- `ToolRegistry`: AST の試験(slot を置くのは `__init__` と `register` だけ)と負の対照(`clear`・`reset` を足すと見つかる)がある。実行時は `setattr`/`delattr`/名の無い属性/`vars()` が止まる。止まらないのは `__init__` の呼び直し(L2)と、名を変えた slot の名を知った `object.__setattr__`(1-5 と同じ限界)。
- `GroupList`・`PhoneTable`: 配列は読み取り専用、表は `MappingProxyType`、付け替えは `AttributeError`。`__init__` の呼び直しは L2。
- 連絡先の印: src の AST の走査では、書くのは `RelationLayer._write_contacts` だけ、付け替えは `__init__` だけ、書く口を呼ぶのは `seed_initial`・`_reset_slots`・`rebuild_contacts` だけ。**検収役が植えた負の対照**: `relations.py` の写し(メモリの中)で `contact_tally` に `self.contact_flags[0, 0] = 1` を足すと、道具は `RelationLayer.contact_tally` を書き手として出す(試験の `writes == [_write_contacts]` が落ちる)。モジュールの外の関数で `layer.contact_flags = None` と付け替えても見つかる。形の広さは M1、実行時の守りは L1。
- 出来事の記録: decide の宣言から `E:events.*` を外すと `PermissionError`(試験 `test_undeclared_write_from_decide_fails_at_run_time`)。

## 5. 宣言と凍結 ✓

- 系の宣言: decide の `writes.paths` に `E:events.*`、memory の `writes.paths` に `CT5:rel_layer.contact_flags`、decide と report の `reads` に `fx.tools`。`writes.soa` は変わらない(印は SoA の外)。書くのが memory だけで正しいことをコードで確かめた。新しい辺は `MemoryLayer.record` → `on_episodes` → `_write_round` → `_reset_slots` の道だけで生まれる。decide の発話の記録は `relations=False`、relations_wake の同席は既存の欄を書くだけ。
- 状態台帳の行 `CT5`: 軸 1 diag(読み手は manifest の数えの口 `contact_tally` だけ)・軸 2 derivable・`hash_skip`=`items`。導出できる根拠: C0 では印はいつも `flags_from_kinds(rel_kind, rel_partner)` に等しい。初めの辺の種別は W16 の世帯と事業所から来る。新しい辺は知人(種別 5 → 印 0)で、既存の辺の種別は変わらない(`_write_round` の `kind = where(found, old_kind, acquaintance)`)。だから、戻した `rel_*` から作り直せる。版を上げないのは 1-3・1-6・1-9・1-2 と同じ仮採用。
- 凍結の表: `manifest_keys_frozen.json` は末尾に `tools` を 1 つ足しただけ(115 鍵)。`writes_paths_events.json` は `decide` を足しただけ。
- manifest の既存の欄の値: 上の 1。

## 6. 同値 ✓

- 読んだ試験: 腕の on/off(合成 60 体と世界資産 2,000 体)・書く口を止めたランと印を乱したラン(合成 80 体と世界資産 2,000 体)・再開(2,000 体を 150 刻みで止める)・段 B(宣言の中と、宣言を外した負の対照)・HEAD の写しとの比べ(byte-check・manifest・系ごとの指紋)。
- **独立の再計算 (i) 腕の on/off**(`w6_v3_default`・5,000 体・seed 1・1 日・テープつき・作業木の src・腕は環境変数で外から渡した): `Renderer.render` を包み、描画ごとに(刻み・体・本文の sha・ブロックの repr の sha・`prompt_hash`・看板の物の番号・`belongings`・`tool_state`)を 1 本の sha256 に積んだ。65,597 回の digest が on と off で同じ。final の全桁・呼数・テープの calls と blocks の sha も同じ。on の看板の出来事は 65,002 行=看板の見えた描画の数で、`origin` は全部 `signboard:synthetic`、原因は `Process("perception")`、`via` は `無し`。manifest で動いた葉は 8 つで、全部が観測の節(`daily[0].events` の `rows`・`bytes`・`live_rows`・`live_bytes`・`by_what.道具:看板`・`by_cause.process` と、`tools.signboard` の `events_arm`・`read_events`)。設定の節は 1 つも動かない。
- **(ii) 印は誰も読まない**(`v3_mem_rel`・5,000 体): 初めの印を乱数で埋め、`_write_contacts` も乱数を書く関数に差し替えた。生きた辺 9,304 本のうち 9,276 本が乱れた印を持つ状態で、final の全桁・呼数・テープ・behavior/full の最後・締めの後の 2 本が、自分の c0 の side と同じ。
- **(iii) 再開の作り直し**(10d の形・世界資産 2,000 体・2 日・語彙 v3・活動層・記憶+関係): 止める時刻 750(日中)・1440(日の境目)・1860(2 日目の日中)で止めて再開した。3 点とも、`rebuild_contacts` の直前は印が全部 0、直後は止めたランのその時刻の印と同じ(印のある辺 500 本・全部が職場)。最後の印・final・`rel_*` の 6 列・manifest の数も通しと同じ。300 体では印のある辺が 0 本で比べが空になるので、2,000 体で回した。

## 7. 試験 ✓

- 指定の範囲(`tests/engine/tools tests/engine/events tests/engine/rights tests/engine/systems tests/engine/time tests/engine/bridging tests/engine/test_state_ledger_10b.py tests/engine/test_env_and_sections_10f.py tests/engine/test_resume_10d.py tests/perception`・`-n 2 --dist loadfile -m "not slow"`・作業木): **996 passed**(17 分 55 秒)。data が無くて飛ばした試験は 0 件。
- 追加(実装役が直した所と関係の層): `tests/engine/test_state_checks_10f.py`・`test_relations.py`・`test_relations_8b.py`・`test_relations_tenure.py`・`tests/engine/memory`: **106 passed**(9 分 6 秒)。
- `lint-imports`(作業木の src を `PYTHONPATH` で指し、`shibuya` が作業木から読まれることを確かめた): 5 契約とも kept・208 ファイル。
- 秘密の走査(変えたファイルと新しいファイル・作業用の置き場は除く): CLEAN。全体の試験は親が回す。

## 8. 抜け道と記録

- (a) ✓ 腕 `SHIBUYA_TOOL_EVENTS` は `run_day` の引数にも CLI にも無い(`run.py` の差分は `RunResult.tools` と manifest の末尾だけ・`cli.py` は無変更)。だから `_call_args` の指紋に入らない。manifest の設定の節も動かない(上の 6 (i))。腕の値は観測の節 `tools.signboard.events_arm` に出る。環境変数はモジュールを読み込む時に読み、組み立ての時は `enabled()` を見る(1-3 の `SHIBUYA_EVENTS`・1-8 の `SHIBUYA_DECISION_PORT` と同じ形)。
- (b) src で書くのは `_write_contacts` 1 つだけ ✓。ただし AST の道具の広さは M1(1-5 の `rights_writers.py` が見つける 7 形を見つけない)。再開の作り直し ✓(上の 6 (iii))。行 `CT5` の diag/derivable/hash_skip ✓(上の 5)。
- (c) ✓ 語彙は 57 語で、`道具:看板` のコードは 56。1-5 までの 56 語(`行為:許可のない行動`=55 を含む)のコードは動かない。版は `events-vocab/1-7`。原因の名 `perception` は `CAUSE_PROCESS_NAMES` の末尾に足した。本体 HEAD の 1-8 の `log.py` は、過程の番号 `_PROC_CODE` を `V.CAUSE_PROCESS_NAMES` から作り、`test_j0_cause_columns` は表の全部を回す。だから末尾に足しても既存の名の番号は変わらず、整合する。`Event.via` に `看板` を足さなかった判断は、口の約束 1-3 の `via` の語(対面/通話/メッセージ/グループ/SNS/無し=CT9 (b))どおりで、1-7 の〔決定〕(店の番号の表の出どころだけを決めている)とも矛盾しない。道具の名は `what` の族 `道具` に載る。
- (d) ✓ 数え直し(src を使わず parquet と JSON を直に読んだ。読んだのは `data/world/v2/` と `data/realworld/osm/` だけ): 全母集団 390,067 体で、成員のいる世帯の番号 27,404=`w16_households.parquet` の行(番号の集合も一致)、組織の番号 9,872=`w6_org.parquet` の行、合わせて **37,276**。成員は 43,588/222,849、一番大きい行は 3/1,756。5,000 体(seed 1・ランの母集団を組み立ての中で取り出して数えた)は 474+1,380=**1,854**(成員 475/2,421)。OSM の `poi_tags_overpass_20260928.json` は **575/3,516**(`phone` 476・`contact:phone` 100・両方 1)。W6 の POI は 2,337 行で、同じ行の名が 2,337 行とも同じ・OSM の番号を持つ行 2,327・番号で結べる行 **2,259**・そのうち `phone` を持つ行 **477**。
- (e) ✓ `Percept.belongings`・`tool_state` は src のどこでも値を置いていない。合成のランの描画 129 回で両方とも `None`。5,000 体の on/off の digest にも両方の repr を入れて同じ。
- (f) ✓ 既存の試験 9 本の直しを `git diff` で 1 本ずつ読んだ。数と並びの固定の直し(語彙 56 → 57・版・見出し 76 → 77・ファイル 73 → 74・項 342 → 345・`HD-` の行 76 → 77・外の状態 101 → 102・全体 192 → 193・行の並びの末尾に `CT5`・manifest の末尾の並びに `tools`)だけだった。足した検査は `test_state_ledger_10b.py` の `CT5` の 2 行だけ。`test_rights_events.py` の `V.VOCAB[-1]` → `V.VOCAB[55]` は位置の固定の直しで、`code_of(WHAT) == 55` の検査は残る。
- (g) ✓ 2 日のラン(`10e/two_day_check_act.py one`・5,000 体・seed 1・`sim_days=2`・既定 v3・テープつき)を**最後の src** で回した。名札・`src_is_worktree`・壁時計を除く 13 欄が記録の値と全部同じ(final `912446bd2b42b6ab`・140,913 呼・calls `cb330e76b4b8a573`・blocks `7f09f3dc78d84ac4`・暦 07-13 → 07-14・天気の日ごとの記録)。`src_is_worktree` は真、壁時計 118 秒。
- 記録: この置き場(README・JSON・`tools/`)に絶対パス・ホスト名・個人名は無い(grep)。改行は全部 LF。触った共有ファイルの一覧(記録 §9)は `git diff --stat` の 23 ファイル(src と台帳 12・凍結の表 2・試験 9)と合う。`cli.py` は触っていない。実装役の作業用の置き場 `_bc/` は git の外にあるが ignore されていない(取り込みで stage しない)。

## 親に確かめてほしいこと

1. **看板の出来事の腕の既定**(記録 §10 の 1): 既定 off のままでは、口の約束の「作り物の印」と CT0 の共通の決まり 5 は既定のランに出ない。全母集団に比例で当てた量は約 507 万行/日・約 365 MB/日(65,002 行 × 390,067/5,000 × 72 B/行。実装役の推計を検収役が再計算した)。
2. **取り込み**(L4): 14 ファイルの衝突と、HEAD の行 `HD-engine.decision.layer-2d3672ba`(外す段 1-7)の扱い。
3. **予算の宣言**: 連絡先の印は体あたり k B(k=15 → 全母集団で約 5.9 MB・関係の記憶のあるランだけ)、グループの一覧は全母集団で約 2.8 MB(記録 §3 の目安)。1-5 と同じく、取り込みの後に親が予算の宣言へ足す。
4. 5,000 体の抽出では、家族のグループ 474 のうち成員が 2 人いるのは 1 つだけ(成員 475)。C1 のグループのメッセージの検証には、全母集団で回すか抽出の仕方を見直す必要がある(記録 §3 のとおり)。
5. 1-3 の `Event.origin`(「範囲の外からの印」)を、作り物の印 `signboard:synthetic` にも使っている(発注どおり)。用語集や 1-3 の定義に「作り物」の使い方を足すかどうか。
