# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **10 / 10**
> 第1〜第250(2026-09-01〜09-22)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第251 サーバー運用の知見を実装に織り込む形でまとめる(2026-09-22 夜)

- **依頼**(ユーザー): 「(c) 当面は実 LLM を止める方針で行く。未踏は別チャットで壁打ち中なので保留。**サーバーを使用する中で気づいたことをまとめてほしい**。その記録を参照することで、実機で検証するときとコードを書いているときのギャップを減らしたい」。
- **成果**: [docs/ops/v2-server-lessons.md](../ops/v2-server-lessons.md)(187 行)。§1 ギャップが出た 6 か所(G1 計器の穴・G2 律速は規模で入れ替わる・G3 上限が結果を作る・G4 mock と実 LLM・G5 資産のゲート・G6 配備)/ §2 計器の穴 4 件 / §3 律速(5,000 体=エンジン 1.23 s/tick vs 39 万体=艦隊 84%・繰り延べの真因は `queue_capacity` 1,792)/ §4 予算が結果を作る(AB8 の表)/ §5 mock と実 LLM の差(書式 18.4%・会話ゼロ・説明語の写り・few-shot 47%)/ §6 LLM が書いた資産(W17 v2 の 2.01 本/日)/ §7 配備 10 項(**`src/` が `docs/` を実行時に読む**・データはリンク・Python 3.10・tmux インライン・pkill 自殺・パスのマスク)/ §8 事故の型 5 件 / §9 チェックリスト(実装前・回す前・回した後)/ §10 再始動手順。
- **出どころ**: すべて自分たちの実測(C6/C7/C8 の受入報告・親報告・devlog)。一般論は書いていない。
- **同時に**: devlog 第241〜250 を圧縮(カウンタ 0→この回で 1/10)。
- **次**: 未踏の要素が .md で来たら起草。それまでは (c) の範囲=モック・実装・文書(記憶 第1段・PENDING 掃除・R-23 残 15・W6 再生成の判断)。

## 第252 v1 の教訓を棚卸しして §11 に追加(2026-09-22 夜)

- **依頼**(ユーザー): 「v1 で気づいたことはないの?」=第251 の知見まとめが v2 のランだけで閉じていた指摘。
- **実施**: 参照専用リポ `shibuya-simulation` の `docs/log/devlog.md`(2,017 行)・`devlog-compressed.md` を実読(記憶で書かない=§5)。[v2-server-lessons.md](../ops/v2-server-lessons.md) に **§11**(63 行)を追加し、ヘッダの出どころを「§1〜10=v2・§11=v1」に、§9 チェックリストに 5 行を足した。
- **§11 の中身**: 11-1 再開と checkpoint(未保存状態 15 件+5 族・再開で二重発火 29→44・ウォームキャッシュ消失で呼数と行動が変わる・日中 flush で未走査区間が永久消失・正常終了ランへの再開で日次締め二重・受入 `resume==straight`)/ 11-2 状態の成長で死ぬ(SNS 推薦の二乗爆発で step 95 に 10 時間/step・finalize 一括 concat 42.7 GB で「書き終わり」に落ちる・beliefs 4.2〜6.4 TiB・RAM 13.6 倍・性能の誤帰属・**壁は LLM でなく解析と RAM**)/ 11-3 1 呼のハードデッドライン欠落(1 呼 1h47m 張り付き・ソケット timeout は無通信しか測れない)と見張りが健全ランを 2 回殺した話 / 11-4 **mock が `where` を返さないためクラッシュが完全に潜在化**していた実例 / 11-5 「直線移動」の正体はログが最終座標のみ=記録の穴 / 11-6 層別クォータ・データの保持期限・サブ同時死・YAML 重複キー。
- **露呈(親の確認)**: v2 のランは**すべて 1 日**で、**再開の実装がどこにも無い**(`manifest/schema.py` に `parent_run` の欄だけ)。一方 記憶の合格線 M15 は「複数日ランが前提」。→ **新規 D-102**(親推奨 (a)=複数日の前に再開の口を設計し `resume==straight` を最初の受入条件にする。**実 LLM が無くてもモックで着手できる**)。
- **次**: D-102 の判断。未踏の要素 .md が来たら起草。

## 第253 BERT 系 / Open-Jev の調査(2026-09-23)

