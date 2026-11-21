# 包みの割り当ての照らし合わせ(案 K と案 F)2026-11-05

> 照らし合わせ役が作りました。どちらの案の書き手でもありません。リポのファイルは 1 本も変えていません(commit・push もしていません。`git status` は空のまま)。
> 読んだもの: 案 K(`docs/reference/package-map-claude-code-2026-11-05.md`・同 `-files.md`)、案 F(`/mnt/user-data/outputs/package-map-independent-2026-11-05.md`)、設計書 `docs/design/v3-core-design-2026-11-03.md`、`docs/design/prompt-2026-11-05-reply6.md` §1〜§7、`src/shibuya` のコード(必要な所)。`data/`・IMPLEMENTED.md・build-report・門 1 の計画・パターン台帳は開いていません。Web は使っていません。
> コードの版: HEAD `e863c8b`。案 K は `15b6bbd`、案 F は `2b92173` を読んでいますが、`git diff` で `src/` と `pyproject.toml` は 3 つとも同じと確かめました。だから両案は同じコードを読んでいます。
> 数えたスクリプトはスクラッチ `/tmp/claude-0/-home-claude/f5fea789-0c80-5ecd-90ec-d611f8ebd2e7/scratchpad/reconcile/` に置きました(リポには入れていません)。
> 印: 【確認】=コードか数えで確かめた。【未確認】=確かめていない。【見立て】=私の判断。

## 0. 要旨

1. 324 本のうち **265 本は両案が同じ包み**に置いています(build の 79 本を含む。build を除くと 245 本中 186 本)。**違う包みは 59 本**。片方にしか無いファイルは 0 本です。
2. 59 本の仕分け: **(i) 事実の読み違い 2 本**・**(ii) 当てはめの違い 41 本**・**(iii) 原則が決まっていないので決められない 16 本**。(ii) の推しは K 29 本・F 6 本・どちらでもよい 6 本です。
3. (i) の 2 本: `engine/calendar_shadow.py` は案 K の読み違い(「計器だけ」ではなく、1b の腕が読む W20 の約束の表の読み口を含む)。`perception/attention.py` は案 F の読み違い(世界の過程が使うのは「誰が気づくか」ではなく、文の札付け・命令文の除去・セルの目立ちの並べ替え)。
4. 案 F には、1 バイト不変を壊す穴の指摘がありません。`state_hashes._qual` がクラスの「モジュール名.クラス名」を final のハッシュに流すので、path の文字列を全部直してもファイルを動かせば final が変わります(コードで確認)。案 F §6-6 の「158 個と試験を同じ commit で直せばよい」という書き方は、これだけでは足りません。
5. ユーザーに聞く問いは 7 つです(§4)。必須の 3 つ(心の読み・世界の書き・関係と約束)に、束ねの置き場・実行中の行為・System 1 の「届いたか」・制度の事実の置き場を足しました。
6. 案 K の数の主張は、今の木の数はほぼ全部合いました。割った後の数(796 本・35 本・循環 2 組)は、関数単位の割り先が全部は載っていないので再現できません。部品は確かめました。「心が外の列を読むのは 54 か所」は**下限**で、リポ自身の走査の道具で数えると約 77 か所・12 本でした。
7. 合わせた案(§7)は、59 本のうち 50 本で K、7 本で F、2 本は両案と違い「消す」です。ただし K に寄った本数のうち 16 本は (iii) の問いの答えで動きます。

---

## 1. ファイル単位の突き合わせ

### 1-1 数

| | 本数 |
|---|---:|
| src の追跡ファイル(`.py` 323・JSON 1) | 324 |
| 両案が同じ包みに置いた(主な置き場で比べた) | **265**(うち build 79) |
| 違う包みに置いた | **59** |
| 片方にしか無いファイル | **0**(両案とも 324 本を全部載せている【確認】) |

比べ方: 割るファイルは「主な置き場」(案 K は最初に書いた=いちばん大きい割り先、案 F は表の「新しい置き場」)で比べました。主な置き場が同じでも割り方が違う中心の部品は §1-3 に別に書きます。

違う 59 本の向き(K → F): foundation→mind 8・society→mind 6・runtime→foundation 6・world→economy 6・society→world 4・world→foundation 3・foundation→runtime 3・foundation→society 3・mind→runtime 3・act→mind 2・world→mind 2・ほか 1 本ずつ 13。

包みごとの本数(主な置き場):

| 包み | 案 K | 案 F |
|---|---:|---:|
| foundation | 37 | 31 |
| runtime | 41 | 44 |
| world | 60 | 52 |
| mind | 32 | 45 |
| act | 7 | 4 |
| economy | 18 | 25 |
| society | 30 | 23 |
| experiments | 10 | 11 |
| validation | 6 | 8 |
| interfaces | 1 | 1 |
| build | 79 | 79 |
| 根(`__init__.py`) | 1 | 1 |
| 消す | 2 | 0 |

### 1-2 違う包みに置いたファイル(59 本・全部)

区分の列: (i)=事実の読み違い・(ii)=当てはめの違い・(iii)=原則の迷い(§4 の問いの番号)。推しの列は §2 で理由を書きます。

