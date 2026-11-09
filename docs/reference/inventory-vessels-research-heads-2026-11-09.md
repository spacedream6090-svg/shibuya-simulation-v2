# 器と研究の残りの棚卸し(2026-11-09)

> 発注: [返事その 6](../design/prompt-2026-11-05-reply6.md) §3-2 の 3(`11-05/§3-2`)と、[返事その 7](../design/prompt-2026-11-09-reply7.md) §2 の 5(`11-09/§2`)。文書役(Opus 5.5)が作りました。
>
> **この作業では何も消していません。消すのは、ユーザーの側でこの表を確かめてからです(11-05/§3-2 の 3 の原文)。** src・tests・tools・設定のファイルは 1 バイトも変えていません。
>
> コードの版は枝 `stage/inventory` の HEAD `14b151a` で、行番号はこの版のものです。ランも pytest も回していません。
>
> 確かめ方: 対象の一覧は [技術マップ](tech-map-2026-11-03.md) の §0-5 と §1 の表から作りました。呼び手は、src・tests・tools に加えて docs/ の下の計測のスクリプト 287 本(byte-check の道具もここにあります)まで調べました。import を AST で集め、ファイルの頭の import と関数の中の import を分けて数えました。結果は [カード](repo-guide/cards/README.md) の「呼び手」の欄とも照らしました。数えたスクリプトはリポに入れていません。
>
> 開いていないもの: IMPLEMENTED.md・build-report-C7/C8・門 1 の計画・パターン台帳・`data/` の下・検証の側の錨の JSON・handover-memory.md。Web は使っていません。

## 要約

- **対象は 32 本です。** 技術マップの「器だけ」15 本、「研究」10 本、それに呼び手の無い再輸出の頭 7 本です。15 本と 10 本は技術マップの数と合いました。7 本という数は技術マップには無く、包みの照らし合わせ(案 F)から来ています。数え直しても 7 本でした(§1)。
- **案ごとの数**は、**消す 8 本**、**残す 22 本**、**v3 で使う 2 本**です。
  - 消す 8 本: 中身の無い頭 `census/__init__.py` と、再輸出の頭 7 本の再輸出。
  - v3 で使う 2 本: 人物の欄 `engine/decision/persona.py` と、印象の器 `engine/memory_impression.py`。
  - このほか、死んだ道 2 つは「別の段で消す」です(§5。32 本には数えていません)。
- **「器」「研究」と言い切れないものが 10 本ありました。** 消すと既定のランの結果か記録が変わるので、残す側に入れました。
  - `world/processes/constitution.py`: 起動時の門で、既定の道を通ります。技術マップの「研究・いいえ(定数だけ読む)」は誤りです。
  - `economy/pricing.py`: 係数が原価と参入資本に効きます。
  - `economy/credit.py`: 容量 0 の帳面を作り、記録に載ります。
  - `engine/body/system1.py`: manifest に載り、連絡の腕 c1 が呼びます。
  - `engine/tools/` の 4 本(groups・places・record・registry): 組み立てが毎回作り、manifest に載ります。
  - `engine/systems/probe.py`: 進行役が読みます。
  - `build/sched/trial.py`: W20 暦 1a の構築が使います。
- **ユーザーに確かめてほしい行**(表の〔確認〕の印・7 つ)
  1. 表 A #1 `census/__init__.py`: 消すなら、`pyproject.toml` の import-linter の契約 3 本(層の契約)から `shibuya.census` を外す直しが要ります。
  2. 表 A #3 `economy/pricing.py`: 係数は残します。結線しないと決まった関数(Calvo の改定・逸脱比例コスト・`propose_price`)を消すかを決めてください(仕様 EO-18)。
  3. 表 A #7 `engine/memory_trace.py`: 世界の出来事の記録から組み立てる今の形が、11-09 の「心に渡すのは知覚だけ」「溜めない・数秒の名残だけ」と合うか、確かめてください。
  4. 表 A #8 `engine/processes/rail_events.py`: docstring にある予定(版上げ 3 回目で読む)は過ぎましたが、結線されていません。鉄道の秒の段(WD-34・未決)まで残すでよいか、確かめてください。
  5. 表 A #15 `world/processes/deletion_candidates.py`: D-R2-4 の「CI が削除候補を台帳へ自動で足す」が結線されていません。CI へ結線するか消すかを決めてください。
  6. 表 C #4 `manifest/__init__.py`: 試験 1 本が頭から 9 個の名を読んでいます。頭を空にするなら、その試験の import も直します。
  7. 表 C の 7 本全部: 頭を空にすると import の順が変わります。消す前と後で byte-check 19 構成と全体の試験を回す前提でよいか、確かめてください(§7)。