- **依頼**(ユーザー): 「BERT 系 / Open-Jev の調査をしてほしい」。
- **分担**: 閉じた出力の判断器の系譜(Q1〜Q4)= サブ Opus 5 の答申 R-38 / **Jev・Open-Jev の実在確認 = 親**(存在しないものをサブに探させると捏造の危険があるため)。
- **Open-Jev(親の一次読み・[ノート](../research/v2-openjev-note.md)・等級 A)**: **実在する**。`razorback16/openjev`・Apache-2.0・**TypeSafe とは無関係の独立実装**(README に明記)。土台は Google の拡散型 **DiffusionGemma 26B-A4B**(Apache-2.0・総 25.2B/活性 3.8B・canvas 256・最大 48 denoising steps)。**v2 が採らない 3 理由**=① vLLM 経路は 24 GB 以上が要る(手元は RTX 5070 12 GB)② 精度の数値が無く、素の DiffusionGemma は自己回帰版 Gemma より軒並み低い(MMLU Pro 77.6 vs 82.6)③ 決定論の保証が無い(エントロピー 0.1 超で最大 4 回読み直して平均)。`confidence` は 1−H(p)/ln K の計算式で **RLCD の較正ではない**。**注意**: Open-Jev が拡散モデルなのは **Jev が拡散モデルである証拠ではない**(TypeSafe 公式は "parallel sampler" としか書かない)。
- **R-38(サブ・等級 B・原典 18 群)+親検収 4 件**: ① **vLLM 公式 FAQ に逐語「vLLM does not guarantee stable log probabilities (logprobs)」**(親確認)=**logprob 方式は v2 の bit 一致の受入と衝突**(**→ 第254 で訂正**: v2 の構成では衝突しない) ② 自己申告 confidence での振り分けは原典で否定(Xiong ICLR2024・ECE×100 が GPT-4 でも 18.0)・効くのは別学習のスコアラ(FrugalGPT) ③ **GenWorld(arXiv:2606.27650・日本の東広島・196,608 体)** が教師 Gemma 3 27B を **lookup 表にコンパイル**し **CPU で 1.85M queries/s = 0.54 μs/件**(親が本文逐語確認・端から端の高速化は未報告) ④ 日本語ゼロショットは実在(`Formzu/bert-base-japanese-jsnli`・JSNLI 0.9288・親確認)。**R-39 の「先行なし」は狭める**=毎決定の蒸留代理は在る/実行時の学習ルータは無い。
- **親推奨の更新(D-101)**: 判断層の第一候補を **蒸留 lookup 表(GenWorld 方式)**へ。**GPU が要らない・完全に決定論・先行が同条件・教師は既存テープで足りる見込み**。次の一歩は「テープ 10 本から (文脈キー→行動分布) を作り被覆率と鋭さを測る」下見(GPU 不要)。
- **未確認**: Light Society の routing policies と macro F1(本文・親未確認)・`akiFQC` の JNLI 0.914(HF が 401)。
- **次**: D-101 の判断(下見に進むか)。

## 第254 ユーザー指示「計算資源は設計判断の軸にしない」+親の訂正(2026-09-23)

