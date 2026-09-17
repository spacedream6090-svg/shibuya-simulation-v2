# 監査: 答申の推奨・決定項は設計と実装にどれだけ入ったか(P0 35 本)

<!-- hdr:v1 -->
- **分野**: ソフトウェア工学 #29 / ABM方法論 #21 | **重要度**: **P0**
- **一次確認**: **repo 内監査**(Web 不使用)。判定の根拠はすべて `ファイル:行` か関数名。**親の再確認を要する**(§6-4 に優先 5 件) **→ 親再確認 4 件(第214)**: T2 内省は `resolve.py` L39/L1863「発火を記録するだけ」=実呼なし ✓ / 感度台帳 2 本とも 19 行=done 6・todo 13 ✓ / `docs/bench/c8/ablation/` の実施済み腕=AB1・AB6・AB7・AB7b(AB2〜AB5 未実施)✓ / 知覚契約書に「なし」を書かない条文は grep で見当たらず=サブ判定を維持
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **決定台帳**: [v2-redesign.md](../design/v2-redesign.md) §9

> 依頼(2026-09-17・ユーザー): 「現在のシミュレーションはリサーチした内容をどれだけ反映させたものとなっているのか検証して」。
> 対象 = [INDEX.md](INDEX.md) §3 の **P0 35 本**。各答申の推奨表・決定アジェンダ節・結論から主要 3〜8 項を抜き、
> **設計への反映**(DECIDED 行・設計書の節)と **実装への反映**(`src/` のモジュール・関数、`tests/` の有無、IMPLEMENTED #)で 5 値判定した。
> 手本は [batch1](v2-r23-primary-check-batch1.md) §1(参照表)・[batch2](v2-r23-primary-check-batch2.md) §1(特徴値 grep)。

## 0. 判定の定義と作業条件

| 値 | 意味 |
|---|---|
| **実装済** | `src/`(または `tools/`・設計文書が成果物の項は当該文書)に実体があり、`tests/` が触れている |
| **設計済・未実装** | DECIDED 行か設計書にあるが `src/` に実体が無い |
| **部分** | 縮退版・expedient で代替されている(答申の形とは違うが機能は入っている) |
| **未採用** | 答申は推奨したが決定で採らなかった(理由の記録の有無を併記) |
| **未判定** | 答申にも設計にも痕跡が見つからない(=**取りこぼし候補**)、または答申の記述が曖昧で判定不能 |

**作業条件(重要)**
- HEAD = `a6fcea0`(第213・C9a)。**作業ツリーに未コミットの変更が 14 ファイル・945 行ある**(C9b 相当: 注意の焦点・「近づく」・会話距離の分離・語彙まわり)。本監査は**作業ツリー**を見ており、未コミットのものは判定欄に `(未コミット)` と書いた。
- 設計文書が成果物である項(文書の訂正・決定の明文化)は、**その文書が実際に直っているか**を `ファイル:行` で見て「実装済」とした。
- 「テストがある」は該当モジュールを import または定数を参照するテストが `tests/` にあることを指す。個々のテスト関数名までは追っていない(§6)。

---

## 1. 集計

### 1-1. 5 値の総計(P0 35 本・判定項 240 件)

| 判定 | 件数 | 割合 |
|---|---:|---:|
| **実装済** | 127 | 52.9% |
| **設計済・未実装** | 48 | 20.0% |
| **部分** | 44 | 18.3% |
| **未採用** | 11 | 4.6% |
| **未判定(取りこぼし候補)** | 10 | 4.2% |
| 合計 | **240** | 100% |

**読み方**: 「実装済+部分」= 171 件(**71.3%**)が何らかの形でエンジンに入っている。
「設計済・未実装」48 件の大半は **工程 C3 以降へ持ち越した認知層**(記憶 M4・関係辺 M5・習慣 M3・ペルソナ M6・T2 内省)と **第2陣/Phase 3 に置いた世界過程**(SNS・健康・犯罪検知・立法/裁定)、そして **C9 で方針転換した群衆物理**に集中している。
「未判定」は 10 件と**少ない**。この repo が答申→決定台帳→設計書→実装の写しを毎回残しているため。ただし後述のとおり、10 件のうち 6 件は**「答申が推奨したのに決定ラウンドの議題に一度も乗っていない」型**で、これが本監査の主な発見。
**未採用 11 件のうち、理由の記録が無いのは 1 件だけ**(ad-information のスカラー変換)——不採用の理由づけの規律は概ね守られている。

### 1-2. 分野別(INDEX §2 の分野番号・複数分野の答申は主分野へ寄せた)

| 分野群 | 判定項 | 実装済 | 設計済未実装 | 部分 | 未採用 | 未判定 |
|---|---:|---:|---:|---:|---:|---:|
| 知覚心理学・精神物理学 #5 | 43 | 25 | 2 | 9 | 3 | 4 |
| 環境音響学 #6 / 認知(更新規則) #12 | 14 | 6 | 4 | 3 | 0 | 1 |
| 会話分析 #15 / 行動経済 #16 / 社会ネットワーク #14 | 13 | 9 | 2 | 1 | 1 | 0 |
| SFCマクロ経済学 #10 / 都市代謝論 #19 / OR #20 | 23 | 14 | 6 | 1 | 1 | 1 |
| 認知科学(記憶・習慣) #12 / 人格心理学 #13 | 20 | **2** | **13** | 5 | 0 | 0 |
| 人口学 #1 / 人間移動 #3 / 交通工学 #2 / 時間利用 #4 | 27 | 20 | 1 | 3 | 3 | 0 |
| 地理情報科学 #9 / 気象 #8 / 建築環境 #7 | 20 | 16 | 1 | 3 | 0 | 0 |
| 歩行者動力学 #18 | 22 | 8 | 8 | 4 | 2 | 0 |
| 検証とV&V #22 / 統計 #23 / 予測科学 #24 | 30 | 11 | 6 | 10 | 1 | 2 |
| 法学(業法・条例) #11 | 8 | 3 | 3 | 1 | 0 | 1 |
| ABM方法論 #21 / 計算社会科学 #25 / NLP #27 | 20 | 13 | 2 | 4 | 0 | 1 |
| 合計 | 240 | 127 | 48 | 44 | 11 | 10 |

**分野の偏りが本監査の最大の所見**:
- **認知科学 #12 / 人格心理学 #13 は 20 件中 実装済 2・設計済未実装 13(65%)**。答申・設計はあるが `src/` が空に近い唯一の分野群。
- **歩行者動力学 #18 も 22 件中 実装済 8・設計済未実装 8**。ただし性質が違い、こちらは C9 G13(物理は事前計算)で**方針が変わったために設計が宙に浮いている**。
- **検証とV&V #22 / 統計 #23 は「部分」が 10 件と最も多い**。計器の骨格はあるが合否線・fair 化・多重比較が入っていない=**holdout 開封の直前で効く穴**。
- 逆に 人流/人口(27 件中 20 実装済)・地理/気象(20 中 16)・経済(23 中 14)は高い。C0〜C6 の工程順序と一致しており、意図した順序の結果である。

### 1-3. 一次確認の等級別

| 等級 | 答申 | 判定項 | 実装済 | 未判定 |
|---|---:|---:|---:|---:|
| A(親検収済) | 4 本 | 28 | **10(35.7%)** | 2 |
| B(出典あり・空欄明示) | 30 本 | 207 | 113(54.6%) | 8 |
| C(空欄未整理) | 1 本(ad-information) | 5 | 4(80%) | 0 |

**含意**: 等級 A の答申(crowd-physics・dashboard・replication・w7-law)は**実装率が最も低い**(10/28 = 35.7%)。
理由は 4 本とも「決定が下りた**後**に一次確認した」答申だから——crowd-physics は G13 で方針が変わり、replication は G-8 の「8 seed」を**否定する**答申、w7-law は既存コードの穴の指摘、dashboard だけが事前リサーチ。
**一次確認の質と実装率は相関していない**。「A 等級だから入っている」とは言えず、むしろ **A 等級は「後から効いてきた宿題」の山**になっている。

---

## 2. 答申ごとの判定表(P0 35 本)

> 列: 項 / 設計への反映 / 実装への反映 / **判定**。根拠はすべて `ファイル:行` か関数名。

### 2-1. v2-r23-primary-check-batch2(背骨 4 答申の一次確認・B)

| # | 答申の決定項(§4) | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | A: 「制度は Sid の実証」→「Sid は足場なし条件を走らせていない」に置換 | D-78 (a) | `docs/design/v2-redesign.md:198-199`(第210 訂正の逐語あり) | **実装済** |
| 2 | B: 「4 答申が独立収束」→「4 つの異なる先行群と両立」 | D-78 | `docs/design/v2-architecture-roadmap.md:39`・`CLAUDE.md` §3 第1行 | **実装済** |
| 3 | C: `ACCEPT_PROBABILITY=0.8` の「較正目標」を expedient に統一+感度試験へ登録 | D-78 | `src/shibuya/engine/conversation.py:81-82` が「較正データ無しの定数・expedient」と明記。**ただし `tools/c8/ablations_v1.json` に 0.8 の腕は無い**(AB1〜AB7c) | **部分** |
| 4 | D: 「Concordia が撤回した設計」→「既定据え置きのまま止める口」 | D-78 | `docs/design/v2-action-contract.md`(第210 訂正) | **実装済** |
| 5 | E: 保存則テスト 5 層の **T3(冗長方程式の毎期 assert)**が実装にも設計にも無い | D-78 | `docs/design/v2-boundary-economy-design.md:59` に残務として明記。`src/shibuya/economy/checks.py` は検算①②のみ | **設計済・未実装** |
| 6 | F: Decoupling を根拠に「地理+到達可能性で改善」と書くのは原典の主張でない | D-78 | `docs/design/v2-inventory-and-bottlenecks.md`(第210 訂正・「v2 の仮説」へ格下げ) | **実装済** |
| 7 | G: CPC を「ゼロ相関」と呼ばず実データ間フロアを併記 | D-78 | 同上+`CLAUDE.md` §5 に**フロア併記検査**を規律として追加 | **実装済** |

### 2-2. v2-ad-information-research(広告・情報伝播・**C 等級**)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 注意ゲート 4 段(幾何 → p_see → 注視時間 → 効果キャップ) | 知覚契約書 §4・DECIDED「R3-8 §4」 | `perception/attention.py`: 段0 は呼び出し側、`p_see():185`・`gate_stage1():205`・`apply_budget():266`・`content_cap_chars():272` | **実装済** |
| 2 | 既定は**非注入**・1 ステップ最大 1 件 | 知覚契約書 §4 段2 | `attention.apply_budget`(枠に入らなければ載せない)+`channels.ChannelLimit("B2.signage",…,25)` | **実装済** |
| 3 | テキストでなく**スカラー変換**(親近性 ε)を第一候補に | — | `src/` に親近性スカラーの経路は**無い**。看板は B2 にテキストとして描かれる(`templates.py:435`) | **未採用**(理由の記録**なし**) |
| 4 | ablation「広告ゼロ ラン」を予約 | 知覚契約書 §8 第1陣 ⑥ | `tools/c8/ablations_v1.json` の **AB6-AD-ZERO**(rank 6)+`renderer.py:601 signage_enabled` | **実装済** |
| 5 | 世界内プロンプトインジェクション防御(構造化属性へ還元+命令文除去) | 憲法6・知覚契約 §1 条6 | `attention.strip_imperatives():278`・`renderer.py:947`(看板(a)=店舗基本属性へ還元) | **実装済** |

### 2-3. v2-perception-u17-research(五感/VLA・最大の答申)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | (a) 構造化観測+**決定論的可視性計算**を正典(VLA 不採用) | DECIDED「R3-1」 | `build/vis/w8_visibility.py`(`_los`/`_visible_targets`/`_cell_pair_visibility`・W8 356,732 視点)+`tests/build_vis/` | **実装済** |
| 2 | 動的物体の遮蔽は低解像度セグメンテーション/短距離レイキャストで毎ステップ | — | `src/` に動的遮蔽は**無い**(W8 は静的・可視性は事前計算のみ) | **未判定**(設計書にも痕跡なし=**取りこぼし候補**) |
| 3 | VLM は「場所の静的言語化」(償却型)に限定 | DECIDED「R3-1」 | `build/lang/w15_cell_static.py`(514/520 セル凍結・IMPLEMENTED #15)。ただし**VLM ではなく LLM(32B AWQ)**で生成 | **部分** |
| 4 | VLM を SAGAI 式の**現実整合アンカー検証器**に | DECIDED「R3-6a」(7 項) | `src/`・`tools/` に VLM 検証器は**無い** | **設計済・未実装** |
| 5 | (c) VLA 直結は不採用 | DECIDED「R3-1」に明記 | — | **未採用**(理由の記録あり) |
| 6 | **内受容感覚を視覚より先に**(満腹・体力・体感温度の 3 変数) | DECIDED「R3-2」 | `agents/state.py:289 INTEROCEPTION_FIELDS=("hunger","fatigue","thermal")`+`:377-389`(段+ヒステリシス段) | **実装済** |
| 7 | 五感の残りは「発生源が自己申告するスティミュラス」型 | DECIDED「R3-7」 | `engine/processes/salient.py`(顕著行為イベント)+`p_notice.notice_event()` | **実装済** |
| 8 | 嗅覚は保留 | DECIDED「R3-4」= 保留 | — | **未採用**(理由の記録あり) |

### 2-4. v2-area-boundary-definition(5 エリア定義)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 5 エリアは指針2010 の分割線+拡大地図の記述で定義できる(町丁目リストでは不可) | DECIDED「D1′=(b)」 | `tools/c7/area_axes_v0.json`(`source.primary`=指針2010 p.18 図・`status:"expedient"`) | **実装済** |
| 2 | 境界は OSM 線形で座標化する | DECIDED「R3-8 第2弾 ①」 | `area_axes_v0.json` は**軸(分割線)による近似**で、OSM 線形化は入っていない(R-19 が残務) | **部分** |
| 3 | holdout(KDDI)の 5 エリア写像はこの定義に依存 | 事前登録 v1.1 §2 | `tools/c7/c7lib.area_hour_table`・`occupancy_series.build_map`・`holdout_compare.py` | **実装済** |
| 4 | 外周(5 エリアの外縁)は区域図から幾何推定=推測 | — | `area_axes_v0.json` の `status:"expedient"` として宣言 | **実装済** |

### 2-5. v2-density-hearing-verification(可聴半径は密度の関数か)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 暗騒音 = 静的場(ASJ RTN 計算)を前計算 | DECIDED「R3-7 ①」 | `build/field/w10_noise.py:56 ASJ_COEFF`・`laeq_at():300`+`world/processes/first_batch.py:237 _NOISE` | **実装済** |
| 2 | 密度項(多数話者エネルギー和+Lombard 不動点)を毎更新で足す | DECIDED「R3-7 統合形」・`first_batch._CROWD.reaches=("聴覚: 密度項",)` | `engine/processes/crowd.py` は密度・流れのみ。**騒音の密度項は無い** | **設計済・未実装** |
| 3 | 半径は各イベントで導出関数 `r=10^((L_src−L_amb−ΔSNR)/N)`・場所ごとの定数を置かない | 知覚契約 §3 | `src/` に `hear_radius` は無い。`engine/commit.py:453`「雑談の可聴距離 1-2.5 m → **同一セルで代理**」 | **部分**(expedient 代替・宣言あり) |
| 4 | ΔSNR 2 段(内容理解 ≈0/検知 ≈−10 dB)→ 後続答申で −3/−12 へ | 知覚契約 §3 | `perception/attention.py:9`「聴覚=SNRマージン(ΔSNR −3/−12)」+`ablations_v1.json` **AB4-HEARING-SNR** | **実装済** |
| 5 | 5m 格子・シミュ内 1 分毎の更新(GPU 0.04ms/CPU 82ms) | — | 動的な聴覚場そのものが無いので更新頻度も無い | **設計済・未実装** |
| 6 | 「騒音は移動を駆動しない」を台帳行の完了条件に | `v2-pattern-ledger.md` | `first_batch._NOISE.contributes=("D12′",)`・`gate_condition` は残差 ≤3 dB。**移動を駆動しないことの照合行は見当たらない** | **未判定** |

### 2-6. v2-observation-format-research(観測の表現形式・予算)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 決定論テンプレで素性タグ付き短い平叙文(生 JSON を渡さない) | 知覚契約 §2.1 | `perception/templates.py`(TEMPLATES 表・凍結 SHA 161fe181)+`renderer.py` | **実装済** |
| 2 | ブロック順序は変化率の昇順・`[個体]→[問い]` を末尾に | 知覚契約 §2.2・DECIDED「R3-8 §5」 | `templates.BLOCK_IDS=("B0","B1","B2","B3","B4","B4b","B5","B6")`(B6=問い) | **実装済** |
| 3 | 決定論レンダリング規約 8 項(版数先頭・量子化・キーソート・**NFKC**・**固定行数パディング**・共有に時刻/乱数/個体 ID を入れない) | 知覚契約 §2.4 正規化規約 9 項 | `perception/normalize.py:172` NFKC・`sort_ids():145`・`peg_stage():204`・`assert_no_agent_dependent_words():241`。**「共有ブロックは固定行数・空でもパディング行」は `src/` にも契約書にも無い** | **部分** |
| 4 | 文面規約: 「なし」を書かない(否定文は注意を引きすぎる) | — | `templates.py:436` `"B2.signage_empty": "[B2 看板] 見える表示はありません。"`、`:453`・`:457`・`:459` も否定文。**答申の推奨と逆** | **未判定**(採否の記録なし=**取りこぼし候補**) |
| 5 | 出力側に厳密 JSON スキーマを課さない(2 行形+決定論パーサ) | DECIDED「R3-8 §2」 | `llm/parser.py`(2 行形)+`llm/contract.py`・書式エラー率 0.007-0.047(IMPLEMENTED #16) | **実装済** |
| 6 | 差分観測は LLM 入力に持ち込まない(差分は配送層のみ) | 知覚契約 §1 条3(有界な完全現在形・差分禁止) | `perception/hashes.should_resend():92`(dormant 再送抑止)・`perception/state.py:104-106` | **実装済** |
| 7 | 観測トークン予算 ≈950(共有 650+個体 300) | 予算書 **M11**(入力 ≤1,300・共有静的 ≤750/セル ≤250/個体 ≤300) | `perception/channels.py` の `ChannelLimit` 表+`tests/test_budget_table.py` | **実装済**(値は答申案と別建て=契約書側が正) |
| 8 | ベンチ 3 本(BN-1 セル数139/BN-2 共有長/BN-3 KVFlow 型追い出し) | — | BN-1/BN-2 は実施(IMPLEMENTED #6・docs/bench)。**BN-3(次tick生存セル保護の追い出し)は未実施** | **部分** |

### 2-7. v2-perception-latency-research(δ_perc)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | δ_perc 導入・`0.213 s × k(予期クラス) × m_att` | 知覚契約 §6・DECIDED「R3-8 §6」 | `engine/commit.py:119-120 DELTA_PERC_BASE_NS=213_000_000`・`delta_perc_ns():185`(k=0/1.0/1.6/4.9/6.1) | **実装済** |
| 2 | 分布は**対数正規 σ_ln=0.20**(バースト平準化を兼ねる) | 知覚契約 §6 | `commit.delta_perc_ns` は**予期クラス別の定数**(docstring に明記)。乱数は入っていない | **部分** |
| 3 | `m_att`(スマホ/会話中 ×2.0)・傍観者倍率(C5 のみ) | — | `src/` に `m_att` は無い | **未判定**(設計書にも痕跡なし=**取りこぼし候補**) |
| 4 | p_notice は**事象発生 tick での一発ベルヌーイ**(毎tickハザードにしない) | 知覚契約 §3.1 | `perception/p_notice.py:12`「発生 tick での一発ベルヌーイ」・`notice_event():397` | **実装済** |
| 5 | δ_perc は世界時刻を進めず tick 内のナノ秒欄としてのみ使う | 運用設計書 §2.3 | `engine/clock.py:89`・`engine/commit.py:16`・pk 第1要素 | **実装済** |
| 6 | ablation 4 本(δ_perc=0/クラス一律/m_att=1/σ_ln=0) | 知覚契約 §8 | `ablations_v1.json` に δ_perc の腕は**無い**(AB1〜AB7c) | **設計済・未実装** |

### 2-8. v2-perception-timing-research(知覚のタイミング)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 第1条: 知覚更新(エンジン算術)と認知起床(LLM 呼)を別契約に | 知覚契約 §6 | `engine/change_detect.py`(更新)と `engine/arbiter.py`(起床)が別モジュール・予算も P6 と L4 で別 | **実装済** |
| 2 | 第3条: セル共有ブロックのバイト列ハッシュ=prefix鍵=変化検出器=dormant抑止の**三役** | DECIDED「R3-8 §5」 | `perception/hashes.py`(`block_hash`/`prefix_key`/`should_resend`)・`change_detect.b4_block_hashes():168` | **実装済** |
| 3 | 第4条: 量子化にヒステリシスと最小滞留時間 `T_hold=60 秒` | 知覚契約 §6(内受容のみ) | `change_detect.py:74`(ヒステリシス幅 1 段・内受容)。**T_hold(最小滞留時間)は無い**。セル側の密度/騒音段にヒステリシスも無い | **部分** |
| 4 | 第5条: 起床時に「前回起床からの差分要約」を必ず渡す(FD 対策) | — | `renderer.py` の B5 に差分要約の欄は無い | **未判定**(**取りこぼし候補**) |
| 5 | 起床トリガ正典 6 類+**顕著性アキュムレータ S(t)>θ**(ADSR エンベロープ) | 知覚契約 §6 の起床条件(i)-(iv)+不応期表 11 行 | `agents/state.py:234 WakeCondition`(11 行)・`REFRACTORY_MINUTES:255`。**S(t) アキュムレータと θ は無い**(顕著性は `attention.rank_by_saliency` の**順位づけ**にのみ使用) | **部分** |
| 6 | ハートビート(最大無起床間隔)は活動中のみ | DECIDED「R3-8」= **周期HB廃止**(IMPLEMENTED #6) | `src/` に heartbeat 無し | **未採用**(理由の記録あり) |
| 7 | 予算超過時のアービタ(LOD Trader 型・破棄でなく繰り延べ・16 バケット量子化) | DECIDED「R3-8 §6/§9」 | `engine/arbiter.py:31`(整列鍵)・`:411`(T_max 超過で累積昇格=starvation-free)・`:425`(同一体の合流) | **実装済** |
| 8 | 予算行 P1〜P10(うち P5 ファンアウト上限・P8 dormant 抑止率 ≥90%・P10 起床原因内訳) | 予算書に **P6/P7/L4/L5/L6/M10/M11/M12** を採用 | `tests/test_budget_table.py`。**P5(ファンアウト上限)・P8(dormant 抑止率)・P10(起床原因 60% 超で見直し)は予算書にも `src/` にも無い** | **部分** |

### 2-9. v2-turing-test-validation-research(識別テスト)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | ID-test を**Phase ゲートに置かない**(診断扱い) | DECIDED「R3-6b」 | `docs/design/v2-dashboard-verification-orchestration.md:5`(「識別テスト=診断扱い」) | **実装済**(決定として) |
| 2 | T0 計器健全性(既知歪み注入で power .8・同分布で AUC 0.5±CI)= **唯一ゲート化してよい項目** | DECIDED「R3-6b 陽性対照ゲート」 | `tools/`・`src/` に識別器も陽性対照も**無い** | **設計済・未実装** |
| 3 | 封印 3 層(D 層 burned / S 層封印識別器 2 本 / P 層陽性対照) | DECIDED「R3-6b 封印3層」・台帳 S1/S2/S3 | `v2-pattern-ledger.md` の封印行は実在(`world/processes/constitution.py:21` が封印行の `contributes` 記載を違反にしている)。**識別器の封印は無い** | **部分** |
| 4 | 較正禁止条項「識別器の出力を損失・目的関数に使わない」 | 方法論「自己修正ループ」禁止 4 つ(`v2-methodology.md`) | `v2-methodology.md` の禁止 ①「LLM に世界を採点させて直す」で実質的に包含 | **実装済**(文書として) |
| 5 | δ(等価性マージン)を開封前に事前登録(D4′ 0.10/D1 0.07/SSB 0.02) | 事前登録 v1.3 草案に**同値検定**として入った(`docs/bench/c7/prereg_arms_v1.md:78`) | δ の列ごとの値は未設定 | **部分** |
| 6 | SSB 匿名個票の取得(唯一 δ=0.02 級が言える列) | 決定台帳「SSB」= **OPEN** | 未取得 | **設計済・未実装** |

### 2-10. v2-action-conversation-contract-research(行動契約・会話)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 行動契約表(横断 12 語+種別固有 12 語=24)・列 7 欄 | DECIDED「R4 1」・行動契約書 §1 | `llm/contract.py`(`ACTION_VOCAB_12`・`ROLE_ACTION_WORDS`・`ALL_ACTION_WORDS`・`VOCAB_LIMIT_PER_KIND=24`)+`tests/llm/` | **実装済** |
| 2 | 会話プロトコル: 招待→応答判定(≈0.8)→ invited/walkingOver/participating | DECIDED「R4 3」・行動契約書 §3 | `engine/conversation.py:129 ConvState`・`ACCEPT_PROBABILITY:82`・`:431` | **実装済** |
| 3 | 終了を LLM に決めさせない(max_turns 3・沈黙閾値・定型の締め) | 同上 | `conversation.py:83 MAX_TURNS`・`CLOSING_UTTERANCE:115`・`_enter_closing():760` | **実装済** |
| 4 | 記憶転写の重み(宛先 1.0/非宛先 0.5/傍受 0.2) | 行動契約書 §4(1.0/0.5/0.2) | `src/` に記憶レジストリが無い(`agents/state.py:8`「記憶 M4・関係 M5 は C3 以降の別レジストリ」)。転写も無い | **設計済・未実装** |
| 5 | 関係辺: 層容量 5/15/50/150・強度 Δ・半減期 90 日・押し出し規則 | DECIDED「R4 4」・行動契約書 §5 | `src/` に `Dunbar` も関係辺 SoA も無い(`state.py:26`「関係辺…持たないことを本書の未実装として登録」) | **設計済・未実装** |
| 6 | 未定義行動 5 段(段0 辞書→段1 レコード→段2 裁定→段3 検収→段4 判例) | DECIDED「R8 裁定判例」 | 段0-1=`llm/undefined.py`・段2-3=`tools/vocab/adjudicate.py`(IMPLEMENTED #25)・段4=`llm/contract.VOCAB_VERSIONS`(IMPLEMENTED #26) | **実装済** |
| 7 | 語彙は種別あたり 24 語を硬い上限・到達したら最も使われない語を封印 | 行動契約書 §6 | `contract.py:93 VOCAB_LIMIT_PER_KIND=24`。**封印(剪定)の機構は無い**(D-71 §2 J で「計測だけ先に」) | **部分** |
| 8 | `counts_as(物理的事実, 制度的事実, 文脈)` への登録 | 世界過程設計 §2 | `world/processes/relations.py`(関係 4 本)。`counts_as` は型として存在 | **実装済** |

### 2-11. v2-boundary-economy-u10-u11-research(U10 境界・U11 経済)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | U10 案A(外界 RoW+週次活動スケジュール表+差分時のみ LLM) | DECIDED「U10」= 案A+案C | `build/field/w12_external_nodes.py:55`(方面別 10 ノード)+`agents/weekly.py`/`build/sched/w17_schedule.py` | **実装済** |
| 2 | 案B(重力モデル抽選)は**下限対照 ablation として 1 本必ず走らせる** | DECIDED「U10」・`v2-boundary-economy-design.md:22` | `ablations_v1.json` に重力抽選の腕は**無い**。`--no-plan-executor`(帰無腕)は rail 乱数 12% の**旧挙動**であって重力モデルではない | **設計済・未実装** |
| 3 | U11 6 部門(銀行を追加)・BS6 行・TFM12 科目+残差+退蔵 | DECIDED「U11」 | `economy/accounts.py:59 Sector`(6)・`:88 BS 6 行`・`:110 Account`(12+残差+退蔵+逸脱コスト) | **実装済** |
| 4 | faucet/sink 表を `account_code` と 1:1・列挙にない科目は実行不能 | DECIDED「U11」・CLAUDE.md §4 | `accounts.faucet_sink_table()`・`economy/ledger.py:402 transfer`(単一 API)・`engine/ledger_api.py:109` | **実装済** |
| 5 | 検算 2 本(行和列和=0 / 純資産合計=実物資産)・主検算は後者 | DECIDED「U11」 | `economy/checks.py:76`(検算①)・`:98`(検算②)+`tests/economy/` | **実装済** |
| 6 | 日次/月次センサス(EVE MER 型の固定表) | DECIDED「U11」 | `economy/census.py`+`cli.write_census_files`(`--census-out`・IMPLEMENTED #23)+部門軸(#24) | **実装済** |
| 7 | 参入資本は transfer 由来のみ(ex nihilo 禁止) | DECIDED「U11 R4」 | `economy/entry_capital.py`+`checks.py`(ex nihilo 検査)・IMPLEMENTED #14 | **実装済** |
| 8 | 較正 3 階層 + 「較正が生成分布を変えてよい上限(±5%)」の事前宣言 | — | `data/ground_truth/registry.yaml` は存在。**±5% の上限宣言は見当たらない** | **未判定** |

### 2-12. v2-channel-budget-attention-research(チャネル予算・注意)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | チャネル別観測予算の上限表(根拠等級つき) | DECIDED「R3-8 §3」 | `perception/channels.py:127-160 CHANNEL_LIMITS`(`Grade` 付き)+`tests/perception/` | **実装済** |
| 2 | B5 220 > B2 150(クリティカル注視に基づく**意図的な歪み**と明記) | 知覚契約 §3.2 | `channels.py:19`・`:68` に逐語で歪みの宣言 | **実装済** |
| 3 | 近接 k の**密度逓減**(疎3/中2/密1) | DECIDED「R3-8 §3」 | `channels.py:128`「近接人物 上位k(密度逓減3/2/1)×33」 | **実装済** |
| 4 | p_see の日本アンカー(大型ビジョン 0.70・中小 0.14-0.40 は英仏からの流用=expedient) | DECIDED「R3-8 §4」 | `attention.py:5-7`・`:27 P_SEE_MEDIUM_DEFAULT=0.27` | **実装済** |
| 5 | 顕著性を「サイズ×輝度×距離の単純和」にしない(標準モデルが否定) | DECIDED「R3-8 §4」= 視角×局所コントラスト | `attention.py:100 SALIENCY_WEIGHTS`・`rank_by_saliency():230` | **実装済** |
| 6 | 内容キャップ: 日本語 `round(7.5×注視秒)`・下限4・上限30(旧 10-20 字は片側で誤り) | DECIDED「R3-8 §4」 | `attention.py:111-115`・`content_cap_chars():272` | **実装済** |
| 7 | 密度スケーリング(新規提案・人への注視配分を密度で上げる) | — | `src/` に密度による注視配分の変更は無い(密度は k の逓減にのみ効く) | **部分** |

### 2-13. v2-p-notice-research(p_notice の関数形)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 案B 2 段 Hill を採用(案A は ablation として保持) | DECIDED「R3-8 §3」 | `perception/p_notice.py:275 p1_primary`・`:295 p2_social`・`:307 combine`・`:134 Ablation` | **実装済** |
| 2 | 一次検出 `d50_eff = d50 × m_light × m_ecc × m_density`・`P1'=P1×m_load` | 知覚契約 §3.1 | `p_notice.py:5-9`+`eccentricity_deg():262`・`TaskLoad:118`・`DensityClass:126` | **実装済** |
| 3 | 二次検出(社会伝播)`P2 = 0.92·N^1.05/(1.2^1.05+N^1.05)`・半径 15 m | 同上 | `p_notice.py:105-109 SOCIAL_RADIUS_M=15.0/SOCIAL_A=0.92/SOCIAL_B=1.05/SOCIAL_N50=1.2`・`social_counts():315` | **実装済** |
| 4 | `d50=40 m` は expedient・ablation で 20/40/80 を振る | 知覚契約 §10 expedient 登録簿 | `p_notice.py:85 D50_DEFAULT_M=40.0`+`ablations_v1.json` **AB2-PNOTICE-D50**(0.5×/2×) | **実装済** |
| 5 | 打ち切り半径 80 m(=2·d50)を**性能予算とのトレードオフとして宣言** | 予算書 **P7**(打ち切り 80 m・±1 リング 9 セル・顕著イベント上限 200/tick) | `docs/design/v2-budget-declaration.md` P7 行+`p_notice.EventBudget:224` | **実装済** |
| 6 | ablation 段 A0〜A4(定数 0.54 → 距離 → 負荷/照明 → 偏心/密度 → 社会) | 知覚契約 §8 | `p_notice.py:134 class Ablation` は存在。**A0〜A4 を回す腕は `ablations_v1.json` に無い**(AB2 は d50 のみ) | **部分** |

### 2-14. v2-update-rules-hearing-research(更新規則・聴覚数値)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 不応期 A 案: イベント駆動は床なし・状態駆動に床(11 行の表) | DECIDED「R3-8 §6 (1)」 | `agents/state.py:234 WakeCondition`(11 行)・`:255 REFRACTORY_MINUTES`・`:441 refractory_until (n,11)` | **実装済** |
| 2 | 不応期は**体×条件ごと**・同時に明けたら 1 呼に合流 | 同上 | `state.py:441`(2 次元)・`arbiter.py:425`(合流) | **実装済** |
| 3 | 内受容は**ヒステリシスで置換を試す** | 知覚契約 §6 | `change_detect.py:10-11`・`:74`(ヒステリシス幅 1)・`agents/state.py:262` | **実装済** |
| 4 | 日次内省 A 案: 就寝イベント同期・1.05 回/体/日・上位 5% は即時 | DECIDED「R3-8 §6」・予算 **L5**(42 万呼/日) | `engine/resolve.py:1840`「就寝→**T2 日次内省の発火を記録**」+`:1867 n_reflections`。**実際の T2 呼は無い**(`resolve.py:39`「実際の内省呼は C3」だが C3 で入っていない) | **設計済・未実装** |
| 5 | 繰り延べ 4 クラス固定優先+T_max 昇格+縮退実行 | DECIDED「R3-8 §6 繰り延べアービタ」 | `arbiter.py:7-8`・`:38 T_MAX_TICKS`(3/10/30/60)・`:411` | **実装済** |
| 6 | **invocation distance を 3 役で使う**(繰り延べ順序・KV 退避優先度・プリフェッチ) | 予算 **M12**(2 B/体) | `agents/state.py:403 invocation_distance` 欄は確保済み。**3 役のいずれにも使われていない**(`arbiter` の整列鍵は待ち tick・`llm/fleet.py` に退避優先度なし) | **部分** |
| 7 | ΔSNR 内容理解 −5→**−3 dB**・Lombard 折れ点 45 dB・高齢/非母語 +3 dB | 知覚契約 §3 | `attention.py:9`(−3/−12)。**Lombard 折れ点・高齢補正は `src/` に無い** | **部分** |
| 8 | sleep-time compute(内省出力を翌日 prefix に焼く)をベンチで測る | 予算 L5 の欄 | 未実施 | **設計済・未実装** |

### 2-15. v2-world-process-rows-research(エンジン/LLM 線引き 16 行)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 行5 価格形成: 内生フロア+クリアリング+逸脱比例コスト+Calvo 改定・LLM は相対倍率スカラー | DECIDED「D-R2-3 行5=A案」 | `economy/pricing.py`+`accounts.Account.DEVIATION_COST:130`。Calvo 頻度は世界過程設計 §8 H-1 | **実装済** |
| 2 | 行6 賃金も同型・制度フロア(最低賃金)は硬い制約にしない | DECIDED「D-R2-3 行6」 | `economy/accounts.Account.WAGE`・`ledger.transfer`。**賃金の内生形成(改定)は無い**(賃金は W16 由来の固定) | **部分** |
| 3 | 行8 社会関係グラフ: 上限 150・層 5/15/50 を同時強制 | DECIDED「R4 4」 | 関係辺レジストリ(M5)が無い | **設計済・未実装** |
| 4 | 行9 SNS: O(feed_size) 増分限定 | DECIDED「D-R2-5 **第2陣**」 | `llm/contract.py:481`(「並ぶ/撮影」の効果に「SNS 投稿候補」)のみ。過程は無い | **設計済・未実装** |
| 5 | 行15 記憶: 減衰・retrieval の定数 | DECIDED「U1 ハイブリッド」 | 記憶レジストリ(M4)が無い | **設計済・未実装** |
| 6 | 行16 未定義行動: 3 層の受理パイプライン(すべてエンジン規則) | DECIDED「R8」 | `llm/undefined.py`+`tools/vocab/` | **実装済** |
| 7 | 行2 待ち行列: 施設の収容・M/M/c 近似 | DECIDED「D-R2-3 行2」 | `world/processes/first_batch.py:355 _INDOOR`(M/M/c 近似)+`engine/processes/crowd.py` | **実装済** |
| 8 | 行10 健康 / 行12 犯罪検知 | DECIDED「Phase 3 以降」 | `src/` に無し | **設計済・未実装** |

### 2-16. v2-cognition-detail-research(δ_think・U19・昇格・記憶)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | δ_think レーン表 L0 0/L1 2.6 s/L2 82 s/L3 300 s×≤3/L4 0.2 s | DECIDED「R5/U19」・認知設計書 §1 | `engine/llm_bridge.py:8`(レーン表を逐語)・`:46`(L1=1 tick) | **部分**(L1 のみ稼働・L2/L3 は経路なし) |
| 2 | U19: T1=思考 0・T2 は世界規則上の上限を置かない・**打ち切り禁止でクォータで守る** | DECIDED「R5/U19」 | `build/lang/common.py:117 "thinking": False`・`llm/fleet.py`。`max_tokens 96` は expedient(実装計画書 §8:214) | **部分** |
| 3 | 昇格式 `S(e)=w1..w5`・θ_imm/θ_cum | DECIDED「R5 昇格 S(e)」 | `src/` に `surprise`/`stake`/`novelty`/`theta_imm` は**無い** | **設計済・未実装** |
| 4 | 記憶の採点式 ACT-R base-level + Ruri-v3-30m 埋め込み cos | DECIDED「U1」・認知設計書 §4 | `src/` に `ACT-R`・`Ruri`・`embedding` は**無い** | **設計済・未実装** |
| 5 | 記憶バイト予算 6.1 KB/体(構造化 3.0 KB+12 本×260 B) | 予算書 M4 相当 | 記憶レジストリが無いのでバイトも 0 | **設計済・未実装** |
| 6 | 会話中の長考は既定 (b)「その場は L1・T2 昇格は事後に非同期」 | DECIDED「R5」 | `conversation.py:101`(δ_think L1=1 tick を前提とした待ち)。T2 経路が無いので (b) の後半は未稼働 | **部分** |
| 7 | 日次内省で gist 化(最大 3 gist/晩・24h ブースト) | DECIDED「U1」 | `resolve.py:1867` は発火の計数のみ | **設計済・未実装** |

### 2-17. v2-persona-dynamics-research(ペルソナ動態)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 3 層(L0 不変核/L1 緩変数/L2 速変数)・**習慣表は L1** | DECIDED「ペルソナ動態」 | `src/` にペルソナ 3 層のレジストリは無い。`build/pop/pool.py`・`build/sched/pool_facts.py` が生成時に persona を使うのみ | **設計済・未実装** |
| 2 | persona 文は**不変**・変化は内省 gist の追記で表す | DECIDED「ペルソナ動態」 | `perception/renderer.py:23-26`「B1 から年代・性別を落とした(個体依存語)」。**persona 文は B ブロックに載っていない**=不変以前に未搭載 | **部分** |
| 3 | 近況 gist 2 本を B5(220 tok)の内数に | 知覚契約 §3.2 | `channels.py:127-135` の B5 は近接/内受容/自己状態/被注視の 4 チャネルのみ。**近況 gist の欄が無い** | **設計済・未実装** |
| 4 | ドリフト予算(traits L∞=0・persona 文ハッシュ不変・選好 L1≤0.10・習慣入替 ≤1件/体/30日) | DECIDED「ペルソナ動態」 | `src/` に traits も選好ベクトルも無い。ドリフト予算のテストも無い | **設計済・未実装** |
| 5 | ablation A/B/C(凍結 vs 変化ペルソナ) | 「第2陣」 | `ablations_v1.json` に無し | **設計済・未実装** |
| 6 | 関係は「辺の集合=L1・強度=L2」に分ける | DECIDED「R4 4」と整合 | 関係辺が無い | **設計済・未実装** |

### 2-18. v2-population-synthesis-research(母集団合成)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 7 段手順(在庫棚卸し→目標体数→層化抽出→raking→方面 OD→セル割当→スケジュール) | DECIDED「母集団合成」 | `build/pop/w16_population.py`・`fitting.py`(IPF raking)・`build/sched/w17_schedule.py`。390,188 体(IMPLEMENTED #14) | **実装済** |
| 2 | raking の合否= SRMSE(性別 <0.01・年齢 <0.13) | DECIDED「母集団合成」 | 実測 性別 3e-06・年齢 1.4e-04(IMPLEMENTED #14)+`tests/build_pop/` | **実装済** |
| 3 | `residence_line`(方面)の一様を大都市交通センサス OD へ置換 | DECIDED「母集団合成」・E-1 | 方面 JSD 8.5e-04(IMPLEMENTED #14)・`w12_external_nodes.py:55` | **実装済** |
| 4 | 5,000 体は**二層抽出**(定員先取り層は縮尺しない) | DECIDED「母集団合成(追補)」 | `build/pop/w16_population.py`(二層抽出・役割ベース定員層 769・IMPLEMENTED #15) | **実装済** |
| 5 | holdout を汚さない担保 3 点(抽出重みに KDDI を使わない・比較は外側・触ったら降格) | DECIDED・`data/ground_truth/registry.yaml` | `tools/c7/holdout_compare.py` が抽出パイプラインの外。`registry.yaml` に `split` | **実装済** |
| 6 | expedient E-1〜E-9(方面一様・`is_foreign`=30%・来街者全件 rail・traits 写像 ほか) | 実装計画書 §8 | 感度台帳に W 系の行(`S-W16-FLOOR` 等)はあり E-1 相当は解消済み。**E-2〜E-9 に対応する行は見当たらない**(`docs/bench/c8/sensitivity_v1.md` 19 行) | **部分** |
| 7 | 段2 強制修正率 <20% | DECIDED | W17 v2 実測 0.187(IMPLEMENTED #15)・v2 第2回は修復なし(#19) | **実装済** |

### 2-19. v2-world-coverage-index-research(世界被覆指標)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 5 値ベクトル `(C,Q,D,V,R)`+X+孤児・**加重和にしない** | DECIDED「世界被覆指標」・`v2-methodology.md` | `build/audit/w18_coverage.py:147 compute_index`・`:210`(Q)・`:219`(orphans) | **実装済** |
| 2 | 分母は**凍結カタログ全体**(実装済みだけでない) | 同上 | `w18_coverage.py:11-13` の式・`manifest/world_catalog.py`(凍結 SHA 34f9fa9d) | **実装済** |
| 3 | 重み `w=1+log10(1+N_real)`(上限 6) | 同上 | `w18_coverage.weight():140` | **実装済** |
| 4 | WC-5(過剰)と WC-6(孤児)のみゲート・他は報告 | 同上 | `w18_coverage.py:334-338`(`C.Gate` の閾値: X は None=報告・orphans は 0=ゲート) | **実装済** |
| 5 | REACH は宣言でなく**実測**(ランタイムで実読 >0) | 同上 | `w18_coverage.py:309`「VERIFIED は構築時に評価しない(全 false)」。**REACH もランタイム実測ではなく構築時の宣言ベース** | **部分** |
| 6 | パターン台帳との**逆引き表を自動生成**し「支える世界クラス 0 本のパターン行」を検出 | 同上 | `w18_coverage.py:280`「クラス → それを埋める構築段階。パターン台帳側の逆引き」。**「0 本のパターン行」の検出は見当たらない** | **部分** |

### 2-20. v2-world-data-build-research(世界データ構築 W0-W20)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 構築パイプライン段階表(W0-W20)・純関数+ヘッダ(input_hash/param_hash) | DECIDED「世界データ構築仕様」 | `build/geo/`・`build/field/`・`build/lang/`・`build/vis/`・`build/audit/`(17 段階・IMPLEMENTED #11) | **実装済** |
| 2 | 決定論とハッシュ固定(再構築で `build_hash` 一致) | 同上 §7.2 | `build_hash f5566f5f`(#11)→ `0100706b`(#14)→ `4acb4eb3`(#15) | **実装済** |
| 3 | 格子∩街区のセル生成(2 解像度: 場所セル 100 m・可視性 2.5 m) | DECIDED「R3-5」 | `build/geo/w2_cells.py`(453 セル)+`build/vis/w8_visibility.py`(2.5 m) | **実装済** |
| 4 | POI 営業時間・価格帯の欠損を法規上限+チェーン公式表+上位 300 手入力で埋める | DECIDED「D-W8 上書き最大化」 | `build/field/w7_planspec.py`(PlanSpec 2,337・法規上限・OSM 上書き 477)。**チェーン公式表・上位 300 手入力は未実施**(R-21) | **部分** |
| 5 | 可視性テーブルの前計算(≤512 MB・≤5 分) | 予算 **M10** | 実測 5.87 MB・1.15 s(#11) | **実装済** |
| 6 | 混雑場の初期「平常密度地図」は KDDI からは作れない(訂正) | DECIDED(holdout 保護) | 密度は実行時の在圏から算出(`engine/processes/crowd.py`) | **実装済** |
| 7 | 気象は実日ブートストラップ乱択で「特定日を再生」 | DECIDED「D-W15」 | `build/field/w13_weather.py`(アメダス 35 日・etrn 補完 301 h) | **実装済** |
| 8 | 出典表示(ライセンス)の要件 | CLAUDE.md §7 | `docs/data-license-ledger.md`(83 行) | **実装済** |

### 2-21. v2-world-data-build-round2-research(騒音・気象・PLATEAU・法規)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | A1 ASJ RTN-Model 2018 音響パワーレベル式 | 世界データ構築仕様 §4 | `build/field/w10_noise.py:56 ASJ_COEFF`・`l_wa():219`・`laeq_at():300` | **実装済** |
| 2 | A2 道路交通センサス令和3年度 箇所別基本表 | 同上 | `w10_noise.read_kasyo():131`・`route_match():197` | **実装済** |
| 3 | A5 群衆騒音の密度→LAeq 式(**要約経由・親未読=採用前に一次確認**) | R3-7 の密度項 | 未実装(§2-5 #2 と同じ) | **設計済・未実装** |
| 4 | B1/B2 気象庁 過去の気象データ・北の丸移転の差 | D-W13 | `build/field/w13_weather.py:7`(点番号 44132・北の丸公園)・`:40`(etrn 47662) | **実装済** |
| 5 | B3 環境省 WBGT | 同上 | `w13_weather.py:13`(WBGT 推定+B3 語彙)。**実況値 API は未取得=推定式**(`:17` に宣言) | **部分** |
| 6 | B5 営業時間の法規上限(条文) | D-W8 | `build/field/w7_planspec.py:57-125 LAW_CAPS` | **実装済** |
| 7 | B6 OSM `levels`→高さ既定(`h_floor=3.0 m`・levels≠2 のときだけ信じる) | D-W5 | `build/geo/w4_heights.py:3-8` | **実装済** |
| 8 | B4 PLATEAU ライセンス | CLAUDE.md §7 | `docs/data-license-ledger.md` | **実装済** |

### 2-22. v2-world-process-inventory-research(世界過程の棚卸し)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | **中核提案 U-Goods**(`move_goods` 単一 API・faucet/sink・棚卸差異・退蔵・検算) | DECIDED「世界過程拡張(R6)」 | `economy/goods.py`(`move_goods`)+`world/processes/first_batch.py:262 _GOODS`・`:283 _SHELF`+`tests/economy/` | **実装済** |
| 2 | 廃棄 sink の月次総量 ≈ 区ごみ実数(119.6 t/日)の band 照合 | 同上 | `engine/processes/logistics.py`(廃棄物収集)+`economy/anchors.py`。band ゲートは日次センサス側 | **実装済** |
| 3 | 第1陣: 店舗補充・納品・廃棄物収集・屋内占有・断面自動車交通 | DECIDED「D-R2-5 第1陣」 | `engine/processes/`(21 過程・IMPLEMENTED #13)・`first_batch.py` | **実装済** |
| 4 | 第2陣: 宅配・バス/タクシー・公共サービス出動・インフラ・ホテル・工事・報道・大規模イベント | DECIDED「第2陣」+「陣分けは可能な限り初回実装で」 | `engine/processes/logistics.py`・`civic.py`(宅配/バス/出動/清掃/インフラ/ホテル/工事/報道/大規模イベント・IMPLEMENTED #13) | **実装済** |
| 5 | 第3陣: 不動産・家賃・開発 / 災害 / 税・行政サービス | 「Phase 3 以降」 | 税は `Account.TAX` のみ。不動産・災害は無し | **設計済・未実装** |
| 6 | 保留: 配電網・水道管網・通信網・PV(D-R2-4 (a)(b) 不成立) | DECIDED(保留) | — | **未採用**(理由の記録あり) |
| 7 | 予算・状態成長への申し送り(D-R2-6 適用) | DECIDED「D-R2-6」 | `core/growth.py`+`engine/growth_decl.py`+`first_batch` 各行の `growth=_g(...)` | **実装済** |

### 2-23. v2-crowd-physics-research(群衆物理 U15・**A 等級**)

| # | 推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 方式 = **CFSM 第1候補**・AVM 第2・SFM 対照・ORCA/連続体 不採用 | DECIDED「R7 群衆物理」・`v2-crowd-physics.md` | `src/` に CFSM は無い。**第210 の G13(ユーザー案)で「物理エンジンは表を作る側にだけ使い tick 内は表・解析式」に方針転換** | **未採用**(理由の記録あり=G13) |
| 2 | 較正: Weidmann v_free 1.34・ρ_max 5.4・γ 1.913 | DECIDED「R7」→ C9 §4 | `engine/geometry.py kladek_speed_factor`(γ=1.913・ρ_max 5.4)+`tests/engine/`(IMPLEMENTED #27) | **実装済** |
| 3 | 自由速度は 1.00–1.60 m/s の個体分布(Bosina & Weidmann 2018) | DECIDED「C9 G2」 | `engine/geometry.desired_speeds`(Uniform(1.00,1.60)・seed+agent_id から決定論) | **実装済** |
| 4 | Fruin LOS の基本図・幾何別に較正(単一基本図への較正は誤り) | DECIDED「C9 §4 改訂」 | `world/state.py:72 DENSITY_STAGE_EDGES_PER_M2`(Fruin LOS・人/m²)。**幾何別の基本図較正は未実施** | **部分** |
| 5 | GPU = Warp HashGrid+カーネル 2 本 | DECIDED「R7」・実装計画書 | `src/` に Warp カーネルは無い(numba は `build/geo/w3_distances.py` のみ) | **未採用**(G13 の帰結・理由の記録あり) |
| 6 | dt 掃引(0.01〜1.0)の収束テスト | DECIDED「R7 U15-8」 | 未実施。C9a は 1 分 tick 内で解析式(`MAX_HOPS_PER_TICK=32`) | **設計済・未実装** |
| 7 | 検証指標: 基本図 RMSE・幅線形性・order parameter・破綻統計 | DECIDED「R7」 | 破綻統計に相当する「詰まり 0」の受入はあるが(IMPLEMENTED #27)、4 指標の計器は無い | **部分** |
| 8 | 改札 56 人/台/分・エスカレーター 95.3/107.8 人/分・信号 140 秒 | DECIDED「R7」 | `src/` に該当定数は**無い**(`grep 56.1/95.3/107.8` = 0 件) | **設計済・未実装** |

### 2-24. v2-dashboard-verification-orchestration-research(計器盤・検収・オーケストレーション・**A 等級**)

| # | 推奨(A-F) | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | A 計器盤 3 面(較正面=報告/holdout 面=唯一のゲート/運用面) | DECIDED「R14 G-1」 | `tools/c8/dashboard.py`+`tests/c8/test_dashboard.py` | **実装済** |
| 2 | B 検収 = TRACE 8 ブロックを工程別受入基準表へ写像 | DECIDED「R14 G-2」・実装計画書 §9 | `docs/ops/build-report-C0..C6.md`(工程別受入報告)。**TRACE 8 見出しへの写像は文書に無い** | **部分** |
| 3 | C オーケストレーション = `EnsembleSpec`(seed 群)と `SweepSpec`(掃引)の 2 型・`seed=f(manifest_sha, run_index)`・逐次書き出し・完了済みラン表で再開 | DECIDED「R14 G-3」 | `tools/c8/c8lib.py`・`ensemble.py`(`EnsembleSpec`/`SweepSpec`)+`tests/c8/test_ensemble.py` | **実装済** |
| 4 | D アンサンブル計器 = CRPS+spread-skill+スコアカード | DECIDED「R14」 | `tools/c8/c8lib.py`・`ensemble.py`(CRPS・spread-skill) | **実装済** |
| 5 | E 事前登録 = ADEMP 5 見出し+ラン本数の MCSE 逆算+凍結ファイル | DECIDED「R14」 | `docs/bench/c7/prereg_arms_v1.md`(v1.1/v1.2/v1.3 草案)。**ADEMP 5 見出しの形にはなっていない**・MCSE 逆算は R-25 で後から入った | **部分** |
| 6 | SBC(片側性)・History Matching(I≤3・NROY) | DECIDED「R14 G-1」 | `tools/c8/dashboard.py`・`ensemble.py`(`SBC`・`implausibility`) | **実装済** |
| 7 | mlflow Tracking の採用候補 | DECIDED「R14 **G-7**」= 自前ラン表(Parquet)+DuckDB | `tools/c8/ensemble.py:20,182`「mlflow は **Phase 5 の閲覧用アダプタとして後付け**」と理由つきで記録 | **未採用**(理由の記録あり) |

### 2-25. v2-c7-fix-research(C7 の 2 つの歪み)

| # | 推奨既定値 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | `DWELL_TICKS` 通過型 1・終端 2 | D-51 | `engine/processes/rail.py:118 DWELL_TICKS=1`・`:123 DWELL_TICKS_TERMINAL=2`・`:128 DWELL_TICKS_BY_LINE` | **実装済** |
| 2 | 「乗車を決めてから乗る」まで 3〜7 分の過程をエンジンに入れる | D-51(c) 乗車意図の保持 | `agents/state.py:413 board_line`・`:416 board_since`(最寄りホーム→FIFO→停車で乗車・打ち切り 30 tick=expedient・IMPLEMENTED #17) | **実装済** |
| 3 | 線別混雑率(2025 値・山手 135/136 ほか) | 運用設計書 §2.6 | `engine/processes/rail.py:11-13`(混雑率上限型・受容関数 expedient) | **実装済** |
| 4 | a(h)(時刻別起床率)24 行 | D-56 | `engine/arbiter.py:71-74`(a(h) を逐語で持つ)・`engine/run.py:520 起床率(在圏)/時` | **実装済** |
| 5 | `budget(h) = 総予算 × a(h)/mean(a)` で tick 呼数上限を可変に | — | `arbiter.py:74`「**a(h) は一律に掛けない**…a(h) は検証にだけ使う」=**明示的に採らなかった**(交替制 12.9% が消えるため) | **未採用**(理由の記録あり) |
| 6 | 層別 3 層(交替制/若年/その他)で就寝判定を分ける | — | `src/` に層別の a(h) は無い。就寝は W17 の計画に従う(D-62) | **部分** |
| 7 | ホーム到着分布(発車 2:30 前ピークの正規分布)は将来 tick 細分化用 | — | 未実装(1 分 tick では使えないと答申が明記) | **未採用**(理由の記録あり) |

### 2-26. v2-d66-outside-residents-research(域外居住者の到着・退出)

| # | アンカー/推奨 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 帰宅時刻分布(大都市交通センサス 第12回+社会生活基本調査 第4-1表の 2 系列) | `v2-d66-outside-residents-agenda.md`・`v2-plan-executor-design.md` | `engine/presence.py`(日次イベント列 ARRIVE/DEPART/SLEEP/WAKE・IMPLEMENTED #18) | **実装済** |
| 2 | 駅別×時刻別の公表表は**存在しない**(裏取り済み) | 残務 §6「再探索しない」 | — | **実装済**(空欄の確定として) |
| 3 | 国勢調査 令和2年 町丁目別 昼間/夜間人口 | 事前登録 v1 の物差し | `tools/c7/presence_yardstick.py`(現実の帯 1.5〜3 万・昼 13〜14.5 万) | **実装済** |
| 4 | 出勤率(テレワーク実施率+年休)→「登録通勤者のうち当日来る比率」 | D-67 (b) | `cli` `--attendance-rate`+事前登録の腕 5(0.88) | **実装済** |
| 5 | E8 到着分散・E1 間に合う最遅便・出口セル分散 | `v2-plan-executor-design.md` | `engine/presence.py`(E1/E8/E12・`_spread_arrivals`・`_assign_return`) | **実装済** |
| 6 | 訪日客の扱い(★ 種別から外し「宿泊施設で就寝(参考)」へ) | D-66 の物差し訂正 | `presence_yardstick.D66_KINDS=(0,1,6,8)`・`LODGING_KINDS=(7,)`(IMPLEMENTED #20) | **実装済** |
| 7 | 来街者の来訪頻度の公的分布は**見つからず** | 残務 §6 | — | **実装済**(空欄の確定として) |

### 2-27. v2-d68-behavioral-diversity-research(行動の多様性)

| # | 推奨/アンカー | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 予測可能性 93%(Song 2010)・17 モチーフで 90%(Schneider 2013)を多様性の物差しに | D-68・`v2-d68-pilot-design.md` | `tools/w17/diversity_yardstick.py`(種類率・エントロピー)。**モチーフ数・Π(予測可能性)の計器は無い** | **部分** |
| 2 | LLM の同質化を測る(モデルサイズ 7-8B vs 27-70B の差) | D-68 経路 | 指標B 8B 違反率 0.123 vs 14B 0.003(IMPLEMENTED #16)・W17 v2 の H 2.41→4.83 bit(#19) | **実装済** |
| 3 | 「出勤」≠ 始業時刻(重大な注意) | D-68・W17 v2 の物差し | `tools/w17/`(出勤代理 :00/:30 0.649 vs 現実 0.675・#19) | **実装済** |
| 4 | 個人内規則性は高く個人間多様性が本体=**エンジン規則で分散を作らない** | CLAUDE.md §3(LLM ネイティブな多様性)・AB7 | `perception/templates.INTENT_MODES`・`--intent-mode {vocab,open,hint}`(IMPLEMENTED #21・#23) | **実装済** |
| 5 | ActivitySim の個人差の作り方(CDAP)を借りる | 母集団合成 Q4 | `build/sched/w17_schedule.py` は LLM 生成(CDAP は採らず) | **未採用**(理由の記録=LLM ネイティブ方針) |
| 6 | 経路 3(記憶・習慣)で同質性に当たる | D-68 → D-81 | 記憶・習慣が未実装 | **設計済・未実装** |

### 2-28. v2-llm-social-sim-timeline-seed(LLM 社会シミュの現在地・未正典化)

| # | 内容 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 17 件の確認表 → 本文実読(R-2)へ | R-2 完了(第202) | `docs/research/v2-r2-llm-social-sim-fulltext-check.md`+`docs/research/lit/`(12 本) | **実装済** |
| 2 | この repo の位置づけ(流れの一句) | `v2_significance.md`・`v2-inventory-and-bottlenecks.md` | — | **実装済**(文書として) |
| 3 | OASIS 超線形 N^1.5・事前登録の外部根拠は Larooij の 1 行のみ | D-75・D-70 | `PENDING.md`(D-70/D-75) | **設計済・未実装** |
| 4 | TRAILS-R 5 次元が v2 に空白(v1 S-16 の置換忘れ) | D-75 (d) | `docs/bench/c8/trails_coverage_v0.md`(被覆表 v0=**どの次元を監査していないかの宣言**)。**腕は増やしていない**(第2波=D-75 (e)・`ablate.prompt_paraphrase` の復活は判断待ち) | **部分** |
| 5 | 同時代の作品(AUTOMATA HACKATHON 38 作品) | — | 参照のみ | **未判定**(決定への接続なし) |

### 2-29. v2-replication-count-research(反復回数・**A 等級**)

| # | 含意 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | **G-8「初回 seed 群 8 本」は文献系譜では正当化できない**(2〜3 桁不足) | D-70・D-44・G-8 | `PENDING.md` D-70/D-44 に記載。`tools/c8/ablations_v1.json` の `totals` は 8〜18 ラン | **設計済・未実装**(G-8 の記述は据え置き) |
| 2 | 正当化できる唯一の枠= ECMWF の R&D 枠(小アンサンブル+fair score) | 事前登録 v1.3 草案「fair CRPS +33%」 | `tools/c8/ensemble.py:214 crps_ensemble` は `mean|x−y| − ½·mean_{i,j}|x_i−x_j|`(**i=j を含む標本推定量=有限 M の正のバイアスを引かない非 fair 形**)。`:36`「分解は未実装」と自認 | **設計済・未実装** |
| 3 | 検出可能効果量の床(≈1.6〜2.1 seed 間 SD)を台帳に明示宣言 | D-79・prereg v1.3 | `tools/fig/fig_seed_pair.py`(CV(n=2)・N=(CV/r)²・IMPLEMENTED #24) | **部分** |
| 4 | seed の交換可能性の検査(温度・初期配置・母集団抽出が同一分布か) | — | `src/`・`tools/` に交換可能性の検査は無い | **未判定**(**取りこぼし候補**) |
| 5 | 稀な行動の指標に c_V は不向き(窓付き分散か検出力設計へ) | prereg v1.3 「深夜は記述に格下げ」 | `docs/bench/c7/prereg_arms_v1.md:71`(第209 注記) | **実装済**(文書として) |

### 2-30. v2-w7-law-primary-check-research(W7 法規・**A 等級**)

| # | 指摘(D-72) | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | ① 地域条件が世界に無い(一律適用)→ expedient 未登録 | D-72 (a) | `build/field/w7_planspec.py` の `EXPEDIENTS` に法規の穴 5 行を追加(IMPLEMENTED #23)+`tests/build_field/test_field_units.py` 4 本 | **実装済**(登録として。**地域条件そのものは未実装**) |
| 2 | ② citation の条ずれ(規則 6 条 2 項=時/地域=条例 4 条の 2 第 2 項+規則 5 条+告示) | D-72 (a) | `w7_planspec.py`(citation 訂正・#23) | **実装済** |
| 3 | ③ `violability` が青少年条例 16 条違反を「unenforced」にする | D-72 | `EXPEDIENTS` に「violability 保留」として登録(#23)。**判定ロジックは未修正** | **部分** |
| 4 | ④ 条例 8 条(ゲーセン)・6 条(騒音 dB)が設計書にあってコードに無い | D-72 | 未実装 | **設計済・未実装** |
| 5 | ⑤ 立入制限(風営法 22 条 1 項 4/5/6 号・18 条掲示・32 条 3 項) | D-72 | 未実装。W14 は 18 条の入口掲示を生成しない | **設計済・未実装** |
| 6 | ⑦ 特別日の延長が無い | D-72 (a) | `EXPEDIENTS` に「特別日なし」として登録(#23) | **実装済**(登録として) |
| 7 | ⑧ 興行場・ボウリング等が `minor_entry_limit` に未写像 | D-72 | 未実装 | **設計済・未実装** |
| 8 | ⑥ 別件: 品質プローブが「用途地域は第 4 種区域です」(体系の取り違え) | サブ報告 | `tools/quality_probe_v0/build_probes.py` は未修正 | **未判定**(D-72 の外・修正記録なし) |

### 2-31. v2-c9-geometry-capacity-research(幾何に基づく容量)

| # | 置換候補 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | 歩行可能面積を PLATEAU TrafficArea 実測(中央値 1,752 m²)へ | C9 アジェンダ G8(判断待ち) | `src/` に `walkable_m2`・`TrafficArea` は無い。現行は `perception/renderer.py:100 STREET_POINT_AREA_M2=6.25` | **設計済・未実装** |
| 2 | 現行式は「歩行可能面積」でなく「道路面(車道込み)」相当(事実の訂正) | 同上 | 訂正は答申にのみ。設計書 §4 改訂に反映 | **部分** |
| 3 | 店舗床面積を特別区部 小売業の分布(中央値 80.6 m²)へ | G8 | `src/` に `floor_area` は無い | **設計済・未実装** |
| 4 | 1 席面積(物販 4.0 / 飲食 3.0 m²)を mechanism へ昇格 | G8 | `src/` に `seat_area` は無い | **設計済・未実装** |
| 5 | ホーム滞留容量 3.30 人/m²(R-8 ④ の空欄を解消) | G8 | 未実装 | **設計済・未実装** |
| 6 | 改札 56.1 人/分・台/エスカレーター 95.25・107.8(一次出所確認) | G8 | 未実装 | **設計済・未実装** |
| 7 | ホーム面積・コンコース滞留密度・飲食店客席面積の業界標準は**見つからず** | 空欄 | — | **実装済**(空欄の確定として) |

### 2-32. v2-d68-remaining-research(記憶・習慣の残 10 件)

| # | 決定アジェンダ候補 | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | K-1 習慣の表現(何を状態として持つか) | D-81(判断待ち) | 未実装 | **設計済・未実装** |
| 2 | K-2 日々の変動の幅(どこを合格とするか) | D-81 | 未実装 | **設計済・未実装** |
| 3 | K-3 モチーフ数(11〜17 型/83〜90%)の門番の帯 | D-81 | `tools/w17/diversity_yardstick.py` にモチーフ計器なし | **設計済・未実装** |
| 4 | K-4 予測可能性の上限(Lu 2013 Π 0.88・Song 93%) | D-81 | 未実装 | **設計済・未実装** |
| 5 | K-5 時刻の投入(時間帯編 第15-4表・住宅土地統計 58-2-1・交替制) | D-81 | `arbiter.py:71-74` が a(h) を持つが、始業時刻分布・通勤時間分布は未投入 | **部分** |
| 6 | 始業時刻の公的分布表は**存在しない**(代理=時間帯編 第15-4表) | 空欄の確定 | — | **実装済**(空欄の確定として) |
| 7 | TrajLLM の定量評価は**存在しない** | 空欄の確定 | — | **実装済**(空欄の確定として) |

### 2-33. v2-d71-vocab-growth-research(行動語彙を育てる仕組み)

| # | 決定項(A-J) | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | A 閾値 N を「意味の閾値」でなく**予算**として定義し直す(全件保持+被覆順位) | `v2-vocab-growth-design.md` | `tools/vocab/adjudicate.py`(全件保持・被覆順位 体数×セル数×時間帯数・件数予算 10・下限 N=10)+`tests/vocab`(IMPLEMENTED #25) | **実装済** |
| 2 | B 草案は 6 欄+「失敗コード名」「保存則の科目」「テスト ID」を必須欄に | 同上 | `adjudicate.py`(必須 10 欄・プロンプト `vocab-draft-v0` sha 6acda67c) | **実装済** |
| 3 | C 4 検査(正しさ/使用/妥当性/非退化) | 同上 | 段3 静的検査 s1〜s6 は実装(#25)。**動的検査 ①③④ は語彙 v2 側で実施・② は AB7c 待ち** | **部分** |
| 4 | D オフラインバッチ(ラン後)を採る | ユーザー決定 | `tools/vocab/`(オフライン) | **実装済** |
| 5 | E オブジェクトの affordance を足す(語彙は直積) | DECIDED「原則 行動はオブジェクトの affordance 由来」(09-17) | `llm/contract.ACTION_WORD_EAT`+`world.eatery_mask`+`resolve._apply_eat`(IMPLEMENTED #26) | **実装済** |
| 6 | F 版はランの開始前にのみ切る・manifest に載せる・旧テープは旧版で読む | 語彙政策 v0 | `manifest` の `vocab_version`/`synonym_table_version`(#26)。**「旧テープは旧版で読む」の機構は無い** | **部分** |
| 7 | G 指紋 6 つを宣言(閾値 N/欄と並び/裁定モデルと温度/合格線/採用順序/版の切り方) | 同上 | `adjudicate.py` が drafts.json に指紋 6 つを記録(#25) | **実装済** |
| 8 | J 剪定(使用率の計測だけ先に入れる) | 同上 | `manifest` の `action_usage`(#26) | **実装済** |

### 2-34. v2-statistics-causal-research(多重比較・同値検定・CRN・反実仮想)

| # | 決定アジェンダ(S-1〜S-5) | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | S-1 事前登録 v1.3(5 指標を家族・Bonferroni α=0.01・同値検定・GET は記述) | D-79 (a)・prereg §7 v1.3 **草案** | `docs/bench/c7/prereg_arms_v1.md:73-83`。**`tools/c7/holdout_compare.py` に TOST も Bonferroni も無い** | **設計済・未実装** |
| 2 | S-2 D-70 への追加材料(fair score・検出可能効果量の床) | D-70 | `tools/fig/fig_seed_pair.py`(CV・N 逆算) | **部分** |
| 3 | S-3 C8 の解析計画(ablation の対照・**CRN**) | — | `core/rng.py` は Philox ドメイン分離。**腕間で乱数を共通化する CRN の設計は無い** | **未判定**(**取りこぼし候補**) |
| 4 | S-4 反実仮想の主張の作法(SCM・負の対照・S-RCT・History Matching) | 到達点 C(DECIDED 09-17) | `tools/c8/ensemble.py`(implausibility)。**負の対照・S-RCT は無い** | **部分** |
| 5 | S-5 D-44(感度試験の省き方・CSB スクリーニング) | D-44 | 感度台帳は 19 行(`docs/bench/c8/sensitivity_v1.md`・done 6/todo 13)。**CSB(要素効果)スクリーニングの実装は無い** | **設計済・未実装** |
| 6 | GET 大域包絡(seed 3 本では p≥0.25=検定ではない) | prereg v1.3 | 文書に明記済み。計器は無い | **部分** |

### 2-35. v2-c9-position-attention-research(位置・速度・注意・会話距離・目印)

| # | 含意(A-G) | 設計 | 実装 | 判定 |
|---|---|---|---|---|
| 1 | A G1 (b) 辺上連続位置を推奨 | DECIDED「C9 G1 (b)」 | `engine/geometry.EdgeGeometry`+`agents/state.py:354 edge_id`・`:357 edge_s`(IMPLEMENTED #27) | **実装済** |
| 2 | B G2 の「年齢係数(1.00〜1.60)」は読み違い → 希望速度 m/s の幅へ文言修正・年齢配分はやらない | C9 アジェンダ §4 改訂 | `engine/geometry.desired_speeds`(Uniform(1.00,1.60) m/s・年齢なし) | **実装済** |
| 3 | C 現行の密度段階は 7 段すべて Fruin LOS A の内側 → 刻みを LOS 境界に合わせ直す | C9 §4 改訂 | `world/state.py:72 DENSITY_STAGE_EDGES_PER_M2`(Fruin LOS・edge のときのみ。node の段は不変) | **実装済** |
| 4 | D G4 に「焦点の寿命」と「喪失距離 > 取得距離」を足す | C9 G4 | `agents/state.py:362 focus_target`・`:366 focus_ttl`+`resolve.py:159 FOCUS_TTL_TICKS=10`・`:162 FOCUS_ACQUIRE_M=20`/`FOCUS_LOSE_M=30`(**未コミット**) | **実装済(未コミット)** |
| 5 | E G3「近づく」は到達距離でなく**終了条件**(UE の Auto Success Range 型) | C9 G3 | `resolve.py:157 APPROACH_DONE_M=2.0`+`ResultCode.TARGET_GONE`(#27)(**一部未コミット**) | **部分** |
| 6 | F G6 目印は POI の `cat` でなく **W8 の可視領域の重なり**から出す(第2案の併記) | C9 G6(判断待ち) | `src/` に目印の機構は無い | **設計済・未実装** |
| 7 | G G7 会話 2 m は裏づけられる・**密度で縮める根拠は無い**・成立と離脱で別の値 | C9 G7 | `resolve.py:166 TALK_OPEN_METERS=2.0`・`:168 TALK_LEAVE_METERS=3.0`(**未コミット**)。従来は `conversation.py:80 D_TALK_METERS=1.0` | **実装済(未コミット)** |

---

## 3. 取りこぼし候補と「設計済・未実装」の優先一覧(上位 20)

優先度 = その答申の重要度(全て P0)× 決定への影響(いま走っているランの主張に効くか)× 手当ての安さ。

| 順 | 種別 | 項 | 出所 | なぜ効くか | 根拠 |
|---|---|---|---|---|---|
| 1 | 未判定 | **`ACCEPT_PROBABILITY=0.8` の感度腕が無い** | batch2 §4-C の推奨③ | 会話は呼数の 45% を占める設計。0.8 は一次出典が無いと親自身が確認した数値なのに ablation 腕が無い | `ablations_v1.json`(AB1〜AB7c に無し)・`conversation.py:82` |
| 2 | 設計済・未実装 | **U10 案B(重力抽選)の下限対照 ablation** | boundary-economy 6-a | 「案A が案B より良い」を示す唯一の方法だと答申が明記。いまの帰無腕は旧挙動であって重力モデルではない | `v2-boundary-economy-design.md:22`・`ablations_v1.json` |
| 3 | 設計済・未実装 | **感度試験 19 行のうち「駆動していない」と結論できたのは 1 行だけ** | 方法論 §expedient タグ | CLAUDE.md §4 の中核義務。実行済 6 行も構築対照のみで 5 行が「ラン対照が要る」止まり | `docs/bench/c8/sensitivity_v1.md`(done 6/todo 13)・`tools/c8/sensitivity_v1.json` |
| 4 | 設計済・未実装 | **T2 日次内省の実呼が無い**(発火の記録のみ) | update-rules 5-(b)・cognition 5-1 | 予算 L5(42 万呼/日=L4 の 10.5%)を宣言済みで、認知 3 層の T2 が一度も回っていない | `resolve.py:1840,1867`・`llm_bridge.py:8` |
| 5 | 設計済・未実装 | **記憶(M4)・関係辺(M5)・習慣(M3)・ペルソナ(M6)の 4 レジストリ** | action-conversation (c)・cognition 5-4・persona Q6 | 認知 3 層の背骨。D-68 経路 3(同質性)も D-81 もここに依存 | `agents/state.py:8,26` |
| 6 | 未判定 | **観測の「なし」を書かない規約が逆になっている** | observation-format 4-3 #5 | 否定文が LLM の注意を引きすぎるという実証的推奨。空セルが多い渋谷では毎呼発火する | `templates.py:436,453,457,459` |
| 7 | 設計済・未実装 | **prereg v1.3 の統計(Bonferroni・TOST・GET)が計器に無い** | statistics S-1 | holdout 開封は 1 セッション限り。開封時に計器が無ければ主張の形が作れない | `tools/c7/holdout_compare.py`・`prereg_arms_v1.md:73-83` |
| 8 | 未判定 | **seed の交換可能性の検査** | replication §3 | 小アンサンブル+fair score が唯一の正当化枠で、その前提条件 | `tools/c8/` に無し |
| 9 | 設計済・未実装 | **保存則テスト T3(冗長方程式の毎期 assert)** | batch2 §4-E | SFC 標準の検証法。検算 2 本で包含できているかは未確認のまま | `economy/checks.py`・`v2-boundary-economy-design.md:59` |
| 10 | 未判定 | **δ_perc の対数正規分散と `m_att`** | latency ④-1/④-5 | 「顕著行為 1 件で同一セルの数百体が同時起床」を散らす装置。いまは定数なので散らない | `commit.py:185-192` |
| 11 | 設計済・未実装 | **C9 幾何容量の置換値 6 件**(歩行可能面積・店舗床・席面積・ホーム 3.30・改札・エスカレーター) | c9-geometry §3 | 現行の `max(街路点数×6.25, 1500)` は「道路面(車道込み)」相当で、歩道部との比は 0.382。容量が 2.6 倍過大の可能性 | `renderer.py:100`・答申 §1-1 a11 |
| 12 | 未採用(**理由の記録なし**) | **広告の「スカラー変換を第一候補に」が採否の記録なく落ちている** | ad-information 4-C(ii) | 収益化の主要領域。背骨(状態と集約はエンジン)との整合を答申が根拠 1 に挙げている。**未採用 11 件のうち理由の記録が無い唯一の項** | `src/` に親近性スカラー無し |
| 13 | 設計済・未実装 | **識別テスト T0(陽性対照ゲート)** | turing 4-2 | 答申が「ゲート化してよい唯一の項目」と名指し。P 層が落ちたら他の結果を報告しない規律の土台 | `tools/` に識別器無し |
| 14 | 部分 | **REACH がランタイム実測でなく構築時の宣言** | world-coverage 問い5 ③ | 虚栄指標化の防止 5 本のうち 1 本が効いていない | `w18_coverage.py:309` |
| 15 | 設計済・未実装 | **聴覚の密度項(群衆騒音)と半径導出関数** | density-hearing ④-1 | 「混雑は会話より広告の到達を壊す」という最重要の含意が出ない。いまは同一セル代理 | `commit.py:453`・`crowd.py` |
| 16 | 未判定 | **起床時の差分要約(FD 対策)** | timing 4-1 第5条 | dormant 配送の固有リスク。長ランで「観測されていない間の変化」が齟齬として顕在化する | `renderer.py` の B5 に欄無し |
| 17 | 設計済・未実装 | **顕著性アキュムレータ S(t)>θ** | timing 4-2 | 起床トリガ 6 類のうち (e) が無い。いまの顕著性は順位づけ専用 | `attention.rank_by_saliency` |
| 18 | 未判定 | **観測共有ブロックの固定行数パディング** | observation-format 4-2 #6 | `[C]` の行数が揺れると `[D]` の位置が動き prefix 境界が動く=1.6-2.0x の利得が痩せる | `renderer.py`・契約書に条文なし |
| 19 | 設計済・未実装 | **W7 立入制限・条例 8 条/6 条・特別日** | w7-law §3 ④⑤⑦ | 「世界に年齢による立入の制約が無い」=U18(犯罪創発)の入口が塞がっている | `w7_planspec.py` |
| 20 | 未判定 | **CRN(共通乱数)の腕間共通化** | statistics S-3 | ablation の対照の分散低減。C8 の全腕がこれに乗る | `core/rng.py` はドメイン分離のみ |

**「未判定」10 件の全件**(§2 の判定から機械抽出):

| 出所 | 項 |
|---|---|
| 2-3 #2 | 動的物体の遮蔽(低解像度セグメンテーション/短距離レイキャスト) |
| 2-5 #6 | 「騒音は移動を駆動しない」を台帳行の完了条件に |
| 2-6 #4 | 文面規約「『なし』を書かない」(実装は逆を向いている) |
| 2-7 #3 | `m_att`(スマホ/会話中 ×2.0)・傍観者倍率 |
| 2-8 #4 | 起床時の差分要約(FD 対策) |
| 2-11 #8 | 「較正が生成分布を変えてよい上限(±5%)」の事前宣言 |
| 2-28 #5 | 同時代の作品(AUTOMATA HACKATHON 38 作品)= 決定への接続なし |
| 2-29 #4 | seed の交換可能性の検査 |
| 2-30 ⑥ | 品質プローブの「第 4 種区域」= 用途地域と騒音区域の取り違え |
| 2-34 S-3 | C8 の解析計画の CRN(共通乱数) |

**「未採用」11 件**(理由の記録あり 10・なし 1): u17 #5(VLA 直結)・#8(嗅覚保留)/ timing #6(周期HB廃止)/ world-process-inventory #6(配電網等の保留)/ crowd-physics #1(CFSM)・#5(Warp HashGrid)=いずれも **G13 による方針転換**/ dashboard #7(mlflow)/ c7-fix #5(budget(h) 一律掛け)・#7(ホーム到着分布)/ d68-behavioral #5(ActivitySim CDAP)/ **ad-information #3(スカラー変換)= 理由の記録なし**。

---

## 4. 逆引き表(DECIDED 行 → 根拠答申)

> INDEX §5 が「無い」と書いているもの。名前で引いていない行は**特徴値 grep**(batch2 §1 の方式)で当てた。
> 「名指し」= 設計書・決定台帳にファイル名がある / 「特徴値」= 数値・固有名詞の一致で同定 / 「ラウンド」= 同じ決定ラウンドの事前リサーチとして時系列で同定。

| DECIDED 行 | 根拠答申(P0) | 引き方 | 特徴値 |
|---|---|---|---|
| R3-1 知覚の正典形 | perception-u17 | ラウンド | 「GPU isovist・渋谷全域2-3分」= u17 §0.2(236,000セル/137秒) |
| R3-2 内受容感覚 | perception-u17 | ラウンド | 「満腹・体力・体感温度の3変数」「Humanoid Agents +156%」 |
| R3-3 看板=届く対象 | ad-information | **名指し**(`v2-redesign.md`) | — |
| R3-5 可視性 2.5 m | perception-u17 / world-data-build | 特徴値 | 「222,400セル」「LOD2 1.39km²」 |
| R3-6a VLM 測定装置 | vlm-reality-check(P1) | **名指し** | — |
| R3-6b 識別テスト | turing-test-validation | **名指し** | — |
| R3-7 騒音・聴覚 | density-hearing-verification / update-rules-hearing | **名指し**(`v2-redesign.md:420`) | 「+3.4dB/倍」「ρ<0.05」「ΔSNR −3/−12」 |
| R3-8 §1 不変条件7条 | observation-format | ラウンド | 「素性タグ必須(ASR>50%→<2%)」 |
| R3-8 §2 契約の型 | observation-format | ラウンド | 「固定2行形」「厳密JSONで 86.51→23.44」 |
| R3-8 §3 チャネル仕様表 | channel-budget-attention / p-notice / update-rules-hearing | ラウンド(3本) | 「B5 220>B2 150」「p_notice 2段ヒル」「不応期 11 行」 |
| R3-8 §4 注意ゲート4段 | channel-budget-attention / ad-information | ラウンド | 「p_see 0.70(音声有0.78/無音0.63)」「round(7.5×注視秒)」 |
| R3-8 §5 prefix規約 | observation-format | ラウンド | 「変化率の昇順」「ハッシュ三役」 |
| R3-8 §6 更新タイミング | update-rules-hearing / perception-latency / perception-timing | ラウンド(3本) | 「GATSim 30/150分」「δ_perc k=0/1.0/1.6/4.9/6.1」「invocation distance」 |
| R3-8 §7 予算delta | perception-timing / p-notice | ラウンド | 「P6 ≤2 ms/tick」「P7 打ち切り80 m・200/tick」 |
| R3-8 §8 検証装置 | perception-timing | ラウンド | 「ablation 優先= expedient量×駆動可能性÷コスト」 |
| R4 行動契約・会話 | action-conversation-contract | ラウンド | 「12語+種別固有」「max_turns 3」「Dunbar 5/15/50/150」 |
| U10 境界=来街 | boundary-economy-u10-u11 | ラウンド | 「外界ノード8-10」「案B=下限対照」 |
| U11 経済SFC | boundary-economy-u10-u11 | ラウンド | 「6部門(銀行含む)」「Caiani 検算2本」 |
| D-R2-3 行5 価格形成 | world-process-rows / price-formation-llm(P1) | **名指し**(price 側) | 「Calvo 改定」「外食 5.0%/月」 |
| D-R2-3 行2/行8/行9/行15/行16 | world-process-rows | ラウンド | 「M/M/c」「Dunbar 層」「OASIS 推薦」「ACT-R」「3層受理」 |
| D-R2-5 陣分け | world-process-inventory | ラウンド | 「第1陣/第2陣/第3陣」「U-Goods」 |
| 世界過程拡張(R6) | world-process-inventory | ラウンド | 「move_goods 単一API」「119.6 t/日」 |
| 世界被覆指標 | world-coverage-index | **名指し**(`v2-methodology.md`) | — |
| 世界データ構築仕様 | world-data-build / world-data-build-round2 | **名指し**(`v2-world-data-build-spec.md`) | — |
| R5/U19 認知詳細 | cognition-detail | ラウンド | 「L1 2.6秒/L2 82秒」「Rubinstein」 |
| ペルソナ動態 | persona-dynamics | ラウンド | 「3層」「persona文不変」「Lally 15-66回」 |
| 母集団合成 | population-synthesis | ラウンド | 「SRMSE」「二層抽出」「CDAP」 |
| R7 群衆物理(U15) | crowd-physics | **名指し**(`v2-redesign.md`) | — |
| R14 計器盤 | dashboard-verification-orchestration | **名指し** | — |
| R15 可視化 | game-frontend(P1・**D等級**) | **名指し** | — |
| R17 倫理・安全 | ethics-operations(P1) | **名指し** | — |
| D1′ 台帳差し替え | area-boundary-definition / d1-reacquisition(P1) | **名指し** | — |
| D-51/D-56/D-62(C7 修正) | c7-fix | ラウンド | 「DWELL 1/2」「a(h) 24行」 |
| D-66 域外居住者 | d66-outside-residents | **名指し**(`v2-d66-outside-residents-agenda.md`) | — |
| D-68 行動多様性 | d68-behavioral-diversity → d68-remaining | **名指し** | — |
| D-70/D-44/G-8 | replication-count / statistics-causal | ラウンド | 「8 seed」「CV」「Bonferroni α=0.01」 |
| D-71 語彙成長 | d71-vocab-growth | **名指し**(`v2-vocab-growth-design.md`) | — |
| D-72 法規の穴 | w7-law-primary-check | **名指し** | — |
| D-78 背骨の訂正 | r23-primary-check-batch2 | **名指し** | — |
| D-79 統計の作法 | statistics-causal | **名指し**(`prereg_arms_v1.md:73`) | — |
| C9 G1〜G13 | c9-position-attention / c9-geometry-capacity | **名指し**(`v2-c9-geometry-brief.md`) | — |
| 原則「行動は affordance 由来」 | d71-vocab-growth | ラウンド | 「SayCan 551=動詞7×オブジェクト17」 |

**逆引きで分かったこと**: **名指しで引かれている P0 は 16 本**、残り 19 本は「同じ決定ラウンドの事前リサーチ」としてしか辿れない。
これは batch1 §1 が P1 で見つけた構図(ファイル名 grep では落ちるが中身は効いている)が **P0 でも同じ**であることを意味する。
決定台帳の各行に「根拠答申」列が無いのが原因で、INDEX §5 の指摘は正しい。

---

## 5. 方法論の遵守表(`v2-methodology.md` の要求 × 実装での担保 × 穴)

| # | 方法論の要求 | 実装での担保(ファイル:行) | 穴 |
|---|---|---|---|
| 1 | **パターン台帳ゲート**(どの現実パターン照合で使うか 1 行) | `world/processes/constitution.py:57 parse_pattern_ledger_ids`・`:104`(照合行 id)・`:21`(封印行を `contributes` に書くのは違反)+`first_batch.py` の全 21 過程が `reaches`/`contributes` を持つ | **`src/shibuya/` の**世界過程以外**(知覚・経済・エンジン核)にはゲートが掛かっていない**。CI で新規モジュールに門を要求する仕組みも無い |
| 2 | **全 cap/近似に `mechanism\|expedient` タグ** | `core/soa.Registry.declare(mechanism=…)`(`agents/state.py` の 37 箇所が `mechanism=False`)+ `src/` 全体で `expedient` の語が 577 箇所 | 宣言は SoA 欄と docstring に偏り、**定数(`D50_DEFAULT_M`・`MAX_TURNS`・`ACCEPT_PROBABILITY` 等)は機械可読なタグを持たない**。登録簿は Markdown(`v2-implementation-plan.md` §8)側にあり、コードと突合する検査が無い |
| 3 | **expedient は感度試験で「結果を駆動していない」証明** | `tools/c8/sensitivity.py`+台帳 2 本(**仕様** `tools/c8/sensitivity_v1.json` 19 行=全行 `todo` / **結果** `docs/bench/c8/sensitivity_v1.json`= **done 6 / todo 13**、表は `docs/bench/c8/sensitivity_v1.md`)。`criterion_note` に片側判定の定義 | **19 行中 13 行が未実行**。実行済 6 行も**全部 `build_rerun`(構築対照)だけ**で、うち 5 行の判定は「**ラン対照が要る**」= 結論未了。「**駆動していない**」と結論できたのは **1 行のみ**(`S-W14-JRPHASE` JSD 0.0000)。つまり CLAUDE.md §4 の証明義務は **19 分の 1** しか果たされていない。D-44(122 expedient × 2 seed = 93 日)が実行不能なまま |
| 4 | **保存則系は実装前に紙上で収支を閉じる** | `docs/design/v2-boundary-economy-design.md`(BS6行+TFM12科目を先に紙で確定)→ `economy/accounts.py`・`checks.py:76,98`・月次 MER(`census.py`)+`tests/economy/` | **T3(冗長方程式の毎期 assert)が落ちている**(§2-1 #5)。物(U-Goods)側は検算①②相当があるが、**廃棄 sink の月次 band 照合は実データとの突合が未実施** |
| 5 | **性能予算(step時間/RSS)とバイト予算を機能追加前に宣言しテストでゲート** | `docs/design/v2-budget-declaration.md`(W/P/M/L/S 系列)+`core/budget.py`+`tests/test_budget_table.py`(33 行の機械読取)。C9a も P2 ≤300 ms/tick@40万体を先に宣言(IMPLEMENTED #27) | **P5(前回比+10%超で失敗)の CI ゲートが実効していない**(`v2-implementation-plan.md:63` が「共有ランナーでは相対ゲート・絶対値はセルフホストの asv のみ」と書くが asv は無い)。予算行 P5/P8/P10(ファンアウト・dormant 抑止率・起床原因内訳)は**予算書に存在しない** |
| 6 | **逐次ループの新設は宣言必須** | 予算書 **P4**+`v2-implementation-plan.md:63`「P4 は AST 検査を試行(expedient)」。C9a のホップ反復は P4 として宣言(#27) | AST 検査は「試行」のままで、**新規の逐次ループを機械的に検出する CI は無い** |
| 7 | **較正データと holdout を最初に分割・較正が holdout に触れない** | `data/ground_truth/registry.yaml`(`split`)+`tools/c7/holdout_compare.py`(開封記録 `holdout_open_record.json`・`previous_openings` 履歴)+`prereg_arms_v1.md` §5 | **「較正が生成分布を変えてよい上限(±5%)」の事前宣言が無い**(boundary-economy 6-a の推奨)。W18 の `VERIFIED` は構築時に全 false なので、**照合が通っているかを示す計器が実質未稼働**(`w18_coverage.py:309`) |
| 8 | **ablation はスケール前の完了条件** | `tools/c8/ablation_runner.py`+`ablations_v1.json`(9 腕・`first_wave` 6 本)。結果は `docs/bench/c8/ablation/` に **AB1(seed 1/2)・AB6(seed 1/2)・AB7・AB7b** が実在 | **第1陣 6 本のうち AB2(p_notice d50)・AB3(不応期)・AB4(ΔSNR)・AB5(内省頻度)の 4 本が未実施**。この 4 本はいずれも**知覚契約の中核 expedient**(§2-13 #4・§2-14 #1・§2-5 #4・§2-14 #4)。にもかかわらず 40 万体 × 実 LLM のランは既に 4 本走っている=「スケール前の完了条件」の順序が部分的に逆転している |
| 9 | **自己修正ループ 原則1(発火は現実側の距離か試みの台帳から。自己採点では発火しない)** | `tools/vocab/registry_from_tape.py`(テープ→未定義台帳)→ `adjudicate.py`(起草)。LLM による自己採点の経路は無い | 語彙以外(パラメータ較正)の「機械が起草する道」が存在しない=原則 1 が**語彙 1 レーンでしか実装されていない** |
| 10 | **自己修正ループ 原則2(diff+テスト+版・機械の設定を指紋として宣言)** | `adjudicate.py` が drafts.json に指紋 6 つ(裁定モデル・温度・プロンプト版 sha 6acda67c・閾値・合格線・採用順序)を記録+`tests/vocab` 27 件 | 人間起点の修正(運用 ⑤)について、**「次のランでアンカー距離が悪化していないことを受入表で確認」する定型の受入表が無い** |
| 11 | **自己修正ループ 原則3(反実仮想の妥当性は対象外・多重同時照合で守る)** | `v2-pattern-ledger.md`(強5本+封印3)+`world/processes/constitution.py:21`(封印行の悪用を違反に) | POM の「多重同時照合」を**同時に**判定する計器が無い(指標は個別に出る)。statistics S-1 の家族単位判定が未実装なのと同根 |
| 12 | **横断ルール: 手動確認 2 回で自動テスト化 / 意図的負債は台帳+返済期限** | `PENDING.md`(D-1〜D-82 の番号制)+`IMPLEMENTED.md`+ pytest 2,446 件 | **返済期限の欄が無い**(Fowler 4 象限の「期限」に相当する列が PENDING に無い)。D-66 の「W17 待ち」が資産導入後も残った事件(記憶)と同型のリスク |

---

## 6. 監査の限界

### 6-1. 見なかったもの

- **P1 40 本・P2 9 本は見ていない**(依頼の「時間があれば P1 主要 10 本」は時間内に届かなかった)。ただし §4 の逆引き表には P1 の 4 本(vlm-reality-check・ethics-operations・game-frontend・price-formation-llm・d1-reacquisition)が**名指しで DECIDED を支えている**ことだけ記録した。P1 の判定は次の監査へ。
- **答申の本文の正しさは一切検証していない**。本書は「答申が言ったことが設計と実装に入ったか」だけを見る。数値の真偽は R-23(一次確認)の仕事。
- **テスト関数の中身は読んでいない**。「テストがある」は該当モジュール・定数を参照するテストファイルの存在をもって判定した。テストが実質的に何も検査していない可能性は排除できていない。
- **実行はしていない**(pytest を回していない)。`grep` と `sed` による静的読解のみ。
- **`docs/bench/` の実測記録は IMPLEMENTED.md の記述を通じてのみ参照**した。生の記録ファイルは開いていない。

### 6-2. 判定の弱いところ

- **「ラウンド」で引いた逆引き 19 本**は、答申と決定の対応を**日付と特徴値**で推定している。答申が決定の根拠だったか、決定が先で答申が追認だったかは区別できていない(batch2 §3 が「背骨」で見つけた問題と同型)。
- **未コミットの 945 行**を「実装済(未コミット)」として数えた。親がこれを別扱いにするなら、§1 の実装済は 2 件減り、部分が 1 件増える(§2-35 #4・#7・#5)。
- **「部分」と「設計済・未実装」の境界は判断が入っている**。縮退版が残っていれば「部分」、跡形もなければ「設計済・未実装」とした。
- **1 答申あたり 3〜8 項という制約**のため、答申が挙げた推奨をすべて拾ってはいない。特に perception-u17(1,106 行)・ad-information(586 行)・channel-budget(529 行)は推奨の 2〜3 割しか見ていない。

### 6-3. 数え方

- 判定項は §2 の表の行数(**240**)。1 行 = 1 項。集計は本書自身を機械的に走査して数えた(判定欄の `**実装済**` 等を正規表現で抽出)ので、**§1 の数と §2 の表は必ず一致する**。再現:
  ```
  # §2 の各行の判定欄から 5 値を抽出して数える(本書を入力にする)
  python - <<'EOF'
  import re,collections
  t=open('docs/research/v2-research-reflection-audit.md',encoding='utf-8').read()
  b=t[t.index('## 2. 答申ごとの判定表'):t.index('## 3. 取りこぼし候補')]
  c=collections.Counter()
  for l in b.split('\n'):
      if not l.startswith('| '): continue
      cells=[x.strip() for x in l.strip().strip('|').split('|')]
      if len(cells)<5 or cells[0]=='#' or set(cells[0])<=set('-: '): continue
      m=re.search(r'\*\*(実装済|設計済・未実装|部分|未採用|未判定)',cells[-1])
      if m: c[m.group(1)]+=1
  print(sum(c.values()), dict(c))
  EOF
  ```
- §1-2 の分野割当は INDEX §2 の紐づけを使い、複数分野の答申は主分野に寄せた(割当表は §1-2 の行名のとおり)。
- 「未採用」は理由の記録の有無を §2 の判定欄に併記した。**理由の記録が無い未採用は 1 件のみ**(ad-information #3 のスカラー変換)で、これは §3 の 12 位に上げた。
- **1 答申あたりの項数は 4〜8**(最小=area-boundary の 4・最多=8 が 12 本)。答申の長短で項数を揃えていないので、**§1 の割合は「答申の重み」ではなく「項の重み」**である。

### 6-4. 親が最初に再確認すべき判定 5 件

| # | 判定 | なぜ再確認が要るか | 再現手順 |
|---|---|---|---|
| 1 | §2-14 #4「T2 日次内省の実呼が無い」 | 予算 L5 を宣言済みなので、もし別経路で回っていれば本監査の最大の誤りになる | `grep -rn "n_reflections\|T2" src/shibuya/engine/llm_bridge.py src/shibuya/llm/fleet.py` |
| 2 | §5 #3「感度試験で『駆動していない』と結論できたのは 1 行だけ」 | CLAUDE.md §4 の中核義務の履行率そのもの。**台帳が 2 本ある**(仕様 `tools/` 側は全行 todo・結果 `docs/bench/` 側が done 6)ので、どちらを正とするかで話が変わる | `python - <<'EOF'` / `import json,collections;d=json.load(open('docs/bench/c8/sensitivity_v1.json',encoding='utf-8'));print(collections.Counter(r['status'] for r in d['rows']));print([ (r['id'], r.get('verdict') or r.get('result')) for r in d['rows'] if r['status']=='done'])` / `EOF` |
| 3 | §5 #8「第1陣 6 本のうち AB2〜AB5 が未実施」 | 「ablation はスケール前の完了条件」の履行状況の判定そのもの | `ls docs/bench/c8/ablation/`(AB1・AB6・AB7・AB7b は実在。AB2/AB3/AB4/AB5 が無いことを確認) |
| 4 | §2-6 #4「『なし』を書かない規約が逆」 | 答申の推奨と実装が逆を向いている珍しい例。契約書 §2.4 に採否の条文があれば「未採用」へ落ちる | `grep -n "なし\|否定文\|空欄" docs/design/v2-perception-contract.md` |
| 5 | §2-1 #3「0.8 の感度腕が無い」 | batch2 §4-C の推奨③の履行状況。D-78 (e) の中身が「登録簿へ」までなのか「腕を作る」までなのかで判定が変わる | `grep -n "D-78" PENDING.md docs/log/devlog.md` |
