# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **4 / 10**
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

## 第283 R-51(単純接触・偶発的接触)と R-52(群集較正・渋谷計測)の親検収 → M17 の形・D-122 §3-4・U-9 の判定(2026-09-28)

- **検収**: R-51 の数値 5 件(Zajonc 対数則・Ferraro 17.1/21.6/40.0%・Seamon 60.5/65.0 vs 再認 50.8・Schooler & Hertwig の 2 閾値と活性順の走査・Barbosa κ 23.6/64.3)と R-52 の 5 件(JuPedSim のソース 3 行・Helbing 1995/2000・ShibuyaSocial・PLATEAU 技術資料 22・渋谷区交通戦略)を親が原典で一致。INDEX・backlog に 2 行。
- **訂正の伝播 3 件**(親): R-7(信号 140 s は個人ブログのみ → 学術 2 本で一致)・R-42 §7-3(3,000 人の出所を朝日 2016 まで追跡・一次は依然なし)・**広告答申 4-C (ii) の循環参照**(「ε は AD4 で較正」は AD4=holdout と矛盾 → AD1/AD4 は照合専用・ε/β は宣言+感度腕)。
- **封印の判定**: パターン台帳に「スクランブル通行量」の封印行は無い(封印は `shibuya_jinryu`/`boundary_counts` だけ)。R-52 が本文に書いた渋谷の計測値 A17〜A20 は公刊の粗い値=**validation(開封済み)扱い・較正には使わない**。U15-6 の「holdout 面」は validation 面に読み替え。
- **M17 の形**(記憶アジェンダ v1): 親推奨=α(走査順 rank′=rank−β·A)+候補入り確率(ACT-R 想起確率・s=0.25 宣言)・2 閾値 τ_high/τ_low・飽和は感度腕・τ は分単位で文献値は移せない・K=64 は κ 64.3 と同桁。
- **D-122 v0.2**: §3-4 に錨 A1〜A16 と分割(較正=Jülich+原典の定数 / validation=KDDI 3 ストリート+A17〜A20 / test=封印層)・U-9 の判定(公的一次なし・区への照会の前例・ATR は研究目的のみ)。**P1〜P10 は答えられる**。
- **次**: ユーザーの答え(D-122 P1〜P10・D-102 Q1〜Q9・M17 の形・U-9 区への照会の可否)。実装役の段 1a 帰還 → 検収 → commit。

## 第284 W6 再生成 段 1a の親検収と commit(IMPLEMENTED #49)・段 1b/1c の発注(2026-09-28)

- **実装役の 1 回目**は W6 のゲート(タグの cat と v8 の cat が矛盾する POI 3 件)で止まり問い 4 件。親の決め: Q1 期待値 3 で記録(cat は動かさない)/ **Q2 build runner に凍結段の口 `--keep-stage` と昇格版の上書き拒否**(素直に回すと W17 v2 を v1 応答で上書きする経路を実装役が発見=道具の変更として承認)/ Q3 規則を足さず空欄 / Q4 D-96 の予想の訂正 / ダッシュボードのパーサを新 PENDING 形式へ。
- **親検収(再実行)**: build `--keep-stage W17` → build_hash 75b264cb・kept・21 段 / `--keep-stage` 無し → exit 2 で拒否 / W17 md5 3113e9ba7abb・header 不変 / W6 notes に矛盾 3 件と未分類 4 件 / 2 腕の final 02bd0312・2f3969cf 不変 / 全体 2,977 件(failed 0・skipped 1)exit 0。engine/perception/world に subcat の読み手が無いことを grep で確認(実装役の主張と一致)。
- **発見**: W6 再生成で既定 checkpoint は **15 腕とも final 不変**。D-96 の「6 種が動く」は外れ。動くのは 17:59 の world_hash だけ(琥珀の営業窓 17:00→22:00・W7 の 1 行)。subcat の効果は W17 の再生成(場所語の解決)で初めて現れる=来街者の作り直しの回。
- **次**: 実装役に 1b(eatery 切替口・既定不変)と 1c(W10 道路名突合・D-1 (a))を発注。ユーザーの答え待ち=D-122 P1〜P10・D-102 Q1〜Q9・M17 の形・U-9。