- **依頼**(ユーザー・逐語要旨): 「GPU を使用できるかどうかは構築に関係ない。妥協は決してしてはいけないし、最適な実装を探っていくべき。計算資源は僕がどうにかするから、完成度・精度・スピードを上げることだけに集中してほしい。決して妥協しないように。」
- **撤回**: 第253 の D-101 親推奨(第一候補=蒸留 lookup 表・理由の筆頭「GPU が要らない」)と、R-38 サブへ渡した「RTX 5070 12 GB」の必須評価軸。資源の要件(VRAM・GPU 時間)は事実として添えるだけにする。Open-Jev の「採らない理由 1(手元に載らない)」も撤回(理由 2・3 は残る)。
- **親の訂正(結論を変える)**: 第253 ①「logprob 方式は bit 一致の受入と衝突」は**誤り**。vLLM FAQ の非保証は既定モードの話。v2 の艦隊は `VLLM_BATCH_INVARIANT=1` で起動し(検証ランは manifest 規則 (c) で必須)、[B14](../bench/b14_batch_invariance/README.md)(09-07)で **logprobs 32/32 一致(OFF 0/32)**・T6 で応答 833/833 一致を実測済み。AB8 ×1 と AB6b s1 の bit 一致(第247)とも整合。既存ベンチの確認を怠った §2-4 違反。伝播: PENDING D-101・STATUS・R-38 親検収・Open-Jev ノート §1/§5・build_index・INDEX・backlog・devlog 第253。
- **親推奨(再・精度/完成度/スピードだけで順位)**: 第一候補 **(G) 自前艦隊の logprob 判断**(詳説 §2-j の既定どおり・忠実度の上限・決定論は実測済み)/ 第二 **(F/I/K) (G) から蒸留した学生**(入力は同じ文脈テキスト=個体差を保つ・速度の器)/ **(J) lookup 表は学生の最低容量の基線** / (C/D) NLI は候補から外す / Jev・Open-Jev は測るなら腕。**論点**: 教師/思考層のモデル格上げ(8B INT8 は 7×A5000 由来=決定項)・学生の学習データ(テープは prompt_hash+共有ブロック+応答 1 標本で**体ごとの本文は持たない**→再生で復元・分布は教師の再問い合わせが要る=第253 の「テープで足りる」を条件つきに訂正)・surface form と位置バイアス。
- **D-99 への含意**: 上限は機構(憲法1 打ち切り禁止)で置き、資源をそれに合わせる=全規模で「起床要求は全部応じる(繰り延べ 0)」を目標に、L4 は監査線へ。39 万体の無制限は AB8 の 15.46 呼/体/日から外挿で約 6.0M 呼/日・7×A5000(78 応答/s)で約 21.5 h(要実測)。
- **メモリ**: `compute-not-a-design-axis`(feedback)を新設・`server-gone-2026-09-22` の How to apply を従わせた。
- **次**: 判断待ち=(1) 教師/思考層のモデル格上げの可否 (2) 次の一歩(テープ再生から教師データを抽出して J 基線を測る=抽出口の実装が要るので先に聞く / 設計アジェンダ J1〜J10 / AB9 の資源目安)。

## 第255 認知・社会アーキテクチャ議事録の監査(2026-09-23)

- **依頼**(ユーザー): 別チャット(Fable 5.1)の議事録(54 節・System 1/Jev/System 2・知覚・記憶・社会・時間・同時性・検証)を「v2 に組み込む妥当性と実装方法をあらゆる観点から分析し、必要ならリサーチし、Fable 5.1 で検証した内容をもう一度監査」。サブ可。
- **分担**: 親 = 決定台帳・契約書・認知設計書・記憶/C10 アジェンダ・予算書の実読と監査本文 / Explore サブ = `src/` の実装の現在地 12 項(file:line)/ 研究サブ Opus 5 ×2 = R-41(個体側の先行: 二重過程・BDI 再考・ACT-R/Soar のコンパイル・CoALA/PIANO・割り込み・注意/LOD・他者予測・Agent LOD)・R-42(社会側・方法論側: 更新順序・群・規範・組織・伝播/信頼・創発の測り方・検証 3 層・ablation 行列)。
- **成果**: [docs/design/v2-minutes-audit-2026-09-23.md](../design/v2-minutes-audit-2026-09-23.md)。**結論**: ① 議事録の骨格は決定台帳の認知 3 層(案B′・08-28/09-07 決定)の再導出=System 1 = T0+T1 / 再考(「System 1.5」「Jev」)= T1→T2 昇格(S(e) 式は議事録の E 式と同じ)/ System 2 = T2。原則 A/C/G/H/I/K は実装済み(G/H は L1 のみ)。② 新規 9 点。高価値 3 = 予測状態+予測誤差(S(e) の surprise の機構化・門番の実体)・経験ログ(D-101 の学生の教師データ)・鮮度検査。③ 衝突 3 = 会話の意味を System 1 が決める(憲法 3・09-11 選好)/ マイクロ行動は宣言解像度の外(憲法 4・歩行者データ無し=資源の理由ではない)/ Jev を層名に使う。④ 数値はすべて根拠なし → 台帳の出典つきの値で置換。⑤ 検証は方法論と整合・H2 は照合データ無し。
- **Explore で確定した実装の現在地**(表 1-1・§1-3 に file:line): 全呼 L1(レーン選択なし・T2 昇格なし・縮退は計数のみ)・記憶/関係/群/信念 0・社会系チャネル 3 本(知人・被注視・傍受)no-op・人どうしの知覚は同セル距離順 k=3/2/1・組織は雇用主表のみ(権限検査は開閉店 1 か所・担当は丸振り expedient)・既定移動は 1 tick=1 ノード跳び・発話本文は保存されない・状態の追加口は `Registry.declare`+`growth_decl`。→ 組み込みは「採るか」でなく「実装の順序」。
- **台帳**: D-103(語彙対応表・推奨 (a))・D-104(予測状態+経験ログ・推奨 (a) モック着手)・D-105(会話の意味は LLM・推奨 (a))・D-106(マイクロ層はデータ後・推奨 (a))・D-107(群・規範・組織は計器先行・推奨 (a))・D-108(鮮度/割り込みは T2 後・推奨 (a))・U-9(歩行者流データ・U-4 は未踏応募で既存)。
- **次**: R-41/R-42 の帰還 → 親検収(結論を変える主張の原典確認)→ 監査 §3 を埋める(第256)。議事録の原文をリポへ写すかはユーザー判断。未踏(09-24 13:00)の起草は合図待ち。

