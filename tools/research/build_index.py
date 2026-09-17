# -*- coding: utf-8 -*-
"""A-1 索引生成 + A-2 3行ヘッダの一斉付与(第191)。
分野・重要度は親(Opus 5)の判断。一次確認の等級は機械判定+親の例外指定。
再実行しても二重挿入しない(HDR_MARK で検出)。
"""
import io, os, re, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
D = os.path.join(REPO, 'docs', 'research')
HDR_MARK = '<!-- hdr:v1 -->'
SKIP = {'research-backlog.md', 'v2-discipline-map.md', 'INDEX.md', 'RESEARCH-STATE.md', 'v1-asset-triage.md'}

# 分野番号→名前(v2-discipline-map.md)
F = {
 1:'人口学・合成人口論', 2:'交通工学(活動ベース)', 3:'人間移動科学', 4:'時間利用研究',
 5:'知覚心理学・精神物理学', 6:'環境音響学', 7:'建築環境工学', 8:'気象学・生気象学',
 9:'地理情報科学', 10:'SFCマクロ経済学', 11:'法学(業法・条例)',
 12:'認知科学(記憶・習慣)', 13:'人格心理学', 14:'社会ネットワーク科学', 15:'会話分析・語用論',
 16:'行動経済学・マーケティング科学', 17:'小売科学・商業立地論', 18:'歩行者動力学', 19:'都市代謝論・MFA', 20:'オペレーションズリサーチ',
 21:'ABM方法論', 22:'検証とV&V・UQ', 23:'統計学・因果推論', 24:'予測科学(アンサンブル)',
 25:'計算社会科学', 26:'科学哲学', 27:'自然言語処理・機械学習', 28:'計算機科学(並列・決定論)',
 29:'ソフトウェア工学', 30:'ゲームエンジン工学・CG', 31:'研究倫理・情報法', 32:'犯罪学',
 0:'分野外(事業・資金)',
}

