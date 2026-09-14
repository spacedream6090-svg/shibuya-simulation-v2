# v2ゲーム/VR産業技術の輸入リサーチ答申(2026-08-31・Opusサブエージェント・全出典URL付き)

<!-- hdr:v1 -->
- **分野**: ゲームエンジン工学・CG #30 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **D** = **出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る — 出典痕跡 1 件・URL 0 件。09-02 以降の中央値 62 に対して桁が違う
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> FE方針(ゲームを作らない・技術知見を輸入する)に基づく調査。各技法に適用先(コア/ビューワー/データ契約)を明示。

## 結論: 今すぐ輸入すべき技法トップ5

| # | 技法 | 適用先 | 根拠 |
|---|---|---|---|
| 1 | **checkpoint+デルタ+タグ付きイベント索引の三層リプレイ契約**(checkpoint保存は時間スライスしてstepを止めない) | データ契約+ビューワー | UE Replay/StarCraft II/LoL観戦の3業界が独立に同形へ収束。UEの`CheckpointSaveMaxMSPerFrame`=「観測が本体を遅らせない」の直接解 |
| 2 | **アーキタイプ/チャンクSoA+existential processing**(全個体ループ廃止・発火index配列のみ回す・チャンク単位メタで丸ごとスキップ) | コア | Unity DOTS 16KBチャンク・UE Mass ChunkFragment・Acton「複数形で設計せよ」。40万体で唯一スケールする形 |
| 3 | **重要度付き部分スナップショット配信**(Importance/Relevancy+量子化+帯域クランプ+静的個体は送らない) | ビューワー+データ契約 | Unity Netcode(MTUクランプ=部分スナップショット)+Quake3(「古い情報は再送しない」)+Replication Graph(グリッドで総当たり関連性評価を消す・Fortnite 100接続×5万アクタ実績) |
| 4 | **認知LOD階層+on-demand昇格**(遠景=統計移動/中景=テンプレ行動/注目時のみLLM思考へ昇格・プール入替) | コア | AC Unity(実AI40+高解像度120で画面内1万体)・Hitman Absolution(群衆1200体・必要時に本物NPCへ昇格)・UE MassLOD(表現とtick頻度の両方を切替)。**LLM予算配分則そのもの** |
| 5 | **スマートオブジェクト広告+utilityスコアリング**(行動は場所/役割の側に置き、個体は広告を欲求で採点するだけ) | コア(層2) | The Sims(Forbus&Wright: オブジェクトが行動を広告→拡張パックが成立した理由)+IAUS。GOAPは再計画コストで落ち・BTは先読みせず・**utilityは選択理由が数式で読める**=説明可能性。新しい場所/役割の追加が認知コードを触らない |

次点: 空間グリッド分割を近傍検索・関心領域の共通基盤に(World Partitionセル+Grid Spatialization 2D)=#2-4の土台。
採らない判断: USD/Omniverseのフォーマット丸ごと採用・cuOpt・Warp移植は「原理だけ借りる/頭打ち実測後」で足りる。

## 分野別の要点(事実)

- **DOD/ECS**: Acton 2原則(「プログラムの目的はデータ変換のみ」「単数でなく複数形で設計」)・Fabianの
  リレーショナルモデル化+existential processing(存在する=そのテーブルに載っている、でifを消す)。
  Python翻訳の先行=AgentTorch(完全テンソル化・数千万体・微分可能)。
- **World Partition**: グリッドセル+ストリーミングソース(カメラ)距離で自動ロード・Data Layers=状態駆動の
  非破壊オーバーレイ。→観測窓=streaming sourceを複数置ける設計・シナリオ/介入層のオーバーレイ思想。
- **Quake 3ネットコード**: 32スナップショットリング+最終ACK差分・全ゼロダミーとの差分でフル更新が同一コードパス・
  フィールド毎変更1bit+事前Huffman。哲学=「初回で届かない情報は再送する価値がない」。
- **The Sims smart objects**: 行動はオブジェクト側・motiveに対しスコアリング・ツリー/トークン表現。
- **Watch Dogs: Legion Census**: 手続き生成層(人口統計整合)+シミュレーション層(永続化+動的日程)の二層
  =「40万体に統計整合の背景+日程を与える」当方の要件とほぼ同一問題。
- **NVIDIA**: Warp=Python関数をJITでCPU/GPUカーネル化(numba頭打ち時の次の一手・torch連携可)・
  OpenUSD=レイヤ合成による非破壊上書き(**原理だけ輸入**: base世界+シナリオ層+介入層+観測層)・
  cuOpt=VRP/LP(経路一括前処理に限れば有用・優先度低)。
- **VR/メタバース**: VRChat=並列インスタンス(1インスタンス20-80人×無制限)・Fortniteイベント同時12.3M=
  多数の小インスタンス同時開催。→「シムは1本・観測は多数のread-only fanout」が業界標準に沿う。
- **リプレイ商用実装**: UE Replay(checkpoint=差分スナップショット30秒間隔+時間スライス+**タグ付きイベントで
  全DLなし検索**)・SC2(.SC2Replay=game.events/tracker.events/message.eventsの分離収録)・
  LoL観戦(30秒chunk+2chunkに1 keyframe+観戦遅延)。

## 当方設計との対応(推測)

- #1はD6決定(案b)と整合: 足りないのは「タグ付きイベント索引」と「checkpoint時間スライス」の2点→データ契約に追記候補。
- #4は憲法1(打ち切りでなくLOD)の実装形。境界規則「言葉は必ず心を通る」は昇格条件として保存
  (遠景でも発話が要る場面は昇格させる)。
- #5は層2「役割+行動プリミティブ」の正しい実装形(affordance広告)+Watch Dogs Censusは人口/日程の参照設計。

## 主要出典

Acton CppCon 2014・dataorienteddesign.com(node3/node4)・Unity DOTS ECS concepts・UE Mass Entity/MassLOD・
World Partition/Data Layers・Interest Management(ACM CSUR 46(4))・Fabien Sanglard Quake3解説・
UE Replication Graph・Unity Netcode ghost snapshots/compression・Forbus&Wright(The Sims・北西大QRG)・
Game Developer(GOAP/BT/Utility比較)・GDC: AC Unity群衆/Hitman Absolution群衆/Watch Dogs Legion Census・
NVIDIA Warp/OpenUSD/cuOpt・VRChat docs・Epic公式(Astronomical 12.3M)・Roblox(Game Developer)・
UE DemoNetDriver/Replay System・sc2reader/s2protocol・LoL観戦gist・AgentTorch。(URLはリサーチ実行ログに完全版)
