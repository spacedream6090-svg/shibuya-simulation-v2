# 割る段 5a の記録(G0=src は変えない・道具の拡張と守り)

- 指示: 返事その 8 §8 の 5(段 5〜7=割る)。計画: [最終の表と移す段の計画](../../../reference/package-map-final-2026-11-09.md) §7-4 の段 5a の行。割り先の正: [全ファイルの表](../../../reference/package-map-final-2026-11-09-files.md) §3・§4。
- 段 5a の実行の計画(下調べ)と、問い Q1〜Q15 への親の裁定は、親の作業の置き場にある(計画 plan_stage5a・裁定 rulings_stage5a)。計画の要旨は第347 の報告 [docs/ops/report-347-2026-11-16.md](../../../ops/report-347-2026-11-16.md) §2。下の §1 に裁定の表を写した。
- G0 では src(`src/shibuya/`)を 1 字も変えていない。17 本を割るのは G1 から。〔G1 の発注で親の裁定 Q11 を変えた〕群ごとに 1 commit(群 5 つ)。実装役が 1 本ごとに byte-check(19 構成・群の土台の commit と、その本まで当てた木を比べる=積み重ね)を回して記録を本ごとに残し、親が群の終わりにもう一度 byte-check・範囲の全体の試験・別の役の検収をしてから commit する(§9)。18 本目だった `engine/speech/port.py` は延ばした(§1 の「G0 の検収の後の親の答え」1)。
- G0 は別の役の検収で条件つきの受け入れ(高 1・中 4・低 6)になり、道具と試験と記録を直した(§1-2・§2・§3・§4)。src は直しでも変えていない。

## 1. 親の裁定(Q1〜Q15)と、G0 での当て方

| 問い | 裁定 | G0 で入れたもの |
|---|---|---|
| Q1 割り先の 2 つ目以降の新しいファイル 9 本の元の置き場 | 全ファイルの表 §3 に move の形の行(old=移す前の置き場に在ったとしたらの道)・主な割り先は割る行の old | §3 に行 5a・117a・142a・143b・223a・223b・291a・298a・309a(と 18 本目の 244a)。割るかの欄=「いいえ(`元` の割り先)」→ 対応表の `split_from`。`tests/_places.py`・`tools/c8/c8lib.py` は割る行の主な割り先の元の道=old と読む |
| Q2 古い写しの固定の意味 | `_places` に名の単位の元の置き場を引く口・`_head_copy_pin` がそれを使う・固定の値は取り直さない | `PL.origin_module_of_name`・`PL.split_name_origins_from`。`_head_copy_pin._describe` は関数とクラスを頂上の名で、値を読む名で引く |
| Q3 新しい例外 4 本 | `contracts.toml` の新しい表 `[[ignore_split]]` | 4 本(下の §4)。`appears_with` の割る行を当てた木から載せる(当てる前の木の節は変わらない) |
| Q4 `DEFAULT_WALKABLE_AREA_M2` が段 7 まで古い renderer を読む | 例外(段 7 まで) | `[[ignore_split]]` の 割 2 |
| Q5 注釈だけの辺(`AgentState`) | 例外・契約の設定は変えない | `[[ignore_split]]` の 割 3 |
| Q6 自分の別名 `V.` で読む 7 文 | `V.x` → `x` に書き換え、守りで同値を確かめる | §4-9・§4-16 の注「宣言した書き換え」→ 対応表の `[row.rewrites]`。道具が当て、守り ① が元の側を同じ形に直して比べる |
| Q7 非公開の名を外から読む 3 つ | 名を変えない | 道具は名を変えない |
| Q8 表に無い `CELL_WAKE_USES_NUMBA` | `mind/system1/change_detect.py` | §4-6 に足して注を付けた(計画に無い名=仮採用) |
| Q9 「ほか N 個」の 61 名 | その行の割り先・§4 を全部の名に開く | 5a の 18 節を開いた(開いた名に注)。今は無い名 3 つ(`REPO_ROOT`・`resolve_repo_path`・`EFFECT_CAP_PER_EXPOSURE`)は表から外して注 |
| Q10 道具 | 案 A | `tools/pkgmove/split.py`・`cli.py split`(§2) |
| Q11 commit の切り方 | 1 本 1 commit・群 5 つ → G1 の発注で群ごとに 1 commit に変えた(実装役が 1 本ごとに byte-check) | `table.SPLIT_ORDER`・`SPLIT_GROUPS`(G1〜G5。前の G6=18 本目は延ばした) |
| Q12 `mora_count` | 18 本目に foundation の文の道具へ・先に表を直す | §3 の行 244 を割る行に替え、§4-25 を足した。守り ④ で止まる(§5 の 1)→ G0 の検収の後に延ばした(下の答え 1) |
| Q13 範囲の手がかり | llm=`act.intake.parser`・agents=`world.facts.population_reader` | §6 の表 |
| Q14 古い頭を消す時 | 最後のファイルを割った commit で | 道具が 0 バイトの頭しか残らないディレクトリの頭を消す |
| Q15 llm の割り方 | `llm/__init__` を先に・0 バイトの頭を `llm/undefined` まで残す | 道具が元のファイル(頭)を、ほかのファイルが残る間は 0 バイトで残す |

### 計画に無いことを決めた所(実装役の仮採用・戻し方=G0 の commit の前の木)

1. 18 本目(延ばした)の割り先のファイルの名 `foundation/text/mora.py`(裁定は「foundation の文の道具」)。
2. 2 つ目以降の割り先の行の old の名(移す前の置き場に在ったとしたらの道): `agents/agent_codes.py`・`engine/wake.py`・`engine/scene_hash.py`・`engine/choice.py`・`engine/relations_vocab.py`・`engine/initial_ties.py`・`llm/act_codes.py`・`perception/attention_gate.py`・`world/place_words.py`・`engine/speech/mora.py`。ディレクトリは、その割り先を作る本の元のディレクトリ。
3. 既に在る割り先に `__all__` が無いとき(前の本が作った割り先=`foundation/vocab/place_words.py`)は、import の後ろに足す名だけの `__all__` を作る。
4. 割るモジュールが import で結んだ名(再輸出・例 `agents/state.py` の `_WP`)を読む所は、その名を持ち続ける割り先(主な割り先を先に)へ向ける。どの割り先も持たなければ元のモジュールへ。
5. 2 つ目以降の新しい割り先の docstring は決まった型(元のファイルと主な割り先を名指す・凍結の値と expedient の見出しを書かない)。
6. 頂上のほかの文(assert)は、読む名の割り先へ(2 つ以上なら主な割り先・主な割り先が入らなければ断る)。
7. 元が 0 バイトの頭として残る間(G3 の 7〜9 本目の `llm/__init__.py`)は、主な割り先(`foundation/ports/inference.py`)の元の置き場は今の道のまま(元の道が 2 本の今のファイルに重ならないように)。10 本目で頭を消すと元の道 `llm/__init__.py` になる。
8. 道の文字列の許可の一覧は、その本の走査で作る(割るファイルの道か名を持つ文字列の記号だけ)。`allow_tests_tools.toml` は作り直さない(段 4 の後の木では作り直すと空=試験は当てていない木でだけ比べる)。除くもの=`tests/test_places_guard.py::NON_MOVE_ROWS`(表の old の固定)・`tests/build_pop/test_w21_stage8_9.py::test_persona_does_not_reference_llm_ports`(llm の字の検出器の植えた文)。docs の記録の道具は import だけ(親の決定 7)。
9. 割る段の終了コード: 守りが止めたときも 2(親の発注「守りが同じでなければ当てない(終了コード 2)」)。段 4 の `move` は 1 のまま。
10. `test_fleet_contract` の `agents.state` の手がかりも Q13 と同じに付け替えた。`test_nav1_units` の選び手は、名の定義の置き場(`ChoiceContext`・`ClassicalChooser` の `__module__`)から引く形にした(割ると 2 つのモジュールになる=両方を禁じる)。

G0 の検収の後に足した仮採用(親の答え 4=検収の低の指摘を入れて受け入れ):