# ファイル -> (分野番号リスト, 重要度, 一言の役割)
C = {
 'v2-action-conversation-contract-research.md': ([15,12], 'P0', '行動契約(心→世界)と会話プロトコル。第2陣の主題に直結'),
 'v2-ad-information-research.md':               ([16,14], 'P0', '広告・看板の実効と情報伝播。収益化方針の根拠'),
 'v2-area-boundary-definition.md':              ([9],     'P0', '5エリア定義の一次確認。holdout 照合の写像が依存'),
 'v2-area-boundary-map-reading.md':             ([9],     'P1', '地図スクショからの境界読み取り(親の一次作業)'),
 'v2-benchmark-standards-research.md':          ([22],    'P1', '再現ベンチマークの実測標準'),
 'v2-boundary-deep-research.md':                ([1,2],   'P1', '境界条件と人口の出自'),
 'v2-boundary-economy-u10-u11-research.md':     ([10,1],  'P0', '境界(来街の決定)と経済SFC。保存則の運用形が依存'),
 'v2-c7-fix-research.md':                       ([3,4],   'P0', 'C7 の 2 つの歪みの現実側数値。D-66/D-67 の土台'),
 'v2-capabilities-business-research.md':        ([0],     'P2', '獲得能力・産業応用・事業形態'),
 'v2-cell-granularity-research.md':             ([9,28],  'P1', '場所セルの粒度(prefix 共有単位)'),
 'v2-channel-budget-attention-research.md':     ([5],     'P0', 'チャネル別観測予算と注意ゲート。知覚契約書の骨格'),
 'v2-cognition-detail-research.md':             ([12],    'P0', 'δ_think 上限・思考トークン・記憶細部'),
 'v2-content-safety-deep-research.md':          ([31],    'P2', 'コンテンツ安全・モデレーション'),
 'v2-conversation-deep-research.md':            ([15],    'P1', '会話生成の実装'),
 'v2-coupled-adaptation-deep-research.md':      ([21],    'P1', '適応3ループの複合安定性'),
 'v2-crowd-physics-research.md':                ([18],    'P0', '群衆物理 U15。幾何に基づく容量(R-8)の前提'),
 'v2-d1-reacquisition.md':                      ([3],     'P1', '時刻別同時滞在カーブの出典疑義と代替探索'),
 'v2-d66-outside-residents-research.md':        ([2,3],   'P0', '域外居住者の到着・退出アンカー。v2.1 読み口の根拠'),
 'v2-d68-behavioral-diversity-research.md':     ([3,4,13],'P0', '行動の多様性。17モチーフ・予測可能性93%・同質化'),
 'v2-dashboard-verification-orchestration-research.md': ([22,24],'P0','計器盤・検収戦略・オーケストレーション。G-1〜G-9'),
 'v2-data-contract-research.md':                ([29],    'P2', 'データ契約'),
 'v2-density-hearing-verification.md':          ([6,5],   'P0', '可聴半径は人密度の関数か(敵対的検証)'),
 'v2-digital-twin-landscape-research.md':       ([25],    'P1', 'デジタルツインの実名ランドスケープ。未踏の位置づけに効く'),
 'v2-economy-sfc-deep-research.md':             ([10],    'P1', '経済SFCの具体設計'),
 'v2-engine-llm-boundary-research.md':          ([25],    'P1', 'エンジン/LLM 線引き。v2 の背骨'),
 'v2-ethics-operations-research.md':            ([31],    'P1', '倫理・コンテンツ安全の運用規則'),
 'v2-funding-deep-research.md':                 ([0],     'P2', '資金調達の実務'),
 'v2-game-frontend-research.md':                ([30],    'P1', 'ゲーム的フロントエンド。R-5 可視化の出発点'),
 'v2-game-tech-import-research.md':             ([30],    'P1', 'ゲーム/VR 産業技術の輸入(常設レーン)'),
 'v2-hearing-numbers-and-d1-coverage.md':       ([6],     'P1', '会話可能距離の公開数表 / D1′ の bbox 被覆'),
 'v2-impact-risk-research.md':                  ([31],    'P2', '影響とリスク・メタ安全保障'),
 'v2-implementation-stack-research.md':         ([29,28], 'P1', '実装スタック(言語・ABM基盤・データ層・CI)'),
 'v2-institutions-deep-research.md':            ([11],    'P1', '制度の最小足場と失敗の観測'),
 'v2-kddi-attribute-shares-2024.md':            ([1],     'P1', 'KDDI LA 属性構成(親が手元生データから再集計)'),
 'v2-learned-simulation-research.md':           ([27],    'P2', '学習ベースシミュレーション路線'),
 'v2-legal-licensing-deep-research.md':         ([31],    'P1', '法務・ライセンス'),
 'v2-llm-knowledge-deep-research.md':           ([27],    'P1', 'LLM 事前知識の影響と活用/遮断'),
 'v2-llm-mobility-research.md':                 ([3,27],  'P1', 'LLM 起点の人流生成'),
 'v2-llm-serving-deep-research.md':             ([27,28], 'P1', 'LLM サービング実務。艦隊設計の土台'),
 'v2-llm-social-sim-timeline-seed.md':          ([25],    'P0', 'LLM 社会シミュの現在地(未正典化)。R-2 の対象 17 件'),
 'v2-longrun-ops-deep-research.md':             ([29],    'P2', '長期運用 SRE・ストレージ・観測 I/O'),
 'v2-memory-retrieval-research.md':             ([12],    'P1', '記憶と想起'),
 'v2-mobility-field-research.md':               ([3,2],   'P1', '人流・交通シミュレーション分野の体系'),
 'v2-observation-format-research.md':           ([5,27],  'P0', '観測の表現形式・配置・トークン予算。知覚契約書 R3-8'),
 'v2-observation-projection-deep-research.md':  ([22],    'P1', '観測射影 L-OBS/L-REC'),
 'v2-p-notice-research.md':                     ([5],     'P0', 'p_notice の関数形。2段ヒル型の根拠'),
 'v2-parallel-execution-deep-research.md':      ([28],    'P1', '並行実行の意味論'),
 'v2-pattern-ledger-deep-research.md':          ([21],    'P1', 'パターン台帳の候補と運用。方法論ゲートの中身'),
 'v2-perception-latency-research.md':           ([5],     'P0', '知覚遅延 δ_perc の導入判断'),
 'v2-perception-timing-research.md':            ([5],     'P0', '知覚のタイミング'),
 'v2-perception-u17-research.md':               ([5],     'P0', '五感/VLA 知覚の導入(最大の答申・1,101行)'),
 'v2-person-perception-verification.md':        ([5],     'P1', '人物知覚4段階案の敵対的検証'),
 'v2-persona-dynamics-research.md':             ([13],    'P0', 'ペルソナは回す中で変化させる必要があるか'),
 'v2-persona-population-deep-research.md':      ([13,1],  'P1', 'ペルソナ・人口合成と個体差'),
 'v2-population-synthesis-research.md':         ([1],     'P0', '母集団合成・40万体の実体化。W16 の根拠'),
 'v2-precedent-system-deep-research.md':        ([11],    'P1', 'GM裁定→判例結晶化。第3陣「制度の創発」の前身'),
 'v2-prediction-module-deep-research.md':       ([12],    'P1', 'エージェント内蔵の予測モジュール'),
 'v2-price-formation-llm-research.md':          ([17,16], 'P1', '行5 価格形成。LLM 店主の値付け'),
 'v2-publication-ethics-deep-research.md':      ([31],    'P2', '出版戦略と倫理審査'),
 'v2-run-manifest-concurrency-research.md':     ([29,28], 'P1', 'run manifest 形式と並行実行の意味論'),
 'v2-science-claims-research.md':               ([26,25], 'P1', '科学的知見・新規性の再検証'),
 'v2-small-scale-verification-research.md':     ([22],    'P1', '小資源検証の方法論'),
 'v2-turing-test-validation-research.md':       ([22,26], 'P0', '識別テスト(Turing型)の評価。第一目標の測り方'),
 'v2-ugc-platform-import.md':                   ([30,10], 'P1', 'UGC/大規模オンラインゲーム基盤の輸入。EVE 残差科目の出所'),
 'v2-update-rules-hearing-research.md':         ([12,6],  'P0', '更新規則(不応期・日次内省・繰り延べ)と聴覚数値'),
 'v2-vlm-reality-check-research.md':            ([22],    'P1', '街路画像+VLM によるシム都市の現実整合検証'),
 'v2-world-coverage-index-research.md':         ([22],    'P0', '世界の再現度指標(WCI)。第一目標の計器'),
 'v2-world-data-build-research.md':             ([9],     'P0', '世界データ構築仕様 W1〜W22 の本体'),
 'v2-world-data-build-round2-research.md':      ([6,8,7], 'P0', '騒音・交通量・気象・PLATEAU・法規'),
 'v2-world-ledger-verification.md':             ([21],    'P1', '世界台帳 D-R2-2 改訂案の敵対的検証'),
 'v2-world-model-relation-research.md':         ([25],    'P2', '世界モデル(Genie 等)との関係'),
 'v2-world-process-inventory-research.md':      ([19,20], 'P0', '世界過程の棚卸しと拡張ロードマップ。陣分けの出所'),
 'v2-world-process-rows-research.md':           ([19,10], 'P0', 'エンジン/LLM 線引き16行の詳細決定材料'),
 'v2-w7-law-primary-check-research.md':         ([11,9],  'P0', 'W7 法規の条文一次確認とコード突合(L-24)。法学 #11 を D→A。D-72 の出所'),
 'v2-replication-count-research.md':            ([23,21], 'P0', '反復回数(seed 数)の文献手続き 7 系譜と「初回 8 seed」の位置(L-B)。D-70/D-44/G-8 の材料。統計 #23 の最初の答申'),
 'v2-destination-choice-llm-research.md':       ([3,27,25,21], 'P1', 'R-37 行き先選択に LLM の思考(候補提示型 H): 先行の主流は逆向き(LLM が意図/カテゴリ・エンジンが POI)・唯一の直接比較 When Plausible は集計(STVD)で重力則が LLM 主導に勝ち個体(Δr・r_g)で LLM が勝つ=符号が逆・8B は候補の並べ替えで Acc@1 .52→.20・k=3〜5 に一次(2 to 5 / 3 to 5)・渋谷はセル内 POI 中央値 4(食事 2)=複数セル跨ぎ必須・候補行 28 tok・合否は D1′ でなく P-6/P-8・推奨=k 4・母集合 K-1∪近傍 8 セル・順序撹拌・番号ラベルなし・段階語・腕 A0〜A4。副産物: nightlife 259 件が飲食マスク外・v2-llm-mobility は D 等級'),
 'v2-c10-initial-relations-research.md':        ([14,12,21,27], 'P1', 'C10 着手前: 関係の強さは記憶の基底活性(ACT-R・d=0.5 は認知設計 §4 で既決)から導ける=Δ 5 個+半減期は消え、残るのは符号・検索閾値 τ(較正可)・エピソード粒度(Gilbert 2009 β 最終接触 −0.76/初回接触 0.755・Zhao 2012=ACT-R を辺にした唯一の先行)。3 値を LLM に書かせない(Qwen3-8B FR 46.22%)=符号は ResultCode から。ラン前ウォームアップの先行 0 本・世界内では会話率 0.0021/体/日で不可→ 機械的初期化を既定・強制ペアは 5,000 体で先に測る。齟齬 6(半減期 90 vs 30・3 人会話の口が無い ほか)'),
 'v2-r23-primary-check-batch3.md':              ([30,29,22,21,12,27,25], 'P0', 'R-23 第3批: D 等級だけを根拠にする決定台帳 18 行の一次確認=支持 9/訂正 9/撤回 0・主張 69・訂正 18(NCP-Bench 20 ターン 42%・0.599^10 導出値・1:5:25 は cascade 制御の実務比で Dunbar でない・L401 強 5 本の陳腐化・Pseudo-PFLOW 学習域・AutoAWQ 非推奨)・L385 三層世界方式の根拠答申は本リポに不在'),
 'v2-personality-traits-research.md':           ([13,12,27], 'P0', '人の構成要素 P2=性格: 規準=川本 2015(N 4,588・TIPI-J M/SD・因子間相関 −.29〜.32・年齢×性別の R² ≤5.35%)・効果量(外向性→会話 |r| .17・協調性→向社会 .12・開放性→移動は負・誠実性→時間厳守は空欄)・LLM 付与(Han 2025「persona は自己申告を動かすが行動は動かない」)→ C 案=入れずに測る(corr(z_E, 会話起点) 目標 .17)・traits 3 次元は設計書で未定義・プールの上側隆起'),
 'v2-hobby-preference-research.md':             ([4,13,1], 'P0', '人の構成要素 P1=趣味・嗜好の公的分布(社会生活基本調査 R3 生活行動編・行動者率 全国 86.3/東京都 91.4・年齢勾配 7 倍・独立抽選は無趣味率で 98 倍ずれる・共起 φ≤0.53)→ 種目 58 bit+コピュラ+稀事象の待ち時間・W6 カタログの欠陥 3(公園が PLACE_PARK に行かない)・先行例ゼロ'),
 'v2-preference-vector-research.md':            ([3,21,13], 'P0', '人の構成要素 P3=選好ベクトルと常連/探索(EPR γ 0.21・Π=f・δ 1.2 / returners k=4・EPR は k≈60 / Schläpfer η≈2 / 外食リピート 77.5%・業態 32〜95.5%・Dubé 状態依存)→ 選好はエンジンの数値・二重計上の整理(戻る=K-1・探す=ρ_i・P3 は初回選択・P1/P2 は掛けない)・repo は店選択が「セル内最小 id」'),
 'v2-classical-vs-llm-simulation-research.md':  ([25,21,26], 'P0', '古典 ABM の要求 × LLM 系の新規性 × 検証の対照表(L-CLS)。「良い LLM 社会シミュレーション」判定基準 10 項(古典由来 6・LLM 由来 1・両方 3)・Axtell 2016 1.2 億体・Edmonds 2019 の 7 目的・観測的同値は Haavelmo 1944'),
 'v2-research-reflection-audit.md':             ([29,21], 'P0', 'リサーチ反映の監査 A=P0 35 本 240 項(実装済 52.9%・設計済未実装 20.0%・部分 18.3%・未採用 4.6%・未判定 4.2%)・逆引き表 42 行・方法論遵守 12 行'),
 'v2-research-reflection-audit-p1p2.md':        ([29,21], 'P0', 'リサーチ反映の監査 B=P1 40+P2 9 本 244 項(実装済 35.7%・部分 24.6%・未判定 21.3%・設計済未実装 13.9%・未採用 4.5%)・分野別反映率(認知科学 #12 0%)'),
 'v2-d68-remaining-research.md':                ([3,4,12], 'P0', 'D-68 経路 3(記憶・習慣)の残 10 件(R-3): 始業時刻の代理=時間帯編 15-4 表・通勤時間=住宅土地統計 58-2-1・交替制の深夜率 4.8〜14 倍・モチーフ 11〜17 型/83〜90%・Lu 2013 Π 0.88・REAL/2605.09995 は別の層 → K-1〜K-5(D-81)'),
 'v2-micro-observation-research.md':            ([22,21,29], 'P1', 'ミクロ観察(個体カルテ/場所カルテ)の先行(R-4): GA の replay+無作為抽出・Concordia のログ粒度・Via の agent/facility クエリ・ODD の Observation・de Montjoye 1/10 乗則 → M1 アジェンダ O1〜O20(D-80)'),
 'v2-statistics-causal-research.md':            ([23,22], 'P0', '統計学・因果推論 #23 の最初の答申(R-25): 多重比較/同値検定(Sargent 区間検定・TOST)・CRN・反実仮想(SCM・負の対照・S-RCT・History Matching)・GET 大域包絡(seed 3 本では p≥0.25)・CSB スクリーニング → prereg v1.3・D-70・D-44・到達点 C の作法'),
 'v2-r23-primary-check-batch2.md':              ([25,10,15,3,11], 'P0', '出典ゼロ答申の一次確認 第2批=背骨の 4 答申(経済 SFC・会話・人流・制度)。独立収束は過程レベルで不成立・D4 修正3・0.8・Decoupling・CPC フロア → D-78'),
 'v2-c9-geometry-capacity-research.md':         ([2,18,9,11,17], 'P0', 'C9 幾何の容量 3 種+ホーム容量の実測化(L-R8): PLATEAU 歩道部面・法定幅員・経済センサス売場面積・建告1441/消防規則の密度・鈴木 2012 のホーム 3.30 人/m²。G8 の置換候補'),
 'v2-c9-position-attention-research.md':        ([3,18,12,25], 'P0', 'C9 位置・速度・注意・会話距離・目印の先行(L-C9): LLM 系 4 通り・Weidmann/Kladek 式(γ=1.913)・希望速度 1.00〜1.60 m/s・FOA/UE Perception・Sorokowska 1.35 m・待ち合わせ実証 2 本'),
 'v2-d71-vocab-growth-research.md':             ([21,27,12], 'P0', '観測から行動語彙を育てる仕組みの先行(Voyager/AWM/ASI/LearnAct/SayCan/CBR/活動分類の規模)。D-71 設計アジェンダ v2-vocab-growth-design.md の出所'),
 'v2-r2-llm-social-sim-fulltext-check.md':      ([25,22,27,23,28], 'P1', 'LLM 社会シミュ文献 12 件の本文実読の判定表(R-2)。lit 12 本の親。OASIS 超線形・事前登録の外部根拠・TRAILS-R の空白=D-75/D-70 の出所'),
 'v2-r23-primary-check-batch1.md':              ([22,25,21], 'P1', '出典 URL ゼロの答申 33 本の一次確認 第1批(設計書が引く 8 本・28 主張)。D-74(値を直す 4 件)の出所・写し検査の提案(R-23)'),
}