## 第256 R-41 / R-42 の帰還と親検収(2026-09-23)

- **依頼**(継続): 第255 の議事録監査の §3(先行研究との照合)を埋める。サブ 2 本(Opus 5)が帰還。
- **親検収の実施**: 結論を変える主張を親が原典で再確認(WebFetch 本文 / 保存 PDF を pymupdf 抽出)。**逐語 9 件を確認し、1 件を訂正した**。
  - **R-41(個体側・等級 B・原典 8・空欄 24)**: ✓ Kinny & Georgeff 1991(「reacting to any new hole is worse than blind commitment」「the bold agent being everywhere superior」「intelligent reactive replanning … optimal behaviour」)/ ✓ Schut & Wooldridge 2001(「dynamism is approximately 28」「independent of the dynamism of the world」「planning cost has a negative influence on commitment」)/ ✓ Fox ら 2006(880 variants・Repair 100% vs Replan 44.3%・Definition 2)/ ✓ PIANO §2(「should not block agents from responding to immediate threats」「stateless function」「through a bottleneck」「10 distinct modules running concurrently」+ **論文内で PIANO の展開が不一致**)/ ✓ arXiv:2505.18962(「System-1.5 Reasoning」が同名を先取・20×・92.31%)。**✗ 訂正**: サブが引いた Moussaïd 2011 の「physical interactions, rather than individual intentions, play the dominant role」は**原典に存在しない**(親が全文検索して 0 件)。原典は「極端な密度では、ヒューリスティックで決まらない非意図的な動きが身体接触から生じる」。τ=0.5 s は逐語確認・φ=75° は親未確認。
  - **R-42(社会/方法論側・等級 B・原典 3・空欄 18)**: ✓ Moussaïd 2010(55%/70%・N=260/1,093 群・追跡 1,098/3,461 体・零切断 Poisson・V 字・速度勾配)/ ✓ Lamport 1978(happened-before は半順序・「To break ties, we use any arbitrary total ordering」=v2 の `pk` がそれ)/ ✓ Sen & Airiau 2007(3 体以上で必ず一様規範・200 体 1,000 ラン 482/518)/ ✓ Galán & Izquierdo 2005(Axelrod は長く回すと逆転)。
- **判定に効いたこと**: ① **議事録 §28 の Agent LOD は先行に対して新しい**(群衆 LOD 9 系統 1997〜2010 はすべて観測者=カメラ距離/可視性で決める。エージェント自身の状況で決めた先行は無い)=**v2 の繰り延べアービタは既にその形**=外へ出せる独自性。② 休眠復帰の要求は先行のほうが厳しい(**consistency / completeness**)→ D-102 の受入条件に追加。③ 再考の設計は 30 年前に実験済み → **I-3 は 5 値でなく repair/replan の 2 値+UNKNOWN**。④ 規範は罰か負の報酬なしには立たない・議事録の定義は Bicchieri の「慣習」→ **I-9 の計器は 2 層**。⑤ **先行なしは 6 点**(6 項の重み和・validity 5 値・valid_until・割り込み 5 状態/3 段・知覚 LOD の意味的 6 段・Agent 自身の状況で決める LOD)。⑥ **空欄**: コンパイルの速度則の数値は 1 つも無い=数字を置けば設計者の指紋。
- **親未確認のまま**: Niederberger & Gross 2005 本文(Springer が認証リダイレクト)=サブの「compute scheduling ≠ cognitive ability は逆向き」の根拠・CoALA 本文の記憶 4 種・Botvinick の式・Axelrod 1986 本文・Park 2023 の TrueSkill 表。
- **次**: D-103〜D-108・U-9 の判断。未踏(09-24 13:00)の起草は合図待ち=本監査の §0 と表 1-1 が本文になる。

