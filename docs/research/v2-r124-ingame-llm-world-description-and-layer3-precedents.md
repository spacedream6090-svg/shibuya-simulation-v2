# R-124 答申: ゲーム内 LLM エージェント実験の世界の記述の仕方と、層 3(GM の裁定と判例)の設計案

<!-- hdr:v1 -->
- **分野**: ゲームエンジン工学・CG #30 / 自然言語処理・機械学習 #27 / ABM方法論 #21 / ソフトウェア工学 #29 | **重要度**: P0(回答 11-01 §13 R-I・§2 層 3 の復活の材料)
- **一次確認**: サブの自己評価。出典の単位で ◎ 原文を読んだ 19・○ 要約や二次や検索の要約で読んだ 8・△ 推測や未確認 6。**親検収**: 未
- **索引**: [INDEX.md](INDEX.md)

> 作成 2026-11-01・リサーチ役サブ(Opus 5.5)。子サブは起動していない。Web は読むだけ(WebFetch が自動で保存した PDF 2 本は、スクラッチの下でシステムの python と pymupdf を使って文字だけ取り出した。リポには置いていない)。
> 既存答申との関係(重ねない): Concordia の GM 部品のコード読み=[R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md) §1、GA・AI Town のコード読み=[R-43](v2-r43-code-reading-ga-aitown-humanoid.md)、行動の結果を決める 5 つの型(TextWorld・abcEconomics ほか)=[R-105](v2-r105-world-mutation-mechanisms-precedents.md) §1、Voyager・AWM・ASI・CBR・GPTCache=[D-71 答申](v2-d71-vocab-growth-research.md) §1.1・§1.4、裁定の信頼性(判定器のバイアス・注入)=[判例の深掘り](v2-precedent-system-deep-research.md) 面 1(D 等級=出典の親確認なし)。本書はこれらを引くだけにして、新しく読んだもの(The Sims の Edith・Convai・Inworld・Dwarf Fortress・Inform 7・Ceptre・LLM+P・VAL・WALL-E・AutoManual・WorldCoder・APC・Concordia v2 の技術報告・構造化出力の 2 つの実装)を足す。
> 対象の決定: [回答 11-01](../design/v2-answers-2026-11-01.md) §2(層 3 の復活)・§13・§14 / [指示書 10-12](../design/v2-wallbounce-decisions-2026-10-12.md) §1-4 D1〜D6・CP1・CP3・CP10・CP12 / [行き先 11-01](../reference/decision-routing-2026-11-01.md) §3・§5。

---

## §0 要旨

1. 先例の世界の書き方は 3 つに分かれる。**物が自分の行為を広告する型**(The Sims・Convai)、**前提を消費して結果を生む規則の型**(Dwarf Fortress の reaction・Inform 7・Ceptre・PDDL・TextWorld)、**LLM が結果を書く型**(Concordia の標準の GM・Generative Agents の物の状態)。
2. v2 の CP1(A〜E の状態と基本操作)は 2 つ目の型に当たる。層 3 の GM には「前提と差分」を規則の形で書かせ、検証と適用はコードが受け持つ形が先例と合う。
3. LLM に状態の変化を自由に書かせると、正解は最大 59.9% にとどまる(Wang 2024・R-105 で親確認済み)。Concordia v2 の技術報告も「Python のコードと LLM 呼びの混合」を設計の原則にしている。
4. 判例を語彙(規則)に昇格する先例はある(Voyager のスキル・AutoManual・WALL-E・WorldCoder)。ただしどれも 1 体のタスク達成が目的で、保存則と権利の機械検査を通してから昇格させた社会シミュの先例は、今回の検索では見つからなかった。
5. 「同じ状況は LLM を呼ばない」は、埋め込みの近さで引く意味キャッシュより、**鍵の完全一致**が決定論に合う(D-71 答申・APC も完全一致のキーワードから始めている)。
6. 設計案(§5): 入口は「未定義の語」と「なし+活動の文」の 2 つ。GM は閉じた基本操作の JSON 差分だけを出し、検証 8 段・適用は既存の口だけ・判例の鍵は 9 欄の完全一致・昇格は D3 の 8 手順に合流させる。
7. **決めないと進めない矛盾が 1 つある**: 10-12 D5(ラン中の裁定の腕を外す)・CP10(ランは開始時の版で最後まで)と、11-01 §2(ランの中は艦隊の 8B・同じ状況は呼ばない)との関係。§親に聞きたいこと 1。

---

## §1 先例の比較表(A)

列: ① 物と場所の表し方 ② 行為と効果(状態差分)の表し方 ③ 検証(保存則・物理の妥当性) ④ 語彙に無い行為の扱い ⑤ 判例・キャッシュ・スキルの再利用 ⑥ 世界の増やし方 ⑦ 使うモデルの分離 ⑧ 出典と等級。

