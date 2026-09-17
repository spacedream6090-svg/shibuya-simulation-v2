# R-23 第3批: 決定台帳の「D 等級だけを根拠にする 18 行」の一次確認

<!-- hdr:v1 -->
- **分野**: ゲームエンジン工学・CG #30 / ソフトウェア工学 #29 / 検証とV&V・UQ #22 / ABM方法論 #21 / 認知科学 #12 / 自然言語処理 #27 / 計算社会科学 #25 | **重要度**: **P0**
- **一次確認**: **B** = サブが一次資料を実読(逐語つき)・**親未確認**。本書の逐語・URL・判定はすべて親の再確認を要する。**特に §6 の 8 件は親が自分で当たること**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 対象: [決定台帳](../design/v2-redesign.md) §9 の 95 行のうち、[evidence map](../design/v2-decision-evidence-map.md) §3-2 が「**D 等級(出典 URL ゼロ)の答申だけを根拠にする**」と判定した **18 行**。
> 行番号は evidence map 作成時点(2026-09-17)のものと**現行ファイルで一致**することを確認した(L373-L467 = 95 行・見出し語も一致)。
> 先行: [batch1](v2-r23-primary-check-batch1.md)(8 本 28 主張)・[batch2](v2-r23-primary-check-batch2.md)(背骨 4 答申 32 主張)。**両批で確認済みの主張は本書では再検証せず、参照で済ませた**(表の「既確認」列)。
> 答申本体・決定台帳・設計書・台帳 3 ファイル・lit README・ライセンス台帳は**一行も編集していない**。コミットもしていない。作業日 2026-09-17。

---

## §1 対象 18 行と同定した答申

| 台帳行 | 行 ID | 決定の要旨 | 同定した答申(根拠) | 等級 | 決定行に答申名があるか |
|---|---|---|---|---|---|
| L382 | 8 移行計画 | v1 積み残しは台帳の門前条件を通ったものだけ | [pattern-ledger-deep](v2-pattern-ledger-deep-research.md) 面2 運用8条(`v2-pattern-ledger.md:6,10`) | D | ✗(設計書の脇道) |
| L385 | 4b 三層世界方式 | 採用+修正3点 | **本リポに答申ファイルが無い**(決定行は「リサーチ答申(08-29)」とだけ書く)。修正3のみ [institutions-deep](v2-institutions-deep-research.md) に対応 | D | ✗ |
| L386 | FE | ゲームは作らず 3D/VR 産業の技術知見を輸入 | [game-frontend](v2-game-frontend-research.md)・[game-tech-import](v2-game-tech-import-research.md) | D・D | ○ |
| L389 | 6 データ契約 | 案(b) 新スキーマ+3ストリーム | [data-contract](v2-data-contract-research.md) | D | ✗(P1P2 監査 2-41 経由) |
| L390 | U13 統合設計図 | スライド14枚を公式全体像に | [coupled-adaptation-deep](v2-coupled-adaptation-deep-research.md)(1:5:25)・[observation-projection-deep](v2-observation-projection-deep-research.md)(L-OBS/L-REC・R0-R6) | D・D | ✗ |
| L392 | U1 記憶 | (c)ハイブリッド・昇格要約のみ埋め込み | [memory-retrieval](v2-memory-retrieval-research.md) | D | ✗(P1P2 監査 2-8 経由) |
| L394 | U3 データ契約追記2点 | タグ付きイベント索引+checkpoint 時間スライス | [game-tech-import](v2-game-tech-import-research.md) **#1**(evidence map は game-frontend を挙げるが、中身は #1 が出所) | D | ✗ |
| L395 | U4 L-OBS/L-REC | (a)Phase 4 以降の観測アプリ | [observation-projection-deep](v2-observation-projection-deep-research.md)・[capabilities-business](v2-capabilities-business-research.md) §5 | D・D | ✗ |
| L396 | U5 層2実装形 | スマートオブジェクト広告+utility スコアリング | [game-tech-import](v2-game-tech-import-research.md) #5 | D | ✗ |
| L397 | U6 認知 LOD | on-demand 昇格を採用 | [game-tech-import](v2-game-tech-import-research.md) #4 | D | ✗ |
| L398 | U7 チャンク SoA | +空間グリッドを共通基盤に | [game-tech-import](v2-game-tech-import-research.md) #2+次点 | D | ✗ |
| L399 | 線引 16行表 | 方針確認(状態と集約=エンジン) | [engine-llm-boundary](v2-engine-llm-boundary-research.md)(`v2-world-process-design.md:5`) | D | ✗ |
| L400 | BM | ベンチマーク台帳の構造を承認 | [benchmark-standards](v2-benchmark-standards-research.md) §6 | D | ✗ |
| L401 | U12 パターン台帳 | 34行・強5本・運用8条 | [pattern-ledger-deep](v2-pattern-ledger-deep-research.md) 面1+面2 | D | ✗ |
| L403 | 予算 | 予算宣言表22項 | [llm-serving-deep](v2-llm-serving-deep-research.md)(`v2-budget-declaration.md:6`)。L2「ablation 20%」の根拠欄は**総称「方法論答申」** | D | ✗ |
| L405 | R2 世界過程 | 3類限定・線引き原則7本 | [engine-llm-boundary](v2-engine-llm-boundary-research.md)(L399 と同一答申) | D | ✗ |
| L458 | R15 可視化 | 計器盤 WebUI+deck.gl 2D | [game-frontend](v2-game-frontend-research.md) | D | ○(リンクあり) |
| L464 | R16 モデル選定 | Qwen3-8B INT8・32B AWQ・7×A5000 | [llm-serving-deep](v2-llm-serving-deep-research.md)・[legal-licensing-deep](v2-legal-licensing-deep-research.md) | D・D | ✗ |

**同定で判った最大の事実**: **L385(4b 三層世界方式)の根拠答申は本リポに存在しない。** 決定行が引く「リサーチ答申(08-29)」の固有名詞 —— **Orchestrated Reality・PDVA・NCP-Bench** —— を `docs/` 全体に grep すると、ヒットは `v2-redesign.md` の L188/L192/L194 **のみ**(`SkillsBench` だけが後発の [precedent-system-deep](v2-precedent-system-deep-research.md):84 に別文脈で 1 件)。すなわち **v2 の憲法級の決定(三層世界)の根拠文書が、本リポの外(v1 セッション記録)にある**。batch2 §6-1 が「最上流はここにある」と書いたとおりだった。本批では決定行に直接書かれた 5 主張を原典で当たった(§2-2)。

---

## §2 主張ごとの確認表

判定の語(第1・2批と同じ): **一致** / **数値不一致** / **出典が見つからない** / **主張が原典より強い**。逐語は 125 字以内。
「既確認」列 = batch1/batch2 で確認済みのため本批では再検証しなかったもの。

### 2-1 L382 + L401 — パターン台帳(pattern-ledger-deep 面1・面2)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 1 | 「**POM 適用の実録**: 半乾燥放牧地=**10^9 通り→11,316 組(0.001%)が生存**」(= 運用8条③ hard filter の実証根拠) | https://doi.org/10.1016/j.ecolmodel.2013.12.009 (*Ecological Modelling* **275**:78–88, 2014) | 抄録「As a result of the pattern-oriented parameterization, **11,316 out of 10⁹ parameter sets (approximately 0.001%)** were accepted as suitable.」「Using four generic patterns as filters…」 | **一致**(抄録のみ・本文有料) | 影響なし。**答申に書誌が無い**ので親は出典行を足すこと。なお原典が使ったのは**定性的・一般パターン 4 本**(= stylized facts)で、v2 の hard filter 5 本と同型 |
| 2 | 「『生存した**全**パラメータ群(単一最良でなく)を使う方が予測が良い』」 | 同上 | 抄録「The set of parameterizations that pass all patterns is used for further model analysis.」 | **一致**(条件つき) | 影響なし。ただし「予測が良い」の比較実験は抄録に無い=**答申の言い換えが一段強い** |
| 3 | 「明示的 POM 研究 **13 件**で概ね **1-5 本**」「アボカド FSPM 10,000→22 組」「Wang 2018=verification 7+validation 9」 | **見つからない** | 13 件の内訳・Wang 2018 の書誌が答申に無く、検索で同定できなかった | **本批の空欄** | 「コア 8-12 本」の本数根拠が未確認のまま。**決定(台帳 36 行・強 5 本)の本数はこれに依存している** |
| 4 | 面1 の見出し「stylized facts 候補 **44 本**」 | (内部) | 答申本文の節見出しは **P01–P45**(P01-P13 / P14-P19 / P20-P24 / P25-P29 / P30-P37 / P38-P45)= **45 本**。`v2-pattern-ledger.md:8` は既に「44 本は答申の誤記・原本は 45 行」と記録済み | **数値不一致**(答申内部の不整合・設計書では訂正済み) | 影響なし(訂正は伝播済み) |
| 5 | 「**P36 渋谷スクランブル実測**(平日 26 万/休日 39 万人/日・1 サイクル最大 3,000 人)」◎ | (一次不在) → 朝日新聞 2016-04-22 朝刊 p.29「【東京はてな】渋谷交差点、1回で3千人横断?」/ 元データ=**渋谷再開発協会 2014 流動計測調査**・渋谷センター街サイト(2016) | 一次調査報告は公開されておらず、到達できたのは新聞記事(有料)とその二次引用のみ | **出典が見つからない(一次)** | 影響は小(台帳では D1′/D4′ に差し替わり P36 は不採用)。ただし答申は **◎(最良)印**を付けている=**◎ の付け方が原典の入手可能性を見ていない** |
| 6 | A1(強・hard filter)「会話グループ 2人53.9%・95%が4人以下」 | — | **batch1 #6 で一致確認済み**(Dunbar, Duncan & Nettle 1995, Human Nature 6(1) Table 1) | 既確認 | — |
| 7 | C1(強・hard filter)「カスケード 99% が1世代・中央値1.3」 | — | **batch1 #7 = 数値不一致**(1.3 は平均)。`v2-pattern-ledger.md` C1 は **第203 で 2 本立てへ訂正済み** | 既確認・訂正済み | — |

### 2-2 L385 — 三層世界方式(08-29 答申・本リポに不在)