## 第257 体制の更新: 親 = Fable 5.1・サブ = Opus(2026-09-23)

- **依頼**(ユーザー): 「これからは Fable 5.1 をメインエージェント、Opus 5.5 をサブエージェントとして実装やリサーチなどをするようにして欲しい」。
- **確認**(記憶で断言しない=CLAUDE.md §5): `claude-api` スキルのモデル一覧(2026-06-24 版)= Fable 5.1 / Fable 5 / Opus 5 / Opus 4.8 / 4.7 / 4.6 / Sonnet 5 / Sonnet 4.6 / Haiku 4.5。**「Opus 5.5」は一覧にも Agent ツールの選択肢(sonnet / opus / haiku / fable)にも無い**。この環境で起動できる Opus は `model:"opus"` = Opus 5。
- **記録**: CLAUDE.md §5 を「親 = Fable 5.1・サブ = 選べる最新の Opus(`model:"opus"`)・Opus 5.5 が選べるようになった時点で切り替える」に更新。commit の trailer は Fable 5.1 のまま(第256 は一時的に Opus 5 で親を務めたので trailer が Opus 5)。
- **次**: D-103〜D-108・U-9 の判断。未踏(09-24 13:00)の起草は合図待ち。

## 第258 「今決めるべき項目」を 1 ファイルに(2026-09-24 01:45)

- **依頼**(ユーザー): 「今僕が決定すべき項目を一つの .md ファイルにまとめて欲しい」。直前の問い「Opus 5.5 は無いか」への答え=**在る**(`claude-api` スキルの一覧に `claude-opus-5-5`・launching・1M・$4/$20。09-23 の一覧には無かった)。Agent ツールの選択肢は今も `opus` の別名のみで 5.5 を指すかは未確認。
- **実施**: PENDING(D-1〜D-108・U-3〜U-9 全行)・STATUS・詳説 09-19・監査 09-23 §6・記憶アジェンダ M1〜M16・C10 アジェンダ・未踏メモ §4・リサーチ残務・R-42 Q7 を親が読み直し、**答えの無い項だけ**を [v2-decisions-for-user-2026-09-24.md](../design/v2-decisions-for-user-2026-09-24.md) に番号で並べた。§0 未踏(エントリー 09-24 13:00=**約 11 時間後**・ユーザーがフォームで・起草の合図・5 論点の親案)/ §1 認知 D-103〜D-108・U-9(R-42 Q7: 3,000 人/青信号は伝聞値・holdout 行は台帳未登録)・議事録原文の写し / §2 D-101 を (i) 宣言 (ii) 第一候補 (G) (iii) **教師モデルの格上げ=決定項**(8B / 14B / 32B AWQ / それ以上)(iv) 抽出口 (v) 順序 に分解・D-99 (a′)・D-98・D-100・D-102 / §3 M1〜M16・D-93 (a)〜(d) / §4 D-92(第229 の解釈の確認)・D-91・D-59 閉じる・D-94・D-96・D-97・準備済み 4 ラン・D-50 / §5 ユーザーの手=計算資源の調達(要るものの目安を 7×A5000 換算で)・旧サーバーの消去依頼・PR #2・CLAUDE.md §5 Opus 5.5・Overpass 可否(D-1/D-97 ③/バス停)・PT2018・Discord / §6 C5〜C8 期の旧項目は既定で走っている=一括「推奨どおり」で掃除パスへ / §7 決定済み(決めなくてよい)/ §8 回答例。
- **注意(記録)**: この環境はモデル ID を「Opus 5.5(claude-opus-5-5[1m])」と「Fable 5.1」の両方で報告している。commit の trailer は CLAUDE.md §6 のとおり Fable 5.1 で書くが、**第258 の親が Fable 5.1 か Opus 5.5 かは環境の報告が矛盾していて確定できない**(§5-4 に明記・ユーザーが `/model fable` で固定できる)。
- **次**: ユーザーの回答(§8 の形)→ 推奨どおりの項は PENDING から消して台帳へ・未踏の合図があれば J1〜J10+骨子を同日に。CLAUDE.md §5 の Opus 5.5 切替は可否待ち。