| 先例 | ① 物と場所 | ② 行為と効果 | ③ 検証 | ④ 語彙外 | ⑤ 再利用 | ⑥ 増やし方 | ⑦ モデル分離 | ⑧ 出典・等級 |
|---|---|---|---|---|---|---|---|---|
| Project Sid(Altera 2024) | Minecraft のブロックと持ち物をゲームが持つ。体は座標つきの記憶で場所を知る(付録 C の例「a cave … near 558, 72, 496」) | PIANO の Skill Execution が低い層の行動に直す(§2.3・§8.2)。モジュールは共有の Agent State を読み書きする stateless な関数(§2.1) | ゲームの物理が守る。Action Awareness が予想と観測を比べる(§3.2)。「imaginary pickaxe」の幻覚が下流を汚すと書く(§1.3) | 書かれていない(ゲームで実行できない行動は起きないだけ。推測) | なし(スキルの書庫は書かれていない) | 法(憲法・税)は設計の前提として置く(§5.2・既存答申で親確認済み) | 反射は小さな非 LLM のネット(§2.1)。主な判断は GPT-4o(§3.2) | arXiv 2411.00114 v1 の HTML を読んだ ◎(実行の口の詳細は本文に無い) |
| Voyager(Wang 2023) | Minecraft(Mineflayer の JavaScript API を使う=△ 今回は読んでいない) | 行為=実行できるコード(スキル) | 環境の反応・実行の誤り・self-verification で直す(抄録) | 新しいスキルを書く | 成功して検証を通ったコードを書庫に入れ、説明の埋め込みで引く(D-71 答申 §1.1 で本文を確認) | 自動カリキュラム(探索を最大にする) | GPT-4 を blackbox で呼ぶ(抄録) | arXiv 2305.16291 抄録 ◎・本文は D-71 答申 |
| Concordia v1(Vezhnevets 2023) | GM の記憶と grounded variables(お金・持ち物・票。§2.2)。場所は GM の部品が文で持つ | 体は自然文で意図を書き、GM が結果の出来事の文を LLM で引く(§2・式 3) | 「GM checks the physical plausibility」(抄録)。専用の物理の検査は本文に無く、LLM の判断+grounded variables の検査(§2)。持ち物の釣り合いはプロンプトの文だけ(R-44) | 「violates the grounding」なら無効と伝える(§2) | なし | 実験ごとに grounded variables の組を選ぶ(§2) | GM も体も LLM(同じ作り) | arXiv 2312.03664 抄録と HTML 本文 ◎・コードは R-44 |
| Concordia v2(Vezhnevets 2025) | GM も entity。entity は component の集まり(README・§2) | 「Components are created by combining Python code with LLM calls」(§2) | Simulationist の要件=因果の一貫・予測の妥当・実証の裏づけ(§3.3)。強い守りは手書きの guardrail(§2) | GM が「generatively manage open-ended world details」(§3.3) | 本文に無い | engineer が部品を、designer が場面を作る分業(§2) | 本文は分けない | arXiv 2507.08892 v1 HTML ◎・GitHub README ◎(Apache-2.0) |
| Generative Agents(Park 2023) | 場所と物を包含の木で持ち、文に直して渡す(§5.1「there is a stove in the kitchen」) | 物の状態は文字列。行為のあと「what happens to the state of the object」を LLM に問う(§5.1・コーヒーメーカー off→brewing coffee) | なし | 語彙が無い(全部自由文) | なし | 物と場所は作者が置く | 1 つの LLM | arXiv 2304.03442 v2 HTML ◎ |
| The Sims(Edith・Forbus & Wright 2001) | 世界は object の集まり。Sim も「a somewhat more elaborate object」 | 物の behavior=実行の手続き+できるかを確かめる手続き(Check Tree)+広告(どの欲求をいくつ満たすか・距離で減る・性格で尺度が変わる) | Check Tree が偽ならその行為は選択肢にも出ない | 起きない(物が広告した行為しか選べない) | 広告の値が判例に近い役(固定)。「Skeptical Sims」=広告どおりだったかを記録して次の評価に効かせる案が演習に書かれている | 物を足せば行為が増える(拡張パックの仕組み=○ 二次の記事) | 判断は効用最大化のコード | Forbus & Wright「Some notes on programming objects in The Sims」(5/31/01 版)◎ |
| Convai(Unreal/Unity の NPC) | Environment=Actions・Objects・Characters の 3 部の契約。登録した物しか指せない | 行為の雛形(名前・説明・型つき引数)を LLM が選び、ゲーム側の handler が実行 | handler が成否を返す。失敗なら残りの列を捨てる | 名前が合わなければ handler を呼ばず警告。行為の組は「fixed when a session starts」 | なし | 物と雛形を開発者が足す(次のセッションから効く) | LLM はサーバー、実行はゲームエンジン | docs.convai.com の how-character-actions-work ◎ |
| Inworld(Goals 2.0) | 世界はゲーム側が持ち、trigger の引数で情報を渡す | goal=起動(intent か trigger)+action(instruction・say_verbatim・send_trigger)。character_changes で感情などを変える | 物理の検査はゲーム側(推測) | 決められた goal の外は会話だけ(推測) | なし | goal を足す | LLM は会話と意図の分類 | 公式の頁はログインへ転送され読めず、検索の要約だけ ○ |
| Dwarf Fortress | 材質は raw ファイルの token(融点・発火点・密度・状態ごとの名前=SOLID/LIQUID/GAS/POWDER など) | reaction=建物+REAGENT(消費する材料・量・条件)+PRODUCT(確率・量・材質を材料から継ぐ)+技能 | 材料が揃わなければ作れない(前提の消費で保存が守られる) | プレイヤーが raw を書いて足す(mod) | なし | Tarn Adams の 4 原則: 計画しすぎない・系を基本の要素とやりとりに分ける・複雑にしすぎない・現実の類比に基づく | LLM は無い | Game AI Pro 2 第 41 章 ◎・DF wiki の token と reaction の頁は 429 で直接読めず検索の要約 ○ |
| TextWorld | 事実の集まり(at・in など) | 「前提 → 結果」の書き換え規則。`$` の事実は残す | 規則の形で 2 か所に同時に居る状態が作れない | 規則が無い行為はできない | なし | 規則を足す | なし | R-105 §1-2 ○(本書では読み直していない) |
| Inform 7 | 物・部屋・関係 | 行為ごとに Check(意味があるか)→ Carry out(実際にする)→ Report(何が起きたかを言う)の rulebook。例外は Before・Instead・After | Check で止める | 新しい行為を作るときは表に列を足す | なし | 作者が規則を足す | なし | Writing with Inform §12.2 ◎ |
| Ceptre(Martens 2015) | 述語の事実=資源 | 線形論理の規則 `A -o B`=左を消費して右を生む | 消費と生成が規則の形そのもの(資源が湧かない) | 規則が無ければ起きない | なし | stage で部品を分ける | なし | AIIDE 2015・tutorial の要約 ○ |
| LLM+P(Liu 2023)+ VAL | PDDL の domain と problem | LLM が自然文を PDDL に直し、古典プランナが解く | 計画の検査は VAL(「The plan validation system」・BSD-3) | — | — | — | LLM は翻訳だけ・解くのはプランナ | arXiv 2304.11477 抄録 ◎・KCL-Planning/VAL README ◎ |
| WALL-E(Zhou 2024) | Minecraft・ALFWorld | LLM の世界モデル+学んだ少数の規則 | 探索の軌跡と予測の食い違いから規則を「inducing, updating, and pruning」 | — | 規則が prompt に入る(軌跡より短い) | 規則を学ぶ(勾配なし) | LLM | arXiv 2410.07484 抄録 ◎ |
| AutoManual(Chen 2024) | ALFWorld ほか | Planner がコードで計画、Builder が規則を直す、Formulator が手引きにまとめる | case-conditioned prompting で規則の幻覚を抑える | — | 手引きを小さな LLM の計画に使える | 規則の系をオンラインで育てる | 大きなモデルで作り小さなモデルで使う | arXiv 2405.16247 抄録 ◎(NeurIPS 2024) |
| WorldCoder(Tang 2024) | gridworld ほか | 世界モデルを Python のプログラムで持つ | プログラムが観測を説明できるか | — | コードを直して別の環境へ移す | — | LLM がコードを書く | arXiv 2402.12275 抄録 ◎ |
| APC(Zhang 2025) | — | 計画の雛形(固有名を抜いたもの) | — | — | キーワードを抜いて雛形のキャッシュに当てる。小さなモデルで具体化。費用 50.31%・遅延 27.28% 減(v2 抄録) | — | 作るのは大きなモデル・当てはめは小さなモデル | arXiv 2506.14852 v2 抄録 ◎(NeurIPS 2025) |
| AI Town | 入力口 13 と activity | R-43 | R-43 | R-43 | なし | — | — | R-43 ○ |