## 1. 対象の一覧と数

| 区分 | 数 | 出どころ | 合ったか |
|---|---:|---|---|
| 器だけ | 15 | 技術マップ §0-5 の表の計と、§1 の表の「器だけ」の行 | 計 15・行 15 で合う |
| 研究 | 10 | 同じ | 計 10・行 10 で合う |
| 呼び手の無い再輸出の頭 | 7 | 技術マップには無い。[照らし合わせ](package-map-reconcile-2026-11-05.md) §6 の「再輸出の頭 7 本の src の呼び手 0」(案 F の数・照らし合わせ役が確かめた) | 数え直して 7 で合う(下) |

再輸出の頭は、次のように数え直しました。

- `src/shibuya` の下の `__init__.py` は 36 本です。そのうち import 文を持つ頭が 17 本あります。
- 17 本から build の下の 7 本(audit・field・geo・lang・pop・sched・vis)を除くと 10 本です。build の 7 本は段の一覧 `STAGES` などの中身を自分で持っているので、再輸出だけの頭ではありません。この 10 本は[案 K](package-map-claude-code-2026-11-05.md) の「再輸出の頭 10 本」と合います。
- 10 本のうち、頭から名を読む呼び手が src にあるのは次の 3 本です。
  - `economy/__init__.py`: `cli.py` が読む。
  - `engine/body/__init__.py`: `engine/systems/build.py` が読む。
  - `llm/__init__.py`: 30 本が読む。自分のクラスと関数も持っている。
- 残りの 7 本が表 C の対象です。この 7 本は tests・tools・docs の計測のスクリプトからも、`manifest/__init__.py` を読む試験 1 本を除いて読まれていません。
- 名前が似ていても、次のものは対象外です。
  - build の頭 7 本(本数は同じ 7 本ですが別物)。
  - 中身の無い頭 `census/__init__.py` と `engine/tools/__init__.py`。どちらも再輸出は無く、器だけの 15 本に入っています。

## 2. 表 A 器だけ(15 本)

表の「呼び手」の欄で、src の(頭)はファイルの頭の import、(関数)は関数の中の import です。「docs の計測」は docs/bench の下の過去の記録のスクリプトです。

