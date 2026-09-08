# 工程 C3(知覚・LLM接続層)受入報告(進行中・2026-09-08・ブランチ build/c0-c4)

> 根拠: 実装計画書 §9.1 C3 行(レンダラ B0-B6+チャネル上限+正規化規約9項+ハッシュ三役+変化検出+注意ゲート0-2+p_notice(2段ヒル)+パーサ(2行形)+未定義行動5段+行動契約12語+会話1呼1発話ブロック+診断行。検収=golden バイト一致(同セル2体で B0-B4 差分0)・契約テスト・チャネル上限テスト・mock 5,000体で診断行5本)。証拠=親自身の実行出力のみ。

## 1. 契約側(サブF: llm/contract・parser・undefined・engine/conversation・llm_bridge・run 結線)= 親検収済み

```
$ .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -o addopts=""      (全体)
614 passed, 1 xfailed in 93.18s
$ .venv/Scripts/lint-imports.exe → Contracts: 5 kept, 0 broken.
$ python tools/scan_secrets.py <new+modified> → CLEAN
$ pytest tests/engine/test_tape_wiring.py -s   (5,000体×1,440 tick・seed 1・合成139セル)
[record] 2fd1c081…(結線前・スタブ)→ 結線後(層2再実行・合成139セル): 7363c14b44808cd30101d676f7568c303854cc2df46827f11bc0042c2d58dbf0 = [replay]
  呼 44,887 / テープ 44,887 行 / テープ外 0 / 書式エラー率 0.0000
```

| 受入項目 | 実測 | 判定 |
|---|---|---|
| 行動契約 12語+種別固有 12語=24語(§2.2 の 指示/並ぶ/撮影を含む)を `llm.contract` に正典化(前提/効果/コスト/失敗文言を逐語・失敗コード写像) | 契約テスト合格 | 済 |
| 2行形パーサ(ラベル基準・寛容・4行形も受理・行内ラベル分割・例外なし=hypothesis) | 書式エラー率 0.0000(mock) | 済 |
| 未定義行動5段(辞書写像→記録+失敗FB→N=10体で裁定1呼→保存則/性能に触れる行は親検収まで不採用→採用=判例化) | 段ごとのテスト合格 | 済 |
| 会話プロトコル(開始ゲート5条件・招待→受諾0.8・状態機械・話者選択と相槌はエンジン・終了はエンジン=max_turns 3/ソフト停止/CLOSING定型) | 5,000体日で 168 セッション・スクリプトLLMで 16 セッション/32 発話ブロック | 済 |
| 録画テープ結線(全呼を Parquet へ・record/replay・TapeMiss は実LLMへ落とさない) | 録画→再生で最終状態ハッシュ一致・テープ外0・別 seed 再生で TapeMiss>0 かつ実クライアント不呼出 | 済 |
| 診断行(日次 8 行: deferred/promoted/degraded/suppressed/parse_errors/undefined_actions/tape_misses/conversations_opened) | 5 本以上が出る | 済 |

親の裁定: δ_think L1 は認知設計書どおり 2.6 s→切り上げ 1 tick(親の「0」指示が誤り)。招待の RNG カウンタ順を運用設計書 §2.5 の (tick, entity) に修正。手伝いの「能力不足」に `ResultCode.INSUFFICIENT_ABILITY` を追加。語彙 24 語=上限到達・種別固有語の効果・被招待側の CONVERSING は PENDING/C4 へ。expedient は実装計画書 §8 C3 契約側節に登録。

## 2. 知覚側(サブE: templates・normalize・channels・p_notice・attention・hashes・state・renderer)= 親検収済み

```
$ .venv/Scripts/python.exe -m pytest tests/perception -q -s
[P7] n=26000 候補=5814 A3(一次のみ)=0.792 ms / A4(+社会項)=1.993 ms
[renderer] 1,000描画 平均 0.1208 ms/描画・キャッシュ命中率 0.906
[実データ] cells=520 poi=2337 0.0928 ms/描画・hit_rate=0.527
132 passed in 1.14s      (全体: 746 passed, 1 xfailed)
$ lint-imports → 5 kept, 0 broken   $ scan → CLEAN   template_sha256 = 161fe181bc325f00…(固定)
```

