# 文献コーパス(docs/research/lit/)— 1 論文 1 メモ

> **v1 の `docs/lit/` と同形式**(ユーザー承認 2026-09-14・第182)。v1 では 44 本がこの形で蓄積され、答申より短く・引きやすく・批判まで書く形が機能した。v2 でもこの形に戻す。
> 置き場の違い: **答申(`docs/research/v2-*.md`)= 決定のための報告書**(複数分野・複数論文・推奨つき)。**本フォルダ = 1 論文のエッセンス**。答申は本フォルダのメモを引く。

## なぜ分けるか

答申は 400〜1,000 行あり、「この論文が何を言っていたか」を後から引くには重い。実際、第178 の残務台帳で「一次確認が残っている」と判明した数値の多くは、答申の本文に埋もれていて出所が辿れなかった。1 論文 1 ファイルなら、**確認済みか未確認かがファイル単位で分かる**。

## メモの定型(v1 の形をそのまま採る)

```markdown
# <著者 年> — <タイトル>

- リンク: <検証済み URL(正規ドメインのみ)> | 分野: <field> | 重要度: P0/P1/P2
- **一次確認**: 実読 / 抄録のみ / 二次引用 (+ 確認日と手段)
- 主張(claim):
- 機構(mechanism):
- 効く箇所(seam):
- 「結論でなく機構として」の入れ方:
- 数値(そのまま使う値があれば。**出所の頁・表番号まで**):
- コスト/スケール含意:
- 批判・限界:
- 関連: [[...]]
```

**v1 からの追加は「一次確認」行だけ**。第178 で「サーチスニペットのみ」「規格本文未確認」が 10 件以上あると分かったので、状態をファイルの頭に出す。

## 命名

`<field>__<著者年>_<短縮タイトル>.md`(例 `mobility__song2010_predictability.md`)。`field` は [分野地図](../v2-discipline-map.md) の分野名を短縮したもの。

## 規律

- **参照は多く、実装は少なく**。論文の結論を直接実装しない(機構として入れる)。
- リンクは正規ドメイン(arxiv.org / doi.org / 公的機関)のみ。未検証ならリンクを張らず「未検証」と書く。
- **記憶で埋めない**。読んでいない項目は空欄のまま残す(CLAUDE.md §5)。
- 一次確認が済んだら [残務台帳](../research-backlog.md) の該当行を消す。

## 既存の答申との関係(2026-09-14 時点の方針)

- **既存 74 本の答申は書き換えない**。決定の根拠として設計書から参照されており、形を変えると追跡が切れる。
- 代わりに、**答申を読み直す用事が出たときに、その論文のメモを本フォルダへ切り出す**(残務台帳 R-2・R-10 から R-16 の一次確認がその機会)。
- v1 の `docs/lit/` 44 本のうち v2 でも生きるものは、**読み替えのうえ複写**する(残務台帳 R-4b の棚卸しで仕分ける)。

## 一次確認の 3 段階(索引の欄)

- **実読** = 親が原典(PDF・本文)を開いて数値を直接読んだ。
- **二次(v1 メモ経由)** = 親が v1 の読解メモを実読したが、**原典は未読**。v1 メモは出典 URL を検証済みと記載しているが、親自身は確かめていない。→ [残務台帳](../research-backlog.md)・[進行状況](../RESEARCH-STATE.md) に原典確認の行がある。
- **抄録のみ** = 抄録・検索要約までしか見ていない。

**二次のメモを新しい決定の根拠にしてはいけない。**機構(どういう形か)の議論には使ってよいが、数値は原典を読んでから使う。

## 索引