# 一次確認の等級を上書きする例外(親が中身を見て判断)
OVERRIDE = {
 # 09-08 の 2 本は URL ゼロだが親検収の逐語引用つき=最上位
 'v2-crowd-physics-research.md': ('A', '親検収(2026-09-08)。逐語引用つき。ただし U15 §4 に空欄 10 件(R-7)'),
 'v2-dashboard-verification-orchestration-research.md': ('A', '親検収(2026-09-08)。逐語引用つき。空欄 6 件(R-14)'),
 # 09-16 第200: 引用条文(風営法 13/22/32・都条例 4条の2/4条の3/5/11/13/15・規則 5/6・青少年条例 15条の4/16/26)を親が全て再取得し逐語一致を確認。告示 PDF のみ親未再取得
 'v2-w7-law-primary-check-research.md': ('A', '親再取得(2026-09-16・第200)。逐語一致つき。空欄 6 件(§4)・告示 PDF は親未再取得'),
 'v2-replication-count-research.md': ('A', '親再取得(2026-09-16・第200)。9 出典を親が再取得(4 Web+5 PDF)・全数値を再計算。空欄 5 件(§4: Lorscheid 原典・Law 教科書原文・Secchi 式(2) 係数・Leutbecher 査読版・ECMWF「51」の根拠文書)'),
 # 09-16 第202: サブ実読+親が 3 主張を原典で再確認(Goel 2016 PDF「on average」・Law in Silico HTML に precedent なし・Ruri カード 71.53<71.65)。Dunbar 1995(有料)・UE5 の不在は親未確認
 'v2-destination-choice-llm-research.md': ('B', 'サブ実読 12+抄録 3(2026-09-17・第232)+親確認 3(When Plausible §5.1 HTML・LLM-Move Table II/IV HTML・nightlife マスク=コード)。付録 B.5 の 3–5/γ・Honka・Zheng・Turpin は親未確認'),
 'v2-c10-initial-relations-research.md': ('B', 'サブ実読 8+読み取り器 4+要約 6(2026-09-17・第230)+親確認 3 件(Gilbert 2009 PDF・Zhao 2012 PDF・Li 2026 HTML)+実物確認 2(会話マネージャ・半減期の齟齬)。Dunbar 2020・内閣官房 R5 は親未確認'),
 'v2-r23-primary-check-batch3.md': ('B', 'サブ実読 約 30(本文 14・抄録 16・2026-09-17)+親確認 3 件(NCP-Bench 抄録・0.599^10・ISA 2013 cascade)。訂正 3 反映・15 未反映・空欄 21+8'),
 'v2-personality-traits-research.md': ('B', 'サブ実読(2026-09-17・第222)+親確認 3 件(川本 2015 PDF の N/M/SD/R²/性別係数・TIPI-J 2012 は大学生 902・Serapio-García 抄録)。Thielmann/Harari(有料)・Han 2025・Contreras 2026 は親未確認'),
 'v2-hobby-preference-research.md': ('B', 'サブ実読(2026-09-17・第221)+親確認 3 件(e-Stat API 再取得 86.3/91.4/37.4/43.4・井出安井 2003 7.1/6/0・47,965・φ 0.5268)。平均行動日数の式・CitySim は親未確認'),
 'v2-preference-vector-research.md': ('B', 'サブ実読(2026-09-17・第221)+親確認 4 件(Song 2010 γ/Π=f/δ・Pappalardo 2015 bisector/k=4/67,000/46,000/k≈60/9・ホットペッパー 2018 77.5%/n 2,106/95.5%/60.9%・repo 現状)。Schläpfer 2021・Dubé 2010 は親未確認'),
 'v2-classical-vs-llm-simulation-research.md': ('B', 'サブ実読 14/17(2026-09-17・第214)+親確認 3 件(PIMMUR v4・Anthis §4.5.2・Sid §5.2/§8.3/§5.3)。Schelling 1971 は二次・Horton/Aher/Gao は抄録のみ'),
 'v2-research-reflection-audit.md': ('E', 'repo 内監査(2026-09-17・第214)・親が上位 4 判定を再確認。外部出典は本質的に不要'),
 'v2-research-reflection-audit-p1p2.md': ('E', 'repo 内監査(2026-09-17・第214)・親が #5(D4 修正3)を誤りと確認・T3 は確認済み。外部出典は本質的に不要'),
 'v2-d68-remaining-research.md': ('B', 'サブ実読(2026-09-17・第212)+親確認 3 件(15-4 表の再計算・REAL App.J・2605.09995 本文)。通勤時間分位・Lu 2013・PFLOW は親未確認'),
 'v2-micro-observation-research.md': ('B', 'サブ実読(2026-09-17・第211)+親確認 3 件(ODD S1・GA §7.1・de Montjoye)。Concordia/Via/AgentSociety は親未確認'),
 'v2-statistics-causal-research.md': ('B', 'サブ実読 8/11(2026-09-17・第209)+親確認 3 件(Sargent 2016・GET p 式・3 seed 算術)。N≈87 は親再計算で ≈20 に訂正。Murphy 2013 は親未確認'),
 'v2-r23-primary-check-batch2.md': ('B', 'サブ実読 32 主張(2026-09-17・第208)+親確認 3 件(Project Sid §5.2/§8.3/500 体・Decoupling 住居移転 39M・0.8 の注記)。残りは親未確認'),
 'v2-c9-geometry-capacity-research.md': ('B', 'サブ実読(2026-09-17・第207)+親確認 4 件(鈴木 2012 逐語・建告1441・消防規則 4 m²・PLATEAU 面積合計)。セル別の比・e-Stat 分位は親未確認'),
 'v2-c9-position-attention-research.md': ('B', 'サブ実読(2026-09-17・第207)+親確認 3 件(STRC Table 2・Kladek 式の再計算・密度段階)。Sorokowska/Hall/Itti は親未確認'),
 'v2-d71-vocab-growth-research.md': ('B', 'サブ実読(2026-09-17・第204)+親が 5 件を原典で確認(社会生活基本調査 20/6-22-90・ATUS 17・Emergence World 2 tools・Atil 2024)。ATUS 465 の再計数・ASI 等は親未確認'),
 'v2-r2-llm-social-sim-fulltext-check.md': ('B', 'サブ実読 12 件(2026-09-16・第202)+親が 4 件を原典で確認(OASIS Table 2・GAMA Table 3・Ye 事前登録の不在・Larooij PDF 逐語)。残り 8 件は親未確認・空欄 18 行(§3)'),
 'v2-r23-primary-check-batch1.md': ('B', 'サブ実読(2026-09-16・第202)+親が 3/28 主張を原典で確認。Dunbar 1995・UE5 不在は親未確認。答申本体の等級は動かしていない(確認済み主張は本文に印)'),
 'v2-area-boundary-map-reading.md': ('E', '親自身の地図読み取り。外部出典が本質的に不要'),
 'v2-kddi-attribute-shares-2024.md': ('E', '親が手元生データ la_raw.json から再集計。外部出典不要'),
}