| # | ファイル | 案 K | 案 F | K の理由(要約) | F の理由(要約) | 区分 | 推し |
|---:|---|---|---|---|---|---|---|
| 1 | `agents/__init__.py` | mind の頭(空) | foundation の頭(空) | 再輸出を消す | 再輸出を消す・呼び手 0 | (ii) 頭 | 消す |
| 2 | `agents/state.py` | world.model(表 447 行)+foundation(語彙) | foundation(器)+型を foundation | 語彙は全層、表は組み立てが渡す | 器と書きの守り=状態の台帳 | (iii) 問い 1 | 既定 K |
| 3 | `census/__init__.py` | 消す | validation の頭 | 呼び手が無い | 中身なし | (ii) 頭 | 消す |
| 4 | `engine/activity.py` | act | mind | 持続する活動の実行 | 本人の時間の使い方 | (iii) 問い 5 | 既定 K |
| 5 | `engine/batching.py` | foundation | runtime | 連絡の配達と runtime が読む | 窓の待ち行列=事象の列 | (ii) | K |
| 6 | `engine/bridging/__init__.py` | foundation の頭 | validation の頭 | 頭 | 頭 | (ii) 頭 | どちらでも |
| 7 | `engine/calendar.py` | world.facts(+刻みの換算を foundation) | foundation(+季節の表を world) | 暦 | 時刻の層 | (ii)(問い 7 と連動) | K |
| 8 | `engine/calendar2/__init__.py` | society.arms | mind | 頭 | 頭 | (iii) 問い 4 | 問い 4 次第 |
| 9 | `engine/calendar2/arm.py` | foundation.arms | mind | 何も読まない切替口・心と腕が読む | 切替口 | (ii)(問い 4 と連動) | K |
| 10 | `engine/calendar2/layer.py` | society.arms | mind | 心・器・体の実行の束ね(v3 で割る) | 会話とメッセージから予定を作る系 | (iii) 問い 4 | 問い 4 次第 |
| 11 | `engine/calendar3/arm.py` | foundation.arms | society | 切替口 | 切替口 | (ii)(問い 4) | K |
| 12 | `engine/calendar3/knowledge.py` | society.arms | world.facts | 常識と店の決まりの口 | 世界の事実(誰でも引ける) | (ii) | どちらでも(推しは K) |
| 13 | `engine/calendar_self.py` | society.arms | mind | 束ね | 勤務の出入りを本人の判断へ | (iii) 問い 4 | 問い 4 次第 |
| 14 | `engine/calendar_shadow.py` | society.vessels | world.facts(+計器を validation) | 「計器だけ」 | W20 の約束の表 | **(i)** | F |
| 15 | `engine/contact/arm.py` | foundation.arms | society | 切替口 | 切替口 | (ii)(問い 4) | K |
| 16 | `engine/contact/device.py` | society.arms | world.things | 道具の状態と通知の刺激 | 持ち物=世界の状態(CT0) | (ii) | F |
| 17 | `engine/decision/__init__.py` | mind | runtime | 頭 | 頭 | (ii) | K |
| 18 | `engine/decision/layer.py` | mind | runtime | 候補の口の層 | 判断の口を束ねる | (ii) | K |
| 19 | `engine/decision/ports.py` | mind | runtime | 3 つの実装 | 3 つの実装 | (ii) | K |
| 20 | `engine/defect_fixes_1103.py` | world.laws | runtime | 欠陥 4 件の切替口 | 組み立てが読む切替口 | (ii) | F |
| 21 | `engine/duties/__init__.py` | society.arms | mind | 頭 | 頭 | (iii) 問い 4 | 問い 4 次第 |
| 22 | `engine/duties/arm.py` | foundation.arms | mind | 切替口 | 切替口 | (ii)(問い 4) | K |
| 23 | `engine/duties/knowledge.py` | society.arms | world.facts | 店の決まりの口 | 世界の事実 | (ii) | どちらでも(推しは K) |
| 24 | `engine/duties/layer.py` | society.arms | mind | 束ね | 働く人の体へ店の仕事 | (iii) 問い 4 | 問い 4 次第 |
| 25 | `engine/events/__init__.py` | 消す | foundation の頭 | 頭 | 頭 | (ii) 頭 | F(events の小包みを残すなら) |
| 26 | `engine/events/body.py` | society.vessels(+語の変換を foundation) | mind | 体の出来事を記録に書く口 | 記憶の書き手が使う口 | (ii) | F(語の変換は K のとおり foundation) |
| 27 | `engine/events/links.py` | world.model | foundation | 記録の行に目印を付ける口 | 同じ | (ii) | F(差は小さい) |
| 28 | `engine/experiment/gate.py` | foundation.ports | experiments | 出来事の型が検査で読むので下へ | 唯一の口・依存を逆転 | (ii) | 移す段は K・意味は F |
| 29 | `engine/growth_decl.py` | runtime | foundation | 状態成長の宣言 | 同じ | (ii) | K |
| 30 | `engine/intent.py` | act | mind | 実行中の状態の保持 | 意図の保持=考えかけ | (iii) 問い 5 | 既定 K |
| 31 | `engine/ledger_api.py` | foundation.ports | economy | 依存逆転の口 | 同じ | (ii) | K |
| 32 | `engine/manifest_sections.py` | runtime | foundation | 欄の分け方 | 欄の区分 | (ii) | F(差は小さい) |
| 33 | `engine/norm_meter.py` | society.vessels | validation | 計器(読むだけ) | 同じ | (ii) | K |
| 34 | `engine/owner_guard.py` | runtime | foundation | 外の状態の持ち主の守り | 同じ | (ii) | K |
| 35 | `engine/relations.py` | mind+world.facts+foundation | society(強さと相手選びは mind へ) | 客観の初期の辺と主観の辺が 1 つ | 関係の器 | (iii) 問い 3 | 既定 K |
| 36 | `engine/rights/__init__.py` | world.facts | economy | 頭 | 頭 | (iii) 問い 7 | 既定 K |
| 37 | `engine/rights/initial.py` | world.facts | economy | 権利台帳の最初の中身 | 同じ | (iii) 問い 7 | 既定 K |
| 38 | `engine/rights/ledger.py` | world.facts | economy | 誰が権利を持つかの客観の事実 | 権利台帳 | (iii) 問い 7 | 既定 K |
| 39 | `engine/rights/record.py` | world.facts | economy(役割語の確かめは act へ) | 許可のない行動の記録 | 同じ | (iii) 問い 7 | 既定 K |
| 40 | `engine/rules/__init__.py` | world.facts | economy | 頭 | 頭 | (iii) 問い 7 | 既定 K |
| 41 | `engine/rules/table.py` | world.facts | economy | 法と制度の値=事実 | 主な読み手は経済 | (iii) 問い 7 | 既定 K |
| 42 | `engine/scheduler.py` | foundation | runtime | 汎用の予約の列 | 起床と繰り延べの列 | (ii) | K |
| 43 | `engine/state_hashes.py` | runtime | foundation | 2 つのハッシュ | 同じ | (ii) | K |
| 44 | `engine/state_ledger.py` | runtime | foundation | 状態台帳 | 同じ | (ii) | K |
| 45 | `engine/state_ledger_ast.py` | runtime | foundation | 読み手の AST の検査 | 同じ | (ii) | K |
| 46 | `engine/systems/overrides.py` | validation | runtime | 試験だけ | 試験だけ | (ii) | K |
| 47 | `engine/tools/contacts.py` | foundation | society | 手段の印の語彙 | 手段の印 | (ii) | K(差は小さい) |
| 48 | `llm/__init__.py` | foundation.ports(型)・頭は消す | runtime の頭+型を foundation | 型は口へ | 同じ | (ii) 実質同じ | 型は foundation・頭は消す |
| 49 | `llm/parser.py` | act.intake | runtime.inference | 本人の言葉を行為の型へ | 2 行形のパーサ | (ii) | K |
| 50 | `perception/attention.py` | foundation.text(目立ち・命令文の除去)+mind(p_see の門) | mind | 2 つの物が 1 つ。割る | 注意ゲート=何に気づくか | **(i)** | K |
| 51 | `perception/channels.py` | foundation.text | mind | 状態を持たない道具・build も読む | プロンプトの組み立て | (ii) | K |
| 52 | `perception/contact_view.py` | foundation.ports | mind | 連絡の知覚の事実の型 | 事実と描き方 | (ii) | K |
| 53 | `perception/hashes.py` | foundation.text | mind(+B4 の行を world) | 状態を持たない道具 | ハッシュ三役 | (ii) | K |
| 54 | `perception/normalize.py` | foundation.text | mind | 道具・build と act も読む | 正規化の規約 | (ii) | K |
| 55 | `perception/p_notice.py` | world.model | mind | 届いたか=物理の側 | 確率的到達=気づき | (iii) 問い 6 | 既定 K |
| 56 | `perception/state.py` | world.model | mind | 向きなどの列・読み手は顕著な出来事の過程 | 知覚側の個体の列 | (ii) | K |
| 57 | `perception/templates.py` | foundation.text | mind | 何も読まない定数 | 凍結テンプレ | (ii) | K |
| 58 | `world/processes/constitution.py` | world.ledger | validation(定数は world) | 台帳の組み立てが読む | 憲法 5 の機械検査 | (ii) | 移す段は K・後で F の割り |
| 59 | `world/processes/deletion_candidates.py` | validation | world | 試験だけ | 器だけ | (ii) | K |

### 1-3 同じ包みでも割り方が違う中心の部品

