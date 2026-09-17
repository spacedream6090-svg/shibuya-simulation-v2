# Ju, Liu, Sinha, Xue & Salim 2025 — TrajLLM(WWW 2025 Demo): 定量評価が存在しない

- リンク: https://arxiv.org/abs/2502.18712 (WWW 2025 Companion, doi:10.1145/3701716.3715201) | 分野: 人間移動科学 #3 / 自然言語処理 #27 | 重要度: P2
- **一次確認**: **実読(サブ・2026-09-17・arXiv HTML v1 全文)・親未確認**
- 主張(claim): 既存答申の「TrajLLM の定量評価は未確認」の答えは **「評価そのものが存在しない」**。デモ論文であり、実験節も結果節も無く、評価に関わる数値が本文に 1 つも無い。
- 機構(mechanism): ペルソナ生成 → 活動選択 → 目的地写像の階層 + 記憶モジュール(日次→週次→月次の要約と重要度剪定)。目的地は LLM 版と物理モデル版(空間モジュール = 距離減衰・頻度モジュール = 履歴)の 2 通り。
- 効く箇所(seam): 既存答申 §4 の表「LLM 人流生成は集計分布(JSD)でしか評価していない」の**最も弱い実例**。v2 が事前登録で個体指標を凍結する方法論的新規性の根拠。第2陣の記憶設計の**採らない道の基準線**。
- 「結論でなく機構として」の入れ方: 記憶の重要度スコア(情報密度 × 新近性 × 参照頻度を sigmoid で正規化)を**真似しない**。著者自身が重みの根拠が無いと書いている=設計者の指紋そのもの。
- 数値(節番号まで):
  - **節構成**: 1 Introduction / 2 Framework Architecture(2.1 Persona / 2.2 Activity / 2.3 Destination / 2.4 Memory)/ **3 Demonstration** / 4 Conclusion / 5 Ethical Use of Data。**実験節・結果節が無い**
  - 本文中の数値を全数抽出した結果、評価に関わる数値は **0 件**(現れるのは節番号・arXiv ID・参照 DOI のみ)
  - 逐語(抄録): 「**Preliminary results indicate** that LLM-driven simulations align with observed real-world patterns」— 比較対象も指標も書かれていない
  - 逐語(§3): 「the visualization presents a sample of **one-day trajectories for ten agents in Tokyo**」
  - データ: 「the public check-ins dataset of Tokyo」を POI として使用。ペルソナは「population statistics collected from local government」+ Big Five
  - 逐語(§2.4・重み): 「While these references provided a conceptual basis for assigning weights, **the actual numerical values were determined independently during development**」
- コスト/スケール含意: なし(10 体のデモ)。Flask バックエンド + Leaflet.js の可視化。
- 批判・限界: 4 頁のデモ論文なので評価が無いこと自体は責められない。**問題は既存答申がこれを「評価軸を持つ先行」の候補として数えていたこと**。個体多様性どころか集計分布の一致も測られていない。記憶の重み・剪定閾値は「反復的なテスト」で決めたとあるだけで、値も手順も公開されていない。
- 関連: [[compute__alves2026_llm-urban-mobility]]・既存答申 v2-d68-behavioral-diversity-research §4(LLMob / MobiGeaR / MobilityGPT / TrajGenAgent / When Plausible)