11. どの割り先も使わない import(途中の再輸出を含む)と、import・`from __future__`・`__all__` の前と中の注は写さない。黙って落とさず、書かない実行の報告の `unwritten` に本ごとに出す(検収 低-2・§3-2 に 17 本の一覧の要約と副作用の確かめ)。
12. `contracts.view()` は、頭を割る行(`llm/__init__.py`)の主な割り先を、中身が出た後(元の頭が無いか 0 バイト)に最終の名に載せる(検収 高-1。G0 では直していなかった)。割る前と後の import の決まりを比べ、宣言(`contracts.toml` の `[[split_weakens]]`=2 本目の `agents`・10 本目の `llm`)のほかに言えなくなった単位・決まりや古い決まりから外れた名が増えたら、道具が止める(終了コード 2)。
13. 元の相対の import は絶対の形に作り直して写す(断らない。5a の 17 本には無い)。相対の import と星の import で割るモジュールを読む読み手は「手で直す一覧」(5a の読み手には 0 件)。
14. 2 つ目以降の新しい割り先の決まった型の docstring は「割る段で ``元`` を割った割り先」(段の名を決め打ちしない=5b〜7 で使い回す・検収 低-6)。
15. `cli.py split` は木の src に `__pycache__` を書かない(`sys.dont_write_bytecode`・検収 低-4)。

### 1-2. G0 の検収の後の親の答え(2026-11-16)と、当て方

| 答え | 中身 | 当て方 |
|---|---|---|
| 1 | 18 本目(`mora_count`)は延ばす(案 b)。台帳の道を書き換えられる版上げで一緒に下ろす。5a は 17 本で終える。決まり 10 の例外 1 本(核 1)はそれまで残る | 割る行のまま残し、割る段の順から外した: `table.SPLIT_ORDER` は 17 本・新しい `table.SPLIT_DEFERRED`(理由つき)・`map.toml` の頭に `split_deferred`・全ファイルの表の行 244 の割るかの欄=「割る(§4-25・延ばした)」・行 244a の段の欄=「延ばした(版上げ)」・§4-25 に注。元の move の行へ戻さなかった理由: 行 244 を move の行へ戻すと、割り先の行 244a(`split_from`)を表から消すか形を変えることになり、§4-25 の名の表も読む行を失う。割る行のまま順から外せば、`map --check`(表 → `map.toml`)・段の順の検査(順の行が割る行で名が揃う)・段 4 の段の検査(割る行は段の行に数えない=G0 と同じ)がどれもそのまま通り、版上げのときは順に 1 行足すだけで当てられる。道具は順に無い行を名指しでも断る(試験 `test_split_rows_in_the_real_map_match_the_source_files`) |
| 2 | 手で直す読み 24 件は、その本の commit の中で、道具を当てる前に直す(直した後に書かない実行を回し、「手で直す一覧」が 0 になってから当てる) | §3-1 の一覧に、その本と、中身を見る試験 3 本(答え 6)を並べた |
| 3 | G3 の 7〜9 本目の間、`foundation/ports/inference.py` の元の置き場が範囲の外に出る件は受け入れる(高-1 の直しで決まりが弱まらないことが条件) | 仮採用 7 のまま。高-1 の直しで 7〜9 本目も決まり 2 と単位 foundation が言える(§4) |
| 4 | 計画に無い仮採用 10 個は、検収の低の指摘を入れて受け入れる | 仮採用 11〜15 を足した |
| 5 | 自動の安全検査に止められた件の中身 | 報告に書いた(記録には書かない) |
| 6 | 中身を見る試験 3 本(`test_relations`・`test_fleet_contract`・`test_two_phase`)は、その本の手で直す一覧に入れる | §3-1 |

## 2. 道具(`tools/pkgmove/split.py`)

使い方と当て方は [tools/pkgmove/README.md](../../../../tools/pkgmove/README.md) の「割る段 5a」の節。要点:

- 名の単位の表: 全ファイルの表 §4 → `cli.py map` → `map.toml` の割る行の `[row.names]`・`[row.rewrites]`・`split_order`。17 本と延ばした 1 本とも、表の名と元のファイルの頂上の名が完全に一致する(試験 `test_split_rows_in_the_real_map_match_the_source_files`)。
- 当て方: 頂上の文を単位(前の注と空行つき)で割り先へ元の順・元の字面のまま写す。import は割り先が使う名だけ(組み込みの名を覆う元の名も数える)・兄弟の割り先からの import を足す・`__all__` は割り先ごと・相対の import は絶対の形に作り直す。既に在る割り先へは後ろへ足す。宣言した書き換えだけを当てる。断る形: 星の import のある元・既に在る割り先と同じ名を足す・`from __future__` が元と既に在る割り先とで食い違う・宣言した書き換えの `x` が局所の名に捕まる。
- 読み手: import の文は名の単位で割り先へ(1 文を割り先ごとに分ける)。別名で読み割り先が 2 つ以上になる読み・相対の import と星の import で割るモジュールを読む読みは「手で直す一覧」に出し、`--next`・`--only` では断る(`--through` の書かない実行では残して報告する)。
- 報告: 本ごとに「写さなかった import と注」(`unwritten`)と、割る前と後の import の決まりの数と弱まり(`contracts`)を出す。
- 固定の表の鍵(クラスの単位の写像と逆写像の守り)・台帳の道の表(主な割り先 → 元の道)・(道, 関数)の組の表(同じ組の名の割り先へ=計画 c9)。
- 段の順: 済んだ割る行が順の頭から並び、当てる本が次の 1 本でなければ断る。

### 守り(割る段)

| 守り | 中身 | 止めた負の対照(試験) |
|---|---|---|
| ① 文 | 元の頂上の文(import・docstring・`__all__`・`from __future__` を除く)の AST の多重集合=割り先に足した文の多重集合(宣言した書き換えは元の側を同じ形に直して比べる)。割り先ごとに、足した文の並び=元の並びからその割り先の文だけを抜いた並び(既に在る割り先は在る文の並びが変わらず、後ろに足した分の並び) | 1 文を落とす・1 文を 2 か所に置く・同じ割り先の中で 2 文を入れ替える(① だけが止める) |
| ② 定数 | 文字列とバイト列の定数の多重集合(モジュールの docstring を含む)=割り先の | 文字列の定数を変える・主な割り先のモジュールの docstring を変える(② だけが止める) |
| ③ 名の結び | 割り先で結ばれない名が、元のファイルより増えない。元の頂上で結ぶ名(組み込みの名を覆う名を含む)を読む文は、割り先でも同じ物に結ばれる(頂上の定義なら名の割り先・import なら同じ出どころ) | 要る import を落とす・組み込みを覆う名(`def format`)の import を落とす(③ だけが止める) |
| ④ 宣言 | つなぎの台帳の 6 形の宣言(台帳の道で比べる)が同じ。2 つ目以降の新しい割り先に宣言が入れば止める(台帳の道の表=1 対 1) | 2 つ目以降の割り先へ expedient の段落を入れる |
| 鍵 | 固定の表の鍵=クラスの単位の写像が 1 対 1・逆写像で古い鍵に戻り値が同じ・値の多重集合が同じ | 2 つの鍵の値の取り違え・2 つのクラスを 1 つの鍵へ |
| 宣言した書き換え | 宣言の無い自己の別名は断る・当たらない宣言も断る | 宣言を外す・当たらない宣言を足す |
| 手で直す読み | 別名で読み割り先が 2 つ以上の読みは断る | 2 つの割り先の名を読む別名 |
| 段 4 の守り | 名の凍結・固定の表(値と網羅)・道の形の 74 種・許可の一覧の外の定数・import の文が結ぶ名・頭の `__all__` | (段 4 の試験のまま) |
| import の決まり(検収 高-1) | 割る前と後の木で `contracts.toml` から作る節を比べ、`not_expressed`(言えない単位・決まり)と `dropped_old`(古い決まりから外れた名)に増えた項が `[[split_weakens]]` の宣言のほかにあれば止める。値は「同じ」か「宣言どおり N」 | 宣言の外で単位が言えなくなる(見本で `contracts.build` を差し替え)・頭を割る行の主な割り先が最終の名になる(`contracts.view`)・本物の木で 17 本を順に当てる(`slow`) |
| 順と止め(検収 中-4) | 済んだ本の当て直し・順が違う本・順を飛ばした木・本体の作業木への `--apply`・`--apply` に `--tree` が無い・`--through` と `--apply` | 見本の木で全部断る(終了コード 2) |
| 組み立ての断り(検収 中-1・中-2・低-1・低-3) | 星の import のある元・既に在る割り先と同じ名・`from __future__` の食い違い・局所の名に捕まる書き換え | 見本の木で全部断る |

