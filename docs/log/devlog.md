# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **2 / 10**
> 第1〜第280(2026-09-01〜09-28)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第281 R-54/R-55 の親検収・D-122 草案 v0・D-102 設計書 v0.1(2026-09-28)

- **検収**: R-54(前提検査の棚卸し 71 件=空間 25/ルール 35/両方 11)の主張 5 件と R-55(checkpoint・乱数・再開)の主張 5 件を、親が同じ行を印字して一致。INDEX・backlog に 2 行。
- **D-122 草案 v0**([空間層の草案](../design/v2-spatial-physics-layer-draft.md)): 第一原理の分解=実現可能性は「届くか・見えるか・入れるか」の幾何の問い 3 つ+規則。**S 層(静的クエリ=G13 そのもの: W3 の距離表 `cell_dist`・W8 のセル間視線 `w8_t2`・PLATEAU 面積×法定 3.0 は既に在るのに実行時に読まれていない)を先に、D 層(動力学=U15 の LOD)を後に**が親の推奨(P1 (b))。6 項目の吸収可否・失敗の返し方(新コード TOO_FAR/FULL_ON_ARRIVAL・呼数は上限 +0.2/体/日)・移行(セルは下に敷く・checkpoint は段ごとに 1 回)・P1〜P10・段階案 S1〜S3→D1〜D3。§3 のエンジン比較と較正は R-53/R-52 の帰還後。
- **D-102 v0.1**([再開と決定論の設計書](../design/v2-resume-determinism-draft.md)): R-55 の事実で §4 を埋めた。**複数日の障害 2 つ**=乱数・run_salt・call_id・テープの鍵に日番号が無い(Q7)・状態を持つ乱数 2 本(Q8)。behavior-hash/full-hash(Q1)・死蔵 3 列の削除(Q9)を追加=Q1〜Q9 答えられる。
- **次**: R-51/R-52/R-53 の帰還 → M17 の形・D-122 §3・較正表。実装役の段 1a 帰還 → 検収 → commit。

## 第282 R-53(物理・群集エンジン候補の事実)の親検収 → D-122 草案 v0.1(2026-09-28)

- **検収**: 決定論の逐語 7 件(PhysX docs+ヘッダ「not currently supported on GPU」・Jolt「Broadphase queries … NOT deterministic」「8% slower」・Box2D「across thread counts and platforms」「on by default」・Rapier「locally deterministic」「parallel … identical to the sequential」・ORCA「5,000 agents on eight cores … 8 ms」・GPU ORCA「33ms per frame … 5 × 10^5」)を親が原典で一致。INDEX・backlog に R-53。
- **D-122 §3 を埋めた**([空間層の草案](../design/v2-spatial-physics-layer-draft.md) v0.1): 候補 × 軸の表(同じ環境での決定論を公式に言うのは PhysX(CPU)・Box2D・Jolt(問い合わせ順を除く)・Rapier。群集実装 RVO2/JuPedSim/Menge/Vadere は保証文なし=採るなら固定順序を自前で保証かテープ)・規模の外挿(39 万体 0.1 s 刻み=CPU 150〜292 h/日・GPU 6.2 h/日・5,000 体 CPU 1.9 h/日)・テープ(tick 末の位置で 4.49 GB/日=S1 のほぼ全量・刻みごとは不可)・2 時間軸の先行(3 層・SUMO action-step・Unity DecisionPeriod)・**席の意味論はどの実装にも無い**(満席は S 層=面積×法定係数)。残る空欄=R-52 の較正表と U-9 の判定。
- **次**: R-52 帰還 → §3-4 → ユーザーに P1〜P10。R-51 帰還 → M17 の形。実装役の段 1a 帰還 → 検収。
