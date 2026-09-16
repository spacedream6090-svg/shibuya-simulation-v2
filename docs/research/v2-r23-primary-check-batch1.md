# R-23 第1批: 出典URLゼロの答申(D等級33本)の一次確認

<!-- hdr:v1 -->
- **分野**: 検証とV&V・UQ #22 ほか横断(計算社会科学 #25 / ABM方法論 #21 / 認知科学 #12 / 研究倫理・情報法 #31 / ゲームエンジン工学 #30) | **重要度**: P1
- **一次確認**: **B** = サブが一次資料を実読(逐語つき)・**親未確認**。本書の逐語・URL・判定はすべて親の再確認を要する
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 対象: INDEX §1 の D等級 33 本のうち **P1 24 本**。第1批の方針=「決定台帳・設計書が実際に引いている答申」から先に一次確認する。
> 作業日 2026-09-16。答申本体・台帳は一切編集していない。

---

## §1 参照表(P1 24 本 × 設計書からの参照)

参照回数 = `docs/design/*.md` + `PENDING.md` + `IMPLEMENTED.md` + `STATUS.md` + `docs/*.md` における**ファイル名の出現回数**。

| 答申 | 参照回数 | どこから引かれているか(引かれている決定) | 第1批 |
|---|---|---|---|
| legal-licensing-deep-research | 5 | `docs/data-license-ledger.md` 冒頭(「法務答申の実装」=台帳そのものの根拠)・`v2-world-data-build-spec.md` §186(公開形態=ODbL継承判断)・`v2-ethics-safety-operations.md` | **入れた** |
| science-claims-research | 3 | `v2_significance.md` 序(「先行ゼロ表現を3件修正」)・`v2_draft_proposal.md` L44(新規性の正確な範囲) | **入れた** |
| engine-llm-boundary-research | 2 | `v2-world-process-design.md` L5(「根拠: 線引き答申=設計原則7本+16行マッピング」)→ D-R2-2・D-R2-3・世界過程 16 行表 | **入れた** |
| llm-serving-deep-research | 2 | `v2-bench-plan.md` L4(「根拠: サービング答申」)・`v2-budget-declaration.md` L6(名前呼び) → R16(艦隊構成)・D-26 | **入れた** |
| pattern-ledger-deep-research | 2 | `v2-pattern-ledger.md` L6・L10(「原資料: 答申U-D=stylized facts 44本+運用8条」) → U12 パターン台帳(Phase 0 ゲート)・強5本のうち A1/C1 | **入れた** |
| game-frontend-research | 1 | `v2-redesign.md` L453 = **DECIDED「R15 可視化」**(「既存答申(v2-game-frontend-research.md・親検収済み)の3段階案から」) | **入れた** |
| game-tech-import-research | 1 | `v2_significance.md` L8(参照5本の1本) | **入れた** |
| memory-retrieval-research | 1 | `v2_draft_proposal.md` L58(「記憶と想起=ハイブリッド案(c)」= U1・判断待ち) | **入れた** |
| benchmark-standards-research | 0 | 未参照(ただし `v2-deep-research-program.md` L30 が「ベンチマーク答申の5層構造」と本文で言及) | 外す |
| digital-twin-landscape-research | 0 | 未参照 | 外す |
| llm-knowledge-deep-research | 0 | 未参照 | 外す |
| llm-mobility-research | 0 | 未参照(**ただし下記の注**) | 外す |
| mobility-field-research | 0 | 未参照(**ただし下記の注**) | 外す |
| prediction-module-deep-research | 0 | 未参照 | 外す |
| small-scale-verification-research | 0 | 未参照 | 外す |
| boundary-deep-research | 0 | 未参照(境界の数値は `v2-boundary-economy-design.md` にあるが引用元名が書かれていない) | 外す |
| conversation-deep-research | 0 | 未参照(**ただし下記の注**) | 外す |
| coupled-adaptation-deep-research | 0 | 未参照(統合設計図 §1「適応3ループ 時定数1:5:25」が中身を使っている可能性) | 外す |
| economy-sfc-deep-research | 0 | 未参照(**ただし下記の注**) | 外す |
| institutions-deep-research | 0 | 未参照(**ただし下記の注**) | 外す |
| observation-projection-deep-research | 0 | 未参照(統合設計図 §1 に L-OBS/L-REC・推定器R0-R6 が載る) | 外す |
| parallel-execution-deep-research | 0 | 未参照 | 外す |
| persona-population-deep-research | 0 | 未参照 | 外す |
| precedent-system-deep-research | 0 | 未参照(`v2-science-claims-research.md` からのみ相互参照) | 外す |