| # | ファイル | 今の中身 | 呼び手 | 決定の出どころ | 案 | 理由 |
|---:|---|---|---|---|---|---|
| 1 | `census/__init__.py` | 4 行の docstring だけ(「診断行・センサス・被覆指標の読み取り専用集計」)。経済センサスは別の `economy/census.py` にある | src・tests・tools・docs の計測とも 0。`pyproject.toml` の import-linter の契約 3 本が名を挙げる | `11-05/§3-2`(3)・照らし合わせ §2-2(消してよい)・案 K「消す候補」 | **消す** 〔確認 1〕 | 中身も呼び手も無い。消すときは契約 3 本を同じ commit で直す |
| 2 | `economy/credit.py` | 信用の器 C1〜C3(`CreditBook`・`repay_due`・利息の上限と総量の検査) | src: `economy/ledger.py`(関数)。`attach_stage2` が `CreditBook(capacity=0)` を作り(ledger.py:403-410)、記録に載せる(ledger.py:395)/ tests 3 本 | `10-12/§4-11`・R-106・R-118。仕様 EO-13(仮決定・差 G-186=器だけ) | **残す** | 既定(段階 2 が on)で容量 0 の帳面を作り、記録に載る。消すと記録が変わる。返済などの関数は試験だけが呼ぶ。EO-13 の信用の中身を足す先 |
| 3 | `economy/pricing.py` | 価格形成のエンジン側(内生フロアの係数 k・Calvo の改定・逸脱比例コスト・`propose_price`) | src: `economy/goods.py`(頭)。係数 `K_VOLUME`・`K_AVERAGE`・`K_PREMIUM` を `CATEGORY_K` に使う(goods.py:60・181-183)。参入資本の原価率もこの表を使う / tests 2 本 | D-R2-3 の行 5・H-1〜H-5(世界過程の設計書)を `11-01/A1-2`・`11-01/A1-3`・`11-01/§10`(#101)が上書き。仕様 EO-18(Calvo は結線しない・β を E7 で較正しない) | **残す** 〔確認 2〕 | 係数は既定のランの補充の代金と参入資本に効く(段 2 の突き合わせ §1 の 10)。関数の部分は EO-18 で結線しないと決まった。関数だけ消すかを確かめてほしい |
| 4 | `engine/body/system1.py` | 意図しない System 1 の反応の口 3 つ(ロンバード効果・混雑の中の歩き方・大きな音に向く注意)。値は空(None)。騒音の段の読み口 `noise_stage_at` | src: `engine/body/model.py`(頭・manifest の `body.system1` に `manifest_rows`・model.py:282)・`engine/contact/layer.py`(頭・腕 c1 が `noise_stage_at` を呼ぶ・layer.py:91・955)/ tests 2 本 | `10-12/§1-5`。仕様 WD-07(差 G-053)・WD-22(差 G-068) | **残す** | 既定のランの manifest に載り、連絡の腕 c1 が呼ぶ。3 つの口は、空間の段で値が入る先。docstring の「読み手が居ない」は古い(段 2 の突き合わせ a の #1) |
| 5 | `engine/decision/persona.py` | 人物の欄の読み口(短い版・長い版)と差し替えの口(`load_persona`・`persona_blocks`・`override`) | src 0 / tests 1 本(`tests/engine/test_pop_w21_world.py`) | `10-12/§4-7`・仮-33 (6)。仕様 MD-12(研究待ち・差 G-107) | **v3 で使う** | 心の段で、本人の文を判断と LLM の入力へ渡す口になる。中身(性格・生い立ち)は MD-12 の研究待ちなので、読み口の形は変わりうる |
| 6 | `engine/memory_impression.py` | 記憶 M3 の器。印象の履歴と、本人が寝たときの書き直し(`ImpressionBook`)。持つのは文だけ | src 0 / tests 1 本 | `10-12/§4-6`(MR3・MR13)・`11-09/A-05`(記録 2-32)。仕様 MD-06(差 G-101)・MD-39(差 G-133) | **v3 で使う** | 11-09 の A-05「本人が持つのは印象の文だけ」と形が合う。書き直す時機(寝たとき)は、`11-09/A-08` の習慣の文と同じ |
| 7 | `engine/memory_trace.py` | 注意を向けずに見ていた人の浅い痕跡(`shallow_trace`・`trace_word`)。保存はせず、手がかりが来たときに出来事の記録から組み立てる | src 0 / tests 1 本 | `10-12/§4-6`(MR6)。仕様 MD-39 の M5(差 G-133) | **残す**(記憶の壁打ちまで)〔確認 3〕 | 世界の側の出来事の記録を読んで組み立てる形が、11-09 の「心に渡すのは知覚だけ」(`11-09/§4-1` の問い 1・記録 2-33)と「溜めない・数秒の名残だけ」(`11-09/A-14`・記録 2-27)に合うか分からない |
| 8 | `engine/processes/rail_events.py` | 渋谷の発着の表(W12 1.3.0)を読む口。`READ_RAIL_EVENTS = False` なので、既定のランでは読まない | src 0 / tests 1 本(`tests/build_rail/`) | 実装の計画 10-12 の第 2 期 2-3c(docstring)。仕様 WD-34(未決・差 G-080) | **残す** 〔確認 4〕 | 鉄道の秒の段の題「到着の表」が未決。docstring の「呼ぶと決めるのは版上げ 3 回目」は過ぎたが、結線されていない |
| 9 | `engine/tools/__init__.py` | 道具の台帳 C0 の包みの頭。docstring だけで、再輸出は無い | 包みの印(下の 5 本が使われている) | `10-12/§4-4`(CT0) | **残す** | 下のモジュールの包みの印。再輸出が無いので、空にする作業も要らない |
| 10 | `engine/tools/contacts.py` | 個人の連絡先に、手段ごとの印を付ける(`flags_from_kinds`・`tally`) | src: `engine/contact/book.py`・`engine/contact/layer.py`・`engine/relations.py`・`engine/relations_people.py`(どれも頭)/ tests 3 本 | `10-12/§4-4`・R-85 | **残す** | 腕(`--relations on`・`--contact c1`)が読む |
| 11 | `engine/tools/groups.py` | グループの一覧(家族と職場・`GroupList`) | src: `engine/contact/book.py`・`engine/contact/layer.py`・`engine/tools/record.py`(頭)/ tests 11 本 | `10-12/§4-4`(CT10) | **残す** | 既定のランでも、組み立てが母集団から毎回作る(build.py:1395)。連絡 c1・カレンダー 2・3 の腕が読む |
| 12 | `engine/tools/places.py` | 店の番号の場所の表(`PhoneTable`・C0 では空)と、OSM の電話番号の読み | src: `engine/tools/record.py`(頭)/ tests 3 本 / docs の計測 1 本 | `10-13b/§3` | **残す** | 組み立てが毎回空の表を作り、manifest の `tools` に載る(report.py:313-315)。消すと manifest が変わる |
| 13 | `engine/tools/record.py` | 道具の記録の欄と、ランの道具の一式(`build_fixture`・`manifest_fields`)。看板の記録の腕 | src: `engine/events/body.py`(頭)・`engine/systems/build.py`・`engine/systems/report.py`(関数)/ tests 9 本 / docs の計測 1 本 | `10-12/§4-4`・R-113 | **残す** | 既定のランの組み立てと manifest が通る。看板の記録は腕 `SHIBUYA_TOOL_EVENTS`(既定 off) |
| 14 | `engine/tools/registry.py` | 道具の台帳(`ToolRegistry`・`default_registry`・`affordance_words`) | src: `engine/contact/tools.py`・`engine/tools/record.py`(頭)・`engine/calendar_self.py`・`engine/decision/layer.py`・`engine/tools/places.py`(関数)/ tests 6 本 / docs の計測 1 本 | `10-12/§1-13`・`10-12/§4-4`(CT0)・`10-13b/§1`・R-85・R-113。仕様 SO-19(差 G-223)・PR-17(土台の 1 つ・`10-12/§0-3`) | **残す** | 毎回作られ、腕(判断の口 J0・暦 1b・連絡 c1)が読む。道具の台帳は 10-12/§0-3 の土台の 1 つ |
| 15 | `world/processes/deletion_candidates.py` | 「削除候補」の台帳ファイル(`runs/` の下)へ、同じ行を重ねずに足す口(`append_candidates`) | src: `world/processes/__init__.py` の再輸出だけ / tests 1 本 | D-R2-4(世界過程の設計書 §5)。仕様 WD-05(仮決定) | **残す** 〔確認 5〕 | 憲法 5 の検査(表 B #10)は起動時に削除候補を数えるが、それを台帳ファイルへ書く呼び手が無い。D-R2-4 の「CI が自動で足す」も結線されていない。CI へ結線するか消すかを確かめてほしい |

## 3. 表 B 研究(10 本)

| # | ファイル | 今の中身 | 呼び手 | 決定の出どころ | 案 | 理由 |
|---:|---|---|---|---|---|---|
| 1 | `build/field/w10_ruler.py` | W10 の物差し。較正点に町丁目の代表点を付け、騒音の場の値と実測の差を測る | src 0 / tests 1 本 / docs の計測 2 本(`docs/bench/analysis/wave2-2026-09-30/w10_ruler_measure.py` ほか) | `09-30/W10`(Q6 の物差し) | **残す** | 騒音の場の答え合わせの物差し。W10 の段には組み込まない作りで、構築の出力を変えない |
| 2 | `build/sched/trial.py` | D-68 下見(2,000 体・5 腕)の別の道(2,870 行) | src: `build/sched/w20_calendar_1a.py`(頭・相対の import・w20_calendar_1a.py:136)。`BinTable`・`_bin_table`・`anchor_path`・`load_anchor` と定数 3 つを使う / tests 3 本 / tools 1 本(`tools/instruments/anchor_gauge.py`)/ docs の計測 4 本 | D-63・D-67・D-68([下見の設計書](../design/v2-d68-pilot-design.md)) | **残す** | W20 暦 1a の構築と錨の計器が一部を使う。下見の腕の部分だけを割って外すかは、移す作業の後に別に決める |
| 3 | `core/serialize.py` | SoA の checkpoint(.npz と zstd)と、膨張率 M7 の測定 | src 0 / tests 2 本(`tests/core/test_serialize.py`・`tests/engine/test_determinism_t1_t2_t4.py`) | 第 141(v1 の膨張 13.6 倍の再発を防ぐ)・実装計画書 §5(M7 は 2.0 倍以下) | **残す** | 性能予算 M7 を機械で検査する試験が使い、CI で回る。ランの状態の保存は、別の `engine/state_codec.py` が受け持つ |
| 4 | `engine/bridging/scan.py` | コードにある expedient の宣言を AST で数え、つなぎの台帳と 1 対 1 で突き合わせる | src 0 / tests 2 本 / docs の計測 11 本 | 第 334 | **残す** | expedient のタグと台帳の対応を試験で守る(CLAUDE.md §4) |
| 5 | `engine/rng_audit.py` | 乱数の流れのブロックが重なっていないかの検査(K19) | src 0 / tests 5 本 | 第 330(10f・K25 (a)) | **残す** | 決定論を守る検査 |
| 6 | `engine/systems/overrides.py` | 試験の負の対照のため、系の宣言を一時的に差し替える | src 0 / tests 9 本 / docs の計測 1 本 | 第 1 期 1-0(草案 §3-1 の T1〜T3) | **残す** | 書きの宣言の検査が本当に落ちるかを確かめる対照 |
| 7 | `engine/systems/probe.py` | 系ごとの全欄の差と指紋(試験のときだけ動く) | src: `engine/systems/conductor.py`(頭・conductor.py:23)・`engine/experiment/branch.py`(関数)/ tests 12 本 / docs の計測 8 本 | 第 1 期 1-0(草案 §2-6 の B・§2-7) | **残す** | 進行役が頭で読む(既定のランでは何もしない)。消すと src を直すことになる。ランどうしが最初に食い違った所を探す道具 |
| 8 | `engine/systems/static_check.py` | 系の宣言と系のコードを AST で突き合わせる | src 0 / tests 2 本 | 第 1 期 1-0(草案 §2-6 の D) | **残す** | 宣言の外の書きを試験で見つける |
| 9 | `world/processes/circularity.py` | 循環(同じ値の系で動かして採点する)の機械検査 | src 0 / tests 1 本 | `11-01/§3`(A1-3 の案 a)・`11-02r/§1`(#6・#8)。仕様 VL-11 | **残す** | 決定どおりの検査そのもの |
| 10 | `world/processes/constitution.py` | 憲法 5 の機械検査(`check_constitution5`)と、その定数 | src: `world/processes/registry.py`(頭・検査を委ねる)・`first_batch.py`・`circularity.py`・`deletion_candidates.py`・包みの頭 / tests 4 本。**既定のランで `engine/processes/runner.py:216-223` が起動時に呼び、落ちたらランを止める** | D-R2-4(決定 2026-09-07)。仕様 WD-05 | **残す** | 既定のランの起動時の門。技術マップの「研究・いいえ(定数だけ読む)」は誤り(§6-3) |

## 4. 表 C 呼び手の無い再輸出の頭(7 本)

この表の「消す」は、再輸出の import と `__all__` を消し、docstring だけの頭にすることを指します。ファイルは包みの印として残ります。移す作業(`11-09/§4-2`)で包みごと無くなるものもあります。

| # | ファイル | 今の中身 | 呼び手 | 決定の出どころ | 案 | 理由 |
|---:|---|---|---|---|---|---|
| 1 | `agents/__init__.py` | 45 行。16 個の名を再輸出する(state・schedule・population) | src・tests・tools・docs の計測とも 0 | `11-05/§3-2`(3)・照らし合わせ §2-2(推しは「消す」)・案 K と案 F はどちらも再輸出を消す | **消す** | 呼び手は下のモジュールを直に読んでいる |
| 2 | `engine/__init__.py` | 75 行。30 個の名を再輸出する(arbiter・change_detect・clock・commit・scheduler・tape) | 0 | `11-05/§3-2`(3)・案 K と案 F | **消す** | 同上 |
| 3 | `engine/processes/__init__.py` | 39 行。7 個の名を再輸出する(crowd・environment・opening・rail・runner・traffic) | 0 | 同上 | **消す** | 同上 |
| 4 | `manifest/__init__.py` | 90 行。39 個の名を再輸出する(canonical・schema) | src 0 / **tests 1 本が頭から 9 個の名を読む**(`tests/test_manifest_roundtrip.py:16`) | 同上 | **消す** 〔確認 6〕 | 試験の import を下のモジュールへ直す必要がある(試験の変更になる) |
| 5 | `perception/__init__.py` | 158 行。61 個の名を再輸出する(attention・channels・hashes・normalize・p_notice・renderer・state・templates) | 0 | 同上 | **消す** | 呼び手は下のモジュールを直に読んでいる |
| 6 | `world/__init__.py` | 29 行。9 個の名を再輸出する(assets・graph・state) | 0 | 同上 | **消す** | 同上 |
| 7 | `world/processes/__init__.py` | 117 行。41 個の名を再輸出する(actual_log・constitution・deletion_candidates・records・registry・relations) | 0 | 同上 | **消す** | 同上。`deletion_candidates.py` の src の呼び手はこの頭だけなので、表 A #15 と一緒に決める |

## 5. 別の段で消すもの(死んだ道 2 つ)

| 部品 | 場所 | 案 |
|---|---|---|
| 会話の応答率 0.8 の抽選 | `engine/conversation.py:86-89`・`:449`(`answered=None` のときだけ引く。呼び手は全部 `answered=True` を渡す) | 別の段で消す(`11-05/§3-2` の 2) |
| 重要度上位の +2 呼 | `engine/conversation.py:92-93`・`:360`。組み立て `engine/systems/build.py:672` が `important` を渡さない | 別の段で消す(同上。台帳の行 `DOC-fix4-dead-important-extra-turns`) |

## 6. 照らし合わせの結果

### 6-1 包みの照らし合わせ(§2-2)で「消す」とした 2 本

- `agents/__init__.py`: 照らし合わせは「呼び手 0・消してよい」としています。この棚卸しでも、docs の計測のスクリプトまで見て呼び手は 0 でした。案は「消す」です(表 C #1)。
- `census/__init__.py`: 照らし合わせは同じく「呼び手 0・消してよい」としていて、この棚卸しでも呼び手は 0 でした。ただし `pyproject.toml` の import-linter の契約 3 本(層の契約・llm の禁止・build の禁止)が `shibuya.census` を名指ししています。消すなら、契約を同じ commit で直し、CI の ci-0 の lint-imports で確かめます。この契約は実装計画書 §3 の層の契約を写したものなので、直してよいかを確かめてください(確認 1)。

### 6-2 段 2 の突き合わせで「器」と言い切れないと分かったもの

[段 2 の突き合わせ](stage2-crosscheck-2026-11-05.md) の指摘と、この表での扱いです。

| ファイル | 突き合わせの指摘 | この表での扱い |
|---|---|---|
| `economy/pricing.py` | 係数 K は「原価=価格÷k」と参入資本の原価率に効くので、器ではない(§1 の 10・day-flow と can-say の #1) | 残す。関数だけ消すかは確認 2 |
| `economy/credit.py` | 既定で `CreditBook(capacity=0)` を作り、記録に載せる。「器」の区分は合うが「呼び手なし」は違う(day-flow と can-say の #2) | 残す |
| `engine/body/system1.py` | `noise_stage_at` は連絡の腕 c1 が呼ぶ(§1 の 5・a の #1) | 残す。manifest に載ることも、この棚卸しで分かった |
| `engine/tools/` の頭・contacts・groups・registry | 「C0 では誰も読まない」は C0 のころの文(b の #5) | 残す(腕が読み、組み立てが毎回作る) |
| `engine/decision/persona.py` | `load_persona`・`persona_blocks` の呼び手は src に無い(b の節 17。資料と合う) | v3 で使う |
| `engine/processes/rail_events.py` | `READ_RAIL_EVENTS=False` で呼び手は無い(a の確かめた主張。資料と合う) | 残す(確認 4) |
| `engine/memory_impression.py`・`engine/memory_trace.py` | 印象と浅い痕跡の口は呼び手なし(b の節 8。資料と合う) | v3 で使う / 残す(確認 3) |

### 6-3 この棚卸しで見つけた、技術マップとの違い

- `world/processes/constitution.py`: 技術マップは「研究・いいえ(定数だけ読む)」と書いています。実際には `world/processes/registry.py` が検査を委ね、`engine/processes/runner.py:217` が起動時に呼ぶので、既定の道を通ります。仕様の[差の一覧](../design/spec/gaps.md)の WD-05 の行(「起動時に走る」)とは合います。
- `engine/systems/probe.py`: 技術マップも「条件つき」と書くとおり、進行役が頭で読みます。研究の区分でも、消せば src を直すことになります。
- `build/sched/trial.py`: 技術マップの迷いの列のとおり、`w20_calendar_1a.py` が一部を使います。
- `engine/tools/` の groups・places・record・registry: 既定のランで組み立てが作り、manifest に載ります。結果のハッシュは変えません(`engine/tools/__init__.py` の docstring)が、消すと manifest が変わります。
- 研究の区分のうち scan・rng_audit・overrides・probe・static_check・circularity・serialize の 7 本は、試験(一部は docs の計測のスクリプトも)が読む守りの道具です。

## 7. 消すときの注意(ユーザーが確かめた後)

1. 消し方は 11-05/§3-2 の 1 と同じにします。消すたびに byte-check 19 構成を回し、安定版のタグを付け、戻す手順を 1 行書きます。消す・戻すコマンドは単独で、明示したパスだけで行います(`11-09/§1-4`)。
2. 頭を空にすると、どのモジュールがいつ読み込まれるかが変わります。たとえば今の `engine/__init__.py` は、`engine` の下のどのモジュールを読んでも、先に arbiter・change_detect・clock・commit・scheduler・tape を読み込みます。読み込みの順に頼る所があると、試験の結果が変わりえます。循環 import の解け方や、`engine/rng_audit.py:405` の `StreamRecorder` が読み込み済みのモジュールだけを差し替える所がそれに当たります。消す前と後で、全体の試験と byte-check を回します。
3. つなぎの台帳 `docs/design/bridging-ledger.json` には、表 A のファイルを指す行があります(grep の数で credit 3・pricing 3・system1 3・persona 3・memory_impression 1・memory_trace 1・rail_events 2・`engine/tools` 9)。今回「消す」にした 8 本(census と頭 7 本)を指す行は 0 です。表 A のファイルを後で消すなら、台帳の行の扱いも一緒に決めます(`engine/bridging/scan.py` の試験が 1 対 1 を見ています)。
4. CI の ci-0 にはカードの検査(`tools/repo_guide/build.py --check`)があります。ファイルを消したらカードを作り直します。
5. docs の計測のスクリプトは、過去の記録を再現するためのものです。読んでいる本数は trial 4・scan 11・probe 8・w10_ruler 1・overrides 1・`engine/tools` の包み 2 で、頭 7 本は 0 です。消すと記録を再現できなくなるものは、残す側に入れました。

## 8. 読んだもの

[技術マップ](tech-map-2026-11-03.md)・[包みの照らし合わせ](package-map-reconcile-2026-11-05.md)・[案 K](package-map-claude-code-2026-11-05.md) とその[ファイルの表](package-map-claude-code-2026-11-05-files.md)・[段 2 の突き合わせ](stage2-crosscheck-2026-11-05.md)・[カード](repo-guide/cards/README.md)・[1 日の流れ](repo-guide/day-flow.md) §10-2・仕様の[差の一覧](../design/spec/gaps.md)と各章の項目(EO-13・EO-18・MD-06・MD-12・MD-39・WD-05・WD-07・WD-22・WD-34・SO-19・VL-11・PR-17)・[返事その 6](../design/prompt-2026-11-05-reply6.md)・[返事その 7](../design/prompt-2026-11-09-reply7.md)・[回答 10-25](../design/v2-answers-2026-10-25.md) §2-5・§6-1・[決定の索引](../design/decision-id-index.md)・対象の各ファイルの docstring と該当する行・`pyproject.toml`・`.github/workflows/ci.yml`。
