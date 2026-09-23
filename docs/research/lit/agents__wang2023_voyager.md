# Wang et al. 2023 — Voyager: An Open-Ended Embodied Agent with Large Language Models

- リンク: https://arxiv.org/abs/2305.16291 | 分野: 自然言語処理 #27 / ABM 方法論 #21 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが `ar5iv.labs.arxiv.org/html/2305.16291` 本文を取得。**付録は取得が途中で切れている**=剪定の有無は本文範囲での判定)。**親未確認**。v1 2023-05-25 / v2 2023-10-19。著者 Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu, Linxi Fan, Anima Anandkumar。

## 主張(claim)

LLM エージェントは、**成功した行動プログラムを庫に貯めていく**ことで、追加学習なしに能力を増やせる。3 部品=自動カリキュラム / **スキル庫** / 反復プロンプト(環境フィードバック・実行エラー・自己検証)。

## 機構(mechanism)— 「いつ庫に入るか」がこの repo の関心

- §1「Voyager incrementally builds a skill library by storing the action programs that help solve a task successfully.」
- §2.3「until self-verification validates the task's completion, at which point we add this new skill to the skill library」——**登録の条件は「自己検証が課題の完了を認めた」1 回だけ**。頻度でも投票でもない。4 回の生成で解けなければ別の課題へ移る(付録 A.1 の擬似コードでは失敗課題を記録)。
- **自己検証**: 別の GPT-4 インスタンスに状態と課題を渡し「act as a critic」させ、達成したかを答えさせる。失敗なら「provides a critique by suggesting how to complete the task」。
- **索引と検索**: §1「Each program is indexed by the embedding of its description, which can be retrieved in similar situations in the future.」/ §2.2「we query the skill library with the embedding of self-generated task plans and environment feedback」。Fig.4 = ベクタ DB・鍵は GPT-3.5 が書いた説明文の埋め込み・値はプログラム・問い合わせ時に **top-5** を引く。
- **重複排除・剪定**: 本文に**記述が無い**。庫は abstract で「ever-growing」、§2.2 で「継続的に拡張される」とだけ。

## 数値(出所つき)

- §3.4 ablation: **自己検証を外すと発見アイテムが −73%**。「a critical mechanism to decide when to move on to a new task or reattempt a previously unsuccessful task」。
- 検索は top-5(Fig.4 caption)。生成の再試行は最大 4 ラウンド(§2.3)。

## 効く箇所(seam)

[行動契約書 §7](../../design/v2-action-contract.md) 段2〜4。**Voyager は段2 を「ラン中・1 回の成功で・自動採用」で回す設計**=D-71 のユーザー決定(ラン内に裁定を入れない)の**対極**。両者の差は「採用の可逆性」——Minecraft は誤った技能を入れても世界の整合が壊れないが、v2 は保存則と現実整合アンカーを持つので壊れる。

## 「結論でなく機構として」の入れ方

- **借りない**: 自動採用・オンライン書き戻し・埋め込み索引での top-5 検索(v2 の契約表は決定論参照であるべき)。
- **借りる**: (1) **自己検証を別インスタンスに分ける**(起草者と検査者を分ける)という形。v2 の「裁定 T2 → 自動検査 → 親検収」は同じ向きで、検査を機械側に寄せたもの。(2) **「検証を外すと −73%」=検証の段が無い獲得は機能しない**という外部根拠。(3) **剪定機構が無いことが後続論文(SkillBrew 2026)に批判されている**という系譜=v2 は最初から使用率の計測を入れる根拠。

## コスト/スケール含意

自己検証が 1 課題あたり追加 LLM 呼を要する。v2 でこれをラン内でやると呼数予算に直撃する——**オフラインなら未定義台帳の語数(数十)にしか比例せず、ラン費用はゼロ**。これが D-71 のオフライン案の費用面の利点。

## 批判・限界

- 単一環境(Minecraft)・単一モデル(GPT-4)。**社会シミュではない**。
- **庫が単調増加**で、誤って入った技能を外す機構が無い(SkillBrew 2026 の批判対象)。
- 自己検証は LLM の自己申告で、外部の真値と照合していない。
- **獲得の判定基準が「1 回の成功」**なので、偶然通った草案がそのまま能力になる。v2 の 4 検査(答申 §2-C)はここを埋める設計。

## 関連

[[agents__wang2024_workflow-memory]] ・ [[agents__wang2025_programmatic-skill-induction]] ・ [[agents__zhao2024_learnact]] ・ [[cbr__aamodt1994_cbr-cycle]] ・ [D-71 答申](../v2-d71-vocab-growth-research.md) §1.1