**注(第1批の絞り込みの穴)**: `v2-architecture-roadmap.md` L39 は
「**背骨(35面が独立収束)**: 状態と集約はエンジン、意思決定と発話だけLLM(**経済・会話・人流・制度の4答申が同一分業に到達**)」
と書いている。これは CLAUDE.md §3 の第1行(v2 の背骨)そのものだが、指す4本は
economy-sfc / conversation / llm-mobility(または mobility-field)/ institutions = **いずれも D等級・ファイル名参照ゼロ**。
**ファイル名 grep では落ちるが、いま一番効いている答申はこの4本**。第2批の先頭に置くべき(§5)。

---

## §2 主張ごとの確認表

判定の語: **一致** / **数値不一致** / **出典が見つからない** / **主張が原典より強い**。
「原典の逐語」は 125 字以内。PDF は WebFetch 保存分をシステム python の `fitz` で本文抽出して読んだ。

### 2-1 engine-llm-boundary-research(→ `v2-world-process-design.md` 原則7本+16行表)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 1 | 「BYTESIZED32-SP(76,369遷移)=GPT-4は非自明な状態遷移で**精度59.9%止まり**・誤りは算術に集中(ACL 2024)」 | https://arxiv.org/html/2406.06485v1 | §2.2/Table 1「Total transitions 76,369」/§1「model accuracy does not exceed 59.9% for transitions in which a non-trivial change in the world state occurs」 | **一致** | 影響なし。補足: 内訳は action-driven 77.1% / environment-driven 49.7%(答申は未記載) |
| 2 | 「(唯一の実測アンカー=**OASIS 100万体1ステップ18h/A100×27**)→「裁定は初回のみ」(原則6)が計算上も必須」 | https://arxiv.org/html/2411.11581v4 | §4.1 Table 2「Hours per time step 18.0」「GPUs (A100) 27.0」(1M scale)。10K は 0.2 h / 2 GPU | **一致** | 影響なし(原則6=判例参照の計算根拠を支持) |
| 3 | 「OASISの行動空間は**21種**で実験毎に部分集合」 | https://arxiv.org/html/2411.11581v4 | §2.4「The action module enables 21 different types of interactions with the environment」 | **一致** | 影響なし |
| 4 | 「**EconAgent**: LLMが決めるのは**スカラー2つだけ**(就労傾向p^w・消費傾向p^c∈[0,1]**刻み0.02**)。生産・価格・賃金・税・金利・失業は全部方程式」 | https://arxiv.org/html/2310.10436v3 | Appendix A プロンプト「'work' (a value between 0 and 1 with intervals of 0.02, indicating the willingness or propensity to work)」。税 Eq.1-2・賃金 Eq.7・価格 Eq.8・金利 Eq.12 は式 | **一致** | 影響なし(原則4「量はスカラー」・16行表 行5/行6 を支持) |
| 5 | 「Concordia v2はEntity-Component化し、Engineが **next_acting/make_observation/resolve/終了判定の4役**」 | https://github.com/google-deepmind/concordia/blob/main/concordia/environment/README.md | 「Observing / Scheduling / Resolving / Terminating」。key methods = run_loop・next_acting・make_observation・resolve | **一致**(ただし **主張が原典より強い** 部分あり) | 影響なし。原典は「Termination criteria and specific turn-taking logic are meant to live in GM components rather than in the engine itself」=終了判定は engine の役でなく GM コンポーネント |