**読み取れること**
- **広告の型**(Sims・Convai)は「物が行為を持つ」。09-17 の原則「行動はオブジェクトの affordance 由来」と同じ考え方で、語彙を閉じたまま物を足せば世界が増える。そのかわり語彙の外は起きない。
- **規則の型**(DF・Inform 7・Ceptre・PDDL・TextWorld)は「前提を確かめ、消費し、生む」。保存則が規則の形そのものに入っている。CP1 の A(移す)・B(作る・使う)はこの型。
- **LLM が書く型**は語彙外を受けられる。そのかわり検証が弱い(Concordia v1 の持ち物はプロンプト頼み・GA は文字列を貼るだけ)。v2 の層 3 は「入口は LLM が書く型、出口は規則の型」の組み合わせにすれば先例の両方の利点を取れる。この組み合わせは Concordia v2 §2 の「Python と LLM の混合」と同じ向き。
- 語彙の版を**セッションの頭で固定**する先例がある(Convai「The action set is fixed when a session starts」)。CP10 と同じ形。

---

## §2 「状態差分」のスキーマの先例(B)

| 欄 | 先例の持ち方 | 出典・等級 |
|---|---|---|
| 前提 | Sims の Check Tree(物の状態からその行為ができるか)・Inform 7 の Check・PDDL の precondition・DF の REAGENT の修飾(UNROTTEN・EMPTY など) | ◎・◎・○・○ |
| 消費と生成 | DF の REAGENT→PRODUCT(量・確率・材質を材料から継ぐ)・Ceptre の `-o`・TextWorld の書き換え | ○・○・○ |
| 効果の量 | Sims の広告(欲求ごとに Min〜Max・性格で線形に尺度)・Concordia の grounded variables の増減 | ◎・◎ |
| 費用と時間 | Sims の広告は距離で減る(Attenuation)。Concordia は経過時間を GM の LLM が後から推定(R-44)。DF は技能と建物を前提に置く | ◎・○・○ |
| 誰に効くか | Sims の「Available to」の印(誰に広告するか)・Concordia の「Which entities are aware of the event?」(R-44) | ◎・○ |
| 知覚の文 | Inform 7 の Report・Concordia の event statement・Convai の結果を会話の文脈に戻す auto report | ◎・◎・◎ |