GRADE = {
 'A': '親検収済(逐語引用または再計算つき)',
 'B': '出典あり・空欄を明示(残務台帳へ写し済みまたは要写し)',
 'C': '出典あり・空欄は未整理',
 'D': '**出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る',
 'E': '出典不要(親自身の一次作業)',
}


def trace(s):
    return (len(re.findall(r'https?://', s))
            + len(re.findall(r'arXiv[: ]?\s*\d{4}\.\d{4,5}|arxiv\.org', s, re.I))
            + len(re.findall(r'doi\.org|DOI[: ]', s, re.I))
            + len(re.findall(r'✔', s))
            + len(re.findall(r'[A-Z][a-z]+ (?:et al\.?,? )?(?:19|20)\d\d', s)))


def main(apply_headers=True):
    rows = []
    for fn in sorted(os.listdir(D)):
        if not fn.endswith('.md') or fn in SKIP:
            continue
        p = os.path.join(D, fn)
        raw = io.open(p, encoding='utf-8', errors='replace').read()
        L = raw.split('\n')
        has_hdr = HDR_MARK in raw            # ← 判定は raw に対して行う(二重挿入の防止)
        # 解析は自分が入れたヘッダを外した本文に対して行う(自己参照で等級が動くのを防ぐ)
        s = re.sub(r'<!-- hdr:v1 -->\n(?:- \*\*.*\n){3}', '', raw)
        title = next((l[2:].strip() for l in L if l.startswith('# ')), fn)
        m = re.search(r'2026-(0[89])-(\d\d)', s[:600])
        dt = m.group(0) if m else '?'
        nurl = len(re.findall(r'https?://', s))
        tr = trace(s)
        has_gap = bool(re.search(r'空欄|未確認', s))
        if fn in OVERRIDE:
            g, note = OVERRIDE[fn]
        elif dt <= '2026-09-01':
            g, note = 'D', f'出典痕跡 {tr} 件・URL 0 件。09-02 以降の中央値 62 に対して桁が違う'
        elif has_gap:
            g, note = 'B', f'出典痕跡 {tr} 件。空欄節あり'
        else:
            g, note = 'C', f'出典痕跡 {tr} 件。空欄節なし(=無いのか未整理なのか未判定)'
        fields, pri, role = C.get(fn, ([0], 'P2', '(未分類)'))
        fstr = ' / '.join(f'{F[i]} #{i}' for i in fields)
        rows.append(dict(fn=fn, title=title, dt=dt, n=len(L), url=nurl, tr=tr,
                         g=g, note=note, fields=fields, fstr=fstr, pri=pri, role=role))
        if apply_headers and not has_hdr:
            hdr = (f'\n{HDR_MARK}\n'
                   f'- **分野**: {fstr} | **重要度**: {pri}(親判断・2026-09-15 第191)\n'
                   f'- **一次確認**: **{g}** = {GRADE[g]} — {note}\n'
                   f'- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)\n')
            # H1 の直後に差し込む
            for i, l in enumerate(L):
                if l.startswith('# '):
                    L.insert(i + 1, hdr.rstrip('\n'))
                    break
            io.open(p, 'w', encoding='utf-8').write('\n'.join(L))
    return rows


if __name__ == '__main__':
    rows = main(apply_headers=('--dry' not in sys.argv))
    io.open(os.path.join(os.path.dirname(__file__), 'rows.json'), 'w', encoding='utf-8').write(
        json.dumps(rows, ensure_ascii=False, indent=1))
    from collections import Counter
    print('files', len(rows))
    print('grade', sorted(Counter(r['g'] for r in rows).items()))
    print('pri  ', sorted(Counter(r['pri'] for r in rows).items()))