## 3. 17 本の書かない実行(本物の木・メモリの中で順に当てた・手で直す読みは残した)

G0 の検収の直しの後の木(本体の頭 `dcd25a6c` の上へ載せ直した木・src は段 4 の後のまま)で、`split.py` の書かない実行を順にメモリの
中で当てた(`cli.py split --through all` と同じ。各本は前の本を当てた後の木に当てる・import の決まりの守りも回した)。手で直す読みは
残して進めた(`--next` では断る)。数は直す前(G0)の書かない実行と全部同じだった(載せ直しで読み手の数は変わらなかった)。

| 本 | 割る行 | 割り先(new=新しい・existing=既に在る) | 守り | 書き換えた import の文 | 分けた文 | 鍵 | 台帳の道 | 道の文字列の記号 | 消した・空にした・足した頭 | 手で直す | 契約(古い+新しい) | 写さなかった |
|---:|---|---|---|---:|---:|---:|---:|---:|---|---:|---|---|
| 1 | `world/assets.py` | `world/model/assets.py` new・`foundation/vocab/place_words.py` new | 全部「同じ」 | 53 | 1 | 2 | 1 | 2 | — | 1 | 3+9 → 3+9 | 注 5 |
| 2 | `agents/state.py` | `world/model/agent_table.py` new・`foundation/vocab/agent_codes.py` new | 「同じ」・決まり=宣言どおり 4 | 196 | 67 | 7 | 1 | 8 | 消 `agents/__init__.py` | 1 | 3+9 → 3+9(古い 4 本から名 `agents` が外れる) | — |
| 3 | `engine/calendar.py` | `world/facts/calendar.py` new・`foundation/types.py` existing | 全部「同じ」 | 35 | 0 | 3 | 1 | 2 | — | 1 | 3+9 → 3+9 | — |
| 4 | `engine/tools/registry.py` | `society/tools/registry.py` new・`foundation/vocab/events.py` existing | 全部「同じ」 | 12 | 1 | 3 | 1 | 1 | — | 2 | 3+9 → 3+9 | — |
| 5 | `engine/tools/record.py` | `society/tools/record.py` new・`foundation/vocab/events.py` existing | 全部「同じ」 | 11 | 0 | 2 | 1 | 0 | 消 `engine/tools/__init__.py` | 1 | 3+9 → 3+9 | — |
| 6 | `engine/events/body.py` | `mind/memory/body_events.py` new・`foundation/vocab/events.py` existing | 全部「同じ」 | 2 | 0 | 1 | 1 | 0 | 消 `engine/events/__init__.py` | 1 | 3+9 → 3+9 | — |
| 7 | `llm/__init__.py` | `foundation/ports/inference.py` new | 全部「同じ」 | 36 | 5 | 4 | 1 | 1 | 空 `llm/__init__.py` | 0 | 3+9 → 3+9 | import 3・注 12 |
| 8 | `llm/fleet.py` | `runtime/inference/fleet.py` new・`foundation/ports/inference.py` existing | 全部「同じ」 | 25 | 4 | 15 | 1 | 2 | — | 0 | 3+9 → 3+9 | — |
| 9 | `llm/mock.py` | `runtime/inference/mock.py` new・`foundation/vocab/actions.py` existing | 全部「同じ」 | 30 | 1 | 2 | 1 | 1 | — | 0 | 3+9 → 3+9 | — |
| 10 | `llm/undefined.py` | `act/intake/undefined.py` new・`foundation/vocab/act_codes.py` new | 「同じ」・決まり=宣言どおり 5 | 26 | 1 | 5 | 1 | 0 | 消 `llm/__init__.py` | 0 | 3+9 → 2+9(古い 3 本から名 `llm` が外れ、llm の決まりが丸ごと消える) | 注 3 |
| 11 | `engine/llm_bridge.py` | `runtime/inference/bridge.py` new・`foundation/ports/inference.py` existing | 全部「同じ」 | 28 | 0 | 7 | 1 | 0 | — | 0 | 2+9 → 2+9 | — |
| 12 | `engine/chooser.py` | `mind/judge/chooser.py` new・`foundation/ports/choice.py` new | 全部「同じ」 | 16 | 3 | 4 | 1 | 1 | — | 1 | 2+9 → 2+9 | — |
| 13 | `engine/poi_target.py` | `act/target.py` new・`foundation/vocab/place_words.py` existing | 全部「同じ」 | 13 | 1 | 1 | 1 | 0 | — | 1 | 2+9 → 2+9 | — |
| 14 | `perception/attention.py` | `foundation/text/salience.py` new・`mind/percept/attention.py` new | 全部「同じ」 | 14 | 2 | 2 | 1 | 0 | — | 1 | 2+9 → 2+9 | — |
| 15 | `engine/change_detect.py` | `mind/system1/change_detect.py` new・`world/model/scene_hash.py` new・`foundation/vocab/agent_codes.py` existing | 全部「同じ」 | 13 | 0 | 3 | 1 | 1 | 足 `mind/system1/__init__.py` | 4 | 2+9 → 2+9 | — |
| 16 | `engine/arbiter.py` | `runtime/arbiter.py` new・`mind/system1/wake.py` new | 全部「同じ」 | 22 | 6 | 3 | 1 | 2 | — | 0 | 2+9 → 2+9 | — |
| 17 | `engine/relations.py` | `mind/relations/layer.py` new・`world/facts/initial_ties.py` new・`foundation/vocab/relations.py` new | 全部「同じ」 | 14 | 3 | 3 | 1 | 4 | — | 10 | 2+9 → 2+9 | — |
| (延) | `engine/speech/port.py` | — | 延ばした(順に無い=道具は断る) | — | — | — | — | — | — | — | — | — |

- 守り=①文(多重集合と割り先ごとの順)・②定数・③名の結び(結ばれない名と、同じ物への結び)・④宣言・名の凍結・固定の表・道の形の 74 種・許可の一覧の外・import の文が結ぶ名・頭の `__all__`・import の決まり の 11 個。import の決まりの値は「同じ」か「宣言どおり N」(§4)。
- 書き換えた import の文は src・build・tests・tools・docs の記録の道具の和(道具の数え方=書き換えた文の数)。分けた文=名が 2 つ以上の割り先へ分かれて 1 文を分けた数。
- 1 本あたり 10〜20 秒(import の決まりを割る前と後の木で 2 回作る分を含む)。

### 3-1. 手で直す読み(24 件)と中身を見る試験(親の答え 2・6=その本の commit の中で、道具を当てる前に直す)

直した後に書かない実行を回し、「手で直す一覧」が 0 になってから当てる。

- 1 本目 `world/assets.py`: `tests/engine/test_assets_10e_b0_b1.py:24`
- 2 本目 `agents/state.py`: `docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py:257`。中身を見る試験 `tests/engine/test_two_phase.py`(`.thaw` の呼び手の集合に `agents/state.py` の割り先)
- 3 本目 `engine/calendar.py`: `tests/engine/test_calendar_10e_e3.py:23`
- 4 本目 `engine/tools/registry.py`: `tests/engine/tools/test_c0_affordance_from_registry.py:24`・`tests/engine/tools/test_c0_tool_registry.py:18`
- 5 本目 `engine/tools/record.py`: `tests/engine/tools/test_c0_signboard_mark_invariance.py:26`
- 6 本目 `engine/events/body.py`: `tests/engine/multiday/test_md23_body_events.py:26`
- 8 本目 `llm/fleet.py`: 中身を見る試験 `tests/llm/test_fleet_contract.py`(禁じる名を 2 つの割り先で見る)
- 12 本目 `engine/chooser.py`: `tests/engine/test_classical_policy.py:20`
- 13 本目 `engine/poi_target.py`: `tests/engine/test_intent_chooser.py:272`
- 14 本目 `perception/attention.py`: `tests/perception/test_attention.py:8`
- 15 本目 `engine/change_detect.py`: `tests/engine/clock/test_tm3_step_scope.py:25`・`tests/engine/space/test_nav1_density.py:213`・`tests/engine/test_change_detect_p6.py:21`・`tests/engine/test_renderer_wiring.py:22`
- 17 本目 `engine/relations.py`: `docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py:161`・`docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py:205`・`docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py:347`・`docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py:517`・`docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py:570`・`docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py:650`・`tests/engine/test_relations.py:24`・`tests/engine/test_relations_8b.py:23`・`tests/engine/test_relations_tenure.py:25`・`tests/engine/tools/test_c0_contacts_in_relations.py:23`。中身を見る試験 `tests/engine/test_relations.py`(`copresence`・`slot_cells` は `world/facts/initial_ties.py`)