**構造化出力で形を強制する口**
- vLLM: `structured_outputs` に `json`(JSON Schema)・`choice`・`regex`・`grammar`。backend は xgrammar か guidance(旧 `guided_json` は v0.12.0 で廃止)◎(docs.vllm.ai)。
- Claude の API: `output_config.format` に `type: "json_schema"`。strict の tool use も同じ制限。**数の範囲(minimum・maximum)と文字列の長さの制約は使えない**、`additionalProperties` は false だけ、再帰のスキーマは使えない ◎(platform.claude.com)。**範囲の検査はどの道コードで行う必要がある**。
- 構造に合っても値の正しさは別(判例の深掘りの面 1 が「構造適合 96% でも値の正答は 0.69〜0.83」を引く。D 等級=親未確認 △)。

---

## §3 検証の先例(C)

- **前提の検査を機械で**: PDDL の計画を VAL で検査する(BSD-3)◎。Inform 7 は Check の rulebook ◎。Sims は Check Tree が偽なら選択肢にも出さない ◎。
- **保存を作りで守る**: R-105 の型 D(abcEconomics の give/take・AI Economist の取り置き・TigerBeetle の transfer だけが残高を変える=R-113)。v2 は既にこの型(`economy/ops.py` の `transfer`・`GoodsLedger.move_goods` が単一の口・書き手は AST で検査)。
- **権利は止めずに記録**: Dwarf Fortress の司法(R-113 で形だけ借りた)。v2 の `engine/rights/ledger.py` は書く口が `grant`・`revoke` の 2 つだけ。
- **ECS とルールエンジン**: Concordia v2 は entity と component(◎)。ゲームの ECS で「system だけが component を書く」形は v2 の「A〜D は基本操作から、E は物理のコードからしか書き換えない」(CP1)と同じ。業務のルールエンジン(Drools など)は今回読んでいない(§空欄)。
- **「物理の妥当性」の実装**: Concordia の論文は「GM checks the physical plausibility」と書くが、専用の検査器は本文に無く、LLM の判断に任せている ◎。**物理の妥当性を機械で検査した LLM の GM の先例は見つからなかった**。

---

## §4 判例の昇格の先例(D)

| 先例 | 何を貯めるか | 昇格の条件 | 固定の規則になるか | 出典 |
|---|---|---|---|---|
| Voyager | 成功したコード | 1 件の成功+self-verification | 書庫のコード=実行できる | D-71 答申 ◎ |
| ASI(Wang 2025) | プログラムのスキル | 実行して解けるか・新しいスキルを使ったか・環境が変わったか の 3 検査 | なる | D-71 答申 ◎ |
| AutoManual | 規則 | Builder が相互作用ごとに直す | 手引き(文) | 抄録 ◎ |
| WALL-E | 規則 | 予測と軌跡の食い違い | 規則(文)+LLM | 抄録 ◎ |
| WorldCoder | 世界モデルのコード | 観測を説明できるか | なる(Python) | 抄録 ◎ |
| APC | 計画の雛形 | 完了した実行から抜く | 雛形+小さなモデルで具体化 | 抄録 ◎ |
| CBR(Aamodt & Plaza 1994) | 事例 | RETAIN | 事例のまま | D-71 答申 ◎ |
| SkillsBench | 自作のスキル | 検証なしでは効果が無い(v1 の版を固定して引く) | — | 決定台帳 §4b(親訂正済み)○ |

- 共通点: 昇格の門は「頻度」より「1 件の成功+検証」(D-71 答申の判定と同じ)。
- 違い: どれも 1 体がタスクを解く場面。**多数の体が居る世界で、保存則・権利・規則の表の検査を通した差分を判例として貯め、語彙へ昇格した先例は今回の検索では見つからなかった**(決定台帳 §4b の「新規性の空白地帯」と同じ結論。ただし 10-12 で主張の形は書き換えた)。

---

## §5 層 3 の設計案(E・回答 11-01 §2 に沿う。すべて案・未決)

前提: 10-12 D1(人の手続きはコードに書かない)・CP1(A〜E・基本操作 4 つ)・CP3(権利は止めずに記録)・D4(正しい失敗と欠陥を分ける)を変えない。下の案は §親に聞きたいこと 1 の答えが「(b) 既定はラン後に下書き、ランの中は判例の参照だけ」のときを本線にし、(a) ランの中で GM を呼ぶ場合の差を各項に書く。