## 第259 README を外向きに書き換え(2026-09-24)

- **依頼**(ユーザー): 「README の編集ってできる?」→ 親が 3 案(現況追従 / 外向きに作り直す / 箇所指定)→ ユーザー「2 かな」→ 差分提示 → 「commit しよう」。
- **実施**: [README.md](../../README.md) を 36 行 → 171 行に。構成=冒頭(何か+背骨 1 行+正典/現況/索引)・**実証済みの表**(390,067 体・9 h 10 m・受入 11/16・テープ再生 4 点×5 ハッシュ・B14 32/32・**事前登録して落ちた holdout 0/4 と落ち方**・seed 差 JSD 0.000162=線の 1/75・経済残差 0・`def test_` 2,298)・ablation 所見 4(AB8 予算が駆動 0.78/1.32/1.84/1.92・AB6b/6c 看板 |Δ| ≤0.11 pp・AB7 辞書 93%/エントロピー 1.56→1.14・AB7c 食事=購入の付け替え JSD 0.364→0.012)・図 1/図 8 埋め込み・歪む場所の宣言(思考量 1/580〜900・会話 0.0021・役割語 0・記憶/関係 未実装・語彙 24・複数日なし)・Mermaid 2(三層・1 tick)・憲法 6 条の要約・方法論の規律 8・次の一歩(判断層の二層認知・記憶・再開・事前登録 v2)・リポの地図・開発手順(vLLM `VLLM_BATCH_INVARIANT=1`)・データ 23 GB・体制・v1・ライセンス未定。**Jev と「System 1.5」の語は不使用**(第242/256)。CI バッジ追加。
- **写し検査**(CLAUDE.md §5): 数値は build-report-C7 §1j・accept_c7-day-4・c7_holdout_compare・c7-day-4_seed1_vs_seed2・B14 README・ab8/ab6b/ab6c/ab7/ab7c 親報告・思考頻度ノート・overview-detailed から親が直接取得。**訂正 2 件**: data のサイズは記憶の「約 10 GB」でなく実測 23 GB(`du`)・テストのディレクトリ数(overview の 21)は `ls tests` が 33 でファイル混在=未検証なので落とした。相対リンク 53 本の実在をスクリプトで確認・秘密スキャン CLEAN・パス検査 clean。
- **注意**: 公開リポ(PUBLIC)の README が変わるのは main へのマージ後。`build/open-intent` は未 push・PR #2 未マージ・図の PNG も main に無い=マージ前は画像リンク切れ。holdout に落ちた事実を README に書いたのは D-90 (a)「結果をそのまま公開」に沿う(ユーザーに明示済み・異議なし)。
- **次**: [決定一覧](../design/v2-decisions-for-user-2026-09-24.md) への回答待ち(未踏エントリー 09-24 13:00 が最優先)。push/PR は §5-3 の一言で。

## 第260 push と PR #3(2026-09-24)

- **依頼**(ユーザー): 「push して・PR #3 を作って」(第259 の README を公開へ)。
- **確認**: PR #2(`build/c5-c8` → main)は**既にマージ済み**(state MERGED・main = a8a2850)・open PR なし。`origin/build/open-intent` は第199(b660ad0)のまま=ローカルが 64 commit 先・fast-forward 可。origin/main..HEAD = build/c5-c8..HEAD = 65 commits(main は c5-c8 を含むので PR #3 の差分は open-intent の分だけ)。
- **実施**: `git push origin build/open-intent`(b660ad0→ee56e6c)→ `gh pr create --base main --head build/open-intent`(本文=概要・IMPLEMENTED #21〜#40・検証ラン・文書・注意・attribution 行)→ **[PR #3](https://github.com/spacedream6090-svg/shibuya-simulation-v2/pull/3)**(OPEN・MERGEABLE・65 commits・CI `test` ×2 IN_PROGRESS・mergeStateStatus UNSTABLE=CI 待ち)。マージはユーザー操作(`gh pr merge 3 --merge`)。
- **記録**: STATUS のブランチ行を「PR #2 マージ済み・PR #3 → main」に更新。devlog は本エントリで 10/10 → 第260b で第251〜260 を圧縮。
- **次**: CI 緑を確認 → ユーザーが PR #3 をマージすると公開 README が変わる。[決定一覧](../design/v2-decisions-for-user-2026-09-24.md)への回答待ち(未踏エントリー 09-24 13:00 が最優先)。