| # | 主張の逐語(決定行) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 8 | 「**Orchestrated Reality**(正準状態木+スキーマ検証済み差分のみコミット)が独立に同じ三層構造へ到達」 | https://arxiv.org/abs/2606.16014 | 抄録「state is a tree of canonical JSON entities」/「the transition kernel F is an LLM-driven **Plan-Diff-Validate-Apply (PDVA)** pipeline that commits **schema-validated, content-hashed JSON deltas**」 | **一致**(帰属注意) | 影響なし。注記推奨: 原典は自ら「**work in progress**」と書く CHI PLAY **Companion** '26 の短報+商用製品(WorldLines)の付随論文で、**査読済みフルペーパーではない**。「独立に到達」の 2 本目としては重みが Concordia より軽い |
| 9 | 修正1 定量根拠「純LLM状態管理は**非自明遷移 59.9%**」 | — | **batch1 #1 で一致確認済み**(BYTESIZED32-SP・https://arxiv.org/html/2406.06485v1) | 既確認 | — |
| 10 | 修正1 定量根拠「**10ステップ連鎖で累積精度 <1%**(ACL 2024)」 | https://arxiv.org/html/2406.06485v1 | 原典に「10 ステップ連鎖」の測定は**無い**。0.599^10 = **0.00604**(再計算)なので**算術は正しいが導出値**。**答申 engine-llm-boundary 自身が「[帰属注意] …論文の直接主張ではない=表現修正が必要」と自己訂正している** | **主張が原典より強い**(訂正が未伝播) | **文言を直す必要**。`v2-redesign.md:194` は「(ACL 2024)」と並記したままで、**答申の自己訂正が設計書へ伝播していない**(第1批 §3-B・第2批 §4-A と同型の 3 例目) |
| 11 | 修正1 定量根拠「**GM長期矛盾 40-68%/30ターンで無矛盾ほぼゼロ**(NCP-Bench)」 | https://arxiv.org/abs/2608.08160 (Ma+ ICML 2026, NCP-Bench) | 結果節「**40% to 68% of interactions ultimately end in factual conflicts**」/「GPT-5.2, remains **conflict-free in only 42% of cases after 20 turns**」。上限は **100 ターン**。「Only isolated runs satisfied all achievement commitments **within the 100-turn limit**」 | **一致**(40-68%)+**数値不一致**(30ターン) | **値を直す必要**。①「30ターン」は原典に無い(**20 ターン**での 42%)②「無矛盾ほぼゼロ」は原典では **100 ターン上限での全コミットメント達成率**=別の量。**修正1 の結論(裁定の出力はスキーマ検証済み差分に限定)は 59.9% と 40-68% だけで支えられるので決定は動かない** |
| 12 | 修正2 定量根拠「**無検証の LLM 自作ルールは効果ゼロの実測**(SkillsBench)」 | https://arxiv.org/abs/2602.12670 | **v1 抄録**「**self-generated Skills provide no benefit on average**, showing that models cannot reliably author the procedural knowledge they benefit from consuming.」(86 タスク/11 領域/7 構成/7,308 軌跡・curated は +16.2pp) | **一致**(版の固定が要る) | 影響なし。ただし**現行版(87 タスク/8 領域/18 構成・curated +16.6pp)は抄録から self-generated 条件を落としている**。しかも `v2-precedent-system-deep-research.md:84` は **+16.6pp(現行版)**を引いており、**設計書と答申が同一論文の別版を引いている**=版を固定して引き直すこと |
| 13 | 「**Project Sid(500体Minecraft=保存則だけの世界)で役割分化・文化伝播が足場なし創発**=層2の基礎を支持」(`v2-redesign.md:189`) | https://arxiv.org/html/2411.00114v1 | **batch2 #25/#26/#27 が確定**: §5.2「we establish an existing set of laws」・宗教は「20 agents … spawned as Pastafarians」=**足場つき**。同じ節の修正3 は第210 で「**Sid は足場なし条件を走らせていない**」へ訂正済み | **主張が原典より強い**(同一節の 3 行上が未訂正) | **文言を直す必要**。**L189 の「足場なし創発」と L198-199 の第210 訂正が同じ §4b の中で矛盾している**。L189 を「(足場=法体系・司祭 20 体を設計者が置いた上で)役割分化・文化伝播が観測された」へ直す |
| 14 | 「Concordia v2(GM=grounded variables の Python 側強制)」 | — | **batch1 #5 で一致確認済み**(終了判定を engine の役に数える点だけ原典より強い) | 既確認 | — |

### 2-3 L386 + L458 — フロントエンド・可視化(game-frontend / game-tech-import)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 15 | 「3D 渋谷は **Cesium ion「Japan 3D Buildings」(2024-06・2300万棟・3D Tiles)**か PLATEAU 公式配信で『読むだけ』」 | https://cesium.com/platform/cesium-ion/content/japan-3d-buildings/ | 「approximately **23 million individual buildings** across the country of Japan」/「derived from Japan's MLIT **Project PLATEAU** 3D City Model GML data」/「Format: **3D Tiles**」/ 210 超の市区町村 | **一致**(条件つき) | 影響なし(R15 第2段の材料)。**「2024-06」は公式ページに記載が無い**(§7)。利用条件は「license」でなく**帰属表示義務**のみ記載 |
| 16 | 「**Fortnite イベント同時 12.3M**=多数の小インスタンス同時開催」 | https://x.com/Fortnite/status/1253524351376330752 (Epic 公式アカウント・2020-04-24) | 「Over **12.3 million concurrent players** participated live in Travis Scott's Astronomical, an all-time record!」 | **一致** | 影響なし。注記: 12.3M は**単一インスタンス数でなく全世界同時接続数**。「シムは1本・観測は多数の read-only fanout」の論拠としては間接 |
| 17 | 「神視点UIの規範: SimCity GlassBox「**What You See Is What You Sim**」=画面上の事象は常にシムの1:1表現」(= **DECIDED L458 の GlassBox 規律の出所**) | https://www.ea.com/en-gb/news/inside-simcity-glassbox-game-revealed / GDC 2012「Inside the GlassBox」(Quigley・Willmott・Moskowitz) | EA 公式「We have a philosophy of **What You See Is What You Sim**; every aspect of the game is an agent that **reports back to the underlying simulation**.」 | **一致**(条件つき) | 影響なし。注記: 原典の含意は「**表示物がシムへ報告する**(エージェント化)」。v2 の使い方「**ビューアが独自に補間・演出したものは描かない**」は裏返しの含意で、**原典の逐語ではない**(v2 側の運用化として妥当だが出所は言い換え) |
| 18 | 「deck.gl 約100万点まで60FPS」「PLATEAU uc25-05 で高評価は 11人中4人」「UE5 City Sample 35,000人」 | — | **batch1 #11(一致)・#13(一致+見出しが原典より強い)・#12(出典が見つからない→第203 で訂正済み)** | 既確認 | — |
| 19 | (決定行 L458 の自己記述)「既存答申(v2-game-frontend-research.md・**親検収済み**=コードと構成の検収。**出典の一次確認は未・INDEX 等級 D(第218)**)」 | (内部) | **第218 で既に自己訂正が入っている**(evidence map §5 が挙げた「記載と等級の食い違い」は**解消済み**) | 既訂正 | 影響なし。evidence map §5 の L458 行は**古い状態を指している**ので親は消してよい |

### 2-4 L389 — データ契約 案(b)(data-contract)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 20 | 「**float 秒でなく整数ナノ秒**(MCAP が uint64 ns+ユーザー定義 epoch)」(= 決定の `t_ns(uint64)` の出所) | https://mcap.dev/spec | Serialization「**uint64 nanoseconds since a user-understood epoch** (i.e unix epoch, robot boot time, etc.)」。Message は `log_time`/`publish_time` の 2 本 | **一致** | 影響なし。**決定の主キー `(t_ns, seq)` の型根拠は原典どおり** |
| 21 | 「**MCAP ChunkIndex**(時刻範囲クエリ ◎)」 | 同上 | 「A **Chunk Index** record contains the location of a Chunk record and its associated Message Index records.」「exists for every Chunk in the file」 | **一致** | 影響なし |
| 22 | 「**OTel GenAI semconv**: Required=`gen_ai.operation.name`/`gen_ai.provider.name`・Recommended=`gen_ai.usage.input_tokens/output_tokens`・`gen_ai.conversation.id`・Opt-in=`gen_ai.input.messages`/`gen_ai.output.messages`」 | https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/ | 7 属性すべて**実在を確認**。ただし現在この registry 上では全て **Deprecated(Moved)** で、GenAI semconv は**別リポへ移設済み**。要求レベル(Required/Recommended/Opt-in)の記載は移設先にある | **一致**(存在)+**参照先が失効** | **文言を直す必要**。決定行「llm_calls=**OTel GenAI 準拠**」の準拠先 URL が opentelemetry.io から移動している。**実装時に参照する仕様の場所を固定し直す**こと |
| 23 | 「`invoke_agent`/`execute_tool`/**`create_memory`**/**`search_memory`** の語彙あり」 | 同上 | `gen_ai.operation.name` の既知値は `chat` / `create_agent` / `embeddings` / `execute_tool` / `generate_content` / `invoke_agent` / `invoke_workflow` / `retrieval` / `text_completion` の **9 値**。**`create_memory` と `search_memory` は無い** | **出典が見つからない**(4 語中 2 語) | 影響は小(記憶操作の span 名は v2 側で自由に付けられる)。ただし**「準拠」と書くなら実在しない値を並べない**。訂正案: 「記憶操作は既知値に無く、`retrieval` を使うか独自値を宣言する」 |
| 24 | 「**IEEE 1849(XES・2023 改訂)**: log>trace>event の3階層+全て key-value 属性・意味付けは extension 機構に外出し」 | https://www.xes-standard.org/ | 「**1849-2023** - IEEE Standard for eXtensible Event Stream (XES)…」(2023-08-09 公布・2016 版を置換・2033 まで有効)。extension 機構「provides semantics to the structure as prescribed by the XES instance」+ W3C XML Schema 2 本 | **一致**(条件つき) | 影響なし。**log>trace>event の 3 階層はこのランディングページには書かれていない**(規格本文=有料)。「コア最小+拡張で語彙を足す」という v2 が採った設計原理は extension 機構の記述で裏が取れる |
| 25 | 「DuckDB `read_parquet(hive_partitioning=true)` のプルーニング**実測30倍**」「arXiv 2104.01146 イベントソーシング進化5戦術」「arXiv 2105.00069 無バイアス全順序」 | — | **本批では未確認**(§7) | **本批の空欄** | 決定の物理配置(hive パーティション)と versioned events+upcaster の根拠が未確認のまま |

### 2-5 L390 — 統合設計図(coupled-adaptation / observation-projection)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 26 | 「時定数分離≥5倍(**3段はカスケード則の再帰適用で L1:L2:L3=1:5:25 以上**)」 | https://www.controlglobal.com/control/article/33005627/the-benefits-and-challenges-of-cascade-control / https://www.opticontrols.com/files/documents/cascade_control_perspective.pdf | ControlGlobal(Rhinehart)「the inner loop must be about **five times faster** than the outer loop」/ OptiControls「the minimum ratio … is subject to some dispute. Guidance … has ranged from **3:1 to as much as 20:1**」 | **一致**(条件つき)+**答申が [推測] と明記** | **文言を直す必要**。①原典は**2 段の実務則**(査読文献でなく制御実務の経験則・比は 3:1〜20:1 と幅がある)②**3 段への再帰は答申自身が `[推測]` と書いている**。`v2-architecture-roadmap.md:45` と `v2_design_slides.html:175` は **[推測] タグを落として断定**している |
| 27 | 時定数の順序: 答申「**習慣(最速)→記憶統合(中)→判例(最遅)**」 | (内部・写し検査) | `v2-coupled-adaptation-deep-research.md:187`「**習慣**(最速・個体ローカル)→**記憶統合**(中)→**判例**(最遅)」/ 同 :188「L1:L2:L3=1:5:25」/ P1P2 監査 :254 も「**習慣:記憶統合:判例** = 1:5:25 以上」 | **数値不一致(順序の取り違え)** | **値を直す必要**。`v2-architecture-roadmap.md:45`=「**記憶:習慣:判例**=時定数1:5:25」・`v2_design_slides.html:175`=「**記憶(個人):習慣(個人):判例(世界)**=時定数1:5:25で分離」。**先頭 2 項が入れ替わっている**。答申どおりなら習慣が 1・記憶統合が 5。`v2-c10-relations-agenda.md:26,53` が「1:5:25 の中間」で Δ・時定数を expedient 宣言しているので、**この取り違えは既に別決定へ波及している** |
| 28 | 「L-OBS=イベントログの決定論的射影(filter∘quantize∘fold)+**乱数消費0本**+`affects_k=False`」「L-REC=推定器階層 R0-R6」 | (答申内で完結・外部原典なし) | 答申自身が「中心命題」と書く**設計提案**で、原典に対応物は無い(POMDP/データ処理不等式は一般論として引かれるのみ) | **答申固有の設計(expedient)** | 影響なし。統合設計図が中身を採るなら「**先行なし=v2 の設計**」と宣言して載せるのが正しい |