### 2-2 pattern-ledger-deep-research(→ `v2-pattern-ledger.md` = U12・Phase 0 ゲート)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 6 | 「**P03-05 会話グループサイズ**: 2人53.9%/3人26.9%/4人13.5%/**95%が4人以下・5人超は1-2%**(Dunbar+)」(= 台帳 **A1・強=hard filter**) | https://link.springer.com/article/10.1007/BF02734136 (Dunbar, Duncan & Nettle, Human Nature 6(1):67-78, 1995) | Table 1 Overall %: 2=53.9・3=26.9・4=13.5・5=4.7・6=0.7・7=0.3(Total groups 1057)/本文「approximately 95% of all cliques contained four or fewer individuals」 | **一致** | 影響なし。注記推奨: 53.9% は4標本合算の Overall %、「5人超」は表では 6人+7人=1.0%(本文は標本別に 0.5% / 2.4%)。判定関数は「同時会話クリーク」であって在席グループではない |
| 7 | 「**P28 カスケードの99%が1世代で終了・中央値1.3**(10億件・Goel/Watts)」(= 台帳 **C1・強=hard filter**) | https://pubsonline.informs.org/doi/10.1287/mnsc.2015.2158 (Goel, Anderson, Hofman & Watts, Management Science 62(1):180-196, 2016) | 「the average size of these diffusion trees ... is 1.3—meaning that for every ten introductions of content, there are on average three additional downstream adoptions」 | **数値不一致**(定義違い) | **値を直す必要**。1.3 は**平均(average)**であって中央値ではない。99% が size 1 なので**中央値は 1**。C1 は hard filter なので判定関数がそのまま誤る |
| 8 | 同上「99%が1世代で終了」「10億件」 | 同上 | 「the vast majority of cascades—over 99%—are tiny, and terminate within a single generation (Goel et al. 2012)」/「a billion diffusion events on Twitter」 | **一致**(帰属注意) | 影響なし。ただし 99% は本論文の自前測定でなく **Goel et al. 2012(EC'12)の引用**。本論文 p.9 の自前値は「about 99% of adoptions are accounted for either by the root nodes themselves or by the immediate followers of root nodes」=別の量 |
| 9 | 「**P24 交際・付き合いは1日わずか10分**」(= 台帳 **A4**・LLM過大の上界見張り) | https://www.stat.go.jp/data/shakai/2021/pdf/youyakua.pdf | 表1(男女・行動の種類別生活時間 2016/2021・週全体)「交際・付き合い 総数 0.17 → 0.10(-0.07)」男 0.15→0.08・女 0.19→0.12/本文「５年前に比べ…交際・付き合いの時間が７分の減少」 | **一致** | 影響なし(週全体・10歳以上・男女総数の総平均時間=0時間10分) |

### 2-3 llm-serving-deep-research(→ `v2-bench-plan.md`・R16 艦隊構成)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 10 | 「**FP8はCC≥8.9必須=A5000(Ampere CC8.6)ではW8A16に落ちて**高バッチの演算高速化が得られない」 | https://docs.vllm.ai/en/latest/features/quantization/llm_compressor/fp8/ | Note「FP8 computation is supported on NVIDIA GPUs with compute capability >= 8.9 (Ada Lovelace, Hopper, Blackwell).」「FP8 models will run on compute capability >= 7.5 (Turing) as weight-only W8A16, utilizing FP8 Marlin.」 | **一致** | 影響なし(`v2-bench-plan.md` L17「FP8演算不可→W8A8-INT8が本命」を支持)。ただし **A5000=CC 8.6 は NVIDIA 側の別事実で本批では未確認**(§4) |

### 2-4 game-frontend-research(→ **DECIDED R15 可視化**)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 11 | 「**deck.gl**: 公式性能文書でScatterplotLayer等は**約100万点まで60FPS**(1000万点で10-20FPS)・picking 16M件/レイヤ」 | https://deck.gl/docs/developer-guide/performance | 「renders fluidly at 60 FPS during pan and zoom operations up to about 1M (one million) data items」/「(10-20FPS) when the data sets approach 10M items」/「The picking system can only distinguish between 16M items per layer.」 | **一致** | 影響なし(R15 初回=deck.gl 1枚で40万体 の判断を支持)。注記推奨: 公式の実測機は「2015 dual-GPU MacBook Pros」 |
| 12 | 「**UE5 City Sample**: **歩行者35,000人**がMass AI+Naniteの**公開実績上限**」 | https://dev.epicgames.com/documentation/en-us/unreal-engine/city-sample-project-unreal-engine-demonstration / https://www.unrealengine.com/en-US/blog/introducing-the-matrix-awakens-an-unreal-engine-5-experience | City Sample 公式ドキュメントに群衆の**体数の記載なし**。Matrix Awakens 公式ブログは 45,073 parked cars・27,848 lamp posts 等を具体数で挙げるが、群衆は "thousands of MetaHuman agents" 止まり。UE5.0 リリースノートは MassEntity を "tens of thousands of AI agents" と記述 | **出典が見つからない** | **値を直す必要**。残務台帳 R-5 が「公開実績上限との記載」として引いている数値の公式根拠が見つからない。GDC/Epic 講演の一次当たりが要る(§4) |
| 13 | 「**見た目の忠実度は信頼を生まない(国交省実測)**: PLATEAU uc25-05 で結果の信憑性を高評価した自治体職員は**11人中4人のみ**」 | https://www.mlit.go.jp/plateau/use-case/uc25-05/ | 「シミュレーション結果の定量的な再現性に対する納得度について、アンケートでは5段階中4以上の評価は11名中4名にとどまり、ユーザーの感覚や実態との乖離を埋める必要性が浮き彫りとなった」 | **一致**(数値)+ **主張が原典より強い**(見出し) | 影響なし(DECIDED R15 の結論=GlassBox規律+追跡可能性 は原文と整合)。原文の設問は「**定量的な再現性に対する納得度**」であって「見た目の忠実度」ではない。答申見出しは言い換えが一段強い |

### 2-5 memory-retrieval-research(→ `v2_draft_proposal.md` L58 = U1 記憶案(c)・判断待ち)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 14 | 「Generative Agents(25体): memory stream全記録+**recency(0.995指数減衰)**」 | https://ar5iv.labs.arxiv.org/html/2304.03442 | §4.1「Our decay factor is 0.995.」(recency は最終想起からのゲーム内時間の指数減衰・3成分は min-max 正規化し α は全て 1) | **一致** | 影響なし |
| 15 | 「**reflection=importance合計150超で発火**(実測1日2-3回)」 | 同上 | §4.2「exceeds a threshold (150 in our implementation)」/「In practice, our agents reflected roughly two or three times a day.」 | **一致** | 影響なし |
| 16 | 「**25体×2日で数千ドル**≈$40/体日→40万体では原理的に不可」 | 同上 | §8.2「costing thousands of dollars in token credits and taking multiple days to complete」(モデルは gpt-3.5-turbo) | **一致**(ただし $40/体日 は答申側の割り算=**原典に無い外挿**) | 影響なし |
| 17 | 「日本語埋め込み: **Ruri-small(68M・768次元)がJMTEB 71.53でmE5-large(70.90)超**。mE5-small(384次元)=67.71」 | https://huggingface.co/cl-nagoya/ruri-small | モデルカードのベンチ表: Ruri-Small **71.53** / intfloat/multilingual-e5-large **71.65** / intfloat/multilingual-e5-small **69.52**(パラメータ 68M・次元 768 は一致) | **数値不一致・主張が反転** | **値を直す必要**。71.53 < 71.65 なので「mE5-large 超」は成立しない。U1 は判断待ちなので決定は未拘束だが、埋め込みモデル選定の根拠は消える |
| 18 | 「**Lally+2010実測**: 習慣の自動化は漸近95%まで**中央値66日**(18-254日)」 | https://onlinelibrary.wiley.com/doi/abs/10.1002/ejsp.674 (Lally et al., Eur J Soc Psychol 40(6):998-1009, 2010) | 抄録「The time it took participants to reach 95% of their asymptote of automaticity ranged from 18 to 254 days」。「median of 66 days (range: 18–254 days)」は追試側(Keller et al. 2021, Br J Health Psychol)の逐語 | **一致**(条件つき) | 影響なし。**直読は 403 で不可**(§4)。母集団は「漸近モデルが良好に当てはまった 39/82 人」= 全被験者の中央値ではない |

### 2-6 science-claims-research(→ `v2_significance.md` 序「3件を修正する」・`v2_draft_proposal.md` L44)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 19 | 「GM裁定=**Law in Silico**(2510.24442・TRPG型GM・罪刑法定主義適用・**ミクロ4体/マクロ1万体単発**)が先行」 | https://arxiv.org/html/2510.24442v1 | §4.1「We sample 10,000 agents and evaluate each in a single-shot setting using temperature-1 decoding.」/§4.2 = 1社+3労働者(Appendix D `NUM_LABORERS = 3`) | **一致** | 影響なし |
| 20 | 「**[2026-09-01訂正: 本文HTML照会でprecedent等の語は一度も出現せず=同論文は判例概念を丸ごと持たない**」(答申側の自己訂正) | 同上 | "precedent"・"case law" ともに本文中に出現せず。**future work / limitations の専用節も存在しない**(結論 §5 に記載なし) | **一致**(訂正が正しい) | **値を直す必要**。`v2_significance.md` は **L16-17「同論文が future work に明記した未実装領域」・L23「先行のfuture work領域」・L151「先行のfuture work領域」** のまま=原典に無い記述。`v2_draft_proposal.md` L44 は訂正済みで、**設計書2本の間で不整合** |
| 21 | 「**Clauset+**(SIAM Review)=べき則検出は裾サンプル**n≥50**が経験則」 | https://ar5iv.labs.arxiv.org/html/0706.1062 | §3.2「Our experience suggests that n≳50 is a reasonable rule of thumb for extracting reliable parameter estimates.」 | **一致** | 影響なし。補足: §3.4 は x_min 推定側に「good results can be achieved provided we have about 1000 or more observations in this part of the distribution」=規模Nの正当化に使うならこちらの方が効く |
| 22 | 「**OASIS=100体ではherd効果が出ず、10,000体で明示的に出現**=規模を上げないと現象そのものが発生しない」 | https://arxiv.org/html/2411.11581v4 | §3.4.2「when the number of agents was small, there appeared to be no herd effect」/「We then increased the number of agents from 100 to 10,000, and found that the agents began to exhibit explicit herd effect.」 | **一致** | 影響なし(効果量は Fig.8 の図のみで数表なし) |
| 23 | 「**PIMMUR監査**(2509.18052)=**39研究の89.7%**が妥当性原則違反・代表5実験の再現で集合現象が消失/反転・**LLMの50.8%**が実験下にあることを看破・**61%**のプロンプトが結果を先決め」 | https://arxiv.org/abs/2509.18052 | 現行 v4(2026-09-10 改訂)抄録: 「576 studies reported in 350 recent papers」/「65.2% of cases」(実験だと看破)/「50.6% of prompts imposed constraints that pre-determined the outcome」/再現は5実験。**89.7% は現行版に無い** | **数値不一致**(版差の可能性) | **値を直す必要**。PIMMUR は PENDING F-8(未決・ユーザー判断待ち)なので決定は未拘束。母数が 39→576 に変わっているので、採用時は版を固定して引き直す |

### 2-7 legal-licensing-deep-research(→ `docs/data-license-ledger.md`・`v2-world-data-build-spec.md` §186)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 24 | 「**Produced Workにしてもshare-alike回避にならない**(4.6でDerivative DB別途公開義務が残る)」 | https://opendatacommons.org/licenses/odbl/1-0/ | §4.6「If You Publicly Use a Derivative Database or a Produced Work from a Derivative Database, You must also offer…」/§4.4(c)「Publicly Used ... if a Produced Work created from the Derivative Database is Publicly Used」 | **一致** | 影響なし(台帳の設計原則②「出力スキーマからOSM生値を排除」を支持)。補足: §4.5(b) により**原 Database から直接**作った Produced Work は Derivative Database を生じない |
| 25 | 「**Qwen3全般=Apache 2.0**」(主軸モデルの選定根拠) | https://huggingface.co/Qwen/Qwen3-8B | モデルカード メタデータ「License: apache-2.0」 | **一致**(範囲は限定) | 影響なし。ただし本批で確認したのは **8B の1点のみ**=「全般」は未検証(§4) |
| 26 | 「**PPC Q1-17**=統計情報は個人情報に非該当 →統計から生成した架空エージェントは個人情報に非該当と整理できる可能性が高い」 | https://www.ppc.go.jp/all_faq_index/faq1-q1-17/ | Ａ１-17「特定の個人との対応関係が排斥されている限りにおいては、「個人に関する情報」に該当するものではないため、「個人情報」にも該当しないと考えられます。」 | **一致** | 影響なし(台帳 `data/persona_pool_v2` 行の根拠)。答申自身が「[推測]」と「合成データの公的整理は未発見」を明記しており、過剰一般化はしていない |

### 2-8 game-tech-import-research(→ `v2_significance.md` L8)

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 27 | 「**Unity DOTS 16KBチャンク**」(輸入#2 アーキタイプ/チャンクSoA の根拠) | https://docs.unity3d.com/Packages/com.unity.entities@1.3/manual/concepts-archetypes.html | 「Each chunk consists of 16 KiB and the number of entities that they can store depends on the number and size of the components」 | **一致** | 影響なし(単位は KB でなく **KiB**) |
| 28 | 「**Replication Graph**(グリッドで総当たり関連性評価を消す・**Fortnite 100接続×5万アクタ実績**)」 | https://dev.epicgames.com/documentation/en-us/unreal-engine/replication-graph-in-unreal-engine | 「starts each game with 100 connected players and about 50,000 replicated Actors」/「The Replication Graph eliminates the need for Actors to evaluate each connected client individually」 | **一致** | 影響なし(知覚の配送=Replication Graph型5ノード の由来は UGC 答申側=B等級) |

### 判定の内訳

| 判定 | 件数 |
|---|---|
| 一致 | **22**(うち条件つき・注記推奨 6) |
| 数値不一致 | **3**(#7 Goel「中央値1.3」/#17 Ruri JMTEB/#23 PIMMUR) |
| 出典が見つからない | **1**(#12 UE5 City Sample 35,000人) |
| 主張が原典より強い | **2**(#5 Concordia「Engineの4役」に終了判定を含める/#13 uc25-05 の「見た目の忠実度」見出し) |
| 合計 | 28(#5・#13 は一致と重複計上) |

---

## §3 決定への影響の要約

**決定台帳の DECIDED 行そのものを撤回・再検討すべき件は、本批では見つからなかった。**
確認した 28 主張のうち 22 が原典と一致し、DECIDED R15(可視化)・D-R2-2/D-R2-3(世界過程の線引き)・R16(艦隊)・データライセンス台帳の根拠は、
少なくとも今回照合した範囲では原典で裏が取れた。

一方、**値を直す必要がある件が 4 つ**ある。うち 1 つは**強パターン(hard filter)に直接載っている**。

| 件 | 名指し | いま何が起きているか | 推奨(決定は親とユーザー) |
|---|---|---|---|
| **A** | **パターン台帳 C1**(`v2-pattern-ledger.md` 階層C・**強○=hard filter**・判定型 band) | 「P28 カスケードの99%が1世代で終了・**中央値1.3**」。原典は **平均(average)1.3** であって中央値ではなく、99% が size 1 である以上 **中央値は 1**。判定関数を「中央値1.3」で実装すると現実側の値が誤る | C1 の照合値を **①平均カスケードサイズ ≒1.3 ②1世代終了率 >99%** の 2 本立てに書き直す。強パターンは Phase 2 ゲートの前提条件なので、判定関数のハッシュ固定(運用8条⑥)より前に直す |
| **B** | **`v2_significance.md` L16-17・L23・L151** | 「判例としての結晶化ループは同論文(Law in Silico)が **future work に明記**した未実装領域」。原典に future work / limitations の節は無く、precedent・case law の語も出現しない。**`v2_draft_proposal.md` L44 は 09-01 に訂正済みで、設計書2本が不整合** | 「future work に明記」を「同論文は判例概念を持たない(成文法照合の逐次判定)=空白はより強い形で成立」に置換。空白主張自体は**弱まらず強まる**ので、新規性の主張は維持できる |
| **C** | **残務 R-5 / `v2-game-frontend-research.md`**(DECIDED R15 の長期段の材料) | 「UE5 City Sample 歩行者 35,000人が**公開実績上限**」の数値が Epic 公式(City Sample ドキュメント・Matrix Awakens ブログ・UE5.0 リリースノート)に見つからない。公式は "thousands of MetaHuman agents" / "tens of thousands of AI agents" 止まり | 「公開実績上限」の表現を落とし、R-5 の再確認項目に「Epic の GDC/Talks を一次で当たる」を残す。**R15 の初回範囲(deck.gl・2D)は 35,000 に依存していないので決定は動かない** |
| **D** | **`v2-memory-retrieval-research.md` の Ruri 行 / PENDING F-8 の PIMMUR 行** | Ruri-small 71.53 は mE5-large **71.65** を超えていない(答申は 70.90 と記載)。PIMMUR は現行 v4 で母数が 39→576 研究・350 論文、数値も 65.2%/50.6% に変わり 89.7% は現行版に無い | どちらも**未決事項の材料**(U1 記憶案・F-8)なので決定は未拘束。採用する段で版を固定して引き直す。Ruri は「mE5-large 超」という優位主張を落とし、「同等の平均スコアを 1/8 のパラメータで」に直す |

**第1批の結論**: 33 本を「使えない」と一括りにする必要はない。今回の 8 本については、**決定を駆動している主張の大半は原典で裏が取れる**。
ただし **1 本(pattern-ledger)の強パターンに定義の取り違えがあり**、**1 本(science-claims)の訂正が設計書へ伝播していない**。
この 2 つは中身の誤りというより **「答申→設計書への写しの事故」** で、D 等級かどうかとは別の検査(写し検査)が要ることを示している。

---

## §4 空欄(見つからなかった・読めなかった・上限に当たった)

### 一次資料に当たれなかった主張(第1批の対象答申の中)

| 答申 | 主張 | 状態 |
|---|---|---|
| pattern-ledger | **P01 対面接触時間のべき則**(指数-2前後・平均46秒・SocioPatterns 4現場)= 台帳 A2 | 未確認(時間切れ) |
| pattern-ledger | **P36 渋谷スクランブル実測**(平日26万/休日39万人/日・1サイクル最大3,000人) | 未確認。台帳では D 階層に入っていない(D1′/D4′ に差し替わっている)ため優先度は下がるが、答申では ◎ 印 |
| pattern-ledger | **POM の実録**(半乾燥放牧地 10^9通り→11,316組 0.001%・アボカドFSPM 10,000→22組・Wang 2018 の台帳形式 verification 7+validation 9) | 未確認。運用8条の出所なので第2批の先頭候補 |
| pattern-ledger | 「明示的POM研究13件で概ね1-5本」「ABCの次元の呪い(Blum 2013)」「Abramowitz 2019」 | 未確認 |
| llm-serving | **Prefix caching=16トークン単位ブロック・完全一致のみ**(v2 の「固定節を先頭へ寄せる」設計制約の根拠) | 未確認 |
| llm-serving | **Model Runner V2(2026-03)= 小モデル×高リクエストで +56%**(16K→25K tok/s)・**Sleep mode 切替 0.26-6 秒**・`VLLM_BATCH_INVARIANT=1` | 未確認 |
| llm-serving | **A5000 の compute capability = 8.6**(#10 の結論はこの事実に依存) | 未確認(NVIDIA 公式の CUDA GPUs 表を当たる必要) |
| legal-licensing | **ODPT のライセンス内訳**(基本165/CC BY 92/チャレンジ限定73/PDL 12/CC0 3・商用なら107件) | 未確認(ODPT は登録が要る) |
| legal-licensing | **Qwen2.5-3B=非商用・Qwen2.5-72B=独自商用・Llama 3.1 で「出力で他モデルを訓練するな」が削除・Gemma PUP の自動意思決定制限・Swallow の二重ライセンス** | 未確認(Qwen3-8B の 1 点のみ確認) |
| science-claims | **Light Society(10億体)・GenWorld(196,608体・東広島市)・CityReal(3,000体)・AgentTorch 840万体** の規模主張 | 未確認。「4条件同時成立の空白」の土台なので第2批の対象 |
| science-claims | **Ashokkumar+(Nature 2026)= 70事前登録実験469効果で r=0.85** / **Barrie&Törnberg(2505.23796)** | 未確認 |
| memory-retrieval | 「**1万体超で per-agent embedding 検索を採用した公表例はゼロ**」(=不在の主張。反証探索が要る) | 未確認 |
| game-tech-import | Fortnite 同時 12.3M・AC Unity 群衆・Hitman Absolution 1200体・Quake3 32スナップショットリング | 未確認 |

### 読めなかった / 上限に当たったもの

- **Wiley(Lally 2010 原典)= HTTP 403**。抄録の逐語は検索経由で取得し、「median 66 days」は追試(Keller 2021)の逐語で代替した。**親は原典 PDF で median / mean の語を確認すること**。
- **出版社版が有料の 2 本**: Dunbar 1995(Human Nature)は著者公開 PDF、Goel 2016(Management Science)は著者機関公開 PDF を読んだ。**逐語はいずれも published 版のページ体裁(running head 付き)**だが、親は出版社版で再確認するのが望ましい。Goel は preprint 版が **1.4** と書いており、published 版は **1.3**。
- **Concordia の `engine.py` ソース直読に失敗**(raw パスの推測が 404、`tree` ページも 404)。`concordia/environment/README.md` の記述で代替した。
- arXiv の抄録ページだけでは数値が取れず、`arxiv.org/html/...` と `ar5iv.labs.arxiv.org/html/...` に切り替えて取得した(2006-2007 年の論文は ar5iv のみ)。

---

## §5 第2批への引き継ぎ

### 5-1 第2批の対象(優先順)

1. **「ファイル名では引かれていないが、いま一番効いている4本」**: economy-sfc / conversation / llm-mobility(または mobility-field)/ institutions。
   `v2-architecture-roadmap.md` L39 が「**経済・会話・人流・制度の4答申が同一分業に到達**」と書き、これが **CLAUDE.md §3 の第1行(v2 の背骨)**になっている。
   **ファイル名 grep では 0 件なので第1批の絞り込みから漏れた**。確認すべき主張=「4本が独立に同じ分業へ収束した」という**収束の事実そのもの**(各答申がどの先行研究を根拠にしているか)。
   → **第2批はここから始めるべき**。
2. **benchmark-standards-research**: `v2-deep-research-program.md` が「ベンチマーク答申の5層構造」を本文で参照。C8 の忠実度計器盤が到達したら効く。
3. **observation-projection-deep-research**: 統合設計図 §1 の「L-OBS→L-REC・filter∘quantize∘fold・7チャネル・推定器R0-R6」の出所。U4 採否の材料。
4. **coupled-adaptation-deep-research**: 統合設計図 §1 の「記憶:習慣:判例=時定数1:5:25」の出所。D-68 経路3 の設計に触る。
5. **precedent-system-deep-research**: 第3陣「制度の創発」の前身。science-claims の 09-01 訂正(#20)の詳細がここに書かれているので、**§3-B の訂正文を作る時に必ず読む**。
6. **parallel-execution-deep-research**(U9・id順バイアス=D-31 に効く)・**persona-population-deep-research**・**boundary-deep-research**。

### 5-2 参照されていない答申(16本)の扱いの案

- **案(a) いま触らない**: ファイル名でも本文でも引かれていないものは「決定を駆動していない」ので、**使う時に一次確認する**規律(INDEX §4)で足りる。INDEX に「未参照」印を足すだけにする。
- **案(b) 内容 grep を1回だけ回す**: 各答申の**特徴的な数値・固有名詞**(例: 「1:5:25」「R0-R6」「21種」)を設計書側に grep して、**名前なしで中身だけ入っている**ものを洗い出す。
  第1批で §5-1-1 の 4 本を取りこぼした原因がこれなので、**案(b) を推奨**。1 時間程度で終わり、第2批の対象がはっきりする。
- **案(c)** P2 9 本は最後(いずれも決定に触れていない)。

### 5-3 第1批で見つかった「検査の型」の提案(リサーチでなく運用)

本批の最大の発見は、**中身の誤りより「答申→設計書への写しの事故」の方が多かった**ことである(§3-A の中央値/平均、§3-B の訂正未伝播)。
D 等級かどうかとは独立の検査として、次の 2 つが要る(記憶ノート「繋ぎ expedient の置換忘れ検査」と同型):

- **写し検査**: 設計書に載っている数値を答申へ、答申の数値を原典へ、**2 段で突き合わせる**。とくに **強パターン(hard filter)** と **DECIDED 行の括弧内の数値**。
- **訂正の伝播検査**: 答申に「訂正」「[2026-xx-xx訂正」が入ったら、その答申を引いている設計書を grep して同じ訂正が入っているかを見る。
  今回の §3-B は `v2_draft_proposal.md` だけ直って `v2_significance.md` が残った例。