### ① 入口(住民が語彙に無い行為を「したがった」ことの検出)
今の v3 で取れる信号は 3 つある。
1. **未定義の語**(`action_code_of` が `UNDEFINED_ACTION`=-2)。今は段 0 の辞書写像 → 段 1 の記録(`llm/undefined.py` の `UndefinedActionRecord(raw_word, agent_id, tick, context_hash)`)。
2. **「なし」+活動の文が世界に触れる意図を含む**(例「傘を買いたいが売っていない」)。v3 の「なし」は失敗しない安全弁なので、意図が黙って消える。System 1(Ruri の埋め込み)か単純な語の表で「世界に触れる動詞を含むか」を印にする(推測・expedient)。
3. **既存の語の失敗**(`fail_intent` の結果コード)。現実でもできない失敗か、部品が足りない欠陥かを D4 で分ける材料。

自由記述の欄「ほかにしたいこと:」を足す案もあるが、D2(分類をメニューにしない)と設計者の指紋の観点で、足すなら腕(既定 OFF)にする。

### ② GM の下書きの入出力(JSON のスキーマ案)
入力: 体の意図の文(datamarking で囲む=判例の深掘り 面 1)・体の役割・場所の種類・対象の物の型と状態・関係する規則の表の行・基本操作の一覧と型。**入れないもの**: 錨の値(A1-6 の漏洩)・体の id・評判。
出力の案は次の JSON(`additionalProperties: false`)。
```json
{
  "schema": "shibuya.ruling/1",
  "verdict": "apply | correct_failure | defect",
  "preconditions": [{"pred": "at|open|stock_ge|cash_ge|holds|reach|free_hands", "args": ["actor", "poi:123"]}],
  "ops": [{"kind": "A_transfer_money|A_move_goods|B_make|B_use|C_grant|C_revoke|D_self|E_body", "args": {}}],
  "cost": {"time_min": 0, "money_yen": 0},
  "duration_min": 0,
  "affected": {"agents": ["actor"], "objects": ["poi:123"]},
  "percept": {"actor": "…", "observers": "…"},
  "evidence": [{"kind": "rules_table|law|common", "ref": "consumption_tax.standard_rate"}],
  "missing_part": "…(verdict=defect のとき・D3 の②)",
  "why": "…"
}
```
- ops は CP1 の基本操作だけ。**D は本人の分だけ**(10-03 の約束「他人の心は決めない」)。E は物理の法則への入力(歩く・持つ・置く・押す=D1 の体の基本動作)で、位置を直接書かない。
- 体の名前は `actor`・`target` などの役の名で書かせ、適用のときに束ねる(APC の「固有名を抜いた雛形」と同じ)。これで同じ下書きを判例に使い回せる。
- 先に自由に考えさせてから構造に提出させる(判例の深掘り 面 1「premature serialization」・D 等級 △)。

### ③ 検証(上から順に。落ちたら verdict を defect に書き換えて記録)
1. 形: JSON Schema(vLLM の xgrammar/Claude の json_schema)。
2. 範囲: 数の上下限・整数(Claude の構造化出力では書けないのでコード)。
3. 参照: 役の名・POI・SKU・権利の行が実在するか。
4. 型の許可: ops の種類が CP1 の表で許されるか(D を他人に書く・A を作る は不可)。
5. 前提: 述語をエンジンの読み口で評価(`GoodsLedger.can_sell`・`Rights.holds`・`talk_within_reach` など)。PDDL の precondition と VAL の役。
6. 保存則: お金は `economy/ops.py` の `transfer`、物は `GoodsLedger.move_goods` の口でしか動かさない。写しの状態に試しに当て、日の締めの検算(`economy/checks.py`)が閉じるか(R-105 の型 D)。
7. 権利と規則の表: 権利に反する差分は止めず「許可のない行動」の印(CP3)。規則の表の `kind=machine` の行は機械が強制する(例: 消費税は購入の口が自動でかける)。`human`・`norm` は記録だけ。
8. 物理の妥当性: 届く距離・時間が残っているか・持てる量・席や列の上限。**体の能力の表(持てる重さなど)は今リポに無い**(推測)。無い欄は「検査なし」と宣言して数える。

### ④ 適用(エンジンの口)
- `engine/resolve.py` の適用表(`_APPLY_BY_VOCAB`)に「裁定」の分岐を 1 つ足し(コードは末尾の 26 を予約する案)、中で ops を既存の口へ順に渡すだけにする。新しい書き手を作らない(`money_writers`・`rights_writers` の AST 検査がそのまま効く)。
- 出来事の記録(`engine/events/log.py`)の原因は、ランの中の GM 呼びなら `LlmCall(call_id)`、判例の参照なら `Process`(判例 id)を使う案。CP12 は原因を 3 型に限るので、4 つ目の型「判例」を足すかは §親に聞きたいこと 4。
- 順序: 同じ刻みに複数あれば体の番号の昇順(既存の「資源裁定 pk 昇順」と同じ)。

