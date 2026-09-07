# データ・ライセンス台帳(2026-09-01初期化)

> 法務答申([v2-legal-licensing-deep-research.md](research/v2-legal-licensing-deep-research.md))の実装。**データ資産を追加するたびに1行追記**する。
> 設計原則: ①data type単位の層分離(OSM/PLATEAU/ODPT/人流を物理分離・重複統合しない=Collective Database維持)②出力スキーマからOSM生値を排除(内部ID+集計のみ)。

| ディレクトリ | 内容 | 出典 | ライセンス | 商用 | 備考 |
|---|---|---|---|---|---|
| data/realworld | OSM抽出(地図・POI)・ODPT実ダイヤ・経済センサス・気象庁実測・国勢調査系 | OSM/ODPT/e-Stat/気象庁 | **混在**(下記行参照)・v1の取得台帳 _ledger.jsonl 同梱 | △ | 層分離の再編はPhase 2で実施 |
| data/realworld(OSM由来分) | 渋谷の地図・POI 2,337 | OpenStreetMap | **ODbL 1.0** | △ | 公開・配布時にshare-alike発火。出力にOSM生値を載せない設計で回避 |
| data/realworld(気象分) | アメダス実測(v2手元は35日=2026-07-28〜08-31。930日はv1時点) | 気象庁 | PDL 1.0相当 | ○ | 外部提供時「予報」でなく過去実績/仮想シナリオと明示(気象業務法17条) |
| data/realworld(統計分) | 経済センサス9,872社・国勢調査 | e-Stat | 政府標準利用規約2.0 | ○ | 出典表示 |
| data/plateau | 渋谷3D建物3,531棟 | 国交省PLATEAU | PDL 1.0(CC BY 4.0互換) | ○ | **データセット×年度でライセンス個別確認**(ODbL混在の可能性) |
| data/odpt | 駅・路線マスタ | ODPT | 基本ライセンス | △ | 商用化時はCC BY/CC0/PDLの107件へ絞る(答申) |
| data/persona_pool_v2 | 100万ペルソナ(国勢調査IPF較正+LLM生成来歴) | 自家生成(上流=e-Stat統計) | 自家 | ○ | 統計からの合成=個人情報非該当と整理可(PPC Q1-17/Q1-8類推)。生成LLMのライセンス貫通に注意 |
| data/calib | v1較正パラメータ(sigma_c/theta_scale) | 自家生成 | 自家 | ○ | |
| data/ground_truth | **現実整合アンカー台帳 registry.yaml(37本・出典/holdout分割付き)** | 各アンカーの出典はregistry内に記載 | 引用 | ○ | 北極星KPIの物差し。v2で成長させる |
| data/jinryu | 渋谷人流(1kmメッシュ2019-2021・同時滞在カーブ) | data/jinryu/SOURCE.md 参照 | SOURCE.md 参照 | △ | 較正専用・生データ再配布しない |
| data/realworld/osm(2026-09-06複写・v1由来) | 渋谷OSM地図v8(ノード3,499・エッジ4,944[地上4,448/デッキ306/地下190]・POI 2,337[営業時間・価格なし]・建物7,210)+**架空組織台帳**(organizations_*.json=v1の手続き生成・seed 42・経済センサス町丁目別に較正・実在名なし=名寄せ不可)+建物高さ・横断歩道・フロアガイド | OpenStreetMap / 自家生成(上流=e-Stat) | ODbL 1.0 / 自家 | △ | 出力にOSM生値を載せない(内部ID+集計のみ)・osm_date凍結 |
| data/realworld/kddi_la(2026-09-06収載) | KDDI Location Analyzer 滞在人口・通過人口(5エリア×24h×属性・2024年)=Power BI公開ダッシュボード由来の生JSON(2万行)+渋谷区オープンデータ日次CSV(shibuya_jinryu/2026) | 渋谷区オープンデータ／KDDI・技研商事 | CC BY 4.0(区OD)・ダッシュボード由来分は同系列として出典表示 | △ | 較正には使わず事後検証専用(holdout)・出典表示必須 |
| data/realworld/estat(2026-09-07取得) | e-Stat API取得JSON: 国勢調査2020 昼間/夜間人口(渋谷区)・経済センサス2021 企業等ベース集計(渋谷区) | e-Stat(総務省統計局) | 政府標準利用規約2.0 | ○ | 出典表示(「e-Stat」+統計名+年次)・APIキーは環境変数のみ |

## 持ち込まなかったもの(意図的)

| 資産 | 理由 |
|---|---|
| data/odpt_challenge(73件) | **チャレンジ限定ライセンス=用途限定**・事業化に使えない可能性大→本番構成から除外(答申推奨) |
| data/juelich_ped(146MB) | 群衆物理の較正ベンチ。U15(ORCA/SFM)判断まで保留・必要時にv1からコピー |
| v1の runs/・Chronicle成果物 | v1リポに残置(参照専用) |

## モデル方針(答申の要約)

主軸=**Qwen3系(Apache 2.0・取消不能)**・日本語補強=CALM3/Sarashina2(Apache/MIT)。Swallow/Llama系は研究フェーズ限定(二重ライセンス・命名義務)。採用時は重み+ライセンス原文をハッシュ付きアーカイブ。
