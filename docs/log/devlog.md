# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **1 / 10**
> 第1〜第230(2026-09-01〜09-17)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第231 記憶 brief 帰還・親確認 3 件・アジェンダ v0(2026-09-17 夜)

- **brief**([v2-memory-brief.md](../design/v2-memory-brief.md)・6 節・未決 15・問い 16・空欄 15)。**親確認**: ① `run.py` `plan_sleep=True`(D-62)で就寝境界は LLM を呼ばず、`n_reflections` は `resolve.py:1890`(行動語「就寝」)だけ・c7-day-4 テープに就寝 0 → **本番の内省は 0 発火** ✓ ② 予算 L7=T2 2,048 tok・c7-day-4 実測 3,046.9 tok/s → 8.6 億 tok=**78.4 h/日** ✓ ③ `Registry.state_hash` は宣言順の全配列を混ぜる=欄追加は腕でだけ ✓。
- **アジェンダ v0**([v2-memory-agenda.md](../design/v2-memory-agenda.md)): M1〜M16 に親推奨(エピソード=ID+結果コード・A(m) 下限+N=128・重要度固定表・想起 会話 3/計画境界 2 を B5 記憶 60 tok・埋め込みは腕で後・内省=就寝直後 1 呼 8B 128 tok 要旨 3 本・関係 ±1 は書かせない・EventClass+想起 ID 列・D-93 (a)・訪問カウンタ先・ablation 1 表・合格線 K-2〜K-4・τ 固定+感度)+実装 3 段(記録と想起 → 内省 → 関係・習慣への接続)。
- 判断待ち: **記憶 M1〜M16**・D-93 (a)〜(d)・D-94・D-92 解釈・D-91・ハーネス 4 問・push/PR/未踏。実行中: R-37・W6・D-59。