| メモ | 分野 | 一次確認 | 何のために引くか |
|---|---|---|---|
| [compute__agentsociety2025_parallel_framework](compute__agentsociety2025_parallel_framework.md) | 計算機科学(並列)#28 / 計算社会科学 #25 | **実読** | この分野が「実用」と主張するときの基準(実時間比 > 1)と、GPU 時間/体日での正規化比較 |
| [compute__matsim2020_hermes](compute__matsim2020_hermes.md) | 計算機科学(並列)#28 / 人間移動科学 | **実読** | 「非実用」の判定は 1 本の時間でなく `必要ラン数 × 1 本の時間` で下されるという枠組み |
| [stats__lorscheid2012_replication-doe](stats__lorscheid2012_replication-doe.md) | 統計学・因果推論 #23 | 二次(v1 メモ経由・原典未読) | **反復回数は CV 収束で決める**。G-8 の expedient を解消する道。**D-70 の答えを決める測定** |
| [network__complex-contagion-overview](network__complex-contagion-overview.md) | 社会ネットワーク科学 #14 | 二次(v1 メモ経由・原典未読) | **行動・規範は 1 接触で伝わらない**(complex contagion)。会話 410/日 と第2陣の主題に直結 |
| [validation__operational-validity-overview](validation__operational-validity-overview.md) | 検証とV&V #22 / 科学哲学 #26 | 二次(v1 メモ経由・原典未読) | 妥当性は多 seed のマクロ分布で見る / **LLM は効果量を大きく出す** / 既知結果の再現を先に |
| [stats__lee2015_abm-output-analysis](stats__lee2015_abm-output-analysis.md) | 統計学・因果推論 #23 / ABM方法論 #21 | **実読**(第200・親再取得) | **Lorscheid の CV 法を逐語で引く二次**・c_V は μ≈0 の指標に不向き・「分散の安定→効果量→n_min」の 2 段 |
| [stats__siepe2024_simulation-study-template](stats__siepe2024_simulation-study-template.md) | 統計学・因果推論 #23 / 検証とV&V #22 | **実読**(第200・親再取得) | **反復回数は MCSE 目標から逆算し事前登録で宣言**(n=S²/MCSE*²)・分野の実態=中央値 900・根拠あり 8% |
| [stats__tenbroeke2016_sensitivity-abm](stats__tenbroeke2016_sensitivity-abm.md) | 統計学・因果推論 #23 / ABM方法論 #21 | **実読**(第200・親再取得) | 目的別の反復数(分布推定=数百・感度解析=10/5/0)・**seed 間分散÷条件間分散で追加不要を証明**(0.88%) |
| [stats__ritter2011_number-of-runs](stats__ritter2011_number-of-runs.md) | 統計学・因果推論 #23 | **実読(著者版 PDF・第200・親 pymupdf)** | 「シミュレーションは理論であって標本でない」・検出力表(power .90: ES 0.8→34・0.5→88・0.2→545)・**8 seed の床 ES≈1.65** |
| [stats__secchi-seri2017_power-abm](stats__secchi-seri2017_power-abm.md) | 統計学・因果推論 #23 / ABM方法論 #21 | **実読**(第200・親 PDF。式 (2) の係数のみ親未確認) | ABM の標準= α 0.01・power 0.95・経験式 n≃14.091·J^−0.640·ES^−1.986・**多すぎるのも害** |
| [stats__hoad2007-law2020_replication-ci](stats__hoad2007-law2020_replication-ci.md) | 統計学・因果推論 #23 / OR | **実読**(第200・親 pymupdf。Law 教科書原文は未確認) | 相対精度の逐次停止則+先読み kLimit・**d₈=83.6·CV**・n→4n で半幅 1/2 |
| [ensemble__ecmwf_ensemble-size](ensemble__ecmwf_ensemble-size.md) | 不確実性定量化 #22 / 気象アンサンブル | **実読**(第200・親再取得+pymupdf。QJRMS 査読版は未読) | **51 の根拠(10→50 で改善・50 超は逓減・資源との妥協)**・交換可能なら CRPS_M=(1+1/M)CRPS_∞・**R&D は 2〜4 で足りる(fair score)**=8 seed を正当化できる唯一の枠 |
| [nlp__choi2025_identity-drift](nlp__choi2025_identity-drift.md) | 自然言語処理 #27 / 人格心理学 #13 | B(サブ実読・第202・親未確認) | 「大きいモデルほど漂う」に**効果量は無い**(Table 3 の尺度数だけ)・8B 級は安定側 |
| [nlp__taubenfeld2024_debate-biases](nlp__taubenfeld2024_debate-biases.md) | 計算社会科学 #25 / 自然言語処理 #27 | B(サブ実読・第202・親未確認) | 指示した立場より**基底の傾きが勝つ**・回帰の大きさは図のみ(空欄)・帰無腕(Default)の作法 |
| [agents__rozanov2025_stateact](agents__rozanov2025_stateact.md) | 自然言語処理 #27 / ABM方法論 #21 | B(サブ実読・第202・親未確認) | **状態を出力に書かせる**と +3.7〜13.3 pt・手数 31.5→19.1・**JSON にすると −18.5** |
| [agents__goodyear2025_state-representation](agents__goodyear2025_state-representation.md) | 自然言語処理 #27 / ABM方法論 #21 / 統計学 #23 | B(サブ実読・第202・親未確認) | **要約 × 後悔 × 自分だけ**が均衡に最も近い(17.71/18)・**平均でなく試行間分散で判定せよ** |
| [compute__alves2026_llm-urban-mobility](compute__alves2026_llm-urban-mobility.md) | 計算機科学(並列)#28 / 交通工学 #2 | **実読**(第202・サブ WebFetch+親再読) | Table 3 で **LLM 判断層は規則ベースの 2.6〜5.1 倍**・**記憶は +30〜44% と誤り率 2 倍** |
| [validation__larooij2025_generative-abm-validation](validation__larooij2025_generative-abm-validation.md) | 検証とV&V #22 / 計算社会科学 #25 / 科学哲学 #26 | **実読**(第202・サブ WebFetch+親再読) | 35 本中 **15 本が主観のみ**・「公刊パターンでの検証は**データ漏洩**」・**事前登録ベンチの唯一の外部根拠** |
| [mas__li2026_agents-not-sufficient](mas__li2026_agents-not-sufficient.md) | 計算社会科学 #25 / ABM方法論 #21 | B(サブ実読・第202・親未確認) | **処方は §4 の Action 1-3**・**Vis / Sch / Tr / D₀** の語彙・「分布として報告・分散分解」 |
| [validation__ye2026_robustness-audits](validation__ye2026_robustness-audits.md) | 検証とV&V #22 / 計算社会科学 #25 | **実読**(第202・サブ WebFetch+親再読) | **事前登録は本文に無い**・TRAILS-D 3 層 8 次元 + **TRAILS-R 5 次元**・76 pt = ペルソナ書式・N=30 seed |
| [causal__shah2026_agent-replay](causal__shah2026_agent-replay.md) | 統計学・因果推論 #23 / 計算機科学 #28 | B(サブ実読・第202・親未確認) | 介入代数 5 種・**point-of-commitment 則**(下流再抽選の交絡)・**共通乱数は未対応=ローカル艦隊なら持てる側** |
| [nlp__abootorabi2026_steering-geometry](nlp__abootorabi2026_steering-geometry.md) | 自然言語処理 #27 / 人格心理学 #13 | B(サブ実読・第202・親未確認) | **指示チューニングで ρ_T が 0.51→0.33**(1 モデルのみ)・採らない道の確認・価値ベースの個体差は弱い |
| [memory__lu2026_procedural-graphs](memory__lu2026_procedural-graphs.md) | 認知科学(記憶・習慣)#12 / 自然言語処理 #27 | B(サブ実読・第202・親未確認) | **属性を辺に置く**(条件・助言・落とし穴)・受理は**非減少**・却下記録・**助言呼で呼数が倍** |
| [mas__yang2024_oasis](mas__yang2024_oasis.md) | 計算社会科学 #25 / 計算機科学(並列)#28 | **実読**(第202・サブ WebFetch+親再読/pymupdf・v1 メモと突合) | **Table 2 が唯一の出所**・v1 の ★2 数値は一致・**超線形 N^1.55**(体あたり 0.144→0.540→1.750 GPU·s) |
| [agents__wang2023_voyager](lit/agents__wang2023_voyager.md) | 自然言語処理 #27 / ABM方法論 #21 | B(サブ実読・第204・親未確認) | **獲得の閾値は「1 回の成功 + 自己検証」**・オンライン書き戻し・**剪定なし**。D-71 で採らない道の基準線 |
| [agents__wang2024_workflow-memory](lit/agents__wang2024_workflow-memory.md) | 自然言語処理 #27 / ABM方法論 #21 | B(サブ実読・第204・親未確認) | **オフラインとオンラインが同じ枠で成立**する唯一の明示先行・**オンライン獲得が性能を下げる実例**(§3.2.2) |
| [agents__wang2025_programmatic-skill-induction](lit/agents__wang2025_programmatic-skill-induction.md) | 自然言語処理 #27 / ソフトウェア工学 #29 | B(サブ実読・第204・親未確認) | **検証の段が効果の主因(+4.2 pt)**・3 検査(Correctness/Usage/Validity)・**採用率 15.6%** |
| [agents__zhao2024_learnact](lit/agents__zhao2024_learnact.md) | ABM方法論 #21 / 自然言語処理 #27 | B(サブ実読・第204・親未確認) | **失敗 → 行動追加をオフラインでやる唯一の先行**・**2 反復で最適・行動は 3.75→3.83 しか増えない** |
| [agents__yu2024_affordable-generative-agents](lit/agents__yu2024_affordable-generative-agents.md) | 計算社会科学 #25 / 認知科学 #12 | B(サブ実読・第204・親未確認) | **固定環境では行動語彙が飽和する**(実測)・**cosine 0.97 = 重複判定の唯一の数値先行**・費用 31.1% |
| [agents__ahn2022_saycan](lit/agents__ahn2022_saycan.md) | 自然言語処理 #27 / ABM方法論 #21 | B(サブ実読・第204・親未確認) | **551 = 動詞族 7 × オブジェクト 17**=「オブジェクト由来」原則の定量的裏づけ・affordance = 前提条件の価値関数 |
| [cbr__aamodt1994_cbr-cycle](lit/cbr__aamodt1994_cbr-cycle.md) | 法学 #11 / ABM方法論 #21 | B(サブ実読・著者版 PDF・第204・親未確認) | **4R の原典**・**「どう解けたかに関わらず事例庫を更新する」=閾値なし全件保持**・失敗も事例 |
| [nlp__atil2024_nondeterminism](lit/nlp__atil2024_nondeterminism.md) | 計算機科学(並列・決定論)#28 / 自然言語処理 #27 | **実読**(第204・親が abs を再読: 「much less identical output strings」・精度差 up to 15%・TARr/TARa) | **温度 0 は同一出力を保証しない**=段4 の決定論は表参照でしか作れない・**TARr@N / TARa@N** |
| [transport__suzuki2012_station-facility-capacity](transport__suzuki2012_station-facility-capacity.md) | 交通工学 #2 / 歩行者動力学 #18 | **実読**(第207・サブ+親 pymupdf: 3.30/4.00〜4.50/56.1/65.7 逐語一致) | **ホーム滞留容量 3.30 人/m²**(銀座線渋谷駅を含む実測)と 改札 56.1・ES 63.5 / 53.9% の**一次出所**。表―1 の単位(人/m・分)= R-7 の空欄を閉じる |
| [law__kokuji1441_occupant-density](law__kokuji1441_occupant-density.md) | 法学 #11 / 建築環境工学 #7 | **実読**(第207・サブ+親 PDF: 売場 0.5/飲食室 0.7/廊下 0.3 逐語一致) | **用途別の法定占有密度**(飲食室 0.7・売場 0.5 人/m²)と**必要滞留面積 0.3 m²/人**。1 席面積の置換と滞留上限の錨 |
| [law__shobo-kisoku_occupancy](law__shobo-kisoku_occupancy.md) | 法学 #11 | **実読**(第207・サブ+親 e-Gov API: 四平方メートル 逐語一致) | 収容人員の算定(飲食 3 m²/人・物販 4 m²/人)。**現行の 4.0 m²/席 と逐語一致**する唯一の法定値 |
| [law__doro-kozorei_walkway-width](law__doro-kozorei_walkway-width.md) | 交通工学 #2 / 地理情報科学 #9 | **実読(サブ)・親未確認** | 歩道 3.5 / 2.0 m・自歩道 4 / 3 m・車線 2.75〜3.5 m・細街路の車道 4 m。**OSM の線から面を作るときの既定幅員の出典** |
| [stats__estat2021_retail-floor-area](stats__estat2021_retail-floor-area.md) | 小売科学 #17 / 人口学 #1 | **実読(サブ・API 取得と再計算)・親未確認** | 店舗床面積の**分布**(特別区部 中央値 80.6 m²)。既定 80 m² の置換 |
| [crowd__bosina-weidmann2018_fd-generic-model](crowd__bosina-weidmann2018_fd-generic-model.md) | 歩行者動力学 #18 / 人間移動科学 #3 | **実読**(第207・サブ+親 STRC PDF Table 2: 1.00/1.60 m/s 逐語一致) | **「1.00〜1.60」は年齢係数でなく希望歩行速度の m/s 幅**(Table 2 逐語)・体幅/反応時間/Hall 親密距離を 1 表で持つ |
| [crowd__kretz2015_kladek-formula](crowd__kretz2015_kladek-formula.md) | 歩行者動力学 #18 | B(サブ実読・第206・親未確認)・第207 | **Weidmann の速度−密度式を式番号つきで**(v_f 1.34・γ 1.913・ρmax 5.4)= R-7 の γ 空欄が埋まる |
| [crowd__morita2004_kobe-luminarie](crowd__morita2004_kobe-luminarie.md) | 歩行者動力学 #18 | B(サブ実読・第206・親未確認)・第207 | **日本の屋外・多方向流の実測**(U15-5 が「実験室データに無い」と宣言した穴)・安全密度 2〜3 人/㎡ |
| [percep__itti1998_saliency-foa](percep__itti1998_saliency-foa.md) | 知覚心理学 #5 / 認知科学 #12 | B(サブ実読・第206・親未確認)・第207 | **注意の焦点 = 1 個の状態**・**IOR 500–900 ms**・proximity preference = G4 の形の原型 |
| [gameeng__unreal_ai-perception](gameeng__unreal_ai-perception.md) | ゲームエンジン工学 #30 | B(サブ実読・公式ドキュメント・第206・親未確認)・第207 | **取得半径と喪失半径を分ける**・刺激の寿命(Max Age)・Dominant Sense = G4/G7 の「外れる条件」 |
| [urban__okada2019_station-waiting](urban__okada2019_station-waiting.md) | GIScience #9 / 認知科学 #12 | B(サブ実読・第206・親未確認)・第207 | **待ち合わせの滞留位置 = 可視領域の重なり × 流動からの距離** = W8 で計算できる |
| [urban__ichimiya2026_meeting-place-amenity](urban__ichimiya2026_meeting-place-amenity.md) | GIScience #9 / 時間利用研究 #4 | B(サブ実読・第206・親未確認)・第207 | **認知性 × 快適性の 2 軸**・**合流後滞在 3〜7 秒 vs 1 分 19〜35 秒**・**待機者の 8 割以上がスマホ** |
| [psych__sorokowska2017_interpersonal-distance](psych__sorokowska2017_interpersonal-distance.md) | 人格心理学 #13 / 会話分析・語用論 #15 | B(サブ実読・第206・親未確認)・第207 | **見知らぬ人 1.35 m・知人 0.92 m**(N = 8,943・42 か国・**日本は含まれない**)= G7 の 2 m の裏づけ |
| [validation__sargent2016_interval-test](validation__sargent2016_interval-test.md) | 検証とV&V #22 / 統計学 #23 | **実読**(第209・サブ+親 pymupdf 逐語一致) | **「帯の中にある」を検定する正典**=区間仮説検定・モデル製作者危険 α / 利用者危険 β・α+β=1 の作例 |
| [stats__lakens2017_tost-equivalence](stats__lakens2017_tost-equivalence.md) | 統計学・因果推論 #23 | B(サブ実読・第208・親未確認)・第209 | **TOST の手続き**・「90% CI が帯の内側」で同値・**3 seed での必要帯 = 偏り + 1.686·CV** |
| [stats__currie-cheng2016_output-analysis](stats__currie-cheng2016_output-analysis.md) | 統計学・因果推論 #23 / OR | B(サブ実読・第208・親未確認)・第209 | **Bonferroni の作例(5 比較 × 90% → 家族 50%・個別 98% が要る)**+CRN+対応のある差の CI |
| [causal__lipsitch2010_negative-controls](causal__lipsitch2010_negative-controls.md) | 統計学・因果推論 #23 | B(サブ実読・第208・親未確認)・第209 | **正解が無いときの検証法の原典**・U-comparability・「鋭いが鈍い道具」 |
| [stats__ogara2025_history-matching-abm](stats__ogara2025_history-matching-abm.md) | 統計学・因果推論 #23 / ABM方法論 #21 | B(サブ実読・第208・親未確認)・第209 | **R-14 の残務を閉じる**・非含意度と閾値 3・4 波で NROY 7.23%→0.82%・**代理なしでは成立しない** |
| [stats__myllymaki2024_global-envelopes](stats__myllymaki2024_global-envelopes.md) | 統計学・因果推論 #23 | **実読**(第209・サブ+親 pymupdf 逐語一致) | **曲線の同時帯**=Bonferroni を 1 本に畳む道・**p の下限 1/s ⇒ 3 seed では α=0.05 不可**・交換可能性 |
| [stats__wan2003_controlled-sequential-bifurcation](stats__wan2003_controlled-sequential-bifurcation.md) | 統計学・因果推論 #23 / ABM方法論 #21 | B(サブ実読・第208・親未確認)・第209 | **D-44 の「十分の線」の語彙**=2 閾値 Δ0/Δ1・群スクリーニング・**CRN の有無を問わない** |
| [validation__hut2026_simulated-rct](validation__hut2026_simulated-rct.md) | 検証とV&V #22 / 計算社会科学 #25 | B(サブ実読・第208・親未確認)・第209 | **到達点 C の物差しの唯一の近い先行**・67 件の逆行検証・**向き 0.70(無内容予測 0.75 に負ける)**・誤差の 2 層分解 |
| [agents__park2023_generative-agents-replay](agents__park2023_generative-agents-replay.md) | 検証とV&V #22 / 計算社会科学 #25 | **実読**(第211・サブ+親 pymupdf/Europe PMC 逐語一致) | **逸話を測定に降ろす 3 段(物語→全員への聞き取り→記憶ストリームでの裏取り)**・**453 応答の 1.3%(n=6)が幻覚**・評価は「**無作為に選んだ** 1 体の replay」 |
| [agents__concordia_structured-logging](agents__concordia_structured-logging.md) | ソフトウェア工学 #29 / ABM方法論 #21 | B(サブ実読・公式ドキュメント/CHANGELOG・第211・親未確認) | **ログの粒度 = entity × step × component × key**・`get_entity_timeline(name)` が個体カルテ・**「再生」は無く checkpoint 復元**・**計器が空になる事故の実例** |
| [abm__grimm2020_odd-observation](abm__grimm2020_odd-observation.md) | ABM方法論 #21 / 検証とV&V #22 | **実読(サブ・pymupdf 62 頁)・親未確認** | **個体カルテの ODD 上の定義**(S1 p.23)・**「1 日 1 羽を無作為に選び trace を出す」**(S1 p.52)・**平均だけか分布も見たかを書け**・**HARKing 禁止=合わなかったパターンも書け** |
| [abm__grimm-railsback2012_pom-multiscope](abm__grimm-railsback2012_pom-multiscope.md) | ABM方法論 #21 / 科学哲学 #26 | B(サブ実読・PMC 本文・第211・親未確認) | **「1 つのパターンは間違った理由でも合う」**(equifinality)・**弱いパターンは束ねて効く**・**パターン = 却下のフィルタ**。Grimm 2005 *Science* の代替(原典は有料未読) |
| [transport__matsim-via_agent-facility-queries](transport__matsim-via_agent-facility-queries.md) | 交通工学 #2 / ソフトウェア工学 #29 | **実読(サブ・pymupdf 216 頁)・親未確認** | **個体カルテ(agent plan クエリ)と場所カルテ(Select Facility Analysis)を同じイベント列から引く先行**・**場所カルテの列の型**(到着/出発/滞在 × 時刻 × 属性)・「記録がある」と「読める」は別 |
| [ethics__demontjoye2013_unicity](ethics__demontjoye2013_unicity.md) | 研究倫理・情報法 #31 / 人間移動科学 #3 | **実読**(第211・サブ+親 pymupdf/Europe PMC 逐語一致) | **4 点で 95% が一意**・**粗化は 1/10 乗でしか効かない**=**「粒度を落として公開」は効かない道**。個体カルテ公開の線を引く唯一の数値 |
| [timeuse__estat2021_timeslot-shiftwork](timeuse__estat2021_timeslot-shiftwork.md) | 時間利用研究 #4 / 人口学 #1 | **実読(サブ・xlsx 取得と再計算)・親未確認** | **日本に始業時刻の分布表は無い**ことの全数確認と、唯一の代理(時間帯編 第15-4表)。**交替制の深夜率は固定の 4.8〜14.0 倍** |
| [stats__estat2023_commute-time](stats__estat2023_commute-time.md) | 人口学 #1 / 交通工学 #2 | **実読(サブ・API 取得と再計算)・親未確認** | 片道通勤時間の**分布**(東京都 p50 43.7 分 / 渋谷区 33.0 分)。`arrival_lead_min` の裏づけ。社会生活基本調査は平成23年で終了 |
| [mobility__lu2013_predictability-civ](mobility__lu2013_predictability-civ.md) | 人間移動科学 #3 | **実読(サブ)・親未確認** | **Π_max = 0.93 は上限でなく設定依存**(0.88 / 0.85)。**実アルゴリズムは 0.91 まで届く**=規則性の下限側の門番 |
| [mobility__pflow2022_japan-motifs](mobility__pflow2022_japan-motifs.md) | 人間移動科学 #3 / GIScience #9 | **実読(サブ・PDF)・親未確認** | **日本の PT にモチーフを当てた唯一の公開実例**。「**都市圏では差が出ず役割で差が出る**」= 多様性は地理でなく属性から |
| [mobility__trajllm2025_demo-eval](mobility__trajllm2025_demo-eval.md) | 人間移動科学 #3 / 自然言語処理 #27 | **実読(サブ・全文)・親未確認** | **定量評価が存在しない**ことの確定。記憶の重みが著者自身の申告で expedient = 採らない道の基準線 |
| [nlp__chang2024_real-sampling](nlp__chang2024_real-sampling.md) | 自然言語処理 #27 | **実読(サブ・HTML 付録 J)・親未確認** | 「大きいほどエントロピーが低い」は**ベースの次トークン**の話(90.2% / 9M トークン)。意味的多様性とは別層 |
| [nlp__springer2026_annotation-anchoring](nlp__springer2026_annotation-anchoring.md) | 自然言語処理 #27 / 人格心理学 #13 | **実読(サブ・HTML)・親未確認** | **ベースは大きいほど多様・事後学習後は大きいほど単調**(inverse scaling)。**プロンプトでは埋まらない**=8B 据置の最強の根拠 |
| [mas__wang2026_s-researcher](mas__wang2026_s-researcher.md) | 計算社会科学 #25 / ABM方法論 #21 | **実読(サブ・HTML)・親未確認** | **「LLM の応答分散は人間の 20–300 倍小さい」の唯一の出所**(考察節・裏づけ表なし)。裾の研究には人間を入れよ |