### 2-6 L392 — 記憶と想起(memory-retrieval)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 29 | 「**GASim 実測**: 1万体30ステップで**記憶想起が316分**=実行時間の支配項→グラフ構造化想起で**16.4倍**高速化」(= 決定「索引は作らない・埋め込みは昇格分のみ」の速度根拠) | https://arxiv.org/abs/2605.07692 (ACL 2026 Long, pp.12510–12528) | 「Adding GOM yields a **16.39× speedup (from 316.33 to 19.30 minutes)**」(10,000 agents / 30 time steps)。全体は 6.69→0.67 h = 9.94× | **一致** | 影響なし。**支配項の判定も正しい**(316.33 / 401.4 分 ≒ 79%・再計算)。注記推奨: 316 分は**LLM 多段想起パイプライン**の時間であってベクタ検索の時間ではない。「検索自体は安い」を支えるのは別の論拠 |
| 30 | 「**1万体超で per-agent embedding 検索を採用した公表例はゼロ**」(=(b)全員embedding を推さない理由の中核) | (不在の主張) | 本批でも反証は見つからなかったが、**不在の証明は探索範囲に依存する**。答申が挙げる 4 例(AgentSociety 1万/OASIS 100万/Sid/AgentTorch 840万)の個別確認は本批では未実施 | **本批の空欄**(不在の主張) | **決定の主根拠が「不在の主張」である**。親は「ゼロ」でなく「**本探索範囲では見つからなかった**」へ表現を弱めるか、探索条件(検索語・日付)を台帳に残すこと |
| 31 | 「バイト予算例: 構造化3.0KB+統合ベクタ **12×388B ≈ 7.7KB/体・40万体で3.1GB**」(= 決定行の「約7.7KB/体」) | (再計算) | 12 × 388 B = 4,656 B = 4.547 KiB。3.0 KB + 4.656 KB = **7.656 KB ≒ 7.7 KB** ✓。400,000 × 7.656 KB = **3.06 GB** ✓ | **一致**(親再計算) | 影響なし。注記: 388 B = 384 次元 int8 + 4 B ヘッダ。決定行の「8-16本/体」に対し計算例は 12 本(中央値)を使っている |
| 32 | 「Generative Agents: recency 0.995・reflection 150・25体×2日で数千ドル」「Ruri-small 71.53」「Lally+ 中央値66日」 | — | **batch1 #14・#15・#16(一致)・#17(数値不一致→第203 で訂正済み)・#18(一致)** | 既確認・訂正済み | — |

### 2-7 L394 — データ契約追記2点(game-tech-import #1)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 33 | 「UE の `CheckpointSaveMaxMSPerFrame`=『**観測が本体を遅らせない**』の直接解」(= 決定「**checkpoint 保存の時間スライス**」の出所) | https://dev.epicgames.com/documentation/unreal-engine/demonetdriver-and-streamers-in-unreal-engine | 「DemoNetDrivers can amortize the time cost of recording replay data by setting the "**demo.CheckpointSaveMaxMSPerFrame**" CVar to a positive value.」/「will be queued to record on the next frame」/「caps the amount of time that checkpoint recording can take and helps to keep your game free of hitches」 | **一致** | 影響なし。**決定の片方(時間スライス)は原典どおり**。副作用も原典に明記「**slight visual errors can appear during playback** due to checkpoints containing data on Actors taken from different frames」=**v2 は「checkpoint 内の時刻が揃わない」を受け入れるかを宣言すべき** |
| 34 | 「checkpoint=差分スナップショット**30秒間隔**」 | 同上 | 「Checkpoint recording frequency can be adjusted by changing the CVar `demo.CVarCheckpointUploadDelayInSeconds`.」「The **default is 30 seconds**.」 | **一致** | 影響なし |
| 35 | 「**タグ付きイベントで全DLなし検索**」(= 決定のもう片方「**タグ付きイベント索引**」の出所) | 同上 | **このページにイベント/タグ付きイベント/部分ダウンロードの記述は無い**。最も近いのはリプレイのテキストメタデータ「user-defined **text tags** (HTTP Streamer only), which can be used when **searching or filtering through lists of games**」= **リプレイ間の検索**であってリプレイ内のイベント検索ではない | **出典が見つからない** | **文言を直す必要**。**U3 決定の 2 点のうち片方の出所が公式ドキュメントで確認できない**。UE のイベント API(`EnumerateEvents` 系)は HTTP Streamer REST API 側にある可能性があるので、親はそのページを当たるか、「**タグ付きイベント索引は v2 の設計(SC2 の game/tracker/message events 分離が近い先行)**」へ言い換える |

### 2-8 L395 — L-OBS/L-REC 観測射影(observation-projection / capabilities-business)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 36 | 「データ最小化曲線=**de Montjoye 2013**(**4点で95%・2点で50%**一意・**粒度は1/10乗でしか効かない**)」(= R5 再識別攻撃の手順の出所) | https://www.nature.com/articles/srep01376 (Sci Rep **3**:1376) | 抄録「**four spatio-temporal points are enough to uniquely identify 95% of the individuals**」/「the uniqueness of mobility traces **decays approximately as the 1/10 power of their resolution**」/ 本文「**two randomly chosen points still uniquely characterize more than 50%** of the users」 | **一致** | 影響なし。**R5 の手順根拠は原典どおり**。補足: 標本=150 万人・15 か月・アンテナ解像度(都市 0.15 km²〜地方 15 km²)。「2点で50%」は抄録でなく本文(Fig.2B) |
| 37 | 「現実チャネルの粒度: 基地局(アンテナ**都市0.15km²**・通信発生時のみ=**114回/人/月**)」 | 同上(0.15 km² 部分のみ) | 「The region covered by an antenna ranges from **0.15 km² in urban areas to 15 km² in rural areas**.」 | **一致**(0.15 km²)/ **114 回/人/月 は未確認** | 影響は小(CH-CELL のバイト予算に効く)。**114 の出所が答申に無い**(§7) |
| 38 | 「**予測可能性の上限 93%(Song+)は推定器クラス依存**(Kulkarni+ が RNN で超えた)=**L-REC を単一推定器で作ってはいけない根拠**」 | **本批では未確認** | — | **本批の空欄** | **L-REC の設計原理(R0-R6 の階層化)の唯一の外部根拠**なので優先度高 |
| 39 | 「合成データ評価=**Anonymeter**(risk=(main−control)/(1−control)・3攻撃並走)」「軌跡=集約カウントから**73-91%**復元・DP 後も深層再構成で **68%** 改善」 | **本批では未確認** | — | **本批の空欄** | 面1 の実験プロトコル(A0-A3・報告値の定義)の根拠が未確認 |
| 40 | 「**LLM 社会シムを攻撃テストベッドにした先行=すべて未発見=v2 の貢献点**」 | (不在の主張) | 本批では反証探索をしていない | **本批の空欄**(不在の主張) | **U4 の採否(Phase 4 へ後置)は「コア設計への影響ゼロ」という工程判断で決まっており、この不在主張には依存していない**=決定は未拘束 |

### 2-9 L396 / L397 / L398 — 層2実装形・認知LOD・チャンクSoA(game-tech-import #5/#4/#2)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 41 | #5「**The Sims**(Forbus&Wright: **オブジェクトが行動を広告**→個体は広告を欲求で採点するだけ)」(= **U5 DECIDED の出所**) | https://qrg.northwestern.edu/papers/Files/Programming_Objects_in_The_Sims.pdf (Forbus & Wright, v. 5/31/01, Northwestern QRG) | 「Sims … choose what to do by **selecting, from all of the possible behaviors in all of the objects, the behavior that maximizes their current happiness**.」「the procedure for that behavior (**which is part of the object**) is then run in the thread of the Sim itself」。関連講義は相互作用を「Normal (90%): **Advertised (Autonomous)** / Manual」と分類 | **一致** | 影響なし。**U5 の中核(行動はオブジェクト側・個体は採点するだけ)は原典どおり**。注記: 答申の「**拡張パックが成立した理由**」は原典に無い言い換え(§7) |
| 42 | #4「**AC Unity**(実AI **40**+高解像度 **120** で画面内 **1万体**)」(= **U6 認知LOD の出所**) | https://gdcvault.com/play/1022411/Massive-Crowd-on-Assassin-s (GDC「Massive Crowd on Assassin's Creed Unity: AI Recycling」) | 講演概要「With the limit of **40 real AIs and 120 high resolution models**, we could successfully create a scene where **10,000 crowd NPCs** are on screen at the same time.」/「a **pooling system** that allowed us to swap from low-res NPCs to high-res NPCs without the player noticing」 | **一致** | 影響なし。**「プール入替」も原典どおり**。動画本体は会員限定で概要のみ実読 |
| 43 | #4「**Hitman Absolution**(群衆 **1200体**・**必要時に本物NPCへ昇格**)」 | https://www.gdcvault.com/play/1015315/Crowds-in-Hitman / https://media.gdcvault.com/gdceurope2012/Presentations/Programming/Kasper_Fauerby_Programming_CrowdsInHitman.pdf | 「the techniques and optimizations used to achieve the **1200 character crowds** … while still running at 30fps」/ スライド「~**1200 agents per crowd with 500 on-screen**」「the player should **not distinguish between crowd and NPC actors**」 | **一致**(1200)+**主張が原典より強い**(昇格) | **文言を直す必要**(小)。公開資料が言うのは「**群衆とNPCの見分けが付かないようにする**」で、**「必要時に本物NPCへ昇格させる」という機構の明記は見つからない**。**同画面 500 体**の制約も答申に落ちていない。**U6 の決定(契機で昇格)は AC Unity のプール入替で十分支えられる**ので決定は動かない |
| 44 | #2「**Unity DOTS 16KB チャンク**」 | https://docs.unity3d.com/Packages/com.unity.entities@1.3/manual/concepts-archetypes.html | 「Each chunk consists of **16 KiB** and the number of entities that they can store depends on the number and size of the components」(**batch1 #27 と同一・本批で再確認**) | **一致** | 影響なし。単位は **KiB** |
| 45 | #2「Acton 2原則」「existential processing」「AgentTorch(完全テンソル化・数千万体・微分可能)」 | **本批では未確認** | — | **本批の空欄** | U7 の「発火index配列駆動」の設計原理側の根拠が未確認(16 KiB チャンクは確認済み) |

### 2-10 L399 / L405 — エンジン/LLM 線引き(engine-llm-boundary)

