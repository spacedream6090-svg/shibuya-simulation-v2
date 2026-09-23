# v2ゲーム的フロントエンド リサーチ答申(2026-08-30・Opusサブエージェント・全出典URL付き)

<!-- hdr:v1 -->
- **分野**: ゲームエンジン工学・CG #30 | **重要度**: P1(親判断・2026-09-15 第191)
- **一次確認**: **D** = **出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る — 出典痕跡 4 件・URL 0 件。09-02 以降の中央値 62 に対して桁が違う
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> N1(ゲーム的ハイブリッド)の深掘り。方針=コアheadless・ゲーム側は再生+介入・介入=記録される実験条件。

## 最重要の3所見

1. **PLATEAU側は既に解決済み**: 3D渋谷はCesium ion「Japan 3D Buildings」(2024-06・2300万棟・3D Tiles)か
   PLATEAU公式3D Tiles/MVT配信サービスで「読むだけ」。Unity/Unreal用PLATEAU SDKも2023年から正式版(MIT)。
   自前でCityGMLを焼く工数は原則不要。
2. **「LLM社会シムのリプレイ+介入記録」は先行実装が空白**: AgentSociety(清華・1万体)はコア/GUI分離
   (MQTT 3トピック: agent-chat/user-chat/user-survey=構造化JSONサーベイ投下)まで到達したが**リプレイの記述なし**。
   Generative Agentsはリプレイ(/replayエンドポイント)を持ち**論文の評価自体をリプレイ視聴で実施**したが25体。
   40万体×リプレイ×介入記録は未踏=v2の明確な差別化点。
3. **見た目の忠実度は信頼を生まない(国交省実測)**: PLATEAU uc25-05(AIマルチエージェント・Unity+ローカルLLM)で
   結果の信憑性を高評価した自治体職員は**11人中4人のみ**。ゲーム化は「なぜそうなったか」の追跡可能性
   (Chronicle+介入provenance)とセットでなければ逆効果になりうる。

## 技術比較(事実)

- **deck.gl**: 公式性能文書でScatterplotLayer等は**約100万点まで60FPS**(1000万点で10-20FPS)・picking 16M件/レイヤ。
  ボトルネックは描画でなくGPUバッファ再生成。40万体は公称の半分以下で射程内。
- **three.js InstancedMesh**: 公式上限記載なし・ジオメトリ複雑度依存が大。点/スプライトなら可、アニメキャラ40万は非現実的。
- **Unity DOTS/Entities Graphics**: 公式は上限非公表(バッチ効率指標のみ)。実例は10万体級(Crowd Skinner等)。
- **UE5 City Sample**: **歩行者35,000人**がMass AI+Naniteの公開実績上限。
- **Godot 4**: 40万体級の公開実績・ベンチなし→本件では劣後。
- **rerun.io**: マルチレート時系列の同期スクラブビューア(rrd/MCAP対応)。開発中の検証ビューアとして最短距離。
- **国交省uc24-07(汎用人流シミュ)**: 変換/シミュ/可視化の3分離・中間IF=**MF-JSON(OGC Moving Features)**
  =「headlessコア+別ビューア」と同型の公式前例。

## 再生+介入の設計知見

- **Computational steering**(確立分野): 可視化がシムを同期ブロックしないこと(in-situ/in-transit・Catalyst 2+ADIOS2)が中心命題。
  介入はtick境界にのみ適用・ビューアは状態変更を持たない。
- **RTS決定論リプレイ**(初期状態+入力ストリーム再実行)はLLM非決定性のため不可→
  **「checkpoint=Iフレーム+行動イベント=Pフレーム」の再生型ハイブリッド**が正解(v2の観測3階建てと同型)。
- **介入の記録契約**: `{intervention_id, tick, actor, target_selector, params, provenance}`をイベントログに同居+
  各checkpointに有効介入セットのハッシュ→「どの実験条件下の再生か」が自明・検収不変性と両立。
  学術語彙は**analytic provenance**(Trrack等)。
- 神視点UIの規範: SimCity GlassBox「**What You See Is What You Sim**」=画面上の事象は常にシムの1:1表現
  (ビューアが独自に補間・演出したものは描かない)。RimWorld/DF共通文法=一時停止+速度段階+個体インスペクト。
- 群衆LOD: CGF 2016サーベイ=多角形/点/インポスタ3系統+実行時LOD選択。

## 収益・コミュニティ(事実→示唆)

- EVE Project Discovery(既存ゲームに研究タスク埋込・2週で500万画像)・Foldit・UN-Habitat Block by Block
  (Minecraftで参加型都市デザイン・37カ国25,000人)。
- 示唆: 研究シムの直接B2C収益例はほぼ無い。現実的な出口=**行政・企業向け参加型ワークショップ(Block by Block型)**
  +「社会の風洞」B2B。

## 推奨3段階案

- **初期(2-4週)**: deck.gl主体(three.js資産継承)・40万体=ScatterplotLayer 1枚・背景=PLATEAU MVT/2D。
  checkpoint+デルタのタイムラインスクラブ。介入UIは最小(pause/速度/個体インスペクト/イベント注入1種)。
  GlassBox規律採用。最大の価値=「任意時刻に飛べること」(Generative Agentsの評価様式に倣う)。
- **中期(1-2ヶ月)**: Cesium ion Japan 3D Buildings/PLATEAU 3D Tilesを載せ3D化。遠景=点・中景=ビルボード・
  近景=スプライトのLOD。**介入の一級化**(AgentSociety 3トピック型+provenanceグラフ)。
- **長期(3ヶ月+・必要なら)**: Unity+PLATEAU SDK+DOTSのネイティブ観戦ビルド(視錐台+LODで常時数万体に制限)。
  UE5はCity Sample実績で見栄え上位だがPLATEAU SDK for Unrealの成熟度で不利。Godotは非推奨。

## 接続IF要点

checkpoint(6h・全状態)+イベントログの二層/配信・スクラブ=MCAP系(O(1)時刻シーク)・分析=Parquet/
外部相互運用=MF-JSON/ワイヤはint16量子化+差分符号化で1tick40万体3MB→1桁削減可。

## 主要出典

deck.gl performance docs・Unity Entities Graphics docs・UE5 City Sample・Godot MultiMesh docs・rerun.io・
PLATEAU SDK for Unity(GitHub/MIT)・PLATEAU 3D Tiles配信・Cesium ion Japan 3D Buildings・uc25-05・uc24-07・
computational steeringサーベイ(TU/e)・Catalyst-ADIOS2(arXiv 2406.18112)・Generative Agents(UIST'23)・
AI Town・Project Sid(arXiv 2411.00114)・AgentSociety(arXiv 2502.08691)・OASIS(arXiv 2411.11581)・
AgentTorch・OGC都市DT要件(24-025)・ProvenanceWidgets/Trrack・MCAP・CGF 2016群衆LODサーベイ・
SimCity GlassBox(GDC 2012)・EVE Project Discovery・Block by Block Playbook。(URLはリサーチ実行ログに完全版)