### 3-2. 写さなかった import と注(検収 低-2・17 本の報告の `unwritten`)

| 本 | 写さなかったもの |
|---|---|
| 1 `world/assets.py` | `__all__` の中の区切りの注 5 行(`# ---- 10e(B0・B1): 資産の指紋と旧資産の切替口 ----` ほか)。`__all__` を割り先ごとに作り直すため |
| 7 `llm/__init__.py` | 途中の再輸出の import 3 文(`from shibuya.llm.mock import MockLLM, TapeLLM`・`from shibuya.llm.undefined import (…)`・`from shibuya.llm.fleet import (…)`。どの割り先も使わない)と、その前の注 4 行(循環を避けるための置き場の説明)・行末の `# noqa: E402` 3 つ・`__all__` の中の区切りの注 5 行 |
| 10 `llm/undefined.py` | `__all__` の中の区切りの注 3 行(`# ---- 段0 辞書 v3 … ----` ほか) |
| ほかの 14 本 | 無い |

- 副作用の確かめ: 写さなかった import は 7 本目の再輸出の 3 文だけ。読む先の `llm/mock.py`・`llm/undefined.py`・`llm/fleet.py` の頂上の文を AST で見た(関数・クラス・import のほかの文): `re.compile`・自分の表から作る辞書と組・自分の表の assert・`dataclass` と `runtime_checkable` の飾りだけで、ほかのモジュールへの登録・環境変数の読み・乱数・入出力は無い。3 文は循環を避けるために後ろへ置いた再輸出(注の説明どおり)で、読み手は道具が名の割り先(元のモジュール)へ向ける(7 本目の手で直す読みは 0)。副作用のある import は無い=主な割り先へ残すものは無い。読み込みの順が変わる分は、親の byte-check(G3)で確かめる。
- 注は区切りと説明だけ(コードの意味は持たない)。割り先に写さないことを仮採用 11 とした。

## 4. import の決まり(`[[ignore_split]]`・`[[split_weakens]]`)

### 4-1. 例外(計画に無い 4 本)

| 番号 | 最終の名 | 決まり | 載る本 | 消える段 |
|---|---|---|---|---|
| 割 1 | `mind.percept.draw -> world.model.agent_table`(今の名は `perception.renderer`) | 3 | 2 本目 `agents/state.py` | 段 7 |
| 割 2 | `world.model.scene_hash -> world.model.percept_scene`(今の名は `perception.renderer`) | 1 | 15 本目 `engine/change_detect.py` | 段 7 |
| 割 3 | `mind.system1.change_detect -> world.model.agent_table`(注釈だけ) | 3 | 15 本目 | 注釈だけ(段 8) |
| 割 4 | `mind.system1.change_detect -> world.model.scene_hash`(例外 T3) | 3 | 15 本目 | 残る |

今の木(まだ割っていない)では 4 本とも載らない(`contracts --check` は前と同じ)。

### 4-2. 契約の数の動きと、弱まってよい決まりの宣言(検収 高-1)

- 直す前(G0): 契約の数(古い+新しい)は 3+9 → 7 本目で 3+8(単位 foundation が「最終の名でないモジュールがある(`shibuya.foundation.ports.inference`)」で言えなくなり、決まり 2「foundation は何も読まない」が消え、決まり 1 の層からも foundation が外れた。lint は kept のまま)→ 10 本目で 2+8 → 17 本目 2+8=10。計画(11)より 1 少ない。
- 原因: `contracts.view()` が old が頭の行を割る行でも飛ばし、`llm/__init__.py` の主な割り先が最終の名に載らなかった。直し: 割る行の頭は、中身が出た後(元の頭が無いか 0 バイト)に主な割り先を最終の名に載せる。
- 直した後: 3+9 → 9 本目まで 3+9 → 10 本目で 2+9 → 17 本目 2+9=11(計画どおり)。単位 foundation と決まり 2 は最後まで言える。
- 黙って弱めない仕組み: 割る道具は割る前と後の木で節を作り、`not_expressed`(言えない単位・決まり)と `dropped_old`(古い決まりから外れた名)に増えた項を比べる。`contracts.toml` の `[[split_weakens]]` で宣言した分のほかに増えたら止める(終了コード 2)。宣言は 2 本: 2 本目 `agents/state.py`=古い決まりから名 `agents` が外れる(包み agents が無くなる・4 項)・10 本目 `llm/undefined.py`=名 `llm` が外れ、古い決まり「llm は world/agents を import しない」が丸ごと消える(5 項)。17 本の書かない実行で、宣言の外の増えは 0・当たらない宣言も 0。

## 5. 止まる所・親の判断を待つ所

1. **18 本目(`mora_count`)は延ばした**(G0 の検収の後の親の答え 1)。理由は守り ④ で止まること: `mora_count` の docstring の `expedient:` の段落はつなぎの台帳の行 `BR-DOC-SPEECH-MORA-KANA`(`src/shibuya/engine/speech/port.py#docstring:67c85df9`)で、同じ元の道の見出し `HD-engine.speech.port-6f282ea4` は主な割り先 `society/speech/port.py` に残る。台帳の道の対応の表(今の道 → 台帳の道)は 1 対 1 なので、2 つの今の道を同じ台帳の道に向けられない。台帳の JSON は変えない決まり。台帳の道を書き換えられる版上げのときに一緒に下ろす。それまで決まり 10 の例外 1 本(核 1)は残る。
2. 手で直す読み(§3-1)は、その本の commit の中で、道具を当てる前に直す(親の答え 2)。

## 6. 空回りする試験の直しと、範囲の手がかりの付け替え

直す前と後で、同じ 10 本の試験(ノードを名指し)を今の木で回した: 前 10 passed・0 skipped → 後 10 passed・0 skipped。

| 試験 | 前 | 後 |
|---|---|---|
| `tests/perception/test_channels.py::test_estimate_tokens_matches_the_llm_side_convention` | `pytest.importorskip("shibuya.llm")`(llm が無くなると黙って飛ぶ) | `from shibuya.llm import estimate_tokens`(移す道具が名の割り先へ向ける) |
| `tests/engine/clock/test_tm2_talk_clock.py::test_think_time_is_not_added_to_the_gap` | `"shibuya.engine.llm_bridge" not in mods`(割ると何も確かめずに通る) | `LLMBridge.__module__` から作る(割った後は割り先の名)。〔検収 低-5〕割った後に禁じるのは橋のモジュールだけになる(型の口 `RenderedPrompt`・`Renderer` は `foundation.ports.inference` へ行き、時計が読んでも考える時間は二重に数えない=禁じない)。代わりに考える時間の名 4 つ(`LANE_SECONDS`・`LANE_THINK_TOKENS`・`ALPHA_THINK_SECONDS_PER_TOKEN`・`delta_think_ticks`)は、どこから読んでも禁じる形に足した |
| `tests/engine/test_state_checks_10f.py::test_k19_static_sites_are_frozen` | `s.path != "llm/fleet.py"`(割ると空回り) | `FleetClient` の定義のファイルから道を作る(そのファイルに `client.stream` が在ることも確かめる) |
| `tests/build_pop/test_w21_stage8_9.py::test_persona_build_does_not_import_or_call_llm` | `import shibuya.llm as LLM`(範囲の手がかり) | `act.intake.parser`(元の置き場 llm/・Q13) |
| `tests/build_pop/test_w21_stage8_9.py::test_persona_does_not_reference_llm_ports`(検収 低-5) | 字面の "llm" の検出器だけ(G3 の後は新しい置き場 `runtime.inference.*`・`foundation.ports.inference` の読みを見ない) | 字面の検出器(植えた文は変えない)に加えて、元の置き場が llm/ のモジュール(実行時の試験と同じ範囲=`PL.names_from(act.intake.parser)`)を読む import も禁じる。負の対照=範囲のモジュールを今の名で植えると見つかる。G3 の 7〜9 本目の間の `foundation.ports.inference` は範囲の外(親の答え 3) |
| `tests/economy/cp2/test_cp2_event_links.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/space/test_nav1_units.py` | `import shibuya.llm as LLM` | `act.intake.parser`(Q13) |
| `tests/engine/memory/test_m0_store_schema.py`・`tests/llm/test_fleet_contract.py` | `from shibuya.agents import state as AGENTS` | `world.facts.population_reader`(元の置き場 agents/・Q13) |
| `tests/engine/space/test_nav1_units.py::test_engine_does_not_decide_for_the_person` | `from shibuya.engine import chooser` → `module_names(chooser, …)` | `ChoiceContext`・`ClassicalChooser` の `__module__` の集合(割ると選び手と口の 2 つ=両方を禁じる) |