### ⑤ 判例の形と鍵(同じ状況は LLM を呼ばない)
判例の行(案): `precedent_id`・`key`(下の 9 欄の blake3)・`key_fields`・`ruling_json`(役の名のまま)・`n_applied`・`n_violation`・`n_contexts`(違うセルと時間帯の数)・`conf`(mechanism/expedient)・`source_model`・`schema_version`・`created_run`・`status`(candidate/trial/promoted/revoked)。
鍵の 9 欄(完全一致): ① 語彙の版 ② 正規化した意図の語(段 0 の辞書を通した後)③ 対象の型(`TargetKind`+物の種類)④ 対象の状態の印(営業中・在庫あり・空き)⑤ 体の役割 ⑥ 場所の種類 ⑦ 規則の表のハッシュ ⑧ 権利の有無の印 ⑨ スキーマの版。
- **入れないもの**: 体の id・自由文・時刻の細部(要るものは④の印にする)。入れると当たらない。
- 埋め込みの近さでは引かない(D-71 答申 §1.4「似た語が同じ裁定に吸われる」)。近いものは「候補」として下書きの入力に添えるだけ。
- 決定論: 鍵は状態の純関数なので、同じ状態・同じ判例の器ならバイト一致で同じ差分になる。

### ⑥ 昇格の手順(10-12 D3 の 8 手順に合流させる)
1. 候補: 違反 0 のまま `n_applied ≥ N`・`n_contexts ≥ 3`(判例の深掘りの「独立 3 事例」。値は expedient)。
2. 再生: 元の試みをスナップショットから再生し、保存則の試験と合わせて確かめる(D3 ⑤)。
3. 親(Fable)が生の記録で検収(D3 ⑥・D6)。
4. 形を決める: 09-17 の原則どおり、まず**物の affordance**(既存の語+対象の型)で表せるか。表せれば世界データに物と状態を足し、語は足さない。表せないときだけ契約の行(`ActionSpec`)を足す。
5. ユーザーの承認(D3 ⑦)→ 版上げ(D3 ⑧)。台帳は「世界の部品を足した記録の台帳」(10-12 CP8 の代わり)に 1 行・パターン台帳ゲートの 1 行(どの照合で使うか)・つなぎの台帳には載せない(代打ではない)。
6. 失効: 規則の表のハッシュが変われば鍵が変わるので自然に外れる。手で外すときは `status=revoked` にして消さない(判例の深掘りの bi-temporal)。

### ⑦ テープへの記録
- 呼びの表(`engine/tape.py`・今は `shibuya.tape/4`): GM の呼びも 1 呼 1 行。`agent_id` は意図を出した体、`wake_class` に GM の値を 1 つ足す案(int8)。
- 新しい表 `rulings.parquet`(案): `ruling_id`・`call_id`(GM の呼び・判例なら空)・`precedent_id`・`key`・`verdict`・`failed_check`(③の段の番号)・`ops_json`・`event_first`/`event_n`(出来事の記録の範囲)・`model`・`temperature`・`rules_table_hash`・`vocab_version`。

### ⑧ GM に使うモデルの分離
- **構築側(ラン後)**: 下書きはフロンティアモデル可(回答 11-01 §2)。構造化出力は `output_config.format`。数の範囲はコードで。
- **ランの中**: 判例の参照はモデルを呼ばない。(a) を選ぶ場合だけ艦隊の 8B に vLLM の `structured_outputs.json` で下書きさせる。LLM に状態の変化を書かせる正解は GPT-4 でも最大 59.9%(R-105)なので、8B の下書きは③の検証が主役になる(8B の正解率は未計測・推測)。
- 下書きの判定器と検収のモデルを分ける(判例の深掘り 面 1 の自己選好。D 等級 △)。

### ⑨ 決定論と再開への影響
- (b) 本線: ランの中は判例の器を開始時に凍結(CP10 と同じ)。manifest に器のハッシュ。決定論と checkpoint は今のまま。
- (a) の場合: 器がランの中で育つ。器を状態の台帳に入れ checkpoint に書く(`resume.py`・`restore_soa` の対象を増やす)。GM の呼びはテープで再生できるが、器の育ち方が分岐ごとに違うので、反実仮想の差に「判例の差」が混ざる。分岐の実験では器を凍結する(10-03 の約束「比較実験ではラン開始時の規則集の版を固定」と同じ)。

### ⑩ 既存の実装との差分の見積り(すべて推測)
| ファイル | 中身 | 行数の目安 |
|---|---|---|
| `src/shibuya/engine/ruling/`(新規 4 本: schema・validate・apply・precedent) | ②〜⑤ | 700〜1,000 |
| `src/shibuya/engine/resolve.py` | 裁定の分岐と順序表 | 40〜80 |
| `src/shibuya/llm/contract.py` | 裁定のコード 26 の予約・v4 の表 | 30〜60 |
| `src/shibuya/llm/undefined.py` | 段 1 の記録から入口へ・「なし」の印 | 50〜100 |
| `src/shibuya/engine/tape.py` | `rulings.parquet` と wake_class | 60〜120 |
| `src/shibuya/engine/events/` | 原因の型(4 つ目を足す場合) | 20〜50 |
| `tools/vocab/adjudicate.py` | 出力を契約の行の草案から差分の JSON へ | 100〜200 |
| tests(ミューテーション試験を含む=CP11) | | 800〜1,500 |