| 受入項目 | 実測 | 判定 |
|---|---|---|
| golden バイト一致(同セル・同5分帯・同種別の2体で B0-B4(+B4b) 差分0) | 合格(規約⑧は種別を含めて読む=登録) | 済 |
| 個体依存語の変更が B5/B6 にのみ影響・描画決定論・5分丸め(12:31/12:34 同一 B3)・個体依存語ガード・命令文除去 | 合格 | 済 |
| チャネル上限(§3.2 表・等級 A-E)・ブロック/群予算 | 最悪 B0 603/B1 9/B2 81/B3 32/B4 40/B4b 11/B5 91/B6 63・群 644/750・132/250・154/300 | B0 単体は行予算超過=PENDING |
| p_notice 2段ヒル型(§3.1 表 10-200 m を再現)・上限 200 事象/tick・A0-A4 | 26,000 候補で 0.79/1.99 ms(P7) | 済 |
| ハッシュ三役(prefix key・変化検出・dormant 再送抑止) | 実装。**エンジンの変化検出(C2)と知覚側の B4 行が不一致=描画変化の約48%を取りこぼす→結線で切替** | 結線待ち |
| M12(向き1B+課題1B+再送ハッシュ16B=18B/体) | 7.2 MB@40万体 | 済 |
| 実資産(520セル・2,337 POI)での描画 | 0.093 ms/描画・予算内・規約⑧成立 | 済 |

## 3. 結線(サブ C3-wire: レンダラ→bridge・last_action・W10 騒音段・変化検出切替・書き込みガード)= 親検収済み

```
$ .venv/Scripts/python.exe -m shibuya.engine.run --agents 5000 --seed 1 --world data/world/v2   (実レンダラ)
壁時計 9.22 s(≤60 s・stub 3.99 s→+5.2 s=描画 44,003 回)/ P2 0.082 ms/tick / L4 8.80 呼/体/日 / 保存則 OK
診断 8 行: deferred 44,114 / promoted 81,817 / degraded 9,112 / suppressed 7,680 / parse_error_rate 0 / undefined 0 / tape_miss 0 / sessions 40
レンダラ: キャッシュ命中率 0.992・平均 tok 共有 643/750・セル 139/250・個体 131/300(合計 914)
変化検出の取りこぼし: 1,387/2,878(48.2%)→ 0(過検出 42→0)・P6 0.80/1.03/1.36 ms/tick@40万体
規約⑧ in situ: 合成 11 群・実データ 147 群(50 標本)すべて B0-B4b 同一
$ pytest -q(全体)→ 862 passed, 1 xfailed   $ lint-imports → 5 kept   $ scan → CLEAN
```

親の裁定: prompt_hash はテープ鍵(sha256_cbor 本文)と prefix 鍵(blake3 ブロック)の 2 役で並存(登録簿)。開閉店は起床源から外す(知覚契約 §6(i) に無い)。呼数は検出器の精密化で −8.2%(47,910→44,003=無駄起床の減少)。

## 4. 層2 独立検収(別インスタンスの Fable)

**判定: 合格(条件付き)**。レビュー役の実行: 510 passed(C3 範囲)/862 passed 全体/lint 5 kept/scan CLEAN/実レンダラ 5,000 体×1 日を 2 回=最終ハッシュ完全一致(T2)・呼 44,003=8.80/体/日・命中率 0.992・群 tok 643/139/131/録画=再生 7363c14b…/規約⑧を自前スクリプトで実証(差分は B5/B6 のみ・hunger 変更→B5 のみ・wake 変更→B6 のみ・種別変更→B1 のみ)/p_notice 7 点を独立再計算=差 0/パーサ敵対 15 本=例外 0/`git diff main -- docs/design/`=§8/§4 追記のみ(+89/−0)。2 つの prompt_hash は同一バイト列の別表現で片方だけ変わる経路なし=再生決定論は壊れない。

| 指摘 | 処置 |
|---|---|
| 不応答/ゲート却下の招待側がセッション無しの CONVERSING に残る(15 体/日) | `resolve.revert_conversation` を追加し run が不応答時に IDLE へ戻す+日末 CONVERSING==活動セッション のテスト |
| prefix_key が B0-B6 全体(共有 prefix 鍵になっていない) | 共有 B0-B4b のみで合成へ修正 |
| 規約②⑥の関数が描画経路で未使用 | ⑥を B4/B4b/B5 に結線(B2 の固有名詞は対象外=登録)・②は可視視点数降順→ID 昇順の読みを登録 |
| 受入報告 §1 の録画/再生値が結線前 | 更新 |
| expedient 未登録 10 件 | §8 へ追記 |
| 部品のみで未結線(注意ゲート・p_notice・dormant・起床(ii)残り・4 回打ち切り) | C4/C5 の受入へ(PENDING) |
