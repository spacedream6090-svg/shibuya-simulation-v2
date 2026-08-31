# v1シミュレーション 全機能棚卸し(2026-08-29・v2ゼロベース再設計の入力)

> ユーザー指示タスク(2026-08-28)。src/society/ 185ファイル96,563行・conf 8,904行・scripts 122本・
> tests 337ファイル6,558関数・機能トグル379件を全走査。
> 判定根拠: conf/finals_observe.yaml実効値・devlog第159まで・Run A/B kind_totals実測・矛盾監査28件。
> 再利用判定: **a**=コードごと使える / **b**=設計・知見だけ引き継ぐ / **c**=不要または作り直し

## 最重要の総括

**「v1で最も磨かれた層(物理・cap・予算)ほど c に落ち、最も磨く時間がなかった層(データ資産・観測契約・較正)ほど a に残る」**という非対称が確認された。c判定のほぼ全部は矛盾監査の根1-3(計算資源が物理律/経済が循環定義/心と世界が相互不可視)で説明できる。

## 仕分けサマリ

**a(コードごと使える)**: 実データ資産全般+データ生成器(build_map/build_orgs/build_persona_pool/
build_persona_backstory/build_transit_odpt/rw_fetch)・較正台帳(data/ground_truth/registry.yaml=37アンカー・
split宣言つき)+calibrate_report/reality_score・L1/L2契約と観測層(logger/schema/causality/provenance/GTロガー)・
Chronicle(6,617行)・解析スクリプト33本(l1_stream移行済19本)・LLM基盤(fleet/cache/journal/deadline/request_seed)・
mind三層配置(8bはA/B/Cで勝つがD層分散が潰れる=混成は多様性のため)・day_planスキーマ+夜間プリフェッチ・
EnvPack(地名リテラル外部化=任意タイル対応の先行実装)・習慣カレンダー(分布厳密保存)・遺失物(返還率が実測band着地)・
EMS行為連鎖(時刻表で撃たない)・street_life(尊厳規約)・A8トーナメント(実journal駆動のモデル比較)・
モデルバッテリー(D層分散が生命線)・freeze_config(mock黙走ガード)

**b(設計・知見のみ)**: ORCA/SFMのパラメータ・基本図較正・破綻統計検証枠(コードはGPU書き直し)・
presence/pool(dehydrate allowlistは根治)・attention top-k/声の段階・LOD予算(ゼロ発火帯を作らない配分へ)・
relations tier+内生化実験プロトコル(CRN+sign-flip permutation)・記憶/内省(T2夜間監査へ再定義)・
真偽台帳の伝播木・envfeedback閉ループ・SoA到達点見積(250k実測c=1/500)・ablate対照設計・Δt分類テーブル
(rate/prob/steps/invariant+逆比例の第4分類)・装置DEVS層・転出入(原則に最も忠実なのに本番OFFだった)

**c(捨てるor作り直し)**: scheduler単一巨大関数(6,893行・約90フェーズ固定順)・cap群(聴衆20/記憶120/関係20/
会話履歴8×4)・driveの不発30%減衰・routineの支配的経路化(→T0習慣へ昇華)・C2実文なし会話・
経済の循環定義(売上=賃金×margin/RoW湧き金/財布自動補充/定数価格)・キャリア日次抽選・選挙実装(本番未使用)・
chance(退役済)・屋内エンジン1,300行(本番OFF・知覚が読まない)・POV/VLM(stub)・policy_cache(T0が機能置換)・
SUMO連成(外部プロセス=可搬性と相性最悪)・no-fingerprint現行適用範囲・regression

## 実データ資産(陳腐化しない・v2の第一級インプット)