いまは実装の停止中で、11-01 の限定再開の段に層 3 は入っていない([指示書 11-01](../design/prompt-2026-11-01.md))。上の見積りは着手の計画ではない。

---

## §6 現実との整合の列(F・回答 11-01 §14)

| 錨(パターン台帳) | 層 3 を入れると | 測れなくなる危険と手当て |
|---|---|---|
| E10 客単価×客数・E5 消費支出(較正)・E4 エンゲル | 語彙外の買い方(取り置き・頼んで届けてもらうなど)が通ると、支出の道が増える | GM が率や平均を書くと錨と循環する。差分は 1 回の行為だけ(A1-2 の 5 条件②)。E5 は較正に使っているので、層 3 の支出が E5 の較正の後に増えたら `burned` の扱いを確かめる |
| E7 店舗間価格分散 | GM が値段を決めると錨を書いてしまう | 値段は ops に入れない(価格は構築時の値で固定=routing §3-2)。GM は既存の値を読むだけ |
| W1 ごみの量 | 「捨てる」が層 3 で通ると sink が増える | 捨てるは routing §5 で語に足す予定。層 3 の判例と語の追加が二重にならないよう、語が入ったら判例を `revoked` |
| D8 商業滞在時間・A4 交際 10 分/日 | 語彙外の過ごし方の時間を GM が書く | `duration_min` に上限の検査。分布は錨と照合するだけで、GM の入力に錨の値を入れない |
| D1′ 時刻別滞在人口・D11′ 目的構成 | 影響は小さい(移動は既存の語)と推測 | 判例の件数を計器に出し、件数が多い場合だけ感度を見る |
| W3 救急出場 | 「倒れた人を運ぶ」などを GM が通すと、無いと宣言した過程(routing §3-1)が裏口から入る | 主体が居ない過程を GM が代わりにしない(10-12 の「エンジンが代わりに実行しない」)。verdict=defect にして D3 の診断へ |
| 新しい計器 | 正しい失敗と欠陥の件数・判例の当たり率・却下率・違反 0 の割合 | 錨ではなく診断の行。D4 の計器の中身になる |

まとめ: 層 3 は錨を「直接動かす」より「無いと宣言した過程や率の過程を裏口から入れてしまう」危険のほうが大きい(推測)。GM の入力から錨を外し、主体の居ない過程は defect に落とす規則を③の検査に足すのが手当て。

---

## §空欄

1. Inworld の公式ドキュメント(docs.inworld.ai)はログインの頁へ転送され、本文を読めなかった。検索の要約だけ(○)。
2. Dwarf Fortress wiki の material と reaction の頁は 429 で直接読めなかった。検索の要約だけ(○)。Tarn Adams の講演(GDC など)は読んでいない。
3. Voyager の Mineflayer の API の部分(△)・MineDojo・ScienceWorld の本文(抄録には課題の数も模擬の中身も無い)・Smallville の派生は読んでいない。
4. The Sims の Will Wright の GDC 講演と Forbus の講義のスライドは読んでいない(Forbus & Wright の覚え書きの PDF だけ ◎)。拡張パックで物を足す仕組みの記述は二次の記事(○)。
5. 業務のルールエンジン(Drools・Rete)で差分を検査する先例は読んでいない。
6. 物理の妥当性を機械で検査する LLM の GM、保存則と権利の検査を通した判例の昇格を多数の体の世界で行った先例は、今回の検索では見つからなかった。
7. 8B の GM が JSON の差分を書く正解率・却下率の実測は無い(5070 の dm_eval で測れる。推測)。
8. Concordia v2 で grounded variables をコードで強制する部品の実装は読み直していない(R-44 は v2 のコードを読んでいるが、本書では確かめていない)。
9. 判例の深掘り(D 等級)が引く数値(構造適合 96%・値の正答 0.69〜0.83 ほか)は一次を読んでいない(△)。

---

## §親に聞きたいこと

1. **ランの中で GM を呼ぶか**(10-12 D5・CP10 と 11-01 §2 の関係)。(a) ランの中で 8B の GM が下書きし判例の器も育つ/(b) 下書きはラン後にフロンティアモデルで行い、ランの中は凍結した判例の参照だけ(親の推奨候補・決定論と分岐の実験に効く)/(c) (b) を既定にして (a) を腕(既定 OFF)。11-01 §2 の「ランの中は艦隊の 8B」がどれを指すか。
2. 10-12 D3 は「足すのは行動ではなく世界の部品」、11-01 §2 は「判例は語彙へ昇格」。昇格の形は §5 ⑥ 4 のとおり「affordance を先に・語は最後」でよいか。
3. GM の verdict に「正しい失敗」(現実でもできない)を GM が出してよいか。出すなら根拠(規則の表・法)の欄を必須にするか。
4. CP12 の原因の型は 3 つ。判例の適用を `Process` に入れるか、4 つ目の型を足すか。
5. 入口の②(「なし」+活動の文の印)を既定にするか。自由記述の欄「ほかにしたいこと」は腕に留めるか。
6. GM が本人の D(気持ち・予定)を書いてよいか。他人の D は書かない(10-03 の約束)を維持するか。
7. GM の入力に規則の表と法の条文を入れ、錨の値は入れない(A1-6)。この線引きでよいか。
8. 判例の昇格の閾値(`n_applied`・`n_contexts ≥ 3`)は expedient として置き、感度は全規模で測る(11-01 §12)でよいか。
9. 体の能力の表(持てる重さ・届く距離)が無い。③の 8 の物理の検査のために足すか、当面は「検査なし」と宣言して数えるか。