| ファイル | 共通 | 案 K | 案 F | 見立て |
|---|---|---|---|---|
| `perception/renderer.py` | 主は mind。世界の側を割り出す | `perceive`(状態 → `Percept`)は **world** の `percept_scene`、`_signage_seen` だけ mind(例外 T6) | `perceive` は **mind/notice**、`_scene`・`_time_view`・近くの人の事実は world/perceptible | K が原則に忠実。`perceive` は SoA の列(セル・種別・所持金・手・行為・内受容)を直に読む(`renderer.py:1477-1495`)ので、mind に置くとそれ自体が「心が世界を直に読む」になる。F の注意書き(副作用の順=注視の抽選 → 露出 → 閉店の句 → B3 → 近接の同点 → 想起。`perceive` の docstring にある)は割るときに必ず守る要点で、K には無い |
| `engine/resolve.py` | 主は act。心の欄の書き手は mind へ・再開の復元は runtime へ | 意図と活動の書き・焦点の書きは act に残す | 意図・活動・焦点・不応期の書きを mind へ。`write_relations` は society へ | 問い 5 と問い 3 の答えで決まる |
| `engine/commit.py` | 主は act | `parse_action`・`intents_from_responses` は act.intake。δ_perc は act | `parse_action` は runtime のパーサへ。δ_perc は mind/notice | K(パーサの置き場と揃える。#49) |
| `engine/arbiter.py` | 主は runtime(9-4 で消える部品) | `WakeCandidates` を mind | `WakeCandidates` を foundation の口・域外と就寝と不応期の抑止を mind | 消える部品なので差は小さい |
| `engine/conversation.py` | society | 割らずに society.vessels | 記録・門・番の時刻・相槌の 4 つに割る | 移す段は K。F の割り方は v3(題 5)の材料 |
| `engine/presence.py` | world | world.laws(2 本に割る) | world/population | 同じ考え。両案とも `PlanBlocks`(予定)を mind とする読み方を v3 の迷いに挙げている |
| `engine/run.py`・`cli.py` | runtime・interfaces | 3 つと 2 つに割る | もっと細かく割る(計器を validation・招待の決着を society・乱数の領域を foundation ほか) | 移す段は K で足りる |
| `llm/contract.py` | foundation | 割らない | 2 行形の書式と対象の読みを割り出す | 移す段は K |
| `engine/processes/salient.py` | world | 割らない | `p_notice` の結線を mind へ | 問い 6 |
| `engine/events/log.py` | foundation | 割らない(gate も foundation へ) | 原因の型を分け、gate の検査を逆転 | #28 と同じ |

### 1-4 片方にしか無いもの

ファイルは 0 本です。片方にしか無いのは次です。

- **割るファイル**: 両案とも割る 15 本。K だけ割る 8 本(`chooser`・`events/body`・`tools/record`・`tools/registry`・`llm/fleet`・`llm/mock`・`perception/attention`・`world/assets`)。F だけ割る 22 本(束ね 5 本・`activity`・`intent`・`calendar_shadow`・`conversation`・`events/log`・`salient`・`rights/record`・系 6 本・`llm/contract`・`perception/facts`・`perception/hashes`・`constitution`)。
- **新しい置き場**: K だけ=`foundation/write_guard`・`foundation/arms`・`foundation/paths`(`repo_root()`)・`runtime/state/class_ids`(固定の表)・`society.arms`。F だけ=`world/perceptible`・`world/things`・`foundation/ports/wake`・`foundation/rng_domains`・`act/check`・`act/unmet`・`validation/holdout`・`validation/leak`・`interfaces/export`。
- **解析**: K だけ=`_qual` の穴・乱数の領域の名・版の ID・模擬の木に本物の lint-imports をかけた結果・列の持ち主の読み書きの表。F だけ=1 辺 1 行の直し方の表(A1〜A52・B1〜B10・C1〜C10)・`perceive` の副作用の順・F §2 の行番号つきの割り先。

---

## 2. 違いの仕分け

### 2-1 (i) 事実の読み違い

**(i-1) `engine/calendar_shadow.py` — 案 K の読み違い。F が正しい。**
- K は「暦 1a の影=計器だけ」と書いて society.vessels に置きました。
- コードでは、このモジュールは計器 `CalendarShadow` のほかに、W20 の勤務と授業の週の表の読み口(`CalendarTable`・`load_table`・`resolve_path`・`WEEK0_MONDAY`・`COMMIT_WORK`・`COMMIT_SCHOOL`)を持ちます。これを、結果を変える腕のコードが読んでいます。`calendar_self.py:86` が import し、`:658`・`:677`・`:691` で表を使って出勤・通学を決めます。`calendar3/roster.py:188` も読みます【確認】。
- 推し: 割ります。表の読み口は world.facts(K 自身が W17 の読み口 `agents/weekly.py` を world.facts に置いたのと同じ扱い)。影の計器は society.vessels(K)か validation(F)。

**(i-2) `perception/attention.py` — 案 F の読み違い。K が正しい。**
- F はファイル全体を mind/notice に置きました。世界の過程からの辺 A15(`civic.py:41`)と A16(`salient.py:63`)は「出来事だけを出し、誰が気づくかは mind/notice が決める」で直す、と書いています。
- コードでは、`civic.py` が使うのは `feature_tag` と `strip_imperatives` だけです(`civic.py:250-251`。放送の文に札を付け、命令文を除く)。`salient.py` が使うのは `SalientItem`・`rank_by_saliency`・`apply_budget` で、セル共有の B4 の「目につく出来事」の行を並べる処理です(`salient.py:384-403`)。どちらも「誰が気づくか」ではありません【確認】。「誰が気づくか」を決めるのは A17(`p_notice.notice_event`)だけです。
- 推し: K の割り方(文と目立ちの道具は foundation.text、`p_see`・`gate_stage1` だけ mind)が、実際の使われ方に合っています。

**小さな読み違い・数え漏れ(区分は変えない)**
- 案 F の `engine/intent.py` の理由「意図の保持=考えかけ」: 設計書 9-5 の「考えかけ」は、問い・途中までの考え・前提・始めた時刻を持つ「開いている考え」です。`engine/intent.py` の docstring は「着いたら LLM を呼ばずエンジンが意図の行為を実行する … 判断 1 回・実行は世界」です。だから語の当てはめが違います。置き場そのものは問い 5 で扱います。
- 案 F の `engine/calendar.py` の「天気の型」: 型はありません。あるのは規則の名の定数 `WEATHER_SCHEME`(`calendar.py:82`)と `SEASON_OF_MONTH` です。
- 案 K の「`draw` の側に状態を読む列は 0」: SoA の列についてはそのとおりです。ただ `_b2` などは `self.world.assets.cell_band` を読み(`renderer.py:1759`・`2121`・`2735`)、`self.assets.poi_name` も読みます。静的な世界の資産を World の物を通して読んでいます。例外 T1 は `PerceptionAssets` だけを挙げているので、`self.world` の読みは数に入っていません。
- 案 K の `agents/state.py` の語彙の行数は、本文 §2-1 で 324 行、ファイルの表で 234 行です。中で食い違っています(私の AST の数えでは 204 行。数え方の違いは確かめていません)。
- **案 F の 1 バイト不変の見立ての穴(重い)**: F §6-6 は「path の文字列 158 個と試験を同じ commit で直す」で足りるように読めます。しかし `engine/state_hashes.py:89-91` の `_qual` は `type.__module__ + "." + __qualname__` を、Enum(`:155`)・dataclass(`:181`)・名前つきの組(`:187`)・値のクラス(`:218-220`)のバイトに流します。final の定義は behavior-hash です(`:42` `FINAL_DEFINITION = "behavior"`)。behavior-hash は外の状態の digest を含みます(`:262-264`)。だからクラスの置き場を変えると final が変わる道があります【確認】。`state_codec.py` の `ALLOWED_CLASSES` 17 行・`CLASS_FIELDS` 2 行も、名前を `importlib` で組み立て直します。K §6-1 の「固定の表を先に入れる」段が必要です。K の実測(`ca1c761a…`→`9d7fd317…`)は私は回していません【未確認】。

### 2-2 (ii) 原則の当てはめの違い(どちらが忠実か)

案 K を推すもの(29 本)

- **`engine/batching.py`・`engine/scheduler.py` → foundation(K)**: 読むのは core と manifest の型だけです。`world/body/schedule.py`(体)と `contact/deliver.py`・`contact/layer.py`(連絡)も読みます【確認】。runtime に置くと、F 自身が挙げる上向きの辺 A23・A41・A42 が残ります。「上から下へだけ読む」に忠実なのは K です。
- **`engine/calendar.py` → world.facts(K)**: 中身は日付・曜日のほかに祝日・学校の休み・給料日・営業日・祝日の差し替え(`calendar.py:320-405` の `is_holiday`・`set_holiday`・`is_payday`・`is_business_day`・`in_school_holiday`)です。CLAUDE.md §3 の「社会の決まり(暦)」に当たる制度の事実です。foundation に置くと、意味の無い土台に制度が入ります。economy は道の補助 `resolve_repo_path` を読むだけです(`economy/wages.py:159`)。
- **切替口 4 本(`calendar2/arm`・`calendar3/arm`・`contact/arm`・`duties/arm`)→ foundation.arms(K)**: どれも何も import しません【確認】。読み手は CLI・組み立て・束ねのほかに、心の側(`calendar2/book.py` が `LEDGER_ARM` を読む)と道具(`contact/device.py:55`)です。束ねと同じ所に置くと上向きの辺になります。問い 4 の答えが F の (C) なら mind か society になります。
- **`engine/decision/{__init__,layer,ports}.py` → mind(K)**: 9-3a で判断モデルは心の過程(速い過程の上段)です。`layer.py` の docstring も「1 呼の判断を口に通す・候補の源の計器」です。F は runtime/inference に置きましたが、F 自身の契約 6(runtime の核は中身を読まない)に `decision/layer.py` の 4 辺が反します(F §3 の表)。K では例外 T4・T7 の 2 本で済みます。
- **`engine/experiment/gate.py` → 移す段は foundation.ports(K)**: `events/log.py:169` が関数の中で gate を読み、`ADMIT_CODE` と比べて CP12 を守っています【確認】。K の置き方ならコードは変えずに移せます。F の逆転(gate が自分を登録)は意味としては正しいですが、守りの仕組みを書き換えます。整理の段ではなく v3 で行う案がよいと考えます【見立て】。
- **`engine/state_ledger.py`・`state_hashes.py`・`state_ledger_ast.py`・`growth_decl.py`・`owner_guard.py` → runtime(K)**: どれも core のほかは互いしか読まず、読み手は runtime だけです(`resolve.py` の `restore_soa` は両案とも runtime へ出す)【確認】。保存とハッシュと復元は runtime の仕事です。`state_codec`(両案とも runtime)と `state_hashes` は同じクラス名の表を持つので、一緒に置くのが筋です。
- **`engine/ledger_api.py` → foundation.ports(K)**: ファイル自身が「台帳の依存逆転の口(Protocol)。経済の中身を読まない」です。読み手は経済のほかに resolve(act)・rail(法則)・run・cli です【確認】。口の型は口の層に置くのが原則に合います。
- **`engine/norm_meter.py` → society.vessels(K)**: 群と規範の計器で、ランの中で組み立てが作ります(`systems/build.py` だけが読む)。原則の文「society は器と計器だけ」にそのまま当たります。
- **`engine/systems/overrides.py` → validation(K)**: src の呼び手は 0 で、tests だけが読みます【確認】。
- **`world/processes/deletion_candidates.py` → validation(K)**: src の呼び手は再輸出の頭だけで、使うのは tests と CI です【確認】。
- **`world/processes/constitution.py` → 移す段は world.ledger(K)**: `first_batch`・`registry`・`circularity` が定数と型を読みます。F の割り(検査は validation・定数は world)はきれいですが、割る作業が要ります。移す段は K、割りは後で F の形にします。
- **`engine/tools/contacts.py` → foundation.vocab(K)**: 何も読まず、mind 側(`relations`・`relations_people`)と society 側(`contact/book`・`layer`)の両方が読みます。中立の置き場が合います(差は小さい)。
- **`llm/parser.py` → act.intake(K)**: 9-2 の行為の鎖(依頼 → 本人の言葉 → 穴の値 → 差分)の入口です。`commit.py`(act)が読み、パーサも `llm/undefined.py`(両案とも act)を読みます。F の置き方では act → runtime の上向きの辺(F の A26)が生まれ、`parse_action` を移す作業が要ります。
- **`perception/channels.py`・`normalize.py`・`hashes.py`・`templates.py`・`contact_view.py` → foundation(K)**: 読み手に world(`contact/device.py` → templates)・act(`activity.py` → normalize)・build(`build/lang/common.py` → channels・normalize・attention)・runtime がいます【確認】。mind に置くと world → mind(F の A13)と build → mind の辺が生まれます。`contact_view` は、F 自身も A34・A35・A37 の直し方で「型を foundation/ports へ」と書いています。代わりに foundation に意味のある物が入ります(K の異論 4)。
- **`perception/state.py` → world(K)**: 中身は向き(heading)と課題の旗で、読み手は世界の過程 salient だけです【確認】。体の向きは 9-1 の「体・位置」の側=心の外です。
- **`perception/attention.py`** は (i-2) のとおり K。

案 F を推すもの(6 本)

- **`engine/contact/device.py` → world.things(F)**: docstring が CT0「持ち物はエンジンが持つ世界の状態」を引き、電池・電源・マナーモード・かばんの中を持つ、と書いています【確認】。9-1 の「持ち物」は心の外です。K は連絡の束ねと一緒に置きましたが、ファイル自身の定義に合うのは F です。
- **`engine/defect_fixes_1103.py` → runtime(F)**: 直した 4 件は会話の終わり(M10)・列の印(M11)・列での支払い(M28)・返事待ち(M16)で、act と society の振る舞いです。世界の法則ではありません。読み手は組み立て・結果・状態の書き出しと CLI だけです【確認】。K の world.laws には根拠がありません。
- **`engine/events/body.py` → mind(F)、語の変換は K のとおり foundation**: `BodyEventLink` は記憶の器 `memory_store` の属性 `body_events` として持たれます(`state_ledger.py:1731`・`systems/talk.py:84`)【確認】。K の society.vessels.tools には根拠が見当たりません(読む `SIGNBOARD_*` の定数だけ)。
- **`engine/events/links.py` → foundation(F)**: 読むのは foundation(出来事の記録と語彙)だけで、呼び手は世界の過程の実行器と組み立てです【確認】。差は小さいです。
- **`engine/manifest_sections.py` → foundation(F)**: manifest の型(両案とも foundation)と同じ種類の表です。experiments(branch)も読みます。差は小さいです。
- **`engine/events/__init__.py` → foundation の頭(F)**: 出来事の記録の小包みを残すなら頭が要ります。

どちらでもよいもの(6 本)

- `agents/__init__.py`・`census/__init__.py`: どちらも呼び手 0 です【確認】。消してよいです。
- `engine/bridging/__init__.py`: 中身(`ledger` は両案とも foundation・`scan` は両案とも validation)が割れるので、頭はどちらでも構いません。
- `engine/calendar3/knowledge.py`・`engine/duties/knowledge.py`: 何も読まず(duties は権利台帳を関数の中で読む)、呼び手は束ねの 2 本だけです。v3 で束ねを割るときに、「知覚の口」か「組織の口=器」か「本人の知識」かを決め直す物です。今は束ねと一緒(K)を推します。
- `llm/__init__.py`: 両案とも型は foundation.ports へ・再輸出は消す、で中身は同じです。

### 2-3 (iii) 原則の迷い

16 本(`agents/state.py`・`activity`・`intent`・束ねの 5 本(`calendar2/__init__`・`calendar2/layer`・`calendar_self`・`duties/__init__`・`duties/layer`)・`relations`・権利 4 本・規則 2 本・`p_notice`)です。§4 の問いで扱います。

---

## 3. 両案が揃って出している原則の直し(ユーザーの承認が要る)

違いではありませんが、両案とも原則の文を直す提案をしています。

1. **runtime の「中身に触らない」を 2 つに割る**: K 異論 5 と F 異論 3 が同じ案です。「核(時計・進行役・事象の列・テープ・保存)は中身を読まない。組み立て・系・結果は読む」。
2. **「世界を書けるのは act だけ」の文の範囲**: K 異論 2 と F 異論 2 が同じ指摘です。法則の書き・心の欄の書き・金の書きが文から漏れています。問い 2 で扱います。
3. **「mind は world を読まない」は import の検査だけでは守れない**: K §5-1 と F 異論 1 が同じ指摘です。問い 1 で扱います。
4. **封印(holdout)を読む部品は import では守れない・src に守る先が無い**: K 異論 6 と F 異論 5 が同じ指摘です。K の「封印の語の AST の検査」を推します。

---

## 4. ユーザーに聞く問い(1 つずつ)

### 問い 1 「心は世界の列を直接読まない」を、35 万体を 1 つの表で渡している今、どう守るか

**今の事実【確認】**
- 個体の表 `AgentState` は 82 列です。実行時に `AgentState` を使う(作る)のは `engine/systems/build.py` だけで、ほかの 14 本は型の注釈にしか使っていません。
- 心のファイルは表を受け取り、外の列を直に読んでいます。K は 54 か所・11 本と数えました。リポ自身の走査の道具(`engine/state_ledger_ast.scan` の strict)を K の持ち主の分け方(world 35・act 12・economy 2・mind 33)で回すと、**約 77 か所・12 本**でした(私の数え。同じ名の別物を数えている所がありえます)。K が落としているのは `f("cell")` の形の読み(`memory.py:470-484` ほか)と、名前の表を回す読み(`change_detect.py` の空腹・疲れ・暑さ 12 か所)です。K 自身も §10 で「実際はもっと多い【推測】」と書いています。
- 読みの例: `classical.py` が本人のセル・活動・居る店・空腹・乗車の状態・性・年齢を読む。`store_choice.py` が店の値段 `pois.price` を読む(全員が全部の店の値段を知っている形)。`relations.py` が知人の位置 `cell`・`xy` を読む(見ていない知人の居場所を知っている形)。

**選択肢**
- **A 段で守る(案 K)**: ① import の契約(mind は foundation の口の型だけ読む)② 状態台帳に列の持ち主の欄を足し、「心が読んでよい列」の一覧を試験で固定し、減らす向きにだけ動かす ③ 組み立てで表を丸ごと渡さず、列の部分集合だけを持つ読み取り専用の口を渡す ④ 見えないはずの他人の行や口の外の列を揺らし、判断と final が動かないことを試す。表を持ち主ごとに割るのは v3。
- **B 表を今、持ち主ごとに割る(案 F の迷い 1 の B)**: import で列を縛れます。state_hash・状態のファイル・checkpoint が変わる=版上げです(並びを固定すれば不変にできる見込みと F は書いていますが、推測です)。
- **C 心に渡すのを知覚の値だけにする(F 異論 1 の (c)・K の v3 の到達点)**: 心は `Percept`(1 人 1 起床の事実)と、System 1 用の読み取り専用の配列の束(K の `SenseBatch`)だけを受け取ります。12 本の読みを知覚の欄へ書き直します。店の値段を見ていない人は知らない、という形になり、結果が変わります(1 バイト不変ではない)。
- **D 今の読みを「宣言した例外」として凍結するだけ(A の ② だけ)**

**現実の人の振る舞いとの整合**
- C がいちばん合います。人は自分の体を内受容で大まかに知り、他人の居場所や店の値段は見たか覚えているときだけ知っています。
- A は ③④ まで入れれば C に近づきます。ただし ②③ が分かるのは列の名までで、「他人の行を読んだか」は ④ でしか分かりません(K の指摘のとおり、配列は全員分なので型では止められない)。
- B は列を縛るだけで、他人の行の読みは止まりません。現実との整合は A の ② と同じ程度です。
- D は今の全知の形のままです。

**影響するファイル**: 心の 12 本(K の数えでは 11 本)+`agents/state.py`+組み立て(`systems/build.py`)+知覚の口の型。C ではさらに `renderer` の割り方も絡みます。

**推し: A を今(① と ② は移すと同時に。結果は変わらない)、③ は題 9-2(心の口)を決めるときに入れ、到達点は C と明記する。**
- 理由 1: 1 バイト不変の整理の段で入れられるのは ①② だけです。
- 理由 2: B は版上げの費用の割に、他人の行の読みを止められません。
- 理由 3: C は振る舞いを変えるので、9-2 の設計(何を知覚として渡すか)が先です。
- 補足: 決める前に「今いくつ読んでいるか」を、リポの走査の道具で数え直して固定するのがよいです(54 は下限)。

### 問い 2 世界を書ける範囲(act だけか、法則のコードからも書けるか)

**今の事実【確認】**
- 書きの解除口 `writable()` を呼ぶのは `engine/resolve.py` だけです(AST で 50 回。行で数えると 47 行=F の数)。SoA の書きは AST で見える分が 395 か所で、355 か所が resolve、40 か所は表の組み立ての初期値です(K の数と一致)。
- 世界の過程 9 本(`presence`・`civic`・`crowd`・`environment`・`goods_flow`・`opening`・`rail`・`runner`・`salient`)が resolve の関数を直に呼んで書いています。束ね 3 本(`calendar2/layer` の `begin_walk_to`・`calendar_self` の `rail_arrive` ほか・`duties/layer` の `request_open_close`)も呼んでいます。
- 金は台帳の口を通ります(例 `rail.py:747` の `transfer_many`)。法則は自分の内側の状態(列車・待ち行列など)を表の外に持ちます。
- 背景の決定は「世界の差分を書くのは act を通してだけ。例外は物理・保存則・制度の手順・物理的に止める仕組み(E 区分)だけで、これはコードの法則」です。ところが今の過程のうち補充(`goods_flow`)と開閉店(`opening`)は E 区分ではありません。人の行為の代わりの**つなぎ**です(CLAUDE.md §3「まだ人の行動で作れない変化はエンジン規則でつなぐ」)。

**選択肢**
- **A 書く関数は act だけが持ち、法則もつなぎも act の関数を呼ぶ(案 K)**: 書きの門は 1 つ。原因の印(`Process` か宣言つきのつなぎ)で区別します。包みの単位の world ⇄ act の循環は、副包みの層(world.laws > act > world.model)で解きます。
- **B E 区分の法則は自分で書く(門を 2 つ)。人の行為とつなぎだけ act(F の迷い 3 の B 寄り)**: 循環なし。書きの検査(`systems/allow.py` の閉包・AST の検査)が 2 重になります。
- **C 法則は差分を返し、act が当てる(案 F の本案・R-134 の差分の器)**: いちばんきれいです。書く時刻が「過程の中」から「act の適用」へ動くので、同じ刻みの中の順と byte-check の値が動きうります。19 口の書き直しで、v3 の範囲です。

**現実の世界の仕組みとの整合**
- 天気や物理は誰の行為でもなく世界を変えます。B はこの「ひとりでに起きる」形にいちばん近いです。
- 一方、補充や開閉店は現実では店員の行為です。つなぎを act に通す(A・C)のは、「いずれ人の行為に置き換える物」として正しい扱いです。
- A と C の「全部の変化を 1 つの門で原因つきで記録する」は帳簿の付け方の選択で、現実と矛盾しません(複式簿記のように、どの変化にも原因がある)。

**影響するファイル**: 法則 9 本+resolve+束ね 3 本(金と物の書き手 `economy/ops.py`・`goods.py` は変えない)。

**推し: A を今(今の形のまま移せる)。原則の文を次のように直し、到達点は C。**
- 直す文の案: 「世界の列を書く関数は act だけが持つ。呼んでよいのは act・E 区分の法則・宣言つきのつなぎで、呼ぶときは原因の印を付ける。金と物は economy の基本操作だけが書く」。
- 理由 1: 今でも書きの門は 1 つで、形を保つのが動かす量がいちばん少なくて済みます。
- 理由 2: 原因の印で E 区分とつなぎを区別すれば、B が狙う「法則は例外」は門を 2 つにせずに書けます。
- 理由 3: 給料日のような economy の過程の書きは act を通りません(K 異論 2)。これも文に書いておきます。

### 問い 3 関係と約束を、客観の事実(world)・器(society)・本人の理解(mind)のどこに置くか

**今の事実【確認】**
- `engine/relations.py` の関係の表は、体ごとに 15 辺を持ちます。書き手は本人の記憶の層です(`MemoryLayer.record` が相互作用のエピソードを書いた直後に `on_episodes`)。強さ A は記憶と同じ減り方の式です。「表に居る相手だけ」辺を作り(知らない同席者は作らない)、新しい相手は「知人」です。初期の辺だけは、W16・W17 の客観のデータ(同じ世帯・職場・学校で同じ時間に居た長さ)から作ります(`initial_edges`)。つまり今の表は**人ごとの主観に近い**物です(F §6-4 も「主観に近い」と書いています)。
- 約束の帳面 `calendar2/book.py` は CA3「各自が自分の理解の行・変えられるのは自分の行だけ」です。
- W20 の勤務と授業の表(`calendar_shadow.py` の読み口)は、構築した客観のデータです。
- 権利台帳(雇用・所有・賃借・許可)は客観の事実です。会話のセッション・メッセージの配達・グループの一覧は運ぶ器です。

**選択肢**
- **A 3 か所に分ける(案 K)**: 客観の事実=world.facts(初期の結びつき・権利・W20 の表)。運ぶ器=society(会話・配達・グループ。連絡帳は今だけ)。本人の理解=mind(関係の記憶・約束の帳面・頭の中の予定)。器は約束を持ちません。world から mind への写しは始めの 1 回だけにします。
- **B 関係の表を society の「関係の器」に置き、強さと相手選びだけ mind(案 F の今の割り当て)**
- **C 約束を共有の 1 行(客観の記録)として world か society に置き、各自の記憶はそれを指す**

**現実の人の振る舞いとの整合**
- 関係: 家族や雇用は本人の気持ちと関係なく存在する事実です。親しさや信頼や印象は各自の頭の中にあり、非対称で忘れます。A がこの両方に合います。
- 約束: 「A が B に 18 時と言った」という発話は出来事(見た人がいれば確かめられる)です。各自の覚え方は食い違ってよく(時刻を覚え違えるのは普通)、手帳やアプリに書けばそれは持ち物です。A は 3 つとも表せます。
- B は人ごとの表を「器」と呼ぶ形で、運ぶ物ではないので名と中身が合いません。
- C は CA3(すでに決めた「共有の 1 行にしない」)と食い違い、覚え違いを表せません。

**影響するファイル**: 約 14 本(`relations`・`relations_people`・`calendar2/book`・`calendar2/recall`・`calendar_shadow`・`calendar3/roster`・`contact/book`・`tools/groups`・`tools/contacts`・`conversation`・権利 4 本)。

**推し: A。**
- 理由: コードの関係の表は本人の記憶から書かれる主観の表で、約束は CA3 で決まっています。
- 足すこと: 手帳やアプリに書いた予定と連絡帳は、本人が忘れても端末に残る「持ち物」です。v3 では world.things(F が `contact/device` に使った置き場)に寄せるのがよいと考えます【見立て】。

### 問い 4 束ね(カレンダー 2・3・1b・連絡・店の仕事の層)を v3 で割るまでどこに置くか

**今の事実【確認】**
- 束ねは 5 本です(`calendar2/layer` 1,105 行・`calendar3/layer` 864 行・`calendar_self` 1,750 行・`contact/layer` 1,536 行・`duties/layer` 691 行)。どれも、本人の判断(候補の口)・resolve での書き・世界の読み(営業時間 `rows_of_day`・在圏のブロック `PlanBlocks`・補充の定数)・器の働きを 1 つに持ちます。
- 案 K はまとめて society.arms に置き、原則に反する辺 20 本を宣言しました。モジュールの対で 13(→ mind)+5(→ world.laws)+1(→ world.body)+1(→ world.ledger)と、私も同じ数を再現しました。
- 案 F は意味で分けました(calendar2・calendar_self・duties は mind、calendar3・contact は society)。直す辺は F の表で約 30 本あります(A29〜A44・B1〜B3・B6〜B8・C6〜C8)。

**選択肢**
- **A society の下の一時の副包み society.arms(案 K)**: 原則に一時の例外を書きます。
- **B 12 番目の一時の包み(例 `arms`)**: society の原則の文はそのまま守れます。包みの一覧が 1 つ増えます。
- **C 主な意味で今置く(案 F)**: mind と society に入れます。注入や口の型での直しが要り、移すだけでは済みません。直さなければ、いちばん厳しい mind の契約に例外が約 30 本入ります。
- **D 系の本体を runtime/systems へ(F の迷い 13・14 の B)**: 「runtime は中身に触らない」と衝突します。

**現実の人の振る舞いとの整合**
- 現実にこの束ねに当たる 1 つの物はありません。本人が決め(心)、歩き(体と act)、知らせが届き(器)、雇い主のシフトは別の人の仕事です。
- だからどの選択肢も、v3 で割るまでの「一時の置き場の名の付け方」の違いです。正直さで比べると、一時であることが見える B か A がよいです。C は書きと世界の読みを mind の中に隠します。

**影響するファイル**: 22 本(束ねの持ち主 14 本+切替口 4 本+頭 4 本)。うち 13 本で両案が違います。

**推し: B(11 の包みのままにしたいなら A)。**
- 理由: 原則の「society は器と計器だけ」を文どおりに保てます。一時の置き場であることが名に出て、v3 で割る対象が一目で分かります。A と B の違いは名と契約の書き方だけで、移す作業は同じです。

### 問い 5 実行中の行為(意図の保持・活動の持続)は心の物か act の物か

**今の事実【確認】**
- `engine/intent.py`: 対象が別のセルにあるとき、行為を「意図」(`intent_action`・`intent_target`・`intent_kind`・`intent_since`)に残し、目的地つきの移動を始めます。着いたら LLM を呼ばずにエンジンが意図の行為を実行します(docstring「判断 1 回・実行は世界」)。書きは resolve を通ります。
- `engine/activity.py`: 活動=世界を変えない時間の使い方(自由文 10 字+持続の上限)です。エンジンが持つのは「あたり」の位置・持続・観測への表示の 3 つだけで、書きは resolve を通ります。
- 9-1 は心の内側に「目標と予定・考えかけ」を挙げますが、実行中の行為がどちらかは書いていません。9-5 の「考えかけ」は熟考の途中の物です。

**選択肢**
- **A act(案 K)**: 実行の状態として act が持ち、心へは `Percept` の意図の欄・自分の欄で見せます。
- **B mind(案 F)**: 本人の目標・時間の使い方として心が持ちます。
- **C 割る**: 「着いたら X をする」という意図と「何時まで」の予定は mind(覚えている限り効く)。歩かせる・着いたら当てる・満了させる仕組みは act。

**現実の人の振る舞いとの整合**
- 人の「後でこれをする」という意図は頭の中にあり、途中で忘れたり変えたりします(部屋に入って何をしに来たか忘れる、など)。体を動かすのは別の働きです。だから C がいちばん合います。
- A は今のエンジンの動き(意図を必ず実行する)にそのまま合います。人らしくはありませんが、今の振る舞いです。
- B は、実行の仕組み(resolve の呼び出し)を心に入れることになります。

**影響するファイル**: 2 本(`activity`・`intent`)+resolve の一部(意図の書き 115 行・焦点 94 行)+act の 12 列。

**推し: A を今(1 バイト不変で移せ、今の意味に合う)。C を v3 の到達点にし、9-2・9-5 で「開いている意図」を心の口に入れるときに割る。**

### 問い 6 System 1 の「物理として届いたか」は世界の物か心の物か

**今の事実【確認】**
- `perception/p_notice.py` は、目標の捕捉の式 TTPF(距離・照明・視野の偏心・混雑の紛れ)と、周りの人が気づいた数による伝わり(Milgram のデータへの当てはめ)で「気づく確率」を出します。呼ぶのは世界の過程 `salient.py:256` だけで、そこで起きる人を決めています。
- `perception/state.py` は向きと課題の旗を持ちます。
- 9-3c は「System 1 は物理として届いたかだけを決める(音の大きさ・距離・視野・急な変化・接触)。意味の表は持たない」と書き、9-3a は System 1 を心の連続の土台としています。文の上では「届いたか」が心の中にあります。一方で、距離や照明を計算するには世界の位置を読む必要があり、「心は世界を直接読まない」とぶつかります。

**選択肢**
- **A 届いたか=world、気づくか(看板の p_see)=mind(案 K)**
- **B 両方 mind の System 1(案 F)**
- **C 割る**: 刺激が体の所まで届く物理(距離・光・遮り・音の減衰)は world。それを感覚が拾うか(検出の確率・どこを見ているか・混雑の紛れ・人の視線につられる)は mind の System 1。

**現実の世界の仕組みとの整合**
- 光や音が目と耳に届くのは物理です。拾えるかは見る人の感覚と、どこを見ているかで変わります。だから C が合います。
- 今の TTPF の式は人の検出のモデルなので、大半は心(System 1)の側です。距離と照明は世界が渡す入力です。

**影響するファイル**: 4〜5 本(`p_notice`・`perception/state`・`salient` の一部・`attention` の一部・`change_detect`)。

**推し: 移す段は A の置き場(呼び手は世界の過程だけなので、mind に置くと上向きの辺 A17 が増える)。9-3c で式を作り直すとき C に割る(9-3c で作り直すことは決まっている)。** `perception/state.py` の向きは、どちらの答えでも体の向きなので world です。

### 問い 7 権利と規則の表(制度の事実)は world か economy か

**今の事実【確認】**
- 権利台帳(`rights/ledger.py`)の読み手は、開閉店の過程(`opening`)・店の仕事の口と層・雇い主の知らせ(`roster`)・`economy_stage2`・権利の他のファイルです。
- 規則の表(`rules/table.py`)は machine(税の計算・改札)・human(条例)・norm(罰則の無い決まり、例: 路上飲酒の禁止)を持ちます。読み手は `economy/anchors`・`economy/taxes`・`calendar3/layer`・組み立てです。
- 両案の層の順が違うのがこの差の元です。F は economy を world の下に置くので、world が economy を読めます。K は economy に world.facts を読むことを許します(契約 6)。

**選択肢**
- **A world.facts(案 K)**
- **B economy(案 F)**
- **C world の中に「制度」の副包みを作る(A の名を変えた形)**

**現実の世界の仕組みとの整合**
- 法と権利は「X は Y と見なす」という制度の事実で、経済の一部ではありません。条例・営業の許可・罰則の無い決まりのように、お金と関係の無い物も多いです。A か C が合います。F も迷い 16 で「経済でない規則も economy に入る」と書いています。

**影響するファイル**: 6 本(権利 4・規則 2)。同じ層の考えで `engine/calendar.py` と `engine/ledger_api.py` も決まります。

**推し: A(名を見せたいなら C)。**

---

## 5. 案 K の迷い 16 件・原則への異論 6 件への見立て

### 迷い

| # | 見立て |
|---:|---|
| 1 法則の書き | **賛成**((a) で移し v3 で (c))。原則の文は問い 2 の直し方にするとよい。 |
| 2 `AgentState` の置き場 | **賛成**((a) world.model)。実行時に使うのは `systems/build.py` だけで、ほかは注釈だけと確かめた。foundation に置くと心が合法に import できてしまい、契約が効かない(F の置き方の弱点)。 |
| 3 腕の束ね | **賛成(ただし (b) を推す)**。問い 4。 |
| 4 presence | **賛成**((a) のあと (c))。F も world に置き、予定の部分を mind とする読み方を同じく迷いに挙げている。 |
| 5 権利・規則・暦 | **賛成**((a) world.facts)。問い 7。 |
| 6 意図・活動・焦点 | **賛成(今は act)**。焦点は 9-1 の注意で心の物だが、行為と一緒に書かれている。v3 で直すことに賛成。問い 5。 |
| 7 言葉を読む部品 | **賛成**((a) act.intake)。F の runtime 案は act → runtime の上向きを生む。 |
| 8 出来事の記録 | **賛成**((a)+「心は `find`・`positions` を呼ばない」の AST の検査)。F も foundation。 |
| 9 語彙と文の雛形 | **賛成(今は foundation)**。foundation の割り方は異論 4 を参照。 |
| 10 p_notice・attention・B4 | **賛成**。問い 6 の C を 9-3c の段の到達点に。 |
| 11 推論のクライアント | **賛成**((a) runtime/inference)。F も同じ。 |
| 12 封印を読む部品 | **保留**。(a)+AST の検査に賛成。(b) へ移すのは、F が挙げた `w19_freeze.HOLDOUT_TOKENS` と `w21_sources.W21Guard` が本当にランの側から要るかを確かめてから。 |
| 13 経済の計器 | **賛成**((a) economy)。F も同じ。 |
| 14 系の中身 | **賛成**((a))。F も同じ。原則の文の直しは §3 の 1。 |
| 15 試験の置き場 | **賛成**((a) src の後)。 |
| 16 割る時期 | **賛成**((a) 移す段と割る段を分け、`Renderer` は最後)。足すこと: いちばん先に §6-1 の固定の表(クラス → 今の名前)を入れる。`Renderer` を割るときは F の注意書き(`perceive` の副作用の順)を試験で固定する。 |

### 異論

| # | 見立て |
|---:|---|
| 1 world を 1 つの包みで書くと循環 | **賛成**。副包みの層を原則に書く案に賛成。F の「法則は差分を返す」は循環そのものを消すが、v3 の作業。 |
| 2 「世界を書けるのは act だけ」を直す | **賛成**。背景の E 区分の例外と合わせ、問い 2 の文にする。 |
| 3 society に腕の行き場が無い | **賛成**。F も同じ指摘(迷い 13・14)。 |
| 4 foundation は import の話に限る | **保留**。foundation(意味なし)と contracts(語彙と口の型)に割る案は筋が通るが、名の問題で振る舞いは変わらない。移した後に決めればよい。 |
| 5 runtime は中身に触らないは全部には言えない | **賛成**。F 異論 3 と同じ。「核は読まない・組み立てと系と結果は読む」で契約に書ける。 |
| 6 封印は import では守れない | **賛成**。封印の語の AST の検査と、ランを `sealed_only` で包む試験を足す案に賛成。 |

---

## 6. 案 K の数の主張の確認

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| 今の木: import の名 2,523(頭 2,152・関数の中 370・TYPE_CHECKING 1) | AST(shibuya の中の import の名を数える) | **一致**【確認】 |
| モジュールの対 1,251(頭 1,032・関数の中 218・TC 1) | AST | **一致**(F の 1,251 とも一致)【確認】 |
| 本物の TYPE_CHECKING は `economy/ops.py` の 1 文だけ | grep | **一致**(`economy/ops.py:75`)【確認】 |
| 名前を追う数え方 1,196 本 | 自前で再輸出の頭 10 本を飛ばして名前を追った | 1,211 本(+15・約 1%)。頭の数 10 本は一致。追い方の細部が違う【確認】 |
| 割らずに移すだけで包みをまたぐ辺 662 本 | 同じ追い方で、K の主な置き場(`agents/state.py` は foundation)に置いた | 669 本(+7)。近い【確認】 |
| **割った後に包みをまたぐ辺 796 本** | 関数単位の割り先の表が「ほか」で終わり、全部は載っていない | **再現できない**【未確認】 |
| **原則に反する辺 35 本** | 中身を部品ごとに確かめた | 部品は確認、合計は【未確認】。例外 T1〜T8 は読む名前が実在する(T2 `renderer.py` の `_signage_seen` が `_signage_poi` を呼ぶ・T3 `change_detect.py:302,310`・T4 `decision/layer.py:253-261`・T5 `relations.py` が関数の中で `notice_p`・T6 `perceive` が `_signage_seen`・T7 `decision/layer.py` が関数の中で `affordance_words`・T8 `speech/layer.py` が関数の中で `wom`)。腕の束ね 20 本はモジュールの対で 13+5+1+1 を**再現**。注釈だけ 7 本は、`AgentState`・`World` が `change_detect`・`renderer`・`resolve`・`norm_meter` で注釈だけに使われることを確認(本数そのものは割り方次第) |
| **包みの単位の循環 2 組**(world・act・economy と runtime・experiments) | 原因の辺があるかを見た | 原因の辺はある【確認】: 世界の過程 9 本 → resolve・`resolve.py:2401` → `economy_stage2`(関数の中)・economy → 規則の表・暦・権利(関数の中)・`experiment/branch.py`・`switch.py` → probe・tape ほか・`run.py:138`・`systems/build.py:388`・`systems/state_io.py:440`・`systems/table.py:91` → `experiment/layer`、`run.py:1213` → `run_kind`。割った後の組そのものは【未確認】。割らずに置くと 9 包みが 1 つの強連結成分になる(F の主張)ことは再現した |
| 乱数の領域の名 8 本 | grep | **一致**【確認】。8 本とも、今のモジュールの道と同じ文字列が乱数の領域の名として使われている(`rail.py:162`・`environment.py:112`・`chooser.py:64`・`mock.py:70`+接尾 `:112`・`:117`・`renderer.py:171`=`attention.py:227`・`p_notice.py:477`)。機械の置換で書き換えると乱数の列が変わる |
| 版の ID 70 か所・46 本 | grep(引用符つきの `shibuya.〜/〜`) | 70 か所は**一致**(docstring を除く AST では 69)。ファイル数は 52 本(build を除くと 41 本)で、46 本とは**合わない**【確認】 |
| `state_hashes._qual` が `module.Class` をハッシュする | コードを読む | **一致**【確認】(§2-1 のとおり final に入る道がある)。`VALUE_CLASSES` 4 行・`ALLOWED_CLASSES` 17 行・`CLASS_FIELDS` 2 行も一致。K の実測のハッシュ値は【未確認】(ランを回していない) |
| SoA の書き 395 か所・resolve 355・`writable()` は resolve の 50 回だけ | リポの AST の道具の関数で数えた | **一致**【確認】 |
| 82 列・心が外の列を読むのは 54 か所・19 列・11 本 | リポの `state_ledger_ast.scan`(strict)を K の持ち主の分け方で | 82 列は一致。読みは**約 77 か所・12 本**。54 は下限【確認】(§4 問い 1) |
| `AgentState` を使うのは 16 本・心と社会からは注釈だけ | AST | 15 本(再輸出の頭を除く)。実行時に使うのは `systems/build.py` だけ。**一致**【確認】 |
| lint-imports の HEAD の結果(5 契約 KEPT・1,250 の依存)・模擬の木の 8 契約 KEPT | — | 【未確認】(模擬の木がリポに無い。依存のパッケージも入っていない) |

あわせて確かめた案 F の数:
- 割らずに置くと 665/1,251、頭 7 本を空にすると 660/1,219(頭の import 517): **一致**【確認】。
- 再輸出の頭 7 本の src の呼び手 0: **一致**【確認】。
- 割らずに置くと 9 包みが 1 つの強連結成分: **一致**【確認】。
- 「path の文字列 158 個(状態台帳 100)」: 私の grep では `state_ledger.py` だけで引用符つきの `〜.py` が約 280 あり、数え方が分かりません。K の「機能する 91+記録の文 279」の方が、私の数えに近いです【確認は部分的】。

---

## 7. 合わせた案の要約

### 7-1 包みごとのファイル数(主な置き場・割るファイルは主な割り先で数えた)

既定は「(ii) は §2-2 の推し、(iii) は §4 の推し」です。

| 包み | 本数 | 案 K との差 | 案 F との差 | 問いの答えで動く分 |
|---|---:|---:|---:|---|
| foundation | 40 | +3 | +9 | 問い 4 が C なら切替口 4 本が mind・society へ |
| runtime | 41 | 0 | −3 | — |
| world | 60 | 0 | +8 | 問い 7 が B なら −6(economy へ)。問い 6 が B なら −1。問い 1 で表を foundation に置くなら −1 |
| mind | 32 | 0 | −13 | 問い 4 が C なら +5〜7。問い 5 が B なら +2。問い 3 が B なら −1 |
| act | 7 | 0 | +3 | 問い 5 が B なら −2 |
| economy | 18 | 0 | −7 | 問い 7 が B なら +6 |
| society | 27 | −3 | +4 | 問い 4 が B なら −17(新しい一時の包みへ) |
| experiments | 10 | 0 | −1 | — |
| validation | 6 | 0 | −2 | — |
| interfaces | 1 | 0 | 0 | — |
| build | 79 | 0 | 0 | 動かさない |
| 根 | 1 | 0 | 0 | — |
| 消す | 2(`agents/__init__.py`・`census/__init__.py`) | 0 | +2 | — |
| 計 | 324 | | | |

- 違う 59 本のうち、合わせた案は 50 本で K、7 本で F(`calendar_shadow`・`contact/device`・`defect_fixes_1103`・`events/body`・`events/links`・`events/__init__`・`manifest_sections`)、2 本は「消す」です。K に寄った 50 本のうち 16 本は (iii) で、問いの答えで動きます。
- 割るファイルには、K の 23 本に `calendar_shadow`(表の読み口と計器)を足します。F の割り方のうち、`constitution`(検査と定数)・`conversation`(4 つ)・`experiment/gate` の逆転・`llm/contract` の書式の切り出しは v3 の段に回します。
- 層と契約は K の形(副包みの層・8 契約)を土台にします。そのうえで、`defect_fixes_1103` は runtime、`contact/device` は world.things、`events/body` は mind に置きます。この 3 本は既存の契約に新しい違反を足しません【見立て・模擬はしていない】。

### 7-2 移す順(K §6-4 を土台に、足すこと)

1. 固定の表(クラス → 今の名前の文字列)を入れ、`_qual`・`state_codec.qualname`・`resume._canon` がそれを引くようにする。byte-check 19 構成【K の案・F には無い】。
2. 乱数の領域の名 8 本・版の ID・ハッシュの見出しを、機械の置換の除外の一覧として試験で凍結する。
3. 以後は K §6-4 の 2〜8。`Renderer` を割る段では、`perceive` の副作用の順を試験で固定する【F の注意書き】。

### 7-3 未決で残る問い

1. 問い 1: 心の読みの守り方(推し A を今・C を到達点)
2. 問い 2: 世界を書ける範囲と原則の文(推し A を今・C を到達点・文を直す)
3. 問い 3: 関係と約束の置き場(推し A)
4. 問い 4: 束ねの一時の置き場(推し B、または A)
5. 問い 5: 実行中の行為(推し A を今・C を到達点)
6. 問い 6: System 1 の「届いたか」(推し A を今・C を 9-3c で)
7. 問い 7: 権利と規則(推し A)
8. §3 の原則の直し 4 つ(runtime の核と組み立ての区別・書きの文・心の読みの守り・封印の AST の検査)の承認
9. 名だけの問い: foundation を foundation と contracts に割るか(K 異論 4・保留)

## 8. 確かめていないこと・限界

- 割った後の模擬(K の 796 本・35 本の合計・循環 2 組・副包みで 0)は再現していません。関数単位の割り先が全部は書かれていないためです。
- ランも pytest も lint-imports も回していません。1 バイト不変かは確かめていません。K のハッシュの実測値も確かめていません。
- 名前を追う数え方は私の手順で、K の 1,196 本と 15 本違います。
- 心の読みの数(約 77 か所)はリポの走査の道具の strict の数で、同じ名の別物(例 `agents.cell` と `pois.cell`、`memory.py:1115` の `getattr(ev, "cell")`)を含みうります。
- 案 F §2 の行の範囲と、案 K の割り先の関数の一覧は、全部は突き合わせていません(中心の部品の要所だけ)。
- 束ね・知識の口・会話の本文は docstring と import と呼び出しの名だけを読み、関数の本体は全部は読んでいません。