## 7. 試験の結果(作業の木・2026-11-16・pytest は 1 本ずつ・`-n` なし)

### 7-1. G0 の検収の直しの後(本体の頭 `dcd25a6c` の上へ載せ直した木)

| 回したもの | 結果 |
|---|---|
| 載せ直しで混ざった 2 本(`tests/economy/cp2/test_cp2_event_links.py`・`tests/engine/space/test_nav1_units.py`)を最初に | 29 passed |
| `tests/tools/test_pkgmove.py`(直しの試験を足した後・`slow` の 17 本の試験を含む) | 79 passed・20 skipped(飛んだ 20 本は段 4 の段が残っていない木の理由=前からの理由) |
| 1 本の pytest: 置き場の守り(`test_places_guard`)・写しの一致(`test_places_rule_copies`)・`test_c8lib`・カード(`test_repo_guide`)・古い写しの固定(`test_render_from_percept_bytes`)・G0 で直した試験のファイル 7 本(`test_cp2_event_links`・`test_tm2_talk_clock`・`test_m0_store_schema`・`test_mr65_guards`・`test_nav1_units`・`test_fleet_contract`・`test_channels`)と 3 ノード(`test_k19_static_sites_are_frozen`・`test_persona_does_not_reference_llm_ports`・`test_persona_build_does_not_import_or_call_llm`)・中身を見る試験の残り 2 本(`test_relations`・`test_two_phase`) | 296 passed・0 skipped |
| 古い写しの固定を使う残りの 2 本(`test_cp2_nine_ops_equivalence`・`test_percept_is_scratch`) | 51 passed・0 skipped |
| 直しの突然変異(メモリの中・1 本ずつ): `contracts.view` を直す前に戻す・捕まりの確かめを外す・決まりの守りの宣言の外を空にする | 3 本とも足した試験が落ちた(変異を捕まえた) |
| `lint-imports` | 12 kept・0 broken(今と同じ) |
| `cli.py map --check`・`cli.py contracts --stage delete --tree . --check` | 同じ・同じ |
| カード `tools/repo_guide/build.py --check` | 最新(`cards/data.md` は作り直した後に戻した) |
| src の差 | 0 本(`git diff -- src` が空) |

### 7-2. G0(載せ直しの前)

| 回したもの | 結果 |
|---|---|
| `tests/tools/test_pkgmove.py`(割る段の試験を足した後) | 61 passed・20 skipped |
| 置き場の守り・写しの一致・心の読み・古い写しの固定・カードの試験と、空回りの直しの 10 本(1 本の pytest) | 132 passed・0 skipped |
| 古い写しの固定を使う残りの 2 本 | 51 passed・0 skipped |
| 空回りの直しの 10 本の前後 | 前 10 passed・0 skipped → 後 10 passed・0 skipped |

範囲の全体の試験と byte-check は回していない(親が回す)。`allow --check` は段 4 の後の木では前から「違う」(作り直すと空=試験は当てていない木でだけ比べる)。

## 8. 親の確かめ(第347)

- src の差: `tools/bytecheck/astsame.py --base HEAD`=変わったファイル 0 本([astsame_g0.json](astsame_g0.json)・土台 `cc0c658`)。byte-check は回して
  いない(src を変えていない段)。