---

## 出典(読んだ日はすべて 2026-11-01)

- Project Sid: https://arxiv.org/abs/2411.00114 ・ https://arxiv.org/html/2411.00114v1 ◎
- Voyager: https://arxiv.org/abs/2305.16291 ◎(抄録)
- Concordia v1: https://arxiv.org/abs/2312.03664 ・ https://arxiv.org/html/2312.03664v2 ◎ / v2: https://arxiv.org/html/2507.08892v1 ◎ / https://github.com/google-deepmind/concordia ◎
- Generative Agents: https://arxiv.org/html/2304.03442v2 ◎
- The Sims: https://qrg.northwestern.edu/papers/Files/Programming_Objects_in_The_Sims.pdf ◎(Forbus & Wright・5/31/01 版)
- Convai: https://docs.convai.com/api-docs/plugins-and-integrations/convai-unreal-engine-plugin/features/character-actions/how-character-actions-work ◎
- Inworld: https://docs.inworld.ai/docs/tutorial-basics/goals(転送で読めず・検索の要約 ○)
- Dwarf Fortress: http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter41_Simulation_Principles_from_Dwarf_Fortress.pdf ◎ / https://dwarffortresswiki.org/index.php/Material_definition_token ・ https://dwarffortresswiki.org/index.php/DF2014:Reaction(検索の要約 ○)
- Inform 7: https://ganelson.github.io/inform-website/book/WI_12_2.html ◎
- Ceptre: https://ojs.aaai.org/index.php/AIIDE/article/view/12784 ・ https://github.com/chrisamaphone/interactive-lp(検索の要約 ○)
- LLM+P: https://arxiv.org/abs/2304.11477 ◎ / VAL: https://github.com/KCL-Planning/VAL ◎
- WALL-E: https://arxiv.org/abs/2410.07484 ◎ / AutoManual: https://arxiv.org/abs/2405.16247 ◎ / WorldCoder: https://arxiv.org/abs/2402.12275 ◎ / APC: https://arxiv.org/abs/2506.14852 ◎
- ScienceWorld: https://arxiv.org/abs/2203.07540(抄録 ◎・中身の詳細は無し)
- vLLM structured outputs: https://docs.vllm.ai/en/latest/features/structured_outputs.html ◎
- Claude structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs ◎

## 親の一次確認(第340・2026-11-01・Fable 5.1)

- The Sims(Forbus & Wright の覚え書き・筆者が抜いた文字を親が実読): 「a procedure that checks to see whether or not it is possible, and a set of advertisements that describe its properties in terms of what need(s) of a Sim it will satisfy」「Sims … choose … the behavior that maximizes their current happiness」「Check Tree … If this code exits false then that behavior will not appear … and also will not be available for autonomous selection」「Attenuation sets how quickly the advertisement fades … independent of distance」「a toilet advertises to Bladder, in a range from 0 to 70 (set by the Min and Max boxes)」=本文 §1 の「行為の手続き+Check Tree+広告=欲求ごとに Min〜Max・距離で減る」と一致(◎)。
- Concordia v2(arXiv 2507.08892v1・親が HTML を実読): §2 に「Components are created by combining Python code with LLM calls.」=一致(◎)。「GM checks the physical plausibility」は v1(2312.03664)の記述で、v2 には専用の検査器の記述が無い(§3.3 は「the GM can generatively manage open-ended world details」・§4.2 に physical consistency の言及)=本文 §0 の 3 の読みと矛盾しない。
- 等級: 筆者の ◎ 19・○ 8・△ 6 のうち親が原文で確かめたのは上の 2 本。Wang 2024 の 59.9% は R-105 で親確認済み。Voyager・WALL-E・AutoManual・WorldCoder・APC の「1 件の成功+検証で昇格」は筆者の読みのまま。
- 親の判断(ユーザーへ・PENDING §1-1): 問い 1(ランの中で GM を呼ぶか)は親案 (c)=下書きはラン後にフロンティアモデル・ランの中は凍結した判例の参照だけを既定にし、ラン中の 8B の GM は腕(既定 off)。10-12 D5・CP10(開始時の版で最後まで)と決定論を守れる。問い 2(affordance を先に・語は最後)=親案 賛成。問い 3〜9 は層 3 の実装の段(11-01p の段に無い=着手しない)で決める。差分の見積り(src 700〜1,000 行)は推測のまま。
