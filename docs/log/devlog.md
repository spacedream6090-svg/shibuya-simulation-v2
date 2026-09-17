# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **2 / 10**
> 第1〜第230(2026-09-01〜09-17)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第231 記憶 brief 帰還・親確認 3 件・アジェンダ v0(2026-09-17 夜)

- **brief**([v2-memory-brief.md](../design/v2-memory-brief.md)・6 節・未決 15・問い 16・空欄 15)。**親確認**: ① `run.py` `plan_sleep=True`(D-62)で就寝境界は LLM を呼ばず、`n_reflections` は `resolve.py:1890`(行動語「就寝」)だけ・c7-day-4 テープに就寝 0 → **本番の内省は 0 発火** ✓ ② 予算 L7=T2 2,048 tok・c7-day-4 実測 3,046.9 tok/s → 8.6 億 tok=**78.4 h/日** ✓ ③ `Registry.state_hash` は宣言順の全配列を混ぜる=欄追加は腕でだけ ✓。
- **アジェンダ v0**([v2-memory-agenda.md](../design/v2-memory-agenda.md)): M1〜M16 に親推奨(エピソード=ID+結果コード・A(m) 下限+N=128・重要度固定表・想起 会話 3/計画境界 2 を B5 記憶 60 tok・埋め込みは腕で後・内省=就寝直後 1 呼 8B 128 tok 要旨 3 本・関係 ±1 は書かせない・EventClass+想起 ID 列・D-93 (a)・訪問カウンタ先・ablation 1 表・合格線 K-2〜K-4・τ 固定+感度)+実装 3 段(記録と想起 → 内省 → 関係・習慣への接続)。
- 判断待ち: **記憶 M1〜M16**・D-93 (a)〜(d)・D-94・D-92 解釈・D-91・ハーネス 4 問・push/PR/未踏。実行中: R-37・W6・D-59。

## 第232 D-59 実装 親検収・R-37 帰還・親確認 3(2026-09-17 夜)

- **D-59 (b)** → IMPLEMENTED #36: `--signage-p-see`(決定論ベルヌーイ・既定 1.0 は抽選 0 回)+腕 AB6b(1.0/ad_zero/0.30/0.14)。親検収 171 passed・変異 11 本失敗・ba01bd0b 不変。写し訂正: 実測帯は 中小 0.14〜0.40/大型 0.63〜0.78(「0.79」は誤り)。次=サーバー 4 腕(約 2.5 h)。
- **R-37**([答申](../research/v2-destination-choice-llm-research.md)・lit 7): H の先行はシミュ側に無く主流は逆向き。When Plausible(親確認 HTML §5.1): 集計 STVD は重力則 607.69 < LLM 748.71・個体 Δr 14.83→7.53=符号が逆。LLM-Move(親確認 Table IV): 並べ替えだけで .52→.20。k=3〜5 一次あり。渋谷はセル内 POI 中央値 4=複数セル跨ぎ必須。合否は P-6/P-8。**親の誤り訂正**: 任務文の「探索は距離の逆冪 δ 1.2」は α 0.55 と δ 1.2 の取り違え(docs には未伝播・答申内で訂正)。**実物確認**: `hash_free_cat_code` は nightlife 259 件を飲食コードに入れない → W6 サブへ追加指示(SendMessage)。
- 判断待ち: 記憶 M1〜M16・D-93 (a)〜(d)・D-94・D-92 解釈・D-91・ハーネス 4 問・push/PR/未踏。実行中: W6。