| # | 主張の逐語(答申) | 一次資料 URL | 判定 | 決定への影響 |
|---|---|---|---|---|
| 46-50 | BYTESIZED32-SP 59.9%(#1)/ OASIS 100万体1step 18h・A100×27(#2)/ OASIS 行動空間21種(#3)/ EconAgent スカラー2つ・刻み0.02(#4)/ Concordia v2 Engine 4役(#5) | — | **batch1 §2-1 で 5 主張すべて一致**(#5 のみ「終了判定を engine の役に含める」が原典より強い) | 既確認。**原則7本のうち 1・2・3・4・5 は原典で支えられている** |
| 51 | 「**Law in Silico**: 決定論側=プロファイル生成・厚生加重式・**腐敗ファクタ(p=0.7 の確率上書き)**」「裁定の一貫性検証は無い」 | **本批では未確認**(batch1 #19/#20 は別主張を確認) | **本批の空欄** | 原則6(裁定→判例昇格)の対照例の細部。決定への影響は小 |
| 52 | 「neuro-symbolic サーベイ(**178本**)=記号側は事実的グラウンディングと推論の強制に使う」「PettingZoo AEC=natureの介入も1エージェント」 | **本批では未確認** | **本批の空欄** | 原則5・理論枠組みの補強。決定への影響は小 |
| 53 | 「**rulingがruleになるのは容易、fiatがruleになるのは不可能**」(The Alexandrian)= 原則6「裁定は必ず判例化」の理論的根拠 | (ブログ) | **本批では未確認**。出所は TRPG 理論のブログであって査読文献ではない | **本批の空欄**(出所の性格は要注記) | **v2 の判例システム(R8・D-R2-3 行14)の理論的根拠が非査読ブログ 1 本**。後発の [precedent-system-deep](v2-precedent-system-deep-research.md) が置き換えているかを親が確認すること |

### 2-11 L400 — ベンチマーク台帳の構造(benchmark-standards)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 54 | 「**GEH統計**: 判定帯=GEH<5良好/5-10要調査/>10問題。**英DMRB=「交通量の85%がGEH<5」が較正基準**」 | https://assets.publishing.service.gov.uk/media/67ed0e54e9c76fa33048c634/tag-m3-1-highway-assignment-modelling.pdf (TAG Unit M3.1 Table 2) | TAG M3.1「Guideline 2: **GEH < 5 for individual flows (> 85% of cases)**」 | **一致**(数値)+**帰属が疑わしい** | **文言を直す必要**(小)。**「85% が GEH<5」は DMRB でなく DfT の TAG Unit M3.1 Table 2** に載っている。答申は DMRB と TAG の両方を並べているが、85% の帰属先が DMRB になっている。GEH 自体は DMRB 由来 |
| 55 | 「**TAG Unit M3.1**: 流量帯別3本立て(<700→±100以内・700-2,700→**±15%**・>2,700→±400以内)を **>85%** で+GEH<5 を >85%」 | 同上 | 「Individual flows within **100 veh/h** of counts for flows **less than 700** veh/h (> 85% of cases); within **15%** for flows from **700 to 2,700**; within **400 veh/h** for flows **more than 2,700** (> 85% of cases)」 | **一致** | 影響なし。**C8 忠実度計器盤の帯設計にそのまま移植できる**(逐語確認済み) |
| 56 | 「**重要**: 『受入基準の達成は fit for purpose を保証せず、未達も不適を意味しない』と明記=基準は合否ゲートでなく説明責任の土台」 | 同上 | **本批では逐語未取得**(PDF 119 頁・landing page には無し)。近い記述として §3.2.9「the acceptability guideline should be applied to link flows but **may be difficult to achieve for turning movements**」 | **本批の空欄** | **v2 の方法論(「歪む場所の宣言」)がこの一文に寄りかかっている**ので §6 の優先候補にした |
| 57 | 「**米FHWA Toolbox Vol.III(2019)**: ①出力の**95%が2σ帯内** ②**2/3が1σ帯内**+臨界時間帯 ③**BDAE**=平均絶対誤差が「実測の日間ばらつき」以下 ④**\|平均誤差\|≤(1/3)×BDAE閾値**」 | https://ops.fhwa.dot.gov/publications/fhwahop18036/chapter5.htm | Criterion I「**95% of simulated outputs fall within the ~2 Sigma Band**」(cr(t)±1.96σ)/ Criterion II「**Two-thirds** of the simulated results (and both critical time intervals) fall within the 1 Sigma Band」/ Criterion III **Bounded Dynamic Absolute Error**(閾値=代表日以外の各日の平均絶対差の平均)/ Criterion IV **Bounded Dynamic Systematic Error**「≤ **one-third (1/3) of the BDAE Threshold**」 | **一致**(4 基準すべて逐語一致) | 影響なし。**「実測の自然変動そのものを許容誤差にする」という v2 の移植は原典の設計どおり**。**D1′(L423)の閾値根拠「年次変動 JSD」もこの型**=同じ原典で支えられる。注記: 答申の「**GEH を捨て**」は本批では未確認(chapter5 に GEH 不採用の明言は見ていない) |
| 58 | 「**Pseudo-PFLOW**(全国 **1.3億人**合成人流・CC BY 4.0)=**R²>0.5**・東京都市圏トリップ量誤差**約10%**・目的別カバレッジ**93-104%**」 | https://arxiv.org/pdf/2205.00657 (親手順: WebFetch 保存 PDF を `fitz` で本文抽出) | 抄録「approximately **130 million people**」「a **coefficient of determination of more than 0.5** was confirmed for … population distribution and trip volume」/ §4.2.3「The results for the **Tokyo and Kinki** metropolitan areas indicate that the error in trip volume for each purpose is **approximately 10%**」/ Table 5 東京列 = 95% / 104% / 96% / **93%** | **一致**(数値)+**主張が原典より強い**(位置づけ) | **文言を直す必要**。①**93-104% は東京列の範囲**だが、**東京都市圏 PT は行動モデルの生成に使われた域**(§4.2「the Tokyo metropolitan area PT survey **used to generate** the behavior model」)=**in-sample 寄り**。②真の外部検証域は **Kinki(97-113%)と East Suruga(83-102%)** で、East Suruga は通勤 R²<0.5・通勤量 17% 過少。③CC BY 4.0 は論文に記載なし(配布先の JoRAS 側)。**「都市規模人流の現実的合格ライン」と呼ぶなら Kinki/East Suruga の値を使うべき** |
| 59 | 「**唯一級の実務的合否規則の先行**(EPJ Data Science 2026)=**30本の独立30日ラン**を実30日窓30個と対比し「**99%信頼区間が重なれば合格**」・不合格=**クラスタ係数4.6倍**過大・**コア規模3.8倍**」 | https://arxiv.org/abs/2508.21740 ・ https://arxiv.org/html/2508.21740v3 | 抄録「**30 independent 30-day simulations** of a technology forum modeled on Voat's v/technology」/「**30 matched, non-overlapping 30-day Voat comparison windows**」/「overlapping **99% confidence intervals** for unique users, root posts, and daily active users」/ Table 6「clustering **0.017 vs 0.004 = 4.6×**」「Core % of LCC **19.6% vs 5.1% = 3.8×**」(コアのノード数は 3.7×) | **一致** | 影響なし。**「歪む場所の宣言」の手本として v2 が採る形は原典どおり**。注記: 3.8× は **LCC に占めるコアの割合の比**であって「コア規模(ノード数)」は 3.7×。また Discussion には別の 3.8×(root 投稿の毒性)があるので**取り違え注意** |
| 60 | 「分野の現状: **Larooij&Törnberg=35本中22本が主観評価中心・15本は主観のみ**」 | https://link.springer.com/article/10.1007/s10462-025-11412-6 (*Artificial Intelligence Review*・受理 2025-09-24) / https://arxiv.org/abs/2504.03274 | 「**15 out of 35** papers are validated **solely** through subjective validation, and **22 out of 35** use subjective validation as their **only primary technique**」 | **一致** | 影響なし。**D-75 で既に親確認済みの答申と同じ数値**=整合。注記: 「minimal yardstick(最低基準)」の語は本批では本文中に確認できなかった |
| 61 | 「国交省鉄道需要テクニカルレポート=**全駅間終日断面交通量の現況再現性±10%以内を基本**」 | **本批では未確認** | — | **本批の空欄** | 5層構造の「物理・時空間」層の判定規則「駅±10%」の出所 |

### 2-12 L403 / L464 — 予算宣言表・モデル選定(llm-serving / legal-licensing)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 62 | 「**Prefix caching**: **16トークン単位ブロック・完全一致のみ**・prefill にのみ効く→**固定節を必ずプロンプト先頭へ寄せる**のが v2 の設計制約」 | https://docs.vllm.ai/en/latest/design/prefix_caching.html | 「**We only cache full blocks.**」/ 部分一致の例「only the first 2 blocks (8 tokens) hit the cache, because the 3rd block only matches 2 of 4 tokens」/ ブロック長は例示値(16 と 4 の両方を使用)/ cache_salt「this value is injected into the hash of the **first block**」 | **一致**(完全一致)+**条件つき**(16) | 影響なし。**「固定節を先頭へ」という設計制約は原典から正しく導ける**(親ハッシュ連鎖+full block のみ)。注記: **16 は vLLM の既定ブロック長であって仕様定数ではない**(設定可能)。知覚契約 §5 prefix 規約(L433)が 16 を前提にしているなら**既定値依存を宣言**すること |
| 63 | 「**Model Runner V2(2026-03)=小モデル×高リクエストで +56%**(**16K→25K tok/s**)——『小モデル高QPS はホスト側オーバーヘッドがボトルネック』=**本プロジェクトの負荷像そのもの・バージョンアップだけで二桁%が取れる可能性最大の項目**」 | https://vllm.ai/blog/2026-03-24-mrv2 | 「MRV2 achieves **25K output tok/s vs 16K** for MRV1, a **56.2%** improvement」。**条件 = Qwen3-0.6B を 1×GB200 で走らせたストレステスト**(「intentionally choosing a small model so that host-side overhead would be proportionally large」)。MRV2 は既定でなく `VLLM_USE_V2_MODEL_RUNNER=1`・v0.17+・**実験的**(0.18.0 時点で LoRA 等未対応) | **一致**(数値)+**主張が原典より強い**(外挿) | **文言を直す必要**。**+56% は 0.6B×GB200 という極端条件の値**で、**Qwen3-8B×A5000(CC 8.6)へそのまま当たる保証は無い**。かつ MRV2 は**実験的・非既定**。「バージョンアップだけで二桁%」は**未実証の期待値**として宣言し直すこと |
| 64 | 「**FP8 は CC≥8.9 必須=A5000(Ampere CC8.6)では W8A16 に落ちる**」 | https://developer.nvidia.com/cuda-gpus | **NVIDIA RTX A5000 = compute capability 8.6**(A100=8.0・L40S/Ada=8.9)。**batch1 §4 が「未確認」に残した穴を本批で埋めた**。FP8 の CC≥8.9 側は batch1 #10 で確認済み | **一致**(親再確認推奨) | 影響なし。**R16 の「INT8 を選ぶ」判断は 2 つの事実の合成で、両方とも原典で取れた** |
| 65 | 「**Qwen3 全般=Apache 2.0**」(主軸モデル選定の唯一の法務根拠) | https://huggingface.co/Qwen/Qwen3-32B | モデルカード メタデータ「**apache-2.0**」。**batch1 #25 は 8B の 1 点のみ確認**だったので、本批で**決定が名指しする 32B** を追加確認 | **一致**(8B+32B の 2 点) | 影響なし。**14B は未確認**(§7)。決定行が挙げる 3 サイズのうち 2 つで裏が取れた |
| 66 | 「**AutoAWQ は非推奨化=移行計画要**」 | https://github.com/casper-hansen/AutoAWQ (アーカイブ 2025-05-11) / https://docs.vllm.ai/en/v0.18.0/features/quantization/auto_awq/ | AutoAWQ repo「AutoAWQ is **officially deprecated** and will no longer be maintained」「adopted by the vLLM Project: llm-compressor」/ vLLM docs「**The AutoAWQ library is deprecated.** This functionality has been adopted by the vLLM project in llm-compressor.」 | **一致** | **決定に効く**。**L464 は「静的言語化 = Qwen3-32B AWQ」を採っているが、決定行に AutoAWQ 非推奨への言及が無い**。AWQ **形式**の推論は vLLM で継続サポートだが、**量子化ツールは llm-compressor へ移す**必要がある。答申が「移行計画要」と書いた項が**決定行に落ちていない** |
| 67 | 「`VLLM_BATCH_INVARIANT=1`(**CC≥8.0=A5000 可**)でバッチ不変・**オーバーヘッド非公表**」 | https://docs.vllm.ai/en/latest/features/batch_invariance.html / https://docs.vllm.ai/en/latest/usage/reproducibility.html | 「Batch invariance can be enabled by setting the `**VLLM_BATCH_INVARIANT**` environment variable to `1`」/「NVIDIA GPUs with **compute capability 8.0 or higher**」/「**may impact performance** compared to the default non-deterministic mode」(数値なし・**beta**)/ reproducibility「vLLM does **not guarantee** the reproducibility of the results by default」 | **一致** | 影響なし。**L467(B14)の親測定「コスト差なし」は原典が数値を出していない領域の一次データ**=v2 側の貢献。注記: 公式は現在も **beta** 表記 |
| 68 | 「スケールは**データ並列**: 8B/14B が 1 枚に載るなら **TP7 でなく DP7**(TP は毎トークン同期)」 | **本批では未確認**(vLLM 公式の DP/TP 選択指針の逐語は取れていない) | — | **本批の空欄** | **艦隊構成 A(均質 DP7)= L464 の決定そのもの**の根拠。ただし親の B10/B14/品質プローブ実測が別途ある |
| 69 | L403 L2「**ablation 20% 予約**」の根拠欄=「**方法論答申**」(`v2-budget-declaration.md:58`) | (答申ファイルが特定できない) | `docs/research/` に「方法論答申」という名の答申は無い。`v2-methodology.md` は**設計書**であって答申ではない | **一次が無い** | **(c) expedient として宣言し直すべき**。予算宣言表 22 項のうち少なくとも 1 項が**総称の根拠欄**で答申に落ちない |

---

## §3 行別の総合判定

| 台帳行 | 行 ID | 判定 | 理由 |
|---|---|---|---|
| L382 | 8 移行計画 | **(a)** | POM の「複数パターン同時フィルタ」は原典(Ecological Modelling 275)で支えられる。「門前条件」は v2 独自の語だが実質は 8条③+⑦ |
| L385 | 4b 三層世界方式 | **(b)** | 決定(三層採用+最小足場)は動かない。ただし**修正1 の数値 2 件**(10ステップ<1%・30ターン)を直す必要+**L189 の「足場なし創発」が同節の第210 訂正と矛盾**。根拠答申が本リポに無い点は **(c) 寄り** |
| L386 | FE | **(a)** | 方針決定。Cesium 2300万棟・Fortnite 12.3M・GlassBox いずれも原典で取れた。35,000 は訂正済み |
| L389 | 6 データ契約 | **(b)** | MCAP・XES は一致。**OTel の `create_memory`/`search_memory` が現行レジストリに無い**+参照先 URL が移設済み |
| L390 | U13 統合設計図 | **(b)** | **1:5:25 の順序が答申と逆**(設計書 2 本・スライド)+**答申の `[推測]` タグが落ちている** |
| L392 | U1 記憶 | **(a)** | GASim 316→19.3 分(16.39×)・バイト予算 7.7KB/3.06GB とも一致。ただし「公表例ゼロ」は **(c) 不在の主張** |
| L394 | U3 データ契約追記2点 | **(b)** | checkpoint 時間スライスは原典どおり。**「タグ付きイベントで全DLなし検索」が Epic 公式に見つからない** |
| L395 | U4 観測射影 | **(a)** | de Montjoye 4点95%/2点50%/1/10乗は一致。決定自体は工程配置(Phase 4)で一次にほぼ依存しない |
| L396 | U5 層2実装形 | **(a)** | Forbus & Wright に「全オブジェクトの行動から幸福を最大化するものを選ぶ」が逐語で存在 |
| L397 | U6 認知LOD | **(a)** | AC Unity 40/120/1万体・プール入替が逐語で一致。Hitman の「昇格」だけ言い換えが強い |
| L398 | U7 チャンクSoA | **(a)** | Unity DOTS 16 KiB が逐語一致。設計原理側(Acton・existential processing)は未確認 |
| L399 | 線引16行表 | **(a)** | batch1 §2-1 の 5 主張が一致。原則 1・2・3・4・5 は原典で支えられる |
| L400 | BM | **(b)** | TAG M3.1・FHWA 4基準・EPJ・Larooij は逐語一致。**GEH 85% の DMRB 帰属**と**Pseudo-PFLOW 93-104% が学習域(東京)の列**を直す必要 |
| L401 | U12 パターン台帳 | **(b)** | **強5本の名が陳腐化**(D4「休日平日比」は同日 09-01 の追補⑤で D4′ へ差し替え済み・D1 は 09-03 に D1′ へ)+34行 vs 36行+世界側38% vs 42-44% |
| L403 | 予算宣言表 | **(b)** | prefix 16 は既定値依存・MRV2 +56% は 0.6B×GB200 の条件を落としている。**L2「方法論答申」は (c)** |
| L405 | R2 世界過程 | **(a)** | L399 と同一答申。原則7本の 5 本まで原典で取れた |
| L458 | R15 可視化 | **(b)** | 決定の中身(deck.gl・uc25-05・GlassBox)は原典どおり。**evidence map §5 が挙げた「親検収済み vs D 等級」の食い違いは第218 で解消済み**=evidence map 側を直す |
| L464 | R16 モデル選定 | **(b)** | A5000 CC 8.6・Qwen3-32B Apache 2.0 を新たに確認=決定の骨格は支えられる。**AutoAWQ 非推奨が決定行に落ちていない** |

**集計: (a) = 9 行 / (b) = 9 行 / (c) = 0 行(ただし項目レベルで 4 件が (c))。**
(c) の項目: ①L403 L2「ablation 20% 予約=方法論答申」②L385 の根拠答申が本リポに不在 ③L392「1万体超で per-agent embedding 検索の公表例ゼロ」④L395「LLM 社会シムを攻撃テストベッドにした先行=すべて未発見」。②以外はいずれも**不在の主張か総称の根拠欄**。

**18 行のうち、DECIDED そのものを撤回すべき行は本批でも見つからなかった。**(第1批・第2批と同じ結論。)
一方、**18 行のうち 9 行で「答申→設計書の写し」か「原典→答申の言い換え」に直すべき箇所があった**=第1批が見つけた型(「中身の誤りより写しの事故が多い」)が 3 批連続で再現した。

---

## §4 4 つの検査の所見

### 4-1 写し検査(設計書の数値 → 答申 → 原典の 2 段)

| 箇所 | 設計書の値 | 答申の値 | 原典 | 判定 |
|---|---|---|---|---|
| `v2-architecture-roadmap.md:45` / `v2_design_slides.html:175` | **記憶:習慣:判例=1:5:25** | **習慣:記憶統合:判例=1:5:25 以上 [推測]** | カスケード制御の実務則(内ループが外ループの **5 倍以上**速く・3:1〜20:1 の幅) | **✗ 順序が逆・[推測] が落ちている** |
| `v2-redesign.md:194`(L385 修正1) | 10ステップ連鎖で累積精度 **<1%**(ACL 2024) | 「0.599^10 からの導出値・論文の直接主張ではない=表現修正が必要」(答申の自己訂正) | BYTESIZED32-SP に 10 ステップ連鎖の測定は無い | **✗ 訂正が未伝播**(0.599^10=0.00604 は算術としては正しい) |
| `v2-redesign.md:194`(L385 修正1) | GM長期矛盾 40-68%/**30ターン**で無矛盾ほぼゼロ | (答申不在) | NCP-Bench: 40-68% ✓ / **20 ターンで無矛盾 42%**・上限は **100 ターン** | **✗ ターン数が原典に無い** |
| `v2-redesign.md:189`(L385) | Project Sid 500体で**足場なし創発** | (答申不在。institutions 答申は 09-01 に自己訂正) | Sid §5.2「we establish an existing set of laws」・司祭 20 体をスポーン | **✗ 同じ節の第210 訂正と矛盾** |
| `v2-redesign.md:401`(L401) | 強5本 = A1/C1/**D1**/**D4休日平日比**/E2・**34行**・世界側 **38%** | — | `v2-pattern-ledger.md:5,166` = **36行・世界側 42-44%・強5本は A1・C1・D1′・D4′・E2**(追補⑤「休日/平日比は公表データに軸が無く**不成立**」) | **✗ DECIDED 行が同日の追補で陳腐化したまま** |
| `v2-budget-declaration.md:58`(L403 L2) | ablation 20% 予約・根拠=**方法論答申** | (該当答申なし) | — | **✗ 答申ファイルに落ちない総称** |
| `v2-pattern-ledger.md:8` | 「44 本は答申の誤記・原本は 45 行」 | 答申見出し「44 本」だが節は P01–P45 | — | **✓ 訂正済み**(答申側の内部不整合を設計書が正しく注記) |
| `v2-pattern-ledger.md:C1` | 平均 ≒1.3 / 1世代終了 >99% の 2 本立て | 中央値 1.3 | Goel+ 2016「is **1.3** … on average」 | **✓ 第203 で訂正済み** |

**強パターン(hard filter)への影響**: C1 は訂正済み。**A1 は batch1 で一致確認済み**。**残る問題は「DECIDED L401 の本文が強5本の旧名を持ったままであること」**で、判定関数のハッシュ固定(運用8条⑥)より前に直さないと、台帳と決定台帳で強パターンの名前が食い違ったまま Phase 2 ゲートへ入る。

### 4-2 訂正の伝播検査(答申に訂正が入った → それを引く設計書を grep)

| 訂正 | 入った場所 | 伝播先を grep した結果 |
|---|---|---|
| UE5 City Sample 35,000 → 出典未確認 | `v2-game-frontend-research.md`(第203) | **✓ 伝播済み**(`35,000` の設計書ヒットは無し) |
| Ruri-small 71.53 < mE5-large 71.65 | `v2-memory-retrieval-research.md`(第203) | **✓ 伝播済み**(`70.90`/`67.71` の設計書ヒットは無し) |
| Project Sid の解析は 500 体 / 足場なし条件は走っていない | `v2_significance.md:41`(第210)・`v2-redesign.md:198-199`(第210) | **△ 部分伝播**。修正3 は訂正済みだが、**同じ §4b の `v2-redesign.md:189` が「足場なし創発」のまま**(3 行上) |
| 「10ステップ連鎖で累積精度<1%」は導出値 | `v2-engine-llm-boundary-research.md` §2 の自己訂正 | **✗ 未伝播**。`v2-redesign.md:194` は「(ACL 2024)」を付けたまま |
| institutions 答申の自己訂正(制度は自己実行しない は強すぎる) | 09-01 の答申自己訂正 | **✓ 伝播済み**(第210)。batch2 §4-A は解消 |
| SkillsBench の版差(v1=self-generated 条件あり / 現行=無し) | (訂正なし・版が更新された) | **✗ 未整理**。`v2-redesign.md:196`=v1 の結論・`v2-precedent-system-deep-research.md:84`=現行版の +16.6pp。**同一論文の別版を 2 文書が引いている** |

### 4-3 循環参照検査(後発答申が「※既存答申X」と書き、X が D 等級)

`docs/research/*.md` で「既存答申」「答申U-」「同答申」を洗った結果、**本批の 18 行に関わる新規の循環は見つからなかった**(batch2 §4-C の応答率 0.8 が唯一の既知例)。
ただし**別の形の循環に近いもの**が 1 件:

- **L401(U12)の原本が本リポにも v1 リポにも無い**。`v2-pattern-ledger.md:8` が「完全定義表の原本は 45 行で、v1 リポでなく **Claude Code セッション記録側**に所在(発掘班報告参照)」と明記している。**強パターンの完全定義(判定関数)が、参照できない記録にある**。これは循環ではないが、**一次に到達できない点では同型**。

### 4-4 フロア併記検査(「ほぼゼロ」「桁違い」と書いた比較値に実データ同士のばらつきが併記されているか)

| 箇所 | 比較値 | フロア(実データ同士)の併記 | 判定 |
|---|---|---|---|
| benchmark-standards §6「歪む場所の宣言の運用形」 | 「**実測データ自身の年次ばらつきを達成可能上限として併記(FHWA式)**」 | **✓ 併記を明文で要求している**。FHWA Criterion I/II が文字どおり「観測の日間ばらつきを帯にする」設計で、原典と一致 | **✓ 合格**(本批で確認した中で唯一、フロア併記が方法論として組み込まれている箇所) |
| benchmark-standards §5「EPJ 30ラン vs 実30窓」 | 「クラスタ係数 **4.6倍**過大・コア規模 **3.8倍**」 | **✓ 実データ側の値が原典 Table 6 に並記**(0.017 vs 0.004 / 19.6% vs 5.1%)。ただし**答申は倍率だけを書き、実データ側の絶対値を落としている** | **△ 倍率のみ**。C8 計器盤へ移すときは実データ側の値も一緒に運ぶこと |
| benchmark-standards §3「Pseudo-PFLOW R²>0.5=現実的合格ライン」 | 「**R²>0.5**・誤差**約10%**・カバレッジ **93-104%**」 | **✗ フロアどころか、外部検証域(Kinki 97-113% / East Suruga 83-102%)の値が落ちている**。93-104% は**学習に使った東京の列** | **✗ 不合格**。「合格ライン」を学習域の数字で引いている |
| memory-retrieval「1万体超で per-agent embedding 検索の公表例はゼロ」 | 「ゼロ」 | (不在の主張なのでフロアの概念が当たらないが、**探索範囲の明示が無い**) | **△** 探索条件を残すこと |

---

## §5 直すべき値・文言(親が設計書へ反映する材料)

| # | 場所 | 現在 | 直す案 | 根拠 |
|---|---|---|---|---|
| 1 | `v2-architecture-roadmap.md:45`・`v2_design_slides.html:175` | 「記憶:習慣:判例=時定数 **1:5:25**」 | 「**習慣:記憶統合:判例** = 時定数 **1:5:25 以上**(**[推測]**: 2 段のカスケード制御則=内ループは外ループの 5 倍以上速く、を 3 段へ再帰適用したもの。実務則の幅は 3:1〜20:1・3 段の先行は無い)」 | 答申 :187-188・P1P2 監査 :254・ControlGlobal / OptiControls |
| 2 | `v2-c10-relations-agenda.md:26,53` | 「Δ と時定数は expedient 宣言(**1:5:25 の中間**)」 | #1 の順序訂正を反映して再確認(半減期 30 日が「中間」かは、どの層が 1 かで変わる) | 同上 |
| 3 | `v2-redesign.md:194`(L385 修正1) | 「非自明遷移59.9%・**10ステップ連鎖で累積精度<1%**(ACL 2024)」 | 「非自明遷移 59.9%(ACL 2024)。**10 ステップ連鎖で <1% は 0.599^10 = 0.6% からの導出値で論文の直接主張ではない**(答申が 2026-09-01 に自己訂正済み)」 | `v2-engine-llm-boundary-research.md` §2 の [帰属注意]・親再計算 |
| 4 | `v2-redesign.md:194`(L385 修正1) | 「GM長期矛盾40-68%/**30ターンで無矛盾ほぼゼロ**(NCP-Bench)」 | 「GM の事実矛盾で終わるランが **40-68%**・**20 ターン後に無矛盾を保つのは最良モデル(GPT-5.2)でも 42%**(NCP-Bench・arXiv 2608.08160・上限 100 ターン)」 | https://arxiv.org/abs/2608.08160 |
| 5 | `v2-redesign.md:189`(L385) | 「Project Sid(500体Minecraft)で役割分化・文化伝播が**足場なし創発**」 | 「Project Sid(**解析は 500 体**)で役割分化・文化伝播が観測された。**ただし法体系・司祭 20 体は設計者が置いた足場**であり、足場なし条件は走っていない(§4b 修正3 の第210 訂正と同じ)」 | arXiv 2411.00114 §5.2・Methods(batch2 #25-27)・同節 L198-199 |
| 6 | `v2-redesign.md:196`(L385 修正2) | 「無検証のLLM自作ルールは効果ゼロの実測(**SkillsBench**)」 | 「…(**SkillsBench arXiv 2602.12670 v1**・86 タスク/11 領域/7 構成/7,308 軌跡。**現行版は self-generated 条件を抄録から外している**ので版を固定して引く)」 | https://arxiv.org/abs/2602.12670・`v2-precedent-system-deep-research.md:84` が現行版 +16.6pp を引いている |
| 7 | `v2-redesign.md:401`(L401 DECIDED) | 「34行…強5本(A1会話グループ/C1カスケード/**D1滞在カーブ**/**D4休日平日比**/E2成長率ラプラス)」 | 「**36行**(世界側 **42-44%**)…強5本(A1・C1・**D1′ 滞在人口カーブ**(09-03 差し替え)・**D4′ 3街路の日内プロファイル分化**(09-01 追補⑤)・E2)。**D1′ と D4′ は同一パネル=実効強 4.5 本**」 | `v2-pattern-ledger.md:5,136,164,166` |
| 8 | `v2-budget-declaration.md:58`(L403 L2) | ablation 20% 予約・根拠=「**方法論答申**」 | 「**expedient(一次なし)**。`v2-methodology.md` の工程判断であり、答申の裏づけは無い」 | `docs/research/` に該当答申なし |
| 9 | `v2-benchmark-standards-research.md` §1 | 「**英DMRB**=『交通量の85%がGEH<5』が較正基準」 | 「**英DfT TAG Unit M3.1 Table 2 Guideline 2**=『GEH<5 を >85% のケースで』(GEH 統計そのものは DMRB 由来)」 | TAG M3.1 PDF |
| 10 | `v2-benchmark-standards-research.md` §3 | 「Pseudo-PFLOW … 東京都市圏トリップ量誤差約10%・目的別カバレッジ **93-104%**=都市規模人流の現実的合格ライン」 | 「**東京(=行動モデルの生成に使った域)93-104%・Kinki 97-113%・East Suruga 83-102%**。**外部検証域は Kinki と East Suruga** で、East Suruga は通勤 R²<0.5・通勤量 17% 過少。『合格ライン』を引くなら外部検証域の値を使う」 | arXiv 2205.00657 §4.2・§4.2.3・Table 5 |
| 11 | `v2-llm-serving-deep-research.md` 面1 / `v2-budget-declaration.md` | 「MRV2=小モデル×高リクエストで **+56%**…バージョンアップだけで二桁%が取れる可能性最大の項目」 | 「MRV2 は **Qwen3-0.6B × 1×GB200** のホスト側オーバーヘッド強調条件で **16K→25K tok/s(+56.2%)**。**既定ではなく実験的**(`VLLM_USE_V2_MODEL_RUNNER=1`・v0.17+・LoRA 等未対応)。**8B × A5000 への外挿は未実証**」 | https://vllm.ai/blog/2026-03-24-mrv2 |
| 12 | `v2-redesign.md:464`(L464 DECIDED) | 「静的言語化 = **Qwen3-32B AWQ**・TP4・温度0」 | AWQ 量子化の実行系を明記: 「**AutoAWQ は 2025-05-11 にアーカイブ済み**なので量子化は **llm-compressor** の AWQ レシピで行う(推論側は vLLM が AWQ 形式を継続サポート)」 | AutoAWQ repo・vLLM docs |
| 13 | `v2-data-contract-research.md` / L389 | 「OTel GenAI semconv…`create_memory`/`search_memory` の語彙あり」 | 「`gen_ai.operation.name` の既知値は 9 個(`chat`/`create_agent`/`embeddings`/`execute_tool`/`generate_content`/`invoke_agent`/`invoke_workflow`/`retrieval`/`text_completion`)。**記憶操作の値は無い**ので `retrieval` か独自値を宣言する。**仕様は opentelemetry.io から GenAI 専用リポへ移設済み**」 | OTel 属性レジストリ |
| 14 | `v2-game-tech-import-research.md` #1 / L394 | 「checkpoint …+**タグ付きイベントで全DLなし検索**」 | 「**Epic の DemoNetDriver 公式ドキュメントにイベント検索の記述は無い**(text tags は**リプレイ一覧の検索**用)。タグ付きイベント索引の先行は **SC2 の game.events / tracker.events / message.events 分離**の方。UE 側は HTTP Streamer REST API を一次で当たる(残務)」 | Epic DemoNetDriver ページ |
| 15 | `v2-game-tech-import-research.md` #4 / L397 | 「Hitman Absolution(群衆1200体・**必要時に本物NPCへ昇格**)」 | 「群衆 **1200 体/1 群衆・同画面 500 体**・30fps(GDC Europe 2012)。公開資料の目標は『**プレイヤーが群衆と NPC を見分けられないこと**』で、**on-demand 昇格の明記は見つからない**(昇格機構の先行は AC Unity のプール入替)」 | GDC Vault / Fauerby スライド |
| 16 | `v2-decision-evidence-map.md` §5 の L458 行 | 「決定行が『親検収済み』と書くが INDEX 等級は D=記載と等級の食い違い」 | **この行は消してよい**。現行 `v2-redesign.md:458` は「**出典の一次確認は未・INDEX 等級 D(第218)**」と自己訂正済み | `v2-redesign.md:458` |
| 17 | `v2-pattern-ledger-deep-research.md` 面2(POM 実録) | 「半乾燥放牧地=10^9→11,316 組(0.001%)」に**書誌が無い** | 出典行を足す: ***Ecological Modelling* 275:78–88 (2014), doi:10.1016/j.ecolmodel.2013.12.009**(「Pattern-oriented parameterization of general models for ecological application」) | 抄録逐語 |
| 18 | `v2-game-frontend-research.md` / L458 | 「SimCity GlassBox『What You See Is What You Sim』=**ビューアが独自に補間・演出したものは描かない**」 | 原典の逐語は「**every aspect of the game is an agent that reports back to the underlying simulation**」(表示物がシムへ報告する向き)。v2 の運用「ビューアは演出しない」は**裏返しの含意=v2 側の規律として宣言**する | EA 公式・GDC 2012 |

---

## §6 親が優先して一次確認すべき主張 上位 8 件

| 順 | 主張 | URL | なぜ最優先か |
|---|---|---|---|
| 1 | **NCP-Bench の「30ターンで無矛盾ほぼゼロ」** | https://arxiv.org/abs/2608.08160 | **憲法級の決定(L385 三層世界・修正1)の定量根拠**で、原典の上限は 100 ターン・報告は「20 ターンで 42%」。親は Table(Part II Conflict Breakdown)で 40-68% と 42% の両方を自分で見ること |
| 2 | **「10ステップ連鎖で累積精度<1%」は 0.599^10 の導出値** | https://arxiv.org/html/2406.06485v1 | 同じ L385 修正1。**答申が自己訂正済みなのに設計書が未訂正**=訂正の伝播検査の 3 例目。親は原典に 10 ステップの測定が無いことを本文検索で確かめ、0.599^10=0.00604 を再計算すること |
| 3 | **1:5:25 の順序と [推測] タグ** | https://www.opticontrols.com/files/documents/cascade_control_perspective.pdf | **設計書 2 本とスライドが答申と逆順**。かつ原典は制御実務の経験則(3:1〜20:1)で査読文献ではない。**D-68 経路3 と C10 関係辺の Δ・時定数がここに乗っている** |
| 4 | **Pseudo-PFLOW の 93-104% は東京(学習域)の列** | https://arxiv.org/pdf/2205.00657 (Table 5・§4.2) | **C8 忠実度計器盤の「合格ライン」の出所**。親は Table 5 の 3 列(東京 95/104/96/93・Kinki 97-113・East Suruga 83-102)と §4.2 の「Tokyo … used to generate the behavior model」を直接読むこと。PDF は `fitz` 抽出が要る |
| 5 | **OTel GenAI の `create_memory`/`search_memory` 不在** | https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/ | **L389 の決定文「llm_calls = OTel GenAI 準拠」の準拠先**。既知値 9 個に記憶操作が無く、仕様自体が別リポへ移設済み。実装前に参照先を固定すること |
| 6 | **UE Replay の「タグ付きイベントで全DLなし検索」** | https://dev.epicgames.com/documentation/unreal-engine/demonetdriver-and-streamers-in-unreal-engine | **U3 決定(L394)の 2 点のうち片方**の出所が公式ページに無い。親は HTTP Streamer REST API ページを当たるか、決定の根拠を SC2 側へ付け替えるかを判断すること |
| 7 | **MRV2 +56% の実験条件** | https://vllm.ai/blog/2026-03-24-mrv2 | **L403 予算宣言と L464 艦隊構成の両方**が「バージョンアップで二桁%」を期待値に含んでいる。条件は **Qwen3-0.6B × GB200**・MRV2 は実験的で非既定。9/10 のサーバー返却が絡む判断なので条件の確認が要る |
| 8 | **SkillsBench の版差** | https://arxiv.org/abs/2602.12670 | **L385 修正2 が v1 の結論(self-generated は効果ゼロ)を引き、`v2-precedent-system-deep-research.md:84` が現行版の +16.6pp を引いている**。同一論文の別版が 2 文書で混在。親は v1 と現行版の抄録を並べて版を固定すること |

---

## §7 空欄(見つからなかった・読めなかった・時間で落とした)

### 一次に当たれなかった主張(本批の対象 18 行の中)

| 行 | 主張 | 状態 |
|---|---|---|
| L382/L401 | 「明示的 POM 研究 **13 件**で概ね 1-5 本」「アボカド FSPM 10,000→22 組」「**Wang 2018** の台帳形式(verification 7+validation 9・合否=P≥0.05∧相対差≤20%)」 | **未確認**。答申に書誌が無く同定できず。**「コア 8-12 本」という本数決定の根拠**なので優先度高 |
| L382/L401 | 「ABC の次元の呪い(**Blum 2013**)」「気候の教訓(**Abramowitz 2019**)」「Kramer-Schadt 2007・Wiegand 2004」 | **未確認**(答申自身が「未取得」と書いている 3 件を含む) |
| L401 | **P36 渋谷スクランブル**(平日26万/休日39万・3,000人/サイクル) | **一次に到達できず**。朝日新聞 2016-04-22(有料)→ 渋谷再開発協会 2014 調査(非公開)。答申の ◎ 印は再考が要る |
| L401 | P01 接触時間べき則(指数-2前後・平均46秒・SocioPatterns)= 台帳 A2 | **未確認**(batch1 §4 から持ち越し) |
| L385 | **08-29 リサーチ答申そのもの**(Orchestrated Reality・PDVA・NCP-Bench・SkillsBench・Concordia v2 の 5 本を束ねた文書) | **本リポに不在**。原典は v1 セッション記録側。**決定台帳で最も上流の行の根拠文書が参照できない** |
| L389 | DuckDB hive プルーニング **30 倍**・arXiv **2104.01146**(イベントソーシング進化5戦術)・arXiv **2105.00069**(無バイアス全順序)・LangSmith `dotted_order` | **未確認**(時間切れ)。`(t_ns, seq)` 主キーと versioned events+upcaster の根拠 |
| L389 | XES の **log > trace > event 3 階層** | **規格本文が有料**。xes-standard.org のランディングページには階層の記述が無い |
| L390 | **Borkar 1997 TTSA**・GAN の TTUR・特異摂動論の ε≪1・Simon 1962 近似分解可能性・Sculley+ 2015 隠れループ | **未確認**。1:5:25 の理論側(実務則側は確認した) |
| L392 | 「**1万体超で per-agent embedding 検索の公表例はゼロ**」の反証探索 | **未実施**(不在の主張) |
| L392 | Lyfe Agents Summarize-and-Forget(2310.02172)・SCM(2604.20943)・Murre&Dros 2015・Conway SMS | **未確認** |
| L395 | **Song+ 予測可能性 93%** と **Kulkarni+ の RNN 超え**(= L-REC を単一推定器で作らない根拠) | **未確認**。優先度高(§6 の次点) |
| L395 | **Anonymeter** の risk 式・集約カウントからの軌跡復元 **73-91%**・DP 後の深層再構成 **68% 改善**・Carlini「MIA From First Principles」の TPR@FPR=0.1%・**CDR 114 回/人/月** | **未確認** |
| L396 | **IAUS**(Infinite Axis Utility System)・GOAP/BT/Utility 比較(Game Developer) | **未確認**。「utility は選択理由が数式で読める」= 説明可能性の主張の出所 |
| L396 | Forbus & Wright「**拡張パックが成立した理由**」 | **原典に無い**(答申の言い換え)。PDF 目次と §2 の逐語では確認できず |
| L398 | **Acton CppCon 2014 の 2 原則**・Fabian の existential processing・**AgentTorch 840万体** | **未確認** |
| L399/L405 | **Law in Silico の腐敗ファクタ p=0.7**・neuro-symbolic サーベイ **178 本**・PettingZoo AEC・**「ruling vs fiat」(The Alexandrian・非査読ブログ)** | **未確認**。最後の 1 件は**原則6(判例昇格)の理論的根拠が非査読ブログ 1 本**である点が要注記 |
| L400 | TAG M3.1 の「**受入基準の達成は fit for purpose を保証しない**」の逐語 | **未取得**(PDF 119 頁・landing page には無し)。**v2 の方法論がこの一文に寄りかかっている**ので §6 に入れるか迷った |
| L400 | 国交省鉄道需要テクニカルレポート **±10%**・モバイル空間統計/KLA/Agoop の粒度表・**JR渋谷 222,150人/日・メトロ 751,998人/日**・FHWA が「GEH を捨てた」かどうか | **未確認** |
| L403/L464 | 「**TP7 でなく DP7**」(vLLM 公式の DP/TP 選択指針)・W8A8-INT8 の「精度 99% 超回復(Red Hat 50万件評価)」・**Qwen3-14B の Apache 2.0**・prefix-aware routing の「レイテンシ 3-10 倍改善」 | **未確認**。**艦隊構成 A の根拠そのもの**(ただし親の実測が別途ある) |
| L458 | AgentSociety の **MQTT 3 トピック**・Generative Agents の `/replay` エンドポイント・uc24-07 の **MF-JSON** | **未確認**(batch1 が deck.gl と uc25-05 を確認済み) |
| L464 | Gemma PUP の自動意思決定制限・Swallow の二重ライセンス・Llama 3.1 で蒸留禁止条項が削除 | **未確認**(batch1 §4 から持ち越し・Qwen3 主軸の決定には効かない) |

### 読めなかった / 上限に当たったもの

- **Ecological Modelling 275:78-88(POM 半乾燥放牧地)は ScienceDirect で有料**。抄録の逐語(11,316 / 10⁹ / 0.001% / four generic patterns)のみで判定した。
- **TAG Unit M3.1 の PDF(119 頁)は landing page 経由で本文が取れず**、Table 2 の逐語は検索経由の引用で取った。**親は PDF を直接開いて §3.2 を読むこと**(URL は §5 #9)。
- **Pseudo-PFLOW の arXiv PDF は WebFetch がバイナリを返した**ため、保存分をシステム python の `fitz` で本文抽出して読んだ(記憶ノート「PDF 読解の作法」の手順)。24 頁・§4.2 と Table 5 を実読。
- **opentelemetry.io の GenAI spans ページは「別リポへ移設」のリダイレクト通知のみ**。属性の実在は registry ページで確認したが、**Required/Recommended/Opt-in の要求レベルは移設先(semantic-conventions-genai リポ)にある**ため未確認。
- **GDC Vault の AC Unity / Hitman の動画本体は会員限定**。講演概要と GDC Europe 2012 の公開スライド PDF の記述で代替した。
- **朝日新聞 2016-04-22 は有料**。渋谷スクランブルの数値は Wikipedia の脚注経由でしか辿れず、元データ(渋谷再開発協会 2014 流動計測調査)は非公開。
- **Cesium ion Japan 3D Buildings のページに公開日(2024-06)の記載が無い**。棟数・出所・形式は確認できた。
- **`v2-redesign.md` の L385 が引く 08-29 答申は本リポに存在しない**ため、決定行に直接書かれた主張だけを原典で当たった(§2-2)。

---

## lit README 追記行

> 形式は [lit/README.md](lit/README.md) の既存行と同じ(`| メモ | 分野 | 一次確認 | 要点 |`)。**新規出典のみ**。メモファイル本体は本批では作成していない(親がメモを起こすときの素材)。

| [gamedev__ue-replay-checkpoint-timeslice](lit/gamedev__ue-replay-checkpoint-timeslice.md) | ゲームエンジン工学 #30 / ソフトウェア工学 #29 | **実読**(サブ・Epic 公式 DemoNetDriver ページ) | **U3(L394)の片方の出所**。`demo.CheckpointSaveMaxMSPerFrame`=フレーム当たり上限を超えたアクタは次フレームへ繰り越し・既定 checkpoint 間隔 **30 秒**(`CVarCheckpointUploadDelayInSeconds`)。副作用「checkpoint 内のアクタが別フレーム由来になる」を原典が明記。**「タグ付きイベントで全DLなし検索」は同ページに無い** |
| [gamedev__acunity-crowd-ai-recycling](lit/gamedev__acunity-crowd-ai-recycling.md) | ゲームエンジン工学 #30 | **抄録のみ**(GDC Vault 講演概要・動画は会員限定) | **U6 認知LOD(L397)の出所**。「**40 real AIs and 120 high resolution models** で画面内 **10,000** crowd NPCs」+低解像度↔高解像度の**プール入替**。v2 の on-demand 昇格の唯一の数値先行 |
| [gamedev__hitman-absolution-crowds](lit/gamedev__hitman-absolution-crowds.md) | ゲームエンジン工学 #30 | **抄録のみ**(GDC Vault 概要+GDC Europe 2012 公開スライド) | **1200 体/群衆・同画面 500 体・30fps**。目標は「プレイヤーが群衆と NPC を見分けられないこと」。**「必要時に本物NPCへ昇格」の明記は公開資料に無い**=答申の言い換え |
| [gamedev__forbus-wright-sims-objects](lit/gamedev__forbus-wright-sims-objects.md) | ゲームエンジン工学 #30 | **実読**(Northwestern QRG PDF・v.5/31/01) | **U5 層2実装形(L396)の出所**。「全オブジェクトの全行動の中から**現在の幸福を最大化する行動を選ぶ**」「行動の手続きは**オブジェクトの一部**だが Sim のスレッドで走る」。相互作用の 90% が **Advertised(自律)** |
| [transport__tag-m3-1-validation](lit/transport__tag-m3-1-validation.md) | 検証とV&V・UQ #22 / 人間移動科学 #3 | **抄録のみ**(gov.uk の Table 2 逐語を引用経由。**PDF 119 頁は親が直読すること**) | **C8 計器盤の帯設計の直接材料**。Guideline 1=<700 veh/h は ±100・700-2,700 は **±15%**・>2,700 は ±400、いずれも **>85% のケース**。Guideline 2=**GEH<5 を >85%**。**「85% が GEH<5」は DMRB でなく TAG** |
| [transport__fhwa-toolbox-vol3-calibration](lit/transport__fhwa-toolbox-vol3-calibration.md) | 検証とV&V・UQ #22 | **実読**(サブ・FHWA-HOP-18-036 Chapter 5) | **「実測の自然変動を許容誤差にする」型の原典**。~2σ帯=cr(t)±1.96σ に **95%**・1σ帯に **2/3**+臨界区間・**BDAE**(代表日以外の日の平均絶対差の平均)・**BDSE ≤ (1/3)×BDAE 閾値**。**D1′(L423)の閾値根拠と同じ型** |
| [mobility__pseudo-pflow-2022](lit/mobility__pseudo-pflow-2022.md) | 人間移動科学 #3 / 検証とV&V #22 | **実読**(サブ・arXiv PDF を pymupdf 抽出・24 頁) | **1.3 億人合成人流・R²>0.5**。**Table 5 のカバレッジは東京 95/104/96/93・Kinki 97-113・East Suruga 83-102**。**東京 PT は行動モデルの生成に使った域**=93-104% を「合格ライン」に使うのは in-sample。外部検証は Kinki と East Suruga(通勤 R²<0.5・17% 過少) |
| [socialsim__voat-30run-benchmark-2508.21740](lit/socialsim__voat-30run-benchmark-2508.21740.md) | 計算社会科学 #25 / 検証とV&V #22 | **実読**(サブ・arXiv HTML v3・Table 6) | **「歪む場所の宣言」の手本**。**30 本の独立 30 日ラン vs 実 30 日窓 30 個・99% CI 重なりで合否**。合格=unique users/root posts/DAU。不合格=クラスタ係数 **0.017 vs 0.004(4.6×)**・コア割合 **19.6% vs 5.1%(3.8×)**・毒性 |
| [socialsim__gasim-2605.07692](lit/socialsim__gasim-2605.07692.md) | 認知科学 #12 / 自然言語処理 #27 | **抄録+結果値**(ACL 2026 Long pp.12510-12528) | **U1 記憶(L392)の速度根拠**。1 万体 × 30 step で**記憶想起 316.33 分 → 19.30 分(16.39×)**・全体 6.69→0.67 h(9.94×)。316 分は**LLM 多段想起**の時間でベクタ検索の時間ではない |
| [llmsim__ncp-bench-2608.08160](lit/llmsim__ncp-bench-2608.08160.md) | 計算社会科学 #25 / 自然言語処理 #27 | **抄録+結果節**(arXiv) | **L385 修正1 の定量根拠**。映画あらすじ由来 100 環境・**上限 100 ターン**。**40-68% のランが事実矛盾で終わる**・**GPT-5.2 でも 20 ターン後に無矛盾は 42%**。**「30ターンで無矛盾ほぼゼロ」は原典に無い** |
| [llmagent__skillsbench-2602.12670](lit/llmagent__skillsbench-2602.12670.md) | 自然言語処理 #27 | **抄録のみ**(v1 と現行版の両方) | **L385 修正2 の根拠**。**v1**: 86 タスク/11 領域/7 構成/7,308 軌跡・curated +16.2pp・**self-generated Skills は平均で効果ゼロ**。**現行版**: 87 タスク/8 領域/18 構成・**+16.6pp**・self-generated 条件を抄録から削除。**版の固定が必須** |
| [llmsim__orchestrated-reality-2606.16014](lit/llmsim__orchestrated-reality-2606.16014.md) | 計算社会科学 #25 / ゲームエンジン工学 #30 | **実読**(arXiv HTML 経由の逐語) | **L385「独立に三層へ到達」の 2 本目**。正準 JSON エンティティ木を単一オーケストレータが所有・遷移核=**PDVA(Plan-Diff-Validate-Apply)**・**スキーマ検証済み+内容ハッシュ付き JSON デルタ**をコミット。**自称 work in progress の CHI PLAY Companion '26 短報**(商用 WorldLines の付随論文) |
| [privacy__demontjoye2013-unique-in-the-crowd](lit/privacy__demontjoye2013-unique-in-the-crowd.md) | 研究倫理・情報法 #31 / 人間移動科学 #3 | **抄録+本文引用**(Sci Rep 3:1376・Nature は認証リダイレクトのため MIT DSpace 版も存在) | **L-REC の R5 再識別手順(L395)の出所**。150 万人・15 か月。**4 点で 95%・2 点で >50%** 一意・一意性は**解像度の 1/10 乗**でしか落ちない。アンテナ被覆 **都市 0.15 km²〜地方 15 km²** |
| [data__mcap-spec](lit/data__mcap-spec.md) | ソフトウェア工学 #29 | **実読**(mcap.dev/spec) | **L389 の `t_ns(uint64)` の型根拠**。Timestamp=「**uint64 nanoseconds since a user-understood epoch**」・Message は log_time/publish_time の 2 本・**Chunk Index** は全 Chunk に存在し時刻範囲シークを可能にする |
| [data__ieee1849-2023-xes](lit/data__ieee1849-2023-xes.md) | ソフトウェア工学 #29 | **実読**(xes-standard.org・規格本文は有料で未読) | **「コア最小+拡張で語彙を足す」の先行**。**1849-2023**(2023-08-09・2016 版を置換・2033 まで有効)。extension が「XES インスタンスの構造に意味を与える」・W3C XML Schema 2 本。**log>trace>event の 3 階層はこのページには無い** |
| [serving__vllm-prefix-caching](lit/serving__vllm-prefix-caching.md) | 自然言語処理 #27 / 計算機科学 #28 | **実読**(vLLM design doc) | **知覚契約 §5 prefix 規約(L433)と予算宣言(L403)の根拠**。「**We only cache full blocks**」+親ハッシュ連鎖=**固定節を先頭へ寄せる**が正しく導ける。**ブロック長 16 は既定値で仕様定数ではない**。`cache_salt` は先頭ブロックのハッシュに注入 |
| [serving__vllm-mrv2-2026-03](lit/serving__vllm-mrv2-2026-03.md) | 自然言語処理 #27 / 計算機科学 #28 | **抄録相当**(vLLM 公式ブログの逐語) | **L403/L464 の「二桁% 期待」の条件**。**16K→25K tok/s = +56.2%** は **Qwen3-0.6B × 1×GB200** のホスト側オーバーヘッド強調条件。**既定でなく実験的**(`VLLM_USE_V2_MODEL_RUNNER=1`・v0.17+・LoRA 等未対応) |
| [serving__vllm-batch-invariance](lit/serving__vllm-batch-invariance.md) | 計算機科学 #28 | **実読**(vLLM docs 2 ページ) | **B14(L467)の公式側**。`VLLM_BATCH_INVARIANT=1`・**CC ≥ 8.0**(A5000 可)・「**may impact performance**」(数値なし・**beta**)。既定では「vLLM does not guarantee the reproducibility of the results」 |
| [hardware__nvidia-cuda-gpus-cc](lit/hardware__nvidia-cuda-gpus-cc.md) | 計算機科学 #28 | **実読**(NVIDIA 公式 CUDA GPUs 表) | **batch1 §4 の穴を埋めた**。**RTX A5000 = CC 8.6**(A100=8.0・L40S/Ada=8.9)。FP8 演算の CC≥8.9 要件(batch1 #10)と合わせて「A5000 では INT8」が確定 |
| [license__autoawq-deprecated](lit/license__autoawq-deprecated.md) | 研究倫理・情報法 #31 / 計算機科学 #28 | **実読**(AutoAWQ repo + vLLM docs v0.18.0) | **L464 の 32B AWQ に効く**。AutoAWQ は **2025-05-11 にアーカイブ**・「officially deprecated」。vLLM 公式が **llm-compressor の AWQ レシピ**へ誘導。推論側の AWQ 形式サポートは継続 |
| [ecology__pom-rangeland-2014](lit/ecology__pom-rangeland-2014.md) | ABM方法論 #21 | **抄録のみ**(ScienceDirect 有料) | **運用8条③ hard filter の実証根拠**。*Ecological Modelling* 275:78-88・**10⁹ 組 → 11,316 組(0.001%)が 4 本の一般パターンを通過**。通過した**全**パラメータ群を後続解析に使う |
| [gamedev__cesium-ion-japan-3d-buildings](lit/gamedev__cesium-ion-japan-3d-buildings.md) | ゲームエンジン工学 #30 | **実読**(Cesium 公式) | **R15 第2段(L458)の材料**。**約 2,300 万棟**・MLIT **PLATEAU** CityGML 由来・**3D Tiles**・210 超の市区町村。地形は GSI 基盤地図情報。**ライセンス条項は無く帰属表示義務のみ**・公開日の記載も無し |