| 資産 | パス | 要点 |
|---|---|---|
| OSM地図v8 | data/shibuya_osm_wide_v8.json | POI 2,337・道路1,677折れ線・地下141・デッキ148(ODbL・osm_date凍結) |
| PLATEAU 3D | data/plateau/ | CityGML 6,311棟→照合3,531棟・DEM 2m・地下街LOD4.1 |
| 人流アンカー | data/jinryu/ | 渋谷区1kmメッシュ+144step同時滞在曲線(平日昼ピーク37.2万) |
| 実ダイヤ | data/odpt/+transit_odpt.json | 9路線・実発車1,810本(チャレンジ枠データは再配布不可の可能性・README必読) |
| 組織台帳 | data/organizations_shibuya_census.json | センサス較正9,872社・従業者22.2万・夜勤3,370社・営業曜日宣言 |
| ペルソナ100万 | data/persona_pool_v2/ | IPF×国勢調査+LLM・年齢乖離0.36pt・28秒で決定論再生成可 |
| backstory | data/persona_backstory_v2/(サーバー側) | 99.98万人分・語彙多様性+23-24%・ラン時コストゼロの「事前生成凍結」型 |
| 天候 | data/snapshot/weather_tokyo_aug.json | 気象庁930日凍結+WGEN生成器(猛暑連長KS p=0.97) |
| 日次現実データ | data/realworld/ | amedas/wbgt/人流/ODPT-RT等・毎日12:00取得・欠測をnullで正直記録 |
| 歩行者実軌跡 | data/juelich_ped/ (149MB) | Jülich bottleneck/crossing=物理較正の外部ground truth |
| 信号実測 | data/crossings_shibuya.json | スクランブルcycle140/green37/flash10・信号69基 |
| 較正アンカー台帳 | data/ground_truth/registry.yaml | **37アンカー・全項目にsource/year/split強制。v2で最初に移植すべき1ファイル** |

実人口アンカー: 夜間2.96万/同時滞在20-30万/日次ユニーク70-120万/従業者25.7万/平日ピーク371,829。

## 死蔵資産(実装完了・本番OFFのまま終了)

- **認知プログラム中核 fire/watch/engaged/plasticity/calib ≈2,900行**(θ較正済み・呼数実測が揃わず未開栓)
- **屋内エンジンB0-B9 ≈1,300行**(知覚が読まない座標を計算する設計矛盾ごと死蔵)
- ATT層B(LLM自律注意宣言・1行でON可)・emergent presence(cap撤去・RAM+72GBゲートで見送り)・
  HOME_AWAKE(較正済MAPE2.5%・縦煙ゲート未通過)・POV/VLM・policy_cache・aging・転出入・
  ablate4種+zero_traits(対照ラン余力なし)・worldmod(反実仮想)・state_hash・verifyモード・SUMOライブ
- **k対照系列が本番1条件のみ**(D7主実験は未実施のまま)=v2 §10b「実験一級市民化」の最大の動機

## ONだったが発火しなかったもの(空振り・正直記録)

選挙(名簿制固定でコード不使用)・crime/police_response(L1で0行=実LLM実測は本選後)・自然造語(step66で0=
10日では出ない・時間スケールの知見)・出前order/deliver(Run Bで0=自発判断は出前を頼まない?)・
組織形成/world-changer出現(主張⑥「未発火の正直開示」)

## テスト資産(6,558関数)のv2含意

**意味を失う層**: golden(既定OFF=バイト一致)・物理同値(ビット同一を捨てる方針のため)
**契約テストとして優先移植すべき6層**: ①L1スキーマ ②観測不変性(サイドカーがシムを触らない・局所変数名
静的検査という手法込み) ③レジストリ全数宣言(未宣言CI fail) ④conf値ピン(貼り込み消失防止)
⑤名簿⇔conf整合(conf が名指す職業が名簿に実在するか=配達員不在事故の再発防止) ⑥経済保存則(Σ不変)

## 主要な運用知見(コードでなく教訓として引き継ぐ)

- 暦は一級市民(第148: 土曜始まりランで在勤全ゼロ=営業曜日を黙って捨てるバグが最大級)
- rebind_daily必須(OFFだと客引き3日で-89%)
- 「担い手が名簿に実在するか」の検収(設備保守員0人事故)
- watchdogのstall閾値<flush間隔で健全ラン2回殺害
- 読み取り専用ビューアがWindows共有フラグでランをfinalize異常終了させる経路が実在
- vLLM: 4xx誤爆で全台cooldown汚染・1呼1時間47分張り付き→deadline必須・8B×5=6.0呼/s(並列64)
- モデル切替時のVRAM未解放で3.3倍遅延
- chat経路parse 99.0% vs raw completions 58.7%(A8)

> 完全版の表(15セクション・全サブシステムの実装場所・規模・ON/OFF・価値判定)は監査エージェントの
> 出力として本ファイルに要約。詳細が必要な場合は各実装ファイルの docstring とIMPLEMENTED.mdを参照。