- 範囲の全体の試験(`tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`・linked の作業木・土台 `8c58d9f` の上): 6,902 passed・
  1 failed・21 skipped・1 xfailed(36 分 18 秒)。落ちた 1 本は前からの
  `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(linked の作業木でだけ落ちる)。
- 本体の頭 `cc0c658`(版上げ A48 と台帳が入った)へ載せ直した後: 道具の試験と置き場の守り(`tests/tools/test_pkgmove.py`〔本物の木で 17 本を順に当てる
  slow の試験を含む〕・`tests/test_places_guard.py`・`tests/c8/test_places_rule_copies.py`)=108 passed・20 skipped(飛んだ 20 本は、段 4 の段がもう残って
  いない木という前からの理由)。`map --check`・`contracts --stage delete --check` は「同じ」。`lint-imports` 12 kept。
- 別の役の検収: 1 回目 条件つき(高 1・中 4・低 6)→ 直した → 2 回目 受入(高 0・中 0・低 4)。
- §3 の表の数(書き換える import の文の数など)は、版上げ A48 が本体に入る前の木で取った値。A48 は割る 17 本を変えていないが、読み手の数は
  本ごとに当てるときの実測で記録し直す。
- 例外(ignore)の本数は G0 では変わらない(31 本・延べ 45 行。まだ 1 本も割っていない)。

## 9. G1 の当て(本物の木・群の土台 `adbe8bb`=G0 の commit・安定版のタグ `stable-v2-before-split5a-G1`)

- 回し方(G1 の発注): 1 本ごとに、手で直す読みと中身を見る試験を先に直す → 書かない実行(守り 11 個・手で直す一覧 0)→ `cli.py split --next --apply --tree <作業木>`(その本だけ・全モジュールを 1 本ずつ読む import の確かめ)→ `cli.py contracts --stage delete --tree . --apply` → 狙いの試験(作業木で変わった試験のファイル・`tests/tools`・置き場の守り・写しの一致。`-n 4`・`-m "not slow"`)と `lint-imports` → byte-check 19 構成(`--base adbe8bb`=群の土台と、その本まで当てた木を比べる=積み重ね)→ この節。
- 数は版上げ A48 の後の木で取り直した(§3 の表は A48 の前の値)。tests の文が §3 より増えた分: 1 本目 +2(A48 が足した `tests/perception/test_weather_a48.py` が `world.assets` を読む 1・手で直した別名 `WA` を道具が書き換えた 1)・2 本目 +1(同じ試験が `agents.state` を読む)・3 本目 +1(手で直した別名 `CAL`)。docs は 2 本目が +2(手で直した `rel8b_measure.py` の別名 `S` の文と、足した名の import の文=どちらも G0 では書き換えなかった)。
- `cli.py allow`(段 4 の対応で `allow_tests_tools.toml` を作り直す道具)は回していない。段 4 の後の木で作り直すと中身が空になる(仮採用 8・§7)。割る段の道の文字列の許可は、本ごとの走査で作る。
- 心の読みの一覧の `scope.split` に G1 の 3 本は載っていない(載るのは 5a の 6 本=arbiter・change_detect・chooser・events/body・relations・attention と、`engine/resolve.py`・`perception/renderer.py`)=直す所なし。古い頭: 2 本目で `agents/` が消えた(`agents/state.py` と `agents/__init__.py`)。

### 9-1. 本ごとの数

| 本 | 割る行 | 書き換えた import の文(src・tests・tools・docs) | 分けた文 | 鍵 | 台帳の道 | 道の文字列 | 手で直した読み | 写さなかった | 守り | byte-check | 契約 | 例外 載せた・効いている(辺/行) |
|---:|---|---|---:|---:|---:|---|---|---|---|---|---|---|
| 1 | `world/assets.py` | 55(23・32・0・0) | 1 | 2 | 1 | src の表 2・tests の記号 2 | 1(`tests/engine/test_assets_10e_b0_b1.py`) | `__all__` の中の注 5 | 全部「同じ」 | 19/19 同じ・終了コード 0 | 3+9 → 3+9 | 31/45・19/29 |
| 2 | `agents/state.py` | 199(65・125・3・6) | 67 | 7 | 1 | src の表 2・tests の記号 8 | 1(`docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py`) | 無い | 「同じ」・決まり=宣言どおり 4 | 19/19 同じ・終了コード 0 | 3+9 → 3+9(古い 4 本から名 `agents` が外れた) | 32/46・20/30(割 1 が載った) |
| 3 | `engine/calendar.py` | 36(16・19・0・1) | 0 | 3 | 1 | tests の記号 1・tools の記号 1(`ROOT_READERS`) | 1(`tests/engine/test_calendar_10e_e3.py`) | 無い | 全部「同じ」 | 19/19 同じ・終了コード 0 | 3+9 → 3+9 | 31/45・20/30(28 本の #8 `mind.judge.classical -> engine.calendar` が消えた) |

- 書き換えた import の文と道の文字列は、道具の報告(`split_NN_report.json`)の数。道の文字列の「src の表」は許可の一覧 (b-src) の表の書き換え(固定の表の値)、「記号」は tests と tools の走査で書き換えた記号。
- byte-check の記録: `bytecheck_01_world_assets/`・`bytecheck_02_agents_state/`・`bytecheck_03_engine_calendar/`(このディレクトリの下。19 構成とも 37 欄=25 欄+第346 の 12 欄がすべて同じ・final が同じ 19・終了コード 0)。
- 例外の数は `cli.py contracts --stage delete --tree . --probe`(効いている=外すと契約が broken になる行と辺)。群の土台は 31/45・18/28(G1 の検収役が本体の木で測った・計画 §5-3 の模擬と同じ)。1 本目で効いている例外が 1 本増えたのは、もとから載っていた 28 本の #18 `perception.renderer -> world.model.assets`(決まり 3・消える段=段 7)が効くようになった分: 割る前の読む先 `world.assets` は決まり 3 の禁じる側(単位 world.model)の外にあり、割った後は `world.model.assets` になって、`mind.memory.memory_store` → `perception.renderer` → `world.model.assets` の連なりが決まり 3 に当たる。この例外がその連なりを切る(#18 の注=段 7 で renderer を割るまで、のとおり)。

### 9-2. 手で直した読みと、中身を見た試験

- 1 本目 `tests/engine/test_assets_10e_b0_b1.py`: 別名 `WA` の素の使い方 2 か所(`monkeypatch` で `file_sha256` を差し替えるモジュールの並び・消した口の名の `hasattr`)を、名の定義の置き場(`WA.file_sha256.__module__`・`WA.load_assets.__module__`)から引く形にした。道具は `WA` を主な割り先 `world.model.assets` へ書き換えた。消した口の名は、割った後は主な割り先でだけ見る(2 つ目の割り先 `foundation.vocab.place_words` へ行くのは店の語の定数 `SYNTHETIC_POI_CATS` だけ)。
- 2 本目 `docs/bench/analysis/c10-relations-2026-09-28/rel8b_measure.py`(記録の道具): `getattr(S, "RELATION_FIELDS", ())` を `from shibuya.agents.state import RELATION_FIELDS` に替えた(関係の列の名は agent_codes へ・`AgentState` は agent_table へ分かれる)。既定の値 `()` は `RELATION_FIELDS` が無かった古い木のための形で、今の木では同じ値。中身を見た試験 `tests/engine/test_two_phase.py`: `.thaw(` の呼び手は割った後も `world/model/agent_table.py`(`AgentState` の中)と `world/model/state.py` だけ(2 つ目の割り先 agent_codes に呼び手は無い)。逐次ループ宣言の一覧は道具が `world/model/agent_table.py` へ向け、主な割り先は元の docstring(宣言を含む)を持つ。
- 3 本目 `tests/engine/test_calendar_10e_e3.py`: 別名 `CAL` の素の使い方 1 か所(消した切替口の名の `hasattr`)を、`SimCalendar.__module__` から引く形にした(2 つ目の割り先 `foundation.types` へ行くのは `ticks_per_day` だけ)。`tools/bytecheck/tree.py` の `ROOT_READERS` の鍵は、道具が道の文字列の走査で `shibuya/world/facts/calendar.py` へ書き換えた(手では直していない)。直した後に `tests/tools/test_bytecheck.py` を通してから byte-check を回した。

### 9-3. 写さなかった import と注

- 1 本目: `__all__` の中の区切りの注 5 行(§3-2 と同じ)。2 本目・3 本目: 無い。

### 9-4. 再検収(review_g0_2)の低 4 件

1. 決まりの守りの粒度: `contracts.weakened` に、前から言えない決まりで「言えない名の並び」(理由の文「…もの: a, b」)に増えた名・`uncovered` に増えたモジュール・`late_allowed` に増えた読み手・載せた例外の行の増え(28 本・§6-6・表の外の表。`[[ignore_split]]` はその本の宣言なので除く)を足した。宣言には `other`(報告の文そのもの)を足した。理由の文がほかの形(「最終の名でないモジュールがある(… ほか N)」など)のときは、言い回しの数が動くだけで、言える範囲は (決まり, 名) で比べている=中身の文字列は比べない。広げた守りで 2〜17 本を書かない実行で順に当て、宣言の外の増えと当たらない宣言はどちらも 0。試験 `test_split_weakened_sees_more_than_new_rule_names`。
2. 既に在る割り先と同じ名の確かめは、その割り先が割る元からその名を import しているだけの形も断る=安全な側に倒している(割った後は自分を読む import になるので、その import を落とせば足りる形)。5a の既に在る割り先は割る元から import しないので当たらない。5b で当たったら直す。
3. 記録の冒頭が指す第347 の報告 §2 は、親が「18 本目の `mora_count` は延ばします」に直した(同じ報告の §11 の表 17 も「延ばす」)。記録の参照の文(計画の要旨は §2)と食い違わない。
4. `test_persona_does_not_reference_llm_ports` に足した元の置き場の確かめは import の文だけを見る(`importlib` の文字列で新しい置き場を読む形は、字面の "llm" の検出器が見る範囲の外)。足しただけで前より狭くはない。そのままにする。

### 9-5. 狙いの試験(作業の木・1 本ごと・`-n 4`・`-m "not slow"`)

| 本 | 回したもの | 結果 |
|---:|---|---|
| 1 | 作業木で変わった試験のファイル(G1 の分)・`tests/tools`・`tests/test_places_guard.py`・`tests/c8/test_places_rule_copies.py`・`tests/engine/processes` | 1275 passed・20 skipped |
| 2 | 同じ形(変わった試験のファイルが増えた・`test_two_phase` を含む) | 2919 passed・20 skipped |
| 3 | 同じ形(`tests/tools/test_bytecheck.py` を含む。byte-check の前に `test_bytecheck` を単独でも回した=123 passed) | 3118 passed・20 skipped |

- 飛んだ 20 本は、どれも `tests/tools/test_pkgmove.py` の段 4 の理由(「当てる段が無い木」ほか=前からの理由)。
- `lint-imports` は 3 本とも 12 kept・0 broken。byte-check は 1 本 7 分ほど(基準の側 210〜216 秒・比べる側 206 秒)。

### 9-6. 割った後に、置き場で範囲が決まる決まりに合わせて直した所(宣言)

- **3 本目 `engine/calendar.py` → `foundation/types.py` の `ticks_per_day` の docstring を 1 か所直した。** 前「1 日の tick 数(``tick_seconds`` が 1 日を割り切らなければ ``ValueError``)。」→ 後「1 日の刻みの数(``tick_seconds`` が 1 日を割り切らなければ ``ValueError``)。」。字面だけで、コードは変えていない。
- 理由: 決まり「核と系の注釈と docstring に素の tick を書かない(刻み・計算のまとめにする・名の引用はバッククォートで)」(`tests/engine/time/test_t0_no_tick_word.py::test_no_bare_word_in_comments_and_docstrings_of_core_and_systems`)の範囲は置き場で決まる。元の置き場 `engine/calendar.py` は範囲の外で、割り先 `foundation/types.py` は範囲の中だった。G1 の狙いの試験はこの試験を含んでいなかったので、親の範囲の全体の試験で見つかった。
- 道具の守り(① 文・② 定数)は元の文と割り先の文が同じことを確かめた後に、この 1 か所を手で直した=② の「元と割り先の定数が同じ」から外れるのは、この 1 つの文字列だけ(宣言)。済んだ割る行の判定(`split.is_done`=名が割り先の頂上に在り、元のファイルが無い)は docstring を見ないので、変わらない。
- `__doc__` を読む所: src に無い(`grep "__doc__"` は 0 件)。docstring を読む道具(カードの `tools/repo_guide/build.py` ほか)は記録と案内だけ。カードは作り直した。
- 親がこの直しの後に byte-check をもう一度回す(src を変えたため)。
- G2 からは、1 本ごとの狙いの試験に「置き場で範囲が決まる決まりの試験」の束(`tests/engine/time`・`tests/engine/state`・`tests/engine/bridging`・`tests/engine/systems`・`tests/test_places_guard.py`。`tests/validation` は今は無い)を足す。割ると名が別の包みへ移り、今まで範囲の外だった文が範囲に入ることがあるため。

### 9-7. 検収(review_g1)の低と、残すもの

- 決まりどおり書き換えない docstring の例 2 か所(`engine/change_detect.py` の 260 行目・`perception/renderer.py` の 1129 行目の `>>> from shibuya.agents.state import AgentState`)は、無くなった包みを指すようになった。doctest は回していない(pyproject と CI に設定が無い)ので結果には効かない。段 8 の文の掃除で直す(renderer の docstring は宣言の見出しがあるファイルなので、今は触らない)。
- 親の byte-check の記録 `bytecheck_G1_parent/` は親が commit に載せる(実装役は触らない)。

### 9-8. 親の確かめ(群 1)

- byte-check(3 本とも当てた木・基準 `adbe8bb`=群の土台): 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・final が同じ 19(既定
  `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939)。§9-6 の docstring の直しの後に回し直した値。組は
  [bytecheck_G1_parent/](bytecheck_G1_parent/)。実装役が 1 本ごとに回した 3 組(`bytecheck_01`〜`03`)も、すべて同じ。
- 範囲の全体の試験(`tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`・linked の作業木・土台 `adbe8bb` の上): 6,918 passed・
  2 failed・21 skipped・1 xfailed(37 分 41 秒)。落ちた 2 本は、前からの
  `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(linked の作業木でだけ落ちる)と、
  `tests/engine/time/test_t0_no_tick_word.py::test_no_bare_word_in_comments_and_docstrings_of_core_and_systems`(§9-6=割って
  `foundation/types.py` へ移った docstring の語)。後者は §9-6 のとおり直し、その試験(6 passed)と決まりの試験の束(316 passed)を回し直した。
- 本体の頭 `9495521`(版上げ Q13 の試験の直しと台帳が入った)へ載せ直した後: 両方の枝が変えた試験 8 ファイル(Q13 が引数を足し、
  群 1 が import の文を書き換えた)と、決まりの試験を回し直した(結果は commit の文に書く)。
- 別の役の検収: 受入(高 0・中 0・低 3)。割った 3 本の頂上の文は、元と数・並び・字面が完全に同じ。import の文のほかに変わった行は、
  宣言された物だけ。
- 飛んだ試験(skipped)は 21 本で、群の前と同じ。

## 10. G2 の当て(本物の木・群の土台 `bf0ccbb`=G1 の commit・安定版のタグ `stable-v2-before-split5a-G2`)

- 回し方は G1(§9)と同じ。狙いの試験に、置き場で範囲が決まる決まりの試験の束(`tests/engine/time`・`tests/engine/state`・`tests/engine/bridging`・`tests/engine/systems`・`tests/test_places_guard.py`)を入れた(§9-6)。親の範囲の試験と重なる間は `-n 2`。
- 当てる前に、foundation/vocab/events.py へ足す文(注と docstring と識別子)を、核の決まりの試験の関数(素の tick・tick を含む識別子)で見た。当たる所は無い(events は、その決まりの範囲=元の置き場が core と engine/systems の外でもある)。
- 1 本の byte-check が通るたびに、戻り点(`git diff --binary HEAD` と未追跡のファイルの写し)を作業の置き場に残した。

### 10-1. 5 本目(record)の循環と、直したこと

- **起きたこと**: 表 §4-16 のとおり `SIGNBOARD_CAUSE: Final[Process] = Process("perception")` を `foundation/vocab/events.py` へ割ると、道具は events に `from shibuya.foundation.journal.log import Process` を足す。`foundation/journal/log.py` は頂上で `from shibuya.foundation.vocab import events as V` を読むので、events → journal.log → events が循環した。`--apply` の後の import の確かめで 357 のうち 38 モジュールが落ちた(終了コード 3)。書かない実行の守り 11 個は「同じ」だった(既に在る割り先へ足す import が、その割り先を読むモジュールと循環する形を見る守りが無かった)。
- **手順の誤り**: 同じコマンドの続きで `contracts --stage delete --apply` を走らせ、壊れた木で `pyproject.toml` を書いた(`--apply` の終了コードを見ていなかった)。以後、1 本ごとの手順は `&&` でつなぐ。
- **戻した**: 親の手順で、道具の差分(4 本目の後 → 5 本目の後)を `git apply -R --check` → `git apply -R` で戻し、差分に載らない 0 バイトの頭 `engine/tools/__init__.py` を `git checkout` で戻し(単独のコマンド)、`pyproject.toml` は `contracts --apply` で 4 本目の後の節へ戻した。戻した後: `git status` の一覧が 4 本目の後と同じ・import の確かめ 357/落ちた 0・`python -m shibuya.cli --help` 0・lint 12 kept・4 本目の狙いの試験 1151 passed・20 skipped。
- **親の裁定=案 A(仮採用・ユーザーの判断待ち)**: `SIGNBOARD_CAUSE` は `foundation/journal/log.py`(`Process` の定義と同じ所)の後ろへ。`SIGNBOARD_ORIGIN`・`SIGNBOARD_WHAT` は表のとおり events。最終の表の意図(`SIGNBOARD_*` を foundation へ下ろし例外 #12 を消す)を保ち、違いは foundation の中のファイル 1 つだけ。この循環は 11-05 の案の表(`docs/reference/package-map-claude-code-2026-11-05.md` の「割った後のモジュールの 7 組」の 1 行目)が先に見つけていた。全ファイルの表 §3 の行 283・§4-16 を直し、`map.toml` を道具で作り直した。
  - 当てる前に確かめたこと: (1) `Process` は作る口の検査を持たない(口の検査 `_only_from_gate` は `Experiment` だけ・`_SEALED` は子の型を作るときだけ)。`Process("perception")` は record が今も読み込みの時に作っている。道具は文を log.py の後ろ(`Process` の定義と封の後ろ)へ足す。(2) log.py の名を固定する試験・表(`__all__` の確かめ・名の凍結・クラスの名の表・つなぎの台帳の道・核の決まりの語)に当たる所は無い(`__all__` には道具が 1 名足す)。(3) 新しい守りで循環は「同じ」・lint 12 kept(下)。
- **足した守り**(検証で見つけた欠陥の直し): `split.py` の「import の循環」。読み込みの時に走る import(頂上と頂上の if・try・with の中。`TYPE_CHECKING` の下と関数の中は除く・親の包みの頭を含む)のグラフで、割る前に無かった循環ができたら書く前に止める(終了コード 2)。止めた文に循環のモジュールと新しい辺・読む文の場所を出す。新しい割り先は元のモジュールの名に引き戻して比べる。今の表のままの 5 本目を新しい守りが止めることを確かめた(`循環 ['shibuya.foundation.journal.log', 'shibuya.foundation.vocab.events'] の新しい辺: events -> journal.log(events.py:101 Process)`)。試験 `test_negative_split_stops_a_new_import_cycle_through_an_existing_destination`(循環する割り先は止め、循環しない割り先は通す。守りを外すと落ちる)。
- 守りを足した後、5〜17 本の書かない実行を取り直した: import の循環に当たる本は 0(案 A の 5 本目を含む)。宣言の外の弱まりも 0。

### 10-2. 本ごとの数

| 本 | 割る行 | 書き換えた import の文(src・tests・tools・docs) | 分けた文 | 鍵 | 台帳の道 | 道の文字列 | 宣言した書き換え | 手で直した読み | 写さなかった | 守り | byte-check | 契約 | 例外 載せた・効いている(辺/行) |
|---:|---|---|---:|---:|---:|---|---|---|---|---|---|---|---|
| 4 | `engine/tools/registry.py` | 16(5・11・0・0) | 1 | 3 | 1 | tests の記号 1 | — | 2 | 無い | 11 個「同じ」(循環の守りを足す前) | 19/19 同じ・終了コード 0 | 3+9 → 3+9 | 31/45・21/32(#11 が効くようになった) |
| 5 | `engine/tools/record.py`(案 A) | 14(3・11・0・0) | 2 | 2 | 1 | 無い | events で 2(`V.word`・`V.FAMILY_TOOL`) | 1+1(案 A で 1 増えた) | 無い | 12 個「同じ」 | 19/19 同じ・終了コード 0 | 3+9 → 3+9 | 30/43・20/30(#12 が消えた) |
| 6 | `engine/events/body.py` | 4(2・2・0・0) | 0 | 1 | 1 | 無い | events で 12 | 1 | 無い | 12 個「同じ」 | 19/19 同じ・終了コード 0 | 3+9 → 3+9 | 30/43・20/30 |

- 割り先: 4 本目 `society/tools/registry.py`(新)・`foundation/vocab/events.py`(在る・`SIGNBOARD`)/5 本目 `society/tools/record.py`(新)・events(在る・`SIGNBOARD_ORIGIN`・`SIGNBOARD_WHAT`)・`foundation/journal/log.py`(在る・`SIGNBOARD_CAUSE`)/6 本目 `mind/memory/body_events.py`(新)・events(在る・語と種類の 10 名)。events へ足した名の順は SIGNBOARD → SIGNBOARD_ORIGIN・SIGNBOARD_WHAT → WHAT_SIGNAGE ほか(計画 c7)。
- 消えた頭: 5 本目で `engine/tools/`、6 本目で `engine/events/`。record の版の ID `shibuya.engine.tools/c0/1` と `_ENABLED`(読み込みの時に環境変数を読む)は主な割り先 `society/tools/record.py` に同じ値で入った。非公開の名(`_WHAT_OF_KIND`・`_KIND_TALK`)は名を変えずに events へ。
- 効いている例外: 4 本目で 1 本増えたのは、もとから載っていた 28 本の #11 `mind.judge.decision.layer -> society.tools.registry`(決まり 1・3・消える段=残る)。割る前の読む先 `engine.tools.registry` は決まりの単位の外で、割った後の `society.tools.registry` は単位の中になった(G1 の #18 と同じ形)。5 本目で #12 `engine.events.body -> engine.tools.record` が消え(計画どおり)、計画 §5-3 の G2 の終わり 30/43・20/30 と同じになった。
- 心の読みの一覧: 6 本目で `engine/events/body.py` が無くなったので、`tests/engine/state/mind_world_reads_frozen.json` の `scope.split` からその行を外した(記録 `self-update-347` の裁定 6 のとおり。割り先 `mind/memory/body_events.py` は `scope.dirs`=`mind/` の下に来る。body の心の読みは 1 行(`conversation_end` の `cell`)で、割る前から割り先の道で数えていたので、`key_counts` の合計 83 は変わらない=検収の低 2 で直した文。前の文は「心の読みが無い」と書いていた)。
- 1 本ごとの戻り点: 4 本目の後 `restore_04`・5 本目の後 `restore_05`(作業の置き場)。

### 10-3. 手で直した読み

- 4 本目: `tests/engine/tools/test_c0_affordance_from_registry.py`(`TR.SIGNBOARD` を名の import に・`monkeypatch.setattr(TR, "TOOL_ACTION_WORDS", …)` の相手を、それを読む `affordance_words` の定義の置き場 `_TR_MOD` から引く形に=5 か所)・`tests/engine/tools/test_c0_tool_registry.py`(`TR.SIGNBOARD` を名の import に)。
- 5 本目: `tests/engine/tools/test_c0_signboard_mark_invariance.py`(`TR.SIGNBOARD_ORIGIN`・`SIGNBOARD_WHAT`・`SIGNBOARD_CAUSE` を名の import に)・`tests/engine/multiday/test_md23_body_events.py`(案 A で `SIGNBOARD_CAUSE` だけ別の割り先へ行くので、`TR.SIGNBOARD_CAUSE` を名の import に=案 A で増えた 1 つ)。
- 6 本目: `tests/engine/multiday/test_md23_body_events.py`(`B.` で読む events 行きの 6 名=`KIND_ACT_WORD`・`WHAT_NOTICE`・`WHAT_SIGNAGE`・`WHAT_TALK_END`・`WHAT_TALK_OPEN`・`kind_of_what` を名の import に)。

### 10-4. 狙いの試験(`-n 2`・`-m "not slow"`。決まりの束を含む)

| 本 | 結果 |
|---:|---|
| 4 | 1136 passed・20 skipped(戻した後にもう一度 1151 passed・20 skipped) |
| 5 | 1268 passed・20 skipped(道具の試験 `tests/tools` の全部=slow を含む 724 passed・20 skipped を先に回した) |
| 6 | 1390 passed・21 skipped |

- 飛んだのは、`tests/tools/test_pkgmove.py` の段 4 の理由 20 本と、6 本目の束に入れた `tests/engine/memory/test_m2_cue.py` の 1 本(「Ruri の重みが置き場に無い」=前からの理由)。
- `lint-imports` は 3 本とも 12 kept・0 broken。
- byte-check の記録: `bytecheck_04_tools_registry/`・`bytecheck_05_tools_record/`・`bytecheck_06_events_body/`(基準 `bf0ccbb`=群の土台・その本まで当てた木と比べる。19 構成とも 37 欄がすべて同じ・final が同じ 19・終了コード 0。1 本 7 分ほど)。4 本目の byte-check は合図のファイルが親の byte-check で塞がっていたので、空くのを待ってから回した。

### 10-5. 親の確かめと別の役の検収(第347)

- **別の役の検収: 受入(高 0・中 0・低 3)**。今の道具と表で 4〜6 本目をメモリの中で当て直し、できた src が作業木と完全に同じことを確かめた
  (違いは手で直した試験 4 本と道具のファイル 2 本だけ)。割り先と、既に在る 2 本へ足した 14 文は、元と数・並び・字面・前の注が同じ。
  宣言した書き換え 14 か所は、AST の属性の位置だけを書き換えた形と一致。案 A に壊れる所は無い(log.py に import は足していない・増えるのは
  `Process("perception")` を 1 つ作ることだけ・原因は値で比べる)。読み込みの時の import の循環は、群の前も後も前からの 1 組(parser・llm・
  fleet・mock)だけ。差し替えの相手 `_TR_MOD` は空振りしない。
- 検収の低: ① 循環の守りは強連結成分の単位で比べるので、割る前から在る循環の中で読み込みの順が変わって落ちる形は見ない(G3 の llm の 4 本は
  今その循環の中に在る=書いた後の import の確かめが本当の守り。G3 の発注に書いた)② §10-2 の「心の読みが無い」の文(直した)③ 親の
  byte-check の記録 `bytecheck_G2_parent/` は commit に載せる(G1 と同じ)。
- **親の byte-check**(本体の頭 `9f4fa77`=版上げ Q13 の後へ載せ直した木・`--base 9f4fa77`): 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0
  (既定の final `c8d68704b7b0760d`・呼数 60,939・全体の壁時計 433 秒)。記録 [bytecheck_G2_parent/](bytecheck_G2_parent/)。
- 載せ直し: ぶつかったのはカード 2 枚だけ(作り直した)。src・tests・tools にぶつかりは無い。載せ直した後の `lint-imports` は 12 kept。
- **範囲の全体の試験**(載せ直した木): 6,927 passed・1 failed・21 skipped・1 xfailed(39 分 8 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(linked の作業木でだけ落ちる)。新しい失敗は無い。飛んだ試験は 21 本で群の前と同じ。増えた 2 本は、循環の守りの試験。
